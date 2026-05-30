# 분산 시스템 패턴 (Distributed Patterns)

여러 서비스/노드 간 데이터 일관성, 트랜잭션, 통신을 다루는 패턴.

---

## 1. CQRS (Command Query Responsibility Segregation)

**목적**: 쓰기(Command) 모델과 읽기(Query) 모델을 분리하여 각각을 독립적으로 최적화합니다.

**특징**:
- Command는 상태 변경, Query는 읽기 전용
- 쓰기 DB와 읽기 DB를 분리할 수 있음 (Materialized View)
- 비대칭 워크로드(읽기 ≫ 쓰기)에 효과적

**장점**:
- 읽기/쓰기 독립 스케일링
- 도메인 모델 단순화 (한쪽 책임만)
- 읽기 모델을 화면에 맞게 비정규화 가능

**단점**:
- 시스템 복잡도 증가
- 읽기/쓰기 동기화 지연 (Eventual consistency)
- 모델 중복 관리

**활용 예시**:
- 주문/결제 시스템 (쓰기 ≪ 조회)
- Axon Framework
- Event Sourcing과 결합한 마이크로서비스

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// Command side
data class CreateOrder(val id: String, val amount: Int)
class OrderCommandHandler(private val writeRepo: OrderWriteRepo) {
    fun handle(cmd: CreateOrder) = writeRepo.save(cmd)
}

// Query side (separate read model)
data class OrderView(val id: String, val amount: Int, val displayDate: String)
class OrderQueryHandler(private val readRepo: OrderReadRepo) {
    fun byId(id: String): OrderView? = readRepo.findView(id)
}
```

**관련 패턴**: Event Sourcing, Event-Driven, Mediator

---

## 2. Event Sourcing

**목적**: 현재 상태를 저장하는 대신 모든 상태 변경 이벤트를 시퀀스로 누적 저장하고, 재생(replay)으로 상태를 복원합니다.

**특징**:
- Append-only 이벤트 스토어
- 현재 상태 = 이벤트 시퀀스의 fold
- 과거 임의 시점 상태 복원 가능

**장점**:
- 완전한 감사 로그 (audit trail)
- 시간 여행 디버깅
- 새로운 read model을 과거 이벤트로 재구축

**단점**:
- 이벤트 스키마 진화 어려움
- 초기 학습 곡선 가파름
- 스냅샷 전략 필요 (긴 시퀀스 재생 비용)

**활용 예시**:
- 회계/금융 거래 시스템
- 깃 커밋 히스토리
- EventStoreDB, Axon

**난이도**: 매우 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
sealed class AccountEvent {
    data class Deposited(val amount: Int) : AccountEvent()
    data class Withdrew(val amount: Int) : AccountEvent()
}

class Account(events: List<AccountEvent>) {
    val balance: Int = events.fold(0) { acc, e ->
        when (e) {
            is AccountEvent.Deposited -> acc + e.amount
            is AccountEvent.Withdrew -> acc - e.amount
        }
    }
}
```

**관련 패턴**: CQRS, Event-Driven, Memento

---

## 3. Saga (Choreography)

**목적**: 분산 트랜잭션을 중앙 코디네이터 없이 각 서비스가 이벤트 발행/구독으로 협력해 처리하고, 실패 시 보상 트랜잭션을 발행합니다.

**특징**:
- 중앙 제어자 없음 (Peer-to-peer 이벤트 흐름)
- 각 서비스는 다음 이벤트를 자율적으로 발행
- 실패 시 역방향 보상 이벤트

**장점**:
- 서비스 간 결합도 낮음
- 단일 장애점 없음
- 마이크로서비스 자율성 보존

**단점**:
- 전체 흐름 파악 어려움 (cyclic dependency 위험)
- 디버깅 난이도 높음
- 이벤트 누락 시 stuck 상태

**활용 예시**:
- 전자상거래 주문 → 결제 → 배송
- 호텔+항공 예약 결합
- 마이크로서비스 데이터 일관성

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// OrderService publishes
EventBus.publish("OrderCreated", OrderCreated(id, amount))

// PaymentService subscribes
EventBus.subscribe("OrderCreated") { e ->
    val ok = pg.charge((e as OrderCreated).amount)
    EventBus.publish(if (ok) "PaymentSucceeded" else "PaymentFailed", e.orderId)
}

// OrderService compensates on failure
EventBus.subscribe("PaymentFailed") { id -> orderRepo.cancel(id as String) }
```

**관련 패턴**: Saga Orchestration, Event-Driven, Outbox

---

## 4. Saga (Orchestration)

**목적**: 중앙 Orchestrator가 분산 트랜잭션의 각 단계를 호출하고 실패 시 보상 명령을 명시적으로 지휘합니다.

**특징**:
- Orchestrator가 워크플로 상태 머신 유지
- 각 서비스에 명령 전송 + 응답 수신
- 실패 시 역순으로 보상 명령 발행

**장점**:
- 흐름이 한 곳에 명시 → 가독성/디버깅 우수
- 복잡한 분기/조건 처리 용이
- 상태 추적 단순

**단점**:
- Orchestrator가 단일 장애점/병목
- 서비스가 Orchestrator에 결합됨
- Orchestrator 비대화 위험

**활용 예시**:
- Camunda, Temporal, AWS Step Functions
- 복잡한 워크플로(여행 예약, 대출 심사)
- 보험 청구 처리

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
class BookingSaga(
    private val flight: FlightService,
    private val hotel: HotelService,
) {
    suspend fun execute(req: BookingRequest) {
        val f = runCatching { flight.book(req) }
        val h = runCatching { hotel.book(req) }
        if (f.isFailure || h.isFailure) {
            f.getOrNull()?.let { flight.cancel(it) }
            h.getOrNull()?.let { hotel.cancel(it) }
            error("Booking failed, compensated")
        }
    }
}
```

