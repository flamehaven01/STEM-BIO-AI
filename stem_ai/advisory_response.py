from __future__ import annotations

import hashlib
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .advisory_contract import ADVISORY_SCHEMA_VERSION, validate_advisory_output


def validate_advisory_response_file(result: dict[str, Any], response_path: Path) -> dict[str, Any]:
    """Validate a provider-produced advisory JSON response against the evidence contract."""
    raw = response_path.read_bytes()
    contract = _response_contract(response_path, raw)
    try:
        response = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, JSONDecodeError) as exc:
        return _response_error(result, contract, "response_parse_error", str(exc))
    if not isinstance(response, dict):
        return _response_error(result, contract, "response_not_object", "Advisory response JSON must be an object.")
    advisory = validate_advisory_output(result, response)
    advisory["response_contract"] = contract
    return advisory


def _response_error(
    result: dict[str, Any],
    contract: dict[str, Any],
    error_type: str,
    message: str,
) -> dict[str, Any]:
    advisory = validate_advisory_output(result, {
        "provider": "external_response",
        "model": None,
        "mode": "response_file_validation",
        "reviewer_notes": [],
        "inspection_priorities": [],
    })
    advisory.update({
        "schema_version": ADVISORY_SCHEMA_VERSION,
        "provider": "external_response",
        "model": None,
        "mode": "response_file_validation",
        "status": "error",
        "errors": [error_type],
        "response_error": {"type": error_type, "message": message},
        "response_contract": contract,
    })
    return advisory


def _response_contract(path: Path, raw: bytes) -> dict[str, Any]:
    return {
        "source_file": path.name,
        "source_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "byte_count": len(raw),
        "parser": "json",
        "citation_repair_attempted": False,
        "network_called": False,
    }
