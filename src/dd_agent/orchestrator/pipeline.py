"""Pipeline for running analysis flows."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from dd_agent.contracts.questions import Question
from dd_agent.contracts.specs import CutSpec, HighLevelPlan, SegmentSpec
from dd_agent.contracts.tool_output import ToolOutput
from dd_agent.engine.executor import ExecutionResult
from dd_agent.orchestrator.agent import Agent
from dd_agent.run_store import RunStore
from dd_agent.util.logging import get_logger

logger = get_logger("pipeline")


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""

    success: bool
    run_id: str
    run_dir: Path
    plan: Optional[HighLevelPlan] = None
    cuts_planned: list[CutSpec] = field(default_factory=list)
    cuts_failed: list[dict[str, Any]] = field(default_factory=list)
    execution_result: Optional[ExecutionResult] = None
    errors: list[str] = field(default_factory=list)


class Pipeline:
    """Pipeline for running analysis flows.

    Provides two main flows:
    1. run_single: Execute a single analysis request
    2. run_autoplan: Generate and execute a full analysis plan
    """

    def __init__(
        self,
        data_dir: Path,
        runs_dir: Optional[Path] = None,
    ):
        """Initialize the pipeline.

        Args:
            data_dir: Directory containing questions.json, responses.csv, scope.md
            runs_dir: Directory for saving run artifacts (defaults to data_dir/runs)
        """
        self.data_dir = Path(data_dir)
        self.runs_dir = runs_dir or self.data_dir / "runs"

        # Load data
        self.questions = self._load_questions()
        self.responses_df = self._load_responses()
        self.scope = self._load_scope()

        # Create agent
        self.agent = Agent(
            questions=self.questions,
            responses_df=self.responses_df,
            scope=self.scope,
            data_dir=self.data_dir,
        )

    def _load_questions(self) -> list[Question]:
        """Load questions from questions.json."""
        questions_path = self.data_dir / "questions.json"
        if not questions_path.exists():
            raise FileNotFoundError(f"Questions file not found: {questions_path}")

        with open(questions_path) as f:
            data = json.load(f)

        # Handle both list and dict formats
        if isinstance(data, list):
            return [Question.model_validate(q) for q in data]
        elif isinstance(data, dict) and "questions" in data:
            return [Question.model_validate(q) for q in data["questions"]]
        else:
            raise ValueError("Invalid questions.json format")

    def _load_responses(self) -> pd.DataFrame:
        """Load responses from responses.csv."""
        responses_path = self.data_dir / "responses.csv"
        if not responses_path.exists():
            raise FileNotFoundError(f"Responses file not found: {responses_path}")

        return pd.read_csv(responses_path)

    def _load_scope(self) -> Optional[str]:
        """Load scope from scope.md if it exists."""
        scope_path = self.data_dir / "scope.md"
        if scope_path.exists():
            return scope_path.read_text()
        return None

    def run_single(
        self,
        prompt: str,
        save_run: bool = True,
    ) -> PipelineResult:
        """Execute a single analysis request.

        Args:
            prompt: Natural language analysis request
            save_run: Whether to save run artifacts

        Returns:
            PipelineResult with execution details
        """
        # 1. Initialize RunStore
        run_store = RunStore(self.runs_dir)
        run_id = run_store.create_run(prompt)
        run_dir = run_store.get_run_dir(run_id)
        
        logger.info(f"Starting run {run_id} with prompt: {prompt}")

        try:
            # 2. Plan the cut via agent
            logger.info(f"Planning cut for: {prompt}")
            cut_result = self.agent.plan_cut(prompt)
            
            if not cut_result.ok:
                errors = [str(e) for e in cut_result.errors]
                logger.error(f"Cut planning failed: {errors}")
                
                return PipelineResult(
                    success=False,
                    run_id=run_id,
                    run_dir=run_dir,
                    errors=errors
                )
            
            cut_spec = cut_result.data
            logger.info(f"Cut planned successfully: {cut_spec.cut_id}")

            # 3. Execute the cut
            logger.info(f"Executing cut: {cut_spec.cut_id}")
            execution_result = self.agent.execute_single_cut(cut_spec)
            
            # 4. Save artifacts and generate report
            if save_run:
                # Save input prompt
                run_store.save_artifact(run_id, "user_prompt.txt", prompt)
                
                # Save cut specification
                run_store.save_artifact(
                    run_id, 
                    "cut_spec.json", 
                    json.dumps(cut_spec.model_dump(), indent=2)
                )
                
                # Save execution results
                if execution_result.tables:
                    # Save each table
                    for i, table in enumerate(execution_result.tables):
                        table_filename = f"table_{i}_{cut_spec.cut_id}.json"
                        run_store.save_artifact(
                            run_id,
                            table_filename,
                            json.dumps(table.model_dump(), indent=2)
                        )
                        
                        # Also save as CSV for easy viewing
                        if hasattr(table, 'df') and table.df is not None:
                            csv_filename = f"table_{i}_{cut_spec.cut_id}.csv"
                            table.df.to_csv(run_dir / csv_filename, index=False)
                
                # Save execution summary
                run_store.save_artifact(
                    run_id,
                    "execution_summary.json",
                    json.dumps({
                        "cut_id": cut_spec.cut_id,
                        "tables_count": len(execution_result.tables),
                        "errors": execution_result.errors,
                        "segments_computed": execution_result.segments_computed
                    }, indent=2)
                )
                
                # Generate report
                run_store.generate_report(run_id, execution_result)
                
                logger.info(f"Artifacts saved to: {run_dir}")

            return PipelineResult(
                success=True,
                run_id=run_id,
                run_dir=run_dir,
                cuts_planned=[cut_spec],
                execution_result=execution_result
            )
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            
            return PipelineResult(
                success=False,
                run_id=run_id,
                run_dir=run_dir,
                errors=[str(e)]
            )

    def run_autoplan(
        self,
        save_run: bool = True,
        max_cuts: int = 20,
    ) -> PipelineResult:
        """Generate and execute a full analysis plan.

        Args:
            save_run: Whether to save run artifacts
            max_cuts: Maximum number of cuts to execute

        Returns:
            PipelineResult with execution details
        """
        # TODO: Implement the autoplan pipeline
        # 1. Initialize RunStore
        # 2. Generate high-level plan via agent
        # 3. For each intent, plan a cut
        # 4. Execute all planned cuts
        # 5. Save all artifacts and generate report
        
        # For now, return a simple implementation
        logger.warning("Auto-plan not fully implemented, running single prompt instead")
        
        # Use a default prompt for autoplan
        default_prompt = "Show key metrics and trends from the survey data"
        
        return self.run_single(default_prompt, save_run)