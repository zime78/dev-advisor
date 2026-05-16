# OMX/Codex 에이전트 hand-off 상세

dev-advisor advisor 7 모드 → 트리거 조건 도달 → Codex 전문 서브에이전트 또는 후속 OMX 스킬 hand-off. 각 대상의 정식 입출력 계약. SKILL.md `## OMX hand-off` 요약 표에서 참조.

---

## OMX hand-off

advisor 7 모드는 다음 트리거 조건 도달 시 Codex 전문 서브에이전트 또는 후속 OMX 스킬로 hand-off 한다. `architect` / `code-reviewer` / `security-reviewer` / `verifier` / `designer` / `planner` 는 Codex `spawn_agent` 대상이고, `$ai-slop-cleaner` 는 별도 스킬 호출 대상이다. 서브에이전트는 사용자가 `swarm`, 병렬 점검, 서브에이전트 사용을 명시했거나 상위 지침이 허용한 경우에만 사용한다.

### `architect` — 아키텍처 설계
- **트리거**: `recommend` 5단계 결과가 아키텍처 영향 ≥ 3 파일 / 계층 재설계 / 도메인 분해 / [database-fundamentals](principles/database-fundamentals.md) (CAP/PACELC/복제/파티셔닝 결정) / [master-data-management](patterns/master-data-management.md) (MDM 통합) / [data-quality-governance](patterns/data-quality-governance.md) (DQ 거버넌스 설계) / [data-warehousing-bi](patterns/data-warehousing-bi.md) (DWH 차원 모델링 / Lakehouse 선택 / SCD 정책) / [standards-mapping](principles/standards-mapping.md) (SWEBOK/CS2023/DMBOK/NIST/ISO 매핑 검증) / [formal-methods](principles/formal-methods.md) (안전 critical / 분산 합의 / 동시성 정합성 — TLA+ / Alloy / Hoare / Model Checking 적용 의사결정) / [hpc-scientific](patterns/hpc-scientific.md) (HPC 도메인 영향 — MPI/CUDA/SLURM 환경 / NUMA 토폴로지 / Roofline 모델 기반 성능 설계) 영향
- **인풋**: `{ context, candidates_matrix (3~5행), rationale_6fields, project_signals: { language, scale, stack } }`
- **산출**: ADR (Architecture Decision Record) + 컴포넌트 다이어그램 (Mermaid) + 계층 경계 + 인터페이스 계약
- **후속**: `executor` 구현. Codex 역할 에이전트의 기본 모델 정책을 우선하고, 별도 `model` 파라미터는 사용자가 명시적으로 요구하거나 작업상 필요성이 분명한 경우에만 지정한다.

