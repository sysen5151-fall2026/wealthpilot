"""F.6.2 Present Investment Plan, performed by C.6.2 Plan Presentation Component.

Satisfies CS6.1.4.2; also CS6.1.1.2, CS6.1.2.2 and SR-13.

ICOM from the second-level IDEF0 of F.6:
    inputs     Investment Recommendations and Weights (from F.5, over EF.18)
               Investment Plan Explanation (from F.6.1, over IF.6.1)
    control    Explanation Rules (from X.3, over EF.17)
    outputs    Presented Investment Plan (to X.1, over EF.19)
               IO.6.1 Reviewed Plan Snapshot (to F.6.3, over IF.6.2)
    mechanism  C.6.2 Plan Presentation Component

The snapshot is assembled first, and both the display text and the structured
content the browser shows are built from it alone, so what the investor sees
is exactly what F.6.3 to F.6.5 can save. The simulated amounts show what each
weight means for the investor's cash plus current holdings; nothing moves.
"""

from dataclasses import asdict

from .explanation_engine import share_text
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
        risk_score=plan.risk_score,
        profile_basis=dict(plan.profile_basis),
        simulated_amounts=_simulated_amounts(plan),
        plan_metrics=plan.plan_metrics,
        data_snapshot_id=plan.data_snapshot_id,
        rules_configuration_id=plan.rules_configuration_id,
    )
    display_text = _render(snapshot, explanation_rules.learner_actions)
    phrase = explanation_rules.first_prohibited_phrase(display_text)
    if phrase:
        raise ValueError(f"display breaks Explanation Rules {explanation_rules.version}: '{phrase}'")

    presented = PresentedInvestmentPlan(
        plan_id=snapshot.plan_id,
        display_text=display_text,
        learner_actions=list(explanation_rules.learner_actions),
        content=asdict(snapshot),
    )
    return presented, snapshot


def _simulated_amounts(plan: InvestmentRecommendationsAndWeights) -> dict:
    """What each weight means in dollars for the investor's cash plus current holdings."""
    basis = plan.profile_basis
    if not basis:
        return {}
    cash = float(basis["investable_savings"])
    holdings = {h["symbol"]: float(h["value"]) for h in basis["current_holdings"]}
    total = cash + sum(holdings.values())
    rows = []
    for r in plan.recommendations:
        target = round(total * r.weight, 2)
        current = holdings.get(r.symbol, 0.0)
        rows.append({"symbol": r.symbol, "in_plan": True, "plan": target, "current": current,
                     "difference": round(target - current, 2)})
    planned = {r.symbol for r in plan.recommendations}
    for symbol, value in holdings.items():
        if symbol not in planned:
            rows.append({"symbol": symbol, "in_plan": False, "plan": 0.0, "current": value, "difference": -value})
    return {"total": total, "cash": cash, "current_holdings_value": sum(holdings.values()), "by_symbol": rows}


def _render(snapshot: ReviewedPlanSnapshot, learner_actions: list[str]) -> str:
    """Display text, built only from the snapshot so the two cannot disagree."""
    explanation = snapshot.explanation
    allocation = ", ".join(f"{asset_class} {share_text(share)}" for asset_class, share in snapshot.target_allocation.items())
    amounts = {row["symbol"]: row for row in snapshot.simulated_amounts.get("by_symbol", [])}
    risk = snapshot.risk_category + (f" (risk score {snapshot.risk_score} of 100)" if snapshot.risk_score is not None else "")

    lines = [
        f"=== SIMULATED EDUCATIONAL PLAN {snapshot.plan_id} ===",
        snapshot.scope_notice,
        f"Risk category: {risk}",
        f"Target allocation: {allocation}",
    ]
    if snapshot.simulated_amounts:
        total = snapshot.simulated_amounts
        lines.append(
            f"Planned amount: {_usd(total['total'])} ({_usd(total['cash'])} cash + "
            f"{_usd(total['current_holdings_value'])} current holdings)"
        )
    lines.append("Candidate securities:")
    for r in snapshot.recommendations:
        line = f"  {r.symbol:<6}{r.asset_class:<22}{share_text(r.weight):>6}"
        if r.symbol in amounts:
            line += f"  {_usd(amounts[r.symbol]['plan']):>12}"
            if amounts[r.symbol]["current"]:
                line += f"  (you hold {_usd(amounts[r.symbol]['current'])})"
        lines.append(line)
    outside = [row for row in amounts.values() if not row["in_plan"]]
    if outside:
        lines.append("Current holdings outside this plan: " + ", ".join(
            f"{row['symbol']} {_usd(row['current'])}" for row in outside))
    lines += [
        f"Summary: {explanation.summary}",
        "Why this plan:",
        *(f"  - {line}" for line in explanation.allocation_rationale),
        "Risks to know:",
        *(f"  - {line}" for line in explanation.material_risks),
    ]
    if explanation.historical_evidence:
        lines += ["What the historical sample shows:", *(f"  - {line}" for line in explanation.historical_evidence)]
    lines += [
        "Data limitations:",
        *(f"  - {line}" for line in explanation.data_limitations or ["none reported"]),
        f"Explanation written by: {explanation.generated_by}",
        "Your options: " + "; ".join(learner_actions),
    ]
    return "\n".join(lines)


def _usd(amount: float) -> str:
    return f"${amount:,.0f}"
