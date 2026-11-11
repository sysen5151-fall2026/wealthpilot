# Environment

- **Language / version:** Python 3.12 (CI); Python 3.13 on the development Mac
- **Runtime:** local virtual environment. `python app.py --serve` starts a FastAPI 0.161.1 app on uvicorn 0.53.0 at http://127.0.0.1:8000; saved plans and simulated portfolios are kept in SQLite (`data/wealthpilot.db`, Python standard library). The browser front end (`frontend/`) loads no outside scripts or fonts.
- **Model runner:** LM Studio (local, OpenAI-compatible API, default `http://localhost:1234/v1`), optional
- **Model:** not yet selected. With `WEALTHPILOT_LLM_MODEL` unset, F.6.1 uses its deterministic template
- **Editor:** VS Code
- **Assistants used in project work:** Claude Code (Chapter 1 scaffold); ChatGPT (Task 2 requirements/repository review and UC.1 walking-skeleton alignment); Claude, claude-opus-5-5 (F.6 code on 2026-11-03, the UC.1 browser app on 2026-11-04, the rules review on 2026-11-05)

## Historical market data provider

This section records the actual provider and endpoint, as the SPEC.md Historical Market Data Contract requires.

- **Provider:** Yahoo Finance, read through the open-source `yfinance` library, version 1.7.0, which is not affiliated with Yahoo.
- **Endpoint:** `scripts/fetch_price_snapshot.py` calls `yfinance.Ticker(symbol).history(start, end, interval="1d", auto_adjust=True, actions=False)`. yfinance 1.7.0 requests `https://query2.finance.yahoo.com/v8/finance/chart/{symbol}`, according to the library source (`yfinance/const.py`, `yfinance/scrapers/history.py`).
- **Field mapping:**

  | Contract field | Source |
  | --- | --- |
  | `symbol` | The requested ticker |
  | `date` | The trading date of each daily bar, as an ISO 8601 date |
  | `adjusted_close` | `Close` with `auto_adjust=True`, which yfinance replaces with Yahoo's adjusted close (split- and dividend-adjusted) |

  Rows with a missing or non-positive close are skipped and counted in the manifest, never filled in.
- **When the data are fetched:** only when someone runs the script, which needs `requirements-data.txt` and internet access. WealthPilot itself never contacts Yahoo. It reads the snapshot in `data/prices/` and refuses one whose SHA-256 fingerprint does not match its manifest.
- **Installed snapshot:** `yahoo-2026-11-04`, retrieved 2026-11-04 22:01 UTC.
  - Range: 2021-11-04 to 2026-11-04.
  - Coverage: AAPL, AGG, BIL, BND, MSFT, TQQQ, VTI and VXUS, 1,254 trading days each (10,032 rows); no rows skipped.
  - SHA-256: `f9be21b4c819ac65415502f951d43bb4b76f42df78d0ff9229058319cf150e40`.
- **Refreshing:** `python scripts/fetch_price_snapshot.py` (use `--years N` for a different window) writes a new CSV and points the manifest at it. Commit both files. Saved plans record the snapshot ID they were built from.
- **Terms of use:** the data are used for this educational course project only. Check Yahoo's terms before using them for anything else.

## Current implementation status

UC.1 runs end to end in the browser and in the console. F.1 to F.5 apply `config/rules.json` (WP-RULES-0.2; reasons in `docs/rules-rationale.md`). X.2 serves the installed Yahoo Finance snapshot through the data contract. F.6.1 explains with the template, or with an LM Studio model when one is configured. F.6.4 saves to SQLite. The requirement tests (`tests/test_functional_requirements.py`, `test_uc1_functions.py`, `test_api.py`, `test_explanation_language_model.py`, `test_fetch_snapshot.py`) are green. The N-01–N-08 coursework checks now run by default with the AI-role protocol described in SPEC.md. Current local verification: 131 passed, 0 skipped. Human comprehension and usability have not been empirically measured.
