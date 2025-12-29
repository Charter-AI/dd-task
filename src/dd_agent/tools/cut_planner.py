"""Cut planner tool for converting NL requests to CutSpecs."""

import json
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from dd_agent.contracts.specs import CutSpec, MetricSpec
from dd_agent.contracts.tool_output import ToolMessage, ToolOutput, err, warn
from dd_agent.contracts.validate import validate_cut_spec
from dd_agent.llm.structured import build_messages, chat_structured_pydantic
from dd_agent.tools.base import Tool, ToolContext


class AmbiguityOption(BaseModel):
    """A single ambiguity option for user selection."""
    question_id: str = Field(..., description="The question ID")
    label: str = Field(..., description="Human-readable label")
    match_reason: str = Field(..., description="Why this matches the user request")
    confidence: float = Field(default=0.0, description="Confidence score 0-1")
    question_type: str = Field(default="", description="Type of question")


class CutPlanResult(BaseModel):
    """Result of the cut planner tool."""
    ok: bool = Field(..., description="Whether planning succeeded")
    cut: Optional[CutSpec] = Field(default=None, description="The planned cut specification")
    resolution_map: Dict[str, str] = Field(default_factory=dict, description="Mapping of NL terms to question/segment IDs")
    ambiguity_options: List[AmbiguityOption] = Field(default_factory=list, description="Possible interpretations if ambiguous")
    requires_user_resolution: bool = Field(default=False, description="Whether user needs to resolve ambiguity")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Any errors from the LLM")


