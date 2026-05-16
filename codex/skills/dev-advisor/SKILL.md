---
name: dev-advisor
description: 5중 카탈로그(547 패턴 / 273 알고리즘 / 75 언어 / 106 보안 / 212 원칙 + 18 부록)로 앱 개발을 안내하는 Codex용 어드바이저. 7 advisor 모드 (5 기본 + 2 통합) — recommend / validate / refactor / maintain / security-audit / full / swarm + lookup. 트리거 — '/dev-advisor recommend|validate|refactor|maintain|security-audit|full|swarm', '/pattern singleton|mvvm|clean-architecture', '/algorithm quick-sort|dijkstra|bfs', '/language python|kotlin|rust', '/security oauth2-pkce|jwt|rbac', '/principle srp|grasp|iso25010', '아키텍처 추천', '코드 검증', '리팩토링 가이드', '기술 부채 점검', '보안 점검', '전체 점검', '종합 분석', '병렬 점검', '심층 분석', 'swarm', 'dev-advisor'.
---

# Dev Advisor — Patterns, Algorithms, Languages, Security

## 목적

**앱 개발 시 올바른 방향으로 개발할 수 있도록 안내하는 어드바이저**다. 현재 프로젝트에 맞는 소프트웨어 개발 프로세스를 추천하고, 검증하고, 리팩토링을 가이드하고, 유지보수를 지원한다.

### 7가지 핵심 기능 (5 기본 + 2 통합)

각 기능은 `advisor` 7 모드 중 하나로 직접 매핑된다. 자세한 절차·출력 포맷은 `## 워크플로우` 섹션 참조.

| # | 기능 | 모드 | 1차 출력 형태 |
|---|---|---|---|
| 1 | **추천 (Recommend)** | `recommend`      | 후보 매트릭스 3~5행 + 선택 근거(왜) + 대안 trade-off |
| 2 | **검증 (Validate)** | `validate`       | 위반 항목 표 + 표준 인용 (SOLID/GRASP/DDD/Clean Arch/ISO 25010/12-Factor/OWASP/NIST) + 우선순위 P1/P2/P3 |
| 3 | **리팩토링 가이드 (Refactor Guide)** | `refactor`       | 단계 표 + Before/After 코드 + 회귀 위험 등급 |
| 4 | **유지보수 (Maintain)** | `maintain`       | 안티패턴/기술 부채 표 + 우선순위(영향 × 발생빈도) + 코드 스멜 5 그룹 |
| 5 | **보안 점검 (Security Audit)** | `security-audit` | STRIDE 6행 표 + DREAD 점수 + 컴플라이언스 매핑 + 표준 인용 (OWASP/NIST/RFC) |
| 6 | **전체 점검 (Full)** | `full`           | 5 모드 sub-섹션 순차 통합 + 통합 우선순위 Top 10 + 단일 6 필드 |
| 7 | **병렬 심층 점검 (Swarm)** | `swarm`          | 5 Codex 서브에이전트 병렬 결과 + reviewer 통합 + Top 10 (OMX ultrawork) |

모든 모드는 5번째 단계에서 **선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천(예외/수용) 조건** 6 필드 산출이 필수다. `full` / `swarm` 은 5 기본 모드의 6 필드를 통합 압축한다.

### 데이터 기반 — 5중 카탈로그 (5 도메인)

5 카탈로그는 도메인 특성에 맞춘 비대칭 구조 (데이터 비대칭, 호출 표면 `list / search / <id>` 대칭) + advisor 8 형태 (`recommend / validate / refactor / maintain / security-audit / full / swarm / --help`). 자세한 동작은 **## 호출 인터페이스** 섹션.

