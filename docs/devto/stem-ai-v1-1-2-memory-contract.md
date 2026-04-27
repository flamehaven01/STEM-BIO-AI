---
title: STEM-AI v1.1.2: How We Bound an AI Auditor to a Machine-Checkable Memory Contract
published: false
description: After auditing 10 open-source bio-AI repositories, STEM-AI v1.1.2 adds MICA, a memory contract layer for more reproducible AI governance audits.
tags: bioinformatics, medicalai, aigovernance, healthtech
series: STEM-AI: Sovereign Trust Evaluator for Medical AI Artifacts
---

> Reading path:
>
> This post follows the earlier write-up:
> [How Auditing 10 Bio-AI Repositories Shaped STEM-AI](https://dev.to/flamehaven01/how-auditing-10-bio-ai-repositories-shaped-stem-ai-41b5)
>
> The previous post asked what code-path analysis can reveal that text-only review misses.
> This post asks the next question: how do we trust the AI that is doing the audit?

---

## The problem after the audit

In March 2026, we ran STEM-AI across 10 open-source bio/medical AI repositories.

The audits surfaced the problems we expected: missing clinical disclaimers, weak reproducibility signals, absent governance artifacts, and code paths that did not match the public-facing claims around them.

The code-path layer mattered because some failures were invisible from README text alone:

- a clinical-looking method whose body was a stub
- a rate limiter that appeared to enforce a boundary but defaulted to bypass
- clinical-adjacent imports that exposed risk before the README acknowledged it
- repository surfaces that looked scientifically mature but lacked test, provenance, or bias documentation

That work shaped the current STEM-AI scoring model.

But it also exposed a second problem.

If an LLM is helping audit medical AI repositories, the LLM itself becomes part of the governance surface.

And LLMs drift.

One session may enforce a clinical boundary strictly. Another session may invent a generous intermediate score for the same boundary case. In a normal code review, that is annoying. In medical AI governance, that variance is a liability.

So STEM-AI v1.1.2 does not rely on prompting alone.

It adds a memory contract layer.

---

## What changed in v1.1.2

STEM-AI v1.1.2 introduces MICA: Memory-Injected Contract Architecture.

MICA is not a claim that the LLM has become deterministic. The audit still runs through an LLM or AI CLI runtime. The point is narrower and more useful:

before the auditor reads the target repository, it must load and verify a contract that constrains how the audit is allowed to proceed.

The v1.1.2 package includes:

- `memory/mica.yaml`: composition contract
- `memory/stem-ai.mica.v1.1.2.json`: machine-checkable archive
- `memory/stem-ai-playbook.v1.1.2.md`: session playbook and rubric drift guard
- `memory/stem-ai-lessons.v1.1.2.md`: historical failure mode lessons
- `spec/STEM-AI_v1.1.2_CORE.md`: canonical scoring and execution spec

The MICA layer requires the auditor to load 18 immutable invariants before scoring begins.

Examples:

- the evaluation order is fixed
- the base weight formula is fixed
- tier boundaries are fixed
- `T0_HARD_FLOOR` cannot be bypassed
- governance overlay cannot raise the formal base tier
- the mandatory disclaimer block cannot be omitted
- Stage 3G remains advisory

This turns the audit session into a constrained execution of a contract, not a free-form interpretation of a prompt.

---

## Why this matters for bio and medical AI

Bio/medical AI repositories often sit near a dangerous ambiguity.

They may be research tools, but the vocabulary around them is clinical. They may not claim deployment, but they process clinical data. They may not produce medical advice, but they expose pharmacogenomics, imaging, diagnosis, survival analysis, or triage-adjacent code paths.

That means an audit needs to distinguish:

- documented intent from executable behavior
- research-use proximity from patient-facing proximity
- governance language from governance artifacts
- model capability from trust establishment

STEM-AI does not certify clinical safety. It does not replace regulatory review. It does not determine whether the underlying science is valid.

It answers a narrower question:

> Does the observable repository surface establish enough trust for institutional review, supervised pilot consideration, or rejection?

For that question to be useful, the scoring logic itself must be stable enough to inspect.

That is what v1.1.2 tries to improve.

---

## Public evidence without exposing target IP

A reasonable objection from bio teams is:

> Can you show evidence without exposing audited repositories, patient data, private code, or proprietary implementation details?

For v1.1.2, I added a public evidence artifact that is intentionally aggregate-only and IP-neutral:

```json
{
  "artifact_id": "STEM-AI-BIO-PUBLIC-EVIDENCE-v1.1.2",
  "ip_safety_statement": {
    "contains_patient_data": false,
    "contains_private_repository_data": false,
    "contains_proprietary_target_code": false,
    "contains_target_repository_names": false,
    "contains_model_weights_or_datasets": false
  },
  "public_audit_batch": {
    "repository_count": 10,
    "repository_identity_policy": "redacted_aggregate_only",
    "tier_distribution": {
      "T0": 8,
      "T1": 1,
      "T2": 1,
      "T3": 0,
      "T4": 0
    }
  },
  "contract_invariants": {
    "active_invariant_count": 18,
    "base_weights": {
      "stage_1": 0.4,
      "stage_2": 0.2,
      "stage_3": 0.4
    },
    "stage_2_na_weights": {
      "stage_1": 0.5,
      "stage_3": 0.5
    }
  }
}
```

The full file is in:

```text
examples/public_evidence/stem_ai_v1_1_2_public_evidence.json
```

It does not name the audited repositories. It does not include patient records. It does not include target code. It only records the public batch aggregate, release metadata, contract invariants, and synthetic scoring cases.

That is deliberate.

The point is to let a reviewer verify the contract math without requiring access to sensitive or proprietary material.

---

## A small validator anyone can run

The evidence artifact is paired with a Python validator:

```python
#!/usr/bin/env python3
"""
Validate the public STEM-AI v1.1.2 evidence artifact.

This script is intentionally small, dependency-free, and IP-neutral. It checks
aggregate evidence and contract math without requiring audited repository names,
private code, patient records, model weights, or proprietary datasets.
"""
```

The validator uses only the Python standard library.

It checks that:

- aggregate tier counts sum to the repository count
- base weights sum to `1.0`
- Stage 2 `N/A` redistribution sums to `1.0`
- tier boundaries match the canonical `T0` through `T4` ranges
- the active invariant count is 18
- Stage 3G cannot raise the formal tier
- synthetic score cases reproduce expected final scores and tiers
- forbidden keys such as patient identifiers, private keys, tokens, and target code do not appear

Example scoring check:

```python
def compute_final_score(case):
    if case["t0_hard_floor"]:
        return 0

    stage_1 = float(case["stage_1"])
    stage_3 = float(case["stage_3"])
    risk_penalty = float(case["risk_penalty"])

    if case["stage_2_available"]:
        stage_2 = float(case["stage_2"])
        weighted = (stage_1 * 0.40) + (stage_2 * 0.20) + (stage_3 * 0.40)
    else:
        weighted = (stage_1 * 0.50) + (stage_3 * 0.50)

    return int(max(0, min(100, round(weighted - risk_penalty))))
```

Run it with:

```bash
python examples/public_evidence/validate_public_evidence.py
```

Expected output:

```text
STEM-AI public evidence validation: PASS
- forbidden-key scan passed
- IP safety flags passed
- public audit batch aggregate count passed
- invariant count and stage order passed
- weight checks passed
- tier boundary checks passed
- governance overlay separation passed
- PCT critical halt check count passed
- synthetic score cases passed
```

The validator does not prove that every future LLM run will produce the same audit. That is not the claim.

It proves that the public evidence artifact is internally consistent and that the contract math can be checked outside the LLM.

---

## What MICA prevents

MICA is designed to block a narrow class of governance failures:

- changing tier boundaries during a session
- treating missing Stage 2 evidence as zero instead of redistributing weight
- letting governance overlay inflate the formal base tier
- skipping mandatory disclaimers
- scoring C1-C4 when not in local analysis mode
- omitting evidence chains for scored findings
- bypassing `T0_HARD_FLOOR`

These failures matter because they are exactly where LLM auditors tend to drift.

They do not drift only by hallucinating facts.

They drift by becoming lenient at the boundary.

They invent partial credit. They smooth over hard floors. They treat missing data as a weak negative instead of `N/A`. They let governance language count as governance evidence.

In a medical AI setting, those are not style differences. They change the audit outcome.

---

## What MICA does not claim

The v1.1.2 memory contract is not:

- regulatory clearance
- clinical validation
- proof of model safety
- proof that a repository is scientifically valid
- a replacement for expert review
- a guarantee of exact cross-LLM reproducibility

The current target remains bounded:

same input, any supported LLM or AI CLI, base score within a defined consistency target.

The repository also keeps the disclaimer explicit: STEM-AI is an LLM-executed rubric. It supports review; it does not certify deployment.

That limitation is not a footnote. It is part of the contract.

---

## Why I think this is the right layer

The first version of STEM-AI asked:

> Can the repository be trusted in front of a patient's life?

The code-path work added another question:

> Does the code actually do what the documentation says?

v1.1.2 adds a third:

> Can the auditor itself be constrained, inspected, and corrected?

That is the layer I think AI governance pipelines need next.

Not just better prompts.

Not just longer checklists.

A contract that loads before the audit begins, records its own failure modes, and refuses to silently bend the rules that make the audit meaningful.

Governance without evidence is theater.

But an AI auditor without a memory contract is just a stochastic reviewer.

---

Repository:

```text
https://github.com/flamehaven01/STEM-AI-BIO
```

Stable tag:

```text
v1.1.2
```

Public evidence files:

```text
examples/public_evidence/stem_ai_v1_1_2_public_evidence.json
examples/public_evidence/validate_public_evidence.py
```

STEM-AI v1.1.2: trust evaluation framework for medical AI repositories.

"Code works. But does the author care about the patient?"
