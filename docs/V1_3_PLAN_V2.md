# STEM BIO-AI v1.3 Plan v2

**Status:** Draft v2
**Target Version:** 1.3.0
**Date:** 2026-04-30
**Supersedes:** `docs/V1_3_PLAN_V1.md`
**Positioning:** Deterministic benchmark-evidenced bio/medical repository audit framework

---

## 1. Strategic Judgment

v1.3의 목표는 v1.2에서 정직하게 선언한 측정 경계가 실제로 의미 있음을 증명하는 것이다.

```text
v1.2 = "우리가 측정하는 것을 솔직하게 말한다"          (label honesty)
v1.3 = "그 측정이 의미 있음을 증거로 보여준다"          (benchmark evidence)
v1.4 = "증명된 결정론적 바닥 위에 AI advisory를 올린다" (AI on solid floor)
```

v1.3은 AI 기능 추가가 아니라, 로컬 Python/stdlib 기반 결정론적 검수 엔진의 한계를 최대한 끌어올리고 그 한계를 공개적으로 기록하는 버전이다.

v1.3의 한 줄 목표:

> Deterministic local evidence scanning is made meaningful through evidence-ledger contracts, AST-backed observation, replication-evidence analysis, explainable findings, and a fixed 30-repository benchmark.

---

## 2. v2 Change Log From Plan v1

외부 분석에서 지적된 실행 리스크를 평가했고, 다음 변경을 v2에 반영한다.

| Issue | Severity | Decision |
|---|---|---|
| AST scoring policy conflict | High | Accepted. v1.3.0은 `ast_signal_summary` 별도 출력만 한다. Final score 미반영. |
| LOGOS dependency as implementation blocker | High | Accepted. LOGOS review는 Week 1 detector work를 막지 않는 parallel research track으로 격리한다. `reasoning_model.py` implementation은 v1.3.1로 이동한다. |
| Week 1 overload | High | Accepted. Week 1/2/3/4 작업을 재편성한다. |
| Benchmark selection criteria missing | Medium | Accepted. GitHub topic/stars/recency/language/commit pinning 기준 추가. |
| AST file limit and timeout policy missing | Medium | Accepted. file count/size/skip finding 정책 추가. |
| File split timing conflict | Low | Accepted. v1.3.0은 `evidence.py`, `detectors.py`를 추가하고 기존 `scanner.py`는 compatibility orchestrator로 유지한다. `reasoning_model.py`는 v1.3.1 target이다. |

보존할 v1 원칙:

- v1.4 조건: AI는 evidence ledger를 읽고 finding ID를 cite한다.
- evidence status 6종: `detected`, `not_detected`, `absent`, `not_applicable`, `manual_review_required`, `error`
- release gates
- `audits/benchmark-v1.3/` 구조

---

## 3. Scope Boundary

v1.3이 할 수 있는 것:

- 저장소 표면에서 관찰 가능한 evidence signal을 결정론적으로 탐지한다.
- 파일/라인/스니펫/패턴 ID 기반 evidence ledger를 남긴다.
- AST 기반으로 Python 코드 구조 신호를 분석한다.
- 재현성/복제 가능성 신호를 Stage 4로 분리한다.
- 30개 고정 benchmark repo에서 오탐/미탐과 tier alignment를 측정한다.
- `--explain`으로 왜 매칭되었는지 사람이 검증 가능한 출력을 제공한다.

v1.3이 하지 않는 것:

- 임상 안전성, 과학적 타당성, 모델 성능, 규제 적합성을 판정하지 않는다.
- 모델을 실행하거나 추론하지 않는다.
- AI/LLM으로 점수 또는 최종 verdict를 생성하지 않는다.
- private repo의 외부 네트워크 증거를 자동 수집하지 않는다.
- AST signal을 v1.3.0 final score에 반영하지 않는다.
- reasoning mathematical model은 v1.3.1로 진행한다.

---

## 4. Core Architecture

v1.3.0은 새 데이터 계약을 추가하되, 기존 scanner를 대규모로 뒤집지 않는다.

```text
Repository files
  -> Detector Registry
  -> Evidence Ledger
  -> Stage Evaluators
  -> Compatibility Scorer
  -> Renderers / --explain / JSON
```

v1.3.0 required files:

```text
stem_ai/evidence.py          # EvidenceFinding dataclass and finding_id policy
stem_ai/patterns.py          # shared regex/constants
stem_ai/detector_utils.py    # shared detector filesystem/parsing helpers
stem_ai/detector_surface.py  # README/package/file/dependency/regex detectors
stem_ai/detector_ast.py      # stdlib AST detectors and ast_signal_summary
stem_ai/detector_stage4.py   # Stage 4 replication-evidence detectors
stem_ai/detectors.py         # compatibility orchestrator / public collect API
stem_ai/scanner.py           # orchestration + backward-compatible score output
stem_ai/render.py            # report and explain rendering
stem_ai/cli.py               # --explain CLI flag
```

Policy:

- v1.3.0: create focused detector modules and keep `detectors.py` as the public compatibility orchestrator.
- v1.3.0: existing `scanner.py` functions remain the compatibility layer.
- v1.3.0: new detector output is wrapped into `evidence_ledger`.
- v1.3.1+: gradually migrate old scanner internals into detector modules after benchmark evidence.

---

## 5. Evidence Ledger Contract

All detectors should emit `EvidenceFinding` records when possible.

```json
{
  "finding_id": "B2_bias_limitations:README.md:42:001",
  "detector": "B2_bias_limitations",
  "detector_version": "1.3.0",
  "pattern_id": "bias_limitations_v2",
  "status": "detected",
  "severity": "info",
  "file": "README.md",
  "line": 42,
  "snippet": "Limitations and validation boundaries are documented.",
  "match_type": "regex",
  "explanation": "README exposes limitation or validation-boundary language."
}
```

Stable `finding_id` policy:

```python
finding_id = f"{detector}:{file_path.as_posix()}:{line}:{occurrence_index:03d}"
```

Rules:

- `file_path` is repo-root-relative and must use `Path.as_posix()` semantics even on Windows.
- `occurrence_index` resets per `(detector, file_path)` and increments in deterministic path-sorted, line-sorted match order.
- Multiple matches on the same line use `001`, `002`, etc. in discovery order.
- File-existence findings use `line = 0`.
- Repo-level findings use `file_path = "."` and `line = 0`.
- Finding IDs are part of the v1.4 AI citation contract; changing this policy requires a schema migration note.

Standard status values:

- `detected`: 결정론적 증거 발견
- `not_detected`: scanner가 찾지 못함
- `absent`: 관련 표면은 있으나 해당 증거 없음
- `not_applicable`: 해당 repo에 적용 불가 또는 safe skip
- `manual_review_required`: 로컬 결정론적 scan만으로 결론 불가
- `error`: 파일 파싱 또는 detector 실행 오류

v1.3 JSON additions:

```json
{
  "schema_version": "stem-ai-local-cli-result-v1.3",
  "evidence_ledger": [],
  "detector_summary": {},
  "ast_signal_summary": {},
  "stage_4_rubric": {},
  "replication_score": 0,
  "replication_tier": "R0",
  "explain_available": true
}
```

Backward compatibility:

- Keep existing `stage_1_readme_intent` JSON key.
- Keep existing score keys.
- Keep v1.2 final score semantics unless explicitly changed in a later minor/patch with benchmark evidence.

---

## 6. AST Code Structure Analysis

AST analysis is observation-only in v1.3.0.

Policy:

- v1.3.0 emits `ast_signal_summary`.
- v1.3.0 may attach AST findings to `evidence_ledger`.
- v1.3.0 does **not** alter final score based on AST findings.
- v1.3.1 may add score influence only after benchmark analysis shows it improves tier alignment and does not inflate false confidence.

Required AST detectors:

| Detector | Purpose | Method |
|---|---|---|
| `AST_test_functions` | 실제 테스트 함수 수 | `FunctionDef.name.startswith("test_")` |
| `AST_assertion_tests` | assertion 있는 테스트 수 | `ast.Assert`, common assert-call patterns |
| `AST_docstring_coverage` | public function docstring 비율 | `ast.get_docstring()` |
| `AST_type_annotation_coverage` | function parameter/return annotation 비율 | `arg.annotation`, `returns` |
| `AST_seed_setting` | 재현성 seed 설정 | `random.seed`, `np.random.seed`, `torch.manual_seed` |
| `AST_argparse_cli` | CLI 재현성 인터페이스 | `argparse.ArgumentParser` |
| `AST_portable_model_loading` | GPU-agnostic loading pattern | `torch.load(..., map_location=...)` |
| `AST_fail_open_precision` | broad/fail-open exception 정밀화 | `ExceptHandler`, `Pass`, `return True` |

AST scale policy:

```python
MAX_AST_FILES = 500
MAX_AST_FILE_SIZE_BYTES = 512_000
```

Skip behavior:

- Files above size limit are skipped with `status: "not_applicable"` and `reason: "file_size_limit_exceeded"`.
- Repos above file count limit analyze the first deterministic path-sorted `MAX_AST_FILES` and emit a finding with `reason: "file_limit_exceeded"`.
- Syntax errors produce `status: "error"` for that file only.
- Binary or undecodable files are skipped with `status: "not_applicable"`.

---

## 7. Stage 4: Reproducibility & Replication Evidence

v1.3 creates a fourth stage as a separate evidence lane.

Name:

> Stage 4: Reproducibility & Replication Evidence

Detector candidates:

| Signal | Method |
|---|---|
| Dockerfile / docker-compose.yml | file existence |
| Makefile `reproduce`, `eval`, `benchmark`, `test` target | text parse |
| environment.yml / requirements lock evidence | file + regex |
| exact dependency pins / hashes | regex |
| README reproducibility section | heading regex |
| checksum files `*.sha256`, `*.md5` | glob |
| dataset URL in README/docs | URL regex + keyword context |
| model weight URL/checksum | URL regex + model/checkpoint context |
| CITATION.cff | file existence |
| CLI entry point | pyproject scripts / argparse AST |
| seed setting | AST summary |
| runnable examples/notebooks | file existence + path heuristics |

Scoring policy:

- v1.3.0 outputs `replication_score`, `replication_tier`, and `stage_4_rubric`.
- v1.3.0 does not fold Stage 4 into the existing final score.
- Reports show Stage 4 beside the existing score as a replication evidence lane.
- v1.3.1 may adjust final score weights after benchmark evidence.

Replication tier mapping:

| Tier | Score | Meaning |
|---|---:|---|
| R0 | 0-24 | No meaningful replication evidence detected |
| R1 | 25-44 | Minimal replication evidence; manual setup likely required |
| R2 | 45-64 | Partial replication evidence; some runnable or provenance signals present |
| R3 | 65-84 | Adequate replication evidence for independent technical review |
| R4 | 85-100 | Strong replication evidence surface; still not clinical validation |

---

## 8. Reasoning Mathematical Model Deferred To v1.3.1

`stem_ai/reasoning_model.py` is no longer required for v1.3.0. It is a v1.3.1 target after the v1.3 evidence ledger, Stage 4, `--explain`, and benchmark foundation are in place.

Accepted LOGOS-derived candidates are documented in:

```text
docs/V1_3_REASONING_MODEL_CANDIDATES.md
```

v1.3.1 candidate model outputs:

```json
{
  "reasoning_model": {
    "version": "stem-bio-ai-reasoning-v1.3.1",
    "evidence_budget": {},
    "confidence_envelope": {},
    "lane_coherence": {},
    "uncertainty_budget": {},
    "evidence_risk_gate": {},
    "benchmark_alignment": null
  }
}
```

Required functions:

```python
def required_bits(confidence: float) -> float: ...
def unique_token_count(text: str) -> int: ...
def observed_bits(text: str) -> float: ...
def evidence_budget(confidence: float, evidence_text: str) -> dict: ...
def confidence_envelope(confidence: float, evidence_count: int) -> dict: ...
def lane_coherence(stage_scores: dict) -> dict: ...
def uncertainty_budget(stage_scores: dict, detector_counts: dict) -> dict: ...
def evidence_risk_gate(risk_components: dict, risk_gate: float = 0.60) -> dict: ...
def benchmark_alignment(stem_tiers: list[int], manual_tiers: list[int]) -> dict: ...
```

v1.3.1 reasoning model policy:

- It is diagnostic, not a final-score replacement.
- It may flag high uncertainty or overconfidence.
- It may support v1.3.1+ release gates.
- It must not claim clinical truth.
- It must be implementable with Python stdlib only.
- It must not create a grand unified trust equation.
- It must not replace or override the existing final score.
- All initial weights are uncalibrated priors. They must be labeled as initial estimates and recalibrated only if the 30-repo benchmark supports adjustment.
- `lane_coherence` excludes any stage score that is `None`. If Stage 4 is unavailable, coherence is computed from the remaining valid lane pairs instead of treating S4 as zero.

Deferred:

- Entropy gate
- representation geometry
- LLM reasoning adapters
- symbolic theorem proving

---

## 9. 30-Repository Benchmark

The benchmark is the body of v1.3. It turns deterministic scanning from a claim into evidence.

Target composition:

| Expected Tier | Count | Selection Character |
|---|---:|---|
| T0 | 5 | 코드/문서/테스트/CI가 거의 없거나 unbounded clinical claim |
| T1 | 5 | README 중심, code stub 수준, evidence surface 빈약 |
| T2 | 8 | 부분 문서, CI/test 부족, clinical-adjacent language 존재 |
| T3 | 8 | CI + tests + docs 존재, reproducibility는 제한적 |
| T4 | 4 | 논문/재현성 패키지/명확한 provenance/peer-reviewed context |

