# AIRI Data Governance

Version: 1.8.0
Status: Active governance note for the local AIRI data layer

---

## Purpose

STEM BIO-AI uses the MIT AI Risk Repository (AIRI) as an external source of risk identifiers and taxonomy labels.

To keep runtime behavior deterministic while still preserving provenance, the project separates AIRI into three local layers:

1. `stem_ai/data/airi_registry_full.v1.json`
   - normalized full local registry derived from the upstream AIRI CSV snapshot
2. `stem_ai/data/airi_runtime_bundle.v1.json`
   - curated runtime subset used by deterministic local scans
3. `stem_ai/data/airi_detector_mapping.v1.json`
   - local detector-to-risk mapping registry plus known-gap records

The scanner must use the curated runtime bundle, not the entire AIRI universe, for deterministic scan outputs.

---

## Upstream Provenance

- Upstream source: <https://airisk.mit.edu/>
- Upstream artifact: `The AI Risk Repository V4_03`
- Upstream license: `MIT`
- Local snapshot date: `2026-04-23`

The project must continue to attribute AIRI in:

- README
- docs
- runtime result metadata
- local registry metadata

MIT licensing does not remove the provenance requirement for downstream transparency.

---

## Versioning Rules

### Registry version

Bump `airi_registry_full.vN.json` when the normalized local representation changes structurally or the upstream snapshot changes.

### Runtime bundle version

Bump `airi_runtime_bundle.vN.json` when:

- bundle membership changes
- bundle scope changes
- bundle-level provenance wording changes in a way that affects scan outputs

### Mapping version

Bump `airi_detector_mapping.vN.json` when:

- a detector gains or loses a mapped AIRI risk
- a mapping confidence / review status / justification materially changes
- a known gap changes scope (`in_runtime_bundle` vs `outside_runtime_bundle_reference`)

---

## Gap Scope Rules

Known gaps must explicitly declare one of two scopes:

- `in_runtime_bundle`
  - the AIRI risk exists in the current runtime bundle but is not covered by any detector
- `outside_runtime_bundle_reference`
  - the AIRI risk exists in the full upstream registry and is relevant to planning, but is not part of the current runtime bundle

This prevents the bundled 184-risk subset from being confused with the full upstream AIRI universe.

---

## Public Schema Location

The AIRI governance schemas remain in `docs/`:

- `docs/airi_registry.schema.json`
- `docs/airi_detector_mapping.schema.json`

They are kept here intentionally because they are public governance / contract
reference files, not hidden implementation details. The runtime scanner reads
the normalized JSON registries under `stem_ai/data/`; the `docs/` schemas
describe and validate those public data shapes for reviewers, contributors, and
downstream integrators.

Do not delete or relocate these schema files unless every packaging, manifest,
and documentation reference is updated with them.

---

## Runtime Contract

`airi_risk_coverage` in scan results must surface:

- `airi_registry_version`
- `airi_bundle_version`
- `airi_mapping_version`
- `airi_bundle_scope`
- `airi_upstream_snapshot_date`
- `airi_upstream_license`
- `known_gaps_in_bundle`
- `known_gaps_outside_bundle`

Covered AIRI entries may also carry additive `mapping_details` objects. These are
bounded local reasoning records with:

- `detector_id`
- `mapping_justification`
- `trigger_reason`

This is a detector-to-risk explanation layer, not an upstream AIRI verdict.
If a report-layer or regulatory-layer warning has no AIRI mapping row, it must
remain outside AIRI coverage counts rather than being implied into coverage.

This keeps AIRI usage auditable from the artifact itself.







