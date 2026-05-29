# `qa` 모드 — 품질 보증 (Quality Assurance)

요구사항, 테스트 전략, 추적성, 릴리즈 승인 등 **프로세스 중심** 품질을 점검한다. 실행 결과 자체보다 품질 활동이 충분히 설계되었는지와 승인 근거가 추적 가능한지가 핵심이다.

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 모듈/path 필수 | 요구사항 추적성 + 테스트 전략 + 릴리즈 준비도 + 프로세스 gap |

## 인용 references

- [`references/quality/index.md`](../quality/index.md)
- [`references/quality/qa.md`](../quality/qa.md)
- [`references/principles/sdlc-models.md`](../principles/sdlc-models.md)
- [`references/principles/standards-mapping.md`](../principles/standards-mapping.md)
- [`references/principles/iso25010.md`](../principles/iso25010.md)

## qa 모드 절차 (품질 보증)

1. **입력 수집** — 모듈/path, 요구사항/스토리, 릴리즈 범위, 테스트 전략 문서
2. **컨텍스트 분류** — 변경 유형, 위험 영역, 규제/감사 요구, 릴리즈 단계
3. **QA 기준 매핑** — [`quality/qa.md`](../quality/qa.md)의 traceability / test strategy / release readiness 항목 매핑
4. **프로세스 gap 분석** — 요구사항-테스트 매핑, acceptance criteria, regression scope, evidence plan 확인
5. **근거 산출** — 단일 6 필드 + 승인·면제 조건 명시
6. **후속 계획** — 누락 요구사항, 테스트 전략 보강, 릴리즈 go/no-go 결정

## 5단계 6 필드 공통 템플릿 (필수)

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호
- **대안 비교**: A vs B vs C 형태로 대안 2~3개 + 각 trade-off
- **표준 인용**: SOLID / GRASP / ISO 25010 / 12-Factor / DDD / Clean Architecture / OWASP / NIST / RFC 등 직접 anchor link
- **적용 조건**: 이 결정이 유효한 컨텍스트
- **승인·면제 조건**: 품질 프로세스 예외, 릴리즈 조건부 승인

## 산출물 출력 스켈레톤

```
## QA — <module|path>

### 요구사항 추적성
| # | 요구사항 | 테스트 | 증거 |

### 테스트 전략
<단위/통합/E2E 분포, NFR 커버리지>

### 릴리즈 준비도
<go/no-go 체크리스트>

### 프로세스 gap
| # | gap | 영향 | 조치 |

### 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 승인·면제 조건
```

## 공통 severity 정규화

| 등급 | 정의 |
|------|------|
| P1 | release blocker, traceability 핵심 누락, threat model 미승인 |
| P2 | 조건부 승인 필요, regression scope gap |
| P3 | 문서 보강, 낮은 위험 known issue |

## OMC hand-off 후보

- 릴리즈 직전 회귀 확인 → `verifier`
- 보안 위반 우세 → `security-reviewer`
