# output-format.md — research 모드 산출물 포맷 규약

> **참조 PLAN**: `PLAN-research-mode.md` v0.5
> **참조 섹션**: §6.1 (메인 출력 스켈레톤) / §6.2 (0건 대응) / §11.1 (사전 차단 정책) / §5.4 (환각 방지 정책) / §17.1 (Degraded Mode)
> **작성일**: 2026-05-28
> **상태**: Phase 3 — 신규 작성

---

## 1. 개요

`/dev-advisor research` 모드가 생성하는 모든 출력은 이 문서의 포맷 규약을 따른다.

포맷 규약의 목적은 세 가지다.

1. **환각 방지** — 매트릭스 행은 실제 API 응답에 존재하는 식별자(DOI / arXiv ID / S2 paperId / OpenAlex Work ID)를 반드시 포함해야 하며, 없는 값을 Claude가 추론·생성하는 것을 원천 차단한다.
2. **3-source 교차 검증 가시화** — 각 논문이 arXiv / Semantic Scholar / OpenAlex 중 어느 소스에서 발견됐는지를 출력에 명시하여 단일 소스 환각·편향을 드러낸다.
3. **카탈로그 연결** — 검색 결과를 기존 카탈로그 항목(ID)에 매핑하여 dev-advisor의 정적 권위(카탈로그)와 동적 최신성(학술 논문)을 결합한다.

이 문서는 다음 영역을 다룬다.

- **§2** 정상 케이스 출력 스켈레톤 (메인 출력)
- **§3** 0건 대응 출력
- **§4** Degraded Mode 배너
- **§5** 사전 차단 정책 (매트릭스 행 생성 전 검증)
- **§6** 매트릭스 컬럼별 API 응답 필드 출처
- **§7** 환각 방지 체크리스트
- **§8** 출력 포맷 선택 기준 요약
- **§9** 무료 정책 출력 규칙
- **§10** arXiv Atom XML 파싱 주의사항
- **§11** 관련성 점수 공식 및 `--bias` 옵션
- **§12** rate-limit 안내 출력 정책

---

## 2. 메인 출력 스켈레톤 (정상 케이스)

정상 케이스란 3-source(arXiv / Semantic Scholar / OpenAlex) 중 2개 이상이 정상 응답(HTTP 200)을 반환하고, 중복 제거 후 최소 1건 이상의 논문이 존재하는 경우다.

