# Langfuse Tracing Fix & E2E Agent Testing

**Date**: 2026-02-15
**Status**: Ready for implementation
**Branch**: Create `feature/langfuse-e2e-testing` from `dev`
**Related commits on dev**: `1e81e8f`, `da4b8cc`, `7d93251` (hotfixes for structured output)

## Background

Three production errors were hotfixed on `dev`:
1. `include_reasoning` is not a valid OpenAI/LiteLLM parameter — removed entirely
2. OpenAI SDK v2.x requires `parse()` not `create()` for BaseModel `response_format`
3. LiteLLM proxy rejects unknown params even via `extra_body`

Two remaining work streams:
- **Stream A**: Fix Langfuse tracing (revert PR #117 proxy-level approach → LiveKit-only + client-side wrappers)
- **Stream B**: Build E2E agent tests using LiveKit's built-in testing framework

## Stream A: Langfuse Tracing Fix

### Context

PR #117 moved Langfuse tracing to the LiteLLM proxy level via `success_callback: ["langfuse"]`. This works for proxy-routed calls but:
- Doesn't capture LiveKit's built-in conversation/STT/TTS spans
- Creates session grouping issues (proxy doesn't know room name without metadata)
- Will double-log if we also use client-side Langfuse

**Decision**: Keep LiveKit OTEL tracing (already working in `base.py:1224-1257`) as the primary trace source. For sidecar LLM calls (post_call_processor, nano_helper, tool_backup_observer), use `langfuse.openai.AsyncOpenAI` wrapper with session-level grouping.

### Steps

#### A1. Remove proxy-level Langfuse callbacks

**File**: `infrastructure/litellm/panbot_config.yaml` (lines 85-86)

Remove:
```yaml
success_callback: ["langfuse"]
failure_callback: ["langfuse"]
```

This prevents double-logging when client-side Langfuse wrapper is active.

#### A2. Clean up `include_reasoning` from prompt config

**File**: `prompts/restaurant_agent.yaml` (line 123)

Remove:
```yaml
include_reasoning: true
```

Only `enabled` and `effort` are valid reasoning config keys.

#### A3. Swap `AsyncOpenAI` → `langfuse.openai.AsyncOpenAI` in sidecar callers

**Files to modify**:

1. **`src/agents/telephony/post_call_processor.py`** (line 286)
   - Change `from openai import AsyncOpenAI` → `from langfuse.openai import AsyncOpenAI`
   - Remove the manual `metadata` param injection (lines 279-282)
   - Instead, pass `session_id=room_name` and `trace_name="post-call-processing"` to the client constructor or via `langfuse_kwargs`
   - The `langfuse.openai` wrapper auto-captures all LLM calls with proper session grouping

2. **`src/agents/telephony/nano_helper.py`** (line 13)
   - Change `from openai import AsyncOpenAI` → `from langfuse.openai import AsyncOpenAI`
   - The lazy `_nano_client` needs session context. Either:
     - (a) Create client per-call with session_id, or
     - (b) Use `@observe()` decorator on the generate function and `propagate_attributes(session_id=room_name)`
   - Option (b) recommended — add `@observe(name="nano-helper")` to `generate_response()` function

3. **`src/agents/telephony/tool_backup_observer.py`** (line 43)
   - Change `from openai import AsyncOpenAI` → `from langfuse.openai import AsyncOpenAI`
   - Add `@observe(name="tool-backup-observer")` to the main check method

**Import pattern for all files**:
```python
from langfuse.openai import AsyncOpenAI
from langfuse.decorators import observe
```

**Session propagation**: In the agent's `_setup_langfuse()` or at session start, call:
```python
from langfuse.decorators import langfuse_context
langfuse_context.configure(session_id=ctx.room.name)
```

This ensures all `@observe()` calls in that thread inherit the session ID.

#### A4. Simplify `langfuse_metadata.py`

**File**: `src/agents/telephony/langfuse_metadata.py`

This helper was built for the proxy-level metadata approach. With client-side `langfuse.openai` wrapper, it's no longer needed. Either:
- Delete it entirely and remove imports from `nano_helper.py`, `tool_backup_observer.py`, `post_call_processor.py`
- Or keep it as a thin wrapper if there's a need for consistent tag/metadata building

**Recommendation**: Delete it. The `@observe()` decorator handles naming and the `langfuse_context` handles session grouping.

#### A5. Verify `_setup_langfuse()` in base.py is unchanged

**File**: `src/agents/telephony/base.py` (lines 1224-1257)

This is the LiveKit OTEL integration — keep it as-is. It handles:
- STT/TTS/LLM spans from LiveKit's pipeline
- Session ID via `metadata={"langfuse.session.id": ctx.room.name}`
- Flush on shutdown

No changes needed here.

#### A6. Add Langfuse connectivity unit test

**File**: Create `tests/unit/test_langfuse_integration.py`

```python
"""Verify Langfuse SDK can authenticate and create traces."""
import pytest
import os

@pytest.mark.integration
def test_langfuse_connectivity():
    """Verify Langfuse credentials work and SDK can create a trace."""
    from langfuse import Langfuse

    client = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )

    # Create a test trace and verify it succeeds
    trace = client.trace(name="ci-connectivity-test", session_id="test-session")
    trace.generation(name="test-generation", input="hello", output="world")
    client.flush()

    # If we get here without exception, connectivity works
    assert trace.id is not None

@pytest.mark.integration
def test_langfuse_openai_wrapper():
    """Verify langfuse.openai.AsyncOpenAI wrapper initializes correctly."""
    from langfuse.openai import AsyncOpenAI

    client = AsyncOpenAI(
        base_url=os.getenv("LITELLM_BASE_URL", "https://router.panbot.ai/v1"),
        api_key=os.getenv("LITELLM_API_KEY", "dummy"),
    )
    assert client is not None
```

#### A7. Commit Langfuse work

Commit message: `fix(observability): revert to LiveKit-only Langfuse tracing with client-side wrappers`

Files to stage:
- `infrastructure/litellm/panbot_config.yaml`
- `prompts/restaurant_agent.yaml`
- `src/agents/telephony/post_call_processor.py`
- `src/agents/telephony/nano_helper.py`
- `src/agents/telephony/tool_backup_observer.py`
- `src/agents/telephony/langfuse_metadata.py` (deleted)
- `tests/unit/test_langfuse_integration.py` (new)

---

## Stream B: E2E Agent Testing

### Context

LiveKit Agents SDK v1.3.10 has a first-party testing framework:
```python
from livekit.agents import AgentSession
result = await agent_session.run(user_input="I'd like to place an order")
# result.text_output, result.tool_calls, etc.
```

Key features:
- Text-only mode (no audio pipeline needed)
- `mock_tools()` for isolating tool behavior
- `capture_run=True` for detailed interaction logs
- `RunResult` with assertions on output, tool calls, conversation flow

### Existing Test Infrastructure to Research

Before writing new tests, research these existing files:

1. **`scripts/agent_prompt_test.py`** — Existing prompt testing script. Check if it uses LiveKit's framework or a custom approach. Determine if it should be migrated to the new E2E framework or kept separate.

2. **`scripts/run_agent_prompt_regression_suite.py`** — Regression suite runner. Check what test scenarios it covers and whether they overlap with the E2E tests we plan to write.

3. **`data/test_business_config.json`** — Test business configuration. **Must be updated** from the current dev database (Shokudo Development business) because multiple migrations have run since it was last updated (language_preferences, optional_phone, etc.). Connect to dev DB and export the current config.

4. **`tests/` folder** — Scan all existing tests for:
   - Tests that are outdated or broken
   - Tests that duplicate what E2E tests would cover
   - Tests that should be consolidated
   - Test fixtures that can be reused

### Steps

#### B1. Research existing test infrastructure

Run a subagent to:
- Read and analyze `scripts/agent_prompt_test.py` and `scripts/run_agent_prompt_regression_suite.py`
- Connect to dev DB and export Shokudo Development business config to update `data/test_business_config.json`
- Scan `tests/` folder for outdated, broken, or overlapping tests
- Write findings as a GitHub issue with a detailed plan

**To update test_business_config.json from dev DB**:
```bash
# Connect to dev DB (credentials in .env after make sync-env)
# Query: SELECT config FROM businesses WHERE name = 'Shokudo Development'
# Or use the API: GET /api/v1/businesses/{id}/config
```

#### B2. Create E2E test directory structure

```
tests/
  evals/
    conftest.py          # Shared fixtures (business config, agent session factory)
    test_greeting.py     # Greeting flow tests
    test_ordering.py     # Order placement flow
    test_review_order.py # Order review structured output
    test_end_call.py     # Call ending flow
    test_multilingual.py # Language switching
```

#### B3. Build fixtures

**`tests/evals/conftest.py`**:
- Load `data/test_business_config.json` as fixture
- Create `RestaurantUserData` factory (menu, business config, operating hours)
- Create `agent_session` fixture that bootstraps `RestaurantAgent` in text-only mode
- Mock external services (Redis, DB, event bus) but keep LLM calls real (through proxy)

#### B4. Write core E2E test scenarios

Priority order:
1. **Greeting test** — Agent responds with restaurant name, asks how to help
2. **Simple order** — "I'd like a California Roll" → agent confirms item, asks for more
3. **Review order** — After adding items, `review_order` tool fires → structured output works without error
4. **End call** — `end_call` tool fires → structured output extraction works
5. **Error resilience** — Malformed user input, unavailable menu items

Each test should verify:
- No exceptions thrown (the primary goal)
- Reasonable response content (not empty, not error messages)
- Expected tool calls fired
- Structured output parsed successfully

#### B5. Run tests and debug

```bash
pytest tests/evals/ -v --tb=long
```

Fix any remaining issues discovered by the E2E tests. This is where we verify:
- Langfuse tracing works end-to-end
- Structured output with `parse()` works correctly
- No SDK compatibility issues remain

#### B6. Add CI integration

Add `evals` pytest marker and update CI to run E2E tests:
```bash
pytest tests/evals/ -m evals --timeout=60
```

---

## GitHub Issue

Create a tracking issue with title: `[telephony] fix: Langfuse tracing + E2E agent testing`

Labels: `backend`, `testing`, `sprint-23`

Body should reference:
- The three hotfix commits (`1e81e8f`, `da4b8cc`, `7d93251`)
- PR #117 (Langfuse proxy approach being reverted)
- The two streams (A: Langfuse, B: E2E testing)
- Acceptance criteria for each stream

---

## Execution Order

```
1. Create feature branch from dev
2. Stream A: Langfuse fix (A1-A7) → commit
3. Stream B research (B1) → may run in parallel with A
4. Stream B implementation (B2-B6) → after A is committed and B1 research is done
5. Run full test suite to verify everything
6. PR to dev
```

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Langfuse tracing approach | LiveKit OTEL + client-side `langfuse.openai` wrapper | Captures all spans (STT/TTS/LLM) under one session |
| Sidecar call tracing | `@observe()` + session-level grouping | True child spans not achievable across threads; session grouping is Langfuse's recommended pattern |
| Testing framework | LiveKit's built-in `AgentSession.run()` | First-party, text-only, no audio pipeline needed |
| Test philosophy | E2E over unit tests | User explicitly requested not to "lock down" individual methods; focus on session-level correctness |
| `include_reasoning` | Removed entirely | Not supported by OpenAI API or LiteLLM proxy |
| `langfuse_metadata.py` | Delete | Replaced by `langfuse.openai` wrapper + `@observe()` |
| LiteLLM proxy callbacks | Remove `success_callback: ["langfuse"]` | Prevents double-logging with client-side wrapper |

## Dependencies

- `langfuse` Python package (check if already in `pyproject.toml`)
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` env vars (already configured)
- `LITELLM_API_KEY` for proxy access (already configured)
- LiveKit Agents SDK >= 1.3.10 (already installed)

## Files Reference

| File | Action | Stream |
|------|--------|--------|
| `infrastructure/litellm/panbot_config.yaml` | Remove Langfuse callbacks | A |
| `prompts/restaurant_agent.yaml` | Remove `include_reasoning: true` | A |
| `src/agents/telephony/post_call_processor.py` | Swap to `langfuse.openai.AsyncOpenAI` | A |
| `src/agents/telephony/nano_helper.py` | Swap to `langfuse.openai.AsyncOpenAI` | A |
| `src/agents/telephony/tool_backup_observer.py` | Swap to `langfuse.openai.AsyncOpenAI` | A |
| `src/agents/telephony/langfuse_metadata.py` | Delete | A |
| `src/agents/telephony/base.py` | No changes (keep OTEL setup) | A |
| `tests/unit/test_langfuse_integration.py` | Create | A |
| `data/test_business_config.json` | Update from dev DB | B |
| `tests/evals/conftest.py` | Create | B |
| `tests/evals/test_*.py` | Create | B |
| `scripts/agent_prompt_test.py` | Research, possibly consolidate | B |
| `scripts/run_agent_prompt_regression_suite.py` | Research, possibly consolidate | B |
