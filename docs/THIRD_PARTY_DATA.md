# Third-Party Data and Taxonomy Sources

## MIT AI Risk Repository (AIRI)

STEM BIO-AI uses local derived data from the MIT AI Risk Repository as a taxonomy and detector-mapping reference.

- Source: <https://airisk.mit.edu/>
- Upstream artifact: `The AI Risk Repository V4_03`
- Upstream license: `MIT`
- Local snapshot date used by the current registry: `2026-04-23`

Local derived files:

- `stem_ai/data/airi_registry_full.v1.json`
- `stem_ai/data/airi_runtime_bundle.v1.json`
- `stem_ai/data/airi_detector_mapping.v1.json`

These local files are not a replacement for the upstream project. They are a normalized STEM BIO-AI compatibility layer used to:

- preserve provenance
- bound deterministic runtime scope
- document detector-to-risk mapping decisions
- separate bundled runtime gaps from full-reference planning gaps

The AIRI source remains external and independently maintained. STEM BIO-AI must continue to attribute the upstream project in README, docs, and runtime artifacts.
