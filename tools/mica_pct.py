#!/usr/bin/env python3
"""
MICA PCT Validator -- portable self-diagnostic runner.

Usage:
    python mica_pct.py [project_root]

Runs PCT-001 through PCT-011 and prints results.
Exit code: 0 = CLOSED CONTRACT, 1 = INCOMPLETE/FAILURE

PCT-010 (v0.2.3): binding completeness check for critical DIs. WARN-only.
  Maturity path: WARN in v0.2.3-v0.2.5; FAIL when binding_required: true
  is declared in mica.yaml (planned v0.2.6); global FAIL reviewed at v0.3.0.

PCT-011 (v0.2.4): lesson_ref existence validation. WARN-only.
  A dead lesson_ref link is treated as a binding integrity failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import]
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except ImportError:
        return _minimal_yaml_parse(path)


def run_pct(project_root: Path) -> bool:
    results: list[tuple[str, str, str]] = []

    mica_yaml_path = project_root / "mica.yaml"
    if not mica_yaml_path.exists():
        mica_yaml_path = project_root / "memory" / "mica.yaml"

    if mica_yaml_path.exists():
        results.append(("PCT-001", "PASS", "mica.yaml present"))
    else:
        results.append(("PCT-001", "FAIL", "mica.yaml missing (checked root + memory/)"))
        _report(results)
        return False

    try:
        yd = load_yaml(mica_yaml_path)
    except Exception as exc:
        results.append(("PCT-002", "FAIL", f"mica.yaml parse error: {exc}"))
        _report(results)
        return False

    required_fields = {"mica_spec", "mode", "layers"}
    missing_fields = required_fields - set(yd.keys())
    layers = yd.get("layers", []) if isinstance(yd.get("layers"), list) else []
    layer_names = [layer.get("name", "") for layer in layers if isinstance(layer, dict)]
    valid_modes = {"memory_injection", "protocol_evolution"}

    if missing_fields:
        results.append(("PCT-002", "FAIL", f"missing fields: {sorted(missing_fields)}"))
    elif "archive" not in layer_names:
        results.append(("PCT-002", "FAIL", "archive layer missing"))
    elif "playbook" not in layer_names:
        results.append(("PCT-002", "FAIL", "playbook layer missing"))
    elif yd.get("mode") not in valid_modes:
        results.append(("PCT-002", "FAIL", f"invalid mode: {yd.get('mode')}"))
    else:
        results.append(("PCT-002", "PASS", "required fields valid"))

    missing_paths: list[str] = []
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        if not layer.get("required", True):
            continue
        rel = layer.get("path")
        if isinstance(rel, str) and not (project_root / rel).exists():
            missing_paths.append(rel)

    if missing_paths:
        results.append(("PCT-003", "FAIL", f"missing layer paths: {missing_paths}"))
    else:
        results.append(("PCT-003", "PASS", "all required layer paths exist"))

    mode = yd.get("mode", "")
    if mode == "memory_injection" and {"archive", "playbook"} <= set(layer_names):
        results.append(("PCT-004", "PASS", "memory_injection coherence ok"))
    elif mode == "protocol_evolution" and {"archive", "playbook", "lessons"} <= set(layer_names):
        results.append(("PCT-004", "PASS", "protocol_evolution coherence ok"))
    elif mode == "protocol_evolution":
        results.append(("PCT-004", "FAIL", "protocol_evolution requires lessons layer"))
    else:
        results.append(("PCT-004", "FAIL", f"mode={mode} incompatible with layers={layer_names}"))

    archive_rel = next(
        (layer.get("path") for layer in layers if isinstance(layer, dict) and layer.get("name") == "archive"),
        None,
    )
    archive: dict[str, Any] = {}
    if isinstance(archive_rel, str):
        archive_path = project_root / archive_rel
        if archive_path.exists():
            try:
                archive = json.loads(archive_path.read_text(encoding="utf-8"))
            except Exception:
                archive = {}

    if "mica_spec" in archive:
        results.append(("PCT-005", "INFO", f"archive mica_spec = {archive['mica_spec']}"))
    else:
        results.append(("PCT-005", "INFO", "archive mica_spec absent (legacy-valid)"))

    yaml_spec = str(yd.get("mica_spec", ""))
    arch_spec = str(archive.get("mica_spec", ""))
    if yaml_spec and arch_spec and yaml_spec == arch_spec:
        results.append(("PCT-006", "PASS", f"mica_spec aligned: {yaml_spec}"))
    elif yaml_spec and arch_spec:
        results.append(("PCT-006", "WARN", f"drift: mica.yaml={yaml_spec} archive={arch_spec}"))
    else:
        results.append(("PCT-006", "INFO", "mica_spec absent in one or both files"))

    inv = yd.get("invocation_protocol") if isinstance(yd.get("invocation_protocol"), dict) else {}
    pattern = inv.get("primary_pattern") if isinstance(inv.get("primary_pattern"), str) else None
    valid_patterns = {
        "readme_protocol", "hook_trigger", "agent_yaml_bootstrap",
        "global_skill", "workspace_directive", "explicit",
    }
    if pattern is None:
        results.append(("PCT-007", "INFO", "invocation_protocol absent (default/manual handling)"))
    elif pattern not in valid_patterns:
        results.append(("PCT-007", "FAIL", f"invalid primary_pattern: {pattern}"))
    else:
        results.append(("PCT-007", "PASS", f"primary_pattern valid: {pattern}"))

    hook_hint_layers = [
        layer.get("name") for layer in layers
        if isinstance(layer, dict) and layer.get("loading_hint") == "hook"
    ]
    hook_script = inv.get("hook_script") if isinstance(inv.get("hook_script"), str) else None
    if pattern == "hook_trigger":
        if not hook_script:
            results.append(("PCT-008", "FAIL", "hook_trigger declared without hook_script"))
        elif not (project_root / hook_script).exists():
            results.append(("PCT-008", "FAIL", f"hook_script missing: {hook_script}"))
        else:
            results.append(("PCT-008", "PASS", f"hook_script present: {hook_script}"))
    elif hook_hint_layers:
        results.append(("PCT-008", "WARN", f"loading_hint=hook used without hook_trigger on layers {hook_hint_layers}"))
    else:
        results.append(("PCT-008", "INFO", "no hook-specific coherence issues"))

    if archive:
        dis = [d for d in archive.get("design_invariants", []) if isinstance(d, dict)]
        critical_dis = [d for d in dis if d.get("severity") == "critical"]
        unbound = [
            d.get("id", "?") for d in critical_dis
            if not isinstance(d.get("binding"), dict)
            or not d.get("binding", {}).get("origin_episode")
        ]
        if not critical_dis:
            results.append(("PCT-010", "INFO", "no critical DIs in archive"))
        elif unbound:
            results.append((
                "PCT-010", "WARN",
                f"critical DIs missing binding.origin_episode: {unbound}"
                f" -- escalates to FAIL when binding_required: true is set (planned v0.2.6)",
            ))
        else:
            results.append(("PCT-010", "PASS", f"all {len(critical_dis)} critical DIs have binding"))

        broken_refs: list[tuple[str, str]] = []
        for d in critical_dis:
            binding = d.get("binding") if isinstance(d.get("binding"), dict) else {}
            lref = binding.get("lesson_ref")
            if isinstance(lref, str) and lref and not (project_root / lref).exists():
                broken_refs.append((d.get("id", "?"), lref))
        if broken_refs:
            results.append(("PCT-011", "WARN", f"binding.lesson_ref dead links: {broken_refs}"))
        else:
            bound_with_ref = [
                d for d in critical_dis
                if isinstance(d.get("binding"), dict) and d["binding"].get("lesson_ref")
            ]
            if bound_with_ref:
                results.append(("PCT-011", "PASS", f"all {len(bound_with_ref)} lesson_ref paths exist"))
            else:
                results.append(("PCT-011", "INFO", "no lesson_ref fields declared; nothing to validate"))
    else:
        results.append(("PCT-010", "INFO", "archive not loaded; binding check skipped"))
        results.append(("PCT-011", "INFO", "archive not loaded; lesson_ref check skipped"))

    hard_fails = {"PCT-001", "PCT-002", "PCT-003", "PCT-004", "PCT-007", "PCT-008"}
    fails = [r[0] for r in results if r[1] == "FAIL" and r[0] in hard_fails]
    if fails:
        results.append(("PCT-009", "FAIL", f"package incomplete. failing checks: {fails}"))
    else:
        results.append(("PCT-009", "PASS", "package complete. closed contract verified."))

    _report(results)
    return not fails


def _report(results: list[tuple[str, str, str]]) -> None:
    print()
    for pid, status, msg in results:
        print(f"{pid} [{status:<4}] {msg}")
    print()
    all_pass = all(s in ("PASS", "INFO", "WARN") for _, s, _ in results)
    print("Overall:", "CLOSED CONTRACT" if all_pass else "INCOMPLETE")
    print()


def _minimal_yaml_parse(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_list: list[Any] | None = None
    current_list_item: dict[str, Any] | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            val = stripped[2:].strip()
            if ":" in val:
                k, v = val.split(":", 1)
                current_list_item = {k.strip(): v.strip().strip('"')}
                if current_list is not None:
                    current_list.append(current_list_item)
            else:
                current_list_item = None
                if current_list is not None:
                    current_list.append(val.strip('"'))
        elif ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"')
            if v == "":
                current_list = []
                data[k] = current_list
                current_list_item = None
            else:
                current_list = None
                current_list_item = None
                data[k] = v
    return data


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    if not root.is_dir():
        print(f"[ERROR] Not a directory: {root}")
        sys.exit(1)
    print("MICA PCT Validator v0.2.4")
    print(f"Project root: {root}")
    passed = run_pct(root)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
