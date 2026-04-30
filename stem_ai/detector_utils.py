from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import __version__
from .evidence import EvidenceFinding, clip_snippet, make_finding_id
from .patterns import EXACT_PINNED_DEP, LOOSE_DEP, SKIP_DIRS, TEXT_EXTENSIONS


DETECTOR_VERSION = __version__


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


def is_unpinned_dependency(line: str) -> bool:
    normalized = line.split("#", 1)[0].strip().rstrip(",")
    if not normalized or normalized.startswith(("-", "[", "{")):
        return False
    if EXACT_PINNED_DEP.search(normalized):
        return False
    if LOOSE_DEP.search(normalized):
        return True
    return bool(re.match(r"^[A-Za-z0-9_.-]+(\[[^\]]+\])?(\s*;.*)?$", normalized))
