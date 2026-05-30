# 엔터프라이즈 통합 패턴 (Enterprise Integration Patterns)

서비스 간 메시지/이벤트 통합 패턴. Gregor Hohpe 의 EIP 카탈로그 기반.

---

## 1. Pipes & Filters (파이프 앤 필터)

**목적**: 처리 단계를 작은 필터로 분리하고 파이프로 연결하여 데이터 변환 흐름을 구성합니다.

**특징**:
- 각 필터는 단일 책임
- 필터 간 결합은 파이프 (큐 / 스트림)
- 순서 / 병렬화 자유로움

**장점**:
- 필터 재사용 / 재배치 용이
- 단계별 독립 확장

**단점**:
- 단계 간 데이터 직렬화 비용
- 트랜잭션 경계 관리 어려움

**활용 예시**:
- Unix shell pipeline
- ETL 파이프라인 (Airflow, Beam)
- 컴파일러 단계 (lex → parse → optimize)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.flow.*
suspend fun pipeline(src: Flow<String>) = src
    .filter { it.isNotBlank() }
    .map { it.trim().lowercase() }
    .map { Event.parse(it) }
    .collect { sink.write(it) }
```

**관련 패턴**: Chain of Responsibility, Splitter

---

## 2. Publish-Subscribe (발행-구독)

**목적**: 발행자와 구독자를 디커플링하여 이벤트를 다수의 관심 있는 수신자에게 전달합니다.

**특징**:
- 토픽 (topic) 기반 라우팅
- fan-out 자연스러움
- 발행자는 구독자를 모름

**장점**:
- 느슨한 결합으로 확장성
- 신규 구독자 추가가 비침습

**단점**:
- 메시지 순서 / 중복 처리 어려움
- 운영 가시성 (누가 듣고 있나) 저하

**활용 예시**:
- Kafka topic / NATS subject
- Redis Pub/Sub
- GUI 이벤트 버스

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class EventBus {
    private val subs = mutableMapOf<String, MutableList<(Any) -> Unit>>()
    fun subscribe(topic: String, h: (Any) -> Unit) { subs.getOrPut(topic) { mutableListOf() } += h }
    fun publish(topic: String, msg: Any) { subs[topic]?.forEach { it(msg) } }
}
```

**관련 패턴**: Observer, Message Broker

---

## 3. Message Broker (메시지 브로커)

**목적**: 메시지를 송신자/수신자 사이의 중앙 허브가 받아서 라우팅 / 변환 / 보존합니다.

**특징**:
- 큐 / 토픽 / exchange 추상화
- 영속성 / ACK / replay
- 라우팅 규칙은 브로커에 위임

**장점**:
- 송수신자 시간/위치 분리
- 트래픽 spike 흡수

**단점**:
- 단일 장애점 위험 (HA 필요)
- 메시지 운영 비용 / 모니터링

**활용 예시**:
- RabbitMQ, ActiveMQ, Kafka
- AWS SQS / SNS, GCP Pub/Sub
- NATS JetStream

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring AMQP 예시 - 브로커가 라우팅 키 기반 분배
@RabbitListener(queues = ["orders.created"])
fun onOrderCreated(msg: OrderCreated) {
    fulfillment.handle(msg)
}
// rabbitTemplate.convertAndSend("orders", "orders.created", OrderCreated(id))
```

**관련 패턴**: Publish-Subscribe, Content-Based Router

---

## 4. Aggregator (애그리게이터)

**목적**: 의미적으로 연관된 다수 메시지를 모아 하나의 결합된 메시지로 만듭니다.

**특징**:
- correlation id 로 메시지 그룹화
- 완료 조건 (count / timeout)
- 상태가 있는 (stateful) 컴포넌트

**장점**:
- 분산 응답 단일 처리
- 다운스트림 호출 횟수 감소

**단점**:
- 메모리 / 상태 관리 필요
- timeout 정책 설계 난이도

**활용 예시**:
- Scatter-Gather 응답 결합
- 주문 분할 후 재결합
- 다중 마이크로서비스 fan-in

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
class Aggregator<T>(private val expected: Int, private val onComplete: (List<T>) -> Unit) {
    private val groups = mutableMapOf<String, MutableList<T>>()
    @Synchronized fun submit(correlationId: String, item: T) {
        val list = groups.getOrPut(correlationId) { mutableListOf() }
        list += item
        if (list.size == expected) { onComplete(list); groups.remove(correlationId) }
    }
}
```

**관련 패턴**: Splitter, Scatter-Gather

---

## 5. Splitter (스플리터)

**목적**: 하나의 큰 메시지를 다수의 작은 메시지로 분해해 각각을 독립적으로 처리합니다.

**특징**:
- 원본 메시지의 항목별 분할
- correlation id 부여
- 후속 Aggregator 와 짝

**장점**:
- 항목 병렬 처리 가능
- 다운스트림 단순화

**단점**:
- 메시지 수 증가 (브로커 부하)
- 일관성 유지 책임 이동