```markdown
## Research — <topic|catalog-id|query>

> anonymous mode — rate limit 적용 가능 (무료 API 키 옵션 있음)
> (API 키 없이도 완전 동작. 키는 선택적 무료 옵션)

### 1. 검색 쿼리 (Search Queries)

- arXiv: `<쿼리>` (카테고리: `cs.SE`, 연도: 2020-2026)
- Semantic Scholar: `<쿼리>` (field: "Software Engineering")
- OpenAlex: `<쿼리>` (topic: T12490 ✓verified)

### 2. 논문 매트릭스 (Primary, Top N)

| # | 제목 | 저자 (1st+) | 연도 | 발표처 | 인용수 | 무료PDF | 카탈로그 매핑 | 신뢰도 | 3-source | 관련성 |
|:-:|------|------------|:----:|--------|:-----:|:------:|--------------|:------:|:--------:|:------:|
| 1 | Attention Is All You Need | Vaswani et al. (8) | 2017 | NeurIPS | 120,453 | [arXiv](https://arxiv.org/abs/1706.03762) | `/algorithm transformer` | HIGH | A✓ S✓ O✓ | ★★★★★ |
| 2 | BERT: Pre-training of Deep Bidirectional Transformers | Devlin et al. (4) | 2019 | NAACL | 87,210 | [arXiv](https://arxiv.org/abs/1810.04805) | `/algorithm bert` | HIGH | A✓ S✓ O✓ | ★★★★★ |
| 3 | ... | ... | ... | ... | ... | ... | ... | MED | A✓ S✓ O✗ | ★★★★ |

> ⚠️ **RETRACTED**: 철회된 논문이 포함된 경우 해당 행 앞에 이 마커를 표시하고, §5 신뢰성 필드에 "RETRACTED" 명시.

### 3. 카탈로그 Cross-Reference

| 매핑된 카탈로그 항목 | 매핑 논문 # | 매핑 신뢰도 |
|---------------------|------------|:----------:|
| `/algorithm transformer` | #1, #3 | HIGH |
| `/pattern attention-mechanism` | #1 | MED |
| `/principle deep-learning-fundamentals` | #4 | LOW |

**매핑 신뢰도 정량 기준** (LLM 주관 판단 금지 — §6.1 PLAN):

| 신뢰도 | 판정 조건 (AND) |
|:------:|----------------|
| **HIGH** | 논문 제목에 카탈로그 ID 토큰 1개 이상 포함 **AND** 인용수 ≥ 100 (또는 ID와 정확히 일치하는 알고리즘/패턴명) |
| **MED** | abstract 또는 Semantic Scholar TLDR에 ID 토큰 1개 이상 포함 (제목에는 없음) |
| **LOW** | S2 `fieldsOfStudy` 또는 OpenAlex Topics에 카탈로그 도메인 매칭만 존재 |

> 위 조건을 만족하지 않는 매핑은 출력 금지 (§5 사전 차단 정책 참조).
> 카탈로그 ID는 `catalog-index.json` 실제 항목과 대조 후에만 인용. 추정·유추 금지.

### Weak Evidence (최대 2개, DOI/arXiv ID 없지만 S2/OA ID 있음)

> PLAN §5.4: DOI / arXiv ID 없이 S2 paperId 또는 OpenAlex Work ID만 있는 항목은
> primary matrix에 포함하지 않고 이 섹션에 최대 2개까지만 표시한다.
> Top 3 핵심 논문 선정에는 포함되지 않는다.

| # | 제목 | 저자 (1st) | 연도 | 발표처 | S2 paperId / OA Work ID | 비고 |
|:-:|------|-----------|:----:|--------|------------------------|------|
| W1 | <제목> | <저자> | <연도> | <발표처> | S2: `<40자 hex>` | 워크숍 논문, DOI/arXiv 없음 |

### 4. 6 필드 산출

**선택/판정**: Top 3 핵심 논문 + 한 줄 종합 결론 (raw API 응답 기반 — Claude cutoff 이전 지식 혼입 금지)

**근거 (Why)**: 왜 이 3편이 핵심인가 — 인용수·발표처 권위·시점·재현성 (모든 수치는 API 응답 직접 reference)

**대안 비교**: A vs B vs C 각 접근법의 trade-off 비교

**표준 인용**: DOI / arXiv ID / S2 paperId / OpenAlex Work ID + 발표처 (§5 정규식 검증 통과 필수)
- 예: `doi:10.48550/arXiv.1706.03762` / `arXiv:1706.03762` / `NeurIPS 2017`

**적용 조건**: 이 논문(들)의 결과가 유효한 컨텍스트 — 데이터 규모 / 하드웨어 / 언어 / 도메인

**신뢰성·재현성 조건**:
- 코드/데이터 공개 여부 (Papers with Code 검색 결과 또는 `unknown (no reproduction report found)`)
- 동료 검토 vs 프리프린트 (`venue` API 필드 직접 reference)
- 재현 시도 보고 존재 여부 (1차: S2 응답 Papers with Code link → 2차: `paperswithcode.com/api/v1/papers/?title=<title>` → 3차: `unknown`)
- 알려진 한계 / 철회 여부 (OpenAlex `is_retracted` 필드)
- degraded mode인 경우 single-source 한계 명시

### 5. 3-source 교차 검증 로그

- 총 검색 결과: arXiv **N1**건 / S2 **N2**건 / OpenAlex **N3**건 → 중복 제거 후 **K**건
- 3중 검증 통과: **M**편 (전체 Top N 중)
- 단일 소스 only: **P**편 (검증 약함 — 인용수 없거나 메타 불완전)
- API 응답 상태: arXiv **200** / S2 **200** / OpenAlex **200** (정상 / degraded / 0건 중 해당 명시)
- drop된 행: **Q**건 (identifier 정규식 검증 실패 — §5 사전 차단)
- 경계 구간 분리 표시: **R**건 (제목 유사도 0.85~0.90 — 병합 보류)

### 6. Hand-off 후보

- 카탈로그 매핑 신뢰도 HIGH ≥ 3 → 카탈로그 lookup 후속 (`/algorithm <id>`, `/pattern <id>` 등)
- 코드 구현 요청 동반 → `Task(subagent_type="oh-my-claudecode:executor", model="opus", ...)`
- 검색어 모호 / 0건 → `Task(subagent_type="oh-my-claudecode:document-specialist", model="opus", ...)`
- 심층 비교 분석 요청 → `Task(subagent_type="oh-my-claudecode:analyst", model="opus", ...)` 또는 `scientist`
- 카탈로그 매핑 충돌 (한 논문이 여러 카탈로그 ID로 매핑) → `Task(subagent_type="oh-my-claudecode:architect", model="opus", ...)`

---

※ 본 결과는 외부 API 응답 원문 기반이며, 인용 전 사용자 검증을 권장합니다.
※ PDF 링크 안전성은 사용자 책임입니다.
※ anonymous mode 사용 시 rate limit 적용 가능 (무료 API 키 옵션 있음 — 키 없이도 동작 보장).
```

