# STEM BIO-AI Public API Contract

Version: 1.5.6
Status: **Stable**
Supersedes: `docs/API_CONTRACT_V1_5_DRAFT.md`

---

## Compatibility Policy

STEM BIO-AI follows an additive-only compatibility guarantee for all items marked **Locked**:

- **Locked**: Field names, types, and semantics will not change without a major version bump.
- **Additive**: New fields may appear in future minor versions. Consumers must ignore unknown fields.
- **Internal**: Unlisted fields are not part of the public contract and may change at any time.

A major version bump (e.g., 1.x → 2.0) is required to:
- Rename or remove any Locked field
- Change the scoring formula, tier boundaries, or weight distribution
- Change `schema_version`

Minor version bumps (e.g., 1.5.x → 1.5.y) may:
- Add new Locked fields (additive)
- Add new items to `evidence_ledger`, `stage_1_rubric`, or `stage_3_rubric`
- Add new detectors or rubric items without changing existing item keys

---

## CLI Entry Point (Locked)

```
python -m stem_ai <repo>               # brief 1-page, all formats
stem audit <repo> [OPTIONS]            # explicit subcommand

Options:
  --level 1|2|3                        # report depth
  --format json|md|pdf|all             # output format
  --out DIR                            # output directory
  --explain                            # write {stem}_explain.txt
  --advisory none|validate|packet      # advisory mode
  --advisory-response FILE             # validate provider response
  --version                            # print version and exit
```

The `stem audit <repo>` invocation is stable. Output format choices and the
`--explain` flag are stable. Advisory flags are stable at the protocol level;
individual provider integrations are additive.

---

## JSON Result: Top-Level Fields

All fields below are present in every `audit_repository()` result.

### Identity and Metadata (Locked)

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | `"stem-ai-local-cli-result-v1.4"` — bumped on breaking change |
| `stem_ai_version` | string | Package version (e.g. `"1.5.6"`) |
| `generated_at_local` | string | ISO 8601 date of scan |
| `execution_mode` | string | Always `"LOCAL_ANALYSIS"` for the CLI |
| `method` | string | Human-readable method description |

### Target (Locked)

| Field | Type | Description |
|-------|------|-------------|
| `target.name` | string | `owner/repo` from git remote, or directory name |
| `target.local_path` | string | Absolute local path scanned |
| `target.remote` | string\|null | `git remote get-url origin` output |
| `target.branch` | string\|null | Current branch |
| `target.commit` | string\|null | HEAD commit SHA |
| `target.file_count` | integer | Total files found (excluding skip dirs) |

### Classification (Locked)

| Field | Type | Description |
|-------|------|-------------|
| `classification.clinical_adjacent` | boolean | True if any CA term detected |
| `classification.ca_severity` | string | `"CA-DIRECT"` / `"CA-INDIRECT"` / `"none"` |
| `classification.t0_hard_floor` | boolean | True if T0 hard floor triggered |
| `classification.score_cap` | integer\|null | Score ceiling applied (39 or 69), or null |
| `classification.has_explicit_clinical_boundary` | boolean | Disclaimer detected |

### Score (Locked)

| Field | Type | Description |
|-------|------|-------------|
| `score.stage_1_readme_intent` | integer | Stage 1 score (0–100) |
| `score.stage_2_cross_platform` | string | `"not_applicable_in_LOCAL_ANALYSIS"` |
| `score.stage_2_repo_local_consistency` | integer | Stage 2R score (0–100) |
| `score.stage_2_lane` | string | `"STAGE_2R_REPO_LOCAL_CONSISTENCY"` |
| `score.stage_3_code_bio` | integer | Stage 3 score (0–100) |
| `score.weights` | object | `{"stage_1": 0.4, "stage_2": 0.2, "stage_3": 0.4}` |
| `score.risk_penalty` | integer | C1 credential penalty (0 or 10) |
| `score.raw_score_before_floor` | integer | Score before cap applied |
| `score.final_score` | integer | Final clamped score (0–100) |
| `score.formal_tier` | string | `"T0 Rejected"` / `"T1 Quarantine"` / `"T2 Caution"` / `"T3 Supervised"` / `"T4 Candidate"` |
| `score.use_scope` | string | Human-readable scope description for the tier |

### Rubrics (Additive — new items may appear)

| Field | Type | Description |
|-------|------|-------------|
| `stage_1_rubric` | object | Per-item Stage 1 scores (baseline, S1_domain_*, H*, R*) |
| `stage_2r_rubric` | object | Per-item Stage 2R scores (R2R_*, R2R_D*) |
| `stage_3_rubric` | object | Per-item Stage 3 scores (T1, T2, T3, B1, B2, B3, raw_total) |
| `stage_4_rubric` | object | Stage 4 replication rubric (S4_*, raw_total) |

Rubric item keys within each object are stable once published. New keys may be added.
The `score`, `max`, and `evidence` sub-fields are stable for all existing keys.

### Replication Lane (Locked)

| Field | Type | Description |
|-------|------|-------------|
| `replication_score` | integer | Stage 4 raw score (0–100) |
| `replication_tier` | string | `"R0"` / `"R1"` / `"R2"` / `"R3"` / `"R4"` |

