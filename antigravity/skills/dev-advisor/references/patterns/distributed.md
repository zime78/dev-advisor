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
