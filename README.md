# STEM BIO-AI

<p align="center">
  <img src="docs/assets/logo.png" alt="STEM BIO-AI logo" width="390">
</p>

<p align="center">
  <b>Deterministic evidence-surface scanner for bio/medical AI repositories.</b><br>
  No LLM. No API key. No model runtime. No secrets sent anywhere.
</p>

<p align="center">
  <a href="https://github.com/flamehaven01/STEM-BIO-AI/actions/workflows/python-package.yml">
    <img src="https://github.com/flamehaven01/STEM-BIO-AI/actions/workflows/python-package.yml/badge.svg" alt="CI">
  </a>
  <a href="CHANGELOG.md">
    <img src="https://img.shields.io/badge/stable-v1.5.6-informational.svg" alt="v1.5.6">
  </a>
  <a href="pyproject.toml">
    <img src="https://img.shields.io/badge/python-3.9%2B-blue.svg" alt="Python 3.9+">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="Apache 2.0">
  </a>
  <a href="https://huggingface.co/spaces/Flamehaven/stem-bio-ai">
    <img src="https://img.shields.io/badge/demo-Hugging%20Face%20Space-yellow.svg" alt="HF Space">
  </a>
</p>

---

## Why STEM BIO-AI

Bio and medical AI repositories vary enormously in evidence quality — from rigorous academic tools to marketing-grade demos that carry clinical language with no data provenance, no reproducibility path, and no clinical-use disclaimer. Manual review is slow and inconsistent.

STEM BIO-AI scans the **observable repository surface** — README, docs, code structure, CI configuration, dependency manifests, changelogs — and maps detected signals to a structured evidence tier (T0–T4). The scan runs in seconds on a local clone, produces machine-readable JSON and PDF reports, and makes every scoring decision traceable to a specific file, line, and pattern.

> A T4 score means strong observable evidence signals. It does not mean the repository is safe for clinical deployment — that requires independent expert validation.

---

## Quick Start

```bash
git clone https://github.com/flamehaven01/STEM-BIO-AI.git
cd STEM-BIO-AI
pip install -e .[pdf]

# 1-page executive dashboard
stem /path/to/bio-ai-repo --level 1 --format all

# 3-page stage analysis
stem /path/to/bio-ai-repo --level 2 --format all

# 5-page full evidence packet with proof trace
stem /path/to/bio-ai-repo --level 3 --format all --explain
```

```bash
# Advisory mode (no provider API call required)
stem /path/to/bio-ai-repo --advisory validate
stem /path/to/bio-ai-repo --advisory packet
stem /path/to/bio-ai-repo --advisory-response provider_advisory.json
```

Clone the target repository first; the CLI operates on local paths only.

---

## Triage Tiers

| Tier | Score | Recommended Action |
|------|------:|-------------------|
| **T0 Rejected** | 0 – 39 | Insufficient evidence — do not rely on without independent expert validation |
| **T1 Quarantine** | 40 – 54 | Exploratory review only — expert validation required before any use |
| **T2 Caution** | 55 – 69 | Research reference and supervised non-clinical technical review only |
| **T3 Supervised** | 70 – 84 | Supervised institutional review candidate |
| **T4 Candidate** | 85 – 100 | Strong evidence posture — clinical deployment still requires independent validation |

Clinical-adjacent repositories without an explicit disclaimer are **hard-capped at T2** (score ≤ 69).
Repositories with unbounded CA-DIRECT claims are **hard-capped at T0** (score ≤ 39).

Tier boundary derivation and calibration gap disclosures: [`docs/SCORING_RATIONALE.md`](docs/SCORING_RATIONALE.md).

---

## Scoring Model

```
Final = (Stage 1 × 0.40) + (Stage 2R × 0.20) + (Stage 3 × 0.40) − C1 Penalty
```

| Stage | Weight | What Is Measured |
|-------|-------:|-----------------|
| **Stage 1** README Evidence | 40% | Bio-domain vocabulary; H1–H6 hype-claim penalties; R1–R5 responsibility signals (limitations, regulatory framing, clinical disclaimer, demographic-bias, reproducibility) |
| **Stage 2R** Repo-Local Consistency | 20% | Vocabulary overlap across README, docs, package metadata, CI, and tests; limitation repetition; contradiction, staleness, and unsupported-workflow deductions |
| **Stage 3** Code/Bio Responsibility | 40% | CI presence; domain test coverage; changelog hygiene (T3); data provenance and IRB/dataset citation (B1); bias/limitation measurement evidence (B2); conflict-of-interest disclosure (B3) |
| **Stage 4** Replication Evidence | Separate lane | Containers; reproducibility targets; dependency locks/pins; dataset and model artifact references; seed, CLI, and citation signals; license/use-scope restrictions |
| **C1–C4** Code Integrity | Penalty / advisory | Hardcoded credentials (C1, −10 pts); dependency pinning (C2); deprecated patient-adjacent paths (C3); fail-open exception handlers (C4) |

