from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "docs" / "regulatory_basis_registry.v1.json"
_REGISTRY_CACHE: dict[str, Any] | None = None


def load_regulatory_basis_registry() -> dict[str, Any]:
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        _REGISTRY_CACHE = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    return _REGISTRY_CACHE


def build_regulatory_basis(current_date: date | None = None) -> dict[str, Any]:
    registry = load_regulatory_basis_registry()
    review_reasons = _basis_review_reasons(registry, current_date or date.today())
    return {
        "registry_version": registry["schema_version"],
        "as_of": registry["as_of"],
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
        "source_ids": [source["id"] for source in registry.get("sources", [])],
        "note": {
            "title": registry["display_note"]["title"],
            "body_line_1": registry["display_note"]["body_line_1"],
            "body_line_2": registry["display_note"]["body_line_2"],
        },
    }


def build_stage_traceability(result: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        "stage_1": _stage_1_traceability(result),
        "stage_2r": _stage_2r_traceability(result),
        "stage_3": _stage_3_traceability(result),
        "stage_4": _stage_4_traceability(result),
        "bio_diagnostics": _bio_traceability(result),
    }


def build_regulatory_traceability(result: dict[str, Any]) -> dict[str, Any]:
    stage_traceability = build_stage_traceability(result)
    items = [item for stage_items in stage_traceability.values() for item in stage_items]
    return {
        "version": "stem-ai-reg-trace-v1.6",
        "summary": _traceability_summary(stage_traceability),
        "items": items,
    }


def _stage_1_traceability(result: dict[str, Any]) -> list[dict[str, Any]]:
    rubric = result.get("stage_1_rubric", {})
    positive_refs = [key for key in (
        "R1_limitations_section",
        "R2_regulatory_framework",
        "R3_clinical_disclaimer",
        "R4_demographic_bias_boundary",
        "R5_reproducibility_provisions",
    ) if rubric.get(key, {}).get("score", 0) > 0]
    if positive_refs:
        return [_traceability_item(
            stage="stage_1",
            requirement_id="EU_AI_ACT_ARTICLE_13",
            mapping_confidence="weak",
            finding_refs=positive_refs,
            source_ids=["eu_ai_act_2024_1689", "fda_mlmd_transparency_2024"],
            note="Boundary, intended-use, and limitation language is relevant to transparency scaffolding only.",
            not_assessed=["IFU completeness", "deployer communication workflow"],
        )]
    if not result.get("classification", {}).get("clinical_adjacent"):
        return []
    return [{
        "stage": "stage_1",
        "requirement_id": "EU_AI_ACT_ARTICLE_13",
        "mapping_confidence": "weak",
        "evidence_strength": "weak",
        "status": "not_detected",
        "not_assessed": ["IFU completeness", "deployer communication workflow"],
        "finding_refs": [],
        "source_ids": ["eu_ai_act_2024_1689", "fda_mlmd_transparency_2024"],
        "note": "Clinical-adjacent repository language was observed, but positive claim-boundary or limitation scaffolding was not detected in README/package surfaces.",
    }]


def _stage_2r_traceability(result: dict[str, Any]) -> list[dict[str, Any]]:
    rubric = result.get("stage_2r_rubric", {})
    refs = [key for key in (
        "R2R_4_limitation_repetition",
        "R2R_D1_internal_clinical_boundary_contradiction",
        "R2R_D2_missing_clinical_use_boundary",
        "R2R_D4_unsupported_workflow_claim",
    ) if key in rubric]
    if not refs:
        return []
    positive_refs = [key for key in refs if key == "R2R_4_limitation_repetition" and rubric.get(key, {}).get("score", 0) > 0]
    status = "partially_aligned" if positive_refs else "signal_only"
    return [{
        "stage": "stage_2r",
        "requirement_id": "IMDRF_CLINICAL_CONTEXT_BOUNDARY_SIGNAL",
        "mapping_confidence": "weak_moderate",
        "evidence_strength": _evidence_strength(refs),
        "status": status,
        "not_assessed": ["target-population performance", "operational clinical workflow fit"],
        "finding_refs": refs,
        "source_ids": ["imdrf_samd_clinical_eval_2017"],
        "note": "Repository-local contradiction and boundary signals are relevant to clinical-context traceability, not clinical validation.",
    }]


