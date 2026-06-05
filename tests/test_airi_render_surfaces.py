from __future__ import annotations

import json
from pathlib import Path

from stem_ai.render import render_explain, render_markdown, render_pdf_pages, write_outputs
from stem_ai.render_html import render_html
from stem_ai.render_html_components import airi_row
from stem_ai.scanner import audit_repository

from tests.helpers import write_text


def test_html_compacts_repeated_info_evidence_rows(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    write_text(
        tmp_path / "tests" / "test_domain.py",
        "def test_alpha():\n    assert 'genomics' == 'genomics'\n"
        "def test_beta():\n    assert 'proteomics' == 'proteomics'\n"
        "def test_gamma():\n    assert 'clinical' == 'clinical'\n",
    )

    result = audit_repository(tmp_path)
    html = render_html(result)

    assert "compact rows" in html


def test_markdown_and_explain_note_compacted_narrative_surfaces(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path)
    markdown = render_markdown(result, "brief", 1)
    explain = render_explain(result)

    assert "Surface Note" in markdown
    assert "Surface : repeated same-file evidence may be compacted in narrative output" in explain


def test_explain_compacts_repeated_info_findings(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bioinformatics repository for viral sequencing.\n")
    write_text(
        tmp_path / "tests" / "test_domain.py",
        "def test_alpha():\n    assert 'genomics' == 'genomics'\n"
        "def test_beta():\n    assert 'proteomics' == 'proteomics'\n"
        "def test_gamma():\n    assert 'clinical' == 'clinical'\n",
    )

    result = audit_repository(tmp_path)
    explain = render_explain(result)

    assert "compacted to" in explain


def test_json_and_pdf_surface_notes_preserve_canonical_boundary(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular analysis.\n")

    result = audit_repository(tmp_path)
    out_dir = tmp_path / "out"
    write_outputs(result, out_dir, mode="brief", pages=1, fmt="json", explain=False)
    payload = json.loads((out_dir / f"{tmp_path.name}_experiment_results.json").read_text(encoding="utf-8"))

    notes = payload.get("artifact_surface_notes", {})
    assert notes.get("json", "").startswith("JSON remains the canonical full-fidelity artifact")
    assert "compact repeated same-file evidence" in notes.get("human_readable_compaction", "")

    pdf_pages = render_pdf_pages(result, mode="detailed", pages=7)
    flat_lines = "\n".join("\n".join(page) for page in pdf_pages)
    assert "Surface Note:" in flat_lines


def test_tier_lock_ca_cap_surfaces_in_markdown(tmp_path: Path) -> None:
    write_text(
        tmp_path / "README.md",
        "Scientific skills catalog.\n"
        "Includes AutoDock Vina drug docking, nnU-Net medical imaging, pydicom, "
        "biomarker survival analysis, and clinical trial examples.\n",
    )
    result = audit_repository(tmp_path)
    assert result["classification"]["score_cap"] == 69
    markdown = render_markdown(result, mode="detailed", pages=7)
    assert "Tier Lock [CA-CAP]" in markdown
    assert "Score ceiling active at **69**" in markdown
    assert "Classification Applied:" in markdown
    assert "score_cap=69" in markdown
    assert "t0_floor=clear" in markdown


def test_tier_lock_t0_floor_surfaces_in_markdown(tmp_path: Path) -> None:
    write_text(
        tmp_path / "README.md",
        "Autonomous diagnosis tool for clinical triage decisions.\n",
    )
    result = audit_repository(tmp_path)
    assert result["classification"]["t0_hard_floor"] is True
    assert result["classification"]["score_cap"] == 39
    markdown = render_markdown(result, mode="detailed", pages=7)
    assert "Tier Lock [T0-FLOOR]" in markdown
    assert "Score ceiling active at **39**" in markdown
    assert "t0_floor=active" in markdown


def test_stage3_normalization_formula_in_markdown(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    write_text(tmp_path / ".github" / "workflows" / "ci.yml", "name: CI\n")
    result = audit_repository(tmp_path)
    s3_rubric = result.get("stage_3_rubric", {})
    raw_entry = s3_rubric.get("stage_3_raw_total", {})
    assert raw_entry.get("max") == 80
    markdown = render_markdown(result, mode="detailed", pages=7)
    assert "(raw: " in markdown
    assert "/80)" in markdown


def test_airi_gaps_count_suffix_in_markdown_when_over_five(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    result = audit_repository(tmp_path)
    result["airi_risk_coverage"]["known_gaps_in_bundle"] = [
        {"id": f"99.0{i}.00", "title": f"Synthetic gap {i}"} for i in range(8)
    ]
    markdown = render_markdown(result, mode="detailed", pages=7)
    assert "Known Gaps In Bundle" in markdown
    for i in range(8):
        assert f"99.0{i}.00" in markdown


def test_airi_html_row_component_surfaces_explicit_compacting_for_secondary_detectors() -> None:
    html = airi_row(
        {
            "id": "24.01.03",
            "title": "Synthetic AIRI trigger",
            "primary_detector_id": "C5_compliance_boundary_integrity",
            "secondary_detector_ids": [f"DET_{i}" for i in range(7)],
            "mapping_details": [
                {
                    "detector_id": f"DET_{i}",
                    "trigger_reason": f"trigger {i}",
                    "mapping_justification": f"why {i}",
                }
                for i in range(7)
            ],
        },
        "covered",
    )
    assert "(+2 more)" in html
    assert "(+2 more mapping details)" in html


def test_airi_pdf_surfaces_explicit_compacting_for_secondary_detectors(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "Bio repository for molecular analysis.\n")
    result = audit_repository(tmp_path)
    result["airi_risk_coverage"]["covered_risks"] = [
        {
            "id": "24.01.03",
            "title": "Synthetic AIRI trigger",
            "primary_detector_id": "C5_compliance_boundary_integrity",
            "secondary_detector_ids": [f"DET_{i}" for i in range(7)],
            "mapping_details": [
                {
                    "detector_id": f"DET_{i}",
                    "trigger_reason": f"trigger {i}",
                    "mapping_justification": f"why {i}",
                }
                for i in range(7)
            ],
        }
    ]
    pdf_pages = render_pdf_pages(result, mode="detailed", pages=7)
    flat = "\n".join("\n".join(page) for page in pdf_pages)
    assert "(+2 more)" in flat
