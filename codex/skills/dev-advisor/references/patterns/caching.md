# 캐싱 패턴 (Caching Patterns)

데이터 접근 비용(DB 쿼리, 외부 API 호출, 복잡한 연산)을 줄이기 위해 결과를 임시 저장소에 보관·재사용하는 패턴 모음. 인-프로세스(Caffeine), 분산(Redis), 다계층(L1+L2) 조합으로 구현된다.

---

## 1. Cache-Aside (Lazy Load)

**목적**: 애플리케이션이 직접 캐시를 조회하고, 미스(miss) 시 원본 저장소에서 읽어 캐시에 채우는 가장 범용적인 패턴입니다.

**특징**:
- 읽기 흐름: 캐시 조회 → miss면 DB 조회 → 캐시에 저장 → 반환
- 쓰기 흐름: DB 직접 쓰기 → 캐시 무효화(invalidate) 또는 갱신
- 캐시와 DB의 일관성 책임이 애플리케이션 코드에 있음
- Redis + Caffeine 모두 적용 가능한 가장 보편적 패턴
- Cache miss storm(Stampede) 방지를 위해 별도 전략 필요

**장점**:
- 실제로 읽히는 데이터만 캐시에 적재 (lazy population)
- 캐시 장애 시 DB로 자동 폴백 — 서비스 연속성 보장
- 읽기 패턴에 매우 유연

**단점**:
- 최초 요청은 항상 cache miss → DB 부하
- 캐시 무효화 타이밍에 따라 stale data 노출 가능
- 코드에 캐시 로직이 산재하여 추상화가 없으면 중복 증가

**활용 예시**:
- 사용자 프로파일 조회 API
- 상품 상세 페이지
- 권한·역할(RBAC) 캐싱
- Caffeine `getIfPresent` + DB fallback 조합

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import com.github.benmanes.caffeine.cache.Caffeine
import java.util.concurrent.TimeUnit

data class Product(val id: Long, val name: String, val priceKrw: Long)

class ProductRepository {
    fun findById(id: Long): Product? {
        println("[DB] 상품 $id 조회")
        return Product(id, "상품-$id", 10_000L)  // 실제로는 DB 쿼리
    }
}

class ProductService(private val repo: ProductRepository) {
    // Caffeine 인-프로세스 캐시 (최대 1000개, TTL 5분)
    private val cache = Caffeine.newBuilder()
        .maximumSize(1_000)
        .expireAfterWrite(5, TimeUnit.MINUTES)
        .build<Long, Product>()

    /** Cache-Aside: 캐시 먼저 조회, miss 시 DB에서 로드 후 캐시 저장 */
    fun getProduct(id: Long): Product? {
        return cache.getIfPresent(id) ?: repo.findById(id)?.also { cache.put(id, it) }
    }

    /** 쓰기 후 캐시 무효화 */
    fun updateProduct(product: Product) {
        // repo.save(product)  -- 실제 DB 저장
        cache.invalidate(product.id)
        println("[Cache] 상품 ${product.id} 무효화")
    }
}

