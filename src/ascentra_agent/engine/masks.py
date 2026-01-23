"""Filter expression to Pandas boolean mask evaluation."""

from typing import Union

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


def build_mask(
    df: pd.DataFrame,
    expr: FilterExpr,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate a filter expression to a boolean mask.

    Args:
        df: The responses DataFrame
        expr: The filter expression to evaluate
        questions_by_id: Question catalog for column name lookup

    Returns:
        Boolean Series indicating which rows match the filter
    """
    if isinstance(expr, PredicateEq):
        return _eval_predicate_eq(df, expr, questions_by_id)
    elif isinstance(expr, PredicateIn):
        return _eval_predicate_in(df, expr, questions_by_id)
    elif isinstance(expr, PredicateRange):
        return _eval_predicate_range(df, expr, questions_by_id)
    elif isinstance(expr, PredicateContainsAny):
        return _eval_predicate_contains_any(df, expr, questions_by_id)
    elif isinstance(expr, PredicateGt):
        return _eval_predicate_gt(df, expr, questions_by_id)
    elif isinstance(expr, PredicateGte):
        return _eval_predicate_gte(df, expr, questions_by_id)
    elif isinstance(expr, PredicateLt):
        return _eval_predicate_lt(df, expr, questions_by_id)
    elif isinstance(expr, PredicateLte):
        return _eval_predicate_lte(df, expr, questions_by_id)
    elif isinstance(expr, And):
        return _eval_and(df, expr, questions_by_id)
    elif isinstance(expr, Or):
        return _eval_or(df, expr, questions_by_id)
    elif isinstance(expr, Not):
        return _eval_not(df, expr, questions_by_id)
    else:
        raise ValueError(f"Unknown filter expression type: {type(expr)}")


def _get_column_name(question_id: str, questions_by_id: dict[str, Question]) -> str:
    """Get the DataFrame column name for a question."""
    question = questions_by_id.get(question_id)
    if question is None:
        # Fallback to question_id if not in catalog
        return question_id
    return question.effective_column_name


def _eval_predicate_eq(
    df: pd.DataFrame,
    pred: PredicateEq,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate equality predicate."""
    col = _get_column_name(pred.question_id, questions_by_id)
    if col not in df.columns:
        # Return all False if column doesn't exist
        return pd.Series(False, index=df.index)

    series = df[col]

    # Handle type coercion for comparison
    value = pred.value
    if pd.api.types.is_numeric_dtype(series):
        try:
            value = float(value) if isinstance(value, str) else value
        except ValueError:
            pass

    return series == value


def _eval_predicate_in(
    df: pd.DataFrame,
    pred: PredicateIn,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate 'in' predicate."""
    col = _get_column_name(pred.question_id, questions_by_id)
    if col not in df.columns:
        return pd.Series(False, index=df.index)

    series = df[col]

    # Prepare values for comparison
    values = pred.values
    if pd.api.types.is_numeric_dtype(series):
        # Convert values to numeric if series is numeric
        converted = []
        for v in values:
            try:
                converted.append(float(v) if isinstance(v, str) else v)
            except ValueError:
                converted.append(v)
        values = converted

    return series.isin(values)


def _eval_predicate_range(
    df: pd.DataFrame,
    pred: PredicateRange,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate range predicate."""
    col = _get_column_name(pred.question_id, questions_by_id)
    if col not in df.columns:
        return pd.Series(False, index=df.index)

    series = pd.to_numeric(df[col], errors="coerce")

    if pred.inclusive:
        return (series >= pred.min) & (series <= pred.max)
    else:
        return (series > pred.min) & (series < pred.max)


def _eval_predicate_gt(
    df: pd.DataFrame,
    pred: PredicateGt,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate greater than predicate."""
    col = _get_column_name(pred.question_id, questions_by_id)
    if col not in df.columns:
        return pd.Series(False, index=df.index)

    series = pd.to_numeric(df[col], errors="coerce")
    return series > pred.value


def _eval_predicate_gte(
    df: pd.DataFrame,
    pred: PredicateGte,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate greater than or equal predicate."""
    col = _get_column_name(pred.question_id, questions_by_id)
    if col not in df.columns:
        return pd.Series(False, index=df.index)

    series = pd.to_numeric(df[col], errors="coerce")
    return series >= pred.value


def _eval_predicate_lt(
    df: pd.DataFrame,
    pred: PredicateLt,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate less than predicate."""
    col = _get_column_name(pred.question_id, questions_by_id)
    if col not in df.columns:
        return pd.Series(False, index=df.index)

    series = pd.to_numeric(df[col], errors="coerce")
    return series < pred.value


def _eval_predicate_lte(
    df: pd.DataFrame,
    pred: PredicateLte,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate less than or equal predicate."""
    col = _get_column_name(pred.question_id, questions_by_id)
    if col not in df.columns:
        return pd.Series(False, index=df.index)

    series = pd.to_numeric(df[col], errors="coerce")
    return series <= pred.value


def _eval_predicate_contains_any(
    df: pd.DataFrame,
    pred: PredicateContainsAny,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate 'contains any' predicate for multi-choice questions.

    Multi-choice responses are stored as semicolon-separated codes,
    e.g., "1;3;5" means options 1, 3, and 5 were selected.
    """
    col = _get_column_name(pred.question_id, questions_by_id)
    if col not in df.columns:
        return pd.Series(False, index=df.index)

    # Convert values to strings for comparison
    target_values = {str(v) for v in pred.values}

    def check_contains(cell: Union[str, float, None]) -> bool:
        if pd.isna(cell) or cell is None:
            return False
        # Split on semicolon and check for any matches
        cell_str = str(cell)
        cell_values = {v.strip() for v in cell_str.split(";")}
        return bool(cell_values & target_values)

    return df[col].apply(check_contains)


def _eval_and(
    df: pd.DataFrame,
    expr: And,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate AND expression (all children must be true)."""
    if not expr.children:
        return pd.Series(True, index=df.index)

    result = build_mask(df, expr.children[0], questions_by_id)
    for child in expr.children[1:]:
        result = result & build_mask(df, child, questions_by_id)
    return result


def _eval_or(
    df: pd.DataFrame,
    expr: Or,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate OR expression (at least one child must be true)."""
    if not expr.children:
        return pd.Series(False, index=df.index)

    result = build_mask(df, expr.children[0], questions_by_id)
    for child in expr.children[1:]:
        result = result | build_mask(df, child, questions_by_id)
    return result


def _eval_not(
    df: pd.DataFrame,
    expr: Not,
    questions_by_id: dict[str, Question],
) -> pd.Series:
    """Evaluate NOT expression (inverts child)."""
    return ~build_mask(df, expr.child, questions_by_id)
