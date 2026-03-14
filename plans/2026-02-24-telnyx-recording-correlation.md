# Telnyx Recording Correlation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the agent-side Redis handshake so Telnyx call recordings are automatically linked to call records via the existing correlation service.

**Architecture:** The API pod already receives Telnyx webhooks and stores events in Redis. The agent pod needs to call `register_livekit_call()` after extracting phone numbers, so Redis can match the two sides by phone pair + timing. A new `telnyx_call_session_id` DB column supports transfer scenarios.

**Tech Stack:** Python, SQLModel, Alembic, Redis, pytest

**Related Issues:** #25, #39

---

### Task 1: Add `telnyx_call_session_id` column to CallDB

**Files:**
- Modify: `src/models/database.py:199` (add column after `telnyx_call_id`)
- Modify: `src/services/call_service.py:60-116` (accept + store new param)
- Create: migration via `make migrate-auto`

**Step 1: Add column to CallDB model**

In `src/models/database.py`, after `telnyx_call_id` (line 199), add:

```python
telnyx_call_session_id: Optional[str] = SQLModelField(default=None, index=True)
```

**Step 2: Add parameter to `CallService.create_call()`**

In `src/services/call_service.py`, add `telnyx_call_session_id: Optional[str] = None` parameter and set it on the `CallDB(...)` constructor.

**Step 3: Start local dev infra and generate migration**

```bash
make dev-infra
make migrate-auto message="Add telnyx_call_session_id to calls"
```

**Step 4: Apply migration to local DB**

```bash
make migrate-upgrade
```

**Step 5: Verify migration**

```bash
make migrate-current
```

**Step 6: Commit**

```bash
git add src/models/database.py src/services/call_service.py migrations/versions/
git commit -m "feat(db): add telnyx_call_session_id column to calls table

Supports transfer scenarios where recording is attached to a different
call leg but same session.

Refs #25, #39"
```

---

### Task 2: Extract SIP Call-ID in agent and call `register_livekit_call()`

This is the core wiring. Replace the ineffective `_extract_telnyx_call_id()` SIP header approach with the Redis correlation handshake.

**Files:**
- Modify: `src/agents/telephony/base.py:440-468` (replace telnyx extraction with correlation)

**Step 1: Replace `_extract_telnyx_call_id()` usage with correlation service**

In `base.py`, after phone number extraction (~line 440), replace:

```python
# OLD (lines 442-447):
telnyx_call_id = self._extract_telnyx_call_id(ctx)
if telnyx_call_id:
    logger.info(f"Telnyx call ID: {telnyx_call_id}")
else:
    logger.warning("Could not extract Telnyx call ID - using fallback UUID")
```

With:

```python
# Extract SIP Call-ID (standard header, always available)
sip_call_id = self._extract_sip_call_id(ctx)

# Try Redis correlation to get Telnyx IDs
telnyx_call_id = None
telnyx_call_session_id = None
try:
    from src.services.call_correlation_service import get_call_correlation_service
    correlation_service = get_call_correlation_service()
    correlation_result = await correlation_service.register_livekit_call(
        call_id=str(uuid.uuid4()),  # Temporary ID; real call_id assigned in post-call
        sip_call_id=sip_call_id or "",
        room_name=ctx.room.name,
        from_number=caller_phone or "",
        to_number=target_phone or "",
    )
    if correlation_result:
        telnyx_call_id = correlation_result.telnyx_call_leg_id
        telnyx_call_session_id = correlation_result.telnyx_call_session_id
        logger.info(f"Telnyx correlation matched: leg={telnyx_call_id}, session={telnyx_call_session_id}")
    else:
        logger.info("No Telnyx correlation yet (webhook may arrive later)")
except Exception as e:
    logger.warning(f"Correlation service unavailable, falling back to SIP headers: {e}")
    telnyx_call_id = self._extract_telnyx_call_id(ctx)
```

**Step 2: Add `_extract_sip_call_id()` helper method**

Add a small method to `base.py` (near `_extract_telnyx_call_id`):

```python
def _extract_sip_call_id(self, ctx: JobContext) -> Optional[str]:
    """Extract the standard SIP Call-ID header from participant attributes."""
    for participant in ctx.room.remote_participants.values():
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            attrs_lower = {str(k).lower(): v for k, v in getattr(participant, 'attributes', {}).items()}
            for key in ['sip.h.call-id', 'sip.call_id']:
                value = attrs_lower.get(key, '')
                if value and isinstance(value, str) and value.strip():
                    return value.strip()
    return None
```

**Step 3: Store `telnyx_call_session_id` in userdata**

Update the userdata storage block (~line 462-468):

```python
if hasattr(userdata, '__dict__'):
    userdata._telnyx_call_id = telnyx_call_id
    userdata._telnyx_call_session_id = telnyx_call_session_id
    userdata._sip_call_id = sip_call_id
    userdata._session_start_time = session_start_time
    userdata._langfuse_session_id = ctx.room.name
    userdata._langfuse_job_id = ctx.job.id if ctx.job else None
```

**Step 4: Commit**

