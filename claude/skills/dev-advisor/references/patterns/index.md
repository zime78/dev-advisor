# 디자인 패턴 레퍼런스

## 개요

소프트웨어 디자인 패턴 모음입니다.

## 디자인 패턴 (15 카테고리 + Phase 2 확장 32 카테고리)

GoF 23 + 아키텍처/분산/신뢰성/동시성/통합 + DDD 전술/데이터 접근/테스트/Observability/AI-LLM/배포/캐싱 (기존 159) + Phase 2 확장 (안티패턴·플랫폼·산업 도메인 등 32 카테고리).

> **보안 패턴은 별도 도메인으로 분리되었습니다**: [`../security/`](../security/) (14 파일, 메타 + 12 sub + 컴플라이언스). dev-catalog는 4중 카탈로그(patterns / algorithms / languages / security)로 격상되었다.

| 카테고리 | 파일 | 대표 항목 |
|---------|------|-----------|
| [생성 패턴](creational.md) | creational.md | Singleton, Factory Method, Abstract Factory, Builder, Prototype |
| [구조 패턴](structural.md) | structural.md | Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy |
| [행위 패턴](behavioral.md) | behavioral.md | Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method, Visitor, Interpreter |
| [아키텍처 패턴](architectural.md) | architectural.md | MVC, MVP, MVVM, MVI, MVVM-C, VIPER, Flux/Redux, Layered, Clean, Hexagonal, Onion, Modular Monolith, Microservices, SOA, Event-Driven, Serverless |
| [분산 시스템 패턴](distributed.md) | distributed.md | CQRS, Event Sourcing, Saga(Choreography), Saga(Orchestration), Outbox, Idempotency Key, BFF, API Gateway, Service Mesh |
| [신뢰성 패턴](reliability.md) | reliability.md | Circuit Breaker, Retry, Bulkhead, Timeout, Rate Limiter, Backpressure, Health Check, Sidecar, Ambassador |
| [동시성 패턴](concurrency.md) | concurrency.md | Active Object, Monitor, Thread Pool, Producer-Consumer, Reactor, Proactor, Read-Write Lock, DCL, Future/Promise, Actor, CSP, STM, Fork-Join, Structured Concurrency |
| [통합 패턴](integration.md) | integration.md | Pipes&Filters, Pub-Sub, Message Broker, Aggregator, Splitter, Content-Based Router, Translator, DLQ, Competing Consumers, Wire Tap, Claim Check, Resequencer, Scatter-Gather, Process Manager, Normalizer, Routing Slip |
| [DDD 전술 패턴](ddd-tactical.md) | ddd-tactical.md | Entity, Value Object, Aggregate, Domain Event, Domain Service, Specification, ACL, Bounded Context, Context Map, Factory(DDD), Repository(DDD) |
| [데이터 접근 패턴](data-access.md) | data-access.md | Repository, Unit of Work, Active Record, Data Mapper, Identity Map, Lazy Load, Query Object, Specification(Query), Table Module, Row Data Gateway |
| [테스트 패턴](testing.md) | testing.md | Test Pyramid, AAA, Given-When-Then, Test Double, Property-Based, Contract, Snapshot, Mutation, Fixture, Object Mother, Page Object |
| [Observability 패턴](observability.md) | observability.md | Three Pillars, Distributed Tracing, Correlation ID, Structured Logging, RED, USE, Golden Signals, SLO/Error Budget, Health Endpoint, Audit Trail |
| [AI/LLM 앱 패턴](ai-llm.md) | ai-llm.md | RAG, Tool Use, Agent Loop(ReAct), Multi-Agent, Prompt Template, Few-Shot, Self-Critique, Memory, Guardrails, Evaluator-Optimizer, Context Compaction, HITL |
| [배포 패턴](deployment.md) | deployment.md | Blue-Green, Canary, Rolling, Shadow, Feature Flag, Dark Launch, Strangler Fig, Branch by Abstraction, Expand-Contract |
| [캐싱 패턴](caching.md) | caching.md | Cache-Aside, Read-Through, Write-Through, Write-Behind, Refresh-Ahead, Cache Stampede, Eviction Policy, Negative Caching, Multi-Tier Cache |

---

## 추가 카테고리 (Phase 2 확장)

기존 159 패턴을 보완하기 위해 거버넌스·플랫폼·패러다임·도메인·품질·산업별 32 카테고리(약 320 패턴)를 추가했다. 그룹별로 분류한다.

### Governance (거버넌스 — 7 카테고리)

코드 품질·에러 모델·요구공학·레거시 변환·비용·DX 등 조직/프로세스 차원의 의사결정 패턴.

| 카테고리 | 파일 | 대표 항목 |
|---------|------|-----------|
| [안티패턴](anti-patterns.md) | anti-patterns.md | Big Ball of Mud, God Object, Anemic Domain Model, Distributed Monolith, Lava Flow, Golden Hammer, Cargo Cult, Vendor Lock-in, Spaghetti Code, Magic Numbers, Boat Anchor, Premature Optimization |
| [에러 처리](error-handling.md) | error-handling.md | Exception, Error Code, Result/Either, Railway-Oriented, Option/Maybe, Fail-Fast, Compensating Transaction, Panic/Recover, Defensive Copying, Retry+Backoff+Circuit |
| [레거시 코드 작업](legacy-code.md) | legacy-code.md | Seam, Characterization Test, Sprout/Wrap Method, Sensing Variable, Extract Interface, Extract and Override, Subclass and Override, Break Out Method Object, Mikado Method |
| [요구공학](requirements-engineering.md) | requirements-engineering.md | User Story, INVEST, MoSCoW, Use Case, Job Stories, Event Storming, Example Mapping, Gherkin (GWT), Impact Mapping, Three Amigos |
| [FinOps / 비용 공학](finops.md) | finops.md | Unit Economics, Rightsizing, Reserved/Savings Plans, Spot/Preemptible, Autoscaling Cost, Tagging & Allocation, FinOps Lifecycle, Budget Guardrails |
| [DX Engineering](dx-engineering.md) | dx-engineering.md | Scaffolding, Code Generation, LSP, Devcontainer, REPL/Notebook, Hot Reload/Fast Refresh, DevTools, Backstage/IDP |

### Context (플랫폼·문맥 — 7 카테고리)

특정 런타임/플랫폼 (모바일·게임·임베디드·크로스플랫폼·오프라인·웹 렌더링·상태관리·UI/UX) 에 종속된 패턴 모음.

| 카테고리 | 파일 | 대표 항목 |
|---------|------|-----------|
| [모바일 앱 운영](mobile-app.md) | mobile-app.md | App Lifecycle, Background Task, Push Notification, Deep Link, Navigation, App Startup, Crash & ANR, IAP/Subscription, OTA Update, App Signing, App Size, Permission UX, Battery Profiling |
| [임베디드/RTOS](embedded.md) | embedded.md | Rate Monotonic, EDF, WCET, Time-Triggered, ISR, DMA Buffer, Watchdog, Ring Buffer, Memory Pool, Hierarchical State Machine |
| [게임 개발](game-dev.md) | game-dev.md | Game Loop, ECS, Component Pattern, Object Pool (Game), Spatial Partition, Scene Graph, AI State Machine, Dirty Flag, Double Buffer, Netcode, Save System, Asset Pipeline |
| [크로스플랫폼 앱](crossplatform.md) | crossplatform.md | Flutter State / Platform Channel, RN Bridge / New Architecture, KMP expect/actual, Expo/EAS, Capacitor, Tauri vs Electron, Compose Multiplatform, SwiftUI↔Compose Interop, Hot Reload |
| [Offline-First](offline-first.md) | offline-first.md | Local-First DB, Sync Queue (Client Outbox), Conflict Resolution, Tombstone, Delta Sync, Conflict UI, Optimistic UI + Rollback, Network State Detection |
| [Web 렌더링](web-rendering.md) | web-rendering.md | CSR, SSR, SSG, ISR, Streaming SSR, Islands, RSC, Hydration, Resumability, Edge Rendering |
| [상태 관리](state-management.md) | state-management.md | Single Store, Feature Slice, Atomic State, Signal-Based, Server State, Form State, URL/Routing State, CRDT Collaborative State, Optimistic Update |
| [UI/UX](ui-ux.md) | ui-ux.md | Atomic Design, Container/Presenter, Skeleton/Shimmer, Optimistic UI, Infinite Scroll/Pagination UI, Empty/Error/Loading State, i18n, A11y (WCAG), Responsive/Adaptive, Design Tokens, Compound Components |

