# CLI Reference

**Version:** 1.8.3
**Status:** Stable

---

## Command Model

The 1.8.3 CLI is organized around workflows instead of one long option string, exposes named calibration profiles directly, and adds auditable researcher-intent derive/simulate surfaces.

```bash
stem <folder> [OPTIONS]                  # shortcut for `stem scan <folder>`
stem scan <folder> [OPTIONS]             # report generation
stem gate <folder> --min-tier T2         # CI/CD gate
stem advisory validate <folder>          # offline advisory validation
stem advisory packet <folder>            # provider-neutral packet export
stem advisory call <folder>              # explicit provider-call workflow
stem advisory check-response <folder> --response FILE
stem policy list                         # available calibration profiles
stem policy explain <name>               # inspect one calibration profile
stem policy derive [INTENT OPTIONS]      # translate researcher intent
stem policy simulate <folder> [INTENT OPTIONS]
stem policy simulate <folder> --profile-file PROFILE.json
```

Backward compatibility remains in place:

```bash
stem audit <folder> ...
stem <folder> --tier-gate T2 --quiet
stem <folder> --advisory packet
stem <folder> --advisory-response provider_advisory.json
```

---

## Picking The Right Command

| Goal | Recommended command |
|------|---------------------|
| Get the normal scan outputs | `stem scan <folder>` |
| Use the fastest default path | `stem <folder>` |
| Fail CI if the repo is too weak | `stem gate <folder> --min-tier T2` |
| Export a provider-neutral handoff packet | `stem advisory packet <folder>` |
| Validate an external provider response | `stem advisory check-response <folder> --response FILE` |

---

## Shared Options

These options work across `scan`, `gate`, and `advisory` workflows unless otherwise noted.

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `--level` | `1`, `2`, `3` | `3` | Report depth: 1=brief 1p (legacy), 2=standard review 5p, 3=full packet 7p |
| `--format` | `json`, `md`, `pdf`, `all` | command-specific | Artifact format to write |
| `--out`, `--output` | `DIR` | `stem_output` | Output directory |
| `--policy` | `NAME` | `default` | Named calibration profile to surface in the scan result |
| `--explain` | flag | off | Write `{stem}_explain.txt` proof trace |
| `--summary` | `full`, `compact`, `off` | command-specific | stdout summary mode |
| `--quiet` | flag | off | Alias for `--summary off` |
| `--version` | flag | — | Print version and exit |

### Default behavior by workflow

| Command | Default `--format` | Default `--summary` |
|---------|--------------------|---------------------|
| `scan` | `all` | `full` |
| `gate` | `json` | `compact` |
| `advisory validate` | `json` | `compact` |
| `advisory packet` | `json` | `compact` |
| `advisory call` | `json` | `compact` |
| `advisory check-response` | `json` | `compact` |

---

## Scan Workflow

Use `scan` when you want the normal report artifacts.

```bash
stem scan /path/to/repo
stem scan /path/to/repo --level 3 --format all --explain
```

The shorthand remains:

```bash
stem /path/to/repo
```

Policy selection remains mirror-only in scans in `1.8.3`: the chosen profile is surfaced in outputs and summaries, and `policy derive` / `policy simulate` preview governed posture changes without turning those deltas into authoritative scan behavior.

Layer 2 AST contract detectors (`CC1` / `CC2` / `CC3`) run during normal scans
and surface through:

- `code_contract` in JSON results
- the "Code Integrity & Contract" section in HTML reports
- `notable_risks` / evidence-ledger findings when triggered

## Policy Intent Workflows

`stem policy derive` applies the documented 1-5 translation rule table:

```bash
stem policy derive \
  --clinical-strictness 4 \
  --code-integrity-priority 3 \
  --reproducibility-priority 2 \
  --structured-limitations-requirement 3
```

`stem policy simulate` runs the deterministic scan, then shows a baseline-vs-preview outcome:

```bash
stem policy simulate /path/to/repo \
  --clinical-strictness 4 \
  --code-integrity-priority 3 \
  --reproducibility-priority 2 \
  --structured-limitations-requirement 3
```

For domain experimentation without registering a new named profile, `simulate` can also load a local profile file:

```bash
stem policy simulate /path/to/repo \
  --profile-file policy/drafts/scoring_profile.reproducibility_first.v1.json
```

In this mode, the profile file must remain schema-valid and `mirror_only`. The file is used for preview only and is not added to the packaged named-profile set.

Current `1.8.3` rule scope is intentionally narrow:

- strong clinical strictness maps to `strict_clinical_adjacency`
- balanced `2..3` answers keep `default`
- reproducibility-heavy postures still fall to `preview_only`
- all other non-default postures fall to `preview_only` bounded deltas rather than pretending a release-grade named profile already exists

