# PLAN — `research` 모드 추가 (dev-advisor v1.x → v2.0)

> **⚠️ 픽스처 상태 (2026-05-28 P3 정리 시점)**: 본 PLAN의 `50쌍 / 50 케이스` 골든 fixture는 **장기 목표**(future target)이다. **현재 활성 검증 기준**은 `scripts/verify/verify-research.sh` 의 `[11-12] research/fixtures/ JSON 케이스 ≥5`. 실제 fixture 카운트는 `references/research/fixtures/`에 5개 (normal 2 + partial-failure 1 + zero-result 1 + schema-drift 1). 50쌍 확장은 §19.5 환각 회귀 자동화 후속 PR 범위.

> **상태**: 설계 (코드 변경 전) — **v0.5 (무료 원칙 강제 + Codex "credit 모델" 주장 폐기)**
> **작성일**: 2026-05-28 (v0.1) / **개정**: 2026-05-28 (v0.2, v0.3, v0.4, v0.5)
> **작성자**: zime + Codex (GPT-5)
> **검토자**: OMX critic (xhigh) + OMX architect (xhigh) + Codex rescue (GPT-5.4) + 사용자 피드백 (zime)
> **대상 스킬**: `~/.codex/skills/dev-advisor/`
> **현재 버전**: 9 advisor 모드 + 6 카탈로그 도메인 (1,235 항목 + 18 부록)
> **목표 버전**: **10 advisor 모드** + 6 카탈로그 도메인 (카탈로그 자체는 변경 없음)
> **아키텍처 결정 (사용자 confirm)**: 옵션 A — `/dev-advisor research` 통합 모드 유지 (§13.2)
> **🆓 무료 원칙 (사용자 확정 — 절대 원칙)**: 모든 외부 API는 키 없이 anonymous 동작 보장. 유료 API/Premium 등급 영원히 out-of-scope. 상용 MCP(Exa 등) 기본 fallback 제거. (v0.5)

### v0.5 변경 요약 (사용자 무료 원칙 피드백 반영)

| 발견 | 출처 | 반영 |
|------|------|------|
| **"API 키 입력 = 유료" 오인 우려** | 사용자 (zime) | §1.2 + §10.1 + §5.1 **"완전 무료" 명시**, "API 키 옵션" 표현으로 통일 |
| **Codex의 "OpenAlex credit 모델" 주장은 검증 없이 채택** |Codex hallucination 가능성 | §5.1 + §10.1 — **무료 무제한**으로 정정, Phase 2 사전 게이트에서 실측 검증 추가 |
| **anonymous 동작 강제 정책 부재** | 사용자 피드백 | 모든 API 호출에서 키 없이도 정상 동작 보장. 키 요구 메시지 출력 금지 |
| **MCP fallback (Exa AI = 상용 유료)** | 사용자 피드백 | §13.4 — **기본 fallback에서 제거**, 사용자 명시 동의 시에만 사용 (default OFF) |
| **무료 정책 실측 검증 게이트 부재** | 사용자 피드백 | §14.5 Phase 2 사전 게이트에 "무료 정책 실측 검증" 의무화 추가 |
| **메모리 저장** | 사용자 피드백 | `feedback_free_api_only_strict.md` 생성 — 향후 모든 PLAN에 적용 |

### v0.4 변경 요약 (미반영 권고안 추가 흡수)

