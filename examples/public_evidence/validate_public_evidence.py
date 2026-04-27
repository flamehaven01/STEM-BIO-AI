#!/usr/bin/env python3
"""
Validate the public STEM-AI v1.1.2 evidence artifact.

This script is intentionally small, dependency-free, and IP-neutral. It checks
aggregate evidence and contract math without requiring audited repository names,
private code, patient records, model weights, or proprietary datasets.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


FORBIDDEN_KEYS = {
    "patient_name",
    "patient_id",
    "email",
    "phone",
    "address",
    "api_key",
    "secret",
    "token",
    "private_key",
    "repository_names",
    "target_code",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized_key = key.lower()
            require(
                normalized_key not in FORBIDDEN_KEYS,
                f"forbidden key at {path}.{key}",
            )
            assert_no_forbidden_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_forbidden_keys(item, f"{path}[{index}]")


def tier_for(score: float, boundaries: dict[str, list[int]]) -> str:
    for tier, (low, high) in boundaries.items():
        if low <= score <= high:
            return tier
    raise AssertionError(f"score outside tier boundaries: {score}")


def compute_final_score(case: dict[str, Any]) -> int:
    if case["t0_hard_floor"]:
        return 0

    stage_1 = float(case["stage_1"])
    stage_3 = float(case["stage_3"])
    risk_penalty = float(case["risk_penalty"])

    if case["stage_2_available"]:
        stage_2 = float(case["stage_2"])
        weighted = (stage_1 * 0.40) + (stage_2 * 0.20) + (stage_3 * 0.40)
    else:
        weighted = (stage_1 * 0.50) + (stage_3 * 0.50)

    return int(max(0, min(100, round(weighted - risk_penalty))))


def validate(data: dict[str, Any]) -> list[str]:
    checks: list[str] = []

    assert_no_forbidden_keys(data)
    checks.append("forbidden-key scan passed")

    ip = data["ip_safety_statement"]
    for key, value in ip.items():
        if key.startswith("contains_"):
            require(value is False, f"IP safety flag must be false: {key}")
    checks.append("IP safety flags passed")

    batch = data["public_audit_batch"]
    tier_counts = batch["tier_distribution"]
    require(sum(tier_counts.values()) == batch["repository_count"], "tier counts do not sum to repository_count")
    checks.append("public audit batch aggregate count passed")

    invariants = data["contract_invariants"]
    require(invariants["active_invariant_count"] == 18, "active invariant count must equal 18")
    require(
        invariants["required_stage_order"]
        == [
            "Stage 1: README Intent",
            "Stage 2: Cross-Platform",
            "Stage 3: Code/Bio",
        ],
        "stage order drift detected",
    )
    checks.append("invariant count and stage order passed")

    base_weights = invariants["base_weights"]
    require(math.isclose(sum(base_weights.values()), 1.0), "base weights must sum to 1.0")
    na_weights = invariants["stage_2_na_weights"]
    require(math.isclose(sum(na_weights.values()), 1.0), "Stage 2 N/A weights must sum to 1.0")
    checks.append("weight checks passed")

    boundaries = invariants["tier_boundaries"]
    expected_boundaries = {
        "T0": [0, 39],
        "T1": [40, 54],
        "T2": [55, 69],
        "T3": [70, 84],
        "T4": [85, 100],
    }
    require(boundaries == expected_boundaries, "tier boundary drift detected")
    checks.append("tier boundary checks passed")

    stage3g = invariants["stage3g_policy"]
    require(stage3g["advisory_only"] is True, "Stage 3G must remain advisory")
    require(stage3g["may_raise_formal_tier"] is False, "Stage 3G must not raise formal tier")
    checks.append("governance overlay separation passed")

    pct = data["pct_gate"]
    require(len(pct["critical_halt_checks"]) == 3, "PCT critical halt check count must be 3")
    checks.append("PCT critical halt check count passed")

    for case in data["synthetic_score_cases"]:
        final_score = compute_final_score(case)
        require(final_score == case["expected_final_score"], f"{case['case_id']} final score mismatch")
        final_tier = tier_for(final_score, boundaries)
        require(final_tier == case["expected_tier"], f"{case['case_id']} tier mismatch")
    checks.append("synthetic score cases passed")

    return checks


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("usage: validate_public_evidence.py [evidence_json]", file=sys.stderr)
        return 2

    evidence_path = Path(argv[1]) if len(argv) == 2 else Path(__file__).with_name("stem_ai_v1_1_2_public_evidence.json")
    data = load_json(evidence_path)
    checks = validate(data)

    print("STEM-AI public evidence validation: PASS")
    for check in checks:
        print(f"- {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
