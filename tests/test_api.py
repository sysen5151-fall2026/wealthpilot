"""UC.1 through the browser's HTTP interface (wealthpilot_service/api.py).

Each test drives the same calls the front end makes. Names start with the
SPEC.md system requirement they give evidence for: SR-01 planning inputs,
SR-02 and SR-03 explanation, SR-04 explicit save, SR-05 saving leaves the
simulated portfolio unchanged, SR-10 limitation disclosure, SR-13 scope notice
and SR-14 learner controls.
"""

import re

import pytest
from fastapi.testclient import TestClient

from wealthpilot_service import Planner
from wealthpilot_service.api import FRONTEND_DIRECTORY, create_app


@pytest.fixture
def client(tmp_path, snapshot_directory):
    planner = Planner(snapshot_directory=snapshot_directory, database_path=tmp_path / "wealthpilot.db")
    return TestClient(create_app(planner))


def start(client) -> str:
    response = client.post("/api/sessions")
    assert response.status_code == 200
    return response.json()["session_id"]


def submit(client, session_id, investor):
    return client.post(f"/api/sessions/{session_id}/investor-information", json=investor)


def plan(client, investor) -> tuple[str, dict]:
    session_id = start(client)
    assert submit(client, session_id, investor).status_code == 200
    response = client.post(f"/api/sessions/{session_id}/plan", json={"profile_interpretation_confirmed": True})
    assert response.status_code == 200
    return session_id, response.json()


def test_status_reports_configuration_snapshot_and_mode(client):
    status = client.get("/api/status").json()
    assert status["configuration_id"] == "WP-RULES-0.1-PLACEHOLDER" and status["placeholder_rules"] is True
    assert status["market_data"]["available"] is True
    assert status["market_data"]["snapshot_id"] == "synthetic-test"
    assert status["explanation"]["mode"] == "template"


def test_session_returns_requests_for_investor_input(client):
    body = client.post("/api/sessions").json()
    requests = body["requests_for_investor_input"]
    assert {"financial_profile_fields", "risk_questionnaire", "current_holdings"} <= set(requests)
    assert [step["tag"] for step in body["trace"]] == ["X.1", "F.1 | C.1"]


def test_invalid_answers_are_returned_as_a_list_to_fix(client, investor):
    session_id = start(client)
    investor["financial_profile"]["age"] = 7
    investor["risk_questionnaire_responses"].pop("objective")

    response = submit(client, session_id, investor)

    assert response.status_code == 422
    assert len(response.json()["errors"]) == 2


def test_risk_assessment_is_shown_before_any_plan(client, investor):
    session_id = start(client)
    risk = submit(client, session_id, investor).json()["risk_assessment"]

    assert (risk["risk_score"], risk["risk_category"]) == (70, "Moderately Aggressive")
    assert len(risk["strongest_factors"]) == 2 and len(risk["factors"]) == 7
    assert [c["name"] for c in risk["categories"]][0] == "Conservative"
    refused = client.post(f"/api/sessions/{session_id}/plan", json={"profile_interpretation_confirmed": False})
    assert refused.status_code == 409


def test_SR_01_plan_reflects_goal_horizon_capacity_and_holdings(client, investor):
    investor["current_holdings"].append({"symbol": "TSLA", "value": 2000})
    _, body = plan(client, investor)
    content = body["presented_plan"]["content"]
    text = body["presented_plan"]["display_text"]

    assert content["profile_basis"]["goal_label"] == "Retirement" and "retirement in 25 years" in text
    amounts = content["simulated_amounts"]
    assert amounts["total"] == 25000 + 5000 + 2000
    rows = {row["symbol"]: row for row in amounts["by_symbol"]}
    assert rows["VTI"]["current"] == 5000 and rows["TSLA"] == {
        "symbol": "TSLA", "in_plan": False, "plan": 0.0, "current": 2000.0, "difference": -2000.0
    }
    assert sum(row["plan"] for row in amounts["by_symbol"]) == pytest.approx(amounts["total"], abs=0.05)


