from __future__ import annotations

import math
import re
from statistics import mean, pstdev
from typing import Any


REASONING_VERSION = "stem-bio-ai-reasoning-v1.3.2"
MODEL_STATUS = "diagnostic_only_uncalibrated_initial_prior"


def required_bits(confidence: float) -> float:
    """Return the evidence budget required for a confidence value in [0, 1]."""
    value = _clip(float(confidence), 0.0, 1.0)
    return max(0.0, -math.log2(1 - value + 1e-6))


def unique_token_count(text: str) -> int:
    """Deterministic evidence token count; no model tokenizer or locale rules."""
    return len(set(re.findall(r"[A-Za-z0-9]+", str(text).lower())))


def observed_bits(text: str) -> float:
    return math.log2(1 + unique_token_count(text))


def evidence_budget(
    confidence: float,
    evidence_text: str,
    budget_deficit_max: float = 1.0,
) -> dict[str, Any]:
    required = required_bits(confidence)
    observed = observed_bits(evidence_text)
    deficit = required - observed
    return {
        "confidence": round(_clip(confidence, 0.0, 1.0), 4),
        "required_bits": round(required, 4),
        "observed_bits": round(observed, 4),
        "unique_token_count": unique_token_count(evidence_text),
        "deficit": round(deficit, 4),
        "budget_deficit_max": round(budget_deficit_max, 4),
        "flagged": deficit > budget_deficit_max,
        "status": "under_supported" if deficit > budget_deficit_max else "supported",
        "basis": MODEL_STATUS,
    }


def confidence_envelope(confidence: float, evidence_count: int) -> dict[str, Any]:
    value = _clip(float(confidence), 0.0, 1.0)
    count = max(0, int(evidence_count))
    # Initial deterministic prior: more evidence narrows the diagnostic interval.
    margin = min(0.35, 0.50 / math.sqrt(count + 1))
    return {
        "confidence": round(value, 4),
        "evidence_count": count,
        "lower": round(_clip(value - margin, 0.0, 1.0), 4),
        "upper": round(_clip(value + margin, 0.0, 1.0), 4),
        "margin": round(margin, 4),
        "basis": MODEL_STATUS,
    }


def lane_coherence(stage_scores: dict[str, float | int | None]) -> dict[str, Any]:
    normalized = {key: _normalize_score(value) for key, value in stage_scores.items()}
    pair_specs = [
        ("stage_1_readme_evidence", "stage_3_code_bio"),
        ("stage_3_code_bio", "stage_4_replication"),
    ]
    pairs: list[dict[str, Any]] = []
    for left, right in pair_specs:
        left_score = normalized.get(left)
        right_score = normalized.get(right)
        if left_score is None or right_score is None:
            continue
        coherence = _clip(1 - abs(left_score - right_score), 0.0, 1.0)
        pairs.append({
            "pair": f"{left}:{right}",
            "left": round(left_score, 4),
            "right": round(right_score, 4),
            "coherence": round(coherence, 4),
        })
    overall = mean([item["coherence"] for item in pairs]) if pairs else None
    return {
        "stage_scores": {k: (round(v, 4) if v is not None else None) for k, v in normalized.items()},
        "pairs": pairs,
        "overall": round(overall, 4) if overall is not None else None,
        "status": _coherence_status(overall),
        "basis": MODEL_STATUS,
    }


def uncertainty_budget(
    stage_scores: dict[str, float | int | None],
    detector_counts: dict[str, int],
) -> dict[str, Any]:
    values = [score for score in (_normalize_score(v) for v in stage_scores.values()) if score is not None]
    stage_std = pstdev(values) if len(values) > 1 else 0.0
    total = max(1, int(detector_counts.get("total", 0)))
    manual_ratio = int(detector_counts.get("manual_review_required", 0)) / total
    error_ratio = int(detector_counts.get("error", 0)) / total
    uncertainty = (
        0.50 * _clip(stage_std / 0.35, 0.0, 1.0)
        + 0.35 * _clip(manual_ratio, 0.0, 1.0)
        + 0.15 * _clip(error_ratio, 0.0, 1.0)
    )
    return {
        "stage_std": round(stage_std, 4),
        "manual_review_required_ratio": round(manual_ratio, 4),
        "error_ratio": round(error_ratio, 4),
        "uncertainty": round(uncertainty, 4),
        "status": _uncertainty_status(uncertainty),
        "basis": MODEL_STATUS,
    }


