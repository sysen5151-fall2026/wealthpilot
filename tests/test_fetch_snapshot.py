"""scripts/fetch_price_snapshot.py, run against a stand-in for yfinance (no network).

The script is what puts X.2 Market Data Provider's data into the repository, so
its output must pass the same data contract the app applies (SR-09), and gaps
in the provider's data must be recorded rather than filled in.
"""

import json
import math
from datetime import date, datetime, timedelta

from scripts.fetch_price_snapshot import download_rows, write_snapshot

from market_data_provider import provide_historical_market_data
from model_flows import MarketDataRequest


class FakeHistory:
    def __init__(self, closes):
        start = datetime(2026, 1, 5, 0, 0)
        self.index = [start + timedelta(days=i) for i in range(len(closes))]
        self.closes = closes

    def __contains__(self, column):
        return column == "Close"

    def __getitem__(self, column):
        return self.closes


class FakeYfinance:
    __version__ = "fake"
    histories = {
        "VTI": [100.0, 101.0, math.nan, 102.5],
        "BND": [70.0, 70.1, 70.2, 70.15],
        "GONE": [],
    }

    class Ticker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, **options):
            assert options["auto_adjust"] is True and options["interval"] == "1d"
            return FakeHistory(FakeYfinance.histories[self.symbol])


def test_snapshot_is_written_with_a_fingerprint_and_passes_the_data_contract(tmp_path):
    rows, empty, skipped = download_rows(FakeYfinance, ["VTI", "BND", "GONE"], date(2026, 1, 1), date(2026, 2, 1))

    assert empty == ["GONE"]
    assert skipped == {"VTI": 1}
    manifest = write_snapshot(rows, tmp_path, start=date(2026, 1, 1), end=date(2026, 2, 1), source="fake", skipped=skipped)

    assert manifest["snapshot_id"] == "yahoo-2026-02-01"
    assert manifest["rows"] == 7 and manifest["skipped_non_positive_or_missing_closes"] == {"VTI": 1}
    assert json.loads((tmp_path / "manifest.json").read_text()) == manifest
    data = provide_historical_market_data(MarketDataRequest(["VTI", "BND"]), snapshot_directory=tmp_path)
    assert data.limitations == []
    assert len(data.series["VTI"].dates) == 3 and len(data.series["BND"].dates) == 4
