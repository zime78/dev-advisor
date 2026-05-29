# advisor 모드 산출물 템플릿

dev-advisor 9 모드의 표준 마크다운 출력 스켈레톤. SKILL.md `## 워크플로우` 5단계 "근거 산출" 6 필드는 모든 모드에 공통 포함된다. 본 파일의 표·코드 블록·필드 alias 를 그대로 복사해 채우면 advisor 응답이 완성된다.

> **공통 규칙**
> - 4단계 산출 → 5단계 "왜" 6 필드 → 6단계 검증/후속 순으로 배치한다.
> - 표 행 수가 부족하면 빈 행을 두지 말고 행을 줄인다. 산출 행 수가 0 이면 모드 적용 불가로 간주하고 사유를 명시.
> - "표준 인용" 필드는 다음 anchor 만 사용한다: [`SOLID`](principles/solid.md) · [`GRASP`](principles/grasp.md) · [`ISO 25010`](principles/iso25010.md) · [`12-Factor`](principles/12-factor.md) · [`Code Smells`](principles/code-smells.md) · [`DDD Tactical`](patterns/ddd-tactical.md) · [`Clean Architecture`](patterns/architectural.md) · [`OWASP/NIST/STRIDE`](security/index.md) · 외부 RFC 는 풀 URL.

---

## 1. recommend — 추천 산출물 템플릿

**목적**: 도메인 + 제약 조건을 받아 529 패턴 / 250 알고리즘 / 75 언어 / 106 보안 / 206 원칙 / 20 품질 + 18 부록 카탈로그에서 후보 3~5 개를 추출하고, 정량 score 와 trade-off 로 1 위 후보를 권장한다. score 는 1~5 정수.

### 후보 매트릭스

| # | ID | 적합 컨텍스트 | trade-off | score (1~5) |
|---|----|--------------|-----------|-------------|
| 1 | `<catalog-id>` | <적합 시나리오 1~2줄> | <장점 / 단점 1~2줄> | <1~5> |
| 2 | `<catalog-id>` | ... | ... | ... |
| 3 | `<catalog-id>` | ... | ... | ... |
| 4 | `<catalog-id>` | ... | ... | ... |
| 5 | `<catalog-id>` | ... | ... | ... |

> score 가중치 예시: 적합도 × 0.4 + 구현 비용(역수) × 0.3 + 운영 부담(역수) × 0.2 + 팀 친숙도 × 0.1.

### 5단계 "왜" 산출

- **선택/판정**: 1 위 후보 `<id>` 권장. 핵심 결정 근거 1~2줄.
- **근거 (Why)**: 정량 신호(score 분포, 벤치마크 / 부하 추정 / 메모리 footprint) + 정성 신호(팀 컨텍스트, 도메인 복잡도).
- **대안 비교**: `A vs B vs C` — 각 trade-off 1~2줄. 왜 1 위가 2/3 위를 이기는지 비교 우위 명시.
- **표준 인용**: 적용 표준 anchor 직접 link. 예 — [`ISO 25010 / Performance Efficiency`](principles/iso25010.md), [`GRASP / Information Expert`](principles/grasp.md).
- **적용 조건**: 권장이 유효한 컨텍스트 (스택, 트래픽 규모, 팀 크기, SLA).
- **비추천 조건**: 이 후보를 **쓰면 안 되는** 컨텍스트 (anti-context). 예 — 동시성 1k 미만, 트랜잭션 강한 일관성 필수.

### 6단계 검증/후속

- **회귀 테스트**: 도입 시 검증 시나리오 (단위 / 통합 / 부하).
- **재검증 명령**: 예 — `go test ./internal/<pkg>/... -run <Pattern>`, `make test`, `k6 run scripts/load.js`.
- **OMX hand-off 후보**:
  - 신규 모듈 ≥ 3 파일 → `architect`
  - 구현 후 PR 리뷰 → `code-reviewer`
  - 보안 통제 신설 → `security-reviewer`
  - 도입 후 실제 동작 확인 → `verifier`

### 인용 references

- [`patterns/index.md`](patterns/index.md)
- [`algorithms/index.md`](algorithms/index.md)
- [`languages/index.md`](languages/index.md)
- [`principles/iso25010.md`](principles/iso25010.md) — 품질 특성 기준
- [`principles/grasp.md`](principles/grasp.md) — 책임 할당

---

## 2. validate — 검증 산출물 템플릿

**목적**: 기존 코드/모듈을 SOLID / GRASP / DDD / Clean Architecture / ISO 25010 / 12-Factor / OWASP / NIST 기준으로 감사. 위반 항목을 심각도(P1=차단 / P2=경고 / P3=관찰) 와 영향 범위로 표기.

### 위반 항목 표

| # | 위치 (`file:line`) | 위반 표준 | 심각도 | 영향 | 조치 |
|---|-------------------|----------|--------|------|------|
| 1 | `internal/x/y.go:42` | SRP / 12-Factor III | P1 | <영향 범위 1줄> | <리팩토링/롤백/예외 처리 1줄> |
| 2 | ... | ... | P2 | ... | ... |
| 3 | ... | ... | P3 | ... | ... |

