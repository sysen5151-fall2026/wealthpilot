"""F.2 Assess Investor Risk Profile, performed by C.2 Risk Assessment Engine.

Satisfies 1.4.2; also 1.1.12 and 1.2.5.

ICOM from the first-level IDEF0 of F.0:
    input      Investor Profile and Risk Questionnaire Responses (from F.1)
    control    Risk Scoring Rules (from X.3)
    output     Risk Score and Risk Category (to F.3 and X.1)
    mechanism  C.2 Risk Assessment Engine

Each questionnaire answer, the horizon and the liquidity need earn points; the
total is scaled to 0-100 and mapped to the first category whose upper bound it
does not exceed. The rules are in config/rules.json; docs/rules-rationale.md explains them.
"""

from model_flows import InvestorProfileAndResponses, RiskFactor, RiskScoreAndCategory


def assess_investor_risk_profile(
    investor_profile_and_responses: InvestorProfileAndResponses,
    *,
    risk_scoring_rules: dict,
) -> RiskScoreAndCategory:
    """Score the investor's answers with the Risk Scoring Rules."""
    investor = investor_profile_and_responses
    rules = risk_scoring_rules
    profile = investor.financial_profile
    labels = investor.answer_labels

    factors = [
        RiskFactor(
            factor=question_id,
            label=rules["factor_labels"][question_id],
            answer=labels.get(question_id, investor.risk_questionnaire_responses[question_id]),
            points=points[investor.risk_questionnaire_responses[question_id]],
            min_points=min(points.values()),
            max_points=max(points.values()),
        )
        for question_id, points in rules["question_points"].items()
    ]
    horizon_bins = rules["horizon_points"]
    factors.append(
        RiskFactor(
            factor="horizon",
            label=rules["factor_labels"]["horizon"],
            answer=f"{profile['horizon_years']} years",
            points=next(b["points"] for b in horizon_bins if profile["horizon_years"] <= b["max_years"]),
            min_points=min(b["points"] for b in horizon_bins),
            max_points=max(b["points"] for b in horizon_bins),
        )
    )
    liquidity_points = rules["liquidity_points"]
    factors.append(
        RiskFactor(
            factor="liquidity",
            label=rules["factor_labels"]["liquidity"],
            answer=labels.get("liquidity_needs", profile["liquidity_needs"]),
            points=liquidity_points[profile["liquidity_needs"]],
            min_points=min(liquidity_points.values()),
            max_points=max(liquidity_points.values()),
        )
    )

    lowest = sum(f.min_points for f in factors)
    highest = sum(f.max_points for f in factors)
    score = round(100 * (sum(f.points for f in factors) - lowest) / (highest - lowest))
    category = next(c["name"] for c in rules["categories"] if score <= c["max_score"])

    return RiskScoreAndCategory(
        risk_score=score,
        risk_category=category,
        factors=factors,
        max_one_year_loss=rules["max_loss_values"][investor.risk_questionnaire_responses["max_loss"]],
        profile_basis=_profile_basis(investor),
        rules_version=rules["version"],
    )


def _profile_basis(investor: InvestorProfileAndResponses) -> dict:
    """The planning inputs SR-01 asks the plan to reflect, carried forward for the explanation."""
    profile = investor.financial_profile
    labels = investor.answer_labels
    holdings = [{"symbol": h.symbol, "value": h.value} for h in investor.current_holdings]
    return {
        "goal": profile["goal"],
        "goal_label": labels.get("goal", profile["goal"]),
        "horizon_years": profile["horizon_years"],
        "investable_savings": profile["investable_savings"],
        "monthly_contribution": profile["monthly_contribution"],
        "annual_income": profile["annual_income"],
        "age": profile["age"],
        "liquidity_needs": profile["liquidity_needs"],
        "liquidity_label": labels.get("liquidity_needs", profile["liquidity_needs"]),
        "experience": labels.get("experience", investor.risk_questionnaire_responses.get("experience", "")),
        "current_holdings": holdings,
        "current_holdings_value": sum(h["value"] for h in holdings),
    }
