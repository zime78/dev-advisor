# 카탈로그 Cross-Reference 매핑 알고리즘

> **SSoT**: `catalog-index.json` (스킬 루트 직속)
> **버전**: v0.1 (2026-05-28, PLAN-research-mode.md v0.5 §6.1 기반)
> **핵심 원칙**: LLM 주관 판단 금지 — 모든 매핑 판정은 아래 정량 기준만 적용
> **조회 도구**: `python3 scripts/lookup-catalog.py <domain> search <kw>` (markdown 직접 grep 금지 — SKILL.md §98 정합)

---

## 1. 개요

`/dev-advisor research` 모드는 외부 논문 검색 결과(arXiv / Semantic Scholar / OpenAlex)를
카탈로그 항목(`catalog-index.json`)과 **정량 기준**으로 자동 매핑한다.

### 1.1 매핑의 목적

| 목적 | 설명 |
|------|------|
| 학습 지속성 | 논문 ↔ 카탈로그 항목(패턴/알고리즘/원칙 등) 연결로 `/dev-advisor` 후속 lookup 유도 |
| 환각 방지 | LLM이 임의로 카탈로그 항목을 추측하는 것을 차단; `catalog-index.json` 실제 ID만 사용 |
| 신뢰도 표기 | HIGH/MED/LOW 세 단계로 매핑의 강도를 명시 — 사용자가 결과 신뢰 여부를 스스로 판단 가능 |

### 1.2 SSoT 강제 규칙

- **`catalog-index.json` 실제 ID에 존재하는 항목만 매핑 결과에 포함**
- markdown 파일(`references/patterns/*.md` 등)을 직접 grep하여 ID를 추출하는 방식 금지
- 카탈로그 조회는 반드시 헬퍼 스크립트를 통해 수행:

```bash
# 키워드로 알고리즘 검색 (예시)
python3 scripts/lookup-catalog.py algorithm search transformer

# 패턴 키워드 검색 (예시)
python3 scripts/lookup-catalog.py pattern search attention

# 원칙 키워드 검색 (예시)
python3 scripts/lookup-catalog.py principle search solid
```

반환된 JSON의 `"id"` 필드만 매핑 결과에 사용한다.

---

## 2. 카탈로그 매핑 신뢰도 정량 기준

> **LLM 주관 판단 금지** — 아래 조건 표를 코드처럼 순서대로 평가한다.
> 조건이 충족되지 않으면 해당 신뢰도는 부여하지 않고 다음 단계로 내려간다.
> 어느 조건도 충족되지 않으면 매핑 결과에 포함하지 않는다.

| 신뢰도 | 조건 (AND) |
|--------|-----------|
| **HIGH** | 논문 제목(`title`)에 카탈로그 ID 토큰 1개 이상 포함 **AND** (인용수 ≥ 100 **또는** ID와 정확히 일치하는 알고리즘/패턴명이 title에 존재) |
| **MED** | abstract **또는** Semantic Scholar TLDR에 ID 토큰 1개 이상 포함 (단, 제목에는 해당 토큰이 없음) |
| **LOW** | S2 `fieldsOfStudy` **또는** OpenAlex `topics` 필드에 카탈로그 도메인 매칭만 존재 (title/abstract/TLDR 어디에도 ID 토큰 없음) |
| **제외** | 위 세 조건 중 하나도 충족되지 않음 — 매핑 결과에 포함하지 않는다 |

**OpenAlex `topics` 사용 규칙**:
- `topics` 필드만 사용한다 (`concepts` 필드는 OpenAlex에서 deprecated — 사용 금지)
- 사전 검증된 Topics ID 9개 목록은 `references/research/sources.md` 참조

---

## 3. 알고리즘 의사코드

