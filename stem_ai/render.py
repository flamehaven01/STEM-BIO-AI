from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    _RL = True
except ImportError:
    _RL = False

# ── palette ───────────────────────────────────────────────────────────────────
_NAVY   = "#1B2A4A"
_TEAL   = "#2E86AB"
_PURPLE = "#6B4D8E"
_SLATE  = "#3D5A7A"
_GREEN  = "#27A560"
_AMBER  = "#C97B10"
_RED    = "#C0392B"
_ORANGE = "#C96010"
_LGRAY  = "#F5F7FA"
_MGRAY  = "#E2E8F0"
_DGRAY  = "#4A5568"
_WHITE  = "#FFFFFF"

_TIER_COLOR = {"T0": _RED, "T1": _RED, "T2": _ORANGE, "T3": _TEAL, "T4": _GREEN}
_STAGE_COLOR = [_TEAL, _PURPLE, _SLATE]

def _hx(h: str):
    return colors.HexColor(h)

def _tier_hex(tier: str) -> str:
    for k, v in _TIER_COLOR.items():
        if k in tier:
            return v
    return _DGRAY

def _status_hex(s: str) -> str:
    return {
        "PASS": _GREEN, "FAIL": _RED, "WARN": _AMBER,
    }.get(s.upper(), _DGRAY)


# ── public API ────────────────────────────────────────────────────────────────
def write_outputs(
    result: dict[str, Any], output_dir: Path, mode: str, pages: int, fmt: str
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(result["target"]["name"])
    created: list[Path] = []

    if fmt in {"json", "all"}:
        p = output_dir / f"{stem}_experiment_results.json"
        p.write_text(json.dumps(result, indent=2), encoding="utf-8")
        created.append(p)

    md = render_markdown(result, mode, pages)
    if fmt in {"md", "all"}:
        p = output_dir / f"{stem}_report.md"
        p.write_text(md, encoding="utf-8")
        created.append(p)

    if fmt in {"pdf", "all"}:
        p = output_dir / f"{stem}_{mode}_{pages}p.pdf"
        if _RL:
            _write_rl_pdf(p, result, mode, pages)
        else:
            write_simple_pdf(p, render_pdf_pages(result, mode, pages))
        created.append(p)

    return created


# ── markdown ──────────────────────────────────────────────────────────────────
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
        lines.append(f"- **{key}:** {item['status']} — {item['evidence'][0]}")

    lines.extend(["", "## Top Risks"])
    for risk in result["notable_risks"][:5]:
        lines.append(f"- {risk}")

    if mode == "detailed":
        lines.extend(["", "## Stage 2R Evidence"])
        for key, item in result["stage_2r_rubric"].items():
            if isinstance(item, dict):
                lines.append(f"- **{key}:** {item.get('score', '')} — {item.get('evidence', '')}")
        lines.extend(["", "## Stage 3 Evidence"])
        for key, item in result["stage_3_rubric"].items():
            lines.append(f"- **{key}:** {item['score']} / {item['max']} — {item['evidence']}")
        lines.extend(["", "## Method Boundary", result["method"]])

    lines.extend([
        "",
        "## Disclaimer",
        "This is a trustworthiness pre-screen, not clinical certification, "
        "regulatory clearance, or medical advice.",
    ])
    return "\n".join(lines) + "\n"


# ── reportlab PDF ─────────────────────────────────────────────────────────────
def _write_rl_pdf(path: Path, result: dict[str, Any], mode: str, pages: int) -> None:
    W, H = A4
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
    )
    story: list[Any] = []
    story += _header_block(result)
    story += _score_row(result)
    story.append(Spacer(1, 3 * mm))
    story += _stage_cards(result)
    story.append(Spacer(1, 3 * mm))
    story += _integrity_and_risks(result)

    if mode == "detailed":
        story += _detail_pages(result, pages)

    story += _footer_block()
    doc.build(story)


def _style(name="Normal", size=9, leading=12, color=_DGRAY, bold=False, align="LEFT") -> ParagraphStyle:
    return ParagraphStyle(
        name,
        fontSize=size,
        leading=leading,
        textColor=_hx(color),
        fontName="Helvetica-Bold" if bold else "Helvetica",
        alignment={"LEFT": 0, "CENTER": 1, "RIGHT": 2}.get(align, 0),
    )


