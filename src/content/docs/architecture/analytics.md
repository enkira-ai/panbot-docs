---
title: Analytics System
description: Temporal-based analytics and end-of-day processing plan.
---

## Overview

Analytics will be powered by Temporal workflows for durable, scheduled processing. Currently using client-side computation as placeholder.

| Area | Current State | Target State |
|------|--------------|-------------|
| Dashboard stats | Client-side aggregation | Temporal daily workflows |
| Popular dishes | Computed per page load | Pre-computed daily summary |
| Customer warnings | Client-side from order data | End-of-day batch computation |
| Call metrics | Basic count from API | Temporal post-call analysis |

## Planned API Endpoints (Placeholder)

```
GET /api/v1/analytics/summary?business_id=&period=today|week|month|custom
GET /api/v1/analytics/popular-items?business_id=&period=&limit=10
GET /api/v1/analytics/customer-stats?business_id=&period=
GET /api/v1/analytics/order-breakdown?business_id=&period=
```

## Temporal Workflows

### End-of-Day Close

Triggered at business closing time (business timezone) or manually via "Close Day" button.

- [ ] Calculate daily totals by payment type
- [ ] Generate customer warnings (unpaid orders)
- [ ] Compute call metrics (total calls, duration, transfer rate)
- [ ] Store in `daily_summaries` table
- [ ] Optional: send daily report email to owner

### Post-Call Processing

Already partially implemented in `src/agents/telephony/post_call_processor.py`:

- [ ] Transcript scoring for quality review
- [ ] Order reconciliation with POS
- [ ] Customer sentiment analysis (future)

### Scheduled Reports

- [ ] Weekly revenue summary
- [ ] Popular dish trends
- [ ] Staff performance metrics

## Data Model (Planned)

```python
class DailySummaryDB:
    business_id: UUID
    business_date: date        # In business timezone
    summary_data: Dict         # orders_count, total_revenue, by_payment_type
    warnings: List[Dict]       # customer warnings snapshot
    call_metrics: Dict         # total_calls, avg_duration, transfer_rate
    generated_at: datetime
```

## Timezone Handling

All analytics use business timezone for day boundaries. The `businesses.timezone` field determines when "end of day" occurs.
