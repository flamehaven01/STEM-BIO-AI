from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .evidence import EvidenceFinding
from .detector_utils import add_finding, iter_python_files, read_text, source_line


MAX_AST_FILES = 500
MAX_AST_FILE_SIZE_BYTES = 512_000


@dataclass(frozen=True)
class AstVisitContext:
    target: Path
    path: Path
    findings: list[EvidenceFinding]
    counters: dict[tuple[str, str], int]
    lines: list[str]


def collect_ast_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    max_ast_files: int = MAX_AST_FILES,
    max_ast_file_size_bytes: int = MAX_AST_FILE_SIZE_BYTES,
) -> dict[str, Any]:
    py_files = list(iter_python_files(target))
    selected_files = py_files[:max_ast_files]
    file_limit_exceeded = len(py_files) > max_ast_files
    if file_limit_exceeded:
        add_finding(
            target,
            findings,
            counters,
            detector="AST_file_limit",
            pattern_id="ast_file_limit_v1",
            status="not_applicable",
            severity="info",
            path=Path("."),
            line=0,
            snippet="",
            match_type="limit",
            explanation="Python file count exceeds AST analysis limit; deterministic prefix subset analyzed.",
            metadata={"file_count": len(py_files), "max_ast_files": max_ast_files, "reason": "file_limit_exceeded"},
        )

    summary: dict[str, Any] = {
        "files_total": len(py_files),
        "files_considered": len(selected_files),
        "files_parsed": 0,
        "files_skipped_size": 0,
        "syntax_errors": 0,
        "file_limit_exceeded": file_limit_exceeded,
        "test_functions": 0,
        "assertion_tests": 0,
        "public_functions": 0,
        "docstring_functions": 0,
        "annotated_functions": 0,
        "seed_settings": 0,
        "argparse_cli": False,
        "portable_model_loading": 0,
        "fail_open_handlers": 0,
    }

    for path in selected_files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > max_ast_file_size_bytes:
            summary["files_skipped_size"] += 1
            add_finding(
                target,
                findings,
                counters,
                detector="AST_file_size_limit",
                pattern_id="ast_file_size_limit_v1",
                status="not_applicable",
                severity="info",
                path=path,
                line=0,
                snippet="",
                match_type="limit",
                explanation="Python file skipped because it exceeds AST size limit.",
                metadata={"file_size_bytes": size, "max_file_size_bytes": max_ast_file_size_bytes, "reason": "file_size_limit_exceeded"},
            )
            continue
        text = read_text(path)
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            summary["syntax_errors"] += 1
            add_finding(
                target,
                findings,
                counters,
                detector="AST_syntax_error",
                pattern_id="ast_parse_v1",
                status="error",
                severity="warn",
                path=path,
                line=exc.lineno or 0,
                snippet=exc.text or "",
                match_type="ast",
                explanation="Python file could not be parsed by stdlib ast.",
                metadata={"reason": "syntax_error"},
            )
            continue
        summary["files_parsed"] += 1
        _inspect_ast_tree(target, path, tree, text, findings, counters, summary)

    if summary["public_functions"]:
        summary["docstring_coverage"] = round(summary["docstring_functions"] / summary["public_functions"], 4)
        summary["type_annotation_coverage"] = round(summary["annotated_functions"] / summary["public_functions"], 4)
    else:
        summary["docstring_coverage"] = None
        summary["type_annotation_coverage"] = None
    return summary


def _inspect_ast_tree(
    target: Path,
    path: Path,
    tree: ast.AST,
    text: str,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    summary: dict[str, Any],
) -> None:
    lines = text.splitlines()
    ctx = AstVisitContext(target, path, findings, counters, lines)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _visit_function_node(node, summary, ctx)
        _visit_call_node(node, summary, ctx)
        if isinstance(node, ast.ExceptHandler) and _is_fail_open_handler(node):
            summary["fail_open_handlers"] += 1
            add_finding(ctx.target, ctx.findings, ctx.counters, "AST_fail_open_precision",
                        "ast_fail_open_v1", "detected", "warn", ctx.path,
                        getattr(node, "lineno", 0),
                        source_line(ctx.lines, getattr(node, "lineno", 0)), "ast",
                        "Fail-open exception handler detected by AST.")


def _visit_function_node(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    summary: dict[str, Any],
    ctx: AstVisitContext,
) -> None:
    if not node.name.startswith("_"):
        summary["public_functions"] += 1
        if ast.get_docstring(node):
            summary["docstring_functions"] += 1
        if _function_has_annotations(node):
            summary["annotated_functions"] += 1
    if node.name.startswith("test_"):
        summary["test_functions"] += 1
        has_assert = any(isinstance(c, ast.Assert) or _is_assert_call(c) for c in ast.walk(node))
        if has_assert:
            summary["assertion_tests"] += 1
            add_finding(ctx.target, ctx.findings, ctx.counters, "AST_assertion_tests",
                        "ast_assertion_test_v1", "detected", "info", ctx.path,
                        getattr(node, "lineno", 0),
                        source_line(ctx.lines, getattr(node, "lineno", 0)),
                        "ast", "Test function with assertion detected.",
                        {"function": node.name})


def _visit_call_node(node: ast.AST, summary: dict[str, Any], ctx: AstVisitContext) -> None:
    lineno = getattr(node, "lineno", 0)
    snippet = source_line(ctx.lines, lineno)
    if _is_seed_call(node):
        summary["seed_settings"] += 1
        add_finding(ctx.target, ctx.findings, ctx.counters, "AST_seed_setting", "ast_seed_setting_v1",
                    "detected", "info", ctx.path, lineno, snippet, "ast",
                    "Deterministic random seed setting call detected.")
    if _is_argparse_constructor(node):
        summary["argparse_cli"] = True
        add_finding(ctx.target, ctx.findings, ctx.counters, "AST_argparse_cli", "ast_argparse_cli_v1",
                    "detected", "info", ctx.path, lineno, snippet, "ast",
                    "argparse CLI interface detected.")
    if _is_portable_torch_load(node):
        summary["portable_model_loading"] += 1
        add_finding(ctx.target, ctx.findings, ctx.counters, "AST_portable_model_loading",
                    "ast_torch_load_map_location_v1", "detected", "info", ctx.path, lineno,
                    snippet, "ast", "torch.load call includes map_location.")


def _function_has_annotations(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    if node.args.vararg is not None:
        args.append(node.args.vararg)
    if node.args.kwarg is not None:
        args.append(node.args.kwarg)
    return any(arg.annotation is not None for arg in args) or node.returns is not None


def _is_assert_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    name = _call_name(node.func)
    last_part = name.rsplit(".", 1)[-1]
    return last_part.startswith("assert") or name == "pytest.raises"


def _is_seed_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    return _call_name(node.func) in {"random.seed", "np.random.seed", "numpy.random.seed", "torch.manual_seed"}


def _is_argparse_constructor(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _call_name(node.func) in {"argparse.ArgumentParser", "ArgumentParser"}


def _is_portable_torch_load(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or _call_name(node.func) != "torch.load":
        return False
    return any(keyword.arg == "map_location" for keyword in node.keywords)


def _is_fail_open_handler(node: ast.ExceptHandler) -> bool:
    if not node.body:
        return False
    for child in node.body:
        if isinstance(child, ast.Pass):
            return True
        if isinstance(child, ast.Return) and isinstance(child.value, ast.Constant) and child.value.value is True:
            return True
    return False


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""
