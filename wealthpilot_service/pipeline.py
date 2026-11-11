"""C.0 WealthPilot orchestration: runs UC.1 through F.1 to F.6 for the browser and the console.

This is not a function on the IDEF0. A Planner keeps one PlanningSession per
investor and calls the functions in UC.1 order. Each flow goes from the
function that produces it to the functions that consume it; the controls come
from X.3 (the approved configuration in config/rules.json) and from X.1 (the
investor's confirmation and save request). Every step is recorded as a
TraceStep tagged with the function and the asset that performs it, for example
"F.6.3 | C.6.3", so any run can be followed on the IDEF0 diagrams.
"""

import secrets
import threading
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from allocation_engine import determine_target_asset_allocation, request_historical_market_data
from investment_plan_management import (
    LanguageModel,
    PlanSaveRequest,
    PlanStore,
    PresentedInvestmentPlan,
    ReviewedPlanSnapshot,
    SavedInvestmentPlan,
    SavedPlanConfirmation,
    SqlitePlanStore,
    confirm_successful_plan_save,
    explain_investment_plan,
    persist_reviewed_investment_plan,
    plan_save_request_problem,
    present_investment_plan,
    share_text,
    validate_explicit_plan_save_request,
)
from investor_interface import collect_investor_information, requests_for_investor_input
from market_data_provider import DEFAULT_SNAPSHOT_DIRECTORY, provide_historical_market_data
from model_flows import (
    HistoricalMarketData,
    InvestmentRecommendationsAndWeights,
    InvestorProfileAndResponses,
    MarketDataRequest,
    RiskScoreAndCategory,
    ScreenedCandidateSecurities,
    TargetAssetAllocation,
)
from portfolio_construction_engine import generate_investment_recommendations
from risk_engine import assess_investor_risk_profile
from screening_engine import screen_candidate_securities
from system_administration import ApprovedConfiguration, load_configuration

from .storage import DEFAULT_DATABASE_PATH, SimulatedPortfolioStore

MAX_SESSIONS = 500  # oldest sessions are forgotten first; saved plans are kept in the database


@dataclass(frozen=True)
class TraceStep:
    tag: str  # "F.2 | C.2" for a function and the asset that performs it, "X.1" for an external system
    name: str
    output: str


@dataclass
class PlanningSession:
    session_id: str
    started_at: str
    investor: InvestorProfileAndResponses | None = None
    risk: RiskScoreAndCategory | None = None
    target: TargetAssetAllocation | None = None
    screened: ScreenedCandidateSecurities | None = None
    recommendations: InvestmentRecommendationsAndWeights | None = None
    presented: PresentedInvestmentPlan | None = None
    snapshot: ReviewedPlanSnapshot | None = None
    trace: list[TraceStep] = field(default_factory=list)

    def record(self, tag: str, name: str, output: str) -> None:
        self.trace.append(TraceStep(tag, name, output))


@dataclass(frozen=True)
class SaveOutcome:
    status: str  # "saved", "not_authorized", "rejected" or "failed"
    detail: str
    saved_plan: SavedInvestmentPlan | None
    confirmation: SavedPlanConfirmation | None
    simulated_portfolio_before: dict | None
    simulated_portfolio_after: dict | None


class SessionNotFound(KeyError):
    pass


class StepOutOfOrder(RuntimeError):
    pass


class PlanWithheld(RuntimeError):
    """The analysis is withheld rather than built on unsuitable evidence (SR-10)."""

    def __init__(self, reason: str, limitations: list[str]):
        super().__init__(reason)
        self.reason = reason
        self.limitations = limitations


