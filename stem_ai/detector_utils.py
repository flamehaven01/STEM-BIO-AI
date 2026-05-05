from __future__ import annotations

import configparser
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import __version__
from .evidence import EvidenceFinding, clip_snippet, make_finding_id
from .patterns import EXACT_PINNED_DEP, LOOSE_DEP, SKIP_DIRS, TEXT_EXTENSIONS


DETECTOR_VERSION = __version__
FIXTURE_PATH_PARTS = {"test", "tests", "testing", "fixture", "fixtures", "example", "examples", "demo", "demos", "sample", "samples"}


def add_finding(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    detector: str,
    pattern_id: str,
    status: str,
    severity: str,
    path: Path,
    line: int,
    snippet: str,
    match_type: str,
    explanation: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    rel_path = relative_path(target, path).as_posix() if path != Path(".") else "."
    key = (detector, rel_path)
    counters[key] += 1
    findings.append(
        EvidenceFinding(
            finding_id=make_finding_id(detector, rel_path, line, counters[key]),
            detector=detector,
            detector_version=DETECTOR_VERSION,
            pattern_id=pattern_id,
            status=status,
            severity=severity,
            file=rel_path,
            line=int(line),
            snippet=clip_snippet(snippet),
            match_type=match_type,
            explanation=explanation,
            metadata=metadata or {},
        )
    )


def existing_named_files(root: Path, names: list[str]) -> list[Path]:
    return [root / name for name in names if (root / name).is_file()]


def iter_text_files(root: Path, max_files: int) -> Iterable[Path]:
    if not root.exists():
        return []
    paths = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_EXTENSIONS
        and not any(part in SKIP_DIRS for part in path.parts)
    ]
    return sorted(paths, key=lambda p: p.as_posix())[:max_files]


def iter_python_files(root: Path) -> Iterable[Path]:
    paths = [
        path
        for path in root.rglob("*.py")
        if path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
    ]
    return sorted(paths, key=lambda p: relative_path(root, p).as_posix())


def iter_code_files(root: Path, max_files: int) -> Iterable[Path]:
    paths = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".py", ".sh"}
        and not any(part in SKIP_DIRS for part in path.parts)
    ]
    return sorted(paths, key=lambda p: relative_path(root, p).as_posix())[:max_files]


def iter_deprecated_files(root: Path, max_files: int) -> Iterable[Path]:
    deprecated_names = {"deprecated", "legacy", "archive", "archives", "old"}
    paths = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_EXTENSIONS
        and not any(part in SKIP_DIRS for part in path.parts)
        and ({part.lower() for part in path.parts} & deprecated_names)
    ]
    return sorted(paths, key=lambda p: relative_path(root, p).as_posix())[:max_files]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def relative_path(root: Path, path: Path) -> Path:
    if path == Path("."):
        return Path(".")
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def source_line(lines: list[str], line: int) -> str:
    if line <= 0 or line > len(lines):
        return ""
    return lines[line - 1].strip()


