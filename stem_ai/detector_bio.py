from __future__ import annotations

import ast
import re
from pathlib import Path

from .detector_utils import add_finding, is_fixture_like_path, iter_code_files, iter_python_files, read_text, source_line
from .evidence import EvidenceFinding


SMILES_ALLOWED = re.compile(r"^[A-Za-z0-9@+\-\[\]\(\)=#$%\\/\.]+$")
SMILES_PARSER_CALLS = {"MolFromSmiles", "Chem.MolFromSmiles", "dm.to_mol", "to_mol"}
SMILES_CONTEXT_TOKENS = ("smiles", "smarts", "molecule", "mol", "ligand", "compound", "substrate", "chem")
MOCK_FLAG_NAMES = {"USE_MOCK", "DEMO_MODE", "SIMULATE_DATA", "SIMULATED_DATA", "MOCK_MODE"}
MOCK_NAME_TOKENS = ("mock", "fake", "dummy", "simulat", "synthetic", "demo")
BIO_IMPORT_MODULES = ("rdkit", "Bio", "biopython", "scanpy", "anndata", "FlowCytometryTools", "pysam")
TRACE_MANIFEST_NAMES = {
    "manifest.json",
    "checksums.txt",
    "model_hashes.yaml",
    "model_hashes.yml",
    "audit_log_schema.json",
    "event_log_schema.yaml",
    "event_log_schema.yml",
}
TRACE_KEYWORDS = re.compile(
    r"\b(decision_event|override_event|model_version|dataset_hash|operator_id|timestamp|input_hash|output_hash)\b",
    re.I,
)
TRACE_SCAN_SUFFIXES = {".json", ".yaml", ".yml", ".toml", ".md", ".txt"}
TRACE_FILE_HINT = re.compile(r"(trace|audit|event|log|manifest|checksum|hash|schema|override|decision)", re.I)
BIO_TOOL_NAMES = {"blast", "blastn", "blastp", "samtools", "bwa", "bcftools", "bedtools", "minimap2"}
TAINT_NAME_TOKENS = ("query", "input", "sample", "path", "request", "user", "fastq", "bam", "vcf")


def collect_bio_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> None:
    code_paths = list(iter_code_files(target, max_files=240))
    _collect_smiles_surface_findings(target, findings, counters, code_paths)
    _collect_smiles_parser_guard_findings(target, findings, counters, code_paths)
    _collect_silent_mock_findings(target, findings, counters, code_paths)
    _collect_trace_manifest_findings(target, findings, counters)
    _collect_run_trace_findings(target, findings, counters, code_paths)


def _collect_smiles_surface_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    paths: list[Path],
) -> None:
    detected = False
    for path in paths:
        if path.suffix.lower() != ".py" or is_fixture_like_path(path):
            continue
        text = read_text(path)
        if not text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        _annotate_parents(tree)
        lines = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            value = node.value.strip()
            if not _looks_like_smiles(value):
                continue
            if not _smiles_context_permits(node, value):
                continue
            issues = _smiles_issues(value)
            if not issues:
                continue
            detected = True
            add_finding(
                target,
                findings,
                counters,
                "BIO_smiles_surface_integrity",
                "bio_smiles_surface_v1",
                "detected",
                "warn",
                path,
                getattr(node, "lineno", 0),
                source_line(lines, getattr(node, "lineno", 0)),
                "ast",
                "Suspicious or malformed SMILES-like string detected by conservative surface checks.",
                {"smiles_text": value, "issues": issues},
            )
    if not detected:
        add_finding(
            target,
            findings,
            counters,
            "BIO_smiles_surface_integrity",
            "bio_smiles_surface_v1",
            "not_detected",
            "info",
            Path("."),
            0,
            "",
            "ast",
            "No malformed or suspicious SMILES-like strings detected by conservative surface checks.",
        )


def _collect_smiles_parser_guard_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    paths: list[Path],
) -> None:
    detected = False
    for path in paths:
        if path.suffix.lower() != ".py" or is_fixture_like_path(path):
            continue
        text = read_text(path)
        if not text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        _annotate_parents(tree)
        lines = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target_node = node.targets[0]
            if not isinstance(target_node, ast.Name):
                continue
            parser_call = _call_name(node.value)
            if parser_call not in SMILES_PARSER_CALLS:
                continue
            if _guarded_against_none(node, target_node.id):
                continue
            detected = True
            add_finding(
                target,
                findings,
                counters,
                "BIO_smiles_parser_guard",
                "bio_smiles_parser_guard_v1",
                "detected",
                "warn",
                path,
                getattr(node, "lineno", 0),
                source_line(lines, getattr(node, "lineno", 0)),
                "ast",
                "SMILES parser result is used without an explicit None/invalid guard.",
                {"variable": target_node.id, "parser_call": parser_call},
            )
    if not detected:
        add_finding(
            target,
            findings,
            counters,
            "BIO_smiles_parser_guard",
            "bio_smiles_parser_guard_v1",
            "not_detected",
            "info",
            Path("."),
            0,
            "",
            "ast",
            "No missing None/invalid guards detected after SMILES parser calls.",
        )


