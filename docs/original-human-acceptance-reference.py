"""Task 2 acceptance-test skeleton for WealthPilot.

These acceptance obligations are unfinished at this project increment.
Default runs report them as SKIPPED, never PASSED. To run the retained failing
skeletons, use pytest tests/test_spec_acceptance.py --run-pending-acceptance.
Each test name includes the corresponding stakeholder need ID so that
GitHub Actions provides auditable requirement-to-test traceability.

Later increments should replace each pytest.fail() with executable evidence
without weakening the acceptance criterion in SPEC.md.
"""

import pytest


def test_N01_coherent_planning(tmp_path):
    import json
    from pathlib import Path
    from scripts.acceptance_audit import prepare_n01, validate_n01_review
    packet_path = Path(__file__).resolve().parents[1] / "evidence/acceptance/n01-independent-review-packet.json"
    if not packet_path.exists():
        pytest.skip("N-01 independent review packet has not been prepared")
    packet = json.loads(packet_path.read_text())
    if not all(c.get("independent_review", {}).get("reviewer_id") for c in packet.get("cases", [])):
        pytest.skip("N-01 ten synthetic cases prepared; all ten still require recorded independent review")
    # Rebuild against current code/rules so an old review cannot certify a changed baseline.
    fresh = prepare_n01(tmp_path)
    assert [(c["case_id"],c["plan_id"],c["synthetic_input"],c["display_text"]) for c in packet["cases"]] == [
        (c["case_id"],c["plan_id"],c["synthetic_input"],c["display_text"]) for c in fresh["cases"]]
    validate_n01_review(packet)


def test_N02_comprehension():
    pytest.fail(
        "N-02 unmet: implement evidence for novice rationale and material-risk comprehension thresholds."
    )


def test_N03_user_control():
    pytest.fail(
        "N-03 unmet: verify explicit save confirmation, unchanged simulated state, and separate change approval."
    )


def test_N04_goal_based_exploration():
    pytest.fail(
        "N-04 unmet: verify what-if creation, saved-baseline preservation, and goal-effect explanation."
    )


def test_N05_suitable_historical_data(tmp_path):
    from scripts.acceptance_audit import audit_n05
    result = audit_n05(tmp_path)
    assert result["passed"] == result["total"] == 30


def test_N06_reproducible_operation():
    pytest.fail(
        "N-06 unmet: verify independent reproduction and controlled recovery from the approved baseline."
    )


def test_N07_honest_educational_scope():
    pytest.fail(
        "N-07 unmet: verify learner scope recognition and 100% interface-boundary integrity."
    )


def test_N08_usable_educational_exercise():
    pytest.fail(
        "N-08 unmet: verify the 8/10 independent UC.1 completion threshold and record assistance events."
    )