def _header_block(result: dict[str, Any]) -> list[Any]:
    t = result["target"]
    commit = t.get("commit", "")[:12] or "—"
    branch = t.get("branch", "—")
    last_commit = t.get("last_commit_date", "—")[:10]
    audit_date = result.get("generated_at_local", "—")
    mode = result.get("execution_mode", "—")

    header_data = [[
        Paragraph(
            f'<font color="{_WHITE}"><b>STEM-AI Trustworthiness Audit v{result["stem_ai_version"]}</b></font>',
            _style("H", 14, 18, _WHITE, True, "LEFT"),
        ),
    ]]
    header_tbl = Table(header_data, colWidths=["100%"])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hx(_NAVY)),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))

    meta = (
        f'<font color="{_DGRAY}"><b>Repository:</b> {t["name"]} &nbsp;|&nbsp; '
        f'<b>&#x2713;</b> {commit} &nbsp;|&nbsp; '
        f'<b>Branch:</b> {branch} &nbsp;|&nbsp; '
        f'<b>Last commit:</b> {last_commit} &nbsp;|&nbsp; '
        f'<b>Audit Date:</b> {audit_date} &nbsp;|&nbsp; '
        f'<b>Mode:</b> {mode}</font>'
    )
    meta_data = [[Paragraph(meta, _style("M", 7.5, 11, _DGRAY))]]
    meta_tbl = Table(meta_data, colWidths=["100%"])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hx(_MGRAY)),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    return [header_tbl, meta_tbl, Spacer(1, 3 * mm)]


def _score_row(result: dict[str, Any]) -> list[Any]:
    score = result["score"]
    fs = score["final_score"]
    tier = score["formal_tier"]
    tier_hex = _tier_hex(tier)
    use_scope = score.get("use_scope", "")

    # Left: big score
    score_cell = [
        Paragraph(
            f'<font color="{_NAVY}" size="28"><b>{fs}</b></font>'
            f'<font color="{_DGRAY}" size="13"> / 100</font>',
            _style("SC", 28, 34, _NAVY, True, "CENTER"),
        ),
        Paragraph("Final Score", _style("SL", 8, 11, _DGRAY, False, "CENTER")),
    ]

    # Right: tier badge + use scope
    tier_badge = [[
        Paragraph(
            f'<font color="{_WHITE}"><b>{tier}</b></font>',
            _style("TB", 12, 16, _WHITE, True, "CENTER"),
        )
    ]]
    tier_tbl = Table(tier_badge, colWidths=[60 * mm])
    tier_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hx(tier_hex)),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROUNDEDCORNERS", [4]),
    ]))
    scope_cell = [
        tier_tbl,
        Spacer(1, 2 * mm),
        Paragraph(
            f'<font color="{_DGRAY}"><b>Use Scope:</b></font><br/>'
            f'<font color="{_DGRAY}" size="8">{use_scope}</font>',
            _style("US", 8, 11, _DGRAY),
        ),
    ]

    weight_note = (
        f'<font color="{_DGRAY}" size="7.5">Weighted model: '
        f'Stage 1 × 0.40 &nbsp;+&nbsp; Stage 2R × 0.20 &nbsp;+&nbsp; Stage 3 × 0.40 '
        f'− Risk Penalty = <b>{fs}</b></font>'
    )

    row_data = [[score_cell, scope_cell]]
    row_tbl = Table(row_data, colWidths=[50 * mm, None])
    row_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), _hx(_LGRAY)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
    ]))
    return [row_tbl, Spacer(1, 1 * mm), Paragraph(weight_note, _style("WN", 7.5, 10, _DGRAY))]


def _stage_cards(result: dict[str, Any]) -> list[Any]:
    score = result["score"]
    stages = [
        ("Stage 1", "README Intent", score["stage_1_readme_intent"], _TEAL),
        ("Stage 2R", "Repo-Local Consistency", score["stage_2_repo_local_consistency"], _PURPLE),
        ("Stage 3", "Code / Bio Responsibility", score["stage_3_code_bio"], _SLATE),
    ]
    cells = []
    for label, sub, val, col in stages:
        card = [
            [Paragraph(
                f'<font color="{_WHITE}"><b>{label}</b><br/><i>{sub}</i></font>',
                _style("CH", 8.5, 12, _WHITE, True, "CENTER"),
            )],
            [Paragraph(
                f'<font color="{col}" size="22"><b>{val}</b></font>'
                f'<font color="{_DGRAY}" size="9"> / 100</font>',
                _style("CV", 22, 26, col, True, "CENTER"),
            )],
        ]
        t = Table(card, colWidths=["100%"])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), _hx(col)),
            ("BACKGROUND", (0, 1), (0, 1), _hx(_LGRAY)),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
        ]))
        cells.append(t)

    row = Table([cells], colWidths=["33%", "33%", "34%"])
    row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    return [row]