Compatibility flags still work on `scan`:

| Flag | Description |
|------|-------------|
| `--advisory {none,validate,packet,call}` | Legacy inline advisory path; prefer `stem advisory ...` |
| `--advisory-response FILE` | Legacy provider-response validation path; prefer `stem advisory check-response ... --response FILE` |
| `--tier-gate T0..T4` | Legacy inline gate path; prefer `stem gate ... --min-tier ...` |

---

## Gate Workflow

Use `gate` when the command is part of CI/CD and the tier threshold matters more than human-readable output.

```bash
stem gate /path/to/repo --min-tier T2
stem gate /path/to/repo --min-tier T3 --summary off --output results
```

Exit codes:

| Code | Meaning |
|------|---------|
| `0` | Audit complete and gate passed |
| `1` | Gate failed: actual tier is below `--min-tier` |
| `2` | Invalid CLI invocation / help path |

---

## Advisory Workflow

Use `advisory` when you want a clean boundary between deterministic scoring and downstream model review.

### Validate

```bash
stem advisory validate /path/to/repo
```

Runs the deterministic scan and attaches offline advisory-validation metadata. No provider API call is made.

### Packet

```bash
stem advisory packet /path/to/repo --output advisory_out
```

Exports a sanitized, provider-neutral advisory packet with allowlisted `finding_id` citations.

### Call

```bash
stem advisory call /path/to/repo
```

Enters the explicit provider-call boundary. This is the only workflow that is intended to cross the deterministic-only line.

### Check Response

```bash
stem advisory check-response /path/to/repo --response provider_advisory.json
```

Validates a provider-produced JSON response against the evidence ledger with no network call.

---

## stdout Summary Modes

### `--summary full`

Best for local review. Shows:
- workflow
- target
- stage 1-4 breakdown
- clinical adjacency / caps
- integrity warnings
- bio diagnostics
- regulatory review flag
- AI usage status
- top action items
- output file list

### `--summary compact`

Best for CI logs and quick checks. Shows only:
- workflow
- target
- final tier and score
- clinical cap / T0 floor when applicable
- gate verdict when applicable
- artifact count and output directory

### `--summary off`

Writes artifacts only. Equivalent to `--quiet`.

---

## Output Artifacts

| Pattern | Meaning |
|---------|---------|
| `<repo>_experiment_results.json` | Machine-readable result object |
| `<repo>_report.md` | Human-readable Markdown report |
| `<repo>_brief_1p.pdf` | Level 1 brief report (legacy quick brief) |
| `<repo>_detailed_5p.pdf` | Level 2 standard review packet |
| `<repo>_detailed_7p.pdf` | Level 3 full packet |
| `<repo>_explain.txt` | Proof trace from `--explain` |

---

## CI/CD Examples

### GitHub Actions

```yaml
- name: STEM BIO-AI governance gate
  run: |
    pip install stem-ai
    stem gate ${{ github.workspace }} --min-tier T3 --summary off --output results
```

### GitLab CI

```yaml
stem_gate:
  script:
    - pip install stem-ai
    - stem gate . --min-tier T2 --summary off --output results
```

### Parse the JSON result

```bash
stem gate /path/to/repo --min-tier T2 --summary off --output results
cat results/*_experiment_results.json | jq '.score.final_score'
```

---

## AI Usage Transparency

Every workflow declares whether AI was used.

| Workflow | Typical stdout |
|----------|----------------|
| `scan` / `gate` | `AI: not used (deterministic only)` |
| `advisory validate` | `AI: not_run (provider=none)` |
| `advisory packet` | `AI: packet_ready (provider=none)` |
| `advisory call` | `AI: <status> (provider=<name>)` |
| `advisory check-response` | `AI: valid|invalid|error (provider=<name>)` |

This is a trust-transparency feature, not a marketing line.

---

## Relationship To Other Docs

| Document | Scope |
|----------|-------|
| [`API_CONTRACT.md`](API_CONTRACT.md) | JSON result schema, field stability, compatibility policy |
| [`SCORING_RATIONALE.md`](SCORING_RATIONALE.md) | Formula derivation, tier boundaries, calibration gaps |
| [`ADVISORY_SECRET_HANDLING.md`](ADVISORY_SECRET_HANDLING.md) | Provider API key policy, endpoint restrictions |
| [`ADVISORY_RUNTIME.md`](ADVISORY_RUNTIME.md) | `advisory call` runtime boundary |
| This document | Human CLI workflows, flags, defaults, summary modes, CI patterns |







