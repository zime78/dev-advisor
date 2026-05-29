# `recommend` 모드 — 추천 + 근거

대상 도메인/제약에 맞는 패턴·알고리즘·언어·통제·원칙·품질 활동 후보를 매트릭스로 제시하고, 선택 근거와 대안 trade-off를 명시한다.

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 도메인 + 제약 (코드 선택) | 후보 매트릭스 3~5행: ID / 적합 컨텍스트 / trade-off / score |

## 인용 references

- [`references/patterns/index.md`](../patterns/index.md)
- [`references/algorithms/index.md`](../algorithms/index.md)
- [`references/languages/index.md`](../languages/index.md)
- [`references/principles/iso25010.md`](../principles/iso25010.md) — 품질 특성 기준
- [`references/principles/grasp.md`](../principles/grasp.md) — 책임 할당

## 공통 6단계 절차

1. **입력 수집** — 도메인 + 제약 (코드 선택)
2. **컨텍스트 분류** — 언어 자동 감지, 프로젝트 규모, 스택 신호, 도메인 분류
3. **기준 매핑** — 위 "인용 references" 항목 식별
4. **분석/판정** — 후보 매트릭스 3~5행 작성 (ID / 적합 컨텍스트 / trade-off / score)
5. **근거 산출 (필수)** — 아래 6 필드 템플릿
6. **검증/후속 계획** — 회귀 테스트 + 재검증 명령 + OMX 에이전트 hand-off 후보 (아키텍처 영향 ≥ 3 파일 → `architect`)

## 5단계 6 필드 공통 템플릿 (필수)

어느 하나라도 빠지면 응답 불완전.

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호
- **대안 비교**: A vs B vs C 형태로 대안 2~3개 + 각 trade-off
- **표준 인용**: SOLID / GRASP / ISO 25010 / 12-Factor / DDD / Clean Architecture / OWASP / NIST / RFC 등 직접 anchor link
- **적용 조건**: 이 결정이 유효한 컨텍스트
- **비추천 조건**: 이 패턴/통제를 안 써야 할 때

## 산출물 출력 스켈레톤

```
## Recommend — <도메인 + 제약>

### 후보 매트릭스
| # | ID | 적합 컨텍스트 | Trade-off | Score |

### 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천 조건
```

## OMX hand-off 후보

- 아키텍처 영향 ≥ 3 파일 / 계층 재설계 → `architect`
- 구현 진행 → `executor`