> 심각도 기준
> - **P1**: 보안 / 데이터 손실 / 차단 — 즉시 수정
> - **P2**: 유지보수 비용 증가 / SLA 위협 — 다음 스프린트
> - **P3**: 스타일 / 일관성 — 백로그

### 5단계 "왜" 산출

- **판정**: 전체 검증 결론 (PASS / CONDITIONAL / FAIL) + P1 건수 / P2 건수 / P3 건수.
- **근거 (Why)**: 표 행별 비중 큰 위반 2~3개의 인과 설명.
- **대안 비교**: 위반 해소 방법 A vs B vs C — 예: `Extract Class` vs `Move Method` vs `현 상태 + 면제 처리`. 각 trade-off 1~2줄.
- **표준 인용**: 위반된 anchor 직접 link. 예 — [`SOLID / SRP`](principles/solid.md), [`Clean Architecture / Dependency Rule`](patterns/architectural.md).
- **적용 조건**: 본 검증 기준 적용 범위 (모듈 단위, 패키지 단위, 전 코드베이스).
- **예외·면제 조건**: 표준 carve-out 또는 compliance exception — 예: legacy compat shim, 외부 SDK 강제 인터페이스, regulatory waiver.

### 6단계 검증/후속

- **회귀 테스트**: P1/P2 수정 시 영향 모듈 회귀 — 단위 + 통합.
- **재검증 명령**: `make vet`, `make lint`, `make test`, `lsp_diagnostics_directory <pkg>`.
- **OMX hand-off 후보**:
  - P1 ≥ 3 또는 계층 위반 → `architect`
  - 수정 PR 리뷰 → `code-reviewer`
  - 보안 위반 P1 → `security-reviewer`
  - 수정 후 동작 검증 → `verifier`

### 인용 references

- [`patterns/architectural.md`](patterns/architectural.md)
- [`patterns/ddd-tactical.md`](patterns/ddd-tactical.md)
- [`patterns/index.md`](patterns/index.md)
- [`security/index.md`](security/index.md)
- [`principles/solid.md`](principles/solid.md)
- [`principles/grasp.md`](principles/grasp.md)
- [`principles/iso25010.md`](principles/iso25010.md)
- [`principles/12-factor.md`](principles/12-factor.md)

---

## 3. refactor — 리팩토링 산출물 템플릿

**목적**: 단일 코드/함수를 받아 단계별 리팩토링 플랜(Before → After) 을 생성. 각 단계는 회귀 위험 등급(LOW/MED/HIGH) 과 롤백 포인트를 포함한다.

### 단계 표

| # | 단계 | 변경 내용 | 회귀 위험 | 롤백 포인트 |
|---|------|----------|----------|------------|
| 1 | Extract Method | `<func>` 의 검증 블록을 `validate<X>()` 로 분리 | LOW | step-1 commit |
| 2 | Move Method | 도메인 로직을 `<Entity>` 로 이동 | MED | step-2 commit |
| 3 | Introduce Parameter Object | 파라미터 5+ → `<RequestDTO>` | LOW | step-3 commit |
| 4 | Replace Conditional with Polymorphism | switch 제거 → 전략 패턴 | HIGH | step-4 branch |
| 5 | ... | ... | ... | ... |

### Before

```<lang>
// 리팩토링 전 코드 (대표 블록 30~60 줄 이내)
// 코드 스멜 위치는 // ⚠ 주석으로 표시
```

### After

```<lang>
// 리팩토링 후 코드 (동일 동작 보장)
// 변경 의도는 // ✅ 주석으로 표시
```

### 5단계 "왜" 산출

- **판정**: 단계 N 개 리팩토링 권장. 누적 회귀 위험 합산 등급 (LOW/MED/HIGH).
- **근거 (Why)**: 제거되는 코드 스멜 ID + ISO 25010 유지보수성 향상 신호 (cyclomatic / fan-out / 중복률).
- **대안 비교**: `점진적 단계 분할 vs 빅뱅 재작성 vs 현 상태 유지` — 각 trade-off 1~2줄.
- **표준 인용**: [`Code Smells`](principles/code-smells.md), [`SOLID / OCP·DIP`](principles/solid.md), [`DDD Tactical`](patterns/ddd-tactical.md).
- **적용 조건**: 단위 테스트 커버리지 ≥ X%, 영향 모듈 격리 가능, 롤백 가능한 release 윈도우.
- **비추천 조건**: 회귀 테스트 부재, 동결 코드(legacy freeze), EOL 임박 모듈, 외부 계약 변경 동반.

### 6단계 검증/후속

- **회귀 테스트**: 단계별 commit 후 `make test` + 영향 통합 테스트. 가능하면 mutation testing.
- **재검증 명령**: `go test -race ./...`, `make lint`, `lsp_diagnostics <file>` 각 단계 직후.
- **OMX hand-off 후보**:
  - HIGH 위험 단계 또는 ≥ 3 파일 → `architect` 사전 검토
  - PR 리뷰 → `code-reviewer`
  - 보안 영향 동반 → `security-reviewer`
  - 단계별 동작 검증 → `verifier`
  - 잔여 dead code / 주석 잔재 정리 → `$ai-slop-cleaner`

