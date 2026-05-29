# `audit` 모드 — 7 모드 통합 점검 (serial | parallel)

`recommend / validate / refactor / maintain / security-audit / qa / qc` 7 모드의 1~5단계를 통합 호출하고 단일 보고로 합산. 실행 토폴로지는 `--mode=serial`(default) 또는 `--mode=parallel`로 선택한다.

`research`는 `audit`에 미포함 (독립 모드 — 토큰 한계 + 외부 API 의존성 격리).

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 모듈/path 필수 + `--mode=serial\|parallel` (선택) | 7 모드 sub-섹션 통합 + 통합 우선순위 Top 10 + 단일 6 필드 |

## --mode 선택 기준

| --mode | 실행 토폴로지 | 토큰 예상 | 권장 조건 |
|--------|--------------|----------|----------|
| `serial` (default) | 단일 컨텍스트에서 7 모드 순차 호출 | 1만~2만 × 7 = 7만~14만 | 단일 모듈 / OMC ultrawork 사용 불가 환경 / 안전 우선 |
| `parallel` | OMC ultrawork + Claude Code Task 7 서브에이전트 병렬 → reviewer 통합 | 1만~2만 × 7 (병렬) + reviewer 5천 ≈ 8만~16만 | 입력 코드 규모 > 1000 LOC / 독립 분석 토픽 / ultrawork 사용 가능 환경 |

명시적 키워드 매핑:
- "전체 점검" / "종합 분석" / "모두 체크" / "full audit" → `--mode=serial`
- "병렬 점검" / "심층 분석" / "swarm" / "ultra audit" → `--mode=parallel`

## 인용 references

7 모드 references 통합:

- [`workflows/recommend.md`](recommend.md)
- [`workflows/validate.md`](validate.md)
- [`workflows/refactor.md`](refactor.md)
- [`workflows/maintain.md`](maintain.md)
- [`workflows/security-audit.md`](security-audit.md)
- [`workflows/qa.md`](qa.md)
- [`workflows/qc.md`](qc.md)
- [`workflows/_severity.md`](_severity.md) — 공통 severity 정규화 + 통합 우선순위 매트릭스

`--mode=parallel`에 한해 추가 인용:

- OMC ultrawork + Claude Code `Task(subagent_type="oh-my-claudecode:<name>", model="opus", ...)` 기반 병렬 실행
- verifier 또는 code-reviewer / security-reviewer / architect hand-off

## audit 모드 절차 — `--mode=serial` (순차 통합)

1. **입력 수집** — 단일 모듈/path. 여러 path 동시 입력 시 `--mode=parallel` 권장
2. **컨텍스트 분류** — 언어 자동 감지 + 프로젝트 규모 (LOC) + 스택 신호 + 도메인 분류. **공통 컨텍스트**로 7 모드에 재사용 (중복 분석 방지)
3. **7 sub-모드 순차 호출** — `recommend → validate → security-audit → qa → qc → maintain → refactor` 순서로 각 모드의 1~5단계를 단축 실행 (refactor 는 validate/maintain/qc 결과 의존이라 마지막)
4. **통합 분석** — 7 결과의 우선순위 매트릭스로 합산 ([`_severity.md`](_severity.md) 참조). Top 10 추출
5. **근거 산출** — 7 모드의 6 필드를 통합 압축한 **단일 6 필드** 작성 (선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천·예외·수용·품질 차단 통합 조건)
6. **hand-off** — 가장 큰 위반 영역의 reviewer 분기 (보안 위반 우세 → `security-reviewer`, 아키텍처 영향 ≥ 3 파일 → `architect`, P1 ≥ 3 → `code-reviewer`)

## audit 모드 절차 — `--mode=parallel` (병렬 ULW)

1. **입력 수집** — 모듈/path
2. **컨텍스트 분류** — 언어 자동 감지 + 규모 + 스택 + 도메인. 공통 컨텍스트를 7 서브에이전트에 공유 prompt 로 전달
3. **ULW 1차 발사** — Claude Code `Task(subagent_type="oh-my-claudecode:executor", model="opus", description="...", prompt="...")` 형태로 독립 분석 7명을 병렬 호출 (각 모드 1명: recommend / validate / security-audit / qa / qc / maintain / refactor). 분석·설계·리뷰 성격의 ULW 호출은 전역 `CLAUDE.md`의 OMC 모델 정책에 따라 `model="opus"` 를 명시한다.
4. **결과 수집** — 7 보고를 모두 수집하고 중복 이슈·충돌 판정·P1 후보를 정규화
5. **Reviewer 통합** — 7 결과를 입력으로 reviewer 1명(`verifier` default, 옵션 `code-reviewer` / `security-reviewer` / `architect`)을 호출하거나 로컬 synthesis 로 통합한다. reviewer 는 P1/심각도/영향 비교 후 통합 Top 10 + 단일 6 필드를 산출한다.
6. **hand-off** — reviewer 판단에 따라 후속 에이전트 또는 스킬로 분기 (보안 위반 우세 → `security-reviewer`, 아키텍처 영향 → `architect`, PR 준비 → `code-reviewer`, 회귀 검증 → `verifier`, deslop → `/oh-my-claudecode:ai-slop-cleaner`)

## 산출물 출력 스켈레톤 — `--mode=serial`

```
## Audit (serial) — <module|path>

### 1. recommend
<후보 매트릭스 3~5행 + trade-off>

### 2. validate
<위반 표 + P1/P2/P3>

### 3. security-audit
<STRIDE 6행 + DREAD>

### 4. qa
<요구사항 추적성 + 테스트 전략 + 릴리즈 준비도>

### 5. qc
<빌드/테스트 실행 증거 + 품질 게이트 + 릴리즈 차단 증거>

### 6. maintain
<코드 스멜 5 그룹 + 부채 표>

### 7. refactor
<단계 표 + Before/After>

### 통합 우선순위 Top 10
| # | 항목 | 출처 모드 | 심각도 | 영향 | 즉시성 | 점수 |

### 통합 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천·예외·수용·품질 차단 통합 조건

### Hand-off
<우세 영역 → reviewer 분기>
```

## 산출물 출력 스켈레톤 — `--mode=parallel`

```
## Audit (parallel) — <module|path>

### Parallel Results (7 Claude Code subagents)
<recommend / validate / security-audit / qa / qc / maintain / refactor 결과 7 개 sub-섹션>

### Reviewer Synthesis (<reviewer agent>)
#### 통합 우선순위 Top 10
| # | 항목 | 출처 모드 | 심각도 | 영향 | 즉시성 | 점수 |

#### 통합 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천·예외·수용 통합 조건

### Hand-off
<reviewer 결정 → 후속 에이전트>
```

## OMC hand-off 후보

- 보안 위반 우세 → `security-reviewer`
- 아키텍처 영향 ≥ 3 파일 → `architect`
- P1 ≥ 3 → `code-reviewer`
- PR 준비 (`--mode=parallel`) → `code-reviewer`
- 변경 후 회귀 → `verifier`
- deslop 정리 (`--mode=parallel` 후 dispensables 비중 ≥ 40%) → `/oh-my-claudecode:ai-slop-cleaner`

## Legacy aliases

- `/dev-advisor full <module|path>` ≡ `/dev-advisor audit --mode=serial <module|path>`
- `/dev-advisor swarm <module|path>` ≡ `/dev-advisor audit --mode=parallel <module|path>`

기존 호출자는 그대로 동작하며 내부적으로 audit 모드로 라우팅된다. 신규 호출은 `audit --mode=` 사용을 권장한다.
