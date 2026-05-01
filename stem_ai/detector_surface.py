from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from .evidence import EvidenceFinding
from .detector_utils import (
    add_finding,
    dependency_entries,
    existing_named_files,
    is_unpinned_dependency,
    iter_code_files,
    iter_deprecated_files,
    iter_text_files,
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
    FAIL_OPEN,
    HYPE_AUTONOMOUS_REPLACEMENT,
    HYPE_BREAKTHROUGH,
    HYPE_CLINICAL_CERTAINTY,
    HYPE_PERFECT_ACCURACY,
    HYPE_REGULATORY_APPROVAL,
    HYPE_UNIVERSAL_GENERALIZATION,
    LIMITATIONS_SECTION,
    PATIENT_METADATA,
    PLACEHOLDER_SECRET_VALUES,
    REGULATORY_FRAMEWORK_TERMS,
    REPRODUCIBILITY_TERMS,
    SECRET_TERMS,
)


def collect_surface_findings(
    target: Path,
    findings: list[EvidenceFinding],
    counters: dict[tuple[str, str], int],
) -> None:
    readme_paths = existing_named_files(target, ["README.md", "README.rst", "readme.md"])
    docs_paths = list(iter_text_files(target / "docs", max_files=30))
    package_paths = existing_named_files(target, ["pyproject.toml", "setup.py", "setup.cfg", "package.json"])
    funding_paths = existing_named_files(target, ["FUNDING.md", "CITATION.cff", "AUTHORS.md"])
    workflow_paths = list(iter_text_files(target / ".github" / "workflows", max_files=20))
    test_paths = list(iter_text_files(target / "tests", max_files=40))
    dep_paths = existing_named_files(target, ["environment.yml", "requirements.txt", "pyproject.toml", "setup.cfg"])
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
    regex_detector(target, findings, counters, "S1_R4_demographic_bias_boundary", "demographic_bias_boundary_v1", DEMOGRAPHIC_BIAS_TERMS, [*readme_paths, *docs_paths], "Demographic, subgroup, fairness, bias, or validation-cohort language detected.")
    regex_detector(target, findings, counters, "S1_R5_reproducibility_provisions", "reproducibility_provisions_v1", REPRODUCIBILITY_TERMS, [*readme_paths, *docs_paths], "Reproducibility, replication, seed, lockfile, or checksum language detected.")
    file_presence_detector(target, findings, counters, "S3_T1_workflow_files", "workflow_presence_v1", workflow_paths, "Workflow file exists.")
    regex_line_detector(target, findings, counters, "S3_T2_domain_tests", "domain_tests_bio_terms_v1", BIO_TERMS, test_paths, "Domain-specific test text detected.", normalize_underscores=True)
    file_presence_detector(target, findings, counters, "S3_T3_changelog_release_hygiene", "changelog_presence_v1", changelog_paths, "Changelog or release-history file exists.")
    regex_detector(target, findings, counters, "S3_T3_changelog_bugfix_evidence", "changelog_bugfix_terms_v1", CHANGELOG_BUG_TERMS, changelog_paths, "Bug-fix, patch, or security entry detected in changelog.")
    file_presence_detector(target, findings, counters, "S3_B1_dependency_manifest", "dependency_manifest_presence_v1", dep_paths, "Dependency or environment manifest exists.")
    regex_detector(target, findings, counters, "S3_B1_data_source_language", "data_source_terms_v1", DATA_SOURCE_TERMS, [*readme_paths, *docs_paths], "Data source, dataset citation, IRB, or provenance language detected.")
    regex_detector(target, findings, counters, "S3_B2_bias_limitations", "bias_limitations_v2", BIAS_LIMITATION_TERMS, [*readme_paths, *docs_paths], "Bias, limitation, or validation-boundary language detected.")
    regex_detector(target, findings, counters, "S3_B2_measurement_evidence", "bias_measurement_terms_v1", BIAS_MEASUREMENT_TERMS, [*readme_paths, *docs_paths, *test_paths], "Quantitative bias/limitation measurement or related test evidence detected.")
    regex_detector(target, findings, counters, "S3_B3_coi_funding", "coi_funding_v1", COI_FUNDING_TERMS, [*readme_paths, *docs_paths, *funding_paths], "COI, funding, sponsor, or acknowledgement language detected.")
    regex_detector(target, findings, counters, "S2_package_bio_terms", "package_bio_terms_v1", BIO_TERMS, package_paths, "Package metadata exposes bio/medical vocabulary.")
    credential_detector(target, findings, counters, code_paths)
    dependency_pinning_detector(target, findings, counters, dep_paths)
    regex_detector(target, findings, counters, "C3_dead_or_deprecated_patient_adjacent_paths", "deprecated_patient_metadata_v1", PATIENT_METADATA, deprecated_paths, "Patient-adjacent metadata pattern detected in deprecated/legacy/archive path.")
    regex_detector(target, findings, counters, "C4_exception_handling_clinical_adjacent_paths", "fail_open_exception_v1", FAIL_OPEN, code_paths, "Fail-open exception pattern detected in code text.")


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
    for line_number, line in enumerate(read_text(path).splitlines(), start=1):
        for entry in dependency_entries(line):
            if not is_unpinned_dependency(entry):
                continue
            found = True
            add_finding(target, findings, counters, "C2_dependency_pinning",
                        "loose_dependency_v1", "detected", "warn", path, line_number,
                        line, "dependency", "Unpinned or loosely pinned dependency detected.",
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
            status = "not_applicable" if PLACEHOLDER_SECRET_VALUES.search(match.group(0)) else "detected"
            severity = "info" if status == "not_applicable" else "warn"
            explanation = (
                "Credential-like placeholder in test/example context ignored for C1 penalty."
                if status == "not_applicable"
                else "Hardcoded credential-like pattern detected."
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
                {"match": match.group(0), "placeholder": status == "not_applicable"},
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