---

## 3. 0건 대응 출력 (§6.2)

0건 대응이란 3-source 모두 0건을 반환하거나, 정규식 검증을 통과한 식별자가 있는 논문이 없는 경우다. 이 경우 매트릭스 출력 없이 아래 포맷만 출력한다.

```markdown
## Research — <query>

### 검색 결과 없음

3-source 모두 0건. 다음을 시도해보세요:

1. **검색어 재정제**: 한국어 → 영어 변환, 약어 풀어쓰기, 카탈로그 ID 사용
2. **연도 범위 확장**: `--years 2010-2026`
3. **카탈로그 lookup 먼저**: `/pattern search <키워드>` 또는 `/principle search <키워드>`
4. **document-specialist 에이전트 위임**: 외부 학술 사이트 다중 소스 교차 검증

추천 다음 명령:
- `/dev-advisor research "<재정제된 검색어>"`
- `/pattern search <키워드>`
- `Task(subagent_type="oh-my-claudecode:document-specialist", model="opus", prompt="<query> 학술 논문 5편 정리")`

---

### 검색 로그

- arXiv: `<쿼리>` → 0건 (HTTP <상태코드>)
- Semantic Scholar: `<쿼리>` → 0건 (HTTP <상태코드>)
- OpenAlex: `<쿼리>` → 0건 (HTTP <상태코드>)
```

**0건 대응 트리거 조건**:

| 조건 | 처리 |
|------|------|
| 3-source 모두 HTTP 200이지만 결과 0건 | 위 포맷 출력 + 재정제 제안 |
| 정규식 검증 통과 식별자가 있는 행이 0개 (모두 drop) | 동일 |
| 한국어 입력 + 영문 후보 제시 후 사용자가 재검색 안 함 | 동일 + "한→영 재정제를 먼저 시도해보세요" 추가 |

---

## 4. Degraded Mode 배너 (§17.1)

3-source 중 일부가 응답 불가(HTTP 4xx/5xx, timeout)인 경우, 매트릭스 출력 상단에 배너를 삽입하고 신뢰성 필드에 single-source 한계를 명시한다.

### 4.1 배너 포맷

**2-of-3 정상** (1개 소스 불가):
```markdown
> ⚠️ **degraded mode**: Semantic Scholar unavailable (HTTP 503). 인용수 컬럼은 OpenAlex 값만 사용.
```

**1-of-3 정상** (2개 소스 불가):
```markdown
> ⚠️⚠️ **severe degradation**: only arXiv responding. 인용수 데이터 없음. 결과 신뢰도 낮음.
```

**3-of-3 불가** (전체 장애):
```markdown
> ❌ **API 전체 응답 불가**. 검색 결과 없음 포맷(§3)으로 전환. document-specialist 위임 권장.
```