def test_SR_02_SR_03_plan_explains_drivers_and_risks(client, investor):
    _, body = plan(client, investor)
    explanation = body["presented_plan"]["content"]["explanation"]

    drivers = [line for line in explanation["allocation_rationale"] if line.startswith("Your answer about")]
    assert len(drivers) == 2
    assert explanation["material_risks"]
    assert explanation["historical_evidence"][-1].endswith("do not predict future results.")


def test_SR_04_SR_05_nothing_is_saved_without_an_explicit_request_and_saving_moves_nothing(client, investor):
    session_id, body = plan(client, investor)
    plan_id = body["presented_plan"]["plan_id"]
    assert client.get("/api/saved-plans").json()["saved_plans"] == []

    implicit = client.post(f"/api/sessions/{session_id}/plan-save-requests", json={"plan_id": plan_id, "action": "view"})
    assert implicit.json()["status"] == "not_authorized"
    assert client.get("/api/saved-plans").json()["saved_plans"] == []

    saved = client.post(f"/api/sessions/{session_id}/plan-save-requests", json={"plan_id": plan_id, "action": "save"}).json()
    assert saved["status"] == "saved"
    assert saved["confirmation"]["plan_id"] == plan_id
    assert saved["simulated_portfolio_before"] == saved["simulated_portfolio_after"]
    assert saved["simulated_portfolio_after"]["cash"] == 25000
    assert [step["tag"] for step in saved["trace"][-4:]] == ["X.1", "F.6.3 | C.6.3", "F.6.4 | C.6.4", "F.6.5 | C.6.5"]

    listing = client.get("/api/saved-plans").json()["saved_plans"]
    assert [p["plan_id"] for p in listing] == [plan_id]
    record = client.get(f"/api/saved-plans/{plan_id}").json()["saved_plan"]
    assert record == body["presented_plan"]["content"]


def test_SR_04_request_for_another_plan_is_not_saved(client, investor):
    session_id, _ = plan(client, investor)
    response = client.post(
        f"/api/sessions/{session_id}/plan-save-requests", json={"plan_id": "plan-0000000000", "action": "save"}
    ).json()
    assert response["status"] == "not_authorized"
    assert "different or superseded plan" in response["detail"]


def test_SR_10_missing_prices_withhold_the_plan_and_say_why(tmp_path, investor):
    client = TestClient(create_app(Planner(snapshot_directory=tmp_path / "none", database_path=tmp_path / "db")))
    assert client.get("/api/status").json()["market_data"]["available"] is False
    session_id = start(client)
    submit(client, session_id, investor)

    body = client.post(f"/api/sessions/{session_id}/plan", json={"profile_interpretation_confirmed": True}).json()

    assert body["status"] == "withheld"
    assert "No historical price snapshot" in body["limitations"][0]


def test_SR_13_every_planning_response_carries_the_scope_notice(client, investor):
    session_id, body = plan(client, investor)
    notice = client.get("/api/status").json()["scope_notice"]
    assert body["scope_notice"] == notice
    assert notice in body["presented_plan"]["display_text"]
    saved = client.post(
        f"/api/sessions/{session_id}/plan-save-requests",
        json={"plan_id": body["presented_plan"]["plan_id"], "action": "save"},
    ).json()
    assert saved["scope_notice"] == notice
    page = client.get("/").text
    assert notice in page  # shown before any script runs


def test_SR_14_learner_interface_offers_no_brokerage_controls(client, investor):
    _, body = plan(client, investor)
    assert body["presented_plan"]["learner_actions"] == ["Save this simulated plan"]
    page = (FRONTEND_DIRECTORY / "index.html").read_text() + (FRONTEND_DIRECTORY / "app.js").read_text()
    assert 'type="password"' not in page
    for control in ("place order", "buy now", "sell now", "transfer funds", "connect your brokerage", "account number"):
        assert control not in page.lower()
    page = page.replace("http://www.w3.org/2000/svg", "")  # the SVG namespace of the favicon is not a request
    assert not re.search(r"https?://(?!127\.0\.0\.1|localhost)", page)  # the page calls no outside service


def test_unknown_session_is_reported(client):
    response = client.post("/api/sessions/session-unknown/plan", json={"profile_interpretation_confirmed": True})
    assert response.status_code == 404
