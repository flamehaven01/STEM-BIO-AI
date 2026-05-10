# STEM BIO-AI Calibration Profile Design

Version: draft for post-1.6.3 implementation discussion  
Status: design proposal, not active runtime behavior

---

## 1. Purpose

STEM BIO-AI already separates formal scoring, deterministic diagnostics, regulatory traceability, and AI advisory into distinct lanes.

What it does **not** yet separate cleanly is the **calibration surface**:

- stage weights
- tier boundaries
- clinical caps and hard floors
- evidence-only versus score-authoritative detector status
- reasoning-model status labels

In `1.6.3`, most of these values are still implemented as code constants plus prose in `SCORING_RATIONALE.md`. That is acceptable for a stable prototype, but it creates a long-term maintenance risk:

> if calibration values are easy to change but hard to govern, the architecture will drift even if the lane boundaries remain conceptually correct.

This document proposes a **versioned calibration profile** so STEM BIO-AI can remain maintainable without turning into a free-form tuning surface.

---

## 2. Problem Statement

As advisory systems become stronger, teams usually feel pressure to:

- raise or lower tier thresholds
- relax or tighten clinical caps
- promote diagnostics from evidence-only into score-bearing logic
- add new penalties or soften old ones
- reinterpret reasoning or advisory outputs as scoring evidence

If those changes happen ad hoc in code, three problems appear:

1. the formal score becomes harder to reproduce across versions
2. policy drift hides inside implementation edits
3. advisory or diagnostic signals may slowly leak into the formal score without an explicit governance decision

The issue is not whether calibration should ever change.

The issue is whether calibration changes are:

- versioned
- reviewable
- explainable in artifacts
- bounded by explicit promotion rules

---

## 3. Design Goal

The goal is **not** to let users arbitrarily tune the score from the CLI.

The goal is to make calibration:

- easy to inspect
- easy to version
- easy to compare between releases
- hard to mutate accidentally

In short:

> STEM BIO-AI needs easy maintenance, not easy drift.

---

## 4. Core Principle

Calibration should become a **policy object**, not a scattered implementation detail.

That means:

- the active scoring profile is represented in a versioned file
- result artifacts record which profile was used
- policy changes become visible release events
- score-affecting changes require explicit promotion criteria

This preserves the current architectural discipline:

- formal score remains deterministic
- diagnostics can stay evidence-only until promoted
- advisory remains structurally subordinate to the score
- regulatory mapping remains traceability support, not a score multiplier

---

## 5. Recommended Shape

Recommended location:

`policy/scoring_profile_v1.6.3.json`

Recommended future support:

- `policy/scoring_profile_v1.6.3.json`
- `policy/scoring_profile_benchmark_candidate.json`
- `policy/scoring_profile_dev_experimental.json`

Important restriction:

- normal users should select from named profiles
- normal users should **not** pass arbitrary weights or tier cutoffs on the command line

Good:

```bash
stem scan <repo> --policy default
stem scan <repo> --policy benchmark-candidate
```

Bad:

```bash
stem scan <repo> --stage1-weight 0.35 --t3-threshold 68 --cap 72
```

The first preserves governance.  
The second turns the tool into an untracked tuning console.

---

## 6. What the Profile Should Contain

Minimum recommended fields:

```json
{
  "policy_version": "1.6.3",
  "profile_name": "default",
  "profile_status": "authoritative_release",
  "weights": {
    "stage_1": 0.4,
    "stage_2r": 0.2,
    "stage_3": 0.4
  },
  "stage_baselines": {
    "stage_1": 60,
    "stage_2r": 60,
    "stage_3": 0
  },
  "tier_boundaries": {
    "T0_max": 39,
    "T1_min": 40,
    "T1_max": 54,
    "T2_min": 55,
    "T2_max": 69,
    "T3_min": 70,
    "T3_max": 84,
    "T4_min": 85
  },
  "clinical_policy": {
    "ca_no_disclaimer_cap": 69,
    "t0_hard_floor_cap": 39
  },
  "code_integrity_policy": {
    "C1_penalty": 10,
    "C2_score_affecting": false,
    "C3_score_affecting": false,
    "C4_score_affecting": false
  },
  "stage_3_policy": {
    "raw_max": 80,
    "normalization_mode": "round(raw/80*100)"
  },
  "diagnostic_policy": {
    "BIO_smiles_surface_integrity": "evidence_only",
    "BIO_smiles_rdkit_validation": "evidence_only",
    "BIO_smiles_parser_guard": "evidence_only",
    "BIO_silent_mock_fallback": "evidence_only",
    "BIO_traceability_manifest_surface": "evidence_only",
    "BIO_subprocess_run_trace": "evidence_only"
  },
  "reasoning_policy": {
    "status": "diagnostic_only_uncalibrated_initial_prior",
    "score_integration": "forbidden"
  }
}
```

