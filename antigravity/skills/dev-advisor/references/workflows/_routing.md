# 라우팅 우선순위 (lookup vs advisor)

dev-advisor의 두 호출 표면(카탈로그 lookup vs advisor 9 모드) 사이의 자동 분기 규칙.

## 라우팅 우선순위 표

발화 형태에 따라 자동 분기한다:

| 발화 패턴 | 라우팅 | 예 |
|---------|--------|----|
| 카탈로그 ID 명시 (`singleton`, `quick-sort`, `python`, `oauth2-pkce`, `jwt`, `srp` 등) | 해당 도메인 lookup | "JWT 보안" → `/security jwt` / "SOLID 위반 사례" → `/principle solid` |
| 코드/모듈/API/파일 경로 입력 동반 (`이 코드`, `이 API`, `path: ...`) | advisor 모드 | "이 API 보안 점검 (api.go)" → `security-audit` |
| 의도 동사만 (`추천`, `검증`, `리팩토링`, `유지보수 점검`, `보안 점검`) | advisor 모드 | "기술 부채 점검해줘" → `maintain` |
| 품질 프로세스 키워드 (`QA`, `품질 보증`, `테스트 전략`, `릴리즈 승인`) | `qa` 모드 | "이 모듈 QA 점검" → `qa <module>` |
| 품질 실행 키워드 (`QC`, `품질 게이트`, `테스트 실행`, `결함 재현`) | `qc` 모드 | "릴리즈 전 QC 검증" → `qc <module>` |
| 통합 점검 명시 키워드 (`전체 점검`, `종합 분석`, `모두 체크`, `full audit`) | `audit --mode=serial` (legacy alias: `full`) | "이 모듈 전체 점검해줘" → `audit --mode=serial <module>` |
| 병렬 심층 명시 키워드 (`병렬 점검`, `심층 분석`, `swarm`, `ultra audit`) | `audit --mode=parallel` (legacy alias: `swarm`) | "이 모듈 심층 분석" → `audit --mode=parallel <module>` |
| 학술/연구/논문 키워드 ("논문", "research", "SOTA", "literature", "evidence") | research 모드 | "Transformer 최신 연구" → `research transformer` |
| 둘 다 모호 | **시퀀스**: 1) lookup 응답 출력, 2) 후속 advisor 모드 분기 질문 | "JWT 보안 검토" → 1) `/security jwt` 출력 → 2) "특정 코드/API 를 검사할까요?" 질문 |

## research 모드 충돌 해소 규칙

| 입력 패턴 | 라우팅 | 예 |
|----------|--------|----|
| 학술 키워드 + 카탈로그 ID 명시 | 시퀀스: lookup → research | "transformer 패턴 최신 연구" → `/pattern transformer` → 확인 → `research transformer` |
| 학술 키워드 + 코드/모듈 입력 | 시퀀스: `<advisor mode> + research` | "이 API 보안 점검 + 최신 연구" |
| "최신 연구"/"SOTA" 단독 | `research` 단독 | "transformer SOTA" → `research transformer` |
| 학술 키워드 + 통합 키워드 | `audit --mode=serial` 후 `research` (research는 audit 미포함) | 명시적 시퀀스 |

## 라이프사이클 보조 라우팅

`dev-advisor`의 advisor 모드는 계속 9개로 유지한다. 다만 사용자가 개발 생명주기의 특정 단계만 언급하면 아래 보조 라우팅으로 적절한 카탈로그와 9모드 조합을 선택한다.

| 보조 라우트 | 범위 | 기본 매핑 |
|---|---|---|
| `lifecycle` | Discovery → Requirements → Design → Build → Test → Release → Operate → Improve 전체 흐름 | 단계 식별 후 `recommend / validate / qa / qc / security-audit / maintain` 중 필요한 모드로 분기 |
| `requirements` | PRD, user story, NFR, acceptance criteria, traceability, scope/risk | `qa` + `patterns/requirements-engineering.md` + `principles/sdlc-models.md` |
| `release` | rollout, migration, rollback, hotfix, release note, go/no-go | `qa` + `qc` + `patterns/deployment.md` + `principles/configuration-management.md` |
| `ops` / `sre` | SLO, alert, runbook, on-call, incident, postmortem, capacity, DR | `maintain` + `qc` + `patterns/observability.md` + `principles/process-metrics.md` + `principles/resilience-theory.md` |
| `ecosystem/current-docs` | framework, SDK, cloud, library, CLI, 버전 마이그레이션 | 카탈로그에 고정하지 않고 최신 공식 문서 조회로 라우팅. 안정적 판단 원칙은 본 카탈로그를 보조 근거로만 사용 |
| `evidence` / `research` | 학술 논문, SOTA 추적, 표준 RFC/NIST, 벤치마크 보고, 비교 연구 | `research` 모드 + 카탈로그 cross-ref (단방향) |

## audit `--mode` 자동 라우팅 보조 규칙

| 조건 | 라우팅 |
|---|---|
| 명시적 키워드 (`audit`, `full`, `swarm`) | 해당 모드/별칭 우선. `full` → `audit --mode=serial`, `swarm` → `audit --mode=parallel` |
| 의도 동사만 (`종합 점검`) — 별다른 조건 없음 | `audit --mode=serial` (default, 순차 통합) |
| 입력 코드 규모 > 1000 LOC | `audit --mode=parallel` 권장 (단일 컨텍스트 한계 — 1만~2만 토큰 × 7 = 압축 불가피) |
| OMC ultrawork 또는 Claude Code 서브에이전트 사용 불가 환경 | `audit --mode=serial` fallback (병렬 위임 불가 → 순차 직렬 실행) |
| 6 도메인 중 1~2 모드만 필요 | 개별 advisor 모드 단독 호출 권장 |

Legacy aliases:
- `/dev-advisor full <module|path>` ≡ `/dev-advisor audit --mode=serial <module|path>`
- `/dev-advisor swarm <module|path>` ≡ `/dev-advisor audit --mode=parallel <module|path>`

research는 `audit` (legacy `full` / `swarm`)에 미포함 (독립 모드 — 토큰 한계 + 외부 API 의존성 격리).
