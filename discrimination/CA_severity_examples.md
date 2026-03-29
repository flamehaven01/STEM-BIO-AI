# STEM-AI Clinical Adjacency Severity Examples

3-tier severity classification for CLINICAL_ADJACENT repositories (PATCH-30).

---

## CA-DIRECT (R2 absent: -10, R3 absent: -10)

Tool CURRENTLY outputs patient-facing recommendations, dosage adjustments,
diagnostic classifications, or treatment decisions.

**Examples:**
- PharmGx outputting "AVOID codeine" based on CYP2D6 genotype
- Biomarker classifier outputting patient risk score with severity label
- Survival analysis producing patient stratification for treatment selection
- Drug interaction checker returning contraindication alerts
- Pathology image classifier returning malignancy probability

---

## CA-INDIRECT (R2 absent: -5, R3 absent: -5)

Tool processes clinical data or uses clinical libraries but does NOT
directly output patient-facing decisions.

**Examples:**
- scRNA-seq clustering for cell type annotation (research output)
- GWAS fine-mapping pipeline (variant discovery, not treatment)
- VCF annotation without treatment recommendation
- BLAST+ sequence alignment in genomics context
- Molecular docking (binding affinity scores, not drug recommendation)
- Medical image preprocessing (normalization, not diagnosis)

---

## CA-PLANNED (R2 absent: -0, R3 absent: -0, flag only)

Clinical capability listed in roadmap but NO implementation exists.

**Examples:**
- "ClinVar integration planned for Q3" in README
- Skill stub in routing table with no backing code
- "Future work: clinical trial matching" in roadmap
- Import statement present but function body is `pass`

---

## Upgrade Rules

- CA-PLANNED -> CA-INDIRECT: if CODE_PATH finds actual implemented function
- CA-INDIRECT -> CA-DIRECT: if function output includes treatment/dosage/diagnostic labels
- Multiple triggers at different levels: use HIGHEST severity found
