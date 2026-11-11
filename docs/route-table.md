# UC.1 product routes and model responsibilities

The browser is a single-page interface served at `/`. Its four views are UI states, not separate server pages. HTTP paths below are implemented in `wealthpilot_service/api.py`. They serve UC.1; UC.2 through UC.5 are not implemented. F.6 is the proposed Milestone 2 demonstration function; confirm that it matches the classroom demonstration.

| Product entry or visible action | Actual HTTP route | Use case step | Model responsibility | Requirement evidence |
| --- | --- | --- | --- | --- |
| Open WealthPilot | `GET /`, `GET /api/status` | Before UC.1 | C.0 supplies UI, scope notice, configuration and data status | SR-13; `test_SR_13_every_planning_response_carries_the_scope_notice` |
| Start planning | `POST /api/sessions` | UC.1.1 and initial requests | F.1 / C.1 | 1.4.1; `test_session_returns_requests_for_investor_input` |
| About you and Your answers; See my risk profile | `POST /api/sessions/{session_id}/investor-information` | UC.1.2–UC.1.9 | F.1 / C.1; F.2 / C.2 | 1.4.1, 1.4.2; `tests/test_uc1_functions.py` |
| Your risk profile; Yes, build my plan | `POST /api/sessions/{session_id}/plan` with confirmed interpretation | UC.1.10–UC.1.17 | F.3–F.5 then F.6.1 / C.6.1 and F.6.2 / C.6.2 | 1.4.3–1.4.6; CS6.1.4.1–CS6.1.4.2 |
| Your simulated plan; Save this simulated plan | `POST /api/sessions/{session_id}/plan-save-requests` with matching `plan_id` and `action: save` | UC.1.18–UC.1.19 | F.6.3 / C.6.3 → F.6.4 / C.6.4 → F.6.5 / C.6.5 | 1.4.7, 1.4.8, 1.2.7; CS6.1.4.3–CS6.1.4.5 |
| See saved plans | `GET /api/saved-plans` | UC.1.20 | C.0 read-only retrieval through C.6.4 repository | CS6.2.3; `test_SR_04_SR_05_nothing_is_saved_without_an_explicit_request_and_saving_moves_nothing` |
| Open a saved plan | `GET /api/saved-plans/{plan_id}` | UC.1.20 | C.6.4 read-only retrieval | CS6.2.3; saved content equals the presented snapshot |

## F.6 internal operations

`contracts/api-v1.yaml` records five Python calls under `x-model-operations` and serialized payload schemas under `components.schemas`. Three internal flows IO.6.1–IO.6.3 and the explanation interface IF.6.1 are listed under `x-model-flows`. These are local server calls, not five additional HTTP endpoints. Model interface IDs come from module documentation and need comparison with the current Innoslate baseline before recording.

## Off-nominal behavior

- Invalid investor input produces a validation response; rejected profile confirmation cannot release a plan.
- Missing historical data may yield HTTP 200 with `status: withheld`; the UI discloses the limitation rather than showing a valid plan.
- A save request may yield HTTP 200 with a domain status such as `not_authorized`; HTTP success alone does not prove persistence.
- Failed or rejected persistence cannot produce Saved Plan Confirmation. Component tests exercise these paths without damaging the demo database.
- Viewing a plan is not authorization to save it. No brokerage action is provided.

## Additional coursework prototypes

| Actual operation | Module | Scope and verification |
| --- | --- | --- |
| POST /api/saved-plans/{plan_id}/what-if | wealthpilot_service/exploration.py:compare_goal_scenario | Saved baseline preserved; zero-return contribution comparison. tests/test_exploration.py and N-04. |
| POST /api/sessions/{session_id}/simulated-change-approvals | wealthpilot_service/exploration.py:apply_approved_change | Separate explicit approval; internal SQLite ledger only; no brokerage. tests/test_exploration.py and N-03. |
| Baseline freeze/restore | scripts/baseline_recovery.py | Two-process reproducibility and two corruption/recovery exercises; N-06. |

These prototype operations do not alter the existing F.6 cloud allocation. Map their functions and requirements in Innoslate before claiming model-to-product coverage beyond the recorded UC.1/F.6 path.
