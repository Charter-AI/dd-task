"""Question-related contracts."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Enumeration of supported question types."""

    single_choice = "single_choice"
    multi_choice = "multi_choice"
    likert_1_5 = "likert_1_5"
    likert_1_7 = "likert_1_7"
    numeric = "numeric"
    nps_0_10 = "nps_0_10"
    open_text = "open_text"


class Option(BaseModel):
    """A single option/choice for a question."""

    code: str | int = Field(..., description="Unique code for this option")
    label: str = Field(..., description="Human-readable label for this option")


class Question(BaseModel):
    """A survey question definition."""

    question_id: str = Field(..., description="Unique identifier for this question")
    label: str = Field(..., description="The question text/label")
    type: QuestionType = Field(..., description="The type of question")
    options: Optional[list[Option]] = Field(
        default=None,
        description="Available options for choice-type questions",
    )
    column_name: Optional[str] = Field(
        default=None,
        description="Column name in the responses CSV (defaults to question_id)",
    )

    @property
    def effective_column_name(self) -> str:
        """Get the column name to use in the responses DataFrame."""
        return self.column_name or self.question_id

    def get_option_codes(self) -> set[str | int]:
        """Get all valid option codes for this question."""
        if self.options is None:
            return set()
        return {opt.code for opt in self.options}

    def get_option_label(self, code: str | int) -> Optional[str]:
        """Get the label for a given option code."""
        if self.options is None:
            return None
        for opt in self.options:
            if opt.code == code:
                return opt.label
        return None
