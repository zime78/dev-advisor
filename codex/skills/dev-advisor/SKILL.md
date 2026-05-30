---
name: dev-advisor
description: 앱 개발 어드바이저 — 6중 카탈로그(543 패턴 / 292 알고리즘 / 75 언어 / 106 보안 / 211 원칙 / 20 품질 + 20 부록). **9 모드** — recommend / validate / refactor / maintain / security-audit / qa / qc / research / audit (`--mode=serial\|parallel`, legacy aliases full / swarm). 호출 — `/dev-advisor <mode>`, `/pattern <id>`, `/algorithm <id>`, `/language <id>`, `/security <id>`, `/principle <id>`, `/quality <id>`. 코드/모듈/API 입력 시 advisor 모드 우선 라우팅.
argument-hint: "<recommend|validate|refactor|maintain|security-audit|qa|qc|research|audit|full|swarm|--help|pattern|algorithm|language|security|principle|quality> [input]"
---

# Dev Advisor — Patterns, Algorithms, Languages, Security, Quality

각 advisor 모드의 절차·산출물·인용 references는 `references/workflows/<mode>.md` 참조.

## 목적

**앱 개발 시 올바른 방향으로 개발할 수 있도록 안내하는 어드바이저**다. 현재 프로젝트에 맞는 소프트웨어 개발 프로세스를 추천하고, 검증하고, 리팩토링을 가이드하고, 유지보수를 지원한다.

## Codex 실행 규칙

- **[필수]** `references/`와 `scripts/`는 현재 스킬 디렉터리 기준 상대 경로로 읽는다. 하드코딩 금지.
- **[필수]** `swarm` 또는 OMX hand-off에서 분석·설계·리뷰 에이전트 호출 시 Codex 역할 서브에이전트(`architect`, `critic`, `planner`, `code-reviewer`, `security-reviewer` 등)를 사용한다. 복잡한 설계·리뷰 작업은 AGENTS.md 정책에 따라 xhigh 계열 역할을 우선한다.
- **[필수]** `/language <id>` 응답은 `사용처/특징/장점/제약/실사용 예제/관련 문서`를 포함하며, `관련 문서`에 공식/표준/레퍼런스 링크 3개 이상 제공한다.
- **[권장]** 카탈로그 변경 후 `bash scripts/verify-references.sh`를 실행하고, 실패 1건 이상 시 수정 후 재실행한다.

## 데이터 기반 — 6중 카탈로그

<!-- Counts are synced from .counts.manifest via bin/sync-skill-counts.sh. Do not edit count numbers manually. -->

| 도메인 | 디렉토리 | 항목 수 | 용도 |
|---|---|--:|---|
| Patterns   | `references/patterns/`   | <!--counts:patterns-->543<!--/--> | 디자인·아키텍처 의사결정 (55 카테고리) |
| Algorithms | `references/algorithms/` | <!--counts:algorithms-->292<!--/--> | 자료구조·연산·분산·동시성 (32 카테고리) |
| Languages  | `references/languages/`  | <!--counts:languages-->75<!--/--> | 언어 선택·비교·분야별 추천 |
| Security   | `references/security/`   | <!--counts:security-->106<!--/--> | 인증·인가·암호·API·모바일·AI·규제 (15 파일) |
| Principles | `references/principles/` | <!--counts:principles-->211<!--/--> + <!--counts:micro-->20<!--/--> 부록 | SOLID / GRASP / ISO 25010 / 12-Factor / Code Smells + 확장 16 + 미시 18 |
| Quality    | `references/quality/`    | <!--counts:quality-->20<!--/--> | QA 10 + QC 10 — 요구사항·테스트·릴리즈·게이트 |

합계 **<!--counts:total-->1247<!--/--> 항목 + <!--counts:micro-->20<!--/--> 부록**.

## 호출 인터페이스

### 1. 카탈로그 lookup (6 도메인)

