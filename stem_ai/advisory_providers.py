from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


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
    return {
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


def _positive_int(raw: str | None, default: int) -> int:
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default
