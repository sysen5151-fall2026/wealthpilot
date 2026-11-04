# Prompt Log
## 2026-09-19 — [Yicheng Yang] — [claude code]
Built from: docs/context.md; no requirements exist yet.
Prompt: prompts/2026-09-19-ch1-scaffold.md
Reviewed by: [Fangziyuea Zhang]
Assistant assumptions: None.
## 2026-10-04 — Yicheng Yang — ChatGPT (GPT-5.6 Sol)
Built from: approved Task 2 stakeholder needs N-01 through N-08; stakeholder requirements SR-01 through SR-15; final Innoslate traceability; existing repository scaffold.
Prompt: Inspect the current WealthPilot repository against the Chapter 3 / Task 2 product-build requirements and prepare repository-ready changes for SPEC.md, acceptance tests, GitHub Actions CI, prompt logging, and scope consistency.
Reviewed by: Yicheng Yang and Fangziyue Zhang — team review required before commit.
Assistant assumptions: Historical-market-data and model-response contracts are target contracts. The current scaffold uses hard-coded market data and a fixed explanation string, so it does not yet satisfy those contracts. LM Studio is the intended local runner, but the exact open-source model is not yet selected/integrated.
Disposition: Retain the N-xx/SR-xx traceability and acceptance thresholds from the approved Task 2 report. Keep the Task 2 acceptance tests intentionally failing at this increment. Remove the stale brokerage/custodian execution scope from repository documentation. Confirm future provider-specific field mappings and the selected local model before implementation.

## 2026-10-06 — Yicheng Yang — ChatGPT (GPT-5.6 Sol)
Built from: current WealthPilot UC.1 model, repository walking skeleton, Milestone 1 self-assessment criteria, and reviewer feedback.
Prompt: Review the runnable walking skeleton against UC.1 and identify code changes needed to align the implementation with the modeled nominal flow and educational-simulation boundary.
Reviewed by: Yicheng Yang.
Assistant assumptions: Current participant implementations may remain hard-coded or stubbed because the Milestone 1 walking-skeleton criterion permits stubbed participants.
Disposition: Added hypothetical current holdings; aligned profile-interpretation confirmation with UC.1.10; aligned plan-save functions with UC.1.17–UC.1.18; removed unmodeled rejection branches; changed output terminology from recommendations to candidate securities; and added explicit simulated educational output labels.

## 2026-10-06 — Yicheng Yang — ChatGPT (GPT-5.6 Sol)
Built from: Milestone 1 Canvas self-assessment, Task 1 UC.1/OpsCon evidence, Task 2 stakeholder-needs and requirements evidence, and the updated repository.
Prompt: Review the Milestone 1 self-assessment for inconsistencies between claimed ratings, MBSE evidence, repository behavior, and live demonstration output.
Reviewed by: Yicheng Yang.
Assistant assumptions: Self-ratings should not exceed the evidence currently available in the model and repository.
Disposition: Use Proficient rather than Exemplary where the evidence does not support the higher rubric threshold; make UC.1 step references explicit; distinguish traced-to, satisfied-by, and RVTM evidence; and ensure self-assessment wording matches the runnable walking skeleton.
## 2026-11-03 — Yicheng Yang — Claude (claude-opus-5-5)
Built from: Innoslate second-level IDEF0 of F.6 (F.6.1–F.6.5 performed by C.6.1–C.6.5; internal flows IO.6.1–IO.6.3); CS.6 component specification (CS6.1.1.1–CS6.1.4.5, CS6.2.1–CS6.2.4); first-level ICOMs of F.5; SPEC.md Model Response Contract.
Prompt: Claude conversation on 2026-11-03 asking for product code that carries out F.6 for the PMC2 demo (investment_plan_management/, portfolio_construction_engine/, requirement-named tests, docs/traceabilitqy.md).
Reviewed by: Fangziyue Zhang
Assistant assumptions:
- Plan identity is a hash of the Investment Recommendations and Weights content, so a save request for a superseded plan no longer matches.
- F.5 has no Risk Score input on the IDEF0, so F.3 records the risk score and category in Target Asset Allocation and they travel to F.6.1.
- The Explanation Rules and Portfolio Construction Rules in system_administration/ are placeholder fixtures.
- Each saved plan is one JSON file, written atomically and read back before success is reported.
- The explanation is a deterministic template; no language model is called.
- The code was generated iteratively with full project context, so it is not the Chapter 9 one-pass exercise.
Disposition: Accepting the model becomes a requirement.