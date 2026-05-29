# 동시성 패턴 (Concurrency Patterns)

멀티스레드/멀티프로세스 환경에서 안전한 자원 공유 및 효율적 작업 분배 패턴. POSA, Schmidt 의 분류 기반.

---

## 1. Active Object (액티브 오브젝트)

**목적**: 메서드 호출과 실행을 분리하여, 호출은 큐에 적재하고 별도 워커 스레드가 실행하도록 합니다.

**특징**:
- 메서드 요청을 메시지로 변환
- Scheduler + Activation Queue + Servant 구성
- 호출자와 실행 컨텍스트 분리

**장점**:
- 동기화 코드가 호출 측에서 사라짐
- 호출 비동기화로 응답성 향상

**단점**:
- 큐 운영 오버헤드
- 디버깅 난이도 (콜 스택 단절)

**활용 예시**:
- Actor 시스템 (Akka)
- GUI 이벤트 디스패치
- 마이크로서비스 message handler

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
class Counter(scope: CoroutineScope) {
    private val mailbox = Channel<suspend (IntArray) -> Unit>(Channel.UNLIMITED)
    private val state = intArrayOf(0)
    init { scope.launch { for (msg in mailbox) msg(state) } }
    suspend fun inc() = mailbox.send { it[0]++ }
    suspend fun get(): Int { var v = 0; mailbox.send { v = it[0] }; return v }
}
```

**관련 패턴**: Producer-Consumer, Thread Pool

---

## 2. Monitor Object (모니터 오브젝트)

**목적**: 객체의 메서드를 한 번에 하나의 스레드만 실행하도록 캡슐화된 락으로 보호합니다.

**특징**:
- 객체 내부에 mutex + condition variable 내장
- synchronized / Lock 추상화
- wait / notify 로 협력적 대기

**장점**:
- 락 관리가 객체 내부에 숨겨짐
- 클라이언트 코드 단순화

**단점**:
- 객체 단위 락으로 동시성 한계
- 데드락 위험 (락 순서)

**활용 예시**:
- Java synchronized 객체
- BlockingQueue 구현
- 임베디드 / RTOS mutex 객체

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class BoundedBuffer<T>(private val capacity: Int) {
    private val items = ArrayDeque<T>()
    @Synchronized fun put(x: T) {
        while (items.size == capacity) (this as Object).wait()
        items.addLast(x); (this as Object).notifyAll()
    }
    @Synchronized fun take(): T {
        while (items.isEmpty()) (this as Object).wait()
        return items.removeFirst().also { (this as Object).notifyAll() }
    }
}
```

**관련 패턴**: Active Object, Read-Write Lock

---

## 3. Thread Pool (스레드 풀)

**목적**: 작업 큐와 고정된 수의 워커 스레드를 둬서 생성/소멸 비용 없이 작업을 분산 실행합니다.

**특징**:
- 워커 수 고정 또는 동적
- 작업 큐 (bounded / unbounded)
- 거부 정책 (abort / discard / caller-runs)

**장점**:
- 스레드 생성 비용 절감
- 동시성 상한으로 자원 보호

**단점**:
- 큐 폭증 시 메모리 누수
- 블로킹 작업 혼합 시 풀 고갈

**활용 예시**:
- `java.util.concurrent.ExecutorService`
- Tomcat / Netty worker pool
- Kotlin `Dispatchers.IO`

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import java.util.concurrent.Executors
val pool = Executors.newFixedThreadPool(8)
fun submitJob(job: Runnable) = pool.submit(job)
// 종료 시 pool.shutdown() + awaitTermination
```

**관련 패턴**: Producer-Consumer, Active Object

---

## 4. Producer-Consumer (생산자-소비자)

**목적**: 생산자와 소비자를 큐로 분리하여 처리 속도 차이를 흡수하고 결합도를 낮춥니다.

**특징**:
- 공유 buffer / queue
- bounded buffer 가 백프레셔 역할
- N : M 관계 자연스럽게 지원

**장점**:
- 생산/소비 속도 디커플링
- 수평 확장 용이

**단점**:
- 큐 크기/정책 튜닝 필요
- 데드락 / 기아 위험

**활용 예시**:
- 로그 수집 파이프라인
- 작업 큐 (Celery, Sidekiq)
- Kafka producer/consumer

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
suspend fun pipeline() = coroutineScope {
    val q = Channel<Int>(capacity = 32)
    launch { for (i in 1..100) q.send(i); q.close() }      // producer
    repeat(4) { launch { for (x in q) println(x * x) } }   // 4 consumers
}
```

