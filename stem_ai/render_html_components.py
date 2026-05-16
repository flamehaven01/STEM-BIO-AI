"""SVG generators, card builders, and shared helpers for STEM BIO-AI HTML report."""
from __future__ import annotations

import math
from typing import Any

_C = {
    "navy":   "#0D1F3C",  # deeper, truer navy (AIRI-aligned)
    "teal":   "#1A6FA8",  # richer mid-blue
    "green":  "#1A7A47",  # botanical green
    "amber":  "#C07B10",  # warm amber
    "red":    "#9B2335",  # AIRI crimson
    "purple": "#5B3D8A",  # deeper purple
    "slate":  "#2D4A6E",  # slate-blue
    "lgray":  "#F8FAFC",  # cooler background
    "mgray":  "#E4EBF5",  # cooler divider
    "dgray":  "#5A6B80",  # bluer muted text
    "white":  "#FFFFFF",
}
_TIER_COLOR   = {"T0": _C["red"], "T1": _C["red"], "T2": _C["amber"], "T3": _C["teal"], "T4": _C["green"]}
_STATUS_COLOR = {"PASS": _C["green"], "WARN": _C["amber"], "FAIL": _C["red"]}

# AIRI 7-domain palette (matches MIT AI Risk Navigator)
_AIRI_DOMAIN_COLORS = {
    1: "#B5272A",  # Discrimination & Toxicity
    2: "#1E3A6E",  # Privacy & Security
    3: "#C07020",  # Misinformation
    4: "#6B3FA0",  # Malicious Actors & Misuse
    5: "#1B7A4E",  # Human-Computer Interaction
    6: "#7A6520",  # Socioeconomic & Environmental
    7: "#1A5568",  # AI System Safety, Failures & Limitations
}
_AIRI_DOMAIN_NAMES = {
    1: "Discrimination & Toxicity",
    2: "Privacy & Security",
    3: "Misinformation",
    4: "Malicious Actors & Misuse",
    5: "Human-Computer Interaction",
    6: "Socioeconomic & Environmental",
    7: "AI System Safety, Failures & Limitations",
}

_STAGE_TIPS = [
    "Stage 1: Scans README/docs for hype language, overconfidence claims, and missing clinical disclaimers.",
    "Stage 2R: Cross-checks API names advertised in README against actual code exports and __all__ lists.",
    "Stage 3: AST scan for clinical safety patterns: PII validators, exception handling, dependency pinning.",
    "Stage 4: Evaluates reproducibility artifacts: seed fixation, dataset pinning, environment lock files.",
]


def tier_color(tier: str) -> str:
    for k, v in _TIER_COLOR.items():
        if k in tier:
            return v
    return _C["dgray"]


def status_color(s: str) -> str:
    return _STATUS_COLOR.get(str(s).upper(), _C["dgray"])


def xt(t: str) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tip_icon(tip: str) -> str:
    safe = tip.replace('"', "&quot;")
    return f'<span class="tip-icon" data-tooltip="{safe}" tabindex="0">?</span>'


# ── SVG generators ─────────────────────────────────────────────────────────────

def svg_gauge(score: int, color: str, size: int = 160) -> str:
    cx, cy, r = size // 2, size // 2, size // 2 - 16
    a = math.radians(180 - min(max(score, 0), 100) * 1.8)
    ex, ey = round(cx + r * math.cos(a), 2), round(cy - r * math.sin(a), 2)
    lx, ly, rx, ry, sw = cx - r, cy, cx + r, cy, 14
    h = size // 2 + 28
    return (
        f'<svg width="{size}" height="{h}" viewBox="0 0 {size} {h}"'
        f' aria-label="Score gauge: {score}/100">'
        f'<path d="M {lx},{ly} A {r},{r} 0 0,1 {rx},{ry}" fill="none"'
        f' stroke="{_C["mgray"]}" stroke-width="{sw}" stroke-linecap="round"/>'
        f'<path d="M {lx},{ly} A {r},{r} 0 0,1 {ex},{ey}" fill="none"'
        f' stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>'
        f'<text x="{cx}" y="{cy+10}" text-anchor="middle" font-size="32"'
        f' font-weight="700" fill="{color}">{score}</text>'
        f'<text x="{cx}" y="{cy+28}" text-anchor="middle" font-size="11"'
        f' fill="{_C["dgray"]}">/ 100</text></svg>'
    )


