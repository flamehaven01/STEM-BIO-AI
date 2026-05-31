# Deterministic Diagnostics for Bio-AI Integrity
## Version 1.7.9 (Active deterministic bio diagnostics note)

This document is the active deterministic diagnostics specification for STEM BIO-AI's bio-focused deterministic lane. The local lane is implemented as evidence-bearing repository diagnostics inside `stem_ai/detector_bio.py`. The optional AI lane remains advisory, opt-in, and non-authoritative.

---

## 1. Executive Summary
Traditional LLM-based auditing suffers from "hallucination of safety." To reach the strongest structural audit-readiness tier, STEM-BIO-AI must move from **interpreting claims** (README analysis) to **measuring reality** (Code/Config analysis). We therefore separate the problem into two lanes:

1.  **Lane A -- Deterministic local diagnostics**
    * Fast, reproducible, no network requirement.
    * Produces line-level or string-level evidence suitable for `evidence_ledger`.
    * Handles syntax integrity, placeholder patterns, silent mock fallbacks, and unsafe bio-tool subprocess construction.

2.  **Lane B -- Optional AI-assisted semantic review**
    * Runs only as an explicit second pass.
    * Consumes extracted evidence packets, not arbitrary raw repository text by default.
    * Helps with nuanced SMILES plausibility review, medicinal-chemistry style pattern review, and ranking suspicious molecules for manual inspection.

The local deterministic lane is authoritative for hard findings. The AI lane is advisory and may elevate review priority, but it must not silently override deterministic evidence.

---

## 1A. Implementation Status (STEM BIO-AI v1.7.9)

Implemented now:
1. `SMILES-DECEPT` Lane A0 conservative surface scanner
2. `SMILES-DECEPT` Lane A1 optional RDKit validation lane
3. `SILENT-MOCK` fallback detection
4. `TRACE-MANIFEST` traceability surface detection
5. `RUN-TRACE` bio-tool subprocess heuristics
6. Markdown / explain report surfacing for bio deterministic diagnostics
7. Registry-driven regulatory traceability attachment using deterministic evidence without score override
8. Performance-oriented AST context reuse, node pre-bucketing, generated-path pruning, and optional RDKit gating that preserve detector semantics while reducing scan overhead

Implemented as evidence-only:
1. Findings are emitted into `evidence_ledger`
2. Findings appear in Markdown, HTML, PDF summaries, and `--explain`
3. Findings do not change `final_score` or `formal_tier`

Not yet implemented:
1. AI-assisted Lane B semantic review
2. `MOUNT-AUDIT`
3. `IFU-DEEP-SCAN`
4. `SAFETY-INTERRUPT`

---

## 2. Technical Roadmap

### 2.1 [SMILES-DECEPT] SMILES Mock & Integrity Scanner
*   **Objective:** Identify "Chemistry Slop" — where a model claims to produce biological molecules but outputs placeholders or invalid SMILES.
*   **Implementation:**
    *   **Lane A0 / Stdlib-Only Surface Scan:** Default path with no chemistry dependency; focuses on malformed or suspicious SMILES-like strings and unsafe parser usage patterns.
    *   **Lane A1 / Optional Chemistry Parser Validation:** If RDKit is installed, validate candidate SMILES via `MolFromSmiles(...)` and treat parser failure as stronger deterministic evidence. This lane remains local and optional.
    *   **Lane A / Phase 1 (Local Heuristic):** Scan for hardcoded strings matching SMILES-like patterns. Flag strings with low entropy (e.g., `CCCCCCCCCC`), extremely short length (< 4 heavy atoms unless explicitly example/test context), repeated placeholder patterns, or molecule lists where a large fraction are duplicated.
    *   **Lane A / Phase 2 (Local Grammar & State Machine):**
        *   **Balanced Parentheses:** Verify branching logic integrity using a stack-based counter for `(` and `)`.
        *   **Ring Label Pairing:** Tokenize one-digit ring labels (`1`-`9`) and two-digit labels (`%10`, `%11`, etc.) and verify that each label closes correctly while active. Already-closed labels may be reused later within the same SMILES string, so the implementation must maintain an active closure map rather than enforce a naive global digit-count rule.
        *   **Bracket Integrity:** Verify `[` and `]` are paired and contain syntactically plausible atom tokens.
        *   **Token Validity:** Verify basic element symbol validity (B, C, N, O, P, S, F, Cl, Br, I, etc.), bond markers, aromatic symbols, and ring tokens.
        *   **Boundary Note:** This phase is a conservative syntax-screen, not a full SMILES parser. It is expected to catch obvious malformed strings and suspicious structure tokens, but not to establish full cheminformatics correctness without an external chemistry engine.
    *   **Lane A / Phase 3 (Surface Safety Checks):**
        *   **Parser-Guard Pattern:** Detect `MolFromSmiles(...)`, `Chem.MolFromSmiles(...)`, `dm.to_mol(...)`, or equivalent calls and verify that the returned object is checked for `None` or handled via explicit error logic before downstream use.
        *   **Placeholder Context Check:** Flag suspicious reuse of trivial molecules (`CCO`, `c1ccccc1`, `CCCC`, etc.) in non-example, non-test, non-doc contexts.
        *   **Entropy/Redundancy Check:** Flag batches where a high proportion of outputs are identical, near-identical, or structurally repetitive placeholder strings.
    *   **Lane B / Optional AI-Assisted Review:**
        *   **Input:** Deterministic evidence packet containing extracted candidate SMILES, file/line references, parser-guard findings, duplication statistics, and context snippets.
        *   **Task:** Ask an AI model to classify whether suspicious strings look like placeholders, malformed chemistry, low-diversity output, or domain-inappropriate output for the claimed task.
        *   **Output Contract:** AI must cite each reviewed molecule by finding ID, return a confidence bucket, and distinguish `syntax concern`, `semantic concern`, and `manual review needed`.
        *   **Boundary:** AI review is advisory only. It does not prove chemical validity and does not override local parser-guard or syntax findings.
    *   **Public Wording Constraint:** This detector should be described as a **conservative SMILES surface integrity scanner**. It does not establish full chemical validity, medicinal usefulness, synthetic feasibility, binding plausibility, or efficacy.
