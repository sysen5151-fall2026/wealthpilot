# Milestone 2 evidence update

Prepared 2026-11-08 from the supplied wealthpilot-main.zip. This is a local update, not a pushed or merged GitHub change.

## Added

- `contracts/api-v1.yaml`: generated implemented HTTP API plus five F.6 callable contracts, ICOMs, schema definitions and internal flow endpoints.
- `scripts/export_api_contract.py`: reproducible contract export from the actual code.
- `tests/test_model_contract.py`: four drift, signature, payload-schema and continuity checks.
- `docs/route-table.md`: product action to route, UC.1 step, function, asset and evidence.
- `docs/requirements-flowdown.md`: implementation mapping and a proposed equivalence rationale, with explicit cloud-model checks outstanding.
- `docs/model-recording-checklist.md`: physical architecture, second-level function/asset hierarchy and requirement-link checklist.
- `docs/recording-guide.md`, `docs/english-speaker-script.txt`, `录屏指南.html`: Chinese recording cues and English spoken script for about ten minutes, including webcam instructions.
- `Launch_WealthPilot.command`: macOS setup/start helper. It installs into a local .venv and starts on 127.0.0.1:8000.
- `evidence/`: local pytest XML and a browser save-confirmation screenshot; neither is a hosted CI result.

## Changed

- Renamed `tests/test_cs6_requirements.py` to `tests/test_functional_requirements.py`, retaining all existing assertions and test names. Updated its import in `test_explanation_language_model.py` and documentation references.
- Default collection reports eight unfinished stakeholder acceptance skeletons as skipped with a reason. Their original failing assertions remain executable using `--run-pending-acceptance`; no acceptance obligation has been marked passed.
- Replaced the workflow with implemented-requirement, contract, integration and explicit pending-acceptance steps; JUnit reports are retained even on failure.
- Added pinned PyYAML and jsonschema verification dependencies.
- Updated README, environment notes and traceability navigation.

## Validation

- Selected functional and contract suites: 34 passed.
- Full default suite: 114 passed, 8 skipped.
- Browser walkthrough: fictional inputs → score 70 → plan → explicit save → unchanged cash/holdings → saved-plan reopening.
- Launch helper passed shell syntax validation; first-time setup instructions use the dependencies installed during this review.

## Not claimed

This update does not contain a successful hosted Actions run, live cloud-model edits, team approval of rule values, a 100-run performance evaluation, novice trials, a recording, or a Canvas submission. The currently connected GitHub account has read-only access to the course repository; a writer must merge/push the update and obtain the hosted CI evidence.

Merge this update into the latest repository using this list. Do not replace newer teammate work with an older ZIP baseline. Preserve `.github/workflows/tests.yml`, including the leading dot in the folder name.