**관련 패턴**: Saga Choreography, Command, State

---

## 5. Outbox Pattern

**목적**: 데이터베이스 트랜잭션과 메시지 발행을 원자적으로 처리하기 위해, 이벤트를 같은 DB의 outbox 테이블에 함께 기록하고 별도 publisher가 메시지 브로커로 전송합니다.

**특징**:
- DB write + 이벤트 기록을 단일 트랜잭션으로
- Publisher가 outbox를 폴링하거나 CDC로 읽어 발행
- At-least-once 전달 보장

**장점**:
- DB와 메시지 브로커 간 일관성 (2PC 없이)
- 메시지 손실 방지
- 재시도/재발행 단순

**단점**:
- Publisher 인프라 필요 (Debezium 등)
- 발행 지연 발생
- outbox 테이블 정리 정책 필요

**활용 예시**:
- 이벤트 기반 마이크로서비스
- Debezium + Kafka CDC 파이프라인
- 본 프로젝트의 Server → Slack/ClickUp 발송에도 유사 적용 가능

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// inside one DB transaction
transaction {
    orderRepo.save(order)
    outboxRepo.insert(OutboxRow(topic = "order.created", payload = order.toJson()))
}

// background publisher
class OutboxPublisher(private val outbox: OutboxRepo, private val broker: Broker) {
    fun tick() {
        outbox.fetchPending(limit = 100).forEach {
            broker.publish(it.topic, it.payload)
            outbox.markSent(it.id)
        }
    }
}
```

**관련 패턴**: Event-Driven, Saga, CQRS

---

## 6. Idempotency Key

**목적**: 동일 요청이 네트워크 재시도로 중복 도착해도 한 번만 처리되도록 클라이언트가 발급한 고유 키로 결과를 캐시합니다.

**특징**:
- 클라이언트가 UUID 같은 키를 헤더(`Idempotency-Key`)로 전송
- 서버는 (키, 응답)을 저장하여 재요청 시 캐시 응답
- 만료 정책으로 키 수명 관리

**장점**:
- 결제/주문 등 부작용 있는 API 안전 재시도
- At-least-once 환경에서 exactly-once 효과
- 클라이언트 UX 안정 (네트워크 오류 무서움 감소)

**단점**:
- 키 저장소 필요 (Redis 등)
- 요청 본문 hash 검증 필요 (동일 키 다른 본문 방지)
- TTL 선택의 트레이드오프

**활용 예시**:
- Stripe Idempotency-Key 헤더
- 결제 API
- 주문 생성 API

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class PaymentApi(private val cache: IdempotencyStore, private val pg: Gateway) {
    fun pay(key: String, req: PayRequest): PayResponse {
        cache.get(key)?.let { return it }
        val res = pg.charge(req)
        cache.put(key, res, ttl = Duration.ofHours(24))
        return res
    }
}
```

**관련 패턴**: Retry, Circuit Breaker, Outbox

---

## 7. BFF (Backend For Frontend)

**목적**: 각 프론트엔드(웹/모바일/IoT) 별로 전용 백엔드를 두어 클라이언트가 필요한 형태로 응답을 가공/집계합니다.

**특징**:
- 클라이언트별 1:1 백엔드
- 다운스트림 마이크로서비스 호출 집계
- 클라이언트 팀이 BFF를 소유하는 경우 많음

**장점**:
- 클라이언트별 최적화된 응답 (over-fetch/under-fetch 해소)
- 프론트엔드 팀 자율성
- 모바일 트래픽/배터리 절감

**단점**:
- BFF 수만큼 코드 중복
- 다운스트림 변경 시 모든 BFF 영향
- 운영 부담 증가

**활용 예시**:
- Netflix (디바이스별 BFF)
- SoundCloud (모바일/웹 BFF 분리)
- GraphQL을 BFF 계층으로 사용

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Mobile BFF aggregates multiple services
class MobileHomeBff(
    private val user: UserService,
    private val feed: FeedService,
    private val ads: AdService,
) {
    suspend fun home(userId: String): MobileHomeDto = coroutineScope {
        val u = async { user.get(userId) }
        val f = async { feed.top(userId, limit = 20) }
        val a = async { ads.forUser(userId) }
        MobileHomeDto(u.await(), f.await(), a.await())
    }
}
```

**관련 패턴**: API Gateway, Facade, Microservices

---

## 8. API Gateway

**목적**: 클라이언트 요청의 단일 진입점에서 라우팅, 인증, 속도 제한, 로깅, 응답 집계를 처리하여 다운스트림 마이크로서비스의 횡단 관심사를 통합합니다.

**특징**:
- 단일 endpoint → 내부 서비스로 분기
- Cross-cutting concerns (auth, rate limit, observability)
- 응답 조합/변환 가능

**장점**:
- 클라이언트가 내부 토폴로지를 모름
- 인증/로깅 중앙화
- 버전 관리 / 카나리 라우팅 용이

**단점**:
- Gateway가 단일 장애점/병목
- Gateway 비대화 위험 (Smart Gateway anti-pattern)
- 추가 홉 → 지연 증가

**활용 예시**:
- Kong, AWS API Gateway, Spring Cloud Gateway
- Kubernetes Ingress
- 마이크로서비스 전면 게이트웨이

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Ktor-based simple gateway
fun Application.gateway(client: HttpClient) = routing {
    intercept(ApplicationCallPipeline.Plugins) {
        if (!call.request.headers.contains("Authorization")) {
            call.respond(HttpStatusCode.Unauthorized); finish()
        }
    }
    route("/users/{...}") {
        handle {
            val res = client.get("http://user-svc${call.request.uri.removePrefix("/users")}")
            call.respondText(res.bodyAsText(), status = res.status)
        }
    }
}
```

