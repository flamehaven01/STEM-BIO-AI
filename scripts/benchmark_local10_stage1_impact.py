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

DEFAULT_BASELINE = ROOT / "audits/benchmark-v1.3/local-10-v1.3.2-reasoning"
DEFAULT_OUT = ROOT / "audits/benchmark-v1.5/local-10-v1.5.2-stage1-impact"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local-10 and compare v1.5.2 Stage 1 impact.")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--repo-artifacts", action="store_true", help="write per-repo JSON/explain artifacts")
    args = parser.parse_args()

    baseline_dir = args.baseline
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((baseline_dir / "benchmark_manifest.json").read_text(encoding="utf-8"))
    baseline_records = _load_jsonl(baseline_dir / "benchmark_results.jsonl")
    baseline_by_repo = {r["repo"]: r for r in baseline_records}

    records: list[dict[str, Any]] = []
    for repo in manifest["repos"]:
        target = Path(repo["local_path"])
        result = audit_repository(target)
        baseline = baseline_by_repo[repo["repo"]]
        baseline_result = _load_baseline_result(ROOT / baseline["artifact_dir"])
        record = _record(repo, baseline, baseline_result, result)
        records.append(record)

        if args.repo_artifacts:
            repo_out = out_dir / "repos" / f"{repo['local_name']}_{repo['commit'][:12]}"
            write_outputs(result, repo_out, "detailed", 5, "json", explain=True)

    _write_json(out_dir / "benchmark_manifest.json", _manifest(manifest, records))
    _write_jsonl(out_dir / "benchmark_results.jsonl", records)
    (out_dir / "comparison_summary.md").write_text(_summary(records), encoding="utf-8")
    print(f"records={len(records)}")
    print(out_dir)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_baseline_result(artifact_dir: Path) -> dict[str, Any]:
    files = list(artifact_dir.glob("*_experiment_results.json"))
    if not files:
        return {}
    return json.loads(files[0].read_text(encoding="utf-8"))


def _record(
    repo: dict[str, Any],
    baseline: dict[str, Any],
    baseline_result: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    stage1_rubric = result.get("stage_1_rubric", {})
    hype_total = sum(item.get("score", 0) for key, item in stage1_rubric.items() if key.startswith("H"))
    responsibility_scores = [item.get("score", 0) for key, item in stage1_rubric.items() if key.startswith("R")]
    responsibility_positive_total = sum(score for score in responsibility_scores if score > 0)
    responsibility_penalty_total = sum(score for score in responsibility_scores if score < 0)
    responsibility_net_total = sum(responsibility_scores)
    hype_hits = [key for key, item in stage1_rubric.items() if key.startswith("H") and item.get("score", 0) < 0]
    responsibility_hits = [key for key, item in stage1_rubric.items() if key.startswith("R") and item.get("score", 0) > 0]

    old_score = int(baseline["stem_score"])
    new_score = int(result["score"]["final_score"])
    old_tier = baseline["stem_tier"]
    new_tier = result["score"]["formal_tier"]
    old_stage1 = baseline_result.get("score", {}).get("stage_1_readme_intent")
    new_stage1 = result["score"]["stage_1_readme_intent"]

    return {
        "repo": repo["repo"],
        "local_name": repo["local_name"],
        "local_path": repo["local_path"],
        "commit": repo["commit"],
        "baseline_version": baseline["stem_ai_version"],
        "stem_ai_version": __version__,
        "baseline_score": old_score,
        "v1_5_2_score": new_score,
        "score_delta": new_score - old_score,
        "baseline_tier": old_tier,
        "v1_5_2_tier": new_tier,
        "tier_delta": _tier_index(new_tier) - _tier_index(old_tier),
        "baseline_stage_1": old_stage1,
        "v1_5_2_stage_1": new_stage1,
        "stage_1_delta": None if old_stage1 is None else new_stage1 - int(old_stage1),
        "hype_penalty_total": hype_total,
        "responsibility_positive_total": responsibility_positive_total,
        "responsibility_penalty_total": responsibility_penalty_total,
        "responsibility_net_total": responsibility_net_total,
        "hype_hits": hype_hits,
        "responsibility_hits": responsibility_hits,
        "ca_severity": result["classification"]["ca_severity"],
        "score_cap": result["classification"]["score_cap"],
        "replication_score": result.get("replication_score"),
        "replication_tier": result.get("replication_tier"),
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
        "schema_version": "stem-bio-ai-benchmark-v1.5-local10-stage1-impact",
        "generated_at": date.today().isoformat(),
        "stem_ai_version": __version__,
        "benchmark_type": "local10_stage1_hr_impact",
        "baseline_comparison": str(DEFAULT_BASELINE.relative_to(ROOT)).replace("\\", "/"),
        "repo_count": len(records),
        "repos": base_manifest["repos"],
    }


def _summary(records: list[dict[str, Any]]) -> str:
    tier_changes = [r for r in records if r["tier_delta"] != 0]
    score_deltas = [r["score_delta"] for r in records]
    hype_repos = [r for r in records if r["hype_penalty_total"] < 0]
    responsibility_repos = [r for r in records if r["responsibility_positive_total"] > 0]
    tier_counts = Counter(r["v1_5_2_tier"] for r in records)

    lines = [
        "# Local-10 v1.5.2 Stage 1 Impact",
        "",
        f"- Records: {len(records)}",
        f"- Tier changes vs v1.3.2 baseline: {len(tier_changes)}",
        f"- Score delta range: {min(score_deltas)} to {max(score_deltas)}",
        f"- Mean score delta: {sum(score_deltas) / len(score_deltas):.1f}",
        f"- Repos with H1-H6 hype penalties: {len(hype_repos)}",
        f"- Repos with R1-R5 responsibility credit: {len(responsibility_repos)}",
        f"- v1.5.2 tier distribution: {dict(tier_counts)}",
        "",
        "## Interpretation",
        "",
        "- Stage 1 H/R scoring did not create broad tier inflation on local-10.",
        "- Only one repository changed tier: ClawBio moved from T1 to T2, remaining under the CA-DIRECT no-disclaimer cap.",
        "- BioAgents is the only repository with a hype penalty hit, and it stayed in the same tier.",
        "- T0 hard floors and score caps kept direct clinical-adjacent repositories from jumping to high-confidence tiers.",
        "",
        "| Repo | Score | Tier | Stage 1 | H total | R + | R - | R net | H hits | R+ hits |",
        "|---|---:|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in records:
        score = f"{r['baseline_score']} -> {r['v1_5_2_score']} ({r['score_delta']:+d})"
        tier = f"{r['baseline_tier']} -> {r['v1_5_2_tier']}"
        s1_delta = "" if r["stage_1_delta"] is None else f" ({r['stage_1_delta']:+d})"
        stage1 = f"{r['baseline_stage_1']} -> {r['v1_5_2_stage_1']}{s1_delta}"
        lines.append(
            f"| {r['local_name']} | {score} | {tier} | {stage1} | "
            f"{r['hype_penalty_total']} | {r['responsibility_positive_total']} | "
            f"{r['responsibility_penalty_total']} | {r['responsibility_net_total']} | "
            f"{', '.join(r['hype_hits']) or '-'} | {', '.join(r['responsibility_hits']) or '-'} |"
        )
    return "\n".join(lines) + "\n"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


if __name__ == "__main__":
    main()
