# STEM-AI -- Sovereign Trust Evaluator for Medical AI Artifacts

A rubric-based trust evaluation framework for open-source bio/medical AI repositories. Works as a universal AI agent skill across 16+ platforms.

```
  ____ _____ _____ __  __      _    ___
 / ___|_   _| ____|  \/  |    / \  |_ _|
 \___ \ | | |  _| | |\/| |   / _ \  | |
  ___) || | | |___| |  | |  / ___ \ | |
 |____/ |_| |_____|_|  |_| /_/   \_\___|
```

## What is STEM-AI?

STEM-AI answers one question about any bio/medical AI repository:

**"Can the people who built this code be trusted in front of a patient's life?"**

It is NOT a code linter. It is a meta-inspection framework that cross-verifies repository artifacts -- README claims, code reality, social media consistency, governance maturity -- to produce a numeric trust score and tier classification.

## Key Features

- **Rubric-based scoring** -- fixed point values, not LLM intuition. Cross-LLM target: same input, any LLM, score within +/-10 points.
- **4 execution modes** -- LOCAL_ANALYSIS (AI CLI), FULL (web tools), SEARCH_ONLY, MANUAL
- **Dual-path evidence** -- TEXT_PATH (interpret documents) + CODE_PATH (measure code). Measurement beats interpretation.
- **3-tier clinical adjacency** -- CA-DIRECT, CA-INDIRECT, CA-PLANNED. Graduated penalties proportional to actual patient risk.
- **Governance overlay** -- Stage 3G evaluates bounded external governance without inflating base trust tier.
- **Audit-layer separation** -- technical audit establishes what the repository actually does; STEM-AI classifies whether the visible artifact surface is sufficient for institutional trust establishment.
- **Code integrity scanning** -- C1-C4 items detect hardcoded credentials, unpinned dependencies, dead clinical paths, fail-open exception handling.
- **Institutional output package** -- Audit Report, Executive Summary, Claim Matrix, Evidence Ledger, Method Appendix.

## Installation

### Universal path (Codex CLI, Gemini CLI, Kiro, Antigravity)

```bash
git clone https://github.com/flamehaven01/STEM-AI-BIO.git ~/.agents/skills/stem-ai
```

### Claude Code

```bash
git clone https://github.com/flamehaven01/STEM-AI-BIO.git ~/.claude/skills/stem-ai
```

### Project-level (any platform)

```bash
cd your-project
git clone https://github.com/flamehaven01/STEM-AI-BIO.git .agents/skills/stem-ai
# or
git clone https://github.com/flamehaven01/STEM-AI-BIO.git .claude/skills/stem-ai
```

### Symlink for multi-platform

```bash
git clone https://github.com/flamehaven01/STEM-AI-BIO.git ~/stem-ai-skill
ln -s ~/stem-ai-skill ~/.claude/skills/stem-ai
ln -s ~/stem-ai-skill ~/.agents/skills/stem-ai
```

## Quick Start

Once installed, tell your AI agent:

```
Audit the repository at https://github.com/example/bio-tool using STEM-AI.
```

Or in LOCAL_ANALYSIS mode:

```
cd /path/to/cloned/repo
Run a STEM-AI LOCAL_ANALYSIS audit on this repository.
```

The skill will automatically:
1. Detect execution mode
2. Run the 3-stage evaluation protocol
3. Generate scored audit report with evidence chains
4. Produce Claim Matrix and Executive Summary

## Relationship to Technical Audit

STEM-AI is not a substitute for technical audit.

- **Technical audit** establishes what a repository actually does by inspecting executable surfaces, workflows, configs, and failure paths.
- **STEM-AI** classifies whether the repository's visible artifact surface is sufficient for trust establishment, supervised pilot consideration, or institutional review.

In practice:

- technical audit is the **fact-extraction layer**
- STEM-AI is the **trust-classification layer**

Where both are available, technical findings should be established first and then scored through STEM-AI.

## Local CLI

STEM-AI now includes a zero-API local CLI for fast repository pre-screening.

Install from the repository root:

```bash
pip install -e .
```

