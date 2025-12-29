# Analysis Run Report

**Run ID:** 2025-12-29T14-42-47Z_071434a2
**Timestamp:** 2025-12-29T14:43:05.645760+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** This analysis plan aims to provide a comprehensive understanding of customer satisfaction with our SaaS analytics platform, focusing on identifying key drivers of satisfaction and dissatisfaction, understanding demographic and usage patterns, and assessing retention risks. By segmenting customers based on their subscription plans, tenure, and usage patterns, we can pinpoint areas for improvement and prioritize actionable insights that will inform our Q1 product roadmap and enhance customer experience.

## Cuts Executed: 4
- **cut_nps_by_region**: nps on Q_NPS
- **cut_feature_usage_correlation_with_sat**: mean on Q_OVERALL_SAT
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_low_nps_low_purchase_intent**: frequency on Q_NPS

## Failed Cuts: 1
- **intent_002**: Compare satisfaction across subscription plans to ...

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

### cut_feature_usage_correlation_with_sat
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
- Base N: 13
- ⚠️ [low_purchase_intent] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent] Base size (8) is below minimum threshold (30). Results may not be statistically reliable.
