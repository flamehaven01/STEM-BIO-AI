# v1.3.2 Reasoning Local-10 Comparison

Scope: same 10 local repositories, now scanned with v1.3.2 reasoning diagnostics. The reasoning layer is diagnostic-only and does not alter final score.

## Aggregate

| Metric | Value |
|---|---:|
| Exact tier agreement vs manual control | 6/10 |
| Within-one-tier agreement vs manual control | 10/10 |
| Score changes vs v1.3.1 baseline | 0/10 |
| Tier changes vs v1.3.1 baseline | 0/10 |

## Per-Repository Diagnostics

| Repo | Score/Tier | v1.3.1 Delta | Manual | Lane | Uncertainty | Risk | Confidence Envelope |
|---|---|---:|---|---|---|---|---|
| Biomni | 36 / T0 Rejected | 0 | T0 Rejected | coherent (0.89) | review_advised (0.2402) | within_gate (0.033) | 0.309-0.411 |
| AI-Scientist | 36 / T0 Rejected | 0 | T1 Quarantine | coherent (0.89) | review_advised (0.2402) | within_gate (0.033) | 0.3221-0.3979 |
| CellAgent | 28 / T0 Rejected | 0 | T0 Rejected | coherent (0.8) | review_advised (0.3712) | within_gate (0.06) | 0.1819-0.3781 |
| ClawBio | 54 / T1 Quarantine | 0 | T2 Caution | mixed (0.615) | review_advised (0.2597) | within_gate (0.5155) | 0.5178-0.5622 |
| LabClaw | 28 / T0 Rejected | 0 | T0 Rejected | coherent (0.8) | review_advised (0.3712) | within_gate (0.06) | 0.1819-0.3781 |
| claude-scientific-skills | 39 / T0 Rejected | 0 | T0 Rejected | coherent (0.86) | stable (0.1257) | within_gate (0.4423) | 0.3608-0.4192 |
| SciAgent-Skills | 48 / T1 Quarantine | 0 | T0 Rejected | mixed (0.725) | review_advised (0.2967) | within_gate (0.4825) | 0.4215-0.5385 |
| BioAgents | 50 / T1 Quarantine | 0 | T0 Rejected | mixed (0.715) | review_advised (0.3442) | within_gate (0.0855) | 0.4263-0.5737 |
| BioClaw | 39 / T0 Rejected | 0 | T0 Rejected | coherent (0.825) | review_advised (0.2202) | within_gate (0.4525) | 0.3016-0.4784 |
| OpenClaw-Medical-Skills | 38 / T0 Rejected | 0 | T0 Rejected | coherent (0.85) | review_advised (0.3297) | within_gate (0.045) | 0.3587-0.4013 |

## Interpretation

- v1.3.2 should show zero score/tier drift against the v1.3.1 precision baseline; any drift would violate the diagnostic-only policy.
- The useful new signal is explanatory: lane coherence, uncertainty, evidence risk, and confidence envelope now give reviewers structured reasons to prioritize manual inspection.
- Repositories with low lane coherence or high evidence risk should be reviewed before using tier agreement as a quality claim.
