from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any

from . import __version__

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        PageBreak,
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

def _hx(h: str) -> Any:
    return colors.HexColor(h)

def _tier_hex(tier: str) -> str:
    for k, v in _TIER_COLOR.items():
        if k in tier:
            return v
    return _DGRAY

def _status_hex(s: str) -> str:
    return {"PASS": _GREEN, "FAIL": _RED, "WARN": _AMBER}.get(s.upper(), _DGRAY)

def _xt(t: str) -> str:
    """Escape text for use in reportlab XML markup."""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _clip_words(text: str, limit: int) -> str:
    """Trim table text without cutting through a word."""
    value = " ".join(str(text).split())
    if len(value) <= limit:
        return value
    trimmed = value[: max(0, limit - 1)].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{trimmed}..."


# ── public API ────────────────────────────────────────────────────────────────
def write_outputs(
    result: dict[str, Any],
    output_dir: Path,
    mode: str,
    pages: int,
    fmt: str,
    explain: bool = False,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_name(result["target"]["name"])
    created: list[Path] = []

    if fmt in {"json", "all"}:
        p = output_dir / f"{stem}_experiment_results.json"
        p.write_text(json.dumps(result, indent=2), encoding="utf-8")
        created.append(p)

    if "ai_advisory_input" in result:
        p = output_dir / f"{stem}_advisory_input.json"
        p.write_text(json.dumps(result["ai_advisory_input"], indent=2), encoding="utf-8")
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

    if explain:
        p = output_dir / f"{stem}_explain.txt"
        p.write_text(render_explain(result), encoding="utf-8")
        created.append(p)

    return created


# ── markdown ──────────────────────────────────────────────────────────────────
def render_markdown(result: dict[str, Any], mode: str, pages: int) -> str:
    score = result["score"]
    lines = [
        "# STEM BIO-AI Local Audit Report",
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
        f"| Stage 1 README Evidence Signal | 0.40 | {score['stage_1_readme_intent']} |",
        f"| Stage 2R Repo-Local Consistency | 0.20 | {score['stage_2_repo_local_consistency']} |",
        f"| Stage 3 Code/Bio Responsibility | 0.40 | {score['stage_3_code_bio']} |",
        f"| Risk Penalty | -- | {score['risk_penalty']} |",
        "",
        "## Replication Evidence Lane",
        "",
        f"**Stage 4 Replication Score:** **{result.get('replication_score', 0)} / 100**",
        f"**Replication Tier:** **{result.get('replication_tier', 'R0')}**",
        "",
        "## Reasoning Diagnostics",
        "",
        _markdown_reasoning_summary(result.get("reasoning_model", {})),
        "",
        *_markdown_advisory_section(result.get("ai_advisory")),
        "## Code Integrity",
    ]
    for key, item in result["code_integrity"].items():
        lines.append(f"- **{key}:** {item['status']} — {item['evidence'][0]}")

    lines.extend(["", "## Top Risks"])
    for risk in result["notable_risks"][:5]:
        lines.append(f"- {risk}")

    if mode == "detailed":
        lines.extend(["", "## Stage 1 Evidence"])
        for key, item in result.get("stage_1_rubric", {}).items():
            if isinstance(item, dict):
                score_value = item.get("score", "")
                lines.append(f"- **{key}:** {score_value} — {item.get('evidence', '')}")
        lines.extend(["", "## Stage 2R Evidence"])
        for key, item in result["stage_2r_rubric"].items():
            if isinstance(item, dict):
                lines.append(f"- **{key}:** {item.get('score', '')} — {item.get('evidence', '')}")
        lines.extend(["", "## Stage 3 Evidence"])
        for key, item in result["stage_3_rubric"].items():
            lines.append(f"- **{key}:** {item['score']} / {item['max']} — {item['evidence']}")
        lines.extend(["", "## Stage 4 Replication Evidence"])
        for key, item in result.get("stage_4_rubric", {}).items():
            lines.append(f"- **{key}:** {item['score']} / {item['max']} — {item['evidence']}")
        lines.extend(["", "## Method Boundary", result["method"]])

    lines.extend([
        "",
        "## Disclaimer",
        "This is an evidence-surface pre-screen, not clinical certification, "
        "regulatory clearance, or medical advice.",
    ])
    return "\n".join(lines) + "\n"


# ── explain text report ───────────────────────────────────────────────────────
_EXPLAIN_SEP = "=" * 72
_EXPLAIN_META_SKIP = frozenset({"file_count", "max_ast_files", "max_file_size_bytes"})


def render_explain(result: dict[str, Any]) -> str:
    """Return a human-readable plain-text explain report grouped by detector."""
    ledger: list[dict[str, Any]] = result.get("evidence_ledger", [])
    score = result["score"]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for finding in ledger:
        grouped.setdefault(finding["detector"], []).append(finding)

    out: list[str] = [
        "STEM BIO-AI Explain Report",
        f"Target  : {result['target']['name']}",
        f"Score   : {score['final_score']} / 100  ({score['formal_tier']})",
        f"Replic  : {result.get('replication_score', 0)} / 100"
        f"  ({result.get('replication_tier', 'R0')})",
        _EXPLAIN_SEP, "",
    ]
    for detector, findings in grouped.items():
        out += _explain_detector_group(detector, findings)
    out += _explain_ast_section(result.get("ast_signal_summary", {}))
    out += _explain_s4_section(result.get("stage_4_rubric", {}))
    out += _explain_reasoning_section(result.get("reasoning_model", {}))
    out += _explain_advisory_section(result.get("ai_advisory"))
    out += [_EXPLAIN_SEP,
            "DISCLAIMER: Evidence-surface pre-screen only.",
            "Not clinical certification, regulatory clearance, or medical advice."]
    return "\n".join(out) + "\n"


def _markdown_reasoning_summary(reasoning: dict[str, Any]) -> str:
    if not reasoning:
        return "Reasoning diagnostics are not available."
    coherence = reasoning.get("lane_coherence", {})
    uncertainty = reasoning.get("uncertainty_budget", {})
    gate = reasoning.get("evidence_risk_gate", {})
    envelope = reasoning.get("confidence_envelope", {})
    return (
        f"Diagnostic-only model `{reasoning.get('version', 'unknown')}`; "
        f"lane coherence `{coherence.get('status', 'unknown')}` "
        f"({coherence.get('overall', 'n/a')}), "
        f"uncertainty `{uncertainty.get('status', 'unknown')}` "
        f"({uncertainty.get('uncertainty', 'n/a')}), "
        f"risk gate `{gate.get('status', 'unknown')}` "
        f"({gate.get('evidence_risk', 'n/a')}), "
        f"confidence envelope {envelope.get('lower', 'n/a')}-"
        f"{envelope.get('upper', 'n/a')}. "
        "This diagnostic layer does not override the final score."
    )


def _markdown_advisory_section(advisory: dict[str, Any] | None) -> list[str]:
    if not advisory:
        return []
    return [
        "## AI Advisory Contract",
        "",
        f"**Status:** `{advisory.get('status', 'unknown')}`",
        f"**Provider:** `{advisory.get('provider', 'none')}`",
        f"**Mode:** `{advisory.get('mode', 'unknown')}`",
        f"**Invalid Citations:** {len(advisory.get('invalid_citations', []))}",
        "",
    ]


def _explain_detector_group(detector: str, findings: list[dict[str, Any]]) -> list[str]:
    label = _explain_status_label({f["status"] for f in findings})
    noun = "finding" if len(findings) == 1 else "findings"
    lines = [f"{detector}  [{label}]  ({len(findings)} {noun})"]
    for f in findings:
        lines += _explain_finding_lines(f)
    lines.append("")
    return lines


def _explain_finding_lines(f: dict[str, Any]) -> list[str]:
    occ = f["finding_id"].rsplit(":", 1)[-1]
    file_str = "(repository)" if f["file"] == "." else (
        f"{f['file']}:{f['line']}" if f["line"] else f["file"]
    )
    lines = [f"  [{occ}]  {file_str}", f"         finding_id: {f['finding_id']}"]
    if f.get("pattern_id"):
        lines.append(f"         pattern : {f['pattern_id']}")
    if f.get("snippet"):
        lines.append(f"         snippet : \"{f['snippet']}\"")
    if f.get("explanation"):
        lines.append(f"         reason  : {f['explanation']}")
    for k, v in (f.get("metadata") or {}).items():
        if k not in _EXPLAIN_META_SKIP:
            lines.append(f"         {k}      : {v}")
    return lines


def _explain_ast_section(ast: dict[str, Any]) -> list[str]:
    if not ast:
        return []
    lines = [_EXPLAIN_SEP, "AST Signal Summary", ""]
    lines += [f"  {k:<34} {v}" for k, v in ast.items() if v is not None]
    lines.append("")
    return lines


def _explain_s4_section(s4: dict[str, Any]) -> list[str]:
    if not s4:
        return []
    lines = [_EXPLAIN_SEP, "Stage 4 Replication Rubric", ""]
    for key, item in s4.items():
        sc, mx, ev = item.get("score", 0), item.get("max", 0), item.get("evidence", "")
        lines.append(f"  {key:<42} {sc:>3} / {mx:<3}  {ev}")
    lines.append("")
    return lines


def _explain_reasoning_section(reasoning: dict[str, Any]) -> list[str]:
    if not reasoning:
        return []
    lines = [_EXPLAIN_SEP, "Reasoning Diagnostics", ""]
    lines.append(f"  version                         {reasoning.get('version', 'unknown')}")
    policy = reasoning.get("policy", {})
    lines.append(f"  mode                            {policy.get('mode', 'unknown')}")
    lines.append(f"  final_score_override            {policy.get('final_score_override', False)}")
    for key in ("evidence_budget", "confidence_envelope", "lane_coherence",
                "uncertainty_budget", "evidence_risk_gate"):
        item = reasoning.get(key, {})
        status = item.get("status", "unknown")
        lines.append(f"  {key:<31} {status}")
    lines.append("")
    return lines


def _explain_advisory_section(advisory: dict[str, Any] | None) -> list[str]:
    if not advisory:
        return []
    lines = [_EXPLAIN_SEP, "AI Advisory Contract", ""]
    lines.append(f"  schema_version                  {advisory.get('schema_version', 'unknown')}")
    lines.append(f"  provider                        {advisory.get('provider', 'none')}")
    lines.append(f"  mode                            {advisory.get('mode', 'unknown')}")
    lines.append(f"  status                          {advisory.get('status', 'unknown')}")
    lines.append(f"  final_score_override            {advisory.get('policy', {}).get('final_score_override', False)}")
    lines.append(f"  invalid_citations               {len(advisory.get('invalid_citations', []))}")
    lines.append("")
    return lines


def _explain_status_label(statuses: set[str]) -> str:
    for candidate in ("error", "detected", "not_detected", "absent", "not_applicable"):
        if candidate in statuses:
            return candidate.upper()
    return next(iter(statuses), "UNKNOWN").upper()


# ── reportlab: document entry point ──────────────────────────────────────────
def _write_rl_pdf(path: Path, result: dict[str, Any], mode: str, pages: int) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=10 * mm,
        bottomMargin=12 * mm,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
    )
    story: list[Any] = []
    story += _page1_executive(result, mode, pages)
    if mode == "detailed":
        story += _detail_pages(result, pages)
    doc.build(story)