### Infrastructure (인프라·통신 — 8 카테고리)

네트워크·API·스트림·데이터 일관성·워크플로우·빌드·ML 파이프라인 등 시스템 인프라 패턴.

| 카테고리 | 파일 | 대표 항목 |
|---------|------|-----------|
| [네트워크/프로토콜](networking.md) | networking.md | TCP vs UDP, TCP Congestion, QUIC/HTTP3, HTTP versions, TLS Handshake, DNS, CDN/Edge, NAT Traversal, WebSocket, WebRTC, Reliable UDP, Connection Pooling |
| [API 설계 패턴](api-design.md) | api-design.md | Richardson Maturity, HATEOAS, Resource-Oriented (AIP), API Versioning, Pagination 3종, Idempotency Key, Bulk/Batch, LRO, Problem Details (RFC 7807), Resource Naming, Filter/Sort/FieldSel, Rate Limiting, Webhook/Async, Deprecation/Sunset |
| [API 스타일](api-styles.md) | api-styles.md | REST, GraphQL, gRPC, WebSocket API, SSE, Webhook, JSON-RPC, SOAP, WebTransport |
| [워크플로우·잡](workflow-jobs.md) | workflow-jobs.md | Durable Workflow, DAG Workflow, Job Queue, Saga (Workflow), Scheduled Job/Cron, Worker Leasing, Idempotent Worker, Long-Running Activity, Workflow Versioning |
| [스트림 처리 의미론](streaming-semantics.md) | streaming-semantics.md | Delivery Semantics, Event Time vs Processing Time, Watermark, Windowing, Triggering, Allowed Lateness, Stateful Stream, Checkpoint/Savepoint, Stream Backpressure |
| [데이터 일관성·복제](data-modeling.md) | data-modeling.md | CAP, PACELC, Consistency Models, Single-Leader, Multi-Leader, Leaderless, Sharding/Partitioning, Consistent Hashing, CDC, Materialized View, HTAP/Lambda/Kappa, Data Mesh/Lakehouse |
| [빌드·버전 관리](build-versioning.md) | build-versioning.md | Monorepo, Polyrepo, SemVer, CalVer, ZeroVer, Build Caching, Hermetic Build, Reproducible Build, Dependency Resolution |
| [MLOps](mlops.md) | mlops.md | Feature Store, Model Registry, Model Card, Data Drift, Concept Drift, Shadow/Champion-Challenger, ML Pipeline (DAG), Online/Batch Inference, Data Contract, Model Monitoring |

### Paradigm (패러다임 — 2 카테고리)

함수형·리액티브 등 프로그래밍 패러다임 패턴.

| 카테고리 | 파일 | 대표 항목 |
|---------|------|-----------|
| [함수형 프로그래밍](functional.md) | functional.md | Functor, Applicative, Monad, Free Monad, Lens/Optics, Tagless Final, Effect Handlers, CPS, Trampolining, Pattern Matching (ADT), Persistent Data Structures |
| [Reactive Streams & FRP](reactive-streams.md) | reactive-streams.md | Reactive Streams Spec, Cold/Hot Stream, Subject Types, Marble Diagram, Backpressure Strategy, Operator Composition, FRP, Stream Fusion |

### Domain (도메인 모델링 — 1 카테고리)

| 카테고리 | 파일 | 대표 항목 |
|---------|------|-----------|
| [DDD 전략](ddd-strategic.md) | ddd-strategic.md | Ubiquitous Language, Subdomain Classification, Bounded Context (전략), Context Map, Customer-Supplier, Conformist, ACL (전략), OHS, Published Language, Shared Kernel, Partnership, Separate Ways |

### Quality (품질·검증 — 1 카테고리)

| 카테고리 | 파일 | 대표 항목 |
|---------|------|-----------|
| [테스트 전략](testing-strategies.md) | testing-strategies.md | Pyramid/Trophy/Diamond/Honeycomb, Chaos Engineering, Load, Stress, Spike, Soak/Endurance, A/B/Multivariate, Synthetic Monitoring, Canary Analysis, Shadow Traffic |

### Industry (산업 도메인 — 6 카테고리)

특정 산업(금융·의료·이커머스·물류·IoT·Web3)에 특화된 도메인 패턴.

| 카테고리 | 파일 | 대표 항목 |
|---------|------|-----------|
| [Fintech / 결제](domains/fintech.md) | domains/fintech.md | Double-Entry Bookkeeping, Ledger, Reconciliation, Settlement/Clearing, Idempotent Payment, 3DS, Payment Intent/Saga, Multi-Currency/FX, Refund/Chargeback, AML/KYC, PCI Scope Reduction, Subscription Billing |
| [Healthcare](domains/healthcare.md) | domains/healthcare.md | FHIR R5, HL7 v2, SMART on FHIR, CDS Hooks, Consent (FHIR), PHI Audit Trail, De-identification, DICOM Pipeline, IHE Profiles, Telehealth Session |
| [eCommerce](domains/ecommerce.md) | domains/ecommerce.md | Cart Aggregate, Inventory Reservation, Product Catalog, Pricing/Promotion Engine, Order State Machine, Checkout Flow, Fulfillment, Returns/RMA, Search & Discovery, Recommendation, Marketplace Multi-Seller, Loyalty |
| [Logistics / 배송](domains/logistics.md) | domains/logistics.md | VRP/Route Optimization, Realtime Tracking, ETA, Geofencing, Fleet Dispatch, Last-Mile, Reverse Logistics, Cross-Docking, Capacity Planning, Track & Trace |
| [IoT / Edge](domains/iot-edge.md) | domains/iot-edge.md | Device Twin, OTA Firmware, Telemetry Buffer, Provisioning, Edge Gateway, MQTT Pub-Sub, Edge Inference, Time-Series Storage, Command & Control, Device mTLS |
| [Blockchain / Web3](blockchain.md) | blockchain.md | Consensus (PoW/PoS/PBFT/DPoS/PoA), Smart Contract Upgrade (Proxy), Oracle, Gas Optimization, Custody (MPC/Multisig), Event Indexer (The Graph), Token Standards (ERC), Layer-2 Scaling, MEV, Cross-chain Bridge |

---

## 패턴 선택 가이드

### 상황별 추천 패턴

| 상황 | 추천 패턴 | 카테고리 |
|------|----------|---------|
| 객체를 하나만 생성해야 할 때 | Singleton | 생성 |
| 객체 생성을 캡슐화하고 싶을 때 | Factory Method, Abstract Factory | 생성 |
| 복잡한 객체를 단계별로 생성할 때 | Builder | 생성 |
| 기존 객체를 복제하고 싶을 때 | Prototype | 생성 |
| 호환되지 않는 인터페이스를 연결할 때 | Adapter | 구조 |
| 추상화와 구현을 분리할 때 | Bridge | 구조 |
| 트리 구조를 표현할 때 | Composite | 구조 |
| 객체에 동적으로 기능을 추가할 때 | Decorator | 구조 |
| 복잡한 서브시스템을 단순화할 때 | Facade | 구조 |
| 대량의 객체를 효율적으로 관리할 때 | Flyweight | 구조 |
| 객체 접근을 제어할 때 | Proxy | 구조 |
| 요청을 체인으로 처리할 때 | Chain of Responsibility | 행위 |
| 요청을 객체로 캡슐화할 때 | Command | 행위 |
| 컬렉션을 순회할 때 | Iterator | 행위 |
| 객체 간 통신을 중재할 때 | Mediator | 행위 |
| 객체 상태를 저장/복원할 때 | Memento | 행위 |
| 상태 변화를 통지할 때 | Observer | 행위 |
| 상태에 따라 행동을 변경할 때 | State | 행위 |
| 알고리즘을 교환 가능하게 할 때 | Strategy | 행위 |
| 알고리즘 골격을 정의할 때 | Template Method | 행위 |
| 객체 구조에서 연산을 분리할 때 | Visitor | 행위 |
| 간단한 언어를 해석할 때 | Interpreter | 행위 |

---