**관련 패턴**: Thread Pool, Backpressure

---

## 5. Reactor (리액터)

**목적**: 단일 이벤트 루프가 다수 I/O 핸들의 readiness 를 감시하고 적절한 핸들러로 동기 디스패치합니다.

**특징**:
- `select` / `epoll` / `kqueue` 기반
- 단일 스레드 이벤트 루프
- 핸들러는 짧고 non-blocking

**장점**:
- 다수 연결을 적은 스레드로 처리
- 락 없음 → 단순한 동시성 모델

**단점**:
- 블로킹 핸들러 하나가 전체 정지
- CPU bound 작업에 부적합

**활용 예시**:
- Node.js, Netty, Nginx
- Redis 단일 스레드 루프
- Vert.x

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import java.nio.channels.*
val selector = Selector.open()
serverChannel.configureBlocking(false).register(selector, SelectionKey.OP_ACCEPT)
while (true) {
    selector.select()
    for (key in selector.selectedKeys()) {
        if (key.isAcceptable) accept(key)
        if (key.isReadable) read(key)
    }
    selector.selectedKeys().clear()
}
```

**관련 패턴**: Proactor, Producer-Consumer

---

## 6. Proactor (프로액터)

**목적**: 비동기 I/O 시작 후 OS 가 완료를 알려주면 등록된 완료 핸들러를 실행합니다.

**특징**:
- 완료 기반 (completion based)
- OS 가 I/O 를 대신 수행 (IOCP, io_uring)
- 핸들러는 데이터가 준비된 후 호출

**장점**:
- 진정한 비동기 I/O (커널이 작업 완료)
- 매우 높은 처리량

**단점**:
- OS 의존성 / 이식성 낮음
- 디버깅 어려움

**활용 예시**:
- Windows IOCP
- Linux io_uring
- Boost.Asio (Proactor 모드)

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
import java.nio.channels.AsynchronousSocketChannel
import java.nio.ByteBuffer
val ch = AsynchronousSocketChannel.open()
val buf = ByteBuffer.allocate(1024)
ch.read(buf, null, object : java.nio.channels.CompletionHandler<Int, Any?> {
    override fun completed(n: Int, a: Any?) { /* 데이터 사용 */ }
    override fun failed(e: Throwable, a: Any?) { /* 오류 처리 */ }
})
```

**관련 패턴**: Reactor, Future/Promise

---

## 7. Read-Write Lock (읽기-쓰기 락)

**목적**: 다수의 동시 읽기는 허용하고 쓰기는 배타적으로 수행하여 read-heavy 워크로드 처리량을 높입니다.

**특징**:
- 공유 (read) / 배타 (write) 두 모드
- 쓰기 우선 / 읽기 우선 정책
- StampedLock 의 optimistic read 지원

**장점**:
- 읽기 동시성 극대화
- 일반 mutex 대비 처리량 향상

**단점**:
- 쓰기 기아 (writer starvation) 위험
- 락 자체 오버헤드 큼

**활용 예시**:
- 인메모리 캐시
- 설정 / 라우팅 테이블
- 통계 수집기

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import java.util.concurrent.locks.ReentrantReadWriteLock
class Cache<K, V> {
    private val map = HashMap<K, V>()
    private val lock = ReentrantReadWriteLock()
    fun get(k: K): V? = lock.readLock().run { lock(); try { map[k] } finally { unlock() } }
    fun put(k: K, v: V) = lock.writeLock().run { lock(); try { map[k] = v } finally { unlock() } }
}
```

**관련 패턴**: Monitor Object

---

## 8. Double-Checked Locking (이중 검사 잠금)

**목적**: 락 비용 없이 지연 초기화를 안전하게 수행합니다.

**특징**:
- 첫 검사 (no lock) → 락 → 재검사 → 초기화
- `volatile` 필수 (가시성 / reordering 방지)
- 잘못 구현하면 부분 초기화 객체 노출

**장점**:
- 핫 패스에서 락 회피
- 지연 초기화 비용 최소화

**단점**:
- 메모리 모델 이해 부족 시 버그
- Kotlin / Java 에선 더 안전한 idiom (LazyInit) 권장

**활용 예시**:
- 클래식 Singleton 지연 초기화
- 무거운 클라이언트 객체 캐싱
- DI 컨테이너 내부

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
class HeavyService private constructor() {
    companion object {
        @Volatile private var instance: HeavyService? = null
        fun get(): HeavyService = instance ?: synchronized(this) {
            instance ?: HeavyService().also { instance = it }
        }
    }
}
// 또는 Kotlin idiom: by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { HeavyService() }
```