# ── style factory ─────────────────────────────────────────────────────────────
_style_cache: dict[str, Any] = {}
_STYLE_CACHE_LIMIT = 256

def _style(name: str, size: int = 9, leading: int = 12, color: str = _DGRAY,
           bold: bool = False, align: str = "LEFT") -> Any:
    key = f"{name}_{size}_{leading}_{color}_{bold}_{align}"
    if key not in _style_cache:
        if len(_style_cache) >= _STYLE_CACHE_LIMIT:
            _style_cache.clear()
        _style_cache[key] = ParagraphStyle(
            key,
            fontSize=size,
            leading=leading,
            textColor=_hx(color),
            fontName="Helvetica-Bold" if bold else "Helvetica",
            alignment={"LEFT": 0, "CENTER": 1, "RIGHT": 2}.get(align, 0),
        )
    return _style_cache[key]


# ── Page 1: Executive Dashboard (brief + detailed) ────────────────────────────
def _page1_executive(result: dict[str, Any], mode: str, pages: int) -> list[Any]:
    story: list[Any] = []
    story += _header_block(result)
    story += _score_row(result)
    story.append(Spacer(1, 3 * mm))
    story += _stage_cards(result)
    story.append(Spacer(1, 3 * mm))
    story += _integrity_and_risks(result)
    story += _footer_block()
    return story


