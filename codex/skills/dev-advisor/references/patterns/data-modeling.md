# 데이터 일관성·복제·분산 패턴 (Data Consistency, Replication & Distribution Patterns)

분산 데이터 시스템의 정평 있는 12 패턴. Martin Kleppmann *Designing Data-Intensive Applications* (2017) 기반. **CAP/PACELC → Replication → Sharding → CDC → Materialized View → HTAP/Lambda/Kappa → Data Mesh** 의 진화.

**원전·표준 참고**:
- Martin Kleppmann — *Designing Data-Intensive Applications* (DDIA, 2017)
- Eric Brewer — "Towards Robust Distributed Systems" (PODC 2000) — CAP
- Daniel Abadi — "Consistency Tradeoffs in Modern Distributed Database System Design" (Computer 2012) — PACELC
- DeCandia et al. — *Dynamo: Amazon's Highly Available Key-value Store* (SOSP 2007)
- David Karger et al. — Consistent Hashing (STOC 1997)
- Nathan Marz — Lambda Architecture (2011)
- Jay Kreps — *Questioning the Lambda Architecture* (2014) — Kappa
- Zhamak Dehghani — *Data Mesh* (O'Reilly, 2022)

**의사결정 매트릭스 (CAP 선택)**:

| 시스템 | C | A | P | 사용처 |
|--------|---|---|---|--------|
| 단일 노드 RDBMS | O | O | X | OLTP 소규모 |
| PostgreSQL+Replica (sync) | O | △ | O (CP) | 금융 |
| MongoDB | △ | O | O | 일반 분산 |
| Cassandra / DynamoDB | △ (tunable) | O | O (AP) | 대규모 분산 |
| Spanner / CockroachDB | O | O | O (실용) | NewSQL |

**관련 카탈로그**:
- [distributed.md](distributed.md) — CQRS / Event Sourcing / Saga / Outbox (이미 있음)
- [`../principles/concurrency-theory.md`](../principles/concurrency-theory.md) — Linearizability / Serializability (이론 본체)
- [`../algorithms/distributed.md`](../algorithms/distributed.md) — Vector Clock / Gossip / Consistent Hashing
- [`../algorithms/db-storage-engines.md`](../../../data-advisor/references/algorithms/db-storage-engines.md) — WAL / Replication Log

**관련 원칙·거버넌스 (P0 신설)**:
- [`../principles/database-fundamentals.md`](../../../data-advisor/references/principles/db-fundamentals.md) — ACID/BASE · CAP/PACELC · 정규화 · 격리 수준 · 복제 · 일관성 모델 · 파티셔닝의 이론 기반 (Codd · Brewer · Abadi · Kleppmann)
- [`master-data-management.md`](../../../data-advisor/references/patterns/mdm.md) — 마스터 데이터 정합성: Golden Record · Match-Merge · Reference Data · Hierarchy (데이터 모델링의 거버넌스 보완)
- [`data-quality-governance.md`](../../../data-advisor/references/patterns/data-quality.md) — 데이터 품질 6 차원 · Data Lineage · OpenLineage · 카탈로그 · 스튜어드십 RACI (모델링 산출물에 적용)

---

<a id="cap-theorem"></a>

## 1. CAP Theorem (CAP 정리)

**정의**: Eric Brewer가 2000년 PODC 기조강연에서 제시하고 2002년 Gilbert & Lynch가 형식화한 정리. 분산 시스템은 **Consistency** (모든 노드가 같은 데이터를 본다), **Availability** (모든 요청은 응답 받는다), **Partition Tolerance** (네트워크 분할에도 동작한다) 세 가지를 동시에 만족할 수 없다. 실용적으로 P는 분산 시스템에서 선택이 아니라 필연이므로, **CP** (일관성 우선, 분할 시 응답 거부) vs **AP** (가용성 우선, 분할 시 불일치 허용) 의 양자택일이 된다.

**메커니즘**:
- **Consistency** — Linearizability 수준의 강한 일관성. 모든 읽기는 가장 최근 쓰기 결과를 본다
- **Availability** — 모든 살아있는 노드가 모든 요청에 (에러가 아닌) 응답을 한다
- **Partition Tolerance** — 메시지 손실/지연이 있어도 시스템이 계속 동작한다
- 분할 발생 시점에 C와 A 중 하나를 포기해야 한다 — 분할되지 않은 평상시에는 둘 다 가능

**장점**:
- 시스템 설계 의사결정의 명확한 프레임 (CP / AP 라벨링)
- "왜 우리는 강한 일관성을 못 가지나" 라는 질문에 답할 수 있음
- 데이터스토어 선택의 1차 필터

**단점·trade-off**:
- 분할 없는 정상 상태의 trade-off (지연 vs 일관성)는 표현하지 못함 — PACELC 가 보완 ([2번](#pacelc))
- C/A/P 정의가 단순화돼 실제 DB는 "tunable consistency" 같이 grayscale (Cassandra, DynamoDB)
- 2PC, Paxos, Raft 같이 동의 알고리즘으로 P 하에서 C 와 A 를 부분 만족할 수 있음 (실용적 회피)

**실제 DB/시스템**:
- **CP** — HBase, MongoDB (기본), Zookeeper, etcd, Redis Cluster (failover 중 unavailable)
- **AP** — Cassandra (default), DynamoDB, Riak, CouchDB
- **CA (분할 없는 단일 노드)** — 기존 단일 RDBMS (PostgreSQL/MySQL 단일 인스턴스)

**Kotlin / pseudo-code 예제**:
```kotlin
// CP 시스템: 쿼럼 미달 시 에러 (Availability 포기)
class CPStore(private val nodes: List<Node>, private val quorum: Int) {
    fun write(key: String, value: String): WriteResult {
        val acks = nodes.map { runCatching { it.write(key, value) } }
            .count { it.isSuccess }
        return if (acks >= quorum) WriteResult.Ok
               else WriteResult.Error("quorum lost — partition detected")
    }
}

// AP 시스템: 살아있는 노드는 무조건 응답 (Consistency 포기)
class APStore(private val nodes: List<Node>) {
    fun write(key: String, value: String): WriteResult {
        nodes.forEach { runCatching { it.write(key, value) } } // best-effort
        return WriteResult.Ok // 한 노드만 받아도 ack
    }
    // 나중에 Anti-Entropy / Read Repair 로 수렴
}
```

**관련 패턴**: [PACELC](#pacelc), [Consistency Models](#consistency-models-systems), [Leaderless Replication](#leaderless-replication)

---

<a id="pacelc"></a>

## 2. PACELC Theorem (PACELC 정리)

**정의**: Daniel Abadi 가 2010년 발표하고 2012년 *Computer* 지에서 형식화한 CAP 의 확장. **If Partition (P) → Availability (A) vs Consistency (C). Else (E) → Latency (L) vs Consistency (C)**. 분할 시의 trade-off (CAP) 만이 아니라, **분할 없는 정상 상태에서도 지연을 줄이려면 일관성을 약화해야 한다** 는 점을 명시한다.

**메커니즘**:
- **분할 발생 (P)** — A 와 C 중 선택 (CAP 와 동일)
- **분할 없음 (E)** — L (낮은 지연) 과 C (강한 일관성) 중 선택
- 동기 복제 (sync replication) = 높은 일관성 + 높은 지연
- 비동기 복제 (async replication) = 낮은 지연 + eventual consistency
- 4 사분면 분류 — **PA/EL**, **PA/EC**, **PC/EL**, **PC/EC**

**장점**:
- 정상 상태에서의 trade-off 도 명시 — 실제 시스템 운영에 더 가까움
- 분할이 드물어도 매 요청마다 발생하는 지연-일관성 trade-off 를 인지
- DB 분류가 더 정밀해짐

**단점·trade-off**:
- 4 사분면이 깔끔히 분리되지 않는 시스템 多 (tunable consistency 가 일반화)
- CAP 만큼 직관적이지 않아 도입 장벽 존재

**실제 DB/시스템**:
- **PA/EL** — Cassandra, DynamoDB, Riak — 항상 지연 최소화, 분할 시 가용성 우선
- **PC/EC** — HBase, Megastore, BigTable — 항상 일관성 우선
- **PA/EC** — MongoDB (configurable) — 정상 시 강일관성, 분할 시 가용성
- **PC/EL** — PNUTS (Yahoo) — 정상 시 지연 최소화, 분할 시 일관성

**Kotlin / pseudo-code 예제**:
```kotlin
// PA/EL 시스템 (Cassandra-style): 항상 한 노드에 쓰기만 성공하면 ack
class PA_EL_Store(private val nodes: List<Node>) {
    fun write(key: String, value: String): WriteResult {
        val first = nodes.firstOrNull { runCatching { it.write(key, value) }.isSuccess }
        return if (first != null) WriteResult.Ok else WriteResult.Error("no live node")
    }
}

// PC/EC 시스템 (HBase-style): 분할 없어도 모든 replica 동기 ack 필요
class PC_EC_Store(private val nodes: List<Node>) {
    fun write(key: String, value: String): WriteResult {
        val allAck = nodes.all { runCatching { it.write(key, value) }.isSuccess }
        return if (allAck) WriteResult.Ok
               else WriteResult.Error("at least one replica failed — consistency violated")
    }
}
```

**관련 패턴**: [CAP Theorem](#cap-theorem), [Consistency Models](#consistency-models-systems), [Single/Multi/Leaderless Replication](#single-leader-replication)

---

<a id="consistency-models-systems"></a>

## 3. Strong / Sequential / Causal / Eventual 일관성 모델 비교 (시스템 운영 관점)

**정의**: 분산 시스템이 보장하는 일관성 강도의 스펙트럼. 이론적 정의는 [`../principles/concurrency-theory.md`](../principles/concurrency-theory.md) 에 있고, 여기서는 **운영자가 어떤 보장을 선택할지** 의 관점에서 4 모델을 비교한다.

**메커니즘**:
- **Strong Consistency (Linearizability)** — 모든 연산이 단일 글로벌 순서로 보임. 합의 알고리즘 (Paxos, Raft) 필요
- **Sequential Consistency** — 각 클라이언트는 자신의 순서를 유지하고, 모든 클라이언트가 같은 글로벌 순서를 본다 (실시간 제약 없음)
- **Causal Consistency** — 인과 관계 (happens-before) 가 있는 연산만 순서가 보장됨. 동시 연산은 다른 순서로 보일 수 있음. CRDT, Vector Clock 기반
- **Eventual Consistency** — 쓰기가 멈추면 결국 모든 replica 가 수렴. 그 사이의 순서/시점은 보장 없음

**장점·trade-off 매트릭스**:

| 모델 | 지연 | 가용성 | 구현 비용 | 사용처 |
|------|------|--------|-----------|--------|
| Strong | 높음 (cross-region RT) | 분할 시 부분 unavailable | 합의 알고리즘 필수 | 금융 거래, 재고 |
| Sequential | 중간 | 좋음 | 글로벌 시퀀서 / 토큰 | 게임 리더보드 |
| Causal | 낮음 | 매우 좋음 | Vector Clock / dependency tracking | SNS 피드, 댓글 |
| Eventual | 매우 낮음 | 최고 | gossip / anti-entropy | DNS, 카운터 |

**구현 메커니즘**:
- **Strong** — Spanner (TrueTime + Paxos), CockroachDB (HLC + Raft), etcd / Zookeeper (Raft / Zab)
- **Sequential** — Kafka 단일 파티션, Redis 단일 인스턴스
- **Causal** — COPS, Eiger, Riak (causal context), Bayou
- **Eventual** — Cassandra (default), DynamoDB, Amazon S3 (구버전), CouchDB

**Kotlin 예제 (Causal Consistency with Vector Clock)**:
```kotlin
data class VectorClock(val nodeId: String, val counts: Map<String, Long>) {
    fun increment() = copy(counts = counts + (nodeId to (counts[nodeId] ?: 0L) + 1))
    fun happensBefore(other: VectorClock): Boolean =
        counts.all { (k, v) -> v <= (other.counts[k] ?: 0L) } && this != other
}

class CausalStore(private val nodeId: String) {
    private var clock = VectorClock(nodeId, emptyMap())
    private val log = mutableListOf<Pair<VectorClock, String>>()

    fun write(value: String): VectorClock {
        clock = clock.increment()
        log += clock to value
        return clock
    }

    fun read(after: VectorClock): List<String> =
        log.filter { (vc, _) -> after.happensBefore(vc) || vc == after }
           .map { it.second }
}
```

**관련 패턴**: [CAP](#cap-theorem), [PACELC](#pacelc), [Leaderless Replication](#leaderless-replication), [`../principles/concurrency-theory.md`](../principles/concurrency-theory.md)

---

<a id="single-leader-replication"></a>

## 4. Single-Leader Replication (단일 리더 복제)

**정의**: 한 노드가 leader (primary, master) 로 지정되어 모든 쓰기를 받고, follower (replica, secondary) 들에게 변경 로그를 전파하는 가장 보편적인 복제 방식. PostgreSQL streaming replication, MySQL binlog replication, MongoDB replica set, Kafka partition leader 등이 모두 이 구조다.

**메커니즘**:
- **쓰기** — 모두 leader 로 전송. leader 는 local WAL/binlog 에 기록 후 follower 들에게 log shipping
- **읽기** — leader 또는 follower 에서. follower 읽기는 read-your-writes 위반 가능 (lag)
- **동기 (sync)** — 적어도 하나의 follower 가 ack 한 후 client 에게 응답. 지연 ↑, 데이터 안전 ↑
- **반동기 (semi-sync)** — N 개 follower 중 K 개만 ack 대기 (MySQL semi-sync)
- **비동기 (async)** — leader 만 기록되면 즉시 ack. 지연 ↓, leader 장애 시 데이터 손실 가능
- **failover** — leader 장애 시 follower 중 하나를 새 leader 로 승격. split-brain 방지를 위해 STONITH / fencing

**장점**:
- 단순하고 직관적인 일관성 모델 (leader 에서는 항상 최신)
- 충돌 (conflict) 없음 — 모든 쓰기가 한 곳에서 직렬화
- 운영 도구 풍부 (대부분 RDBMS가 지원)

**단점·trade-off**:
- leader 가 단일 쓰기 병목 — 수평 확장 한계
- leader 장애 시 failover 시간 동안 unavailable (수 초 ~ 수 분)
- async 복제 시 follower lag 으로 stale read
- failover 중 split-brain 위험 (두 leader 동시 존재)

**실제 DB/시스템**:
- **PostgreSQL** — streaming replication (sync / async / quorum)
- **MySQL** — binlog replication, GTID, semi-sync
- **MongoDB** — Replica Set with oplog
- **Redis** — primary + replica
- **Kafka** — partition leader + ISR (In-Sync Replicas)

**Kotlin pseudo-code 예제**:
```kotlin
class SingleLeaderCluster(
    private val leader: Node,
    private val followers: List<Node>,
    private val mode: ReplicationMode = ReplicationMode.SEMI_SYNC,
) {
    enum class ReplicationMode { SYNC_ALL, SEMI_SYNC, ASYNC }

    fun write(entry: LogEntry): WriteResult {
        leader.appendLog(entry)
        return when (mode) {
            ReplicationMode.SYNC_ALL -> {
                val allAck = followers.all { it.replicate(entry) }
                if (allAck) WriteResult.Ok else WriteResult.Error("follower lag")
            }
            ReplicationMode.SEMI_SYNC -> {
                val anyAck = followers.any { it.replicate(entry) }
                followers.forEach { runCatching { it.replicate(entry) } } // best-effort 나머지
                if (anyAck) WriteResult.Ok else WriteResult.Error("no follower ack")
            }
            ReplicationMode.ASYNC -> {
                followers.forEach { runCatching { it.replicate(entry) } } // fire-and-forget
                WriteResult.Ok
            }
        }
    }

    fun read(key: String, fromLeaderOnly: Boolean = false): String? =
        if (fromLeaderOnly) leader.read(key)
        else (followers + leader).random().read(key) // stale read 가능
}
```

**관련 패턴**: [Multi-Leader Replication](#multi-leader-replication), [Leaderless Replication](#leaderless-replication), [CDC](#cdc), [`../algorithms/db-storage-engines.md`](../../../data-advisor/references/algorithms/db-storage-engines.md)

---

<a id="multi-leader-replication"></a>

## 5. Multi-Leader Replication (다중 리더 복제)

**정의**: 여러 노드가 동시에 쓰기를 받을 수 있는 leader 로 동작하고, 서로의 변경 로그를 교환하는 복제 방식. multi-region 배포에서 각 region 에 leader 를 두어 local write 지연을 줄이거나, 오프라인 우선 (offline-first) 애플리케이션에서 사용. 충돌 (conflict) 처리가 핵심 과제.

**메커니즘**:
- 각 leader 는 local 쓰기 수용 → log 기록 → 다른 leader 들에게 비동기 전파
- **충돌 (conflict)** 발생 — 같은 키를 서로 다른 leader 에서 동시에 수정
- 충돌 해소 전략:
  - **Last-Writer-Wins (LWW)** — 타임스탬프가 늦은 쪽이 승. 손실 위험 ([LWW-Set CRDT](../algorithms/distributed.md))
  - **Application-level merge** — 두 버전을 모두 client 에 노출하고 사용자 해결
  - **CRDT** — 자동 수렴 가능한 데이터 타입 (G-Counter, OR-Set 등)
  - **No-op (manual)** — 충돌 큐에 쌓고 운영자 해결

**장점**:
- 지역별 local write — cross-region 지연 회피
- 오프라인 운영 지원 (CouchDB-style)
- 한 region 전체 장애에도 다른 region 계속 동작

**단점·trade-off**:
- 충돌 해소 로직 필수 — 복잡도 폭증
- Auto-increment ID, 외래키 제약 위반 위험
- 동기 강제 시 cross-region 지연 → 의미 상실
- 운영 시 "어느 region 이 진실인가" 답이 모호함

**실제 DB/시스템**:
- **MySQL** — circular replication (비추천, 위험)
- **Galera Cluster** — synchronous multi-master with certification-based replication
- **Cassandra** — leaderless 이지만 multi-leader 와 유사하게 동작
- **CouchDB** — multi-master with revision tree
- **Bucardo** (PostgreSQL) — async multi-master

**Kotlin pseudo-code 예제**:
```kotlin
data class VersionedValue<T>(val value: T, val timestamp: Long, val nodeId: String)

class MultiLeaderNode<T>(val nodeId: String, private val peers: List<MultiLeaderNode<T>>) {
    private val store = mutableMapOf<String, VersionedValue<T>>()

    fun write(key: String, value: T) {
        val v = VersionedValue(value, System.currentTimeMillis(), nodeId)
        applyLocal(key, v)
        peers.forEach { runCatching { it.receiveReplication(key, v) } } // async
    }

    fun receiveReplication(key: String, incoming: VersionedValue<T>) {
        applyLocal(key, incoming)
    }

    // Last-Writer-Wins 충돌 해소
    private fun applyLocal(key: String, incoming: VersionedValue<T>) {
        val current = store[key]
        if (current == null || current.timestamp < incoming.timestamp ||
            (current.timestamp == incoming.timestamp && current.nodeId < incoming.nodeId)) {
            store[key] = incoming
        }
        // 동률(ts+nodeId 동일)은 idempotent — 그대로 둠
    }

    fun read(key: String): T? = store[key]?.value
}
```

**관련 패턴**: [Single-Leader Replication](#single-leader-replication), [Leaderless Replication](#leaderless-replication), [`../algorithms/distributed.md`](../algorithms/distributed.md) (CRDT)

---

<a id="leaderless-replication"></a>

## 6. Leaderless Replication (리더리스 복제)

**정의**: 지정된 leader 없이 client 가 여러 replica 에 직접 동시에 읽기/쓰기를 보내는 구조. Amazon Dynamo (2007) 가 정립한 모델. **Quorum (R+W>N)** 으로 일관성 강도를 조절하고, **read repair / anti-entropy** 로 수렴.

**메커니즘**:
- N = replica 수, W = write 시 ack 필요 수, R = read 시 응답 필요 수
- **R + W > N** → 적어도 한 replica 는 최신값을 보유 (read-your-writes 보장)
- **Sloppy Quorum** — 원래 책임 노드가 down 이면 임시로 다른 노드에 쓰기 (hinted handoff)
- **Read Repair** — 읽기 시 stale 한 replica 발견하면 최신값으로 갱신
- **Anti-Entropy** — 백그라운드로 Merkle Tree 비교 후 차이 동기화
- 충돌 — Vector Clock 으로 detect, application-level resolve 또는 CRDT

**장점**:
- leader 가 없어 failover 개념 자체가 없음 — 가용성 최고
- 노드 추가/제거에 매우 유연 (consistent hashing 조합)
- W=1 로 설정 시 쓰기 지연 매우 낮음

**단점·trade-off**:
- 일관성 보장이 약함 — eventual consistency 기본
- Sloppy Quorum 시 일관성 보장이 깨질 수 있음
- 충돌 해소가 application 책임 — 복잡
- 모니터링 / 디버깅 어려움

**실제 DB/시스템**:
- **Amazon DynamoDB** — leaderless (configurable consistency)
- **Apache Cassandra** — tunable consistency (ONE / QUORUM / ALL)
- **Riak KV** — 원조 Dynamo-style
- **Voldemort** (LinkedIn, 종료됨) — Dynamo paper 구현체

**Kotlin pseudo-code 예제**:
```kotlin
class LeaderlessCluster(val replicas: List<Node>, val n: Int = 3, val w: Int = 2, val r: Int = 2) {
    init { require(r + w > n) { "Quorum violated: R+W must > N" } }

    fun write(key: String, value: String, timestamp: Long = System.currentTimeMillis()): WriteResult {
        val acks = replicas.shuffled().take(n).map { replica ->
            runCatching { replica.write(key, VersionedValue(value, timestamp)) }
        }.count { it.isSuccess }
        return if (acks >= w) WriteResult.Ok
               else WriteResult.Error("only $acks/$w acks")
    }

    fun read(key: String): String? {
        val responses = replicas.shuffled().take(n)
            .mapNotNull { runCatching { it.read(key) }.getOrNull() }
        if (responses.size < r) return null // quorum not met
        // 최신 timestamp 가 진실
        val latest = responses.maxByOrNull { it.timestamp } ?: return null
        // Read Repair: stale replica 갱신
        replicas.forEach { node ->
            val current = node.read(key)
            if (current == null || current.timestamp < latest.timestamp) {
                runCatching { node.write(key, latest) }
            }
        }
        return latest.value
    }
}
```

**관련 패턴**: [CAP](#cap-theorem), [Consistent Hashing](#consistent-hashing-sharding), [`../algorithms/distributed.md`](../algorithms/distributed.md) (Quorum, Anti-Entropy)

---

<a id="sharding-partitioning"></a>

## 7. Sharding / Partitioning (샤딩 / 파티셔닝)

**정의**: 단일 데이터셋이 너무 커지거나 단일 노드 처리량을 초과할 때 데이터를 여러 노드에 분할 (shard, partition) 하여 저장하는 패턴. 각 shard 는 독립된 노드 (또는 노드 집합) 에서 운영되어 수평 확장 (horizontal scaling) 을 가능하게 한다.

**메커니즘 — 4 가지 파티셔닝 전략**:
- **Range Partitioning** — 키 범위로 분할 (예: A-F, G-M, N-S, T-Z). 범위 쿼리에 유리, hot spot 위험. HBase, BigTable
- **Hash Partitioning** — hash(key) % N 으로 분할. 균등 분포, 범위 쿼리 불가. Cassandra, Redis Cluster
- **Geographic Partitioning** — region/country 기준. 데이터 주권 (GDPR), 지역 지연 최적화
- **Directory-based** — 별도 lookup 서비스가 어떤 shard 에 데이터가 있는지 매핑. Vitess, HDFS NameNode

**핵심 과제 — Rebalancing**:
- 노드 추가/제거 시 데이터 재분배 필요
- 고정 hash modulo 는 모든 노드 재분배 → 운영 마비
- 해결책: **Consistent Hashing** ([8번](#consistent-hashing-sharding)), **Hash Ring**, **Token Range**

**장점**:
- 거의 무한한 수평 확장 (페타바이트 규모 가능)
- shard 간 독립 — 한 shard 장애가 다른 shard 영향 없음
- 로컬 처리량 ↑ (한 노드가 전체 부하의 1/N 만 담당)

**단점·trade-off**:
- **Cross-shard 쿼리 어려움** — JOIN, aggregation 비용 폭증
- **Cross-shard 트랜잭션** — 2PC 또는 Saga 필요 (분산 트랜잭션 복잡도)
- **Hot Spot** — 키 분포 편향 시 일부 shard 만 과부하 (Range 의 단점)
- **Rebalancing 시 가용성/지연 영향**
- **Secondary index** — global vs local 선택 trade-off

**실제 DB/시스템**:
- **Range** — HBase, BigTable, MongoDB (shard key)
- **Hash** — Cassandra, DynamoDB, Redis Cluster (slot 16384)
- **Geographic** — Spanner (regions), CockroachDB (locality)
- **Directory** — Vitess (MySQL sharding), Citus (PostgreSQL), HDFS

**Kotlin pseudo-code 예제**:
```kotlin
interface Partitioner<K> {
    fun shardFor(key: K): Int
}

class HashPartitioner<K>(private val shardCount: Int) : Partitioner<K> {
    override fun shardFor(key: K): Int = (key.hashCode().toLong() and 0xFFFFFFFFL).toInt() % shardCount
}

class RangePartitioner(private val boundaries: List<String>) : Partitioner<String> {
    override fun shardFor(key: String): Int =
        boundaries.indexOfFirst { key <= it }.let { if (it < 0) boundaries.size else it }
}

class ShardedCluster<K, V>(
    private val shards: List<Node>,
    private val partitioner: Partitioner<K>,
) {
    fun put(key: K, value: V) = shards[partitioner.shardFor(key)].write(key.toString(), value.toString())
    fun get(key: K): V? = shards[partitioner.shardFor(key)].read(key.toString()) as? V

    // cross-shard 쿼리는 scatter-gather
    suspend fun aggregateAll(query: String): List<String> = coroutineScope {
        shards.map { async { it.query(query) } }.awaitAll().flatten()
    }
}
```

**관련 패턴**: [Consistent Hashing](#consistent-hashing-sharding), [CDC](#cdc), [Leaderless Replication](#leaderless-replication)

---

<a id="consistent-hashing-sharding"></a>

## 8. Consistent Hashing (일관 해싱 — Sharding 관점)

**정의**: David Karger 등이 1997 STOC 논문에서 제시한 해싱 기법. 노드 추가/제거 시 K/N 개 키만 재배치되도록 (전체 modulo 해싱의 K(N-1)/N 대비 압도적 개선) 설계된 hash ring 구조. Dynamo (2007), Cassandra, Memcached 클라이언트 라이브러리 (ketama) 가 표준으로 채택. 알고리즘 자체 상세는 [`../algorithms/distributed.md`](../algorithms/distributed.md) §11 및 [`../algorithms/load-balancing.md`](../algorithms/load-balancing.md) §6 참조.

**메커니즘**:
- 키 공간 = 0 ~ 2^32 (또는 2^64) 의 원형 ring
- 각 노드는 hash(nodeId) 위치에 배치
- 키는 hash(key) 위치에서 시계방향 첫 노드에 할당
- **Virtual Node (vnode)** — 한 노드를 ring 위 여러 점에 배치 (예: 256개 vnode/node)
  - 노드 간 부하 균형 ↑
  - 노드 추가/제거 시 영향 분산
- **Replication** — 시계방향 다음 N-1 개 노드에도 복제

**장점**:
- 노드 변경 시 K/N 키만 이동 — rebalancing 비용 최소
- vnode 로 heterogeneous 노드 (스펙 다른) 지원 가능
- 단순한 알고리즘 — client 측에서도 구현 가능
- Dynamo / Cassandra / DynamoDB 의 기반

**단점·trade-off**:
- vnode 가 적으면 부하 불균형 (변동성 ↑)
- 노드 추가 시 인접 노드만 부하 받음 (vnode 가 완화)
- 가상 노드 메타데이터 관리 비용

**실제 시스템**:
- **Amazon Dynamo / DynamoDB** — 원조
- **Apache Cassandra** — vnode 기본 256개
- **Memcached (ketama)** — client 라이브러리 표준
- **Riak** — 64 vnode 고정
- **Discord** — 자체 KV 스토어

**Kotlin pseudo-code 예제**:
```kotlin
import java.util.TreeMap

class ConsistentHashRing(private val virtualNodesPerNode: Int = 256) {
    private val ring = TreeMap<Long, String>() // hash → nodeId

    fun addNode(nodeId: String) {
        repeat(virtualNodesPerNode) { i ->
            val vnodeKey = "$nodeId#$i"
            ring[hash(vnodeKey)] = nodeId
        }
    }

    fun removeNode(nodeId: String) {
        repeat(virtualNodesPerNode) { i -> ring.remove(hash("$nodeId#$i")) }
    }

    fun nodeFor(key: String): String? {
        if (ring.isEmpty()) return null
        val h = hash(key)
        return ring.ceilingEntry(h)?.value ?: ring.firstEntry().value // wrap around
    }

    fun replicasFor(key: String, replicationFactor: Int): List<String> {
        if (ring.isEmpty()) return emptyList()
        val h = hash(key)
        val result = LinkedHashSet<String>()
        var iter = ring.tailMap(h).values.iterator()
        while (result.size < replicationFactor) {
            if (!iter.hasNext()) iter = ring.values.iterator() // wrap
            result.add(iter.next())
            if (result.size == ring.values.toSet().size) break // 모든 물리노드 다 추가됨
        }
        return result.toList()
    }

    private fun hash(input: String): Long {
        // 실제로는 MD5/MurmurHash3 등 사용
        return input.hashCode().toLong() and 0xFFFFFFFFL
    }
}
```

**관련 패턴**: [Sharding](#sharding-partitioning), [Leaderless Replication](#leaderless-replication), [`../algorithms/distributed.md`](../algorithms/distributed.md), [`../algorithms/load-balancing.md`](../algorithms/load-balancing.md)

---

<a id="cdc"></a>

## 9. Change Data Capture (CDC, 변경 데이터 캡처)

**정의**: 데이터베이스의 변경 사항 (INSERT / UPDATE / DELETE) 을 실시간으로 추출하여 다른 시스템으로 스트리밍하는 패턴. 트랜잭션 로그 (WAL, binlog, redo log) 를 tail 해서 이벤트 스트림으로 변환한다. Outbox 패턴 ([distributed.md](distributed.md) §5) 의 대체 또는 보완으로 사용된다.

**메커니즘 — 두 가지 구현 방식**:
- **Log-based CDC** — DB 트랜잭션 로그를 직접 tail. 부하 거의 없고 정확하지만 DB 별 구현체 필요
  - PostgreSQL → logical decoding (wal2json, pgoutput)
  - MySQL → binlog (ROW format)
  - Oracle → LogMiner, XStream
  - SQL Server → CDC tables
- **Trigger-based CDC** — DB 트리거로 변경 테이블에 INSERT. DB 부하 ↑, 모든 DB 에서 가능
- **Polling-based CDC** — 타임스탬프 컬럼 주기적 SELECT. 가장 단순하지만 비효율

**대표 도구**:
- **Debezium** — 오픈소스 표준. Kafka Connect 기반. PostgreSQL/MySQL/MongoDB/Oracle/SQL Server 지원
- **Maxwell** — MySQL binlog → Kafka/Kinesis
- **DBLog (Netflix)** — 초기 snapshot + 이후 incremental
- **AWS DMS** — managed CDC
- **Airbyte / Fivetran** — managed ELT with CDC

**Kafka Connect 메시지 형식 (Debezium 예)**:
```json
{
  "schema": {...},
  "payload": {
    "before": null,
    "after": { "id": 1, "email": "alice@example.com" },
    "source": { "ts_ms": 1700000000000, "table": "users", "lsn": 12345 },
    "op": "c",                  // c=create, u=update, d=delete, r=read(snapshot)
    "ts_ms": 1700000000123
  }
}
```

**장점**:
- 애플리케이션 코드 변경 없이 이벤트 추출
- 트랜잭션 로그 기반 → 데이터 손실 없음 + 순서 보장
- Outbox 패턴의 운영 부담 (테이블 관리, polling) 제거
- Event Sourcing, Read Model 갱신, Cache invalidation, Data Warehouse ingestion 모두 가능

**단점·trade-off**:
- DB 별 구현체 lock-in
- 스키마 변경 시 호환성 깨질 위험 (DDL 처리)
- 초기 snapshot 비용 (큰 테이블 시 수 시간)
- ROW 포맷 binlog 필수 (MySQL) → 디스크 사용량 ↑
- 로그 보존 정책 — replication slot 누적 시 디스크 가득 위험 (PostgreSQL)

**활용 예시**:
- **마이크로서비스 이벤트 발행** — Outbox 대체
- **Search index 동기화** — DB → Elasticsearch
- **Cache invalidation** — DB → Redis
- **Data Warehouse ingestion** — OLTP → Snowflake / BigQuery
- **Audit log / Compliance**
- **Read Model 갱신** — CQRS 의 read side 자동 업데이트

**Kotlin pseudo-code 예제**:
```kotlin
data class ChangeEvent(
    val op: Op,
    val table: String,
    val before: Map<String, Any?>?,
    val after: Map<String, Any?>?,
    val timestamp: Long,
    val lsn: Long, // log sequence number
) {
    enum class Op { CREATE, UPDATE, DELETE, SNAPSHOT }
}

class DebeziumStyleConsumer(private val consumer: KafkaConsumer<String, ChangeEvent>) {
    fun consume() {
        consumer.subscribe(listOf("dbserver1.public.users"))
        while (true) {
            consumer.poll(Duration.ofMillis(500)).forEach { record ->
                when (record.value().op) {
                    ChangeEvent.Op.CREATE -> indexInElastic(record.value().after!!)
                    ChangeEvent.Op.UPDATE -> updateElasticAndInvalidateCache(record.value())
                    ChangeEvent.Op.DELETE -> removeFromElastic(record.value().before!!)
                    ChangeEvent.Op.SNAPSHOT -> bulkLoad(record.value().after!!)
                }
            }
        }
    }
}
```

**관련 패턴**: Outbox ([distributed.md](distributed.md) §5), Event Sourcing ([distributed.md](distributed.md) §2), [Materialized View](#materialized-view), [Lambda/Kappa](#lambda-kappa-htap)

---

<a id="materialized-view"></a>

## 10. Materialized View (구체화 뷰)

**정의**: 쿼리 결과를 실제 저장소에 미리 계산해 저장해 두는 패턴. 일반 View 는 매번 실행되는 가상 테이블이지만, Materialized View 는 물리적으로 저장되어 읽기 시 계산 비용을 제거한다. CQRS 의 read side, OLAP 의 pre-aggregation, real-time dashboard 의 기본 빌딩 블록.

**메커니즘 — 갱신 전략**:
- **Complete Refresh** — 전체 재계산. 단순하지만 대용량 시 비용 ↑
- **Incremental Refresh** — 변경분만 적용. 효율적이지만 구현 복잡
- **On-Demand Refresh** — 명시적 트리거 (`REFRESH MATERIALIZED VIEW`)
- **Scheduled Refresh** — cron / 주기적
- **Streaming Refresh** — CDC 또는 stream processing 으로 실시간 (Flink, Materialize.com)

**일관성 모델**:
- **Stale (Eventual)** — 기본. base table 변경 후 일정 시간 후 반영
- **Synchronous** — base table 갱신 시 동시에 view 갱신 (트리거). 쓰기 지연 ↑
- **Transactional** — view 가 같은 트랜잭션에 참여 (드물게 지원)

**장점**:
- 복잡한 JOIN / aggregation 쿼리를 O(1) 조회로 변환
- 읽기 부하가 base table 에서 분리됨
- CQRS read model 의 자연스러운 구현
- OLAP / Dashboard 응답 속도 극적 개선

**단점·trade-off**:
- 저장 공간 추가 (계산 결과 저장)
- 갱신 비용 (write amplification)
- Stale 데이터 가능성
- 스키마 변경 시 view 재구축 필요
- Incremental refresh 의 정확성 검증 어려움

**실제 시스템**:
- **PostgreSQL** — `CREATE MATERIALIZED VIEW` (REFRESH 명시적, CONCURRENTLY 옵션)
- **Oracle** — Materialized View Logs 로 incremental
- **SQL Server** — Indexed View (자동 동기화)
- **Snowflake / BigQuery** — Materialized View (자동 maintain)
- **Apache Flink / Materialize.com** — streaming materialized view
- **Cassandra** — built-in materialized view (deprecated, replaced by manual denormalization)
- **ClickHouse** — incremental materialized view (push-based)

**SQL 예제**:
```sql
-- PostgreSQL: 주문별 일별 매출 집계 view
CREATE MATERIALIZED VIEW daily_sales AS
SELECT
    date_trunc('day', created_at) AS sale_date,
    product_id,
    SUM(amount) AS total_amount,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'completed'
GROUP BY 1, 2;

-- 인덱스 추가 (조회 속도 ↑)
CREATE UNIQUE INDEX idx_daily_sales ON daily_sales (sale_date, product_id);

-- 주기적 갱신 (downtime 없이)
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_sales;

-- 사용
SELECT * FROM daily_sales WHERE sale_date = CURRENT_DATE - INTERVAL '7 days';
```

**Kotlin 예제 (CQRS read model with CDC-driven materialized view)**:
```kotlin
data class OrderSummary(val userId: String, val totalOrders: Int, val totalAmount: Long)

class OrderSummaryView(
    private val readDb: ReadDatabase,
    private val cdcStream: Flow<ChangeEvent>,
) {
    suspend fun start() = cdcStream.collect { event ->
        when (event.op) {
            ChangeEvent.Op.CREATE -> incrementSummary(
                userId = event.after!!["user_id"] as String,
                amount = event.after["amount"] as Long,
            )
            ChangeEvent.Op.DELETE -> decrementSummary(
                userId = event.before!!["user_id"] as String,
                amount = event.before["amount"] as Long,
            )
            ChangeEvent.Op.UPDATE -> {
                // before subtract + after add
            }
            else -> Unit
        }
    }

    private suspend fun incrementSummary(userId: String, amount: Long) {
        readDb.upsert("UPDATE order_summary SET total_orders = total_orders + 1, " +
                     "total_amount = total_amount + $amount WHERE user_id = '$userId'")
    }

    private suspend fun decrementSummary(userId: String, amount: Long) {
        readDb.upsert("UPDATE order_summary SET total_orders = total_orders - 1, " +
                     "total_amount = total_amount - $amount WHERE user_id = '$userId'")
    }
}
```

**관련 패턴**: CQRS ([distributed.md](distributed.md) §1), [CDC](#cdc), [Lambda/Kappa](#lambda-kappa-htap), [Data Mesh / Lakehouse](#data-mesh-lakehouse)

---

<a id="lambda-kappa-htap"></a>

## 11. HTAP / Lambda / Kappa Architecture (HTAP / 람다 / 카파 아키텍처)

**정의**: 트랜잭션 (OLTP) 과 분석 (OLAP) 워크로드를 동일/별개 인프라에서 처리하는 세 가지 데이터 아키텍처 패턴. **Lambda (배치+실시간 이중)** → **Kappa (스트림 단일)** → **HTAP (단일 DB 에서 양쪽)** 의 진화.

**메커니즘**:

### 11.1 Lambda Architecture (Nathan Marz, 2011)
- **Batch Layer** — 모든 raw 데이터 저장 (HDFS), 주기적 (시간/일) 정확한 view 계산 (Spark, MapReduce)
- **Speed Layer** — 최근 데이터 실시간 처리 (Storm, Spark Streaming)
- **Serving Layer** — batch view + speed view 병합해 query (HBase, Druid)
- 동일 로직을 **batch 와 stream 두 곳에 중복 구현**해야 함

### 11.2 Kappa Architecture (Jay Kreps, LinkedIn, 2014)
- "Lambda 의 중복 구현이 문제다 — stream 만으로 다 하자"
- 모든 데이터는 immutable log (Kafka) 에 저장
- 처리 = stream processing (Flink, Kafka Streams)
- 재처리 (reprocess) = 로그 처음부터 다시 stream
- 단일 코드 path

### 11.3 HTAP (Hybrid Transactional/Analytical Processing)
- Gartner 용어 (2014)
- 한 DB 에서 OLTP + OLAP 동시 수행
- Row store + column store 동시 보유 (TiDB, SingleStore, SAP HANA)
- ETL 필요 없음 — analytical 쿼리가 실시간 데이터 본다

**장점·trade-off 매트릭스**:

| 아키텍처 | 실시간성 | 정확성 | 운영 복잡도 | 코드 중복 | 대표 시스템 |
|----------|----------|--------|-------------|-----------|-------------|
| Lambda | 분~시간 | 매우 높음 (batch) | 매우 높음 | 있음 (2배) | Twitter (구), Spotify (구) |
| Kappa | 초~분 | 높음 (정확한 once 보장 필요) | 높음 | 없음 (1배) | LinkedIn, Uber |
| HTAP | 실시간 | 매우 높음 | 낮음~중간 | 없음 | TiDB, SingleStore, SAP HANA, Snowflake Unistore |

**Lambda 의 단점**:
- batch 와 stream 로직을 별도 구현/유지 → 버그/불일치 빈발
- 두 인프라 운영 (Spark + Storm/Flink) — 비용 ↑
- batch view 와 speed view 병합 로직 복잡

**Kappa 의 단점**:
- 매우 큰 재처리 = 시간/비용 ↑ (수년치 로그 재실행)
- exactly-once 보장 필요 (Flink checkpointing, Kafka Transactions)
- stream 만으로 일부 분석 (복잡한 ML training) 어려움

**HTAP 의 단점**:
- 단일 DB 에 모든 워크로드 → 리소스 격리 어려움
- 압도적 분석 부하 시 OLTP 영향
- 벤더 lock-in (TiDB, SingleStore 등)
- ETL 없이 ML/외부 분석 도구 연계 시 한계

**실제 시스템**:
- **Lambda** — Twitter (Heron + Hadoop, 2014), 초기 Netflix
- **Kappa** — LinkedIn (Samza), Uber (Flink + Kafka)
- **HTAP** — TiDB (TiFlash), SingleStore (구 MemSQL), SAP HANA, Oracle Database In-Memory, Snowflake Unistore, CockroachDB + columnar
- **Hybrid** — Apache Pinot, Druid (real-time + historical merged)

**Kotlin pseudo-code 예제 (Kappa 스타일 stream processing)**:
```kotlin
// Kafka Streams 로 stream 만으로 daily aggregation
class DailySalesAggregator(private val streams: KafkaStreams) {
    fun build(): Topology {
        val builder = StreamsBuilder()
        val orders: KStream<String, Order> = builder.stream("orders")

        orders
            .filter { _, order -> order.status == "completed" }
            .groupBy { _, order -> order.productId }
            .windowedBy(TimeWindows.of(Duration.ofDays(1)))
            .aggregate(
                { DailySales(0L, 0) },
                { _, order, agg -> agg.copy(
                    totalAmount = agg.totalAmount + order.amount,
                    orderCount = agg.orderCount + 1,
                )},
                Materialized.`as`("daily_sales_store"),
            )
            .toStream()
            .to("daily_sales_output")

        return builder.build()
    }

    // 재처리 (reprocess) = Kafka offset 처음으로 reset 후 재시작
    fun reprocess() {
        streams.cleanUp()
        // 새 application.id 로 재시작 → Kafka 처음부터 consume
    }
}
```

**관련 패턴**: [CDC](#cdc), [Materialized View](#materialized-view), [Data Mesh / Lakehouse](#data-mesh-lakehouse), Event Sourcing ([distributed.md](distributed.md) §2)

---

<a id="data-mesh-lakehouse"></a>

## 12. Data Mesh / Data Lakehouse (데이터 메시 / 데이터 레이크하우스)

**정의**: 중앙집중식 데이터 웨어하우스의 한계를 극복하기 위한 두 가지 현대적 패러다임.
- **Data Mesh** (Zhamak Dehghani, 2019) — 데이터를 도메인 팀이 소유하는 **product** 로 다루는 **조직적** 분산 패턴
- **Data Lakehouse** (Databricks, 2020) — Data Lake 의 유연성 + Data Warehouse 의 ACID/성능을 결합한 **기술적** 통합 아키텍처

**메커니즘**:

### 12.1 Data Mesh — 4 핵심 원칙
1. **Domain Ownership** — 데이터를 도메인 팀이 소유. 중앙 데이터팀이 모든 데이터를 관리하지 않음
2. **Data as a Product** — 데이터셋을 product 로 취급 (SLA, discoverability, versioning, observability)
3. **Self-Serve Data Platform** — 도메인 팀이 데이터 product 를 만들/배포할 셀프 서비스 인프라
4. **Federated Computational Governance** — 글로벌 표준 + 도메인 자율성 균형

### 12.2 Data Lakehouse — 핵심 기술 요소
- **Open Table Format** — Delta Lake (Databricks), Apache Iceberg (Netflix), Apache Hudi (Uber)
- **ACID 트랜잭션** — 분산 파일 시스템 위에서 (S3, GCS, ADLS)
- **Time Travel** — snapshot 기반 과거 시점 조회
- **Schema Evolution** — 컬럼 추가/삭제 자동 처리
- **Z-Ordering / Data Skipping** — 컬럼 통계로 파일 pruning
- **Unified Compute** — SQL (Trino, Presto, Spark SQL), Python (Spark, Polars), ML (MLflow)

**비교 — Warehouse vs Lake vs Lakehouse**:

| 특성 | Data Warehouse | Data Lake | Data Lakehouse |
|------|----------------|-----------|----------------|
| 저장 | 관계형 (Snowflake/Redshift) | 파일 (S3/HDFS) | 파일 (S3) + 메타데이터 (Delta/Iceberg) |
| 스키마 | Schema-on-write | Schema-on-read | Both |
| ACID | O | X | O |
| BI 도구 | 우수 | 어려움 | 우수 |
| ML 워크로드 | 제한적 | 우수 | 우수 |
| 비용 | 높음 | 낮음 | 중간 |
| 거버넌스 | 강함 | 약함 | 강함 |

**Data Mesh 장점**:
- 도메인 자율성 — 데이터 변경이 빠름
- 데이터팀 병목 제거
- 도메인 지식이 데이터에 반영됨
- 대규모 조직에서 scale-out

**Data Mesh 단점**:
- 조직 변화 비용 — 도메인 팀의 데이터 책임 학습 필요
- 거버넌스 복잡도 — federated 가 어려움
- 작은 조직엔 과잉 — Conway's Law 와 충돌 시 실패
- 도메인 간 데이터 product 통합 어려움

**Data Lakehouse 장점**:
- 단일 인프라로 BI + ML 모두 지원
- 오픈 포맷 (Parquet, Avro) — vendor lock-in 회피
- 저렴한 object storage (S3) 활용
- Time travel 로 reproducibility ↑ (특히 ML)

**Data Lakehouse 단점**:
- 신생 기술 — production 운영 노하우 부족
- 메타데이터 관리 복잡 (millions of files)
- 동시성 / 작은 파일 문제 (small file problem)
- 전통 Warehouse 대비 일부 BI 쿼리 성능 떨어질 수 있음

**실제 시스템·예시**:
- **Data Mesh 도입** — Zalando, JPMorgan Chase, Intuit, Netflix (부분)
- **Data Lakehouse 구현**:
  - **Delta Lake** (Databricks) — 가장 성숙. Databricks Platform
  - **Apache Iceberg** (Netflix, Apple) — 벤더 중립적. Snowflake, AWS Athena, Trino 지원
  - **Apache Hudi** (Uber) — incremental/streaming 강점
- **통합 시도** — Databricks Unity Catalog, Microsoft Fabric, AWS Lake Formation

**SQL 예제 (Delta Lake — ACID + Time Travel)**:
```sql
-- Delta Lake 테이블 생성
CREATE TABLE orders (
    order_id BIGINT,
    user_id STRING,
    amount DECIMAL(10, 2),
    created_at TIMESTAMP
) USING DELTA LOCATION 's3://lakehouse/orders';

-- ACID 트랜잭션
BEGIN TRANSACTION;
INSERT INTO orders VALUES (1, 'alice', 99.99, current_timestamp());
UPDATE orders SET amount = 89.99 WHERE order_id = 1;
COMMIT;

-- Time travel (1시간 전 데이터 조회)
SELECT * FROM orders TIMESTAMP AS OF '2026-05-14 10:00:00';
SELECT * FROM orders VERSION AS OF 42;

-- Schema evolution
ALTER TABLE orders ADD COLUMN discount DECIMAL(5, 2);

-- MERGE (Upsert)
MERGE INTO orders t
USING staging_orders s ON t.order_id = s.order_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

**Kotlin pseudo-code 예제 (Data Product API 인터페이스 — Data Mesh)**:
```kotlin
// 도메인 팀이 소유하는 데이터 product 의 표준 인터페이스
interface DataProduct<T> {
    val id: String
    val owner: String              // 도메인 팀
    val sla: SLA                   // freshness, availability
    val schema: Schema
    val documentation: String      // discoverability

    suspend fun read(query: Query): Flow<T>
    suspend fun subscribe(): Flow<ChangeEvent<T>>  // CDC stream
    suspend fun describe(): Metadata               // observability
}

// 예: Order 도메인 팀이 발행하는 data product
class OrderDataProduct(
    private val storage: DeltaLakeStorage,
) : DataProduct<Order> {
    override val id = "domain.order.completed-orders.v1"
    override val owner = "team-order"
    override val sla = SLA(freshnessMinutes = 5, availabilityNines = 3)
    override val schema = OrderSchema.v1
    override val documentation = "https://wiki/data-products/completed-orders"

    override suspend fun read(query: Query): Flow<Order> =
        storage.query("SELECT * FROM completed_orders WHERE ${query.toSql()}").map { it.toOrder() }

    override suspend fun subscribe(): Flow<ChangeEvent<Order>> =
        storage.cdcStream("completed_orders")

    override suspend fun describe(): Metadata = Metadata(
        rowCount = storage.count("completed_orders"),
        lastUpdated = storage.lastModified("completed_orders"),
        partitions = storage.partitions("completed_orders"),
    )
}
```

**관련 패턴**: [CDC](#cdc), [Materialized View](#materialized-view), [Lambda/Kappa](#lambda-kappa-htap), CQRS ([distributed.md](distributed.md) §1), Event Sourcing ([distributed.md](distributed.md) §2)

---

## 종합 의사결정 가이드

**일관성 vs 가용성 선택** (분할 시):
- 금융, 재고, 결제 → **CP** (Strong consistency)
- SNS, 추천, 로그 → **AP** (Eventual consistency)

**복제 토폴로지 선택**:
- 단일 region OLTP → **Single-Leader**
- Multi-region 쓰기 → **Multi-Leader** (충돌 해소 필수) 또는 **Leaderless**
- 무제한 확장 + 가용성 우선 → **Leaderless** (Dynamo-style)

**확장 전략**:
- 단일 노드 처리량 초과 → **Sharding** + **Consistent Hashing**
- 단일 region 의 cross-region 지연 → **Multi-Leader** 또는 **Geographic Partitioning**

**이벤트 흐름·통합**:
- DB 변경 → 다른 시스템 → **CDC** (Debezium)
- 트랜잭션 + 메시지 일관성 → **Outbox** 또는 **CDC**
- 복잡한 read 쿼리 최적화 → **Materialized View** (또는 CQRS read side)

**분석·OLAP**:
- 작은 조직, 정확성 최우선 → **Lambda** (drawback: 중복 구현)
- 실시간 + 단일 코드 → **Kappa**
- OLTP + 가벼운 OLAP 통합 → **HTAP** (TiDB, SingleStore)
- 무거운 분석 + ML + BI → **Data Lakehouse** (Delta / Iceberg)
- 대규모 조직, 도메인 자율성 → **Data Mesh** (조직 패러다임)

---

## 학습 경로 권장 순서

1. **이론 기반** — [CAP Theorem](#cap-theorem) → [PACELC](#pacelc) → [Consistency Models](#consistency-models-systems)
2. **복제 메커니즘** — [Single-Leader](#single-leader-replication) → [Multi-Leader](#multi-leader-replication) → [Leaderless](#leaderless-replication)
3. **확장 메커니즘** — [Sharding](#sharding-partitioning) → [Consistent Hashing](#consistent-hashing-sharding)
4. **이벤트·뷰** — [CDC](#cdc) → [Materialized View](#materialized-view)
5. **현대 아키텍처** — [Lambda/Kappa/HTAP](#lambda-kappa-htap) → [Data Mesh/Lakehouse](#data-mesh-lakehouse)

**필독 문헌**:
- Martin Kleppmann — *Designing Data-Intensive Applications* (2017) — 본 카탈로그 전체의 원전
- *Dynamo: Amazon's Highly Available Key-value Store* (SOSP 2007) — Leaderless / Consistent Hashing 원전
- Daniel Abadi — *Consistency Tradeoffs in Modern Distributed Database System Design* (Computer 2012) — PACELC 원전
- Zhamak Dehghani — *Data Mesh: Delivering Data-Driven Value at Scale* (O'Reilly 2022)
- Databricks — *Lakehouse: A New Generation of Open Platforms* (CIDR 2021)

**관련 (P1 신설)**:
- [`data-warehousing-bi.md#kimball-star-snowflake`](../../../data-advisor/references/patterns/data-warehousing.md#kimball-star-snowflake) — OLTP 정규화 모델 ↔ DWH 차원 모델 (Star / Snowflake) 의 양극단 비교
- [`data-warehousing-bi.md#scd-types`](../../../data-advisor/references/patterns/data-warehousing.md#scd-types) — 시간 차원 변경 추적 (SCD Type 1/2/3/4/6) 은 데이터 모델링 결정과 직결
- [`data-warehousing-bi.md#lakehouse-iceberg-delta-hudi`](../../../data-advisor/references/patterns/data-warehousing.md#lakehouse-iceberg-delta-hudi) — Lakehouse 의 분석 워크로드 ↔ Lambda / Kappa / Data Mesh 의 위치

---

<a id="harvest-yield-akf"></a>

## 13. Harvest & Yield / AKF Scale Cube (수확·산출 / AKF 확장 큐브)

**정의**: 두 개의 보완 모델을 묶은 항목.
- **Harvest & Yield** — Armando Fox & Eric Brewer 가 1999 HotOS 논문 *Harvest, Yield, and Scalable Tolerant Systems* 에서 제시. CAP 의 이분법 (C 또는 A) 을 **연속적 스펙트럼**으로 정련한다. **Harvest** = 응답에 반영된 데이터의 비율 (`완전성 = 반영된 데이터 / 전체 데이터`), **Yield** = 성공적으로 응답된 요청의 비율 (`yield = 완료 요청 / 전체 요청`, availability 의 정련된 측정치). 분할/장애 시 시스템을 통째로 죽이는 대신 **harvest 나 yield 중 하나를 점진적으로 낮춰 부분 가용성 (graceful degradation) 을 제공**한다.
- **AKF Scale Cube** — Abbott & Fisher 가 *The Art of Scalability* (2009) 에서 제시한 확장 모델. 시스템 확장을 직교하는 3 축으로 분해한다. **X축 = 복제 (clone)**, **Y축 = 기능 분할 (functional decomposition)**, **Z축 = 데이터 샤딩 (data partitioning)**. 세 축은 독립적으로 적용 가능하며 동시에 적용하면 cube 의 한 점 (예: X+Y+Z) 으로 표현된다.

두 모델은 한 축으로 묶인다: AKF 큐브로 **확장**해 부하/장애 영향을 작은 단위에 가두고, Harvest/Yield 로 그 단위가 깨졌을 때 **어떻게 우아하게 저하시킬지**를 정량적으로 결정한다.

**메커니즘**:

### Harvest & Yield (CAP 정련)
- **Yield 우선 (high-yield)** — 검색 엔진처럼 일부 노드 응답이 빠져도 "있는 데이터만으로" 응답 반환. 100 개 shard 중 95 개만 응답 → harvest 95%, yield 는 유지. 누락 데이터는 "approximate result" 로 명시
- **Harvest 우선 (high-harvest)** — 결제/잔액처럼 완전한 데이터가 아니면 차라리 응답을 거부. harvest 100% 를 보장하고 yield 를 희생 (요청 거부)
- **DQ Principle** — Fox/Brewer 의 보조 원리. `Data per query × Queries per second ≈ 상수`. 시스템 용량이 고정이면 harvest (D) 와 throughput (Q) 사이에 trade-off 가 존재 → 부하 폭증 시 harvest 를 낮춰 yield 를 지킨다
- **적용 단위** — 요청별/필드별로 다르게 설정 가능 (graceful degradation 의 입도)

### AKF Scale Cube (3축)
- **X축 (Replication / Clone)** — 동일한 전체 시스템을 복제하고 load balancer 로 분산. 가장 쉬움. 무상태 서비스/read replica. 한계: 데이터/캐시는 여전히 전체를 복제 → 데이터 증가에 한계
- **Y축 (Functional Decomposition / Split by service)** — 기능/리소스/동사 기준 분리. 모놀리식 → 마이크로서비스 (users-service, orders-service). 팀 독립성 ↑, 배포 단위 ↓
- **Z축 (Data Sharding / Split by customer-data)** — 동일 코드를 데이터 기준으로 분할. tenant_id, region, customer_id 로 샤딩 ([Sharding](#sharding-partitioning) 의 조직적 표현). 무한 확장 가능, 운영 복잡

**장점**:
- CAP 의 "all-or-nothing" 을 **정량 스펙트럼**으로 바꿔 SLA/제품 결정과 직접 연결 (예: "검색은 yield 99.9% + harvest 95%, 결제는 harvest 100%")
- AKF 큐브는 확장 논의를 **공통 어휘 (X/Y/Z)** 로 통일 — 아키텍처 리뷰의 체크리스트로 사용
- 세 축이 직교 → 병목 종류에 맞는 축만 선택적으로 적용 가능
- 부분 장애를 "전면 장애" 가 아닌 "harvest 저하" 로 흡수 → 가용성 체감 ↑

**단점·trade-off**:
- harvest 를 낮춘 응답은 **불완전함을 호출자에게 알려야** 함 (조용한 부분 응답은 데이터 신뢰를 해침)
- harvest/yield 측정·노출 인프라 (per-shard 성공률 집계) 가 추가로 필요
- Z축 샤딩은 cross-shard 쿼리/트랜잭션 비용 ([Sharding](#sharding-partitioning) 의 단점) 을 그대로 상속
- Y축 분할은 분산 트랜잭션·서비스 간 일관성 (Saga / Outbox) 문제를 새로 만든다
- X축만 확장하면 데이터 계층 병목은 해소되지 않음 (착시) — 큐브의 흔한 함정

**실제 시스템·예시**:
- **High-yield (harvest 희생)** — Google/Elasticsearch 검색 (일부 shard timeout 시 `timed_out: true` + 부분 결과), Netflix 추천 (개인화 실패 시 fallback 인기 목록)
- **High-harvest (yield 희생)** — 은행 잔액 조회, 재고 차감 (불완전 데이터면 거부)
- **X축** — stateless web tier + ALB, PostgreSQL read replica
- **Y축** — 마이크로서비스 분해 (Amazon, Netflix)
- **Z축** — Shopify pod (shop 단위 샤딩), Slack/Salesforce 멀티테넌시 tenant 샤딩, Instagram user_id 샤딩

**Kotlin 예제 (Scatter-gather with Harvest/Yield degradation)**:
```kotlin
data class PartialResult<T>(
    val data: List<T>,
    val harvest: Double,   // 반영된 데이터 비율 (응답 shard / 전체 shard)
    val complete: Boolean, // harvest == 1.0 인가
)

class HarvestYieldQuery<T>(
    private val shards: List<Node>,          // AKF Z축: 데이터 샤드들
    private val minHarvest: Double = 0.8,    // 이 미만이면 yield 포기(거부)
    private val perShardTimeoutMs: Long = 200,
) {
    suspend fun query(sql: String): PartialResult<T> = coroutineScope {
        // 각 shard 에 병렬 요청, 타임아웃된 shard 는 harvest 에서 제외
        val responses = shards.map { shard ->
            async {
                runCatching {
                    withTimeout(perShardTimeoutMs) { shard.query(sql) as List<T> }
                }.getOrNull()
            }
        }.awaitAll()

        val succeeded = responses.filterNotNull()
        val harvest = succeeded.size.toDouble() / shards.size

        // high-harvest 정책: harvest 가 임계 미만이면 yield 를 포기(거부)
        require(harvest >= minHarvest) {
            "harvest=$harvest < $minHarvest — 불완전 결과 거부 (yield 희생)"
        }

        // high-yield 정책: 임계 이상이면 부분 결과라도 반환 (불완전성 명시)
        PartialResult(
            data = succeeded.flatten(),
            harvest = harvest,
            complete = harvest == 1.0,
        )
    }
}
```

**관련 패턴**: [CAP Theorem](#cap-theorem), [PACELC](#pacelc), [Sharding / Partitioning](#sharding-partitioning), [Consistent Hashing](#consistent-hashing-sharding)
