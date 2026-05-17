from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from pathlib import Path

from .evidence import EvidenceFinding
from .detector_utils import (
    add_finding,
    existing_named_files,
    is_fixture_like_path,
    is_unpinned_dependency,
    iter_code_files,
    iter_deprecated_files,
    iter_text_files,
    manifest_dependency_entries,
    read_text,
    relative_path,
    source_line,
)
from .patterns import (
    BIAS_LIMITATION_TERMS,
    BIAS_MEASUREMENT_TERMS,
    BIO_TERMS,
    CHANGELOG_BUG_TERMS,
    COI_FUNDING_TERMS,
    DATA_SOURCE_TERMS,
    DEMOGRAPHIC_BIAS_TERMS,
    DISCLAIMER_TERMS,
    HYPE_AUTONOMOUS_REPLACEMENT,
    HYPE_BREAKTHROUGH,
    HYPE_CLINICAL_CERTAINTY,
    HYPE_PERFECT_ACCURACY,
    HYPE_REGULATORY_APPROVAL,
    HYPE_UNIVERSAL_GENERALIZATION,
    LEGAL_COMPLIANCE_CLAIM_TERMS,
    LEGAL_COMPLIANCE_GROUNDING_TERMS,
    LEGAL_COMPLIANCE_NEGATION_TERMS,
    LIMITATIONS_SECTION,
    MOCK_AUTH_FAIL_OPEN_TERMS,
    PATIENT_METADATA,
    PLACEHOLDER_SECRET_VALUES,
    REGULATORY_FRAMEWORK_TERMS,
    REPRODUCIBILITY_TERMS,
    SECRET_TERMS,
    WEAK_REGULATORY_SELF_ASSERTION_TERMS,
    LOCAL_SELF_HOST_CLAIM_TERMS,
)

_EXTERNAL_PROVIDER_ENV_MAP: dict[str, str] = {
    "VALYU_API_KEY": "Valyu",
    "DAYTONA_API_KEY": "Daytona",
    "OPENAI_API_KEY": "OpenAI",
    "ANTHROPIC_API_KEY": "Anthropic",
    "GEMINI_API_KEY": "Gemini",
    "OPENAI_COMPATIBLE_API_KEY": "OpenAI-compatible",
    "SUPABASE_SERVICE_ROLE_KEY": "Supabase",
    "SUPABASE_ANON_KEY": "Supabase",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "Supabase",
}

_REQUIRED_HINT = re.compile(r"\brequired\b", re.I)
_OPTIONAL_HINT = re.compile(r"\boptional\b", re.I)
_API_KEY_ASSIGNMENT = re.compile(r"^\s*([A-Z0-9_]+_API_KEY)\s*=")
_PROVIDER_LINE_HINT = re.compile(r"\b(api key|powered by|used for|built with|platform)\b", re.I)


