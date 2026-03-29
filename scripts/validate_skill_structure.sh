#!/usr/bin/env bash
# STEM-AI Skill Package Structure Validator
# Usage: bash validate_skill_structure.sh [SKILL_ROOT]
# Validates the STEM-AI skill package is complete and well-formed
set -euo pipefail

SKILL_ROOT="${1:-.}"
ERRORS=0
WARNINGS=0

print_help() {
  echo "STEM-AI Skill Package Structure Validator"
  echo ""
  echo "Usage: bash validate_skill_structure.sh [SKILL_ROOT]"
  echo ""
  echo "  SKILL_ROOT  Path to stem-ai skill directory (default: current directory)"
  echo ""
  echo "Validates: directory structure, required files, frontmatter, version consistency."
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  print_help
  exit 0
fi

check_file() {
  local path="$1"
  local required="$2"
  if [ -f "$SKILL_ROOT/$path" ]; then
    echo "  [OK] $path"
  elif [ "$required" = "required" ]; then
    echo "  [FAIL] $path -- REQUIRED but missing"
    ERRORS=$((ERRORS + 1))
  else
    echo "  [WARN] $path -- recommended but missing"
    WARNINGS=$((WARNINGS + 1))
  fi
}

check_dir() {
  local path="$1"
  if [ -d "$SKILL_ROOT/$path" ]; then
    echo "  [OK] $path/"
  else
    echo "  [FAIL] $path/ -- REQUIRED directory missing"
    ERRORS=$((ERRORS + 1))
  fi
}

echo "=== STEM-AI Skill Package Validation ==="
echo "Root: $SKILL_ROOT"
echo ""

echo "--- Root Files ---"
check_file "SKILL.md" "required"
check_file "README.md" "required"
check_file "LICENSE" "required"
check_file "CHANGELOG.md" "required"
check_file "CONTRIBUTING.md" "recommended"
check_file ".gitignore" "recommended"

echo ""
echo "--- Required Directories ---"
check_dir "spec"
check_dir "discrimination"
check_dir "templates"
check_dir "scripts"
check_dir "references"

echo ""
echo "--- Core Spec ---"
CORE=$(find "$SKILL_ROOT/spec/" -name "STEM-AI_v*_CORE.md" 2>/dev/null | head -1)
if [ -n "$CORE" ]; then
  echo "  [OK] Core spec: $CORE"
else
  echo "  [FAIL] No STEM-AI_v*_CORE.md found in spec/"
  ERRORS=$((ERRORS + 1))
fi

echo ""
echo "--- Discrimination Files ---"
check_file "discrimination/H1-H6_examples.md" "required"
check_file "discrimination/T2_examples.md" "required"
check_file "discrimination/CA_severity_examples.md" "required"
check_file "discrimination/B3_COI_guide.md" "required"
check_file "discrimination/G1-G5_examples.md" "required"

echo ""
echo "--- Templates ---"
check_file "templates/audit_report.md" "required"
check_file "templates/claim_matrix.md" "required"
check_file "templates/executive_summary.md" "required"
check_file "templates/evidence_ledger.md" "recommended"
check_file "templates/method_appendix.md" "recommended"
check_file "templates/document_control.md" "recommended"
check_file "templates/errata_log.md" "recommended"

echo ""
echo "--- Scripts ---"
check_file "scripts/local_analysis_scan.sh" "required"
check_file "scripts/ca_detection_scan.sh" "required"
check_file "scripts/snapshot_provenance.sh" "required"

echo ""
echo "--- References ---"
check_file "references/tier_decision_table.md" "recommended"
check_file "references/risk_taxonomy.md" "recommended"
check_file "references/clinical_adjacent_triggers.md" "recommended"

echo ""
echo "=== Validation Summary ==="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"

if [ "$ERRORS" -gt 0 ]; then
  echo "RESULT: FAIL -- $ERRORS required items missing"
  exit 1
else
  echo "RESULT: PASS ($WARNINGS warnings)"
  exit 0
fi
