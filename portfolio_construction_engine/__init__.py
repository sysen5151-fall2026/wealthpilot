"""F.5 Generate Investment Recommendations, performed by C.5 Portfolio Construction Engine.

Satisfies 1.4.5; also 1.1.9.

ICOM from the first-level IDEF0 of F.0:
    input      Screened Candidate Securities (from F.4)
    controls   Target Asset Allocation (from F.3)
               Portfolio Construction Rules (from X.3, over EF.11)
    output     Investment Recommendations and Weights (to F.6, over IF.6)
    mechanism  C.5 Portfolio Construction Engine

Within each asset class, every individual stock gets a small capped weight and
the funds share the rest equally; a class with only stocks shares its weight
among them. If a class has no candidate, its share goes to the other classes
and a limitation says so. The plan's historical behaviour is measured on the
candidates' admitted prices.
"""

from dataclasses import replace

from historical_analysis import (
    annualized_return,
    annualized_volatility,
    daily_returns,
    mix_value_path,
    worst_one_year_return,
)
from model_flows import (
    InvestmentRecommendationsAndWeights,
    PlanMetrics,
    Recommendation,
    ScreenedCandidateSecurities,
    TargetAssetAllocation,
)

PRECISION = 4


def generate_investment_recommendations(
    screened_candidate_securities: ScreenedCandidateSecurities,
    *,
    target_asset_allocation: TargetAssetAllocation,
    portfolio_construction_rules: dict,
    minimum_observations: int = 2,
) -> InvestmentRecommendationsAndWeights:
    """Weight the screened candidates so each asset class gets its target share.

    Raises ValueError if no candidate survived screening at all.
    """
    rules = portfolio_construction_rules
    screened = screened_candidate_securities
    if not screened.candidates:
        raise ValueError("no security passed screening, so no plan can be built")

    shares, limitations = _shares_with_candidates(target_asset_allocation.weights, screened)
    recommendations = []
    for asset_class, share in shares.items():
        members = [c for c in screened.candidates if c.asset_class == asset_class]
        stocks = [c for c in members if c.instrument_type == "Stock"]
        funds = [c for c in members if c.instrument_type != "Stock"]
        if funds:
            stock_weight = min(rules["single_stock_max_weight"], share * rules["max_stock_share_of_class"] / len(stocks)) if stocks else 0.0
            fund_weight = (share - stock_weight * len(stocks)) / len(funds)
        else:
            stock_weight, fund_weight = share / len(stocks), 0.0
        for candidate in members:
            weight = stock_weight if candidate.instrument_type == "Stock" else fund_weight
            recommendations.append(
                Recommendation(candidate.symbol, asset_class, weight, candidate.name, candidate.instrument_type)
            )
    recommendations = _rounded(recommendations)

    series = {c.symbol: c.series for c in screened.candidates}
    dates, values = mix_value_path(series, {r.symbol: r.weight for r in recommendations})
    metrics = None
    if len(dates) >= max(2, minimum_observations):
        metrics = PlanMetrics(
            start=dates[0],
            end=dates[-1],
            observations=len(dates),
            annualized_return=round(annualized_return(dates, values), PRECISION),
            annualized_volatility=round(annualized_volatility(daily_returns(values)), PRECISION),
            worst_one_year_return=_round_or_none(worst_one_year_return(values)),
        )
    else:
        limitations.append(
            f"The recommended securities share only {len(dates)} trading days, fewer than the "
            f"{max(2, minimum_observations)} required to measure the plan's history; historical metrics are withheld."
        )
    risk = target_asset_allocation.risk_assessment
    return InvestmentRecommendationsAndWeights(
        risk_score=risk.risk_score,
        risk_category=risk.risk_category,
        target_allocation={c: round(s, PRECISION) for c, s in shares.items()},
        recommendations=recommendations,
        identified_risks=_identify_risks(shares, recommendations, target_asset_allocation, metrics, rules),
        data_limitations=[*screened.data_limitations, *target_asset_allocation.limitations, *limitations],
        profile_basis=risk.profile_basis,
        risk_drivers=[
            {"label": f.label, "answer": f.answer, "effect": _effect(f.lean)} for f in risk.strongest_factors()
        ],
        allocation_adjustments=list(target_asset_allocation.adjustments),
        plan_metrics=metrics,
        max_one_year_loss=risk.max_one_year_loss,
        data_snapshot_id=screened.snapshot_id,
        rules_configuration_id=rules.get("configuration_id"),
    )


def _shares_with_candidates(weights: dict, screened: ScreenedCandidateSecurities) -> tuple[dict, list[str]]:
    """Give the share of any class without candidates to the classes that have them."""
    covered = {c.asset_class for c in screened.candidates}
    empty = [c for c, w in weights.items() if w > 0 and c not in covered]
    kept = {c: w for c, w in weights.items() if w > 0 and c in covered}
    total = sum(kept.values())
    shares = {c: w / total for c, w in kept.items()}
    limitations = [
        f"No {c} security passed screening, so its {weights[c]:.0%} was spread over the other asset classes."
        for c in empty
    ]
    return shares, limitations


def _identify_risks(shares, recommendations, target, metrics, rules) -> list[str]:
    risks = [risk for asset_class in shares for risk in rules["class_risks"][asset_class]]
    if any(r.instrument_type == "Stock" and r.weight > rules["concentration_flag_weight"] for r in recommendations):
        risks.append("concentration")
    cash_share = sum(s for c, s in shares.items() if c in rules["cash_classes"])
    if cash_share >= rules["cash_inflation_flag_weight"]:
        risks.append("inflation")
    risks += target.planning_flags
    worst = metrics.worst_one_year_return if metrics else None
    if worst is not None and worst < -target.risk_assessment.max_one_year_loss:
        risks.append("loss_tolerance")
    return list(dict.fromkeys(risks))


def _effect(lean: float) -> str:
    if lean > 0:
        return "pushed your score up"
    if lean < 0:
        return "pulled your score down"
    return "kept your score in the middle"


def _rounded(recommendations: list[Recommendation]) -> list[Recommendation]:
    rounded = [replace(r, weight=round(r.weight, PRECISION)) for r in recommendations]
    residual = round(1 - sum(r.weight for r in rounded), PRECISION)
    if residual:
        i = max(range(len(rounded)), key=lambda k: rounded[k].weight)
        rounded[i] = replace(rounded[i], weight=round(rounded[i].weight + residual, PRECISION))
    return rounded


def _round_or_none(value: float | None) -> float | None:
    return None if value is None else round(value, PRECISION)