Run a 1-page brief audit:

```bash
stem audit /path/to/bio-ai-repo --mode brief --format all --out stem_output
```

Run a detailed 3-5 page audit:

```bash
stem audit /path/to/bio-ai-repo --mode detailed --pages 5 --format all --out stem_output
```

Shortcut form is also supported:

```bash
stem /path/to/bio-ai-repo
```

Generated outputs:

- `*_experiment_results.json` -- machine-readable score and evidence object
- `*_report.md` -- human-readable audit report
- `*_brief_1p.pdf` -- 1-page executive brief
- `*_detailed_3p.pdf` or `*_detailed_5p.pdf` -- longer review packet

The local CLI is deterministic and does not require an LLM API key. It uses Stage 2R Repo-Local Consistency when external cross-platform evidence is not collected.

## Web Demo

The HuggingFace/Gradio entry point is `app.py`.

Local demo run:

```bash
pip install -e .[demo]
python app.py
```

The demo accepts a public GitHub URL, clones it into a temporary directory, runs the same deterministic local scanner, and returns Markdown, JSON, and PDF outputs.

## Repository Structure

```
stem-ai/
  SKILL.md                          # Entry point (universal agent skill format)
  README.md                         # This file
  pyproject.toml                     # Python CLI package metadata
  app.py                             # HuggingFace/Gradio demo entry point
  LICENSE                           # Apache 2.0
  CHANGELOG.md                      # Version history
  CONTRIBUTING.md                   # Contribution guidelines
  .gitignore                        # Git ignore rules
  .github/
    workflows/
      validate-skill.yml            # CI: validate SKILL.md format
      validate-templates.yml        # CI: validate template completeness
      validate-scripts.yml          # CI: lint and test shell scripts
  memory/                           # MICA v0.2.0 memory layer
    mica.yaml                       # Composition contract (mode: protocol_evolution)
    stem-ai.mica.v1.1.2.json        # Archive: 18 IMMUTABLE rules, lessons, provenance
    stem-ai-playbook.v1.1.2.md      # Session protocol and rubric drift guard
    stem-ai-lessons.v1.1.2.md       # Failure mode history (L-001 through L-010)
  spec/
    STEM-AI_v1.1.2_CORE.md          # Canonical rubric + scoring + execution
    CONSISTENCY_PROTOCOL.md          # Reproducibility verification protocol
    STYLE_GUIDE.md                   # Institutional writing style guide
  discrimination/
    H1-H6_examples.md               # Stage 1 hype detection examples
    T2_examples.md                   # Stage 3 domain test discrimination
    G1-G5_examples.md               # Governance overlay examples
    CA_severity_examples.md          # Clinical adjacency 3-tier examples
    B3_COI_guide.md                  # COI declaration discrimination
  templates/
    audit_report.md                  # Main audit report template
    executive_summary.md             # 1-page institutional summary
    claim_matrix.md                  # Evidence tracking matrix
    evidence_ledger.md               # Artifact provenance ledger
    method_appendix.md               # Methodology documentation
    document_control.md              # Document governance table
    errata_log.md                    # Revision and dispute log
  scripts/
    local_analysis_scan.sh           # C1-C4 code integrity scan
    ca_detection_scan.sh             # Clinical adjacency detection
    snapshot_provenance.sh           # Commit hash + checksum collection
    validate_skill_structure.sh      # Self-validation for skill package
  stem_ai/
    cli.py                           # `stem audit <folder>` entry point
    scanner.py                       # Deterministic LOCAL_ANALYSIS scanner
    render.py                        # Markdown/JSON/PDF output renderer
  audits/
    fieldbioinformatics_v1_1_2/      # Official v1.1.2 LOCAL_ANALYSIS audit output
  references/
    tier_decision_table.md           # T0-T4 operational decision mapping
    risk_taxonomy.md                 # Finding category definitions
    clinical_adjacent_triggers.md    # 60+ clinical tool trigger list
```

## Scoring Overview