def _header_block(result: dict[str, Any]) -> list[Any]:
    t = result["target"]
    commit = (t.get("commit") or "")[:12] or "—"
    branch = t.get("branch") or "—"
    audit_date = result.get("generated_at_local", "—")
    mode = result.get("execution_mode", "—")

    header_data = [[Paragraph(
        f'<font color="{_WHITE}"><b>STEM BIO-AI Evidence-Surface Scan v{result["stem_ai_version"]}</b></font>',
        _style("H1", 14, 18, _WHITE, True),
    )]]
    header_tbl = Table(header_data, colWidths=["100%"])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _hx(_NAVY)),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))

    meta = (
        f'<font color="{_DGRAY}"><b>Repository:</b> {_xt(t["name"])} &nbsp;|&nbsp; '
        f'<b>Commit:</b> {commit} &nbsp;|&nbsp; '
        f'<b>Branch:</b> {_xt(branch)} &nbsp;|&nbsp; '
        f'<b>Audit Date:</b> {audit_date} &nbsp;|&nbsp; '
        f'<b>Mode:</b> {mode}</font>'
    )
    meta_data = [[Paragraph(meta, _style("M1", 7, 10, _DGRAY))]]
    meta_tbl = Table(meta_data, colWidths=["100%"])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _hx(_MGRAY)),
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

    score_cell = [
        Paragraph(
            f'<font color="{_NAVY}" size="28"><b>{fs}</b></font>'
            f'<font color="{_DGRAY}" size="13"> / 100</font>',
            _style("SC1", 28, 34, _NAVY, True, "CENTER"),
        ),
        Paragraph("Final Score", _style("SL1", 8, 11, _DGRAY, False, "CENTER")),
    ]

    tier_badge = [[Paragraph(
        f'<font color="{_WHITE}"><b>{_xt(tier)}</b></font>',
        _style("TB1", 12, 16, _WHITE, True, "CENTER"),
    )]]
    tier_tbl = Table(tier_badge, colWidths=[60 * mm])
    tier_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _hx(tier_hex)),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    scope_cell = [
        tier_tbl,
        Spacer(1, 2 * mm),
        Paragraph(
            f'<font color="{_DGRAY}"><b>Use Scope:</b></font><br/>'
            f'<font color="{_DGRAY}" size="8">{_xt(use_scope)}</font>',
            _style("US1", 8, 11, _DGRAY),
        ),
    ]

    weight_note = (
        f'<font color="{_DGRAY}" size="7.5">Weighted model: '
        f'Stage 1 x 0.40 + Stage 2R x 0.20 + Stage 3 x 0.40 '
        f'- Risk Penalty = <b>{fs}</b></font>'
    )

    row_tbl = Table([[score_cell, scope_cell]], colWidths=[50 * mm, None])
    row_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), _hx(_LGRAY)),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
    ]))
    return [row_tbl, Spacer(1, 1 * mm), Paragraph(weight_note, _style("WN1", 7.5, 10, _DGRAY))]


def _stage_cards(result: dict[str, Any]) -> list[Any]:
    score = result["score"]
    stages = [
        ("Stage 1", "README Evidence", score["stage_1_readme_intent"], _TEAL),
        ("Stage 2R", "Repo-Local Consistency", score["stage_2_repo_local_consistency"] or 0, _PURPLE),
        ("Stage 3", "Code / Bio Responsibility", score["stage_3_code_bio"], _SLATE),
        ("Stage 4", "Replication Evidence", result.get("replication_score", 0), _GREEN),
    ]
    cells = []
    for label, sub, val, col in stages:
        card = [
            [Paragraph(
                f'<font color="{_WHITE}"><b>{label}</b><br/><i>{sub}</i></font>',
                _style(f"CH_{label}", 8.5, 12, _WHITE, True, "CENTER"),
            )],
            [Paragraph(
                f'<font color="{col}" size="22"><b>{val}</b></font>'
                f'<font color="{_DGRAY}" size="9"> / 100</font>',
                _style(f"CV_{label}", 22, 26, col, True, "CENTER"),
            )],
        ]
        t = Table(card, colWidths=["100%"])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), _hx(col)),
            ("BACKGROUND",    (0, 1), (0, 1), _hx(_LGRAY)),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
        ]))
        cells.append(t)

    row = Table([cells], colWidths=["25%", "25%", "25%", "25%"])
    row.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [row]


def _integrity_and_risks(result: dict[str, Any]) -> list[Any]:
    ci = result["code_integrity"]
    risks = result["notable_risks"]
    positive = result.get("notable_positive_evidence", [])

    ci_rows = [[Paragraph(
        f'<font color="{_WHITE}"><b>Code Integrity</b></font>',
        _style("CIH1", 9, 12, _WHITE, True),
    )]]
    labels = {
        "C1_hardcoded_credentials": "C1 Credentials",
        "C2_dependency_pinning": "C2 Dependency Pinning",
        "C3_dead_or_deprecated_patient_adjacent_paths": "C3 Deprecated Paths",
        "C4_exception_handling_clinical_adjacent_paths": "C4 Exception Handling",
    }
    for key, item in ci.items():
        s = item["status"]
        sc = _status_hex(s)
        ev = _clip_words(item["evidence"][0] if item["evidence"] else "", 92)
        badge = [[Paragraph(
            f'<font color="{_WHITE}" size="7"><b>{s}</b></font>',
            _style(f"B_{key[:4]}", 7, 9, _WHITE, True, "CENTER"),
        )]]
        bt = Table(badge, colWidths=[15 * mm])
        bt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), _hx(sc)),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        short_key = labels.get(key, key)
        ci_rows.append([[
            bt,
            Paragraph(
                f'<font color="{_DGRAY}" size="8"><b>{short_key}</b><br/>{_xt(ev)}</font>',
                _style(f"CI_{key[:4]}", 7.5, 10, _DGRAY),
            ),
        ]])

    ci_tbl = Table(ci_rows, colWidths=["100%"])
    ci_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), _hx(_NAVY)),
        ("ROWBACKGROUNDS",(0, 1), (0, -1), [_hx(_LGRAY), _hx(_WHITE)]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
    ]))

    risk_lines = "".join(f'&#8226; {_xt(r[:110])}<br/>' for r in risks[:4])
    pos_lines  = "".join(f'&#8226; {_xt(p[:110])}<br/>' for p in positive[:3])
    right_rows = [
        [Paragraph(f'<font color="{_WHITE}"><b>Remediation Targets</b></font>', _style("RH1", 9, 12, _WHITE, True))],
        [Paragraph(f'<font color="{_DGRAY}" size="8">{risk_lines}</font>', _style("RL1", 8, 11, _DGRAY))],
        [Paragraph(f'<font color="{_WHITE}"><b>Positive Evidence</b></font>', _style("PH1", 9, 12, _WHITE, True))],
        [Paragraph(f'<font color="{_DGRAY}" size="8">{pos_lines}</font>', _style("PL1", 8, 11, _DGRAY))],
    ]
    right_tbl = Table(right_rows, colWidths=["100%"])
    right_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), _hx(_RED)),
        ("BACKGROUND",    (0, 1), (0, 1), _hx(_LGRAY)),
        ("BACKGROUND",    (0, 2), (0, 2), _hx(_GREEN)),
        ("BACKGROUND",    (0, 3), (0, 3), _hx(_WHITE)),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
    ]))

    two_col = Table([[ci_tbl, right_tbl]], colWidths=["48%", "52%"])
    two_col.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    return [two_col]


