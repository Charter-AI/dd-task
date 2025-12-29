"""Deterministic execution engine for analysis cuts."""

from typing import Any, Optional
import pandas as pd
from pydantic import BaseModel, Field

from dd_agent.contracts.filters import FilterExpr
from dd_agent.contracts.questions import Question, QuestionType
from dd_agent.contracts.specs import CutSpec, DimensionSpec, SegmentSpec
from dd_agent.engine.masks import build_mask
from dd_agent.engine.metrics import (
    compute_bottom2box,
    compute_frequency,
    compute_mean,
    compute_multi_choice_frequency,
    compute_nps,
    compute_top2box,
)
from dd_agent.engine.tables import TableResult, add_base_size_warnings


class ExecutionResult(BaseModel):
    """Result of executing all cuts."""

    tables: list[TableResult] = Field(
        default_factory=list, description="Results for each cut"
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list, description="Errors encountered during execution"
    )
    segments_computed: dict[str, int] = Field(
        default_factory=dict, description="Base sizes for each segment"
    )


class Executor:
    """Deterministic execution engine for analysis cuts.

    This class executes validated cut specifications against a responses
    DataFrame, computing metrics and cross-tabulations.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        questions_by_id: dict[str, Question],
        segments_by_id: Optional[dict[str, SegmentSpec]] = None,
        min_base_size: int = 30,
        warn_base_size: int = 100,
    ):
        """Initialize the executor.

        Args:
            df: The responses DataFrame
            questions_by_id: Question catalog
            segments_by_id: Segment definitions (optional)
            min_base_size: Minimum base size threshold
            warn_base_size: Warning base size threshold
        """
        self.df = df
        self.questions_by_id = questions_by_id
        self.segments_by_id = segments_by_id or {}
        self.min_base_size = min_base_size
        self.warn_base_size = warn_base_size

        # Pre-computed segment masks
        self._segment_masks: dict[str, pd.Series] = {}
        self._segments_materialized = False
        
        # Materialize segments on first use, not in init
        # This avoids wasting computation if no cuts use segments

    def materialize_segments(self) -> dict[str, int]:
        """Pre-compute masks for all segments."""
        if self._segments_materialized:
            # Return cached base sizes
            return {seg_id: int(mask.sum()) for seg_id, mask in self._segment_masks.items()}
        
        segment_bases = {}
        
        for seg_id, segment_spec in self.segments_by_id.items():
            # Build mask on the full DataFrame
            mask = build_mask(self.df, segment_spec.definition, self.questions_by_id)
            self._segment_masks[seg_id] = mask
            
            # Calculate base size
            segment_bases[seg_id] = int(mask.sum())
            
            # Also compute complement mask for dimension comparisons
            complement_id = f"not_{seg_id}"
            self._segment_masks[complement_id] = ~mask
            segment_bases[complement_id] = int((~mask).sum())
        
        self._segments_materialized = True
        return segment_bases

    def execute_cuts(self, cuts: list[CutSpec]) -> ExecutionResult:
        """Execute all cuts and return results.

        Args:
            cuts: List of validated cut specifications

        Returns:
            ExecutionResult with tables and any errors
        """
        result = ExecutionResult()

        for cut in cuts:
            try:
                table_result = self._execute_single_cut(cut)
                result.tables.append(table_result)
            except Exception as e:
                result.errors.append({
                    "cut_id": cut.cut_id,
                    "error": str(e),
                    "type": type(e).__name__,
                })

        return result

    def _execute_single_cut(self, cut: CutSpec) -> TableResult:
        """Execute a single cut specification.

        Args:
            cut: The cut specification to execute

        Returns:
            TableResult with computed metrics
        """
        # Start with all rows
        mask = pd.Series(True, index=self.df.index)

        # Apply cut filter if present
        if cut.filter is not None:
            if isinstance(cut.filter, str):
                # String could be a segment ID
                if cut.filter in self.segments_by_id:
                    # Materialize segments if needed
                    if not self._segments_materialized:
                        self.materialize_segments()
                    
                    # Use pre-computed mask
                    if cut.filter in self._segment_masks:
                        mask = self._segment_masks[cut.filter]
                    else:
                        # Compute dynamically
                        mask = build_mask(self.df, 
                                         self.segments_by_id[cut.filter].definition,
                                         self.questions_by_id)
                else:
                    # Try to treat as a simple column filter
                    # Example: "Q1 == 'value'"
                    try:
                        # Evaluate the filter expression
                        filtered_mask = self.df.eval(cut.filter)
                        mask = mask & filtered_mask
                    except:
                        raise ValueError(f"Could not parse filter string: {cut.filter}")
            else:
                # Regular filter expression
                filter_mask = build_mask(self.df, cut.filter, self.questions_by_id)
                mask = mask & filter_mask

        # Get the filtered DataFrame
        filtered_df = self.df[mask].copy()

        # Get the question for the metric
        question = self.questions_by_id.get(cut.metric.question_id)
        col_name = cut.metric.question_id
        if question is not None:
            col_name = question.effective_column_name

        # Check if column exists
        if col_name not in filtered_df.columns:
            raise ValueError(f"Column '{col_name}' not found in DataFrame")

        # Execute based on dimensions
        if not cut.dimensions:
            # Simple metric (no cross-tabulation)
            return self._compute_metric_simple(cut, filtered_df, question, col_name)
        else:
            # Cross-tabulated metric
            return self._compute_metric_with_dimensions(
                cut, filtered_df, question, col_name, mask
            )

    def _compute_metric_simple(
        self,
        cut: CutSpec,
        df: pd.DataFrame,
        question: Optional[Question],
        col_name: str,
    ) -> TableResult:
        """Compute a simple metric without dimensions."""
        series = df[col_name]
        base_n = int(series.notna().sum())
        warnings = add_base_size_warnings(base_n, self.min_base_size, self.warn_base_size)

        metric_type = cut.metric.type
        result_data: dict[str, Any] = {}

        if metric_type == "frequency":
            # Check for multi-choice
            if question is not None and question.type == QuestionType.multi_choice:
                freq_df = compute_multi_choice_frequency(series, question)
            else:
                freq_df = compute_frequency(series, question)

            result_data = {
                "distribution": freq_df.to_dict(orient="records"),
            }

        elif metric_type == "mean":
            result_data = compute_mean(series)

        elif metric_type == "top2box":
            top_values = cut.metric.params.get("top_values")
            result_data = compute_top2box(series, question, top_values)

        elif metric_type == "bottom2box":
            bottom_values = cut.metric.params.get("bottom_values")
            result_data = compute_bottom2box(series, question, bottom_values)

        elif metric_type == "nps":
            promoter_min = cut.metric.params.get("promoter_min", 9)
            detractor_max = cut.metric.params.get("detractor_max", 6)
            result_data = compute_nps(series, promoter_min, detractor_max)

        else:
            raise ValueError(f"Unknown metric type: {metric_type}")

        result = TableResult(
            cut_id=cut.cut_id,
            metric_type=metric_type,
            question_id=cut.metric.question_id,
            result_data=result_data,
            base_n=base_n,
            warnings=warnings,
        )
        
        # Set the internal dataframe representation
        if metric_type == "frequency" and "distribution" in result_data:
            result.set_dataframe(pd.DataFrame(result_data["distribution"]))
        else:
            result.set_dataframe(pd.DataFrame([result_data]))
            
        return result

    def _compute_metric_with_dimensions(
        self,
        cut: CutSpec,
        df: pd.DataFrame,
        question: Optional[Question],
        col_name: str,
        base_mask: pd.Series,
    ) -> TableResult:
        """Compute a metric with dimension cross-tabulation."""
        # For now, support single dimension
        # (multi-dimension cross-tabs are more complex)
        if len(cut.dimensions) > 1:
            # Fall back to first dimension only with a warning
            dim = cut.dimensions[0]
            extra_dims = [d.id for d in cut.dimensions[1:]]
            warnings = [
                f"Multi-dimension cross-tabs not fully supported. "
                f"Using first dimension only. Ignored: {extra_dims}"
            ]
        else:
            dim = cut.dimensions[0]
            warnings = []

        # Get dimension values
        if dim.kind == "question":
            # Question dimension
            dim_question = self.questions_by_id.get(dim.id)
            if dim_question is None:
                raise ValueError(f"Dimension question '{dim.id}' not found")
            dim_col = dim_question.effective_column_name
            if dim_col not in df.columns:
                raise ValueError(f"Dimension column '{dim_col}' not found")
            groups = df.groupby(dim_col)
            
        elif dim.kind == "segment":
            # Segment dimension - handle specially
            # Materialize segments if needed
            if not self._segments_materialized:
                self.materialize_segments()
            
            if dim.id in self._segment_masks:
                # Use pre-computed mask, but align it with the filtered dataframe
                full_mask = self._segment_masks[dim.id]
                # Apply the base filter mask to get correct subset
                segment_mask = full_mask[base_mask.index].fillna(False)
                
                groups = {
                    f"{dim.id}": df[segment_mask],
                    f"not_{dim.id}": df[~segment_mask],
                }
            elif dim.id in self.segments_by_id:
                # Compute mask on full df, then apply to filtered df
                full_mask = build_mask(self.df, self.segments_by_id[dim.id].definition, self.questions_by_id)
                segment_mask = full_mask[base_mask.index].fillna(False)
                
                groups = {
                    f"{dim.id}": df[segment_mask],
                    f"not_{dim.id}": df[~segment_mask],
                }
            else:
                raise ValueError(f"Segment dimension '{dim.id}' not found")
        else:
            raise ValueError(f"Unknown dimension kind: {dim.kind}")

        # Compute metric for each group
        result_by_group: dict[str, Any] = {}
        base_sizes: dict[str, int] = {}

        if isinstance(groups, pd.core.groupby.DataFrameGroupBy):
            # Question dimension groups
            for group_val, group_df in groups:
                if group_df.empty:
                    result_by_group[str(group_val)] = None
                    base_sizes[str(group_val)] = 0
                    continue
                    
                series = group_df[col_name]
                base_n = int(series.notna().sum())
                base_sizes[str(group_val)] = base_n

                group_warnings = add_base_size_warnings(
                    base_n, self.min_base_size, self.warn_base_size
                )
                if group_warnings:
                    warnings.extend(
                        [f"[{group_val}] {w}" for w in group_warnings]
                    )

                result_by_group[str(group_val)] = self._compute_metric_value(
                    cut.metric.type, series, question, cut.metric.params
                )
        else:
            # Dict-based groups (for segments or custom groupings)
            for group_val, group_df in groups.items():
                if group_df.empty:
                    result_by_group[group_val] = None
                    base_sizes[group_val] = 0
                    continue
                    
                series = group_df[col_name]
                base_n = int(series.notna().sum())
                base_sizes[group_val] = base_n

                group_warnings = add_base_size_warnings(
                    base_n, self.min_base_size, self.warn_base_size
                )
                if group_warnings:
                    warnings.extend([f"[{group_val}] {w}" for w in group_warnings])

                result_by_group[group_val] = self._compute_metric_value(
                    cut.metric.type, series, question, cut.metric.params
                )

        total_base = sum(base_sizes.values())

        result_data = {
            "by_dimension": result_by_group,
            "base_sizes": base_sizes,
        }

        result = TableResult(
            cut_id=cut.cut_id,
            metric_type=cut.metric.type,
            question_id=cut.metric.question_id,
            result_data=result_data,
            base_n=total_base,
            dimensions=[f"{dim.kind}:{dim.id}"],
            warnings=warnings,
        )
        
        # Set the internal dataframe representation
        # For cross-tabs, we can flatten this into a more useful format
        df_rows = []
        for dim_val, val in result_by_group.items():
            row = {
                "dimension": dim.id,
                "value": dim_val,
                "metric": val,
                "base_n": base_sizes.get(dim_val, 0)
            }
            df_rows.append(row)
        result.set_dataframe(pd.DataFrame(df_rows))
        
        return result

    def _compute_metric_value(
        self,
        metric_type: str,
        series: pd.Series,
        question: Optional[Question],
        params: dict,
    ) -> Any:
        """Compute a single metric value for a group."""
        if series.empty:
            # Handle empty groups gracefully
            if metric_type in ["mean", "nps", "top2box", "bottom2box"]:
                return None
            elif metric_type == "frequency":
                return []
        
        try:
            if metric_type == "frequency":
                if question is not None and question.type == QuestionType.multi_choice:
                    freq_df = compute_multi_choice_frequency(series, question)
                else:
                    freq_df = compute_frequency(series, question)
                return freq_df.to_dict(orient="records")

            elif metric_type == "mean":
                result = compute_mean(series)
                return result.get("mean")

            elif metric_type == "top2box":
                result = compute_top2box(series, question, params.get("top_values"))
                return result.get("top2box_pct")

            elif metric_type == "bottom2box":
                result = compute_bottom2box(series, question, params.get("bottom_values"))
                return result.get("bottom2box_pct")

            elif metric_type == "nps":
                result = compute_nps(
                    series,
                    params.get("promoter_min", 9),
                    params.get("detractor_max", 6),
                )
                return result.get("nps")

            else:
                raise ValueError(f"Unknown metric type: {metric_type}")
        except Exception as e:
            # Gracefully handle computation errors
            return None