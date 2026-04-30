# STEM BIO-AI v1.4.0 Plan V1

**Target Version:** 1.4.0  
**Status:** Draft plan  
**Date:** 2026-04-30  
**Core Theme:** Evidence-bound AI advisory substrate without immediate hard dependency on any single AI API.

---

## 1. Strategic Position

v1.3.x built the deterministic floor:

- v1.3.0: evidence ledger, AST summary, Stage 4 replication lane, `--explain`
- v1.3.1: local-10 CA/C1 precision patch
- v1.3.2: reasoning diagnostics without score drift

v1.4.0 should not jump directly to a Gemini/OpenAI/Claude-only API feature. The goal is to create a provider-neutral AI advisory substrate that can later run through cloud APIs, OpenAI-compatible APIs, or local models.

One-line target:

> v1.4.0 makes AI advisory possible, evidence-bound, provider-neutral, and auditable; it does not make AI the scoring authority.

---

## 2. Non-Negotiable AI Boundary

AI advisory in v1.4 must obey these constraints:

- AI reads structured STEM outputs, not raw repository text by default.
- AI input is limited to `evidence_ledger`, `reasoning_model`, `stage_4_rubric`, `ast_signal_summary`, `detector_summary`, score metadata, and selected report text.
- AI must cite `finding_id` values for every material advisory claim.
- AI cannot modify `final_score`, `formal_tier`, `replication_score`, or `replication_tier`.
- AI output is advisory only: reviewer notes, inspection priorities, contradiction hypotheses, missing-evidence questions.
- AI must not claim clinical truth, safety, efficacy, regulatory readiness, or deployment approval.
- If citations are missing or invalid, the advisory result is invalid.

This preserves v1.3's deterministic scanner as the source of record.

---

## 3. Provider-Neutral Architecture

v1.4 should define an adapter contract before implementing provider-specific clients.

Inspired by `D:\Sanctum\Flamehaven-Filesearch`, the provider space should remain broad:

| Provider Class | Examples | v1.4 Role |
|---|---|---|
| Cloud native | Gemini, ChatGPT/OpenAI, Claude | Future optional adapters |
| OpenAI-compatible | Kimi, vLLM, LM Studio, custom gateways | Future optional adapters |
| Local server | Ollama, llama.cpp server, text-generation-webui | Future optional adapters |
| Local model runtime | Qwen, Kimi local variants, Unsloth/Transformers | Future experimental adapters |
| Offline stub | deterministic no-AI validator | Required in v1.4.0 for tests |

Environment shape should be provider-neutral:

```text
STEM_AI_ADVISORY_PROVIDER=none|openai|anthropic|gemini|openai_compatible|ollama|local_runtime
STEM_AI_ADVISORY_MODEL=...
STEM_AI_ADVISORY_BASE_URL=...
STEM_AI_ADVISORY_API_KEY=...
STEM_AI_ADVISORY_TIMEOUT_SEC=...
STEM_AI_ADVISORY_MAX_TOKENS=...
```

No provider SDK should be required for the core package in v1.4.0. Provider adapters should be optional extras or later v1.4.x modules.

---

## 4. Proposed Data Contract

Add an optional top-level field:

```json
{
  "ai_advisory": {
    "schema_version": "stem-ai-advisory-v1.4",
    "provider": "none",
    "model": null,
    "mode": "offline_contract_validation",
    "status": "not_run|valid|invalid|error",
    "input_contract": {},
    "reviewer_notes": [],
    "inspection_priorities": [],
    "citation_index": {},
    "invalid_citations": [],
    "policy": {
      "final_score_override": false,
      "requires_finding_id_citations": true,
      "raw_repo_text_allowed": false,
      "clinical_claims_allowed": false
    }
  }
}
```

`ai_advisory` should be omitted unless advisory is requested or contract validation is explicitly enabled.

---

## 5. Advisory Input Packet

v1.4 should introduce a deterministic packet builder:

```text
stem_ai/advisory_contract.py
```

Required functions:

```python
def build_advisory_input(result: dict) -> dict: ...
def validate_advisory_output(result: dict, advisory: dict) -> dict: ...
def cited_finding_ids(advisory: dict) -> set[str]: ...
def known_finding_ids(result: dict) -> set[str]: ...
```

The advisory input packet should include:

- target metadata
- score and tier
- classification boundaries
- code integrity statuses
- detector summary
- reasoning diagnostics
- Stage 4 rubric
- AST summary
- capped evidence ledger entries

Evidence ledger cap should be deterministic:

```text
MAX_ADVISORY_FINDINGS = 200
Sort: severity/status priority, then detector, then file, then line, then finding_id
```

This allows local models with smaller context windows to participate.

---

## 6. ASDP Compilation Experiment

User hypothesis:

> Compiling `spec/STEM-AI_v1.1.2_CORE.md` through ASDP may make the AI-facing structure clearer.

This is suitable for v1.4 as an experimental planning track, not a blocking runtime dependency.

Reference sources inspected:

- `D:\Sanctum\STEM-BIO-AI\spec\STEM-AI_v1.1.2_CORE.md`
- `D:\Sanctum\flamehaven-ag-core\FAC_DESIGN_v2.md`
- `D:\Sanctum\flamehaven-ag-core\fac\governance\evidence_contract.py`