def _footer_block() -> list[Any]:
    return [
        Spacer(1, 4 * mm),
        HRFlowable(width="100%", thickness=0.5, color=_hx(_MGRAY)),
        Spacer(1, 1.5 * mm),
        Paragraph(
            f'<font color="{_DGRAY}" size="7">Independent audit summary — STEM BIO-AI v{__version__} &nbsp;|&nbsp; '
            "Not clinical certification. Not regulatory clearance. Not medical advice.</font>",
            _style("FT1", 7, 9, _DGRAY, False, "CENTER"),
        ),
    ]


# ── Detail page dispatcher ────────────────────────────────────────────────────
def _detail_pages(result: dict[str, Any], pages: int) -> list[Any]:
    story: list[Any] = []
    story += _page2_stage_analysis(result)
    story += _page3_stage3_analysis(result)
    if pages >= 5:
        story += _page4_integrity_deep(result)
        story += _page5_method_remediation(result)
    return story


# ── Shared detail helpers ─────────────────────────────────────────────────────
def _sec_hdr(title: str, color: str = _NAVY) -> list[Any]:
    tbl = Table([[Paragraph(
        f'<font color="{_WHITE}"><b>{title}</b></font>',
        _style(f"SH_{title[:8]}", 10, 14, _WHITE, True),
    )]], colWidths=["100%"])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _hx(color)),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    return [tbl, Spacer(1, 2 * mm)]


def _mini_score(label: str, val: int, max_val: int, col: str) -> Table:
    d = [
        [Paragraph(
            f'<font color="{col}" size="20"><b>{val}</b></font>'
            f'<font color="{_DGRAY}" size="9"> / {max_val}</font>',
            _style(f"MS_{label[:6]}", 20, 24, col, True, "CENTER"),
        )],
        [Paragraph(label, _style(f"ML_{label[:6]}", 7, 9, _DGRAY, False, "CENTER"))],
    ]
    t = Table(d, colWidths=[34 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _hx(_LGRAY)),
        ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
    ]))
    return t


def _rubric_rows(items: list[tuple[str, str, str, str]], id_prefix: str = "R") -> Table:
    """items: (name, score_str, color_hex, evidence_text)"""
    header = [
        Paragraph(f'<font color="{_WHITE}"><b>Check</b></font>', _style(f"{id_prefix}H1", 8, 10, _WHITE, True)),
        Paragraph(f'<font color="{_WHITE}"><b>Points</b></font>', _style(f"{id_prefix}H2", 8, 10, _WHITE, True, "CENTER")),
        Paragraph(f'<font color="{_WHITE}"><b>Evidence / Finding</b></font>', _style(f"{id_prefix}H3", 8, 10, _WHITE, True)),
    ]
    rows = [header]
    for i, (name, score_str, col, ev) in enumerate(items):
        uid = f"{id_prefix}_{i}"
        rows.append([
            Paragraph(f'<b>{_xt(name)}</b>', _style(f"{uid}N", 8, 11, _DGRAY, True)),
            Paragraph(
                f'<font color="{col}"><b>{_xt(score_str)}</b></font>',
                _style(f"{uid}S", 8, 11, col, True, "CENTER"),
            ),
            Paragraph(_xt(_clip_words(ev, 175)), _style(f"{uid}E", 7.5, 10, _DGRAY)),
        ])
    t = Table(rows, colWidths=[52 * mm, 18 * mm, None])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), _hx(_NAVY)),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_hx(_LGRAY), _hx(_WHITE)]),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, _hx(_MGRAY)),
        ("GRID",          (0, 0), (-1, -1), 0.3, _hx(_MGRAY)),
    ]))
    return t


