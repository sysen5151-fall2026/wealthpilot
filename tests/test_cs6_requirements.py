"""Requirement tests for C.6 Investment Plan Management Subsystem.

Each test name starts with the ID of the CS.6 component requirement it checks,
as written in the Innoslate component specification. Fixtures are fixed, and
saved plans go to pytest's temporary folder, so no test touches a real account
or the repository folder.

Not covered here: CS6.2.1 (2-second timing over 100 runs) and CS6.2.2 (novice
comprehension study) need a performance run and a usability session, and
CS6.1.3.1 to CS6.1.3.3 are verified by inspecting the conduits in the model.
"""

import json
from dataclasses import asdict, replace

import pytest

from investment_plan_management import (
    EXPLICIT_SAVE,
    FAILED,
    REJECTED,
    SUCCEEDED,
    InvestmentRecommendationsAndWeights,
    JsonPlanStore,
    PlanSaveRequest,
    Recommendation,
    confirm_successful_plan_save,
    explain_investment_plan,
    persist_reviewed_investment_plan,
    present_investment_plan,
    validate_explicit_plan_save_request,
)
from system_administration import get_explanation_rules
from wealthpilot_service import run_investment_planning_session

RULES = get_explanation_rules()


def make_recommendations(**changes) -> InvestmentRecommendationsAndWeights:
    plan = InvestmentRecommendationsAndWeights(
        risk_score=65,
        risk_category="Moderate",
        target_allocation={"Stocks": 0.6, "ETFs": 0.4},
        recommendations=[
            Recommendation("AAPL", "Stocks", 0.3),
            Recommendation("MSFT", "Stocks", 0.3),
            Recommendation("VTI", "ETFs", 0.4),
        ],
        identified_risks=["market_volatility", "concentration"],
        data_limitations=["Prices come from a fixed historical sample, not live market data."],
    )
    return replace(plan, **changes)


def explain_and_present(recommendations=None):
    recommendations = recommendations or make_recommendations()
    explanation = explain_investment_plan(recommendations, explanation_rules=RULES)
    presented, snapshot = present_investment_plan(
        recommendations, explanation, explanation_rules=RULES
    )
    return recommendations, explanation, presented, snapshot


def explicit_request(snapshot, **changes) -> PlanSaveRequest:
    request = PlanSaveRequest(request_id="req-1", plan_id=snapshot.plan_id, action=EXPLICIT_SAVE)
    return replace(request, **changes)


def authorize(snapshot):
    request = explicit_request(snapshot)
    return request, validate_explicit_plan_save_request(snapshot, plan_save_request=request)


class FailingStore(JsonPlanStore):
    def write(self, plan_id, record):
        raise OSError("disk full")