| 명령 | 패턴 (<!--counts:patterns-->543<!--/-->) | 알고리즘 (<!--counts:algorithms-->292<!--/-->) | 언어 (<!--counts:languages-->75<!--/-->) | 보안 (<!--counts:security-->106<!--/-->) | 원칙 (<!--counts:principles-->211<!--/-->+<!--counts:micro-->20<!--/-->) | 품질 (<!--counts:quality-->20<!--/-->) |
|---|---|---|---|---|---|---|
| `list` | `/pattern list` | `/algorithm list [cat]` | `/language list` | `/security list` | `/principle list` | `/quality list` |
| `search` | `/pattern search 생성` | `/algorithm search 정렬` | `/language search 웹` | `/security search 인증` | `/principle search 결합도` | `/quality search release` |
| `<id>` | `/pattern singleton` | `/algorithm quick-sort` | `/language python` | `/security oauth2-pkce` | `/principle srp` | `/quality qa-test-strategy` |

### 2. advisor 모드 (9 모드)

| advisor 호출 | 1차 산출물 | 절차 상세 |
|---|---|---|
| `/dev-advisor recommend <context>` | 후보 매트릭스 3~5행 + Trade-off | [`workflows/recommend.md`](references/workflows/recommend.md) |
| `/dev-advisor validate <file\|module>` | 위반 항목 표 + P1/P2/P3 | [`workflows/validate.md`](references/workflows/validate.md) |
| `/dev-advisor refactor <file\|function>` | 단계 표 + Before/After + 회귀 위험 | [`workflows/refactor.md`](references/workflows/refactor.md) |
| `/dev-advisor maintain <module\|project>` | 코드 스멜 5 그룹 + 부채 표 + 우선순위 | [`workflows/maintain.md`](references/workflows/maintain.md) |
| `/dev-advisor security-audit <module\|api>` | STRIDE 6행 + DREAD + 컴플라이언스 | [`workflows/security-audit.md`](references/workflows/security-audit.md) |
| `/dev-advisor qa <module\|path>` | 요구사항 추적성 + 테스트 전략 + 릴리즈 준비도 | [`workflows/qa.md`](references/workflows/qa.md) |
| `/dev-advisor qc <module\|path>` | 빌드/테스트 증거 + 품질 게이트 + 릴리즈 차단 | [`workflows/qc.md`](references/workflows/qc.md) |
| `/dev-advisor research <topic>` | 논문 매트릭스 + 카탈로그 cross-ref + 6 필드 | [`workflows/research.md`](references/workflows/research.md) |
| `/dev-advisor audit [--mode=serial\|parallel] <module\|path>` | 7 모드 통합 + Top 10 + 단일 6 필드 (`serial` 기본 / `parallel` ULW) | [`workflows/audit.md`](references/workflows/audit.md) |
| `/dev-advisor --help` | 모드/옵션/사용법 텍스트 | [`references/_help.md`](references/_help.md) |
| _legacy_ `/dev-advisor full <…>` ≡ `audit --mode=serial`, `/dev-advisor swarm <…>` ≡ `audit --mode=parallel` | (호환용) | [`workflows/full.md`](references/workflows/full.md) · [`workflows/swarm.md`](references/workflows/swarm.md) |

`audit --mode=serial`은 단일 컨텍스트 7 모드 순차 통합, `audit --mode=parallel`은 OMX ultrawork 기반 7 서브에이전트 병렬 + reviewer 통합. `research`는 audit에 미포함 (독립). 라우팅 우선순위·audit `--mode` 자동 분기는 [`references/workflows/_routing.md`](references/workflows/_routing.md) 참조.

### 3. cross-skill 라우팅 — data-advisor (DMBOK)

