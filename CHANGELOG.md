# Changelog

All notable changes to STEM BIO-AI are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

IMMUTABLE formula changes require a minor version increment (1.x.0).
Rubric refinements and additions use patch versions (1.0.x).

---

## [1.7.3] - 2026-05-13

### Changed
- Removed two confirmed unused helpers from the active runtime surface:
  - `stem_ai/detectors.py::collect_evidence`
  - `stem_ai/app.py::_gradio_major`
- Refreshed the Hugging Face / Gradio demo text in `stem_ai/app.py` so the UI no longer advertises stale `1.6.0` wording and now reflects the current deterministic layer set.
- Standardized CLI artifact output under `stem_output/<repo_slug>` whenever the output root is `stem_output`, so repeated local scans stay grouped by target repository without changing other custom output paths.
- Rotated the active package, CLI, policy, documentation, and MICA version surfaces to `v1.7.3`.

### Verified
- Confirmed the removed helpers had no active runtime callers in the current repository.
- Re-ran import smoke for `stem_ai.detectors` after dead-code removal.
- Added regression coverage for `stem_output/<repo_slug>` output routing in the CLI scan path.

---

## [1.7.2] - 2026-05-12

### Changed
- Tightened `.slopconfig.yaml` so temporary and generated analysis paths (`tmp`, `build`, `audits`, `stem_output*`, `.manual_verify`) are excluded more explicitly from local structural inspection runs.
- Removed unused HTML renderer imports in `stem_ai/render_html.py`, reducing inspection noise without changing report behavior.
- Simplified `stem_ai/detector_contract.py` by extracting shared Python-module traversal and public-function iteration helpers, reducing repetition while preserving detector outputs.
- Revalidated the shipped calibration profiles against `1.7.2` and rotated public package, CLI, documentation, policy, and active MICA version surfaces to `v1.7.2`.

### Verified
- Confirmed P0/P1 parity on a same-target self-scan comparison (`A` vs `B`) with no drift in:
  - `score.final_score`
  - `score.formal_tier`
  - `code_contract`
  - `detector_summary`
  - `airi_risk_coverage`
  - `evidence_ledger` count

---

## [1.7.1] - 2026-05-12

### Added
- Added a governed local AIRI data layer with three packaged registries:
  - `stem_ai/data/airi_registry_full.v1.json` — normalized full local registry derived from the upstream AIRI CSV snapshot
  - `stem_ai/data/airi_runtime_bundle.v1.json` — curated deterministic runtime bundle
  - `stem_ai/data/airi_detector_mapping.v1.json` — detector-to-risk mapping registry with bundle/full-scope gap labels
- Added AIRI governance and attribution documents:
  - `docs/AIRI_DATA_GOVERNANCE.md`
  - `docs/THIRD_PARTY_DATA.md`
  - `docs/airi_registry.schema.json`
  - `docs/airi_detector_mapping.schema.json`
- Added regression coverage for AIRI registry/bundle/mapping provenance surfacing and bundle-scope gap separation.

### Changed
- Replaced hardcoded AIRI detector mappings and known-gap lists in `stem_ai/airi_risk_mapping.py` with packaged local registry files so provenance, runtime scope, and mapping governance are separated explicitly.
- Updated AIRI coverage outputs to surface registry version, runtime bundle version, mapping version, upstream snapshot date, license, attribution note, and split known gaps into `known_gaps_in_bundle` and `known_gaps_outside_bundle`.
- Corrected HTML score-matrix T0 hard-floor wording to match the authoritative 39-point cap used by the scanner and scoring rationale.
- Strengthened AIRI wording across README, HTML report docs, API contract, calibration architecture, and runtime output so the scanner’s curated runtime bundle is not confused with the full upstream AIRI universe.
- Rotated package/version surfaces to v1.7.1 and packaged the new AIRI registry artifacts.

---

## [1.7.0] - 2026-05-12

### Added
- **Layer 2 AST Contract Detectors (CC-1 / CC-2 / CC-3)** — new `stem_ai/detector_contract.py` module performing Python AST analysis beyond surface-scan reach:
  - `CC1_clinical_zero_default`: detects keyword-only and positional function parameters named `confidence_threshold`, `score_threshold`, `min_confidence`, etc. defaulted to `0.0` — a silent fail-open pattern in clinical inference paths.
  - `CC2_api_contract`: cross-checks names documented in README against `__all__` exports; flags phantom APIs (documented but not exported).
  - `CC3_shallow_validator`: identifies `validate_*` / `check_*` functions that use only `len()` (length gate) without regex structure validation — insufficient for PII/clinical data fields.
- **MIT AI Risk Repository (AIRI) V4 integration** — new `stem_ai/airi_risk_mapping.py` and `stem_ai/data/airi_medical_risks.json` (184 curated medical/clinical risk entries). Every scan now produces an `airi_risk_coverage` section mapping triggered detectors to their AIRI risk IDs, coverage rate, and known gaps.
- **Interactive 5-section HTML dashboard** — `--format html` (and `--format all`) now generates a self-contained interactive report with:
  - Sticky nav with scroll-spy active state
  - SVG semicircle score gauge + tier badge in hero header
  - Expandable code-integrity cards (click to reveal full evidence list)
  - AIRI covered/gaps toggle buttons
  - Evidence ledger filter chips (FAIL / WARN / PASS / INFO)
  - Tooltip `?` icons on every metric header (CSS `::after`, no JS)
  - Hover transitions and keyboard accessibility throughout
