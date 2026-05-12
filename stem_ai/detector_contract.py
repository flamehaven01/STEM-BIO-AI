"""Code Contract Detector — CC-1, CC-2, CC-3.

Closes the Layer-2 gap identified in clinical code analysis:
  CC-1  clinical_zero_default   : public function with confidence/threshold param defaulting to 0.0
  CC-2  api_contract            : name claimed in README code block absent from package __all__
  CC-3  shallow_validator       : validate_*/check_* function with len() but no regex structure check

Algorithm lineage (stdlib-only, no slop_detector import):
  CC-2 resolution concept adapted from AI-SLOP-Detector
  python_imports._get_resolvable_modules / _module_exists pattern —
  applied at package __all__ layer rather than module import layer.
"""
from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .detector_utils import add_finding, iter_python_files
from .evidence import EvidenceFinding


# ── constants ───────────────────────────────────────────────────────────────

_CLINICAL_PARAM_RE = re.compile(
    r"(?:^|_)(confidence|threshold|conf_threshold|score_threshold|min_confidence|min_score)(?:_|$)",
    re.I,
)
_README_IMPORT_RE = re.compile(
    r"^(?:from\s+([\w.]+)\s+import\s+([\w,\s*]+)|import\s+([\w.]+))",
    re.M,
)
_VALIDATOR_NAME_RE = re.compile(r"^(validate|check|verify|assert)_", re.I)
_SKIP_DIRS = frozenset({
    ".venv", "venv", "site-packages", "node_modules",
    "__pycache__", ".git", "tests", "test", "docs",
})


# ── helpers ──────────────────────────────────────────────────────────────────

def _collect_candidate_pairs(args: ast.arguments) -> list[tuple[Any, Any]]:
    """Return (arg, default) pairs for all params that carry a default value."""
    pairs: list[tuple[Any, Any]] = []
    offset = len(args.args) - len(args.defaults)
    for i, default in enumerate(args.defaults):
        idx = offset + i
        if idx < len(args.args):
            pairs.append((args.args[idx], default))
    for kw_arg, kw_default in zip(args.kwonlyargs, args.kw_defaults):
        if kw_default is not None:
            pairs.append((kw_arg, kw_default))
    return pairs


def _parse_all_assign(node: ast.Assign) -> set[str]:
    """Extract string literals from an __all__ = [...] assignment node."""
    if not isinstance(node.value, (ast.List, ast.Tuple)):
        return set()
    return {
        elt.value
        for elt in node.value.elts
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
    }


def _flush_code_block(
    block_lines: list[tuple[int, str]],
) -> dict[str, list[int]]:
    """Extract importable names from a single README code block."""
    names: dict[str, list[int]] = defaultdict(list)
    for blineno, bline in block_lines:
        for m in _README_IMPORT_RE.finditer(bline):
            if not m.group(2):
                continue
            for name in re.split(r"[,\s]+", m.group(2).strip()):
                name = name.strip()
                if name and name != "*":
                    names[name].append(blineno)
    return names


# ── CC-1: clinical zero default ─────────────────────────────────────────────

def _detect_clinical_zero_default(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> int:
    """Find public functions where confidence/threshold param defaults to 0 or 0.0."""
    hits = 0
    for path in iter_python_files(target):
        if any(p in path.parts for p in _SKIP_DIRS):
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue

        lines = source.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue

            candidate_pairs = _collect_candidate_pairs(node.args)

            for arg, default in candidate_pairs:
                if not _CLINICAL_PARAM_RE.search(arg.arg):
                    continue
                is_zero = isinstance(default, ast.Constant) and default.value in (0, 0.0)
                if not is_zero:
                    continue
                lineno = getattr(node, "lineno", 0)
                snippet = lines[lineno - 1].strip() if lineno and lineno <= len(lines) else ""
                add_finding(
                    target, findings, counters,
                    detector="CC1_clinical_zero_default",
                    pattern_id="clinical_zero_default_v1",
                    status="detected",
                    severity="warn",
                    path=path,
                    line=lineno,
                    snippet=snippet,
                    match_type="ast",
                    explanation=(
                        f"Public function '{node.name}': parameter '{arg.arg}' "
                        f"defaults to 0 — all predictions pass threshold including near-zero confidence."
                    ),
                )
                hits += 1
    return hits


# ── CC-2: README → __all__ contract ─────────────────────────────────────────
# Algorithm concept adapted from AI-SLOP-Detector python_imports._module_exists:
# instead of resolving top-level module names, we resolve public API names
# from the package __init__.__all__ and compare against README claims.

def _extract_package_all(target: Path) -> frozenset[str]:
    """Parse __all__ from the first-level package __init__.py via AST."""
    names: set[str] = set()
    for candidate in sorted(target.rglob("__init__.py")):
        if any(p in candidate.parts for p in _SKIP_DIRS):
            continue
        try:
            source = candidate.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Assign) and
                    any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets)):
                continue
            names.update(_parse_all_assign(node))
    return frozenset(names)


