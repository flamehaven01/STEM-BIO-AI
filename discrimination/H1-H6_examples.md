# STEM-AI Stage 1 Discrimination Examples: H1-H6

These examples are normative. When evaluating H1-H6, consult these before assigning a deduction.
If a phrase falls outside all listed examples, apply the rubric definition strictly.
Do not invent intermediate deduction values.

---

## [H1] Performance superlatives without benchmark comparison (-8 pts)

**TRIGGERS:**
- "autonomously execute a wide range of research tasks" -- broad performance scope without benchmark
- "best-in-class accuracy across 15 benchmarks" -- superlative without cited numeric comparison
- "leading AI platform for research" -- positioning claim without comparative evidence

**DOES NOT TRIGGER:**
- "supports scRNA-seq, GWAS, and protein folding workflows" -- capability listing
- "achieves 0.89 AUROC on ClinVar pathogenicity prediction" -- specific, benchmarked, falsifiable
- "compatible with Scanpy, RDKit, and BLAST+" -- tool integration list

---

## [H2] Unsubstantiated innovation claims (-8 pts)

**TRIGGERS:**
- "dramatically enhance research productivity" -- unquantified transformation
- "revolutionary approach to drug discovery" -- explicit innovation superlative
- "groundbreaking AI-powered analysis" -- unsubstantiated novelty

**DOES NOT TRIGGER:**
- "reduces manual annotation time by approximately 40%" -- quantified, hedged
- "novel architecture combining GNN with attention" -- technical description
- "new approach to molecular docking using diffusion models" -- no superlative

---

## [H3] Fully autonomous framing in clinical context (-10 pts)

**TRIGGERS:**
- "fully automated diagnostic pipeline" -- autonomous + clinical, no human oversight
- "end-to-end patient risk stratification without manual review" -- removes human review
- "zero human oversight required for clinical decision support" -- explicit H3 keyword

**DOES NOT TRIGGER:**
- "automated data preprocessing pipeline" -- not clinical decision context
- "the first comprehensive system for fully automatic scientific discovery" -- NOT clinical
- "assists clinicians in reviewing imaging results" -- human-in-the-loop preserved

**BOUNDARY CASE:**
- "autonomously execute ... rare disease diagnosis, patient gene detection"
  Evaluate whether combined framing implies removal of human oversight in clinical application.
  If ambiguous, do NOT trigger H3. Prefer H1 instead.

---

## [H4] Unverified AGI / human-level capability claims (-10 pts)

**TRIGGERS:**
- "AGI-powered biomedical reasoning"
- "surpasses clinician performance across all benchmarks"
- "human-level diagnostic accuracy"

**DOES NOT TRIGGER:**
- "achieves clinician-comparable accuracy on subset X (see Table 3)" -- qualified
- "approaches human performance on CheXpert" -- hedged, specific benchmark

---

## [H5] Social proof as reliability evidence (-5 pts)

**TRIGGERS:**
- Star History chart embedded in README
- "trusted by 10,000+ researchers worldwide"
- "most downloaded bio-AI package on PyPI"

**DOES NOT TRIGGER:**
- Star count visible on GitHub page (not embedded in README)
- "cite our paper if you use this tool" -- citation request

---

## [H6] External optics as technical credibility (-5 pts)

**TRIGGERS:**
- "backed by $50M Series B from Andreessen Horowitz" -- VC as credibility
- "as featured in Nature and The New York Times" -- press without technical link
- "endorsed by leading pharmaceutical companies" -- endorsement without evidence

**DOES NOT TRIGGER:**
- "developed at Stanford SNAP Lab" -- institutional affiliation (factual)
- "affiliated with MIT CSAIL" -- academic affiliation
- "published at NeurIPS 2025 (see paper link)" -- peer-reviewed with link

**BOUNDARY CASE:**
- "Stanford-developed, production-ready"
  "Stanford-developed" = affiliation (H6 = NO)
  "production-ready" = quality claim without benchmark (evaluate H1)