### 4.2 Degraded Mode별 컬럼 처리

| 불가 소스 | 인용수 컬럼 | 발표처 컬럼 | 3-source 표시 |
|----------|:----------:|:----------:|:-------------:|
| S2 불가 | OpenAlex `cited_by_count` (출처 명시) | OpenAlex `host_venue.display_name` | `A✓ S✗ O✓` |
| OA 불가 | S2 `citationCount` | S2 `venue` | `A✓ S✓ O✗` |
| arXiv 불가 | S2 `citationCount` | S2 `venue` | `A✗ S✓ O✓` |
| S2 + OA 불가 | n/a (arXiv는 인용수 없음) | arXiv `journal-ref` (있으면) | `A✓ S✗ O✗` |

### 4.3 신뢰성·재현성 필드 Degraded Mode 명시

Degraded Mode에서는 6 필드 "신뢰성·재현성 조건"에 다음 문장을 반드시 포함한다.

```
단일 소스 한계: <불가 소스명> 응답 불가로 인용수/메타데이터 불완전. 결과 검증 권장.
```

---

## 5. 사전 차단 정책 (§11.1)

Claude가 매트릭스 행(`### 2. 논문 매트릭스`)에 논문을 추가하기 전, 아래 검증을 통과해야 한다. 통과 실패 시 해당 행은 자동 drop하고 검증 로그(`### 6. 3-source 교차 검증 로그`)에 drop 사유를 기록한다.

### 5.1 Identifier 필수 검증

모든 primary matrix 행은 다음 식별자 중 **최소 1개**가 존재해야 한다.

| 식별자 | 정규식 | 예시 |
|--------|--------|------|
| DOI | `^10\.\d{4,}/` | `10.48550/arXiv.1706.03762` |
| arXiv ID (신형) | `^\d{4}\.\d{4,5}(v\d+)?$` | `1706.03762`, `2401.00001v2` |
| arXiv ID (구형) | `^[a-z-]+/\d{7}(v\d+)?$` | `cs/0404001v1` |
| S2 paperId | `^[a-f0-9]{40}$` | `204e3073870fae3d05bcbc2f6a8e263d9b72e776` |
| OpenAlex Work ID | `^W\d{8,}$` | `W2963403868` |

DOI / arXiv ID 없이 S2 paperId 또는 OpenAlex Work ID만 있는 항목은 **primary matrix에 포함하지 않고** §2의 `### 3. Weak Evidence` 섹션에 최대 2개까지만 포함한다.

### 5.2 URL 화이트리스트

출력에 포함되는 모든 URL은 다음 도메인만 허용한다.

| 허용 도메인 | 용도 |
|------------|------|
| `arxiv.org` | 프리프린트 / abstract / PDF |
| `doi.org` | DOI 해석 |
| `semanticscholar.org` | 논문 페이지 |
| `openalex.org` | 메타데이터 |

shortener(예: `bit.ly`, `t.co`), redirect URL, 기타 미인증 도메인은 출력 금지. PDF 링크는 `[arXiv](url)` 또는 `[PDF](url)` 라벨만 사용하고 안전성은 사용자 책임임을 출력 하단 면책 문구로 명시한다.

### 5.3 메타 필드 직접 reference 강제

다음 컬럼은 **API 응답 raw value만 사용**한다. Claude의 추론·요약·번역·보완 금지.

| 컬럼 | 금지 행위 | 올바른 처리 |
|------|----------|------------|
| 저자명 | 번역·단순화·추가 | API `authors[].name` 그대로 |
| 연도 | 추정 | API `year` 또는 `publicationDate` 그대로 |
| 인용수 | 추정·반올림 표기 변경 | API `citationCount` / `cited_by_count` 그대로 |
| 발표처 | 약어 확장·추측 | API `venue` / `host_venue.display_name` 그대로 |

### 5.4 카탈로그 매핑 검증

매핑 컬럼에 기재하는 카탈로그 항목 ID는 `catalog-index.json`의 실제 항목 목록과 대조 후에만 인용한다. `catalog-index.json`에 존재하지 않는 ID를 추정·유추하여 기재하는 것은 금지한다.