*   **Required Dependency:** None (Python Standard Library).
*   **Optional Dependency:** RDKit for Lane A1 chemistry parser validation.

### 2.2 [MOUNT-AUDIT] Bio-Infrastructure Volume Scanner
*   **Objective:** Identify "BioClaw" failure modes — writable mounts on sensitive biological databases or clinical data directories.
*   **Implementation:**
    *   **Surface Scan:** Recursive search for `Dockerfile`, `docker-compose.yml`, and Kubernetes manifests.
    *   **Rigor Check:** Flag volume mappings that omit the `:ro` (read-only) flag when mapping to known data directories (`/data`, `/datasets`, `/models`, `/workspace`).
    *   **Permission Shadowing:** Detect `chmod 777`, `chmod -R a+w`, privileged container settings, writable host-path or PVC mounts, or ownership/mode changes that make sensitive biological artifacts writable or obscure expected access boundaries.
    *   **Evidence:** File path + line number of the insecure mount/permission.
*   **Dependency:** None.

### 2.3 [RUN-TRACE] Bio-Insecure Subprocess Analysis
*   **Objective:** Identify "Biomni" failure modes — unvalidated shell execution in medical analysis pipelines.
*   **Implementation:**
    *   **AST Analysis:** Extend `detector_ast.py` to trace `subprocess.*`, `os.system`, and `eval`.
    *   **Context Check:** Identify if shell execution is used for critical bio-tools (e.g., `blast`, `samtools`, `bwa`, `bcftools`) and check if `shell=True` is enabled (High Risk).
    *   **Taint Check (Heuristic):** Flag calls where the command string is constructed via f-strings, concatenation, or `.format()` using variables that are likely external-input carrying (e.g., `query`, `input`, `sample`, `user_path`, `request_path`). Simple string formatting alone is not sufficient for a hard finding.
    *   **Severity Policy (Initial Release):**
        *   `shell=True` with known bio-tool invocation -> `warn`
        *   `shell=True` plus external-input taint indicators -> `high-priority warn`
        *   direct `os.system(...)` with external-input taint indicators -> `high-priority warn`
        *   initial release output is **evidence-only** and does not change final score until benchmark calibration is complete
    *   **False-Positive Boundary:** Paths derived from fixed internal config, repository constants, or static workflow definitions should not be treated as equivalent to user-controlled request input.
*   **Dependency:** None (`ast` stdlib).

