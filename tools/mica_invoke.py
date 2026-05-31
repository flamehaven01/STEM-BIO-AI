#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from mica_runtime import build_session_report, find_mica_yaml, load_yaml


def build_invocation_packet(project_root: Path, mode: str) -> dict[str, Any]:
    read_targets: list[dict[str, Any]] = []
    readme = project_root / "README.md"
    if readme.exists():
        read_targets.append(
            {
                "name": "readme",
                "path": str(readme),
                "required": False,
                "reason": "human and agent front door",
            }
        )

    mica_yaml = find_mica_yaml(project_root)
    if mica_yaml:
        read_targets.append(
            {
                "name": "mica_yaml",
                "path": str(mica_yaml),
                "required": True,
                "reason": "authoritative composition contract",
            }
        )
        contract = load_yaml(mica_yaml)
        layers = contract.get("layers", []) if isinstance(contract.get("layers"), list) else []
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            rel = layer.get("path")
            if not isinstance(rel, str):
                continue
            read_targets.append(
                {
                    "name": layer.get("name") or "layer",
                    "path": str((project_root / rel).resolve()),
                    "required": bool(layer.get("required", True)),
                    "reason": f"declared {layer.get('name', 'layer')} surface",
                    "loading_hint": layer.get("loading_hint"),
                }
            )

    packet: dict[str, Any] = {
        "mode": mode,
        "project_root": str(project_root),
        "entry_strategy": mode,
        "read_targets": read_targets,
        "session_report": build_session_report(project_root),
    }
    if mode == "natural":
        packet["directive"] = (
            "Prefer reading README first, then load mica.yaml, archive, and playbook before scan work."
        )
    elif mode == "guided":
        packet["directive"] = (
            "Host agent should load declared MICA surfaces first and use the session report as opening state."
        )
    else:
        packet["directive"] = "Block work until the session report gate is not BLOCKED."
    return packet


def emit_text(packet: dict[str, Any]) -> str:
    report = packet["session_report"]
    lines = [
        f"[MICA INVOKE] mode={packet['mode']}",
        f"Project root: {packet['project_root']}",
        f"Gate       : {report.get('gate')}",
        f"State      : {report.get('load_state', {}).get('state')}",
        f"PCT        : {report.get('self_test', {}).get('pct')}",
        "",
        "Read targets:",
    ]
    for idx, target in enumerate(packet.get("read_targets", []), start=1):
        req = "required" if target.get("required") else "optional"
        lines.append(f"{idx}. {target.get('name')} [{req}]")
        lines.append(f"   {target.get('path')}")
    lines.extend(["", f"Directive: {packet.get('directive')}"])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoke STEM BIO-AI MICA in natural, guided, or forced mode.")
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--mode", choices=["natural", "guided", "forced"], default="guided")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    packet = build_invocation_packet(project_root, args.mode)
    if args.format == "json":
        print(json.dumps(packet, indent=2))
    else:
        print(emit_text(packet))
    if args.mode == "forced" and packet["session_report"].get("gate") == "BLOCKED":
        sys.exit(1)


if __name__ == "__main__":
    main()
