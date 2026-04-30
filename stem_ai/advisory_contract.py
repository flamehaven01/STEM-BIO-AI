from __future__ import annotations

import hashlib
import json
import re
from typing import Any


ADVISORY_SCHEMA_VERSION = "stem-ai-advisory-v1.4"
MAX_ADVISORY_FINDINGS = 200

_SEVERITY_RANK = {"error": 0, "warn": 1, "info": 2}
_STATUS_RANK = {
    "error": 0,
    "detected": 1,
    "manual_review_required": 2,
    "not_applicable": 3,
    "not_detected": 4,
    "absent": 5,
}
_PROHIBITED_CLAIMS = re.compile(
    r"\b("
    r"clinically safe|safe for clinical deployment|clinical deployment ready|"
    r"regulatory approved|regulatory clearance|fda approved|ce marked|"
    r"certified for clinical|proven effective|medical advice"
    r")\b",
    re.I,
)


def known_finding_ids(result: dict[str, Any]) -> set[str]:
    return {str(finding.get("finding_id")) for finding in result.get("evidence_ledger", [])}


def cited_finding_ids(advisory: dict[str, Any]) -> set[str]:
    cited: set[str] = set()
    for section in ("reviewer_notes", "inspection_priorities"):
        for item in advisory.get(section, []) or []:
            for cite in item.get("cites", []) or []:
                cited.add(str(cite))
    return cited


