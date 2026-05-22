# Standards Mapping — 국제 표준 ↔ dev-advisor 카탈로그 매핑

> **목적**: SWEBOK V4 / ACM·IEEE CS2023 / DAMA-DMBOK 2 / OWASP Top 10 / NIST 800-series + ISO 27001 등 권위 표준의 지식 영역(KA, Knowledge Area)이 dev-advisor 6중 카탈로그(patterns / algorithms / languages / security / principles / quality)의 어느 파일·anchor 에 대응하는지 빠르게 lookup 하기 위한 **메타 인덱스**입니다.
>
> **사용법**: "OWASP API Top 10 의 API3:2023 가 dev-advisor 어디에 있는가?" / "SWEBOK V4 의 Software Construction KA 가 다루는 항목이 어디에 매핑되는가?" 같은 질문에 대한 단일 참조 지점.
>
> **포맷 약속**:
> - 각 매핑표 직후 **커버리지 등급** 명시: ✓ 완전 커버 / ◐ 부분 커버 / ✗ 갭(미커버)
> - 한 KA 가 여러 카탈로그 파일·anchor 에 매핑될 수 있음 (n:m 관계)
> - 카탈로그 파일은 `references/<domain>/<file>.md` 의 상대 경로로 표기
> - anchor 참조는 `<file>.md#<anchor-id>` 형식 (anchor 가 없는 파일은 `<file>.md` 만 명시 + `## N.` 항목 번호 보조)
>
> **개정 이력**: 2026-05 (Step 2 t07 P1 신설, 표준 5종 × 카탈로그 ~80 파일 cross-link)

---

## 1. SWEBOK V4 (2024) ↔ dev-advisor 매핑

<a id="swebok-v4-mapping"></a>

