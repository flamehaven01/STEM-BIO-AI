# Errata and Revision Log

**Parent Document:** [REPORT_ID]
**Spec Version:** STEM BIO-AI v1.1.2

---

## Errata Policy

1. **Factual corrections** (wrong file path, arithmetic error, misattributed finding):
   - Issued as errata entry below with correction date
   - Original text preserved with strikethrough; corrected text appended
   - Score recalculation performed if error affects numeric result

2. **Interpretation disputes** (repository maintainer disagrees with finding):
   - Dispute recorded with maintainer's stated counter-interpretation
   - Auditor response recorded
   - Finding status updated to: CONFIRMED / REVISED / WITHDRAWN
   - Score recalculated only if finding is REVISED or WITHDRAWN

3. **Scope corrections** (finding applied to wrong severity tier):
   - Treated as factual correction
   - Full recalculation chain documented

4. **Repository updates post-audit** (repo changed after snapshot date):
   - Not treated as errata -- original audit remains valid for snapshot date
   - New audit required to reflect current state
   - Link to re-audit appended if performed

---

## Revision Log

| Errata ID | Date | Type | Original Statement | Correction | Score Impact | Issued By |
|-----------|------|------|--------------------|------------|-------------|-----------|
| ERR-001 | [DATE] | [factual/dispute/scope] | [ORIGINAL] | [CORRECTED] | [+/- pts or N/A] | [NAME] |

---

## Dispute Log

| Dispute ID | Date Filed | Filed By | Finding Ref | Counter-Interpretation | Auditor Response | Status | Resolution Date |
|------------|-----------|----------|-------------|----------------------|-----------------|--------|----------------|
| DSP-001 | [DATE] | [NAME] | [CLM-ID] | [COUNTER] | [RESPONSE] | [OPEN/CONFIRMED/REVISED/WITHDRAWN] | [DATE] |

---

## Score Recalculation History

| Recalc ID | Date | Trigger | Original Score | Revised Score | Original Tier | Revised Tier | Justification |
|-----------|------|---------|---------------|--------------|--------------|-------------|---------------|
| RCL-001 | [DATE] | [ERR-ID or DSP-ID] | [SCORE] | [SCORE] | [TIER] | [TIER] | [REASON] |

---

## Amendment Versioning Rule

- Errata that do not change the tier: append to this log, no document version change
- Errata that change the tier: increment document version (e.g., v1.0 -> v1.1)
- Complete re-audit: new document ID, link from this errata log
