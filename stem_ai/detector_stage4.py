from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .detector_utils import add_finding, existing_named_files, read_text, relative_path, source_line
from .evidence import EvidenceFinding
from .patterns import EXACT_PINNED_DEP, SKIP_DIRS


URL = re.compile(r"https?://[^\s)>\]\"']+", re.I)
REPRO_HEADING = re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*\b(reproduc\w*|replicat\w*|rerun|recreate results)\b")
MAKE_TARGET = re.compile(r"(?im)^(reproduce|replicate|eval|evaluate|benchmark|test|results)\s*:")
HASH_PIN = re.compile(r"(--hash=sha256:|sha256[:=]|md5[:=])[A-Fa-f0-9]{16,}", re.I)
PYPROJECT_SCRIPT = re.compile(r"(?im)^\s*\[project\.scripts\]|\bentry_points\b|\bconsole_scripts\b")
DATASET_CONTEXT = re.compile(r"\b(dataset|data set|data|SRA|GEO|Zenodo|Figshare|Kaggle|OpenML|Hugging ?Face)\b", re.I)
MODEL_CONTEXT = re.compile(r"\b(model|weight|checkpoint|ckpt|\.pt|\.pth|\.onnx|safetensors|hugging ?face)\b", re.I)


def collect_stage4_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    ast_summary: dict[str, Any],
) -> tuple[int, str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}

    _container_files(target, findings, counters, items)
    _make_targets(target, findings, counters, items)
    _environment_lock_evidence(target, findings, counters, items)
    _exact_pins_or_hashes(target, findings, counters, items)
    _readme_repro_section(target, findings, counters, items)
    _checksum_files(target, findings, counters, items)
    _dataset_urls(target, findings, counters, items)
    _model_weight_urls(target, findings, counters, items)
    _citation_cff(target, findings, counters, items)
    _cli_entrypoint(target, findings, counters, items, ast_summary)
    _seed_setting(target, findings, counters, items, ast_summary)
    _runnable_examples(target, findings, counters, items)

    raw_total = sum(int(item["score"]) for item in items.values())
    rubric: dict[str, Any] = dict(items)
    rubric["stage_4_raw_total"] = {
        "score": raw_total,
        "max": 100,
        "evidence": "Raw Stage 4 rubric total. Stage 4 is reported separately and does not alter final score in v1.3.0.",
    }
    return raw_total, replication_tier(raw_total), rubric


def replication_tier(score: int) -> str:
    if score <= 24:
        return "R0"
    if score <= 44:
        return "R1"
    if score <= 64:
        return "R2"
    if score <= 84:
        return "R3"
    return "R4"


def _score_item(
    items: dict[str, dict[str, Any]],
    key: str,
    score: int,
    max_score: int,
    evidence: str,
) -> None:
    items[key] = {"score": score, "max": max_score, "evidence": evidence}


