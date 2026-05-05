from __future__ import annotations

from pathlib import Path
import json

import stem_ai.detectors as detectors
from stem_ai.advisory_contract import (
    advisory_contract_schemas,
    build_advisory_input,
    build_provider_advisory_input,
    known_finding_ids,
    validate_advisory_input_packet,
    validate_advisory_output,
)
from stem_ai.advisory_providers import (
    load_provider_config,
    provider_handoff_metadata,
    provider_request_schema,
    provider_registry,
    validate_provider_request_args,
)
from stem_ai.cli import main as cli_main
from stem_ai.evidence import make_finding_id
from stem_ai.provider_benchmark import (
    PROVIDER_BENCHMARK_SCHEMA_VERSION,
    packet_stats_record,
    packet_summary,
    response_validation_record,
)
from stem_ai.reasoning_model import (
    benchmark_alignment,
    lane_coherence,
    unique_token_count,
)
from stem_ai.render import _explain_status_label, render_explain, render_markdown
from stem_ai.scanner import _score_bias, _score_changelog, _score_provenance, _score_stage_2r, audit_repository


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


def test_framework_meta_documentation_does_not_trigger_ca_floor(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "# Triage Tiers\n"
        "A T4 score means strong observable evidence signals. It does not mean the repository is safe for clinical deployment -- that requires independent expert validation.\n"
        "| Stage 1 hype penalties (H1-H6) | Regex: clinical certainty, regulatory approval, breakthrough marketing, perfect accuracy claims |\n"
        "| CA severity | Clinical/diagnostic phrase regex in README, docs, and package metadata |\n",
    )
    _write(
        tmp_path / "docs" / "API_CONTRACT.md",
        "| `reasoning_model` | object | Diagnostic layer (observation-only, does not affect score) |\n",
    )

    result = audit_repository(tmp_path)

    assert result["classification"]["ca_severity"] == "none"
    assert result["classification"]["t0_hard_floor"] is False
    assert result["classification"]["score_cap"] is None
    assert "H1_clinical_certainty_hype" not in result["stage_1_rubric"]
    assert "H4_breakthrough_marketing_hype" not in result["stage_1_rubric"]
    assert "H6_perfect_accuracy_hype" not in result["stage_1_rubric"]


def test_expanded_clinical_boundary_phrases_count_as_disclaimer(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio clinical decision support research package. This is not a medical device and does not provide clinical diagnoses.\n",
    )

    result = audit_repository(tmp_path)

    assert result["classification"]["ca_severity"] == "CA-DIRECT"
    assert result["classification"]["has_explicit_clinical_boundary"] is True
    assert result["classification"]["t0_hard_floor"] is False
    assert result["classification"]["score_cap"] is None


def test_stage_3_full_rubric_can_reach_100(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bioinformatics repository for viral genome analysis.\n"
        "Limitations and validation boundaries are documented.\n"
        "Subgroup analysis shows performance gap across demographic groups.\n"
        "Data availability: dataset deposited on Zenodo. IRB approved.\n"
        "Funding and competing interest disclosures are provided.\n",
    )
    _write(tmp_path / "requirements.txt", "numpy==1.26.4\n")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: test\n")
    _write(tmp_path / "tests" / "test_domain.py", "def test_viral_genome_variant_pipeline(): pass\n")
    _write(tmp_path / "CHANGELOG.md", "# Changelog\n\n## v1.0.1\n- Fixed bug in variant calling pipeline.\n")

    result = audit_repository(tmp_path)

    assert result["score"]["stage_3_code_bio"] == 100
    assert result["stage_3_rubric"]["stage_3_raw_total"]["score"] == 80
    assert result["stage_3_rubric"]["B1_data_provenance_controls"]["max"] == 15


