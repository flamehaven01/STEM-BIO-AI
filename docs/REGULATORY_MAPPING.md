# STEM-BIO-AI Regulatory Traceability Assistant
## Version 1.2.2 (Structural Audit-Readiness Mapping)

**Positioning:** STEM-BIO-AI is a **pre-audit structural evidence tool**. It does not determine legal compliance, regulatory clearance, clinical certification, market authorization, or deployer conformance. It identifies observable technical and governance signals that may support a later formal audit.

**Interpretation Rule:** This document maps **detected evidence classes** to **regulatory requirement families**. The result is a **traceability aid**, not a compliance verdict.

---

## 1. Confidence Model for Regulatory Mapping
Every mapping in this document should be read with one of five confidence levels:

- **Strong**: direct structural evidence aligns with a requirement class
- **Moderate**: structural evidence supports part of the requirement
- **Weak-Moderate**: structural evidence is meaningful but still largely indirect or only partially structural
- **Weak**: only surface or declarative signal exists
- **Not Assessed**: outside STEM-BIO-AI scope

This confidence level applies to the **mapping relationship**, not to legal acceptability.

---

## 2. EU AI Act (Regulation 2024/1689)
Mapping of observable signals to high-risk requirement families.

| AI Act Article | Requirement Family | STEM-BIO-AI Evidence Class | Observable Evidence | Mapping Confidence | Boundary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Article 10** | Data governance and data quality | `Data integrity and bias evidence signals` | IRB/dataset citations, provenance-linked references, quantitative subgroup/bias measurement language, validation-boundary language | **Weak** | Detects claim-linked or code-linked evidence of governance intent and subgroup measurement surfaces, but does not verify that the measurements were correctly executed, complete, or regulator-adequate |
| **Article 11** | Technical documentation | `Reproducibility and documentation scaffolding` | CI/CD, lockfiles, environment manifests, containers, reproducibility sections, runnable examples | **Moderate** | Does not establish that technical documentation is complete or regulator-ready |
| **Article 12** | Record-keeping / traceability | `Traceability scaffolding` | changelogs, hash manifests, model/dataset checksum artifacts, versioned config surfaces, explicit manifests, runtime audit-log schemas, decision-event schemas, override-event schemas | **Moderate** | Changelog alone is not runtime logging; deploy-time event logging is outside current scope |
| **Article 13** | Transparency / instructions for use | `IFU scaffolding and claim-boundary signals` | intended-use language, misuse sections, disclaimer/boundary text, input/output interpretation sections, accuracy/metric headings | **Moderate** | Declarative sections do not prove Article 13 completeness |
| **Article 14** | Human oversight | `Control interface signals` | manual override flags, safe interrupt handling, oversight-oriented CLI/config switches, stop/reverse control points | **Weak** | Entry points are not equivalent to operational human oversight procedure; stronger confidence would require role definition, escalation path, override reason capture, and post-hoc review evidence |
| **Article 15** | Accuracy, robustness, cybersecurity | `Safety and failure-behavior signals` | safe exception handling, silent-mock detection, parser guards, reproducibility artifacts, unsafe subprocess findings | **Moderate** | Does not perform runtime performance validation, penetration testing, or cybersecurity assurance |

---

## 3. IMDRF / SaMD Evidence Families
STEM-BIO-AI can support pre-audit review against common SaMD evidence families, but only at the level of structural readiness signals.

| SaMD Evidence Family | STEM-BIO-AI Evidence Class | Observable Evidence | Mapping Confidence | Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **Clinical claim surface / intended-use signal** | `Stage 1 domain and boundary signals` | bio/clinical terminology plus explicit intended-use, limitation, and non-clinical-use boundaries | **Weak** | This is **not** clinical validation |
| **Scientific validity signal** | `Claim-linked provenance signals` | literature, dataset, or benchmark references tied to the specific biological/clinical association being claimed | **Weak-Moderate** | Citation presence alone does not prove valid clinical association |
| **Analytical / technical validation signal** | `Domain test and reproducibility signals` | domain-specific tests, known fixtures, parser guards, environment reproducibility, error handling around domain outputs | **Moderate** | Does not prove target-population performance |
| **Clinical-context boundary and traceability signal** | `Risk/boundary disclosure and traceability signals` | intended-use sections, misuse sections, explicit limitations, dataset provenance, subgroup analysis mention | **Weak** | Does not establish that the system achieves intended clinical purpose in a target population |

**Important:** If this document uses the phrase `clinical`, it refers to **claim surface and audit-readiness context**, not to proven clinical utility.

---

## 4. FDA / GMLP / PCCP-Oriented Readiness Signals
These mappings are included because iterative AI/ML device development often depends on change management and lifecycle evidence.

| Framework | STEM-BIO-AI Evidence Class | Observable Evidence | Mapping Confidence | Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **FDA AI-enabled device software functions** | `Change-control and traceability signals` | changelogs, versioned configs, hash manifests, release artifacts, benchmark calibration history | **Moderate** | Does not establish safety/effectiveness for submission |
| **IMDRF GMLP lifecycle expectations** | `Lifecycle discipline signals` | reproducibility artifacts, explicit limitations, domain tests, governance memory, advisory trace packets | **Moderate** | Does not replace design controls or formal QMS |
| **Predetermined Change Control Plan (PCCP) readiness signal** | `Versioned change evidence` | benchmark deltas, changelog granularity, manifest changes, explicit model/data version surfaces | **Weak-Moderate** | Detects change evidence presence, not PCCP adequacy |

---