fun main() {
    val svc = ProductService(ProductRepository())
    println(svc.getProduct(1))  // DB 조회
    println(svc.getProduct(1))  // 캐시 히트 (DB 미조회)
}
```

**관련 패턴**: Read-Through, Cache Stampede 방지, Negative Caching

---

## 2. Read-Through

**목적**: 캐시 라이브러리/미들웨어가 cache miss 시 자동으로 DB를 조회하여 캐시를 채우므로, 애플리케이션은 항상 캐시만 호출합니다.

**특징**:
- 애플리케이션은 캐시 인터페이스만 호출 → 로딩 로직이 캐시 계층에 캡슐화
- Caffeine `CacheLoader`, Spring `@Cacheable`(with loader), Redis + Spring Cache Abstraction
- Cache-Aside와 달리 애플리케이션 코드에 miss 처리 로직 없음
- 데이터 소스(DB)를 추상화한 `CacheLoader`를 주입하는 형태
- 쓰기는 별도 전략(Write-Through 또는 Invalidation) 필요

**장점**:
- 캐시 로직이 애플리케이션 코드에서 제거 → 코드 단순화
- 캐시 미스 처리가 일관됨 (라이브러리가 관리)
- Cache-Aside의 N+1 패턴(중복 miss 로직) 방지

**단점**:
- 최초 요청 지연은 Cache-Aside와 동일
- CacheLoader 교체 시 캐시 라이브러리 의존성 강화
- 세밀한 miss 제어(TTL 분기, partial miss 등)가 어려움

**활용 예시**:
- Caffeine `LoadingCache` (CacheLoader 주입)
- Spring `@Cacheable` + CacheManager
- JPA Second-Level Cache (Ehcache/Infinispan 연동)
- Redis + Spring Cache Abstraction

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import com.github.benmanes.caffeine.cache.Caffeine
import com.github.benmanes.caffeine.cache.CacheLoader
import java.util.concurrent.TimeUnit

class UserLoader : CacheLoader<Long, String> {
    /** CacheLoader: cache miss 시 자동 호출 — 애플리케이션은 이 로직을 직접 호출하지 않음 */
    override fun load(userId: Long): String {
        println("[DB] 사용자 $userId 로드")
        return "User-$userId"  // 실제로는 DB 쿼리
    }
}

fun main() {
    // LoadingCache: get() 호출 시 miss면 CacheLoader가 자동으로 DB 조회
    val cache = Caffeine.newBuilder()
        .maximumSize(500)
        .expireAfterWrite(10, TimeUnit.MINUTES)
        .build(UserLoader())

    println(cache.get(1L))  // DB 조회 후 캐시 저장
    println(cache.get(1L))  // 캐시 히트
    println(cache.get(2L))  // DB 조회 후 캐시 저장

    // 일괄 조회 — getAll은 누락된 키만 CacheLoader.loadAll 호출
    val users = cache.getAll(listOf(1L, 2L, 3L))
    println(users)
}
```

**관련 패턴**: Cache-Aside, Write-Through, Refresh-Ahead

---

## 3. Write-Through

**목적**: 쓰기 시 캐시와 DB를 동시에 갱신하여 캐시와 DB의 강한 일관성을 보장합니다.

**특징**:
- 모든 쓰기가 캐시를 통과(through)하여 DB에 기록
- 캐시와 DB가 항상 동기화 → stale data 없음
- 읽기는 항상 캐시에서 히트 (Write-Through는 읽기 패턴과 결합)
- 쓰기 지연(latency)은 DB 쓰기만큼 증가 (동기 DB 반영)
- Write-Behind와 대비: Write-Through는 동기, Write-Behind는 비동기

**장점**:
- 캐시 일관성 보장 (stale read 없음)
- 읽기 성능 극대화 (항상 캐시 히트)
- 장애 복구 후 캐시 워밍 불필요

**단점**:
- 쓰기 지연 증가 (DB 쓰기 대기)
- 한 번도 읽히지 않는 데이터도 캐시에 적재 → 캐시 오염
- 캐시 장애 시 쓰기 경로 전체 차단 가능

**활용 예시**:
- 세션 저장소 (Redis Session)
- 실시간 랭킹·카운터 (Redis INCR + DB sync)
- 금융 잔액 업데이트
- Spring Cache `@CachePut`

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import redis.clients.jedis.Jedis

class BalanceRepository(private val jedis: Jedis) {
    private val dbStore = mutableMapOf<String, Long>()  // 실제로는 DB

    /** Write-Through: 캐시와 DB를 동시에 갱신 */
    fun updateBalance(userId: String, amount: Long) {
        // 1. DB 먼저 쓰기 (또는 트랜잭션 내에서 캐시·DB 동시)
        dbStore[userId] = amount
        println("[DB] $userId 잔액 $amount 저장")

        // 2. 캐시 즉시 갱신
        jedis.setex("balance:$userId", 3600, amount.toString())
        println("[Cache] $userId 잔액 캐시 갱신")
    }

