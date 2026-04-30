from __future__ import annotations

from typing import Any

from .advisory_contract import ADVISORY_SCHEMA_VERSION, build_advisory_input, validate_advisory_output
from .advisory_providers import load_provider_config, provider_handoff_metadata


ADVISORY_HARNESS_MODES = ("mock-valid", "mock-invalid", "mock-error", "mock-timeout")


class AdvisoryAdapterError(RuntimeError):
    """Raised when an advisory adapter fails before output validation."""


class AdvisoryAdapterTimeout(TimeoutError):
    """Raised when an advisory adapter exceeds its configured budget."""


def run_advisory_harness(result: dict[str, Any], mode: str) -> dict[str, Any]:
    """Run deterministic no-network adapter contract fixtures for v1.4.x hardening."""
    if mode not in ADVISORY_HARNESS_MODES:
        raise ValueError(f"Unsupported advisory harness mode: {mode}")
    config = load_provider_config()
    packet = build_advisory_input(result)
    packet["provider_request"] = provider_handoff_metadata(config)
    try:
        draft = _mock_adapter_output(result, packet, mode)
    except AdvisoryAdapterTimeout as exc:
        return _adapter_error(result, mode, "timeout", str(exc))
    except AdvisoryAdapterError as exc:
        return _adapter_error(result, mode, "adapter_error", str(exc))
    advisory = validate_advisory_output(result, draft)
    advisory["adapter_contract"] = {
        "mode": mode,
        "provider_request": packet["provider_request"],
        "citation_repair_attempted": False,
        "network_called": False,
    }
    return advisory


def _mock_adapter_output(result: dict[str, Any], packet: dict[str, Any], mode: str) -> dict[str, Any]:
    cite = _first_packet_finding_id(packet)
    if mode == "mock-error":
        raise AdvisoryAdapterError("mock adapter failure")
    if mode == "mock-timeout":
        timeout = packet["provider_request"].get("timeout_sec")
        raise AdvisoryAdapterTimeout(f"mock adapter timeout after {timeout}s budget")
    if mode == "mock-invalid":
        return {
            "provider": "mock",
            "model": "contract-harness",
            "mode": "mock_invalid_output",
            "final_score": 100,
            "reviewer_notes": [
                {
                    "claim": "This repository is safe for clinical deployment.",
                    "severity": "info",
                    "cites": ["MOCK:NO_SUCH_FINDING:001"],
                    "recommended_action": "Use it clinically.",
                }
            ],
            "inspection_priorities": [
                {"priority": "high", "reason": "Missing citations should remain invalid.", "cites": []}
            ],
        }
    return {
        "provider": "mock",
        "model": "contract-harness",
        "mode": "mock_valid_output",
        "reviewer_notes": [
            {
                "claim": "Mock adapter requests human review of cited evidence.",
                "severity": "info",
                "cites": [cite],
                "recommended_action": "Inspect the cited finding in the evidence ledger.",
            }
        ],
        "inspection_priorities": [
            {
                "priority": "medium",
                "reason": "Confirm that the cited evidence is relevant to the review question.",
                "cites": [cite],
            }
        ],
    }


def _adapter_error(result: dict[str, Any], mode: str, error_type: str, message: str) -> dict[str, Any]:
    advisory = validate_advisory_output(result, {
        "provider": "mock",
        "model": "contract-harness",
        "mode": mode,
        "reviewer_notes": [],
        "inspection_priorities": [],
    })
    advisory.update({
        "schema_version": ADVISORY_SCHEMA_VERSION,
        "provider": "mock",
        "model": "contract-harness",
        "mode": mode,
        "status": "error",
        "errors": [error_type],
        "adapter_error": {"type": error_type, "message": message},
        "adapter_contract": {
            "mode": mode,
            "provider_request": provider_handoff_metadata(load_provider_config()),
            "citation_repair_attempted": False,
            "network_called": False,
        },
    })
    return advisory


def _first_packet_finding_id(packet: dict[str, Any]) -> str:
    findings = packet.get("evidence_ledger", [])
    if not findings:
        raise AdvisoryAdapterError("advisory input packet has no evidence findings to cite")
    return str(findings[0]["finding_id"])
