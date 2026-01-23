from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ascentra_agent.contracts.filters import (
    PredicateContainsAny,
    PredicateEq,
    PredicateGt,
)
from ascentra_agent.contracts.questions import Question
from ascentra_agent.contracts.specs import (
    CutSpec,
    DimensionSpec,
    ChatResponse,
    MetricSpec,
    SegmentSpec,
    UserIntent,
)
from ascentra_agent.contracts.tool_output import ToolOutput
from ascentra_agent.engine import executor as executor_mod
from ascentra_agent.orchestrator.agent import Agent
from ascentra_agent.tools.cut_planner import CutPlanResult


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

    # Ensure the suite is runnable even before candidates fix intent typing.
    def fake_intent(ctx):
        text = (ctx.prompt or "").lower()
        if "define segment" in text or text.startswith("define segment"):
            i = UserIntent(intent_type="segment_definition", confidence=1.0, reasoning="test")
        else:
            i = UserIntent(intent_type="cut_analysis", confidence=1.0, reasoning="test")
        return ToolOutput.success(data=i, trace={})

    monkeypatch.setattr(a.intent_classifier, "run", fake_intent)

    # Artifact invariant: invalid requests must never reach execution.
    # We record calls rather than raising so the test failures are clear assertions.
    a._validation_execute_calls = 0  # type: ignore[attr-defined]

    def record_execute(self, cuts):  # noqa: ANN001
        a._validation_execute_calls += 1  # type: ignore[attr-defined]
        return executor_mod.ExecutionResult(tables=[], errors=[], segments_computed={})

    monkeypatch.setattr(executor_mod.Executor, "execute_cuts", record_execute)

    # Deterministic, safe chat response (no Azure calls).
    def fake_chat(ctx):
        return ToolOutput.success(
            data=ChatResponse(
                message="I might be misunderstanding. Can you clarify?",
                suggested_actions=[],
            )
        )

    monkeypatch.setattr(a.chat_responder, "run", fake_chat)

    return a


