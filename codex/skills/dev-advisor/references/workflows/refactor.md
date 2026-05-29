# `refactor` 모드 — 리팩토링 단계별 가이드

코드/함수의 Before/After 코드, 단계별 절차, 회귀 위험 등급을 제시한다.

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 코드/함수 필수 | 단계 표 + Before/After 코드 + 회귀 위험 등급 |

## 인용 references

- [`references/code_templates.md`](../code_templates.md)
- [`references/patterns/architectural.md`](../patterns/architectural.md)
- [`references/patterns/ddd-tactical.md`](../patterns/ddd-tactical.md)
- [`references/principles/code-smells.md#5-그룹-진입점`](../principles/code-smells.md#5-그룹-진입점) — 스멜 → 리팩토링
- [`references/principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙`](../principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙)
- [`references/principles/solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙`](../principles/solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙)

## 공통 6단계 절차

1. **입력 수집** — 코드/함수 필수
2. **컨텍스트 분류** — 언어 자동 감지, 프로젝트 규모, 스택 신호
3. **기준 매핑** — 위 "인용 references" 항목 식별
4. **분석/판정** — 단계 표 + Before/After 코드 + 회귀 위험 등급
5. **근거 산출 (필수)** — 아래 6 필드 템플릿
6. **검증/후속 계획** — 회귀 테스트 + 재검증 명령 + `code-reviewer` PR 검토

## 5단계 6 필드 공통 템플릿 (필수)

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호
- **대안 비교**: A vs B vs C 형태로 대안 2~3개 + 각 trade-off
- **표준 인용**: SOLID / GRASP / ISO 25010 / 12-Factor / DDD / Clean Architecture / OWASP / NIST / RFC 등 직접 anchor link
- **적용 조건**: 이 결정이 유효한 컨텍스트
- **비추천 조건**: 이 리팩토링을 안 써야 할 때

## 산출물 출력 스켈레톤

```
## Refactor — <file|function>

### 단계
| # | 작업 | 파일 | 회귀 위험 (HIGH/MED/LOW) |

### Before
```code
...
```

### After
```code
...
```

### 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천 조건
```

## OMX hand-off 후보

- 리팩토링 PR 검토 → `code-reviewer`
- 변경 후 회귀 확인 → `verifier`
