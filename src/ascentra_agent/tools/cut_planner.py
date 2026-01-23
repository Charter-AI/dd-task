"""Cut specification planner tool."""

from typing import Any

from pydantic import BaseModel, Field

from ascentra_agent.contracts.specs import CutSpec
from ascentra_agent.contracts.tool_output import ToolOutput, err
from ascentra_agent.llm.structured import build_messages, chat_structured_pydantic
from ascentra_agent.tools.base import Tool, ToolContext


class CutPlanResult(BaseModel):
    ok: bool = True
    cut: CutSpec
    resolution_map: dict[str, str] = Field(default_factory=dict)
    ambiguity_options: list[str] = Field(default_factory=list)
    debug: dict[str, Any] = Field(default_factory=dict)


class CutPlanner(Tool):
    @property
    def name(self) -> str:
        return "cut_planner"

    @property
    def description(self) -> str:
        return "Creates a cut specification"

    def run(self, ctx: ToolContext) -> ToolOutput[CutSpec]:
        if not ctx.prompt:
            return ToolOutput.failure(errors=[err("missing_prompt", "No analysis request provided")])

        system_prompt = self._load_prompt("cut_plan.md")
        questions = ctx.get_questions_summary()
        segments = ctx.get_segments_summary()

        user_content = (
            f"Request:\n{ctx.prompt}\n\n"
            f"Questions:\n{questions}\n\n"
            f"Segments:\n{segments}\n"
        )
        messages = build_messages(system_prompt=system_prompt, user_content=user_content)

        try:
            plan, trace = chat_structured_pydantic(messages=messages, model=CutPlanResult)
            if not plan.ok:
                return ToolOutput.failure(
                    errors=[err("planning_failed", "Cut planner returned ok=false")],
                    trace=trace,
                )
            return ToolOutput.success(
                data=plan.cut,
                trace={**trace, "resolution_map": plan.resolution_map},
            )
        except Exception as e:
            return ToolOutput.failure(errors=[err("tool_error", f"Cut planning failed: {str(e)}")])


