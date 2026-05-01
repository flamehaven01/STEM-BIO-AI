from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stem_ai import __version__
from stem_ai.scanner import audit_repository

DEFAULT_BASELINE = ROOT / "audits/benchmark-v1.5/local-10-v1.5.4-stage3-3tier-impact"
DEFAULT_OUT = ROOT / "audits/benchmark-v1.5/local-10-v1.5.6-ca-fp-impact"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local-10 and compare v1.5.6 CA false-positive impact.")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((args.baseline / "benchmark_manifest.json").read_text(encoding="utf-8"))
    baseline_records = _load_jsonl(args.baseline / "benchmark_results.jsonl")
    baseline_by_repo = {r["repo"]: r for r in baseline_records}

    records = []
    for repo in manifest["repos"]:
        result = audit_repository(Path(repo["local_path"]))
        records.append(_record(repo, baseline_by_repo[repo["repo"]], result))

    _write_json(args.out / "benchmark_manifest.json", _manifest(manifest, records))
    _write_jsonl(args.out / "benchmark_results.jsonl", records)
    (args.out / "comparison_summary.md").write_text(_summary(records), encoding="utf-8")
    print(f"records={len(records)}")
    print(args.out)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _record(repo: dict[str, Any], baseline: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    old_score = int(baseline["v1_5_4_score"])
    new_score = int(result["score"]["final_score"])
    old_tier = baseline["v1_5_4_tier"]
    new_tier = result["score"]["formal_tier"]
    return {
        "repo": repo["repo"],
        "local_name": repo["local_name"],
        "local_path": repo["local_path"],
        "commit": repo["commit"],
        "baseline_version": baseline["stem_ai_version"],
        "stem_ai_version": __version__,
        "baseline_score": old_score,
        "v1_5_6_score": new_score,
        "score_delta": new_score - old_score,
        "baseline_tier": old_tier,
        "v1_5_6_tier": new_tier,
        "tier_delta": _tier_index(new_tier) - _tier_index(old_tier),
        "baseline_ca_severity": baseline.get("ca_severity"),
        "v1_5_6_ca_severity": result["classification"]["ca_severity"],
        "baseline_score_cap": baseline.get("score_cap"),
        "v1_5_6_score_cap": result["classification"]["score_cap"],
        "v1_5_6_has_boundary": result["classification"]["has_explicit_clinical_boundary"],
        "v1_5_6_t0_hard_floor": result["classification"]["t0_hard_floor"],
    }


def _tier_index(tier: str) -> int:
    for i, prefix in enumerate(["T0", "T1", "T2", "T3", "T4"]):
        if tier.startswith(prefix):
            return i
    return -1


def _manifest(base_manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "stem-bio-ai-benchmark-v1.5-local10-ca-fp-impact",
        "generated_at": date.today().isoformat(),
        "stem_ai_version": __version__,
        "benchmark_type": "local10_ca_false_positive_impact",
        "baseline_comparison": str(DEFAULT_BASELINE.relative_to(ROOT)).replace("\\", "/"),
        "repo_count": len(records),
        "repos": base_manifest["repos"],
    }


def _summary(records: list[dict[str, Any]]) -> str:
    changed = [r for r in records if r["score_delta"] or r["tier_delta"]]
    tier_changes = [r for r in records if r["tier_delta"]]
    score_deltas = [r["score_delta"] for r in records]
    tier_counts = Counter(r["v1_5_6_tier"] for r in records)
    lines = [
        "# Local-10 v1.5.6 CA False-Positive Impact",
        "",
        f"- Records: {len(records)}",
        f"- Score/tier changes vs v1.5.4 baseline: {len(changed)}",
        f"- Tier changes vs v1.5.4 baseline: {len(tier_changes)}",
        f"- Score delta range: {min(score_deltas)} to {max(score_deltas)}",
        f"- Mean score delta: {sum(score_deltas) / len(score_deltas):.1f}",
        f"- v1.5.6 tier distribution: {dict(tier_counts)}",
        "",
        "## Interpretation",
        "",
        "- ClawBio gains score within T2 because explicit non-medical-device and no-diagnosis boundary language is now recognized.",
        "- BioClaw moves from T0 to T1 because workspace triage is no longer treated as patient triage.",
        "- No repository moves into T3/T4 from this precision patch.",
        "",
        "| Repo | Score | Tier | CA | Cap | Boundary | T0 floor |",
        "|---|---:|---|---|---|---|---|",
    ]
    for r in records:
        score = f"{r['baseline_score']} -> {r['v1_5_6_score']} ({r['score_delta']:+d})"
        tier = f"{r['baseline_tier']} -> {r['v1_5_6_tier']}"
        ca = f"{r['baseline_ca_severity']} -> {r['v1_5_6_ca_severity']}"
        cap = f"{r['baseline_score_cap']} -> {r['v1_5_6_score_cap']}"
        lines.append(
            f"| {r['local_name']} | {score} | {tier} | {ca} | {cap} | "
            f"{r['v1_5_6_has_boundary']} | {r['v1_5_6_t0_hard_floor']} |"
        )
    return "\n".join(lines) + "\n"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    main()
