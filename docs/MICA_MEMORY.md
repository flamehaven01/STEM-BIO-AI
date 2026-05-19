# STEM BIO-AI MICA Memory Layer

Version: 1.7.8  
MICA Contract: 0.2.4  
Status: Active operational memory contract

---

## Purpose

The `memory/` directory is the MICA memory layer for STEM BIO-AI.

It is not a generated cache.
It is not disposable release residue.
It is not a substitute for the public result schema.

Its role is to:

- pin the active protocol state for agent sessions
- preserve versioned archive snapshots across releases
- keep drift rules, lessons, and operating playbooks aligned with the current release
- provide a portable invocation contract for session startup
- provide package-contract self-tests through the MICA PCT runner

The active memory layer is selected by [memory/mica.yaml](../memory/mica.yaml).

---

## What Changed In The 0.2.4 Uplift

STEM BIO-AI already had a working memory package before this upgrade.

This release does **not** replace the archive model.
It upgrades the package to the non-breaking `MICA v0.2.4` runtime and validation contract.

That means:

- `memory/mica.yaml` now declares `mica_spec: "0.2.4"`
- the active archive JSON now carries `mica_spec` / `mica_schema_version` `0.2.4`
- `tools/mica_pct.py` is available for package validation
- `tools/mica_runtime.py` is available for portable runtime summaries
- `invocation_protocol.hook_output` is now declared in `memory/mica.yaml`
- DI `binding` remains a progressive maturity feature, not a forced rewrite

This is a runtime/contract uplift, not a wholesale archive redesign.

---

## Single Source Of Truth

`memory/mica.yaml` is the active composition contract.

It selects exactly three live files:

- archive JSON
- playbook markdown
- lessons markdown

For the current release the active set is:

- `memory/stem-ai.mica.v1.7.8.json`
- `memory/stem-ai-playbook.v1.7.8.md`
- `memory/stem-ai-lessons.v1.7.8.md`

Anything older in `memory/` is retained as archive history unless explicitly retired.

---

## Runtime Tooling

Two runtime tools are now part of the package:

- `python tools/mica_pct.py .`
- `python tools/mica_runtime.py . --format text`

Recommended session-start sequence:

1. load `memory/mica.yaml`
2. run `python tools/mica_pct.py .`
3. run `python tools/mica_runtime.py . --format text`
4. load the archive referenced by `mica.yaml`
5. load the playbook referenced by `mica.yaml`
6. load lessons on demand

Expected posture:

- PCT-001 through PCT-004 must be clean
- PCT-007 / PCT-009 should indicate a closed package
- PCT-010 WARN is acceptable during progressive DI binding rollout
- PCT-011 WARN is acceptable only when a declared `lesson_ref` path has not yet been repaired

---

## DI Binding Maturity Boundary

MICA `v0.2.4` adds stronger support for DI binding, but STEM BIO-AI is using it in the intended conservative way.

Critical design invariants are **not** being mass-rewritten with speculative binding blocks.

The rule is:

- add `binding.origin_episode` when a real violation or operating lesson exists
- add `binding.lesson_ref` only when the referenced lesson file actually exists
- do not fabricate incident lineage just to satisfy a schema

This keeps the memory layer evidence-based rather than ceremonial.

---

## Hook Output Policy

The active `invocation_protocol` keeps:

- `primary_pattern: readme_protocol`

So normal STEM BIO-AI sessions do **not** require a hook-capable runtime.

However, `hook_output` is now declared for forward portability:

```yaml
hook_output:
  max_di_lines: 3
  di_filter: violations_only
```

Meaning:

- future hook adapters can emit terse summaries
- low-signal stable DIs do not flood the session preamble
- violated critical invariants stay visible first

This is a portability improvement, not a change to scan semantics.

---

## README And SKILL Relationship

There are two different entry surfaces:

- `README.md`: public project contract and operator-facing overview
- `SKILL.md`: agent-facing entry point and load order

They should not duplicate full memory contents.
They should point to the active contract.

Required linkage:

1. `README.md` links here for memory policy.
2. `SKILL.md` tells agents to load `memory/mica.yaml` first.
3. `SKILL.md` should prefer the files referenced by `mica.yaml` rather than hard-coding stale filenames.
4. `SKILL.md` should reference the current PCT range and current `[MICA READY]` output surface.

---

## Retention Policy

Historical memory snapshots are intentionally kept in Git.

Reasons:

- they are part of release provenance
- they preserve drift history and patch rationale
- they allow exact reconstruction of prior agent operating state

Because of that, `memory/` should not be added to `.gitignore`.

What stays stable:

- old versioned memory files remain as archive
- only `memory/mica.yaml` decides what is active

What changes on each release-memory rotation:

- `memory/mica.yaml`
- the new versioned archive/playbook/lessons trio
- any doc or skill surface that hard-codes active memory filenames

---

## Release Checklist

When the release version changes and memory is updated:

1. create new versioned memory snapshots from the previous active layer
2. update release-specific version strings inside the new snapshots
3. point `memory/mica.yaml` to the new active files
4. verify `SKILL.md` still follows `mica.yaml`
5. run `python tools/mica_pct.py .`
6. run `python tools/mica_runtime.py . --format text`
7. verify README and docs still point to the current memory policy
8. keep older snapshots unless there is an explicit archive-pruning decision

---

## Sanity Checks

Minimum checks for the memory layer:

- `memory/mica.yaml` exists
- each required layer path in `mica.yaml` exists
- the archive `project.version` matches the current release
- `mica_spec` aligns between `mica.yaml` and the active archive
- `SKILL.md` does not hard-code stale active memory filenames
- `README.md` links to the current MICA policy doc
- `python tools/mica_pct.py .` returns a closed package state

---

## Non-Goals

The MICA layer does not:

- replace the public API contract
- replace `README.md`
- define score math by itself
- justify hiding old memory files from version control
- turn the scanner into a runtime enforcement engine

It is an operational memory contract for agent sessions, not a substitute for the scanner's public result schema.
