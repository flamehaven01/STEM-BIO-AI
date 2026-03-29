# STEM-AI Consistency Protocol

**Status:** Draft -- to be populated with empirical data from live audits.

## Purpose

Document the reproducibility characteristics of STEM-AI scoring across different LLMs, sessions, and auditors.

## Required Evidence (target for v1.2.0)

1. **Same-repo re-scoring:** minimum 3 runs of same input on same LLM, score drift recorded
2. **Cross-LLM comparison:** same input on Claude, GPT, Gemini -- score variance measured
3. **Evaluator prompt freeze:** document the exact system prompt used for each audit
4. **Model/version pinning:** record model identifier and version for each audit run
5. **Blind rescoring sample:** independent auditor rescores 3 repos without seeing original scores
6. **Manual override rule:** conditions under which human auditor may override LLM score
7. **Adjudication protocol:** how disagreements between LLM runs are resolved

## Current State (v1.1.1)

- Cross-LLM target: +/-10 points on same input
- Discrimination examples (H1-H6, T2, B3, CA, G1-G5) reduce boundary variance
- Self-Validation Gate (19 checks) prevents structural errors
- No empirical consistency data collected yet

## Data Collection Template

| Run ID | Date | Model | Version | Repo | S1 | S3 | Final | Tier | Notes |
|--------|------|-------|---------|------|----|----|-------|------|-------|
| | | | | | | | | | |
