# STEM BIO-AI Trustworthiness Audit Report v1.1.2

**Repository:** artic-network/fieldbioinformatics  
**Local Target Path:** `D:\Sanctum\Extra Repo\fieldbioinformatics`  
**Remote:** https://github.com/artic-network/fieldbioinformatics  
**Commit:** `8008b4c97c2193a82308ff6f0be507b1d9306e36`  
**Branch:** `master`  
**Last Commit Date:** 2026-04-10  
**Audit Date:** 2026-04-28
**Report Expiry:** 2027-04-10  
**Execution Mode:** LOCAL_ANALYSIS  
**Auditor Affiliation:** independent  
**Flags:** NASCENT_REPO: false | CLINICAL_ADJACENT: true | CA_SEVERITY: CA-INDIRECT | T0_HARD_FLOOR: false

## Mandatory Clinical-Use Disclaimer

This audit is a trustworthiness assessment of an open-source bioinformatics repository. It is not a certification, regulatory clearance, clinical validation, or medical recommendation. The audited repository must not be used for autonomous diagnosis, treatment selection, or patient management without independent domain validation, local quality controls, and applicable regulatory review.

## 1. Trust Score Matrix

| Component | Weight | Score | Verdict |
| --- | ---: | ---: | --- |
| Stage 1 -- README Intent | 0.40 | 65 / 100 | Clear technical scope; missing explicit clinical-use boundary |
| Stage 2R -- Repo-Local Consistency | 0.20 | 75 / 100 | Strong local claim/code/doc/test alignment; clinical boundary still missing |
| Stage 3 -- Code/Bio Responsibility | 0.40 | 55 / 100 | Strong test/documentation surface; dependency and governance gaps remain |
| Risk Penalties | -- | 0 | No C1 credential failure; no T0 hard floor |
| **Base Final Score** | -- | **63 / 100** | **T2 Caution** |
| Governance Overlay (Stage 3G) | advisory | N/A | No bounded governance artifact detected |
| Code Integrity (C1-C4) | advisory | PASS/WARN/WARN/WARN | LOCAL_ANALYSIS only |

**Formal Tier:** T2 Caution  
**Use Scope:** Research reference and supervised non-clinical technical review only. No autonomous clinical decision support.  
**Stage 2 Lane:** Stage 2R Repo-Local Consistency. No Stage 2 weight redistribution was used.

## 2. Stage 1: README Intent

The README describes `artic` as "a bioinformatics pipeline for working with virus sequencing data sequenced with nanopore" and more specifically as tools for "viral nanopore sequencing data, generated from tiling amplicon schemes" (`README.md:4`, `README.md:17`). The stated outputs include read filtering, primer trimming, amplicon normalisation, variant calling, and consensus building (`README.md:24-27`).

The claims are concrete and implementation-aligned rather than hype-driven. The repository does not present autonomous diagnosis, treatment selection, or direct patient-management claims. However, the pipeline produces clinically adjacent artifacts such as consensus FASTA and VCF outputs, and the README does not include an explicit "not for diagnostic/clinical use" boundary. That omission matters because the project is viral sequencing infrastructure and may be used near public-health or clinical workflows.

**Stage 1 Score:** 65 / 100

## 3. Stage 2R: Repo-Local Consistency

External cross-platform Stage 2 evidence was not collected for this LOCAL_ANALYSIS run. Instead, v1.1.2 Stage 2R was applied as the repo-local consistency lane. Stage 2R does not claim social or public-activity validation; it checks whether the repository's own surfaces agree with each other.

**Stage 2R Rubric:**

| Item | Score | Evidence |
| --- | ---: | --- |
| Baseline | 60 | Non-nascent repository baseline |
| R2R-1 README/package/code alignment | +15 | README viral nanopore pipeline claims align with `pyproject.toml` package description and CLI entry points (`README.md:4`, `README.md:17`, `pyproject.toml:16`, `pyproject.toml:39`). |
| R2R-2 README/docs alignment | +10 | README pipeline scope aligns with quick-start outputs and troubleshooting surfaces (`README.md:24-27`, `docs/quick-start.md:21-22`, `docs/troubleshooting.md:13-21`). |
| R2R-3 README/test/CI alignment | +10 | README test instructions align with CI workflow and documented pipeline/validation tests (`README.md:66-80`, `.github/workflows/unittests.yml:23-44`, `docs/tests.md:47-62`). |
| R2R-D2 Missing clinical-use boundary | -20 | Clinical-adjacent consensus/VCF outputs exist, but no explicit non-diagnostic/non-clinical boundary was observed across the local README/docs surface. |

**Calculation:** 60 + 15 + 10 + 10 - 20 = 75
**Stage 2R Score:** 75 / 100
**Verdict:** Mixed Local Consistency

## 4. Stage 3: Code/Bio Responsibility

