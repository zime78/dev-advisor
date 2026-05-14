# 부하 분산 알고리즘 (Load Balancing Algorithms)

정평 있는 8 부하 분산 알고리즘. NGINX / HAProxy / Envoy / AWS ELB·NLB / Google Maglev / Linkerd 사례. **L4 (TCP/UDP)** 와 **L7 (HTTP)** 모두 적용. 분산 시스템의 트래픽 분배는 reliability(failover), scalability(horizontal scale), latency 최소화의 교차점이며, 알고리즘 선택은 백엔드 성능 분포·연결 수명·세션 친화성(sticky) 요구에 따라 갈린다.

**원전·표준 참고**:
- Michael Mitzenmacher — *The Power of Two Random Choices: A Survey of Techniques and Results* (2001)
- Google — *Maglev: A Fast and Reliable Software Network Load Balancer* (NSDI 2016, Eisenbud et al.)
- David Karger et al. — *Consistent Hashing and Random Trees* (STOC 1997)
- NGINX Documentation — `ngx_http_upstream_module`
- HAProxy Documentation — `balance` algorithms (roundrobin, leastconn, source, uri, hdr, ...)
- Envoy — Load balancer algorithms (round_robin, least_request, ring_hash, maglev, random)
- Linkerd — EWMA + P2C (proxy 2.x default)

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [round-robin](#round-robin) | Round Robin | 라운드 로빈 | 낮음 |
| [weighted-round-robin](#weighted-round-robin) | Weighted Round Robin (Smooth WRR) | 가중 라운드 로빈 | 중간 |
| [least-connections](#least-connections) | Least Connections | 최소 연결 | 중간 |
| [least-response-time](#least-response-time) | Least Response Time | 최소 응답시간 | 중간 |
| [power-of-two-choices](#power-of-two-choices) | Power of Two Choices (P2C) | 둘 중 적은 쪽 | 중간 |
| [consistent-hashing-lb](#consistent-hashing-lb) | Consistent Hashing (LB 관점) | 일관 해싱 (LB) | 중간 |
| [maglev-hashing](#maglev-hashing) | Maglev Hashing | 매글레브 해싱 | 높음 |
| [ewma](#ewma) | EWMA | 지수 가중 이동평균 | 낮음 |

**관련 카탈로그**:
- [distributed.md#consistent-hashing](distributed.md#consistent-hashing) — Consistent Hashing 본체 (ring + virtual node)
- [data-structures.md](data-structures.md) — Min-Heap (Least Connections 의 우선순위 큐 구현)
- [probabilistic.md](probabilistic.md) — Reservoir / 랜덤 샘플링 (P2C 의 무작위 선택)
- [`../patterns/reliability.md`](../patterns/reliability.md) — Rate Limiter, Bulkhead, Circuit Breaker (LB 와 함께 reliability 스택)
- [`../patterns/distributed.md`](../patterns/distributed.md) — Service Mesh, API Gateway, Sidecar (LB 적용 지점)
- [`../patterns/networking.md`](../patterns/networking.md) — Reverse Proxy, L4/L7 구분

---

<a id="round-robin"></a>
## 1. Round Robin (라운드 로빈, RR)

**목적**: 백엔드 풀에 순차적으로 요청을 분배하여 부하를 균등하게 분산

**시간 복잡도**: O(1) per request

**공간 복잡도**: O(N) — 백엔드 수 N, 인덱스 1개

**특징**:
- 가장 단순한 LB 알고리즘 — 인덱스 i 를 `(i + 1) mod N` 으로 회전
- **모든 백엔드 동일 성능** 가정 (homogeneous)
- 백엔드의 현재 부하·응답 시간을 고려하지 않음 (stateless)
- L4·L7 모두 적용 가능, DNS RR 도 동일 원리
- 분산 LB 인스턴스 간 인덱스 동기화 불가 — 각 LB 가 독립 RR 시 글로벌 균등은 통계적으로만 성립

**장점**:
- 구현 1줄, 디버깅 쉬움, 예측 가능
- 락 경합 거의 없음 (atomic increment 1회)
- 백엔드 추가/제거 시 1 단위 갱신만 필요

**단점**:
- 백엔드 성능 차이 무시 → 느린 노드가 병목 (LSB: Last Slow Backend)
- long-lived 연결 시 연결 수 불균형 누적
- 백엔드 health check 와 결합 필요 (장애 노드도 순서대로 받음)

**활용 예시**:
- NGINX `upstream` 기본 알고리즘
- HAProxy `balance roundrobin`
- AWS ELB Classic (TCP listener 기본)
- 동일 스펙 stateless API 서버 풀

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
class RoundRobinBalancer(private val backends: List<String>) {
    private val idx = java.util.concurrent.atomic.AtomicInteger(0)

    fun next(): String {
        require(backends.isNotEmpty()) { "No backend available" }
        // 음수 wrap 방지 위해 & Int.MAX_VALUE
        val i = (idx.getAndIncrement() and Int.MAX_VALUE) % backends.size
        return backends[i]
    }
}

// 의사코드 - health-aware RR:
//   loop k = 0..N-1:
//       i = (idx + k) mod N
//       if healthy(backends[i]):
//           idx = i + 1
//           return backends[i]
//   raise NoHealthyBackend
//
// 분산 LB 환경 주의:
//   각 LB 인스턴스가 독립 idx 를 가지면 백엔드별 받는 인덱스가 어긋남
//   → 단기에는 약간의 hot/cold 발생, 장기에는 통계적으로 균등
```

**관련 알고리즘**: Weighted Round Robin, Least Connections, P2C

---

<a id="weighted-round-robin"></a>
## 2. Weighted Round Robin (가중 라운드 로빈, WRR / Smooth WRR)

**목적**: 백엔드별 capacity 가중치(weight)에 비례하여 요청을 분배

**시간 복잡도**: O(N) per request (Smooth WRR, NGINX 방식)

**공간 복잡도**: O(N) — 백엔드 N 개, 각 노드에 `(weight, currentWeight, effectiveWeight)`

**특징**:
- 이기종 백엔드(혼합 spec) 지원 — 예: 8 vCPU 노드 weight=8, 4 vCPU 노드 weight=4
- **Naive WRR** (단순 반복): 가중치만큼 연속 요청 → bursty, 캐시 친화성 ↓
- **Smooth WRR** (NGINX, Nginx Plus): 가중치 합 비율 유지 + 순서를 부드럽게 분산
- 동적 weight 조정 가능 (장애 시 effectiveWeight 감소 → 자동 페일오버)
- 비율 누적 알고리즘: 매 요청마다 `current += effective`, 최대값 노드 선택 후 `current -= total`

**장점**:
- 이기종 풀에서 capacity 비례 분배 — RR 의 직접적 확장
- Smooth WRR 은 burst 없는 부드러운 분배 (예: 5,1,1 → a a a b a c a a 가 아닌 a b a c a a a a 식)
- failover: failed 노드의 effectiveWeight 감소로 자연스러운 격하

**단점**:
- 정적 weight — 실시간 부하 반영 불가 (Least Connections 와 결합 필요)
- weight 갱신 시 모든 노드 상태 재계산
- weight 합이 클수록 캐시 라인 영향 큼 (보통 단일 LB worker 라 큰 문제 아님)

**활용 예시**:
- NGINX `upstream backend { server a weight=5; server b weight=1; }` (Smooth WRR)
- HAProxy `balance roundrobin` + `weight N` (Smooth)
- LVS (Linux Virtual Server) WRR 스케줄러
- Canary deploy: 신버전 weight=1, 구버전 weight=99 → 점진 증가

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// Smooth Weighted Round Robin (NGINX 방식)
data class WrrNode(
    val id: String,
    val weight: Int,                 // 정적 capacity
    var effectiveWeight: Int = weight, // 장애 시 감소
    var currentWeight: Int = 0,      // 매 회 누적
)

class SmoothWeightedRoundRobin(private val nodes: List<WrrNode>) {
    private val totalWeight: Int get() = nodes.sumOf { it.effectiveWeight }
    private val lock = Any()

    fun next(): WrrNode? = synchronized(lock) {
        if (nodes.isEmpty() || totalWeight <= 0) return null

        // 1) 모든 노드에 effectiveWeight 누적
        for (n in nodes) n.currentWeight += n.effectiveWeight

        // 2) 최대 currentWeight 노드 선택
        val best = nodes.maxBy { it.currentWeight }

        // 3) 선택된 노드는 total 만큼 차감 → 비율 유지
        best.currentWeight -= totalWeight
        return best
    }

    fun reportFailure(id: String) = synchronized(lock) {
        nodes.find { it.id == id }?.let {
            // 자연 페일오버: effective 감소 (점진 복구도 가능)
            it.effectiveWeight = maxOf(1, it.effectiveWeight - 1)
        }
    }
}

// 의사코드 - 동작 예 (weight 5, 1, 1):
//   iter   a.cur b.cur c.cur  pick   afterPick
//     1     5    1     1       a     -2 1 1
//     2     3    2     2       a     -4 2 2
//     3     1    3     3       b     1 -4 3
//     4     6    -3    4       a     -1 -3 4
//     5     4    -2    5       c     4 -2 -2
//     6     9    -1    -1      a     2 -1 -1   ...
//   결과: a a b a c a a → smooth, burst 없음
```

**관련 알고리즘**: Round Robin, Least Connections (동적 보정), Maglev (다른 해시 접근)

---

<a id="least-connections"></a>
## 3. Least Connections (최소 연결, LC)

**목적**: 현재 활성 연결 수가 가장 적은 백엔드에 요청 라우팅

**시간 복잡도**: O(log N) per request (min-heap), O(N) (linear scan)

**공간 복잡도**: O(N) — 각 백엔드의 active connection counter

**특징**:
- **long-lived connection** (WebSocket, gRPC streaming, DB pool) 에 적합
- LB 가 백엔드별 활성 연결 수를 직접 추적 (connect → +1, close → -1)
- **Weighted Least Connections**: `connections / weight` 최소값 선택 — 이기종 풀 지원
- 분산 LB 인스턴스 간 정보 공유는 보통 안 함 (local view 만) → 글로벌 최적은 아님
- 백엔드 응답 시간이 다르면 연결 수만으로는 부족 → LRT/EWMA 와 결합

**장점**:
- 백엔드 처리 속도 차이를 연결 수가 자연스럽게 반영 (느린 노드 = 연결 누적 = 회피)
- 새 노드 추가 시 빠르게 트래픽 흡수 (count=0)
- failover 와 자연스러운 결합

**단점**:
- 짧은 HTTP 요청에는 RR 대비 이득 작음 (연결 수 차이 미미)
- LB 가 stateful — 분산 LB 시 동기화 비용
- "connection slow start" 문제: 새 노드가 0 → 모든 트래픽 집중 → thundering herd

**활용 예시**:
- NGINX `least_conn`
- HAProxy `balance leastconn`
- AWS NLB (TCP) — `least_outstanding_requests` 옵션
- WebSocket / SSE 서버 풀, DB connection pooler (PgBouncer)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.concurrent.atomic.AtomicInteger
import java.util.PriorityQueue

class Backend(val id: String, val weight: Int = 1) {
    val connections = AtomicInteger(0)
    // 비교 키: connections / weight (Weighted LC)
    fun score(): Double = connections.get().toDouble() / weight
}

class LeastConnectionsBalancer(private val backends: List<Backend>) {

    fun acquire(): Backend? {
        // O(N) linear scan — N 이 작으면(<100) heap 보다 빠름
        val target = backends
            .filter { it.connections.get() < MAX_CONN_PER_BACKEND }
            .minBy { it.score() } ?: return null
        target.connections.incrementAndGet()
        return target
    }

    fun release(backend: Backend) {
        backend.connections.decrementAndGet()
    }

    companion object { const val MAX_CONN_PER_BACKEND = 10_000 }
}

// 사용:
//   val be = lb.acquire() ?: throw NoBackend()
//   try { handle(be) } finally { lb.release(be) }

// 의사코드 - heap 기반 O(log N):
//   pq = PriorityQueue<Backend> by score()
//   on request:
//       b = pq.poll()
//       b.connections++
//       pq.offer(b)
//   문제: poll/offer 만으로는 score 갱신 추적 불가 → "lazy delete + reinsert" 패턴 필요
//   실용적으로 N < 1000 이면 linear scan 권장
```

**관련 알고리즘**: Round Robin, Weighted RR, Least Response Time, P2C (분산 환경에서 LC 의 더 가벼운 대안)

---

<a id="least-response-time"></a>
## 4. Least Response Time (최소 응답시간, LRT)

**목적**: 백엔드의 응답 시간(평균/EWMA)이 가장 짧은 노드 선택 — latency-aware 라우팅

**시간 복잡도**: O(N) per request (heap 사용 시 O(log N), 동적 키 갱신 부담 있음)

**공간 복잡도**: O(N) — 백엔드별 EWMA 응답 시간

**특징**:
- 연결 수 + 응답 시간 (또는 둘만)을 함께 고려
- 응답 시간 평가는 **EWMA** (지수 가중 이동평균) 가 표준 — [#ewma](#ewma) 참조
- NGINX Plus `least_time` 변형: `header` (TTFB), `last_byte` (TTLB), `header inflight` 등
- HAProxy `balance random` + agent check 와 결합도 비슷한 효과
- backend slow start 와 결합되면 새 노드 RTT 가 작아 폭주 가능 → **probation period** 필요

**장점**:
- 백엔드 성능 변화(GC pause, 디스크 spike)를 빠르게 반영
- 사용자 체감 latency 직접 최적화
- 이기종 백엔드 + 가변 워크로드에 강함

**단점**:
- 측정 노이즈(outlier) 영향 큼 → EWMA window 튜닝 필수
- 응답 시간 0 인 새 노드로 폭주 → 초기 phantom load 패딩(`1ms` 등) 필요
- LB 와 backend 의 거리·네트워크 RTT 변동을 노이즈로 받아들이기 쉬움

**활용 예시**:
- NGINX Plus `least_time header` / `least_time last_byte`
- Envoy `LEAST_REQUEST` + `slow_start_config`
- Linkerd EWMA + P2C (default)
- 지역별 latency-sensitive 서비스 (CDN edge → origin)

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class LrtBackend(val id: String) {
    val ewma = Ewma(halfLifeMs = 10_000) // 10초 반감기
    val inflight = java.util.concurrent.atomic.AtomicInteger(0)
    // 초기 phantom RTT: 새 노드 폭주 방지
    init { ewma.observe(50.0) }
}

class LeastResponseTimeBalancer(private val backends: List<LrtBackend>) {

    fun next(): LrtBackend? {
        // score = ewma.value * (1 + inflight)
        // → inflight 가 가중치 (penalty 가 가산)
        val target = backends.minBy {
            it.ewma.value() * (1.0 + it.inflight.get())
        }
        target.inflight.incrementAndGet()
        return target
    }

    fun report(backend: LrtBackend, latencyMs: Double) {
        backend.inflight.decrementAndGet()
        backend.ewma.observe(latencyMs)
    }
}

// 의사코드 - slow start (probation):
//   newBackend.weight = 0
//   over probation period (e.g. 30s):
//       newBackend.weight = elapsed / probation  // 0 → 1 선형 증가
//   ⇒ 새 노드가 갑자기 모든 트래픽을 받지 않음 (Envoy slow_start_config)
```

**관련 알고리즘**: EWMA, Least Connections, P2C+EWMA (Linkerd 조합)

---

<a id="power-of-two-choices"></a>
## 5. Power of Two Choices (P2C, 둘 중 적은 쪽)

**목적**: 무작위 2개 후보를 뽑은 뒤 부하가 적은 쪽을 선택 — 분산 LB 에서 글로벌 정보 없이 LC 에 근접하는 결과를 얻는 기법

**시간 복잡도**: O(1) per request (heap 등 자료구조 불필요)

**공간 복잡도**: O(N) — 백엔드별 부하 카운터만 (분산 LB 인스턴스 간 동기화 불필요)

**특징**:
- **이론 근거**: Mitzenmacher (1996, 2001) — N 개의 bin 에 m 개의 ball 을 던질 때
  - 1개 무작위 선택: 최대 bin 의 load = `ln N / ln ln N + Θ(1)`
  - 2개 무작위 후 적은 쪽: 최대 bin 의 load = `ln ln N / ln 2 + Θ(1)` — **exponential 개선**
- "The Power of Two Random Choices" — d=2 가 sweet spot. d=3 이상은 marginal gain
- 무작위 선택이므로 분산 LB 인스턴스가 독립적으로 결정해도 글로벌 균형 보장
- score 함수는 임의: connections, inflight, EWMA latency, queue depth 등

**장점**:
- O(1) — heap/sorted set 없이 random.sample(N, 2) + 1 비교
- 분산 환경에 강함 — global state coordination 불필요
- 단일 LC 보다 noisy backend(GC pause 등) 회피 효율 ↑ (균등 hash + score 결합 효과)
- exponential 분포 개선이라는 강한 이론적 보장

**단점**:
- 무작위라 worst case (같은 노드 2회 선택) 처리 필요 — 다른 노드 1회 더 뽑기
- 매우 작은 N (N=2,3) 에서 이점 없음 — RR 권장
- score 가 stale 하면 잘못된 선택 (LC 와 동일 문제)

**활용 예시**:
- **Linkerd 2.x** proxy 기본 알고리즘 (EWMA + P2C)
- Envoy `LEAST_REQUEST` (기본 `choice_count: 2`)
- HAProxy `balance random(2)` (`random` 알고리즘 + draw=2)
- Twitter Finagle — P2C + EWMA (논문: *Predictive Load-Balancing*)
- Akka cluster routing

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
class P2cBackend(val id: String) {
    val inflight = java.util.concurrent.atomic.AtomicInteger(0)
    val ewma = Ewma(halfLifeMs = 10_000)
    fun score(): Double = ewma.value() * (1.0 + inflight.get())
}

class P2cBalancer(private val backends: List<P2cBackend>) {
    private val rng = java.util.concurrent.ThreadLocalRandom.current()

    fun next(): P2cBackend? {
        val n = backends.size
        if (n == 0) return null
        if (n == 1) return backends[0]

        // 무작위로 서로 다른 두 인덱스
        val i = rng.nextInt(n)
        var j = rng.nextInt(n - 1)
        if (j >= i) j++

        val a = backends[i]
        val b = backends[j]
        val pick = if (a.score() <= b.score()) a else b
        pick.inflight.incrementAndGet()
        return pick
    }

    fun report(b: P2cBackend, latencyMs: Double) {
        b.inflight.decrementAndGet()
        b.ewma.observe(latencyMs)
    }
}

// 의사코드 - d-choice 일반화:
//   sample d distinct indices
//   pick min score among d
//   d=2 가 권장 (gain/cost trade-off optimal)
//
// Mitzenmacher 결과 핵심:
//   max load with d=1: O(log N / log log N)   ← uniform random
//   max load with d=2: O(log log N / log 2)   ← P2C
//   ⇒ N=1024 기준 약 11 → 4 로 감소 (대략)
```

**관련 알고리즘**: Least Connections, Random LB, EWMA, Consistent Hashing (반대 접근 — deterministic)

---

<a id="consistent-hashing-lb"></a>
## 6. Consistent Hashing (LB 관점, 일관 해싱)

**목적**: 요청 키(예: client IP, session ID, URL hash)를 해시 ring 에 매핑해 동일 키는 항상 동일 백엔드로 — sticky session / cache locality / sharding 동시 달성

**시간 복잡도**: O(log V) — V = 가상 노드 수 (binary search on sorted ring)

**공간 복잡도**: O(V) — virtual node 수 (보통 N × 100 ~ 200)

**특징**:
- LB 관점에서는 **sticky session** 과 **upstream cache hit rate** 가 주된 동기
- **distributed.md/consistent-hashing 본체와 차별점** (LB 관점):
  - 캐시 분배(memcached, varnish) 가 아닌 **요청 → 백엔드 매핑**
  - 키 선택: `client_ip` (NGINX `hash $remote_addr consistent`), `session_id`, `URI`, `header` 가 흔함
  - 백엔드 추가/제거 시 **K/N 비율의 세션만 재배치** → 캐시 mass invalidation 방지
- **bounded-load** 변형 (Google 2017): 노드 load 가 평균의 (1+ε) 초과 시 다음 노드로 spill → hot key 대응
- 가상 노드(vnode) 수: 적으면 분포 불균등, 많으면 메모리 ↑ — 100~200 이 일반적

**장점**:
- 같은 client / session 은 항상 같은 백엔드 → upstream 캐시 hit ↑, 세션 affinity 자연 확보
- 백엔드 추가/제거 시 1/N 만 재배치 (vs RR 의 N-1/N)
- 분산 LB 인스턴스 간 협의 불필요 — 같은 해시 함수 + 같은 ring 이면 동일 결과

**단점**:
- 부하 분포는 균등이 아닌 **확률적** — vnode 가 부족하면 skew 발생
- hot key (예: VIP user) 가 단일 백엔드 폭주 → bounded-load 또는 P2C 결합 필요
- ring 재계산 비용 (백엔드 변경 시 N×V 개 hash 재정렬)

**활용 예시**:
- NGINX `hash $request_uri consistent;` (Plus 기능, `consistent` 키워드)
- HAProxy `balance uri consistent` / `balance hdr(X-User) consistent`
- Envoy `ring_hash` LB policy
- Memcached client (sharding) — Ketama 알고리즘
- DynamoDB / Cassandra 의 partitioning (ring + vnode)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import java.util.TreeMap

class ConsistentHashLb(
    backends: Collection<String>,
    private val vnodes: Int = 160, // Ketama default
) {
    private val ring = TreeMap<Long, String>()

    init { backends.forEach(::addBackend) }

    fun addBackend(b: String) {
        repeat(vnodes) { i ->
            val h = murmur64("$b#$i")
            ring[h] = b
        }
    }

    fun removeBackend(b: String) {
        repeat(vnodes) { i ->
            ring.remove(murmur64("$b#$i"))
        }
    }

    /** 키(client IP / session ID / URI) → 백엔드 */
    fun route(key: String): String? {
        if (ring.isEmpty()) return null
        val h = murmur64(key)
        // ring 에서 h 이상의 첫 entry (없으면 wrap-around → firstEntry)
        val e = ring.ceilingEntry(h) ?: ring.firstEntry()
        return e.value
    }

    private fun murmur64(s: String): Long {
        // 실전: MurmurHash3, xxHash 같은 균등 해시 사용
        var h = 0xcbf29ce484222325UL.toLong()
        for (c in s) h = (h xor c.code.toLong()) * 0x100000001b3L
        return h
    }
}

// 의사코드 - bounded-load consistent hashing:
//   averageLoad = totalRequests / N
//   cap = ceil(averageLoad * (1 + ε))     // ε = 0.25 가 흔함
//   on route(key):
//       node = ring.ceil(hash(key))
//       while node.load >= cap:
//           node = ring.successor(node)   // 다음 노드로 spill
//       node.load++
//       return node
//   ⇒ hot key 가 단일 노드 폭주를 방지하면서도 affinity 최대한 유지
```

**관련 알고리즘**: [distributed.md#consistent-hashing](distributed.md#consistent-hashing) (본체), Maglev Hashing, Rendezvous Hashing, Bounded-Load Consistent Hashing

---

<a id="maglev-hashing"></a>
## 7. Maglev Hashing (매글레브 해싱)

**목적**: lookup table 기반 consistent hash 로 O(1) 조회 + 균등한 분포 + 백엔드 변경 시 최소 disruption — Google 의 대규모 software LB 알고리즘

**시간 복잡도**: O(1) lookup, O(M·N) table build (M = table size, N = 백엔드 수)

**공간 복잡도**: O(M) — lookup table 크기 (보통 M = 65537 같은 prime)

**특징**:
- 출처: *Maglev: A Fast and Reliable Software Network Load Balancer*, NSDI 2016 (Eisenbud 외)
- **lookup table** `entry[0..M-1]` 가 각 슬롯에 백엔드 인덱스를 저장 → 패킷마다 `entry[hash(5-tuple) mod M]` 한 번 참조
- 각 백엔드는 두 해시 함수로 **permutation** 을 생성 (`offset`, `skip`)
- table 채우기: 각 백엔드가 자기 permutation 순으로 빈 슬롯 차지 → ring 보다 균등 분포
- 백엔드 1개 변경 시 평균 약 `1/N` 슬롯만 변경 → consistent hashing 성질
- M >> N · 100 일 때 분포 균등 + disruption 최소
- L4 LB (Google Cloud LB, AWS NLB 영감) 에서 packet-rate 가 매우 높을 때 ring 의 O(log N) 도 부담 → O(1) 필요

**장점**:
- **O(1) lookup** — 패킷 처리 hot path 최적
- ring hashing 보다 더 균등한 분포 (worst case 차이 작음)
- 백엔드 변경 시 ~1/N 슬롯만 변경 (consistent)
- multi-core 환경에서 lookup table 이 read-only → lock-free, false sharing 없음

**단점**:
- table rebuild 비용 O(M·N) — 백엔드 변경 시 전체 재계산 (대규모에서는 ms 단위 소요)
- M (table size) 선택 민감: 너무 작으면 분포 skew, 너무 크면 메모리
- 가중치 지원이 native 가 아님 — 같은 백엔드를 여러 번 등록하거나 별도 weight 확장 필요
- 구현이 ring 보다 복잡

**활용 예시**:
- **Google Cloud Network LB** (Maglev 그 자체)
- Envoy `maglev` LB policy
- Katran (Facebook 의 eBPF 기반 L4 LB)
- 대규모 stateful packet routing (DSR, Direct Server Return)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
/**
 * Maglev hashing — Eisenbud et al., NSDI 2016
 * lookup table 기반 consistent hash. O(1) lookup, ~1/N disruption.
 *
 * @param backends 백엔드 ID 목록 (N 개)
 * @param tableSize M (prime 권장, M >> N · 100)
 */
class MaglevHash(
    private val backends: List<String>,
    private val tableSize: Int = 65537, // prime
) {
    private val lookup: IntArray = buildLookup()

    /** Maglev 의 핵심: 두 해시 함수 → permutation → 빈 슬롯 채우기 */
    private fun buildLookup(): IntArray {
        val n = backends.size
        val m = tableSize
        require(n in 1..m) { "Need 1 <= N <= M" }

        // permutation[i][j] = i 번째 백엔드의 j 번째 시도 인덱스
        val permutation = Array(n) { i ->
            val offset = (hash1(backends[i]) % m).toInt().let { if (it < 0) it + m else it }
            val skip = ((hash2(backends[i]) % (m - 1)).toInt().let { if (it < 0) it + m - 1 else it } + 1)
            IntArray(m) { j -> (offset + j * skip) % m }
        }

        val next = IntArray(n)
        val entry = IntArray(m) { -1 }
        var filled = 0
        while (filled < m) {
            for (i in 0 until n) {
                // i 번째 백엔드가 자기 permutation 다음 슬롯에 자리 잡으려 시도
                var c = permutation[i][next[i]]
                while (entry[c] != -1) {
                    next[i]++
                    c = permutation[i][next[i]]
                }
                entry[c] = i
                next[i]++
                filled++
                if (filled == m) break
            }
        }
        return entry
    }

    /** 패킷의 5-tuple hash → 백엔드 */
    fun route(connectionKey: String): String {
        val idx = ((connectionKey.hashCode().toLong() and 0xffffffffL) % tableSize).toInt()
        return backends[lookup[idx]]
    }

    private fun hash1(s: String): Long = s.hashCode().toLong() * 0x9E3779B97F4A7C15UL.toLong()
    private fun hash2(s: String): Long = (s.hashCode().toLong() xor 0xDEADBEEFL) * 0xC6BC279692B5C323UL.toLong()
}

// 의사코드 - disruption 비교:
//   N=1000, M=65537 일 때 백엔드 1개 제거 시:
//     ring hashing:  vnodes=160 면 약 0.1% slot 이동 (이론)
//     maglev:        평균 1/N = 0.1% slot 이동 + 분포 더 균등
//   N=10, M=65537:
//     ring 의 vnode 가 적으면 skew 큼
//     maglev 는 균등 분포 보장
```

**관련 알고리즘**: Consistent Hashing, Rendezvous Hashing, Ring Hash + bounded-load

---

<a id="ewma"></a>
## 8. EWMA (지수 가중 이동평균, Exponentially Weighted Moving Average)

**목적**: 백엔드 응답 시간의 최근 추세를 O(1) 메모리로 추적하여 LRT/P2C 의 score 함수에 사용

**시간 복잡도**: O(1) per observation

**공간 복잡도**: O(1) per backend — `(value, lastUpdate)` 만 저장

**특징**:
- 일반 이동평균은 window 메모리 O(W) 필요 — EWMA 는 O(1) + 시간 가중 자동 감쇠
- 수식: `value_new = α · sample + (1 - α) · value_old`, α ∈ (0, 1)
- **time-decayed EWMA**: 관측 간격 Δt 와 반감기(half-life) τ 를 사용
  - `α = 1 - exp(-Δt · ln 2 / τ)` — 관측이 띄엄띄엄 와도 시간 비례 가중
- 반감기 τ: 짧으면 (예: 1초) 반응성 ↑ / noise ↑, 길면 (예: 30초) 안정성 ↑ / 반응성 ↓
- P50, P99 같은 percentile 은 EWMA 로 추적 불가 (HDR histogram 또는 t-digest 필요)

**장점**:
- O(1) 메모리·연산 — high-throughput LB hot path 에 적합
- 시간 가중 자동 — 오래된 관측은 자연 소멸 (sliding window 불필요)
- 단순 — 구현 10줄, 디버깅 쉬움

**단점**:
- 평균만 추적 — outlier / tail latency 미반영
- 반감기 τ 튜닝 필요 (워크로드별 적정값 다름)
- α 가 너무 크면 jitter 에 과민, 너무 작으면 stale spike 미감지
- 부정확한 시간 동기 환경(virtual machine pause)에서 lastUpdate 가 튀면 α 계산 잘못됨

**활용 예시**:
- **Linkerd EWMA** (P2C 결합) — 백엔드 score 추적
- Netflix Atlas / Hystrix — 회로 차단기 통계
- TCP RTO 추정 (Jacobson 알고리즘, EWMA 변형)
- 시스템 메트릭 dashboard (Datadog, Prometheus `*_rate_*` 함수 일부)
- 알고리즘 트레이딩의 EMA / DEMA

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import kotlin.math.exp
import kotlin.math.ln
import java.util.concurrent.atomic.AtomicLong

/**
 * Time-decayed EWMA
 *
 * 반감기 halfLifeMs 동안 가중치가 정확히 절반으로 감쇠.
 * 관측이 띄엄띄엄 와도 시간 비례로 자동 감쇠 (sliding window 불필요).
 */
class Ewma(private val halfLifeMs: Long, initial: Double = 0.0) {
    @Volatile private var value: Double = initial
    private val lastUpdateNs = AtomicLong(System.nanoTime())
    private val decayPerMs = ln(2.0) / halfLifeMs

    @Synchronized
    fun observe(sample: Double) {
        val now = System.nanoTime()
        val deltaMs = (now - lastUpdateNs.get()) / 1_000_000.0
        // 시간 가중 α — 관측 간격이 길수록 새 sample 비중 ↑
        val alpha = 1.0 - exp(-deltaMs * decayPerMs)
        value = alpha * sample + (1.0 - alpha) * value
        lastUpdateNs.set(now)
    }

    fun value(): Double = value
}

// 의사코드 - half-life 직관:
//   halfLifeMs = 10_000 (10초) 라면:
//     10초 후 새 관측 1번 → 새 값이 50% 비중
//     20초 후 새 관측 1번 → 새 값이 75% 비중
//     ⇒ 오래된 데이터는 자연스럽게 forget
//
// Jacobson TCP RTO 변형 (참고):
//   SRTT  = (1 - α) · SRTT  + α · RTT_sample     α = 1/8
//   RTTVAR = (1 - β) · RTTVAR + β · |SRTT - RTT_sample|   β = 1/4
//   RTO    = SRTT + 4 · RTTVAR
//   ⇒ 평균 + 분산 둘 다 EWMA 로 추적해 robust 한 timeout 계산
```

**관련 알고리즘**: Least Response Time, P2C, Reservoir Sampling, HDR Histogram (percentile 필요 시 대안)

---

## 알고리즘 선택 가이드

| 상황 | 권장 알고리즘 | 이유 |
|------|-------------|------|
| 동일 스펙 stateless API, 짧은 HTTP | Round Robin | 단순·예측 가능, 락 없음 |
| 이기종 풀 (CPU/RAM 다름) | Weighted Round Robin (Smooth) | capacity 비례 분배 |
| WebSocket / gRPC streaming / DB pool | Least Connections (또는 Weighted LC) | long-lived 연결 균등화 |
| 분산 LB 인스턴스 다수, score 동기화 불가 | Power of Two Choices | global state 불필요, exponential 개선 |
| latency 변동 큰 백엔드 (GC, disk spike) | EWMA + P2C 또는 Least Response Time | 실시간 성능 반영 |
| sticky session, upstream cache locality | Consistent Hashing (+ bounded-load) | 같은 키 → 같은 노드 |
| L4 packet-rate 매우 높음, 변경 잦음 | Maglev Hashing | O(1) lookup + 1/N disruption |
| Canary deploy, 점진 트래픽 이동 | Weighted Round Robin | weight 동적 조정 |

**조합 패턴**:
- **Linkerd 2.x**: `P2C + EWMA` — 분산 + latency-aware
- **Envoy ring_hash**: `Consistent Hashing + bounded-load` — affinity + hot key 보호
- **NGINX**: `Smooth WRR + health check` — 이기종 + 자연 failover
- **Google Maglev**: `Maglev + DSR` — L4 hot path, 패킷당 O(1)

## 운영 체크리스트

- [ ] **백엔드 health check** 와 결합 — LB 알고리즘 자체는 장애 노드를 자동 격리하지 않음
- [ ] **slow start (probation period)** — 새 노드가 EWMA=0 으로 모든 트래픽 받지 않게
- [ ] **session affinity** 요구가 있으면 Consistent Hashing 으로 시작, hot key 발견되면 bounded-load 추가
- [ ] **분산 LB 환경**에서는 P2C 또는 Consistent Hashing 우선 — Least Connections 는 local view 라 글로벌 최적 보장 안 됨
- [ ] **메트릭**: `lb.backend.{requests, errors, latency_p50, latency_p99, inflight, connections}` per backend
- [ ] **alarm**: 백엔드별 traffic skew (vs 평균 ±20% 이상 지속) → algorithm/weight 점검
- [ ] **canary**: WRR weight 단계적 증가 (1% → 5% → 25% → 100%) — 한 번에 100% 금지
