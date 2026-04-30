from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stem_ai import __version__
from stem_ai.provider_benchmark import (
    PROVIDER_BENCHMARK_SCHEMA_VERSION,
    packet_stats_record,
    packet_summary,
    response_validation_record,
)
from stem_ai.render import _safe_name
from stem_ai.scanner import audit_repository


def main() -> int:
    args = _parser().parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    response_dir = Path(args.responses).expanduser().resolve() if args.responses else None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_dir = out_dir / "packets"
    packet_dir.mkdir(parents=True, exist_ok=True)

    packet_records: list[dict[str, Any]] = []
    response_records: list[dict[str, Any]] = []
    failures: list[str] = []
    for repo in manifest.get("repos", []):
        local_path = Path(repo["local_path"])
        if not local_path.exists():
            failures.append(f"- {repo.get('repo')}: local path missing: {local_path}")
            continue
        result = audit_repository(local_path, advisory="packet")
        packet = result["ai_advisory_input"]
        packet_path = packet_dir / f"{_safe_name(repo.get('local_name') or repo.get('repo'))}_advisory_input.json"
        packet_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
        packet_records.append(packet_stats_record(repo, result, packet, packet_path.relative_to(out_dir)))

        response_path = _response_path(response_dir, repo) if response_dir is not None else None
        if response_path is not None and response_path.exists():
            validated = audit_repository(local_path, advisory_response_path=response_path)
            response_records.append(response_validation_record(repo, validated["ai_advisory"], response_path))

    _write_json(out_dir / "benchmark_manifest.json", _output_manifest(manifest_path, manifest, packet_records, response_records))
    _write_jsonl(out_dir / "packet_stats.jsonl", packet_records)
    _write_json(out_dir / "packet_summary.json", packet_summary(packet_records))
    _write_jsonl(out_dir / "provider_response_validation.jsonl", response_records)
    _write_notes(out_dir / "provider_failure_notes.md", failures, response_dir, response_records)
    print(f"provider benchmark records: packets={len(packet_records)} responses={len(response_records)}")
    print(out_dir)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build provider-packet benchmark artifacts without API calls.")
    parser.add_argument(
        "--manifest",
        default="audits/benchmark-v1.3/local-10/benchmark_manifest.json",
        help="Benchmark manifest containing repos with local_path fields",
    )
    parser.add_argument(
        "--out",
        default="audits/benchmark-v1.4/provider-response-local-10",
        help="Output directory for v1.4 provider benchmark artifacts",
    )
    parser.add_argument(
        "--responses",
        default=None,
        help="Optional directory of provider advisory JSON files named by local_name, repo safe name, or '<local_name>_provider_advisory.json'",
    )
    return parser


def _output_manifest(
    source_manifest: Path,
    source: dict[str, Any],
    packet_records: list[dict[str, Any]],
    response_records: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": PROVIDER_BENCHMARK_SCHEMA_VERSION,
        "generated_at": date.today().isoformat(),
        "stem_ai_version": __version__,
        "benchmark_type": "provider_packet_readiness",
        "source_manifest": str(source_manifest),
        "source_schema_version": source.get("schema_version"),
        "repo_count": len(packet_records),
        "response_validation_count": len(response_records),
        "packet_profile": "provider_budgeted",
        "api_calls_made_by_script": False,
        "repos": [
            {
                "repo": record.get("repo"),
                "local_name": record.get("local_name"),
                "local_path": record.get("local_path"),
                "expected_commit": record.get("expected_commit"),
                "scan_commit": record.get("scan_commit"),
                "packet_file": record.get("packet_file"),
            }
            for record in packet_records
        ],
    }


def _response_path(response_dir: Path | None, repo: dict[str, Any]) -> Path | None:
    if response_dir is None:
        return None
    names = [
        f"{repo.get('local_name')}_provider_advisory.json",
        f"{repo.get('local_name')}.json",
        f"{_safe_name(repo.get('repo') or '')}_provider_advisory.json",
    ]
    for name in names:
        path = response_dir / name
        if path.exists():
            return path
    return None


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _write_notes(
    path: Path,
    failures: list[str],
    response_dir: Path | None,
    response_records: list[dict[str, Any]],
) -> None:
    lines = [
        "# Provider Response Benchmark Notes",
        "",
        "This benchmark script makes no provider API calls.",
        "It exports provider-budgeted packets and optionally validates existing provider response JSON files.",
        "",
        f"Response directory: `{response_dir}`" if response_dir else "Response directory: not provided",
        f"Response validations: {len(response_records)}",
        "",
        "## Failures",
        "",
    ]
    lines += failures or ["None"]
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
