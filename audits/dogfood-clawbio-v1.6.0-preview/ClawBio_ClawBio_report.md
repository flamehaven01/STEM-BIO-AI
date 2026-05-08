# STEM BIO-AI Local Audit Report

**Target:** `ClawBio/ClawBio`
**Execution Mode:** `LOCAL_ANALYSIS`
**Final Score:** **67 / 100**
**Formal Tier:** **T2 Caution**
**Use Scope:** Research reference and supervised non-clinical technical review only.

## Score Matrix

| Stage | Weight | Score |
| --- | ---: | ---: |
| Stage 1 README Evidence Signal | 0.40 | 60 |
| Stage 2R Repo-Local Consistency | 0.20 | 70 |
| Stage 3 Code/Bio Responsibility | 0.40 | 72 |
| Risk Penalty | -- | 0 |

## Replication Evidence Lane

**Stage 4 Replication Score:** **55 / 100**
**Replication Tier:** **R2**

## Reasoning Diagnostics

Diagnostic-only heuristic `stem-bio-ai-reasoning-v1.3.2` (uncalibrated_initial_priors_pending_benchmark_calibration); lane consistency `heuristic_consistent` (0.855), uncertainty band `low_spread` (0.1002), risk heuristic `within_heuristic_gate` (0.0435), confidence envelope 0.6489-0.6911. This heuristic layer does not override the final score.

## Regulatory Traceability Assistant

> **Regulatory basis note**
> Aligned to current official source classes as of May 2026: EU AI Act (Regulation (EU) 2024/1689), FDA QMSR, FDA AI-enabled device guidance themes, and IMDRF SaMD/GMLP frameworks.
> This is a traceability aid, not a compliance or clearance determination.

### Stage 1
- **EU_AI_ACT_ARTICLE_13** — signal_only (mapping confidence: weak, evidence strength: moderate)
  - Boundary, intended-use, and limitation language is relevant to transparency scaffolding only.

### Stage 3
- **EU_AI_ACT_ARTICLE_12** — signal_only (mapping confidence: weak_moderate, evidence strength: weak)
  - Change-history scaffolding is present, but runtime log completeness is not established.
- **EU_AI_ACT_ARTICLE_10** — signal_only (mapping confidence: weak, evidence strength: moderate)
  - Provenance and bias signals are relevant to data-governance review, but do not verify execution quality.

### Stage 4
- **EU_AI_ACT_ARTICLE_12** — partially_aligned (mapping confidence: moderate, evidence strength: moderate)
  - Reproducibility and trace manifests support record-keeping scaffolding, not operational logging completeness.

**Summary:** Structural signals partially align with traceability scaffolding. This remains a pre-audit traceability aid, not a compliance determination.

## Code Integrity
- **C1_hardcoded_credentials:** PASS — No direct credential patterns detected by local CLI scan.
- **C2_dependency_pinning:** WARN — requirements.txt:1 biopython>=1.82
- **C3_dead_or_deprecated_patient_adjacent_paths:** PASS — No deprecated patient-adjacent metadata patterns detected.
- **C4_exception_handling_clinical_adjacent_paths:** WARN — bot/roboterri.py:133 except OSError:

## Bio Deterministic Diagnostics

- **SMILES Surface Integrity:** not_detected=1 — No malformed or suspicious SMILES-like strings detected by conservative surface checks.
- **SMILES RDKit Validation:** not_applicable=1 — RDKit optional validation lane unavailable in current environment.
- **SMILES Parser Guard:** not_detected=1 — No missing None/invalid guards detected after SMILES parser calls.
- **Silent Mock Fallback:** not_detected=1 — No silent mock or simulated-data fallback patterns detected in production code paths.
- **Traceability Manifest Surface:** not_detected=1 — No traceability manifest or runtime audit-log schema surface detected.
- **Bio Subprocess Run Trace:** not_detected=1 — No risky subprocess or os.system bio-tool execution patterns detected.

## Top Risks
- C2_dependency_pinning: WARN
- C4_exception_handling_clinical_adjacent_paths: WARN

## Stage 1 Evidence
- **baseline:** 60 — Non-nascent README evidence baseline.
- **R2_regulatory_framework:** -10 — CA-DIRECT surface lacks regulatory or governance framework language.
- **R3_clinical_disclaimer:** 10 — Explicit non-clinical or non-diagnostic boundary detected.
- **R4_demographic_bias_boundary:** 10 — Demographic, subgroup, fairness, bias, or validation-cohort language detected.
- **R5_reproducibility_provisions:** 10 — Reproducibility, replication, seed, lockfile, or checksum language detected.
- **S1_missing_readme:** -20 — No root README detected.

## Stage 2R Evidence
- **baseline:** 60 — Non-nascent local repository baseline.
- **R2R_3_readme_test_ci_alignment:** 10 — Test/CI surfaces are present and locally consistent.

## Stage 3 Evidence
- **T1_CI_CD:** 15 / 15 — Workflow files detected.
- **T2_domain_tests:** 0 / 15 — No tests detected.
- **T3_changelog_release_hygiene:** 15 / 15 — CHANGELOG.md contains bug-fix, patch, or security entries.
- **B1_data_provenance_controls:** 15 / 15 — Dependency manifest detected with data source, IRB, or dataset citation language.
- **B2_bias_limitations:** 8 / 15 — Bias/limitations language detected; no quantitative measurement evidence found.
- **B3_coi_funding:** 5 / 5 — COI, funding, sponsor, or acknowledgement language detected.
- **stage_3_raw_total:** 58 / 80 — Raw rubric total before normalization to 100.

## Stage 4 Replication Evidence
- **S4_container_environment:** 10 / 10 — Container or compose file exists.
- **S4_make_reproduce_target:** 10 / 10 — Makefile reproduction/evaluation target detected.
- **S4_environment_lock_evidence:** 10 / 10 — Environment, dependency, or lock manifest detected.
- **S4_exact_dependency_pins_or_hashes:** 0 / 10 — Dependency manifests exist but no exact pins or hashes were detected.
- **S4_readme_reproducibility_section:** 0 / 10 — No README detected.
- **S4_checksum_files:** 0 / 10 — No evidence detected for S4_checksum_files.
- **S4_dataset_url:** 10 / 10 — Dataset URL or data source reference detected.
- **S4_model_weight_url_or_checksum:** 0 / 10 — Documentation exists but no model artifact URL/checksum evidence was detected.
- **S4_citation_cff:** 0 / 5 — No evidence detected for S4_citation_cff.
- **S4_license_restriction:** 0 / 0 — No license/use restriction language detected.
- **S4_cli_entrypoint:** 5 / 5 — CLI entry point or argparse interface detected.
- **S4_seed_setting:** 5 / 5 — Deterministic seed setting detected.
- **S4_runnable_examples:** 5 / 5 — Runnable example, notebook, or demo file exists.
- **stage_4_raw_total:** 55 / 100 — Raw Stage 4 rubric total. Stage 4 is reported separately and does not alter final score.

## Method Boundary
Deterministic local CLI scan. No LLM, network, or runtime test execution is required.

## Disclaimer
This is an evidence-surface pre-screen, not clinical certification, regulatory clearance, or medical advice.
