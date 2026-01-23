"""Base classes for tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, TypeVar

import pandas as pd

from ascentra_agent.contracts.questions import Question
from ascentra_agent.contracts.specs import SegmentSpec
from ascentra_agent.contracts.tool_output import ToolOutput

T = TypeVar("T")


@dataclass
class ToolContext:
    """Context passed to tools for execution.

    Contains all the information tools need to operate:
    - Question catalog
    - Segment definitions
    - Optional scope/prompt
    - Responses DataFrame (when needed)
    """

    questions: list[Question]
    questions_by_id: dict[str, Question] = field(default_factory=dict)
    segments: list[SegmentSpec] = field(default_factory=list)
    segments_by_id: dict[str, SegmentSpec] = field(default_factory=dict)
    scope: Optional[str] = None
    prompt: Optional[str] = None
    responses_df: Optional[pd.DataFrame] = None
    data_dir: Optional[Path] = None

    def __post_init__(self):
        """Build lookup dictionaries if not provided."""
        if not self.questions_by_id:
            self.questions_by_id = {q.question_id: q for q in self.questions}
        if not self.segments_by_id:
            self.segments_by_id = {s.segment_id: s for s in self.segments}

    def with_prompt(self, prompt: str) -> ToolContext:
        """Create a new context with an updated prompt."""
        return ToolContext(
            questions=self.questions,
            questions_by_id=self.questions_by_id,
            segments=self.segments,
            segments_by_id=self.segments_by_id,
            scope=self.scope,
            prompt=prompt,
            responses_df=self.responses_df,
            data_dir=self.data_dir,
        )

    def with_segments(self, segments: list[SegmentSpec]) -> ToolContext:
        """Create a new context with updated segments."""
        return ToolContext(
            questions=self.questions,
            questions_by_id=self.questions_by_id,
            segments=segments,
            segments_by_id={s.segment_id: s for s in segments},
            scope=self.scope,
            prompt=self.prompt,
            responses_df=self.responses_df,
            data_dir=self.data_dir,
        )

    def get_questions_summary(self) -> str:
        """Get a summary of available questions for prompts."""
        lines = []
        for q in self.questions:
            options_str = ""
            if q.options:
                opts = [f"{o.code}: {o.label}" for o in q.options[:5]]
                if len(q.options) > 5:
                    opts.append(f"... ({len(q.options) - 5} more)")
                options_str = f" | Options: [{', '.join(opts)}]"
            lines.append(f"- {q.question_id} ({q.type.value}): {q.label}{options_str}")
        return "\n".join(lines)

    def get_segments_summary(self) -> str:
        """Get a summary of available segments for prompts."""
        if not self.segments:
            return "No segments defined."
        lines = [f"- {s.segment_id}: {s.name}" for s in self.segments]
        return "\n".join(lines)


class Tool(ABC):
    """Abstract base class for all tools.

    Tools are the primary interface for LLM-powered operations. Each tool:
    1. Receives a ToolContext
    2. Constructs appropriate prompts
    3. Calls the LLM with structured output
    4. Validates the result
    5. Returns a ToolOutput envelope
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of this tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what this tool does."""
        pass

    @abstractmethod
    def run(self, ctx: ToolContext) -> ToolOutput[Any]:
        """Execute the tool with the given context.

        Args:
            ctx: The tool context with questions, scope, etc.

        Returns:
            ToolOutput with the result or errors
        """
        pass

    def _load_prompt(self, filename: str) -> str:
        """Load a prompt template from the prompts directory."""
        prompt_dir = Path(__file__).parent.parent / "llm" / "prompts"
        prompt_path = prompt_dir / filename
        return prompt_path.read_text()
