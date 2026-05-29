# research 모드 — 외부 소스 레퍼런스

> **파일 역할**: dev-advisor `research` 모드가 사용하는 3개 외부 API의 엔드포인트, 응답 스키마, 속도 제한, 도메인 매핑, 사용 정책을 기술한다.
> **버전**: arXiv API v1.0 / Semantic Scholar Graph API v1 / OpenAlex API v1
> **최초 작성**: 2026-05-28 (Phase 2 사전 게이트 검증 통과 후 기록)
> **PLAN 참조**: `PLAN-research-mode.md` §5.1 (소스별 역할) + §5.2 (도메인별 매핑) + §10.1 (API 약관)

---

## 0. 무료 정책 절대 원칙

> **🆓 3 API 모두 완전 무료. 키 없이 anonymous 동작 보장.**

| 원칙 | 설명 |
|------|------|
| **키 없이도 동작 보장** | 3 API 모두 API 키 없이 anonymous 호출 가능. 키는 선택적 무료 옵션 |
| **사용자에게 키 발급 강요 금지** | "키를 발급해주세요" 등의 안내 출력 금지. 키 없으면 anonymous로 진행 + 1줄 소극적 안내만 |
| **유료 API 영원히 out-of-scope** | Web of Science / Scopus / IEEE Xplore / Semantic Scholar Premium 등 모두 제외 |
| **상용 MCP fallback 기본 OFF** | Exa AI 등 상용 유료 MCP는 default fallback에서 제거. 사용자 명시 동의 시에만 사용 |
| **키 누락 시 처리** | anonymous fallback + 응답 상단 1줄 안내: "anonymous mode — rate limit 적용" |

---

## 1. arXiv API

### 1.1 개요

arXiv는 Cornell University가 운영하는 오픈 프리프린트 서버다. 물리학, 수학, CS, 통계 등 분야의 미출판 논문을 publication-day 수준으로 제공한다. `research` 모드에서 **최신성 1순위** 소스로 사용한다.

### 1.2 엔드포인트

```
https://export.arxiv.org/api/query
```

- **프로토콜**: HTTPS 필수 (`http://` 사용 금지)
- **메서드**: GET
- **응답 포맷**: Atom 1.0 XML (JSON 아님 — 주의)

### 1.3 주요 요청 파라미터

| 파라미터 | 타입 | 설명 | 예시 |
|---------|------|------|------|
| `search_query` | string | 검색식 (`ti:`, `au:`, `abs:`, `cat:` 접두어 사용) | `ti:transformer+AND+cat:cs.LG` |
| `start` | int | 결과 오프셋 (default 0) | `0` |
| `max_results` | int | 최대 결과 수 (default 10, max 2000) | `10` |
| `sortBy` | string | 정렬 기준: `relevance`, `lastUpdatedDate`, `submittedDate` | `submittedDate` |
| `sortOrder` | string | 정렬 방향: `ascending`, `descending` | `descending` |

#### 검색식 접두어

| 접두어 | 검색 대상 |
|--------|----------|
| `ti:` | 제목 |
| `au:` | 저자 |
| `abs:` | 초록 |
| `cat:` | arXiv 카테고리 코드 |
| `all:` | 전체 필드 |

#### 예시 요청 URL

```
https://export.arxiv.org/api/query?search_query=ti:transformer+AND+cat:cs.LG&start=0&max_results=10&sortBy=submittedDate&sortOrder=descending
```

### 1.4 인증

**없음 (완전 무료)**. API 키, 토큰, 계정 등 일체 불필요.

### 1.5 Rate Limit (ToU 필수 준수)

| 규칙 | 값 | 비고 |
|------|-----|------|
| **요청 간격** | **3초당 1요청** | ToU 명시 — 위반 시 IP 차단 가능 |
| **동시 연결** | **단일 연결** | 병렬 호출 금지 |
| **동일 쿼리 재호출** | 하루 1회 권장 | 세션 내 in-memory cache로 회피 |

> **구현 주의**: arXiv는 동일 API 내 다중 쿼리를 병렬로 실행하면 ToU(단일 연결) 위반이다. arXiv 요청은 반드시 **직렬 throttled** 방식으로 실행한다. API 간(arXiv + OpenAlex) 병렬은 허용.

