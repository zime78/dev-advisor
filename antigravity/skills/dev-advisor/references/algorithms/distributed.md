# 분산 알고리즘 (Distributed Algorithms)

분산 시스템에서 노드 간 시간 순서, 멤버십, 상태 동기화, 데이터 분배, 일관성 보장을 처리하는 알고리즘입니다. 합의(consensus)는 별도 카테고리에 있으며, 본 카테고리는 logical clock, membership, anti-entropy, CRDT, partitioning, quorum 등 분산 시스템의 보조 빌딩블록을 다룹니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [lamport-clock](#lamport-clock) | Lamport Clock | 램포트 시계 | 중간 |
| [vector-clock](#vector-clock) | Vector Clock | 벡터 시계 | 중간 |
| [hybrid-logical-clock](#hybrid-logical-clock) | Hybrid Logical Clock | 하이브리드 논리 시계 | 높음 |
| [gossip-protocol](#gossip-protocol) | Gossip Protocol | 가십 프로토콜 | 중간 |
| [swim](#swim) | SWIM | SWIM 멤버십 | 높음 |
| [anti-entropy](#anti-entropy) | Anti-Entropy | 안티엔트로피 (Merkle sync) | 높음 |
| [crdt-g-counter](#crdt-g-counter) | CRDT G-Counter | G-카운터 | 중간 |
| [crdt-pn-counter](#crdt-pn-counter) | CRDT PN-Counter | PN-카운터 | 중간 |
| [crdt-or-set](#crdt-or-set) | CRDT OR-Set | OR-셋 | 높음 |
| [crdt-lww-set](#crdt-lww-set) | CRDT LWW-Set | LWW-셋 | 중간 |
| [consistent-hashing](#consistent-hashing) | Consistent Hashing | 일관 해싱 | 중간 |
| [quorum](#quorum) | Quorum (R+W>N) | 쿼럼 | 중간 |
| [chandy-lamport](#chandy-lamport) | Chandy-Lamport Distributed Snapshot | 찬디-램포트 분산 스냅샷 | 높음 |
| [phi-accrual](#phi-accrual) | Phi Accrual Failure Detector | 파이 누적 장애 감지기 | 중간 |

---

<a id="lamport-clock"></a>
## 1. Lamport Clock (램포트 시계)

**목적**: 분산 노드 간 이벤트의 happens-before(→) 관계를 단일 정수 카운터로 부분 순서화

**시간 복잡도**: O(1) per event

**공간 복잡도**: O(1) per node

**특징**:
- 스칼라 logical clock (단일 정수)
- 규칙 1: 로컬 이벤트 시 `clock++`
- 규칙 2: 메시지 송신 시 timestamp 첨부
- 규칙 3: 수신 시 `clock = max(local, recv) + 1`
- 부분 순서(partial order)만 보장 — 동시(concurrent) 이벤트는 구분 불가

**장점**:
- 매우 단순, O(1) 메모리
- 어떤 분산 환경에서도 동작
- 인과 관계의 필요 조건(necessary) 제공

**단점**:
- 충분 조건은 아님 — `a → b ⇒ C(a) < C(b)` 만 보장, 역은 거짓
- 동시성 판별 불가 (Vector Clock 필요)
- 동률(tie) 발생 시 node ID로 깨야 함

**활용 예시**:
- 분산 mutex (Lamport mutual exclusion)
- 메시지 ordering 기본기
- DynamoDB, Cassandra 의 timestamp 기반 LWW
- 디버깅 / trace 정렬

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
class LamportClock(val nodeId: String) {
    private var clock: Long = 0

    @Synchronized
    fun localEvent(): Long {
        clock += 1
        return clock
    }

    @Synchronized
    fun send(): Long {
        clock += 1
        return clock // 메시지에 첨부
    }

    @Synchronized
    fun receive(remote: Long): Long {
        clock = maxOf(clock, remote) + 1
        return clock
    }

    // 전체 순서(total order)가 필요하면 (timestamp, nodeId) 튜플 비교
    data class Stamp(val ts: Long, val nodeId: String) : Comparable<Stamp> {
        override fun compareTo(other: Stamp): Int =
            compareValuesBy(this, other, { it.ts }, { it.nodeId })
    }
}

// 의사코드 - happens-before:
//   if a, b in same node and a before b → C(a) < C(b)
//   if a = send(m), b = recv(m)         → C(a) < C(b)
//   transitivity 로 확장
//
// 한계:
//   C(a) < C(b) 만으로는 a → b 라고 결론 불가 (concurrent 일 수 있음)
```

**관련 알고리즘**: Vector Clock, HLC, Version Vector

---

<a id="vector-clock"></a>
## 2. Vector Clock (벡터 시계)

**목적**: 노드별 카운터 벡터로 인과 관계와 동시성(concurrency)을 모두 판별

**시간 복잡도**: O(N) per merge, N = 노드 수

**공간 복잡도**: O(N) per event

**특징**:
- 각 노드 i 는 길이 N 벡터 `V[i]` 유지
- 로컬 이벤트: `V[i][i]++`
- 송신: 자신의 V 첨부
- 수신: `V[i][k] = max(V[i][k], V_recv[k])` 모든 k, 그 후 `V[i][i]++`
- 비교: `V_a < V_b` iff 모든 원소 ≤ 이고 적어도 하나 < → 인과; 둘 다 아니면 concurrent

**장점**:
- 인과(causal) 관계 정확 판별 (필요+충분)
- 동시 업데이트 충돌 감지 가능
- Dynamo, Riak 의 anti-entropy 기반

**단점**:
- O(N) 공간 — 노드 수 증가 시 부담
- 멤버십 변동 시 벡터 truncate 필요
- 메시지마다 벡터 전송 — 대역폭 비용

**활용 예시**:
- Amazon Dynamo (값 버전 관리)
- Riak object versioning
- Voldemort
- Git 의 commit ancestry 와 유사 개념

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
data class VectorClock(val v: MutableMap<String, Long> = mutableMapOf()) {

    fun localEvent(nodeId: String) {
        v[nodeId] = (v[nodeId] ?: 0L) + 1L
    }

    fun merge(other: VectorClock) {
        for ((k, t) in other.v) {
            v[k] = maxOf(v[k] ?: 0L, t)
        }
    }

    fun receive(nodeId: String, other: VectorClock) {
        merge(other)
        localEvent(nodeId)
    }

    // 인과 비교
    enum class Order { BEFORE, AFTER, EQUAL, CONCURRENT }

    fun compare(other: VectorClock): Order {
        val keys = v.keys union other.v.keys
        var less = false
        var greater = false
        for (k in keys) {
            val a = v[k] ?: 0L
            val b = other.v[k] ?: 0L
            if (a < b) less = true
            if (a > b) greater = true
        }
        return when {
            !less && !greater -> Order.EQUAL
            less && !greater  -> Order.BEFORE
            !less && greater  -> Order.AFTER
            else              -> Order.CONCURRENT // 충돌 (sibling)
        }
    }
}

// 의사코드 - Dynamo 충돌 해소:
//   put(key, value, context = V_old):
//       V_new = V_old.clone()
//       V_new.localEvent(coordinator)
//       store (value, V_new)
//   get(key) 가 여러 sibling 반환 시:
//       application 이 merge 또는 LWW 로 해결
```

**관련 알고리즘**: Lamport Clock, Version Vector, HLC, Dotted Version Vector

---

<a id="hybrid-logical-clock"></a>
## 3. Hybrid Logical Clock (하이브리드 논리 시계, HLC)

**목적**: 물리 시계(wall clock)의 직관성과 logical clock 의 인과 보장을 결합

**시간 복잡도**: O(1) per event

**공간 복잡도**: O(1) — `(pt, l, c)` 튜플

**특징**:
- 타임스탬프 = `(l, c)` — l: 논리 physical time, c: 동률 카운터
- 로컬: `l_new = max(l, pt_now)`, `pt_now > l` 면 `c=0`, 아니면 `c++`
- 수신: `l = max(l, l_recv, pt_now)`, c 는 적절히 증가
- 64-bit 표현 가능: 상위 48bit physical (ms), 하위 16bit logical
- 시계 drift 가 작으면 wall clock 과 거의 동일

**장점**:
- 인과 관계 보존 (Lamport 성질)
- 사람에게 친숙한 timestamp (대략 NTP 시간)
- 분산 SQL/snapshot isolation 에 적합
- 64-bit 1개로 표현 가능 → vector clock 보다 가벼움

**단점**:
- 시계 drift 가 너무 크면 logical 성분이 비대화
- NTP 동기화 가정에 의존
- 인과 충분 조건은 아님 (vector clock 필요시 별도)

**활용 예시**:
- **CockroachDB** — distributed SQL 의 transaction timestamp 핵심
- YugabyteDB
- MongoDB cluster time ($clusterTime)
- TrueTime 대안 (Google Spanner 의 GPS/atomic clock 없이)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
data class HLCTimestamp(val l: Long, val c: Int) : Comparable<HLCTimestamp> {
    override fun compareTo(other: HLCTimestamp): Int =
        compareValuesBy(this, other, { it.l }, { it.c })

    fun toLong(): Long = (l shl 16) or (c.toLong() and 0xFFFF)
}

class HybridLogicalClock(private val physicalNow: () -> Long /* ms */) {
    private var l: Long = 0
    private var c: Int = 0

    @Synchronized
    fun now(): HLCTimestamp {
        val pt = physicalNow()
        val oldL = l
        l = maxOf(oldL, pt)
        c = if (l == oldL) c + 1 else 0
        return HLCTimestamp(l, c)
    }

    @Synchronized
    fun update(recv: HLCTimestamp): HLCTimestamp {
        val pt = physicalNow()
        val oldL = l
        l = maxOf(oldL, recv.l, pt)
        c = when (l) {
            oldL, recv.l -> {
                if (l == oldL && l == recv.l) maxOf(c, recv.c) + 1
                else if (l == oldL) c + 1
                else recv.c + 1
            }
            else -> 0
        }
        return HLCTimestamp(l, c)
    }
}

// 의사코드 - CockroachDB 사용:
//   txn.timestamp = hlc.now()
//   read(key) → 반환된 row 의 HLC 가 txn.timestamp 보다 작으면 visible
//   commit 시 HLC update — 다른 노드에서 받은 응답의 HLC 와 max
//   uncertainty interval = pt + max_clock_skew, 이 구간 내 row 발견 시 restart
```

**관련 알고리즘**: Lamport Clock, Vector Clock, TrueTime, Spanner timestamp

---

<a id="gossip-protocol"></a>
## 4. Gossip Protocol (가십 프로토콜)

**목적**: 노드들이 무작위 peer 와 정보를 교환하여 클러스터 전체에 epidemic(전염병)처럼 정보를 전파

**시간 복잡도**: O(log N) round 로 전 노드 도달 (N = 노드 수)

**공간 복잡도**: O(N) 노드별 멤버십/상태 view

**특징**:
- 주기적으로 random peer 1~3 명 선택 후 상태 교환
- 변형: Push / Pull / Push-Pull
- 수렴(convergence): 지수적으로 빠름
- 비동기, 분산, 부분 장애에 내성
- 노드 추가/제거 자체도 gossip 으로 전파

**장점**:
- 단순 + scale-out 우수 (수천 노드)
- 단일 실패점 없음
- 부분 네트워크 분할에 강함
- 평균 부하 균등 분산

**단점**:
- 강한 일관성 없음 (eventually consistent)
- 수렴까지 시간차 발생
- 대역폭 낭비 가능 (anti-entropy 와 결합 필요)
- 메시지 순서 보장 없음

**활용 예시**:
- **Amazon Dynamo / DynamoDB** — 멤버십, partition map
- **Apache Cassandra** — cluster state, schema
- Consul / Serf — service catalog
- Redis Cluster — cluster bus

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
data class NodeState(
    val nodeId: String,
    val heartbeat: Long,
    val version: Long, // HLC 또는 vector clock 가능
    val payload: Map<String, String>
)

class GossipNode(
    val nodeId: String,
    private val peers: List<String>,
    private val send: (peer: String, view: Map<String, NodeState>) -> Map<String, NodeState>
) {
    private val view = ConcurrentHashMap<String, NodeState>()

    fun start(intervalMs: Long = 1000L) = thread {
        while (!Thread.interrupted()) {
            tick()
            Thread.sleep(intervalMs)
        }
    }

    private fun tick() {
        // 자기 heartbeat 증가
        view.compute(nodeId) { _, s ->
            (s ?: NodeState(nodeId, 0, 0, emptyMap()))
                .copy(heartbeat = System.currentTimeMillis())
        }

        // 무작위 peer 1명 선택 (push-pull)
        val peer = peers.random()
        val incoming = send(peer, view.toMap())
        merge(incoming)
    }

    private fun merge(incoming: Map<String, NodeState>) {
        for ((id, s) in incoming) {
            view.merge(id, s) { old, new ->
                if (new.version > old.version) new else old
            }
        }
    }
}

// 의사코드 - epidemic 변형:
//   Push:      random peer 에게 내 view 보내고 끝
//   Pull:      random peer 에게서 view 가져옴
//   Push-Pull: 양방향 — 가장 빠른 수렴 (O(log N))
//
// Dynamo / Cassandra:
//   gossip round = 1초
//   3개 peer 선택 (live, unreachable, seed 비율)
//   accrual failure detector 와 결합 → suspect 판단
```

**관련 알고리즘**: SWIM, Anti-Entropy, Epidemic Broadcast Trees

---

<a id="swim"></a>
## 5. SWIM (Scalable Weakly-consistent Infection-style Membership)

**목적**: 대규모 클러스터에서 멤버십 관리 + 장애 감지를 분리해 scalable 하게 처리

**시간 복잡도**: O(1) per ping/round (멤버 수에 무관한 detection time)

**공간 복잡도**: O(N) 멤버 리스트

**특징**:
- 두 컴포넌트 분리: **Failure Detection** + **Membership Dissemination**
- 매 protocol period 마다 random peer 1명을 ping
- 직접 ping 실패 → 다른 k 명에게 indirect ping 요청 (네트워크 일시 장애 false positive 감소)
- 멤버십 변경(alive/suspect/dead)은 piggyback gossip 으로 전파
- Suspicion mechanism — dead 판정 전 grace period

**장점**:
- detection time 이 클러스터 크기에 무관 (O(1) — gossip 은 O(log N))
- 일시 네트워크 장애에 강함 (indirect ping)
- 메시지 비용 노드당 일정
- Hashicorp Serf / memberlist / Consul 검증된 구현

**단점**:
- weakly consistent — 일시적 split-brain view 가능
- piggyback 크기 제한 (UDP MTU 등)
- 네트워크 파티션 전체에는 어쩔 수 없음

**활용 예시**:
- **HashiCorp Serf / memberlist** — Consul, Nomad, Vault 의 클러스터 코어
- **Hazelcast** — IMDG cluster discovery
- Uber Ringpop
- ScyllaDB

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
enum class MemberStatus { ALIVE, SUSPECT, DEAD }
data class Member(val id: String, val addr: String, var status: MemberStatus, var inc: Long)

class SwimNode(
    val self: Member,
    private val members: MutableMap<String, Member>,
    private val k: Int = 3,                  // indirect ping fan-out
    private val periodMs: Long = 1000L,
    private val suspectTimeoutMs: Long = 5000L
) {
    private val rng = java.util.Random()

    fun protocolPeriod() {
        val target = pickRandomAlive() ?: return
        if (directPing(target)) {
            markAlive(target)
        } else {
            // indirect ping via k random peers
            val helpers = pickRandomAlive(k, exclude = setOf(target.id))
            val ack = helpers.any { indirectPing(via = it, target = target) }
            if (ack) markAlive(target) else markSuspect(target)
        }
        disseminate() // piggyback 멤버십 업데이트
    }

    private fun markSuspect(m: Member) {
        m.status = MemberStatus.SUSPECT
        scheduleSuspectTimeout(m, suspectTimeoutMs) {
            if (m.status == MemberStatus.SUSPECT) m.status = MemberStatus.DEAD
        }
    }

    // 의사코드 직접 호출부는 생략 — 핵심은 incarnation 기반 충돌 해소
    private fun directPing(m: Member): Boolean = TODO()
    private fun indirectPing(via: Member, target: Member): Boolean = TODO()
    private fun pickRandomAlive(n: Int = 1, exclude: Set<String> = emptySet()): List<Member> = TODO()
    private fun pickRandomAlive(): Member? = pickRandomAlive(1).firstOrNull()
    private fun markAlive(m: Member) { m.status = MemberStatus.ALIVE }
    private fun disseminate() { /* piggyback 정보 갱신 */ }
    private fun scheduleSuspectTimeout(m: Member, ms: Long, action: () -> Unit) {}
}

// 의사코드 - incarnation 기반 refute:
//   각 노드는 자신의 incarnation 번호 보관
//   다른 노드가 자신을 SUSPECT 라고 전파 → 자신 incarnation++ 후 ALIVE 반박 gossip
//   더 높은 incarnation 가진 정보가 항상 이김
```

**관련 알고리즘**: Gossip Protocol, Phi Accrual Failure Detector, Heartbeat

---

<a id="anti-entropy"></a>
## 6. Anti-Entropy (안티엔트로피, Merkle 트리 기반 sync)

**목적**: 두 replica 간 데이터 차이를 효율적으로 찾아 동기화 (eventual consistency 의 후속 수렴)

**시간 복잡도**: O(diff · log N), N = 데이터 항목 수, diff = 차이 항목 수

**공간 복잡도**: O(N) Merkle tree

**특징**:
- 키 공간을 segment(range)로 분할
- 각 segment 의 hash 를 leaf 로 Merkle tree 구성
- 두 노드가 root hash 비교 → 다르면 children 비교 → 차이 segment 까지 내려감
- 실제 데이터 동기화는 차이 segment 만 전송
- Read Repair / Hinted Handoff 와 함께 Dynamo 의 일관성 메커니즘

**장점**:
- 큰 데이터셋에서도 작은 네트워크 비용
- offline → online 복귀 노드 재동기화에 적합
- gossip 의 보완재 (gossip 은 변경 알림, anti-entropy 는 손실 복구)

**단점**:
- Merkle tree 유지 비용 (insert/update 시 leaf-to-root 갱신)
- range scan / tree rebuild 부담
- key 분포가 균등하지 않으면 효율 저하

**활용 예시**:
- **Apache Cassandra** — nodetool repair 의 핵심
- **Riak** — active anti-entropy (AAE)
- DynamoDB
- IPFS, BitTorrent 의 verification (개념적 유사)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.security.MessageDigest

class MerkleTree(private val segments: List<ByteArray>) {
    val root: Node
    sealed class Node(val hash: ByteArray) {
        class Leaf(val segmentId: Int, hash: ByteArray) : Node(hash)
        class Branch(val left: Node, val right: Node, hash: ByteArray) : Node(hash)
    }

    init { root = build(segments.indices.toList()) }

    private fun build(ids: List<Int>): Node {
        if (ids.size == 1) {
            val id = ids[0]
            return Node.Leaf(id, sha256(segments[id]))
        }
        val mid = ids.size / 2
        val l = build(ids.subList(0, mid))
        val r = build(ids.subList(mid, ids.size))
        return Node.Branch(l, r, sha256(l.hash + r.hash))
    }

    private fun sha256(bytes: ByteArray): ByteArray =
        MessageDigest.getInstance("SHA-256").digest(bytes)
}

// 의사코드 - 두 replica 동기화:
//   fun diff(a: MerkleTree.Node, b: MerkleTree.Node): List<Int> {
//       if (a.hash contentEquals b.hash) return emptyList()
//       if (a is Leaf && b is Leaf) return listOf(a.segmentId)
//       return diff(a.left, b.left) + diff(a.right, b.right)
//   }
//
// Cassandra repair:
//   1. 모든 노드가 token range 별 Merkle tree 빌드
//   2. coordinator 가 트리들을 받아 root 부터 비교
//   3. 불일치 leaf 의 row 들만 stream
//   4. read-repair / hinted-handoff 가 짧은 윈도우의 결손을 메우고,
//      anti-entropy 가 긴 윈도우의 결손을 메움
```

**관련 알고리즘**: Gossip Protocol, Read Repair, Hinted Handoff, Bloom Filter

---

<a id="crdt-g-counter"></a>
## 7. CRDT - G-Counter (Grow-only Counter, G-카운터)

**목적**: 증가만 가능한 분산 카운터. 충돌 없이 모든 replica 가 결정적으로 수렴

**시간 복잡도**: O(N) merge, N = replica 수

**공간 복잡도**: O(N) per replica

**특징**:
- 각 replica i 는 벡터 `P[]` 보관, `P[i]` 만 자기가 증가
- value = Σ P[k] for all k
- merge: 두 벡터 원소별 max
- 상태 기반 CRDT (state-based, CvRDT)
- 멱등(idempotent), 가환(commutative), 결합(associative)

**장점**:
- 동시 increment 손실 없음
- 네트워크 분할 후 자동 수렴
- 단순 구현
- LWW 카운터의 문제(write 손실) 회피

**단점**:
- 감소 불가 (PN-Counter 필요)
- replica ID 별 슬롯 → 동적 멤버십 추가 시 관리 필요
- O(N) 공간

**활용 예시**:
- 페이지뷰 / like / 조회수 분산 집계
- Riak Counter (deprecated → Datatypes)
- Redis CRDT (Enterprise)
- 분산 메트릭 합산

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class GCounter(val replicaId: String) {
    private val p = mutableMapOf<String, Long>()

    fun increment(amount: Long = 1) {
        require(amount > 0) { "G-Counter 는 증가만 가능" }
        p[replicaId] = (p[replicaId] ?: 0L) + amount
    }

    fun value(): Long = p.values.sum()

    fun merge(other: GCounter): GCounter {
        val merged = GCounter(replicaId)
        val keys = p.keys union other.p.keys
        for (k in keys) {
            merged.p[k] = maxOf(p[k] ?: 0L, other.p[k] ?: 0L)
        }
        return merged
    }

    fun snapshot(): Map<String, Long> = p.toMap()
}

// 의사코드 - 수렴 증명 스케치:
//   merge 는 max(commutative, associative, idempotent) 기반
//   → join-semilattice 형성
//   → 어떤 순서로 merge 해도 같은 결과로 수렴 (Strong Eventual Consistency)
//
// 예시:
//   A: increment 1 → P_A = {A:1}
//   B: increment 1 → P_B = {B:1}
//   A.merge(B) = {A:1, B:1}, value = 2
//   B.merge(A) = {A:1, B:1}, value = 2  (대칭, 결정적)
```

**관련 알고리즘**: PN-Counter, OR-Set, LWW-Set, Version Vector

---

<a id="crdt-pn-counter"></a>
## 8. CRDT - PN-Counter (Positive-Negative Counter, PN-카운터)

**목적**: 증가와 감소가 모두 가능한 분산 카운터

**시간 복잡도**: O(N) merge

**공간 복잡도**: O(N) — P 벡터 + N 벡터

**특징**:
- 두 G-Counter 결합: P (증가용) + N (감소용)
- value = ΣP[k] - ΣN[k]
- increment → P[i]++, decrement → N[i]++
- merge: 두 G-Counter 를 각각 merge

**장점**:
- 증가/감소 모두 충돌 없이 수렴
- 음수 가능
- 분산 잔액(balance) 형 데이터에 적합

**단점**:
- 음수 방지(잔액 0 미만 금지) 같은 제약 표현 불가 → 별도 로직 필요
- O(2N) 공간
- 인과 정보 없음

**활용 예시**:
- 분산 inventory count
- 좋아요 + 싫어요 분산 집계
- 멀티-DC 카운터 (좋아요 취소 포함)
- Akka Distributed Data PNCounter

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class PNCounter(val replicaId: String) {
    private val p = GCounter(replicaId) // positive
    private val n = GCounter(replicaId) // negative

    fun increment(amount: Long = 1) = p.increment(amount)
    fun decrement(amount: Long = 1) = n.increment(amount)

    fun value(): Long = p.value() - n.value()

    fun merge(other: PNCounter): PNCounter {
        val merged = PNCounter(replicaId)
        // p, n 각각 G-Counter merge
        val pm = p.merge(other.p)
        val nm = n.merge(other.n)
        for ((k, v) in pm.snapshot()) merged.p.snapshot() // 의사 — 실제 구현은 내부 상태 직접 복사
        return merged
    }
}

// 의사코드 - 음수 잔액 방어:
//   PNCounter 자체로는 잔액 음수 막을 수 없음 (분산 트랜잭션 필요)
//   해법:
//     1. 강한 일관성이 필요한 경계만 별도 처리 (synchronous lock / Raft)
//     2. eventual consistency 허용 + 사후 보정 (refund)
//     3. Bounded CRDT (escrow 기법)
//
// Akka Distributed Data 예시:
//   replicator ! Update(key, PNCounter(), WriteLocal) { _.increment(node, 1) }
```

**관련 알고리즘**: G-Counter, OR-Set, Bounded Counter

---

<a id="crdt-or-set"></a>
## 9. CRDT - OR-Set (Observed-Remove Set, OR-셋)

**목적**: 원소 추가/삭제가 모두 가능하고, "add 가 concurrent remove 를 이긴다(add-wins)"는 직관에 맞는 집합 CRDT

**시간 복잡도**: O(M) merge, M = 원소 + tombstone 수

**공간 복잡도**: O(M) — 각 add 마다 unique tag

**특징**:
- 각 add 에 unique tag(예: UUID, (replica, counter)) 부여
- remove 는 자신이 "본(observed)" tag 들만 제거
- merge: tag 집합의 union (add) ⊟ removed tag 집합
- 같은 원소를 concurrent 하게 add + remove 시 add 가 살아남음 (서로 본 적 없으므로)

**장점**:
- 직관적 add-wins 의미론
- LWW-Set 보다 데이터 손실 적음
- 분산 셋의 표준 CRDT

**단점**:
- tag 누적 (tombstone 포함) → 공간 비용 증가
- 주기적 garbage collection 필요
- Causal stability 없으면 GC 어려움

**활용 예시**:
- Riak Set datatype
- Redis CRDT Sets
- 협업 앱의 친구 목록 / 태그
- 분산 feature flag set

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
data class Tag(val replicaId: String, val counter: Long)

class ORSet<E>(val replicaId: String) {
    private val elements = mutableMapOf<E, MutableSet<Tag>>() // value -> tags
    private val tombstones = mutableMapOf<E, MutableSet<Tag>>() // removed tags
    private var counter: Long = 0

    fun add(e: E) {
        counter += 1
        val tag = Tag(replicaId, counter)
        elements.getOrPut(e) { mutableSetOf() }.add(tag)
    }

    fun remove(e: E) {
        val observed = elements[e]?.toSet() ?: return
        tombstones.getOrPut(e) { mutableSetOf() }.addAll(observed)
        // 즉시 제거는 안 함 — merge 후 effective subtract
    }

    fun contains(e: E): Boolean {
        val live = elements[e] ?: return false
        val dead = tombstones[e] ?: emptySet()
        return (live - dead).isNotEmpty()
    }

    fun value(): Set<E> =
        elements.entries
            .filter { (e, _) -> contains(e) }
            .map { it.key }
            .toSet()

    fun merge(other: ORSet<E>): ORSet<E> {
        val merged = ORSet<E>(replicaId)
        val keys = elements.keys union other.elements.keys
        for (k in keys) {
            merged.elements[k] = ((elements[k] ?: emptySet()) union (other.elements[k] ?: emptySet())).toMutableSet()
            merged.tombstones[k] = ((tombstones[k] ?: emptySet()) union (other.tombstones[k] ?: emptySet())).toMutableSet()
        }
        return merged
    }
}

// 의사코드 - add-wins:
//   A: add(x) → tag(A,1)
//   B: receives, then B.remove(x) — 본 tag = {(A,1)} → tombstone {(A,1)}
//   A: 동시에 add(x) → tag(A,2)
//   merge 후: live = {(A,1),(A,2)}, dead = {(A,1)} → (A,2) 살아있음 → x 존재
```

**관련 알고리즘**: 2P-Set, LWW-Set, Add-Wins Map, RGA

---

<a id="crdt-lww-set"></a>
## 10. CRDT - LWW-Set (Last-Writer-Wins Set, LWW-셋)

**목적**: timestamp 기반으로 add/remove 충돌을 해결하는 셋 CRDT

**시간 복잡도**: O(1) per op, O(M) merge

**공간 복잡도**: O(M) — 원소별 최근 timestamp 보관

**특징**:
- 각 원소에 두 timestamp: addTs, removeTs (또는 (op, ts) 쌍)
- contains: `addTs > removeTs`
- merge: 원소별 max timestamp 채택
- timestamp 동률 시 결정적 tiebreak (replicaId)
- HLC / Vector Clock 기반이면 인과 보존

**장점**:
- 매우 단순, 메모리 효율 우수
- garbage collection 쉬움 (timestamp 비교만)
- DynamoDB / Cassandra 의 LWW 모델과 호환

**단점**:
- 동시 add/remove 시 한 쪽 손실 (OR-Set 보다 정보량 적음)
- wall-clock 사용 시 clock skew 위험
- "정답"이 직관과 다를 수 있음

**활용 예시**:
- DynamoDB / Cassandra 의 cell-level LWW
- Redis CRDT (특정 데이터타입)
- 캐시 invalidation set
- 단순 분산 set 가 데이터 손실 허용 시

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class LWWSet<E>(val replicaId: String, private val now: () -> Long) {
    data class Stamp(val ts: Long, val replicaId: String) : Comparable<Stamp> {
        override fun compareTo(other: Stamp): Int =
            compareValuesBy(this, other, { it.ts }, { it.replicaId })
    }

    private val addSet = mutableMapOf<E, Stamp>()
    private val removeSet = mutableMapOf<E, Stamp>()

    fun add(e: E) {
        val s = Stamp(now(), replicaId)
        addSet.merge(e, s) { a, b -> if (a > b) a else b }
    }

    fun remove(e: E) {
        val s = Stamp(now(), replicaId)
        removeSet.merge(e, s) { a, b -> if (a > b) a else b }
    }

    fun contains(e: E): Boolean {
        val a = addSet[e] ?: return false
        val r = removeSet[e] ?: return true
        return a > r // 동률 시 false (remove-wins) 또는 true (add-wins) — 정책 선택
    }

    fun value(): Set<E> = addSet.keys.filter { contains(it) }.toSet()

    fun merge(other: LWWSet<E>): LWWSet<E> {
        val merged = LWWSet<E>(replicaId, now)
        for ((e, s) in addSet + other.addSet) {
            merged.addSet.merge(e, s) { a, b -> if (a > b) a else b }
        }
        for ((e, s) in removeSet + other.removeSet) {
            merged.removeSet.merge(e, s) { a, b -> if (a > b) a else b }
        }
        return merged
    }
}

// 의사코드 - clock skew 주의:
//   wall clock 사용 시 노드 간 시계 차이만큼 결과 흔들림
//   → HLC 사용 권장: Stamp = HLCTimestamp
//   → 인과 위반(causal violation) 차단
```

**관련 알고리즘**: OR-Set, 2P-Set, HLC, Version Vector

---

<a id="consistent-hashing"></a>
## 11. Consistent Hashing (일관 해싱, with virtual nodes)

**목적**: 노드 추가/제거 시 재배치되는 키를 최소화하는 분산 해시 분배

**시간 복잡도**: O(log N) lookup (TreeMap), O(K/N) 재배치

**공간 복잡도**: O(N · V) — V = virtual node 수 per node

**특징**:
- 키와 노드를 모두 같은 해시 링(0 ~ 2^m) 에 매핑
- 키는 시계방향으로 가장 가까운 노드에 할당
- 노드 추가/제거 시 인접 구간의 키만 이동 (`K/N` 평균)
- virtual node — 한 물리 노드를 여러 가상 점에 매핑 → 부하 균등 + 이종 노드 가중치 표현
- 해시 함수: MurmurHash3, xxHash, MD5(Cassandra)

**장점**:
- 노드 추가/제거 비용 최소 (`O(K/N)`)
- replica 배치(N+1, N+2, …) 자연스러움
- 멤버십 변경 시 client 재시작 불필요
- virtual node 로 hot-spot 완화

**단점**:
- 데이터 분포 편향 → virtual node 필수
- 인접 노드 정보 필요 (gossip 과 결합)
- 매우 큰 클러스터에서는 jump hash / rendezvous hash 보다 무거움

**활용 예시**:
- **Amazon Dynamo / DynamoDB** — partitioning
- **Apache Cassandra** — token ring
- Memcached / Redis client-side sharding
- CDN edge 노드 라우팅 (Akamai, Cloudflare)
- gRPC load balancing (ring hash policy)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
class ConsistentHashRing<N : Any>(
    private val virtualNodes: Int = 150,
    private val hash: (String) -> Long = { it.hashCode().toLong() and 0xFFFFFFFFL }
) {
    private val ring = java.util.TreeMap<Long, N>()
    private val physical = mutableMapOf<N, List<Long>>()

    fun addNode(node: N, id: String, weight: Int = 1) {
        val tokens = (0 until virtualNodes * weight).map { hash("$id#$it") }
        physical[node] = tokens
        tokens.forEach { ring[it] = node }
    }

    fun removeNode(node: N) {
        physical.remove(node)?.forEach { ring.remove(it) }
    }

    fun route(key: String): N? {
        if (ring.isEmpty()) return null
        val h = hash(key)
        val entry = ring.ceilingEntry(h) ?: ring.firstEntry()
        return entry.value
    }

    fun routeN(key: String, n: Int): List<N> {
        val result = mutableListOf<N>()
        if (ring.isEmpty()) return result
        var cur = hash(key)
        while (result.size < n && result.size < physical.size) {
            val entry = ring.ceilingEntry(cur) ?: ring.firstEntry()
            if (entry.value !in result) result.add(entry.value)
            cur = entry.key + 1
        }
        return result
    }
}

// 의사코드 - replication:
//   primary = route(key)
//   replicas = routeN(key, N) — 시계방향으로 N개 (Dynamo 의 preference list)
//   같은 rack/AZ 회피 옵션은 후처리 필터로 적용
```

**관련 알고리즘**: Rendezvous Hashing (HRW), Jump Hash, Maglev Hash, Range Partitioning

---

<a id="quorum"></a>
## 12. Quorum (R+W>N, 쿼럼; Sloppy Quorum, Read Repair)

**목적**: 분산 replica 들 중 일부만 응답해도 강한 일관성을 보장하는 read/write 정책

**시간 복잡도**: O(max(R,W)) round trip

**공간 복잡도**: O(N) — N replica

**특징**:
- N = replica 수, R = read 쿼럼, W = write 쿼럼
- `R + W > N` ⇒ read 와 write 집합이 반드시 겹침 → 최신 데이터 1개 이상 포함
- `W > N/2` ⇒ write 충돌 방지
- **Strict Quorum** — N 안에서만 응답 인정
- **Sloppy Quorum** — 일부 replica 다운 시 다른 노드가 임시 대신 받음 (hinted handoff 로 복구)
- **Read Repair** — read 시 stale replica 발견하면 비동기로 최신 값 전파

**장점**:
- 일관성/가용성/지연 간 trade-off 를 R, W 로 조절
- 강한 일관성 (R+W>N) 또는 빠른 응답 (R=W=1) 선택 가능
- Sloppy quorum + hinted handoff 로 가용성 향상

**단점**:
- R+W>N 만으로 linearizability 미보장 (Cassandra 사례, 별도 LWT 필요)
- Sloppy quorum 은 일관성 약화 가능
- 응답 대기 시간 = 가장 느린 R 또는 W replica

**활용 예시**:
- **Amazon Dynamo / DynamoDB** — N=3, W=2, R=2 표준
- **Apache Cassandra** — ONE / QUORUM / ALL consistency level
- **Riak** — N=3, configurable R/W
- Etcd / Raft (다른 의미의 quorum — 강 일관)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
data class ReplicaResponse<V>(val nodeId: String, val value: V?, val version: VectorClock)

class QuorumClient<K, V>(
    private val replicas: List<String>,
    private val n: Int,
    private val r: Int,
    private val w: Int,
    private val sendWrite: (node: String, key: K, value: V, ctx: VectorClock) -> Boolean,
    private val sendRead:  (node: String, key: K) -> ReplicaResponse<V>?
) {
    init {
        require(r + w > n) { "R+W>N 위반 — 강한 일관성 보장 불가" }
        require(w > n / 2) { "W>N/2 위반 — write 충돌 가능" }
    }

    fun put(key: K, value: V, ctx: VectorClock): Boolean {
        val acks = replicas.parallelStream()
            .map { sendWrite(it, key, value, ctx) }
            .filter { it }
            .count()
        return acks >= w
    }

    fun get(key: K): V? {
        val responses = replicas.parallelStream()
            .map { sendRead(it, key) }
            .filter { it != null }
            .toList()
            .filterNotNull()
        if (responses.size < r) return null // 쿼럼 미달

        // version 으로 최신 선택, stale 발견 시 비동기 read-repair
        val newest = responses.maxByOrNull { it.version.compare(VectorClock()).ordinal } ?: return null
        val stale = responses.filter { it.version != newest.version }
        if (stale.isNotEmpty()) launchReadRepair(key, newest)
        return newest.value
    }

    private fun launchReadRepair(key: K, newest: ReplicaResponse<V>) { /* async */ }
}

// 의사코드 - Sloppy Quorum:
//   원래 preference list [A, B, C] 중 C 다운
//   → C 대신 D 가 hinted handoff 로 임시 수신
//   C 복귀 시 D 가 hint 전달 → C 가 적용
//   장점: 가용성↑    단점: 일관성 약화 가능
```

**관련 알고리즘**: Read Repair, Hinted Handoff, Paxos, Raft (Strong Quorum)

---

<a id="chandy-lamport"></a>
## 13. Chandy-Lamport Distributed Snapshot (찬디-램포트 분산 스냅샷)

**목적**: 실행을 멈추지 않고 분산 시스템의 일관된 전역 상태(consistent global state) — 각 프로세스 상태 + 각 채널의 in-flight 메시지 — 를 기록한다

**시간 복잡도**: O(E) 메시지 — 각 채널(방향)당 marker 1회 전송 (E = 채널 수)

**공간 복잡도**: O(P + M) — P개 프로세스 상태 + 채널에 기록되는 in-flight 메시지 M개

**특징**:
- Chandy & Lamport, 1985 (ACM TOCS) 제안. FIFO 신뢰 채널을 가정한다
- 임의의 프로세스가 자신의 상태를 기록한 뒤 모든 나가는 채널로 marker를 보내며 스냅샷을 개시(initiate)
- 어떤 채널 c에서 marker를 처음 받으면 c의 채널 상태를 "빈 집합"으로 확정하고, 자신 상태를 기록한 뒤 모든 나가는 채널로 marker 전달
- 이미 자신 상태를 기록한 후 채널 c에서 marker를 받으면, 그 채널의 상태 = (상태 기록 시점 ~ marker 도착 사이에 c로 들어온 메시지들)로 확정
- 결과 스냅샷은 실제 한 순간엔 없었을 수 있으나 어떤 일관된 실행과 구분 불가(consistent cut)하다 — 인과 순서를 위배하지 않음

**장점**:
- 정상 연산을 중단(stop-the-world)하지 않고 동시에 스냅샷 수집 가능
- 메시지 오버헤드가 채널 수에 선형(O(E))으로 가볍다
- 여러 프로세스가 독립적으로 동시에 개시해도 동작 (단일 코디네이터 불필요)

**단점**:
- FIFO 채널 가정 필수 — 비-FIFO/메시지 유실 환경에선 그대로 적용 불가
- 채널·프로세스 장애(crash)나 동적 토폴로지를 기본형은 다루지 못함
- 강연결(모든 프로세스 도달 가능) 가정이 깨지면 일부 프로세스가 marker를 못 받아 스냅샷 미완성

**활용 예시**:
- 분산 체크포인트/복구 (예: Apache Flink의 비동기 배리어 스냅샷이 변형 채택)
- 안정 속성(stable property) 탐지 — 분산 데드락 탐지, 종료(termination) 탐지, 가비지 컬렉션
- 분산 디버깅·전역 불변식 검사용 일관된 상태 캡처

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// 단일 프로세스 노드의 Chandy-Lamport 스냅샷 로직 (FIFO 채널 가정)
class SnapshotNode(val id: Int, val outChannels: List<Int>) {
    var localState: String = "init"          // 기록될 프로세스 상태
    private var recorded = false              // 자신 상태 기록 여부
    private val markerSeen = mutableSetOf<Int>()              // marker 받은 채널
    private val channelState = mutableMapOf<Int, MutableList<String>>() // 채널별 기록 메시지
    private val recording = mutableSetOf<Int>()              // 현재 기록 중인 채널

    // marker를 모든 나가는 채널로 전송 (네트워크 계층은 외부에서 주입)
    fun recordOwnState(send: (to: Int, marker: Boolean, msg: String?) -> Unit) {
        localState = "snap@$id"              // 현재 상태 스냅샷
        recorded = true
        outChannels.forEach { c -> recording.add(c); send(c, true, null) }
    }

    // src 채널에서 marker 수신 처리
    fun onMarker(src: Int, send: (to: Int, marker: Boolean, msg: String?) -> Unit) {
        markerSeen.add(src)
        if (!recorded) {
            channelState[src] = mutableListOf()   // 이 채널은 빈 상태로 확정
            recordOwnState(send)                  // 첫 marker -> 자신 상태 기록 + 전파
        } else {
            recording.remove(src)                 // 이후 marker -> 해당 채널 기록 종료
        }
    }

    // src 채널에서 일반 메시지 수신 처리
    fun onMessage(src: Int, msg: String) {
        if (recorded && src in recording) {       // 상태 기록 후 ~ marker 전까지의 in-flight
            channelState.getOrPut(src) { mutableListOf() }.add(msg)
        }
        // 애플리케이션 메시지 처리는 별도로 계속 진행
    }

    fun isComplete() = recorded && recording.isEmpty()
    fun snapshot() = localState to channelState
}
```

**관련 알고리즘**: Lamport Timestamp, Vector Clock, Two-Phase Commit

---

<a id="phi-accrual"></a>
## 14. Phi Accrual Failure Detector (파이 누적 장애 감지기)

**목적**: heartbeat 도착 간격을 확률 분포로 모델링해 의심도 φ(연속값)를 산출, 노드 장애 여부를 적응적으로 판단

**시간 복잡도**: O(1) heartbeat 갱신 / O(1) φ 조회 (sliding window 통계 누적)

**공간 복잡도**: O(W) - W: 도착 간격 sampling window 크기

**특징**:
- 도착 간격(inter-arrival time)을 정규분포 등으로 모델링하고, 마지막 heartbeat 이후 경과 시간에 대한 미수신 확률 P_later 를 계산
- 의심도 φ = -log10(P_later) — 시간이 흐를수록 단조 증가하는 연속값 (binary up/down 대신 신뢰도 척도 제공)
- φ 가 임계값 Φ(threshold)를 넘으면 장애로 판정 — 애플리케이션이 false-positive 허용도에 맞춰 Φ 조정 가능
- 네트워크 지연 변동(jitter)에 적응 — 간격 분산이 크면 φ 가 천천히 상승해 자동으로 관대해짐
- Hayashibara et al. (2004) 제안, Akka Cluster·Apache Cassandra gossip 장애 감지에 채택

**장점**:
- adaptive threshold — 고정 타임아웃과 달리 실제 네트워크 상황(평균·분산)에 따라 민감도 자동 조정
- 연속값 φ 제공으로 애플리케이션마다 다른 신뢰-속도 트레이드오프 설정 가능
- accrual 설계상 감지 로직과 판정 정책(임계값) 분리 — 모니터링·해석이 용이

**단점**:
- 분포 가정(주로 정규/지수)이 실제 도착 패턴과 어긋나면 정확도 저하
- 초기 sample 부족 시 추정 불안정 — warm-up 구간 필요
- GC pause·일시적 전체 지연 시 동시 false-positive 위험 (window·Φ 튜닝 필요)

**활용 예시**:
- Akka Cluster 멤버십 장애 감지 (`akka.remote.PhiAccrualFailureDetector`)
- Apache Cassandra 노드 간 gossip 기반 장애 판정
- 분산 시스템 heartbeat 모니터링 일반
- 마이크로서비스 health-check 의 적응형 타임아웃

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.math.ln
import kotlin.math.sqrt
import kotlin.math.exp

// 도착 간격을 정규분포로 근사해 의심도 phi 를 산출하는 Phi Accrual 장애 감지기
class PhiAccrualFailureDetector(
    private val windowSize: Int = 1000,
    private val minStdMillis: Double = 100.0 // 분산 하한 (jitter 안전장치)
) {
    private val intervals = ArrayDeque<Double>()
    private var sum = 0.0
    private var sumSq = 0.0
    private var lastHeartbeatMillis = -1L

    // heartbeat 수신 시 호출 — 직전 수신과의 간격을 window 에 누적
    fun heartbeat(nowMillis: Long) {
        if (lastHeartbeatMillis >= 0) {
            val interval = (nowMillis - lastHeartbeatMillis).toDouble()
            intervals.addLast(interval); sum += interval; sumSq += interval * interval
            if (intervals.size > windowSize) {
                val old = intervals.removeFirst(); sum -= old; sumSq -= old * old
            }
        }
        lastHeartbeatMillis = nowMillis
    }

    // 경과 시간이 도착 간격 분포상 얼마나 비정상인지를 phi = -log10(P_later) 로 반환
    fun phi(nowMillis: Long): Double {
        if (lastHeartbeatMillis < 0 || intervals.isEmpty()) return 0.0
        val n = intervals.size
        val mean = sum / n
        val variance = (sumSq / n) - (mean * mean)
        val std = maxOf(sqrt(maxOf(variance, 0.0)), minStdMillis)
        val elapsed = (nowMillis - lastHeartbeatMillis).toDouble()
        val pLater = 1.0 - cdf(elapsed, mean, std) // 아직 미수신일 확률
        return -log10(maxOf(pLater, 1e-10))
    }

    fun isAvailable(nowMillis: Long, threshold: Double = 8.0): Boolean =
        phi(nowMillis) < threshold

    // 정규분포 누적분포함수 (로지스틱 근사)
    private fun cdf(x: Double, mean: Double, std: Double): Double {
        val y = (x - mean) / std
        return 1.0 / (1.0 + exp(-y * (1.5976 + 0.070566 * y * y)))
    }

    private fun log10(x: Double) = ln(x) / ln(10.0)
}
```

**관련 알고리즘**: SWIM (Gossip Failure Detection), Gossip Protocol, Heartbeat Failure Detector, Vector Clock
