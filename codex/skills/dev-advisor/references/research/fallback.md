# Fallback & Graceful Degradation — research 모드

> **출처**: PLAN-research-mode.md v0.5 §17 (Graceful Degradation) + §13.4 (3-tier Fallback 체인)
> **적용 범위**: `/dev-advisor research` 모드 전용. `full` / `swarm` 등 다른 7 모드에는 외부 API 의존성 없음 (§13.3)
> **무료 원칙**: 모든 fallback 경로는 완전 무료. 상용 MCP는 default OFF (사용자 명시 동의 필요).

---

## 1. 개요

`research` 모드는 3종의 외부 무료 API (arXiv / Semantic Scholar / OpenAlex) 에 의존한다.
이 문서는 그 의존성에서 발생하는 모든 장애 유형에 대해 **결과를 완전히 버리지 않고 가능한 최대의 정보를 사용자에게 전달**하는 fault tolerance 전략을 정의한다.

**핵심 원칙**:
1. 부분 장애는 출력 품질을 낮춰서라도 결과를 돌려준다 (silent failure 금지).
2. 장애 상태는 반드시 사용자에게 명시한다 (숨김 금지).
3. 모든 fallback 경로는 🆓 완전 무료여야 한다 (상용 MCP = default OFF).
4. 0건 확정 시에만 검색어 자동 재정제 1회 시도 후 `document-specialist` hand-off.

---

## 2. 부분 장애 매트릭스 (§17.1)

3개 소스 중 몇 개가 응답하느냐에 따라 동작과 출력이 달라진다.

| 응답 상태 | 동작 | 출력 |
|----------|------|------|
| **3-of-3 정상** | 정상 매트릭스 + 3-source 교차 검증 로그 생성 | 매트릭스 + `[arXiv ✓ S2 ✓ OA ✓]` |
| **2-of-3 정상** (S2 또는 OA 실패) | 정상 매트릭스 출력 + 누락 source 명시 | 출력 상단 `⚠️ degraded mode: <source> unavailable` 배너 + 인용수 컬럼은 가용 source 값만 표시 (source 출처 명시) |
| **1-of-3 정상** (arXiv only 등) | 단일 source 매트릭스 + 신뢰성 LOW 마크 전체 적용 | 출력 상단 `⚠️⚠️ severe degradation: only <source> responding` 배너 + 6 필드 중 "신뢰성·재현성 조건" 필드에 single-source 한계 명시 |
| **0-of-3 정상** | output-format.md §6.2 0건 대응 출력 + 검색어 재정제 제안 | 검색 결과 없음 출력 + `document-specialist` hand-off 안내 |

### 2.1 배너 출력 형식

**2-of-3 정상 배너**:
```
> ⚠️ degraded mode: Semantic Scholar unavailable (503 Service Unavailable)
> 인용수는 OpenAlex 값만 표시됩니다. 결과 신뢰도가 일부 낮을 수 있습니다.
```

**1-of-3 정상 배너**:
```
> ⚠️⚠️ severe degradation: only arXiv responding
> Semantic Scholar / OpenAlex 모두 응답 없음. 인용수·메타데이터 없이 제목/저자/연도만 표시됩니다.
> 신뢰성·재현성 조건 필드: single-source 한계 — 동료검토 여부·인용수·철회 여부 확인 불가.
```

### 2.2 인용수 컬럼 처리 (degraded mode)

| 가용 source | 인용수 표시 |
|------------|------------|
| S2 + OA 모두 가용 | S2 `citationCount` 우선, OA `cited_by_count` 보조 (일치 시 단일 표시) |
| S2만 가용 | S2 `citationCount` (출처: S2) |
| OA만 가용 | OA `cited_by_count` (출처: OA) |
| 인용수 source 없음 | `n/a (no citation data)` — Codex 추정 절대 금지 |

---

## 3. Circuit Breaker (§17.2)

동일 source에서 단시간 내 반복 실패가 발생하면 해당 source를 일정 시간 자동 제외한다.

### 3.1 발동 조건

