# STEM-BIO-AI — MIT AI Risk Repository 기반 적용 가능성 진단

**날짜:** 2026-05-12
**기반 데이터:**
- MIT AI Risk Repository V4_03 (2026-04-23 export) — 1,595 risk entries, 7 domains, 24 subdomains
- arXiv:2408.12622 (Slattery et al., Patterns 2026, CC BY 4.0)
- airisk.mit.edu

---

## 1. MIT AI Risk Repository 구조 요약

### 7대 도메인 / 24 서브도메인

| ID | 도메인 | 핵심 서브도메인 |
|---|---|---|
| 1 | Discrimination & Toxicity | 1.1 차별/왜곡, 1.2 독성 콘텐츠, 1.3 집단간 성능 불균등 |
| 2 | Privacy & Security | 2.1 PII 유출/추론, 2.2 AI 시스템 보안 취약점 |
| 3 | Misinformation | 3.1 허위/오도 정보, 3.2 정보 생태계 오염 |
| 4 | Malicious Actors | 4.1 디스인포, 4.2 사이버공격/무기, 4.3 사기/조작 |
| 5 | Human-Computer Interaction | 5.1 과의존/불안전 사용, 5.2 자율성 상실 |
| 6 | Socioeconomic & Environmental | 6.1-6.6 불평등/고용/거버넌스/환경 |
| 7 | AI System Safety | 7.1 목표충돌, 7.2 위험역량, 7.3 성능부족, 7.4 투명성부족, 7.5-7.6 |

**핵심 발견:** 인간 결정이 AI 리스크의 38%, AI 시스템 자체가 42% 유발 — 즉 Pre-deployment governance가 50% 이상의 리스크를 커버할 수 있다.

---

## 2. 의료/임상 관련 핵심 리스크 목록

### 임상/의료 직접 리스크

| Risk ID | 제목 | 도메인 | 출처 |
|---|---|---|---|
| 41.04.00 | Healthcare — 과의존 | 5.1 | Allianz2018 |
| 24.01.03 | 새 질병 컨텍스트 의료 AI 탐색 문제 | 7.3 | Gabriel2024 |
| 24.03.08 | 의료 AI 통한 개인 의료기록 추출 | 2.1 | Gabriel2024 |
| 39.25.00 | 의료 헬스케어 black-box AI 검증불가 | 7.4 | Saghiri2022 |
| 70.01.02 | 헬스케어 자동화 사고 피해 | 7.3 | Perlo2025 |
| 70.02.02 | 임상 지식 환각(hallucination) | 3.1 | Perlo2025 |
| 60.02.01 | 부정확한 의료 정보 신뢰성 문제 | 7.3 | Bengio2025 |
| 43.01.00 | 의료/법률/금융 AI 신뢰성 요건 | 7.0 | InfoComm2023 |

### PII / 재식별 리스크

| Risk ID | 제목 | 도메인 | 출처 |
|---|---|---|---|
| 65.03.01 | PII/SPI in training data | 2.1 | IBM2025 |
| **65.03.03** | **재식별 (PII 제거 후에도)** | **2.1** | **IBM2025** |
| 65.20.01 | PII 출력 유출 | 2.1 | IBM2025 |
| 02.07.01-03 | LLM PII 기억/추출/연결 | 2.1 | Cui2024 |
| 60.03.05 | 훈련 데이터 내 의료기록 노출 | 2.1 | Bengio2025 |
| 70.02.01 | EAI의 PII 공개 | 2.1 | Perlo2025 |

### 관련 거버넌스 프레임워크

- **HIPAA**: Virginia HB 2154 — 병원/요양원 AI HIPAA 준수 의무
- **NIST AI RMF**: Federal AI Risk Management Act 2023
- **FDA**: 의약품 감시 AI, FDA 승인 AI 처방
- **EU AI Act**: 의료 고위험 AI 분류
- **HHS 차별금지**: 환자 케어 의사결정 지원 도구 비차별

---

## 3. STEM-BIO-AI — 도메인별 커버리지 매핑

### 커버리지 매트릭스

| MIT 도메인 | 커버리지 | STEM-BIO-AI 탐지기 | 비고 |
|---|---|---|---|
| **1. 차별/독성** | LOW | B2 (텍스트), R4 (인구통계) | 표면 텍스트만, 실측 성능 미평가 |
| **2. 프라이버시/보안** | MEDIUM-HIGH | C1 (자격증명), C3 (환자경로), CC-3 (얕은 검증) | 재식별 API 노출 미탐지 |
| **3. 허위정보** | HIGH | CC-1 (confidence=0), CC-2 (API계약) | 코드 레벨 허위 클레임 탐지 |
| **4. 악의적 행위자** | NONE | — | 설계 범위 밖 |
| **5. HCI / 과의존** | HIGH | T0 floor, CA-DIRECT, H1-H3 (임상 과장) | 핵심 차별화 강점 |
| **6. 사회경제/환경** | LOW | Stage 4 (재현성) | 거버넌스 언어 부분 탐지 |
| **7. AI 안전/한계** | MEDIUM | C4 (fail-open), CC-1, CC-3, B2 | 7.3 성능부족, 7.4 투명성 부분 |

### 세부 탐지기 → MIT 리스크 ID 매핑