### 인용 references

- [`references/code_templates.md`](code_templates.md)
- [`patterns/architectural.md`](patterns/architectural.md)
- [`patterns/ddd-tactical.md`](patterns/ddd-tactical.md)
- [`principles/code-smells.md`](principles/code-smells.md) — 스멜 → 리팩토링 매핑
- [`principles/solid.md`](principles/solid.md)

---

## 4. maintain — 유지보수 산출물 템플릿

**목적**: 모듈/프로젝트의 기술 부채 7~10 항목을 코드 스멜 5 그룹(Bloaters / OO Abusers / Change Preventers / Dispensables / Couplers) 으로 분류하고, **영향 × 발생빈도** 우선순위 매트릭스로 정렬한다.

### 부채 표

| # | 스멜 | 위치 (`file:line` or 모듈) | 그룹 | 우선순위 (영향 × 빈도) | 권장 리팩토링 |
|---|------|---------------------------|------|----------------------|--------------|
| 1 | Long Method | `internal/x/y.go:Foo` | Bloaters | 4 × 5 = 20 (P1) | Extract Method |
| 2 | Shotgun Surgery | feature `<name>` 전반 | Change Preventers | 5 × 3 = 15 (P1) | Move Method / Inline Class |
| 3 | Duplicate Code | `pkg/a` ↔ `pkg/b` | Dispensables | 3 × 4 = 12 (P2) | Extract Superclass / Pull Up |
| 4 | Feature Envy | `<file>` | Couplers | 3 × 3 = 9 (P2) | Move Method |
| 5 | Primitive Obsession | API param `<x>` | Bloaters | 2 × 4 = 8 (P2) | Introduce Value Object |
| 6 | Switch Statement | `<file>` | OO Abusers | 3 × 2 = 6 (P3) | Replace with Polymorphism |
| 7 | Dead Code | `<dir>` | Dispensables | 1 × 5 = 5 (P3) | Remove |
| 8 | ... | ... | ... | ... | ... |

> 우선순위 = 영향(1~5) × 발생빈도(1~5). P1 ≥ 15, P2 = 8~14, P3 ≤ 7.

### 코드 스멜 5 그룹 매핑

| 그룹 | 본 분석에서 식별된 스멜 | 행 # |
|------|----------------------|------|
| **Bloaters** | Long Method, Primitive Obsession | 1, 5 |
| **OO Abusers** | Switch Statement | 6 |
| **Change Preventers** | Shotgun Surgery | 2 |
| **Dispensables** | Duplicate Code, Dead Code | 3, 7 |
| **Couplers** | Feature Envy | 4 |

### 5단계 "왜" 산출

- **판정**: 부채 N 건 식별 (P1 a / P2 b / P3 c). 다음 스프린트 처리 권장 항목 행 #.
- **근거 (Why)**: 영향 × 빈도 점수 산출 근거 — 변경 빈도 git log 통계, 영향 범위(import 역참조 수), 결함 밀도.
- **대안 비교**: `즉시 리팩토링 vs 점진 상환 vs 부채 수용` — 각 ROI / 리스크 1~2줄.
- **표준 인용**: [`Code Smells`](principles/code-smells.md), [`ISO 25010 / Maintainability`](principles/iso25010.md), [`12-Factor`](principles/12-factor.md), [`patterns/index.md`](patterns/index.md) (역방향 적합도).
- **적용 조건**: 모듈이 활발히 변경 중, 회귀 테스트 존재, 다음 마이너 릴리스 윈도우 보유.
- **수용 가능 조건**: 해당 부채를 그냥 두는 것이 합리적인 컨텍스트 — EOL 모듈, 외부 SDK 강제, 변경 빈도 ≤ 1 회/년, 제거 비용 > 잔여 가치.

### 6단계 검증/후속

- **회귀 테스트**: P1 항목 수정 시 영향 모듈 통합 테스트 + 변경 빈도 높은 경로 우선.
- **재검증 명령**: `make vet`, `make lint`, `make test`, 변경 빈도 측정 `git log --since=...` 재실행.
- **OMX hand-off 후보**:
  - 그룹 단위 일괄 정리 → `$ai-slop-cleaner`
  - 계층 재설계 동반 → `architect`
  - 정리 PR 리뷰 → `code-reviewer`
  - 정리 후 회귀 → `verifier`

### 인용 references

- [`principles/code-smells.md`](principles/code-smells.md) — 22 스멜 5 그룹
- [`principles/iso25010.md`](principles/iso25010.md) — 유지보수성
- [`principles/12-factor.md`](principles/12-factor.md) — 운영 부채
- [`patterns/index.md`](patterns/index.md) — 역방향 적합도

---

## 5. security-audit — 보안 점검 산출물 템플릿