```python
STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "for",
    "and", "or", "with", "via", "using", "based", "toward",
    "towards", "new", "novel", "improved", "efficient",
}

def tokenize(text: str) -> set[str]:
    """
    텍스트를 소문자 토큰 집합으로 변환한다.

    규칙:
    - 소문자 변환
    - 하이픈(-), 언더스코어(_), 공백을 단어 경계로 처리
    - STOPWORDS 제거
    - 최소 토큰 길이 3자 이상만 포함
    """
    import re
    # 하이픈·언더스코어를 공백으로 통일
    normalized = re.sub(r"[-_]", " ", text.lower())
    # 알파벳·숫자·공백 이외 제거
    cleaned = re.sub(r"[^\w\s]", " ", normalized)
    tokens = {t for t in cleaned.split() if len(t) >= 3 and t not in STOPWORDS}
    return tokens


def domain_from_topics(topics: list[dict]) -> set[str]:
    """
    OpenAlex topics 필드에서 카탈로그 도메인 집합을 추출한다.

    topics 항목 구조:
      {"id": "T...", "display_name": "...", "subfield": {...}, "field": {...}, "domain": {...}}

    사전 검증된 Topics ID 9개 → sources.md 매핑 표에서 catalog domain을 역참조한다.
    검증되지 않은 Topics ID는 무시한다.
    """
    # sources.md의 "검증된 Topics ID → catalog domain" 매핑 (Phase 2 사전 게이트 통과 후 기록)
    VERIFIED_TOPICS_TO_DOMAIN = {
        # 형식: "T<ID>": "catalog_domain"
        # 실제 ID는 references/research/sources.md의 검증 통과 기록을 참조할 것
        # Phase 2 사전 게이트(PLAN §14.5) 완료 후 여기에 채운다
    }
    domains = set()
    for t in (topics or []):
        tid = t.get("id", "")
        if tid in VERIFIED_TOPICS_TO_DOMAIN:
            domains.add(VERIFIED_TOPICS_TO_DOMAIN[tid])
    return domains


def domain_from_fos(fields_of_study: list[str]) -> set[str]:
    """
    Semantic Scholar fieldsOfStudy 문자열 목록에서 카탈로그 도메인 집합을 추출한다.

    매핑 표 (PLAN §5.2 도메인별 매핑 표 기준):
      "Software Engineering"          → "patterns" / "principles" / "quality"
      "Computer Science"              → "algorithms"
      "Programming Languages"         → "languages"
      "Computer Security and Cryptography" → "security"
      "Software Testing"              → "quality"
      "Machine Learning"              → "algorithms" (AI/ML 서브셋)
      "Distributed Computing"         → "algorithms" (분산 서브셋)
      "Database Systems"              → "algorithms" (DB 서브셋)
    """
    FOS_TO_DOMAIN = {
        "Software Engineering": {"patterns", "principles", "quality"},
        "Computer Science": {"algorithms"},
        "Programming Languages": {"languages"},
        "Computer Security and Cryptography": {"security"},
        "Software Testing": {"quality"},
        "Machine Learning": {"algorithms"},
        "Distributed Computing": {"algorithms"},
        "Database Systems": {"algorithms"},
    }
    domains = set()
    for fos in (fields_of_study or []):
        domains.update(FOS_TO_DOMAIN.get(fos, set()))
    return domains


def map_paper_to_catalog(
    paper: dict,
    catalog_index_json: dict,
) -> list[dict]:
    """
    논문 하나를 catalog-index.json 항목들과 매핑하여 신뢰도 결과를 반환한다.

    Parameters
    ----------
    paper : dict
        API 응답에서 추출한 논문 dict.
        필수 키:
          title          (str)  — 논문 제목
        선택 키:
          abstract       (str | None)
          tldr           (str | None)  — Semantic Scholar TLDR
          fields_of_study (list[str])  — S2 fieldsOfStudy
          topics         (list[dict])  — OpenAlex topics (concepts 아님)
          citation_count (int)

    catalog_index_json : dict
        catalog-index.json 전체 파싱 결과.
        스키마: {"items": [...], "aliases": [...], ...}
        직접 json.load()한 결과를 전달한다.

    Returns
    -------
    list[dict]
        매핑 결과 리스트 (최대 5개, 신뢰도 우선 정렬 후 가나다 순):
        [{"catalog_id": str, "domain": str, "confidence": "HIGH"|"MED"|"LOW"}, ...]

    제약:
        - catalog-index.json에 존재하는 ID만 반환 (hallucination 방지)
        - is_paratext=True 논문은 호출 전에 필터링되어 있어야 함 (아래 §4 참조)
        - 매핑 0개이면 빈 리스트 반환 ("no catalog mapping" 명시는 호출자 책임)
    """
    results: list[dict] = []

    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""
    tldr = paper.get("tldr") or ""
    citation_count = paper.get("citation_count", 0) or 0
    fields_of_study = paper.get("fields_of_study") or []
    topics = paper.get("topics") or []

    title_tokens = tokenize(title)
    abstract_tokens = tokenize(abstract)
    tldr_tokens = tokenize(tldr)

    title_lower = title.lower()

    for item in catalog_index_json["items"]:
        catalog_id: str = item["id"]
        domain: str = item["domain"]

        # catalog_id를 토큰화 (하이픈을 단어 경계로 처리)
        id_tokens = tokenize(catalog_id)

        # aliases 소문자 목록 (정확 일치 체크용)
        aliases: list[str] = [a.lower() for a in item.get("aliases", [])]

        # ----------------------------------------------------------------
        # HIGH 판정
        #   조건: 제목에 ID 토큰 1개 이상 OR alias 정확 포함
        #         AND (인용수 ≥ 100 OR alias와 제목이 정확히 일치)
        # ----------------------------------------------------------------
        title_has_id_token = any(t in title_tokens for t in id_tokens)
        title_has_alias = any(a in title_lower for a in aliases)

        if title_has_id_token or title_has_alias:
            citation_ok = citation_count >= 100
            exact_match = any(a == title_lower for a in aliases)

            if citation_ok or exact_match:
                results.append({
                    "catalog_id": catalog_id,
                    "domain": domain,
                    "confidence": "HIGH",
                })
                continue  # HIGH 판정 시 MED/LOW 평가 불필요

        # ----------------------------------------------------------------
        # MED 판정
        #   조건: abstract 또는 TLDR에 ID 토큰 1개 이상 포함
        #         (제목에는 해당 토큰이 없는 경우만)
        # ----------------------------------------------------------------
        abs_tldr_has_id_token = any(
            t in abstract_tokens or t in tldr_tokens
            for t in id_tokens
        )

        if abs_tldr_has_id_token and not title_has_id_token and not title_has_alias:
            results.append({
                "catalog_id": catalog_id,
                "domain": domain,
                "confidence": "MED",
            })
            continue

        # ----------------------------------------------------------------
        # LOW 판정
        #   조건: fieldsOfStudy 또는 OpenAlex topics에 카탈로그 도메인 매칭
        #         (title/abstract/TLDR 어디에도 ID 토큰 없음)
        # ----------------------------------------------------------------
        matched_domains_topics = domain_from_topics(topics)
        matched_domains_fos = domain_from_fos(fields_of_study)
        all_matched_domains = matched_domains_topics | matched_domains_fos

        if domain in all_matched_domains:
            results.append({
                "catalog_id": catalog_id,
                "domain": domain,
                "confidence": "LOW",
            })

    # ----------------------------------------------------------------
    # 후처리: Top 5 반환, 신뢰도 우선(HIGH > MED > LOW) → 가나다 순
    # ----------------------------------------------------------------
    CONFIDENCE_ORDER = {"HIGH": 0, "MED": 1, "LOW": 2}
    results.sort(key=lambda r: (CONFIDENCE_ORDER[r["confidence"]], r["catalog_id"]))
    return results[:5]
```

