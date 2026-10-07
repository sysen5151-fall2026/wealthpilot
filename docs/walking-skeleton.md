# UC.1 — Investor obtains a simulated investment plan and candidate securities

The walking skeleton below mirrors the current UC.1 model and preserves the educational-simulation boundary.

1. **UC.1.1** Individual Investor → WealthPilot: Initiate Session
2. **UC.1.2** WealthPilot → Individual Investor: Request Financial Profile
3. **UC.1.3** Individual Investor → WealthPilot: Provide Financial Profile
4. **UC.1.4** WealthPilot → Individual Investor: Request Risk Responses
5. **UC.1.5** Individual Investor → WealthPilot: Provide Risk Responses
6. **UC.1.6** WealthPilot → Individual Investor: Request Current Holdings
7. **UC.1.7** Individual Investor → WealthPilot: Provide Current Holdings (hypothetical / simulated planning input)
8. **UC.1.8** WealthPilot: Determine Risk Score
9. **UC.1.9** WealthPilot → Individual Investor: Present Risk Assessment
10. **UC.1.10** Individual Investor → WealthPilot: Confirm Profile Interpretation
11. **UC.1.11** WealthPilot → Market Data Provider: Request Market Data
12. **UC.1.12** Market Data Provider → WealthPilot: Provide Market Data
13. **UC.1.13** WealthPilot: Determine Target Allocation
14. **UC.1.14** WealthPilot: Filter Candidate Securities
15. **UC.1.15** WealthPilot: Explain Plan Rationale and Risks
16. **UC.1.16** WealthPilot → Individual Investor: Present Investment Plan
17. **UC.1.17** Individual Investor → WealthPilot: Request Plan Save
18. **UC.1.18** WealthPilot: Save Plan and Confirm
19. **UC.1.19** Individual Investor: Review Saved Plan

No step connects to a brokerage or custodian, and no step executes a real transaction.

## Current Walking-Skeleton Implementation

The current Python implementation exercises the primary UC.1 path with hard-coded or stubbed participant behavior. It includes financial-profile and risk-response inputs, hypothetical current holdings, risk assessment, profile-interpretation confirmation, historical market data, target allocation, candidate-security filtering, educational explanation, plan presentation, plan-save request, and simulated plan saving.

The implementation is a walking skeleton rather than full acceptance verification. Historical market data, risk calculation, allocation, screening, explanation, confirmations, holdings, and plan saving remain stubbed or hard-coded at this increment.
