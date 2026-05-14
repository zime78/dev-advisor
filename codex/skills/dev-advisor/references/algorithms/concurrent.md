# 동시성 알고리즘 (Concurrent Algorithms)

다중 스레드/코어가 공유 메모리에 안전하고 효율적으로 접근하기 위한 알고리즘입니다. 잠금(lock) 기반 접근의 한계를 극복하기 위한 lock-free / wait-free 기법, 메모리 모델, 동시성 자료구조의 핵심 빌딩블록을 다룹니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [cas](#cas) | CAS (Compare-And-Swap) | 비교-교환 | 중간 |
| [ll-sc](#ll-sc) | LL-SC (Load-Linked / Store-Conditional) | LL-SC | 높음 |
| [rcu](#rcu) | RCU (Read-Copy-Update) | RCU | 높음 |
| [mvcc](#mvcc) | MVCC (Multi-Version Concurrency Control) | 다중 버전 동시성 제어 | 높음 |
| [hazard-pointer](#hazard-pointer) | Hazard Pointer | 위험 포인터 | 높음 |
| [lock-free-queue](#lock-free-queue) | Lock-Free Queue (Michael-Scott) | 비잠금 큐 | 높음 |
| [work-stealing](#work-stealing) | Work-Stealing | 작업 훔치기 | 중간 |
| [seqlock](#seqlock) | Seqlock | 시퀀스 잠금 | 중간 |
| [memory-barriers](#memory-barriers) | Memory Barriers | 메모리 배리어 | 높음 |
| [aba-problem](#aba-problem) | ABA Problem 해법 | ABA 문제 해결 | 높음 |

---

<a id="cas"></a>
## 1. CAS (Compare-And-Swap, 비교-교환)

**목적**: 단일 메모리 위치에 대한 원자적 read-modify-write 연산. 모든 lock-free 알고리즘의 기본 원자 연산

**시간 복잡도**: O(1) 평균, contention 시 O(스레드 수)

**공간 복잡도**: O(1)

**특징**:
- 의미: `if (*addr == expected) { *addr = new; return true; } else { return false; }` 가 원자적
- x86: `LOCK CMPXCHG`, ARM: `LL-SC` 기반 모방
- 실패 시 재시도(retry loop) — Spin
- Java: `Atomic*.compareAndSet`, C++: `std::atomic::compare_exchange_*`
- ABA 문제 발생 가능 (`aba-problem` 참조)

**장점**:
- lock 없이 강한 동기화 (lock-free)
- deadlock 불가능
- 짧은 critical section 에서 lock 보다 빠름
- 모든 lock-free 자료구조의 기반

**단점**:
- contention 높으면 retry 비용 폭발
- ABA 문제
- 단일 word 만 원자 (DCAS 는 별도 지원 필요)
- 잘못 쓰면 silent bug — 메모리 모델 이해 필수

**활용 예시**:
- `java.util.concurrent.atomic.*` 전체 (AtomicReference, AtomicLong, AtomicInteger)
- `ConcurrentHashMap` size counter, bucket update
- Lock-Free Queue / Stack
- 분산 ID 생성 (Snowflake 등)의 sequence counter

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import java.util.concurrent.atomic.AtomicReference
import java.util.concurrent.atomic.AtomicLong

// 1) AtomicReference 로 단순 lock-free 객체 교체
class LockFreeBox<T>(initial: T) {
    private val ref = AtomicReference(initial)

    fun get(): T = ref.get()

    // CAS 기반 update — 함수가 멱등하지 않으면 lambda 가 여러 번 호출될 수 있음
    fun update(f: (T) -> T): T {
        while (true) {
            val current = ref.get()
            val next = f(current)
            if (ref.compareAndSet(current, next)) return next
            // 실패 시 다른 스레드가 변경 — 재시도
        }
    }
}

// 2) AtomicLong 카운터 — synchronized 보다 빠른 hot counter
class FastCounter {
    private val value = AtomicLong(0)
    fun increment(): Long = value.incrementAndGet()
    fun add(delta: Long): Long {
        while (true) {
            val cur = value.get()
            val next = cur + delta
            if (value.compareAndSet(cur, next)) return next
        }
    }
}

// 의사코드 - CAS 의 본질:
//   atomic_cas(addr, expected, new):
//     LOCK
//     if (*addr == expected):
//         *addr = new
//         return true
//     return false
//     UNLOCK
//   (CPU 가 cache coherence + memory ordering 으로 보장)
//
// 주의:
//   - lambda 안에서 I/O, mutable side effect 금지 (CAS 실패 시 재실행)
//   - 매우 높은 contention 시 LongAdder / Striped64 가 더 빠름
```

**관련 알고리즘**: LL-SC, DCAS, Hazard Pointer, ABA Problem

---

<a id="ll-sc"></a>
## 2. LL-SC (Load-Linked / Store-Conditional)

**목적**: CAS 대안인 약 RISC 아키텍처의 원자 연산 — ABA 문제를 하드웨어 수준에서 회피

**시간 복잡도**: O(1) 정상, contention 시 재시도

**공간 복잡도**: O(1) + CPU 내부 reservation register

**특징**:
- 두 명령어 쌍: **LL(load-linked)** + **SC(store-conditional)**
- LL: 주소를 reservation 으로 마킹하면서 읽음
- SC: 마킹이 유효(중간에 누가 안 건드림)할 때만 쓰기 성공
- 중간에 같은 cache line 에 누가 쓰면 reservation 무효 → SC 실패
- ARM (`LDREX/STREX`, `LDAXR/STLXR`), PowerPC (`LWARX/STWCX`), MIPS, RISC-V

**장점**:
- ABA 문제 자연 회피 (값이 아닌 reservation 추적)
- DCAS / 멀티-word 원자성 흉내 가능 (제한적)
- CAS 보다 의미론적으로 강함

**단점**:
- spurious failure 가능 (false sharing, context switch 로 reservation 손실)
- 직접 사용 불가 — 컴파일러/JVM/런타임이 추상화
- x86 에는 없음 (CMPXCHG 만)
- 코드가 retry loop 강제

**활용 예시**:
- ARM/AArch64 의 `std::atomic` 구현 backend
- JVM 의 `Unsafe.compareAndSwap*` → ARM 에서는 LL-SC 로 컴파일
- Linux kernel 의 atomic_* operation
- 임베디드/모바일 SoC 의 동시성 primitive

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// LL-SC 는 직접 노출 안 됨 — JVM 이 ARM 에서 자동 사용
// 의사코드로 의미 표현
//
// asm pseudo (ARMv8):
//   retry:
//       LDAXR  x0, [x1]          ; LL: load + acquire + mark
//       ADD    x0, x0, #1
//       STLXR  w2, x0, [x1]      ; SC: store + release + check reservation
//       CBNZ   w2, retry         ; w2 != 0 → SC 실패 → 재시도
//
// 이 시퀀스가 atomic increment.
// 중간에 다른 코어가 [x1] cache line 에 쓰면 reservation 무효 → STLXR 실패.

// Kotlin/Java 관점: 그냥 AtomicInteger.incrementAndGet() 사용 — JVM 이 알아서 LL-SC 로 컴파일
class LLSCDemo {
    private val counter = java.util.concurrent.atomic.AtomicInteger(0)

    // JVM on ARM: 내부적으로 LL/SC 루프
    // JVM on x86: 내부적으로 LOCK XADD
    fun increment() = counter.incrementAndGet()
}

// 의사코드 - LL-SC 가 ABA 를 회피하는 이유:
//   CAS(addr, A, C) 는 값이 A → B → A 로 바뀐 경우 알 수 없음
//   LL/SC 는 값이 아닌 "내가 LL 한 후 누가 [addr] 에 썼는가"를 추적
//   B 로 바뀌었다가 A 로 돌아왔어도 SC 는 실패 → 명확히 감지
```

**관련 알고리즘**: CAS, ABA Problem, DCAS, Memory Barriers

---

<a id="rcu"></a>
## 3. RCU (Read-Copy-Update)

**목적**: 읽기가 압도적으로 많은 자료구조에서 **read-side 가 거의 free(lock-free, barrier-free)** 가 되도록 하는 동기화 기법

**시간 복잡도**: 읽기 O(1) — 잠금/원자연산 없음. 쓰기 O(N) — 복사 비용

**공간 복잡도**: O(N) — 잠시 새/구 버전 공존

**특징**:
- 핵심 idea: **읽기는 그대로 두고, 쓰기는 copy → 수정 → atomic pointer swap**
- read-side critical section: `rcu_read_lock()` ~ `rcu_read_unlock()` — 실제로는 preemption disable 등 매우 가벼움
- writer: 옛 버전을 즉시 free 하지 못함 — 아직 읽는 reader 가 있을 수 있음
- **Grace Period**: 모든 reader 가 자신의 read-side critical section 을 빠져나갈 때까지 대기
- grace period 이후 옛 버전 free (`call_rcu`)
- **read-side 는 lock-free 가 아니라 wait-free 에 가까움** — 메모리 배리어조차 거의 없음

**장점**:
- 읽기 성능 압도적 — 거의 zero overhead
- multi-reader / single-writer 시나리오에 최적
- deadlock 불가능 (read-side 에 lock 없음)
- Linux kernel 의 scaling 핵심

**단점**:
- 쓰기 비용 큼 (전체 또는 부분 복사 + grace period 대기)
- 메모리 reclaim 지연
- 구현 복잡 (특히 user-space — URCU)
- 강한 일관성 아님 — reader 는 old 버전 볼 수 있음

**활용 예시**:
- **Linux kernel** — process list, routing table, dcache, sysctl, namespaces 전반
- **URCU (Userspace RCU)** library
- DPDK, BPF
- Linux 의 `seqcount` 와 조합

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.concurrent.atomic.AtomicReference

// JVM 의 GC 가 grace period 를 자동으로 해줌 — RCU 의 user-space 단순화 버전
// (kernel RCU 의 정밀한 의미론은 아니지만, copy-on-write + atomic swap 패턴은 동일)
class RcuLikeList<E> {
    private val head = AtomicReference<List<E>>(emptyList())

    // read-side: lock 없음, atomic ref 한 번 읽기만
    fun snapshot(): List<E> = head.get() // 거의 free

    // write-side: copy → modify → atomic swap
    fun add(e: E) {
        while (true) {
            val cur = head.get()
            val next = cur + e // copy
            if (head.compareAndSet(cur, next)) return
        }
    }

    fun remove(e: E) {
        while (true) {
            val cur = head.get()
            val next = cur - e
            if (head.compareAndSet(cur, next)) return
            // old 버전은 JVM GC 가 reader 종료 후 회수 → grace period 역할
        }
    }
}

// 의사코드 - Linux kernel RCU:
//
// reader:
//   rcu_read_lock();             // preemption disable
//   p = rcu_dereference(global);  // load + dependency barrier
//   use(p->field);                 // p 는 grace period 동안 유효 보장
//   rcu_read_unlock();
//
// writer:
//   new = kmalloc(); *new = *old; new->field = X;
//   rcu_assign_pointer(global, new); // smp_wmb + WRITE_ONCE
//   synchronize_rcu();               // 모든 현 reader 가 끝날 때까지 대기 (grace period)
//   kfree(old);                       // 안전하게 회수
//
// 또는 비동기:
//   call_rcu(&old->rcu_head, free_callback);
```

**관련 알고리즘**: Hazard Pointer, Seqlock, Epoch-Based Reclamation, COW

---

<a id="mvcc"></a>
## 4. MVCC (Multi-Version Concurrency Control)

**목적**: 데이터에 여러 버전을 동시에 유지해 read 가 write 를 막지 않도록 하는 동시성 제어

**시간 복잡도**: read O(log V) — V = 버전 수, write O(1) + GC

**공간 복잡도**: O(N · V) — N = row 수, V = active 버전

**특징**:
- 각 row 에 `(value, xmin, xmax)` — 생성 트랜잭션 / 무효화 트랜잭션
- read 트랜잭션은 자신의 snapshot 에 보이는 버전만 봄
- write 는 새 버전 추가 (in-place update 없음)
- snapshot isolation / serializable snapshot isolation
- 옛 버전은 트랜잭션 종료 후 vacuum/GC 로 회수
- 충돌 검출 — write-write 충돌 시 첫 commit 이 이김 (first-committer-wins)

**장점**:
- read 가 write 를 차단하지 않음 (read 의 lock 거의 없음)
- write 도 read 를 차단하지 않음
- snapshot isolation 자연스러움
- backup / time-travel query 가능

**단점**:
- 공간 비용 (옛 버전 누적) — vacuum 필요
- write-skew anomaly (snapshot isolation 한계)
- GC 가 long-running read 트랜잭션에 의해 막힘
- index 가 모든 버전 가리켜야 → bloat

**활용 예시**:
- **PostgreSQL** — heap tuple xmin/xmax
- **InnoDB (MySQL)** — undo log 기반
- **Oracle** — undo segment
- **CockroachDB / Spanner / FoundationDB** — HLC + MVCC
- Git (개념적으로 유사 — content-addressable)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
data class Version<V>(
    val value: V,
    val xmin: Long,        // 생성 트랜잭션 ID
    var xmax: Long? = null // 무효화 트랜잭션 ID
)

class MvccTable<K, V> {
    private val rows = mutableMapOf<K, MutableList<Version<V>>>()
    private val txCounter = java.util.concurrent.atomic.AtomicLong(0)

    fun begin(): Long = txCounter.incrementAndGet()

    // snapshot read: 내 tx 시작 시점에 visible 한 버전만 본다
    fun read(key: K, txId: Long, snapshot: Snapshot): V? {
        val versions = rows[key] ?: return null
        return versions
            .filter { v ->
                v.xmin <= txId && v.xmin !in snapshot.active &&
                (v.xmax == null || v.xmax!! > txId || v.xmax!! in snapshot.active)
            }
            .maxByOrNull { it.xmin }
            ?.value
    }

    fun write(key: K, value: V, txId: Long) {
        val list = rows.getOrPut(key) { mutableListOf() }
        // 이전 active 버전을 무효화 (충돌 검사 생략한 단순 버전)
        list.lastOrNull { it.xmax == null }?.xmax = txId
        list.add(Version(value, xmin = txId))
    }

    data class Snapshot(val active: Set<Long>) // 시작 시점 활성 tx 들
}

// 의사코드 - PostgreSQL MVCC:
//
// SELECT 시 visibility check:
//   visible if:
//     xmin committed AND xmin < my_xmin AND xmin not in active_xids
//   AND
//     (xmax is null) OR (xmax not committed at my snapshot) OR (xmax > my_xmin)
//
// UPDATE row:
//   1) old tuple 의 xmax = my_xid
//   2) new tuple insert with xmin = my_xid
//   3) index 양쪽 가리키도록 갱신 (HOT 최적화 시 단축)
//   4) commit log 갱신
//
// VACUUM:
//   모든 active tx 가 보지 않게 된 죽은 tuple 회수
//   long-running tx 가 있으면 회수 지연 → table bloat
```

**관련 알고리즘**: RCU, Snapshot Isolation, HLC, 2PL

---

<a id="hazard-pointer"></a>
## 5. Hazard Pointer (위험 포인터)

**목적**: lock-free 자료구조에서 안전한 메모리 회수(memory reclamation) — "이 노드를 누가 보고 있는가?"

**시간 복잡도**: read O(1) — hazard ptr publish, reclaim O(H · R) — H = 스레드 수, R = 회수 후보

**공간 복잡도**: O(H · K) — K = 스레드당 hazard slot 수 (보통 1~2)

**특징**:
- 각 스레드가 "지금 보고 있는 포인터" 를 공개 슬롯에 기록 (hazard pointer)
- 회수자(retire 호출)는 즉시 free 하지 않고 **retire list** 에 넣어둠
- 주기적으로 hazard pointer 들을 모두 스캔 → 어느 슬롯에도 없는 retire 노드만 free
- read-side overhead: 포인터 publish + memory fence + 재검사
- GC 없는 언어(C/C++) 의 lock-free 표준 reclamation 기법

**장점**:
- 정확한 메모리 회수 — leak 없음
- read 측 overhead 작음 (slot write + fence)
- RCU 보다 latency 예측 가능 (grace period 무한 대기 없음)
- ABA 문제 부분 완화

**단점**:
- 스레드당 hazard slot 수 제한 → 알고리즘 복잡도 증가
- 회수 비용 — 스레드 수가 많으면 scan O(H·R) 큼
- 구현 복잡 (특히 retire list 분산)
- read 측에 memory fence 필요 → RCU 보다는 느림

**활용 예시**:
- C++ folly::hazptr (Facebook)
- Concurrent Building Blocks 라이브러리
- lock-free queue / stack / hashmap 의 free 단계
- Rust crossbeam 의 epoch-based 와 경쟁/병행

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicReference

// 의사 구현 — JVM 에서는 GC 가 reclamation 을 처리하므로 hazard pointer 가 보통 불필요
// 학습용 의사코드
class HazardPointerManager<T : Any> {
    private val hazards = ConcurrentHashMap<Long, AtomicReference<T?>>() // threadId -> slot
    private val retireList = ConcurrentHashMap<Long, MutableList<T>>()
    private val threshold = 64

    fun slot(): AtomicReference<T?> =
        hazards.computeIfAbsent(Thread.currentThread().id) { AtomicReference(null) }

    // read 측: 포인터를 슬롯에 publish 후 재확인 (race 방지)
    fun protect(loadFrom: () -> T?): T? {
        val s = slot()
        while (true) {
            val p = loadFrom() ?: return null
            s.set(p)
            // memory fence + 재확인 — 그 사이에 retire 됐을 수 있음
            if (loadFrom() === p) return p
            // 다시 시도
        }
    }

    fun clear() { slot().set(null) }

    // 회수 측: free 하지 않고 retire list 에 넣어 두기
    fun retire(p: T) {
        val list = retireList.computeIfAbsent(Thread.currentThread().id) { mutableListOf() }
        list.add(p)
        if (list.size >= threshold) scanAndFree(list)
    }

    private fun scanAndFree(list: MutableList<T>) {
        val protected = hazards.values.mapNotNull { it.get() }.toSet()
        val iter = list.iterator()
        while (iter.hasNext()) {
            val node = iter.next()
            if (node !in protected) {
                // free(node) — 실제로는 unsafe free 또는 cleanup
                iter.remove()
            }
        }
    }
}

// 의사코드 - lock-free stack pop 에서 hazard pointer 사용:
//   loop:
//     old = head.get()
//     if (old == null) return null
//     hp.set(old)                              // ① publish hazard
//     if (head.get() != old) continue          // ② 변경됐으면 재시도
//     val next = old.next                       // 안전하게 dereference (free 보호받음)
//     if (head.compareAndSet(old, next)) {
//         hp.set(null)
//         retire(old)                            // free 는 나중에
//         return old.value
//     }
```

**관련 알고리즘**: RCU, Epoch-Based Reclamation, Reference Counting, CAS

---

<a id="lock-free-queue"></a>
## 6. Lock-Free Queue (Michael-Scott non-blocking queue)

**목적**: 여러 producer / consumer 가 lock 없이 안전하게 enqueue/dequeue 하는 FIFO 큐

**시간 복잡도**: O(1) per op (amortized, retry 포함)

**공간 복잡도**: O(N) — node 당 next pointer + value

**특징**:
- linked list 기반, head/tail 두 포인터를 atomic 으로 관리
- enqueue: tail.next CAS → 새 노드 연결 후 tail 자체 CAS 로 진행
- dequeue: head CAS 로 head→head.next 전환
- **dummy(sentinel) node** 로 빈 큐와 한 원소 큐 구분
- "swing the tail" — tail 이 마지막 노드를 가리키지 않을 수 있어 helper logic 필요
- 1996 Michael & Scott 논문, java `ConcurrentLinkedQueue` 의 모태

**장점**:
- lock 없음 — deadlock 불가, priority inversion 없음
- producer / consumer 가 서로 거의 안 막음
- 평균 latency 안정적

**단점**:
- contention 높으면 CAS retry 폭증
- ABA 문제 (tagged pointer / hazard pointer 필요)
- 메모리 reclaim 어려움
- 코드가 까다로움 — 정확성 검증 필요

**활용 예시**:
- `java.util.concurrent.ConcurrentLinkedQueue`
- Akka mailbox
- Disruptor 의 일부 모드 (ring buffer 변형이 더 유명)
- High-throughput logging buffer

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.concurrent.atomic.AtomicReference

class MichaelScottQueue<E : Any> {
    private class Node<E>(val value: E?) {
        val next = AtomicReference<Node<E>?>(null)
    }

    private val head: AtomicReference<Node<E>>
    private val tail: AtomicReference<Node<E>>

    init {
        val dummy = Node<E>(null)
        head = AtomicReference(dummy)
        tail = AtomicReference(dummy)
    }

    fun enqueue(value: E) {
        val node = Node(value)
        while (true) {
            val curTail = tail.get()
            val tailNext = curTail.next.get()
            if (curTail == tail.get()) {                          // ① 일관성 검사
                if (tailNext == null) {
                    if (curTail.next.compareAndSet(null, node)) {  // ② tail.next 에 새 노드 연결
                        tail.compareAndSet(curTail, node)           // ③ tail 자체 swing (실패 OK — 다른 스레드가 도와줌)
                        return
                    }
                } else {
                    // tail 이 뒤처져 있음 — 다른 스레드 enqueue 진행 중. 도와서 swing
                    tail.compareAndSet(curTail, tailNext)
                }
            }
        }
    }

    fun dequeue(): E? {
        while (true) {
            val curHead = head.get()
            val curTail = tail.get()
            val first = curHead.next.get()
            if (curHead == head.get()) {
                if (curHead == curTail) {
                    if (first == null) return null              // 빈 큐
                    tail.compareAndSet(curTail, first)          // tail 뒤처짐 — 도움
                } else {
                    val value = first!!.value
                    if (head.compareAndSet(curHead, first)) {   // head 진행
                        return value
                    }
                }
            }
        }
    }
}

// 의사코드 - 정확성 포인트:
//   - dummy 노드로 빈 큐 / 한 노드 큐 분리
//   - tail 은 "마지막"이 아니라 "마지막 또는 그 직전" 일 수 있음 → 항상 next 확인
//   - 자신이 못 끝낸 swing 을 다른 스레드가 도울 수 있어야 wait-free 에 가까움
//   - ABA: Node 재사용 시 tagged pointer 또는 hazard pointer 필요
```

**관련 알고리즘**: CAS, ABA Problem, Hazard Pointer, MPSC Queue (Vyukov), Disruptor

---

<a id="work-stealing"></a>
## 7. Work-Stealing (작업 훔치기)

**목적**: 다중 worker 스레드가 각자 deque 에서 자기 일을 처리하고, 자기 일이 떨어지면 다른 worker 의 deque 에서 일을 훔치는 부하 분산

**시간 복잡도**: O(T_1/P + T_∞) — T_1=직렬 시간, P=worker 수, T_∞=critical path

**공간 복잡도**: O(P · D) — D = 평균 deque 크기

**특징**:
- 각 worker 가 **lock-free deque** 보유 (Chase-Lev deque 등)
- worker 본인은 **bottom** 에서 push/pop (LIFO 처럼) — cache locality
- thief 는 다른 worker 의 **top** 에서 steal (FIFO 처럼) — 경쟁 최소화
- divide-and-conquer 작업과 궁합 최고 (재귀 분할 → 자식 task push → 자식이 자기 deque 에 쌓임)
- 휴리스틱: 무작위 victim 선택, 점진 backoff

**장점**:
- 부하 균형 자동 — 작업 불균등에 강함
- centralized queue 의 contention 회피
- 분할 정복에 자연 적용
- 캐시 친화적 (local 은 LIFO)

**단점**:
- deque 구현이 까다로움 (Chase-Lev — bottom side 는 single owner, top side 는 다중 thief)
- steal 자체에 overhead — 너무 잦으면 손해
- task granularity 가 너무 작으면 분할 비용이 처리 비용 초과
- locality 일부 손실 (steal 된 task)

**활용 예시**:
- **Java ForkJoinPool / `CompletableFuture` 의 common pool**
- **Cilk / Cilk Plus** (논문 기반)
- Rust **Rayon** — 데이터 병렬화
- Go 의 GMP 스케줄러 (work-stealing 기반)
- TBB (Intel Threading Building Blocks)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.concurrent.ForkJoinPool
import java.util.concurrent.RecursiveTask

// JVM 의 ForkJoinPool 이 work-stealing 의 가장 흔한 인터페이스
class ParallelSum(private val arr: IntArray, private val lo: Int, private val hi: Int)
    : RecursiveTask<Long>() {

    override fun compute(): Long {
        val n = hi - lo
        if (n <= THRESHOLD) {
            var s = 0L
            for (i in lo until hi) s += arr[i]
            return s
        }
        val mid = (lo + hi) ushr 1
        val left = ParallelSum(arr, lo, mid)
        left.fork()                          // ① left task 를 worker deque 의 bottom 에 push
        val right = ParallelSum(arr, mid, hi).compute() // ② 즉시 직접 실행
        val leftResult = left.join()          // ③ 아직 안 끝났으면 자기가 처리하거나, 다른 worker 가 steal 했을 수 있음
        return leftResult + right
    }

    companion object { const val THRESHOLD = 10_000 }
}

fun parallelSum(a: IntArray): Long =
    ForkJoinPool.commonPool().invoke(ParallelSum(a, 0, a.size))

// 의사코드 - Chase-Lev deque:
//
// owner-side:
//   push(task):
//       b = bottom
//       array[b] = task
//       bottom = b + 1
//   pop():
//       b = bottom - 1
//       bottom = b
//       t = top
//       if (b < t) { bottom = t; return EMPTY }
//       task = array[b]
//       if (b > t) return task                     // race 없음
//       if (!CAS(top, t, t+1)) task = EMPTY        // thief 와 경쟁
//       bottom = t + 1
//       return task
//
// thief-side:
//   steal():
//       t = top
//       b = bottom
//       if (t >= b) return EMPTY
//       task = array[t]
//       if (!CAS(top, t, t+1)) return RETRY        // 다른 thief 와 경쟁
//       return task
```

**관련 알고리즘**: Fork-Join, Divide-and-Conquer, MPMC Queue, Lock-Free Deque

---

<a id="seqlock"></a>
## 8. Seqlock (시퀀스 잠금)

**목적**: 읽기가 매우 빈번하고 쓰기가 드문 데이터에서, **reader 가 lock 도 atomic 도 거의 안 쓰도록** 하는 동기화

**시간 복잡도**: read O(1) — 일관성 확인만, write O(1) — counter++ × 2

**공간 복잡도**: O(1) — counter + 데이터

**특징**:
- 짝수/홀수 sequence counter 사용
- writer: `seq++; write data; seq++;` — 진행 중에는 홀수
- reader: `s1 = seq; read data; s2 = seq; if (s1 != s2 || s1&1) retry;`
- reader 가 단 한 번의 atomic op 도 안 함 (counter 읽기만 — load + barrier)
- reader 가 옛 값 / 새 값 / 찢어진 값 중 첫 두 개만 받도록 보장
- writer 끼리는 별도 lock 필요

**장점**:
- read 가 거의 free (RCU 와 유사한 read 비용)
- 데이터 구조 크기 무관
- 구현 단순

**단점**:
- writer 가 잦으면 reader 가 starvation 가능 (계속 retry)
- read 측이 retry-loop 안에서 trivially copyable 데이터만 다뤄야 함 (찢어진 값 가능)
- writer 끼리는 별도 mutex 필요

**활용 예시**:
- **Linux kernel** — `gettimeofday` 의 timekeeping 변수
- Linux `seqcount` / `seqlock_t`
- Routing table snapshot
- 고빈도 read 의 config snapshot

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.util.concurrent.atomic.AtomicLong

class Seqlock<T>(initial: T) {
    private val seq = AtomicLong(0)        // 짝수=stable, 홀수=write 진행
    @Volatile private var data: T = initial
    private val writerLock = Any()         // writer 간 직렬화

    fun read(): T {
        while (true) {
            val s1 = seq.get()
            if (s1 and 1L == 1L) continue   // write 진행 중 → 대기
            // memory fence 후 데이터 읽기
            val snapshot = data
            val s2 = seq.get()
            if (s1 == s2) return snapshot   // 그 사이 write 없었음 → 안전
            // 그 사이 write 발생 → 재시도
        }
    }

    fun write(newValue: T) {
        synchronized(writerLock) {
            seq.incrementAndGet()           // even → odd
            data = newValue
            seq.incrementAndGet()           // odd → even
        }
    }
}

// 의사코드 - Linux gettimeofday:
//
// reader (lock-free hot path):
//   do {
//       seq = read_seqbegin(&timekeeper.seq);   // memory barrier load
//       now = timekeeper.now;
//       cycle_last = timekeeper.cycle_last;
//   } while (read_seqretry(&timekeeper.seq, seq));
//   return compute_time(now, cycle_last, hpet_read());
//
// writer (timekeeping update, 1 Hz):
//   write_seqlock(&timekeeper.seq);
//   timekeeper.now = ...;
//   timekeeper.cycle_last = ...;
//   write_sequnlock(&timekeeper.seq);
//
// 주의:
//   reader 가 read 한 데이터는 torn(찢어진) 일 수 있다 — retry 전까지는 신뢰 금지
//   따라서 retry 안에서만 사용하고 외부로 효과(부작용) 내보내지 말 것
```

**관련 알고리즘**: RCU, Hazard Pointer, Memory Barriers, COW

---

<a id="memory-barriers"></a>
## 9. Memory Barriers (메모리 배리어 — mfence/lfence/sfence, acquire/release/seq_cst)

**목적**: CPU 와 컴파일러의 메모리 재정렬(reordering) 을 제어해 lock-free 코드의 정확성 보장

**시간 복잡도**: O(1) per barrier, 그러나 cache flush / store buffer drain 으로 수십~수백 cycle

**공간 복잡도**: O(0)

**특징**:
- 하드웨어 메모리 모델: x86 (TSO — strong), ARM/PowerPC (weak), Alpha (가장 weak)
- 컴파일러 재정렬 + CPU 재정렬 둘 다 막아야 함
- **하드웨어 펜스**:
  - `mfence`: 모든 load/store 정렬
  - `sfence`: store ↔ store 정렬 (write barrier)
  - `lfence`: load ↔ load 정렬 (read barrier)
- **메모리 ordering 분류** (C++/Java/Rust 공통 개념):
  - `relaxed`: 원자성만, ordering 없음
  - `acquire`: 이 load 이후 코드가 이 load 이전으로 재배치 안 됨 (read-side fence)
  - `release`: 이 store 이전 코드가 이 store 이후로 재배치 안 됨 (write-side fence)
  - `acq_rel`: read-modify-write 에서 양쪽
  - `seq_cst`: 전 순서(total order) — 가장 강하지만 비쌈

**JMM(Java Memory Model)**:
- `volatile` 읽기 = acquire, `volatile` 쓰기 = release
- `synchronized` 진입 = acquire, 종료 = release
- `final` 필드 = 생성자 종료 시 freeze
- `VarHandle` 로 명시적 ordering 선택 가능 (Java 9+)

**장점**:
- 필요한 강도만 선택 → 성능 최적화
- lock-free 정확성의 기반
- 명시적 — 의도를 코드에 새김

**단점**:
- 아키텍처별 동작 차이 (x86 에서 잘 되던 코드가 ARM 에서 깨짐)
- 잘못된 선택은 silent bug
- 학습 곡선 가파름

**활용 예시**:
- 모든 lock-free 자료구조
- Java `volatile`, `AtomicReference`, `VarHandle`
- C++ `std::atomic` ordering
- Linux kernel `smp_mb()`, `smp_rmb()`, `smp_wmb()`, `READ_ONCE`, `WRITE_ONCE`
- Disruptor 의 padded sequence

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.lang.invoke.VarHandle
import java.lang.invoke.MethodHandles

// 1) volatile = acquire(load) + release(store)
class FlagPublish {
    @Volatile private var ready = false
    private var payload: String = ""

    fun publish(p: String) {
        payload = p          // plain write
        ready = true         // volatile write = release — 위 write 들이 이 위로 못 옴
    }

    fun consume(): String? {
        if (!ready) return null  // volatile read = acquire — 아래 read 들이 이 위로 못 감
        return payload           // ready=true 본 순간 payload 보장
    }
}

// 2) VarHandle 로 fine-grained ordering 선택 (Java 9+)
class FineGrained {
    @JvmField var x: Long = 0
    @JvmField var y: Long = 0

    companion object {
        private val X: VarHandle = MethodHandles.lookup().findVarHandle(
            FineGrained::class.java, "x", Long::class.javaPrimitiveType
        )
        private val Y: VarHandle = MethodHandles.lookup().findVarHandle(
            FineGrained::class.java, "y", Long::class.javaPrimitiveType
        )
    }

    fun publish(a: Long, b: Long) {
        X.setOpaque(this, a)            // ordering 없음 (relaxed)
        Y.setRelease(this, b)            // release — 위 store 가 아래로 못 감
    }

    fun consume(): Pair<Long, Long> {
        val b = Y.getAcquire(this) as Long  // acquire — 아래 load 가 위로 못 감
        val a = X.getOpaque(this) as Long
        return a to b
    }
}

// 의사코드 - acquire/release 의미:
//
// release(store):
//   compiler: 위 코드 ↑ 못 넘어옴
//   CPU:      위 store 들 모두 globally visible 후에야 이 store visible
//
// acquire(load):
//   compiler: 아래 코드 ↓ 못 넘어감
//   CPU:      이 load 가 끝난 뒤에야 아래 load 들이 시작
//
// 짝(pair):
//   T1: data = X; flag.store(true, release);
//   T2: while (!flag.load(acquire)) {}
//       use(data);                      ← flag 읽고 acquire 했으니 T1 의 data 보장 visible
//
// seq_cst:
//   모든 seq_cst 연산이 전체 시스템에서 단일 순서를 가짐
//   x86: 거의 무료, ARM: 비쌈 (dmb ish)
```

**관련 알고리즘**: CAS, LL-SC, RCU, Lock-Free Queue, Seqlock

---

<a id="aba-problem"></a>
## 10. ABA Problem 해법 (tagged pointer / double-CAS / hazard pointer)

**목적**: CAS 가 "값이 같다" 만 보고 "그 사이 변경이 있었는가" 를 못 보는 문제 해결

**시간 복잡도**: O(1) per op (해법 무관 — 추가 word 1개 또는 메모리 reclamation 비용)

**공간 복잡도**: tag 추가 시 추가 word, hazard pointer 시 O(H)

**특징**:
- 문제: T1 이 A 읽음 → T2 가 A→B→A 로 되돌림 → T1 의 CAS(A→C) 성공 ← 잘못된 진행
- 가장 흔히 발생: lock-free stack/queue 의 노드 재사용 + free-list
- 해법:
  1. **Tagged Pointer / Versioned Pointer** — 포인터 + 카운터 한 word 로 묶어 CAS (DWCAS 또는 64bit pointer 의 상위 비트 활용)
  2. **Double-CAS (DCAS / 128-bit CAS)** — x86-64 의 `CMPXCHG16B` 로 16 byte 원자 비교
  3. **Hazard Pointer** — 노드를 재사용하지 않거나, 충분히 늦게 회수 → ABA 자체가 발생 안 함
  4. **Epoch-based reclamation** — RCU 의 user-space 버전. 같은 epoch 안에서는 free 안 함
  5. **LL-SC** — 하드웨어 수준에서 reservation 추적, 값 기반이 아니라 ABA 자체가 없음
  6. **GC 가 있는 언어 (Java/Kotlin/C#/Go)** — 노드가 회수되지 않으면 ABA 가 발생할 수 있어도 메모리 안전성은 보장. 그래도 논리적 ABA 는 별도 처리 필요

**장점/단점**:
- Tagged pointer: 단순, 비용 작음 / 단어 너비 제약 (32bit pointer + 32bit tag 또는 DCAS 필요)
- DCAS: 가장 단순하고 정확 / 일부 ISA 만 지원
- Hazard pointer: 메모리 회수도 같이 해결 / 구현 복잡
- LL-SC: 자연스러움 / ARM/PowerPC 만

**활용 예시**:
- Java `AtomicStampedReference`, `AtomicMarkableReference` — 사실상 tagged pointer
- C++ `std::atomic<std::pair<T*, std::uintptr_t>>` (DCAS 가능 플랫폼)
- folly::AtomicSharedPtr (hazard pointer 기반)
- crossbeam (Rust) — epoch-based

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.concurrent.atomic.AtomicStampedReference

// 1) Tagged pointer (Java 의 AtomicStampedReference)
class AbaSafeStack<E> {
    private class Node<E>(val value: E, val next: Node<E>?)
    private val head = AtomicStampedReference<Node<E>?>(null, 0)

    fun push(value: E) {
        while (true) {
            val stamp = IntArray(1)
            val cur = head.get(stamp)
            val newNode = Node(value, cur)
            if (head.compareAndSet(cur, newNode, stamp[0], stamp[0] + 1)) return
            // stamp 까지 함께 비교 → A→B→A 라도 stamp 가 다르므로 CAS 실패 → 안전
        }
    }

    fun pop(): E? {
        while (true) {
            val stamp = IntArray(1)
            val cur = head.get(stamp) ?: return null
            val next = cur.next
            if (head.compareAndSet(cur, next, stamp[0], stamp[0] + 1)) return cur.value
        }
    }
}

// 2) DCAS / 128-bit CAS — JVM 에서는 직접 노출 안 됨 (Project Valhalla 의 inline class 대기 중)
//    의사코드:
//      struct Tagged { void* ptr; uint64_t tag; };  // 16 bytes
//      cmpxchg16b(addr, expected, new)              // x86-64 명령
//
// 3) Hazard Pointer (앞 항목 참조) — 노드를 retire 후 grace 까지 free 안 함
//    → A 가 회수되지 않으므로 새 A 가 같은 주소를 받을 일이 없음
//
// 4) LL-SC (앞 항목 참조) — 하드웨어가 reservation 추적
//
// 5) GC 언어:
//    Java/Kotlin 에서는 JVM 이 노드 free 를 미루므로 "메모리 안전" 측면의 ABA 는 없음
//    그러나 "논리적" ABA (예: 카운터가 0→1→0 으로 돌아온 경우) 는 stamp 로 해결 필요
//
// 의사코드 - 언제 ABA 가 진짜 문제인가:
//   stack/queue 의 노드를 free-list 로 재활용할 때 매우 흔함
//   인덱스(증가 일변도 ID) 만 CAS 한다면 ABA 없음
//   GC 있는 언어 + Node 객체 새로 할당이면 보통 안전 (그러나 ConcurrentLinkedQueue 같은 곳도 stamp 사용)
```

**관련 알고리즘**: CAS, LL-SC, Hazard Pointer, Lock-Free Queue, Epoch-Based Reclamation

---