### 5.5 6 필드 "선택/판정" 지식 혼입 금지

6 필드의 "선택/판정" 및 "근거 (Why)" 항목 작성 시, Claude의 훈련 데이터(cutoff 이전 지식)를 혼입하는 것을 금지한다. 오직 현재 API 응답에서 반환된 내용만을 근거로 작성한다. API 응답에 없는 사실은 반드시 `unknown` 또는 명시적 출처를 붙여 표기한다.

### 5.6 철회 논문 처리

OpenAlex `is_retracted: true`인 논문은 다음 처리를 따른다.

- 매트릭스 행 제목 앞에 `⚠️ RETRACTED:` 접두어 부착
- Top 3 핵심 논문에서 제외
- 6 필드 "신뢰성·재현성 조건"에 "RETRACTED" 명시
- Weak Evidence 섹션에도 포함하지 않음 (완전 제외)

### 5.7 drop 로그 기록 형식

정규식 검증 실패로 drop된 행은 `### 5. 3-source 교차 검증 로그` 내에 다음 형식으로 기록한다.

```
- drop된 행: 2건
  - "Some Paper Title" (S2 only) — DOI/arXiv ID 없음, S2 paperId: 3a4b...c9d0 → Weak Evidence 이동
  - "Another Paper" — 식별자 정규식 불일치 (DOI: "doi.org/..." — ^10\.\d{4,}/ 미통과) → 완전 drop
```

drop 사유는 세 가지로 구분한다.

| drop 사유 | 처리 |
|----------|------|
| DOI/arXiv ID 없음, S2 paperId 또는 OA Work ID 있음 | Weak Evidence 섹션으로 이동 (최대 2개 한도 내) |
| 식별자 있으나 정규식 불일치 | 완전 drop + 로그에 불일치 상세 기록 |
| `is_retracted: true` | 완전 drop + 로그에 "RETRACTED" 기록 |

---

## 6. 매트릭스 컬럼별 API 응답 필드 출처

primary matrix(`### 2. 논문 매트릭스`)의 각 컬럼이 어느 API 응답의 어느 필드에서 오는지를 명확히 한다. 동일 컬럼에 여러 소스가 있을 때는 **우선순위** 순서로 첫 번째 non-null 값을 사용한다.

| 컬럼 | 우선 소스 → API 응답 필드 | 비고 |
|------|--------------------------|------|
| 제목 | S2 `title` → OA `title` → arXiv `title` | 줄바꿈 제거, 원문 유지 |
| 저자 (1st+) | S2 `authors[0].name` + ` et al. (N)` → OA `authorships[0].author.display_name` → arXiv `author[0]` | 이름 번역 금지, 총 저자수 N은 API `authors.length` |
| 연도 | S2 `year` → OA `publication_year` → arXiv `published` (연도 부분) | 4자리 숫자 |
| 발표처 | S2 `venue` → OA `host_venue.display_name` → arXiv `journal-ref` | null이면 arXiv 기재 또는 `n/a` |
| 인용수 | S2 `citationCount` → OA `cited_by_count` | arXiv는 인용수 미제공 → n/a. degraded 시 출처 명시 |
| 무료PDF | arXiv `id` → OA `open_access.oa_url` → S2 `openAccessPdf.url` | 화이트리스트 도메인만. 없으면 셀 비움 |
| 카탈로그 매핑 | `catalog-index.json` 대조 결과 | 없으면 셀 비움 |
| 신뢰도 | §5 사전 차단 + §4 매핑 신뢰도 정량 기준 | HIGH / MED / LOW |
| 3-source | 각 API 응답에서 발견 여부 | `A✓/A✗`, `S✓/S✗`, `O✓/O✗` |
| 관련성 | `score = log(citations+1) × recency_weight × source_count` (query-strategies.md §관련성 점수 공식 참조) | ★1~5로 표시 |
| DOI | arXiv `doi` → S2 `externalIds.DOI` → OA `doi` | `^10\.\d{4,}/` 정규식 검증 |
| arXiv ID | arXiv `id` (정규화) → S2 `externalIds.ArXiv` | 버전 suffix 제거: `2401.12345v2` → `2401.12345` |
| TLDR | S2 `tldr.text` | null이면 abstract 첫 문장(최대 2문장). 여전히 null이면 `n/a`. 3문장 초과 전재 금지(fair use) |

