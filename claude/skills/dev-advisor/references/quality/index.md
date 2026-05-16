# Quality 카탈로그

QA/QC 카탈로그는 품질 활동을 **계획·프로세스 중심 QA**와 **실행·증거 중심 QC**로 분리한다. `/quality` lookup 은 `list / search / <id>` 표면을 제공하며, advisor 모드에서는 `/dev-advisor qa <module|path>`와 `/dev-advisor qc <module|path>`로 직접 호출한다.

## 호출 인터페이스

| 명령 | 예시 | 동작 |
|---|---|---|
| `/quality list` | `/quality list` | QA 10개 + QC 10개 진입점 표 |
| `/quality search <kw>` | `/quality search release` | ID, 별칭, 한글명, 태그 기준 후보 검색 |
| `/quality <id>` | `/quality qa-test-strategy` | `quality/<file>.md#<id>` 본문 조회 |

## 카테고리

| 카테고리 | 파일 | 항목 수 | 초점 |
|---|---|---:|---|
| QA | [qa.md](qa.md) | 10 | 요구사항, 테스트 전략, 추적성, 릴리즈 승인 등 프로세스 품질 |
| QC | [qc.md](qc.md) | 10 | 실제 산출물 검증, 테스트 실행, 품질 게이트, 결함 증거 |

## Quality ID 매핑

| ID | 파일 | 이름 | 태그 |
|---|---|---|---|
| `qa-requirements-traceability` | [qa.md#qa-requirements-traceability](qa.md#qa-requirements-traceability) | Requirements Traceability | qa, requirements, traceability |
| `qa-test-strategy` | [qa.md#qa-test-strategy](qa.md#qa-test-strategy) | Test Strategy | qa, strategy, coverage |
| `qa-risk-based-testing` | [qa.md#qa-risk-based-testing](qa.md#qa-risk-based-testing) | Risk-Based Testing | qa, risk, prioritization |
| `qa-acceptance-criteria` | [qa.md#qa-acceptance-criteria](qa.md#qa-acceptance-criteria) | Acceptance Criteria Review | qa, acceptance, requirements |
| `qa-test-plan-review` | [qa.md#qa-test-plan-review](qa.md#qa-test-plan-review) | Test Plan Review | qa, planning, readiness |
| `qa-release-readiness` | [qa.md#qa-release-readiness](qa.md#qa-release-readiness) | Release Readiness Review | qa, release, go-no-go |
| `qa-defect-triage` | [qa.md#qa-defect-triage](qa.md#qa-defect-triage) | Defect Triage Governance | qa, defects, priority |
| `qa-change-impact-analysis` | [qa.md#qa-change-impact-analysis](qa.md#qa-change-impact-analysis) | Change Impact Analysis | qa, change, regression |
| `qa-regression-scope` | [qa.md#qa-regression-scope](qa.md#qa-regression-scope) | Regression Scope Design | qa, regression, scope |
| `qa-compliance-evidence-plan` | [qa.md#qa-compliance-evidence-plan](qa.md#qa-compliance-evidence-plan) | Compliance Evidence Plan | qa, compliance, evidence |
| `qc-build-verification` | [qc.md#qc-build-verification](qc.md#qc-build-verification) | Build Verification | qc, build, smoke |
| `qc-test-execution-evidence` | [qc.md#qc-test-execution-evidence](qc.md#qc-test-execution-evidence) | Test Execution Evidence | qc, test-run, evidence |
| `qc-functional-verification` | [qc.md#qc-functional-verification](qc.md#qc-functional-verification) | Functional Verification | qc, functional, behavior |
| `qc-nonfunctional-verification` | [qc.md#qc-nonfunctional-verification](qc.md#qc-nonfunctional-verification) | Nonfunctional Verification | qc, performance, reliability |
| `qc-regression-result` | [qc.md#qc-regression-result](qc.md#qc-regression-result) | Regression Result Review | qc, regression, result |
| `qc-defect-reproduction` | [qc.md#qc-defect-reproduction](qc.md#qc-defect-reproduction) | Defect Reproduction Evidence | qc, defects, reproduction |
| `qc-quality-gate` | [qc.md#qc-quality-gate](qc.md#qc-quality-gate) | Quality Gate Check | qc, gate, release |
| `qc-release-blocker-check` | [qc.md#qc-release-blocker-check](qc.md#qc-release-blocker-check) | Release Blocker Check | qc, blocker, go-no-go |
| `qc-data-integrity-check` | [qc.md#qc-data-integrity-check](qc.md#qc-data-integrity-check) | Data Integrity Check | qc, data, integrity |
| `qc-post-release-smoke` | [qc.md#qc-post-release-smoke](qc.md#qc-post-release-smoke) | Post-Release Smoke | qc, production, smoke |

## 별칭

| 별칭 | Primary ID |
|---|---|
| `traceability` | `qa-requirements-traceability` |
| `test-strategy` | `qa-test-strategy` |
| `release-readiness` | `qa-release-readiness` |
| `quality-gate` | `qc-quality-gate` |
| `test-evidence` | `qc-test-execution-evidence` |
| `post-release-smoke` | `qc-post-release-smoke` |

## `/quality <id>` 호출 동작

1. 별칭 표에서 primary ID를 정규화한다.
2. 위 `Quality ID 매핑` 표에서 파일과 anchor를 찾는다.
3. 본문은 목적, 입력 증거, 판정 기준, 출력 산출물, 실패 시 조치를 함께 제공한다.
