# Acceptance evidence update 2026-11-11

Local verification: **116 passed, 7 skipped**. N-05 executes real assertions and passes; the other seven need acceptance items are not represented as passed. A successful local run is not a hosted GitHub Actions result.

## Completed

N-05 covers 30 fixed synthetic cases, with exclusion/limitation propagation and analysis withholding checks. The changes harden manifest handling, CSV field handling, exact ISO dates, configured observation counts and common analysis interval coverage. Runtime behavior for the normal bundled snapshot is retained.

N-01 has ten synthetic input/output cases and automated consistency checks. It remains pending because the original criterion requires independent review. Open `evidence/acceptance/N01_独立复核表.html`, have an actual independent reviewer evaluate each case, and copy the exported JSON back to the evidence folder. Completed records must match the current plan baseline; at least nine of ten must pass. The record validator cannot certify the truthfulness of user-entered evidence.

The remaining pilot needs have an unfilled collection template and instructions in `docs/acceptance-next-steps.md`. No reviewers, participants, sign-offs or trial results were invented. N-04 still requires what-if functionality; N-06 requires actual independent reproduction/recovery evidence.

## Tests and evidence

- `tests/test_spec_acceptance.py::test_N05_suitable_historical_data`
- `tests/test_n01_readiness.py`: automated preparation, not N-01 acceptance
- `evidence/acceptance/n05-contract-audit.json`: 30-case report
- `evidence/acceptance/n01-independent-review-packet.json`: actual synthetic outputs with blank independent decisions
- `evidence/acceptance/pilot-records-template.json`: empty participant record slots, not results
- `evidence/local-pytest.xml`: complete local JUnit result

The local review form passed static HTML/JavaScript checks. Agent browser preview was blocked by the browser's local-file policy, so no browser interaction with that form is claimed.

## Commands

From the project root, after the environment is installed:

```bash
.venv/bin/python -m pytest -q -rs
.venv/bin/python -m pytest tests/test_spec_acceptance.py -k N05 -v
.venv/bin/python scripts/acceptance_audit.py
```

The audit preserves any existing N-01 JSON packet rather than overwriting reviewer decisions. Regenerate a changed baseline in a separate folder and arrange a new review, rather than reusing old approval. Restart any running server to load updated runtime code.
