from __future__ import annotations

import re
from typing import Any, Mapping


REDACTION_POLICY_VERSION = "stem-ai-redaction-v1.5"
REDACTED = "[REDACTED]"
_SECRET_REGEXES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{8,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{8,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{8,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{8,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*=\s*([^\s\"'`,;]+)"),
    re.compile(r"(?i)\b(x-api-key)\s*:\s*([^\s\"'`,;]+)"),
)


def redaction_policy() -> dict[str, Any]:
    return {
        "schema_version": REDACTION_POLICY_VERSION,
        "artifact_behavior": "sanitize_before_write",
        "exception_behavior": "sanitize_before_report",
        "patterns": [pattern.pattern for pattern in _SECRET_REGEXES],
    }


def redact_text(value: str | None) -> str | None:
    if value is None:
        return None
    redacted = value
    for pattern in _SECRET_REGEXES:
        redacted = pattern.sub(_replacement, redacted)
    return redacted


def redact_object(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_object(item) for item in value]
    if isinstance(value, tuple):
        return [redact_object(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): redact_object(item) for key, item in value.items()}
    return value


def secret_scan(text: str) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for pattern in _SECRET_REGEXES:
        for match in pattern.finditer(text):
            hits.append({
                "pattern": pattern.pattern,
                "match": redact_text(match.group(0)) or REDACTED,
            })
    return {
        "schema_version": REDACTION_POLICY_VERSION,
        "status": "detected" if hits else "clean",
        "hit_count": len(hits),
        "hits": hits[:20],
    }


def sanitize_artifact_text(text: str) -> tuple[str, dict[str, Any]]:
    scan = secret_scan(text)
    return redact_text(text) or "", scan


def _replacement(match: re.Match[str]) -> str:
    prefix = match.group(1) if match.lastindex and match.lastindex >= 1 else None
    if prefix is not None and prefix.lower() in {"api_key", "apikey", "api-key", "token", "secret", "password", "x-api-key"}:
        return f"{prefix}={REDACTED}"
    token = match.group(0)
    if token.lower().startswith("bearer "):
        return "Bearer [REDACTED]"
    if token.lower().startswith("x-api-key"):
        return "x-api-key: [REDACTED]"
    return REDACTED
