# Preprint Draft: STEM-BIO-AI Methodology
## Title: Deterministic Evidence-Surface Auditing for Bio-Medical AI Repositories
### Authors: Yun, Kwansub (flamehaven01)

---
## Abstract
The proliferation of large language models (LLMs) in bio-informatics has led to a surge in "Bio-AI Slop" — repositories that utilize clinical marketing language without underlying technical rigor, data provenance, or safety safeguards. We present **STEM-BIO-AI**, a deterministic framework that audits the "evidence-surface" of a repository without relying on LLM inference. By mapping 40+ observable signals across documentation, source code (AST), and configuration, we define a tiered scoring system (T0-T4) that serves as a **preliminary structural alignment signal** for regulatory frameworks (EU AI Act, FDA SaMD). We demonstrate the efficacy of this approach by identifying critical failure modes in existing Bio-AI projects, including mock-data fallbacks and insecure infrastructure mounts.

---

## 5. Regulatory Alignment
Mapping STEM-BIO-AI scores to EU AI Act High-Risk AI requirements and FDA SaMD pillars. We emphasize that this tool measures the **structural readiness for accountability** rather than empirical clinical performance. A T4 score indicates that the repository contains the necessary infrastructure and governance artifacts required for a formal regulatory audit.
*   **The Problem:** The "Black Box" of AI in medicine is not just the model, but the entire repository lifecycle.
*   **The Gap:** Existing tools focus on code security (SAST) or model performance (benchmarks), but lack an integrated view of *biological responsibility*.
*   **The Solution:** A local-first, zero-LLM scanner that makes the audit trail 100% traceable.

---

## 2. Methodology: The 4 Stages of Evidence
*   **Stage 1: Declarative Surface.** Analysis of README and docs for domain vocabulary and clinical boundaries.
*   **Stage 2R: Cross-Surface Consistency.** Detecting "Stale" documentation or contradictions between claims and config.
*   **Stage 3: Verifiable Integrity.** CI/CD, domain tests, data provenance (IRB), and bias measurement.
*   **Stage 4: Replication Liquidity.** Containers, lockfiles, and artifact references.

---

## 3. Implementation: Deterministic Diagnostics
*   **SMILES-DECEPT:** Detecting chemistry slop via stack-based grammar validation.
*   **MOUNT-AUDIT:** Identifying insecure container configurations for clinical data.
*   **RUN-TRACE:** Taint-tracking of biological tool subprocesses.
*   **SILENT-MOCK:** Detecting library fallbacks to simulated data.

---

## 4. Evaluation and Benchmarking
*   Analysis of 50+ Bio-AI repositories from GitHub.
*   Case studies: `Biomni` (Subprocess/Mock risk), `BioClaw` (Mount risk).
*   Correlation with human expert auditor scores (Ω >= 0.95).

---

## 5. Regulatory Alignment
Mapping STEM-BIO-AI scores to EU AI Act High-Risk AI requirements and FDA SaMD pillars.

---

## 6. Conclusion
STEM-BIO-AI provides a scalable, private, and verifiable first line of defense for the institutional adoption of Bio-Medical AI.
