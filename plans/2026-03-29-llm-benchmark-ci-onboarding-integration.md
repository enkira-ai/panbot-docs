# RFC: LLM Benchmark CI Gate + Onboarding Integration Test

**Status:** Draft — needs team discussion  
**Author:** Developer  
**Date:** 2026-03-29  
**Related:** Issue #215, Issue #193

---

## Problem

LLM upgrades are like database migrations: they change the behavior of the system and need to be validated before promotion to production. Right now we have no gate.

Two specific gaps:

1. **Benchmark harness drifts from production** — the harness runs infrequently (every few months when a new model appears). Between runs, production context assembly changes (prompt templates, tool definitions, menu injection strategy). By the time we run the benchmark, the harness is testing against degraded context, not real production conditions. This invalidates results. (Discovered 2026-03-28: menu was missing, tools were wrong — all benchmark scores from that session are invalid.)

2. **No per-customer validation** — when we onboard a new restaurant, we have no automated check that the agent works correctly with that restaurant's specific menu and configuration. A customer with unusual menu items or missing config fields could silently fail.

---

## Proposal

### Phase 1 (now): Benchmark CI gate — dev branch as source of truth

**Mechanism: CI-generated snapshot**

On every merge to `dev`, CI:
1. Runs `src/benchmark/export_context.py` — renders the full production context (system prompt + menu injection + tool definitions) using the actual production code paths
2. Commits the output to `tests/fixtures/benchmark_context.json`
3. Runs `scripts/run_agent_prompt_regression_suite.py` against that snapshot
4. Blocks merge if pass rate < 90%

The benchmark harness loads the snapshot instead of assembling context itself. This guarantees the harness is always testing real production conditions.

**Why dev branch, not main?**  
Production has no real users yet. Dev is our working standard. Once we have production users, we apply the same gate to main.

**Affected files:**
- `src/benchmark/export_context.py` (new)
- `tests/fixtures/benchmark_context.json` (new, auto-updated by CI)
- `scripts/run_agent_prompt_regression_suite.py` (load snapshot, not custom context assembly)
- `.github/workflows/ci.yml` (add export + benchmark step)

### Phase 2 (future): Per-customer onboarding integration test

When a new restaurant is onboarded, automatically run a small smoke test suite against their specific menu and configuration.

**5 core scenarios (fixed, parameterized by menu):**
1. Order a real menu item → agent confirms it
2. Order something not on menu → agent declines
3. Ask for the total → `review_order` tool called
4. Say goodbye → `end_call` tool called
5. Mention an allergy → `transfer_to_staff` called

This runs as part of the onboarding flow. If it fails, we catch configuration issues before the customer goes live.

---

## Open Questions for Team Discussion

1. **Pass rate threshold:** 90% for dev merge gate — too strict, too loose? We saw gpt-4.1-mini at ~95% with correct context. What's the floor?

2. **Snapshot commit strategy:** Auto-commit the snapshot in CI (means CI pushes to dev on every merge). Alternative: require snapshot to be manually committed before PR merge. Which is less disruptive?

3. **Onboarding smoke test timing:** Run at onboard time (blocking), or run async and alert if it fails? What's the right behavior if it fails — block onboarding or just alert?

4. **Test data:** The benchmark uses Shokudo's menu. Should we keep a set of canonical test restaurants for benchmark purposes, or use a synthetic menu that covers edge cases?

5. **Multi-tenant benchmark:** As we add more customers, should we run the benchmark against multiple menus or just the canonical test config?

---

## Not in scope

- Changing the 28 benchmark scenarios themselves (separate discussion)
- Full E2E testing with real LiveKit/Telnyx (that's the E2E infra work, #145)
- Automated LLM selection (human still decides which model to promote)