[SWEBOK V4](https://www.computer.org/education/bodies-of-knowledge/software-engineering) (IEEE Computer Society, 2024 개정판) 는 소프트웨어 엔지니어링의 합의된 지식 체계를 **15 Knowledge Area** 로 구분합니다. dev-advisor 의 advisor 모드(`recommend / validate / refactor / maintain / security-audit`) 가 표준 KA 의 어느 영역을 다루는지 한눈에 보기 위한 매핑표입니다.

| # | SWEBOK V4 KA | dev-advisor 카탈로그 매핑 (파일#anchor) | 커버리지 |
|---|---|---|---|
| 1 | **Software Requirements** | `patterns/requirements-engineering.md#user-story`, `#invest`, `#moscow`, `#use-case`, `#job-stories`, `#event-storming`, `#example-mapping`, `#gherkin-given-when-then`, `#impact-mapping`, `#three-amigos` + `principles/documentation.md#adr`, `#y-statement-nygard`, `#madr` | ✓ |
| 2 | **Software Architecture** | `patterns/architectural.md` (전체 17 항목 — Layered/Hexagonal/Onion/Clean/MVC/MVP/MVVM/MVI/Flux-Redux/CQRS/EventSourcing/Microservices/SOA/Saga/Strangler/BFF/Micro-Frontend) + `patterns/ddd-strategic.md#ubiquitous-language`~`#separate-ways` + `principles/evolutionary-arch.md#1-fitness-function`~`#8-architecture-as-hypothesis` + `patterns/distributed.md` + `principles/12-factor.md` | ✓ |
| 3 | **Software Design** | `principles/solid.md` + `principles/grasp.md#1-information-expert`~`#9-protected-variations` + `patterns/structural.md` + `patterns/creational.md` + `patterns/behavioral.md` + `principles/micro-principles.md#dry`, `#kiss`, `#yagni`, `#lod`, `#soc`, `#composition-over-inheritance` + `patterns/ddd-tactical.md` | ✓ |
| 4 | **Software Construction** | `principles/refactoring-techniques.md` (전체 ~80 기법) + `principles/code-smells.md` (전체 ~25 smell) + `principles/type-systems.md#1-static-dynamic-typing`~`#10-effect-system` + `patterns/error-handling.md#exception-checked-unchecked`~`#retry-backoff-circuit` + `patterns/legacy-code.md#seam-types`~`#mikado-method` + `languages/` 전체 75 언어 가이드 | ✓ |
| 5 | **Software Testing** | `patterns/testing.md` + `patterns/testing-strategies.md#pyramid-trophy-diamond-honeycomb`, `#chaos-engineering`, `#load-testing`, `#stress-testing`, `#spike-testing`, `#soak-endurance-testing`, `#ab-multivariate-testing`, `#synthetic-monitoring`, `#canary-analysis`, `#shadow-traffic-testing` + `principles/process-metrics.md#4-dora-4-metrics` | ✓ |
| 6 | **Software Engineering Operations** | `patterns/deployment.md` + `patterns/observability.md#three-pillars` + `patterns/finops.md#unit-economics`~`#budget-guardrails` + `principles/resilience-theory.md#1-brittleness-robustness-resilience`~`#8-resilience-4-cornerstones` + `patterns/integration.md` + `patterns/networking.md#tcp-udp`~`#connection-pooling` | ✓ |
| 7 | **Software Maintenance** | `patterns/legacy-code.md` (전체 10 기법) + `principles/refactoring-techniques.md` + `principles/code-smells.md` + `principles/sw-economics.md#9-technical-debt-quadrant` + `patterns/build-versioning.md#semver`, `#calver`, `#zerover` (deprecation 관리) | ✓ |
| 8 | **Software Configuration Management** | `principles/configuration-management.md` (SCMP/Baseline/CCB/FCA/PCA/Variant) + `patterns/build-versioning.md#monorepo`, `#polyrepo`, `#hermetic-build`, `#reproducible-build`, `#dependency-resolution` + `patterns/deployment.md` | ✓ |
| 9 | **Software Engineering Management** | `principles/sw-economics.md#1-function-points`~`#10-reference-class-forecasting` + `principles/process-metrics.md#1-scrum`~`#10-pair-mob-programming` + `principles/scaled-agile.md#safe-framework`~`#team-topologies` + `principles/sdlc-models.md#sdlc-waterfall`~`#sdlc-pmbok` | ✓ |
| 10 | **Software Engineering Process** | `principles/sdlc-models.md` (전체 7 모델) + `principles/scaled-agile.md` (전체 6 프레임워크) + `principles/process-metrics.md` (전체 10 항목) + `principles/professional-ethics.md` | ✓ |
| 11 | **Software Engineering Models & Methods** | `patterns/ddd-strategic.md` + `patterns/ddd-tactical.md` + `principles/evolutionary-arch.md` + `principles/formal-methods.md` (TLA+/Alloy/Hoare/Model Checking/Z) + `patterns/state-management.md` | ◐ (formal methods 영역은 P3 t18 신설 예정) |
| 12 | **Software Quality** | `principles/iso25010.md#usability`, `#reliability`, `#maintainability` (8 품질 특성) + `principles/performance-metrics.md#latency-numbers`~`#apdex-score` + `principles/resilience-theory.md` + `principles/sustainable-sw.md#1-carbon-aware-computing`~`#8-efficient-data-storage` | ✓ |
| 13 | **Software Security** | `security/index.md` (전체 14 파일 / 106 항목) — `security-authn.md`, `security-authz.md`, `security-api-web.md`, `security-mobile.md`, `security-ai-model.md`, `security-crypto-ops.md`, `security-data-protection.md`, `security-supply-chain.md`, `security-sdlc.md`, `security-detect-respond.md`, `security-platform.md`, `privacy-engineering.md`, `compliance.md` | ✓ |
| 14 | **Software Engineering Professional Practice** | `principles/professional-ethics.md#acm-code-ethics-2018`, `#ieee-code-ethics`, `#se-code-ethics-1999`, `#eu-ai-act-2024`, `#gdpr-article-22`, `#dark-pattern-classification` + `principles/documentation.md` + `principles/sustainable-sw.md` | ✓ |
| 15 | **Software Engineering Economics** | `principles/sw-economics.md` (전체 10 항목 — Function Points / COCOMO II / Story Point / Planning Poker / T-shirt Sizing / WSJF / RICE / Cost of Delay / Technical Debt / Reference Class) + `patterns/finops.md` (전체 9 항목) | ✓ |

**갭 분석**:
- ◐ **Software Engineering Models & Methods (KA 11)**: Formal methods (TLA+/Alloy 등) 는 P3 t18 (`principles/formal-methods.md`) 신설 시 ✓ 로 격상 예정
- 그 외 14 KA 모두 **✓ 완전 커버** — dev-advisor 는 SWEBOK V4 의 사실상 전 범위를 다룬다.

---

## 2. ACM/IEEE Computing Curricula 2023 (CS2023) ↔ dev-advisor 매핑

<a id="cs2023-mapping"></a>

[Computing Curricula 2023 (CS2023)](https://csed.acm.org/) 는 ACM·IEEE-CS·AAAI 공동 발표 학부 컴퓨터과학 교과과정 권고 표준으로, 17 Knowledge Area (+ 통합 Mathematical Foundations) 를 정의합니다. dev-advisor 는 응용 엔지니어링 중심이라 일부 이론 KA (FPL, MSF) 는 부분 커버입니다.

| # | CS2023 KA | dev-advisor 카탈로그 매핑 | 커버리지 |
|---|---|---|---|
| 1 | **AI — Artificial Intelligence** | `algorithms/ml.md#k-means`~`#node2vec` (13 알고리즘) + `patterns/ai-llm.md` + `security/security-ai-model.md` (5 항목) + `algorithms/game-ai.md` | ✓ |
| 2 | **AL — Algorithmic Foundations** | `algorithms/index.md` 전체 (`sorting.md`, `searching.md`, `dynamic-programming.md`, `greedy.md`, `divide-conquer.md`, `backtracking.md`, `flow.md`, `geometry.md`, `string.md`, `math.md`, `probabilistic.md`) + `principles/performance-metrics.md#big-o-practical` | ✓ |
| 3 | **AR — Architecture & Organization** | `algorithms/os-foundations.md#mark-sweep-gc`~`#mesi-cache-coherence` + `algorithms/concurrent.md#cas`~`#aba-problem` + `principles/performance-metrics.md#latency-numbers` | ✓ |
| 4 | **DM — Data Management** | `data-advisor:principles/db-fundamentals.md#tx-isolation-levels`~`#db-partitioning` + `data-advisor:algorithms/db-indexes.md` + `data-advisor:algorithms/db-storage-engines.md` + `patterns/data-modeling.md#cap-theorem`~`#data-mesh-lakehouse` + `patterns/data-access.md` + `data-advisor:patterns/mdm.md` + `data-advisor:patterns/data-quality.md` + `data-advisor:patterns/data-warehousing.md` (P1 t10 신설) + `data-advisor:algorithms/db-query-optimizer.md` (P2 t11 신설) | ✓ |
| 5 | **FPL — Foundations of Programming Languages** | `principles/type-systems.md#1-static-dynamic-typing`~`#10-effect-system` (10 항목) + `languages/` 75 언어 + `algorithms/parsing.md` | ◐ (람다 칼큘러스·denotational semantics 같은 순수 이론은 미커버, 응용 중심) |
| 6 | **GIT — Graphics & Interactive Techniques** | `patterns/graphics-rendering.md` (P2 t15a 신설 — Rasterization/RayTracing/Z-buffering/PBR/Forward vs Deferred) + `patterns/ar-vr-xr.md` (P2 t15b 신설) + `patterns/game-dev.md` + `algorithms/spatial.md` + `algorithms/signal-processing.md` + `algorithms/image-processing.md` | ✓ |
| 7 | **HCI — Human-Computer Interaction** | `principles/hci-methodology.md` (P3 t17 신설 — Persona/Journey Map/Card Sort/Think-Aloud/Heuristic Eval/Cognitive Walkthrough) + `patterns/ui-ux.md#a11y-wcag`, `#i18n`, `#responsive-adaptive`, `#design-tokens` | ✓ |
| 8 | **HS — Human Security** | `security/privacy-engineering.md#consent-ledger`~`#privacy-operations` + `principles/professional-ethics.md#dark-pattern-classification`, `#gdpr-article-22`, `#eu-ai-act-2024` + `security/compliance.md` (GDPR/CCPA/HIPAA) | ✓ |
| 9 | **MSF — Mathematical & Statistical Foundations** | `algorithms/math.md` + `algorithms/probabilistic.md` + `algorithms/ml.md` (통계 기법) | ◐ (이산수학·선형대수 이론 자체는 미커버, 알고리즘 응용 중심) |
| 10 | **NC — Networking & Communication** | `patterns/networking.md#tcp-udp`~`#connection-pooling` (12 항목) + `algorithms/load-balancing.md` (8 알고리즘) + `algorithms/distributed.md#gossip-protocol`, `#swim`, `#anti-entropy` | ✓ |
| 11 | **OS — Operating Systems** | `algorithms/os-foundations.md` (전체 ~30 알고리즘 — GC/스케줄러/메모리관리/IO) + `algorithms/concurrent.md` + `principles/concurrency-theory.md` | ✓ |
| 12 | **PDC — Parallel & Distributed Computing** | `algorithms/distributed.md#lamport-clock`~`#quorum` + `algorithms/consensus.md#2pc`, `#paxos`, `#raft` + `patterns/distributed.md` + `principles/concurrency-theory.md#linearizability`~`#race-condition` + `patterns/hpc-scientific.md` (P3 t19 신설 — MPI/OpenMP/CUDA HPC/Slurm/BLAS-LAPACK/NUMA) | ✓ |
| 13 | **SDF — Software Development Fundamentals** | `principles/micro-principles.md` (전체 ~15 원칙) + `principles/solid.md` + `principles/grasp.md` + `principles/code-smells.md` + `principles/refactoring-techniques.md` | ✓ |
| 14 | **SE — Software Engineering** | (= SWEBOK V4 ↔ §1 매핑표 전체 참조) | ✓ |
| 15 | **SEC — Security** | `security/index.md` 전체 (14 파일 / 106 항목) — §4 OWASP / §5 NIST 매핑 참조 | ✓ |
| 16 | **SEP — Society, Ethics, Professionalism** | `principles/professional-ethics.md` (전체 6 항목) + `principles/sustainable-sw.md` (전체 8 항목 — Carbon-aware / SCI / Green Software) | ✓ |
| 17 | **SPD — Specialized Platform Development** | `patterns/mobile-app.md#app-lifecycle`~`#battery-profiling` (13 항목) + `patterns/embedded.md` + `patterns/web-rendering.md` + `patterns/crossplatform.md` + `patterns/serverless-faas.md` (P2 t15c 신설) + `patterns/blockchain.md` | ✓ |

**갭 분석**:
- ◐ **FPL — Foundations of Programming Languages**: 람다 칼큘러스·denotational/operational semantics 등 순수 이론 미커버 — 응용 개발자 advisor 특성상 의도된 갭
- ◐ **MSF — Mathematical & Statistical Foundations**: 이산수학·선형대수 이론 자체는 미커버 — `algorithms/math.md` 가 실용 알고리즘으로 커버
- 그 외 15 KA **✓ 완전 커버** (Mathematical Foundations 통합 KA 포함 시 17/18)

---

## 3. DAMA-DMBOK 2 (Data Management Body of Knowledge, 2nd Ed.) ↔ dev-advisor 매핑

<a id="dmbok-mapping"></a>

[DAMA-DMBOK 2](https://www.dama.org/cpages/body-of-knowledge) 는 데이터 관리 전문 협회 DAMA International 이 발표한 데이터 관리 표준 지식체계로 **11 Knowledge Area** + Data Governance (Umbrella) 로 구성됩니다. dev-advisor 의 데이터/DB 카테고리(#4) P0 보강 후 거의 완전 커버.

| # | DMBOK 2 KA | dev-advisor 카탈로그 매핑 | 커버리지 |
|---|---|---|---|
| 0 | **Data Governance (Umbrella)** | `data-advisor:patterns/data-quality.md#dq-stewardship-raci`, `#data-lineage`, `#data-catalog`, `#openlineage-standard` + `principles/professional-ethics.md#gdpr-article-22` + `security/privacy-engineering.md#dpia`, `#purpose-binding`, `#retention-policy` | ✓ |
| 1 | **Data Architecture** | `patterns/data-modeling.md#cap-theorem`, `#pacelc`, `#consistency-models-systems`, `#sharding-partitioning`, `#consistent-hashing-sharding`, `#data-mesh-lakehouse` + `data-advisor:patterns/data-warehousing.md` (P1 t10) | ✓ |
| 2 | **Data Modeling & Design** | `patterns/data-modeling.md` (전체 12 항목) + `data-advisor:principles/db-fundamentals.md#normalization-1nf-bcnf` + `data-advisor:patterns/mdm.md#mdm-hierarchy` | ✓ |
| 3 | **Data Storage & Operations** | `patterns/data-access.md` — DB 인덱스/스토리지/쿼리 최적화 상세는 data-advisor 스킬 참조 | ✓ |
| 4 | **Data Security** | `security/security-data-protection.md` (8 항목 — 암호화/토큰화/마스킹/익명화/차분프라이버시/Confidential Computing) + `security/privacy-engineering.md` + `security/security-crypto-ops.md` | ✓ |
| 5 | **Data Integration & Interoperability** | `patterns/integration.md` + `patterns/streaming-semantics.md#1-delivery-semantics`~`#9-backpressure-stream` + `patterns/data-modeling.md#cdc`, `#materialized-view`, `#lambda-kappa-htap` + `patterns/api-design.md` + `patterns/api-styles.md` | ✓ |
| 6 | **Document & Content Management** | `algorithms/search-systems.md#inverted-index`, `#tf-idf`, `#bm25`, `#vector-search`, `#hybrid-search`, `#faceted-search`, `#autocomplete`, `#learning-to-rank` + `principles/documentation.md` | ✓ |
| 7 | **Reference & Master Data Management** | `patterns/ddd-tactical.md#aggregate` (MDM 경계 식별 기반) — MDM 6 패턴은 data-advisor 스킬 참조 | ✓ |
| 8 | **Data Warehousing & Business Intelligence** | `data-advisor:patterns/data-warehousing.md` (P1 t10 신설 — Kimball/SCD/Fact Table/OLAP/Lakehouse/dbt) + `patterns/data-modeling.md#lambda-kappa-htap`, `#data-mesh-lakehouse` | ✓ |
| 9 | **Metadata Management** | `data-advisor:patterns/data-quality.md#data-catalog`, `#data-lineage`, `#openlineage-standard` + `patterns/mlops.md#model-card`, `#data-contract` | ✓ |
| 10 | **Data Quality** | `data-advisor:patterns/data-quality.md#dq-6-dimensions`, `#dq-validation-tools` (P0 t04b 신설 — 6 dimensions: Accuracy/Completeness/Consistency/Timeliness/Uniqueness/Validity) + `patterns/mlops.md#data-drift`, `#data-contract` | ✓ |
| 11 | **Big Data & Data Science** | `patterns/mlops.md#feature-store`~`#model-monitoring` (10 항목) + `algorithms/ml.md` (13 알고리즘) + `patterns/data-modeling.md#lambda-kappa-htap` + `patterns/streaming-semantics.md` | ✓ |

**갭 분석**:
- 11 KA + Data Governance Umbrella **✓ 완전 커버** — P0 t04a/t04b/t01 + P1 t10 + P2 t11 신설로 DMBOK 2 전 범위 매핑 완료
- 가장 강한 영역: **Data Storage & Operations** (DB 엔진 내부 + 인덱스 + 쿼리 옵티마이저 깊이 있게 커버)
- 보강 권장: **Data Architecture** 의 데이터 패브릭(Data Fabric) 항목 — 현재 `data-mesh-lakehouse` 가 부분 대체

---

## 4. OWASP Top 10 (Web / API / Mobile / LLM) ↔ dev-advisor 매핑

<a id="owasp-top10-mapping"></a>

OWASP Foundation 의 4 종 Top 10 — [Web 2021](https://owasp.org/Top10/) / [API 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) / [Mobile 2024](https://owasp.org/www-project-mobile-top-10/) / [LLM 2025](https://genai.owasp.org/llm-top-10/) — 의 각 카테고리가 dev-advisor `security/` 카탈로그의 어느 항목으로 방어 가이드를 제공하는지 4 표로 정리합니다.

### 4-1. OWASP Web Top 10 (2021)

| 코드 | 카테고리 | dev-advisor 매핑 | 커버리지 |
|---|---|---|---|
| A01 | Broken Access Control | `security/security-authz.md` §1 RBAC / §2 ABAC / §3 ReBAC / §4 OPA / §5 Permission Boundary / §6 Least Privilege / §7 JWT Claims + `security/security-api-web.md` §3 IDOR/BOLA | ✓ |
| A02 | Cryptographic Failures | `security/security-crypto-ops.md` §1 KMS / §2 HSM / §3 Envelope / §4 Rotation / §5 PFS / §6 PQC / §7 Crypto Agility + `security/security-data-protection.md` §1 Encryption at Rest | ✓ |
| A03 | Injection | `security/security-api-web.md` §5 XXE / §8 Mass Assignment + `data-advisor:principles/db-fundamentals.md` (parameterized query 가이드) + `patterns/api-design.md#10-resource-naming` | ✓ |
| A04 | Insecure Design | `security/security-sdlc.md` §1 Threat Modeling (STRIDE/DREAD/PASTA) + `principles/evolutionary-arch.md#1-fitness-function` (security fitness function) | ✓ |
| A05 | Security Misconfiguration | `security/security-platform.md` §1 Pod Security / §3 Network Policy / §6 IaC Scanning / §7 CIS Benchmark + `patterns/build-versioning.md#hermetic-build` | ✓ |
| A06 | Vulnerable & Outdated Components | `security/security-supply-chain.md` §1 SBOM / §5 Provenance (in-toto) + `security/security-sdlc.md` §5 SCA | ✓ |
| A07 | Identification & Authentication Failures | `security/security-authn.md` §1 OAuth2 PKCE / §2 OIDC / §3 SAML / §4 FIDO2-WebAuthn-Passkeys / §5 MFA / §6 Device Flow / §7 Magic Link / §8 Social Login | ✓ |
| A08 | Software & Data Integrity Failures | `security/security-supply-chain.md` §2 Sigstore/Cosign / §3 SLSA / §4 Reproducible Build / §5 Provenance Attestation | ✓ |
| A09 | Security Logging & Monitoring Failures | `security/security-detect-respond.md` §1 SIEM / §3 Audit Log Tamper-Evident / §4 UEBA + `patterns/observability.md#three-pillars` | ✓ |
| A10 | Server-Side Request Forgery (SSRF) | `security/security-api-web.md` §4 SSRF 방어 | ✓ |

**커버리지**: OWASP Web Top 10 (2021) **10/10 ✓ 완전 커버**

### 4-2. OWASP API Security Top 10 (2023)

| 코드 | 카테고리 | dev-advisor 매핑 | 커버리지 |
|---|---|---|---|
| API1 | Broken Object Level Authorization (BOLA) | `security/security-api-web.md` §3 IDOR/BOLA + `security/security-authz.md` §3 ReBAC | ✓ |
| API2 | Broken Authentication | `security/security-authn.md` 전체 (8 항목) | ✓ |
| API3 | Broken Object Property Level Authorization | `security/security-api-web.md` §8 Mass Assignment + `security/security-authz.md` §2 ABAC (속성 단위 정책) | ✓ |
| API4 | Unrestricted Resource Consumption | `security/security-api-web.md` §1 per-Identity Rate Limiting + `patterns/api-design.md#12-api-rate-limiting` | ✓ |
| API5 | Broken Function Level Authorization | `security/security-authz.md` §1 RBAC / §4 OPA / §6 Least Privilege | ✓ |
| API6 | Unrestricted Access to Sensitive Business Flows | `security/security-detect-respond.md` §4 UEBA + `security/security-api-web.md` §1 Rate Limiting (per-flow) | ◐ (비즈니스 흐름별 ML 탐지는 부분) |
| API7 | Server-Side Request Forgery | `security/security-api-web.md` §4 SSRF 방어 | ✓ |
| API8 | Security Misconfiguration | `security/security-platform.md` §6 IaC Scanning / §7 Hardening Baseline | ✓ |
| API9 | Improper Inventory Management | `patterns/api-design.md#4-api-versioning`, `#14-api-deprecation-sunset` + `security/security-supply-chain.md` §1 SBOM | ✓ |
| API10 | Unsafe Consumption of APIs | `security/security-api-web.md` §4 SSRF + `patterns/api-design.md#13-webhook-async-api` (verified webhook) | ✓ |

**커버리지**: OWASP API Top 10 (2023) **9.5/10 (9 ✓ + 1 ◐)** — API6 의 비즈니스 흐름별 ML 이상 탐지가 부분 커버

### 4-3. OWASP Mobile Top 10 (2024)

| 코드 | 카테고리 | dev-advisor 매핑 | 커버리지 |
|---|---|---|---|
| M1 | Improper Credential Usage | `security/security-mobile.md` §5 Secure Storage + `security/security-authn.md` §4 Passkeys | ✓ |
| M2 | Inadequate Supply Chain Security | `security/security-supply-chain.md` 전체 (8 항목) | ✓ |
| M3 | Insecure Authentication / Authorization | `security/security-mobile.md` §2 App Attest / Play Integrity + `security/security-authn.md` + `security/security-authz.md` | ✓ |
| M4 | Insufficient Input/Output Validation | `security/security-api-web.md` §5 XXE / §8 Mass Assignment + `patterns/error-handling.md#exception-checked-unchecked` | ✓ |
| M5 | Insecure Communication | `security/security-mobile.md` §1 Certificate Pinning + `patterns/networking.md#tls-handshake` + `security/security-crypto-ops.md` §5 PFS | ✓ |
| M6 | Inadequate Privacy Controls | `security/privacy-engineering.md#dsar`, `#purpose-binding`, `#data-minimization` + `patterns/mobile-app.md#permission-ux` | ✓ |
| M7 | Insufficient Binary Protections | `security/security-mobile.md` §3 Jailbreak/Root Detection / §4 RASP + `patterns/mobile-app.md#app-signing` | ✓ |
| M8 | Security Misconfiguration | `security/security-platform.md` §7 Hardening Baseline + `patterns/mobile-app.md#app-startup` | ✓ |
| M9 | Insecure Data Storage | `security/security-mobile.md` §5 Secure Storage + `security/security-data-protection.md` §2 Field-level Encryption / §6 Pseudonymization | ✓ |
| M10 | Insufficient Cryptography | `security/security-crypto-ops.md` §6 PQC / §7 Crypto Agility + `security/security-mobile.md` §1 Certificate Pinning | ✓ |

**커버리지**: OWASP Mobile Top 10 (2024) **10/10 ✓ 완전 커버**

### 4-4. OWASP LLM Top 10 (2025)

| 코드 | 카테고리 | dev-advisor 매핑 | 커버리지 |
|---|---|---|---|
| LLM01 | Prompt Injection | `security/security-ai-model.md` §4 Adversarial Inputs/Evasion + `patterns/ai-llm.md` (input/output filter 패턴) | ✓ |
| LLM02 | Sensitive Information Disclosure | `security/security-ai-model.md` §2 Membership Inference + `security/privacy-engineering.md#data-minimization` + `security/security-data-protection.md` §7 Differential Privacy | ✓ |
| LLM03 | Supply Chain | `security/security-supply-chain.md` §7 Slopsquatting / §8 AI-Assisted Code Secret Leak + `security/security-ai-model.md` §3 Data Poisoning | ✓ |
| LLM04 | Data & Model Poisoning | `security/security-ai-model.md` §3 Data Poisoning / §5 Federated Learning 보안 | ✓ |
| LLM05 | Improper Output Handling | `security/security-api-web.md` §5 XXE / §8 Mass Assignment + `patterns/ai-llm.md` (output validator) | ✓ |
| LLM06 | Excessive Agency | `security/security-authz.md` §6 Least Privilege (Just-Enough-Access) + `patterns/ai-llm.md` (tool permission gating) | ✓ |
| LLM07 | System Prompt Leakage | `security/security-ai-model.md` §1 Model Extraction/Theft + `security/privacy-engineering.md#purpose-binding` | ✓ |
| LLM08 | Vector & Embedding Weakness | `algorithms/ml.md#hnsw`, `#quantization` + `algorithms/search-systems.md#vector-search`, `#hybrid-search` + `security/security-ai-model.md` §2 Membership Inference | ✓ |
| LLM09 | Misinformation | `security/security-ai-model.md` §3 Data Poisoning + `patterns/mlops.md#model-monitoring`, `#data-drift`, `#concept-drift` | ✓ |
| LLM10 | Unbounded Consumption | `security/security-api-web.md` §1 per-Identity Rate Limiting + `patterns/finops.md#unit-economics` (LLM 토큰 비용 가드레일) | ✓ |

**커버리지**: OWASP LLM Top 10 (2025) **10/10 ✓ 완전 커버**

---

## 5. NIST 800-series + ISO 27001/27017/27018 ↔ dev-advisor 매핑

<a id="nist-iso-mapping"></a>

미국 NIST(National Institute of Standards and Technology) 의 컴퓨터 보안 표준(800-series) 과 ISO/IEC 정보보안 인증 표준(27001/27017/27018) 이 dev-advisor 의 어느 영역에 대응하는지 통합 정리합니다.

### 5-1. NIST 800-series 매핑

| 표준 | 제목 | dev-advisor 매핑 | 커버리지 |
|---|---|---|---|
| **SP 800-53 Rev.5** | Security and Privacy Controls for Information Systems and Organizations | `security/security-platform.md` §7 Hardening Baseline / §6 IaC Scanning + `security/compliance.md` §5 SOC 2 + `security/security-authz.md` 전체 + `security/security-data-protection.md` 전체 + `security/privacy-engineering.md` 전체 | ✓ |
| **SP 800-63B** | Digital Identity Guidelines — Authentication & Lifecycle Management | `security/security-authn.md` §1 OAuth2 PKCE / §4 FIDO2-WebAuthn-Passkeys / §5 MFA / §6 Device Flow + `security/security-crypto-ops.md` §8 OPAQUE/aPAKE | ✓ |
| **SP 800-63C** | Digital Identity Guidelines — Federation & Assertions | `security/security-authn.md` §2 OIDC / §3 SAML / §8 Social Login | ✓ |
| **SP 800-171** | Protecting CUI in Nonfederal Systems | `security/security-data-protection.md` 전체 (8 항목) + `security/compliance.md` §4 HIPAA / §5 SOC 2 + `security/security-authz.md` §6 Least Privilege | ✓ |
| **SP 800-207** | Zero Trust Architecture | `security/security-authz.md` §1 RBAC / §2 ABAC / §3 ReBAC / §4 OPA / §5 Permission Boundary / §6 Least Privilege + `security/security-platform.md` §3 Network Policy + `security/security-authn.md` (continuous auth) | ✓ |
| **SP 800-218** | Secure Software Development Framework (SSDF v1.1) | `security/security-sdlc.md` 전체 (6 항목 — Threat Modeling/SAST/DAST/IAST/SCA/Secret Scan) + `security/security-supply-chain.md` 전체 + `principles/sdlc-models.md` | ✓ |
| **SP 800-61 Rev.2** | Computer Security Incident Handling Guide | `security/security-detect-respond.md` §6 Incident Response Playbook (이 항목이 SP 800-61 Rev.2 를 직접 인용) + §1 SIEM / §2 SOAR | ✓ |
| **SP 800-115** | Technical Guide to Information Security Testing and Assessment | `security/security-sdlc.md` §2 SAST / §3 DAST / §4 IAST + `patterns/testing-strategies.md#chaos-engineering` | ✓ |
| **SP 800-145** | NIST Definition of Cloud Computing | `patterns/finops.md` + `patterns/serverless-faas.md` (P2 t15c) + `security/security-platform.md` | ◐ (정의서 자체는 매핑 항목 적음) |
| **SP 800-37 Rev.2** | Risk Management Framework (RMF) | `security/security-sdlc.md` §1 Threat Modeling + `security/compliance.md` + `principles/sdlc-models.md` | ◐ (RMF 6 단계 프로세스 직접 항목은 없음, 분산 커버) |

**커버리지**: 10 핵심 표준 중 **8 ✓ + 2 ◐**

### 5-2. ISO/IEC 정보보안 표준 매핑

| 표준 | 제목 | dev-advisor 매핑 | 커버리지 |
|---|---|---|---|
| **ISO/IEC 27001:2022** | Information Security Management Systems (ISMS) | `security/index.md` 전체 (14 파일) + `security/compliance.md` §5 SOC 2 + `security/security-platform.md` §7 Hardening Baseline | ✓ |
| **ISO/IEC 27002:2022** | Information Security Controls (93 controls) | `security/security-authn.md` + `security/security-authz.md` + `security/security-data-protection.md` + `security/security-crypto-ops.md` + `security/security-detect-respond.md` + `security/privacy-engineering.md` (controls 분산 매핑) | ✓ |
| **ISO/IEC 27017** | Cloud Services Security Code of Practice | `security/security-platform.md` (Pod Security/Network Policy/IaC Scanning/Falco/CIS Benchmark) + `security/security-supply-chain.md` (cloud-native SBOM/SLSA) | ✓ |
| **ISO/IEC 27018** | Protection of PII in Public Clouds (Cloud Processor 가이드) | `security/privacy-engineering.md#consent-ledger`, `#dsar`, `#retention-policy`, `#data-minimization`, `#dpia` + `security/security-data-protection.md` §6 Pseudonymization / §7 Differential Privacy + `security/compliance.md` §1 GDPR / §2 CCPA | ✓ |
| **ISO/IEC 27701:2019** | Privacy Information Management System (ISMS 의 PIMS 확장) | `security/privacy-engineering.md` 전체 (9 항목) + `principles/professional-ethics.md#gdpr-article-22` + `security/compliance.md` §1 GDPR | ✓ |
| **ISO/IEC 25010:2023** | Systems and Software Quality Models (Quality in Use + Product Quality) | `principles/iso25010.md` (이 파일이 ISO/IEC 25010 직접 인용 — Functional Suitability / Performance Efficiency / Compatibility / Interaction Capability / Reliability / Security / Maintainability / Flexibility / Safety) | ✓ |
| **ISO 9241-210** | Human-Centred Design for Interactive Systems | `principles/hci-methodology.md` (P3 t17) + `patterns/ui-ux.md#a11y-wcag` | ✓ |
| **ISO/IEC 12207:2017** | Software Life Cycle Processes | `principles/sdlc-models.md` (전체 7 모델) + `principles/process-metrics.md` + `principles/scaled-agile.md` | ✓ |
| **ISO/IEC 42001:2023** | AI Management System (AIMS) | `security/security-ai-model.md` + `principles/professional-ethics.md#eu-ai-act-2024` + `patterns/mlops.md#model-card`, `#model-monitoring` | ✓ |

**커버리지**: ISO 9 표준 **✓ 완전 커버**

### 5-3. 통합 갭 분석

- **◐ 부분 커버 (2 항목)**:
  1. **NIST SP 800-145 (Cloud Computing 정의서)** — 정의서 특성상 매핑 항목 적음, `patterns/finops.md` + `patterns/serverless-faas.md` 가 응용 영역 커버
  2. **NIST SP 800-37 Rev.2 (RMF)** — 6 단계 리스크 관리 프레임워크 직접 항목 없음, 분산 커버. RMF 명시 페이지가 필요하면 `security/security-sdlc.md` 에 §7 RMF 항목 신설 고려
- **✗ 완전 갭**: 없음. NIST 800-series 핵심 + ISO 9 표준 모두 ✓ 또는 ◐ 로 최소 부분 커버

---

## 6. ISO/IEC 25010:2023 8 특성 분해 매핑

<a id="iso25010-detail-mapping"></a>

5-2 표는 ISO/IEC 25010:2023 을 단일 행으로 묶었지만, *Product Quality Model* 의 8 특성을 개별 코드로 분해해 `principles/iso25010.md` 의 8 섹션 anchor 와 1:1 매핑하고, 각 특성을 보강하는 외부 카탈로그 항목을 함께 표기합니다. lookup 단위 정확도를 위해 추가합니다.

| 코드 | 특성 (Characteristic) | dev-advisor 매핑 | 커버리지 |
|---|---|---|---|
| FS | Functional Suitability (기능 적합성) | `principles/iso25010.md` + `patterns/api-design.md` + `patterns/testing-strategies.md` | ✓ |
| PE | Performance Efficiency (성능 효율성) | `principles/iso25010.md` + `principles/performance-metrics.md` + `patterns/caching.md` | ✓ |
| CO | Compatibility (호환성) | `principles/iso25010.md` + `patterns/api-design.md` + `patterns/integration.md` | ✓ |
| US | Usability (사용성) | `principles/iso25010.md#usability` + `principles/hci-methodology.md` + `patterns/ui-ux.md` | ✓ |
| RE | Reliability (신뢰성) | `principles/iso25010.md#reliability` + `principles/resilience-theory.md` + `patterns/error-handling.md` | ✓ |
| SE | Security (보안) | `principles/iso25010.md` + `security/index.md` | ✓ |
| MA | Maintainability (유지보수성) | `principles/iso25010.md#maintainability` + `principles/code-smells.md` + `principles/refactoring-techniques.md` + `principles/solid.md` | ✓ |
| PO | Portability (이식성) | `principles/iso25010.md` + `patterns/build-versioning.md` + `patterns/deployment.md` | ✓ |

**커버리지**: ISO/IEC 25010:2023 Product Quality Model **8/8 ✓ 완전 커버**

> 비고: 2023 개정에서 Usability 는 **Interaction Capability** 로, Portability 의 일부는 **Flexibility** 로 재구성됐고 **Safety** 가 새 특성으로 추가됐습니다. 본 표는 기존 명명을 유지하되 신규 특성은 향후 reference 확장 시 추가합니다.

---

## 7. DORA 4 Key Metrics ↔ dev-advisor 매핑

<a id="dora-mapping"></a>

DORA (DevOps Research and Assessment) *State of DevOps Report* 가 통계적으로 검증한 **SW 전달 4 메트릭**을 측정·개선 actionable 카탈로그 항목으로 매핑합니다. 메트릭 정의 본문은 `principles/process-metrics.md#4-dora-4-metrics` 단일 source 이고, 본 표는 각 메트릭을 *개선하는* 카탈로그 자산을 가리킵니다.

| 코드 | 메트릭 | dev-advisor 매핑 | 커버리지 |
|---|---|---|---|
| DF | Deployment Frequency | `principles/process-metrics.md#4-dora-4-metrics` + `principles/process-metrics.md#6-trunk-based-development` + `principles/process-metrics.md#7-gitops` + `patterns/deployment.md` | ✓ |
| LT | Lead Time for Changes | `principles/process-metrics.md#4-dora-4-metrics` + `principles/process-metrics.md#6-trunk-based-development` + `principles/refactoring-techniques.md` + `patterns/build-versioning.md` | ✓ |
| MTTR | Mean Time To Restore | `principles/process-metrics.md#4-dora-4-metrics` + `patterns/error-handling.md` + `security/security-detect-respond.md#6-incident-response-playbook` + `patterns/observability.md` | ✓ |
| CFR | Change Failure Rate | `principles/process-metrics.md#4-dora-4-metrics` + `patterns/testing-strategies.md` + `principles/evolutionary-arch.md#1-fitness-function` + `patterns/deployment.md` | ✓ |

**커버리지**: DORA 4 Key Metrics **4/4 ✓ 완전 커버**

> 보조: 2021~2022 보고서가 추가한 5번째 메트릭 *Reliability (SLO 달성률)* 는 `patterns/observability.md` 및 `principles/resilience-theory.md` 가 SLI/SLO 패턴으로 커버 — 표 외 부록.

---

## Cross-link Summary (역방향 인덱스)

본 매핑 파일이 가장 자주 참조하는 카탈로그 파일 Top 15 (출현 빈도순):

1. `security/security-authn.md` — §1 / §4-1 A07 / §4-2 API2 / §4-3 M3 / §5-1 SP 800-63B,C
2. `security/security-authz.md` — §1 / §4-1 A01 / §4-2 API1,3,5 / §5-1 SP 800-207
3. `security/security-api-web.md` — §1 / §4-2 API4,7,10 / §4-3 M4 / §4-4 LLM05
4. `security/security-data-protection.md` — §3 KA4 / §4-1 A02 / §4-3 M9 / §5-1 SP 800-171
5. `security/security-crypto-ops.md` — §1 / §4-1 A02 / §4-3 M5,M10
6. `security/security-supply-chain.md` — §4-1 A06,A08 / §4-3 M2 / §4-4 LLM03 / §5-1 SP 800-218
7. `security/security-sdlc.md` — §1 / §4-1 A04 / §5-1 SP 800-218
8. `security/security-detect-respond.md` — §1 / §4-1 A09 / §5-1 SP 800-61
9. `security/security-ai-model.md` — §2 KA1 / §4-4 LLM 전체 / §5-2 ISO 42001
10. `security/privacy-engineering.md` — §2 KA8 / §3 KA0 / §5-2 ISO 27018,27701
11. `patterns/data-modeling.md` — §1 KA2 / §3 KA1,2,5
12. `patterns/api-design.md` — §1 KA1 / §4-2 API4,9,10
13. `principles/iso25010.md` — §1 KA12 / §5-2 ISO 25010
14. `principles/sdlc-models.md` — §1 KA10 / §2 KA14 / §5-2 ISO 12207
15. `data-advisor:algorithms/db-storage-engines.md` — §2 KA4 / §3 KA3

**총 cross-link 카운트** (본 파일 → 카탈로그): 약 **85+ 파일** 참조 (5 표준 × 평균 ~17 KA × 평균 ~3 카탈로그 매핑)

---

## 변경 추적

- 2026-05-16 (Step 2 t07) 초안 — 5 표준(SWEBOK V4 / CS2023 / DMBOK 2 / OWASP / NIST·ISO) × dev-advisor 6중 카탈로그 매핑 메타 인덱스 신설
- 신규 anchor 5개 (`swebok-v4-mapping`, `cs2023-mapping`, `dmbok-mapping`, `owasp-top10-mapping`, `nist-iso-mapping`)
- 사전 anchor 충돌 검사: 0 충돌 확인 (`grep -r '<a id='` 전체 카탈로그 대비)
- P0 신설 카탈로그(`database-fundamentals.md` / `sdlc-models.md` / `scaled-agile.md` / `master-data-management.md` / `data-quality-governance.md` / `professional-ethics.md`) 반영
- P1~P3 예정 카탈로그(`web-performance.md` / `configuration-management.md` / `data-warehousing-bi.md` / `db-query-optimizer.md` / `graphics-rendering.md` / `ar-vr-xr.md` / `serverless-faas.md` / `hci-methodology.md` / `formal-methods.md` / `hpc-scientific.md`) 도 사전 매핑에 포함 — 본 파일은 단일 신뢰 메타 인덱스로 동작
- 2026-05-22 (data-advisor 분리) `database-fundamentals.md` / `master-data-management.md` / `data-quality-governance.md` / `data-warehousing-bi.md` / `db-indexes.md` / `db-storage-engines.md` / `db-query-optimizer.md` 7개 카탈로그가 **data-advisor 스킬(DMBOK 전용)로 이관** — 위 매핑에서 해당 항목은 data-advisor 소관, dev-advisor 는 SWEBOK KA 중심 잔류

> **사용 팁**: "내가 모르는 영역" 을 빠르게 찾으려면 본 파일을 먼저 검색하세요. 예) `Ctrl-F "Software Construction"` → SWEBOK KA 4 매핑 → `principles/refactoring-techniques.md` / `principles/code-smells.md` 로 진입. 또는 `Ctrl-F "API3"` → OWASP API Top 10 §4-2 → `security/security-api-web.md` §8 Mass Assignment 으로 진입.
