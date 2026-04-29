# Changelog

All notable changes to STEM BIO-AI are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

IMMUTABLE formula changes require a minor version increment (1.x.0).
Rubric refinements and additions use patch versions (1.0.x).

---

## [1.1.2] - 2026-03-27

### Added
- PATCH-46: MICA v0.2.0 memory layer — `memory/` directory with composition contract,
  archive (18 IMMUTABLE rules as design_invariants), session playbook, and lessons document
  (10 failure modes from L-001 through L-010)
- `memory/mica.yaml` — MICA v0.2.0 composition contract (mode: protocol_evolution)
- `memory/stem-ai.mica.v1.1.2.json` — machine-checkable governance archive
- `memory/stem-ai-playbook.v1.1.2.md` — session protocol and rubric drift guard
- `memory/stem-ai-lessons.v1.1.2.md` — failure mode history (10 lessons from 33 patches)
- PATCH-47: MICA initialization step added to SKILL.md loading order (Step 0) and CORE spec Section 8.2 Execution Instruction
- DEV.to draft for STEM BIO-AI v1.1.2 memory contract explanation
- Official v1.1.2 LOCAL_ANALYSIS audit artifact shape: `report.md` plus `experiment_results.json`
- Real public-repository audit output under `audits/fieldbioinformatics_v1_1_2/`
- Stage 2R: Repo-Local Consistency lane for LOCAL_ANALYSIS audits when external Stage 2 evidence is not collected
- Python CLI package with `stem audit <folder>` local scan command
- CLI output modes for 1-page brief and 3/5-page detailed Markdown, JSON, and PDF reports
- HuggingFace/Gradio `app.py` demo entry point using the same deterministic scanner

### Changed
- Canonical spec filename advanced to `spec/STEM-AI_v1.1.2_CORE.md`
- SKILL.md version updated to 1.1.2
- Public explanation shifted from synthetic evidence examples to a real audit-result JSON and verifier flow

### Fixed
- Post-release consistency cleanup applied to active package surfaces on 2026-04-27
- Active package surfaces aligned to STEM BIO-AI v1.1.2 and MICA v0.2.0
- Template references updated to the current canonical spec and audit report version
- Skill validator strengthened to detect template/spec/MICA drift before release
- `local_analysis_scan.sh` output description corrected to match actual stdout format
- Removed placeholder example audits and synthetic public evidence bundle from the official v1.1.2 surface

---

## [1.1.1] - 2026-03-26

### Fixed
- Canonical spec version alignment errors (`1.0.6` remnants removed from the 1.1.x package surface)
- Template and package references updated to the correct canonical spec filename

### Added
- Explicit statement of the relationship between technical audit and STEM BIO-AI
- Method/template wording clarifying technical audit as fact extraction and STEM BIO-AI as trust classification

### Changed
- Canonical spec filename advanced to `spec/STEM-AI_v1.1.1_CORE.md`

---

## [1.1.0] - 2026-03-26

### Changed
- **Architecture:** Single-file spec split into universal skill package (multi-file)
- **Name:** "Trust Audit Framework for Bio/Medical AI" -> "Trust Audit Framework for Bio/Medical AI Repositories"
- **Runtime:** Added AI CLI support alongside LLM-Native

### Added
- SKILL.md entry point (universal agent skill format, 16+ platforms)
- `spec/` directory for core rubric
- `discrimination/` directory for YES/NO example pairs
- `templates/` directory for institutional output (7 templates)
- `scripts/` directory for automation (3 shell scripts)
- `references/` directory for lookup tables
- `examples/` directory for real audit examples
- `.github/workflows/` CI/CD pipelines (3 workflows)
- README.md, CONTRIBUTING.md, LICENSE, .gitignore
- GitHub-ready repository structure

### Carried Forward (from 1.0.6)
- All 43 patches (PATCH-1 through PATCH-43)
- All 19 self-validation checks
- 4 execution modes (LOCAL_ANALYSIS, FULL, SEARCH_ONLY, MANUAL)
- Dual-path TEXT/CODE rubric
- CA 3-tier severity (DIRECT, INDIRECT, PLANNED)
- C1-C4 code integrity items
- Governance overlay (Stage 3G) with generic terminology
- T4 PENDING denominator = 80 (corrected)
- INSUFFICIENT_DATA split (NASCENT / STALE)
- CA-DIRECT redistribution guardrail

---

## [1.0.6] - 2026-03-22

### Added
- PATCH-27: LOCAL_ANALYSIS execution mode
- PATCH-28: Dual-path rubric (TEXT_PATH / CODE_PATH)
- PATCH-29: C1-C4 code-level integrity items
- PATCH-30: CLINICAL_ADJACENT 3-tier severity
- PATCH-31: CA detection dual-path (import scan + keyword scan)
- PATCH-32: T4 PENDING denominator corrected (85 -> 80)
- PATCH-33: INSUFFICIENT_DATA label split (NASCENT / STALE)
- PATCH-34: Stage 2 S2-0 social evidence auto-fetch
- PATCH-35: FULL MODE fetch failure per-item fallback
- PATCH-36: Stage 3G activation strengthened (artifact required)
- PATCH-37: Governance terminology abstracted (generic terms)
- PATCH-38: Score Matrix inline arithmetic mandatory
- PATCH-39: T2 discrimination examples
- PATCH-40: Auditor affiliation field
- PATCH-41: CHECK 17-19 (C1-C4 gating, CA severity, dual-path)
- PATCH-42: C1 env-var fallback pattern detection
- PATCH-43: Mode comparability notice + self-audit advisory

---

## [1.0.5] - 2026-03-22

### Added
- PATCH-15: Governance Overlay lane (Stage 3G)
- PATCH-16: Base tier preserved, overlay advisory only
- PATCH-17: G1-G5 rubric
- PATCH-18: Remediated target reading order
- PATCH-19: Dual output (Base Tier + Overlay Verdict)
- PATCH-20: CHECK 12-16
- PATCH-21: H1-H6 discrimination examples
- PATCH-22: B3 COI 3-tier expansion
- PATCH-23: Execution order fix (DERIVED-3 before Stage 3)
- PATCH-24: Procurement Threshold Note
- PATCH-25: N/A redistribution observation
- PATCH-26: G1-G5 discrimination examples

---

## [1.0.4] - 2026-03-19

### Added
- PATCH-9: Author Domain Context (informational, zero score impact)
- PATCH-10: DERIVED-1 expiry_date
- PATCH-11: DERIVED-2 audit_branch
- PATCH-12: DERIVED-3 trajectory_signal
- PATCH-13: Non-English README confidence flag
- PATCH-14: Trajectory modifier (+/-5 pts Stage 3)

---

## [1.0.3] - 2026-03-19

### Changed
- Weighted formula: S1x0.40, S2x0.20, S3x0.40
- T0_HARD_FLOOR replaces RP3
- CLINICAL_ADJACENT trigger list expanded to 60+
- T4 PENDING minimum activity threshold
- Mandatory disclaimer block

---

## [1.0.2] - 2026-03-19

### Added
- NASCENT_REPO flag + baseline 50 + T4 PENDING
- CLINICAL_ADJACENT flag + active deduction table
- Live-fire audit: jaechang-hits/scicraft

---

## [1.0.1] - 2026-03

### Changed
- Narrative scoring -> rubric-based point checklists
- Hard STOP -> MANUAL mode with partial audit fallback
- Biological Integrity checklist (B1-B3) added

---

## [1.0.0] - 2026-03

### Added
- Initial 3-stage evaluation concept
- README Dissection, Cross-Platform Verification, Code Debt Audit
- JSON + Markdown output format
