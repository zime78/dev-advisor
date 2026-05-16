# dev-advisor

`dev-advisor`는 앱 개발 과정에서 아키텍처, 알고리즘, 언어 선택, 보안, 소프트웨어 공학 원칙, QA/QC 품질 활동을 한 번에 참조할 수 있도록 정리한 멀티 에이전트용 개발 어드바이저 카탈로그입니다. 현재 저장소는 Codex용 스킬과 Claude용 스킬을 함께 제공하며, 두 환경에서 같은 개발 판단 기준을 재사용할 수 있도록 구성되어 있습니다.

## 설치 방법

가장 먼저 아래 설치 절차를 진행하면 됩니다. 자동 설치 스크립트는 Codex와 Claude Code 설치 여부를 확인한 뒤, 사용 가능한 환경에 `dev-advisor` 스킬을 복사합니다.

### 자동 설치

Codex 또는 Claude Code가 설치되어 있으면 아래 스크립트가 자동으로 감지해 `dev-advisor` 스킬을 각 홈 디렉터리로 복사합니다. 기존 스킬이 있으면 덮어쓰기 전에 `.backups/` 아래로 백업합니다.

```bash
git clone https://github.com/zime78/dev-advisor.git
cd dev-advisor
bash scripts/install-skills.sh
```

| 설치 대상 | 감지 기준 | 복사 위치 | 원본 경로 |
|---|---|---|---|
| Codex | `~/.codex` 존재 또는 `codex` 명령 존재 | `~/.codex/skills/dev-advisor` | `codex/skills/dev-advisor` |
| Claude Code | `~/.claude` 존재 또는 `claude` 명령 존재 | `~/.claude/skills/dev-advisor` | `claude/skills/dev-advisor` |

| 설치 옵션 | 명령 | 설명 |
|---|---|---|
| 전체 자동 설치 | `bash scripts/install-skills.sh` | Codex와 Claude Code를 감지해 가능한 대상에 모두 설치 |
| 설치 전 확인 | `bash scripts/install-skills.sh --dry-run` | 복사하지 않고 대상 경로와 백업 경로만 확인 |
| Codex만 설치 | `bash scripts/install-skills.sh --only codex` | Codex 스킬만 설치 |
| Claude Code만 설치 | `bash scripts/install-skills.sh --only claude` | Claude Code 스킬만 설치 |
| 설치 위치 변경 | `CODEX_HOME=/path/to/codex bash scripts/install-skills.sh --only codex` | 기본 홈 디렉터리 대신 지정 경로에 설치 |

### 수동 설치

자동 설치 대신 직접 복사할 수도 있습니다.

```bash
mkdir -p ~/.codex/skills ~/.claude/skills
cp -R codex/skills/dev-advisor ~/.codex/skills/dev-advisor
cp -R claude/skills/dev-advisor ~/.claude/skills/dev-advisor
```

## 스킬 옵션

| 구분 | 옵션 / 명령 | 입력 | 출력 |
|---|---|---|---|
| 도움말 | `/dev-advisor --help` | 없음 | 모드, 카탈로그, 라우팅 사용법 |
| 추천 | `/dev-advisor recommend <context>` | 만들 앱, 도메인, 제약 조건 | 후보 매트릭스, 선택 근거, 대안 비교 |
| 검증 | `/dev-advisor validate <file\|module>` | 코드, 모듈, 파일 경로 | 위반 항목, 표준 인용, P1/P2/P3 우선순위 |
| 리팩토링 | `/dev-advisor refactor <file\|function>` | 코드, 함수, 클래스 | 단계별 리팩토링, Before/After, 회귀 위험 |
| 유지보수 | `/dev-advisor maintain <module\|project>` | 모듈, 프로젝트 구조 | 기술 부채, 코드 스멜, 우선순위 |
| 보안 점검 | `/dev-advisor security-audit <module\|api>` | API, 모듈, 인증/인가 흐름 | STRIDE, DREAD, 통제 방안, 컴플라이언스 매핑 |
| QA 점검 | `/dev-advisor qa <module\|path>` | 요구사항, 모듈, 릴리즈 범위 | 요구사항 추적성, 테스트 전략, 릴리즈 준비도 |
| QC 검증 | `/dev-advisor qc <module\|path>` | 빌드, 테스트 리포트, 배포 후보 | 테스트 실행 증거, 품질 게이트, 결함 재현 |
| 전체 점검 | `/dev-advisor full <module\|path>` | 모듈, 경로, 프로젝트 | 7 기본 모드 순차 통합 보고서 |
| 병렬 심층 점검 | `/dev-advisor swarm <module\|path>` | 큰 모듈, 복합 프로젝트 | 다중 에이전트 병렬 분석과 reviewer 통합 |

| 카탈로그 | 명령 형식 | 예시 | 용도 |
|---|---|---|---|
| Patterns | `/pattern <id\|list\|search>` | `/pattern singleton`, `/pattern search 캐싱` | 디자인/아키텍처 패턴 조회 |
| Algorithms | `/algorithm <id\|list [category]\|search>` | `/algorithm quick-sort`, `/algorithm list graph` | 알고리즘/자료구조 조회 |
| Languages | `/language <id\|list\|search>` | `/language python`, `/language search 모바일` | 언어 선택/비교 조회 |
| Security | `/security <id\|list\|search>` | `/security oauth2-pkce`, `/security jwt` | 보안 패턴/통제 조회 |
| Principles | `/principle <id\|list\|search>` | `/principle srp`, `/principle dry` | SW 공학 원칙 조회 |
| Quality | `/quality <id\|list\|search>` | `/quality qa-test-strategy`, `/quality qc-quality-gate` | QA/QC 품질 활동 조회 |

## 사용 방법

`dev-advisor`는 크게 두 방식으로 사용합니다. 특정 개념을 바로 찾아보려면 카탈로그 조회 명령을 쓰고, 코드나 프로젝트를 평가받으려면 advisor 모드를 씁니다.

### 1. 카탈로그에서 바로 찾아보기

| 사용 목적 | 입력 예시 | 기대 결과 |
|---|---|---|
| 패턴 하나를 알고 싶을 때 | `/pattern singleton` | Singleton 패턴의 목적, 적용 조건, 장단점, 비추천 조건 |
| 관련 패턴을 검색할 때 | `/pattern search 캐싱` | 캐싱 관련 패턴 후보 목록과 각 항목의 쓰임 |
| 알고리즘을 확인할 때 | `/algorithm dijkstra` | Dijkstra 알고리즘 설명, 사용 조건, 복잡도, 적용 예 |
| 알고리즘 카테고리를 볼 때 | `/algorithm list graph` | 그래프 알고리즘 목록 |
| 언어 선택 기준을 볼 때 | `/language kotlin` | Kotlin의 사용처, 장점, 제약, 추천 상황 |
| 특정 분야 언어를 찾을 때 | `/language search 모바일` | 모바일 개발에 관련된 언어 후보 |
| 보안 통제를 찾을 때 | `/security oauth2-pkce` | OAuth2 + PKCE의 목적, 적용 조건, 주의점 |
| 원칙을 찾을 때 | `/principle srp` | 단일 책임 원칙 설명, 위반 신호, 리팩토링 방향 |
| QA/QC 기준을 찾을 때 | `/quality qc-quality-gate` | 품질 게이트의 입력 증거, 판정 기준, 실패 시 조치 |

### 2. 프로젝트나 코드를 분석시키기

