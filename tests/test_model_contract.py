"""Check the recorded F.6 contracts against actual call signatures and data."""

import importlib
import inspect
from dataclasses import asdict
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

from scripts.export_api_contract import build_contract
from test_functional_requirements import RULES, authorize, explain_and_present
from investment_plan_management import SqlitePlanStore, persist_reviewed_investment_plan, confirm_successful_plan_save

ROOT = Path(__file__).resolve().parents[1]


def contract():
    return yaml.safe_load((ROOT / "contracts/api-v1.yaml").read_text())


def test_recorded_contract_matches_implemented_api_and_dataclasses():
    assert contract() == build_contract(), "Regenerate contracts/api-v1.yaml after an API or flow-type change"


def test_f6_icom_names_are_real_function_parameters():
    for operation in contract()["x-model-operations"]:
        module, name = operation["callable"].rsplit(".", 1)
        function = getattr(importlib.import_module(module), name)
        assert operation["functionId"] in inspect.getmodule(function).__doc__
        assert set(operation["inputs"]) | set(operation["controls"]) <= set(inspect.signature(function).parameters)


def test_internal_flow_payloads_match_published_schemas(tmp_path):
    spec = contract()
    validator = Draft202012Validator(spec)
    plan, explanation, presented, snapshot = explain_and_present()
    request, authorized = authorize(snapshot)
    result = persist_reviewed_investment_plan(authorized, plan_save_request=request, plan_store=SqlitePlanStore(tmp_path / "contract.db"))
    saved, confirmation = confirm_successful_plan_save(result, plan_save_request=request)
    for value in (plan, RULES, explanation, presented, snapshot, request, authorized, result, saved, confirmation):
        schema = {"$ref": f"#/components/schemas/{type(value).__name__}"}
        validator.evolve(schema={**spec, **schema}).validate(asdict(value))

    invalid = asdict(snapshot)
    invalid.pop("plan_id")
    with pytest.raises(ValidationError):
        validator.evolve(schema={**spec, "$ref": "#/components/schemas/ReviewedPlanSnapshot"}).validate(invalid)


def test_each_model_internal_flow_has_source_and_receiver_operations():
    spec = contract()
    operations = {op["functionId"]: op for op in spec["x-model-operations"]}
    for flow in spec["x-model-flows"]:
        assert flow["schema"] in operations[flow["from"]]["outputs"].values()
        assert flow["schema"] in operations[flow["to"]]["inputs"].values()
