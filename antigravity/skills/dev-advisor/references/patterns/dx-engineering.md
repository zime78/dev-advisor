# DX Engineering (Developer Experience Engineering)

개발자 경험 향상 8 패턴. **개발자 시간 = 가장 비싼 자원**. Scaffolding / Codegen / LSP / Devcontainer / REPL / Hot Reload / DevTools / Backstage 를 한 자리에 모아, "처음 onboarding 5분" · "코드 한 줄 바꿔 1초 안에 화면 확인" · "팀 표준대로 서비스 1분 안에 부팅" 같은 구체 목표를 달성한다.

**원전·표준 참고**:
- Microsoft — *Language Server Protocol* (https://microsoft.github.io/language-server-protocol/, 2016)
- Microsoft — *Debug Adapter Protocol* (https://microsoft.github.io/debug-adapter-protocol/, 2018)
- Brian Marick / Fernando Pérez — *Notebook* concept (IPython → Jupyter, 2014)
- VS Code Dev Containers (https://containers.dev) / Gitpod / GitHub Codespaces
- Spotify — *Backstage* (https://backstage.io, CNCF Incubating, 2020)
- McKinsey — *Developer Velocity / Developer Productivity* survey (2020, 2023)
- Humanitec — *Platform Engineering* annual report
- Bret Victor — *Inventing on Principle* (immediate feedback / hot reload 사상적 기원, 2012)
- Dan Abramov — *React Fast Refresh* RFC (2019)

**관련 카탈로그**:
- [observability.md](observability.md) — DevTools 와 production observability 의 다리
- [testing.md](testing.md) — Hot Reload / REPL 기반 빠른 피드백 루프와 TDD 결합
- [deployment.md](deployment.md) — Backstage golden path 가 표준화하는 배포 패턴
- [crossplatform.md](crossplatform.md) — Flutter / React Native Hot Reload 의 플랫폼 관점
- [../principles/12-factor.md](../principles/12-factor.md) — Dev/Prod parity (devcontainer 의 사상적 배경)

---

## 1. Scaffolding (Project / Component Generator)

<a id="scaffolding"></a>

**목적**: 프로젝트 시작·컴포넌트 추가 시 반복되는 boilerplate(폴더 구조, 설정 파일, lint·formatter 룰, CI 워크플로) 작성을 generator 로 자동화하여, "5분만에 새 서비스 한 개" 가능하게 만든다.

**특징**:
- 입력 = 답변(서비스명, 언어, DB 종류 등). 출력 = 완성된 파일 트리
- 대표 도구: Yeoman, create-react-app / create-next-app / create-vite, Cookiecutter(Python), Hygen(JS), Plop, Yarn create
- 템플릿은 **답변 변수 + Liquid/EJS/Jinja 같은 템플릿 엔진**으로 구성
- 사내 표준이 굳어지면 사내 전용 generator (e.g. `create-acme-service`) 작성
- Plop 같은 in-repo generator 는 컴포넌트 추가(component, store, page) 같은 미시 작업에 유리

**장점**:
- onboarding 가속: 신규 입사자가 첫날 "어디부터 만들지" 고민 없음
- 표준 강제: lint·CI·secret 관리 등 빠뜨릴 수 있는 것을 generator 가 보장
- 다양성 감소 → 유지보수·도구 자동화 용이 (모든 서비스 동일 구조)
- 한 곳(generator 템플릿)을 고치면 새 서비스에 즉시 반영

**단점**:
- 템플릿이 stale 되면 generator 가 만든 신규 프로젝트도 곧장 outdated (지속 유지보수 필요)
- 과도하게 prescriptive 하면 새로운 패턴 도입을 막을 수 있음
- generator output 을 사후에 다 같이 마이그레이션하는 비용 별도 (e.g. Next.js minor 업그레이드)
- 한 번 만든 후 사용자가 직접 수정한 곳은 generator 가 모름 (re-run 시 충돌)

**활용 예시**:
- React 신규 앱: `npx create-react-app` / `npm create vite@latest`
- Next.js 신규 앱: `npx create-next-app`
- Python 신규 라이브러리: `cookiecutter gh:audreyfeldroy/cookiecutter-pypackage`
- 사내 표준 마이크로서비스: `npx create-acme-service --lang=kotlin --db=postgres`
- Plop 으로 in-repo 컴포넌트 추가: `npm run plop component MyButton`

```yaml
# .plop/plopfile.js — In-repo component generator (Hygen / Plop 동급 패턴)
# 호출: npm run plop component Button
# 결과: src/components/Button/{Button.tsx, Button.test.tsx, index.ts}

generators:
  component:
    description: "Create a new React component with test + barrel"
    prompts:
      - type: input
        name: name
        message: "Component name (PascalCase)?"
    actions:
      - type: add
        path: "src/components/{{pascalCase name}}/{{pascalCase name}}.tsx"
        templateFile: "templates/component.tsx.hbs"
      - type: add
        path: "src/components/{{pascalCase name}}/{{pascalCase name}}.test.tsx"
        templateFile: "templates/component.test.tsx.hbs"
      - type: add
        path: "src/components/{{pascalCase name}}/index.ts"
        template: "export * from './{{pascalCase name}}';"
      - type: modify
        path: "src/components/index.ts"
        pattern: "// PLOP_INJECT_EXPORT"
        template: "export * from './{{pascalCase name}}';\n// PLOP_INJECT_EXPORT"
```

**관련 패턴**:
- [Code Generation](#code-generation) — runtime 생성과 build-time 생성의 차이
- [Backstage IDP](#backstage-idp) — Software Template 으로 scaffolding 을 portal 화
- `../principles/12-factor.md` — Codebase / Config / Dependencies 표준 강제

---

## 2. Code Generation (Codegen)

<a id="code-generation"></a>

**목적**: schema(OpenAPI / GraphQL / Protobuf / SQL DDL) 같은 단일 source of truth 로부터 type-safe 클라이언트·서버 stub·DB 어댑터 코드를 **build-time** 에 자동 생성하여, 휴먼 에러(타입 오타, 직렬화 mismatch)를 컴파일 단계로 끌어올린다.

**특징**:
- 입력 = schema 파일. 출력 = 언어별 type / client / server stub
- 대표 도구:
  - OpenAPI Generator / openapi-typescript / Orval
  - GraphQL Code Generator (`graphql-codegen`)
  - Prisma (Schema → TypeScript client + migration)
  - Protocol Buffers / gRPC (`protoc`)
  - SQLDelight / jOOQ (SQL → Kotlin/Java type)
  - Quicktype (JSON sample → 타입)
- 생성된 파일은 **VCS 에 commit 하거나 build 단계마다 재생성**. 양쪽 다 trade-off 있음
- scaffolding 이 "한 번 만들고 끝" 이라면 codegen 은 "schema 가 바뀔 때마다 재생성"

**장점**:
- type-safe 클라이언트 → 컴파일 단계에서 schema mismatch 적발
- backend/frontend 동기화: schema 한 곳을 고치면 양쪽 코드가 즉시 반응
- boilerplate (DTO, serializer) 제거 → 비즈니스 로직에 집중
- API 문서·타입·client 가 자동 일치 (drift 방지)

**단점**:
- schema 가 잘못되면 모든 클라이언트가 일제히 깨짐 → schema 변경에 review 절차 필요
- 생성된 코드가 거대해져 IDE 가 느려질 수 있음 (Prisma client 등)
- generator 버전 업 시 미세한 출력 차이로 large diff 발생
- runtime reflection 보다 build 시간이 길어짐 (특히 monorepo)

**활용 예시**:
- 백엔드가 OpenAPI 명세 publish → `openapi-typescript` 로 frontend `client.ts` 생성
- Prisma `schema.prisma` → `prisma generate` → `PrismaClient` TypeScript 타입
- gRPC `service.proto` → `protoc` → Go server stub + Kotlin client stub
- SQLDelight `*.sq` → Kotlin Data class + type-safe query

```kotlin
// schema.prisma 예시 + 사용 코드 (Codegen 후의 type-safe client)

// schema.prisma
// generator client { provider = "prisma-client-js" }
// model User {
//   id    String @id @default(cuid())
//   email String @unique
//   posts Post[]
// }
// model Post { id String @id; title String; authorId String; author User @relation(...) }

// $ npx prisma generate  →  type-safe client 생성

// 사용 코드 (TypeScript, 생성된 client)
import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

// ↓ 자동완성·타입체크가 schema 기반으로 완전 동작
const user = await prisma.user.findUnique({
  where: { email: "alice@example.com" },
  include: { posts: true }, // posts 가 schema 의 relation 임을 컴파일러가 인지
});

// 잘못된 필드: 컴파일 에러
// prisma.user.findUnique({ where: { emial: "..." } }); // ❌ TS2353
```

**관련 패턴**:
- [Scaffolding](#scaffolding) — codegen 은 schema-driven, scaffolding 은 prompt-driven
- [Language Server Protocol](#language-server-protocol) — 생성된 타입이 editor 자동완성으로 연결되려면 LSP 가 필수
- `api-styles.md` — OpenAPI / GraphQL / gRPC 의 schema-first 사상

---

## 3. Language Server Protocol (LSP)

<a id="language-server-protocol"></a>

**목적**: 자동완성, lint, refactor, goto definition 같은 IDE 지능 기능을 **언어 server 1개 ↔ editor N개** 구조로 분리하여, 한 언어를 한 번만 구현하면 모든 editor 가 동등하게 지원받게 한다.

**특징**:
- 2016 Microsoft 가 VS Code 와 TypeScript Server 통신 규약을 공개 표준화한 것이 시초
- transport: stdio / TCP / WebSocket. payload: JSON-RPC 2.0
- 핵심 메서드: `initialize`, `textDocument/didOpen`, `textDocument/completion`, `textDocument/definition`, `textDocument/hover`, `textDocument/rename`, `workspace/symbol`, `textDocument/publishDiagnostics`
- capability negotiation: initialize 시 client / server 가 서로 지원하는 기능 advertise
- 자매 표준: **DAP (Debug Adapter Protocol)** — debugger 도 동일 사상으로 분리

**장점**:
- N × M 폭발 제거: 언어 N개 × editor M개 = N+M 으로 축소
- editor 갈아타도 동일 지능 (rust-analyzer 한 번 설치 → VS Code / Neovim / Helix / Emacs 모두 동일 경험)
- 언어 도구 개발자가 IDE UI 작성 부담 없이 핵심에 집중
- 사내 DSL 도 server 한 번 짜면 모든 editor 에 자동완성 제공 가능

**단점**:
- IPC 오버헤드: 큰 프로젝트에서 100ms+ latency 누적 (proximity 한 in-process 대비 손해)
- JSON-RPC 라 binary 직렬화 불가능 → 큰 응답(diagnostics 수천 개) 시 throughput 제한
- 각 server 의 capability 가 균일하지 않음 (LSP 표준이지만 구현체 격차 큼)
- multi-root workspace, virtual file system 같은 고급 기능은 client/server 모두 까다로움

**활용 예시**:
- TypeScript: `tsserver` / `typescript-language-server`
- Rust: `rust-analyzer`
- Python: `pyright` / `ruff-lsp`
- Kotlin: `kotlin-language-server` / `JetBrains Fleet` 가 사용하는 사내 LSP
- Dart/Flutter: `dart language-server` (Flutter SDK 번들)
- 사내 DSL: 회사 protobuf schema 전용 LSP server 작성 → 모든 IDE 에서 자동완성

```kotlin
// JSON-RPC 2.0 over stdio — LSP capability negotiation 핵심 흐름
// (client = editor, server = language server)

// ── 1) client → server: initialize ──
// {
//   "jsonrpc": "2.0", "id": 1, "method": "initialize",
//   "params": {
//     "processId": 12345,
//     "rootUri": "file:///workspace/app",
//     "capabilities": {
//       "textDocument": {
//         "completion": { "completionItem": { "snippetSupport": true } },
//         "hover": { "contentFormat": ["markdown", "plaintext"] },
//         "definition": { "linkSupport": true }
//       }
//     }
//   }
// }

// ── 2) server → client: initialize result (server capabilities) ──
// {
//   "jsonrpc": "2.0", "id": 1,
//   "result": {
//     "capabilities": {
//       "textDocumentSync": 2,                  // incremental
//       "completionProvider": { "triggerCharacters": [".", ":"] },
//       "hoverProvider": true,
//       "definitionProvider": true,
//       "renameProvider": { "prepareProvider": true }
//     },
//     "serverInfo": { "name": "acme-dsl-ls", "version": "0.1.0" }
//   }
// }

// ── 3) client → server: textDocument/didOpen, didChange ... ──
// ── 4) server → client: textDocument/publishDiagnostics (push 알림) ──
//    user 가 코드를 칠 때마다 server 가 진단을 client 에 push.
//    LSP 가 request-response 외에 **push 알림** 채널을 갖는 이유.

// Kotlin server 측 처리 의사 코드
class AcmeDslServer : LanguageServer {
    override fun initialize(params: InitializeParams): CompletableFuture<InitializeResult> {
        val caps = ServerCapabilities().apply {
            textDocumentSync = Either.forLeft(TextDocumentSyncKind.Incremental)
            completionProvider = CompletionOptions(true, listOf(".", ":"))
            hoverProvider = Either.forLeft(true)
            definitionProvider = Either.forLeft(true)
        }
        return completedFuture(InitializeResult(caps, ServerInfo("acme-dsl-ls", "0.1.0")))
    }
}
```

**관련 패턴**:
- [DevTools](#devtools) — LSP 의 자매 표준인 DAP 가 debugger 를 동일 사상으로 분리
- [Code Generation](#code-generation) — codegen 결과물에 LSP 가 type info 를 제공해야 자동완성이 살아남
- `../principles/type-systems.md` — 정적 타입 시스템이 LSP 의 효용을 극대화

---

## 4. Devcontainer / Dev Environment as Code

<a id="devcontainer"></a>

**목적**: "내 PC 에선 됐는데" 를 제거. 개발 환경(언어 SDK, DB, redis, 환경변수, VS Code extension)을 **파일(코드)** 로 선언하여, clone → 1 분 안에 동일한 환경이 어디서나 부팅된다.

**특징**:
- 대표 구현:
  - **VS Code Dev Containers** + `devcontainer.json` (https://containers.dev) — Docker 기반
  - **GitHub Codespaces** — Dev Containers 사양을 클라우드 VM 에서 실행
  - **Gitpod** — `.gitpod.yml` + workspace image
  - **Nix dev shell** (`flake.nix`) — 패키지 매니저 수준에서 declarative
  - **devbox** (Jetify) — Nix 위의 friendly wrapper
- 12-Factor `Dev/prod parity` 의 dev 측 구현
- secrets / 환경 변수는 별도 (devcontainer 는 환경 정의, 비밀은 secret manager)

**장점**:
- onboarding: `git clone` → 자동 컨테이너 빌드 → IDE 자동 attach → 즉시 코드 작성
- OS 독립: macOS / Windows / Linux 어디서나 동일 환경
- 의존성 충돌 제거: 프로젝트마다 Node 18 / Node 20 같은 버전 분리
- CI 와 같은 베이스 이미지 사용 가능 → "CI 에서만 깨지는" 문제 감소
- 노트북 잃어버려도 30분 안에 복구

**단점**:
- 첫 빌드 시간이 길다 (이미지 풀 + extension 설치)
- 디스크 사용량 증가 (프로젝트마다 컨테이너)
- GPU / 카메라 / 시뮬레이터(iOS) 같은 native 자원 사용은 까다로움
- 네이티브 IDE(JetBrains 계열)는 LSP-over-SSH 대비 통합도 격차
- Mac 의 Docker Desktop 성능 (특히 파일 시스템 I/O) 이슈

**활용 예시**:
- React/Node 프로젝트의 `devcontainer.json`
- Python ML 프로젝트: CUDA 런타임 + jupyter 포함 이미지
- Kotlin/Spring 프로젝트: JDK 21 + postgres + redis docker-compose
- 사내 표준 base image 를 두고 프로젝트별로 extend

```yaml
# .devcontainer/devcontainer.json — VS Code Dev Containers spec
# - clone 직후 IDE 열면 docker compose up + extension 자동 설치
# - postgres / redis 같은 backing service 도 함께 부팅
{
  "name": "acme-api",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",

  "features": {
    "ghcr.io/devcontainers/features/node:1": { "version": "20" },
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },

  "forwardPorts": [3000, 5432, 6379],
  "portsAttributes": {
    "3000": { "label": "API", "onAutoForward": "openBrowser" }
  },

  "postCreateCommand": "pnpm install && pnpm prisma migrate dev",
  "postStartCommand": "pnpm dev",

  "customizations": {
    "vscode": {
      "extensions": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "Prisma.prisma",
        "ms-azuretools.vscode-docker"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode"
      }
    }
  },

  "remoteUser": "node",
  "containerEnv": {
    "DATABASE_URL": "postgresql://dev:dev@db:5432/acme",
    "REDIS_URL": "redis://cache:6379"
  }
}
```

**관련 패턴**:
- [Backstage IDP](#backstage-idp) — 서비스 신규 생성 시 devcontainer 까지 함께 scaffold
- `../principles/12-factor.md` — Dev/Prod parity, Backing services, Config
- `deployment.md` — 같은 base image 를 prod / staging / dev 가 공유

---

## 5. REPL / Notebook

<a id="repl-notebook"></a>

**목적**: 코드 한 줄을 즉시 실행하고 결과를 즉시 본다(exploratory programming). "한 사이클 = ms 단위" 의 피드백 루프로, 가설 → 검증 → 가설 의 사고 흐름을 끊지 않게 한다.

**특징**:
- **REPL (Read-Eval-Print Loop)**: 텍스트 줄 단위. Lisp 1960s, Python `>>>`, Node `node`, Kotlin `kotlinc -script`
- **Notebook**: 셀(cell) 단위 + 셀 출력에 그래프 / 표 / 이미지 inline 가능. IPython(2001) → Jupyter(2014)
- 대표:
  - Jupyter (Python, Julia, R, Kotlin via Kotlin Kernel)
  - Observable (JavaScript, reactive 셀)
  - Polyglot Notebooks (.NET, multiple languages 한 노트북)
  - Pluto.jl (Julia, reactive)
  - Hex / Deepnote / Google Colab — SaaS 형태
- 변형: **scratchpad** (IntelliJ Scratch file, Visual Studio Interactive)

**장점**:
- 빠른 가설 검증: 데이터 분석·머신러닝·API 탐험·DB 쿼리에 강력
- 결과가 코드와 함께 보존됨 (notebook 파일이 곧 분석 보고서)
- onboarding 자료로 활용 가능 (실행 가능한 튜토리얼)
- 시각화 (matplotlib, Altair) 가 셀 결과로 inline

**단점**:
- 셀 실행 순서 의존성: 위에서 아래로 실행하지 않으면 재현 불가 ("hidden state")
- VCS diff 어려움: `.ipynb` 가 JSON 이라 인간이 읽기 어려움 (nbdime, Jupytext 로 완화)
- production code 와 분리: notebook 코드는 그대로 production 으로 옮기면 안 됨
- 테스트·CI 통합이 어색 (papermill, nbmake 같은 도구로 보완)
- 셀 간 변수 leak → 의도치 않은 상태 공유

**활용 예시**:
- 데이터 분석: pandas + matplotlib 으로 매출 분포 확인
- ML 실험: 모델 학습 epoch 별 loss 시각화
- API 탐험: 신규 API endpoint 호출 → JSON 응답 구조 파악
- 운영 분석: 한 번성 SQL → DataFrame 변환 → 그래프
- 교육: 인터랙티브한 튜토리얼 / 라이브 코딩

```kotlin
// Kotlin Jupyter Kernel (Jupyter 위에서 Kotlin REPL)
// $ kotlin -classpath ... -kernel  → Jupyter 가 kotlin-jupyter-kernel 호출

// Cell 1: 의존성 선언 (라인 매직)
%use krangl
%use lets-plot

// Cell 2: 데이터 로드
val df = DataFrame.readCSV("sales_2026.csv")
df.head()
// → 셀 출력으로 표 자동 렌더

// Cell 3: 집계
val byMonth = df.groupBy("month").summarize("revenue") { it["amount"].sum() }
byMonth
// → 셀 출력 표

// Cell 4: 시각화 (lets-plot)
import org.jetbrains.letsPlot.*
import org.jetbrains.letsPlot.geom.geomBar

val plot = letsPlot(byMonth.toMap()) {
    x = "month"; y = "revenue"
} + geomBar(stat = Stat.identity)
plot
// → 셀 출력으로 그래프 inline

// Cell 5: 가설 — peak 월 확인 후 production 쿼리로 옮기기 전 검증
val peak = byMonth.sortedByDescending { it["revenue"] as Double }.head(3)
peak
```

**관련 패턴**:
- [Hot Reload / Fast Refresh](#hot-reload-fast-refresh-dx) — 둘 다 "ms 단위 피드백 루프" 사상
- [DevTools](#devtools) — Chrome DevTools Console 도 사실상 REPL
- `testing.md` — production 화 전 REPL 에서 도출한 가설을 테스트로 고정

---

## 6. Hot Reload / Fast Refresh

<a id="hot-reload-fast-refresh-dx"></a>

**목적**: 코드를 저장하면 **앱 상태를 유지한 채** 변경분이 즉시 화면에 반영된다. "변경 → 빌드 → 재시작 → 화면 이동 → 결과 확인" 의 수 분짜리 루프를 < 1초 로 단축한다.

**특징**:
- **Hot Reload**: 코드 변경 부분을 런타임에 hot-swap. 가능하면 앱 상태 유지
- **Fast Refresh**: React 의 명칭. 컴포넌트 단위 hot reload, hook state 보존
- **HMR (Hot Module Replacement)**: webpack / Vite / Turbopack 의 모듈 단위 교체
- 사상적 기원: Bret Victor *Inventing on Principle* (2012) — "immediate connection between creation and result"
- 차별 개념:
  - **Hot Restart**: 앱은 재시작하되 전체 빌드는 생략 (Flutter 의 hot restart)
  - **Live Reload**: 전체 페이지 새로고침 (state 손실)

**장점**:
- 압도적인 피드백 속도 (Flutter < 1s, Vite HMR < 100ms)
- 상태 유지 → 깊이 들어가야 보이는 화면 (다단계 폼, 게임의 boss stage)도 즉시 디버깅
- 디자이너·기획자와 페어 작업 시 같이 보면서 즉시 반응
- 학습 곡선 가파른 신규 입사자에게도 "내가 친 코드가 어디에 어떻게 반영되는지" 체감

**단점**:
- 일부 변경은 hot reload 불가 (전역 상수, native 코드, top-level enum) → 자동 full restart fallback
- 상태가 의도와 다르게 유지되어 "왜 안 바뀌지?" 혼란 (잘못 캐시된 props)
- production build 와 미세하게 다른 동작 (dev-only 코드 경로)
- 빌드 도구 의존: webpack, Vite, Turbopack, Flutter engine 등 toolchain 종속

**활용 예시**:
- Flutter: `flutter run` → 코드 저장 → 화면 즉시 갱신 (hot reload), `R` 키 = hot restart
- React Native: Fast Refresh 자동 활성화
- Web: Vite HMR (`import.meta.hot`), Next.js Fast Refresh, Remix
- Java/Kotlin (Spring Boot): JRebel, Spring Boot DevTools (제한적 — 클래스 reload)
- Elixir/Phoenix: code reloader + LiveView 라이브 갱신

```kotlin
// Vite HMR API — 모듈이 자기 자신을 "hot replaceable" 로 등록하는 패턴
// (TypeScript / JavaScript)

// counter.ts — 카운터 상태를 유지하면서 로직만 교체하고 싶다
let count = 0;

export function increment(): number {
  return ++count;
}

// HMR API: 이 모듈이 갱신되면 어떻게 처리할지 명시
// import.meta.hot 은 Vite dev server 에서만 정의됨 (production 빌드에서는 undefined)
if (import.meta.hot) {
  // 1) state 보존: 새 모듈에 카운터를 넘긴다
  import.meta.hot.dispose((data) => {
    data.count = count;
  });

  // 2) 모듈 reload 시 이전 state 복원
  if (import.meta.hot.data.count !== undefined) {
    count = import.meta.hot.data.count;
  }

  // 3) 이 모듈을 hot replaceable 로 마킹
  import.meta.hot.accept((newModule) => {
    // 새 모듈이 로드되면 caller 들은 자동으로 newModule.increment 를 사용
    console.log("[HMR] counter.ts updated, count preserved:", count);
  });
}

// React 에서는 react-refresh 가 컴포넌트 단위로 위 패턴을 자동 적용 (수동 작성 불필요)
// Flutter 에서는 Dart VM 의 hot reload 가 동일 사상을 native 단계에서 처리
```

**관련 패턴**:
- [REPL / Notebook](#repl-notebook) — "ms 단위 피드백 루프" 사상의 형제
- [DevTools](#devtools) — Hot reload 와 함께 element inspector / time-travel debug 결합
- `crossplatform.md` — Flutter / React Native Hot Reload 의 플랫폼 구현 디테일
- `state-management.md` — Hot reload 가 보존하는 "상태" 의 정의

---

## 7. DevTools / Observability for Developers

<a id="devtools"></a>

**목적**: 개발자가 **개발 중에** 앱 내부 상태(컴포넌트 트리, 네트워크, performance flame chart, memory) 를 들여다보고, 가설 → 검증 → 수정 의 디버깅 루프를 가속한다. production observability(메트릭/트레이스/로그) 와는 사용자(개발자) 와 시점(개발 중) 이 다르다.

**특징**:
- 대표:
  - **Chrome DevTools** — Web (Elements, Console, Network, Performance, Memory, Lighthouse)
  - **React DevTools** — Component tree, props/state inspector, Profiler
  - **Vue DevTools / Redux DevTools** — store time-travel
  - **Flutter DevTools** — Inspector, Performance, Memory, Network, Logging
  - **Android Studio Profiler / Xcode Instruments**
  - **TanStack Query DevTools / SWR DevTools** — server state inspector
- 자매 표준: **Debug Adapter Protocol (DAP)** — debugger 통신 표준 (LSP 의 자매)
- React DevTools 의 *Profiler* 는 commit 별 render 시간을 측정 (production observability 의 trace 와 유사하지만 dev-only)

**장점**:
- 개발 단계에서 production 화 전에 성능 / 메모리 문제 적발
- 비전공자(QA, 디자이너) 도 Chrome DevTools 로 간단한 검증 가능
- Time-travel 디버깅(Redux DevTools) 으로 비결정적 bug 재현
- production observability 까지의 다리 (개발 중 trace_id 확인, sourcemap)

**단점**:
- profiling overhead: dev build 측정값은 production 과 다름
- 학습 곡선: DevTools 의 패널·메뉴가 방대
- 일부 도구는 framework lock-in (React DevTools 는 React 만)
- 모바일 native debugging 은 OS 별로 도구 / 절차가 다 다름

**활용 예시**:
- React 컴포넌트 re-render 폭주 → React DevTools Profiler 로 culprit 식별
- 페이지 LCP 지연 → Chrome DevTools Performance → 메인 스레드 long task 분석
- Flutter 위젯 트리 점검 → Flutter Inspector → widget select / layout overlay
- Redux 상태 변화 추적 → Redux DevTools time-travel
- Memory leak → Chrome DevTools Memory → heap snapshot diff

```kotlin
// Debug Adapter Protocol (DAP) — debugger 도 LSP 와 동일한 분리 사상
// (client = IDE, server = debug adapter, debuggee = 실제 디버그 대상 프로세스)

// ── 1) client → adapter: initialize ──
// { "seq": 1, "type": "request", "command": "initialize",
//   "arguments": { "clientID": "vscode", "linesStartAt1": true } }

// ── 2) client → adapter: launch / attach ──
// { "seq": 2, "type": "request", "command": "launch",
//   "arguments": { "program": "/workspace/app/build/server.jar",
//                  "stopOnEntry": false, "env": { "PROFILE": "dev" } } }

// ── 3) client → adapter: setBreakpoints ──
// { "seq": 3, "type": "request", "command": "setBreakpoints",
//   "arguments": {
//     "source": { "path": "/workspace/app/src/Order.kt" },
//     "breakpoints": [ { "line": 42 }, { "line": 78 } ]
//   } }

// ── 4) adapter → client: events ──
// { "type": "event", "event": "stopped",
//   "body": { "reason": "breakpoint", "threadId": 1 } }

// adapter 구현은 언어별로 (kotlin-debug-adapter, debugpy for Python, dlv for Go)
// 클라이언트(VS Code / Neovim DAP / IntelliJ DAP) 는 단일 UI 로 모든 언어 디버그

class AcmeKotlinDebugAdapter : DebugAdapter {
    override fun initialize(args: InitializeRequestArguments): Capabilities {
        return Capabilities().apply {
            supportsConditionalBreakpoints = true
            supportsFunctionBreakpoints = false
            supportsConfigurationDoneRequest = true
            supportsSetVariable = true
        }
    }

    override fun setBreakpoints(args: SetBreakpointsArguments): SetBreakpointsResponse {
        // JVM TI / JDWP 호출하여 실제 breakpoint 설치
        // ...
        return SetBreakpointsResponse(args.breakpoints.map { Breakpoint(verified = true) })
    }
}
```

**관련 패턴**:
- [Language Server Protocol](#language-server-protocol) — DAP 는 LSP 의 자매 표준
- [Hot Reload / Fast Refresh](#hot-reload-fast-refresh-dx) — DevTools 와 결합하면 "수정 즉시 결과 + 즉시 측정"
- `observability.md` — 개발자 도구와 production observability 의 차이·연결
- `reliability.md` — DevTools 가 잡지 못하는 production-only 이슈

---

## 8. Internal Developer Portal (Backstage)

<a id="backstage-idp"></a>

**목적**: 회사 안의 모든 서비스·문서·온콜·표준 템플릿을 **단일 portal 한 화면**에서 검색·생성·배포할 수 있게 한다. "golden path" 를 선언적으로 정의하여 신규 서비스 1분 안에 표준대로 부팅 가능.

**특징**:
- 2016 Spotify 내부 프로젝트 → 2020 오픈소스 → CNCF Incubating
- 핵심 구성:
  - **Software Catalog**: 모든 service / library / website / API 를 entity 로 등록 (`catalog-info.yaml`)
  - **Software Templates**: scaffolding 의 portal 화. 사용자가 form 입력 → 새 repo + CI + 배포 자동 생성
  - **TechDocs**: docs-as-code (Markdown in repo) → Backstage UI 로 표시
  - **Plugin 생태계**: Kubernetes, ArgoCD, PagerDuty, Sentry, GitHub Actions, Grafana 등 (200+)
- Humanitec / Cortex / Roadie / Port 같은 SaaS / 상용 IDP 도 동일 사상
- "Platform Engineering" 운동의 대표 도구

**장점**:
- discovery: "이 API 누가 만들었지? 온콜은 누구야?" 에 30초 안에 답
- 표준화: golden path = scaffolding template + CI template + observability template + on-call template
- 점진 도입: 한 plugin 부터 시작 가능 (e.g. Catalog 만 먼저)
- self-service: 개발팀이 platform 팀에 ticket 안 끊고 직접 신규 서비스 부팅
- 메타데이터 중앙화: ownership / SLO / compliance 가 한 곳에 모임

**단점**:
- 초기 setup 부담: React 앱 운영 + plugin 통합 + entity 메타데이터 정합성 유지
- "또 하나의 system" — 다른 시스템(GitHub, Jira, PagerDuty) 과의 sync 가 stale 되기 쉬움
- 사용자가 직접 안 들르면(GitHub / Slack 안 떠나면) 효용 낮음
- plugin 품질 격차: 공식 / 커뮤니티 / 사내 fork 가 섞임
- 작은 조직에는 over-engineering (서비스 < 10개 면 wiki 한 페이지로 충분할 수도)

**활용 예시**:
- Software Template: "Kotlin Spring 서비스 신규 생성" 폼 → 새 GitHub repo + CI + ArgoCD + PagerDuty + Grafana dashboard 일괄 생성
- Catalog: 모든 서비스에 owner / tier / lifecycle / dependsOn 메타데이터
- TechDocs: 서비스 onboarding 문서가 코드와 같은 repo 에 살고 portal 에 자동 publish
- 온콜 통합: PagerDuty plugin 으로 portal 안에서 누가 온콜인지 즉시 확인

```yaml
# Backstage Software Template (template.yaml) — golden path 정의
# 입력: 서비스명 + owner + db kind
# 출력: 새 GitHub repo + CI workflow + Helm chart + Backstage catalog 등록
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: kotlin-spring-service
  title: Kotlin Spring Service (Acme Standard)
  description: "사내 표준 Kotlin Spring 마이크로서비스 생성"
  tags: [kotlin, spring, microservice, golden-path]
spec:
  owner: group:platform
  type: service

  parameters:
    - title: Basic info
      required: [name, owner, db]
      properties:
        name:
          type: string
          pattern: "^[a-z][a-z0-9-]+$"
          title: Service name (kebab-case)
        owner:
          type: string
          title: Owning team
          ui:field: OwnerPicker
          ui:options: { allowedKinds: [Group] }
        db:
          type: string
          title: Database
          enum: [postgres, none]

  steps:
    - id: fetch
      name: Render skeleton
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
          db: ${{ parameters.db }}

    - id: publish
      name: Publish to GitHub
      action: publish:github
      input:
        repoUrl: github.com?repo=${{ parameters.name }}&owner=acme
        defaultBranch: main
        protectDefaultBranch: true

    - id: register
      name: Register in catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps.publish.output.repoContentsUrl }}
        catalogInfoPath: "/catalog-info.yaml"

  output:
    links:
      - title: Open repository
        url: ${{ steps.publish.output.remoteUrl }}
      - title: Open in catalog
        icon: catalog
        entityRef: ${{ steps.register.output.entityRef }}

---
# 함께 commit 되는 catalog-info.yaml — Backstage Software Catalog 등록
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: orders-api
  description: Orders write-side API
  tags: [kotlin, spring]
  annotations:
    github.com/project-slug: acme/orders-api
    pagerduty.com/integration-key: ${PAGERDUTY_KEY}
    grafana/dashboard-selector: "service=orders-api"
spec:
  type: service
  lifecycle: production
  owner: group:orders-team
  system: commerce
  providesApis: [orders-rest-v1]
  dependsOn:
    - component:default/identity-service
    - resource:default/orders-postgres
```

**관련 패턴**:
- [Scaffolding](#scaffolding) — Backstage Software Template = scaffolding 의 portal 화
- [Devcontainer](#devcontainer) — Software Template 결과물에 devcontainer 까지 포함하면 onboarding 완벽
- [DevTools](#devtools) — Backstage 의 Grafana / Kibana plugin 으로 production observability 통합
- `deployment.md` — Backstage golden path 가 표준화하는 배포 패턴 (Blue-Green / Canary 템플릿)
- `../principles/12-factor.md` — golden path 는 12-Factor 의 자동 강제 장치

---

## 정리

- DX Engineering 의 8 패턴은 **개발자 시간을 가장 비싼 자원** 으로 보는 사상에서 출발한다.
- **Scaffolding / Codegen / Backstage** 는 "쓰기 자동화" 축, **LSP / DevTools** 는 "읽기 / 분석 자동화" 축, **Devcontainer / REPL / Hot Reload** 는 "환경 / 피드백 루프 단축" 축.
- 세 축은 서로 결합될 때 가치가 커진다 (e.g. Backstage Template 이 devcontainer + LSP 설정 + DevTools 통합까지 일괄 scaffold).
- DX 투자는 측정하기 어렵지만 **onboarding 시간 / build 시간 / "변경 → 화면 반영" 시간 / 신규 서비스 부팅 시간** 같은 leading indicator 로 추적 가능 (SPACE / DORA 와 결합).
- 작은 조직(< 20명) 은 LSP + Hot Reload + Devcontainer 만으로도 충분. Backstage 는 서비스 30개 이상부터 ROI 명확.
