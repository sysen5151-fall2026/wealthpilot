"""Flows on the first-level IDEF0 of F.0, one class per Input/Output entity.

    Investor Profile and Risk Questionnaire Responses   F.1 -> F.2
    Risk Score and Risk Category                        F.2 -> F.3, X.1
    Market Data Request                                 F.3 -> X.2
    Historical Market Data                              X.2 -> F.3, F.4
    Target Asset Allocation                             F.3 -> F.4, F.5
    Screened Candidate Securities                       F.4 -> F.5
    Investment Recommendations and Weights              F.5 -> F.6

Controls from X.3 and ENV.1 (the rules) are plain dictionaries loaded from
config/rules.json by system_administration. Several flows also carry the
evidence they were derived from (the investor's profile, the risk drivers, the
allocation adjustments), so that F.6.1 can explain the plan without reaching
back to earlier functions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Holding:
    """One hypothetical holding the investor already has."""

    symbol: str
    value: float  # USD, hypothetical


@dataclass(frozen=True)
class InvestorProfileAndResponses:
    """Investor Profile and Risk Questionnaire Responses: F.1 output, F.2 input."""

    session_id: str
    financial_profile: dict  # field name -> value, exactly as supplied
    risk_questionnaire_responses: dict  # question id -> option id
    current_holdings: list[Holding]
    answer_labels: dict = field(default_factory=dict)  # field or question id -> wording of the chosen answer


@dataclass(frozen=True)
class RiskFactor:
    """How one answer contributed to the risk score."""

    factor: str
    label: str
    answer: str
    points: int
    min_points: int
    max_points: int

    @property
    def lean(self) -> float:
        """-1 (most cautious) to +1 (most risk-tolerant)."""
        middle = (self.min_points + self.max_points) / 2
        half_range = (self.max_points - self.min_points) / 2 or 1
        return (self.points - middle) / half_range


@dataclass(frozen=True)
class RiskScoreAndCategory:
    """Risk Score and Risk Category: F.2 output to F.3 and X.1."""

    risk_score: int  # 0 to 100
    risk_category: str
    factors: list[RiskFactor]
    max_one_year_loss: float  # the limit the investor stated, e.g. 0.2
    profile_basis: dict  # goal, horizon, capacity and holdings, carried for the explanation
    rules_version: str

    def strongest_factors(self, count: int = 2) -> list[RiskFactor]:
        """The answers that pulled the score furthest from the middle."""
        return sorted(self.factors, key=lambda f: abs(f.lean), reverse=True)[:count]


@dataclass(frozen=True)
class MarketDataRequest:
    """Market Data Request: F.3 output to X.2 Market Data Provider."""

    symbols: list[str]


@dataclass(frozen=True)
class PriceSeries:
    """Admitted adjusted closing prices for one symbol, oldest first."""

    symbol: str
    dates: list[str]  # ISO 8601
    adjusted_closes: list[float]


@dataclass(frozen=True)
class HistoricalMarketData:
    """Historical Market Data: X.2 output to F.3 and F.4, after the SPEC data contract."""

    snapshot_id: str | None
    source: str | None
    series: dict[str, PriceSeries]  # admitted symbols only
    limitations: list[str]


@dataclass(frozen=True)
class TargetAssetAllocation:
    """Target Asset Allocation: F.3 output to F.4 and F.5."""

    weights: dict[str, float]  # asset class -> share of the portfolio
    base_weights: dict[str, float]  # before the planning constraints were applied
    adjustments: list[str]  # plain-language note for each constraint that changed the mix
    risk_assessment: RiskScoreAndCategory
    limitations: list[str]
    planning_flags: list[str] = field(default_factory=list)  # risk keys F.3 found, e.g. "short_horizon"


@dataclass(frozen=True)
class Exclusion:
    symbol: str
    reason: str


@dataclass(frozen=True)
class Candidate:
    """One security that passed screening, with the evidence it was judged on."""

    symbol: str
    name: str
    asset_class: str
    instrument_type: str
    observations: int
    annualized_return: float
    annualized_volatility: float
    series: PriceSeries


@dataclass(frozen=True)
class ScreenedCandidateSecurities:
    """Screened Candidate Securities: F.4 output to F.5."""

    candidates: list[Candidate]
    exclusions: list[Exclusion]
    data_limitations: list[str]
    snapshot_id: str | None


@dataclass(frozen=True)
class Recommendation:
    """One recommended security and its weight in the simulated portfolio."""

    symbol: str
    asset_class: str
    weight: float  # share of the simulated portfolio, 0 to 1
    name: str = ""
    instrument_type: str = ""  # "ETF" or "Stock"


@dataclass(frozen=True)
class PlanMetrics:
    """How the recommended mix behaved in the historical sample. Not a forecast."""

    start: str
    end: str
    observations: int
    annualized_return: float
    annualized_volatility: float
    worst_one_year_return: float | None


@dataclass(frozen=True)
class InvestmentRecommendationsAndWeights:
    """Investment Recommendations and Weights: F.5 output, F.6 input (IF.6)."""

    risk_score: int
    risk_category: str
    target_allocation: dict[str, float]  # asset class -> share of the portfolio
    recommendations: list[Recommendation]
    identified_risks: list[str]  # keys into the Explanation Rules risk_language
    data_limitations: list[str]
    profile_basis: dict = field(default_factory=dict)
    risk_drivers: list[dict] = field(default_factory=list)  # {"label", "answer", "effect"}
    allocation_adjustments: list[str] = field(default_factory=list)
    plan_metrics: PlanMetrics | None = None
    max_one_year_loss: float | None = None
    data_snapshot_id: str | None = None
    rules_configuration_id: str | None = None

    @property
    def plan_id(self) -> str:
        """Identity of this plan, derived from its content.

        A plan with different content gets a different identity, so a save
        request for a superseded plan no longer matches (CS6.1.4.3).
        """
        content = json.dumps(asdict(self), sort_keys=True)
        return "plan-" + hashlib.sha256(content.encode()).hexdigest()[:10]