def test_deprecated_patient_paths_are_generic_not_repo_specific(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    _write(tmp_path / "legacy" / "metadata.py", "sample_id = 'S1'\npatient_age = 42\n")

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C3_dead_or_deprecated_patient_adjacent_paths"]["status"] == "WARN"


def test_skill_catalog_clinical_terms_trigger_ca_indirect_cap(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Scientific skills catalog.\n"
        "Includes AutoDock Vina drug docking, nnU-Net medical imaging, pydicom, "
        "biomarker survival analysis, and clinical trial examples.\n",
    )

    result = audit_repository(tmp_path)

    assert result["classification"]["ca_severity"] == "CA-INDIRECT"
    assert result["classification"]["clinical_adjacent"] is True
    assert result["classification"]["score_cap"] == 69
    assert result["score"]["stage_1_readme_intent"] == 60


def test_placeholder_credentials_in_tests_do_not_trigger_c1_penalty(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(
        tmp_path / "tests" / "test_provider.py",
        "def test_provider():\n"
        "    provider = Client(api_key=\"super-secret-key\")\n",
    )

    result = audit_repository(tmp_path)
    c1_findings = [f for f in result["evidence_ledger"] if f["detector"] == "C1_hardcoded_credentials"]

    assert result["code_integrity"]["C1_hardcoded_credentials"]["status"] == "PASS"
    assert result["score"]["risk_penalty"] == 0
    assert any(f["status"] == "not_applicable" and f.get("metadata", {}).get("placeholder") is True for f in c1_findings)


def test_real_credential_like_values_still_trigger_c1_penalty(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(
        tmp_path / "pipeline.py",
        "TOKEN = 'sk-" + "abcdefghijklmnopqrstuv" + "'\n",
    )

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C1_hardcoded_credentials"]["status"] == "FAIL"
    assert result["score"]["risk_penalty"] == 10


def test_realistic_sk_fixture_in_test_path_does_not_trigger_c1_penalty(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(
        tmp_path / "tests" / "test_severity.py",
        "def test_hardcoded_api_key():\n"
        "    code = '''\\napi_key = \\\"sk-1234567890abcdef\\\"\\n'''\n",
    )

    result = audit_repository(tmp_path)
    c1_findings = [f for f in result["evidence_ledger"] if f["detector"] == "C1_hardcoded_credentials"]

    assert result["code_integrity"]["C1_hardcoded_credentials"]["status"] == "PASS"
    assert result["score"]["risk_penalty"] == 0
    assert any(f["status"] == "not_applicable" and f.get("metadata", {}).get("fixture_context") is True for f in c1_findings)


def test_fail_open_detection_handles_crlf(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    code_path = tmp_path / "pipeline.py"
    code_path.write_bytes(b"def validate():\r\n    try:\r\n        return False\r\n    except Exception:\r\n        pass\r\n")

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C4_exception_handling_clinical_adjacent_paths"]["status"] == "WARN"


def test_fail_open_string_literal_in_runtime_code_does_not_trigger_c4(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    _write(
        tmp_path / "patcher.py",
        "def replacement(snippet: str) -> str:\n"
        "    if 'except: pass' in snippet.lower():\n"
        "        return 'raise'\n"
        "    return snippet\n",
    )

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C4_exception_handling_clinical_adjacent_paths"]["status"] == "PASS"


def test_pyproject_metadata_lines_do_not_trigger_c2_without_dependency_section(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    _write(
        tmp_path / "pyproject.toml",
        "[project]\n"
        "name = \"sample-project\"\n"
        "version = \"0.1.0\"\n"
        "readme = \"README.md\"\n"
        "requires-python = \">=3.11\"\n"
        "keywords = [\"bio\", \"analysis\"]\n",
    )

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C2_dependency_pinning"]["status"] == "PASS"


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

    assert result["schema_version"] == "stem-ai-local-cli-result-v1.4"
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


def test_stage1_hype_penalties_reduce_readme_evidence_score(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio medical platform with clinically proven diagnostic grade results.\n"
        "FDA approved autonomous clinical decision support for any patient.\n"
        "Revolutionary model with 100% accurate predictions.\n",
    )

    result = audit_repository(tmp_path)
    rubric = result["stage_1_rubric"]
    detectors_seen = {finding["detector"] for finding in result["evidence_ledger"]}

    assert result["score"]["stage_1_readme_intent"] == 0
    assert rubric["H1_clinical_certainty_hype"]["score"] == -10
    assert rubric["H2_regulatory_approval_hype"]["score"] == -10
    assert rubric["H3_autonomous_replacement_hype"]["score"] == -10
    assert rubric["H4_breakthrough_marketing_hype"]["score"] == -5
    assert rubric["H5_universal_generalization_hype"]["score"] == -5
    assert rubric["H6_perfect_accuracy_hype"]["score"] == -10
    assert rubric["R2_regulatory_framework"]["score"] == -10
    assert rubric["R3_clinical_disclaimer"]["score"] == -10
    assert "S1_H1_clinical_certainty_hype" in detectors_seen
    assert "S1_H6_perfect_accuracy_hype" in detectors_seen


def test_stage1_responsibility_signals_can_reach_cap(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio medical repository for viral genome analysis.\n\n"
        "## Limitations\n"
        "Known limitations and validation boundaries are documented by subgroup.\n"
        "Research use only, not for clinical use.\n"
        "Regulatory framework references SaMD, IRB, and TRIPOD-AI.\n"
        "Reproducibility provisions include deterministic random seed and environment.yml.\n",
    )

    result = audit_repository(tmp_path)
    rubric = result["stage_1_rubric"]
    detectors_seen = {finding["detector"] for finding in result["evidence_ledger"]}

    assert result["score"]["stage_1_readme_intent"] == 100
    assert rubric["R1_limitations_section"]["score"] == 15
    assert rubric["R2_regulatory_framework"]["score"] == 15
    assert rubric["R3_clinical_disclaimer"]["score"] == 10
    assert rubric["R4_demographic_bias_boundary"]["score"] == 10
    assert rubric["R5_reproducibility_provisions"]["score"] == 10
    assert "S1_R1_limitations_section" in detectors_seen
    assert "S1_R5_reproducibility_provisions" in detectors_seen


def test_finding_id_uses_posix_paths_and_per_file_occurrence_index() -> None:
    finding_id = make_finding_id("B2_bias_limitations", "docs\\guide.md", 12, 2)

    assert finding_id == "B2_bias_limitations:docs/guide.md:12:002"


def test_evidence_ledger_covers_scored_stage3_and_c1_c4_components(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio repository for molecular analysis.\n"
        "Data availability: dataset deposited on Zenodo with IRB approval.\n"
        "Limitations include subgroup analysis and calibration curve review.\n",
    )
    _write(tmp_path / "requirements.txt", "numpy>=1.26\n")
    _write(tmp_path / "CHANGELOG.md", "# Changelog\n\n## 1.0.1\n- Fixed bug in calibration pipeline.\n")
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
    assert "S3_T3_changelog_bugfix_evidence" in detectors_seen
    assert "S3_B1_data_source_language" in detectors_seen
    assert "S3_B2_measurement_evidence" in detectors_seen
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


def test_reasoning_model_is_diagnostic_only_and_does_not_change_score(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral genome analysis.\n")
    _write(tmp_path / "requirements.txt", "numpy==1.26.4\n")

    result = audit_repository(tmp_path)
    reasoning = result["reasoning_model"]

    assert reasoning["version"] == "stem-bio-ai-reasoning-v1.3.2"
    assert reasoning["policy"]["mode"] == "diagnostic_only"
    assert reasoning["policy"]["final_score_override"] is False
    assert "reasoning_score" not in result["score"]
    assert result["score"]["final_score"] == round(
        result["score"]["stage_1_readme_intent"] * 0.4
        + result["score"]["stage_2_repo_local_consistency"] * 0.2
        + result["score"]["stage_3_code_bio"] * 0.4
        - result["score"]["risk_penalty"]
    )


def test_reasoning_surfaces_in_markdown_and_explain(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, mode="detailed", pages=3)
    explain = render_explain(result)

    assert "Reasoning Diagnostics" in markdown
    assert "does not override the final score" in markdown
    assert "Reasoning Diagnostics" in explain
    assert "stem-bio-ai-reasoning-v1.3.2" in explain


def test_reasoning_unique_token_count_is_deterministic() -> None:
    text = "Limitations and limitations are documented."

    assert unique_token_count(text) == 4


def test_reasoning_lane_coherence_excludes_null_stage4() -> None:
    result = lane_coherence({
        "stage_1_readme_evidence": 80,
        "stage_3_code_bio": 60,
        "stage_4_replication": None,
    })

    assert len(result["pairs"]) == 1
    assert result["pairs"][0]["pair"] == "stage_1_readme_evidence:stage_3_code_bio"
    assert result["overall"] == 0.8


def test_reasoning_benchmark_alignment_counts_major_disagreements() -> None:
    result = benchmark_alignment([0, 1, 2, 4], [0, 0, 3, 1])

    assert result["count"] == 4
    assert result["exact_tier_agreement"] == 1
    assert result["within_one_tier_agreement"] == 3
    assert result["major_disagreement_count"] == 1


def test_ai_advisory_is_omitted_by_default(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path)

    assert "ai_advisory" not in result


def test_ai_advisory_validate_adds_offline_contract(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "requirements.txt", "numpy>=1.26\n")

    result = audit_repository(tmp_path, advisory="validate")
    advisory = result["ai_advisory"]

    assert advisory["schema_version"] == "stem-ai-advisory-v1.4"
    assert advisory["provider"] == "none"
    assert advisory["status"] == "valid"
    assert advisory["policy"]["final_score_override"] is False
    assert advisory["reviewer_notes"]
    assert all(set(note["cites"]).issubset(known_finding_ids(result)) for note in advisory["reviewer_notes"])


def test_advisory_input_omits_raw_repo_snippets_by_default(tmp_path: Path) -> None:
    sentinel = "RAW_SENTINEL_SHOULD_NOT_REACH_ADVISORY_INPUT"
    _write(tmp_path / "README.md", f"Bio repository for molecular analysis. {sentinel}\n")

    result = audit_repository(tmp_path)
    packet = build_advisory_input(result)
    serialized = json.dumps(packet)

    assert packet["policy"]["raw_repo_text_allowed"] is False
    assert "snippet" not in serialized
    assert sentinel not in serialized
    assert packet["evidence_ledger"]
    assert packet["allowed_finding_ids"] == [f["finding_id"] for f in packet["evidence_ledger"]]
    assert packet["provider_prompt_contract"]["citation_rule"].startswith("Each cites entry")


def test_advisory_validation_rejects_unknown_citation_and_missing_cites(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    result = audit_repository(tmp_path)

    advisory = validate_advisory_output(result, {
        "reviewer_notes": [
            {
                "claim": "Inspect this repository.",
                "severity": "warn",
                "cites": ["NO_SUCH_FINDING:README.md:1:001"],
                "recommended_action": "Review cited evidence.",
            }
        ],
        "inspection_priorities": [
            {"priority": "high", "reason": "Needs inspection.", "cites": []}
        ],
    })

    assert advisory["status"] == "invalid"
    assert advisory["invalid_citations"] == ["NO_SUCH_FINDING:README.md:1:001"]
    assert "inspection_priorities[0]" in advisory["missing_citation_items"]


def test_advisory_validation_rejects_score_override_and_clinical_claim(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    result = audit_repository(tmp_path)
    cite = next(iter(known_finding_ids(result)))

    advisory = validate_advisory_output(result, {
        "final_score": 100,
        "reviewer_notes": [
            {
                "claim": "This repository is safe for clinical deployment.",
                "severity": "info",
                "cites": [cite],
                "recommended_action": "Use it clinically.",
            }
        ],
        "inspection_priorities": [],
    })

    assert advisory["status"] == "invalid"
    assert "final_score_override_requested" in advisory["errors"]
    assert "prohibited_clinical_or_regulatory_claims" in advisory["errors"]


def test_cli_advisory_validate_writes_ai_advisory_json(tmp_path: Path) -> None:
    _write(tmp_path / "repo" / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "out"

    code = cli_main(["audit", str(tmp_path / "repo"), "--format", "json", "--out", str(out_dir), "--advisory", "validate"])

    assert code == 0
    [json_path] = list(out_dir.glob("*_experiment_results.json"))
    result = json.loads(json_path.read_text(encoding="utf-8"))
    assert result["ai_advisory"]["status"] == "valid"


def test_advisory_surfaces_in_markdown_and_explain(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    result = audit_repository(tmp_path, advisory="validate")

    markdown = render_markdown(result, mode="detailed", pages=3)
    explain = render_explain(result)

    assert "AI Advisory Contract" in markdown
    assert "AI Advisory Contract" in explain
    assert "final_score_override            False" in explain


def test_advisory_contract_schemas_export_stable_required_fields() -> None:
    schemas = advisory_contract_schemas()

    assert schemas["schema_version"] == "stem-ai-advisory-contracts-v1.4"
    assert schemas["advisory_input"]["properties"]["schema_version"]["const"] == "stem-ai-advisory-input-v1.4"
    assert "evidence_ledger" in schemas["advisory_input"]["required"]
    assert schemas["advisory_output"]["properties"]["status"]["enum"] == ["valid", "invalid", "error"]


def test_provider_config_is_secret_free_and_broad() -> None:
    config = load_provider_config({
        "STEM_AI_ADVISORY_PROVIDER": "openai_compatible",
        "STEM_AI_ADVISORY_MODEL": "qwen-local",
        "STEM_AI_ADVISORY_BASE_URL": "http://localhost:8000/v1",
        "STEM_AI_ADVISORY_API_KEY": "secret-value",
        "STEM_AI_ADVISORY_TIMEOUT_SEC": "30",
        "STEM_AI_ADVISORY_MAX_TOKENS": "4096",
    })
    handoff = provider_handoff_metadata(config)
    providers = {item["provider"] for item in provider_registry()}

    assert {"openai", "anthropic", "gemini", "openai_compatible", "ollama", "local_runtime"}.issubset(providers)
    assert handoff["provider"] == "openai_compatible"
    assert handoff["api_key_present"] is True
    assert "secret-value" not in json.dumps(handoff)
    assert handoff["status"] == "adapter_not_implemented"
    assert handoff["request_schema"]["schema_version"] == "stem-ai-provider-request-v1.4"
    assert handoff["args_validation"]["status"] == "valid"


def test_provider_request_validator_reports_structured_arg_errors() -> None:
    schema = provider_request_schema()
    validation = validate_provider_request_args({
        "provider": "bad-provider",
        "timeout_sec": 0,
        "max_tokens": -1,
    })

    assert schema["schema_version"] == "stem-ai-provider-request-v1.4"
    assert validation["status"] == "invalid"
    assert {error["path"] for error in validation["errors"]} == {"provider", "timeout_sec", "max_tokens"}


def test_advisory_packet_mode_adds_provider_request_without_ai_output(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path, advisory="packet")
    packet = result["ai_advisory_input"]

    assert "ai_advisory" not in result
    assert packet["schema_version"] == "stem-ai-advisory-input-v1.4"
    assert packet["packet_profile"] == "provider_budgeted"
    assert packet["provider_request"]["provider"] == "none"
    assert packet["provider_request"]["status"] == "offline_ready"
    assert packet["provider_request"]["args_validation"]["status"] == "valid"
    assert packet["contract_schemas"]["schema_version"] == "stem-ai-advisory-contracts-v1.4"
    assert packet["packet_contract"]["status"] == "valid"
    assert packet["evidence_ledger"]
    assert len(packet["evidence_ledger"]) <= 40
    assert packet["allowed_finding_ids"] == [f["finding_id"] for f in packet["evidence_ledger"]]


def test_cli_advisory_packet_writes_standalone_input_packet(tmp_path: Path) -> None:
    _write(tmp_path / "repo" / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "out"

    code = cli_main(["audit", str(tmp_path / "repo"), "--format", "json", "--out", str(out_dir), "--advisory", "packet"])

    assert code == 0
    [packet_path] = list(out_dir.glob("*_advisory_input.json"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["policy"]["requires_finding_id_citations"] is True
    assert packet["provider_request"]["registry"]
    assert packet["packet_profile"] == "provider_budgeted"
    assert packet["packet_contract"]["status"] == "valid"
    assert len(packet["evidence_ledger"]) <= 40


def test_provider_advisory_input_budget_and_allowed_ids_are_deterministic(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "requirements.txt", "\n".join(f"dep{i}>=1.0" for i in range(60)))
    result = audit_repository(tmp_path)

    packet_a = build_provider_advisory_input(result)
    packet_b = build_provider_advisory_input(result)

    assert packet_a == packet_b
    assert packet_a["packet_profile"] == "provider_budgeted"
    assert len(packet_a["evidence_ledger"]) <= 40
    assert packet_a["omitted_finding_count"] > 0
    assert packet_a["allowed_finding_ids"] == [finding["finding_id"] for finding in packet_a["evidence_ledger"]]
    assert "shortened finding IDs" in packet_a["provider_prompt_contract"]["forbidden_citations"]


def test_advisory_packet_validator_rejects_allowlist_mismatch(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    packet = build_provider_advisory_input(audit_repository(tmp_path))
    packet["allowed_finding_ids"] = ["BROKEN:README.md:1:001"]

    validation = validate_advisory_input_packet(packet)

    assert validation["status"] == "invalid"
    assert "allowed_finding_ids_mismatch" in validation["errors"]


def test_advisory_response_file_validates_provider_json_without_network(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    base = audit_repository(repo)
    cite = next(iter(known_finding_ids(base)))
    response_path = tmp_path / "provider_advisory.json"
    _write(response_path, json.dumps({
        "provider": "openai_compatible",
        "model": "qwen-local",
        "mode": "provider_response_file",
        "reviewer_notes": [
            {
                "claim": "Inspect the cited evidence before review use.",
                "severity": "info",
                "cites": [cite],
                "recommended_action": "Open the cited finding in the evidence ledger.",
            }
        ],
        "inspection_priorities": [],
    }))

    result = audit_repository(repo, advisory_response_path=response_path)
    advisory = result["ai_advisory"]

    assert advisory["status"] == "valid"
    assert advisory["provider"] == "openai_compatible"
    assert advisory["response_contract"]["network_called"] is False
    assert advisory["response_contract"]["citation_repair_attempted"] is False
    assert "source_sha256" in advisory["response_contract"]


def test_advisory_validation_reports_payload_shape_errors(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    result = audit_repository(tmp_path)

    advisory = validate_advisory_output(result, {
        "reviewer_notes": [{"claim": "Inspect.", "cites": ["x"]}],
        "inspection_priorities": {"priority": "high"},
    })

    assert advisory["status"] == "invalid"
    assert "invalid_payload_shape" in advisory["errors"]
    assert any(error["path"] == "reviewer_notes[0].severity" for error in advisory["shape_errors"])
    assert any(error["path"] == "inspection_priorities" for error in advisory["shape_errors"])


def test_advisory_response_file_keeps_malformed_provider_output_invalid(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    response_path = tmp_path / "bad_provider_advisory.json"
    _write(response_path, json.dumps({
        "provider": "gemini",
        "model": "external-model",
        "final_score": 100,
        "reviewer_notes": [
            {
                "claim": "This repository is safe for clinical deployment.",
                "severity": "info",
                "cites": ["NO_SUCH_FINDING:README.md:1:001"],
                "recommended_action": "Use it clinically.",
            }
        ],
        "inspection_priorities": [
            {"priority": "high", "reason": "Missing citations should remain invalid.", "cites": []}
        ],
    }))

    advisory = audit_repository(repo, advisory_response_path=response_path)["ai_advisory"]

    assert advisory["status"] == "invalid"
    assert advisory["invalid_citations"] == ["NO_SUCH_FINDING:README.md:1:001"]
    assert "inspection_priorities[0]" in advisory["missing_citation_items"]
    assert "final_score_override_requested" in advisory["errors"]
    assert "prohibited_clinical_or_regulatory_claims" in advisory["errors"]
    assert advisory["response_contract"]["citation_repair_attempted"] is False


def test_advisory_response_file_parse_error_uses_error_envelope(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    response_path = tmp_path / "broken_provider_advisory.json"
    _write(response_path, "{not-json")

    advisory = audit_repository(repo, advisory_response_path=response_path)["ai_advisory"]

    assert advisory["status"] == "error"
    assert advisory["errors"] == ["response_parse_error"]
    assert advisory["response_error"]["type"] == "response_parse_error"
    assert advisory["response_contract"]["network_called"] is False


def test_advisory_response_file_accepts_utf8_bom(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    base = audit_repository(repo)
    cite = next(iter(known_finding_ids(base)))
    response_path = tmp_path / "provider_advisory_bom.json"
    payload = json.dumps({
        "provider": "external_response",
        "reviewer_notes": [
            {"claim": "Review cited evidence.", "severity": "info", "cites": [cite], "recommended_action": "Inspect cited finding."}
        ],
        "inspection_priorities": [],
    })
    response_path.write_bytes(payload.encode("utf-8-sig"))

    advisory = audit_repository(repo, advisory_response_path=response_path)["ai_advisory"]

    assert advisory["status"] == "valid"
    assert advisory["response_contract"]["parser"] == "json"


def test_cli_advisory_response_writes_validated_ai_advisory_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    base = audit_repository(repo)
    cite = next(iter(known_finding_ids(base)))
    response_path = tmp_path / "provider_advisory.json"
    _write(response_path, json.dumps({
        "provider": "anthropic",
        "model": "external-model",
        "reviewer_notes": [
            {"claim": "Review cited evidence.", "severity": "info", "cites": [cite], "recommended_action": "Inspect cited finding."}
        ],
        "inspection_priorities": [],
    }))
    out_dir = tmp_path / "out"

    code = cli_main([
        "audit", str(repo), "--format", "json", "--out", str(out_dir),
        "--advisory-response", str(response_path),
    ])

    assert code == 0
    [json_path] = list(out_dir.glob("*_experiment_results.json"))
    result = json.loads(json_path.read_text(encoding="utf-8"))
    assert result["ai_advisory"]["status"] == "valid"
    assert result["ai_advisory"]["response_contract"]["network_called"] is False


def test_provider_benchmark_packet_record_and_summary(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    result = audit_repository(tmp_path, advisory="packet")
    repo_entry = {"repo": "example/repo", "local_name": "repo", "local_path": str(tmp_path), "commit": "abc123"}

    record = packet_stats_record(repo_entry, result, result["ai_advisory_input"], Path("packets/repo.json"))
    summary = packet_summary([record])

    assert record["schema_version"] == PROVIDER_BENCHMARK_SCHEMA_VERSION
    assert record["record_type"] == "packet_stats"
    assert record["packet_profile"] == "provider_budgeted"
    assert record["citation_allowlist_exact"] is True
    assert record["packet_finding_count"] == record["allowed_finding_id_count"]
    assert summary["record_count"] == 1
    assert summary["all_citation_allowlists_exact"] is True


def test_provider_benchmark_response_record(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    base = audit_repository(repo)
    cite = next(iter(known_finding_ids(base)))
    response_path = tmp_path / "provider.json"
    _write(response_path, json.dumps({
        "provider": "gemini",
        "model": "external-model",
        "reviewer_notes": [
            {"claim": "Review cited evidence.", "severity": "info", "cites": [cite], "recommended_action": "Inspect cited finding."}
        ],
        "inspection_priorities": [],
    }))
    result = audit_repository(repo, advisory_response_path=response_path)

    record = response_validation_record({"repo": "example/repo", "local_name": "repo"}, result["ai_advisory"], response_path)

    assert record["record_type"] == "provider_response_validation"
    assert record["status"] == "valid"
    assert record["invalid_citation_count"] == 0
    assert record["network_called"] is False


def test_license_restriction_evidence_is_detected_without_score_change(tmp_path: Path) -> None:
    base = tmp_path / "base"
    restricted = tmp_path / "restricted"
    _write(base / "README.md", "Bio repository for molecular analysis.\n")
    _write(restricted / "README.md", "Bio repository for molecular analysis.\n")
    _write(restricted / "LICENSE", "This model is for non-commercial research use only and not for clinical use.\n")

    base_result = audit_repository(base)
    restricted_result = audit_repository(restricted)
    findings = [
        finding for finding in restricted_result["evidence_ledger"]
        if finding["detector"] == "S4_license_restriction"
    ]

    assert restricted_result["replication_score"] == base_result["replication_score"]
    assert restricted_result["stage_4_rubric"]["S4_license_restriction"]["score"] == 0
    assert restricted_result["stage_4_rubric"]["S4_license_restriction"]["max"] == 0
    assert any(finding["status"] == "detected" and finding["severity"] == "warn" for finding in findings)


def test_stage2r_refactor_preserves_score_and_rubric() -> None:
    readme = "Bio sequencing package with pytest CI workflow and clinical decision support notes."
    docs = "Bio sequencing tutorial and pytest workflow guide."
    package = "bio sequencing cli"
    workflow = "pytest workflow"
    tests = "pytest bio sequencing"

    score, rubric = _score_stage_2r(
        readme, docs, package, workflow, tests, "", "",
        clinical_adjacent=True,
        has_disclaimer=False,
    )

    assert score == 75
    assert rubric["R2R_1_readme_package_code_alignment"]["score"] == 15
    assert rubric["R2R_2_readme_docs_alignment"]["score"] == 10
    assert rubric["R2R_3_readme_test_ci_alignment"]["score"] == 10
    assert rubric["R2R_D2_missing_clinical_use_boundary"]["score"] == -20
    assert rubric["verdict"] == "Mixed Local Consistency"


def test_stage2r_limitation_repetition_adds_signal() -> None:
    score, rubric = _score_stage_2r(
        "Bio sequencing package.\n## Limitations\nResearch validation only.",
        "Validation cohort limitations are documented.",
        "bio sequencing cli",
        "",
        "",
        "Known limitations fixed across releases.",
        "",
        clinical_adjacent=False,
        has_disclaimer=False,
    )

    assert score == 85
    assert rubric["R2R_4_limitation_repetition"]["score"] == 10


def test_stage2r_internal_clinical_boundary_contradiction_penalizes() -> None:
    score, rubric = _score_stage_2r(
        "Research use only. This package provides clinical decision support for diagnosis.",
        "",
        "bio diagnosis cli",
        "",
        "",
        "",
        "",
        clinical_adjacent=True,
        has_disclaimer=True,
    )

    assert score == 40
    assert rubric["R2R_D1_internal_clinical_boundary_contradiction"]["score"] == -20
    assert "R2R_D2_missing_clinical_use_boundary" not in rubric


def test_stage2r_stale_metadata_penalizes_version_mismatch() -> None:
    score, rubric = _score_stage_2r(
        "Bio repository.\nVersion: 1.0.0\n",
        "",
        "version = \"2.0.0\"\n",
        "",
        "",
        "",
        "",
        clinical_adjacent=False,
        has_disclaimer=False,
    )

    assert score == 50
    assert rubric["R2R_D3_stale_metadata"]["score"] == -10


def test_stage2r_unsupported_workflow_claim_penalizes_missing_surfaces() -> None:
    score, rubric = _score_stage_2r(
        "Bio repository with a runnable CLI workflow demo and pytest test suite.",
        "",
        "",
        "",
        "",
        "",
        "",
        clinical_adjacent=False,
        has_disclaimer=False,
    )

    assert score == 45
    assert rubric["R2R_D4_unsupported_workflow_claim"]["score"] == -15


def test_stage2r_workflow_claim_with_code_surface_is_not_penalized() -> None:
    score, rubric = _score_stage_2r(
        "Bio repository with a runnable CLI workflow demo.",
        "Run python run_mcp_server.py to start the tool.",
        "",
        "",
        "",
        "",
        "if __name__ == '__main__':\n    main()\n",
        clinical_adjacent=False,
        has_disclaimer=False,
    )

    assert score == 60
    assert "R2R_D4_unsupported_workflow_claim" not in rubric


def test_stage3_changelog_three_tiers(tmp_path: Path) -> None:
    no_changelog, _ = _score_changelog(None, "")
    bare_path = tmp_path / "CHANGELOG.md"
    bare_path.write_text("# Changelog\n", encoding="utf-8")
    bare_score, _ = _score_changelog(bare_path, "# Changelog")
    bug_path = tmp_path / "CHANGELOG_bugs.md"
    bug_path.write_text("# Changelog\n\n## v1.0.1\n- Fixed bug in pipeline.\n", encoding="utf-8")
    bug_score, _ = _score_changelog(bug_path, "# Changelog\n\n## v1.0.1\n- Fixed bug in pipeline.")

    assert no_changelog == 0
    assert bare_score == 5
    assert bug_score == 15


def test_stage3_provenance_three_tiers() -> None:
    no_dep, _ = _score_provenance("", "", "")
    basic, _ = _score_provenance("numpy==1.26.4", "Bioinformatics repo.", "")
    with_source, _ = _score_provenance("numpy==1.26.4", "Data from Zenodo. IRB approved.", "")

    assert no_dep == 0
    assert basic == 10
    assert with_source == 15


def test_stage3_bias_three_tiers() -> None:
    no_bias, _ = _score_bias("No relevant language here.", "")
    vocab_only, _ = _score_bias("Model has known limitations in edge cases.", "")
    with_measurement, _ = _score_bias("Model has known limitations. Subgroup analysis shows performance gap.", "")

    assert no_bias == 0
    assert vocab_only == 8
    assert with_measurement == 15