| 사용 목적 | 입력 예시 | 기대 결과 |
|---|---|---|
| 아키텍처 추천 | `/dev-advisor recommend 실시간 채팅 앱을 만들 예정이고 모바일과 웹을 모두 지원해야 함` | 후보 아키텍처, 추천 이유, 대안 비교, 적용 조건 |
| 코드 구조 검증 | `/dev-advisor validate src/modules/payment` | 위반 가능성이 있는 설계 원칙, 심각도, 수정 우선순위 |
| 리팩토링 가이드 | `/dev-advisor refactor src/services/UserService.ts` | 단계별 리팩토링 계획, Before/After 방향, 회귀 위험 |
| 유지보수 점검 | `/dev-advisor maintain backend/` | 기술 부채, 코드 스멜, 운영 리스크, 개선 우선순위 |
| 보안 점검 | `/dev-advisor security-audit api/auth` | STRIDE/DREAD 기반 위협, 보안 통제, 컴플라이언스 매핑 |
| QA 점검 | `/dev-advisor qa src/checkout` | 요구사항 추적성, 테스트 전략, 릴리즈 준비도 |
| QC 검증 | `/dev-advisor qc src/checkout` | 빌드/테스트 실행 증거, 품질 게이트, 릴리즈 차단 여부 |
| 전체 점검 | `/dev-advisor full src/checkout` | 추천, 검증, 리팩토링, 유지보수, 보안, QA, QC를 순차 통합 |
| 병렬 심층 점검 | `/dev-advisor swarm src/checkout` | 여러 관점의 병렬 분석 결과와 통합 Top 10 개선안 |

### 3. 자연어로도 요청하기

명령어를 정확히 몰라도 자연어 요청이 가능합니다. 명시적인 ID나 파일 경로가 있으면 해당 카탈로그 또는 advisor 모드로 자동 라우팅합니다.

| 자연어 입력 예시 | 자동 해석 |
|---|---|
| `싱글톤 패턴 설명해줘` | `/pattern singleton` |
| `JWT 보안에서 주의할 점 알려줘` | `/security jwt` 또는 관련 보안 항목 검색 |
| `이 결제 모듈 전체 점검해줘: src/payment` | `/dev-advisor full src/payment` |
| `이 API 보안 점검해줘: api/login` | `/dev-advisor security-audit api/login` |
| `Python이 이 프로젝트에 맞는지 검토해줘` | `/language python` + `recommend` 관점 |
| `이 코드 SOLID 위반인지 봐줘` | `/dev-advisor validate <제공된 코드>` |
| `기술 부채 높은 부분부터 정리해줘` | `/dev-advisor maintain <project>` |
| `릴리즈 전에 QA 점검해줘: src/checkout` | `/dev-advisor qa src/checkout` |
| `품질 게이트 통과했는지 QC 검증해줘` | `/dev-advisor qc <module>` |
| `큰 모듈이라 병렬로 심층 분석해줘` | `/dev-advisor swarm <module>` |

### 4. 추천 사용 흐름

| 상황 | 추천 순서 |
|---|---|
| 새 기능 설계 전 | `/dev-advisor recommend` → 후보 비교 → `/pattern <id>`로 세부 확인 |
| 기존 코드 품질 확인 | `/dev-advisor validate` → 위반 항목 확인 → `/dev-advisor refactor` |
| 배포 전 보안 점검 | `/dev-advisor security-audit` → 취약점 조치 → 재검증 |
| 릴리즈 전 품질 승인 | `/dev-advisor qa` → 추적성/전략 gap 보완 → `/dev-advisor qc` |
| 레거시 모듈 개선 | `/dev-advisor maintain` → 부채 우선순위 결정 → 단계별 리팩토링 |
| 큰 프로젝트 종합 점검 | `/dev-advisor full` 또는 `/dev-advisor swarm` → Top 10 개선안 실행 |

### 4.1 개발 라이프사이클 라우팅

`dev-advisor`는 advisor 모드를 9개로 유지하면서, 개발 생명주기 질문은 아래 보조 라우팅으로 9모드와 카탈로그를 조합합니다.

| 라우트 | 범위 | 기본 동작 |
|---|---|---|
| `lifecycle` | Discovery → Requirements → Design → Build → Test → Release → Operate → Improve | 단계 식별 후 필요한 advisor 모드로 분기 |
| `requirements` | PRD, user story, NFR, acceptance criteria, traceability, scope/risk | `qa` + 요구공학/SDLC 카탈로그 |
| `release` | rollout, migration, rollback, hotfix, release note, go/no-go | `qa` + `qc` + 배포/형상관리 카탈로그 |
| `ops` / `sre` | SLO, alert, runbook, on-call, incident, postmortem, capacity, DR | `maintain` + `qc` + 관측성/회복성 카탈로그 |
| `ecosystem/current-docs` | framework, SDK, cloud, library, CLI, 버전 마이그레이션 | 최신 공식 문서 조회로 라우팅하고, dev-advisor 카탈로그는 안정적 판단 원칙 보조 근거로만 사용 |

### 5. 출력 결과를 읽는 기준

| 출력 항목 | 의미 |
|---|---|
| 선택/판정 | 현재 입력에 대한 핵심 결론 |
| 근거 | 왜 그렇게 판단했는지에 대한 코드/구조/표준 기반 이유 |
| 대안 비교 | 다른 선택지와 trade-off |
| 표준 인용 | SOLID, GRASP, ISO 25010, 12-Factor, OWASP, NIST, RFC 등 관련 기준 |
| 적용 조건 | 해당 판단이 유효한 상황 |
| 비추천/예외/수용 조건 | 이 결정을 쓰지 않거나 예외로 둘 수 있는 조건 |

## 1. 해당 프로젝트를 만든 이유

| 항목 | 설명 |
|---|---|
| 문제 상황 | 앱을 만들 때 디자인 패턴, 알고리즘, 언어 선택, 보안 통제, 유지보수 원칙이 서로 다른 문서와 경험에 흩어져 있어 의사결정 기준이 흔들리기 쉽습니다. |
| 목표 | 반복되는 개발 판단을 카탈로그화하여 추천, 검증, 리팩토링, 유지보수, 보안 점검을 일관된 방식으로 수행하도록 돕습니다. |
| 핵심 방향 | "무엇을 선택할지"뿐 아니라 "왜 선택하는지", "언제 쓰면 안 되는지", "어떤 표준과 연결되는지"까지 함께 제시합니다. |
| 사용 대상 | Codex, Claude 같은 코딩 에이전트와 함께 앱 개발, 코드 리뷰, 설계 검토, 보안 점검, 기술 부채 점검을 수행하는 개발자입니다. |
| 운영 형태 | `SKILL.md`를 진입점으로 삼고, `references/` 아래의 도메인별 Markdown 카탈로그를 필요할 때 점진적으로 참조합니다. |

## 2. 프로젝트 내 포함된 내용 정리

### 2.1 전체 구성 요약

| 구분 | 경로 | 파일 수 | 역할 | 비고 |
|---|---:|---:|---|---|
| Git 제외 규칙 | `.gitignore` | 1 | 로컬 상태, 캐시, 비밀 파일 제외 | `.omx/`, `.DS_Store`, `.env*`, Python 캐시 제외 |
| Claude 스킬 | `claude/skills/dev-advisor/` | 204 | Claude 환경에서 사용할 dev-advisor 스킬 패키지 | `SKILL.md`, `references/`, `scripts/` 포함 |
| Codex 스킬 | `codex/skills/dev-advisor/` | 202 | Codex 환경에서 사용할 dev-advisor 스킬 패키지 | `agents/openai.yaml` 포함 |
| 루트 문서 | `README.md` | 1 | 프로젝트 개요, 구성, 출처 정리 | 현재 문서 |
| 설치 스크립트 | `scripts/install-skills.sh` | 1 | Codex/Claude Code 스킬 자동 설치 | 기존 설치본은 `.backups/`로 백업 |
| 로컬 런타임 | `.omx/` | 추적 제외 | oh-my-codex 실행 상태와 로그 | 저장소에는 포함하지 않음 |
| macOS 메타파일 | `.DS_Store` | 추적 제외 | Finder 로컬 메타데이터 | 저장소에는 포함하지 않음 |

