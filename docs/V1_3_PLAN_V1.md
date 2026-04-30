# STEM BIO-AI v1.3 Plan v1

**Status:** Draft v1
**Target Version:** 1.3.0
**Date:** 2026-04-30
**Positioning:** Deterministic benchmark-evidenced bio/medical repository audit framework

---

## 1. Strategic Judgment

v1.3의 목표는 v1.2에서 정직하게 선언한 측정 경계가 실제로 의미 있음을 증명하는 것이다.

```text
v1.2 = "우리가 측정하는 것을 솔직하게 말한다"          (label honesty)
v1.3 = "그 측정이 의미 있음을 증거로 보여준다"          (benchmark evidence)
v1.4 = "증명된 결정론적 바닥 위에 AI advisory를 올린다" (AI on solid floor)
```

이 순서가 뒤집히면 AI advisory는 검증되지 않은 해석층이 된다. 따라서 v1.3은 AI 기능 추가가 아니라, 로컬 Python/stdlib 기반 결정론적 검수 엔진의 한계를 최대한 끌어올리고 그 한계를 공개적으로 기록하는 버전이다.

v1.3의 한 줄 목표:

> Deterministic local evidence scanning is made meaningful through AST-backed detectors, replication-evidence analysis, explainable findings, and a fixed 30-repository benchmark.

---

## 2. Scope Boundary

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

---

## 3. Core Architecture Change

현재 v1.2 구조는 scanner가 detection, scoring, evidence text 생성을 상당 부분 동시에 수행한다. v1.3에서는 다음 계층으로 분리한다.

```text
Repository files
  -> Detector Registry
  -> Evidence Ledger
  -> Stage Evaluators
  -> Scoring Model
  -> Renderers / --explain / JSON
```

필수 구조:

- **Detector:** 물리적 신호를 찾는다. 점수 판단을 하지 않는다.
- **EvidenceFinding:** detector 결과를 표준 구조로 저장한다.
- **Stage Evaluator:** evidence를 stage별 meaning으로 해석한다.
- **Scorer:** stage score와 tier를 계산한다.
- **Renderer:** 사람이 읽을 수 있는 proof packet을 만든다.

초기 구현은 큰 리팩터를 피하기 위해 `scanner.py` 내부에서 시작할 수 있다. 단, 데이터 구조는 별도 모듈로 분리 가능한 형태로 둔다.

권장 파일:

```text
stem_ai/evidence.py        # EvidenceFinding, DetectorResult dataclass
stem_ai/detectors.py       # detector registry and deterministic detectors
stem_ai/scanner.py         # orchestration + score compatibility layer
stem_ai/render.py          # report and explain rendering
```

---

## 4. Evidence Ledger Contract

모든 detector는 가능한 경우 다음 형태의 evidence를 남긴다.

