"""Interactive HTML report renderer for STEM BIO-AI.

Sections: Executive Summary | Decision Path | Code Integrity | AIRI Risk Triggers | Evidence Detail
Self-contained: inline CSS + SVG + JS, zero external dependencies.
"""
from __future__ import annotations

from typing import Any

from .render_html_components import (
    _C,
    _STAGE_TIPS,
    REQ_LABELS,
    REQ_STATUS_BADGE,
    xt,
    tier_color,
    tip_icon,
    svg_gauge,
    svg_donut,
    svg_hbar,
    integrity_card,
    domain_card,
    airi_row,
    evidence_row,
)
from .render_html_styles import build_css, JS


def _compress_evidence_for_html(evidence_ledger: list[dict[str, Any]], limit: int = 200) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    grouped_order: list[tuple[str, str, str]] = []

    for ev in evidence_ledger[:limit]:
        severity = str(ev.get("severity", ev.get("status", "INFO"))).upper()
        detector = str(ev.get("detector", ev.get("check", "")))
        file_path = str(ev.get("file", ev.get("path", "")))
        line = int(ev.get("line", 0) or 0)
        message = str(ev.get("message") or ev.get("detail") or ev.get("explanation") or "").strip()

        if severity in {"INFO", "WARN", "PASS"} and detector and file_path and file_path != "." and message:
            key = (severity, detector, file_path, message)
            if key not in grouped:
                grouped[key] = {
                    "severity": severity.lower(),
                    "status": severity.lower(),
                    "detector": detector,
                    "file": file_path,
                    "line": line,
                    "snippet": ev.get("snippet", ""),
                    "message": message,
                    "aggregate_count": 1,
                    "aggregate_lines": [line] if line else [],
                }
                grouped_order.append(key)
            else:
                grouped[key]["aggregate_count"] += 1
                if line and line not in grouped[key]["aggregate_lines"]:
                    grouped[key]["aggregate_lines"].append(line)
            continue

        compact.append(ev)

    for key in grouped_order:
        group = grouped[key]
        count = int(group.get("aggregate_count", 1))
        lines = sorted(group.get("aggregate_lines", []))
        if count > 1:
            base = str(group.get("message") or "Repeated informational evidence detected.").strip()
            if lines:
                line_preview = ", ".join(str(n) for n in lines[:6])
                if len(lines) > 6:
                    line_preview += ", ..."
                group["message"] = f"{base} Aggregated {count} matches from one file (lines: {line_preview})."
            else:
                group["message"] = f"{base} Aggregated {count} matches from one file."
            group["snippet"] = ""
        compact.append(group)

    return compact


def _calibration_effect_note(calibration: dict[str, Any]) -> str | None:
    if calibration.get("profile_read_mode") != "mirror_only":
        return None
    return (
        "Mirror-only policy surface: selected profile metadata is shown in this report, "
        "but authoritative scan scoring still follows deterministic runtime constants. "
        "Preview-only posture changes, including Stage 4 replication emphasis, do not "
        "change the formal score until a future read-through phase."
    )


def _score_boundary_html() -> str:
    return (
        f'<article class="memo-card" style="grid-column:1 / -1">'
        f'<div class="eyebrow">&#9888; About This Score</div>'
        f'<h3>How to read the number</h3>'
        f'<p class="memo-text"><strong>Score reflects calculation integrity, not calibrated validity. Triage signal only.</strong></p>'
        f'<ul class="memo-list">'
        f'<li><strong>What is verified:</strong> calculation integrity. The same input produces the same score.</li>'
        f'<li><strong>What is not verified:</strong> calibrated measurement validity. Weights and detector scope remain bounded.</li>'
        f'<li><strong>Use this score as a triage signal</strong>, not as certification, safety proof, or deployment approval.</li>'
        f'</ul>'
        f'</article>'
    )


def _nav(ver: str) -> str:
    links = [
        ("#s1", "1. Summary"),
        ("#s2", "2. Decision Path"),
        ("#s3", "3. Code Integrity"),
        ("#s6", "4. Regulatory"),
        ("#s4", "5. AIRI Risk Triggers"),
        ("#s5", "6. Evidence"),
        ("#s7", "7. Developer"),
    ]
    items = "".join(f'<a href="{h}" class="nav-link">{l}</a>' for h, l in links)
    return (
        f'<nav class="nav" aria-label="Report sections">'
        f'<div class="nav-links">{items}</div>'
        f'<div class="nav-brand"><strong>STEM-BIO-AI</strong><span>STEM BIO-AI Local CLI Scan &nbsp;|&nbsp; {ver}</span></div>'
        f'</nav>'
    )


def _hero_accent(tc: str) -> str:
    if tc == _C["red"]:
        return "#D65D6D"
    if tc == _C["amber"]:
        return "#D28F22"
    if tc == _C["green"]:
        return "#2A8A56"
    return "#3B86BE"