**활용 예시**:
- 주문 → 라인 아이템 분할
- 배치 파일 → 레코드 단위
- IoT 일괄 측정 분해

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
fun splitOrder(order: Order): List<OrderLineMessage> =
    order.lines.map { line ->
        OrderLineMessage(correlationId = order.id, total = order.lines.size, line = line)
    }
```

**관련 패턴**: Aggregator, Pipes & Filters

---

## 6. Content-Based Router (콘텐츠 기반 라우터)

**목적**: 메시지 내용에 따라 적절한 채널로 메시지를 라우팅합니다.

**특징**:
- 규칙 기반 분기 (header / payload)
- 무상태 컴포넌트로 구현 가능
- 송신자는 목적지를 모름

**장점**:
- 라우팅 정책이 한 곳에 집중
- 신규 채널 추가 비침습

**단점**:
- 라우터 자체가 hotspot 가능성
- 규칙 폭증 시 유지보수 부담

**활용 예시**:
- Kafka Streams branch
- API gateway 라우팅
- 결제 수단별 처리 분기

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
fun route(msg: Payment) = when {
    msg.amount > 1_000_000 -> highValueQueue.send(msg)
    msg.currency == "KRW"  -> krwQueue.send(msg)
    else                   -> defaultQueue.send(msg)
}
```

**관련 패턴**: Message Broker, Chain of Responsibility

---

## 7. Message Translator (메시지 트랜슬레이터)

**목적**: 서로 다른 데이터 포맷 / 스키마를 사용하는 시스템 간 메시지를 변환합니다.

**특징**:
- 1:1 포맷 변환 (JSON ↔ XML, v1 ↔ v2)
- 무상태 변환 함수
- 양방향 또는 단방향

**장점**:
- 시스템 간 결합도 최소화
- 스키마 진화 흡수

**단점**:
- 누락 필드 / 의미 변경에 취약
- 변환 규칙 폭증 시 관리 부담

**활용 예시**:
- 레거시 ↔ 신규 API 변환
- ProtoBuf ↔ JSON 게이트웨이
- 멀티 버전 API 지원

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
data class LegacyUser(val u_id: String, val nm: String)
data class User(val id: String, val name: String)
fun toModern(l: LegacyUser): User = User(id = l.u_id, name = l.nm)
```

**관련 패턴**: Adapter, Pipes & Filters

---

## 8. Dead Letter Queue (DLQ)

**목적**: 반복 실패한 메시지를 별도 큐로 격리하여 메인 처리 흐름을 보호합니다.

**특징**:
- 최대 재시도 초과 시 이동
- 운영자 수동 / 재처리 도구 지원
- 원본 메시지 + 실패 메타데이터 보존

**장점**:
- 한 메시지 실패가 큐 전체를 막지 않음
- 사후 분석 / 재처리 가능

**단점**:
- DLQ 자체 모니터링 필요
- 무관심하면 무한 적재

**활용 예시**:
- RabbitMQ x-dead-letter-exchange
- SQS Redrive policy
- Kafka error topic

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
fun consume(msg: Message) {
    try { handle(msg) }
    catch (e: Exception) {
        if (msg.retries >= 5) dlq.send(msg.copy(error = e.message))
        else retryQueue.send(msg.copy(retries = msg.retries + 1))
    }
}
```

**관련 패턴**: Retry, Message Broker

---

## 9. Competing Consumers (경쟁 소비자)

**목적**: 동일 큐를 여러 소비자가 경쟁적으로 소비하여 부하를 분산하고 처리량을 늘립니다.

**특징**:
- 1 메시지 = 1 소비자
- 수평 확장이 단순 (consumer 수 증가)
- 순서 보장 불가 (필요 시 partition key 사용)

**장점**:
- 처리량 선형 확장
- 단일 소비자 장애에 강함

**단점**:
- 메시지 순서 보장 불가
- 동일 작업 동시성 충돌은 별도 처리 필요

**활용 예시**:
- SQS / RabbitMQ work queue
- Kafka consumer group
- Celery / Sidekiq worker pool

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
suspend fun runWorkers(queue: Channel<Job>, n: Int) = coroutineScope {
    repeat(n) {
        launch { for (job in queue) job.run() } // 동일 큐 경쟁 소비
    }
}
```

**관련 패턴**: Message Broker, Pipes & Filters

---

## 10. Wire Tap (와이어 탭)

**목적**: 메시지 흐름을 변경하지 않고 가로채어 별도 채널로 복사·검사합니다. 운영 중 메시지 내용 로깅·모니터링·감사에 사용합니다.

**특징**:
- 원본 메시지는 원래 채널로 그대로 흐름
- 복사본을 감사 큐·로그·모니터링 시스템으로 전달
- 투명성 (주 흐름 지연 없음) — 비동기 사이드 채널
- Spring Integration `WireTap`, Apache Camel `wireTap()`

**장점**:
- 비침습적 관찰 (핵심 흐름 수정 불필요)
- 감사 로그·디버깅·A/B 샘플링에 활용
- 컴플라이언스 요구사항 충족

**단점**:
- 민감 데이터 복사 → 보안·개인정보 정책 검토 필요
- 부하 높은 메시지 흐름에서 사이드 채널 백프레셔 주의
- 복사 지점 다수 → 관리 복잡도 증가

**활용 예시**:
- Apache Camel `wireTap("log:audit")`
- Spring Integration `WireTapChannelInterceptor`
- Kafka `MirrorMaker` (토픽 미러링)
- 결제 메시지 감사 로그

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*

/**
 * Wire Tap: 메시지를 주 채널로 전달하면서 감사 채널로도 복사
 */
fun CoroutineScope.wireTap(
    input: ReceiveChannel<String>,
    main: SendChannel<String>,
    audit: SendChannel<String>
) = launch {
    for (msg in input) {
        main.send(msg)                         // 원본 흐름 유지
        launch { audit.trySend(msg) }          // 비동기 감사 복사 (블로킹 방지)
    }
}
```

