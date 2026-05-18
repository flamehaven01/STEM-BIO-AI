"""CSS and JS template strings for STEM BIO-AI interactive HTML report."""
from __future__ import annotations

from .render_html_components import _C


def build_css(tc: str) -> str:
    n, t = _C["navy"], _C["teal"]
    g, a, r = _C["green"], _C["amber"], _C["red"]
    p, lg, mg, dg, w = _C["purple"], _C["lgray"], _C["mgray"], _C["dgray"], _C["white"]
    return f"""
:root{{
  --navy:{n};
  --teal:{t};
  --green:{g};
  --amber:{a};
  --red:{r};
  --purple:{p};
  --slate:{_C["slate"]};
  --bg:{lg};
  --panel:{w};
  --line:{mg};
  --muted:{dg};
  --tier:{tc};
  --shadow-soft:0 10px 28px rgba(13,31,60,.08);
  --shadow-strong:0 20px 48px rgba(13,31,60,.16);
  --radius:18px;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{
  font-family:"Segoe UI Variable Text","Segoe UI",ui-sans-serif,sans-serif;
  background:
    radial-gradient(circle at top left, rgba(26,111,168,.09), transparent 28%),
    linear-gradient(180deg, #f5f8fc 0%, {lg} 42%, #eef3f9 100%);
  color:{n};
  font-size:14px;
  line-height:1.6;
}}
h1,h2,h3,.stage-name,.metric-value,.tier{{
  font-family:"Iowan Old Style","Palatino Linotype","Book Antiqua",Georgia,serif;
}}
.nav{{
  position:sticky;top:0;z-index:60;
  background:rgba(255,255,255,.86);
  backdrop-filter:blur(14px);
  display:flex;gap:4px;overflow-x:auto;
  border-bottom:1px solid rgba(13,31,60,.08);
  box-shadow:0 8px 24px rgba(13,31,60,.06);
}}
.nav-link{{
  padding:14px 18px;color:{dg};font-size:12px;font-weight:700;
  text-decoration:none;transition:color .2s,background .2s,border-color .2s;
  border-bottom:3px solid transparent;white-space:nowrap;
}}
.nav-link:hover{{color:{n};background:rgba(13,31,60,.04)}}
.nav-link.active{{color:{n};border-bottom-color:{t}}}
.hero{{
  background:
    radial-gradient(circle at top right, rgba(255,255,255,.12), transparent 26%),
    linear-gradient(135deg, {n} 0%, #163457 48%, #24537B 100%);
  color:#fff;
  padding:42px 48px 46px;
  display:grid;
  grid-template-columns:minmax(180px,220px) 1fr;
  gap:30px;
  align-items:center;
}}
.hero-left{{display:flex;justify-content:center}}
.hero-right{{display:flex;flex-direction:column;gap:10px}}
.hero h1{{font-size:34px;font-weight:700;line-height:1.1;letter-spacing:-.02em}}
.eyebrow{{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:rgba(13,31,60,.62)}}
.hero .eyebrow{{color:rgba(255,255,255,.62)}}
.hero-meta{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
.tier{{
  display:inline-block;background:{tc};color:#fff;font-size:13px;font-weight:700;
  padding:6px 16px;border-radius:999px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);
}}
.hero-chip{{
  display:inline-flex;align-items:center;padding:6px 12px;border-radius:999px;
  border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.08);
  color:rgba(255,255,255,.84);font-size:11px;font-weight:700;
}}
.lede{{font-size:14px;color:rgba(255,255,255,.82);max-width:720px}}
.content{{max-width:1180px;margin:0 auto;padding:34px 24px 54px}}
section{{margin-bottom:34px;scroll-margin-top:72px}}
.s-title{{font-size:24px;font-weight:700;color:{n};margin-bottom:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
.subhead{{font-size:22px;font-weight:700;color:{n};margin:2px 0 10px}}
.panel{{
  background:{w};
  border:1px solid rgba(13,31,60,.07);
  border-radius:var(--radius);
  padding:24px;
  box-shadow:var(--shadow-soft);
}}
.memo-grid,.integrity-layout,.airi-layout{{display:grid;grid-template-columns:repeat(12,1fr);gap:18px}}
.memo-card,.stage-card{{
  background:{w};
  border:1px solid rgba(13,31,60,.08);
  border-radius:var(--radius);
  padding:20px 20px 18px;
  box-shadow:var(--shadow-soft);
}}
.memo-primary{{background:linear-gradient(180deg,#ffffff 0%,#f8fbff 100%)}}
.memo-card:nth-child(1){{grid-column:span 6}}
.memo-card:nth-child(2),.memo-card:nth-child(3),.memo-card:nth-child(4){{grid-column:span 6}}
.memo-text{{font-size:13px;color:{n}}}
.memo-note,.muted-note,.muted{{font-size:11px;color:{dg};line-height:1.5}}
.memo-list{{padding-left:18px;display:grid;gap:8px;font-size:12px;color:{n}}}
.pill-row{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}
.pill{{display:inline-flex;align-items:center;padding:5px 11px;border-radius:999px;background:{lg};border:1px solid {mg};font-size:11px;font-weight:700;color:{n}}}
.metric-grid{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-bottom:18px}}
.metric-card{{
  background:{w};border:1px solid rgba(13,31,60,.08);border-radius:16px;
  padding:18px 16px;box-shadow:var(--shadow-soft);text-align:center
}}
.metric-value{{font-size:32px;font-weight:700;line-height:1;margin-bottom:6px}}
.metric-label{{font-size:11px;color:{dg};font-weight:800;text-transform:uppercase;letter-spacing:.08em}}
.alert-t0{{background:{r};color:#fff;padding:15px 18px;border-radius:14px;margin-bottom:18px;font-weight:700;box-shadow:var(--shadow-soft)}}
.decision-panel{{padding:18px}}
.formula-banner{{
  margin-bottom:16px;padding:12px 14px;border-radius:14px;background:#eef5fb;
  border:1px solid #d7e5f4;font-size:12px;color:{n};font-family:"Consolas","SFMono-Regular",monospace
}}
.config-pattern{{
  display:grid;
  grid-template-columns:minmax(0,1.2fr) minmax(0,1.8fr);
  gap:18px;
  margin-bottom:18px;
  padding:18px;
  border-radius:16px;
  background:linear-gradient(180deg,#fbfdff 0%,#f2f7fc 100%);
  border:1px solid #dbe6f1;
}}
.config-copy{{display:grid;gap:10px;align-content:start}}
.config-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
.config-card{{
  background:{w};
  border:1px solid rgba(13,31,60,.08);
  border-radius:14px;
  padding:12px;
  box-shadow:var(--shadow-soft);
}}
.config-label{{
  font-size:10px;
  font-weight:800;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:{dg};
  margin-bottom:8px;
}}
.config-code{{
  font-family:"Consolas","SFMono-Regular",monospace;
  font-size:11px;
  line-height:1.55;
  white-space:pre-wrap;
  color:{n};
  background:#f7fafc;
  border:1px solid #e3ebf3;
  border-radius:10px;
  padding:10px 11px;
  overflow:auto;
}}
.stage-deck{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.stage-card-top{{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:10px}}
.stage-name{{font-size:18px;font-weight:700;color:{n};line-height:1.2}}
.stage-value{{font-size:26px;font-weight:700;line-height:1}}
.stage-summary{{font-size:12px;color:{dg};margin:12px 0 10px}}
.focus-list{{list-style:none;display:grid;gap:10px}}
.focus-line{{padding-top:10px;border-top:1px solid rgba(13,31,60,.08)}}
.focus-top{{display:flex;justify-content:space-between;gap:12px;align-items:baseline;margin-bottom:4px}}
.focus-key{{font-size:12px;font-weight:700;color:{n}}}
.focus-score{{font-size:12px;font-weight:800;color:{n}}}
.focus-detail{{font-size:11px;color:{dg};line-height:1.55}}
.focus-detector{{display:inline-flex;margin-right:8px;padding:2px 8px;border-radius:999px;background:#f2f6fa;border:1px solid {mg};font-family:"Consolas","SFMono-Regular",monospace;color:{p}}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}}
.card{{background:{w};border-radius:14px;box-shadow:var(--shadow-soft);cursor:pointer;transition:box-shadow .2s,transform .15s;overflow:hidden;outline:none;border:1px solid rgba(13,31,60,.06)}}
.card:hover{{box-shadow:var(--shadow-strong);transform:translateY(-2px)}}
.card:focus{{box-shadow:0 0 0 3px rgba(26,111,168,.2)}}
.card.expanded{{box-shadow:var(--shadow-strong)}}
.card.expanded .caret{{transform:rotate(180deg)}}
.caret{{display:block;transition:transform .2s}}
.faq-block{{display:grid;gap:10px;margin-top:16px}}
.faq-item{{border-top:1px solid rgba(13,31,60,.08);padding-top:10px}}
.faq-item summary{{cursor:pointer;font-size:12px;font-weight:800;color:{n};list-style:none}}
.faq-item summary::-webkit-details-marker{{display:none}}
.faq-item p{{margin-top:8px;font-size:12px;color:{dg}}}
.tip-icon{{display:inline-flex;align-items:center;justify-content:center;width:17px;height:17px;border-radius:50%;background:{mg};color:{dg};font-size:10px;font-weight:800;cursor:help;position:relative;flex-shrink:0;vertical-align:middle}}
[data-tooltip]{{position:relative}}
[data-tooltip]::after{{
  content:attr(data-tooltip);position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);
  background:{n};color:#fff;padding:9px 12px;border-radius:10px;font-size:11px;line-height:1.45;white-space:normal;
  max-width:280px;width:max-content;opacity:0;pointer-events:none;transition:opacity .2s;z-index:200;text-align:left;
  font-weight:500;box-shadow:0 10px 28px rgba(0,0,0,.25)
}}
[data-tooltip]:hover::after,[data-tooltip]:focus::after{{opacity:1}}
.toggle-row{{display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
.toggle-group{{display:flex;border:1px solid {mg};border-radius:999px;overflow:hidden;width:fit-content;background:{w}}}
.toggle-btn{{padding:8px 18px;font-size:12px;font-weight:800;color:{dg};background:{w};border:none;cursor:pointer;transition:all .2s}}
.toggle-btn:hover{{background:{lg}}}
.toggle-btn.active{{background:{n};color:#fff}}
.risk-item{{padding:12px 15px;border-left:4px solid {a};margin-bottom:10px;background:{w};border-radius:0 10px 10px 0;font-size:12px;color:{n};line-height:1.5;transition:border-color .2s,box-shadow .2s}}
.risk-item:hover{{border-left-color:{r};box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.domain-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin-bottom:18px}}
.domain-card{{display:flex;align-items:center;gap:10px;padding:11px 14px;background:{w};border:1.5px solid {mg};border-radius:12px;transition:border-color .15s,box-shadow .15s;user-select:none}}
.domain-card:hover{{border-color:{t};box-shadow:0 2px 8px rgba(0,0,0,.1)}}
.domain-card.domain-active{{border-color:var(--d-color,{t});box-shadow:0 0 0 3px color-mix(in srgb,var(--d-color,{t}) 18%,transparent)}}
.domain-num{{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:6px;color:#fff;font-size:11px;font-weight:800;flex-shrink:0}}
.domain-label{{font-size:11px;color:{n};font-weight:700;flex:1;line-height:1.3}}
.domain-cnt{{font-size:12px;font-weight:800;flex-shrink:0}}
.airi-tag{{font-size:12px;color:{dg};font-weight:500;margin-left:4px}}
.airi-kpi{{display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin-top:14px}}
.airi-copy{{display:grid;gap:8px;min-width:240px}}
.metric-inline{{font-size:12px;color:{n}}}
.airi-table{{width:100%;border-collapse:collapse}}
.airi-table th{{padding:10px 8px;font-size:11px;text-align:left;color:{dg};background:{lg};font-weight:800;text-transform:uppercase;letter-spacing:.05em}}
.airi-table tr:hover{{background:{lg}}}
.ev-row{{transition:background .15s;cursor:default}}
.ev-row:hover{{background:{lg}}}
.filter-chip{{display:inline-flex;align-items:center;padding:5px 12px;border-radius:999px;font-size:11px;font-weight:800;cursor:pointer;border:1px solid {mg};margin:0 6px 8px 0;transition:all .15s;background:{w};user-select:none}}
.filter-chip.active{{background:{n};color:#fff;border-color:{n}}}
.filter-chip:hover:not(.active){{background:{lg}}}
.footer{{font-size:11px;color:{dg};text-align:center;padding:24px 0;border-top:1px solid rgba(13,31,60,.08);margin-top:40px}}
@media(max-width:1000px){{
  .metric-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}
  .stage-deck{{grid-template-columns:1fr}}
  .memo-card,.memo-card:nth-child(1),.memo-card:nth-child(2),.memo-card:nth-child(3),.memo-card:nth-child(4){{grid-column:span 12}}
  .integrity-layout,.airi-layout{{grid-template-columns:1fr}}
  .config-pattern{{grid-template-columns:1fr}}
  .config-grid{{grid-template-columns:1fr}}
}}
@media(max-width:760px){{
  .hero{{padding:28px 22px;grid-template-columns:1fr}}
  .content{{padding:24px 14px 42px}}
  .nav-link{{padding:12px 12px;font-size:11px}}
  .metric-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}
}}
@media(max-width:520px){{
  .metric-grid{{grid-template-columns:1fr}}
  .s-title{{font-size:21px}}
  .hero h1{{font-size:28px}}
}}
"""


