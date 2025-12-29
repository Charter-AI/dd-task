# Analysis Run Report

**Run ID:** 2025-12-29T14-56-58Z_5d9f4a79
**Timestamp:** 2025-12-29T14:57:15.351750+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** The analysis plan aims to provide actionable insights into customer satisfaction and loyalty, identify key drivers of satisfaction and dissatisfaction, and highlight segments that require attention for improvement. By analyzing NPS, satisfaction levels, feature usage, and demographic patterns, we can pinpoint areas for product enhancement and retention strategies, ultimately supporting business decisions and informing the Q1 product roadmap.

## Cuts Executed: 2
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_at_risk_customers**: nps on Q_NPS

## Failed Cuts: 3
- **intent_001**: Analyze overall NPS and satisfaction levels to ass...
- **intent_002**: Compare satisfaction across different subscription...
- **intent_003**: Analyze feature usage correlation with satisfactio...

## Execution Results
**Tables Generated:** 2

### cut_nps_by_tenure
- Metric: nps
- Question: Q_NPS
- Base N: 45
- ⚠️ [LONG] Base size (29) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [NEW] Base size (16) is below minimum threshold (30). Results may not be statistically reliable.

### cut_at_risk_customers
- Metric: nps
- Question: Q_NPS
- Base N: 60
- ⚠️ [low_purchase_intent] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent] Base size (55) is below recommended threshold (100). Interpret results with caution.