## 패턴 ID → 파일 매핑 (기존 159 + Phase 2 확장 320 ≈ 479개)

`/pattern <id>` 호출 시 SKILL.md → 본 표 → 카테고리 파일 `## N. <패턴>` 헤더 순으로 lookup. 카테고리 파일 안에서 패턴 항목은 `## 1.`, `## 2.` 순서로 등장한다. Phase 2 확장 카테고리는 본 매핑 표 후반부에 별도로 정렬되어 있다.

### 생성 패턴 (creational.md) — 5
| ID | 영문명 | 한글명 |
|----|--------|--------|
| singleton | Singleton | 싱글톤 |
| factory-method | Factory Method | 팩토리 메서드 |
| abstract-factory | Abstract Factory | 추상 팩토리 |
| builder | Builder | 빌더 |
| prototype | Prototype | 프로토타입 |

### 구조 패턴 (structural.md) — 7
| ID | 영문명 | 한글명 |
|----|--------|--------|
| adapter | Adapter | 어댑터 |
| bridge | Bridge | 브릿지 |
| composite | Composite | 컴포지트 |
| decorator | Decorator | 데코레이터 |
| facade | Facade | 퍼사드 |
| flyweight | Flyweight | 플라이웨이트 |
| proxy | Proxy | 프록시 |

### 행위 패턴 (behavioral.md) — 11
| ID | 영문명 | 한글명 |
|----|--------|--------|
| chain-of-responsibility | Chain of Responsibility | 책임 연쇄 |
| command | Command | 커맨드 |
| iterator | Iterator | 반복자 |
| mediator | Mediator | 중재자 |
| memento | Memento | 메멘토 |
| observer | Observer | 옵저버 |
| state | State | 상태 |
| strategy | Strategy | 전략 |
| template-method | Template Method | 템플릿 메서드 |
| visitor | Visitor | 방문자 |
| interpreter | Interpreter | 인터프리터 |

### 아키텍처 패턴 (architectural.md) — 16
| ID | 영문명 | 한글명 |
|----|--------|--------|
| mvc | MVC | 모델-뷰-컨트롤러 |
| mvp | MVP | 모델-뷰-프레젠터 |
| mvvm | MVVM | 모델-뷰-뷰모델 |
| mvi | MVI | 모델-뷰-인텐트 |
| mvvm-c | MVVM-C | MVVM + 코디네이터 |
| viper | VIPER | 비퍼 |
| flux | Flux / Redux | 플럭스/리덕스 |
| layered | Layered Architecture | 계층 아키텍처 |
| clean-architecture | Clean Architecture | 클린 아키텍처 |
| hexagonal | Hexagonal Architecture | 헥사고날 |
| onion | Onion Architecture | 어니언 아키텍처 |
| modular-monolith | Modular Monolith | 모듈러 모놀리스 |
| microservices | Microservices | 마이크로서비스 |
| soa | SOA | 서비스 지향 |
| event-driven | Event-Driven Architecture | 이벤트 드리븐 |
| serverless | Serverless | 서버리스 |

### 분산 시스템 패턴 (distributed.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| cqrs | CQRS | 명령/조회 분리 |
| event-sourcing | Event Sourcing | 이벤트 소싱 |
| saga-choreography | Saga (Choreography) | 사가 코레오그래피 |
| saga-orchestration | Saga (Orchestration) | 사가 오케스트레이션 |
| outbox | Outbox Pattern | 아웃박스 |
| idempotency-key | Idempotency Key | 멱등성 키 |
| bff | BFF | 백엔드 포 프론트엔드 |
| api-gateway | API Gateway | API 게이트웨이 |
| service-mesh | Service Mesh | 서비스 메시 |

### 신뢰성 패턴 (reliability.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| circuit-breaker | Circuit Breaker | 서킷 브레이커 |
| retry | Retry | 재시도 |
| bulkhead | Bulkhead | 벌크헤드 |
| timeout | Timeout | 타임아웃 |
| rate-limiter | Rate Limiter | 레이트 리미터 |
| backpressure | Backpressure | 백프레셔 |
| health-check | Health Check | 헬스 체크 |
| sidecar | Sidecar | 사이드카 |
| ambassador | Ambassador | 앰배서더 |

### 동시성 패턴 (concurrency.md) — 14
| ID | 영문명 | 한글명 |
|----|--------|--------|
| active-object | Active Object | 액티브 오브젝트 |
| monitor-object | Monitor Object | 모니터 오브젝트 |
| thread-pool | Thread Pool | 스레드 풀 |
| producer-consumer | Producer-Consumer | 생산자-소비자 |
| reactor | Reactor | 리액터 |
| proactor | Proactor | 프로액터 |
| read-write-lock | Read-Write Lock | 읽기-쓰기 락 |
| double-checked-locking | Double-Checked Locking | 이중 검사 잠금 |
| future-promise | Future / Promise | 퓨처/프라미스 |
| actor-model | Actor Model | 액터 모델 |
| csp | CSP | 통신 순차 프로세스 |
| stm | STM | 소프트웨어 트랜잭셔널 메모리 |
| fork-join | Fork-Join | 포크-조인 |
| structured-concurrency | Structured Concurrency | 구조화된 동시성 |

### 엔터프라이즈 통합 패턴 (integration.md) — 16
| ID | 영문명 | 한글명 |
|----|--------|--------|
| pipes-filters | Pipes & Filters | 파이프 앤 필터 |
| publish-subscribe | Publish-Subscribe | 발행-구독 |
| message-broker | Message Broker | 메시지 브로커 |
| aggregator | Aggregator | 애그리게이터 |
| splitter | Splitter | 스플리터 |
| content-based-router | Content-Based Router | 콘텐츠 기반 라우터 |
| message-translator | Message Translator | 메시지 트랜슬레이터 |
| dead-letter-queue | Dead Letter Queue | 데드 레터 큐 |
| competing-consumers | Competing Consumers | 경쟁 소비자 |
| wire-tap | Wire Tap | 와이어 탭 |
| claim-check | Claim Check | 클레임 체크 |
| resequencer | Resequencer | 리시퀀서 |
| scatter-gather | Scatter-Gather | 스캐터-게더 |
| process-manager | Process Manager | 프로세스 매니저 |
| normalizer | Normalizer | 정규화기 |
| routing-slip | Routing Slip | 라우팅 슬립 |

### DDD 전술 패턴 (ddd-tactical.md) — 11
| ID | 영문명 | 한글명 |
|----|--------|--------|
| entity | Entity | 엔티티 |
| value-object | Value Object | 값 객체 |
| aggregate | Aggregate | 애그리거트 |
| domain-event | Domain Event | 도메인 이벤트 |
| domain-service | Domain Service | 도메인 서비스 |
| specification | Specification | 명세 |
| anti-corruption-layer | Anti-Corruption Layer | 부패 방지 계층 |
| bounded-context | Bounded Context | 경계 컨텍스트 |
| context-map | Context Map | 컨텍스트 맵 |
| ddd-factory | Factory (DDD) | DDD 팩토리 |
| ddd-repository | Repository (DDD) | DDD 리포지토리 |

### 데이터 접근 패턴 (data-access.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| repository | Repository | 리포지토리 |
| unit-of-work | Unit of Work | 작업 단위 |
| active-record | Active Record | 액티브 레코드 |
| data-mapper | Data Mapper | 데이터 매퍼 |
| identity-map | Identity Map | 식별자 맵 |
| lazy-load | Lazy Load | 지연 로딩 |
| query-object | Query Object | 쿼리 객체 |
| query-specification | Specification (Query) | 쿼리 명세 |
| table-module | Table Module | 테이블 모듈 |
| row-data-gateway | Row Data Gateway | 행 데이터 게이트웨이 |

### 테스트 패턴 (testing.md) — 11
| ID | 영문명 | 한글명 |
|----|--------|--------|
| test-pyramid | Test Pyramid | 테스트 피라미드 |
| aaa | AAA (Arrange-Act-Assert) | AAA |
| given-when-then | Given-When-Then | BDD 스타일 |
| test-double | Test Double | 테스트 더블 |
| property-based-test | Property-Based Test | 속성 기반 |
| contract-test | Contract Test | 계약 테스트 |
| snapshot-test | Snapshot Test | 스냅샷 |
| mutation-test | Mutation Test | 변이 |
| test-fixture | Test Fixture | 픽스처 |
| object-mother | Object Mother | 오브젝트 마더 |
| page-object | Page Object | 페이지 오브젝트 |