# ── Page 2: Stage 1 + Stage 2R Analysis ──────────────────────────────────────
def _page2_stage_analysis(result: dict[str, Any]) -> list[Any]:
    story: list[Any] = [PageBreak()]
    score = result["score"]
    cls = result["classification"]
    s1 = score["stage_1_readme_intent"]
    s2r = score["stage_2_repo_local_consistency"] or 0
    ca = cls["clinical_adjacent"]
    has_disc = cls["has_explicit_clinical_boundary"]
    readme_present = "README.md" in result.get("file_hashes_sha256", {})

    # ── Stage 1 ──────────────────────────────────────────────────────────────
    story += _sec_hdr("Stage 1 — README Evidence Signal  |  Weight: 0.40", _TEAL)

    s1_rubric = result.get("stage_1_rubric", {})
    s1_order = [
        ("baseline", "Baseline"),
        ("S1_missing_readme", "README present"),
        ("S1_domain_readme", "BIO/medical terms in README"),
        ("S1_domain_package", "BIO/medical terms in package"),
        ("H1_clinical_certainty_hype", "H1: Clinical Certainty Hype"),
        ("H2_regulatory_approval_hype", "H2: Regulatory Approval Hype"),
        ("H3_autonomous_replacement_hype", "H3: Autonomous Replacement Hype"),
        ("H4_breakthrough_marketing_hype", "H4: Marketing Hype"),
        ("H5_universal_generalization_hype", "H5: Universal Generalization"),
        ("H6_perfect_accuracy_hype", "H6: Perfect Accuracy Claim"),
        ("R1_limitations_section", "R1: Limitations Section"),
        ("R2_regulatory_framework", "R2: Regulatory Framework"),
        ("R3_clinical_disclaimer", "R3: Clinical Boundary"),
        ("R4_demographic_bias_boundary", "R4: Bias / Subgroup Boundary"),
        ("R5_reproducibility_provisions", "R5: Reproducibility Provisions"),
    ]
    s1_items: list[tuple[str, str, str, str]] = []
    for key, label in s1_order:
        item = s1_rubric.get(key)
        if not item:
            continue
        pts = item.get("score", 0)
        col = _RED if pts < 0 else _GREEN if pts > 0 else _DGRAY
        s1_items.append((label, f"{pts:+d}", col, item.get("evidence", "")))
    if not s1_items:
        s1_items = [
            ("Baseline", "+60", _DGRAY, "All non-nascent repositories start at 60."),
            ("README present", "+0" if readme_present else "-20", _GREEN if readme_present else _RED,
             "README.md detected in repository root." if readme_present else "No README found — major deduction applied."),
        ]
    calc_note = s1_rubric.get("calculation", f"Stage 1 evidence score = {s1} / 100")

    chip1 = _mini_score("S1 Score", s1, 100, _TEAL)
    tbl1 = _rubric_rows(s1_items, "S1")
    combined1 = Table([[chip1, tbl1]], colWidths=[38 * mm, None])
    combined1.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(combined1)
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph(
        f'<font color="{_DGRAY}" size="7.5"><i>Calculation: {_xt(calc_note)}</i></font>',
        _style("S1CL", 7.5, 10, _DGRAY),
    ))

    # Classification info bar
    ca_col = _ORANGE if ca else _GREEN
    disc_col = _GREEN if has_disc else _RED
    t0_col = _RED if cls["t0_hard_floor"] else _GREEN
    info_text = (
        f'&#8226; Clinical-Adjacent: <font color="{ca_col}"><b>{"YES" if ca else "NO"}</b></font>'
        f' ({_xt(cls["ca_severity"])}) &nbsp;&nbsp; '
        f'&#8226; Explicit Disclaimer: <font color="{disc_col}"><b>{"PRESENT" if has_disc else "ABSENT"}</b></font>'
        f' &nbsp;&nbsp; '
        f'&#8226; T0 Hard Floor: <font color="{t0_col}"><b>{"TRIGGERED" if cls["t0_hard_floor"] else "Clear"}</b></font>'
    )
    info_tbl = Table([[Paragraph(info_text, _style("INF1", 8, 11, _DGRAY))]], colWidths=["100%"])
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _hx(_LGRAY)),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
    ]))
    story.append(Spacer(1, 2 * mm))
    story.append(info_tbl)

    # ── Stage 2R ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 5 * mm))
    story += _sec_hdr("Stage 2R — Repo-Local Consistency  |  Weight: 0.20", _PURPLE)

    rubric = result.get("stage_2r_rubric", {})
    verdict = str(rubric.get("verdict", ""))
    calculation = str(rubric.get("calculation", f"= {s2r}"))

    _label_map = {
        "baseline": "Baseline",
        "R2R_1_readme_package_code_alignment": "R2R-1: README / Package Alignment",
        "R2R_2_readme_docs_alignment": "R2R-2: README / Docs Alignment",
        "R2R_3_readme_test_ci_alignment": "R2R-3: README / Test-CI Alignment",
        "R2R_D2_missing_clinical_use_boundary": "R2R-D2: Missing Clinical Boundary (PENALTY)",
    }
    _ev_tooltip = {
        "baseline": "Every repository that is not nascent starts at 60. "
                    "This baseline accounts for basic structural maturity.",
        "R2R_1_readme_package_code_alignment": "README and package metadata share bio-domain vocabulary, "
                    "indicating claim-to-implementation alignment.",
        "R2R_2_readme_docs_alignment": "README and docs/ share domain vocabulary, "
                    "indicating consistent external communication.",
        "R2R_3_readme_test_ci_alignment": "Test and CI surfaces are present and reference the same "
                    "domain as the README.",
        "R2R_D2_missing_clinical_use_boundary": "Clinical-adjacent repository lacks an explicit "
                    "'research use only' or 'not for diagnostic use' boundary — high review risk.",
    }

    s2r_items: list[tuple[str, str, str, str]] = []
    for key in ("baseline", "R2R_1_readme_package_code_alignment",
                "R2R_2_readme_docs_alignment", "R2R_3_readme_test_ci_alignment",
                "R2R_D2_missing_clinical_use_boundary"):
        item = rubric.get(key)
        if item is None or not isinstance(item, dict):
            continue
        sc = item.get("score", 0)
        ev_raw = item.get("evidence", "")
        ev_ext = _ev_tooltip.get(key, "")
        combined_ev = f"{ev_raw} — {ev_ext}" if ev_ext else ev_raw
        if key == "baseline":
            col = _DGRAY
            sc_str = f"+{sc}"
        elif key.startswith("R2R_D"):
            col = _RED if sc < 0 else _DGRAY
            sc_str = str(sc)
        else:
            col = _TEAL if sc > 0 else _DGRAY
            sc_str = f"+{sc}" if sc > 0 else "0 (not detected)"
        s2r_items.append((_label_map.get(key, key), sc_str, col, combined_ev))

    chip2 = _mini_score("S2R Score", s2r, 100, _PURPLE)
    tbl2 = _rubric_rows(s2r_items, "S2R")
    combined2 = Table([[chip2, tbl2]], colWidths=[38 * mm, None])
    combined2.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(combined2)
    story.append(Spacer(1, 1 * mm))

    verdict_col = _GREEN if "Strong" in verdict else (_AMBER if "Mixed" in verdict else _RED)
    story.append(Paragraph(
        f'<font color="{_DGRAY}" size="7.5"><i>{_xt(calculation)}</i></font>'
        f'  &nbsp;&nbsp; <font color="{verdict_col}"><b>{_xt(verdict)}</b></font>',
        _style("S2RVERDICT", 7.5, 10, _DGRAY),
    ))

    story += _footer_block()
    return story