def collect_surface_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> None:
    readme_paths = existing_named_files(target, ["README.md", "README.rst", "readme.md"])
    docs_paths = list(iter_text_files(target / "docs", max_files=30))
    package_paths = existing_named_files(target, ["pyproject.toml", "setup.py", "setup.cfg", "package.json"])
    config_paths = existing_named_files(target, [".env.example", ".env.local.example", ".env.sample", "env.example"])
    funding_paths = existing_named_files(target, ["FUNDING.md", "CITATION.cff", "AUTHORS.md"])
    workflow_paths = list(iter_text_files(target / ".github" / "workflows", max_files=20))
    test_paths = list(iter_text_files(target / "tests", max_files=40))
    provenance_manifest_paths = existing_named_files(
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
    dependency_pinning_paths = existing_named_files(
        target,
        [
            "environment.yml",
            "requirements.txt",
            "pyproject.toml",
            "setup.cfg",
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "npm-shrinkwrap.json",
        ],
    )
    changelog_paths = existing_named_files(target, ["CHANGELOG.md", "CHANGELOG", "NEWS.md"])
    code_paths = list(iter_code_files(target, max_files=200))
    deprecated_paths = list(iter_deprecated_files(target, max_files=120))

    regex_detector(target, findings, counters, "S1_readme_bio_terms", "bio_terms_v1", BIO_TERMS, readme_paths, "README exposes bio/medical vocabulary.")
    regex_detector(target, findings, counters, "S1_clinical_boundary", "clinical_boundary_v1", DISCLAIMER_TERMS, [*readme_paths, *docs_paths], "Explicit non-clinical or non-diagnostic boundary language detected.")
    regex_detector(target, findings, counters, "S1_H1_clinical_certainty_hype", "hype_clinical_certainty_v1", HYPE_CLINICAL_CERTAINTY, readme_paths, "Clinical certainty or deployment-readiness claim detected.")
    regex_detector(target, findings, counters, "S1_H2_regulatory_approval_hype", "hype_regulatory_approval_v1", HYPE_REGULATORY_APPROVAL, readme_paths, "Regulatory approval or clearance claim detected.")
    regex_detector(target, findings, counters, "S1_H3_autonomous_replacement_hype", "hype_autonomous_replacement_v1", HYPE_AUTONOMOUS_REPLACEMENT, readme_paths, "Autonomous clinician-replacement claim detected.")
    regex_detector(target, findings, counters, "S1_H4_breakthrough_marketing_hype", "hype_breakthrough_marketing_v1", HYPE_BREAKTHROUGH, readme_paths, "Marketing hype language detected.")
    regex_detector(target, findings, counters, "S1_H5_universal_generalization_hype", "hype_universal_generalization_v1", HYPE_UNIVERSAL_GENERALIZATION, readme_paths, "Universal generalization claim detected.")
    regex_detector(target, findings, counters, "S1_H6_perfect_accuracy_hype", "hype_perfect_accuracy_v1", HYPE_PERFECT_ACCURACY, readme_paths, "Perfect or guaranteed accuracy claim detected.")
    regex_detector(target, findings, counters, "S1_R1_limitations_section", "limitations_section_v1", LIMITATIONS_SECTION, readme_paths, "Explicit limitations or validation-boundary section detected.")
    regex_detector(target, findings, counters, "S1_R2_regulatory_framework", "regulatory_framework_v1", REGULATORY_FRAMEWORK_TERMS, [*readme_paths, *docs_paths], "Regulatory, IRB, SaMD, or clinical-reporting framework language detected.")
    regex_detector(target, findings, counters, "S1_R2_weak_regulatory_self_assertion", "weak_regulatory_self_assertion_v1", WEAK_REGULATORY_SELF_ASSERTION_TERMS, [*readme_paths, *docs_paths], "Self-asserted privacy/compliance language detected without stronger regulatory-framework evidence.")
    unsupported_legal_or_compliance_claim_detector(target, findings, counters, [*readme_paths, *docs_paths, *package_paths])
    regex_detector(target, findings, counters, "S1_R4_demographic_bias_boundary", "demographic_bias_boundary_v1", DEMOGRAPHIC_BIAS_TERMS, [*readme_paths, *docs_paths], "Demographic, subgroup, fairness, bias, or validation-cohort language detected.")
    regex_detector(target, findings, counters, "S1_R5_reproducibility_provisions", "reproducibility_provisions_v1", REPRODUCIBILITY_TERMS, [*readme_paths, *docs_paths], "Reproducibility, replication, seed, lockfile, or checksum language detected.")
    file_presence_detector(target, findings, counters, "S3_T1_workflow_files", "workflow_presence_v1", workflow_paths, "Workflow file exists.")
    regex_line_detector(target, findings, counters, "S3_T2_domain_tests", "domain_tests_bio_terms_v1", BIO_TERMS, test_paths, "Domain-specific test text detected.", normalize_underscores=True)
    file_presence_detector(target, findings, counters, "S3_T3_changelog_release_hygiene", "changelog_presence_v1", changelog_paths, "Changelog or release-history file exists.")
    regex_detector(target, findings, counters, "S3_T3_changelog_bugfix_evidence", "changelog_bugfix_terms_v1", CHANGELOG_BUG_TERMS, changelog_paths, "Bug-fix, patch, or security entry detected in changelog.")
    file_presence_detector(target, findings, counters, "S3_B1_dependency_manifest", "dependency_manifest_presence_v1", provenance_manifest_paths, "Dependency or environment manifest exists.")
    regex_detector(target, findings, counters, "S3_B1_data_source_language", "data_source_terms_v1", DATA_SOURCE_TERMS, [*readme_paths, *docs_paths], "Data source, dataset citation, IRB, or provenance language detected.")
    regex_detector(target, findings, counters, "S3_B2_bias_limitations", "bias_limitations_v2", BIAS_LIMITATION_TERMS, [*readme_paths, *docs_paths], "Bias, limitation, or validation-boundary language detected.")
    regex_detector(target, findings, counters, "S3_B2_measurement_evidence", "bias_measurement_terms_v1", BIAS_MEASUREMENT_TERMS, [*readme_paths, *docs_paths, *test_paths], "Quantitative bias/limitation measurement or related test evidence detected.")
    regex_detector(target, findings, counters, "S3_B3_coi_funding", "coi_funding_v1", COI_FUNDING_TERMS, [*readme_paths, *docs_paths, *funding_paths], "COI, funding, sponsor, or acknowledgement language detected.")
    regex_detector(target, findings, counters, "S2_package_bio_terms", "package_bio_terms_v1", BIO_TERMS, package_paths, "Package metadata exposes bio/medical vocabulary.")
    external_service_dependency_detector(target, findings, counters, [*readme_paths, *docs_paths, *package_paths], config_paths)
    mock_auth_or_fail_open_boundary_detector(
        target,
        findings,
        counters,
        [*readme_paths, *docs_paths, *package_paths],
        config_paths,
        code_paths,
    )
    credential_detector(target, findings, counters, code_paths)
    dependency_pinning_detector(target, findings, counters, dependency_pinning_paths)
    regex_detector(target, findings, counters, "C3_dead_or_deprecated_patient_adjacent_paths", "deprecated_patient_metadata_v1", PATIENT_METADATA, deprecated_paths, "Patient-adjacent metadata pattern detected in deprecated/legacy/archive path.")
    fail_open_detector(target, findings, counters, code_paths)


def regex_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    detector: str,
    pattern_id: str,
    pattern: re.Pattern[str],
    paths: Iterable[Path],
    explanation: str,
) -> None:
    detected = False
    for path in sorted(set(paths), key=lambda p: relative_path(target, p).as_posix()):
        text = read_text(path)
        lines = text.splitlines()
        for match in pattern.finditer(text):
            detected = True
            line = text.count("\n", 0, match.start()) + 1
            add_finding(target, findings, counters, detector, pattern_id, "detected", "info", path, line, source_line(lines, line), "regex", explanation, {"match": match.group(0)})
    if not detected:
        add_finding(target, findings, counters, detector, pattern_id, "not_detected", "info", Path("."), 0, "", "regex", f"No evidence detected for {detector}.")


