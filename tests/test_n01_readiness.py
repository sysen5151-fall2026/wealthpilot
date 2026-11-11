"""Preparation evidence only; N-01 still requires independent review."""
from scripts.acceptance_audit import prepare_n01
from scripts.acceptance_audit import validate_n01_review
import pytest


def test_SR_01_ten_synthetic_profiles_are_ready_for_independent_review(tmp_path):
    packet = prepare_n01(tmp_path)
    assert packet["automated_cases_passed"] == 10
    assert packet["status"] == "READY_FOR_INDEPENDENT_REVIEW_NOT_ACCEPTED"
    assert all(c["independent_review"]["reviewer_id"] is None for c in packet["cases"])
    with pytest.raises(AssertionError, match="real reviewer"):
        validate_n01_review(packet)