| 발견 | 출처 | 반영 |
|------|------|------|
| `full`/`swarm` 통합 시 research 포함 여부 결정 부재 | architect F-13 | **§13.3 신설** — 미포함 결정 + 사유 + 사용자 명시 시퀀스 |
| `--bias` 디폴트 + 가중치 함수 형태 미명시 | architect F-T1 | **§8.3 보강** — 디폴트 `balanced`, 함수 식 명시 |
| 재현 보고 출처(Papers with Code) 자동화 정책 부재 | critic F12 | **§5.4 보강** — pwc 검색 fallback or `unknown` 명시 |
| MCP 위임 fallback 미고려 (Codex 대안 #4) |Codex | **§13.4 신설** — `WebFetch` 미사용 환경 MCP fallback |
| "환각 0건" 회귀 테스트 자동화 부재 | critic F15 + architect F-10 | **§19.5 신설** — 정규식 검증 hook + golden fixture 50쌍 |

### v0.3 변경 요약 (Codex 검토 반영 — Risk Score 6/10 → 3/10 목표)

| 발견 (Codex) | 심각도 | 반영 |
|--------------|:------:|------|
| **OpenAlex Concepts deprecated → Topics로 전환 필요** | **P1** | §5.2 매핑 표 Topics ID 기반으로 전환 + §14.5 사전 게이트 변경 |
| OpenAlex 2026 기준 API key + credit 모델 (무료 무제한 outdated) | **P1** | §5.1 + §10.1 API 키 환경변수 정책 명시 (`OPENALEX_API_KEY`, `OPENALEX_MAILTO`) |
| arXiv 3초당 1요청/단일 연결 (ToU 위반 가능) | **P1** | §4.4.1 + §18.2 동시성 schedule 수정 (rate-limit aware, arXiv 직렬 throttled) |
| arXiv DOI `10.48550/arXiv.*` ↔ arXiv ID 매핑 누락 | **P1** | §5.3 중복 제거 알고리즘에 명시적 매핑 추가 |
| 제목 유사도 임계값 0.85 → 0.90 권장 (Codex) | P2 | §5.3 임계값 상향 + 충돌 시 분리 표시 |
| "DOI/arXiv ID 없는 논문 출력 금지" 과격 → weak-evidence 섹션 권장 | P2 | §5.4 + §11.1 — primary matrix는 strict, weak identifier는 별도 섹션 최대 2개 |
| Semantic Scholar 무인증 1 RPS 표현 부정확 (실제는 shared throttling) | P2 | §5.1 + §18.2 표현 수정 |
| OpenAlex filter 문법 (`cited_by_count>1000` → `cited_by_count:>1000`) | P3 | §5.1 예시 수정 |
|Codex 대안 #2: 별도 `/research` 스킬 분리 권장 | **결정필요** | §13.2 신설 — 사용자 확인 후 채택 여부 결정 (현재 PLAN은 dev-advisor 통합 유지) |

### v0.2 변경 요약 (Critic + Architect 반영)

| 발견 | 심각도 | 반영 |
|------|:------:|------|
| `search-specialist` 환각 에이전트 (9회 인용) | **P1** | `document-specialist` + `explore` + `analyst` + `scientist`로 교체 |
| HTTP 호출 도구 미정의 | **P1** | §4.4.1 신설 — `WebFetch` 3회 동시 호출 명시 |
| `verify-references.sh` 11번 블록 확장 누락 | **P1** | §8.8 + §19.4에 구체화 |
| OpenAlex Concept ID 환각 위험 | **P1** | §12 Phase 2 사전 게이트 + §14.5 신설 |
| 부분 장애 fallback 정책 부재 | **HIGH** | §17 신설 — Graceful Degradation |
| 성능 목표 / 동시성 모델 미정의 | **HIGH** | §18 신설 — Performance & Concurrency |
| 회귀 방지 메커니즘 부재 | **HIGH** | §19 신설 — Testing Matrix |
| 카탈로그 매핑 신뢰도 정량 기준 | **MED** | §6.1 매핑 신뢰도 정량 표 추가 |
| 라우팅 충돌 케이스 | **MED** | §7.2 충돌 해소 규칙 추가 |
| 세션 내 캐싱 정책 | **MED** | §18.3 in-memory dedup 명시 |
| API 보안 위험 (TLS / polite pool / PDF) | **MED** | §11 위험 표 5행 추가 + §11.1 사전 차단 정책 |
| 한국어 입력 정규화 | **MED** | §4.4 단계 1 정규화 서브스텝 |

---

## 1. 목표 (Goal)

`/dev-advisor`에 **`research` 모드**를 추가하여, 카탈로그(패턴/알고리즘/원칙 등)의 **최신 학술적 근거**를 외부 무료 API 3종(arXiv + Semantic Scholar + OpenAlex)로 검색·정리·인용한다. 카탈로그 lookup의 정적 권위(고정된 표준 인용)와 학술 논문의 동적 최신성(SOTA 추적)을 결합한다.

### 1.1 핵심 가치
1. **최신성** — arXiv 프리프린트로 publication-day 수준의 최신 SOTA 추적
2. **권위** — Semantic Scholar 인용수 + OpenAlex 메타데이터로 영향력 검증
3. **3-source 교차 검증** — 단일 소스 환각·편향 방지
4. **카탈로그 연결** — 검색 결과를 기존 카탈로그 항목(ID)에 매핑하여 학습 지속성 보장
5. **신뢰성·성능 목표** *(v0.2 신규)* — Graceful degradation + p95 latency < 15s + 회귀 차단

### 1.2 비목표 (Non-Goal)
- 정적 논문 카탈로그(`papers/`) 신설 ❌ — 본 PLAN 범위 외 (옵션 A 미채택)
- 양방향 cross-reference (`/pattern singleton`이 자동으로 GoF 논문 표시) ❌ — research 모드 호출 시에만 표시
- 한국어 논문 검색(RISS/DBpia/KCI) ❌ — 추후 별도 PLAN (단, 한국어 입력 검색어는 정규화하여 영문 검색에 활용)
- 유료 API(Web of Science, Scopus, IEEE Xplore) ❌
- **유료 API 영원히 ❌** *(v0.5 — 사용자 무료 원칙)* — Web of Science / Scopus / IEEE Xplore / Semantic Scholar Premium / OpenAlex commercial offering 등 모두 out-of-scope
- **사용자에게 API 키 요구 메시지 출력 ❌** *(v0.5 신규)* — "키를 발급해주세요" 같은 안내 금지. 키 없으면 anonymous로 진행 + 1줄 소극적 안내만
- **API 키 영구 저장 시스템 ❌** *(v0.3 수정)* — 모든 API는 키 없이 **anonymous 동작 보장 (완전 무료)**. 키는 **선택적 rate limit 완화 옵션**이며 **모두 무료 발급**. 런타임 환경변수 입력만 지원: `SEMANTIC_SCHOLAR_API_KEY`(무료), `OPENALEX_API_KEY`(무료), `OPENALEX_MAILTO`(무료 polite pool)
- **상용 MCP fallback ❌** *(v0.5 신규)* — Exa MCP(상용 유료) 등은 사용자 plan 의존이므로 default fallback에서 제거. 사용자 명시 동의 시에만 사용 (§13.4)
- **디스크 영구 캐싱 ❌** — 1차 구현은 세션 내 in-memory dedup만 (단, arXiv ToU 준수를 위해 동일 query 하루 1회 이상 호출 금지 — §18.3)

---

## 2. 범위 (Scope)

### 2.1 In-Scope (이번 PLAN — v0.2)

| 변경 영역 | 변경 유형 | 내용 |
|----------|----------|------|
| `SKILL.md` | 수정 | 9 모드 → 10 모드, 라이프사이클 보조 라우팅에 `evidence/research` 추가, `--help` 업데이트 |
| `references/research/` | **신규** | research 모드 가이드 (`sources.md` / `query-strategies.md` / `output-format.md` / `mapping-algorithm.md` / `fallback.md` / `performance.md` / `testing.md`) |
| `references/research/fixtures/` | **신규** | API mock fixture 50 케이스 (정상/부분장애/0건/스키마변경/한국어) |
| `references/output_templates.md` | 수정 | research 모드 산출 스켈레톤 추가 |
| `references/examples.md` | 수정 | 예시 K (research 정상) / L (자유 질문) / M (0건 대응) 추가 |
| `references/handoff.md` | 수정 | `document-specialist` + `analyst` + `scientist` hand-off 계약 추가 (모두 xhigh 역할 우선) |
| `scripts/verify-references.sh` | 수정 | **11번 블록 확장** — research 모드 등록 7항목 검증 + fixture 무결성 |

### 2.2 Out-of-Scope (이번 PLAN)
- 새 카탈로그 도메인 (`papers/`) 신설 *(§13에 migration path 명시)*
- 양방향 cross-reference (기존 lookup 출력 변경)
- `catalog-index.json` 스키마 변경 (research는 동적이라 정적 색인 불필요)
- 디스크 영구 캐싱 (세션 내 in-memory만 — §18.3)
- 한국어 논문 직접 검색 (한→영 정규화는 in-scope)

---

## 3. 사용자 시나리오 (User Journey)

### 시나리오 A — 카탈로그 ID 기반 학술 근거 탐색
```
사용자: /dev-advisor research transformer
→ Codex:
  1. arXiv API (WebFetch): "transformer attention" search (cs.LG, 2020-2026)
  2. Semantic Scholar API (WebFetch): "transformer architecture" highly cited
  3. OpenAlex API (WebFetch): concept=C119857082 (verified), filter=cited_by_count>1000
  4. 3-source 교차 검증 + 중복 제거 (DOI / arXiv ID / Levenshtein 0.85)
  5. 매트릭스 출력 (8~10편) + 카탈로그 매핑 (/algorithm transformer)
     매핑 신뢰도: HIGH (제목 토큰 일치 + 인용수 ≥ 100)
  6. 6 필드 산출 (선택/근거/대안/표준 인용/적용 조건/신뢰성)
```

### 시나리오 B — 자유 질문 기반 문헌 리뷰
```
사용자: /dev-advisor research "LLM code generation evaluation"
→ Codex:
  1. arXiv: "LLM code generation benchmark" 2024-2026 latest
  2. Semantic Scholar: TLDR 자동 요약 포함
  3. OpenAlex: concept verified + related works
  4. 매트릭스 + 카탈로그 cross-ref (/principle evaluation)
```

### 시나리오 C — 자연어 트리거 + 충돌 해소
```
사용자: "SRP에 대한 최신 연구 보여줘"
→ 라우팅 충돌 해소 (§7.2 신규 규칙):
  1단계: /principle srp (lookup 출력)
  2단계: "이 분야 최신 연구도 보시겠습니까?" 확인
  3단계: research srp (research 모드 후속)
```

### 시나리오 D — 부분 장애 시 Graceful Degradation *(v0.2 신규)*
```
사용자: /dev-advisor research transformer
→ Codex:
  1. arXiv 응답 OK / S2 503 / OpenAlex OK
  2. partial result 모드 진입 (§17.1)
  3. 매트릭스 상단에 ⚠️ degraded mode: Semantic Scholar unavailable
  4. 인용수 컬럼은 OpenAlex 값만 표시 (출처 명시)
  5. 신뢰성·재현성 필드에 single-source 한계 명시
```

---

## 4. 새 advisor 모드 정의 — `research`

### 4.1 명령 시그니처

```
/dev-advisor research <topic|catalog-id|query> [--limit N] [--years YYYY-YYYY] [--source arxiv|s2|openalex|all] [--bias recency|citation]

옵션:
  --limit N         결과 개수 (default 8, max 20)
  --years RANGE     발행 연도 범위 (예: 2020-2026, default last 5 years)
  --source S        검색 소스 강제 (default all = 3-source 교차)
  --bias B          정렬 가중치 (recency=최신성 우선 / citation=인용수 우선, default balanced)
  --no-tldr         Semantic Scholar TLDR 비활성 (속도 우선)
  --free-only       무료 PDF가 있는 논문만 (default false)
```

### 4.2 자연어 트리거

| 자연어 패턴 | 라우팅 결과 |
|-----------|------------|
| "논문 찾아줘", "논문 추천", "학술 근거", "근거 논문" | `research <추출된 키워드>` |
| "research", "literature review", "evidence for X", "SOTA" | `research <X>` |
| "최신 연구", "최신 SOTA", "이 분야 trend" | `research <컨텍스트 기반 키워드>` |
| "X 관련 논문 / X에 대한 연구" | `research X` |
| 카탈로그 ID + "근거"/"학술적 출처" + 학술 키워드 | **시퀀스**: lookup → research (§7.2 충돌 해소) |

### 4.3 10 모드 정의 표에 한 행 추가

```diff
| 모드 | 4단계 인풋 | 4단계 산출 | 인용 references |
| recommend | ... | ... | ... |
...
| swarm | ... | ... | ... |
+ | research | 키워드/카탈로그 ID/자유 질문 + 옵션 | 논문 매트릭스 8~10행 (제목/저자/연도/장소/인용수/무료PDF/카탈로그 매핑/3-source 검증) + 6 필드 + degraded mode 배너(필요시) | [references/research/sources.md], [query-strategies.md], [mapping-algorithm.md], [fallback.md], [performance.md], 카탈로그 6 도메인 (§5.2 도메인별 매핑 표 참조) |
```

### 4.4 6단계 워크플로

| 단계 | 액션 | 산출 |
|------|------|------|
| **1. 입력 수집 + 정규화** | (a) 한국어 감지 시 영문 후보 1~3개 제시 + 모호하면 사용자 confirm 1회 (b) 카탈로그 ID 매핑 시도 → `python3 scripts/lookup-catalog.py <domain> search <kw>` (catalog-index.json SSoT) (c) 정규화된 영문 키워드 우선 사용 | 정제된 영문 검색어 1~3개 + 카탈로그 ID 후보 |
| **2. 컨텍스트 분류** | 카탈로그 ID 매핑 결과 + 도메인 추론(CS/AI/SE/Security) | 검색 도메인 태그 |
| **3. 검색 전략 매핑** | arXiv 분류 코드 + Semantic Scholar field-of-study + OpenAlex concept ID(사전 검증된) 매핑 | API 별 쿼리 3종 |
| **4. 분석/판정 (병렬 검색)** | §4.4.1 도구 매핑 + §18 동시성 schedule 준수 + 개별 timeout 5s + 부분 장애 시 §17 graceful degradation + 중복 제거 (DOI > arXiv ID > 제목 Levenshtein 0.85) + `--bias` 가중치 정렬 | 매트릭스 8~10행 + degraded mode 배너(필요시) |
| **5. 근거 산출 (6 필드)** | 아래 4.5 표 참조 + §11.1 사전 차단 정책(identifier 필수, raw API 응답 직접 reference) | 6 필드 완성 |
| **6. 검증/후속** | 3-source 교차 검증 로그(어느 소스에서 발견했는지) + 카탈로그 매핑 신뢰도(HIGH/MED/LOW) + OMX hand-off 후보 | 검증 로그 + 다음 액션 |

### 4.4.1 API → 도구 매핑 *(v0.3 —Codex P1: arXiv ToU 준수)*

| 소스 | 사용 도구 | 응답 포맷 | 파싱 책임 | 동시성 (Rate-limit aware) |
|------|----------|----------|----------|:------------------------:|
| arXiv | `WebFetch` | Atom 1.0 XML (JSON 아님) | Codex inline XML parsing | **직렬 throttled** (3초당 1요청, 단일 연결) *(v0.3 수정 — 병렬 → 직렬)* |
| Semantic Scholar | `WebFetch` + `fields=` 명시 | JSON | Codex inline JSON parsing | **직렬** (key 권장, shared throttling) |
| OpenAlex | `WebFetch` + `User-Agent: mailto:...` 헤더 (옵션) | JSON | Codex inline JSON parsing | 직렬 (🆓 완전 무료, mailto/key는 무료 옵션) *(v0.5)* |

**실행 모델** *(v0.3 — 전면 수정)*:
- **API 간 병렬은 허용**: arXiv 요청 1건 + OpenAlex 요청 1건은 다른 도메인이므로 단일 어시스턴트 턴에서 동시 실행 가능
- **동일 API 내 다중 query 병렬 금지**: arXiv 다중 query를 병렬로 날리면 ToU(단일 연결) 위반
- **arXiv 동일 query 하루 1회 권장** — §18.3 in-memory cache로 회피
- **Semantic Scholar**: API key 사용 시 1+ RPS, 무인증은 shared throttling (보장 없음)
- 도구 미사용 환경에서는 `document-specialist` 에이전트(xhigh 역할)로 fallback
- `WebFetch` 호출 실패 시 `Bash + curl` fallback 가능 (단, 응답 신뢰성 검증 필수)
- **rate-limit aware throttle/backoff 명시 필수** — LLM 런타임이 자동으로 rate limit을 지켜준다고 가정 금지 *(v0.3 —Codex)*

### 4.5 6 필드 산출 (research 모드 alias)

| 필드 | research 모드 의미 |
|------|------------------|
| **선택/판정** | Top 3 핵심 논문 + 한 줄 종합 결론 (이 분야의 SOTA가 무엇인가) — **raw API 응답 기반, Codex cutoff 이전 지식 혼입 금지** |
| **근거 (Why)** | 왜 이 3편이 핵심인가 — 인용수·발표처 권위·시점·재현성 (모든 수치는 API 응답 직접 reference) |
| **대안 비교** | 경쟁 접근법 2~3개 + 각 trade-off (예: Transformer vs RNN vs SSM) |
| **표준 인용** | DOI / arXiv ID / Semantic Scholar paperId / OpenAlex Work ID 직접 link + 발표처 (NeurIPS/ICML/CVPR/POPL/SOSP 등) — §11.1 정규식 검증 통과 필수 |
| **적용 조건** | 이 논문(들)의 결과가 유효한 컨텍스트 (데이터 규모/하드웨어/언어/도메인) |
| **신뢰성·재현성 조건** *(research 전용 6번째 필드)* | ① 코드/데이터 공개 여부 (Papers with Code 검색 또는 `unknown`) ② 동료 검토 vs 프리프린트 (`venue` 필드) ③ 재현 시도 보고 존재 ④ 알려진 한계/철회 여부 (OpenAlex `is_retracted` 필드) ⑤ degraded mode인 경우 single-source 한계 명시 |

---

## 5. 외부 소스 통합 — 3-source 전략

### 5.1 소스별 역할 *(v0.5 — 무료 원칙 강제,Codex "credit 모델" 폐기)*

> 🆓 **3 API 모두 완전 무료**. 키는 선택적 무료 옵션 — 없어도 동작 보장.

| 소스 | 역할 | API 엔드포인트 | 비용 / 인증 | 동시성 |
|------|------|--------------|------------|:------:|
| **arXiv** | 최신성 1순위 (프리프린트, publication-day 수준) | `https://export.arxiv.org/api/query` (HTTPS) | **완전 무료, 인증 없음**. ToU: 3초당 1요청, 단일 연결. 동일 query 하루 1회 권장 | **직렬 throttled** |
| **Semantic Scholar** | 권위 1순위 (인용수, TLDR, `influentialCitationCount`) | `https://api.semanticscholar.org/graph/v1/paper/search` + `fields=` 명시 필수 | **완전 무료**. ⚪ 무인증 = shared throttling (느림, 동작은 함). 🟢 무료 API 키 = 1 RPS 보장 (옵션) | 직렬 (key 유무 무관) |
| **OpenAlex** | 메타데이터 보완 (Topics, `is_retracted`, `ids`) | `https://api.openalex.org/works` | **완전 무료** *(v0.5 정정 —Codex "credit 모델" 주장 폐기)*. 🟢 mailto polite pool 무료 옵션 (User-Agent 헤더에 이메일 1회 등록) | 직렬 |

**중요 사실 확인 사항** *(v0.5)*:
-Codex가 v0.3에서 *"OpenAlex API key + credit 모델 사실상 필요"*라고 보고 → **현재까지 공식 문서로 미확인** (Phase 2 사전 게이트 §14.5에서 실측 검증). 검증 통과 시 본 표 유지, 실패(=실제로 유료 전환됨) 시 PLAN v0.6에서 OpenAlex 제외 + 대체 소스 검토
- OpenAlex Concepts deprecated → Topics 사용 (이건 사실, §5.2 매핑 표 참조)
- Semantic Scholar 무인증도 정상 호출 가능 (단지 shared throttling으로 느림)
- 필터 문법: `cited_by_count:>1000` (콜론 사용)
- **사용자에게 키 발급 강요 금지** — 키 없으면 anonymous로 진행, 1줄 소극적 안내만

### 5.2 검색 전략 — 도메인별 매핑 *(v0.3 — OpenAlex Topics로 전환,Codex P1)*

> ⚠️ **OpenAlex Concepts는 deprecated**. 본 PLAN은 **Topics API** 기반으로 매핑한다.
> Topics ID는 **Phase 2 진입 전 사전 검증 필수** (§14.5 게이트)

| 카탈로그 도메인 | arXiv 카테고리 | Semantic Scholar fieldsOfStudy | OpenAlex **Topic** (사전 검증 대상) |
|-----------------|---------------|--------------------------------|------------------------------------|
| Patterns (Software Engineering) | `cs.SE` | "Software Engineering" | Topic: Software Design Patterns *(ID 검증 필요)* |
| Algorithms (CS Theory) | `cs.DS`, `cs.CC` | "Computer Science" | Topic: Algorithm Design and Analysis *(ID 검증 필요)* |
| Languages (Programming) | `cs.PL` | "Programming Languages" | Topic: Programming Languages and Compilers *(ID 검증 필요)* |
| Security | `cs.CR` | "Computer Security and Cryptography" | Topic: Computer Security *(ID 검증 필요)* |
| Principles (SE Theory) | `cs.SE` | "Software Engineering" | Topic: Software Engineering *(ID 검증 필요)* |
| Quality (Testing/QA) | `cs.SE` | "Software Testing" | Topic: Software Testing *(ID 검증 필요)* |
| AI/ML 패턴/알고리즘 | `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV` | "Machine Learning" | Topic: Machine Learning *(ID 검증 필요)* |
| Distributed Systems | `cs.DC` | "Distributed Computing" | Topic: Distributed Computing *(ID 검증 필요)* |
| Database | `cs.DB` | "Database Systems" | Topic: Database Systems *(ID 검증 필요)* |

**사전 검증 절차** (§14.5 — v0.3 수정):
```bash
# Phase 2 진입 차단 게이트 (Topics 기반 — Concepts 사용 금지)
# Step 1: Topic ID 검색
for KEYWORD in "software design patterns" "algorithm design" "programming languages" \
               "computer security" "software engineering" "software testing" \
               "machine learning" "distributed computing" "database systems"; do
  echo "=== ${KEYWORD} ==="
  curl -s "https://api.openalex.org/topics?search=${KEYWORD// /+}&per-page=3" \
    | jq -r '.results[] | "  \(.id) \(.display_name)"'
done

# Step 2: 각 Topic의 영역(field/subfield/domain) 확인
# Step 3: 의도한 도메인과 일치 검증 → references/research/sources.md에 검증 통과 ID 기록
# Step 4: Concept 매핑은 fallback으로만 사용 (deprecated)
```

**필터 문법 정정** *(v0.3 —Codex P3)*:
```
GET /works?filter=cited_by_count:>1000,topics.id:T<ID>  # 콜론(:) 사용
```

> 본 매핑 표는 `references/research/sources.md`에 상세 기술 (검증 통과 후)

### 5.3 중복 제거 알고리즘 *(v0.3 —Codex P1: arXiv DOI 매핑 추가, P2: 임계값 0.90)*

1. **DOI 정규화 일치**: lowercase + `https://doi.org/` prefix 제거 + URL decode → 일치 시 동일 논문
   - 함정: preprint vs published DOI가 다를 수 있음 — 제목 + 저자로 cross-check
2. **arXiv ID 정규화**: `2401.12345v2` → `2401.12345` (version 제거), 동일 시 동일 논문
3. **arXiv DOI ↔ arXiv ID 매핑** *(v0.3 신규)*: `10.48550/arXiv.2401.12345` → arXiv ID `2401.12345`와 **동일 논문으로 병합**
4. **제목 유사도**: normalized title similarity > **0.90** *(v0.3 상향 —Codex 권장, 50쌍 골든 fixture로 P/R 보정, §19.1)* + 첫 저자 last name 일치 → 후보 병합
   - 충돌 시(0.85~0.90 경계) **분리 표시** + 검증 로그에 기록 *(v0.3 —Codex 권장)*
5. **외부 ID 병합**: Semantic Scholar `externalIds` + OpenAlex `ids` 필드의 DOI/arXiv/MAG/PubMed cross-reference로 ID 보강
6. **출처 우선순위**: Semantic Scholar > OpenAlex > arXiv (메타데이터 완성도 기준)
7. **3-source 검증 로그**: 각 논문이 어느 소스에서 발견됐는지 표시 (예: `[arXiv ✓ S2 ✓ OA ✓]` = 3중 검증 통과)

### 5.4 환각 방지 정책 *(v0.3 —Codex P2: weak-evidence 섹션 도입)*

- **Primary matrix (strict)**: DOI / arXiv ID 중 **최소 1개 존재**해야 primary matrix에 포함 (§11.1 정규식 검증)
- **Weak-evidence 섹션** *(v0.3 신규)*: DOI/arXiv ID는 없지만 S2 paperId 또는 OpenAlex Work ID만 있는 항목은 별도 `**Weak Evidence**` 섹션에 **최대 2개**까지 표시 (Top 3 핵심 논문에는 미포함)
  - 사유: 일부 유효한 워크숍 자료/책/표준은 DOI/arXiv 없이도 가치 있음 (Codex P2 발견)
- **인용수는 Semantic Scholar 또는 OpenAlex 응답에 있는 값만 사용** — Codex가 추정 금지
- **저자명은 API 응답 원문 그대로** — 표기 변형 금지
- **발표처(NeurIPS 등)는 API 응답의 `venue` 필드만 사용** — Codex가 추측 금지
- **TLDR / abstract는 항상 존재하지 않음** *(v0.3 —Codex)* — null 가능, fallback 정책 명시
- **카탈로그 매핑 후보는 `catalog-index.json`의 실제 ID 목록과 대조 후에만 인용** — 추정/유추 금지 *(v0.2 추가)*
- **3-source 모두 0건이면 명시적 "검색 결과 없음" 출력 + 검색어 재정제 제안**
- **Codex cutoff 이전 지식 혼입 금지** — "선택/판정" 6필드 작성 시 raw API 응답만 사용 *(v0.2 추가)*
- **재현 보고 출처 정책** *(v0.4 신규 — critic F12)*: 6 필드 "신뢰성·재현성 조건" 작성 시:
  - 1차: Semantic Scholar 응답에 Papers with Code link 포함 → 사용
  - 2차: `https://paperswithcode.com/api/v1/papers/?title=<title>` 검색 (선택적 통합)
  - 3차: 응답 없음 → 명시적 `unknown (no reproduction report found)` 표기. Codex 추정 금지.
- **`is_retracted` / `is_paratext` 등 OpenAlex 메타 필드 활용** *(v0.4)*: 철회 논문은 매트릭스 상단에 ⚠️ 표시 + 신뢰성 필드에 "RETRACTED" 명시

---

## 6. 산출물 포맷 (Output Template)

### 6.1 메인 출력 스켈레톤

```markdown
## Research — <topic|catalog-id|query>

### 1. 검색 쿼리 (Search Queries)
- arXiv: `<쿼리>` (카테고리: `cs.SE`, 연도: 2020-2026)
- Semantic Scholar: `<쿼리>` (field: "Software Engineering")
- OpenAlex: `<쿼리>` (concept: C2522767166 ✓verified)

### 2. 논문 매트릭스 (Top N)

| # | 제목 | 저자 (1st+) | 연도 | 발표처 | 인용수 | 무료PDF | 카탈로그 매핑 | 신뢰도 | 3-source | 관련성 |
|:-:|------|------------|:----:|--------|:-----:|:------:|--------------|:------:|:--------:|:------:|
| 1 | <Title>  | Vaswani et al. (8) | 2017 | NeurIPS | 120,453 | [arXiv](url) | `/algorithm transformer` | HIGH | A✓ S✓ O✓ | ★★★★★ |
| 2 | ... | ... | ... | ... | ... | ... | ... | MED | A✓ S✓ O✗ | ★★★★ |

### 3. 카탈로그 Cross-Reference

| 매핑된 카탈로그 항목 | 매핑 논문 # | 매핑 신뢰도 |
|---------------------|------------|------------|
| `/algorithm transformer` | #1, #3 | HIGH (제목 토큰 + 인용수 ≥ 100) |
| `/pattern attention-mechanism` | #1 | MED (abstract/TLDR 토큰 매치) |
| `/principle deep-learning-fundamentals` | #4 | LOW (S2 fieldsOfStudy 매칭) |

**매핑 신뢰도 정량 기준** *(v0.2 신규 — LLM 주관 판단 금지)*:

| 신뢰도 | 조건 (AND) |
|--------|-----------|
| **HIGH** | 논문 제목에 카탈로그 ID 토큰 1개 이상 포함 AND 인용수 ≥ 100 (또는 ID와 정확히 일치하는 알고리즘/패턴명) |
| **MED** | abstract 또는 Semantic Scholar TLDR에 ID 토큰 1개 이상 포함 (제목에는 없음) |
| **LOW** | S2 `fieldsOfStudy` 또는 OpenAlex `concepts`에 카탈로그 도메인 매칭만 존재 |

※ 위 조건을 만족하지 않는 매핑은 출력 금지 (§11.1 사전 차단 정책)

### 4. 6 필드 산출

**선택/판정**: <Top 3 + 한 줄 결론 — raw API 응답 기반>
**근거 (Why)**: <인용수·발표처·시점 종합 — 수치는 모두 API 응답 직접 reference>
**대안 비교**: A vs B vs C (각 trade-off)
**표준 인용**: DOI / arXiv ID / S2 paperId / OpenAlex Work ID + 발표처 (§11.1 정규식 검증 통과)
**적용 조건**: 데이터 규모/하드웨어/언어/도메인 명시
**신뢰성·재현성 조건**: 코드 공개 / peer review / 재현 보고 / 한계 / 철회 (`is_retracted`) / degraded mode 한계

### 5. 3-source 교차 검증 로그

- 총 검색 결과: arXiv N1건 / S2 N2건 / OpenAlex N3건 → 중복 제거 후 K건
- 3중 검증 통과: M편 (전체 Top N 중)
- 단일 소스 only: P편 (검증 약함 — 인용수 없거나 메타 불완전)
- API 응답 상태: arXiv 200 / S2 200 / OpenAlex 200 (정상 / degraded / 0건 명시)

### 6. Hand-off 후보

- 카탈로그 매핑 신뢰도 HIGH ≥ 3 → 카탈로그 lookup 후속 (`/pattern <id>` 등)
- 코드 구현 요청 동반 → `spawn_agent(agent_type="executor", message="...")`
- 검색어 모호/0건 → `spawn_agent(agent_type="document-specialist", message="...")` (외부 학술 문서 다중 소스 검색)
- 심층 비교 요청 → `spawn_agent(agent_type="analyst", message="...")` 또는 `scientist`

---

※ 본 결과는 외부 API 응답 원문 기반이며, 인용 전 사용자 검증을 권장합니다. PDF 링크 안전성은 사용자 책임입니다.
```

### 6.2 0건 대응 출력

```markdown
## Research — <query>

### 검색 결과 없음

3-source 모두 0건. 다음을 시도해보세요:

1. **검색어 재정제**: 한국어 → 영어 변환, 약어 풀어쓰기, 카탈로그 ID 사용
2. **연도 범위 확장**: `--years 2010-2026`
3. **카탈로그 lookup 먼저**: `/pattern search <키워드>` 또는 `/principle search <키워드>`
4. **document-specialist 에이전트 위임**: 외부 학술 사이트 다중 소스 교차 검증 (Google Scholar 등)

추천 다음 명령:
- `/dev-advisor research "<재정제된 검색어>"`
- `/pattern search <키워드>`
- `spawn_agent(agent_type="document-specialist", message="<query> 학술 논문 5편 정리")`
```

---

## 7. 라이프사이클 보조 라우팅 추가

### 7.1 SKILL.md 라우팅 표 수정 (diff)

```diff
| 보조 라우트 | 범위 | 기본 매핑 |
| `lifecycle` | ... | ... |
| `requirements` | ... | ... |
| `release` | ... | ... |
| `ops` / `sre` | ... | ... |
| `ecosystem/current-docs` | ... | ... |
+ | `evidence` / `research` | 학술 논문, SOTA 추적, 표준 RFC/NIST, 벤치마크 보고, 비교 연구 | `research` 모드 + 카탈로그 cross-ref (단방향) |
```

### 7.2 라우팅 우선순위 표 수정 (diff) + 충돌 해소 규칙 *(v0.2 추가)*

```diff
| 발화 패턴 | 라우팅 | 예 |
| 카탈로그 ID 명시 | 해당 도메인 lookup | ... |
| 코드/모듈/API 입력 동반 | advisor 모드 | ... |
| 의도 동사만 | advisor 모드 | ... |
| QA/QC 키워드 | qa / qc | ... |
| 통합 키워드 | full | ... |
| 병렬 키워드 | swarm | ... |
+ | 학술/연구/논문 키워드 ("논문", "research", "SOTA", "literature", "evidence") | research 모드 | "Transformer 최신 연구" → `research transformer` |
| 둘 다 모호 | 시퀀스 (lookup → 후속 질문) | ... |
```

**research 모드 충돌 해소 규칙** *(v0.2 신규)*:

| 입력 패턴 | 라우팅 | 예 |
|----------|--------|----|
| 학술 키워드 + 카탈로그 ID 명시 | **시퀀스**: 1) lookup → 2) "최신 연구도 보시겠습니까?" → 3) `research <id>` | "transformer 패턴 최신 연구" → `/pattern transformer` → 확인 → `research transformer` |
| 학술 키워드 + 코드/모듈 입력 | **시퀀스**: `<advisor mode> + research` (코드 분석 우선) | "이 API 보안 점검 + 최신 연구" → `security-audit api.go` 후 `research api-security` |
| "최신 연구" / "SOTA" 단독 | `research` 단독 | "transformer SOTA" → `research transformer` |
| 학술 키워드 + 통합 키워드 ("전체 점검 + 최신 연구") | `full` 후 `research` (research는 full에 미포함 — 토큰 한계) | 명시적 시퀀스 |