- **동일 source에서 5분 이내 실패 ≥ 3회** → 해당 source 30분 skip (자동 제외)
- "실패"의 정의: `status 5xx` / `timeout (5s 초과)` / `TLS 오류` / `연결 거부`
- 429 (Too Many Requests)는 Circuit Breaker 대신 Exponential Backoff로 처리 (§5 참조)

### 3.2 skip 상태 사용자 명시

skip 상태에서 research를 호출하면 출력 하단에 footnote를 붙인다:

```
---
footnote: Semantic Scholar circuit breaker 발동 중 (5분 내 3회 실패 — 30분 skip, 만료 시각: HH:MM KST)
결과는 arXiv + OpenAlex 2-source 기반입니다.
```

### 3.3 자동 복귀

- skip 만료(30분 경과) 후 다음 research 호출 시 해당 source를 자동으로 재포함
- 사용자가 별도 명령을 실행하거나 세션을 재시작할 필요 없음
- 자동 복귀 후 첫 호출에서 해당 source 응답 성공 시 "circuit breaker 해제" 로그 출력 (옵션)

### 3.4 Circuit Breaker 상태 테이블 (세션 내 in-memory)

```
source       | fail_count | last_fail_ts | skip_until
-------------|------------|--------------|------------
arxiv        | 0          | -            | -
s2           | 2          | T-3m         | -  (아직 미발동)
openalex     | 3          | T-1m         | T+29m  (skip 중)
```

---

## 4. Fast-Fail 규칙 (§17.3)

응답이 0건일 때 다른 source를 기다리는 총 시간을 최소화한다.

### 4.1 첫 응답 source 0건

- **첫 번째 응답 source가 200 OK + 결과 0건**이면 나머지 2개 source는 **timeout을 절반(2.5s)으로 단축**하여 polling 계속
- 이미 응답 중인 source는 원래 timeout(5s) 유지

### 4.2 전체 0건 확정

모든 가용 source에서 0건이 확정되면:

1. **검색어 자동 정제 1회 재시도**:
   - 한국어 → 영어 변환 (예: "변환기 모델" → "transformer model")
   - 약어 풀어쓰기 (예: "LLM" → "large language model")
   - 카탈로그 ID가 있으면 카탈로그 항목 이름으로 대체 검색
2. 재정제 후에도 0건이면 → output-format.md §6.2 "검색 결과 없음" 출력

### 4.3 Fast-Fail 흐름 다이어그램

```
[source 1 응답: 200 + 0건]
        ↓
[source 2, 3: timeout 2.5s로 단축 polling]
        ↓
   ┌─────┴────────────────────┐
   ↓                          ↓
[하나라도 결과 있음]       [전체 0건 확정]
   ↓                          ↓
[partial 또는 정상 출력]  [검색어 자동 정제 1회 재시도]
                               ↓
                          ┌────┴────────────┐
                          ↓                 ↓
                      [결과 있음]       [여전히 0건]
                          ↓                 ↓
                      [정상 출력]      [§6.2 0건 출력]
```

---

## 5. HTTP 상태 코드별 처리 정책

| HTTP 상태 | 의미 | 처리 |
|----------|------|------|
| `200 OK` | 정상 | 결과 파싱 진행. 0건이면 §4 Fast-Fail 진입 |
| `429 Too Many Requests` | Rate limit 초과 | Exponential backoff: 1s → 2s → 4s, 최대 3회 재시도. 3회 후에도 429면 해당 source를 이번 호출에서 제외 + degraded mode 진입 |
| `503 Service Unavailable` | 서비스 일시 중단 | Circuit Breaker 실패 카운트 +1. backoff 1회 후 재시도, 실패 시 source 제외 + degraded mode |
| `4xx (기타)` | 잘못된 요청 (400, 404 등) | 검색어 정제 후 1회 재시도. 그래도 4xx면 source 제외 (circuit breaker 카운트는 증가하지 않음 — 클라이언트 오류이므로) |
| `5xx (기타)` | 서버 오류 | Circuit Breaker 실패 카운트 +1. backoff 후 1회 재시도, 실패 시 partial result로 이번 호출 계속 |
| `000` (timeout/network error) | 연결 불가 | Circuit Breaker 실패 카운트 +1. 즉시 3-tier Fallback 체인 §6 진입 |

