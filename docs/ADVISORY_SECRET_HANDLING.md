# Advisory Secret Handling

Version: 1.7.8
Status: Operational policy for provider-neutral advisory handoff

---

## Scope

This document covers how STEM BIO-AI handles provider configuration for advisory packet export and downstream provider runners.

The deterministic scanner itself does not call external provider APIs. The secret boundary still matters because provider-neutral handoff packets and future adapters must not normalize unsafe practices.

---

## Non-Negotiable Rules

1. Provider API keys must come from environment variables or an external secret store.
2. Provider API keys must never appear in CLI arguments.
3. Provider API keys must never be written to audit JSON, Markdown, PDF, or explain artifacts.
4. Provider handoff metadata may report `api_key_present` and the expected env-var name, but never the secret value.
5. Base URLs containing embedded credentials are invalid.
6. Cloud-provider overrides require `https`.
7. Plain `http` is restricted to `localhost`, `127.0.0.1`, or `::1`.
8. Real provider-call intent must be explicit via `stem advisory call`.

---

## Supported Environment Variables

### Shared

- `STEM_AI_ADVISORY_PROVIDER`
- `STEM_AI_ADVISORY_MODEL`
- `STEM_AI_ADVISORY_BASE_URL`
- `STEM_AI_ADVISORY_TIMEOUT_SEC`
- `STEM_AI_ADVISORY_MAX_TOKENS`
- `STEM_AI_ADVISORY_RUNTIME`

### Provider-Specific API Keys

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `OPENAI_COMPATIBLE_API_KEY`
- `OLLAMA_API_KEY`
- `LOCAL_RUNTIME_API_KEY`

### Generic Fallback

- `STEM_AI_ADVISORY_API_KEY`

STEM BIO-AI prefers the provider-specific variable first and falls back to `STEM_AI_ADVISORY_API_KEY` only when the provider-specific variable is absent.

---

## .env Policy

- `.env` and `.env.*` are ignored by Git.
- `.env.example` is committed as a names-only template.
- Real secrets belong in local untracked env files, CI/HF/host secret stores, or OS secret managers.

Committed example files must contain placeholders only.

---

## Artifact Boundary

The following artifacts must remain secret-free:

- `*_experiment_results.json`
- `*_advisory_input.json`
- `*_report.md`
- `*.pdf`
- `*_explain.txt`

Provider handoff metadata may include:

- `provider`
- `model`
- `base_url`
- `api_key_present`
- `api_key_env_var`
- `secret_source`
- `network_mode`
- `base_url_validation`
- `secret_policy`
- `env_contract`

It must not include any actual key value.

---

## Endpoint Policy

### Valid

- `https://api.openai.com/v1`
- `https://api.anthropic.com`
- `https://generativelanguage.googleapis.com`
- `http://localhost:11434`
- `http://127.0.0.1:8000/v1`

### Invalid

- `http://api.openai.com/v1`
- `http://10.0.0.4:8000/v1`
- `https://user:pass@example.com/v1`

---

## Recommended Operating Pattern

1. Generate deterministic audit output locally.
2. Export `stem advisory packet`.
3. Validate `provider_request.args_validation` and `provider_request.base_url_validation`.
4. Pass the packet to a downstream adapter only after the secret/env contract is satisfied.
5. Validate the provider response with `stem advisory check-response <repo> --response FILE`.

This keeps deterministic scoring and external provider execution on separate trust boundaries.

---

## Runtime Guardrails

`stem advisory call` is an explicit provider-call boundary. In v1.7.8 the runtime exports:

- centralized redaction policy
- adapter logging policy
- child-env allowlist summary
- network intent vs actual network-called flag

This keeps call intent observable even when a provider adapter is not yet implemented.

See also: [`docs/ADVISORY_RUNTIME.md`](ADVISORY_RUNTIME.md)