---

## 8. 변경 파일 상세

### 8.1 `SKILL.md` (수정)

| 섹션 | 변경 |
|------|------|
| 첫 줄 description | "9 advisor 모드" → "**10 advisor 모드** (8 기본 + 2 통합 — research 추가)" |
| 트리거 목록 | `'/dev-advisor research'`, `'논문 찾기'`, `'학술 근거'`, `'literature review'`, `'SOTA'`, `'최신 연구'`, `'근거 논문'` 추가 *(v0.2 확장)* |
| argument-hint | `research` 추가 |
| `9가지 핵심 기능` 표 | `10가지 핵심 기능` (8 기본 + 2 통합)으로 변경 + research 행 추가 |
| `호출 인터페이스 > 2. advisor 모드` 표 | research 행 추가 |
| `9 모드 정의` 표 | 10 모드 정의 표로 + research 행 추가 |
| `라이프사이클 보조 라우팅` 표 | `evidence/research` 행 추가 |
| `라우팅 우선순위` 표 | 학술 키워드 행 + **충돌 해소 규칙** 추가 |
| `full vs swarm 자동 라우팅 보조 규칙` | research는 full/swarm에 포함 X 명시 (독립 모드) |
| `--help` 출력 | research 모드 + 옵션 + 사용 예시 추가 |
| `OMX hand-off` 표 | `document-specialist` + `analyst` + `scientist` 행 추가 (모두 xhigh 역할) |

