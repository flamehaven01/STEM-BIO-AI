"""5-section interactive HTML report renderer for STEM BIO-AI.

Sections: Executive Summary | Score Matrix | Code Integrity | AIRI Coverage | Evidence Detail
Self-contained: inline CSS + SVG + JS, zero external dependencies.
"""
from __future__ import annotations

from typing import Any

from .render_html_components import (
    _C, _STAGE_TIPS,
    xt, tier_color, tip_icon,
    svg_gauge, svg_donut, svg_hbar,
    integrity_card, domain_card, airi_row, evidence_row,
)
from .render_html_styles import build_css, JS


def _calibration_effect_note(calibration: dict[str, Any]) -> str | None:
    if calibration.get("profile_read_mode") != "mirror_only":
        return None
    return (
        "Mirror-only policy surface: selected profile metadata is shown in this report, "
        "but authoritative scan scoring still follows deterministic runtime constants. "
        "Preview-only posture changes, including Stage 4 replication emphasis, do not "
        "change the formal score until a future read-through phase."
    )


def _nav() -> str:
    links = [
        ("#s1", "1. Summary"), ("#s2", "2. Score Matrix"),
        ("#s3", "3. Code Integrity"), ("#s4", "4. AIRI Coverage"),
        ("#s5", "5. Evidence"),
    ]
    items = "".join(f'<a href="{h}" class="nav-link">{l}</a>' for h, l in links)
    return f'<nav class="nav" aria-label="Report sections">{items}</nav>'


def _hero(score: dict, final: int, tier: str, tc: str, target: str, date: str) -> str:
    gauge = svg_gauge(final, tc)
    use_scope = xt(str(score.get("use_scope", "")))
    return (
        f'<header class="hero">'
        f'<div>{gauge}</div>'
        f'<div>'
        f'<div class="sub">STEM BIO-AI Local Audit &nbsp;|&nbsp; {date}</div>'
        f'<h1>{target}</h1>'
        f'<div class="tier">{xt(tier)}</div>'
        f'<p style="font-size:13px;color:rgba(255,255,255,.75);'
        f'max-width:520px;line-height:1.5;margin-top:6px">{use_scope}</p>'
        f'</div></header>'
    )


def _section1(result: dict, final: int, tc: str,
               s1: int, s2: int, s3: int, s4: int, t0: bool) -> str:
    alert = ""
    if t0:
        alert = (
            f'<div class="alert-t0">'
            f'T0 HARD FLOOR TRIGGERED &mdash; Clinical boundary declaration absent. '
            f'Score capped at {final}/100.</div>'
        )
    stats = "".join(
        f'<div class="stat-card">'
        f'<div class="stat-val" style="color:{c}">{v}</div>'
        f'<div class="stat-lbl">{l}</div></div>'
        for v, l, c in [
            (final, "Final Score", tc),
            (s1, "S1 Intent", _C["teal"]),
            (s2, "S2 Repo", _C["purple"]),
            (s3, "S3 Code/Bio", _C["slate"]),
            (s4, "S4 Replication", _C["green"]),
        ]
    )
    notable = "".join(
        f'<div class="risk-item">{xt(str(r))}</div>'
        for r in result.get("notable_risks", [])[:6]
    )
    notable_block = (
        f'<div style="margin-top:24px">'
        f'<h3 style="font-size:15px;font-weight:700;color:{_C["navy"]};margin-bottom:12px">'
        f'Notable Risks</h3>{notable}</div>'
        if notable else ""
    )
    calibration = result.get("calibration_profile", {})
    policy_name = xt(str(calibration.get("profile_name", "unknown")))
    policy_status = xt(str(calibration.get("profile_status", "unknown")))
    policy_mode = xt(str(calibration.get("profile_read_mode", "unknown")))
    calibration_note = _calibration_effect_note(calibration)
    policy_block = (
        f'<div class="panel" style="margin-top:20px;padding:14px 16px">'
        f'<div style="font-size:12px;font-weight:700;color:{_C["navy"]};margin-bottom:6px">'
        f'Policy Surface: {policy_name} ({policy_status}, {policy_mode})</div>'
        f'<div style="font-size:12px;line-height:1.55;color:{_C["dgray"]}">'
        f'{xt(calibration_note)}</div></div>'
        if calibration_note
        else ""
    )
    return (
        f'<section id="s1">'
        f'<h2 class="s-title">Executive Summary</h2>'
        f'{alert}'
        f'<div class="stats-grid">{stats}</div>'
        f'{policy_block}'
        f'{notable_block}'
        f'</section>'
    )