### 2.2 스킬 패키지 구성

| 구분 | Claude 경로 | Codex 경로 | 포함 내용 | 사용 목적 |
|---|---|---|---|---|
| 스킬 진입점 | `claude/skills/dev-advisor/SKILL.md` | `codex/skills/dev-advisor/SKILL.md` | 목적, 호출 인터페이스, 라우팅, 9개 advisor 모드 | 에이전트가 어떤 기준으로 dev-advisor를 호출할지 정의 |
| 참조 카탈로그 | `claude/skills/dev-advisor/references/` | `codex/skills/dev-advisor/references/` | 패턴, 알고리즘, 언어, 보안, 원칙 문서 | 실제 판단 근거와 lookup 데이터 저장 |
| 검증 스크립트 | `claude/skills/dev-advisor/scripts/` | `codex/skills/dev-advisor/scripts/` | anchor, 링크, 카운트, 품질 게이트 검증 | 카탈로그 무결성 확인 |
| 에이전트 설정 | 없음 | `codex/skills/dev-advisor/agents/openai.yaml` | Codex 에이전트 설정 | Codex 환경 전용 설정 |

### 2.3 Advisor 모드

| 번호 | 모드 | 자연어 트리거 | 주요 산출물 | 연결 도메인 |
|---:|---|---|---|---|
| 1 | `recommend` | 추천, 아키텍처 추천 | 후보 매트릭스, 선택 근거, 대안 trade-off | Patterns, Algorithms, Languages, Principles |
| 2 | `validate` | 검증, 체크, 맞아? | 위반 항목 표, 표준 인용, P1/P2/P3 우선순위 | Patterns, Security, Principles |
| 3 | `refactor` | 리팩토링, Before/After | 단계 표, Before/After 코드, 회귀 위험 | Patterns, Code Templates, Principles |
| 4 | `maintain` | 유지보수, 기술 부채 | 코드 스멜, 부채 표, 영향도 우선순위 | Principles, Patterns |
| 5 | `security-audit` | 보안 점검, 취약점 | STRIDE, DREAD, 컴플라이언스 매핑 | Security, Principles |
| 6 | `qa` | QA 점검, 품질 보증, 테스트 전략 | 요구사항 추적성, 테스트 전략, 릴리즈 승인 | Quality, Principles |
| 7 | `qc` | QC 검증, 품질 게이트, 테스트 실행 | 빌드/테스트 증거, 결함 재현, 품질 게이트 | Quality, Patterns, Principles |
| 8 | `full` | 전체 점검, 종합 분석 | 7 기본 모드 순차 통합 보고서 | 전체 도메인 |
| 9 | `swarm` | 병렬 점검, 심층 분석, swarm | 다중 에이전트 병렬 분석과 reviewer 통합 | 전체 도메인, OMX ultrawork |

### 2.4 카탈로그 도메인

| 도메인 | 경로 | 항목 수 | 내부 파일 수 | 주요 내용 | 대표 호출 |
|---|---|---:|---:|---|---|
| Patterns | `references/patterns/` | 547 | 56 | GoF, 아키텍처, 분산, 신뢰성, 동시성, 통합, DDD, 테스트, Observability, AI/LLM, 배포, 캐싱, 모바일, 도메인 패턴 등 | `/pattern singleton`, `/pattern list` |
| Algorithms | `references/algorithms/` | 273 | 33 | 정렬, 탐색, 그래프, DP, 문자열, 수학, 자료구조, DB 인덱스, OS, 검색, 이미지, 신호, 코덱 등 | `/algorithm quick-sort`, `/algorithm list graph` |
| Languages | `references/languages/` | 75 | 77 | 언어별 사용처, 특징, 장점, 제약, 예제, 분야별 추천 | `/language python`, `/language search 웹` |
| Security | `references/security/` | 106 | 15 | 인증, 인가, 암호 운영, 데이터 보호, API/Web, 공급망, 플랫폼, SDLC, 탐지, 모바일, AI 모델, 개인정보, 컴플라이언스 | `/security oauth2-pkce`, `/security jwt` |
| Principles | `references/principles/` | 212 + 18 부록 | 25 | SOLID, GRASP, ISO 25010, 12-Factor, Code Smells, 타입 시스템, 동시성 이론, 리팩토링, SW 경제, 성능, 지속가능성 등 | `/principle srp`, `/principle dry` |
| Quality | `references/quality/` | 20 | 3 | QA 요구사항 추적성/테스트 전략/릴리즈 승인 + QC 빌드 검증/테스트 실행 증거/품질 게이트 | `/quality qa-test-strategy`, `/quality qc-quality-gate` |
| 보조 문서 | `references/*.md` | 6 | 6 | 코드 템플릿, 예시, handoff, 출력 템플릿, references 디렉토리 가이드 | 스킬 내부 참조 |

### 2.5 도메인별 세부 항목

| 도메인 | 세부 구분 | 포함 범위 |
|---|---|---|
| Patterns | 기본/아키텍처 | Creational, Structural, Behavioral, Architectural, Distributed, Reliability, Concurrency, Integration |
| Patterns | 확장/운영 | Deployment, Caching, Observability, Testing, Testing Strategies, Build/Versioning, Workflow Jobs, MLOps, DX Engineering |
| Patterns | 제품/플랫폼 | Mobile App, Embedded, Game Dev, Networking, Crossplatform, Offline-First, Web Rendering, State Management |
| Patterns | 설계/도메인 | DDD Tactical, DDD Strategic, Data Access, Data Modeling, API Design, API Styles, UI/UX, Requirements Engineering |
| Patterns | 산업 도메인 | Fintech, Healthcare, eCommerce, Logistics, IoT Edge |
| Algorithms | 기초 알고리즘 | Sorting, Searching, Graph, Dynamic Programming, Divide and Conquer, Greedy, Backtracking |
| Algorithms | 자료/문자/수학 | String, Math, Data Structures, Geometry, Flow, Matching |
| Algorithms | 시스템/분산 | Consensus, Distributed, Concurrent, Parsing, OS Foundations, Load Balancing |
| Algorithms | 데이터/미디어 | DB Indexes, DB Storage Engines, Spatial, Search Systems, Image Processing, Signal Processing, Codecs |
| Languages | 언어 참조 | 75개 언어별 사용처, 특징, 장점, 제약, 예제, 관련 문서 |
| Languages | 자동 감지 | Kotlin, Java, Swift, Python, JavaScript, TypeScript, Go, Rust, C++, C#, Ruby, PHP, Scala |
| Languages | 코드 생성 | Kotlin, Java, Swift, Python 중심 코드 템플릿 |
| Security | 애플리케이션 보안 | AuthN, AuthZ, API/Web, Mobile, AI Model, Data Protection |
| Security | 운영/조직 보안 | Crypto Ops, Supply Chain, Platform, SDLC, Detect/Respond, Privacy Engineering, Compliance |
| Principles | 핵심 원칙 | SOLID, GRASP, ISO 25010, 12-Factor, Code Smells |
| Principles | 확장 원칙 | Type Systems, Concurrency Theory, Refactoring Techniques, SW Economics, Evolutionary Architecture, Resilience, Documentation, Process Metrics, Performance Metrics, Sustainable Software |
| Principles | 미시 원칙 부록 | DRY, KISS, YAGNI, Law of Demeter, Separation of Concerns, Tell Don't Ask, Composition over Inheritance, Single Source of Truth, Conway's Law, Hyrum's Law 등 |
| Quality | QA | Requirements Traceability, Test Strategy, Risk-Based Testing, Acceptance Criteria Review, Test Plan Review, Release Readiness, Defect Triage, Change Impact, Regression Scope, Compliance Evidence Plan |
| Quality | QC | Build Verification, Test Execution Evidence, Functional/Nonfunctional Verification, Regression Result, Defect Reproduction, Quality Gate, Release Blocker, Data Integrity, Post-Release Smoke |