```bash
git add src/agents/telephony/base.py
git commit -m "feat(agent): wire Redis correlation for Telnyx call ID matching

Replace _extract_telnyx_call_id() SIP header approach (which never worked
because Telnyx strips internal IDs) with register_livekit_call() Redis
handshake. Falls back to SIP header extraction if Redis unavailable.

Refs #25, #39"
```

---

### Task 3: Pass correlation data through to call record creation

**Files:**
- Modify: `src/agents/telephony/restaurant_agent.py:2630-2664` (pass new fields)

**Step 1: Update `_create_call_record` in restaurant_agent.py**

In the post-call processing section (~line 2630), update to pass the new fields:

```python
telnyx_call_id = getattr(userdata, '_telnyx_call_id', None)
telnyx_call_session_id = getattr(userdata, '_telnyx_call_session_id', None)
sip_call_id = getattr(userdata, '_sip_call_id', None)
session_start_time = getattr(userdata, '_session_start_time', None)
session_end_time = getattr(userdata, '_session_end_time', None)
```

Update the `create_call()` call to use `sip_call_id` for `session_id` (instead of telnyx_call_id):

```python
call = await call_service.create_call(
    business_id=userdata.business.id,
    session_id=sip_call_id or str(uuid.uuid4()),  # SIP Call-ID, not Telnyx ID
    caller_phone=userdata.caller_phone or "unknown",
    forwarding_from=userdata.business.phone_number,
    direction="inbound",
    stt_mode=stt_mode,
    agent_version=agent_version,
    customer_id=userdata.customer.id if userdata.customer else None,
    telnyx_call_id=telnyx_call_id,
    telnyx_call_session_id=telnyx_call_session_id,
    langfuse_session_id=langfuse_session_id,
    session_start_time=session_start_time,
    session_end_time=session_end_time,
)
```

**Step 2: Commit**

```bash
git add src/agents/telephony/restaurant_agent.py src/services/call_service.py
git commit -m "feat(agent): pass SIP Call-ID and telnyx_call_session_id to call records

Fix nomenclature: session_id param now receives actual SIP Call-ID
instead of Telnyx call ID. Both telnyx_call_id (leg) and
telnyx_call_session_id (session) stored for recording lookup.

Refs #25, #39"
```

---

### Task 4: Write unit tests for the correlation flow

**Files:**
- Create: `tests/unit/test_call_correlation.py`

**Step 1: Write tests**

Test the key scenarios:
1. Telnyx webhook arrives first, then agent registers → match
2. Agent registers first, then Telnyx webhook arrives → match
3. Timing mismatch → no match
4. Phone number normalization

