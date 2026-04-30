from __future__ import annotations

from pathlib import Path
import json

import stem_ai.detectors as detectors
from stem_ai.advisory_contract import (
    build_advisory_input,
    known_finding_ids,
    validate_advisory_output,
)
from stem_ai.advisory_adapters import ADVISORY_HARNESS_MODES
from stem_ai.advisory_providers import (
    load_provider_config,
    provider_handoff_metadata,
    provider_registry,
)
from stem_ai.cli import main as cli_main
from stem_ai.evidence import make_finding_id
from stem_ai.reasoning_model import (
    benchmark_alignment,
    lane_coherence,
    unique_token_count,
)
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


def test_advisory_packet_mode_adds_provider_request_without_ai_output(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path, advisory="packet")
    packet = result["ai_advisory_input"]

    assert "ai_advisory" not in result
    assert packet["schema_version"] == "stem-ai-advisory-input-v1.4"
    assert packet["provider_request"]["provider"] == "none"
    assert packet["provider_request"]["status"] == "offline_ready"
    assert packet["evidence_ledger"]


def test_cli_advisory_packet_writes_standalone_input_packet(tmp_path: Path) -> None:
    _write(tmp_path / "repo" / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "out"

    code = cli_main(["audit", str(tmp_path / "repo"), "--format", "json", "--out", str(out_dir), "--advisory", "packet"])

    assert code == 0
    [packet_path] = list(out_dir.glob("*_advisory_input.json"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["policy"]["requires_finding_id_citations"] is True
    assert packet["provider_request"]["registry"]


def test_mock_valid_advisory_harness_returns_valid_no_network_contract(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path, advisory="mock-valid")
    advisory = result["ai_advisory"]

    assert "mock-valid" in ADVISORY_HARNESS_MODES
    assert advisory["status"] == "valid"
    assert advisory["provider"] == "mock"
    assert advisory["adapter_contract"]["network_called"] is False
    assert advisory["adapter_contract"]["citation_repair_attempted"] is False
    assert advisory["invalid_citations"] == []


def test_mock_invalid_advisory_harness_does_not_repair_bad_output(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path, advisory="mock-invalid")
    advisory = result["ai_advisory"]

    assert advisory["status"] == "invalid"
    assert "MOCK:NO_SUCH_FINDING:001" in advisory["invalid_citations"]
    assert "inspection_priorities[0]" in advisory["missing_citation_items"]
    assert "final_score_override_requested" in advisory["errors"]
    assert "prohibited_clinical_or_regulatory_claims" in advisory["errors"]
    assert advisory["adapter_contract"]["citation_repair_attempted"] is False


def test_mock_error_and_timeout_use_standard_error_envelope(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    error_result = audit_repository(tmp_path, advisory="mock-error")["ai_advisory"]
    timeout_result = audit_repository(tmp_path, advisory="mock-timeout")["ai_advisory"]

    assert error_result["status"] == "error"
    assert error_result["adapter_error"]["type"] == "adapter_error"
    assert error_result["adapter_contract"]["network_called"] is False
    assert timeout_result["status"] == "error"
    assert timeout_result["adapter_error"]["type"] == "timeout"
    assert timeout_result["adapter_contract"]["network_called"] is False


def test_cli_mock_invalid_writes_invalid_ai_advisory_json(tmp_path: Path) -> None:
    _write(tmp_path / "repo" / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "out"

    code = cli_main(["audit", str(tmp_path / "repo"), "--format", "json", "--out", str(out_dir), "--advisory", "mock-invalid"])

    assert code == 0
    [json_path] = list(out_dir.glob("*_experiment_results.json"))
    result = json.loads(json_path.read_text(encoding="utf-8"))
    assert result["ai_advisory"]["status"] == "invalid"
    assert result["ai_advisory"]["adapter_contract"]["network_called"] is False