- `stem_ai/render_html_components.py` and `stem_ai/render_html_styles.py` — renderer split into three focused modules (each < 250 lines).
- `docs/UI_HTML_REPORT.md` — full specification for the HTML dashboard format, interactive features, and AIRI coverage mapping.
- `docs/assets/html_report_preview.png` — screenshot of the interactive HTML report.

### Changed
- `stem_ai/scanner.py` — wired CC-1/CC-2/CC-3 findings into `code_contract` result key; CC WARN entries surface in `notable_risks`; `build_airi_coverage()` called at the end of every scan.
- Rotated the active MICA memory layer and public package/version surfaces to v1.7.0.

---

## [1.6.8] - 2026-05-11

### Added
- Added root `CITATION.cff` and `.zenodo.json` so GitHub releases can be archived as DOI-backed software records through Zenodo.
- Added regression coverage for profile-aware C1 penalty simulation and preview-only post-delta profile validation.

### Changed
- Hardened `stem policy simulate` so preview scoring now uses the selected profile's `C1_penalty` when the baseline scan has already triggered C1, instead of assuming the runtime constant forever.
- Revalidated effective `preview_only` profiles after bounded deltas are applied, keeping future preview expansion inside the same runtime policy guardrails as packaged profiles.
- Strengthened mirror-only wording across CLI, Markdown, explain, calibration-architecture, and API-contract surfaces so `scan --policy <name>` is not confused with score-authoritative policy simulation.
- Rotated the active MICA memory layer and public package/version surfaces to v1.6.8.

---

## [1.6.7] - 2026-05-11

### Added
- Added `stem policy derive` as an auditable researcher-intent translation surface built from the documented 0-5 rule table.
- Added `stem policy simulate <repo>` so users can preview named-profile or preview-only policy outcomes against a real repository before any authoritative score changes are enabled.
- Added deterministic translation and simulation helpers for top-down rule matching, preview-only bounded deltas, and policy-tier/cap preview math.
- Added regression coverage for intent translation, preview-only fallback, and CLI derive/simulate outputs.

### Changed
- Kept formal scan scoring unchanged while adding governed derive/simulate UX, so 1.6.7 narrows the user-policy gap without turning the CLI into a free-form tuning console.
- Clarified calibration documentation so the profile contract, policy visibility, and derive/simulate preview lanes are described as implemented mirror-only architecture rather than as a future-only proposal.
- Rotated the active MICA memory layer and public package/version surfaces to v1.6.7.

---

## [1.6.6] - 2026-05-10

### Added
- Added `stem policy list` and `stem policy explain <name>` so named calibration profiles can be inspected directly from the CLI.
- Added `--policy <name>` to scan, gate, and advisory workflows so selected profiles are surfaced consistently in result metadata and stdout summaries.
- Added regression coverage for policy list/explain CLI behavior and selected-profile metadata surfacing.

### Changed
- Extended Markdown, explain, and PDF header surfaces to show the active calibration profile name, status, and read mode.
- Kept policy selection mirror-only in 1.6.6 so named profiles remain visible and testable before any score-authoritative read-through is enabled.
- Rotated the active MICA memory layer and public package/version surfaces to v1.6.6.

---

## [1.6.5] - 2026-05-10

### Added
- Added `stem_ai.calibration_profile` for Phase 1 mirror-only calibration profile loading, validation, and canonical policy hashing.
- Added packaged policy artifacts: `policy/scoring_profile.schema.json`, `policy/scoring_profile.default.v1.json`, and `policy/scoring_profile.strict_clinical_adjacency.v1.json`.
- Added calibration profile metadata to result objects so outputs now surface `policy_version`, `profile_name`, `profile_status`, `profile_read_mode`, and canonical `policy_sha256`.
- Added regression coverage for calibration profile validation, metadata surfacing, and Markdown / explain rendering.
- Added a fixture-format example for Phase 1 profile parity under `tests/fixtures/calibration_profiles/`.

### Changed
- Kept scoring behavior unchanged while introducing mirror-only profile validation so Phase 1 remains parity-first rather than behavior-changing.
- Updated `docs/API_CONTRACT.md` and `docs/CALIBRATION_PROFILE_DESIGN.md` to define Phase 1 calibration metadata, fixture format, and schema/runtime validation boundaries.
- Rotated the active MICA memory layer and public package/version surfaces to v1.6.5.

---

## [1.6.4] - 2026-05-10

### Added
- Added CA taxonomy provenance fields to the public classification surface so outputs now record the active runtime taxonomy version and source.
- Added regression coverage for CA taxonomy metadata surfacing and tightened B2 threshold behavior.

### Changed
- Tightened Stage 3 B2 entry criteria so a minimal single-term limitations mention no longer receives partial credit without structured boundary language.
- Clarified in public docs that the active clinical-adjacent taxonomy remains a runtime `scanner.py` authority and that reference markdown is informative, not authoritative.
- Rotated the active MICA memory layer and public package/version surfaces to v1.6.4.

---

## [1.6.3] - 2026-05-10

### Added
- Added AST analysis scope surfacing to stdout, Markdown reports, and PDF outputs when deterministic AST scanning is capped by file-count limits.
- Added `docs/CALIBRATION_PROFILE_DESIGN.md` as a design proposal for future versioned scoring-policy profiles.
- Added regression coverage for AST cap surfacing across CLI, Markdown, and PDF fallback outputs.
- Added regression coverage for negative-context provenance handling in Stage 3 B1 scoring.

