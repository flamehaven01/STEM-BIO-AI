from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping


SUPPORTED_ADVISORY_PROVIDERS = (
    "none",
    "openai",
    "anthropic",
    "gemini",
    "openai_compatible",
    "ollama",
    "local_runtime",
)

DEFAULT_TIMEOUT_SEC = 60
DEFAULT_MAX_TOKENS = 2048
PROVIDER_REQUEST_SCHEMA_VERSION = "stem-ai-provider-request-v1.4"


@dataclass(frozen=True)
class AdvisoryProviderConfig:
    provider: str
    model: str | None
    base_url: str | None
    api_key_present: bool
    timeout_sec: int
    max_tokens: int
    runtime: str | None = None


def load_provider_config(env: Mapping[str, str] | None = None) -> AdvisoryProviderConfig:
    """Load provider-neutral advisory configuration without exposing secrets."""
    values = os.environ if env is None else env
    provider = values.get("STEM_AI_ADVISORY_PROVIDER", "none").strip().lower() or "none"
    if provider not in SUPPORTED_ADVISORY_PROVIDERS:
        allowed = ", ".join(SUPPORTED_ADVISORY_PROVIDERS)
        raise ValueError(f"Unsupported advisory provider: {provider}. Expected one of: {allowed}")
    return AdvisoryProviderConfig(
        provider=provider,
        model=_none_if_blank(values.get("STEM_AI_ADVISORY_MODEL")),
        base_url=_none_if_blank(values.get("STEM_AI_ADVISORY_BASE_URL")),
        api_key_present=bool(_none_if_blank(values.get("STEM_AI_ADVISORY_API_KEY"))),
        timeout_sec=_positive_int(values.get("STEM_AI_ADVISORY_TIMEOUT_SEC"), DEFAULT_TIMEOUT_SEC),
        max_tokens=_positive_int(values.get("STEM_AI_ADVISORY_MAX_TOKENS"), DEFAULT_MAX_TOKENS),
        runtime=_none_if_blank(values.get("STEM_AI_ADVISORY_RUNTIME")),
    )


def provider_registry() -> list[dict[str, object]]:
    """Return the provider classes reserved by the v1.4 advisory substrate."""
    return [
        _provider("none", "offline_stub", network=False, implemented=True),
        _provider("openai", "cloud_native", network=True, implemented=False),
        _provider("anthropic", "cloud_native", network=True, implemented=False),
        _provider("gemini", "cloud_native", network=True, implemented=False),
        _provider("openai_compatible", "openai_compatible", network=True, implemented=False),
        _provider("ollama", "local_server", network=True, implemented=False),
        _provider("local_runtime", "local_runtime", network=False, implemented=False),
    ]


def provider_handoff_metadata(config: AdvisoryProviderConfig) -> dict[str, object]:
    """Build a secret-free handoff block for an advisory input packet."""
    request = {
        "provider": config.provider,
        "model": config.model,
        "base_url": config.base_url,
        "api_key_present": config.api_key_present,
        "timeout_sec": config.timeout_sec,
        "max_tokens": config.max_tokens,
        "runtime": config.runtime,
        "registry": provider_registry(),
        "status": "offline_ready" if config.provider == "none" else "adapter_not_implemented",
    }
    validation = validate_provider_request_args(request)
    request["request_schema_version"] = PROVIDER_REQUEST_SCHEMA_VERSION
    request["request_schema"] = provider_request_schema()
    request["args_validation"] = {
        "status": validation["status"],
        "error_count": len(validation["errors"]),
    }
    return request


def provider_request_schema() -> dict[str, Any]:
    return {
        "schema_version": PROVIDER_REQUEST_SCHEMA_VERSION,
        "type": "object",
        "required": ["provider", "api_key_present", "timeout_sec", "max_tokens"],
        "properties": {
            "provider": {"type": "string", "enum": list(SUPPORTED_ADVISORY_PROVIDERS)},
            "model": {"type": ["string", "null"]},
            "base_url": {"type": ["string", "null"]},
            "api_key_present": {"type": "boolean"},
            "timeout_sec": {"type": "integer", "minimum": 1},
            "max_tokens": {"type": "integer", "minimum": 1},
            "runtime": {"type": ["string", "null"]},
        },
        "additionalProperties": True,
    }


def validate_provider_request_args(payload: Mapping[str, object]) -> dict[str, Any]:
    timeout_sec, timeout_error = _coerce_positive_int(payload.get("timeout_sec"), DEFAULT_TIMEOUT_SEC)
    max_tokens, max_tokens_error = _coerce_positive_int(payload.get("max_tokens"), DEFAULT_MAX_TOKENS)
    normalized = {
        "provider": str(payload.get("provider", "none")).strip().lower() or "none",
        "model": _none_if_blank(_string_or_none(payload.get("model"))),
        "base_url": _none_if_blank(_string_or_none(payload.get("base_url"))),
        "api_key_present": bool(payload.get("api_key_present", False)),
        "timeout_sec": timeout_sec,
        "max_tokens": max_tokens,
        "runtime": _none_if_blank(_string_or_none(payload.get("runtime"))),
    }
    errors: list[dict[str, str]] = []
    if normalized["provider"] not in SUPPORTED_ADVISORY_PROVIDERS:
        errors.append({
            "path": "provider",
            "code": "unsupported_provider",
            "message": f"Expected one of: {', '.join(SUPPORTED_ADVISORY_PROVIDERS)}",
        })
    for key, error in (("timeout_sec", timeout_error), ("max_tokens", max_tokens_error)):
        if error is not None:
            errors.append({
                "path": key,
                "code": "expected_positive_int",
                "message": error,
            })
    return {
        "schema_version": PROVIDER_REQUEST_SCHEMA_VERSION,
        "status": "invalid" if errors else "valid",
        "normalized": normalized,
        "errors": errors,
    }


def _provider(name: str, provider_class: str, network: bool, implemented: bool) -> dict[str, object]:
    return {
        "provider": name,
        "provider_class": provider_class,
        "network_required": network,
        "implemented": implemented,
    }


def _none_if_blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _positive_int(raw: str | None, default: int) -> int:
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _coerce_positive_int(raw: object, default: int) -> tuple[int, str | None]:
    if raw is None:
        return default, None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default, "Value must be a positive integer."
    if value <= 0:
        return default, "Value must be a positive integer."
    return value, None
