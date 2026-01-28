from __future__ import annotations
"""Domain validation helpers (kept minimal for MVP).

Note: The Ascentra MVP intentionally avoids strict domain validation and
assumes happy-path inputs.
"""

from typing import Optional

from ascentra_agent.contracts.questions import QuestionType
from ascentra_agent.contracts.tool_output import ToolMessage, err


# ============================================================================
# Metric/Question Type Compatibility
# ============================================================================

# Define which metrics are compatible with which question types
METRIC_TYPE_COMPATIBILITY: dict[str, set[QuestionType]] = {
    "frequency": {
        QuestionType.single_choice,
        QuestionType.multi_choice,
        QuestionType.likert_1_5,
        QuestionType.likert_1_7,
        QuestionType.nps_0_10,
        QuestionType.numeric,
    },
    "mean": {
        QuestionType.likert_1_5,
        QuestionType.likert_1_7,
        QuestionType.numeric,
        QuestionType.nps_0_10,
    },
    "top2box": {
        QuestionType.likert_1_5,
        QuestionType.likert_1_7,
    },
    "bottom2box": {
        QuestionType.likert_1_5,
        QuestionType.likert_1_7,
    },
    "nps": {
        QuestionType.nps_0_10,
    },
}


def check_metric_compatibility(
    metric_type: str, question_type: QuestionType
) -> Optional[ToolMessage]:
    """Check if a metric type is compatible with a question type."""
    compatible_types = METRIC_TYPE_COMPATIBILITY.get(metric_type)
    if compatible_types is None:
        return err(
            "unknown_metric_type",
            f"Unknown metric type: {metric_type}",
            metric_type=metric_type,
        )
    if question_type not in compatible_types:
        return err(
            "metric_incompatible",
            f"Metric '{metric_type}' is not compatible with question type '{question_type.value}'",
            metric_type=metric_type,
            question_type=question_type.value,
            compatible_types=[t.value for t in compatible_types],
        )
    return None
