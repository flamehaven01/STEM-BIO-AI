from __future__ import annotations

from pathlib import Path
import json
from datetime import date

import stem_ai.detectors as detectors
from stem_ai.advisory_contract import (
    _fallback_citations,
    advisory_contract_schemas,
    build_advisory_input,
    build_provider_advisory_input,
    known_finding_ids,
    validate_advisory_input_packet,
    validate_advisory_output,
)
from stem_ai.advisory_providers import (
    load_provider_config,
    provider_env_contract,
    provider_handoff_metadata,
    provider_request_schema,
    provider_registry,
    provider_secret_policy,
    redact_secret_text,
    validate_provider_request_args,
)
from stem_ai.advisory_runtime import (
    advisory_log_policy,
    build_child_env_allowlist,
    execute_advisory_call,
    provider_call_runtime,
)
from stem_ai.calibration_profile import (
    available_policy_names,
    calibration_profile_metadata,
    load_calibration_profile,
    load_calibration_profile_file,
    validate_profile,
)
from stem_ai.cli import main as cli_main
from stem_ai.policy_intent import derive_policy_intent, simulate_policy_outcome
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
from stem_ai.regulatory_traceability import build_regulatory_basis
from stem_ai.redaction import redact_object, redaction_policy, sanitize_artifact_text, secret_scan
from stem_ai.render import _explain_status_label, render_explain, render_markdown, render_pdf_pages
from stem_ai.render_html import render_html
from stem_ai.scanner import _score_bias, _score_changelog, _score_provenance, _score_stage_2r, audit_repository


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_loose_dependency_ranges_warn(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    _write(tmp_path / "requirements.txt", "gradio>=4.44.0\nreportlab>=4.0\n")

    result = audit_repository(tmp_path)

    assert result["code_integrity"]["C2_dependency_pinning"]["status"] == "WARN"


def test_evidence_findings_surface_confidence_and_evidence_status(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    _write(tmp_path / "requirements.txt", "numpy>=1.26\n")

    result = audit_repository(tmp_path)
    finding = next(f for f in result["evidence_ledger"] if f["detector"] == "C2_dependency_pinning")

    assert finding["evidence_status"] == "confirmed_present"
    assert finding["confidence"] == "high"


def test_audit_freshness_surfaces_expiry_and_reaudit_triggers(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Automated diagnostic decision support research package.\n")

    result = audit_repository(tmp_path)
    freshness = result["audit_freshness"]

    assert freshness["review_after_days"] == 45
    assert freshness["freshness_basis"] == "clinical_adjacent_short_cycle"
    assert "git_commit_changed" in freshness["change_triggers"]
    assert "readme_or_docs_claim_surface_changed" in freshness["change_triggers"]
    assert "expires_on" in freshness


def test_markdown_and_explain_surface_audit_freshness(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, "brief", 1)
    explain = render_explain(result)

    assert "## Audit Freshness" in markdown
    assert "Audit Freshness" in explain
    assert "review_after_days" in explain


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


def test_classification_surfaces_ca_taxonomy_metadata(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Automated diagnostic decision support for patient treatment recommendation.\n")

    result = audit_repository(tmp_path)

    assert result["classification"]["ca_taxonomy_version"] == "ca-taxonomy-v1"
    assert result["classification"]["ca_taxonomy_source"] == "runtime_regex_hardcoded_in_scanner_py"


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
        "    code = '''\\napi_key = \\\"sk-1234567890abcdefghijklmn\\\"\\n'''\n",
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


def test_bio_smiles_surface_detector_flags_malformed_and_placeholder_strings(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(
        tmp_path / "generator.py",
        "bad_smiles_ring = 'C1CC'\n"
        "bad_smiles_branch = 'C(C'\n"
        "PLACEHOLDER = 'CCCCCCCCCC'\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_surface_integrity" and f["status"] == "detected"]

    assert findings
    issues = [issue for finding in findings for issue in finding.get("metadata", {}).get("issues", [])]
    assert "unclosed_ring_label" in issues
    assert "unbalanced_parentheses" in issues
    assert "low_entropy_placeholder_pattern" in issues


def test_bio_smiles_surface_detector_ignores_hex_colors_and_versionish_strings(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(
        tmp_path / "plot.py",
        "PRIMARY = '#8b949e'\n"
        "SCHEMA = 'stem-ai-advisory-v1.4'\n"
        "ENC = 'utf-8-sig'\n"
        "HASH = 'sha256'\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_surface_integrity"]

    assert any(f["status"] == "not_detected" for f in findings)
    assert not any(f["status"] == "detected" for f in findings)


def test_bio_smiles_surface_detector_ignores_generated_build_paths(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(tmp_path / "build" / "lib" / "generated.py", "bad_smiles_ring = 'C1CC'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_surface_integrity"]

    assert any(f["status"] == "not_detected" for f in findings)
    assert not any(f["status"] == "detected" for f in findings)


def test_bio_smiles_rdkit_validation_is_not_applicable_without_rdkit(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    monkeypatch.setattr(detector_bio, "_rdkit_mol_from_smiles", lambda smiles: detector_bio._RDKIT_UNAVAILABLE)
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(tmp_path / "pipeline.py", "bad_smiles = 'C1CC'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_rdkit_validation"]

    assert any(f["status"] == "not_applicable" for f in findings)


def test_bio_smiles_rdkit_validation_flags_invalid_candidate_when_available(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    def fake_rdkit(smiles: str):
        if smiles == "C1CC":
            return None
        return object()

    monkeypatch.setattr(detector_bio, "_rdkit_mol_from_smiles", fake_rdkit)
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(tmp_path / "pipeline.py", "bad_smiles = 'C1CC'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_rdkit_validation" and f["status"] == "detected"]

    assert findings
    assert findings[0]["metadata"]["smiles_text"] == "C1CC"


def test_bio_smiles_rdkit_validation_reports_not_detected_when_available_and_valid(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    monkeypatch.setattr(detector_bio, "_rdkit_is_available", lambda: True)
    monkeypatch.setattr(detector_bio, "_rdkit_mol_from_smiles", lambda smiles: object())
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(tmp_path / "pipeline.py", "candidate_smiles = 'CC(=O)O'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_rdkit_validation"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_smiles_rdkit_validation_reports_not_detected_when_available_without_candidates(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    monkeypatch.setattr(detector_bio, "_rdkit_is_available", lambda: True)
    monkeypatch.setattr(detector_bio, "_rdkit_mol_from_smiles", lambda smiles: object())
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(tmp_path / "pipeline.py", "PRIMARY = '#8b949e'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_rdkit_validation"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_smiles_parser_guard_flags_missing_none_check(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(
        tmp_path / "pipeline.py",
        "def build(smiles):\n"
        "    mol = Chem.MolFromSmiles(smiles)\n"
        "    return mol.GetNumAtoms()\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_parser_guard" and f["status"] == "detected"]

    assert findings
    assert findings[0]["metadata"]["variable"] == "mol"
    assert findings[0]["metadata"]["parser_call"] == "Chem.MolFromSmiles"


def test_bio_smiles_parser_guard_accepts_explicit_none_check(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(
        tmp_path / "pipeline.py",
        "def build(smiles):\n"
        "    mol = Chem.MolFromSmiles(smiles)\n"
        "    if mol is None:\n"
        "        raise ValueError('invalid smiles')\n"
        "    return mol.GetNumAtoms()\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_parser_guard"]

    assert result["score"]["raw_score_before_floor"] == result["score"]["final_score"]
    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_smiles_parser_guard_flags_allchem_missing_none_check(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    _write(
        tmp_path / "pipeline.py",
        "def build(seq):\n"
        "    mol = AllChem.MolFromSmiles(seq)\n"
        "    return AllChem.AddHs(mol)\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_parser_guard" and f["status"] == "detected"]

    assert findings
    assert findings[0]["metadata"]["variable"] == "mol"
    assert findings[0]["metadata"]["parser_call"] == "AllChem.MolFromSmiles"


def test_bio_silent_mock_detector_flags_import_fallback_to_mock_mode(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for immunology analysis.\n")
    _write(
        tmp_path / "immunology.py",
        "try:\n"
        "    import FlowCytometryTools\n"
        "except ImportError:\n"
        "    USE_MOCK = True\n"
        "    provider = 'simulated data'\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_silent_mock_fallback" and f["status"] == "detected"]

    assert findings
    assert any(f["metadata"]["reason"] == "import_failure_sets_mock_flag" for f in findings)


def test_bio_silent_mock_detector_marks_explicit_demo_branch_not_applicable(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for immunology analysis.\n")
    _write(
        tmp_path / "pipeline.py",
        "def run(sample):\n"
        "    if DEMO_MODE:\n"
        "        return {'mode': 'synthetic', 'sample': sample}\n"
        "    return {'mode': 'real'}\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_silent_mock_fallback"]

    assert findings
    assert any(f["status"] == "not_applicable" and f["metadata"]["reason"] == "explicit_demo_mode_branch" for f in findings)


def test_bio_silent_mock_detector_ignores_test_fixture_paths(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for immunology analysis.\n")
    _write(
        tmp_path / "tests" / "test_mock.py",
        "try:\n"
        "    import rdkit\n"
        "except ImportError:\n"
        "    USE_MOCK = True\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_silent_mock_fallback"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_trace_manifest_detector_flags_traceability_files_and_keywords(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for traceable molecular analysis.\n")
    _write(
        tmp_path / "audit_log_schema.json",
        "{\n"
        "  \"decision_event\": true,\n"
        "  \"model_version\": \"v1\",\n"
        "  \"input_hash\": \"abc\",\n"
        "  \"output_hash\": \"def\"\n"
        "}\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_trace_manifest" and f["status"] == "detected"]

    assert findings
    assert any(f["pattern_id"] == "bio_trace_manifest_file_v1" for f in findings)
    assert any(f.get("metadata", {}).get("matched_term") == "decision_event" for f in findings)


def test_bio_trace_manifest_detector_flags_keywords_in_docs(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for traceable molecular analysis.\n")
    _write(
        tmp_path / "docs" / "traceability.md",
        "# Traceability\n"
        "Each override_event stores operator_id, timestamp, and dataset_hash.\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_trace_manifest" and f["status"] == "detected"]

    assert findings
    matched_terms = {f.get("metadata", {}).get("matched_term") for f in findings if "metadata" in f}
    assert "override_event" in matched_terms


def test_bio_trace_manifest_detector_reports_not_detected_when_absent(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "pipeline.py", "def run():\n    return 1\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_trace_manifest"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_run_trace_flags_shell_true_with_tainted_bio_tool_command(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    _write(
        tmp_path / "pipeline.py",
        "import subprocess\n"
        "def run(query_path):\n"
        "    subprocess.run(f'blastn -query {query_path}', shell=True)\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_run_trace" and f["status"] == "detected"]

    assert findings
    assert any(f["severity"] == "warn" and f["metadata"]["shell_true"] is True and f["metadata"]["external_input_taint"] is True for f in findings)


def test_bio_run_trace_flags_shell_true_without_obvious_taint_as_info(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    _write(
        tmp_path / "pipeline.py",
        "import subprocess\n"
        "def run():\n"
        "    subprocess.run('samtools view sample.bam', shell=True)\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_run_trace" and f["status"] == "detected"]

    assert findings
    assert any(f["severity"] == "info" and f["metadata"]["shell_true"] is True for f in findings)


def test_bio_run_trace_flags_missing_timeout_for_known_bio_tool(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    _write(
        tmp_path / "pipeline.py",
        "import subprocess\n"
        "def run():\n"
        "    subprocess.run(['bcftools', 'view', 'sample.vcf'])\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_run_trace" and f["status"] == "detected"]

    assert findings
    assert any(f["severity"] == "info" and f["metadata"]["timeout_present"] is False for f in findings)


def test_bio_run_trace_does_not_flag_safe_known_bio_tool_argv_with_timeout(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    _write(
        tmp_path / "pipeline.py",
        "import subprocess\n"
        "def run():\n"
        "    subprocess.run(['bedtools', 'intersect', '-a', 'a.bed', '-b', 'b.bed'], timeout=30)\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_run_trace"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_run_trace_flags_os_system_for_known_bio_tool(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    _write(
        tmp_path / "pipeline.py",
        "import os\n"
        "def run(sample_path):\n"
        "    os.system('minimap2 ' + sample_path)\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_run_trace" and f["status"] == "detected"]

    assert findings
    assert any(f["metadata"]["call_name"] == "os.system" and f["severity"] == "warn" for f in findings)


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

    assert result["schema_version"] == "stem-ai-local-cli-result-v1.6"
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


def test_stage1_hipaa_self_assertion_is_weak_signal_not_full_regulatory_credit(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio medical repository for molecular review.\n"
        "HIPAA-compliant architecture when self-hosted.\n",
    )

    result = audit_repository(tmp_path)
    rubric = result["stage_1_rubric"]
    detectors_seen = {finding["detector"] for finding in result["evidence_ledger"] if finding["status"] == "detected"}

    assert result["score"]["stage_1_readme_intent"] == 75
    assert rubric["R2_regulatory_framework"]["score"] == 5
    assert "S1_R2_weak_regulatory_self_assertion" in detectors_seen
    assert "S1_R2_regulatory_framework" not in detectors_seen
    assert "Self-asserted compliance or privacy-governance claim requires independent verification." in result["notable_risks"]


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


def test_ast_file_limit_surfaces_in_markdown_and_pdf(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(detectors, "MAX_AST_FILES", 1)
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(tmp_path / "a.py", "def a():\n    return 1\n")
    _write(tmp_path / "b.py", "def b():\n    return 2\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, mode="brief", pages=1)
    pages = render_pdf_pages(result, mode="brief", pages=1)
    page_text = "\n".join(pages[0])

    assert "AST analysis scope" in markdown
    assert "excluded from C1/C4 AST-backed analysis" in markdown
    assert "AST analysis scope:" in page_text
    assert "excluded from C1/C4 AST-backed analysis" in page_text


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


def test_stage4_dataset_url_does_not_credit_generic_data_api_marketing_line(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio medical repository for literature review.\n"
        "- Built with [Valyu](https://platform.valyu.ai) - The unified biomedical data API\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "S4_dataset_url"]

    assert result["stage_4_rubric"]["S4_dataset_url"]["score"] == 0
    assert any(f["status"] == "not_detected" for f in findings)


def test_stage4_javascript_lockfiles_count_as_lock_and_exact_resolution_evidence(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio medical repository.\n"
        "Dataset: https://zenodo.org/records/12345\n",
    )
    _write(tmp_path / "pnpm-lock.yaml", "lockfileVersion: '9.0'\n")

    result = audit_repository(tmp_path)

    assert result["stage_4_rubric"]["S4_environment_lock_evidence"]["score"] == 10
    assert result["stage_4_rubric"]["S4_exact_dependency_pins_or_hashes"]["score"] == 10


def test_single_external_service_dependency_surfaces_required_provider_lock_in(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "# Bio\n"
        "Self-hosted mode is the recommended way to run Bio.\n"
        "Powered by Valyu's specialized biomedical data API.\n",
    )
    _write(
        tmp_path / ".env.example",
        "# VALYU API (REQUIRED)\n"
        "VALYU_API_KEY=valyu_your_api_key_here\n"
        "# OPENAI API (OPTIONAL)\n"
        "OPENAI_API_KEY=sk-your_openai_api_key_here\n",
    )

    result = audit_repository(tmp_path)

    by_detector = result["detector_summary"]["by_detector"]["R2R_D5_single_external_service_dependency"]
    assert by_detector["detected"] >= 2
    assert "Core workflow appears materially dependent on named external service providers; local or self-host claims may overstate operational independence." in result["notable_risks"]


def test_single_external_service_dependency_ignores_optional_provider_only_surface(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Repo\nOptional OpenAI fallback only.\n")
    _write(
        tmp_path / ".env.example",
        "# OPENAI API (OPTIONAL)\n"
        "OPENAI_API_KEY=sk-your_openai_api_key_here\n",
    )

    result = audit_repository(tmp_path)

    assert result["detector_summary"]["by_detector"]["R2R_D5_single_external_service_dependency"]["not_detected"] == 1
    assert "Core workflow appears materially dependent on named external service providers; local or self-host claims may overstate operational independence." not in result["notable_risks"]


def test_unsupported_legal_claim_surfaces_without_grounding_and_enters_traceability(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "# Repo\n"
        "HIPAA-compliant architecture for clinical deployment.\n",
    )

    result = audit_repository(tmp_path)

    assert result["detector_summary"]["by_detector"]["S1_R2_unsupported_legal_or_compliance_claim"]["detected"] == 1
    assert "Legal, privacy, or compliance claim appears without supporting governance or security-grounding evidence in reviewed repository sources." in result["notable_risks"]
    stage1 = result["stage_traceability"]["stage_1"]
    assert any(item["requirement_id"] == "COMPLIANCE_CLAIM_GROUNDING_SIGNAL" for item in stage1)


def test_unsupported_legal_claim_ignored_when_grounding_language_present(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "# Repo\n"
        "HIPAA-compliant architecture with audit logging, access control, encryption at rest, and incident response.\n",
    )

    result = audit_repository(tmp_path)

    assert result["detector_summary"]["by_detector"]["S1_R2_unsupported_legal_or_compliance_claim"]["not_detected"] == 1
    assert "Legal, privacy, or compliance claim appears without supporting governance or security-grounding evidence in reviewed repository sources." not in result["notable_risks"]


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


def test_bio_detectors_surface_in_markdown_and_explain(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(
        tmp_path / "pipeline.py",
        "import subprocess\n"
        "BAD = 'C1CC'\n"
        "def run(query_path):\n"
        "    subprocess.run(f'blastn -query {query_path}', shell=True)\n"
        "    return BAD\n",
    )

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, mode="detailed", pages=3)
    explain = render_explain(result)

    assert "Bio Deterministic Diagnostics" in markdown
    assert "SMILES Surface Integrity" in markdown
    assert "Bio Subprocess Run Trace" in markdown
    assert "Bio Deterministic Diagnostics" in explain
    assert "SMILES Surface Integrity" in explain
    assert "Bio Subprocess Run Trace" in explain


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


def test_score_provenance_negative_irb_context_does_not_get_max_credit() -> None:
    score, evidence = _score_provenance(
        "numpy==1.26.4",
        "Data availability: no IRB required for this public benchmark dataset.\n",
        "",
    )

    assert score == 10
    assert "negative or non-approval context" in evidence


def test_score_bias_single_minimal_limitation_term_no_longer_gets_partial_credit() -> None:
    score, evidence = _score_bias("A short note says limitations exist.", "")

    assert score == 0
    assert "minimal single-term" in evidence


def test_score_bias_structured_limitations_still_gets_partial_credit() -> None:
    score, evidence = _score_bias("## Limitations\nKnown limitations in edge cases are documented.\n", "")

    assert score == 8
    assert "Structured bias/limitations language" in evidence


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
    assert handoff["api_key_env_var"] == "STEM_AI_ADVISORY_API_KEY"
    assert handoff["secret_source"] == "generic_env"
    assert handoff["network_mode"] == "local_server"
    assert handoff["base_url_validation"]["status"] == "valid"
    assert handoff["secret_policy"]["schema_version"] == "stem-ai-secret-policy-v1.5"
    assert handoff["env_contract"]["provider_api_keys"]["openai"] == "OPENAI_API_KEY"


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


def test_provider_specific_env_var_takes_precedence_over_generic_fallback() -> None:
    config = load_provider_config({
        "STEM_AI_ADVISORY_PROVIDER": "openai",
        "OPENAI_API_KEY": "provider-secret",
        "STEM_AI_ADVISORY_API_KEY": "generic-secret",
    })

    handoff = provider_handoff_metadata(config)

    assert handoff["api_key_present"] is True
    assert handoff["api_key_env_var"] == "OPENAI_API_KEY"
    assert handoff["secret_source"] == "provider_env"
    assert "provider-secret" not in json.dumps(handoff)
    assert "generic-secret" not in json.dumps(handoff)


def test_provider_request_validator_rejects_embedded_credentials_and_remote_http() -> None:
    validation = validate_provider_request_args({
        "provider": "openai_compatible",
        "base_url": "http://user:pass@example.com/v1",
        "timeout_sec": 30,
        "max_tokens": 1024,
    })

    assert validation["status"] == "invalid"
    assert validation["base_url_validation"]["code"] == "embedded_credentials_forbidden"
    assert "redacted-user@example.com" in validation["normalized"]["base_url"]


def test_cloud_provider_requires_https_and_api_key() -> None:
    validation = validate_provider_request_args({
        "provider": "openai",
        "base_url": "http://localhost:8000/v1",
        "api_key_present": False,
        "timeout_sec": 30,
        "max_tokens": 1024,
    })

    assert validation["status"] == "invalid"
    assert {error["code"] for error in validation["errors"]} == {"https_required", "missing_api_key"}


def test_provider_secret_policy_and_env_contract_are_exportable() -> None:
    policy = provider_secret_policy()
    contract = provider_env_contract()

    assert policy["schema_version"] == "stem-ai-secret-policy-v1.5"
    assert "OPENAI_API_KEY" == contract["provider_api_keys"]["openai"]
    assert contract["generic_fallback"] == "STEM_AI_ADVISORY_API_KEY"
    assert any("CLI arguments" in rule for rule in policy["rules"])


def test_redact_secret_text_masks_known_prefixes() -> None:
    text = redact_secret_text("https://example.com sk-abcdefghijklmnop")

    assert "abcdefghijklmnop" not in text
    assert "[REDACTED]" in text


def test_advisory_log_policy_is_structured_and_secret_safe() -> None:
    policy = advisory_log_policy()

    assert policy["schema_version"] == "stem-ai-advisory-log-policy-v1.5"
    assert "api_key_value" in policy["forbidden_fields"]
    assert policy["exception_sanitization"] is True


def test_child_env_allowlist_keeps_only_required_keys() -> None:
    config = load_provider_config({
        "STEM_AI_ADVISORY_PROVIDER": "openai",
        "OPENAI_API_KEY": "provider-secret",
        "PATH": "C:\\Windows\\System32",
        "UNRELATED_SECRET": "drop-me",
    })

    child_env = build_child_env_allowlist(config, {
        "STEM_AI_ADVISORY_PROVIDER": "openai",
        "OPENAI_API_KEY": "provider-secret",
        "PATH": "C:\\Windows\\System32",
        "UNRELATED_SECRET": "drop-me",
    })

    assert child_env["OPENAI_API_KEY"] == "provider-secret"
    assert child_env["PATH"] == "C:\\Windows\\System32"
    assert "UNRELATED_SECRET" not in child_env


def test_provider_call_runtime_exports_logging_and_child_env_contract() -> None:
    config = load_provider_config({
        "STEM_AI_ADVISORY_PROVIDER": "openai_compatible",
        "STEM_AI_ADVISORY_BASE_URL": "http://localhost:11434/v1",
        "OPENAI_COMPATIBLE_API_KEY": "provider-secret",
        "PATH": "C:\\Windows\\System32",
    })

    runtime = provider_call_runtime(config, {
        "STEM_AI_ADVISORY_PROVIDER": "openai_compatible",
        "STEM_AI_ADVISORY_BASE_URL": "http://localhost:11434/v1",
        "OPENAI_COMPATIBLE_API_KEY": "provider-secret",
        "PATH": "C:\\Windows\\System32",
    })

    assert runtime["mode"] == "explicit_network_opt_in"
    assert runtime["network_intent"] is True
    assert runtime["network_called"] is False
    assert runtime["log_policy"]["schema_version"] == "stem-ai-advisory-log-policy-v1.5"
    assert "OPENAI_COMPATIBLE_API_KEY" in runtime["child_env_allowlist"]["keys"]


def test_execute_advisory_call_returns_explicit_not_implemented_error_without_network() -> None:
    result = {
        "target": {"name": "example/repo", "remote": None, "branch": None, "commit": None, "file_count": 1},
        "score": {"final_score": 50, "formal_tier": "T1 Quarantine"},
        "classification": {},
        "code_integrity": {
            "C1_hardcoded_credentials": {"status": "PASS", "evidence": ["none"]},
            "C2_dependency_pinning": {"status": "PASS", "evidence": ["none"]},
            "C3_dead_or_deprecated_patient_adjacent_paths": {"status": "PASS", "evidence": ["none"]},
            "C4_exception_handling_clinical_adjacent_paths": {"status": "PASS", "evidence": ["none"]},
        },
        "detector_summary": {},
        "reasoning_model": {},
        "stage_4_rubric": {},
        "ast_signal_summary": {},
        "evidence_ledger": [{"finding_id": "X:README.md:1:001", "status": "detected", "detector": "X"}],
    }

    advisory = execute_advisory_call(result, {
        "STEM_AI_ADVISORY_PROVIDER": "openai",
        "OPENAI_API_KEY": "provider-secret",
        "PATH": "C:\\Windows\\System32",
    })

    assert advisory["status"] == "error"
    assert advisory["errors"] == ["adapter_not_implemented"]
    assert advisory["provider_call"]["network_called"] is False
    assert advisory["provider_call"]["network_intent"] is True


def test_redaction_utilities_scrub_objects_and_artifact_text() -> None:
    scan = secret_scan("Authorization: Bearer secret-token-value")
    clean_text, artifact_scan = sanitize_artifact_text("api_key=super-secret-key")
    payload = redact_object({"token": "ghp_abcdefghijklmnopqrstuvwxyz"})

    assert scan["status"] == "detected"
    assert "secret-token-value" not in clean_text
    assert artifact_scan["status"] == "detected"
    assert payload["token"] == "[REDACTED]"
    assert redaction_policy()["artifact_behavior"] == "sanitize_before_write"


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


def test_cli_shorthand_defaults_to_scan_command_and_output_alias(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "results"

    code = cli_main([
        str(repo),
        "--format", "json",
        "--output", str(out_dir),
        "--summary", "compact",
    ])

    captured = capsys.readouterr()

    assert code == 0
    assert "STEM BIO-AI | scan |" in captured.out
    assert list(out_dir.glob("*_experiment_results.json"))


def test_cli_output_under_stem_output_creates_repo_subfolder(tmp_path: Path) -> None:
    repo = tmp_path / "Bio Repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "stem_output"

    code = cli_main([
        "scan",
        str(repo),
        "--format", "json",
        "--summary", "off",
        "--output", str(out_dir),
    ])

    repo_out = out_dir / "Bio-Repo"

    assert code == 0
    assert repo_out.is_dir()
    assert list(repo_out.glob("*_experiment_results.json"))


def test_cli_summary_surfaces_ast_cap_limit(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(detectors, "MAX_AST_FILES", 1)
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    _write(repo / "a.py", "def a():\n    return 1\n")
    _write(repo / "b.py", "def b():\n    return 2\n")

    code = cli_main([
        str(repo),
        "--format", "json",
        "--summary", "compact",
        "--output", str(tmp_path / "results"),
    ])

    captured = capsys.readouterr()

    assert code == 0
    assert "AST: capped at 1 / 2 python files" in captured.out


def test_cli_gate_subcommand_enforces_threshold_and_uses_compact_summary(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "gate"

    code = cli_main([
        "gate",
        str(repo),
        "--min-tier", "T4",
        "--output", str(out_dir),
    ])

    captured = capsys.readouterr()

    assert code == 1
    assert "STEM BIO-AI | gate |" in captured.out
    assert "Gate: FAIL" in captured.out
    assert list(out_dir.glob("*_experiment_results.json"))


def test_cli_advisory_packet_subcommand_writes_packet_json(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "packet"

    code = cli_main([
        "advisory",
        "packet",
        str(repo),
        "--output", str(out_dir),
    ])

    captured = capsys.readouterr()
    [json_path] = list(out_dir.glob("*_experiment_results.json"))
    result = json.loads(json_path.read_text(encoding="utf-8"))

    assert code == 0
    assert "STEM BIO-AI | advisory packet |" in captured.out
    assert result["ai_advisory_input"]["packet_profile"] == "provider_budgeted"


def test_cli_advisory_check_response_subcommand_validates_response_file(tmp_path: Path, capsys) -> None:
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
    out_dir = tmp_path / "response"

    code = cli_main([
        "advisory",
        "check-response",
        str(repo),
        "--response", str(response_path),
        "--output", str(out_dir),
    ])

    captured = capsys.readouterr()
    [json_path] = list(out_dir.glob("*_experiment_results.json"))
    result = json.loads(json_path.read_text(encoding="utf-8"))

    assert code == 0
    assert "STEM BIO-AI | advisory check-response |" in captured.out
    assert result["ai_advisory"]["status"] == "valid"


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
    js_lock_with_source, _ = _score_provenance("lockfileVersion: '9.0'\n", "Data from Zenodo. IRB approved.", "")

    assert no_dep == 0
    assert basic == 10
    assert with_source == 15
    assert js_lock_with_source == 15


def test_stage3_bias_three_tiers() -> None:
    no_bias, _ = _score_bias("No relevant language here.", "")
    vocab_only, _ = _score_bias("Model has known limitations in edge cases.", "")
    structured_only, _ = _score_bias("## Limitations\nKnown limitations in edge cases.\n", "")
    with_measurement, _ = _score_bias("Model has known limitations. Subgroup analysis shows performance gap.", "")

    assert no_bias == 0
    assert vocab_only == 0
    assert structured_only == 8
    assert with_measurement == 15


def test_audit_repository_emits_regulatory_basis_and_stage_traceability(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio repository.\n\n## Limitations\nResearch use only. Not for clinical use.\n"
        "Dataset provenance and subgroup analysis are documented.\n",
    )
    _write(tmp_path / "CHANGELOG.md", "# Changelog\n\n## v1.0.1\n- Fixed bug in pipeline.\n")
    _write(tmp_path / "requirements.txt", "numpy==1.26.4\n")
    _write(tmp_path / "checksums.txt", "abc123  model.bin\n")

    result = audit_repository(tmp_path)

    assert result["regulatory_basis"]["registry_version"] == "stem-ai-regulatory-basis-registry-v1"
    assert result["regulatory_basis"]["note"]["title"] == "Regulatory basis note"
    assert result["stage_traceability"]["stage_1"]
    assert result["stage_traceability"]["stage_3"]
    assert result["stage_traceability"]["stage_4"]
    assert result["regulatory_traceability"]["version"] == "stem-ai-reg-trace-v1.6"
    assert "pre-audit traceability aid" in result["regulatory_traceability"]["summary"]


def test_stage1_traceability_does_not_treat_missing_boundary_as_alignment(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Clinical decision support prototype for patient triage.\n",
    )

    result = audit_repository(tmp_path)
    stage1 = result["stage_traceability"]["stage_1"]

    assert stage1
    assert stage1[0]["status"] == "not_detected"
    assert "transparency scaffolding" not in result["regulatory_traceability"]["summary"]


def test_markdown_and_explain_include_regulatory_basis_note(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bio repository. Research use only. Not for clinical use.\n",
    )
    _write(tmp_path / "CHANGELOG.md", "# Changelog\n\n## v1.0.1\n- Fixed bug in pipeline.\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, mode="brief", pages=1)
    explain = render_explain(result)

    assert "Regulatory Traceability Assistant" in markdown
    assert "Regulatory basis note" in markdown
    assert "This is a traceability aid, not a compliance or clearance determination." in markdown
    assert "Regulatory Traceability Assistant" in explain
    assert "Regulatory basis note" in explain


def test_bio_markdown_uses_scope_specific_note_when_detector_not_detected(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, mode="brief", pages=1)

    assert "No malformed or suspicious SMILES-like strings detected by conservative surface checks." in markdown


def test_write_outputs_json_remains_valid_with_placeholder_credential_snippet(tmp_path: Path) -> None:
    from stem_ai.render import write_outputs

    _write(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    _write(
        tmp_path / "tests" / "test_provider.py",
        'provider = ICAMetadataProvider(api_key="super-secret-key", session=session)\n',
    )

    result = audit_repository(tmp_path)
    out_dir = tmp_path / "out"
    write_outputs(result, out_dir, mode="brief", pages=1, fmt="json", explain=False)

    [json_path] = list(out_dir.glob("*_experiment_results.json"))
    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["schema_version"].startswith("stem-ai-local-cli-result")


def test_regulatory_basis_review_required_is_false_for_current_registry_month() -> None:
    basis = build_regulatory_basis(date(2026, 5, 6))

    assert basis["review_required"] is False
    assert basis["review_reasons"] == []


def test_default_calibration_profile_loads_with_computed_sha256() -> None:
    profile = load_calibration_profile("default")

    assert profile["profile_name"] == "default"
    assert profile["profile_read_mode"] == "mirror_only"
    assert isinstance(profile["policy_sha256"], str)
    assert len(profile["policy_sha256"]) == 64


def test_strict_clinical_profile_loads_with_defined_diff() -> None:
    profile = load_calibration_profile("strict_clinical_adjacency")

    assert profile["clinical_policy"]["ca_no_disclaimer_cap"] == 60
    assert profile["clinical_policy"]["t0_hard_floor_cap"] == 35
    assert profile["profile_status"] == "experimental"


def test_validate_profile_rejects_weights_that_do_not_sum_to_100() -> None:
    profile = load_calibration_profile("default")
    profile["weights"]["stage_3_percent"] = 41

    try:
        validate_profile(profile)
    except ValueError as exc:
        assert "sum to 100" in str(exc)
    else:
        raise AssertionError("Expected validate_profile to reject invalid weights")


def test_validate_profile_rejects_non_monotonic_tier_boundaries() -> None:
    profile = load_calibration_profile("default")
    profile["tier_policy"]["tier_boundaries"] = [69, 40, 55, 85]

    try:
        validate_profile(profile)
    except ValueError as exc:
        assert "strictly increasing" in str(exc)
    else:
        raise AssertionError("Expected validate_profile to reject non-monotonic boundaries")


def test_validate_profile_rejects_authoritative_mode_without_declared_hash() -> None:
    profile = load_calibration_profile("default")
    profile["profile_read_mode"] = "authoritative"
    profile["policy_sha256"] = None

    try:
        validate_profile(profile)
    except ValueError as exc:
        assert "must declare a policy_sha256" in str(exc)
    else:
        raise AssertionError("Expected validate_profile to reject authoritative mode without hash")


def test_audit_repository_surfaces_calibration_profile_metadata(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral genome analysis.\n")

    result = audit_repository(tmp_path)
    calibration = result["calibration_profile"]

    assert calibration["policy_schema_version"] == "1"
    assert calibration["policy_version"] == "ca-policy-1.0"
    assert calibration["profile_name"] == "default"
    assert calibration["profile_read_mode"] == "mirror_only"
    assert calibration["profile_status"] == "authoritative_release"
    assert isinstance(calibration["policy_sha256"], str)


def test_markdown_and_explain_surface_calibration_profile(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral genome analysis.\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, mode="brief", pages=1)
    explain = render_explain(result)
    html = render_html(result)

    assert "**Calibration Profile:** `default` (`ca-policy-1.0`, `mirror_only`, `authoritative_release`)" in markdown
    assert "**Calibration Effect:** mirror-only in 1.7.2" in markdown
    assert "Stage 4 replication emphasis" in markdown
    assert "Policy  : default [ca-policy-1.0; mirror_only; authoritative_release]" in explain
    assert "Policy Mode: mirror-only in 1.7.2" in explain
    assert "Stage 4 replication emphasis" in explain
    assert "Policy Surface: default (authoritative_release, mirror_only)" in html
    assert "Stage 4 replication emphasis" in html


def test_audit_repository_can_surface_selected_policy_metadata(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "Bioinformatics repository for viral genome analysis.\n")

    result = audit_repository(tmp_path, policy_name="strict_clinical_adjacency")
    calibration = result["calibration_profile"]

    assert calibration["policy_version"] == "ca-policy-1.0-strict-ca"
    assert calibration["profile_name"] == "strict_clinical_adjacency"
    assert calibration["profile_status"] == "experimental"


def test_load_calibration_profile_file_surfaces_hash_and_path(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.json"
    profile = load_calibration_profile("default")
    profile["profile_name"] = "external_profile_file"
    profile["profile_status"] = "preview_only"
    profile["policy_sha256"] = None
    profile.pop("policy_path", None)
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    loaded = load_calibration_profile_file(profile_path)

    assert loaded["profile_name"] == "external_profile_file"
    assert loaded["profile_status"] == "preview_only"
    assert loaded["policy_path"] == str(profile_path.resolve())
    assert isinstance(loaded["policy_sha256"], str)
    assert len(loaded["policy_sha256"]) == 64


def test_policy_list_cli_surfaces_available_profiles(capsys) -> None:
    code = cli_main(["policy", "list"])
    captured = capsys.readouterr()

    assert code == 0
    assert "STEM BIO-AI calibration profiles" in captured.out
    assert "- default: authoritative_release | mirror_only | ca-policy-1.0" in captured.out
    assert "- strict_clinical_adjacency: experimental | mirror_only | ca-policy-1.0-strict-ca" in captured.out
    assert set(available_policy_names()) >= {"default", "strict_clinical_adjacency"}


def test_policy_explain_cli_surfaces_profile_details(capsys) -> None:
    code = cli_main(["policy", "explain", "strict_clinical_adjacency"])
    captured = capsys.readouterr()

    assert code == 0
    assert "STEM BIO-AI policy: strict_clinical_adjacency" in captured.out
    assert "Scoring Effect: mirror-only in 1.7.2" in captured.out
    assert "Clinical Caps:  no_disclaimer_cap=60 | t0_hard_floor_cap=35" in captured.out
    assert "Default Diff:" in captured.out


def test_airi_registry_bundle_and_gap_scope_surface_in_scan_result(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "Bioinformatics repository for clinical trial biomarker analysis.\n"
        "Limitations are documented.\n",
    )
    _write(tmp_path / "requirements.txt", "numpy==1.26.4\n")

    result = audit_repository(tmp_path)
    coverage = result["airi_risk_coverage"]

    assert coverage["airi_registry_version"] == "stem-ai-airi-registry-v1"
    assert coverage["airi_bundle_version"] == "stem-ai-airi-runtime-bundle-v1"
    assert coverage["airi_mapping_version"] == "stem-ai-airi-detector-mapping-v1"
    assert coverage["airi_upstream_license"] == "MIT"
    assert coverage["total_risks_in_registry"] == 1595
    assert coverage["total_risks_in_bundle"] == 184

    in_bundle_ids = {item["id"] for item in coverage["known_gaps_in_bundle"]}
    outside_bundle_ids = {item["id"] for item in coverage["known_gaps_outside_bundle"]}

    assert "65.03.03" in in_bundle_ids
    assert "11.02.00" in outside_bundle_ids
    assert "72.04.02" in outside_bundle_ids


def test_cli_scan_accepts_named_policy_and_surfaces_it_in_output(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")
    out_dir = tmp_path / "results"

    code = cli_main([
        "scan",
        str(repo),
        "--policy", "strict_clinical_adjacency",
        "--format", "json",
        "--summary", "compact",
        "--output", str(out_dir),
    ])

    captured = capsys.readouterr()
    [json_path] = list(out_dir.glob("*_experiment_results.json"))
    result = json.loads(json_path.read_text(encoding="utf-8"))

    assert code == 0
    assert "Policy: strict_clinical_adjacency [experimental; mirror_only]" in captured.out
    assert "Policy Mode: mirror-only preview; scan scoring still follows authoritative runtime constants." in captured.out
    assert result["calibration_profile"]["profile_name"] == "strict_clinical_adjacency"


def test_cli_rejects_invalid_policy_name(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bio repository for molecular analysis.\n")

    try:
        cli_main(["scan", str(repo), "--policy", "not_a_profile"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected argparse SystemExit for invalid policy")


def test_policy_derive_returns_named_strict_profile_for_high_clinical_posture() -> None:
    derived = derive_policy_intent(
        {
            "clinical_strictness": 4,
            "code_integrity_priority": 3,
            "reproducibility_priority": 2,
            "structured_limitations_requirement": 3,
        }
    )

    assert derived["outcome_type"] == "named_profile"
    assert derived["recommended_profile"] == "strict_clinical_adjacency"


def test_policy_derive_returns_default_match_for_balanced_answers() -> None:
    derived = derive_policy_intent(
        {
            "clinical_strictness": 2,
            "code_integrity_priority": 3,
            "reproducibility_priority": 3,
            "structured_limitations_requirement": 2,
        }
    )

    assert derived["outcome_type"] == "default_match"
    assert derived["recommended_profile"] == "default"


def test_policy_derive_returns_preview_only_for_conflicting_strong_postures() -> None:
    derived = derive_policy_intent(
        {
            "clinical_strictness": 4,
            "code_integrity_priority": 4,
            "reproducibility_priority": 4,
            "structured_limitations_requirement": 4,
        }
    )

    assert derived["outcome_type"] == "preview_only"
    assert derived["recommended_profile"] == "preview_only"
    assert "clinical_policy" in derived["preview_only_deltas"]
    assert "weights" in derived["preview_only_deltas"]


def test_policy_simulation_can_reduce_score_via_stricter_clinical_cap() -> None:
    result = {
        "target": {"name": "demo/repo"},
        "classification": {
            "ca_severity": "CA-INDIRECT",
            "t0_hard_floor": False,
            "has_explicit_clinical_boundary": False,
        },
        "score": {
            "stage_1_readme_intent": 80,
            "stage_2_repo_local_consistency": 80,
            "stage_3_code_bio": 80,
            "risk_penalty": 0,
            "raw_score_before_floor": 80,
            "final_score": 69,
            "formal_tier": "T2 Caution",
        },
    }
    derived = derive_policy_intent(
        {
            "clinical_strictness": 4,
            "code_integrity_priority": 3,
            "reproducibility_priority": 2,
            "structured_limitations_requirement": 3,
        }
    )

    simulation = simulate_policy_outcome(result, derived)

    assert simulation["effective_profile"] == "strict_clinical_adjacency"
    assert simulation["score_cap"] == 60
    assert simulation["final_score"] == 60
    assert simulation["formal_tier"] == "T2 Caution"
    assert simulation["score_delta"] == -9


def test_policy_simulation_uses_profile_c1_penalty_when_c1_triggered(monkeypatch) -> None:
    result = {
        "target": {"name": "demo/repo"},
        "classification": {
            "ca_severity": "none",
            "t0_hard_floor": False,
            "has_explicit_clinical_boundary": True,
        },
        "score": {
            "stage_1_readme_intent": 80,
            "stage_2_repo_local_consistency": 70,
            "stage_3_code_bio": 90,
            "risk_penalty": 10,
            "raw_score_before_floor": 70,
            "final_score": 70,
            "formal_tier": "T3 Supervised",
        },
    }
    derived = {
        "outcome_type": "named_profile",
        "recommended_profile": "strict_clinical_adjacency",
        "preview_only_deltas": {},
        "notes": [],
    }
    baseline = load_calibration_profile("default")
    strict = load_calibration_profile("strict_clinical_adjacency")
    strict["code_integrity_policy"]["C1_penalty"] = 15

    def _fake_load(name: str = "default") -> dict:
        return baseline if name == "default" else strict

    monkeypatch.setattr("stem_ai.policy_intent.load_calibration_profile", _fake_load)

    simulation = simulate_policy_outcome(result, derived)

    assert simulation["raw_score_before_cap"] == 67
    assert simulation["raw_score_delta"] == -3


def test_policy_simulation_revalidates_preview_only_profile_after_deltas() -> None:
    result = {
        "target": {"name": "demo/repo"},
        "classification": {
            "ca_severity": "none",
            "t0_hard_floor": False,
            "has_explicit_clinical_boundary": True,
        },
        "score": {
            "stage_1_readme_intent": 80,
            "stage_2_repo_local_consistency": 80,
            "stage_3_code_bio": 80,
            "risk_penalty": 0,
            "raw_score_before_floor": 80,
            "final_score": 80,
            "formal_tier": "T3 Supervised",
        },
    }
    derived = {
        "outcome_type": "preview_only",
        "recommended_profile": "preview_only",
        "preview_only_deltas": {
            "weights": {
                "stage_1_percent": 70,
                "stage_2r_percent": 20,
                "stage_3_percent": 45,
            }
        },
        "notes": [],
    }

    try:
        simulate_policy_outcome(result, derived)
    except ValueError as exc:
        assert "sum to 100" in str(exc)
    else:
        raise AssertionError("Expected preview-only simulation to revalidate effective profile deltas")


def test_policy_derive_cli_surfaces_preview_only_deltas(capsys) -> None:
    code = cli_main([
        "policy",
        "derive",
        "--clinical-strictness", "4",
        "--code-integrity-priority", "4",
        "--reproducibility-priority", "4",
        "--structured-limitations-requirement", "4",
    ])
    captured = capsys.readouterr()

    assert code == 0
    assert "Outcome:       preview_only" in captured.out
    assert "Preview Deltas:" in captured.out
    assert "weights" in captured.out


def test_policy_simulate_cli_surfaces_score_delta_for_strict_profile(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    _write(
        repo / "README.md",
        "Bioinformatics repository for clinical trial biomarker analysis and medical imaging.\n"
        "Limitations are documented.\n"
    )
    _write(repo / "requirements.txt", "numpy==1.26.4\n")
    _write(repo / ".github" / "workflows" / "ci.yml", "name: test\n")
    _write(repo / "tests" / "test_domain.py", "def test_clinical_trial_variant_pipeline(): pass\n")
    _write(repo / "CHANGELOG.md", "# Changelog\n\n## v1.0.1\n- Fixed bug in pipeline.\n")

    code = cli_main([
        "policy",
        "simulate",
        str(repo),
        "--clinical-strictness", "4",
        "--code-integrity-priority", "3",
        "--reproducibility-priority", "2",
        "--structured-limitations-requirement", "3",
    ])
    captured = capsys.readouterr()

    assert code == 0
    assert "STEM BIO-AI policy simulation" in captured.out
    assert "Mode:          preview only; baseline scan scoring remains authoritative" in captured.out
    assert "Simulation:    strict_clinical_adjacency" in captured.out
    assert "Score Delta:" in captured.out


def test_policy_simulate_cli_accepts_local_profile_file(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    _write(
        repo / "README.md",
        "Bioinformatics repository for clinical trial biomarker analysis and medical imaging.\n"
        "Limitations are documented.\n"
    )
    _write(repo / "requirements.txt", "numpy==1.26.4\n")
    _write(repo / ".github" / "workflows" / "ci.yml", "name: test\n")
    _write(repo / "tests" / "test_domain.py", "def test_clinical_trial_variant_pipeline(): pass\n")
    _write(repo / "CHANGELOG.md", "# Changelog\n\n## v1.0.1\n- Fixed bug in pipeline.\n")

    profile_path = tmp_path / "reproducibility_first.json"
    profile = load_calibration_profile("default")
    profile["profile_name"] = "reproducibility_first"
    profile["policy_version"] = "ca-policy-1.0-repro-first"
    profile["profile_status"] = "experimental"
    profile["stage_4_policy"] = {"emphasis": "stronger_than_baseline"}
    profile["policy_sha256"] = None
    profile.pop("policy_path", None)
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    code = cli_main([
        "policy",
        "simulate",
        str(repo),
        "--profile-file", str(profile_path),
    ])
    captured = capsys.readouterr()

    assert code == 0
    assert "Simulation:    reproducibility_first [local_file]" in captured.out
    assert "Outcome Type:  external_profile_file" in captured.out
    assert "Profile Mode:  experimental | mirror_only | local_file" in captured.out
    assert "Profile File:" in captured.out
    assert "Profile Hash:" in captured.out
    assert "Replication:   baseline=baseline | simulation=stronger_than_baseline" in captured.out
    assert "Formal Score:  unchanged; Stage 4 remains a separate replication lane in 1.7.2" in captured.out


def test_policy_simulate_cli_rejects_mixing_profile_file_and_intent_answers(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "README.md", "Bioinformatics repository.\n")

    profile_path = tmp_path / "profile.json"
    profile = load_calibration_profile("default")
    profile["profile_name"] = "external_profile_file"
    profile["profile_status"] = "preview_only"
    profile["policy_sha256"] = None
    profile.pop("policy_path", None)
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    try:
        cli_main([
            "policy",
            "simulate",
            str(repo),
            "--profile-file", str(profile_path),
            "--clinical-strictness", "4",
            "--code-integrity-priority", "3",
            "--reproducibility-priority", "2",
            "--structured-limitations-requirement", "3",
        ])
    except SystemExit as exc:
        assert "Use either intent answers or --profile-file" in str(exc)
    else:
        raise AssertionError("Expected policy simulate to reject mixed profile-file and intent input")


def test_regulatory_basis_review_required_flips_when_registry_is_stale() -> None:
    basis = build_regulatory_basis(date(2026, 6, 1))

    assert basis["review_required"] is True
    assert "registry_as_of_stale" in basis["review_reasons"]


def test_fallback_citations_exclude_not_detected_and_absent_statuses() -> None:
    result = {
        "evidence_ledger": [
            {"finding_id": "A", "status": "not_detected", "severity": "info", "detector": "D1", "file": ".", "line": 0},
            {"finding_id": "B", "status": "absent", "severity": "info", "detector": "D2", "file": ".", "line": 0},
            {"finding_id": "C", "status": "detected", "severity": "warn", "detector": "D3", "file": ".", "line": 0},
            {"finding_id": "D", "status": "error", "severity": "error", "detector": "D4", "file": ".", "line": 0},
        ]
    }

    assert _fallback_citations(result) == ["D", "C"]

