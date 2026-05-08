# CLI Reference

**Version:** 1.6.1
**Status:** Stable

---

## Entry Points

```bash
# Recommended: installed console_scripts entry point
stem <folder> [OPTIONS]
stem audit <folder> [OPTIONS]

# Package-level module
python -m stem_ai <folder> [OPTIONS]

# Direct module (supported since v1.6.1)
python -m stem_ai.cli <folder> [OPTIONS]
```

---

## Options

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--level` | `1`, `2`, `3` | `1` | Report depth: 1=brief 1p, 2=detailed 3p, 3=full 5p |
| `--format` | `json`, `md`, `pdf`, `all` | `all` | Output format |
| `--out` | `DIR` | `stem_output` | Output directory |
| `--explain` | flag | off | Write `{stem}_explain.txt` proof trace |
| `--advisory` | `none`, `validate`, `packet`, `call` | `none` | Advisory mode |
| `--advisory-response` | `FILE` | — | Validate provider-produced JSON response |
| `--tier-gate` | `T0`, `T1`, `T2`, `T3`, `T4` | — | CI gate: exit 1 if audit tier is below threshold |
| `--quiet` | flag | off | Suppress human-readable stdout (artifacts still written) |
| `--version` | flag | — | Print version and exit |

---

## Output

### Default stdout (without `--quiet`)

```
STEM BIO-AI local evidence-surface scan complete
Target:      owner/repo-name
Level:       1  (brief, 1p)

Score:       72 / 100  (T3 Supervised)
  Stage 1:   85 / 100   (README evidence)
  Stage 2R:  60 / 100   (repo consistency)
  Stage 3:   70 / 100   (code + bio)
  Stage 4:   45 / 100   (replication R2)
Clinical:    CA-INDIRECT
Integrity:   WARN (C1, C2)
AI:          not used (deterministic only)

Action items (2 total):
  - C1_hardcoded_credentials: FAIL
  - C2_dependency_pinning: WARN

Output:      /path/to/stem_output
  owner_repo-name_experiment_results.json
  owner_repo-name_report.md
  owner_repo-name_brief_1p.pdf
```

### stdout lines explained

| Line | Source | Since |
|------|--------|-------|
| Score / Tier | `result.score.final_score`, `result.score.formal_tier` | v1.1.3 |
| Stage 1–3 | `result.score.stage_1_readme_intent`, etc. | v1.6.1 |
| Stage 4 | `result.replication_score`, `result.replication_tier` | v1.3.0 (stdout: v1.6.1) |
| Clinical | `result.classification.ca_severity` | v1.1.3 (stdout: v1.6.1) |
| Integrity | `result.code_integrity.C1..C4` | v1.1.3 (stdout: v1.6.1) |
| AI | Advisory mode / provider status | v1.6.1 |
| Action items | `result.notable_risks` | v1.2.0 (stdout: v1.6.1) |

---

## CI/CD Integration

### Tier Gate

Use `--tier-gate` to enforce a minimum tier in CI pipelines:

```bash
# Fail the pipeline if the repository scores below T2
stem /path/to/repo --tier-gate T2 --quiet
echo $?   # 0 = gate passed, 1 = gate failed
```

```bash
# GitHub Actions example
- name: STEM BIO-AI governance gate
  run: |
    pip install stem-ai
    stem ${{ github.workspace }} --tier-gate T3 --format json --quiet
```

```bash
# GitLab CI example
stem_gate:
  script:
    - pip install stem-ai
    - stem . --tier-gate T2 --format json --quiet
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Audit complete; tier gate passed (or no gate set) |
| `1` | Tier gate failed: actual tier is below `--tier-gate` threshold |
| `2` | No subcommand provided (help printed) |

### Machine-Readable Output

For CI scripts that need structured data:

```bash
# JSON only, no stdout noise
stem /path/to/repo --format json --quiet --out results/
# Parse the result
cat results/*_experiment_results.json | jq '.score.final_score'
```

---

## AI Usage Transparency

The CLI always reports AI usage status:

| Mode | stdout |
|------|--------|
| Default (`--advisory none`) | `AI: not used (deterministic only)` |
| `--advisory validate` | `AI: not_run (provider=none)` |
| `--advisory packet` | `AI: packet_ready (provider=none)` |
| `--advisory call` | `AI: <status> (provider=<name>)` |

This is a trust-transparency feature: every scan explicitly declares whether any AI model was consulted.

---

## Relationship to Other Docs

| Document | Scope |
|----------|-------|
| [`API_CONTRACT.md`](API_CONTRACT.md) | JSON result schema, field stability, compatibility policy |
| [`SCORING_RATIONALE.md`](SCORING_RATIONALE.md) | Formula derivation, tier boundaries, calibration gaps |
| [`ADVISORY_SECRET_HANDLING.md`](ADVISORY_SECRET_HANDLING.md) | Provider API key policy, endpoint restrictions |
| [`ADVISORY_RUNTIME.md`](ADVISORY_RUNTIME.md) | `--advisory call` trust boundary |
| This document | CLI flags, stdout format, CI/CD integration |
