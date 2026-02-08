---
title: Printer System
description: Desktop printer discovery, printing, and cache architecture.
---

## Overview

The printer system runs in the Tauri Rust backend, providing network discovery, print job execution, and local caching with backend sync.

## Printer Discovery

Two discovery methods run concurrently:

| Method | Target | Protocol | Port |
|--------|--------|----------|------|
| Network scan | Thermal printers | Raw TCP | 9100 |
| mDNS/Bonjour | Office printers | IPP/IPPS | 631 |

**Identity**: Printers are uniquely identified by MAC address. Discovery deduplicates by MAC, merging metadata from multiple sources.

**Platform support**:
- Linux/macOS: `ip -o -4 addr show` for network ranges, CUPS for IPP
- Windows: PowerShell Get-NetIPAddress, Windows Print API

## Print Processing

| Printer Type | Protocol | Format |
|-------------|----------|--------|
| Thermal | ESC/POS via TCP:9100 | ESC/POS commands |
| Office | IPP via CUPS:631 | IPP print jobs |

### Template System

Templates use Mustache syntax with ESC/POS formatting tokens:

```
[[align:center]][[size:large]][[bold:on]]
Order #{{order_number}}
[[bold:off]][[size:normal]][[align:left]]
{{#items}}
{{name}} x{{quantity}} ${{price}}
{{/items}}
```

**Supported tokens**: `[[size:normal|medium|large|wide|tall]]`, `[[font:A|B]]`, `[[bold:on|off]]`, `[[align:left|center|right]]`

## Print Queue

Background job queue with retry logic:

| Setting | Value |
|---------|-------|
| Max retries | 3 |
| Backoff | Exponential (2^(attempts-1) seconds) |
| Job delay | 100ms between jobs |
| Thread safety | Arc\<Mutex\> |

## Printer Cache

Smart local cache with event-driven backend sync:

| Feature | Details |
|---------|---------|
| Storage | JSON files via Tauri Store plugin (`printers_{business_id}.json`) |
| Sync strategy | Per-key 2-minute debounce timers |
| Sync method | Latest-state-only (load current state at sync time) |
| Network calls | Delegated to JS layer via Tauri events |
| Recovery | Fetch from backend with 30-second timeout |

### Sync Flow

```
Local save → Queue sync event → Start/restart 2-min timer
    → Timer expires → Load current state → Emit to JS
    → JS calls backend API → Confirm sync
```

## Template Cache

Stored in `template_cache.json` with section-level configuration:

| Key Pattern | Content |
|-------------|---------|
| `templates_business_{id}` | HashMap of templates by template ID |
| `template_assignments_business_{id}` | Printer MAC → template ID mapping |

Template types: `receipt`, `kitchen`, `report`

## Detailed Documentation

- `apps/desktop/docs/printer-architecture.md` — Full printer system design
- `apps/desktop/TEMPLATE_CACHE_GUIDE.md` — Template cache implementation guide
- `apps/desktop/ARCHITECTURE.md` — Desktop app architecture overview
