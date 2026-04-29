# STEM BIO-AI Stage 3 Discrimination Examples: T2 Domain Tests

T2 awards +15 for DOMAIN-SPECIFIC regression tests. This means tests that verify
biological, chemical, or clinical correctness of outputs -- not infrastructure tests.

---

## QUALIFIES as T2 (+15 pts)

- **test_scrnaseq_clustering.py** -- tests specific input produces expected cell type clusters
- **test_gwas_pipeline.py** -- tests known causal variants correctly identified
- **test_docking_output.py** -- tests AutoDock Vina binding affinity within expected range
- **test_pharmacogenomics.py** -- tests CYP2D6 *4 allele triggers correct CPIC recommendation
- **test_variant_classification.py** -- tests known pathogenic ClinVar variant correctly classified
- **test_smiles_validity.py** -- tests generated SMILES parse correctly in RDKit with valid properties

## DOES NOT QUALIFY as T2 (score at T1 level or +0)

- **test_governance_boundaries.py** -- tests gate mechanics, not biological accuracy
- **test_api_integration.py** -- tests external API calls succeed (infrastructure)
- **test_file_format.py** -- tests output file structure (format, not accuracy)
- **test_skill_validation.py** -- tests SKILL.md sections present (structural)
- pytest with only `assert result is not None` -- null check, not domain verification

## BOUNDARY CASE

- **test_input_validation.py** that checks scRNA-seq h5ad format:
  T2 PARTIAL -- tests domain data format but not output accuracy.
  Award +8 (T1 coverage-unstated level), not +15.

## CODE_PATH Verification (LOCAL_ANALYSIS)

```bash
# Find domain-specific test files
find . -name "test_*.py" -o -name "*_test.py" | \
  xargs grep -l "CYP\|CPIC\|allele\|SMILES\|binding_affinity\|cluster\|GWAS\|variant"

# Distinguish from infrastructure tests
find . -name "test_*.py" | \
  xargs grep -l "governance\|api_key\|file_format\|schema\|connection"
```