def _section2(s1: int, s2: int, s3: int, s4: int) -> str:
    stages = [
        ("Stage 1 &mdash; README Intent",      s1, _C["teal"],   0),
        ("Stage 2R &mdash; Repo Consistency",  s2, _C["purple"], 1),
        ("Stage 3 &mdash; Code / Bio",         s3, _C["slate"],  2),
        ("Stage 4 &mdash; Replication",        s4, _C["green"],  3),
    ]
    rows = ""
    for label, val, color, ti in stages:
        bar_color = _C["red"] if val < 40 else (_C["amber"] if val < 65 else color)
        rows += (
            f'<div class="stage-row">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;margin-bottom:6px">'
            f'<span style="font-size:13px;color:{_C["navy"]};font-weight:500;'
            f'display:flex;align-items:center;gap:6px">'
            f'{label}{tip_icon(_STAGE_TIPS[ti])}</span>'
            f'<span style="font-size:14px;font-weight:700;color:{bar_color}">'
            f'{val}</span></div>'
            f'{svg_hbar(val, 100, bar_color)}</div>'
        )
    score_tip = tip_icon(
        "Weighted formula: 40% README intent + 20% repo consistency + 40% code/bio. "
        "T0 hard floor (missing clinical disclaimer) caps score at 39/100 maximum."
    )
    return (
        f'<section id="s2">'
        f'<h2 class="s-title">Score Matrix {score_tip}</h2>'
        f'<div class="panel">'
        f'{rows}'
        f'<div class="formula">'
        f'Final = 0.4 &times; S1 + 0.2 &times; S2R + 0.4 &times; S3 &minus; C1_penalty'
        f' &nbsp;|&nbsp; T0 floor: max 39/100'
        f'</div></div></section>'
    )


def _section3(integrity: dict, cc: dict) -> str:
    combined: dict[str, Any] = {**integrity}
    for k, v in cc.items():
        if isinstance(v, dict):
            combined[k] = {
                "status": v.get("status", "PASS"),
                "evidence": [f"count={v.get('count', 0)}"],
            }
    cards = "".join(integrity_card(k, v) for k, v in combined.items() if isinstance(v, dict))
    hint = tip_icon(
        "C1-C4: static code checks (credentials, dependencies, deprecated paths, exceptions). "
        "CC1-CC3: Layer 2 AST contract detectors. Click any card to expand evidence."
    )
    return (
        f'<section id="s3">'
        f'<h2 class="s-title">Code Integrity &amp; Contract {hint}</h2>'
        f'<div class="card-grid">{cards}</div>'
        f'</section>'
    )


def _section4(airi: dict) -> str:
    if not airi or "covered_risks" not in airi:
        return ""
    pct       = float(airi.get("coverage_rate", 0))
    covered_n = int(airi.get("covered_count", 0))
    total_n   = int(airi.get("total_risks_in_detector_scope", 0))
    gaps      = airi.get("known_gaps", [])
    all_risks = airi.get("covered_risks", [])
    donut     = svg_donut(pct, _C["green"], 90)

    # Count covered risks per AIRI domain (first digit of subdomain_id)
    domain_counts: dict[int, int] = {d: 0 for d in range(1, 8)}
    for r in all_risks:
        try:
            d = int(str(r.get("subdomain_id", "0")).split(".")[0])
            if d in domain_counts:
                domain_counts[d] += 1
        except (ValueError, IndexError):
            pass
    domain_boxes = "".join(domain_card(d, domain_counts[d]) for d in range(1, 8))

    c_rows = "".join(airi_row(r, "covered") for r in all_risks[:24])
    g_rows = "".join(airi_row(g, "gap") for g in gaps)
    toggle = (
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap">'
        f'<div class="toggle-group">'
        f'<button class="toggle-btn" data-view="covered"'
        f' onclick="airiToggle(\'covered\')">Covered ({covered_n})</button>'
        f'<button class="toggle-btn" data-view="gaps"'
        f' onclick="airiToggle(\'gaps\')">Gaps ({len(gaps)})</button>'
        f'</div>'
        f'<span style="font-size:11px;color:{_C["dgray"]}">Click a domain to filter</span>'
        f'</div>'
    )
    table = (
        f'<div style="overflow-x:auto"><table class="airi-table">'
        f'<thead><tr><th>ID</th><th>Risk</th><th>Domain</th>'
        f'<th>Covered by / Note</th></tr></thead>'
        f'<tbody>{c_rows}{g_rows}</tbody></table></div>'
    )
    src  = xt(airi.get("airi_version", ""))
    bundle_scope = xt(airi.get("airi_bundle_scope", ""))
    snapshot = xt(airi.get("airi_upstream_snapshot_date", ""))
    license_name = xt(airi.get("airi_upstream_license", ""))
    attribution = xt(airi.get("airi_attribution_note", ""))
    hint = tip_icon(
        "Coverage rate = risks addressed / total risks in detector scope. "
        "Gaps are AIRI risks present in scope but not yet covered by any detector. "
        "The HTML report uses the curated runtime AIRI bundle, not the full upstream registry."
    )
    return (
        f'<section id="s4">'
        f'<h2 class="s-title">MIT AI Risk Repository Coverage {hint}'
        f'<span style="font-size:12px;color:{_C["dgray"]};font-weight:400;margin-left:4px">'
        f'{src} | airisk.mit.edu</span></h2>'
        f'<div class="panel">'
        f'<div style="display:flex;gap:28px;align-items:flex-start;'
        f'flex-wrap:wrap;margin-bottom:20px">'
        f'<div style="text-align:center;flex-shrink:0">{donut}'
        f'<div style="font-size:13px;font-weight:600;color:{_C["navy"]};margin-top:8px">'
        f'{covered_n} / {total_n}</div>'
        f'<div style="font-size:11px;color:{_C["dgray"]}">risks in scope</div></div>'
        f'<div style="flex:1;min-width:240px">'
        f'<p style="font-size:12px;color:{_C["dgray"]};margin-bottom:14px;line-height:1.5">'
        f'Risks addressed by STEM-BIO-AI detectors across the AIRI V4 '
        f'curated runtime bundle. Click a domain card to filter. Toggle covered/gaps.'
        f'</p>'
        f'<p style="font-size:11px;color:{_C["dgray"]};margin-bottom:0;line-height:1.5">'
        f'Bundle scope: {bundle_scope} | snapshot: {snapshot} | license: {license_name}<br>'
        f'{attribution}'
        f'</p></div></div>'
        f'<div class="domain-grid">{domain_boxes}</div>'
        f'{toggle}{table}'
        f'</div></section>'
    )


