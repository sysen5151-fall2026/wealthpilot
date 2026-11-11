"""F.6.1 with a language model: the SPEC.md Model Response Contract (CS6.1.4.1, CS6.1.1.1).

A response is used only if it meets every constraint of the contract;
anything else falls back to the deterministic template. LM Studio itself is
replaced by a small local HTTP server, so no model has to be installed.
"""

import json
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from test_functional_requirements import RULES, make_recommendations

from investment_plan_management import (
    LanguageModelError,
    LmStudioModel,
    explain_investment_plan,
    language_model_from_environment,
)
from investment_plan_management.explanation_engine import contract_input


def good_response(plan) -> dict:
    return {
        "summary": "This practice plan puts 60% in US Stocks and 40% in Bonds for a Moderate investor.",
        "allocation_rationale": [
            "Your risk score of 55 places you in the Moderate category.",
            "AAPL and MSFT each make up 30% of the plan, and BND makes up 40%.",
        ],
        "material_risks": ["Stock prices can fall sharply, so the plan can lose value."],
        "data_limitations": list(plan.data_limitations),
        "scope_notice": RULES.scope_notice,
    }


class FakeModel:
    name = "fake-model"

    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    def complete_json(self, system, user, schema):
        self.calls.append((system, json.loads(user), schema))
        if self.error:
            raise self.error
        return self.response


def test_CS6_1_4_1_model_response_that_meets_the_contract_is_used():
    plan = make_recommendations()
    model = FakeModel(good_response(plan))

    explanation = explain_investment_plan(plan, explanation_rules=RULES, language_model=model)

    assert explanation.generated_by == "language model fake-model"
    assert explanation.summary == good_response(plan)["summary"]
    assert explanation.data_limitations == plan.data_limitations
    assert explanation.scope_notice == RULES.scope_notice
    _, facts, schema = model.calls[0]
    assert facts["risk_score"] == 55 and facts["identified_risks"] == plan.identified_risks
    assert set(schema["required"]) == {"summary", "allocation_rationale", "material_risks", "data_limitations", "scope_notice"}


def broken(field, value):
    def make(plan):
        response = good_response(plan)
        if value is KeyError:
            del response[field]
        else:
            response[field] = value(plan) if callable(value) else value
        return response
    return make


@pytest.mark.parametrize(
    "make_response",
    [
        broken("summary", KeyError),
        broken("summary", "   "),
        broken("material_risks", []),
        broken("allocation_rationale", "not a list"),
        broken("data_limitations", []),
        broken("scope_notice", "Just a plan."),
        broken("summary", "This plan is guaranteed to grow."),
        broken("summary", "Your risk score is 80, so the plan puts 60% in US Stocks."),
        broken("allocation_rationale", ["Put $5,000 into AAPL."]),
        lambda plan: ["not", "an", "object"],
    ],
    ids=[
        "missing-summary", "empty-summary", "no-risk", "rationale-not-list", "dropped-limitation",
        "wrong-scope-notice", "prohibited-phrase", "contradicts-score", "invented-amount", "not-an-object",
    ],
)
def test_CS6_1_4_1_response_that_breaks_the_contract_falls_back_to_the_template(make_response):
    plan = make_recommendations()
    template = explain_investment_plan(plan, explanation_rules=RULES)

    explanation = explain_investment_plan(plan, explanation_rules=RULES, language_model=FakeModel(make_response(plan)))

    assert explanation.generated_by == "template"
    assert explanation.generation_note.startswith("The language model's response was rejected")
    assert replace(explanation, generation_note="") == template


def test_CS6_1_4_1_unreachable_model_falls_back_to_the_template():
    plan = make_recommendations()
    model = FakeModel(error=LanguageModelError("connection refused"))

    explanation = explain_investment_plan(plan, explanation_rules=RULES, language_model=model)

    assert explanation.generated_by == "template"
    assert "connection refused" in explanation.generation_note


def test_CS6_1_1_1_facts_given_to_the_model_follow_the_spec_input_schema():
    plan = make_recommendations()
    template = explain_investment_plan(plan, explanation_rules=RULES)
    facts = contract_input(plan, RULES, template)

    for key in ("risk_score", "risk_level", "planning_inputs", "target_allocation", "candidate_securities",
                "identified_risks", "data_limitations"):
        assert key in facts
    assert facts["target_allocation"] == [{"asset_class": "US Stocks", "weight": 0.6}, {"asset_class": "Bonds", "weight": 0.4}]


# LM Studio's OpenAI-compatible endpoint, served locally

class FakeLmStudio(BaseHTTPRequestHandler):
    replies: list = []
    requests: list = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).requests.append((self.path, body))
        status, payload = type(self).replies.pop(0)
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def lm_studio():
    FakeLmStudio.replies, FakeLmStudio.requests = [], []
    server = HTTPServer(("127.0.0.1", 0), FakeLmStudio)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()
    server.server_close()


def chat_reply(content: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


def test_lm_studio_reply_is_parsed_including_a_code_fence(lm_studio):
    FakeLmStudio.replies = [(200, chat_reply('```json\n{"summary": "ok"}\n```'))]
    model = LmStudioModel("qwen-test", base_url=lm_studio, timeout=5)

    assert model.complete_json("system", "user", {"type": "object"}) == {"summary": "ok"}
    path, body = FakeLmStudio.requests[0]
    assert path == "/v1/chat/completions"
    assert body["model"] == "qwen-test"
    assert body["response_format"]["type"] == "json_schema"


def test_lm_studio_without_structured_output_is_asked_again_without_it(lm_studio):
    FakeLmStudio.replies = [(400, {"error": "response_format not supported"}), (200, chat_reply('{"summary": "ok"}'))]
    model = LmStudioModel("qwen-test", base_url=lm_studio, timeout=5)

    assert model.complete_json("system", "user", {"type": "object"}) == {"summary": "ok"}
    assert "response_format" not in FakeLmStudio.requests[1][1]


@pytest.mark.parametrize(
    "reply",
    [(500, {"error": "boom"}), (200, {"unexpected": True}), (200, chat_reply("no json here"))],
    ids=["server-error", "no-choices", "not-json"],
)
def test_lm_studio_failures_raise_language_model_error(lm_studio, reply):
    FakeLmStudio.replies = [reply]
    with pytest.raises(LanguageModelError):
        LmStudioModel("qwen-test", base_url=lm_studio, timeout=5).complete_json("s", "u", {})


def test_lm_studio_not_running_raises_language_model_error():
    with pytest.raises(LanguageModelError):
        LmStudioModel("qwen-test", base_url="http://127.0.0.1:9/v1", timeout=2).complete_json("s", "u", {})


def test_language_model_is_used_only_when_configured():
    assert language_model_from_environment({}) is None
    model = language_model_from_environment({"WEALTHPILOT_LLM_MODEL": "qwen-test", "WEALTHPILOT_LLM_TIMEOUT": "12"})
    assert model.model == "qwen-test" and model.timeout == 12.0
    assert model.base_url == "http://localhost:1234/v1"
