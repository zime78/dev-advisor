# 쿼리 전략 가이드 (Query Strategies)

> **대상 파일**: `references/research/query-strategies.md`
> **버전**: v0.1 (PLAN-research-mode.md v0.5 §4.4 + §5.3 + §8.3 기반)
> **작성일**: 2026-05-28
> **참조**: §4.4 6단계 워크플로, §5.3 중복 제거 알고리즘, §8.3 관련성 점수 + bias 함수

---

## 1. 개요 (Overview)

`query-strategies.md`는 `research` 모드의 검색 파이프라인에서 **3가지 핵심 책임**을 명세한다.

| 책임 | 목적 | 해당 섹션 |
|------|------|-----------|
| **쿼리 정제** | 사용자 입력(한국어/약어/자유 질문)을 API에 최적화된 영문 검색어로 변환 | §2 |
| **중복 제거** | 3개 소스 교차 검색 결과에서 동일 논문 식별 + 병합 | §3 |
| **관련성 점수** | 매트릭스 정렬 가중치 계산 + `--bias` 옵션 처리 | §4 |

> **핵심 원칙**: 모든 검색어 변환 과정에서 **환각 금지** — Codex가 존재하지 않는 카탈로그 ID, arXiv 카테고리, OpenAlex Topic ID를 임의로 생성하지 않는다. 불확실한 경우 사용자에게 confirm 1회.

---

## 2. 쿼리 정제 규칙 (Query Refinement)

### 2.1 처리 순서

```
입력 수집 → 언어 감지 → 한국어 변환 → 약어 풀기 → boolean 처리 → 카탈로그 ID 매핑 → 정규화된 영문 키워드 확정
```

### 2.2 한국어 → 영어 변환

**규칙**:
- 한국어 입력이 감지되면 영문 후보 1~3개를 제시한다.
- 후보가 1개이고 명확한 경우: 자동 진행 (사용자 interrupt 없음).
- 후보가 2~3개이고 의미가 다를 경우: **사용자 confirm 1회** 후 진행.
  - confirm 없이 추측으로 진행하지 않는다.
- 기술 용어는 영문 원어를 우선한다.

**예시**:

| 한국어 입력 | 영문 변환 후보 | confirm 필요 여부 |
|------------|--------------|:-----------------:|
| `주의 메커니즘` | `attention mechanism` | 아니오 (단일 명확) |
| `변압기` | `transformer` | 아니오 |
| `분산 시스템 합의` | `distributed consensus` | 아니오 |
| `의존성 역전` | `dependency inversion` / `inversion of control` | **예** (의미 분기) |
| `테스트 자동화` | `test automation` / `automated testing` | **예** (범위 차이) |
| `검색 증강 생성` | `retrieval-augmented generation` | 아니오 |
| `대형 언어 모델 코드 생성` | `large language model code generation` | 아니오 |

**구현 절차**:
```
1. 한국어 감지: 입력에 유니코드 가-힣 범위 문자 존재 여부 확인
2. 기술 용어 우선 번역: 고유 명사·약어는 원어 유지 (예: CNN, BERT, SOLID)
3. 일반 한국어 단어는 의미 기반 영문 대응어 선택
4. 후보 2개+ 이고 의미 분기 시:
   → "다음 중 어느 의미인가요? (1) X (2) Y" 형식으로 1회 confirm
5. confirm 응답 또는 자동 진행 후 정규화된 영문 키워드 확정
```

### 2.3 약어 풀어쓰기 (Acronym Expansion)

API 검색 시 약어만 사용하면 관련 없는 결과가 섞일 수 있다.  
약어는 **풀어쓰기 + 약어 병기** 형식으로 쿼리를 확장한다.

**규칙**:
- 약어를 단독으로 검색하지 않는다. `"LLM"` → `"large language model"` 또는 `"LLM large language model"`.
- 도메인이 명확한 경우: 풀어쓰기만 사용.
- 도메인이 모호한 경우: 풀어쓰기 + 약어 병기 (arXiv는 boolean OR 활용).

**자주 사용되는 약어 풀어쓰기 표**:

