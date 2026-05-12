# STEM-BIO-AI 이중 검수 보고서

**날짜:** 2026-05-11 | **버전:** v1.6.8 → v1.7.0 기록 기준 | **상태:** 패치 로드맵 확정 (2026-05-12)

---

## 검수 결과 요약

| 검수 도구 | 판정 | 핵심 지표 |
|---|---|---|
| AI-SLOP-Detector v3.7.3 | **clean** (exit 0) | 결함 파일 4개 / 97개, weighted deficit 19.38 |
| SIDRCE SaaS 1.1.15 | **REVIEW** (Grade A) | Omega 0.7883 (inspect) / 0.9945 (pipeline-insight) |

---

## AI-SLOP-Detector — 결함 파일 4개

| 순위 | 파일 | Score | 등급 | 핵심 패턴 |
|---|---|---|---|---|
| 1 | `stem_ai/detector_bio.py` | 72.12 | `critical_deficit` | 11-함수 클론 클러스터, nested_complexity x4 |
| 2 | `stem_ai/detector_contract.py` | 63.93 | `inflated_signal` | nested_complexity x3 (신규 작성 파일) |
| 3 | `stem_ai/cli.py` | 43.45 | `suspicious` | `main` cc=14, print 함수 5개 클론 |
| 4 | `stem_ai/advisory_contract.py` | 39.52 | `suspicious` | 8-함수 클론 클러스터 |

### CRITICAL 발견 상세

#### detector_bio.py (score 72.12)
- `function_clone_cluster`: `_looks_like_smiles`, `_is_obviously_not_smiles`, `_smiles_context_permits`, `_is_strong_smiles_variable`, `_smiles_issues`, `_stmt_sets_mock_behavior` 등 11개 함수 AST JSD < 0.05
- `nested_complexity` x4:
  - `_collect_silent_mock_findings` (L260, depth=4, cc=14)
  - `_smiles_context_permits` (L513, depth=4, cc=13)
  - `_stmt_sets_mock_behavior` (L624, depth=5, cc=12)
  - `_run_trace_metadata` (L648, depth=5, cc=13)

#### detector_contract.py (score 63.93) — 신규 작성 파일
- `_readme_claimed_names` (L137): **depth=8** — 프로젝트 전체 최악 중첩 깊이
- `_detect_clinical_zero_default` (L44): depth=4, cc=16
- `_extract_package_all` (L115): depth=5, cc=12

#### advisory_contract.py (score 39.52)
- `function_clone_cluster`: `cited_finding_ids`, `_prohibited_claims`, `_missing_citation_items`, `_validate_item_list`, `_offline_reviewer_notes`, `_offline_inspection_priorities` 등 8개 클론

#### cli.py (score 43.45)
- `main` (L717): depth=5, cc=14
- `function_clone_cluster`: `_print_full_summary`, `_print_policy_simulate` 등 print 함수 5개

### 공통 패턴

| Pattern ID | Axis | Severity | 건수 |
|---|---|---|---|
| `nested_complexity` | quality | CRITICAL | 10 |
| `function_clone_cluster` | structure | CRITICAL | 3 |
| `god_function` | style | high | 22 |
| `deep_nesting` | style | high | 8 |
| `phantom_import` | quality | medium | 2 (rdkit, detector_bio.py L826/L837) |
| `lint_escape` | quality | medium | 3 |

---

## SIDRCE SaaS — 차원별 점수

| 차원 | 기호 | 가중치 | pipeline-insight 점수 |
|---|---|---|---|
| Integrity | Sigma | 0.30 | 0.9946 |
| Purity | Pi | 0.25 | 1.0000 |
| Stability | Delta | 0.25 | 1.0000 |
| Coherence | Gamma | 0.20 | 0.9806 |
| **Omega** | **Omega** | — | **0.9945** |