**관련 패턴**: Singleton, Monitor Object

---

## 9. Future / Promise (퓨처 / 프라미스)

**목적**: 비동기 작업의 결과를 placeholder 로 표현하여 호출/완료를 분리합니다.

**특징**:
- Future: 읽기 측 (소비자)
- Promise: 쓰기 측 (생산자)
- 조합 (then / map / flatMap / await)

**장점**:
- 콜백 지옥 회피
- 비동기 조합 (병렬 / 직렬) 표현 용이

**단점**:
- 예외 전파 모델 학습 필요
- 잘못 사용 시 데드락 / 누수

**활용 예시**:
- `CompletableFuture` / `Deferred`
- JS `Promise` / `async-await`
- gRPC `ListenableFuture`

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
suspend fun fetchAll(ids: List<String>): List<User> = coroutineScope {
    ids.map { id -> async { fetchUser(id) } }.awaitAll()
}
```

**관련 패턴**: Active Object, Reactor

---

## 10. Actor Model (액터 모델)

**목적**: 각 Actor가 독립 상태 + 메시지 박스를 가져 공유 메모리 없이 메시지 패싱만으로 동시성을 표현합니다.

**특징**:
- Actor = 상태 + 행동 + 메일박스 (큐)
- 메시지는 비동기 전송, Actor 는 순차 처리 (내부 직렬화)
- Actor 계층: Supervisor 가 자식 Actor 장애를 감독 (let it crash 철학)
- 주소(ActorRef)로만 참조 — 직접 메모리 공유 없음

**장점**:
- 공유 가변 상태 제거 → 데이터 레이스 원천 차단
- 장애 격리 / 자가 복구 (Supervisor Strategy)
- 분산 시스템으로 자연스럽게 확장 (Akka Cluster, Erlang OTP)

**단점**:
- 메시지 직렬화 오버헤드
- 순서 보장 복잡 (같은 발신자-수신자 쌍 내에서만 보장)
- 디버깅 어려움 (비동기 메시지 추적)

**활용 예시**:
- Erlang/Elixir OTP GenServer
- Akka (JVM) / Akka.NET
- Microsoft Orleans (Virtual Actor)
- Kotlin `kotlinx-actor` (Channel 기반)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.actor

/** 카운터 Actor — 메시지 패싱으로 상태 보호 */
sealed class CounterMsg
data object Increment : CounterMsg()
data class GetValue(val reply: CompletableDeferred<Int>) : CounterMsg()

@OptIn(ObsoleteCoroutinesApi::class)
fun CoroutineScope.counterActor() = actor<CounterMsg> {
    var count = 0                          // 내부 상태 — 외부 접근 불가
    for (msg in channel) {
        when (msg) {
            is Increment -> count++
            is GetValue  -> msg.reply.complete(count)
        }
    }
}

suspend fun main() = coroutineScope {
    val counter = counterActor()
    repeat(1000) { counter.send(Increment) }  // 동시 전송 — 레이스 없음
    val reply = CompletableDeferred<Int>()
    counter.send(GetValue(reply))
    println("Count: ${reply.await()}")         // 1000
    counter.close()
}
```

**관련 패턴**: Active Object, CSP, Future/Promise

---

## 11. CSP (Communicating Sequential Processes)

**목적**: 독립 프로세스가 채널을 통해 통신하여 동시성을 구성합니다. Hoare 1978, Go 언어의 설계 철학 기반.

**특징**:
- 프로세스는 독립 실행, 공유 메모리 없음
- 채널: 동기(unbuffered) 또는 비동기(buffered)
- 동기 채널: 송신자·수신자 동시 준비 시 랑데뷰 (rendezvous)
- select 문: 여러 채널 중 준비된 것 처리