# ── Page 3: Stage 3 Full Breakdown ───────────────────────────────────────────
def _page3_stage3_analysis(result: dict[str, Any]) -> list[Any]:
    story: list[Any] = [PageBreak()]
    score = result["score"]
    s3 = score["stage_3_code_bio"]
    rubric = result.get("stage_3_rubric", {})

    story += _sec_hdr("Stage 3 — Code & Bio Responsibility  |  Weight: 0.40", _SLATE)

    _ev_ext = {
        "T1_CI_CD": "CI/CD workflows (GitHub Actions, GitLab CI, CircleCI) verify "
                    "that commits do not silently break the pipeline. Full credit (15) requires workflow files present.",
        "T2_domain_tests": "Domain-specific tests verify biological outputs — e.g., "
                    "sequencing pipeline correctness, variant call validation, or genomic data integrity. "
                    "Full credit (15) requires BIO-term presence in test files. Partial (8) if tests exist but are generic.",
        "T3_changelog_release_hygiene": "A CHANGELOG tracks which version fixed which defect — "
                    "essential for regulatory traceability and reproducibility audits. "
                    "CHANGELOG.md, CHANGELOG, or NEWS.md all qualify.",
        "B1_data_provenance_controls": "Pinned or checksummed dependency manifests "
                    "(requirements.txt, pyproject.toml, environment.yml) ensure reproducible environments. "
                    "Score 10 if manifest detected; max 15 requires hash-pinning evidence.",
        "B2_bias_limitations": "Documentation of algorithmic bias, limitations, "
                    "or model boundary conditions. Requires manual review of README, model cards, "
                    "or supplementary docs — not detectable by local CLI scan.",
        "B3_coi_funding": "Conflict of interest and funding disclosure in README or FUNDING.md. "
                    "Required for institutional review context — not detectable by local CLI scan.",
    }

    t_items: list[tuple[str, str, str, str]] = []
    for key, label in [
        ("T1_CI_CD", "T1: CI/CD Workflow"),
        ("T2_domain_tests", "T2: Domain-Specific Tests"),
        ("T3_changelog_release_hygiene", "T3: Changelog & Release Hygiene"),
    ]:
        item = rubric.get(key, {})
        sc = item.get("score", 0)
        mx = item.get("max", 15)
        ev = item.get("evidence", "")
        ext = _ev_ext.get(key, "")
        col = _GREEN if sc == mx else (_AMBER if sc > 0 else _RED)
        t_items.append((label, f"{sc} / {mx}", col, f"{ev} — {ext}" if ext else ev))

    b_items: list[tuple[str, str, str, str]] = []
    for key, label in [
        ("B1_data_provenance_controls", "B1: Data Provenance Controls"),
        ("B2_bias_limitations", "B2: Bias / Limitations Documentation"),
        ("B3_coi_funding", "B3: COI & Funding Disclosure"),
    ]:
        item = rubric.get(key, {})
        sc = item.get("score", 0)
        mx = item.get("max", 15)
        ev = item.get("evidence", "")
        ext = _ev_ext.get(key, "")
        not_detectable = "local CLI scan" in ev
        col = (_GREEN if sc == mx else (_AMBER if sc > 0 else
               (_DGRAY if not_detectable else _RED)))
        note = " [Manual review required]" if not_detectable else ""
        b_items.append((label, f"{sc} / {mx}{note}", col, f"{ev} — {ext}" if ext else ev))

    chip3 = _mini_score("S3 Score", s3, 100, _SLATE)

    body_items: list[Any] = [
        Paragraph(
            f'<font color="{_SLATE}"><b>Engineering Accountability (T-series)</b></font>',
            _style("TS1", 8.5, 12, _SLATE, True),
        ),
        Spacer(1, 1 * mm),
        _rubric_rows(t_items, "T"),
        Spacer(1, 3 * mm),
        Paragraph(
            f'<font color="{_SLATE}"><b>Biological Integrity (B-series)</b></font>',
            _style("BS1", 8.5, 12, _SLATE, True),
        ),
        Spacer(1, 1 * mm),
        _rubric_rows(b_items, "B"),
    ]

    main_row = Table([[chip3, body_items]], colWidths=[38 * mm, None])
    main_row.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(main_row)

    # Gap analysis
    story.append(Spacer(1, 5 * mm))
    story += _sec_hdr("Stage 3 Gap Analysis — Path to Next Tier", _DGRAY)

    local_max = 55
    fs = score["final_score"]
    gap_t3 = max(0, 70 - fs)
    gap_t4 = max(0, 85 - fs)
    t_total = sum(rubric.get(k, {}).get("score", 0) for k in ["T1_CI_CD", "T2_domain_tests", "T3_changelog_release_hygiene"])
    b_total = sum(rubric.get(k, {}).get("score", 0) for k in ["B1_data_provenance_controls", "B2_bias_limitations", "B3_coi_funding"])

    gap_lines = [
        f'&#8226; <b>T-series (engineering) attained:</b> {t_total} / 45 &nbsp; '
        f'<b>B-series (bio integrity) attained:</b> {b_total} / 35',
        f'&#8226; <b>Local CLI scan maximum:</b> {local_max} / 100 '
        f'(T1+T2+T3 max 15 each; B1 max 10; B2/B3 require manual review)',
        f'&#8226; <b>Gap to T3 (final score &gt;= 70):</b> {gap_t3} points needed across all stages',
        f'&#8226; <b>Gap to T4 (final score &gt;= 85):</b> {gap_t4} points needed across all stages',
        '&#8226; <b>B2 Bias/Limitations:</b> Not detectable — requires manual audit of README, '
        'model card, or supplementary documentation for validation boundaries and algorithmic limitations',
        '&#8226; <b>B3 COI/Funding:</b> Not detectable — requires inspection of README or FUNDING.md '
        'for conflict of interest and funding source disclosure',
    ]
    for line in gap_lines:
        story.append(Paragraph(
            f'<font color="{_DGRAY}" size="8">{line}</font>',
            _style(f"GL_{line[:6]}", 8, 13, _DGRAY),
        ))

    story += _footer_block()
    return story


