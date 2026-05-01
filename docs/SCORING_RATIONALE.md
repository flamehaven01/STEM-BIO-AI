# STEM BIO-AI Scoring Rationale

Version: 1.5.6
Status: Authoritative design record. Update with each structural score change.

---

## 1. What This Framework Measures

STEM BIO-AI answers one question:

> Does the visible artifact surface of this repository support institutional trust in a bio/medical AI context?

It is **not** a clinical validation tool, a security audit, or a regulatory submission. It is a deterministic text-surface scan that classifies the *evidence posture* of a repository — the degree to which the author has made responsible claims, disclosed limitations, and maintained technical hygiene.

**The framework measures author behavior and surface signals, not clinical accuracy.**

A repo that scores T3 has strong evidence signals. It has not been clinically validated.

---

## 2. Formula

```
final = clamp(0.4 * S1 + 0.2 * S2R + 0.4 * S3 - C1_penalty, score_cap)
```

### Weight rationale: 0.4 / 0.2 / 0.4

Stage 1 (README intent) and Stage 3 (engineering accountability) carry equal weight because both are independently necessary. A repo with a responsible README but no tests or CI is not trustworthy. A repo with complete CI but hype-filled claims is also not trustworthy.

Stage 2R (repo-local consistency) carries half the weight because it is a *bounded substitute* for full cross-platform verification. In LOCAL_ANALYSIS mode, the CLI cannot verify what the author says externally — on X, LinkedIn, or conference slides. Stage 2R checks only whether the repo's own surfaces agree with each other. This is weaker evidence, so it receives half the weight.

When Stage 2 is fully N/A (no external evidence and no local repo), its weight redistributes 50/50 to S1 and S3, preserving the symmetry of the two primary lanes.

This weight split was stabilized in spec FAILURE 7 (v1.0.3), which found that equal 1/3 weights caused instability when Stage 2 = N/A.

---

## 3. Baseline 60

Both Stage 1 and Stage 2R start at 60. Stage 3 starts at 0.

The 60 baseline for S1 and S2R encodes a deliberate prior: a repository that exists and has accumulated structure (README, package metadata, code) has already crossed the minimal threshold of intentionality. It is not a nascent experiment. It deserves a neutral starting position, not a deficit position.

Stage 3 starts at 0 because its items (CI, tests, changelog, provenance, bias disclosure, COI) are independently verifiable engineering and governance commitments. A repo that has none of them earns none of the points.

**The 60 baseline is a design convention, not an empirically calibrated number.** It was set at the T2/T3 midpoint (halfway between 55 and 69) so that a repo with no positive or negative signals lands at T2 — the "proceed with caution" tier.

---

## 4. Tier Boundaries

| Tier | Range | Meaning | Derivation |
|------|-------|---------|------------|
| T0 Rejected | 0–39 | Do not rely on without independent expert validation | Baseline minus 21+: requires serious structural failures (no README + hype claims, or hard-floor trigger) |
| T1 Quarantine | 40–54 | Exploratory review only; no patient-adjacent use | Below baseline: minimal positive signals, or near-baseline with active deductions |
| T2 Caution | 55–69 | Research reference and supervised non-clinical technical review only | Near baseline: weak positive signals; also enforced ceiling for clinical-adjacent repos without explicit boundary |
| T3 Supervised | 70–84 | Supervised institutional review candidate | Baseline + meaningful positive signals across at least two stages |
| T4 Candidate | 85–100 | Strong evidence posture; clinical deployment still requires independent validation | Baseline + strong positive signals across all three stages with no major hype deductions |

The boundaries are symmetric around the 60 baseline:

```
T0/T1 boundary: 60 - 20 = 40   (no-README penalty alone)
T1/T2 boundary: 60 - 5  = 55   (near-baseline deficit zone)
T2/T3 boundary: 60 + 10 = 70   (first meaningful rigor signal above baseline)
T3/T4 boundary: 60 + 25 = 85   (sustained positive signal required)
```