**관련 패턴**: BFF, Proxy, Facade, Service Mesh

---

## 9. Service Mesh

**목적**: 마이크로서비스 간 통신을 sidecar 프록시로 인프라화하여 트래픽 관리, mTLS, 관측성을 애플리케이션 코드 변경 없이 제공합니다.

**특징**:
- 각 서비스 옆에 sidecar(Envoy 등) 배치
- 컨트롤 플레인(Istio, Linkerd)이 정책 배포
- L7 라우팅, 재시도, 회로 차단기 내장

**장점**:
- 애플리케이션 코드 비침투적
- mTLS 자동 (Zero Trust)
- 카나리/A-B, 트래픽 미러링 기본 지원

**단점**:
- 운영 복잡도 매우 높음
- sidecar 리소스 오버헤드
- 학습 곡선 가파름

**활용 예시**:
- Istio + Envoy (Kubernetes)
- Linkerd
- Consul Connect

**난이도**: 매우 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// app code stays oblivious; sidecar handles mTLS/retry/timeouts.
// declarative policy lives in YAML, e.g.:
// apiVersion: networking.istio.io/v1
// kind: VirtualService
// spec:
//   http:
//     - route: [{ destination: { host: order, subset: v2 }, weight: 10 }]

class OrderClient(private val http: HttpClient) {
    suspend fun place(req: OrderReq): HttpResponse =
        http.post("http://order/api/v1/orders") { setBody(req) } // sidecar intercepts
}
```

**관련 패턴**: API Gateway, Microservices, Proxy

---

<a id="tcc-try-confirm-cancel"></a>

## 10. TCC (Try-Confirm-Cancel)

**목적**: 분산 트랜잭션을 3단계(Try / Confirm / Cancel)로 분리하여 리소스를 사전 예약하고, 모든 참가자의 Try 가 성공하면 Confirm, 하나라도 실패하면 Cancel 하여 원자성을 달성합니다.

**3 Phase**:
- **Try**: 비즈니스 리소스를 예약(reserve) — 재고 차감 대신 "예약 상태" 로 잠금, 잔액 차감 대신 "동결(freeze)"
- **Confirm**: Try 에서 예약된 자원을 실제 차감/확정. 멱등성 필수, 재시도해도 동일 결과
- **Cancel**: Try 에서 예약된 자원을 해제(release). 멱등성 필수, Try 실패 시에도 안전 호출

**Saga 와의 차이**:
- **Saga**: 즉시 commit → 실패 시 **보상(compensation) 트랜잭션** 으로 역효과 발행. 중간 상태가 외부에 노출됨
- **TCC**: Try 단계에서 **예약(reservation)** 만 잠금 → 외부에 미공개 상태로 격리. Cancel 은 보상이 아니라 "예약 해제"
- Saga 는 단순/장기 워크플로, TCC 는 짧고 강한 격리가 필요한 결제/재고에 적합

**Reservation 패턴 (핵심)**:
- 자원 상태를 `available / reserved / confirmed / cancelled` 4가지로 모델링
- Try 는 `available → reserved` 전이만, Confirm 은 `reserved → confirmed`, Cancel 은 `reserved → available`
- 외부 조회는 `confirmed` 만 노출 → 중간 상태 누출 차단

**특징 / 요구사항**:
- **Idempotency**: Confirm/Cancel 은 네트워크 재시도로 중복 호출 가능 → 트랜잭션 ID 로 멱등 처리
- **Timeout & Recovery**: Try 후 Confirm/Cancel 누락 시 타임아웃 → 자동 Cancel 보장 (TCC 코디네이터가 주기적 sweep)
- **비즈니스 잠금**: DB row lock 이 아니라 "예약" 이라는 비즈니스 상태로 잠금 → 장기 트랜잭션도 DB 리소스 점유 없음
- **Null Compensation 방지**: Try 가 도착 전 Cancel 이 먼저 도착하는 경우 → "공허한 보상(empty compensation)" 처리, Cancel 기록을 남겨 후행 Try 차단

**장점**:
- 강한 일관성에 가까운 격리 (중간 상태 미노출)
- 보상 트랜잭션의 부작용 우려 해소 (재고 환불 시점차 등)
- 짧은 트랜잭션 → 높은 처리량
- DB lock 없이 비즈니스 수준 잠금

**단점**:
- 모든 참가 서비스가 Try/Confirm/Cancel 3 API 제공해야 함 → 침투적
- 비즈니스 로직에 예약 상태 모델링 강제
- 멱등성/타임아웃/null compensation 처리 복잡
- 레거시 시스템 적용 어려움 (3 API 강제 불가)

**활용 예시**:
- 결제 (잔액 동결 → 확정 / 환불)
- 항공/호텔 예약 (좌석 hold → confirm / release)
- 쿠폰 사용 (선점 → 확정 / 반환)
- 본 프로젝트 클라이언트→서버 결제 흐름의 예약/확정 분리

**구현 비교**:
- **Seata TCC mode**: Alibaba 의 분산 트랜잭션 프레임워크. `@TwoPhaseBusinessAction` 어노테이션으로 Try/Confirm/Cancel 메서드 지정. Transaction Coordinator(TC) 가 글로벌 트랜잭션 ID 관리, 멱등/타임아웃/null compensation 내장
- **EventuateTram**: Saga 중심. TCC 는 Saga 의 한 형태로 표현 가능하나 native TCC 지원은 약함. Saga orchestration + reservation 패턴 직접 구현 권장
- **선택 기준**: 강한 격리 + 짧은 트랜잭션 → Seata TCC. 장기 워크플로 + 느슨한 일관성 → EventuateTram Saga

**난이도**: 매우 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
// Try / Confirm / Cancel 3 API 를 가진 결제 서비스
interface PaymentTcc {
    fun tryFreeze(txId: String, userId: String, amount: Int): Boolean  // 잔액 동결
    fun confirm(txId: String): Boolean                                  // 동결 → 차감
    fun cancel(txId: String): Boolean                                   // 동결 해제
}

class PaymentTccImpl(private val repo: PaymentRepo) : PaymentTcc {
    override fun tryFreeze(txId: String, userId: String, amount: Int): Boolean = transaction {
        // 멱등성: 동일 txId 재호출 시 기존 결과 반환
        repo.findReservation(txId)?.let { return@transaction it.status == "RESERVED" }
        val bal = repo.balance(userId)
        if (bal < amount) return@transaction false
        repo.insertReservation(txId, userId, amount, status = "RESERVED")
        repo.freezeBalance(userId, amount)
        true
    }

    override fun confirm(txId: String): Boolean = transaction {
        val r = repo.findReservation(txId) ?: return@transaction false  // null comp 방지
        if (r.status == "CONFIRMED") return@transaction true             // 멱등
        if (r.status == "CANCELLED") return@transaction false
        repo.deductFrozen(r.userId, r.amount)
        repo.updateStatus(txId, "CONFIRMED")
        true
    }

    override fun cancel(txId: String): Boolean = transaction {
        val r = repo.findReservation(txId)
        if (r == null) {
            // 공허한 보상: Try 가 아직 안 옴 → cancel 기록만 남겨 후행 Try 차단
            repo.insertReservation(txId, userId = "", amount = 0, status = "CANCELLED")
            return@transaction true
        }
        if (r.status == "CANCELLED") return@transaction true            // 멱등
        if (r.status == "CONFIRMED") return@transaction false           // 이미 확정
        repo.releaseFrozen(r.userId, r.amount)
        repo.updateStatus(txId, "CANCELLED")
        true
    }
}

// Coordinator: 모든 참가자 Try → 전체 성공 시 Confirm, 아니면 Cancel
class TccCoordinator(private val participants: List<PaymentTcc>) {
    fun execute(txId: String, ops: List<() -> Boolean>): Boolean {
        val results = ops.map { runCatching { it() }.getOrDefault(false) }
        return if (results.all { it }) {
            participants.forEach { it.confirm(txId) }; true
        } else {
            participants.forEach { it.cancel(txId) }; false
        }
    }
}
```