| 도메인 | 디렉토리 | 항목 수 | 용도 | 구조 |
|---|---|--:|---|---|
| Patterns   | `references/patterns/`   | 547 | 디자인·아키텍처 의사결정 (산업 도메인 포함, MDM·DQ 거버넌스 + Web Performance / Data Warehousing & BI / HPC-Scientific 신설) | 55 카테고리, `patterns/<category>.md` + `patterns/domains/<industry>.md` 평면 inline + 카테고리당 `## N.` 헤더 |
| Algorithms | `references/algorithms/` | 273 | 자료구조·연산·분산·동시성·파싱·DB·OS·미디어 | 32 카테고리, `<a id>` anchor + 카테고리 목차 + `algorithms/index.md` 전역 ID 매핑 (4중 lookup) |
| Languages  | `references/languages/`  |  75 | 언어 선택·비교·분야별 추천 | 분야 매트릭스, `languages/<lang>.md` 평탄 + 우선순위 `index.md` + 분야별 `domains.md` |
| Security   | `references/security/`   | 106 | 인증·인가·암호 운영·데이터 보호·API/Web·공급망·플랫폼·SDLC·탐지·모바일·AI 모델·프라이버시·규제 | 15 파일 (메타 4 + 12 sub-카테고리 + Privacy Engineering 9 + 컴플라이언스 5), `security/index.md` ID→파일 + cross-link 매트릭스 |
| **Principles** | `references/principles/` | **212 + 18 부록** | **SOLID / GRASP / ISO 25010 / 12-Factor / Code Smells + 타입 시스템 / 동시성 이론 / Refactoring 기법 / SW 경제·추정 / 진화적 아키텍처 / 탄력성 / 문서화 / DORA / 성능 / Green Software + DB 기초 / SDLC 모델 / Scaled Agile / 직업 윤리 + Standards Mapping (SWEBOK/CS2023/DMBOK/OWASP/NIST-ISO) / Configuration Management (IEEE 828 SCMP) + HCI Methodology (ISO 9241 / Persona / Journey Map / Heuristic Eval) / Formal Methods (TLA+ / Alloy / Hoare / Model Checking)** | 21 파일 + 부록 [`micro-principles.md`](references/principles/micro-principles.md) (DRY/KISS/YAGNI/LoD/SoC/Tell-Don't-Ask/Composition/SSoT + Conway/Hyrum/Postel/Brooks/Hollywood/Boy Scout/Pareto/Goodhart/Cunningham/Inverse Conway, verify 카운트 외, `/principle <id>` 호출 가능). advisor 7 모드의 핵심 표준 인용 source |

합계 **1,213 항목 + 18 부록** (verify 카운트 기준).

### 언어 지원 범위

- **자동 감지**: 13 언어 (Kotlin / Java / Swift / Python / JavaScript / TypeScript / Go / Rust / C++ / C# / Ruby / PHP / Scala) — [`references/languages/index.md#언어-자동-감지`](references/languages/index.md#언어-자동-감지)
- **자동 코드 생성**: 4 언어 (Kotlin / Java / Swift / Python) — [`references/code_templates.md`](references/code_templates.md) GoF 패턴 템플릿 기준
- **그 외 언어**: 75 언어 전체에 대해 `/language <id>` lookup 으로 reference (사용처/특징/장점/제약/실사용 예제/관련 문서) 를 제공, 자동 코드 생성은 미지원

## Scope (포함 / 비포함 경계)

**In-scope**: 디자인 패턴 (GoF 23 + 아키텍처/분산/신뢰성/동시성/통합/DDD 전술/데이터 접근/보안/테스트/Observability/AI-LLM/배포/캐싱) · 알고리즘 (정렬·탐색·그래프·DP·문자열·수학·자료구조·암호·ML·확률·합의·분산·동시성·파싱) · 프로그래밍 언어 reference (사용처/특징/장점/제약/실사용 예제/관련 문서/비교) · 안티패턴 / 리팩토링 카탈로그 (카테고리 내 항목).

**Out-of-scope**: 프레임워크별 가이드 (React/Spring/Django/Rails 등 product-specific) · 벤더 SDK API 사용법 (AWS/GCP/Azure/Firebase) · 클라우드 관리형 서비스 매핑 · 라이브러리 버전 마이그레이션 가이드.

**경계 원칙**: 이 카탈로그는 "**이름을 모르면 검색조차 못 하는 추상 어휘**"를 다룬다. 버전 의존적·product-specific 항목은 명시적으로 out-of-scope.

## 호출 인터페이스

호출 표면은 두 층 — **카탈로그 lookup** (5 도메인 × `list / search / <id>`, ID 명시 조회) + **advisor 모드** (5 모드 + `--help`, 코드/모듈/API 입력 + 절차적 분석).

### 1. 카탈로그 lookup (5 도메인)

| 명령        | 패턴 (547)           | 알고리즘 (273)                  | 언어 (75)          | 보안 (106)             | 원칙 (212 + 18 부록)   |
|-------------|---------------------|--------------------------------|--------------------|-----------------------|-----------------------|
| `list`      | `/pattern list`     | `/algorithm list [category]`   | `/language list`   | `/security list`      | `/principle list`     |
| `search <kw>` | `/pattern search 생성` | `/algorithm search 정렬`      | `/language search 웹` | `/security search 인증` | `/principle search 결합도` |
| `<id>`      | `/pattern singleton`| `/algorithm quick-sort`        | `/language python` | `/security oauth2-pkce` | `/principle srp`      |

### 2. advisor 모드 (옵션 추가)

| advisor 호출 | 자연어 트리거 | 1차 산출물 |
|-------------|--------------|-----------|
| `/dev-advisor recommend <context>`       | "추천", "아키텍처 추천"      | 후보 매트릭스 3~5행 + Trade-off + 근거 |
| `/dev-advisor validate <file\|module>`     | "검증", "체크", "맞아?"      | 위반 항목 표 + 표준 인용 + P1/P2/P3 |
| `/dev-advisor refactor <file\|function>`   | "리팩토링", "Before/After"   | 단계 표 + Before/After + 회귀 위험 |
| `/dev-advisor maintain <module\|project>`  | "유지보수", "기술 부채"      | 코드 스멜 5 그룹 + 부채 표 + 우선순위 |
| `/dev-advisor security-audit <module\|api>`| "보안 점검", "취약점"        | STRIDE 6행 + DREAD + 컴플라이언스 |
| `/dev-advisor full <module\|path>`         | "전체 점검", "종합 분석", "모두 체크", "5 도메인 분석", "full audit" | 5 모드 통합 보고 + 우선순위 Top 10 + 단일 6 필드 |
| `/dev-advisor swarm <module\|path>`        | "병렬 점검", "심층 분석", "swarm", "ultra audit", "5 에이전트 분석" | 5 Codex 서브에이전트 병렬 → reviewer 통합 + Top 10 |
| `/dev-advisor --help`                    | "도움말", "사용법"           | 모드/옵션/사용법 텍스트 |

자세한 절차·산출물·인용 references 는 **## 워크플로우** 섹션 참조. `full` 은 순차 통합 (5 모드 직렬 실행), `swarm` 은 OMX ultrawork 기반 병렬 통합 (5 Codex 서브에이전트 + reviewer)이다.

### list / search / `<id>` 동작

- **list**: 도메인 카테고리 진입점 표 응답. 패턴/보안/원칙은 `<domain>/index.md` 카테고리 매핑, 알고리즘은 `references/algorithms/index.md` 32 카테고리 표, 언어는 `references/languages/index.md` 우선순위 + 분야 매트릭스. **list <category>**: 카테고리 파일 `## 목차` 응답 (알고리즘만 카테고리 인자).
- **search**: 키워드를 각 도메인 `index.md` 의 **별칭 표·영문명·한글명·태그 4 컬럼**과 매칭하여 상위 ID 목록 반환. 매칭 우선순위: 별칭 표 > 영문명 > 한글명 > 태그.
- **`<id>` 동작 (도메인별)**:
  - `/pattern <id>` → `references/patterns/index.md` ID→file → `<category>.md#<id>` 본문
  - `/algorithm <id>` → 별칭 / ID 매핑 / 명명 규칙 / 호출 동작 (4중 lookup) 모두 [`references/algorithms/index.md`](references/algorithms/index.md)
  - `/language <id>` → 언어 별칭 / 명명 규칙 / 호출 동작 / 분야 추천 모두 [`references/languages/index.md`](references/languages/index.md)
  - `/security <id>` → `references/security/index.md` ID→file → `<file>.md#<id>` 본문
  - `/principle <id>` → `references/principles/index.md` 별칭 표 → primary ID → `<file>.md#<anchor>`. 별칭 예: `single-responsibility→srp`, `god-class→code-smell-large-class`, `12factor`/`twelve-factor→12-factor`. **미시 원칙 18 항목** (`dry`, `kiss`, `yagni`, `lod`, `soc`, `tell-dont-ask`, `composition-over-inheritance`, `ssot`, `conway-law`, `hyrum-law` 등) 도 같은 경로로 [`micro-principles.md`](references/principles/micro-principles.md) (주 카탈로그 212 외 부록).

자연어 호출 (예: "싱글톤 적용해줘", "퀵 정렬 구현해줘", "OAuth2 PKCE 어떻게?", "SOLID 위반 사례") 도 동일 lookup. 모호 시 search 결과 우선 제시.

### 라우팅 우선순위 (lookup vs advisor)

발화 형태에 따라 자동 분기한다:

| 발화 패턴 | 라우팅 | 예 |
|---------|--------|----|
| 카탈로그 ID 명시 (`singleton`, `quick-sort`, `python`, `oauth2-pkce`, `jwt`, `srp` 등) | 해당 도메인 lookup | "JWT 보안" → `/security jwt` / "SOLID 위반 사례" → `/principle solid` |
| 코드/모듈/API/파일 경로 입력 동반 (`이 코드`, `이 API`, `path: ...`) | advisor 모드 | "이 API 보안 점검 (api.go)" → `security-audit` |
| 의도 동사만 (`추천`, `검증`, `리팩토링`, `유지보수 점검`, `보안 점검`) | advisor 모드 | "기술 부채 점검해줘" → `maintain` |
| 통합 점검 명시 키워드 (`전체 점검`, `종합 분석`, `모두 체크`, `full audit`) | `full` 모드 | "이 모듈 전체 점검해줘" → `full <module>` |
| 병렬 심층 명시 키워드 (`병렬 점검`, `심층 분석`, `swarm`, `ultra audit`) | `swarm` 모드 | "이 모듈 심층 분석" → `swarm <module>` |
| 둘 다 모호 | **시퀀스**: 1) lookup 응답 출력, 2) 후속 advisor 모드 분기 질문 | "JWT 보안 검토" → 1) `/security jwt` 출력 → 2) "특정 코드/API 를 검사할까요?" 질문 |