### Observability 패턴 (observability.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| three-pillars | Three Pillars | 3대 축 |
| distributed-tracing | Distributed Tracing | 분산 트레이싱 |
| correlation-id | Correlation ID | 상관관계 ID |
| structured-logging | Structured Logging | 구조화 로깅 |
| red-method | RED Method | RED |
| use-method | USE Method | USE |
| golden-signals | Golden Signals | 골든 시그널 |
| slo-error-budget | SLO / Error Budget | SLO/에러 예산 |
| health-endpoint | Health Endpoint | 헬스 엔드포인트 |
| audit-trail | Audit Trail | 감사 추적 |

### AI / LLM 패턴 (ai-llm.md) — 12
| ID | 영문명 | 한글명 |
|----|--------|--------|
| rag | RAG | 검색 증강 생성 |
| tool-use | Tool Use | 도구 호출 |
| agent-loop-react | Agent Loop (ReAct) | 에이전트 루프 |
| multi-agent | Multi-Agent Orchestration | 다중 에이전트 |
| prompt-template | Prompt Template | 프롬프트 템플릿 |
| few-shot | Few-Shot Prompting | 퓨샷 |
| self-critique | Self-Critique | 자기 비판 |
| llm-memory | Memory | LLM 메모리 |
| guardrails | Guardrails | 가드레일 |
| evaluator-optimizer | Evaluator-Optimizer | 평가자-최적화 |
| context-compaction | Context Compaction | 컨텍스트 압축 |
| hitl | Human-in-the-Loop | HITL |

### 배포 패턴 (deployment.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| blue-green | Blue-Green Deployment | 블루-그린 |
| canary | Canary Release | 카나리 |
| rolling-update | Rolling Update | 롤링 업데이트 |
| shadow-deployment | Shadow Deployment | 섀도우 |
| feature-flag | Feature Flag | 피처 플래그 |
| dark-launch | Dark Launch | 다크 런치 |
| strangler-fig | Strangler Fig | 스트랭글러 피그 |
| branch-by-abstraction | Branch by Abstraction | 추상화 분기 |
| expand-contract | Expand-Contract | 확장-축소 |

### 캐싱 패턴 (caching.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| cache-aside | Cache-Aside | 캐시 옆 채움 |
| read-through | Read-Through | 읽기 통과 |
| write-through | Write-Through | 쓰기 통과 |
| write-behind | Write-Behind | 쓰기 지연 |
| refresh-ahead | Refresh-Ahead | 사전 갱신 |
| cache-stampede-prevention | Cache Stampede Prevention | 스탬피드 방지 |
| eviction-policies | Eviction Policies | 만료/제거 정책 |
| negative-caching | Negative Caching | 부정 캐싱 |
| multi-tier-cache | Multi-Tier Cache | 다단 캐시 |

---

## Phase 2 확장 ID 매핑

기존 159 패턴과 분리된 신규 32 카테고리의 패턴 ID 매핑. 각 ID는 해당 카테고리 파일의 `<a id="..."></a>` anchor 와 1:1 대응한다.

### 안티패턴 (anti-patterns.md) — 18
| ID | 영문명 | 한글명 |
|----|--------|--------|
| 1-big-ball-of-mud | Big Ball of Mud | 빅 볼 오브 머드 |
| 2-god-object | God Object / God Class | 갓 오브젝트 |
| 3-anemic-domain-model | Anemic Domain Model | 빈혈 도메인 모델 |
| 4-distributed-monolith | Distributed Monolith | 분산 모놀리스 |
| 5-lava-flow | Lava Flow | 라바 플로우 |
| 6-golden-hammer | Golden Hammer | 골든 해머 |
| 7-cargo-cult-programming | Cargo Cult Programming | 카고 컬트 프로그래밍 |
| 8-vendor-lock-in | Vendor Lock-in / Magic Pushbutton | 벤더 락인 |
| 9-spaghetti-code | Spaghetti Code | 스파게티 코드 |
| 10-magic-numbers-strings | Magic Numbers / Magic Strings | 매직 넘버/문자열 |
| 11-boat-anchor | Boat Anchor | 보트 앵커 |
| 12-premature-optimization | Premature Optimization | 조기 최적화 |
| 13-reinventing-the-wheel | Reinventing the Wheel / NIH | 바퀴 재발명 |
| 14-yo-yo-problem | Yo-Yo Problem | 요요 문제 |
| 15-copy-paste-programming | Copy-Paste Programming | 복붙 프로그래밍 |
| 16-hard-coding | Hard Coding | 하드 코딩 |
| 17-sequential-coupling | Sequential / Temporal Coupling | 순차 결합 |
| 18-stovepipe-system | Stovepipe System | 스토브파이프 시스템 |

### 모바일 앱 운영 (mobile-app.md) — 13
| ID | 영문명 | 한글명 |
|----|--------|--------|
| app-lifecycle | App Lifecycle State Machine | 앱 생명주기 상태머신 |
| background-task | Background Task | 백그라운드 작업 |
| push-notification | Push Notification Topology | 푸시 알림 토폴로지 |
| deep-link | Deep Link / Universal Link / App Link | 딥링크 |
| navigation-pattern | Navigation Pattern | 네비게이션 패턴 |
| app-startup | App Cold/Warm/Hot Start 최적화 | 앱 시작 시간 최적화 |
| crash-anr | Crash & ANR Handling | 크래시·ANR 처리 |
| iap-subscription | In-App Purchase / Subscription | 인앱 결제·구독 |
| ota-update | OTA Update / Code Push | OTA 업데이트 |
| app-signing | App Signing & Distribution | 앱 서명·배포 |
| app-size | App Size 최적화 | 앱 용량 최적화 |
| permission-ux | Permission Request UX | 권한 요청 UX |
| battery-profiling | Battery & Performance Profiling | 배터리·성능 프로파일링 |

### 임베디드 / RTOS (embedded.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| rate-monotonic-scheduling | Rate Monotonic Scheduling (RMS) | 단조 비율 스케줄링 |
| earliest-deadline-first | Earliest Deadline First (EDF) | 최단 마감 우선 |
| wcet-analysis | Worst-Case Execution Time 분석 | WCET 분석 |
| time-triggered-architecture | Time-Triggered Architecture (TTA) | 시간 트리거 아키텍처 |
| isr-pattern | Interrupt Service Routine (Top/Bottom-half) | 인터럽트 서비스 루틴 |
| dma-buffer | DMA Buffer (Ping-Pong / Circular) | DMA 버퍼 |
| watchdog-timer | Watchdog Timer | 워치독 타이머 |
| ring-buffer | Ring Buffer / Circular Buffer | 링 버퍼 |
| memory-pool | Memory Pool / Static Allocation | 메모리 풀 |
| state-machine-embedded | Hierarchical State Machine / Statechart | 계층 상태 기계 |

### 게임 개발 (game-dev.md) — 12
| ID | 영문명 | 한글명 |
|----|--------|--------|
| 1-game-loop | Game Loop | 게임 루프 |
| 2-ecs | Entity-Component-System | ECS |
| 3-component-pattern | Component Pattern | 컴포넌트 패턴 |
| 4-object-pool-game | Object Pool (Game) | 오브젝트 풀 (게임) |
| 5-spatial-partition | Spatial Partition | 공간 분할 |
| 6-scene-graph | Scene Graph | 씬 그래프 |
| 7-ai-state-machine | State Machine for AI | AI 상태 기계 |
| 8-dirty-flag | Dirty Flag | 더티 플래그 |
| 9-double-buffer-game | Double Buffer (Game) | 더블 버퍼 |
| 10-netcode | Game Netcode | 게임 네트코드 |
| 11-save-system | Save System / Serialization | 저장 시스템 |
| 12-asset-pipeline | Asset Pipeline | 에셋 파이프라인 |