**관련 패턴**: Pipes & Filters, Message Broker, DLQ

---

## 11. Claim Check (클레임 체크)

**목적**: 대용량 메시지 payload 를 외부 저장소에 저장하고, 메시지 버스에는 참조 키만 전달하여 채널 과부하를 방지합니다.

**특징**:
- Check-In: payload → 외부 스토어(S3, DB, Redis) 저장 후 claim key 발급
- Check-Out: 수신측이 key 로 원본 payload 조회
- 메시지 크기 = 키 크기로 고정 (수 바이트)
- 저장소 TTL 로 자동 정리 가능

**장점**:
- 메시지 버스 대역폭·메모리 절감
- 대용량 바이너리(이미지, PDF) 전달 가능
- 저장소 분리 → 메시지와 payload 수명 주기 독립

**단점**:
- 수신측이 추가 저장소 조회 필요 → 레이턴시 증가
- 저장소 가용성이 메시지 처리 가용성에 영향
- 참조 키 분실 시 payload 고아화

**활용 예시**:
- S3 + SQS/SNS 대용량 이벤트
- Azure Service Bus + Blob Storage
- Kafka + MinIO (대용량 바이너리)
- 이메일 첨부파일 → 오브젝트 스토리지 패턴

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import java.util.UUID

/** Claim Check 패턴: check-in / check-out */
interface PayloadStore {
    fun save(payload: ByteArray): String   // claim key 반환
    fun load(key: String): ByteArray
}

data class Message(val claimKey: String, val metadata: Map<String, String>)

class ClaimCheckRouter(private val store: PayloadStore) {
    /** Check-In: 대용량 payload → 저장소 보관, 키만 메시지에 포함 */
    fun checkIn(payload: ByteArray, metadata: Map<String, String>): Message {
        val key = store.save(payload)
        return Message(claimKey = key, metadata = metadata)
    }

    /** Check-Out: 수신측이 claim key 로 원본 payload 복원 */
    fun checkOut(msg: Message): ByteArray = store.load(msg.claimKey)
}

// 인메모리 구현 (테스트용)
class InMemoryPayloadStore : PayloadStore {
    private val store = mutableMapOf<String, ByteArray>()
    override fun save(payload: ByteArray): String =
        UUID.randomUUID().toString().also { store[it] = payload }
    override fun load(key: String): ByteArray =
        store[key] ?: error("Claim key not found: $key")
}
```

**관련 패턴**: Message Translator, Aggregator, Pipes & Filters

---

## 12. Resequencer (리시퀀서)

**목적**: 네트워크·병렬 처리로 뒤섞인 메시지를 원래 순서로 재정렬하여 하류로 전달합니다.

**특징**:
- 각 메시지에 sequence number (또는 timestamp) 포함
- 버퍼에 메시지 축적 후 기대 번호가 도착하면 순서대로 방출
- 타임아웃: 특정 번호가 오지 않으면 갭 처리 (skip 또는 DLQ)
- Kafka 파티션 내 순서 보장 + 파티션 간 재정렬에 활용

**장점**:
- 병렬 처리 후 순서 복원 가능
- Splitter → 병렬 처리 → Resequencer 파이프라인 구성

**단점**:
- 버퍼 메모리 사용 (늦게 오는 메시지 대기)
- 누락 메시지 처리 정책 필요 (타임아웃, 갭 허용)
- 분산 환경에서 시퀀스 번호 글로벌 단조 증가 보장 어려움

**활용 예시**:
- TCP 패킷 재조립
- Apache Camel `resequence()`
- 금융 거래 시퀀스 복원
- 이벤트 소싱 이벤트 순서 정렬

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import java.util.TreeMap

/** 시퀀스 번호 기반 Resequencer */
class Resequencer(private val onOrdered: (String) -> Unit) {
    private val buffer = TreeMap<Int, String>()  // seq → payload
    private var nextExpected = 0

    /** 메시지 수신 — 순서가 맞으면 즉시 방출, 아니면 버퍼 */
    @Synchronized
    fun receive(seq: Int, payload: String) {
        buffer[seq] = payload
        // 연속된 번호가 도착할 때까지 방출
        while (buffer.containsKey(nextExpected)) {
            onOrdered(buffer.remove(nextExpected)!!)
            nextExpected++
        }
    }

    /** 타임아웃 후 갭 강제 스킵 (누락 메시지 처리) */
    @Synchronized
    fun flushGap() {
        if (buffer.isNotEmpty() && buffer.firstKey() > nextExpected) {
            nextExpected = buffer.firstKey()   // 갭 건너뜀
        }
    }
}
```