**목적**: 모듈/API 를 STRIDE 6 위협 유형(Spoofing / Tampering / Repudiation / Information Disclosure / Denial of Service / Elevation of Privilege) 으로 분석하고 DREAD 점수(Damage / Reproducibility / Exploitability / Affected Users / Discoverability — 각 1~10, 합계 5~50), CVSS v4, EPSS, CISA KEV, OWASP Risk Rating, 데이터 민감도, blast radius, exploitability, risk acceptance 가능 여부를 함께 매핑. 컴플라이언스(OWASP ASVS / NIST SP 800-53 / ISO 27001 / GDPR / PCI-DSS / RFC 9110·8725) 적합 여부 별도 표.

### STRIDE 위협 표

| # | 컴포넌트 | 위협 유형 | 시나리오 | DREAD (D/R/E/A/Dc = 합계) | 대응책 |
|---|---------|----------|---------|--------------------------|--------|
| 1 | `<api/path>` | Spoofing | <공격 시나리오 1~2줄> | 8/7/6/9/5 = 35 | <통제 1~2줄> |
| 2 | `<service>` | Tampering | ... | 7/5/6/7/4 = 29 | ... |
| 3 | `<log>` | Repudiation | ... | 4/3/5/3/4 = 19 | ... |
| 4 | `<db>` | Information Disclosure | ... | 9/8/7/9/6 = 39 | ... |
| 5 | `<gateway>` | Denial of Service | ... | 6/8/7/8/7 = 36 | ... |
| 6 | `<auth>` | Elevation of Privilege | ... | 10/6/5/9/4 = 34 | ... |

> DREAD 등급: ≥ 40 Critical / 30~39 High / 20~29 Medium / < 20 Low.

### 컴플라이언스 매핑

| # | 요구사항 | 표준 조항 | 적합 여부 | 증거 (`file:line` or 정책 ID) |
|---|---------|----------|----------|-------------------------------|
| 1 | 인증·세션 | OWASP ASVS V2, RFC 8725 | PASS / GAP / N/A | `internal/auth/x.go:42` |
| 2 | 접근 제어 | OWASP ASVS V4, NIST AC-3 | ... | ... |
| 3 | 암호화 | OWASP ASVS V6, NIST SC-13 | ... | ... |
| 4 | 로깅·감사 | OWASP ASVS V7, NIST AU-2 | ... | ... |
| 5 | 입력 검증 | OWASP ASVS V5 | ... | ... |
| 6 | 데이터 보호 | GDPR Art.32, PCI-DSS 3.x | ... | ... |
| 7 | 공급망 | NIST SP 800-218 (SSDF) | ... | ... |

### 보안 릴리즈 게이트

| Gate | 필수 증거 | 실패 시 판정 |
|---|---|---|
| Threat model 승인 | 최신 DFD, trust boundary, STRIDE 결과, 소유자 승인 | P1 release blocker |
| SAST / DAST / SCA / secrets scan | CI run, SARIF/HTML report, high 이상 0건 또는 승인된 waiver | P1/P2 |
| SBOM / provenance | CycloneDX 또는 SPDX, SLSA/in-toto provenance, artifact signature | P1 |
| Privacy evidence | DPIA, retention, DSAR, data minimization, purpose binding 증거 | P1/P2 |
| Risk acceptance | 소유자, 만료일, 대체 통제, 재검토 조건 | 미충족 시 waiver 불가 |

### 5단계 "왜" 산출

- **판정**: 위협 N 건 (Critical a / High b / Medium c / Low d), 컴플라이언스 GAP m 건. 즉시 조치 위협 행 #.
- **근거 (Why)**: DREAD/CVSS/EPSS/KEV/OWASP Risk Rating 산정 근거 + 위협 모델링 가정(공격자 capability, 자산 가치, 데이터 민감도, blast radius, 노출 경로).
- **대안 비교**: 대응책 옵션 `Defense in depth vs Single Control vs Risk Accept` — 비용 / 가용성 / 잔여 위험 1~2줄.
- **표준 인용**: [`STRIDE / DREAD`](security/security-sdlc.md), [`OWASP / NIST`](security/index.md), [`12-Factor / Config`](principles/12-factor.md), 외부 RFC URL.
- **적용 조건**: 위협 모델 scope (asset, trust boundary, attacker profile) 와 환경(prod / staging) 명시.
- **비추천 조건**: 본 대응책을 **쓰면 안 되는** 컨텍스트 — 내부 격리망에서 외부 IAM 강제 도입, 저트래픽에서 과도한 rate limit, 저자산 가치 vs 대응 비용 역전.

### 6단계 검증/후속

- **회귀 테스트**: 보안 통제 도입 후 인증/인가 회귀 + 부하/장애 시 fail-safe 검증. SAST/DAST.
- **재검증 명령**: `make test`, SAST(`gosec ./...` 등), DAST(`zap-cli quick-scan ...`), 의존성 스캔(`govulncheck ./...`, `npm audit`).
- **OMX hand-off 후보**:
  - 위협 모델 확정 / 통제 변경 → `security-reviewer`
  - 계층 변경 동반 → `architect`
  - 통제 PR 리뷰 → `code-reviewer`
  - 통제 도입 후 동작 검증 → `verifier`