Relevant ASDP/FAC ideas:

- ResultContract as first-class output
- EvidenceContract with declared why, risk score, planned scope, actual scope, required artifacts, expiry
- 5-plane separation: reasoning, governance, approval, memory, execution
- FAC as execution plane, not a model provider

v1.4 experiment:

```text
docs/asdp/STEM_AI_v1_1_2_ASDP_COMPILE_NOTES.md
spec/asdp/stem_ai_advisory_contract.schema.json
spec/asdp/stem_ai_result_contract.schema.json
```

Experiment goal:

- Convert the legacy v1.1.2 semantic skill spec into machine-facing advisory contracts.
- Extract invariant rules that v1.4 AI advisory must obey.
- Produce a JSON schema for advisory output validation.

Non-goal:

- Do not import ASDP or FAC as runtime dependencies in v1.4.0.
- Do not replace v1.3 deterministic scoring with ASDP scoring.
- Do not treat ASDP compilation as proof of clinical validity.

---

## 7. Local Model Path

Reference source inspected:

- `D:\Sanctum\Extra Repo\unsloth`

Unsloth is relevant as a future local model/runtime path, especially for Qwen-family or other local models. v1.4.0 should only reserve the adapter surface:

```text
provider = local_runtime
runtime = unsloth|transformers|llama_cpp|ollama
model = qwen/kimi/local path
```

v1.4.0 should not require installing Unsloth. The dependency and hardware surface is too large for the core scanner.

Recommended v1.4.0 stance:

- support local advisory through an adapter interface and offline stub
- document Unsloth/Qwen/Kimi as future v1.4.x/v1.5 experimental adapters
- keep core scanner zero-runtime-model by default

---

## 8. 30-Repo Benchmark Gate

Before any AI output is presented as useful, run the 30-repo benchmark.

Required artifacts:

```text
audits/benchmark-v1.4/benchmark_manifest.json
audits/benchmark-v1.4/benchmark_results.jsonl
audits/benchmark-v1.4/manual_verdicts.jsonl
audits/benchmark-v1.4/fp_fn_log.md
audits/benchmark-v1.4/reasoning_diagnostics_summary.md
```

Selection criteria:

- public GitHub repos
- Python primary or substantial Python component
- bioinformatics, medical AI, clinical NLP, genomics, biomedical agents, scientific-agent skills
- commit hash pinned
- not selected after viewing STEM score
- include T0-T4 expected spread

Benchmark questions:

- Does `reasoning_model` identify manual-review priorities without score drift?
- Do Stage 4 replication signals distinguish reproducible packages from README-only projects?
- Do CA caps and C1-C4 warnings align with manual concerns?
- Which detectors produce repeated false positives or false negatives?
- Which evidence surfaces are thin but scored strongly?

AI advisory should remain disabled or offline-stub-only until this benchmark is recorded.

---

## 9. v1.4.0 Implementation Scope

### Required

1. `docs/V1_4_PLAN_V1.md`
2. `stem_ai/advisory_contract.py`
3. JSON schema for advisory output
4. offline advisory contract validator
5. CLI flag:

```text
stem audit <repo> --advisory none|validate
```

6. Tests:

- advisory input contains no raw repo text by default
- valid advisory cites known `finding_id`
- invalid citation is rejected
- advisory cannot override final score
- clinical/safety/regulatory claim terms are rejected or flagged
- provider config is parsed but provider calls are not required

### Deferred To v1.4.x

- Gemini adapter
- OpenAI/ChatGPT adapter
- Claude adapter
- OpenAI-compatible adapter for Kimi/vLLM/LM Studio
- Ollama adapter
- Unsloth/local runtime adapter
- AI-generated reviewer note rendering in PDF

---

## 10. Provider Adapter Contract

Future adapter interface:

```python
class AdvisoryProvider:
    provider_name: str

    def available(self) -> bool: ...
    def generate(self, advisory_input: dict, config: dict) -> dict: ...
```

Provider output must normalize to:

```json
{
  "reviewer_notes": [
    {
      "claim": "...",
      "severity": "info|warn|block",
      "cites": ["C2_dependency_pinning:requirements.txt:3:001"],
      "recommended_action": "..."
    }
  ],
  "inspection_priorities": [
    {
      "priority": "high|medium|low",
      "reason": "...",
      "cites": ["..."]
    }
  ]
}
```

Validation happens after provider output and before report rendering.

---

## 11. Release Gates

v1.4.0 is releasable only if:

- existing v1.3.2 tests pass
- advisory contract tests pass
- package build passes
- `validate_release.ps1` passes
- slop detector remains clean
- no provider API key is required for tests
- no final score drift occurs on local-10
- `ai_advisory.policy.final_score_override` is always false
- invalid advisory citations are detected
- advisory schema rejects raw uncited clinical deployment claims

---

## 12. Strategic Conclusion

v1.4.0 should be an AI-ready contract release, not an AI-provider release.

The correct progression:

```text
v1.3.2  deterministic evidence + reasoning diagnostics
v1.4.0  advisory contract + ASDP compilation experiment + offline validation
v1.4.x  optional provider adapters
v1.5+   calibrated advisory workflows after 30-repo benchmark evidence
```

This keeps STEM BIO-AI honest: AI is allowed to explain and prioritize evidence, but not to become the evidence.
