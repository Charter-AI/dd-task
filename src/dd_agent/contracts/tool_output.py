"""Tool output envelope and message types."""

from typing import Generic, TypeVar, Optional, List, Dict, Any

from pydantic import BaseModel, Field

T = TypeVar("T")


class ToolMessage(BaseModel):
    """A message (error or warning) from a tool."""

    code: str = Field(..., description="Machine-readable error/warning code")
    message: str = Field(..., description="Human-readable message")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for debugging",
    )


class ToolOutput(BaseModel, Generic[T]):
    """Standard output envelope for all tools.

    This provides a consistent interface for tool results, making it easy
    to handle success/failure cases and trace execution.
    """

    ok: bool = Field(..., description="Whether the tool execution was successful")
    data: Optional[T] = Field(
        default=None, description="The result data (if successful)"
    )
    errors: list[ToolMessage] = Field(
        default_factory=list, description="List of errors (if any)"
    )
    warnings: list[ToolMessage] = Field(
        default_factory=list, description="List of warnings (if any)"
    )
    trace: dict[str, Any] = Field(
        default_factory=dict,
        description="Trace information (prompts, model, latency, mappings, etc.)",
    )

    # add for interactions
    requires_user_input: bool = Field(default=False, description="Whether tool requires user input to proceed")
    user_input_options: List[Dict[str, Any]] = Field(default_factory=list, description="Options for user to choose from")
    user_input_prompt: str = Field(default="", description="Prompt to show user when input is needed")

    @classmethod
    def partial_for_user_input(
        cls,
        prompt: str,
        options: List[Dict[str, Any]],
        trace: Optional[Dict[str, Any]] = None
    ) -> "ToolOutput[T]":
        """Create a partial result that requires user input."""
        return cls(
            ok=False,
            data=None,
            requires_user_input=True,
            user_input_prompt=prompt,
            user_input_options=options,
            trace=trace or {}
        )


    @classmethod
    def success(
        cls,
        data: T,
        warnings: Optional[list[ToolMessage]] = None,
        trace: Optional[dict[str, Any]] = None,
    ) -> "ToolOutput[T]":
        """Create a successful tool output."""
        return cls(
            ok=True,
            data=data,
            warnings=warnings or [],
            trace=trace or {},
        )

    @classmethod
    def failure(
        cls,
        errors: list[ToolMessage],
        warnings: Optional[list[ToolMessage]] = None,
        trace: Optional[dict[str, Any]] = None,
    ) -> "ToolOutput[T]":
        """Create a failed tool output."""
        return cls(
            ok=False,
            data=None,
            errors=errors,
            warnings=warnings or [],
            trace=trace or {},
        )


def err(code: str, message: str, **context: Any) -> ToolMessage:
    """Helper to create an error message."""
    return ToolMessage(code=code, message=message, context=context)


def warn(code: str, message: str, **context: Any) -> ToolMessage:
    """Helper to create a warning message."""
    return ToolMessage(code=code, message=message, context=context)