JS = r"""
function toggleCard(card) {
  var d = card.querySelector('.card-detail');
  var exp = card.classList.toggle('expanded');
  card.setAttribute('aria-expanded', String(exp));
  if (d) d.style.display = exp ? 'block' : 'none';
}

var _airiView = 'covered';
var _airiDomain = 0;

function _applyAiriFilter() {
  document.querySelectorAll('.airi-covered,.airi-gaps').forEach(function(r) {
    var viewOk = r.classList.contains('airi-' + _airiView);
    var domainOk = (_airiDomain === 0 || r.dataset.domain == _airiDomain);
    r.style.display = (viewOk && domainOk) ? '' : 'none';
  });
}

function airiToggle(view) {
  _airiView = view;
  _applyAiriFilter();
  document.querySelectorAll('.toggle-btn[data-view]').forEach(function(b) {
    b.classList.toggle('active', b.dataset.view === view);
  });
}

function filterDomain(num) {
  _airiDomain = (_airiDomain === num) ? 0 : num;
  document.querySelectorAll('.domain-card').forEach(function(c) {
    var active = (c.dataset.domain == _airiDomain);
    c.classList.toggle('domain-active', active);
    c.style.setProperty('--d-color', active ? c.querySelector('.domain-num').style.background : '');
  });
  _applyAiriFilter();
}

function filterEv(sev) {
  document.querySelectorAll('.ev-row').forEach(function(r) {
    r.style.display = (sev === 'all' || r.classList.contains('ev-' + sev)) ? '' : 'none';
  });
  document.querySelectorAll('.filter-chip').forEach(function(c) {
    c.classList.toggle('active', c.dataset.sev === sev);
  });
}

function updateNav() {
  var cur = '';
  document.querySelectorAll('section[id]').forEach(function(s) {
    if (window.scrollY >= s.offsetTop - 88) cur = s.id;
  });
  document.querySelectorAll('.nav-link').forEach(function(l) {
    l.classList.toggle('active', l.getAttribute('href') === '#' + cur);
  });
}

window.addEventListener('scroll', updateNav, { passive: true });

document.addEventListener('DOMContentLoaded', function() {
  updateNav();
  airiToggle('covered');
  filterEv('all');
  document.querySelectorAll('.card').forEach(function(c) {
    c.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleCard(c); }
    });
  });
});
"""