def _fake_cut_plan_output(text: str) -> dict:
    t = text.lower()

    # 1) Invalid ID used in cut dimension
    if "qunknown" in t or "qunknown" in t:
        return {
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

    # 2) Invalid metric (mean on single_choice)
    if "mean gender" in t:
        return {
            "ok": True,
            "cut": {
                "cut_id": "cut_invalid_metric",
                "metric": {"type": "mean", "question_id": "Q_GENDER", "params": {}},
                "dimensions": [],
                "filter": None,
            },
            "resolution_map": {},
            "ambiguity_options": [],
            "debug": {},
        }

    # 3) Unsupported metric (median) -> schema-invalid on purpose (should be handled gracefully)
    if "median" in t:
        return {
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

    # 4) Invalid ID in filter
    if "unknown = 10" in t or "q_unknown" in t:
        return {
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

    # 5) Invalid filter operation (numeric comparison on categorical question)
    if "region >" in t:
        return {
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

    # 6) Invalid filter criteria (bad option code)
    if "region = southeast" in t:
        return {
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

    # Additional: invalid operator for multi_choice (eq instead of contains_any)
    if "features" in t and "dash" in t:
        return {
            "ok": True,
            "cut": {
                "cut_id": "cut_invalid_multichoice_filter",
                "metric": {"type": "frequency", "question_id": "Q_GENDER", "params": {}},
                "dimensions": [],
                "filter": {"kind": "eq", "question_id": "Q_FEATURES_USED", "value": "DASH"},
            },
            "resolution_map": {},
            "ambiguity_options": [],
            "debug": {},
        }

    # Additional: invalid type on numeric question (Age = UK)
    if "age = uk" in t:
        return {
            "ok": True,
            "cut": {
                "cut_id": "cut_invalid_numeric_filter",
                "metric": {"type": "frequency", "question_id": "Q_GENDER", "params": {}},
                "dimensions": [],
                "filter": {"kind": "eq", "question_id": "Q_AGE", "value": "UK"},
            },
            "resolution_map": {},
            "ambiguity_options": [],
            "debug": {},
        }

    # Default: return a trivially invalid schema (missing cut) to force handling
    return {"ok": False, "ambiguity_options": ["Need more context"], "debug": {}}


def _fake_segment_output(text: str) -> SegmentSpec:
    t = text.lower()

    if "unknown = 10" in t or "q_unknown" in t:
        expr = PredicateEq(kind="eq", question_id="UNKNOWN", value=10)
    elif "region >" in t:
        expr = PredicateGt(kind="gt", question_id="Q_REGION", value=5)
    elif "region = southeast" in t:
        expr = PredicateEq(kind="eq", question_id="Q_REGION", value="SOUTHEAST")
    elif "age = uk" in t:
        expr = PredicateEq(kind="eq", question_id="Q_AGE", value="UK")
    elif "features" in t and "dash" in t:
        expr = PredicateEq(kind="eq", question_id="Q_FEATURES_USED", value="DASH")
    else:
        # Something still invalid-ish: wrong predicate type for multi-choice
        expr = PredicateContainsAny(kind="contains_any", question_id="Q_GENDER", values=["M"])

    return SegmentSpec(
        segment_id="seg_invalid",
        name="Invalid Segment",
        definition=expr,
    )


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch: pytest.MonkeyPatch):
    # Patch the structured LLM call used by CutPlanner/SegmentBuilder/ChatResponder/etc.
    from ascentra_agent.llm import structured as structured_mod

    def fake_chat_structured_pydantic(*, messages, model, model_deployment=None, temperature=None):
        user_content = messages[-1]["content"]

        # Cut planning
        if model is CutPlanResult:
            # Extract original request line from the composed prompt
            # Format is: "Request:\n{ctx.prompt}\n\nQuestions:..."
            text = user_content.split("Request:\n", 1)[-1].split("\n\nQuestions:", 1)[0].strip()
            payload = _fake_cut_plan_output(text)
            inst = model.model_validate(payload)  # may raise (e.g. unsupported metric)
            return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

        # Segment builder (returns SegmentSpec)
        if model is SegmentSpec:
            text = user_content.split("Segment request:\n", 1)[-1].split("\n\nQuestions:", 1)[0].strip()
            seg = _fake_segment_output(text)
            return seg, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

        # Other models: return a minimal failure-ish dict to keep tests deterministic
        inst = model.model_validate({"message": "stub", "suggested_actions": []})
        return inst, {"model": "fake", "temperature": 0.0, "latency_s": 0.0, "usage": {}}

    monkeypatch.setattr(structured_mod, "chat_structured_pydantic", fake_chat_structured_pydantic)


@pytest.mark.parametrize(
    "text",
    [
        # 1) Invalid ID used in cut dimension
        "Cut QUNKNOWN",
        # 2) Invalid metric(s)
        "Create a cut displaying the mean gender",
        # 3) Unsupported metrics
        "Create cut displaying the median age",
        # 4) Invalid ID used in a filter
        "Show me gender distribution where UNKNOWN = 10",
        # 5) Invalid filter operation
        "Show me gender distribution where Region > North",
        # 6) Invalid filter criteria
        "Show me gender distribution where Region = SOUTHEAST",
        # Additional invalids
        "Show me gender distribution where Age = UK",
        "Show me gender distribution where features = DASH",
    ],
)
def test_invalid_cut_requests_do_not_execute_or_create_artifacts(agent: Agent, text: str) -> None:
    before_segments = list(agent.segments)

    agent.handle_message(text)

    # No segment artifacts should be created as a side effect of invalid cut requests.
    assert agent.segments == before_segments
    assert agent.segments_by_id == {s.segment_id: s for s in before_segments}

    # No execution should occur for invalid requests.
    assert getattr(agent, "_validation_execute_calls", 0) == 0


@pytest.mark.parametrize(
    "text",
    [
        # Repeat filter validations for segments
        "Define segment where UNKNOWN = 10",
        "Define segment where Region > North",
        "Define segment where Region = SOUTHEAST",
        "Define segment where Age = UK",
        "Define segment where features = DASH",
    ],
)
def test_invalid_segment_requests_do_not_create_segment(agent: Agent, text: str) -> None:
    before_segments = list(agent.segments)

    agent.handle_message(text)

    # No segment should be created for invalid segment definitions.
    assert agent.segments == before_segments
    assert agent.segments_by_id == {s.segment_id: s for s in before_segments}
    assert getattr(agent, "_validation_execute_calls", 0) == 0


