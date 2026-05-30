# `research` 모드 — 학술 논문 + 카탈로그 cross-ref

키워드/카탈로그 ID/자유 질문 입력에 대해 arXiv / Semantic Scholar / OpenAlex 무료 API를 통합 검색하고, 카탈로그 6 도메인 cross-ref와 함께 논문 매트릭스를 산출한다.

`full` / `swarm`에 미포함 — 독립 모드 (토큰 한계 + 외부 API 의존성 격리).

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 키워드/카탈로그 ID/자유 질문 + 옵션 (`--limit`/`--years`/`--source`/`--bias`) | 논문 매트릭스 8~10행 + 6 필드 + degraded mode 배너(필요시) |

## 옵션

```
/dev-advisor research <topic|catalog-id|query>
  [--limit N]                # 결과 행 수 (기본 8)
  [--years YYYY-YYYY]        # 발표 연도 범위
  [--source arxiv|s2|openalex|all]   # 단일 또는 통합
  [--bias recency|citation]  # 정렬/가중치 편향
```

## 인용 references

- [`references/research/sources.md`](../research/sources.md) — 무료 학술 API 3 source 명세
- [`references/research/query-strategies.md`](../research/query-strategies.md) — 키워드/카탈로그 ID/자유 질문 → 쿼리 변환
- [`references/research/output-format.md`](../research/output-format.md) — 논문 매트릭스 + 6 필드 출력 포맷
- [`references/research/mapping-algorithm.md`](../research/mapping-algorithm.md) — 카탈로그 cross-ref 단방향 매핑 알고리즘
- [`references/research/fallback.md`](../research/fallback.md) — 0건/장애/한국어 검색 시 degraded mode
- [`references/research/performance.md`](../research/performance.md) — 캐싱 / Rate limit / 병렬 호출 정책
- 카탈로그 6 도메인 (cross-ref)

## 공통 6단계 절차

1. **입력 수집** — 키워드/카탈로그 ID/자유 질문 + 옵션
2. **컨텍스트 분류** — 한국어 입력 시 query-strategies 영문 변환, 학술 vs 산업 분류
3. **기준 매핑** — sources.md 3 API 호출 전략 + mapping-algorithm.md 카탈로그 cross-ref
4. **분석/판정** — 논문 매트릭스 8~10행 작성 (제목 / 저자 / 연도 / 인용수 / 출처 / abstract / 카탈로그 cross-ref)
5. **근거 산출 (필수)** — 6 필드 + 3-source 교차 검증
6. **검증/후속 계획** — degraded mode 배너 (0건/한국어/장애 시) + `researcher` / `analyst` hand-off

## 5단계 6 필드 공통 템플릿 (필수)

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호 + 3-source 교차 검증 결과
- **대안 비교**: 검색 전략·source bias 대안 2~3개
- **표준 인용**: RFC / NIST / ISO / 표준 RFC 등 직접 anchor link (학술 논문 외)
- **적용 조건**: 이 결과가 유효한 컨텍스트
- **비추천 조건**: 이 결과 셋이 부적합한 컨텍스트 (편향, 시점, 도메인 불일치)

## 산출물 출력 스켈레톤

```
## Research — <topic|catalog-id|query>

### 논문 매트릭스
| # | 제목 | 저자 | 연도 | 인용수 | 출처 | abstract | 카탈로그 cross-ref |

### 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천 조건

[Degraded mode 배너 — 필요시]
```

## OMX hand-off 후보

> research 모드 hand-off 대상은 Codex에 실제 등록된 `researcher` / `analyst` 역할만 사용한다.

- 0건 / 한국어 검색 / 외부 학술 문서 다중 소스 → `researcher`
- 다수의 비교/요약/통계 분석 → `analyst`
