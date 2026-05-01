# Local-10 v1.5.6 CA False-Positive Impact

- Records: 10
- Score/tier changes vs v1.5.4 baseline: 2
- Tier changes vs v1.5.4 baseline: 1
- Score delta range: 0 to 12
- Mean score delta: 2.1
- v1.5.6 tier distribution: {'T0 Rejected': 6, 'T2 Caution': 1, 'T1 Quarantine': 3}

## Interpretation

- ClawBio gains score within T2 because explicit non-medical-device and no-diagnosis boundary language is now recognized.
- BioClaw moves from T0 to T1 because workspace triage is no longer treated as patient triage.
- No repository moves into T3/T4 from this precision patch.

| Repo | Score | Tier | CA | Cap | Boundary | T0 floor |
|---|---:|---|---|---|---|---|
| Biomni | 33 -> 33 (+0) | T0 Rejected -> T0 Rejected | none -> none | None -> None | False | False |
| AI-Scientist | 33 -> 33 (+0) | T0 Rejected -> T0 Rejected | none -> none | None -> None | False | False |
| CellAgent | 28 -> 28 (+0) | T0 Rejected -> T0 Rejected | none -> none | None -> None | False | False |
| ClawBio | 55 -> 67 (+12) | T2 Caution -> T2 Caution | CA-DIRECT -> CA-DIRECT | 69 -> None | True | False |
| LabClaw | 28 -> 28 (+0) | T0 Rejected -> T0 Rejected | none -> none | None -> None | False | False |
| claude-scientific-skills | 39 -> 39 (+0) | T0 Rejected -> T0 Rejected | CA-DIRECT -> CA-DIRECT | 39 -> 39 | False | True |
| SciAgent-Skills | 48 -> 48 (+0) | T1 Quarantine -> T1 Quarantine | CA-INDIRECT -> CA-INDIRECT | 69 -> 69 | False | False |
| BioAgents | 48 -> 48 (+0) | T1 Quarantine -> T1 Quarantine | none -> none | None -> None | False | False |
| BioClaw | 39 -> 48 (+9) | T0 Rejected -> T1 Quarantine | CA-DIRECT -> CA-INDIRECT | 39 -> 69 | False | False |
| OpenClaw-Medical-Skills | 38 -> 38 (+0) | T0 Rejected -> T0 Rejected | none -> none | None -> None | False | False |
