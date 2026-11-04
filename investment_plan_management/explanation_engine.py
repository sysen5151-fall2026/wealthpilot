"""F.6.1 Explain Investment Plan, performed by C.6.1 Explanation Engine.

Satisfies CS6.1.4.1; also CS6.1.1.1, CS6.1.1.2, CS6.1.2.1, SR-02 and SR-03.

ICOM from the second-level IDEF0 of F.6:
    input      Investment Recommendations and Weights (from F.5, over EF.15)
    control    Explanation Rules (from X.3, over EF.14)
    output     Investment Plan Explanation (to F.6.2 over IF.6.1, to X.1 over EF.16)
    mechanism  C.6.1 Explanation Engine, optionally with a local language model

The two paths of the SPEC.md Model Response Contract:

- The deterministic template always runs. It explains the plan from the
  evidence carried in the flow: the risk score and the answers that moved it
  most, the constraints that changed the starting mix, the holdings in each
  asset class, the planning inputs, and what the historical sample shows.
- If a language model is given (language_model.py), it is asked to word the
  same facts. Its response is used only if it passes every check of the
  contract: all fields present, limitations preserved, the approved scope
  notice, no prohibited phrase, and no number that is not in the facts.
  Otherwise the template is returned and generation_note says why.
"""

import json
import re
from dataclasses import replace

from .io_types import (
    ExplanationRules,
    InvestmentPlanExplanation,
    InvestmentRecommendationsAndWeights,
)
from .language_model import LanguageModel, LanguageModelError

RESPONSE_FIELDS = ("summary", "allocation_rationale", "material_risks", "data_limitations", "scope_notice")
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "allocation_rationale": {"type": "array", "items": {"type": "string"}},
        "material_risks": {"type": "array", "items": {"type": "string"}},
        "data_limitations": {"type": "array", "items": {"type": "string"}},
        "scope_notice": {"type": "string"},
    },
    "required": list(RESPONSE_FIELDS),
    "additionalProperties": False,
}
MAX_SENTENCE_LENGTH = 600
MAX_ITEMS = 12
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
STRUCTURAL_NUMBERS = {0.0, 1.0, 100.0}  # "one year", "out of 100"


def explain_investment_plan(
    recommendations_and_weights: InvestmentRecommendationsAndWeights,
    *,
    explanation_rules: ExplanationRules,
    language_model: LanguageModel | None = None,
) -> InvestmentPlanExplanation:
    """Explain how the investor's profile and risk assessment led to this plan, and its risks.

    Raises ValueError if the plan has no identified risk, if a risk has no
    novice-language wording in the rules, or if the template text breaks a rule.
    """
    plan = recommendations_and_weights
    rules = explanation_rules
    template = _template_explanation(plan, rules)
    _check_wording(template, rules)
    if language_model is None:
        return template

    facts = contract_input(plan, rules, template)
    try:
        response = language_model.complete_json(_system_prompt(rules), json.dumps(facts, indent=1), RESPONSE_SCHEMA)
    except LanguageModelError as error:
        return replace(template, generation_note=f"The language model was not used: {error}")
    problem = response_problem(response, plan, rules, facts)
    if problem:
        return replace(template, generation_note=f"The language model's response was rejected: {problem}.")
    return InvestmentPlanExplanation(
        plan_id=plan.plan_id,
        rules_version=rules.version,
        summary=response["summary"].strip(),
        allocation_rationale=[line.strip() for line in response["allocation_rationale"]],
        material_risks=[line.strip() for line in response["material_risks"]],
        data_limitations=list(plan.data_limitations),
        scope_notice=rules.scope_notice,
        historical_evidence=template.historical_evidence,
        generated_by=f"language model {language_model.name}",
    )


# The deterministic template

def _template_explanation(
    plan: InvestmentRecommendationsAndWeights, rules: ExplanationRules
) -> InvestmentPlanExplanation:
    return InvestmentPlanExplanation(
        plan_id=plan.plan_id,
        rules_version=rules.version,
        summary=_summary(plan),
        allocation_rationale=[
            f"Your answers gave a risk score of {plan.risk_score} out of 100, which places you in the "
            f"{plan.risk_category} category.",
            *(_describe_driver(driver) for driver in plan.risk_drivers),
            *_describe_adjustments(plan),
            *(_describe_asset_class(asset_class, share, plan) for asset_class, share in plan.target_allocation.items()),
            *_describe_planning_inputs(plan.profile_basis),
        ],
        material_risks=_describe_risks(plan.identified_risks, rules),
        data_limitations=list(plan.data_limitations),
        scope_notice=rules.scope_notice,
        historical_evidence=_historical_evidence(plan),
    )


def _summary(plan: InvestmentRecommendationsAndWeights) -> str:
    basis = plan.profile_basis
    purpose = ""
    if basis.get("goal_label") and basis.get("horizon_years"):
        purpose = f" for {basis['goal_label'].lower()} in {years(basis['horizon_years'])}"
    return f"This simulated {plan.risk_category} plan{purpose} puts {_describe_allocation(plan.target_allocation)}."