Stage 4 does not affect `score.final_score` or `score.formal_tier`.

### Code Integrity (Locked)

| Field | Type | Description |
|-------|------|-------------|
| `code_integrity.C1_hardcoded_credentials` | object | `{status: "PASS"/"FAIL", evidence: [...]}` |
| `code_integrity.C2_dependency_pinning` | object | `{status: "PASS"/"WARN", evidence: [...]}` |
| `code_integrity.C3_dead_or_deprecated_patient_adjacent_paths` | object | `{status: "PASS"/"WARN", evidence: [...]}` |
| `code_integrity.C4_exception_handling_clinical_adjacent_paths` | object | `{status: "PASS"/"WARN", evidence: [...]}` |

### Evidence and Diagnostics (Locked structure, Additive content)

| Field | Type | Description |
|-------|------|-------------|
| `evidence_ledger` | array | List of `EvidenceFinding` records (see below) |
| `detector_summary` | object | `{total_findings, by_status, by_detector}` |
| `ast_signal_summary` | object | AST analysis counts and coverage ratios |
| `reasoning_model` | object | Diagnostic layer (observation-only, does not affect score) |
| `measurement_basis` | object | Per-stage description of detection method |
| `notable_positive_evidence` | array | Human-readable positive signals |
| `notable_risks` | array | Human-readable risk signals |
| `file_hashes_sha256` | object | SHA-256 hashes of key files (README, manifests) |

### EvidenceFinding Record (Locked)

Each item in `evidence_ledger` has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `finding_id` | string | `"detector:pattern_id:occurrence"` — no backslashes |
| `detector` | string | Detector name (e.g., `"S1_readme_bio_terms"`) |
| `pattern_id` | string | Pattern version identifier |
| `status` | string | `"detected"` / `"not_detected"` / `"absent"` / `"not_applicable"` / `"error"` |
| `severity` | string | `"info"` / `"warn"` |
| `file` | string | Relative path from repo root, or `"."` for repo-level |
| `line` | integer | Line number (0 if not applicable) |
| `snippet` | string | Source line text |
| `match_type` | string | `"regex"` / `"ast"` / `"file_presence"` / `"dependency"` / `"aggregate"` / `"limit"` / `"metadata"` |
| `explanation` | string | Human-readable explanation |
| `metadata` | object\|null | Optional additional evidence detail |

---

## Advisory Protocol (Locked — Non-Negotiable)

These rules govern all advisory packet exports and provider response validations.
They cannot be relaxed by configuration or provider agreement.

1. AI/provider output **cannot** override `score.final_score` or `score.formal_tier`.
2. Every material advisory item **must** cite exact `finding_id` strings from `allowed_finding_ids`.
3. Providers **must** copy citation strings verbatim; the validator does not repair citations.
4. Raw repository source text is **not** included in provider packets.
5. Provider responses containing clinical safety, efficacy, regulatory, deployment, or
   medical-advice claims are **rejected** by the validator.
6. `allowed_finding_ids` is capped at 40 entries per packet.

### Advisory CLI Flags (Locked)

| Flag | Behavior |
|------|----------|
| `--advisory none` | Default. No advisory output. |
| `--advisory validate` | Offline contract validation without API call. |
| `--advisory packet` | Export provider-neutral advisory input packet. |
| `--advisory-response FILE` | Validate a provider-produced JSON response. |

---

## Python API (Stable for Local Automation)

These functions are stable at the signature level. Return value fields may receive
additive extensions in minor versions.

```python
from stem_ai.scanner import audit_repository
result = audit_repository(target: Path, advisory: str = "none", advisory_response_path: Path | None = None) -> dict

from stem_ai.advisory_contract import build_provider_advisory_input, validate_advisory_output
from stem_ai.advisory_response import validate_advisory_response_file
from stem_ai.provider_benchmark import packet_stats_record, response_validation_record, packet_summary
```

---

## Tier Definitions (Locked)

| Tier | Score Range | Use Scope |
|------|------------|-----------|
| T0 Rejected | 0–39 | Do not rely on without independent expert validation |
| T1 Quarantine | 40–54 | Exploratory review only; no patient-adjacent use |
| T2 Caution | 55–69 | Research reference and supervised non-clinical technical review only |
| T3 Supervised | 70–84 | Supervised institutional review candidate |
| T4 Candidate | 85–100 | Strong evidence posture; clinical deployment still requires independent validation |

Tier boundaries are conventional thresholds anchored to the scoring baseline.
See `docs/SCORING_RATIONALE.md` for the derivation and calibration gap disclosures.

---

## What This Contract Does Not Cover

- **Clinical validation**: A tier is an evidence classification, not a clinical safety rating.
- **Regulatory compliance**: STEM BIO-AI output is not a regulatory submission or audit.
- **Runtime behavior**: The contract covers the local CLI scan output; it does not cover
  the runtime behavior of the scanned repository.
- **LLM-mode audits**: The full spec (LLM-native runtime with Stage 2 cross-platform
  verification) operates under a separate execution contract not covered here.