**full vs swarm 자동 라우팅 보조 규칙**:

| 조건 | 라우팅 |
|---|---|
| 명시적 키워드 (`full` / `swarm`) | 해당 모드 우선 |
| 의도 동사만 (`종합 점검`) — 별다른 조건 없음 | `full` (default, 순차 통합) |
| 입력 코드 규모 > 1000 LOC | `swarm` 권장 (단일 컨텍스트 한계 — 1만~2만 토큰 × 5 = 압축 불가피) |
| OMX ultrawork 또는 Codex 서브에이전트 사용 불가 환경 | `full` fallback (병렬 위임 불가 → 순차 직렬 실행) |
| 5 도메인 중 1~2 모드만 필요 | 개별 advisor 모드 단독 호출 권장 |

## 알고리즘 (273개, 32 카테고리)

32 카테고리 진입점 표 + 273 알고리즘 ID → 파일 매핑 + ID 명명 규칙 + `/algorithm <id>` 호출 동작 + 별칭 표 (`knn`, `bit`, `rb-tree`, `disjoint-set`, `a-star-search`, `lru-cache`, `breadth-first-search`, `depth-first-search` 등 8개) 는 [`references/algorithms/index.md`](references/algorithms/index.md) 참조.

## 프로그래밍 언어 (75개)