    /** 읽기는 항상 캐시 히트 (Write-Through로 캐시가 항상 최신) */
    fun getBalance(userId: String): Long {
        return jedis.get("balance:$userId")?.toLong()
            ?: dbStore[userId]?.also { jedis.setex("balance:$userId", 3600, it.toString()) }
            ?: 0L
    }
}
```

**관련 패턴**: Write-Behind, Cache-Aside, Read-Through

---

## 4. Write-Behind (Write-Back)

**목적**: 쓰기를 캐시에만 즉시 반영하고 DB 기록은 비동기로 지연 처리하여 쓰기 처리량을 극대화합니다.

**특징**:
- 쓰기: 캐시만 즉시 갱신 → 큐에 적재 → 백그라운드 배치로 DB 반영
- Write-Through 대비 쓰기 지연(latency)이 극히 낮음
- 짧은 시간에 같은 키에 대한 여러 쓰기가 일어나면 마지막 값만 DB에 기록 (write coalescing)
- Redis의 AOF(Append Only File)와 유사한 원리
- 데이터 유실 위험: 캐시 장애 시 큐의 미반영 데이터 손실

**장점**:
- 쓰기 처리량 극대화 (DB I/O 배치 처리)
- 동일 키 반복 쓰기 시 DB 부하 감소 (coalescing)
- 사용자 체감 응답속도 개선

**단점**:
- 캐시 장애 시 미반영 데이터 유실 위험
- 구현 복잡도 높음 (큐 관리, 재시도, 순서 보장)
- 금융·주문처럼 강한 일관성이 필요한 도메인에 부적합

**활용 예시**:
- 게임 점수·플레이 통계 업데이트
- 페이지뷰·클릭 카운터 집계
- IoT 센서 데이터 버퍼링
- Redis + 배치 DB flush

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ConcurrentLinkedQueue

class WriteBehindCache<K, V>(
    private val flushIntervalMs: Long = 5_000,
    private val dbWrite: suspend (K, V) -> Unit,
    private val scope: CoroutineScope = CoroutineScope(Dispatchers.IO),
) {
    private val cache = ConcurrentHashMap<K, V>()
    private val dirtyKeys = ConcurrentLinkedQueue<K>()

    init {
        // 주기적으로 dirty 키를 DB에 비동기 flush
        scope.launch {
            while (isActive) {
                delay(flushIntervalMs)
                flush()
            }
        }
    }

    /** 쓰기: 캐시만 즉시 갱신, DB는 나중에 */
    fun put(key: K, value: V) {
        cache[key] = value
        dirtyKeys.offer(key)
        println("[Cache] $key 캐시 즉시 저장 (DB 지연)")
    }

    fun get(key: K): V? = cache[key]

    private suspend fun flush() {
        val keys = mutableSetOf<K>()
        while (dirtyKeys.isNotEmpty()) keys += dirtyKeys.poll() ?: break
        for (key in keys) {
            cache[key]?.let { value ->
                dbWrite(key, value)
                println("[DB] $key flush 완료")
            }
        }
    }
}
```

**관련 패턴**: Write-Through, Cache-Aside, Refresh-Ahead

---

## 5. Refresh-Ahead

**목적**: TTL 만료 전에 미리 캐시를 갱신하여 만료 직후 발생하는 cache miss와 지연을 방지합니다.

**특징**:
- TTL의 일정 비율(예: 80%) 시점에 백그라운드에서 선제적 갱신 시작
- 사용자 요청이 캐시 만료 순간에 miss를 경험하지 않음
- Caffeine `refreshAfterWrite` 옵션이 대표 구현
- 실제 갱신은 다음 read 요청 시 비동기로 트리거 (Caffeine 방식)
- 접근 빈도 낮은 키에는 불필요한 갱신 비용 발생

**장점**:
- 핫(hot) 데이터의 cache miss 지연 제거
- Write-Through처럼 쓰기 경로 변경 없이 읽기 경로에서만 최적화
- 사용자 체감 일관된 응답속도

**단점**:
- 접근 빈도 낮은 키도 갱신 → 불필요한 DB 부하
- Caffeine 방식은 "만료 후 첫 조회" 시 갱신 트리거 → 엄밀한 사전 갱신 아님
- 갱신 실패 시 stale 데이터 계속 서빙

**활용 예시**:
- 홈 화면 상품 추천 리스트 (항상 최신)
- 환율·주가처럼 주기적 갱신이 필요한 데이터
- 인증 토큰 자동 갱신
- Caffeine `refreshAfterWrite` + `AsyncCacheLoader`

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import com.github.benmanes.caffeine.cache.AsyncCacheLoader
import com.github.benmanes.caffeine.cache.Caffeine
import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executor
import java.util.concurrent.TimeUnit

