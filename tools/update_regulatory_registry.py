"""
Regulatory Registry Update Tool
================================
Reads YAML metadata files from references/_registry_entries/ and merges
managed entries into docs/regulatory_basis_registry.v1.json.

Usage:
    python tools/update_regulatory_registry.py [--dry-run] [--check]

Options:
    --dry-run   Print diff without writing
    --check     Exit non-zero if registry is out of sync (for CI)

Workflow:
1. User converts regulatory PDF to MD, places in references/
2. User creates/updates references/_registry_entries/<id>.yaml
3. Run this script
4. Verify docs/regulatory_basis_registry.v1.json
5. If new requirement_ids needed, update stem_ai/regulatory_traceability.py
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

_ROOT = Path(__file__).resolve().parent.parent
_ENTRIES_DIR = _ROOT / "references" / "_registry_entries"
_REGISTRY_PATH = _ROOT / "docs" / "regulatory_basis_registry.v1.json"

_MANAGED_FIELD = "managed_by_update_script"


def _load_yaml_entries() -> list[dict]:
    entries = []
    for path in sorted(_ENTRIES_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            entry = yaml.safe_load(f)
        if not isinstance(entry, dict) or not entry.get("id"):
            print(f"WARN: skipping {path.name} (missing id)")
            continue
        entries.append(entry)
    return entries


def _yaml_to_registry_source(entry: dict) -> dict:
    """Convert YAML entry to registry source dict."""
    return {
        "id": entry["id"],
        "jurisdiction": entry.get("jurisdiction", "unknown"),
        "title": entry.get("title", ""),
        "short_label": entry.get("short_label", entry.get("title", "")),
        "display_label": entry.get("display_label", entry.get("title", "")),
        "status": entry.get("status", "unknown"),
        "published_date": entry.get("published_date"),
        "effective_date": entry.get("effective_date"),
        "source_file": entry.get("source_file"),
        "url": entry.get("source_url"),
        "used_for": entry.get("used_for", []),
        "sections": entry.get("sections", {}),
        "notes": (entry.get("notes") or "").strip(),
        _MANAGED_FIELD: True,
    }


def _update_registry(registry: dict, yaml_entries: list[dict]) -> tuple[dict, list[str]]:
    """Merge YAML entries into registry sources. Returns (updated_registry, change_log)."""
    sources = registry.get("sources", [])
    source_index = {s["id"]: i for i, s in enumerate(sources)}
    changes: list[str] = []

    for entry in yaml_entries:
        new_source = _yaml_to_registry_source(entry)
        entry_id = entry["id"]
        if entry_id in source_index:
            old = sources[source_index[entry_id]]
            if old != new_source:
                sources[source_index[entry_id]] = new_source
                changes.append(f"UPDATED: {entry_id}")
        else:
            sources.append(new_source)
            changes.append(f"ADDED: {entry_id}")

    registry["sources"] = sources
    return registry, changes


def _build_display_note(sources: list[dict]) -> dict:
    """Rebuild display_note body_line_1 from sources that have an explicit label.

    Only sources with display_label or short_label are included — supplementary
    reference entries (timeline pages, umbrella URLs) without these fields are
    omitted from the human-facing note to keep it concise.
    display_label takes precedence because it carries contextual clarifiers
    (e.g. "Step 4, Jan 2026") that short_label intentionally omits.
    """
    jurisdiction_groups: dict[str, list[str]] = {}
    for s in sources:
        label = s.get("display_label") or s.get("short_label")
        if not label:
            continue
        j = s.get("jurisdiction", "other")
        jurisdiction_groups.setdefault(j, []).append(label)

    parts = []
    for j in ("EU", "US", "FDA", "ICH", "IMDRF"):
        if j in jurisdiction_groups:
            parts.append(", ".join(jurisdiction_groups[j]))
    for j, labels in jurisdiction_groups.items():
        if j not in ("EU", "US", "FDA", "ICH", "IMDRF"):
            parts.extend(labels)

    month = date.today().strftime("%B %Y")
    body = f"Aligned to current official source classes as of {month}: " + "; ".join(parts) + "."
    return {
        "title": "Regulatory basis note",
        "body_line_1": body,
        "body_line_2": "This is a traceability aid, not a compliance or clearance determination.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Update regulatory basis registry from YAML entries.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    yaml_entries = _load_yaml_entries()
    if not yaml_entries:
        print("No YAML entries found in", _ENTRIES_DIR)
        return 0

    with _REGISTRY_PATH.open(encoding="utf-8") as f:
        registry = json.load(f)

    updated, changes = _update_registry(registry, yaml_entries)
    if not changes:
        print("Registry already up to date.")
        return 0

    today = date.today().strftime("%B %Y")
    updated["as_of"] = today
    updated["display_note"] = _build_display_note(updated["sources"])

    if args.dry_run or args.check:
        print(f"Changes ({len(changes)}):")
        for c in changes:
            print(f"  {c}")
        if args.check:
            return 1 if changes else 0
        return 0

    with _REGISTRY_PATH.open("w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Registry updated ({len(changes)} changes):")
    for c in changes:
        print(f"  {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