| 약어 | 풀어쓰기 | arXiv 검색어 예 |
|------|---------|----------------|
| LLM | Large Language Model | `"large language model"` |
| RAG | Retrieval-Augmented Generation | `"retrieval-augmented generation"` |
| SRP | Single Responsibility Principle | `"single responsibility principle"` |
| DI | Dependency Injection | `"dependency injection"` |
| CI/CD | Continuous Integration Continuous Deployment | `"continuous integration" "continuous deployment"` |
| RLHF | Reinforcement Learning from Human Feedback | `"reinforcement learning human feedback"` |
| MoE | Mixture of Experts | `"mixture of experts"` |
| SSM | State Space Model | `"state space model"` |
| GNN | Graph Neural Network | `"graph neural network"` |
| LoRA | Low-Rank Adaptation | `"low-rank adaptation"` |

> 위 표에 없는 약어는 Codex가 임의 추측하지 않고 사용자에게 confirm 1회 또는 약어+풀어쓰기 병기로 진행한다.

### 2.4 boolean 연산자 처리

arXiv API (`export.arxiv.org/api/query`)는 `query` 파라미터에 Lucene 스타일 boolean 연산자를 지원한다.

**지원 연산자**:

| 연산자 | arXiv 문법 | S2 문법 | 비고 |
|--------|-----------|---------|------|
| AND | `AND` (대문자 필수) | space (묵시적 AND) | 두 용어 모두 포함 |
| OR | `OR` (대문자 필수) | 미지원 (단일 쿼리) | 대안 표현 포함 |
| NOT | `ANDNOT` | 미지원 | 특정 용어 제외 |
| 정확 일치 | `"..."` 따옴표 | `"..."` 따옴표 | 구문 검색 |
| 필드 한정 | `ti:`, `au:`, `abs:` | — | arXiv 전용 |

**필드 한정자** (arXiv 전용):
- `ti:"attention mechanism"` — 제목에서만 검색
- `abs:"transformer architecture"` — abstract에서만 검색
- `au:Vaswani` — 저자명 검색
- 복합: `ti:transformer AND abs:attention` — 제목 + abstract

**사용 예시**:
```
입력: "transformer OR attention mechanism"
arXiv 변환: ti:"transformer" OR ti:"attention mechanism"
S2 변환:    "transformer attention mechanism" (OR 미지원, 병합 쿼리)
OpenAlex:   filter=title.search:transformer|attention
```

**실패 패턴 회피**:
- arXiv에서 소문자 `and`, `or`는 연산자가 아닌 단어로 처리됨 → **반드시 대문자** 사용.
- 괄호 그룹은 `(transformer OR attention) AND neural network` 형식으로 사용.
- S2는 boolean 구문을 지원하지 않으므로, OR 표현이 필요하면 쿼리를 2회 분리 호출 (단, 동일 API 직렬 throttle 준수).

### 2.5 카탈로그 ID 매핑

사용자가 카탈로그 ID(예: `/algorithm transformer`, `/pattern singleton`)를 입력한 경우, 해당 항목의 실제 키워드를 `catalog-index.json`에서 조회하여 검색어를 보강한다.

**도구 호출**:
```bash
# catalog-index.json SSoT — 반드시 이 파일을 기준으로 조회
python3 scripts/lookup-catalog.py <domain> search <keyword>
```

**예시**:
```bash
# 입력: /dev-advisor research transformer
python3 scripts/lookup-catalog.py algorithm search transformer
# 출력: algorithm/transformer — "Transformer architecture, attention mechanism, encoder-decoder"

python3 scripts/lookup-catalog.py pattern search singleton
# 출력: pattern/singleton — "Singleton pattern, creational, instance management"
```

**규칙**:
- `catalog-index.json`에 존재하는 ID만 카탈로그 매핑 후보로 사용한다.
- 존재하지 않는 ID를 추측하여 참조하지 않는다 (환각 금지 — §5.4).
- 매핑 결과가 없으면 자유 질문으로 처리하여 계속 진행한다.

### 2.6 정규화된 영문 키워드 우선

모든 정제 단계를 거친 후 확정된 **정규화된 영문 키워드**를 API 검색에 사용한다.

**정규화 체크리스트**:
- [ ] 한국어 제거 (영문 변환 완료)
- [ ] 약어 풀어쓰기 완료
- [ ] 불필요한 관사/전치사 제거 (a, the, of, in 등은 arXiv API에서 noise)
- [ ] 핵심 기술 용어 2~5개로 집중 (10단어 초과 쿼리는 관련성 저하)
- [ ] 공백은 `+` 또는 `%20` URL 인코딩 적용 (Codex web 도구 호출 시)

---

## 3. 도메인별 검색 전략 매핑