class PartialWriteStore(JsonPlanStore):
    """Writes only the first half of the file, as an interrupted write would."""

    def write(self, plan_id, record):
        self.directory.mkdir(parents=True, exist_ok=True)
        text = json.dumps(record)
        self._path(plan_id).write_text(text[: len(text) // 2])


# F.6.1 Explain Investment Plan

def test_CS6_1_4_1_explanation_has_rationale_and_risk():
    recommendations, explanation, _, _ = explain_and_present()

    assert explanation.plan_id == recommendations.plan_id
    assert explanation.summary
    assert "Moderate" in explanation.allocation_rationale[0]
    assert "65" in explanation.allocation_rationale[0]
    assert any("AAPL 30%" in line for line in explanation.allocation_rationale)
    assert len(explanation.material_risks) >= 1
    assert set(explanation.material_risks) <= set(RULES.risk_language.values())
    assert explanation.data_limitations == recommendations.data_limitations
    assert explanation.scope_notice == RULES.scope_notice


def test_CS6_1_4_1_plan_without_identified_risk_is_not_explained():
    with pytest.raises(ValueError):
        explain_investment_plan(make_recommendations(identified_risks=[]), explanation_rules=RULES)


def test_CS6_1_4_1_risk_without_novice_wording_is_not_explained():
    with pytest.raises(ValueError):
        explain_investment_plan(
            make_recommendations(identified_risks=["liquidity"]), explanation_rules=RULES
        )


def test_CS6_1_4_1_wording_that_breaks_the_rules_is_rejected():
    strict_rules = replace(RULES, prohibited_phrases=["simulated plan"])
    with pytest.raises(ValueError):
        explain_investment_plan(make_recommendations(), explanation_rules=strict_rules)


# F.6.2 Present Investment Plan

def test_CS6_1_4_2_presented_plan_matches_recommendations():
    recommendations, _, presented, snapshot = explain_and_present()
    lines = presented.display_text.splitlines()

    assert presented.plan_id == snapshot.plan_id == recommendations.plan_id
    assert snapshot.recommendations == recommendations.recommendations
    assert snapshot.target_allocation == recommendations.target_allocation
    for r in recommendations.recommendations:
        assert any(r.symbol in line and f"{r.weight:.0%}" in line for line in lines)
    assert RULES.scope_notice in presented.display_text
    assert presented.learner_actions == RULES.learner_actions


def test_CS6_1_2_1_explanation_of_another_plan_is_not_presented():
    other_plan = make_recommendations(risk_category="Conservative")
    explanation = explain_investment_plan(other_plan, explanation_rules=RULES)
    with pytest.raises(ValueError):
        present_investment_plan(make_recommendations(), explanation, explanation_rules=RULES)


def test_CS6_1_1_2_explanation_and_presentation_use_the_same_rules_version():
    recommendations = make_recommendations()
    explanation = explain_investment_plan(recommendations, explanation_rules=RULES)
    with pytest.raises(ValueError):
        present_investment_plan(
            recommendations, explanation, explanation_rules=replace(RULES, version="ER-2")
        )


# F.6.3 Validate Explicit Plan Save Request

@pytest.mark.parametrize(
    "make_request",
    [
        lambda snapshot: None,
        lambda snapshot: explicit_request(snapshot, action="view"),
        lambda snapshot: explicit_request(snapshot, action="open"),
        lambda snapshot: explicit_request(snapshot, action="close"),
        lambda snapshot: explicit_request(snapshot, request_id=""),
        lambda snapshot: explicit_request(snapshot, plan_id="plan-0000000000"),
    ],
    ids=["absent", "view-event", "open-event", "close-event", "no-request-id", "other-plan"],
)
def test_CS6_1_4_3_invalid_requests_produce_no_payload(make_request):
    _, _, _, snapshot = explain_and_present()
    request = make_request(snapshot)
    assert validate_explicit_plan_save_request(snapshot, plan_save_request=request) is None


def test_CS6_1_4_3_request_for_a_superseded_plan_produces_no_payload():
    _, _, _, old_snapshot = explain_and_present()
    newer = make_recommendations(
        target_allocation={"Stocks": 0.4, "ETFs": 0.6},
        recommendations=[
            Recommendation("AAPL", "Stocks", 0.2),
            Recommendation("MSFT", "Stocks", 0.2),
            Recommendation("VTI", "ETFs", 0.6),
        ],
    )
    _, _, _, new_snapshot = explain_and_present(newer)
    stale_request = explicit_request(old_snapshot)
    assert validate_explicit_plan_save_request(new_snapshot, plan_save_request=stale_request) is None


def test_CS6_1_4_3_only_valid_matching_request_authorizes():
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)

    assert payload is not None
    assert payload.reviewed_plan == snapshot
    assert payload.authorization == request


# F.6.4 Persist Reviewed Investment Plan

def test_CS6_1_4_4_persisted_plan_matches_payload(tmp_path):
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)

    result = persist_reviewed_investment_plan(
        payload, plan_save_request=request, plan_store=JsonPlanStore(tmp_path)
    )

    assert result.status == SUCCEEDED
    on_disk = json.loads((tmp_path / f"{snapshot.plan_id}.json").read_text())
    assert on_disk == asdict(snapshot) == result.persisted_plan


