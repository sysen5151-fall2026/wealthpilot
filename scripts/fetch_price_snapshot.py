"""Download a versioned historical price snapshot from Yahoo Finance (run once, needs internet).

    pip install -r requirements-data.txt
    python scripts/fetch_price_snapshot.py            # 5 years ending today
    python scripts/fetch_price_snapshot.py --years 7

Writes data/prices/prices-<end date>.csv with the SPEC.md data-contract fields
(symbol, date, adjusted_close) for every instrument in config/rules.json, and
data/prices/manifest.json with the source, date range and SHA-256 fingerprint.
Commit both files so the app runs offline and graders see the same data.
WealthPilot itself never calls Yahoo Finance; it only reads the snapshot.
"""

import argparse
import csv
import hashlib
import json
import math
import sys
import warnings
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "data" / "prices"
RULES_PATH = ROOT / "config" / "rules.json"


def configured_symbols(rules_path: Path = RULES_PATH) -> list[str]:
    allocation = json.loads(rules_path.read_text())["allocation_rules"]["asset_classes"]
    symbols = []
    for definition in allocation.values():
        for symbol in [definition["benchmark"], *definition["instruments"]]:
            if symbol not in symbols:
                symbols.append(symbol)
    return symbols


# yfinance 1.7.0 still uses pandas calls that pandas 3.1 has deprecated; the warnings are not about the data.
warnings.filterwarnings("ignore", message=r"The inplace keyword", module=r"yfinance")


def download_rows(yfinance, symbols: list[str], start: date, end: date) -> tuple[list[dict], list[str], dict]:
    """Adjusted daily closes for each symbol.

    Returns (rows, symbols that returned nothing, count of empty or non-finite
    closes skipped per symbol). Skipped rows are recorded in the manifest, so
    the gap stays visible instead of being filled in.
    """
    rows, empty, skipped = [], [], {}
    for symbol in symbols:
        history = yfinance.Ticker(symbol).history(
            start=start.isoformat(), end=end.isoformat(), interval="1d", auto_adjust=True, actions=False
        )
        closes = list(zip(history.index, history["Close"])) if "Close" in history else []
        kept = 0
        for timestamp, close in closes:
            value = float(close)
            if not math.isfinite(value) or value <= 0:
                skipped[symbol] = skipped.get(symbol, 0) + 1
                continue
            rows.append({"symbol": symbol, "date": timestamp.date().isoformat(), "adjusted_close": f"{value:.6f}"})
            kept += 1
        if not kept:
            empty.append(symbol)
    return rows, empty, skipped


def write_snapshot(
    rows: list[dict], output: Path, *, start: date, end: date, source: str, skipped: dict | None = None
) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    data_file = output / f"prices-{end.isoformat()}.csv"
    rows = sorted(rows, key=lambda r: (r["symbol"], r["date"]))
    with data_file.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "date", "adjusted_close"])
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "snapshot_id": f"yahoo-{end.isoformat()}",
        "file": data_file.name,
        "sha256": hashlib.sha256(data_file.read_bytes()).hexdigest(),
        "source": source,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "symbols": sorted({r["symbol"] for r in rows}),
        "rows": len(rows),
        "skipped_non_positive_or_missing_closes": skipped or {},
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        import yfinance
    except ImportError:
        print("yfinance is not installed. Run: pip install -r requirements-data.txt", file=sys.stderr)
        return 1

    end = date.today()
    start = end - timedelta(days=round(365.25 * args.years))
    symbols = configured_symbols()
    print(f"Downloading {len(symbols)} symbols from {start} to {end}: {', '.join(symbols)}")
    try:
        rows, empty, skipped = download_rows(yfinance, symbols, start, end)
    except Exception as error:  # network trouble or Yahoo rate limits: nothing is written
        print(f"Download failed ({type(error).__name__}: {error}). Nothing was written; try again later.", file=sys.stderr)
        return 1
    if empty:
        print(f"No data returned for: {', '.join(empty)}. Nothing was written.", file=sys.stderr)
        return 1
    manifest = write_snapshot(
        rows, args.output, start=start, end=end,
        source=f"Yahoo Finance via yfinance {yfinance.__version__}", skipped=skipped,
    )
    if skipped:
        print("Skipped empty or non-positive closes (kept out of the snapshot): "
              + ", ".join(f"{symbol} {count}" for symbol, count in skipped.items()))
    print(f"Wrote {manifest['rows']} rows to {args.output / manifest['file']}")
    print(f"Snapshot {manifest['snapshot_id']}, sha256 {manifest['sha256'][:12]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
