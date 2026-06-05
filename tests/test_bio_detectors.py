from __future__ import annotations

from pathlib import Path

import pytest

from stem_ai.render import render_explain, render_markdown
from stem_ai.scanner import audit_repository

from tests.helpers import write_text


def test_bio_smiles_surface_detector_flags_malformed_and_placeholder_strings(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(tmp_path / "build" / "lib" / "generated.py", "bad_smiles_ring = 'C1CC'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_surface_integrity"]

    assert any(f["status"] == "not_detected" for f in findings)
    assert not any(f["status"] == "detected" for f in findings)


def test_bio_smiles_rdkit_validation_is_not_applicable_without_rdkit(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    monkeypatch.setattr(detector_bio, "_rdkit_mol_from_smiles", lambda smiles: detector_bio._RDKIT_UNAVAILABLE)
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(tmp_path / "pipeline.py", "bad_smiles = 'C1CC'\n")

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
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(tmp_path / "pipeline.py", "bad_smiles = 'C1CC'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_rdkit_validation" and f["status"] == "detected"]

    assert findings
    assert findings[0]["metadata"]["smiles_text"] == "C1CC"


def test_bio_smiles_rdkit_validation_reports_not_detected_when_available_and_valid(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    monkeypatch.setattr(detector_bio, "_rdkit_is_available", lambda: True)
    monkeypatch.setattr(detector_bio, "_rdkit_mol_from_smiles", lambda smiles: object())
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(tmp_path / "pipeline.py", "candidate_smiles = 'CC(=O)O'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_rdkit_validation"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_smiles_rdkit_validation_reports_not_detected_when_available_without_candidates(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    monkeypatch.setattr(detector_bio, "_rdkit_is_available", lambda: True)
    monkeypatch.setattr(detector_bio, "_rdkit_mol_from_smiles", lambda smiles: object())
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(tmp_path / "pipeline.py", "PRIMARY = '#8b949e'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_rdkit_validation"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_smiles_rdkit_validation_skips_availability_check_without_candidates(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    def fail_if_called():
        raise AssertionError("_rdkit_is_available should not run when there are no SMILES candidates")

    monkeypatch.setattr(detector_bio, "_rdkit_is_available", fail_if_called)
    monkeypatch.setattr(detector_bio, "_rdkit_mol_from_smiles", lambda smiles: object())
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(tmp_path / "pipeline.py", "PRIMARY = '#8b949e'\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_smiles_rdkit_validation"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_ast_context_cache_avoids_reparsing_same_file(monkeypatch, tmp_path: Path) -> None:
    import stem_ai.detector_bio as detector_bio

    detector_bio._build_ast_context_cached.cache_clear()
    write_text(tmp_path / "pipeline.py", "candidate_smiles = 'CC(=O)O'\n")
    path = tmp_path / "pipeline.py"
    calls = {"count": 0}
    original_parse = detector_bio.ast.parse

    def counted_parse(*args, **kwargs):
        calls["count"] += 1
        return original_parse(*args, **kwargs)

    monkeypatch.setattr(detector_bio.ast, "parse", counted_parse)

    list(detector_bio._iter_ast_code_contexts([path]))
    list(detector_bio._iter_ast_code_contexts([path]))

    assert calls["count"] == 1


def test_bio_smiles_parser_guard_flags_missing_none_check(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for molecular generation.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for immunology analysis.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for immunology analysis.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for immunology analysis.\n")
    write_text(
        tmp_path / "tests" / "test_mock.py",
        "try:\n"
        "    import rdkit\n"
        "except ImportError:\n"
        "    USE_MOCK = True\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_silent_mock_fallback"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_detectors_ignore_manual_verify_paths(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for immunology analysis.\n")
    write_text(
        tmp_path / ".manual_verify" / "trial.py",
        "import os\n"
        "os.system('blastn sample.fa')\n",
    )
    write_text(
        tmp_path / ".manual_verify" / "audit_trace.md",
        "decision_event: override\n",
    )

    result = audit_repository(tmp_path)
    run_findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_run_trace"]
    trace_findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_trace_manifest"]

    assert any(f["status"] == "not_detected" for f in run_findings)
    assert any(f["status"] == "not_detected" for f in trace_findings)


def test_bio_trace_manifest_detector_flags_traceability_files_and_keywords(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for traceable molecular analysis.\n")
    write_text(
        tmp_path / "audit_log_schema.json",
        "{\n"
        '  "decision_event": true,\n'
        '  "model_version": "v1",\n'
        '  "input_hash": "abc",\n'
        '  "output_hash": "def"\n'
        "}\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_trace_manifest" and f["status"] == "detected"]

    assert findings
    assert any(f["pattern_id"] == "bio_trace_manifest_file_v1" for f in findings)
    assert any(f.get("metadata", {}).get("matched_term") == "decision_event" for f in findings)


def test_bio_trace_manifest_detector_flags_keywords_in_docs(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for traceable molecular analysis.\n")
    write_text(
        tmp_path / "docs" / "traceability.md",
        "# Traceability\n"
        "Each override_event stores operator_id, timestamp, and dataset_hash.\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_trace_manifest" and f["status"] == "detected"]

    assert findings
    matched_terms = {f.get("metadata", {}).get("matched_term") for f in findings if "metadata" in f}
    assert "override_event" in matched_terms


def test_bio_trace_manifest_detector_still_detects_non_generated_trace_surface(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for traceable molecular analysis.\n")
    write_text(
        tmp_path / "traceability" / "audit_trace.md",
        "decision_event: override\n"
        "timestamp: 2026-05-17\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_trace_manifest" and f["status"] == "detected"]

    assert findings
    assert any(f["pattern_id"] == "bio_trace_manifest_keyword_v1" for f in findings)


def test_bio_trace_manifest_detector_reports_not_detected_when_absent(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    write_text(tmp_path / "pipeline.py", "def run():\n    return 1\n")

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_trace_manifest"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_run_trace_flags_shell_true_with_tainted_bio_tool_command(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    write_text(
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
    write_text(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    write_text(
        tmp_path / "pipeline.py",
        "import subprocess\n"
        "def run():\n"
        "    subprocess.run(['bedtools', 'intersect', '-a', 'a.bed', '-b', 'b.bed'], timeout=30)\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_run_trace"]

    assert any(f["status"] == "not_detected" for f in findings)


def test_bio_run_trace_flags_os_system_for_known_bio_tool(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for sequence analysis.\n")
    write_text(
        tmp_path / "pipeline.py",
        "import os\n"
        "def run(sample_path):\n"
        "    os.system('minimap2 ' + sample_path)\n",
    )

    result = audit_repository(tmp_path)
    findings = [f for f in result["evidence_ledger"] if f["detector"] == "BIO_run_trace" and f["status"] == "detected"]

    assert findings
    assert any(f["metadata"]["call_name"] == "os.system" and f["severity"] == "warn" for f in findings)


def test_bio_detectors_surface_in_markdown_and_explain(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    write_text(
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


def test_bio_markdown_uses_scope_specific_note_when_detector_not_detected(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, mode="brief", pages=1)

    assert "No malformed or suspicious SMILES-like strings detected by conservative surface checks." in markdown