### 2.4 [SILENT-MOCK] Library Fallback Detector
*   **Objective:** Identify silent fallbacks to mock/simulated data when biological dependencies are missing (Empirical pattern found in `Biomni/immunology.py`).
*   **Implementation:**
    *   **Import-Time Fallback:** Scan for `try...except...` blocks surrounding `import rdkit`, `import biopython`, `import scanpy`, etc., where the `except` block sets a `use_mock = True` flag, logs "Using simulated data", or silently swaps to a synthetic provider.
    *   **Runtime Fallback:** Detect production-path branches such as `if USE_MOCK`, `DEMO_MODE`, `SIMULATE_DATA`, or environment-driven mock toggles that redirect real analysis code into synthetic output paths without an explicit hard-stop or visible disclosure.
    *   **Residual Test Logic in Production:** Flag `skipif`, `mock`, `fake`, `dummy`, or simulation-oriented control flow that appears in non-test runtime modules and influences output generation.
    *   **Severity Policy:**
        *   mock surface present but clearly disclosed and non-clinical/demo scoped -> `warn`
        *   mock/simulated output continues through functional analysis path without explicit boundary -> `fail candidate`
        *   final score mapping should remain gated behind benchmark evidence; initial release should emit evidence and recommended severity
    *   **Integrity Penalty:** If `clinical_adjacent_severity` is high, a silent fallback to mock data without a hard error is a clinical risk aligned with `C3/C4`.
*   **Dependency:** None.

### 2.5 [TRACE-MANIFEST] Traceability Artifact Scanner
*   **Objective:** Identify evidence of Art 12 (Record-keeping) intent via versioned configuration and hash manifests.
*   **Implementation:**
    *   **Heuristic:** Scan for files matching `manifest.json`, `checksums.txt`, `model_hashes.yaml`, or `.lock` files that include cryptographic hashes of non-code artifacts (models, datasets).
    *   **Config Tracking:** Flag usage of `hydra`, `pydantic-settings`, or `.env` files that explicitly version environment parameters.
    *   **Runtime Log Schema Surface:** Detect files or schema fragments such as `audit_log_schema.json`, `event_log_schema.yaml`, `decision_event`, `override_event`, `model_version`, `dataset_hash`, `operator_id`, `timestamp`, `input_hash`, and `output_hash`.
*   **Dependency:** None.

### 2.6 [IFU-DEEP-SCAN] Transparency & Misuse Detector
*   **Objective:** Move beyond simple disclaimers to identify Art 13 (Transparency) structural components.
*   **Implementation:**
    *   **Regex Scan:** Search for high-fidelity section headers: `Intended Use`, `Foreseeable Misuse`, `Interpretation Guidance`, `Accuracy Metrics`, `Cybersecurity Posture`.
    *   **Scoring Boundary:** Higher weight should apply only when a target section has a non-empty body and includes specific misuse cases, boundary language, and metric or limitation references. Headers alone are not sufficient evidence.
*   **Dependency:** None.

### 2.7 [SAFETY-INTERRUPT] Human Oversight Interface Detector
*   **Objective:** Identify the *mechanism* for Art 14 (Human Oversight) via code-level entry points.
*   **Implementation:**
    *   **AST Analysis:** Scan for signal handlers (`signal.signal`), explicit "Stop" flags in config loops, or `try...except KeyboardInterrupt` blocks that transition to a `SAFE_STATE`.
    *   **CLI Logic:** Detect boolean flags like `--force`, `--override`, `--manual` in Argparse/Click definitions that allow a human to bypass or reverse an AI-driven decision.
    *   **Reason-Capture Surface:** Detect override reason fields, reviewer identity fields, escalation notes, or post-hoc review capture surfaces associated with manual interruption or override.
*   **Dependency:** None (`ast` stdlib).

---

## 3. Integration with STEM-BIO-AI CORE
These diagnostics align with the current **Code Integrity (C1-C6)** and bio-diagnostic surfaces in the `1.7.9` line:

- **SMILES-DECEPT** -> bio deterministic diagnostics surface first; possible future linkage to `C3` or a dedicated bio-integrity lane after benchmark review
- **MOUNT-AUDIT** -> future hardening candidate; not currently shipped in the active runtime
- **RUN-TRACE** -> bio deterministic diagnostics surface first; may later inform `C4` or downstream governance review if benchmarked
- **SILENT-MOCK** -> bio deterministic diagnostics surface first; conceptually adjacent to `C6` when mock or demo behavior weakens local/self-host trust boundaries, but not currently score-linked
- **TRACE-MANIFEST** -> Stage 4 / regulatory-traceability support surface, not a direct Code Integrity penalty lane

**Regulatory Relevance Note:** These mappings are engineering-risk mappings inside STEM-BIO-AI CORE. They should not be restated externally as direct evidence of legal compliance without the traceability boundaries described in `REGULATORY_MAPPING.md`.

**Current boundary note:** `C4`, `C5`, and `C6` are now intentionally split:

- `C4` is reserved for executable fail-open exception behavior in code
- `C5` is reserved for unsupported legal/compliance or clinical-boundary integrity warnings
- `C6` is reserved for mock-auth, auto-login, or no-auth local/self-host trust-boundary warnings

