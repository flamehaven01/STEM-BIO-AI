#!/usr/bin/env bash
# STEM-AI Local Analysis Scan -- C1-C4 Code Integrity
# Usage: bash local_analysis_scan.sh /path/to/repo
# Output: JSON-formatted findings to stdout
set -euo pipefail

REPO_PATH="${1:-.}"
FINDINGS=""

print_help() {
  echo "STEM-AI Local Analysis Scan (C1-C4 Code Integrity)"
  echo ""
  echo "Usage: bash local_analysis_scan.sh [REPO_PATH]"
  echo ""
  echo "  REPO_PATH  Path to local repository clone (default: current directory)"
  echo ""
  echo "Scans for:"
  echo "  C1: Hardcoded credentials and API keys"
  echo "  C2: Dependency pinning status"
  echo "  C3: Dead code / unreachable clinical paths"
  echo "  C4: Exception handling in clinical output paths"
  echo ""
  echo "Output: structured findings to stdout"
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  print_help
  exit 0
fi

if [ ! -d "$REPO_PATH" ]; then
  echo "ERROR: Directory not found: $REPO_PATH"
  exit 1
fi

echo "=== STEM-AI C1-C4 Code Integrity Scan ==="
echo "Target: $REPO_PATH"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- C1: Hardcoded credentials ---
echo "--- C1: Hardcoded Credentials ---"

# Scan 1: Direct hardcoded patterns
C1_SCAN1=$(grep -rn "AKIA[A-Z0-9]\{16\}\|sk-[a-zA-Z0-9]\{20,\}\|ghp_[a-zA-Z0-9]\{36\}" \
  --include="*.py" --include="*.js" --include="*.ts" "$REPO_PATH" 2>/dev/null || true)

# Scan 2: Env-var fallback patterns
C1_SCAN2=$(grep -rn "environ.*get.*default.*sk-\|environ.*get.*default.*AKIA\|getenv.*sk-" \
  --include="*.py" "$REPO_PATH" 2>/dev/null || true)

# Scan 3: Config file embedded credentials
C1_SCAN3=$(grep -rn "api_key.*:.*['\"][A-Za-z0-9_-]\{20,\}['\"]" \
  --include="*.yaml" --include="*.yml" --include="*.json" --include="*.toml" \
  "$REPO_PATH" 2>/dev/null | grep -v "your_api_key\|placeholder\|example\|<token>" || true)

if [ -z "$C1_SCAN1" ] && [ -z "$C1_SCAN2" ] && [ -z "$C1_SCAN3" ]; then
  echo "C1: PASS -- No hardcoded credentials detected"
else
  echo "C1: FAIL -- Credential patterns found:"
  [ -n "$C1_SCAN1" ] && echo "  Direct: $C1_SCAN1"
  [ -n "$C1_SCAN2" ] && echo "  Env-fallback: $C1_SCAN2"
  [ -n "$C1_SCAN3" ] && echo "  Config: $C1_SCAN3"
fi
echo ""

# --- C2: Dependency pinning ---
echo "--- C2: Dependency Pinning ---"

REQ_FILE=""
for f in requirements.txt requirements-dev.txt pyproject.toml setup.cfg package.json; do
  if [ -f "$REPO_PATH/$f" ]; then
    REQ_FILE="$REPO_PATH/$f"
    break
  fi
done

if [ -z "$REQ_FILE" ]; then
  echo "C2: WARN -- No dependency file found"
else
  TOTAL_DEPS=$(grep -cE "^[a-zA-Z]" "$REQ_FILE" 2>/dev/null || echo 0)
  PINNED_DEPS=$(grep -cE "==" "$REQ_FILE" 2>/dev/null || echo 0)
  UNPINNED_DEPS=$(grep -E "^[a-zA-Z]" "$REQ_FILE" 2>/dev/null | grep -vcE "==\|>=" || echo 0)

  echo "File: $REQ_FILE"
  echo "Total: $TOTAL_DEPS | Pinned (==): $PINNED_DEPS | Unpinned: $UNPINNED_DEPS"

  if [ "$UNPINNED_DEPS" -eq 0 ] 2>/dev/null; then
    echo "C2: PASS -- All dependencies pinned"
  elif [ "$PINNED_DEPS" -gt 0 ] 2>/dev/null; then
    echo "C2: WARN -- Partially pinned"
  else
    echo "C2: FAIL -- No version pinning"
  fi
fi
echo ""

# --- C3: Dead code / unreachable clinical paths ---
echo "--- C3: Dead Clinical Code Paths ---"

STUBS=$(grep -rn "def .*clinical\|def .*diagnos\|def .*patient\|def .*pharma" \
  --include="*.py" "$REPO_PATH" 2>/dev/null || true)

if [ -n "$STUBS" ]; then
  echo "Clinical function signatures found:"
  echo "$STUBS" | while read -r line; do
    FILE=$(echo "$line" | cut -d: -f1)
    LINE_NUM=$(echo "$line" | cut -d: -f2)
    # Check if function body is just 'pass' or 'raise NotImplementedError'
    NEXT_LINE=$(sed -n "$((LINE_NUM + 1))p" "$FILE" 2>/dev/null || true)
    if echo "$NEXT_LINE" | grep -qE "^\s*(pass|raise NotImplementedError|\.\.\.)\s*$"; then
      echo "  C3: WARN -- Stub found: $line"
    fi
  done
else
  echo "C3: PASS -- No dead clinical code paths detected"
fi
echo ""

# --- C4: Exception handling in clinical paths ---
echo "--- C4: Clinical Path Exception Handling ---"

# Look for bare except or broad exception catching in clinical-related files
BROAD_EXCEPT=$(grep -rn "except:\|except Exception:" \
  --include="*.py" "$REPO_PATH" 2>/dev/null | \
  grep -i "clinical\|patient\|diagnos\|pharma\|drug\|allele\|variant" || true)

SILENT_PASS=$(grep -rnA1 "except" --include="*.py" "$REPO_PATH" 2>/dev/null | \
  grep -B1 "pass$" | grep -i "clinical\|patient\|drug" || true)

if [ -z "$BROAD_EXCEPT" ] && [ -z "$SILENT_PASS" ]; then
  echo "C4: PASS -- No fail-open patterns detected in clinical paths"
else
  echo "C4: WARN -- Broad exception handling found in clinical-adjacent code:"
  [ -n "$BROAD_EXCEPT" ] && echo "  $BROAD_EXCEPT"
  [ -n "$SILENT_PASS" ] && echo "  Silent pass after except: $SILENT_PASS"
fi
echo ""

echo "=== Scan Complete ==="
