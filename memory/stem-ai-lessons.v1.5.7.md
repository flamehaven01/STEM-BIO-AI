# STEM BIO-AI Lessons & Failure Mode History
# Memory Layer — protocol_evolution
# Version: 1.5.7 | Updated: 2026-05-05

This document records protocol failure modes discovered through real-world use and their
authoritative resolutions. Each entry represents a confirmed failure in a prior version.
All resolutions are now encoded in IMMUTABLE or VARIABLE rules.

---

## How to Use This Document

- Consult when a rubric edge case appears to have multiple valid interpretations.
- Each lesson maps to one or more PATCH numbers in CHANGELOG.md.
- Lessons are immutable records — they are never removed, only extended.
- When a new failure mode is found, append to this file and increment STEM BIO-AI version.

---

## Lesson Registry

### L-001: Narrative Scoring Drift
**Patches:** PATCH-001 through PATCH-006
**Failure mode:** Early versions allowed LLMs to narrate trust assessments without fixed point
values. Different LLMs producing scores 20+ points apart on identical repositories.
**Resolution:** Replaced narrative scoring with rubric-based point checklists. Fixed baselines,
fixed point values, fixed tier boundaries. Cross-LLM target: ±10 points.
**Lesson:** Narrative reasoning is not reproducible. Every scored item must have a fixed,
citable point value.

---

### L-002: NASCENT_REPO Baseline Contamination
**Patch:** PATCH-007 (v1.0.2)
**Failure mode:** Repositories with age < 90 days scored against Stage 2 baseline of 60
(designed for established projects). Nascent repos with no social activity received -10 or
more false deductions, pushing legitimate early-stage work into T0.
**Resolution:** NASCENT_REPO flag. When true: Stage 2 baseline = 50. T4 PENDING path enabled.
**Lesson:** Rubric baselines must account for project lifecycle stage. One baseline for all
projects produces systematic false negatives against early-stage work.

---

### L-003: T0 Hard Floor Missing
**Patch:** PATCH-008 (v1.0.3)
**Failure mode:** Repositories with CA-DIRECT classification and zero code presence could
still score above T0 based on strong Stage 1 README rhetoric. A well-written README was
sufficient to escape T0 despite no actual code.
**Resolution:** T0_HARD_FLOOR rule: CA-DIRECT + zero code presence = T0 regardless of stage
scores. No override. No exception.
**Lesson:** Hard floors must exist for combinations that represent absolute disqualifying risk.
Stage scores can be gamed through documentation quality alone.

---

### L-004: DERIVED Computation Order Error
**Patch:** PATCH-023 (v1.0.5)
**Failure mode:** DERIVED-3 (trajectory signal) was computed after Stage 3, meaning the
trajectory modifier (+/-5 pts) was not available during Stage 3 scoring. Auditors added it
inconsistently — sometimes before clamp, sometimes after.
**Resolution:** DERIVED-3 must be computed in Step 5a, before Stage 3 execution (Step 5b).
Now enforced as IMMUTABLE rule in execution instruction Section 8.2.
**Lesson:** Computation order is part of the spec. Ordering ambiguities produce silent errors
that only appear when trajectory modifiers change tier boundaries.

---

### L-005: Governance Overlay Inflating Base Tier
**Patches:** PATCH-015, PATCH-016, PATCH-020 (v1.0.5)
**Failure mode:** Stage 3G governance overlay scores were being used to revise the formal
base tier upward. A T0 repository with a governance framework was being reported as T1.
**Resolution:** Governance overlay separation rule (IMMUTABLE): Stage 3G is advisory only.
Base tier is never modified by overlay score. G3 = 0 caps overlay verdict at WEAK (Cosmetic
Uplift Guard). Both tiers reported separately in output.
**Lesson:** Governance documentation is not the same as governance in practice. Operational
overlays must not allow paper governance to inflate clinical trust classification.

---

### L-006: T4 PENDING Denominator Error
**Patch:** PATCH-032 (v1.0.6)
**Failure mode:** When T4 PENDING path activated (governance overlay present), Stage 3 rubric
was normalized to /85 instead of /80. This reduced all Stage 3 scores by ~6%, pushing some
borderline T3 repositories below the T4 threshold incorrectly.
**Resolution:** T4 PENDING denominator corrected to 80 (IMMUTABLE rule). All prior audits
that activated T4 PENDING path should be re-run.
**Lesson:** Normalization denominators are part of the scoring formula. Even small denominator
errors compound across the weighted formula into tier-boundary violations.

---

### L-007: LOCAL_ANALYSIS Mode Not Detected
**Patch:** PATCH-027 (v1.0.6)
**Failure mode:** Without an explicit execution mode declaration, auditors running in AI CLI
environments (with local repo access) defaulted to FULL or MANUAL mode, missing C1-C4 code
integrity checks entirely.
**Resolution:** Execution mode declared as mandatory Pre-Execution Check EM-0 (Step 1 of
Section 8.2). Mode determines CODE_PATH availability.
**Lesson:** Capability detection must be explicit, not inferred. Silent mode ambiguity causes
systematic omission of higher-quality evidence paths.