75 언어 reference (사용처/특징/장점/제약/실사용 예제/관련 문서) + 분야별 진입점(웹/AI/모바일/게임/시스템/DevOps) + `/language <id>` 호출 동작 + 명명 규칙 (kebab-case + 특수 기호 ASCII 정규화) + 별칭 표 (`js→javascript`, `ts→typescript`, `py→python`, `c++→cplusplus`, `c#→csharp`, `f#→fsharp`, `objc→objective-c`, `vb`/`vb.net→visual-basic-dotnet`, `ps→powershell`, `sh`/`shell→bash-shell` 등 12개) 는 [`references/languages/index.md`](references/languages/index.md) 참조.

## 지원 패턴 (547개, 55 카테고리)

GoF 23 + 아키텍처/분산/신뢰성/동시성/통합/DDD 전술·전략/데이터 접근/테스트/Observability/AI-LLM/배포/캐싱/안티패턴/모바일/임베디드/게임/네트워크/크로스플랫폼/Offline-First/에러 처리/API 설계·스타일/Web 렌더링/상태 관리/FP/Reactive/레거시 코드/워크플로우/스트리밍/데이터 모델링/UI-UX/FinOps/테스트 전략/빌드·버전/MLOps/DX/블록체인/요구공학/MDM/DQ 거버넌스/Web Performance/Data Warehousing & BI/도메인 5종.

**카테고리 진입점 + 547 패턴 ID → 파일 매핑**: [`references/patterns/index.md`](references/patterns/index.md) 참조.

**보안 영역(106개)은 4번째 도메인으로 분리**: [`references/security/index.md`](references/security/index.md) 참조.

## 워크플로우