### 6.1 arXiv DOI ↔ arXiv ID 중복 병합 규칙 (§5.3 PLAN)

`10.48550/arXiv.2401.12345` 형태의 DOI는 arXiv ID `2401.12345`와 **동일 논문**으로 처리한다. 두 소스에서 각각 발견된 경우 단일 행으로 병합하고 3-source 표시를 합산한다.

```
arXiv ID 정규화: 2401.12345v2 → 2401.12345
arXiv DOI 분해: 10.48550/arXiv.2401.12345 → arXiv ID 2401.12345
→ 동일 행으로 병합
```

### 6.2 제목 유사도 중복 제거 규칙

normalized title similarity > **0.90** AND 첫 저자 last name 일치 → 동일 논문으로 병합.
경계 구간(0.85~0.90)은 **분리 표시** 유지 + 교차 검증 로그에 기록.

---

## 7. 환각 방지 체크리스트

Claude가 research 모드 출력을 생성하기 직전, 아래 체크리스트를 확인한다. 하나라도 위반이 있으면 해당 항목을 수정하거나 drop한 후 출력한다.

```
[ ] 모든 primary matrix 행에 식별자(DOI / arXiv ID / S2 paperId / OA Work ID) 1개 이상 존재
[ ] 각 식별자가 §5.1 정규식 검증을 통과함
[ ] 출력에 포함된 모든 URL이 §5.2 화이트리스트 도메인에 속함
[ ] 인용수는 API raw value (Claude 추정·반올림 X)
[ ] 저자명은 API 응답 원문 그대로 (번역·단순화 X)
[ ] 발표처는 API `venue` / `host_venue.display_name` 원문 (추측 X)
[ ] 카탈로그 매핑 ID가 catalog-index.json 실제 항목에 존재함
[ ] weak-evidence 항목이 2개 이하
[ ] is_retracted=true 논문에 ⚠️ RETRACTED 마커가 부착되고 Top 3에서 제외됨
[ ] "선택/판정" 6 필드 작성 시 Claude cutoff 이전 지식 미혼입
[ ] 3-source 교차 검증 로그(§6)가 출력에 포함됨
[ ] Degraded Mode인 경우 배너(§4.1)가 매트릭스 상단에 삽입됨
[ ] TLDR / abstract 인용이 3문장 이하 (전체 전재 금지)
[ ] 0건인 경우 매트릭스 생성 없이 §3 포맷만 출력됨
[ ] 출력 하단 면책 문구 3줄이 포함됨
```

---

## 8. 출력 포맷 선택 기준 요약

| 상황 | 사용 포맷 |
|------|----------|
| 3-source 중 ≥2 정상 + 결과 ≥1건 | §2 메인 출력 스켈레톤 |
| 3-source 중 1개 불가 | §2 + §4.1 ⚠️ degraded mode 배너 |
| 3-source 중 2개 불가 | §2 + §4.1 ⚠️⚠️ severe degradation 배너 (결과 있으면) 또는 §3 (결과 0건) |
| 3-source 모두 불가 | §4.1 ❌ 전체 장애 배너 → §3 0건 포맷 전환 |
| 3-source 모두 정상이지만 결과 0건 | §3 0건 포맷 |
| 정규식 검증 통과 행이 0개 (모두 drop) | §3 0건 포맷 + drop 사유 로그 |

---

## 9. 무료 정책 출력 규칙 (§10.1 PLAN)

research 모드 출력은 다음 무료 정책 규칙을 준수한다.

