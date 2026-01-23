from __future__ import annotations

import pytest

from ascentra_agent.contracts.questions import Question, QuestionType
from ascentra_agent.contracts.specs import ChatResponse
from ascentra_agent.contracts.tool_output import ToolOutput
from ascentra_agent.engine import executor as executor_mod
from ascentra_agent.orchestrator.agent import Agent


def looks_like_clarification(msg: str) -> bool:
    m = msg.lower()
    return ("?" in msg) or ("which" in m) or ("did you mean" in m) or ("clarif" in m)


@pytest.fixture()
def ambiguous_questions() -> list[Question]:
    # Crafted to create intent collisions:
    # - Q_PLAN collides with "plan"
    # - multiple satisfaction questions collide with "satisfaction"
    return [
        Question(question_id="Q_PLAN", label="Subscription Plan", type=QuestionType.single_choice),
        Question(
            question_id="Q_OVERALL_SAT",
            label="Overall Satisfaction",
            type=QuestionType.likert_1_5,
        ),
        Question(
            question_id="Q_SUPPORT_SAT",
            label="Support Satisfaction",
            type=QuestionType.likert_1_5,
        ),
        Question(question_id="Q_REGION", label="Region", type=QuestionType.single_choice),
        Question(question_id="Q_NPS", label="Net Promoter Score", type=QuestionType.nps_0_10),
    ]


@pytest.fixture()
def ambiguous_agent(monkeypatch: pytest.MonkeyPatch, ambiguous_questions: list[Question]) -> Agent:
    # Minimal DF is fine because we are asserting "no execution happens".
    import pandas as pd

    df = pd.DataFrame(
        {
            "Q_PLAN": [],
            "Q_OVERALL_SAT": [],
            "Q_SUPPORT_SAT": [],
            "Q_REGION": [],
            "Q_NPS": [],
        }
    )
    agent = Agent(questions=ambiguous_questions, responses_df=df, scope=None)

    # If the agent routes ambiguously and tries to create artifacts, fail fast.
    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Tool was called for an ambiguous/underspecified request, but should not have been"
        )

    monkeypatch.setattr(agent.high_level_planner, "run", forbidden)
    monkeypatch.setattr(agent.cut_planner, "run", forbidden)
    monkeypatch.setattr(agent.segment_builder, "run", forbidden)

    # Also prevent execution at the engine layer.
    monkeypatch.setattr(executor_mod.Executor, "execute_cuts", forbidden)

    # Allow chat responder to run, but keep it deterministic.
    def stub_chat(ctx):
        return ToolOutput.success(
            data=ChatResponse(
                message="Can you clarify what you mean?",
                suggested_actions=[],
            )
        )

    monkeypatch.setattr(agent.chat_responder, "run", stub_chat)

    return agent


@pytest.mark.parametrize(
    "text",
    [
        # Ambiguous between "analysis plan" and question Q_PLAN
        "Analyse Plan",
        "plan",
        # Underspecified cut request (no metric/question)
        "Create a cut",
        "Run a cut",
        "Do an analysis",
        # Ambiguous target question (multiple satisfaction questions exist)
        "Create a cut about satisfaction",
        "analyze satisfaction",
        # Underspecified breakdown (dimension without metric)
        "by region",
        "break down by region",
    ],
)
def test_ambiguous_requests_do_not_create_artifacts_or_execute(
    ambiguous_agent: Agent, text: str
) -> None:
    resp = ambiguous_agent.handle_message(text)

    # The core invariant: no artifacts created.
    assert ambiguous_agent.segments == []
    assert ambiguous_agent.segments_by_id == {}

    # UX invariant: agent should ask for clarification, not guess.
    assert resp.success is True
    assert resp.message is not None
    assert looks_like_clarification(resp.message)

    # Safety invariant: do not leak internals.
    assert "traceback" not in resp.message.lower()
    assert "exception" not in resp.message.lower()