def regex_line_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    detector: str,
    pattern_id: str,
    pattern: re.Pattern[str],
    paths: Iterable[Path],
    explanation: str,
    normalize_underscores: bool = False,
) -> None:
    detected = False
    for path in sorted(set(paths), key=lambda p: relative_path(target, p).as_posix()):
        lines = read_text(path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            searchable = line.replace("_", " ") if normalize_underscores else line
            if not pattern.search(searchable):
                continue
            detected = True
            add_finding(target, findings, counters, detector, pattern_id, "detected", "info", path, line_number, line, "regex", explanation)
    if not detected:
        add_finding(target, findings, counters, detector, pattern_id, "not_detected", "info", Path("."), 0, "", "regex", f"No evidence detected for {detector}.")


def dependency_pinning_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    paths: Iterable[Path],
) -> None:
    unpinned_found = False
    manifest_found = False
    for path in sorted(set(paths), key=lambda p: relative_path(target, p).as_posix()):
        manifest_found = True
        if _check_unpinned_deps_in_file(target, path, findings, counters):
            unpinned_found = True
    if not unpinned_found:
        status = "not_detected" if manifest_found else "absent"
        explanation = "No loose dependency evidence detected." if manifest_found else "No dependency manifest detected."
        add_finding(target, findings, counters, "C2_dependency_pinning", "loose_dependency_v1",
                    status, "info", Path("."), 0, "", "dependency", explanation)