def _describe_allocation(target_allocation: dict[str, float]) -> str:
    parts = [f"{share:.0%} in {asset_class}" for asset_class, share in target_allocation.items()]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _describe_driver(driver: dict) -> str:
    return f"Your answer about {driver['label']} (“{driver['answer']}”) {driver['effect']}."


def _describe_adjustments(plan: InvestmentRecommendationsAndWeights) -> list[str]:
    if plan.allocation_adjustments:
        return list(plan.allocation_adjustments)
    if plan.profile_basis:
        return [
            f"The starting mix for the {plan.risk_category} category needed no change for your horizon, "
            "your chance of needing the money early, or your loss limit."
        ]
    return []


def _describe_asset_class(asset_class: str, share: float, plan: InvestmentRecommendationsAndWeights) -> str:
    holdings = ", ".join(
        f"{r.symbol} {r.weight:.0%}" + (f" ({r.name})" if r.name else "")
        for r in plan.recommendations
        if r.asset_class == asset_class
    )
    return f"{asset_class} {share:.0%}: {holdings}."


def _describe_planning_inputs(basis: dict) -> list[str]:
    if not basis:
        return []
    cash, held = basis["investable_savings"], basis["current_holdings_value"]
    if basis["current_holdings"]:
        listing = ", ".join(f"{h['symbol']} {usd(h['value'])}" for h in basis["current_holdings"])
        lines = [f"The plan covers {usd(cash + held)}: {usd(cash)} of cash plus your current holdings ({listing})."]
    else:
        lines = [f"The plan covers the {usd(cash)} of cash you entered; you listed no current holdings."]
    if basis.get("monthly_contribution"):
        lines.append(
            f"Your {usd(basis['monthly_contribution'])} monthly contribution is recorded with the plan; "
            "the amounts shown cover what you have today."
        )
    lines.append("Saving this plan does not change your simulated cash or holdings.")
    return lines


def _describe_risks(identified_risks: list[str], rules: ExplanationRules) -> list[str]:
    if not identified_risks:
        raise ValueError("CS6.1.4.1 needs at least one identified risk for every plan")
    unworded = [risk for risk in identified_risks if risk not in rules.risk_language]
    if unworded:
        raise ValueError(f"Explanation Rules {rules.version} have no novice wording for: {', '.join(unworded)}")
    return [rules.risk_language[risk] for risk in identified_risks]


def _historical_evidence(plan: InvestmentRecommendationsAndWeights) -> list[str]:
    metrics = plan.plan_metrics
    if metrics is None:
        return ["No historical evidence is available for this mix."]
    snapshot = f" in price snapshot {plan.data_snapshot_id}" if plan.data_snapshot_id else ""
    direction = "gained" if metrics.annualized_return >= 0 else "lost"
    lines = [
        f"From {metrics.start} to {metrics.end} ({metrics.observations:,} trading days{snapshot}), this mix "
        f"{direction} {abs(metrics.annualized_return):.1%} a year on average, and its yearly volatility "
        f"(how much its value typically moved) was {metrics.annualized_volatility:.1%}."
    ]
    worst = metrics.worst_one_year_return
    if worst is None:
        lines.append("The sample is shorter than one year, so no one-year result is shown.")
    else:
        result = f"a {abs(worst):.1%} loss" if worst < 0 else f"still a {worst:.1%} gain"
        limit = ""
        if plan.max_one_year_loss is not None:
            limit = f"; you said you could accept a one-year loss of up to {plan.max_one_year_loss:.0%}"
            if worst < -plan.max_one_year_loss:
                limit += ", so this plan went beyond your limit in that period"
        lines.append(f"Its worst one-year result in that period was {result}{limit}.")
    lines.append("These figures describe the historical sample only and do not predict future results.")
    return lines


def _check_wording(explanation: InvestmentPlanExplanation, rules: ExplanationRules) -> None:
    texts = [
        explanation.summary,
        *explanation.allocation_rationale,
        *explanation.material_risks,
        *explanation.data_limitations,
        *explanation.historical_evidence,
    ]
    for text in texts:
        phrase = rules.first_prohibited_phrase(text)
        if phrase:
            raise ValueError(f"explanation breaks Explanation Rules {rules.version}: '{phrase}'")


# The language-model path