**관련 패턴**: Splitter, Aggregator, Scatter-Gather

---

## 13. Scatter-Gather (스캐터-개더)

**목적**: 요청을 여러 수신자에게 병렬 분기(Scatter)하고, 모든 응답을 수집·집계(Gather)하여 최종 결과를 반환합니다.

**특징**:
- Scatter: 동일 요청을 N개 채널/서비스로 동시 전송
- Gather (Aggregator): N개 응답을 수집, 완료 조건 충족 시 집계
- 완료 조건: 전체 응답, 최초 N개, 타임아웃 중 선택
- 가격 비교·검색 결과 병합에 흔히 사용

**장점**:
- 병렬 처리로 레이턴시 = max(각 응답 시간) — 순차 합산 대비 빠름
- 일부 응답 실패 허용 가능 (partial result)

**단점**:
- 모든 응답 대기 시 가장 느린 서비스가 병목
- 응답 집계 로직 복잡 (중복 제거, 순위, 합산)
- 타임아웃 정책 설계 필요

**활용 예시**:
- 가격 비교 사이트 (여러 공급사 동시 조회)
- 검색 결과 federated 집계
- Apache Camel `recipientList()` + Aggregator
- BFF 패턴에서 여러 마이크로서비스 병렬 호출

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*

data class PriceQuote(val vendor: String, val price: Double)

/** Scatter-Gather: 여러 공급사에 병렬 가격 조회 후 최저가 반환 */
suspend fun scatterGatherLowestPrice(
    vendors: List<String>,
    queryFn: suspend (String) -> PriceQuote,
    timeoutMs: Long = 2000L
): PriceQuote? = coroutineScope {
    val deferred = vendors.map { vendor ->
        async {
            withTimeoutOrNull(timeoutMs) { queryFn(vendor) }  // 타임아웃 허용
        }
    }
    // Gather: 전체 응답 수집 후 최저가 선택
    deferred.awaitAll()
        .filterNotNull()
        .minByOrNull { it.price }
}

// 사용 예
suspend fun main() {
    val result = scatterGatherLowestPrice(
        vendors = listOf("vendorA", "vendorB", "vendorC"),
        queryFn = { vendor -> PriceQuote(vendor, (10..100).random().toDouble()) }
    )
    println("Best price: $result")
}
```

**관련 패턴**: Aggregator, Splitter, Resequencer, Competing Consumers

---

## 14. Process Manager (프로세스 매니저)

**목적**: 장기 실행 메시지 흐름을 중앙에서 오케스트레이션합니다. 상태를 유지하며 다음 처리 단계를 결정합니다.

**특징**:
- 중앙 조율자(orchestrator): 현재 단계·상태 보관
- 각 단계 완료 메시지를 수신 → 다음 단계 메시지 발송
- Saga 패턴과 유사하나 Process Manager 는 EIP 용어 (단일 프로세스 흐름 관리)
- Saga vs Process Manager: Saga = 보상 트랜잭션 강조, PM = 일반 흐름 제어

**장점**:
- 복잡한 다단계 흐름을 단일 지점에서 추적
- 흐름 상태 영속화 → 재시작·재개 가능
- 병렬·조건부 단계 표현 가능

**단점**:
- 중앙 조율자 = 단일 장애점 가능성
- 상태 저장소 필요 (DB, Redis)
- Saga 보상 로직과 중복될 수 있음

**활용 예시**:
- 주문 처리 흐름 (결제 → 재고 → 배송 → 완료)
- Apache Camel `saga()` component
- Temporal.io Workflow
- AWS Step Functions
- MassTransit Saga StateMachine

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
/** 주문 프로세스 매니저 — 상태 머신 기반 */
enum class OrderState { PENDING, PAYMENT_SENT, INVENTORY_RESERVED, SHIPPED, COMPLETED, FAILED }

data class OrderProcess(val orderId: String, var state: OrderState = OrderState.PENDING)

class OrderProcessManager(private val store: MutableMap<String, OrderProcess> = mutableMapOf()) {

    fun start(orderId: String): String {
        val process = OrderProcess(orderId)
        store[orderId] = process
        sendPaymentRequest(orderId)    // 첫 단계 트리거
        return orderId
    }

    fun onPaymentConfirmed(orderId: String) {
        val p = store[orderId] ?: return
        p.state = OrderState.PAYMENT_SENT
        sendInventoryReserve(orderId) // 다음 단계 트리거
    }

    fun onInventoryReserved(orderId: String) {
        val p = store[orderId] ?: return
        p.state = OrderState.INVENTORY_RESERVED
        sendShipment(orderId)
    }

    fun onShipped(orderId: String) {
        val p = store[orderId] ?: return
        p.state = OrderState.SHIPPED
        p.state = OrderState.COMPLETED  // 완료
    }

    fun onFailure(orderId: String, reason: String) {
        val p = store[orderId] ?: return
        p.state = OrderState.FAILED
        sendCompensation(orderId, reason)  // 보상 트랜잭션
    }

    private fun sendPaymentRequest(id: String) { /* 메시지 발송 */ }
    private fun sendInventoryReserve(id: String) { /* 메시지 발송 */ }
    private fun sendShipment(id: String) { /* 메시지 발송 */ }
    private fun sendCompensation(id: String, reason: String) { /* 보상 */ }
}
```