def _integrity_and_risks(result: dict[str, Any]) -> list[Any]:
    ci = result["code_integrity"]
    risks = result["notable_risks"]
    positive = result.get("notable_positive_evidence", [])

    # Code integrity column
    ci_rows = [[
        Paragraph(f'<font color="{_WHITE}"><b>Code Integrity</b></font>', _style("CIH", 9, 12, _WHITE, True)),
    ]]
    for key, item in ci.items():
        s = item["status"]
        sc = _status_hex(s)
        ev = item["evidence"][0][:90] if item["evidence"] else ""
        badge = [[Paragraph(
            f'<font color="{_WHITE}" size="7"><b>{s}</b></font>',
            _style("B", 7, 9, _WHITE, True, "CENTER"),
        )]]
        bt = Table(badge, colWidths=[10 * mm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), _hx(sc)),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        short_key = key.replace("C1_hardcoded_credentials", "C1 Credentials") \
                       .replace("C2_dependency_pinning", "C2 Dependency Pinning") \
                       .replace("C3_dead_or_deprecated_patient_adjacent_paths", "C3 Dead Paths") \
                       .replace("C4_exception_handling_clinical_adjacent_paths", "C4 Exception Handling")
        ci_rows.append([
            [bt, Paragraph(f'<font color="{_DGRAY}" size="8"><b>{short_key}</b><br/>{ev}</font>',
                           _style("CI", 7.5, 10, _DGRAY))],
        ])

    ci_tbl = Table(ci_rows, colWidths=["100%"])
    ci_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), _hx(_NAVY)),
        ("BACKGROUND", (0, 1), (0, -1), _hx(_LGRAY)),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_hx(_LGRAY), _hx(_WHITE)]),
    ]))

    # Risks + positive column
    risk_lines = "".join(f'&#8226; {r[:110]}<br/>' for r in risks[:4])
    pos_lines  = "".join(f'&#8226; {p[:110]}<br/>' for p in positive[:3])
    right_rows = [
        [Paragraph(f'<font color="{_WHITE}"><b>Remediation Targets</b></font>', _style("RH", 9, 12, _WHITE, True))],
        [Paragraph(f'<font color="{_DGRAY}" size="8">{risk_lines}</font>', _style("RL", 8, 11, _DGRAY))],
        [Paragraph(f'<font color="{_WHITE}"><b>Positive Evidence</b></font>', _style("PH", 9, 12, _WHITE, True))],
        [Paragraph(f'<font color="{_DGRAY}" size="8">{pos_lines}</font>', _style("PL", 8, 11, _DGRAY))],
    ]
    right_tbl = Table(right_rows, colWidths=["100%"])
    right_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), _hx(_RED)),
        ("BACKGROUND", (0, 1), (0, 1), _hx(_LGRAY)),
        ("BACKGROUND", (0, 2), (0, 2), _hx(_GREEN)),
        ("BACKGROUND", (0, 3), (0, 3), _hx(_WHITE)),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
    ]))

    two_col = Table([[ci_tbl, right_tbl]], colWidths=["48%", "52%"])
    two_col.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [two_col]