---

### L-008: Stage 3G Activating on Intent Statements
**Patch:** PATCH-036 (v1.0.6)
**Failure mode:** Stage 3G was activating when README or CHANGELOG mentioned governance
"plans" or "intent" without actual artifacts. This allowed repositories to claim governance
overlay credit on aspirational statements.
**Resolution:** Stage 3G activation requires actual governance artifacts (documents, schemas,
policy files). Intent statements without artifacts = Stage 3G NOT_APPLICABLE.
**Lesson:** Governance theater is the primary attack surface. Require material evidence, not
rhetorical evidence.

---

### L-009: Single-File Spec Context Window Overflow
**Patch:** v1.1.0 architecture revision
**Failure mode:** v1.0.6 spec was a single file of 2000+ lines. Context window pressure caused
LLMs to drop discrimination examples or governance overlay details in long audit sessions.
This produced silent scoring errors that were undetectable in output.
**Resolution:** Multi-file skill package architecture (v1.1.0). Core spec + discrimination
examples + templates as separate files loaded on demand.
**Lesson:** A spec that cannot be fully loaded in context is a spec that will be silently
violated. File decomposition is an accuracy requirement, not just an organization preference.

---

### L-010: Cosmetic Governance Uplift via G1-G2 Without Runtime Evidence
**Patch:** PATCH-020 (v1.0.5), strengthened in v1.0.6
**Failure mode:** Repositories could score G1 (bounded insertion) and G2 (capability
preservation) on documentation alone, reaching BOUNDED verdict without any runtime
fail-closed evidence. Clinical operators were making procurement decisions based on
BOUNDED verdicts that had no operational substance.
**Resolution:** Cosmetic Uplift Guard: G3 (Fail-Closed Runtime Evidence) = 0 caps overlay
verdict at WEAK, regardless of G1/G2/G4/G5 scores. Stage3G_Score capped at 10.
**Lesson:** Operational safety claims require operational safety evidence. Documentation
governance and runtime governance are not interchangeable.

---

## Lesson Addition Protocol

When a new failure mode is discovered:

1. Document it as `L-NNN` with patches, failure mode, resolution, and lesson.
2. Verify the resolution is encoded in CORE spec (IMMUTABLE or VARIABLE rule).
3. Increment STEM BIO-AI version (patch version for rubric refinement, minor for formula change).
4. Update `operation_meta.update_count` and `last_updated` in archive JSON.
5. Add provenance entry for the triggering repository if a real audit exposed the failure.

---

## Drift Profile First Cycle -- 2026-03-28

MICA v0.2.0 Drift Profile applied to STEM-BIO-AI for the first time.

### Drift events caught and resolved

| DRF | Stale surface | Stale value | Current value | Resolution |
|-----|--------------|-------------|---------------|------------|
| DRF-004 | CORE spec L1766 | Audit Report header v1.1.1 | v1.1.2 | Patched |
| DRF-004 | CORE spec L1781 | Disclaimer executing v1.1.1 | v1.1.2 | Patched |
| DRF-004 | CORE spec L2096 | Input Template header v1.1.1 | v1.1.2 | Patched |
| DRF-004 | CORE spec L2160 | Confirmation line v1.1.1 | v1.1.2 | Patched |
| DRF-004 | README BibTeX | version = {1.1.1} | {1.1.2} | Patched |
| DRF-004 | playbook L84 | on_version_increment | on_version_bump | Patched |

### Pattern registered (high-risk zone)

CORE spec template sections do NOT auto-update on file copy.
On every version bump, grep for ALL occurrences of the prior version string in:
- Output Format header (Section 8.1)
- Disclaimer line (Section 8.1)
- Input Template header (Section 8.3)
- Audit Report generation confirmation (Section 8.3 footer)
This is now a mandatory DRF-004 pre-release check.

---

### L-011: Label Honesty Drift
**Patch:** v1.2.0
**Failure mode:** Earlier surfaces used trust/audit wording that could be read as stronger than
what the deterministic scanner physically measured. This created a mismatch between output labels
and regex/file/AST evidence.
**Resolution:** Repositioned STEM BIO-AI as a deterministic evidence-surface scanner. Output labels
now describe observable evidence signals and review-priority tiers, not clinical certification.
**Lesson:** Measurement labels must name the evidence actually observed. Trust language must be
reserved for externally validated conclusions, not scanner output.

---

### L-012: Evidence Ledger Gaps Block Explainability
**Patch:** v1.3.0
**Failure mode:** Some scored components were not represented in the evidence ledger, which meant
`--explain` could not fully justify score-affecting decisions with file/line evidence.
**Resolution:** Added stable POSIX `finding_id` generation, ledger coverage for scored components,
AST observations, and Stage 4 replication evidence as a separate lane.
**Lesson:** Any score-affecting signal must be traceable. AI advisory layers must cite evidence IDs,
not detector names or prose summaries.

---