**관련 패턴**: Aggregator, Scatter-Gather, DLQ, Competing Consumers

---

## 15. Normalizer (노멀라이저)

**목적**: 서로 다른 포맷의 메시지를 단일 Canonical Data Model(표준 모델)로 변환하여 하류 처리를 단순화합니다.

**특징**:
- 입력: 포맷 A, B, C … (JSON, XML, CSV, EDI 등)
- 각 포맷별 변환기 + Content-Based Router 조합
- 출력: 단일 표준 포맷 → 동일 처리 파이프라인 진입
- Message Translator 의 복수 소스 버전

**장점**:
- 하류 처리 로직 단순화 (포맷 분기 제거)
- 새 소스 추가 시 변환기만 추가 (OCP)
- 이기종 시스템 통합 허브에 적합

**단점**:
- 표준 모델 설계가 핵심 — 잘못 설계 시 모든 변환기 수정 필요
- 변환 손실 가능 (소스 포맷에만 있는 필드 누락)
- 변환 유지보수 비용

**활용 예시**:
- EDI → 내부 주문 모델
- 다중 결제 게이트웨이 응답 통합
- Apache Camel `marshal() / unmarshal()`
- 이기종 IoT 센서 데이터 통합

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
/** Canonical 주문 모델 */
data class CanonicalOrder(val id: String, val amount: Double, val currency: String)

/** 포맷별 변환기 인터페이스 */
fun interface OrderTranslator<T> {
    fun translate(source: T): CanonicalOrder
}

/** Normalizer: Content-Based Router + 변환기 조합 */
class OrderNormalizer {
    private val translators = mutableMapOf<String, OrderTranslator<Any>>()

    @Suppress("UNCHECKED_CAST")
    fun <T : Any> register(format: String, translator: OrderTranslator<T>) {
        translators[format] = translator as OrderTranslator<Any>
    }

    fun normalize(format: String, raw: Any): CanonicalOrder {
        val translator = translators[format]
            ?: error("No translator for format: $format")
        return translator.translate(raw)
    }
}

// 등록 예시
fun buildNormalizer(): OrderNormalizer {
    val n = OrderNormalizer()
    // JSON 소스
    n.register<Map<String, Any>>("json") { src ->
        CanonicalOrder(src["order_id"] as String, (src["total"] as Number).toDouble(), src["ccy"] as String)
    }
    // CSV 소스 (단순 split)
    n.register<String>("csv") { src ->
        val parts = src.split(",")
        CanonicalOrder(parts[0], parts[1].toDouble(), parts[2])
    }
    return n
}
```

**관련 패턴**: Message Translator, Content-Based Router, Pipes & Filters

---

## 16. Routing Slip (라우팅 슬립)

**목적**: 메시지 자체에 처리 단계 목록(슬립)을 기록하여, 각 단계가 다음 목적지를 동적으로 결정합니다. 중앙 라우터 없이 분산 라우팅을 구현합니다.

**특징**:
- 메시지 헤더/메타데이터에 처리 단계 큐 포함
- 각 컴포넌트는 슬립에서 자신의 다음 목적지를 읽고 전달
- 슬립 내용은 런타임에 동적 결정 가능
- Process Manager 와 반대: 분산(메시지 보유) vs 중앙집중(PM 보유)

**장점**:
- 중앙 조율자 불필요 → 단일 장애점 제거
- 메시지별 독립 라우팅 경로 (유연성↑)
- 동적 흐름 변경 용이

**단점**:
- 슬립 위변조 가능 → 입력 검증 필요
- 전체 흐름 가시성 저하 (분산 추적 필요)
- 슬립 길이 제한 (메시지 크기 증가)

**활용 예시**:
- Apache Camel `routingSlip()`
- 문서 승인 흐름 (부서별 동적 결재선)
- 보험 청구 처리 (규칙 기반 동적 단계)
- 이메일 필터링 파이프라인

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
/** Routing Slip 메시지 */
data class SlipMessage(
    val payload: String,
    val slip: ArrayDeque<String>,      // 처리 단계 큐 (FIFO)
    val metadata: MutableMap<String, String> = mutableMapOf()
)

/** 각 처리 단계 컴포넌트 인터페이스 */
fun interface SlipProcessor {
    fun process(msg: SlipMessage): SlipMessage
}

/** Routing Slip 라우터: 슬립에서 다음 단계를 꺼내 디스패치 */
class RoutingSlipRouter(private val processors: Map<String, SlipProcessor>) {
    fun route(msg: SlipMessage): SlipMessage {
        var current = msg
        while (current.slip.isNotEmpty()) {
            val step = current.slip.removeFirst()
            val processor = processors[step]
                ?: error("Unknown processor: $step")
            current = processor.process(current)
        }
        return current
    }
}

// 사용 예
fun main() {
    val router = RoutingSlipRouter(
        mapOf(
            "validate"  to SlipProcessor { msg -> msg.also { it.metadata["validated"] = "true" } },
            "enrich"    to SlipProcessor { msg -> msg.copy(payload = "[enriched] ${msg.payload}") },
            "transform" to SlipProcessor { msg -> msg.copy(payload = msg.payload.uppercase()) }
        )
    )

    val msg = SlipMessage(
        payload = "order-123",
        slip = ArrayDeque(listOf("validate", "enrich", "transform"))
    )
    val result = router.route(msg)
    println(result.payload)           // [ENRICHED] ORDER-123
    println(result.metadata)          // {validated=true}
}
```