---

## 4. 사전 필터링 규칙 (호출 전 처리)

`map_paper_to_catalog()` 호출 전에 다음 논문을 **제외**해야 한다.
이 규칙들은 매핑 함수 내부가 아니라 **상위 파이프라인**에서 적용한다.

| 필터 조건 | 적용 필드 | 사유 |
|----------|----------|------|
| `is_paratext == True` | OpenAlex `is_paratext` | 편집후기, 서문, 목차 등 실질 콘텐츠 없음 |
| `is_retracted == True` | OpenAlex `is_retracted` | 철회 논문은 매트릭스 상단에 ⚠️ RETRACTED 표시 후 별도 처리 (매핑 제외) |
| 식별자 없음 | DOI / arXiv ID 둘 다 없음 | §11.1 사전 차단 정책 — weak-evidence 섹션으로 이동, 매핑 함수 호출 불가 |
| title이 빈 문자열 | `paper["title"]` | 매핑 불가 |

---

## 5. 토큰화 규칙 상세

`tokenize()` 함수의 동작을 구체화한다.

| 규칙 | 내용 | 예시 |
|------|------|------|
| 소문자 변환 | 모든 문자를 소문자로 | `"Transformer"` → `"transformer"` |
| 하이픈/언더스코어 → 공백 | 단어 경계로 처리 | `"quick-sort"` → `{"quick", "sort"}` |
| 알파벳·숫자 이외 제거 | 구두점, 괄호 등 제거 | `"(BERT)"` → `"bert"` |
| 최소 길이 3자 | 2자 이하 토큰 제거 | `"is"`, `"of"` 제거 |
| STOPWORDS 제거 | 관사·전치사·의미 없는 형용사 | `"the"`, `"new"`, `"novel"` 등 제거 |