def build_advisory_input(result: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, bounded packet for future AI advisory adapters."""
    findings = sorted(
        result.get("evidence_ledger", []),
        key=lambda item: (
            _SEVERITY_RANK.get(str(item.get("severity", "")).lower(), 9),
            _STATUS_RANK.get(str(item.get("status", "")).lower(), 9),
            str(item.get("detector", "")),
            str(item.get("file", "")),
            int(item.get("line", 0) or 0),
            str(item.get("finding_id", "")),
        ),
    )[:MAX_ADVISORY_FINDINGS]
    return {
        "schema_version": "stem-ai-advisory-input-v1.4",
        "policy": _policy(),
        "target": {
            "name": result.get("target", {}).get("name"),
            "remote": result.get("target", {}).get("remote"),
            "branch": result.get("target", {}).get("branch"),
            "commit": result.get("target", {}).get("commit"),
            "file_count": result.get("target", {}).get("file_count"),
        },
        "score": result.get("score", {}),
        "classification": result.get("classification", {}),
        "code_integrity": result.get("code_integrity", {}),
        "detector_summary": result.get("detector_summary", {}),
        "reasoning_model": result.get("reasoning_model", {}),
        "stage_4_rubric": result.get("stage_4_rubric", {}),
        "ast_signal_summary": result.get("ast_signal_summary", {}),
        "evidence_ledger": [_advisory_finding(finding) for finding in findings],
        "omitted_finding_count": max(0, len(result.get("evidence_ledger", [])) - len(findings)),
    }


def validate_advisory_output(result: dict[str, Any], advisory: dict[str, Any]) -> dict[str, Any]:
    known = known_finding_ids(result)
    cited = cited_finding_ids(advisory)
    invalid_citations = sorted(cited - known)
    missing_citation_items = _missing_citation_items(advisory)
    prohibited_claims = _prohibited_claims(advisory)
    override_requested = bool(advisory.get("final_score_override")) or any(
        key in advisory for key in ("final_score", "formal_tier", "replication_score", "replication_tier")
    )
    errors: list[str] = []
    if invalid_citations:
        errors.append("invalid_citations")
    if missing_citation_items:
        errors.append("missing_required_citations")
    if prohibited_claims:
        errors.append("prohibited_clinical_or_regulatory_claims")
    if override_requested:
        errors.append("final_score_override_requested")
    status = "invalid" if errors else "valid"
    return {
        "schema_version": ADVISORY_SCHEMA_VERSION,
        "provider": advisory.get("provider", "none"),
        "model": advisory.get("model"),
        "mode": advisory.get("mode", "offline_contract_validation"),
        "status": status,
        "input_contract": _input_contract(build_advisory_input(result)),
        "reviewer_notes": list(advisory.get("reviewer_notes", []) or []),
        "inspection_priorities": list(advisory.get("inspection_priorities", []) or []),
        "citation_index": {finding_id: finding_id in known for finding_id in sorted(cited)},
        "invalid_citations": invalid_citations,
        "missing_citation_items": missing_citation_items,
        "prohibited_claims": prohibited_claims,
        "errors": errors,
        "policy": _policy(),
    }


def build_offline_advisory(result: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic no-AI advisory result for contract validation."""
    draft = {
        "provider": "none",
        "model": None,
        "mode": "offline_contract_validation",
        "reviewer_notes": _offline_reviewer_notes(result),
        "inspection_priorities": _offline_inspection_priorities(result),
    }
    return validate_advisory_output(result, draft)


def _advisory_finding(finding: dict[str, Any]) -> dict[str, Any]:
    return {
        "finding_id": finding.get("finding_id"),
        "detector": finding.get("detector"),
        "detector_version": finding.get("detector_version"),
        "pattern_id": finding.get("pattern_id"),
        "status": finding.get("status"),
        "severity": finding.get("severity"),
        "file": finding.get("file"),
        "line": finding.get("line"),
        "match_type": finding.get("match_type"),
        "explanation": finding.get("explanation"),
    }


def _offline_reviewer_notes(result: dict[str, Any]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for key, item in result.get("code_integrity", {}).items():
        status = str(item.get("status", ""))
        if status not in {"WARN", "FAIL"}:
            continue
        cites = _first_finding_ids(result, key, statuses={"detected", "error"})
        if not cites:
            continue
        notes.append({
            "claim": f"{key} reports {status}; reviewer should inspect the cited evidence before use.",
            "severity": "block" if status == "FAIL" else "warn",
            "cites": cites,
            "recommended_action": "Inspect cited file and determine whether the finding is production-relevant.",
        })
    return notes


def _offline_inspection_priorities(result: dict[str, Any]) -> list[dict[str, Any]]:
    priorities: list[dict[str, Any]] = []
    reasoning = result.get("reasoning_model", {})
    risk_gate = reasoning.get("evidence_risk_gate", {})
    if risk_gate.get("status") == "review_required":
        priorities.append({
            "priority": "high",
            "reason": "Reasoning diagnostics report evidence risk beyond the advisory gate.",
            "cites": _fallback_citations(result),
        })
    uncertainty = reasoning.get("uncertainty_budget", {})
    if uncertainty.get("status") == "manual_review_required":
        priorities.append({
            "priority": "high",
            "reason": "Reasoning diagnostics report high uncertainty.",
            "cites": _fallback_citations(result),
        })
    return priorities


def _first_finding_ids(
    result: dict[str, Any],
    detector: str,
    statuses: set[str],
    limit: int = 3,
) -> list[str]:
    ids: list[str] = []
    for finding in result.get("evidence_ledger", []):
        if finding.get("detector") == detector and finding.get("status") in statuses:
            ids.append(str(finding.get("finding_id")))
        if len(ids) >= limit:
            break
    return ids


def _fallback_citations(result: dict[str, Any], limit: int = 3) -> list[str]:
    ids = [
        str(finding.get("finding_id"))
        for finding in result.get("evidence_ledger", [])
        if finding.get("status") in {"detected", "error", "not_detected", "absent"}
    ]
    return ids[:limit]


def _missing_citation_items(advisory: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for section in ("reviewer_notes", "inspection_priorities"):
        for index, item in enumerate(advisory.get(section, []) or []):
            if not item.get("cites"):
                missing.append(f"{section}[{index}]")
    return missing


def _prohibited_claims(advisory: dict[str, Any]) -> list[str]:
    claims: list[str] = []
    for section in ("reviewer_notes", "inspection_priorities"):
        for item in advisory.get(section, []) or []:
            text = " ".join(str(item.get(key, "")) for key in ("claim", "reason", "recommended_action"))
            if _PROHIBITED_CLAIMS.search(text):
                claims.append(text)
    return claims


def _input_contract(advisory_input: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(advisory_input, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": advisory_input["schema_version"],
        "finding_count": len(advisory_input.get("evidence_ledger", [])),
        "omitted_finding_count": advisory_input.get("omitted_finding_count", 0),
        "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest().upper(),
    }


def _policy() -> dict[str, bool]:
    return {
        "final_score_override": False,
        "requires_finding_id_citations": True,
        "raw_repo_text_allowed": False,
        "clinical_claims_allowed": False,
    }
