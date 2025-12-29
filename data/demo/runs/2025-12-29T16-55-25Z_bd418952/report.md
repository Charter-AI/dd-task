# Analysis Run Report

**Run ID:** 2025-12-29T16-55-25Z_bd418952
**Timestamp:** 2025-12-29T16:55:39.405477+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** The analysis plan is designed to provide a comprehensive understanding of customer satisfaction and identify actionable insights for product improvement. By examining overall satisfaction, segment differences, feature usage, and retention risks, we can pinpoint areas that require attention and prioritize efforts to enhance customer experience and loyalty. This plan will support strategic decisions for the Q1 product roadmap and help achieve business goals such as increasing NPS and satisfaction levels.

## Cuts Executed: 3
- **cut_nps_by_region**: nps on Q_NPS
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_at_risk_customers**: frequency on Q_NPS

## Failed Cuts: 2
- **intent_002**: Compare satisfaction across subscription plans to ...
- **intent_003**: Analyze correlation between feature usage and over...

## Execution Results
**Tables Generated:** 3

### cut_nps_by_region
- Metric: nps
- Question: Q_NPS
- Base N: 60
- ⚠️ [CENTRAL] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [EAST] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [NORTH] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [SOUTH] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [WEST] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.

### cut_nps_by_tenure
- Metric: nps
- Question: Q_NPS
- Base N: 60
- ⚠️ [LONG] Base size (29) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [MED] Base size (15) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [NEW] Base size (16) is below minimum threshold (30). Results may not be statistically reliable.

### cut_at_risk_customers
- Metric: frequency
- Question: Q_NPS
- Base N: 60
- ⚠️ [at_risk_customers] Base size (13) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_at_risk_customers] Base size (47) is below recommended threshold (100). Interpret results with caution.