**STOPWORDS 전체 목록**:
```
the, a, an, of, in, on, at, to, for, and, or, with, via, using,
based, toward, towards, new, novel, improved, efficient
```

**토큰화 예시**:

| 입력 | 출력 토큰 집합 |
|------|--------------|
| `"Attention Is All You Need"` | `{"attention", "all", "you", "need"}` |
| `"transformer-architecture"` | `{"transformer", "architecture"}` |
| `"quick-sort"` (catalog ID) | `{"quick", "sort"}` |
| `"A New Efficient Method"` | `{"method"}` (new, efficient 제거) |

---

## 6. False Positive 회피 정책

단순 토큰 일치가 의미 없는 매핑을 만드는 경우를 차단한다.

### 6.1 단일 토큰 다운그레이드

매핑 근거가 토큰 1개만 일치하는 경우, 신뢰도를 한 단계 아래로 강등한다.

| 원래 판정 | 다운그레이드 후 |
|----------|--------------|
| HIGH (단일 토큰) | MED |
| MED (단일 토큰) | LOW |
| LOW (단일 토큰) | 제외 |

단일 토큰 다운그레이드가 적용되는 조건:
- `id_tokens` 집합 크기 ≥ 2인데 그 중 title/abstract/TLDR과 겹치는 토큰이 1개뿐인 경우
- `id_tokens` 집합 크기가 1이면 단일 토큰이어도 다운그레이드 없음 (예: catalog ID `"bert"` → 토큰 `{"bert"}` → 1개 일치가 전부이므로 원래 판정 유지)

### 6.2 도메인 불일치 제외

카탈로그 항목의 도메인과 논문 주제가 명백히 다른 경우 매핑 제외.

예시:
- catalog ID `factory` (카탈로그 도메인: `patterns`) → 산업 공장 건설 논문에 매핑 금지
  - 판정 기준: S2 `fieldsOfStudy`에 `"Civil Engineering"`, `"Manufacturing"` 등이 있고 `"Software Engineering"` 없으면 제외
- catalog ID `pipeline` (도메인: `patterns`) → 석유 파이프라인 논문에 매핑 금지

구현 방법: LOW 판정 시 `domain_from_fos()` / `domain_from_topics()`가 반환한 도메인 집합에
해당 카탈로그 `domain`이 포함되어야만 LOW 판정을 부여한다 (알고리즘 §3 LOW 판정 블록에 이미 반영됨).

### 6.3 is_paratext 제외 (§4에서 사전 처리)

OpenAlex `is_paratext: true` 논문은 `map_paper_to_catalog()` 호출 전에 제외되어야 한다.
편집후기·서문·리뷰 서론 등은 카탈로그 항목과의 의미 있는 매핑이 불가능하다.

---

## 7. catalog-index.json 조회 방식

### 7.1 조회 헬퍼 사용 필수

```bash
# 형식: python3 scripts/lookup-catalog.py <domain> search <keyword>
# domain: pattern|algorithm|language|security|principle|quality

# 패턴 도메인에서 "factory" 검색
python3 scripts/lookup-catalog.py pattern search factory

# 알고리즘 도메인에서 "transformer" 검색
python3 scripts/lookup-catalog.py algorithm search transformer

# 원칙 도메인에서 "solid" 검색
python3 scripts/lookup-catalog.py principle search solid
```

반환 형식 (JSON 배열):
```json
[
  {
    "domain": "algorithms",
    "id": "transformer",
    "item_type": "entry",
    "title": "Transformer",
    "title_ko": "트랜스포머",
    "category": "딥러닝",
    "file": "references/algorithms/deep-learning.md",
    "anchor": "transformer",
    "aliases": ["attention-model", "self-attention-architecture"]
  }
]
```

### 7.2 JSON 직접 파싱 시 경로

