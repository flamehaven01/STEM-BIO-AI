from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvidenceFinding:
    finding_id: str
    detector: str
    detector_version: str
    pattern_id: str
    status: str
    severity: str
    file: str
    line: int
    snippet: str
    match_type: str
    explanation: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = {
            "finding_id": self.finding_id,
            "detector": self.detector,
            "detector_version": self.detector_version,
            "pattern_id": self.pattern_id,
            "status": self.status,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "snippet": self.snippet,
            "match_type": self.match_type,
            "explanation": self.explanation,
        }
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


def make_finding_id(
    detector: str,
    file_path: str | Path,
    line: int,
    occurrence_index: int,
) -> str:
    if isinstance(file_path, Path):
        normalized_path = file_path.as_posix()
    else:
        normalized_path = str(file_path).replace("\\", "/")
    normalized_path = normalized_path or "."
    return f"{detector}:{normalized_path}:{int(line)}:{int(occurrence_index):03d}"


def clip_snippet(text: str, limit: int = 180) -> str:
    value = " ".join(str(text).split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."