def evidence_risk_gate(
    risk_components: dict[str, float | int],
    risk_gate: float = 0.60,
) -> dict[str, Any]:
    missing = _clip(float(risk_components.get("missing_required_boundary_ratio", 0.0)), 0.0, 1.0)
    contradiction = _clip(float(risk_components.get("contradiction_ratio", 0.0)), 0.0, 1.0)
    manual = _clip(float(risk_components.get("manual_review_required_ratio", 0.0)), 0.0, 1.0)
    parse_error = _clip(float(risk_components.get("parse_error_ratio", 0.0)), 0.0, 1.0)
    evidence_risk = 0.40 * missing + 0.30 * contradiction + 0.20 * manual + 0.10 * parse_error
    gate = max(0.0, float(risk_gate))
    gate_factor = 0.0 if gate == 0 else max(0.0, 1 - evidence_risk / gate)
    return {
        "components": {
            "missing_required_boundary_ratio": round(missing, 4),
            "contradiction_ratio": round(contradiction, 4),
            "manual_review_required_ratio": round(manual, 4),
            "parse_error_ratio": round(parse_error, 4),
        },
        "evidence_risk": round(evidence_risk, 4),
        "risk_gate": round(gate, 4),
        "risk_gate_factor": round(gate_factor, 4),
        "status": "review_required" if evidence_risk >= gate else "within_gate",
        "basis": MODEL_STATUS,
    }


def benchmark_alignment(stem_tiers: list[int], manual_tiers: list[int]) -> dict[str, Any]:
    if len(stem_tiers) != len(manual_tiers):
        raise ValueError("stem_tiers and manual_tiers must have the same length")
    count = len(stem_tiers)
    deltas = [int(stem) - int(manual) for stem, manual in zip(stem_tiers, manual_tiers)]
    exact = sum(1 for delta in deltas if delta == 0)
    within_one = sum(1 for delta in deltas if abs(delta) <= 1)
    return {
        "count": count,
        "exact_tier_agreement": exact,
        "within_one_tier_agreement": within_one,
        "major_disagreement_count": sum(1 for delta in deltas if abs(delta) > 1),
        "mean_abs_delta": round(mean([abs(delta) for delta in deltas]), 4) if deltas else 0.0,
        "deltas": deltas,
    }


def build_reasoning_model(result: dict[str, Any]) -> dict[str, Any]:
    score = result.get("score", {})
    stage_scores = {
        "stage_1_readme_evidence": score.get("stage_1_readme_intent"),
        "stage_2_repo_local_consistency": score.get("stage_2_repo_local_consistency"),
        "stage_3_code_bio": score.get("stage_3_code_bio"),
        "stage_4_replication": result.get("replication_score"),
    }
    ledger = list(result.get("evidence_ledger", []))
    detector_summary = result.get("detector_summary", {})
    status_counts = detector_summary.get("by_status", {})
    total_findings = int(detector_summary.get("total_findings", len(ledger)))
    detector_counts = {
        "total": total_findings,
        "manual_review_required": int(status_counts.get("manual_review_required", 0)),
        "error": int(status_counts.get("error", 0)),
    }
    evidence_text = _evidence_text(ledger)
    confidence = _clip(float(score.get("final_score", 0)) / 100, 0.0, 1.0)
    coherence = lane_coherence(stage_scores)
    contradiction = 0.0 if coherence["overall"] is None else 1 - float(coherence["overall"])
    manual_ratio = detector_counts["manual_review_required"] / max(1, total_findings)
    error_ratio = detector_counts["error"] / max(1, total_findings)
    classification = result.get("classification", {})
    missing_boundary = (
        1.0
        if classification.get("clinical_adjacent") and not classification.get("has_explicit_clinical_boundary")
        else 0.0
    )
    return {
        "version": REASONING_VERSION,
        "policy": {
            "mode": "diagnostic_only",
            "final_score_override": False,
            "uses_ai": False,
            "weights": "uncalibrated_initial_priors_pending_benchmark_calibration",
        },
        "evidence_budget": evidence_budget(confidence, evidence_text),
        "confidence_envelope": confidence_envelope(confidence, total_findings),
        "lane_coherence": coherence,
        "uncertainty_budget": uncertainty_budget(stage_scores, detector_counts),
        "evidence_risk_gate": evidence_risk_gate({
            "missing_required_boundary_ratio": missing_boundary,
            "contradiction_ratio": contradiction,
            "manual_review_required_ratio": manual_ratio,
            "parse_error_ratio": error_ratio,
        }),
        "benchmark_alignment": None,
    }


def _evidence_text(ledger: list[dict[str, Any]], limit: int = 200) -> str:
    chunks: list[str] = []
    for finding in ledger[:limit]:
        chunks.extend([
            str(finding.get("detector", "")),
            str(finding.get("status", "")),
            str(finding.get("snippet", "")),
            str(finding.get("explanation", "")),
        ])
    return " ".join(chunks)


def _normalize_score(value: float | int | None) -> float | None:
    if value is None:
        return None
    number = float(value)
    if number > 1:
        number = number / 100
    return _clip(number, 0.0, 1.0)


def _coherence_status(value: float | None) -> str:
    if value is None:
        return "not_available"
    if value >= 0.80:
        return "coherent"
    if value >= 0.55:
        return "mixed"
    return "divergent"


def _uncertainty_status(value: float) -> str:
    if value < 0.20:
        return "stable"
    if value <= 0.45:
        return "review_advised"
    return "manual_review_required"


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
