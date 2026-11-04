"""Requirement tests for C.6 Investment Plan Management Subsystem.

Each test name starts with the ID of the CS.6 component requirement it checks,
as written in the Innoslate component specification. Fixtures are fixed, saved
plans go to a database in pytest's temporary folder, and the end-to-end runs
use synthetic prices (tests/synthetic_market.py), so no test touches a real
account, the network or the repository's data folder.

Not covered here: CS6.2.1 (2-second timing over 100 runs) and CS6.2.2 (novice
comprehension study) need a performance run and a usability session, and
CS6.1.3.1 to CS6.1.3.3 are verified by inspecting the conduits in the model.
"""

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict, replace

import pytest

from investment_plan_management import (
    EXPLICIT_SAVE,
    FAILED,
    REJECTED,
    SUCCEEDED,
    InvestmentRecommendationsAndWeights,
    PlanSaveRequest,
    Recommendation,
    SqlitePlanStore,
    confirm_successful_plan_save,
    explain_investment_plan,
    persist_reviewed_investment_plan,
    present_investment_plan,
    validate_explicit_plan_save_request,
)
from system_administration import get_explanation_rules
from wealthpilot_service import SimulatedPortfolioStore, run_investment_planning_session

RULES = get_explanation_rules()


def make_recommendations(**changes) -> InvestmentRecommendationsAndWeights:
    plan = InvestmentRecommendationsAndWeights(
        risk_score=55,
        risk_category="Moderate",
        target_allocation={"US Stocks": 0.6, "Bonds": 0.4},
        recommendations=[
            Recommendation("AAPL", "US Stocks", 0.3, "Apple Inc.", "Stock"),
            Recommendation("MSFT", "US Stocks", 0.3, "Microsoft Corporation", "Stock"),
            Recommendation("BND", "Bonds", 0.4, "Vanguard Total Bond Market ETF", "ETF"),
        ],
        identified_risks=["market_volatility", "concentration"],
        data_limitations=["Prices come from a fixed historical sample, not live market data."],
    )
    return replace(plan, **changes)


def explain_and_present(recommendations=None):
    recommendations = recommendations or make_recommendations()
    explanation = explain_investment_plan(recommendations, explanation_rules=RULES)
    presented, snapshot = present_investment_plan(recommendations, explanation, explanation_rules=RULES)
    return recommendations, explanation, presented, snapshot


def explicit_request(snapshot, **changes) -> PlanSaveRequest:
    request = PlanSaveRequest(request_id="req-1", plan_id=snapshot.plan_id, action=EXPLICIT_SAVE)
    return replace(request, **changes)


def authorize(snapshot):
    request = explicit_request(snapshot)
    return request, validate_explicit_plan_save_request(snapshot, plan_save_request=request)


def saved_rows(database_path) -> list[tuple[str, str]]:
    """(plan_id, record text) for every saved plan, read straight from the database file."""
    if not database_path.exists():
        return []
    with closing(sqlite3.connect(database_path)) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "saved_plans" not in tables:
            return []
        return connection.execute("SELECT plan_id, record FROM saved_plans").fetchall()


class FailingStore(SqlitePlanStore):
    def write(self, plan_id, record):
        raise sqlite3.OperationalError("database or disk is full")