> `references/research/sources.md` §5와 동기화. OpenAlex Topic ID는 Phase 2 사전 검증 통과 후 기록됨 (`*(ID 검증 필요)*` 표시 항목은 실측 전).

### 3.1 카탈로그 도메인 → API 전략 매핑 표

| 카탈로그 도메인 | arXiv 카테고리 | Semantic Scholar `fieldsOfStudy` | OpenAlex Topic (사전 검증 대상) |
|----------------|---------------|----------------------------------|-------------------------------|
| **Patterns** (Software Engineering) | `cs.SE` | `"Software Engineering"` | Topic: Software Design Patterns *(ID 검증 필요)* |
| **Algorithms** (CS Theory) | `cs.DS`, `cs.CC` | `"Computer Science"` | Topic: Algorithm Design and Analysis *(ID 검증 필요)* |
| **Languages** (Programming) | `cs.PL` | `"Programming Languages"` | Topic: Programming Languages and Compilers *(ID 검증 필요)* |
| **Security** | `cs.CR` | `"Computer Security and Cryptography"` | Topic: Computer Security *(ID 검증 필요)* |
| **Principles** (SE Theory) | `cs.SE` | `"Software Engineering"` | Topic: Software Engineering *(ID 검증 필요)* |
| **Quality** (Testing/QA) | `cs.SE` | `"Software Testing"` | Topic: Software Testing *(ID 검증 필요)* |
| **AI/ML** 패턴·알고리즘 | `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV` | `"Machine Learning"` | Topic: Machine Learning (`T10320`) *(검증 대상)* |
| **Distributed Systems** | `cs.DC` | `"Distributed Computing"` | Topic: Distributed Computing *(ID 검증 필요)* |
| **Database** | `cs.DB` | `"Database Systems"` | Topic: Database Systems *(ID 검증 필요)* |

> **경고**: OpenAlex Concepts는 deprecated. 반드시 **Topics API** 기반으로 검색한다.  
> Topic ID 사전 검증 절차: `GET https://api.openalex.org/topics?search=<keyword>&per-page=3`  
> — 검증 통과 ID만 `references/research/sources.md`에 기록하여 SSoT로 유지.

### 3.2 arXiv 카테고리 전체 참조

| 카테고리 코드 | 분야 |
|:------------:|------|
| `cs.AI` | Artificial Intelligence |
| `cs.CL` | Computation and Language (NLP) |
| `cs.CV` | Computer Vision and Pattern Recognition |
| `cs.LG` | Machine Learning |
| `cs.SE` | Software Engineering |
| `cs.PL` | Programming Languages |
| `cs.DS` | Data Structures and Algorithms |
| `cs.CC` | Computational Complexity |
| `cs.CR` | Cryptography and Security |
| `cs.DC` | Distributed, Parallel, and Cluster Computing |
| `cs.DB` | Databases |
| `cs.NE` | Neural and Evolutionary Computing |
| `cs.RO` | Robotics |
| `cs.HC` | Human-Computer Interaction |
| `cs.IR` | Information Retrieval |
| `stat.ML` | Statistics - Machine Learning |

### 3.3 API 쿼리 구성 예시 (도메인별)

**AI/ML 주제 (예: transformer)**:
```
arXiv:
  URL: https://export.arxiv.org/api/query
  params:
    search_query: ti:"transformer attention" AND (cat:cs.LG OR cat:cs.AI)
    start: 0
    max_results: 20
    sortBy: submittedDate
    sortOrder: descending

Semantic Scholar:
  URL: https://api.semanticscholar.org/graph/v1/paper/search
  params:
    query: transformer attention mechanism
    fields: title,authors,year,citationCount,externalIds,venue,openAccessPdf,tldr
    fieldsOfStudy: Computer Science,Machine Learning
    limit: 20

OpenAlex:
  URL: https://api.openalex.org/works
  params:
    filter: title.search:transformer,topics.id:T10320
    sort: cited_by_count:desc
    per-page: 20
    mailto: (선택적 — 무료 polite pool 옵션)
```

**보안 주제 (예: zero-knowledge proof)**:
```
arXiv:
  search_query: ti:"zero-knowledge proof" AND cat:cs.CR
  sortBy: submittedDate, sortOrder: descending

Semantic Scholar:
  query: zero-knowledge proof cryptography
  fieldsOfStudy: Computer Security and Cryptography

OpenAlex:
  filter: title.search:zero-knowledge,topics.id:<CS 보안 Topic ID>
```

