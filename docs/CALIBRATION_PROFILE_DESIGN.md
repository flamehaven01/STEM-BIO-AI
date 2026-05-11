# STEM BIO-AI Calibration Profile Design

Version: updated for 1.6.7 derive/simulate preview implementation
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

In `1.6.7`, most score-affecting values are still implemented as runtime constants plus prose in `SCORING_RATIONALE.md`, even though mirror-only profile metadata, CLI-visible profile selection, and derive/simulate preview surfaces are now surfaced. That is acceptable for a stable prototype, but it creates a long-term maintenance risk:

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

`policy/scoring_profile.default.v1.json`

Recommended future support:

- `policy/scoring_profile.strict_clinical_adjacency.v1.json`
- `policy/scoring_profile.reproducibility_first.v1.json`
- `policy/scoring_profile.experimental.v1.json`

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
  "policy_schema_version": "1",
  "policy_version": "ca-policy-1.0",
  "tool_version_introduced": "1.6.5",
  "tool_version_last_validated": "1.6.7",
  "profile_name": "default",
  "profile_status": "authoritative_release",
  "profile_read_mode": "mirror_only",
  "weights": {
    "stage_1_percent": 40,
    "stage_2r_percent": 20,
    "stage_3_percent": 40
  },
  "stage_baselines": {
    "stage_1": 60,
    "stage_2r": 60,
    "stage_3": 0
  },
  "tier_policy": {
    "tier_names": ["T0", "T1", "T2", "T3", "T4"],
    "tier_boundaries": [40, 55, 70, 85],
    "boundary_semantics": "left_closed_right_open",
    "score_domain": "integer_0_to_100"
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
    "normalization": {
      "kind": "linear_round",
      "raw_max": 80,
      "target_max": 100,
      "rounding": "half_up_int"
    }
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
  },
  "governance_sources": {
    "ca_taxonomy_version": "ca-taxonomy-v1",
    "ca_taxonomy_source": "runtime_regex_hardcoded_in_scanner_py"
  }
}
```

This is not meant to be the final schema.  
It is the minimum useful shape.

Schema notes:

- weights should be stored as integer percentages, not floating-point fractions
- tier boundaries should be stored once as a single ordered array
- normalization should be represented as named semantics plus parameters, not a free-form expression string
- `policy_version` should be independent from the tool release version
- `profile_read_mode` must distinguish mirror-only exposure from authoritative runtime loading

Recommended `profile_status` state set:

- `preview_only`
- `experimental`
- `benchmark_candidate`
- `authoritative_release`
- `deprecated`

Recommended status transition path:

`preview_only -> experimental -> benchmark_candidate -> authoritative_release -> deprecated`

Other transitions should require an explicit migration note.

---

## 7. Artifact Requirements

Every result object should record:

- `policy_schema_version`
- `policy_version`
- `profile_name`
- `profile_status`
- `profile_read_mode`
- `policy_sha256`

Why:

- two runs are not meaningfully comparable unless they share the same active profile
- policy drift should be visible in the artifact itself
- benchmark comparisons should be able to say whether differences came from repository evidence or policy revision
- mirror-only and authoritative-read runs must not look equivalent in artifacts

`policy_sha256` must be defined precisely.

Recommended definition:

- canonicalize the policy JSON using sorted keys and UTF-8 encoding
- exclude the `policy_sha256` field itself from the hash input
- hash the canonicalized policy file bytes only

In `mirror_only` mode, the profile file may leave `policy_sha256` as `null`.

The runtime artifact should still surface the computed canonical hash so profile comparisons remain stable during Phase 1.

This hash does **not** claim to represent every runtime governance source.

Instead, runtime governance dependencies such as the CA taxonomy should be surfaced separately under `governance_sources`.

Recommended JSON example:

```json
"calibration_profile": {
  "policy_schema_version": "1",
  "policy_version": "ca-policy-1.0",
  "profile_name": "default",
  "profile_status": "authoritative_release",
  "profile_read_mode": "mirror_only",
  "policy_sha256": "..."
},
"governance_sources": {
  "ca_taxonomy_version": "ca-taxonomy-v1",
  "ca_taxonomy_source": "runtime_regex_hardcoded_in_scanner_py"
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

Recommended transition rules:

| From | To | Allowed? | Notes |
|---|---|---|---|
| `evidence_only` | `candidate_scored` | yes | requires promotion gate below |
| `candidate_scored` | `scored` | yes | requires promotion gate below |
| `candidate_scored` | `evidence_only` | yes | allowed if benchmark review regresses confidence |
| `scored` | `candidate_scored` | yes | allowed for rollback after release observation |
| `scored` | `deprecated` | yes | allowed when detector is retired |
| `evidence_only` | `deprecated` | yes | allowed when detector is abandoned |
| `deprecated` | any active state | no by default | require explicit redesign note |

Recommended promotion gate before moving from `evidence_only` to `candidate_scored`:

1. commit-pinned benchmark fixtures exist for at least `N >= 20` repositories
2. detector output is reproducible across `3` consecutive identical runs
3. false-positive review has been documented with observed `false_positive_rate <= 0.05`
4. a release note explains what changed
5. `SCORING_RATIONALE.md` is updated if the detector affects score logic

Recommended promotion gate before moving from `candidate_scored` to `scored`:

1. benchmark evidence shows the detector improves review precision on the maintained fixture set
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

## 11. Researcher UX and Participation Model

The most important UX constraint is this:

> researchers should be able to influence policy intent without turning the CLI into a free-form scoring console.

That means STEM BIO-AI should prefer:

- named profile templates
- guided questions
- side-by-side score diffs
- explicit promotion to shared policy

over:

- raw numeric knobs
- hidden threshold editing
- untracked one-off scoring profiles

### 11.1 Starting Point: Profile Templates

The first interaction should not be:

> "enter your own weights and caps"

It should be:

> "which evaluation posture best matches your repository context?"

Recommended starter profiles:

- `default`
- `strict_clinical_adjacency`
- `reproducibility_first`
- `research_repo_baseline` (deferred until explicitly defined)
- `documentation_lenient` (deferred until explicitly defined)
- `biosecurity_cautious` (deferred until explicitly defined)

These names are easier for researchers to reason about than raw numbers.

### 11.2 Guided Policy Builder

After a template is selected, the next layer should be a guided builder rather than free-form editing.

Examples of acceptable questions:

- "Should code-integrity evidence outweigh README surface evidence?"
- "Should clinical-adjacent claims trigger stricter caps?"
- "Should bias/limitations require structured sections rather than term presence?"
- "Should replication evidence matter more for your workflow?"

The user answers policy questions.

The system translates them into profile deltas.

This preserves usability while keeping the policy surface inspectable.

### 11.2.1 Researcher Intent Scale

Before users touch any named policy, STEM BIO-AI should reduce the interpretation gap between:

- what the researcher actually cares about
- what the default profile currently emphasizes

The recommended mechanism is a **researcher intent layer** built around short `0–5` scales.

Important boundary:

> the `0–5` scale is a UX input surface, not part of the formal score engine.

In other words:

- users do **not** set formal weights directly
- users do **not** set tier thresholds directly
- users do **not** generate a score by summing their answers

Instead, the scale helps the system infer which existing policy posture is closer to the researcher's intent.

Recommended scale interpretation:

- `0` = do not emphasize this factor
- `1` = very light emphasis
- `2` = light emphasis
- `3` = moderate emphasis
- `4` = strong emphasis
- `5` = very strong emphasis

Recommended question areas:

- how strict clinical-adjacent claims should be treated
- whether code-integrity evidence should outweigh README/documentation evidence
- how much reproducibility evidence should matter
- whether structured limitations should be required before partial credit is awarded

This approach borrows the usability advantage of Likert-style scales without turning the scanner into a free-form tuning instrument.

### 11.2.2 Why the Scale Belongs in UX, Not Scoring

Researchers can usually answer:

> "clinical-adjacent claims should be treated very strictly"

more reliably than:

> "set the CA cap delta to -12 and reduce the Stage 1 weight by 0.05"

That is why the scale should live in the interview layer.

The formal engine should still consume:

- named profiles
- explicit policy objects
- versioned calibration state

The scale is only a translation surface between human intent and governed policy.

### 11.2.3 Translation Rule

The system should map researcher answers to one of three outcomes:

1. recommend an existing named profile
2. show a preview-only profile delta
3. show that the default profile already matches the stated posture under an explicit rule

This is safer than letting the user edit raw scoring parameters directly.

The initial implementation should prefer an auditable rule table over a hidden similarity function.

Recommended intent variables:

- `clinical_strictness`
- `code_integrity_priority`
- `reproducibility_priority`
- `structured_limitations_requirement`

Recommended first-pass decision rules:

| Condition | Outcome |
|---|---|
| `clinical_strictness >= 4` and `reproducibility_priority <= 3` | recommend `strict_clinical_adjacency` |
| `reproducibility_priority >= 4` and `clinical_strictness <= 3` | recommend `reproducibility_first` |
| `code_integrity_priority <= 2` and `structured_limitations_requirement <= 2` and `clinical_strictness <= 3` | recommend `documentation_lenient` only after that profile is explicitly defined; otherwise fall back to `preview_only` |
| all four values are `2` or `3` | keep `default` |
| no named profile rule matches | generate `preview_only` profile delta from explicit bounded deltas only |

The purpose of this first-pass table is not to be perfect.

It is to make the translation layer visible, reviewable, and testable.

Rule priority:

- evaluate rules top-down
- stop at the first named-profile match
- if multiple strong postures are simultaneously requested and no single named profile dominates, fall back to `preview_only`

Example:

- `clinical_strictness = 4`
- `reproducibility_priority = 4`

This should fall back to `preview_only` in the initial implementation rather than pretending one named posture has clear priority.

Zero-value meaning:

- `0` means minimal emphasis
- `0` does **not** remove or disable an axis
- therefore `0` participates in threshold checks such as `<= 2`

Recommended "default already matches" rule:

- if the selected baseline is `default`
- and all four intent variables are in the `2..3` range
- and no explicit named-profile rule is triggered

then the system should report that the default profile already matches the stated posture closely enough to avoid a custom preview.

Recommended `preview_only` boundary for the first implementation:

- do **not** compute nearest-profile distance
- do **not** infer hidden similarity scores
- do **not** mutate arbitrary raw numbers

Instead:

- start from the selected baseline profile
- apply explicit bounded deltas associated with the triggered answers
- mark the result as `preview_only`

This keeps the intent layer auditable during the first implementation cycle.

Illustrative bounded deltas for the first implementation:

| Triggered answer | Allowed `preview_only` delta shape |
|---|---|
| `clinical_strictness >= 4` with no named-profile match | switch to stricter CA posture only; do not change unrelated weights |
| `reproducibility_priority >= 4` with no named-profile match | raise Stage 4 emphasis only within predeclared policy bounds |
| `structured_limitations_requirement >= 4` with no named-profile match | require stricter Stage 3 B2 partial-credit posture only |
| multiple strong answers with no named-profile match | combine only explicitly listed bounded deltas; do not infer new arithmetic outside documented policy fields |

These are not hidden similarity operations.

They are bounded, inspectable policy deltas that must be documented before activation.

### 11.2.4 Comparison Output

This subsection describes the immediate output of the intent-scale flow.

If the scale is used, the system should immediately show:

- chosen baseline profile
- recommended profile or preview delta
- score difference on the current repository
- tier difference on the current repository
- which policy dimensions changed

The key UX question is not:

> "what settings changed?"

It is:

> "what did the repository outcome change to, and why?"

### 11.2.5 Minimum Starter Profile Definitions

Before implementation begins, at least two named profiles should have explicit documented diffs.

Required minimum:

- `default`
- `strict_clinical_adjacency`

Strongly recommended:

- `reproducibility_first`

Deferred until explicitly defined:

- `documentation_lenient`
  - row 3 of the wizard rule table must not recommend this profile until its actual policy diff is documented here
- `research_repo_baseline`
  - must not appear in active wizard recommendation paths until its actual policy diff is documented here
- `biosecurity_cautious`
  - must not appear in active wizard recommendation paths until its actual policy diff is documented here

Minimum documented diff fields per profile:

- stage weights
- clinical cap / hard-floor posture
- Stage 3 B2 strictness posture
- Stage 4 emphasis posture

Illustrative starter diff:

| Profile | Stage weights | Clinical posture | B2 posture | Stage 4 posture |
|---|---|---|---|---|
| `default` | `0.40 / 0.20 / 0.40` | standard CA cap / hard-floor rules | structured boundary language for partial credit | current baseline |
| `strict_clinical_adjacency` | same as `default` initially | stricter CA posture candidate for later policy revision | same as `default` unless explicitly changed | current baseline |
| `reproducibility_first` | future profile; must be defined before implementation if referenced by wizard rules | same as `default` unless explicitly changed | same as `default` unless explicitly changed | stronger replication emphasis candidate |

These do not need to be final policy values yet, but they must exist as explicit diffs before the wizard can be treated as an implementation-ready surface.

These values are illustrative placeholders.

Phase 1 implementation must not proceed until this table contains actual policy diffs for every named profile that the active wizard rule table is allowed to recommend.

### 11.3 Side-by-Side Simulation

This subsection describes the more general simulation surface, which may also be used outside the intent-scale interview.

The most important feedback loop is not the profile editor itself.

It is the comparison view.

Researchers should be able to see:

- default profile result
- custom profile result
- score delta
- tier delta
- cap / hard-floor delta
- which evidence lanes changed the outcome

The right question is not:

> "what numbers did I change?"

It is:

> "what review outcome changed, and why?"

### 11.4 Roles

The intended governance model is not "every researcher defines the official score alone."

Recommended roles:

- `researcher`
  - explains domain priorities
  - surfaces false positives / false negatives
  - evaluates whether the default policy fits the repository context
- `policy steward`
  - maintains release-grade named profiles
  - reviews score-affecting changes
  - prevents silent drift between personal and team policy
- `tool`
  - computes policy diff
  - computes result diff
  - records profile metadata in artifacts

This division keeps domain experts involved without sacrificing reproducibility.

### 11.5 Promotion Path

Recommended progression:

1. personal preview profile
2. side-by-side run against real repository output
3. review and comparison against default profile
4. promotion to named team policy if approved

That promotion should update:

- `profile_name`
- `profile_status`
- `policy_sha256`
- changelog / rationale references when score logic changes

### 11.6 Interface Direction

Recommended near-term CLI additions:

- `stem policy list`
- `stem policy explain <name>`
- `stem scan <repo> --policy <name>`

Recommended later UX additions:

- wizard-style policy derivation
- side-by-side simulation view
- profile diff explanation panel

The guiding rule is:

> researchers should tune posture through explicit choices, not hidden arithmetic.

---

## 12. Migration Plan

Suggested low-risk rollout:

### Phase 1: mirror only

- create the profile file
- keep scanner behavior unchanged
- expose profile metadata in JSON output
- verify the profile matches current release behavior exactly using a differential fixture set with gold outputs

Recommended fixture format:

```json
{
  "fixture_name": "default_profile_parity_small_repo",
  "target_repo": "tests/fixtures/repos/small_repo_a",
  "expected": {
    "raw_score_before_floor": 67,
    "final_score": 67,
    "formal_tier": "T2 Caution",
    "score_cap": null
  }
}
```

Recommended fixture location:

- `tests/fixtures/calibration_profiles/`

Recommended Phase 1 parity target fields:

- `raw_score_before_floor`
- `final_score`
- `formal_tier`
- `classification.score_cap`

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

## 13. Suggested Release Sequence

The current implementation state suggests the following release order:

- `1.6.5`
  - introduce profile files
  - expose `policy_version`, `profile_name`, `profile_status`, `policy_sha256`
  - keep named-profile selection narrow and deterministic
- `1.6.6`
  - add `stem policy list` and `stem policy explain`
  - support explicit `--policy <name>` on scan commands
- `1.6.7`
  - add guided policy derivation and side-by-side simulation

This keeps calibration governance ahead of personalization.

---

## 14. Non-Goals

This proposal does **not** aim to:

- let users personalize trust scores
- introduce hidden model-based calibration
- turn regulatory mapping into a numerical score multiplier
- make advisory output part of the formal score
- replace benchmark or manual review with profile editing

It only aims to make calibration easier to maintain **without weakening lane boundaries**.

---

## 15. Final Recommendation

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
