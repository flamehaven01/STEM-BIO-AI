# STEM BIO-AI Architecture

This document describes the implemented repository structure and runtime boundaries in `v1.8.0`.

## Purpose

STEM BIO-AI scans a local repository and classifies its observable evidence surface.

It does not execute target training runs, call an LLM in the default scoring path, or assert clinical safety.

## Operating Model

The default path is local and deterministic:

1. read repository files from a local clone
2. extract README, docs, code, CI, and package metadata signals
3. score those signals across Stage 1, Stage 2R, Stage 3, and Stage 4 lanes
4. apply code-integrity penalties and policy caps
5. emit traceable JSON, Markdown, HTML, and PDF artifacts

Optional advisory flows exist as a separate trust boundary and are documented in:

- [ADVISORY_RUNTIME.md](ADVISORY_RUNTIME.md)
- [ADVISORY_SECRET_HANDLING.md](ADVISORY_SECRET_HANDLING.md)
- [API_CONTRACT.md](API_CONTRACT.md)

## High-Level Flow

```text
Target repository
  -> scanner.py
  -> detector_surface.py / detectors.py
  -> detector_ast.py / detector_bio.py / detector_contract.py / detector_stage4.py
  -> evidence.py + policy_intent.py + calibration_profile.py
  -> render.py / render_html.py
  -> JSON / Markdown / HTML / PDF evidence packet
```

## Core Modules

| Module | Responsibility |
|---|---|
| `stem_ai/cli.py` | CLI entry points for `scan`, `gate`, `policy`, and advisory commands |
| `stem_ai/scanner.py` | Repository walk, signal orchestration, score assembly |
| `stem_ai/detectors.py` | Shared detector entry surfaces and signal collection glue |
| `stem_ai/detector_surface.py` | README/docs/package/CI evidence extraction |
| `stem_ai/detector_ast.py` | AST-based code integrity and contract checks |
| `stem_ai/detector_bio.py` | Bio-adjacent deterministic diagnostics and parser-guard lanes |
| `stem_ai/detector_contract.py` | Contract and mismatch detection across advertised and implemented surfaces |
| `stem_ai/detector_stage4.py` | Replication and reproducibility evidence lane |
| `stem_ai/evidence.py` | Trace object construction and proof ledger materialization |
| `stem_ai/render.py` / `stem_ai/render_html.py` | Markdown, PDF, and HTML report generation |
| `stem_ai/calibration_profile.py` | Versioned policy profile loading and preview/simulation support |
| `stem_ai/policy_intent.py` | Governed profile-derivation and policy-intent handling |
| `stem_ai/advisory_*` | Provider-neutral advisory packet/export/validation boundary |

## Score Construction

The canonical score path is documented in [SCORING_RATIONALE.md](SCORING_RATIONALE.md). At a high level:

- Stage 1 measures README evidence and hype/responsibility signals
- Stage 2R measures repo-local consistency across docs, package metadata, CI, and tests
- Stage 3 measures code/bio responsibility and integrity-adjacent evidence
- Stage 4 reports replication evidence as a separate lane
- C1-C6 penalties and caps apply bounded deductions or floors

The architecture preserves a strict rule: preview policy simulations must not silently rewrite the authoritative deterministic score.

## Trust Boundaries

### Default deterministic boundary

- local repository only
- no required network access
- no LLM in the scoring loop
- evidence must point to a concrete file, line, pattern, or artifact

### Advisory boundary

- entered only through explicit advisory commands
- packet export, provider call intent, and response validation are separated
- secret handling and claim filters are governed independently of the deterministic score path

### Output boundary

- reports are review aids
- tiers classify observable evidence posture
- reports are not clinical validation, regulatory approval, or deployment certification

## Failure And Fallback Behavior

- missing optional extras reduce output capabilities rather than rewrite the score semantics
- PDF generation depends on the `pdf` extra; JSON/Markdown paths remain available without it
- advisory provider execution is intentionally separate from deterministic scoring
- policy simulation can preview alternate postures without mutating the canonical scoring profile

## Verification Surface

The repository exposes these concrete verification paths:

```bash
pip install -e ".[pdf]"
python -m py_compile stem_ai/cli.py stem_ai/scanner.py stem_ai/render.py stem_ai/app.py
stem --help
python -m stem_ai --help
python -m pytest -q
python -m build
```

## Related Documents

- [README.md](../README.md)
- [CLI_REFERENCE.md](CLI_REFERENCE.md)
- [SCORING_RATIONALE.md](SCORING_RATIONALE.md)
- [DETERMINISTIC_DIAGNOSTICS.md](DETERMINISTIC_DIAGNOSTICS.md)
- [API_CONTRACT.md](API_CONTRACT.md)
- [ADVISORY_RUNTIME.md](ADVISORY_RUNTIME.md)
