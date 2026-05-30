# testing.md — research 모드 테스트 / 검증 매트릭스

> **출처**: `PLAN-research-mode.md` v0.5 §19 + §19.5 + §11.1  
> **상태**: Phase 3 산출물 (Phase 2 Pre-flight Gate 통과 후 유효)  
> **목적**: research 모드의 회귀 방지 + 환각 차단 전략을 테스트 명세로 구체화한다.

---

## 1. 개요

research 모드는 외부 무료 API 3종(arXiv + Semantic Scholar + OpenAlex)에서 실시간으로 논문 메타데이터를 수집·교차 검증하여 출력한다. 정적 카탈로그와 달리 응답이 동적이므로 두 가지 위협이 존재한다.

**위협 1 — 회귀**: 기존 9 모드 + 6 카탈로그 lookup이 research 모드 추가로 인해 손상되는 경우.  
**위협 2 — 환각**: Codex가 API 응답 외의 지식(pre-training cutoff 이전 지식, 추정값, 존재하지 않는 식별자)을 매트릭스 행에 혼입하는 경우.

이 문서는 두 위협을 자동으로 검출하는 테스트 매트릭스를 정의한다. 모든 테스트는 실제 API 호출 없이 `references/research/fixtures/`의 mock fixture로 실행 가능하다.

### 1.1 테스트 계층 구조

```
testing.md
├── §2  단위 테스트 (U-01 ~ U-07)   — 알고리즘·함수 수준 검증
├── §3  통합 테스트                  — mock fixture 기반 end-to-end 검증
├── §4  회귀 테스트                  — 기존 모드 보호
├── §5  verify-references.sh 확장   — 자동 게이트 (11-7 ~ 11-13)
└── §6  환각 회귀 테스트 자동화      — HR-01 ~ HR-10 (핵심)
```

### 1.2 실행 전제 조건

- Phase 2 Pre-flight Gate(§14.5) 통과 후 실행
- `references/research/fixtures/` 디렉토리에 최소 5 케이스 존재
- `catalog-index.json` 접근 가능 (HR-08 JSON lookup에 필요)
- `scripts/verify-references.sh` 존재

---

## 2. 단위 테스트 (§19.1)

단위 테스트는 research 모드 내부 알고리즘·함수의 입출력을 검증한다. 각 케이스는 mock 입력만으로 실행 가능하며 외부 네트워크 호출 없이 완결된다.

### 2.1 단위 테스트 매트릭스

| # | 케이스 | 입력 | Assertion |
|:-:|--------|------|-----------|
| U-01 | DOI 누락 행 입력 | `doi: null`, `arxiv_id: null`, `s2_paper_id: null`, `openalex_work_id: null` 행 | 행 자동 drop + 검증 로그에 `[DROP] identifier missing` 기록 |
| U-02 | Levenshtein 0.90 임계 (50쌍 골든) | `fixtures/normal/` 15 케이스 + `fixtures/partial-failure/` 12 케이스 제목 쌍 | precision ≥ 0.9, recall ≥ 0.85 (임계값 0.90 기준) |
| U-03 | 매핑 신뢰도 HIGH/MED/LOW 5×3 골든 | 제목 토큰 일치율 + 인용수 조합 15패턴 | 알고리즘 출력 신뢰도 == 골든 레이블 |
| U-04 | URL 화이트리스트 위반 입력 | `http://bit.ly/xxxxx`, `https://sci-hub.se/...` 등 비허용 도메인 | 행 drop (또는 URL 필드 null 처리) |
| U-05 | recency_weight 함수 boundary | 논문 연령: 0년 / 5년 / 10년 / 20년 | 각각 명세된 가중치 반환 (PLAN §8.3 `--bias` 함수 식 준수) |
| U-06 | OpenAlex Topics ID 사전 검증 누락 시 | `sources.md`에 검증 로그 없는 상태 | Phase 2 진입 차단 + 오류 메시지 출력 |
| U-07 | 식별자 정규식 검증 (DOI/arXiv/S2/OA) | 유효·무효 식별자 각 4종 × 2패턴 | 유효 패턴 통과, 무효 패턴 drop |