### 1.6 응답 스키마 (Atom 1.0 XML)

응답은 `<feed>` 루트 아래 `<entry>` 요소 목록으로 구성된다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom"
      xmlns:openSearch="http://a9.com/-/spec/opensearch/1.1/">
  <opensearch:totalResults>12345</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>10</opensearch:itemsPerPage>

  <entry>
    <id>http://arxiv.org/abs/2312.12345v2</id>
    <title>Attention Is All You Need</title>
    <summary>We propose a new simple network architecture...</summary>
    <published>2017-06-12T17:00:00Z</published>
    <updated>2023-08-02T10:00:00Z</updated>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <!-- ... 추가 저자 ... -->
    <arxiv:primary_category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <arxiv:doi>10.48550/arXiv.1706.03762</arxiv:doi>
    <arxiv:journal_ref>Advances in Neural Information Processing Systems 30 (2017)</arxiv:journal_ref>
    <link href="https://arxiv.org/abs/1706.03762" rel="alternate" type="text/html"/>
    <link href="https://arxiv.org/pdf/1706.03762" rel="related" type="application/pdf"/>
  </entry>
</feed>
```

### 1.7 주요 필드

| XML 경로 | 설명 | 환각 방지 주의 |
|----------|------|--------------|
| `entry/id` | arXiv URL (`http://arxiv.org/abs/<ID>vN`) — ID 추출: `abs/` 이후 문자열 | 응답 원문 그대로 사용 |
| `entry/title` | 논문 제목 | 응답 원문 그대로 사용 (재작성 금지) |
| `entry/summary` | 초록 (abstract) | 1~3문장만 인용 (fair use) |
| `entry/author/name` | 저자명 | 응답 원문 그대로. 변형 금지 |
| `entry/published` | 최초 제출일 (ISO 8601) | |
| `entry/updated` | 최근 버전 갱신일 | |
| `entry/arxiv:primary_category[@term]` | 주 분류 코드 (`cs.LG` 등) | |
| `entry/category[@term]` | 추가 분류 코드 (복수) | |
| `entry/arxiv:doi` | DOI (있는 경우 — `10.48550/arXiv.*` 포함) | `10.48550/arXiv.XXXX.XXXXX` 형태는 arXiv ID와 동일 논문 |
| `entry/arxiv:journal_ref` | 학술지/컨퍼런스 게재 정보 (있는 경우) | null 가능 |
| `entry/link[@rel="related"][@type="application/pdf"]/@href` | 무료 PDF URL | 화이트리스트: `arxiv.org`만 허용 |

### 1.8 arXiv ID 정규화

- 원본 형식: `http://arxiv.org/abs/2401.12345v2`
- 정규화: `2401.12345` (version 제거, URL prefix 제거)
- 구형 ID: `cs/0701001` 형태도 존재 (`<category>/YYMMNNN`)
- **arXiv DOI 매핑**: `10.48550/arXiv.2401.12345` → arXiv ID `2401.12345`와 **동일 논문** (중복 제거 시 병합)

### 1.9 CS 관련 주요 카테고리 코드

| 코드 | 분야 |
|------|------|
| `cs.AI` | Artificial Intelligence |
| `cs.LG` | Machine Learning |
| `cs.CL` | Computation and Language (NLP) |
| `cs.CV` | Computer Vision |
| `cs.SE` | Software Engineering |
| `cs.PL` | Programming Languages |
| `cs.DS` | Data Structures and Algorithms |
| `cs.CC` | Computational Complexity |
| `cs.CR` | Cryptography and Security |
| `cs.DC` | Distributed, Parallel, and Cluster Computing |
| `cs.DB` | Databases |
| `cs.NE` | Neural and Evolutionary Computing |
| `cs.IR` | Information Retrieval |
| `cs.RO` | Robotics |
| `cs.SY` | Systems and Control |
| `cs.HC` | Human-Computer Interaction |
| `cs.GT` | Computer Science and Game Theory |
| `cs.NA` | Numerical Analysis |
| `cs.NI` | Networking and Internet Architecture |
| `cs.OS` | Operating Systems |
| `stat.ML` | Statistics — Machine Learning |