**소프트웨어 패턴 주제 (예: CQRS)**:
```
arXiv:
  search_query: abs:"CQRS" OR abs:"command query responsibility segregation" AND cat:cs.SE

Semantic Scholar:
  query: CQRS command query responsibility segregation
  fieldsOfStudy: Software Engineering

OpenAlex:
  filter: title.search:CQRS OR command query segregation,topics.id:<SE Topic ID>
```

---

## 4. 중복 제거 알고리즘 (Deduplication Algorithm)

> **출처**: PLAN §5.3 (v0.3 —Codex P1: arXiv DOI 매핑 추가, P2: 임계값 0.90)

3개 소스(arXiv, Semantic Scholar, OpenAlex)에서 수집된 논문 목록을 입력으로 받아 동일 논문을 병합한다.

### 4.1 의사코드 (Pseudocode)

```python
def deduplicate(papers: list[Paper]) -> list[Paper]:
    """
    3-source 교차 검색 결과에서 중복 논문을 제거하고 메타데이터를 병합한다.
    
    입력: arXiv / Semantic Scholar / OpenAlex 응답에서 파싱된 Paper 객체 목록
    출력: 중복 제거 + 출처 병합된 Paper 목록
    """

    # --- 단계 1: DOI 정규화 ---
    # lowercase 변환 + "https://doi.org/" prefix 제거 + URL decode
    # 정규화된 DOI가 일치하면 동일 논문으로 간주
    for paper in papers:
        if paper.doi:
            paper.normalized_doi = (
                paper.doi
                .lower()
                .removeprefix("https://doi.org/")
                .removeprefix("http://doi.org/")
                .strip()
            )
            paper.normalized_doi = urllib.parse.unquote(paper.normalized_doi)

    # --- 단계 2: arXiv ID 정규화 ---
    # "2401.12345v2" → "2401.12345" (버전 suffix 제거)
    # 정규화된 arXiv ID가 일치하면 동일 논문으로 간주
    ARXIV_VERSION_RE = re.compile(r"^(\d{4}\.\d{4,5})v\d+$")
    for paper in papers:
        if paper.arxiv_id:
            m = ARXIV_VERSION_RE.match(paper.arxiv_id)
            paper.normalized_arxiv_id = m.group(1) if m else paper.arxiv_id

    # --- 단계 3: arXiv DOI ↔ arXiv ID 매핑 ---
    # "10.48550/arXiv.2401.12345" 형태의 DOI는 arXiv ID "2401.12345"와 동일 논문
    ARXIV_DOI_RE = re.compile(r"^10\.48550/arxiv\.(\d{4}\.\d{4,5})", re.IGNORECASE)
    for paper in papers:
        if paper.normalized_doi:
            m = ARXIV_DOI_RE.match(paper.normalized_doi)
            if m:
                derived_arxiv_id = m.group(1)
                # normalized_arxiv_id가 없거나 일치하면 병합 대상
                if not paper.normalized_arxiv_id:
                    paper.normalized_arxiv_id = derived_arxiv_id

    # --- 단계 4: 제목 유사도 기반 후보 병합 ---
    # normalized title similarity > 0.90 + 첫 저자 last name 일치 → 병합
    # 충돌 시 (0.85~0.90 경계) → 분리 표시 + 검증 로그 기록
    def normalize_title(title: str) -> str:
        """소문자 변환 + 구두점 제거 + 공백 정규화"""
        return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()

    def first_author_last_name(paper: Paper) -> str:
        """첫 번째 저자의 성(last name) 추출"""
        if not paper.authors:
            return ""
        first = paper.authors[0]
        parts = first.split()
        return parts[-1].lower() if parts else ""

    def title_similarity(a: str, b: str) -> float:
        """Levenshtein 또는 token overlap 기반 유사도 (0.0~1.0)"""
        # 구현: difflib.SequenceMatcher 또는 rapidfuzz
        return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()

    groups = []  # list[list[Paper]] — 병합 그룹
    ungrouped = list(papers)

    for paper in ungrouped:
        matched_group = None
        for group in groups:
            representative = group[0]

            # DOI 일치 검사
            if (paper.normalized_doi and representative.normalized_doi
                    and paper.normalized_doi == representative.normalized_doi):
                matched_group = group
                break

            # arXiv ID 일치 검사
            if (paper.normalized_arxiv_id and representative.normalized_arxiv_id
                    and paper.normalized_arxiv_id == representative.normalized_arxiv_id):
                matched_group = group
                break

            # 제목 유사도 + 첫 저자 last name 검사
            sim = title_similarity(paper.title, representative.title)
            same_author = (
                first_author_last_name(paper) == first_author_last_name(representative)
            )
            if sim > 0.90 and same_author:
                matched_group = group
                break
            elif 0.85 <= sim <= 0.90 and same_author:
                # 충돌 경계 — 분리 표시 + 검증 로그 기록
                verification_log.append({
                    "type": "title_similarity_boundary",
                    "sim": sim,
                    "paper_a": representative.title,
                    "paper_b": paper.title,
                    "action": "kept_separate"
                })
                # 병합하지 않고 분리 유지

        if matched_group is not None:
            matched_group.append(paper)
        else:
            groups.append([paper])

    # --- 단계 5: 외부 ID 병합 (cross-reference 보강) ---
    # Semantic Scholar externalIds + OpenAlex ids 필드로 ID 보강
    # 예: S2가 DOI를 알고 arXiv가 DOI를 모를 때 → 병합 후 DOI 채움
    for group in groups:
        merged_ids = {}
        for paper in group:
            if hasattr(paper, "s2_external_ids") and paper.s2_external_ids:
                merged_ids.update(paper.s2_external_ids)  # DOI, arXiv, MAG, PubMed
            if hasattr(paper, "oa_ids") and paper.oa_ids:
                merged_ids.update(paper.oa_ids)           # DOI, MAG, OpenAlex, PubMed
        for paper in group:
            paper.enriched_ids = merged_ids

    # --- 단계 6: 출처 우선순위로 대표 메타데이터 선택 ---
    # 출처 우선순위: Semantic Scholar > OpenAlex > arXiv (메타데이터 완성도 기준)
    PRIORITY = {"s2": 0, "openalex": 1, "arxiv": 2}

    def merge_group(group: list[Paper]) -> Paper:
        """그룹 내 Papers를 출처 우선순위 기준으로 병합한다."""
        sorted_group = sorted(group, key=lambda p: PRIORITY.get(p.source, 99))
        primary = sorted_group[0]

        # 인용수: S2 또는 OpenAlex 값만 사용 (arXiv는 인용수 제공 안 함)
        for paper in sorted_group:
            if paper.source in ("s2", "openalex") and paper.citation_count is not None:
                primary.citation_count = paper.citation_count
                break

        # found_in_sources: 어느 소스에서 발견됐는지 집계
        primary.found_in_sources = list({p.source for p in group})
        primary.source_count = len(primary.found_in_sources)

        # 3-source 검증 배지
        sources = set(primary.found_in_sources)
        primary.source_badge = (
            "A✓ " if "arxiv" in sources else "A✗ "
        ) + (
            "S✓ " if "s2" in sources else "S✗ "
        ) + (
            "O✓" if "openalex" in sources else "O✗"
        )

        return primary

    return [merge_group(g) for g in groups]
```