class ExchangeRateLoader : AsyncCacheLoader<String, Double> {
    /** 비동기 로더: DB/외부 API에서 환율 조회 */
    override fun asyncLoad(currency: String, executor: Executor): CompletableFuture<Double> =
        CompletableFuture.supplyAsync({
            println("[API] $currency 환율 갱신")
            if (currency == "USD") 1350.0 else 1450.0  // 실제로는 외부 API 호출
        }, executor)
}

fun main() {
    // expireAfterWrite: 10분 후 만료 / refreshAfterWrite: 8분 후 백그라운드 갱신
    val cache = Caffeine.newBuilder()
        .maximumSize(100)
        .expireAfterWrite(10, TimeUnit.MINUTES)
        .refreshAfterWrite(8, TimeUnit.MINUTES)  // TTL 80% 시점에 선제 갱신
        .buildAsync(ExchangeRateLoader())

    val usd = cache.get("USD").join()
    println("USD 환율: $usd")
    // 이후 8분 경과 후 첫 조회 시 백그라운드에서 자동 갱신
}
```

**관련 패턴**: Cache-Aside, Read-Through, Cache Stampede 방지

---

<a id="cache-stampede-prevention"></a>
## 6. Cache Stampede 방지 (singleflight / lock / probabilistic early expiration)

**목적**: 인기 키의 TTL 만료 순간 다수의 요청이 동시에 DB로 몰리는 Cache Stampede(Thundering Herd) 현상을 방지합니다.

**특징**:
- **Singleflight(Go 어휘)**: 동일 키에 대한 중복 로딩 요청을 하나로 병합 → 단 1번만 DB 조회, 결과 공유
- **분산 Lock**: Redis SETNX로 첫 번째 요청만 DB 조회, 나머지는 대기 후 캐시 히트
- **Probabilistic Early Expiration**: TTL 만료 전 확률적으로 갱신 시작 (Vlad Mihalcea, 2015 논문 기반)
  - `P(갱신) = exp(-(TTL_remaining / β))` — 만료가 가까울수록 갱신 확률 증가
- Caffeine의 `refreshAfterWrite`는 singleflight 방식으로 동시 갱신 방지

**장점**:
- DB 폭발적 부하 방지 (특히 인기 키 만료 시)
- Singleflight: 구현 단순, 응답 공유로 효율적
- Probabilistic: Lock 없이 점진적 갱신 → 분산 환경 적합

**단점**:
- Singleflight: 첫 갱신 완료까지 후속 요청 대기 → P99 지연 증가
- 분산 Lock: Lock 해제 실패(TTL 미설정) 시 Deadlock 위험
- Probabilistic: 구현 복잡, β 파라미터 튜닝 필요

**활용 예시**:
- 상품 상세 페이지 인기 상품 (초당 수천 요청)
- Redis 분산 캐시 miss 처리
- 인증 토큰 갱신 (동시 만료 방지)
- Caffeine 내부 singleflight 활용

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.concurrent.ConcurrentHashMap
import kotlin.math.exp
import kotlin.math.ln

// --- 방법 1: Singleflight (동일 키 중복 요청 병합) ---
class SingleflightCache<K, V>(
    private val loader: suspend (K) -> V,
) {
    private val cache = ConcurrentHashMap<K, V>()
    private val inFlight = ConcurrentHashMap<K, Deferred<V>>()
    private val mutex = Mutex()

    suspend fun get(key: K): V {
        cache[key]?.let { return it }
        return coroutineScope {
            val deferred = mutex.withLock {
                inFlight.getOrPut(key) {
                    async(Dispatchers.IO) {
                        loader(key).also { value ->
                            cache[key] = value
                            inFlight.remove(key)
                        }
                    }
                }
            }
            deferred.await()
        }
    }
}

// --- 방법 2: Probabilistic Early Expiration (Vlad Mihalcea 논문) ---
data class CacheEntry<V>(val value: V, val expiresAt: Long, val delta: Long)

fun <V> shouldRefresh(entry: CacheEntry<V>, beta: Double = 1.0): Boolean {
    val now = System.currentTimeMillis()
    val ttlRemaining = (entry.expiresAt - now).coerceAtLeast(0L)
    // P(갱신) = exp(-ttlRemaining / (beta * delta)) — 만료 근접할수록 확률 증가
    val probability = exp(-ttlRemaining.toDouble() / (beta * entry.delta.toDouble()))
    return Math.random() < probability
}
```