def _check_unpinned_deps_in_file(
    target: Path,
    path: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> bool:
    found = False
    text = read_text(path)
    for line_number, entry, snippet in manifest_dependency_entries(path, text):
        if not is_unpinned_dependency(entry):
            continue
        found = True
        add_finding(target, findings, counters, "C2_dependency_pinning",
                    "loose_dependency_v1", "detected", "warn", path, line_number,
                    snippet, "dependency", "Unpinned or loosely pinned dependency detected.",
                    {"dependency": entry})
    return found


def credential_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    paths: Iterable[Path],
) -> None:
    detected = False
    placeholders = False
    for path in sorted(set(paths), key=lambda p: relative_path(target, p).as_posix()):
        text = read_text(path)
        lines = text.splitlines()
        for match in SECRET_TERMS.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            placeholder = PLACEHOLDER_SECRET_VALUES.search(match.group(0)) is not None
            fixture_like = is_fixture_like_path(path)
            status = "not_applicable" if placeholder or fixture_like else "detected"
            severity = "info" if status == "not_applicable" else "warn"
            explanation = (
                "Credential-like placeholder or test/example fixture ignored for C1 penalty."
                if status == "not_applicable" else "Hardcoded credential-like pattern detected."
            )
            detected = detected or status == "detected"
            placeholders = placeholders or status == "not_applicable"
            add_finding(
                target,
                findings,
                counters,
                "C1_hardcoded_credentials",
                "credential_pattern_v2",
                status,
                severity,
                path,
                line,
                source_line(lines, line),
                "regex",
                explanation,
                {"match": match.group(0), "placeholder": placeholder, "fixture_context": fixture_like},
            )
    if not detected and not placeholders:
        add_finding(
            target,
            findings,
            counters,
            "C1_hardcoded_credentials",
            "credential_pattern_v2",
            "not_detected",
            "info",
            Path("."),
            0,
            "",
            "regex",
            "No hardcoded credential evidence detected for C1_hardcoded_credentials.",
        )


def fail_open_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    paths: Iterable[Path],
) -> None:
    detected = False
    for path in sorted(set(paths), key=lambda p: relative_path(target, p).as_posix()):
        if path.suffix.lower() != ".py":
            continue
        text = read_text(path)
        if not text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        lines = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler) or not _is_fail_open_handler(node):
                continue
            detected = True
            line = getattr(node, "lineno", 0)
            add_finding(
                target,
                findings,
                counters,
                "C4_exception_handling_clinical_adjacent_paths",
                "fail_open_exception_v2",
                "detected",
                "warn",
                path,
                line,
                source_line(lines, line),
                "ast",
                "Fail-open exception handler detected in executable Python code.",
            )
    if not detected:
        add_finding(
            target,
            findings,
            counters,
            "C4_exception_handling_clinical_adjacent_paths",
            "fail_open_exception_v2",
            "not_detected",
            "info",
            Path("."),
            0,
            "",
            "ast",
            "No fail-open exception handler detected in executable Python code.",
        )


