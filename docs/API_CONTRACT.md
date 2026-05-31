# STEM BIO-AI Public API Contract

Version: 1.7.9
Status: **Stable**
Supersedes: historical v1.5 draft contract

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

```bash
stem <repo>                            # shortcut for `stem scan <repo>`
stem scan <repo> [OPTIONS]             # primary scan workflow
stem gate <repo> --min-tier T2         # CI/CD gate workflow
stem advisory validate <repo>          # offline advisory validation
stem advisory packet <repo>            # provider-neutral packet export
stem advisory call <repo>              # explicit provider-call boundary
stem advisory check-response <repo> --response FILE
stem policy list                       # list named calibration profiles
stem policy explain <name>             # inspect one calibration profile

# Compatibility entry points
python -m stem_ai <repo>
python -m stem_ai.cli <repo>
stem audit <repo> [OPTIONS]
```

Shared stable options:

```text
--level 1|2|3
--format json|md|pdf|all
--out DIR / --output DIR
--explain
--summary full|compact|off
--version
```

The workflow-oriented commands are stable. `stem <repo>` and `stem audit <repo>`
remain backward-compatible entry points. Advisory packet/response semantics are
stable at the protocol level; individual provider integrations are additive.

---

## JSON Result: Top-Level Fields

All fields below are present in every `audit_repository()` result.

### Identity and Metadata (Locked)

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | `"stem-ai-local-cli-result-v1.6"` — bumped on breaking change |
| `stem_ai_version` | string | Package version (e.g. `"1.7.9"`) |
| `generated_at_local` | string | ISO 8601 date of scan |
| `execution_mode` | string | Always `"LOCAL_ANALYSIS"` for the CLI |
| `method` | string | Human-readable method description |

### Audit Freshness (Additive)

| Field | Type | Description |
|-------|------|-------------|
| `audit_freshness.review_after_days` | integer | Suggested review window before the audit should be treated as stale |
| `audit_freshness.freshness_basis` | string | Rule used to choose the review window, e.g. `clinical_adjacent_short_cycle` |
| `audit_freshness.expires_on` | string | ISO 8601 date after which the audit should be reviewed again |
| `audit_freshness.expired` | boolean | Whether the audit is past its review window on generation date |
| `audit_freshness.anchored_commit` | string\|null | Commit SHA used as the current audit anchor |
| `audit_freshness.hashes_available_for` | array | Key files with surfaced SHA-256 hashes |
| `audit_freshness.change_triggered_reaudit_supported` | boolean | Whether commit/hash anchors exist for change-triggered re-audit checks |
| `audit_freshness.change_triggered_reaudit_recommended_now` | boolean | True when missing anchors make immediate re-audit caution appropriate |
| `audit_freshness.change_triggered_reaudit_reasons` | array | Machine-readable reasons such as `git_commit_unavailable` |
| `audit_freshness.change_triggers` | array | Canonical trigger classes that should force a re-audit on change |

### Calibration Profile (Implemented Mirror-Only Surface)

| Field | Type | Description |
|-------|------|-------------|
| `calibration_profile.policy_schema_version` | string | Calibration profile schema version (currently `"1"`) |
| `calibration_profile.policy_version` | string | Versioned policy identifier independent from package version |
| `calibration_profile.tool_version_introduced` | string | First tool version that introduced this policy shape |
| `calibration_profile.tool_version_last_validated` | string | Last tool version whose runtime constants were checked against this profile |
| `calibration_profile.profile_name` | string | Active profile label selected by CLI `--policy` |
| `calibration_profile.profile_status` | string | Profile lifecycle status (`authoritative_release`, `experimental`, etc.) |
| `calibration_profile.profile_read_mode` | string | `"mirror_only"` in `1.7.9`; later `"authoritative"` when scan scoring reads policy values directly |
| `calibration_profile.policy_sha256` | string | Canonical SHA256 surfaced by the runtime artifact; profile files may carry `null` before authoritative read-through |

In `1.7.9`, `scan --policy <name>` still keeps authoritative scan scoring on the deterministic runtime-constant path. Policy selection changes surfaced metadata only; governed score-delta preview belongs to `stem policy simulate`.

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
| `classification.ca_taxonomy_version` | string | Active CA taxonomy version label (e.g. `"ca-taxonomy-v1"`) |
| `classification.ca_taxonomy_source` | string | Runtime authority for CA trigger logic |
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
Published rubric items may also carry additive `detector_id` and `decision_basis`
sub-fields to surface the detector trace and human-readable decision rationale.

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
| `code_integrity.C5_compliance_boundary_integrity` | object | `{status: "PASS"/"WARN", evidence: [...]}` |
| `code_integrity.C6_mock_auth_or_fail_open_boundary` | object | `{status: "PASS"/"WARN", evidence: [...]}` |

### Code Contract (Locked)

`code_contract` is the Layer 2 AST contract-detector summary. It is additive at
the detector-family level, but the published `CC1`/`CC2`/`CC3` keys below are
stable once released.