def _collect_silent_mock_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    paths: list[Path],
) -> None:
    detected = False
    not_applicable = False
    for path in paths:
        if path.suffix.lower() != ".py" or is_fixture_like_path(path):
            continue
        text = read_text(path)
        if not text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        _annotate_parents(tree)
        lines = text.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                reason = _import_failure_sets_mock_flag(node)
                if reason:
                    detected = True
                    add_finding(
                        target,
                        findings,
                        counters,
                        "BIO_silent_mock_fallback",
                        "bio_silent_mock_v1",
                        "detected",
                        "warn",
                        path,
                        getattr(node, "lineno", 0),
                        source_line(lines, getattr(node, "lineno", 0)),
                        "ast",
                        "Silent mock or simulated-data fallback detected in a biological dependency path.",
                        {"reason": reason},
                    )
            if isinstance(node, ast.If):
                if _is_explicit_demo_mode_branch(node):
                    not_applicable = True
                    add_finding(
                        target,
                        findings,
                        counters,
                        "BIO_silent_mock_fallback",
                        "bio_silent_mock_v1",
                        "not_applicable",
                        "info",
                        path,
                        getattr(node, "lineno", 0),
                        source_line(lines, getattr(node, "lineno", 0)),
                        "ast",
                        "Explicit demo or simulated-data branch detected; treated as disclosed non-production behavior.",
                        {"reason": "explicit_demo_mode_branch"},
                    )
    if not detected and not not_applicable:
        add_finding(
            target,
            findings,
            counters,
            "BIO_silent_mock_fallback",
            "bio_silent_mock_v1",
            "not_detected",
            "info",
            Path("."),
            0,
            "",
            "ast",
            "No silent mock or simulated-data fallback patterns detected in production code paths.",
        )


def _collect_trace_manifest_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> None:
    detected = False
    for name in sorted(TRACE_MANIFEST_NAMES):
        path = target / name
        if not path.is_file():
            continue
        detected = True
        add_finding(
            target,
            findings,
            counters,
            "BIO_trace_manifest",
            "bio_trace_manifest_file_v1",
            "detected",
            "info",
            path,
            0,
            "",
            "file_presence",
            "Traceability manifest or audit-log schema file detected.",
            {"file_name": name},
        )
        text = read_text(path)
        lines = text.splitlines()
        for line_number, line in enumerate(lines, start=1):
            match = TRACE_KEYWORDS.search(line)
            if not match:
                continue
            add_finding(
                target,
                findings,
                counters,
                "BIO_trace_manifest",
                "bio_trace_manifest_keyword_v1",
                "detected",
                "info",
                path,
                line_number,
                source_line(lines, line_number),
                "regex",
                "Traceability-related runtime event keyword detected.",
                {"matched_term": match.group(1).lower()},
            )
    for path in sorted(target.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TRACE_SCAN_SUFFIXES:
            continue
        if path.name in TRACE_MANIFEST_NAMES:
            continue
        if is_fixture_like_path(path):
            continue
        rel = path.relative_to(target).as_posix()
        if not TRACE_FILE_HINT.search(rel):
            continue
        text = read_text(path)
        if not text:
            continue
        lines = text.splitlines()
        for line_number, line in enumerate(lines, start=1):
            match = TRACE_KEYWORDS.search(line)
            if not match:
                continue
            detected = True
            add_finding(
                target,
                findings,
                counters,
                "BIO_trace_manifest",
                "bio_trace_manifest_keyword_v1",
                "detected",
                "info",
                path,
                line_number,
                source_line(lines, line_number),
                "regex",
                "Traceability-related runtime event keyword detected.",
                {"matched_term": match.group(1).lower()},
            )
    if not detected:
        add_finding(
            target,
            findings,
            counters,
            "BIO_trace_manifest",
            "bio_trace_manifest_file_v1",
            "not_detected",
            "info",
            Path("."),
            0,
            "",
            "file_presence",
            "No traceability manifest or runtime audit-log schema surface detected.",
        )


def _collect_run_trace_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    paths: list[Path],
) -> None:
    detected = False
    for path in paths:
        if path.suffix.lower() != ".py" or is_fixture_like_path(path):
            continue
        text = read_text(path)
        if not text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        _annotate_parents(tree)
        lines = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            finding = _run_trace_metadata(node)
            if not finding:
                continue
            detected = True
            add_finding(
                target,
                findings,
                counters,
                "BIO_run_trace",
                finding["pattern_id"],
                "detected",
                finding["severity"],
                path,
                getattr(node, "lineno", 0),
                source_line(lines, getattr(node, "lineno", 0)),
                "ast",
                finding["explanation"],
                finding["metadata"],
            )
    if not detected:
        add_finding(
            target,
            findings,
            counters,
            "BIO_run_trace",
            "bio_run_trace_v1",
            "not_detected",
            "info",
            Path("."),
            0,
            "",
            "ast",
            "No risky subprocess or os.system bio-tool execution patterns detected.",
        )


