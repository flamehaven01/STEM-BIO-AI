from __future__ import annotations

from copy import deepcopy
from typing import Any

from .calibration_profile import load_calibration_profile, validate_profile


INTENT_KEYS = (
    "clinical_strictness",
    "code_integrity_priority",
    "reproducibility_priority",
    "structured_limitations_requirement",
)


def validate_intent_answers(answers: dict[str, int]) -> None:
    missing = [key for key in INTENT_KEYS if key not in answers]
    if missing:
        raise ValueError(f"Missing intent answers: {', '.join(missing)}")
    for key in INTENT_KEYS:
        value = answers[key]
        if not isinstance(value, int) or value < 1 or value > 5:
            raise ValueError(f"{key} must be an integer in 1..5")


def derive_policy_intent(
    answers: dict[str, int],
    *,
    baseline_profile_name: str = "default",
) -> dict[str, Any]:
    validate_intent_answers(answers)
    baseline = load_calibration_profile(baseline_profile_name)
    clinical = answers["clinical_strictness"]
    code_priority = answers["code_integrity_priority"]
    reproducibility = answers["reproducibility_priority"]
    structured_limits = answers["structured_limitations_requirement"]

    derived: dict[str, Any] = {
        "baseline_profile": baseline_profile_name,
        "answers": deepcopy(answers),
        "rule_mode": "top_down_first_match",
        "outcome_type": "",
        "recommended_profile": "",
        "triggered_rules": [],
        "notes": [],
        "preview_only_deltas": {},
    }

    if clinical >= 4 and reproducibility <= 3:
        derived["outcome_type"] = "named_profile"
        derived["recommended_profile"] = "strict_clinical_adjacency"
        derived["triggered_rules"].append("clinical_strictness>=4 and reproducibility_priority<=3")
        derived["notes"].append("Strong clinical strictness maps to the existing strict clinical-adjacency profile.")
        return derived

    if baseline_profile_name == "default" and all(2 <= answers[key] <= 3 for key in INTENT_KEYS):
        derived["outcome_type"] = "default_match"
        derived["recommended_profile"] = "default"
        derived["triggered_rules"].append("all_four_values_in_2_to_3_range")
        derived["notes"].append("The default profile already matches the stated posture closely enough.")
        return derived

    preview_deltas: dict[str, Any] = {}
    if clinical >= 4:
        preview_deltas["clinical_policy"] = {
            "ca_no_disclaimer_cap": min(baseline["clinical_policy"]["ca_no_disclaimer_cap"], 60),
            "t0_hard_floor_cap": min(baseline["clinical_policy"]["t0_hard_floor_cap"], 35),
        }
        derived["notes"].append("Clinical strictness requests a stricter cap posture in preview-only mode.")
    if code_priority >= 4:
        preview_deltas["weights"] = {
            "stage_1_percent": 35,
            "stage_2r_percent": 20,
            "stage_3_percent": 45,
        }
        derived["notes"].append("Code-integrity priority shifts 5 points from Stage 1 to Stage 3 in preview-only mode.")
    if reproducibility >= 4:
        preview_deltas["stage_4_policy"] = {"emphasis": "stronger_than_baseline"}
        derived["notes"].append("Reproducibility priority raises Stage 4 emphasis, but does not change the formal score in the current engine.")
    if structured_limits >= 4:
        preview_deltas["stage_3_policy"] = {"b2_partial_credit_mode": "structured_boundary_required"}
        derived["notes"].append("Structured limitations requirement keeps the stricter B2 posture active.")
    if not preview_deltas:
        derived["notes"].append("No named profile rule matched and no explicit bounded delta was activated.")

    derived["outcome_type"] = "preview_only"
    derived["recommended_profile"] = "preview_only"
    derived["triggered_rules"].append("fallback_preview_only")
    derived["preview_only_deltas"] = preview_deltas
    return derived


