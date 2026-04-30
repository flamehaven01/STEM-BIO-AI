# STEM AI v1.1.2 ASDP Compile Notes

Status: experimental v1.4.0 planning artifact.

Source:

- `spec/STEM-AI_v1.1.2_CORE.md`
- `D:\Sanctum\flamehaven-ag-core\FAC_DESIGN_v2.md`
- `D:\Sanctum\flamehaven-ag-core\fac\governance\evidence_contract.py`

## Compile Target

The v1.1.2 semantic skill is not imported as runtime logic. For v1.4.0, it is treated as a legacy semantic source that can be compiled into machine-facing contracts:

- advisory input contract
- advisory output contract
- citation rules
- prohibited claim rules
- result contract boundaries

## Extracted Invariants

- AI advisory must cite evidence by `finding_id`.
- AI advisory must not override deterministic scores or tiers.
- AI advisory must not claim clinical safety, regulatory approval, or deployment readiness.
- Raw repository text is not the default AI input.
- Evidence ledger and reasoning diagnostics are the source of record.
- Provider adapters are execution details, not scoring authorities.

## ASDP/FAC Mapping

| ASDP/FAC Concept | STEM BIO-AI v1.4 Mapping |
|---|---|
| ResultContract | `ai_advisory` top-level contract |
| EvidenceContract | advisory input hash + finding count + citation validation |
| Reasoning Plane | optional provider adapter output |
| Governance Plane | deterministic contract validator |
| Memory Plane | committed benchmark and audit artifacts |
| Execution Plane | future provider adapters; not required in v1.4.0 |

## v1.4.0 Boundary

This compile track is non-blocking and stdlib-only inside STEM BIO-AI.

Do not add a runtime dependency on ASDP, FAC, Filesearch, Unsloth, or any model provider in v1.4.0 core.
