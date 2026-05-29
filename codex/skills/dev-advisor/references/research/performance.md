# performance.md — research 모드 성능 목표 / 동시성 / 캐싱

> **출처**: PLAN-research-mode.md v0.5 §18 (Latency / 동시성 / 캐싱) + §4.4.1 (API → 도구 매핑)
> **최종 업데이트**: 2026-05-28
> **상태**: Phase 3 구현 기준 (Phase 2 사전 게이트 통과 후 유효)

---

## 1. 개요

research 모드는 arXiv · Semantic Scholar · OpenAlex 3개의 외부 무료 API를 호출하여
학술 논문 매트릭스를 생성한다. 외부 네트워크 I/O가 포함되므로 응답 시간이 내부 카탈로그
lookup보다 길다. 이 문서는 **수용 가능한 latency 목표**, **rate-limit aware 동시성 스케줄**,
**세션 내 캐싱 정책**을 정의하여 다음 두 목표를 동시에 달성한다.

| 목표 | 구체적 수치 |
|------|------------|
| 사용자 체감 응답 시간 최소화 | p50 < 8s, p95 < 15s |
| 외부 API 약관·rate limit 준수 | arXiv ToU (3초/1req), S2 shared throttle, OA polite pool |

### 1.1 성능 목표와 동시성의 관계

- **병렬 허용 범위**: 서로 다른 API 도메인 사이 (`arXiv` + `OpenAlex`)
- **직렬 강제 범위**: 동일 API 내 다중 쿼리 (`arXiv` 쿼리 2개 → 3초 간격)
- **LLM 런타임 자동 rate-limit 가정 금지**:Codex 런타임이 rate limit를 투명하게
  지켜준다고 가정하지 않는다. 명시적 sleep 또는 timestamp-based throttle이 구현 코드에
  반드시 존재해야 한다.

---

## 2. Latency 목표 (§18.1)

| 메트릭 | 목표 | 비고 |
|--------|------|------|
| **p50 응답 시간** | **< 8s** | 3-of-3 정상 + 중복 제거 + 매트릭스 생성 전체 |
| **p95 응답 시간** | **< 15s** | Semantic Scholar 직렬 + fallback 1회 포함 |
| **개별 API timeout** | **5s** | arXiv / Semantic Scholar / OpenAlex 동일 적용 |
| **총 timeout** | **20s** | 초과 시 partial result 출력 (§5 graceful degradation 참조) |

### 2.1 측정 기준

- **p50**: 연속 10회 호출 중 5번째 값 (mock fixture dry-run 포함)
- **p95**: 연속 20회 호출 중 19번째 값
- **개별 API timeout**: `WebFetch` 호출 시작~응답 수신 완료까지의 wall-clock 시간
- **총 timeout**: research 모드 진입~최종 출력 마지막 바이트까지의 wall-clock 시간

### 2.2 회귀 경보 기준

- p50 > 10s: 경보 발생 → `testing.md §3.3` dry-run latency 측정 재실행
- p95 > 18s: 경보 발생 → API 응답 시간 분포 점검 + circuit breaker 상태 확인
- 총 timeout 도달 횟수 > 3회/세션: fallback 체인 점검

---

## 3. API → 도구 매핑 (§4.4.1)

| 소스 | 사용 도구 | 응답 포맷 | 파싱 책임 | 동시성 |
|------|----------|----------|----------|:------:|
| **arXiv** | `WebFetch` | **Atom 1.0 XML** (JSON 아님 — 주의) | Codex inline XML parsing | **직렬 throttled** |
| **Semantic Scholar** | `WebFetch` + `fields=` 파라미터 명시 | JSON | Codex inline JSON parsing | **직렬** |
| **OpenAlex** | `WebFetch` + `User-Agent: mailto:...` 헤더 (옵션) | JSON | Codex inline JSON parsing | **직렬** (🆓 완전 무료) |

### 3.1 arXiv 응답 포맷 주의사항