`map_paper_to_catalog()` 내부에서 `catalog_index_json`을 직접 사용할 때:

```python
import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent  # scripts/ → dev-advisor/
catalog = json.loads((SKILL_ROOT / "catalog-index.json").read_text(encoding="utf-8"))
```

### 7.3 markdown 직접 grep 금지

```bash
# 금지 — 절대 사용하지 않는다
grep -r "transformer" references/algorithms/  # WRONG

# 올바른 방법
python3 scripts/lookup-catalog.py algorithm search transformer  # CORRECT
```

이유: markdown 파일은 항목 ID와 별개로 서술 텍스트에 키워드가 포함될 수 있어
오탐(false positive)이 발생한다. `catalog-index.json` 기반 조회만이 실제 등록된 ID를 보장한다.

---

## 8. 출력 제약

### 8.1 반환 상한

- `map_paper_to_catalog()` 반환값은 최대 **5개** (Top 5)
- 논문 하나당 여러 카탈로그 항목과 매핑될 수 있다 (예: transformer 논문 → `algorithm/transformer` + `pattern/attention-mechanism`)

### 8.2 정렬 규칙

1. 신뢰도 우선: HIGH → MED → LOW
2. 동순위 시: `catalog_id` 가나다(알파벳) 오름차순

### 8.3 0개 시 처리

`map_paper_to_catalog()`가 빈 리스트를 반환하면, 출력 매트릭스의 "카탈로그 매핑" 컬럼에
`no catalog mapping`을 명시한다. 추정 매핑 금지 — "아마도 X 패턴과 관련이 있을 것 같다" 형식의
서술은 허용되지 않는다.

### 8.4 매핑 결과 표시 형식

`references/research/output-format.md` §3 "카탈로그 Cross-Reference" 섹션 형식:

```markdown
### 3. 카탈로그 Cross-Reference

| 매핑된 카탈로그 항목 | 매핑 논문 # | 매핑 신뢰도 |
|---------------------|------------|------------|
| `/algorithm transformer` | #1, #3 | HIGH (제목 토큰 + 인용수 ≥ 100) |
| `/pattern attention-mechanism` | #1 | MED (abstract/TLDR 토큰 매치) |
| `/principle deep-learning` | #4 | LOW (S2 fieldsOfStudy 매칭) |
```

신뢰도 표기 시 판정 근거를 괄호 안에 요약한다:
- HIGH: `HIGH (제목 토큰 + 인용수 ≥ 100)` 또는 `HIGH (alias 정확 일치)`
- MED: `MED (abstract 토큰 매치)` 또는 `MED (TLDR 토큰 매치)`
- LOW: `LOW (S2 fieldsOfStudy 매칭)` 또는 `LOW (OpenAlex topics 매칭)`

---

## 9. 테스트 골든 케이스

`references/research/testing.md` U-03과 정합. Phase 6에서 `fixtures/` 디렉토리에 작성.

### 9.1 5×3 = 15 골든 케이스 구조

신뢰도 3단계 × 카탈로그 도메인 3종 = 15 케이스.

| 케이스 번호 | 신뢰도 목표 | 카탈로그 도메인 | 논문 제목 특성 | 기대 출력 |
|:----------:|:----------:|:-------------:|--------------|---------|
| GC-01 | HIGH | algorithms | 제목에 catalog ID 토큰 포함 + 인용수 ≥ 100 | `HIGH` |
| GC-02 | HIGH | patterns | 제목에 alias 정확 포함 | `HIGH` |
| GC-03 | HIGH | principles | 제목에 ID 토큰 포함 + 인용수 = 100 (경계값) | `HIGH` |
| GC-04 | MED | algorithms | 제목에 없고, abstract에 ID 토큰 포함 | `MED` |
| GC-05 | MED | patterns | 제목에 없고, TLDR에 ID 토큰 포함 | `MED` |
| GC-06 | MED | principles | 제목에 없고, abstract + TLDR 둘 다 ID 토큰 포함 | `MED` |
| GC-07 | LOW | algorithms | title/abstract/TLDR 모두 미포함, S2 fieldsOfStudy 매칭 | `LOW` |
| GC-08 | LOW | patterns | title/abstract/TLDR 모두 미포함, OpenAlex topics 매칭 | `LOW` |
| GC-09 | LOW | security | title/abstract/TLDR 모두 미포함, 도메인 매칭 | `LOW` |
| GC-10 | HIGH (다운그레이드→MED) | algorithms | 제목에 단일 토큰만 일치 + 인용수 ≥ 100 (ID 토큰 2개 중 1개만) | `MED` |
| GC-11 | MED (다운그레이드→LOW) | patterns | abstract에 단일 토큰만 일치 (ID 토큰 2개 중 1개만) | `LOW` |
| GC-12 | LOW (다운그레이드→제외) | principles | 단일 토큰 도메인 매칭 (ID 토큰 2개 중 1개만) | `제외` |
| GC-13 | 제외 (도메인 불일치) | patterns | `factory` catalog, `fieldsOfStudy=Civil Engineering` | `제외` |
| GC-14 | 제외 (is_paratext) | algorithms | is_paratext=True 논문 | `제외` (사전 필터) |
| GC-15 | 제외 (0건) | any | 어떤 조건도 충족하지 않는 논문 | `[]` (no catalog mapping) |