**관련 패턴**: Content-Based Router, Process Manager, Pipes & Filters

**관련 패턴**: Producer-Consumer, Message Broker

---

<a id="message-broker-selection-matrix"></a>
## 17. Message Broker Selection Matrix (메시지 브로커 선택 매트릭스)

**목적**: 메시지/이벤트 기반 아키텍처에서 5종 대표 브로커(Kafka / RabbitMQ / NATS / Pulsar / Redis Streams)를 12 차원으로 비교하여 워크로드 특성에 맞는 선택 기준을 제공합니다.

**언제 사용하는가**:
- 신규 서비스의 메시지 백본 선정 단계
- 단일 브로커로 처리량/지연/내구성을 동시에 만족하지 못해 전환을 검토할 때
- Polyglot 메시징 (브로커 혼용) 전략 수립 시

**난이도**: 중간 | **사용 빈도**: ★★★★★

### 17.1 브로커 개요

#### Apache Kafka
**핵심 모델**: 분산 영구 로그(Distributed Commit Log) + Partitioned Topic + Consumer Group.

**특징**:
- 메시지를 토픽-파티션의 append-only 로그에 영구 저장 (retention 정책 단위: 시간/크기/compaction)
- Consumer 가 offset 을 직접 관리 (replay 가능)
- Idempotent Producer + Transactional Producer 로 exactly-once 지원 (Kafka Streams 한정)
- ZooKeeper / KRaft 메타데이터 관리

**강점**: 초고처리량(수백만 msg/sec), 영구 보관, 스트림 재생, Geo-replication (MirrorMaker 2).
**약점**: 운영 복잡도 높음, 단건 RPC 부적합, 토픽 수 폭증 시 메타데이터 부하.

#### RabbitMQ
**핵심 모델**: AMQP 0.9.1 기반 Broker. Exchange → Binding → Queue 경로로 라우팅.

**Exchange 타입**:
- `direct` — Routing Key 완전 일치
- `topic` — Routing Key 와일드카드 (`order.*.created`)
- `fanout` — 모든 바인딩 큐로 브로드캐스트
- `headers` — 헤더 매칭 (Routing Key 무시)

**기능**: DLX (Dead Letter Exchange), TTL, Priority Queue, Lazy Queue, Publisher Confirms, Quorum Queue (Raft 기반 복제).
**강점**: 유연한 라우팅, 낮은 진입장벽, 트랜잭션·확인 응답.
**약점**: 영구 로그 미지원 (소비 후 삭제), 단일 큐 처리량 한계, 클러스터 split-brain 위험 (classic mirroring).

#### NATS (with JetStream)
**핵심 모델**: 경량 Subject 기반 Pub/Sub + 선택적 JetStream(영구 스트림 + Consumer + KV/Object Store).

**Subject 와일드카드**:
- `*` — 한 토큰 매칭 (`orders.*.created`)
- `>` — 다중 토큰 매칭 (`orders.>`)

**특징**: 단일 바이너리 (Go), 마이크로초 단위 지연, NATS Core 는 fire-and-forget, JetStream 으로 at-least-once / exactly-once (per-message) 보장.
**강점**: 초저지연, 운영 단순성, Edge / IoT 친화, Leaf Node 토폴로지.
**약점**: 생태계 Kafka 대비 좁음, JetStream 영속성 옵션 학습 필요.

#### Apache Pulsar
**핵심 모델**: Compute(Broker)와 Storage(BookKeeper) 분리 + 멀티테넌시(Tenant / Namespace / Topic).

**특징**:
- Geo-replication 네이티브 (토픽 단위)
- Tiered Storage (오래된 세그먼트를 S3/GCS 로 오프로드)
- Pulsar Functions (Lightweight Stream Processing)
- 구독 모드: Exclusive / Shared / Failover / Key_Shared

**강점**: 수평 확장(브로커 stateless), 멀티 DC, 토픽 수 수백만 지원.
**약점**: BookKeeper 운영 추가, 한국어 자료 부족, 학습 곡선.

#### Redis Streams
**핵심 모델**: Redis 5.0+ 의 append-only 자료구조. `XADD` / `XREAD` / `XGROUP` / `XACK`.

**특징**: Consumer Group + Pending Entries List (PEL) 로 at-least-once, 메모리 기반(AOF/RDB 영속화 옵션), `MAXLEN ~` 으로 길이 제한.
**강점**: 기존 Redis 인프라 재사용, 초저지연, 단순 API.
**약점**: 메모리 비용, 수평 확장 한계 (Cluster 모드에서도 단일 키 shard), 대용량 retention 부적합.