```json
{
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

표준 status:

- `detected`: 결정론적 증거 발견
- `not_detected`: scanner가 찾지 못함
- `absent`: 관련 표면은 있으나 해당 증거 없음
- `not_applicable`: 해당 repo에 적용 불가
- `manual_review_required`: 로컬 결정론적 scan만으로 결론 불가
- `error`: 파일 파싱 또는 detector 실행 오류

v1.3 JSON에는 다음 top-level field를 추가한다.

```json
{
  "schema_version": "stem-ai-local-cli-result-v1.3",
  "evidence_ledger": [],
  "detector_summary": {},
  "explain_available": true
}
```

Backward compatibility를 위해 기존 `stage_1_readme_intent` key는 유지한다. 출력 label만 `README Evidence Signal`로 유지한다.

---

## 5. AST Code Structure Analysis

AST 분석은 v1.3의 최대 수확이다. stdlib `ast`만 사용하므로 zero-dependency 원칙을 유지한다.

필수 detector:

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

AST detector는 syntax error를 실패로 처리하지 않는다. 해당 파일은 `error` finding으로 기록하고 나머지 파일 분석을 계속한다.

초기 scoring 반영:

- v1.3.0에서는 AST signal을 Stage 4와 Code Integrity에 보조 반영한다.
- 기존 final score를 대폭 흔들지 않기 위해 AST score는 별도 `ast_signal_summary`로 먼저 공개한다.
- benchmark 결과를 보고 v1.3.1 또는 v1.4에서 final score 반영 폭을 조정한다.

---

## 6. Stage 4: Reproducibility & Replication Evidence

v1.3에서는 기존 C1-C4 advisory와 일부 reproducibility 신호를 공식 Stage 4로 분리한다.

권장 이름:

> Stage 4: Reproducibility & Replication Evidence

결정론적 detector:

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
| seed setting | AST |
| runnable examples/notebooks | file existence + path heuristics |

초기 점수 정책:

- v1.3.0에서는 Stage 4를 **separate stage score**로 출력한다.
- final score 반영은 보수적으로 한다.
- 권장안: final score는 기존 산식 유지, Stage 4는 `replication_score`와 `replication_tier`로 별도 출력.
- benchmark 후 Stage 4 가중치를 final score에 통합할지 결정한다.

---

## 7. Reasoning Mathematical Model Track

v1.3에는 reasoning 수학 모델을 넣을 후보 자리를 만든다. 단, 모델은 v1.3 Plan v1 작성 이후 `D:\Sanctum\Flamehaven-LOGOS`에서 검토해 실제로 적용 가능한 것만 채택한다.

요구 조건:

- deterministic evidence ledger 위에서 동작해야 한다.
- raw text를 임의 해석하지 않아야 한다.
- detector finding을 입력으로 받아야 한다.
- 점수 산식, confidence, uncertainty, contradiction을 분리해야 한다.
- AI가 없어도 계산 가능해야 한다.

후보 적용 지점:

1. **Evidence Confidence Model**
   - file type, line evidence, detector precision, cross-surface agreement를 결합해 confidence 계산
2. **Contradiction / Consistency Model**
   - README claim과 code/test/docs evidence 사이의 불일치 점수화
3. **Risk-Weighted Scoring Model**
   - clinical-adjacent severity에 따라 같은 missing evidence도 다른 penalty를 갖게 함
4. **Benchmark Alignment Model**
   - STEM tier와 manual tier의 차이를 calibration error로 계산
5. **Uncertainty Budget**
   - `manual_review_required`, `not_detected`, parse error를 uncertainty로 분리 기록

Plan v1에서는 수학 모델을 확정하지 않는다. 다음 단계에서 Flamehaven-LOGOS의 모델을 검토하고 `docs/V1_3_REASONING_MODEL_CANDIDATES.md` 또는 plan v2에 반영한다.

---

## 8. 30-Repository Benchmark

v1.3의 본체는 benchmark evidence다. "결정론적 탐지가 의미 있다"는 주장은 실제 repo benchmark 없이는 할 수 없다.

목표 구성:

| Expected Tier | Count | Selection Character |
|---|---:|---|
| T0 | 5 | 코드/문서/테스트/CI가 거의 없거나 unbounded clinical claim |
| T1 | 5 | README 중심, code stub 수준, evidence surface 빈약 |
| T2 | 8 | 부분 문서, CI/test 부족, clinical-adjacent language 존재 |
| T3 | 8 | CI + tests + docs 존재, reproducibility는 제한적 |
| T4 | 4 | 논문/재현성 패키지/명확한 provenance/peer-reviewed context |

각 benchmark entry는 commit hash로 고정한다.

```json
{
  "repo": "owner/name",
  "commit": "abcdef123456",
  "date_scanned": "2026-05-xx",
  "stem_score": 71,
  "stem_tier": "T3",
  "replication_score": 64,
  "manual_verdict": "T3",
  "tier_delta": 0,
  "false_positive_flags": ["B2 detected from non-clinical limitations section"],
  "false_negative_flags": ["missed Docker reproducibility signal"],
  "notes": "Manual review agrees with T3 but Stage 4 is weak."
}
```

Benchmark output location:

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

Metrics:

- exact tier agreement
- adjacent tier agreement
- mean absolute tier error
- false positive count by detector
- false negative count by detector
- manual review required rate
- parse error rate
- Stage 4 signal coverage

---

## 9. `--explain` Flag

`--explain` is the proof interface.

Expected CLI:

```bash
stem audit /path/to/repo --explain
stem /path/to/repo --level 3 --format all --explain
```

Expected output:

```text
B2_bias_limitations: MATCH
  file: README.md:42
  pattern: bias_limitations_v2
  snippet: "Limitations and validation boundaries are documented."

C4_fail_open: WARN
  file: src/model.py:87
  reason: broad exception handler with pass

S4_reproducibility: PASS
  Dockerfile found
  Makefile target "reproduce" found
  CITATION.cff found