| Stage | Weight | What It Evaluates |
|-------|--------|-------------------|
| Stage 1: README Intent | 0.40 | Hype detection, clinical disclaimers, regulatory awareness |
| Stage 2: Cross-Platform / Stage 2R | 0.20 | External consistency; LOCAL_ANALYSIS may use repo-local README/docs/package/workflow/test consistency |
| Stage 3: Code Debt | 0.40 | CI/CD, domain tests, CHANGELOG, data provenance, bias, COI |
| Stage 3G: Governance Overlay | Advisory | Bounded governance uplift (does not change base tier) |
| C1-C4: Code Integrity | Advisory | Credentials, dependencies, dead paths, exception handling |

**Tier boundaries:** T0 (0-39) | T1 (40-54) | T2 (55-69) | T3 (70-84) | T4 (85-100)

## Version History

| Version | Key Changes |
|---------|------------|
| 1.0.0 | Initial 3-stage concept |
| 1.0.1 | Rubric-based scoring, MANUAL fallback |
| 1.0.2 | NASCENT_REPO, CLINICAL_ADJACENT flags |
| 1.0.3 | Weighted formula, T0_HARD_FLOOR, mandatory disclaimer |
| 1.0.4 | Derived context (expiry, trajectory, author domain) |
| 1.0.5 | Governance overlay, H1-H6 discrimination, B3 3-tier |
| 1.0.6 | LOCAL_ANALYSIS, dual-path rubric, CA 3-tier, C1-C4 |
| **1.1.0** | **Universal skill package, multi-file architecture, institutional templates** |
| **1.1.1** | **Canonical version alignment, explicit audit-layer separation, package consistency fixes** |
| **1.1.2** | **MICA v0.2.0 memory layer plus official LOCAL_ANALYSIS report/json audit artifact shape** |

See [CHANGELOG.md](CHANGELOG.md) for full details.

## Release Tags

- Current stable tag: `v1.1.2`
- Tag format: `vMAJOR.MINOR.PATCH`
- Stable install example:

```bash
git clone --branch v1.1.2 --depth 1 https://github.com/flamehaven01/STEM-AI-BIO.git ~/.agents/skills/stem-ai
```

## Empirical Validation

STEM-AI has been applied to 10 leading open-source bio-AI repositories (March 2026):
- 8/10 scored T0 (Trust Not Established)
- 1/10 scored T1 (Quarantine)
- 1/10 scored T2 (Caution)
- 0/10 scored T3 or T4

Results published in "Navigating the Illusion of Competence in Biological AI Agents" (v3.0, March 2026).

## Platform Compatibility

| Platform | Status | Skill Path |
|----------|--------|-----------|
| Claude Code | Supported | `~/.claude/skills/stem-ai/` |
| OpenAI Codex | Supported | `~/.agents/skills/stem-ai/` |
| Gemini CLI | Supported | `~/.agents/skills/stem-ai/` |
| Cursor | Supported | `.agents/skills/stem-ai/` |
| GitHub Copilot | Supported | `.github/skills/stem-ai/` |
| Antigravity IDE | Supported | `~/.agents/skills/stem-ai/` |
| Any MCP client | Via Local Skills MCP | Custom path |

## Limitations

- STEM-AI is an LLM-executed rubric. Scores are not regulatory determinations.
- Cross-LLM consistency target is +/-10 points, not exact reproducibility.
- Governance overlay (Stage 3G) cannot raise the formal base tier.
- C1-C4 code integrity items require LOCAL_ANALYSIS mode (AI CLI + local clone).
- This tool evaluates repository artifacts, not the underlying science.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Adding discrimination examples from live audits
- Proposing rubric modifications (IMMUTABLE rules require version increment)
- Submitting new clinical adjacency triggers
- Improving institutional templates

## License

Apache 2.0. See [LICENSE](LICENSE).

## Citation

```
@software{stem-ai,
  author = {Yun, Kwansub},
  title = {STEM-AI: Sovereign Trust Evaluator for Medical AI Artifacts},
  version = {1.1.2},
  year = {2026},
  url = {https://github.com/flamehaven01/STEM-AI-BIO}
}
```

---

*"Code works. But does the author care about the patient?"*
