---
title: "Architecture Documentation Consolidation Outline"
description: "Outline for consolidating architecture docs (Issue #10)."
---

# Architecture Documentation Consolidation Outline (Issue #10)

## Goal
Consolidate fragmented architecture documentation into a single, cohesive source of truth within `panbot-docs`.

## 1. Unified System Overview
- **High-Level Diagram**: Mermaid.js diagram of all components (Backend, Web, Desktop, Telephony, Printer).
- **Core Principles**: Multi-tenancy, Real-time first, Privacy-safe.
- **Component Roles**: Define the responsibility of each repo.

## 2. Shared Data Models & Contracts
- **OpenAPI Strategy**: How we use shared clients and avoid shape mismatches (#5, #82).
- **Real-time Event Schema**: Centrifugo channel patterns and JSON payloads.
- **Auth Contract**: Logto (Web/Owner) vs. Device/PIN (Staff/Desktop).

## 3. Deployment & CI/CD Patterns
- **Staging/Per-PR namespaces**: E2E infrastructure design (#87, #88).
- **Forensics/Observability**: RBAC for kubectl/helm forensics (#110).

## 4. Integration Guides
- **Payment Flow**: Stripe/Payment intents.
- **Telephony Flow**: LiveKit Agents + VAD + TTS.
- **Printer System**: Cloud-to-Local bridge.

## Proposed Action Plan
1. **Inventory**: Gather maintained `ARCHITECTURE.md` sources from `panbot`, `panbot-web`, and
   this documentation site.
2. **Standardization**: Use consistent Mermaid diagrams and markdown headers.
3. **Migration**: Promote validated technical details from current code and accepted decisions
   into `src/content/docs/architecture/`; archived plans are historical evidence, not a source of
   truth.
4. **Maintenance**: Establish a "docs-first" rule for new architecture changes.
