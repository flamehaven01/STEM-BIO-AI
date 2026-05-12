# HTML Report Dashboard

STEM BIO-AI v1.7.0 introduces a **self-contained interactive HTML dashboard** as the primary human-readable output format. The report is a single `.html` file with inline CSS, SVG, and JavaScript — zero external dependencies, fully offline-capable.

## Generating the Report

```bash
stem scan /path/to/repo --format html
stem scan /path/to/repo --format all    # JSON + MD + HTML + PDF in one pass
```

Output: `stem_output/<repo>_report.html`

## 5-Section Structure

| Section | ID | Content |
|---------|-----|---------|
| **Executive Summary** | `#s1` | Score gauge, 5-metric stat grid, notable risks, T0 alert banner |
| **Score Matrix** | `#s2` | Stage bars (S1/S2R/S3/S4) with formula tooltip |
| **Code Integrity & Contract** | `#s3` | C1–C4 + CC1–CC3 expandable cards |
| **AIRI Risk Coverage** | `#s4` | MIT AI Risk Repository donut + covered/gaps toggle table |
| **Evidence Detail** | `#s5` | Full evidence ledger with severity filter chips |

Navigation between sections via a **sticky top navbar** with scroll-spy active state.

## Interactive Features

### Score Gauge
SVG semicircle speedometer (0–100). Arc color matches the tier:
- T0/T1: red (`#C0392B`)
- T2: amber (`#C97B10`)
- T3: teal (`#2E86AB`)
- T4: green (`#27A560`)

### Expandable Cards (Section 3)
Each `C1–C4` / `CC1–CC3` card is clickable. Click expands the full evidence list (up to 8 entries). The caret rotates 180° on expand. Keyboard accessible via Enter/Space.

```
[C4 Exception Handling Clinical Adjacent Paths]   WARN ▾
  bare except in infer.py:42 ← collapsed
  ──────────────────────────────────────────────
  - bare_except @ openmed/inference.py:42
  - bare_except @ openmed/utils.py:17       ← expanded
```

### AIRI Toggle (Section 4)
Two-button toggle: `[Covered (n)]` / `[Gaps (n)]`. Shows the corresponding risk table rows and hides the other view.

### Evidence Filter Chips (Section 5)
One-click severity filter: `All` `FAIL` `WARN` `PASS` `INFO`. Filters `ev-row` elements by CSS class; active chip highlighted in navy.

### Tooltip `?` Icons
Every metric header carries a `?` icon with a `data-tooltip` attribute. CSS `::after` pseudo-element renders the tooltip on hover/focus — no JavaScript required.

```css
[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute; bottom: calc(100% + 8px);
  /* ... navy background, 240px max-width, fade-in transition */
}
```

### Scroll Spy Navigation
`updateNav()` listens to `window.scroll` (passive) and toggles `.active` on the nav link whose section is at the top of the viewport.

## Architecture

The HTML renderer is split into three modules (each < 250 lines):

| File | Role |
|------|------|
| `stem_ai/render_html_components.py` | `_C` palette, SVG generators (`svg_gauge`, `svg_donut`, `svg_hbar`), card builders (`integrity_card`, `airi_row`, `evidence_row`) |
| `stem_ai/render_html_styles.py` | `build_css(tc)` f-string (tier-color parameterized), `JS` constant |
| `stem_ai/render_html.py` | Five `_section*()` assemblers + `render_html(result)` entry point |

## Report Preview

![HTML Report Preview](assets/html_report_preview.png)

*Screenshot: openmed scan, T1 tier (39/100), T0 hard floor triggered.*

## AIRI Risk Coverage Section

The AIRI coverage section maps STEM-BIO-AI detectors to the [MIT AI Risk Repository V4](https://airisk.mit.edu/) medical/clinical risk subset (184 bundled entries).

Coverage rate = covered risk IDs / total IDs in detector scope.

| Detector | AIRI Risk IDs Covered |
|----------|----------------------|
| `CC1_clinical_zero_default` | 62.15.02, 02.09.00, 30.01.02, 69.01.01, 16.03.01 |
| `CC3_shallow_validator` | 65.03.03, 02.01.03, 16.02.01, 47.03.01, 70.02.01 |
| `T0_hard_floor` | 41.04.00, 61.02.28, 18.05.03, 56.14.00, 47.02.12, 16.05.02, 43.01.00 |
| `C4_exception_handling_clinical_adjacent_paths` | 70.01.02, 24.01.03, 60.02.01 |

Five known gaps are reported for risks that require dynamic evaluation or extend beyond static scan scope.

## File Size Reference

| Repository | HTML size |
|-----------|----------|
| `maziyarpanahi/openmed` (T1, 39/100) | ~164 KB |
| Typical T3 repository | ~40–80 KB |

Size scales with evidence ledger length. The renderer caps the evidence table at 200 rows.
