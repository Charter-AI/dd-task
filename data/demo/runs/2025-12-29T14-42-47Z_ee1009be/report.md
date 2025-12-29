# Analysis Run Report

**Run ID:** 2025-12-29T14-42-47Z_ee1009be
**Timestamp:** 2025-12-29T14:43:03.881278+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** The analysis plan is designed to provide a comprehensive understanding of customer satisfaction and identify areas for improvement, which are crucial for enhancing customer experience and informing strategic business decisions. By analyzing NPS scores, satisfaction levels, and feature usage across different customer segments, we can pinpoint drivers of satisfaction and dissatisfaction, identify at-risk customers, and uncover actionable insights for product improvement. This will help prioritize efforts to boost customer loyalty, optimize product offerings, and tailor marketing strategies to different customer needs.

## Cuts Executed: 4
- **cut_nps_by_region**: nps on Q_NPS
- **cut_mean_sat_by_plan**: mean on Q_OVERALL_SAT
- **cut_nps_by_tenure**: nps on Q_NPS
- **cut_low_nps_low_purchase_intent**: frequency on Q_NPS

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

### cut_mean_sat_by_plan
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

### cut_low_nps_low_purchase_intent
- Metric: frequency
- Question: Q_NPS
- Base N: 13
- ⚠️ [low_purchase_intent] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent] Base size (8) is below minimum threshold (30). Results may not be statistically reliable.
