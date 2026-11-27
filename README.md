# WealthPilot

**SYSEN 5151 Final Demo** · WealthPilot turns a novice investor’s goals and risk assessment into an explainable, simulated investment plan.

- [Run the demo](#running-wealthpilot). The product shows only what the learner needs; model-to-code tracing is in the documents below, not in the interface.
- [Requirements](SPEC.md) · [Model-to-code traceability](docs/traceability.md) · [Architecture decision](docs/adr/0002-explanation-deployment.md) · [Risk and verification](docs/risks.md).
- [Automated verification](https://github.com/sysen5151-fall2026/wealthpilot/actions/runs/45239771975) on baseline 3acb8dc recorded 137 passed, five expected failures, and zero skipped.

## Operational Concept

WealthPilot is an **educational investment-planning simulator for novice investors**. It does not connect to a real brokerage account, place real trades, transfer funds, or authorize real investment execution.

An Individual Investor starts a planning session and provides a financial profile, including a stated goal, investment horizon, financial capacity, liquidity needs, investment experience, and hypothetical current holdings. The investor also completes a structured risk questionnaire. WealthPilot uses these inputs to determine a risk score and corresponding risk level.

WealthPilot requests historical market data from a Market Data Provider, determines a target allocation, filters candidate securities, and presents a simulated educational investment plan. The plan includes the target allocation, candidate securities, material risks, and an explanation of how the investor profile and risk assessment influenced the result. The investor confirms the profile interpretation and can request that the simulated plan be saved.

The saved plan remains separate from later simulated portfolio actions. Additional course use cases support simulated recurring planning, simulated portfolio drift/rebalancing review, what-if analysis, and administrative maintenance. A System Administrator manages approved educational baselines and recovery. Market and regulatory conditions constrain the simulator through the Market and Regulatory Environment.

## Running WealthPilot

WealthPilot runs on your own computer as a small web app: a Python server (FastAPI) and a browser front end. Saved plans are kept in a local SQLite file.

### 1. Set up (once)

```bash
cd wealthpilot
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 2. Install the price history (once, needs internet)

Plans are built from a versioned snapshot of daily adjusted closing prices from Yahoo Finance, so every run of the exercise uses the same evidence and the app itself never goes online.

```bash
pip install -r requirements-data.txt
python scripts/fetch_price_snapshot.py          # 5 years ending today, every instrument in config/rules.json
git add data/prices && git commit -m "Add price snapshot"
```

Until a snapshot is installed, the app runs but withholds every plan and says why (SR-10).

### 3. Run it

```bash
python app.py --serve      # then open http://127.0.0.1:8000
python app.py              # UC.1 once in the terminal with a sample investor, who saves the plan
python app.py --no-save    # the same, but the investor never asks to save, so nothing is saved
```

In the browser, a learner goes through the four steps of UC.1: About you, Your answers, Your risk profile (confirm it), and Your plan (save it). The pages show only the learner's inputs, risk profile, plan and save result. The Planner still tags each step internally with the model function and asset (for example `F.6.3 | C.6.3`); that mapping is documented in `docs/traceability.md` and checked by the tests, and is not shown in the product.

### 4. Optional: explanations from a local language model (LM Studio)

By default the plan explanation comes from the approved template. To let a model loaded in LM Studio word it instead, start LM Studio's local server and name the model:

```bash
export WEALTHPILOT_LLM_MODEL="<model identifier shown in LM Studio>"
python app.py --serve
```

The model's answer is used only if it passes the implemented checks of the SPEC.md Model Response Contract. Otherwise the template is used and the plan says why. `WEALTHPILOT_LLM_BASE_URL` (default `http://localhost:1234/v1`) must use `localhost`, `127.0.0.1`, or `::1`. Model redirects are rejected. `WEALTHPILOT_LLM_TIMEOUT` sets the timeout in seconds (default 30).

### Tests

```bash
python -m pytest -v -rs    # full implementation and AI-role coursework checks
python -m pytest tests/test_functional_requirements.py tests/test_model_contract.py -v
python scripts/coursework_exercise.py  # regenerate detailed exercise evidence
```

Tests use synthetic prices in temporary folders, never `data/prices/`.

### Rules and what is not built yet

- `config/rules.json` holds every rule value (questionnaire points, category bands, mixes, screening limits, weights, wording). The AI assistant proposed them; they were reviewed on 2026-11-05 against the installed price snapshot, and `docs/rules-rationale.md` gives the reason for each. The team (Yicheng Yang and Fangziyue Zhang) signed them off on 2026-11-26; the `status` line at the bottom of every page shows this.
- UC.1 is implemented. Saved-plan what-if comparison, separate internal simulated-change approval and baseline recovery now have course prototypes. These additions do not establish complete UC.2–UC.5 implementations or cloud model allocation.
- In-progress sessions live in memory, so restarting the server ends them; saved plans stay in `data/wealthpilot.db` (git ignores it).
- The app has no sign-in and is meant to run on one computer (it listens on 127.0.0.1 only). See `docs/deployment.md` before hosting it anywhere else.

## Repository map

- `SPEC.md`: stakeholder needs, requirements, acceptance criteria, Data Contract and Model Response Contract.
- `config/rules.json`: the configuration X.3 supplies; `docs/rules-rationale.md` explains each value.
- `model_flows/`: one class per flow on the first-level IDEF0.
- `investor_interface/` F.1, `risk_engine/` F.2, `allocation_engine/` F.3, `screening_engine/` F.4, `portfolio_construction_engine/` F.5, `investment_plan_management/` F.6.1 to F.6.5.
- `market_data_provider/` X.2 boundary and data contract, `system_administration/` X.3 configuration, `historical_analysis/` shared calculations.
- `wealthpilot_service/`: C.0 orchestration (`pipeline.py`), HTTP interface (`api.py`) and local storage.
- `frontend/`: the browser front end. `scripts/fetch_price_snapshot.py`: the one-time price download.
- `tests/`: requirement-named tests; `.github/workflows/tests.yml` runs them.
- `docs/traceability.md`: function to module, requirements and tests. `docs/walking-skeleton.md`: UC.1 step to code. `docs/prompt-log.md`: AI-assistance log.

## Earlier Task 2 artifacts

- `SPEC.md` — stakeholder needs, traces to stakeholder requirements, acceptance criteria, Data Contract, and Model Response Contract.
- `tests/test_spec_acceptance.py` — executable AI-role coursework checks for N-01 through N-08; original human-study skeleton archived in docs/original-human-acceptance-reference.py.
- `.github/workflows/tests.yml` — Milestone 2 workflow running the full implementation and coursework verification suite.
- `docs/prompt-log.md` — cumulative prompt log, including AI-assisted repository and walking-skeleton updates.

The coursework execution method and its limits are stated in SPEC.md. AI-role results do not establish empirical human comprehension or usability.

## Milestone 2 recording package

- On macOS, double-click `Launch_WealthPilot.command` (or run `zsh Launch_WealthPilot.command` from this folder). It creates a local environment, installs the pinned development dependencies and starts the app.
- `contracts/api-v1.yaml`: actual HTTP operations and F.6 internal callable ICOMs. Regenerate with `python scripts/export_api_contract.py`; contract tests detect drift.
- `docs/route-table.md`: product action → HTTP route → UC.1 step → function/asset.
- `tests/test_functional_requirements.py`: renamed existing C.6 requirement tests, with their real assertions retained.
- `docs/requirements-flowdown.md`: implementation traces, a proposed equivalence rationale and remaining model checks.
- `docs/model-recording-checklist.md`: cloud views and relationships to verify before recording.
- `docs/recording-guide.md`: Chinese screen cues with an English ten-minute script.
- `evidence/local-pytest.xml`: local verification report; not a GitHub Actions result.

## Coursework acceptance evidence

See [the coursework acceptance update](COURSE_ACCEPTANCE_UPDATE.md) and its [AI-role observations](evidence/acceptance/coursework-role-report.json) for the original Milestone 2 evidence. The current verification result and the limits of the coursework protocol are described in [SPEC.md](SPEC.md).
