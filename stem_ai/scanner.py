from __future__ import annotations

import hashlib
import re
import subprocess
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from . import __version__
from .advisory_contract import (
    advisory_contract_schemas,
    build_offline_advisory,
    build_provider_advisory_input,
    validate_advisory_input_packet,
)
from .advisory_providers import load_provider_config, provider_handoff_metadata
from .advisory_response import validate_advisory_response_file
from .advisory_runtime import execute_advisory_call
from .calibration_profile import calibration_profile_metadata, load_calibration_profile
from .airi_risk_mapping import build_airi_coverage
from .detector_contract import collect_contract_findings
from .detectors import collect_evidence_bundle
from .evidence import EvidenceFinding
from .patterns import (
    BIAS_LIMITATION_TERMS,
    BIAS_MEASUREMENT_TERMS,
    BIO_TERMS,
    CHANGELOG_BUG_TERMS,
    COI_FUNDING_TERMS,
    DATA_SOURCE_TERMS,
    DATA_SOURCE_NEGATIVE_TERMS,
    DEMOGRAPHIC_BIAS_TERMS,
    DISCLAIMER_TERMS,
    EXACT_PINNED_DEP,
    FAIL_OPEN,
    HYPE_AUTONOMOUS_REPLACEMENT,
    HYPE_BREAKTHROUGH,
    HYPE_CLINICAL_CERTAINTY,
    HYPE_PERFECT_ACCURACY,
    HYPE_REGULATORY_APPROVAL,
    HYPE_UNIVERSAL_GENERALIZATION,
    LIMITATIONS_SECTION,
    LOOSE_DEP,
    PATIENT_METADATA,
    PLACEHOLDER_SECRET_VALUES,
    REGULATORY_FRAMEWORK_TERMS,
    REPRODUCIBILITY_TERMS,
    SECRET_TERMS,
    SKIP_DIRS,
    STAGE2R_CLINICAL_DEPLOYMENT_CLAIMS,
    STAGE2R_ENTRYPOINT_TERMS,
    STAGE2R_WORKFLOW_CLAIMS,
    TEXT_EXTENSIONS,
    WEAK_REGULATORY_SELF_ASSERTION_TERMS,
)
from .regulatory_traceability import (
    build_regulatory_basis,
    build_regulatory_traceability,
    build_stage_traceability,
)
from .reasoning_model import build_reasoning_model


CA_INDIRECT_TERMS = re.compile(
    r"\b(consensus|vcf|variant|viral|virus|genome|sequenc|sample|allele|clinical trial|"
    r"medical imaging|pydicom|biomarker|survival analysis|AutoDock|drug docking|nnU-Net|"
    r"regulatory submission)\b",
    re.I,
)
CA_DIRECT_TERMS = re.compile(
    r"\b(diagnosis|diagnostic\s+(?:tool|model|system|decision|support|pipeline|classifier|prediction|screening|test|use|grade|claim)|"
    r"clinical decision|decision support|patient-facing|(?:clinical|patient|emergency|medical)\s+triage|"
    r"triage\s+(?:tool|model|system|decision|support|prediction|risk)|risk score|"
    r"treatment recommendation|treatment guidance|drug recommendation|pharmacogenomic|pharmacogenetic|"
    r"DPYD|CYP2D6|CPIC|FDA clearance|CE mark)\b",
    re.I,
)
CA_TAXONOMY_VERSION = "ca-taxonomy-v1"
CA_TAXONOMY_SOURCE = "runtime_regex_hardcoded_in_scanner_py"
T0_HARD_FLOOR_TERMS = re.compile(
    r"\b(autonomous|automated|without clinician|clinical decision support|diagnosis|"
    r"diagnostic\s+(?:tool|model|system|decision|support|pipeline|classifier|prediction|screening|test|use)|"
    r"treatment recommendation|(?:clinical|patient|emergency|medical)\s+triage|"
    r"triage\s+(?:tool|model|system|decision|support|prediction|risk)|risk score)\b",
    re.I,
)
META_EVIDENCE_LINE = re.compile(
    r"(regex|detector|pattern|schema|contract|rubric|score component|detection method|"
    r"CA severity|CA-DIRECT|CA-INDIRECT|T0_HARD_FLOOR_TERMS|Stage 1 hype|hype penalties|"
    r"triage tiers|review priority|Executive / triage|diagnostic layer|"
    r"does not mean|clinical deployment .*requires independent expert validation|"
    r"framework's primary question|does not need|Clinically validated; safe|"
    r"prohibited .*claims|rejected by the validator|forbidden citations)",
    re.I,
)