### L-013: Reasoning Diagnostics Must Not Become a Shadow Score
**Patch:** v1.3.2
**Failure mode:** Mathematical diagnostics can appear authoritative even when their weights are
initial priors rather than calibrated truth sources.
**Resolution:** `reasoning_model` is diagnostic-only. It reports evidence budget, confidence envelope,
lane coherence, uncertainty budget, evidence-risk gate, and benchmark alignment without changing the
final score or tier.
**Lesson:** A reasoning model is useful only when it preserves the measurement boundary. Do not build
a grand unified trust equation before benchmark calibration.

---

### L-014: Provider Advisory Citation Drift
**Patch:** v1.4.4
**Failure mode:** Early Gemini/Qwen provider trials showed that models may shorten or paraphrase
citation IDs, producing advisory JSON that looked plausible but could not be traced back to the ledger.
**Resolution:** Advisory packets now include `allowed_finding_ids` and a strict prompt contract. Provider
responses are validated offline and rejected if citations do not exactly match current ledger IDs.
**Lesson:** Provider-neutral AI can be layered on the scanner only as evidence-bound commentary. Exact
citation copying is a contract requirement, not a formatting preference.

---

### L-015: License/Use Restrictions Are Review Evidence, Not Score Credit
**Patch:** v1.5.0
**Failure mode:** License and use-scope restrictions such as non-commercial, research-only, academic-only,
or no-clinical-use language can be missed if treated as generic README text. Scoring them positively
would also confuse restriction evidence with repository quality.
**Resolution:** Added score-neutral `S4_license_restriction` evidence. Restrictions are surfaced for
review without altering final score, replication score, or tier.
**Lesson:** Boundary conditions should be visible to reviewers even when they are not quality signals.
Evidence visibility and score credit are separate design choices.

---

### L-016: Memory Layer Version Drift After Release Tag
**Patch:** v1.5.1
**Failure mode:** The v1.5.0 code release tag was created before the MICA memory layer was advanced from v1.1.2-era pointers, leaving the active archive/playbook/lessons outside the release tag.
**Resolution:** Released v1.5.1 as a hygiene patch that rotates memory snapshots to the current release surface and updates loader pointers, README citation, package metadata, and validation defaults together.
**Lesson:** Memory alignment is part of release readiness. Version tags should include the active memory contract or the next patch must explicitly repair the drift without force-moving published tags.

---

### L-017: Stage 1 Hype Surface Missing From CLI
**Patch:** v1.5.2
**Failure mode:** CLI Stage 1 was materially more permissive than the internal rubric because H1-H6 hype penalties and R1-R5 responsibility signals were absent. Hype-heavy repositories could retain inflated README evidence scores.
**Resolution:** Added deterministic Stage 1 H/R scoring, `stage_1_rubric` JSON output, and evidence-ledger detectors for hype and responsibility surfaces.
**Lesson:** If a scored surface exists in the active internal rubric, the local scanner must either implement it or explicitly keep it out of scoring. Silent partial implementation creates tier inflation risk.

---

### L-018: Stage 2R Consistency Needs Negative Evidence
**Patch:** v1.5.3
**Failure mode:** Repo-local consistency could reward vocabulary overlap while missing contradictory clinical boundaries, stale README/package version metadata, and workflow/test/CLI claims that had no matching local support surface.
**Resolution:** Added Stage 2R R4 limitation-repetition credit plus D1/D3/D4 deductions for internal clinical-boundary contradictions, stale metadata, and unsupported workflow claims.
**Lesson:** Consistency is not only overlap. A deterministic scanner must also surface local contradictions and unsupported operational claims before advisory or calibration layers rely on the score.

---

### L-019: Framework Meta-Documentation Can Trigger Clinical Floors
**Patch:** v1.5.6
**Failure mode:** README/API/scoring-rationale text that described scanner rules used words such as "triage", "diagnostic", and "clinical deployment". The scanner treated those meta descriptions as target-repository clinical claims and forced its own self-audit to T0.
**Resolution:** Added meta-evidence line filtering for CA/T0/hype claim detection and expanded explicit clinical-boundary phrases such as "not a medical device" and "not clinically validated".
**Lesson:** Detector documentation is not the same as a product claim. Claim detectors need a narrow exclusion path for framework meta-language while preserving detection of real direct clinical claims.

---

### L-020: Active Memory Pointers Must Advance With Release Version
**Patch:** v1.5.7
**Failure mode:** Code and public docs moved to v1.5.7 while `memory/mica.yaml` still pointed at v1.5.6 and `SKILL.md` still hard-coded v1.1.2 memory filenames. The active release surface and the MICA loader could initialize different project states.
**Resolution:** Rotated the active memory layer to v1.5.7, updated `mica.yaml` pointers, and changed `SKILL.md` to follow the files referenced by `mica.yaml` instead of embedding historical memory filenames.
**Lesson:** Memory retention can be indefinite, but active loader pointers must remain single-source-of-truth. Historical snapshots stay archived; only `mica.yaml` decides what is live.

