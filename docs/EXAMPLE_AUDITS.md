# Example Audits

Version: 1.6.7
Status: Public proof-surface index

---

## Purpose

This project is easier to evaluate through outputs than through claims. This page points to the fastest proof surfaces.

---

## Sample Report Packet

- Report preview pages: [`docs/assets/report-preview/fieldbioinformatics/`](assets/report-preview/fieldbioinformatics)
- Sample PDF: [`artic-network_fieldbioinformatics_detailed_5p.pdf`](assets/report-preview/fieldbioinformatics/artic-network_fieldbioinformatics_detailed_5p.pdf)

Use this when you want to inspect the 5-page report shape, stage cards, rubric detail, and disclaimer boundary.

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
6. `stage_1_rubric`, `stage_2r_rubric`, `stage_3_rubric`, `stage_4_rubric`

If one result comes from the Hugging Face Space and the other from a pinned local benchmark, compare only after confirming both are scanning the same repository snapshot.
