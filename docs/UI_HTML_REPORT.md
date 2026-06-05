# HTML Report Dashboard

Version: 1.8.3
Status: Active HTML/PDF surface note

STEM BIO-AI ships a **self-contained interactive HTML dashboard** as the primary human-readable output format. In the current `1.8.3` line, the dashboard reflects the post-`C4/C5/C6` code-integrity split, AIRI detector-to-risk reasoning, policy-surface metadata, audit-freshness summaries, and explicit compacting notes for human-readable AIRI/render surfaces. The report is a single `.html` file with inline CSS, SVG, and JavaScript — zero external dependencies, fully offline-capable.

## Generating the Report

```bash
stem scan /path/to/repo --format html
stem scan /path/to/repo --format all    # JSON + MD + HTML + PDF in one pass
```

Output:

- default root: `stem_output/<repo_slug>/<repo_slug>_report.html`
- custom output directory: `<output_dir>/<repo_slug>_report.html`

Example:

- browser preview: <https://htmlpreview.github.io/?https://raw.githubusercontent.com/flamehaven01/STEM-BIO-AI/main/docs/assets/report-preview/yorkeccak_bio_report.html>
- raw artifact: [`docs/assets/report-preview/yorkeccak_bio_report.html`](assets/report-preview/yorkeccak_bio_report.html)

## 5-Section Structure

| Section | ID | Content |
|---------|-----|---------|
| **Executive Summary** | `#s1` | Score gauge, 5-metric stat grid, notable risks, Tier Lock alert banner, Classification Applied state |
| **Decision Path** | `#s2` | Stage bars (S1/S2R/S3/S4 with Stage 3 raw formula), score formula, and policy/configuration explainer |
| **Code Integrity & Contract** | `#s3` | C1–C6 + CC1–CC3 expandable cards, with C4/C5/C6 split visible |
| **AIRI Risk Triggers** | `#s4` | MIT AI Risk Repository donut + covered/gaps toggle table + domain filter cards |
| **Evidence Detail** | `#s5` | Full evidence ledger with severity filter chips |

Navigation between sections via a **sticky top navbar** with scroll-spy active state.

### Tier Lock Alert (Section 1)

When a score ceiling is active, a colored alert banner appears at the top of the Executive Summary:

- **`Tier Lock [T0-FLOOR]`** (red): CA-DIRECT classification with no disclaimer. Score ceiling at 39. Must be resolved before any tier advancement.
- **`Tier Lock [CA-CAP]`** (amber): Clinical-adjacent surface without non-clinical boundary. Score ceiling at 69 (T2 maximum). Adding a non-diagnostic disclaimer resolves this lock.

### Classification Applied (Section 1)

The Policy Boundary card in Section 1 now shows the applied classification state:

```
Classification applied: ca_severity=CA-INDIRECT | score_cap=69 | t0_floor=clear
```

This makes the active cap and severity class inspectable without reading the raw JSON.

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
The AIRI explorer starts with an `All Domains` card, followed by seven domain cards. Each card shows **covered / gaps** counts for that domain. Colors match the MIT AI Risk Navigator palette:

| # | Domain | Badge color |
|---|--------|------------|
| All | All Domains | primary navy |
| 1 | Discrimination & Toxicity | `#B5272A` crimson |
| 2 | Privacy & Security | `#1E3A6E` deep navy |
| 3 | Misinformation | `#C07020` amber |
| 4 | Malicious Actors & Misuse | `#6B3FA0` deep purple |
| 5 | Human-Computer Interaction | `#1B7A4E` deep green |
| 6 | Socioeconomic & Environmental | `#7A6520` olive |
| 7 | AI System Safety, Failures & Limitations | `#1A5568` dark teal |

Click a domain card → risk table filters to that domain only and the `Covered (n)` / `Gaps (n)` toggle labels update to that domain's counts. Click `All Domains` → full table restored. Cards with `0/0` are dimmed but still document bundle coverage boundaries.

### AIRI Toggle (Section 4)
Two-button toggle: `[Covered (n)]` / `[Gaps (n)]`. Composes with the domain filter — both conditions must be satisfied for a row to be visible. The counts shown on the toggle buttons are dynamic and reflect the current domain selection.

Covered AIRI rows surface bounded `why` reasoning derived from:

- the triggered local detector ID,
- the local detector-to-risk mapping justification, and
- the trigger reason surfaced by the scan.

This is a review aid only. It does not mean AIRI independently audited the repository.

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

The HTML renderer is split into three modules:

| File | Role |
|------|------|
| `stem_ai/render_html_components.py` | `_C` palette, `_AIRI_DOMAIN_COLORS/NAMES`, SVG generators (`svg_gauge`, `svg_donut`, `svg_hbar`), card builders (`integrity_card`, `domain_card`, `airi_row`, `evidence_row`) |
| `stem_ai/render_html_styles.py` | `build_css(tc)` f-string (tier-color parameterized), `.domain-card/.domain-active` CSS, `JS` constant with `filterDomain()` + `_applyAiriFilter()` |
| `stem_ai/render_html.py` | Five `_section*()` assemblers + domain-count computation + `render_html(result)` entry point |

The matching PDF surfaces now track the packet tiers:

- `level 1` → `brief_1p.pdf` (legacy quick brief)
- `level 2` → `detailed_5p.pdf` (standard review packet)
- `level 3` → `detailed_7p.pdf` (full evidence packet)

The 5-page and 7-page packets both include AIRI coverage and bounded `why:` explanations, while the 7-page packet adds the deeper closeout and metadata pages.

## Report Preview

![HTML Report Preview](assets/html_report_preview.png)

*Screenshot: current 1.8.3 HTML dashboard surface with the post-C4/C5/C6 integrity split and AIRI domain filtering.*

## Color Palette

Refined across the `1.7.x` line to align with AIRI Navigator's visual language — deeper saturation, cooler backgrounds, AIRI-standard crimson for risk indicators.

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

## AIRI Risk Triggers Section

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

Representative active mapping rows in the `1.8.3` line:

| Detector | AIRI Risk IDs Covered |
|----------|----------------------|
| `CC1_clinical_zero_default` | 62.15.02, 02.09.00, 30.01.02, 69.01.01, 16.03.01 |
| `CC3_shallow_validator` | 65.03.03, 02.01.03, 16.02.01, 47.03.01, 70.02.01 |
| `T0_hard_floor` | 41.04.00, 61.02.28, 18.05.03, 56.14.00, 47.02.12, 16.05.02, 43.01.00 |
| `C2_dependency_pinning` | 33.01.05, 24.04.01 |
| `S1_R2_unsupported_legal_or_compliance_claim` | 69.01.00, 39.25.00 |
| `R2R_D5_single_external_service_dependency` | 60.02.01, 72.04.02 |
| `C5_compliance_boundary_integrity` | 24.01.03, 69.01.00 |

`C4_exception_handling_clinical_adjacent_paths` remains reserved for executable fail-open exception behavior in code.

`C6_mock_auth_or_fail_open_boundary` is currently a report-layer/code-integrity surface only. It does not yet carry an AIRI mapping row.

Five known gaps are reported for risks that require dynamic evaluation or extend beyond static scan scope.

## File Size Reference

| Repository | HTML size |
|-----------|----------|
| `maziyarpanahi/openmed` (T1, 39/100) | ~164 KB |
| Typical T3 repository | ~40–80 KB |

Size scales with evidence ledger length. The renderer caps the evidence table at 200 rows.