def _stage_3_traceability(result: dict[str, Any]) -> list[dict[str, Any]]:
    rubric = result.get("stage_3_rubric", {})
    items: list[dict[str, Any]] = []
    if rubric.get("T3_changelog_release_hygiene", {}).get("score", 0) > 0:
        items.append(_traceability_item(
            stage="stage_3",
            requirement_id="EU_AI_ACT_ARTICLE_12",
            mapping_confidence="weak_moderate",
            finding_refs=["T3_changelog_release_hygiene"],
            source_ids=["eu_ai_act_2024_1689", "fda_qmsr", "fda_pccp_2025"],
            note="Change-history scaffolding is present, but runtime log completeness is not established.",
            not_assessed=["runtime event logging", "operator retention procedures"],
        ))
    bias_refs = [key for key in ("B1_data_provenance_controls", "B2_bias_limitations") if rubric.get(key, {}).get("score", 0) > 0]
    if bias_refs:
        items.append(_traceability_item(
            stage="stage_3",
            requirement_id="EU_AI_ACT_ARTICLE_10",
            mapping_confidence="weak",
            finding_refs=bias_refs,
            source_ids=["eu_ai_act_2024_1689", "imdrf_samd_clinical_eval_2017"],
            note="Provenance and bias signals are relevant to data-governance review, but do not verify execution quality.",
            not_assessed=["measurement correctness", "dataset adequacy", "regulator adequacy"],
        ))
    return items


def _stage_4_traceability(result: dict[str, Any]) -> list[dict[str, Any]]:
    rubric = result.get("stage_4_rubric", {})
    refs = [key for key in (
        "S4_environment_lock_evidence",
        "S4_checksum_files",
        "S4_readme_reproducibility_section",
        "S4_container_environment",
    ) if rubric.get(key, {}).get("score", 0) > 0]
    if not refs:
        return []
    return [_traceability_item(
        stage="stage_4",
        requirement_id="EU_AI_ACT_ARTICLE_12",
        mapping_confidence="moderate",
        finding_refs=refs,
        source_ids=["eu_ai_act_2024_1689", "fda_qmsr", "fda_pccp_2025"],
        note="Reproducibility and trace manifests support record-keeping scaffolding, not operational logging completeness.",
        not_assessed=["deploy-time event logging", "runtime event completeness"],
    )]


