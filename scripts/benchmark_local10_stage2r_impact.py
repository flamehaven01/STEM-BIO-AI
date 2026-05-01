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
from stem_ai.render import write_outputs
from stem_ai.scanner import audit_repository

DEFAULT_BASELINE = ROOT / "audits/benchmark-v1.5/local-10-v1.5.2-stage1-impact"
DEFAULT_OUT = ROOT / "audits/benchmark-v1.5/local-10-v1.5.3-stage2r-impact"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local-10 and compare v1.5.3 Stage 2R impact.")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--repo-artifacts", action="store_true", help="write per-repo JSON/explain artifacts")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((args.baseline / "benchmark_manifest.json").read_text(encoding="utf-8"))
    baseline_records = _load_jsonl(args.baseline / "benchmark_results.jsonl")
    baseline_by_repo = {r["repo"]: r for r in baseline_records}

    records: list[dict[str, Any]] = []
    for repo in manifest["repos"]:
        result = audit_repository(Path(repo["local_path"]))
        record = _record(repo, baseline_by_repo[repo["repo"]], result)
        records.append(record)
        if args.repo_artifacts:
            repo_out = args.out / "repos" / f"{repo['local_name']}_{repo['commit'][:12]}"
            write_outputs(result, repo_out, "detailed", 5, "json", explain=True)

    _write_json(args.out / "benchmark_manifest.json", _manifest(manifest, records))
    _write_jsonl(args.out / "benchmark_results.jsonl", records)
    (args.out / "comparison_summary.md").write_text(_summary(records), encoding="utf-8")
    print(f"records={len(records)}")
    print(args.out)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _record(repo: dict[str, Any], baseline: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    rubric = result.get("stage_2r_rubric", {})
    new_items = {
        key: item.get("score", 0)
        for key, item in rubric.items()
        if key.startswith("R2R_4") or key.startswith("R2R_D1") or key.startswith("R2R_D3") or key.startswith("R2R_D4")
    }
    old_score = int(baseline["v1_5_2_score"])
    new_score = int(result["score"]["final_score"])
    old_tier = baseline["v1_5_2_tier"]
    new_tier = result["score"]["formal_tier"]
    return {
        "repo": repo["repo"],
        "local_name": repo["local_name"],
        "local_path": repo["local_path"],
        "commit": repo["commit"],
        "baseline_version": baseline["stem_ai_version"],
        "stem_ai_version": __version__,
        "baseline_score": old_score,
        "v1_5_3_score": new_score,
        "score_delta": new_score - old_score,
        "baseline_tier": old_tier,
        "v1_5_3_tier": new_tier,
        "tier_delta": _tier_index(new_tier) - _tier_index(old_tier),
        "v1_5_3_stage_2r": result["score"]["stage_2_repo_local_consistency"],
        "new_stage_2r_items": new_items,
        "ca_severity": result["classification"]["ca_severity"],
        "score_cap": result["classification"]["score_cap"],
    }


def _tier_index(tier: str) -> int:
    if tier.startswith("T0"):
        return 0
    if tier.startswith("T1"):
        return 1
    if tier.startswith("T2"):
        return 2
    if tier.startswith("T3"):
        return 3
    if tier.startswith("T4"):
        return 4
    return -1


def _manifest(base_manifest: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "stem-bio-ai-benchmark-v1.5-local10-stage2r-impact",
        "generated_at": date.today().isoformat(),
        "stem_ai_version": __version__,
        "benchmark_type": "local10_stage2r_impact",
        "baseline_comparison": str(DEFAULT_BASELINE.relative_to(ROOT)).replace("\\", "/"),
        "repo_count": len(records),
        "repos": base_manifest["repos"],
    }


def _summary(records: list[dict[str, Any]]) -> str:
    tier_changes = [r for r in records if r["tier_delta"] != 0]
    score_deltas = [r["score_delta"] for r in records]
    triggered = [r for r in records if r["new_stage_2r_items"]]
    tier_counts = Counter(r["v1_5_3_tier"] for r in records)
    lines = [
        "# Local-10 v1.5.3 Stage 2R Impact",
        "",
        f"- Records: {len(records)}",
        f"- Tier changes vs v1.5.2 baseline: {len(tier_changes)}",
        f"- Score delta range: {min(score_deltas)} to {max(score_deltas)}",
        f"- Mean score delta: {sum(score_deltas) / len(score_deltas):.1f}",
        f"- Repos with new Stage 2R R4/D1/D3/D4 items: {len(triggered)}",
        f"- v1.5.3 tier distribution: {dict(tier_counts)}",
        "",
        "| Repo | Score | Tier | Stage 2R | New Stage 2R items |",
        "|---|---:|---|---:|---|",
    ]
    for r in records:
        score = f"{r['baseline_score']} -> {r['v1_5_3_score']} ({r['score_delta']:+d})"
        tier = f"{r['baseline_tier']} -> {r['v1_5_3_tier']}"
        items = ", ".join(f"{k}={v:+d}" for k, v in r["new_stage_2r_items"].items()) or "-"
        lines.append(f"| {r['local_name']} | {score} | {tier} | {r['v1_5_3_stage_2r']} | {items} |")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    main()