### Changed
- Tightened Stage 3 B1 provenance scoring so negative or non-approval IRB / data-source contexts no longer receive maximum provenance credit.
- Updated `docs/SCORING_RATIONALE.md` with executive summary, quick reference, key terms, deliberate scope boundaries, and explicit order-of-operations onboarding.
- Rotated the active MICA memory layer and public package/version surfaces to v1.6.3.

---

## [1.6.2] - 2026-05-08

### Added
- Added workflow-oriented CLI entry points: `stem scan`, `stem gate`, and `stem advisory validate|packet|call|check-response`.
- Added `--summary full|compact|off` stdout control with command-specific defaults (`scan=full`, `gate/advisory=compact`).
- Added `--output` as a clearer alias for `--out`.
- Added regression coverage for the new workflow-oriented CLI paths and shorthand compatibility.
- Added `pytest.ini` to ignore transient local output/temp directories during test collection.

### Changed
- Reframed the CLI around user intent instead of one long option string while preserving `stem <folder>` and `stem audit ...` compatibility.
- Updated README and `docs/CLI_REFERENCE.md` to document the new workflow model and migration path from legacy inline advisory/gate flags.
- Promoted package metadata and public version references to v1.6.2.

---

## [1.6.1] - 2026-05-08

### Added
- Added `--tier-gate T0|T1|T2|T3|T4` CLI flag for CI/CD pipeline integration: exit code 1 if the audit tier is below the required threshold.
- Added `--quiet` CLI flag to suppress human-readable stdout summary while still writing artifacts.
- Added enriched CLI stdout summary with per-stage scoring breakdown (Stage 1–4), clinical adjacency status, code integrity warnings, bio diagnostics, and regulatory review flags.
- Added AI usage transparency line to stdout: always reports whether the scan used deterministic-only mode or advisory provider mode.
- Added remediation hints from `notable_risks` (top 3 action items displayed in stdout).
- Added `if __name__ == "__main__"` guard to `cli.py` so `python -m stem_ai.cli` works as a valid entry point.
- Added `docs/CLI_REFERENCE.md` documenting all CLI flags, stdout format, CI/CD integration examples, exit codes, and AI transparency features.

### Changed
- CLI stdout now surfaces data from v1.3.0–v1.6.0 engine features (replication lane, bio diagnostics, regulatory traceability) that were previously only available in JSON/Markdown/PDF artifacts.
- Updated README Quick Start section with CI/CD gate examples and CLI reference link.
- Updated version badge and citation to v1.6.1.

---

## [1.6.0] - 2026-05-06

### Added
- Added a registry-driven regulatory traceability output layer with `regulatory_basis`, `stage_traceability`, and `regulatory_traceability` fields in the local CLI result object.
- Added report/explain/PDF regulatory basis note rendering using `docs/regulatory_basis_registry.v1.json` and its JSON schema.
- Added automated `review_required` checks for stale registry month labels, draft-guidance presence, and missing required regulatory source families.
- Added direct surfacing of bio-detector scope notes so `not_detected` and `not_applicable` statuses explain what was and was not assessed.

### Changed
- Promoted the local CLI result schema to `stem-ai-local-cli-result-v1.6` to match the now-stable traceability payload shape.
- Hardened regulatory traceability semantics so negative or missing Stage 1 boundary signals no longer read as positive Article 13 alignment.
- Lowered reasoning diagnostics wording from model-like confidence language to explicit heuristic language (`heuristic_consistent`, `low_spread`, `within_heuristic_gate`) and surfaced uncalibrated priors directly in report text.
- Updated package metadata, README, MICA active memory layer, and public docs for the v1.6.0 release.

### Fixed
- Restricted offline advisory fallback citations to active evidence states (`detected`, `error`, `manual_review_required`) so absent or not-detected findings no longer masquerade as priority evidence.
- Regenerated ClawBio dogfooding artifacts against the live v1.6.0 code path to confirm new schema, traceability wording, and detector-scope notes are rendered consistently.
- Removed superseded deterministic-diagnostics proposal indirection from the active public docs surface so the 1.6.0 implementation pair is now `DETERMINISTIC_DIAGNOSTICS.md` plus `REGULATORY_MAPPING.md`.

---

## [1.5.11] - 2026-05-06

### Added
- Added `BIO_smiles_rdkit_validation` as an optional A1 lane that emits stronger evidence when RDKit is available and rejects invalid hardcoded SMILES-like candidates.
- Added regression coverage for RDKit-lane unavailable / invalid / valid paths and for `AllChem.MolFromSmiles` parser-guard detection.

### Changed
- Tightened `BIO_smiles_surface_integrity` precision by excluding generated surfaces (`build/`, `dist/`, `audits/`), hex colors, version/hash/schema strings, and other non-chemistry token patterns.
- Expanded SMILES parser-guard detection to include `AllChem.MolFromSmiles`.
- Updated the deterministic diagnostics spec to mark A1 as implemented and to document the current evidence-only behavior.
- Rotated the active MICA memory layer to v1.5.11 for the SMILES precision and RDKit-lane patch release.

### Fixed
- Eliminated major SMILES false positives observed during dogfooding on `AI-SLOP-DETECTOR`, `STEM-BIO-AI`, and `BioClaw`.
- Corrected RDKit-lane status semantics so environments with RDKit installed but no invalid candidates report `not_detected` instead of `not_applicable`.

---

## [1.5.10] - 2026-05-06