```

`--explain`은 report보다 더 낮은 층의 증거 인터페이스다. 사람이 grep이나 파일 열기로 바로 검증할 수 있어야 한다.

---

## 10. Required Implementation Work

### Week 1: Detector + Evidence Foundation

- Add `EvidenceFinding` data structure.
- Add detector registry contract.
- Add AST parser utility with syntax-error isolation.
- Add AST test/assertion/docstring/type/seed/argparse/fail-open detectors.
- Add `evidence_ledger` to JSON output.
- Preserve existing score keys and report compatibility.

### Week 1: Stage 4 Foundation

- Add Stage 4 reproducibility detectors.
- Add `replication_score`, `replication_tier`, and `stage_4_rubric`.
- Keep final score behavior conservative.
- Add Markdown/PDF Stage 4 summary.

### Week 2: Explainability

- Add `--explain` CLI flag.
- Add explain text renderer.
- Add line/snippet extraction for regex detectors.
- Add detector summary table.

### Week 2: Benchmark Harness

- Add benchmark manifest schema.
- Add script to run fixed repo paths/commits locally.
- Add result aggregation script.
- Add manual verdict template.

### Week 3: Benchmark Execution

- Select 30 repos.
- Pin commit hashes.
- Run deterministic audit.
- Record manual verdicts.
- Record false positives/false negatives.
- Patch detector patterns only when benchmark evidence justifies it.

### Week 3: Discrimination Expansion

- Add at least 20 YES/NO examples for Stage 4 and AST signals.
- Add examples for `manual_review_required` vs `not_detected`.
- Add false-positive examples from benchmark.

### Week 4: Release Hardening

- Freeze schema.
- Update README with v1.3 benchmark methodology.
- Update CHANGELOG.
- Add tests for every new detector category.
- Run full package build.
- Generate one public benchmark artifact packet.

---

## 11. Test Plan

Unit tests:

- AST parser handles valid Python.
- AST parser records syntax error without aborting.
- test function detector counts `test_` functions.
- assertion detector distinguishes tests with/without assertions.
- seed detector catches `random.seed`, `np.random.seed`, `torch.manual_seed`.
- fail-open AST detector catches `except: pass` and `except Exception: return True`.
- Stage 4 detects Dockerfile, Makefile targets, checksum files, CITATION.cff.
- Evidence ledger entries include detector, status, file, line, snippet where applicable.

Regression tests:

- Existing v1.2 scoring behavior remains stable unless explicitly changed.
- `stage_1_readme_intent` key remains present.
- B2 evidence still excludes bare `population`.
- measurement_basis remains present.
- JSON schema version advances to v1.3 only when v1.3 fields are implemented.

Integration tests:

- `python -m pytest -q`
- `python -m build --no-isolation`
- `stem audit fixtures/t3_good_research_repo --explain`
- benchmark aggregation on a small 3-repo smoke set before full 30-repo run.

---

## 12. Release Gates

v1.3.0 is not releasable until all gates pass:

- Evidence ledger exists in JSON output.
- At least 8 AST-backed tests pass.
- Stage 4 score appears in JSON and Markdown output.
- `--explain` produces file/line/snippet evidence for regex and AST findings.
- 30-repo benchmark manifest is committed.
- Manual verdict exists for every benchmark repo.
- Tier alignment summary is committed.
- False-positive/false-negative log is committed.
- README states benchmark methodology and measurement boundary.
- No claim says clinical safety, scientific validity, or regulatory compliance is certified.

---

## 13. v1.4 Entry Conditions

AI may enter in v1.4 only if v1.3 produces a stable deterministic evidence floor.

AI constraints:

- AI reads the evidence ledger, not arbitrary raw repo text as its primary source.
- AI cannot directly mutate deterministic score fields.
- AI output is stored separately as advisory rationale.
- AI must cite evidence finding IDs.
- AI may assist `manual_review_required` items but cannot silently resolve them.
- AI uncertainty must be represented explicitly.

This keeps AI as an evidence analyst, not a judge.

---

## 14. Immediate Next Step

Before implementation, inspect `D:\Sanctum\Flamehaven-LOGOS` for reusable mathematical reasoning models.

Questions for the LOGOS review:

1. Is there a deterministic confidence aggregation model usable for evidence findings?
2. Is there a contradiction/consistency scoring model suitable for Stage 2R?
3. Is there a risk-weighted penalty model suitable for clinical-adjacent severity?
4. Is there an uncertainty budget model suitable for `manual_review_required` and parser errors?
5. Can any model be implemented with Python stdlib only?

The result of that review should become either:

- `docs/V1_3_REASONING_MODEL_CANDIDATES.md`, or
- `docs/V1_3_PLAN_V2.md` if the model materially changes the v1.3 architecture.
