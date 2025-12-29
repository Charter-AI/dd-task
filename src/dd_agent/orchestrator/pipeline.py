"""Pipeline for running analysis flows."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from rich.console import Console  # 添加这一行

from dd_agent.contracts.questions import Question
from dd_agent.contracts.specs import CutSpec, HighLevelPlan, SegmentSpec
from dd_agent.contracts.tool_output import ToolOutput
from dd_agent.engine.executor import ExecutionResult
from dd_agent.orchestrator.agent import Agent
from dd_agent.run_store import RunStore
from dd_agent.util.logging import get_logger

logger = get_logger("pipeline")
"""Pipeline for running analysis flows."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from rich.console import Console

from dd_agent.contracts.questions import Question
from dd_agent.contracts.specs import CutSpec, HighLevelPlan, SegmentSpec
from dd_agent.contracts.tool_output import ToolOutput, ToolMessage
from dd_agent.engine.executor import ExecutionResult
from dd_agent.orchestrator.agent import Agent
from dd_agent.run_store import RunStore
from dd_agent.util.logging import get_logger

logger = get_logger("pipeline")

# Create global console object
console = Console()


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
        run_id = run_store.new_run(prompt)
        run_dir = run_store.run_dir
        
        logger.info(f"Starting run {run_id} with prompt: {prompt}")

        try:
            # 2. Save input files
            run_store.save_input("questions.json", self.data_dir / "questions.json")
            run_store.save_input("responses.csv", self.data_dir / "responses.csv")
            if self.scope:
                run_store.save_input_text("scope.md", self.scope)
            
            # 3. Compute dataset hash
            run_store.compute_dataset_hash(
                self.data_dir / "questions.json",
                self.data_dir / "responses.csv",
                self.data_dir / "scope.md" if (self.data_dir / "scope.md").exists() else None
            )
            
            # 4. Plan the cut via agent
            logger.info(f"Planning cut for: {prompt}")
            cut_result = self.agent.plan_cut(prompt)
            
            if not cut_result.ok:
                errors = []
                for error in cut_result.errors:
                    if isinstance(error, ToolMessage):
                        errors.append(error.message)
                    else:
                        errors.append(str(error))
                
                logger.error(f"Cut planning failed: {errors}")
                
                # Save failure result
                if save_run:
                    run_store.save_artifact("cut_planning_error.json", {
                        "prompt": prompt,
                        "errors": errors,
                        "timestamp": datetime.now().isoformat()
                    })
                    run_store.save_report(PipelineResult(
                        success=False,
                        run_id=run_id,
                        run_dir=run_dir,
                        errors=errors
                    ))
                
                return PipelineResult(
                    success=False,
                    run_id=run_id,
                    run_dir=run_dir,
                    errors=errors
                )
            
            cut_spec = cut_result.data
            logger.info(f"Cut planned successfully: {cut_spec.cut_id}")

            # 5. Execute the cut
            logger.info(f"Executing cut: {cut_spec.cut_id}")
            execution_result = self.agent.execute_single_cut(cut_spec)
            
            # 6. Save artifacts and generate report
            if save_run:
                # Save cut specification
                run_store.save_artifact("cut_spec.json", cut_spec)
                
                # Save execution results
                run_store.save_artifact("execution_result.json", execution_result)
                
                # Save individual tables as separate files
                for i, table in enumerate(execution_result.tables):
                    table_filename = f"table_{i}_{cut_spec.cut_id}.json"
                    run_store.save_artifact(table_filename, table)
                    
                    # Also save as CSV if dataframe exists
                    if hasattr(table, 'df') and table.df is not None:
                        csv_filename = f"table_{i}_{cut_spec.cut_id}.csv"
                        csv_path = run_dir / "artifacts" / csv_filename
                        table.df.to_csv(csv_path, index=False)
                
                # Generate report
                pipeline_result = PipelineResult(
                    success=True,
                    run_id=run_id,
                    run_dir=run_dir,
                    cuts_planned=[cut_spec],
                    execution_result=execution_result
                )
                run_store.save_report(pipeline_result)
                
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
            
            # Save error to artifacts
            if save_run and 'run_store' in locals():
                run_store.save_artifact("pipeline_error.json", {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
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
        # 1. Initialize RunStore
        run_store = RunStore(self.runs_dir)
        run_id = run_store.new_run("Auto-plan: Comprehensive analysis")
        run_dir = run_store.run_dir
        
        logger.info(f"Starting autoplan run {run_id}")

        try:
            # 2. Save input files
            run_store.save_input("questions.json", self.data_dir / "questions.json")
            run_store.save_input("responses.csv", self.data_dir / "responses.csv")
            if self.scope:
                run_store.save_input_text("scope.md", self.scope)
            
            # 3. Compute dataset hash
            run_store.compute_dataset_hash(
                self.data_dir / "questions.json",
                self.data_dir / "responses.csv",
                self.data_dir / "scope.md" if (self.data_dir / "scope.md").exists() else None
            )
            
            # 4. Generate high-level plan via agent
            logger.info("Generating high-level analysis plan")
            plan_result = self.agent.plan_analysis()
            
            if not plan_result.ok:
                errors = []
                for error in plan_result.errors:
                    if isinstance(error, ToolMessage):
                        errors.append(error.message)
                    else:
                        errors.append(str(error))
                
                logger.error(f"High-level planning failed: {errors}")
                
                if save_run:
                    run_store.save_artifact("planning_error.json", {
                        "errors": errors,
                        "timestamp": datetime.now().isoformat()
                    })
                    run_store.save_report(PipelineResult(
                        success=False,
                        run_id=run_id,
                        run_dir=run_dir,
                        errors=errors
                    ))
                
                return PipelineResult(
                    success=False,
                    run_id=run_id,
                    run_dir=run_dir,
                    errors=errors
                )
            
            high_level_plan = plan_result.data
            logger.info(f"High-level plan generated with {len(high_level_plan.intents)} intents")
            
            # 5. Add suggested segments to agent
            if hasattr(high_level_plan, 'suggested_segments') and high_level_plan.suggested_segments:
                for segment in high_level_plan.suggested_segments:
                    self.agent.add_segment(segment)
                    logger.info(f"Added suggested segment: {segment.name}")
            
            # 6. Plan and execute cuts for each intent
            all_cuts_planned = []
            all_cuts_failed = []
            all_execution_results = []
            
            # Sort intents by priority
            sorted_intents = sorted(
                high_level_plan.intents,
                key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.priority, 3)
            )
            
            # Limit to max_cuts
            intents_to_process = sorted_intents[:max_cuts]
            
            for i, intent in enumerate(intents_to_process):
                logger.info(f"Processing intent {i+1}/{len(intents_to_process)}: {intent.description}")
                
                try:
                    # Plan cut from intent description
                    cut_result = self.agent.plan_cut(intent.description)
                    
                    if cut_result.ok:
                        cut_spec = cut_result.data
                        all_cuts_planned.append(cut_spec)
                        
                        # Execute the cut
                        exec_result = self.agent.execute_single_cut(cut_spec)
                        all_execution_results.append(exec_result)
                        
                        logger.info(f"✓ Executed cut: {cut_spec.cut_id}")
                    else:
                        # Extract error messages from ToolMessages
                        error_messages = []
                        for error in cut_result.errors:
                            if isinstance(error, ToolMessage):
                                error_messages.append(error.message)
                            else:
                                error_messages.append(str(error))
                        
                        failed_cut = {
                            "intent_id": getattr(intent, 'intent_id', f"intent_{i}"),
                            "description": intent.description,
                            "errors": error_messages
                        }
                        all_cuts_failed.append(failed_cut)
                        logger.warning(f"✗ Failed to plan cut for intent: {intent.description}")
                        
                except Exception as e:
                    failed_cut = {
                        "intent_id": getattr(intent, 'intent_id', f"intent_{i}"),
                        "description": intent.description,
                        "error": str(e)
                    }
                    all_cuts_failed.append(failed_cut)
                    logger.error(f"Error processing intent: {e}")
            
            # 7. Combine all execution results
            combined_tables = []
            combined_errors = []
            segments_computed = {}
            
            for result in all_execution_results:
                combined_tables.extend(result.tables)
                combined_errors.extend(result.errors)
                if result.segments_computed:
                    segments_computed.update(result.segments_computed)
            
            combined_execution_result = ExecutionResult(
                tables=combined_tables,
                errors=combined_errors,
                segments_computed=segments_computed
            )
            
            # 8. Save artifacts and generate report
            if save_run:
                # Save high-level plan
                run_store.save_artifact("high_level_plan.json", high_level_plan)
                
                # Save all cut specifications
                run_store.save_artifact("all_cuts.json", all_cuts_planned)
                
                # Save failed cuts
                if all_cuts_failed:
                    run_store.save_artifact("failed_cuts.json", all_cuts_failed)
                
                # Save execution summary
                run_store.save_artifact("execution_summary.json", {
                    "total_intents": len(high_level_plan.intents),
                    "intents_processed": len(intents_to_process),
                    "cuts_planned": len(all_cuts_planned),
                    "cuts_failed": len(all_cuts_failed),
                    "tables_generated": len(combined_execution_result.tables),
                    "errors_encountered": len(combined_execution_result.errors)
                })
                
                # Save each table
                for i, table in enumerate(combined_execution_result.tables):
                    table_filename = f"table_{i}_{table.cut_id}.json"
                    run_store.save_artifact(table_filename, table)
                    
                    # Also save as CSV
                    if hasattr(table, 'df') and table.df is not None:
                        csv_filename = f"table_{i}_{table.cut_id}.csv"
                        csv_path = run_dir / "artifacts" / csv_filename
                        table.df.to_csv(csv_path, index=False)
                
                # Generate comprehensive report
                pipeline_result = PipelineResult(
                    success=len(all_cuts_planned) > 0,
                    run_id=run_id,
                    run_dir=run_dir,
                    plan=high_level_plan,
                    cuts_planned=all_cuts_planned,
                    cuts_failed=all_cuts_failed,
                    execution_result=combined_execution_result,
                    errors=[] if len(all_cuts_planned) > 0 else ["No cuts were successfully executed"]
                )
                run_store.save_report(pipeline_result)
                
                logger.info(f"Autoplan complete. Artifacts saved to: {run_dir}")
            
            return PipelineResult(
                success=len(all_cuts_planned) > 0,
                run_id=run_id,
                run_dir=run_dir,
                plan=high_level_plan,
                cuts_planned=all_cuts_planned,
                cuts_failed=all_cuts_failed,
                execution_result=combined_execution_result,
                errors=[] if len(all_cuts_planned) > 0 else ["No cuts were successfully executed"]
            )
            
        except Exception as e:
            logger.error(f"Autoplan pipeline failed: {str(e)}")
            
            if save_run and 'run_store' in locals():
                run_store.save_artifact("autoplan_error.json", {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return PipelineResult(
                success=False,
                run_id=run_id,
                run_dir=run_dir,
                errors=[str(e)]
            )
    
    def run_interactive(
        self,
        prompt: Optional[str] = None,
        save_run: bool = True,
    ) -> PipelineResult:
        """Execute an analysis request with interactive ambiguity resolution.
        
        Args:
            prompt: Optional starting prompt (if None, will prompt user)
            save_run: Whether to save run artifacts
            
        Returns:
            PipelineResult with execution details
        """
        # 1. Get prompt from user if not provided
        if not prompt:
            console = Console()
            prompt = console.input("\n🔍 [bold]Enter analysis request: [/bold]")
            if not prompt.strip():
                return PipelineResult(
                    success=False,
                    run_id="",
                    run_dir=Path("."),
                    errors=["No prompt provided"]
                )
        
        # 2. Initialize RunStore
        run_store = RunStore(self.runs_dir)
        run_id = run_store.new_run(prompt)
        run_dir = run_store.run_dir
        
        logger.info(f"Starting interactive run {run_id} with prompt: {prompt}")
        
        try:
            # 3. Plan the cut (may require user interaction)
            logger.info(f"Planning cut for: {prompt}")
            cut_result = self.agent.plan_cut(prompt)
            
            # 4. Handle ambiguity resolution
            resolution_attempts = 0
            max_resolution_attempts = 3
            
            while hasattr(cut_result, 'requires_user_input') and cut_result.requires_user_input and resolution_attempts < max_resolution_attempts:
                resolution_attempts += 1
                
                console.print("\n" + "="*60)
                console.print("[bold yellow]🤔 AMBIGUITY DETECTED[/bold yellow]")
                console.print("="*60)
                console.print(f"Your request '[cyan]{prompt}[/cyan]' could mean multiple things:")
                console.print()
                
                # Display options
                for i, option in enumerate(cut_result.user_input_options):
                    question_id = option.get("question_id", "UNKNOWN")
                    label = option.get("label", "No label")
                    match_reason = option.get("match_reason", "No reason given")
                    confidence = option.get("confidence", 0.0)
                    
                    console.print(f"[bold]{i+1}.[/bold] {label}")
                    console.print(f"   [dim]Question ID: {question_id}[/dim]")
                    console.print(f"   [dim]Match reason: {match_reason}[/dim]")
                    console.print(f"   [dim]Confidence: {confidence:.1%}[/dim]")
                    console.print()
                
                console.print(f"[bold]{len(cut_result.user_input_options)+1}.[/bold] Enter a different request")
                console.print(f"[bold]{len(cut_result.user_input_options)+2}.[/bold] Cancel analysis")
                console.print()
                
                # Get user choice
                try:
                    choice = console.input(f"Select option (1-{len(cut_result.user_input_options)+2}): ").strip()
                    choice_num = int(choice)
                    
                    if choice_num == len(cut_result.user_input_options) + 1:
                        # New request
                        prompt = console.input("Enter new analysis request: ")
                        if not prompt.strip():
                            return PipelineResult(
                                success=False,
                                run_id=run_id,
                                run_dir=run_dir,
                                errors=["No new prompt provided"]
                            )
                        cut_result = self.agent.plan_cut(prompt)
                        
                    elif choice_num == len(cut_result.user_input_options) + 2:
                        # Cancel
                        return PipelineResult(
                            success=False,
                            run_id=run_id,
                            run_dir=run_dir,
                            errors=["Analysis cancelled by user"]
                        )
                        
                    elif 1 <= choice_num <= len(cut_result.user_input_options):
                        # User selected an option
                        selected_index = choice_num - 1
                        logger.info(f"User selected option {choice_num}: {cut_result.user_input_options[selected_index].get('question_id')}")
                        
                        # Resolve with selected option
                        # First, we need to ensure agent has resolve_ambiguity_and_plan method
                        if hasattr(self.agent, 'resolve_ambiguity_and_plan'):
                            cut_result = self.agent.resolve_ambiguity_and_plan(prompt, selected_index)
                        else:
                            # Fallback: create modified prompt with selection
                            selected_question_id = cut_result.user_input_options[selected_index].get('question_id')
                            modified_prompt = f"{prompt} (use question: {selected_question_id})"
                            cut_result = self.agent.plan_cut(modified_prompt)
                        
                    else:
                        console.print(f"[red]Invalid choice. Please enter 1-{len(cut_result.user_input_options)+2}[/red]")
                        continue
                        
                except ValueError:
                    console.print("[red]Please enter a number[/red]")
                    continue
                
                except Exception as e:
                    logger.error(f"Error during user interaction: {e}")
                    return PipelineResult(
                        success=False,
                        run_id=run_id,
                        run_dir=run_dir,
                        errors=[f"Interaction error: {str(e)}"]
                    )
            
            # 5. Check if we still have ambiguity after attempts
            if hasattr(cut_result, 'requires_user_input') and cut_result.requires_user_input:
                console.print("\n[bold yellow]⚠️  Too many resolution attempts. Using highest confidence option.[/bold yellow]")
                # Use first (highest confidence) option
                if hasattr(self.agent, 'resolve_ambiguity_and_plan'):
                    cut_result = self.agent.resolve_ambiguity_and_plan(prompt, 0)
                else:
                    selected_question_id = cut_result.user_input_options[0].get('question_id')
                    modified_prompt = f"{prompt} (use question: {selected_question_id})"
                    cut_result = self.agent.plan_cut(modified_prompt)
            
            # 6. Process the final cut result
            if not cut_result.ok:
                errors = []
                for error in cut_result.errors:
                    if isinstance(error, ToolMessage):
                        errors.append(error.message)
                    else:
                        errors.append(str(error))
                
                logger.error(f"Cut planning failed: {errors}")
                
                if save_run:
                    run_store.save_artifact("cut_planning_error.json", {
                        "prompt": prompt,
                        "errors": errors,
                        "interactive": True,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return PipelineResult(
                    success=False,
                    run_id=run_id,
                    run_dir=run_dir,
                    errors=errors
                )
            
            cut_spec = cut_result.data
            logger.info(f"Cut planned successfully: {cut_spec.cut_id}")

            # 7. Execute the cut
            logger.info(f"Executing cut: {cut_spec.cut_id}")
            execution_result = self.agent.execute_single_cut(cut_spec)
            
            # 8. Save artifacts and generate report
            if save_run:
                # Save input files
                run_store.save_input("questions.json", self.data_dir / "questions.json")
                run_store.save_input("responses.csv", self.data_dir / "responses.csv")
                if self.scope:
                    run_store.save_input_text("scope.md", self.scope)
                
                # Compute dataset hash
                run_store.compute_dataset_hash(
                    self.data_dir / "questions.json",
                    self.data_dir / "responses.csv",
                    self.data_dir / "scope.md" if (self.data_dir / "scope.md").exists() else None
                )
                
                # Save cut specification
                run_store.save_artifact("cut_spec.json", cut_spec)
                
                # Save execution results
                run_store.save_artifact("execution_result.json", execution_result)
                
                # Save interaction trace
                if hasattr(cut_result, 'trace') and cut_result.trace:
                    run_store.save_artifact("interaction_trace.json", {
                        "original_prompt": prompt,
                        "resolution_attempts": resolution_attempts,
                        "final_cut_id": cut_spec.cut_id,
                        "trace": cut_result.trace
                    })
                
                # Save individual tables
                for i, table in enumerate(execution_result.tables):
                    table_filename = f"table_{i}_{cut_spec.cut_id}.json"
                    run_store.save_artifact(table_filename, table)
                    
                    if hasattr(table, 'df') and table.df is not None:
                        csv_filename = f"table_{i}_{cut_spec.cut_id}.csv"
                        csv_path = run_dir / "artifacts" / csv_filename
                        table.df.to_csv(csv_path, index=False)
                
                # Generate report
                pipeline_result = PipelineResult(
                    success=True,
                    run_id=run_id,
                    run_dir=run_dir,
                    cuts_planned=[cut_spec],
                    execution_result=execution_result
                )
                run_store.save_report(pipeline_result)
                
                logger.info(f"Artifacts saved to: {run_dir}")

            return PipelineResult(
                success=True,
                run_id=run_id,
                run_dir=run_dir,
                cuts_planned=[cut_spec],
                execution_result=execution_result
            )
            
        except Exception as e:
            logger.error(f"Interactive pipeline execution failed: {str(e)}")
            
            if save_run and 'run_store' in locals():
                run_store.save_artifact("interactive_error.json", {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return PipelineResult(
                success=False,
                run_id=run_id,
                run_dir=run_dir,
                errors=[str(e)]
            )
# 创建全局console对象
console = Console()


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
        run_id = run_store.new_run(prompt)  # FIXED: new_run() not create_run()
        run_dir = run_store.run_dir  # FIXED: Use run_store.run_dir
        
        logger.info(f"Starting run {run_id} with prompt: {prompt}")

        try:
            # 2. Save input files
            run_store.save_input("questions.json", self.data_dir / "questions.json")
            run_store.save_input("responses.csv", self.data_dir / "responses.csv")
            if self.scope:
                run_store.save_input_text("scope.md", self.scope)
            
            # 3. Compute dataset hash
            run_store.compute_dataset_hash(
                self.data_dir / "questions.json",
                self.data_dir / "responses.csv",
                self.data_dir / "scope.md" if (self.data_dir / "scope.md").exists() else None
            )
            
            # 4. Plan the cut via agent
            logger.info(f"Planning cut for: {prompt}")
            cut_result = self.agent.plan_cut(prompt)
            
            if not cut_result.ok:
                errors = [str(e) for e in cut_result.errors]
                logger.error(f"Cut planning failed: {errors}")
                
                # Save failure result
                if save_run:
                    run_store.save_artifact("cut_planning_error.json", {
                        "prompt": prompt,
                        "errors": errors,
                        "timestamp": datetime.now().isoformat()
                    })
                    run_store.save_report(PipelineResult(
                        success=False,
                        run_id=run_id,
                        run_dir=run_dir,
                        errors=errors
                    ))
                
                return PipelineResult(
                    success=False,
                    run_id=run_id,
                    run_dir=run_dir,
                    errors=errors
                )
            
            cut_spec = cut_result.data
            logger.info(f"Cut planned successfully: {cut_spec.cut_id}")

            # 5. Execute the cut
            logger.info(f"Executing cut: {cut_spec.cut_id}")
            execution_result = self.agent.execute_single_cut(cut_spec)
            
            # 6. Save artifacts and generate report
            if save_run:
                # Save cut specification
                run_store.save_artifact("cut_spec.json", cut_spec)
                
                # Save execution results
                run_store.save_artifact("execution_result.json", execution_result)
                
                # Save individual tables as separate files
                for i, table in enumerate(execution_result.tables):
                    table_filename = f"table_{i}_{cut_spec.cut_id}.json"
                    run_store.save_artifact(table_filename, table)
                    
                    # Also save as CSV if dataframe exists
                    if hasattr(table, 'df') and table.df is not None:
                        csv_filename = f"table_{i}_{cut_spec.cut_id}.csv"
                        table.df.to_csv(run_dir / "artifacts" / csv_filename, index=False)
                
                # Generate report
                pipeline_result = PipelineResult(
                    success=True,
                    run_id=run_id,
                    run_dir=run_dir,
                    cuts_planned=[cut_spec],
                    execution_result=execution_result
                )
                run_store.save_report(pipeline_result)
                
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
            
            # Save error to artifacts
            if save_run and 'run_store' in locals():
                run_store.save_artifact("pipeline_error.json", {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
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
        # 1. Initialize RunStore
        run_store = RunStore(self.runs_dir)
        run_id = run_store.new_run("Auto-plan: Comprehensive analysis")
        run_dir = run_store.run_dir
        
        logger.info(f"Starting autoplan run {run_id}")

        try:
            # 2. Save input files
            run_store.save_input("questions.json", self.data_dir / "questions.json")
            run_store.save_input("responses.csv", self.data_dir / "responses.csv")
            if self.scope:
                run_store.save_input_text("scope.md", self.scope)
            
            # 3. Compute dataset hash
            run_store.compute_dataset_hash(
                self.data_dir / "questions.json",
                self.data_dir / "responses.csv",
                self.data_dir / "scope.md" if (self.data_dir / "scope.md").exists() else None
            )
            
            # 4. Generate high-level plan via agent
            logger.info("Generating high-level analysis plan")
            plan_result = self.agent.plan_analysis()
            
            if not plan_result.ok:
                errors = [str(e) for e in plan_result.errors]
                logger.error(f"High-level planning failed: {errors}")
                
                if save_run:
                    run_store.save_artifact("planning_error.json", {
                        "errors": errors,
                        "timestamp": datetime.now().isoformat()
                    })
                    run_store.save_report(PipelineResult(
                        success=False,
                        run_id=run_id,
                        run_dir=run_dir,
                        errors=errors
                    ))
                
                return PipelineResult(
                    success=False,
                    run_id=run_id,
                    run_dir=run_dir,
                    errors=errors
                )
            
            high_level_plan = plan_result.data
            logger.info(f"High-level plan generated with {len(high_level_plan.intents)} intents")
            
            # 5. Add suggested segments to agent
            if hasattr(high_level_plan, 'suggested_segments') and high_level_plan.suggested_segments:
                for segment in high_level_plan.suggested_segments:
                    self.agent.add_segment(segment)
                    logger.info(f"Added suggested segment: {segment.name}")
            
            # 6. Plan and execute cuts for each intent
            all_cuts_planned = []
            all_cuts_failed = []
            all_execution_results = []
            
            # Sort intents by priority
            sorted_intents = sorted(
                high_level_plan.intents,
                key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.priority, 3)
            )
            
            # Limit to max_cuts
            intents_to_process = sorted_intents[:max_cuts]
            
            for i, intent in enumerate(intents_to_process):
                logger.info(f"Processing intent {i+1}/{len(intents_to_process)}: {intent.description}")
                
                try:
                    # Plan cut from intent description
                    cut_result = self.agent.plan_cut(intent.description)
                    
                    if cut_result.ok:
                        cut_spec = cut_result.data
                        all_cuts_planned.append(cut_spec)
                        
                        # Execute the cut
                        exec_result = self.agent.execute_single_cut(cut_spec)
                        all_execution_results.append(exec_result)
                        
                        logger.info(f"✓ Executed cut: {cut_spec.cut_id}")
                    else:
                        failed_cut = {
                            "intent_id": getattr(intent, 'intent_id', f"intent_{i}"),
                            "description": intent.description,
                            "errors": [str(e) for e in cut_result.errors]
                        }
                        all_cuts_failed.append(failed_cut)
                        logger.warning(f"✗ Failed to plan cut for intent: {intent.description}")
                        
                except Exception as e:
                    failed_cut = {
                        "intent_id": getattr(intent, 'intent_id', f"intent_{i}"),
                        "description": intent.description,
                        "error": str(e)
                    }
                    all_cuts_failed.append(failed_cut)
                    logger.error(f"Error processing intent: {e}")
            
            # 7. Combine all execution results
            combined_tables = []
            combined_errors = []
            segments_computed = {}
            
            for result in all_execution_results:
                combined_tables.extend(result.tables)
                combined_errors.extend(result.errors)
                if result.segments_computed:
                    segments_computed.update(result.segments_computed)
            
            combined_execution_result = ExecutionResult(
                tables=combined_tables,
                errors=combined_errors,
                segments_computed=segments_computed
            )
            
            # 8. Save artifacts and generate report
            if save_run:
                # Save high-level plan
                run_store.save_artifact("high_level_plan.json", high_level_plan)
                
                # Save all cut specifications
                run_store.save_artifact("all_cuts.json", all_cuts_planned)
                
                # Save failed cuts
                if all_cuts_failed:
                    run_store.save_artifact("failed_cuts.json", all_cuts_failed)
                
                # Save execution summary
                run_store.save_artifact("execution_summary.json", {
                    "total_intents": len(high_level_plan.intents),
                    "intents_processed": len(intents_to_process),
                    "cuts_planned": len(all_cuts_planned),
                    "cuts_failed": len(all_cuts_failed),
                    "tables_generated": len(combined_execution_result.tables),
                    "errors_encountered": len(combined_execution_result.errors)
                })
                
                # Save each table
                for i, table in enumerate(combined_execution_result.tables):
                    table_filename = f"table_{i}_{table.cut_id}.json"
                    run_store.save_artifact(table_filename, table)
                    
                    # Also save as CSV
                    if hasattr(table, 'df') and table.df is not None:
                        csv_filename = f"table_{i}_{table.cut_id}.csv"
                        table.df.to_csv(run_dir / "artifacts" / csv_filename, index=False)
                
                # Generate comprehensive report
                pipeline_result = PipelineResult(
                    success=len(all_cuts_planned) > 0,
                    run_id=run_id,
                    run_dir=run_dir,
                    plan=high_level_plan,
                    cuts_planned=all_cuts_planned,
                    cuts_failed=all_cuts_failed,
                    execution_result=combined_execution_result,
                    errors=[] if len(all_cuts_planned) > 0 else ["No cuts were successfully executed"]
                )
                run_store.save_report(pipeline_result)
                
                logger.info(f"Autoplan complete. Artifacts saved to: {run_dir}")
            
            return PipelineResult(
                success=len(all_cuts_planned) > 0,
                run_id=run_id,
                run_dir=run_dir,
                plan=high_level_plan,
                cuts_planned=all_cuts_planned,
                cuts_failed=all_cuts_failed,
                execution_result=combined_execution_result,
                errors=[] if len(all_cuts_planned) > 0 else ["No cuts were successfully executed"]
            )
            
        except Exception as e:
            logger.error(f"Autoplan pipeline failed: {str(e)}")
            
            if save_run and 'run_store' in locals():
                run_store.save_artifact("autoplan_error.json", {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            return PipelineResult(
                success=False,
                run_id=run_id,
                run_dir=run_dir,
                errors=[str(e)]
            )
    
    def run_interactive(
            self,
            prompt: Optional[str] = None,
            save_run: bool = True,
        ) -> PipelineResult:
            """Execute an analysis request with interactive ambiguity resolution.
            
            Args:
                prompt: Optional starting prompt (if None, will prompt user)
                save_run: Whether to save run artifacts
                
            Returns:
                PipelineResult with execution details
            """
            # 1. Get prompt from user if not provided
            if not prompt:
                console = Console()
                prompt = console.input("\n🔍 [bold]Enter analysis request: [/bold]")
                if not prompt.strip():
                    return PipelineResult(
                        success=False,
                        run_id="",
                        run_dir=Path("."),
                        errors=["No prompt provided"]
                    )
            
            # 2. Initialize RunStore
            run_store = RunStore(self.runs_dir)
            run_id = run_store.new_run(prompt)
            run_dir = run_store.run_dir
            
            logger.info(f"Starting interactive run {run_id} with prompt: {prompt}")
            
            try:
                # 3. Plan the cut (may require user interaction)
                logger.info(f"Planning cut for: {prompt}")
                cut_result = self.agent.plan_cut(prompt)
                
                # 4. Handle ambiguity resolution
                resolution_attempts = 0
                max_resolution_attempts = 3
                
                while hasattr(cut_result, 'requires_user_input') and cut_result.requires_user_input and resolution_attempts < max_resolution_attempts:
                    resolution_attempts += 1
                    
                    console = Console()
                    console.print("\n" + "="*60)
                    console.print("[bold yellow]🤔 AMBIGUITY DETECTED[/bold yellow]")
                    console.print("="*60)
                    console.print(f"Your request '[cyan]{prompt}[/cyan]' could mean multiple things:")
                    console.print()
                    
                    # Display options
                    for i, option in enumerate(cut_result.user_input_options):
                        question_id = option.get("question_id", "UNKNOWN")
                        label = option.get("label", "No label")
                        match_reason = option.get("match_reason", "No reason given")
                        confidence = option.get("confidence", 0.0)
                        
                        console.print(f"[bold]{i+1}.[/bold] {label}")
                        console.print(f"   [dim]Question ID: {question_id}[/dim]")
                        console.print(f"   [dim]Match reason: {match_reason}[/dim]")
                        console.print(f"   [dim]Confidence: {confidence:.1%}[/dim]")
                        console.print()
                    
                    console.print(f"[bold]{len(cut_result.user_input_options)+1}.[/bold] Enter a different request")
                    console.print(f"[bold]{len(cut_result.user_input_options)+2}.[/bold] Cancel analysis")
                    console.print()
                    
                    # Get user choice
                    try:
                        choice = console.input(f"Select option (1-{len(cut_result.user_input_options)+2}): ").strip()
                        choice_num = int(choice)
                        
                        if choice_num == len(cut_result.user_input_options) + 1:
                            # New request
                            prompt = console.input("Enter new analysis request: ")
                            if not prompt.strip():
                                return PipelineResult(
                                    success=False,
                                    run_id=run_id,
                                    run_dir=run_dir,
                                    errors=["No new prompt provided"]
                                )
                            cut_result = self.agent.plan_cut(prompt)
                            
                        elif choice_num == len(cut_result.user_input_options) + 2:
                            # Cancel
                            return PipelineResult(
                                success=False,
                                run_id=run_id,
                                run_dir=run_dir,
                                errors=["Analysis cancelled by user"]
                            )
                            
                        elif 1 <= choice_num <= len(cut_result.user_input_options):
                            # User selected an option
                            selected_index = choice_num - 1
                            logger.info(f"User selected option {choice_num}: {cut_result.user_input_options[selected_index].get('question_id')}")
                            
                            # Resolve with selected option
                            # First, we need to ensure agent has resolve_ambiguity_and_plan method
                            if hasattr(self.agent, 'resolve_ambiguity_and_plan'):
                                cut_result = self.agent.resolve_ambiguity_and_plan(prompt, selected_index)
                            else:
                                # Fallback: create modified prompt with selection
                                selected_question_id = cut_result.user_input_options[selected_index].get('question_id')
                                modified_prompt = f"{prompt} (use question: {selected_question_id})"
                                cut_result = self.agent.plan_cut(modified_prompt)
                            
                        else:
                            console.print(f"[red]Invalid choice. Please enter 1-{len(cut_result.user_input_options)+2}[/red]")
                            continue
                            
                    except ValueError:
                        console.print("[red]Please enter a number[/red]")
                        continue
                    
                    except Exception as e:
                        logger.error(f"Error during user interaction: {e}")
                        return PipelineResult(
                            success=False,
                            run_id=run_id,
                            run_dir=run_dir,
                            errors=[f"Interaction error: {str(e)}"]
                        )
                
                # 5. Check if we still have ambiguity after attempts
                if hasattr(cut_result, 'requires_user_input') and cut_result.requires_user_input:
                    console.print("\n[bold yellow]⚠️  Too many resolution attempts. Using highest confidence option.[/bold yellow]")
                    # Use first (highest confidence) option
                    if hasattr(self.agent, 'resolve_ambiguity_and_plan'):
                        cut_result = self.agent.resolve_ambiguity_and_plan(prompt, 0)
                    else:
                        selected_question_id = cut_result.user_input_options[0].get('question_id')
                        modified_prompt = f"{prompt} (use question: {selected_question_id})"
                        cut_result = self.agent.plan_cut(modified_prompt)
                
                # 6. Process the final cut result
                if not cut_result.ok:
                    errors = [str(e) for e in cut_result.errors]
                    logger.error(f"Cut planning failed: {errors}")
                    
                    if save_run:
                        run_store.save_artifact("cut_planning_error.json", {
                            "prompt": prompt,
                            "errors": errors,
                            "interactive": True,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    return PipelineResult(
                        success=False,
                        run_id=run_id,
                        run_dir=run_dir,
                        errors=errors
                    )
                
                cut_spec = cut_result.data
                logger.info(f"Cut planned successfully: {cut_spec.cut_id}")

                # 7. Execute the cut
                logger.info(f"Executing cut: {cut_spec.cut_id}")
                execution_result = self.agent.execute_single_cut(cut_spec)
                
                # 8. Save artifacts and generate report
                if save_run:
                    # Save input files
                    run_store.save_input("questions.json", self.data_dir / "questions.json")
                    run_store.save_input("responses.csv", self.data_dir / "responses.csv")
                    if self.scope:
                        run_store.save_input_text("scope.md", self.scope)
                    
                    # Compute dataset hash
                    run_store.compute_dataset_hash(
                        self.data_dir / "questions.json",
                        self.data_dir / "responses.csv",
                        self.data_dir / "scope.md" if (self.data_dir / "scope.md").exists() else None
                    )
                    
                    # Save cut specification
                    run_store.save_artifact("cut_spec.json", cut_spec)
                    
                    # Save execution results
                    run_store.save_artifact("execution_result.json", execution_result)
                    
                    # Save interaction trace
                    if hasattr(cut_result, 'trace') and cut_result.trace:
                        run_store.save_artifact("interaction_trace.json", {
                            "original_prompt": prompt,
                            "resolution_attempts": resolution_attempts,
                            "final_cut_id": cut_spec.cut_id,
                            "trace": cut_result.trace
                        })
                    
                    # Save individual tables
                    for i, table in enumerate(execution_result.tables):
                        table_filename = f"table_{i}_{cut_spec.cut_id}.json"
                        run_store.save_artifact(table_filename, table)
                        
                        if hasattr(table, 'df') and table.df is not None:
                            csv_filename = f"table_{i}_{cut_spec.cut_id}.csv"
                            table.df.to_csv(run_dir / "artifacts" / csv_filename, index=False)
                    
                    # Generate report
                    pipeline_result = PipelineResult(
                        success=True,
                        run_id=run_id,
                        run_dir=run_dir,
                        cuts_planned=[cut_spec],
                        execution_result=execution_result
                    )
                    run_store.save_report(pipeline_result)
                    
                    logger.info(f"Artifacts saved to: {run_dir}")

                return PipelineResult(
                    success=True,
                    run_id=run_id,
                    run_dir=run_dir,
                    cuts_planned=[cut_spec],
                    execution_result=execution_result
                )
                
            except Exception as e:
                logger.error(f"Interactive pipeline execution failed: {str(e)}")
                
                if save_run and 'run_store' in locals():
                    run_store.save_artifact("interactive_error.json", {
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                
                return PipelineResult(
                    success=False,
                    run_id=run_id,
                    run_dir=run_dir,
                    errors=[str(e)]
                )