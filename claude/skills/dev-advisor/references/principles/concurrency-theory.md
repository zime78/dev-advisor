# 동시성 이론 (Concurrency Theory)

동시성 패턴([`../patterns/concurrency.md`](../patterns/concurrency.md))·알고리즘([`../algorithms/concurrent.md`](../algorithms/concurrent.md)) 의 **이론적 기반** 10 항목. *증명·정합성 모델·formal property*.

**관련 카탈로그**:
- [`formal-methods.md#formal-tla-plus`](formal-methods.md#formal-tla-plus) — TLA+ (Temporal Logic of Actions) 로 동시성/분산 시스템의 안전성·생존성 명세 (Linearizability·Happens-Before 의 형식 증명 도구)

**원전 참고**:
- Maurice Herlihy, Nir Shavit — *The Art of Multiprocessor Programming* (2008, 2nd ed. 2020)
- Maurice Herlihy & Jeannette Wing — "Linearizability: A Correctness Condition for Concurrent Objects", TOPLAS 12(3), 1990
- Leslie Lamport — "Time, Clocks, and the Ordering of Events in a Distributed System", CACM 21(7), 1978
- Leslie Lamport — "How to Make a Multiprocessor Computer That Correctly Executes Multiprocess Programs", IEEE TC 28(9), 1979
- Edsger Dijkstra — "Cooperating Sequential Processes" (1965)
- Edward Coffman, M. Elphick, A. Shoshani — "System Deadlocks", ACM Computing Surveys (1971)
- Philip Bernstein, Vassos Hadzilacos, Nathan Goodman — *Concurrency Control and Recovery in Database Systems* (1987)
- Hal Berenson et al. — "A Critique of ANSI SQL Isolation Levels", SIGMOD (1995)
- Werner Vogels — "Eventually Consistent", CACM 52(1), 2009
- Mustaque Ahamad et al. — "Causal Memory: Definitions, Implementation, and Programming", Distributed Computing 9(1), 1995

**핵심 가치**: 동시성 *패턴* 은 구현, *이론* 은 "그 구현이 옳다는 것을 어떻게 증명할 수 있는가" 의 언어. 같은 코드라도 어떤 정합성 모델을 만족하느냐에 따라 *허용되는 관측* 이 결정되며, 그 경계 위에서만 race / deadlock / 데이터 손실의 부재를 *증명* 할 수 있다.

**관련 카탈로그**:
- [`../patterns/concurrency.md`](../patterns/concurrency.md) — 14 동시성 패턴 (Actor / CSP / STM / Future ...)
- [`../algorithms/concurrent.md`](../algorithms/concurrent.md) — 10 동시성 알고리즘 (CAS / RCU / MVCC ...)
- [`../algorithms/consensus.md`](../algorithms/consensus.md) — 분산 합의 (2PC / Paxos / Raft)
- [`../algorithms/distributed.md`](../algorithms/distributed.md) — 분산 알고리즘 (Lamport Clock / Vector Clock ...)

## 항목 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [linearizability](#linearizability) | Linearizability | 선형성 | 높음 |
| [serializability](#serializability) | Serializability | 직렬성 | 높음 |
| [sequential-consistency](#sequential-consistency) | Sequential Consistency | 순차 일관성 | 중간 |
| [causal-consistency](#causal-consistency) | Causal Consistency | 인과 일관성 | 중간 |
| [eventual-consistency](#eventual-consistency) | Eventual Consistency | 최종 일관성 | 중간 |
| [snapshot-isolation](#snapshot-isolation) | Snapshot Isolation / SSI | 스냅샷 격리 | 높음 |
| [happens-before](#happens-before) | Happens-Before Relation | 선후관계 | 중간 |
| [liveness-safety](#liveness-safety) | Liveness vs Safety Properties | 진행성 vs 안전성 | 중간 |
| [deadlock-conditions](#deadlock-conditions) | Deadlock 4 Conditions | 교착상태 4 조건 | 중간 |
| [race-condition](#race-condition) | Race Condition / Data Race | 경쟁 상태 / 데이터 경쟁 | 중간 |

---

<a id="linearizability"></a>
## 1. Linearizability (선형성)

**정의**: Herlihy & Wing 1990 이 정의한 **단일 객체 (single-object)** 강한 일관성. 동시 호출되는 객체 연산이, *각 연산이 invocation 과 response 사이의 어느 한 시점에서 원자적으로 실행된 것처럼* 보여야 한다. 이 "원자 시점" 을 **linearization point** 라 하며, 모든 클라이언트가 동일한 전역 순서를 관측한다. 또한 **실시간 순서 (real-time order)** 를 보존한다 — `op A` 가 끝난 후 시작된 `op B` 는 반드시 *A 다음에* 일어난 것처럼 보여야 한다.

**형식적 표현**:
```
History H 가 linearizable 이다
  ⟺ ∃ sequential history S 가 존재해서
     1) S 는 H 의 sequential specification 을 만족 (정합성)
     2) op(A) →_H op(B)  ⇒  op(A) →_S op(B)  (실시간 순서 보존)
        여기서  op(A) →_H op(B)  :=  A 의 response 가 B 의 invocation 보다 먼저
```

**장점/적용**:
- **Composability (조합성)**: 두 객체가 각각 linearizable 이면 두 객체를 함께 사용하는 시스템도 linearizable. Serializability 는 이 성질이 없다 — 이론적으로 가장 강력한 실용적 모델
- **로컬 추론**: 각 객체를 sequential 처럼 추론 가능 → 라이브러리·자료구조 검증에 적합
- **적용**: `java.util.concurrent.ConcurrentHashMap`, `AtomicReference`, ZooKeeper (linearizable writes), etcd (Raft 기반)

**한계**:
- 분산 환경에서 비용 큼 — 모든 노드가 글로벌 순서에 합의 필요 (CAP 의 C 측)
- read 도 quorum / leader 경유 → latency 증가
- 단일 객체 모델 — 여러 객체에 걸친 트랜잭션 의미론은 `serializability` 영역

**실무 적용 예**: Redis `INCR`, AWS DynamoDB `ConditionExpression`, ZooKeeper `create`/`setData`, etcd `Put`, JDK `AtomicLong.compareAndSet`. "단일 키 / 단일 객체에 대한 atomic op" 광고는 사실상 linearizability 광고.

**난이도**: 높음

**Kotlin 예제** — 위반과 회피:
```kotlin
import java.util.concurrent.atomic.AtomicLong

// (1) Linearizability 위반 — non-atomic check-then-act
class UnsafeCounter {
    @Volatile private var v: Long = 0
    fun incrementIfPositive(): Long {
        if (v > 0) {           // T1 read: v=1
            v = v + 1          // T2 가 동시에 v=1 읽고 v=2 로 set → 한 increment 손실
        }
        return v
    }
    // 위반 관측: 클라이언트는 "두 incrementIfPositive 가 모두 성공" 했다고 보지만
    //          counter 는 +1 만 증가 — sequential history 로 설명 불가
}

// (2) Linearizable — CAS retry loop 가 linearization point 제공
class SafeCounter {
    private val v = AtomicLong(0)
    fun incrementIfPositive(): Long {
        while (true) {
            val cur = v.get()
            if (cur <= 0) return cur
            // CAS 성공 순간 = linearization point. 어떤 관찰자도
            // "cur → cur+1" 사이의 중간 상태를 볼 수 없다
            if (v.compareAndSet(cur, cur + 1)) return cur + 1
        }
    }
}
```

**관련 항목**: [serializability](#serializability) (다중 객체 트랜잭션), [sequential-consistency](#sequential-consistency) (실시간 순서 미보장), [happens-before](#happens-before), [`../algorithms/concurrent.md#cas`](../algorithms/concurrent.md#cas), [`database-fundamentals.md#tx-isolation-levels`](database-fundamentals.md#tx-isolation-levels) (DB 격리 4 수준의 실무 구현)

---

<a id="serializability"></a>
## 2. Serializability (직렬성)

**정의**: Bernstein-Hadzilacos-Goodman 1987 에서 정식화된 **DB 트랜잭션의 정합성 모델**. 동시에 실행된 트랜잭션 집합의 결과가, *어떤 순차 (serial) 실행 순서와 등가* 인 결과를 만들어내면 그 schedule 은 serializable. 트랜잭션이 *여러 객체에 걸친 read/write 의 묶음* 이라는 점에서 linearizability (단일 객체) 와 구분된다.

**형식적 표현**:
```
Schedule S 가 serializable 이다
  ⟺ ∃ serial schedule S' 이 존재해서
     output(S) = output(S')  AND  final state(S) = final state(S')

세부 유형:
  - View Serializable (VSR): read-from / final-write 관계 동등 — NP-hard
  - Conflict Serializable (CSR): conflict graph 가 acyclic — 다항시간 검사 가능
       CSR ⊆ VSR ⊆ Serializable
```

**Linearizability vs Serializability — 핵심 차이**:
| 축 | Linearizability | Serializability |
|----|-----------------|------------------|
| 단위 | 단일 객체 op | 트랜잭션 (다중 객체) |
| 실시간 순서 | **강제** (op A 끝 → op B 시작이면 A < B) | **무관** (어떤 순서든 OK) |
| 조합성 | 있음 | **없음** |
| 사용 영역 | 동시 자료구조 / 분산 KV | 관계형 DB / 트랜잭션 시스템 |

→ Strict Serializability = Serializability + Linearizability 의 실시간 순서. Google Spanner, FoundationDB 가 광고하는 "external consistency" 가 이것.

**장점/적용**:
- 트랜잭션을 *순차로 일어난 것* 처럼 추론 → 개발자 멘탈 모델 단순
- ANSI SQL `SERIALIZABLE` 격리 수준의 *이론적* 정의

**한계**:
- **비조합성**: 두 시스템이 각각 serializable 이어도 통합 시스템은 serializable 보장 없음
- 구현 비용: 2PL / SSI 모두 contention / abort 비용 큼
- *순서* 가 자유롭기 때문에 클라이언트가 자기가 방금 commit 한 트랜잭션이 다른 트랜잭션보다 *늦게* 일어난 것처럼 보일 수 있음 → 외부 일관성을 원하면 Strict Serializability 필요

**실무 적용 예**: PostgreSQL `SERIALIZABLE` (SSI 기반), CockroachDB (Strict Serializability 표방), FoundationDB, Google Spanner (TrueTime + Strict Serializability). MySQL InnoDB `SERIALIZABLE` 은 2PL 기반.

**관련 항목**: [`database-fundamentals.md#tx-isolation-levels`](database-fundamentals.md#tx-isolation-levels) (ANSI SQL 4 격리 수준 — Read Uncommitted/Committed/Repeatable Read/Serializable 의 실무 anomaly 매트릭스), [`database-fundamentals.md#ansi-sql-anomaly`](database-fundamentals.md#ansi-sql-anomaly) (Dirty Read/Non-Repeatable/Phantom/Lost Update/Write Skew 정형 정의)

**난이도**: 높음

**SQL 예제** — write skew 가 Snapshot Isolation 에선 가능, Serializable 에선 차단:
```sql
-- 두 의사 모두 on-call. 정책: 최소 1명은 on-call 유지
-- T1, T2 가 동시에 "다른 의사가 있으니 나는 빠져도 OK" 판단 → 둘 다 빠짐 = write skew

-- T1 (의사 Alice):
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT count(*) FROM doctors WHERE on_call = true AND shift = 'NIGHT'; -- 2
UPDATE doctors SET on_call = false WHERE name = 'Alice';
COMMIT;
-- T2 (의사 Bob) 가 동시에:
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT count(*) FROM doctors WHERE on_call = true AND shift = 'NIGHT'; -- 2
UPDATE doctors SET on_call = false WHERE name = 'Bob';
COMMIT;
-- SERIALIZABLE 하에서는 PostgreSQL SSI 가 conflict 감지 → 한 쪽 abort
-- → "어떤 serial 순서로도 양쪽 commit 결과가 나올 수 없음" 을 증명한다
```

**관련 항목**: [linearizability](#linearizability), [snapshot-isolation](#snapshot-isolation) (write skew 허용 모델), [`../algorithms/concurrent.md#mvcc`](../algorithms/concurrent.md#mvcc)

---

<a id="sequential-consistency"></a>
## 3. Sequential Consistency (순차 일관성)

**정의**: Lamport 1979 가 멀티프로세서 정합성 모델로 도입. 모든 프로세서의 메모리 연산이 *어떤 하나의 sequential 순서* 로 일어난 것처럼 보이고, **각 프로세서 입장에서 자신의 program order 가 그 순서 안에 보존** 되면 sequential consistent. Linearizability 와 달리 **실시간 순서는 강제하지 않는다** — 그래서 "더 약한" 모델.

**형식적 표현**:
```
History H 가 sequentially consistent 이다
  ⟺ ∃ legal sequential history S 가 존재해서
     ∀ process P: program_order(P, H) ⊆ S   (P 의 명령 순서가 S 에 보존)

차이:
  Linearizability  =  Sequential Consistency  +  실시간 순서 보존
```

**장점/적용**:
- 멀티프로세서 메모리 모델의 직관적 baseline
- 컴파일러 / 하드웨어 reorder 가 program-order 위배 시 위반 — race 분석의 기준

**한계**:
- 현대 하드웨어는 SC 보다 약한 메모리 모델 채택 (x86 = TSO, ARM/POWER = weaker) → 성능을 위해 reorder 허용
- 실시간 순서 미보장 → 분산 시스템에서 stale read 가능 ("내가 방금 쓴 게 다른 클라이언트에서 보일 수도 안 보일 수도")
- 비조합성

**실무 적용 예**: Java Memory Model 의 `volatile` 변수는 SC 를 *DRF 프로그램에 대해* 제공. C++ `memory_order_seq_cst` 가 SC 보장. Cassandra 의 `LOCAL_QUORUM` read/write 조합은 SC 아님 (eventually consistent).

**난이도**: 중간

**Java 예제** — Dekker 알고리즘과 SC 위반:
```java
// 두 스레드의 mutual exclusion 시도 (단순화된 Dekker)
class DekkerLike {
    int flag1 = 0, flag2 = 0;

    void thread1() {
        flag1 = 1;                  // (a) write
        if (flag2 == 0) {           // (b) read
            // critical section
        }
    }
    void thread2() {
        flag2 = 1;                  // (c) write
        if (flag1 == 0) {           // (d) read
            // critical section
        }
    }
    // SC 가정 하: (a)<(b), (c)<(d) program order 보존
    //   → 어떤 interleaving 도 둘 다 CS 진입을 허용하지 않는다 (mutual exclusion OK)
    // 실제 x86/ARM: store buffer 가 write 를 늦춰 (a),(c) 가 다른 코어에서 늦게 보임
    //   → (b),(d) 모두 0 으로 읽혀서 둘 다 CS 진입 가능 — SC 가 깨짐
    //
    // 회피: volatile (Java) 또는 memory_order_seq_cst (C++) 로 SC 강제
    //   Or: explicit memory barrier (StoreLoad fence)
}
```

**관련 항목**: [linearizability](#linearizability) (SC + 실시간 순서), [happens-before](#happens-before) (Java SC for DRF), [`../algorithms/concurrent.md#memory-barriers`](../algorithms/concurrent.md#memory-barriers)

---

<a id="causal-consistency"></a>
## 4. Causal Consistency (인과 일관성)

**정의**: Ahamad et al. 1995 가 정식화. **인과관계로 묶인 연산만 모든 프로세스가 같은 순서로 보고**, *동시 (concurrent)* 인 연산은 프로세스마다 다른 순서로 볼 수 있다. Happens-Before 관계가 보존되는 가장 약한 유용한 모델 — eventual consistency + causality.

**형식적 표현**:
```
op(A) →_hb op(B)  ⇒  모든 process 가 A 를 B 보다 먼저 관측

A ∥ B  (A 와 B 가 concurrent, 즉 인과관계 없음)  ⇒  관측 순서 free
```

여기서 happens-before 는 Lamport 의 partial order: 같은 프로세스 내 program order ∪ 메시지 send→receive ∪ transitive closure. Vector clock 으로 추적 가능.

**장점/적용**:
- "사용자 A 가 게시한 댓글이 사용자 B 가 게시한 답글보다 늦게 보이는" 비논리 차단
- High availability 와 양립 (CAP 의 AP 측에서 가장 강한 모델 — COPS 논문)
- 지리적으로 분산된 시스템에서 linearizability 비용 회피하면서 인과적 정합성 유지

**한계**:
- "concurrent 한 write" 충돌 해결은 별도 정책 필요 (LWW / CRDT 등)
- vector clock 메타데이터 오버헤드 (process 수에 비례)
- "내가 본 적 없는 답글에 reply" 같은 hidden causality 추적 불가능 (out-of-band 정보)

**실무 적용 예**: COPS, Eiger (Princeton 분산 KV), Riak (causal context), MongoDB Causal Consistency 세션 옵션, Azure Cosmos DB 의 5 정합성 레벨 중 *Consistent Prefix* 와 *Session* 이 인과 관련.

**난이도**: 중간

**pseudo-code 예제** — Vector clock 기반 causal delivery:
```kotlin
// Vector Clock 기반 causal broadcast — 인과 순서 보장
data class VClock(val n: Int) {
    val v = IntArray(n)
    fun increment(self: Int) { v[self]++ }
    fun merge(other: IntArray) {
        for (i in v.indices) v[i] = maxOf(v[i], other[i])
    }
    fun canDeliver(from: Int, msgVC: IntArray, self: Int): Boolean {
        // 조건 1: msgVC[from] == localVC[from] + 1  (직전 메시지)
        // 조건 2: ∀ k ≠ from: msgVC[k] ≤ localVC[k] (인과 선행 메시지 모두 도착)
        if (msgVC[from] != v[from] + 1) return false
        for (k in v.indices) if (k != from && msgVC[k] > v[k]) return false
        return true
    }
}
// Alice 가 "post X" → Bob 이 "X 에 대한 reply" 보냄
// Causal: Charlie 는 X 가 도착해야만 reply 를 deliver — 무한 hold 가능
// Concurrent (Alice "post X" || Dan "post Y"): Charlie 가 X,Y 또는 Y,X 어느 순서든 OK
```

**관련 항목**: [eventual-consistency](#eventual-consistency) (causal 은 eventual 의 강화), [happens-before](#happens-before) (이론적 기반), [`../algorithms/distributed.md`](../algorithms/distributed.md) (Vector Clock)

---

<a id="eventual-consistency"></a>
## 5. Eventual Consistency (최종 일관성)

**정의**: Werner Vogels 2009 가 산업적으로 정착시킨 약한 정합성 모델. *update 가 멈춘 후 충분한 시간이 흐르면* 모든 replica 가 동일 상태로 수렴한다 (convergence). 그 사이 시간 동안 read 가 stale 한 값을 반환할 수 있음을 **명시적으로 허용**. CAP 의 AP 측에서 가용성 우선 시 가장 흔한 선택.

**형식적 표현**:
```
∀ replica R₁, R₂:
  (∃ T₀ 이후 어떤 write 도 없음)  ⇒  ∃ T₁ ≥ T₀ 에서 state(R₁, T₁) = state(R₂, T₁)
```

"eventually" 의 의미: write quiescence 후 finite time 내 수렴. 시간 boundary 는 모델에 미포함.

**세부 강화 변형**:
- **Read-your-writes**: 자신이 쓴 값은 즉시 본인이 다시 읽을 때 보장
- **Monotonic reads**: 한 클라이언트의 연속 read 가 시간 역행 안 함
- **Monotonic writes**: 한 클라이언트의 write 가 순서대로 적용
- **Causal**: 위 모두 + 인과 순서 ([causal-consistency](#causal-consistency))

**장점/적용**:
- Availability + Partition tolerance 최대화
- Write latency 최소 (local replica 에 쓰고 비동기 전파)
- 광역 분산·offline-first 모바일 앱에서 필수

**한계**:
- 충돌 해결 정책 필요: Last-Write-Wins, Vector Clock, CRDT, application-level merge
- "내가 방금 댓글 달았는데 새로고침하면 안 보임" 같은 UX 문제
- 정합성 검증·디버깅 난해

**실무 적용 예**: Amazon Dynamo (2007), DynamoDB default read, Cassandra `ONE`, Riak, Voldemort, DNS 캐시, CDN edge, CRDT (Redis `CRDT`, Automerge, Yjs).

**난이도**: 중간

**Kotlin 예제** — LWW Register 와 수렴:
```kotlin
// Last-Write-Wins Register (간단한 CRDT) — eventually consistent
data class LWWReg<T>(val value: T, val timestamp: Long, val replicaId: Int) {
    // merge 는 commutative / associative / idempotent → 어떤 순서로 와도 같은 결과
    fun merge(other: LWWReg<T>): LWWReg<T> = when {
        this.timestamp > other.timestamp -> this
        this.timestamp < other.timestamp -> other
        // 동일 timestamp 시 replicaId 로 tie-break (deterministic)
        this.replicaId > other.replicaId -> this
        else -> other
    }
}
// Replica A: x = LWWReg("a", 100, 1)
// Replica B: x = LWWReg("b", 101, 2)
// 양쪽 모두 상대 update 를 merge 하면 결국 LWWReg("b", 101, 2) 로 수렴
// — 단, "a" write 는 영구 손실. 정합성보다 가용성 우선의 trade-off
```

**관련 항목**: [causal-consistency](#causal-consistency) (eventual + causality), [linearizability](#linearizability) (반대 극단), [`../algorithms/concurrent.md#mvcc`](../algorithms/concurrent.md#mvcc)

---

<a id="snapshot-isolation"></a>
## 6. Snapshot Isolation (스냅샷 격리) / Serializable SI

**정의**: Berenson et al. SIGMOD 1995 ("A Critique of ANSI SQL Isolation Levels") 에서 정식화. 트랜잭션이 *시작 시점의 일관된 snapshot* 을 본다. 다른 트랜잭션이 그 사이 commit 해도 자기 read 는 변하지 않으며, write 충돌 (같은 행을 두 트랜잭션이 update) 시 First-Committer-Wins 또는 First-Updater-Wins 로 한 쪽 abort. MVCC 의 표준 산물.

**형식적 표현**:
```
T 가 시작 시각 = start(T), commit 시각 = commit(T) 일 때:
  T 의 read 는 { x : ∃ Tᵢ. commit(Tᵢ) < start(T) ∧ Tᵢ wrote x } 의 가장 최근 값
  T₁, T₂ 가 같은 객체 write ∧ [start(Tᵢ), commit(Tᵢ)] 가 겹침  ⇒  하나 abort

→ SI 는 다음을 차단: Dirty Read, Non-repeatable Read, Phantom Read (일반 정의 기준)
→ 차단 못 함: Write Skew (예: 위 의사 on-call 예제)
```

**Serializable Snapshot Isolation (SSI)** — Cahill 2008. SI 위에 *dangerous structure* (rw-conflict cycle) 감지를 추가해 write skew 까지 차단. PostgreSQL `SERIALIZABLE` 의 구현.

**장점/적용**:
- Reader 가 writer 를 block 하지 않음 / 그 반대도 안 함 (MVCC 의 약속)
- 기존 SI 시스템의 *대부분의* 비정합 anomaly 차단
- SSI 는 성능 손실 작게 serializability 달성

**한계**:
- Vanilla SI: **Write Skew anomaly** 존재 — serializable 가정 깨짐
- Storage overhead (다중 버전 보관 + GC/VACUUM)
- Long-running read transaction 이 GC 차단 시 bloat

**실무 적용 예**: Oracle `SERIALIZABLE` 은 사실상 SI (write skew 가능 — Berenson 비판의 핵심), PostgreSQL `REPEATABLE READ` 가 SI, PostgreSQL `SERIALIZABLE` 이 SSI (Cahill 알고리즘), MS SQL Server `SNAPSHOT` 격리, FoundationDB, CockroachDB.

**난이도**: 높음

**SQL 예제** — Vanilla SI 의 Write Skew:
```sql
-- 정책: doctors.on_call=true 인 행이 항상 ≥ 1 (병원 24시간 운영)
-- 현재 2명이 on_call. SI 하에서:

-- T1: BEGIN; SELECT count(*) WHERE on_call;  -- snapshot=2
--     UPDATE doctors SET on_call=false WHERE id=1;
-- T2: BEGIN; SELECT count(*) WHERE on_call;  -- snapshot=2 (T1 영향 못 봄)
--     UPDATE doctors SET on_call=false WHERE id=2;
-- T1: COMMIT;  -- 성공 (id=1 만 변경)
-- T2: COMMIT;  -- 성공 (id=2 만 변경, write 충돌 없음 — 다른 행)
-- 결과: 둘 다 false → 정책 위반. write skew anomaly.

-- 회피 1: PostgreSQL SSI ( SERIALIZABLE ) — rw-conflict cycle 감지로 한쪽 abort
-- 회피 2: SELECT ... FOR UPDATE 로 read 도 lock — 2PL 식 차단
-- 회피 3: 응용 레벨 invariant 보장 — 갱신 전 명시적 lock row
```

**관련 항목**: [serializability](#serializability) (SSI 가 도달하는 목표), [`../algorithms/concurrent.md#mvcc`](../algorithms/concurrent.md#mvcc), [linearizability](#linearizability) (Strict Serializability)

---

<a id="happens-before"></a>
## 7. Happens-Before Relation (선후관계)

**정의**: Lamport CACM 1978 의 partial order. 두 이벤트의 "원인-결과" 관계를 형식화. **세 가지 규칙**:
1. **Program Order**: 같은 프로세스 내에서 A 가 B 보다 *코드상 먼저* 면 `A →hb B`
2. **Synchronization Order**: A 가 message send, B 가 그 receive 면 `A →hb B` (또는 lock release → 후속 acquire, volatile write → 후속 read 등)
3. **Transitivity**: `A →hb B ∧ B →hb C  ⇒  A →hb C`

이 관계에 들어가지 않는 두 이벤트는 **concurrent** (`A ∥ B`) — 누가 먼저인지 정의되지 않음.

**형식적 표현**:
```
→hb ⊆ Events × Events  is a strict partial order:
  - irreflexive: ¬(A →hb A)
  - antisymmetric: A →hb B ⇒ ¬(B →hb A)
  - transitive: A →hb B ∧ B →hb C ⇒ A →hb C

DRF (Data Race Free) 정리:
  프로그램이 → SC under DRF ⇔  모든 conflicting access 가 →hb 로 순서 매겨짐
  (Java Memory Model, C++11 Memory Model 의 기반 정리)
```

**장점/적용**:
- 메모리 모델·인과 일관성·distributed snapshot 의 공통 언어
- "데이터 race 없는 프로그램은 SC 처럼 추론 가능" 정리의 핵심
- Vector clock 으로 happens-before 를 *추적 가능* — distributed system 디버깅 도구의 기반

**한계**:
- *Hidden causality*: 시스템 밖 통신 (전화·메일) 로 인과 형성 시 추적 불가
- Partial order — 모든 이벤트 쌍에 순서 정의되지 않음 (vs total order)
- 분산에서 한 노드가 happens-before 를 완벽 추적하려면 vector clock 필요 (O(N) 메타데이터)

**실무 적용 예**: Java Memory Model 의 happens-before 규칙 (volatile, synchronized, Thread.start, Thread.join), Go memory model, C++11 `memory_order_acquire`/`release`, Cassandra hinted handoff, Vector clock (Dynamo / Riak), Git commit graph (parent→child 가 happens-before).

**난이도**: 중간

**Java 예제** — happens-before 위반 vs 회피:
```java
// (1) 위반: happens-before 없이 공유 변수 접근 = data race
class Broken {
    boolean ready = false;
    int value = 0;
    void writer() {
        value = 42;          // (a)
        ready = true;        // (b) — 단순 write, happens-before 없음
    }
    void reader() {
        if (ready) {         // (c)
            // (a) 와 (c) 사이에 happens-before 가 없음 → JIT/하드웨어가
            // reorder 가능. value=0 으로 읽힐 수 있다 (DRF 정리 위배)
            System.out.println(value);
        }
    }
}

// (2) 회피: volatile 이 happens-before edge 생성
class Fixed {
    int value = 0;
    volatile boolean ready = false;  // (b) write → (c) read 에 happens-before

    void writer() {
        value = 42;             // (a) program order → (b)
        ready = true;           // (b) volatile write
    }
    void reader() {
        if (ready) {            // (c) volatile read
            // JMM: (a) →hb (b) →hb (c) →hb (d) → (a) 의 효과가 (d) 에 보임
            System.out.println(value);  // (d) 반드시 42
        }
    }
}
```

**관련 항목**: [sequential-consistency](#sequential-consistency) (DRF 정리), [causal-consistency](#causal-consistency) (분산 hb), [race-condition](#race-condition), [`../algorithms/concurrent.md#memory-barriers`](../algorithms/concurrent.md#memory-barriers)

---

<a id="liveness-safety"></a>
## 8. Liveness vs Safety Properties (진행성 vs 안전성)

**정의**: Lamport 가 정형 검증 문헌에서 정착시킨 분류. 동시 / 분산 시스템의 모든 *temporal property* 는 이 두 클래스의 conjunction 으로 분해 가능 (Alpern-Schneider 정리, 1985).

| 클래스 | 슬로건 | 형식 | 위반 관측 |
|---|---|---|---|
| **Safety** | "Something bad never happens" | □ ¬Bad | **유한 prefix** 로 위반 확인 가능 |
| **Liveness** | "Something good eventually happens" | ◇ Good | **무한 trace** 로만 위반 확인 가능 |

**형식적 표현**:
```
Safety  P : ∀ trace σ. P(σ)  ⇒  ∀ prefix σ' ≤ σ. ∃ extension σ'' . P(σ' · σ'')
  의미: 위반은 유한 시점에 확정됨 — 그 시점 이후 어떻게 가도 회복 불가

Liveness P : ∀ finite prefix σ. ∃ extension σ' . P(σ · σ')
  의미: 어떤 유한 시점에서도 아직 만족 가능 — "지금까지 안 일어났을 뿐"

Alpern-Schneider: ∀ property P. ∃ Safety S, Liveness L. P = S ∩ L
```

**예시 매핑**:
- *Mutual exclusion*: "두 스레드가 동시에 CS 진입 안 함" — Safety
- *Starvation freedom*: "CS 진입을 요청한 모든 스레드가 결국 진입" — Liveness
- *Deadlock freedom*: "시스템이 결국 진행" — Liveness
- *Type safety / Invariant*: Safety
- *Termination*: Liveness
- *Linearizability*: Safety

**장점/적용**:
- 검증 도구가 분리 처리 — Safety 는 invariant / model checking, Liveness 는 fairness 가정 + temporal logic (LTL)
- Bug 보고 시 "이 violation 은 safety / liveness 중 무엇인가" 로 영향도·재현 난이도 분류 가능
- Lock-free 알고리즘은 보통 deadlock-freedom (liveness 약) 또는 wait-freedom (liveness 강) 을 *증명* 한다

**한계**:
- 실제 시스템에서 liveness 는 fairness 가정 없이는 증명 불가 (스케줄러가 한 프로세스를 영원히 굶기지 않음 등)
- "결국" 의 시간 boundary 가 없으면 useful 한 latency 보장은 별도 (real-time property)

**실무 적용 예**: TLA+ / TLC 모델 체커, SPIN / Promela LTL property, Coq / Isabelle 정형 검증, lock-free 자료구조의 *Wait-Free* (모든 스레드 유한 단계 내 완료, 강 liveness) vs *Lock-Free* (어떤 스레드가 유한 단계 내 완료, 약 liveness) vs *Obstruction-Free* (간섭 없으면 완료).

**난이도**: 중간

**TLA+ 스타일 pseudo-code 예제**:
```
\* Mutual Exclusion 알고리즘 검증
VARIABLES pc, flag, turn
Init == /\ pc = [p \in {0,1} |-> "idle"]
        /\ flag = [p \in {0,1} |-> FALSE]
        /\ turn = 0

\* SAFETY: 절대 두 프로세스가 동시에 CS 에 있지 않다
MutualExclusion == \A p1, p2 \in {0,1}:
    (p1 # p2 /\ pc[p1] = "cs") => pc[p2] # "cs"

\* LIVENESS: trying 상태에 들어간 프로세스는 결국 CS 에 진입한다
\* Fairness 가정 필요: WF_vars(Step(p))
StarvationFreedom == \A p \in {0,1}:
    (pc[p] = "trying") ~> (pc[p] = "cs")

\* TLC 모델 체커:
\*   MutualExclusion 위반 → 유한 trace counterexample (safety)
\*   StarvationFreedom 위반 → 무한 loop 안에서 p 가 영원히 trying (liveness)
```

**관련 항목**: [deadlock-conditions](#deadlock-conditions) (liveness 위반), [linearizability](#linearizability) (safety), [`../patterns/concurrency.md`](../patterns/concurrency.md) (lock-free / wait-free 분류)

---

<a id="deadlock-conditions"></a>
## 9. Deadlock 4 Conditions (교착상태 4 조건 — Coffman)

**정의**: Coffman / Elphick / Shoshani 1971 "System Deadlocks" 가 식별한 deadlock 발생을 위한 **4 가지 필요 조건**. 네 조건이 *동시에* 성립하면 deadlock 가능. 하나라도 깨면 deadlock 불가능 — 이것이 **deadlock prevention** 의 이론적 출발점.

**4 조건**:
| 조건 | 영문명 | 의미 |
|---|---|---|
| 1 | **Mutual Exclusion** | 자원이 *non-shareable* — 동시에 한 프로세스만 보유 |
| 2 | **Hold and Wait** | 프로세스가 자원을 보유한 채 다른 자원 *추가 요청* |
| 3 | **No Preemption** | 자원을 *강제 회수* 불가, 보유자가 자발적 해제만 |
| 4 | **Circular Wait** | 프로세스 그래프에 *순환 대기* 존재: P₁→P₂→...→Pₙ→P₁ |

**형식적 표현**:
```
Resource-Allocation Graph (RAG):
  Nodes = Processes ∪ Resources
  Edges = "request" (P → R) ∪ "allocation" (R → P)

Deadlock ⇔ RAG 에 cycle 존재 (single-instance resource 경우)
        ⇔ cycle ∧ 자원 가용성 부족 (multi-instance 경우 — Banker's algorithm 필요)
```

**대응 전략** (조건별 1:1 대응):
| 전략 | 깨는 조건 | 방법 |
|---|---|---|
| Prevention 1 | Mutual Exclusion | Shareable 자원으로 전환 (read lock 등). 적용 제한적 |
| Prevention 2 | Hold-and-Wait | 모든 자원 *한 번에* 요청 (all-or-nothing). 자원 활용도 ↓ |
| Prevention 3 | No Preemption | 자원 강제 회수 + 재시작 (DB transaction abort) |
| Prevention 4 | Circular Wait | **자원 순서화** — 모든 프로세스가 동일한 global order 로 acquire |
| Avoidance | (모든 조건 OK 라도 회피) | Banker's Algorithm — safe state 만 허용 |
| Detection | (다 허용 후 사후 처리) | RAG cycle 검출 + recovery (한 프로세스 kill) |

**장점/적용**:
- 진단의 공통 언어 — production deadlock 보고 시 "어느 조건이 무너졌나" 로 빠르게 좁힘
- Lock ordering ([circular wait 방지](#deadlock-conditions)) 은 가장 실용적 prevention

**한계**:
- Multi-instance resource 에선 cycle 만으로 deadlock 단정 불가
- *Livelock* 은 4 조건과 별개 — 모두 진행하지만 의미 있는 진행 없음
- 분산 시스템의 *distributed deadlock* 은 RAG 자체 구축 비용 큼

**실무 적용 예**: DBMS 의 deadlock detector (wait-for graph cycle), Java `jstack` 으로 thread deadlock 진단, Linux kernel `lockdep` 의 lock acquisition order 추적, MySQL InnoDB `SHOW ENGINE INNODB STATUS` deadlock log.

**난이도**: 중간

**Kotlin 예제** — Circular Wait 발생과 Lock Ordering 회피:
```kotlin
// (1) Deadlock 발생 — 두 lock 을 반대 순서로 잡는다
class TransferBroken(val from: Account, val to: Account) {
    fun transfer(amount: Long) {
        synchronized(from) {       // T1: from=A, to=B → lock A
            Thread.sleep(10)       // T2: from=B, to=A → lock B  (동시)
            synchronized(to) {     // T1: B 요청 (T2 보유) — wait
                from.balance -= amount   // T2: A 요청 (T1 보유) — wait
                to.balance += amount     // → Circular Wait → Deadlock
            }
        }
    }
}

// (2) 회피 — 자원 순서화 (Coffman 조건 4 차단)
class TransferSafe(val from: Account, val to: Account) {
    fun transfer(amount: Long) {
        // Account 의 id 로 total order 정의 → 모든 스레드가 같은 순서로 acquire
        val (first, second) = if (from.id < to.id) from to to else to to from
        synchronized(first) {
            synchronized(second) {
                from.balance -= amount
                to.balance += amount
            }
        }
        // 모든 transfer 가 id 오름차순으로 lock → RAG cycle 형성 불가
    }
}
```

**관련 항목**: [liveness-safety](#liveness-safety) (deadlock = liveness 위반), [`../patterns/concurrency.md`](../patterns/concurrency.md) (Lock Ordering, Lock-Free), [`../algorithms/concurrent.md#cas`](../algorithms/concurrent.md#cas) (lock-free 가 조건 1 자체를 회피)

---

<a id="race-condition"></a>
## 10. Race Condition / Data Race / Atomicity Violation

**정의**: **Race condition (경쟁 상태)** 과 **Data race (데이터 경쟁)** 는 자주 혼용되지만 *다르다*. Netzer & Miller 1992 가 정식 구분.

| 개념 | 정의 | 예 |
|---|---|---|
| **Data Race** | 같은 메모리 위치에 대한 두 *conflicting* 접근 (≥1 write) 이 happens-before 로 순서 매겨지지 않음 — **메모리 모델** 수준 정의 | 두 스레드가 동기화 없이 같은 변수 write |
| **Race Condition** | 결과의 정확성이 *상대적 실행 타이밍* 에 의존하는 *논리* 결함 — **알고리즘** 수준 정의 | check-then-act, read-modify-write, TOCTOU |

→ Data race 없는 프로그램에도 race condition 존재 가능 (atomic op 만 써도 논리 결함 가능).
→ Race condition 없는 프로그램에도 data race 존재 가능 (benign race — 실제로는 거의 위험).

**3 차원 분류** (Lu et al. 2008, "Learning from Mistakes — A Comprehensive Study on Real World Concurrency Bug Characteristics"):
| 차원 | 위반 유형 | 의미 |
|---|---|---|
| **Atomicity** | Atomicity Violation | 함께 일어나야 할 op 묶음 사이에 다른 스레드 개입 (TOCTOU, check-then-act) |
| **Order** | Order Violation | A 이후 B 가 일어나야 하는데 순서가 바뀜 (uninitialized read) |
| **Visibility** | Visibility Violation | 한 스레드 write 가 다른 스레드에 *영원히* 안 보임 (메모리 모델 / 캐시 문제) |

**형식적 표현**:
```
Data Race(x) ⇔ ∃ accesses a, b on x:
  - thread(a) ≠ thread(b)
  - (a writes x ∨ b writes x)
  - ¬(a →hb b) ∧ ¬(b →hb a)   (concurrent under happens-before)

Race Condition(spec) ⇔ ∃ schedule σ. output(σ) ≠ spec
  (스케줄러 선택에 따라 spec 위반 결과 가능)
```

**장점/적용**:
- 동시성 bug 분류 — 어떤 도구로 잡을 수 있나 결정
  - Data race → TSan (ThreadSanitizer), Helgrind, FastTrack, Java `-XX:+UseRaceDetector`
  - Atomicity violation → Stress test, ConTest, model checking
  - Order violation → Code review + invariant 명시
- happens-before 와 짝 — DRF 프로그램은 SC 처럼 추론 가능

**한계**:
- Data race 검출기는 false negative (실행 안 한 path 못 잡음) / false positive (benign race) 둘 다 존재
- Race condition 은 데이터 race 검출기로 못 잡는 경우 다수 — 의미적 race 는 spec 필요

**실무 적용 예**: Google ThreadSanitizer (Chromium / Go 내장), Java `jcstress`, Rust 의 *fearless concurrency* (소유권 시스템이 data race 를 컴파일 타임 차단), Kotlin coroutines 의 `Mutex` / `Atomic*Ref`, TOCTOU 보안 취약점 (CVE-2009-1894 등).

**난이도**: 중간

**Kotlin / Java 예제** — 3 차원 모두 보여주는 코드:
```kotlin
import java.util.concurrent.atomic.AtomicReference

// (A) Atomicity Violation — 개별 op 는 atomic, 묶음은 아님
class Cache {
    private val map = java.util.concurrent.ConcurrentHashMap<String, String>()
    // putIfAbsent 가 atomic 함에도 check-then-act 로 race
    fun getOrCompute(k: String, f: () -> String): String {
        val cached = map[k]                   // (1) atomic read
        if (cached != null) return cached     // (2) check
        val fresh = f()                       // (3) — 다른 스레드가 동안 put 가능
        map[k] = fresh                        // (4) atomic write — 덮어쓰기 race
        return fresh
        // 회피: map.computeIfAbsent(k) { f() }  — 묶음을 atomic 으로
    }
}

// (B) Order Violation — 초기화 전 사용
class OrderBug {
    private var config: String? = null
    init {
        Thread { config = loadConfig() }.start()   // (1) 비동기 초기화
        // join() 없이 진행 — config 가 null 인 채로 (2) 가 실행될 수 있다
    }
    fun use() = config!!.length   // (2) NPE risk — order violation
    private fun loadConfig() = "x"
}

// (C) Visibility Violation — happens-before 부재
class VisibilityBug {
    private var stop = false              // non-volatile
    fun runUntilStopped() {
        while (!stop) { /* hot loop */ }  // JIT 가 stop 을 register 로 호이스트 가능
        // → 다른 스레드가 stop=true 해도 *영원히* 안 보임 (visibility)
    }
    fun stopIt() { stop = true }
    // 회피: @Volatile var stop = false   → write 에 happens-before edge 생성
}
```

**관련 항목**: [happens-before](#happens-before) (data race 의 정의 기반), [linearizability](#linearizability) (atomic op 으로 race condition 회피), [sequential-consistency](#sequential-consistency) (DRF → SC), [`../algorithms/concurrent.md#cas`](../algorithms/concurrent.md#cas), [`../patterns/concurrency.md`](../patterns/concurrency.md) (Monitor / STM)

---

## 종합 비교표

### 정합성 모델 강도 (강 → 약)

```
Strict Serializability   (Spanner, FoundationDB)
        │  실시간 순서 보장 + 트랜잭션
        ▼
Serializability          (PostgreSQL SERIALIZABLE = SSI)
        │  실시간 순서 ✗, 트랜잭션 단위 직렬 등가
        ▼
Snapshot Isolation       (PostgreSQL REPEATABLE READ, Oracle SERIALIZABLE)
        │  Write skew anomaly 허용
        ▼
Linearizability          (etcd, ZooKeeper write, AtomicReference)
        │  단일 객체, 실시간 순서
        ▼
Sequential Consistency   (Java volatile under DRF)
        │  Program order + 어떤 인터리빙, 실시간 순서 ✗
        ▼
Causal Consistency       (COPS, MongoDB causal session, Riak)
        │  happens-before 만 보존
        ▼
Eventual Consistency     (DynamoDB default, Cassandra ONE)
           Convergence only — write quiescence 후 수렴
```

### 항목 - 적용 영역 매핑

| 항목 | 단일 객체 (자료구조) | DB 트랜잭션 | 분산 KV | 메모리 모델 | 정형 검증 |
|---|:---:|:---:|:---:|:---:|:---:|
| Linearizability | ★★★ | | ★★★ | | ★ |
| Serializability | | ★★★ | ★★ | | |
| Sequential Consistency | ★★ | | | ★★★ | ★ |
| Causal Consistency | | | ★★★ | | |
| Eventual Consistency | | | ★★★ | | |
| Snapshot Isolation | | ★★★ | | | |
| Happens-Before | ★★★ | | ★★ | ★★★ | ★★ |
| Liveness vs Safety | ★★ | ★ | ★★ | ★ | ★★★ |
| Deadlock 4 Conditions | ★★★ | ★★★ | ★★ | | ★ |
| Race Condition | ★★★ | ★★ | ★ | ★★★ | ★★ |

### 도구 ↔ 이론 매핑

| 도구 | 이론적 기반 |
|---|---|
| TLA+, SPIN | Liveness vs Safety, Happens-Before, Linearizability |
| ThreadSanitizer | Data Race (Happens-Before) |
| Jepsen | Linearizability, Causal Consistency, Serializability (Elle) |
| Coq, Isabelle/HOL | Liveness vs Safety 형식 증명 |
| Java JCStress | Memory model conformance (Sequential Consistency, Happens-Before) |
| Verifast, Iris | Concurrent separation logic — Linearizability 증명 |
| Vector Clock | Causal Consistency, Happens-Before |
| MVCC | Snapshot Isolation, Serializability (SSI) |

---

## 학습 경로 권장 순서

1. **입문**: [race-condition](#race-condition) → [happens-before](#happens-before) → [liveness-safety](#liveness-safety)
2. **메모리 모델**: [sequential-consistency](#sequential-consistency) → [linearizability](#linearizability)
3. **트랜잭션 / DB**: [snapshot-isolation](#snapshot-isolation) → [serializability](#serializability)
4. **분산 시스템**: [eventual-consistency](#eventual-consistency) → [causal-consistency](#causal-consistency)
5. **종합 진단**: [deadlock-conditions](#deadlock-conditions)

각 단계에서 패턴([`../patterns/concurrency.md`](../patterns/concurrency.md)) · 알고리즘([`../algorithms/concurrent.md`](../algorithms/concurrent.md)) 의 해당 구현으로 *이론과 구현의 매핑* 을 익히는 것을 권장.