def external_service_dependency_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    surface_paths: Iterable[Path],
    config_paths: Iterable[Path],
) -> None:
    required_env_rows = _required_external_service_rows(target, config_paths)
    provider_lines = _provider_dependency_lines(target, surface_paths)
    local_claim_lines = _local_self_host_claim_lines(target, surface_paths)
    providers = sorted({row["provider"] for row in required_env_rows})
    if required_env_rows and (provider_lines or local_claim_lines):
        for row in required_env_rows:
            add_finding(
                target,
                findings,
                counters,
                "R2R_D5_single_external_service_dependency",
                "single_external_service_dependency_v1",
                "detected",
                "warn",
                row["path"],
                row["line"],
                row["snippet"],
                "config",
                "Required external service API key detected for a named workflow dependency.",
                {"provider": row["provider"], "env_var": row["env_var"], "required_signal": True},
            )
        for row in provider_lines[:3]:
            add_finding(
                target,
                findings,
                counters,
                "R2R_D5_single_external_service_dependency",
                "single_external_service_dependency_v1",
                "detected",
                "warn",
                row["path"],
                row["line"],
                row["snippet"],
                "regex",
                "Named external service provider is presented as part of the core repository workflow.",
                {"provider": row["provider"], "line_role": "provider_dependency_claim"},
            )
        for row in local_claim_lines[:3]:
            add_finding(
                target,
                findings,
                counters,
                "R2R_D5_single_external_service_dependency",
                "single_external_service_dependency_v1",
                "detected",
                "warn",
                row["path"],
                row["line"],
                row["snippet"],
                "regex",
                "Local or self-host claims coexist with required external service dependencies.",
                {
                    "providers": providers,
                    "line_role": "local_or_self_host_claim",
                    "provider_count": len(providers),
                },
            )
        return
    add_finding(
        target,
        findings,
        counters,
        "R2R_D5_single_external_service_dependency",
        "single_external_service_dependency_v1",
        "not_detected",
        "info",
        Path("."),
        0,
        "",
        "aggregate",
        "No named required external service dependency pattern was detected.",
    )


