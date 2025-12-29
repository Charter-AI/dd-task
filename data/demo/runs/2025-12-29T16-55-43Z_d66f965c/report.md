# Analysis Run Report

**Run ID:** 2025-12-29T16-55-43Z_d66f965c
**Timestamp:** 2025-12-29T16:55:59.248812+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** This analysis plan aims to provide a comprehensive understanding of customer satisfaction across various segments, identify key drivers of satisfaction and dissatisfaction, and assess retention risks. By analyzing NPS scores, satisfaction levels, feature usage, and demographic patterns, we can uncover actionable insights to improve product offerings and customer experience. The plan focuses on segmentation to identify underperforming areas and high-value customer groups, enabling targeted interventions and strategic decisions for product development and marketing.

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
- ⚠️ [tenure_groups] Base size (60) is below recommended threshold (100). Interpret results with caution.

### cut_at_risk_customers
- Metric: frequency
- Question: Q_NPS
- Base N: 60
- ⚠️ [at_risk_customers] Base size (13) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_at_risk_customers] Base size (47) is below recommended threshold (100). Interpret results with caution.