`data-advisor` 는 dev-advisor 와 **별도 스킬**(DMBOK KA 기반 데이터 관리 카탈로그, lookup-only, advisor 모드 없음)이다. dev-advisor 만 호출되어도 아래 **DMBOK 데이터 관리 주제**가 입력에 감지되면 `data-advisor` 로 hand-off 한다. 대상 reference (cross-skill 상대경로): [`db-fundamentals.md`](../data-advisor/references/principles/db-fundamentals.md) (KA2) · [`mdm.md`](../data-advisor/references/patterns/mdm.md) (KA7) · [`data-warehousing.md`](../data-advisor/references/patterns/data-warehousing.md) (KA8) · [`data-quality.md`](../data-advisor/references/patterns/data-quality.md) (KA10) · [`db-indexes.md`](../data-advisor/references/algorithms/db-indexes.md) · [`db-storage-engines.md`](../data-advisor/references/algorithms/db-storage-engines.md) · [`db-query-optimizer.md`](../data-advisor/references/algorithms/db-query-optimizer.md) (KA3).

- **[필수-조건: DMBOK 데이터 관리 주제 감지]** 다음 트리거 키워드가 입력/컨텍스트에 있으면 `data-advisor` 로 hand-off 한다 — `MDM`/`마스터 데이터`/`골든 레코드`/`Survivorship`/`Match-Merge` (KA7) · `데이터 웨어하우스`/`DWH`/`Kimball`/`Star`/`Snowflake`/`SCD`/`Fact Table`/`OLAP`/`Lakehouse`/`dbt` (KA8) · `데이터 품질`/`DQ`/`Data Lineage`/`Data Catalog`/`Stewardship`/`OpenLineage` (KA10) · `CAP`/`PACELC`/`격리 수준`/`ACID`/`BASE`/`복제`/`파티셔닝`/`정규화` (KA2) · `B+Tree`/`LSM Tree`/`WAL`/`MVCC`/`Buffer Pool`/`쿼리 옵티마이저`/`EXPLAIN ANALYZE`/`db-indexes`/`db-storage-engines` (KA3) · `DMBOK`.
- **[필수]** hand-off 호출은 `/data <id>` · `/data list` · `/data search <kw>` 또는 `Skill(skill="data-advisor")` 로 한다. 단축 진입점 `/mdm`(KA7) · `/dwh`(KA8) · `/dq`(KA10) 도 동일 스킬로 매핑된다. `data-advisor` 는 도메인 prefix 없이 부명령을 직접 받는다 (예: `/data mdm-golden-record`).
- **[권장]** dev-advisor 카탈로그([`patterns/data-modeling.md`](references/patterns/data-modeling.md) CAP 실무 패턴 · [`patterns/data-access.md`](references/patterns/data-access.md) OO 영속성 · [`algorithms/spatial.md`](references/algorithms/spatial.md)·[`algorithms/search-systems.md`](references/algorithms/search-systems.md) 공간/검색 · [`security/security-data-protection.md`](references/security/security-data-protection.md) 데이터 보안 · [`patterns/mlops.md`](references/patterns/mlops.md) ML/AI 파이프라인)와 겹치는 주제는 dev-advisor 에 유지하고, **순수 DMBOK 데이터 관리 어휘(KA2/3/7/8/10)** 만 `data-advisor` 로 넘긴다. (data-advisor `## Out-of-scope` 와 대칭)

## 워크플로우 (요약)

각 모드의 4단계 입출력·6단계 절차·6 필드 템플릿·출력 스켈레톤은 모드별 파일에 있다:

- [`references/workflows/index.md`](references/workflows/index.md) — 전체 모드 인덱스 + 공통 6 필드 alias 표
- [`references/workflows/_routing.md`](references/workflows/_routing.md) — 라우팅 우선순위 + 라이프사이클 보조 + full vs swarm 규칙
- [`references/workflows/_severity.md`](references/workflows/_severity.md) — 공통 severity 정규화 + 통합 우선순위 매트릭스

## OMX hand-off

