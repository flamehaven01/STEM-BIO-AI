from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any


def write_outputs(result: dict[str, Any], output_dir: Path, mode: str, pages: int, fmt: str) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(result["target"]["name"])
    created: list[Path] = []

    if fmt in {"json", "all"}:
        json_path = output_dir / f"{stem}_experiment_results.json"
        json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        created.append(json_path)

    markdown = render_markdown(result, mode, pages)
    if fmt in {"md", "all"}:
        md_path = output_dir / f"{stem}_report.md"
        md_path.write_text(markdown, encoding="utf-8")
        created.append(md_path)

    if fmt in {"pdf", "all"}:
        pdf_path = output_dir / f"{stem}_{mode}_{pages}p.pdf"
        write_simple_pdf(pdf_path, render_pdf_pages(result, mode, pages))
        created.append(pdf_path)

    return created


def render_markdown(result: dict[str, Any], mode: str, pages: int) -> str:
    score = result["score"]
    lines = [
        "# STEM-AI Local Audit Report",
        "",
        f"**Target:** `{result['target']['name']}`",
        f"**Execution Mode:** `{result['execution_mode']}`",
        f"**Final Score:** **{score['final_score']} / 100**",
        f"**Formal Tier:** **{score['formal_tier']}**",
        f"**Use Scope:** {score['use_scope']}",
        "",
        "## Score Matrix",
        "",
        "| Stage | Weight | Score |",
        "| --- | ---: | ---: |",
        f"| Stage 1 README Intent | 0.40 | {score['stage_1_readme_intent']} |",
        f"| Stage 2R Repo-Local Consistency | 0.20 | {score['stage_2_repo_local_consistency']} |",
        f"| Stage 3 Code/Bio Responsibility | 0.40 | {score['stage_3_code_bio']} |",
        f"| Risk Penalty | -- | {score['risk_penalty']} |",
        "",
        "## Code Integrity",
    ]
    for key, item in result["code_integrity"].items():
        lines.append(f"- **{key}:** {item['status']} -- {item['evidence'][0]}")

    lines.extend(["", "## Top Risks"])
    for risk in result["notable_risks"][:5]:
        lines.append(f"- {risk}")

    if mode == "detailed":
        lines.extend(["", "## Stage 2R Evidence"])
        for key, item in result["stage_2r_rubric"].items():
            if isinstance(item, dict):
                lines.append(f"- **{key}:** {item.get('score', '')} -- {item.get('evidence', '')}")
        lines.extend(["", "## Stage 3 Evidence"])
        for key, item in result["stage_3_rubric"].items():
            lines.append(f"- **{key}:** {item['score']} / {item['max']} -- {item['evidence']}")
        lines.extend(["", "## Method Boundary", result["method"]])

    lines.extend(
        [
            "",
            "## Disclaimer",
            "This is a trustworthiness pre-screen, not clinical certification, regulatory clearance, or medical advice.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_pdf_pages(result: dict[str, Any], mode: str, pages: int) -> list[list[str]]:
    score = result["score"]
    brief = [
        "STEM-AI Local Audit Brief",
        f"Target: {result['target']['name']}",
        f"Final Score: {score['final_score']} / 100",
        f"Formal Tier: {score['formal_tier']}",
        f"Use Scope: {score['use_scope']}",
        "",
        "Stage Scores",
        f"- Stage 1 README Intent: {score['stage_1_readme_intent']} / 100",
        f"- Stage 2R Repo-Local Consistency: {score['stage_2_repo_local_consistency']} / 100",
        f"- Stage 3 Code/Bio Responsibility: {score['stage_3_code_bio']} / 100",
        "",
        "Code Integrity",
        *[f"- {key}: {item['status']}" for key, item in result["code_integrity"].items()],
        "",
        "Top Risks",
        *[f"- {risk}" for risk in result["notable_risks"][:4]],
        "",
        "Not clinical certification. Not regulatory clearance. Not medical advice.",
    ]
    if mode == "brief":
        return [_fit_page(brief)]

    page_sets = [_fit_page(brief)]
    page_sets.append(
        _fit_page(
            [
                "Stage 2R Repo-Local Consistency",
                f"Score: {score['stage_2_repo_local_consistency']} / 100",
                "",
                *[
                    f"- {key}: {item.get('score', '')} {item.get('evidence', '')}"
                    for key, item in result["stage_2r_rubric"].items()
                    if isinstance(item, dict)
                ],
            ]
        )
    )
    page_sets.append(
        _fit_page(
            [
                "Stage 3 Code/Bio Responsibility",
                f"Score: {score['stage_3_code_bio']} / 100",
                "",
                *[
                    f"- {key}: {item['score']} / {item['max']} {item['evidence']}"
                    for key, item in result["stage_3_rubric"].items()
                ],
            ]
        )
    )
    if pages == 5:
        page_sets.append(_fit_page(["Code Integrity", *[f"- {key}: {item['status']} {item['evidence'][0]}" for key, item in result["code_integrity"].items()]]))
        page_sets.append(_fit_page(["Method Boundary", result["method"], "", "Runtime tests are not implied unless explicitly recorded in the result JSON."]))
    return page_sets[:pages]


def write_simple_pdf(path: Path, pages: list[list[str]]) -> None:
    objects: list[bytes] = []

    def add(obj: str) -> int:
        objects.append(obj.encode("latin-1", errors="replace"))
        return len(objects)

    font_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []
    content_ids: list[int] = []
    for page in pages:
        stream = _page_stream(page)
        content_ids.append(add(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream"))
        page_ids.append(0)

    kids = []
    pages_id_placeholder = len(objects) + len(pages) + 1
    for idx, _ in enumerate(pages):
        page_id = add(
            f"<< /Type /Page /Parent {pages_id_placeholder} 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_ids[idx]} 0 R >>"
        )
        page_ids[idx] = page_id
        kids.append(f"{page_id} 0 R")

    pages_id = add(f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(page_ids)} >>")
    if pages_id != pages_id_placeholder:
        # Rebuild page objects with correct parent if object count assumptions changed.
        for idx, page_id in enumerate(page_ids):
            objects[page_id - 1] = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_ids[idx]} 0 R >>"
            ).encode("latin-1", errors="replace")
    catalog_id = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{idx} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(output)


def _page_stream(lines: list[str]) -> str:
    y = 800
    chunks = ["BT", "/F1 11 Tf", "50 800 Td"]
    first = True
    for line in lines:
        for wrapped in textwrap.wrap(_ascii(line), width=88) or [""]:
            if first:
                first = False
            else:
                chunks.append("0 -16 Td")
                y -= 16
            chunks.append(f"({_escape_pdf(wrapped)}) Tj")
            if y < 60:
                break
    chunks.append("ET")
    return "\n".join(chunks)


def _fit_page(lines: list[str], max_lines: int = 44) -> list[str]:
    fitted: list[str] = []
    for line in lines:
        wrapped = textwrap.wrap(_ascii(line), width=88) or [""]
        fitted.extend(wrapped)
        if len(fitted) >= max_lines:
            return fitted[:max_lines]
    return fitted


def _escape_pdf(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _ascii(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "stem_audit"

