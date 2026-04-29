#!/usr/bin/env bash
# STEM BIO-AI Snapshot Provenance Collector
# Usage: bash snapshot_provenance.sh /path/to/repo
# Output: provenance data for audit trail
set -euo pipefail

REPO_PATH="${1:-.}"

print_help() {
  echo "STEM BIO-AI Snapshot Provenance Collector"
  echo ""
  echo "Usage: bash snapshot_provenance.sh [REPO_PATH]"
  echo ""
  echo "  REPO_PATH  Path to local repository clone (default: current directory)"
  echo ""
  echo "Collects: commit hash, branch, README hash, file checksums,"
  echo "access timestamp, remote URL for audit trail evidence."
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  print_help
  exit 0
fi

if [ ! -d "$REPO_PATH" ]; then
  echo "ERROR: Directory not found: $REPO_PATH"
  exit 1
fi

cd "$REPO_PATH"

echo "=== STEM BIO-AI Snapshot Provenance ==="
echo "Collection Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Repo Path: $(pwd)"
echo ""

# Git information
if [ -d ".git" ]; then
  echo "--- Git Provenance ---"
  echo "Current Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
  echo "HEAD Commit: $(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
  echo "HEAD Short: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
  echo "Commit Date: $(git log -1 --format=%ci 2>/dev/null || echo 'unknown')"
  echo "Commit Author: $(git log -1 --format='%an <%ae>' 2>/dev/null || echo 'unknown')"
  echo "Remote URL: $(git remote get-url origin 2>/dev/null || echo 'none')"
  echo "Total Commits: $(git rev-list --count HEAD 2>/dev/null || echo 'unknown')"
  echo "Tags: $(git tag --list 2>/dev/null | tr '\n' ', ' || echo 'none')"
  echo ""
else
  echo "--- Git Provenance ---"
  echo "WARNING: Not a git repository"
  echo ""
fi

# Key file checksums
echo "--- File Checksums (SHA-256) ---"
KEY_FILES="README.md CHANGELOG.md LICENSE requirements.txt pyproject.toml setup.cfg package.json"
for f in $KEY_FILES; do
  if [ -f "$f" ]; then
    HASH=$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1 || echo 'hash_error')
    SIZE=$(wc -c < "$f" 2>/dev/null || echo '0')
    echo "$f: $HASH ($SIZE bytes)"
  fi
done
echo ""

# CI/CD presence
echo "--- CI/CD Artifacts ---"
if [ -d ".github/workflows" ]; then
  echo "GitHub Actions workflows:"
  ls -1 .github/workflows/ 2>/dev/null
else
  echo "No .github/workflows/ directory"
fi

if [ -f ".gitlab-ci.yml" ]; then
  echo "GitLab CI: present"
fi

if [ -f "Jenkinsfile" ]; then
  echo "Jenkins: present"
fi
echo ""

# Test directory
echo "--- Test Infrastructure ---"
TEST_DIRS=$(find . -maxdepth 3 -type d -name "test*" -o -name "spec" 2>/dev/null | head -10)
if [ -n "$TEST_DIRS" ]; then
  echo "Test directories found:"
  echo "$TEST_DIRS"
  TEST_COUNT=$(find . -maxdepth 4 -name "test_*.py" -o -name "*_test.py" -o -name "*.test.js" -o -name "*.spec.ts" 2>/dev/null | wc -l)
  echo "Test file count: $TEST_COUNT"
else
  echo "No test directories found"
fi
echo ""

# License
echo "--- License Surface ---"
if [ -f "LICENSE" ] || [ -f "LICENSE.md" ] || [ -f "LICENSE.txt" ]; then
  LICENSE_FILE=$(ls LICENSE* 2>/dev/null | head -1)
  LICENSE_FIRST=$(head -5 "$LICENSE_FILE" 2>/dev/null | tr '\n' ' ')
  echo "License file: $LICENSE_FILE"
  echo "First line: $LICENSE_FIRST"
else
  echo "WARNING: No LICENSE file found"
fi
echo ""

echo "=== Provenance Collection Complete ==="
