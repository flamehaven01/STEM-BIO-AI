# Regulatory Registry Entries

This directory holds YAML metadata files for each regulatory document in `references/`.
Each YAML file is the authoritative source for its corresponding entry in
`docs/regulatory_basis_registry.v1.json`.

## Workflow

1. User converts regulatory PDF to MD → places in `references/`
2. User creates or updates the matching YAML file in this directory
3. Run: `python tools/update_regulatory_registry.py`
4. Verify `docs/regulatory_basis_registry.v1.json` is updated correctly
5. If new requirement_ids are needed, update `stem_ai/regulatory_traceability.py`
6. Version bump (patch) + commit + push

## YAML Schema

```yaml
id: <unique_source_id>           # e.g. ich_m15_midd_2026
jurisdiction: ICH | EU | US | IMDRF | FDA
title: "Full official title"
short_label: "Short display name"
status: final_guideline | final_framework | law_in_force | draft_guidance
published_date: "YYYY-MM-DD"     # ICH Step 4 or official publication date
effective_date: "YYYY-MM-DD"     # null if not applicable
source_file: "filename.md"       # MD file in references/
source_url: "https://..."
display_label: "Text shown in UI badges"

used_for:                        # Maps to registry used_for field
  - key_use_case_1

sections:                        # Key section refs for traceability
  "X.Y": "Section title and purpose"

notes: >                         # Any governance or alignment caveats
  Free text note.
```

## Active Entries

| ID | Document | Status | MD file |
|---|---|---|---|
| `eu_ai_act_2024_1689` | EU AI Act (Regulation (EU) 2024/1689) | law_in_force | — |
| `fda_qmsr` | FDA QMSR | final_guidance | — |
| `fda_mlmd_transparency_2024` | FDA ML-MD Transparency | final_guidance | — |
| `fda_pccp_2025` | FDA PCCP | final_guidance | — |
| `imdrf_samd_clinical_eval_2017` | IMDRF SaMD Clinical Eval | final_framework | — |
| `imdrf_gmlp_2025` | IMDRF GMLP | final_framework | — |
| `ich_m15_midd_2026` | ICH M15 MIDD (Step 4, Jan 2026) | final_guideline | `M15 General Principles...md` |

> `eu_ai_act_timeline_ec` is a supplementary reference URL — no YAML entry, excluded from display_note by design.

## Planned Entries

When new documents are received as MD files, add YAML entries here and set `source_file`:
- `airi_v5_xx` — when MIT AIRI updates
- `eu_ai_act_implementing_acts` — EU AI Act implementing measures
- `imdrf_gmlp_update` — IMDRF GMLP revisions
