# QA 카탈로그

QA(Quality Assurance)는 품질을 사전에 보장하기 위한 프로세스, 기준, 추적성, 승인 활동이다. 산출물 실행 자체보다 "무엇을 어떻게 검증해야 하는가"와 "릴리즈 판단을 어떤 근거로 승인하는가"에 초점을 둔다.

<a id="qa-requirements-traceability"></a>
## 1. Requirements Traceability

- **목적**: 요구사항, 설계, 구현, 테스트, 결함을 추적 가능한 단위로 연결한다.
- **입력**: 요구사항 ID, 사용자 스토리, 테스트 케이스, 결함 티켓, 변경 요청.
- **판정 기준**: 핵심 요구사항마다 최소 1개 검증 케이스와 결과 증거가 연결되어야 한다.
- **출력 산출물**: traceability matrix, 누락 요구사항 목록, 릴리즈 차단 요구사항 목록.
- **실패 시 조치**: 누락 요구사항을 P1/P2/P3로 분류하고 테스트 설계 또는 범위 변경 승인을 요청한다.

<a id="qa-test-strategy"></a>
## 2. Test Strategy

- **목적**: 단위, 통합, E2E, 성능, 보안, 수동 검증의 역할과 경계를 정한다.
- **입력**: 시스템 아키텍처, 위험 영역, 팀 역량, 자동화 수준, 릴리즈 주기.
- **판정 기준**: 위험도가 높은 경로가 더 깊은 테스트 레벨에서 검증되고 중복 테스트 비용이 통제되어야 한다.
- **출력 산출물**: 테스트 레벨 매트릭스, 자동화 우선순위, 제외 범위, 환경 요구사항.
- **실패 시 조치**: coverage gap을 릴리즈 위험으로 등록하고 검증 책임자를 지정한다.

<a id="qa-risk-based-testing"></a>
## 3. Risk-Based Testing

- **목적**: 비즈니스 영향과 변경 가능성이 높은 영역에 테스트 노력을 우선 배치한다.
- **입력**: 변경 diff, 장애 이력, 고객 영향도, 보안/규제 민감도, 모듈 복잡도.
- **판정 기준**: high risk 영역은 릴리즈 전 명시적 검증 증거를 가져야 한다.
- **출력 산출물**: risk heatmap, 테스트 우선순위, 수용 가능한 잔여 위험.
- **실패 시 조치**: high risk 미검증 항목을 release blocker 또는 승인 예외로 분류한다.

<a id="qa-acceptance-criteria"></a>
## 4. Acceptance Criteria Review

- **목적**: 요구사항이 테스트 가능한 문장과 예외 조건으로 표현되었는지 확인한다.
- **입력**: 사용자 스토리, PRD, Gherkin 시나리오, API 계약, 디자인 시안.
- **판정 기준**: 성공 조건, 실패 조건, 경계값, 권한 조건, 데이터 상태가 명확해야 한다.
- **출력 산출물**: 승인 기준 보완 목록, 테스트 가능성 판정, 모호성 로그.
- **실패 시 조치**: 모호한 기준은 구현 전에 제품/설계 소유자에게 되돌린다.

<a id="qa-test-plan-review"></a>
## 5. Test Plan Review

- **목적**: 테스트 계획이 요구사항, 일정, 환경, 데이터, 책임자와 일치하는지 검토한다.
- **입력**: 테스트 계획서, sprint scope, 환경 구성, fixture/data 준비 상태.
- **판정 기준**: 일정 안에 실행 가능한 범위와 명확한 exit criteria가 있어야 한다.
- **출력 산출물**: test plan approval, 준비 부족 항목, 일정 리스크.
- **실패 시 조치**: 계획 범위 축소, 환경 확보, 테스트 데이터 보강 중 하나를 결정한다.

<a id="qa-release-readiness"></a>
## 6. Release Readiness Review

- **목적**: 릴리즈 전 품질, 보안, 운영, 문서, 지원 준비 상태를 승인한다.
- **입력**: 테스트 요약, 미해결 결함, rollback plan, runbook, 모니터링 대시보드.
- **판정 기준**: blocker 결함 0건, 승인된 known issue, rollback 경로, 관측 지표가 준비되어야 한다.
- **출력 산출물**: go/no-go 결정, 승인자 목록, 조건부 승인 항목.
- **실패 시 조치**: 릴리즈 보류, 범위 축소, hotfix plan 중 하나를 선택한다.

<a id="qa-defect-triage"></a>
## 7. Defect Triage Governance

- **목적**: 결함의 심각도, 우선순위, 소유자, 릴리즈 영향 판정을 일관되게 관리한다.
- **입력**: 결함 티켓, 재현 절차, 로그, 고객 영향도, SLA/규제 요구사항.
- **판정 기준**: severity와 priority가 분리되어야 하며 blocker 기준이 문서화되어야 한다.
- **출력 산출물**: triage board, blocker list, deferred defect 승인 기록.
- **실패 시 조치**: 판정 기준을 재합의하고 미분류 결함을 릴리즈 전까지 해소한다.

<a id="qa-change-impact-analysis"></a>
## 8. Change Impact Analysis

- **목적**: 변경이 영향을 주는 기능, 데이터, API, 운영 흐름, 회귀 범위를 사전에 산정한다.
- **입력**: diff, dependency graph, API contract, schema migration, feature flag 계획.
- **판정 기준**: 영향 경로마다 검증 책임과 rollback 조건이 연결되어야 한다.
- **출력 산출물**: impact map, regression 후보, 운영 위험, stakeholder notification.
- **실패 시 조치**: 영향 미확인 변경은 배포 범위에서 제외하거나 추가 검토로 보낸다.

<a id="qa-regression-scope"></a>
## 9. Regression Scope Design

- **목적**: 변경별 회귀 테스트 범위를 과소/과대 실행 없이 설계한다.
- **입력**: 변경 영역, 기존 테스트 맵, 결함 이력, critical user journey.
- **판정 기준**: 핵심 사용자 경로, 인접 모듈, 계약 경계가 최소 회귀 범위에 포함되어야 한다.
- **출력 산출물**: regression suite selection, 제외 근거, 실행 순서.
- **실패 시 조치**: 제외 근거가 약한 항목은 수동 검증 또는 자동화 backlog로 이동한다.

<a id="qa-compliance-evidence-plan"></a>
## 10. Compliance Evidence Plan

- **목적**: 규제, 감사, 보안 표준에 필요한 품질 증거를 릴리즈 전에 계획한다.
- **입력**: 컴플라이언스 요구사항, 정책, 테스트 증거, 승인 기록, 로그 보존 조건.
- **판정 기준**: 각 요구사항에 재현 가능한 증거와 보존 위치가 있어야 한다.
- **출력 산출물**: evidence checklist, 감사 추적 링크, 보존 기간, 책임자.
- **실패 시 조치**: 증거 없는 요구사항은 릴리즈 예외 승인 또는 구현 보강이 필요하다.
