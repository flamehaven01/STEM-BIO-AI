# Audits Directory

`audits/` is retained for historical benchmark and reference artifacts.

What belongs here:

- versioned benchmark workspaces such as `benchmark-v1.3/`, `benchmark-v1.4/`, and `benchmark-v1.5/`
- legacy public reference artifacts that are intentionally kept for release-history context

What does not belong here going forward:

- routine local scan output
- one-off dogfooding runs
- temporary comparison runs
- external inspection scratch artifacts

Current live CLI output goes to:

- `stem_output/<repo_slug>/`

This keeps historical benchmark material separate from routine generated scan output.
