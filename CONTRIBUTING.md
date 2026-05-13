# Contributing to STEM BIO-AI

Thank you for your interest in improving STEM BIO-AI. This document explains how to contribute effectively.

## Types of Contributions

### 1. Discrimination Examples (Most Common)

When you run a live audit and encounter a boundary case that existing examples do not cover, add it to the appropriate file in `discrimination/`.

**Format:**
```
TRIGGERS (deduct -N):
  "[exact quoted text from README]"
    -- [why this triggers the item]

DOES NOT TRIGGER:
  "[exact quoted text]"
    -- [why this does not trigger]
```

**Submit via:** Pull request to `discrimination/` files only. No spec changes needed.

### 2. Clinical Adjacency Triggers

If you encounter a clinical tool, library, or keyword not in the current 60+ trigger list, add it to `references/clinical_adjacent_triggers.md`.

**Requirements:**
- Tool must be used in actual clinical or patient-adjacent contexts
- Include the CA severity tier (DIRECT / INDIRECT / PLANNED)
- Provide a real-world usage example

### 3. Template Improvements

Templates in `templates/` can be improved for clarity, completeness, or institutional compatibility. Changes must not alter the scoring logic or output structure defined in `spec/`.

### 4. Script Improvements

Scripts in `scripts/` can be improved for portability, accuracy, or coverage. All scripts must:
- Run on bash (Linux/macOS) without external dependencies
- Include `set -euo pipefail` error handling
- Document their purpose in header comments
- Not modify any files outside the audit output directory

### 5. Rubric Modifications (Requires Discussion)

Changes to the core rubric in `spec/STEM-AI_v1.1.2_CORE.md` follow strict rules:

**VARIABLE items** (LLM discretion, evidence narration, output language):
- Can be modified via PR with rationale

**IMMUTABLE items** (score formula, tier boundaries, weights, hard floors):
- Require a new version number (e.g., 1.1.1 -> 1.2.0)
- Must be discussed in a GitHub Issue first
- Must include impact analysis on existing audit results
- Must be approved by a maintainer

### 6. Calibration Profile Proposals

Calibration contributions are welcome, but they follow a stricter path than normal docs or discrimination-example edits.

Allowed contribution shapes:

- propose new `derive` / `simulate` posture examples
- propose bounded `preview_only` deltas
- propose an `experimental` named profile with documented diffs
- provide benchmark or repository-side comparison evidence for profile promotion

Not allowed as direct contribution outcomes:

- silently changing the authoritative default scoring policy
- introducing ad hoc CLI numeric tuning knobs
- promoting score-affecting detector logic without documented policy/rationale review

If you want to change calibration behavior:

1. describe the domain posture you want
2. show the `default` vs preview/profile comparison on a real repository
3. document the proposed policy diff
4. explain whether the change should stay `preview_only`, become `experimental`, or be considered for future authoritative promotion

Authoritative score policy changes still require governed profile promotion, rationale updates, and maintainer review. See [`docs/CALIBRATION_PROFILE_DESIGN.md`](docs/CALIBRATION_PROFILE_DESIGN.md).

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b add-h2-example`)
3. Make changes
4. Run validation (`bash scripts/validate_skill_structure.sh`)
5. Submit PR with description of:
   - What changed
   - Why (link to live audit finding if applicable)
   - Impact on existing scores (if any)

## Code of Conduct

- STEM BIO-AI evaluates repository artifacts, not people
- Contributions must not introduce personal attacks or bias
- Clinical safety is the priority; marketing is not
- Evidence-based claims only; speculation is not acceptable

## Questions?

Open a GitHub Issue with the `question` label.
