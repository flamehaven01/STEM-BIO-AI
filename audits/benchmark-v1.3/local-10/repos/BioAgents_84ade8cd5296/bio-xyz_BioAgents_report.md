# STEM BIO-AI Local Audit Report

**Target:** `bio-xyz/BioAgents`
**Execution Mode:** `LOCAL_ANALYSIS`
**Final Score:** **50 / 100**
**Formal Tier:** **T1 Quarantine**
**Use Scope:** Exploratory review only; no patient-adjacent use.

## Score Matrix

| Stage | Weight | Score |
| --- | ---: | ---: |
| Stage 1 README Evidence Signal | 0.40 | 70 |
| Stage 2R Repo-Local Consistency | 0.20 | 70 |
| Stage 3 Code/Bio Responsibility | 0.40 | 19 |
| Risk Penalty | -- | 0 |

## Replication Evidence Lane

**Stage 4 Replication Score:** **25 / 100**
**Replication Tier:** **R1**

## Code Integrity
- **C1_hardcoded_credentials:** PASS — No direct credential patterns detected by local CLI scan.
- **C2_dependency_pinning:** PASS — Dependency manifest appears pinned or not present.
- **C3_dead_or_deprecated_patient_adjacent_paths:** PASS — No deprecated patient-adjacent metadata patterns detected.
- **C4_exception_handling_clinical_adjacent_paths:** PASS — No broad fail-open exception pattern detected.

## Top Risks
- No major local risks detected by the CLI scan.

## Stage 2R Evidence
- **baseline:** 60 — Non-nascent local repository baseline.
- **R2R_3_readme_test_ci_alignment:** 10 — Test/CI surfaces are present and locally consistent.

## Stage 3 Evidence
- **T1_CI_CD:** 15 / 15 — Workflow files detected.
- **T2_domain_tests:** 0 / 15 — No tests detected.
- **T3_changelog_release_hygiene:** 0 / 15 — No changelog detected.
- **B1_data_provenance_controls:** 0 / 15 — No dependency/provenance manifest detected.
- **B2_bias_limitations:** 0 / 15 — No bias/limitations language detected by local CLI scan.
- **B3_coi_funding:** 0 / 5 — No COI/funding disclosure detected by local CLI scan.
- **stage_3_raw_total:** 15 / 80 — Raw rubric total before normalization to 100.

## Stage 4 Replication Evidence
- **S4_container_environment:** 10 / 10 — Container or compose file exists.
- **S4_make_reproduce_target:** 0 / 10 — No Makefile detected.
- **S4_environment_lock_evidence:** 0 / 10 — No environment, dependency, or lock manifest detected.
- **S4_exact_dependency_pins_or_hashes:** 0 / 10 — No dependency manifest detected.
- **S4_readme_reproducibility_section:** 0 / 10 — README exists but no reproducibility or replication section heading was detected.
- **S4_checksum_files:** 0 / 10 — No evidence detected for S4_checksum_files.
- **S4_dataset_url:** 10 / 10 — Dataset URL or data source reference detected.
- **S4_model_weight_url_or_checksum:** 0 / 10 — Documentation exists but no model artifact URL/checksum evidence was detected.
- **S4_citation_cff:** 0 / 5 — No evidence detected for S4_citation_cff.
- **S4_cli_entrypoint:** 5 / 5 — CLI entry point or argparse interface detected.
- **S4_seed_setting:** 0 / 5 — No deterministic seed setting detected.
- **S4_runnable_examples:** 0 / 5 — No evidence detected for S4_runnable_examples.
- **stage_4_raw_total:** 25 / 100 — Raw Stage 4 rubric total. Stage 4 is reported separately and does not alter final score in v1.3.0.

## Method Boundary
Deterministic local CLI scan. No LLM, network, or runtime test execution is required.

## Disclaimer
This is an evidence-surface pre-screen, not clinical certification, regulatory clearance, or medical advice.