### 네트워크 / 프로토콜 (networking.md) — 12
| ID | 영문명 | 한글명 |
|----|--------|--------|
| tcp-udp | TCP vs UDP | TCP vs UDP |
| tcp-congestion-control | TCP Congestion Control | TCP 혼잡 제어 |
| quic-http3 | QUIC / HTTP/3 | QUIC / HTTP3 |
| http-versions | HTTP/1.1 vs HTTP/2 vs HTTP/3 | HTTP 버전 비교 |
| tls-handshake | TLS Handshake | TLS 핸드셰이크 |
| dns-patterns | DNS Patterns | DNS 패턴 |
| cdn-edge | CDN / Edge Patterns | CDN/엣지 |
| nat-traversal | NAT Traversal | NAT 트래버설 |
| websocket | WebSocket Protocol | 웹소켓 |
| webrtc | WebRTC | 웹RTC |
| reliable-udp | Reliable UDP / KCP / RUDP | 신뢰성 UDP |
| connection-pooling | Connection Pooling & Keep-Alive | 커넥션 풀링 |

### 크로스플랫폼 앱 (crossplatform.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| flutter-state-management | Flutter State Management | Flutter 상태 관리 |
| flutter-platform-channel | Flutter Platform Channel | Flutter 플랫폼 채널 |
| rn-bridge-new-arch | React Native Bridge → New Architecture | RN 신아키텍처 (JSI/Turbo/Fabric) |
| kmp-expect-actual | Kotlin Multiplatform expect/actual | KMP expect/actual |
| expo-eas | Expo / EAS | Expo / EAS |
| capacitor | Capacitor (Web → Native Hybrid) | 캐퍼시터 |
| tauri-vs-electron | Tauri vs Electron | Tauri vs Electron |
| compose-multiplatform | Compose Multiplatform | 컴포즈 멀티플랫폼 |
| swiftui-compose-interop | SwiftUI ↔ Compose Interop | SwiftUI/Compose 인터옵 |
| hot-reload-fast-refresh | Hot Reload / Fast Refresh | 핫 리로드 |

### Offline-First (offline-first.md) — 8
| ID | 영문명 | 한글명 |
|----|--------|--------|
| local-first-db | Local-First Database | 로컬 우선 DB |
| sync-queue-outbox-client | Sync Queue / Client Outbox | 동기화 큐 |
| conflict-resolution | Conflict Resolution Strategy | 충돌 해결 |
| tombstone | Tombstone Pattern | 묘비 패턴 |
| delta-sync | Delta Sync | 증분 동기화 |
| conflict-ui-pattern | Conflict UI Pattern | 충돌 UI |
| optimistic-ui-rollback | Optimistic UI with Rollback | 낙관적 UI + 롤백 |
| network-state-detection | Network State Detection | 네트워크 상태 감지 |

### 에러 처리 (error-handling.md) — 11
| ID | 영문명 | 한글명 |
|----|--------|--------|
| exception-checked-unchecked | Exception (Checked/Unchecked) | 예외 |
| error-code-sentinel | Error Code / Sentinel Value | 에러 코드/센티넬 |
| result-either-monad | Result / Either Monad | Result/Either 모나드 |
| railway-oriented | Railway-Oriented Programming | 레일웨이 지향 |
| option-maybe | Option / Maybe | 옵션/메이비 |
| fail-fast-safe | Fail-Fast vs Fail-Safe | 페일패스트/페일세이프 |
| compensating-transaction | Compensating Transaction | 보상 트랜잭션 |
| error-aggregation | Error Aggregation / Multi-Error | 에러 어그리게이션 |
| panic-recover | Panic / Recover | 패닉/리커버 |
| defensive-copying | Defensive Copying / Boundary Validation | 방어적 복사 |
| retry-backoff-circuit | Retry + Backoff + Circuit Breaker | 재시도 + 백오프 + 서킷 |

### API 설계 패턴 (api-design.md) — 14
| ID | 영문명 | 한글명 |
|----|--------|--------|
| 1-richardson-maturity | Richardson Maturity Model | 리처드슨 성숙도 |
| 2-hateoas | HATEOAS | 하이퍼미디어 |
| 3-resource-oriented-design | Resource-Oriented Design (AIP) | 리소스 지향 설계 |
| 4-api-versioning | API Versioning | API 버저닝 |
| 5-pagination-patterns | Pagination (Offset/Cursor/Keyset) | 페이지네이션 |
| 6-idempotency-key-api | Idempotency Key (API) | 멱등성 키 |
| 7-bulk-batch-operation | Bulk / Batch Operation | 벌크/배치 작업 |
| 8-long-running-operation | Long-Running Operation (LRO) | 장기 실행 작업 |
| 9-problem-details-rfc7807 | Problem Details (RFC 7807) | 에러 응답 표준 |
| 10-resource-naming | Resource Naming Convention | 리소스 네이밍 |
| 11-filter-sort-fieldsel | Filter / Sort / Field Selection | 필터/정렬/필드 선택 |
| 12-api-rate-limiting | API Rate Limiting & Quota | API 레이트 리미팅 |
| 13-webhook-async-api | Async API (Webhook / Callback) | 비동기 API |
| 14-api-deprecation-sunset | API Deprecation & Sunset | API 폐기/일몰 |

### API 스타일 (api-styles.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| rest | REST | REST |
| graphql | GraphQL | 그래프QL |
| grpc | gRPC | gRPC |
| websocket-api | WebSocket | 웹소켓 |
| server-sent-events | Server-Sent Events (SSE) | SSE |
| webhook | Webhook (HTTP Push) | 웹훅 |
| json-rpc | JSON-RPC 2.0 | JSON-RPC |
| soap | SOAP | SOAP |
| webtransport | WebTransport | 웹트랜스포트 |

### Web 렌더링 (web-rendering.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| csr | Client-Side Rendering | CSR |
| ssr | Server-Side Rendering | SSR |
| ssg | Static Site Generation | SSG |
| isr | Incremental Static Regeneration | ISR |
| streaming-ssr | Streaming SSR | 스트리밍 SSR |
| islands-architecture | Islands Architecture | 아일랜드 아키텍처 |
| react-server-components | React Server Components | RSC |
| hydration | Hydration | 하이드레이션 |
| resumability | Resumability | 리주머빌리티 |
| edge-rendering | Edge Rendering | 엣지 렌더링 |

### 상태 관리 (state-management.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| single-store | Single Store | 단일 스토어 |
| feature-slice-store | Feature Slice / Multiple Store | 피처 슬라이스 스토어 |
| atomic-state | Atomic State | 원자 상태 |
| signal-based | Signal-Based | 시그널 기반 |
| server-state | Server State | 서버 상태 |
| form-state | Form State | 폼 상태 |
| url-routing-state | URL / Routing State | URL/라우팅 상태 |
| crdt-collab-state | CRDT-based Collaborative State | CRDT 공동편집 상태 |
| optimistic-update | Optimistic UI Update | 낙관적 업데이트 |

### 함수형 프로그래밍 (functional.md) — 11
| ID | 영문명 | 한글명 |
|----|--------|--------|
| functor | Functor | 펑터 |
| applicative-functor | Applicative Functor | 애플리커티브 펑터 |
| monad | Monad | 모나드 |
| free-monad | Free Monad | 자유 모나드 |
| lens-optics | Lens / Optics | 렌즈/옵틱스 |
| tagless-final | Tagless Final | 태그리스 파이널 |
| effect-handlers | Effect Handlers / Algebraic Effects | 대수적 효과 |
| cps | Continuation-Passing Style | CPS |
| trampolining | Trampolining | 트램폴린 |
| pattern-matching-adt | Pattern Matching (ADT + Exhaustive) | 패턴 매칭 |
| persistent-data-structures | Persistent Data Structures | 지속 자료구조 |

### Reactive Streams & FRP (reactive-streams.md) — 8
| ID | 영문명 | 한글명 |
|----|--------|--------|
| 1-reactive-streams-spec | Reactive Streams Spec | 리액티브 스트림즈 사양 |
| 2-cold-hot-stream | Cold vs Hot Stream | 콜드/핫 스트림 |
| 3-subject-types | Subject (Behavior/Replay/Publish) | 서브젝트 종류 |
| 4-marble-diagram | Marble Diagram | 마블 다이어그램 |
| 5-backpressure-strategy | Backpressure Strategy | 백프레셔 전략 |
| 6-operator-composition | Operator Composition | 오퍼레이터 합성 |
| 7-frp | Functional Reactive Programming | FRP |
| 8-stream-fusion | Stream / Operator Fusion | 스트림 융합 |