def simulate_policy_outcome(
    result: dict[str, Any],
    derived: dict[str, Any],
    *,
    baseline_profile_name: str = "default",
) -> dict[str, Any]:
    baseline_profile = load_calibration_profile(baseline_profile_name)
    effective_profile = deepcopy(baseline_profile)
    outcome_type = derived["outcome_type"]
    recommended_profile = derived["recommended_profile"]

    if outcome_type == "named_profile" and recommended_profile != baseline_profile_name:
        effective_profile = load_calibration_profile(recommended_profile)
    elif outcome_type == "preview_only":
        _apply_preview_deltas(effective_profile, derived.get("preview_only_deltas", {}))
        validate_profile(effective_profile)

    raw_score = _simulate_weighted_raw_score(result, effective_profile)
    score_cap = _simulate_score_cap(result, effective_profile)
    final_score = min(raw_score, score_cap) if score_cap is not None else raw_score
    tier = _tier_from_policy(final_score, effective_profile["tier_policy"])

    baseline_raw = int(result["score"]["raw_score_before_floor"])
    baseline_final = int(result["score"]["final_score"])
    simulation = {
        "baseline_profile": baseline_profile_name,
        "effective_profile": effective_profile["profile_name"],
        "effective_policy_version": effective_profile["policy_version"],
        "outcome_type": outcome_type,
        "raw_score_before_cap": raw_score,
        "score_cap": score_cap,
        "final_score": final_score,
        "formal_tier": tier,
        "score_delta": final_score - baseline_final,
        "raw_score_delta": raw_score - baseline_raw,
        "formal_score_changed": final_score != baseline_final,
        "notes": list(derived.get("notes", [])),
    }
    return simulation


def _apply_preview_deltas(profile: dict[str, Any], deltas: dict[str, Any]) -> None:
    for section, values in deltas.items():
        if isinstance(values, dict) and isinstance(profile.get(section), dict):
            profile[section].update(values)
        else:
            profile[section] = values


def _simulate_weighted_raw_score(result: dict[str, Any], profile: dict[str, Any]) -> int:
    weights = profile["weights"]
    score = result["score"]
    penalty = _simulated_c1_penalty(score, profile)
    weighted = (
        score["stage_1_readme_intent"] * weights["stage_1_percent"] / 100
        + score["stage_2_repo_local_consistency"] * weights["stage_2r_percent"] / 100
        + score["stage_3_code_bio"] * weights["stage_3_percent"] / 100
        - penalty
    )
    return round(weighted)


def _simulated_c1_penalty(score: dict[str, Any], profile: dict[str, Any]) -> int:
    baseline_penalty = int(score.get("risk_penalty", 0) or 0)
    if baseline_penalty <= 0:
        return 0
    return int(profile["code_integrity_policy"]["C1_penalty"])


def _simulate_score_cap(result: dict[str, Any], profile: dict[str, Any]) -> int | None:
    classification = result["classification"]
    clinical_policy = profile["clinical_policy"]
    if classification.get("t0_hard_floor"):
        return int(clinical_policy["t0_hard_floor_cap"])
    if classification.get("ca_severity") != "none" and not classification.get("has_explicit_clinical_boundary"):
        return int(clinical_policy["ca_no_disclaimer_cap"])
    return None


def _tier_from_policy(score: int, tier_policy: dict[str, Any]) -> str:
    boundaries = tier_policy["tier_boundaries"]
    names = tier_policy["tier_names"]
    labels = {
        "T0": "Rejected",
        "T1": "Quarantine",
        "T2": "Caution",
        "T3": "Supervised",
        "T4": "Candidate",
    }
    if score < boundaries[0]:
        tier_key = names[0]
    elif score < boundaries[1]:
        tier_key = names[1]
    elif score < boundaries[2]:
        tier_key = names[2]
    elif score < boundaries[3]:
        tier_key = names[3]
    else:
        tier_key = names[4]
    return f"{tier_key} {labels.get(tier_key, tier_key)}"
