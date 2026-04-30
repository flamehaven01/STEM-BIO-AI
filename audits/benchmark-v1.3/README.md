# STEM BIO-AI v1.3 Benchmark Workspace

This directory defines the benchmark artifact contract for v1.3. It is intentionally a template workspace until the 30-repository benchmark is executed and manually reviewed.

Do not claim benchmark alignment from this directory until `benchmark_manifest.json`, `benchmark_results.jsonl`, `tier_alignment_summary.md`, and `false_positive_false_negative_log.md` are populated with commit-pinned repository results.

Expected final layout:

```text
audits/benchmark-v1.3/
  benchmark_manifest.json
  benchmark_results.jsonl
  tier_alignment_summary.md
  false_positive_false_negative_log.md
  repos/
    owner_repo_commit/
      experiment_results.json
      report.md
      explain.txt
```

Selection rules:

- Select repositories by objective criteria before manual tier adjudication.
- Prefer GitHub topics such as `bioinformatics`, `medical-ai`, `clinical-nlp`, `genomics`, `variant-calling`, and `biomedical-ai`.
- Prefer repositories with more than 30 stars.
- Prefer repositories with activity within the last 3 years.
- Prefer Python or Python-majority mixed-language repositories.
- Run STEM first, then record manual verdicts. Manual verdict must not be used to pre-sort repositories into expected tiers.

Release gate:

- v1.3.0 is not benchmark-backed until the final non-template files exist and contain 30 commit-pinned entries.