### 레거시 코드 작업 (legacy-code.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| seam-types | Seam (Object / Preprocessing / Link) | 심 |
| characterization-test | Characterization Test | 특성화 테스트 |
| sprout-method-class | Sprout Method / Sprout Class | 새싹 메서드/클래스 |
| wrap-method-class | Wrap Method / Wrap Class | 랩 메서드/클래스 |
| sensing-variable | Sensing Variable | 센싱 변수 |
| extract-interface-testability | Extract Interface (for testability) | 인터페이스 추출 |
| extract-and-override | Extract and Override | 추출 후 오버라이드 |
| subclass-and-override-method | Subclass and Override Method | 서브클래스 후 오버라이드 |
| break-out-method-object | Break Out Method Object | 메서드 객체 추출 |
| mikado-method | Mikado Method | 미카도 메서드 |

### 워크플로우 · 잡 (workflow-jobs.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| durable-workflow | Durable Workflow | 지속성 워크플로우 |
| dag-workflow | DAG-based Workflow | DAG 워크플로우 |
| job-queue | Job Queue | 잡 큐 |
| saga-workflow | Saga (Workflow 관점) | 사가 (워크플로우) |
| scheduled-job-cron | Scheduled Job / Cron | 스케줄드 잡 |
| worker-leasing | Worker Leasing / Visibility Timeout | 워커 리스 |
| idempotent-worker | Idempotent Worker | 멱등 워커 |
| long-running-activity | Long-Running Activity | 장기 실행 액티비티 |
| workflow-versioning | Workflow Versioning | 워크플로우 버저닝 |

### 스트림 처리 의미론 (streaming-semantics.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| 1-delivery-semantics | Delivery Semantics | 전달 의미론 |
| 2-event-time-processing-time | Event Time vs Processing Time | 이벤트 시각 vs 처리 시각 |
| 3-watermark | Watermark | 워터마크 |
| 4-windowing-patterns | Windowing (Tumbling/Sliding/Session/Hopping/Global) | 윈도잉 |
| 5-triggering | Triggering | 트리거 |
| 6-allowed-lateness | Allowed Lateness | 허용 지연 |
| 7-stateful-stream | Stateful Stream (Keyed state) | 스테이트풀 스트림 |
| 8-checkpoint-savepoint | Checkpoint / Savepoint | 체크포인트/세이브포인트 |
| 9-backpressure-stream | Stream Backpressure | 스트림 백프레셔 |

### 데이터 일관성 · 복제 (data-modeling.md) — 12
| ID | 영문명 | 한글명 |
|----|--------|--------|
| cap-theorem | CAP Theorem | CAP 정리 |
| pacelc | PACELC Theorem | PACELC 정리 |
| consistency-models-systems | Consistency Models (Strong/Sequential/Causal/Eventual) | 일관성 모델 |
| single-leader-replication | Single-Leader Replication | 단일 리더 복제 |
| multi-leader-replication | Multi-Leader Replication | 다중 리더 복제 |
| leaderless-replication | Leaderless Replication | 리더리스 복제 |
| sharding-partitioning | Sharding / Partitioning | 샤딩/파티셔닝 |
| consistent-hashing-sharding | Consistent Hashing (Sharding 관점) | 일관 해싱 |
| cdc | Change Data Capture | CDC |
| materialized-view | Materialized View | 구체화 뷰 |
| lambda-kappa-htap | HTAP / Lambda / Kappa Architecture | 람다/카파/HTAP |
| data-mesh-lakehouse | Data Mesh / Data Lakehouse | 데이터 메시/레이크하우스 |

### DDD 전략 (ddd-strategic.md) — 12
| ID | 영문명 | 한글명 |
|----|--------|--------|
| ubiquitous-language | Ubiquitous Language | 편재 언어 |
| subdomain-classification | Subdomain (Core/Supporting/Generic) | 서브도메인 분류 |
| bounded-context-strategic | Bounded Context (전략적 관점) | 경계 컨텍스트 |
| context-map | Context Map | 컨텍스트 맵 |
| customer-supplier | Customer-Supplier | 고객-공급자 |
| conformist | Conformist | 컨포미스트 |
| anti-corruption-layer-strategic | Anti-Corruption Layer (전략) | ACL (전략) |
| open-host-service | Open Host Service | OHS |
| published-language | Published Language | 발행 언어 |
| shared-kernel | Shared Kernel | 공유 커널 |
| partnership | Partnership | 파트너십 |
| separate-ways | Separate Ways | 분리 |

### UI/UX (ui-ux.md) — 11
| ID | 영문명 | 한글명 |
|----|--------|--------|
| atomic-design | Atomic Design | 아토믹 디자인 |
| container-presenter | Container / Presenter (Smart/Dumb) | 컨테이너/프레젠터 |
| skeleton-shimmer | Skeleton Screen / Shimmer | 스켈레톤/시머 |
| optimistic-ui-update | Optimistic UI Update | 낙관적 UI |
| infinite-scroll-pagination-ui | Pull-to-Refresh / Infinite Scroll / Pagination UI | 무한 스크롤/페이지네이션 UI |
| empty-error-loading-state | Empty / Error / Loading State | 빈/에러/로딩 상태 |
| i18n | Internationalization | 국제화 |
| a11y-wcag | Accessibility (WCAG 2.2) | 접근성 |
| responsive-adaptive | Responsive vs Adaptive | 반응형/적응형 |
| design-tokens | Design Tokens | 디자인 토큰 |
| compound-components | Compound Components / Slot | 컴파운드 컴포넌트 |

### Fintech / 결제 (domains/fintech.md) — 12
| ID | 영문명 | 한글명 |
|----|--------|--------|
| double-entry-bookkeeping | Double-Entry Bookkeeping | 복식부기 |
| ledger-pattern | Ledger Pattern | 원장 |
| reconciliation | Reconciliation | 대사 |
| settlement-clearing | Settlement / Clearing | 결제/청산 |
| idempotent-payment | Idempotent Payment | 멱등 결제 |
| 3ds-authentication | 3-D Secure Authentication | 3DS 인증 |
| payment-intent-saga | Payment Intent / Saga | 결제 인텐트/사가 |
| multi-currency-fx | Multi-Currency / FX Handling | 다통화/환율 |
| refund-chargeback | Refund / Chargeback / Dispute | 환불/차지백 |
| aml-kyc | AML / KYC | 자금세탁방지/KYC |
| card-pci-scope-reduction | Card Network 통합 (PCI Scope 축소) | PCI 범위 축소 |
| subscription-billing | Subscription / Recurring Billing | 구독 결제 |

### Healthcare (domains/healthcare.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| fhir-r5-resource | FHIR R5 Resource Model | FHIR R5 리소스 모델 |
| hl7-v2-messaging | HL7 v2 Messaging | HL7 v2 메시징 |
| smart-on-fhir | SMART on FHIR / OAuth2 Launch | SMART on FHIR |
| cds-hooks | CDS Hooks | 임상 의사결정 지원 훅 |
| consent-management-fhir | Consent Management (FHIR) | 환자 동의 관리 |
| phi-audit-trail | PHI Audit Trail (HIPAA §164.312) | PHI 감사 추적 |
| de-identification | De-identification / Safe Harbor | 비식별화 |
| dicom-pipeline | DICOM Imaging Pipeline | DICOM 파이프라인 |
| ihe-profiles | IHE Profiles (XDS / XCA / PIX) | IHE 프로파일 |
| telehealth-session | Telehealth Session Pattern | 원격진료 세션 |

### eCommerce (domains/ecommerce.md) — 12
| ID | 영문명 | 한글명 |
|----|--------|--------|
| cart-aggregate | Cart Aggregate | 장바구니 애그리거트 |
| inventory-reservation | Inventory Reservation / Soft Hold | 재고 예약 |
| product-catalog | Product Catalog (계층) | 상품 카탈로그 |
| pricing-promotion-engine | Pricing & Promotion Engine | 가격/프로모션 엔진 |
| order-state-machine | Order State Machine | 주문 상태 기계 |
| checkout-flow | Checkout Flow | 결제 플로우 |
| fulfillment-warehouse | Fulfillment / Warehouse (Pick-Pack-Ship) | 풀필먼트 |
| returns-rma | Returns / RMA | 반품/RMA |
| search-discovery | Search & Discovery | 검색/디스커버리 |
| recommendation-personalization | Recommendation (Personalization) | 추천/개인화 |
| marketplace-multi-seller | Marketplace Multi-Seller | 마켓플레이스 다중 셀러 |
| loyalty-rewards | Loyalty / Rewards Program | 적립/리워드 |

