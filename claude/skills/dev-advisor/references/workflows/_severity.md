# 공통 severity 정규화 + 통합 우선순위 매트릭스

`full` / `swarm` 통합 Top 10은 각 모드의 서로 다른 등급을 아래 공통 등급으로 정규화한 뒤 합산한다.

## 공통 severity 정규화 표

| 공통 등급 | validate/maintain/refactor | security-audit | qa | qc |
|---|---|---|---|---|
| P1 | 차단 위반, 데이터 손실, 런타임 장애, 회귀 위험 HIGH | Critical/High, CVSS ≥ 7.0, EPSS 상위권, CISA KEV 등재, 민감 데이터 high, blast radius 큼, exploitability 높음 | release blocker, traceability 핵심 누락, threat model 미승인 | failed required gate, critical path 실패, 증거 누락, 데이터 mismatch |
| P2 | 유지보수 비용 증가, SLA 위협, 회귀 위험 MED | Medium, OWASP Risk Rating Medium, 보완 통제 필요 | 조건부 승인 필요, regression scope gap | WARN gate, flaky 미분류, 재실행 필요 |
| P3 | 관찰/스타일/미래 부채, 회귀 위험 LOW | Low, exploitability 낮음, 승인된 risk acceptance | 문서 보강, 낮은 위험 known issue | 비차단 증거 보완 |

보안 risk acceptance는 소유자, 만료일, 대체 통제, 재검토 조건을 포함해야 하며, 민감 데이터·공개 노출·권한 상승 가능성이 있으면 기본값은 P1이다.

## full / swarm 통합 우선순위 매트릭스

7 모드 결과를 단일 점수로 합산해 Top 10 추출.

| 컬럼 | 정의 | 가중치 |
|---|---|---|
| **심각도** | P1=3 / P2=2 / P3=1 (validate / security-audit), DREAD 8~10=3 / 5~7=2 / 1~4=1 | × 3 |
| **영향** | 영향 파일 수 ≥ 5=3 / 2~4=2 / 1=1 | × 2 |
| **즉시성** | runtime crash / 보안 침해 가능=3 / 유지보수 부담=2 / 스타일=1 | × 2 |
| **점수** | `심각도×3 + 영향×2 + 즉시성×2` (max 21) | — |

같은 항목이 여러 모드에서 검출되면 **출처 모드** 컬럼에 모두 표기 (예: `validate, security-audit`). 중복 항목은 단일 행으로 합산.