---

## 2. Semantic Scholar API

### 2.1 개요

Semantic Scholar는 Allen Institute for AI(AI2)가 운영하는 학술 검색 엔진이다. 인용수(`citationCount`), 영향력 있는 인용(`influentialCitationCount`), AI 생성 TLDR 요약 등 독자적인 메타데이터를 제공한다. `research` 모드에서 **권위 1순위** 소스로 사용한다.

### 2.2 엔드포인트

```
https://api.semanticscholar.org/graph/v1/paper/search
```

- **메서드**: GET
- **응답 포맷**: JSON
- **`fields=` 파라미터 필수**: 명시하지 않으면 `paperId`와 `title`만 반환

### 2.3 주요 요청 파라미터

| 파라미터 | 타입 | 설명 | 예시 |
|---------|------|------|------|
| `query` | string | 검색어 | `transformer attention mechanism` |
| `fields` | string | 콤마 구분 응답 필드 목록 (**필수**) | 아래 권장 필드 참조 |
| `limit` | int | 최대 결과 수 (default 10, max 100) | `10` |
| `offset` | int | 오프셋 | `0` |
| `publicationTypes` | string | 논문 유형 필터 (`JournalArticle`, `Conference`, `Preprint` 등) | `JournalArticle,Conference` |
| `year` | string | 연도 범위 | `2020-2026` |
| `fieldsOfStudy` | string | 분야 필터 | `Computer Science` |

#### 권장 `fields=` 값

```
paperId,title,abstract,authors,year,venue,publicationDate,citationCount,influentialCitationCount,externalIds,openAccessPdf,tldr,fieldsOfStudy,publicationTypes
```

#### 예시 요청 URL

```
https://api.semanticscholar.org/graph/v1/paper/search?query=transformer+attention&fields=paperId,title,abstract,authors,year,venue,citationCount,influentialCitationCount,externalIds,openAccessPdf,tldr,fieldsOfStudy&limit=10&year=2020-2026
```

### 2.4 인증

| 모드 | 방법 | Rate Limit | 비용 |
|------|------|-----------|------|
| **무인증 (anonymous)** | 헤더 없음 | Shared throttling (느리지만 동작함) | **무료** |
| **무료 API 키** | `x-api-key: <key>` 헤더 | 1 RPS 보장 | **무료 발급** |

- 무인증도 정상 호출 가능. 단, shared throttling으로 429 응답을 받을 수 있음
- **429 응답 = 정책상 무료 (anonymous shared throttling)** — 유료 전환 아님
- 키 발급: `https://www.semanticscholar.org/product/api` (무료)
- 런타임 환경변수: `SEMANTIC_SCHOLAR_API_KEY` (있으면 사용, 없으면 anonymous)

### 2.5 응답 스키마 (JSON)

```json
{
  "total": 12345,
  "offset": 0,
  "next": 10,
  "data": [
    {
      "paperId": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
      "title": "Attention Is All You Need",
      "abstract": "The dominant sequence transduction models are based on complex recurrent...",
      "authors": [
        {"authorId": "1741101", "name": "Ashish Vaswani"},
        {"authorId": "1700325", "name": "Noam Shazeer"}
      ],
      "year": 2017,
      "venue": "Neural Information Processing Systems",
      "publicationDate": "2017-06-12",
      "citationCount": 120453,
      "influentialCitationCount": 18234,
      "externalIds": {
        "DOI": "10.48550/arXiv.1706.03762",
        "ArXiv": "1706.03762",
        "MAG": "2963403868",
        "DBLP": "journals/corr/VaswaniSPUJGKP17",
        "PubMed": null
      },
      "openAccessPdf": {
        "url": "https://arxiv.org/pdf/1706.03762",
        "status": "GREEN"
      },
      "tldr": {
        "model": "tldr@v2.0.0",
        "text": "A new simple network architecture, the Transformer, based solely on attention mechanisms..."
      },
      "fieldsOfStudy": ["Computer Science"],
      "publicationTypes": ["JournalArticle", "Conference"]
    }
  ]
}
```