**Phase 분할** *(v0.2 신규 — F-09 반영)*:
- Phase 2-A: 1차 라우팅 (description/argument-hint/10 모드 표만)
- Phase 2-B: 2차 보조 라우팅 (라이프사이클/우선순위/충돌 해소/--help)
- Phase 2-C: 부가 (handoff/examples)
- 각 별도 commit (사용자 직접 — 작업자 정책 §15)

### 8.2 `references/research/sources.md` (신규)

내용:
- 3 API 엔드포인트 + 요청/응답 스키마 (실제 응답 샘플 포함)
- arXiv 분류 코드 표 (cs.AI, cs.SE, cs.DC 등 30+ 카테고리)
- Semantic Scholar field-of-study 코드 표
- OpenAlex concept ID 표 (**Phase 2 사전 검증 통과한 ID만 기록**)
- Rate limit / polite usage 가이드
- 3-source 비교 매트릭스 (커버리지/메타/인용/속도)
- **버전 명시**: arXiv API v1.0 / S2 graph v1 / OpenAlex v1 (schema 변경 추적용)

### 8.3 `references/research/query-strategies.md` (신규)

내용:
- 도메인별 검색 전략 (CS/AI/Security/SE 등)
- 쿼리 정제 규칙 (한→영 변환, 약어 풀어쓰기, boolean 연산자)
- 중복 제거 알고리즘 의사코드
- **관련성 점수 공식**: `score = log(citations+1) × recency_weight × source_count`
  - `recency_weight = max(0.5, 1 - (current_year - pub_year) * 0.1)` *(v0.2 명시)*
  - `--bias recency` → `recency_weight ** 2` 가중
  - `--bias citation` → `log(citations+1) ** 2` 가중
- 0건 대응 전략 (검색어 fallback 체인)

### 8.4 `references/research/output-format.md` (신규)

내용:
- 메인 출력 스켈레톤 (§6.1)
- 0건 출력 (§6.2)
- 카탈로그 매핑 신뢰도 HIGH/MED/LOW 정량 기준 (§6.1 표)
- 매트릭스 컬럼별 정확한 출처(API 응답의 어느 필드)
- 환각 방지 체크리스트 (§11.1 사전 차단 정책)

### 8.5 `references/research/mapping-algorithm.md` (신규) *(v0.2)*

내용:
- 카탈로그 매핑 알고리즘 구체 명세
- HIGH/MED/LOW 판정 로직 의사코드
- 토큰 매칭 / 인용수 임계값 / fieldsOfStudy 매칭
- false positive 회피 정책

