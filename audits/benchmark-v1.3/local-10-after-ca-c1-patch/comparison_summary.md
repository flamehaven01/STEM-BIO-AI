# v1.3 Local-10 Patch Comparison

Patch scope:

- Added deterministic clinical-adjacent vocabulary for biomedical skill/catalog surfaces such as clinical trial, medical imaging, pydicom, biomarker, survival analysis, AutoDock, drug docking, nnU-Net, and regulatory submission.
- Excluded obvious placeholder/test credential values such as `super-secret`, `dummy`, `fake`, and `example` keys from the C1 risk penalty while keeping them visible in the evidence ledger as `not_applicable`.

Boundary:

- This comparison uses the existing local-10 control set from `audits/benchmark-v1.3/local-10`.
- The manual control comes from STEM-AI v1.0.4 MANUAL mode and is not calibrated ground truth.

## Aggregate Comparison

| Metric | Before | After |
|---|---:|---:|
| Exact tier agreement | 6/10 | 6/10 |
| Within-one-tier agreement | 9/10 | 10/10 |
| Major disagreement count | 1 | 0 |

## Key Deltas

| Repo | Before | After | Manual Control | Change |
|---|---|---|---|---|
| SciAgent-Skills | 56 / T2 Caution | 48 / T1 Quarantine | T0 Rejected | `ca_severity` changed from `none` to `CA-INDIRECT`; major disagreement resolved |
| ClawBio | 44 / T1 Quarantine | 54 / T1 Quarantine | T2 Caution | `C1_hardcoded_credentials` changed from `FAIL` to `PASS` for `api_key="super-secret-key"` test fixture placeholders |

## Remaining Review Items

- SciAgent-Skills is still one tier above the old manual control; review whether additional clinical-adjacent skill-catalog penalties are justified before altering score formulas.
- ClawBio remains one tier below the old manual control because clinical-adjacent boundary penalties and C2/C4 warnings still apply.
- BioAgents remains one tier above the old manual control; missing deterministic detection for insecure default configuration remains a v1.3.x candidate.
