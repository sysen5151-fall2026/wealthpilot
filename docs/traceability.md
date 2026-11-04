# Traceability: model functions to code

Transcribed from the Innoslate model (Financial Project, read 2026-11-03). One row per function on the first-level IDEF0 of F.0 and on the second-level IDEF0 of F.6. `wealthpilot_service/` is listed with the external systems below: it is the C.0 orchestration that calls these functions in UC.1 order, not a function on the IDEF0.

| Function | Performed by | Module | Code | Requirements | Tests |
| --- | --- | --- | --- | --- | --- |
| F.1 Collect Investor Information | C.1 Investor Information Interface | `investor_interface/` (with `frontend/`) | `requests_for_investor_input`, `collect_investor_information` | 1.4.1; also 1.1.2, 1.1.4, 1.1.11, 1.1.14, 1.2.4 | `test_1_4_1_*` |
| F.2 Assess Investor Risk Profile | C.2 Risk Assessment Engine | `risk_engine/` | `assess_investor_risk_profile` | 1.4.2; also 1.1.12, 1.2.5 | `test_1_4_2_*` |
| F.3 Determine Target Asset Allocation | C.3 Asset Allocation Engine | `allocation_engine/` | `request_historical_market_data`, `determine_target_asset_allocation` | 1.4.3; also 1.1.1, 1.1.6, 1.1.10, 1.2.2 | `test_1_4_3_*` |
| F.4 Screen Candidate Securities | C.4 Security Screening Engine | `screening_engine/` | `screen_candidate_securities` | 1.4.4; also 1.1.7, 1.1.13 | `test_1_4_4_*` |
| F.5 Generate Investment Recommendations | C.5 Portfolio Construction Engine | `portfolio_construction_engine/` | `generate_investment_recommendations` | 1.4.5; also 1.1.9 | `test_1_4_5_*` |
| F.6 Manage Investment Plan Delivery | C.6 Investment Plan Management Subsystem | `investment_plan_management/` | decomposed into F.6.1 to F.6.5 | 1.1.8, 1.2.7, 1.4.6, 1.4.7, 1.4.8; CS6.1.3.1 to CS6.1.3.3; CS6.2.1 to CS6.2.4 | `test_CS6_2_3_*`, `test_CS6_2_4_*` |
| F.6.1 Explain Investment Plan | C.6.1 Explanation Engine | `investment_plan_management/explanation_engine.py`, `language_model.py` | `explain_investment_plan` | CS6.1.4.1, CS6.1.1.1, CS6.1.1.2, CS6.1.2.1; SR-02, SR-03 | `test_CS6_1_4_1_*`, `test_CS6_1_2_1_*`, `test_CS6_1_1_1_*` |
| F.6.2 Present Investment Plan | C.6.2 Plan Presentation Component | `investment_plan_management/plan_presentation.py` | `present_investment_plan` | CS6.1.4.2, CS6.1.1.2, CS6.1.2.2; SR-13 | `test_CS6_1_4_2_*`, `test_CS6_1_1_2_*` |
| F.6.3 Validate Explicit Plan Save Request | C.6.3 Save Authorization Component | `investment_plan_management/save_authorization.py` | `validate_explicit_plan_save_request` | CS6.1.4.3, CS6.1.1.3; SR-04 | `test_CS6_1_4_3_*`, `test_CS6_1_1_3_*` |
| F.6.4 Persist Reviewed Investment Plan | C.6.4 Plan Repository Component | `investment_plan_management/plan_repository.py` | `persist_reviewed_investment_plan`, `SqlitePlanStore` | CS6.1.4.4, CS6.1.1.3; SR-05 | `test_CS6_1_4_4_*` |
| F.6.5 Confirm Successful Plan Save | C.6.5 Save Confirmation Component | `investment_plan_management/save_confirmation.py` | `confirm_successful_plan_save` | CS6.1.4.5, CS6.1.1.3, CS6.1.2.3, CS6.1.2.4 | `test_CS6_1_4_5_*` |

Test files: `tests/test_uc1_functions.py` (F.1 to F.5, data contract, configuration), `tests/test_cs6_requirements.py` and `tests/test_explanation_language_model.py` (C.6), `tests/test_api.py` (UC.1 through the HTTP interface, named by SR), `tests/test_fetch_snapshot.py` (the snapshot script). Not covered by automated tests yet: CS6.2.1 (2-second timing over 100 runs), CS6.2.2 (novice comprehension study), and CS6.1.3.1 to CS6.1.3.3 (verified by inspecting the conduits in the model).

