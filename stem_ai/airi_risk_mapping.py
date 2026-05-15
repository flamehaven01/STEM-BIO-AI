"""AIRI (MIT AI Risk Repository) integration for STEM BIO-AI.

Runtime behavior is intentionally split into three local layers:

1. Full normalized local registry (`airi_registry_full.v1.json`)
2. Curated runtime bundle (`airi_runtime_bundle.v1.json`)
3. Detector-to-risk mapping registry (`airi_detector_mapping.v1.json`)

This keeps provenance, update governance, and runtime scan scope separate.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_DATA_DIR = Path(__file__).parent / "data"
_REGISTRY_FILE = _DATA_DIR / "airi_registry_full.v1.json"
_BUNDLE_FILE = _DATA_DIR / "airi_runtime_bundle.v1.json"
_MAPPING_FILE = _DATA_DIR / "airi_detector_mapping.v1.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, Any]:
    return _load_json(_REGISTRY_FILE)


@lru_cache(maxsize=1)
def _load_runtime_bundle() -> dict[str, Any]:
    return _load_json(_BUNDLE_FILE)


@lru_cache(maxsize=1)
def _load_mapping_registry() -> dict[str, Any]:
    return _load_json(_MAPPING_FILE)


def _risk_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in rows if row.get("id")}


def _mapping_rows_by_detector(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        detector = str(row.get("detector_id", ""))
        if not detector:
            continue
        grouped.setdefault(detector, []).append(row)
    return grouped


def _missing_data_error() -> dict[str, Any]:
    return {
        "error": (
            "AIRI registry data unavailable; expected "
            "airi_registry_full.v1.json, airi_runtime_bundle.v1.json, and "
            "airi_detector_mapping.v1.json."
        )
    }


def build_airi_coverage(
    code_integrity: dict[str, Any],
    cc_summary: dict[str, Any],
    stage_1_rubric: dict[str, Any],
    t0_hard_floor: bool,
    evidence_ledger: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build AIRI coverage analysis from deterministic scan results."""
    registry = _load_registry()
    runtime_bundle = _load_runtime_bundle()
    mapping_registry = _load_mapping_registry()
    if not registry or not runtime_bundle or not mapping_registry:
        return _missing_data_error()

    registry_risks = registry.get("risks", [])
    bundle_risks = runtime_bundle.get("risks", [])
    mapping_rows = mapping_registry.get("detector_mappings", [])
    known_gaps = mapping_registry.get("known_gaps", [])

    registry_index = _risk_index(registry_risks)
    bundle_index = _risk_index(bundle_risks)
    mappings_by_detector = _mapping_rows_by_detector(mapping_rows)

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
            if stage_1_rubric[key].get("score", 0) < 0:
                triggered.add(key)
    for finding in evidence_ledger or []:
        detector = str(finding.get("detector", ""))
        if finding.get("status") == "detected" and detector in mappings_by_detector:
            triggered.add(detector)

    covered_ids: dict[str, list[str]] = {}
    for detector in triggered:
        for row in mappings_by_detector.get(detector, []):
            risk_id = str(row.get("risk_id", ""))
            if not risk_id:
                continue
            covered_ids.setdefault(risk_id, []).append(detector)

    covered_risks: list[dict[str, Any]] = []
    for risk_id, detectors in sorted(covered_ids.items()):
        entry = bundle_index.get(risk_id) or registry_index.get(risk_id, {})
        covered_risks.append(
            {
                "id": risk_id,
                "title": entry.get("title", risk_id),
                "subdomain_id": entry.get("subdomain_id", ""),
                "subdomain_label": entry.get("subdomain_label", ""),
                "causal_timing": entry.get("causal_timing", ""),
                "covered_by": detectors,
            }
        )

    all_mapped_ids = {str(row.get("risk_id")) for row in mapping_rows if row.get("risk_id")}
    total_in_scope = len(all_mapped_ids)
    coverage_rate = round(len(covered_ids) / total_in_scope, 3) if total_in_scope else 0.0

    known_gaps_in_bundle = [gap for gap in known_gaps if gap.get("gap_scope") == "in_runtime_bundle"]
    known_gaps_outside_bundle = [
        gap for gap in known_gaps if gap.get("gap_scope") == "outside_runtime_bundle_reference"
    ]

    return {
        "airi_version": registry.get("upstream_version", ""),
        "airi_source": (
            f"{registry.get('upstream_source_url', '')} | "
            f"{registry.get('upstream_name', '')} | "
            f"license={registry.get('upstream_license', '')}"
        ),
        "airi_registry_version": registry.get("registry_version", ""),
        "airi_bundle_version": runtime_bundle.get("bundle_version", ""),
        "airi_mapping_version": mapping_registry.get("mapping_version", ""),
        "airi_bundle_scope": runtime_bundle.get("bundle_scope", ""),
        "airi_upstream_snapshot_date": registry.get("upstream_snapshot_date", ""),
        "airi_upstream_license": registry.get("upstream_license", ""),
        "airi_attribution_note": runtime_bundle.get("attribution_note", registry.get("attribution_note", "")),
        "total_risks_in_registry": len(registry_risks),
        "total_risks_in_bundle": len(bundle_risks),
        "total_risks_in_detector_scope": total_in_scope,
        "detectors_triggered": sorted(triggered),
        "covered_risks": covered_risks,
        "covered_count": len(covered_risks),
        "coverage_rate": coverage_rate,
        "known_gaps": known_gaps,
        "known_gaps_in_bundle": known_gaps_in_bundle,
        "known_gaps_outside_bundle": known_gaps_outside_bundle,
    }
