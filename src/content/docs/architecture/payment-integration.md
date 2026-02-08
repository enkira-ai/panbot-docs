---
title: Payment Integration
description: Square and Stripe integration plan for PanBot.
---

## Overview

PanBot uses two payment platforms for different purposes:

| Platform | Purpose | Status |
|----------|---------|--------|
| **Square** | Customer payment collection (POS) | Planned |
| **Stripe** | Subscription billing (our SaaS fees) | Planned |

## Square Integration (Customer Payments)

Square handles payment collection from restaurant customers:

- [ ] Square OAuth flow for restaurant onboarding
- [ ] Square Orders API for order management
- [ ] Square Reader for contactless + chip payments
- [ ] Automatic tax calculation by business address
- [ ] Order fulfillment state tracking (new → ready → completed)
- [ ] Receipt layout via Square's built-in tools (research needed)

**Key decision**: Square's Order Update API will be the source of truth for order changes, providing built-in audit trail.

## Stripe Integration (SaaS Billing)

Stripe handles subscription payments from restaurant owners to us:

- [ ] Stripe Checkout for web dashboard subscription flow
- [ ] Stripe Elements for desktop app (no redirect support)
- [ ] Subscription management (plan changes, cancellations)
- [ ] Usage-based billing (per-call metering, future)

## Order Status Model

Orders have separate statuses aligned with payment platform requirements:

| Field | Values | Owner |
|-------|--------|-------|
| `order_status` | pending, sent, printed | Backend (internal) |
| `payment_status` | pending, authorized, captured, failed, refunded | Payment platform |
| `display_status` | Derived from above for UI | Frontend computation |

## Order Audit Trail

```python
# Planned: OrderEventDB table
class OrderEventDB:
    order_id: UUID
    event_type: str  # item_added, item_removed, quantity_changed, discount_applied
    changed_by: UUID  # staff user
    previous_value: Dict  # JSONB
    new_value: Dict      # JSONB
    reason: str          # required for accountability
    synced_to_pos: bool
```
