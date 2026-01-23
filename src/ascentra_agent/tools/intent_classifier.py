"""Intent classification tool for routing user input."""

from ascentra_agent.contracts.specs import UserIntent
from ascentra_agent.contracts.tool_output import ToolOutput, err
from ascentra_agent.llm.structured import build_messages, chat_structured_pydantic
from ascentra_agent.tools.base import Tool, ToolContext


class IntentClassifier(Tool):
    """Tool for classifying user intent from natural language input.

    Determines whether the user wants to:
    - Have a general chat (greetings, questions about capabilities)
    - Generate a high-level analysis plan
    - Execute a specific cut/analysis
    - Define a segment
    - Needs clarification (ambiguous input)
    """

    @property
    def name(self) -> str:
        return "intent_classifier"

    @property
    def description(self) -> str:
        return "Classifies user input into intent types for routing"

    def run(self, ctx: ToolContext) -> ToolOutput[UserIntent]:
        """Classify the intent of the user's input.

        Args:
            ctx: Tool context with questions and the user prompt

        Returns:
            ToolOutput containing a UserIntent or errors
        """
        if not ctx.prompt:
            return ToolOutput.failure(
                errors=[err("missing_prompt", "No user input provided")]
            )

        try:
            # Load the prompt template
            system_prompt = self._load_prompt("intent_classify.md")

            # Build user content with context
            user_content = self._build_user_content(ctx)

            # Hard Code Intent
            if "plan" in user_content.lower():
                intent = UserIntent(
                    intent_type="high_level_plan",
                    confidence=1.0,
                    reasoning="User is requesting a high-level analysis plan",
                )
            elif "cut" in user_content.lower():
                intent = UserIntent(
                    intent_type="cut_analysis",
                    confidence=1.0,
                    reasoning="User is requesting a specific cut analysis",
            )
            elif "segment" in user_content.lower():
                intent = UserIntent(
                    intent_type="segment_definition",
                    confidence=1.0,
                    reasoning="User is requesting a segment definition",
                )
            else:
                intent = UserIntent(
                    intent_type="chat",
                    confidence=1.0,
                    reasoning="User is requesting a general chat",
                )

            # Call LLM with structured output
            trace = {
                "model": None,
                "temperature": 0.0,
                "latency_s": 0.0,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "finish_reason": None,
            }

            return ToolOutput.success(data=intent, trace=trace)

        except Exception as e:
            return ToolOutput.failure(
                errors=[err("tool_error", f"Intent classification failed: {str(e)}")],
            )

    def _build_user_content(self, ctx: ToolContext) -> str:
        """Build the user message content."""
        return ctx.prompt