class PartialWriteStore(SqlitePlanStore):
    """Stores only the first half of the record, as an interrupted write would."""

    def write(self, plan_id, record):
        text = json.dumps(record)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT INTO saved_plans (plan_id, saved_at, record) VALUES (?, ?, ?)",
                (plan_id, "2026-11-04T00:00:00+00:00", text[: len(text) // 2]),
            )


# F.6.1 Explain Investment Plan

def test_CS6_1_4_1_explanation_has_rationale_and_risk():
    recommendations, explanation, _, _ = explain_and_present()

    assert explanation.plan_id == recommendations.plan_id
    assert explanation.summary
    assert "Moderate" in explanation.allocation_rationale[0]
    assert "55" in explanation.allocation_rationale[0]
    assert any("AAPL 30%" in line for line in explanation.allocation_rationale)
    assert len(explanation.material_risks) >= 1
    assert set(explanation.material_risks) <= set(RULES.risk_language.values())
    assert explanation.data_limitations == recommendations.data_limitations
    assert explanation.scope_notice == RULES.scope_notice
    assert explanation.generated_by == "template"


def test_CS6_1_4_1_plan_without_identified_risk_is_not_explained():
    with pytest.raises(ValueError):
        explain_investment_plan(make_recommendations(identified_risks=[]), explanation_rules=RULES)


def test_CS6_1_4_1_risk_without_novice_wording_is_not_explained():
    with pytest.raises(ValueError):
        explain_investment_plan(make_recommendations(identified_risks=["liquidity"]), explanation_rules=RULES)


def test_CS6_1_4_1_wording_that_breaks_the_rules_is_rejected():
    strict_rules = replace(RULES, prohibited_phrases=["simulated"])
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
    assert presented.content == asdict(snapshot)  # the browser shows exactly what can be saved


def test_CS6_1_2_1_explanation_of_another_plan_is_not_presented():
    other_plan = make_recommendations(risk_category="Conservative")
    explanation = explain_investment_plan(other_plan, explanation_rules=RULES)
    with pytest.raises(ValueError):
        present_investment_plan(make_recommendations(), explanation, explanation_rules=RULES)


def test_CS6_1_1_2_explanation_and_presentation_use_the_same_rules_version():
    recommendations = make_recommendations()
    explanation = explain_investment_plan(recommendations, explanation_rules=RULES)
    with pytest.raises(ValueError):
        present_investment_plan(recommendations, explanation, explanation_rules=replace(RULES, version="ER-2"))


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
        target_allocation={"US Stocks": 0.4, "Bonds": 0.6},
        recommendations=[
            Recommendation("AAPL", "US Stocks", 0.2, "Apple Inc.", "Stock"),
            Recommendation("MSFT", "US Stocks", 0.2, "Microsoft Corporation", "Stock"),
            Recommendation("BND", "Bonds", 0.6, "Vanguard Total Bond Market ETF", "ETF"),
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
    database = tmp_path / "wealthpilot.db"
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)

    result = persist_reviewed_investment_plan(payload, plan_save_request=request, plan_store=SqlitePlanStore(database))

    assert result.status == SUCCEEDED
    [(plan_id, record)] = saved_rows(database)
    assert plan_id == snapshot.plan_id
    assert json.loads(record) == asdict(snapshot) == result.persisted_plan


def test_CS6_1_4_4_unauthorized_save_is_rejected(tmp_path):
    database = tmp_path / "wealthpilot.db"
    _, _, _, snapshot = explain_and_present()
    _, payload = authorize(snapshot)
    different_request = explicit_request(snapshot, request_id="req-2")

    result = persist_reviewed_investment_plan(
        payload, plan_save_request=different_request, plan_store=SqlitePlanStore(database)
    )

    assert result.status == REJECTED
    assert saved_rows(database) == []


@pytest.mark.parametrize("store_class", [FailingStore, PartialWriteStore], ids=["write-error", "partial-write"])
def test_CS6_1_4_4_failed_write_is_not_reported_as_success(tmp_path, store_class):
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)

    result = persist_reviewed_investment_plan(
        payload, plan_save_request=request, plan_store=store_class(tmp_path / "wealthpilot.db")
    )

    assert result.status == FAILED
    assert result.persisted_plan is None


def test_CS6_1_4_4_save_leaves_simulated_portfolio_unchanged(tmp_path):
    database = tmp_path / "wealthpilot.db"
    portfolio = SimulatedPortfolioStore(database)
    portfolio.record("session-1", 20000, [{"symbol": "VTI", "value": 5000}])
    before = portfolio.read("session-1")
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)

    persist_reviewed_investment_plan(payload, plan_save_request=request, plan_store=SqlitePlanStore(database))

    assert portfolio.read("session-1") == before
    assert [plan_id for plan_id, _ in saved_rows(database)] == [snapshot.plan_id]


# F.6.5 Confirm Successful Plan Save

@pytest.fixture
def successful_save(tmp_path):
    _, _, _, snapshot = explain_and_present()
    request, payload = authorize(snapshot)
    result = persist_reviewed_investment_plan(
        payload, plan_save_request=request, plan_store=SqlitePlanStore(tmp_path / "wealthpilot.db")
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

def run_uc1(tmp_path, snapshot_directory, *, save_requested=True):
    database = tmp_path / "wealthpilot.db"
    outcome = run_investment_planning_session(
        save_requested=save_requested, snapshot_directory=snapshot_directory, database_path=database, echo=False
    )
    return outcome, database


def test_CS6_2_3_plan_identity_and_content_preserved_end_to_end(tmp_path, snapshot_directory):
    outcome, database = run_uc1(tmp_path, snapshot_directory)

    plan_id = outcome.presented_plan.plan_id
    [(stored_id, record)] = saved_rows(database)
    assert outcome.saved_plan.plan_id == outcome.confirmation.plan_id == plan_id == stored_id
    assert outcome.saved_plan.content == json.loads(record) == outcome.presented_plan.content
    for r in json.loads(record)["recommendations"]:
        assert r["symbol"] in outcome.presented_plan.display_text


def test_CS6_1_1_3_no_save_request_means_nothing_saved(tmp_path, snapshot_directory):
    outcome, database = run_uc1(tmp_path, snapshot_directory, save_requested=False)

    assert outcome.saved_plan is None
    assert outcome.confirmation is None
    assert saved_rows(database) == []


def test_CS6_2_4_only_simulation_controls_are_offered(tmp_path, snapshot_directory):
    outcome, _ = run_uc1(tmp_path, snapshot_directory)

    assert outcome.presented_plan.learner_actions == ["Save this simulated plan"]
    for text in (outcome.presented_plan.display_text, outcome.confirmation.message):
        assert RULES.first_prohibited_phrase(text) is None
    assert "No real trade" in outcome.confirmation.message
