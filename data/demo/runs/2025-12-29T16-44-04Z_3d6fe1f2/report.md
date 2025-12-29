# Analysis Run Report

**Run ID:** 2025-12-29T16-44-04Z_3d6fe1f2
**Timestamp:** 2025-12-29T16:44:18.236508+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** The analysis plan aims to provide actionable insights into customer satisfaction, feature usage, and retention risks, which are crucial for enhancing product offerings and customer experience. By understanding satisfaction levels across different segments, we can identify areas for improvement and prioritize efforts to boost customer loyalty and retention. This will support strategic decisions for product development and marketing initiatives.

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
- Base N: 13
- ⚠️ [low_purchase_intent] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent] Base size (8) is below minimum threshold (30). Results may not be statistically reliable.