def _looks_like_smiles(value: str) -> bool:
    if len(value) < 3 or len(value) > 256:
        return False
    if not SMILES_ALLOWED.fullmatch(value):
        return False
    if not any(ch in value for ch in "()[]=#123456789"):
        condensed = value.replace(".", "")
        if not (len(condensed) >= 8 and len(set(condensed)) <= 2 and re.search(r"[BCNOFPSIbcnops]", condensed)):
            return False
    return bool(re.search(r"[BCNOFPSIbcnops]", value))


def _smiles_context_permits(node: ast.Constant, value: str) -> bool:
    parent = getattr(node, "parent", None)
    if isinstance(parent, ast.Assign):
        for target in parent.targets:
            if isinstance(target, ast.Name) and any(tok in target.id.lower() for tok in SMILES_CONTEXT_TOKENS):
                return True
            if isinstance(target, ast.Name):
                condensed = value.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
                if len(condensed) >= 8 and len(set(condensed)) <= 2 and re.search(r"[BCNOFPSIbcnops]", condensed):
                    return True
    if any(tok in value.lower() for tok in ("cl", "br", "@", "#", "=")):
        return True
    if re.search(r"\d", value):
        return True
    return False


def _smiles_issues(value: str) -> list[str]:
    issues: list[str] = []
    if value.count("(") != value.count(")"):
        issues.append("unbalanced_parentheses")
    if value.count("[") != value.count("]"):
        issues.append("unbalanced_brackets")
    ring_counts = {digit: value.count(digit) for digit in set(re.findall(r"\d", value))}
    for digit, count in ring_counts.items():
        if count % 2 != 0:
            issues.append("unclosed_ring_label")
            break
    condensed = value.replace("(", "").replace(")", "").replace("[", "").replace("]", "")
    if len(condensed) >= 8 and len(set(condensed)) <= 2:
        issues.append("low_entropy_placeholder_pattern")
    return issues


def _call_name(node: ast.AST) -> str:
    if not isinstance(node, ast.Call):
        return ""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts: list[str] = []
        cur: ast.AST | None = node.func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def _guarded_against_none(assign_node: ast.Assign, variable_name: str) -> bool:
    parent = getattr(assign_node, "parent", None)
    body: list[ast.stmt] | None = None
    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
        body = parent.body
    if body is None:
        return False
    try:
        index = body.index(assign_node)
    except ValueError:
        return False
    for stmt in body[index + 1 : index + 4]:
        if _stmt_checks_none(stmt, variable_name):
            return True
    return False


def _stmt_checks_none(stmt: ast.stmt, variable_name: str) -> bool:
    if not isinstance(stmt, ast.If):
        return False
    test = stmt.test
    if isinstance(test, ast.Compare) and isinstance(test.left, ast.Name) and test.left.id == variable_name:
        for comparator in test.comparators:
            if isinstance(comparator, ast.Constant) and comparator.value is None:
                return True
    if isinstance(test, ast.Call) and _call_name(test) in {"assert", "raise"}:
        return variable_name in ast.unparse(test)
    return False


def _import_failure_sets_mock_flag(node: ast.Try) -> str | None:
    imports_bio = any(_stmt_imports_bio_module(stmt) for stmt in node.body)
    if not imports_bio:
        return None
    for handler in node.handlers:
        if handler.type is not None and not _handler_is_import_error(handler.type):
            continue
        if any(_stmt_sets_mock_behavior(stmt) for stmt in handler.body):
            return "import_failure_sets_mock_flag"
    return None