**관련 패턴**: Saga, Outbox, Idempotency Key, Reservation, 2PC

**Cross-link**:
- 메시지 전달 보장: [`patterns/integration.md#message-broker-selection-matrix`](../patterns/integration.md#message-broker-selection-matrix)
- 합의 알고리즘 (코디네이터 가용성): [`algorithms/consensus.md`](../algorithms/consensus.md)
- ACID vs BASE 절충: [`principles/database-fundamentals.md#acid-vs-base`](../../../data-advisor/references/principles/db-fundamentals.md#acid-vs-base)
- 예약 상태 데이터 모델링: [`patterns/data-modeling.md`](../patterns/data-modeling.md)

---

<a id="distributed-transaction-selection-matrix"></a>

## 11. Distributed Transaction Selection Matrix

**목적**: 분산 트랜잭션 패턴 선택 시 일관성/가용성/운영 복잡도/실패 처리/성능 트레이드오프를 한눈에 비교하여 시스템 요구사항에 맞는 패턴을 선택합니다.

**패턴 개요**:

- **2PC (Two-Phase Commit)**: Prepare → Commit 2단계. 코디네이터가 모든 참가자에게 Prepare 요청 → 모두 "yes" 응답 시 Commit, 하나라도 실패 시 Abort. **동기/Blocking** — 모든 참가자가 응답할 때까지 대기. **Coordinator 단일 실패** — 코디네이터 장애 시 참가자가 "in-doubt" 상태로 무한 대기. XA 표준이 대표적
- **3PC (Three-Phase Commit)**: Prepare → PreCommit → Commit 3단계. 2PC 의 blocking 문제 완화 위해 PreCommit 단계 추가, 타임아웃 시 참가자가 자율 결정 가능. **여전히 네트워크 분할 취약** — split-brain 시 일관성 깨질 수 있음. 실제 운영에서 거의 사용 안 됨
- **Saga (Orchestration / Choreography)**: 즉시 commit, 실패 시 **보상 트랜잭션** 으로 역효과 발행. 중간 상태가 외부에 노출됨. Eventually consistent. 장기 워크플로에 적합 ([§3, §4](#3-saga-choreography) 참조)
- **TCC (Try-Confirm-Cancel)**: 3단계 **예약 기반**. Try 에서 자원 예약 → Confirm/Cancel. 강한 격리, 중간 상태 미노출. 모든 참가자가 3 API 제공 필요 ([§10](#tcc-try-confirm-cancel) 참조)
- **Outbox Pattern**: **메시지 보장 + DB 트랜잭션** 결합. DB write 와 이벤트 기록을 원자적으로 처리, publisher 가 비동기 발행. 분산 트랜잭션 자체보다 "DB ↔ 메시지 브로커 일관성" 해결책 ([§5](#5-outbox-pattern) 참조)

**비교 매트릭스**:

| 패턴 | Consistency | Availability | Operational Complexity | Failure Handling | Performance | 적합 시나리오 |
|------|-------------|--------------|------------------------|------------------|-------------|---------------|
| 2PC | Strong (ACID) | Low (Coordinator SPOF) | 높음 (XA 인프라) | Blocking, in-doubt | 낮음 (동기 대기) | 단일 DC 내 동종 RDB, 짧은 트랜잭션 |
| 3PC | Strong (이론) | Medium | 매우 높음 | Non-blocking, split-brain 취약 | 매우 낮음 (3 round) | 거의 미사용 |
| Saga Choreography | Eventual | High | 중간 (이벤트 추적 난이도) | 보상 트랜잭션, 부분 노출 | 높음 (비동기) | 마이크로서비스 장기 워크플로 |
| Saga Orchestration | Eventual | Medium (Orchestrator) | 중간 (워크플로 엔진) | 보상 + 명시적 상태 추적 | 중간 | 복잡한 분기 워크플로 |
| TCC | Strong (격리) | Medium | 매우 높음 (3 API 강제) | 멱등 + 타임아웃 sweep | 중간 (3 round, 짧음) | 결제/예약, 강한 격리 필요 |
| Outbox | Eventual | High | 낮음 (CDC 인프라) | At-least-once + 멱등 | 높음 | DB ↔ 메시지 브로커 일관성 |

**선택 가이드 (의사결정 트리)**:

- **단일 DC, 동종 RDB, 짧은 트랜잭션, ACID 필수** → 2PC (XA)
- **마이크로서비스, 장기 워크플로, eventual OK, 단순 흐름** → Saga Choreography
- **마이크로서비스, 복잡한 분기/조건, 상태 추적 필요** → Saga Orchestration (Camunda/Temporal)
- **결제/재고/예약, 중간 상태 미노출 필수, 짧은 트랜잭션** → TCC
- **DB ↔ Kafka 일관성, 메시지 손실 방지** → Outbox Pattern
- **여러 패턴 조합**: Saga + Outbox (이벤트 보장) / TCC + Idempotency Key (안전 재시도) 가 실무 표준

**Anti-patterns**:
- 마이크로서비스 + 2PC: 서비스 자율성/가용성 파괴, 안티패턴
- 단순 CRUD + TCC: 과잉 설계, 3 API 강제로 개발 비용 폭증
- Saga + 중간 상태 노출 허용 안 되는 도메인 (결제 잔액 등): TCC 로 전환
- Outbox 없이 "DB commit 후 메시지 발행": 메시지 손실 위험

**Cross-link**:
- 메시지 전달 보장 / 브로커 선택: [`patterns/integration.md#message-broker-selection-matrix`](../patterns/integration.md#message-broker-selection-matrix)
- 코디네이터 가용성 / 합의: [`algorithms/consensus.md`](../algorithms/consensus.md)
- ACID vs BASE 절충 기초: [`principles/database-fundamentals.md#acid-vs-base`](../../../data-advisor/references/principles/db-fundamentals.md#acid-vs-base)
- 예약/이벤트 데이터 모델링: [`patterns/data-modeling.md`](../patterns/data-modeling.md)

**관련 패턴**: 2PC, Saga, TCC, Outbox, Idempotency Key

---

<a id="valet-key"></a>
## 12. Valet Key (밸릿 키)

**목적**: 클라이언트가 데이터 스토어에 직접 접근하도록 제한적·시한적 접근 토큰(밸릿 키)을 발급하여, 대용량 업로드/다운로드 트래픽이 애플리케이션 서버를 경유하지 않도록 우회시킵니다.

**특징**:
- 토큰에 권한 범위(특정 리소스, read/write)와 만료 시각을 새겨 발급
- 클라이언트는 토큰으로 스토리지(S3, Blob)에 직접 I/O
- 서버는 인증/인가 후 토큰 발급만 담당 (데이터 평면에서 빠짐)

**장점**:
- 서버 CPU/메모리/대역폭 부하 우회 (서버는 control plane만)
- 대용량 파일 전송 비용/지연 절감
- 권한 범위·만료로 노출 영향 최소화 (최소 권한)

**단점**:
- 토큰 발급 후에는 즉시 취소가 어려움 (만료까지 유효)
- 토큰 유출 시 만료 전까지 무단 접근 위험
- 스토리지가 토큰 기반 직접 접근을 지원해야 함

**활용 예시**:
- AWS S3 Pre-signed URL (PUT/GET)
- Azure Storage SAS (Shared Access Signature)
- GCS Signed URL, 사용자 프로필 이미지 직접 업로드

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// S3 Pre-signed URL 발급 — 서버는 토큰만 발급, 업로드는 클라이언트가 직접 수행
class FileUploadService(private val presigner: S3Presigner) {
    fun issueUploadUrl(userId: String, key: String): String {
        // 인가: 본인 경로만 허용 (권한 범위 제한)
        require(key.startsWith("users/$userId/")) { "forbidden path" }

        val putReq = PutObjectRequest.builder()
            .bucket("user-uploads")
            .key(key)
            .contentType("image/jpeg")
            .build()

        // 만료 제한: 15분 시한부 토큰
        val presignReq = PutObjectPresignRequest.builder()
            .signatureDuration(Duration.ofMinutes(15))
            .putObjectRequest(putReq)
            .build()

        return presigner.presignPutObject(presignReq).url().toString()
    }
}

// 클라이언트: 발급받은 URL로 스토리지에 직접 PUT (서버 미경유)
suspend fun uploadDirect(url: String, bytes: ByteArray) {
    httpClient.put(url) { setBody(bytes) }  // 트래픽이 앱 서버를 거치지 않음
}
```

**관련 패턴**: API Gateway, Idempotency Key, BFF, Gatekeeper

---

<a id="deployment-stamps"></a>

## 13. Deployment Stamps / Geode (배포 스탬프 / 지오드)

**목적**: 애플리케이션과 데이터 저장소를 포함한 풀스택을 하나의 독립 단위(stamp, 또는 scale unit / service unit)로 묶어 복제 배포하여, 테넌트/리전을 스탬프 단위로 분리하고 장애 전파 범위(blast radius)를 격리하면서 수평 확장합니다. Geode 는 이 스탬프를 지리적으로 분산 배치하고 모든 노드가 read/write 를 처리하도록 확장한 변형입니다.

**두 패턴의 관계**:
- **Deployment Stamps**: 동일한 풀스택 단위를 N개 복제. 각 스탬프는 자족적(self-contained) — 자체 DB, 자체 컴퓨트, 자체 캐시 보유. 테넌트/지역을 스탬프에 할당(샤딩 by stamp)
- **Geode (Geographical Node)**: 스탬프를 여러 지리 리전에 배치하고, 각 노드가 **active-active 로 read 와 write 를 모두** 처리. 사용자는 가장 가까운 노드로 라우팅(geo-routing). 데이터는 노드 간 비동기 복제로 수렴
- 즉 Geode = "지리 분산 + 모든 노드 write 가능" 으로 확장된 Deployment Stamps

**특징**:
- 스탬프는 풀스택 단위(컴퓨트 + 데이터 + 의존 리소스)로 통째 복제됨
- 테넌트(또는 사용자/지역)를 스탬프에 매핑하는 **traffic routing 계층** 필요 (어떤 스탬프로 보낼지 결정)
- 각 스탬프는 자체 데이터 저장소 → 스탬프 간 데이터 공유 없음(shared-nothing)
- 스탬프 단위 배포/롤아웃 → 카나리·블루그린을 스탬프 granularity 로 수행
- Geode 는 다중 마스터 쓰기 → **충돌 해소(conflict resolution)** 와 결과적 일관성 모델 필요

**장점**:
- **Blast radius 격리**: 한 스탬프의 장애/배포 사고가 다른 스탬프 테넌트에 전파되지 않음
- **수평 확장**: 용량 한계 도달 시 스탬프를 추가(scale-out)하는 단순 모델, 단일 스탬프 비대화 회피
- **멀티테넌시 격리**: 프리미엄 테넌트 전용 스탬프(noisy neighbor 차단), 규제 요건(데이터 거주지)별 스탬프 분리 가능
- **점진적 롤아웃**: 신규 버전을 일부 스탬프에만 먼저 배포(canary stamp)
- **Geode**: 사용자 근접 리전에서 read/write → 지연 최소화 + 리전 장애 시 가용성 유지

**단점**:
- **라우팅 계층 복잡도**: 테넌트→스탬프 매핑, 재배치(rebalancing), 스탬프 이전(migration) 메커니즘 필요
- **운영 다중화**: 스탬프 수만큼 배포/모니터링/패치 자동화(IaC) 필수 — 수작업 시 폭증
- **스탬프 간 cross-stamp 쿼리 어려움**: 전체 집계/검색은 fan-out 또는 별도 집계 저장소 필요
- **Geode 충돌 해소**: 다중 마스터 write → last-write-wins / CRDT / 벡터 클록 등 충돌 전략 설계 필요, 강한 일관성 포기
- **용량 계획**: 스탬프 단위 capacity tipping point 정의 필요(언제 새 스탬프를 띄울지)

**활용 예시**:
- 대규모 SaaS 멀티테넌시 (테넌트를 스탬프에 샤딩, 엔터프라이즈 테넌트 전용 스탬프)
- 글로벌 서비스의 리전별 독립 배포 (EU/US/APAC 스탬프, GDPR 데이터 거주지 격리)
- Azure Cosmos DB(다중 리전 write = Geode 의 매니지드 구현), Azure Front Door 로 스탬프 라우팅
- Azure Architecture Center 의 Deployment Stamps / Geode 공식 패턴
- 본 프로젝트의 멀티리전 확장 시 리전별 스탬프 분리에 적용 가능

**Stamp vs 일반 샤딩의 차이**:
- 일반 샤딩: **데이터 계층만** 분할(DB 샤드). 컴퓨트는 공유
- Deployment Stamp: **풀스택 전체**(컴퓨트 + 데이터 + 캐시 + 큐) 를 단위로 복제 → 장애 격리 경계가 데이터가 아닌 스택 전체

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// 테넌트를 스탬프(scale unit)로 라우팅하는 핵심: tenant -> stamp 매핑 + 스탬프별 자족 스택
data class Stamp(
    val id: String,            // 예: "stamp-eu-01"
    val region: String,        // 데이터 거주지/지리 근접
    val baseUrl: String,       // 스탬프 자체 진입점
    val capacity: Int,         // 수용 가능 테넌트 수 (tipping point)
)

class StampRouter(private val stamps: List<Stamp>, private val registry: TenantStampRegistry) {
    // 기존 테넌트는 고정 매핑, 신규 테넌트는 여유 있는 스탬프에 배치
    fun resolve(tenantId: String): Stamp {
        registry.find(tenantId)?.let { stampId ->
            return stamps.first { it.id == stampId }   // 한번 정해진 스탬프 고정 (data locality)
        }
        val target = stamps.filter { registry.load(it.id) < it.capacity }
            .minByOrNull { registry.load(it.id) }      // least-loaded 배치
            ?: error("All stamps full — provision a new stamp")
        registry.assign(tenantId, target.id)           // 매핑 영속화
        return target
    }
}

// Geode 변형: 사용자 위치 기준 최근접 노드 선택 (모든 노드가 read/write active-active)
class GeodeRouter(private val nodes: List<Stamp>) {
    fun nearest(userRegion: String): Stamp =
        nodes.minByOrNull { geoDistance(userRegion, it.region) }
            ?: error("No geode node available")
    // write 는 최근접 노드에서 수행 후 노드 간 비동기 복제 → 충돌은 last-write-wins 등으로 수렴
}
```

**관련 패턴**: BFF, API Gateway, CQRS, Outbox

**Cross-link**:
- 리전 라우팅 / 단일 진입점: [`patterns/distributed.md#8-api-gateway`](../patterns/distributed.md#8-api-gateway)
- 다중 마스터 충돌 / 결과적 일관성: [`principles/database-fundamentals.md#acid-vs-base`](../../../data-advisor/references/principles/db-fundamentals.md#acid-vs-base)
- 스탬프 간 read model 분리: [`patterns/distributed.md#1-cqrs-command-query-responsibility-segregation`](../patterns/distributed.md#1-cqrs-command-query-responsibility-segregation)
- 데이터 샤딩 / 파티셔닝 모델링: [`patterns/data-modeling.md`](../patterns/data-modeling.md)

---

<a id="gateway-aggregation"></a>
## 14. Gateway Aggregation / Offloading / Routing (게이트웨이 집계/오프로딩/라우팅)

**목적**: API Gateway 가 클라이언트와 백엔드 사이에서 수행하는 3가지 변형 책임을 정리합니다 — 여러 백엔드 호출을 하나의 응답으로 합성(Aggregation), 인증/TLS/캐싱 등 공통 횡단 기능을 위임받아 처리(Offloading), L7 경로 기반으로 적절한 서비스에 전달(Routing). 공통 목표는 클라이언트 라운드트립 감소와 백엔드 단순화입니다.

**3 변형**:
- **Aggregation (집계)**: 한 번의 클라이언트 요청에 대해 게이트웨이가 다중 백엔드를 병렬 호출하고 결과를 하나의 응답으로 합성. 클라이언트가 N번 왕복할 일을 1번으로 축소 (chatty client 해소)
- **Offloading (오프로딩)**: 인증/인가, TLS termination, 응답 캐싱, 압축(gzip), rate limiting, 로깅 같은 공통 기능을 각 서비스에서 빼내 게이트웨이로 위임. 백엔드는 비즈니스 로직만 담당
- **Routing (라우팅)**: HTTP 경로/호스트/헤더 등 L7 정보로 요청을 적절한 다운스트림 서비스로 전달. `/users/*` → user-svc, `/orders/*` → order-svc 식의 경로 매핑

**특징**:
- 클라이언트는 단일 endpoint 만 알면 됨 (내부 토폴로지 은닉)
- Aggregation 은 fan-out/fan-in 병렬 호출이 핵심
- Offloading 은 횡단 관심사를 한 곳에 집중 (DRY)
- Routing 은 정적 매핑 + 동적 라우팅(가중치/카나리) 모두 가능

**장점**:
- 클라이언트 라운드트립 ↓ (모바일/고지연 환경에서 특히 효과)
- 백엔드 서비스는 비즈니스 로직에만 집중 (공통 기능 중복 제거)
- 인증/TLS/캐싱 정책을 중앙에서 일괄 관리
- 내부 서비스 재배치/분할 시 클라이언트 영향 없음

**단점**:
- 게이트웨이가 단일 장애점/병목 (Aggregation 시 한 백엔드 지연이 전체 응답 지연)
- Aggregation 로직 비대화 위험 (BFF 와 책임 경계 모호)
- Offloading 과다 시 게이트웨이가 "Smart Gateway" 안티패턴화
- 추가 홉으로 인한 지연 (캐싱으로 상쇄 가능)

**활용 예시**:
- Aggregation: 모바일 홈 화면 1요청 → 프로필+피드+알림 합성
- Offloading: Kong/AWS API Gateway 의 JWT 검증, TLS termination, 응답 캐싱
- Routing: Spring Cloud Gateway / Kubernetes Ingress 의 경로 기반 분기
- 본 프로젝트 클라이언트 → 서버 전면 게이트웨이의 인증/라우팅 위임

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Ktor 게이트웨이: Offloading(인증) + Routing(경로 분기) + Aggregation(병렬 합성)
fun Application.gateway(client: HttpClient) = routing {
    // 1) Offloading: 인증을 게이트웨이로 위임 (백엔드는 인증 모름)
    intercept(ApplicationCallPipeline.Plugins) {
        if (!call.request.headers.contains("Authorization")) {
            call.respond(HttpStatusCode.Unauthorized); finish()
        }
    }

    // 2) Routing: L7 경로 기반으로 다운스트림 서비스에 전달
    route("/users/{...}") {
        handle {
            val res = client.get("http://user-svc${call.request.uri.removePrefix("/users")}")
            call.respondText(res.bodyAsText(), status = res.status)
        }
    }

    // 3) Aggregation: 다중 백엔드 병렬 호출 → 단일 응답 합성
    get("/home/{userId}") {
        val id = call.parameters["userId"]!!
        val home = coroutineScope {
            val profile = async { client.get("http://user-svc/users/$id").bodyAsText() }
            val feed    = async { client.get("http://feed-svc/feed/$id").bodyAsText() }
            val notis   = async { client.get("http://noti-svc/notifications/$id").bodyAsText() }
            """{"profile":${profile.await()},"feed":${feed.await()},"notifications":${notis.await()}}"""
        }
        call.respondText(home, ContentType.Application.Json)
    }
}
```

**관련 패턴**: API Gateway, BFF, Facade, Service Mesh, Proxy

---

<a id="gatekeeper"></a>
## 15. Gatekeeper (게이트키퍼)

**목적**: 외부 요청을 전용 검증/정제(sanitization) 인스턴스가 먼저 받아 인증·유효성·악성 페이로드를 검사한 뒤 내부 신뢰 서비스로 중계(brokered access)하여, 핵심 비즈니스 서비스가 신뢰 경계 밖에 직접 노출되지 않도록 보안 격리합니다.

**특징**:
- Gatekeeper 인스턴스는 클라이언트와 동일한 DMZ/공개 영역에 배치, 핵심 서비스는 내부망에만 배치
- 검증/정제만 담당 → 민감 데이터·자격증명·비즈니스 로직을 보유하지 않음 (탈취되어도 피해 최소)
- 모든 요청은 Gatekeeper 를 거쳐야만 내부에 도달 (직접 경로 차단)
- API Gateway 가 라우팅/집계 중심이라면 Gatekeeper 는 신뢰 경계 격리 중심

**장점**:
- 공격면(attack surface) 축소 — 핵심 서비스가 공개 엔드포인트를 갖지 않음
- Gatekeeper 침해 시에도 자격증명·민감 데이터가 없어 횡적 이동 어려움
- 검증 로직 중앙화 → 모든 진입점에 일관된 입력 검사
- 핵심 서비스는 "이미 검증된 신뢰 요청" 만 처리 → 내부 로직 단순화

**단점**:
- 추가 홉 발생 → 지연(latency) 증가
- Gatekeeper 가 단일 장애점/병목이 될 수 있음 (다중화 필요)
- 검증 규칙과 내부 계약을 양쪽에서 동기화해야 함
- 과도한 검증 로직 집중 시 Gatekeeper 비대화 위험

**활용 예시**:
- DMZ 의 리버스 프록시 → 내부 결제/사용자 서비스 중계
- Azure Cloud Design Patterns 의 Gatekeeper pattern (Trusted Host 와 결합)
- WAF(Web Application Firewall) + 정제 계층을 거친 후 백엔드 도달
- 본 프로젝트의 외부 웹훅 수신 → 검증 후 내부 Server 로 전달

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// Gatekeeper: 검증/정제만 수행, 자격증명·비즈니스 로직 미보유.
// 통과한 요청만 내부 신뢰 서비스(TrustedHost)로 중계한다.
class Gatekeeper(private val trusted: TrustedHostClient) {
    fun handle(raw: RawRequest): Response {
        // 1) 인증 토큰 형식 검증 (실패 시 내부에 도달하지 못함)
        val token = raw.headers["Authorization"]
            ?: return Response(401, "missing token")
        if (!TokenFormat.isValid(token)) return Response(401, "bad token")

        // 2) 입력 정제: 크기 제한, 허용 필드 화이트리스트, 인젝션 패턴 차단
        val sanitized = runCatching { Sanitizer.clean(raw.body) }
            .getOrElse { return Response(400, "invalid payload") }

        // 3) 검증된 요청만 내부 신뢰 서비스로 중계 (brokered access)
        return trusted.forward(sanitized, token)
    }
}

// 내부 신뢰 서비스는 공개 엔드포인트가 없고, Gatekeeper 경유만 허용.
class TrustedHostClient(private val internalUrl: String, private val mtls: MtlsConfig) {
    fun forward(req: SanitizedRequest, token: String): Response =
        httpPost("$internalUrl/process", req, token, mtls) // 내부망 + mTLS
}
```

**관련 패턴**: API Gateway, Proxy, Service Mesh, BFF