## External systems and the orchestration

| Model element | Code | What it does | Requirements | Tests |
| --- | --- | --- | --- | --- |
| X.1 Individual Investor | `frontend/` (browser), `investor_interface/console.py` (sample investor) | Answers the Requests for Investor Input, confirms the profile interpretation, sends the Plan Save Request | SR-13, SR-14, SR-15 | `test_SR_13_*`, `test_SR_14_*` |
| X.2 Market Data Provider | `market_data_provider/`, `scripts/fetch_price_snapshot.py`, `data/prices/` | Serves Historical Market Data from the fingerprinted snapshot, after the SPEC.md data contract | SR-09, SR-10 | `test_SR_09_*`, `test_SR_10_*`, `test_fetch_snapshot.py` |
| X.3 System Administrator | `system_administration/`, `config/rules.json` | Supplies every control as approved configuration; refuses a configuration that contradicts itself | SR-11 (configuration identifier) | `test_configuration_*` |
| ENV.1 Market and Regulatory Environment | `config/rules.json` section `market_and_regulatory_constraints` | Permitted product types; no leveraged or inverse products | | `test_1_4_4_leveraged_products_are_excluded` |
| C.0 WealthPilot (orchestration, not on the IDEF0) | `wealthpilot_service/pipeline.py`, `api.py`, `storage.py` | Calls the functions in UC.1 order and records the trace; keeps saved plans and the simulated portfolio in `data/wealthpilot.db` | SR-01, SR-04, SR-05 | `tests/test_api.py` |

## Flows on the first-level IDEF0 of F.0

| Flow | From | To | Type in code |
| --- | --- | --- | --- |
| Requests for Investor Input | F.1 | X.1 | `dict` from `requests_for_investor_input` |
| Financial Profile, Risk Questionnaire Responses, Current Holdings | X.1 | F.1 | request body of `POST /api/sessions/{id}/investor-information` |
| Investor Profile and Risk Questionnaire Responses | F.1 | F.2 | `model_flows.InvestorProfileAndResponses` |
| Risk Score and Risk Category | F.2 | F.3, X.1 | `model_flows.RiskScoreAndCategory` |
| Profile Interpretation Confirmation (control) | X.1 | F.3 | `profile_interpretation_confirmed` |
| Market Data Request | F.3 | X.2 | `model_flows.MarketDataRequest` |
| Historical Market Data | X.2 | F.3, F.4 | `model_flows.HistoricalMarketData` |
| Target Asset Allocation | F.3 | F.4, F.5 | `model_flows.TargetAssetAllocation` |
| Screened Candidate Securities | F.4 | F.5 | `model_flows.ScreenedCandidateSecurities` |
| Investment Recommendations and Weights | F.5 | F.6 | `model_flows.InvestmentRecommendationsAndWeights` |
| Controls from X.3 and ENV.1 | X.3, ENV.1 | F.1 to F.6 | sections of `config/rules.json`, loaded by `system_administration.load_configuration` |

## Flows between the F.6 functions

| Flow | From | To | Type in code |
| --- | --- | --- | --- |
| Investment Recommendations and Weights | F.5 | F.6.1, F.6.2 | `InvestmentRecommendationsAndWeights` |
| Explanation Rules (control) | X.3 | F.6.1, F.6.2 | `ExplanationRules` |
| Investment Plan Explanation | F.6.1 | F.6.2, X.1 | `InvestmentPlanExplanation` |
| Presented Investment Plan | F.6.2 | X.1 | `PresentedInvestmentPlan` |
| IO.6.1 Reviewed Plan Snapshot | F.6.2 | F.6.3 | `ReviewedPlanSnapshot` |
| Plan Save Request (control) | X.1 | F.6.3, F.6.4, F.6.5 | `PlanSaveRequest` |
| IO.6.2 Authorized Plan Save Payload | F.6.3 | F.6.4 | `AuthorizedPlanSavePayload` |
| IO.6.3 Plan Persistence Result | F.6.4 | F.6.5 | `PlanPersistenceResult` |
| Saved Investment Plan | F.6.5 | X.1 | `SavedInvestmentPlan` |
| Saved Plan Confirmation | F.6.5 | X.1 | `SavedPlanConfirmation` |

The F.6 types are defined in `investment_plan_management/io_types.py`; Investment Recommendations and Weights comes from `model_flows/`.