class Planner:
    def __init__(
        self,
        *,
        configuration: ApprovedConfiguration | None = None,
        snapshot_directory: Path = DEFAULT_SNAPSHOT_DIRECTORY,
        database_path: Path = DEFAULT_DATABASE_PATH,
        plan_store: PlanStore | None = None,
        portfolio_store: SimulatedPortfolioStore | None = None,
        language_model: LanguageModel | None = None,
    ) -> None:
        self.configuration = configuration or load_configuration()
        self.snapshot_directory = Path(snapshot_directory)
        self.plan_store = plan_store or SqlitePlanStore(database_path)
        self.portfolio_store = portfolio_store or SimulatedPortfolioStore(database_path)
        self.language_model = language_model
        self._sessions: OrderedDict[str, PlanningSession] = OrderedDict()
        self._lock = threading.Lock()

    # UC.1 steps, in order

    def start_session(self) -> PlanningSession:
        session = PlanningSession(session_id="session-" + secrets.token_hex(6), started_at=_now())
        session.record("X.1", "Initiate Session", f"Session Initiation Command {session.session_id}")
        session.record(
            "F.1 | C.1",
            "Collect Investor Information",
            "Requests for Investor Input: financial profile, risk questionnaire, current holdings",
        )
        with self._lock:
            self._sessions[session.session_id] = session
            while len(self._sessions) > MAX_SESSIONS:
                self._sessions.popitem(last=False)
        return session

    def requests_for_investor_input(self) -> dict:
        return requests_for_investor_input(
            investment_planning_constraints=self.configuration.investment_planning_constraints
        )

    def submit_investor_information(
        self,
        session_id: str,
        *,
        financial_profile: dict,
        risk_questionnaire_responses: dict,
        current_holdings: list[dict],
    ) -> RiskScoreAndCategory:
        """F.1 then F.2. Raises InvestorInputError listing every problem with the answers."""
        session = self.session(session_id)
        config = self.configuration
        investor = collect_investor_information(
            financial_profile,
            risk_questionnaire_responses,
            current_holdings,
            investment_planning_constraints=config.investment_planning_constraints,
            session_initiation_command=session.session_id,
        )
        # New answers supersede anything built from earlier ones.
        session.target = session.screened = session.recommendations = None
        session.presented = session.snapshot = None
        session.investor = investor
        session.record(
            "F.1 | C.1",
            "Collect Investor Information",
            f"Investor Profile and Risk Questionnaire Responses: {len(investor.financial_profile)} profile answers, "
            f"{len(investor.risk_questionnaire_responses)} questionnaire answers, "
            + _count(len(investor.current_holdings), "current holding"),
        )
        self.portfolio_store.record(
            session.session_id,
            investor.financial_profile["investable_savings"],
            [asdict(holding) for holding in investor.current_holdings],
        )
        risk = assess_investor_risk_profile(investor, risk_scoring_rules=config.risk_scoring_rules)
        session.risk = risk
        session.record(
            "F.2 | C.2",
            "Assess Investor Risk Profile",
            f"Risk Score and Risk Category: {risk.risk_score}, {risk.risk_category}",
        )
        return risk

    def build_plan(self, session_id: str, *, profile_interpretation_confirmed: bool) -> PlanningSession:
        """F.3 to F.6.2. Raises PlanWithheld if the evidence cannot support a plan."""
        session = self.session(session_id)
        if session.risk is None:
            raise StepOutOfOrder("Enter your information and answer the questionnaire first.")
        session.record(
            "X.1",
            "Confirm Profile Interpretation",
            "Profile Interpretation Confirmation: " + ("confirmed" if profile_interpretation_confirmed else "not given"),
        )
        if not profile_interpretation_confirmed:
            raise StepOutOfOrder("The plan is built only after you confirm the risk assessment.")
        config = self.configuration

        request = request_historical_market_data(session.risk, allocation_rules=config.allocation_rules)
        session.record("F.3 | C.3", "Determine Target Asset Allocation", "Market Data Request: " + ", ".join(request.symbols))
        data = provide_historical_market_data(
            request, snapshot_directory=self.snapshot_directory,
            minimum_observations=config.security_screening_criteria["min_observations"],
        )
        session.record("X.2", "Provide Historical Market Data", _describe_data(data, request))
        if not data.series:
            raise PlanWithheld("No historical market data could be admitted, so the analysis is withheld.", data.limitations)
        common_dates = set.intersection(*(set(s.dates) for s in data.series.values()))
        minimum = config.security_screening_criteria["min_observations"]
        if len(common_dates) < minimum:
            raise PlanWithheld(
                "Historical data do not cover a sufficient common analysis interval, so the plan is withheld.",
                [*data.limitations, f"Only {len(common_dates)} common daily observations; {minimum} are required for this exercise."],
            )

        target = determine_target_asset_allocation(
            session.risk,
            data,
            allocation_rules=config.allocation_rules,
            investment_planning_constraints=config.investment_planning_constraints,
            profile_interpretation_confirmed=True,
        )
        session.record("F.3 | C.3", "Determine Target Asset Allocation", "Target Asset Allocation: " + _shares(target.weights))

        screened = screen_candidate_securities(
            target,
            data,
            market_and_regulatory_constraints=config.market_and_regulatory_constraints,
            security_screening_criteria=config.security_screening_criteria,
        )
        excluded = "; excluded " + ", ".join(e.symbol for e in screened.exclusions) if screened.exclusions else ""
        session.record(
            "F.4 | C.4",
            "Screen Candidate Securities",
            "Screened Candidate Securities: " + (", ".join(c.symbol for c in screened.candidates) or "none") + excluded,
        )

        try:
            recommendations = generate_investment_recommendations(
                screened,
                target_asset_allocation=target,
                portfolio_construction_rules=config.portfolio_construction_rules,
                minimum_observations=config.security_screening_criteria["min_observations"],
            )
        except ValueError as error:
            reasons = [f"{e.symbol}: {e.reason}" for e in screened.exclusions]
            raise PlanWithheld(f"{error}.", [*screened.data_limitations, *reasons]) from error
        session.record(
            "F.5 | C.5",
            "Generate Investment Recommendations",
            "Investment Recommendations and Weights: "
            + ", ".join(f"{r.symbol} {share_text(r.weight)}" for r in recommendations.recommendations),
        )

        explanation = explain_investment_plan(
            recommendations, explanation_rules=config.explanation_rules, language_model=self.language_model
        )
        note = f" ({explanation.generation_note})" if explanation.generation_note else ""
        session.record(
            "F.6.1 | C.6.1",
            "Explain Investment Plan",
            f"Investment Plan Explanation: {len(explanation.material_risks)} risks explained, "
            f"written by {explanation.generated_by}{note}",
        )
        presented, snapshot = present_investment_plan(
            recommendations, explanation, explanation_rules=config.explanation_rules
        )
        session.record(
            "F.6.2 | C.6.2",
            "Present Investment Plan",
            f"Presented Investment Plan {presented.plan_id} and IO.6.1 Reviewed Plan Snapshot",
        )
        session.target, session.screened, session.recommendations = target, screened, recommendations
        session.presented, session.snapshot = presented, snapshot
        return session

    def request_save(self, session_id: str, *, plan_id: str, action: str, request_id: str | None = None) -> SaveOutcome:
        """X.1 sends a Plan Save Request; F.6.3 to F.6.5 decide what happens."""
        session = self.session(session_id)
        if session.snapshot is None:
            raise StepOutOfOrder("There is no presented plan to save.")
        request = PlanSaveRequest(
            request_id=request_id if request_id is not None else "req-" + secrets.token_hex(6),
            plan_id=plan_id,
            action=action,
        )
        session.record("X.1", "Request Plan Save", f"Plan Save Request {request.request_id} ({request.action}) for {request.plan_id}")
        before = self.portfolio_store.read(session.session_id)

        payload = validate_explicit_plan_save_request(session.snapshot, plan_save_request=request)
        if payload is None:
            problem = plan_save_request_problem(session.snapshot, request)
            session.record("F.6.3 | C.6.3", "Validate Explicit Plan Save Request", f"no payload: {problem}")
            session.record("F.6.4 | C.6.4", "Persist Reviewed Investment Plan", "not run, nothing is saved")
            session.record("F.6.5 | C.6.5", "Confirm Successful Plan Save", "not run, no confirmation is sent")
            return SaveOutcome("not_authorized", problem, None, None, before, self.portfolio_store.read(session.session_id))
        session.record("F.6.3 | C.6.3", "Validate Explicit Plan Save Request", "IO.6.2 Authorized Plan Save Payload")

        result = persist_reviewed_investment_plan(payload, plan_save_request=request, plan_store=self.plan_store)
        session.record(
            "F.6.4 | C.6.4",
            "Persist Reviewed Investment Plan",
            f"IO.6.3 Plan Persistence Result: {result.status}, {result.detail}",
        )
        confirmed = confirm_successful_plan_save(result, plan_save_request=request)
        after = self.portfolio_store.read(session.session_id)
        if confirmed is None:
            session.record("F.6.5 | C.6.5", "Confirm Successful Plan Save", "no confirmation, the save did not succeed")
            return SaveOutcome(result.status, result.detail, None, None, before, after)
        saved_plan, confirmation = confirmed
        session.record(
            "F.6.5 | C.6.5", "Confirm Successful Plan Save", "Saved Investment Plan and Saved Plan Confirmation"
        )
        return SaveOutcome("saved", result.detail, saved_plan, confirmation, before, after)

    # Lookups

    def session(self, session_id: str) -> PlanningSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFound(session_id)
        return session

    def saved_plans(self, limit: int = 20) -> list[dict]:
        list_saved = getattr(self.plan_store, "list_saved", None)
        return list_saved(limit) if list_saved else []

    def saved_plan(self, plan_id: str) -> dict | None:
        return self.plan_store.read(plan_id)


def _describe_data(data: HistoricalMarketData, request: MarketDataRequest) -> str:
    if data.snapshot_id is None:
        return "Historical Market Data: none (" + "; ".join(data.limitations) + ")"
    text = f"Historical Market Data: snapshot {data.snapshot_id}, {len(data.series)} of {len(request.symbols)} symbols admitted"
    if data.limitations:
        text += f", {len(data.limitations)} limitations"
    return text


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" + ("" if number == 1 else "s")


def _shares(weights: dict) -> str:
    return ", ".join(f"{asset_class} {share_text(share)}" for asset_class, share in weights.items())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