### 2.6 주요 필드

| 필드 경로 | 설명 | 환각 방지 주의 |
|----------|------|--------------|
| `data[].paperId` | S2 고유 ID (40자 hex) | 정규식: `^[a-f0-9]{40}$` |
| `data[].title` | 제목 | 응답 원문 그대로 |
| `data[].abstract` | 초록 | 1~3문장만 인용 (null 가능) |
| `data[].authors[].name` | 저자명 | 응답 원문 그대로. 변형 금지 |
| `data[].year` | 출판 연도 (int) | 응답 원문 그대로 |
| `data[].venue` | 발표처 (컨퍼런스/학술지명) | 응답 원문 그대로. Claude 추측 금지 |
| `data[].citationCount` | 총 인용수 | 응답 원문 그대로. Claude 추정 금지 |
| `data[].influentialCitationCount` | 영향력 있는 인용수 (S2 독자 지표) | null 가능 |
| `data[].externalIds.DOI` | DOI (있는 경우) | null 가능 |
| `data[].externalIds.ArXiv` | arXiv ID (있는 경우) | null 가능 |
| `data[].openAccessPdf.url` | 무료 PDF URL (있는 경우) | 화이트리스트: `arxiv.org`, `semanticscholar.org`, `doi.org`만 |
| `data[].tldr.text` | AI 생성 TLDR 요약 | **null 가능** — null이면 abstract 첫 문장 또는 `n/a` |
| `data[].fieldsOfStudy` | 분야 배열 | 도메인 매핑에 사용 |

### 2.7 `fieldsOfStudy` 주요 값

| 값 | 설명 |
|----|------|
| `"Computer Science"` | 컴퓨터 과학 전반 |
| `"Software Engineering"` | 소프트웨어 엔지니어링 |
| `"Computer Security and Cryptography"` | 보안 및 암호학 |
| `"Programming Languages"` | 프로그래밍 언어론 |
| `"Distributed Computing"` | 분산 컴퓨팅 |
| `"Database Systems"` | 데이터베이스 |
| `"Software Testing"` | 소프트웨어 테스팅 |
| `"Machine Learning"` | 머신러닝 |
| `"Artificial Intelligence"` | 인공지능 |

---

## 3. OpenAlex API

### 3.1 개요

OpenAlex는 Our Research가 운영하는 완전 오픈 학술 메타데이터 데이터베이스다. 논문, 저자, 기관, 학술지, 개념을 그래프 형태로 제공한다. `research` 모드에서 **메타데이터 보완** (Topics 매핑, `is_retracted` 철회 여부, cross-reference ID) 소스로 사용한다.

### 3.2 엔드포인트

```
https://api.openalex.org/works
```

- **메서드**: GET
- **응답 포맷**: JSON
- **인증**: 완전 무료, 인증 없음

### 3.3 주요 요청 파라미터

| 파라미터 | 타입 | 설명 | 예시 |
|---------|------|------|------|
| `search` | string | 전문 검색어 | `transformer attention` |
| `filter` | string | 필터 조건 (콜론 문법 필수 — 아래 참조) | `cited_by_count:>1000,topics.id:T12490` |
| `sort` | string | 정렬: `cited_by_count:desc`, `publication_date:desc` 등 | `cited_by_count:desc` |
| `per-page` | int | 페이지당 결과 수 (max 200) | `10` |
| `page` | int | 페이지 번호 | `1` |
| `select` | string | 반환 필드 선택 (콤마 구분) | `id,doi,title,authorships,publication_year` |

#### 필터 문법 (콜론 사용 — 중요)

```
# 올바른 문법 (콜론 사용)
filter=cited_by_count:>1000,topics.id:T12490

# 잘못된 문법 (등호 사용 — 동작 안 함)
filter=cited_by_count>1000,topics.id=T12490
```

#### 예시 요청 URL

```
https://api.openalex.org/works?search=transformer+attention&filter=cited_by_count:>100,topics.id:T10320&sort=cited_by_count:desc&per-page=10
```

### 3.4 인증

