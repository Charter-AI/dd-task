# Analysis Run Report

**Run ID:** 2025-12-29T16-49-46Z_21189efd
**Timestamp:** 2025-12-29T16:50:00.844225+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** This analysis plan aims to provide a comprehensive understanding of customer satisfaction with our SaaS analytics platform. By analyzing various aspects such as NPS, satisfaction levels, feature usage, and demographic segments, we can identify key drivers of satisfaction and dissatisfaction. This will help us make informed decisions to improve product features, target underperforming segments, and enhance customer retention strategies. The insights gained will support strategic planning for product development and customer engagement, ultimately driving business growth.

## Cuts Executed: 3
- **cut_nps_by_region**: nps on Q_NPS
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_at_risk_customers**: frequency on Q_NPS

## Failed Cuts: 2
- **intent_002**: Compare satisfaction across subscription plans to ...
- **intent_003**: Analyze correlation between feature usage and sati...

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
- ⚠️ Multi-dimension cross-tabs not fully supported. Using first dimension only. Ignored: ['new_customers']
- ⚠️ [long_term_customers] Base size (29) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_long_term_customers] Base size (31) is below recommended threshold (100). Interpret results with caution.

### cut_at_risk_customers
- Metric: frequency
- Question: Q_NPS
- Base N: 13
- ⚠️ [low_purchase_intent_customers] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent_customers] Base size (8) is below minimum threshold (30). Results may not be statistically reliable.
