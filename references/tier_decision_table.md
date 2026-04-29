# STEM BIO-AI Tier Decision Table

Operational meaning of each tier for institutional decision-makers.

## Tier Definitions and Institutional Actions

| Tier | Score | Trust Signal | Institutional Action | Permitted Scope |
|------|-------|-------------|---------------------|-----------------|
| T0 Rejected | 0-39 | Trust not established | Do not integrate. Do not rely without repository-specific expert validation. Clinical use prohibited. No exceptions. | None |
| T1 Quarantine | 40-54 | High risk, structurally interesting | Educational and exploratory use only. Air-gapped systems. No patient-adjacent data. Human review of all outputs. Time-limited deployment with re-evaluation. | Scope A (Research Only) |
| T2 Caution | 55-69 | Bounded review candidate | Supervised non-clinical use. Governance overlay required if deploying. Continuous monitoring. No autonomous clinical decision support. | Scope A (Research Only) |
| T3 Review | 70-84 | Supervised pilot eligible | Supervised clinical pilot candidate. Full governance controls required. Human-in-the-loop mandatory. Regulatory pre-submission recommended. | Scope A + B (Supervised Pilot) |
| T4 Approved | 85-100 | Operational trust candidate | Verified deployment eligible. Full governance layer required. Regulatory submission completed or in progress. Domain validation mandatory. | Scope A + B + C (D: regulatory) |

## Governance Overlay Interaction

| Base Tier | Overlay Verdict | Operational Interpretation |
|-----------|----------------|--------------------------|
| T0 | NONE | No trust, no governance. Standard T0. |
| T0 | BOUNDED | Repo still low-trust, but bounded structural remediation is real. Does NOT justify T3 promotion. |
| T0 | STRONG | Governance is real but native maturity gap remains critical. Re-audit after remediation. |
| T2 | STRONG | Meaningful maturity + governance. Formal T3 requires base score math, not overlay. |
| T3 | STRONG | Strong candidate for supervised pilot with full governance. |

## T0_HARD_FLOOR Override

When H3 (fully autonomous clinical) AND H4 (AGI-level claims) both trigger:
- Final Score = 0, Tier = T0, USE_SCOPE = None
- No exceptions. No governance overlay can override.
- Hard floor notice mandatory in report.

## CA-DIRECT Redistribution Warning

When Stage 2 = N/A AND CA-DIRECT AND Stage 1 >= 70 AND Stage 3 <= 40:
- Score is mathematically valid but potentially misleading
- README quality may mask engineering deficiency
- Mandatory advisory in Final Judgment
- Reviewers should weight Stage 3 independently for clinical decisions