### 인용 references

- [`security/security-sdlc.md`](security/security-sdlc.md) — STRIDE / DREAD / CVSS / EPSS / KEV
- [`security/index.md`](security/index.md) — 표준 매트릭스
- [`security/security-authn.md`](security/security-authn.md)
- [`security/security-authz.md`](security/security-authz.md)
- [`security/security-crypto-ops.md`](security/security-crypto-ops.md)
- [`security/security-data-protection.md`](security/security-data-protection.md)
- [`security/security-api-web.md`](security/security-api-web.md)
- [`security/security-supply-chain.md`](security/security-supply-chain.md)
- [`security/security-platform.md`](security/security-platform.md)
- [`security/security-sdlc.md`](security/security-sdlc.md)
- [`security/security-detect-respond.md`](security/security-detect-respond.md)
- [`security/security-mobile.md`](security/security-mobile.md)
- [`security/security-ai-model.md`](security/security-ai-model.md)
- [`security/privacy-engineering.md`](security/privacy-engineering.md)
- [`security/compliance.md`](security/compliance.md)
- [`principles/12-factor.md`](principles/12-factor.md) — 운영 보안

---

## 부록 — 6 필드 공통 템플릿 (alias 표)

모든 모드의 5단계 "왜" 산출은 다음 6 필드를 채운다. 6 번째 필드 alias 만 모드별로 다르다.

| 필드 | 공통 의미 | recommend / refactor / security-audit | validate | maintain | qa | qc |
|------|----------|--------------------------------------|----------|----------|----|----|
| 1 선택/판정 | 4단계 산출의 핵심 결론 1~2줄 | 동일 | 동일 | 동일 | 동일 | 동일 |
| 2 근거 (Why) | 정량/정성 신호 | 동일 | 동일 | 동일 | 동일 | 동일 |
| 3 대안 비교 | A vs B vs C + trade-off | 동일 | 동일 | 동일 | 동일 | 동일 |
| 4 표준 인용 | anchor 직접 link | 동일 | 동일 | 동일 | 동일 | 동일 |
| 5 적용 조건 | 결정 유효 컨텍스트 | 동일 | 동일 | 동일 | 동일 | 동일 |
| 6 (alias) | — | **비추천 조건** | **예외·면제 조건** | **수용 가능 조건** | **승인·면제 조건** | **차단·재검증 조건** |

## 부록 — 6단계 hand-off 후보 매트릭스 (공통)

| 트리거 | 에이전트 |
|--------|---------|
| 아키텍처 영향 ≥ 3 파일 / 계층 재설계 | `architect` |
| 리팩토링 / 정리 PR 검토 | `code-reviewer` |
| 보안 통제 변경 / threat model 확정 | `security-reviewer` |
| 변경 후 회귀 확인 | `verifier` |
| 코드 스멜 deslop 정리 (`maintain` 후속) | `$ai-slop-cleaner` |

---

## 6. qa — 품질 보증 산출물 템플릿

**목적**: 요구사항, 테스트 전략, 추적성, 릴리즈 승인 등 프로세스 중심 품질을 점검한다. 실행 결과 자체가 아니라 실행 전 기준과 승인 경로가 충분한지 판단한다.

### QA 점검 표