def test_CS6_1_4_4_unauthorized_save_is_rejected(tmp_path):
    _, _, _, snapshot = explain_and_present()
    _, payload = authorize(snapshot)
    different_request = explicit_request(snapshot, request_id="req-2")

    result = persist_reviewed_investment_plan(
        payload, plan_save_request=different_request, plan_store=JsonPlanStore(tmp_path)
    )

    assert result.status == REJECTED
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "store_class", [FailingStore, PartialWriteStore], ids=["write-error", "partial-write"]
)
def test_CS6_1_4_4_failed_write_is_not_reported_as_success(tmp_path, store_class):
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)

    result = persist_reviewed_investment_plan(
        payload, plan_save_request=request, plan_store=store_class(tmp_path)
    )

    assert result.status == FAILED
    assert result.persisted_plan is None


def test_CS6_1_4_4_save_leaves_simulated_portfolio_unchanged(tmp_path):
    portfolio = tmp_path / "simulated_portfolio.json"
    portfolio.write_text(json.dumps({"cash": 20000, "holdings": [{"ticker": "VTI", "value": 5000}]}))
    before = portfolio.read_bytes()
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)

    persist_reviewed_investment_plan(payload, plan_save_request=request, plan_store=JsonPlanStore(tmp_path))

    assert portfolio.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        ["simulated_portfolio.json", f"{snapshot.plan_id}.json"]
    )


# F.6.5 Confirm Successful Plan Save

@pytest.fixture
def successful_save(tmp_path):
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)
    result = persist_reviewed_investment_plan(
        payload, plan_save_request=request, plan_store=JsonPlanStore(tmp_path)
    )
    return request, result


def test_CS6_1_4_5_confirms_only_successful_save(successful_save):
    request, result = successful_save

    saved_plan, confirmation = confirm_successful_plan_save(result, plan_save_request=request)

    assert saved_plan.plan_id == confirmation.plan_id == request.plan_id
    assert confirmation.request_id == request.request_id
    assert saved_plan.content == result.persisted_plan


@pytest.mark.parametrize("status", [REJECTED, FAILED, "pending", "indeterminate"])
def test_CS6_1_4_5_unsuccessful_result_gets_no_confirmation(successful_save, status):
    request, result = successful_save
    unsuccessful = replace(result, status=status)
    assert confirm_successful_plan_save(unsuccessful, plan_save_request=request) is None


def test_CS6_1_4_5_result_for_another_request_gets_no_confirmation(successful_save):
    request, result = successful_save
    other_request = replace(request, request_id="req-2")
    assert confirm_successful_plan_save(result, plan_save_request=other_request) is None


# C.6 as a whole, through the UC.1 run

def test_CS6_2_3_plan_identity_and_content_preserved_end_to_end(tmp_path):
    outcome = run_investment_planning_session(save_requested=True, plan_store=JsonPlanStore(tmp_path))

    plan_id = outcome.presented_plan.plan_id
    on_disk = json.loads((tmp_path / f"{plan_id}.json").read_text())
    assert outcome.saved_plan.plan_id == outcome.confirmation.plan_id == plan_id
    assert outcome.saved_plan.content == on_disk
    for r in on_disk["recommendations"]:
        assert f"{r['symbol']}" in outcome.presented_plan.display_text


def test_CS6_1_1_3_no_save_request_means_nothing_saved(tmp_path):
    outcome = run_investment_planning_session(save_requested=False, plan_store=JsonPlanStore(tmp_path))

    assert outcome.saved_plan is None
    assert outcome.confirmation is None
    assert list(tmp_path.iterdir()) == []


def test_CS6_2_4_only_simulation_controls_are_offered(tmp_path):
    outcome = run_investment_planning_session(save_requested=True, plan_store=JsonPlanStore(tmp_path))

    assert outcome.presented_plan.learner_actions == ["Save this simulated plan"]
    for text in (outcome.presented_plan.display_text, outcome.confirmation.message):
        assert RULES.first_prohibited_phrase(text) is None
    assert "No real trade" in outcome.confirmation.message
