"""CSS and JS template strings for STEM BIO-AI interactive HTML report."""
from __future__ import annotations
from .render_html_components import _C


def build_css(tc: str) -> str:
    n, t = _C["navy"], _C["teal"]
    g, a, r = _C["green"], _C["amber"], _C["red"]
    p, lg, mg, dg, w = _C["purple"], _C["lgray"], _C["mgray"], _C["dgray"], _C["white"]
    return f"""
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  background:{lg};color:{n};font-size:14px;line-height:1.5}}
.nav{{position:sticky;top:0;z-index:50;background:{n};display:flex;
  border-bottom:2px solid {t};overflow-x:auto}}
.nav-link{{padding:12px 18px;color:rgba(255,255,255,.6);font-size:12px;font-weight:600;
  text-decoration:none;transition:color .2s,background .2s;
  border-bottom:3px solid transparent;margin-bottom:-2px;white-space:nowrap}}
.nav-link:hover{{color:#fff;background:rgba(255,255,255,.07)}}
.nav-link.active{{color:#fff;border-bottom-color:{t}}}
.hero{{background:linear-gradient(135deg,{n} 0%,#263d5e 100%);color:#fff;
  padding:36px 48px;display:flex;gap:36px;align-items:center;flex-wrap:wrap}}
.hero h1{{font-size:24px;font-weight:700;margin-bottom:6px}}
.sub{{font-size:12px;color:rgba(255,255,255,.5);margin-bottom:10px}}
.tier{{display:inline-block;background:{tc};color:#fff;font-size:12px;font-weight:700;
  padding:4px 14px;border-radius:20px;margin-bottom:10px}}
.content{{max-width:980px;margin:0 auto;padding:36px 24px}}
section{{margin-bottom:40px;scroll-margin-top:60px}}
.s-title{{font-size:18px;font-weight:700;color:{n};margin-bottom:18px;
  display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.panel{{background:{w};border-radius:10px;padding:24px;
  box-shadow:0 1px 4px rgba(0,0,0,.08)}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}}
.card{{background:{w};border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.08);
  cursor:pointer;transition:box-shadow .2s,transform .15s;overflow:hidden;
  outline:none}}
.card:hover{{box-shadow:0 6px 20px rgba(0,0,0,.14);transform:translateY(-2px)}}
.card:focus{{box-shadow:0 0 0 3px {t}40}}
.card.expanded{{box-shadow:0 6px 24px rgba(0,0,0,.16)}}
.card.expanded .caret{{transform:rotate(180deg)}}
.caret{{display:block;transition:transform .2s}}
.tip-icon{{display:inline-flex;align-items:center;justify-content:center;
  width:16px;height:16px;border-radius:50%;background:{mg};color:{dg};
  font-size:10px;font-weight:700;cursor:help;position:relative;
  flex-shrink:0;vertical-align:middle}}
[data-tooltip]{{position:relative}}
[data-tooltip]::after{{content:attr(data-tooltip);position:absolute;
  bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);
  background:{n};color:#fff;padding:8px 12px;border-radius:6px;
  font-size:11px;line-height:1.4;white-space:normal;max-width:240px;
  width:max-content;opacity:0;pointer-events:none;transition:opacity .2s;
  z-index:200;text-align:left;font-weight:400;
  box-shadow:0 4px 12px rgba(0,0,0,.25)}}
[data-tooltip]:hover::after,[data-tooltip]:focus::after{{opacity:1}}
.toggle-group{{display:flex;border:1px solid {mg};border-radius:6px;
  overflow:hidden;width:fit-content;margin-bottom:16px}}
.toggle-btn{{padding:7px 18px;font-size:12px;font-weight:600;color:{dg};
  background:{w};border:none;cursor:pointer;transition:all .2s}}
.toggle-btn:hover{{background:{lg}}}
.toggle-btn.active{{background:{n};color:#fff}}
.airi-table{{width:100%;border-collapse:collapse}}
.airi-table th{{padding:10px 8px;font-size:11px;text-align:left;color:{dg};
  background:{lg};font-weight:600;text-transform:uppercase;letter-spacing:.05em}}
.airi-table tr:hover{{background:{lg}}}
.ev-row{{transition:background .15s;cursor:default}}
.ev-row:hover{{background:{lg}}}
.alert-t0{{background:{r};color:#fff;padding:14px 24px;border-radius:8px;
  margin-bottom:24px;font-weight:600;font-size:13px;
  border-left:4px solid rgba(0,0,0,.2)}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));
  gap:14px;margin-bottom:28px}}
.stat-card{{background:{w};border-radius:8px;padding:18px 16px;
  box-shadow:0 1px 3px rgba(0,0,0,.07);text-align:center;
  transition:box-shadow .2s}}
.stat-card:hover{{box-shadow:0 4px 12px rgba(0,0,0,.12)}}
.stat-val{{font-size:28px;font-weight:700;margin-bottom:4px}}
.stat-lbl{{font-size:11px;color:{dg};font-weight:600;text-transform:uppercase;
  letter-spacing:.05em}}
.risk-item{{padding:12px 16px;border-left:4px solid {a};margin-bottom:10px;
  background:{w};border-radius:0 8px 8px 0;font-size:12px;color:{n};
  line-height:1.5;transition:border-color .2s,box-shadow .2s}}
.risk-item:hover{{border-left-color:{r};box-shadow:0 2px 8px rgba(0,0,0,.08)}}
.filter-chip{{display:inline-flex;align-items:center;padding:4px 12px;
  border-radius:14px;font-size:11px;font-weight:600;cursor:pointer;
  border:1px solid {mg};margin:0 6px 8px 0;transition:all .15s;
  background:{w};user-select:none}}
.filter-chip.active{{background:{n};color:#fff;border-color:{n}}}
.filter-chip:hover:not(.active){{background:{lg}}}
.stage-row{{margin-bottom:18px}}
.footer{{font-size:11px;color:{dg};text-align:center;padding:20px 0;
  border-top:1px solid {mg};margin-top:40px}}
.formula{{font-size:11px;color:{dg};margin-top:16px;font-family:monospace;
  background:{lg};padding:8px 12px;border-radius:6px}}
@media(max-width:640px){{
  .hero{{padding:24px;flex-direction:column}}
  .content{{padding:24px 16px}}
  .nav-link{{padding:10px 12px;font-size:11px}}
  .stats-grid{{grid-template-columns:repeat(2,1fr)}}
}}"""


JS = r"""
function toggleCard(card) {
  var d = card.querySelector('.card-detail');
  var exp = card.classList.toggle('expanded');
  card.setAttribute('aria-expanded', String(exp));
  if (d) d.style.display = exp ? 'block' : 'none';
}

function airiToggle(view) {
  document.querySelectorAll('.airi-covered,.airi-gaps').forEach(function(el) {
    el.style.display = el.classList.contains('airi-' + view) ? '' : 'none';
  });
  document.querySelectorAll('.toggle-btn[data-view]').forEach(function(b) {
    b.classList.toggle('active', b.dataset.view === view);
  });
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
    if (window.scrollY >= s.offsetTop - 80) cur = s.id;
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