Selection criteria:

- Source: public GitHub repositories.
- Topics/search terms include `bioinformatics`, `medical-ai`, `clinical-nlp`, `genomics`, `variant-calling`, `biomedical-ai`.
- Stars: prefer `> 30` to avoid trivial abandoned samples; exceptions must be justified.
- Last commit: within 3 years unless the repo is historically important and clearly labeled as stale.
- Primary language: Python or Python-majority mixed repo.
- Each repo must be pinned by commit hash.
- Repos must not be selected solely because they fit a desired tier.

Bias-control rule:

1. Select candidate repos using criteria above.
2. Run STEM deterministic scan first.
3. Record STEM score/tier.
4. Perform manual verdict after scan output is frozen.
5. Compare STEM tier to manual verdict.

Manual verdict must not be used to pre-shape the STEM score.

Benchmark entry:

```json
{
  "repo": "owner/name",
  "commit": "abcdef123456",
  "date_scanned": "2026-05-xx",
  "stem_score": 71,
  "stem_tier": "T3",
  "replication_score": 64,
  "replication_tier": "R2",
  "manual_verdict": "T3",
  "tier_delta": 0,
  "false_positive_flags": ["B2 detected from generic limitations section"],
  "false_negative_flags": ["missed Docker reproducibility signal"],
  "notes": "Manual review agrees with T3 but Stage 4 is weak."
}
```

Output location:

```text
audits/benchmark-v1.3/
  benchmark_manifest.json
  benchmark_results.jsonl
  tier_alignment_summary.md
  false_positive_false_negative_log.md
  repos/
    owner_repo_commit/
      experiment_results.json
      report.md
      explain.txt
```

`benchmark_manifest.json` minimum schema:

```json
{
  "schema_version": "stem-bio-ai-benchmark-v1.3",
  "generated_at": "2026-05-xx",
  "stem_ai_version": "1.3.0",
  "selection_criteria": {
    "topics": ["bioinformatics", "medical-ai", "clinical-nlp", "genomics", "variant-calling", "biomedical-ai"],
    "stars_preferred_min": 30,
    "last_commit_within_years": 3,
    "primary_language": "Python or Python-majority mixed",
    "manual_verdict_after_scan": true
  },
  "repo_count": 30,
  "repos": [
    {
      "repo": "owner/name",
      "commit": "abcdef123456",
      "selected_by": ["topic:bioinformatics", "stars>30", "python-majority"],
      "exception_note": ""
    }
  ]
}
```

Metrics:

- exact tier agreement
- adjacent tier agreement
- mean absolute tier error
- rank agreement
- detector false positive count/rate
- detector false negative count/rate
- manual review required rate
- parse error rate
- Stage 4 signal coverage

---

## 10. `--explain` Flag

`--explain` is the proof interface.

Expected CLI:

```bash
stem audit /path/to/repo --explain
stem /path/to/repo --level 3 --format all --explain
```

Expected output:

```text
B2_bias_limitations: MATCH
  finding_id: B2_bias_limitations:README.md:42:001
  file: README.md:42
  pattern: bias_limitations_v2
  snippet: "Limitations and validation boundaries are documented."

C4_fail_open: WARN
  finding_id: AST_fail_open_precision:src/model.py:87:001
  file: src/model.py:87
  reason: broad exception handler with pass

S4_reproducibility: PASS
  Dockerfile found
  Makefile target "reproduce" found
  CITATION.cff found

```

`--explain`은 report보다 더 낮은 층의 증거 인터페이스다. 사람이 파일을 열어 바로 검증할 수 있어야 한다.

---

## 11. Execution Plan

### Week 1: Evidence Foundation

- Add `stem_ai/evidence.py`.
- Add `EvidenceFinding` and detector result contracts.
- Add `stem_ai/detectors.py`.
- Wrap existing regex/file-existence detectors into evidence ledger output.
- Add AST parser utility with file count/size limits.
- Add AST detectors listed in Section 6.
- Add `evidence_ledger` and `ast_signal_summary` to JSON output.
- Preserve existing v1.2 score behavior.

Week 1 acceptance criteria:

- `python -m pytest -q` passes.
- A JSON audit run against an existing stable fixture or reference repo preserves the v1.2 final score exactly.
- JSON output includes `evidence_ledger`.
- JSON output includes `ast_signal_summary`.
- `stage_1_readme_intent` remains present.

### Week 2: Stage 4 + Explainability