### Logistics / 배송 (domains/logistics.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| vrp-route-optimization | VRP / Route Optimization | 경로 최적화 (VRP) |
| realtime-tracking | Real-time Tracking | 실시간 추적 |
| eta-calculation | ETA Calculation | 도착 예상 시간 |
| geofencing | Geofencing | 지오펜싱 |
| fleet-dispatch | Fleet Dispatch / Driver Matching | 차량·기사 배차 |
| last-mile-delivery | Last-Mile Delivery | 라스트 마일 |
| reverse-logistics | Reverse Logistics | 역물류/반품 회수 |
| multi-hop-cross-docking | Multi-Hop / Cross-Docking | 다단계 환적/크로스도킹 |
| capacity-planning | Capacity Planning / Demand Forecasting | 수요 예측/캐파 |
| track-and-trace | Track & Trace (Chain of Custody) | 추적/이력관리 |

### IoT / Edge (domains/iot-edge.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| device-twin | Device Twin (Digital Twin) | 디바이스 트윈 |
| ota-firmware | OTA Firmware Update | 무선 펌웨어 업데이트 |
| telemetry-buffer | Telemetry Buffer (Store-and-Forward) | 텔레메트리 버퍼 |
| device-provisioning | Device Provisioning / Onboarding | 디바이스 프로비저닝 |
| edge-gateway | Edge Gateway | 엣지 게이트웨이 |
| mqtt-pubsub | MQTT Pub-Sub | MQTT 발행/구독 |
| edge-ml-inference | Edge ML Inference | 엣지 ML 추론 |
| time-series-storage | Time-Series Storage | 시계열 저장소 |
| command-control | Command & Control (C2) | 명령·제어 |
| device-mtls | Device Identity & Mutual TLS | 디바이스 mTLS |

### FinOps / 비용 공학 (finops.md) — 8
| ID | 영문명 | 한글명 |
|----|--------|--------|
| unit-economics | Unit Economics (Unit Cost) | 단위 경제학 |
| rightsizing | Rightsizing | 라이트사이징 |
| reserved-savings-plans | Reserved / Savings Plans / Commitment | 약정 할인 |
| spot-preemptible | Spot / Preemptible Instances | 스팟/프리엠티블 |
| autoscaling-cost | Autoscaling Cost Optimization | 오토스케일링 비용 |
| tagging-allocation | Tagging & Cost Allocation | 태깅/비용 할당 |
| finops-lifecycle | FinOps Lifecycle (Inform/Optimize/Operate) | FinOps 라이프사이클 |
| budget-guardrails | Budget Guardrails & Anomaly Detection | 예산 가드레일 |

### 테스트 전략 (testing-strategies.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| pyramid-trophy-diamond-honeycomb | Pyramid / Trophy / Diamond / Honeycomb | 테스트 형태 비교 |
| chaos-engineering | Chaos Engineering | 카오스 엔지니어링 |
| load-testing | Load Testing | 부하 테스트 |
| stress-testing | Stress Testing | 스트레스 테스트 |
| spike-testing | Spike Testing | 스파이크 테스트 |
| soak-endurance-testing | Soak / Endurance Testing | 내구성 테스트 |
| ab-multivariate-testing | A/B / Multivariate Testing | A/B 테스트 |
| synthetic-monitoring | Synthetic Monitoring | 합성 모니터링 |
| canary-analysis | Canary Analysis | 카나리 분석 |
| shadow-traffic-testing | Shadow Traffic / Dark Launch Testing | 섀도 트래픽 |

### 빌드 · 버전 관리 (build-versioning.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| monorepo | Monorepo | 단일 저장소 |
| polyrepo | Polyrepo | 다중 저장소 |
| semver | Semantic Versioning (SemVer 2.0) | 시맨틱 버저닝 |
| calver | Calendar Versioning (CalVer) | 캘린더 버저닝 |
| zerover | ZeroVer (0ver) | 제로버 |
| build-caching | Build Caching | 빌드 캐싱 |
| hermetic-build | Hermetic Build | 격리 빌드 |
| reproducible-build | Reproducible Build | 재현 가능 빌드 |
| dependency-resolution | Dependency Resolution | 의존성 해결 |

### MLOps (mlops.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| feature-store | Feature Store | 피처 스토어 |
| model-registry | Model Registry | 모델 레지스트리 |
| model-card | Model Card | 모델 카드 |
| data-drift | Data Drift Detection | 데이터 드리프트 |
| concept-drift | Concept Drift Detection | 컨셉 드리프트 |
| shadow-champion-challenger | Shadow Model / Champion-Challenger | 섀도/챔피언-챌린저 |
| ml-pipeline-dag | ML Pipeline (DAG) | ML 파이프라인 |
| online-batch-inference | Online vs Batch Inference | 온라인/배치 추론 |
| data-contract | Data Contract | 데이터 계약 |
| model-monitoring | Model Monitoring (Prediction Quality) | 모델 모니터링 |

### DX Engineering (dx-engineering.md) — 8
| ID | 영문명 | 한글명 |
|----|--------|--------|
| scaffolding | Scaffolding (Project/Component Generator) | 스캐폴딩 |
| code-generation | Code Generation (Codegen) | 코드 생성 |
| language-server-protocol | Language Server Protocol | LSP |
| devcontainer | Devcontainer / Dev Environment as Code | 데브컨테이너 |
| repl-notebook | REPL / Notebook | REPL/노트북 |
| hot-reload-fast-refresh-dx | Hot Reload / Fast Refresh (DX) | 핫 리로드 (DX) |
| devtools | DevTools / Observability for Developers | 데브툴스 |
| backstage-idp | Internal Developer Portal (Backstage) | 내부 개발자 포털 |

### Blockchain / Web3 (blockchain.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| consensus-blockchain | Consensus Mechanism (PoW/PoS/PBFT/DPoS/PoA) | 합의 메커니즘 |
| smart-contract-upgrade | Smart Contract Upgrade (Proxy Pattern) | 스마트 컨트랙트 업그레이드 |
| oracle-pattern | Oracle Pattern | 오라클 패턴 |
| gas-optimization | Gas Optimization | 가스 최적화 |
| custody-mpc-multisig | Custody (Self / MPC / Multi-sig) | 커스터디 (MPC/멀티시그) |
| event-indexer-graph | Event Indexer (The Graph) | 이벤트 인덱서 |
| token-standard-erc | Token Standard (ERC-20 / 721 / 1155) | 토큰 표준 |
| layer-2-scaling | Layer 2 Scaling | L2 스케일링 |
| mev | MEV (Maximal Extractable Value) | MEV |
| cross-chain-bridge | Cross-chain Bridge | 크로스체인 브릿지 |

### 요구공학 (requirements-engineering.md) — 10
| ID | 영문명 | 한글명 |
|----|--------|--------|
| user-story | User Story | 사용자 스토리 |
| invest | INVEST 원칙 | INVEST |
| moscow | MoSCoW Prioritization | 모스카우 우선순위 |
| use-case | Use Case | 유스 케이스 |
| job-stories | Job Stories | 잡 스토리 |
| event-storming | Event Storming | 이벤트 스토밍 |
| example-mapping | Example Mapping | 예시 매핑 |
| gherkin-given-when-then | Gherkin / Given-When-Then | Gherkin GWT |
| impact-mapping | Impact Mapping | 임팩트 매핑 |
| three-amigos | Three Amigos | 쓰리 아미고 |

---

## 카테고리 선택 가이드

