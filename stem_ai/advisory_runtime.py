from __future__ import annotations

import os
from typing import Any, Mapping

from .advisory_contract import build_offline_advisory, build_provider_advisory_input
from .advisory_providers import (
    AdvisoryProviderConfig,
    load_provider_config,
    provider_handoff_metadata,
)
from .redaction import redact_object, redact_text, redaction_policy


ADVISORY_RUNTIME_SCHEMA_VERSION = "stem-ai-advisory-runtime-v1.5"
ADVISORY_LOG_POLICY_VERSION = "stem-ai-advisory-log-policy-v1.5"
_BASE_CHILD_ENV = ("PATH", "SYSTEMROOT", "WINDIR", "HOME", "USERPROFILE", "TMP", "TEMP")


def execute_advisory_call(
    result: dict[str, Any],
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    config = load_provider_config(env)
    packet = build_provider_advisory_input(result)
    packet["provider_request"] = provider_handoff_metadata(config)
    runtime = provider_call_runtime(config, env)
    if config.provider == "none":
        advisory = build_offline_advisory(result)
        advisory["mode"] = "provider_call_offline"
        advisory["provider_call"] = runtime
        return redact_object(advisory)
    advisory = build_offline_advisory(result)
    advisory.update({
        "provider": config.provider,
        "model": config.model,
        "mode": "provider_call",
        "status": "error",
        "errors": ["adapter_not_implemented"],
        "provider_call": runtime,
        "request_contract": {
            "packet_profile": packet.get("packet_profile"),
            "finding_count": len(packet.get("evidence_ledger", [])),
            "allowed_finding_id_count": len(packet.get("allowed_finding_ids", [])),
        },
        "response_error": {
            "type": "adapter_not_implemented",
            "message": "Explicit advisory call mode is enabled, but the selected provider adapter is not implemented in this release.",
        },
    })
    return redact_object(advisory)


def provider_call_runtime(
    config: AdvisoryProviderConfig,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    child_env = build_child_env_allowlist(config, env)
    return {
        "schema_version": ADVISORY_RUNTIME_SCHEMA_VERSION,
        "mode": "explicit_network_opt_in",
        "provider": config.provider,
        "model": config.model,
        "base_url": redact_text(config.base_url),
        "network_mode": config.network_mode,
        "network_intent": config.provider != "none",
        "network_called": False,
        "adapter_status": "offline_ready" if config.provider == "none" else "not_implemented",
        "log_policy": advisory_log_policy(),
        "redaction_policy": redaction_policy(),
        "child_env_allowlist": {
            "count": len(child_env),
            "keys": sorted(child_env.keys()),
        },
        "secrets_persisted": False,
    }


def advisory_log_policy() -> dict[str, Any]:
    return {
        "schema_version": ADVISORY_LOG_POLICY_VERSION,
        "logger_mode": "structured_metadata_only",
        "allowed_fields": [
            "provider",
            "model",
            "base_url",
            "network_mode",
            "api_key_present",
            "api_key_env_var",
            "secret_source",
            "timeout_sec",
            "max_tokens",
            "runtime",
        ],
        "forbidden_fields": [
            "api_key_value",
            "authorization_header",
            "raw_request_body",
            "raw_response_body",
            "full_environment_dump",
        ],
        "exception_sanitization": True,
        "artifact_sanitization": True,
    }


def build_child_env_allowlist(
    config: AdvisoryProviderConfig,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    allowed: dict[str, str] = {}
    for key in _BASE_CHILD_ENV:
        if key in values and values[key]:
            allowed[key] = values[key]
    for key in (
        "STEM_AI_ADVISORY_PROVIDER",
        "STEM_AI_ADVISORY_MODEL",
        "STEM_AI_ADVISORY_BASE_URL",
        "STEM_AI_ADVISORY_TIMEOUT_SEC",
        "STEM_AI_ADVISORY_MAX_TOKENS",
        "STEM_AI_ADVISORY_RUNTIME",
    ):
        if key in values and values[key]:
            allowed[key] = values[key]
    if config.api_key_env_var and values.get(config.api_key_env_var):
        allowed[config.api_key_env_var] = values[config.api_key_env_var]
    return allowed
