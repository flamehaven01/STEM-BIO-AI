# STEM-AI Trustworthiness Audit Report v1.1.2

**Repository:** artic-network/fieldbioinformatics  
**Local Target Path:** `D:\Sanctum\Extra Repo\fieldbioinformatics`  
**Remote:** https://github.com/artic-network/fieldbioinformatics  
**Commit:** `8008b4c97c2193a82308ff6f0be507b1d9306e36`  
**Branch:** `master`  
**Last Commit Date:** 2026-04-10  
**Audit Date:** 2026-04-27  
**Report Expiry:** 2027-04-10  
**Execution Mode:** LOCAL_ANALYSIS  
**Auditor Affiliation:** independent  
**Flags:** NASCENT_REPO: false | CLINICAL_ADJACENT: true | CA_SEVERITY: CA-INDIRECT | T0_HARD_FLOOR: false

## Mandatory Clinical-Use Disclaimer

This audit is a trustworthiness assessment of an open-source bioinformatics repository. It is not a certification, regulatory clearance, clinical validation, or medical recommendation. The audited repository must not be used for autonomous diagnosis, treatment selection, or patient management without independent domain validation, local quality controls, and applicable regulatory review.

## 1. Trust Score Matrix

| Component | Weight | Score | Verdict |
| --- | ---: | ---: | --- |
| Stage 1 -- README Intent | 0.50 | 65 / 100 | Clear technical scope; missing explicit clinical-use boundary |
| Stage 2 -- Cross-Platform | N/A | N/A | Not executed in LOCAL_ANALYSIS-only run |
| Stage 3 -- Code/Bio Responsibility | 0.50 | 55 / 100 | Strong test/documentation surface; dependency and governance gaps remain |
| Risk Penalties | -- | 0 | No C1 credential failure; no T0 hard floor |
| **Base Final Score** | -- | **60 / 100** | **T2 Caution** |
| Governance Overlay (Stage 3G) | advisory | N/A | No bounded governance artifact detected |
| Code Integrity (C1-C4) | advisory | PASS/WARN/WARN/WARN | LOCAL_ANALYSIS only |

**Formal Tier:** T2 Caution  
**Use Scope:** Research reference and supervised non-clinical technical review only. No autonomous clinical decision support.  
**Weight Redistribution:** Stage 2 was not executed, so the fixed v1.1.2 redistribution applies: Stage 1 = 0.50, Stage 3 = 0.50.

## 2. Stage 1: README Intent

The README describes `artic` as "a bioinformatics pipeline for working with virus sequencing data sequenced with nanopore" and more specifically as tools for "viral nanopore sequencing data, generated from tiling amplicon schemes" (`README.md:4`, `README.md:17`). The stated outputs include read filtering, primer trimming, amplicon normalisation, variant calling, and consensus building (`README.md:24-27`).

The claims are concrete and implementation-aligned rather than hype-driven. The repository does not present autonomous diagnosis, treatment selection, or direct patient-management claims. However, the pipeline produces clinically adjacent artifacts such as consensus FASTA and VCF outputs, and the README does not include an explicit "not for diagnostic/clinical use" boundary. That omission matters because the project is viral sequencing infrastructure and may be used near public-health or clinical workflows.

**Stage 1 Score:** 65 / 100

## 3. Stage 2: Cross-Platform Analysis

Stage 2 was not executed for this run. This audit intentionally used local repository evidence only: source code, documentation, dependency files, workflows, and local test execution attempt. No social-media, package-registry, or external web consistency evidence was fetched.

**Stage 2 Score:** N/A  
**Effect:** Stage 2 weight redistributed to Stage 1 and Stage 3 according to v1.1.2 rules.

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

## 4b. Code Integrity (C1-C4)

| Check | Status | Finding |
| --- | --- | --- |
| C1 Hardcoded credentials | PASS | Secret scan found only GitHub Actions secret placeholders, not committed credentials (`.github/workflows/stale-issues.yml:23`, `.github/workflows/docker-build-push.yml:45-46`). |
| C2 Dependency pinning | WARN | `environment.yml` is mostly unpinned or lower-bound only (`environment.yml:6-24`). This improves compatibility but weakens reproducibility. |
| C3 Dead clinical/patient-adjacent paths | WARN | Deprecated code contains patient-adjacent literal metadata and formats lab/sample/location/date fields into FASTA IDs (`artic/deprecated/filter_clusters/tagfastas.py:62`, `:65`). It is deprecated, so this is hygiene risk rather than active-path evidence. |
| C4 Exception handling in clinical-adjacent output paths | WARN | `artic/vcf_filter.py` fails closed on missing AF, but missing sample-level DP is swallowed by `except Exception: pass`, after which the variant can still return `True` if other filters pass (`artic/vcf_filter.py:42-49`, `:63-71`). |

C1-C4 are advisory in v1.1.2 except C1 FAIL, which would trigger RP3. C1 did not fail, so no RP3 penalty was applied.

## 5. Runtime Verification Attempt

Command attempted:

```powershell
python -m pytest tests\vcf_filter_unit_test.py -q
```

Result: blocked before test execution because the current local environment lacks Biopython:

```text
ModuleNotFoundError: No module named 'Bio'
```

This audit therefore does not claim local runtime test success. It records CI/test definitions and static code evidence, plus the failed local execution precondition.

## 6. Final Judgment

`fieldbioinformatics` is not slop: it is a real, domain-specific viral sequencing pipeline with CI, pipeline tests, documented validation tests, clear user-facing limitations, and code paths matching its README claims. The repository earns a T2 Caution result because the underlying engineering surface is credible, but it remains unsuitable for autonomous clinical use. The main remediation targets are explicit clinical-use boundaries, reproducible dependency locking, removal or quarantine of deprecated patient-adjacent metadata examples, and fail-closed handling for missing depth fields in variant filtering.

