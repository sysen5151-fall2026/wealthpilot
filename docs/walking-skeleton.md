# UC.1 — Investor obtains a simulated investment plan and candidate securities

The walking skeleton below mirrors the current 20-step UC.1 model and preserves the educational-simulation boundary. The last column names the code that carries out each step.

| Step | Interaction | Code |
| --- | --- | --- |
| **UC.1.1** | Individual Investor → WealthPilot: Initiate Session | `investor_interface.initiate_session` |
| **UC.1.2** | WealthPilot → Individual Investor: Request Financial Profile | `investor_interface.request_financial_profile` (F.1) |
| **UC.1.3** | Individual Investor → WealthPilot: Provide Financial Profile | stubbed answer from `request_financial_profile` |
| **UC.1.4** | WealthPilot → Individual Investor: Request Risk Responses | `investor_interface.provide_risk_questionnaire_response` (F.1) |
| **UC.1.5** | Individual Investor → WealthPilot: Provide Risk Responses | stubbed answer |
| **UC.1.6** | WealthPilot → Individual Investor: Request Current Holdings | `investor_interface.provide_current_holdings` (F.1) |
| **UC.1.7** | Individual Investor → WealthPilot: Provide Current Holdings (hypothetical / simulated planning input) | stubbed answer |
| **UC.1.8** | WealthPilot: Determine Risk Score | `risk_engine.assess_investor_risk_profile` (F.2) |
| **UC.1.9** | WealthPilot → Individual Investor: Present Risk Assessment | `investor_interface.present_risk_assessment` |
| **UC.1.10** | Individual Investor → WealthPilot: Confirm Profile Interpretation | `investor_interface.confirm_profile_interpretation` |
| **UC.1.11** | WealthPilot → Market Data Provider: Request Market Data | `market_data_provider.get_historical_prices` |
| **UC.1.12** | Market Data Provider → WealthPilot: Provide Market Data | stubbed prices from `get_historical_prices` |
| **UC.1.13** | WealthPilot: Determine Target Allocation | `allocation_engine.determine_target_asset_allocation` (F.3) |
| **UC.1.14** | WealthPilot: Filter Candidate Securities | `screening_engine.screen_candidate_securities` (F.4) |
| **UC.1.15** | WealthPilot: Generate Investment Recommendations and Weights | `portfolio_construction_engine.generate_investment_recommendations` (F.5) |
| **UC.1.16** | WealthPilot: Explain Plan Rationale and Risks | `investment_plan_management.explain_investment_plan` (F.6.1) |
| **UC.1.17** | WealthPilot → Individual Investor: Present Investment Plan | `investment_plan_management.present_investment_plan` (F.6.2) |
| **UC.1.18** | Individual Investor → WealthPilot: Request Plan Save | `investor_interface.request_plan_save` |
| **UC.1.19** | WealthPilot: Save Plan and Confirm | `validate_explicit_plan_save_request`, `persist_reviewed_investment_plan`, `confirm_successful_plan_save` (F.6.3 to F.6.5) |
| **UC.1.20** | Individual Investor: Review Saved Plan | `investor_interface.review_saved_plan` |

No step connects to a brokerage or custodian, and no step executes a real transaction.

## Current Walking-Skeleton Implementation

`wealthpilot_service.run_investment_planning_session` runs the steps above in order and prints one line per step, tagged with the function and the asset that performs it, for example `[F.6.3 | C.6.3]`. `python app.py --no-save` runs the same session without a Plan Save Request, so nothing is saved and no confirmation is sent.

F.1 to F.4 and all participant answers remain hard-coded stubs, and market data is a fixed sample. F.5 and the five F.6 functions are implemented. The explanation comes from a fixed template governed by Explanation Rules; no language model is called yet. A saved plan is written to `saved_plans/` and read back before the save is confirmed. See `docs/traceability.md` for the function-to-module map and `tests/test_cs6_requirements.py` for the component requirement tests.