| 모드 | 방법 | 비용 |
|------|------|------|
| **anonymous** | 헤더 없음 | **완전 무료** (동작 보장) |
| **polite pool (권장)** | `mailto:` 포함 User-Agent 헤더 | **무료** — `User-Agent: dev-advisor/1.0 (mailto:user@example.com)` |
| **API 키** | `api_key=<key>` 쿼리 파라미터 | **무료 발급** |

- **Codex가 v0.3에서 "credit 모델 필요"라고 주장했으나 Phase 2 실측 검증(2026-05-28)에서 anonymous 200 응답 확인 — 주장 폐기됨**
- 런타임 환경변수: `OPENALEX_MAILTO`, `OPENALEX_API_KEY` (있으면 사용, 없으면 anonymous)
- **SKILL.md/markdown에 이메일·키 하드코딩 금지**

### 3.5 응답 스키마 (JSON)

```json
{
  "meta": {
    "count": 12345,
    "db_response_time_ms": 42,
    "page": 1,
    "per_page": 10
  },
  "results": [
    {
      "id": "https://openalex.org/W2741809807",
      "doi": "https://doi.org/10.48550/arXiv.1706.03762",
      "title": "Attention Is All You Need",
      "publication_year": 2017,
      "authorships": [
        {
          "author_position": "first",
          "author": {"id": "https://openalex.org/A5023888391", "display_name": "Ashish Vaswani"},
          "institutions": [{"display_name": "Google Brain"}]
        }
      ],
      "host_venue": {
        "id": "https://openalex.org/V1983995261",
        "display_name": "Neural Information Processing Systems",
        "type": "conference"
      },
      "cited_by_count": 120453,
      "is_retracted": false,
      "is_paratext": false,
      "ids": {
        "openalex": "https://openalex.org/W2741809807",
        "doi": "https://doi.org/10.48550/arXiv.1706.03762",
        "mag": "2741809807",
        "arxiv": "https://arxiv.org/abs/1706.03762"
      },
      "topics": [
        {
          "id": "https://openalex.org/T10320",
          "display_name": "Neural Networks and Applications",
          "score": 0.9997,
          "subfield": {"display_name": "Artificial Intelligence"},
          "field": {"display_name": "Computer Science"},
          "domain": {"display_name": "Physical Sciences"}
        }
      ],
      "open_access": {
        "is_oa": true,
        "oa_url": "https://arxiv.org/pdf/1706.03762"
      },
      "concepts": []
    }
  ]
}
```

### 3.6 주요 필드

| 필드 경로 | 설명 | 환각 방지 주의 |
|----------|------|--------------|
| `results[].id` | OpenAlex Work ID URL (`https://openalex.org/WXXXXXXXXX`) | 정규식: `^W\d{8,}$` (URL에서 추출) |
| `results[].doi` | DOI URL (`https://doi.org/10.XXXX/...`) | null 가능. 정규화: prefix 제거 후 `^10\.\d{4,}/` |
| `results[].title` | 제목 | 응답 원문 그대로 |
| `results[].publication_year` | 출판 연도 (int) | 응답 원문 그대로 |
| `results[].authorships[].author.display_name` | 저자명 | 응답 원문 그대로. 변형 금지 |
| `results[].host_venue.display_name` | 발표처 | 응답 원문 그대로 |
| `results[].cited_by_count` | 인용수 | 응답 원문 그대로. Claude 추정 금지 |
| `results[].is_retracted` | 철회 여부 (bool) | **true이면 매트릭스 상단 ⚠️ 표시 + 신뢰성 필드에 "RETRACTED" 명시** |
| `results[].is_paratext` | 파라텍스트 여부 (bool) | true이면 출력 제외 (목차, 서문 등) |
| `results[].ids.doi` | DOI (중복 제거에 사용) | null 가능 |
| `results[].ids.arxiv` | arXiv URL (중복 제거에 사용) | null 가능 |
| `results[].ids.mag` | Microsoft Academic ID | |
| `results[].topics[].id` | OpenAlex Topic ID URL (`https://openalex.org/TXXXXX`) | 검증된 9개 ID만 사용 (§4) |
| `results[].topics[].display_name` | Topic 표시명 | |
| `results[].open_access.oa_url` | 무료 PDF URL (있는 경우) | 화이트리스트 도메인만 |