dev-advisor 는 **7 모드** (5 기본 + 2 통합) + `--help` 로 동작한다. 자연어 트리거 또는 명시 호출(`/dev-advisor <mode>`) 로 라우팅된다. 5 카탈로그 lookup 은 별도 호출 (위 **## 호출 인터페이스 1. 카탈로그 lookup**) 로 보존된다.

### `--help` 출력

```
dev-advisor — 추천 / 검증 / 리팩토링 / 유지보수 / 보안 점검 / 통합(full) / 병렬(swarm) 어드바이저

사용법:
  /dev-advisor <mode> <input>     advisor 모드 명시 호출
  /dev-advisor --help             이 도움말

Advisor 모드 (옵션) — 5 기본 + 2 통합:
  recommend        추천 + 근거 (대안 trade-off, 표준 인용)
  validate         기존 코드/구조 검증 (SOLID/GRASP/DDD/Clean Arch/ISO 25010/12-Factor/OWASP/NIST)
  refactor         리팩토링 단계별 가이드 (Before/After + 회귀 위험)
  maintain         안티패턴/기술 부채 점검 (코드 스멜 5 그룹)
  security-audit   STRIDE / OWASP / NIST 보안 점검 (DREAD + 컴플라이언스)
  full             5 모드 순차 통합 보고 + 통합 우선순위 Top 10 + 단일 6 필드
  swarm            5 Codex 서브에이전트 병렬 → reviewer 통합 (OMX ultrawork) + Top 10

카탈로그 lookup (기존 보존):
  /pattern   <id|list|search>             547 패턴 (55 카테고리 — GoF + 아키텍처/분산/신뢰성/동시성/통합/DDD 전술·전략/데이터 접근/테스트/Observability/AI-LLM/배포/캐싱/안티패턴/모바일/임베디드/게임/네트워크/크로스플랫폼/Offline-First/에러 처리/API 설계·스타일/Web 렌더링/상태 관리/FP/Reactive/레거시 코드/워크플로우/스트리밍/데이터 모델링/UI-UX/FinOps/테스트 전략/빌드·버전/MLOps/DX/블록체인/요구공학/MDM/DQ 거버넌스/Web Performance/Data Warehousing & BI/Graphics Rendering/AR-VR-XR/Serverless-FaaS/HPC-Scientific/도메인 5종(Fintech·Healthcare·eCommerce·Logistics·IoT))
  /algorithm <id|list [category]|search>  273 알고리즘 (32 카테고리 — 정렬/탐색/그래프/DP/문자열/수학/자료구조/계산기하/플로우/매칭/암호/압축/게임AI/ML/확률/분산합의/분산알고/동시성/파싱 + DB 인덱스/DB 스토리지 엔진/DB 쿼리 옵티마이저/공간 인덱싱/검색·랭킹/부하 분산/OS 기초/이미지/신호/코덱)
  /language  <id|list|search>             75 언어
  /security  <id|list|search>             106 보안 항목 (15 파일 — 인증/인가/암호 운영/데이터 보호/API·Web/공급망/플랫폼/SDLC/탐지/모바일/AI 모델/Privacy Engineering/규제 컴플라이언스)
  /principle <id|list|search>             212 + 18 부록 SW 공학 원칙
                                          기본 5: SOLID 5 / GRASP 9 / ISO 25010 8 / 12-Factor 12 / Code Smells 22
                                          확장 10: Type Systems 10 / Concurrency Theory 10 / Refactoring Techniques 25 / SW Economics 10 / Evolutionary Arch 8 / Resilience Theory 8 / Documentation 8 / Process Metrics (DORA) 10 / Performance Metrics 10 / Sustainable SW (Green) 8
                                          P0 신설 4: Database Fundamentals 8 / SDLC Models 7 / Scaled Agile 6 / Professional Ethics 6
                                          P1 신설 2: Standards Mapping (SWEBOK/CS2023/DMBOK/OWASP/NIST-ISO) 5 / Configuration Management (IEEE 828) 6
                                          P3 신설 2: HCI Methodology (ISO 9241 / Persona / Journey Map / Heuristic Eval) 6 / Formal Methods (TLA+ / Alloy / Hoare / Model Checking) 5
                                          부록 18: DRY/KISS/YAGNI/LoD/SoC/Tell-Don't-Ask/Composition/SSoT + Conway/Inverse Conway/Hyrum/Postel/Brooks/Hollywood/Boy Scout/Pareto/Goodhart/Cunningham

라우팅 우선순위:
  카탈로그 ID 명시 발화 ("JWT 보안", "싱글톤 패턴", "SRP")            → 해당 도메인 lookup
  코드/모듈/API 입력 동반 발화 ("이 코드 검증", "이 API 보안 점검")    → advisor 모드
  의도 동사만 ("추천", "리팩토링", "기술 부채")                       → advisor 모드
  통합 키워드 ("전체 점검", "종합 분석", "모두 체크", "full audit")    → full
  병렬 키워드 ("병렬 점검", "심층 분석", "swarm", "ultra audit")       → swarm
  둘 다 모호                                                          → lookup 후 감사 범위 질문
```

### 7 모드 정의

| 모드 | 4단계 인풋 | 4단계 산출 | 인용 references |
|------|-----------|-----------|----------------|
| `recommend`      | 도메인 + 제약 (코드 선택)   | 후보 매트릭스 3~5행: ID / 적합 컨텍스트 / trade-off / score | [patterns/index.md](references/patterns/index.md), [algorithms/index.md](references/algorithms/index.md), [languages/index.md](references/languages/index.md), [principles/iso25010.md](references/principles/iso25010.md) (품질 특성 기준), [principles/grasp.md](references/principles/grasp.md) (책임 할당) |
| `validate`       | 코드/모듈 필수 | 위반 표: 위치 / 표준 / 심각도 P1/P2/P3 / 영향 / 조치 | [patterns/architectural.md](references/patterns/architectural.md), [patterns/ddd-tactical.md](references/patterns/ddd-tactical.md), [patterns/index.md](references/patterns/index.md), [security/index.md](references/security/index.md), [principles/solid.md](references/principles/solid.md) (5 원칙 anchor), [principles/grasp.md](references/principles/grasp.md) (9 원칙 anchor), [principles/iso25010.md](references/principles/iso25010.md) (8 품질 특성 anchor), [principles/12-factor.md](references/principles/12-factor.md) (12 인자 anchor) — 위반 항목별 specific anchor 권장 |
| `refactor`       | 코드/함수 필수 | 단계 표 + Before/After 코드 + 회귀 위험 등급 | [references/code_templates.md](references/code_templates.md), [patterns/architectural.md](references/patterns/architectural.md), [patterns/ddd-tactical.md](references/patterns/ddd-tactical.md), [principles/code-smells.md#5-그룹-진입점](references/principles/code-smells.md#5-그룹-진입점) (스멜 → 리팩토링), [principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙](references/principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙), [principles/solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙](references/principles/solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙) |
| `maintain`       | 모듈/프로젝트 필수 | 부채 표 7~10행 + 우선순위 (영향 × 발생빈도) + 코드 스멜 5 그룹 | [principles/code-smells.md#5-그룹-진입점](references/principles/code-smells.md#5-그룹-진입점) (22 스멜 5 그룹), [principles/iso25010.md#7-maintainability-유지보수성](references/principles/iso25010.md#7-maintainability-유지보수성), [principles/12-factor.md](references/principles/12-factor.md) (운영 부채), [patterns/index.md](references/patterns/index.md) (역방향 적합도) |
| `security-audit` | 모듈/API 필수 | STRIDE 6행 표 + DREAD 점수 + 대응책 + 컴플라이언스 | [security/security-sdlc.md](references/security/security-sdlc.md) (STRIDE/DREAD), [security/index.md](references/security/index.md) (표준 매트릭스), security 카테고리 7 파일 (`security-api-web`, `security-supply-chain`, `security-platform`, `security-sdlc`, `security-detect-respond`, `security-mobile`, `security-ai-model`), [principles/12-factor.md](references/principles/12-factor.md) (운영 보안) |
| `full`           | 모듈/path 필수 | 5 모드 sub-섹션 순차 + 통합 우선순위 Top 10 + 단일 6 필드 (5 모드 압축) | recommend / validate / refactor / maintain / security-audit 의 모든 references 통합 |
| `swarm`          | 모듈/path 필수 | 5 Codex 서브에이전트 병렬 결과 + reviewer 통합 보고 + Top 10 | OMX ultrawork + `spawn_agent` 기반 병렬 실행, verifier 또는 code-reviewer/security-reviewer/architect hand-off |

### 공통 6단계

모든 모드는 동일한 6단계를 따른다 (단계 명은 모드별 조정).

1. **입력 수집** — 위 표 "4단계 인풋" 컬럼의 필수 인자 확보
2. **컨텍스트 분류** — 언어 자동 감지, 프로젝트 규모, 스택 신호, 도메인 분류
3. **기준 매핑** — 위 표 "인용 references" 의 적용 가능 항목 식별
4. **분석/판정** — 위 표 "4단계 산출" 컬럼 형태로 산출물 작성
5. **근거 산출 (필수)** — 아래 6 필드 공통 템플릿 (모드별 alias 적용)
6. **검증/후속 계획** — 회귀 테스트 + 재검증 명령 + OMX 에이전트 hand-off 후보

### 5단계 "왜" 산출 — 6 필드 공통 템플릿 (필수)

모든 모드는 4단계 산출물 위에 다음 6 필드를 반드시 채워야 한다. 어느 하나라도 빠지면 응답 불완전으로 간주.

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호
- **대안 비교**: A vs B vs C 형태로 대안 2~3개 + 각 trade-off
- **표준 인용**: SOLID / GRASP / ISO 25010 / 12-Factor / DDD / Clean Architecture / OWASP / NIST / RFC 등 직접 anchor link
- **적용 조건**: 이 결정이 유효한 컨텍스트
- **6번째 필드 (모드별 alias)**:
  - `recommend` / `refactor` / `security-audit` → **비추천 조건** (이 패턴/리팩토링/통제를 안 써야 할 때)
  - `validate` → **예외·면제 조건** (표준 carve-out, compliance exception)
  - `maintain` → **수용 가능 조건** (이 부채를 그냥 두는 게 합리적일 때)

### 6단계 OMX 에이전트 hand-off 후보

모드별로 다음 후보 에이전트로 hand-off 검토 (트리거 조건 도달 시):

- 아키텍처 영향 ≥ 3 파일 / 계층 재설계 → `architect`
- 리팩토링 PR 검토 → `code-reviewer`
- 보안 통제 변경 / threat model 확정 → `security-reviewer`
- 변경 후 회귀 확인 → `verifier`
- 코드 스멜 deslop 정리 → `$ai-slop-cleaner` (`maintain` 모드 후속 스킬)

### maintain 모드 — 코드 스멜 5 그룹

22 스멜의 5 그룹 분류 (Bloaters / OO Abusers / Change Preventers / Dispensables / Couplers) + 식별 신호 + 권장 리팩토링은 [`references/principles/code-smells.md#5-그룹-진입점`](references/principles/code-smells.md#5-그룹-진입점) 참조.

### full 모드 절차 (순차 통합)

5 모드의 1~5단계를 직렬로 호출 후 단일 보고로 통합. 단일 컨텍스트 내 압축이라 토큰 한계가 명확 (1만~2만 × 5 = 5만~10만).

1. **입력 수집** — 단일 모듈/path. 여러 path 동시 입력 시 `swarm` 권장
2. **컨텍스트 분류** — 언어 자동 감지 + 프로젝트 규모 (LOC) + 스택 신호 + 도메인 분류. **공통 컨텍스트** 로 5 모드에 재사용 (중복 분석 방지)
3. **5 sub-모드 순차 호출** — `recommend → validate → security-audit → maintain → refactor` 순서로 각 모드의 1~5단계를 단축 실행 (refactor 는 validate/maintain 결과 의존이라 마지막)
4. **통합 분석** — 5 결과의 우선순위 매트릭스로 합산 (아래 **통합 우선순위 매트릭스** 참조). Top 10 추출
5. **근거 산출** — 5 모드의 6 필드를 통합 압축한 **단일 6 필드** 작성 (선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천·예외·수용 통합 조건)
6. **hand-off** — 가장 큰 위반 영역의 reviewer 분기 (보안 위반 우세 → `security-reviewer`, 아키텍처 영향 ≥ 3 파일 → `architect`, P1 ≥ 3 → `code-reviewer`)

**출력 스켈레톤**:

```
## Full Audit — <module|path>

### 1. recommend
<후보 매트릭스 3~5행 + trade-off>

### 2. validate
<위반 표 + P1/P2/P3>

### 3. security-audit
<STRIDE 6행 + DREAD>

### 4. maintain
<코드 스멜 5 그룹 + 부채 표>

### 5. refactor
<단계 표 + Before/After>

### 통합 우선순위 Top 10
| # | 항목 | 출처 모드 | 심각도 | 영향 | 즉시성 | 점수 |

### 통합 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천·예외·수용 통합 조건

### Hand-off
<우세 영역 → reviewer 분기>
```

### swarm 모드 절차 (병렬 ULW)

OMX ultrawork 기반 5 Codex 서브에이전트 병렬 위임 + reviewer 통합. 토큰 1만~2만 × 5 (병렬) + reviewer 5천 ≈ 6만~12만. ultrawork 또는 서브에이전트 사용이 불가한 환경에서는 `full` 로 fallback.

1. **입력 수집** — 모듈/path
2. **컨텍스트 분류** — 언어 자동 감지 + 규모 + 스택 + 도메인. 공통 컨텍스트를 5 서브에이전트에 공유 prompt 로 전달
3. **ULW 1차 발사** — `spawn_agent(agent_type="executor", message="...")` 형태로 독립 분석 5명을 병렬 호출 (각 모드 1명: recommend / validate / security-audit / maintain / refactor). Codex 역할 에이전트의 고정 모델 정책을 우선하며, 별도 모델 파라미터는 사용자가 명시한 경우에만 지정한다.
4. **결과 수집** — 5 보고를 모두 수집하고 중복 이슈·충돌 판정·P1 후보를 정규화
5. **Reviewer 통합** — 5 결과를 입력으로 reviewer 1명(`verifier` default, 옵션 `code-reviewer` / `security-reviewer` / `architect`)을 호출하거나 로컬 synthesis 로 통합한다. reviewer 는 P1/심각도/영향 비교 후 통합 Top 10 + 단일 6 필드를 산출한다.
6. **hand-off** — reviewer 판단에 따라 후속 에이전트 또는 스킬로 분기 (보안 위반 우세 → `security-reviewer`, 아키텍처 영향 → `architect`, PR 준비 → `code-reviewer`, 회귀 검증 → `verifier`, deslop → `$ai-slop-cleaner`)

**출력 스켈레톤**:

```
## Swarm Audit — <module|path>

### Parallel Results (5 Codex subagents)
<recommend / validate / security-audit / maintain / refactor 결과 5 개 sub-섹션>

### Reviewer Synthesis (<reviewer agent>)
#### 통합 우선순위 Top 10
| # | 항목 | 출처 모드 | 심각도 | 영향 | 즉시성 | 점수 |

#### 통합 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천·예외·수용 통합 조건

### Hand-off
<reviewer 결정 → 후속 에이전트>
```

### full / swarm 통합 우선순위 매트릭스

5 모드 결과를 단일 점수로 합산해 Top 10 추출.

| 컬럼 | 정의 | 가중치 |
|---|---|---|
| **심각도** | P1=3 / P2=2 / P3=1 (validate / security-audit), DREAD 8~10=3 / 5~7=2 / 1~4=1 | × 3 |
| **영향** | 영향 파일 수 ≥ 5=3 / 2~4=2 / 1=1 | × 2 |
| **즉시성** | runtime crash / 보안 침해 가능=3 / 유지보수 부담=2 / 스타일=1 | × 2 |
| **점수** | `심각도×3 + 영향×2 + 즉시성×2` (max 21) | — |

같은 항목이 여러 모드에서 검출되면 **출처 모드** 컬럼에 모두 표기 (예: `validate, security-audit`). 중복 항목은 단일 행으로 합산.

## OMX hand-off

advisor 7 모드의 트리거 조건 도달 시 Codex 전문 서브에이전트 또는 후속 OMX 스킬로 hand-off. 각 대상의 정식 입출력 계약·호출 형식은 [`references/handoff.md`](references/handoff.md) 참조.

| 대상 | 종류 | 트리거 | 후속 |
|---|---|---|---|
| `architect` | Codex subagent | `recommend` 결과 아키텍처 영향 ≥ 3 파일 / 계층 재설계 | `executor` 구현 |
| `code-reviewer` | Codex subagent | `refactor` 후 PR / `validate` P1 위반 수정 후 PR | `verifier` 회귀 |
| `security-reviewer` | Codex subagent | `security-audit` 결과 DREAD ≥ 8 / 컴플라이언스 carve-out / threat model 신규 | `verifier` + `code-reviewer` |
| `verifier` | Codex subagent | `refactor` / `maintain` / `security-audit` 적용 후, autopilot 종료 직전 | 통과 → 종료, 실패 → 재실행 |
| `$ai-slop-cleaner` | OMX skill | `maintain` Dispensables 그룹 비중 ≥ 40% | `code-reviewer` PR 리뷰 |

호출 형식 + 모델 정책은 AGENTS.md OMX/ULW 분석·설계 모델 정책 + `references/handoff.md` 참조.

## 언어 자동 감지

프로젝트 파일 패턴 (Kotlin/Java/Swift/Python/JS/TS/Go/Rust/C++/C#/Ruby/PHP/Scala 13 패턴) + 다중 언어 우선순위는 [`references/languages/index.md#언어-자동-감지`](references/languages/index.md#언어-자동-감지) 참조.

## 참조 문서

5 도메인 진입점 (항목 수·구조·용도는 위 **## 데이터 기반 — 5중 카탈로그** 표 참조):

- 패턴 (547) — [`references/patterns/index.md`](references/patterns/index.md)
- 알고리즘 (273) — [`references/algorithms/index.md`](references/algorithms/index.md)
- 언어 (75) — [`references/languages/index.md`](references/languages/index.md) · 분야별: [`domains.md`](references/languages/domains.md)
- 보안 (106) — [`references/security/index.md`](references/security/index.md)
- 원칙 (212 + 18 부록) — [`references/principles/index.md`](references/principles/index.md) · 미시 부록: [`micro-principles.md`](references/principles/micro-principles.md)

부가 자산:
- [`references/code_templates.md`](references/code_templates.md) — 자동 코드 생성 4 언어 템플릿 (Kotlin/Java/Swift/Python)
- [`references/output_templates.md`](references/output_templates.md) — advisor 7 모드 산출물 마크다운 스켈레톤
- [`references/examples.md`](references/examples.md) — advisor 7 모드 + 카탈로그 lookup 실제 호출/응답 8 예시 (A~H)
- [`references/handoff.md`](references/handoff.md) — OMX hand-off 상세 (architect/code-reviewer/security-reviewer/verifier + `$ai-slop-cleaner`) 정식 입출력 계약

### 무결성 검증

새 항목 추가 후 `bash scripts/verify-references.sh` 실행. 5 도메인 동기화 검증 (anchor / 목차 / index.md / SKILL.md 카운트 / 핵심 문서 Markdown 링크).

## 예시

각 advisor 모드 + 카탈로그 lookup 의 실제 호출/응답 8 예시는 [`references/examples.md`](references/examples.md) 참조.

- **A.** 카탈로그 lookup — Singleton 패턴 호출
- **B.** `recommend` 모드 — 결제 시스템 아키텍처 추천 (Strategy + Factory Method)
- **C.** `validate` 모드 — SOLID 위반 검증 (OrderProcessor.kt SRP/DIP 위반)
- **D.** `refactor` 모드 — God Class 분해 (PricingCalculator / InventoryService / OrderNotifier)
- **E.** `maintain` 모드 — 기술 부채 점검 (UserService.kt 5 그룹 분포)
- **F.** `security-audit` 모드 — 결제 API STRIDE / DREAD / PCI-DSS 매핑
- **G.** `full` 모드 — 5 모드 순차 통합 점검
- **H.** `swarm` 모드 — 동일 모듈 병렬 심층 분석
