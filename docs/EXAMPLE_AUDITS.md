# Example Audits

Version: 1.8.3
Status: Public proof-surface index

---

## Purpose

This project is easier to evaluate through outputs than through claims. This page points to the fastest proof surfaces.

---

## Sample Report Packet

- Report preview pages: [`docs/assets/report-preview/`](assets/report-preview)
- Sample PDF: [`yorkeccak_bio_detailed_8p.pdf`](assets/report-preview/yorkeccak_bio_detailed_8p.pdf)

Use this when you want to inspect the current `1.8.3` full 8-page packet shape, Stage 4 separation, AIRI reasoning, and closeout metadata.

---

## Live Web Demo

- Hugging Face Space: <https://huggingface.co/spaces/Flamehaven/stem-bio-ai>

Notes:

- The Space scans the current default branch of a public GitHub repository at run time.
- Results may differ from commit-pinned benchmark artifacts or older local snapshots.
- The Space is for live triage; commit-pinned benchmark comparisons should be done locally.

---

## Local CLI Output

Run locally for full artifacts:

```bash
stem scan /path/to/bio-ai-repo --level 3 --format all --explain
```

Live generated output belongs under:

- `stem_output/<repo_slug>/`

Historical benchmark and comparison material remains under:

- `audits/`

Primary artifacts:

- `*_experiment_results.json`
- `*_report.md`
- `*.pdf`
- `*_explain.txt`

---

## What To Compare

When comparing two runs, check these fields first:

1. `score.final_score`
2. `score.formal_tier`
3. `classification.ca_severity`
4. `replication_score` / `replication_tier`
5. `code_integrity`
6. `code_contract`
7. `airi_risk_coverage`
8. `stage_1_rubric`, `stage_2r_rubric`, `stage_3_rubric`, `stage_4_rubric`

If one result comes from the Hugging Face Space and the other from a pinned local benchmark, compare only after confirming both are scanning the same repository snapshot.







