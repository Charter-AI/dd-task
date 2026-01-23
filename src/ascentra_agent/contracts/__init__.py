"""Contracts package - Pydantic models for the Ascentra agent."""

from ascentra_agent.contracts.questions import Option, Question, QuestionType
from ascentra_agent.contracts.filters import (
    And,
    FilterExpr,
    Not,
    Or,
    Predicate,
    PredicateContainsAny,
    PredicateEq,
    PredicateGt,
    PredicateGte,
    PredicateIn,
    PredicateLt,
    PredicateLte,
    PredicateRange,
)
from ascentra_agent.contracts.specs import (
    Action,
    AgentResponse,
    AnalysisIntent,
    ChatResponse,
    CutSpec,
    DimensionSpec,
    HighLevelPlan,
    MetricSpec,
    SegmentSpec,
    UserIntent,
)
from ascentra_agent.contracts.tool_output import ToolMessage, ToolOutput

__all__ = [
    # Questions
    "Option",
    "Question",
    "QuestionType",
    # Filters
    "And",
    "FilterExpr",
    "Not",
    "Or",
    "Predicate",
    "PredicateContainsAny",
    "PredicateEq",
    "PredicateGt",
    "PredicateGte",
    "PredicateIn",
    "PredicateLt",
    "PredicateLte",
    "PredicateRange",
    # Specs
    "Action",
    "AgentResponse",
    "AnalysisIntent",
    "ChatResponse",
    "CutSpec",
    "DimensionSpec",
    "HighLevelPlan",
    "MetricSpec",
    "SegmentSpec",
    "UserIntent",
    # Tool Output
    "ToolMessage",
    "ToolOutput",
]
