# 2026-11-11 coursework acceptance update

Verified locally: **131 passed, 0 skipped**. All eight coursework acceptance checks execute; no assertion is replaced by an unconditional pass.

## Method

AI-role coursework execution is described once in SPEC.md. The ten roles use AI-authored scripted responses and actual application requests. This does not establish human comprehension, independent human review or human usability. Original criteria and the original test skeleton remain available for comparison.

## Added working behavior

- Saved-plan contribution comparison: same hypothetical goal and zero-return method, baseline unchanged. The browser comparison was exercised: $180,000 baseline versus $210,000 scenario after increasing monthly contributions from $500 to $600 for 25 years.
- Separate explicit internal simulated-change approval, with duplicate handling and transaction conservation. Saving still does not change the portfolio.
- Baseline freezing, integrity verification and recovery, exercised with two operator processes and two deliberate corruption/recovery runs.
- Thirty seeded historical-data contract cases remain part of N-05.

## Evidence and recording

- evidence/local-pytest.xml: actual local test report.
- evidence/acceptance/coursework-role-report.json: generated observations and method.
- evidence/browser-whatif.png: browser verification.
- docs/recording-guide.md and docs/english-speaker-script.txt: updated test narration.

Run from this project folder: `.venv/bin/python -m pytest -q -rs`.

Hosted CI has not been run for this update. A repository writer must push it and show a successful new Actions run. Innoslate mapping for additional prototypes and team configuration approval remain separate work; this package does not claim to change them.