### 4.2 단계별 요약

| 단계 | 방법 | 동일 논문 판정 기준 |
|:----:|------|-------------------|
| **1** | DOI 정규화 | lowercase + prefix 제거 + URL decode → 완전 일치 |
| **2** | arXiv ID 정규화 | version suffix 제거 후 완전 일치 |
| **3** | arXiv DOI 매핑 | `10.48550/arXiv.XXXX.XXXXX` → arXiv ID `XXXX.XXXXX`로 변환 후 단계 2와 교차 병합 |
| **4** | 제목 유사도 | > 0.90 + 첫 저자 last name 일치 → 병합 / 0.85~0.90 → 분리 + 검증 로그 |
| **5** | 외부 ID 보강 | S2 `externalIds` + OpenAlex `ids` cross-reference → 누락 ID 채움 |
| **6** | 출처 우선순위 | S2 > OpenAlex > arXiv (메타데이터 완성도 기준) |

### 4.3 출처 우선순위 근거

| 출처 | 메타데이터 강점 | 약점 |
|------|---------------|------|
| **Semantic Scholar** (우선 1위) | 인용수, TLDR, influentialCitationCount, 저자 상세, externalIds 다양 | 커버리지 제한 (일부 논문 누락) |
| **OpenAlex** (우선 2위) | Topics, `is_retracted`, `is_paratext`, 오픈 메타데이터 | Concepts deprecated, Topics 학습 중 |
| **arXiv** (우선 3위) | 최신성 (프리프린트), 무제한 커버리지 | 인용수 없음, 메타데이터 제한적 |

