from __future__ import annotations

import json
from pathlib import Path

import pytest

from ascentra_agent.contracts.questions import Question, QuestionType
from ascentra_agent.tools.base import ToolContext
from ascentra_agent.tools.intent_classifier import IntentClassifier


@pytest.fixture()
def question_catalog() -> list[Question]:
    # Load the real demo dataset question catalog
    repo_root = Path(__file__).resolve().parent.parent
    questions_path = repo_root / "data" / "demo" / "questions.json"
    raw = json.loads(questions_path.read_text())

    if isinstance(raw, list):
        return [Question.model_validate(q) for q in raw]
    if isinstance(raw, dict) and "questions" in raw:
        return [Question.model_validate(q) for q in raw["questions"]]

    raise ValueError("Invalid questions.json format")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Conversational
        ("hello", "chat"),
        ("help", "chat"),
        ("what can you do?", "chat"),
        ("thanks, that helps", "chat"),
        ("how does this work?", "chat"),
        ("what is a segment?", "chat"),   # mention of 'segment' shouldn't force segment_definition
        ("my plan is to explore results later", "chat"),  # 'plan' used conversationally
        ("we have a pricing plan problem", "chat"),       # 'plan' in general text
        # High level plan
        ("create an analysis plan", "high_level_plan"),
        ("plan the analysis", "high_level_plan"),
        ("what should we analyze?", "high_level_plan"),
        ("suggest a plan for this survey", "high_level_plan"),
        ("give me a roadmap of analyses", "high_level_plan"),
        # Segment definition (explicit creation)
        ("define a segment for promoters", "segment_definition"),
        ("create segment: users aged 18-24", "segment_definition"),
        ("build a cohort for users in region North", "segment_definition"),
        ("create an audience of detractors (0-6)", "segment_definition"),
        ("filter to customers aged 30-40", "segment_definition"),
        ("users who are 9-10 on Q_NPS", "segment_definition"),
        # Cut analysis (metric questions)
        ("show me nps by region", "cut_analysis"),
        ("analyze Q_NPS by Q_REGION", "cut_analysis"),
        ("break down Net Promoter Score by Region", "cut_analysis"),  # label-based
        ("what is the distribution of Overall Satisfaction?", "cut_analysis"),
        ("average satisfaction by age", "cut_analysis"),
        ("frequency of Q_REGION", "cut_analysis"),
        ("show Q_PLAN", "cut_analysis"),  # question id/label references should bias toward cut
        # Multi-intent messages (choose a consistent primary intent)
        ("define promoters as 9-10 and show nps by region", "cut_analysis"),
        ("create a segment for promoters and analyze Q_SAT", "cut_analysis"),
    ],
)
def test_intent_classifier_enhanced(text: str, expected: str, question_catalog: list[Question]) -> None:
    tool = IntentClassifier()
    ctx = ToolContext(questions=question_catalog, prompt=text)
    out = tool.run(ctx)
    assert out.ok is True
    assert out.data is not None
    assert out.data.intent_type == expected