### 2.6 보조 파일과 스크립트

| 파일 | 경로 | 역할 |
|---|---|---|
| Reference guide | `references/README.md` | `references/` 내부 링크 규약과 분할 매핑 설명 |
| Code templates | `references/code_templates.md` | 언어별 코드 템플릿과 패턴 예시 |
| Examples | `references/examples.md` | advisor 호출 예시와 사용 시나리오 |
| Handoff | `references/handoff.md` | 에이전트 hand-off 기준과 협업 계약 |
| Output templates | `references/output_templates.md` | advisor 모드별 출력 스켈레톤 |
| Enrich languages | `scripts/enrich-languages.py` | 언어 reference 확장/보강용 스크립트 |
| Verify references | `scripts/verify-references.sh` | 전체 카탈로그, 링크, anchor, 카운트 검증 |
| Verify anchors | `scripts/verify-anchors.sh` | deprecated wrapper, `verify-references.sh`로 위임 |
| Skill installer | `scripts/install-skills.sh` | 루트 자동 설치 스크립트. Codex/Claude Code 설치 여부를 감지해 스킬을 복사 |

### 2.7 전체 세부 항목 인벤토리

아래 표는 각 reference 파일의 실제 세부 항목을 전부 펼친 인벤토리입니다. 항목명은 각 파일의 `## N.` 제목 기준이며, 긴 항목은 같은 칸에서 줄바꿈으로 구분합니다.

#### Patterns 전체 항목