def audit_repository(
    target: Path,
    policy_name: str = "default",
    advisory: str = "none",
    advisory_response_path: Path | None = None,
) -> dict[str, Any]:
    calibration_profile = load_calibration_profile(policy_name)
    audit_date = date.today()
    files = _list_files(target)
    readme = _read_first(target, ["README.md", "README.rst", "readme.md"])
    docs_text = _read_many(target / "docs", max_files=30)
    package_text = _read_first(target, ["pyproject.toml", "setup.py", "setup.cfg", "package.json"])
    dep_text = _read_first(
        target,
        [
            "environment.yml",
            "requirements.txt",
            "pyproject.toml",
            "setup.cfg",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "npm-shrinkwrap.json",
            "package.json",
        ],
    )
    workflow_text = _read_many(target / ".github" / "workflows", max_files=20)
    test_text = _read_many(target / "tests", max_files=40)
    changelog_text = _read_first(target, ["CHANGELOG.md", "CHANGELOG", "NEWS.md"])
    code_text = _read_many(target, max_files=200, suffixes={".py", ".sh"})

    repo_name = _repo_name(target)
    surface_text = "\n".join([readme, docs_text, package_text])
    ca_severity = _classify_ca_severity(surface_text)
    clinical_adjacent = ca_severity != "none"
    has_disclaimer = bool(DISCLAIMER_TERMS.search(readme + "\n" + docs_text))
    t0_hard_floor = _t0_hard_floor(surface_text, ca_severity, has_disclaimer)

    stage_1, stage_1_rubric = _score_stage_1(readme, docs_text, package_text, ca_severity, has_disclaimer)
    stage_2r, stage_2r_rubric = _score_stage_2r(
        readme,
        docs_text,
        package_text,
        workflow_text,
        test_text,
        changelog_text,
        code_text,
        clinical_adjacent,
        has_disclaimer,
    )
    evidence_ledger, ast_signal_summary, stage_4 = collect_evidence_bundle(target)
    evidence_ledger = [_normalize_evidence_finding(f) for f in evidence_ledger]

    cc_findings: list[EvidenceFinding] = []
    cc_counters: dict[tuple[str, str], int] = defaultdict(int)
    cc_summary = collect_contract_findings(target, readme, cc_findings, cc_counters)
    evidence_ledger.extend(_normalize_evidence_finding(f.to_dict()) for f in cc_findings)

    stage_3, stage_3_rubric = _score_stage_3(target, readme, docs_text, workflow_text, test_text, dep_text, changelog_text)
    code_integrity = _code_integrity_from_findings(evidence_ledger, clinical_adjacent, has_disclaimer)

    weights = {"stage_1": 0.4, "stage_2": 0.2, "stage_3": 0.4}
    risk_penalty = 10 if code_integrity["C1_hardcoded_credentials"]["status"] == "FAIL" else 0
    raw_score = round(stage_1 * weights["stage_1"] + stage_2r * weights["stage_2"] + stage_3 * weights["stage_3"] - risk_penalty)
    score_cap = _score_cap(ca_severity, has_disclaimer, t0_hard_floor)
    final_score = min(raw_score, score_cap) if score_cap is not None else raw_score

    result = {
        "schema_version": "stem-ai-local-cli-result-v1.6",
        "stem_ai_version": __version__,
        "generated_at_local": audit_date.isoformat(),
        "execution_mode": "LOCAL_ANALYSIS",
        "target": {
            "name": repo_name,
            "local_path": str(target),
            "remote": _git(target, "remote", "get-url", "origin"),
            "branch": _git(target, "rev-parse", "--abbrev-ref", "HEAD"),
            "commit": _git(target, "rev-parse", "HEAD"),
            "file_count": len(files),
        },
        "classification": {
            "clinical_adjacent": clinical_adjacent,
            "ca_severity": ca_severity,
            "ca_taxonomy_version": CA_TAXONOMY_VERSION,
            "ca_taxonomy_source": CA_TAXONOMY_SOURCE,
            "t0_hard_floor": t0_hard_floor,
            "score_cap": score_cap,
            "has_explicit_clinical_boundary": has_disclaimer,
        },
        "score": {
            "stage_1_readme_intent": stage_1,
            "stage_2_cross_platform": "not_applicable_in_LOCAL_ANALYSIS",
            "stage_2_repo_local_consistency": stage_2r,
            "stage_2_lane": "STAGE_2R_REPO_LOCAL_CONSISTENCY",
            "stage_3_code_bio": stage_3,
            "weights": weights,
            "risk_penalty": risk_penalty,
            "raw_score_before_floor": raw_score,
            "final_score": final_score,
            "formal_tier": _tier(final_score),
            "use_scope": _use_scope(final_score),
        },
        "stage_2r_rubric": stage_2r_rubric,
        "stage_1_rubric": stage_1_rubric,
        "stage_3_rubric": stage_3_rubric,
        "replication_score": stage_4["replication_score"],
        "replication_tier": stage_4["replication_tier"],
        "stage_4_rubric": stage_4["stage_4_rubric"],
        "code_integrity": code_integrity,
        "code_contract": cc_summary,
        "airi_risk_coverage": build_airi_coverage(code_integrity, cc_summary, stage_1_rubric, t0_hard_floor, evidence_ledger),
        "evidence_ledger": evidence_ledger,
        "detector_summary": _detector_summary(evidence_ledger),
        "ast_signal_summary": ast_signal_summary,
        "notable_positive_evidence": _positive_evidence(workflow_text, test_text, docs_text, package_text),
        "notable_risks": _risks(
            clinical_adjacent,
            has_disclaimer,
            code_integrity,
            evidence_ledger,
            cc_summary,
            self_asserted_compliance=stage_1_rubric.get("R2_regulatory_framework", {}).get("score") == 5,
        ),
        "file_hashes_sha256": _hash_key_files(target),
        "method": "Deterministic local CLI scan. No LLM, network, or runtime test execution is required.",
        "artifact_surface_notes": {
            "json": "JSON remains the canonical full-fidelity artifact. Human-readable surfaces may compact repeated same-file evidence for readability while preserving detector semantics.",
            "human_readable_compaction": "Markdown, HTML, PDF, and explain outputs may compact repeated same-file evidence rows or narrative blocks. Refer to JSON for full per-finding detail.",
        },
        "measurement_basis": {
            "stage_1": "README/package bio-domain regex; hype-claim penalties; limitation, strong regulatory-framework signals, weaker self-asserted compliance signals, disclaimer, demographic-bias, and reproducibility responsibility signals. R2 regulatory-framework signals post-hoc align with ICH M15 §4.1 MAP and §2.2.2 Appropriateness of Proposed MIDD.",
            "stage_2r": "Repo-local consistency checks across README, package metadata, docs, changelog, test/CI files, and deterministic contradiction/staleness/workflow-support heuristics. R2R_D2 missing clinical boundary post-hoc aligns with ICH M15 §2.1.2 Context of Use requirement.",
            "stage_3_T1": ".github/workflows/ directory contains files",
            "stage_3_T2": "tests/ directory contains bio-domain vocabulary (regex)",
            "stage_3_T3": "CHANGELOG.md, CHANGELOG, or NEWS.md file exists; max credit requires bug-fix, patch, or security entries",
            "stage_3_B1": "Python and JavaScript dependency or lock manifests are treated as repository provenance surfaces; max credit still requires data-source, dataset-citation, or IRB language and does not by itself prove dataset lineage. Post-hoc aligns with ICH M15 §3 Verification (user-generated code documentation) and §4.2 MAR (data and methods section).",
            "stage_3_B2": "bias/limitation vocabulary present in README and docs; max credit requires quantitative measurement evidence or related test coverage. Post-hoc aligns with ICH M15 §3 Validation and Applicability Assessment: 'limitations of the data and model should be described and discussed.'",
        "stage_3_B3": "funding/sponsor/COI vocabulary present in README, docs, or FUNDING.md (regex)",
            "stage_4": "Deterministic replication evidence lane: containers, reproducibility targets, lock/pin/hash evidence, README reproducibility sections, dataset/model artifact references, citation metadata, license/use-scope restriction evidence, CLI/seed/example signals. Post-hoc aligns with ICH M15 §4.3: coding scripts, data, and supporting files should be available for regulatory review.",
            "ca_severity": "Clinical/diagnostic term regex match in README, docs, and package metadata",
            "ca_taxonomy_governance": f"{CA_TAXONOMY_VERSION} from {CA_TAXONOMY_SOURCE}; reference markdown is informative, not authoritative runtime source.",
            "C1": "Hardcoded key pattern regex (AWS AKIA*, sk-*, ghp_*, api_key=...), excluding obvious placeholder/test values and test/example fixture contexts",
            "C2": "Dependency-manifest-only pin check across requirements/environment/setup.cfg/pyproject dependency sections; ignores non-dependency metadata lines",
            "C3": "Patient metadata patterns in deprecated/legacy/archive directories (regex)",
            "C4": "AST-backed detection of executable fail-open Python exception handlers (except/pass or except/return True)",
            "C6": "Mock-auth, auto-login, or no-auth local/self-host boundary signals surfaced from README/docs/config/code review",
            "CC1": "AST scan for public functions with confidence/threshold parameter defaulting to 0 or 0.0.",
            "CC2": "README code-block import names compared against package __all__; flags names claimed as importable but absent.",
            "CC3": "AST scan for validate_*/check_* functions using len() but no re.match/search structure check.",
            "airi_risk_coverage": "MIT AI Risk Repository V4_03 (airisk.mit.edu, arXiv:2408.12622) local-governed mapping: detectors cross-referenced to AIRI risk IDs through a full local registry, curated runtime bundle, and detector-mapping registry.",
            "BIO-Diagnostics": "Deterministic evidence-only bio diagnostics: conservative SMILES surface checks, SMILES parser-guard checks, silent mock fallback detection, traceability manifest surface checks, and subprocess bio-tool run-trace heuristics.",
            "REG-Scaffolding": "Evidence-only traceability scaffolding signals from manifest/hash/audit-log schema surfaces; intended as structural audit-readiness support rather than compliance proof.",
            "score_cap": "Score ceiling applied when clinical-adjacent signals lack explicit disclaimer",
        },
        "calibration_profile": calibration_profile_metadata(calibration_profile),
    }
    result["audit_freshness"] = _build_audit_freshness(result, audit_date)
    result["regulatory_basis"] = build_regulatory_basis(audit_date)
    result["stage_traceability"] = build_stage_traceability(result)
    result["regulatory_traceability"] = build_regulatory_traceability(result)
    result["reasoning_model"] = build_reasoning_model(result)
    if advisory == "validate":
        result["ai_advisory"] = build_offline_advisory(result)
    elif advisory == "packet":
        result["ai_advisory_input"] = build_provider_advisory_input(result)
        result["ai_advisory_input"]["contract_schemas"] = advisory_contract_schemas()
        result["ai_advisory_input"]["provider_request"] = provider_handoff_metadata(load_provider_config())
        result["ai_advisory_input"]["packet_contract"] = validate_advisory_input_packet(result["ai_advisory_input"])
    elif advisory == "call":
        result["ai_advisory_input"] = build_provider_advisory_input(result)
        result["ai_advisory_input"]["contract_schemas"] = advisory_contract_schemas()
        result["ai_advisory_input"]["provider_request"] = provider_handoff_metadata(load_provider_config())
        result["ai_advisory_input"]["packet_contract"] = validate_advisory_input_packet(result["ai_advisory_input"])
        result["ai_advisory"] = execute_advisory_call(result)
    if advisory_response_path is not None:
        result["ai_advisory"] = validate_advisory_response_file(result, advisory_response_path)
    return result