### 2.2 U-07 식별자 정규식 상세

§11.1 사전 차단 정책에서 정의된 정규식을 기반으로 검증한다.

| 식별자 종류 | 정규식 | 유효 예시 | 무효 예시 |
|------------|--------|----------|----------|
| DOI | `^10\.\d{4,}/` | `10.1145/3292500.3330646` | `doi:10.1145/...` (접두사 포함 시 drop) |
| arXiv ID (신형) | `^\d{4}\.\d{4,5}(v\d+)?$` | `2106.09685`, `1706.03762v5` | `arxiv:2106.09685` |
| arXiv ID (구형) | `^[a-z-]+/\d{7}(v\d+)?$` | `cs/0301023` | `cs.LG/0301023` |
| S2 paperId | `^[a-f0-9]{40}$` | `204e3073870fae3d05bcbc2f6a8e263d9b72e776` | `S2:204e3073...` |
| OpenAlex Work ID | `^W\d{8,}$` | `W2741809807` | `https://openalex.org/W2741809807` |

> 정규식을 통과하지 못한 행은 primary matrix에서 제외하고 검증 로그에 `[DROP] invalid identifier: <값>` 형태로 기록한다. weak-evidence 섹션 이동도 금지 (식별자 없는 논문은 어느 섹션에도 출력 불가).

### 2.3 U-02 Levenshtein 임계값 이력