### 3.7 OpenAlex Concepts deprecated 경고

> **⚠️ `concepts` 필드는 deprecated. `topics` 필드를 사용해야 한다.**

- OpenAlex는 2024년부터 `concepts` 기반 분류를 deprecated 처리하고 `topics` 기반으로 전환
- `concepts` 필드는 응답에 빈 배열(`[]`)로 오거나 레거시 값이 남아있을 수 있음
- **`topics.id` 필터만 사용 금지**: 반드시 `§4 도메인별 매핑 표`에서 검증된 Topic ID 사용
- `concepts.id` 기반 필터(`concepts.id:C...`) 사용 금지 — deprecated API에 의존하게 됨

---

## 4. OpenAlex Topics ID 매핑 표 (Phase 2 검증 완료)

> **검증 일자**: 2026-05-28
> **검증 방법**: `curl -s "https://api.openalex.org/topics?search=<keyword>&per-page=3"` 실측 호출
> **상태**: 9개 도메인 모두 200 응답 확인 + display_name 의도 일치 검증 완료

| 카탈로그 도메인 | arXiv 카테고리 | Semantic Scholar `fieldsOfStudy` | OpenAlex Topic ID | Topic 표시명 |
|----------------|--------------|----------------------------------|-------------------|-------------|
| **Patterns** (Software Engineering) | `cs.SE` | `"Software Engineering"` | `T12490` | Software Engineering and Design Patterns |
| **Algorithms** (CS Theory) | `cs.DS`, `cs.CC` | `"Computer Science"` | `T11269` | Algorithms and Data Compression |
| **Languages** (Programming) | `cs.PL` | `"Programming Languages"` | `T10126` | Logic, programming, and type systems |
| **Security** | `cs.CR` | `"Computer Security and Cryptography"` | `T10734` | Information and Cyber Security |
| **Principles** (SE Theory) | `cs.SE` | `"Software Engineering"` | `T10260` | Software Engineering Research |
| **Quality** (Testing/QA) | `cs.SE` | `"Software Testing"` | `T10743` | Software Testing and Debugging Techniques |
| **AI/ML** | `cs.AI`, `cs.LG`, `cs.CL` | `"Machine Learning"` | `T10320` | Neural Networks and Applications |
| **Distributed** | `cs.DC` | `"Distributed Computing"` | `T10715` | Distributed and Parallel Computing Systems |
| **Database** | `cs.DB` | `"Database Systems"` | `T10317` | Advanced Database Systems and Queries |

### 4.1 Topics ID 사용 규칙

- **이 표의 9개 ID만 사용** — 임의로 다른 Topic ID를 사용하거나 추측하지 않는다
- 새 도메인이 추가되면 Phase 2 게이트와 동일한 실측 검증 절차를 거친 후 이 표에 등재한다
- 필터 문법: `filter=topics.id:T12490` (콜론 사용, `https://openalex.org/` prefix 제거)

### 4.2 Topics ID 검증 절차 (신규 도메인 추가 시)

```bash
# Step 1: 키워드로 Topic 검색
curl -s "https://api.openalex.org/topics?search=software+design+patterns&per-page=3" \
  | python3 -c "import sys,json; [print(t['id'], t['display_name']) for t in json.load(sys.stdin)['results']]"

# Step 2: Topic 상세 확인 (subfield/field/domain 일치 여부)
curl -s "https://api.openalex.org/topics/T12490" \
  | python3 -c "import sys,json; t=json.load(sys.stdin); print(t['display_name'], t['subfield']['display_name'], t['field']['display_name'])"

# Step 3: 의도한 분야와 일치 확인 후 이 표에 등재
```

---

## 5. Phase 2 사전 게이트 검증 로그

> **검증 일자**: 2026-05-28
> **목적**: 키 없이 anonymous 호출 가능 여부 실측 확인 (무료 정책 절대 원칙 검증)

