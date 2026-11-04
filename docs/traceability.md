# Traceability: model functions to code

Transcribed from the Innoslate model (Financial Project, read 2026-11-03). One row per function on the first-level IDEF0 of F.0 and on the second-level IDEF0 of F.6. `wealthpilot_service/` has no row: it is the C.0 orchestration that calls these functions in UC.1 order, not a function on the IDEF0.

| Function | Performed by | Module | Code | Requirements | Tests |
| --- | --- | --- | --- | --- | --- |
| F.1 Collect Investor Information | C.1 Investor Information Interface | `investor_interface/` | `request_financial_profile`, `provide_risk_questionnaire_response`, `provide_current_holdings` (stubs) | 1.4.1 | pending |
| F.2 Assess Investor Risk Profile | C.2 Risk Assessment Engine | `risk_engine/` | `assess_investor_risk_profile` (stub) | 1.4.2 | pending |
| F.3 Determine Target Asset Allocation | C.3 Asset Allocation Engine | `allocation_engine/` | `determine_target_asset_allocation` (stub) | 1.4.3 | pending |
| F.4 Screen Candidate Securities | C.4 Security Screening Engine | `screening_engine/` | `screen_candidate_securities` (stub) | 1.4.4 | pending |
| F.5 Generate Investment Recommendations | C.5 Portfolio Construction Engine | `portfolio_construction_engine/` | `generate_investment_recommendations` | 1.4.5 | pending |
| F.6 Manage Investment Plan Delivery | C.6 Investment Plan Management Subsystem | `investment_plan_management/` | decomposed into F.6.1 to F.6.5 | 1.1.8, 1.2.7, 1.4.6, 1.4.7, 1.4.8; CS6.1.3.1 to CS6.1.3.3; CS6.2.1 to CS6.2.4 | `test_CS6_2_3_*`, `test_CS6_2_4_*` |
| F.6.1 Explain Investment Plan | C.6.1 Explanation Engine | `investment_plan_management/explanation_engine.py` | `explain_investment_plan` | CS6.1.4.1, CS6.1.1.1, CS6.1.1.2, CS6.1.2.1 | `test_CS6_1_4_1_*`, `test_CS6_1_2_1_*` |
| F.6.2 Present Investment Plan | C.6.2 Plan Presentation Component | `investment_plan_management/plan_presentation.py` | `present_investment_plan` | CS6.1.4.2, CS6.1.1.2, CS6.1.2.2 | `test_CS6_1_4_2_*`, `test_CS6_1_1_2_*` |
| F.6.3 Validate Explicit Plan Save Request | C.6.3 Save Authorization Component | `investment_plan_management/save_authorization.py` | `validate_explicit_plan_save_request` | CS6.1.4.3, CS6.1.1.3 | `test_CS6_1_4_3_*`, `test_CS6_1_1_3_*` |
| F.6.4 Persist Reviewed Investment Plan | C.6.4 Plan Repository Component | `investment_plan_management/plan_repository.py` | `persist_reviewed_investment_plan` | CS6.1.4.4, CS6.1.1.3 | `test_CS6_1_4_4_*` |
| F.6.5 Confirm Successful Plan Save | C.6.5 Save Confirmation Component | `investment_plan_management/save_confirmation.py` | `confirm_successful_plan_save` | CS6.1.4.5, CS6.1.1.3, CS6.1.2.3, CS6.1.2.4 | `test_CS6_1_4_5_*` |

All tests named here are in `tests/test_cs6_requirements.py`. Not covered by automated tests yet: CS6.2.1 (2-second timing over 100 runs), CS6.2.2 (novice comprehension study), and CS6.1.3.1 to CS6.1.3.3 (verified by inspecting the conduits in the model).

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

All types are defined in `investment_plan_management/io_types.py`.
