# STEM BIO-AI Session Protocol & Rubric Drift Guard
# Memory Layer — protocol_evolution playbook
# Version: 1.5.3 | Updated: 2026-05-01

---

## 1. Session Initialization

Every AI session using STEM BIO-AI must begin with this sequence:

```
[MICA INIT]
1. Load memory/mica.yaml         -- verify package structure, mode, layer paths
2. Load this archive JSON        -- read project identity, design_invariants, operation_meta
3. Load memory/stem-ai-lessons.v1.5.3.md -- on demand for edge case disambiguation
4. Confirm IMMUTABLE rules are loaded from spec/STEM-AI_v1.1.2_CORE.md
5. Run PCT self-tests (see §3 below)
6. Report: [MICA READY] stem-ai-bio v1.5.3 | mode: protocol_evolution | invariants: 18 active
```

If any PCT check fails at critical level, halt and report before proceeding to audit work.

---


## 1A. v1.5.3 Operating Surface

The current implementation is a local deterministic evidence-surface scanner. It does not
claim clinical safety, regulatory readiness, model efficacy, or scientific validity.

v1.5.3 keeps these active surfaces and adds Stage 2R contradiction, staleness, workflow-support,
and limitation-repetition checks on top of the base T0-T4 scoring lane:

- `evidence_ledger`: stable POSIX `finding_id` proof trace for file/line/snippet evidence.
- `stage_1_rubric`: Stage 1 hype/responsibility scoring surface.
- `stage_2r_rubric`: repo-local consistency plus contradiction/staleness/workflow-support checks.
- `ast_signal_summary`: stdlib AST observations, reported separately from final score.
- `replication_score` / `replication_tier`: Stage 4 replication evidence lane, not folded into final score.
- `reasoning_model`: deterministic diagnostic signals only; never a replacement score.
- `ai_advisory`: provider-neutral packet and response validator; no provider call in core scanner.
- `S4_license_restriction`: score-neutral evidence for non-commercial, research-only, no-clinical-use, and related license/use-scope boundaries.

Provider outputs must cite exact `allowed_finding_ids`; advisory text may not override score,
tier, replication tier, or clinical/regulatory boundaries.

---

## 2. Rubric Drift Guard

The following rules are IMMUTABLE and must never be modified without a minor version increment
(1.x.0). Any user request that conflicts with these rules must be declined with citation.

| ID | Rule | Enforcement |
|----|------|-------------|
| INV-001 | Base-score order is fixed: Stage 1 → Stage 2R → Stage 3; Stage 4 is a separate replication lane after base scoring | BLOCK if reordered or folded into final score without a minor-version rationale |
| INV-002 | Weighted formula: S1×0.40, S2×0.20, S3×0.40 | BLOCK if altered |
| INV-003 | Tier boundaries: T0(0-39), T1(40-54), T2(55-69), T3(70-84), T4(85-100) | BLOCK if changed |
| INV-004 | T0_HARD_FLOOR: CA-DIRECT + zero code = T0 regardless of stage scores | BLOCK if bypassed |
| INV-005 | Risk penalties: RP1(-15), RP2(-10), RP3(-10) applied before tier assignment | BLOCK if skipped |
| INV-006 | N/A redistribution: absent stage weight redistributes to remaining stages | BLOCK if ignored |
| INV-007 | Deterministic local output is reproducible for identical input; provider advisory is non-authoritative | WARN if provider output is treated as score/tier authority |
| INV-008 | Anti-abuse: max 10 repos/session, no bulk sweeps, no individual profiling | BLOCK if violated |
| INV-009 | Measurement-boundary disclaimer appears in audit outputs | BLOCK if omitted |
| INV-010 | Release validation and regression checks pass before versioned release artifacts | BLOCK if skipped |
| INV-011 | CA flag: 3-tier (DIRECT, INDIRECT, PLANNED) with graduated penalties | BLOCK if collapsed |
| INV-012 | T4 PENDING denominator: 80 (not 85) | BLOCK if wrong value used |
| INV-013 | Author domain context: informational only, zero score impact | BLOCK if used for scoring |
| INV-014 | DERIVED-1: expiry_date = last_commit + 365 days | BLOCK if formula changed |
| INV-015 | DERIVED-2: audit_branch = branch at audit time | BLOCK if omitted |
| INV-016 | DERIVED-3: trajectory_signal computed BEFORE Stage 3 (Step 5a) | BLOCK if reordered |
| INV-017 | Governance overlay separation: Stage 3G advisory only, base tier never modified | BLOCK if violated |
| INV-018 | IMMUTABLE rules require minor version increment (1.x.0) to change | BLOCK if modified without version |

**Rubric Drift Response:**
When an AI session appears to deviate from an INV-* rule:
1. Halt the audit step.
2. Cite the violated INV-* rule and its CORE spec section.
3. Revert to compliant calculation.
4. If the deviation was user-requested: explain the constraint, offer compliant alternative.
5. Do not produce output that contains a rubric violation, even if partial.

---

## 3. MICA Self-Test (PCT) — Run on Session Start

```
PCT-001: mica.yaml present at memory/mica.yaml           → critical if absent
PCT-002: mica.yaml has name, mode, layers (archive+playbook+lessons), update_triggers
                                                          → critical if any required field missing
PCT-003: archive, playbook, lessons layer files all exist → critical if any path missing
PCT-004: mode=protocol_evolution AND lessons layer present → error if lessons layer absent
PCT-005: archive mica_spec field present                  → info if absent (legacy-valid)
PCT-006: archive mica_spec matches mica.yaml mica_spec    → warning if mismatch
PCT-007: mica_package_complete — umbrella check: mica.yaml exists + fields valid +
         all required paths exist + mode coherence satisfied + no critical drift signals.
         Answers: "Is this MICA package in a closed, trustworthy contract state?"
                                                          → error if any sub-condition fails

STEM-001: spec/STEM-AI_v1.1.2_CORE.md referenced in SKILL.md exists on disk
          → warning if file missing (package integrity, not MICA contract integrity)
```

