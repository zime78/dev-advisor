# `maintain` 모드 — 유지보수 / 기술 부채 점검

안티패턴, 코드 스멜 5 그룹, 기술 부채를 우선순위(영향 × 발생빈도)로 정리한다.

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 모듈/프로젝트 필수 | 부채 표 7~10행 + 우선순위 (영향 × 발생빈도) + 코드 스멜 5 그룹 |

## 인용 references

- [`references/principles/code-smells.md#5-그룹-진입점`](../principles/code-smells.md#5-그룹-진입점) — 22 스멜 5 그룹
- [`references/principles/iso25010.md#7-maintainability-유지보수성`](../principles/iso25010.md#7-maintainability-유지보수성)
- [`references/principles/12-factor.md`](../principles/12-factor.md) — 운영 부채
- [`references/patterns/index.md`](../patterns/index.md) — 역방향 적합도

## 공통 6단계 절차

1. **입력 수집** — 모듈/프로젝트 필수
2. **컨텍스트 분류** — 언어 자동 감지, 프로젝트 규모, 스택 신호, 도메인
3. **기준 매핑** — 위 "인용 references" 항목 식별
4. **분석/판정** — 부채 표 7~10행 + 우선순위 (영향 × 발생빈도) + 코드 스멜 5 그룹 분포
5. **근거 산출 (필수)** — 아래 6 필드 템플릿
6. **검증/후속 계획** — `$ai-slop-cleaner` (Dispensables 비중 ≥ 40%) + `verifier` 회귀

## 코드 스멜 5 그룹

22 스멜의 5 그룹 분류(Bloaters / OO Abusers / Change Preventers / Dispensables / Couplers) + 식별 신호 + 권장 리팩토링은 [`references/principles/code-smells.md#5-그룹-진입점`](../principles/code-smells.md#5-그룹-진입점) 참조.

## 5단계 6 필드 공통 템플릿 (필수)

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호
- **대안 비교**: A vs B vs C 형태로 대안 2~3개 + 각 trade-off
- **표준 인용**: SOLID / GRASP / ISO 25010 / 12-Factor / DDD / Clean Architecture / OWASP / NIST / RFC 등 직접 anchor link
- **적용 조건**: 이 결정이 유효한 컨텍스트
- **수용 가능 조건**: 이 부채를 그냥 두는 게 합리적일 때

## 산출물 출력 스켈레톤

```
## Maintain — <module|project>

### 부채 표
| # | 항목 | 5 그룹 | 영향 | 발생빈도 | 우선순위 |

### 코드 스멜 5 그룹 분포
Bloaters / OO Abusers / Change Preventers / Dispensables / Couplers — 비중 표기

### 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 수용 가능 조건
```

## OMX hand-off 후보

- Dispensables 그룹 비중 ≥ 40% → `$ai-slop-cleaner`
- 변경 후 회귀 확인 → `verifier`