def _readme_claimed_names(readme: str) -> dict[str, list[int]]:
    """Extract names claimed in README code blocks as importable from this package."""
    names: dict[str, list[int]] = defaultdict(list)
    in_block = False
    block_lines: list[tuple[int, str]] = []
    for lineno, raw in enumerate(readme.splitlines(), 1):
        line = raw.strip()
        if line.startswith("```"):
            if in_block:
                for n, lns in _flush_code_block(block_lines).items():
                    names[n].extend(lns)
                block_lines = []
            in_block = not in_block
        elif in_block:
            block_lines.append((lineno, line))
    return names


def _detect_api_contract(
    target: Path,
    readme: str,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> int:
    """Compare names claimed in README code blocks vs package __all__."""
    package_all = _extract_package_all(target)
    if not package_all:
        return 0

    claimed = _readme_claimed_names(readme)
    hits = 0
    for name, linenos in claimed.items():
        if name in package_all:
            continue
        lineno = linenos[0] if linenos else 0
        add_finding(
            target, findings, counters,
            detector="CC2_api_contract",
            pattern_id="api_contract_v1",
            status="detected",
            severity="warn",
            path=Path("README.md"),
            line=lineno,
            snippet=f"from ... import {name}",
            match_type="readme_vs_all",
            explanation=(
                f"README code block claims '{name}' as importable, "
                f"but it is absent from package __all__ ({len(package_all)} entries)."
            ),
        )
        hits += 1
    return hits


# ── CC-3: shallow validator ──────────────────────────────────────────────────

def _detect_shallow_validator(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> int:
    """Find validate_*/check_* functions that use len() but no regex structure check."""
    hits = 0
    _RE_CALL = re.compile(r"\bre\.(match|search|fullmatch|compile)\b")
    for path in iter_python_files(target):
        if any(p in path.parts for p in _SKIP_DIRS):
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue

        lines = source.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _VALIDATOR_NAME_RE.match(node.name):
                continue

            func_source = ast.get_source_segment(source, node) or ""
            has_len = bool(re.search(r"\blen\s*\(", func_source))
            has_re  = bool(_RE_CALL.search(func_source))
            if not (has_len and not has_re):
                continue

            lineno = getattr(node, "lineno", 0)
            snippet = lines[lineno - 1].strip() if lineno and lineno <= len(lines) else ""
            add_finding(
                target, findings, counters,
                detector="CC3_shallow_validator",
                pattern_id="shallow_validator_v1",
                status="detected",
                severity="warn",
                path=path,
                line=lineno,
                snippet=snippet,
                match_type="ast",
                explanation=(
                    f"Validator '{node.name}' uses len() check but no regex structure validation — "
                    f"may accept structurally invalid values (e.g. wrong group format)."
                ),
            )
            hits += 1
    return hits


# ── public entry point ───────────────────────────────────────────────────────

def collect_contract_findings(
    target: Path,
    readme: str,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> dict[str, Any]:
    """Run CC-1, CC-2, CC-3 and return a summary dict."""
    cc1 = _detect_clinical_zero_default(target, findings, counters)
    cc2 = _detect_api_contract(target, readme, findings, counters)
    cc3 = _detect_shallow_validator(target, findings, counters)
    return {
        "CC1_clinical_zero_default": {"count": cc1, "status": "WARN" if cc1 else "PASS"},
        "CC2_api_contract":          {"count": cc2, "status": "WARN" if cc2 else "PASS"},
        "CC3_shallow_validator":     {"count": cc3, "status": "WARN" if cc3 else "PASS"},
    }