def _container_files(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = existing_named_files(target, ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"])
    _file_presence_score(target, findings, counters, items, "S4_container_environment", "container_file_v1", paths, 10, "Container or compose file exists.")


def _make_targets(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = existing_named_files(target, ["Makefile", "makefile"])
    detected = False
    for path in paths:
        lines = read_text(path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            match = MAKE_TARGET.search(line)
            if not match:
                continue
            detected = True
            add_finding(target, findings, counters, "S4_make_reproduce_target", "make_reproduce_target_v1", "detected", "info", path, line_number, line, "text", "Makefile target supporting reproduction, evaluation, benchmark, or test detected.", {"target": match.group(1)})
    _score_or_absent(target, findings, counters, items, "S4_make_reproduce_target", "make_reproduce_target_v1", detected, bool(paths), 10, "Makefile reproduction/evaluation target detected.", "No Makefile reproduction/evaluation target detected.", "No Makefile detected.")


def _environment_lock_evidence(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = existing_named_files(target, ["environment.yml", "environment.yaml", "requirements.txt", "requirements.lock", "poetry.lock", "uv.lock", "Pipfile.lock", "conda-lock.yml", "conda-lock.yaml"])
    detected = bool(paths)
    for path in paths:
        add_finding(target, findings, counters, "S4_environment_lock_evidence", "environment_lock_file_v1", "detected", "info", path, 0, relative_path(target, path).as_posix(), "file_presence", "Environment, dependency, or lock manifest detected.")
    _score_item(items, "S4_environment_lock_evidence", 10 if detected else 0, 10, "Environment, dependency, or lock manifest detected." if detected else "No environment, dependency, or lock manifest detected.")
    if not detected:
        add_finding(target, findings, counters, "S4_environment_lock_evidence", "environment_lock_file_v1", "not_detected", "info", Path("."), 0, "", "file_presence", "No environment, dependency, or lock manifest detected.")


def _exact_pins_or_hashes(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = existing_named_files(target, ["requirements.txt", "pyproject.toml", "setup.cfg", "environment.yml", "environment.yaml", "requirements.lock", "poetry.lock", "uv.lock", "Pipfile.lock"])
    detected = False
    for path in paths:
        lines = read_text(path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not (EXACT_PINNED_DEP.search(line) or HASH_PIN.search(line)):
                continue
            detected = True
            add_finding(target, findings, counters, "S4_exact_dependency_pins_or_hashes", "exact_pin_or_hash_v1", "detected", "info", path, line_number, line, "dependency", "Exact dependency pin or hash evidence detected.")
    _score_or_absent(target, findings, counters, items, "S4_exact_dependency_pins_or_hashes", "exact_pin_or_hash_v1", detected, bool(paths), 10, "Exact dependency pin or hash evidence detected.", "Dependency manifests exist but no exact pins or hashes were detected.", "No dependency manifest detected.")


def _readme_repro_section(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = existing_named_files(target, ["README.md", "README.rst", "readme.md"])
    detected = False
    for path in paths:
        text = read_text(path)
        lines = text.splitlines()
        for match in REPRO_HEADING.finditer(text):
            detected = True
            line = text.count("\n", 0, match.start()) + 1
            add_finding(target, findings, counters, "S4_readme_reproducibility_section", "readme_repro_heading_v1", "detected", "info", path, line, source_line(lines, line), "regex", "README reproducibility or replication section heading detected.")
    _score_or_absent(target, findings, counters, items, "S4_readme_reproducibility_section", "readme_repro_heading_v1", detected, bool(paths), 10, "README reproducibility or replication section detected.", "README exists but no reproducibility or replication section heading was detected.", "No README detected.")


def _checksum_files(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = _glob_files(target, {".sha256", ".md5", ".sha512"})
    _file_presence_score(target, findings, counters, items, "S4_checksum_files", "checksum_file_v1", paths, 10, "Checksum file exists.")


def _dataset_urls(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = [*existing_named_files(target, ["README.md", "README.rst", "readme.md"]), *list(_docs_files(target))]
    detected = _contextual_url_detector(target, findings, counters, "S4_dataset_url", "dataset_url_v1", paths, DATASET_CONTEXT, "Dataset URL or data source reference detected.")
    _score_or_absent(target, findings, counters, items, "S4_dataset_url", "dataset_url_v1", detected, bool(paths), 10, "Dataset URL or data source reference detected.", "Documentation exists but no dataset URL or data source URL was detected.", "No README/docs files detected.")


def _model_weight_urls(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = [*existing_named_files(target, ["README.md", "README.rst", "readme.md"]), *list(_docs_files(target))]
    detected = _contextual_url_detector(target, findings, counters, "S4_model_weight_url_or_checksum", "model_weight_url_v1", paths, MODEL_CONTEXT, "Model weight, checkpoint, or model artifact URL detected.")
    checksum_present = bool(_glob_files(target, {".sha256", ".md5", ".sha512"}))
    if checksum_present and not detected:
        detected = True
        add_finding(target, findings, counters, "S4_model_weight_url_or_checksum", "model_weight_url_v1", "detected", "info", Path("."), 0, "", "aggregate", "Checksum file present; model/artifact integrity evidence may be available.", {"source": "checksum_files"})
    _score_or_absent(target, findings, counters, items, "S4_model_weight_url_or_checksum", "model_weight_url_v1", detected, bool(paths) or checksum_present, 10, "Model artifact URL or checksum evidence detected.", "Documentation exists but no model artifact URL/checksum evidence was detected.", "No README/docs or checksum files detected.")


def _citation_cff(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    paths = existing_named_files(target, ["CITATION.cff"])
    _file_presence_score(target, findings, counters, items, "S4_citation_cff", "citation_cff_v1", paths, 5, "CITATION.cff exists.")


def _cli_entrypoint(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
    ast_summary: dict[str, Any],
) -> None:
    paths = existing_named_files(target, ["pyproject.toml", "setup.py", "setup.cfg"])
    detected = False
    for path in paths:
        lines = read_text(path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not PYPROJECT_SCRIPT.search(line):
                continue
            detected = True
            add_finding(target, findings, counters, "S4_cli_entrypoint", "cli_entrypoint_v1", "detected", "info", path, line_number, line, "metadata", "Package CLI entry point metadata detected.")
    if ast_summary.get("argparse_cli"):
        detected = True
        add_finding(target, findings, counters, "S4_cli_entrypoint", "cli_entrypoint_v1", "detected", "info", Path("."), 0, "", "aggregate", "argparse CLI evidence detected by AST summary.", {"source": "ast_signal_summary"})
    _score_or_absent(target, findings, counters, items, "S4_cli_entrypoint", "cli_entrypoint_v1", detected, bool(paths) or bool(ast_summary.get("files_total")), 5, "CLI entry point or argparse interface detected.", "Code/package metadata exists but no CLI entry point evidence was detected.", "No package metadata or Python AST surface detected.")


def _seed_setting(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
    ast_summary: dict[str, Any],
) -> None:
    count = int(ast_summary.get("seed_settings") or 0)
    if count:
        add_finding(target, findings, counters, "S4_seed_setting", "ast_seed_setting_stage4_v1", "detected", "info", Path("."), 0, "", "aggregate", "Deterministic seed setting evidence detected by AST summary.", {"seed_settings": count})
    else:
        add_finding(target, findings, counters, "S4_seed_setting", "ast_seed_setting_stage4_v1", "not_detected", "info", Path("."), 0, "", "aggregate", "No deterministic seed setting evidence detected by AST summary.")
    _score_item(items, "S4_seed_setting", 5 if count else 0, 5, "Deterministic seed setting detected." if count else "No deterministic seed setting detected.")


def _runnable_examples(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
) -> None:
    candidates = []
    for base in [target / "examples", target / "notebooks", target / "demo", target / "demos"]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".ipynb", ".sh", ".md"} and not any(part in SKIP_DIRS for part in path.parts):
                candidates.append(path)
    _file_presence_score(target, findings, counters, items, "S4_runnable_examples", "runnable_example_file_v1", candidates[:20], 5, "Runnable example, notebook, or demo file exists.")


def _file_presence_score(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
    detector: str,
    pattern_id: str,
    paths: list[Path],
    max_score: int,
    detected_evidence: str,
) -> None:
    if paths:
        for path in sorted(set(paths), key=lambda p: relative_path(target, p).as_posix()):
            add_finding(target, findings, counters, detector, pattern_id, "detected", "info", path, 0, relative_path(target, path).as_posix(), "file_presence", detected_evidence)
        _score_item(items, detector, max_score, max_score, detected_evidence)
    else:
        add_finding(target, findings, counters, detector, pattern_id, "not_detected", "info", Path("."), 0, "", "file_presence", f"No evidence detected for {detector}.")
        _score_item(items, detector, 0, max_score, f"No evidence detected for {detector}.")


def _score_or_absent(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    items: dict[str, dict[str, Any]],
    detector: str,
    pattern_id: str,
    detected: bool,
    surface_present: bool,
    max_score: int,
    detected_evidence: str,
    not_detected_evidence: str,
    absent_evidence: str,
) -> None:
    if detected:
        _score_item(items, detector, max_score, max_score, detected_evidence)
        return
    status = "not_detected" if surface_present else "absent"
    explanation = not_detected_evidence if surface_present else absent_evidence
    add_finding(target, findings, counters, detector, pattern_id, status, "info", Path("."), 0, "", "aggregate", explanation)
    _score_item(items, detector, 0, max_score, explanation)


def _contextual_url_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    detector: str,
    pattern_id: str,
    paths: list[Path],
    context: re.Pattern[str],
    explanation: str,
) -> bool:
    detected = False
    for path in sorted(set(paths), key=lambda p: relative_path(target, p).as_posix()):
        lines = read_text(path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not URL.search(line) or not context.search(line):
                continue
            detected = True
            add_finding(target, findings, counters, detector, pattern_id, "detected", "info", path, line_number, line, "regex", explanation, {"url": URL.search(line).group(0)})
    return detected


def _docs_files(target: Path) -> list[Path]:
    docs = target / "docs"
    if not docs.exists():
        return []
    paths = [
        path
        for path in docs.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".rst", ".txt"} and not any(part in SKIP_DIRS for part in path.parts)
    ]
    return sorted(paths, key=lambda p: relative_path(target, p).as_posix())[:30]


def _glob_files(target: Path, suffixes: set[str]) -> list[Path]:
    paths = [
        path
        for path in target.rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes and not any(part in SKIP_DIRS for part in path.parts)
    ]
    return sorted(paths, key=lambda p: relative_path(target, p).as_posix())[:50]
