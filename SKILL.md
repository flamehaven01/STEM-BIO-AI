---
name: stem-ai
description: "Deterministic Evidence-Surface Scanner for Bio/Medical AI Repositories. Audits and reviews open-source bio/medical AI repositories for repository evidence-surface triage using a rubric-based 3-stage evaluation protocol with governance overlay. Produces scored review-priority reports with evidence chains. Supports 4 execution modes: LOCAL_ANALYSIS (AI CLI + local clone), FULL (web search + fetch), SEARCH_ONLY, and MANUAL. Use when asked to evaluate, audit, review, or assess evidence signals for any bio-AI, medical AI, or clinical-adjacent repository."
version: "1.4.2"
author: "Flamehaven"
license: "Apache-2.0"
platforms: ["claude-code", "codex", "gemini-cli", "cursor", "copilot", "antigravity", "universal"]
---

# STEM BIO-AI -- Deterministic Evidence-Surface Scanner for Bio/Medical AI Repositories

**Version:** 1.4.2
**Codename:** Hippocratic_Code_Engine_Unified
**Runtime:** LLM-Native + AI CLI (Universal)

> "Code works. But does the author care about the patient?
>  Governance without evidence is theater.
>  Evidence without accountability is still not trust.
>  Measurement beats interpretation."

## When to Use This Skill

- Evaluating repository evidence signals for a bio-AI or medical AI repository
- Auditing open-source clinical-adjacent tools before procurement or pilot
- Assessing governance maturity of repositories handling patient data
- Generating structured audit reports with evidence chains and scores
- Comparing repository review-priority tiers across an ecosystem
- Producing institutional-grade documentation (Claim Matrix, Evidence Ledger)

## What This Skill Produces

1. **STEM BIO-AI Audit Report** -- scored repository evidence-surface triage (T0-T4 review-priority tier)
2. **Executive Summary** -- 1-page institutional decision support
3. **Claim Matrix** -- line-level evidence anchors for every finding
4. **Evidence Ledger** -- snapshot provenance and artifact tracking
5. **Code Integrity Report** -- C1-C4 findings (LOCAL_ANALYSIS only)

## Audit Layering

STEM BIO-AI sits on top of technical audit. It should not replace it.

- **Technical audit** determines what the repository actually does.
- **STEM BIO-AI** determines whether the observable artifact surface is sufficient for institutional review triage.

Use this skill after or alongside technical inspection, not instead of it.

## Quick Start

To audit a repository, provide:
- GitHub URL or README text
- (Optional) CHANGELOG, social media activity, CI/CD status
- (Optional) Governance overlay materials

The skill will:
1. Detect execution mode (LOCAL_ANALYSIS / FULL / MANUAL)
2. Run 3-stage evaluation (README Evidence Signal, Cross-Platform, Code Debt)
3. Score with fixed rubric (cross-LLM target: +/-10 points)
4. Evaluate governance overlay if artifacts present
5. Generate multi-file output package

## Skill Architecture

```
stem-ai/
  SKILL.md                    <-- You are here (entry point)
  memory/                     <-- MICA v0.2.0 memory layer (load first)
    mica.yaml                 <-- composition contract
    stem-ai.mica.v1.1.2.json  <-- archive (18 IMMUTABLE rules, lessons, provenance)
    stem-ai-playbook.v1.1.2.md <-- session protocol and rubric drift guard
    stem-ai-lessons.v1.1.2.md  <-- failure mode history
  spec/                       <-- Core rubric, scoring, execution rules
  discrimination/             <-- YES/NO example pairs for scoring consistency
  templates/                  <-- Output templates (report, claim matrix, etc.)
  scripts/                    <-- Automation scripts (scans, provenance)
  references/                 <-- Lookup tables (tiers, triggers, taxonomy)
  examples/                   <-- Real audit examples
```

## Instructions

When activated, load files in this order:

0. **Load MICA memory layer first (before any audit work):**
   - Load `memory/mica.yaml` -- verify package structure and mode
   - Load `memory/stem-ai.mica.v1.1.2.json` -- activate 18 IMMUTABLE rules as design_invariants
   - Load `memory/stem-ai-playbook.v1.1.2.md` -- session protocol and rubric drift guard
   - Run PCT self-tests (PCT-001 through PCT-007). Halt on PCT-001/002/003 failure.
   - Report: `[MICA READY] stem-ai-bio v1.1.2 | invariants: 18 active`

1. **Always load next:** `spec/STEM-AI_v1.1.2_CORE.md`
   This is the canonical rubric and execution instruction.

2. **Load on demand during Stage 1:**
   - `discrimination/H1-H6_examples.md`
   - `references/clinical_adjacent_triggers.md`

3. **Load on demand during Stage 3:**
   - `discrimination/T2_examples.md`
   - `discrimination/B3_COI_guide.md`
   - `discrimination/CA_severity_examples.md`

4. **Load if governance overlay detected:**
   - `discrimination/G1-G5_examples.md`

5. **Load for output generation:**
   - `templates/audit_report.md`
   - `templates/claim_matrix.md`
   - `templates/executive_summary.md`
   - `templates/evidence_ledger.md`

6. **Run in LOCAL_ANALYSIS mode:**
   - `scripts/local_analysis_scan.sh`
   - `scripts/ca_detection_scan.sh`
   - `scripts/snapshot_provenance.sh`

## Execution Modes

| Mode | Environment | Evidence Quality | C1-C4 |
|------|------------|-----------------|-------|
| LOCAL_ANALYSIS | AI CLI + local clone | CODE_PATH (measurement) | Active |
| FULL | Online LLM + web tools | TEXT_PATH + web fetch | N/A |
| SEARCH_ONLY | Online LLM + search only | TEXT_PATH + search | N/A |
| MANUAL | Online LLM, no tools | TEXT_PATH only | N/A |

## Tier Definitions

| Tier | Score | Meaning |
|------|-------|---------|
| T0 Rejected | 0-39 | Trust not established -- clinical use prohibited |
| T1 Quarantine | 40-54 | High risk -- independent verification required |
| T2 Caution | 55-69 | Research reference only -- clinical automation forbidden |
| T3 Review | 70-84 | Supervised clinical pilot eligible -- oversight mandatory |
| T4 Approved | 85-100 | Trust approved -- regulatory review alongside deployment |