**장점**:
- "메모리 공유로 통신하지 말고, 통신으로 메모리를 공유하라" (Go 격언)
- 데드락 정적 분석 가능 (CSP 모델 체킹)
- 파이프라인·팬아웃·팬인 패턴 표현 간결

**단점**:
- 채널 오용 시 고루틴 누수 / 데드락
- 순서 보장 복잡 (여러 채널 select 시)
- Actor 대비 분산 확장 어려움

**활용 예시**:
- Go goroutine + channel
- Kotlin `kotlinx.coroutines.channels`
- Clojure `core.async`
- occam 언어 (CSP 원 구현)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*

/** 파이프라인: 생산 → 제곱 → 출력 */
fun CoroutineScope.produce(n: Int): ReceiveChannel<Int> = produce {
    repeat(n) { send(it) }
}

fun CoroutineScope.square(input: ReceiveChannel<Int>): ReceiveChannel<Int> = produce {
    for (x in input) send(x * x)
}

suspend fun main() = coroutineScope {
    val numbers = produce(5)
    val squares = square(numbers)
    for (v in squares) println(v)  // 0 1 4 9 16
    coroutineContext.cancelChildren()
}
```

**관련 패턴**: Actor Model, Producer-Consumer, Reactor

---

## 12. STM (Software Transactional Memory)

**목적**: 공유 메모리 접근을 데이터베이스 트랜잭션처럼 원자적(ACID)으로 처리하여 락 없이 동시성을 안전하게 관리합니다.

**특징**:
- 트랜잭션 블록 내 읽기·쓰기를 낙관적으로 실행
- 커밋 시 충돌 감지 → 충돌 시 자동 재시도 (retry)
- 중첩 트랜잭션 가능 (composable)
- Haskell STM (TVar), Clojure Ref + dosync, Scala STM

**장점**:
- 락 없이 구성 가능한 동시성 (lock-free composability)
- 데드락 불가 (낙관적 재시도)
- 트랜잭션 조합 시 의미론 유지

**단점**:
- 쓰기 충돌 많은 워크로드에서 재시도 폭발
- I/O 를 트랜잭션 내에서 수행 불가 (부작용 금지)
- JVM STM 구현은 GC 압박 (버전 관리 객체)

**활용 예시**:
- Haskell `Control.Concurrent.STM` (TVar, TChan)
- Clojure `ref` + `dosync`
- Scala STM (`scala-stm`)
- Intel TSX (하드웨어 지원 HTM)

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
// Kotlin 표준에는 STM 미포함 — 개념 의사코드
// 실제 사용: Clojure dosync / Haskell atomically / Multiverse(Java)

/**
 * STM 트랜잭션 의사코드
 * atomically { } 블록 내 TVar 읽기·쓰기는 원자적
 */
/*
val balance = TVar(1000)
val savings = TVar(500)

// 계좌 이체 — 락 없이 원자적
atomically {
    val b = balance.read()
    val s = savings.read()
    if (b >= 200) {
        balance.write(b - 200)
        savings.write(s + 200)
    } else {
        retry()   // 잔액 부족 시 재시도 대기
    }
}
*/

// Clojure 등가 코드:
// (dosync
//   (when (>= @balance 200)
//     (alter balance - 200)
//     (alter savings + 200)))
```

**관련 패턴**: Monitor Object, Read-Write Lock, Actor Model

---

## 13. Fork-Join (포크-조인)

**목적**: 작업을 재귀적으로 분할(Fork)하고 결과를 합산(Join)하는 분할 정복 병렬 패턴. Work-stealing 스케줄러로 효율을 높입니다.

**특징**:
- 임계 크기 이하 → 순차 처리, 초과 → 2분할 Fork
- Work-stealing: 유휴 스레드가 바쁜 스레드의 큐에서 작업 탈취
- Java `ForkJoinPool` / `RecursiveTask<T>` / `RecursiveAction`
- Kotlin `coroutineScope { async { } }` 로 동일 패턴 표현 가능

**장점**:
- CPU 코어 포화율 극대화 (work-stealing)
- 재귀 분할 코드가 직관적
- 공유 상태 없이 결과 합산

