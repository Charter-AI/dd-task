from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from ascentra_agent.contracts.questions import Question
from ascentra_agent.contracts.specs import ChatResponse, SegmentSpec, UserIntent
from ascentra_agent.contracts.tool_output import ToolOutput
from ascentra_agent.engine import executor as executor_mod
from ascentra_agent.orchestrator.agent import Agent
from ascentra_agent.tools.cut_planner import CutPlanResult


LEAK_PATTERNS = [
    r"Traceback \(most recent call last\):",
    r"\b(ValueError|KeyError|TypeError|AssertionError|Pydantic|ValidationError)\b",
    r'File ".*", line \d+',
    r"\bToolOutput\b",
    r"\berrors=\[",
]


def assert_no_leak(msg: str) -> None:
    for pat in LEAK_PATTERNS:
        assert (
            re.search(pat, msg) is None
        ), f"Leaked internal error pattern: {pat}\nMSG:\n{msg}"


def looks_helpful(msg: str) -> bool:
    m = msg.lower()
    return ("?" in msg) or ("try" in m) or ("rephrase" in m) or ("did you mean" in m) or ("you can" in m)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def demo_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "demo"


@pytest.fixture(scope="session")
def demo_questions(demo_dir: Path) -> list[Question]:
    raw = json.loads((demo_dir / "questions.json").read_text())
    return [Question.model_validate(q) for q in raw]


