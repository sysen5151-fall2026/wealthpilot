"""F.6.2 Present Investment Plan, performed by C.6.2 Plan Presentation Component.

Satisfies CS6.1.4.2; also CS6.1.1.2 and CS6.1.2.2.

ICOM from the second-level IDEF0 of F.6:
    inputs     Investment Recommendations and Weights (from F.5, over EF.18)
               Investment Plan Explanation (from F.6.1, over IF.6.1)
    control    Explanation Rules (from X.3, over EF.17)
    outputs    Presented Investment Plan (to X.1, over EF.19)
               IO.6.1 Reviewed Plan Snapshot (to F.6.3, over IF.6.2)
    mechanism  C.6.2 Plan Presentation Component
"""

from .io_types import (
    ExplanationRules,
    InvestmentPlanExplanation,
    InvestmentRecommendationsAndWeights,
    PresentedInvestmentPlan,
    ReviewedPlanSnapshot,
)


def present_investment_plan(
    recommendations_and_weights: InvestmentRecommendationsAndWeights,
    investment_plan_explanation: InvestmentPlanExplanation,
    *,
    explanation_rules: ExplanationRules,
) -> tuple[PresentedInvestmentPlan, ReviewedPlanSnapshot]:
    """Assemble the plan for the investor and record exactly what was shown.

    Raises ValueError if the explanation belongs to another plan, was built
    under a different Explanation Rules version, or if the display breaks a rule.
    """
    plan = recommendations_and_weights
    explanation = investment_plan_explanation
    if explanation.plan_id != plan.plan_id:
        raise ValueError("the Investment Plan Explanation belongs to a different plan")
    if explanation.rules_version != explanation_rules.version:
        raise ValueError(
            f"the explanation used Explanation Rules {explanation.rules_version}, "
            f"not the current {explanation_rules.version}"
        )

    snapshot = ReviewedPlanSnapshot(
        plan_id=plan.plan_id,
        scope_notice=explanation_rules.scope_notice,
        risk_category=plan.risk_category,
        target_allocation=dict(plan.target_allocation),
        recommendations=list(plan.recommendations),
        explanation=explanation,
    )
    display_text = _render(snapshot, explanation_rules.learner_actions)
    phrase = explanation_rules.first_prohibited_phrase(display_text)
    if phrase:
        raise ValueError(f"display breaks Explanation Rules {explanation_rules.version}: '{phrase}'")

    presented = PresentedInvestmentPlan(
        plan_id=snapshot.plan_id,
        display_text=display_text,
        learner_actions=list(explanation_rules.learner_actions),
    )
    return presented, snapshot


def _render(snapshot: ReviewedPlanSnapshot, learner_actions: list[str]) -> str:
    """Display text, built only from the snapshot so the two cannot disagree."""
    explanation = snapshot.explanation
    allocation = ", ".join(
        f"{asset_class} {share:.0%}" for asset_class, share in snapshot.target_allocation.items()
    )
    lines = [
        f"=== SIMULATED EDUCATIONAL PLAN {snapshot.plan_id} ===",
        snapshot.scope_notice,
        f"Risk category: {snapshot.risk_category}",
        f"Target allocation: {allocation}",
        "Candidate securities:",
        *(f"  {r.symbol:<6}{r.asset_class:<8}{r.weight:>5.0%}" for r in snapshot.recommendations),
        f"Summary: {explanation.summary}",
        "Why this plan:",
        *(f"  - {line}" for line in explanation.allocation_rationale),
        "Risks to know:",
        *(f"  - {line}" for line in explanation.material_risks),
        "Data limitations:",
        *(f"  - {line}" for line in explanation.data_limitations),
        "Your options: " + "; ".join(learner_actions),
    ]
    return "\n".join(lines)
