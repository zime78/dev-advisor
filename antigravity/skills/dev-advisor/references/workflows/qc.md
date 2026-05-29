# `qc` 모드 — 품질 관리 (Quality Control)

빌드, 테스트 실행, 결함 재현, 품질 게이트, post-release smoke 등 **실제 산출물 검증 증거**를 확인한다. 증거가 없으면 실행하지 않은 것으로 간주한다.

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 모듈/path 필수 | 빌드/테스트 실행 증거 + 결함 재현 + 품질 게이트 + 릴리즈 차단 증거 |

## 인용 references

- [`references/quality/index.md`](../quality/index.md)
- [`references/quality/qc.md`](../quality/qc.md)
- [`references/patterns/testing.md`](../patterns/testing.md)
- [`references/patterns/testing-strategies.md`](../patterns/testing-strategies.md)
- [`references/principles/process-metrics.md`](../principles/process-metrics.md)

## qc 모드 절차 (품질 관리)

1. **입력 수집** — 모듈/path, CI run, 테스트 리포트, 결함 티켓, 배포 후보 artifact
2. **컨텍스트 분류** — 배포 단계, 품질 gate, critical path, known issue
3. **QC 기준 매핑** — [`quality/qc.md`](../quality/qc.md)의 build verification / test evidence / quality gate 항목 매핑
4. **증거 검증** — 빌드 산출물, 테스트 결과, 회귀 결과, blocker, 데이터 무결성 확인
5. **근거 산출** — 단일 6 필드 + 차단·재검증 조건 명시
6. **후속 계획** — 재실행 명령, 결함 재현, release hold / rollback / hotfix 분기

## 5단계 6 필드 공통 템플릿 (필수)

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호
- **대안 비교**: A vs B vs C 형태로 대안 2~3개 + 각 trade-off
- **표준 인용**: SOLID / GRASP / ISO 25010 / 12-Factor / DDD / Clean Architecture / OWASP / NIST / RFC 등 직접 anchor link
- **적용 조건**: 이 결정이 유효한 컨텍스트
- **차단·재검증 조건**: 품질 게이트 실패, 재실행 필요 조건

## 산출물 출력 스켈레톤

```
## QC — <module|path>

### 빌드/테스트 실행 증거
| # | artifact | run id | 결과 | 비고 |

### 결함 재현
| # | 결함 | 재현 절차 | 상태 |

### 품질 게이트
| # | gate | 기준 | 결과 (PASS/WARN/FAIL) | 증거 |

### 릴리즈 차단 증거
<blocker 리스트>

### 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 차단·재검증 조건
```

## 공통 severity 정규화

| 등급 | 정의 |
|------|------|
| P1 | failed required gate, critical path 실패, 증거 누락, 데이터 mismatch |
| P2 | WARN gate, flaky 미분류, 재실행 필요 |
| P3 | 비차단 증거 보완 |

## OMC hand-off 후보

- 재실행 후 회귀 검증 → `verifier`
- 결함 PR 수정 → `code-reviewer`