def dependency_entries(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return []
    quoted = [m.group(1) or m.group(2) for m in re.finditer(r'"([^"]+)"|\'([^\']+)\'', stripped)]
    if quoted:
        return [item.strip() for item in quoted if item.strip()]
    return [stripped]


def manifest_dependency_entries(path: Path, text: str) -> list[tuple[int, str, str]]:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if name == "requirements.txt":
        return _requirements_entries(text)
    if name == "environment.yml":
        return _environment_entries(text)
    if name == "setup.cfg":
        return _setup_cfg_entries(text)
    if name == "pyproject.toml" or suffix == ".toml":
        return _pyproject_entries(text)
    return [(line_number, entry, snippet) for line_number, snippet in enumerate(text.splitlines(), start=1) for entry in dependency_entries(snippet)]


def is_unpinned_dependency(line: str) -> bool:
    normalized = line.split("#", 1)[0].strip().rstrip(",")
    if not normalized or normalized.startswith(("-", "[", "{")):
        return False
    if EXACT_PINNED_DEP.search(normalized):
        return False
    if LOOSE_DEP.search(normalized):
        return True
    return bool(re.match(r"^[A-Za-z0-9_.-]+(\[[^\]]+\])?(\s*;.*)?$", normalized))


def is_fixture_like_path(path: Path) -> bool:
    return any(part.lower() in FIXTURE_PATH_PARTS for part in path.parts)


def _requirements_entries(text: str) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    for line_number, snippet in enumerate(text.splitlines(), start=1):
        stripped = snippet.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(("-", "--")):
            continue
        rows.extend((line_number, entry, snippet) for entry in dependency_entries(stripped))
    return rows


def _environment_entries(text: str) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    in_dependencies = False
    in_pip_block = False
    dep_indent = 0
    pip_indent = 0
    for line_number, snippet in enumerate(text.splitlines(), start=1):
        raw = snippet.rstrip()
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "dependencies:":
            in_dependencies = True
            in_pip_block = False
            dep_indent = indent
            continue
        if in_dependencies and indent <= dep_indent and not stripped.startswith("-"):
            in_dependencies = False
            in_pip_block = False
        if not in_dependencies:
            continue
        if stripped == "- pip:":
            in_pip_block = True
            pip_indent = indent
            continue
        if in_pip_block and indent <= pip_indent and stripped.startswith("-"):
            in_pip_block = False
        if not stripped.startswith("- "):
            continue
        entry = stripped[2:].strip()
        if in_pip_block or entry:
            rows.append((line_number, entry, snippet))
    return rows


def _setup_cfg_entries(text: str) -> list[tuple[int, str, str]]:
    parser = configparser.ConfigParser()
    try:
        parser.read_string(text)
    except configparser.Error:
        return []
    rows: list[tuple[int, str, str]] = []
    valid_sections = {"options", "options.extras_require"}
    line_numbers = {idx + 1: line for idx, line in enumerate(text.splitlines())}
    for section in parser.sections():
        if section not in valid_sections:
            continue
        for key, value in parser.items(section):
            if key not in {"install_requires"} and section != "options.extras_require":
                continue
            for raw_entry in value.splitlines():
                entry = raw_entry.strip()
                if not entry:
                    continue
                line_number = _find_line_number(line_numbers, raw_entry.strip())
                rows.append((line_number, entry, line_numbers.get(line_number, raw_entry)))
    return rows


def _pyproject_entries(text: str) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    current_section = ""
    collecting_array = False
    for line_number, snippet in enumerate(text.splitlines(), start=1):
        stripped = snippet.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped.strip("[]").strip()
            collecting_array = False
            continue
        if collecting_array:
            for entry in dependency_entries(stripped):
                rows.append((line_number, entry, snippet))
            if "]" in stripped:
                collecting_array = False
            continue
        if current_section == "build-system" and stripped.startswith("requires"):
            for entry in dependency_entries(stripped):
                rows.append((line_number, entry, snippet))
            collecting_array = "[" in stripped and "]" not in stripped
            continue
        if current_section == "project" and stripped.startswith("dependencies"):
            for entry in dependency_entries(stripped):
                rows.append((line_number, entry, snippet))
            collecting_array = "[" in stripped and "]" not in stripped
            continue
        if current_section == "project.optional-dependencies":
            if "=" not in stripped:
                continue
            _, rhs = stripped.split("=", 1)
            for entry in dependency_entries(rhs):
                rows.append((line_number, entry, snippet))
            collecting_array = "[" in rhs and "]" not in rhs
            continue
        if current_section.startswith("tool.poetry") and current_section.endswith("dependencies"):
            if "=" not in stripped:
                continue
            key, rhs = stripped.split("=", 1)
            if key.strip().lower() == "python":
                continue
            values = [m.group(1) or m.group(2) for m in re.finditer(r'"([^"]+)"|\'([^\']+)\'', rhs)]
            for value in values:
                rows.append((line_number, f"{key.strip()} {value.strip()}", snippet))
            continue
    return rows


def _find_line_number(lines: dict[int, str], needle: str) -> int:
    for line_number, snippet in lines.items():
        if needle and needle in snippet:
            return line_number
    return 0