def svg_donut(pct: float, color: str, size: int = 90) -> str:
    cx = cy = size // 2
    r = size // 2 - 10
    circ = 2 * math.pi * r
    dash, gap = round(pct * circ, 2), round((1 - pct) * circ, 2)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none"'
        f' stroke="{_C["mgray"]}" stroke-width="10"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="10"'
        f' stroke-dasharray="{dash} {gap}" stroke-linecap="round"'
        f' transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="13"'
        f' font-weight="700" fill="{color}">{int(pct*100)}%</text></svg>'
    )


def svg_hbar(value: int, max_val: int = 100, color: str = _C["teal"],
             height: int = 20, width: int = 270) -> str:
    fw = round(value / max_val * width) if max_val else 0
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" rx="5" fill="{_C["mgray"]}"/>'
        f'<rect width="{fw}" height="{height}" rx="5" fill="{color}"/></svg>'
    )


# ── Card builders ──────────────────────────────────────────────────────────────

def integrity_card(key: str, info: dict[str, Any]) -> str:
    status  = str(info.get("status", "PASS"))
    color   = status_color(status)
    evl     = info.get("evidence", [])
    preview = xt(str(evl[0])[:80]) if evl else "No evidence captured"
    label_map = {
        "C1_hardcoded_credentials": "C1 Hardcoded Credentials",
        "C2_dependency_pinning": "C2 Dependency Pinning",
        "C3_dead_or_deprecated_patient_adjacent_paths": "C3 Deprecated Patient Paths",
        "C4_exception_handling_clinical_adjacent_paths": "C4 Fail-Open Exceptions",
        "C5_compliance_boundary_integrity": "C5 Compliance Boundary Integrity",
        "CC1_clinical_zero_default": "CC1 Clinical Zero Default",
        "CC2_api_contract": "CC2 API Contract",
        "CC3_shallow_validator": "CC3 Shallow Validator",
    }
    label   = label_map.get(key, key.replace("_", " ").title())
    items   = "".join(f'<li style="margin-bottom:3px">{xt(str(e)[:120])}</li>' for e in evl[:8])
    return (
        f'<div class="card" onclick="toggleCard(this)" tabindex="0"'
        f' role="button" aria-expanded="false">'
        f'<div style="border-top:3px solid {color};padding:16px 18px">'
        f'<div style="font-size:11px;font-weight:700;color:{_C["dgray"]};text-transform:uppercase;'
        f'letter-spacing:.06em;margin-bottom:6px">{xt(label)}</div>'
        f'<div style="font-size:13px;font-weight:700;color:{color};display:flex;'
        f'align-items:center;gap:6px;margin-bottom:8px">'
        f'<span style="width:10px;height:10px;border-radius:50%;background:{color};'
        f'display:inline-block"></span>{status}</div>'
        f'<div style="font-size:11px;color:{_C["dgray"]};line-height:1.4">{preview}</div>'
        f'<div class="caret" style="text-align:right;margin-top:6px;font-size:16px;'
        f'color:{_C["dgray"]}">&#8964;</div></div>'
        f'<div class="card-detail" style="display:none;padding:0 18px 14px;'
        f'border-top:1px solid {_C["mgray"]}">'
        f'<ul style="padding-left:16px;margin:10px 0 0;font-size:11px;'
        f'color:{_C["navy"]};line-height:1.7">'
        f'{items or "<li>No details available</li>"}</ul></div></div>'
    )