class CutPlanner(Tool):
    """Tool for converting natural language requests to CutSpecs.

    Takes a natural language analysis request (e.g., "Show NPS by region")
    and produces a validated CutSpec that can be executed deterministically.
    """

    @property
    def name(self) -> str:
        return "cut_planner"

    @property
    def description(self) -> str:
        return "Converts natural language analysis requests to executable CutSpecs"

    def run(self, ctx: ToolContext) -> ToolOutput[CutSpec]:
        """Execute the cut planner tool.

        Args:
            ctx: Tool context with questions, segments, and the prompt

        Returns:
            ToolOutput containing a validated CutSpec or errors
        """
        if not ctx.prompt:
            return ToolOutput.failure(
                errors=[err("missing_prompt", "No analysis request provided")]
            )

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
            cut_plan, llm_trace = chat_structured_pydantic(
                messages=messages,
                model=CutPlanResult,
                temperature=0.1
            )
            
            # 5. Process LLM response
            if not cut_plan.ok:
                # Convert error dicts to ToolMessage objects
                error_messages = []
                for error_dict in cut_plan.errors:
                    error_messages.append(ToolMessage(
                        code=error_dict.get("code", "llm_error"),
                        message=error_dict.get("message", "Unknown LLM error"),
                        context=error_dict.get("context", {})
                    ))
                
                return ToolOutput.failure(
                    errors=error_messages,
                    trace={
                        "prompt": ctx.prompt,
                        "llm_response": cut_plan.model_dump(),
                        "llm_trace": llm_trace
                    }
                )
            
            # 6. Check if user resolution is needed
            if cut_plan.requires_user_resolution and len(cut_plan.ambiguity_options) > 1:
                # Sort by confidence
                sorted_options = sorted(
                    cut_plan.ambiguity_options, 
                    key=lambda x: x.confidence, 
                    reverse=True
                )
                
                # Prepare user input options
                user_options = []
                for opt in sorted_options:
                    user_options.append({
                        "question_id": opt.question_id,
                        "label": opt.label,
                        "match_reason": opt.match_reason,
                        "confidence": opt.confidence,
                        "question_type": opt.question_type
                    })
                
                # Return partial result requiring user input
                return ToolOutput.partial_for_user_input(
                    prompt=f"Your request '{ctx.prompt}' could mean multiple things. Which one do you mean?",
                    options=user_options,
                    trace={
                        "prompt": ctx.prompt,
                        "ambiguity_options": [opt.model_dump() for opt in sorted_options],
                        "resolution_map": cut_plan.resolution_map,
                        "llm_trace": llm_trace
                    }
                )
            
            # 7. If no ambiguity or cut already generated, validate
            if cut_plan.cut:
                # Generate cut_id if missing
                if not cut_plan.cut.cut_id:
                    cut_plan.cut.cut_id = f"cut_{uuid.uuid4().hex[:8]}"
                
                # Validate using the existing validate_cut_spec function
                questions_by_id = {q.question_id: q for q in ctx.questions}
                segments_by_id = {s.segment_id: s for s in (ctx.segments or [])}
                
                validation_errors = validate_cut_spec(
                    cut_plan.cut, 
                    questions_by_id, 
                    segments_by_id
                )
                
                if validation_errors:
                    # Convert validation errors to ToolMessage format
                    tool_errors = []
                    for error_item in validation_errors:
                        # Handle different error formats
                        if isinstance(error_item, dict):
                            tool_errors.append(ToolMessage(
                                code=error_item.get("code", "validation_error"),
                                message=error_item.get("message", "Validation failed"),
                                context=error_item.get("context", {})
                            ))
                        elif isinstance(error_item, ToolMessage):
                            tool_errors.append(error_item)
                        else:
                            # Fallback
                            tool_errors.append(err("validation_error", str(error_item)))
                    
                    return ToolOutput.failure(
                        errors=tool_errors,
                        trace={
                            "prompt": ctx.prompt,
                            "validation_errors": validation_errors,
                            "llm_trace": llm_trace
                        }
                    )
                
                return ToolOutput.success(
                    data=cut_plan.cut,
                    warnings=[ToolMessage(
                        code="resolution_mapped", 
                        message=f"Mapped terms: {cut_plan.resolution_map}"
                    )] if cut_plan.resolution_map else [],
                    trace={
                        "prompt": ctx.prompt,
                        "resolution_map": cut_plan.resolution_map,
                        "llm_response": cut_plan.model_dump(),
                        "llm_trace": llm_trace,
                        "validation_passed": True
                    }
                )
            else:
                # No cut generated and no ambiguity? This shouldn't happen
                return ToolOutput.failure(
                    errors=[err("no_cut_generated", "LLM did not generate a CutSpec")]
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
            # Use question_id from the Question class
            question_desc = f"- ID: {q.question_id}, Label: '{q.label}', Type: {q.type.value}"
            if q.options:
                # Handle numeric option codes for Likert
                option_strings = []
                for opt in q.options:
                    # Show both code and label
                    option_strings.append(f"'{opt.code}': '{opt.label}'")
                options_str = ", ".join(option_strings)
                question_desc += f", Options: {{{options_str}}}"
            questions_info.append(question_desc)
        
        questions_str = "\n".join(questions_info)
        
        # Build segment catalog (if available)
        segments_str = ""
        if ctx.segments:
            segments_info = []
            for s in ctx.segments:
                segment_desc = f"- ID: {s.segment_id}, Name: '{s.name}'"
                # Add filter description if available
                if hasattr(s, 'definition') and s.definition:
                    segment_desc += f", Definition: {s.definition}"
                segments_info.append(segment_desc)
            segments_str = "\nAvailable Segments:\n" + "\n".join(segments_info)
        
        return f"""You are a data analysis expert responsible for converting natural language analysis requests into precise CutSpec specifications.

# Available Data
Here are the questions in the dataset:
{questions_str}
{segments_str}

# Task
Parse the user's natural language request into a CutSpec containing:
1. metric: The metric to compute (MetricSpec object with 'type', 'question_id', and 'params')
2. dimensions: List of dimensions to group by (each dimension is an object with 'kind' and 'id')
3. filter: Optional filter condition (can be null)

# Important Rules
## 1. Ambiguity Detection
When the user request could match multiple questions, YOU MUST:
- List ALL possible matches in ambiguity_options
- For EACH match, provide:
  * question_id: The actual question ID
  * label: The question label
  * match_reason: Why this matches (e.g., "Contains 'region' in label")
  * confidence: Your confidence 0.0-1.0
  * question_type: The type of question

## 2. When to Flag Ambiguity
Flag ambiguity when:
- Multiple questions contain similar keywords (e.g., "region" appears in Q_REGION and Q_GEOGRAPHY)
- The request is vague (e.g., "satisfaction" could mean Q_OVERALL_SAT or Q_SUPPORT_SAT)
- Question labels have synonyms (e.g., "country", "geography", "location" all map to region)

## 3. Metric Compatibility
TYPE          | COMPATIBLE METRICS
--------------|-------------------
nps_0_10      | 'nps', 'mean', 'frequency'
likert_1_5    | 'mean', 'top2box', 'bottom2box', 'frequency'
likert_1_7    | 'mean', 'top2box', 'bottom2box', 'frequency'
numeric       | 'mean', 'frequency'
single_choice | 'frequency'
multi_choice  | 'frequency'

Key constraints:
- 'nps' metric can ONLY be used with questions of type 'nps_0_10'
- 'top2box' and 'bottom2box' can ONLY be used with 'likert_1_5' or 'likert_1_7' questions
- If user says "NPS", you MUST use the nps_0_10 question
- If user says "top-2-box" or "top2box", find Likert questions
- Always include 'params' field in MetricSpec (can be empty dict)

## 4. Dimension Matching
- Find the question ID that best matches the user's description
- Example: "country" → look for questions with "country", "region", "location" in the label
- If multiple matches, list them in ambiguity_options
- For segments: use 'kind': 'segment' and the segment ID

## 5. Automatic Term Mapping
Common mappings:
- "NPS" or "Net Promoter Score" → Q_NPS (if exists)
- "satisfaction" or "sat" → Look for satisfaction questions
- "country", "region", "geography" → Q_REGION (if exists)
- "age" → Q_AGE (if exists)
- "income" → Q_INCOME (if exists)
- "gender" → Q_GENDER (if exists)
- "plan" or "subscription" → Q_PLAN (if exists)

## 6. Output Format
You must return a CutPlanResult object with this exact structure:
{{
    "ok": true,
    "cut": {{
        "cut_id": "suggested_id_here",
        "metric": {{
            "type": "metric_type",
            "question_id": "QUESTION_ID",
            "params": {{}}  # Always include params, can be empty or contain e.g. "top_values": [4, 5]
        }},
        "dimensions": [
            {{"kind": "question", "id": "QUESTION_ID"}}
        ],
        "filter": null
    }},
    "resolution_map": {{"user_term": "actual_id"}},
    "ambiguity_options": [],
    "requires_user_resolution": false,
    "errors": []
}}

# Critical Instructions
1. Check for ambiguity FIRST - if multiple matches, set requires_user_resolution=true
2. Sort ambiguity_options by confidence (highest first)
3. Ensure metric compatibility (check question type)
4. Generate a unique cut_id (e.g., "cut_nps_by_region")
5. Map user terms to actual question/segment IDs in resolution_map
6. If unsure about which question to use, add options to ambiguity_options
7. Return ONLY valid JSON, no other text

# Examples
Example 1: Ambiguous request
User: "Show satisfaction by region"
Available: Q_OVERALL_SAT (likert_1_5), Q_SUPPORT_SAT (likert_1_5), Q_REGION (single_choice)
Response: {{
    "ok": true,
    "cut": null,
    "resolution_map": {{"satisfaction": "multiple_possible", "region": "Q_REGION"}},
    "ambiguity_options": [
        {{
            "question_id": "Q_OVERALL_SAT",
            "label": "Overall, how satisfied are you with our product?",
            "match_reason": "User said 'satisfaction', this is overall satisfaction question",
            "confidence": 0.8,
            "question_type": "likert_1_5"
        }},
        {{
            "question_id": "Q_SUPPORT_SAT",
            "label": "How satisfied are you with our customer support?",
            "match_reason": "User said 'satisfaction', this is support satisfaction question",
            "confidence": 0.6,
            "question_type": "likert_1_5"
        }}
    ],
    "requires_user_resolution": true,
    "errors": []
}}

Example 2: Clear request
User: "Show NPS by region"
Available: Q_NPS (nps_0_10), Q_REGION (single_choice)
Response: {{
    "ok": true,
    "cut": {{
        "cut_id": "cut_nps_by_region",
        "metric": {{"type": "nps", "question_id": "Q_NPS", "params": {{}}}},
        "dimensions": [{{"kind": "question", "id": "Q_REGION"}}],
        "filter": null
    }},
    "resolution_map": {{"nps": "Q_NPS", "region": "Q_REGION"}},
    "ambiguity_options": [],
    "requires_user_resolution": false,
    "errors": []
}}

Example 3: Top-2-box request
User: "Top 2 box satisfaction by income level"
Available: Q_OVERALL_SAT (likert_1_5), Q_INCOME (single_choice)
Response: {{
    "ok": true,
    "cut": {{
        "cut_id": "cut_top2box_sat_by_income",
        "metric": {{"type": "top2box", "question_id": "Q_OVERALL_SAT", "params": {{"top_values": [4, 5]}}}},
        "dimensions": [{{"kind": "question", "id": "Q_INCOME"}}],
        "filter": null
    }},
    "resolution_map": {{"top 2 box satisfaction": "Q_OVERALL_SAT", "income level": "Q_INCOME"}},
    "ambiguity_options": [],
    "requires_user_resolution": false,
    "errors": []
}}

Now process the user request below."""

    def _build_user_content(self, ctx: ToolContext) -> str:
        """Build the user message content."""
        return f"""Analysis request: "{ctx.prompt}"

Based on the available questions and segments shown in the system prompt, generate the appropriate CutSpec.

IMPORTANT: Check for ambiguity first. If multiple questions could match the user's request, list them in ambiguity_options with detailed match reasons.

Remember:
1. Check for ambiguity and list all possible matches if any
2. Check metric compatibility with question type
3. Generate a cut_id (system will finalize it if missing)
4. Map user terms to actual IDs in resolution_map
5. Return ONLY valid JSON matching the CutPlanResult schema

JSON Output:"""