---
title: STEM-AI v1.1.2: An AI Auditor With a Memory Contract
published: false
description: STEM-AI v1.1.2 binds a bio/medical AI repository audit to a machine-checkable memory contract, then demonstrates it on a real open-source bioinformatics repository.
tags: bioinformatics, medicalai, aigovernance, python
series: STEM-AI: Sovereign Trust Evaluator for Medical AI Artifacts
---

> Previous article:
>
> [How Auditing 10 Bio-AI Repositories Shaped STEM-AI](https://dev.to/flamehaven01/how-auditing-10-bio-ai-repositories-shaped-stem-ai-41b5)

In the first STEM-AI write-up, I described what happened after auditing 10 open-source bio/medical AI repositories.

The important lesson was not just that some repositories lacked clinical disclaimers, tests, or governance artifacts.

The more useful lesson was this:

> Text-only review is too weak for bio/medical AI. You have to inspect the code path.

That worked.

But it exposed the next problem.

If an AI system is auditing another AI or bioinformatics repository, how do you trust the auditor?

LLMs drift. One session can enforce a clinical boundary strictly. Another can invent a generous middle score for the same boundary case. In normal software review, that is annoying. In medical AI governance, it is a liability.

STEM-AI v1.1.2 is my answer to that problem.

It does not try to make the LLM deterministic by writing a longer prompt.

It binds the audit to a memory contract.

---

## What v1.1.2 adds

STEM-AI v1.1.2 introduces MICA: Memory-Injected Contract Architecture.

The idea is simple:

before the auditor reads the target repository, it must load a fixed audit contract and self-check the rules it is not allowed to bend.

The v1.1.2 layer includes:

- `memory/mica.yaml` -- composition contract
- `memory/stem-ai.mica.v1.1.2.json` -- machine-checkable memory archive
- `memory/stem-ai-playbook.v1.1.2.md` -- session playbook and drift guard
- `memory/stem-ai-lessons.v1.1.2.md` -- historical failure-mode archive
- `spec/STEM-AI_v1.1.2_CORE.md` -- canonical audit spec

The contract pins 18 invariants.

Examples:

- Stage order is fixed: README intent, cross-platform evidence, code/bio evidence.
- Stage weights are fixed.
- Tier boundaries are fixed.
- `T0_HARD_FLOOR` cannot be bypassed.
- Stage 2 `N/A` has deterministic redistribution.
- Governance overlay cannot raise the formal base tier.
- C1-C4 code-integrity checks only run in LOCAL_ANALYSIS mode.
- Mandatory clinical-use disclaimers cannot be omitted.

This is not a claim that the LLM becomes perfectly deterministic.

It is a narrower claim:

> The auditor is forced to operate inside a contract whose scoring rules, hard floors, and evidence requirements are inspectable.

That is the useful layer.

---

## What "loading the contract" means

MICA is not hidden model memory.

It is also not a claim that the model provider changed the LLM.

In v1.1.2, "loading the contract" means the audit session starts by reading a fixed set of repository files before it is allowed to score the target:

```text
memory/mica.yaml
memory/stem-ai.mica.v1.1.2.json
memory/stem-ai-playbook.v1.1.2.md
memory/stem-ai-lessons.v1.1.2.md
spec/STEM-AI_v1.1.2_CORE.md
```

The auditor then performs a pre-execution contract test:

- confirm the canonical spec exists
- confirm the memory archive exists
- confirm the invariant count is 18
- confirm the fixed tier boundaries are present
- confirm the Stage 2 `N/A` redistribution rule is present
- confirm Stage 3G cannot raise the formal tier
- confirm C1-C4 mode gating is active

Only after that does the audit proceed.

This does not make the LLM mathematically deterministic.

It makes the audit procedure file-backed, inspectable, and interruptible. If the session cannot load or reconcile the contract files, the correct behavior is to stop before scoring.

That is the difference between "please be consistent" and "execute this versioned contract."

---

## The audit workflow

STEM-AI v1.1.2 runs as a structured audit workflow:

```text
Target repository
    |
    v
MICA pre-check
    |
    v
Stage 1: README intent and claim surface
    |
    v
Stage 2: cross-platform consistency
    |
    v
Stage 3: code, tests, provenance, governance
    |
    v
C1-C4 LOCAL_ANALYSIS code-integrity scan
    |
    v
Report + machine-readable audit JSON
```

In LOCAL_ANALYSIS mode, the auditor is not limited to what the README says.

It can inspect:

- package metadata
- workflow files
- test definitions
- dependency manifests
- source-code paths
- deprecated or dead-code paths
- exception handling
- credential patterns
- provenance and hash-checking logic

The output is intentionally split into two files:

```text
report.md                  # human-readable audit judgment
experiment_results.json    # machine-readable evidence and score object
```

That split matters.

The report explains the reasoning.

The JSON lets another reviewer inspect the score, evidence fields, flags, and integrity checks without trusting the prose.

---

## A real target audit, not a synthetic example

For this v1.1.2 demonstration, I used a real public repository:

```text
artic-network/fieldbioinformatics
```

The target is not the protagonist of this post.

It is only the specimen used to show the audit workflow against a real bioinformatics codebase.

The local audit produced:

```text
audits/fieldbioinformatics_v1_1_2/report.md
audits/fieldbioinformatics_v1_1_2/experiment_results.json
```

The target snapshot:

```json
{
  "name": "artic-network/fieldbioinformatics",
  "remote": "https://github.com/artic-network/fieldbioinformatics",
  "branch": "master",
  "commit": "8008b4c97c2193a82308ff6f0be507b1d9306e36",
  "file_count": 114
}
```

This is the important part: the audit did not ask, "Does this README sound trustworthy?"

It asked:

- Do README claims match actual package metadata and entry points?
- Are there real CI and domain-specific tests?
- Are dependencies reproducible enough?
- Are there credential leaks?
- Are there deprecated patient-adjacent paths?
- Do clinical-adjacent output paths fail closed?
- Does the repository include governance evidence, or only governance absence?

That is where STEM-AI is useful.

---

## The score object

The machine-readable result records the score like this:

```json
{
  "stage_1_readme_intent": 65,
  "stage_2_cross_platform": null,
  "stage_2_status": "NOT_COLLECTED_LOCAL_ANALYSIS_ONLY",
  "stage_2_policy": "N/A is not scored as zero; fixed v1.1.2 redistribution applies.",
  "stage_3_code_bio": 55,
  "stage_2_na_redistribution": {
    "stage_1_weight": 0.5,
    "stage_3_weight": 0.5
  },
  "risk_penalty": 0,
  "final_score": 60,
  "formal_tier": "T2 Caution"
}
```

Stage 2 is explicitly represented as `null` for this local-only audit.

That does not mean cross-platform consistency is unimportant.

It means this evidence slice was deliberately scoped to LOCAL_ANALYSIS: repository files, code paths, documentation, dependency manifests, CI definitions, and code-integrity checks. In v1.1.2, when Stage 2 is not collected, it is not treated as zero. The contract redistributes the weight to Stage 1 and Stage 3.

That is not left to the LLM's mood.

The contract defines the redistribution:

```text
Final = (Stage 1 x 0.50) + (Stage 3 x 0.50) - Risk Penalty
      = (65 x 0.50) + (55 x 0.50) - 0
      = 60
```

The final tier is therefore:

```text
T2 Caution
```

Not because the prose sounded balanced.

Because the contract math forces that result.

---

## Why the T0 hard floor did not trigger

`T0_HARD_FLOOR` is the rule that prevents a clinically dangerous repository from escaping rejection through good wording.

In simplified form:

```text
If a repository is CA-DIRECT
and it has no substantive code implementation,
then final tier = T0 regardless of score math.
```

Examples of CA-DIRECT include patient-specific diagnosis, treatment recommendation, triage, risk scoring, or clinical decision support.

The audited repository did not trigger that floor because STEM-AI classified it as:

```json
{
  "clinical_adjacent": true,
  "ca_severity": "CA-INDIRECT",
  "t0_hard_floor": false
}
```

It produces biological sequence artifacts that may sit near public-health or clinical workflows, but the inspected surface did not make direct autonomous diagnosis or treatment claims. It also has substantive implementation, CI, and domain-specific test definitions.

So the result is not T0.

But it is also not high-trust.

The bounded result is T2 Caution.

---

## What the graph looks like

The result can be visualized as a compact scorecard:

```text
Stage 1 README Intent      65/100  █████████████░░░░░░░
Stage 3 Code/Bio Evidence  55/100  ███████████░░░░░░░░░
Risk Penalty                0/100  ░░░░░░░░░░░░░░░░░░░░
Final Score                60/100  ████████████░░░░░░░░

Formal Tier: T2 Caution
Use Scope: supervised non-clinical technical review only
```

The graph is not the evidence.

The JSON is the evidence object.

The graph is just the digest.

---

## Code-integrity findings

The same JSON records C1-C4 LOCAL_ANALYSIS checks:

```json
{
  "C1_hardcoded_credentials": {
    "status": "PASS"
  },
  "C2_dependency_pinning": {
    "status": "WARN"
  },
  "C3_dead_or_deprecated_patient_adjacent_paths": {
    "status": "WARN"
  },
  "C4_exception_handling_clinical_adjacent_paths": {
    "status": "WARN"
  }
}
```

That is the difference between a general review and a code-path audit.

A text review can say:

> The project appears technically mature.

A code-path audit can say:

> Credential patterns were checked. Dependency pinning is weak. Deprecated patient-adjacent metadata exists. One clinical-adjacent filtering path does not fail closed on missing depth.

That is a more useful governance object.

It is not a certificate.

It is a map of what a reviewer should trust, distrust, or inspect next.

---

## A small Python verifier

Here is a small dependency-free Python script that reads the actual audit JSON and verifies the score calculation. It does not need target private code or patient data; it only checks the machine-readable audit result.

```python
#!/usr/bin/env python3
import json
from pathlib import Path


RESULT = Path("audits/fieldbioinformatics_v1_1_2/experiment_results.json")


def tier(score: int) -> str:
    if score <= 39:
        return "T0"
    if score <= 54:
        return "T1"
    if score <= 69:
        return "T2"
    if score <= 84:
        return "T3"
    return "T4"


def bar(score: int, width: int = 20) -> str:
    filled = round((score / 100) * width)
    return "█" * filled + "░" * (width - filled)


data = json.loads(RESULT.read_text(encoding="utf-8"))
score = data["score"]

stage_1 = score["stage_1_readme_intent"]
stage_2 = score["stage_2_cross_platform"]
stage_3 = score["stage_3_code_bio"]
risk_penalty = score["risk_penalty"]

if stage_2 is None:
    weights = score["stage_2_na_redistribution"]
    computed = round(
        (stage_1 * weights["stage_1_weight"])
        + (stage_3 * weights["stage_3_weight"])
        - risk_penalty
    )
else:
    computed = round((stage_1 * 0.40) + (stage_2 * 0.20) + (stage_3 * 0.40) - risk_penalty)

assert computed == score["final_score"]
assert tier(computed) in score["formal_tier"]

print(f"Stage 1  {stage_1:3}/100  {bar(stage_1)}")
print(f"Stage 3  {stage_3:3}/100  {bar(stage_3)}")
print(f"Final    {computed:3}/100  {bar(computed)}")
print(f"Tier     {score['formal_tier']}")

for key, item in data["code_integrity"].items():
    print(f"{key}: {item['status']}")
```

Expected digest:

```text
Stage 1   65/100  █████████████░░░░░░░
Stage 3   55/100  ███████████░░░░░░░░░
Final     60/100  ████████████░░░░░░░░
Tier      T2 Caution
C1_hardcoded_credentials: PASS
C2_dependency_pinning: WARN
C3_dead_or_deprecated_patient_adjacent_paths: WARN
C4_exception_handling_clinical_adjacent_paths: WARN
```

## Why this matters

Bio/medical AI governance is full of language that sounds safe but is hard to verify:

- "research use only"
- "not medical advice"
- "validated pipeline"
- "clinical-grade"
- "responsible AI"
- "human-in-the-loop"

Those phrases are not enough.

STEM-AI asks for observable structure:

- source-code reality
- test reality
- CI reality
- dependency reality
- clinical boundary reality
- governance artifact reality
- code-integrity reality

v1.1.2 adds another layer:

auditor reality.

The AI auditor itself has to load a memory contract before it scores.

That is what MICA is for.

The final answer remains bounded:

```text
T2 Caution
Research reference and supervised non-clinical technical review only.
No autonomous clinical decision support.
```

That is the kind of result I want from an AI auditor.

Not hype.

Not rejection by default.

A bounded trust judgment with evidence paths.

---

## What comes next

The follow-on lane should:

- provision the target dependency environment
- run selected target tests in a controlled shell
- capture command, exit code, environment hash, and output digest
- attach a replay manifest to `experiment_results.json`
- keep runtime evidence separate from source/document/CI evidence

For the current demonstration, runtime execution status is recorded as an evidence boundary in the audit JSON. The score itself remains based on the official v1.1.2 LOCAL_ANALYSIS evidence basis.

---

Repository:

```text
https://github.com/flamehaven01/STEM-AI-BIO
```

Stable tag:

```text
v1.1.2
```

Primary v1.1.2 evidence shape:

```text
report.md
experiment_results.json
```

STEM-AI v1.1.2 is not a clinical certifier.

It is a contract-bound AI audit framework for asking a narrower, more useful question:

> Does this bio/medical AI repository establish enough observable trust to be considered, contained, or rejected?