### 17.2 비교 매트릭스 (12 차원)

| 차원 | Kafka | RabbitMQ | NATS (JetStream) | Pulsar | Redis Streams |
|------|-------|----------|------------------|--------|---------------|
| 전달 보장 | At-least-once / Exactly-once (txn) | At-most/least-once + Confirms | At-most(Core) / At-least/Exactly(JS, per-msg) | At-least-once / Exactly-once (txn) | At-least-once |
| 순서 보장 | 파티션 내 FIFO | 큐 내 FIFO (Consumer 1) | Stream 내 FIFO | Key_Shared 키 내 FIFO | Stream 내 FIFO |
| 영속성 vs 메모리 | 디스크 영구 (retention) | 디스크/메모리 혼합 | 메모리 / JS 디스크 | BookKeeper + Tiered S3 | 메모리 + AOF |
| 처리량 (msg/sec) | 1M+ (파티션 다수) | 50K~100K/큐 | 1M+ (Core), 200K+ (JS) | 1M+ | 100K~1M |
| 지연 (latency) | 5~50ms | 1~10ms | < 1ms (Core), 1~5ms (JS) | 5~20ms | < 1ms |
| 파티셔닝 | Topic Partition (Hash) | Sharded Plugin / Consistent Hash | JetStream Stream Partition | Partitioned Topic | Cluster Slot (수동) |
| 컨슈머 모델 | Pull (Long-poll) | Push (Prefetch) | Push / Pull (JS) | Push / Pull | Pull (Blocking XREAD) |
| 운영 복잡도 | 높음 (KRaft/ZK, 파티션 관리) | 중간 (Erlang, Quorum Queue) | 낮음 (단일 바이너리) | 매우 높음 (Broker+BookKeeper+ZK) | 낮음 (기존 Redis) |
| 라이선스 | Apache 2.0 | MPL 2.0 | Apache 2.0 | Apache 2.0 | RSALv2 / SSPLv1 (7.4+) |
| 백프레셔 | Consumer Lag + Pause/Resume | Prefetch QoS + Flow Control | JS MaxAckPending + Pull Batch | Receiver Queue Size | XREADGROUP COUNT |
| 트랜잭션 | Producer Txn (멀티 파티션) | Channel Txn (성능 저하) | JS Atomic Publish | Producer/Consumer Txn | MULTI/EXEC (제한적) |
| 사용 시나리오 | 이벤트 소싱, 로그 파이프라인, CDC, Stream Processing | RPC, Work Queue, 라우팅 복잡 워크플로 | 마이크로서비스 메시징, IoT/Edge, Request-Reply | 멀티 테넌시 SaaS, Geo-replication, 장기 보관 | 작업 큐, 실시간 알림, 캐시 동반 |

### 17.3 선택 가이드 (시나리오 기반)

**이벤트 소싱 / CDC / Replay 필요**: Kafka 또는 Pulsar.
- 단일 리전 → Kafka. 멀티 리전 + 장기 보관 → Pulsar (Tiered Storage).

**복잡한 라우팅 (Topic Exchange, DLQ, Priority)**: RabbitMQ.
- 메시지 양 < 100K/sec, 비즈니스 워크플로 중심.

**마이크로서비스 Request-Reply / 초저지연**: NATS Core.
- 영속성 필요 시 JetStream 으로 부분 전환.

**기존 Redis 인프라 활용 + 단순 작업 큐**: Redis Streams.
- 메모리 비용 감내 가능 + retention 수 시간 이내.

**멀티 테넌시 SaaS + 토픽 수 폭증**: Pulsar.
- Namespace 단위 격리, 토픽당 메타데이터 비용 낮음.

### 17.4 안티패턴

- **Kafka 로 RPC 구현**: 응답 토픽 + correlationId 패턴은 가능하나 지연·운영 부담 크다 → NATS Request-Reply 권장.
- **RabbitMQ 로 이벤트 로그**: 소비 후 삭제 모델이라 replay 불가. Stream Queue (3.9+) 가 있으나 Kafka 대비 미성숙.
- **NATS Core 로 결제/주문 영구 이벤트**: at-most-once → JetStream 필수.
- **Redis Streams 로 대용량 장기 보관**: 메모리 폭증 → Kafka/Pulsar 로 마이그레이션.
- **Pulsar 를 단일 노드 PoC 로 운영 판단**: BookKeeper 운영 부담은 클러스터에서 비로소 나타남.

### 17.5 운영 체크리스트

- [ ] **백프레셔** 전략 정의 (Consumer Lag 임계, Prefetch, MaxAckPending)
- [ ] **DLQ / Retry** 정책 (재시도 횟수, 백오프, Poison Message 격리)
- [ ] **모니터링 지표**: Consumer Lag (Kafka), Queue Depth (RabbitMQ), Pending Count (NATS JS), Backlog (Pulsar), XLEN (Redis)
- [ ] **순서 의존성** 분석 → 파티션 키 설계
- [ ] **멱등성** (Producer/Consumer 양쪽) — exactly-once 의 본질은 중복 전송 + 중복 처리 무효화
- [ ] **스키마 진화** (Schema Registry, Protobuf/Avro)
- [ ] **재해 복구** (Geo-replication / MirrorMaker / 백업 정책)