```python
"""Tests for call correlation service."""
import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.call_correlation_service import (
    CallCorrelationService,
    PendingTelnyxEvent,
    PendingLiveKitCall,
    CorrelationResult,
    MATCH_WINDOW_SECONDS,
)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    store = {}

    class MockRedis:
        async def get_json(self, key):
            return store.get(key)

        async def set_json(self, key, value, ttl=None):
            store[key] = value

        async def delete(self, key):
            store.pop(key, None)

        async def connect(self):
            return self

        async def scan_iter(self, match=None):
            import fnmatch
            pattern = match or "*"
            for key in list(store.keys()):
                if fnmatch.fnmatch(key, pattern):
                    yield key.encode() if isinstance(key, str) else key

    return MockRedis(), store


@pytest.fixture
def correlation_service(mock_redis):
    redis_mock, _ = mock_redis
    service = CallCorrelationService()
    service.cache = redis_mock
    return service


class TestPhoneNormalization:
    def test_normalize_e164(self):
        service = CallCorrelationService()
        assert service._normalize_phone("+15551234567") == "5551234567"

    def test_normalize_10_digit(self):
        service = CallCorrelationService()
        assert service._normalize_phone("5551234567") == "5551234567"

    def test_normalize_empty(self):
        service = CallCorrelationService()
        assert service._normalize_phone("") == ""


class TestTelnyxFirstMatch:
    """Telnyx webhook arrives before agent registers."""

    @pytest.mark.asyncio
    async def test_telnyx_then_livekit_matches(self, correlation_service):
        now = datetime.now(timezone.utc)

        # Step 1: Telnyx webhook arrives (no match yet)
        result = await correlation_service.handle_telnyx_call_initiated(
            call_leg_id="leg-123",
            call_session_id="session-456",
            call_control_id="ctrl-789",
            connection_id="conn-000",
            from_number="+15551234567",
            to_number="+15559876543",
            direction="inbound",
            occurred_at=now,
        )
        assert result is None  # No match yet

        # Step 2: Agent registers (should match)
        result = await correlation_service.register_livekit_call(
            call_id="call-abc",
            sip_call_id="sip-call-id-xyz",
            room_name="room-1",
            from_number="+15551234567",
            to_number="+15559876543",
            started_at=now + timedelta(seconds=5),
        )
        assert result is not None
        assert result.telnyx_call_leg_id == "leg-123"
        assert result.telnyx_call_session_id == "session-456"
        assert result.confidence > 0.9


class TestLiveKitFirstMatch:
    """Agent registers before Telnyx webhook arrives."""

    @pytest.mark.asyncio
    async def test_livekit_then_telnyx_matches(self, correlation_service):
        now = datetime.now(timezone.utc)

        # Step 1: Agent registers first (no match yet)
        result = await correlation_service.register_livekit_call(
            call_id="call-abc",
            sip_call_id="sip-call-id-xyz",
            room_name="room-1",
            from_number="+15551234567",
            to_number="+15559876543",
            started_at=now,
        )
        assert result is None  # No match yet

        # Step 2: Telnyx webhook arrives (should match)
        result = await correlation_service.handle_telnyx_call_initiated(
            call_leg_id="leg-123",
            call_session_id="session-456",
            call_control_id="ctrl-789",
            connection_id="conn-000",
            from_number="+15551234567",
            to_number="+15559876543",
            direction="inbound",
            occurred_at=now + timedelta(seconds=3),
        )
        assert result is not None
        assert result.telnyx_call_leg_id == "leg-123"
        assert result.call_id == "call-abc"


class TestTimingMismatch:
    """Calls outside the match window should not correlate."""

    @pytest.mark.asyncio
    async def test_timing_too_far_apart(self, correlation_service):
        now = datetime.now(timezone.utc)

        await correlation_service.handle_telnyx_call_initiated(
            call_leg_id="leg-123",
            call_session_id="session-456",
            call_control_id="ctrl-789",
            connection_id="conn-000",
            from_number="+15551234567",
            to_number="+15559876543",
            direction="inbound",
            occurred_at=now,
        )

        # Register 5 minutes later (outside 2-min window)
        result = await correlation_service.register_livekit_call(
            call_id="call-abc",
            sip_call_id="sip-xyz",
            room_name="room-1",
            from_number="+15551234567",
            to_number="+15559876543",
            started_at=now + timedelta(seconds=MATCH_WINDOW_SECONDS + 10),
        )
        assert result is None


class TestRecordingSaved:
    """Recording.saved webhook links to existing correlation."""

    @pytest.mark.asyncio
    async def test_recording_links_to_correlation(self, correlation_service):
        now = datetime.now(timezone.utc)

        # Create a correlation first
        await correlation_service.handle_telnyx_call_initiated(
            call_leg_id="leg-123",
            call_session_id="session-456",
            call_control_id="ctrl-789",
            connection_id="conn-000",
            from_number="+15551234567",
            to_number="+15559876543",
            direction="inbound",
            occurred_at=now,
        )
        await correlation_service.register_livekit_call(
            call_id="call-abc",
            sip_call_id="sip-xyz",
            room_name="room-1",
            from_number="+15551234567",
            to_number="+15559876543",
            started_at=now + timedelta(seconds=2),
        )

        # Recording arrives
        result = await correlation_service.handle_telnyx_recording_saved(
            call_leg_id="leg-123",
            call_session_id="session-456",
            recording_id="rec-999",
            recording_urls={"mp3": "https://example.com/rec.mp3"},
            duration_millis=60000,
        )
        assert result is not None
        assert result.telnyx_recording_id == "rec-999"
```

**Step 2: Run tests**

```bash
pytest tests/unit/test_call_correlation.py -v
```

**Step 3: Commit**

```bash
git add tests/unit/test_call_correlation.py
git commit -m "test: add unit tests for call correlation service

Covers both match orders (telnyx-first, livekit-first), timing
mismatch rejection, recording linkage, and phone normalization.

Refs #25, #39"
```

---

### Task 5: Update documentation

**Files:**
- Modify: `dev_docs/telnyx-recording-integration.md` (update architecture to reflect actual implementation)
- Modify: `src/agents/ARCHITECTURE.md` (remove known-issue section about missing wiring)

**Step 1: Update the architecture doc's known issues section**

In `src/agents/ARCHITECTURE.md`, update the known issues section to mark the correlation as implemented.

**Step 2: Update `dev_docs/telnyx-recording-integration.md`**

Update the "Key Files" table and "Call Flow" section to reflect that the agent now calls `register_livekit_call()`.

**Step 3: Commit**

```bash
git add dev_docs/telnyx-recording-integration.md src/agents/ARCHITECTURE.md
git commit -m "docs: update recording correlation docs to reflect wired implementation

Refs #25, #39"
```

---

### Task 6: Update GitHub issues

Comment on #25 and #39 with progress, and close them if all acceptance criteria are met after testing.

```bash
gh issue comment 25 --body "Implemented in feat/telnyx-recording-correlation branch. Agent now calls register_livekit_call() for Redis-based phone+timing correlation."
gh issue comment 39 --body "Fixed in feat/telnyx-recording-correlation branch:
- Agent calls register_livekit_call() after phone extraction (base.py)
- _extract_telnyx_call_id() kept as fallback if Redis unavailable
- Added telnyx_call_session_id column + migration
- SIP Call-ID now correctly stored (was using telnyx_call_id before)
- Unit tests for correlation flow added"
```