| 파일 | 항목 수 | 전체 서브 항목 |
|---|---:|---|
| `patterns/creational.md` | 5 | Singleton, Factory Method, Abstract Factory, Builder, Prototype |
| `patterns/structural.md` | 7 | Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy |
| `patterns/behavioral.md` | 11 | Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor, Interpreter |
| `patterns/architectural.md` | 16 | MVC, MVP, MVVM, MVI, MVVM-C, VIPER, Flux / Redux, Layered Architecture, Clean Architecture, Hexagonal Architecture, Onion Architecture, Modular Monolith, Microservices, SOA, Event-Driven Architecture, Serverless Architecture |
| `patterns/distributed.md` | 9 | CQRS, Event Sourcing, Saga Choreography, Saga Orchestration, Outbox Pattern, Idempotency Key, BFF, API Gateway, Service Mesh |
| `patterns/reliability.md` | 9 | Circuit Breaker, Retry, Bulkhead, Timeout, Rate Limiter, Backpressure, Health Check, Sidecar, Ambassador |
| `patterns/concurrency.md` | 14 | Active Object, Monitor Object, Thread Pool, Producer-Consumer, Reactor, Proactor, Read-Write Lock, Double-Checked Locking, Future / Promise, Actor Model, CSP, STM, Fork-Join, Structured Concurrency |
| `patterns/integration.md` | 16 | Pipes & Filters, Publish-Subscribe, Message Broker, Aggregator, Splitter, Content-Based Router, Message Translator, Dead Letter Queue, Competing Consumers, Wire Tap, Claim Check, Resequencer, Scatter-Gather, Process Manager, Normalizer, Routing Slip |
| `patterns/ddd-tactical.md` | 11 | Entity, Value Object, Aggregate, Domain Event, Domain Service, Specification, Anti-Corruption Layer, Bounded Context, Context Map, Factory, Repository |
| `patterns/data-access.md` | 10 | Repository, Unit of Work, Active Record, Data Mapper, Identity Map, Lazy Load, Query Object, Specification, Table Module, Row Data Gateway |
| `patterns/testing.md` | 11 | Test Pyramid, AAA, Given-When-Then, Test Double, Property-Based Test, Contract Test, Snapshot Test, Mutation Test, Test Fixture, Object Mother / Test Data Builder, Page Object |
| `patterns/observability.md` | 10 | Three Pillars, Distributed Tracing, Correlation ID, Structured Logging, RED Method, USE Method, Golden Signals, SLO / Error Budget, Health Endpoint Monitoring, Audit Trail |
| `patterns/ai-llm.md` | 12 | RAG, Tool Use, Agent Loop, Multi-Agent Orchestration, Prompt Template, Few-Shot Prompting, Self-Critique / Self-Refine, Memory, Guardrails, Evaluator-Optimizer, Context Compaction, Human-in-the-Loop |
| `patterns/deployment.md` | 9 | Blue-Green Deployment, Canary Release, Rolling Update, Shadow Deployment, Feature Flag, Dark Launch, Strangler Fig, Branch by Abstraction, Expand-Contract Migration |
| `patterns/caching.md` | 9 | Cache-Aside, Read-Through, Write-Through, Write-Behind, Refresh-Ahead, Cache Stampede 방지, TTL / LRU / LFU 정책, Negative Caching, Multi-Tier Cache |
| `patterns/anti-patterns.md` | 18 | Big Ball of Mud, God Object / God Class, Anemic Domain Model, Distributed Monolith, Lava Flow, Golden Hammer, Cargo Cult Programming, Vendor Lock-in / Magic Pushbutton, Spaghetti Code, Magic Numbers / Magic Strings, Boat Anchor, Premature Optimization, Reinventing the Wheel / Not Invented Here, Yo-Yo Problem, Copy-Paste Programming, Hard Coding, Sequential Coupling / Temporal Coupling, Stovepipe System |
| `patterns/error-handling.md` | 11 | Exception, Error Code / Sentinel Value, Result / Either, Railway-Oriented Programming, Option / Maybe, Fail-Fast vs Fail-Safe, Compensating Transaction, Error Aggregation / Multi-Error, Panic / Recover, Defensive Copying / Boundary Validation, Retry with Exponential Backoff + Circuit Breaker |
| `patterns/legacy-code.md` | 10 | Seam, Characterization Test, Sprout Method / Sprout Class, Wrap Method / Wrap Class, Sensing Variable, Extract Interface, Extract and Override, Subclass and Override Method, Break Out Method Object, Mikado Method |
| `patterns/requirements-engineering.md` | 10 | User Story, INVEST 원칙, MoSCoW Prioritization, Use Case, Job Stories, Event Storming, Example Mapping, Gherkin / Given-When-Then, Impact Mapping, Three Amigos |
| `patterns/finops.md` | 8 | Unit Economics, Rightsizing, Reserved / Savings Plans / Commitment, Spot / Preemptible Instances, Autoscaling Cost Optimization, Tagging & Cost Allocation, FinOps Lifecycle, Budget Guardrails & Anomaly Detection |
| `patterns/dx-engineering.md` | 8 | Scaffolding, Code Generation, Language Server Protocol, Devcontainer / Dev Environment as Code, REPL / Notebook, Hot Reload / Fast Refresh, DevTools / Observability for Developers, Internal Developer Portal |
| `patterns/mobile-app.md` | 13 | App Lifecycle State Machine, Background Task, Push Notification Topology, Deep Link / Universal Link / App Link, Navigation Pattern, App Cold/Warm/Hot Start 최적화, Crash & ANR Handling, In-App Purchase / Subscription, OTA Update / Code Push, App Signing & Distribution, App Size 최적화, Permission Request UX, Battery & Performance Profiling |
| `patterns/embedded.md` | 10 | Rate Monotonic Scheduling, Earliest Deadline First, Worst-Case Execution Time, Time-Triggered Architecture, Interrupt Service Routine, DMA Buffer, Watchdog Timer, Ring Buffer / Circular Buffer, Memory Pool / Static Allocation, State Machine |
| `patterns/game-dev.md` | 12 | Game Loop, Entity-Component-System, Component Pattern, Object Pool, Spatial Partition, Scene Graph, State Machine for AI, Dirty Flag, Double Buffer, Game Netcode, Save System / Serialization, Asset Pipeline |
| `patterns/networking.md` | 12 | TCP vs UDP, TCP Congestion Control, QUIC / HTTP/3, HTTP/1.1 vs HTTP/2 vs HTTP/3, TLS Handshake, DNS Patterns, CDN / Edge Patterns, NAT Traversal, WebSocket Protocol, WebRTC, Reliable UDP / KCP / RUDP, Connection Pooling & Keep-Alive |
| `patterns/crossplatform.md` | 10 | Flutter State Management, Flutter Platform Channel, React Native Bridge / New Architecture, Kotlin Multiplatform expect / actual, Expo / EAS, Capacitor, Tauri vs Electron, Compose Multiplatform, SwiftUI / Compose Interop, Hot Reload / Fast Refresh |
| `patterns/offline-first.md` | 8 | Local-First Database, Sync Queue / Outbox, Conflict Resolution, Tombstone Pattern, Delta Sync, Conflict UI Pattern, Optimistic UI with Rollback, Network State Detection |
| `patterns/web-rendering.md` | 10 | CSR, SSR, SSG, ISR, Streaming SSR, Islands Architecture, React Server Components, Hydration, Resumability, Edge Rendering |
| `patterns/state-management.md` | 9 | Single Store, Feature Slice / Multiple Store, Atomic State, Signal-Based, Server State, Form State, URL / Routing State, CRDT-based Collaborative State, Optimistic UI Update |
| `patterns/ui-ux.md` | 11 | Atomic Design, Container / Presenter, Skeleton Screen / Shimmer, Optimistic UI Update, Pull-to-Refresh / Infinite Scroll / Pagination UI, Empty / Error / Loading State, Internationalization, Accessibility, Responsive vs Adaptive, Design Tokens, Compound Components / Slot |
| `patterns/api-design.md` | 14 | Richardson Maturity Model, HATEOAS, Resource-Oriented Design, API Versioning, Pagination 패턴 3종, Idempotency Key, Bulk / Batch Operation, Long-Running Operation, Error Response Standard, Resource Naming Convention, Filtering / Sorting / Field Selection, API Rate Limiting & Quota, Async API Pattern, API Deprecation & Sunset |
| `patterns/api-styles.md` | 9 | REST, GraphQL, gRPC, WebSocket, Server-Sent Events, Webhook, JSON-RPC 2.0, SOAP, WebTransport |
| `patterns/functional.md` | 11 | Functor, Applicative Functor, Monad, Free Monad, Lens / Optics, Tagless Final, Effect Handlers / Algebraic Effects, Continuation-Passing Style, Trampolining, Pattern Matching, Persistent Data Structures |
| `patterns/reactive-streams.md` | 8 | Reactive Streams Spec, Cold vs Hot Stream, Subject, Marble Diagram, Backpressure 전략, Operator Composition, Functional Reactive Programming, Stream Fusion / Operator Fusion |
| `patterns/workflow-jobs.md` | 9 | Durable Workflow, DAG-based Workflow, Job Queue, Saga, Scheduled Job / Cron, Worker Leasing / Visibility Timeout, Idempotent Worker, Long-Running Activity, Workflow Versioning |
| `patterns/streaming-semantics.md` | 9 | Delivery Semantics, Event Time vs Processing Time, Watermark, Windowing 패턴, Triggering, Allowed Lateness, State Management, Checkpoint / Savepoint, Backpressure in Stream |
| `patterns/data-modeling.md` | 12 | CAP Theorem, PACELC Theorem, Strong / Sequential / Causal / Eventual 일관성 모델 비교, Single-Leader Replication, Multi-Leader Replication, Leaderless Replication, Sharding / Partitioning, Consistent Hashing, Change Data Capture, Materialized View, HTAP / Lambda / Kappa Architecture, Data Mesh / Data Lakehouse |
| `patterns/ddd-strategic.md` | 12 | Ubiquitous Language, Subdomain 분류, Bounded Context, Context Map, Customer-Supplier 관계, Conformist 관계, Anti-Corruption Layer, Open Host Service, Published Language, Shared Kernel, Partnership, Separate Ways |
| `patterns/testing-strategies.md` | 10 | Test Pyramid vs Test Trophy vs Test Diamond vs Test Honeycomb, Chaos Engineering, Load Testing, Stress Testing, Spike Testing, Soak / Endurance Testing, A/B Testing / Multivariate, Synthetic Monitoring, Canary Analysis, Shadow Traffic / Dark Launch Testing |
| `patterns/build-versioning.md` | 9 | Monorepo, Polyrepo, Semantic Versioning, Calendar Versioning, ZeroVer, Build Caching, Hermetic Build, Reproducible Build, Dependency Resolution |
| `patterns/mlops.md` | 10 | Feature Store, Model Registry, Model Card, Data Drift Detection, Concept Drift Detection, Shadow Model / Champion-Challenger, ML Pipeline, Online vs Batch Inference, Data Contract, Model Monitoring |
| `patterns/blockchain.md` | 10 | Consensus Mechanism 비교, Smart Contract Upgrade, Oracle Pattern, Gas Optimization, Custody, Event Indexer, Token Standard, Layer 2 Scaling, MEV, Cross-chain Bridge |
| `patterns/domains/fintech.md` | 12 | Double-Entry Bookkeeping, Ledger Pattern, Reconciliation, Settlement / Clearing, Idempotent Payment, 3-D Secure Authentication, Payment Intent / Saga, Multi-Currency / FX Handling, Refund / Chargeback / Dispute, AML / KYC, Card Network 통합, Subscription / Recurring Billing |
| `patterns/domains/healthcare.md` | 10 | FHIR R5 Resource Model, HL7 v2 Messaging, SMART on FHIR / OAuth2 Launch, CDS Hooks, Consent Management, PHI Audit Trail, De-identification / Safe Harbor, DICOM Imaging Pipeline, IHE Profiles, Telehealth Session Pattern |
| `patterns/domains/ecommerce.md` | 12 | Cart Aggregate, Inventory Reservation / Soft Hold, Product Catalog, Pricing & Promotion Engine, Order State Machine, Checkout Flow, Fulfillment / Warehouse Pick-Pack-Ship, Returns / RMA, Search & Discovery, Recommendation, Marketplace Multi-Seller, Loyalty / Rewards Program |
| `patterns/domains/logistics.md` | 10 | VRP / Route Optimization, Real-time Tracking, ETA Calculation, Geofencing, Fleet Dispatch / Driver Matching, Last-Mile Delivery, Reverse Logistics, Multi-Hop / Cross-Docking, Capacity Planning / Demand Forecasting, Track & Trace |
| `patterns/domains/iot-edge.md` | 10 | Device Twin, OTA Firmware Update, Telemetry Buffer, Device Provisioning / Onboarding, Edge Gateway, MQTT Pub-Sub, Edge Inference, Time-Series Storage, Command & Control, Device Identity & Mutual TLS |

#### Algorithms 전체 항목

