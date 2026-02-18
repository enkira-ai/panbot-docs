# Search Specification: panbot-docs Full-Text Search

- **Status:** Draft (Stage 2: Refinement & Structure)
- **Issue:** #4 (Implement full-text search)
- **Stakeholders:** @Stellar-Hogarthian (Owner), @stellar-chiron (Docusaurus integration), @captain-nemo-bot (Testing/Analytics)

## 1. Context & Objective
The goal is to provide a comprehensive, low-latency search experience across all documentation content within the `panbot-docs` Docusaurus site. This enables agents and humans to instantly discover technical specifications, architectural decisions, and research across 120+ markdown files.

## 2. Technical Approach
We will use `docusaurus-search-local` (based on Lunr.js) to provide a self-hosted, offline-ready search index.

### Key Components:
- **Search Engine:** Lunr.js (via `docusaurus-search-local` plugin).
- **Indexing:** Automated indexing of all `.md` and `.mdx` files in `docs/` and `blog/`.
- **UI:** Standard Docusaurus search bar positioned in the **top-right** of the navbar.
- **Filtering:** Implementation of category/repository tags in the index to allow faceted search.
- **Analytics Bridge:** A custom React hook will intercept zero-result events from the Lunr index and `POST` them to `/api/v1/docs/search-metrics` (managed by the internal dashboard backend).

## 3. Requirements

### Functional:
- [ ] **Keyword Search:** High-relevance matching for single and multi-word queries.
- [ ] **Highlighting:** Visual highlighting of search terms in the results snippets.
- [ ] **Faceted Filtering:** Ability to filter results by category (e.g., Architecture, API, Research) based on **directory-level tagging**.
- [ ] **Low Latency:** Average search response time <= 1 second.

### Analytics & Observability:
- [ ] **Query Tracking:** Log popular search terms (to identify core interests).
- [ ] **Failed Query Tracking:** Log queries with zero results (to identify "dead zones" and content gaps for Issue #6).
- [ ] **Integration:** (Pending @captain-nemo-bot feedback) Defaulting to simple server-side logging/GitHub issue feed for failed queries.

## 4. Acceptance Criteria
1. Search returns relevant results for "auth flow", "deployment", and "OpenAPI".
2. Search results show snippets with highlighted terms.
3. Filtering by "API" narrows results to only API-related docs.
4. "No results found" triggers an internal log event.

## 5. Implementation Checklist
- [ ] Install `docusaurus-search-local` dependency.
- [ ] Configure `docusaurus.config.js` with repository-specific tags.
- [ ] Verify indexing pipeline during production build.
- [ ] Implement analytics hook for zero-result queries.
- [ ] Perform reader testing with "Fresh Claude" instances.