| API | HTTP 상태 | 결과 | 비고 |
|-----|----------|------|------|
| **arXiv** | `200 OK` | ✅ 통과 | Atom XML 응답 정상 수신. 인증 없음. |
| **OpenAlex** | `200 OK` | ✅ 통과 | JSON 응답 정상 수신. anonymous 동작 확인. Codex "credit 모델" 주장 **폐기 확정** |
| **Semantic Scholar** | `429 Too Many Requests` | ✅ 정책상 무료 | anonymous shared throttling으로 인한 일시적 속도 제한. 유료 전환 아님. 키 없이도 재시도 시 동작함. |

**결론**: 3 API 모두 키 없이 anonymous 동작 확인. 무료 정책 원칙 유지. Phase 3 진입 승인.

---

## 6. 3-source 비교 매트릭스

| 항목 | arXiv | Semantic Scholar | OpenAlex |
|------|-------|-----------------|----------|
| **주 강점** | 최신성 (publication-day) | 인용수 + TLDR + 영향력 지표 | 메타데이터 완성도 + Topics |
| **커버리지** | CS/Physics/Math/Bio 프리프린트 | 2억+ 논문 (다학제) | 2.5억+ 논문 (오픈 그래프) |
| **인용수** | 없음 | ✅ `citationCount` + `influentialCitationCount` | ✅ `cited_by_count` |
| **TLDR** | 없음 | ✅ (AI 생성, null 가능) | 없음 |
| **철회 여부** | 없음 | 없음 | ✅ `is_retracted` |
| **무료 PDF** | ✅ PDF 직링크 | ✅ `openAccessPdf.url` | ✅ `open_access.oa_url` |
| **응답 포맷** | Atom 1.0 XML | JSON | JSON |
| **인증** | 없음 | 없음 / 무료 키 | 없음 / 무료 키 / polite pool |
| **Rate Limit** | 3초당 1요청, 단일 연결 (ToU) | shared throttling / 1 RPS (키) | 관대함 (polite pool 권장) |
| **Topics/분류** | arXiv 카테고리 코드 | `fieldsOfStudy` 배열 | `topics` 배열 (검증된 ID 필수) |
| **Cross-ref ID** | arXiv ID, DOI | `externalIds` (DOI/ArXiv/MAG/PubMed) | `ids` (DOI/MAG/ArXiv) |
| **schema 버전** | **v1.0** | **Graph API v1** | **v1** |

---

## 7. Rate Limit 및 Polite Usage 가이드

### 7.1 API별 Rate Limit 요약

| API | 무인증 | 키 사용 시 | 비고 |
|-----|--------|-----------|------|
| arXiv | **3초당 1요청, 단일 연결** | 동일 (키 없음) | ToU 위반 시 IP 차단 가능 |
| Semantic Scholar | Shared throttling (보장 없음) | 1 RPS | 429 응답 = 정책상 무료 |
| OpenAlex | 관대함 | polite pool 우선 | mailto 헤더로 polite pool 진입 |

### 7.2 구현 요구사항

| 요구사항 | 설명 |
|---------|------|
| **arXiv 직렬 throttled** | arXiv 요청은 동일 API 내 병렬 금지. API 간(arXiv + OpenAlex 동시) 병렬은 허용 |
| **arXiv 동일 쿼리 1일 캐시** | 세션 내 in-memory dedup으로 동일 쿼리 중복 호출 방지 |
| **S2 429 처리** | 429 응답 시 지수 백오프 재시도 (최대 3회). 3회 초과 시 degraded mode (§fallback.md) |
| **개별 API timeout 5s** | WebFetch 개별 호출 timeout 5초. 초과 시 해당 소스 건너뛰고 partial result |
| **총 검색 timeout 20s** | 3 API 합산 총 20초. 초과 시 수신된 결과만으로 출력 |
| **rate-limit aware 필수** | LLM 런타임이 자동으로 rate limit을 지켜준다고 가정 금지 |

### 7.3 Polite Usage

- arXiv ToU: `https://arxiv.org/help/api/tou`
- Semantic Scholar: 학술/비상업 목적 사용만 허용
- OpenAlex: 완전 오픈 (CC0). polite pool은 `User-Agent: <app>/<version> (mailto:<email>)` 형식

---

## 8. 중복 제거 알고리즘 요약

3-source 검색 결과를 병합할 때 아래 우선순위로 동일 논문을 감지한다.

