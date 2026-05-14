# OS 기초 알고리즘 (OS Foundations Algorithms)

운영체제·런타임 내부의 정평 있는 12 알고리즘. GC / Scheduling / Memory Allocator / I/O Multiplexing / Page Replacement / Cache Coherence. **앱은 직접 호출하지 않지만 성능·동작에 깊이 영향**.

**원전·표준 참고**:
- Richard Jones, Antony Hosking, Eliot Moss — *The Garbage Collection Handbook*, 2nd ed. (2023)
- Andrew Tanenbaum — *Modern Operating Systems*, 5th ed. (2023)
- Mel Gorman — *Understanding the Linux Virtual Memory Manager* (2004)
- Ulrich Drepper — *What Every Programmer Should Know About Memory* (2007)
- JEP 333 (ZGC), JEP 248 (G1)
- Linux kernel source (mm/, kernel/sched/, fs/io_uring.c)
- *Hennessy & Patterson — Computer Architecture: A Quantitative Approach*, 6th ed. (2017)

## 알고리즘 목차

| ID | 알고리즘 | 카테고리 | 적용 |
|----|---------|---------|------|
| [mark-sweep-gc](#mark-sweep-gc) | Mark-Sweep | GC | 기초 GC |
| [generational-gc](#generational-gc) | Generational | GC | JVM/V8 |
| [g1-gc](#g1-gc) | G1 | GC | JVM 9+ default |
| [zgc-shenandoah](#zgc-shenandoah) | ZGC / Shenandoah | GC | sub-ms pause |
| [round-robin-scheduling](#round-robin-scheduling) | Round-Robin | Scheduling | 단순 |
| [cfs](#cfs) | CFS | Scheduling | Linux |
| [mlfq](#mlfq) | MLFQ | Scheduling | XNU, Windows |
| [slab-allocator](#slab-allocator) | Slab | Memory | Linux kernel |
| [buddy-allocator](#buddy-allocator) | Buddy | Memory | kernel page |
| [epoll-kqueue-iouring](#epoll-kqueue-iouring) | epoll/kqueue/io_uring | I/O | event-driven server |
| [page-replacement](#page-replacement) | LRU/Clock/LFU | Memory | page fault |
| [mesi-cache-coherence](#mesi-cache-coherence) | MESI | Cache | multi-core |

**관련 카탈로그**:
- [concurrent.md](concurrent.md) — CAS / RCU / Memory Barriers
- [data-structures.md](data-structures.md) — Red-Black Tree (CFS 기반), Skip List
- [`../patterns/concurrency.md`](../patterns/concurrency.md) — Reactor (epoll 위 패턴), Actor

---

<a id="mark-sweep-gc"></a>
## 1. Mark-Sweep GC (마크-스윕 가비지 컬렉션)

**목적**: 도달 불가능한(unreachable) 힙 객체를 찾아 회수하는 가장 기초적인 추적형(tracing) GC 알고리즘

**시간 복잡도**: O(L + H) — L = live objects 수, H = heap 크기 (sweep 단계가 전체 heap 스캔)

**공간 복잡도**: O(L / word) — mark bit (객체당 1 비트, 별도 bitmap 또는 헤더)

**특징**:
- 두 단계 (Stop-The-World):
  1. **Mark**: GC roots(stack, globals, registers, JNI handles)에서 시작해 도달 가능한 모든 객체를 DFS/BFS 로 traversal 하며 mark bit 세팅
  2. **Sweep**: 전체 힙을 선형 스캔, 마킹 안 된 객체를 free list 에 반환
- McCarthy(1960) — Lisp GC 의 원조
- "Tri-color marking" 으로 확장 (white=미방문, gray=발견 but 자식 미스캔, black=완료) — 증분/병렬 GC 의 기반
- Fragmentation 발생 — sweep 만 하면 free 공간이 흩어짐 → **Mark-Compact** 변형은 sweep 대신 객체 이동

**장점**:
- 구현 단순 (교과서 첫 GC)
- cycle 처리 가능 (reference counting 의 약점 해결)
- read/write barrier 불필요 (STW 면)

**단점**:
- Stop-The-World pause — 힙 크기에 비례 (대형 힙에서 수 초)
- Fragmentation — large allocation 실패 가능
- Cache locality 나쁨 (sweep 시 전체 힙 터치)
- Throughput 좋지만 latency 나쁨

**활용 예시**:
- 초기 Lisp, Smalltalk
- CPython `gc` 모듈 (cycle collector — reference counting 위 보조)
- Boehm GC (C/C++ conservative GC)
- Ruby 2.1 이전 (이후 generational + incremental)

**난이도**: 중간 | **사용 빈도**: ★★★☆☆ (현대 GC 의 기반)

**C 의사코드**:
```c
// Mark-Sweep GC 의 핵심 — 교과서 수준 단순 구현
typedef struct Object {
    uint8_t marked;          // mark bit (실제는 별도 bitmap 권장)
    size_t  size;
    struct Object *next;     // heap-wide linked list
    void   **refs;           // outgoing references
    size_t  ref_count;
} Object;

static Object *heap_head;    // 모든 할당 객체의 linked list
static Object **roots;       // root set (stack scan, globals)
static size_t roots_count;

// Phase 1: Mark — DFS 로 도달 가능 객체 표시
static void mark(Object *obj) {
    if (!obj || obj->marked) return;
    obj->marked = 1;
    for (size_t i = 0; i < obj->ref_count; i++) {
        mark((Object *)obj->refs[i]);
    }
}

static void mark_phase(void) {
    for (size_t i = 0; i < roots_count; i++) {
        mark(roots[i]);
    }
}

// Phase 2: Sweep — 미마킹 객체 회수, mark bit 리셋
static void sweep_phase(void) {
    Object **link = &heap_head;
    Object *cur = heap_head;
    while (cur) {
        Object *next = cur->next;
        if (!cur->marked) {
            *link = next;       // unlink
            free(cur->refs);
            free(cur);
        } else {
            cur->marked = 0;    // 다음 GC 사이클을 위해 리셋
            link = &cur->next;
        }
        cur = next;
    }
}

void gc_collect(void) {
    // STW: 모든 mutator 정지 가정
    mark_phase();
    sweep_phase();
}

// 의사코드 - Tri-color marking (incremental 확장):
//   white set = 모든 객체 (초기)
//   gray  set = roots
//   black set = ∅
//   while gray ≠ ∅:
//       pick obj ∈ gray
//       for ref in obj.refs:
//           if ref ∈ white: move ref → gray
//       move obj → black
//   sweep: free 모든 white
//
//   Invariant: black → white 참조 금지 (write barrier 로 유지)
```

**관련 알고리즘**: Generational GC, G1, Reference Counting, Tri-color Marking, Mark-Compact

---

<a id="generational-gc"></a>
## 2. Generational GC (세대별 가비지 컬렉션)

**목적**: "**대부분의 객체는 일찍 죽는다(weak generational hypothesis)**"는 경험 법칙을 이용해 영역을 세대로 분리, young 영역만 자주 빠르게 수집

**시간 복잡도**: Minor GC O(L_young), Major GC O(L_total) — minor 가 압도적으로 빈번

**공간 복잡도**: O(H) + remembered set O(cross-gen refs)

**특징**:
- **Young Generation**: Eden + Survivor (S0, S1) — 새 할당
- **Old Generation (Tenured)**: 여러 minor GC 를 살아남은 객체가 promote
- **Minor GC (Scavenge)**: young 만 — copy GC(Cheney's) 로 매우 빠름 (수 ms)
- **Major / Full GC**: old 포함 — mark-sweep 또는 mark-compact, 느림
- **Remembered Set / Card Table**: old → young 참조를 추적해야 minor GC 시 young root 로 인식 — write barrier 로 갱신
- 가설 근거: Lieberman & Hewitt (1983), Ungar (1984)
- HotSpot ParNew + CMS, V8 (Scavenger + Mark-Sweep-Compact), .NET CLR (Gen 0/1/2)

**장점**:
- Minor GC 가 압도적으로 빈번하면서 빠름 → 평균 pause 짧음
- young 의 short-lived garbage 를 효율적으로 수집
- copy GC + 작은 영역 → cache locality 좋음

**단점**:
- write barrier 오버헤드 (모든 reference 쓰기에 추가 비용)
- old → young 참조가 많으면 가설 깨짐 (large cache, observer pattern 등)
- Major GC 는 여전히 큰 pause
- promotion 임계값 튜닝 필요

**활용 예시**:
- **HotSpot JVM** — ParNew, ParallelGC, CMS (deprecated)
- **V8 (Chrome/Node.js)** — Scavenger (young) + Mark-Compact (old)
- **.NET CLR** — Gen 0/1/2 + Large Object Heap
- **Ruby 2.1+**, MRI
- **Go (이전)** — 현재는 generational 아님 (concurrent mark-sweep)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**C 의사코드**:
```c
// Generational GC 의 핵심 구조
typedef enum { GEN_EDEN, GEN_SURVIVOR_0, GEN_SURVIVOR_1, GEN_OLD } Generation;

typedef struct GenObject {
    Generation gen;
    uint8_t    age;              // minor GC 살아남은 횟수
    uint8_t    forwarded;        // copy GC: 이미 이동되었나
    void      *forward_ptr;      // 이동 후 새 위치
    size_t     size;
    void     **refs;
    size_t     ref_count;
} GenObject;

// Card table — old gen 을 512B 카드로 분할, dirty 플래그
#define CARD_SIZE 512
static uint8_t card_table[OLD_GEN_SIZE / CARD_SIZE];

// Write barrier: old 객체가 young 을 참조하게 되면 카드를 dirty 로 마킹
void write_barrier(GenObject *obj, size_t idx, GenObject *new_ref) {
    obj->refs[idx] = new_ref;
    if (obj->gen == GEN_OLD && new_ref && new_ref->gen != GEN_OLD) {
        size_t card = ((uintptr_t)obj - OLD_GEN_BASE) / CARD_SIZE;
        card_table[card] = 1;    // dirty
    }
}

// Minor GC — young 만 수집 (Cheney's copying)
static GenObject *to_space;      // survivor (alternating S0/S1)
static GenObject *to_alloc;

static GenObject *copy_obj(GenObject *src) {
    if (!src) return NULL;
    if (src->forwarded) return src->forward_ptr;
    GenObject *dst = to_alloc;
    to_alloc += src->size;
    memcpy(dst, src, src->size);
    dst->age++;
    if (dst->age >= PROMOTION_THRESHOLD) dst->gen = GEN_OLD;
    src->forwarded = 1;
    src->forward_ptr = dst;
    return dst;
}

void minor_gc(void) {
    // 1) young roots: stack/registers
    scan_stack_roots(copy_obj);
    // 2) old → young roots: dirty card 만 스캔
    for (size_t c = 0; c < sizeof(card_table); c++) {
        if (card_table[c]) {
            scan_card(c, copy_obj);
            card_table[c] = 0;
        }
    }
    // 3) BFS: to_space 안의 새 객체를 큐로 진행
    GenObject *scan = to_space;
    while (scan < to_alloc) {
        for (size_t i = 0; i < scan->ref_count; i++) {
            scan->refs[i] = copy_obj(scan->refs[i]);
        }
        scan += scan->size;
    }
    // 4) from_space 통째로 reset (free 비용 없음)
}

// 의사코드 - Weak Generational Hypothesis:
//   "객체의 사망률은 나이의 감소함수다"
//   → 새 객체는 곧 죽을 확률 높음
//   → young 만 자주 GC 하면 대부분의 garbage 를 싸게 수집
//
//   가설이 깨지는 경우:
//     - 대용량 캐시 (객체가 오래 산다 → old 가 부풀어 major GC 빈발)
//     - Observer/EventBus (old 가 young 을 다수 참조 → write barrier hit 폭증)
```

**관련 알고리즘**: Mark-Sweep, Copy GC (Cheney's), G1, Card Marking, Write Barrier

---

<a id="g1-gc"></a>
## 3. G1 GC (Garbage First)

**목적**: 대용량 힙(수십 GB)에서 **예측 가능한 pause time** 을 보장하는 region-based, mostly-concurrent GC. Throughput 보다 latency 우선

**시간 복잡도**: Pause O(target pause), Throughput 약간 손해 (write barrier 무겁다)

**공간 복잡도**: O(H) + Remembered Set per region (region 마다 외부에서 들어오는 ref 추적)

**특징**:
- **Region**: 힙을 동일 크기 region(보통 1~32 MB)으로 분할 — Eden / Survivor / Old / Humongous 역할이 region 단위로 동적 할당
- **Humongous Object**: region 크기의 50% 초과 객체 — 별도 region 들에 직접 할당
- **Remembered Set (RSet)**: region 마다 외부에서 들어오는 참조의 카드 위치 기록 — region 단독 수집 가능하게 함
- **Concurrent Marking**: SATB(Snapshot-At-The-Beginning) write barrier 로 mutator 와 동시 마킹
- **Mixed Collection**: young + 일부 old region 동시 수집 — garbage 가 많은 region 우선 (이름의 유래)
- **Pause Time Target**: `-XX:MaxGCPauseMillis=200` (default 200ms) — 이 budget 안에 맞도록 region 개수 선택
- JEP 248 (JDK 9 default), Charlie Hunt 등

**장점**:
- Pause time 예측 가능 — soft real-time 시스템에 적합
- 대용량 힙에서 STW 짧음 (수십 ms ~ 수백 ms)
- Compaction 자동 수행 (region evacuation = copy)
- Throughput ParallelGC 대비 10~20% 손해이지만 latency 압도적

**단점**:
- 작은 힙(< 4GB)에서는 Parallel 보다 느림
- RSet 유지 비용 큼 (메모리 5~20%)
- Humongous object 가 많으면 단편화
- Concurrent failure 시 Full GC (Serial Old) — 매우 느림

**활용 예시**:
- **JDK 9+ default GC**
- 대용량 server (Cassandra, Elasticsearch, Kafka)
- pause-sensitive 실시간 분석 시스템
- 10~64GB 힙

**난이도**: 매우 높음 | **사용 빈도**: ★★★★★

**의사코드**:
```c
// G1 region 구조
typedef enum { REGION_FREE, REGION_EDEN, REGION_SURVIVOR, REGION_OLD, REGION_HUMONGOUS } RegionKind;

typedef struct Region {
    RegionKind kind;
    uintptr_t  base;
    size_t     size;            // 1~32 MB
    size_t     live_bytes;      // concurrent marking 결과
    size_t     garbage_bytes;   // size - live (수집 우선순위)
    struct RememberedSet *rset; // 외부에서 들어오는 카드 집합
} Region;

#define HEAP_REGIONS  2048
static Region regions[HEAP_REGIONS];

// Remembered Set — 어느 region 의 어느 카드가 나를 참조하는가
typedef struct RememberedSet {
    // (region_idx, card_idx) 의 sparse 집합 — coarse/fine/sparse 3 단계
    void *entries;
} RememberedSet;

// Write barrier: cross-region reference 감지
void g1_write_barrier(void *obj, size_t idx, void *new_ref) {
    *((void **)obj + idx) = new_ref;
    if (!new_ref) return;
    Region *src = region_of(obj);
    Region *dst = region_of(new_ref);
    if (src != dst) {
        // dst 의 RSet 에 (src_region, card_of(obj)) 추가
        rset_add(dst->rset, src - regions, card_index(obj));
    }
    // SATB barrier: concurrent marking 중이면 old 값도 mark queue 에 enqueue
    if (concurrent_marking_active) {
        void *old_ref = *((void **)obj + idx);
        if (old_ref) satb_enqueue(old_ref);
    }
}

// Concurrent marking cycle
void g1_concurrent_mark(void) {
    initial_mark_stw();           // STW (young GC piggyback) — root scan
    concurrent_root_scan();       // 동시 — 살아있는 그래프 traversal
    concurrent_mark();            // 동시 — SATB queue drain 포함
    remark_stw();                 // STW — final SATB drain
    cleanup_stw();                // STW — region 별 live_bytes 계산, free region 회수
}

// Collection Set 선택 — garbage 가 많은 region 우선
void choose_collection_set(int target_pause_ms) {
    // 모든 region 을 garbage_bytes 내림차순 정렬
    Region *sorted[HEAP_REGIONS];
    sort_by_garbage(regions, sorted);
    int budget = target_pause_ms;
    int i = 0;
    while (i < HEAP_REGIONS && budget > predicted_cost(sorted[i])) {
        add_to_cset(sorted[i]);
        budget -= predicted_cost(sorted[i]);
        i++;
    }
}

// Evacuation pause (STW): cset 안의 살아있는 객체를 새 region 으로 복사
void g1_evacuate(void) {
    for each Region *r in cset:
        for each live object o in r:
            void *new_loc = allocate_in_target_region(o->size);
            memcpy(new_loc, o, o->size);
            install_forwarding(o, new_loc);
        // 끝나면 r 전체를 free region 으로
        r->kind = REGION_FREE;
}

// 의사코드 - 왜 "Garbage First" 인가:
//   힙 전체를 한 번에 수집하지 않고
//   garbage 비율 높은 region 부터 수집 (수집 효율 최대화)
//   → pause budget 안에서 가장 많은 garbage 회수
```

**관련 알고리즘**: Generational GC, ZGC, Shenandoah, SATB Marking, Region-based Allocation

---

<a id="zgc-shenandoah"></a>
## 4. ZGC / Shenandoah (Sub-millisecond Pause GC)

**목적**: 수백 GB ~ 수 TB 힙에서도 **pause time < 10ms** (실제로는 < 1ms) 를 보장하는 concurrent compacting GC. 거의 모든 GC 작업이 mutator 와 동시 실행

**시간 복잡도**: Pause O(roots 수) — 힙 크기 무관. Throughput 5~15% 감소

**공간 복잡도**: O(H) + forwarding table

**특징**:
- **Colored Pointers (ZGC)**: 64-bit pointer 의 상위 비트에 metadata 저장 — Marked0, Marked1, Remapped, Finalizable 4 가지 색
- **Load Barrier**: 모든 reference 로드 시 색 검사 → 잘못된 색이면 객체 위치 갱신/마킹
- **Concurrent Relocation**: 객체를 mutator 동작 중 이동 — forwarding table 로 참조 갱신
- **Region-based**: ZGC 는 ZPage(2MB/32MB/large), Shenandoah 는 region
- **Brooks Pointer (Shenandoah)**: 객체 헤더에 forwarding pointer (현재는 load reference barrier 로 대체)
- ZGC: JEP 333 (JDK 11 experimental, JDK 15 production), Oracle
- Shenandoah: Red Hat, OpenJDK
- **Generational ZGC**: JEP 439 (JDK 21+) — young/old 분리

**장점**:
- Pause time 사실상 일정 (< 1ms, 힙 크기 무관)
- 수 TB 힙 지원 (ZGC max 16TB)
- Compaction 동시 수행 — fragmentation 없음
- pause-sensitive 거래/실시간 시스템에 최적

**단점**:
- Throughput 손해 (load barrier 가 모든 ref load 에 추가)
- 메모리 오버헤드 (forwarding table, multi-mapping)
- ZGC 는 colored pointer 때문에 x86-64 / aarch64 만 지원
- 작은 힙에서는 G1 보다 throughput 손해

**활용 예시**:
- 대형 금융 거래 시스템 (low-latency trading)
- 대용량 인메모리 DB (Cassandra, Elasticsearch heavy cache)
- streaming 처리 (Flink, Kafka Streams)
- JDK 21+ Cassandra 가 ZGC 기본 권장

**난이도**: 매우 높음 | **사용 빈도**: ★★★★☆ (JDK 17+ 도입 가속)

**의사코드**:
```c
// ZGC colored pointer — 64bit pointer 의 상위 비트에 색
//
//  63              42 41 40 39 38              0
//  +-----------------+--+--+--+----------------+
//  |  unused (canon) |Fz|M1|M0|R0|  address    |
//  +-----------------+--+--+--+----------------+
//   Fz: Finalizable, M0/M1: Marked0/1, R0: Remapped
//
// 같은 물리 주소가 가상 메모리에 4번 multi-mapped 됨 (각 색마다 다른 가상 주소)
// → 색 검사 없이 dereference 가능 (단순 load), barrier 만 색 검사

#define MASK_REMAPPED  (1ULL << 39)
#define MASK_MARKED0   (1ULL << 40)
#define MASK_MARKED1   (1ULL << 41)
#define MASK_COLOR     (0xfULL << 38)

static uint64_t good_mask;   // GC 가 현재 "유효"로 간주하는 색

// Load Barrier — 모든 reference 로드 후 실행
static inline void *zgc_load_barrier(void **addr) {
    void *ref = *addr;
    uint64_t bits = (uint64_t)ref;
    if (LIKELY((bits & MASK_COLOR) == good_mask)) {
        return ref;  // fast path — 그대로 사용
    }
    // slow path: 색 보정 (객체가 이동했으면 새 주소로, 미마킹이면 marking)
    return zgc_slow_path(addr, ref);
}

// Slow path — 이동된 객체 추적
static void *zgc_slow_path(void **addr, void *ref) {
    if (is_relocated(ref)) {
        void *new_loc = forwarding_lookup(ref);
        // self-healing: 다음에는 fast path 가 되도록 addr 의 값을 갱신
        __atomic_compare_exchange(addr, &ref, &new_loc, ...);
        ref = new_loc;
    }
    if (is_marking_phase()) {
        mark_enqueue(ref);
    }
    return apply_good_color(ref);
}

// Concurrent relocation phase
void zgc_relocate(void) {
    for each ZPage *p in relocation_set:
        for each live obj in p:
            void *new_loc = allocate_in_to_page(obj->size);
            // 1) copy (mutator 가 동시에 읽을 수 있음 — load barrier 가 forwarding 처리)
            memcpy(new_loc, obj, obj->size);
            // 2) forwarding table 에 등록 (lock-free hash)
            forwarding_install(obj, new_loc);
            // 3) old location 은 아직 free 못함 — mutator 가 아직 참조 중일 수 있음
        // page 의 모든 객체 이동 끝 → 다음 cycle 에 page free
}

// Shenandoah Brooks pointer (load reference barrier 이전 구버전)
// 모든 객체 헤더 첫 8바이트 = forwarding pointer (보통 자기 자신)
struct ShenObject {
    void *fwd;       // forwarding pointer — 이동 후 새 주소
    // ... actual fields ...
};
// 모든 ref load = obj->fwd 한 번 더 dereference

// 의사코드 - 왜 sub-ms pause 가 가능한가:
//   STW pause = root scanning + marking handshake 만
//   marking, relocation, reference processing 모두 concurrent
//   roots 수는 힙 크기와 무관 → pause 가 상수 시간에 가까움
//
//   Generational ZGC (JDK 21+):
//     young/old 분리로 throughput 회복
//     young 만 자주 수집 → 전체 cycle 더 짧음
```

**관련 알고리즘**: G1, Generational GC, Brooks Forwarding, Load Barrier, Concurrent Marking

---

<a id="round-robin-scheduling"></a>
## 5. Round-Robin Scheduling (라운드 로빈 스케줄링)

**목적**: 모든 ready process 에 동일한 시간 quantum 을 순환 할당하는 가장 단순한 fair scheduling 알고리즘

**시간 복잡도**: 컨텍스트 스위치당 O(1) (큐 push/pop)

**공간 복잡도**: O(N) — N = ready process 수

**특징**:
- Time-slicing: 각 process 가 고정 quantum (보통 10~100ms) 동안 CPU 사용 후 ready queue 끝으로
- preemptive: timer interrupt 가 quantum 종료 시 강제 스케줄
- FIFO + quantum — pure FCFS 에 preemption 추가
- quantum 크기 선택이 핵심:
  - 너무 짧음 → context switch 오버헤드 폭증
  - 너무 김 → FCFS 와 같아져 응답 시간 나빠짐
- 보통 typical quantum ≈ 평균 CPU burst 의 80%

**장점**:
- 구현 매우 단순 (FIFO queue + timer)
- starvation 없음 (모두에게 차례가 옴)
- 응답 시간 예측 가능 — worst case = (N-1) × quantum
- 시분할 시스템(timesharing)의 기본

**단점**:
- 우선순위 개념 없음 — I/O bound vs CPU bound 차별 불가
- 짧은 job 이 긴 job 뒤에 끼면 응답 느림
- quantum 튜닝이 워크로드 의존적
- 모든 job 을 동등 취급 → 실제 사용성과 안 맞음

**활용 예시**:
- 교과서 / 교육용 OS
- 네트워크 패킷 스케줄러 (Cisco IOS WFQ 변형)
- 실시간 안 중요한 임베디드 RTOS 의 기본 모드
- 컨테이너 런타임의 CPU shares 의 기반

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆ (직접 사용은 줄었지만 다른 알고리즘의 기반)

**C 코드**:
```c
// Round-Robin Scheduling — 가장 단순한 구현
#define QUANTUM_MS  20

typedef struct Process {
    int pid;
    int remaining_burst;   // 남은 CPU 시간
    struct Process *next;  // FIFO queue
} Process;

typedef struct {
    Process *head;
    Process *tail;
} RunQueue;

static RunQueue rq;
static Process *current;

void rq_enqueue(Process *p) {
    p->next = NULL;
    if (!rq.head) {
        rq.head = rq.tail = p;
    } else {
        rq.tail->next = p;
        rq.tail = p;
    }
}

Process *rq_dequeue(void) {
    Process *p = rq.head;
    if (p) {
        rq.head = p->next;
        if (!rq.head) rq.tail = NULL;
    }
    return p;
}

// Timer interrupt handler — quantum 만료 시 호출
void timer_tick(void) {
    if (!current) return;
    current->remaining_burst -= QUANTUM_MS;
    if (current->remaining_burst <= 0) {
        // 완료 — queue 에 다시 넣지 않음
        free_process(current);
    } else {
        // quantum 소진 — queue 끝으로
        rq_enqueue(current);
    }
    schedule();
}

void schedule(void) {
    current = rq_dequeue();
    if (current) {
        set_timer(QUANTUM_MS);
        context_switch_to(current);
    } else {
        idle();
    }
}

// 의사코드 - quantum 크기 분석:
//   Q = quantum, T_cs = context switch cost
//   CPU 효율 = Q / (Q + T_cs)
//
//   Q = 100ms, T_cs = 0.1ms → 99.9% 효율, 응답 N×100ms
//   Q = 1ms,   T_cs = 0.1ms → 90.9% 효율, 응답 N×1ms
//
//   trade-off: 짧을수록 응답성↑ but throughput↓
//
//   I/O bound process: quantum 다 못 쓰고 block → 다른 queue 변형 필요 (MLFQ)
//   CPU bound process: quantum 항상 다 씀 → fair share
```

**관련 알고리즘**: FCFS, MLFQ, CFS, Priority Scheduling, SJF

---

<a id="cfs"></a>
## 6. CFS (Completely Fair Scheduler, 완전 공정 스케줄러)

**목적**: Linux 의 default 스케줄러(2.6.23 ~ 6.5, 6.6+ EEVDF 로 대체). **virtual runtime(vruntime)** 기반으로 모든 task 에 CPU 시간을 비례 배분, "이상적인 multitasking CPU" 의 근사

**시간 복잡도**: 선택 O(1) (RB-tree 최좌측), 삽입/삭제 O(log N)

**공간 복잡도**: O(N) — N = runnable task 수, 자료구조는 RB-tree

**특징**:
- **vruntime**: 각 task 가 "이상적인 CPU 의 1/N 속도로 실행했다면 받았어야 할 시간". CPU 를 쓸수록 증가
- **RB-Tree (sched_entity → vruntime)**: 가장 작은 vruntime 의 task 가 left-most node → 다음 실행
- **nice value (priority)**: -20 ~ +19. weight = `1024 / (1.25^nice)`. vruntime 증가율 ∝ 1/weight
- **Scheduling Period**: 모든 runnable task 가 한 번씩 실행되는 주기 (default 6ms, task 수에 따라 조정)
- **Minimum Granularity**: 최소 slice (default 0.75ms) — task 너무 많아도 너무 짧게 자르지 않음
- **Sleep 보정**: 깨어난 task 의 vruntime 을 min_vruntime 근처로 — starvation 없이 빠른 응답
- 작성자: Ingo Molnár (2007, Linux 2.6.23)
- 후속: EEVDF (Earliest Eligible Virtual Deadline First, Linux 6.6+)

**장점**:
- O(1) scheduling pick (RB-tree left-most caching)
- 공정성 수학적 보장 — vruntime 이 균등하게 진행
- nice value 로 부드러운 priority 조절
- I/O bound task 가 sleep 후 깨어나도 starve 안 함
- heuristic 없는 순수 수학 모델

**단점**:
- nice 값 의미가 직관적이지 않음 (1.25배 weight ratio)
- 실시간(RT) 보장 없음 — RT scheduler (`SCHED_FIFO`, `SCHED_RR`) 별도
- migration 비용 — multi-core 에서 load balancing 복잡
- cgroup hierarchy 와 합쳐지면 매우 복잡

**활용 예시**:
- **Linux kernel default** (2.6.23 ~ 6.5)
- Android (Linux kernel) — task group + cpufreq governor 와 통합
- Docker / Kubernetes CPU shares (cgroup v1/v2 의 cpu.shares 가 CFS weight)
- 사실상 모든 server-side Linux

**난이도**: 매우 높음 | **사용 빈도**: ★★★★★

**C 코드**:
```c
// CFS — Linux kernel/sched/fair.c 의 단순화 버전
#include <stdint.h>

// nice → weight 테이블 (kernel/sched/sched.h sched_prio_to_weight)
static const uint32_t sched_prio_to_weight[40] = {
    /* -20 */ 88761, 71755, 56483, 46273, 36291,
    /* -15 */ 29154, 23254, 18705, 14949, 11916,
    /* -10 */  9548,  7620,  6100,  4904,  3906,
    /*  -5 */  3121,  2501,  1991,  1586,  1277,
    /*   0 */  1024,   820,   655,   526,   423,
    /*   5 */   335,   272,   215,   172,   137,
    /*  10 */   110,    87,    70,    56,    45,
    /*  15 */    36,    29,    23,    18,    15,
};

typedef struct sched_entity {
    uint64_t vruntime;          // virtual runtime (ns)
    uint64_t exec_start;        // 현재 실행 시작 시각
    uint64_t sum_exec_runtime;  // 누적 실제 실행 시간
    int      nice;
    struct rb_node run_node;    // RB-tree node
} sched_entity_t;

typedef struct cfs_rq {
    struct rb_root tasks_timeline;
    struct rb_node *leftmost;   // 캐시된 최소 vruntime node
    uint64_t min_vruntime;
    unsigned int nr_running;
    uint64_t load_weight;       // sum of weights
} cfs_rq_t;

// vruntime 증가량 = delta_exec × NICE_0_LOAD / weight
//   weight 가 크면(nice 낮으면) vruntime 천천히 증가 → 더 자주 선택됨
static uint64_t calc_delta_vruntime(uint64_t delta_exec, int nice) {
    uint32_t weight = sched_prio_to_weight[nice + 20];
    return (delta_exec * 1024) / weight;   // NICE_0_LOAD = 1024
}

// Task 가 CPU 를 쓴 만큼 vruntime 증가
void update_curr(cfs_rq_t *cfs_rq, sched_entity_t *curr, uint64_t now) {
    uint64_t delta = now - curr->exec_start;
    curr->exec_start = now;
    curr->sum_exec_runtime += delta;
    curr->vruntime += calc_delta_vruntime(delta, curr->nice);
    if (curr->vruntime < cfs_rq->min_vruntime)
        cfs_rq->min_vruntime = curr->vruntime;
}

// 다음 실행 task = RB-tree 의 leftmost (최소 vruntime)
sched_entity_t *pick_next_task(cfs_rq_t *cfs_rq) {
    if (!cfs_rq->leftmost) return NULL;
    return rb_entry(cfs_rq->leftmost, sched_entity_t, run_node);
}

// Task 추가 — vruntime 기준 RB-tree 삽입
void enqueue_entity(cfs_rq_t *cfs_rq, sched_entity_t *se) {
    // sleep 에서 깨어난 경우 vruntime 보정 (너무 옛 vruntime 이면 monopolize)
    if (se->vruntime < cfs_rq->min_vruntime - SCHED_LATENCY)
        se->vruntime = cfs_rq->min_vruntime - SCHED_LATENCY;
    rb_insert(&cfs_rq->tasks_timeline, &se->run_node, se->vruntime);
    cfs_rq->nr_running++;
}

// Timer tick — quantum 만료 검사
void task_tick(cfs_rq_t *cfs_rq, sched_entity_t *curr, uint64_t now) {
    update_curr(cfs_rq, curr, now);
    // 동일 nice 가정 하 ideal_runtime = period / nr_running
    uint64_t ideal = SCHED_PERIOD / cfs_rq->nr_running;
    if (curr->sum_exec_runtime - curr->prev_sum_exec > ideal) {
        // preempt
        resched_curr();
    }
}

// 의사코드 - CFS 의 핵심 직관:
//   "이상적인 CPU 는 N 개의 task 를 1/N 속도로 동시에 실행"
//   vruntime = "이 task 가 이상적 CPU 에서라면 받았어야 할 시간"
//   → vruntime 작은 task = 덜 받음 = 다음에 줘야 함
//
//   nice = -5 (높은 우선순위, weight=3121) 가 nice=0 (weight=1024) 보다 3배 자주 실행
//   → CPU bandwidth 비율 = weight 비
```

**관련 알고리즘**: Red-Black Tree, Round-Robin, EEVDF, MLFQ, Fair Queueing (네트워크)

---

<a id="mlfq"></a>
## 7. MLFQ (Multi-Level Feedback Queue, 다단계 피드백 큐)

**목적**: 사전 정보 없이도 **I/O bound vs CPU bound** task 를 자동으로 분류하여, 짧은 interactive job 응답성과 긴 batch job throughput 을 동시에 달성

**시간 복잡도**: 스케줄 선택 O(K) (K = 큐 개수, 보통 3~64), 큐 내부는 RR

**공간 복잡도**: O(N + K) — N task, K queue

**특징**:
- 여러 우선순위 큐 (Q0 > Q1 > Q2 > ...) — 각 큐는 RR
- Rule 1: 우선순위 높은 큐에 task 있으면 그 큐만 실행
- Rule 2: 같은 큐는 RR
- Rule 3: 새 task 는 최상위 큐(Q0) 진입
- Rule 4: quantum 다 쓰면 한 단계 강등 (Q1 → Q2 → ...)
- Rule 4-개선: 같은 큐 내 누적 사용 시간이 임계 초과 시 강등 (gaming 방지)
- Rule 5: **Periodic Priority Boost** — 일정 주기마다 모든 task 를 Q0 으로 (starvation 방지)
- I/O 자주 하는 task → quantum 다 안 쓰고 block → 우선순위 유지 → 응답 빠름
- CPU 만 도는 batch → 강등 → 낮은 우선순위에서 RR
- Corbató, MIT CTSS (1962) — 가장 오래된 adaptive 스케줄러

**장점**:
- 사전 정보 없이도 task 특성 자동 학습
- interactive 응답성 우수 (I/O bound 가 Q0 유지)
- CPU bound 도 starve 안 함 (boost)
- 휴리스틱이지만 실용적으로 매우 효과적

**단점**:
- 튜닝 파라미터 많음 (quantum per queue, boost interval, demotion threshold)
- "gaming" 가능 — quantum 직전 sleep 으로 강등 회피 (Rule 4-개선이 대응)
- 진정한 fairness 보장 없음 (CFS 처럼 수학적이지 않음)
- I/O burst pattern 변화에 즉각 적응 못 함

**활용 예시**:
- **macOS / XNU kernel** — Mach scheduler 기반 + iOS
- **Windows NT** — 32 priority level + dynamic boost
- **Solaris** TS class
- **FreeBSD ULE** scheduler
- BSD 4.3 의 기본

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**C 코드**:
```c
// MLFQ — Tanenbaum 교과서 스타일
#define NUM_QUEUES   4
#define BOOST_INTERVAL_MS  1000

typedef struct Task {
    int      pid;
    int      queue_level;       // 현재 큐 (0 = highest)
    uint64_t accumulated;       // 현재 큐에서 누적 실행 시간
    struct Task *next;
} Task;

typedef struct {
    Task    *head, *tail;
    uint32_t quantum_ms;        // 큐별 quantum (낮은 우선순위일수록 김)
    uint32_t allotment_ms;      // 강등 임계
} Queue;

static Queue queues[NUM_QUEUES] = {
    { NULL, NULL,   8,  16 },   // Q0: quantum 8ms, 16ms 누적 시 강등
    { NULL, NULL,  16,  32 },
    { NULL, NULL,  32,  64 },
    { NULL, NULL, 100, 9999 },  // Q3: 사실상 강등 없음 (최하위)
};
static uint64_t last_boost;

void q_enqueue(int level, Task *t) {
    t->queue_level = level;
    t->next = NULL;
    Queue *q = &queues[level];
    if (!q->head) q->head = q->tail = t;
    else { q->tail->next = t; q->tail = t; }
}

Task *pick_next(void) {
    // 가장 높은 우선순위 큐부터 탐색
    for (int i = 0; i < NUM_QUEUES; i++) {
        if (queues[i].head) {
            Task *t = queues[i].head;
            queues[i].head = t->next;
            if (!queues[i].head) queues[i].tail = NULL;
            return t;
        }
    }
    return NULL;
}

// 새 task 도착 → Q0
void task_arrive(Task *t) {
    t->accumulated = 0;
    q_enqueue(0, t);
}

// Quantum 소진 (timer interrupt)
void on_quantum_expired(Task *t) {
    int level = t->queue_level;
    t->accumulated += queues[level].quantum_ms;
    if (t->accumulated >= queues[level].allotment_ms && level < NUM_QUEUES - 1) {
        // 강등
        t->accumulated = 0;
        q_enqueue(level + 1, t);
    } else {
        // 같은 큐 RR
        q_enqueue(level, t);
    }
}

// Task 가 I/O 로 block → 깨어나면 같은 큐 유지 (또는 한 단계 승급)
void on_io_complete(Task *t) {
    q_enqueue(t->queue_level, t);  // 우선순위 유지 = interactive 보너스
}

// Periodic boost — starvation 방지
void priority_boost(uint64_t now) {
    if (now - last_boost < BOOST_INTERVAL_MS) return;
    last_boost = now;
    // 모든 큐의 task 를 Q0 으로 이동
    for (int i = 1; i < NUM_QUEUES; i++) {
        while (queues[i].head) {
            Task *t = queues[i].head;
            queues[i].head = t->next;
            t->accumulated = 0;
            q_enqueue(0, t);
        }
        queues[i].tail = NULL;
    }
}

// 의사코드 - MLFQ 가 자동으로 분류하는 이유:
//   I/O bound task: quantum 다 못 쓰고 block → on_io_complete → 같은 큐 유지
//   CPU bound task: quantum 다 씀 → on_quantum_expired → 강등
//
//   결과: 자연스럽게 interactive 가 상위, batch 가 하위
//   → "사전 정보 없이 SJF 비슷한 효과" — Corbató 의 핵심 통찰
```

**관련 알고리즘**: Round-Robin, CFS, Priority Scheduling, Lottery Scheduling, Stride Scheduling

---

<a id="slab-allocator"></a>
## 8. Slab Allocator (슬랩 할당자)

**목적**: 커널이 같은 크기·같은 타입 객체를 자주 할당/해제할 때, **초기화 비용**과 **internal fragmentation** 을 함께 줄이는 object cache 할당자

**시간 복잡도**: alloc/free 평균 O(1) (per-CPU cache hit), worst O(1) page 할당

**공간 복잡도**: O(객체 타입 수 × slab 크기)

**특징**:
- **Cache (kmem_cache)**: 같은 타입 객체 전용 풀 — 예: `task_struct`, `inode`, `dentry`
- **Slab**: 한 cache 안의 연속 메모리 페이지 묶음 (보통 1~수 페이지) — 객체 다수 보관
- **Object**: cache 가 관리하는 단위 — 초기화된 상태로 보관됨 (constructor 한 번만 실행)
- 3 상태 slab: **full** (모두 사용), **partial** (일부 free), **empty** (모두 free)
- alloc 우선순위: partial slab → empty slab → 새 slab 할당
- **Per-CPU cache (SLUB/SLAB)**: 각 CPU 마다 작은 free list — lock 없는 alloc/free
- 변형: **SLAB**(원조, Bonwick 1994), **SLUB**(2007 simplification, Linux default), **SLOB**(작은 시스템용)

**장점**:
- alloc 시 초기화 비용 절약 — 객체가 이미 초기화된 상태
- internal fragmentation 거의 없음 (정확한 크기 슬랏)
- cache 친화적 (객체가 메모리에 모여 있음)
- per-CPU 캐시로 lock contention 거의 없음

**단점**:
- 객체 타입 사전 등록 필요 (cache 마다 `kmem_cache_create`)
- 객체 타입 너무 다양하면 slab 수 폭증
- 같은 크기 다른 타입을 한 cache 로 묶으면 false sharing
- external fragmentation 가능 (partial slab 이 많이 남으면)

**활용 예시**:
- **Linux kernel** — `kmalloc` 의 backend (size-N cache), `task_struct`, `inode`, `dentry`, `skb`
- **FreeBSD UMA (Universal Memory Allocator)**
- **Solaris** (Bonwick 의 원작)
- userspace: jemalloc, tcmalloc 의 size-class 와 유사 아이디어

**난이도**: 높음 | **사용 빈도**: ★★★★★ (커널 거의 모든 작은 할당)

**C 코드**:
```c
// Slab Allocator — SLUB 단순화 버전
typedef struct kmem_cache kmem_cache_t;
typedef void (*ctor_fn)(void *obj);

typedef struct Slab {
    void   *base;             // page 들의 시작
    size_t  free_count;
    void   *free_list;        // 빈 슬랏의 single-linked list (free 객체 안에 next 포인터)
    struct Slab *next;
} Slab;

typedef struct kmem_cache {
    const char *name;
    size_t      obj_size;
    size_t      slab_size;    // 보통 (PAGE_SIZE × 2^order)
    size_t      obj_per_slab;
    ctor_fn     ctor;

    Slab *full;
    Slab *partial;
    Slab *empty;

    // per-CPU cache — 빠른 경로
    void *cpu_freelist[MAX_CPUS];
} kmem_cache_t;

// 새 slab 페이지 할당 + 객체들을 freelist 로 chain + 각각 ctor 호출
static Slab *grow_cache(kmem_cache_t *c) {
    void *page = alloc_pages(c->slab_size);
    Slab *s = malloc(sizeof(Slab));
    s->base = page;
    s->free_count = c->obj_per_slab;
    s->free_list = NULL;

    // 객체 슬랏 순회 — 각 슬랏을 next 포인터 chain 으로 link
    for (size_t i = 0; i < c->obj_per_slab; i++) {
        void *obj = (char *)page + i * c->obj_size;
        if (c->ctor) c->ctor(obj);          // 초기화 1회
        *(void **)obj = s->free_list;
        s->free_list = obj;
    }
    s->next = c->empty;
    c->empty = s;
    return s;
}

void *kmem_cache_alloc(kmem_cache_t *c) {
    int cpu = current_cpu();

    // Fast path: per-CPU freelist
    if (c->cpu_freelist[cpu]) {
        void *obj = c->cpu_freelist[cpu];
        c->cpu_freelist[cpu] = *(void **)obj;
        return obj;
    }

    // Slow path: partial 또는 empty slab 에서 가져옴
    Slab *s = c->partial ? c->partial : (c->empty ? c->empty : grow_cache(c));
    void *obj = s->free_list;
    s->free_list = *(void **)obj;
    s->free_count--;

    // slab 상태 전이
    if (s->free_count == 0) {
        // partial/empty → full
        move_slab(s, &c->full);
    } else if (c->empty == s) {
        move_slab(s, &c->partial);
    }
    return obj;
}

void kmem_cache_free(kmem_cache_t *c, void *obj) {
    int cpu = current_cpu();
    // ctor 가 한 초기화 상태를 유지해야 함 — destructor 없음
    *(void **)obj = c->cpu_freelist[cpu];
    c->cpu_freelist[cpu] = obj;
}

kmem_cache_t *kmem_cache_create(const char *name, size_t obj_size, ctor_fn ctor) {
    kmem_cache_t *c = calloc(1, sizeof(*c));
    c->name = name;
    c->obj_size = MAX(obj_size, sizeof(void *));  // freelist next 포인터 자리
    c->slab_size = PAGE_SIZE;
    c->obj_per_slab = c->slab_size / c->obj_size;
    c->ctor = ctor;
    return c;
}

// 의사코드 - Bonwick 의 핵심 통찰:
//   "객체 초기화는 객체 할당과 분리되어야 한다"
//   매번 alloc 마다 fields 0 세팅 + lock init + list head 초기화 = 비용
//   → cache 안에 머무는 동안 초기화 상태 유지 = 재할당 시 zero cost
//
//   예: Linux task_struct = 거대 구조체 + 많은 sublocks
//        fork() 마다 kmem_cache_alloc("task_struct") → 이미 init 된 객체 받음
```

**관련 알고리즘**: Buddy Allocator (slab 의 page 공급원), Free List, Pool Allocator, jemalloc/tcmalloc size-class

---

<a id="buddy-allocator"></a>
## 9. Buddy Allocator (버디 할당자)

**목적**: 커널 페이지 단위 할당에서 **external fragmentation 을 분할/병합으로 제어**하는 2^k 블록 할당자. slab 의 아래 계층

**시간 복잡도**: alloc/free O(log N) — N = 최대 order

**공간 복잡도**: O(MAX_ORDER × log) free list 헤더 + bitmap

**특징**:
- 메모리를 2^0, 2^1, ..., 2^MAX_ORDER 페이지 블록으로 나눠 관리 (Linux MAX_ORDER=11 → 최대 2^10 × 4KB = 4MB)
- order-k free list — 크기 2^k 블록들의 리스트
- alloc(order k):
  1. order k free list 비어있으면 order k+1 블록을 분할 (재귀)
  2. 분할 후 한 쪽은 사용, 다른 쪽 ("buddy") 은 order k free list 로
- free(block, order k):
  1. buddy 주소 계산: `buddy = block XOR (1 << k)`
  2. buddy 도 free 상태면 병합 → order k+1 로 free (재귀)
- buddy 주소 계산이 XOR 한 번 — 매우 빠름
- Knuth Vol.1 (1968)

**장점**:
- alloc/free O(log N)
- external fragmentation 작음 (병합으로 큰 블록 회복)
- 큰 연속 블록 할당 가능
- buddy 위치 계산 O(1) (XOR)

**단점**:
- internal fragmentation — 1.5×2^k 요청 시 2^(k+1) 할당 → 최대 50% 낭비
- 2^k 만 가능 → 불규칙 크기엔 slab 위에 얹어야 함
- MAX_ORDER 초과 크기 할당 어려움 (Linux: contiguous allocator CMA 별도)
- order 가 높을수록 병합 실패 확률 증가 (fragmentation)

**활용 예시**:
- **Linux kernel** — page allocator (`alloc_pages`, `__get_free_pages`)
- **FreeBSD vm** — 변형
- **jemalloc** chunk allocator (변형)
- 임베디드 RTOS heap

**난이도**: 중간 | **사용 빈도**: ★★★★★ (커널 모든 페이지 할당의 기반)

**C 코드**:
```c
// Buddy Allocator — Linux page allocator 단순화 버전
#include <stdint.h>
#include <stdbool.h>

#define MAX_ORDER       11          // 2^0 ~ 2^10 페이지
#define PAGE_SIZE       4096
#define PAGE_SHIFT      12

typedef struct PageBlock {
    struct PageBlock *next;
    struct PageBlock *prev;
    int               order;        // 현재 블록 크기 = 2^order 페이지
    bool              free;
} PageBlock;

static PageBlock *free_lists[MAX_ORDER + 1];
static uintptr_t  heap_base;
static PageBlock *page_meta;        // page frame metadata 배열

static inline PageBlock *block_at(uintptr_t addr) {
    size_t idx = (addr - heap_base) >> PAGE_SHIFT;
    return &page_meta[idx];
}

// buddy 주소 — XOR 한 번
static inline uintptr_t buddy_addr(uintptr_t addr, int order) {
    uintptr_t offset = addr - heap_base;
    uintptr_t buddy_off = offset ^ ((uintptr_t)PAGE_SIZE << order);
    return heap_base + buddy_off;
}

static void list_add(PageBlock **list, PageBlock *b) {
    b->prev = NULL;
    b->next = *list;
    if (*list) (*list)->prev = b;
    *list = b;
}

static void list_del(PageBlock **list, PageBlock *b) {
    if (b->prev) b->prev->next = b->next;
    else         *list = b->next;
    if (b->next) b->next->prev = b->prev;
}

// 큰 블록을 두 buddy 로 분할
static void split_block(PageBlock *b, int target_order) {
    while (b->order > target_order) {
        b->order--;
        uintptr_t addr = heap_base + (b - page_meta) * PAGE_SIZE;
        uintptr_t buddy = addr + ((uintptr_t)PAGE_SIZE << b->order);
        PageBlock *bb = block_at(buddy);
        bb->order = b->order;
        bb->free = true;
        list_add(&free_lists[b->order], bb);
    }
}

void *alloc_pages(int order) {
    // 1) 요구 order 이상의 free list 탐색
    int k = order;
    while (k <= MAX_ORDER && !free_lists[k]) k++;
    if (k > MAX_ORDER) return NULL;     // OOM

    PageBlock *b = free_lists[k];
    list_del(&free_lists[k], b);
    b->free = false;

    // 2) 너무 크면 buddy 로 분할
    if (k > order) {
        b->order = k;
        split_block(b, order);
    }
    return (void *)(heap_base + (b - page_meta) * PAGE_SIZE);
}

void free_pages(void *ptr, int order) {
    uintptr_t addr = (uintptr_t)ptr;
    PageBlock *b = block_at(addr);
    b->free = true;
    b->order = order;

    // 3) buddy 와 반복 병합
    while (b->order < MAX_ORDER) {
        uintptr_t baddr = buddy_addr(addr, b->order);
        PageBlock *buddy = block_at(baddr);
        if (!buddy->free || buddy->order != b->order) break;

        // buddy 도 free → 병합
        list_del(&free_lists[buddy->order], buddy);
        if (baddr < addr) {
            addr = baddr;
            b = buddy;
        }
        b->order++;
    }
    list_add(&free_lists[b->order], b);
}

// 의사코드 - buddy XOR 의 마법:
//   주소 offset 의 비트 표현에서 order k 비트를 뒤집으면 buddy
//
//   offset 0x0000 ─┐ order 2 (16KB) blocks
//   offset 0x4000 ─┘  ← buddy of 0x0000 (XOR 0x4000)
//   offset 0x8000 ─┐
//   offset 0xC000 ─┘  ← buddy of 0x8000
//
//   병합 시: 0x0000 + 0x4000 → 0x0000 order 3 (32KB) block
//   그 다음 buddy: 0x8000 (XOR 0x8000)
//
//   → 분할/병합 모두 O(1) 비트 연산
```

**관련 알고리즘**: Slab Allocator (위 계층), First-Fit / Best-Fit, jemalloc chunk, Linux CMA

---

<a id="epoll-kqueue-iouring"></a>
## 10. epoll / kqueue / io_uring (I/O Multiplexing)

**목적**: 한 스레드가 수만~수십만 동시 연결을 효율적으로 처리하기 위한 커널의 **이벤트 알림** 메커니즘. 동기 I/O 의 한계(select/poll 의 O(N))를 O(1) 알림으로 극복

**시간 복잡도**:
- select / poll: O(N) per call (모든 fd 스캔)
- **epoll / kqueue**: O(1) 등록, O(준비된 fd 수) 알림
- **io_uring**: O(1) submit + completion — 사실상 syscall-free

**공간 복잡도**: epoll/kqueue O(N) ready list, io_uring O(SQ/CQ 깊이) 공유 ring

**특징**:
- **select/poll** (POSIX): 매 호출마다 모든 fd 를 userspace ↔ kernel 복사 후 검사 → O(N²) 성격
- **epoll** (Linux 2.6, 2002):
  - `epoll_create` → epfd
  - `epoll_ctl(epfd, ADD/MOD/DEL, fd, event)` — 한 번 등록
  - `epoll_wait(epfd, events, max, timeout)` — 준비된 것만 반환
  - **Edge-triggered (ET)** vs **Level-triggered (LT)** 모드
- **kqueue** (FreeBSD/macOS, 2000): 더 일반적 — 파일/소켓/타이머/시그널/프로세스 이벤트 통합
- **io_uring** (Linux 5.1, 2019):
  - userspace ↔ kernel 공유 ring buffer 2개: **Submission Queue (SQ)**, **Completion Queue (CQ)**
  - syscall 없이 SQE(Submission Queue Entry)를 enqueue, kernel 이 CQE 로 응답
  - read/write/accept/openat/timeout 등 모든 I/O 지원
  - SQPOLL 모드: kernel thread 가 SQ 폴링 → syscall 0회
- **Reactor / Proactor** 패턴의 OS 기반

**장점**:
- epoll/kqueue: O(N) → O(ready) — C10K, C100K 문제 해결
- io_uring: zero-syscall I/O, batched submission, fully async — 디스크 I/O 까지 async
- Edge-triggered + nonblock = 최소 syscall 수
- io_uring 은 buffered read/write 도 async (kqueue 는 file I/O async 제한적)

**단점**:
- epoll: ET 모드 정확히 쓰기 까다로움 (EAGAIN 까지 drain 해야 함)
- epoll: file I/O async 안 됨 (regular file 은 항상 ready)
- io_uring: 보안 이슈 다수(과거) — Google ChromeOS 비활성, 일부 환경에서 제한
- io_uring API 빠르게 변화 — liburing 권장
- Windows IOCP 는 완전히 다른 모델 (proactor)

**활용 예시**:
- **nginx, HAProxy** — epoll/kqueue
- **Redis** — epoll/kqueue (ae.c)
- **Node.js** — libuv → epoll/kqueue/IOCP 추상화
- **Netty (JVM)** — Native epoll/kqueue transport
- **PostgreSQL 16+, ScyllaDB, RocksDB** — io_uring
- **fio, liburing 기반 db**

**난이도**: 중간 (epoll) ~ 매우 높음 (io_uring) | **사용 빈도**: ★★★★★

**C 코드**:
```c
// 1) epoll — 가장 흔한 패턴 (edge-triggered)
#include <sys/epoll.h>
#include <fcntl.h>
#include <unistd.h>

void make_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

void run_epoll_server(int listen_fd) {
    int epfd = epoll_create1(0);
    struct epoll_event ev = { .events = EPOLLIN | EPOLLET, .data.fd = listen_fd };
    epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

    struct epoll_event events[1024];
    char buf[4096];
    while (1) {
        int n = epoll_wait(epfd, events, 1024, -1);
        for (int i = 0; i < n; i++) {
            int fd = events[i].data.fd;
            if (fd == listen_fd) {
                // ET: EAGAIN 까지 모두 accept
                while (1) {
                    int c = accept4(listen_fd, NULL, NULL, SOCK_NONBLOCK);
                    if (c < 0) break;
                    struct epoll_event cev = { .events = EPOLLIN | EPOLLET, .data.fd = c };
                    epoll_ctl(epfd, EPOLL_CTL_ADD, c, &cev);
                }
            } else if (events[i].events & EPOLLIN) {
                // ET: 모든 데이터 소진
                while (1) {
                    ssize_t r = read(fd, buf, sizeof(buf));
                    if (r <= 0) { if (r == 0 || errno != EAGAIN) close(fd); break; }
                    handle_request(fd, buf, r);
                }
            }
        }
    }
}

// 2) io_uring — submission/completion queue
//
//   userspace                          kernel
//   ┌──────────────┐                  ┌──────────────┐
//   │ Submission   │  ─ SQE entries ─>│  io_uring    │
//   │ Queue (SQ)   │                  │  worker      │
//   │ ring buffer  │                  │              │
//   └──────────────┘                  └──────────────┘
//          ▲                                  │
//          │                                  ▼
//   ┌──────────────┐                  ┌──────────────┐
//   │ Completion   │ <─ CQE entries ──│              │
//   │ Queue (CQ)   │                  │              │
//   │ ring buffer  │                  │              │
//   └──────────────┘                  └──────────────┘
//
//   SQ/CQ 는 mmap 으로 userspace ↔ kernel 공유
//   io_uring_enter() syscall 1번으로 submit + wait completion 가능
//   SQPOLL 모드: kernel thread 가 SQ 폴링 → syscall 0회

#include <liburing.h>

void run_io_uring_server(int listen_fd) {
    struct io_uring ring;
    io_uring_queue_init(256, &ring, 0);

    // accept 요청 미리 submit
    struct sockaddr_storage cli; socklen_t clen = sizeof(cli);
    struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_accept(sqe, listen_fd, (struct sockaddr *)&cli, &clen, 0);
    io_uring_sqe_set_data(sqe, (void *)(uintptr_t)OP_ACCEPT);
    io_uring_submit(&ring);

    struct io_uring_cqe *cqe;
    while (io_uring_wait_cqe(&ring, &cqe) == 0) {
        uintptr_t op = (uintptr_t)io_uring_cqe_get_data(cqe);
        if (op == OP_ACCEPT) {
            int c = cqe->res;
            // 다음 accept 즉시 재submit
            struct io_uring_sqe *s = io_uring_get_sqe(&ring);
            io_uring_prep_accept(s, listen_fd, NULL, NULL, 0);
            io_uring_sqe_set_data(s, (void *)(uintptr_t)OP_ACCEPT);
            // read 도 동시에 submit
            struct io_uring_sqe *r = io_uring_get_sqe(&ring);
            char *buf = alloc_buf();
            io_uring_prep_read(r, c, buf, 4096, 0);
            io_uring_sqe_set_data(r, make_read_ctx(c, buf));
            io_uring_submit(&ring);
        } else if (is_read(op)) {
            handle_read_completion(cqe, &ring);
        }
        io_uring_cqe_seen(&ring, cqe);
    }
}

// 의사코드 - LT vs ET (epoll mode):
//   LT (Level-Triggered, default): "지금 데이터 있음" 이 사실인 동안 계속 알림
//      → 한 번 read 후 EAGAIN 안 나도 됨, 다음 epoll_wait 에서 또 알림
//      → 안전하지만 wake-up 많음
//   ET (Edge-Triggered): "0 → 1 전이" 만 알림
//      → 알림 받으면 EAGAIN 까지 drain 필수
//      → wake-up 적지만 코드 까다로움
//   nginx/HAProxy 는 ET + nonblock 표준 패턴
```

**관련 알고리즘**: Reactor pattern, Proactor pattern (Windows IOCP), Coroutine + epoll (Go runtime, Tokio)

---

<a id="page-replacement"></a>
## 11. Page Replacement: LRU / Clock / LFU / ARC

**목적**: 물리 메모리가 가득 찼을 때, page fault 발생 시 어느 페이지를 **victim** 으로 내쫓을지 결정. **temporal locality** 를 근사

**시간 복잡도**:
- LRU 이상적: O(1) (doubly linked list + hash)
- Clock: 평균 O(1), worst O(N)
- LFU: O(log N) (count 정렬)
- ARC: O(1) amortized

**공간 복잡도**: O(N) — N = 페이지 수 + 메타데이터

**특징**:
- **Belady's Optimal (OPT)**: 가장 멀리 사용될 페이지 추방 — 미래 정보 필요, 이론적 최적. 다른 알고리즘 평가의 기준
- **LRU (Least Recently Used)**: 가장 오래 안 쓰인 페이지 추방. 이상적 LRU 는 비싼 자료구조 필요
- **Clock (Second Chance)**: LRU 의 근사. 페이지마다 **reference bit (R)**, 시계 바늘이 돌면서:
  - R=1: R=0 으로 reset, 한 번 더 기회
  - R=0: victim 선택
- **Enhanced Clock (Linux)**: R 비트 + **dirty bit (D)** 조합 4 상태 (R,D)=(0,0)→(0,1)→(1,0)→(1,1)
- **LFU (Least Frequently Used)**: 가장 적게 쓰인 페이지. 오래된 hot page 추방 안 함 → 변형 필요(aging)
- **ARC (Adaptive Replacement Cache)**, Megiddo & Modha (IBM, 2003): LRU recency + LFU frequency 동시 추적, ghost list 로 self-tuning
- **2Q / LIRS / CAR / Clock-Pro**: 단일 LRU 의 약점(scan resistance) 보완

**장점/단점 비교**:
| 알고리즘 | 장점 | 단점 |
|---------|------|------|
| LRU | 직관적, locality 좋음 | 비싼 자료구조, scan 에 약함 |
| Clock | O(1), 하드웨어 친화적 | LRU 보다 약간 부정확 |
| LFU | hot page 안정적 | 오래된 hot 못 빼냄(aging 필요) |
| ARC | self-tuning, 거의 모든 워크로드 강함 | 특허 이슈(만료), 메모리 2x |
| Clock-Pro | scan resistance | 구현 복잡 |

**활용 예시**:
- **Linux kernel** — 2 list LRU (active + inactive) + Clock-Pro 같은 변형 (Multi-Gen LRU, MGLRU 5.16+)
- **PostgreSQL buffer pool** — Clock-Sweep
- **MySQL InnoDB** — LRU + midpoint insertion (LRU-K 변형)
- **ZFS ARC** — ARC 직접 구현
- **Redis maxmemory-policy** — `allkeys-lru`, `allkeys-lfu`, `volatile-lfu`, `allkeys-random`
- **CPython** `functools.lru_cache` — LRU
- 모든 OS page cache, 모든 DB buffer pool

**난이도**: 중간 (LRU/Clock) ~ 높음 (ARC) | **사용 빈도**: ★★★★★

**C 코드**:
```c
// 1) LRU — doubly linked list + hash
typedef struct PageNode {
    uintptr_t addr;
    struct PageNode *prev, *next;
} PageNode;

typedef struct {
    PageNode *head, *tail;     // head = MRU, tail = LRU
    HashMap  *map;             // addr → PageNode
    size_t    capacity, size;
} LRUCache;

static void lru_move_to_front(LRUCache *c, PageNode *n) {
    if (c->head == n) return;
    // unlink
    n->prev->next = n->next;
    if (n->next) n->next->prev = n->prev;
    else         c->tail = n->prev;
    // link at head
    n->prev = NULL;
    n->next = c->head;
    c->head->prev = n;
    c->head = n;
}

void lru_touch(LRUCache *c, uintptr_t addr) {
    PageNode *n = hash_get(c->map, addr);
    if (n) {
        lru_move_to_front(c, n);
        return;
    }
    // miss
    if (c->size == c->capacity) {
        // evict LRU
        PageNode *victim = c->tail;
        hash_del(c->map, victim->addr);
        c->tail = victim->prev;
        if (c->tail) c->tail->next = NULL;
        else         c->head = NULL;
        free(victim);
        c->size--;
    }
    n = calloc(1, sizeof(*n));
    n->addr = addr;
    n->next = c->head;
    if (c->head) c->head->prev = n;
    c->head = n;
    if (!c->tail) c->tail = n;
    hash_put(c->map, addr, n);
    c->size++;
}

// 2) Clock (Second-Chance)
typedef struct {
    uintptr_t addr;
    uint8_t   ref_bit;
    uint8_t   in_use;
} ClockFrame;

static ClockFrame *frames;
static size_t      frame_count;
static size_t      clock_hand;

uintptr_t clock_select_victim(void) {
    while (1) {
        ClockFrame *f = &frames[clock_hand];
        if (f->in_use && f->ref_bit) {
            f->ref_bit = 0;       // 한 번 더 기회
        } else if (f->in_use) {
            uintptr_t victim = f->addr;
            clock_hand = (clock_hand + 1) % frame_count;
            return victim;
        }
        clock_hand = (clock_hand + 1) % frame_count;
    }
}

void clock_access(uintptr_t addr) {
    // page table walk 시 하드웨어가 자동으로 ref_bit=1 세팅
    // (소프트웨어로 시뮬레이션)
    for (size_t i = 0; i < frame_count; i++) {
        if (frames[i].in_use && frames[i].addr == addr) {
            frames[i].ref_bit = 1;
            return;
        }
    }
}

// 3) ARC — recency + frequency + ghost lists
//
//   T1 (recent)      |  T2 (frequent)
//   ───[ B1 ghost ][T1][T2][ B2 ghost ]───
//   c = total capacity
//   p = target size of T1 (adaptive)
//
//   Hit in T1 → move to T2 head (앞으로 frequent 로 간주)
//   Hit in T2 → move to T2 head (recency 갱신)
//   Hit in B1 (T1 ghost) → p += δ (recency 가 부족 — T1 늘림), pull from T2
//   Hit in B2 (T2 ghost) → p -= δ (frequency 가 부족 — T2 늘림), pull from T1
//   Miss in all → 새 페이지를 T1 head 로, evict T1 또는 T2 tail
//
//   ghost list 는 페이지 데이터 없이 메타데이터만 보관 → 메모리 추가 작음

// 의사코드 - Belady's Anomaly:
//   FIFO 는 페이지 프레임 수를 늘리면 fault 가 더 늘어날 수도 있음 (역설)
//   LRU/Clock/OPT 는 stack property → 절대 증가하지 않음
//
//   따라서 production 시스템에서는 FIFO 회피, LRU 계열 사용
```

**관련 알고리즘**: LRU Cache (data-structures.md), 2Q, LIRS, Multi-Gen LRU (MGLRU), Clock-Pro

---

<a id="mesi-cache-coherence"></a>
## 12. MESI Cache Coherence (캐시 일관성 프로토콜)

**목적**: 멀티코어 시스템에서 각 코어의 L1/L2 캐시가 동일 메모리 위치에 대해 **일관된 값** 을 보게 하는 하드웨어 프로토콜. lock-free 알고리즘의 정확성의 기반

**시간 복잡도**: cache line 전이 O(1) 하드웨어, 그러나 cross-socket 시 latency 100~300 cycles

**공간 복잡도**: 각 cache line 마다 2 bit 상태 + 디렉토리(또는 snoop bus)

**특징**:
- 4 상태 (cache line 단위, 보통 64 bytes):
  - **M (Modified)**: 이 캐시만 가짐 + dirty (메모리와 다름). 쓰기 가능
  - **E (Exclusive)**: 이 캐시만 가짐 + clean (메모리와 같음). 쓰기 가능 (M 으로 전이)
  - **S (Shared)**: 여러 캐시가 가짐 + clean. 읽기 only
  - **I (Invalid)**: 이 캐시에는 없음
- 전이 트리거: 로컬 read/write + 다른 코어의 read/write (snoop bus 또는 directory)
- 변종:
  - **MESIF** (Intel QPI): F (Forward) — Shared 중 한 코어가 응답 대표
  - **MOESI** (AMD): O (Owner) — Modified shared with others
  - **MSI**: 가장 단순 (E 없음)
- **False Sharing**: 서로 다른 변수가 같은 cache line 에 있으면, 두 코어가 각자 변수를 써도 line 이 핑퐁
- **Cache Coherence Latency**: L1 hit ≈ 1ns, 같은 socket L1↔L1 ≈ 30ns, cross-socket ≈ 100ns

**장점**:
- 프로그래머에게 거의 투명 — 그냥 변수 쓰면 됨
- 강한 일관성 (sequential consistency 에 가까움, 완전한 SC 는 아님 — store buffer 때문)
- atomic 명령(LOCK CMPXCHG)이 MESI 위에서 작동

**단점**:
- 작성 시 보이지 않는 비용 — false sharing 으로 100배 성능 차
- snoop traffic 이 코어 수에 따라 증가 — 디렉토리 기반 NUMA 가 대안
- M→S 전이 시 메모리 writeback 또는 dirty share 필요
- **Store Buffer + Invalidate Queue** 로 약한 메모리 모델 발생 → memory barrier 필요

**활용 예시**:
- 모든 현대 x86, ARM, RISC-V 멀티코어 CPU
- `std::atomic` / `AtomicInteger` 가 MESI 위에서 동작
- 성능 튜닝: cache line padding (`alignas(64)`, `@Contended`)
- Disruptor (LMAX), Aeron — false sharing 회피 설계
- Lock-Free DS, RCU 의 정확성 보장

**난이도**: 매우 높음 | **사용 빈도**: ★★★★★ (이해는 모든 시스템 프로그래머 필수)

**C 코드 + 상태도**:
```c
// MESI 상태 전이 (의사코드)
typedef enum { M, E, S, I } MesiState;

typedef struct CacheLine {
    uint64_t  addr;
    MesiState state;
    uint8_t   data[64];
} CacheLine;

// 로컬 read
void local_read(CacheLine *line) {
    switch (line->state) {
        case M: /* 그대로 사용 */ break;
        case E: /* 그대로 사용 */ break;
        case S: /* 그대로 사용 */ break;
        case I:
            // snoop bus 로 다른 캐시에 BusRd 전송
            if (any_other_has_modified(line->addr)) {
                // 그 캐시가 M → 메모리에 writeback + S 로 전이
                request_dirty_share(line);
                line->state = S;
            } else if (any_other_has(line->addr)) {
                line->state = S;  // 공유
            } else {
                line->state = E;  // 나만 — exclusive
            }
            fetch_from_memory(line);
            break;
    }
}

// 로컬 write
void local_write(CacheLine *line, uint8_t *new_data) {
    switch (line->state) {
        case M:
            // 그대로 modify
            memcpy(line->data, new_data, 64);
            break;
        case E:
            // 나만 가지고 있음 → 그냥 M 으로
            memcpy(line->data, new_data, 64);
            line->state = M;
            break;
        case S:
            // 다른 캐시들이 가지고 있음 → invalidate 브로드캐스트
            broadcast_invalidate(line->addr);
            memcpy(line->data, new_data, 64);
            line->state = M;
            break;
        case I:
            // 1) BusRdX 로 가져오면서 모두 invalidate
            broadcast_read_for_ownership(line->addr);
            fetch_from_memory(line);
            memcpy(line->data, new_data, 64);
            line->state = M;
            break;
    }
}

// 다른 코어의 read snoop (이 캐시가 가진 line 에 대해)
void on_remote_read(CacheLine *line) {
    switch (line->state) {
        case M:
            // 메모리에 writeback + S 로
            writeback_to_memory(line);
            line->state = S;
            break;
        case E:
            line->state = S;   // 더 이상 exclusive 아님
            break;
        case S:
        case I:
            // 변화 없음
            break;
    }
}

// 다른 코어의 write snoop
void on_remote_write(CacheLine *line) {
    switch (line->state) {
        case M:
            writeback_to_memory(line);
            line->state = I;
            break;
        case E:
        case S:
            line->state = I;
            break;
        case I:
            break;
    }
}

// MESI 상태도 (요약):
//
//                local W
//          ┌──────────────────┐
//          ▼                  │
//  ┌──>(I)──local R──>(E)──local W──>(M)
//  │    │                │              │
//  │    │ remote R       │ remote R     │ remote R
//  │    │                ▼              ▼
//  │    └─local R──>(S)<──(S)         (S) (writeback)
//  │                  │
//  │ remote W         │ remote W
//  └──────────────────┘
//
//  E (Exclusive) 가 핵심:
//    read miss 시 다른 캐시에 없으면 E → 다음 write 시 broadcast 불필요
//    write contention 없을 때 매우 빠름

// False Sharing 예시 — 같은 cache line 의 다른 변수
struct BadCounters {
    uint64_t a;     // CPU 0 이 자주 씀
    uint64_t b;     // CPU 1 이 자주 씀
};                   // 두 변수가 같은 64B line → 핑퐁

// 해결: padding
struct GoodCounters {
    alignas(64) uint64_t a;  // 자기 line 독점
    alignas(64) uint64_t b;  // 자기 line 독점
};
// → MESI 핑퐁 회피, 성능 10~100배

// 의사코드 - Store Buffer 가 만드는 약한 모델:
//   CPU 가 write 를 cache 에 즉시 반영하지 않고 store buffer 에 먼저 넣음
//   → 다른 CPU 는 잠시 옛 값을 봄 → sequential consistency 깨짐
//   → memory barrier (mfence, dmb) 필요
//   → 이것이 concurrent.md 의 Memory Barriers 알고리즘과 연결
```

**관련 알고리즘**: CAS, LL-SC, Memory Barriers (concurrent.md), False Sharing 회피, NUMA Directory Protocol