**관련 패턴**: Cache-Aside, Refresh-Ahead, Multi-Tier Cache

---

<a id="eviction-policies"></a>
## 7. TTL / LRU / LFU 정책 (Eviction Strategies)

**목적**: 캐시 용량 한계에서 어떤 항목을 제거할지, 얼마나 오래 보관할지를 결정하는 퇴거(Eviction) 정책을 선택합니다.

**특징**:
- **TTL (Time-To-Live)**: 항목 저장 후 지정 시간 경과 시 자동 만료. 시간 기반 일관성 보장
- **LRU (Least Recently Used)**: 가장 오래 전에 접근한 항목 제거. 최근 접근 패턴 반영
- **LFU (Least Frequently Used)**: 접근 빈도가 가장 낮은 항목 제거. 장기 인기 데이터 보존
- Caffeine은 **W-TinyLFU** 알고리즘 사용 — LRU + LFU 혼합, 높은 히트율
- Redis는 기본 LRU 변형(`allkeys-lru`, `volatile-lru`, `allkeys-lfu` 등 정책 선택)

**정책 비교 표**:

| 정책 | 제거 기준 | 메모리 오버헤드 | 적합한 워크로드 | 대표 구현 | 주요 단점 |
|------|-----------|----------------|----------------|-----------|-----------|
| **TTL** | 시간 경과 | 낮음 | 주기적 갱신 데이터, 세션 | Caffeine `expireAfterWrite`, Redis `EXPIRE` | 만료 동시 폭발 → Stampede |
| **LRU** | 최근 접근 시각 (오래될수록 제거) | 중간 (접근 시각 추적) | 시간 지역성 높은 워크로드 | Redis `allkeys-lru`, Caffeine `expireAfterAccess` | 일회성 스캔 패턴에 취약 (cache pollution) |
| **LFU** | 누적 접근 빈도 (낮을수록 제거) | 높음 (빈도 카운터) | 장기 인기 데이터 보존 | Redis `allkeys-lfu`, Caffeine W-TinyLFU | 새 데이터 초기 빈도 낮아 조기 퇴거, aging 필요 |
| **W-TinyLFU** | LRU + LFU 결합, window 기반 | 낮음 (bloom filter) | 범용 고히트율 캐시 | Caffeine 기본 알고리즘 | 구현 복잡 (라이브러리 활용 권장) |

**장점**:
- TTL: 구현 단순, 시간 기반 일관성 자동 보장
- LRU: 최근 접근 패턴 빠른 적응, 구현 O(1)
- LFU/W-TinyLFU: 인기 데이터 장기 보존, 캐시 오염(cache pollution) 방지

**단점**:
- TTL: 만료 시점에 일시적 miss 폭증 가능 (Stampede)
- LRU: 일회성 스캔(scan) 패턴에 취약 — 오래된 인기 데이터 퇴거
- LFU: 오래된 인기 데이터가 새 인기 데이터 유입 방해 (aging 필요)

**활용 예시**:
- Caffeine `maximumSize` + `expireAfterWrite/Access`
- Redis `maxmemory-policy allkeys-lru` (디폴트 권장)
- Redis `maxmemory-policy allkeys-lfu` (균등 접근 패턴)
- 세션 캐시: TTL = 세션 만료 시간

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import com.github.benmanes.caffeine.cache.Caffeine
import java.util.concurrent.TimeUnit

fun buildCacheByStrategy(strategy: String) = when (strategy) {
    // TTL: 쓰기 후 10분, 접근 후 5분 미접근 시 만료
    "ttl" -> Caffeine.newBuilder()
        .maximumSize(1_000)
        .expireAfterWrite(10, TimeUnit.MINUTES)
        .expireAfterAccess(5, TimeUnit.MINUTES)
        .build<String, Any>()

    // LRU 근사: Caffeine 내부 W-TinyLFU (LRU + LFU 혼합, 높은 히트율)
    "lru" -> Caffeine.newBuilder()
        .maximumSize(1_000)
        .build<String, Any>()

    // LFU 강조: 가중치 기반 — 크기가 큰 항목이 빨리 퇴거
    "lfu-weighted" -> Caffeine.newBuilder()
        .maximumWeight(100_000L)
        .weigher<String, Any> { _, v ->
            when (v) {
                is String -> v.length
                is ByteArray -> v.size
                else -> 1
            }
        }
        .build<String, Any>()

    else -> throw IllegalArgumentException("알 수 없는 전략: $strategy")
}

