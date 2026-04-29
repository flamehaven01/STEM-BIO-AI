# STEM BIO-AI Governance Overlay Discrimination Examples: G1-G5

These examples use generic governance terms. Platform-specific mappings are shown in parentheses as illustrations only.

---

## [G1] Bounded Governance Insertion (0/5)

**5 pts:**
- "Governance insertion scope: empirical bounds gate applied to protein structure prediction output only. Other pipeline stages unchanged."
  (Flamehaven example: CCGE Stage-Gate G2 insertion)
- "ISO 13485 QMS review applied to data ingestion module only. Core analysis engine untouched."
  -- scope explicit, boundary legible, not indiscriminate

**0 pts:**
- "We added governance to the entire pipeline." -- unbounded
- "Compliance archive present." -- existence without scope

---

## [G2] Native Capability Preservation (0/5)

**5 pts:**
- "Original scRNA-seq analysis preserved. Governance overlay adds output validation gate. All other paths functionally identical."
- "Planner-Executor-Evaluator architecture retained. Governance gates inserted at ingress and egress only."

**0 pts:**
- "Repository forked and rewritten with governance layer." -- original replaced
- "Governance wrapper replaces original pipeline with deterministic fallback." -- not preserved

---

## [G3] Fail-Closed Runtime Evidence (0/5)

**5 pts:**
- "Gate test log: BLOCK on synthetic divergent input. CI file: tests/test_governance.py, 7 passed."
  (Flamehaven example: _validate_inputs returns False on invalid path)
- "IEC 62304 verification report: halt on threshold violation, evidence attached."

**0 pts:**
- "We plan to add fail-closed gates in Q3." -- intent
- "README states all outputs are gated." -- claim without runtime evidence

---

## [G4] Documentation Alignment (0/5)

**5 pts:**
- "README states outputs gated. Compliance archive records gate parameters. Maintainer procedure matches."
  Three-way consistency verified.

**0 pts:**
- "README says 'all outputs validated' but no compliance archive or procedure exists."

---

## [G5] Approval / Rollback / Human-in-Command Discipline (0/5)

**5 pts:**
- "Approval record signed by maintainer. Rollback: 'revert commit abc123 restores pre-governance state.' Human review required for threshold changes."
  (Flamehaven example: CCGE approval packet + rollback note)

**0 pts:**
- "Governance applied by automated script with no review." -- no human approval
