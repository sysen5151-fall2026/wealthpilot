# Chapter 10 revision evidence

Status: in progress. Final Innoslate simulation and held-out browser validation are pending.

Base product commit: `f012ac2894730bbabbb10d8aac208533504b4ece`.
The unmodified base passed **161 tests**. The revision, with five cache regression tests, passed **166 tests**. Local mock-server tests require permission to bind a loopback port. Neither record contains the old eight placeholder failures.

`pilot_v2/` contains 100 core runs per scenario used ONLY for calibration. Every cache run fingerprints snapshot bytes; the cache is deliberately evicted before runs 1, 11, ..., 91. Thus the workload has 90 hits and 10 rebuilds. That ratio is an experimental input, not a measured production hit rate. `pilot/` is the superseded initial instrumentation pilot and is retained for audit only.

`frozen_parameters.json` records the calibration rule, numeric pilot evidence and the source-data hash before held-out validation. Initial pre-measurement forecasts remain in `../original_forecast/`. Do not substitute pilot results for independent validation.

## Reproduction

From the repository root, install `requirements-dev.txt` in an isolated Python environment, then run:

```sh
python -m pytest -q
python scripts/ch10_measure.py --out evidence/ch10/revision/reproduction --runs 100
python scripts/ch10_browser_server.py
```

Open `http://127.0.0.1:8766/?ch10=1` and click **Run Chapter 10 browser measurements**. Keep the page in the foreground. The loopback-only instrumentation server writes four actual HTTP request boundaries per run and records the product component timings. Browser display timing is a two-animation-frame opportunity proxy, not a physical screen measurement. Human typing, reading and thought are excluded.

The baseline default application remains uncached. The cache is opt-in through the experiment harness. `market_data_provider/snapshot_cache.py` implements fingerprint checks, invalidation, loading, publication and defensive copying. Its key includes directory, symbol list, admission threshold, manifest digest and CSV digest. Concurrent snapshot replacement is not benchmarked and may raise a retry error.

Raw SQLite files contain only synthetic fixtures and are reproducible runtime byproducts; they are excluded from version control. JSON records contain raw timings, per-run correctness checks, platform details, source hashes and the measured commit.
