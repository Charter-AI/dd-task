"""Minimal Ascentra agent orchestrator (happy-path only)."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from ascentra_agent.contracts.filters import (
    And,
    FilterExpr,
    Not,
    Or,
    PredicateContainsAny,
    PredicateEq,
    PredicateGt,
    PredicateGte,
    PredicateIn,
    PredicateLt,
    PredicateLte,
    PredicateRange,
)
from ascentra_agent.contracts.questions import Question
from ascentra_agent.contracts.specs import (
    Action,
    ClarifyRequest,
    CutSpec,
    DisambiguationOption,
    SegmentSpec,
)
from ascentra_agent.contracts.specs import AgentResponse, UserIntent
from ascentra_agent.engine.executor import Executor
from ascentra_agent.tools.base import ToolContext
from ascentra_agent.tools.chat_responder import ChatResponder
from ascentra_agent.tools.cut_planner import CutPlanner
from ascentra_agent.tools.high_level_planner import HighLevelPlanner
from ascentra_agent.tools.intent_classifier import IntentClassifier
from ascentra_agent.tools.segment_builder import SegmentBuilder


def _q_label(question_id: str, questions_by_id: dict[str, Question]) -> str:
    q = questions_by_id.get(question_id)
    if q is None:
        return question_id
    return f"{q.label} ({q.question_id})"


def _segment_label(segment_id: str, segments_by_id: dict[str, SegmentSpec]) -> str:
    s = segments_by_id.get(segment_id)
    if s is None:
        return segment_id
    return f"{s.name} ({s.segment_id})"


def _format_filter(expr: FilterExpr, questions_by_id: dict[str, Question]) -> str:
    if isinstance(expr, PredicateEq):
        return f"{_q_label(expr.question_id, questions_by_id)} == {expr.value}"
    if isinstance(expr, PredicateIn):
        return f"{_q_label(expr.question_id, questions_by_id)} in {expr.values}"
    if isinstance(expr, PredicateRange):
        op = "between" if expr.inclusive else "strictly between"
        return f"{_q_label(expr.question_id, questions_by_id)} {op} [{expr.min}, {expr.max}]"
    if isinstance(expr, PredicateContainsAny):
        return f"{_q_label(expr.question_id, questions_by_id)} contains any of {expr.values}"
    if isinstance(expr, PredicateGt):
        return f"{_q_label(expr.question_id, questions_by_id)} > {expr.value}"
    if isinstance(expr, PredicateGte):
        return f"{_q_label(expr.question_id, questions_by_id)} >= {expr.value}"
    if isinstance(expr, PredicateLt):
        return f"{_q_label(expr.question_id, questions_by_id)} < {expr.value}"
    if isinstance(expr, PredicateLte):
        return f"{_q_label(expr.question_id, questions_by_id)} <= {expr.value}"
    if isinstance(expr, And):
        parts = [_format_filter(c, questions_by_id) for c in expr.children]
        return "(" + " AND ".join(parts) + ")"
    if isinstance(expr, Or):
        parts = [_format_filter(c, questions_by_id) for c in expr.children]
        return "(" + " OR ".join(parts) + ")"
    if isinstance(expr, Not):
        return "(NOT " + _format_filter(expr.child, questions_by_id) + ")"
    return str(expr)


def _format_cut_spec(
    cut: CutSpec,
    questions_by_id: dict[str, Question],
    segments_by_id: dict[str, SegmentSpec],
) -> str:
    metric = f"{cut.metric.type} on {_q_label(cut.metric.question_id, questions_by_id)}"

    dims: list[str] = []
    for d in cut.dimensions:
        if d.kind == "question":
            dims.append(_q_label(d.id, questions_by_id))
        else:
            dims.append(_segment_label(d.id, segments_by_id))

    filter_str = None
    if cut.filter is not None:
        filter_str = _format_filter(cut.filter, questions_by_id)

    lines = [
        "CutSpec:",
        f"- cut_id: {cut.cut_id}",
        f"- metric: {metric}",
        f"- dimensions: {', '.join(dims) if dims else '(none)'}",
        f"- filter: {filter_str if filter_str else '(none)'}",
    ]
    if cut.metric.params:
        lines.append(f"- metric_params: {cut.metric.params}")
    return "\n".join(lines)


class Agent:
    """Routes messages to tools and executes cuts with pandas.

    Intentionally no retries, no ambiguity detection, no persistence.
    """

    def __init__(
        self,
        questions: list[Question],
        responses_df: pd.DataFrame,
        scope: Optional[str] = None,
    ) -> None:
        self.questions = questions
        self.questions_by_id = {q.question_id: q for q in questions}
        self.responses_df = responses_df
        self.scope = scope

        self.segments: list[SegmentSpec] = []
        self.segments_by_id: dict[str, SegmentSpec] = {}

        self.intent_classifier = IntentClassifier()
        self.chat_responder = ChatResponder()
        self.high_level_planner = HighLevelPlanner()
        self.cut_planner = CutPlanner()
        self.segment_builder = SegmentBuilder()

        # Minimal clarification: store a single set of pending options for numeric selection.
        # No persistence across runs; cleared after a selection or any non-numeric follow-up.
        self._pending_actions: list[DisambiguationOption] | None = None

    def _maybe_build_clarification(self, user_input: str) -> ClarifyRequest | None:
        """Build a minimal clarification prompt for ambiguous inputs.

        Happy-path only:
        - Trigger when a single token matches multiple questions ("satisfaction")
        - Trigger for "plan" if there is a plan-related question (command vs question collision)
        - Provide up to 5 options
        """
        token = user_input.strip()
        if not token:
            return None

        t = token.lower().strip()
        tokens = t.split()

        # For MVP, handle two patterns:
        # 1) single token ambiguity (e.g. "satisfaction")
        # 2) "plan" collision in short inputs like "plan" or "analyze plan"
        plan_collision = "plan" in tokens and any(
            ("plan" in q.label.lower()) or (q.question_id.lower() == "q_plan")
            for q in self.questions
        )

        single_token = len(tokens) == 1

        matches: list[Question] = []
        for q in self.questions:
            if single_token and (t == q.question_id.lower() or t in q.label.lower()):
                matches.append(q)

        if (single_token and len(matches) <= 1) and not plan_collision:
            return None

        options: list[DisambiguationOption] = []

        if plan_collision:
            options.append(
                DisambiguationOption(
                    option_id="opt_high_level_plan",
                    label="Create analysis plan",
                    action_type="high_level_plan",
                    action_params={},
                )
            )
            # If we have a literal Q_PLAN, offer it as the competing cut.
            q_plan = self.questions_by_id.get("Q_PLAN")
            if q_plan is not None:
                options.append(
                    DisambiguationOption(
                        option_id="opt_cut_q_plan",
                        label=f"Analyze {_q_label(q_plan.question_id, self.questions_by_id)}",
                        action_type="cut_analysis",
                        action_params={"question_id": q_plan.question_id},
                    )
                )

        # Single-token ambiguity: multiple matching questions
        for q in matches[:5]:
            options.append(
                DisambiguationOption(
                    option_id=f"opt_cut_{q.question_id}",
                    label=f"Analyze {_q_label(q.question_id, self.questions_by_id)}",
                    action_type="cut_analysis",
                    action_params={"question_id": q.question_id},
                )
            )

        # De-duplicate by option_id while preserving order
        seen: set[str] = set()
        deduped: list[DisambiguationOption] = []
        for o in options:
            if o.option_id in seen:
                continue
            seen.add(o.option_id)
            deduped.append(o)

        if not deduped:
            return None

        return ClarifyRequest(
            question="I am not sure what you meant. Which of these did you want?",
            options=deduped[:5],
        )

    def _execute_action(self, action: DisambiguationOption) -> AgentResponse:
        """Execute a minimal action produced by clarification.

        Important: do not route back through `handle_message()` with a prompt like "plan",
        because that would immediately trigger clarification again. Instead, dispatch
        directly to the relevant tool path.
        """
        if action.action_type == "high_level_plan":
            plan_out = self.high_level_planner.run(self._ctx("Create an analysis plan"))
            if not plan_out.ok or plan_out.data is None:
                return AgentResponse(
                    intent=UserIntent(
                        intent_type="high_level_plan",
                        confidence=1.0,
                        reasoning="clarify selection",
                    ),
                    success=False,
                    errors=[f"{e.code}: {e.message}" for e in plan_out.errors],
                )

            plan = plan_out.data
            lines = ["Analysis plan:"]
            for i, item in enumerate(plan.intents[:20], 1):
                lines.append(f"{i}. {item.description} (priority {item.priority})")
            return AgentResponse(
                intent=UserIntent(
                    intent_type="high_level_plan",
                    confidence=1.0,
                    reasoning="clarify selection",
                ),
                success=True,
                message="\n".join(lines),
                data=plan,
            )

        if action.action_type == "segment_definition":
            # Minimal: treat the label as the prompt.
            return self.handle_message(action.label)

        if action.action_type == "cut_analysis":
            question_id = action.action_params.get("question_id")
            prompt = (
                f"analyze {question_id}" if question_id else (action.action_params.get("request") or action.label)
            )
            cut_out = self.cut_planner.run(self._ctx(prompt))
            if not cut_out.ok or cut_out.data is None:
                return AgentResponse(
                    intent=UserIntent(
                        intent_type="cut_analysis",
                        confidence=1.0,
                        reasoning="clarify selection",
                    ),
                    success=False,
                    errors=[f"{e.code}: {e.message}" for e in cut_out.errors],
                )

            cut = cut_out.data
            exec_result = Executor(
                df=self.responses_df,
                questions_by_id=self.questions_by_id,
                segments_by_id=self.segments_by_id,
            ).execute_cuts([cut])

            if exec_result.errors:
                return AgentResponse(
                    intent=UserIntent(
                        intent_type="cut_analysis",
                        confidence=1.0,
                        reasoning="clarify selection",
                    ),
                    success=False,
                    errors=[str(e) for e in exec_result.errors],
                )

            table = exec_result.tables[0] if exec_result.tables else None
            base_n = table.base_n if table else 0
            df = table.get_dataframe() if table else None
            cut_text = _format_cut_spec(cut, self.questions_by_id, self.segments_by_id)
            msg = f"{cut_text}\n\nBase N: {base_n}"
            if df is not None and not df.empty:
                msg += "\n\n" + df.head(20).to_string(index=False)

            return AgentResponse(
                intent=UserIntent(
                    intent_type="cut_analysis",
                    confidence=1.0,
                    reasoning="clarify selection",
                ),
                success=True,
                message=msg,
                data=exec_result,
            )

        return self.handle_message(action.label)

    def _ctx(self, prompt: str) -> ToolContext:
        return ToolContext(
            questions=self.questions,
            questions_by_id=self.questions_by_id,
            segments=self.segments,
            segments_by_id=self.segments_by_id,
            scope=self.scope,
            prompt=prompt,
            responses_df=self.responses_df,
        )

    def handle_message(self, user_input: str) -> AgentResponse:
        # Minimal clarification: if we have pending options, accept a numeric selection.
        text = user_input.strip()
        if self._pending_actions is not None:
            if text.isdigit():
                idx = int(text)
                if 1 <= idx <= len(self._pending_actions):
                    action = self._pending_actions[idx - 1]
                    self._pending_actions = None
                    return self._execute_action(action)
                # Happy-path fallback: clear and continue normal routing.
                self._pending_actions = None
            else:
                # Any non-numeric follow-up cancels the clarification prompt.
                self._pending_actions = None

        clarify = self._maybe_build_clarification(user_input)
        if clarify is not None:
            self._pending_actions = clarify.options
            lines = [clarify.question, "", "Please choose one:"]
            for i, opt in enumerate(clarify.options, 1):
                lines.append(f"{i}) {opt.label}")
            lines.append("Reply with a number.")
            return AgentResponse(
                intent=UserIntent(
                    intent_type="clarify",
                    confidence=1.0,
                    reasoning="ambiguous input",
                ),
                success=True,
                message="\n".join(lines),
                clarify=clarify,
            )

        intent_out = self.intent_classifier.run(self._ctx(user_input))
        if not intent_out.ok or intent_out.data is None:
            return AgentResponse(
                intent=UserIntent(intent_type="chat", confidence=0.0, reasoning="intent failed"),
                success=False,
                errors=[f"{e.code}: {e.message}" for e in intent_out.errors],
            )

        intent = intent_out.data

        if intent.intent_type == "high_level_plan":
            plan_out = self.high_level_planner.run(self._ctx(user_input))
            if not plan_out.ok or plan_out.data is None:
                return AgentResponse(
                    intent=intent,
                    success=False,
                    errors=[f"{e.code}: {e.message}" for e in plan_out.errors],
                )

            plan = plan_out.data
            lines = ["Analysis plan:"]
            for i, item in enumerate(plan.intents[:20], 1):
                lines.append(f"{i}. {item.description} (priority {item.priority})")
            return AgentResponse(intent=intent, success=True, message="\n".join(lines), data=plan)

        if intent.intent_type == "segment_definition":
            seg_out = self.segment_builder.run(self._ctx(user_input))
            if not seg_out.ok or seg_out.data is None:
                return AgentResponse(
                    intent=intent,
                    success=False,
                    errors=[f"{e.code}: {e.message}" for e in seg_out.errors],
                )

            seg = seg_out.data
            self.segments = [s for s in self.segments if s.segment_id != seg.segment_id] + [
                seg
            ]
            self.segments_by_id[seg.segment_id] = seg
            return AgentResponse(
                intent=intent,
                success=True,
                message=f"Created segment {seg.name} ({seg.segment_id})",
                data=seg,
            )

        if intent.intent_type == "cut_analysis":
            cut_out = self.cut_planner.run(self._ctx(user_input))
            if not cut_out.ok or cut_out.data is None:
                return AgentResponse(
                    intent=intent,
                    success=False,
                    errors=[f"{e.code}: {e.message}" for e in cut_out.errors],
                )

            cut = cut_out.data
            exec_result = Executor(
                df=self.responses_df,
                questions_by_id=self.questions_by_id,
                segments_by_id=self.segments_by_id,
            ).execute_cuts([cut])

            if exec_result.errors:
                return AgentResponse(intent=intent, success=False, errors=[str(e) for e in exec_result.errors])

            table = exec_result.tables[0]
            df = table.get_dataframe()
            cut_text = _format_cut_spec(cut, self.questions_by_id, self.segments_by_id)
            msg = f"{cut_text}\n\nBase N: {table.base_n}"
            if df is not None and not df.empty:
                msg += "\n\n" + df.head(20).to_string(index=False)
            return AgentResponse(intent=intent, success=True, message=msg, data=exec_result)

        chat_out = self.chat_responder.run(self._ctx(user_input))
        if not chat_out.ok or chat_out.data is None:
            return AgentResponse(
                intent=intent,
                success=False,
                errors=[f"{e.code}: {e.message}" for e in chat_out.errors],
            )
        return AgentResponse(intent=intent, success=True, message=chat_out.data.message, data=chat_out.data)


