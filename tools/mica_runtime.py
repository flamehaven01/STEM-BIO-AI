#!/usr/bin/env python3
"""
MICA runtime summary utility.

Usage:
    python tools/mica_runtime.py [project_root] --format text
    python tools/mica_runtime.py [project_root] --format hook
    python tools/mica_runtime.py [project_root] --format json

Purpose:
- resolve MICA package state
- emit portable runtime summaries
- surface DI binding evidence (v0.2.3)
- respect hook_output policy for volume control (v0.2.4)
- keep hook adapters thin
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import]
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except ImportError:
        return minimal_yaml_parse(path)


def minimal_yaml_parse(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list: list[Any] | None = None
    current_item: dict[str, Any] | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            value = stripped[2:].strip()
            if current_list is None:
                current_list = []
            if ":" in value:
                k, v = value.split(":", 1)
                current_item = {k.strip(): v.strip().strip('"')}
                current_list.append(current_item)
            else:
                current_item = None
                current_list.append(value.strip('"'))
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if value == "":
            current_list = []
            data[key] = current_list
            current_item = None
        else:
            current_list = None
            current_item = None
            data[key] = value
    return data


def find_mica_yaml(project_root: Path) -> Path | None:
    for rel in ("mica.yaml", "memory/mica.yaml"):
        p = project_root / rel
        if p.exists():
            return p
    return None


def find_legacy_archive(project_root: Path) -> Path | None:
    memory_dir = project_root / "memory"
    if not memory_dir.exists():
        return None
    matches = sorted(memory_dir.glob("*.mica.*.json"))
    return matches[0] if matches else None


def detect_state(project_root: Path) -> tuple[str, Path | None, Path | None]:
    mica_yaml = find_mica_yaml(project_root)
    if mica_yaml:
        return ("INVOCATION_MODE", mica_yaml, None)
    archive = find_legacy_archive(project_root)
    if archive:
        return ("LEGACY_MODE", None, archive)
    return ("INACTIVE", None, None)


def resolve_paths(
    project_root: Path, mica_yaml_path: Path
) -> tuple[dict[str, Any], Path | None, Path | None]:
    yd = load_yaml(mica_yaml_path)
    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
    archive_path = None
    playbook_path = None
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        rel = layer.get("path")
        if not isinstance(rel, str):
            continue
        if layer.get("name") == "archive":
            archive_path = project_root / rel
        elif layer.get("name") == "playbook":
            playbook_path = project_root / rel
    return yd, archive_path, playbook_path


def load_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def count_invariants(
    archive: dict[str, Any],
) -> tuple[int, int, list[dict[str, Any]]]:
    dis = archive.get("design_invariants", [])
    if not isinstance(dis, list):
        return (0, 0, [])
    normalized = [d for d in dis if isinstance(d, dict)]
    crit = sum(1 for d in normalized if d.get("severity") == "critical")
    high = sum(1 for d in normalized if d.get("severity") == "high")
    return crit, high, normalized


def _extract_critical_invariants(dis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for d in dis:
        if d.get("severity") != "critical":
            continue
        entry: dict[str, Any] = {"id": d.get("id"), "label": d.get("label")}
        binding = d.get("binding")
        if isinstance(binding, dict):
            entry["binding"] = binding
        result.append(entry)
    return result


def pct_status(project_root: Path, tools_dir: Path) -> str:
    pct_path = tools_dir / "mica_pct.py"
    if not pct_path.exists():
        return "UNKNOWN"
    state, mica_yaml, archive = detect_state(project_root)
    if state == "INACTIVE":
        return "INACTIVE"
    if state == "LEGACY_MODE":
        return "LEGACY"
    if not mica_yaml:
        return "INCOMPLETE"
    yd, archive_path, playbook_path = resolve_paths(project_root, mica_yaml)
    required = {"mica_spec", "mode", "layers"}
    if not required <= set(yd.keys()):
        return "INCOMPLETE"
    if archive_path is None or playbook_path is None:
        return "INCOMPLETE"
    if not archive_path.exists() or not playbook_path.exists():
        return "INCOMPLETE"
    return "CLOSED"


def build_summary(project_root: Path) -> dict[str, Any]:
    state, mica_yaml, legacy_archive = detect_state(project_root)
    tools_dir = Path(__file__).resolve().parent
    base: dict[str, Any] = {"state": state, "project_root": str(project_root)}

    if state == "INACTIVE":
        base.update({
            "name": None, "version": None, "mode": None, "pattern": None,
            "pct": "INACTIVE", "critical_count": 0, "high_count": 0,
            "critical_invariants": [], "last_updated": None, "hook_output": {},
        })
        return base

    if state == "LEGACY_MODE":
        archive = load_json(legacy_archive)
        crit, high, dis = count_invariants(archive)
        base.update({
            "name": archive.get("project", {}).get("name") if isinstance(archive.get("project"), dict) else None,
            "version": archive.get("project", {}).get("version") if isinstance(archive.get("project"), dict) else None,
            "mode": None, "pattern": "legacy", "pct": "LEGACY",
            "critical_count": crit, "high_count": high,
            "critical_invariants": _extract_critical_invariants(dis),
            "last_updated": archive.get("operation_meta", {}).get("last_updated") if isinstance(archive.get("operation_meta"), dict) else None,
            "hook_output": {},
        })
        return base

    assert mica_yaml is not None
    yd, archive_path, _playbook_path = resolve_paths(project_root, mica_yaml)
    archive = load_json(archive_path)
    crit, high, dis = count_invariants(archive)
    inv = yd.get("invocation_protocol") if isinstance(yd.get("invocation_protocol"), dict) else {}
    hook_output_raw = inv.get("hook_output") if isinstance(inv.get("hook_output"), dict) else {}
    base.update({
        "name": yd.get("name") or (archive.get("project", {}).get("name") if isinstance(archive.get("project"), dict) else None),
        "version": archive.get("project", {}).get("version") if isinstance(archive.get("project"), dict) else None,
        "mode": yd.get("mode"),
        "pattern": inv.get("primary_pattern", "readme_protocol"),
        "pct": pct_status(project_root, tools_dir),
        "critical_count": crit, "high_count": high,
        "critical_invariants": _extract_critical_invariants(dis),
        "last_updated": archive.get("operation_meta", {}).get("last_updated") if isinstance(archive.get("operation_meta"), dict) else None,
        "hook_output": hook_output_raw,
    })
    return base


def slug(text: str | None) -> str:
    if not text:
        return ""
    value = re.sub(r"\s+", "-", str(text).strip().lower())
    value = re.sub(r"[^a-z0-9-]", "", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def emit_text(summary: dict[str, Any]) -> str:
    if summary["state"] == "INACTIVE":
        return "[MICA] INACTIVE -- no mica.yaml or legacy archive found."
    lines = [
        f"[MICA LOADED] {summary.get('name') or 'unknown'} v{summary.get('version') or 'unknown'}",
        f"Mode      : {summary.get('mode') or 'legacy'}",
        f"Pattern   : {summary.get('pattern') or 'legacy'}",
        f"Invariants: {summary.get('critical_count', 0)} critical, {summary.get('high_count', 0)} high",
        f"PCT       : {summary.get('pct')}",
        f"Last upd  : {summary.get('last_updated') or 'unknown'}",
    ]
    crits = summary.get("critical_invariants", []) or []
    if crits:
        lines.append("")
        lines.append("Active critical invariants:")
        for di in crits:
            lines.append(f"  {di.get('id')}: {di.get('label')}")
            binding = di.get("binding")
            if isinstance(binding, dict) and binding.get("origin_episode"):
                vc = binding.get("violation_count")
                vc_str = f" [{vc}x violated]" if isinstance(vc, int) and vc > 0 else ""
                lines.append(f"    Evidence: {binding['origin_episode']}{vc_str}")
    return "\n".join(lines)


def emit_hook(summary: dict[str, Any]) -> str:
    if summary["state"] == "INACTIVE":
        return "[MICA] INACTIVE -- no mica.yaml or legacy archive found."
    first = (
        f"[MICA] {slug(summary.get('name')) or 'unknown'} v{summary.get('version') or 'unknown'}"
        f" | mode={summary.get('mode') or 'legacy'}"
        f" | pattern={summary.get('pattern') or 'legacy'}"
        f" | DI={summary.get('critical_count', 0)}crit/{summary.get('high_count', 0)}high"
        f" | pct={summary.get('pct')}"
        f" | last={summary.get('last_updated') or 'unknown'}"
    )
    hook_output = summary.get("hook_output") if isinstance(summary.get("hook_output"), dict) else {}
    max_di = hook_output.get("max_di_lines")
    di_filter = hook_output.get("di_filter", "all")

    di_lines: list[str] = []
    for di in summary.get("critical_invariants", []) or []:
        if di_filter == "violations_only":
            binding = di.get("binding") if isinstance(di.get("binding"), dict) else {}
            vc = binding.get("violation_count")
            if not (isinstance(vc, int) and vc > 0):
                continue
        if di.get("id") and di.get("label"):
            binding = di.get("binding") if isinstance(di.get("binding"), dict) else {}
            vc = binding.get("violation_count")
            vc_str = f" [{vc}x]" if isinstance(vc, int) and vc > 0 else ""
            di_lines.append(f"[MICA:DI] {di['id']}(critical): {di['label']}{vc_str}")
        if isinstance(max_di, int) and max_di > 0 and len(di_lines) >= max_di:
            break

    return "\n".join([first] + di_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit portable MICA runtime summaries.")
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--format", choices=["text", "json", "hook"], default="text")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists() or not project_root.is_dir():
        print(f"[ERROR] Not a directory: {project_root}", file=sys.stderr)
        sys.exit(1)

    summary = build_summary(project_root)
    if args.format == "json":
        print(json.dumps(summary, indent=2))
    elif args.format == "hook":
        print(emit_hook(summary))
    else:
        print(emit_text(summary))


if __name__ == "__main__":
    main()