Stage 4 is reported as `replication_score` / `replication_tier` and does **not** affect `score.final_score`. Full scoring rationale and calibration gap disclosures are in [`docs/SCORING_RATIONALE.md`](docs/SCORING_RATIONALE.md).

---

## Architecture

```mermaid
flowchart LR
    A[Target repository] --> B[LOCAL_ANALYSIS scanner]
    B --> C[Stage 1\nREADME evidence]
    B --> D[Stage 2R\nRepo-local consistency]
    B --> E[Stage 3\nCode/bio responsibility]
    B --> F[Stage 4\nReplication lane]
    B --> K[C1–C4\nCode integrity]
    C --> G[Weighted evidence score]
    D --> G
    E --> G
    K --> G
    F --> H[replication_score / tier]
    G --> I[JSON result]
    H --> I
    I --> L[Evidence ledger]
    I --> M[Explain trace]
    G --> N[Markdown report]
    G --> O[PDF packet]
```

Core modules: `stem_ai/scanner.py`, `stem_ai/render.py`, `stem_ai/cli.py`, `stem_ai/detectors.py`, `stem_ai/detector_surface.py`, `stem_ai/detector_ast.py`, `stem_ai/detector_stage4.py`, `stem_ai/evidence.py`, `stem_ai/app.py`

---

## Output Artifacts

Each run writes to `--out DIR` (default: `stem_output/`).

| Level | Pages | Audience | Artifacts |
|-------|------:|---------|-----------|
| `--level 1` | 1 | Executive / triage | Score, tier, stage cards, code integrity summary |
| `--level 2` | 3 | Standard audit review | Level 1 + Stage 1/2R/3 breakdown, gap analysis |
| `--level 3` | 5 | Full evidence packet | Level 2 + code integrity deep dive, classification analysis, remediation roadmap |

```
<repo>_experiment_results.json   # machine-readable score + full evidence object
<repo>_report.md                 # human-readable audit report
<repo>_brief_1p.pdf              # Level 1 executive dashboard
<repo>_detailed_3p.pdf           # Level 2 stage analysis
<repo>_detailed_5p.pdf           # Level 3 deep review packet
<repo>_explain.txt               # --explain: file/line/snippet proof trace
```

---

## Report Preview

<p align="center">
  <img src="docs/assets/report-preview/fieldbioinformatics/page-1.png" alt="STEM BIO-AI Level 3 report — page 1" width="760">
</p>

**Sample PDF:** [Download the 5-page Level 3 report](docs/assets/report-preview/fieldbioinformatics/artic-network_fieldbioinformatics_detailed_5p.pdf)

<details>
<summary>View all 5 preview pages</summary>

| Page 1 | Page 2 |
|--------|--------|
| <img src="docs/assets/report-preview/fieldbioinformatics/page-1.png" alt="Page 1"> | <img src="docs/assets/report-preview/fieldbioinformatics/page-2.png" alt="Page 2"> |

| Page 3 | Page 4 |
|--------|--------|
| <img src="docs/assets/report-preview/fieldbioinformatics/page-3.png" alt="Page 3"> | <img src="docs/assets/report-preview/fieldbioinformatics/page-4.png" alt="Page 4"> |

| Page 5 |
|--------|
| <img src="docs/assets/report-preview/fieldbioinformatics/page-5.png" alt="Page 5"> |

</details>

---

## Detection Methods

Every scored item maps to a concrete, inspectable detection method. No inference, no LLM judgment.

<details>
<summary>Full detection table</summary>