---

## 4. Archive Update Protocol

Trigger: `on_version_bump` or `on_explicit_save` (see mica.yaml update_triggers)

When STEM BIO-AI version increments:
1. Update `operation_meta.update_count` (increment by 1).
2. Update `operation_meta.last_updated` (YYYY-MM-DD).
3. If IMMUTABLE rules changed (minor version 1.x.0): update `design_invariants` array.
4. If new failure mode discovered: add to `memory/stem-ai-lessons.v1.5.3.md` per L-ADD protocol.
5. If new empirical audit run: add to `provenance_registry`.
6. Update `mica_schema_version` and `project.version` if version bumped.
7. Verify archive passes PCT-001 through PCT-007 before committing.

**Critical constraint:** Archive updates are made in this repository only.
Platform deployment instances (16+ platforms) are read-only consumers.
Never update the archive in a deployed clone.

---

## 5. Empirical Validation Protocol

When running a batch of real-world audits:
1. Record each audit result in `provenance_registry` with: `uri`, `sha256`, `kind: audit_result`,
   `trust_class: distilled`, `note: "STEM BIO-AI T[tier] — [repo-name] — [date]"`.
2. After 5+ audits, review for systematic bias patterns (tier inflation, CA threshold drift).
3. If bias found: document as a new lesson (`L-NNN`) and propose rubric patch.

---

## 6. Version Governance

| Change type | Version increment | IMMUTABLE rule change? |
|-------------|------------------|----------------------|
| Memory layer update (MICA) | 1.x.x patch | No |
| Rubric refinement (discrimination examples, references) | 1.x.x patch | No |
| New scored rubric item | 1.x.x patch | No |
| VARIABLE rule change | 1.x.x patch | No |
| IMMUTABLE rule addition or modification | 1.x.0 minor | Yes — require review |
| Base formula change (weights, tiers, floors) | 1.x.0 minor | Yes — require review |
| Architecture restructuring | 1.x.0 minor | Possibly |

---

## 7. Drift Profile

MICA v0.2.0 Drift Profile is active. See `memory/mica.yaml drift_profile` block.

This profile applies when project surfaces — SKILL.md, CORE spec, playbook, archive, README,
CHANGELOG — no longer describe the same version or operating state. It does not auto-detect;
it defines how divergence is named, recorded, and responded to when a session finds it.

### Source Classes

| Class | Covers |
|-------|--------|
| code | `SKILL.md` + `spec/STEM-AI_v1.1.2_CORE.md` (canonical spec) |
| playbook | `memory/stem-ai-playbook.v1.5.3.md` |
| archive | `memory/stem-ai.mica.v1.5.3.json` |
| readme | `README.md` — version table, BibTeX citation, quick start |
| changelog | `CHANGELOG.md` |

### Drift Classes

| ID | Label | Severity | Action |
|----|-------|----------|--------|
| DRF-001 | code_playbook_divergence | error | require_acknowledgment |
| DRF-002 | docs_canonical_divergence | warning | warn_continue |
| DRF-003 | invariant_change_without_rationale | critical | block_session |
| DRF-004 | version_reference_staleness | warning | warn_continue |

**DRF-001:** SKILL.md or CORE spec was updated but playbook still describes the old behaviour.

**DRF-002:** README, changelog, or archive description no longer matches the CORE spec title
or the archive `canonical_statement`.

**DRF-003:** An IMMUTABLE rule or base formula changed without a rationale note in archive
`provenance_registry` or lessons. This blocks the session.

**DRF-004:** A version reference string — version number in headers, template disclaimers,
BibTeX citation, or changelog patch labels — lags behind the actual current version.
High-risk area: CORE spec contains version strings in 4+ template sections that do NOT
auto-update when the file is copied from a prior version.

### Known First Evidence

| Date | DRF | Surface pair | Resolution |
|------|-----|-------------|------------|
| 2026-03-28 | DRF-004 | CORE spec L1766 Audit Report header `v1.1.1` vs actual `v1.1.2` | Resolved — patched |
| 2026-03-28 | DRF-004 | CORE spec L1781 disclaimer `v1.1.1` vs actual `v1.1.2` | Resolved — patched |
| 2026-03-28 | DRF-004 | CORE spec L2096 Input Template header `v1.1.1` vs actual `v1.1.2` | Resolved — patched |
| 2026-03-28 | DRF-004 | CORE spec L2160 confirmation line `v1.1.1` vs actual `v1.1.2` | Resolved — patched |
| 2026-03-28 | DRF-004 | README BibTeX `version = {1.1.1}` vs actual `{1.1.2}` | Resolved — patched |

### Drift Response Protocol

1. **Session start:** Scan `readme` and `changelog` for DRF-004 before beginning any work.
2. **On version bump:** Before releasing, grep CORE spec for ALL prior version strings
   (`v{prev}`, `{prev}`) — do NOT rely on find-all-in-file from IDE alone.
   Minimum check points: Output Format header, Disclaimer, Input Template header, confirmation line.
3. **After any spec update:** Check playbook and archive `canonical_statement` for DRF-001/DRF-002.
4. **On DRF-003 detection:** Do not proceed. Record IMMUTABLE change rationale in archive first.
5. **Recording new drift evidence:** Append to `memory/stem-ai-lessons.v1.5.3.md` with:
   - stale surface path + stale value
   - current surface path + current value
   - resolution action taken