| 파일 | 항목 수 | 전체 서브 항목 |
|---|---:|---|
| `algorithms/sorting.md` | 16 | Bubble Sort, Selection Sort, Insertion Sort, Merge Sort, Quick Sort, Heap Sort, Counting Sort, Radix Sort, Bucket Sort, Shell Sort, Tim Sort, Intro Sort, Tree Sort, External Merge Sort, Pancake Sort, Cycle Sort |
| `algorithms/searching.md` | 13 | Linear Search, Binary Search, Jump Search, Interpolation Search, Exponential Search, Fibonacci Search, Ternary Search, Hash Table Search, Two Pointers, Sliding Window, Binary Lifting / Sparse Table, Mo's Algorithm, Parallel Binary Search |
| `algorithms/graph.md` | 18 | BFS, DFS, Dijkstra, Bellman-Ford, Floyd-Warshall, A*, Prim, Kruskal, Topological Sort, Tarjan's SCC, Kosaraju, Johnson, LCA, Articulation Points, Bridges, 2-SAT, Eulerian Path / Circuit, Min Cut / Stoer-Wagner |
| `algorithms/dynamic-programming.md` | 12 | Fibonacci, LCS, LIS, Knapsack, Edit Distance, Matrix Chain Multiplication, Coin Change, Rod Cutting, Bitmask DP, Tree DP, Digit DP, SOS DP |
| `algorithms/divide-conquer.md` | 5 | Binary Search, Merge Sort, Strassen's Matrix Multiplication, Closest Pair of Points, Karatsuba Multiplication |
| `algorithms/greedy.md` | 5 | Activity Selection, Huffman Coding, Fractional Knapsack, Job Sequencing with Deadlines, Optimal Merge Pattern |
| `algorithms/backtracking.md` | 5 | N-Queens, Sudoku Solver, Graph Coloring, Hamiltonian Cycle, Subset Sum |
| `algorithms/string.md` | 11 | KMP, Rabin-Karp, Boyer-Moore, Z Algorithm, Suffix Array, Trie, Aho-Corasick, Manacher's Algorithm, Suffix Automaton, Suffix Tree, Lyndon Decomposition |
| `algorithms/math.md` | 14 | Euclidean GCD, Sieve of Eratosthenes, Fast Exponentiation, Modular Arithmetic, Chinese Remainder Theorem, Fast Fourier Transform, Simpson's Rule, Newton-Raphson, Prime Factorization, Miller-Rabin Primality Test, Extended Euclidean, Lucas Theorem, Pollard's Rho, Linear Sieve |
| `algorithms/data-structures.md` | 9 | Union-Find, Segment Tree, Fenwick Tree, AVL Tree, Red-Black Tree, B-Tree, Skip List, LRU Cache, Bloom Filter |
| `algorithms/geometry.md` | 7 | CCW, Convex Hull / Graham Scan, Convex Hull / Andrew's Monotone Chain, Line Segment Intersection, Sweep Line, Rotating Calipers, Point-in-Polygon |
| `algorithms/flow.md` | 4 | Ford-Fulkerson, Edmonds-Karp, Dinic, Min-Cost Max-Flow |
| `algorithms/matching.md` | 3 | Bipartite Matching, Hopcroft-Karp, Stable Marriage |
| `algorithms/crypto.md` | 6 | SHA-256, HMAC, RSA, AES, Bcrypt, Argon2 |
| `algorithms/compression.md` | 5 | Run-Length Encoding, LZ77, LZ78 / LZW, Arithmetic Coding, Burrows-Wheeler Transform |
| `algorithms/game-ai.md` | 5 | Minimax, Alpha-Beta Pruning, Monte Carlo Tree Search, Genetic Algorithm, Simulated Annealing |
| `algorithms/ml.md` | 13 | K-Means Clustering, K-Nearest Neighbors, Linear Regression, Logistic Regression, Gradient Descent, Naive Bayes, Transformer, Attention Mechanism, HNSW, Quantization, Speculative Decoding, PageRank, Node2Vec |
| `algorithms/probabilistic.md` | 4 | Fisher-Yates Shuffle, Reservoir Sampling, Count-Min Sketch, HyperLogLog |
| `algorithms/consensus.md` | 3 | 2PC, Paxos, Raft |
| `algorithms/distributed.md` | 12 | Lamport Clock, Vector Clock, Hybrid Logical Clock, Gossip Protocol, SWIM, Anti-Entropy, CRDT G-Counter, CRDT PN-Counter, CRDT OR-Set, CRDT LWW-Set, Consistent Hashing, Quorum |
| `algorithms/concurrent.md` | 10 | CAS, LL-SC, RCU, MVCC, Hazard Pointer, Lock-Free Queue, Work-Stealing, Seqlock, Memory Barriers, ABA Problem 해법 |
| `algorithms/parsing.md` | 10 | Lexing / Tokenization, LL(k) Parsing, LR(1) Parsing, LALR Parsing, Earley Parser, Pratt Parser, PEG / Packrat Parser, AST Traversal, SSA Form, Register Allocation |
| `algorithms/db-indexes.md` | 8 | B+Tree Index, Hash Index, Bitmap Index, GIN, GiST, BRIN, Covering Index, Partial Index / Filtered Index |
| `algorithms/db-storage-engines.md` | 10 | Write-Ahead Log, LSM Tree, SSTable, Compaction Strategy, MVCC Vacuum / Garbage Collection, Buffer Pool / Page Cache, Page Layout, B-Link Tree, Replication Log, HOT Update |
| `algorithms/spatial.md` | 8 | R-Tree, R*-Tree, QuadTree, KD-Tree, Geohash, H3, S2 Geometry, BVH |
| `algorithms/search-systems.md` | 8 | Inverted Index, TF-IDF, BM25, Vector Search, Hybrid Search, Faceted Search / Aggregation, Autocomplete / Type-ahead, Learning to Rank |
| `algorithms/load-balancing.md` | 8 | Round Robin, Weighted Round Robin, Least Connections, Least Response Time, Power of Two Choices, Consistent Hashing, Maglev Hashing, EWMA |
| `algorithms/os-foundations.md` | 12 | Mark-Sweep GC, Generational GC, G1 GC, ZGC / Shenandoah, Round-Robin Scheduling, CFS, MLFQ, Slab Allocator, Buddy Allocator, epoll / kqueue / io_uring, Page Replacement, MESI Cache Coherence |
| `algorithms/image-processing.md` | 8 | Convolution / Kernel Filtering, Edge Detection, Hough Transform, Morphological Operations, Histogram & Equalization, Image Segmentation, Feature Detection, Optical Flow |
| `algorithms/signal-processing.md` | 8 | FIR Filter, IIR Filter, STFT, Wavelet Transform, Resampling, Kalman Filter, Extended / Unscented Kalman Filter, Auto-correlation / Cross-correlation |
| `algorithms/codecs.md` | 8 | JPEG, PNG, WebP / AVIF / HEIC, H.264 / AVC, H.265 / H.266 / AV1, MP3 / AAC, Opus, Entropy Coding |

#### Languages 전체 항목

| 파일 | 항목 수 | 전체 서브 항목 |
|---|---:|---|
| `languages/*.md` | 75 | ABAP, Ada, Apex, Assembly, AutoHotkey, AWK, Bash / Shell, C, Carbon, Clojure, COBOL, C++, Crystal, C#, CUDA C/C++, D, Dart, Delphi / Object Pascal, Elixir, Erlang, Forth, Fortran, F#, GDScript, Gleam, GLSL, Go, Groovy, Hack, Haskell, HCL, HLSL, Java, JavaScript, Jsonnet, Julia, Kotlin, Lean, Common Lisp, Lua, MATLAB, Mojo, Move, Nim, Objective-C, OCaml, OpenCL C, Perl, PHP, PL/SQL, PowerShell, Prolog, Python, R, Racket, Ruby, Rust, SAS, Scala, Smalltalk, Solidity, SQL, Stata, Swift, T-SQL, Tcl, TypeScript, VBA, Verilog/SystemVerilog, VHDL, Visual Basic .NET, WAT, Wolfram Language, YAML, Zig |
| `languages/index.md` | 1 | 언어 우선순위, 분야별 추천, 자동 감지, 별칭, 호출 동작 |
| `languages/domains.md` | 1 | 웹, AI/데이터, 모바일, 게임, 시스템, DevOps 등 분야별 언어 매트릭스 |

#### Security 전체 항목