def contract_input(
    plan: InvestmentRecommendationsAndWeights, rules: ExplanationRules, template: InvestmentPlanExplanation
) -> dict:
    """The facts given to the model: the SPEC input schema, plus the evidence the template explains."""
    basis = plan.profile_basis
    return {
        "risk_score": plan.risk_score,
        "risk_level": plan.risk_category,
        "planning_inputs": {
            "goal": basis.get("goal_label", ""),
            "investment_horizon": years(basis["horizon_years"]) if "horizon_years" in basis else "",
            "financial_capacity": _financial_capacity(basis),
            "liquidity_needs": basis.get("liquidity_label", ""),
            "experience": basis.get("experience", ""),
        },
        "target_allocation": [{"asset_class": c, "weight": w} for c, w in plan.target_allocation.items()],
        "candidate_securities": [
            {"symbol": r.symbol, "name": r.name, "asset_class": r.asset_class, "weight": r.weight, "risk_metrics": {}}
            for r in plan.recommendations
        ],
        "identified_risks": list(plan.identified_risks),
        "data_limitations": list(plan.data_limitations),
        "risk_drivers": plan.risk_drivers,
        "allocation_adjustments": list(plan.allocation_adjustments),
        "approved_risk_wording": {risk: rules.risk_language[risk] for risk in plan.identified_risks},
        "historical_evidence": template.historical_evidence,
        "scope_notice": rules.scope_notice,
    }


def response_problem(response, plan: InvestmentRecommendationsAndWeights, rules: ExplanationRules, facts: dict) -> str | None:
    """Why a model response breaks the Model Response Contract, or None if it is acceptable."""
    if not isinstance(response, dict):
        return "it is not a JSON object"
    missing = [name for name in RESPONSE_FIELDS if name not in response]
    if missing:
        return "it is missing " + ", ".join(missing)
    for name in ("summary", "scope_notice"):
        if not isinstance(response[name], str) or not response[name].strip():
            return f"{name} is empty"
    for name in ("allocation_rationale", "material_risks", "data_limitations"):
        items = response[name]
        if not isinstance(items, list) or not all(isinstance(item, str) and item.strip() for item in items):
            return f"{name} is not a list of sentences"
        if len(items) > MAX_ITEMS:
            return f"{name} has more than {MAX_ITEMS} items"
    if not response["allocation_rationale"]:
        return "allocation_rationale is empty"
    if plan.identified_risks and not response["material_risks"]:
        return "material_risks is empty although the plan has identified risks"
    if sorted(line.strip() for line in response["data_limitations"]) != sorted(plan.data_limitations):
        return "data_limitations do not repeat the plan's limitations exactly"
    if response["scope_notice"].strip() != rules.scope_notice:
        return "scope_notice is not the approved notice"

    texts = [response["summary"], *response["allocation_rationale"], *response["material_risks"]]
    if any(len(text) > MAX_SENTENCE_LENGTH for text in texts):
        return "a sentence is too long"
    for text in texts:
        phrase = rules.first_prohibited_phrase(text)
        if phrase:
            return f"it uses the prohibited phrase '{phrase}'"
    allowed = _numbers_in_facts(facts)
    for text in texts:
        for number in _numbers_in_text(text):
            if number not in allowed:
                return f"it states the number {number:g}, which is not in the plan"
    return None


def _system_prompt(rules: ExplanationRules) -> str:
    return (
        "You explain an educational investment-planning simulation to a beginner. "
        "The user message is the authoritative plan as JSON. Reply with one JSON object with exactly these keys: "
        "summary (two or three plain sentences); "
        "allocation_rationale (three to eight short sentences on how the investor's answers and planning inputs "
        "led to this mix, naming at least two of the risk_drivers and every allocation adjustment); "
        "material_risks (one sentence for each identified risk, based on approved_risk_wording); "
        "data_limitations (copy the data_limitations list exactly; [] if it is empty); "
        f'scope_notice (copy exactly: "{rules.scope_notice}"). '
        "Use only the facts given. Do not change, re-round or invent any number, percentage, dollar amount, "
        "date or ticker. Do not tell the reader to buy or sell anything, and do not suggest that any real trade "
        "or transfer happens. Never use these phrases: " + ", ".join(rules.prohibited_phrases) + "."
    )


def _financial_capacity(basis: dict) -> str:
    if not basis:
        return ""
    return (
        f"{usd(basis['investable_savings'])} of cash to invest, {usd(basis['current_holdings_value'])} in current "
        f"holdings, {usd(basis['monthly_contribution'])} monthly contribution, "
        f"{usd(basis['annual_income'])} annual income"
    )


def _numbers_in_facts(facts) -> set[float]:
    """Every number a correct explanation may state, including fractions written as percentages."""
    found = set(STRUCTURAL_NUMBERS)

    def walk(value) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            magnitude = abs(float(value))
            found.add(round(magnitude, 2))
            if isinstance(value, float) and magnitude <= 1:
                for digits in (0, 1, 2):
                    found.add(round(magnitude * 100, digits))
        elif isinstance(value, str):
            found.update(_numbers_in_text(value))
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(facts)
    return found


def _numbers_in_text(text: str) -> list[float]:
    return [round(float(match.replace(",", "")), 2) for match in NUMBER.findall(text)]


def years(count: int) -> str:
    return "1 year" if count == 1 else f"{count} years"


def usd(amount: float) -> str:
    return f"${amount:,.0f}"