def unsupported_legal_or_compliance_claim_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    paths: Iterable[Path],
) -> None:
    grounding_present = False
    claim_rows: list[dict[str, object]] = []
    for path in sorted(set(paths), key=lambda p: relative_path(target, p).as_posix()):
        lines = read_text(path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            if LEGAL_COMPLIANCE_GROUNDING_TERMS.search(line):
                grounding_present = True
            claim_match = LEGAL_COMPLIANCE_CLAIM_TERMS.search(line)
            if not claim_match:
                continue
            if LEGAL_COMPLIANCE_NEGATION_TERMS.search(line):
                continue
            claim_rows.append(
                {
                    "path": path,
                    "line": line_number,
                    "snippet": line,
                    "claim": claim_match.group(0),
                }
            )
    if claim_rows and not grounding_present:
        for row in claim_rows[:5]:
            add_finding(
                target,
                findings,
                counters,
                "S1_R2_unsupported_legal_or_compliance_claim",
                "unsupported_legal_or_compliance_claim_v1",
                "detected",
                "warn",
                row["path"],
                row["line"],
                row["snippet"],
                "regex",
                "Legal, privacy, or compliance claim detected without supporting governance or security-grounding evidence in reviewed sources.",
                {"claim": row["claim"], "grounding_present": False},
            )
        return
    add_finding(
        target,
        findings,
        counters,
        "S1_R2_unsupported_legal_or_compliance_claim",
        "unsupported_legal_or_compliance_claim_v1",
        "not_detected",
        "info",
        Path("."),
        0,
        "",
        "aggregate",
        "No unsupported legal or compliance claim pattern was detected.",
    )


def mock_auth_or_fail_open_boundary_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    surface_paths: Iterable[Path],
    config_paths: Iterable[Path],
    code_paths: Iterable[Path],
) -> None:
    review_paths = [*surface_paths, *config_paths, *code_paths]
    local_claim_rows = _local_self_host_claim_lines(target, [*surface_paths, *config_paths])
    mock_rows: list[dict[str, object]] = []
    for path in sorted(set(review_paths), key=lambda p: relative_path(target, p).as_posix()):
        lines = read_text(path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            match = MOCK_AUTH_FAIL_OPEN_TERMS.search(line)
            if not match:
                continue
            mock_rows.append(
                {
                    "path": path,
                    "line": line_number,
                    "snippet": line,
                    "match": match.group(0),
                }
            )
    if mock_rows:
        for row in mock_rows[:4]:
            add_finding(
                target,
                findings,
                counters,
                "C6_mock_auth_or_fail_open_boundary",
                "mock_auth_fail_open_boundary_v1",
                "detected",
                "warn",
                row["path"],
                row["line"],
                row["snippet"],
                "regex",
                "Mock-auth, auto-login, or no-auth local/self-host boundary surfaced in reviewed sources.",
                {"match": row["match"], "local_claim_context": bool(local_claim_rows)},
            )
        for row in local_claim_rows[:2]:
            add_finding(
                target,
                findings,
                counters,
                "C6_mock_auth_or_fail_open_boundary",
                "mock_auth_fail_open_boundary_v1",
                "detected",
                "warn",
                row["path"],
                row["line"],
                row["snippet"],
                "regex",
                "Local or self-host claims coexist with mock-auth or auto-login boundary signals.",
                {"line_role": "local_or_self_host_claim"},
            )
        return
    add_finding(
        target,
        findings,
        counters,
        "C6_mock_auth_or_fail_open_boundary",
        "mock_auth_fail_open_boundary_v1",
        "not_detected",
        "info",
        Path("."),
        0,
        "",
        "aggregate",
        "No mock-auth or fail-open local-boundary pattern was detected.",
    )


def _required_external_service_rows(target: Path, config_paths: Iterable[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(set(config_paths), key=lambda p: relative_path(target, p).as_posix()):
        section_required = False
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                if _OPTIONAL_HINT.search(stripped):
                    section_required = False
                elif _REQUIRED_HINT.search(stripped):
                    section_required = True
                continue
            match = _API_KEY_ASSIGNMENT.match(stripped)
            if not match:
                continue
            env_var = match.group(1)
            provider = _EXTERNAL_PROVIDER_ENV_MAP.get(env_var)
            if not provider or not section_required:
                continue
            rows.append(
                {
                    "path": path,
                    "line": line_number,
                    "snippet": line,
                    "env_var": env_var,
                    "provider": provider,
                }
            )
    return rows


def _provider_dependency_lines(target: Path, surface_paths: Iterable[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(set(surface_paths), key=lambda p: relative_path(target, p).as_posix()):
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            if not _PROVIDER_LINE_HINT.search(line) and "API" not in line and "api" not in line:
                continue
            provider = _provider_name_from_text(line)
            if not provider:
                continue
            rows.append({"path": path, "line": line_number, "snippet": line, "provider": provider})
    return rows


def _local_self_host_claim_lines(target: Path, surface_paths: Iterable[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(set(surface_paths), key=lambda p: relative_path(target, p).as_posix()):
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            if not LOCAL_SELF_HOST_CLAIM_TERMS.search(line):
                continue
            rows.append({"path": path, "line": line_number, "snippet": line})
    return rows


def _provider_name_from_text(text: str) -> str | None:
    lowered = text.lower()
    for env_var, provider in _EXTERNAL_PROVIDER_ENV_MAP.items():
        stem = env_var.replace("_API_KEY", "").replace("NEXT_PUBLIC_", "").replace("_SERVICE_ROLE_KEY", "").replace("_ANON_KEY", "")
        provider_token = provider.lower()
        if provider_token in lowered or stem.lower().replace("_", " ") in lowered or stem.lower() in lowered:
            return provider
    return None


def _is_fail_open_handler(node: ast.ExceptHandler) -> bool:
    if not node.body:
        return False
    for child in node.body:
        if isinstance(child, ast.Pass):
            return True
        if isinstance(child, ast.Return) and isinstance(child.value, ast.Constant) and child.value.value is True:
            return True
    return False


def file_presence_detector(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
    detector: str,
    pattern_id: str,
    paths: Iterable[Path],
    explanation: str,
) -> None:
    sorted_paths = sorted(set(paths), key=lambda p: relative_path(target, p).as_posix())
    if not sorted_paths:
        add_finding(target, findings, counters, detector, pattern_id, "not_detected", "info", Path("."), 0, "", "file_presence", f"No evidence detected for {detector}.")
        return
    for path in sorted_paths:
        add_finding(target, findings, counters, detector, pattern_id, "detected", "info", path, 0, relative_path(target, path).as_posix(), "file_presence", explanation)
