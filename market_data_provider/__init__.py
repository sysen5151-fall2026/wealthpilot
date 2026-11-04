"""X.2 Market Data Provider boundary: Historical Market Data from the approved snapshot.

The provider's data reaches WealthPilot as a versioned snapshot in data/prices/
(see scripts/fetch_price_snapshot.py), so every run of an exercise uses the same
evidence (SPEC "Replay and reproducibility"). Data enter planning only after the
SPEC.md data contract is applied here (SR-09, 1.1.5); anything that fails is
reported as a historical-data limitation instead of being used (SR-10).
"""

import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from datetime import date
from pathlib import Path

from model_flows import HistoricalMarketData, MarketDataRequest, PriceSeries

DEFAULT_SNAPSHOT_DIRECTORY = Path(
    os.environ.get("WEALTHPILOT_SNAPSHOT_DIRECTORY", Path(__file__).resolve().parent.parent / "data" / "prices")
)
MANIFEST_NAME = "manifest.json"


def provide_historical_market_data(
    market_data_request: MarketDataRequest,
    *,
    snapshot_directory: Path = DEFAULT_SNAPSHOT_DIRECTORY,
) -> HistoricalMarketData:
    """Return the admitted price series for the requested symbols, with any limitations.

    Never fabricates observations: if the snapshot is missing or altered, no
    series are returned and the limitation says why.
    """
    snapshot_directory = Path(snapshot_directory)
    manifest_path = snapshot_directory / MANIFEST_NAME
    if not manifest_path.exists():
        return _unavailable(
            "No historical price snapshot is installed, so the plan cannot be built. "
            "Run scripts/fetch_price_snapshot.py once to create one."
        )
    try:
        manifest = json.loads(manifest_path.read_text())
        data_path = snapshot_directory / manifest["file"]
        fingerprint, snapshot_id = manifest["sha256"], manifest["snapshot_id"]
    except (OSError, ValueError, KeyError, TypeError):
        return _unavailable("The snapshot manifest is unreadable or incomplete, so no historical data are used.")
    if not data_path.is_file():
        return _unavailable(f"The snapshot file {manifest['file']} named in the manifest is missing.")
    if hashlib.sha256(data_path.read_bytes()).hexdigest() != fingerprint:
        return _unavailable(
            f"The snapshot {snapshot_id} does not match its recorded fingerprint, so it is not used."
        )

    rows_by_symbol = defaultdict(list)
    with data_path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            rows_by_symbol[(row.get("symbol") or "").strip()].append(row)

    series, limitations = {}, []
    for symbol in market_data_request.symbols:
        rows = rows_by_symbol.get(symbol)
        if not rows:
            limitations.append(f"{symbol}: no data in snapshot {snapshot_id}; not used.")
            continue
        admitted, problem = _admit(symbol, rows)
        if problem:
            limitations.append(f"{symbol}: {problem}; not used.")
        else:
            series[symbol] = admitted

    return HistoricalMarketData(
        snapshot_id=snapshot_id,
        source=manifest.get("source"),
        series=series,
        limitations=limitations,
    )


def snapshot_status(snapshot_directory: Path = DEFAULT_SNAPSHOT_DIRECTORY) -> dict:
    """Which snapshot is installed and whether it can be used, for the status page."""
    check = provide_historical_market_data(MarketDataRequest(symbols=[]), snapshot_directory=snapshot_directory)
    if check.snapshot_id is None:
        return {"available": False, "problem": check.limitations[0]}
    manifest = json.loads((Path(snapshot_directory) / MANIFEST_NAME).read_text())
    return {
        "available": True,
        "snapshot_id": manifest["snapshot_id"],
        "source": manifest.get("source"),
        "start": manifest.get("start"),
        "end": manifest.get("end"),
        "symbols": manifest.get("symbols", []),
        "rows": manifest.get("rows"),
    }


def _unavailable(reason: str) -> HistoricalMarketData:
    return HistoricalMarketData(snapshot_id=None, source=None, series={}, limitations=[reason])


def _admit(symbol: str, rows: list[dict]) -> tuple[PriceSeries | None, str | None]:
    """Apply the SPEC data contract to one symbol's rows."""
    observations = {}
    for row in rows:
        raw_date, raw_close = row.get("date"), row.get("adjusted_close")
        try:
            day = date.fromisoformat(raw_date or "").isoformat()
            close = float(raw_close)
        except (TypeError, ValueError):
            return None, f"malformed or missing date or adjusted_close ({raw_date!r}, {raw_close!r})"
        if not math.isfinite(close) or close <= 0:
            return None, f"adjusted_close {raw_close} on {day} is not a positive number"
        if day in observations:
            return None, f"duplicate observation on {day}"
        observations[day] = close
    dates = sorted(observations)
    return PriceSeries(symbol, dates, [observations[d] for d in dates]), None
