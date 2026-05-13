# STEM BIO-AI Calibration Profile Architecture

Version: 1.7.2
Status: implemented mirror-only calibration contract with derive/simulate preview surfaces; 1.7.2 preview hardening complete; authoritative read-through remains future work

---

## 1. Current State

STEM BIO-AI already separates formal scoring, deterministic diagnostics, regulatory traceability, and AI advisory into distinct lanes.

As of `1.7.2`, the repository ships a real calibration architecture:

- packaged profiles in `policy/`
- schema and runtime validation
- result metadata surfacing for active profile identity
- CLI policy visibility via `stem policy list`, `stem policy explain`, and `--policy <name>`
- researcher-intent preview surfaces via `stem policy derive` and `stem policy simulate`

What is still not fully separated is the **authoritative score read-through surface**:

- stage weights
- tier boundaries
- clinical caps and hard floors
- evidence-only versus score-authoritative detector status
- reasoning-model status labels

In `1.7.2`, most score-affecting values are still implemented as runtime constants plus prose in `SCORING_RATIONALE.md`, even though mirror-only profile metadata, CLI-visible profile selection, and derive/simulate preview surfaces are already live. That is acceptable for the current release line, but it still creates a long-term maintenance risk:

> if calibration values are easy to change but hard to govern, the architecture will drift even if the lane boundaries remain conceptually correct.

This document describes the **implemented versioned calibration profile architecture** and the remaining governed path to authoritative read-through.

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

## 5. Implemented Shape

Current packaged profile files:

`policy/scoring_profile.default.v1.json`
`policy/scoring_profile.strict_clinical_adjacency.v1.json`

Deferred profiles:

- `reproducibility_first`
- `documentation_lenient`
- `research_repo_baseline`
- `biosecurity_cautious`

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

## 6. Current Profile Contract

Current shipped fields:

