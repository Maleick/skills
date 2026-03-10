# Phase 8: Persistent Cache Engine - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 adds persistent cache behavior for unchanged-skill validation paths so repeated runs are faster while preserving identical correctness and output contracts. Scope is limited to cache enablement, invalidation correctness, and parity guarantees. It does not add distributed cache or dashboard features.

</domain>

<decisions>
## Implementation Decisions

### Cache behavior and trust model
- Cache is an optimization layer only; it is never authoritative over correctness.
- On cache miss, key mismatch, or integrity failure, the validator recomputes from source and continues normally.
- Cache behavior applies across default, CI, and changed-files modes, with explicit bypass control (`--no-cache`) for debugging and parity checks.

### Cache key and invalidation contract
- Cache identity must include deterministic inputs that affect findings: relevant skill file content fingerprint, selected policy profile identity, and rule schema/version context.
- Invalidation is content-first (hash/fingerprint), not timestamp-first.
- Any policy-profile change or rule-version change invalidates affected cached entries.

### Scope-aware cache usage
- Changed-files mode only queries/updates cache for in-scope skills.
- Full-scan mode can reuse and refresh cache across the full catalog.
- Out-of-scope cache entries are ignored for gate/report decisions in scoped runs.

### Output and observability requirements
- Scan metadata should include cache usage summary (`cache_mode`, `cache_hits`, `cache_misses`, `cache_invalidations`) so operators can audit behavior.
- Cache hit and cache miss runs over identical inputs must produce equivalent findings and deterministic summaries.
- Cache corruption or unreadable cache state should emit actionable runtime warning text but fall back safely to recompute.

### Claude's Discretion
- Storage backend details (sqlite schema vs compact file index) as long as deterministic keys, parity, and fallback guarantees are preserved.
- Exact CLI wording for cache metrics and warning lines.
- Internal module boundaries (`cache.py` split vs integrated helpers) if tests and contracts stay clear.

</decisions>

<specifics>
## Specific Ideas

- Prefer repository-local cache location under `.planning/cache/` to keep lifecycle tied to planning/runtime context.
- Keep deterministic output contracts unchanged by default and add cache metadata additively.
- Prioritize parity test matrix early: uncached baseline vs cached run vs forced bypass.

</specifics>

<deferred>
## Deferred Ideas

- Shared/distributed cache backends across machines.
- Advanced cache lifecycle commands (`inspect`, `prune`, profile-targeted invalidation`) beyond baseline scope.
- Historical dashboard visualization for cache effectiveness.

</deferred>

---

*Phase: 08-persistent-cache-engine*
*Context gathered: 2026-02-26*