def _normalize_evidence_finding(finding: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(finding)
    normalized.setdefault("evidence_status", _default_evidence_status(normalized.get("status", "")))
    normalized.setdefault(
        "confidence",
        _default_finding_confidence(normalized.get("status", ""), normalized.get("match_type", "")),
    )
    return normalized


def _default_evidence_status(status: str) -> str:
    mapping = {
        "detected": "confirmed_present",
        "absent": "confirmed_missing",
        "not_detected": "not_found_in_reviewed_sources",
        "not_applicable": "not_applicable",
        "manual_review_required": "manual_review_required",
        "error": "collection_error",
    }
    return mapping.get(str(status), "observed")


def _default_finding_confidence(status: str, match_type: str) -> str:
    status = str(status)
    match_type = str(match_type)
    if status in {"error", "manual_review_required"}:
        return "low"
    if status == "not_detected":
        return "medium"
    if match_type in {"ast", "regex", "file_presence", "dependency"}:
        return "high"
    if match_type in {"aggregate", "metadata", "limit"}:
        return "medium"
    return "medium"


def _build_audit_freshness(result: dict[str, Any], audit_date: date) -> dict[str, Any]:
    classification = result.get("classification", {})
    file_hashes = result.get("file_hashes_sha256", {})
    commit = result.get("target", {}).get("commit")
    ca_severity = classification.get("ca_severity", "none")
    review_after_days = 45 if ca_severity != "none" else 90
    freshness_basis = "clinical_adjacent_short_cycle" if ca_severity != "none" else "standard_cycle"
    expires_on = audit_date + timedelta(days=review_after_days)
    change_triggers = [
        "git_commit_changed",
        "readme_or_docs_claim_surface_changed",
        "dependency_manifest_changed",
        "dataset_or_model_reference_changed",
        "ci_or_reproducibility_surface_changed",
        "changelog_or_release_hygiene_surface_changed",
    ]
    reasons: list[str] = []
    if not commit:
        reasons.append("git_commit_unavailable")
    if not file_hashes:
        reasons.append("key_file_hashes_unavailable")
    return {
        "review_after_days": review_after_days,
        "freshness_basis": freshness_basis,
        "expires_on": expires_on.isoformat(),
        "expired": audit_date > expires_on,
        "anchored_commit": commit,
        "hashes_available_for": sorted(file_hashes.keys()),
        "change_triggered_reaudit_supported": bool(commit) or bool(file_hashes),
        "change_triggered_reaudit_recommended_now": bool(reasons),
        "change_triggered_reaudit_reasons": reasons,
        "change_triggers": change_triggers,
    }


def _score_stage_1(readme: str, docs_text: str, package_text: str, ca_severity: str, has_disclaimer: bool) -> tuple[int, dict[str, Any]]:
    clinical_adjacent = ca_severity != "none"
    responsibility_text = "\n".join([readme, docs_text])
    score = 60
    items: dict[str, Any] = {"baseline": {"score": 60, "evidence": "Non-nascent README evidence baseline."}}
    if readme and BIO_TERMS.search(readme):
        score += _add_stage1_item(items, "S1_domain_readme", 10, "README exposes bio/medical domain vocabulary.")
    if package_text and BIO_TERMS.search(package_text):
        score += _add_stage1_item(items, "S1_domain_package", 5, "Package metadata exposes bio/medical domain vocabulary.")
    hype_penalties = (
        ("H1_clinical_certainty_hype", HYPE_CLINICAL_CERTAINTY, -10, "Clinical certainty or deployment-readiness claim detected."),
        ("H2_regulatory_approval_hype", HYPE_REGULATORY_APPROVAL, -10, "Regulatory approval or clearance claim detected."),
        ("H3_autonomous_replacement_hype", HYPE_AUTONOMOUS_REPLACEMENT, -10, "Autonomous clinician-replacement claim detected."),
        ("H4_breakthrough_marketing_hype", HYPE_BREAKTHROUGH, -5, "Marketing hype language detected."),
        ("H5_universal_generalization_hype", HYPE_UNIVERSAL_GENERALIZATION, -5, "Universal generalization claim detected."),
        ("H6_perfect_accuracy_hype", HYPE_PERFECT_ACCURACY, -10, "Perfect or guaranteed accuracy claim detected."),
    )
    for key, pattern, penalty, evidence in hype_penalties:
        if _has_claim_match(pattern, readme):
            score += _add_stage1_item(items, key, penalty, evidence)
    if LIMITATIONS_SECTION.search(readme):
        score += _add_stage1_item(items, "R1_limitations_section", 15, "README contains an explicit limitations or validation-boundary section.")
    if REGULATORY_FRAMEWORK_TERMS.search(responsibility_text):
        score += _add_stage1_item(items, "R2_regulatory_framework", 15, "Regulatory, IRB, SaMD, or clinical-reporting framework language detected.")
    elif WEAK_REGULATORY_SELF_ASSERTION_TERMS.search(responsibility_text):
        score += _add_stage1_item(items, "R2_regulatory_framework", 5, "Self-asserted privacy/compliance language detected without stronger regulatory-framework evidence.")
    elif ca_severity == "CA-DIRECT":
        score += _add_stage1_item(items, "R2_regulatory_framework", -10, "CA-DIRECT surface lacks regulatory or governance framework language.")
    elif ca_severity == "CA-INDIRECT":
        score += _add_stage1_item(items, "R2_regulatory_framework", -5, "CA-INDIRECT surface lacks regulatory or governance framework language.")
    if has_disclaimer:
        score += _add_stage1_item(items, "R3_clinical_disclaimer", 10, "Explicit non-clinical or non-diagnostic boundary detected.")
    elif ca_severity == "CA-DIRECT":
        score += _add_stage1_item(items, "R3_clinical_disclaimer", -10, "CA-DIRECT surface lacks explicit non-clinical or non-diagnostic boundary.")
    elif ca_severity == "CA-INDIRECT":
        score += _add_stage1_item(items, "R3_clinical_disclaimer", -5, "CA-INDIRECT surface lacks explicit non-clinical or non-diagnostic boundary.")
    if DEMOGRAPHIC_BIAS_TERMS.search(responsibility_text):
        score += _add_stage1_item(items, "R4_demographic_bias_boundary", 10, "Demographic, subgroup, fairness, bias, or validation-cohort language detected.")
    if REPRODUCIBILITY_TERMS.search(responsibility_text):
        score += _add_stage1_item(items, "R5_reproducibility_provisions", 10, "Reproducibility, replication, seed, lockfile, or checksum language detected.")
    if not readme:
        score += _add_stage1_item(items, "S1_missing_readme", -20, "No root README detected.")
    final = _clamp(score)
    items["calculation"] = f"60 plus Stage 1 evidence additions/deductions = {final}"
    items["stage_1_score"] = final
    return final, items


def _add_stage1_item(items: dict[str, Any], key: str, score: int, evidence: str) -> int:
    items[key] = {"score": score, "evidence": evidence}
    return score


def _score_stage_2r(
    readme: str,
    docs_text: str,
    package_text: str,
    workflow_text: str,
    test_text: str,
    changelog_text: str,
    code_text: str,
    clinical_adjacent: bool,
    has_disclaimer: bool,
) -> tuple[int, dict[str, Any]]:
    items: dict[str, Any] = {
        "baseline": {
            "score": 60,
            "evidence": "Non-nascent local repository baseline.",
            "detector_id": "stage2r_baseline",
            "decision_basis": "repository has sufficient local structure to enter repo-local consistency review",
        }
    }
    score = 60
    if readme and package_text and _shared_terms(readme, package_text):
        score += _add_stage2r_item(
            items,
            "R2R_1_readme_package_code_alignment",
            15,
            "README has domain overlap with package metadata or entry points.",
            decision_basis="shared bio-domain terms detected across README and package metadata",
        )
    if readme and docs_text and _shared_terms(readme, docs_text):
        score += _add_stage2r_item(
            items,
            "R2R_2_readme_docs_alignment",
            10,
            "README has domain overlap with docs/tutorial/troubleshooting surfaces.",
            decision_basis="shared bio-domain terms detected across README and docs/tutorial surfaces",
        )
    if (workflow_text or test_text) and re.search(r"(test|pytest|unittest|ci|workflow)", readme + workflow_text + test_text, re.I):
        score += _add_stage2r_item(
            items,
            "R2R_3_readme_test_ci_alignment",
            10,
            "Test/CI surfaces are present and locally consistent.",
            decision_basis="workflow/test support terms found across README and local support surfaces",
        )
    if _limitation_repeated(readme, docs_text, changelog_text):
        score += _add_stage2r_item(
            items,
            "R2R_4_limitation_repetition",
            10,
            "Limitation or validation-boundary language repeats across independent repository surfaces.",
            decision_basis="limitations or validation-boundary language detected in at least two repository surfaces",
        )
    if _has_internal_clinical_contradiction(readme, docs_text, package_text, has_disclaimer):
        score += _add_stage2r_item(
            items,
            "R2R_D1_internal_clinical_boundary_contradiction",
            -20,
            "Explicit clinical-use boundary conflicts with clinical deployment or decision-support claims.",
            decision_basis="explicit clinical boundary and clinical deployment/support claims co-occur in reviewed sources",
        )
    if clinical_adjacent and not has_disclaimer:
        score += _add_stage2r_item(
            items,
            "R2R_D2_missing_clinical_use_boundary",
            -20,
            "Clinical-adjacent surfaces exist without an explicit non-diagnostic/non-clinical boundary.",
            decision_basis="clinical_adjacent=True and explicit non-clinical boundary was not detected",
            tier_impact="can contribute to clinical score ceilings and hard-floor review paths when stronger clinical deployment or certainty claims are also present",
        )
    if _version_mismatch(readme, package_text):
        score += _add_stage2r_item(
            items,
            "R2R_D3_stale_metadata",
            -10,
            "README version metadata conflicts with package metadata version.",
            decision_basis="README version marker and package version marker differ",
        )
    if _unsupported_workflow_claim(readme, docs_text, package_text, workflow_text, test_text, code_text):
        score += _add_stage2r_item(
            items,
            "R2R_D4_unsupported_workflow_claim",
            -15,
            "README/docs claim runnable workflow, CLI, test, or demo support without matching local support surfaces.",
            decision_basis="workflow/demo/CLI claims detected while workflow, tests, or local support entrypoints are absent",
        )
    final = _clamp(score)
    items["calculation"] = f"60 plus local consistency additions/deductions = {final}"
    items["stage_2r_score"] = final
    items["verdict"] = _stage2r_verdict(final)
    return final, items


def _add_stage2r_item(
    items: dict[str, Any],
    key: str,
    score: int,
    evidence: str,
    decision_basis: str | None = None,
    tier_impact: str | None = None,
) -> int:
    items[key] = {
        "score": score,
        "evidence": evidence,
        "detector_id": key,
        "decision_basis": decision_basis or evidence,
        **({"tier_impact": tier_impact} if tier_impact else {}),
    }
    return score


def _stage2r_verdict(score: int) -> str:
    if score >= 80:
        return "Strong Local Consistency"
    if score >= 60:
        return "Mixed Local Consistency"
    return "Local Contradiction / Insufficient Consistency"


def _limitation_repeated(readme: str, docs_text: str, changelog_text: str) -> bool:
    lanes = [
        bool(_has_limitation_language(readme)),
        bool(_has_limitation_language(docs_text)),
        bool(_has_limitation_language(changelog_text)),
    ]
    return sum(lanes) >= 2


def _has_limitation_language(text: str) -> bool:
    return bool(text and (LIMITATIONS_SECTION.search(text) or BIAS_LIMITATION_TERMS.search(text)))


def _has_internal_clinical_contradiction(readme: str, docs_text: str, package_text: str, has_disclaimer: bool) -> bool:
    if not has_disclaimer:
        return False
    return bool(STAGE2R_CLINICAL_DEPLOYMENT_CLAIMS.search("\n".join([readme, docs_text, package_text])))


def _version_mismatch(readme: str, package_text: str) -> bool:
    readme_version = _readme_version(readme)
    package_version = _package_version(package_text)
    return bool(readme_version and package_version and readme_version != package_version)


def _readme_version(text: str) -> str | None:
    match = re.search(r"(?im)\b(?:version|release)\s*[:= ]\s*v?([0-9]+(?:\.[0-9]+){1,3}(?:[-+][A-Za-z0-9_.-]+)?)\b", text)
    return match.group(1).lower() if match else None


def _package_version(text: str) -> str | None:
    match = re.search(r"(?im)^\s*version\s*=\s*['\"]v?([0-9]+(?:\.[0-9]+){1,3}(?:[-+][A-Za-z0-9_.-]+)?)['\"]", text)
    return match.group(1).lower() if match else None


def _unsupported_workflow_claim(readme: str, docs_text: str, package_text: str, workflow_text: str, test_text: str, code_text: str) -> bool:
    claimed = bool(STAGE2R_WORKFLOW_CLAIMS.search("\n".join([readme, docs_text])))
    supported = bool(workflow_text or test_text or code_text or STAGE2R_ENTRYPOINT_TERMS.search(package_text))
    return claimed and not supported


def _score_stage_3(target: Path, readme: str, docs_text: str, workflow_text: str, test_text: str, dep_text: str, changelog_text: str = "") -> tuple[int, dict[str, Any]]:
    ci = 15 if workflow_text else 0
    normalized_test_text = test_text.replace("_", " ")
    tests = 15 if test_text and BIO_TERMS.search(normalized_test_text) else 8 if test_text else 0

    changelog_path = next((p for p in [target / "CHANGELOG.md", target / "CHANGELOG", target / "NEWS.md"] if p.exists()), None)
    changelog, changelog_evidence = _score_changelog(changelog_path, changelog_text)

    provenance, provenance_evidence = _score_provenance(dep_text, readme, docs_text)

    bias_text = "\n".join([readme, docs_text])
    bias, bias_evidence = _score_bias(bias_text, test_text)

    coi_text = "\n".join([readme, docs_text, _read_first(target, ["FUNDING.md", "CITATION.cff", "AUTHORS.md"])])
    coi = 5 if COI_FUNDING_TERMS.search(coi_text) else 0
    raw_score = ci + tests + changelog + provenance + bias + coi
    raw_max = 80
    score = round((raw_score / raw_max) * 100)
    rubric = {
        "T1_CI_CD": {
            "score": ci,
            "max": 15,
            "evidence": "Workflow files detected." if ci else "No workflow files detected.",
            "detector_id": "S3_T1_workflow_files",
            "decision_basis": "workflow files present under .github/workflows/" if ci else "no workflow files present under .github/workflows/",
        },
        "T2_domain_tests": {
            "score": tests,
            "max": 15,
            "evidence": "Domain-specific test text detected." if tests == 15 else "Tests present but domain specificity is limited." if tests else "No tests detected.",
            "detector_id": "S3_T2_domain_tests",
            "decision_basis": "tests surface present with bio-domain vocabulary" if tests == 15 else "tests surface present without clear bio-domain specificity" if tests else "no tests surface detected",
        },
        "T3_changelog_release_hygiene": {
            "score": changelog,
            "max": 15,
            "evidence": changelog_evidence,
            "detector_id": "S3_T3_changelog_release_hygiene",
            "decision_basis": "CHANGELOG/NEWS presence plus bug-fix or patch-entry detection",
        },
        "B1_data_provenance_controls": {
            "score": provenance,
            "max": 15,
            "evidence": provenance_evidence,
            "detector_id": "S3_B1_dependency_manifest",
            "decision_basis": "dependency or lock manifest presence plus data-source, dataset, or IRB language review",
        },
        "B2_bias_limitations": {
            "score": bias,
            "max": 15,
            "evidence": bias_evidence,
            "detector_id": "S3_B2_bias_limitations",
            "decision_basis": "bias/limitations vocabulary with optional measurement-evidence escalation",
        },
        "B3_coi_funding": {
            "score": coi,
            "max": 5,
            "evidence": "COI, funding, sponsor, or acknowledgement language detected." if coi else "No COI/funding disclosure detected by local CLI scan.",
            "detector_id": "S3_B3_coi_funding",
            "decision_basis": "COI/funding/sponsor language review across README, docs, FUNDING, CITATION, and AUTHORS surfaces",
        },
        "stage_3_raw_total": {"score": raw_score, "max": raw_max, "evidence": "Raw rubric total before normalization to 100."},
    }
    return _clamp(score), rubric


def _score_changelog(changelog_path: Path | None, changelog_text: str) -> tuple[int, str]:
    if not changelog_path:
        return 0, "No changelog detected."
    text = changelog_text or _read_text(changelog_path)
    if CHANGELOG_BUG_TERMS.search(text):
        return 15, f"{changelog_path.name} contains bug-fix, patch, or security entries."
    return 5, f"{changelog_path.name} exists but no bug-fix or patch entries detected."


def _score_provenance(dep_text: str, readme: str, docs_text: str) -> tuple[int, str]:
    if not dep_text:
        return 0, "No dependency/provenance manifest detected."
    surface = "\n".join([readme, docs_text])
    if DATA_SOURCE_NEGATIVE_TERMS.search(surface):
        return 10, "Dependency manifest detected; provenance language appears in a negative or non-approval context."
    if DATA_SOURCE_TERMS.search(surface):
        return 15, "Dependency manifest detected with data source, IRB, or dataset citation language."
    return 10, "Dependency manifest detected; no explicit data source or IRB citation found."


def _score_bias(bias_text: str, test_text: str) -> tuple[int, str]:
    if not BIAS_LIMITATION_TERMS.search(bias_text):
        return 0, "No bias/limitations language detected by local CLI scan."
    if BIAS_MEASUREMENT_TERMS.search(bias_text) or (test_text and BIAS_LIMITATION_TERMS.search(test_text)):
        return 15, "Bias/limitations language with measurement evidence or test coverage detected."
    if LIMITATIONS_SECTION.search(bias_text) or len(BIAS_LIMITATION_TERMS.findall(bias_text)) >= 2:
        return 8, "Structured bias/limitations language detected; no quantitative measurement evidence found."
    return 0, "Only a minimal single-term bias/limitations mention was detected; structured boundary language or measurement evidence was not found."


def _code_integrity_from_findings(
    evidence_ledger: list[dict[str, Any]],
    clinical_adjacent: bool,
    has_disclaimer: bool,
) -> dict[str, Any]:
    detector_defaults = {
        "C1_hardcoded_credentials": ("FAIL", "PASS", "No direct credential patterns detected by local CLI scan."),
        "C2_dependency_pinning": ("WARN", "PASS", "Dependency manifest appears pinned or not present."),
        "C3_dead_or_deprecated_patient_adjacent_paths": ("WARN", "PASS", "No deprecated patient-adjacent metadata patterns detected."),
        "C4_exception_handling_clinical_adjacent_paths": ("WARN", "PASS", "No executable fail-open exception handler detected."),
        "C5_compliance_boundary_integrity": ("WARN", "PASS", "No compliance-boundary integrity warning detected in current report layer."),
        "C6_mock_auth_or_fail_open_boundary": ("WARN", "PASS", "No mock-auth or fail-open local-boundary warning detected in reviewed sources."),
    }
    findings_by_detector: dict[str, list[dict[str, Any]]] = {key: [] for key in detector_defaults}
    for finding in evidence_ledger:
        detector = str(finding.get("detector", ""))
        if detector in findings_by_detector:
            findings_by_detector[detector].append(finding)

    result: dict[str, Any] = {}
    for detector, (detected_status, pass_status, pass_message) in detector_defaults.items():
        detected = [f for f in findings_by_detector[detector] if f.get("status") == "detected"]
        if detected:
            evidence = [_finding_summary(f) for f in detected[:5]]
            result[detector] = {"status": detected_status, "evidence": evidence}
        else:
            result[detector] = {"status": pass_status, "evidence": [pass_message]}

    external_dependency_findings = [
        f
        for f in evidence_ledger
        if f.get("detector") == "R2R_D5_single_external_service_dependency" and f.get("status") == "detected"
    ]
    if external_dependency_findings:
        result["C2_dependency_pinning"] = {
            "status": "WARN",
            "evidence": [
                "External operational dependency signal surfaced in code-integrity lane.",
                *[_finding_summary(f) for f in external_dependency_findings[:3]],
            ],
        }

    c5_evidence: list[str] = []
    unsupported_claim_findings = [
        f
        for f in evidence_ledger
        if f.get("detector") == "S1_R2_unsupported_legal_or_compliance_claim" and f.get("status") == "detected"
    ]
    if unsupported_claim_findings:
        c5_evidence.append("Unsupported legal/compliance claim surfaced in boundary-integrity lane.")
        c5_evidence.extend(_finding_summary(f) for f in unsupported_claim_findings[:2])
    if clinical_adjacent and not has_disclaimer:
        c5_evidence.append("Clinical-adjacent surfaces exist without an explicit non-diagnostic/non-clinical boundary.")
    if c5_evidence:
        result["C5_compliance_boundary_integrity"] = {
            "status": "WARN",
            "evidence": c5_evidence[:5],
        }

    c6_findings = [
        f
        for f in evidence_ledger
        if f.get("detector") == "C6_mock_auth_or_fail_open_boundary" and f.get("status") == "detected"
    ]
    if c6_findings:
        result["C6_mock_auth_or_fail_open_boundary"] = {
            "status": "WARN",
            "evidence": [
                "Mock-auth or auto-login boundary surfaced in code-integrity lane.",
                *[_finding_summary(f) for f in c6_findings[:4]],
            ][:5],
        }
    return result


def _finding_summary(finding: dict[str, Any]) -> str:
    file = str(finding.get("file", "."))
    line = int(finding.get("line", 0) or 0)
    snippet = str(finding.get("snippet", "")).strip()
    location = file if file == "." or not line else f"{file}:{line}"
    if snippet:
        return f"{location} {snippet}"
    return location


def _list_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def _read_first(root: Path, names: list[str]) -> str:
    for name in names:
        path = root / name
        if path.exists() and path.is_file():
            return _read_text(path)
    return ""


def _read_many(root: Path, max_files: int = 100, suffixes: set[str] | None = None) -> str:
    if not root.exists():
        return ""
    chunks: list[str] = []
    count = 0
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if suffixes is not None and path.suffix.lower() not in suffixes:
            continue
        if suffixes is None and path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        chunks.append(_read_text(path))
        count += 1
        if count >= max_files:
            break
    return "\n".join(chunks)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _read_deprecated_text(root: Path, max_files: int = 120) -> str:
    chunks: list[str] = []
    count = 0
    deprecated_names = {"deprecated", "legacy", "archive", "archives", "old"}
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        lowered_parts = {part.lower() for part in path.parts}
        if not lowered_parts & deprecated_names:
            continue
        chunks.append(_read_text(path))
        count += 1
        if count >= max_files:
            break
    return "\n".join(chunks)


def _repo_name(target: Path) -> str:
    remote = _git(target, "remote", "get-url", "origin")
    if remote:
        cleaned = remote.rstrip("/").removesuffix(".git")
        return "/".join(cleaned.split("/")[-2:])
    return target.name


def _git(target: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={target.as_posix()}", "-C", str(target), *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _shared_terms(left: str, right: str) -> bool:
    left_terms = {m.group(0).lower() for m in BIO_TERMS.finditer(left)}
    right_terms = {m.group(0).lower() for m in BIO_TERMS.finditer(right)}
    return bool(left_terms & right_terms)


def _dependency_unpinned(dep_text: str) -> bool:
    if not dep_text:
        return False
    dep_lines = _dependency_entries(dep_text)
    return any(_is_unpinned_dependency(line) for line in dep_lines[:100])


def _dependency_entries(dep_text: str) -> list[str]:
    entries: list[str] = []
    in_pyproject_deps = False
    for raw in dep_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r"^(dependencies|requires|install_requires|pdf|demo)\s*=", line):
            in_pyproject_deps = "[" in line and "]" not in line
            entries.extend(_quoted_dependency_strings(line))
            continue
        if in_pyproject_deps:
            entries.extend(_quoted_dependency_strings(line))
            if "]" in line:
                in_pyproject_deps = False
            continue
        if re.match(r"^[-A-Za-z0-9_.]+(\[[^\]]+\])?(\s*(==|===|>=|<=|~=|!=|>|<|@)\s*|$)", line):
            entries.append(line)
    return entries


def _quoted_dependency_strings(line: str) -> list[str]:
    values = [m.group(1) or m.group(2) for m in re.finditer(r'"([^"]+)"|\'([^\']+)\'', line)]
    return [v.strip() for v in values if re.match(r"^[A-Za-z0-9_.-]+(\[[^\]]+\])?(\s*(==|===|>=|<=|~=|!=|>|<|@)\s*|$)", v.strip())]


def _is_unpinned_dependency(line: str) -> bool:
    normalized = line.split("#", 1)[0].strip().rstrip(",")
    if not normalized or normalized.startswith(("-", "[", "{")):
        return False
    if EXACT_PINNED_DEP.search(normalized):
        return False
    if LOOSE_DEP.search(normalized):
        return True
    return bool(re.match(r"^[A-Za-z0-9_.-]+(\[[^\]]+\])?(\s*;.*)?$", normalized))


def _classify_ca_severity(surface_text: str) -> str:
    if _has_claim_match(CA_DIRECT_TERMS, surface_text):
        return "CA-DIRECT"
    if _has_claim_match(CA_INDIRECT_TERMS, surface_text):
        return "CA-INDIRECT"
    return "none"


def _t0_hard_floor(surface_text: str, ca_severity: str, has_disclaimer: bool) -> bool:
    return ca_severity == "CA-DIRECT" and not has_disclaimer and _has_claim_match(T0_HARD_FLOOR_TERMS, surface_text)


def _has_claim_match(pattern: re.Pattern[str], text: str) -> bool:
    return any(pattern.search(line) and not META_EVIDENCE_LINE.search(line) for line in text.splitlines())


def _score_cap(ca_severity: str, has_disclaimer: bool, t0_hard_floor: bool) -> int | None:
    if t0_hard_floor:
        return 39
    if ca_severity != "none" and not has_disclaimer:
        return 69
    return None


def _positive_evidence(workflow_text: str, test_text: str, docs_text: str, package_text: str) -> list[str]:
    items: list[str] = []
    if package_text:
        items.append("Package metadata was available for repo-local consistency checks.")
    if workflow_text:
        items.append("CI workflow files were detected.")
    if test_text:
        items.append("Test files were detected.")
    if docs_text:
        items.append("Documentation files were detected.")
    return items or ["No strong positive local evidence detected by the CLI scan."]


def _risks(
    clinical_adjacent: bool,
    has_disclaimer: bool,
    code_integrity: dict[str, Any],
    evidence_ledger: list[dict[str, Any]],
    cc_summary: dict[str, Any] | None = None,
    self_asserted_compliance: bool = False,
) -> list[str]:
    risks: list[str] = []
    if clinical_adjacent and not has_disclaimer:
        _append_unique_risk(risks, "Clinical-adjacent surfaces exist without an explicit non-diagnostic/non-clinical boundary.")
    if self_asserted_compliance:
        _append_unique_risk(risks, "Self-asserted compliance or privacy-governance claim requires independent verification.")
    if _detector_detected(evidence_ledger, "S1_R2_unsupported_legal_or_compliance_claim"):
        _append_unique_risk(risks, "Legal, privacy, or compliance claim appears without supporting governance or security-grounding evidence in reviewed repository sources.")
    if _detector_detected(evidence_ledger, "R2R_D5_single_external_service_dependency"):
        _append_unique_risk(risks, "Core workflow appears materially dependent on named external service providers; local or self-host claims may overstate operational independence.")
    for key, item in code_integrity.items():
        if item["status"] in {"WARN", "FAIL"}:
            _append_unique_risk(risks, _humanize_code_integrity_risk(key, item))
    for key, item in (cc_summary or {}).items():
        if isinstance(item, dict) and item.get("status") == "WARN":
            _append_unique_risk(risks, _humanize_contract_risk(key, item))
    return risks or ["No major local risks detected by the CLI scan."]


def _append_unique_risk(risks: list[str], text: str) -> None:
    if text and text not in risks:
        risks.append(text)


def _humanize_code_integrity_risk(key: str, item: dict[str, Any]) -> str:
    evidence = str((item.get("evidence") or [""])[0]).strip()
    if evidence:
        return evidence
    label_map = {
        "C1_hardcoded_credentials": "Hardcoded credential signal surfaced in code-integrity lane.",
        "C2_dependency_pinning": "Dependency pinning or external operational dependency signal surfaced in code-integrity lane.",
        "C3_dead_or_deprecated_patient_adjacent_paths": "Deprecated or legacy patient-adjacent path signal surfaced in code-integrity lane.",
        "C4_exception_handling_clinical_adjacent_paths": "Executable fail-open exception signal surfaced in code-integrity lane.",
        "C5_compliance_boundary_integrity": "Compliance-boundary integrity signal surfaced in code-integrity lane.",
        "C6_mock_auth_or_fail_open_boundary": "Mock-auth or auto-login trust-boundary signal surfaced in code-integrity lane.",
    }
    return label_map.get(key, f"{key} surfaced in code-integrity lane.")


def _humanize_contract_risk(key: str, item: dict[str, Any]) -> str:
    count = item.get("count", "?")
    evidence = str((item.get("evidence") or [""])[0]).strip()
    if evidence:
        return evidence
    return f"Contract check {key} surfaced reviewable issues (count={count})."


def _detector_summary(evidence_ledger: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_detector: dict[str, dict[str, int]] = {}
    for finding in evidence_ledger:
        status = str(finding.get("status", "unknown"))
        detector = str(finding.get("detector", "unknown"))
        by_status[status] = by_status.get(status, 0) + 1
        bucket = by_detector.setdefault(detector, {})
        bucket[status] = bucket.get(status, 0) + 1
    return {
        "total_findings": len(evidence_ledger),
        "by_status": by_status,
        "by_detector": by_detector,
    }


def _detector_detected(evidence_ledger: list[dict[str, Any]], detector: str) -> bool:
    return any(
        str(finding.get("detector", "")) == detector and str(finding.get("status", "")) == "detected"
        for finding in evidence_ledger
    )


def _hash_key_files(target: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in ["README.md", "pyproject.toml", "environment.yml", "requirements.txt"]:
        path = target / name
        if path.exists() and path.is_file():
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    return hashes


def _tier(score: int) -> str:
    if score <= 39:
        return "T0 Rejected"
    if score <= 54:
        return "T1 Quarantine"
    if score <= 69:
        return "T2 Caution"
    if score <= 84:
        return "T3 Supervised"
    return "T4 Candidate"


def _use_scope(score: int) -> str:
    if score <= 39:
        return "Do not rely on this repository without independent expert validation."
    if score <= 54:
        return "Exploratory review only; no patient-adjacent use."
    if score <= 69:
        return "Research reference and supervised non-clinical technical review only."
    return "Supervised institutional review candidate; clinical deployment still requires independent validation."


def _clamp(score: int) -> int:
    return max(0, min(100, int(score)))