- Add Stage 4 reproducibility detectors.
- Add `replication_score`, `replication_tier`, and `stage_4_rubric`.
- Add Markdown Stage 4 summary.
- Add PDF Stage 4 summary if layout budget permits; otherwise include in fallback/appendix.
- Add `--explain` CLI flag.
- Add explain text renderer.
- Add finding ID, line, and snippet extraction for regex and AST findings.

### Week 2-3 Parallel: LOGOS / Reasoning Model Research Track

- Inspect `D:\Sanctum\Flamehaven-LOGOS` for reusable mathematical models.
- Record candidates in `docs/V1_3_REASONING_MODEL_CANDIDATES.md`.
- Do not implement `stem_ai/reasoning_model.py` in v1.3.0.
- This track is research/documentation only for v1.3.0.
- If a LOGOS-derived candidate is not applicable, skip that candidate.
- Applicable small stdlib-compatible diagnostic models move to v1.3.1.
- Any high-complexity model is deferred to v1.4+.

### Week 3: Benchmark Execution

- Select 30 repos using Section 9 criteria.
- Pin commit hashes.
- Run deterministic audit.
- Save JSON/report/explain output.
- Record manual verdicts after scan output is frozen.
- Record false positives and false negatives.
- Patch detector patterns only when benchmark evidence justifies it.

### Week 4: Release Hardening

- Freeze schema.
- Update README with v1.3 benchmark methodology.
- Update CHANGELOG.
- Add tests for every new detector category.
- Add benchmark aggregation smoke test.
- Run full package build.
- Generate at least one public benchmark artifact packet.

---

## 12. Test Plan

Unit tests:

- EvidenceFinding serializes to JSON-compatible dict.
- Detector registry returns deterministic detector order.
- AST parser handles valid Python.
- AST parser records syntax error without aborting.
- AST file limits produce `not_applicable` findings.
- test function detector counts `test_` functions.
- assertion detector distinguishes tests with/without assertions.
- seed detector catches `random.seed`, `np.random.seed`, `torch.manual_seed`.
- fail-open AST detector catches `except: pass` and `except Exception: return True`.
- Stage 4 detects Dockerfile, Makefile targets, checksum files, CITATION.cff.
- Evidence ledger entries include detector, status, file, line, snippet where applicable.
- `finding_id` uses repo-relative POSIX paths and deterministic per-file occurrence counters.

Regression tests:

- Existing v1.2 scoring behavior remains stable.
- `stage_1_readme_intent` key remains present.
- B2 evidence still excludes bare `population`.
- `measurement_basis` remains present.
- `stem_ai_version` remains package version.

Integration tests:

- `python -m pytest -q`
- `python -m build --no-isolation`
- `stem audit fixtures/t3_good_research_repo --explain`
- benchmark aggregation on a small 3-repo smoke set before full 30-repo run.

---

## 13. Release Gates

v1.3.0 is not releasable until all gates pass:

- Evidence ledger exists in JSON output.
- `ast_signal_summary` exists and does not alter final score.
- At least 8 AST-backed tests pass.
- Stage 4 score appears in JSON and Markdown output.
- `--explain` produces file/line/snippet evidence for regex and AST findings.
- 30-repo benchmark manifest is committed.
- Manual verdict exists for every benchmark repo.
- Tier alignment summary is committed and includes actual benchmark alignment metrics computed from the 30 committed results.
- False-positive/false-negative log is committed.
- README states benchmark methodology and measurement boundary.
- No claim says clinical safety, scientific validity, or regulatory compliance is certified.

---

## 14. v1.4 Entry Conditions

AI may enter in v1.4 only if v1.3 produces a stable deterministic evidence floor.

AI constraints:

- AI reads the evidence ledger, not arbitrary raw repo text as its primary source.
- AI cannot directly mutate deterministic score fields.
- AI output is stored separately as advisory rationale.
- AI must cite evidence finding IDs.
- AI may assist `manual_review_required` items but cannot silently resolve them.
- AI uncertainty must be represented explicitly.
- AI outputs must pass evidence budget and grounding checks before display as advisory text.

This keeps AI as an evidence analyst, not a judge.

---

## 15. Implementation Start Criteria

Implementation may begin without waiting for LOGOS review completion.

Start immediately with:

1. `evidence.py`
2. `detectors.py`
3. AST observation-only detectors
4. evidence ledger JSON output

Parallel research work:

1. Reasoning model candidates from LOGOS
2. v1.3.1 `reasoning_model.py` diagnostic design
3. benchmark calibration formulas for later implementation

The critical path is evidence foundation first, benchmark proof second, AI-readiness third.
