"""Segment definition builder tool."""

from ascentra_agent.contracts.specs import SegmentSpec
from ascentra_agent.contracts.tool_output import ToolOutput, err
from ascentra_agent.llm.structured import build_messages, chat_structured_pydantic
from ascentra_agent.tools.base import Tool, ToolContext


class SegmentBuilder(Tool):
    @property
    def name(self) -> str:
        return "segment_builder"

    @property
    def description(self) -> str:
        return "Builds a segment definition"

    def run(self, ctx: ToolContext) -> ToolOutput[SegmentSpec]:
        if not ctx.prompt:
            return ToolOutput.failure(
                errors=[err("missing_prompt", "No segment description provided")]
            )

        system_prompt = self._load_prompt("segment_plan.md")
        questions = ctx.get_questions_summary()
        user_content = f"Segment request:\n{ctx.prompt}\n\nQuestions:\n{questions}\n"
        messages = build_messages(system_prompt=system_prompt, user_content=user_content)

        try:
            seg, trace = chat_structured_pydantic(messages=messages, model=SegmentSpec)
            return ToolOutput.success(data=seg, trace=trace)
        except Exception as e:
            return ToolOutput.failure(errors=[err("tool_error", f"Segment failed: {str(e)}")])


