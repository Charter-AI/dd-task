"""High-level analysis planner tool."""

import json
from typing import Any, Optional
from pydantic import BaseModel, Field

from dd_agent.contracts.specs import HighLevelPlan, AnalysisIntent, SegmentSpec
from dd_agent.contracts.tool_output import ToolMessage, ToolOutput, err
from dd_agent.llm.structured import build_messages, chat_structured_pydantic
from dd_agent.tools.base import Tool, ToolContext


class HighLevelPlanResult(BaseModel):
    """Result of the high-level planner tool."""

    ok: bool = Field(..., description="Whether planning succeeded")
    plan: Optional[HighLevelPlan] = Field(
        default=None, description="The generated high-level plan"
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list, description="Any errors from the LLM"
    )


class HighLevelPlanner(Tool):
    """Tool for generating high-level analysis plans.

    Given a question catalog and optional scope document, this tool
    proposes a comprehensive set of analysis intents that would
    provide valuable insights from the survey data.
    """

    @property
    def name(self) -> str:
        return "high_level_planner"

    @property
    def description(self) -> str:
        return "Generates a high-level analysis plan with intents and suggested segments"

    def run(self, ctx: ToolContext) -> ToolOutput[HighLevelPlan]:
        """Execute the high-level planning tool.

        Args:
            ctx: Tool context with questions and optional scope

        Returns:
            ToolOutput containing a HighLevelPlan or errors
        """
        try:
            # 1. Prepare context information
            user_content = self._build_user_content(ctx)
            
            # 2. Build system prompt
            system_prompt = self._build_system_prompt(ctx)
            
            # 3. Call LLM to generate structured output
            messages = build_messages(
                system_prompt=system_prompt,
                user_content=user_content
            )
            
            # 4. Get LLM response
            plan_result, llm_trace = chat_structured_pydantic(
                messages=messages,
                model=HighLevelPlanResult,
                temperature=0.3  # Slightly higher for creative planning
            )
            
            # 5. Process LLM response
            if not plan_result.ok:
                return ToolOutput.failure(
                    errors=[err("llm_failed", f"LLM failed to produce valid plan: {plan_result.errors}")]
                )
            
            # 6. Validate the generated plan
            if plan_result.plan:
                validation_errors = self._validate_plan(plan_result.plan, ctx)
                
                if validation_errors:
                    return ToolOutput.failure(
                        errors=validation_errors
                    )
                
                return ToolOutput.success(
                    data=plan_result.plan,
                    trace={
                        "llm_response": plan_result.model_dump(),
                        "llm_trace": llm_trace,
                        "validation_passed": True
                    }
                )
            else:
                return ToolOutput.failure(
                    errors=[err("no_plan_generated", "LLM did not generate a plan")]
                )
                
        except Exception as e:
            return ToolOutput.failure(
                errors=[err("unexpected_error", f"Unexpected error: {str(e)}")]
            )

    def _build_system_prompt(self, ctx: ToolContext) -> str:
        """Build the system prompt to guide LLM reasoning."""
        
        # Build string representation of question catalog
        questions_info = []
        for q in ctx.questions:
            question_desc = f"- ID: {q.question_id}, Label: '{q.label}', Type: {q.type.value}"
            if q.options:
                option_strings = [f"'{opt.code}': '{opt.label}'" for opt in q.options]
                options_str = ", ".join(option_strings)
                question_desc += f", Options: {{{options_str}}}"
            questions_info.append(question_desc)
        
        questions_str = "\n".join(questions_info)
        
        # Add scope if available
        scope_str = ""
        if ctx.scope:
            scope_str = f"\n\n# Project Scope\n{ctx.scope[:2000]}..."  # Limit scope length
        
        return f"""You are a senior data analyst responsible for creating comprehensive analysis plans for survey data.

# Available Data
Here are the questions in the dataset:
{questions_str}
{scope_str}

# Task
Create a high-level analysis plan that identifies key insights and patterns in the survey data.

Your plan should include:
1. **rationale**: Overall rationale for the analysis plan (why these analyses are important)
2. **intents**: Specific analyses to perform (at least 3-5)
3. **suggested_segments**: Important customer segments to create and analyze

# Analysis Intent Format
Each analysis intent must have:
- intent_id: Unique identifier like "intent_001", "intent_002", etc.
- description: Natural language description of what to analyze
- segments_needed: List of segment IDs that might be needed for this analysis
- priority: Integer where 1=high, 2=medium, 3=low

# Segment Suggestions
For segments, suggest:
- segment_id: Unique identifier
- name: Human-readable name
- definition: Filter expression that defines the segment
- intended_partition: Usually false
- notes: Optional notes about why this segment is important

# Important Data Characteristics
Key questions in the dataset:
1. Q_NPS: Net Promoter Score (0-10) - for customer loyalty analysis
2. Q_OVERALL_SAT: Overall satisfaction (Likert 1-5)
3. Q_REGION: Geographic region - for regional comparisons
4. Q_INCOME: Income level - for demographic segmentation
5. Q_PLAN: Subscription plan - for customer tier analysis
6. Q_TENURE: Customer tenure - for loyalty analysis
7. Q_FEATURES_USED: Multi-choice feature usage - for product analysis

# Output Format
Return a HighLevelPlanResult object with this EXACT structure:
{{
    "ok": true,
    "plan": {{
        "rationale": "Overall rationale explaining why these analyses are valuable for business decisions",
        "intents": [
            {{
                "intent_id": "intent_001",
                "description": "Analyze NPS by region to understand regional satisfaction differences",
                "segments_needed": [],
                "priority": 1
            }}
        ],
        "suggested_segments": [
            {{
                "segment_id": "promoters",
                "name": "Promoters",
                "definition": {{"kind": "range", "question_id": "Q_NPS", "min": 9, "max": 10, "inclusive": true}},
                "intended_partition": false,
                "notes": "Customers who are highly likely to recommend (NPS 9-10)"
            }}
        ]
    }},
    "errors": []
}}

# Critical Instructions
1. MUST include a "rationale" field explaining the plan
2. Each intent MUST have: intent_id, description, segments_needed (list), priority (1,2,3)
3. priority: 1=high, 2=medium, 3=low
4. segments_needed should list segment_ids from suggested_segments if needed
5. For definition field, use proper FilterExpr JSON structure
6. Return ONLY valid JSON, no other text

# Example Intents (adapt to actual data):
1. "Analyze NPS by region" - priority 1
2. "Compare satisfaction across subscription plans" - priority 1  
3. "Analyze feature usage correlation with satisfaction" - priority 2
4. "Segment customers by tenure and analyze NPS" - priority 2
5. "Identify at-risk customers (low NPS + low purchase intent)" - priority 1

# Example Segments (adapt to actual data):
1. Promoters (NPS 9-10)
2. Detractors (NPS 0-6)
3. Enterprise customers (Q_PLAN = "ENT")
4. High income customers (Q_INCOME = "HIGH" or "VHIGH")
5. Long-term customers (Q_TENURE = "LONG")

Now create an analysis plan for this dataset."""

    def _build_user_content(self, ctx: ToolContext) -> str:
        """Build the user message content."""
        return """Based on the available questions shown above, generate a comprehensive analysis plan.

Focus on insights that would help understand customer satisfaction, identify improvement areas, and support business decisions.

Make sure to include:
1. A clear rationale explaining the plan
2. At least 5 analysis intents with proper intent_id, description, segments_needed, and priority
3. Suggested segments with proper filter definitions

JSON Output:"""

    def _validate_plan(
        self, plan: HighLevelPlan, ctx: ToolContext
    ) -> list[Any]:
        """Validate the generated plan."""
        errors = []
        questions_by_id = {q.question_id: q for q in ctx.questions}
        
        # Check that all intents have required fields
        for i, intent in enumerate(plan.intents):
            if not intent.intent_id:
                errors.append(f"Intent at index {i} missing intent_id")
            if not intent.description:
                errors.append(f"Intent {intent.intent_id} missing description")
            if not hasattr(intent, 'priority') or intent.priority not in [1, 2, 3]:
                errors.append(f"Intent {intent.intent_id} has invalid priority: {getattr(intent, 'priority', 'missing')}")
        
        # Check rationale
        if not plan.rationale or len(plan.rationale.strip()) < 10:
            errors.append("Rationale is too short or missing")
        
        return errors