### 5.1 Exponential Backoff 상세

```
시도 1: 즉시 호출
  → 429/503/5xx 응답
시도 2: 1초 대기 후 재호출
  → 429/503/5xx 응답
시도 3: 2초 대기 후 재호출
  → 429/503/5xx 응답
시도 4: 4초 대기 후 재호출
  → 실패 → source 제외, degraded mode 진입
```

- **총 backoff 한도**: 1+2+4 = 7s. 개별 API timeout 5s와 합산 시 최악 12s.
- 총 timeout 20s (§18.1) 이내 수렴 확인 필수.
- arXiv는 ToU상 3초당 1요청이므로, backoff 없이도 3초 간격이 기본 준수됨.

---

## 6. 3-tier Fallback 체인 (§13.4) — 무료 원칙 강제

`WebFetch` 도구 자체가 사용 불가하거나 네트워크 차단 환경에 대한 도구 레벨 fallback.

```
1차: WebFetch (3 API 직접 호출 — §4.4.1) — 🆓 완전 무료
  ↓ 실패 조건: 도구 미지원 / TLS 오류 / rate limit 소진 / WebFetch 자체 오류
2차: Bash + curl (응답 신뢰성 사용자 검증 필수) — 🆓 무료
  ↓ 실패 조건: 네트워크 차단 / curl 명령 미허용 / 3 API 모두 차단
3차: document-specialist 에이전트 위임 (xhigh) — 🆓 OMX 내장
```

### 6.1 1차: WebFetch

기본 동작. `WebFetch` 도구로 3 API를 직접 호출한다 (§4.4.1 도구 매핑 참조).

- arXiv: `https://export.arxiv.org/api/query?...` (Atom 1.0 XML)
- Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/search?...` (JSON)
- OpenAlex: `https://api.openalex.org/works?...` (JSON)
- 모두 🆓 완전 무료. 키 없이 anonymous 동작 보장.

### 6.2 2차: Bash + curl

WebFetch가 사용 불가한 환경에서 `Bash` 도구로 `curl`을 직접 실행한다.

```bash
# arXiv 예시
curl -s --max-time 5 \
  "https://export.arxiv.org/api/query?search_query=ti:transformer&max_results=10&sortBy=submittedDate&sortOrder=descending"

# Semantic Scholar 예시 (anonymous)
curl -s --max-time 5 \
  "https://api.semanticscholar.org/graph/v1/paper/search?query=transformer&limit=10&fields=title,authors,year,citationCount,externalIds,venue"

# OpenAlex 예시 (anonymous)
curl -s --max-time 5 \
  "https://api.openalex.org/works?search=transformer&per-page=10&filter=publication_year:2020-2026"
```

**주의사항**:
- curl 응답은 raw JSON/XML이므로 Codex가 직접 파싱해야 한다.
- 응답 신뢰성은 WebFetch와 동일하나, **사용자에게 curl 결과임을 명시**하고 검증을 권장한다.
- 출력 하단 footnote 추가: "2차 fallback (curl) — 사용자 검증 권장"

### 6.3 3차: document-specialist 에이전트 위임

1차·2차 모두 실패 시 (또는 3 API 모두 네트워크 차단 시) OMX 내장 에이전트에 위임한다.

```python
spawn_agent(
  agent_type="document-specialist",
  message="""
다음 주제에 대한 학술 논문 5~10편을 검색하고 정리해줘:
주제: {query}
연도 범위: {years}

검색 소스: Google Scholar, Semantic Scholar, arXiv, ACM DL, IEEE Xplore 등
각 논문에 대해 제목 / 저자 / 연도 / 발표처 / DOI 또는 arXiv ID / 핵심 기여 1~2문장을 제공해줘.
DOI나 arXiv ID가 없는 논문은 제외해줘.
"""
)
```