# ── Page 4: Code Integrity Deep Dive + Classification (5p only) ───────────────
def _page4_integrity_deep(result: dict[str, Any]) -> list[Any]:
    story: list[Any] = [PageBreak()]
    ci = result["code_integrity"]
    cls = result["classification"]
    hashes = result.get("file_hashes_sha256", {})
    tgt = result["target"]

    story += _sec_hdr("Code Integrity — Deep Analysis", _NAVY)

    _remediation = {
        "C1_hardcoded_credentials":
            "CRITICAL: Rotate all exposed credentials immediately. Remove from git history "
            "using git-filter-repo. Use environment variables or a secrets manager (AWS Secrets Manager, "
            "HashiCorp Vault, Azure Key Vault). Add a pre-commit hook with detect-secrets.",
        "C2_dependency_pinning":
            "Pin all dependencies to exact versions (== for pip, hash-pinning for conda). "
            "Run pip-audit or safety regularly. Consider pip-compile for reproducible lock files. "
            "Unpinned ranges in clinical-adjacent pipelines create silent regression risk.",
        "C3_dead_or_deprecated_patient_adjacent_paths":
            "Audit deprecated/ directories for patient-adjacent metadata patterns. "
            "If clinical data was processed, verify data destruction or anonymization logs. "
            "Dead code with patient metadata patterns must be purged or explicitly annotated as test fixtures.",
        "C4_exception_handling_clinical_adjacent_paths":
            "Replace broad 'except Exception: pass' or 'except: return True' patterns with "
            "specific error types and explicit failure logging. In clinical-adjacent code paths, "
            "any silent failure is a patient safety risk. Fail closed, not open.",
    }

    _desc = {
        "C1_hardcoded_credentials":
            "Scans for AWS access keys (AKIA*), OpenAI keys (sk-*), GitHub tokens (ghp_*), "
            "and api_key = '...' patterns in all text files.",
        "C2_dependency_pinning":
            "Checks whether requirements.txt / pyproject.toml / environment.yml use "
            "exact version pins (==, sha256 hash) or loose ranges (>=, no pin).",
        "C3_dead_or_deprecated_patient_adjacent_paths":
            "Scans deprecated/ directories for patient metadata patterns: "
            "patient_id, patient_age, patient_sex, sample_id, collection_date, lab_id, etc.",
        "C4_exception_handling_clinical_adjacent_paths":
            "Detects fail-open exception patterns: 'except Exception: pass' or "
            "'except: return True' in code — these silently ignore errors that could corrupt clinical outputs.",
    }

    short = {
        "C1_hardcoded_credentials": "C1: Hardcoded Credentials",
        "C2_dependency_pinning": "C2: Dependency Pinning",
        "C3_dead_or_deprecated_patient_adjacent_paths": "C3: Deprecated Patient Paths",
        "C4_exception_handling_clinical_adjacent_paths": "C4: Fail-Open Exceptions",
    }

    ci_items: list[tuple[str, str, str, str]] = []
    for key, cfg in ci.items():
        s = cfg["status"]
        col = _status_hex(s)
        ev_raw = cfg["evidence"][0] if cfg["evidence"] else ""
        ev_full = f"{ev_raw} | Scan: {_desc.get(key, '')}"
        ci_items.append((short.get(key, key), s, col, ev_full))

    story.append(_rubric_rows(ci_items, "CI"))
    story.append(Spacer(1, 3 * mm))

    # Remediation guidance
    fail_warn = [(k, v) for k, v in ci.items() if v["status"] != "PASS"]
    if fail_warn:
        story += _sec_hdr("Remediation Guidance", _RED)
        for key, v in fail_warn:
            s = v["status"]
            col = _RED if s == "FAIL" else _AMBER
            guidance = _remediation.get(key, "Review and remediate before clinical-adjacent deployment.")
            story.append(Paragraph(
                f'<font color="{col}"><b>[{s}] {_xt(short.get(key, key))}:</b></font>',
                _style(f"RG_H_{key[:4]}", 8.5, 12, col, True),
            ))
            story.append(Paragraph(
                f'<font color="{_DGRAY}" size="8">&#8594; {_xt(guidance)}</font>',
                _style(f"RG_B_{key[:4]}", 8, 11, _DGRAY),
            ))
            story.append(Spacer(1, 2 * mm))
    else:
        story.append(Paragraph(
            f'<font color="{_GREEN}">All code integrity checks PASSED. '
            'Continue monitoring with each major release.</font>',
            _style("CIOK", 8, 11, _GREEN),
        ))

    # Classification analysis
    story.append(Spacer(1, 3 * mm))
    story += _sec_hdr("Classification & Repository Analysis", _SLATE)

    cls_items: list[tuple[str, str, str, str]] = [
        ("Clinical Adjacent", "YES" if cls["clinical_adjacent"] else "NO",
         _ORANGE if cls["clinical_adjacent"] else _GREEN,
         f'Severity: {cls["ca_severity"]}. '
         'Triggered by BIO/CLINICAL_OUTPUT term regex match across README, docs, and code.'),
        ("T0 Hard Floor", "TRIGGERED" if cls["t0_hard_floor"] else "Clear",
         _RED if cls["t0_hard_floor"] else _GREEN,
         "Score forced to 0 regardless of rubric performance — e.g., AGI claim in clinical context."
         if cls["t0_hard_floor"] else "No T0_HARD_FLOOR condition detected."),
        ("Explicit Disclaimer", "PRESENT" if cls["has_explicit_clinical_boundary"] else "ABSENT",
         _GREEN if cls["has_explicit_clinical_boundary"] else _AMBER,
         "Regex: 'not for clinical|not for diagnostic|research use only|not medical advice' "
         "in README + docs surface." if cls["has_explicit_clinical_boundary"] else
         "Disclaimer pattern not found in README or docs. High impact on Stage 1 and Stage 2R scores."),
        ("Files Scanned", str(tgt.get("file_count", "—")), _TEAL,
         "Total files indexed by recursive walk. Text files only for content analysis; "
         "binary files counted but not read."),
        ("Execution Mode", result.get("execution_mode", "—"), _DGRAY,
         "No LLM calls. No network access. No runtime execution. "
         "Deterministic regex + file-system scan only."),
    ]
    story.append(_rubric_rows(cls_items, "CLS"))

    # File hashes
    if hashes:
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            f'<font color="{_NAVY}"><b>File Integrity (SHA-256)</b></font>',
            _style("FIH1", 9, 12, _NAVY, True),
        ))
        story.append(Spacer(1, 1 * mm))
        hash_rows: list[list[Any]] = [[
            Paragraph(f'<font color="{_WHITE}"><b>File</b></font>', _style("FHH1", 8, 10, _WHITE, True)),
            Paragraph(f'<font color="{_WHITE}"><b>SHA-256 Hash</b></font>', _style("FHH2", 8, 10, _WHITE, True)),
        ]]
        for fname, h in hashes.items():
            hash_rows.append([
                Paragraph(_xt(fname), _style(f"FN_{fname[:4]}", 8, 11, _DGRAY)),
                Paragraph(f'<font size="6.5" color="{_DGRAY}">{h}</font>',
                          _style(f"FV_{fname[:4]}", 6.5, 8, _DGRAY)),
            ])
        hash_tbl = Table(hash_rows, colWidths=[40 * mm, None])
        hash_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), _hx(_NAVY)),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_hx(_LGRAY), _hx(_WHITE)]),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
            ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
            ("GRID",          (0, 0), (-1, -1), 0.3, _hx(_MGRAY)),
        ]))
        story.append(hash_tbl)

    story += _footer_block()
    return story


