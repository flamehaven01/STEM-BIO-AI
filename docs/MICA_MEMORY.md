# STEM BIO-AI MICA Memory Layer

Version: 1.5.8
Status: Operational reference for the active memory contract

---

## Purpose

The `memory/` directory is the MICA memory layer for STEM BIO-AI. It is not a generated cache
and it is not disposable release residue.

Its role is to:

- pin the active protocol state for agent sessions
- preserve versioned archive snapshots across releases
- keep drift rules, lessons, and operating playbooks aligned with the current release

The active memory layer is selected by `memory/mica.yaml`.

---

## Single Source Of Truth

`memory/mica.yaml` is the active loader contract.

It selects exactly three live files:

- archive JSON
- playbook markdown
- lessons markdown

For v1.5.8 the active set is:

- `memory/stem-ai.mica.v1.5.8.json`
- `memory/stem-ai-playbook.v1.5.8.md`
- `memory/stem-ai-lessons.v1.5.8.md`

Anything older in `memory/` is retained as archive history unless explicitly retired.

---

## Retention Policy

Historical memory snapshots are intentionally kept in Git.

Reason:

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
- any surface that hard-codes active memory filenames

---

## README And SKILL Relationship

There are two different entry surfaces:

- `README.md`: public project contract and operator-facing overview
- `SKILL.md`: agent-facing entry point and load order

They should not duplicate full memory contents. They should only point to the active contract.

Required linkage:

1. `README.md` links to this document for memory policy.
2. `SKILL.md` tells agents to load `memory/mica.yaml` first.
3. `SKILL.md` should prefer the files referenced by `mica.yaml` rather than hard-coding stale memory filenames.

---

## Release Checklist

When the release version changes and memory is updated:

1. Create new versioned memory snapshots from the previous active layer.
2. Update release-specific version strings inside the new snapshots.
3. Point `memory/mica.yaml` to the new active files.
4. Verify `SKILL.md` still follows `mica.yaml`.
5. Verify any README or docs references point to the current policy document.
6. Keep older snapshots unless there is an explicit archive-pruning decision.

---

## Sanity Checks

Minimum checks for the memory layer:

- `memory/mica.yaml` exists
- each layer path in `mica.yaml` exists
- the archive `project.version` matches the current release
- `SKILL.md` does not hard-code stale active memory filenames
- `README.md` links to the current MICA policy doc

---

## Non-Goals

The MICA layer does not:

- replace the public API contract
- replace `README.md`
- define score math by itself
- justify hiding old memory files from version control

It is an operational memory contract for agent sessions, not a substitute for the scanner's
public result schema.