**관련 패턴**: Message Broker, Event-Driven Architecture, Pub/Sub, Competing Consumers, Dead Letter Channel
**Cross-link**: [patterns/distributed.md](./distributed.md), [patterns/reactive-streams.md](./reactive-streams.md), [algorithms/consensus.md](../algorithms/consensus.md), [patterns/streaming-semantics.md](./streaming-semantics.md)

---

<a id="messaging-gateway"></a>
## 18. Messaging Gateway / Service Activator (메시징 게이트웨이 / 서비스 액티베이터)

**목적**: Messaging Gateway 는 메시징 시스템 호출(채널·메시지 생성·전송·응답 대기)을 도메인 친화적 API 뒤로 캡슐화하여, 애플리케이션 코드가 메시징 API 를 직접 다루지 않게 합니다. Service Activator 는 큐/토픽에 도착한 메시지를 받아 기존 동기 서비스(POJO/빈) 호출로 연결하여, 서비스가 메시징 인프라를 모른 채 메시지 흐름에 참여하게 합니다.

**특징**:
- Messaging Gateway: 메시징 API → 도메인 인터페이스로 은닉 (호출자는 메서드 호출로 인지)
- 동기 게이트웨이(Request-Reply, correlation id 로 응답 매칭) / 비동기 게이트웨이(fire-and-forget, `CompletableFuture` 반환) 양쪽 지원
- Service Activator: Polling Consumer(주기 pull) 또는 Event-Driven Consumer(브로커 push) 로 메시지 수신 후 서비스 메서드에 매핑
- 도착-한-번-처리 보장이 필요하면 Idempotent Receiver(메시지 id 중복 제거)와 결합
- Spring Integration `@MessagingGateway` / `@ServiceActivator`, Apache Camel `bean()` / `to("bean:...")`

**장점**:
- 도메인 코드와 메시징 인프라 분리 → 테스트 용이(인터페이스 mock), 브로커 교체 흡수
- 기존 동기 서비스를 수정 없이 메시지 엔드포인트로 재사용(Service Activator)
- 동기/비동기 호출 방식을 게이트웨이 시그니처로 선언적 표현

**단점**:
- 게이트웨이 추상화가 동기 Request-Reply 의 지연·타임아웃·장애를 숨겨 오해 유발 가능
- 응답 상관(correlation)·타임아웃·재시도 정책을 게이트웨이가 떠안아 복잡도 이동
- Event-Driven Consumer 는 at-least-once → 중복 처리 가능, Idempotent Receiver 없으면 부작용 중복

**활용 예시**:
- Spring Integration `@MessagingGateway` (인터페이스 → 채널 송신)
- `@ServiceActivator(inputChannel = "orders")` 로 메시지 → 빈 메서드 연결
- Apache Camel `from("jms:queue:orders").bean(OrderService.class, "handle")`
- 외부 결제 요청을 동기 게이트웨이로 보내고 응답 대기

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CompletableFuture

data class Message(val correlationId: String, val payload: Any, val replyTo: String? = null)

/** 도메인 친화 API — 호출자는 메시징 API 를 전혀 모름 */
interface OrderGateway {
    /** 동기 Request-Reply: correlation id 로 응답 매칭 후 결과 반환 */
    fun placeOrder(order: Any): CompletableFuture<Any>
}

/** Messaging Gateway 구현 — 메시지 생성·전송·응답 상관을 캡슐화 */
class MessagingOrderGateway(private val out: (Message) -> Unit) : OrderGateway {
    private val pending = ConcurrentHashMap<String, CompletableFuture<Any>>()

    override fun placeOrder(order: Any): CompletableFuture<Any> {
        val id = UUID.randomUUID().toString()
        val future = CompletableFuture<Any>()
        pending[id] = future
        out(Message(correlationId = id, payload = order, replyTo = "orders.reply")) // 채널 전송
        return future
    }

    /** 응답 채널 콜백 — correlation id 로 대기 중 future 완료 */
    fun onReply(reply: Message) { pending.remove(reply.correlationId)?.complete(reply.payload) }
}

/** Service Activator — 메시지를 기존 동기 서비스 호출로 연결 (서비스는 메시징을 모름) */
class OrderServiceActivator(
    private val service: (Any) -> Any,            // 기존 도메인 서비스 메서드
    private val seen: MutableSet<String> = ConcurrentHashMap.newKeySet(), // Idempotent Receiver
    private val reply: (Message) -> Unit
) {
    /** Event-Driven Consumer 진입점 — 브로커 push 시 호출 */
    fun onMessage(msg: Message) {
        if (!seen.add(msg.correlationId)) return   // 중복 메시지 멱등 무시
        val result = service(msg.payload)          // 서비스 메서드 활성화
        msg.replyTo?.let { reply(Message(msg.correlationId, result)) }
    }
}
```

**관련 패턴**: Message Broker, Message Translator, Competing Consumers, Dead Letter Queue (DLQ)