### Added
- Added `stem_ai/detector_bio.py` with deterministic evidence-only bio diagnostics for conservative SMILES surface checks, SMILES parser-guard checks, silent mock fallback detection, traceability manifest surface detection, and bio-tool subprocess run-trace heuristics.
- Added Markdown and `--explain` surfacing for bio deterministic diagnostics in audit outputs.
- Added regression coverage for bio diagnostics and explain/Markdown surfacing.
- Added `docs/DETERMINISTIC_DIAGNOSTICS.md` as the promoted active deterministic diagnostics specification.
- Added `docs/REGULATORY_MAPPING.md` to the public docs surface and package manifest.

### Changed
- Promoted `docs/DETERMINISTIC_DIAGNOSTICS_PROPOSAL.md` to a pointer document and moved active documentation to `docs/DETERMINISTIC_DIAGNOSTICS.md`.
- Linked README proof surfaces to deterministic diagnostics and regulatory traceability docs.
- Rotated the active MICA memory layer to v1.5.10 for the bio-detector implementation release.

### Fixed
- Restored bio-detector integration to the evidence-bundle path in `stem_ai/detectors.py` and removed drift from an invalid direct-scanner wiring pattern.
- Restored `stage_3` scoring flow in `stem_ai/scanner.py` after accidental regression during external edits.

---

## [1.5.9] - 2026-05-06

### Added
- Added `docs/ADVISORY_SECRET_HANDLING.md` covering provider-specific environment variables, `.env` handling policy, endpoint restrictions, artifact redaction rules, and the no-secret-persistence boundary for advisory packets.
- Added `docs/ADVISORY_RUNTIME.md` documenting the explicit `--advisory call` trust boundary, runtime guards, and current non-implemented adapter behavior.
- Added `docs/EXAMPLE_AUDITS.md` as a surface-facing proof index for sample report artifacts, live demo behavior, and comparison expectations.
- Added `.env.example` documenting supported advisory environment variables without shipping any secret values.

### Changed
- Strengthened the public README surface with PyPI install path, proof-surface links, and explicit secret-boundary notes for advisory packet export.
- Rotated the active MICA memory layer to v1.5.9 and documented advisory secret-boundary policy in the active archive/playbook/lessons set.

### Fixed
- Advisory provider configuration now prefers provider-specific API key env vars before the generic fallback and exports the selected env-var name without exposing the secret.
- Advisory provider request validation now rejects embedded-credential base URLs, rejects non-local plain `http` endpoints, and requires `https` for cloud-provider overrides.
- Secret-free handoff metadata now includes endpoint-policy validation, network-mode classification, and exported env-contract metadata for downstream runners.
- Added explicit `--advisory call` runtime mode with centralized redaction, adapter logging policy export, child-env allowlist reporting, and artifact pre-write sanitization for JSON/Markdown/explain outputs.

---

## [1.5.8] - 2026-05-05

### Fixed
- Narrowed `C2_dependency_pinning` to real dependency-manifest surfaces so non-dependency `pyproject.toml` metadata lines such as `name`, `version`, `readme`, and `keywords` no longer count as loose dependencies.
- Exempted realistic credential fixtures under test/example paths from `C1_hardcoded_credentials` penalties while keeping production-path `sk-*`, `AKIA*`, `ghp_*`, and `api_key=` detections active.
- Replaced broad text-level `C4` matching with AST-backed executable fail-open handler detection so string literals and detector-explanation text containing `except: pass` no longer trigger warnings.
- Removed the Gradio 6 runtime warning in the Hugging Face demo by routing CSS through the correct `Blocks`/`launch` compatibility path.
- Fixed long-standing package manifest drift so PyPI artifacts include `SKILL.md`, active `memory/` files, and public `docs/` contract files instead of shipping a code-only package surface.

### Added
- Added regression coverage for credential-fixture exemption, pyproject metadata precision, executable fail-open detection, and non-executable `except: pass` string immunity.

### Changed
- Improved detector honesty on final dogfooding targets: `Sidrce` now clears prior `C1/C2/C4` false positives and moves from `52 / T1` to `62 / T2` under the corrected scanner.

---

## [1.5.7] - 2026-05-05

### Added
- Added advisory packet self-validation via `packet_contract`, checking allowlist parity, snippet omission, and omission-count sanity before any provider handoff.
- Added exported advisory contract schemas (`contract_schemas`) so downstream validators can consume stable input/output packet shapes without reading repository code.
- Added secret-free provider request schema export and deterministic provider argument validation metadata under `provider_request`.
- Added regression coverage for advisory contract schema export, provider request validation, advisory packet allowlist mismatch, and invalid payload-shape handling.
- Added `docs/MICA_MEMORY.md` documenting active-vs-archived memory policy, `mica.yaml` loader responsibility, and release rotation rules.

### Changed
- Updated README, API contract, scoring rationale version markers, and release validation defaults for the v1.5.7 advisory contract-hardening release.
- Rotated the active MICA memory layer to v1.5.7 and updated `memory/mica.yaml` / `SKILL.md` so the loader follows the active files instead of stale hard-coded memory filenames.

### Fixed
- Hardened advisory validation so malformed provider payload shapes are rejected as structured contract errors instead of causing a validator crash.

---

## [1.5.6] - 2026-05-01