1. **DOI 정규화 일치**: lowercase + `https://doi.org/` prefix 제거 + URL decode → 일치 시 동일 논문
   - 함정: preprint DOI vs published DOI가 다를 수 있음 → 제목 + 저자로 cross-check
2. **arXiv ID 정규화**: `2401.12345v2` → `2401.12345` (version 제거) → 일치 시 동일 논문
3. **arXiv DOI 매핑**: `10.48550/arXiv.2401.12345` → arXiv ID `2401.12345`와 **동일 논문으로 병합**
4. **제목 유사도 > 0.90** + 첫 저자 last name 일치 → 병합 후보
   - 0.85~0.90 경계: 분리 표시 + 검증 로그에 기록
5. **외부 ID 교차 참조**: S2 `externalIds` + OpenAlex `ids`의 공통 DOI/arXiv ID로 보강
6. **출처 우선순위 (메타 완성도 기준)**: Semantic Scholar > OpenAlex > arXiv

상세 알고리즘: `mapping-algorithm.md` 참조.

---

## 9. 환각 방지 체크리스트

research 모드 매트릭스 행 생성 시 반드시 준수:

| 검사 항목 | 규칙 |
|---------|------|
| **Identifier 필수** | 모든 행은 DOI / arXiv ID / S2 paperId / OpenAlex Work ID 중 최소 1개 존재 |
| **DOI 정규식** | `^10\.\d{4,}/` |
| **arXiv ID 정규식** | `^\d{4}\.\d{4,5}(v\d+)?$` 또는 `^[a-z-]+/\d{7}(v\d+)?$` |
| **S2 paperId 정규식** | `^[a-f0-9]{40}$` |
| **OpenAlex Work ID 정규식** | `^W\d{8,}$` (URL에서 ID 부분 추출 후) |
| **저자명** | API 응답 원문 그대로. 변형/번역/축약 금지 |
| **인용수** | S2 또는 OpenAlex 응답 값만 사용. Claude 추정 금지 |
| **발표처** | API 응답의 `venue` / `host_venue.display_name` 원문. 추측 금지 |
| **TLDR null 처리** | null이면 abstract 첫 문장 사용. 없으면 `n/a` 표기 |
| **URL 화이트리스트** | `arxiv.org`, `doi.org`, `semanticscholar.org`, `openalex.org` 도메인만 출력 |
| **Topics ID** | §4 표의 9개 검증된 ID만 사용. 임의 추측 금지 |
| **카탈로그 매핑** | `catalog-index.json` 실제 ID 목록과 대조 후에만 인용 |
| **Claude cutoff 지식 혼입 금지** | "선택/판정" 6필드 작성 시 raw API 응답만 사용 |
| **철회 논문** | `is_retracted=true` 이면 ⚠️ RETRACTED 표시 |

---

## 10. API 약관 요약 (법적 고려)

| API | 약관 URL | 핵심 제약 |
|-----|---------|----------|
| arXiv | `https://arxiv.org/help/api/tou` | 3초당 1요청, 단일 연결. 상업 목적 직접 사용 제한 |
| Semantic Scholar | `https://www.semanticscholar.org/product/api` | 학술/비상업 목적. 키 없이 사용 가능 |
| OpenAlex | `https://openalex.org/about` | CC0 완전 오픈. polite pool 권장 |

**인용 표기 원칙**:
- 모든 논문은 DOI / arXiv ID / S2 paperId / OpenAlex Work ID 중 하나 이상으로 인용
- Abstract/TLDR 인용 한도: 1~3문장 (full abstract 전재 금지 — fair use)
- PDF 링크: 화이트리스트 도메인만. 링크 안전성은 사용자 책임 (면책 문구 출력)

---

> **schema 버전 명시** (변경 추적용):
> - arXiv API: **v1.0** (2026-05-28 기준)
> - Semantic Scholar Graph API: **v1** (2026-05-28 기준)
> - OpenAlex API: **v1** (2026-05-28 기준)
>
> API 응답 스키마가 변경된 경우 이 파일의 해당 섹션을 갱신하고 `scripts/verify-references.sh` 11번 블록을 재실행한다.