| 파일 | 항목 수 | 전체 서브 항목 |
|---|---:|---|
| `security/security.md` | 4 | Defense in Depth, Zero Trust Architecture, Least Privilege, Secure by Default |
| `security/security-authn.md` | 13 | OAuth2 Authorization Code + PKCE, OIDC, SAML 2.0, FIDO2 / WebAuthn / Passkeys, MFA, OAuth Device Flow, Magic Link / Passwordless, Social Login, Session / Refresh Token Rotation + Reuse Detection, Account Takeover Defense, SCIM 2.0, Just-In-Time Access, PAM |
| `security/security-authz.md` | 7 | RBAC, ABAC, ReBAC, Policy as Code, Permission Boundary, Least Privilege 구현 패턴, JWT Claims-based Authorization |
| `security/security-crypto-ops.md` | 11 | KMS, HSM, Envelope Encryption, Key Rotation, Perfect Forward Secrecy, Post-Quantum Cryptography, Crypto Agility, OPAQUE / aPAKE, mTLS, Key Ceremony, HSM Runbook / Key Lifecycle Operations |
| `security/security-data-protection.md` | 8 | Encryption at Rest, Field-level Encryption, Tokenization, Format-Preserving Encryption, Data Masking, Pseudonymization, Differential Privacy, Confidential Computing |
| `security/security-api-web.md` | 12 | per-Identity Rate Limiting, HMAC Request Signing, IDOR / BOLA 방어, SSRF 방어, XXE 방어, CSRF 방어, Open Redirect 방어, Mass Assignment 방어, Race Condition / TOCTOU 방어, GraphQL 보안, CSP / SRI / HSTS / Trusted Types, CORS / Cookie 정책 |
| `security/security-supply-chain.md` | 8 | SBOM, Sigstore / Cosign, SLSA Framework, Reproducible Build, Provenance Attestation, Secret Scanning, Slopsquatting / Hallucinated Package Defense, AI-Assisted Code Secret Leak Defense |
| `security/security-platform.md` | 7 | Pod Security Standards, Image Signing, Network Policy, OPA / Gatekeeper, Runtime Security, IaC Scanning, Hardening Baseline |
| `security/security-sdlc.md` | 6 | Threat Modeling, SAST, DAST, IAST, SCA, Pre-commit Secret Scan |
| `security/security-detect-respond.md` | 6 | SIEM, SOAR, Audit Log Pattern / Tamper-Evident, UEBA, MITRE ATT&CK Mapping, Incident Response Playbook |
| `security/security-mobile.md` | 5 | Certificate Pinning, App Attest / Play Integrity, Jailbreak / Root Detection, RASP, Secure Storage |
| `security/security-ai-model.md` | 5 | Model Extraction / Theft, Membership Inference Attack, Data Poisoning, Adversarial Inputs / Evasion Attack, Federated Learning 보안 |
| `security/privacy-engineering.md` | 9 | Consent Ledger / Consent Management, Privacy by Design, DSAR, Retention Policy, Purpose Binding / Purpose Limitation, DPIA, Privacy Notice, Data Minimization, Privacy Operations |
| `security/compliance.md` | 5 | GDPR, CCPA / CPRA, PCI DSS, HIPAA, SOC 2 |

#### Principles 전체 항목

| 파일 | 항목 수 | 전체 서브 항목 |
|---|---:|---|
| `principles/solid.md` | 5 | Single Responsibility Principle, Open/Closed Principle, Liskov Substitution Principle, Interface Segregation Principle, Dependency Inversion Principle |
| `principles/grasp.md` | 9 | Information Expert, Creator, Controller, Low Coupling, High Cohesion, Polymorphism, Pure Fabrication, Indirection, Protected Variations |
| `principles/iso25010.md` | 8 | Functional Suitability, Performance Efficiency, Compatibility, Usability, Reliability, Security, Maintainability, Portability |
| `principles/12-factor.md` | 12 | Codebase, Dependencies, Config, Backing Services, Build / Release / Run, Processes, Port Binding, Concurrency, Disposability, Dev/Prod Parity, Logs, Admin Processes |
| `principles/code-smells.md` | 22 | Long Method, Large Class, Primitive Obsession, Long Parameter List, Data Clumps, Repeated Switches, Switch Statements, Refused Bequest, Alternative Classes with Different Interfaces, Divergent Change, Shotgun Surgery, Parallel Inheritance Hierarchies, Comments, Duplicate Code, Lazy Class, Data Class, Dead Code, Speculative Generality, Feature Envy, Inappropriate Intimacy, Message Chains, Middle Man |
| `principles/type-systems.md` | 10 | Static vs Dynamic Typing, Strong vs Weak Typing, Nominal vs Structural Typing, Hindley-Milner Type Inference, Algebraic Data Types, Generics & Variance, Higher-Kinded Types, Linear / Affine / Substructural Types, Dependent Types, Effect System / Algebraic Effects |
| `principles/concurrency-theory.md` | 10 | Linearizability, Serializability, Sequential Consistency, Causal Consistency, Eventual Consistency, Snapshot Isolation / Serializable SI, Happens-Before Relation, Liveness vs Safety Properties, Deadlock 4 Conditions, Race Condition / Data Race / Atomicity Violation |
| `principles/refactoring-techniques.md` | 25 | Extract Function, Inline Function, Extract Variable, Inline Variable, Change Function Declaration, Encapsulate Variable, Rename Variable, Introduce Parameter Object, Combine Functions into Class, Combine Functions into Transform, Split Phase, Encapsulate Record, Encapsulate Collection, Replace Primitive with Object, Replace Conditional with Polymorphism, Replace Type Code with Subclasses, Remove Subclass, Extract Superclass, Replace Inheritance with Delegation, Replace Subclass with Delegate, Hide Delegate, Remove Middle Man, Move Field, Move Function, Decompose Conditional |
| `principles/sw-economics.md` | 10 | Function Points, COCOMO II, Story Point, Planning Poker, T-Shirt Sizing, WSJF, RICE Score, Cost of Delay, Technical Debt Quadrant, Reference Class Forecasting |
| `principles/evolutionary-arch.md` | 8 | Architectural Fitness Function, Architectural Characteristics, Architectural Quanta, Coupling Static vs Dynamic, Modularity Metric, Bounded Context / Architectural Quanta, Last Responsible Moment, Architecture as a Hypothesis |
| `principles/resilience-theory.md` | 8 | Brittleness vs Robustness vs Resilience, Drift into Failure, Safety-I vs Safety-II, STAMP, Antifragility, Graceful Degradation, Chaos Engineering Principles, Resilience Capabilities |
| `principles/documentation.md` | 8 | Architecture Decision Records, Y-Statement / Nygard Format, MADR, RFC 프로세스, Diataxis Framework, Living Documentation, Documentation as Code, C4 Model |
| `principles/process-metrics.md` | 10 | Scrum, Kanban, Extreme Programming, DORA 4 Key Metrics, SPACE Framework, Trunk-Based Development, GitOps, Platform Engineering / IDP, Three Amigos / Example Mapping, Pair Programming / Mob Programming |
| `principles/performance-metrics.md` | 10 | Latency Numbers Every Programmer Should Know, Big-O Notation 실용편, Cyclomatic Complexity, Cognitive Complexity, Halstead Metrics, N+1 Query Problem, Profiling 기법, Latency Percentile, USE / RED / Golden Signals, Apdex Score |
| `principles/sustainable-sw.md` | 8 | Carbon-Aware Computing, Energy Efficiency, Hardware Efficiency / Embodied Carbon, Software Carbon Intensity, Region-aware Deployment, Demand Shifting, Demand Shaping, Efficient Data Storage & Transmission |
| `principles/micro-principles.md` | 18 | DRY, KISS, YAGNI, Law of Demeter, Separation of Concerns, Tell Don't Ask, Composition over Inheritance, Single Source of Truth, Conway's Law, Inverse Conway Maneuver, Hyrum's Law, Postel's Law, Brooks's Law, Hollywood Principle, Boy Scout Rule, Pareto Principle, Goodhart's Law, Cunningham's Law |

