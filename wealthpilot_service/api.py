"""HTTP interface for the browser front end: the X.1 side of UC.1 over JSON.

    GET  /api/status                                  configuration, price snapshot, explanation mode
    POST /api/sessions                                Initiate Session -> Requests for Investor Input
    POST /api/sessions/{id}/investor-information      F.1, F.2 -> Risk Score and Risk Category
    POST /api/sessions/{id}/plan                      Profile Interpretation Confirmation -> F.3 to F.6.2
    POST /api/sessions/{id}/plan-save-requests        Plan Save Request -> F.6.3 to F.6.5
    GET  /api/saved-plans                             saved plans, newest first
    GET  /api/saved-plans/{plan_id}                   one saved plan
    GET  /                                            the front end (frontend/)

Every response that carries a planning output also carries the scope notice
(SR-13), and the only learner action offered is saving the simulated plan
(SR-14). Run it with: python app.py --serve
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from investment_plan_management import language_model_from_environment
from investor_interface import InvestorInputError
from market_data_provider import snapshot_status

from .pipeline import Planner, PlanningSession, PlanWithheld, SessionNotFound, StepOutOfOrder

FRONTEND_DIRECTORY = Path(__file__).resolve().parent.parent / "frontend"


class InvestorInformation(BaseModel):
    financial_profile: dict[str, Any]
    risk_questionnaire_responses: dict[str, Any]
    current_holdings: list[dict[str, Any]] = Field(default_factory=list)


class ProfileInterpretationConfirmation(BaseModel):
    profile_interpretation_confirmed: bool


class PlanSaveRequestBody(BaseModel):
    plan_id: str
    action: str
    request_id: str | None = None


def create_app(planner: Planner | None = None) -> FastAPI:
    planner = planner or Planner(language_model=language_model_from_environment())
    app = FastAPI(title="WealthPilot", description="Educational investment-planning simulator", version="0.2.0")
    scope_notice = planner.configuration.explanation_rules.scope_notice

    def session_or_404(session_id: str) -> PlanningSession:
        try:
            return planner.session(session_id)
        except SessionNotFound:
            raise HTTPException(404, "This session is not known. Start again.") from None

    def trace(session: PlanningSession) -> list[dict]:
        return [asdict(step) for step in session.trace]

    @app.get("/api/status")
    def status() -> dict:
        model = planner.language_model
        return {
            "scope_notice": scope_notice,
            "configuration_id": planner.configuration.configuration_id,
            "placeholder_rules": "PLACEHOLDER" in planner.configuration.configuration_id,
            "market_data": snapshot_status(planner.snapshot_directory),
            "explanation": {"mode": "language model" if model else "template", "model": model.name if model else None},
            "learner_actions": planner.configuration.explanation_rules.learner_actions,
        }

    @app.post("/api/sessions")
    def start_session() -> dict:
        session = planner.start_session()
        return {
            "session_id": session.session_id,
            "scope_notice": scope_notice,
            "requests_for_investor_input": planner.requests_for_investor_input(),
            "trace": trace(session),
        }

    @app.post("/api/sessions/{session_id}/investor-information")
    def submit_investor_information(session_id: str, body: InvestorInformation):
        session = session_or_404(session_id)
        try:
            risk = planner.submit_investor_information(
                session_id,
                financial_profile=body.financial_profile,
                risk_questionnaire_responses=body.risk_questionnaire_responses,
                current_holdings=body.current_holdings,
            )
        except InvestorInputError as error:
            return JSONResponse(status_code=422, content={"errors": error.errors})
        return {
            "scope_notice": scope_notice,
            "risk_assessment": {
                "risk_score": risk.risk_score,
                "risk_category": risk.risk_category,
                "max_one_year_loss": risk.max_one_year_loss,
                "strongest_factors": [
                    {"label": f.label, "answer": f.answer, "lean": round(f.lean, 2)} for f in risk.strongest_factors()
                ],
                "factors": [{"label": f.label, "answer": f.answer, "lean": round(f.lean, 2)} for f in risk.factors],
                "categories": planner.configuration.risk_scoring_rules["categories"],
                "rules_version": risk.rules_version,
            },
            "trace": trace(session),
        }

    @app.post("/api/sessions/{session_id}/plan")
    def build_plan(session_id: str, body: ProfileInterpretationConfirmation):
        session = session_or_404(session_id)
        try:
            planner.build_plan(session_id, profile_interpretation_confirmed=body.profile_interpretation_confirmed)
        except StepOutOfOrder as error:
            raise HTTPException(409, str(error)) from None
        except PlanWithheld as withheld:
            return {
                "status": "withheld",
                "scope_notice": scope_notice,
                "reason": withheld.reason,
                "limitations": withheld.limitations,
                "trace": trace(session),
            }
        presented = session.presented
        return {
            "status": "presented",
            "scope_notice": scope_notice,
            "presented_plan": asdict(presented),
            "screening": {
                "candidates": [c.symbol for c in session.screened.candidates],
                "exclusions": [asdict(e) for e in session.screened.exclusions],
            },
            "trace": trace(session),
        }

    @app.post("/api/sessions/{session_id}/plan-save-requests")
    def request_plan_save(session_id: str, body: PlanSaveRequestBody):
        session = session_or_404(session_id)
        try:
            outcome = planner.request_save(
                session_id, plan_id=body.plan_id, action=body.action, request_id=body.request_id
            )
        except StepOutOfOrder as error:
            raise HTTPException(409, str(error)) from None
        return {
            "status": outcome.status,
            "detail": outcome.detail,
            "scope_notice": scope_notice,
            "saved_plan": asdict(outcome.saved_plan) if outcome.saved_plan else None,
            "confirmation": asdict(outcome.confirmation) if outcome.confirmation else None,
            "simulated_portfolio_before": outcome.simulated_portfolio_before,
            "simulated_portfolio_after": outcome.simulated_portfolio_after,
            "trace": trace(session),
        }

    @app.get("/api/saved-plans")
    def saved_plans(limit: int = 20) -> dict:
        return {"scope_notice": scope_notice, "saved_plans": planner.saved_plans(max(1, min(limit, 100)))}

    @app.get("/api/saved-plans/{plan_id}")
    def saved_plan(plan_id: str) -> dict:
        record = planner.saved_plan(plan_id)
        if record is None:
            raise HTTPException(404, "No saved plan has this identifier.")
        return {"scope_notice": scope_notice, "saved_plan": record}

    if FRONTEND_DIRECTORY.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND_DIRECTORY, html=True), name="frontend")
    return app
