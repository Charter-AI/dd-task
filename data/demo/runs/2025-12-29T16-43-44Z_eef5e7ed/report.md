# Analysis Run Report

**Run ID:** 2025-12-29T16-43-44Z_eef5e7ed
**Timestamp:** 2025-12-29T16:43:59.760921+00:00
**Dataset Hash:** a6f03d8d1e33da7d...

## Status: ✅ Success

## Analysis Plan
**Intents:** 5
**Rationale:** This analysis plan aims to provide a comprehensive understanding of customer satisfaction with the SaaS analytics platform. By examining Net Promoter Scores (NPS), overall satisfaction, and feature usage across different customer segments, we can identify key drivers of satisfaction and dissatisfaction. This will help prioritize product improvements and inform strategic decisions to enhance customer experience and retention. Additionally, understanding demographic and regional differences will allow targeted marketing and support strategies, ensuring we address the needs of underperforming segments and mitigate churn risks.

## Cuts Executed: 2
- **cut_nps_by_region**: nps on Q_NPS
- **cut_at_risk_customers**: frequency on Q_NPS

## Failed Cuts: 3
- **intent_002**: Compare overall satisfaction across different subs...
- **intent_003**: Analyze correlation between feature usage and over...
- **intent_004**: Segment customers by tenure and analyze NPS and ov...

## Execution Results
**Tables Generated:** 2

### cut_nps_by_region
- Metric: nps
- Question: Q_NPS
- Base N: 60
- ⚠️ [CENTRAL] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [EAST] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [NORTH] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [SOUTH] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [WEST] Base size (12) is below minimum threshold (30). Results may not be statistically reliable.

### cut_at_risk_customers
- Metric: frequency
- Question: Q_NPS
- Base N: 13
- ⚠️ [low_purchase_intent_customers] Base size (5) is below minimum threshold (30). Results may not be statistically reliable.
- ⚠️ [not_low_purchase_intent_customers] Base size (8) is below minimum threshold (30). Results may not be statistically reliable.