### 8.6 `references/research/fallback.md` (신규) *(v0.2)*

내용 — §17 본문 참조

### 8.7 `references/research/performance.md` (신규) *(v0.2)*

내용 — §18 본문 참조

### 8.8 `references/research/testing.md` (신규) *(v0.2)*

내용 — §19 본문 참조

### 8.9 `references/research/fixtures/` (신규) *(v0.2)*

내용:
- 50 케이스 API mock 응답 (정상/부분장애/0건/스키마변경/한국어)
- 단위 테스트용 (§19.1)

### 8.10 `references/output_templates.md` (수정)

- research 모드 산출 마크다운 스켈레톤 추가 (§6.1 복사)

### 8.11 `references/examples.md` (수정)

- 예시 K (research 정상 — Transformer SOTA 추적)
- 예시 L (research 자유 질문 — "LLM code generation evaluation")
- 예시 M (research 0건 대응)

### 8.12 `references/handoff.md` (수정)

- `document-specialist` / `analyst` / `scientist` hand-off 정식 계약 신설 (모두 xhigh 역할 우선) *(v0.2 — F1 환각 에이전트 교체)*
  - **document-specialist**: research 0건 / 한국어 검색 → 외부 학술 문서 검색
  - **analyst**: 검색 결과 다수의 비교/요약 분석
  - **scientist**: 데이터 분석 성격 (인용수 분포, 시간 추이)

### 8.13 `scripts/verify-references.sh` (수정) *(v0.2 — F3 반영)*

- **11번 블록 확장**: `qa/qc/full/swarm` 외에 `research` 모드 등록 검증 7항목 추가
  - 11-7. `/dev-advisor research` SKILL.md 등록 확인
  - 11-8. research 자연어 트리거 최소 2개 ("논문", "research", "SOTA", "literature review", "학술")
  - 11-9. output_templates.md에 research 모드 스켈레톤 존재 확인
  - 11-10. examples.md에 research 예시(K/L/M) 3개 존재 확인
  - 11-11. handoff.md에 document-specialist/analyst/scientist 항목 존재 확인
  - 11-12. references/research/fixtures/ 디렉토리 + 최소 5 케이스 존재
  - 11-13. OpenAlex Concept ID 사전 검증 로그 존재 (§14.5)
- research 도메인 anchor 검증 (`references/research/*.md` 내부 link 무결성)
- 카운트 검증은 X (research는 동적)

---

## 9. OMX Hand-off 정책 *(v0.2 — F1 + F10 반영)*

| 트리거 | Hand-off 대상 | 모델 | 비고 |
|--------|-------------|------|------|
| 3-source 모두 0건 + 사용자가 재시도 요청 | `document-specialist` 에이전트 | **xhigh** | 외부 학술 문서 다중 소스 검색 (Google Scholar 등) |
| 한국어 논문 명시 요청 | `document-specialist` | **xhigh** | RISS/DBpia/KCI 외부 검색 |
| 카탈로그 매핑 신뢰도 HIGH ≥ 3 + 사용자가 구현 요청 | `executor` | **xhigh** | research 결과를 prompt 컨텍스트로 전달 |
| 심층 비교 분석 요청 ("이 두 논문 비교") | `analyst` 또는 `scientist` | **xhigh** | 분석 성격이므로 xhigh 우선 |
| 카탈로그 매핑 충돌 (한 논문이 여러 카탈로그 ID로 매핑) | `architect` | **xhigh** | 분류·관계 모델링 |
| PR/문서 작성 요청 ("이 논문 요약 README에 넣어") | `writer` | (sonnet 기본) | 문서 작성은 sonnet 허용 |

> **참고**: `document-specialist` / `analyst` / `scientist`는 dev-advisor `references/handoff.md`에 신규 등재 필요 (§8.12) — Phase 4에 task로 포함

---

## 10. 라이선스 / 윤리 / 법적 고려

### 10.1 API 사용 약관 준수 *(v0.5 — 무료 원칙 강제)*

> 🆓 **3 API 모두 완전 무료**. 키는 모두 무료 발급 + 옵션. 키 없이도 동작 보장.

- **arXiv**: **완전 무료, 인증 없음**. ToU: **3초당 1요청, 단일 연결**. 동일 query 하루 1회 이상 호출 금지 — §18.3 in-memory cache(1일 TTL) 적용
- **Semantic Scholar**: **완전 무료**, 학술/비상업.
  - ⚪ 무인증 = shared throttling (느리지만 동작함, default)
  - 🟢 무료 API 키 옵션 — 1 RPS 보장. 런타임 환경변수 `SEMANTIC_SCHOLAR_API_KEY` 있으면 사용, 없으면 anonymous로 진행
  - **사용자에게 키 발급 강요 금지** — 1줄 소극적 안내만
- **OpenAlex**: **완전 무료** *(v0.5 —Codex "credit 모델" 주장 폐기)*.
  - ⚪ anonymous도 정상 호출 가능 (default)
  - 🟢 mailto polite pool 무료 옵션 — `OPENALEX_MAILTO` 환경변수 있으면 User-Agent 헤더에 주입
  - 🟢 무료 API 키 옵션 — `OPENALEX_API_KEY` 있으면 사용
  - ⚠️ Phase 2 사전 게이트(§14.5)에서 "무료 정책 유지 여부" 실측 검증. 검증 실패(실제로 유료 전환됨) 시 PLAN v0.6 재작성
  - **SKILL.md/markdown에 이메일·키 하드코딩 금지**
- **API 키 정책 일반 원칙** *(v0.5)*:
  - 모든 키는 **무료 발급**, **선택적**, **anonymous fallback 강제**
  - 영구 저장 시스템 X
  - 런타임 환경변수 입력만 지원
  - 키 누락 시 anonymous fallback + 응답 상단 1줄 안내 ("anonymous mode — rate limit 적용")
  - **사용자에게 키 발급/유료 결제 요구 메시지 절대 금지**
  - 유료 API/Premium 등급 영원히 out-of-scope

### 10.2 인용 표기

- 모든 논문은 DOI/arXiv ID/S2 paperId/OpenAlex Work ID 중 하나 이상의 식별자로 인용 (§11.1 정규식 검증)
- Codex가 임의로 저자명·연도·인용수·발표처를 생성하는 것 절대 금지 (환각 방지 정책 §5.4 + §11.1)
- **URL 화이트리스트**: `arxiv.org` / `doi.org` / `semanticscholar.org` / `openalex.org` 도메인만 출력. shortener/redirect URL 금지 *(v0.2 — F-11 반영)*
- **Abstract/TLDR 인용 한도**: 1~3문장. 전체 abstract 전재 금지 (fair use) *(v0.2 — F16 반영)*

### 10.3 데이터 보관

- 검색 결과는 1차 구현에서 디스크 저장 X
- **세션 내 in-memory dedup 적용** (§18.3) *(v0.2 — F5 반영)*
- 추후 디스크 캐싱 도입 시 별도 PLAN

---

## 11. 위험 & 완화 (Risk & Mitigation)

| 위험 | 확률 | 영향 | 완화 |
|------|:----:|:----:|------|
| API rate limit 초과 | 중 | 중 | S2 1 RPS는 §18.2 schedule (직렬) + 세션 내 in-memory dedup (§18.3) |
| API 응답 schema 변경 | 저 | 고 | sources.md에 schema 버전 명시 + verify 스크립트로 주기 점검 |
| Codex 환각 (있지도 않은 논문 출력) | 중 | 매우 고 | §5.4 환각 방지 정책 + §11.1 사전 차단 정책 + DOI/ID 정규식 검증 + 3-source 교차 검증 로그 의무 |
| 카탈로그 매핑 오류 (관계없는 패턴에 연결) | 중 | 중 | 매핑 신뢰도 정량 기준 (§6.1) + LLM 주관 판단 금지 |
| 0건 대응 빈도 높음 (한국어 검색어 직접 사용) | 중 | 저 | 한→영 정규화 (§4.4 단계 1) + 0건 fast-fail (§17.3) + document-specialist hand-off |
| 표절/오인용 (사용자가 검색 결과를 검증 없이 인용) | 중 | 중 | §11.1 사전 차단 정책 + 출력 하단 면책 문구 |
| **arXiv HTTPS 미사용 위험** | 저 | 저 | `https://export.arxiv.org` 사용 확인 (HTTPS 강제) *(v0.2)* |
| **S2 익명 RPS limit 100/5min** | 중 | 중 | 옵션 API 키 지원 + 미사용 시 사용자에게 한계 안내 *(v0.2)* |
| **OpenAlex polite pool 이메일 노출 (PII)** | 저 | 중 | 환경변수 옵션 + default 미사용 *(v0.2 — F-07)* |
| **외부 PDF link 안전성** | 중 | 저 | URL 화이트리스트 (§10.2) + PDF link `[PDF]` 라벨만 + 사용자 책임 면책 *(v0.2 — F-11)* |
| **응답 latency > 30s** | 중 | 저 | §18.1 timeout (개별 5s, 총 20s) + partial result fallback (§17.1) *(v0.2)* |
| **OpenAlex Concept ID 환각 (사전 검증 누락)** | 고 | 고 | **§14.5 Pre-flight 게이트** — Phase 2 진입 차단 *(v0.2 — F4)* |
| **3-source 부분 장애 시 응답 불가** | 중 | 중 | §17.1 부분 장애 매트릭스 + degraded mode 배너 *(v0.2 — F-01)* |
| **OpenAlex Concepts deprecated → 잘못된 매핑** | **고** | **고** | **§5.2 Topics 전환** + §14.5 사전 게이트로 Concepts 사용 차단 *(v0.3 —Codex P1)* |
| **arXiv 병렬 호출 시 ToU 위반** | 중 | 고 | §18.2 직렬 throttled 강제 + 동일 쿼리 1일 cache *(v0.3 —Codex P1)* |
| **arXiv DOI `10.48550/arXiv.*` 중복 미병합** | 중 | 중 | §5.3 알고리즘 #3 명시적 매핑 *(v0.3 —Codex P1)* |
| **OpenAlex 정책 변동 (Codex 주장 검증 필요)** | 저 | 중 | Phase 2 사전 게이트(§14.5)에서 실측 호출로 무료 정책 유지 여부 검증. 검증 실패 시 PLAN v0.6 재작성 + 사용자 통보. 평소엔 §10.1 "완전 무료" 가정 유지 *(v0.5 — 사용자 무료 원칙)* |
| **Semantic Scholar TLDR null 가능** | 저 | 저 | §5.4 fallback 정책: TLDR 없으면 abstract 첫 문장 또는 `n/a` *(v0.3 —Codex)* |
| **API key 미주입 시 rate limit hit** | 중 | 중 | 응답 상단 배너로 "anonymous mode — 결과 제한 가능" 안내 + §17.2 circuit breaker *(v0.3 —Codex)* |