| STEM-BIO-AI 탐지기 | 커버하는 MIT 리스크 | 설명 |
|---|---|---|
| **T0 hard floor** | 5.1 (41.04.00, 61.02.28) | 임상 경계 선언 부재 → 과의존 리스크 |
| **CA-DIRECT** | 5.1, 5.2 | "diagnosis", "treatment recommendation" 감지 |
| **H1-H3 (hype)** | 5.2, 3.1 | 과장 임상 주장 → 허위정보/자율성 상실 |
| **CC-1** | 3.1 (70.02.02, 60.02.01) | confidence=0.0 → 저신뢰도 예측 그대로 임상 출력 |
| **CC-2** | 3.1, 7.4 | README 허위 API 선언 → 투명성 부족 |
| **CC-3** | 2.1 (65.03.01, 70.02.01) | 얕은 SSN/PII 검증 → 재식별 위험 |
| **C1** | 2.2 | 하드코딩 자격증명 → 보안 취약점 |
| **C4** | 7.3 (70.01.02) | fail-open → 사고 피해 |
| **B2** | 1.3, 7.4 | 편향/한계 언어 부재 → 집단간 성능불균등, 불투명 |
| **Stage 4** | 7.3, 7.4 | 재현성 증거 → 신뢰성/투명성 |

---

## 4. 공백 (Gap) 분석 — MIT 기준 미커버 리스크

### 고우선순위 공백

| MIT 리스크 | ID | 현재 STEM-BIO-AI 상태 | 추가 탐지기 제안 |
|---|---|---|---|
| **재식별 API 공개 노출** | 65.03.03 | 미탐지 | `CC-4_reidentify_api_exposure`: public API에 `reidentify()`/`deanonymize()` 감지 |
| **임상 hallucination 정량화** | 70.02.02 | CC-1로 부분 탐지, 실측 불가 | Layer 3 (동적 테스트) — Layer 2 한계 |
| **훈련 데이터 출처 부재** | 65.03.01, 60.03.05 | B1 부분 탐지 | 데이터 카드/Model Card 존재 여부 |
| **Black-box 검증불가** | 39.25.00 | B2 부분 탐지 | Model Card/interpretability 문서 탐지 |
| **집단간 성능불균등** | 1.3 (11.02.00) | B2 텍스트만 | 실측 F1-by-subgroup 불가 (Layer 2 한계) |
| **모델 버전 미고정** | 7.3 | Stage 4 일부 | HF Hub revision 핀 여부 직접 검사 |

### 저우선순위 공백 (설계 범위 밖)

- Domain 4 (악의적 행위자): STEM-BIO-AI는 governance 도구로 악의적 사용 감지 미포함 — 의도적 설계
- Domain 6 사회경제/환경: 단일 레포 스캐너 수준에서 접근 불가
- 7.1 목표충돌, 7.5 AI welfare: 철학적 분류, 정적 분석 불가

---

## 5. STEM-BIO-AI 포지셔닝 진단

### 강점 — 타 도구 대비 차별화

1. **Pre-deployment governance gate 특화**: MIT 인과 분류 기준 "Pre-deployment / Unintentional" 리스크의 70%+ 탐지 가능
2. **임상 과의존 리스크 (5.1) 유일한 자동 탐지**: T0 hard floor 메커니즘은 오픈소스 대안 없음
3. **코드 레벨 허위정보 (3.1)**: CC-1/CC-2는 confidence=0 + 허위 API 동시 탐지

### 약점 — 구조적 한계

1. **Post-deployment 커버리지 0**: 런타임 모니터링, 실제 출력 품질 측정 불가
2. **Domain 1 (차별)**: 표면 텍스트 탐지만 — 실제 subgroup 편향 측정 Layer 3 필요
3. **재식별 리스크 (65.03.03)**: `reidentify()` 공개 API 노출이 가장 큰 미탐지 공백

### 사용 적합 시나리오

| 시나리오 | 적합도 | 이유 |
|---|---|---|
| HuggingFace 의료 AI 레포 사전 검토 | **최상** | T0/CA 분류 + CC 탐지기 완비 |
| 병원 조달 전 AI 도구 1차 심사 | **높음** | 임상 경계 + 코드 계약 자동 검사 |
| HIPAA compliance 보조 레이어 | **중간** | CC-3(PII 검증), CC-4(재식별) 필요 |
| FDA SaMD 제출 전 완전 감사 | **보조만** | Layer 3 동적 + 전문가 검토 필수 |
| 연구 바이오인포매틱스 레포 | **높음** | T0/CA + 재현성 Stage 4 |

---

## 6. 다음 단계 권고

### 즉시 (v1.7.x)
1. **CC-4 추가**: `reidentify()`/`deanonymize()` public API 노출 탐지 → 리스크 65.03.03 직접 커버
2. **HF Hub revision 핀 체크**: `model_id` 지정에 `revision=` 또는 commit hash 없으면 WARN → 리스크 7.3

### 중기 (v2.0)
3. **Model Card / Data Card 존재 탐지**: 미존재 시 7.4 (투명성), 1.3 (편향) 경고
4. **MIT Risk Repository 연동**: 스캔 결과에 커버되는 MIT 리스크 ID 자동 매핑 출력

---

*MIT AI Risk Repository V4_03 (2026-04-23) | airisk.mit.edu | Flamehaven Research | 2026-05-12*
