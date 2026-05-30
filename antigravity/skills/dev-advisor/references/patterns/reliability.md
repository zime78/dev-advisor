# 신뢰성 패턴 (Reliability Patterns)

장애 격리, 재시도, 회복력 (resilience) 을 위한 패턴. 마이크로서비스/분산 시스템에서 필수.

---

## 1. Circuit Breaker (서킷 브레이커)

**목적**: 실패가 임계치를 초과하면 즉시 fast-fail 하여 장애 전파와 자원 고갈을 차단합니다.

**특징**:
- 세 상태(Closed / Open / Half-Open) 머신
- 실패 카운터와 타임아웃으로 자가 회복 시도
- 호출 측 응답 시간 보장

**장점**:
- 다운스트림 장애가 상위로 전파되는 것을 차단
- 빠른 실패로 스레드/커넥션 낭비 방지

**단점**:
- 임계치/타임아웃 튜닝 난이도
- Half-Open 상태에서의 thundering herd 위험

**활용 예시**:
- 외부 API 호출 보호 (Resilience4j, Hystrix)
- DB / 캐시 장애 격리
- gRPC client interceptor

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class CircuitBreaker(private val threshold: Int, private val resetMs: Long) {
    private var failures = 0
    private var openedAt = 0L
    fun <T> call(block: () -> T): T {
        if (failures >= threshold && System.currentTimeMillis() - openedAt < resetMs)
            throw IllegalStateException("circuit open")
        return runCatching(block)
            .onSuccess { failures = 0 }
            .onFailure { failures++; openedAt = System.currentTimeMillis() }
            .getOrThrow()
    }
}
```

**관련 패턴**: Retry, Timeout, Bulkhead

---

## 2. Retry (재시도)

**목적**: 일시적 (transient) 실패를 자동 재시도하여 사용자에게 노출되는 오류 빈도를 줄입니다.

**특징**:
- 지수 백오프 (exponential backoff) + jitter 권장
- 멱등성이 보장된 작업에만 적용
- 최대 시도 횟수 / 총 deadline 상한

**장점**:
- 일시적 네트워크/락 충돌 자동 복구
- 사용자 체감 안정성 향상

**단점**:
- 멱등성이 없는 호출에 적용 시 중복 실행
- 잘못된 retry 가 장애를 증폭 (retry storm)

**활용 예시**:
- HTTP 5xx / 네트워크 timeout
- 메시지 큐 consume 실패
- 분산 락 획득

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
suspend fun <T> retry(times: Int, initialDelay: Long = 100, factor: Double = 2.0, block: suspend () -> T): T {
    var delay = initialDelay
    repeat(times - 1) {
        runCatching { return block() }
        kotlinx.coroutines.delay(delay + (0..delay.toInt()).random())
        delay = (delay * factor).toLong()
    }
    return block()
}
```

**관련 패턴**: Circuit Breaker, Timeout, Backpressure

---

## 3. Bulkhead (벌크헤드)

**목적**: 자원 풀을 영역별로 격리하여 한 영역의 장애가 전체로 전파되지 않게 합니다.

**특징**:
- 선박 격벽에서 유래
- 스레드풀 / 커넥션풀 / 세마포어 단위 분리
- 영역별 동시성 상한 부여

**장점**:
- 한 다운스트림 장애가 전체 워커를 점거하지 않음
- SLO 가 다른 트래픽을 분리 가능

**단점**:
- 풀 분할로 평균 활용률 감소
- 풀 크기 산정 난이도

**활용 예시**:
- 결제 API 와 추천 API 의 스레드풀 분리
- DB connection pool partitioning
- Resilience4j Bulkhead

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class Bulkhead(maxConcurrent: Int) {
    private val sem = java.util.concurrent.Semaphore(maxConcurrent)
    fun <T> call(block: () -> T): T {
        if (!sem.tryAcquire()) throw IllegalStateException("bulkhead full")
        try { return block() } finally { sem.release() }
    }
}
```

**관련 패턴**: Circuit Breaker, Rate Limiter

---

## 4. Timeout (타임아웃)

**목적**: 응답 대기 시간에 상한을 둬서 무한 대기로 인한 자원 고갈을 방지합니다.

**특징**:
- 모든 외부 호출의 기본 안전망
- connect / read / total 단위로 다층 설정
- 상위 deadline 을 하위로 propagate

**장점**:
- 워커/커넥션의 영구 점유 방지
- 장애 감지 시간 단축

**단점**:
- 너무 짧으면 정상 호출까지 실패
- deadline 전파가 누락되면 효과 반감

**활용 예시**:
- HTTP client read timeout
- DB statement timeout
- gRPC deadline

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.withTimeout
suspend fun fetchUser(id: String): User =
    withTimeout(2_000) { // ms
        httpClient.get("/users/$id")
    }
```