---

## 5. 관련성 점수 공식 (Relevance Score)

> **출처**: PLAN §8.3 + §4.4 단계 4 + §18.2

### 5.1 기본 공식

```python
import math

def relevance_score(paper, bias: str = "balanced") -> float:
    """
    논문의 관련성 점수를 계산한다.
    
    매트릭스 정렬 가중치로 사용되며, --bias 옵션에 따라 가중치 구성이 달라진다.
    
    Args:
        paper: 논문 객체 (citation_count, year, found_in_sources 필드 필요)
        bias:  "balanced" (기본) | "recency" (최신성 우선) | "citation" (인용수 우선)
    
    Returns:
        float: 관련성 점수 (정렬 기준, 절대값 의미 없음)
    """
    citations = paper.citation_count or 0          # None → 0 처리
    pub_year = paper.year or 2020                  # None → 보수적 하한 처리
    current_year = 2026

    # recency_weight: 최신 논문일수록 높은 가중치
    # 연 10%씩 감소, 최솟값 0.5 (매우 오래된 논문도 완전히 배제하지 않음)
    # boundary 값:
    #   0년  (2026): max(0.5, 1 - 0*0.1)  = 1.0
    #   5년  (2021): max(0.5, 1 - 5*0.1)  = 0.5
    #   10년 (2016): max(0.5, 1 - 10*0.1) = 0.5  (하한 도달)
    #   20년 (2006): max(0.5, 1 - 20*0.1) = 0.5  (하한 유지)
    recency_weight = max(0.5, 1.0 - (current_year - pub_year) * 0.1)

    # citation_weight: 인용수의 로그 스케일 가중치
    # log(0+1)=0, log(9+1)≈2.3, log(99+1)≈4.6, log(999+1)≈6.9
    # 인용수 0인 신규 논문도 완전히 배제되지 않음
    citation_weight = math.log(citations + 1)

    # source_count: 몇 개 소스에서 발견됐는지 (1~3)
    # 3-source 교차 검증 통과 논문에 자연스러운 보너스 부여
    source_count = len(paper.found_in_sources) if paper.found_in_sources else 1

    if bias == "balanced":
        # 균형: 인용수 × 최신성 × 소스 커버리지
        return citation_weight * recency_weight * source_count

    elif bias == "recency":
        # 최신성 우선: recency_weight 제곱으로 최신 논문 강조
        # 최신 논문(recency=1.0)은 영향 없음, 오래된 논문(recency=0.5)은 0.5²=0.25로 하락
        return citation_weight * (recency_weight ** 2) * source_count

    elif bias == "citation":
        # 인용수 우선: citation_weight 제곱으로 고인용 논문 강조
        # log(1000)≈6.9 → 6.9²≈47.6, log(10)≈2.3 → 2.3²≈5.3 (격차 확대)
        return (citation_weight ** 2) * recency_weight * source_count

    else:
        # 알 수 없는 bias 값 → balanced 폴백
        return citation_weight * recency_weight * source_count
```

### 5.2 `--bias` CLI 옵션

| 옵션 값 | 공식 변형 | 사용 시점 | 특성 |
|---------|----------|----------|------|
| `balanced` (기본) | `log(c+1) × rw × sc` | 일반적인 도메인 조사 | 인용수·최신성·3-source 균형 |
| `recency` | `log(c+1) × rw² × sc` | 빠르게 발전하는 분야 (LLM, CV 등) | 최신 프리프린트 우선; 인용수 아직 낮은 2024-2026 논문 상위 노출 |
| `citation` | `log(c+1)² × rw × sc` | 기초 이론, 권위 있는 교과서급 논문 탐색 | 고인용 클래식 논문 우선; 오래됐어도 중요한 논문 유지 |

**주의**: `recency` 모드는 **재현성(reproducibility)이 lagging**할 수 있다.  
프리프린트는 동료 심사를 통과하지 않았으며 코드/데이터 공개 비율이 낮다.  
6 필드 "신뢰성·재현성 조건"에 이 한계를 명시한다.

### 5.3 recency_weight 경계값 표

