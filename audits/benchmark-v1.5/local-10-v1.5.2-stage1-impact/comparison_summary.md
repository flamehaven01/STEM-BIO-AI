# Local-10 v1.5.2 Stage 1 Impact

- Records: 10
- Tier changes vs v1.3.2 baseline: 1
- Score delta range: -2 to 4
- Mean score delta: 0.2
- Repos with H1-H6 hype penalties: 1
- Repos with R1-R5 responsibility credit: 3
- v1.5.2 tier distribution: {'T0 Rejected': 7, 'T2 Caution': 1, 'T1 Quarantine': 2}

## Interpretation

- Stage 1 H/R scoring did not create broad tier inflation on local-10.
- Only one repository changed tier: ClawBio moved from T1 to T2, remaining under the CA-DIRECT no-disclaimer cap.
- BioAgents is the only repository with a hype penalty hit, and it stayed in the same tier.
- T0 hard floors and score caps kept direct clinical-adjacent repositories from jumping to high-confidence tiers.

| Repo | Score | Tier | Stage 1 | H total | R + | R - | R net | H hits | R+ hits |
|---|---:|---|---:|---:|---:|---:|---:|---|---|
| Biomni | 36 -> 36 (+0) | T0 Rejected -> T0 Rejected | 40 -> 40 (+0) | 0 | 0 | 0 | 0 | - | - |
| AI-Scientist | 36 -> 36 (+0) | T0 Rejected -> T0 Rejected | 40 -> 40 (+0) | 0 | 0 | 0 | 0 | - | - |
| CellAgent | 28 -> 28 (+0) | T0 Rejected -> T0 Rejected | 40 -> 40 (+0) | 0 | 0 | 0 | 0 | - | - |
| ClawBio | 54 -> 58 (+4) | T1 Quarantine -> T2 Caution | 30 -> 40 (+10) | 0 | 20 | -20 | 0 | - | R4_demographic_bias_boundary, R5_reproducibility_provisions |
| LabClaw | 28 -> 28 (+0) | T0 Rejected -> T0 Rejected | 40 -> 40 (+0) | 0 | 0 | 0 | 0 | - | - |
| claude-scientific-skills | 39 -> 39 (+0) | T0 Rejected -> T0 Rejected | 30 -> 55 (+25) | 0 | 25 | -10 | 15 | - | R2_regulatory_framework, R4_demographic_bias_boundary |
| SciAgent-Skills | 48 -> 48 (+0) | T1 Quarantine -> T1 Quarantine | 60 -> 60 (+0) | 0 | 0 | -10 | -10 | - | - |
| BioAgents | 50 -> 48 (-2) | T1 Quarantine -> T1 Quarantine | 70 -> 65 (-5) | -5 | 0 | 0 | 0 | H4_breakthrough_marketing_hype | - |
| BioClaw | 39 -> 39 (+0) | T0 Rejected -> T0 Rejected | 60 -> 60 (+0) | 0 | 10 | -20 | -10 | - | R4_demographic_bias_boundary |
| OpenClaw-Medical-Skills | 38 -> 38 (+0) | T0 Rejected -> T0 Rejected | 40 -> 40 (+0) | 0 | 0 | 0 | 0 | - | - |