### Fixed
- Reduced CA-DIRECT/T0 hard-floor false positives from framework meta-documentation such as scoring tables, regex descriptions, advisory contracts, and diagnostic-layer labels.
- Expanded clinical-boundary detection for phrases such as "not a medical device", "not intended for clinical use", "not clinically validated", and "does not provide clinical diagnoses".
- Updated stale public contract, scoring rationale, release validation default, measurement-basis text, and PDF Stage 3 explanatory copy to match v1.5.5/v1.5.6 behavior.

### Added
- Added regression coverage proving real direct clinical claims still trigger the T0 floor while framework self-documentation does not.
- Added `scripts/benchmark_local10_ca_fp_impact.py` and local-10 v1.5.6 CA false-positive impact artifacts.

---

## [1.5.5] - 2026-05-01

### Added
- Added `docs/API_CONTRACT.md`: stable public contract with Locked/Additive/Internal field classifications, full `EvidenceFinding` record specification, Advisory Protocol (6 non-negotiable rules), Python API signatures, tier definitions, and additive-only compatibility policy.

### Changed
- Superseded `docs/API_CONTRACT_V1_5_DRAFT.md` (retained for historical reference).
- Updated README: professional bio/medical AI structure, v1.5.5 badge and citation, Detection table moved to collapsible section, Advisory Contract section with enforcement rules, removed stale v1.3 references.
- Bumped version to 1.5.5 (aligning package version with v1.5.4 code tag that was released without a version bump).

---

## [1.5.4] - 2026-05-01

### Added
- Refined Stage 3 T3, B1, and B2 scoring from binary to three-tier:
  - T3 Changelog: 0 (absent) / +5 (exists, no bug entries) / +15 (bug-fix, patch, or security entries present).
  - B1 Data Provenance: 0 (no manifest) / +10 (manifest present) / +15 (manifest + IRB or dataset-citation language).
  - B2 Bias/Limitations: 0 (no vocabulary) / +8 (vocabulary only) / +15 (vocabulary + quantitative measurement evidence).
- Added `CHANGELOG_BUG_TERMS`, `DATA_SOURCE_TERMS`, and `BIAS_MEASUREMENT_TERMS` regex patterns.
- Added `_score_changelog`, `_score_provenance`, and `_score_bias` helper functions extracted from `_score_stage_3`.
- Added unit tests for each three-tier scoring path (9 new test cases).
- Added `scripts/benchmark_local10_stage3_3tier_impact.py` and local-10 v1.5.4 Stage 3 three-tier impact benchmark artifacts.
- Added `docs/SCORING_RATIONALE.md`: formula derivation, baseline-60 convention, tier boundary justification (anchored to scoring baseline ± offsets), Stage 1–4 rationale, score-cap policy, and calibration gap disclosures.

### Changed
- Local-10 benchmark: 0 tier changes vs v1.5.3 baseline; mean score delta −0.9 (bare provenance manifests no longer earn full B1 credit without dataset citation language).

---

## [1.5.3] - 2026-05-01

### Added
- Added Stage 2R limitation-repetition credit across README, docs, and changelog surfaces.
- Added Stage 2R deductions for internal clinical-boundary contradictions, stale README/package version metadata, and unsupported workflow/test/CLI claims.
- Added regression coverage for the new Stage 2R R4/D1/D3/D4 scoring paths.
- Added `scripts/benchmark_local10_stage2r_impact.py` and local-10 v1.5.3 Stage 2R impact artifacts.

### Changed
- Updated Stage 2R measurement documentation from simple vocabulary overlap to repo-local consistency plus deterministic contradiction/staleness/workflow-support checks.

---

## [1.5.2] - 2026-05-01

### Added
- Added Stage 1 H1-H6 hype-claim penalties for clinical certainty, regulatory approval, autonomous replacement, breakthrough marketing, universal generalization, and perfect-accuracy language.
- Added Stage 1 R1-R5 responsibility signals for limitations sections, regulatory frameworks, clinical disclaimers, demographic-bias boundaries, and reproducibility provisions.
- Added `stage_1_rubric` JSON output and matching evidence-ledger detectors for the new Stage 1 scoring surface.

### Changed
- Moved `spec/` to local-only private material by ignoring it in Git and removing tracked spec files from the release tree.

---

## [1.5.1] - 2026-05-01

### Changed
- Promoted the active MICA memory layer to v1.5.1 snapshots and updated `memory/mica.yaml` to load the current archive, playbook, and lessons files.
- Updated release metadata, README badge/citation, and release validation defaults from v1.5.0 to v1.5.1.

### Added
- Added v1.5.1 memory provenance entries covering the post-v1.5.0 memory alignment commit and current release metadata.
- Added `MANIFEST.in` to bound source-distribution inputs and exclude generated audit/build/temp artifacts from release packaging.
- Added a stdlib package-build path used by release validation to avoid local setuptools frontend hangs in Python 3.14 environments.

---

## [1.5.0] - 2026-04-30

### Added
- Added `S4_license_restriction` evidence detection for non-commercial, research-only, academic-only, no-clinical-use, and related license/use-scope boundary language.
- Added `docs/API_CONTRACT_V1_5_DRAFT.md` documenting the draft local Python/CLI contract without declaring a stable external SDK.
- Added regression coverage for license restriction evidence and Stage 2R refactor score preservation.

### Changed
- Refactored `_score_stage_2r` into smaller helper functions without changing its scoring behavior or T0-T4 boundaries.

---

## [1.4.5] - 2026-04-30

