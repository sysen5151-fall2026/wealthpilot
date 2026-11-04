"""F.1 Collect Investor Information, performed by C.1 Investor Information Interface.

Satisfies 1.4.1; also 1.1.2, 1.1.4, 1.1.11, 1.1.14 and 1.2.4.

ICOM from the first-level IDEF0 of F.0:
    inputs     Financial Profile, Risk Questionnaire Responses, Current Holdings (from X.1)
    controls   Investment Planning Constraints (from X.3)
               Session Initiation Command (from X.1)
    outputs    Requests for Investor Input (to X.1)
               Investor Profile and Risk Questionnaire Responses (to F.2)
    mechanism  C.1 Investor Information Interface

The browser front end (frontend/) and the console run (console.py, a sample
investor) are the two ways X.1 answers these requests.
"""

import math
import re

from model_flows import Holding, InvestorProfileAndResponses

SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")


class InvestorInputError(ValueError):
    """The supplied information breaks the Investment Planning Constraints."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def requests_for_investor_input(*, investment_planning_constraints: dict) -> dict:
    """Requests for Investor Input: every question UC.1 asks, with its allowed answers."""
    constraints = investment_planning_constraints
    return {
        "financial_profile_fields": constraints["financial_profile_fields"],
        "risk_questionnaire": constraints["risk_questionnaire"],
        "current_holdings": {
            "max_holdings": constraints["max_holdings"],
            "fields": {"symbol": "Ticker symbol, for example VTI", "value": "Hypothetical value in USD"},
        },
    }


def collect_investor_information(
    financial_profile: dict,
    risk_questionnaire_responses: dict,
    current_holdings: list[dict],
    *,
    investment_planning_constraints: dict,
    session_initiation_command: str,
) -> InvestorProfileAndResponses:
    """Check every answer against the constraints and consolidate them unchanged.

    Raises InvestorInputError listing every problem, so the investor can fix
    them all at once.
    """
    if not session_initiation_command:
        raise InvestorInputError(["no session has been started"])
    constraints = investment_planning_constraints
    errors = [
        *_profile_errors(financial_profile, constraints["financial_profile_fields"]),
        *_questionnaire_errors(risk_questionnaire_responses, constraints["risk_questionnaire"]),
        *_holdings_errors(current_holdings, constraints["max_holdings"]),
    ]
    if errors:
        raise InvestorInputError(errors)

    return InvestorProfileAndResponses(
        session_id=session_initiation_command,
        financial_profile=dict(financial_profile),
        risk_questionnaire_responses=dict(risk_questionnaire_responses),
        current_holdings=[Holding(h["symbol"], float(h["value"])) for h in current_holdings],
        answer_labels=_answer_labels(financial_profile, risk_questionnaire_responses, constraints),
    )


def _profile_errors(profile: dict, fields: dict) -> list[str]:
    errors = [f"unexpected field '{name}'" for name in profile if name not in fields]
    for name, spec in fields.items():
        value = profile.get(name)
        label = spec["label"]
        if value is None:
            errors.append(f"{label} is required")
        elif spec["type"] == "choice":
            if not isinstance(value, str) or value not in spec["options"]:
                errors.append(f"{label} must be one of: {', '.join(spec['options'].values())}")
        elif not _is_number(value) or (spec["type"] == "integer" and not float(value).is_integer()):
            kind = "a whole number" if spec["type"] == "integer" else "a number"
            errors.append(f"{label} must be {kind}")
        elif not spec["min"] <= value <= spec["max"]:
            errors.append(f"{label} must be between {spec['min']:,} and {spec['max']:,}")
    return errors


def _questionnaire_errors(responses: dict, questions: list[dict]) -> list[str]:
    known = {q["id"] for q in questions}
    errors = [f"unexpected question '{question_id}'" for question_id in responses if question_id not in known]
    for question in questions:
        answer = responses.get(question["id"])
        if not isinstance(answer, str) or answer not in question["options"]:
            errors.append(f"Please answer: {question['text']}")
    return errors


def _holdings_errors(holdings: list[dict], max_holdings: int) -> list[str]:
    if len(holdings) > max_holdings:
        return [f"at most {max_holdings} holdings can be entered"]
    errors, seen = [], set()
    for position, holding in enumerate(holdings, start=1):
        if not isinstance(holding, dict):
            errors.append(f"holding {position}: give a symbol and a value")
            continue
        symbol, value = holding.get("symbol"), holding.get("value")
        if not isinstance(symbol, str) or not SYMBOL_PATTERN.match(symbol):
            errors.append(f"holding {position}: '{symbol}' is not a ticker symbol (capital letters, up to 10)")
        elif symbol in seen:
            errors.append(f"holding {position}: {symbol} is listed twice")
        seen.add(symbol)
        if not _is_number(value) or value < 0:
            errors.append(f"holding {position}: value must be a number of zero or more")
    return errors


def _answer_labels(profile: dict, responses: dict, constraints: dict) -> dict:
    """The wording of each chosen answer, so later functions can explain it."""
    labels = {
        name: spec["options"][profile[name]]
        for name, spec in constraints["financial_profile_fields"].items()
        if spec["type"] == "choice"
    }
    for question in constraints["risk_questionnaire"]:
        labels[question["id"]] = question["options"][responses[question["id"]]]
    return labels


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
