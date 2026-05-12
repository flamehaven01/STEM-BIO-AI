"""AIRI (MIT AI Risk Repository) integration for STEM-BIO-AI.

Maps each STEM-BIO-AI detector to the AIRI risk IDs it directly covers,
loads the bundled medical/clinical/PII risk subset, and produces a
structured coverage report for scan results.

Data source: The AI Risk Repository V4_03 (airisk.mit.edu)
Citation: Slattery et al. (2024), arXiv:2408.12622, Patterns (Cell Press, 2026)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DATA_FILE = Path(__file__).parent / "data" / "airi_medical_risks.json"

# ── detector → AIRI risk ID mapping ────────────────────────────────────────
# Each key is a STEM-BIO-AI detector name; value is a list of AIRI risk IDs
# that the detector directly addresses.

DETECTOR_TO_AIRI: dict[str, list[str]] = {
    # CC-1: confidence_threshold=0.0 passes near-zero confidence predictions
    "CC1_clinical_zero_default": [
        "62.15.02",  # Poor model confidence calibration
        "02.09.00",  # Hallucinations
        "30.01.02",  # Hallucination
        "69.01.01",  # Hallucinated responses
        "16.03.01",  # Disseminating false or misleading information
    ],
    # CC-2: README claims names absent from package __all__
    "CC2_api_contract": [
        "69.01.00",  # False information
        "39.25.00",  # Verifiability (black-box AI)
        "16.03.01",  # Disseminating false or misleading information
        "04.05.00",  # Misleading Information
    ],
    # CC-3: validate_*/check_* with len() but no regex structure check
    "CC3_shallow_validator": [
        "65.03.03",  # Reidentification (after PII removal)
        "02.01.03",  # Privacy Leakage
        "16.02.01",  # Compromising privacy by leaking sensitive information
        "47.03.01",  # PII in data collection
        "70.02.01",  # PII disclosure by AI
    ],
    # C1: hardcoded API keys / credentials
    "C1_hardcoded_credentials": [
        "33.01.05",  # Privacy and security
        "58.06.11",  # Privacy loss (security vector)
        "04.06.00",  # Privacy and Data Leakage
    ],
    # C2: dependency pinning absent → supply-chain drift
    "C2_dependency_pinning": [
        "33.01.05",  # Privacy and security (dependency supply-chain)
        "24.04.01",  # Software integrity risks
    ],
    # C3: deprecated/legacy paths with patient-adjacent data
    "C3_dead_or_deprecated_patient_adjacent_paths": [
        "48.04.00",  # Data Privacy
        "42.09.00",  # Data Protection/Privacy
    ],
    # C4: fail-open exception handlers in clinical paths
    "C4_exception_handling_clinical_adjacent_paths": [
        "70.01.02",  # Accidental harm — automation failure
        "24.01.03",  # Safe exploration in new clinical contexts
        "60.02.01",  # Reliability — inaccurate medical information
    ],
    # T0 / CA-DIRECT: clinical boundary declaration absent
    "T0_hard_floor": [
        "41.04.00",  # Healthcare — overreliance (Allianz2018)
        "61.02.28",  # Human choice of overreliance in critical sectors
        "18.05.03",  # Overreliance
        "56.14.00",  # Overreliance on AI that cannot be unpicked
        "47.02.12",  # Influence, overreliance and dependence
        "16.05.02",  # Anthropomorphising leads to overreliance
        "43.01.00",  # Safety/trustworthiness in healthcare/legal
    ],
    # Stage 1 hype detectors
    "H1_clinical_certainty_hype": [
        "18.05.03",  # Overreliance
        "61.02.28",  # Overreliance in critical sectors
    ],
    "H3_autonomous_replacement_hype": [
        "56.14.00",  # Overreliance on AI systems
        "47.02.12",  # Overreliance and dependence
    ],
    # B2: bias/limitations language absent
    "B2_bias_limitations": [
        "39.25.00",  # Verifiability / lack of transparency
        "16.02.02",  # Inferring sensitive information
        "11.04.04",  # Privacy violations
    ],
}

# AIRI risks present in scope but NOT covered by any current detector
# (diagnostic gap list — used for gap analysis in reports)
KNOWN_GAPS: list[dict[str, str]] = [
    {
        "id": "65.03.03",
        "title": "Reidentification",
        "subdomain_id": "2.1",
        "note": "CC-3 catches shallow validators; dedicated reidentify() API exposure check (CC-4) not yet implemented.",
    },
    {
        "id": "70.02.02",
        "title": "Misinformation — hallucination of clinical knowledge",
        "subdomain_id": "3.1",
        "note": "CC-1 catches threshold=0.0 default; actual output-level hallucination rate requires Layer 3 dynamic testing.",
    },
    {
        "id": "39.25.00",
        "title": "Verifiability — black-box AI in medical healthcare",
        "subdomain_id": "7.4",
        "note": "B2 detects surface language only; Model Card / interpretability artifact presence not yet checked.",
    },
    {
        "id": "11.02.00",
        "title": "Allocative Harms — withheld resources in healthcare",
        "subdomain_id": "1.1",
        "note": "Subgroup performance disparities require dynamic evaluation; outside static scan scope.",
    },
    {
        "id": "72.04.02",
        "title": "Market Concentration — healthcare single-point failures",
        "subdomain_id": "6.1",
        "note": "Systemic risk beyond single-repository scope.",
    },
]


def _load_risks() -> dict[str, dict[str, str]]:
    """Load bundled AIRI medical risk entries keyed by risk ID."""
    if not _DATA_FILE.exists():
        return {}
    with _DATA_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return {r["id"]: r for r in data.get("risks", [])}


def build_airi_coverage(
    code_integrity: dict[str, Any],
    cc_summary: dict[str, Any],
    stage_1_rubric: dict[str, Any],
    t0_hard_floor: bool,
) -> dict[str, Any]:
    """Build AIRI risk coverage analysis from scan results.

    Returns a dict with covered_risks, gap_risks, and coverage_rate
    suitable for inclusion in the scan result JSON.
    """
    risk_db = _load_risks()
    if not risk_db:
        return {"error": "airi_medical_risks.json not found; coverage analysis skipped."}

    # Determine which detectors fired (status != PASS or hard floor)
    triggered: set[str] = set()

    for det, info in code_integrity.items():
        if isinstance(info, dict) and info.get("status") in {"WARN", "FAIL"}:
            triggered.add(det)

    for det, info in cc_summary.items():
        if isinstance(info, dict) and info.get("status") == "WARN":
            triggered.add(det)

    if t0_hard_floor:
        triggered.add("T0_hard_floor")

    for key in ("H1_clinical_certainty_hype", "H3_autonomous_replacement_hype", "B2_bias_limitations"):
        if key in stage_1_rubric and isinstance(stage_1_rubric[key], dict):
            score = stage_1_rubric[key].get("score", 0)
            if score < 0:
                triggered.add(key)

    # Collect covered risk IDs with which detector triggered them
    covered_ids: dict[str, list[str]] = {}
    for det in triggered:
        for rid in DETECTOR_TO_AIRI.get(det, []):
            covered_ids.setdefault(rid, []).append(det)

    covered_risks = []
    for rid, detectors in sorted(covered_ids.items()):
        entry = risk_db.get(rid, {})
        covered_risks.append({
            "id": rid,
            "title": entry.get("title", rid),
            "subdomain_id": entry.get("subdomain_id", ""),
            "subdomain_label": entry.get("subdomain_label", ""),
            "causal_timing": entry.get("causal_timing", ""),
            "covered_by": detectors,
        })

    # All unique IDs from the detector map (full potential scope)
    all_mapped_ids: set[str] = {rid for ids in DETECTOR_TO_AIRI.values() for rid in ids}
    total_in_scope = len(all_mapped_ids)
    coverage_rate = round(len(covered_ids) / total_in_scope, 3) if total_in_scope else 0.0

    return {
        "airi_version": "V4_03_2026-04-23",
        "airi_source": "airisk.mit.edu | arXiv:2408.12622",
        "total_risks_in_bundle": len(risk_db),
        "total_risks_in_detector_scope": total_in_scope,
        "detectors_triggered": sorted(triggered),
        "covered_risks": covered_risks,
        "covered_count": len(covered_risks),
        "coverage_rate": coverage_rate,
        "known_gaps": KNOWN_GAPS,
    }