### 11.1 사전 차단 정책 (구현 강제) *(v0.2 신규 — F-15)*

Codex가 매트릭스 행 생성 시:

- **Identifier 필수**: 모든 행은 `doi` / `arxiv_id` / `s2_paper_id` / `openalex_work_id` 중 최소 1개 존재
  - 정규식 검증:
    - DOI: `^10\.\d{4,}/`
    - arXiv ID: `^\d{4}\.\d{4,5}(v\d+)?$` 또는 `^[a-z-]+/\d{7}(v\d+)?$`
    - S2 paperId: `^[a-f0-9]{40}$`
    - OpenAlex Work ID: `^W\d{8,}$`
  - 누락 시 행 자동 drop + 검증 로그에 기록
- **메타 필드 직접 reference**: 저자/연도/인용수/발표처는 API 응답 raw dict의 직접 참조. Codex 추론·요약·번역 금지 (raw 그대로 출력)
- **URL 화이트리스트**: §10.2 도메인만 출력
- **카탈로그 매핑**: `catalog-index.json`의 실제 ID 목록과 대조 후에만 인용
- **6 필드 "선택/판정"**: API 응답 외 지식(Codex cutoff 이전) 혼입 금지

---

## 12. 구현 순서 (단계별 체크리스트)

### Phase 1 — 문서 (v0.1 완료, v0.2 개정 완료)
- [x] PLAN-research-mode.md v0.1 초안 작성
- [x] OMX critic + architect + Codex 검토
- [x] PLAN-research-mode.md v0.2 개정 (검토 반영)

### Phase 2 — 사전 검증 (Pre-flight Gate) *(v0.2 신규 — F4)*
- [ ] **OpenAlex Concept ID 8개 사전 검증** (Phase 3 진입 차단 게이트):
  ```bash
  for ID in C2522767166 C33923547 C9417928 C38652104 C2779343474 C119857082 C124101348 C58168014; do
    echo -n "${ID}: "
    curl -s "https://api.openalex.org/concepts/${ID}" | jq -r '.display_name // "FAIL"'
  done
  ```
- [ ] 의도한 분야와 display_name 일치 검증 → `references/research/sources.md`에 기록
- [ ] 불일치 시 `concept.search?q=<keyword>` fallback으로 재선정
- [ ] **`catalog-index.json` modes 필드 존재 여부 확인** — 있으면 schema 변경 task 추가, 없으면 §2.2 검증 통과
- [ ] **`analyst` / `scientist` 에이전트 존재 여부 확인** — `ls ~/.codex/agents/` + OMX marketplace listing

### Phase 3 — `references/research/` 신규 작성 (Phase 2 통과 후)
- [ ] `references/research/sources.md` — 3 API 엔드포인트 + 응답 스키마 + 검증된 카테고리 매핑
- [ ] `references/research/query-strategies.md` — 쿼리 정제 + 중복 제거 + 관련성 점수 + `--bias` 옵션
- [ ] `references/research/output-format.md` — 산출물 스켈레톤 + 매핑 신뢰도 정량 기준
- [ ] `references/research/mapping-algorithm.md` *(v0.2)* — HIGH/MED/LOW 판정 알고리즘
- [ ] `references/research/fallback.md` *(v0.2)* — §17 본문 이관
- [ ] `references/research/performance.md` *(v0.2)* — §18 본문 이관
- [ ] `references/research/testing.md` *(v0.2)* — §19 본문 이관
- [ ] `references/research/fixtures/` — 50 케이스 mock fixture

### Phase 4 — SKILL.md 수정 (Phase 분할 — F-09)
- [ ] **Phase 4-A**: description / argument-hint / 트리거 목록 / 10 모드 정의 표
- [ ] **Phase 4-B**: 라이프사이클 보조 라우팅 / 라우팅 우선순위 / 충돌 해소 규칙 / `--help`
- [ ] **Phase 4-C**: OMX hand-off 표 (document-specialist + analyst + scientist)

### Phase 5 — 부가 자산 수정
- [ ] `references/output_templates.md` — research 모드 스켈레톤
- [ ] `references/examples.md` — 예시 K/L/M (research 호출 3 시나리오)
- [ ] `references/handoff.md` — `document-specialist` + `analyst` + `scientist` hand-off 계약 신설 (xhigh 역할 우선)

### Phase 6 — 검증
- [ ] `scripts/verify-references.sh` 11번 블록 확장 (7항목 추가)
- [ ] `bash scripts/verify-references.sh` 실행 → 무결성 확인
- [ ] `python3 scripts/generate-catalog-index.py --check` — research는 catalog-index.json에 포함 X 확인
- [ ] §19 테스트 매트릭스 단위/통합/회귀 테스트 실행
- [ ] 실제 호출 테스트: `/dev-advisor research transformer` → 매트릭스 출력 확인
- [ ] 부분 장애 시뮬레이션 (mock fixture 사용) → degraded mode 배너 확인

### Phase 7 — 출시
- [ ] README / DOCUMENTATION_INDEX 등 외부 문서에 research 모드 추가 안내
- [ ] git commit (작업자 직접 — 메인 워킹트리 git 정책)

---

## 13. 호환성 & 마이그레이션 *(v0.2 — F-12 반영)*

- **하위 호환**: 기존 9 모드 + 6 카탈로그 호출은 100% 변경 없음
- **버전 표시**: SKILL.md description에 `(research mode added — v2.0)` 명시
- **사용자 학습 곡선**: 새 모드 1개 + 보조 라우팅 1개 + 자연어 트리거로 학습 부담 최소

### 13.1 미래 PLAN 호환 경로 *(v0.2 신규)*

다음 후속 PLAN 도입 시 본 PLAN 구조가 깨지지 않는다는 명시적 보증:

| 후속 PLAN | 호환 경로 |
|----------|---------|
| `papers/` 정적 카탈로그 (옵션 A) | ① `catalog-index.json`의 `domain` enum에 'papers' 추가 ② `items[].domain` 확장 ③ `lookup-catalog.py` `DOMAIN_ALIASES`에 'paper' 추가만 필요 — 기존 6 도메인 무영향 |
| 한국어 논문 검색 (RISS/DBpia/KCI) | `research` 모드 자체는 변경 없음. `sources.md`에 한국어 소스 추가 + 한국어 정규화 정책(§4.4 단계 1) 확장 |
| 양방향 cross-reference | research 결과의 카탈로그 매핑 표를 markdown 스니펫 형식으로 출력 → 추후 lookup 출력에 "See also" 섹션으로 통합 가능 |
| 디스크 영구 캐싱 | §18.3 in-memory를 디스크 캐시로 교체. API 호출 패턴은 동일 |

### 13.2 아키텍처 결정 — 통합 모드 vs 별도 스킬 *(v0.3 —Codex 대안 #2 검토)*

Codex가 **별도 `/research` 스킬 분리**를 권장. 본 PLAN의 현재 결정과 트레이드오프 명시:

| 옵션 | 장점 | 단점 | 채택 |
|------|------|------|:----:|
| **옵션 A (현행)**: `/dev-advisor research` 10번째 모드 | UX 단순 (단일 진입점), 카탈로그 cross-ref 자연스러움, 사용자 학습 부담 최소 | dev-advisor 비대화, 정적 카탈로그(오프라인 markdown)와 동적 API 클라이언트(외부 HTTP) 책임 혼합, API 정책 변경 시 dev-advisor 전체 영향 | **현행 유지** (v0.3 시점) |
| **옵션 B (Codex 권장)**: 별도 `/research` 스킬 분리 | 구현 경계 깨끗, API 정책 변경 대응 용이, dev-advisor는 hand-off만 | 사용자가 모드 1개 추가 학습, cross-ref 명시적 hand-off 필요 | **검토 후보** (사용자 결정 대기) |

**결정 사유 (v0.3 시점에 옵션 A 유지)**:
- 사용자가 v0.1 PLAN 시점에 "dev-advisor에 추가"를 명시적으로 결정
- 정적/동적 책임 혼합 위험은 `references/research/` 하위 디렉토리 격리로 완화
- API 정책 변경 시 영향 범위는 `references/research/sources.md` + §5.1 두 곳에 집중 (큰 부담 아님)
- 카탈로그 cross-ref 활용성이 옵션 B에서는 hand-off overhead로 손실

**옵션 B로 전환할 조건** (트리거):
- API 정책 변경이 1년 내 3회 이상 발생 (실측 데이터 기반 재결정)
- dev-advisor SKILL.md가 100KB 초과 (현재 43KB)
- research 외 추가 동적 모드(예: `web-fetch`, `news`) 신설 필요

### 13.3 `full` / `swarm` 통합 모드와 research의 관계 *(v0.4 — architect F-13)*

**결정**: research 모드는 **`full` / `swarm`에 미포함** (독립 모드로 유지).

**사유 (트레이드오프 명시)**:

| 포함 시 (대안) | 미포함 (현행) |
|---------------|--------------|
| ✅ "전체 점검"에 학술 근거 자동 포함 | ✅ 토큰 한계 회피 (full은 7 모드 직렬 압축, research 추가 시 8 × 1만~2만 = 8만~16만 토큰) |
| ✅ 한 번의 호출로 완성 보고 | ✅ swarm 7 서브에이전트에 추가 시 병렬 8명 = reviewer 부담 증가 |
| ❌ research API 의존성이 full 전체에 전파 (외부 API 장애 → full 실패) | ✅ 외부 API 장애가 다른 7 모드에 영향 없음 |
| ❌ 정적/동적 책임 혼합 (§13.2 동일 문제) | ✅ 책임 분리 명확 |

**사용자가 학술 근거를 통합 보고에 원할 때 시퀀스** (§7.2 충돌 해소 규칙):
```
1. /dev-advisor full <module>        # 7 모드 통합 보고
2. /dev-advisor research <topic>     # 별도 학술 근거
3. 사용자가 두 결과를 종합
```

**옵션 — `full --with-research` 플래그 도입 후보** *(미래 PLAN)*: 사용자 명시 요청 시에만 research 통합. 디폴트는 미포함.

### 13.4 Fallback 체인 *(v0.5 — 무료 원칙 강제, 상용 MCP 제거)*

`WebFetch` 도구가 사용 불가하거나 응답 신뢰성이 낮은 환경에서의 fallback.