- 클래스/객체 수준 디자인: GoF 생성/구조/행위
- 애플리케이션 전체 구조: 아키텍처 패턴 (MVC/MVVM/MVI, Clean/Hexagonal/Microservices)
- 도메인 모델링·집합 경계·도메인 이벤트: DDD 전술 패턴 (Aggregate/Value Object/Domain Event/ACL)
- 영속성·ORM·쿼리 추상화: 데이터 접근 패턴 (Repository/Unit of Work/Data Mapper/Specification)
- 여러 서비스 간 데이터 일관성: 분산 시스템 패턴 (CQRS/Saga/Outbox)
- 장애 격리·회복력: 신뢰성 패턴 (Circuit Breaker/Retry/Bulkhead)
- 멀티스레드 안전성: 동시성 패턴 (Thread Pool/Actor/CSP/STM/Structured Concurrency)
- 메시지/이벤트 통합: 엔터프라이즈 통합 패턴 (Pipes&Filters/Pub-Sub/Wire Tap/Claim Check/Process Manager)
- 보안·인증·인가·암호 운영·데이터 보호·API/Web 공격 방어·공급망·플랫폼·SDLC·탐지/IR·모바일·AI 모델·규제 컴플라이언스: 별도 도메인 [`../security/`](../security/) 참조
- 테스트 전략·이중 객체: 테스트 패턴 (Test Pyramid/AAA/Test Double/Property-Based/Contract Test)
- 운영 가시성·SLO·트레이싱: Observability 패턴 (Three Pillars/Distributed Tracing/RED/USE/Golden Signals/SLO)
- LLM 애플리케이션 구조: AI/LLM 패턴 (RAG/Tool Use/Agent Loop/Multi-Agent/Guardrails/HITL)
- 무중단 배포·점진 출시: 배포 패턴 (Blue-Green/Canary/Feature Flag/Strangler Fig/Expand-Contract)
- 성능 최적화·캐시 일관성: 캐싱 패턴 (Cache-Aside/Read-Through/Write-Through/Stampede 방지/Multi-Tier)

### Phase 2 확장 카테고리 선택 가이드

**Governance (거버넌스)**
- 코드 악취·반복 실패 패턴 식별·교정: [안티패턴](anti-patterns.md) (Big Ball of Mud/God Object/Anemic/Distributed Monolith/Golden Hammer)
- 예외·결과 모델·에러 흐름 설계: [에러 처리](error-handling.md) (Exception/Result-Either/Railway/Option/Fail-Fast/보상 트랜잭션)
- 테스트 없는 레거시에 안전 변경 도입: [레거시 코드 작업](legacy-code.md) (Seam/Characterization Test/Sprout/Wrap/Mikado)
- 모호한 요구를 검증 가능한 명세로: [요구공학](requirements-engineering.md) (User Story/INVEST/MoSCoW/Event Storming/Gherkin)
- 클라우드 비용 추적·최적화·예산 가드: [FinOps](finops.md) (Unit Economics/Rightsizing/Spot/Tagging/Budget Guardrails)
- 개발자 생산성·내부 플랫폼 도구: [DX Engineering](dx-engineering.md) (Scaffolding/Codegen/LSP/Devcontainer/Backstage)

**Context (플랫폼·문맥)**
- 모바일 앱 운영·생명주기·푸시·배포: [모바일 앱](mobile-app.md) (App Lifecycle/Deep Link/IAP/OTA/App Signing/Permission UX)
- 실시간/안전성 임베디드 시스템: [임베디드/RTOS](embedded.md) (RMS/EDF/WCET/ISR/Watchdog/Ring Buffer/Memory Pool)
- 게임 엔진·런타임 아키텍처: [게임 개발](game-dev.md) (Game Loop/ECS/Spatial Partition/Scene Graph/Netcode)
- 단일 코드베이스로 멀티 플랫폼 출시: [크로스플랫폼](crossplatform.md) (Flutter/RN New Arch/KMP/Expo/Capacitor/Tauri/CMP)
- 네트워크 단절에도 동작하는 클라이언트: [Offline-First](offline-first.md) (Local-First DB/Sync Queue/Conflict Resolution/Tombstone/Delta Sync)
- 웹 렌더링 전략·SEO·TTI 트레이드오프: [Web 렌더링](web-rendering.md) (CSR/SSR/SSG/ISR/Streaming SSR/Islands/RSC/Edge)
- 프론트엔드 상태 분류·도구 선택: [상태 관리](state-management.md) (Single Store/Atomic/Signal/Server State/Form State/CRDT)
- 사용자 인터페이스 일관성·접근성: [UI/UX](ui-ux.md) (Atomic Design/Container-Presenter/Skeleton/A11y/Design Tokens)

**Infrastructure (인프라·통신)**
- 전송계층 프로토콜 선택·튜닝: [네트워크](networking.md) (TCP/UDP/QUIC/HTTP3/TLS/CDN/WebSocket/WebRTC)
- HTTP API 설계 표준·명명·페이지네이션·에러: [API 설계](api-design.md) (Richardson/HATEOAS/AIP/Versioning/Pagination/Idempotency/LRO/RFC7807)
- 통신 스타일 선택 (RPC/스트림/이벤트): [API 스타일](api-styles.md) (REST/GraphQL/gRPC/WebSocket/SSE/Webhook/JSON-RPC/WebTransport)
- 장기 실행·DAG·재시도 가능한 작업 흐름: [워크플로우/잡](workflow-jobs.md) (Durable/DAG/Job Queue/Saga/Scheduled/Worker Leasing)
- 스트림 처리 (Flink/Kafka Streams) 의미론: [스트림 처리 의미론](streaming-semantics.md) (Delivery/Event Time/Watermark/Windowing/Triggering/Checkpoint)
- 분산 데이터 복제·일관성·샤딩 전략: [데이터 일관성·복제](data-modeling.md) (CAP/PACELC/Single/Multi/Leaderless/Consistent Hashing/CDC/HTAP)
- 모노레포·SemVer·재현 가능 빌드: [빌드·버전 관리](build-versioning.md) (Monorepo/Polyrepo/SemVer/CalVer/Hermetic/Reproducible)
- ML 모델 운영·드리프트·피처스토어: [MLOps](mlops.md) (Feature Store/Model Registry/Data Drift/Shadow/Online vs Batch/Data Contract)

**Paradigm (패러다임)**
- 부수효과 분리·합성 가능한 도메인 로직: [함수형](functional.md) (Functor/Applicative/Monad/Free/Lens/Tagless/Effect Handlers)
- 비동기 데이터 흐름·백프레셔: [Reactive Streams & FRP](reactive-streams.md) (Spec/Cold-Hot/Subject/Marble/Backpressure/FRP)

**Domain (도메인 모델링)**
- 컨텍스트 경계·통합 관계·DDD 전략 결정: [DDD 전략](ddd-strategic.md) (Ubiquitous Language/Subdomain/Bounded Context/Context Map/Customer-Supplier/Conformist/ACL/OHS/Published Language)

**Quality (품질·검증)**
- 부하·카오스·실험 기반 테스트: [테스트 전략](testing-strategies.md) (Pyramid/Trophy/Diamond/Honeycomb 비교, Chaos/Load/Stress/Spike/Soak, A/B, Synthetic, Canary Analysis, Shadow)

**Industry (산업 도메인)**
- 결제·정산·원장·규제 (PCI/AML): [Fintech](domains/fintech.md) (Double-Entry/Ledger/Reconciliation/Idempotent Payment/3DS/Saga/FX/Refund/AML-KYC/PCI Scope/Subscription)
- 의료·EHR·HIPAA·임상 의사결정: [Healthcare](domains/healthcare.md) (FHIR R5/HL7 v2/SMART on FHIR/CDS Hooks/Consent/PHI Audit/De-identification/DICOM/IHE)
- 상품·재고·주문·결제·풀필먼트: [eCommerce](domains/ecommerce.md) (Cart/Inventory/Catalog/Pricing/Order State/Checkout/Fulfillment/RMA/Search/Recommendation/Marketplace/Loyalty)
- 경로·차량·실시간 위치·라스트마일: [Logistics](domains/logistics.md) (VRP/Realtime Tracking/ETA/Geofencing/Fleet Dispatch/Last-Mile/Reverse/Cross-Docking/Capacity)
- 디바이스 트윈·OTA·엣지 추론·MQTT: [IoT/Edge](domains/iot-edge.md) (Device Twin/OTA/Telemetry Buffer/Provisioning/Edge Gateway/MQTT/Edge ML/Time-Series/C2/mTLS)
- 합의·스마트 컨트랙트·L2·MEV·커스터디: [Blockchain](blockchain.md) (Consensus/Proxy Upgrade/Oracle/Gas Opt/MPC/Indexer/ERC/L2/MEV/Bridge)
