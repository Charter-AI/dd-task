"""Table result models and utilities."""

from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel, Field


class TableResult(BaseModel):
    """Result of executing a single cut."""

    model_config = {"arbitrary_types_allowed": True}

    cut_id: str = Field(..., description="ID of the cut that produced this result")
    metric_type: str = Field(..., description="Type of metric computed")
    question_id: str = Field(..., description="Question the metric was computed on")

    # Result data - stored as dict for serialization
    result_data: dict[str, Any] = Field(
        ..., description="The computed result (structure depends on metric type)"
    )

    # Metadata
    base_n: int = Field(..., description="Base size (number of valid responses)")
    dimensions: list[str] = Field(
        default_factory=list, description="Dimensions used in cross-tabulation"
    )

    # Warnings
    warnings: list[str] = Field(
        default_factory=list, description="Any warnings generated during execution"
    )

    # Optional DataFrame for complex results (not serialized to JSON)
    _df: Optional[pd.DataFrame] = None

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Store the result DataFrame."""
        object.__setattr__(self, "_df", df)

    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """Get the result DataFrame if available."""
        return getattr(self, "_df", None)

    def to_csv(self) -> str:
        """Convert result to CSV string."""
        df = self.get_dataframe()
        if df is not None:
            return df.to_csv(index=False)

        # Try to convert result_data to DataFrame
        if isinstance(self.result_data, dict):
            if "distribution" in self.result_data:
                df = pd.DataFrame(self.result_data["distribution"])
                return df.to_csv(index=False)

        return ""


class CrossTabResult(BaseModel):
    """Result of a cross-tabulation (metric by dimensions)."""

    model_config = {"arbitrary_types_allowed": True}

    cut_id: str = Field(..., description="ID of the cut")
    metric_type: str = Field(..., description="Type of metric")

    # Structure: nested dict by dimension values
    # e.g., {"Male": {"18-24": 0.45, "25-34": 0.52}, "Female": {...}}
    data: dict[str, Any] = Field(..., description="Cross-tabulated results")

    # Base sizes by group
    base_sizes: dict[str, int] = Field(
        default_factory=dict, description="Base size for each group"
    )

    # Dimension info
    row_dimension: Optional[str] = Field(
        default=None, description="Row dimension ID"
    )
    col_dimension: Optional[str] = Field(
        default=None, description="Column dimension ID"
    )

    warnings: list[str] = Field(default_factory=list)


def add_base_size_warnings(
    base_n: int,
    min_base: int = 30,
    warn_base: int = 100,
) -> list[str]:
    """Generate warnings based on base size.

    Args:
        base_n: The base size
        min_base: Minimum acceptable base (below this is an error)
        warn_base: Warning threshold (below this generates a warning)

    Returns:
        List of warning messages
    """
    warnings = []

    if base_n < min_base:
        warnings.append(
            f"Base size ({base_n}) is below minimum threshold ({min_base}). "
            "Results may not be statistically reliable."
        )
    elif base_n < warn_base:
        warnings.append(
            f"Base size ({base_n}) is below recommended threshold ({warn_base}). "
            "Interpret results with caution."
        )

    return warnings
