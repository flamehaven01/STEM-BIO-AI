from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from .redaction import redact_text


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
PROVIDER_SECRET_POLICY_VERSION = "stem-ai-secret-policy-v1.5"
_GENERIC_API_KEY_ENV = "STEM_AI_ADVISORY_API_KEY"
_PROVIDER_API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openai_compatible": "OPENAI_COMPATIBLE_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    "local_runtime": "LOCAL_RUNTIME_API_KEY",
}
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
_SECRET_PATTERNS = (
    "sk-",
    "ghp_",
    "AIza",
    "AKIA",
)


@dataclass(frozen=True)
class AdvisoryProviderConfig:
    provider: str
    model: str | None
    base_url: str | None
    api_key_present: bool
    api_key_env_var: str | None
    secret_source: str
    timeout_sec: int
    max_tokens: int
    network_mode: str
    runtime: str | None = None


def load_provider_config(env: Mapping[str, str] | None = None) -> AdvisoryProviderConfig:
    """Load provider-neutral advisory configuration without exposing secrets."""
    values = os.environ if env is None else env
    provider = values.get("STEM_AI_ADVISORY_PROVIDER", "none").strip().lower() or "none"
    if provider not in SUPPORTED_ADVISORY_PROVIDERS:
        allowed = ", ".join(SUPPORTED_ADVISORY_PROVIDERS)
        raise ValueError(f"Unsupported advisory provider: {provider}. Expected one of: {allowed}")
    api_key, api_key_env_var = _provider_api_key(provider, values)
    base_url = _none_if_blank(values.get("STEM_AI_ADVISORY_BASE_URL"))
    return AdvisoryProviderConfig(
        provider=provider,
        model=_none_if_blank(values.get("STEM_AI_ADVISORY_MODEL")),
        base_url=base_url,
        api_key_present=bool(api_key),
        api_key_env_var=api_key_env_var,
        secret_source=_secret_source(api_key_env_var, api_key),
        timeout_sec=_positive_int(values.get("STEM_AI_ADVISORY_TIMEOUT_SEC"), DEFAULT_TIMEOUT_SEC),
        max_tokens=_positive_int(values.get("STEM_AI_ADVISORY_MAX_TOKENS"), DEFAULT_MAX_TOKENS),
        network_mode=_network_mode(provider, base_url),
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
        "base_url": redact_secret_text(config.base_url),
        "api_key_present": config.api_key_present,
        "api_key_env_var": config.api_key_env_var,
        "secret_source": config.secret_source,
        "timeout_sec": config.timeout_sec,
        "max_tokens": config.max_tokens,
        "network_mode": config.network_mode,
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
    request["base_url_validation"] = validation["base_url_validation"]
    request["secret_policy"] = provider_secret_policy()
    request["env_contract"] = provider_env_contract()
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
            "api_key_env_var": {"type": ["string", "null"]},
            "secret_source": {"type": ["string", "null"]},
            "timeout_sec": {"type": "integer", "minimum": 1},
            "max_tokens": {"type": "integer", "minimum": 1},
            "network_mode": {"type": ["string", "null"]},
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
        "base_url": redact_secret_text(_none_if_blank(_string_or_none(payload.get("base_url")))),
        "api_key_present": bool(payload.get("api_key_present", False)),
        "api_key_env_var": _none_if_blank(_string_or_none(payload.get("api_key_env_var"))),
        "secret_source": _none_if_blank(_string_or_none(payload.get("secret_source"))),
        "timeout_sec": timeout_sec,
        "max_tokens": max_tokens,
        "network_mode": _none_if_blank(_string_or_none(payload.get("network_mode"))),
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
    base_url_validation = _validate_base_url(normalized["provider"], normalized["base_url"])
    if base_url_validation["status"] != "valid":
        errors.append({
            "path": "base_url",
            "code": str(base_url_validation["code"]),
            "message": str(base_url_validation["message"]),
        })
    api_key_error = _api_key_error(normalized["provider"], normalized["api_key_present"], normalized["base_url"])
    if api_key_error is not None:
        errors.append(api_key_error)
    return {
        "schema_version": PROVIDER_REQUEST_SCHEMA_VERSION,
        "status": "invalid" if errors else "valid",
        "normalized": normalized,
        "base_url_validation": base_url_validation,
        "errors": errors,
    }


def provider_env_contract() -> dict[str, Any]:
    return {
        "provider_api_keys": dict(_PROVIDER_API_KEY_ENV),
        "generic_fallback": _GENERIC_API_KEY_ENV,
        "shared": {
            "provider": "STEM_AI_ADVISORY_PROVIDER",
            "model": "STEM_AI_ADVISORY_MODEL",
            "base_url": "STEM_AI_ADVISORY_BASE_URL",
            "timeout_sec": "STEM_AI_ADVISORY_TIMEOUT_SEC",
            "max_tokens": "STEM_AI_ADVISORY_MAX_TOKENS",
            "runtime": "STEM_AI_ADVISORY_RUNTIME",
        },
    }


def provider_secret_policy() -> dict[str, Any]:
    return {
        "schema_version": PROVIDER_SECRET_POLICY_VERSION,
        "rules": [
            "Use provider-specific environment variables or the generic fallback only.",
            "Do not pass provider secrets on CLI arguments.",
            "Do not write provider secrets to audit artifacts, JSON packets, Markdown, or PDFs.",
            "Cloud providers require https endpoints; plain http is limited to localhost/127.0.0.1/::1.",
            "Base URLs with embedded credentials are rejected.",
        ],
        "redaction_patterns": list(_SECRET_PATTERNS),
    }


def redact_secret_text(value: str | None) -> str | None:
    if value is None:
        return None
    redacted = redact_text(value) or ""
    for prefix in _SECRET_PATTERNS:
        if prefix in redacted:
            index = redacted.find(prefix)
            suffix = redacted[index + len(prefix):]
            tail = suffix[:4] if suffix else ""
            redacted = f"{redacted[:index]}{prefix}REDACTED{tail and '...' + tail}"
    if "://" in redacted and " " not in redacted:
        parsed = urlparse(redacted)
        if parsed.username or parsed.password:
            host = parsed.hostname or ""
            port = f":{parsed.port}" if parsed.port else ""
            path = parsed.path or ""
            redacted = f"{parsed.scheme}://redacted-user@{host}{port}{path}"
            if parsed.query:
                redacted = f"{redacted}?{parsed.query}"
    return redacted


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


def _provider_api_key(provider: str, values: Mapping[str, str]) -> tuple[str | None, str | None]:
    if provider == "none":
        return None, None
    specific = _PROVIDER_API_KEY_ENV.get(provider)
    if specific is not None:
        secret = _none_if_blank(values.get(specific))
        if secret is not None:
            return secret, specific
    fallback = _none_if_blank(values.get(_GENERIC_API_KEY_ENV))
    if fallback is not None:
        return fallback, _GENERIC_API_KEY_ENV
    return None, specific


def _secret_source(api_key_env_var: str | None, api_key: str | None) -> str:
    if api_key_env_var is None:
        return "not_required"
    if api_key is None:
        return "missing"
    if api_key_env_var == _GENERIC_API_KEY_ENV:
        return "generic_env"
    return "provider_env"


def _network_mode(provider: str, base_url: str | None) -> str:
    if provider == "none":
        return "offline"
    if provider == "local_runtime":
        return "in_process"
    if provider == "ollama":
        return "local_server"
    if base_url is not None and _is_local_url(base_url):
        return "local_server"
    return "remote_https"


def _api_key_error(provider: str, api_key_present: bool, base_url: str | None) -> dict[str, str] | None:
    if provider in {"openai", "anthropic", "gemini"} and not api_key_present:
        return {
            "path": "api_key_present",
            "code": "missing_api_key",
            "message": "Selected provider requires an API key in environment variables.",
        }
    if provider == "openai_compatible" and not api_key_present and not _is_local_url(base_url):
        return {
            "path": "api_key_present",
            "code": "missing_api_key",
            "message": "Remote openai_compatible endpoints require an API key in environment variables.",
        }
    return None


def _validate_base_url(provider: str, base_url: str | None) -> dict[str, str | None]:
    if base_url is None:
        return {"status": "valid", "code": None, "message": None}
    parsed = urlparse(base_url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return {
            "status": "invalid",
            "code": "invalid_base_url",
            "message": "Base URL must include http/https scheme and host.",
        }
    if parsed.username or parsed.password:
        return {
            "status": "invalid",
            "code": "embedded_credentials_forbidden",
            "message": "Base URL must not contain embedded credentials.",
        }
    if parsed.scheme == "http" and not _is_local_url(base_url):
        return {
            "status": "invalid",
            "code": "http_requires_localhost",
            "message": "Plain http is restricted to localhost, 127.0.0.1, or ::1.",
        }
    if provider in {"openai", "anthropic", "gemini"} and parsed.scheme != "https":
        return {
            "status": "invalid",
            "code": "https_required",
            "message": "Cloud providers require an https base URL.",
        }
    return {"status": "valid", "code": None, "message": None}


def _is_local_url(base_url: str | None) -> bool:
    if base_url is None:
        return False
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    return host in _LOCAL_HOSTS


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
