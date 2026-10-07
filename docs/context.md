# External System and Stakeholder Boundary Inventory

This file reflects the approved educational-simulator scope used in the current WealthPilot model.

- **C.0 WealthPilot** — system of interest. Produces educational planning and internal-simulation outputs; it does not execute real trades or transfer real funds.
- **X.1 Individual Investor** — in/out. Provides financial profile, structured risk responses, hypothetical current holdings, confirmations, and simulated approvals; receives risk assessment, target allocation, candidate securities, rationale, risks, saved-plan status, and what-if results.
- **X.2 Market Data Provider** — in/out. Receives historical-market-data requests and returns historical price data and related metadata for educational analysis.
- **X.3 System Administrator** — in/out. Provides approved configuration, baseline, recovery, and maintenance actions; receives system status and reproducibility/recovery results.
- **ENV.1 Market and Regulatory Environment** — constraining environment. Provides market and regulatory constraints represented as controlled model inputs; it does not provide transaction instructions.

Stakeholders such as the Financial Education Sponsor and Pilot Assurance Reviewer are represented in the stakeholder analysis and requirements traceability but are not modeled as operational transaction interfaces to WealthPilot.
