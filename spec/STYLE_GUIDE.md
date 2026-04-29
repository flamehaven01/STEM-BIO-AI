# STEM BIO-AI Institutional Style Guide

For audit reports intended for institutional submission or external review.

## Core Principles

1. **Observation before interpretation.** State what was seen, then why it matters.
2. **No intent attribution.** "Observable surface does not include..." not "Authors deliberately hid..."
3. **Calibrated severity language.** Use graduated terms matching actual evidence strength.

## Expression Calibration

| Avoid | Prefer |
|-------|--------|
| unsafe | institutionally unsafe under observed configuration |
| fake | capability surface appears stronger than executable evidence confirms |
| broken governance | governance surface is insufficient for institutional confidence |
| overwhelmingly no | predominantly insufficient for institutional trust establishment |
| mock implementation | placeholder or weakly substantiated execution path |

## Three-Part Finding Structure

For each finding, maintain separation:

1. **Observed:** [fact only, no interpretation]
2. **Interpretation:** [why it matters institutionally]
3. **Implication:** [what action this suggests]

Example:
- Observed: No root LICENSE file observed.
- Interpretation: Licensing surface is incomplete or ambiguous.
- Implication: Institutional reuse review would require manual clarification.

## Report-Level Language

- "trust not established" -- acceptable at any formality level
- "clinical use prohibited" -- acceptable, matches regulatory language
- "supervised pilot eligible" -- clear operational directive

## Claim Matrix Language

Use these patterns for Claim Statements:
- "Observed ..."
- "Executable evidence does not confirm ..."
- "Licensing surface is incomplete for ..."
- "No sufficient evidence was observed for ..."
