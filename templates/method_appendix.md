# STEM BIO-AI Method Appendix

**Spec Version:** STEM BIO-AI v1.1.2
**Execution Mode:** [LOCAL_ANALYSIS / FULL / SEARCH_ONLY / MANUAL]

## Rubric Summary

See `spec/STEM-AI_v1.1.2_CORE.md` for the full canonical rubric.

## Audit-Layer Relationship

- Technical audit establishes what the repository actually does.
- STEM BIO-AI classifies whether the artifact surface built around that repository is sufficient for institutional trust establishment.

Technical audit is therefore the fact-extraction layer. STEM BIO-AI is the trust-classification layer.

### Stage 1: README Intent (Weight: 0.40)
- H1-H6: Hype deductions (-5 to -10 pts each)
- R1-R5: Rigor additions (+10 to +15 pts each)
- R2/R3 active penalties for CA-DIRECT (-10) and CA-INDIRECT (-5)
- Baseline: 60 pts

### Stage 2: Cross-Platform (Weight: 0.20)
- F1-F4: Fame-seeking deductions
- A1-A4: Authentic discourse additions
- Baseline: 50 (nascent) or 60 (established)

### Stage 3: Code Debt (Weight: 0.40)
- T1-T4: Technical responsibility (0-15 pts each)
- B1-B3: Biological integrity (0-15 pts each)
- Trajectory modifier: +/-5 pts
- T4 PENDING normalization: denominator = 80

### Stage 3G: Governance Overlay (Advisory)
- G1-G5: 0-5 pts each (max 25)
- Does not change base tier

### C1-C4: Code Integrity (LOCAL_ANALYSIS only)
- C1 FAIL triggers RP3 (-10 pts)
- C2-C4 are advisory

## Confidence Assignment Rule
- High: directly observed in code/config/workflow
- Moderate: indirectly supported through combined signals
- Low: surface-level observation, interpretation margin present

## Audit Stop Conditions
- T0_HARD_FLOOR triggered: skip all score computation
- Private repository: refuse audit (TV-1)
- Personal attack purpose: refuse (TV-2)

## Escalation Criteria
- Score within 3 points of tier boundary: flag for human review
- CODE_PATH contradicts TEXT_PATH: record explicitly, flag finding
- CA-DIRECT with Stage 3 <= 40: CA-DIRECT redistribution warning
