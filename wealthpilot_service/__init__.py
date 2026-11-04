"""C.0 WealthPilot: the orchestration that runs UC.1, for the browser (api.py) and the console.

pipeline.py holds the Planner, which calls F.1 to F.6 in UC.1 order and
records a trace line per step tagged with the function and its asset (for
example [F.6.3 | C.6.3]). run_investment_planning_session runs UC.1 once in
the terminal with the sample investor from investor_interface/console.py.
"""

from pathlib import Path
from typing import NamedTuple

from investment_plan_management import (
    EXPLICIT_SAVE,
    LanguageModel,
    PlanStore,
    PresentedInvestmentPlan,
    SavedInvestmentPlan,
    SavedPlanConfirmation,
)
from investor_interface.console import (
    SAMPLE_INVESTOR,
    show_presented_plan,
    show_risk_assessment,
    show_saved_plan,
    show_withheld,
)
from market_data_provider import DEFAULT_SNAPSHOT_DIRECTORY

from .pipeline import (
    Planner,
    PlanningSession,
    PlanWithheld,
    SaveOutcome,
    SessionNotFound,
    StepOutOfOrder,
    TraceStep,
)
from .storage import DEFAULT_DATABASE_PATH, SimulatedPortfolioStore

__all__ = [
    "DEFAULT_DATABASE_PATH",
    "Planner",
    "PlanningSession",
    "PlanWithheld",
    "SaveOutcome",
    "SessionNotFound",
    "SessionOutcome",
    "SimulatedPortfolioStore",
    "StepOutOfOrder",
    "TraceStep",
    "run_investment_planning_session",
]


class SessionOutcome(NamedTuple):
    presented_plan: PresentedInvestmentPlan
    saved_plan: SavedInvestmentPlan | None
    confirmation: SavedPlanConfirmation | None


def run_investment_planning_session(
    *,
    save_requested: bool = True,
    plan_store: PlanStore | None = None,
    snapshot_directory: Path = DEFAULT_SNAPSHOT_DIRECTORY,
    database_path: Path = DEFAULT_DATABASE_PATH,
    language_model: LanguageModel | None = None,
    investor: dict = SAMPLE_INVESTOR,
    echo: bool = True,
) -> SessionOutcome:
    """Run UC.1 once with a sample investor. save_requested=False models an investor who never saves.

    Raises PlanWithheld if the price snapshot cannot support a plan.
    """
    planner = Planner(
        snapshot_directory=snapshot_directory,
        database_path=database_path,
        plan_store=plan_store,
        language_model=language_model,
    )
    session = planner.start_session()
    printed = 0

    def show_trace() -> None:
        nonlocal printed
        if echo:
            for step in session.trace[printed:]:
                print(f"[{step.tag}] {step.name} -> {step.output}")
        printed = len(session.trace)

    risk = planner.submit_investor_information(
        session.session_id,
        financial_profile=investor["financial_profile"],
        risk_questionnaire_responses=investor["risk_questionnaire_responses"],
        current_holdings=investor["current_holdings"],
    )
    show_trace()
    if echo:
        show_risk_assessment(risk)
    try:
        planner.build_plan(session.session_id, profile_interpretation_confirmed=True)
    except PlanWithheld as withheld:
        show_trace()
        if echo:
            show_withheld(withheld.reason, withheld.limitations)
        raise
    show_trace()
    presented = session.presented
    if echo:
        show_presented_plan(presented)

    if not save_requested:
        if echo:
            print("[X.1] Request Plan Save -> no request sent, so F.6.3 to F.6.5 save nothing")
        return SessionOutcome(presented, None, None)
    outcome = planner.request_save(session.session_id, plan_id=presented.plan_id, action=EXPLICIT_SAVE)
    show_trace()
    if echo and outcome.saved_plan:
        show_saved_plan(outcome.saved_plan, outcome.confirmation)
    return SessionOutcome(presented, outcome.saved_plan, outcome.confirmation)