### Added
- Added `stem_ai/provider_benchmark.py` for compact provider-packet and provider-response validation benchmark records.
- Added `scripts/provider_packet_benchmark.py` to export provider-budgeted packets, packet stats, packet summaries, and optional saved response-validation records without making provider API calls.
- Added `audits/benchmark-v1.4/` workspace documentation for provider response benchmark artifacts.
- Added regression coverage for provider benchmark packet summaries and response-validation records.

---

## [1.4.4] - 2026-04-30

### Added
- Added provider-budgeted advisory packets capped to 40 ranked evidence findings for practical Gemini/Qwen-style context budgets.
- Added `allowed_finding_ids` to advisory input packets so providers can copy exact citation IDs instead of shortening detector names.
- Added `provider_prompt_contract` guidance documenting strict JSON output, exact citation-copying, no score override, and clinical/regulatory claim boundaries.
- Added regression and release validation coverage for deterministic provider packet budgets and citation allowlists.

### Changed
- `--advisory packet` now emits the provider-budgeted packet profile by default while preserving full audit JSON separately.

---

## [1.4.3] - 2026-04-30

### Added
- Added `stem_ai/advisory_response.py` for validating provider-produced advisory JSON files against the current audit evidence ledger.
- Added `stem audit ... --advisory-response FILE` to validate external Gemini/OpenAI/Claude/Ollama/local-model style JSON responses without making API calls.
- Added response contracts with source hash, byte count, JSON parser marker, no-network flag, and no citation-repair flag.
- Added regression coverage for valid provider responses, malformed provider responses, parse errors, and CLI response-file validation.

### Changed
- Removed v1.4.2 mock harness modes from the public CLI surface; v1.4.3 uses real response-file validation instead of mock/stub advisory modes.

---

## [1.4.2] - 2026-04-30

### Added
- Added `stem_ai/advisory_adapters.py` as a deterministic no-network adapter contract harness.
- Added mock advisory modes: `mock-valid`, `mock-invalid`, `mock-error`, and `mock-timeout`.
- Added standard adapter error envelopes for adapter failures and timeout simulations.
- Added regression coverage proving malformed advisory output remains invalid and is not citation-repaired.

---

## [1.4.1] - 2026-04-30

### Added
- Added provider-neutral advisory provider registry and secret-free environment configuration loader.
- Added `--advisory packet` to export a bounded advisory input packet for future cloud, OpenAI-compatible, local-server, and local-runtime adapters without calling any AI API.
- Added standalone `{stem}_advisory_input.json` output with provider handoff metadata, registry status, evidence citation policy, and sanitized evidence ledger.
- Added release validation and regression coverage for advisory packet export and secret-free provider metadata.

---

## [1.4.0] - 2026-04-30

### Added
- Added provider-neutral `ai_advisory` contract support with offline validation via `stem audit <repo> --advisory validate`.
- Added `stem_ai/advisory_contract.py` for advisory input packet construction, citation extraction, citation validation, prohibited-claim checks, and deterministic no-AI advisory output.
- Added ASDP-inspired advisory schema and compile notes under `spec/asdp/` and `docs/asdp/`.
- Added v1.4.0 planning document for evidence-bound AI advisory, provider adapters, ASDP contract compilation, and local Qwen/Kimi/Unsloth future paths.
- Added tests ensuring advisory input omits raw snippets by default, rejects unknown citations, rejects score overrides, rejects clinical/regulatory claims, and surfaces advisory validation in CLI/Markdown/explain output.

### Changed
- Established the provider-neutral advisory contract surface that later converged into the stable local CLI result schema family.

---

## [1.3.2] - 2026-04-30

### Added
- Added `stem_ai/reasoning_model.py` as a deterministic diagnostic layer over the evidence ledger.
- Added `reasoning_model` JSON output with evidence budget, confidence envelope, lane coherence, uncertainty budget, evidence-risk gate, and benchmark alignment function support.
- Added reasoning diagnostics to Markdown and `--explain` outputs without changing the established final score.
- Added regression coverage for deterministic token counting, S4-null lane coherence handling, benchmark alignment metrics, and final-score non-overwrite behavior.

### Changed
- Updated release validation defaults to target v1.3.2.

---

## [1.3.1] - 2026-04-30

### Fixed
- Improved local-10 benchmark alignment by detecting clinical-adjacent skill-catalog surfaces such as AutoDock, nnU-Net, pydicom, drug docking, and medical imaging.
- Excluded obvious placeholder/test credential values from the C1 penalty while keeping them visible in the evidence ledger as non-applicable evidence.

### Added
- Added local-10 control benchmark summaries and before/after comparison artifacts for the CA/C1 precision patch.

---

## [1.3.0] - 2026-04-30

### Added
- Added v1.3 evidence ledger output with stable POSIX `finding_id` values, detector metadata, source file, line, snippet, match type, explanation, and optional metadata.
- Added stdlib AST observation summary (`ast_signal_summary`) for assertion tests, seed settings, argparse CLI surfaces, docstrings, annotations, portable model loading, syntax errors, and fail-open handlers.
- Added Stage 4 Reproducibility & Replication Evidence as a separate lane with `replication_score`, `replication_tier`, and `stage_4_rubric`.
- Added deterministic Stage 4 detectors for containers, Makefile reproduction/evaluation targets, environment/lock files, exact pins/hashes, README reproducibility sections, checksum files, dataset/model artifact references, `CITATION.cff`, CLI evidence, seed evidence, and runnable examples.
- Added `stem audit ... --explain`, which writes a plain-text proof trace grouped by detector and includes full `finding_id` values for citation by future AI layers.
- Added v1.3 planning documents for evidence-ledger contracts, Stage 4, benchmark methodology, and deferred v1.3.1 reasoning model candidates.
- Added `audits/benchmark-v1.3/` template workspace for the 30-repository benchmark manifest, JSONL results, tier alignment summary, and false-positive/false-negative log.

