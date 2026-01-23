from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ascentra_agent.contracts.questions import Question
from ascentra_agent.contracts.specs import ChatResponse
from ascentra_agent.contracts.tool_output import ToolOutput
from ascentra_agent.orchestrator.agent import Agent
from ascentra_validation.stubs import build_stub_cut, build_stub_plan, build_stub_segment


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def demo_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "demo"


@pytest.fixture(scope="session")
def questions(demo_dir: Path) -> list[Question]:
    raw = json.loads((demo_dir / "questions.json").read_text())
    if isinstance(raw, list):
        return [Question.model_validate(q) for q in raw]
    if isinstance(raw, dict) and "questions" in raw:
        return [Question.model_validate(q) for q in raw["questions"]]
    raise ValueError("Invalid questions.json format")


@pytest.fixture(scope="session")
def responses_df(demo_dir: Path) -> pd.DataFrame:
    return pd.read_csv(demo_dir / "responses.csv")


@pytest.fixture()
def agent(monkeypatch: pytest.MonkeyPatch, questions: list[Question], responses_df: pd.DataFrame) -> Agent:
    a = Agent(questions=questions, responses_df=responses_df, scope=None)

    def stub_chat_run(ctx):
        return ToolOutput.success(
            data=ChatResponse(message="stub chat", suggested_actions=[])
        )

    def stub_plan_run(ctx):
        return ToolOutput.success(data=build_stub_plan())

    def stub_segment_run(ctx):
        return ToolOutput.success(data=build_stub_segment(questions))

    def stub_cut_run(ctx):
        # Keep intent classifier tests orthogonal: don't require the user prompt to
        # contain the word "segment" to include a segment dimension.
        seg_id = None
        if a.segments:
            seg_id = a.segments[0].segment_id
        return ToolOutput.success(data=build_stub_cut(questions, segment_id=seg_id))

    monkeypatch.setattr(a.chat_responder, "run", stub_chat_run)
    monkeypatch.setattr(a.high_level_planner, "run", stub_plan_run)
    monkeypatch.setattr(a.segment_builder, "run", stub_segment_run)
    monkeypatch.setattr(a.cut_planner, "run", stub_cut_run)

    return a