- xhigh 역할 우선 (분석/검색 성격이므로 — AGENTS.md 정책)
- 출력 상단 배너: "3차 fallback — document-specialist 에이전트 위임 (외부 API 직접 접근 불가)"
- document-specialist 결과는 §11.1 사전 차단 정책(식별자 정규식 검증)을 동일하게 적용한다.

---

## 7. 상용 MCP 정책 (§13.4) — 사용자 명시 동의 필수

`mcp__exa__*` (Exa AI) 등 상용 유료 MCP는 기본 fallback 체인에서 완전히 제거되어 있다.

### 7.1 왜 제거되었나

- Exa AI = 상용 유료 API. 사용자의 plan에 따라 quota가 소진된다.
- 무료 보장 불가이므로 사용자 동의 없이 호출하는 것은 무료 원칙 위반.
- 향후 무료 학술 MCP (arXiv MCP, OpenAlex MCP 등) 등장 시 본 정책 재검토.

### 7.2 상용 MCP 활성화 방법 (옵션)

사용자가 명시적으로 동의하는 경우에만 사용 가능:

**방법 A — 환경변수**:
```bash
export DEV_ADVISOR_ALLOW_PAID_MCP=true
```

**방법 B — CLI 플래그**:
```
/dev-advisor research transformer --allow-paid-mcp
```

### 7.3 상용 MCP 사용 시 출력 규칙

활성화된 경우, 출력 상단에 반드시 다음 배너를 표시한다:

```
> ⚠️ 상용 MCP 사용 중 (DEV_ADVISOR_ALLOW_PAID_MCP=true)
> Exa AI MCP를 통해 검색합니다. 사용자 quota가 소진될 수 있습니다.
```

- MCP 응답의 **출처 신뢰도는 LOW로 표시** (raw API 응답과 동등하게 취급 금지)
- §11.1 사전 차단 정책(식별자 정규식 검증)을 동일하게 적용
- 상용 MCP 결과가 포함된 행에는 `[MCP]` 태그 추가

---

## 8. Anonymous Fallback 동작 보장 — 무료 원칙 적용

모든 API 키는 선택적 무료 옵션이다. 키가 없어도 anonymous로 정상 동작해야 한다.

| API | 키 누락 시 동작 | 사용자 안내 |
|-----|--------------|------------|
| **arXiv** | 항상 anonymous 정상 동작 (인증 없음) | 안내 불필요 |
| **Semantic Scholar** | anonymous shared throttling (느리지만 동작) | 출력 1줄: "anonymous mode — rate limit 적용 가능" |
| **OpenAlex** | anonymous 정상 동작 (mailto는 polite pool 옵션) | 출력 1줄: "anonymous mode — rate limit 적용 가능" |

**사용자에게 키 발급을 요구하는 메시지 출력 금지**:
- "API 키를 발급해주세요" 같은 안내 절대 금지
- "키가 없어 실행 불가" 메시지 절대 금지
- 키 없이 anonymous로 진행하면서 1줄 소극적 안내만 허용

**환경변수 (모두 무료, 선택적)**:
```bash
SEMANTIC_SCHOLAR_API_KEY=<무료 키>   # 1 RPS 보장 옵션
OPENALEX_API_KEY=<무료 키>           # polite pool priority 옵션
OPENALEX_MAILTO=user@example.com     # polite pool 등록 옵션
```

---

## 9. 다른 모드와의 관계 (§13.3)

research 모드의 외부 API 의존성은 다른 7 모드에 전혀 영향을 주지 않는다.

| 모드 | 외부 API 의존 | 장애 전파 |
|------|:------------:|:--------:|
| `full` | 없음 | 없음 |
| `swarm` | 없음 | 없음 |
| `recommend`, `review`, `qa`, `qc`, `security-audit`, `perf`, `debug` | 없음 | 없음 |
| **`research`** | arXiv + S2 + OpenAlex | research 모드 내부에만 격리 |

**이유**: research 모드는 `full` / `swarm`에 미포함으로 결정됨 (§13.3). 외부 API 장애가 `full` 전체 실패로 이어지는 것을 방지하기 위함.