### 9.2 픽스처 파일 네이밍 규칙

`references/research/fixtures/` 디렉토리:

```
fixtures/
  mapping-gc-01.json   # 논문 dict + catalog_index_json 슬라이스 + expected_output
  mapping-gc-02.json
  ...
  mapping-gc-15.json
```

픽스처 JSON 형식:
```json
{
  "case_id": "GC-01",
  "description": "HIGH: 제목에 catalog ID 토큰 포함 + 인용수 ≥ 100",
  "paper": {
    "title": "Attention Is All You Need",
    "abstract": "...",
    "tldr": null,
    "fields_of_study": ["Computer Science", "Machine Learning"],
    "topics": [],
    "citation_count": 120453
  },
  "catalog_items_subset": [
    {
      "domain": "algorithms",
      "id": "transformer",
      "aliases": ["attention-model"],
      "tags": []
    }
  ],
  "expected_output": [
    {"catalog_id": "transformer", "domain": "algorithms", "confidence": "HIGH"}
  ]
}
```

---

## 10. 관련 파일 참조

| 파일 | 역할 | 이 문서와의 관계 |
|------|------|----------------|
| `catalog-index.json` | SSoT — 모든 카탈로그 항목 ID | 매핑 함수의 유일한 조회 대상 |
| `scripts/lookup-catalog.py` | 카탈로그 조회 헬퍼 | 반드시 이 스크립트를 통해 ID 조회 |
| `references/research/sources.md` | 사전 검증된 OpenAlex Topics ID 9개 기록 | `domain_from_topics()` 내 매핑 표의 출처 |
| `references/research/output-format.md` | 카탈로그 Cross-Reference 섹션 형식 | §8.4 매핑 결과 표시 형식과 정합 |
| `references/research/testing.md` | 단위 테스트 U-03 정의 (5×3 골든) | §9 테스트 골든 케이스의 상위 명세 |
| `references/research/fixtures/` | 15개 매핑 골든 픽스처 파일 | §9.2 형식으로 Phase 6에서 작성 |
| `PLAN-research-mode.md` | §6.1 매핑 신뢰도 정량 기준 (원본) | 본 문서의 설계 근거 |

---

## 11. 구현 제약 요약 (체크리스트)

구현 시 반드시 다음을 확인한다.

- [ ] `catalog-index.json` 실제 ID만 반환 (LLM 추측 금지)
- [ ] `python3 scripts/lookup-catalog.py` 경유 조회 (markdown grep 금지)
- [ ] `is_paratext: true` 논문 사전 제외 (§4)
- [ ] `is_retracted: true` 논문 매핑 제외 + ⚠️ RETRACTED 별도 표시
- [ ] 신뢰도 판정 순서: HIGH → MED → LOW (한 항목이 HIGH 판정 시 MED/LOW 평가 skip)
- [ ] 단일 토큰 일치 시 다운그레이드 적용 (§6.1)
- [ ] 도메인 불일치 제외 (`factory` → 공장 논문 매핑 금지, §6.2)
- [ ] OpenAlex `topics` 필드만 사용 (`concepts` 금지 — deprecated)
- [ ] 반환 상한 5개, HIGH 우선 → 가나다 순 정렬
- [ ] 0건 시 빈 리스트 반환 + 호출자가 `no catalog mapping` 명시