def _stmt_imports_bio_module(stmt: ast.stmt) -> bool:
    if isinstance(stmt, ast.Import):
        return any(alias.name.startswith(BIO_IMPORT_MODULES) for alias in stmt.names)
    if isinstance(stmt, ast.ImportFrom):
        return bool(stmt.module) and stmt.module.startswith(BIO_IMPORT_MODULES)
    return False


def _handler_is_import_error(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id in {"ImportError", "ModuleNotFoundError", "Exception"}
    if isinstance(node, ast.Tuple):
        return any(_handler_is_import_error(elt) for elt in node.elts)
    return False


def _stmt_sets_mock_behavior(stmt: ast.stmt) -> bool:
    for node in ast.walk(stmt):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id.lower()
                    if target.id in MOCK_FLAG_NAMES and isinstance(node.value, ast.Constant) and node.value.value is True:
                        return True
                    if any(tok in name for tok in MOCK_NAME_TOKENS):
                        return True
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(tok in node.value.lower() for tok in MOCK_NAME_TOKENS):
                return True
    return False


def _is_explicit_demo_mode_branch(node: ast.If) -> bool:
    names = {name.id for name in ast.walk(node.test) if isinstance(name, ast.Name)}
    if not names & MOCK_FLAG_NAMES:
        return False
    branch_text = " ".join(ast.unparse(stmt).lower() for stmt in node.body)
    return any(tok in branch_text for tok in MOCK_NAME_TOKENS)


def _run_trace_metadata(node: ast.Call) -> dict[str, object] | None:
    call_name = _call_name(node)
    if call_name in {"subprocess.run", "subprocess.Popen"}:
        command_text = _command_text(node)
        tool = _matched_bio_tool(command_text)
        if not tool:
            return None
        shell_true = _keyword_bool(node, "shell")
        timeout_present = _has_keyword(node, "timeout")
        tainted = _command_uses_tainted_name(node)
        if shell_true and tainted:
            severity = "warn"
            explanation = "Known bio-tool subprocess call uses shell=True with probable external-input taint."
            pattern_id = "bio_run_trace_shell_tainted_v1"
        elif call_name == "subprocess.run" and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str) and tainted:
            severity = "warn"
            explanation = "Known bio-tool subprocess uses a string command with probable external-input taint."
            pattern_id = "bio_run_trace_string_tainted_v1"
        elif shell_true:
            severity = "info"
            explanation = "Known bio-tool subprocess uses shell=True."
            pattern_id = "bio_run_trace_shell_v1"
        elif not timeout_present:
            severity = "info"
            explanation = "Known bio-tool subprocess call has no explicit timeout."
            pattern_id = "bio_run_trace_timeout_v1"
        else:
            return None
        return {
            "pattern_id": pattern_id,
            "severity": severity,
            "explanation": explanation,
            "metadata": {
                "call_name": call_name,
                "bio_tool": tool,
                "shell_true": shell_true,
                "external_input_taint": tainted,
                "timeout_present": timeout_present,
            },
        }
    if call_name == "os.system":
        command_text = _command_text(node)
        tool = _matched_bio_tool(command_text)
        if not tool:
            return None
        return {
            "pattern_id": "bio_run_trace_os_system_v1",
            "severity": "warn",
            "explanation": "Known bio-tool invocation uses os.system, which is hard to constrain safely.",
            "metadata": {
                "call_name": call_name,
                "bio_tool": tool,
                "shell_true": True,
                "external_input_taint": _command_uses_tainted_name(node),
                "timeout_present": False,
            },
        }
    return None


def _command_text(node: ast.Call) -> str:
    if not node.args:
        return ""
    arg = node.args[0]
    try:
        return ast.unparse(arg)
    except Exception:
        return ""


def _matched_bio_tool(command_text: str) -> str:
    lowered = command_text.lower()
    for tool in BIO_TOOL_NAMES:
        if tool in lowered:
            return tool
    return ""


def _command_uses_tainted_name(node: ast.Call) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and any(tok in child.id.lower() for tok in TAINT_NAME_TOKENS):
            return True
    return False


def _keyword_bool(node: ast.Call, name: str) -> bool:
    for kw in node.keywords:
        if kw.arg == name and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, bool):
            return kw.value.value
    return False


def _has_keyword(node: ast.Call, name: str) -> bool:
    return any(kw.arg == name for kw in node.keywords)


def _annotate_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "parent", parent)