### Changed
- Split detector implementation into focused modules: surface detectors, AST detectors, Stage 4 detectors, shared detector utilities, shared patterns, and evidence dataclasses.
- Kept AST and Stage 4 outputs observation-only for v1.3.0; the established final score formula remains unchanged.
- Updated README to describe Stage 4, `--explain`, AST observation, replication tiers, and evidence-ledger artifacts.

### Fixed
- Closed evidence-ledger coverage gaps for scored Stage 3 and C1-C4 components.
- Improved AST detection for direct `ArgumentParser()` imports and mock-style assertion calls.
- Removed duplicated detector constants from scanner internals by centralizing shared patterns.
- Reduced nested complexity in explain rendering, AST visiting, dependency-pinning detection, and fallback PDF page-stream generation; local slop scan reports all Python files clean.

---

## [1.2.0] - 2026-04-30

### Changed
- Repositioned as a **deterministic evidence-surface scanner** rather than a trust auditor; README subtitle and Core Features updated accordingly.
- T0–T4 labels changed from trust verdicts to **triage / review-priority tiers** with explicit scope statements.
- Added **"What STEM Actually Measures"** table to README — each score component now documents its physical detection method.
- Renamed "Stage 1 — README Intent Analysis" to "Stage 1 — README Evidence Signal" in PDF reports.
- `Measurement Boundary` section in README replaces `Boundary` and explicitly states that scores reflect observable signals, not clinical safety or author intent.
- `pyproject.toml` description updated; `[demo]` extra dependencies cleaned up (removes outdated pins).

### Fixed
- Removed bare `treatment` from CA-DIRECT terms; replaced with phrase-level patterns `treatment recommendation` and `treatment guidance` to reduce false positives on bioinformatics data-processing contexts.
- Removed bare `population` from B2 bias/limitations terms; the word alone is a false positive in population-genetics contexts.

### Added
- `measurement_basis` field added to JSON output documenting the detection method for each scored component.

---

## [1.1.3] - 2026-04-29

### Fixed
- Corrected Python dependency-pinning detection so loose ranges such as `>=`, `<=`, `~=`, `<`, and `>` no longer pass C2 as exact pins.
- Added deterministic CA severity classification for LOCAL_ANALYSIS (`CA-DIRECT`, `CA-INDIRECT`, `none`) and activated the T0 hard-floor cap for unbounded direct clinical claims.
- Added a T2 score cap for clinical-adjacent repositories that lack an explicit non-clinical/non-diagnostic boundary.
- Rebalanced Stage 3 scoring to normalize the full 80-point T/B rubric to 100, restoring attainable T3/T4 ranges.
- Fixed B1 max-score mismatch and added local B2 bias/limitations and B3 COI/funding evidence detection.
- Removed repository-specific deprecated-path scanning and replaced it with generic deprecated/legacy/archive directory scanning.
- Hardened fail-open exception detection for CRLF code paths.
- Prevented fallback PDF text overflow when reportlab is unavailable.
- Bounded reportlab style cache growth for long-running Gradio sessions.
- Added CLI `--version` and safer Gradio report-level fallback handling.
- Made the skill validator select the latest core spec and MICA archive instead of hard-coding v1.1.2.

---

## [1.1.2] - 2026-03-27

### Added
- PATCH-46: MICA v0.2.0 memory layer — `memory/` directory with composition contract,
  archive (18 IMMUTABLE rules as design_invariants), session playbook, and lessons document
  (10 failure modes from L-001 through L-010)
- `memory/mica.yaml` — MICA v0.2.0 composition contract (mode: protocol_evolution)
- `memory/stem-ai.mica.v1.1.2.json` — machine-checkable governance archive
- `memory/stem-ai-playbook.v1.1.2.md` — session protocol and rubric drift guard
- `memory/stem-ai-lessons.v1.1.2.md` — failure mode history (10 lessons from 33 patches)
- PATCH-47: MICA initialization step added to SKILL.md loading order (Step 0) and CORE spec Section 8.2 Execution Instruction
- DEV.to draft for STEM BIO-AI v1.1.2 memory contract explanation
- Official v1.1.2 LOCAL_ANALYSIS audit artifact shape: `report.md` plus `experiment_results.json`
- Real public-repository audit output under `audits/fieldbioinformatics_v1_1_2/`
- Stage 2R: Repo-Local Consistency lane for LOCAL_ANALYSIS audits when external Stage 2 evidence is not collected
- Python CLI package with `stem audit <folder>` local scan command
- CLI output modes for 1-page brief and 3/5-page detailed Markdown, JSON, and PDF reports
- HuggingFace/Gradio `app.py` demo entry point using the same deterministic scanner

### Changed
- Canonical spec filename advanced to `spec/STEM-AI_v1.1.2_CORE.md`
- SKILL.md version updated to 1.1.2
- Public explanation shifted from synthetic evidence examples to a real audit-result JSON and verifier flow

### Fixed
- Post-release consistency cleanup applied to active package surfaces on 2026-04-27
- Active package surfaces aligned to STEM BIO-AI v1.1.2 and MICA v0.2.0
- Template references updated to the current canonical spec and audit report version
- Skill validator strengthened to detect template/spec/MICA drift before release
- `local_analysis_scan.sh` output description corrected to match actual stdout format
- Removed placeholder example audits and synthetic public evidence bundle from the official v1.1.2 surface