**Fallback 체인** *(v0.5 — 3-tier로 축소, 상용 MCP 제거)*:
```
1차: WebFetch (3 API 직접 호출 — §4.4.1) — 🆓 완전 무료
  ↓ 실패 (도구 미지원 / TLS / rate limit hit)
2차: Bash + curl (응답 신뢰성 사용자 검증 필수) — 🆓 무료
  ↓ 실패 (네트워크 차단 등)
3차: `document-specialist` 에이전트 위임 (xhigh) — 🆓 OMX 내장
```

**상용 MCP는 default fallback에서 제거** *(v0.5)*:
- `mcp__exa__*` (Exa AI) = **상용 유료 API** (사용자 plan에 따라 quota 소진)
- 무료 보장 X이므로 **사용자 명시 동의 시에만** 사용 (default OFF)
- 향후 무료 학술 MCP 등장 시 본 정책 재검토 (예: arXiv MCP, OpenAlex MCP)

**상용 MCP 사용 시 (옵션 — 사용자 명시 동의 필수)**:
- 환경변수 `DEV_ADVISOR_ALLOW_PAID_MCP=true` 설정 또는 `--allow-paid-mcp` CLI 플래그
- 출력 상단에 ⚠️ 배너: "상용 MCP 사용 중 — 사용자 quota 소진 가능"
- MCP 응답을 raw API 응답과 동등하게 취급 금지 — 출처 신뢰도 LOW로 표시
- §11.1 사전 차단 정책으로 fallback 결과도 정규식 검증

---

## 14. 성공 기준 (Acceptance Criteria)

이 PLAN이 구현되었다고 인정되는 조건:

### 14.1 기능 동작
- `/dev-advisor research transformer` 호출 → 매트릭스 8행 이상 출력
- "Transformer 최신 연구" (자연어) → research 모드 자동 라우팅
- 3-source 교차 검증 로그가 출력에 포함
- 충돌 발화 ("SRP에 대한 최신 연구") → lookup → research 시퀀스 동작

### 14.2 품질
- **환각 0건** = 매트릭스 모든 행에 DOI/arXiv ID/S2 paperId/OpenAlex Work ID 중 최소 1개 식별자 존재 (정규식 검증 통과 — §11.1) *(v0.2 정량화)*
- 카탈로그 매핑 신뢰도 정량 기준 (§6.1) 준수 — LLM 주관 판단 없음
- 6 필드 산출 완성도 100%

### 14.3 검증 통과
- `bash scripts/verify-references.sh` 모두 통과 (11번 블록 7항목 추가 포함)
- 기존 9 모드 호출 회귀 0건
- 기존 6 카탈로그 lookup 회귀 0건
- §19 테스트 매트릭스 단위/통합/회귀 통과

### 14.4 성능 *(v0.2 신규 — F-02)*
- p50 응답 시간 < 8s
- p95 응답 시간 < 15s
- 개별 API timeout 5s 준수
- 부분 장애 시 partial result 출력 (15s 이내)

### 14.5 사전 게이트 (Pre-flight Gate) *(v0.5 — 무료 정책 실측 검증 추가)*
- Phase 2 진입 전 다음 모두 통과 의무화:
  - [ ] **🆓 무료 정책 실측 검증 (Phase 3 진입 차단 — 가장 중요)** *(v0.5 신규 — 사용자 무료 원칙)*:
    ```bash
    # 키 없이 3 API 호출 가능 검증 (anonymous 동작 보장)
    echo "=== arXiv (always free, no auth) ==="
    curl -s "https://export.arxiv.org/api/query?search_query=ti:transformer&max_results=1" \
      | grep -q "<entry>" && echo "OK" || echo "FAIL"

    echo "=== Semantic Scholar (anonymous) ==="
    curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=transformer&limit=1&fields=title" \
      | jq -e '.data[0].title' > /dev/null && echo "OK" || echo "FAIL"

    echo "=== OpenAlex (anonymous, no mailto) ==="
    curl -s "https://api.openalex.org/works?search=transformer&per-page=1" \
      | jq -e '.results[0].id' > /dev/null && echo "OK" || echo "FAIL"
    ```
    - **3 API 모두 키 없이 200 응답 → 무료 정책 유지 확인 → PLAN 그대로 진행**
    - **하나라도 401/402/유료 전환 → 즉시 PLAN v0.6 재작성 + 사용자 통보** (해당 API 제외 또는 대체 소스 검토)
    - **Codex의 "OpenAlex credit 모델" 주장이 사실로 확인되면** → OpenAlex 무료 정책 폐기 시점까지 본 PLAN 진행 보류
  - [ ] **OpenAlex Topics ID 9개 검증** (의도한 도메인과 일치, **Concepts 사용 금지**)
        — §5.2 검증 스크립트로 Topic display_name 일치 확인 → `references/research/sources.md`에 검증 통과 ID 기록
  - [ ] **arXiv ToU 준수 확인** — 3초당 1요청/단일 연결 schedule이 §18.2에 구현 가능 명시
  - [ ] **anonymous fallback 정상 작동** — `SEMANTIC_SCHOLAR_API_KEY`, `OPENALEX_API_KEY`, `OPENALEX_MAILTO` 누락 시에도 정상 응답
  - [ ] `catalog-index.json` modes 필드 존재 여부 확인
  - [ ] `analyst` / `scientist` / `document-specialist` 에이전트 실제 존재 확인 (없으면 handoff.md에 신규 정의)
- 통과 실패 시 Phase 3 차단

### 14.6 문서
- SKILL.md `--help` 출력에 research 명시
- `references/research/` 7+ 파일 작성 (sources/query-strategies/output-format/mapping-algorithm/fallback/performance/testing/fixtures)
- 예시 3개 (K/L/M) 작성
- handoff.md에 document-specialist/analyst/scientist 신규 항목

---

## 15. 참고

- 원본 분석 세션: 2026-05-28 zime + Codex GPT-5
- v0.2 검토: OMX critic + architect (2026-05-28) + Codex rescue (보강 예정)
- 검토 후보 OMX 에이전트: `architect` (구조 설계) + `code-reviewer` (PR 리뷰) + `verifier` (Phase 6)
- 다음 세션 진입점: 이 파일을 읽고 Phase 2 사전 게이트부터 진행

---

## 16. 변경 이력