# ── Page 5: Priority Improvements + Method + Metadata (5p only) ───────────────
def _page5_method_remediation(result: dict[str, Any]) -> list[Any]:
    story: list[Any] = [PageBreak()]
    risks = result.get("notable_risks", [])
    positive = result.get("notable_positive_evidence", [])
    score = result["score"]

    # Priority Improvements
    story += _sec_hdr("Priority Improvement Roadmap", _RED)

    _pri_detail: dict[str, str] = {
        "Clinical-adjacent surfaces exist without an explicit non-diagnostic/non-clinical boundary.":
            "Add a prominent 'Research Use Only — Not for Clinical or Diagnostic Use' disclaimer "
            "to README H1 or H2 section. Reference applicable frameworks: FDA SaMD guidance, "
            "EU AI Act Article 6, or IRB oversight requirements for your deployment context.",
        "C1_hardcoded_credentials: FAIL":
            "CRITICAL: Rotate all exposed credentials immediately. Remove from git history "
            "using git-filter-repo. Implement pre-commit secrets detection. "
            "Use environment variables or a secrets manager for all future credential handling.",
        "C2_dependency_pinning: WARN":
            "Pin all production dependencies to exact versions (== for pip). "
            "Add pip-audit or safety to CI pipeline for vulnerability scanning. "
            "Consider pip-compile for deterministic lock files.",
        "C3_dead_or_deprecated_patient_adjacent_paths: WARN":
            "Audit deprecated/ directories for patient-adjacent metadata patterns. "
            "If clinical data was processed historically, verify destruction or anonymization logs. "
            "If patterns are from test fixtures, annotate clearly with # noqa comments.",
        "C4_exception_handling_clinical_adjacent_paths: WARN":
            "Replace broad exception handlers with specific error types and explicit logging. "
            "In any clinical-adjacent code path: fail closed, not open. "
            "Never silently return True or pass on exception.",
    }

    no_major_risks = not risks or risks == ["No major local risks detected by the CLI scan."]
    if no_major_risks:
        story.append(Paragraph(
            f'<font color="{_GREEN}"><b>No critical risks detected by local CLI scan.</b></font><br/>'
            f'<font color="{_DGRAY}" size="8">A manual audit is still recommended for '
            'clinical-adjacent deployment. Local CLI cannot assess B2 (bias) or B3 (COI).</font>',
            _style("NR1", 8, 12, _DGRAY),
        ))
    else:
        for i, risk in enumerate(risks, 1):
            guidance = _pri_detail.get(risk, (
                "Review this finding and implement appropriate controls "
                "before supervised or clinical-adjacent deployment."
            ))
            ri_col = _RED if ("FAIL" in risk or "Clinical-adjacent" in risk) else _AMBER
            story.append(Paragraph(
                f'<font color="{ri_col}"><b>Priority {i}: {_xt(risk)}</b></font>',
                _style(f"PRI_{i}", 8.5, 12, ri_col, True),
            ))
            story.append(Paragraph(
                f'<font color="{_DGRAY}" size="8">&#8594; {_xt(guidance)}</font>',
                _style(f"PRG_{i}", 8, 11, _DGRAY),
            ))
            story.append(Spacer(1, 2.5 * mm))

    # Positive Evidence
    story.append(Spacer(1, 2 * mm))
    story += _sec_hdr("Positive Evidence Summary", _GREEN)
    for ev in positive:
        story.append(Paragraph(
            f'&#8226; <font color="{_DGRAY}" size="8">{_xt(ev)}</font>',
            _style(f"PE_{ev[:4]}", 8, 12, _DGRAY),
        ))

    # Method Boundary
    story.append(Spacer(1, 4 * mm))
    story += _sec_hdr("Method Boundary", _DGRAY)
    story.append(Paragraph(
        _xt(result.get("method", "")),
        _style("MB2", 8, 12, _DGRAY),
    ))
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph(
        f'<font color="{_AMBER}"><b>Scope boundary:</b></font> '
        '<font color="#4A5568" size="8">Runtime behavior, model output correctness, '
        'dynamic validation, wet-lab reproducibility, and clinical validation are '
        'outside the scope of this local CLI scan. This report assesses structural signals only.</font>',
        _style("MBSCOPE", 8, 11, _DGRAY),
    ))

    # Report Metadata
    story.append(Spacer(1, 4 * mm))
    story += _sec_hdr("Report Metadata", _NAVY)
    tgt = result["target"]
    meta_items = [
        ("Schema Version", result.get("schema_version", "—")),
        ("STEM BIO-AI Version", result.get("stem_ai_version", "—")),
        ("Generated (local date)", result.get("generated_at_local", "—")),
        ("Report Validity", "180 days from audit date"),
        ("Execution Mode", result.get("execution_mode", "—")),
        ("Repository", tgt["name"]),
        ("Remote URL", (tgt.get("remote") or "—")[:70]),
        ("Branch", tgt.get("branch") or "—"),
        ("Commit (HEAD)", (tgt.get("commit") or "—")[:40]),
        ("Files Scanned", str(tgt.get("file_count", "—"))),
        ("Final Score / Tier", f'{score["final_score"]} / 100 — {score["formal_tier"]}'),
    ]
    meta_data: list[list[Any]] = [[
        Paragraph(f'<font color="{_WHITE}"><b>Field</b></font>', _style("MH1", 8, 10, _WHITE, True)),
        Paragraph(f'<font color="{_WHITE}"><b>Value</b></font>', _style("MH2", 8, 10, _WHITE, True)),
    ]]
    for field, val in meta_items:
        meta_data.append([
            Paragraph(f'<b>{_xt(field)}</b>', _style(f"MF_{field[:4]}", 8, 11, _DGRAY, True)),
            Paragraph(_xt(str(val)), _style(f"MV_{field[:4]}", 8, 11, _DGRAY)),
        ])
    meta_tbl = Table(meta_data, colWidths=[55 * mm, None])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), _hx(_NAVY)),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_hx(_LGRAY), _hx(_WHITE)]),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("BOX",           (0, 0), (-1, -1), 0.5, _hx(_MGRAY)),
        ("GRID",          (0, 0), (-1, -1), 0.3, _hx(_MGRAY)),
    ]))
    story.append(meta_tbl)
    story += _footer_block()
    return story


# ── plain-text PDF fallback (no reportlab) ───────────────────────────────────
def render_pdf_pages(result: dict[str, Any], mode: str, pages: int) -> list[list[str]]:
    score = result["score"]
    brief = [
        "STEM BIO-AI Local Audit Brief",
        f"Target: {result['target']['name']}",
        f"Final Score: {score['final_score']} / 100",
        f"Formal Tier: {score['formal_tier']}",
        f"Use Scope: {score['use_scope']}",
        "",
        "Stage Scores",
        f"- Stage 1 README Evidence Signal: {score['stage_1_readme_intent']} / 100",
        f"- Stage 2R Repo-Local Consistency: {score['stage_2_repo_local_consistency']} / 100",
        f"- Stage 3 Code/Bio Responsibility: {score['stage_3_code_bio']} / 100",
        f"- Stage 4 Replication Evidence: {result.get('replication_score', 0)} / 100 ({result.get('replication_tier', 'R0')})",
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
    ], "", "Stage 4 Replication Evidence", *[
        f"- {k}: {v['score']} / {v['max']} {v['evidence']}"
        for k, v in result.get("stage_4_rubric", {}).items()
    ]])
    sets = [_fit_page(brief), p2, p3]
    if pages == 5:
        sets.append(_fit_page(["Code Integrity",
            *[f"- {k}: {v['status']} {v['evidence'][0]}" for k, v in result["code_integrity"].items()]]))
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
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(out)


def _page_stream(lines: list[str]) -> str:
    chunks = ["BT", "/F1 11 Tf", "50 800 Td"]
    y = 800
    first = True
    for line in lines:
        for wrapped in textwrap.wrap(_ascii(line), width=88) or [""]:
            overflow = _emit_page_chunk(chunks, wrapped, y, first)
            if overflow:
                return overflow
            if not first:
                y -= 16
            first = False
    chunks.append("ET")
    return "\n".join(chunks)


def _emit_page_chunk(chunks: list[str], wrapped: str, y: int, first: bool) -> str:
    if not first:
        chunks.append("0 -16 Td")
        if y - 16 < 60:
            chunks.append("ET")
            return "\n".join(chunks)
    chunks.append(f"({_escape_pdf(wrapped)}) Tj")
    return ""


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
