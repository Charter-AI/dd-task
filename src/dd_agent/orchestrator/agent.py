"""Agent for coordinating tools and execution."""

from pathlib import Path
from typing import Optional

import pandas as pd

from dd_agent.contracts.questions import Question
from dd_agent.contracts.specs import CutSpec, SegmentSpec
from dd_agent.contracts.tool_output import ToolOutput
from dd_agent.engine.executor import ExecutionResult, Executor
from dd_agent.tools.base import ToolContext
from dd_agent.tools.cut_planner import CutPlanner
from dd_agent.tools.high_level_planner import HighLevelPlanner
from dd_agent.tools.segment_builder import SegmentBuilder


class Agent:
    """Agent that coordinates tools and execution.

    The agent provides a high-level interface for:
    - Planning analyses (high-level and cut-level)
    - Building segments
    - Executing validated specifications
    """

    def __init__(
        self,
        questions: list[Question],
        responses_df: pd.DataFrame,
        scope: Optional[str] = None,
        data_dir: Optional[Path] = None,
    ):
        """Initialize the agent.

        Args:
            questions: List of question definitions
            responses_df: DataFrame with survey responses
            scope: Optional project scope document
            data_dir: Optional data directory path
        """
        self.questions = questions
        self.questions_by_id = {q.question_id: q for q in questions}
        self.responses_df = responses_df
        self.scope = scope
        self.data_dir = data_dir

        # Segments built during the session
        self.segments: list[SegmentSpec] = []
        self.segments_by_id: dict[str, SegmentSpec] = {}

        # Initialize tools
        self.high_level_planner = HighLevelPlanner()
        self.cut_planner = CutPlanner()
        self.segment_builder = SegmentBuilder()

    def _get_context(self, prompt: Optional[str] = None) -> ToolContext:
        """Get a tool context with current state."""
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

    def plan_analysis(self) -> ToolOutput:
        """Generate a high-level analysis plan.

        Uses the high-level planner to propose analysis intents
        based on the available questions and project scope.

        Returns:
            ToolOutput with HighLevelPlan or errors
        """
        # Get context with scope but no specific prompt
        context = self._get_context()
        
        # Call the high-level planner tool
        plan_result = self.high_level_planner.run(context)
        
        if not plan_result.ok:
            return ToolOutput.failure(
                errors=plan_result.errors,
                warnings=plan_result.warnings,
                trace=plan_result.trace
            )
        
        # If the planner suggested segments, add them to the session
        if hasattr(plan_result.data, 'suggested_segments') and plan_result.data.suggested_segments:
            for segment_spec in plan_result.data.suggested_segments:
                self.add_segment(segment_spec)
        
        return plan_result

    def plan_cut(self, request: str) -> ToolOutput[CutSpec]:
        """Plan a single cut from a natural language request.

        Args:
            request: Natural language analysis request

        Returns:
            ToolOutput with CutSpec or errors
        """
        # Get context with the user's request
        context = self._get_context(prompt=request)
        
        # Call the cut planner tool
        cut_result = self.cut_planner.run(context)
        
        # Return the result directly (cut planner already validates)
        return cut_result

    def build_segment(self, definition: str) -> ToolOutput[SegmentSpec]:
        """Build a segment from a natural language definition.

        Args:
            definition: Natural language segment definition

        Returns:
            ToolOutput with SegmentSpec or errors
        """
        # Get context with the segment definition
        context = self._get_context(prompt=definition)
        
        # Call the segment builder tool
        segment_result = self.segment_builder.run(context)
        
        # If successful, add the segment to the session
        if segment_result.ok and segment_result.data:
            self.add_segment(segment_result.data)
        
        return segment_result

    def add_segment(self, segment: SegmentSpec) -> None:
        """Add a segment to the session.

        Args:
            segment: The segment to add
        """
        # Replace if exists
        self.segments = [s for s in self.segments if s.segment_id != segment.segment_id]
        self.segments.append(segment)
        self.segments_by_id[segment.segment_id] = segment

    def execute_cuts(self, cuts: list[CutSpec]) -> ExecutionResult:
        """Execute a list of validated cut specifications.

        Args:
            cuts: List of CutSpec objects to execute

        Returns:
            ExecutionResult with tables and any errors
        """
        # Initialize the executor with current state
        executor = Executor(
            df=self.responses_df,
            questions_by_id=self.questions_by_id,
            segments_by_id=self.segments_by_id,
            min_base_size=30,  # Default values
            warn_base_size=100
        )
        
        # Execute all cuts
        return executor.execute_cuts(cuts)

    def execute_single_cut(self, cut: CutSpec) -> ExecutionResult:
        """Execute a single cut specification.

        Args:
            cut: The CutSpec to execute

        Returns:
            ExecutionResult with the table
        """
        return self.execute_cuts([cut])

    def resolve_ambiguity_and_plan(self, request: str, choice_index: int) -> ToolOutput[CutSpec]:
        """Resolve ambiguity by user choice and plan cut.
        
        Args:
            request: Original request
            choice_index: Index of user's choice (0-based)
            
        Returns:
            ToolOutput with resolved CutSpec
        """
        # First call to get ambiguity options
        context = self._get_context(prompt=request)
        initial_result = self.cut_planner.run(context)
        
        if not hasattr(initial_result, 'requires_user_input') or not initial_result.requires_user_input:
            return initial_result
        
        # Get the selected question ID
        if choice_index < 0 or choice_index >= len(initial_result.user_input_options):
            return ToolOutput.failure(
                errors=[err("invalid_choice", f"Invalid choice index: {choice_index}")]
            )
        
        selected_option = initial_result.user_input_options[choice_index]
        selected_question_id = selected_option.get("question_id")
        
        if not selected_question_id:
            return ToolOutput.failure(
                errors=[err("no_question_id", "Selected option has no question_id")]
            )
        
        # Create a modified prompt with the selection
        modified_prompt = f"{request} (use question: {selected_question_id})"
        modified_context = self._get_context(prompt=modified_prompt)
        
        # Try again with modified prompt
        return self.cut_planner.run(modified_context)