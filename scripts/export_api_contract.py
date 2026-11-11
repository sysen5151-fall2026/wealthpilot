"""Export the implemented HTTP API and callable F.6 ICOM contracts.

Run from the repository root: python scripts/export_api_contract.py
The x-model-operations are in-process Python calls, not new HTTP routes.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml
from pydantic import TypeAdapter

from investment_plan_management import io_types
from wealthpilot_service.api import create_app


def ref(name):
    return {"$ref": f"#/components/schemas/{name}"}


def build_contract():
    contract = create_app().openapi()
    contract["info"]["description"] = (
        "WealthPilot UC.1 educational simulator. paths are implemented HTTP routes. "
        "x-model-operations specify local Python calls on the F.6 second-level IDEF0; "
        "they do not create network endpoints. Types describe serialized dataclass values. "
        "Cross-field authorization, plan identity and content equality are enforced by code and tests."
    )
    contract["servers"] = [{"url": "http://127.0.0.1:8000"}]
    schemas = contract.setdefault("components", {}).setdefault("schemas", {})
    names = ["InvestmentRecommendationsAndWeights", "ExplanationRules", "InvestmentPlanExplanation",
             "PresentedInvestmentPlan", "ReviewedPlanSnapshot", "PlanSaveRequest",
             "AuthorizedPlanSavePayload", "PlanPersistenceResult", "SavedInvestmentPlan", "SavedPlanConfirmation"]
    for name in names:
        schema = TypeAdapter(getattr(io_types, name)).json_schema(ref_template="#/components/schemas/{model}")
        schemas.update(schema.pop("$defs", {}))
        schemas[name] = schema

    definitions = [
        ("F.6.1", "C.6.1", "investment_plan_management.explanation_engine.explain_investment_plan",
         {"recommendations_and_weights": "InvestmentRecommendationsAndWeights"},
         {"explanation_rules": "ExplanationRules"}, {"investment_plan_explanation": "InvestmentPlanExplanation"},
         ["CS6.1.4.1", "CS6.1.2.1"], ["IF.6.1"],
         "Optional language_model is a mechanism adapter; invalid/unavailable replies fall back to the approved template. ValueError rejects unsupported risk wording or invalid explanation content."),
        ("F.6.2", "C.6.2", "investment_plan_management.plan_presentation.present_investment_plan",
         {"recommendations_and_weights": "InvestmentRecommendationsAndWeights", "investment_plan_explanation": "InvestmentPlanExplanation"},
         {"explanation_rules": "ExplanationRules"}, {"presented_investment_plan": "PresentedInvestmentPlan", "reviewed_plan_snapshot": "ReviewedPlanSnapshot"},
         ["CS6.1.4.2", "CS6.1.1.2"], ["IF.6.1", "IF.6.2"],
         "Returns a tuple in output order. A different plan_id or rules version raises ValueError. The displayed content equals the reviewed snapshot."),
        ("F.6.3", "C.6.3", "investment_plan_management.save_authorization.validate_explicit_plan_save_request",
         {"reviewed_plan_snapshot": "ReviewedPlanSnapshot"}, {"plan_save_request": "PlanSaveRequest"},
         {"authorized_plan_save_payload": "AuthorizedPlanSavePayload"},
         ["CS6.1.4.3", "CS6.1.1.3"], ["IF.6.2", "IF.6.3"],
         "plan_save_request may be None. Missing request, action other than save, empty request_id or different plan_id returns None, without persistence."),
        ("F.6.4", "C.6.4", "investment_plan_management.plan_repository.persist_reviewed_investment_plan",
         {"authorized_plan_save_payload": "AuthorizedPlanSavePayload"}, {"plan_save_request": "PlanSaveRequest"},
         {"plan_persistence_result": "PlanPersistenceResult"},
         ["CS6.1.4.4", "1.4.7", "1.4.8"], ["IF.6.3", "IF.6.4"],
         "plan_store is the repository mechanism adapter (write/read). Status is succeeded only after exact read-back. Rejected authorization yields rejected; write/read-back errors yield failed. Neither is success."),
        ("F.6.5", "C.6.5", "investment_plan_management.save_confirmation.confirm_successful_plan_save",
         {"plan_persistence_result": "PlanPersistenceResult"}, {"plan_save_request": "PlanSaveRequest"},
         {"saved_investment_plan": "SavedInvestmentPlan", "saved_plan_confirmation": "SavedPlanConfirmation"},
         ["CS6.1.4.5", "1.2.7"], ["IF.6.4"],
         "Returns a tuple in output order only for succeeded, non-null content with matching plan_id and request_id. Otherwise returns None, without a successful-save confirmation."),
    ]
    contract["x-model-operations"] = []
    for fid, asset, callable_name, inputs, controls, outputs, requirements, interfaces, semantics in definitions:
        contract["x-model-operations"].append({
            "functionId": fid, "mechanismId": asset, "callable": callable_name,
            "transport": "in-process Python call", "inputs": {k: ref(v) for k, v in inputs.items()},
            "controls": {k: ref(v) for k, v in controls.items()}, "outputs": {k: ref(v) for k, v in outputs.items()},
            "requirementIds": requirements, "interfaceIds": interfaces, "semantics": semantics,
        })
    contract["x-model-flows"] = [
        {"id": "IO.6.1", "name": "Reviewed Plan Snapshot", "from": "F.6.2", "to": "F.6.3", "interfaceId": "IF.6.2", "schema": ref("ReviewedPlanSnapshot")},
        {"id": "IO.6.2", "name": "Authorized Plan Save Payload", "from": "F.6.3", "to": "F.6.4", "interfaceId": "IF.6.3", "schema": ref("AuthorizedPlanSavePayload")},
        {"id": "IO.6.3", "name": "Plan Persistence Result", "from": "F.6.4", "to": "F.6.5", "interfaceId": "IF.6.4", "schema": ref("PlanPersistenceResult")},
        {"id": "Investment Plan Explanation", "from": "F.6.1", "to": "F.6.2", "interfaceId": "IF.6.1", "schema": ref("InvestmentPlanExplanation")},
    ]
    return contract


if __name__ == "__main__":
    target = ROOT / "contracts" / "api-v1.yaml"
    target.parent.mkdir(exist_ok=True)
    target.write_text(yaml.safe_dump(build_contract(), sort_keys=False, allow_unicode=True))
    print(f"Exported {target.relative_to(ROOT)}")