| Component | Detection Method |
|-----------|-----------------|
| Stage 1 baseline | Non-zero README present (+60 base) |
| Stage 1 domain signal | Bio-domain keyword regex in README and package metadata |
| Stage 1 hype penalties (H1–H6) | Regex: clinical certainty, regulatory approval, autonomous replacement, breakthrough marketing, universal generalization, perfect accuracy claims |
| Stage 1 responsibility signals (R1–R5) | Regex: limitations section, regulatory framework, clinical disclaimer (CA-severity-weighted), demographic-bias disclosure, reproducibility provisions |
| Stage 2R consistency | Vocabulary set intersection across README/docs/package/tests; limitation repetition; clinical-boundary contradiction, version-staleness, and workflow-support deductions |
| Stage 3 T1 CI | `.github/workflows/` contains at least one file |
| Stage 3 T2 domain tests | `tests/` directory text contains bio-domain vocabulary (regex) |
| Stage 3 T3 changelog | CHANGELOG file presence + bug-fix/patch/security entry detection (3-tier: 0/+5/+15) |
| Stage 3 B1 data provenance | Dependency manifest presence + IRB/dataset-citation language detection (3-tier: 0/+10/+15) |
| Stage 3 B2 bias measurement | Bias/limitations vocabulary + quantitative measurement evidence (subgroup analysis, AUROC, demographic parity) (3-tier: 0/+8/+15) |
| Stage 3 B3 COI/funding | Funding, grant, sponsor, conflict-of-interest language in README/docs/FUNDING.md |
| Stage 4 containers | Dockerfile or compose file present |
| Stage 4 reproducibility target | Makefile with reproduce/eval/benchmark/test targets |
| Stage 4 dependency lock | Environment/lock/requirements file; exact pins or hash evidence |
| Stage 4 artifact references | Dataset/model/checkpoint URLs or checksum files |
| Stage 4 citation/interface | CITATION.cff; argparse CLI entry points (AST) |
| Stage 4 license restriction | Non-commercial, research-only, academic-only, no-clinical-use restrictions in LICENSE/README |
| CA severity | Clinical/diagnostic phrase regex in README, docs, and package metadata |
| C1 credentials | AWS `AKIA*`, OpenAI `sk-*`, GitHub `ghp_*`, `api_key=...` patterns; obvious placeholders excluded from penalty |
| C2 dependency pinning | `==` or hash pin vs. loose `>=`, `~=`, `<`, `>` ranges |
| C3 deprecated paths | Patient-metadata patterns in `deprecated/`, `legacy/`, `archive/` directories |
| C4 fail-open | `except Exception: pass` or `except: pass` in Python source (AST) |

</details>

---

## AI Advisory Contract

The advisory system exports a sanitized, provider-neutral handoff packet and validates provider responses — without making any provider API call.

```bash
stem /path/to/repo --advisory validate          # offline contract check
stem /path/to/repo --advisory packet            # export sanitized input packet
stem /path/to/repo --advisory-response FILE     # validate provider JSON response
```

**Non-negotiable rules (enforced by the validator):**
- Provider output cannot override `score.final_score` or `score.formal_tier`
- Every advisory item must cite exact `finding_id` strings from `allowed_finding_ids`
- Raw repository source text is not included in provider packets
- Responses containing clinical safety, efficacy, regulatory, or medical-advice claims are rejected
- `allowed_finding_ids` is capped at 40 entries per packet

Full contract: [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md)

---

## Web Demo

Live demo: [huggingface.co/spaces/Flamehaven/stem-bio-ai](https://huggingface.co/spaces/Flamehaven/stem-bio-ai)

<p align="center">
  <img src="docs/assets/HF-STEM-BIO_AI.png" alt="STEM BIO-AI Hugging Face Space" width="760">
</p>

The Space runs the same deterministic local scanner on public GitHub repositories. No provider API call is made.

Run locally:

```bash
pip install -e .[demo]
python app.py
```

---

## Repository Structure

```
STEM-BIO-AI/
  stem_ai/              # Core Python package
  docs/                 # API contract, scoring rationale, report previews
  audits/               # Reference benchmark artifacts
  scripts/              # Benchmark and validation scripts
  tests/                # Regression test suite (58 tests)
  app.py                # HuggingFace Spaces / Gradio entry point
  pyproject.toml        # Package metadata and extras
  SKILL.md              # Universal agent skill definition
  CHANGELOG.md          # Version history
```

---

## Agent Skill Install

```bash
# Claude Code
git clone --depth 1 https://github.com/flamehaven01/STEM-BIO-AI.git ~/.claude/skills/stem-bio-ai

# Generic agent frameworks
git clone --depth 1 https://github.com/flamehaven01/STEM-BIO-AI.git ~/.agents/skills/stem-bio-ai
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). High-value areas: rubric discrimination examples, clinical-adjacency trigger refinements, additional bio-domain benchmark repositories, report rendering improvements.

---

## Citation

```bibtex
@software{stem-bio-ai,
  author  = {Yun, Kwansub},
  title   = {STEM BIO-AI: Deterministic Evidence-Surface Scanner for Bio/Medical AI Repositories},
  version = {1.5.6},
  year    = {2026},
  url     = {https://github.com/flamehaven01/STEM-BIO-AI}
}
```

---

## License

Apache 2.0. See [LICENSE](LICENSE).

Maintained by [flamehaven01](https://github.com/flamehaven01)
