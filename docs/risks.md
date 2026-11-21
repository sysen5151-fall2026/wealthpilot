# WealthPilot product risk register

The team confirmed these pre-mitigation ratings as engineering judgments for the course simulation. Likelihood, cost, schedule, and technical impact use the 1–5 scales in the [Innoslate risk table](https://cloud.innoslate.com/cornell/p/813/database/entity/319203). Overall impact is the rounded mean of the three impacts. The priority score is likelihood × overall impact. The [5×5 risk matrix](https://cloud.innoslate.com/cornell/p/813/diagrams/risk/319203) shows the three system scenarios at their pre-mitigation positions.

| Risk | Failure and consequence | L / C / S / T | Impact | Score | Treatment and evidence |
| --- | --- | --- | --- | --- | --- |
| [RA-01](https://cloud.innoslate.com/cornell/p/813/database/entity/319190) | An explanation from F.6.1 contradicts the source allocation, misleading a learner at F.6.2. | 4 / 2 / 4 / 5 | 4 | 16 | Check stated weights against the named asset class or security. A contradiction returns the deterministic explanation and a rejection reason. [RA-T1](https://cloud.innoslate.com/cornell/p/813/database/entity/319202) traces the regression to CS6.1.4.1. |
| [RA-02](https://cloud.innoslate.com/cornell/p/813/database/entity/319191) | The historical snapshot is missing, incompatible or incomplete. F.4 cannot screen reliably. | 3 / 2 / 3 / 4 | 3 | 9 | Apply SR-09 admission and SR-10 limitation disclosure. The missing-snapshot API test confirms plan withholding with a limitation. Review coverage and fingerprint failures separately. |
| [RA-03](https://cloud.innoslate.com/cornell/p/813/database/entity/319192) | Missing or altered F.1 input reaches F.2 and skews the assessment and allocation. | 2 / 2 / 2 / 4 | 3 | 6 | Reject invalid required inputs and verify the assessment basis agrees with accepted input. The invalid age and missing objective API fixture and a profile-basis fixture pass. |

## Additional AI failure modes

These entries trace to [C.6.1 Explanation Engine](https://cloud.innoslate.com/cornell/p/813/database/entity/280580) and the [deployment trade study](https://cloud.innoslate.com/cornell/p/813/database/entity/319193).

| Failure | Control or follow-up |
| --- | --- |
| Model unavailable or slow | The adapter handles unavailable responses with a deterministic fallback. Measure timeout and retry behavior against the explanation allocation before enabling a model for a pilot. |
| Untrusted upstream text enters model context | Use the approved structured plan contract. Review input fields and keep raw provider text and user messages outside the inference payload unless separately approved and validated. |
| Response schema changes | Keep the response shape checks and malformed-response regressions. Rerun contract tests on model or adapter changes. |
| Runtime or model dependency becomes unavailable | Record the tested runtime and model version when selected. Review support and keep the deterministic template available for replay. |
| Investor context crosses the host boundary | The pilot model adapter rejects non-loopback endpoints before any request and refuses redirects. A hosted deployment requires an approved payload and data boundary before use. |

## RA-01 development monitoring

Use `tests/test_explanation_language_model.py` during adapter changes, prompt or model changes, and before the pilot. Record the tested commit, model configuration, number of contradictory fixtures rejected, and number of times the template reached F.6.2. The current gate is zero accepted contradictions in the fixed fixture set. The added cases cover 40/60 reversed allocation, an incorrect 100% allocation and an incorrect grouped holding weight. The check recognizes explicit percentage claims in supported forms. Unrecognized wording and other unsupported claims remain residual risks.
