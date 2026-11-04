"""X.3 System Administrator (stub): the approved configuration WealthPilot runs under.

The controls on the IDEF0 that come from X.3, plus the Market and Regulatory
Constraints from ENV.1, are read from config/rules.json:

    Investment Planning Constraints      F.1, F.3
    Risk Scoring Rules                   F.2
    Allocation Rules                     F.3
    Security Screening Criteria          F.4
    Market and Regulatory Constraints    F.4   (ENV.1)
    Portfolio Construction Rules         F.5
    Explanation Rules                    F.6.1, F.6.2

Every value in that file is a placeholder until the team approves it. The
file is checked for internal consistency when it is loaded (1.1.1, 1.1.3,
1.1.6, 1.1.7, 1.1.9, 1.1.12, 1.1.13), so an edit that breaks it is refused
instead of producing a wrong plan.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from investment_plan_management import ExplanationRules

DEFAULT_RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "rules.json"


@dataclass(frozen=True)
class ApprovedConfiguration:
    configuration_id: str
    investment_planning_constraints: dict
    risk_scoring_rules: dict
    allocation_rules: dict
    security_screening_criteria: dict
    market_and_regulatory_constraints: dict
    portfolio_construction_rules: dict
    explanation_rules: ExplanationRules


def load_configuration(path: Path = DEFAULT_RULES_PATH) -> ApprovedConfiguration:
    """Read and check config/rules.json. Raises ValueError if it is inconsistent."""
    raw = json.loads(Path(path).read_text())
    problems = _consistency_problems(raw)
    if problems:
        raise ValueError(f"{path} is not a usable configuration: " + "; ".join(problems))
    rules = raw["explanation_rules"]

    def control(section: str) -> dict:
        # every control carries the identifier of the configuration it came from (N-06)
        return {**raw[section], "configuration_id": raw["configuration_id"]}

    return ApprovedConfiguration(
        configuration_id=raw["configuration_id"],
        investment_planning_constraints=control("investment_planning_constraints"),
        risk_scoring_rules=control("risk_scoring_rules"),
        allocation_rules=control("allocation_rules"),
        security_screening_criteria=control("security_screening_criteria"),
        market_and_regulatory_constraints=control("market_and_regulatory_constraints"),
        portfolio_construction_rules=control("portfolio_construction_rules"),
        explanation_rules=ExplanationRules(
            version=rules["version"],
            scope_notice=rules["scope_notice"],
            risk_language=rules["risk_language"],
            prohibited_phrases=rules["prohibited_phrases"],
            learner_actions=rules["learner_actions"],
        ),
    )


def get_explanation_rules() -> ExplanationRules:
    return load_configuration().explanation_rules


def get_portfolio_construction_rules() -> dict:
    return load_configuration().portfolio_construction_rules


SECTIONS = (
    "configuration_id",
    "investment_planning_constraints",
    "risk_scoring_rules",
    "allocation_rules",
    "security_screening_criteria",
    "market_and_regulatory_constraints",
    "portfolio_construction_rules",
    "explanation_rules",
)


def _consistency_problems(raw: dict) -> list[str]:
    missing = [section for section in SECTIONS if section not in raw]
    if missing:
        return [f"missing section(s): {', '.join(missing)}"]

    problems = []
    constraints = raw["investment_planning_constraints"]
    scoring = raw["risk_scoring_rules"]
    allocation = raw["allocation_rules"]
    screening = raw["security_screening_criteria"]

    for question in constraints["risk_questionnaire"]:
        points = scoring["question_points"].get(question["id"])
        if points is None or set(points) != set(question["options"]):
            problems.append(f"question '{question['id']}' options and Risk Scoring Rules points differ")
    if set(scoring["max_loss_values"]) != set(scoring["question_points"].get("max_loss", {})):
        problems.append("max_loss_values must cover every max_loss option")
    if set(scoring["liquidity_points"]) != set(constraints["financial_profile_fields"]["liquidity_needs"]["options"]):
        problems.append("liquidity_points must cover every liquidity_needs option")

    category_names = [c["name"] for c in scoring["categories"]]
    if set(allocation["by_category"]) != set(category_names):
        problems.append("Allocation Rules must define a mix for every risk category")
    if screening["category_order"] != category_names:
        problems.append("Security Screening Criteria category_order must match the risk categories")
    if screening["individual_stocks_from_category"] not in category_names:
        problems.append("individual_stocks_from_category must be a risk category")

    for category, mix in allocation["by_category"].items():
        if set(mix) != set(allocation["asset_classes"]):
            problems.append(f"the {category} mix must list every asset class")
        if abs(sum(mix.values()) - 1) > 1e-9:
            problems.append(f"the {category} mix must add up to 100%")

    for asset_class, definition in allocation["asset_classes"].items():
        for symbol in [definition["benchmark"], *definition["instruments"]]:
            metadata = screening["instruments"].get(symbol)
            if metadata is None:
                problems.append(f"{symbol} ({asset_class}) has no entry in Security Screening Criteria instruments")
            elif metadata["asset_class"] != asset_class:
                problems.append(f"{symbol} is listed under {asset_class} but tagged {metadata['asset_class']}")
        if asset_class not in screening["max_annualized_volatility"]:
            problems.append(f"no volatility limit for {asset_class}")
        if asset_class not in raw["portfolio_construction_rules"]["class_risks"]:
            problems.append(f"Portfolio Construction Rules class_risks has no entry for {asset_class}")
    for key in ("cash_class", "defensive_class"):
        if allocation[key] not in allocation["asset_classes"]:
            problems.append(f"allocation_rules {key} must be one of the asset classes")
    if not 0 < allocation["loss_tolerance_step"] <= allocation["loss_tolerance_max_shift"] <= 1:
        problems.append("allocation_rules need 0 < loss_tolerance_step <= loss_tolerance_max_shift <= 1")
    if not set(raw["portfolio_construction_rules"]["cash_classes"]) <= set(allocation["asset_classes"]):
        problems.append("portfolio_construction_rules cash_classes must be asset classes")
    known_risks = set(raw["explanation_rules"]["risk_language"])
    named_risks = {r for risks in raw["portfolio_construction_rules"]["class_risks"].values() for r in risks}
    named_risks |= {"concentration", "inflation", "short_horizon", "loss_tolerance"}
    if named_risks - known_risks:
        problems.append(f"Explanation Rules have no wording for: {', '.join(sorted(named_risks - known_risks))}")
    return problems
