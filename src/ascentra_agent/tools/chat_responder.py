"""Chat response tool."""

from ascentra_agent.contracts.specs import ChatResponse
from ascentra_agent.contracts.tool_output import ToolOutput, err
from ascentra_agent.llm.structured import build_messages, chat_structured_pydantic
from ascentra_agent.tools.base import Tool, ToolContext


class ChatResponder(Tool):
    @property
    def name(self) -> str:
        return "chat_responder"

    @property
    def description(self) -> str:
        return "Generates a conversational response"

    def run(self, ctx: ToolContext) -> ToolOutput[ChatResponse]:
        if not ctx.prompt:
            return ToolOutput.failure(errors=[err("missing_prompt", "No user input provided")])

        system_prompt = self._load_prompt("chat_respond.md")
        user_content = ctx.prompt
        messages = build_messages(system_prompt=system_prompt, user_content=user_content)

        try:
            resp, trace = chat_structured_pydantic(messages=messages, model=ChatResponse)
            return ToolOutput.success(data=resp, trace=trace)
        except Exception as e:
            return ToolOutput.failure(errors=[err("tool_error", f"Chat failed: {str(e)}")])