arXiv API (`https://export.arxiv.org/api/query`)는 **Atom 1.0 XML**을 반환한다.
JSON이 아니므로 다음을 반드시 확인한다.

```xml
<!-- arXiv 응답 예시 구조 -->
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v2</id>
    <title>Attention Is All You Need</title>
    <author><name>Vaswani, Ashish</name></author>
    <published>2017-06-12T17:00:00Z</published>
    <link href="https://arxiv.org/abs/1706.03762" rel="alternate" type="text/html"/>
    <link href="https://arxiv.org/pdf/1706.03762" rel="related" type="application/pdf"/>
    <!-- arxiv:doi는 10.48550/arXiv.* 형태 -->
    <arxiv:doi xmlns:arxiv="http://arxiv.org/schemas/atom">10.48550/arXiv.1706.03762</arxiv:doi>
  </entry>
</feed>
```

- arXiv ID 추출: `<id>` 태그에서 `abs/` 이후 값 추출 → `1706.03762v7` → version 제거 → `1706.03762`
- arXiv DOI 형태 (`10.48550/arXiv.1706.03762`) → `1706.03762`와 **동일 논문으로 병합** (PLAN §5.3 #3)

### 3.2 Semantic Scholar `fields=` 명시

`fields=` 파라미터 없이 호출하면 필드 대부분이 누락된다. 반드시 명시한다.

```
GET https://api.semanticscholar.org/graph/v1/paper/search
  ?query=<검색어>
  &fields=title,authors,year,venue,citationCount,externalIds,openAccessPdf,tldr,influentialCitationCount
  &limit=10
```

필수 필드:

| 필드 | 용도 |
|------|------|
| `title` | 논문 제목 |
| `authors` | 저자 목록 (1st author 추출) |
| `year` | 발행 연도 |
| `venue` | 발표처 (NeurIPS, ICML 등) — API 응답 raw 그대로 사용, Codex 추정 금지 |
| `citationCount` | 인용수 — API 응답 raw 그대로 사용 |
| `externalIds` | DOI / arXiv ID / MAG / PubMed 등 식별자 교차 참조 |
| `openAccessPdf` | 무료 PDF URL (있을 경우) |
| `tldr` | 자동 요약 (null 가능 — §3.3 fallback 처리) |
| `influentialCitationCount` | 영향력 있는 인용수 (정렬 가중치에 활용) |

### 3.3 TLDR null 처리 (PLAN §5.4)

S2 `tldr` 필드는 항상 존재하지 않는다.

```
tldr 처리 우선순위:
  1. tldr.text 존재 → 그대로 사용
  2. tldr == null AND abstract 존재 → abstract 첫 문장 (최대 150자)
  3. 모두 없음 → "n/a"
```

Codex가 TLDR 내용을 추정하거나 생성하는 것을 절대 금지한다.

### 3.4 OpenAlex `User-Agent` 헤더 (polite pool 옵션)

```
User-Agent: mailto:your@email.com
```

- `OPENALEX_MAILTO` 환경변수가 설정된 경우에만 헤더에 주입
- 미설정 시 anonymous 호출 (완전 무료, 정상 동작)
- 이메일 하드코딩 금지 — 환경변수로만 주입

OpenAlex 필터 문법 (v0.3 정정 — 콜론 사용):

```
GET https://api.openalex.org/works
  ?search=<검색어>
  &filter=cited_by_count:>50,topics.id:T<ID>
  &sort=cited_by_count:desc
  &per-page=10
```

---

## 4. 동시성 Schedule (§18.2) — Rate-limit Aware

### 4.1 실행 모델 개요

```
단일 어시스턴트 턴 실행 순서:

  [동시 호출 가능]
  arXiv WebFetch(q1)  ──────────────── 최대 5s
  OpenAlex WebFetch(q1) ────────────── 최대 5s
          ↓ (두 응답 수신 후)
  [직렬 호출]
  Semantic Scholar WebFetch(q1) ─────── 최대 5s
          ↓
  중복 제거 + 매트릭스 생성 ─────────── < 1s
          ↓
  최종 출력
```

**정상 케이스 총 소요 시간**: max(arXiv, OpenAlex) + S2 = max(5s, 5s) + 5s = **10s**
(**p50 < 8s** 달성: 실제 응답이 timeout보다 빠른 경우 = 3~5s 수준)

### 4.2 arXiv — 직렬 throttled (ToU 준수)

**ToU 조건**: 3초당 1요청, 단일 연결 유지.

| 규칙 | 내용 |
|------|------|
| 동일 API 내 다중 쿼리 | **직렬 + 3초 간격** (arXiv 쿼리 2개 → 첫 번째 완료 후 3초 대기 → 두 번째) |
| 병렬 호출 금지 | arXiv 2개 이상을 동시에 WebFetch 호출하는 것은 **ToU 위반** |
| 동일 쿼리 하루 1회 | §6 캐싱 정책 in-memory cache로 회피 |
| 에러 시 backoff | 429 응답 → exponential backoff (§4.5) |

```
arXiv 다중 쿼리 예시 (올바른 순서):
  1. WebFetch(arXiv, q="transformer attention") → 응답 수신
  2. sleep(3s)  ← 필수
  3. WebFetch(arXiv, q="self-attention mechanism") → 응답 수신
```

### 4.3 Semantic Scholar — 직렬

| 인증 상태 | 동작 | 권장 |
|----------|------|------|
| **무인증 (anonymous)** | shared throttling pool — rate 보장 없음, 느리지만 동작함 | exponential backoff 필수 |
| **무료 API 키** (`SEMANTIC_SCHOLAR_API_KEY`) | 1 RPS 이상 보장 | 있으면 사용, 없으면 anonymous fallback |

- anonymous 모드 시 응답 상단에 1줄 안내 출력: `"anonymous mode — rate limit 적용 가능, 결과 제한 가능"`
- **사용자에게 키 발급 강요 금지** (PLAN §10.1 — 소극적 안내 1줄만)

### 4.4 OpenAlex — 직렬 (🆓 완전 무료)

- anonymous 호출로 완전 무료, 인증 없이 정상 동작
- `OPENALEX_MAILTO` 설정 시 polite pool priority queue 진입 (응답 속도 향상 옵션)
- `OPENALEX_API_KEY` 설정 시 추가 rate limit 완화 (선택)
- **Concepts deprecated** → **Topics API 사용** (PLAN §5.2, v0.3 수정)

### 4.5 Exponential Backoff (공통)

429 또는 503 응답 수신 시:

```
재시도 1: 1초 대기 후 재호출
재시도 2: 2초 대기 후 재호출
재시도 3: 4초 대기 후 재호출
재시도 초과 (3회): 해당 source를 degraded로 표시 → §5 graceful degradation 진입
```

- **별도 helper 함수로 구현** (각 API 호출 코드에 inline 삽입 금지)
- 429 응답 횟수를 세션 내 카운터로 기록
- 동일 source 5분 내 3회 이상 429 → **circuit breaker 진입** (§5.3)

---

## 5. Graceful Degradation — 성능 연계 (§17 요약)

성능 목표를 유지하면서 부분 장애를 처리하는 매트릭스:

| API 응답 상태 | 총 소요 시간 예측 | 출력 |
|-------------|:---------------:|------|
| **3-of-3 정상** | **max 10s** (p50 < 8s 목표) | 정상 매트릭스 + `[arXiv ✓ S2 ✓ OA ✓]` |
| **2-of-3 정상** (S2 실패) | **max 10s** (실패 timeout 5s 포함) | `⚠️ degraded mode: Semantic Scholar unavailable` 배너 |
| **2-of-3 정상** (arXiv 실패) | **max 10s** (실패 timeout 5s 포함) | `⚠️ degraded mode: arXiv unavailable` 배너 |
| **2-of-3 정상** (OA 실패) | **max 10s** (실패 timeout 5s 포함) | `⚠️ degraded mode: OpenAlex unavailable` 배너 |
| **1-of-3 정상** | **max 5s** (나머지 2개 timeout 5s는 병렬) | `⚠️⚠️ severe degradation` 배너 + 신뢰성 LOW |
| **0-of-3 정상** | **< 5s** (fast-fail) | §6.2 0건 대응 + document-specialist hand-off |
| **cache hit** | **< 1s** | 캐시 응답 + "cached — last fetched X minutes ago" |

### 5.1 총 timeout 20s 초과 시

- partial result가 존재하면 즉시 출력 (완성 대기 없음)
- partial result 없으면 §6.2 0건 대응 출력 + 재시도 제안

### 5.2 Fast-Fail 규칙

- 첫 응답 source가 `200 OK` + 0건 → 다른 source는 timeout **절반(2.5s)**으로 단축 polling
- 모두 0건 확정 → 검색어 자동 정제 1회 재시도 (한→영 변환, 약어 풀어쓰기)
- 그래도 0건 → §6.2 출력

### 5.3 Circuit Breaker

- 동일 source 5분 내 실패 ≥ 3회 → **30분 skip** (해당 source 자동 제외)
- skip 상태는 출력 하단 footnote로 사용자에게 명시
- 30분 경과 후 자동 복구 시도 (half-open 상태)

---

## 6. 캐싱 정책 (§18.3) — arXiv ToU 준수

### 6.1 캐시 종류 및 TTL

| 소스 | 캐시 종류 | TTL | 이유 |
|------|----------|:---:|------|
| **arXiv** | 세션 in-memory cache (쿼리 단위) | **1일** | ToU — 동일 query 하루 1회 권장 |
| **Semantic Scholar** | 세션 in-memory dedup (검색어 normalized) | **5분** | shared throttle 회피 |
| **OpenAlex** | 세션 in-memory dedup (검색어 normalized) | **5분** | 불필요한 반복 호출 방지 |

### 6.2 캐시 키 정규화

```
캐시 키 생성 규칙:
  1. 검색어를 lowercase로 변환
  2. 불용어 제거 (the, a, an, of, in, for 등)
  3. 공백을 _ 로 치환
  4. 옵션(--years, --limit, --bias)을 키에 포함

예시:
  입력: "Attention Is All You Need" --years 2017-2026 --limit 10
  캐시 키: "attention_all_you_need_y2017-2026_l10"
```

### 6.3 캐시 hit 처리

캐시 hit 시 반드시 사용자에게 명시:

```
> [캐시 응답] arXiv: "transformer attention" — 마지막 조회 8분 전 (session cache)
```

- 캐시 응답과 신규 응답을 혼합 출력하는 경우: 각 행에 `[cached]` 표시

### 6.4 캐시 무효화 조건

- 사용자가 `--no-cache` 플래그 사용
- TTL 만료
- API 응답 스키마 변경 감지 (필드 누락 → 캐시 전체 drop)

### 6.5 디스크 저장 금지 (PLAN §10.3 정합)

- 검색 결과를 파일로 저장하지 않는다
- `~/.codex/`, `.omx/`, 프로젝트 디렉토리 어디에도 결과를 쓰지 않는다
- 추후 영구 캐시 도입 시 별도 PLAN 작성 + 사용자 승인 필요

---

## 7. 총 응답 시간 예측 시나리오

### 7.1 정상 케이스

```
시간축 (초):
0s  ─── arXiv WebFetch 시작
    ─── OpenAlex WebFetch 시작 (동시)
3s  ─── arXiv 응답 수신 (평균)
4s  ─── OpenAlex 응답 수신 (평균)
4s  ─── Semantic Scholar WebFetch 시작 (arXiv + OA 완료 후)
7s  ─── S2 응답 수신 (평균)
7.5s ── 중복 제거 + 매트릭스 생성 완료
8s  ─── 출력 완료 ← p50 목표 달성
```

### 7.2 부분 장애 (1 source 실패)

```
시간축 (초):
0s  ─── arXiv WebFetch 시작
    ─── OpenAlex WebFetch 시작 (동시)
5s  ─── arXiv timeout (실패로 처리)
5s  ─── OpenAlex 응답 수신 (or 동시 timeout)
5s  ─── S2 WebFetch 시작
8s  ─── S2 응답 수신
9s  ─── 매트릭스 생성 + degraded 배너 출력 ← p50 < 10s
```

- **총 소요 시간**: max(arXiv, OA) + S2 = 5s + 3~5s = **8~10s** (p95 < 15s 달성)

### 7.3 부분 장애 (2 sources 실패)

```
0s  ─── 3개 API 동시 시도 (arXiv throttle 규칙상 OA만 병렬)
5s  ─── 2개 timeout
5s  ─── 1개 응답 수신
6s  ─── 매트릭스 생성 + severe degradation 배너 출력
```

- **총 소요 시간**: **max 5s** (나머지 2개 timeout 포함)

### 7.4 전체 장애 (0-of-3 정상)

```
0s  ─── 호출 시작
5s  ─── 모두 timeout (fast-fail 2.5s로 단축 가능)
5s  ─── §6.2 0건 대응 출력
```

- fast-fail 적용 시 **< 3s** 가능

### 7.5 캐시 hit

```
0s  ─── 캐시 키 조회
<1s ─── 캐시 응답 반환 + "cached" 명시
```

---

## 8. Rate-Limit Aware Throttle 구현 가이드

### 8.1 Throttle 구현 원칙

**LLM 런타임이 자동으로 rate limit를 지켜준다고 가정 금지** (PLAN §4.4.1).

구현 코드에 다음이 반드시 존재해야 한다:

```python
# arXiv throttle 예시 (Python pseudo-code)
import time

ARXIV_LAST_CALL_TS = None  # 세션 내 상태

def arxiv_fetch(query: str) -> dict:
    global ARXIV_LAST_CALL_TS
    if ARXIV_LAST_CALL_TS is not None:
        elapsed = time.time() - ARXIV_LAST_CALL_TS
        if elapsed < 3.0:
            time.sleep(3.0 - elapsed)  # 3초 간격 보장
    ARXIV_LAST_CALL_TS = time.time()
    # ... WebFetch 호출
```

### 8.2 Exponential Backoff Helper

별도 helper 함수로 구현:

```python
# exponential backoff helper (공통)
def with_backoff(fetch_fn, max_retries=3, base_delay=1.0):
    """
    429/503 응답 시 지수 대기 후 재시도.
    최대 3회 재시도, base_delay 1s → 2s → 4s.
    """
    for attempt in range(max_retries + 1):
        result = fetch_fn()
        if result.status_code in (429, 503):
            if attempt == max_retries:
                return None  # circuit breaker 진입 신호
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
            continue
        return result
    return None
```

### 8.3 429 카운터 및 Circuit Breaker

```python
# 세션 내 429 카운터 (소스별)
FAILURE_COUNTS = {"arxiv": 0, "s2": 0, "openalex": 0}
CIRCUIT_OPEN_UNTIL = {"arxiv": 0, "s2": 0, "openalex": 0}
WINDOW_SECONDS = 300  # 5분 window
CIRCUIT_BREAK_THRESHOLD = 3
CIRCUIT_BREAK_DURATION = 1800  # 30분

def is_circuit_open(source: str) -> bool:
    return time.time() < CIRCUIT_OPEN_UNTIL[source]

def record_failure(source: str):
    FAILURE_COUNTS[source] += 1
    if FAILURE_COUNTS[source] >= CIRCUIT_BREAK_THRESHOLD:
        CIRCUIT_OPEN_UNTIL[source] = time.time() + CIRCUIT_BREAK_DURATION
        # 사용자에게 footnote로 명시
```

---

## 9. 성능 측정 (§19.5) — 회귀 방지

### 9.1 Mock Fixture 기반 Dry-Run

실제 API 호출 없이 latency를 측정하는 dry-run:

```bash
# verify-references.sh --check performance 호출 시
bash scripts/verify-references.sh --check performance
```

내부 동작:
1. `references/research/fixtures/` 에서 정상 케이스 15개 로드
2. mock 응답으로 research 모드 실행 (실제 WebFetch 차단)
3. p50 / p95 측정 → 임계 비교

### 9.2 Latency 임계 검증

| 임계 | 측정 방법 | 실패 시 |
|------|----------|--------|
| p50 < 8s | mock 15케이스 중 8번째 값 | 회귀 경보 + `PERF_REGRESSION` 표시 |
| p95 < 15s | mock 20케이스 중 19번째 값 | 회귀 경보 + API timeout 조정 검토 |
| 개별 timeout 5s | mock timeout 케이스 12개 | 초과 시 fallback 진입 검증 |

### 9.3 CI 통합 옵션 (미래 PLAN)

```bash
# CI에서 회귀 방지 명령 (선택)
bash scripts/verify-references.sh --check performance
# 실패 시 exit 1 → CI 빌드 차단
```

---

## 10. Fallback 체인 (성능 관점)

성능 저하 순서로 정의된 3-tier fallback (PLAN §13.4):

```
1차: WebFetch (3 API 직접 호출)
     ├─ 정상: p50 < 8s
     └─ 실패 (도구 미지원 / TLS / rate limit hit)
          ↓
2차: Bash + curl 직접 호출
     ├─ 정상: p50 < 12s (추가 프로세스 fork overhead)
     ├─ 응답 신뢰성 사용자 검증 필수
     └─ 실패 (네트워크 차단 등)
          ↓
3차: document-specialist 에이전트 위임 (xhigh)
     ├─ 에이전트 spin-up 시간 포함 → p50 > 20s 가능
     └─ 사용자에게 "에이전트 위임 중" 명시
```

**상용 MCP (Exa AI 등)는 default fallback에서 제거** (PLAN §13.4, v0.5).
사용자 명시 동의 + `DEV_ADVISOR_ALLOW_PAID_MCP=true` 환경변수 시에만 선택적 사용.

---

## 11. 주요 제약 요약

| 항목 | 제약 | 근거 |
|------|------|------|
| arXiv 호출 간격 | 최소 3초 | arXiv ToU |
| arXiv 동일 쿼리 재호출 | 하루 1회 | arXiv ToU + §6 캐싱 |
| 동일 API 내 병렬 호출 | 금지 | rate limit 준수 |
| arXiv + OpenAlex 병렬 | 허용 | 도메인 다름 |
| S2 호출 순서 | arXiv + OA 완료 후 | 직렬 |
| backoff 최대 재시도 | 3회 | §4.5 정의 |
| circuit breaker 임계 | 5분 내 3회 실패 | §5.3 정의 |
| circuit breaker 지속 | 30분 | §5.3 정의 |
| 총 timeout | 20s | §2 Latency 목표 |
| 디스크 저장 | 금지 | PLAN §10.3 |

---

## 12. 참조 문서

| 문서 | 관련 섹션 |
|------|----------|
| `PLAN-research-mode.md` | §4.4.1 (도구 매핑), §18 (성능), §17 (graceful degradation) |
| `references/research/fallback.md` | Graceful degradation 상세 구현 |
| `references/research/testing.md` | §19 테스트 매트릭스, mock fixture, 환각 회귀 테스트 |
| `references/research/sources.md` | API 엔드포인트 + 응답 스키마 + rate limit 가이드 |

---

> **면책**: 외부 API 응답 시간은 서버 측 요인에 의해 변동된다.
> 이 문서의 수치는 목표값이며, 실제 측정값은 `testing.md §3.3` dry-run으로 확인한다.