def _detail_pages(result: dict[str, Any], pages: int) -> list[Any]:
    story: list[Any] = [Spacer(1, 5 * mm)]
    score = result["score"]

    story.append(HRFlowable(width="100%", thickness=0.5, color=_hx(_MGRAY)))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Stage 2R — Repo-Local Consistency", _style("S2H", 11, 15, _NAVY, True)))
    story.append(Spacer(1, 2 * mm))
    for key, item in result["stage_2r_rubric"].items():
        if isinstance(item, dict):
            s = item.get("score", "")
            ev = item.get("evidence", "")
            story.append(Paragraph(
                f'<b>{key}</b>: <font color="{_TEAL}">{s}</font> — {ev}',
                _style("S2R", 8, 11, _DGRAY),
            ))
            story.append(Spacer(1, 1 * mm))

    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Stage 3 — Code / Bio Responsibility", _style("S3H", 11, 15, _NAVY, True)))
    story.append(Spacer(1, 2 * mm))
    for key, item in result["stage_3_rubric"].items():
        sc = item["score"]
        mx = item["max"]
        ev = item["evidence"]
        color = _GREEN if sc == mx else (_AMBER if sc > 0 else _RED)
        story.append(Paragraph(
            f'<b>{key}</b>: <font color="{color}"><b>{sc} / {mx}</b></font> — {ev}',
            _style("S3R", 8, 11, _DGRAY),
        ))
        story.append(Spacer(1, 1 * mm))

    if pages >= 5:
        story.append(Spacer(1, 3 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=_hx(_MGRAY)))
        story.append(Paragraph("Method Boundary", _style("MBH", 11, 15, _NAVY, True)))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(result["method"], _style("MB", 8, 11, _DGRAY)))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            "Runtime tests are not implied unless explicitly recorded in the result JSON.",
            _style("MBN", 8, 11, _AMBER),
        ))
    return story


def _footer_block() -> list[Any]:
    return [
        Spacer(1, 4 * mm),
        HRFlowable(width="100%", thickness=0.5, color=_hx(_MGRAY)),
        Spacer(1, 1.5 * mm),
        Paragraph(
            f'<font color="{_DGRAY}" size="7">Independent audit summary — STEM-AI v1.1.2 &nbsp;|&nbsp; '
            "Not clinical certification. Not regulatory clearance. Not medical advice.</font>",
            _style("FT", 7, 9, _DGRAY, False, "CENTER"),
        ),
    ]


# ── plain-text PDF fallback (no reportlab) ───────────────────────────────────
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
        *[f"- {k}: {v['status']}" for k, v in result["code_integrity"].items()],
        "",
        "Top Risks",
        *[f"- {r}" for r in result["notable_risks"][:4]],
        "",
        "Not clinical certification. Not regulatory clearance. Not medical advice.",
    ]
    if mode == "brief":
        return [_fit_page(brief)]
    p2 = _fit_page(["Stage 2R Evidence", *[
        f"- {k}: {v.get('score','')} {v.get('evidence','')}"
        for k, v in result["stage_2r_rubric"].items() if isinstance(v, dict)
    ]])
    p3 = _fit_page(["Stage 3 Evidence", *[
        f"- {k}: {v['score']} / {v['max']} {v['evidence']}"
        for k, v in result["stage_3_rubric"].items()
    ]])
    sets = [_fit_page(brief), p2, p3]
    if pages == 5:
        sets.append(_fit_page(["Code Integrity", *[f"- {k}: {v['status']} {v['evidence'][0]}" for k, v in result["code_integrity"].items()]]))
        sets.append(_fit_page(["Method Boundary", result["method"]]))
    return sets[:pages]


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
        pid = add(
            f"<< /Type /Page /Parent {pages_id_placeholder} 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_ids[idx]} 0 R >>"
        )
        page_ids[idx] = pid
        kids.append(f"{pid} 0 R")

    pages_id = add(f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(page_ids)} >>")
    if pages_id != pages_id_placeholder:
        for idx, pid in enumerate(page_ids):
            objects[pid - 1] = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_ids[idx]} 0 R >>"
            ).encode("latin-1", errors="replace")
    catalog_id = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{idx} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(out)


def _page_stream(lines: list[str]) -> str:
    y = 800
    chunks = ["BT", "/F1 11 Tf", "50 800 Td"]
    first = True
    for line in lines:
        for wrapped in textwrap.wrap(_ascii(line), width=88) or [""]:
            if not first:
                chunks.append("0 -16 Td")
                y -= 16
            first = False
            chunks.append(f"({_escape_pdf(wrapped)}) Tj")
            if y < 60:
                break
    chunks.append("ET")
    return "\n".join(chunks)


def _fit_page(lines: list[str], max_lines: int = 44) -> list[str]:
    fitted: list[str] = []
    for line in lines:
        fitted.extend(textwrap.wrap(_ascii(line), width=88) or [""])
        if len(fitted) >= max_lines:
            return fitted[:max_lines]
    return fitted


def _escape_pdf(t: str) -> str:
    return t.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _ascii(t: str) -> str:
    return t.encode("latin-1", errors="replace").decode("latin-1")


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "stem_audit"