**These are conventional thresholds.** They have internal consistency (anchored to the baseline) but have not been validated against an external clinical ground truth. They are defensible as classification conventions; they are not calibrated risk thresholds.

---

## 5. Stage 1: README Intent and Signal Cost

Stage 1 scans the README and package metadata for two classes of evidence:

### Hype Penalties (H1–H6)

Hype is penalized because overclaiming in a bio/medical AI context is a patient-safety concern. An author who claims clinical certainty without evidence, or advertises autonomous clinician replacement, is making a representational commitment the software may not support.

| Item | Pattern class | Penalty | Rationale |
|------|--------------|---------|-----------|
| H1 Clinical certainty | "proven clinically", "FDA cleared", specific accuracy claims without citation | -10 | Clinical certainty claims require evidence; absence of citation makes them unverifiable |
| H2 Regulatory approval | "CE marked", "FDA approved", "cleared for use" without reference | -10 | False regulatory claims are directly dangerous |
| H3 Autonomous replacement | "replaces clinicians", "no human oversight required" | -10 | Autonomous clinical framing triggers T0 hard floor when CA-DIRECT and no disclaimer |
| H4 Breakthrough marketing | "revolutionary", "groundbreaking", "game-changing" | -5 | Lower penalty — marketing language is common and less directly dangerous |
| H5 Universal generalization | "works on all populations", "universal", "any clinical context" | -5 | Overgeneralization signals poor evaluation discipline |
| H6 Perfect accuracy | "100% accuracy", "zero false negatives", "guaranteed" | -10 | Guaranteed-accuracy claims in clinical contexts are epistemically false |

### Responsibility Signals (R1–R5)

Positive signals are rewarded because they represent author behavior — not capability — that directly reduces risk to institutional adopters.

| Item | Trigger | Bonus | Rationale |
|------|---------|-------|-----------|
| R1 Limitations section | Explicit limitations or validation-boundary section heading in README | +15 | The most important single signal: does the author bound their own claims? |
| R2 Regulatory framework | IRB, SaMD, FDA, CE, or clinical-reporting framework language | +15 / -10 (CA-DIRECT) / -5 (CA-INDIRECT) | Regulatory awareness is mandatory context for clinical-adjacent tools |
| R3 Clinical disclaimer | "NOT a substitute for clinical judgment" or equivalent | +10 / -10 (CA-DIRECT) / -5 (CA-INDIRECT) | Binary marker of author intent regarding patient-facing use |
| R4 Demographic bias | Population limits, subgroup analysis, fairness or stratification language | +10 | Signals awareness that model performance is not universal |
| R5 Reproducibility provisions | Seed, lockfile, checksum, or replication language | +10 | Connects to replication integrity; rewards cross-surface consistency |

R2 and R3 have **asymmetric behavior** for clinical-adjacent repos: if those repos lack regulatory or boundary language, they receive an active penalty rather than zero. This reflects the elevated expectation for repos that handle clinical data or produce clinical-adjacent outputs.

### Stage 1 Range

Given the baseline 60, the additions and penalties above, and the `clamp(0, 100)` applied:

- Theoretical minimum: roughly 0 (no README + multiple hype penalties)
- Theoretical maximum: roughly 100 (baseline + R1 + R2 + R3 + R4 + R5 = 60+15+15+10+10+10 = 120, clamped to 100)
- Typical range for active bio/medical AI repos: 45–85

---

## 6. Stage 2R: Repo-Local Consistency

Stage 2R is an approximation of cross-platform verification (Stage 2) using only local repository files. It cannot verify what the author claims externally.

It asks: **do the repository's own surfaces agree with each other?**