This is not meant to be the final schema.  
It is the minimum useful shape.

---

## 7. Artifact Requirements

Every result object should record:

- `policy_version`
- `profile_name`
- `profile_status`
- `policy_sha256`

Why:

- two runs are not meaningfully comparable unless they share the same active profile
- policy drift should be visible in the artifact itself
- benchmark comparisons should be able to say whether differences came from repository evidence or policy revision

Recommended JSON example:

```json
"calibration_profile": {
  "policy_version": "1.6.3",
  "profile_name": "default",
  "profile_status": "authoritative_release",
  "policy_sha256": "..."
}
```

---

## 8. Diagnostics Graduation Policy

The hardest maintenance problem is not weight tuning.

It is detector promotion:

> when does an evidence-only detector become score-authoritative?

Recommended detector states:

- `evidence_only`
- `candidate_scored`
- `scored`
- `deprecated`

Recommended promotion gate before moving from `evidence_only` to `candidate_scored`:

1. commit-pinned benchmark fixtures exist
2. detector output is reproducible
3. false-positive review has been documented
4. a release note explains what changed
5. `SCORING_RATIONALE.md` is updated if the detector affects score logic

Recommended promotion gate before moving from `candidate_scored` to `scored`:

1. benchmark evidence shows the detector improves review precision
2. at least one release cycle of observation has occurred
3. the profile change is versioned as a policy revision

This is the governance mechanism that prevents “AI got more capable, so we quietly started scoring with it.”

---

## 9. Advisory Boundary Rule

The calibration profile should explicitly state that advisory output cannot rewrite the formal score unless a future architecture intentionally changes that rule.

Recommended field:

```json
"reasoning_policy": {
  "status": "diagnostic_only_uncalibrated_initial_prior",
  "score_integration": "forbidden"
}
```

That matters because boundary failures often begin as convenience:

- a provider looks helpful
- the advisory output seems more nuanced
- a team wants to “just incorporate it a little”

Once that happens without a versioned policy change, the formal score stops being what the architecture claims it is.

---

## 10. CLI Policy Surface

Recommended CLI behavior:

- `--policy default`
- `--policy <named_profile>`
- `--list-policies`

Not recommended:

- direct numeric overrides for weights, thresholds, caps, or detector promotion state

Developer-only experimental override support is acceptable if all of the following are true:

- it is clearly marked non-authoritative
- it writes a different `profile_status`
- output artifacts visibly say experimental policy was used
- it is excluded from default examples and documentation

---

## 11. Migration Plan

Suggested low-risk rollout:

### Phase 1: mirror only

- create the profile file
- keep scanner behavior unchanged
- expose profile metadata in JSON output
- verify the profile matches current release behavior exactly

### Phase 2: read-through

- scanner loads weights, thresholds, caps, and detector status from profile
- tests verify parity with old constant-based behavior

### Phase 3: governed evolution

- future score-affecting changes require:
  - profile update
  - rationale update
  - changelog entry
  - benchmark note when relevant

This sequence avoids a risky “big bang” rewrite.

---

## 12. Non-Goals

This proposal does **not** aim to:

- let users personalize trust scores
- introduce hidden model-based calibration
- turn regulatory mapping into a numerical score multiplier
- make advisory output part of the formal score
- replace benchmark or manual review with profile editing

It only aims to make calibration easier to maintain **without weakening lane boundaries**.

---

## 13. Final Recommendation

Yes: STEM BIO-AI should gain an easier calibration maintenance surface.

But the correct mechanism is:

> a versioned calibration profile with explicit promotion rules

not:

> ad hoc runtime tuning knobs

If the architecture is serious about preserving the distinction between:

- formal score
- diagnostics
- regulatory traceability
- advisory

then calibration must be governed with the same discipline.

The right outcome is not “more adjustable.”

The right outcome is:

**more maintainable, without becoming easier to drift.**
