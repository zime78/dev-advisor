# Research Mode Fixtures

`verify-references.sh` 11-12 및 research mode 자동 검증을 위한 mock fixture JSON 파일 모음.

## 디렉토리 구조

```
fixtures/
├── normal/                         정상 케이스 (3-of-3 source 응답)
│   ├── 01-transformer-vaswani.json   Vaswani et al. 2017 "Attention Is All You Need"
│   └── 02-bert-devlin.json           Devlin et al. 2019 "BERT"
├── partial-failure/                부분 장애 케이스
│   └── 01-s2-503.json                Semantic Scholar 503 → degraded mode (2-of-3)
├── zero-result/                    0건 케이스
│   └── 01-nonexistent-keyword.json   3-source 모두 200 + result_count=0
└── schema-drift/                   스키마 변동 케이스
    └── 01-s2-missing-tldr.json       S2 tldr 필드 누락 → fallback 검증
```

## 각 fixture 설명

### normal/01-transformer-vaswani.json

- 검증 논문: Vaswani et al. (2017). "Attention Is All You Need". NeurIPS.
- arXiv ID: `1706.03762` / DOI: `10.48550/arXiv.1706.03762`
- 3-of-3 source 모두 HTTP 200 응답
- HR-01(식별자), HR-02(regex), HR-03(URL whitelist), HR-08(catalog mapping), HR-10(not retracted) 전부 PASS
- catalog_mapping: `/algorithm transformer`

### normal/02-bert-devlin.json

- 검증 논문: Devlin et al. (2019). "BERT: Pre-training of Deep Bidirectional Transformers". NAACL.
- arXiv ID: `1810.04805` / DOI: `10.18653/v1/N19-1423`
- 3-of-3 source 모두 HTTP 200 응답
- HR-01~03, HR-08, HR-10 전부 PASS
- catalog_mapping: `/algorithm bert`

### partial-failure/01-s2-503.json

- 쿼리: `neural architecture search`
- Semantic Scholar → HTTP 503 (Service Unavailable)
- arXiv + OpenAlex → HTTP 200 정상
- 예상 동작: degraded mode 배너 출력, 인용수 OpenAlex only, TLDR은 abstract fallback
- HR-06(degraded mode handling) PASS 검증

### zero-result/01-nonexistent-keyword.json

- 쿼리: `비존재하는키워드xyz123`
- 3-source 모두 HTTP 200이나 result_count=0
- 예상 동작: 0건 안내 + 재정제 제안 3가지 + researcher hand-off 옵션
- HR-05(0건 처리), HR-07(재정제 제안) PASS 검증

### schema-drift/01-s2-missing-tldr.json

- 검증 논문: Kipf & Welling (2017). "Semi-Supervised Classification with Graph Convolutional Networks". ICLR.
- arXiv ID: `1609.02907`
- S2 응답에 `tldr` 키 자체가 없음 (null이 아닌 key absent)
- fallback chain: S2 tldr → S2 abstract 첫 문장 → arXiv summary 첫 문장 → 'n/a'
- HR-04(schema drift fallback) PASS 검증

## 사용 방법

### JSON 유효성 검증

```bash
# 전체 fixture JSON 파싱 확인
find /Users/zime/.codex/skills/dev-advisor/references/research/fixtures -name "*.json" \
  -exec sh -c 'jq . "$1" > /dev/null && echo "PASS: $1" || echo "FAIL: $1"' _ {} \;
```

### 파일 수 확인

```bash
find /Users/zime/.codex/skills/dev-advisor/references/research/fixtures -name "*.json" | wc -l
# 기대값: 5
```

### verify-references.sh 통합

`verify-references.sh` Phase 11-12에서 이 fixtures를 참조하여 각 케이스별 예상 동작을 검증한다.

```bash
# Phase 11: fixture 존재 및 JSON 유효성 검사
# Phase 12: fixture별 expected_validation 규칙 통과 확인
```

## fixture 추가 규칙

1. 파일명: `{순번}-{논문저자}-{키워드}.json` (normal) / `{순번}-{소스}-{에러코드}.json` (partial-failure)
2. 실제 존재하는 논문만 인용 — 환각(hallucination) 금지
3. DOI regex: `^10\.\d{4,9}/\S+$` 통과 형식 사용
4. arXiv ID regex: `^[0-9]{4}\.[0-9]{4,5}$` 통과 형식 사용 (예: `1706.03762`)
5. `is_retracted: false` 필드 포함 (HR-10 검증용)
6. `expected_validation` 블록에 HR 규칙 번호와 PASS/FAIL 명시

## HR 규칙 번호 참조

| 번호 | 설명 |
|------|------|
| HR-01 | 식별자(DOI/arXiv ID) 존재 확인 |
| HR-02 | 식별자 정규식 형식 검증 |
| HR-03 | URL whitelist 통과 (arxiv.org, doi.org, openalex.org, semanticscholar.org) |
| HR-04 | schema drift fallback 정책 동작 확인 |
| HR-05 | 0건 결과 처리 출력 확인 |
| HR-06 | degraded mode (2-of-3) 배너 및 동작 확인 |
| HR-07 | 재정제 제안 출력 확인 |
| HR-08 | catalog mapping 경로 정확성 확인 |
| HR-10 | 철회(retracted) 논문 필터링 확인 |