@pytest.fixture()
def agent(monkeypatch: pytest.MonkeyPatch, demo_dir: Path, demo_questions: list[Question]) -> Agent:
    df = pd.read_csv(demo_dir / "responses.csv")
    a = Agent(questions=demo_questions, responses_df=df, scope=None)

    # Deterministic intent routing (avoid current DD/Ascentra type mismatch issues).
    def fake_intent(ctx):
        text = (ctx.prompt or "").lower()
        if "segment" in text and ("define" in text or "create" in text):
            i = UserIntent(intent_type="segment_definition", confidence=1.0, reasoning="test")
        elif "plan" in text:
            i = UserIntent(intent_type="high_level_plan", confidence=1.0, reasoning="test")
        elif "cut" in text or "show" in text or "analy" in text:
            i = UserIntent(intent_type="cut_analysis", confidence=1.0, reasoning="test")
        else:
            i = UserIntent(intent_type="chat", confidence=1.0, reasoning="test")
        return ToolOutput.success(data=i, trace={})

    monkeypatch.setattr(a.intent_classifier, "run", fake_intent)

    # Record execution calls (the UX suite asserts "no crash/no leak"; artifact checks live elsewhere,
    # but we still track execution to keep this suite informative).
    a._ux_execute_calls = 0  # type: ignore[attr-defined]

    def record_execute(self, cuts):  # noqa: ANN001
        a._ux_execute_calls += 1  # type: ignore[attr-defined]
        return executor_mod.ExecutionResult(tables=[], errors=[], segments_computed={})

    monkeypatch.setattr(executor_mod.Executor, "execute_cuts", record_execute)

    return a


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch: pytest.MonkeyPatch):
    # Patch the structured LLM call used by all tools so tests are deterministic (no Azure).
    from ascentra_agent.llm import structured as structured_mod

    def fake_chat_structured_pydantic(*, messages, model, model_deployment=None, temperature=None):
        user_content = messages[-1]["content"]

        # Chat responder always returns a safe, helpful message.
        if model is ChatResponse:
            inst = ChatResponse(
                message="Sorry, I couldn’t run that as written. Could you clarify which question and filter you meant?",
                suggested_actions=[],
            )
            return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

        # Segment builder returns an invalid segment (unknown question id) for any prompt,
        # to force downstream validation/handling.
        if model is SegmentSpec:
            inst = SegmentSpec.model_validate(
                {
                    "segment_id": "seg_invalid",
                    "name": "Invalid Segment",
                    "definition": {"kind": "eq", "question_id": "UNKNOWN", "value": 10},
                    "intended_partition": False,
                    "notes": None,
                }
            )
            return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

        # Cut planner returns various invalids depending on the user request.
        if model is CutPlanResult:
            text = user_content.split("Request:\n", 1)[-1].split("\n\nQuestions:", 1)[0].strip().lower()

            # Unsupported metric: median
            if "median" in text:
                payload = {
                    "ok": True,
                    "cut": {
                        "cut_id": "cut_unsupported_metric",
                        "metric": {"type": "median", "question_id": "Q_AGE", "params": {}},
                        "dimensions": [],
                        "filter": None,
                    },
                    "resolution_map": {},
                    "ambiguity_options": [],
                    "debug": {},
                }
                # This should raise at model validation time, exercising error handling.
                inst = model.model_validate(payload)
                return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

            # Invalid dimension id
            if "qunknown" in text or "qunknown" in text:
                payload = {
                    "ok": True,
                    "cut": {
                        "cut_id": "cut_invalid_dim",
                        "metric": {"type": "frequency", "question_id": "Q_GENDER", "params": {}},
                        "dimensions": [{"kind": "question", "id": "QUNKNOWN"}],
                        "filter": None,
                    },
                    "resolution_map": {},
                    "ambiguity_options": [],
                    "debug": {},
                }
                inst = model.model_validate(payload)
                return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

            # Invalid filter id
            if "unknown = 10" in text:
                payload = {
                    "ok": True,
                    "cut": {
                        "cut_id": "cut_invalid_filter_id",
                        "metric": {"type": "frequency", "question_id": "Q_GENDER", "params": {}},
                        "dimensions": [],
                        "filter": {"kind": "eq", "question_id": "UNKNOWN", "value": 10},
                    },
                    "resolution_map": {},
                    "ambiguity_options": [],
                    "debug": {},
                }
                inst = model.model_validate(payload)
                return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

            # Invalid filter op: region > north
            if "region >" in text:
                payload = {
                    "ok": True,
                    "cut": {
                        "cut_id": "cut_invalid_filter_op",
                        "metric": {"type": "frequency", "question_id": "Q_GENDER", "params": {}},
                        "dimensions": [],
                        "filter": {"kind": "gt", "question_id": "Q_REGION", "value": 5},
                    },
                    "resolution_map": {},
                    "ambiguity_options": [],
                    "debug": {},
                }
                inst = model.model_validate(payload)
                return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

            # Invalid criteria: bad region code
            if "region = southeast" in text:
                payload = {
                    "ok": True,
                    "cut": {
                        "cut_id": "cut_invalid_filter_value",
                        "metric": {"type": "frequency", "question_id": "Q_GENDER", "params": {}},
                        "dimensions": [],
                        "filter": {"kind": "eq", "question_id": "Q_REGION", "value": "SOUTHEAST"},
                    },
                    "resolution_map": {},
                    "ambiguity_options": [],
                    "debug": {},
                }
                inst = model.model_validate(payload)
                return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

            # Default: "ok": False with missing cut (forces tool to handle planner returning ok=false)
            payload = {"ok": False, "ambiguity_options": ["Need more context"], "debug": {}}
            inst = model.model_validate(payload)
            return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

        # Generic fallback for any other models
        inst = model.model_validate({"message": "stub", "suggested_actions": []})
        return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

    monkeypatch.setattr(structured_mod, "chat_structured_pydantic", fake_chat_structured_pydantic)


INVALID_REQUESTS = [
    # Invalid ID used in cut dimension
    "Cut QUNKNOWN",
    # Invalid metric(s)
    "Create a cut displaying the mean gender",
    # Unsupported metrics (schema-level failure)
    "Create cut displaying the median age",
    # Invalid ID used in filter
    "Show me gender distribution where UNKNOWN = 10",
    # Invalid filter operation
    "Show me gender distribution where Region > North",
    # Invalid filter criteria
    "Show me gender distribution where Region = SOUTHEAST",
    # Segment invalids (same patterns)
    "Define segment where UNKNOWN = 10",
    "Define segment where Region > North",
    "Define segment where Region = SOUTHEAST",
]


@pytest.mark.parametrize("text", INVALID_REQUESTS)
def test_invalid_requests_are_graceful(agent: Agent, text: str) -> None:
    # Core UX safety invariant: must not crash and must return a user-facing message.
    resp = agent.handle_message(text)

    assert isinstance(resp.message, str) and resp.message.strip() != ""
    assert_no_leak(resp.message)
