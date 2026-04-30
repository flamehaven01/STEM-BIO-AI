# v1.3 Local-10 Benchmark Alignment Summary

Status: local dry-run benchmark against the existing STEM-AI v1.0.4 10-repository manual audit control set.

Important boundary: the manual control uses STEM-AI v1.0.4 MANUAL mode and a different formula (`S1 x 0.50 + S3 x 0.50`). v1.3.0 uses deterministic local evidence-surface scanning, Stage 2R, score caps, Stage 4 replication lane, and evidence ledger output. Treat this as a control comparison, not calibrated ground truth.

## Aggregate Metrics

| Metric | Value |
|---|---:|
| Repository count | 10 |
| Exact tier agreement | 6/10 |
| Within-one-tier agreement | 9/10 |
| Major disagreement count | 1 |

## Result Table

| Repo | v1.3 Score | v1.3 Tier | Rep Score | Rep Tier | Manual v1.0.4 Score | Manual Tier | Delta | Flags |
|---|---:|---|---:|---|---:|---|---:|---|
| Biomni | 36 | T0 Rejected | 20 | R0 | 17 | T0 Rejected | +0 | - |
| AI-Scientist | 36 | T0 Rejected | 20 | R0 | 48 | T1 Quarantine | -1 | tier_under_manual_by_1 |
| CellAgent | 28 | T0 Rejected | 0 | R0 | 15 | T0 Rejected | +0 | - |
| ClawBio | 44 | T1 Quarantine | 55 | R2 | 63 | T2 Caution | -1 | tier_under_manual_by_1 |
| LabClaw | 28 | T0 Rejected | 0 | R0 | 20 | T0 Rejected | +0 | - |
| claude-scientific-skills | 39 | T0 Rejected | 30 | R1 | 24 | T0 Rejected | +0 | - |
| SciAgent-Skills | 56 | T2 Caution | 5 | R0 | 32 | T0 Rejected | +2 | tier_over_manual_by_2_or_more |
| BioAgents | 50 | T1 Quarantine | 25 | R1 | 30 | T0 Rejected | +1 | tier_over_manual_by_1 |
| BioClaw | 39 | T0 Rejected | 25 | R1 | 29 | T0 Rejected | +0 | - |
| OpenClaw-Medical-Skills | 38 | T0 Rejected | 10 | R0 | 22 | T0 Rejected | +0 | - |

## Initial Observations

- v1.3.0 remains conservative on most clinical-adjacent low-evidence repositories.
- The largest divergence is SciAgent-Skills, where v1.3.0 gives T2 while the older manual audit gave T0; inspect Stage 2R/Stage 3/Stage 4 evidence before treating this as a true improvement.
- AI-Scientist and ClawBio score lower than the older manual audit because v1.3.0 applies deterministic local evidence and current score caps rather than manual qualitative credit.
- Stage 4 replication scores should be reviewed for possible over-credit in skill/catalog repositories where environment files exist but scientific replication is still weak.

## Manual Review Priorities

1. SciAgent-Skills is the only major tier disagreement. v1.3.0 classified `ca_severity=none` even though the v1.0.4 manual control treated it as clinical-adjacent because of AutoDock Vina, nnU-Net, pydicom, and drug/medical-imaging skill content. This is a candidate clinical-adjacency false negative.
2. ClawBio is one tier below the manual control. The v1.3.0 risk penalty is driven partly by `C1_hardcoded_credentials` findings in test code using `api_key="super-secret-key"`. This is probably a test fixture / placeholder false positive and should not carry the same penalty as a production credential.
3. BioAgents is one tier above the manual control. v1.3.0 gives strong Stage 1 and Stage 2R baseline credit while the manual audit emphasized disabled default security controls. This points to a possible missing deterministic detector, not necessarily a score formula issue.
4. AI-Scientist is one tier below the manual control. The older audit gave qualitative credit for license-level medical-use restrictions; v1.3.0 currently does not score license restriction language as a README evidence boundary.