| Item | Trigger | Effect | Rationale |
|------|---------|--------|-----------|
| R2R-1 | README ∩ package metadata share bio/medical terms | +15 | Domain vocabulary alignment between intent statement and implementation surface |
| R2R-2 | README ∩ docs share bio/medical terms | +10 | Corroborating domain evidence in tutorial/troubleshooting surfaces |
| R2R-3 | README/workflow/test surfaces share CI or test signals | +10 | Intent aligns with engineering practice |
| R2R-4 | Limitation language appears in ≥2 of {README, docs, changelog} | +10 | Limitation disclosure that spans surfaces is more credible than a single mention |
| R2R-D1 | Disclaimer present but clinical deployment claims also present | -20 | Internal contradiction: the repo simultaneously disclaims and endorses clinical use |
| R2R-D2 | Clinical-adjacent signals with no disclaimer anywhere | -20 | Absence of boundary in a clinical-adjacent repo is an active warning signal |
| R2R-D3 | README version and package version disagree | -10 | Stale metadata indicates release hygiene failure |
| R2R-D4 | README/docs claim runnable workflow without matching support surfaces | -15 | Unsupported workflow claims mislead integrators |

### Why the D-deductions are heavy

D1 (internal contradiction) and D2 (missing boundary) are both -20 because they represent the most dangerous failure mode at this layer: a repo that either actively contradicts its own safety signals or provides no safety signal at all.

---

## 7. Stage 3: Engineering Accountability

Stage 3 is a deterministic engineering-accountability rubric. T1, T2, and B3 remain presence-oriented; T3, B1, and B2 use bounded three-tier scoring.

### Rationale for bounded partial scoring

The local CLI still avoids semantic quality judgments. Partial credit is allowed only where deterministic text evidence is available: a changelog can be present with or without bug-fix/security entries, a dependency manifest can be present with or without data-source/IRB language, and limitations language can appear with or without measurement evidence. This improves precision while keeping the scan reproducible.

| Item | Max pts | Trigger | Rationale |
|------|---------|---------|-----------|
| T1 CI/CD | 15 | Workflow files in .github/workflows/ | Automated testing is the baseline of professional software hygiene |
| T2 Domain tests | 15 (8 partial) | test/ dir with bio-domain vocabulary (or generic tests) | Tests that cover domain-specific outputs, not just infrastructure |
| T3 Changelog | 0 / 5 / 15 | Absent / present / present with bug-fix, patch, or security entries | Release history transparency; stronger credit when corrective maintenance is visible |
| B1 Dependency provenance | 0 / 10 / 15 | No manifest / manifest present / manifest plus data-source, dataset citation, or IRB language | Reproducibility requires declared dependencies; bio/medical provenance also needs data-source context |
| B2 Bias/limitations | 0 / 8 / 15 | No vocabulary / bias or limitation vocabulary / vocabulary plus measurement evidence or test coverage | Consistent with R1/R4 in Stage 1; stronger credit requires measurement or test evidence |
| B3 COI/funding | 5 | COI, funding, or sponsor language in README/docs/FUNDING.md | Lower max reflects that COI disclosure is less universally expected than technical hygiene |

Raw max = 80. Normalized to 100: `round((raw / 80) * 100)`.

The 80-point denominator (not 85) was corrected in spec FAILURE 27. An earlier version used 85 as the denominator, which was a 5-point error of unknown origin.

---

## 8. Score Cap Policy

Two hard ceilings apply when clinical risk signals are present without counterbalancing boundary language.

### CA + no disclaimer: cap 69 (max T2)

A repository with clinical-adjacent signals (either CA-DIRECT or CA-INDIRECT) that lacks any explicit disclaimer cannot score T3 or above, regardless of its S1/S2R/S3 performance.

**Rationale:** T3 ("Supervised institutional review candidate") implies sufficient maturity for institutional consideration. A clinical-adjacent repo with no boundary disclaimer has not met the minimum responsible disclosure standard for that tier. The cap enforces a necessary-but-not-sufficient condition: T3 requires not just high scores but also explicit clinical-use boundary language.

### T0 hard floor: cap 39 (forced T0)

When all three conditions hold simultaneously:
- `ca_severity == "CA-DIRECT"`
- `has_disclaimer == False`
- `T0_HARD_FLOOR_TERMS` match (autonomous, clinical decision support, diagnosis, treatment recommendation, triage, risk score)

The score is capped at 39, forcing T0.