**관련 패턴**: Circuit Breaker, Retry

---

## 5. Rate Limiter (레이트 리미터)

**목적**: 단위 시간당 호출 빈도를 제한하여 다운스트림 과부하와 비용 폭주를 차단합니다.

**특징**:
- Token Bucket / Leaky Bucket 알고리즘
- 글로벌 (분산 Redis) vs 로컬 (in-process)
- 거부 (reject) vs 대기 (throttle) 정책

**장점**:
- 외부 API 쿼터 위반 방지
- DoS / 의도치 않은 폭주 차단

**단점**:
- 분산 환경에서 정확도/성능 트레이드오프
- 버스트 허용량 튜닝 필요

**활용 예시**:
- 공개 API gateway
- LLM API 호출 비용 통제
- 로그인 무차별 대입 방어

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class TokenBucket(private val capacity: Int, private val refillPerSec: Int) {
    private var tokens = capacity.toDouble()
    private var lastRefill = System.nanoTime()
    @Synchronized fun tryAcquire(): Boolean {
        val now = System.nanoTime()
        tokens = minOf(capacity.toDouble(), tokens + (now - lastRefill) / 1e9 * refillPerSec)
        lastRefill = now
        return if (tokens >= 1) { tokens -= 1; true } else false
    }
}
```

**관련 패턴**: Backpressure, Bulkhead

---

## 6. Backpressure (백프레셔)

**목적**: 소비자의 처리 능력에 맞춰 생산자의 속도를 조절하여 큐 폭증을 방지합니다.

**특징**:
- pull 기반 vs push + credit 기반
- 버퍼 상한 + drop / block / spill 정책
- Reactive Streams 의 핵심 개념

**장점**:
- 메모리 폭주 / OOM 방지
- 시스템 전체 안정성 향상

**단점**:
- 종단간 신호 전파 설계 필요
- drop 정책 선택 시 데이터 손실 가능

**활용 예시**:
- Reactive Streams (Project Reactor, RxJava)
- Kotlin Flow buffer / conflate
- Kafka consumer lag 제어

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.flow.*
fun upstream(): Flow<Int> = flow { repeat(1_000_000) { emit(it) } }
suspend fun consume() = upstream()
    .buffer(capacity = 64) // 소비자 느리면 producer suspend
    .collect { slowProcess(it) }
```

**관련 패턴**: Rate Limiter, Producer-Consumer

---

## 7. Health Check (헬스 체크)

**목적**: liveness / readiness 신호를 노출하여 오케스트레이터가 트래픽 라우팅과 재시작을 결정하게 합니다.

**특징**:
- liveness (살아있는가) vs readiness (요청 받을 준비)
- shallow check (자기 자신) vs deep check (의존성)
- 응답 시간 상한 필수

**장점**:
- 자동 복구 (재시작 / 트래픽 제거)
- 무중단 배포 지원

**단점**:
- deep check 가 cascading failure 유발
- 잘못된 임계치로 false positive 발생

**활용 예시**:
- Kubernetes liveness/readiness probe
- AWS ELB target health
- Spring Boot Actuator `/actuator/health`

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
data class HealthStatus(val ok: Boolean, val checks: Map<String, Boolean>)
class HealthService(private val db: () -> Boolean, private val cache: () -> Boolean) {
    fun readiness(): HealthStatus {
        val c = mapOf("db" to runCatching(db).getOrDefault(false),
                      "cache" to runCatching(cache).getOrDefault(false))
        return HealthStatus(c.values.all { it }, c)
    }
}
```

**관련 패턴**: Sidecar, Circuit Breaker

---

## 8. Sidecar (사이드카)

**목적**: 주 컨테이너 옆에 보조 컨테이너를 붙여서 cross-cutting 기능(proxy, logging, observability)을 분리합니다.

**특징**:
- 동일 Pod / 동일 호스트 공유
- 언어 / 런타임 독립
- 주 애플리케이션 비침습

**장점**:
- polyglot 환경에서 공통 기능 일관 적용
- 주 앱 코드 변경 없이 기능 추가

**단점**:
- 리소스 오버헤드
- 배포 단위 복잡성 증가

**활용 예시**:
- Service Mesh (Envoy in Istio / Linkerd)
- Fluent Bit 로그 수집
- Vault agent secret 주입

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// 메인 앱은 localhost:15000 의 사이드카 proxy 만 호출.
// 사이드카가 mTLS, 재시도, 메트릭, 트레이싱을 담당.
fun callBilling(req: Request): Response =
    httpClient.post("http://127.0.0.1:15000/billing", req) // 외부 라우팅은 sidecar 가 처리
```