def _hero(score: dict, final: int, tier: str, tc: str, target: str, date: str) -> str:
    gauge = svg_gauge(final, _hero_accent(tc))
    use_scope = xt(str(score.get("use_scope", "")))
    remote = xt(str(score.get("_target_remote", "")))
    title = (
        f'<a href="{remote}" class="hero-link" target="_blank" rel="noopener noreferrer">{target}</a>'
        if remote
        else target
    )
    return (
        f'<header class="hero">'
        f'<div class="hero-left"><div class="hero-gauge-card">{gauge}</div></div>'
        f'<div class="hero-right">'
        f'<div class="eyebrow">STEM BIO-AI Local Audit &nbsp;|&nbsp; {date}</div>'
        f'<h1>{title}</h1>'
        f'<div class="hero-meta">'
        f'<span class="tier">{xt(tier)}</span>'
        f'<span class="hero-chip">Deterministic local scan</span>'
        f'<span class="hero-chip">No LLM / no network / no runtime execution</span>'
        f'</div>'
        f'<p class="lede">{use_scope}</p>'
        f'</div></header>'
    )


def _iter_rubric_rows(rubric: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, info in rubric.items():
        if key.endswith("raw_total") or key == "baseline":
            continue
        if not isinstance(info, dict):
            continue
        score = info.get("score")
        max_score = info.get("max")
        if score is None:
            continue
        rows.append(
            {
                "key": key,
                "score": int(score),
                "max": int(max_score) if isinstance(max_score, (int, float)) else None,
                "evidence": xt(str(info.get("evidence", ""))),
                "detector_id": xt(str(info.get("detector_id", ""))) if info.get("detector_id") else "",
                "decision_basis": xt(str(info.get("decision_basis", ""))) if info.get("decision_basis") else "",
                "tier_impact": xt(str(info.get("tier_impact", ""))) if info.get("tier_impact") else "",
            }
        )
    return rows


def _select_focus_rows(
    rubric: dict[str, Any],
    *,
    negatives_first: bool = True,
    limit: int = 4,
) -> list[dict[str, Any]]:
    rows = [r for r in _iter_rubric_rows(rubric) if r["score"] != 0]
    if negatives_first:
        negatives = sorted([r for r in rows if r["score"] < 0], key=lambda r: abs(r["score"]), reverse=True)
        positives = sorted([r for r in rows if r["score"] > 0], key=lambda r: abs(r["score"]), reverse=True)
        return (negatives + positives)[:limit]
    return sorted(rows, key=lambda r: abs(r["score"]), reverse=True)[:limit]


def _rubric_focus_list(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return '<li class="focus-line muted">No scored rubric movement surfaced.</li>'
    items = ""
    for row in rows:
        sc = row["score"]
        sign = "+" if sc > 0 else ""
        detector_id = str(row.get("detector_id", "")).strip()
        key = str(row.get("key", "")).strip()
        detail = str(row["decision_basis"] or row["evidence"]).strip()
        if detector_id and detail.startswith(detector_id):
            detail = detail[len(detector_id):].lstrip(" :|-")
        detector = (
            f'<span class="focus-detector">{detector_id}</span> '
            if detector_id and detector_id != key else ""
        )
        if row.get("tier_impact"):
            detail = f'{detail} | tier impact: {row["tier_impact"]}'
        items += (
            f'<li class="focus-line">'
            f'<div class="focus-top"><span class="focus-key">{xt(key)}</span>'
            f'<span class="focus-score">{sign}{sc}</span></div>'
            f'<div class="focus-detail">{detector}{detail}</div>'
            f'</li>'
        )
    return items


def _code_integrity_summary(integrity: dict[str, Any]) -> tuple[list[tuple[str, dict[str, Any]]], list[tuple[str, dict[str, Any]]]]:
    warnings: list[tuple[str, dict[str, Any]]] = []
    clear: list[tuple[str, dict[str, Any]]] = []
    for key, info in integrity.items():
        if not isinstance(info, dict):
            continue
        if str(info.get("status", "PASS")).upper() == "PASS":
            clear.append((key, info))
        else:
            warnings.append((key, info))
    return warnings, clear


def _section1(result: dict[str, Any], final: int, tc: str,
              s1: int, s2: int, s3: int, s4: int, t0: bool,
              score_cap: int | None = None) -> str:
    score = result["score"]
    calibration = result.get("calibration_profile", {})
    cls = result.get("classification", {})
    freshness = result.get("audit_freshness", {})
    policy_name = xt(str(calibration.get("profile_name", "unknown")))
    policy_status = xt(str(calibration.get("profile_status", "unknown")))
    policy_mode = xt(str(calibration.get("profile_read_mode", "unknown")))
    calibration_note = _calibration_effect_note(calibration)
    ca_severity = cls.get("ca_severity", "none")
    tier_lock = "T0-FLOOR" if t0 else (f"CA-CAP @{score_cap}" if score_cap is not None else "clear")

    stats = "".join(
        f'<div class="metric-card">'
        f'<div class="metric-value" style="color:{c}">{v}</div>'
        f'<div class="metric-label">{l}</div>'
        f'</div>'
        for v, l, c in [
            (final, "Final Score", tc),
            (s1, "S1 Intent", _C["teal"]),
            (s2, "S2 Repo", _C["purple"]),
            (s3, "S3 Code/Bio", _C["slate"]),
            (s4, "S4 Replication", _C["green"]),
        ]
    )
    risks = result.get("notable_risks", [])[:5]
    positives = result.get("notable_positive_evidence", [])[:4]
    if t0:
        alert = (
            f'<div class="alert-t0">'
            f'<strong>Tier Lock [T0-FLOOR]:</strong> This report does not allow clinical trust. '
            f'The repository presents direct clinical framing without a clear safety boundary. '
            f'Current ceiling: 39. A clear non-clinical boundary is required before any tier advancement.'
            f'</div>'
        )
    elif score_cap is not None:
        alert = (
            f'<div class="alert-t0" style="background:#fff3cd;border-color:#ffc107;color:#856404;">'
            f'<strong>Tier Lock [CA-CAP]:</strong> This repository can be explored, but the report will stop at T2 '
            f'until the project clearly says it is not for clinical or diagnostic use. '
            f'Current ceiling: {score_cap}. Add an explicit non-diagnostic boundary to remove this cap.'
            f'</div>'
        )
    else:
        alert = ""
    risk_list = "".join(f'<li>{xt(str(r))}</li>' for r in risks) or "<li>No notable risks surfaced.</li>"
    positive_list = "".join(f'<li>{xt(str(p))}</li>' for p in positives) or "<li>No notable positive evidence surfaced.</li>"
    policy_card = (
        f'<article class="memo-card" style="grid-column:1 / -1">'
        f'<div class="eyebrow">Policy Boundary</div>'
        f'<h3>How to read this artifact</h3>'
        f'<p class="memo-text">{xt(calibration_note) if calibration_note else "Authoritative scoring and surfaced policy metadata are aligned in this release line."}</p>'
        f'<ul class="memo-list">'
        f'<li><strong>Classification applied:</strong> ca_severity={xt(ca_severity)}</li>'
        f'<li><strong>Score cap:</strong> {xt(str(score_cap)) if score_cap is not None else "none"}</li>'
        f'<li><strong>Tier lock:</strong> {xt(tier_lock)}</li>'
        f'<li><strong>Practical meaning:</strong> the report can cap the tier when the repository sounds clinically adjacent but does not state a clear non-clinical boundary.</li>'
        f'</ul>'
        f'</article>'
    )
    return (
        f'<section id="s1">'
        f'<h2 class="s-title">Executive Summary</h2>'
        f'{alert}'
        f'<div class="metric-grid">{stats}</div>'
        f'<div class="memo-grid">'
        f'<article class="memo-card memo-primary">'
        f'<div class="eyebrow">TL;DR</div>'
        f'<h3>Decision memo</h3>'
        f'<p class="memo-text">This repository lands at <strong>{xt(str(score.get("formal_tier", "")))}</strong> '
        f'with a final score of <strong>{final}/100</strong>. The result is driven more by '
        f'boundary, workflow-support, and governance weaknesses than by classic code-pattern failures.</p>'
        f'<div class="pill-row"><span class="pill">Policy: {policy_name}</span>'
        f'<span class="pill">Status: {policy_status}</span>'
        f'<span class="pill">Mode: {policy_mode}</span></div>'
        f'</article>'
        f'<article class="memo-card">'
        f'<div class="eyebrow">Primary Risks</div>'
        f'<h3>What pushed the review down</h3>'
        f'<ul class="memo-list">{risk_list}</ul>'
        f'</article>'
        f'<article class="memo-card">'
        f'<div class="eyebrow">Positive Evidence</div>'
        f'<h3>What still supports reviewability</h3>'
        f'<ul class="memo-list">{positive_list}</ul>'
        f'</article>'
        f'<article class="memo-card">'
        f'<div class="eyebrow">Freshness</div>'
        f'<h3>When to re-check</h3>'
        f'<p class="memo-text">Review after <strong>{xt(str(freshness.get("review_after_days", "n/a")))}</strong> days. '
        f'Expires on <strong>{xt(str(freshness.get("expires_on", "unknown")))}</strong>.</p>'
        f'<p class="memo-note">Change-triggered re-audit now: '
        f'{xt(str(freshness.get("change_triggered_reaudit_recommended_now", False)))}</p>'
        f'</article>'
        f'</div>'
        f'<div style="margin-top:18px">{_score_boundary_html()}</div>'
        f'<div style="margin-top:18px">{policy_card}</div>'
        f'</section>'
    )


def _stage_card(title: str, value: int, color: str, tip: str, focus_rows: list[dict[str, Any]], summary: str) -> str:
    bar_color = _C["red"] if value < 40 else (_C["amber"] if value < 65 else color)
    return (
        f'<article class="stage-card">'
        f'<div class="stage-card-top">'
        f'<div class="stage-name">{title} {tip_icon(tip)}</div>'
        f'<div class="stage-value" style="color:{bar_color}">{value}</div>'
        f'</div>'
        f'{svg_hbar(value, 100, bar_color)}'
        f'<p class="stage-summary">{xt(summary)}</p>'
        f'<ul class="focus-list">{_rubric_focus_list(focus_rows)}</ul>'
        f'</article>'
    )


def _config_pattern_card() -> str:
    return (
        f'<div class="config-pattern">'
        f'<div class="config-copy">'
        f'<div class="eyebrow">Configured, Not Rewritten</div>'
        f'<h3 class="subhead">Changing review posture does not require touching the score core</h3>'
        f'<p class="memo-text">Use <code>stem policy simulate</code> with a governed profile file when you want to preview a different review posture. '
        f'The authoritative score path stays deterministic; the profile is surfaced as metadata and preview-only interpretation.</p>'
        f'<p class="memo-note">If you only need the default posture, you do not need a profile file at all.</p>'
        f'</div>'
        f'<div class="config-grid">'
        f'<article class="config-card">'
        f'<div class="config-label">profile.json</div>'
        f'<pre class="config-code">{{\n  "profile_name": "strict_clinical_adjacency",\n  "profile_read_mode": "mirror_only"\n}}</pre>'
        f'</article>'
        f'<article class="config-card">'
        f'<div class="config-label">command</div>'
        f'<pre class="config-code">stem policy simulate /path/to/repo --profile-file profile.json</pre>'
        f'</article>'
        f'<article class="config-card">'
        f'<div class="config-label">artifact note</div>'
        f'<pre class="config-code">Calibration Effect: mirror-only\nPolicy metadata surfaced\nFormal score unchanged</pre>'
        f'</article>'
        f'</div>'
        f'</div>'
    )


def _section2(result: dict[str, Any], s1: int, s2: int, s3: int, s4: int) -> str:
    stage1_focus = _select_focus_rows(result.get("stage_1_rubric", {}), negatives_first=True, limit=4)
    stage2_focus = _select_focus_rows(result.get("stage_2r_rubric", {}), negatives_first=True, limit=4)
    stage3_focus = _select_focus_rows(result.get("stage_3_rubric", {}), negatives_first=False, limit=4)
    stage4_focus = _select_focus_rows(result.get("stage_4_rubric", {}), negatives_first=False, limit=4)
    _s3r = result.get("stage_3_rubric", {}).get("stage_3_raw_total", {})
    _s3_normalized = result.get("score", {}).get("stage_3_code_bio")
    if _s3r.get("score") is not None and _s3r.get("max"):
        _s3_formula = f" (raw: {_s3r['score']}/{_s3r['max']}"
        if isinstance(_s3_normalized, (int, float)):
            _s3_formula += f" -> normalized: {int(round(_s3_normalized))}"
        _s3_formula += ")"
    else:
        _s3_formula = ""
    cards = "".join([
        _stage_card(
            "Stage 1 — README Intent",
            s1,
            _C["teal"],
            _STAGE_TIPS[0],
            stage1_focus,
            "Claim language, limitation posture, and clinical boundary wording.",
        ),
        _stage_card(
            "Stage 2R — Repo Consistency",
            s2,
            _C["purple"],
            _STAGE_TIPS[1],
            stage2_focus,
            "Internal contradictions between README, workflow claims, and support surfaces.",
        ),
        _stage_card(
            "Stage 3 — Code / Bio Responsibility",
            s3,
            _C["slate"],
            _STAGE_TIPS[2],
            stage3_focus,
            f"Engineering accountability, provenance, and reviewable responsibility surfaces.{_s3_formula}",
        ),
        _stage_card(
            "Stage 4 — Replication",
            s4,
            _C["green"],
            _STAGE_TIPS[3],
            stage4_focus,
            "Reproducibility evidence is reported separately and does not alter the formal tier.",
        ),
    ])
    formula_tip = tip_icon(
        "Final = 0.4 × S1 + 0.2 × S2R + 0.4 × S3 − C1_penalty  |  Stage 4 remains a separate replication lane."
    )
    return (
        f'<section id="s2">'
        f'<h2 class="s-title">Decision Path {formula_tip}</h2>'
        f'<div class="panel decision-panel">'
        f'{_config_pattern_card()}'
        f'<div class="stage-deck">{cards}</div>'
        f'</div></section>'
    )


def _section3(integrity: dict, cc: dict) -> str:
    combined: dict[str, Any] = {**integrity}
    for k, v in cc.items():
        if isinstance(v, dict):
            combined[k] = {
                "status": v.get("status", "PASS"),
                "evidence": [f"count={v.get('count', 0)}"],
            }
    warn_pairs, pass_pairs = _code_integrity_summary(combined)
    warning_cards = "".join(integrity_card(k, v) for k, v in warn_pairs)
    pass_cards = "".join(integrity_card(k, v) for k, v in pass_pairs)
    warning_fallback = '<p class="memo-text">No WARN/FAIL lanes surfaced.</p>'
    hint = tip_icon(
        "C1-C6: static code and governance checks. CC1-CC3: Layer 2 AST contract detectors. "
        "PASS means no mapped trigger was detected in the current rule scope, not that the whole repository is mature."
    )
    faq = (
        f'<div class="faq-block">'
        f'<details class="faq-item"><summary>Why can Code Integrity contain PASS while the overall score is still low?</summary>'
        f'<p>Because Code Integrity is a narrow detector family. The formal score is still driven mainly by Stage 1, Stage 2R, and Stage 3 evidence posture.</p></details>'
        f'<details class="faq-item"><summary>What changed in the C4 / C5 / C6 split?</summary>'
        f'<p>C4 is now reserved for executable fail-open exception behavior, C5 for unsupported compliance or boundary integrity claims, and C6 for mock-auth or no-auth trust-boundary signals.</p></details>'
        f'</div>'
    )
    return (
        f'<section id="s3">'
        f'<h2 class="s-title">Code Integrity &amp; Contract {hint}</h2>'
        f'<div class="integrity-stack">'
        f'<div class="panel">'
        f'<div class="eyebrow">Warnings First</div>'
        f'<h3 class="subhead">Mapped risk lanes that fired</h3>'
        f'<div class="card-grid">{warning_cards or warning_fallback}</div>'
        f'</div>'
        f'<div class="panel">'
        f'<div class="eyebrow">Clear Lanes</div>'
        f'<h3 class="subhead">What stayed quiet in the current rule scope</h3>'
        f'<div class="card-grid">{pass_cards}</div>'
        f'{faq}'
        f'</div>'
        f'</div></section>'
    )


def _section4(airi: dict) -> str:
    if not airi or "covered_risks" not in airi:
        return ""
    pct = float(airi.get("coverage_rate", 0))
    covered_n = int(airi.get("covered_count", 0))
    total_n = int(airi.get("total_risks_in_detector_scope", 0))
    gaps = airi.get("known_gaps", [])
    all_risks = airi.get("covered_risks", [])
    donut = svg_donut(pct, _C["green"], 98)

    covered_counts: dict[int, int] = {d: 0 for d in range(1, 8)}
    gap_counts: dict[int, int] = {d: 0 for d in range(1, 8)}
    for r in all_risks:
        try:
            d = int(str(r.get("subdomain_id", "0")).split(".")[0])
            if d in covered_counts:
                covered_counts[d] += 1
        except (ValueError, IndexError):
            continue
    for g in gaps:
        try:
            d = int(str(g.get("subdomain_id", "0")).split(".")[0])
            if d in gap_counts:
                gap_counts[d] += 1
        except (ValueError, IndexError):
            continue
    domain_boxes = domain_card(0, covered_n, len(gaps))
    domain_boxes += "".join(domain_card(d, covered_counts[d], gap_counts[d]) for d in range(1, 8))

    c_rows = "".join(airi_row(r, "covered") for r in all_risks[:24])
    g_rows = "".join(airi_row(g, "gap") for g in gaps)
    toggle = (
        f'<div class="toggle-row">'
        f'<div class="toggle-group">'
        f'<button class="toggle-btn" data-view="covered" onclick="airiToggle(\'covered\')">Covered ({covered_n})</button>'
        f'<button class="toggle-btn" data-view="gaps" onclick="airiToggle(\'gaps\')">Gaps ({len(gaps)})</button>'
        f'</div>'
        f'<span class="muted-note">Click a domain card to filter. Counts are shown as covered / gaps.</span>'
        f'</div>'
    )
    table = (
        f'<div style="overflow-x:auto"><table class="airi-table">'
        f'<thead><tr><th>ID</th><th>Risk</th><th>Domain</th><th>Covered by / Note</th></tr></thead>'
        f'<tbody>{c_rows}{g_rows}</tbody></table></div>'
    )
    src = xt(airi.get("airi_version", ""))
    bundle_scope = xt(airi.get("airi_bundle_scope", ""))
    snapshot = xt(airi.get("airi_upstream_snapshot_date", ""))
    license_name = xt(airi.get("airi_upstream_license", ""))
    attribution = xt(airi.get("airi_attribution_note", ""))
    hint = tip_icon(
        "Coverage counts only risks reached through local detector mappings. "
        "Coverage is not a safety verdict, and unmapped review concerns remain outside the numerator."
    )
    faq = (
        f'<div class="faq-block" style="margin-top:18px">'
        f'<details class="faq-item"><summary>What does 7 / 32 mean?</summary>'
        f'<p>It means seven AIRI risk IDs are currently reached by active local detector mappings, out of thirty-two AIRI risk IDs in the current detector scope.</p></details>'
        f'<details class="faq-item"><summary>What does “why mapped” mean?</summary>'
        f'<p>Each covered AIRI row carries a bounded explanation built from the triggered detector, the local mapping justification, and the trigger reason surfaced by the scan.</p></details>'
        f'<details class="faq-item"><summary>What does AIRI not prove here?</summary>'
        f'<p>AIRI does not independently verify harm, causality, clinical failure, or legal noncompliance. It is a risk-vocabulary layer around local findings.</p></details>'
        f'</div>'
    )
    mapping_pattern = (
        f'<div class="config-pattern" style="margin-top:18px">'
        f'<div class="config-copy">'
        f'<div class="eyebrow">Mapped, Not Guessed</div>'
        f'<h3 class="subhead">AIRI rows light up through active detector mappings</h3>'
        f'<p class="memo-text">The report does not infer AIRI coverage from prose alone. '
        f'Coverage appears when a local detector fires and a governed mapping exists in the current AIRI runtime bundle.</p>'
        f'</div>'
        f'<div class="config-grid">'
        f'<article class="config-card">'
        f'<div class="config-label">trigger</div>'
        f'<pre class="config-code">C6_mock_auth_or_fail_open_boundary\nstatus: detected</pre>'
        f'</article>'
        f'<article class="config-card">'
        f'<div class="config-label">mapping</div>'
        f'<pre class="config-code">R2R_D5_single_external_service_dependency\n→ 72.04.02 Market Concentration</pre>'
        f'</article>'
        f'<article class="config-card">'
        f'<div class="config-label">report surface</div>'
        f'<pre class="config-code">covered_by: detector id\nwhy: bounded mapping reason</pre>'
        f'</article>'
        f'</div>'
        f'</div>'
    )
    return (
        f'<section id="s4">'
        f'<h2 class="s-title">MIT AI Risk Repository Risk Triggers {hint}<span class="airi-tag">{src} | airisk.mit.edu</span></h2>'
        f'<div class="airi-stack">'
        f'<div class="panel">'
        f'<div class="eyebrow">Feature Explainer</div>'
        f'<h3 class="subhead">What this section is doing</h3>'
        f'<p class="memo-text">AIRI is used here as a bounded risk-vocabulary layer around deterministic repository findings. '
        f'The report uses the curated runtime bundle, not the full upstream AIRI universe.</p>'
        f'<div class="airi-kpi">'
        f'<div class="airi-donut">{donut}</div>'
        f'<div class="airi-copy">'
        f'<div class="metric-inline"><strong>{covered_n} / {total_n}</strong> risks in detector scope</div>'
        f'<div class="metric-inline">Bundle scope: <strong>{bundle_scope}</strong></div>'
        f'<div class="metric-inline">Snapshot: <strong>{snapshot}</strong> | License: <strong>{license_name}</strong></div>'
        f'<p class="memo-note">{attribution}</p>'
        f'</div></div>'
        f'{faq}'
        f'{mapping_pattern}'
        f'</div>'
        f'<div class="panel">'
        f'<div class="eyebrow">Coverage Explorer</div>'
        f'<h3 class="subhead">Covered and gap rows</h3>'
        f'<div class="domain-grid">{domain_boxes}</div>'
        f'{toggle}{table}'
        f'</div>'
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
    display_rows = _compress_evidence_for_html(evidence_ledger, limit=200)
    shown = len(display_rows)
    chips = " ".join(
        f'<span class="filter-chip{" active" if i == 0 else ""}" data-sev="{s}" onclick="filterEv(\'{s}\')">{l}</span>'
        for i, (s, l) in enumerate(
            [
                ("all", f"All ({n})"),
                ("fail", "FAIL"),
                ("warn", "WARN"),
                ("pass", "PASS"),
                ("info", "INFO"),
            ]
        )
    )
    rows = "".join(evidence_row(ev) for ev in display_rows)
    hint = tip_icon(
        "Full evidence ledger from all detectors. Filter by severity. Capped at 200 entries in HTML view."
    )
    compact_note = ""
    if shown < min(n, 200):
        compact_note = (
            f'<div class="muted" style="margin:0 0 10px 0">'
            f'Showing {shown} compact rows from the first {min(n, 200)} evidence entries.'
            f'</div>'
        )
    th = f'style="padding:8px 5px;font-size:11px;text-align:left;color:{_C["dgray"]}"'
    return (
        f'<section id="s5">'
        f'<h2 class="s-title">Evidence Detail {hint}</h2>'
        f'<div class="panel">'
        f'<div class="toggle-row" style="margin-bottom:14px">{chips}</div>'
        f'{compact_note}'
        f'<div style="overflow-x:auto">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr style="background:{_C["lgray"]}">'
        f'<th style="padding:8px 5px;width:16px"></th>'
        f'<th {th}>SEV</th><th {th}>Detector</th><th {th}>Finding</th><th {th}>File</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody></table></div></div></section>'
    )


def _section6(result: dict[str, Any]) -> str:
    """Regulatory Traceability — actionable per-requirement breakdown."""
    basis = result.get("regulatory_basis", {})
    traceability = result.get("stage_traceability", {})
    if not basis and not traceability:
        return ""
    note = basis.get("note", {})
    body1 = xt(note.get("body_line_1", ""))
    body2 = xt(note.get("body_line_2", ""))
    hint = tip_icon(
        "Traceability maps detector findings to specific regulatory article or guideline requirements. "
        "Signal only = relevant evidence was found but is insufficient to confirm alignment. "
        "Partially aligned = structural evidence exists; gaps remain. "
        "Not assessed items are outside the current scan scope."
    )

    # Basis note box
    review_warn = ""
    if basis.get("review_required"):
        reasons = xt(", ".join(basis.get("review_reasons", [])))
        review_warn = (
            f'<div class="reg-review-warn">&#9888; Registry review required: {reasons}</div>'
        )

    basis_box = (
        f'<div class="reg-basis-box">'
        f'<div class="reg-basis-title">{xt(note.get("title", "Regulatory basis note"))}</div>'
        f'<div class="reg-basis-body">{body1}</div>'
        f'<div class="reg-basis-note">{body2}</div>'
        f'{review_warn}'
        f'</div>'
    )

    # Per-stage traceability rows
    stage_blocks = ""
    _STAGE_LABELS = {
        "stage_1": "Stage 1 — README Intent",
        "stage_2r": "Stage 2R — Repo Consistency",
        "stage_3": "Stage 3 — Code / Bio Responsibility",
        "stage_4": "Stage 4 — Replication",
        "bio_diagnostics": "Bio Diagnostics",
    }
    for stage_key in ("stage_1", "stage_2r", "stage_3", "stage_4", "bio_diagnostics"):
        items = traceability.get(stage_key, [])
        if not items:
            continue
        rows_html = ""
        for item in items:
            req_id = item["requirement_id"]
            label = xt(REQ_LABELS.get(req_id, req_id))
            badge = REQ_STATUS_BADGE.get(item["status"], xt(item["status"]))
            src_chips = "".join(
                f'<span class="reg-src-chip">{xt(s)}</span>'
                for s in item.get("source_ids", [])
            )
            refs = item.get("finding_refs", [])
            refs_html = ""
            if refs:
                refs_str = ", ".join(f'<code>{xt(r)}</code>' for r in refs)
                refs_html = f'<div class="reg-meta">Triggered by: {refs_str}</div>'
            gaps = item.get("not_assessed", [])
            gaps_html = ""
            if gaps:
                gaps_str = "; ".join(xt(g) for g in gaps)
                gaps_html = f'<div class="reg-meta reg-gap-note">Not assessed: {gaps_str}</div>'
            note_html = f'<div class="reg-note-text">{xt(item["note"])}</div>'
            rows_html += (
                f'<div class="reg-item">'
                f'<div class="reg-item-header">'
                f'<span class="reg-req-label">{label}</span>'
                f'{badge}{src_chips}'
                f'</div>'
                f'{refs_html}{gaps_html}{note_html}'
                f'</div>'
            )
        stage_blocks += (
            f'<div class="reg-stage">'
            f'<div class="reg-stage-title">{_STAGE_LABELS.get(stage_key, stage_key)}</div>'
            f'{rows_html}'
            f'</div>'
        )

    summary = result.get("regulatory_traceability", {}).get("summary", "")
    summary_html = ""
    if summary:
        summary_html = (
            f'<div class="reg-summary">{xt(summary)}</div>'
        )
    faq = (
        f'<div class="faq-block" style="margin-top:18px">'
        f'<details class="faq-item"><summary>What does “signal only” mean here?</summary>'
        f'<p>It means repository evidence is relevant to a governance framework, but this scan is not claiming alignment, compliance, or clearance.</p></details>'
        f'<details class="faq-item"><summary>What does this section actually help establish?</summary>'
        f'<p>It shows where repository evidence connects to transparency, record-keeping, model-analysis-plan, or code-submission expectations before any formal audit.</p></details>'
        f'</div>'
    )

    return (
        f'<section id="s6">'
        f'<h2 class="s-title">Regulatory Traceability {hint}</h2>'
        f'<div class="panel">'
        f'{basis_box}'
        f'{stage_blocks}'
        f'{summary_html}'
        f'{faq}'
        f'</div></section>'
    )


def _section7_developer(result: dict[str, Any]) -> str:
    stage2_focus = _select_focus_rows(result.get("stage_2r_rubric", {}), negatives_first=True, limit=3)
    stage3_focus = _select_focus_rows(result.get("stage_3_rubric", {}), negatives_first=False, limit=3)
    score = result.get("score", {})
    stage2_score = int(score.get("stage_2_repo_local_consistency", 0) or 0)
    stage3_score = int(score.get("stage_3_code_bio", 0) or 0)
    risks = result.get("notable_risks", [])[:4]
    if not risks:
        risk_html = "<li>No immediate remediation actions surfaced.</li>"
    else:
        detail_map = {
            "Clinical-adjacent surfaces exist without an explicit non-diagnostic/non-clinical boundary.": "Add a clear research-use / non-diagnostic boundary in README and self-host surfaces first.",
            "Self-asserted compliance or privacy-governance claim requires independent verification.": "Either remove the claim or add supporting governance documentation and operational controls.",
            "Legal, privacy, or compliance claim appears without supporting governance or security-grounding evidence in reviewed repository sources.": "Separate marketing language from reviewed evidence and add concrete governance artifacts.",
            "Core workflow appears materially dependent on named external service providers; local or self-host claims may overstate operational independence.": "Document the external-service dependency explicitly and narrow self-host or privacy claims.",
        }
        risk_html = "".join(
            f'<li><strong>{xt(risk)}</strong><br/><span class="memo-note">{xt(detail_map.get(str(risk), "Review the matching evidence rows and close the contradiction before broadening deployment claims."))}</span></li>'
            for risk in risks
        )
    impact_html = (
        '<li>Boundary and workflow contradictions usually matter more than adding more replication artifacts.</li>'
        '<li>Removing a tier lock changes the meaning of the report first, and can unlock higher tiers later.</li>'
        '<li>Use Code Integrity for detector lanes, and Evidence Detail for file-level proof before making code changes.</li>'
    )
    next_html = (
        '<li><strong>Decision Path:</strong> use it to see which stage is holding the formal tier down.</li>'
        '<li><strong>Code Integrity details:</strong> use it for detector-specific trust boundary failures.</li>'
        '<li><strong>Evidence detail:</strong> use it when you need file-level proof before editing the repository.</li>'
    )
    return (
        f'<section id="s7">'
        f'<h2 class="s-title">Developer Follow-up</h2>'
        f'<div class="memo-grid">'
        f'<article class="memo-card">'
        f'<div class="eyebrow">Decision Path</div>'
        f'<h3>Which stages are holding the report down</h3>'
        f'<p class="memo-note"><strong>Stage 2R:</strong> {stage2_score}/100 — repo-local contradictions and missing trust boundaries.</p>'
        f'<ul class="focus-list">{_rubric_focus_list(stage2_focus)}</ul>'
        f'<p class="memo-note" style="margin-top:10px"><strong>Stage 3:</strong> {stage3_score}/100 — accountability and bio-governance evidence.</p>'
        f'<ul class="focus-list">{_rubric_focus_list(stage3_focus)}</ul>'
        f'</article>'
        f'<article class="memo-card memo-primary">'
        f'<div class="eyebrow">Top remediation actions</div>'
        f'<h3>What to fix first</h3>'
        f'<ul class="memo-list">{risk_html}</ul>'
        f'</article>'
        f'<article class="memo-card">'
        f'<div class="eyebrow">Expected impact</div>'
        f'<h3>What changes the report meaning</h3>'
        f'<ul class="memo-list">{impact_html}</ul>'
        f'</article>'
        f'<article class="memo-card">'
        f'<div class="eyebrow">Where to inspect next</div>'
        f'<h3>Use the developer-facing sections</h3>'
        f'<ul class="memo-list">{next_html}</ul>'
        f'</article>'
        f'</div></section>'
    )


def render_html(result: dict[str, Any]) -> str:
    score = result["score"]
    final = int(score["final_score"])
    tier = str(score["formal_tier"])
    tc = tier_color(tier)
    target = xt(str(result["target"]["name"]))
    score["_target_remote"] = str(result.get("target", {}).get("remote", "")).removesuffix(".git")
    date = xt(str(result.get("generated_at_local", "")))
    s1 = int(score.get("stage_1_readme_intent", 0))
    s2 = int(score.get("stage_2_repo_local_consistency", 0))
    s3 = int(score.get("stage_3_code_bio", 0))
    s4 = int(result.get("replication_score", 0))
    cls = result.get("classification", {})
    t0 = cls.get("t0_hard_floor", False)
    score_cap = cls.get("score_cap")

    css = build_css(tc)
    hero = _hero(score, final, tier, tc, target, date)
    sec1 = _section1(result, final, tc, s1, s2, s3, s4, t0, score_cap)
    sec2 = _section2(result, s1, s2, s3, s4)
    sec3 = _section3(result.get("code_integrity", {}), result.get("code_contract", {}))
    sec4 = _section4(result.get("airi_risk_coverage", {}))
    sec5 = _section5(result.get("evidence_ledger", []))
    sec6 = _section6(result)
    sec7 = _section7_developer(result)
    ver = xt(result.get("stem_ai_version", ""))
    nav = _nav(ver)

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
{sec6}
{sec4}
{sec5}
{sec7}
<div class="footer">
  STEM BIO-AI Local CLI Scan &nbsp;|&nbsp; {ver} &nbsp;|&nbsp; Deterministic surface scan &mdash; no LLM, network, or runtime execution.<br/>
  Not clinical certification. Not regulatory clearance. Not medical advice.
</div>
</div>
<script>{JS}</script>
</body>
</html>"""
