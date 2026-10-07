# WealthPilot

## Operational Concept

WealthPilot is an **educational investment-planning simulator for novice investors**. It does not connect to a real brokerage account, place real trades, transfer funds, or authorize real investment execution.

An Individual Investor starts a planning session and provides a financial profile, including a stated goal, investment horizon, financial capacity, liquidity needs, investment experience, and hypothetical current holdings. The investor also completes a structured risk questionnaire. WealthPilot uses these inputs to determine a risk score and corresponding risk level.

WealthPilot requests historical market data from a Market Data Provider, determines a target allocation, filters candidate securities, and presents a simulated educational investment plan. The plan includes the target allocation, candidate securities, material risks, and an explanation of how the investor profile and risk assessment influenced the result. The investor confirms the profile interpretation and can request that the simulated plan be saved.

The saved plan remains separate from later simulated portfolio actions. Additional course use cases support simulated recurring planning, simulated portfolio drift/rebalancing review, what-if analysis, and administrative maintenance. A System Administrator manages approved educational baselines and recovery. Market and regulatory conditions constrain the simulator through the Market and Regulatory Environment.

## Task 2 / Chapter 3 Repository Artifacts

- `SPEC.md` — stakeholder needs, traces to stakeholder requirements, acceptance criteria, Data Contract, and Model Response Contract.
- `tests/test_spec_acceptance.py` — intentionally failing acceptance-test skeletons for N-01 through N-08.
- `.github/workflows/tests.yml` — CI workflow that runs the Task 2 acceptance tests.
- `docs/prompt-log.md` — cumulative prompt log, including AI-assisted repository and walking-skeleton updates.

The acceptance suite is intentionally **red** at this project increment. Later build increments should replace the placeholder failures with executable evidence as the corresponding capabilities are implemented.