fun main() {
    // Redis 정책 예시 (커맨드라인)
    // redis-cli CONFIG SET maxmemory-policy allkeys-lfu
    // redis-cli CONFIG SET maxmemory 256mb
    println("Caffeine TTL 캐시: ${buildCacheByStrategy("ttl")}")
    println("Caffeine LFU 가중치 캐시: ${buildCacheByStrategy("lfu-weighted")}")
}
```

**관련 패턴**: Cache-Aside, Refresh-Ahead, Cache Stampede 방지

---

## 8. Negative Caching (Negative Result Caching)

**목적**: 존재하지 않는 데이터(null, 404, empty)에 대한 조회 결과도 캐시하여 반복적인 DB 조회를 방지합니다.

**특징**:
- 존재하지 않는 키에 대해 null/빈 값을 짧은 TTL로 캐시
- Cache-Aside 패턴에서 DB miss 시 null을 sentinel 값으로 저장
- 공격자가 의도적으로 없는 키를 대량 조회하는 Cache Busting 공격 방어
- TTL은 일반 데이터보다 짧게 설정 (수십 초 ~ 수 분)
- Bloom Filter와 결합하면 존재하지 않는 키 조회 자체를 차단 가능

**장점**:
- 반복적 DB miss 방어 (DoS·Cache Busting 방어)
- 존재하지 않는 사용자/상품 조회로 인한 DB 부하 제거
- 구현 단순 (Cache-Aside에 null 저장 로직 추가)

**단점**:
- 실제로 데이터가 생성되면 TTL까지 "없음"으로 서빙 → 짧은 TTL 필수
- 캐시 공간 사용 (null 값도 메모리 점유)
- 캐시 오염 방지를 위해 TTL 설계 주의

**활용 예시**:
- 사용자 프로파일 조회 (탈퇴·미존재 유저)
- 상품 상세 조회 (삭제된 상품)
- DNS Negative Caching (NXDOMAIN TTL)
- Bloom Filter + Negative Cache 조합

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import com.github.benmanes.caffeine.cache.Caffeine
import java.util.Optional
import java.util.concurrent.TimeUnit

class UserCacheService {
    // Optional.empty() 로 null(미존재) 캐싱 — Caffeine은 null 저장 불가
    private val cache = Caffeine.newBuilder()
        .maximumSize(10_000)
        .expireAfterWrite(5, TimeUnit.MINUTES)
        .build<Long, Optional<String>>()

    /** Negative Cache: DB miss 시 Optional.empty() 저장 (짧은 TTL) */
    fun getUsername(userId: Long): String? {
        val cached = cache.getIfPresent(userId)
        if (cached != null) {
            return if (cached.isPresent) {
                println("[Cache] 히트: $userId → ${cached.get()}")
                cached.get()
            } else {
                println("[Cache] Negative 히트: $userId 없음 (DB 조회 생략)")
                null
            }
        }

        // DB 조회
        val found = fetchFromDb(userId)
        if (found != null) {
            cache.put(userId, Optional.of(found))
            println("[DB] $userId 조회 성공 → 캐시 저장")
        } else {
            // Negative Caching: 짧은 TTL은 별도 cache로 분리하거나 만료 시간 재정의
            cache.put(userId, Optional.empty())
            println("[DB] $userId 없음 → Negative 캐시 저장 (60초 TTL)")
        }
        return found
    }

    private fun fetchFromDb(userId: Long): String? =
        if (userId in 1L..100L) "User-$userId" else null  // 실제로는 DB 쿼리
}

fun main() {
    val svc = UserCacheService()
    println(svc.getUsername(1L))    // DB 조회
    println(svc.getUsername(1L))    // 캐시 히트
    println(svc.getUsername(999L))  // DB miss → Negative 캐시 저장
    println(svc.getUsername(999L))  // Negative 캐시 히트 (DB 미조회)
}
```

**관련 패턴**: Cache-Aside, Cache Stampede 방지, TTL/LRU/LFU 정책

---