- anonymous mode 상태임을 출력 상단 1줄로 소극적으로 안내한다 (면책 문구 아님, 배너 형태).
- API 키 발급·유료 결제를 사용자에게 요구하는 메시지를 출력하지 않는다.
- 무료 API 키(Semantic Scholar, OpenAlex)는 "선택적 rate limit 완화 옵션"으로만 언급하며, 없어도 동작한다는 사실을 명시한다.
- Exa MCP 등 상용 유료 API는 출력에서 언급하지 않는다 (사용자 명시 동의 시에만 허용).

```markdown
> anonymous mode — rate limit 적용 가능 (무료 API 키 옵션 있음)
> (API 키 없이도 완전 동작. 키는 선택적 무료 옵션)
```

위 2줄을 **메인 출력(§2)의 제목 바로 아래**에 포함한다. 키 발급 링크·유료 플랜 안내는 포함하지 않는다.

### 9.1 금지 메시지 목록

다음 유형의 메시지를 출력하지 않는다.

| 금지 유형 | 예시 (금지) | 올바른 대안 |
|----------|------------|------------|
| 키 발급 요구 | "Semantic Scholar API 키를 발급해 주세요" | 배너 1줄만: "anonymous mode — rate limit 적용 가능" |
| 유료 전환 유도 | "더 많은 결과를 원하시면 프리미엄 플랜을..." | 출력하지 않음 |
| 상용 MCP 안내 | "Exa MCP를 사용하면 더 좋은 결과를..." | 출력하지 않음 |
| 결제 링크 | `https://semanticscholar.org/product/api` | 출력하지 않음 |

---

## 10. arXiv Atom XML 파싱 주의사항 (§4.4.1 PLAN)

arXiv API는 JSON이 아닌 **Atom 1.0 XML** 형식으로 응답한다. WebFetch로 수신한 응답을 파싱할 때 다음 사항을 준수한다.

### 10.1 주요 Atom 1.0 필드 매핑

| 출력 컬럼 | Atom XML 경로 | 주의 |
|----------|--------------|------|
| 제목 | `<entry><title>` | CDATA, 줄바꿈 포함 가능 — `\n` 제거 후 trim |
| 저자 | `<entry><author><name>` (복수) | 첫 번째 `<author>` 태그가 1st author. 총 수는 `<author>` count |
| arXiv ID | `<entry><id>` URL에서 추출 | `https://arxiv.org/abs/2401.12345v2` → `2401.12345` (버전 제거) |
| 발표처 | `<entry><arxiv:journal_ref>` | 없으면 `n/a`. `xmlns:arxiv="http://arxiv.org/schemas/atom"` 네임스페이스 주의 |
| DOI | `<entry><arxiv:doi>` | 없는 경우가 많음. 존재 시 `^10\.\d{4,}/` 검증 |
| abstract | `<entry><summary>` | 줄바꿈 포함. 출력 시 1문장만 발췌 (fair use) |
| 발행일 | `<entry><published>` | ISO 8601. 연도만 추출 시 `[:4]` 슬라이스 |
| 업데이트일 | `<entry><updated>` | 버전 업데이트 시 변경됨 — `published`를 연도 기준으로 사용 |
| arXiv 카테고리 | `<entry><arxiv:primary_category term="cs.SE">` | term 속성값이 카테고리 코드 |

### 10.2 arXiv XML 네임스페이스 선언

arXiv 응답 루트에 다음 네임스페이스가 선언된다. 파싱 시 `arxiv:` 접두어 필드(`journal_ref`, `doi`, `primary_category`)에 사용된다.

```xml
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
```

### 10.3 arXiv rate-limit 준수 (ToU)

arXiv ToU: **3초당 1요청, 단일 연결**. Claude가 WebFetch로 arXiv를 호출할 때:

- 동일 API 내 다중 query를 병렬로 날리지 않는다 (ToU 위반).
- API 간 병렬은 허용: arXiv 1건 + OpenAlex 1건은 동시 실행 가능.
- 동일 쿼리를 하루 1회 이상 호출하지 않는다 (§18.3 in-memory cache).
- rate limit hit(HTTP 429) 시 지수 백오프: 5s → 10s → 20s → fallback.

---

## 11. 관련성 점수 공식 및 `--bias` 옵션 (§8.3 PLAN)