def _section5(evidence_ledger: list) -> str:
    if not evidence_ledger:
        return (
            f'<section id="s5"><h2 class="s-title">Evidence Detail</h2>'
            f'<div class="panel" style="color:{_C["dgray"]};font-size:13px">'
            f'No evidence entries collected.</div></section>'
        )
    n = len(evidence_ledger)
    chips = " ".join(
        f'<span class="filter-chip{" active" if i == 0 else ""}"'
        f' data-sev="{s}" onclick="filterEv(\'{s}\')">{l}</span>'
        for i, (s, l) in enumerate([
            ("all", f"All ({n})"),
            ("fail", "FAIL"), ("warn", "WARN"), ("pass", "PASS"), ("info", "INFO"),
        ])
    )
    rows = "".join(evidence_row(ev) for ev in evidence_ledger[:200])
    hint = tip_icon(
        "Full evidence ledger from all detectors. "
        "Filter by severity. Capped at 200 entries in HTML view."
    )
    th = f'style="padding:8px 5px;font-size:11px;text-align:left;color:{_C["dgray"]}"'
    return (
        f'<section id="s5">'
        f'<h2 class="s-title">Evidence Detail {hint}</h2>'
        f'<div class="panel">'
        f'<div style="margin-bottom:14px">{chips}</div>'
        f'<div style="overflow-x:auto">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr style="background:{_C["lgray"]}">'
        f'<th style="padding:8px 5px;width:16px"></th>'
        f'<th {th}>SEV</th><th {th}>Detector</th>'
        f'<th {th}>Finding</th><th {th}>File</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody></table></div></div></section>'
    )


def render_html(result: dict[str, Any]) -> str:
    score  = result["score"]
    final  = int(score["final_score"])
    tier   = str(score["formal_tier"])
    tc     = tier_color(tier)
    target = xt(str(result["target"]["name"]))
    date   = xt(str(result.get("generated_at_local", "")))
    s1 = int(score.get("stage_1_readme_intent", 0))
    s2 = int(score.get("stage_2_repo_local_consistency", 0))
    s3 = int(score.get("stage_3_code_bio", 0))
    s4 = int(result.get("replication_score", 0))
    t0 = result.get("classification", {}).get("t0_hard_floor", False)

    css    = build_css(tc)
    nav    = _nav()
    hero   = _hero(score, final, tier, tc, target, date)
    sec1   = _section1(result, final, tc, s1, s2, s3, s4, t0)
    sec2   = _section2(s1, s2, s3, s4)
    sec3   = _section3(result.get("code_integrity", {}), result.get("code_contract", {}))
    sec4   = _section4(result.get("airi_risk_coverage", {}))
    sec5   = _section5(result.get("evidence_ledger", []))
    ver    = xt(result.get("stem_ai_version", ""))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>STEM BIO-AI &mdash; {target}</title>
<style>{css}</style>
</head>
<body>
{nav}
{hero}
<div class="content">
{sec1}
{sec2}
{sec3}
{sec4}
{sec5}
<div class="footer">
  STEM BIO-AI Local CLI Scan &nbsp;|&nbsp; {ver}
  &nbsp;|&nbsp; Deterministic surface scan &mdash; no LLM, network, or runtime execution.
</div>
</div>
<script>{JS}</script>
</body>
</html>"""