def _bio_traceability(result: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    mapping_rows = (
        ("BIO_silent_mock_fallback", "EU_AI_ACT_ARTICLE_15", "moderate", "Silent mock fallback is relevant to robustness and misleading-output risk review.", ["eu_ai_act_2024_1689"]),
        ("BIO_run_trace", "EU_AI_ACT_ARTICLE_15", "moderate", "Unsafe bio-tool subprocess construction is relevant to robustness and secure execution review.", ["eu_ai_act_2024_1689"]),
        ("BIO_smiles_parser_guard", "IMDRF_ANALYTICAL_VALIDATION_SIGNAL", "weak_moderate", "Parser guards support analytical-validation hygiene review, not chemical validity.", ["imdrf_samd_clinical_eval_2017"]),
        ("BIO_smiles_rdkit_validation", "IMDRF_ANALYTICAL_VALIDATION_SIGNAL", "weak_moderate", "Optional RDKit validation supports stronger syntax-level chemistry screening when installed.", ["imdrf_samd_clinical_eval_2017"]),
        ("BIO_trace_manifest", "EU_AI_ACT_ARTICLE_12", "moderate", "Traceability manifest surfaces are relevant to structural record-keeping review.", ["eu_ai_act_2024_1689", "fda_pccp_2025"]),
    )
    for detector, requirement_id, confidence, note, sources in mapping_rows:
        refs = [
            finding["finding_id"]
            for finding in result.get("evidence_ledger", [])
            if finding.get("detector") == detector and finding.get("status") == "detected"
        ]
        if not refs:
            continue
        items.append(_traceability_item(
            stage="bio_diagnostics",
            requirement_id=requirement_id,
            mapping_confidence=confidence,
            finding_refs=refs[:5],
            source_ids=sources,
            note=note,
            not_assessed=["runtime completeness"],
        ))
    return items


def _traceability_summary(stage_traceability: dict[str, list[dict[str, Any]]]) -> str:
    aligned_statuses = {"aligned", "partially_aligned"}
    signal_statuses = {"signal_only"}
    all_items = [item for stage_items in stage_traceability.values() for item in stage_items]
    has_art12 = any(item["requirement_id"] == "EU_AI_ACT_ARTICLE_12" and item.get("status") in aligned_statuses for item in all_items)
    has_art13 = any(item["requirement_id"] == "EU_AI_ACT_ARTICLE_13" and item.get("status") in aligned_statuses for item in all_items)
    has_art15 = any(item["requirement_id"] == "EU_AI_ACT_ARTICLE_15" and item.get("status") in aligned_statuses for item in all_items)
    parts: list[str] = []
    if has_art12:
        parts.append("traceability scaffolding")
    if has_art13:
        parts.append("transparency scaffolding")
    if has_art15:
        parts.append("robustness-relevant engineering signals")
    if not parts:
        if any(item.get("status") in signal_statuses for item in all_items):
            return "Only indirect regulatory-relevant signals were observed. This remains a pre-audit traceability aid, not a compliance determination."
        return "No strong structural regulatory traceability signals were observed. This remains a pre-audit traceability aid."
    joined = ", ".join(parts[:-1]) + (f" and {parts[-1]}" if len(parts) > 1 else parts[0])
    return f"Structural signals partially align with {joined}. This remains a pre-audit traceability aid, not a compliance determination."


def _traceability_item(
    stage: str,
    requirement_id: str,
    mapping_confidence: str,
    finding_refs: list[str],
    source_ids: list[str],
    note: str,
    not_assessed: list[str],
) -> dict[str, Any]:
    return {
        "stage": stage,
        "requirement_id": requirement_id,
        "mapping_confidence": mapping_confidence,
        "evidence_strength": _evidence_strength(finding_refs),
        "status": _traceability_status(finding_refs, mapping_confidence),
        "not_assessed": not_assessed,
        "finding_refs": finding_refs,
        "source_ids": source_ids,
        "note": note,
    }


def _evidence_strength(finding_refs: list[str]) -> str:
    count = len(finding_refs)
    if count >= 4:
        return "strong"
    if count >= 2:
        return "moderate"
    return "weak"


def _traceability_status(finding_refs: list[str], mapping_confidence: str) -> str:
    if not finding_refs:
        return "not_detected"
    if mapping_confidence == "weak":
        return "signal_only"
    if mapping_confidence == "weak_moderate":
        return "partially_aligned" if len(finding_refs) >= 2 else "signal_only"
    if mapping_confidence in {"moderate", "strong"}:
        return "partially_aligned"
    return "signal_only"


def _basis_review_reasons(registry: dict[str, Any], today: date) -> list[str]:
    reasons: list[str] = []
    as_of = registry.get("as_of", "")
    registry_month = _parse_registry_month(as_of)
    if registry_month is None:
        reasons.append("registry_as_of_unparseable")
    elif (registry_month.year, registry_month.month) < (today.year, today.month):
        reasons.append("registry_as_of_stale")

    sources = registry.get("sources", [])
    if any(source.get("status") == "draft_guidance" for source in sources):
        reasons.append("draft_guidance_present")

    source_ids = {str(source.get("id", "")) for source in sources}
    required_ids = {
        "eu_ai_act_2024_1689",
        "fda_qmsr",
        "fda_mlmd_transparency_2024",
        "imdrf_samd_clinical_eval_2017",
    }
    missing_ids = sorted(required_ids - source_ids)
    if missing_ids:
        reasons.append("required_source_missing")
    return reasons


def _parse_registry_month(as_of: str) -> date | None:
    try:
        parsed = datetime.strptime(as_of.strip(), "%B %Y")
    except ValueError:
        return None
    return date(parsed.year, parsed.month, 1)