## 3. 폴더 구조 정리

```text
.
├── .gitignore
├── README.md
├── scripts/
│   └── install-skills.sh
├── claude/
│   └── skills/
│       └── dev-advisor/
│           ├── SKILL.md
│           ├── references/
│           │   ├── README.md
│           │   ├── algorithms/
│           │   ├── code_templates.md
│           │   ├── examples.md
│           │   ├── handoff.md
│           │   ├── languages/
│           │   ├── output_templates.md
│           │   ├── patterns/
│           │   │   └── domains/
│           │   ├── principles/
│           │   └── security/
│           └── scripts/
│               ├── README.md
│               ├── enrich-languages.py
│               ├── verify-anchors.sh
│               └── verify-references.sh
└── codex/
    └── skills/
        └── dev-advisor/
            ├── SKILL.md
            ├── agents/
            │   └── openai.yaml
            ├── references/
            │   ├── README.md
            │   ├── algorithms/
            │   ├── code_templates.md
            │   ├── examples.md
            │   ├── handoff.md
            │   ├── languages/
            │   ├── output_templates.md
            │   ├── patterns/
            │   │   └── domains/
            │   ├── principles/
            │   └── security/
            └── scripts/
                ├── README.md
                ├── enrich-languages.py
                ├── verify-anchors.sh
                └── verify-references.sh
```

| 워크트리 항목 | Git 추적 여부 | 설명 |
|---|---|---|
| `.gitignore` | 추적 | 저장소 제외 규칙 |
| `README.md` | 추적 | 루트 프로젝트 설명 문서 |
| `scripts/install-skills.sh` | 추적 | Codex/Claude Code 스킬 자동 설치 스크립트 |
| `claude/` | 추적 | Claude용 dev-advisor 스킬 패키지 |
| `codex/` | 추적 | Codex용 dev-advisor 스킬 패키지 |
| `.omx/` | 제외 | oh-my-codex 실행 상태, 세션, 로그 |
| `.DS_Store` | 제외 | macOS Finder 메타데이터 |
| `__pycache__/`, `*.pyc` | 제외 | Python 실행 캐시 |
| `.env`, `.env.*` | 제외 | 로컬 환경변수와 비밀값 |

## 4. 그 외 추가해야 될 것

| 우선순위 | 추가 항목 | 이유 | 제안 |
|---:|---|---|---|
| 1 | 라이선스 파일 | 공개 저장소에서 사용/수정/배포 조건이 명확해야 합니다. | `LICENSE`를 추가하고 MIT, Apache-2.0, CC BY-SA 중 문서 성격에 맞게 선택 |
| 2 | 기여 가이드 | 카탈로그 항목 추가 기준과 검증 절차가 필요합니다. | `CONTRIBUTING.md`에 ID 명명 규칙, anchor 규칙, PR 체크리스트 작성 |
| 3 | 변경 이력 | 카탈로그 항목 수와 구조 변경을 추적해야 합니다. | `CHANGELOG.md`를 추가하고 버전별 항목 수, breaking change 기록 |
| 4 | GitHub Actions | 사람이 매번 스크립트를 실행하지 않아도 무결성을 확인해야 합니다. | PR마다 `scripts/verify-references.sh` 실행 |
| 5 | 릴리스 태그 | 다른 환경에서 특정 버전을 고정해 설치할 수 있어야 합니다. | `vYYYY.MM.DD` 또는 semantic version 태그 운영 |
| 6 | 설치 문서 | Codex/Claude 각각의 설치 경로와 적용 방법이 필요합니다. | `docs/install-codex.md`, `docs/install-claude.md` 추가 |
| 7 | 카탈로그 생성 규칙 | 새 패턴/알고리즘/원칙 추가 시 품질 편차를 줄여야 합니다. | `docs/catalog-authoring.md`에 필수 섹션, 예시, anti-pattern 정의 |
| 8 | 외부 표준 버전 고정 | OWASP, NIST, ISO 같은 외부 표준은 버전 변화가 있습니다. | README와 카탈로그에 확인일과 기준 버전을 명시 |

### 현재 검증 명령

| 명령 | 목적 |
|---|---|
| `sh codex/skills/dev-advisor/scripts/verify-references.sh` | Codex 스킬 카탈로그 전체 무결성 검증 |
| `sh claude/skills/dev-advisor/scripts/verify-references.sh` | Claude 스킬 카탈로그 전체 무결성 검증 |
| `sh codex/skills/dev-advisor/scripts/verify-anchors.sh` | Codex 스킬 anchor wrapper 검증 |
| `sh claude/skills/dev-advisor/scripts/verify-anchors.sh` | Claude 스킬 anchor wrapper 검증 |

## 5. 출처와 참조 사이트 정리

확인일: 2026-05-14

### 5.1 프로젝트 내부 참조

| 구분 | 경로 | 설명 |
|---|---|---|
| Codex 스킬 진입점 | [`codex/skills/dev-advisor/SKILL.md`](codex/skills/dev-advisor/SKILL.md) | 프로젝트 목적, 호출 인터페이스, advisor 모드, 카탈로그 개요 |
| Claude 스킬 진입점 | [`claude/skills/dev-advisor/SKILL.md`](claude/skills/dev-advisor/SKILL.md) | Claude 환경용 동일 카탈로그 진입점 |
| Reference guide | [`codex/skills/dev-advisor/references/README.md`](codex/skills/dev-advisor/references/README.md) | references 디렉토리 구조와 링크 규약 |
| Patterns index | [`codex/skills/dev-advisor/references/patterns/index.md`](codex/skills/dev-advisor/references/patterns/index.md) | 패턴 카탈로그 진입점 |
| Algorithms index | [`codex/skills/dev-advisor/references/algorithms/index.md`](codex/skills/dev-advisor/references/algorithms/index.md) | 알고리즘 카탈로그 진입점 |
| Languages index | [`codex/skills/dev-advisor/references/languages/index.md`](codex/skills/dev-advisor/references/languages/index.md) | 언어 카탈로그 진입점 |
| Security index | [`codex/skills/dev-advisor/references/security/index.md`](codex/skills/dev-advisor/references/security/index.md) | 보안 카탈로그 진입점 |
| Principles index | [`codex/skills/dev-advisor/references/principles/index.md`](codex/skills/dev-advisor/references/principles/index.md) | 소프트웨어 공학 원칙 카탈로그 진입점 |

### 5.2 외부 참조 사이트

| 주제 | 사이트 | 참고 이유 |
|---|---|---|
| OWASP ASVS | [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/) | 애플리케이션 보안 검증 요구사항과 보안 통제 기준 |
| NIST Digital Identity | [NIST SP 800-63B](https://csrc.nist.gov/pubs/sp/800/63/b/upd2/final) | 인증, 세션, 디지털 신원 관리 기준 |
| NIST SSDF | [NIST SP 800-218](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf) | Secure Software Development Framework 기준 |
| OAuth 2.0 | [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749) | OAuth 2.0 Authorization Framework 기준 |
| ISO/IEC 25010 | [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) | 소프트웨어 제품 품질 모델 기준 |
| 12-Factor App | [The Twelve-Factor App](https://12factor.net/) | SaaS/웹 앱 운영 설계 원칙 |
| Domain-Driven Design | [Martin Fowler: Domain Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html) | DDD 개념과 설계 어휘 참고 |
| Design Patterns | [Refactoring.Guru Design Patterns Catalog](https://refactoring.guru/design-patterns/catalog) | GoF 패턴 학습용 카탈로그 참고 |