| 발행 연도 | 경과 연수 | recency_weight 계산 | 최종값 |
|:--------:|:--------:|:------------------:|:-----:|
| 2026 | 0 | max(0.5, 1.0 - 0×0.1) | **1.00** |
| 2025 | 1 | max(0.5, 1.0 - 1×0.1) | **0.90** |
| 2024 | 2 | max(0.5, 1.0 - 2×0.1) | **0.80** |
| 2023 | 3 | max(0.5, 1.0 - 3×0.1) | **0.70** |
| 2022 | 4 | max(0.5, 1.0 - 4×0.1) | **0.60** |
| 2021 | 5 | max(0.5, 1.0 - 5×0.1) | **0.50** ← 하한 도달 |
| 2016 | 10 | max(0.5, 1.0 - 10×0.1) | **0.50** (하한 유지) |
| 2006 | 20 | max(0.5, 1.0 - 20×0.1) | **0.50** (하한 유지) |

> 2021년 이전 논문은 모두 recency_weight = 0.50으로 동일하게 처리된다. `--bias citation`을 사용하면 이 논문들 중에서 인용수로 재정렬된다.

---

## 6. 0건 대응 전략 체인 (Zero-Result Fallback Chain)

3개 소스 모두 0건이거나 유효한 결과가 없을 때 순서대로 시도한다.

### 6.1 체인 순서

```
단계 1 → 단계 2 → 단계 3 → 단계 4
```

각 단계에서 유효한 결과가 나오면 이후 단계를 건너뛴다.

**단계 1: 검색어 자동 정제**

| 정제 방법 | 예시 |
|----------|------|
| 한국어 → 영어 변환 (§2.2) | `"주의 메커니즘"` → `"attention mechanism"` |
| 약어 풀어쓰기 (§2.3) | `"LLM"` → `"large language model"` |
| 특수문자 제거 | `"C++"` → `"C plus plus"` 또는 `"CPP"` |
| 구문 검색 → 단어 분리 | `"attention mechanism"` (exact) → `attention mechanism` (loose) |
| 복합 쿼리 단순화 | `"LLM code generation evaluation benchmark"` → `"LLM code generation"` |

자동 정제 후 동일 소스에 재호출한다 (arXiv ToU 준수 — 동일 쿼리 하루 1회 권장, 새 정제 쿼리는 별도 호출로 간주).

**단계 2: 연도 범위 확장**

```
기본 범위: last 5 years (2021-2026)
확장 범위: --years 2010-2026
```

- 최신 연도 필터를 제거하거나 2010년으로 확장한다.
- 특히 `cs.SE`, `cs.PL`, `cs.CR` 등 성숙한 분야는 2015년 이전 기초 논문도 유효하다.

**단계 3: 단일 소스 fallback**

```bash
# arXiv만 단독 검색
/dev-advisor research "<query>" --source arxiv

# 또는 Semantic Scholar만
/dev-advisor research "<query>" --source s2
```

- 3-source 교차 검증 없이 단일 소스 결과를 표시한다.
- 매트릭스에 ⚠️ 배너 표시: `single-source mode — cross-verification unavailable`.
- 신뢰성 필드에 단일 소스 한계를 명시한다.

**단계 4: researcher 에이전트 위임**

```
spawn_agent(
  agent_type="researcher",
  message="<query> 관련 학술 논문 5편을 Google Scholar, ACM DL, IEEE Xplore 등 다중 소스에서 조사하여 제목/저자/연도/인용수/DOI를 정리해주세요."
)
```

- arXiv/S2/OpenAlex에서 커버되지 않는 논문 (IEEE Xplore, ACM DL, conference proceedings 등)까지 탐색한다.
- 단, 이 경우 API 응답 기반 인용수/메타데이터 보장이 없으므로 환각 위험 주의 — 에이전트에게 **검증된 출처만 인용** 지시.

### 6.2 사용자 안내 출력 형식

```markdown
## Research — <query>

### 검색 결과 없음

3-source 모두 0건 (arXiv 0 / S2 0 / OpenAlex 0).

다음 순서로 재시도합니다:

1. **검색어 재정제** — 자동 시도: `<원본>` → `<정제된 쿼리>`
2. **연도 범위 확장** — 재시도: `--years 2010-2026`
3. **단일 소스 fallback** — arXiv만 검색: `--source arxiv`
4. **researcher 위임** — 외부 학술 DB 다중 검색

추천 명령:
- `/dev-advisor research "<정제된 검색어>"`
- `/dev-advisor research "<query>" --years 2010-2026`
- `/dev-advisor research "<query>" --source arxiv`
- `spawn_agent(agent_type="researcher", message="<query> 학술 논문 5편 정리")`
```

