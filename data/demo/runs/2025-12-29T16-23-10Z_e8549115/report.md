# Analysis Run Report

**Run ID:** 2025-12-29T16-23-10Z_e8549115
**Timestamp:** 2025-12-29T16:23:24.360499+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** The analysis plan aims to provide a comprehensive understanding of customer satisfaction with our SaaS analytics platform, identify key drivers of satisfaction and dissatisfaction, and highlight areas for improvement. By segmenting customers based on demographic and usage patterns, we can tailor our product development and marketing strategies to better meet customer needs and enhance retention. The insights derived from this analysis will inform strategic decisions for the Q1 product roadmap, ensuring that we focus on areas that maximize customer satisfaction and loyalty.

## Cuts Executed: 3
- **cut_nps_by_region**: nps on Q_NPS
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_at_risk_customers**: frequency on Q_NPS

## Failed Cuts: 2
- **intent_002**: Compare overall satisfaction across subscription p...
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
- ⚠️ Multi-dimension cross-tabs not fully supported. Using first dimension only. Ignored: ['new_customers']
- ⚠️ [long_term_customers] Base size (29) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_long_term_customers] Base size (31) is below recommended threshold (100). Interpret results with caution.

### cut_at_risk_customers
- Metric: frequency
- Question: Q_NPS
- Base N: 60
- ⚠️ [at_risk_customers] Base size (13) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_at_risk_customers] Base size (47) is below recommended threshold (100). Interpret results with caution.
