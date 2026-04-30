# STEM BIO-AI v1.3.1 Reasoning Model Candidates

**Status:** Draft v1
**Date:** 2026-04-30
**Source Reviewed:** `D:\Sanctum\Flamehaven-LOGOS`
**Target:** STEM BIO-AI v1.3.1 reasoning diagnostics after v1.3 evidence-ledger buildup

---

## 1. Review Standard

후보 모델은 다음 조건을 기준으로 검토했다.

- Python stdlib만으로 이식 가능하거나 쉽게 stdlib화 가능해야 한다.
- raw repository text를 임의 해석하지 않고, STEM v1.3 `evidence_ledger`를 입력으로 삼아야 한다.
- AI/LLM 없이 계산 가능해야 한다.
- 점수, confidence, uncertainty, contradiction을 분리해 표현할 수 있어야 한다.
- v1.3의 label honesty 원칙을 깨지 않아야 한다.

결론:

> LOGOS 전체 reasoning engine은 v1.3에 직접 이식하지 않는다. 대신 evidence integrity, confidence envelope, uncertainty penalty, benchmark calibration 모델만 clean-room adaptation으로 가져온다.

---

## 2. High-Value Candidates

### Candidate A: Evidence Budget Model

**Source:** `nexus/integrity/budget.py`, `nexus/integrity/INTEGRITY_SPEC.md`

LOGOS formula:

```text
required_bits = max(0.0, -log2(1 - confidence + 1e-6))
observed_bits = log2(1 + unique_token_count(evidence_text))
deficit = required_bits - observed_bits
flagged = deficit > budget_deficit_max
```

`unique_token_count` must be deterministic:

```python
def unique_token_count(text: str) -> int:
    return len(set(re.findall(r"[A-Za-z0-9]+", text.lower())))
```

No subword tokenization, locale-dependent splitting, or model tokenizer is allowed in v1.3.1.

**STEM adaptation:**

Use this as `evidence_budget` for each scoring claim or detector group.

Example:

```text
claim_confidence = detector_precision_prior * source_weight * cross_surface_bonus
observed_bits = log2(1 + unique_evidence_tokens)
budget_deficit = required_bits(claim_confidence) - observed_bits
```

Recommended use:

- `evidence_ledger` quality field
- `--explain` proof strength
- benchmark false-positive triage
- confidence downscaling when a detector emits high score from thin evidence

Do not use it to claim clinical truth. It only measures whether a detector's confidence is over-supported or under-supported by cited evidence.

Fit for v1.3.1: **High**

Reason:

- Pure stdlib (`math`, tokenization)
- Directly compatible with file/line/snippet evidence
- Answers: "Can you show enough evidence for this score?"

---

### Candidate B: Grounding Overlap / Entailment Heuristic

**Source:** `nexus/integrity/grounding.py`, `nexus/integrity/utils.py`

LOGOS heuristic:

```text
if cites empty -> not_in_context
if claim/evidence token overlap >= threshold -> entailed
if evidence contains explicit negation of claim token -> contradicted
else -> unverifiable
```

**STEM adaptation:**

Use this for claim-to-evidence alignment in report statements.

Example STEM trace step:

```json
{
  "claim": "Stage 4 replication evidence is present",
  "cites": ["S4_DOCKER_001", "S4_CITATION_001"],
  "kind": "stage_summary",
  "confidence": 0.78
}
```

Then grounding check verifies whether cited evidence snippets actually overlap with the claim.

Recommended use:

- evidence-backed report generation
- `--explain` trace validation
- generated Markdown/PDF summary sanity check
- v1.4 AI advisory guardrail

Fit for v1.3.1: **High**

Reason:

- Pure stdlib after copying small tokenizer helpers
- Good match for evidence ledger
- Distinguishes `not_in_context`, `unverifiable`, `contradicted`

Risk:

- Token overlap is not semantic entailment.
- Must label as "grounding heuristic", not proof of truth.