| # | QA 항목 | 현재 증거 | 판정 | 보완 조치 |
|---|---------|----------|------|----------|
| 1 | [requirements-traceability](quality/qa.md#qa-requirements-traceability) | <요구사항-테스트 매핑> | PASS / GAP / N/A | <누락 요구사항 연결> |
| 2 | [test-strategy](quality/qa.md#qa-test-strategy) | <테스트 레벨 전략> | PASS / GAP / N/A | <전략 보강> |
| 3 | [release-readiness](quality/qa.md#qa-release-readiness) | <go/no-go 기록> | PASS / GAP / N/A | <승인 조건> |

### 5단계 "왜" 산출

- **판정**: QA 프로세스 PASS / CONDITIONAL / FAIL. release blocker 또는 승인 예외 건수 명시.
- **근거 (Why)**: 요구사항 추적성, 테스트 전략, regression scope, evidence plan의 누락 정도.
- **대안 비교**: `릴리즈 보류 vs 조건부 승인 vs 범위 축소` — 일정/품질/운영 위험 trade-off.
- **표준 인용**: [`Quality QA`](quality/qa.md), [`SDLC Models`](principles/sdlc-models.md), [`Standards Mapping`](principles/standards-mapping.md), [`ISO 25010`](principles/iso25010.md).
- **적용 조건**: 릴리즈 전 품질 승인, 규제/감사 요구, 핵심 도메인 변경.
- **승인·면제 조건**: known issue 승인, 테스트 제외 근거, 릴리즈 조건부 승인 범위.

### 6단계 검증/후속

- **회귀 테스트**: high risk 요구사항과 critical user journey 우선 검증.
- **릴리즈 게이트**: threat model 승인, SAST/DAST/SCA/secrets scan, SBOM/provenance, DPIA/retention/DSAR 증거가 없으면 조건부 승인 또는 release hold로 분기.
- **재검증 명령**: `make test`, `make e2e`, QA checklist 재실행, traceability matrix 갱신.
- **OMX hand-off 후보**:
  - 릴리즈 승인 충돌 → `planner`
  - 테스트 전략 재설계 → `test-engineer`
  - 규제/보안 증거 gap → `security-reviewer`

---

## 7. qc — 품질 관리 산출물 템플릿

**목적**: 빌드, 테스트 실행, 결함 재현, 품질 게이트, post-release smoke 등 실제 산출물 검증 증거를 확인한다. 증거가 없으면 미실행으로 판정한다.

### 품질 게이트 계층

| Gate | 위치 | 필수 조건 | waiver |
|---|---|---|---|
| Merge gate | PR / main 병합 전 | build, lint, unit, SAST/secrets 기본 통과 | 팀 리드 승인 + follow-up 이슈 |
| Release gate | 배포 후보 승인 전 | E2E/회귀, SCA/DAST, SBOM/provenance, rollback plan | release owner + 보안/품질 owner 승인 |
| Production gate | 실제 배포 중/직후 | smoke, metrics, alert silence, data integrity | P1 증상 없음 + rollback 가능 |
| Waiver policy | 예외 승인 | 소유자, 만료일, 대체 통제, 재검토 조건 | 만료 없는 waiver 금지 |

### QC 증거 표

| # | QC 항목 | 증거 링크/ID | 판정 | 차단 여부 |
|---|---------|-------------|------|----------|
| 1 | [build-verification](quality/qc.md#qc-build-verification) | <CI run / artifact ID> | PASS / FAIL | BLOCK / WARN |
| 2 | [test-execution-evidence](quality/qc.md#qc-test-execution-evidence) | <test report> | PASS / FAIL | BLOCK / WARN |
| 3 | [quality-gate](quality/qc.md#qc-quality-gate) | <gate dashboard> | PASS / FAIL | BLOCK / WARN |

### 5단계 "왜" 산출

- **판정**: QC PASS / CONDITIONAL / FAIL. blocker, failed gate, 재실행 필요 건수 명시.
- **근거 (Why)**: 빌드 산출물, 테스트 리포트, 회귀 결과, 결함 재현, 데이터 무결성 증거.
- **대안 비교**: `재실행 vs 결함 차단 vs 예외 승인` — 신뢰도/시간/잔여 위험 trade-off.
- **표준 인용**: [`Quality QC`](quality/qc.md), [`Testing`](patterns/testing.md), [`Testing Strategies`](patterns/testing-strategies.md), [`Process Metrics`](principles/process-metrics.md).
- **적용 조건**: merge/release gate, 배포 후보 artifact, hotfix 검증, post-release smoke.
- **차단·재검증 조건**: failed gate, 증거 누락, critical path 실패, 데이터 mismatch, blocker 결함.

### 6단계 검증/후속

- **회귀 테스트**: 실패 suite 재실행 + critical path smoke + post-release check.
- **재검증 명령**: `make test`, `make smoke`, `make verify-release`, CI rerun.
- **OMX hand-off 후보**:
  - flaky/failing test 원인 분석 → `debugger`
  - release gate 자동화 → `test-engineer`
  - 배포 후 회귀 확인 → `verifier`

---

## 8. full — 종합 분석 산출물 템플릿

**목적**: 7 기본 모드(recommend / validate / security-audit / qa / qc / maintain / refactor) 를 단일 sequential 흐름으로 묶어 한 모듈/경로에 대한 종합 보고서를 생성. 각 도메인 결과를 통합 우선순위 Top 10 으로 정렬하고 6 필드를 합산.

```markdown
# /dev-advisor full — 종합 분석 보고서

**대상**: <module/path>
**언어**: <auto-detected language>
**분석 시각**: <timestamp>
**총 위반/이슈**: P1×N / P2×N / P3×N

---

## 1. RECOMMEND — 권장 아키텍처

| 후보 | 적합 컨텍스트 | Trade-off | Score |
|------|-------------|-----------|-------|
| ... |

**선택**: <패턴 1>
**근거**: ...

---

## 2. VALIDATE — 표준 위반

| 위치 | 표준 | 심각도 | 영향 | 조치 |
|------|------|--------|------|------|
| <file:line> | [SRP](principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) | P1 | ... | ... |
| ... |

---

## 3. SECURITY-AUDIT — STRIDE 6 + DREAD

| Threat | 위치 | DREAD 점수 | 대응책 |
|--------|------|------|---------|
| Spoofing | ... | 8/10 | ... |
| Tampering | ... | 6/10 | ... |
| ... |

**컴플라이언스 매핑**: GDPR Art 32 위반 1건, PCI-DSS 8.2 위반 2건

---

## 4. QA — 품질 보증 프로세스

| QA 항목 | 판정 | 보완 조치 |
|---------|------|----------|
| requirements-traceability | GAP | 테스트 케이스 연결 |
| release-readiness | CONDITIONAL | 조건부 승인 기록 |

---

## 5. QC — 품질 관리 증거

| QC 항목 | 판정 | 차단 여부 |
|---------|------|----------|
| test-execution-evidence | PASS | WARN |
| quality-gate | FAIL | BLOCK |

---

## 6. MAINTAIN — Code Smells 5 그룹 분포 + 부채

```
Bloater       ████████ 8개
OO Abuser     ██ 2개
Change Pre.   ████ 4개
Dispensable   ████████████ 12개
Coupler       █████ 5개
```

| 부채 | 영향 | 빈도 | 우선순위 |
|------|------|------|---------|
| ... |

---

## 7. REFACTOR — Top 3 처방

### 7.1. <Smell> → <Technique> (Before/After)

```kotlin
// Before
...
// After
...
```

**회귀 위험**: 중간

---

## 통합 우선순위 (Top 10)

| # | Severity | Domain | 위반 | 위치 | 조치 |
|---|----------|--------|------|------|------|
| 1 | P1 | Security | PII 로깅 | order_repo:89 | Pseudonymization 적용 |
| 2 | P1 | Architecture | data → ui 의존 | clean-arch 위반 | 의존성 역전 |
| ... |

---

### 공통 severity 정규화 표

`full` / `swarm` 통합 Top 10은 각 모드의 결과를 아래 표로 정규화한 뒤 점수화한다. QA/QC 결과도 동일한 Top 10 후보에 들어간다.

| 공통 등급 | 설계/코드 | 보안 | QA | QC |
|---|---|---|---|---|
| P1 | 차단 위반, 데이터 손실, 런타임 장애, HIGH 회귀 위험 | Critical/High, CVSS ≥ 7.0, EPSS 상위권, CISA KEV, 민감 데이터 high, blast radius 큼 | release blocker, 핵심 traceability 누락, 승인 없는 scope/risk | failed required gate, critical path 실패, test evidence 누락 |
| P2 | 유지보수 비용 증가, SLA 위협, MED 회귀 위험 | Medium, OWASP Risk Rating Medium, 보완 통제 필요 | 조건부 승인, regression scope gap, known issue 승인 필요 | WARN gate, flaky 미분류, 재실행 필요 |
| P3 | 관찰/스타일/미래 부채, LOW 회귀 위험 | Low, exploitability 낮음, 승인된 risk acceptance | 문서 보강, 낮은 위험 gap | 비차단 증거 보완 |

---

## 6 필드 산출 (통합)

- **선택/판정**: ...
- **근거 (Why)**: ...
- **대안 비교**: A vs B vs C
- **표준 인용**: [SRP](principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙), [Aggregate](patterns/ddd-tactical.md#3-aggregate), [STRIDE](security/security-sdlc.md#1-threat-modeling-stride-dread-pasta)
- **적용 조건**: ...
- **비추천/예외/품질 차단 조건**: ...

---

## OMX hand-off 권장

1차: <agent-name> (가장 큰 P1 영역)
2차: <agent-name>

예) **security-reviewer** (P1 Security 최우선) → **architect** (data 계층 재설계) → **verifier** (회귀 검증)
```

---

## 9. swarm — 병렬 심층 분석 산출물 템플릿

**목적**: 7 Codex 서브에이전트 + 1 reviewer 를 ULW 로 병렬 발사해 동일 대상을 7 관점으로 동시 분석. reviewer(verifier) 가 cross-link 매트릭스 + Top 10 + 통합 6 필드를 통합 산출.

```markdown
# /dev-advisor swarm — 병렬 심층 분석 보고서

**대상**: <module/path>
**ULW 발사**: 7 Codex 서브에이전트 + 1 reviewer
**총 토큰**: ~<수치>
**소요 시간**: ~<수치>

---

## ULW 실행 매트릭스

| Agent | Mode | 결과 | 토큰 | 시간 |
|-------|------|------|------|------|
| executor-1 | recommend | 3 후보 + Trade-off | 18k | 1m40s |
| executor-2 | validate | 20 위반 | 22k | 2m10s |
| executor-3 | security-audit | STRIDE 6 + DREAD | 15k | 1m30s |
| executor-4 | qa | traceability + release readiness | 12k | 1m |
| executor-5 | qc | quality gate + evidence | 12k | 1m |
| executor-6 | maintain | 부채 9 + 5 그룹 | 14k | 1m20s |
| executor-7 | refactor | Top 5 처방 | 20k | 2m |
| verifier | 통합 | 우선순위 Top 10 + 6 필드 | 8k | 50s |

**병렬 게인**: sequential ~9m → parallel ~2m10s (4× 빠름)

---

## 서브에이전트 결과 (7 섹션)

### [Agent 1] recommend
... (각 서브에이전트 출력 인용)

### [Agent 2] validate
...

### [Agent 3] security-audit
...

### [Agent 4] qa
...

### [Agent 5] qc
...

### [Agent 6] maintain
...

### [Agent 7] refactor
...

---

## reviewer 통합 (verifier)

### 도메인 cross-link 매트릭스

```
       Sec   Arch  Refactor  Maintain
Sec    ─     ✓(2)  ✓(1)      ─
Arch   ✓(2)  ─     ✓(3)      ✓(2)
Ref    ─     ✓(3)  ─         ✓(4)
Main   ─     ✓(2)  ✓(4)      ─
```

(숫자 = cross-link 발견된 부채/이슈 개수)

### 통합 Top 10 우선순위

| # | Severity | Domain | 위반 | 위치 | 서브에이전트 | 조치 |
|---|----------|--------|------|------|-----------|------|
| 1 | P1 | Security+Arch | ... | ... | 2,3,5 | ... |

### 통합 6 필드

- **선택/판정**: ...
- **근거**: 7 agent 합의
- **대안 비교**: ...
- **표준 인용**: ...
- **적용 조건**: ...
- **비추천 조건**: ...

---

## OMX hand-off

- code-reviewer / security-reviewer / architect / verifier 자동 분기 권장
- 이미 verifier 가 1차 통합한 상태 → 사용자 결정 후 2차 hand-off
```

---

## research 모드 스켈레톤

> 외부 무료 API(arXiv + Semantic Scholar + OpenAlex)로 학술 논문 검색 + 카탈로그 cross-ref + 6 필드 산출.
> 상세 포맷: [research/output-format.md](research/output-format.md)

### 정상 케이스 (3-of-3 응답)

```markdown
## Research — <topic|catalog-id|query>

### 1. 검색 쿼리
- arXiv: `<쿼리>` (카테고리: `cs.SE`, 연도: 2020-2026)
- Semantic Scholar: `<쿼리>` (field: "Software Engineering")
- OpenAlex: `<쿼리>` (topic: T12490 ✓verified)

### 2. 논문 매트릭스 (Primary, Top N)
| # | 제목 | 저자 (1st+) | 연도 | 발표처 | 인용수 | 무료PDF | 카탈로그 매핑 | 신뢰도 | 3-source | 관련성 |

### 3. Weak Evidence (최대 2개)
DOI/arXiv 없지만 S2/OA ID 있는 항목

### 4. 카탈로그 Cross-Reference
| 매핑된 카탈로그 항목 | 매핑 논문 # | 매핑 신뢰도 |

### 5. 6 필드 산출
**선택/판정**: ...
**근거 (Why)**: ...
**대안 비교**: ...
**표준 인용**: DOI / arXiv ID / S2 paperId / OpenAlex Work ID + 발표처
**적용 조건**: ...
**신뢰성·재현성 조건**: 코드/peer review/재현 보고/한계/철회 (`is_retracted`)

### 6. 3-source 교차 검증 로그
- 총: arXiv N1 / S2 N2 / OpenAlex N3 → 중복 제거 후 K
- 3중 검증 통과: M / 단일 소스 only: P
- API 응답: arXiv 200 / S2 200 / OA 200

### 7. Hand-off 후보
- HIGH ≥ 3 → 카탈로그 lookup / 코드 구현 → executor(opus) / 0건 → document-specialist(opus)

---
※ 본 결과는 외부 API 응답 원문 기반이며, 인용 전 사용자 검증 권장.
※ PDF 링크 안전성은 사용자 책임입니다.
```

### Degraded Mode 케이스 (2-of-3, 1-of-3)

상단 배너:
- 2-of-3: `⚠️ degraded mode: <source> unavailable`
- 1-of-3: `⚠️⚠️ severe degradation: only <source> responding`

신뢰성 필드에 single-source 한계 명시.

### 0건 대응 케이스

```markdown
## Research — <query>

### 검색 결과 없음

3-source 모두 0건. 다음을 시도해보세요:
1. 검색어 재정제 (한→영, 약어 풀기, 카탈로그 ID 사용)
2. 연도 범위 확장 (`--years 2010-2026`)
3. 카탈로그 lookup 먼저 (`/pattern search <키워드>`)
4. document-specialist 에이전트 위임

추천 다음 명령:
- `/dev-advisor research "<재정제된 검색어>"`
- `/pattern search <키워드>`
- `spawn_agent(agent_type="document-specialist", message="...")`
```

### 사전 차단 정책 (출력 전 검증)

매트릭스 행 생성 시 모두 통과해야 함:
- 식별자 1개+ 정규식 검증 (`^10\.\d{4,}/`, `^\d{4}\.\d{4,5}(v\d+)?$`, `^[a-f0-9]{40}$`, `^W\d{8,}$`)
- URL 화이트리스트 (`arxiv.org` / `doi.org` / `semanticscholar.org` / `openalex.org`만)
- 메타 필드 raw API 응답 직접 reference (Claude 추정 X)
- 카탈로그 매핑 ID는 catalog-index.json 실제 ID 목록
- weak-evidence ≤ 2
- is_retracted=true 논문 ⚠️ + RETRACTED 명시

상세: [research/output-format.md](research/output-format.md) / [research/testing.md](research/testing.md) HR-01~HR-10