### `code-reviewer` — 변경 검토
- **트리거**: `refactor` 6단계 후 PR / `validate` 식별 P1 위반 수정 후 PR / [professional-ethics](principles/professional-ethics.md) (ACM/IEEE 코드·다크패턴) 영향 검토 필요 / [configuration-management](principles/configuration-management.md) (CCB 의사결정 검증·Baseline 변경 / SPL Variant 영향) 영향 / [mobile-app#app-store-compliance](patterns/mobile-app.md#app-store-compliance) (Apple App Store / Google Play 심사 거부 사유 사전 점검 — Guideline 2.5.13 ATT / 3.1.1 IAP / 5.1.1 Privacy / Target API Level) / [mobile-app#mobile-advertising-attribution](patterns/mobile-app.md#mobile-advertising-attribution) (IDFA / AAID / ATT 프롬프트 / Data Safety Form / SKAdNetwork 4 등 광고 SDK 통합 검토)
- **인풋**: `{ diff, violation_table (validate 결과), refactoring_plan (refactor 결과), test_evidence }`
- **산출**: P1/P2/P3 라벨 리뷰 + 표준 인용 ([SOLID](principles/solid.md) / [GRASP](principles/grasp.md) / [Code Smells](principles/code-smells.md) / [Professional Ethics](principles/professional-ethics.md)) + 머지 가/부
- **후속**: `verifier` 회귀 확인

### `security-reviewer` — 보안 통제 검증
- **트리거**: `security-audit` 5단계 결과가 DREAD ≥ 8 위협 식별 / 컴플라이언스 carve-out 필요 / threat model 신규 등재 / [data-quality-governance](patterns/data-quality-governance.md) (DQ 검증 → 데이터 무결성·리니지 영향) / [security/index.md OWASP Top 10 매핑](security/index.md) (Web/API/Mobile/LLM 매핑표 신규 위협 → 통제 보강) / [standards-mapping](principles/standards-mapping.md) (OWASP·NIST 800·ISO 27001 적합성 검증) 영향
- **인풋**: `{ stride_table, dread_scores, compliance_mapping, attack_surface_changes }`
- **산출**: threat model 확정 / 통제 변경 권고 / 컴플라이언스 증거 체크리스트 ([표준 매트릭스](security/index.md))
- **후속**: `verifier` + `code-reviewer`

### `verifier` — 회귀 확인
- **트리거**: `refactor` / `maintain` / `security-audit` 변경 적용 후 / autopilot 종료 직전 / [web-performance](patterns/web-performance.md) (Core Web Vitals / Lighthouse 회귀 측정 — 변경 전후 LCP/INP/CLS 회귀 ≤ 임계치 확인) / [formal-methods#model-checking](principles/formal-methods.md#model-checking) (분산 합의·동시성·안전 critical 시스템에서 Model Checking 후속 검증 — Spin/NuSMV/TLC 반례 회귀 확인)
- **인풋**: `{ changed_files, expected_behavior, regression_test_command }`
- **산출**: 테스트 통과/실패 + 행위적 동등성 검증 + 회귀 위험 평가
- **후속**: 실패 시 `refactor` 재실행, 통과 시 hand-off 종료

### `designer` — UI/UX 설계
- **트리거**: [hci-methodology](principles/hci-methodology.md) 카테고리 영향 (Persona / Journey Map / Card Sort / Think-Aloud / Heuristic Eval / Cognitive Walkthrough — UX 연구·평가 절차) / [professional-ethics](principles/professional-ethics.md) (Dark Pattern 분류 / Inclusive Design / WCAG 윤리 검토) 영향 / UI 컴포넌트 영향 ≥ 3 화면 / [ui-ux](patterns/ui-ux.md) 카테고리 변경
- **인풋**: `{ ui_components, user_flows, design_tokens, accessibility_requirements }`
- **산출**: 컴포넌트 트리 + 인터랙션 다이어그램 (Mermaid) + WCAG 2.2 평가 + 디자인 토큰 정의
- **후속**: `executor` 구현 또는 `verifier` 시각 회귀

### `planner` — 로드맵·추정
- **트리거**: [sdlc-models](principles/sdlc-models.md) / [scaled-agile](principles/scaled-agile.md) 카테고리 영향 / 다단계 추정·로드맵 필요 / [configuration-management](principles/configuration-management.md) (Baseline 3종 계획·릴리스 게이트·SCMP IEEE 828 작성) 필요
- **인풋**: `{ goals, scope, timeline, team_topology, methodology_constraints }`
- **산출**: 로드맵 + 마일스톤 + 리스크 매트릭스 + 추정 (PMBOK / PRINCE2 기반)
- **후속**: `architect` 설계 또는 `executor` 분할 task

### `$ai-slop-cleaner` — 코드 스멜 deslop 후속 스킬
- **트리거**: `maintain` 5단계 결과 / [Dispensables 그룹](principles/code-smells.md) (Comments / Duplicate Code / Lazy Class / Dead Code) 비중 ≥ 40%
- **인풋**: `{ smell_table (maintain 결과), affected_paths, smell_groups_distribution }`
- **산출**: 스멜 제거 diff + 회귀 안전성 보고
- **후속**: `code-reviewer` PR 리뷰

### hand-off 호출 형식

아래 형식은 Codex 서브에이전트 역할(`architect`, `code-reviewer`, `security-reviewer`, `verifier`, `designer`, `planner`)에만 적용한다. `$ai-slop-cleaner` 는 스킬 호출로 실행한다.

```text
spawn_agent(
  agent_type="<agent>",
  message="<역할 + 인풋 JSON + 산출 형식 명시>"
)
```

Codex 역할 에이전트의 고정 모델 정책을 우선한다. 별도 `model` 파라미터는 사용자가 명시적으로 요구하거나 작업상 필요성이 분명한 경우에만 지정한다.
