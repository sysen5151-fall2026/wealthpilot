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
Prompt: Claude conversation on 2026-11-03 asking for product code that carries out F.6 for the PMC2 demo (investment_plan_management/, portfolio_construction_engine/, requirement-named tests, docs/traceability.md).
Reviewed by: Fangziyue Zhang
Assistant assumptions:
- Plan identity is a hash of the Investment Recommendations and Weights content, so a save request for a superseded plan no longer matches.
- F.5 has no Risk Score input on the IDEF0, so F.3 records the risk score and category in Target Asset Allocation and they travel to F.6.1.
- The Explanation Rules and Portfolio Construction Rules in system_administration/ are placeholder fixtures.
- Each saved plan is one JSON file, written atomically and read back before success is reported.
- The explanation is a deterministic template; no language model is called.
- The code was generated iteratively with full project context, so it is not the Chapter 9 one-pass exercise.
Disposition: Accepting the model becomes a requirement.

## 2026-11-04 — Yicheng Yang — Claude (claude-opus-5-5)
Built from: first-level IDEF0 of F.0 (ICOMs of F.1–F.5); second-level IDEF0 of F.6; UC.1 (UC.1.1–UC.1.20); SPEC.md (SR-01–SR-15, Historical Market Data Contract, Model Response Contract); ADR-0001 (LM Studio); the F.6 code from 2026-11-03.
Prompt: Claude conversation on 2026-11-04 asking for a program that real users can run. Choices made in the conversation: a local web page (FastAPI, SQLite, static front end), UC.1 implemented end to end, a Yahoo Finance price snapshot, placeholder rules, and LM Studio kept with the template as fallback.
Reviewed by: Yicheng Yang
Assistant assumptions:
- Every value in config/rules.json was an assistant placeholder (WP-RULES-0.1-PLACEHOLDER).
- Current holdings count toward the planned amount. The amounts are illustrative, and saving a plan never changes the simulated cash or holdings.
- The loss-tolerance check measures each asset class by its benchmark fund, moves at most 25 points from stocks to bonds, and lists the risk if the limit is still exceeded.
- Individual stocks are offered from the Moderate category up, capped at 5% each.
- Instrument universe: VTI, AAPL, MSFT, TQQQ (excluded as leveraged), VXUS, BND, AGG, BIL.
- A language-model explanation is rejected if it states a number that is not in the supplied facts, drops a limitation or changes the scope notice; the template is used instead.
- The code was generated iteratively with full project context, so it is not the Chapter 9 one-pass exercise.
Disposition: Accepted. Yicheng Yang ran the 108 requirement tests, downloaded the snapshot yahoo-2026-11-04 and ran the app. The assistant then checked the rules on that snapshot and found that moving stocks to bonds barely reduced losses (bonds fell almost as far as stocks in 2022). A follow-up fix keeps the mix unless a move cuts the worst one-year loss by at least 0.5 points, and shows 12.5% shares exactly. Merged to main as PR #6 on 2026-11-04.

## 2026-11-05 — Yicheng Yang — Claude (claude-opus-5-5)
Built from: config/rules.json (WP-RULES-0.1-PLACEHOLDER); the installed snapshot yahoo-2026-11-04; SPEC.md Historical Market Data Contract; yfinance 1.7.0 source.
Prompt: Claude conversation on 2026-11-05 asking the assistant to carry out its three recommended follow-ups: review the placeholder rules (including whether defensive_class should be Cash), add the prompt-log entries, and record the data provider in docs/environment.md.
Reviewed by: Yicheng Yang
Assistant assumptions:
- Keep defensive_class = Bonds with the 0.5-point stop rule. In this snapshot no move passes it, so plans keep their category mix and list the loss-tolerance risk when the stated limit is exceeded. The reasons and the Bonds/Cash comparison are in docs/rules-rationale.md.
- No rule value changed. The configuration becomes WP-RULES-0.2 (allocation rules AR-0.2 for the stop rule added on 2026-11-04), with status "reviewed 2026-11-05, team sign-off pending".
- The Yahoo endpoint recorded in docs/environment.md is the one yfinance 1.7.0 calls, read from the library source.
Disposition: Pending team sign-off of WP-RULES-0.2.