**관련 패턴**: Ambassador, Adapter

---

## 9. Ambassador (앰배서더)

**목적**: 외부 시스템 통신을 out-of-process proxy 로 위임하여 클라이언트 로직을 단순화합니다.

**특징**:
- 클라이언트 측 sidecar 특수형
- 재시도/회로차단/암호화/디스커버리 위임
- 애플리케이션은 로컬 endpoint 만 인식

**장점**:
- 다양한 언어 클라이언트의 정책 일관성
- 인프라 변경을 ambassador 만 갱신

**단점**:
- 추가 네트워크 hop (지연 증가)
- 운영 복잡도 상승

**활용 예시**:
- Envoy / linkerd2-proxy
- Redis / DB 인증 위임 proxy
- 인증 토큰 자동 주입 sidecar

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// 앱은 도메인/포트 몰라도 localhost ambassador 에만 보냄.
class RemoteCacheClient(private val ambassador: String = "http://127.0.0.1:6380") {
    fun get(key: String): String? = httpClient.get("$ambassador/get/$key")
}
```

**관련 패턴**: Sidecar, Proxy, Adapter

---

<a id="steady-state-fail-fast"></a>
## 10. Steady State / Fail Fast (정상 상태 유지 / 빠른 실패)

**목적**: 시스템이 사람 개입 없이 장시간 안정적으로 동작하도록 자원 누적을 막고(Steady State), 처리 불가한 요청은 자원을 잡기 전에 즉시 거부(Fail Fast)하여 안정성을 확보합니다. Michael Nygard 의 *Release It!* 안정성 패턴.

**특징**:
- Steady State: 자원 누수 방지, 오래된 데이터 정리(purging), 로그 순환(log rotation)으로 무한 증가 차단
- Fail Fast: 요청 시작 시점에 의존성/자원/파라미터를 미리 검증해 실패를 앞당김
- 자원을 점유한 뒤 뒤늦게 실패하는 "slow fail" 을 피해 점유 시간 최소화
- "사람이 만지면 시스템이 불안정해진다" 전제 — 자동 정리로 야간 운영 부하 제거

**장점**:
- 메모리/디스크/커넥션의 단조 증가로 인한 점진적 장애(crash, OOM, disk full) 예방
- Fail Fast 로 스레드/커넥션을 오래 잡지 않아 부하 시 자원 고갈 회피
- 빠른 거부 응답이 호출 측의 무의미한 대기를 줄여 cascading failure 완화

**단점**:
- purge/rotation 임계치(보존 기간, 배치 크기)를 잘못 잡으면 과삭제 또는 누적
- Fail Fast 의 사전 검증 로직이 본 로직과 중복/누락될 수 있음
- 일시적 의존성 장애에도 즉시 거부하면 Retry 와 충돌 — 책임 경계 설계 필요

**활용 예시**:
- 세션/캐시 만료 데이터 주기적 배치 삭제, 로그/임시파일 rotation 및 보존정책
- 요청 진입 시 커넥션풀 여유·circuit 상태·필수 파라미터 선검증 후 빠른 거부
- Resilience4j Bulkhead 가득참 / 큐 한계 초과 시 즉시 reject (Load Shedding 과 결합)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Steady State: 만료 데이터 주기적 purge + 로그 보존정책
class SteadyStateMaintainer(private val retentionDays: Long = 7) {
    fun purgeExpired(now: Instant) {
        db.execute("DELETE FROM session WHERE created_at < ?", now.minus(retentionDays, ChronoUnit.DAYS))
        logDir.rotateAndDeleteOlderThan(retentionDays) // 로그 순환
    }
}

// Fail Fast: 자원을 잡기 전에 선검증 → 즉시 거부 (slow fail 회피)
class OrderService(private val pool: ConnectionPool, private val breaker: CircuitBreaker) {
    fun place(req: OrderRequest): Result<Order> {
        require(req.items.isNotEmpty()) { "empty order" }     // 파라미터 선검증
        if (breaker.isOpen()) return Result.failure(Rejected("downstream open")) // 빠른 실패
        if (!pool.hasIdle()) return Result.failure(Rejected("pool exhausted"))    // 자원 점유 전 거부
        return pool.borrow().use { conn -> Result.success(conn.insert(req)) }
    }
}
```

**관련 패턴**: Circuit Breaker, Bulkhead, Timeout
