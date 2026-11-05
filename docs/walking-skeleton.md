# UC.1 — Investor obtains a simulated investment plan and candidate securities

The table below mirrors the current 20-step UC.1 model and preserves the educational-simulation boundary. The last two columns name the code that carries out each step and where the investor sees it in the browser.

| Step | Interaction | Code | In the browser |
| --- | --- | --- | --- |
| **UC.1.1** | Individual Investor → WealthPilot: Initiate Session | `Planner.start_session` (`POST /api/sessions`) | Start planning |
| **UC.1.2** | WealthPilot → Individual Investor: Request Financial Profile | `investor_interface.requests_for_investor_input` (F.1) | About you |
| **UC.1.3** | Individual Investor → WealthPilot: Provide Financial Profile | `investor_interface.collect_investor_information` (F.1) | About you |
| **UC.1.4** | WealthPilot → Individual Investor: Request Risk Responses | `requests_for_investor_input` (F.1) | Your answers |
| **UC.1.5** | Individual Investor → WealthPilot: Provide Risk Responses | `collect_investor_information` (F.1) | Your answers |
| **UC.1.6** | WealthPilot → Individual Investor: Request Current Holdings | `requests_for_investor_input` (F.1) | About you, What you already hold |
| **UC.1.7** | Individual Investor → WealthPilot: Provide Current Holdings (hypothetical / simulated planning input) | `collect_investor_information` (F.1) | About you, What you already hold |
| **UC.1.8** | WealthPilot: Determine Risk Score | `risk_engine.assess_investor_risk_profile` (F.2) | See my risk profile |
| **UC.1.9** | WealthPilot → Individual Investor: Present Risk Assessment | `POST /api/sessions/{id}/investor-information` response | Your risk profile |
| **UC.1.10** | Individual Investor → WealthPilot: Confirm Profile Interpretation | `Planner.build_plan(profile_interpretation_confirmed=True)` | Yes, build my plan |
| **UC.1.11** | WealthPilot → Market Data Provider: Request Market Data | `allocation_engine.request_historical_market_data` (F.3) | |
| **UC.1.12** | Market Data Provider → WealthPilot: Provide Market Data | `market_data_provider.provide_historical_market_data` (X.2, data contract) | |
| **UC.1.13** | WealthPilot: Determine Target Allocation | `allocation_engine.determine_target_asset_allocation` (F.3) | |
| **UC.1.14** | WealthPilot: Filter Candidate Securities | `screening_engine.screen_candidate_securities` (F.4) | |
| **UC.1.15** | WealthPilot: Generate Investment Recommendations and Weights | `portfolio_construction_engine.generate_investment_recommendations` (F.5) | |
| **UC.1.16** | WealthPilot: Explain Plan Rationale and Risks | `investment_plan_management.explain_investment_plan` (F.6.1) | |
| **UC.1.17** | WealthPilot → Individual Investor: Present Investment Plan | `investment_plan_management.present_investment_plan` (F.6.2) | Your simulated plan |
| **UC.1.18** | Individual Investor → WealthPilot: Request Plan Save | `Planner.request_save` (`POST /api/sessions/{id}/plan-save-requests`) | Save this simulated plan |
| **UC.1.19** | WealthPilot: Save Plan and Confirm | `validate_explicit_plan_save_request`, `persist_reviewed_investment_plan`, `confirm_successful_plan_save` (F.6.3 to F.6.5) | Saved confirmation |
| **UC.1.20** | Individual Investor: Review Saved Plan | `GET /api/saved-plans/{plan_id}` | Saved plans |

No step connects to a brokerage or custodian, and no step executes a real transaction.

## Current Implementation

`wealthpilot_service/pipeline.py` (the `Planner`) runs the steps above in order for the browser (`python app.py --serve`) and for the console (`python app.py`, with the sample investor in `investor_interface/console.py`). Every step is recorded as a trace line tagged with the function and the asset that performs it, for example `F.6.3 | C.6.3`; the browser lists them under "How this plan was built" and the console prints them. `python app.py --no-save` runs the session without a Plan Save Request, so nothing is saved and no confirmation is sent.

F.1 to F.5 apply the rules in `config/rules.json`; `docs/rules-rationale.md` gives the reason for each value. Market data come from the versioned Yahoo Finance snapshot in `data/prices/`, admitted only if it passes the SPEC.md data contract; without a snapshot the plan is withheld. F.6.1 explains the plan with the approved template, or with a local LM Studio model when `WEALTHPILOT_LLM_MODEL` is set, falling back to the template whenever the model's answer breaks the Model Response Contract. A saved plan is written to `data/wealthpilot.db` and read back before the save is confirmed; the simulated cash and holdings in the same file are not touched. See `docs/traceability.md` for the function-to-module map and the requirement tests.