매트릭스 `관련성` 컬럼(★1~5)은 아래 공식으로 계산한다. Claude가 주관적으로 판단하지 않고 수치 기반으로 산출한다.

### 11.1 기본 점수 공식 (default balanced)

```
score = log(citations + 1) × recency_weight × source_count

recency_weight = max(0.5, 1 - (current_year - pub_year) × 0.1)
source_count   = {arXiv에서 발견: 1} + {S2에서 발견: 1} + {OA에서 발견: 1}  (1~3)
citations      = S2 citationCount 또는 OA cited_by_count (없으면 0)
current_year   = 검색 실행 연도
```

### 11.2 `--bias` 옵션 적용

| 옵션 | 공식 변형 | 효과 |
|------|----------|------|
| `--bias recency` | `score = log(citations+1) × recency_weight² × source_count` | 최신 논문 가중 강화 |
| `--bias citation` | `score = log(citations+1)² × recency_weight × source_count` | 높은 인용수 가중 강화 |
| `balanced` (기본값) | 위 기본 공식 | 최신성과 인용수 균형 |

### 11.3 ★ 등급 변환

| score 구간 | ★ 표시 |
|-----------|:------:|
| score ≥ 8 | ★★★★★ |
| 6 ≤ score < 8 | ★★★★ |
| 4 ≤ score < 6 | ★★★ |
| 2 ≤ score < 4 | ★★ |
| score < 2 | ★ |

> 인용수가 0이고 source_count가 1인 경우(단일 소스, 인용 없음)는 항상 ★ 이하.
> degraded mode에서 인용수가 n/a인 경우 `citations=0`으로 처리하고 결과에 `(citations n/a)` 주석을 붙인다.

---

## 12. rate-limit 안내 출력 정책 (§5.1 PLAN)

API 호출 중 rate limit이 발생하거나 응답 속도가 현저히 저하될 때, 출력에 포함하는 안내 문구 형식을 규정한다.

### 12.1 anonymous mode 배너 (항상 포함)

메인 출력 및 0건 출력 모두에서 제목 바로 아래에 다음 1줄을 포함한다.

```
> anonymous mode — rate limit 적용 가능 (무료 API 키 옵션 있음)
```

이 줄은 키 발급을 요구하는 것이 아니라, 익명 호출의 속도 한계를 소극적으로 알리는 것이다.

### 12.2 rate limit hit 시 출력

HTTP 429를 수신하거나 응답 timeout(개별 5s 초과)이 발생한 소스가 있을 때, `### 5. 3-source 교차 검증 로그`에 다음 형식으로 기록한다.

```
- API 응답 상태: arXiv 200 / S2 429 (rate limit, backoff 적용) / OpenAlex 200
- S2 재시도 결과: 5s 후 200 수신 / 또는 timeout — degraded mode 진입
```

### 12.3 환경변수 안내 (optional, 1줄만)

응답이 매우 느리거나 429가 반복될 경우에만, `### 5. 3-source 교차 검증 로그` 하단에 다음 1줄을 선택적으로 추가한다. 이 이상의 안내는 금지한다.

```
(속도 개선 옵션: SEMANTIC_SCHOLAR_API_KEY 또는 OPENALEX_MAILTO 환경변수 설정 — 모두 무료)
```

---

> **관련 파일**:
> - `sources.md` — 3 API 엔드포인트 + 응답 스키마 + 검증된 OpenAlex Topics ID
> - `query-strategies.md` — 쿼리 정제 + 중복 제거 + 관련성 점수 공식 상세
> - `mapping-algorithm.md` — 카탈로그 매핑 HIGH/MED/LOW 판정 알고리즘
> - `fallback.md` — Graceful Degradation + circuit breaker + 3-tier fallback 체인
> - `performance.md` — 동시성 모델 + timeout + rate-limit + in-memory cache
> - `testing.md` — 회귀 테스트 매트릭스 + fixture 위치 (`fixtures/` 50 케이스)
> - `PLAN-research-mode.md` — 전체 설계 문서 (읽기 전용, Phase 체크리스트 포함)
