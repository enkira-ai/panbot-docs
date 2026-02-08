---
title: Telephony Agent
description: Voice AI agent system for handling restaurant phone calls.
---

## Overview

The telephony agent is a LiveKit-based voice AI that handles incoming SIP calls from restaurant customers. It uses STT (speech-to-text), LLM (language model), and TTS (text-to-speech) for real-time conversation.

## Architecture

```
Telnyx (SIP) → LiveKit Cloud → Agent Worker → Restaurant Agent
    → STT (Deepgram) → LLM (OpenAI) → TTS (Cartesia)
    → Function Tools → Service Layer → PostgreSQL
```

## Key Files

| File | Purpose |
|------|---------|
| `src/agents/telephony/entrypoint.py` | Agent bootstrap, LiveKit worker setup |
| `src/agents/telephony/restaurant_agent.py` | Restaurant-specific conversation logic |
| `src/agents/telephony/post_call_processor.py` | Post-call analytics and processing |
| `src/agents/telephony/base.py` | SIP header parsing, call context |

## Agent Tools

Tools are decorated with `@function_tool()` and call service methods directly:

| Tool Category | Examples |
|--------------|---------|
| Context loading | `get_business_by_phone()`, `get_customer_by_phone()`, `get_menu_data()` |
| Order management | `create_order()`, `update_order()`, `get_order_status()` |
| Customer service | `lookup_previous_orders()`, `update_customer_preferences()` |

**Architecture boundary**: Agents → Services → Common. Agents never touch DB/Redis directly.

## Call Flow

1. Customer dials restaurant number
2. Call forwards to Telnyx → SIP to LiveKit
3. Agent identifies restaurant from SIP headers (`sip.h.diversion` or `sip.h.to`)
4. Agent loads restaurant context (menu, hours, preferences)
5. Voice conversation with customer
6. Order created via service layer if applicable
7. Post-call processing: Langfuse traces, analytics

## Restaurant Detection

| Environment | SIP Header | Description |
|------------|-----------|-------------|
| Production | `sip.h.diversion` | Restaurant's real number (forwarded call) |
| Development | `sip.h.to` | Telnyx number assigned to restaurant |

Lookup checks both `businesses.phone_number` and `business_phone_numbers.phone_e164`.

## Menu Context

The agent loads an optimized menu JSON from `src/common/menu_format.py` that includes:
- Item names with spoken names and aliases (for STT accuracy)
- Keyterms for context priming
- Ordering instructions for agent behavior
- Pricing and availability

## Observability

- **Langfuse**: All LLM interactions traced via OpenTelemetry
- **Call recordings**: Stored via Telnyx presigned URLs
- **Transcript alignment**: Using first LLM event as t=0, synced with Langfuse timestamps

## Testing

```bash
# Text-only agent testing (no telephony)
make chat-server              # Start agent in text mode
make chat-client phone=+1...  # Connect to specific restaurant
make chat-test                # Start both server and client

# Console mode (voice testing without SIP)
uv run python -m src.agents.telephony.entrypoint console
```
