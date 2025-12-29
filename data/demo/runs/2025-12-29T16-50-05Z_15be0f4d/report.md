# Analysis Run Report

**Run ID:** 2025-12-29T16-50-05Z_15be0f4d
**Timestamp:** 2025-12-29T16:50:20.642270+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** The analysis plan aims to provide actionable insights into customer satisfaction and retention by examining key metrics such as NPS, overall satisfaction, and feature usage. By segmenting customers based on demographics, subscription plans, and usage patterns, we can identify areas for improvement and tailor strategies to enhance customer experience and reduce churn risk. This analysis will support strategic decisions for product development and marketing initiatives.

## Cuts Executed: 3
- **cut_nps_by_region**: nps on Q_NPS
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_at_risk_customers**: frequency on Q_NPS

## Failed Cuts: 2
- **intent_002**: Compare overall satisfaction across different subs...
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
- Base N: 13
- ⚠️ [low_purchase_intent] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent] Base size (8) is below minimum threshold (30). Results may not be statistically reliable.
