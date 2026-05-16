# QC 카탈로그

QC(Quality Control)는 실제 산출물과 실행 결과가 기준을 만족하는지 확인하는 검증 활동이다. 테스트 실행, 결함 재현, 빌드 검증, 품질 게이트 통과 증거처럼 릴리즈 판단에 사용할 수 있는 관찰 가능한 결과에 초점을 둔다.

<a id="qc-build-verification"></a>
## 1. Build Verification

- **목적**: 빌드 산출물이 재현 가능하고 기본 실행 조건을 만족하는지 확인한다.
- **입력**: CI build log, artifact checksum, dependency lockfile, smoke test result.
- **판정 기준**: main build 성공, artifact 생성, checksum 기록, smoke test 통과.
- **출력 증거**: build URL, artifact ID, version, smoke result.
- **실패 시 조치**: 빌드 실패 원인을 blocker로 등록하고 배포 후보에서 제외한다.

<a id="qc-test-execution-evidence"></a>
## 2. Test Execution Evidence

- **목적**: 테스트가 실제로 실행되었고 결과가 추적 가능한 형태로 남았는지 확인한다.
- **입력**: test run ID, coverage report, junit/xml/html report, 수동 테스트 기록.
- **판정 기준**: 실행 시간, 대상 버전, pass/fail, 실패 로그가 모두 기록되어야 한다.
- **출력 증거**: test summary, 실패 케이스 링크, coverage delta.
- **실패 시 조치**: 증거 누락 테스트는 미실행으로 간주하고 재실행한다.

<a id="qc-functional-verification"></a>
## 3. Functional Verification

- **목적**: 기능 산출물이 승인 기준과 사용자 흐름을 만족하는지 확인한다.
- **입력**: acceptance criteria, test case, API response, UI screenshot, DB 상태.
- **판정 기준**: 정상/예외/권한/경계값 시나리오가 기대 결과와 일치해야 한다.
- **출력 증거**: pass/fail matrix, screenshot, response sample, 로그.
- **실패 시 조치**: 불일치 항목은 결함으로 등록하고 요구사항 또는 구현 중 하나를 수정한다.

<a id="qc-nonfunctional-verification"></a>
## 4. Nonfunctional Verification

- **목적**: 성능, 안정성, 보안, 접근성, 호환성 등 비기능 기준을 검증한다.
- **입력**: SLA/SLO, load test, security scan, accessibility report, compatibility matrix.
- **판정 기준**: 사전에 합의한 임계값과 예외 승인 조건을 충족해야 한다.
- **출력 증거**: latency/error rate, scan result, accessibility violations, device/browser result.
- **실패 시 조치**: 임계값 초과는 릴리즈 위험으로 등록하고 owner와 완화책을 지정한다.

<a id="qc-regression-result"></a>
## 5. Regression Result Review

- **목적**: 변경 후 기존 기능이 깨지지 않았다는 회귀 테스트 결과를 확인한다.
- **입력**: regression suite, impacted test list, flaky test status, rerun evidence.
- **판정 기준**: critical path 실패 0건, flaky 분류 근거, rerun 결과가 있어야 한다.
- **출력 증거**: regression summary, fail trend, waived tests.
- **실패 시 조치**: critical path 실패는 release blocker로 올리고 flaky는 별도 격리한다.

<a id="qc-defect-reproduction"></a>
## 6. Defect Reproduction Evidence

- **목적**: 결함을 동일 조건에서 재현하고 수정 후 재검증 가능한 증거를 확보한다.
- **입력**: defect ticket, reproduction steps, environment, logs, screen recording.
- **판정 기준**: 재현 절차, 기대 결과, 실제 결과, 환경 버전이 명확해야 한다.
- **출력 증거**: reproduction log, before/after result, fixed version.
- **실패 시 조치**: 재현 불가 결함은 정보 요청 상태로 전환하고 release blocker 여부를 재판정한다.

<a id="qc-quality-gate"></a>
## 7. Quality Gate Check

- **목적**: 릴리즈 또는 merge 전에 정량 품질 조건을 자동/수동으로 확인한다.
- **입력**: CI checks, coverage threshold, lint, SAST/DAST, defect count, approval status.
- **판정 기준**: 필수 gate는 모두 PASS이고 예외는 승인 기록이 있어야 한다. gate는 merge gate / release gate / production gate로 분리해 판정한다.
- **출력 증거**: gate dashboard, failed checks, approval exception.
- **실패 시 조치**: gate 실패는 merge/release 차단으로 처리하고 예외는 소유자 승인을 요구한다.

**gate 계층**:

| Gate | 필수 증거 | 실패 시 조치 |
|---|---|---|
| Merge gate | build, lint, unit, typecheck, SAST/secrets 기본 스캔 | merge hold |
| Release gate | E2E/회귀, DAST/SCA, SBOM/provenance, rollback plan, release note | go/no-go 보류 |
| Production gate | smoke, metrics, alert 상태, data integrity, rollback readiness | rollback 또는 feature flag off |
| Waiver policy | 소유자, 만료일, 대체 통제, 재검토 조건 | 조건 미충족 시 waiver 거부 |

<a id="qc-release-blocker-check"></a>
## 8. Release Blocker Check

- **목적**: 릴리즈를 중단해야 하는 결함, 운영 위험, 보안 갭이 남아 있는지 확인한다.
- **입력**: blocker policy, open defects, severity list, incident risk, rollback readiness.
- **판정 기준**: P1/blocker 0건 또는 명시적 go/no-go 승인이 있어야 한다.
- **출력 증거**: blocker list, go/no-go result, waiver record.
- **실패 시 조치**: release hold, scope reduction, hotfix branch 중 하나로 전환한다.

<a id="qc-data-integrity-check"></a>
## 9. Data Integrity Check

- **목적**: 데이터 마이그레이션, 배치, API 변경 후 데이터 무결성을 확인한다.
- **입력**: migration log, row count, checksum, invariant query, reconciliation report.
- **판정 기준**: 행 수, checksum, 참조 무결성, 핵심 business invariant가 기대 범위에 있어야 한다.
- **출력 증거**: before/after count, mismatch list, rollback verification.
- **실패 시 조치**: mismatch를 차단 결함으로 등록하고 rollback 또는 repair script를 실행한다.

<a id="qc-post-release-smoke"></a>
## 10. Post-Release Smoke

- **목적**: 배포 후 실제 환경에서 핵심 사용자 경로와 관측 지표가 정상인지 확인한다.
- **입력**: production URL, synthetic checks, logs, metrics, feature flag 상태.
- **판정 기준**: 핵심 smoke path 통과, error rate/latency 정상, 알림 미발생.
- **출력 증거**: smoke run ID, dashboard snapshot, incident 여부.
- **실패 시 조치**: rollback, feature flag off, hotfix escalation 중 하나를 실행한다.