| Field | Type | Description |
|-------|------|-------------|
| `code_contract.CC1_clinical_zero_default` | object | `{count: integer, status: "PASS"/"WARN"}` — public confidence / threshold parameters defaulted to `0.0` |
| `code_contract.CC2_api_contract` | object | `{count: integer, status: "PASS"/"WARN"}` — README-declared names cross-checked against package `__all__` exports |
| `code_contract.CC3_shallow_validator` | object | `{count: integer, status: "PASS"/"WARN"}` — `validate_*` / `check_*` functions using only `len()` without regex structure checks |

### Evidence and Diagnostics (Locked structure, Additive content)

| Field | Type | Description |
|-------|------|-------------|
| `evidence_ledger` | array | List of `EvidenceFinding` records (see below) |
| `detector_summary` | object | `{total_findings, by_status, by_detector}` |
| `ast_signal_summary` | object | AST analysis counts and coverage ratios |
| `reasoning_model` | object | Diagnostic layer (observation-only, does not affect score) |
| `regulatory_basis` | object | Registry-driven regulatory basis note metadata and source IDs |
| `stage_traceability` | object | Per-stage traceability notes keyed by `stage_1`, `stage_2r`, `stage_3`, `stage_4`, `bio_diagnostics` |
| `regulatory_traceability` | object | Flattened traceability summary layer with additive `items` list |
| `measurement_basis` | object | Per-stage description of detection method |
| `airi_risk_coverage` | object | AIRI registry/bundle/mapping provenance plus covered-risk and known-gap summaries |
| `notable_positive_evidence` | array | Human-readable positive signals |
| `notable_risks` | array | Human-readable risk signals |
| `file_hashes_sha256` | object | SHA-256 hashes of key files (README, manifests) |

### AIRI Risk Trigger Layer (Additive)

| Field | Type | Description |
|-------|------|-------------|
| `airi_risk_coverage.airi_version` | string | Upstream AIRI version label surfaced from the local registry snapshot |
| `airi_risk_coverage.airi_source` | string | Human-readable upstream source / license string |
| `airi_risk_coverage.airi_registry_version` | string | Local full-registry version |
| `airi_risk_coverage.airi_bundle_version` | string | Local runtime-bundle version |
| `airi_risk_coverage.airi_mapping_version` | string | Local detector-mapping registry version |
| `airi_risk_coverage.airi_bundle_scope` | string | Runtime bundle scope label |
| `airi_risk_coverage.airi_upstream_snapshot_date` | string | Snapshot date for the local upstream import |
| `airi_risk_coverage.airi_upstream_license` | string | Upstream license label |
| `airi_risk_coverage.airi_attribution_note` | string | Artifact-level attribution statement |
| `airi_risk_coverage.total_risks_in_registry` | integer | Count of risk rows in the full local registry |
| `airi_risk_coverage.total_risks_in_bundle` | integer | Count of risk rows in the curated runtime bundle |
| `airi_risk_coverage.total_risks_in_detector_scope` | integer | Count of risk IDs referenced by the active detector mapping |
| `airi_risk_coverage.detectors_triggered` | array | Triggered detector IDs used for this coverage result |
| `airi_risk_coverage.covered_risks` | array | Covered AIRI risks with detector references |
| `airi_risk_coverage.covered_risks[*].mapping_details` | array | Additive reasoning objects `{detector_id, mapping_justification, trigger_reason}` for each matched detector-to-risk link |
| `airi_risk_coverage.covered_count` | integer | Count of covered risks |
| `airi_risk_coverage.coverage_rate` | number | Covered risks / total risks in detector scope |
| `airi_risk_coverage.known_gaps` | array | Combined known-gap list from the local mapping registry |
| `airi_risk_coverage.known_gaps_in_bundle` | array | Known gaps that are inside the current runtime bundle |
| `airi_risk_coverage.known_gaps_outside_bundle` | array | Known gaps tracked against the full registry but not included in the runtime bundle |

### Regulatory Traceability Layer (Additive)

| Field | Type | Description |
|-------|------|-------------|
| `regulatory_basis.registry_version` | string | Registry identifier, currently `"stem-ai-regulatory-basis-registry-v1"` |
| `regulatory_basis.as_of` | string | Human-readable freshness label used in report note |
| `regulatory_basis.review_required` | boolean | True when the basis registry should be reviewed for staleness or draft-only dependencies |
| `regulatory_basis.review_reasons` | array | Machine-readable reason codes such as `registry_as_of_stale` or `required_source_missing` |
| `regulatory_basis.source_ids` | array | Source IDs loaded from the registry |
| `regulatory_basis.note` | object | Small report note `{title, body_line_1, body_line_2}` |
| `stage_traceability.*` | array | Per-stage traceability note records; each record is additive |
| `regulatory_traceability.version` | string | Currently `"stem-ai-reg-trace-v1.6"` |
| `regulatory_traceability.summary` | string | Human-readable synthesis paragraph |
| `regulatory_traceability.items` | array | Flattened traceability note records across stages |

Each traceability note record contains:

| Field | Type | Description |
|-------|------|-------------|
| `stage` | string | `stage_1`, `stage_2r`, `stage_3`, `stage_4`, or `bio_diagnostics` |
| `requirement_id` | string | Requirement family key such as `EU_AI_ACT_ARTICLE_12` |
| `mapping_confidence` | string | `strong`, `moderate`, `weak_moderate`, `weak`, or `not_assessed` |
| `evidence_strength` | string | Strength of observed repository evidence |
| `status` | string | `aligned`, `partially_aligned`, `signal_only`, `not_detected`, or `not_assessed` |
| `not_assessed` | array | Explicit out-of-scope or unavailable factors |
| `finding_refs` | array | Finding IDs or stable rubric/evidence references |
| `source_ids` | array | Source IDs from the regulatory basis registry |
| `note` | string | Human-readable bounded interpretation |

### EvidenceFinding Record (Locked)

Each item in `evidence_ledger` has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `finding_id` | string | `"detector:path:line:occurrence"` using POSIX-style `/` separators — no backslashes |
| `detector` | string | Detector name (e.g., `"S1_readme_bio_terms"`) |
| `pattern_id` | string | Pattern version identifier |
| `status` | string | `"detected"` / `"not_detected"` / `"absent"` / `"not_applicable"` / `"manual_review_required"` / `"error"` |
| `evidence_status` | string | Additive evidence-state label such as `confirmed_present`, `confirmed_missing`, or `not_found_in_reviewed_sources` |
| `confidence` | string | Additive confidence label: `high`, `medium`, or `low` |
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

### Advisory CLI Workflows (Locked)

| Command / Flag | Behavior |
|----------------|----------|
| `stem advisory validate <repo>` | Offline contract validation without API call. |
| `stem advisory packet <repo>` | Export provider-neutral advisory input packet. |
| `stem advisory call <repo>` | Enter explicit provider-call mode. The network boundary is opt-in and reported separately from deterministic scanning. |
| `stem advisory check-response <repo> --response FILE` | Validate a provider-produced JSON response. |
| `stem scan <repo> --advisory ...` | Legacy inline compatibility path. |
| `stem scan <repo> --advisory-response FILE` | Legacy provider-response compatibility path. |

### Advisory Packet Fields (Additive)

Provider packet exports from `stem advisory packet` now include the following additive fields:

| Field | Type | Description |
|-------|------|-------------|
| `provider_request` | object | Secret-free provider handoff metadata, request schema, and argument-validation status |
| `provider_request.request_schema_version` | string | `"stem-ai-provider-request-v1.4"` |
| `provider_request.request_schema` | object | Exported provider request shape for downstream validators |
| `provider_request.args_validation` | object | `{status, error_count}` summary for normalized provider request arguments |
| `provider_request.base_url_validation` | object | Deterministic endpoint-policy result for the selected provider/base URL pair |
| `provider_request.secret_policy` | object | Exported secret-handling policy summary for downstream runners |
| `provider_request.env_contract` | object | Allowed provider-specific and shared environment variable names |
| `provider_request.api_key_env_var` | string\|null | Secret-free name of the env var expected by the selected provider |
| `provider_request.secret_source` | string\|null | `"provider_env"` / `"generic_env"` / `"missing"` / `"not_required"` |
| `provider_request.network_mode` | string\|null | `"offline"` / `"remote_https"` / `"local_server"` / `"in_process"` |
| `ai_advisory.provider_call` | object | Explicit provider-call runtime envelope: network intent, logging policy, child-env allowlist summary, and redaction policy |
| `contract_schemas` | object | Advisory input/output contract schema export bundle |
| `contract_schemas.schema_version` | string | `"stem-ai-advisory-contracts-v1.4"` |
| `packet_contract` | object | Deterministic packet self-check result |
| `packet_contract.status` | string | `"valid"` / `"invalid"` |
| `packet_contract.errors` | array | Contract-level packet errors such as allowlist mismatch or raw snippet leakage |

### Advisory Secret Boundary (Locked Policy, Additive Fields)

- Provider API keys must come from environment variables or an external secret store.
- Provider API keys must never appear in CLI arguments, Markdown reports, JSON audit artifacts, or PDFs.
- `provider_request` is secret-free by construction; it reports `api_key_present` and `api_key_env_var`, never the secret value.
- Cloud providers require `https` endpoints; plain `http` is limited to `localhost`, `127.0.0.1`, or `::1`.
- Base URLs containing embedded credentials are rejected by argument validation.
- Explicit `stem advisory call` is the only runtime path allowed to cross into provider-call intent. Packet export and response validation remain separate trust boundaries.

---

## Python API (Stable for Local Automation)

These functions are stable at the signature level. Return value fields may receive
additive extensions in minor versions.

```python
from stem_ai.scanner import audit_repository
result = audit_repository(target: Path, advisory: str = "none", advisory_response_path: Path | None = None) -> dict

from stem_ai.advisory_contract import (
    advisory_contract_schemas,
    build_provider_advisory_input,
    validate_advisory_input_packet,
    validate_advisory_output,
)
from stem_ai.advisory_providers import provider_request_schema, validate_provider_request_args
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







