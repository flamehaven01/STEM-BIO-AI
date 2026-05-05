# STEM BIO-AI v1.5 Public API Contract Draft

**Superseded by `docs/API_CONTRACT.md` (stable, v1.5.7). This file is retained for historical reference only.**

Status: superseded.

v1.5 keeps the scanner core deterministic. Public integrations should treat the following surfaces as draft contracts until a later stable declaration.

## Stable Enough For Local Automation

- CLI audit entry point: `python -m stem_ai <repo>`
- JSON result top-level fields:
  - `schema_version`
  - `stem_ai_version`
  - `target`
  - `classification`
  - `score`
  - `replication_score`
  - `replication_tier`
  - `stage_4_rubric`
  - `code_integrity`
  - `evidence_ledger`
  - `detector_summary`
  - `ast_signal_summary`
  - `reasoning_model`
- Advisory packet export: `--advisory packet`
- Provider response validation: `--advisory-response FILE`

## Draft Python Functions

These functions are usable for local automation but may still receive additive fields:

- `stem_ai.scanner.audit_repository`
- `stem_ai.advisory_contract.build_provider_advisory_input`
- `stem_ai.advisory_contract.validate_advisory_output`
- `stem_ai.advisory_response.validate_advisory_response_file`
- `stem_ai.provider_benchmark.packet_stats_record`
- `stem_ai.provider_benchmark.response_validation_record`

## Non-Negotiable Advisory Rules

- AI/provider output cannot override STEM scores or tiers.
- Every material advisory item must cite exact `finding_id` strings.
- Providers should copy citations from `allowed_finding_ids`.
- The validator does not repair citations.
- Raw repository text is not included in provider packets by default.
- Clinical safety, efficacy, regulatory, deployment, or medical-advice claims are invalid.

## v1.5 Boundary

This draft does not declare a stable external SDK. It documents the current local contract so benchmark and provider experiments can proceed without tying the project to one model vendor.