## 5. Evidence Grading vs. Empirical Compliance
To avoid compliance theater, separate the **signal** from the **requirement**.

| Signal detected by STEM-BIO-AI | Requirement Family | Alignment Status |
| :--- | :--- | :--- |
| **Changelog (T3)** | Record-keeping / change history | **SCAFFOLDING ONLY.** Indicates change tracking discipline, not runtime audit logging |
| **CLI Override / Stop Flag** | Human oversight | **INTERFACE SIGNAL ONLY.** Indicates a mechanism may exist, not that oversight is procedurally or organizationally adequate |
| **Disclaimer / Intended-Use Section** | Transparency / IFU | **DECLARATIVE SIGNAL ONLY.** Indicates a boundary statement exists, not that IFU is complete |
| **Silent-mock finding absent** | Robustness | **NEGATIVE SIGNAL ONLY.** Failure mode not observed by current scanner; does not prove absence under all execution paths |
| **SMILES parser guard present** | Technical validation hygiene | **HYGIENE SIGNAL ONLY.** Safer parsing surface, not proof of chemical or biological validity |

---

## 6. New Deterministic Diagnostics and Regulatory Relevance
The proposed deterministic diagnostics strengthen traceability only when described conservatively.

| Detector | Primary Value | Likely Regulatory Relevance | Mapping Confidence | Boundary |
| :--- | :--- | :--- | :--- | :--- |
| `SMILES-DECEPT` | Detect malformed or suspicious molecular string surfaces, placeholder outputs, and missing parser guards | Supports analytical/technical validation hygiene review | **Weak-Moderate** | Not a chemical validity or efficacy detector |
| `SILENT-MOCK` | Detect mock/simulated outputs continuing through functional paths | Supports robustness and misleading-output risk review | **Moderate** | Does not prove runtime absence of all simulated fallbacks |
| `RUN-TRACE` | Detect unsafe subprocess construction around bio tools | Supports robustness and secure execution review | **Moderate** | Initial heuristic taint analysis is evidence-only |
| `TRACE-MANIFEST` | Detect hash/version/config trace artifacts | Supports traceability and change-control readiness review | **Moderate** | Artifact presence does not prove procedural retention policy |
| `IFU-DEEP-SCAN` | Detect richer intended-use and misuse sections | Supports transparency scaffolding review | **Weak-Moderate** | Structural presence only; does not establish IFU completeness or correctness |
| `SAFETY-INTERRUPT` | Detect stop/override/safe-state code interfaces | Supports human oversight interface review | **Weak-Moderate** | Interface presence is not oversight governance |

---

## 7. Mandatory Warning for Institutional Buyers
STEM-BIO-AI detects the **presence of structural evidence and accountability artifacts**.

- `T0-T1`: insufficient visible scaffolding for serious pre-audit confidence
- `T2-T3`: meaningful structural evidence exists, but gaps remain
- `T4`: **strongest observed structural evidence / audit-readiness signal**

`T4` is **not** regulatory approval, clinical certification, market authorization, legal conformity, or deployer approval.

**STEM-BIO-AI DOES NOT:**
1. Verify the correctness of clinical or biological data.
2. Verify runtime behavior under all operational conditions.
3. Perform live human oversight.
4. Produce deployer-grade runtime logs.
5. Establish legal compliance with the EU AI Act, FDA expectations, IMDRF guidance, or ISO 13485 by itself.

**Institutional Action Recommendation:**  
Use STEM-BIO-AI as a **pre-audit gate** and **traceability assistant**. Low scores identify missing structural prerequisites. Higher scores indicate that a repository may contain enough observable scaffolding for deeper expert review.

---

## 8. ISO 13485:2016 / QMS-Oriented Mapping
STEM-BIO-AI can provide automated structural signals relevant to quality-system review in medical software contexts.

- **7.3.3 Design and development outputs**  
  `Stage 4` containers, lockfiles, manifests, and reproducibility sections can support evidence of controlled technical output surfaces.

- **7.3.7 Control of design and development changes**  
  `Stage 3: T3`, hash manifests, release notes, and benchmark delta traces can support change-history review.

- **7.3.9 Control of design and development files**  
  The MICA memory layer and versioned docs can support design-file traceability signals.

**Boundary:** These are quality-system support signals, not proof that a QMS is implemented or effective.

---

## 9. Recommended Report Output Shape
If regulatory traceability is surfaced in reports, it should remain explicit about evidence type and strength.

- `evidence_strength`: quality of the observed repository evidence itself
- `mapping_confidence`: confidence that this evidence class meaningfully maps to the cited requirement family

These fields may differ. For example, a strong manifest artifact may still map only weakly to a legal requirement if major operational elements remain out of scope.

```json
{
  "requirement": "EU_AI_ACT_ARTICLE_12_RECORD_KEEPING",
  "evidence_type": "hash_manifest_or_versioned_trace_surface_detected",
  "evidence_strength": "strong",
  "mapping_confidence": "moderate",
  "not_assessed": [
    "legal_compliance",
    "deployer_operational_logging",
    "runtime_event_completeness"
  ],
  "finding_refs": [
    "S4_checksum_files:repo/checksums.txt:001",
    "T3_changelog_release_hygiene:CHANGELOG.md:001"
  ]
}
```

---

## 10. Implementation Note
Reports should describe this layer as:

- `Regulatory Traceability Assistant`, or
- `Structural Audit-Readiness Mapping`

They should **not** describe it as:

- `compliance certification`
- `regulatory approval engine`
- `clinical validation engine`
