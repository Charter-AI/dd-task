"""High-level analysis planner tool."""

from ascentra_agent.contracts.specs import HighLevelPlan
from ascentra_agent.contracts.tool_output import ToolOutput, err
from ascentra_agent.llm.structured import build_messages, chat_structured_pydantic
from ascentra_agent.tools.base import Tool, ToolContext


class HighLevelPlanner(Tool):
    @property
    def name(self) -> str:
        return "high_level_planner"

    @property
    def description(self) -> str:
        return "Creates a high-level analysis plan"

    def run(self, ctx: ToolContext) -> ToolOutput[HighLevelPlan]:
        system_prompt = self._load_prompt("high_level_plan.md")

        scope = ctx.scope or ""
        questions = ctx.get_questions_summary()
        user_content = (
            f"User request:\n{ctx.prompt or 'Create an analysis plan.'}\n\n"
            f"Scope:\n{scope}\n\n"
            f"Questions:\n{questions}\n"
        )
        messages = build_messages(system_prompt=system_prompt, user_content=user_content)

        try:
            plan, trace = chat_structured_pydantic(messages=messages, model=HighLevelPlan)
            return ToolOutput.success(data=plan, trace=trace)
        except Exception as e:
            return ToolOutput.failure(errors=[err("tool_error", f"Plan failed: {str(e)}")])


