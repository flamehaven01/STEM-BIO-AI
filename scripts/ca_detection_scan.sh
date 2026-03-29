#!/usr/bin/env bash
# STEM-AI Clinical Adjacency Detection Scan
# Usage: bash ca_detection_scan.sh /path/to/repo
# Output: detected triggers with severity classification
set -euo pipefail

REPO_PATH="${1:-.}"

print_help() {
  echo "STEM-AI Clinical Adjacency Detection Scan"
  echo ""
  echo "Usage: bash ca_detection_scan.sh [REPO_PATH]"
  echo ""
  echo "  REPO_PATH  Path to local repository clone (default: current directory)"
  echo ""
  echo "Scans import statements, dependencies, and README for clinical"
  echo "adjacency triggers. Classifies as CA-DIRECT / CA-INDIRECT / CA-PLANNED."
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  print_help
  exit 0
fi

if [ ! -d "$REPO_PATH" ]; then
  echo "ERROR: Directory not found: $REPO_PATH"
  exit 1
fi

echo "=== STEM-AI Clinical Adjacency Detection ==="
echo "Target: $REPO_PATH"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

HIGHEST_SEVERITY="none"
TRIGGER_COUNT=0

check_import() {
  local pattern="$1"
  local label="$2"
  local severity="$3"

  FOUND=$(grep -rln "$pattern" --include="*.py" "$REPO_PATH" 2>/dev/null || true)
  if [ -n "$FOUND" ]; then
    echo "  [${severity}] ${label}"
    echo "    Files: $(echo "$FOUND" | tr '\n' ' ')"
    TRIGGER_COUNT=$((TRIGGER_COUNT + 1))
    case "$severity" in
      CA-DIRECT)  HIGHEST_SEVERITY="CA-DIRECT" ;;
      CA-INDIRECT)
        [ "$HIGHEST_SEVERITY" != "CA-DIRECT" ] && HIGHEST_SEVERITY="CA-INDIRECT" ;;
      CA-PLANNED)
        [ "$HIGHEST_SEVERITY" = "none" ] && HIGHEST_SEVERITY="CA-PLANNED" ;;
    esac
  fi
}

check_readme() {
  local pattern="$1"
  local label="$2"
  local severity="$3"

  README_FILES=$(find "$REPO_PATH" -maxdepth 2 -iname "readme*" -o -iname "SKILL.md" 2>/dev/null || true)
  for readme in $README_FILES; do
    if grep -qil "$pattern" "$readme" 2>/dev/null; then
      echo "  [${severity}] ${label} (README: $readme)"
      TRIGGER_COUNT=$((TRIGGER_COUNT + 1))
      case "$severity" in
        CA-DIRECT)  HIGHEST_SEVERITY="CA-DIRECT" ;;
        CA-INDIRECT)
          [ "$HIGHEST_SEVERITY" != "CA-DIRECT" ] && HIGHEST_SEVERITY="CA-INDIRECT" ;;
        CA-PLANNED)
          [ "$HIGHEST_SEVERITY" = "none" ] && HIGHEST_SEVERITY="CA-PLANNED" ;;
      esac
      break
    fi
  done
}

echo "--- CODE_PATH: Import/Dependency Scan ---"

# Medical imaging
check_import "import pydicom\|from pydicom" "pydicom (DICOM imaging)" "CA-INDIRECT"
check_import "import SimpleITK\|from SimpleITK" "SimpleITK (medical imaging)" "CA-INDIRECT"
check_import "import monai\|from monai" "MONAI (medical AI)" "CA-INDIRECT"
check_import "import pathml\|from pathml" "PathML (pathology)" "CA-INDIRECT"

# Drug discovery
check_import "import autodock\|AutoDock\|autodock_vina" "AutoDock Vina (docking)" "CA-INDIRECT"
check_import "import deepchem\|from deepchem" "DeepChem (drug discovery)" "CA-INDIRECT"
check_import "REINVENT\|reinvent" "REINVENT (molecular generation)" "CA-INDIRECT"

# Genomics
check_import "ClinVar\|clinvar" "ClinVar (clinical genomics)" "CA-INDIRECT"
check_import "CPIC\|cpic\|PharmGx\|pharmacogenomic" "Pharmacogenomics (CPIC/PharmGx)" "CA-DIRECT"
check_import "DPYD\|CYP2D6\|CYP2C19\|allele" "Pharmacogene alleles" "CA-DIRECT"
check_import "gnomAD\|gnomad" "gnomAD (population genomics)" "CA-INDIRECT"
check_import "GATK\|gatk" "GATK (diagnostic pipeline)" "CA-INDIRECT"

# Clinical NLP
check_import "import ctakes\|cTAKES" "cTAKES (clinical NLP)" "CA-INDIRECT"
check_import "import medspacy\|from medspacy" "MedSpaCy (clinical NLP)" "CA-INDIRECT"
check_import "ClinicalBERT\|clinicalbert" "ClinicalBERT" "CA-INDIRECT"

# Direct clinical output
check_import "AVOID\|contraindicated\|dosage_adjustment\|treatment_recommendation" "Direct clinical output patterns" "CA-DIRECT"
check_import "patient.*risk.*score\|diagnostic.*classif\|survival.*analysis" "Patient-facing analysis" "CA-DIRECT"

echo ""
echo "--- TEXT_PATH: README Keyword Scan ---"

check_readme "clinical trial" "Clinical trial reference" "CA-INDIRECT"
check_readme "patient data" "Patient data reference" "CA-INDIRECT"
check_readme "FDA clearance\|CE mark\|SaMD" "Regulatory reference" "CA-DIRECT"
check_readme "hospital deployment" "Hospital deployment" "CA-DIRECT"
check_readme "treatment recommendation" "Treatment recommendation" "CA-DIRECT"
check_readme "planned.*clinical\|future.*clinical\|roadmap.*clinical" "Planned clinical capability" "CA-PLANNED"

echo ""
echo "=== Summary ==="
echo "Triggers found: $TRIGGER_COUNT"
echo "Highest severity: $HIGHEST_SEVERITY"
echo ""

if [ "$HIGHEST_SEVERITY" = "none" ]; then
  echo "CLINICAL_ADJACENT: false"
else
  echo "CLINICAL_ADJACENT: true"
  echo "CA_SEVERITY: $HIGHEST_SEVERITY"
fi