---

## [1.1.1] - 2026-03-26

### Fixed
- Canonical spec version alignment errors (`1.0.6` remnants removed from the 1.1.x package surface)
- Template and package references updated to the correct canonical spec filename

### Added
- Explicit statement of the relationship between technical audit and STEM BIO-AI
- Method/template wording clarifying technical audit as fact extraction and STEM BIO-AI as trust classification

### Changed
- Canonical spec filename advanced to `spec/STEM-AI_v1.1.1_CORE.md`

---

## [1.1.0] - 2026-03-26

### Changed
- **Architecture:** Single-file spec split into universal skill package (multi-file)
- **Name:** "Trust Audit Framework for Bio/Medical AI" -> "Trust Audit Framework for Bio/Medical AI Repositories"
- **Runtime:** Added AI CLI support alongside LLM-Native

### Added
- SKILL.md entry point (universal agent skill format, 16+ platforms)
- `spec/` directory for core rubric
- `discrimination/` directory for YES/NO example pairs
- `templates/` directory for institutional output (7 templates)
- `scripts/` directory for automation (3 shell scripts)
- `references/` directory for lookup tables
- `examples/` directory for real audit examples
- `.github/workflows/` CI/CD pipelines (3 workflows)
- README.md, CONTRIBUTING.md, LICENSE, .gitignore
- GitHub-ready repository structure

### Carried Forward (from 1.0.6)
- All 43 patches (PATCH-1 through PATCH-43)
- All 19 self-validation checks
- 4 execution modes (LOCAL_ANALYSIS, FULL, SEARCH_ONLY, MANUAL)
- Dual-path TEXT/CODE rubric
- CA 3-tier severity (DIRECT, INDIRECT, PLANNED)
- C1-C4 code integrity items
- Governance overlay (Stage 3G) with generic terminology
- T4 PENDING denominator = 80 (corrected)
- INSUFFICIENT_DATA split (NASCENT / STALE)
- CA-DIRECT redistribution guardrail

---

## [1.0.6] - 2026-03-22

### Added
- PATCH-27: LOCAL_ANALYSIS execution mode
- PATCH-28: Dual-path rubric (TEXT_PATH / CODE_PATH)
- PATCH-29: C1-C4 code-level integrity items
- PATCH-30: CLINICAL_ADJACENT 3-tier severity
- PATCH-31: CA detection dual-path (import scan + keyword scan)
- PATCH-32: T4 PENDING denominator corrected (85 -> 80)
- PATCH-33: INSUFFICIENT_DATA label split (NASCENT / STALE)
- PATCH-34: Stage 2 S2-0 social evidence auto-fetch
- PATCH-35: FULL MODE fetch failure per-item fallback
- PATCH-36: Stage 3G activation strengthened (artifact required)
- PATCH-37: Governance terminology abstracted (generic terms)
- PATCH-38: Score Matrix inline arithmetic mandatory
- PATCH-39: T2 discrimination examples
- PATCH-40: Auditor affiliation field
- PATCH-41: CHECK 17-19 (C1-C4 gating, CA severity, dual-path)
- PATCH-42: C1 env-var fallback pattern detection
- PATCH-43: Mode comparability notice + self-audit advisory

---

## [1.0.5] - 2026-03-22

### Added
- PATCH-15: Governance Overlay lane (Stage 3G)
- PATCH-16: Base tier preserved, overlay advisory only
- PATCH-17: G1-G5 rubric
- PATCH-18: Remediated target reading order
- PATCH-19: Dual output (Base Tier + Overlay Verdict)
- PATCH-20: CHECK 12-16
- PATCH-21: H1-H6 discrimination examples
- PATCH-22: B3 COI 3-tier expansion
- PATCH-23: Execution order fix (DERIVED-3 before Stage 3)
- PATCH-24: Procurement Threshold Note
- PATCH-25: N/A redistribution observation
- PATCH-26: G1-G5 discrimination examples

---

## [1.0.4] - 2026-03-19

### Added
- PATCH-9: Author Domain Context (informational, zero score impact)
- PATCH-10: DERIVED-1 expiry_date
- PATCH-11: DERIVED-2 audit_branch
- PATCH-12: DERIVED-3 trajectory_signal
- PATCH-13: Non-English README confidence flag
- PATCH-14: Trajectory modifier (+/-5 pts Stage 3)

---

## [1.0.3] - 2026-03-19

### Changed
- Weighted formula: S1x0.40, S2x0.20, S3x0.40
- T0_HARD_FLOOR replaces RP3
- CLINICAL_ADJACENT trigger list expanded to 60+
- T4 PENDING minimum activity threshold
- Mandatory disclaimer block

---

## [1.0.2] - 2026-03-19

### Added
- NASCENT_REPO flag + baseline 50 + T4 PENDING
- CLINICAL_ADJACENT flag + active deduction table
- Live-fire audit: jaechang-hits/scicraft

---

## [1.0.1] - 2026-03

### Changed
- Narrative scoring -> rubric-based point checklists
- Hard STOP -> MANUAL mode with partial audit fallback
- Biological Integrity checklist (B1-B3) added

---

## [1.0.0] - 2026-03

### Added
- Initial 3-stage evaluation concept
- README Dissection, Cross-Platform Verification, Code Debt Audit
- JSON + Markdown output format
