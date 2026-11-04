"""SYNTHETIC prices for tests only: a seeded random walk, never market data.

The snapshot it writes has the same layout as scripts/fetch_price_snapshot.py
(a CSV with symbol, date, adjusted_close and a fingerprinted manifest), but its
snapshot_id starts with "synthetic" and its source says what it is. It is
written to pytest's temporary folders and is never committed.
"""

import csv
import hashlib
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

# symbol: (annual drift, annual volatility, share of the equity market factor, crash depth)
PROFILES = {
    "VTI": (0.09, 0.18, 0.9, 0.30),
    "AAPL": (0.17, 0.30, 0.7, 0.35),
    "MSFT": (0.15, 0.27, 0.7, 0.30),
    "TQQQ": (0.25, 0.70, 0.9, 0.70),
    "VXUS": (0.05, 0.16, 0.8, 0.28),
    "BND": (0.02, 0.06, 0.0, 0.08),
    "AGG": (0.02, 0.06, 0.0, 0.08),
    "BIL": (0.03, 0.004, 0.0, 0.0),
}
CRASH_START, CRASH_DAYS = 250, 80


def trading_days(end: date, count: int) -> list[str]:
    days, day = [], end
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day.isoformat())
        day -= timedelta(days=1)
    return days[::-1]


def synthetic_rows(*, days: int = 1260, seed: int = 5151, end: date = date(2026, 10, 30), symbols=None) -> list[dict]:
    generator = random.Random(seed)
    dates = trading_days(end, days)
    market = [generator.gauss(0, 1) for _ in dates]
    rows = []
    for symbol in symbols or PROFILES:
        drift, volatility, beta, crash = PROFILES[symbol]
        own = random.Random(f"{seed}-{symbol}")
        price = 100.0
        for i, day in enumerate(dates):
            if i:
                shock = beta * market[i] + math.sqrt(1 - beta**2) * own.gauss(0, 1)
                step = (drift - volatility**2 / 2) / 252 + volatility / math.sqrt(252) * shock
                if CRASH_START <= i < CRASH_START + CRASH_DAYS and crash:
                    step += math.log(1 - crash) / CRASH_DAYS
                price *= math.exp(step)
            rows.append({"symbol": symbol, "date": day, "adjusted_close": f"{price:.6f}"})
    return rows


def write_snapshot_files(directory: Path, rows: list[dict], *, snapshot_id: str = "synthetic-test") -> dict:
    """Write rows exactly as given (bad rows included) with a matching manifest."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    data_file = directory / "prices-synthetic.csv"
    with data_file.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "date", "adjusted_close"])
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "snapshot_id": snapshot_id,
        "file": data_file.name,
        "sha256": hashlib.sha256(data_file.read_bytes()).hexdigest(),
        "source": "SYNTHETIC random walk for tests; not market data",
        "start": rows[0]["date"] if rows else None,
        "end": rows[-1]["date"] if rows else None,
        "symbols": sorted({r["symbol"] for r in rows}),
        "rows": len(rows),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def write_synthetic_snapshot(directory: Path, **options) -> dict:
    return write_snapshot_files(directory, synthetic_rows(**options))