The repository has a meaningful engineering and domain-test surface. GitHub Actions install the conda environment, install the package editable, download Clair3 models, run unit tests, run the `test-runner.sh clair3` pipeline path, and run `tests/minion_validator.py` (`.github/workflows/unittests.yml:12`, `:23-24`, `:28-29`, `:33-44`). Documentation describes unit tests, a full pipeline test using a small Ebola amplicon sequencing run, and slow SARS-CoV-2 validation tests that compare variants and consensus sequences against known truth sets (`docs/tests.md:47-62`).

The technical documentation is also useful for users. The quick-start states that the pipeline requires reads from a tiling amplicon protocol and will not produce meaningful results on metagenomic or whole-genome shotgun data (`docs/quick-start.md:21-22`). Troubleshooting documents exit codes for no aligned reads, malformed primer schemes, empty FASTQ, model selection failure, missing tools, OOM, and killed processes (`docs/troubleshooting.md:13-21`).

The main Stage 3 limitations are reproducibility and governance. `environment.yml` uses mostly unpinned or lower-bound dependencies such as `python>=3.7`, `clair3>=2.0.0`, `align_trim>=1.0.2`, and many unpinned bioinformatics tools (`environment.yml:6-24`). There is no explicit bias, population, sample-representativeness, or COI/funding declaration in the locally reviewed surface.

**Stage 3 Rubric:**

| Item | Score | Evidence |
| --- | ---: | --- |
| T1 CI/CD | 15 / 15 | Unit, pipeline, and validator workflow present |
| T2 Domain Tests | 15 / 15 | Viral pipeline and variant/consensus validation tests documented |
| T3 Changelog/Release Hygiene | 15 / 15 | `CHANGELOG` and release-oriented workflow present |
| T4 Governance Maturity | 0 / 15 | No governance overlay artifact detected |
| B1 Data/Provenance Controls | 10 / 15 | Primer/model download logic and hash checks exist; full reproducible lockfile absent |
| B2 Bias/Limitations | 0 / 15 | No explicit biological bias or cohort limitation policy observed |
| B3 COI/Funding | 0 / 5 | No COI/funding declaration observed in reviewed local files |

**Stage 3 Score:** 55 / 100

**Weighted Calculation:** `(65 x 0.40) + (75 x 0.20) + (55 x 0.40) - 0 = 63`

## 4b. Code Integrity (C1-C4)

| Check | Status | Finding |
| --- | --- | --- |
| C1 Hardcoded credentials | PASS | Secret scan found only GitHub Actions secret placeholders, not committed credentials (`.github/workflows/stale-issues.yml:23`, `.github/workflows/docker-build-push.yml:45-46`). |
| C2 Dependency pinning | WARN | `environment.yml` is mostly unpinned or lower-bound only (`environment.yml:6-24`). This improves compatibility but weakens reproducibility. |
| C3 Dead clinical/patient-adjacent paths | WARN | Deprecated code contains patient-adjacent literal metadata and formats lab/sample/location/date fields into FASTA IDs (`artic/deprecated/filter_clusters/tagfastas.py:62`, `:65`). It is deprecated, so this is hygiene risk rather than active-path evidence. |
| C4 Exception handling in clinical-adjacent output paths | WARN | `artic/vcf_filter.py` fails closed on missing AF, but missing sample-level DP is swallowed by `except Exception: pass`, after which the variant can still return `True` if other filters pass (`artic/vcf_filter.py:42-49`, `:63-71`). |

C1-C4 are advisory in v1.1.2 except C1 FAIL, which would trigger RP3. C1 did not fail, so no RP3 penalty was applied.

## 5. Runtime Evidence Boundary

This v1.1.2 output is a LOCAL_ANALYSIS audit artifact: it records source-code inspection, documentation evidence, CI/test definitions, scoring decisions, and C1-C4 code-integrity findings.

Local runtime test execution was attempted but stopped at dependency precondition resolution because the current environment did not provide the `Bio` module required by the target test configuration. This is recorded as a runtime evidence boundary, not as completed runtime verification.

The v1.1.2 score therefore remains based on Stage 1 source/README evidence, Stage 2R repo-local consistency, Stage 3 code/bio responsibility, and C1-C4 LOCAL_ANALYSIS evidence. Dependency-provisioned runtime replay is an official follow-on lane for future audit execution, and must remain distinguishable from v1.1.2 scoring evidence.

## 6. Final Judgment

The audited repository is a real, domain-specific viral sequencing pipeline with CI, pipeline tests, documented validation tests, clear user-facing limitations, and code paths matching its README claims. It earns a T2 Caution result because the underlying engineering surface is credible, but it remains unsuitable for autonomous clinical use. The main remediation targets are explicit clinical-use boundaries, reproducible dependency locking, removal or quarantine of deprecated patient-adjacent metadata examples, and fail-closed handling for missing depth fields in variant filtering.
