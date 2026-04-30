from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROVIDER_BENCHMARK_SCHEMA_VERSION = "stem-bio-ai-provider-response-benchmark-v1.4"


def packet_stats_record(
    repo_entry: dict[str, Any],
    result: dict[str, Any],
    packet: dict[str, Any],
    packet_path: Path | None = None,
) -> dict[str, Any]:
    """Build a compact provider-packet benchmark record for one repository."""
    allowed_ids = packet.get("allowed_finding_ids", [])
    findings = packet.get("evidence_ledger", [])
    return {
        "schema_version": PROVIDER_BENCHMARK_SCHEMA_VERSION,
        "record_type": "packet_stats",
        "repo": repo_entry.get("repo") or result.get("target", {}).get("name"),
        "local_name": repo_entry.get("local_name"),
        "local_path": repo_entry.get("local_path"),
        "expected_commit": repo_entry.get("commit"),
        "scan_commit": result.get("target", {}).get("commit"),
        "stem_ai_version": result.get("stem_ai_version"),
        "score": result.get("score", {}).get("final_score"),
        "tier": result.get("score", {}).get("formal_tier"),
        "replication_score": result.get("replication_score"),
        "replication_tier": result.get("replication_tier"),
        "evidence_ledger_count": len(result.get("evidence_ledger", [])),
        "packet_profile": packet.get("packet_profile"),
        "packet_finding_count": len(findings),
        "allowed_finding_id_count": len(allowed_ids),
        "omitted_finding_count": packet.get("omitted_finding_count", 0),
        "provider_prompt_contract_present": bool(packet.get("provider_prompt_contract")),
        "citation_allowlist_exact": allowed_ids == [finding.get("finding_id") for finding in findings],
        "packet_bytes": _json_size(packet),
        "packet_file": packet_path.as_posix() if packet_path is not None else None,
        "top_packet_detectors": _top_detectors(findings),
    }


def response_validation_record(
    repo_entry: dict[str, Any],
    advisory: dict[str, Any],
    response_path: Path,
) -> dict[str, Any]:
    """Build a compact provider-response validation benchmark record."""
    return {
        "schema_version": PROVIDER_BENCHMARK_SCHEMA_VERSION,
        "record_type": "provider_response_validation",
        "repo": repo_entry.get("repo"),
        "local_name": repo_entry.get("local_name"),
        "provider": advisory.get("provider"),
        "model": advisory.get("model"),
        "status": advisory.get("status"),
        "invalid_citation_count": len(advisory.get("invalid_citations", [])),
        "missing_citation_item_count": len(advisory.get("missing_citation_items", [])),
        "prohibited_claim_count": len(advisory.get("prohibited_claims", [])),
        "errors": advisory.get("errors", []),
        "response_file": str(response_path),
        "response_sha256": advisory.get("response_contract", {}).get("source_sha256"),
        "network_called": advisory.get("response_contract", {}).get("network_called"),
        "citation_repair_attempted": advisory.get("response_contract", {}).get("citation_repair_attempted"),
    }


def packet_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize provider-packet readiness records."""
    if not records:
        return {
            "schema_version": PROVIDER_BENCHMARK_SCHEMA_VERSION,
            "record_count": 0,
            "all_citation_allowlists_exact": False,
        }
    return {
        "schema_version": PROVIDER_BENCHMARK_SCHEMA_VERSION,
        "record_count": len(records),
        "all_citation_allowlists_exact": all(bool(r.get("citation_allowlist_exact")) for r in records),
        "max_packet_finding_count": max(int(r.get("packet_finding_count") or 0) for r in records),
        "max_packet_bytes": max(int(r.get("packet_bytes") or 0) for r in records),
        "total_omitted_findings": sum(int(r.get("omitted_finding_count") or 0) for r in records),
        "tiers": _counts(str(r.get("tier")) for r in records),
        "replication_tiers": _counts(str(r.get("replication_tier")) for r in records),
    }


def _json_size(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _top_detectors(findings: list[dict[str, Any]], limit: int = 8) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        detector = str(finding.get("detector"))
        counts[detector] = counts.get(detector, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit])


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))
