from __future__ import annotations

from pathlib import Path

from stem_ai.scanner import audit_repository


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_loose_dependency_ranges_warn(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    _write(tmp_path / "requirements.txt", "gradio>=4.44.0\nreportlab>=4.0\n")

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C2_dependency_pinning"]["status"] == "WARN"


def test_exact_dependency_pins_pass(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    _write(tmp_path / "requirements.txt", "gradio==4.44.1\nreportlab==4.2.5\n")

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C2_dependency_pinning"]["status"] == "PASS"


def test_direct_clinical_claim_triggers_t0_floor(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Automated diagnostic decision support for patient treatment recommendation.\n",
    )
    _write(tmp_path / "requirements.txt", "numpy==1.26.4\n")

    result = audit_repository(tmp_path)

    assert result["classification"]["ca_severity"] == "CA-DIRECT"
    assert result["classification"]["t0_hard_floor"] is True
    assert result["score"]["final_score"] <= 39
    assert result["score"]["formal_tier"].startswith("T0")


def test_stage_3_full_rubric_can_reach_100(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bioinformatics repository for viral genome analysis.\n"
        "Limitations and population validation boundaries are documented.\n"
        "Funding and competing interest disclosures are provided.\n",
    )
    _write(tmp_path / "requirements.txt", "numpy==1.26.4\n")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: test\n")
    _write(tmp_path / "tests" / "test_domain.py", "def test_viral_genome_variant_pipeline(): pass\n")
    _write(tmp_path / "CHANGELOG.md", "# Changelog\n")

    result = audit_repository(tmp_path)

    assert result["score"]["stage_3_code_bio"] == 100
    assert result["stage_3_rubric"]["stage_3_raw_total"]["score"] == 80
    assert result["stage_3_rubric"]["B1_data_provenance_controls"]["max"] == 15


def test_deprecated_patient_paths_are_generic_not_repo_specific(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    _write(tmp_path / "legacy" / "metadata.py", "sample_id = 'S1'\npatient_age = 42\n")

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C3_dead_or_deprecated_patient_adjacent_paths"]["status"] == "WARN"


def test_fail_open_detection_handles_crlf(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    code_path = tmp_path / "pipeline.py"
    code_path.write_bytes(b"def validate():\r\n    try:\r\n        return False\r\n    except Exception:\r\n        pass\r\n")

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C4_exception_handling_clinical_adjacent_paths"]["status"] == "WARN"