def domain_card(d_num: int, count: int) -> str:
    color = _AIRI_DOMAIN_COLORS.get(d_num, _C["dgray"])
    name  = _AIRI_DOMAIN_NAMES.get(d_num, f"Domain {d_num}")
    dim   = "opacity:.3;pointer-events:none" if count == 0 else "cursor:pointer"
    return (
        f'<div class="domain-card" data-domain="{d_num}"'
        f' onclick="filterDomain({d_num})" style="{dim}">'
        f'<span class="domain-num" style="background:{color}">{d_num}</span>'
        f'<span class="domain-label">{name}</span>'
        f'<span class="domain-cnt" style="color:{color}">{count}</span>'
        f'</div>'
    )


def airi_row(r: dict[str, Any], status: str = "covered") -> str:
    color = _C["green"] if status == "covered" else _C["amber"]
    if status == "covered":
        details = r.get("mapping_details", [])
        if details:
            preview_bits = []
            for detail in details[:2]:
                detector_id = str(detail.get("detector_id", "")).strip()
                reason = str(detail.get("trigger_reason") or detail.get("mapping_justification") or "").strip()
                if detector_id and reason:
                    preview_bits.append(f"{detector_id}: {reason}")
                elif detector_id:
                    preview_bits.append(detector_id)
            det = " | ".join(preview_bits) if preview_bits else ", ".join(r.get("covered_by", []))
        else:
            det = ", ".join(r.get("covered_by", []))
    else:
        det = r.get("note", "")[:70]
    sub   = xt(r.get("subdomain_label", r.get("subdomain_id", "")))[:32]
    cls   = "airi-covered" if status == "covered" else "airi-gaps"
    dom   = str(r.get("subdomain_id", "0")).split(".")[0]
    return (
        f'<tr class="{cls}" data-domain="{dom}"'
        f' style="border-bottom:1px solid {_C["mgray"]}">'
        f'<td style="padding:8px 6px;font-size:11px;color:{_C["dgray"]};'
        f'font-family:monospace">{xt(r["id"])}</td>'
        f'<td style="padding:8px 6px;font-size:12px;color:{_C["navy"]};font-weight:500">'
        f'{xt(r.get("title",""))[:55]}</td>'
        f'<td style="padding:8px 6px;font-size:11px;color:{_C["purple"]}">{sub}</td>'
        f'<td style="padding:8px 6px;font-size:11px;color:{color}">'
        f'{xt(str(det))[:65]}</td></tr>'
    )


def evidence_row(ev: dict[str, Any]) -> str:
    sev = str(ev.get("severity", ev.get("status", "INFO"))).upper()
    sc  = _STATUS_COLOR.get(sev, _C["dgray"])
    det = xt(str(ev.get("detector", ev.get("check", "")))[:32])
    raw_msg = ev.get("message", ev.get("detail", ""))
    msg = xt(str(raw_msg if raw_msg else ev)[:90])
    loc = xt(str(ev.get("file", ev.get("path", "")))[:50])
    return (
        f'<tr class="ev-row ev-{sev.lower()}"'
        f' style="border-bottom:1px solid {_C["mgray"]}">'
        f'<td style="padding:8px 5px;width:16px">'
        f'<span style="display:block;width:8px;height:8px;border-radius:50%;'
        f'background:{sc}"></span></td>'
        f'<td style="padding:8px 5px;font-size:11px;color:{sc};font-weight:700">{sev}</td>'
        f'<td style="padding:8px 5px;font-size:11px;color:{_C["purple"]};'
        f'font-family:monospace">{det}</td>'
        f'<td style="padding:8px 5px;font-size:12px;color:{_C["navy"]}">{msg}</td>'
        f'<td style="padding:8px 5px;font-size:11px;color:{_C["dgray"]}">{loc}</td>'
        f'</tr>'
    )
