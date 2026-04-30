# v1.3 Local-10 Benchmark

This directory contains a local dry-run benchmark for STEM BIO-AI v1.3.0 against the existing 10-repository STEM-AI v1.0.4 manual audit control set stored at:

```text
D:\Sanctum\000BIO AI INDUSTRY\STEM-AI_Audit_10Repos_(en).md
```

Boundary:

- This is a local control comparison, not a calibrated 30-repository benchmark.
- The manual control used STEM-AI v1.0.4 MANUAL mode and a different score formula.
- v1.3.0 uses deterministic local evidence-surface scanning with Stage 2R, Stage 4 replication evidence, evidence ledger, and `--explain`.

Headline result:

- Exact tier agreement: 6/10
- Within-one-tier agreement: 9/10
- Major disagreement: 1/10 (`SciAgent-Skills`)

Primary follow-up candidates:

- Improve clinical-adjacency detection for skill catalogs and biomedical tool references.
- Separate test fixture / placeholder credentials from production credential penalties.
- Consider deterministic detection for insecure default configuration in agent platforms.
