"""Specification contracts for analysis definitions (minimal, happy-path)."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from ascentra_agent.contracts.filters import FilterExpr


class SegmentSpec(BaseModel):
    segment_id: str
    name: str
    definition: FilterExpr
    intended_partition: bool = False
    notes: Optional[str] = None


class MetricSpec(BaseModel):
    type: Literal["frequency", "mean", "top2box", "bottom2box", "nps"]
    question_id: str
    params: dict[str, Any] = Field(default_factory=dict)


class DimensionSpec(BaseModel):
    kind: Literal["question", "segment"]
    id: str


class CutSpec(BaseModel):
    cut_id: str
    metric: MetricSpec
    dimensions: list[DimensionSpec] = Field(default_factory=list)
    filter: Optional[FilterExpr] = None


class AnalysisIntent(BaseModel):
    intent_id: str
    description: str
    segments_needed: list[str] = Field(default_factory=list)
    priority: int = 1


class HighLevelPlan(BaseModel):
    intents: list[AnalysisIntent]
    rationale: str
    suggested_segments: list[SegmentSpec] = Field(default_factory=list)


class UserIntent(BaseModel):
    intent_type: Literal[
        "chat",
        "high_level_plan",
        "cut_analysis",
        "segment_definition",
        "clarify",
    ]
    confidence: float = 1.0
    reasoning: str = ""


class Action(BaseModel):
    label: str
    action_type: Literal["cut_analysis", "high_level_plan", "segment_definition", "chat"]
    params: dict[str, Any] = Field(default_factory=dict)


class DisambiguationOption(BaseModel):
    option_id: str
    label: str
    action_type: Literal["cut_analysis", "high_level_plan", "segment_definition", "chat"]
    action_params: dict[str, Any] = Field(default_factory=dict)


class ClarifyRequest(BaseModel):
    question: str
    options: list[DisambiguationOption] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str
    suggested_actions: list[Action] = Field(default_factory=list)


class AgentResponse(BaseModel):
    intent: UserIntent
    success: bool
    message: Optional[str] = None
    errors: list[str] = Field(default_factory=list)
    data: Optional[Any] = None
    clarify: Optional[ClarifyRequest] = None


