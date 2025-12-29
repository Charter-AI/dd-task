# Analysis Run Report

**Run ID:** 2025-12-29T14-58-20Z_572ff8da
**Timestamp:** 2025-12-29T14:58:38.763224+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** This analysis plan aims to provide actionable insights into customer satisfaction and retention for our SaaS analytics platform. By understanding NPS scores, satisfaction levels, and feature usage, we can identify key drivers of satisfaction and dissatisfaction, highlight underperforming segments, and assess retention risks. These insights are crucial for informing product improvements and strategic decisions to enhance customer experience and reduce churn.

## Cuts Executed: 4
- **cut_nps_by_region**: nps on Q_NPS
- **cut_overall_sat_by_plan**: mean on Q_OVERALL_SAT
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_at_risk_customers_low_nps_low_purchase_intent**: frequency on Q_NPS

## Failed Cuts: 1
- **intent_003**: Analyze correlation between feature usage and over...

## Execution Results
**Tables Generated:** 4

### cut_nps_by_region
- Metric: nps
- Question: Q_NPS
- Base N: 60
- ⚠️ [CENTRAL] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [EAST] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [NORTH] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [SOUTH] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [WEST] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.

### cut_overall_sat_by_plan
- Metric: mean
- Question: Q_OVERALL_SAT
- Base N: 60
- ⚠️ [BASIC] Base size (11) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [ENT] Base size (17) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [FREE] Base size (9) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [PRO] Base size (23) is below minimum threshold (30). Results may not be statistically reliable.

### cut_nps_by_tenure
- Metric: nps
- Question: Q_NPS
- Base N: 60
- ⚠️ [LONG] Base size (29) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [MED] Base size (15) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [NEW] Base size (16) is below minimum threshold (30). Results may not be statistically reliable.

### cut_at_risk_customers_low_nps_low_purchase_intent
- Metric: frequency
- Question: Q_NPS
- Base N: 13
- ⚠️ [at_risk_customers] Base size (13) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_at_risk_customers] Base size (0) is below minimum threshold (30). Results may not be statistically reliable.
