# OMX 에이전트 hand-off 상세

dev-advisor advisor 7 모드 → 트리거 조건 도달 → Codex 전문 서브에이전트 또는 후속 OMX 스킬 hand-off. 각 대상의 정식 입출력 계약. SKILL.md `## OMX hand-off` 요약 표에서 참조.

---

## OMX hand-off

advisor 7 모드는 다음 트리거 조건 도달 시 Codex 전문 서브에이전트 또는 후속 OMX 스킬로 hand-off 한다. `architect` / `code-reviewer` / `security-reviewer` / `verifier` 는 `spawn_agent` 대상이고, `$ai-slop-cleaner` 는 별도 스킬 호출 대상이다.

### `architect` — 아키텍처 설계
- **트리거**: `recommend` 5단계 결과가 아키텍처 영향 ≥ 3 파일 / 계층 재설계 / 도메인 분해
- **인풋**: `{ context, candidates_matrix (3~5행), rationale_6fields, project_signals: { language, scale, stack } }`
- **산출**: ADR (Architecture Decision Record) + 컴포넌트 다이어그램 (Mermaid) + 계층 경계 + 인터페이스 계약
- **후속**: `executor` 또는 로컬 구현. 모델 파라미터는 Codex 역할 에이전트의 기본 정책을 우선한다.

### `code-reviewer` — 변경 검토
- **트리거**: `refactor` 6단계 후 PR / `validate` 식별 P1 위반 수정 후 PR
- **인풋**: `{ diff, violation_table (validate 결과), refactoring_plan (refactor 결과), test_evidence }`
- **산출**: P1/P2/P3 라벨 리뷰 + 표준 인용 ([SOLID](principles/solid.md) / [GRASP](principles/grasp.md) / [Code Smells](principles/code-smells.md)) + 머지 가/부
- **후속**: `verifier` 회귀 확인

### `security-reviewer` — 보안 통제 검증
- **트리거**: `security-audit` 5단계 결과가 DREAD ≥ 8 위협 식별 / 컴플라이언스 carve-out 필요 / threat model 신규 등재
- **인풋**: `{ stride_table, dread_scores, compliance_mapping, attack_surface_changes }`
- **산출**: threat model 확정 / 통제 변경 권고 / 컴플라이언스 증거 체크리스트 ([표준 매트릭스](security/index.md))
- **후속**: `verifier` + `code-reviewer`

### `verifier` — 회귀 확인
- **트리거**: `refactor` / `maintain` / `security-audit` 변경 적용 후 / autopilot 종료 직전
- **인풋**: `{ changed_files, expected_behavior, regression_test_command }`
- **산출**: 테스트 통과/실패 + 행위적 동등성 검증 + 회귀 위험 평가
- **후속**: 실패 시 `refactor` 재실행, 통과 시 hand-off 종료

### `$ai-slop-cleaner` — 코드 스멜 deslop 후속 스킬
- **트리거**: `maintain` 5단계 결과 / [Dispensables 그룹](principles/code-smells.md) (Comments / Duplicate Code / Lazy Class / Dead Code) 비중 ≥ 40%
- **인풋**: `{ smell_table (maintain 결과), affected_paths, smell_groups_distribution }`
- **산출**: 스멜 제거 diff + 회귀 안전성 보고
- **후속**: `code-reviewer` PR 리뷰

### hand-off 호출 형식

아래 형식은 Codex 서브에이전트 역할(`architect`, `code-reviewer`, `security-reviewer`, `verifier`)에만 적용한다. `$ai-slop-cleaner` 는 스킬 호출로 실행한다.

```
spawn_agent(
  agent_type="<agent>",
  message="<역할 + 인풋 JSON + 산출 형식 명시>"
)
```

Codex 역할 에이전트의 고정 모델 정책을 우선한다. 별도 `model` 파라미터는 사용자가 명시적으로 요구하거나 작업상 필요성이 분명한 경우에만 지정한다.