```json
{
  "policy_schema_version": "1",
  "policy_version": "ca-policy-1.0",
  "tool_version_introduced": "1.6.5",
  "tool_version_last_validated": "1.7.2",
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

This is the active shipped schema family in `1.7.2`.

Schema notes:

- weights should be stored as integer percentages, not floating-point fractions
- tier boundaries should be stored once as a single ordered array
- normalization should be represented as named semantics plus parameters, not a free-form expression string
- `policy_version` should be independent from the tool release version
- `profile_read_mode` must distinguish mirror-only exposure from authoritative runtime loading
- `stage_3_policy.b2_partial_credit_mode` is currently a declared mirror-only profile field; authoritative Stage 3 B2 scoring in `1.7.2` still follows the hardcoded scanner path and does not yet read this value directly
- `governance_sources.ca_taxonomy_version` must increment whenever runtime CA trigger membership, severity mapping, or cap-relevant phrase semantics change

Current `profile_status` state set:

- `preview_only`
- `experimental`
- `benchmark_candidate`
- `authoritative_release`
- `deprecated`

Current status transition path:

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

Current active named profiles:

- `default`
- `strict_clinical_adjacency`

Deferred named profiles:

- `reproducibility_first`
- `research_repo_baseline`
- `documentation_lenient`
- `biosecurity_cautious`

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

The implemented mechanism is a **researcher intent layer** built around short `0–5` scales.

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

Current question areas:

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

The current implementation uses an auditable rule table instead of a hidden similarity function.

Current intent variables:

- `clinical_strictness`
- `code_integrity_priority`
- `reproducibility_priority`
- `structured_limitations_requirement`

Current `1.7.2` decision rules:

| Condition | Outcome |
|---|---|
| `clinical_strictness >= 4` and `reproducibility_priority <= 3` | recommend `strict_clinical_adjacency` |
| all four values are `2` or `3` | keep `default` |
| no named profile rule matches | generate `preview_only` profile delta from explicit bounded deltas only |

This narrow table is intentional. It keeps the translation layer visible, reviewable, and testable without pretending that every strong posture already has a release-grade named profile. In particular, `reproducibility_first` remains deferred in `1.7.2`; high reproducibility answers still fall back to `preview_only` Stage 4 emphasis rather than a named recommendation.

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

Current "default already matches" rule:

- if the selected baseline is `default`
- and all four intent variables are in the `2..3` range
- and no explicit named-profile rule is triggered

then the system should report that the default profile already matches the stated posture closely enough to avoid a custom preview.

Current `preview_only` boundary:

- do **not** compute nearest-profile distance
- do **not** infer hidden similarity scores
- do **not** mutate arbitrary raw numbers

Instead:

- start from the selected baseline profile
- apply explicit bounded deltas associated with the triggered answers
- mark the result as `preview_only`

This keeps the intent layer auditable during the first implementation cycle.

Current bounded deltas used in preview-only mode:

| Triggered answer | Allowed `preview_only` delta shape |
|---|---|
| `clinical_strictness >= 4` with no named-profile match | switch to stricter CA posture only; do not change unrelated weights |
| `reproducibility_priority >= 4` with no named-profile match | raise Stage 4 emphasis only within predeclared policy bounds |
| `structured_limitations_requirement >= 4` with no named-profile match | require stricter Stage 3 B2 partial-credit posture only |
| multiple strong answers with no named-profile match | combine only explicitly listed bounded deltas; do not infer new arithmetic outside documented policy fields |

These are active preview-only deltas in `1.7.2`. They are not hidden similarity operations and they do not mutate the authoritative scan path.

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

### 11.2.5 Current Named Profile Definitions

The current implementation defines two named profiles:

- `default`
- `strict_clinical_adjacency`

Deferred until explicitly defined:

- `documentation_lenient`
  - not active in the `1.7.2` rule table
- `research_repo_baseline`
  - not active in the `1.7.2` rule table
- `biosecurity_cautious`
  - not active in the `1.7.2` rule table
- `reproducibility_first`
  - intentionally deferred until an actual policy diff exists and a release-grade recommendation path is defined

Documented diff fields per active profile:

- stage weights
- clinical cap / hard-floor posture
- Stage 3 B2 strictness posture
- Stage 4 emphasis posture

Current starter diff:

| Profile | Stage weights | Clinical posture | B2 posture | Stage 4 posture |
|---|---|---|---|---|
| `default` | `0.40 / 0.20 / 0.40` | standard CA cap / hard-floor rules | structured boundary language for partial credit | current baseline |
| `strict_clinical_adjacency` | `0.40 / 0.20 / 0.40` | tighter `ca_no_disclaimer_cap=60`, tighter `t0_hard_floor_cap=35` | same as `default` | `baseline` |

Any additional named profile must document its concrete diff here before it becomes eligible for CLI recommendation.

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

### 11.4.1 Researcher Participation Rules

The participation model should stay simple:

- researchers may propose posture changes
- researchers may run `derive` and `simulate`
- researchers may edit personal or branch-local preview profiles for comparison work
- researchers should not directly redefine the release-grade default policy on the authoritative score path

The key distinction is:

- `preview_only` and `experimental` are valid spaces for domain input
- `authoritative_release` is a governed release artifact

This means a researcher can legitimately say:

> "for this domain, I want stricter clinical-adjacent treatment and stronger reproducibility emphasis"

but should not unilaterally convert that statement into:

- new official tier boundaries
- new default caps
- new score-bearing detector promotion
- new release-grade policy semantics

The system should therefore optimize for:

- easy posture expression
- easy repository-specific simulation
- hard-to-mutate official policy

### 11.4.2 Operating Principles

Operationally, the collaboration rule is:

1. the researcher expresses domain priorities
2. the tool translates those priorities into a visible named-profile recommendation or `preview_only` delta
3. the policy steward decides whether that posture remains local, becomes experimental, or is promoted into a release-grade policy artifact

In practice:

- a researcher should be able to explore calibration without editing scanner code
- a steward should be able to reject score-affecting drift even when the local preview is reasonable
- artifacts should clearly distinguish personal preview from official release policy

The intended output is not "personalized truth."

The intended output is:

- a stable official score policy
- a transparent preview lane for domain-specific posture testing
- an explicit governance path between the two

### 11.4.3 Responsibility Matrix

| Action | Researcher | Policy steward | Tool |
|---|---|---|---|
| express domain posture | primary | optional review | guided input surface |
| run `stem policy derive` | primary | optional review | translates intent |
| run `stem policy simulate` | primary | optional review | computes baseline vs preview |
| edit `preview_only` deltas for local exploration | allowed | review optional | validates bounded deltas |
| create or modify `experimental` named profiles | propose | approve / reject | validates profile schema and metadata |
| promote a profile to `benchmark_candidate` | propose evidence | required approval | records status transition |
| promote a profile to `authoritative_release` | provide domain rationale | required approval | requires parity / benchmark metadata |
| change default release policy semantics | no unilateral authority | required owner | records artifact provenance |
| change score-bearing detector status | no unilateral authority | required owner | enforces transition metadata |

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

### 11.5.1 Promotion Gates

The progression above should not be symbolic only.

Each transition should have an explicit gate:

| From | To | Minimum gate |
|---|---|---|
| `preview_only` | `experimental` | profile file exists, schema-valid, bounded diff documented, repository-side simulation reviewed |
| `experimental` | `benchmark_candidate` | compared against default on named fixtures or benchmark repos, intended score deltas explained, no hidden arithmetic |
| `benchmark_candidate` | `authoritative_release` | parity or benchmark note completed, rationale updated, changelog entry prepared, steward approval recorded |
| `authoritative_release` | `deprecated` | replacement or retirement note recorded, artifact comparability preserved |

The intent is to prevent one common failure mode:

> a locally useful domain tweak quietly becoming the new official score policy without an explicit release decision

### 11.5.2 What Researchers Can Change Directly

Researchers should be allowed to directly change:

- intent-scale answers
- selected baseline profile for simulation
- branch-local `preview_only` deltas inside documented bounds
- explanatory notes attached to why a preview better matches the domain

Researchers should not directly change, on the authoritative path:

- default release profile semantics
- tier boundaries for the official score
- detector graduation state
- score-bearing penalty activation rules
- release-grade policy status labels

If a domain team wants one of those changes, the correct path is:

1. simulate locally
2. capture the proposed diff
3. compare against default on real repositories
4. propose promotion through the governed profile path

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

## 12. Implemented Milestones and Remaining Roadmap

### 1.6.5: mirror-only profile contract

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

Phase 1 parity target fields:

- `raw_score_before_floor`
- `final_score`
- `formal_tier`
- `classification.score_cap`

### 1.6.6: policy visibility

- added `stem policy list` and `stem policy explain`
- added `--policy <name>` on scan/gate/advisory workflows
- surfaced selected profile metadata in stdout, Markdown, explain text, and PDF headers

### 1.6.7: derive/simulate preview

- added `stem policy derive` for auditable 0–5 intent translation
- added `stem policy simulate <repo>` for baseline-vs-preview outcome comparison
- kept derive/simulate outputs mirror-only so authoritative scoring remains unchanged

### 1.6.8: preview hardening and citation readiness

- kept mirror-only scan scoring unchanged while hardening preview simulation against future profile drift
- aligned `simulate` with profile-aware C1 penalty behavior instead of assuming scanner constants forever
- revalidated `preview_only` profiles after bounded deltas are applied
- strengthened mirror-only wording across CLI and report surfaces so `scan --policy` is not confused with `policy simulate`
- added `CITATION.cff` and `.zenodo.json` so release artifacts are ready for DOI-backed citation once GitHub releases are archived by Zenodo

### Remaining roadmap

- authoritative read-through of policy weights/caps/thresholds
- additional release-grade named profiles beyond `strict_clinical_adjacency`
- explicit read-through for currently declared mirror-only fields such as `stage_3_policy.b2_partial_credit_mode`
- `ca-taxonomy-vN` governance policy so runtime trigger-set changes are versioned as first-class release events
- Phase 2 target release remains intentionally unset until parity fixtures, differential tests, and rollback notes are ready for the first score-authoritative read-through patch
- future score-affecting policy changes require:
  - profile update
  - rationale update
  - changelog entry
  - benchmark note when relevant

This keeps calibration governance ahead of personalization while avoiding a risky “big bang” rewrite.

---

## 13. Non-Goals

This architecture does **not** aim to:

- let users personalize trust scores
- introduce hidden model-based calibration
- turn regulatory mapping into a numerical score multiplier
- make advisory output part of the formal score
- replace benchmark or manual review with profile editing

It only aims to make calibration easier to maintain **without weakening lane boundaries**.

---

## 14. Final Position

STEM BIO-AI now has a real calibration architecture.

The correct mechanism is:

> a versioned calibration profile with explicit promotion rules

not:

> ad hoc runtime tuning knobs

If the system is serious about preserving the distinction between:

- formal score
- diagnostics
- regulatory traceability
- advisory

then calibration must be governed with the same discipline.

The right outcome is not “more adjustable.”

The right outcome is:

**more maintainable, without becoming easier to drift.**

