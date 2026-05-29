# `validate` 모드 — 코드/구조 검증

기존 코드/모듈을 표준(SOLID/GRASP/DDD/Clean Arch/ISO 25010/12-Factor/OWASP/NIST)에 따라 검증하고 위반 항목을 우선순위(P1/P2/P3)별로 정리한다.

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 코드/모듈 필수 | 위반 표: 위치 / 표준 / 심각도 P1/P2/P3 / 영향 / 조치 |

## 인용 references

- [`references/patterns/architectural.md`](../patterns/architectural.md)
- [`references/patterns/ddd-tactical.md`](../patterns/ddd-tactical.md)
- [`references/patterns/index.md`](../patterns/index.md)
- [`references/security/index.md`](../security/index.md)
- [`references/principles/solid.md`](../principles/solid.md) — 5 원칙 anchor
- [`references/principles/grasp.md`](../principles/grasp.md) — 9 원칙 anchor
- [`references/principles/iso25010.md`](../principles/iso25010.md) — 8 품질 특성 anchor
- [`references/principles/12-factor.md`](../principles/12-factor.md) — 12 인자 anchor

위반 항목별 specific anchor 권장.

## 공통 6단계 절차

1. **입력 수집** — 코드/모듈 필수
2. **컨텍스트 분류** — 언어 자동 감지, 프로젝트 규모, 스택 신호, 도메인 분류
3. **기준 매핑** — 위 "인용 references" 항목 식별
4. **분석/판정** — 위반 표 작성 (위치 / 표준 / 심각도 P1/P2/P3 / 영향 / 조치)
5. **근거 산출 (필수)** — 아래 6 필드 템플릿
6. **검증/후속 계획** — 회귀 테스트 + 재검증 명령 + OMC `code-reviewer` hand-off (P1 위반 수정 후 PR)

## 5단계 6 필드 공통 템플릿 (필수)

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호
- **대안 비교**: A vs B vs C 형태로 대안 2~3개 + 각 trade-off
- **표준 인용**: SOLID / GRASP / ISO 25010 / 12-Factor / DDD / Clean Architecture / OWASP / NIST / RFC 등 직접 anchor link
- **적용 조건**: 이 결정이 유효한 컨텍스트
- **예외·면제 조건**: 표준 carve-out, compliance exception

## 산출물 출력 스켈레톤

```
## Validate — <file|module>

### 위반 항목
| # | 위치 | 표준 | 심각도 (P1/P2/P3) | 영향 | 조치 |

### 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 예외·면제 조건
```

## 공통 severity 정규화

| 등급 | 정의 |
|------|------|
| P1 | 차단 위반, 데이터 손실, 런타임 장애, 회귀 위험 HIGH |
| P2 | 유지보수 비용 증가, SLA 위협, 회귀 위험 MED |
| P3 | 관찰/스타일/미래 부채, 회귀 위험 LOW |

## OMC hand-off 후보

- P1 위반 수정 후 PR → `code-reviewer`
- 회귀 검증 → `verifier`
