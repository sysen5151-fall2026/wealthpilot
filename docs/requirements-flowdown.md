# F.6 requirements and allocation evidence

This is the implementation-side mapping. It does not establish that the current cloud model contains every link or that a reviewer has approved the allocation. Before recording, verify exact IDs, statements, relationships and component assignments in Innoslate. Retain a screenshot or export of that baseline with the video.

## Functional and component chain

| Parent system functional obligation | Function and asset | Component requirement recorded in code | Executable evidence |
| --- | --- | --- | --- |
| 1.4.6 Present Investment Plan Explanation | F.6.1 / C.6.1 | CS6.1.4.1 explanation; CS6.1.2.1 output | `test_CS6_1_4_1_explanation_has_rationale_and_risk` |
| F.6 presentation responsibility; confirm exact parent requirement link in Innoslate | F.6.2 / C.6.2 | CS6.1.4.2; CS6.1.1.2 input consistency | `test_CS6_1_4_2_presented_plan_matches_recommendations` |
| 1.4.7 Save Presented Investment Plan | F.6.3 / C.6.3 and F.6.4 / C.6.4 | CS6.1.4.3 authorization; CS6.1.4.4 persistence | `test_CS6_1_4_3_only_valid_matching_request_authorizes`; `test_CS6_1_4_4_persisted_plan_matches_payload` |
| 1.4.8 Preserve Simulated Portfolio State During Plan Save | F.6.4 / C.6.4 | State preservation in CS6.1.4.4 implementation | `test_CS6_1_4_4_save_leaves_simulated_portfolio_unchanged` |
| 1.2.7 Provide Saved Plan Confirmation | F.6.5 / C.6.5 | CS6.1.4.5; CS6.1.2.3 and CS6.1.2.4 outputs | `test_CS6_1_4_5_confirms_only_successful_save`; `test_CS6_1_4_5_unsuccessful_result_gets_no_confirmation` |

Tests are in `tests/test_functional_requirements.py`. Payload schemas and endpoints are in `contracts/api-v1.yaml`. Conduit/interface requirements CS6.1.3.1–CS6.1.3.3 still require inspection of the actual model; payload-schema tests do not establish conduit properties.

## Proposed system-wide allocation for the video

Use the educational-simulation safety obligation, previously recorded as NFR-04, only after confirming its current name and wording in Innoslate. Its intended condition is zero real transactions or modifications to actual brokerage accounts. The code records CS6.2.4 as the C.6 simulation-only interface obligation.

**Method: equivalence for the applicable simulation-only constraint.** C.6 inherits the prohibition unchanged: plan delivery may explain, present and save an educational plan, but may not turn that process into real trading. This is a categorical boundary condition with no numeric budget to divide, so apportionment does not apply to this example. No combination of relaxed component conditions is proposed, so synthesis is not the intended argument. Equivalence concerns the inherited prohibition within C.6's scope, not every aspect of system safety.

Evidence includes `test_CS6_2_4_only_simulation_controls_are_offered`, `test_SR_14_learner_interface_offers_no_brokerage_controls`, and the unchanged-portfolio test. These checks cover the stated UI and save paths; they are not a complete security audit.

In Innoslate, show the system-wide requirement, the component requirement under C.6, and the relationship recording the allocation. Record the method and rationale in the model's supported attribute or description. Do not claim this cloud link was added by the repository update.

## Outstanding evidence

- CS6.2.1 timing over 100 runs: no verified performance result is supplied here.
- CS6.2.2 empirical novice comprehension is not established by scripted AI-role answers.
- N-01–N-08 coursework checks execute under the adapted AI-role method in SPEC.md. N-05 runs 30 seeded contract cases. Original human-study targets remain reference obligations.
- Team sign-off on `config/rules.json` remains pending; maintenance does not constitute approval.
- Obtain a GitHub Actions run after committing the update. Local pytest output is not hosted CI evidence.