## 9. Multi-Tier Cache (L1 in-process + L2 distributed)

**목적**: 인-프로세스 캐시(L1, Caffeine)와 분산 캐시(L2, Redis)를 계층화하여 네트워크 지연 없이 최고 성능을 달성하고, 캐시 일관성과 용량을 함께 확보합니다.

**특징**:
- **L1 (in-process)**: 수 마이크로초, 프로세스 메모리, 소용량 (수백~수천 항목)
- **L2 (distributed)**: 수 밀리초, 공유 Redis, 대용량 (수백만 항목)
- 읽기: L1 miss → L2 조회 → DB 폴백, 각 계층에 자동 채움
- 쓰기/무효화: L2 무효화 후 → Redis Pub/Sub 또는 Keyspace Notification으로 모든 인스턴스의 L1 동시 무효화
- **일관성 전략**: L1은 짧은 TTL로 최종 일관성 / Pub/Sub으로 즉시 무효화
- Horizontal scale 시 여러 인스턴스의 L1이 diverge하지 않도록 invalidation broadcast 필수

**장점**:
- L1 히트 시 네트워크 왕복 없음 → 최저 지연
- L2로 용량 확장, 인스턴스 간 데이터 공유
- DB 부하를 두 계층으로 차단

**단점**:
- L1 무효화 동기화 복잡 (Pub/Sub 지연, 일시적 stale)
- L1과 L2 TTL 불일치로 인한 일관성 문제
- 운영 복잡도 증가 (두 캐시 시스템 모니터링 필요)

**활용 예시**:
- 고트래픽 상품 상세 API (Caffeine L1 + Redis L2)
- 인증 토큰 검증 (L1 캐시로 Redis 왕복 제거)
- 설정·피처 플래그 값 (전 인스턴스 일관성 + 낮은 지연)
- Spring Cache + Caffeine + Redis 조합

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
import com.github.benmanes.caffeine.cache.Caffeine
import redis.clients.jedis.Jedis
import redis.clients.jedis.JedisPubSub
import java.util.concurrent.TimeUnit

class MultiTierCache(
    private val jedis: Jedis,
    private val invalidatePubSub: Jedis,  // 무효화 수신 전용 연결
) {
    // L1: 인-프로세스 (Caffeine), 짧은 TTL — 인스턴스 로컬
    private val l1 = Caffeine.newBuilder()
        .maximumSize(1_000)
        .expireAfterWrite(30, TimeUnit.SECONDS)  // L2보다 짧게
        .build<String, String>()

    // L2: Redis (분산 캐시)
    private val L2_TTL_SEC = 300L

    init {
        // Redis Pub/Sub으로 타 인스턴스의 무효화 브로드캐스트 수신
        Thread {
            invalidatePubSub.subscribe(object : JedisPubSub() {
                override fun onMessage(channel: String, key: String) {
                    l1.invalidate(key)
                    println("[L1 무효화] Pub/Sub 수신: $key")
                }
            }, "cache:invalidate")
        }.apply { isDaemon = true }.start()
    }

    /** 읽기: L1 → L2 → DB 순으로 폴백 */
    fun get(key: String, loader: () -> String): String {
        l1.getIfPresent(key)?.let {
            println("[L1 히트] $key")
            return it
        }
        jedis.get(key)?.let { v ->
            println("[L2 히트] $key → L1 채움")
            l1.put(key, v)
            return v
        }
        println("[DB 조회] $key")
        return loader().also { v ->
            jedis.setex(key, L2_TTL_SEC, v)
            l1.put(key, v)
        }
    }

    /** 무효화: L2 삭제 후 전 인스턴스 L1 무효화 브로드캐스트 */
    fun invalidate(key: String) {
        jedis.del(key)
        l1.invalidate(key)
        jedis.publish("cache:invalidate", key)  // 타 인스턴스 L1 무효화
        println("[무효화 브로드캐스트] $key")
    }
}
```

**관련 패턴**: Cache-Aside, Cache Stampede 방지, TTL/LRU/LFU 정책

> **관련 (P1 신설)**: 브라우저 측 캐싱·preload/preconnect 는 [`web-performance.md#resource-hints`](web-performance.md#resource-hints) 참조 — HTTP 캐시 정책과 함께 LCP/TBT 최적화에 직접 영향.

---