---

### Candidate C: Observed Validity Envelope / Overconfidence Check

**Source:** `bridge/calibration_gate.py`

LOGOS OVE logic:

```text
if semantic_consistency < min_similarity -> fail
if evidence_count == 0 and confidence > max_overconfidence -> fail
if evidence_count > 0:
    expected_conf = min(0.9, 0.4 + 0.1 * evidence_count)
    if confidence - expected_conf > max_overconfidence -> fail
```

**STEM adaptation:**

Use this as `confidence_evidence_envelope`.

STEM does not need semantic embedding similarity in v1.3. Replace `semantic_consistency` with:

```text
surface_consistency = token_overlap(readme_terms, docs/package/test_terms)
```

Recommended use:

- cap confidence when evidence count is low
- identify "strong score from weak evidence"
- benchmark error analysis
- v1.4 AI advisory rejection if AI confidence exceeds deterministic evidence

Fit for v1.3.1: **High**

Reason:

- Simple, explainable, deterministic
- Good answer to "why not overclaim?"
- Directly supports label honesty

---

### Candidate D: Uncertainty Penalty From Component Spread

**Source:** `bridge/drift_controller.py`, `docs/release_notes_1.5.0.md`

LOGOS formula:

```text
component_std = std(component_vector)
uncertainty_penalty = clip((component_std - std_ref) * penalty_gain, 0, max_penalty)
effective_drift = drift + uncertainty_penalty
```

**STEM adaptation:**

Compute uncertainty from spread across stage subscores or detector groups.

Example:

```text
stage_vector = [S1, S2R, S3, S4] normalized to [0,1]
component_std = pstdev(stage_vector)
uncertainty_penalty = clip((component_std - 0.15) * 0.25, 0, 0.08)
```

Interpretation:

- High S1 but low S3/S4 means documentation looks strong but implementation/replication evidence is weak.
- The uncertainty penalty should not replace the final score.
- It should appear as `audit_uncertainty` or `score_stability_risk`.

Recommended use:

- separate `uncertainty` field
- tier confidence labeling
- benchmark analysis
- v1.4 AI entry condition

Fit for v1.3.1: **Medium-High**

Reason:

- Stdlib implementation via `statistics.pstdev`
- Useful for audit confidence
- Must avoid silently changing final score in v1.3.1.

---

### Candidate E: SIDRCE-Style Gate-Closed Score

**Source:** `bridge/omega_scorer.py`, `docs/release_notes_1.5.0.md`

LOGOS formula:

```text
omega = raw_base * max(0, 1 - drift_jsd / jsd_gate)
```

**STEM adaptation:**

Do not import JSD at first. Use a deterministic contradiction or missing-evidence ratio as the gate input.

Example:

```text
evidence_risk = weighted_missing_required_evidence_ratio
gated_score = raw_score * max(0, 1 - evidence_risk / risk_gate)
```

Possible gate inputs:

- direct clinical claim without disclaimer
- contradiction between README claim and tests/docs evidence
- high `manual_review_required` ratio
- Stage 4 replication evidence near zero for high clinical-adjacent repos

Recommended use:

- hard floor/cap explanation
- `risk_gate_factor` output
- not as a new final score until benchmark proves it

Fit for v1.3.1: **Medium**

Reason:

- Formula is clean and explainable.
- Current STEM already has cap logic; this can formalize it.
- Needs benchmark calibration before score integration.

---

### Candidate F: Reasoning Coherence / Cross-Path Agreement

**Source:** `docs/release_notes_1.6.0.md`, `bridge/drift_controller.py`

LOGOS formula:

```text
reasoning_coherence = clip(1 - abs(score_a - score_b), 0.0, 1.0)
```

**STEM adaptation:**

Use agreement between independent evidence lanes.

Examples:

```text
claim_code_coherence = 1 - abs(stage_1_readme_evidence - stage_3_code_bio)
replication_code_coherence = 1 - abs(stage_3_code_bio - stage_4_replication)
manual_alignment = 1 - abs(stem_tier_numeric - manual_tier_numeric) / 4
```

Recommended use:

- report `lane_coherence`
- benchmark alignment summary
- detect README-heavy repos with weak code evidence

Fit for v1.3.1: **High**

Reason:

- Pure stdlib
- Easy to explain
- Strong fit for Stage 2R and benchmark evidence

---

### Candidate G: Calibration / Rank Alignment

**Source:** `bridge/calibration_gate.py`, `nexus/integrity/calibrate.py`

LOGOS calibration checks:

- raw correlation
- linear calibration
- rank alignment
- clean/suspicious threshold calibration from sample traces

**STEM adaptation:**

Use benchmark results to compute:

```text
exact_tier_agreement
adjacent_tier_agreement
mean_absolute_tier_error
rank_agreement
detector_false_positive_rate
detector_false_negative_rate
```

Do not require NumPy. Use stdlib:

- Pearson correlation via `statistics`
- rank correlation with manual rank lists
- MAE via simple arithmetic

Recommended use:

- `audits/benchmark-v1.3/tier_alignment_summary.md`
- detector threshold tuning
- release gate for v1.3.1

Fit for v1.3.1: **High**

Reason:

- Directly supports the benchmark evidence goal.
- Makes "our score is meaningful" measurable.

---

### Candidate H: Entropy Gate

**Source:** `bridge/entropy_gate.py`, `docs/release_notes_1.5.0.md`

LOGOS formula:

```text
p = semantic_curvature / (2*pi*10)
rho = diag(1 - 2p/3, 2p/3)
S = -sum(rho_i * ln(rho_i))
S_target = S_base * omega
breach = S > S_target
```

**STEM adaptation:**

This is mathematically interesting but not a first-choice v1.3.1 model. STEM lacks a justified `semantic_curvature` signal without embeddings or AI. A possible deterministic proxy is contradiction density or lane divergence, but that would make the entropy metaphor less defensible.

Recommendation:

- Do not implement in v1.3.1.
- Revisit in v1.4 if AI/embedding layer produces a real curvature-like signal.

Fit for v1.3.1: **Low-Medium**

Reason:

- Pure stdlib possible.
- But input semantics are not yet justified for STEM.
- Risk of mathematical over-styling without better evidence.

---

## 3. Recommended v1.3.1 Mathematical Model

Use a modest, defensible model:

```text
detector evidence -> evidence budget -> confidence envelope -> lane coherence -> benchmark calibration
```

Do not build a grand unified trust equation in v1.3.1. The purpose is proof-bearing audit, not mathematical branding.

### 3.1 Evidence Confidence

For each detector group:

```text
base_confidence =
    detector_prior
  * source_weight
  * status_weight
  * cross_surface_multiplier

evidence_budget_deficit =
    required_bits(base_confidence) - observed_bits(evidence_text)

confidence_adjusted =
    clamp(base_confidence - budget_penalty(evidence_budget_deficit), 0, 1)
```

Suggested weights:

These weights are uncalibrated initial priors. They are not empirical constants. v1.3.1 must label them as initial estimates, and later patch releases may recalibrate them only after the 30-repository benchmark shows a justified adjustment.

```text
source_weight:
  code/AST/test/CI evidence: 1.00
  package metadata:          0.85
  README/docs:               0.75
  generated report text:     0.50

status_weight:
  detected:                 1.00
  absent:                   0.60
  not_detected:             0.40
  manual_review_required:   0.30
  error:                    0.20
```

### 3.2 Lane Coherence

Normalize stage scores to `[0,1]`.

```text
S1 = README Evidence Signal
S2 = Repo-Local Consistency
S3 = Code/Bio Responsibility
S4 = Reproducibility & Replication Evidence

pairs = [(S1, S3)]
if S4 is not None:
    pairs.append((S3, S4))
overall_lane_coherence = mean(1 - abs(a - b) for a, b in pairs)
```

