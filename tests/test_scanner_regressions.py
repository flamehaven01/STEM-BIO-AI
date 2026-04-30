from __future__ import annotations

from pathlib import Path

import stem_ai.detectors as detectors
from stem_ai.evidence import make_finding_id
from stem_ai.render import _explain_status_label, render_explain, render_markdown
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
        "Limitations and validation boundaries are documented.\n"
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


def test_evidence_ledger_and_ast_summary_are_observation_only(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "requirements.txt", "numpy==1.26.4\n")
    _write(
        tmp_path / "tests" / "test_domain.py",
        "import random\n\n"
        "def test_variant_pipeline():\n"
        "    random.seed(1)\n"
        "    assert True\n",
    )

    result = audit_repository(tmp_path)

    assert result["schema_version"] == "stem-ai-local-cli-result-v1.3"
    assert result["score"]["stage_1_readme_intent"] == 70
    assert "evidence_ledger" in result
    assert "detector_summary" in result
    assert "ast_signal_summary" in result
    assert result["ast_signal_summary"]["test_functions"] == 1
    assert result["ast_signal_summary"]["assertion_tests"] == 1
    assert result["ast_signal_summary"]["seed_settings"] == 1
    assert any(
        finding["detector"] == "AST_assertion_tests"
        and finding["file"] == "tests/test_domain.py"
        and "\\" not in finding["finding_id"]
        for finding in result["evidence_ledger"]
    )


def test_finding_id_uses_posix_paths_and_per_file_occurrence_index() -> None:
    finding_id = make_finding_id("B2_bias_limitations", "docs\\guide.md", 12, 2)

    assert finding_id == "B2_bias_limitations:docs/guide.md:12:002"


def test_evidence_ledger_covers_scored_stage3_and_c1_c4_components(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "requirements.txt", "numpy>=1.26\n")
    _write(tmp_path / "CHANGELOG.md", "# Changelog\n")
    _write(tmp_path / "tests" / "test_domain.py", "def test_viral_genome_variant_pipeline():\n    assert True\n")
    _write(tmp_path / "legacy" / "metadata.py", "patient_age = 42\n")
    secret = "sk-" + "abcdefghijklmnopqrstuv"
    _write(
        tmp_path / "pipeline.py",
        f"TOKEN = '{secret}'\n"
        "def validate():\n"
        "    try:\n"
        "        return False\n"
        "    except Exception:\n"
        "        pass\n",
    )

    result = audit_repository(tmp_path)
    detectors_seen = {finding["detector"] for finding in result["evidence_ledger"]}

    assert "S3_T2_domain_tests" in detectors_seen
    assert "S3_T3_changelog_release_hygiene" in detectors_seen
    assert "C1_hardcoded_credentials" in detectors_seen
    assert "C2_dependency_pinning" in detectors_seen
    assert "C3_dead_or_deprecated_patient_adjacent_paths" in detectors_seen
    assert "C4_exception_handling_clinical_adjacent_paths" in detectors_seen


def test_ast_syntax_error_is_recorded_without_abort(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "good.py", "def ok():\n    return True\n")
    _write(tmp_path / "bad.py", "def broken(:\n    pass\n")

    result = audit_repository(tmp_path)

    assert result["ast_signal_summary"]["files_parsed"] == 1
    assert result["ast_signal_summary"]["syntax_errors"] == 1
    assert any(f["detector"] == "AST_syntax_error" and f["status"] == "error" for f in result["evidence_ledger"])


def test_ast_file_limit_records_not_applicable(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(detectors, "MAX_AST_FILES", 1)
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "a.py", "def a():\n    return 1\n")
    _write(tmp_path / "b.py", "def b():\n    return 2\n")

    result = audit_repository(tmp_path)

    assert result["ast_signal_summary"]["file_limit_exceeded"] is True
    assert any(
        f["detector"] == "AST_file_limit"
        and f["status"] == "not_applicable"
        and f.get("metadata", {}).get("reason") == "file_limit_exceeded"
        for f in result["evidence_ledger"]
    )