---

## 7. 검색 시점별 동시성 Schedule

> **출처**: PLAN §18.2 (v0.3 —Codex P1: rate-limit aware, arXiv ToU)

### 7.1 API별 throttle 정책

| API | 실행 모델 | 제약 | 비고 |
|-----|----------|------|------|
| **arXiv** | **직렬 throttled** | 3초당 1요청, 단일 연결 (ToU) | 동일 쿼리 하루 1회 권장 (§18.3 cache) |
| **Semantic Scholar** | 직렬 | 무인증: shared throttling (보장 없음) / 무료 key: 1 RPS | Exponential backoff 필수 (429/503) |
| **OpenAlex** | 직렬 | 🆓 완전 무료. anonymous도 정상 동작 | `mailto` 헤더 = 무료 polite pool (옵션) |
| **API 간 병렬** | **허용** | arXiv 1건 + OpenAlex 1건 = 다른 도메인, 단일 턴 동시 호출 가능 | S2는 동시에 3번째로 직렬 추가 가능 |

### 7.2 실행 순서 다이어그램

```
어시스턴트 턴 시작
│
├── [병렬 시작]
│   ├── arXiv Codex web 도구  (직렬 throttled 3s/req, timeout 5s)
│   └── OpenAlex Codex web 도구  (직렬, timeout 5s)
│
├── [arXiv/OpenAlex 완료 후]
│   └── Semantic Scholar Codex web 도구  (직렬, timeout 5s)
│       [key 없으면 shared throttling — backoff 준비]
│
├── [전체 응답 수집 완료]
│   └── 중복 제거 (§3) + 관련성 점수 계산 (§4) + 매트릭스 생성
│
└── 매트릭스 출력
    총 elapsed: max(arXiv, OA) + S2 ≤ p95 15s 목표
```

### 7.3 Exponential Backoff

```python
def fetch_with_backoff(url: str, max_retries: int = 3) -> Response:
    """
    429/503 응답 시 exponential backoff로 재시도한다.
    
    대기 시간: 1s → 2s → 4s (최대 3회)
    """
    wait = 1
    for attempt in range(max_retries):
        response = codex_web_fetch(url)
        if response.status_code in (429, 503):
            if attempt < max_retries - 1:
                time.sleep(wait)
                wait *= 2
            else:
                raise RateLimitExceeded(f"Max retries reached for {url}")
        else:
            return response
    return response
```

### 7.4 무료 정책 준수 체크리스트

> **절대 원칙**: 모든 API는 키 없이 anonymous 동작 보장. 유료 API 영원히 out-of-scope.

- [ ] arXiv: 인증 없음, ToU 3초 throttle 준수
- [ ] Semantic Scholar: 무인증으로 시작, 키 없어도 동작 확인
- [ ] OpenAlex: 무인증으로 시작, `mailto` 헤더는 옵션
- [ ] 사용자에게 "API 키를 발급해주세요" 메시지 출력 금지
- [ ] 키 없으면 anonymous로 진행 + 1줄 소극적 안내만:
  ```
  (선택) Semantic Scholar 무료 키 등록 시 rate limit 완화:
  export SEMANTIC_SCHOLAR_API_KEY=<free-key>
  ```
- [ ] Exa MCP 등 상용 유료 서비스를 기본 fallback으로 사용 금지

---

## 8. 참조 (References)

| 참조 | 내용 |
|------|------|
| `PLAN-research-mode.md §4.4` | 6단계 워크플로 상세 |
| `PLAN-research-mode.md §5.3` | 중복 제거 알고리즘 원본 |
| `PLAN-research-mode.md §8.3` | query-strategies.md 명세 목록 |
| `PLAN-research-mode.md §18.2` | 동시성 Schedule 상세 |
| `references/research/sources.md` | API 엔드포인트 + OpenAlex Topic ID 검증 결과 |
| `references/research/fallback.md` | Graceful Degradation 상세 |
| `references/research/performance.md` | Latency 목표 + 캐싱 정책 |
| `scripts/lookup-catalog.py` | 카탈로그 ID 매핑 도구 |
| `catalog-index.json` | 카탈로그 ID SSoT |