Report this separately as `lane_coherence`. It should not silently override final score in v1.3.1. If S4 is not available, do not treat S4 as zero; exclude the S3-S4 pair.

### 3.3 Uncertainty Budget

```text
stage_std = pstdev([S1, S2, S3, S4])
manual_ratio = manual_review_required_count / total_detector_count
error_ratio = error_count / total_detector_count

uncertainty =
    0.50 * clip(stage_std / 0.35, 0, 1)
  + 0.35 * manual_ratio
  + 0.15 * error_ratio
```

Interpretation:

```text
uncertainty < 0.20 -> stable
0.20-0.45         -> review advised
> 0.45            -> high uncertainty; manual review required
```

### 3.4 Evidence-Risk Gate

Use only for explanation in v1.3.1.

```text
risk_gate_factor = max(0, 1 - evidence_risk / risk_gate)
```

Where:

```text
evidence_risk =
    0.40 * missing_required_boundary_ratio
  + 0.30 * contradiction_ratio
  + 0.20 * manual_review_required_ratio
  + 0.10 * parse_error_ratio
```

Recommended default:

```text
risk_gate = 0.60
```

These weights are uncalibrated initial priors. Do not use this as the main final score formula until benchmark results justify it.

---

## 4. Implementation Mapping For v1.3.1

Recommended new module for v1.3.1:

```text
stem_ai/reasoning_model.py
```

Suggested functions:

```python
def required_bits(confidence: float) -> float: ...
def unique_token_count(text: str) -> int: ...
def observed_bits(text: str) -> float: ...
def evidence_budget(confidence: float, evidence_text: str) -> dict: ...
def confidence_envelope(confidence: float, evidence_count: int) -> dict: ...
def lane_coherence(stage_scores: dict) -> dict: ...
def uncertainty_budget(stage_scores: dict, detector_counts: dict) -> dict: ...
def evidence_risk_gate(risk_components: dict, risk_gate: float = 0.60) -> dict: ...
def benchmark_alignment(stem_tiers: list[int], manual_tiers: list[int]) -> dict: ...
```

Expected JSON fields:

```json
{
  "reasoning_model": {
    "version": "stem-bio-ai-reasoning-v1.3.1",
    "evidence_budget": {},
    "confidence_envelope": {},
    "lane_coherence": {},
    "uncertainty_budget": {},
    "evidence_risk_gate": {}
  }
}
```

---

## 5. What Not To Import

Do not import these LOGOS elements into v1.3.1:

- LLM reasoning adapters
- Z3 symbolic verification path
- NumPy/SciPy drift controller implementation
- Von Neumann entropy gate as a primary audit gate
- Procrustes/CKA/SLERP representation geometry
- HRPO/AATS/IRF engine abstractions

Reason:

- They either require non-stdlib dependencies, embeddings, AI outputs, or a reasoning trace substrate STEM v1.3 does not yet have.
- Importing them would violate the v1.3 goal of deterministic local repository evidence.

---

## 6. v1.3.1 Plan Changes Recommended

When planning v1.3.1, add:

1. Add `stem_ai/reasoning_model.py` as a required v1.3.1 module.
2. Add evidence budget and lane coherence as first-class v1.3.1 outputs.
3. Add uncertainty budget release gate for v1.3.1.
4. Add benchmark calibration metrics based on v1.3 benchmark artifacts.
5. Keep entropy/geometry models deferred to v1.4+ unless a deterministic proxy is justified.

---

## 7. Bottom Line

The most useful LOGOS transplant is not a large reasoning engine. It is a small set of evidence integrity equations:

```text
evidence budget
+ confidence envelope
+ lane coherence
+ uncertainty budget
+ benchmark calibration
```

This is exactly the layer STEM BIO-AI should add in v1.3.1 before AI enters in v1.4.
