from __future__ import annotations

from typing import Optional

from ascentra_agent.contracts.filters import PredicateRange
from ascentra_agent.contracts.questions import Question
from ascentra_agent.contracts.specs import (
    AnalysisIntent,
    CutSpec,
    DimensionSpec,
    HighLevelPlan,
    MetricSpec,
    SegmentSpec,
)


def first_question_id(questions: list[Question]) -> str:
    if not questions:
        raise ValueError("No questions loaded")
    return questions[0].question_id


def build_stub_segment(questions: list[Question]) -> SegmentSpec:
    qid = first_question_id(questions)
    return SegmentSpec(
        segment_id="stub_segment",
        name="Stub Segment",
        definition=PredicateRange(
            kind="range", question_id=qid, min=0, max=10, inclusive=True
        ),
    )


def build_stub_cut(
    questions: list[Question],
    segment_id: Optional[str] = None,
) -> CutSpec:
    qid = first_question_id(questions)

    dims: list[DimensionSpec] = []
    if segment_id:
        dims.append(DimensionSpec(kind="segment", id=segment_id))

    return CutSpec(
        cut_id="cut_stub_001",
        metric=MetricSpec(type="frequency", question_id=qid, params={}),
        dimensions=dims,
        filter=None,
    )


def build_stub_plan() -> HighLevelPlan:
    return HighLevelPlan(
        rationale="Stub rationale",
        intents=[
            AnalysisIntent(
                intent_id="intent_001",
                description="Stub analysis",
                segments_needed=[],
                priority=1,
            )
        ],
        suggested_segments=[],
    )


