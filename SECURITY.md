# Security Policy

STEM BIO-AI has two distinct trust boundaries:

- the default deterministic repository scanner
- the optional advisory/provider boundary

This file defines the practical security posture for both.

## Scope

The default `stem scan` path is local-first:

- it reads a local repository clone
- it does not require an API key
- it does not call an LLM in the scoring path
- it does not send repository contents to a third-party service

The advisory surface is different. It exists to make provider-call intent explicit and governed, not to silently blend external model behavior into deterministic scoring.

## Supported Security Surface

Security-relevant areas in this repository include:

- CLI entry points in `stem_ai/cli.py`
- repository scanning and evidence assembly in `stem_ai/scanner.py`
- advisory packet/export/validation paths in `stem_ai/advisory_*`
- redaction handling in `stem_ai/redaction.py`
- API and advisory contract documents in `docs/`

## What The Repository Does Not Claim

- A high evidence tier is not a security certification.
- A clean deterministic scan is not proof of clinical safety or regulatory readiness.
- Advisory documents and packets are not a substitute for secret-management policy.

## Safe Use Guidance

### Default scan mode

- run the scanner on local clones you control
- review generated evidence before acting on a tier decision
- treat HTML/PDF output as review artifacts, not source truth

### Advisory mode

- use only explicit advisory commands for provider-bound flows
- keep provider credentials in environment variables or your secret manager
- review [docs/ADVISORY_SECRET_HANDLING.md](docs/ADVISORY_SECRET_HANDLING.md) before enabling provider-bound workflows
- review [docs/ADVISORY_RUNTIME.md](docs/ADVISORY_RUNTIME.md) and [docs/API_CONTRACT.md](docs/API_CONTRACT.md) before trusting downstream response handling

## Reporting A Vulnerability

Do not open a public issue for a live security vulnerability.

Report security issues to the maintainer channel used by Flamehaven for private repository security handling. Include:

1. affected version or commit
2. reproduction steps
3. security impact
4. any proof-of-concept or logs needed to validate the report

## Verification Surface

Use the repository's concrete verification path after security-relevant changes:

```bash
pip install -e ".[pdf]"
python -m py_compile stem_ai/cli.py stem_ai/scanner.py stem_ai/render.py stem_ai/app.py
python -m pytest -q
python -m build
```

## Related Documents

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/ADVISORY_RUNTIME.md](docs/ADVISORY_RUNTIME.md)
- [docs/ADVISORY_SECRET_HANDLING.md](docs/ADVISORY_SECRET_HANDLING.md)
- [docs/API_CONTRACT.md](docs/API_CONTRACT.md)
- [docs/REGULATORY_MAPPING.md](docs/REGULATORY_MAPPING.md)
