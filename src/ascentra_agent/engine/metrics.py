"""Metric computation functions."""

from typing import Any, Optional

import pandas as pd

from ascentra_agent.contracts.questions import Question, QuestionType


def compute_frequency(
    series: pd.Series,
    question: Optional[Question] = None,
    normalize: bool = True,
) -> pd.DataFrame:
    """Compute frequency distribution of values.

    Args:
        series: The data series to analyze
        question: Optional question for label lookup
        normalize: Whether to return percentages (True) or counts (False)

    Returns:
        DataFrame with columns: value, label, count, percentage
    """
    # Get value counts
    counts = series.value_counts(dropna=True)
    total = counts.sum()

    # Build result DataFrame
    data = []
    for value, count in counts.items():
        label = None
        if question is not None:
            label = question.get_option_label(value)
        if label is None:
            label = str(value)

        percentage = (count / total * 100) if total > 0 else 0.0

        data.append({
            "value": value,
            "label": label,
            "count": int(count),
            "percentage": round(percentage, 2),
        })

    result = pd.DataFrame(data)

    # Sort by value if numeric, otherwise by count descending
    if len(result) > 0:
        if pd.api.types.is_numeric_dtype(result["value"]):
            result = result.sort_values("value").reset_index(drop=True)
        else:
            result = result.sort_values("count", ascending=False).reset_index(drop=True)

    return result


def compute_mean(
    series: pd.Series,
    weights: Optional[pd.Series] = None,
) -> dict[str, Any]:
    """Compute mean of a numeric series.

    Args:
        series: The data series (numeric values)
        weights: Optional weights for weighted average

    Returns:
        Dict with mean, std, min, max, and count
    """
    numeric_series = pd.to_numeric(series, errors="coerce")
    valid_mask = numeric_series.notna()

    if weights is not None:
        # Weighted mean
        valid_weights = weights[valid_mask]
        valid_values = numeric_series[valid_mask]

        if valid_weights.sum() > 0:
            mean_val = (valid_values * valid_weights).sum() / valid_weights.sum()
        else:
            mean_val = float("nan")
    else:
        mean_val = numeric_series.mean()

    return {
        "mean": round(float(mean_val), 4) if pd.notna(mean_val) else None,
        "std": round(float(numeric_series.std()), 4) if pd.notna(numeric_series.std()) else None,
        "min": float(numeric_series.min()) if pd.notna(numeric_series.min()) else None,
        "max": float(numeric_series.max()) if pd.notna(numeric_series.max()) else None,
        "count": int(valid_mask.sum()),
    }


def compute_top2box(
    series: pd.Series,
    question: Optional[Question] = None,
    top_values: Optional[list[int]] = None,
) -> dict[str, Any]:
    """Compute top 2 box percentage.

    For Likert scales, "top 2 box" typically means the percentage of
    respondents selecting the top 2 positive options.

    Args:
        series: The data series
        question: Question for determining scale
        top_values: Explicit values to count as "top 2" (overrides auto-detection)

    Returns:
        Dict with top2box percentage, counts, and total
    """
    numeric_series = pd.to_numeric(series, errors="coerce")
    valid_mask = numeric_series.notna()
    valid_series = numeric_series[valid_mask]

    if len(valid_series) == 0:
        return {
            "top2box_pct": None,
            "top2box_count": 0,
            "total": 0,
        }

    if top_values is None:
        # Auto-detect based on question type
        if question is not None:
            if question.type == QuestionType.likert_1_5:
                top_values = [4, 5]
            elif question.type == QuestionType.likert_1_7:
                top_values = [6, 7]
            else:
                # Fallback: top 2 values in the data
                unique_vals = sorted(valid_series.unique())
                if len(unique_vals) >= 2:
                    top_values = list(unique_vals[-2:])
                else:
                    top_values = list(unique_vals)
        else:
            # Fallback without question info
            unique_vals = sorted(valid_series.unique())
            if len(unique_vals) >= 2:
                top_values = list(unique_vals[-2:])
            else:
                top_values = list(unique_vals)

    top2_count = valid_series.isin(top_values).sum()
    total = len(valid_series)
    pct = (top2_count / total * 100) if total > 0 else 0.0

    return {
        "top2box_pct": round(float(pct), 2),
        "top2box_count": int(top2_count),
        "total": int(total),
        "top_values": top_values,
    }


