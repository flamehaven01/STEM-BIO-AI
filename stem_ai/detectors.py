from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .detector_ast import MAX_AST_FILE_SIZE_BYTES, MAX_AST_FILES, collect_ast_findings
from .detector_stage4 import collect_stage4_findings
from .detector_surface import collect_surface_findings
from .evidence import EvidenceFinding


def collect_evidence(target: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evidence_ledger, ast_summary, _stage_4 = collect_evidence_bundle(target)
    return evidence_ledger, ast_summary


def collect_evidence_bundle(target: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    findings: list[EvidenceFinding] = []
    counters: dict[tuple[str, str], int] = defaultdict(int)

    collect_surface_findings(target, findings, counters)
    ast_summary = collect_ast_findings(
        target,
        findings,
        counters,
        max_ast_files=MAX_AST_FILES,
        max_ast_file_size_bytes=MAX_AST_FILE_SIZE_BYTES,
    )
    replication_score, replication_tier, stage_4_rubric = collect_stage4_findings(
        target,
        findings,
        counters,
        ast_summary,
    )
    stage_4 = {
        "replication_score": replication_score,
        "replication_tier": replication_tier,
        "stage_4_rubric": stage_4_rubric,
    }

    return [finding.to_dict() for finding in findings], ast_summary, stage_4
