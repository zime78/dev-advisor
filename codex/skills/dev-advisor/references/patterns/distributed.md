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