| 일자 | 버전 | 변경 |
|------|------|------|
| 2026-05-28 | 0.1 | 초안 작성 (zime + Codex) — 사용자 결정 사항: 설계 문서만 / arXiv+S2+OpenAlex / research 단방향 cross-ref |
| 2026-05-28 | 0.2 | **OMX critic + architect 검토 반영** — P1 4건 / HIGH 3건 / MED 5건 패치. 주요 변경: ① `search-specialist` 환각 에이전트 교체(9곳) → `document-specialist`+`analyst`+`scientist` ② §4.4.1 HTTP 도구 매핑(`WebFetch`) 신설 ③ §17 Graceful Degradation 신설 ④ §18 성능·동시성 모델 신설 ⑤ §19 테스트 매트릭스 신설 ⑥ §11.1 사전 차단 정책 신설 ⑦ §14.5 Pre-flight 게이트 신설 ⑧ 라우팅 충돌 해소 규칙(§7.2) ⑨ 매핑 신뢰도 정량 기준(§6.1) ⑩ 한국어 정규화 (§4.4 단계 1) ⑪ API 보안 위험 5행 추가(§11) ⑫ Phase 2/3/4 분할 강화(§12) ⑬ 미래 PLAN 호환 경로(§13.1) ⑭ 성능 ACC(§14.4) + 사전 게이트(§14.5) 추가 ⑮Codex 결과 도착 시 v0.3 보강 예정 |
| 2026-05-28 | 0.3 | **Codex rescue 검토 반영** (Risk Score 6/10 → 3/10 목표) —Codex P1 4건 / P2 3건 / P3 1건 + 아키텍처 결정 1건 패치. 주요 변경: ① **OpenAlex Concepts deprecated → Topics 전환** (§5.2 매핑 표 전면 재설계, §14.5 사전 게이트 Topics ID 검증으로 변경) ② **OpenAlex 2026 API key + credit 모델** 명시 (§5.1 + §10.1 환경변수 정책) ③ **arXiv ToU 준수** — 병렬 → 직렬 throttled (3초당 1요청, §4.4.1 + §18.2) ④ **arXiv DOI 매핑** (§5.3 알고리즘 #3 신규 — `10.48550/arXiv.*` ↔ arXiv ID 병합) ⑤ **제목 유사도 임계값 0.85 → 0.90** + 경계 분리 표시 (§5.3) ⑥ **Weak-evidence 섹션 도입** (§5.4 — DOI/arXiv 없어도 S2/OA ID 있으면 별도 섹션 최대 2개) ⑦ Semantic Scholar 무인증 "shared throttling" 표현 정정 (§5.1) ⑧ OpenAlex 필터 문법 정정 (`cited_by_count:>1000`) ⑨ API 키 환경변수 정책: `SEMANTIC_SCHOLAR_API_KEY` / `OPENALEX_API_KEY` / `OPENALEX_MAILTO` (§1.2 + §10.1, 영구 저장 X) ⑩ §13.2 아키텍처 결정 — 통합 모드 vs 별도 스킬 트레이드오프 명시 (현행 옵션 A 유지, 옵션 B 전환 조건 제시) ⑪ §11 위험 표 7행 추가 (Concepts deprecated, ToU 위반, DOI 미병합, anonymous fallback 한계, TLDR null 등) ⑫ §18.3 arXiv 1일 TTL cache + 재호출 회피 로그 ⑬ rate-limit aware throttle/backoff 명시 (LLM 자동 회피 가정 금지) |
| 2026-05-28 | 0.4 | **미반영 권고안 추가 흡수 (사용자 confirm 후 옵션 A 통합 유지)** — 5건 신규 패치. 주요 변경: ① **§13.3 신설** — `full`/`swarm`에 research 미포함 결정 + 트레이드오프 명시 + `--with-research` 미래 플래그 후보 (architect F-13) ② **§13.4 신설** — MCP 위임 fallback 4-tier 체인 (`WebFetch` → `curl` → MCP → `document-specialist`,Codex 대안 #4 흡수) ③ **§5.4 보강** — Papers with Code 통합 정책 (재현 보고 출처 자동화, critic F12) + `is_retracted`/`is_paratext` 활용 ④ **§19.5 신설** — 환각 회귀 테스트 자동화 (HR-01~HR-10 자동 검증 + Golden Fixture 50쌍 + CI 통합 옵션, critic F15 + architect F-10) ⑤ 첫 줄에 사용자 confirm 사항 명시 (옵션 A 통합 유지) |
| 2026-05-28 | 0.5 | **🆓 사용자 무료 원칙 피드백 반영 (절대 원칙 강제)** — 사용자 zime 피드백 "API 키 입력 = 유료 사용 의미 아닌가?" 정정. 6건 패치: ① **§1.2 비목표 강화** — "유료 API 영원히 X" + "키 발급 요구 메시지 출력 X" + "상용 MCP fallback X" 명시 ② **§5.1 소스별 역할 표 전면 정정** — 3 API 모두 "완전 무료" 명시, "credit 모델" 표현 폐기, 키는 무료 옵션으로 통일 ③ **§10.1 API 약관 준수 정정** —Codex "OpenAlex credit 모델" 주장 폐기, anonymous fallback 강제, 사용자에게 키 발급 강요 금지 ④ **§11 위험 표 정정** — "OpenAlex 무료 무제한 outdated"를 "정책 변동 검증 필요"(저/중)로 다운그레이드 ⑤ **§13.4 Fallback 체인 축소** — 4-tier → 3-tier (상용 Exa MCP 제거, default OFF, 사용자 명시 동의 시에만) ⑥ **§14.5 사전 게이트 강화** — "무료 정책 실측 검증" 최우선 항목 추가 (3 API 키 없이 200 응답 확인 의무, 실패 시 v0.6 재작성). ⑦ 글로벌 메모리 `feedback_free_api_only_strict.md` 생성 — 향후 모든 PLAN에 적용 |

---

## 17. 폴백 / Graceful Degradation 전략 *(v0.2 신규 — F-01 / F-14)*

### 17.1 부분 장애 매트릭스

| 응답 상태 | 동작 | 출력 |
|----------|------|------|
| 3-of-3 정상 | 정상 매트릭스 + 3-source 검증 로그 | 매트릭스 + `[arXiv ✓ S2 ✓ OA ✓]` |
| 2-of-3 정상 (S2 또는 OA 실패) | 정상 매트릭스 + 누락 source 명시 | 상단 `⚠️ degraded mode: <source> unavailable` 배너 + 인용수는 가용 source만 |
| 1-of-3 정상 (arXiv only 등) | 단일 source 매트릭스 + 신뢰성 LOW 마크 | 상단 `⚠️⚠️ severe degradation: only <source> responding` 배너 + 6 필드 중 "신뢰성·재현성 조건"에 single-source 한계 명시 |
| 0-of-3 정상 | §6.2 0건 대응 출력 (검색어 재정제 제안) | 검색 결과 없음 + document-specialist hand-off |

### 17.2 Circuit Breaker

- 동일 source 5분 내 실패 ≥ 3회 → 30분 skip (해당 source 자동 제외)
- skip 상태에서도 사용자에게 명시 (출력 하단 footnote)

### 17.3 Fast-Fail 규칙

- 첫 응답 source가 200 + 0건 → 다른 2개는 timeout 절반(2.5s)으로 단축 polling
- 모두 0건 확정 시 검색어 자동 정제 1회 재시도 (한→영 변환, 약어 풀어쓰기) → 그래도 0건이면 §6.2

> 상세 구현 가이드: `references/research/fallback.md`

---

## 18. 성능 목표 / 동시성 모델 *(v0.2 신규 — F-02)*

### 18.1 Latency 목표

| 메트릭 | 목표 | 비고 |
|--------|------|------|
| p50 응답 시간 | < 8s | 3-of-3 정상 + 중복 제거 + 매트릭스 생성 |
| p95 응답 시간 | < 15s | S2 직렬 + fallback 1회 포함 |
| 개별 API timeout | 5s | arXiv / S2 / OpenAlex 동일 |
| 총 timeout | 20s | 초과 시 partial result 출력 |

### 18.2 동시성 Schedule *(v0.3 —Codex P1: rate-limit aware, arXiv ToU)*

- **arXiv**: **직렬 throttled** (ToU — 3초당 1요청, 단일 연결). 동일 쿼리 하루 1회 (§18.3 cache).
- **Semantic Scholar**: 직렬 — key 사용 시 1 RPS 이상, 무인증은 shared throttling (보장 없음, exponential backoff 필수)
- **OpenAlex**: 직렬 — 🆓 완전 무료. mailto 헤더(무료 옵션) 시 polite pool priority queue. anonymous도 정상 동작 *(v0.5 정정)*
- **API 간 병렬은 허용**: arXiv 1건 + OpenAlex 1건은 도메인이 다르므로 단일 어시스턴트 턴에서 동시 호출 가능
- **동일 API 내 다중 쿼리는 throttled**: 예 arXiv 2개 쿼리 → 3초 간격 직렬
- **Exponential backoff**: 429/503 응답 시 1s → 2s → 4s 재시도 (최대 3회)
- **Total**: 정상 케이스 arXiv 5s + OA 5s (병렬) + S2 5s (직렬) = max 10s (이전 v0.2 추정과 동일하나 schedule 구조 변경)

### 18.3 캐싱 정책 (1차 구현) *(v0.3 —Codex: arXiv ToU 준수)*

- **arXiv: 동일 쿼리 1일 TTL in-memory cache** (ToU 준수 — 동일 query 하루 1회 권장)
- **S2/OpenAlex: 세션 내 in-memory dedup** — 검색어 normalized → 응답 5분 TTL
- 동일 어시스턴트 턴/세션에서 동일 쿼리·옵션 조합 재호출 금지
- **재호출 회피 로그**: 캐시 hit 시 사용자에게 명시 ("cached — last fetched X minutes ago")
- 디스크 저장 X (§10.3 정합)
- 추후 영구 캐시 도입 시 별도 PLAN

> 상세 구현 가이드: `references/research/performance.md`

---

## 19. 테스트 / 검증 매트릭스 *(v0.2 신규 — F-03)*

### 19.1 단위 테스트

| # | 케이스 | Assertion |
|:-:|--------|-----------|
| U-01 | DOI 누락 행 입력 | drop + 검증 로그 기록 |
| U-02 | Levenshtein 0.85 임계 (50쌍 골든) | precision ≥ 0.9, recall ≥ 0.85 |
| U-03 | 매핑 신뢰도 HIGH/MED/LOW 5×3 골든 | 알고리즘 출력 == 골든 |
| U-04 | URL 화이트리스트 위반 입력 | 행 drop |
| U-05 | recency_weight 함수 boundary (0년/5년/10년/20년) | 명세된 값 |
| U-06 | OpenAlex Concept ID 사전 검증 누락 시 | Phase 2 차단 |
| U-07 | 식별자 정규식 검증 (DOI/arXiv/S2/OA) | 정규식 통과 |

### 19.2 통합 테스트 (API mock fixture)

- `references/research/fixtures/` — 50 케이스 mock 응답
  - 정상 케이스: 15
  - 부분 장애 (1-of-3, 2-of-3): 12
  - 0건: 5
  - 스키마 변경 (필드 누락): 8
  - 한국어 검색어: 5
  - 라우팅 충돌: 5
- mock 기반으로 `/dev-advisor research <topic>` 실행 → 매트릭스 골든 비교

### 19.3 회귀 테스트

- 기존 9 모드 호출 회귀 0건 (verify-references.sh + 명시적 smoke test)
- 6 카탈로그 lookup 회귀 0건
- SKILL.md 변경 후 `python3 scripts/generate-catalog-index.py --check` PASS
- catalog-index.json schema 변경 없음 확인

### 19.4 `verify-references.sh` 확장 (§8.13 참조)

- 11번 블록에 research 모드 등록 검증 7항목 추가 (11-7 ~ 11-13)
- `references/research/*.md` anchor 무결성 검증
- `references/research/fixtures/` 디렉토리 + 최소 5 케이스 존재 확인
- OpenAlex Topics ID 사전 검증 로그 존재 확인 *(v0.3 — Concepts 아님)*

### 19.5 환각 회귀 테스트 자동화 *(v0.4 신규 — critic F15 + architect F-10)*

**목표**: PLAN §14.2 "환각 0건" 기준을 회귀로 강제. 정성 평가가 아니라 자동 검증 가능한 hook으로 변환.

**자동 검증 항목**:

| # | 검증 | 도구 | 트리거 |
|:-:|------|------|--------|
| HR-01 | 매트릭스 모든 행에 식별자 1개+ (DOI/arXiv ID/S2 paperId/OpenAlex Work ID) | 정규식 (§11.1) | research 응답 생성 후 자동 |
| HR-02 | 식별자 정규식 일치 (`^10\.\d{4,}/`, `^\d{4}\.\d{4,5}(v\d+)?$`, `^[a-f0-9]{40}$`, `^W\d{8,}$`) | regex | 위와 동일 |
| HR-03 | URL 화이트리스트 (§10.2) 위반 0건 | 도메인 매칭 | 위와 동일 |
| HR-04 | 인용수 컬럼이 API 응답 raw value와 일치 (Codex 추정 X) | response trace | mock fixture 50쌍 |
| HR-05 | 저자명이 API 응답 원문 그대로 | string match | mock fixture |
| HR-06 | venue 필드가 API 응답 `venue`/`publicationVenue.name` 직접 reference | string match | mock fixture |
| HR-07 | "선택/판정" 6필드에 cutoff 이전 지식 혼입 없음 (Codex pre-training 표지 검증) | LLM judge 또는 휴리스틱 | sample 20% |
| HR-08 | 카탈로그 매핑 ID가 `catalog-index.json` 실제 ID 목록과 일치 | JSON lookup | 매핑 행마다 |
| HR-09 | weak-evidence 섹션 항목 수 ≤ 2 | 카운트 | 위와 동일 |
| HR-10 | `is_retracted: true` 논문은 ⚠️ 표시 + RETRACTED 명시 | flag check | mock fixture 5개 |

**Golden Fixture 50쌍** (`references/research/fixtures/`):
- 정상 케이스 15: 식별자 완비
- 식별자 누락 5: HR-01 drop 검증
- URL violation 5: HR-03 drop 검증
- 인용수 0인 경우 5: HR-04 null handling 검증
- 한국어 검색어 5: 정규화 후 매트릭스 검증
- 철회 논문 5: HR-10 ⚠️ 표시 검증
- 부분 장애 10: §17 graceful degradation 검증

**CI 통합 옵션** (선택, 미래 PLAN):
- `bash scripts/verify-references.sh --check research-hallucination` 명령
- mock fixture로 research 모드를 dry-run → HR-01~HR-10 자동 검증

> 상세 구현 가이드: `references/research/testing.md`