def test_ast_detects_seed_variants_and_direct_argument_parser(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(
        tmp_path / "cli.py",
        "from argparse import ArgumentParser\n"
        "import numpy as np\n"
        "import torch\n"
        "def main():\n"
        "    np.random.seed(1)\n"
        "    torch.manual_seed(2)\n"
        "    return ArgumentParser()\n",
    )

    result = audit_repository(tmp_path)

    assert result["ast_signal_summary"]["seed_settings"] == 2
    assert result["ast_signal_summary"]["argparse_cli"] is True


def test_ast_distinguishes_assertion_tests(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(
        tmp_path / "tests" / "test_assertions.py",
        "def test_without_assertion():\n"
        "    value = 1\n\n"
        "def test_with_assertion():\n"
        "    assert True\n",
    )

    result = audit_repository(tmp_path)

    assert result["ast_signal_summary"]["test_functions"] == 2
    assert result["ast_signal_summary"]["assertion_tests"] == 1


def test_ast_async_function_docstring_and_annotations_count(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(
        tmp_path / "async_module.py",
        "async def load_sample(sample_id: str) -> str:\n"
        "    \"\"\"Load a sample.\"\"\"\n"
        "    return sample_id\n",
    )

    result = audit_repository(tmp_path)

    assert result["ast_signal_summary"]["public_functions"] == 1
    assert result["ast_signal_summary"]["docstring_functions"] == 1
    assert result["ast_signal_summary"]["annotated_functions"] == 1


def test_stage4_replication_evidence_reaches_r4_without_final_score_weight(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bioinformatics repository for viral genome analysis.\n"
        "## Reproduce Results\n"
        "Dataset: https://zenodo.org/records/12345\n"
        "Model checkpoint: https://huggingface.co/example/model/resolve/main/model.safetensors\n",
    )
    _write(tmp_path / "Dockerfile", "FROM python:3.12\n")
    _write(tmp_path / "Makefile", "reproduce:\n\tpython -m stem_ai\n")
    _write(tmp_path / "requirements.txt", "numpy==1.26.4\n--hash=sha256:abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd\n")
    _write(tmp_path / "weights.sha256", "abcdef  weights.bin\n")
    _write(tmp_path / "CITATION.cff", "title: STEM BIO-AI\n")
    _write(tmp_path / "pyproject.toml", "[project.scripts]\nstem-demo = \"demo:main\"\n")
    _write(tmp_path / "examples" / "run_demo.py", "print('demo')\n")
    _write(tmp_path / "train.py", "import random\n\ndef main():\n    random.seed(1)\n")

    result = audit_repository(tmp_path)
    stage4_detectors = {finding["detector"] for finding in result["evidence_ledger"] if finding["detector"].startswith("S4_")}

    assert result["replication_score"] == 100
    assert result["replication_tier"] == "R4"
    assert result["stage_4_rubric"]["stage_4_raw_total"]["score"] == 100
    assert "stage_4_replication" not in result["score"]
    assert {
        "S4_container_environment",
        "S4_make_reproduce_target",
        "S4_environment_lock_evidence",
        "S4_exact_dependency_pins_or_hashes",
        "S4_readme_reproducibility_section",
        "S4_checksum_files",
        "S4_dataset_url",
        "S4_model_weight_url_or_checksum",
        "S4_citation_cff",
        "S4_cli_entrypoint",
        "S4_seed_setting",
        "S4_runnable_examples",
    }.issubset(stage4_detectors)


def test_stage4_no_replication_surface_is_r0_and_markdown_reports_lane(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, mode="detailed", pages=3)

    assert result["replication_score"] == 0
    assert result["replication_tier"] == "R0"
    assert "Stage 4 Replication Score" in markdown
    assert "Stage 4 Replication Evidence" in markdown


def test_explain_report_covers_detectors_and_stage4_rubric(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "requirements.txt", "numpy>=1.26\n")
    _write(tmp_path / "tests" / "test_domain.py", "def test_viral_genome_variant_pipeline():\n    assert True\n")

    result = audit_repository(tmp_path)
    explain = render_explain(result)

    assert "STEM BIO-AI Explain Report" in explain
    assert "C2_dependency_pinning" in explain
    assert "S3_T2_domain_tests" in explain
    assert "Stage 4 Replication Rubric" in explain
    assert "AST Signal Summary" in explain
    assert "DISCLAIMER" in explain
    assert "finding_id: C2_dependency_pinning:requirements.txt" in explain
    assert "\\" not in explain


def test_explain_file_written_when_flag_set(tmp_path: Path) -> None:
    from stem_ai.render import write_outputs

    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    result = audit_repository(tmp_path)
    out_dir = tmp_path / "out"
    created = write_outputs(result, out_dir, mode="brief", pages=1, fmt="json", explain=True)
    explain_files = [p for p in created if p.suffix == ".txt"]

    assert len(explain_files) == 1
    content = explain_files[0].read_text(encoding="utf-8")
    assert "STEM BIO-AI Explain Report" in content


def test_explain_report_no_backslash_in_finding_ids(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "legacy" / "metadata.py", "patient_age = 42\n")

    result = audit_repository(tmp_path)
    explain = render_explain(result)

    for line in explain.splitlines():
        if "finding_id" in line or "[001]" in line or "[002]" in line:
            assert "\\" not in line, f"Backslash in explain line: {line!r}"


def test_explain_status_label_prioritizes_errors() -> None:
    assert _explain_status_label({"detected", "error"}) == "ERROR"
    assert _explain_status_label({"not_detected", "detected"}) == "DETECTED"
