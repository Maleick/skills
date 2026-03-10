# Phase 8: Persistent Cache Engine - Research

**Researched:** 2026-02-26
**Domain:** Deterministic persistent cache behavior for unchanged-skill validation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Cache is optimization-only; correctness remains source-of-truth from current files/rules/profile context.
- Cache keying must include deterministic inputs that affect findings and invalidation.
- Cache behavior must be scope-aware for full vs changed-files mode.
- Scan outputs must surface cache usage metadata additively.
- Cache hit/miss paths over identical inputs must produce equivalent findings and summary contracts.

### Claude's Discretion
- Storage backend details (`sqlite` vs compact file index) as long as key/invalidation contracts hold.
- Internal module boundaries and helper placement.
- Exact wording of cache diagnostics and metadata lines.

### Deferred Ideas (OUT OF SCOPE)
- Shared/distributed cache backends.
- Advanced lifecycle commands (`inspect`, `prune`, targeted invalidation`) beyond baseline.
- Cache analytics dashboarding.
</user_constraints>

<research_summary>
## Summary

The existing validator already has deterministic scope and reporting contracts. Phase 8 should preserve these contracts by introducing cache as a strict internal optimization layer with explicit parity guarantees. The safest approach is read-through/write-through cache with deterministic key inputs and fallback-to-recompute behavior on any key mismatch or cache corruption.

Phase 8 should treat cache metadata as additive scan context and avoid any cache-driven branching that changes ordering or severity semantics. Cache diagnostics should be observable but not noisy, and CI behavior should remain deterministic regardless of cache state.

**Primary recommendation:** implement a cache module with deterministic fingerprint keys, integrate at skill-level validation boundaries, and lock parity/invalidation behavior with subprocess and unit regression tests.
</research_summary>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Cache Behind Deterministic Contract Boundary
- Keep cache internals isolated from output ordering and severity logic.
- Return the same logical findings regardless of cache path.

### Pattern 2: Fingerprint-First Invalidation
- Invalidation based on content/profile/rule-version fingerprint inputs.
- Avoid relying only on timestamps.

### Pattern 3: Safe Fallback on Any Cache Fault
- Cache errors degrade to recompute + warning, not hard failure.
- Preserve exit semantics and result trust.
</architecture_patterns>

<cache_contract>
## Cache Contract Recommendations

Recommended cache metadata block in scan payload:

```json
"cache": {
  "enabled": true,
  "mode": "read-write",
  "hits": 0,
  "misses": 0,
  "invalidations": 0,
  "errors": 0
}
```

Key identity should include:
- Skill key/path
- Relevant file content fingerprint
- Policy profile identity
- Rule/schema version indicator
- Scan mode scope context when applicable

Fallback rules:
- Miss/mismatch/corruption -> recompute from source.
- Cache never suppresses fresh validation if key inputs changed.
</cache_contract>

<test_strategy>
## Test Strategy

1. Parity tests
- Same inputs with cache enabled/disabled produce equal findings and totals.
- Repeated runs stabilize on cache hits without changing payload semantics.

2. Invalidation tests
- File content changes invalidate affected entries only.
- Profile change invalidates impacted entries deterministically.
- Rule/schema version change invalidates prior cache entries.

3. Scope behavior tests
- Changed-files mode only uses in-scope keys.
- Full-scan mode updates broader cache without affecting scoped decision logic.

4. Fault tolerance tests
- Corrupt cache storage triggers recompute and warning path.
- Exit code behavior remains unchanged.
</test_strategy>

<sources>
## Sources

### Primary
- `/opt/skills/.planning/phases/08-persistent-cache-engine/08-CONTEXT.md`
- `/opt/skills/.planning/research/SUMMARY.md`
- `/opt/skills/.planning/ROADMAP.md`
- `/opt/skills/.planning/REQUIREMENTS.md`
- `/opt/skills/tools/skill_audit/cli.py`
- `/opt/skills/tools/skill_audit/scanner.py`
- `/opt/skills/tools/skill_audit/indexing.py`
- `/opt/skills/tools/skill_audit/tests/`

</sources>

---

*Phase: 08-persistent-cache-engine*