**사용자가 통합 결과를 원할 때**:
```
1. /dev-advisor full <module>        # 7 모드 통합 보고 (외부 API 의존 없음)
2. /dev-advisor research <topic>     # 별도 학술 근거 (외부 API 사용)
3. 사용자가 두 결과를 종합
```

---

## 10. Fallback 결정 트리 (전체 흐름 요약)

```
[/dev-advisor research <query> 호출]
        ↓
[WebFetch 도구 가용?]
   ↓ YES                   ↓ NO
[3 API WebFetch 호출]   [Bash + curl 2차 fallback]
   ↓                        ↓
   ↓                   [curl 가능?]
   ↓                    ↓ YES         ↓ NO
   ↓               [curl 호출]   [document-specialist 3차]
   ↓                    ↓
[응답 결과 집계]
   ↓
[Circuit Breaker 확인 — skip 상태 source 제외]
   ↓
[3-of-3 정상?] → 정상 매트릭스 출력
   ↓ NO
[2-of-3 정상?] → degraded mode 배너 + 가용 source만으로 매트릭스
   ↓ NO
[1-of-3 정상?] → severe degradation 배너 + 단일 source 매트릭스 (신뢰성 LOW)
   ↓ NO
[0-of-3 정상?]
   ↓
[Fast-Fail: 검색어 자동 정제 1회 재시도]
   ↓
[여전히 0건?] → §6.2 "검색 결과 없음" 출력 + document-specialist hand-off
```

---

## 11. 출력 예시 — degraded mode

### 11.1 2-of-3 정상 (S2 실패)

```markdown
## Research — transformer

> ⚠️ degraded mode: Semantic Scholar unavailable (503 Service Unavailable after 3 retries)
> 인용수는 OpenAlex 값만 표시됩니다.

### 2. 논문 매트릭스 (Top 8)

| # | 제목 | 저자 (1st+) | 연도 | 발표처 | 인용수 | 출처 | 3-source |
|:-:|------|------------|:----:|--------|:-----:|------|:--------:|
| 1 | Attention Is All You Need | Vaswani et al. | 2017 | NeurIPS | 120,453 (OA) | [arXiv](https://arxiv.org/abs/1706.03762) | A✓ S✗ O✓ |
...

### 5. 3-source 교차 검증 로그

- API 응답 상태: arXiv 200 / S2 503 (circuit breaker 진입) / OpenAlex 200
- **degraded mode**: S2 응답 없음 — 인용수·TLDR·influentialCitationCount 데이터 없음

---
footnote: Semantic Scholar circuit breaker 발동 (5분 내 3회 503 — 30분 skip, 만료: 14:35 KST)
```

### 11.2 1-of-3 정상 (arXiv only)

```markdown
## Research — transformer

> ⚠️⚠️ severe degradation: only arXiv responding
> Semantic Scholar / OpenAlex 모두 응답 없음. 인용수·메타데이터 없이 arXiv 데이터만 표시됩니다.

...

**신뢰성·재현성 조건**:
- single-source 한계 (arXiv only): 동료검토 여부 불명 / 인용수 확인 불가 / 철회 여부 (is_retracted) 확인 불가.
- 결과 활용 전 사용자가 Semantic Scholar 또는 OpenAlex에서 직접 확인하기를 권장합니다.
```

### 11.3 0-of-3 정상 (전체 장애)

```markdown
## Research — 변환기 모델

### 검색 결과 없음

3-source 모두 0건 또는 응답 없음. 검색어 자동 정제 후 재시도합니다.

**정제된 검색어**: "transformer model" (한→영 변환)

재시도 중...

[재시도 후에도 0건인 경우 — output-format.md §6.2 출력]
```

---

## 12. 관련 문서

| 문서 | 참조 내용 |
|------|---------|
| `sources.md` | 3 API 엔드포인트 + 응답 스키마 + rate limit 정책 |
| `output-format.md` | §6.2 0건 대응 출력 스켈레톤 |
| `performance.md` | §18 timeout / latency 목표 / backoff schedule |
| `testing.md` | §19 부분 장애 mock fixture 50케이스 |
| `PLAN-research-mode.md` | §13.4 (원본), §17 (원본), §13.3 full/swarm 관계 |