- inspect 모드 Omega: 0.7883 (10파일 샘플, entropy avg 4.24bit → Delta 억제)
- pipeline-insight 97파일 기준 실질 품질: 0.9945 (A+ 수준)
- 리스크 파일 1개: `tmp/backend_build/build_backend.py` (DDC=0.50, tmp 경로)
- 24/30 파일 "inconsistent entropy" (모듈 성격 다양성으로 판단)
- `vulture` 미설치 — dead code 스캔 미완성

---

## 교차 확인 — 두 도구 일치 항목

| 이슈 | SLOP 판정 | SIDRCE 영향 |
|---|---|---|
| `detector_contract.py` 구조 복잡도 | CRITICAL (depth=8) | Gamma 감산 요인 |
| `detector_bio.py` 클론 클러스터 | CRITICAL | 엔트로피 패턴 이상 |
| `tmp/` 디렉토리 오염 | 97→35 파일 부풀림 | DDC 리스크 파일 원인 |

---

## v1.7.0 이후 상태

`detector_contract.py`는 v1.7.0에서 신규 작성되어 CC-1/CC-2/CC-3 탐지가 동작하지만, 검수에서 지적된 **구조적 복잡도 문제는 미해결** 상태로 다음 패치에 이관.

---

## 패치 로드맵

### v1.7.1 — 구조 부채 1차 해소 (P0) — DONE 2026-05-12

**대상: `stem_ai/detector_contract.py`** (commit 22af1f8)

| 함수 | 현황 | 조치 | 결과 |
|---|---|---|---|
| `_readme_claimed_names` | depth=8 | `_flush_code_block()` 헬퍼 추출 | depth 8→3 |
| `_detect_clinical_zero_default` | cc=16 | `_collect_candidate_pairs()` 추출 | cc ~4 |
| `_extract_package_all` | depth=5, cc=12 | `_parse_all_assign()` 추출 | depth 5→2 |

**대상: 설정** `.slopconfig.yaml` 신규 — `tmp/`, `build/`, `dist/` 제외

137/137 tests pass

### v1.7.2 — 클론 클러스터 해소 (P1)

**대상: `stem_ai/detector_bio.py`**

| 이슈 | 현황 | 조치 |
|---|---|---|
| SMILES 함수 클론 11개 | AST JSD < 0.05 (거의 동일) | `_SMILES_RULES: list[tuple[str, Callable]]` dispatch table로 통합, `_apply_smiles_rule()` 단일 실행기 |
| `nested_complexity` x4 | `_collect_silent_mock_findings` cc=14 등 | 조건 분기 → 전략 함수 추출 |

**대상: `pyproject.toml`**

```toml
[project.optional-dependencies]
bio = ["rdkit>=2023.3"]
```
`rdkit` phantom import → optional dep 선언 + `try/except ImportError` 가드로 교체

### v1.7.3 — 코드 위생 완성 (P2)

| 항목 | 조치 |
|---|---|
| `cli.py` `main` cc=14 | `_handle_scan_cmd()`, `_handle_policy_cmd()` 등 서브핸들러 추출 |
| print 함수 5개 클론 | `_print_section(title, rows)` 공통 렌더러 통합 |
| `advisory_contract.py` 8-함수 클론 | 공통 `_validate_list_field(key, items, rules)` 추출 |
| `vulture` 설치 | `pip install vulture` + `scripts/dead_code_check.sh` 추가 |

---

## 검수 도구 재실행 기준

| 버전 | 기대 목표 |
|---|---|
| v1.7.1 | `detector_contract.py` slop score ≤ 30 (현 63.93) |
| v1.7.2 | `detector_bio.py` slop score ≤ 35 (현 72.12) |
| v1.7.3 | SIDRCE Omega ≥ 0.85 in inspect 모드 (현 0.7883) |

---

*AI-SLOP-Detector v3.7.3 + SIDRCE SaaS 1.1.15 | Flamehaven Research | 2026-05-11*
*패치 로드맵 확정: 2026-05-12*
