# STEM BIO-AI Claim Matrix

**Target:** [REPOSITORY_NAME]
**Audit Date:** [DATE]
**Auditor:** [AUDITOR_NAME / AI_MODEL]
**Auditor Affiliation:** [self / independent / cross-team]
**Spec Version:** STEM BIO-AI v1.1.2

---

## Instructions

One row per finding. Every strong claim in the audit report must have a corresponding row here.

**Claim ID format:** CLM-[DOMAIN]-[NUMBER] (e.g., CLM-BIO-001)

**Confidence levels:**
- High: directly observed in code/config/workflow with specific evidence
- Moderate: indirectly supported through combination of signals
- Low: surface-level observation only, interpretation margin present

**Severity levels:**
- Critical: immediate safety or operational risk
- High: institutional reuse blocked without remediation
- Medium: review required before institutional adoption
- Low: improvement recommended, not blocking

---

## Matrix

| Claim ID | Repository | Finding Category | Claim Statement | Evidence Type | Source Path / Surface | Snapshot Ref | Line / Section Anchor | Observation | Auditor Interpretation | Confidence | Severity | Reproduction Status | Alternative Interpretation Considered | Final Adjudication | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CLM-[DOM]-001 | [REPO] | [CATEGORY] | [CLAIM] | [TYPE] | [PATH] | [REF] | [ANCHOR] | [OBSERVATION] | [INTERPRETATION] | [H/M/L] | [C/H/M/L] | [STATUS] | [ALT] | [ADJUDICATION] | [NOTES] |

---

## Finding Categories (standardized)

- Documentation-Reality Divergence
- Insecure Default
- Operational Exposure
- Mock-to-Production Ambiguity
- Licensing Ambiguity
- Scientific Validity Surface Gap
- Governance Surface Deficiency
- Validation Surface Gap
- Trust-Surface Inconsistency
- Ecosystem-Level Risk Pattern

---

## Reproduction Status Values

- Not executed
- Statically inspected
- Partially reproduced
- Runtime confirmed
- Blocked by external dependency
- Environment not available

---

## Claim Statement Style Guide

Use observation-first language:
- "Observed ..."
- "Executable evidence does not confirm ..."
- "Licensing surface is incomplete for ..."
- "No sufficient evidence was observed for ..."

Avoid intent attribution:
- NO: "Authors deliberately hid ..."
- YES: "Observable repository surface does not include ..."