PLAN v0.3에서Codex 권고에 따라 0.85 → 0.90으로 상향되었다.  
골든 50쌍은 `fixtures/normal/` + `fixtures/partial-failure/`의 제목 쌍으로 구성되며, arXiv DOI `10.48550/arXiv.*` ↔ arXiv ID 교차 매핑을 포함한다(중복 제거 알고리즘 §5.3 #3).

---

## 3. 통합 테스트 (§19.2)

통합 테스트는 `/dev-advisor research <topic>` 전체 워크플로를 mock fixture로 실행하고, 매트릭스 출력이 골든과 일치하는지 검증한다.

### 3.1 fixtures/ 디렉토리 구조

```
references/research/fixtures/
├── normal/            # 15 케이스 — 식별자 완비, 정상 응답
├── partial-failure/   # 12 케이스 — 1-of-3 또는 2-of-3 API 장애
├── zero-result/       # 5 케이스  — 검색 결과 0건
├── schema-drift/      # 8 케이스  — 필드 누락·타입 변경
├── korean-query/      # 5 케이스  — 한국어 검색어 입력
└── retracted/         # 5 케이스  — is_retracted: true 논문 포함
```

총 50 케이스. 각 fixture는 JSON 파일 형태의 mock API 응답이다.

### 3.2 Fixture JSON 형식 (단일 케이스)

```json
{
  "case_id": "normal-001",
  "query": "transformer attention mechanism",
  "source": "openalex",
  "mock_response": {
    "results": [
      {
        "doi": "10.48550/arXiv.1706.03762",
        "title": "Attention Is All You Need",
        "authors": [{"display_name": "Ashish Vaswani"}],
        "publication_year": 2017,
        "cited_by_count": 95000,
        "venue": "NeurIPS",
        "is_retracted": false,
        "ids": {
          "openalex": "W2741809807",
          "arxiv": "1706.03762"
        }
      }
    ]
  },
  "expected_matrix_row": {
    "identifier_present": true,
    "drop": false,
    "mapping_confidence": "HIGH"
  }
}
```

### 3.3 케이스 분류별 통합 검증 목표

| 디렉토리 | 케이스 수 | 검증 목표 |
|---------|:--------:|---------|
| `normal/` | 15 | 전체 워크플로 정상 완료, 매트릭스 8~10행 출력, 카탈로그 매핑 신뢰도 HIGH/MED 비율 |
| `partial-failure/` | 12 | §17.1 degraded mode 배너 출력, 사용 가능 소스의 결과만으로 매트릭스 구성 |
| `zero-result/` | 5 | 0건 fast-fail 처리, researcher hand-off 안내 출력 |
| `schema-drift/` | 8 | 필드 누락 시 null 처리 + 검증 로그 기록, 비정상 타입 행 drop |
| `korean-query/` | 5 | 한→영 정규화 후 영문 검색 실행, 정규화 후보 1~3개 제시 |
| `retracted/` | 5 | `is_retracted: true` 행에 ⚠️ RETRACTED 명시, 매트릭스 포함 시 경고 표시 |

### 3.4 통합 테스트 실행 절차

```bash
# 전체 fixture 순회 — mock dry-run + 골든 비교
for f in /Users/zime/.codex/skills/dev-advisor/references/research/fixtures/*/*.json; do
  case_id=$(python3 -c "import json,sys; d=json.load(open('$f')); print(d['case_id'])")
  echo "=== ${case_id} ==="
  # mock fixture를 research 모드 입력으로 주입 후 출력 검증
  # HR-01~HR-10 자동 검증 (§6 참조)
done
```

---

## 4. 회귀 테스트 (§19.3)

research 모드 추가가 기존 기능을 손상시키지 않음을 확인한다.

### 4.1 기존 모드 회귀 0건

| 검증 대상 | 검증 방법 | 기준 |
|----------|---------|------|
| 기존 9 모드 호출 | `bash scripts/verify-references.sh` smoke test | 회귀 0건 |
| 6 카탈로그 lookup | 각 도메인 lookup 1회 실행 | 정상 응답 + 형식 유지 |
| `--help` 출력 | `/dev-advisor --help` 실행 | research 모드 행 추가 + 기존 행 변경 없음 |

### 4.2 SKILL.md 변경 후 schema 무결성

```bash
# catalog-index.json은 research 모드 추가로 변경되어서는 안 된다
python3 scripts/generate-catalog-index.py --check
# 예상 출력: "[PASS] catalog-index.json schema unchanged"
```

- `catalog-index.json` schema 변경 없음 확인 (research는 동적이므로 정적 색인 불필요 — §2.2)
- SKILL.md 수정 후 `modes` 필드가 새로 생기지 않았음을 확인

### 4.3 smoke test 명세

| # | 테스트 | 명령 | 기대 결과 |
|:-:|--------|------|----------|
| S-01 | recommend 모드 | `/dev-advisor recommend "API design"` | 기존 형식 유지 |
| S-02 | compare 모드 | `/dev-advisor compare "REST vs GraphQL"` | 기존 형식 유지 |
| S-03 | qa 모드 | `/dev-advisor qa "SOLID"` | 기존 형식 유지 |
| S-04 | lookup 모드 | `/dev-advisor lookup pattern singleton` | 카탈로그 응답 유지 |
| S-05 | full 모드 | `/dev-advisor full "auth"` | research 미포함 확인 (§13.3) |
| S-06 | swarm 모드 | `/dev-advisor swarm "microservices"` | research 미포함 확인 (§13.3) |

> full/swarm 모드는 research를 기본 포함하지 않는다(§13.3 결정). 사용자가 `--with-research` 명시 시에만 포함.

---

## 5. verify-references.sh 확장 (§19.4 + §8.13)

`scripts/verify-references.sh`의 11번 블록에 research 모드 등록 검증 7항목을 추가한다.

### 5.1 11번 블록 확장 항목 (11-7 ~ 11-13)

```bash
# ── Block 11: research 모드 등록 검증 ──────────────────────────────────
echo "=== Block 11: research mode registration ==="

# 11-7. /dev-advisor research SKILL.md 등록 확인
grep -q "research" ~/.codex/skills/dev-advisor/SKILL.md \
  && echo "[PASS] 11-7: research mode in SKILL.md" \
  || { echo "[FAIL] 11-7: research mode NOT in SKILL.md"; FAIL=1; }

# 11-8. research 자연어 트리거 최소 2개 확인
# 허용 키워드: "논문", "research", "SOTA", "literature review", "학술"
TRIGGER_COUNT=$(grep -cE '논문|research|SOTA|literature review|학술' \
  ~/.codex/skills/dev-advisor/SKILL.md || true)
[ "$TRIGGER_COUNT" -ge 2 ] \
  && echo "[PASS] 11-8: research triggers >= 2 (found: ${TRIGGER_COUNT})" \
  || { echo "[FAIL] 11-8: research triggers < 2"; FAIL=1; }

# 11-9. output_templates.md에 research 모드 스켈레톤 존재 확인
grep -q "research" ~/.codex/skills/dev-advisor/references/output_templates.md \
  && echo "[PASS] 11-9: research skeleton in output_templates.md" \
  || { echo "[FAIL] 11-9: research skeleton NOT in output_templates.md"; FAIL=1; }

# 11-10. examples.md에 research 예시(K/L/M) 3개 존재 확인
EXAMPLE_COUNT=$(grep -cE '예시 K|예시 L|예시 M|Example K|Example L|Example M' \
  ~/.codex/skills/dev-advisor/references/examples.md || true)
[ "$EXAMPLE_COUNT" -ge 3 ] \
  && echo "[PASS] 11-10: research examples K/L/M found (${EXAMPLE_COUNT})" \
  || { echo "[FAIL] 11-10: research examples K/L/M < 3"; FAIL=1; }

# 11-11. handoff.md에 Codex research hand-off 역할 존재 확인
for AGENT in "researcher" "analyst"; do
  grep -q "$AGENT" ~/.codex/skills/dev-advisor/references/handoff.md \
    && echo "[PASS] 11-11: ${AGENT} in handoff.md" \
    || { echo "[FAIL] 11-11: ${AGENT} NOT in handoff.md"; FAIL=1; }
done

# 11-12. references/research/fixtures/ 디렉토리 + 최소 5 케이스 존재
FIXTURE_ROOT=~/.codex/skills/dev-advisor/references/research/fixtures
if [ -d "$FIXTURE_ROOT" ]; then
  FIXTURE_COUNT=$(find "$FIXTURE_ROOT" -name "*.json" | wc -l | tr -d ' ')
  [ "$FIXTURE_COUNT" -ge 5 ] \
    && echo "[PASS] 11-12: fixtures/ exists with ${FIXTURE_COUNT} cases" \
    || { echo "[FAIL] 11-12: fixtures/ has < 5 cases (found: ${FIXTURE_COUNT})"; FAIL=1; }
else
  echo "[FAIL] 11-12: fixtures/ directory not found"
  FAIL=1
fi

# 11-13. OpenAlex Topics ID 사전 검증 로그 존재 (sources.md 내)
SOURCES_MD=~/.codex/skills/dev-advisor/references/research/sources.md
if [ -f "$SOURCES_MD" ]; then
  grep -q "Topics" "$SOURCES_MD" \
    && echo "[PASS] 11-13: OpenAlex Topics verification log in sources.md" \
    || { echo "[FAIL] 11-13: OpenAlex Topics log NOT in sources.md"; FAIL=1; }
else
  echo "[FAIL] 11-13: sources.md not found"
  FAIL=1
fi
# ── End Block 11 ──────────────────────────────────────────────────────
```

### 5.2 anchor 무결성 검증

`references/research/*.md` 내부 링크 무결성을 확인한다.

```bash
# research/*.md 파일 내 앵커 참조 검증
RESEARCH_DIR=~/.codex/skills/dev-advisor/references/research
for md_file in "$RESEARCH_DIR"/*.md; do
  # [텍스트](#anchor) 형태 링크 추출
  while IFS= read -r anchor; do
    # 동일 파일 내 헤더에 anchor가 존재하는지 확인
    header=$(echo "$anchor" | sed 's/-/ /g' | tr '[:upper:]' '[:lower:]')
    grep -qi "^#.*${header}" "$md_file" \
      || echo "[WARN] broken anchor '${anchor}' in $(basename $md_file)"
  done < <(grep -oP '(?<=\(#)[^)]+' "$md_file" || true)
done
```

> 카운트 검증은 수행하지 않는다. research 모드는 동적 결과를 생성하므로 정적 행 수 검증은 무의미하다.

---

## 6. 환각 회귀 테스트 자동화 (§19.5) — 핵심

### 6.1 목표

PLAN §14.2 "환각 0건" 기준을 회귀로 강제한다. 정성 평가가 아니라 자동 검증 가능한 hook으로 변환한다.

- **환각 정의**: API 응답 외의 값(Codex pre-training 지식, 추정값, 존재하지 않는 식별자)이 매트릭스 행에 혼입된 경우
- **검증 방식**: mock fixture 50쌍 기준 + 정규식/JSON lookup/string match/카운트로 자동 판정
- **트리거 시점**: research 응답 생성 직후 자동 실행 (인터럽트 없음)

### 6.2 HR-01 ~ HR-10 자동 검증 매트릭스

| # | 검증 항목 | 도구 | 트리거 시점 | 실패 시 처리 |
|:-:|-----------|------|------------|-------------|
| HR-01 | 매트릭스 모든 행에 식별자 1개+ (DOI/arXiv ID/S2 paperId/OpenAlex Work ID) | 정규식 (§11.1) | research 응답 생성 후 자동 | 해당 행 drop + 검증 로그 기록 |
| HR-02 | 식별자 정규식 일치 — `^10\.\d{4,}/` / `^\d{4}\.\d{4,5}(v\d+)?$` / `^[a-f0-9]{40}$` / `^W\d{8,}$` | regex | 위와 동일 | 행 drop + `[DROP] invalid identifier` 로그 |
| HR-03 | URL 화이트리스트(`arxiv.org`/`doi.org`/`semanticscholar.org`/`openalex.org`) 위반 0건 | 도메인 매칭 | 위와 동일 | URL 필드 null 처리 또는 행 drop |
| HR-04 | 인용수 컬럼이 API 응답 raw value와 일치 (Codex 추정값 X) | response trace | mock fixture 50쌍 전체 | FAIL — CI 차단 대상 |
| HR-05 | 저자명이 API 응답 원문 그대로 (`authors[].display_name` 직접 참조) | string match | mock fixture 전체 | FAIL — CI 차단 대상 |
| HR-06 | venue 필드가 API 응답 `venue` 또는 `publicationVenue.name` 직접 참조 | string match | mock fixture 전체 | FAIL — CI 차단 대상 |
| HR-07 | "선택/판정" 6필드에 cutoff 이전 지식 혼입 없음 | LLM judge 또는 휴리스틱 | sample 20% (10케이스) | WARNING — 수동 검토 후 판정 |
| HR-08 | 카탈로그 매핑 ID가 `catalog-index.json` 실제 ID 목록과 일치 | JSON lookup | 매핑 행마다 | 매핑 행 제거 + 신뢰도 LOW 강제 |
| HR-09 | weak-evidence 섹션 항목 수 ≤ 2 | 카운트 | 위와 동일 | 초과 항목 자동 truncate |
| HR-10 | `is_retracted: true` 논문에 ⚠️ 표시 + RETRACTED 명시 | flag check | `retracted/` fixture 5개 | FAIL — 철회 논문 무경고 출력 금지 |

### 6.3 HR-07 상세 — LLM judge 또는 휴리스틱

"선택/판정" 필드는 텍스트이므로 정규식으로 완전 검증이 불가능하다. 두 가지 접근을 계층적으로 적용한다.

**휴리스틱 (1차)**: 아래 패턴이 검출되면 WARN을 발생시키고 수동 검토 대상으로 분류한다.
- API 응답에 없는 논문 제목이 "선택/판정" 텍스트에 등장
- API `cited_by_count`와 다른 숫자가 인용수로 기술됨
- API 응답에 없는 저자명이 등장

**LLM judge (2차, 선택)**: 위 휴리스틱 통과 후, sample 20%에 대해 아래 판정 프롬프트를 사용한다.

```
다음 "선택/판정" 텍스트가 주어진 API 응답 JSON에서만 도출된 내용인지 판정하라.
API 응답 외 지식(pre-training 데이터) 혼입이 의심되면 SUSPECT로, 그렇지 않으면 CLEAN으로만 응답하라.

API 응답: <mock_response JSON>
선택/판정 텍스트: <판정 필드 내용>
```

HR-07 결과는 WARN 수준이며 CI 자동 차단 대상이 아니다. 반복 SUSPECT 패턴 발생 시 §11.1 사전 차단 정책에 새 규칙을 추가한다.

### 6.4 HR-04 상세 — 인용수 검증

인용수는 API 응답 raw value를 그대로 출력해야 한다. Codex가 추정하거나 반올림·가공한 값은 환각으로 판정한다.

```python
# HR-04 검증 로직 (의사코드)
def verify_citation_count(matrix_row, mock_response):
    api_count = mock_response["cited_by_count"]
    output_count = matrix_row["citation_count"]
    
    if api_count is None:
        # 인용수 0인 fixture (fixtures/partial-failure/ 일부): null 또는 "n/a" 허용
        assert output_count in (None, "n/a", 0), f"HR-04 FAIL: expected null, got {output_count}"
    else:
        assert output_count == api_count, (
            f"HR-04 FAIL: expected {api_count} (API raw), got {output_count} (possible hallucination)"
        )
```

### 6.5 HR-08 상세 — catalog-index.json lookup

카탈로그 매핑은 Codex가 임의로 ID를 생성하는 것을 방지하기 위해 `catalog-index.json`의 실제 ID 목록과 대조한다.

```bash
# HR-08 검증 (bash)
CATALOG=~/.codex/skills/dev-advisor/catalog-index.json

# 매트릭스 행의 catalog_mapping 필드에서 ID 추출
while IFS= read -r mapped_id; do
  # catalog-index.json에 실제 존재하는지 확인
  python3 -c "
import json, sys
catalog = json.load(open('${CATALOG}'))
mapped_id = '${mapped_id}'
# catalog-index.json의 모든 ID 수집
all_ids = [item['id'] for domain in catalog.values()
           if isinstance(domain, list) for item in domain
           if 'id' in item]
if mapped_id not in all_ids:
    print(f'[HR-08 FAIL] ID \"{mapped_id}\" not in catalog-index.json')
    sys.exit(1)
else:
    print(f'[HR-08 PASS] \"{mapped_id}\" verified')
" || FAIL=1
done < <(grep -oP '"catalog_mapping":\s*"\K[^"]+' matrix_output.json || true)
```

### 6.6 Golden Fixture 50쌍 구조

HR-01~HR-10 자동 검증에 사용하는 mock fixture 50쌍의 분류와 검증 목적이다.

| 디렉토리 | 케이스 수 | 주요 HR 검증 | 비고 |
|---------|:--------:|-------------|------|
| `fixtures/normal/` | 15 | HR-04, HR-05, HR-06, HR-08 | 식별자 완비, 모든 필드 정상 |
| `fixtures/partial-failure/` | 12 | HR-01, HR-02, HR-04 (null handling) | 1-of-3 또는 2-of-3 API 장애 시뮬레이션 |
| `fixtures/zero-result/` | 5 | HR-09 (weak-evidence 0건 허용) | 전 소스 0건, fast-fail 처리 확인 |
| `fixtures/schema-drift/` | 8 | HR-05, HR-06 (필드 누락 시 null) | 필드명 변경·타입 변경 대응 |
| `fixtures/korean-query/` | 5 | HR-07 (정규화 후 영문 검색) | 한국어 입력 → 영문 변환 검증 |
| `fixtures/retracted/` | 5 | HR-10 (⚠️ 표시 의무) | `is_retracted: true` 포함 |

> **주의**: `fixtures/` 내 파일은 실제 논문 응답이 아닌 합성 mock 데이터다. 실제 API 호출 없이 구조·알고리즘 검증만을 목적으로 한다.

---

## 7. CI 통합 옵션 (선택, 미래 PLAN)

현재 PLAN(v0.5) 범위에서 CI 자동 실행은 선택사항이다. 아래 명령이 향후 CI pipeline에 추가될 예정이다.

```bash
# research 모드 전체 검증 게이트
bash scripts/verify-references.sh --check research

# 환각 회귀 검증 게이트 (HR-01~HR-10)
bash scripts/verify-references.sh --check research-hallucination
```

두 명령 모두 `scripts/verify-references.sh`의 확장으로 구현된다. `--check research`는 §5 등록 검증(11-7~11-13)을 실행하고, `--check research-hallucination`은 §6 환각 회귀 검증(HR-01~HR-10)을 mock fixture 50쌍 기준으로 실행한다.

---

## 8. 전체 테스트 실행 절차

```bash
# ──────────────────────────────────────────────────────────
# 사전 조건: Phase 2 Pre-flight Gate 통과 후 실행
# ──────────────────────────────────────────────────────────

# 1. 사전 게이트 — 3 API anonymous 동작 확인 (Phase 2 §14.5)
echo "=== Phase 2: API anonymous smoke test ==="
curl -sf "https://api.semanticscholar.org/graph/v1/paper/search?query=transformer&limit=1&fields=paperId" \
  -o /dev/null && echo "[PASS] Semantic Scholar anonymous" || echo "[WARN] S2 unreachable"

curl -sf "https://api.openalex.org/works?search=transformer&per-page=1" \
  -o /dev/null && echo "[PASS] OpenAlex anonymous" || echo "[WARN] OpenAlex unreachable"

curl -sf "https://export.arxiv.org/api/query?search_query=transformer&max_results=1" \
  -o /dev/null && echo "[PASS] arXiv anonymous" || echo "[WARN] arXiv unreachable"

# 2. 단위 테스트 — verify-references.sh research 블록
echo ""
echo "=== Unit / Registration Tests (Block 11) ==="
bash /Users/zime/.codex/skills/dev-advisor/scripts/verify-references.sh --check research

# 3. 통합 테스트 — fixtures 기반 mock dry-run + 골든 비교
echo ""
echo "=== Integration Tests (fixtures) ==="
FIXTURE_ROOT=/Users/zime/.codex/skills/dev-advisor/references/research/fixtures
for fixture_file in "$FIXTURE_ROOT"/*/*.json; do
  case_id=$(python3 -c "import json,sys; print(json.load(open('$fixture_file'))['case_id'])" 2>/dev/null || echo "unknown")
  echo "  Testing: ${case_id}"
  # mock 응답 주입 후 HR-01~HR-10 자동 검증 (§6 참조)
done

# 4. 회귀 테스트 — 기존 모드 smoke
echo ""
echo "=== Regression Tests ==="
python3 /Users/zime/.codex/skills/dev-advisor/scripts/generate-catalog-index.py --check

# 5. 환각 회귀 — HR-01~HR-10
echo ""
echo "=== Hallucination Regression (HR-01~HR-10) ==="
bash /Users/zime/.codex/skills/dev-advisor/scripts/verify-references.sh --check research-hallucination
```

---

## 9. 참조

| 섹션 | 내용 |
|------|------|
| `PLAN-research-mode.md §11.1` | 사전 차단 정책 — 식별자 정규식 4종 |
| `PLAN-research-mode.md §19.1~§19.5` | 테스트 매트릭스 원본 |
| `PLAN-research-mode.md §10.2` | URL 화이트리스트 (`arxiv.org`/`doi.org`/`semanticscholar.org`/`openalex.org`) |
| `PLAN-research-mode.md §8.13` | verify-references.sh 확장 명세 |
| `PLAN-research-mode.md §14.5` | Phase 2 Pre-flight Gate (OpenAlex Topics ID 사전 검증) |
| `PLAN-research-mode.md §17` | Graceful Degradation (부분 장애 매트릭스) |
| `references/research/sources.md` | OpenAlex Topics ID 검증 로그 (HR-13 근거) |
| `references/research/mapping-algorithm.md` | HIGH/MED/LOW 판정 알고리즘 (U-03 골든 기준) |
| `references/research/fallback.md` | 부분 장애 처리 상세 |
| `references/research/performance.md` | p95 latency < 15s, timeout 5s/20s 정책 |
