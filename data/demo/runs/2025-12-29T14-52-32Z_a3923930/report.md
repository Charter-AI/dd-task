# Analysis Run Report

**Run ID:** 2025-12-29T14-52-32Z_a3923930
**Timestamp:** 2025-12-29T14:52:47.786368+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** The analysis plan is designed to provide a comprehensive understanding of customer satisfaction with our SaaS analytics platform. By examining Net Promoter Scores, satisfaction levels, and feature usage across different customer segments, we aim to identify key drivers of satisfaction and dissatisfaction. This will help us prioritize improvements and optimize our product offerings. Additionally, analyzing retention risks will allow us to proactively address potential churn, ensuring sustainable growth and customer loyalty.

## Cuts Executed: 5
- **cut_nps_by_region**: nps on Q_NPS
- **cut_sat_by_plan**: mean on Q_OVERALL_SAT
- **cut_feature_usage_by_overall_satisfaction**: mean on Q_OVERALL_SAT
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_low_nps_low_intent**: frequency on Q_NPS

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

### cut_sat_by_plan
- Metric: mean
- Question: Q_OVERALL_SAT
- Base N: 60
- ⚠️ [BASIC] Base size (11) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [ENT] Base size (17) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [FREE] Base size (9) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [PRO] Base size (23) is below minimum threshold (30). Results may not be statistically reliable.

### cut_feature_usage_by_overall_satisfaction
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

### cut_low_nps_low_intent
- Metric: frequency
- Question: Q_NPS
- Base N: 13
- ⚠️ [low_purchase_intent] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent] Base size (8) is below minimum threshold (30). Results may not be statistically reliable.
