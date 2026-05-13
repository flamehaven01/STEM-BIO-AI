from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any


PROFILE_STATUS_VALUES = {
    "preview_only",
    "experimental",
    "benchmark_candidate",
    "authoritative_release",
    "deprecated",
}
PROFILE_READ_MODE_VALUES = {"mirror_only", "authoritative"}
BOUNDARY_SEMANTICS = "left_closed_right_open"
SCORE_DOMAIN = "integer_0_to_100"
NORMALIZATION_KIND = "linear_round"
ROUNDING_KIND = "half_up_int"
POLICY_SCHEMA_VERSION = "1"


def available_policy_names() -> list[str]:
    names: list[str] = []
    for path in _policy_dir().glob("scoring_profile.*.v1.json"):
        parts = path.name.split(".")
        if len(parts) >= 4:
            names.append(parts[1])
    return sorted(set(names))


def _load_profile_from_path(path: Path) -> dict[str, Any]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    validate_profile(profile)
    profile = deepcopy(profile)
    profile["policy_sha256"] = compute_policy_sha256(profile)
    profile["policy_path"] = str(path)
    return profile


@lru_cache(maxsize=None)
def _load_calibration_profile_cached(profile_name: str) -> dict[str, Any]:
    path = _policy_path(profile_name)
    if not path.exists():
        raise ValueError(f"Calibration profile not found: {profile_name}")
    return _load_profile_from_path(path)


def load_calibration_profile(profile_name: str = "default") -> dict[str, Any]:
    return deepcopy(_load_calibration_profile_cached(profile_name))


def load_calibration_profile_file(profile_path: str | Path) -> dict[str, Any]:
    path = Path(profile_path).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"Calibration profile file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Calibration profile file must be a file: {path}")
    return _load_profile_from_path(path)


def compute_policy_sha256(profile: dict[str, Any]) -> str:
    payload = deepcopy(profile)
    payload.pop("policy_sha256", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def calibration_profile_metadata(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy_schema_version": profile["policy_schema_version"],
        "policy_version": profile["policy_version"],
        "tool_version_introduced": profile["tool_version_introduced"],
        "tool_version_last_validated": profile["tool_version_last_validated"],
        "profile_name": profile["profile_name"],
        "profile_status": profile["profile_status"],
        "profile_read_mode": profile["profile_read_mode"],
        "policy_sha256": profile["policy_sha256"],
    }


def validate_profile(profile: dict[str, Any]) -> None:
    required = {
        "policy_schema_version",
        "policy_version",
        "tool_version_introduced",
        "tool_version_last_validated",
        "profile_name",
        "profile_status",
        "profile_read_mode",
        "weights",
        "stage_baselines",
        "tier_policy",
        "clinical_policy",
        "code_integrity_policy",
        "stage_3_policy",
        "stage_4_policy",
        "diagnostic_policy",
        "reasoning_policy",
        "governance_sources",
    }
    missing = sorted(required - set(profile))
    if missing:
        raise ValueError(f"Calibration profile missing required keys: {', '.join(missing)}")

    if profile["policy_schema_version"] != POLICY_SCHEMA_VERSION:
        raise ValueError("Unsupported calibration policy_schema_version")
    if profile["profile_status"] not in PROFILE_STATUS_VALUES:
        raise ValueError("Unsupported profile_status")
    if profile["profile_read_mode"] not in PROFILE_READ_MODE_VALUES:
        raise ValueError("Unsupported profile_read_mode")

    weights = profile["weights"]
    weight_values = [
        weights["stage_1_percent"],
        weights["stage_2r_percent"],
        weights["stage_3_percent"],
    ]
    if any(not isinstance(value, int) for value in weight_values):
        raise ValueError("Calibration profile weights must be integer percentages")
    if sum(weight_values) != 100:
        raise ValueError("Calibration profile weights must sum to 100")

    tier_policy = profile["tier_policy"]
    boundaries = tier_policy["tier_boundaries"]
    if len(tier_policy["tier_names"]) != 5:
        raise ValueError("Calibration profile tier_names must contain five tiers")
    if len(boundaries) != 4:
        raise ValueError("Calibration profile tier_boundaries must contain four boundaries")
    if any(not isinstance(value, int) for value in boundaries):
        raise ValueError("Calibration profile tier_boundaries must be integers")
    if any(boundaries[idx] >= boundaries[idx + 1] for idx in range(len(boundaries) - 1)):
        raise ValueError("Calibration profile tier_boundaries must be strictly increasing")
    if tier_policy["boundary_semantics"] != BOUNDARY_SEMANTICS:
        raise ValueError("Unsupported calibration boundary semantics")
    if tier_policy["score_domain"] != SCORE_DOMAIN:
        raise ValueError("Unsupported calibration score domain")

    normalization = profile["stage_3_policy"]["normalization"]
    if normalization["kind"] != NORMALIZATION_KIND:
        raise ValueError("Unsupported stage_3 normalization kind")
    if normalization["rounding"] != ROUNDING_KIND:
        raise ValueError("Unsupported stage_3 normalization rounding mode")
    if normalization["raw_max"] <= 0 or normalization["target_max"] <= 0:
        raise ValueError("Stage 3 normalization bounds must be positive")

    reasoning_policy = profile["reasoning_policy"]
    if reasoning_policy.get("score_integration") != "forbidden":
        raise ValueError("Calibration profile reasoning policy must keep score integration forbidden")

    policy_sha256 = profile.get("policy_sha256")
    if profile["profile_read_mode"] == "authoritative" and not isinstance(policy_sha256, str):
        raise ValueError("Authoritative calibration profiles must declare a policy_sha256")
    if isinstance(policy_sha256, str):
        if policy_sha256 != compute_policy_sha256(profile):
            raise ValueError("Calibration profile policy_sha256 does not match canonical hash")


def _policy_path(profile_name: str) -> Path:
    return _policy_dir() / f"scoring_profile.{profile_name}.v1.json"


def _policy_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "policy"