**Rationale:** The combination of direct clinical output + autonomous framing + no disclaimer represents the highest-risk posture in the framework. A scoring penalty is insufficient here because even a heavily penalized repo could still score T1 or T2 through strong S3 signals. The hard floor bypasses the scoring formula entirely (spec Principle 6: "Hard floors over soft penalties for catastrophic risk").

---

## 9. Stage 4: Replication Evidence

Stage 4 is reported separately and **does not affect the final score or tier**.

Stage 4 answers: *can the results be reproduced?* It collects evidence of containers, lock files, checksum files, dataset URLs, model artifact references, seed settings, and reproducibility README sections.

**Why separate?**

Including Stage 4 in the main score would create a systematic bias against production-grade tools (which don't need Dockerfiles or seeds) and toward academic research repos (which typically have all of these). The framework's primary question is about trust posture, not research reproducibility. A clinical decision support tool that is deployed and validated does not need a Makefile `reproduce:` target.

Stage 4 produces a separate R0–R4 replication tier that informs institutional reviewers without distorting the primary T0–T4 classification.

---

## 10. C1–C4: Code Integrity

C1–C4 are code-level checks available only in LOCAL_ANALYSIS mode. They do not contribute to S1/S2R/S3 scoring.

| Item | Signal | Effect |
|------|--------|--------|
| C1 Hardcoded credentials | AWS/GH/OpenAI key patterns in code, excluding obvious placeholders | -10 risk penalty applied to final score |
| C2 Dependency pinning | Loose `>=` or unversioned deps in manifests | WARN only, no score change |
| C3 Deprecated patient paths | Patient metadata patterns in deprecated/legacy/archive dirs | WARN only, no score change |
| C4 Fail-open exceptions | `except: pass` or `except Exception: pass` in code | WARN only, no score change |

Only C1 affects the final score. C2–C4 are reported as code integrity warnings because they represent elevated risk but do not rise to the level of score penalties in the current calibration.

---

## 11. Known Calibration Gaps

This section documents what the framework does not claim.

**Tier boundaries are conventional, not empirically calibrated.**
The 40/55/70/85 thresholds are internally consistent (anchored to baseline 60) but have not been validated against a clinical ground truth dataset or expert consensus panel. They should not be used as regulatory thresholds.

**H1–H6 and R1–R5 point values are asserted, not derived.**
The penalty/bonus magnitudes reflect the relative severity of each signal (clinical certainty hype is penalized more than marketing language) but have not been calibrated against observed harm rates.

**Stage 3 bounded scoring still loses depth information.**
The CLI now distinguishes basic presence from stronger deterministic evidence for T3, B1, and B2. It still cannot judge whether a changelog is comprehensive, whether data-source language is sufficient for a specific institution, or whether a small domain test suite is scientifically adequate. This remains a precision tradeoff for determinism.

**Local-10 benchmark validates consistency, not correctness.**
The ten-repo benchmark (within-1-tier 100% after v1.3.1) tests that the scorer is internally stable. It does not test whether the tier assignments are clinically meaningful.

**Stage 2 (cross-platform verification) is unavailable in LOCAL_ANALYSIS mode.**
The full Stage 2 score — which checks whether the author's external communications (X, LinkedIn, conference talks) are consistent with the repository — is N/A in CLI mode. Stage 2R is a bounded local substitute.

---

## 12. What a Tier Does and Does Not Mean

| Tier | What it means | What it does NOT mean |
|------|--------------|----------------------|
| T4 | Strong evidence posture across all three evaluation stages | Clinically validated; safe for patient-facing deployment |
| T3 | Meaningful rigor signals; institutional review candidate | Approved for clinical use; independently audited |
| T2 | Near-baseline; research reference acceptable | Production-ready; free of clinical risk |
| T1 | Below-baseline; exploratory review only | Unsafe for any use; definitively flawed |
| T0 | Rejected on structural grounds or hard-floor trigger | Confirmed harmful; adversarially constructed |

STEM BIO-AI tiers are evidence classifications, not clinical risk ratings. Every tier from T1 to T4 requires independent expert validation before patient-adjacent deployment.
