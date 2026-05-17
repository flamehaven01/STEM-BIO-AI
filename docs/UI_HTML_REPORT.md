# HTML Report Dashboard

STEM BIO-AI v1.7.0 introduced a **self-contained interactive HTML dashboard** as the primary human-readable output format. In v1.7.2, the AIRI section was aligned to the governed local AIRI registry/runtime-bundle model. The report is a single `.html` file with inline CSS, SVG, and JavaScript — zero external dependencies, fully offline-capable.

## Generating the Report

```bash
stem scan /path/to/repo --format html
stem scan /path/to/repo --format all    # JSON + MD + HTML + PDF in one pass
```

Output:

- default root: `stem_output/<repo_slug>/<repo_slug>_report.html`
- custom output directory: `<output_dir>/<repo_slug>_report.html`

Example:

- browser preview: <https://htmlpreview.github.io/?https://raw.githubusercontent.com/flamehaven01/STEM-BIO-AI/main/docs/examples/maziyarpanahi_openmed_report.html>
- raw artifact: [`docs/examples/maziyarpanahi_openmed_report.html`](examples/maziyarpanahi_openmed_report.html)

## 5-Section Structure

| Section | ID | Content |
|---------|-----|---------|
| **Executive Summary** | `#s1` | Score gauge, 5-metric stat grid, notable risks, T0 alert banner |
| **Score Matrix** | `#s2` | Stage bars (S1/S2R/S3/S4) with formula tooltip |
| **Code Integrity & Contract** | `#s3` | C1–C6 + CC1–CC3 expandable cards |
| **AIRI Risk Coverage** | `#s4` | MIT AI Risk Repository donut + covered/gaps toggle table |
| **Evidence Detail** | `#s5` | Full evidence ledger with severity filter chips |

Navigation between sections via a **sticky top navbar** with scroll-spy active state.

## Interactive Features

### Score Gauge
SVG semicircle speedometer (0–100). Arc color matches the tier:
- T0/T1: crimson (`#9B2335`)
- T2: amber (`#C07B10`)
- T3: teal (`#1A6FA8`)
- T4: green (`#1A7A47`)

### Expandable Cards (Section 3)
Each `C1–C6` / `CC1–CC3` card is clickable. Click expands the full evidence list (up to 8 entries). The caret rotates 180° on expand. Keyboard accessible via Enter/Space.

```
[C5 Compliance Boundary Integrity]   WARN ▾
  unsupported compliance claim in README.md ← collapsed
  ──────────────────────────────────────────────
  - README.md:262 - HIPAA-compliant architecture (when self-hosted)
  - Clinical-adjacent surfaces exist without an explicit non-diagnostic/non-clinical boundary.       ← expanded
```

### AIRI 7-Domain Shortcut Cards (Section 4)
Seven domain cards above the risk table, each with a numbered badge, domain name, and covered-risk count. Colors match the MIT AI Risk Navigator palette:

| # | Domain | Badge color |
|---|--------|------------|
| 1 | Discrimination & Toxicity | `#B5272A` crimson |
| 2 | Privacy & Security | `#1E3A6E` deep navy |
| 3 | Misinformation | `#C07020` amber |
| 4 | Malicious Actors & Misuse | `#6B3FA0` deep purple |
| 5 | Human-Computer Interaction | `#1B7A4E` deep green |
| 6 | Socioeconomic & Environmental | `#7A6520` olive |
| 7 | AI System Safety, Failures & Limitations | `#1A5568` dark teal |

Click a domain card → risk table filters to that domain only. Click the same card again → filter cleared. Domains with zero covered risks are dimmed (`opacity:0.3`, non-clickable). Domain filter composes with the Covered/Gaps toggle via `_applyAiriFilter()`.

### AIRI Toggle (Section 4)
Two-button toggle: `[Covered (n)]` / `[Gaps (n)]`. Composes with the domain filter — both conditions must be satisfied for a row to be visible.

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
| `stem_ai/render_html_components.py` | `_C` palette, `_AIRI_DOMAIN_COLORS/NAMES`, SVG generators (`svg_gauge`, `svg_donut`, `svg_hbar`), card builders (`integrity_card`, `domain_card`, `airi_row`, `evidence_row`) |
| `stem_ai/render_html_styles.py` | `build_css(tc)` f-string (tier-color parameterized), `.domain-card/.domain-active` CSS, `JS` constant with `filterDomain()` + `_applyAiriFilter()` |
| `stem_ai/render_html.py` | Five `_section*()` assemblers + domain-count computation + `render_html(result)` entry point |

## Report Preview

![HTML Report Preview](assets/html_report_preview.png)

*Screenshot: openmed scan, T1 tier (39/100), T0 hard floor triggered.*

## Color Palette

Refined in v1.7.0 to align with AIRI Navigator's visual language — deeper saturation, cooler backgrounds, AIRI-standard crimson for risk indicators.

| Role | Token | Value |
|------|-------|-------|
| Primary navy | `_C["navy"]` | `#0D1F3C` |
| Link teal | `_C["teal"]` | `#1A6FA8` |
| Pass green | `_C["green"]` | `#1A7A47` |
| Warn amber | `_C["amber"]` | `#C07B10` |
| Fail / T0-T1 | `_C["red"]` | `#9B2335` |
| Accent purple | `_C["purple"]` | `#5B3D8A` |
| Background | `_C["lgray"]` | `#F8FAFC` |
| Divider | `_C["mgray"]` | `#E4EBF5` |
| Muted text | `_C["dgray"]` | `#5A6B80` |

## AIRI Risk Coverage Section

The AIRI coverage section maps STEM-BIO-AI detectors to a governed local AIRI layer derived from the [MIT AI Risk Repository V4](https://airisk.mit.edu/):

- full local registry snapshot
- curated runtime bundle used by deterministic scans
- detector-to-risk mapping registry

The runtime HTML report reflects the curated bundle, not the entire AIRI universe.

Covered rows now show a short bounded explanation built from:

- the local detector ID,
- the detector-to-risk mapping justification, and
- the trigger reason surfaced by the scan.

This helps reviewers understand *why* a risk appears in AIRI coverage without implying that AIRI independently audited the repository.

Coverage rate = covered risk IDs / total IDs in detector scope.

| Detector | AIRI Risk IDs Covered |
|----------|----------------------|
| `CC1_clinical_zero_default` | 62.15.02, 02.09.00, 30.01.02, 69.01.01, 16.03.01 |
| `CC3_shallow_validator` | 65.03.03, 02.01.03, 16.02.01, 47.03.01, 70.02.01 |
| `T0_hard_floor` | 41.04.00, 61.02.28, 18.05.03, 56.14.00, 47.02.12, 16.05.02, 43.01.00 |
| `C4_exception_handling_clinical_adjacent_paths` | 70.01.02, 24.01.03, 60.02.01 |
| `C5_compliance_boundary_integrity` | 24.01.03, 69.01.00 |

`C6_mock_auth_or_fail_open_boundary` is currently a report-layer/code-integrity surface only. It does not yet carry an AIRI mapping row.

Five known gaps are reported for risks that require dynamic evaluation or extend beyond static scan scope.

## File Size Reference

| Repository | HTML size |
|-----------|----------|
| `maziyarpanahi/openmed` (T1, 39/100) | ~164 KB |
| Typical T3 repository | ~40–80 KB |

Size scales with evidence ledger length. The renderer caps the evidence table at 200 rows.