**단점**:
- 태스크 분할 오버헤드 (너무 작은 크기로 분할 시 역효과)
- 순서 의존 알고리즘 적용 어려움
- 스택 깊이 제한 (깊은 재귀)

**활용 예시**:
- Java `ForkJoinPool.commonPool()` (parallel streams 기반)
- Kotlin `Dispatchers.Default` + coroutineScope
- Scala `parallel collections`
- MapReduce (분산 Fork-Join)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*

/** Fork-Join 병렬 합계 — 임계값 이하 순차, 초과 분할 */
suspend fun parallelSum(arr: LongArray, from: Int, to: Int, threshold: Int = 1000): Long {
    if (to - from <= threshold) {
        return (from until to).sumOf { arr[it] }   // 순차 처리
    }
    val mid = (from + to) / 2
    return coroutineScope {
        val left  = async { parallelSum(arr, from, mid, threshold) }  // Fork
        val right = async { parallelSum(arr, mid,  to,  threshold) }  // Fork
        left.await() + right.await()                                   // Join
    }
}

suspend fun main() {
    val data = LongArray(1_000_000) { it.toLong() }
    val sum = parallelSum(data, 0, data.size)
    println("Sum: $sum")  // 499999500000
}
```

**관련 패턴**: Thread Pool, Future/Promise, Producer-Consumer

---

## 14. Structured Concurrency (구조적 동시성)

**목적**: 비동기 작업의 생명주기를 호출 스코프에 묶어 누수·고아 작업·예외 전파를 구조적으로 보장합니다.

**특징**:
- 스코프: 자식 코루틴 모두 완료 전 부모 스코프 종료 불가
- 오류 전파: 자식 실패 → 같은 스코프의 다른 자식 취소 → 부모로 전파
- Kotlin `coroutineScope` / `supervisorScope`, Java Project Loom `StructuredTaskScope`
- Python `trio` nursery, Swift `async let` / `withTaskGroup`

**장점**:
- 고루틴/코루틴 누수 원천 차단 (스코프 탈출 불가)
- 취소·타임아웃이 전체 서브트리에 자동 전파
- 예외 처리 선형화 (콜백 지옥·누락된 await 방지)

**단점**:
- 병렬 독립 작업이 스코프 밖으로 탈출해야 할 때 설계 변경 필요
- 기존 스레드 기반 코드 마이그레이션 비용
- supervisorScope 오용 시 오류 무시 위험

**활용 예시**:
- Kotlin `coroutineScope { }` + `async/launch`
- Java 21+ `StructuredTaskScope.ShutdownOnFailure`
- Python `trio` nursery
- Swift `withTaskGroup`

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*

/** 구조적 동시성 — 모든 자식 완료 보장, 하나 실패 시 전체 취소 */
suspend fun fetchUserDashboard(userId: String): Dashboard {
    return coroutineScope {                          // 구조적 스코프
        val profile  = async { fetchProfile(userId) }   // 자식 1
        val timeline = async { fetchTimeline(userId) }  // 자식 2
        val notifs   = async { fetchNotifications(userId) } // 자식 3

        // 셋 중 하나라도 예외 → 나머지 자동 취소 → 예외 부모로 전파
        Dashboard(
            profile  = profile.await(),
            timeline = timeline.await(),
            notifs   = notifs.await()
        )
    }   // 스코프 종료 = 모든 자식 완료 보장
}

/** supervisorScope: 자식 실패가 다른 자식에 영향 안 줌 */
suspend fun fetchWithFallback(userId: String): Dashboard = supervisorScope {
    val profile  = async { fetchProfile(userId) }
    val timeline = async { runCatching { fetchTimeline(userId) }.getOrDefault(emptyList()) }
    Dashboard(profile = profile.await(), timeline = timeline.await(), notifs = emptyList())
}

data class Dashboard(val profile: Any, val timeline: Any, val notifs: Any)
suspend fun fetchProfile(id: String): Any = "profile-$id"
suspend fun fetchTimeline(id: String): Any = listOf<Any>()
suspend fun fetchNotifications(id: String): Any = listOf<Any>()
```

**관련 패턴**: Future/Promise, Fork-Join, Actor Model

**관련 패턴**: Active Object, Proactor
