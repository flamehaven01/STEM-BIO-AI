# Advisory Runtime Boundary

Version: 1.8.3
Status: Public operational note for `stem advisory call`

---

## Purpose

`stem advisory packet` and `stem advisory validate` are deterministic local contract operations.

`stem advisory call` is different. It is the explicit runtime boundary where a downstream provider adapter may be invoked. In v1.8.3, this mode exists to make the boundary visible and enforce its security contract before real provider execution is attached.

---

## What `stem advisory call` Does In v1.8.3

- builds the same provider-budgeted advisory input packet
- exports provider request metadata
- exports logging and redaction policy metadata
- exports child-env allowlist summary
- marks network intent explicitly
- keeps `network_called = false` unless a future adapter actually performs the call

If no adapter is implemented for the selected provider, the runtime returns:

- `status = error`
- `errors = ["adapter_not_implemented"]`

This is intentional. The mode exists to separate the trust boundary before a live adapter is turned on.

---

## Security Controls In This Mode

### 1. Explicit opt-in

Provider-call intent is never implicit. Users must choose:

```bash
stem advisory call /path/to/repo
```

### 2. Centralized redaction

Known secret patterns are scrubbed from:

- exception text
- advisory payload objects
- JSON artifacts
- Markdown artifacts
- explain artifacts

### 3. Logging policy

The runtime exports a machine-readable logging policy. It allows metadata such as:

- provider
- model
- base_url
- network_mode
- api_key_present
- api_key_env_var

It forbids:

- raw API key values
- authorization headers
- raw request bodies
- raw response bodies
- full environment dumps

### 4. Child environment allowlist

Future adapters must not inherit the full parent environment. The runtime prepares an allowlist summary containing only:

- base OS/runtime variables needed for child execution
- shared advisory config variables
- the selected provider key variable only

### 5. Artifact pre-write sanitization

Artifacts are sanitized before write. This is the last boundary if upstream redaction misses something.

---

## What This Mode Does Not Yet Do

v1.8.3 does **not** ship a live provider adapter.

That means:

- no OpenAI API call
- no Anthropic API call
- no Gemini API call
- no Ollama request
- no local-runtime inference call

The current release hardens the boundary first. Real adapter execution belongs to the next runtime step.

---

## Recommended Operator Use

1. Run the deterministic scan.
2. Export `stem advisory packet`.
3. Review `provider_request`, `packet_contract`, and `contract_schemas`.
4. Use `stem advisory call` only when you need the explicit runtime boundary metadata.
5. Validate any downstream provider output with `stem advisory check-response <repo> --response FILE`.

This keeps deterministic scoring, provider invocation intent, and response validation as separate operational lanes.







