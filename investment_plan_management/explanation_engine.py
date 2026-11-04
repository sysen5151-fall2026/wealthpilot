"""F.6.1 Explain Investment Plan, performed by C.6.1 Explanation Engine.

Satisfies CS6.1.4.1; also CS6.1.1.1, CS6.1.1.2 and CS6.1.2.1.

ICOM from the second-level IDEF0 of F.6:
    input      Investment Recommendations and Weights (from F.5, over EF.15)
    control    Explanation Rules (from X.3, over EF.14)
    output     Investment Plan Explanation (to F.6.2 over IF.6.1, to X.1 over EF.16)
    mechanism  C.6.1 Explanation Engine

The explanation is built from a fixed template: the deterministic path in the
SPEC.md Model Response Contract. No language model is called yet.
"""

from .io_types import (
    ExplanationRules,
    InvestmentPlanExplanation,
    InvestmentRecommendationsAndWeights,
)


def explain_investment_plan(
    recommendations_and_weights: InvestmentRecommendationsAndWeights,
    *,
    explanation_rules: ExplanationRules,
) -> InvestmentPlanExplanation:
    """Explain how the risk assessment led to this plan, and what its risks are.

    Raises ValueError if the plan has no identified risk, if a risk has no
    novice-language wording in the rules, or if the text breaks a rule.
    """
    plan = recommendations_and_weights
    explanation = InvestmentPlanExplanation(
        plan_id=plan.plan_id,
        rules_version=explanation_rules.version,
        summary=f"This simulated plan puts {_describe_allocation(plan.target_allocation)}.",
        allocation_rationale=[
            f"Your risk assessment placed you in the {plan.risk_category} category "
            f"(risk score {plan.risk_score}), and the allocation rules map that category to this split.",
            *(
                _describe_asset_class(asset_class, share, plan)
                for asset_class, share in plan.target_allocation.items()
            ),
        ],
        material_risks=_describe_risks(plan.identified_risks, explanation_rules),
        data_limitations=list(plan.data_limitations),
        scope_notice=explanation_rules.scope_notice,
    )
    _check_wording(explanation, explanation_rules)
    return explanation


def _describe_allocation(target_allocation: dict[str, float]) -> str:
    parts = [f"{share:.0%} in {asset_class}" for asset_class, share in target_allocation.items()]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _describe_asset_class(
    asset_class: str, share: float, plan: InvestmentRecommendationsAndWeights
) -> str:
    holdings = ", ".join(
        f"{r.symbol} {r.weight:.0%}" for r in plan.recommendations if r.asset_class == asset_class
    )
    return f"{asset_class} {share:.0%}: {holdings}."


def _describe_risks(identified_risks: list[str], rules: ExplanationRules) -> list[str]:
    if not identified_risks:
        raise ValueError("CS6.1.4.1 needs at least one identified risk for every plan")
    unworded = [risk for risk in identified_risks if risk not in rules.risk_language]
    if unworded:
        raise ValueError(
            f"Explanation Rules {rules.version} have no novice wording for: {', '.join(unworded)}"
        )
    return [rules.risk_language[risk] for risk in identified_risks]


def _check_wording(explanation: InvestmentPlanExplanation, rules: ExplanationRules) -> None:
    texts = [
        explanation.summary,
        *explanation.allocation_rationale,
        *explanation.material_risks,
        *explanation.data_limitations,
    ]
    for text in texts:
        phrase = rules.first_prohibited_phrase(text)
        if phrase:
            raise ValueError(f"explanation breaks Explanation Rules {rules.version}: '{phrase}'")