advisor 9 모드는 트리거 조건 도달 시 Codex 전문 서브에이전트 또는 별도 스킬로 hand-off 한다. 입출력 계약 상세는 [`references/handoff.md`](references/handoff.md) 참조.

| hand-off 대상 | 종류 | 트리거 요약 |
|---|---|---|
| `architect` | Codex/OMX 역할 서브에이전트 | 아키텍처 영향 ≥ 3 파일 / 계층 재설계 / 도메인 분해 |
| `code-reviewer` | Codex/OMX 역할 서브에이전트 | `refactor`/`validate` 후 PR / 표준·윤리 검토 |
| `security-reviewer` | Codex/OMX 역할 서브에이전트 | DREAD ≥ 8 / 컴플라이언스 carve-out / threat model 등재 |
| `verifier` | Codex/OMX 역할 서브에이전트 | 변경 적용 후 회귀 확인 / autopilot 종료 직전 |
| `designer` | Codex/OMX 역할 서브에이전트 | UI 컴포넌트 영향 ≥ 3 화면 / HCI·UX 평가 |
| `planner` | Codex/OMX 역할 서브에이전트 | 다단계 추정·로드맵 / SDLC·CM 계획 |
| `document-specialist` / `analyst` / `scientist` | Codex/OMX 역할 서브에이전트 | research 모드 외부 문서·비교·통계 분석 |
| `$ai-slop-cleaner` | 스킬 호출 | `maintain` Dispensables 비중 ≥ 40% |
| **`data-advisor`** | **별도 스킬 호출** | **DMBOK 데이터 관리 주제(KA2/3/7/8/10) 감지 — 호출 `/data <id>` · `/mdm` · `/dwh` · `/dq` 또는 `Skill(skill="data-advisor")`** |

- **[필수]** 분석·설계·리뷰 성격 hand-off 는 역할명과 입력 JSON, 기대 산출 형식을 명시해 Codex/OMX 서브에이전트로 위임한다 (bare ID 금지).
- **[필수]** `data-advisor` 는 Codex 서브에이전트가 아니라 **별도 스킬**이므로 스킬 호출(`/data ...` 또는 `Skill(skill="data-advisor")`)로 hand-off 한다.

## 참조 문서

6 도메인 진입점:

| 도메인 | 진입점 |
|---|---|
| 패턴 (<!--counts:patterns-->543<!--/-->) | [`references/patterns/index.md`](references/patterns/index.md) |
| 알고리즘 (<!--counts:algorithms-->292<!--/-->) | [`references/algorithms/index.md`](references/algorithms/index.md) |
| 언어 (<!--counts:languages-->75<!--/-->) | [`references/languages/index.md`](references/languages/index.md) · [`domains.md`](references/languages/domains.md) |
| 보안 (<!--counts:security-->106<!--/-->) | [`references/security/index.md`](references/security/index.md) |
| 원칙 (<!--counts:principles-->211<!--/-->+<!--counts:micro-->20<!--/-->) | [`references/principles/index.md`](references/principles/index.md) · [`micro-principles.md`](references/principles/micro-principles.md) |
| 품질 (<!--counts:quality-->20<!--/-->) | [`references/quality/index.md`](references/quality/index.md) · [`qa.md`](references/quality/qa.md) · [`qc.md`](references/quality/qc.md) |

부가 자산:

- [`references/code_templates.md`](references/code_templates.md) — 자동 코드 생성 (Kotlin/Java/Swift/Python)
- [`references/output_templates.md`](references/output_templates.md) — 9 모드 산출물 스켈레톤
- [`references/examples.md`](references/examples.md) — 실제 호출/응답 예시 10개 (A~J)
- [`references/handoff.md`](references/handoff.md) — OMX hand-off 입출력 계약
- [`references/research/`](references/research/) — research 모드 자산 (sources / query-strategies / mapping-algorithm / fallback / performance / testing)
- `bash scripts/verify-references.sh` — 6 도메인 무결성 검증
