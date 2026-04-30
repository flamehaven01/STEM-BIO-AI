# v1.3 Local-10 False Positive / False Negative Log

Status: generated from tier deltas against the existing v1.0.4 manual audit control. Requires human review before detector changes.

## False Positive Candidates

| Repo | Detector | Finding ID | Reason | Proposed Action |
|---|---|---|---|---|
| SciAgent-Skills | clinical adjacency / score cap | S1_readme_bio_terms:README.md:161:001 | v1.3=T2 Caution vs manual=T0 Rejected; v1.3 found clinical/patient text but `ca_severity=none`, missing skill-catalog clinical adjacency context | Add deterministic clinical-adjacent patterns for AutoDock Vina, nnU-Net, pydicom, drug docking, medical imaging, and skill-catalog clinical categories; then re-run local-10 |
| BioAgents | missing security-default detector | - | v1.3=T1 Quarantine vs manual=T0 Rejected; manual audit emphasized disabled default security controls, which v1.3 does not currently detect | Consider a future deterministic detector for insecure default configuration markers; do not change score until more benchmark evidence exists |

## False Negative Candidates

| Repo | Missed Signal | Expected Detector | Evidence Location | Proposed Action |
|---|---|---|---|---|
| AI-Scientist | tier_under_manual_by_1 | tier_alignment | v1.3=T0 Rejected manual=T1 Quarantine | Manual inspect score caps and detected evidence |
| ClawBio | test fixture credential placeholder treated as C1 FAIL | C1_hardcoded_credentials | C1_hardcoded_credentials:skills/illumina-bridge/tests/test_illumina_bridge.py:303:001 | Separate test-fixture placeholder credentials from production credential patterns; likely downgrade from FAIL penalty to evidence-ledger warning |
| ClawBio | broad fail-open handlers in clinical-adjacent paths | C4_exception_handling_clinical_adjacent_paths | C4_exception_handling_clinical_adjacent_paths:skills/gwas-prs/gwas_prs.py:1131:001 | Keep as warning candidate; inspect whether handlers suppress validation errors or only optional cleanup failures |

## Notes

- Tier deltas are not automatic detector defects because the control report and v1.3.0 use different scoring methods.
- Human review should prioritize major disagreements and high Stage 4 scores on low manual tiers.
