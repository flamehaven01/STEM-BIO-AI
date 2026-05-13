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
    evidence_status: str | None = None
    confidence: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        evidence_status = self.evidence_status or _default_evidence_status(self.status)
        confidence = self.confidence or _default_confidence(self.status, self.match_type)
        data = {
            "finding_id": self.finding_id,
            "detector": self.detector,
            "detector_version": self.detector_version,
            "pattern_id": self.pattern_id,
            "status": self.status,
            "evidence_status": evidence_status,
            "confidence": confidence,
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


def _default_evidence_status(status: str) -> str:
    mapping = {
        "detected": "confirmed_present",
        "absent": "confirmed_missing",
        "not_detected": "not_found_in_reviewed_sources",
        "not_applicable": "not_applicable",
        "manual_review_required": "manual_review_required",
        "error": "collection_error",
    }
    return mapping.get(str(status), "observed")


def _default_confidence(status: str, match_type: str) -> str:
    status = str(status)
    match_type = str(match_type)
    if status in {"error", "manual_review_required"}:
        return "low"
    if status == "not_detected":
        return "medium"
    if match_type in {"ast", "regex", "file_presence", "dependency"}:
        return "high"
    if match_type in {"aggregate", "metadata", "limit"}:
        return "medium"
    return "medium"


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