The deterministic bio diagnostics lane can support or contextualize these surfaces, but it does not silently rewrite them.

---

## 4. Two-Lane SMILES Review Policy
SMILES review is feasible in both a simple local lane and a more precise AI-assisted lane, but they answer different questions.

### 4.1 What local deterministic review can do well
1.  Detect malformed or suspicious SMILES surface patterns without network access.
2.  Detect missing parser guards around common cheminformatics parsers.
3.  Detect placeholder, duplicated, or low-diversity molecule output surfaces.
4.  Produce exact evidence that a human can verify line-by-line.
5.  Serve as a deterministic pre-filter before any optional chemistry-engine or AI-assisted review.

### 4.2 What local deterministic review cannot prove
1.  Medicinal usefulness.
2.  Synthetic feasibility.
3.  Binding plausibility.
4.  Biological efficacy.
5.  Full chemical validity beyond the implemented grammar checks.
6.  Correct interpretation of every legal SMILES edge case without a dedicated chemistry parser.

### 4.3 What AI-assisted review can add
1.  Triage suspicious SMILES batches into likely placeholder output vs. plausible chemistry.
2.  Compare claimed task context (e.g. kinase inhibitor design, antibody linker, fragment generation) against the style of generated molecules.
3.  Highlight unusual protecting groups, unrealistic repetition, or domain-mismatched outputs for manual review.

### 4.4 AI lane constraints
1.  AI review is **opt-in** and must be separated from the deterministic lane.
2.  AI should receive extracted evidence packets first, not unrestricted repository dumps.
3.  AI findings must cite deterministic finding IDs.
4.  AI may **escalate** review priority but may not erase deterministic FAIL/WARN findings.
5.  If AI is unavailable, the deterministic lane remains complete and operational.

---

## 5. Why Deterministic-First?
1.  **Verifiability:** A score of "FAIL" must point to a specific line of code or exact SMILES string that a human can verify.
2.  **Security:** Auditing clinical or bio-adjacent code should not require sending raw code to a 3rd-party model by default.
3.  **Speed:** Deterministic scans run in milliseconds; AI escalation is slower and should be reserved for ambiguous cases.
4.  **Governance:** The deterministic lane creates the evidence substrate that later advisory or AI systems must cite.

---

## 6. Scoring and Release Boundary
These detectors should not all enter scoring at the same time.

1.  **SMILES-DECEPT**
    * Initial mode: evidence-only
    * Candidate later mapping: `C3` or a new bio-integrity detail lane after benchmark review

2.  **RUN-TRACE**
    * Initial mode: evidence-only
    * Reason: heuristic taint detection is useful for triage but too noisy to score before calibration

3.  **SILENT-MOCK**
    * Initial mode: evidence + recommended severity
    * Strongest candidate for eventual `C3/C6` score impact after benchmark confirmation

Any future score impact must be justified by commit-pinned benchmark evidence and explicit false-positive review.

---

## 7. Proposed Output Shape for SMILES Review
```json
{
  "detector": "BIO_smiles_decept",
  "finding_id": "BIO_smiles_decept:src/generator.py:88:001",
  "status": "detected",
  "severity": "warn",
  "smiles_text": "CCCCCCCCCC",
  "issues": [
    "low_entropy_placeholder_pattern",
    "duplicate_batch_pattern"
  ],
  "local_parser_guard": "not_detected",
  "ai_review": {
    "enabled": false,
    "status": "not_requested",
    "semantic_concern": null,
    "confidence_bucket": null
  }
}
```

This shape preserves the rule that deterministic evidence is primary while still allowing optional AI annotations later.

---

## 8. Next Steps
1.  **Build commit-pinned fixture sets:**  
    - positive controls: known silent-mock, unsafe subprocess, malformed/placeholder SMILES repos  
    - negative controls: mature bioinformatics repos with legitimate subprocess usage and explicit parser guards  
    - ambiguous controls: demo/tutorial repos where mock data is clearly scoped and disclosed
2.  **Develop:** Continue extending `stem_ai/detector_bio.py` and its fixture set while preserving deterministic evidence contracts.
3.  **Verify (Local Lane):** Measure precision, recall, false-positive classes, and false-negative classes on commit-pinned fixtures for syntax, parser-guard, silent-mock, and subprocess findings.
4.  **Verify (AI Lane):** Add an optional provider-neutral advisory packet for suspicious SMILES batches and compare AI annotations against deterministic flags.
5.  **Calibrate:** Only after benchmark evidence and reproducible detector output should any SMILES-derived or subprocess-derived signal affect final scoring.
