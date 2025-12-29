# Analysis Run Report

**Run ID:** 2025-12-29T14-34-04Z_7b59d01e
**Timestamp:** 2025-12-29T14:34:21.414847+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** The analysis plan is designed to uncover key insights into customer satisfaction and identify areas for improvement in our SaaS analytics platform. By understanding the drivers of satisfaction and dissatisfaction, we can make informed decisions to enhance product features, improve customer support, and tailor marketing strategies. Analyzing segment-specific satisfaction levels will help identify underperforming areas and guide targeted interventions. Additionally, understanding feature usage and retention risks will enable us to optimize product offerings and reduce churn, ultimately supporting business growth and customer loyalty.

## Cuts Executed: 5
- **cut_nps_by_region**: nps on Q_NPS
- **cut_mean_sat_by_plan**: mean on Q_OVERALL_SAT
- **cut_correlation_features_overall_sat**: mean on Q_OVERALL_SAT
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_low_nps_low_purchase_intent**: frequency on Q_NPS

## Execution Results
**Tables Generated:** 5

### cut_nps_by_region
- Metric: nps
- Question: Q_NPS
- Base N: 60
- ⚠️ [CENTRAL] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [EAST] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [NORTH] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [SOUTH] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [WEST] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.

### cut_mean_sat_by_plan
- Metric: mean
- Question: Q_OVERALL_SAT
- Base N: 60
- ⚠️ [BASIC] Base size (11) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [ENT] Base size (17) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [FREE] Base size (9) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [PRO] Base size (23) is below minimum threshold (30). Results may not be statistically reliable.

### cut_correlation_features_overall_sat
- Metric: mean
- Question: Q_OVERALL_SAT
- Base N: 60
- ⚠️ [DASH] Base size (7) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;EXPORT;MOBILE] Base size (1) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;MOBILE] Base size (6) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;API] Base size (1) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;API;COLLAB] Base size (6) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;COLLAB] Base size (3) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;EXPORT] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;EXPORT;API] Base size (3) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;EXPORT;API;COLLAB] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;EXPORT;COLLAB] Base size (4) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;EXPORT;MOBILE] Base size (1) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [DASH;REPORT;MOBILE] Base size (6) is below minimum threshold (30). Results may not be statistically reliable.

### cut_nps_by_tenure
- Metric: nps
- Question: Q_NPS
- Base N: 60
- ⚠️ [LONG] Base size (29) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [MED] Base size (15) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [NEW] Base size (16) is below minimum threshold (30). Results may not be statistically reliable.

### cut_low_nps_low_purchase_intent
- Metric: frequency
- Question: Q_NPS
- Base N: 0
- ⚠️ [low_purchase_intent_customers] Base size (0) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent_customers] Base size (0) is below minimum threshold (30). Results may not be statistically reliable.