def compute_bottom2box(
    series: pd.Series,
    question: Optional[Question] = None,
    bottom_values: Optional[list[int]] = None,
) -> dict[str, Any]:
    """Compute bottom 2 box percentage.

    For Likert scales, "bottom 2 box" typically means the percentage of
    respondents selecting the bottom 2 negative options.

    Args:
        series: The data series
        question: Question for determining scale
        bottom_values: Explicit values to count as "bottom 2"

    Returns:
        Dict with bottom2box percentage, counts, and total
    """
    numeric_series = pd.to_numeric(series, errors="coerce")
    valid_mask = numeric_series.notna()
    valid_series = numeric_series[valid_mask]

    if len(valid_series) == 0:
        return {
            "bottom2box_pct": None,
            "bottom2box_count": 0,
            "total": 0,
        }

    if bottom_values is None:
        # Auto-detect based on question type
        if question is not None:
            if question.type == QuestionType.likert_1_5:
                bottom_values = [1, 2]
            elif question.type == QuestionType.likert_1_7:
                bottom_values = [1, 2]
            else:
                unique_vals = sorted(valid_series.unique())
                if len(unique_vals) >= 2:
                    bottom_values = list(unique_vals[:2])
                else:
                    bottom_values = list(unique_vals)
        else:
            unique_vals = sorted(valid_series.unique())
            if len(unique_vals) >= 2:
                bottom_values = list(unique_vals[:2])
            else:
                bottom_values = list(unique_vals)

    bottom2_count = valid_series.isin(bottom_values).sum()
    total = len(valid_series)
    pct = (bottom2_count / total * 100) if total > 0 else 0.0

    return {
        "bottom2box_pct": round(float(pct), 2),
        "bottom2box_count": int(bottom2_count),
        "total": int(total),
        "bottom_values": bottom_values,
    }


def compute_nps(
    series: pd.Series,
    promoter_min: int = 9,
    detractor_max: int = 6,
) -> dict[str, Any]:
    """Compute Net Promoter Score.

    NPS = %Promoters - %Detractors
    - Promoters: 9-10
    - Passives: 7-8
    - Detractors: 0-6

    Args:
        series: The data series (0-10 scale)
        promoter_min: Minimum value for promoters (default: 9)
        detractor_max: Maximum value for detractors (default: 6)

    Returns:
        Dict with NPS score and breakdown
    """
    numeric_series = pd.to_numeric(series, errors="coerce")
    valid_mask = numeric_series.notna()
    valid_series = numeric_series[valid_mask]

    if len(valid_series) == 0:
        return {
            "nps": None,
            "promoters_count": 0,
            "passives_count": 0,
            "detractors_count": 0,
            "total": 0,
        }

    total = len(valid_series)
    promoters = (valid_series >= promoter_min).sum()
    detractors = (valid_series <= detractor_max).sum()
    passives = total - promoters - detractors

    promoters_pct = promoters / total * 100
    detractors_pct = detractors / total * 100
    nps_score = promoters_pct - detractors_pct

    return {
        "nps": round(float(nps_score), 2),
        "promoters_count": int(promoters),
        "promoters_pct": round(float(promoters_pct), 2),
        "passives_count": int(passives),
        "passives_pct": round(float(passives / total * 100), 2),
        "detractors_count": int(detractors),
        "detractors_pct": round(float(detractors_pct), 2),
        "total": int(total),
    }


def compute_multi_choice_frequency(
    series: pd.Series,
    question: Optional[Question] = None,
    separator: str = ";",
) -> pd.DataFrame:
    """Compute frequency for multi-choice questions.

    Multi-choice responses are stored as semicolon-separated values.
    Each option is counted independently.

    Args:
        series: The data series with semicolon-separated values
        question: Optional question for label lookup
        separator: The separator character (default: ;)

    Returns:
        DataFrame with columns: value, label, count, percentage
    """
    # Explode multi-choice into individual responses
    all_values = []
    total_respondents = 0

    for cell in series:
        if pd.notna(cell) and cell is not None:
            total_respondents += 1
            cell_str = str(cell)
            values = [v.strip() for v in cell_str.split(separator) if v.strip()]
            all_values.extend(values)

    if not all_values:
        return pd.DataFrame(columns=["value", "label", "count", "percentage"])

    # Count occurrences
    value_counts = pd.Series(all_values).value_counts()

    # Build result DataFrame
    data = []
    for value, count in value_counts.items():
        label = None
        if question is not None:
            # Try both string and int lookup
            label = question.get_option_label(value)
            if label is None:
                try:
                    label = question.get_option_label(int(value))
                except ValueError:
                    pass
        if label is None:
            label = str(value)

        # Percentage is of respondents who answered, not total selections
        percentage = (count / total_respondents * 100) if total_respondents > 0 else 0.0

        data.append({
            "value": value,
            "label": label,
            "count": int(count),
            "percentage": round(percentage, 2),
        })

    result = pd.DataFrame(data)
    return result.sort_values("count", ascending=False).reset_index(drop=True)
