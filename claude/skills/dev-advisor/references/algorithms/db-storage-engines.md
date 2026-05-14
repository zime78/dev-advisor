# DB 스토리지 엔진 알고리즘 (Database Storage Engine Algorithms)

DB 내부의 정평 있는 10 알고리즘. WAL / LSM / SSTable / Compaction / MVCC / Buffer Pool / Page Layout / B-Link / Replication / HOT Update. **`db-indexes.md`** (인덱스 구조) 와 별개의 **트랜잭션·로깅·페이지 관리** 영역.

**원전·표준 참고**:
- Mohan, Haderle, Lindsay, Pirahesh, Schwarz — *ARIES: A Transaction Recovery Method* (TODS, 1992)
- Patrick O'Neil, Edward Cheng, Dieter Gawlick, Elizabeth O'Neil — *The Log-Structured Merge-Tree* (Acta Informatica, 1996)
- Fay Chang et al. — *Bigtable: A Distributed Storage System* (OSDI, 2006) — SSTable
- Hellerstein, Stonebraker, Hamilton — *Architecture of a Database System* (FnTDB, 2007)
- Andy Pavlo — *Database Internals* (Alex Petrov, 2019)
- Philip Lehman, S. Bing Yao — *Efficient Locking for Concurrent Operations on B-Trees* (TODS, 1981)
- Designing Data-Intensive Applications (Kleppmann, 2017)

## 알고리즘 목차

| ID | 알고리즘 | 카테고리 | 용도 |
|----|---------|---------|------|
| [wal](#wal) | Write-Ahead Log | Durability | commit 보장 |
| [lsm-tree](#lsm-tree) | LSM Tree | Write-Opt | 쓰기 최적화 |
| [sstable](#sstable) | SSTable | Storage | sorted key file |
| [compaction-strategy](#compaction-strategy) | Compaction | LSM mgmt | size/leveled tiered |
| [mvcc-vacuum](#mvcc-vacuum) | MVCC Vacuum | GC | dead tuple |
| [buffer-pool](#buffer-pool) | Buffer Pool | Cache | hot page |
| [page-layout-slotted](#page-layout-slotted) | Page Layout | Storage | tuple in page |
| [b-link-tree](#b-link-tree) | B-Link Tree | Index | concurrent B-Tree |
| [replication-log](#replication-log) | Replication Log | Replica | WAL/Binlog 스트림 |
| [hot-update](#hot-update) | HOT Update | Optimization | PG index 회피 |

**관련 카탈로그**:
- [db-indexes.md](db-indexes.md) — B+Tree / Hash / GIN (인덱스 구조)
- [data-structures.md](data-structures.md) — B-Tree / Skip List / Bloom Filter
- [concurrent.md](concurrent.md) — MVCC, Hazard Pointer
- [`../patterns/distributed.md`](../patterns/distributed.md) — Event Sourcing / Outbox (시스템 측 WAL)

---

<a id="wal"></a>
## 1. Write-Ahead Log (WAL)

**목적**: commit 된 트랜잭션의 변경사항이 디스크 손실/크래시 후에도 보존되도록 보장(Durability). 데이터 페이지보다 **먼저** log record 를 영속화하는 것이 핵심.

**알고리즘** (ARIES 기반 의사코드):
```
// 1. 트랜잭션 변경 시
on UPDATE(tx, page, before, after):
    LSN = log.append({ tx, page, before, after, prev_lsn })
    page.pageLSN = LSN          // 페이지 헤더에 LSN 기록
    page.dirty  = true
    // page 는 아직 디스크에 안 써도 됨 — log 만 보장

// 2. Commit 시
on COMMIT(tx):
    LSN = log.append({ tx, type: COMMIT })
    fsync(log)                  // ← Durability point. log 가 디스크에 내려가야 commit 응답
    return OK

// 3. Recovery (재시작 시)
recover():
    // (a) Analysis: 마지막 checkpoint 이후 log scan
    //     → active tx 와 dirty page 식별
    // (b) Redo: pageLSN < record.LSN 인 모든 변경 재적용
    //          (commit 안 된 tx 변경도 포함 — repeating history)
    // (c) Undo: commit 안 된 tx 를 역순으로 취소
    //          (CLR = Compensation Log Record 남김 → idempotent)
```

**WAL fsync 순서 (가장 중요한 invariant)**:
```
1. 메모리에 변경 적용 (page in buffer pool)
2. 변경에 대응하는 log record 작성
3. log fsync → 디스크 영속화         ← Durability 확보
4. (이 시점에 commit 응답 가능)
5. 나중에 background writer 가 dirty page flush
6. checkpoint 시 page fsync
```
**핵심 원칙**: "log first, data later". data page 가 log 보다 먼저 디스크에 가면 crash 시 undo 불가능.

**시간/공간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Log append | O(1) 메모리 + sequential write |
| Commit | O(1) + 1 fsync |
| Recovery | O(log_size) — 마지막 checkpoint 이후 |

**장점**:
- Durability 와 Atomicity 동시 보장
- random write 를 sequential log write 로 변환 → 디스크 친화
- group commit 으로 다수 트랜잭션의 fsync 비용 분산

**단점**:
- 매 commit 마다 fsync → throughput 상한이 디스크 IOPS 에 묶임
- 2배 쓰기 (log + data page) — write amplification
- log 크기 무한 증가 방지 위해 checkpoint 와 archival 필요

**실제 DB 매핑**:

| DB | WAL 이름 | 옵션 |
|---|---|---|
| PostgreSQL | WAL (pg_wal/) | `wal_level`, `synchronous_commit` |
| MySQL InnoDB | Redo Log (ib_logfile*) | `innodb_flush_log_at_trx_commit` |
| SQLite | Rollback Journal / WAL mode | `PRAGMA journal_mode=WAL` |
| Oracle | Redo Log | online/archived |
| SQL Server | Transaction Log (.ldf) | `RECOVERY FULL/SIMPLE` |

**SQL 예제**:
```sql
-- PostgreSQL: WAL 동작 확인
SHOW wal_level;                 -- minimal/replica/logical
SHOW synchronous_commit;        -- on/off/local/remote_apply

-- 그룹 커밋 튜닝
ALTER SYSTEM SET commit_delay = 1000;       -- µs
ALTER SYSTEM SET commit_siblings = 5;

-- MySQL InnoDB: redo log fsync 정책
SET GLOBAL innodb_flush_log_at_trx_commit = 1;
-- 1 = 매 commit fsync (ACID), 2 = OS cache 만, 0 = 1초마다
```

**관련 알고리즘**: [LSM Tree](#lsm-tree) (commit log 와 MemTable), [Replication Log](#replication-log), [Buffer Pool](#buffer-pool)

---

<a id="lsm-tree"></a>
## 2. LSM Tree (Log-Structured Merge Tree)

**목적**: 무작위 쓰기를 sequential write 로 변환하여 SSD/HDD 쓰기 처리량을 극대화. 쓰기 우위 워크로드(시계열, 카운터, 로그)에 최적.

**알고리즘**:
```
// 쓰기 경로
on PUT(key, value):
    wal.append({ key, value })          // (1) commit log
    memtable.insert(key, value)         // (2) in-memory sorted structure (Skip List or Red-Black Tree)
    if memtable.size > THRESHOLD:
        flush_memtable_to_sstable()     // (3) immutable SSTable 로 dump

// 읽기 경로
on GET(key):
    // 최신순으로 탐색
    if v = memtable.find(key):     return v
    for sst in sstables_newest_to_oldest():
        if not sst.bloom.contains(key):  continue   // (4) Bloom Filter 로 skip
        if v = sst.lookup(key):    return v
    return NOT_FOUND

// 백그라운드
periodically:
    compact_sstables()                  // (5) 중복/tombstone 제거
```

**LSM vs B+Tree write amplification 비교**:
```
B+Tree update:
  [ disk page ] → modify in place → fsync → 1× write (단, random)
  추가로 WAL → 총 2× sequential

LSM Tree update:
  [ WAL ] → [ MemTable ] → [ L0 SSTable ] → [ L1 ] → [ L2 ] → ...
              sequential       compaction      compaction
  Write amplification = 1 + (Levels × FanOut)   typical 10~30×
  단, 모든 쓰기가 sequential — SSD wear leveling 친화
```

**시간/공간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Write | O(1) amortized (MemTable insert + WAL append) |
| Read (point lookup) | O(L × log n) — L = level 수 |
| Read with Bloom | 평균적으로 L0~L1 에서 해결 |
| Range scan | O(L × log n + k) |
| Compaction | O(n) sequential scan |

**장점**:
- 쓰기 처리량이 B+Tree 대비 수십배 (sequential write)
- 압축률 우수 (immutable file → 압축 친화)
- crash 시 WAL replay 로 복구 단순

**단점**:
- read amplification — 여러 SSTable 을 뒤져야 함 (Bloom + cache 로 완화)
- write amplification — compaction 으로 같은 데이터를 여러 번 다시 씀
- space amplification — tombstone, 미회수 중복 데이터

**실제 DB 매핑**:

| 시스템 | 비고 |
|---|---|
| LevelDB / RocksDB | LSM 의 사실상 reference 구현 |
| Cassandra | size-tiered compaction 기본 |
| HBase | Bigtable 기반 LSM |
| ScyllaDB | RocksDB 대안, shard-per-core |
| TiKV / CockroachDB | RocksDB/Pebble 위 distributed |
| SQLite (3.x) | B+Tree (LSM 아님) ↔ 차이 명확 |

**관련 알고리즘**: [SSTable](#sstable), [Compaction Strategy](#compaction-strategy), [Skip List](data-structures.md), [Bloom Filter](probabilistic.md), [WAL](#wal)

---

<a id="sstable"></a>
## 3. SSTable (Sorted String Table)

**목적**: 키-값 쌍을 키로 정렬한 immutable 파일 포맷. LSM Tree 의 디스크 표현. Bigtable(2006) 에서 유래.

**파일 레이아웃**:
```
+------------------------------------+
| Data Block 0   (key-value sorted)  |
| Data Block 1                       |
| Data Block 2                       |
| ...                                |
+------------------------------------+
| Filter Block (Bloom Filter)        |
+------------------------------------+
| Index Block (sparse: key → offset) |
+------------------------------------+
| Footer (magic, index offset)       |
+------------------------------------+
```

**알고리즘** (lookup):
```c
// SSTable lookup pseudocode
Value* sst_get(SSTable* sst, Key k) {
    // (1) Bloom Filter 로 빠른 not-found 판정
    if (!bloom_check(sst->filter, k)) return NOT_FOUND;

    // (2) Index Block 에서 binary search → data block 위치
    Block* block = index_find_block(sst->index, k);

    // (3) data block 내부에서 binary search
    return block_binary_search(block, k);
}
```

**시간/공간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Lookup | O(log n) (index + block) |
| Range scan | O(log n + k) |
| Write | sequential O(n) (flush 시점) |
| Update / Delete | **불가** — 새 SSTable 에 tombstone 으로 마킹 |

**장점**:
- immutable → 동시 읽기 lock-free, fsync 후 캐싱 안전
- 정렬되어 있어 range scan O(log n + k)
- 압축 친화 (snappy, zstd, lz4)
- Bloom + sparse index 로 disk seek 최소화

**단점**:
- 직접 update 불가 → tombstone + compaction 필요
- 공간 amplification (구버전 중복)
- 한 키의 최신값을 찾으려면 여러 SSTable 탐색 (Compaction 이 해소)

**실제 DB 매핑**:

| 시스템 | SSTable 변형 |
|---|---|
| LevelDB / RocksDB | `.sst` / `.ldb` |
| Cassandra | `*-Data.db` + Index.db + Filter.db + Summary.db |
| HBase | HFile (SSTable + meta) |
| Bigtable | Original SSTable |

**관련 알고리즘**: [LSM Tree](#lsm-tree), [Compaction Strategy](#compaction-strategy), [Bloom Filter](probabilistic.md), [Binary Search](searching.md)

---

<a id="compaction-strategy"></a>
## 4. Compaction Strategy (컴팩션 전략)

**목적**: SSTable 의 중복·tombstone·구버전을 병합하여 (1) 공간 회수, (2) 읽기 amplification 감소. LSM 의 핵심 운영 변수.

**두 가지 주요 전략**:

### Size-Tiered Compaction (STCS) — Cassandra 기본
```
L0:  [SST] [SST] [SST] [SST]      ← 같은 크기 4개 모이면
                ↓ 병합
L1:  [SST  big  ]
     [SST] [SST] [SST] [SST]      ← 다시 큰 게 4개 모이면
                ↓
L2:  [SST  bigger ]
```
- 같은 size tier 의 SSTable N(보통 4)개가 모이면 1개로 병합
- 쓰기 amplification ≈ log N (낮음)
- 읽기 amplification ≈ tier 수 (높음)
- space amplification 최악 2× — 병합 중 임시로 원본+사본 공존

### Leveled Compaction (LCS) — LevelDB/RocksDB 기본
```
L0: overlap 허용 (fan-in 영역)
L1: 10 MB    non-overlap, 키 범위로 정렬
L2: 100 MB   non-overlap
L3: 1 GB     non-overlap
...
```
- 각 레벨은 직전 레벨의 ~10배 크기
- L_n 의 SSTable 들은 키 범위가 **겹치지 않음** → point lookup 시 레벨당 SSTable 1개만 검사
- 쓰기 amplification ≈ FanOut × Levels (높음, ~25×)
- 읽기 amplification ≈ Levels 만큼 (낮음, ~7)
- space amplification 작음 (~1.1×)

**복잡도/특성 비교**:
| 항목 | Size-Tiered | Leveled |
|------|------------|---------|
| Write amp | 낮음 (log N) | 높음 (10~30×) |
| Read amp | 높음 | 낮음 |
| Space amp | 최악 2× | ~1.1× |
| 적합 | write-heavy | read-heavy, space-conscious |

**기타 전략**:
- **Time-Window Compaction (TWCS)** — Cassandra, 시계열 전용. 시간 윈도우 단위로만 병합 → TTL expiration 효율
- **Universal Compaction** — RocksDB, size-tiered 변형

**실제 DB 매핑**:

| DB | 기본 전략 | 옵션 |
|---|---|---|
| Cassandra | Size-Tiered | `LeveledCompactionStrategy`, `TimeWindowCompactionStrategy` |
| RocksDB | Leveled | `kCompactionStyleUniversal`, `kCompactionStyleFIFO` |
| HBase | Size-Tiered (Stripe 변형) | DateTieredCompactionPolicy |
| ScyllaDB | Size-Tiered | LCS/TWCS/ICS |

**관련 알고리즘**: [LSM Tree](#lsm-tree), [SSTable](#sstable), [External Merge Sort](sorting.md)

---

<a id="mvcc-vacuum"></a>
## 5. MVCC Vacuum / Garbage Collection

**목적**: MVCC(Multi-Version Concurrency Control) 환경에서 더 이상 어떤 트랜잭션도 볼 수 없는 **dead tuple** 을 회수해 디스크/메모리 공간을 확보. PostgreSQL VACUUM 이 대표.

**MVCC 배경**:
- UPDATE 는 in-place 가 아니라 **새 버전 생성** + 구버전에 `xmax` 마킹
- DELETE 도 즉시 제거가 아니라 `xmax` 만 설정
- 결과: dead tuple 이 누적 → "table bloat"

**알고리즘** (PostgreSQL VACUUM 의사코드):
```
vacuum_table(table):
    xmin_horizon = oldest_active_xid()    // 가장 오래된 활성 tx
    for page in table.pages:
        for tuple in page:
            if tuple.xmax != 0
              and tuple.xmax < xmin_horizon
              and tuple_committed(tuple.xmax):
                // 더 이상 누구도 못 보는 dead tuple
                mark_for_removal(tuple)
        if page.has_dead_tuples:
            // 1단계: 인덱스에서 ItemPointer 제거
            for idx in table.indexes:
                idx.remove_dead_pointers(page)
            // 2단계: dead tuple 슬롯 회수, 페이지 compaction
            compact_page(page)
            update_visibility_map(page)
            update_free_space_map(page)
```

**시간/공간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| VACUUM (lazy) | O(n) page scan, O(d) dead tuple |
| VACUUM FULL | O(n) — 전체 테이블 재작성, ACCESS EXCLUSIVE lock |
| Auto-vacuum trigger | dead tuple > `autovacuum_vacuum_threshold + scale × n` |

**장점**:
- read 트랜잭션을 차단하지 않음 (lazy VACUUM)
- visibility map 으로 다음 VACUUM 이 깨끗한 페이지 skip
- index-only scan 가능하게 함

**단점**:
- long-running transaction 이 xmin_horizon 을 막으면 VACUUM 이 무력해짐 → bloat 폭증
- VACUUM FULL 은 lock 이 매우 강함 → 운영 중 사용 어려움
- 매우 큰 테이블의 VACUUM 은 시간/I-O 비용 큼

**실제 DB 매핑**:

| DB | 메커니즘 | 비고 |
|---|---|---|
| PostgreSQL | VACUUM / autovacuum | xid wraparound 방지 의무적 |
| MySQL InnoDB | Purge thread + Undo log | rollback segment 정리 |
| Oracle | Undo Tablespace + automatic UNDO mgmt | ORA-01555 (snapshot too old) |
| SQL Server | Ghost Cleanup task | row versioning store (tempdb) |
| CockroachDB / TiDB | GC TTL + range cleanup | TTL 지난 MVCC 버전 제거 |

**SQL 예제**:
```sql
-- PostgreSQL: 수동 VACUUM
VACUUM ANALYZE orders;
VACUUM (VERBOSE, ANALYZE) orders;
-- bloat 확인
SELECT relname, n_dead_tup, n_live_tup,
       round(n_dead_tup::numeric / NULLIF(n_live_tup,0), 3) AS dead_ratio
  FROM pg_stat_user_tables
 ORDER BY n_dead_tup DESC LIMIT 10;

-- long-running tx 확인 (VACUUM 방해 요인)
SELECT pid, age(backend_xmin), state, query
  FROM pg_stat_activity
 WHERE backend_xmin IS NOT NULL
 ORDER BY age(backend_xmin) DESC;
```

**관련 알고리즘**: [Concurrent MVCC](concurrent.md), [HOT Update](#hot-update), [Buffer Pool](#buffer-pool)

---

<a id="buffer-pool"></a>
## 6. Buffer Pool / Page Cache

**목적**: 자주 접근되는 디스크 페이지를 메모리에 캐싱하여 random disk I/O 를 메모리 접근으로 대체. DB 성능에 가장 큰 영향을 주는 단일 컴포넌트.

**구조**:
```
+------------------------------------------------+
| Buffer Pool (e.g. 128 GB)                      |
|                                                |
| [Page A][Page B][Page C][Page D] ...           |
|                                                |
|  Hash Table: page_id → frame_id (lookup O(1))  |
|  Replacement Policy: LRU / Clock / LRU-K       |
|  Dirty bitmap                                  |
|  Pin count per page (eviction 방지)            |
+------------------------------------------------+
            ↑                ↓
         Read fault      Background writer
                             (dirty flush)
```

**알고리즘** (LRU 변형 — Clock):
```
on PAGE_REQUEST(page_id):
    frame = hash_table.lookup(page_id)
    if frame != null:
        frame.reference_bit = 1
        frame.pin_count++
        return frame
    // 캐시 미스 → eviction 필요
    victim = clock_select_victim()
    if victim.dirty:
        write_to_disk(victim)        // flush
    if victim.pageLSN > flushedLSN:
        flush_wal_up_to(victim.pageLSN)   // WAL rule
    new_frame = load_from_disk(page_id, victim)
    hash_table.insert(page_id, new_frame)
    return new_frame

clock_select_victim():               // Second-chance algorithm
    loop:
        f = frames[clock_hand]
        if f.pin_count == 0:
            if f.reference_bit == 0:
                return f             // victim
            else:
                f.reference_bit = 0  // 한 번 더 기회
        clock_hand = (clock_hand + 1) % N
```

**WAL 규칙과의 연동**:
- dirty page 를 디스크로 flush 하기 **전에** 해당 페이지의 pageLSN 까지 WAL 이 fsync 되어야 함 → `flushedLSN >= page.pageLSN`
- 위반 시 crash 후 redo 불가 → DB 손상

**시간/공간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Hit | O(1) — hash lookup |
| Miss + clean evict | O(1) + 1 disk read |
| Miss + dirty evict | O(1) + 1 write + 1 read |

**Replacement Policy 비교**:
| 정책 | 특성 |
|------|------|
| LRU | scan 부하에 약함 (sequential scan 이 hot page 를 밀어냄) |
| LRU-K (K=2) | 두 번 참조된 페이지만 hot 으로 승격 → scan 저항 |
| Clock (Second-chance) | LRU 근사, 구현 단순, 잠금 경합 적음 |
| MySQL midpoint LRU | LRU 리스트를 young/old 두 구역으로 분리 |

**장점**:
- random disk I/O → 메모리 접근으로 변환 (수천 배 빠름)
- WAL 과 결합하여 commit latency 와 무관하게 dirty flush 지연 가능

**단점**:
- 메모리가 부족하면 thrashing
- shared buffer pool 은 lock 경합 발생 (NUMA, partitioning 으로 완화)
- scan-heavy 워크로드가 hot page 를 밀어낼 수 있음

**실제 DB 매핑**:

| DB | 이름 | 옵션 |
|---|---|---|
| PostgreSQL | shared_buffers | clock-sweep, OS page cache 도 활용 |
| MySQL InnoDB | Buffer Pool | midpoint LRU, multiple instances |
| Oracle | Buffer Cache | LRU-K like (touch count) |
| SQL Server | Buffer Pool | LRU-K (K=2) |

**관련 알고리즘**: [LRU Cache (data-structures.md)](data-structures.md), [WAL](#wal), [Page Layout](#page-layout-slotted)

---

<a id="page-layout-slotted"></a>
## 7. Page Layout (Slotted Page)

**목적**: 가변 길이 tuple 을 고정 크기(8 KB/16 KB) 페이지에 효율적으로 배치하고, in-place 수정/삭제 시에도 ItemPointer(page_id, slot_no) 안정성을 유지.

**Slotted Page 구조**:
```
+---------------------------------------+ offset 0
| Page Header                           |
|   page_id, pageLSN, free_space_ptr,   |
|   slot_count, checksum, type          |
+---------------------------------------+
| Slot 0 → (offset, length)             |  ← slot directory grows down
| Slot 1 → (offset, length)             |
| Slot 2 → (offset, length)             |
+---------------------------------------+
|                                       |
|         Free Space                    |
|                                       |
+---------------------------------------+
|                       Tuple 2 data    |  ← tuple data grows up
+---------------------------------------+
|                       Tuple 1 data    |
+---------------------------------------+
|                       Tuple 0 data    |
+---------------------------------------+ offset PAGE_SIZE
```

**알고리즘** (insert):
```c
int slotted_insert(Page* p, char* tuple, int len) {
    if (p->free_space < len + sizeof(Slot)) return -1;  // 페이지 풀
    // (1) tuple 데이터를 페이지 끝에서부터 채움
    p->free_end -= len;
    memcpy(page_ptr + p->free_end, tuple, len);
    // (2) slot directory 끝에 새 slot 추가
    Slot s = { .offset = p->free_end, .length = len };
    p->slots[p->slot_count++] = s;
    p->free_space -= (len + sizeof(Slot));
    return p->slot_count - 1;       // slot_no 반환
}

int slotted_delete(Page* p, int slot_no) {
    p->slots[slot_no].offset = INVALID;   // tombstone
    // 실제 공간 회수는 page compaction 시
}

// 외부에서 tuple 참조 = ItemPointer (page_id, slot_no)
// tuple 이 페이지 내에서 이동해도 slot_no 는 안정
```

**시간/공간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Insert | O(1) (free space 충분 시) |
| Lookup by slot_no | O(1) |
| Delete (logical) | O(1) |
| Page compaction | O(n) — slot 수 |

**장점**:
- ItemPointer 가 안정 → 인덱스 entry 가 (page_id, slot_no) 만 들고 있으면 됨
- variable-length tuple 지원
- 페이지 내 free space 단편화를 compaction 으로 회수

**단점**:
- tuple 이 페이지 크기보다 크면 TOAST(PG) / off-page(InnoDB) 필요
- update 로 길이가 커지면 페이지 분할 또는 다른 페이지로 이동 (forwarding pointer)
- slot directory + 헤더 오버헤드

**Heap vs Index-Organized**:
| 구조 | 데이터 위치 |
|------|------------|
| Heap (PG) | 별도 heap file, 인덱스가 (page_id, slot_no) 참조 |
| Index-Organized / Clustered (InnoDB, Oracle IOT) | PK B+Tree 잎에 데이터 직접 저장 → secondary index 는 PK 를 참조 |

**실제 DB 매핑**:

| DB | 페이지 크기 | 명칭 |
|---|---|---|
| PostgreSQL | 8 KB | Page + Line Pointer |
| MySQL InnoDB | 16 KB | Index Page (Clustered + 잎 데이터) |
| Oracle | 2~32 KB | Data Block |
| SQL Server | 8 KB | Page |

**관련 알고리즘**: [Buffer Pool](#buffer-pool), [B+Tree](db-indexes.md), [HOT Update](#hot-update)

---

<a id="b-link-tree"></a>
## 8. B-Link Tree (Concurrent B-Tree)

**목적**: B-Tree 의 split-in-progress 상태에서도 reader 가 lock 없이 안전하게 탐색하도록, 각 노드에 우측 형제로의 **link pointer** 와 **high key** 를 추가. Lehman & Yao (1981).

**구조 차이**:
```
일반 B+Tree 노드:
+--------+-----+-----+-----+
| keys   | k1  | k2  | k3  |
+--------+-----+-----+-----+

B-Link Tree 노드:
+--------+-----+-----+-----+----------+-------------+
| keys   | k1  | k2  | k3  | high_key | right_link  |
+--------+-----+-----+-----+----------+-------------+

high_key = 이 노드(또는 분할되어 right 로 옮겨간 형제까지 포함)의 키 상한
right_link = 우측 형제 노드 포인터
```

**알고리즘** (search, lock 없이):
```
search(root, k):
    node = root
    while not node.is_leaf:
        // (1) 만약 split 중이라 k 가 이 노드 영역을 벗어났으면
        //     right link 따라 우측 형제로 이동
        while k > node.high_key and node.right_link != null:
            node = node.right_link              // ← move right
        node = node.child(k)
    // 잎에서도 같은 right-move 보정
    while k > node.high_key and node.right_link != null:
        node = node.right_link
    return node.lookup(k)
```

**Split 동작**:
```
1. 노드 N 분할 → N(좌), N'(우) 생성
2. N.right_link := N'                  ← 먼저 link 설정 (커밋 포인트)
3. N.high_key := split_key
4. (이 시점에 reader 가 와도 right_link 따라 N' 도달 가능)
5. parent 에 N' 의 separator 키 삽입 (parent split 가능 → 재귀)
```
**핵심**: 부모 갱신이 완료되기 전에도 자식 레벨에서 right link 만 있으면 검색이 옳다.

**시간/공간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Search | O(log n) + 평균 < 2 right-moves |
| Insert | O(log n) — leaf lock 만 |
| Concurrent ops | reader lock-free, writer leaf-level lock |

**장점**:
- reader 가 lock 없이 안전 → 높은 동시성
- writer 는 잎 노드만 잠금 → 트리 전체 lock coupling 불필요
- 부모 노드 업데이트를 lazy 하게 해도 안전

**단점**:
- 노드당 high_key + right_link 오버헤드
- 삭제 시 merge 처리는 여전히 복잡 (대부분 구현은 lazy delete + 주기적 cleanup)

**실제 DB 매핑**:

| DB | 비고 |
|---|---|
| PostgreSQL | nbtree (B-Link Tree 변형 — Lanin & Shasha 1986 기반) |
| Berkeley DB | B-Link Tree |
| LMDB | COW B+Tree (B-Link 아님, copy-on-write 로 동시성 해결) |
| InnoDB | B+Tree + latch coupling (B-Link 아님) |

**관련 알고리즘**: [B+Tree](db-indexes.md), [B-Tree](data-structures.md), [Hazard Pointer (concurrent.md)](concurrent.md)

---

<a id="replication-log"></a>
## 9. Replication Log (Binlog / WAL Streaming)

**목적**: 한 노드의 쓰기 로그를 다른 노드로 전송하여 복제본을 만들고, 장애 시 failover 또는 read scaling 을 제공. WAL/Redo 를 그대로 또는 변환하여 스트리밍.

**두 가지 복제 방식**:

### Physical Replication (페이지 단위 byte-level)
```
Primary WAL: "page 0x4F2A offset 32 → new bytes [...]"
                ↓ stream
Standby: 같은 byte 를 같은 페이지에 적용
```
- PostgreSQL streaming replication (`pg_basebackup` + `walreceiver`)
- 빠르고 단순, 단 **버전/플랫폼 동일 필수**
- 부분 객체(특정 테이블만) 복제 불가

### Logical Replication (논리 row 단위)
```
Primary: "INSERT INTO orders (id, amt) VALUES (1, 100)"  (또는 row image)
                ↓ stream (decoded)
Subscriber: 같은 SQL 또는 row 적용
```
- PostgreSQL `pgoutput`, Debezium, MySQL row-based binlog
- 다른 버전/스키마/DB 종류 간 복제 가능
- DDL 자동 전파 어려움, primary key 필수

### MySQL Binlog 3 formats
| Format | 내용 |
|--------|------|
| STATEMENT | 원본 SQL 그대로 (비결정성 함수 위험: `NOW()`, `UUID()`) |
| ROW | 변경된 행의 before/after image |
| MIXED | 기본 STATEMENT, 비결정성 감지 시 ROW |

**알고리즘** (streaming):
```
// Primary
on COMMIT(tx):
    log.append(records)
    fsync(log)
    notify_replication_workers(latest_lsn)

replication_worker(replica):
    while true:
        recs = log.read_since(replica.last_lsn)
        send(replica.conn, recs)
        if synchronous:
            wait_for_ack(replica.conn)        // 동기 복제

// Replica
on RECEIVE(records):
    apply_to_local(records)
    persist_local(records)                    // local WAL 에도 적재
    send_ack(primary, latest_lsn)
```

**동기성 옵션**:
| 모드 | commit 응답 조건 |
|------|----------------|
| async | primary 가 local fsync 만 (replica lag 가능) |
| semi-sync | primary + 적어도 1 replica 가 받음 (적용은 미보장) |
| sync (apply) | primary + replica 가 apply 완료까지 |

**시간/공간 복잡도**:
| 항목 | 비고 |
|------|------|
| Throughput 상한 | primary fsync + network bandwidth |
| Replica lag | async 에서 0~수초 (workload 의존) |

**장점**:
- read scaling, geographic distribution, point-in-time recovery
- 장애 시 failover

**단점**:
- replication lag → read-your-write 보장이 깨질 수 있음
- logical 은 large transaction, DDL, schema drift 에 취약
- physical 은 동일 버전 강제

**실제 DB 매핑**:

| DB | 방식 |
|---|---|
| PostgreSQL | physical(streaming) + logical(publication/subscription) |
| MySQL | binlog (STATEMENT/ROW/MIXED) + relay log |
| Oracle | Redo + Data Guard, GoldenGate |
| MongoDB | oplog (idempotent statements) |
| Kafka 기반 CDC | Debezium → Kafka |

**관련 알고리즘**: [WAL](#wal), [Consensus (Raft/Paxos)](consensus.md), [Event Sourcing](../patterns/distributed.md)

---

<a id="hot-update"></a>
## 10. HOT Update (Heap-Only Tuple)

**목적**: PostgreSQL 에서 UPDATE 시 인덱스 키가 변경되지 않은 경우 **인덱스 갱신을 회피**하고 같은 페이지 내에서 new tuple 을 chain 으로 연결. update-heavy 워크로드의 인덱스 쓰기 amplification 을 크게 줄임.

**MVCC + 인덱스 문제**:
- PG 의 UPDATE 는 새 tuple 버전 생성
- 일반적이라면 **모든 인덱스에** 새 tuple 의 ItemPointer 를 추가해야 함
- 인덱스가 5개면 update 1번에 인덱스 쓰기 5번 + bloat

**HOT 조건** (둘 다 만족 시):
1. **변경된 컬럼이 어떤 인덱스에도 포함되지 않음**
2. 새 tuple 이 **같은 페이지** 에 들어갈 free space 가 있음

**알고리즘**:
```
on UPDATE(old_tuple, new_values):
    if any_index_column_changed(old_tuple, new_values):
        goto regular_update;
    page = page_of(old_tuple);
    if page.free_space < tuple_size(new_values):
        goto regular_update;
    // HOT path
    new_tuple = allocate_on_same_page(page);
    new_tuple.data = new_values;
    new_tuple.xmin = current_xid;
    old_tuple.xmax = current_xid;
    old_tuple.t_ctid = new_tuple.ItemPointer;    // ← HOT chain link
    old_tuple.flags |= HEAP_HOT_UPDATED;
    new_tuple.flags |= HEAP_ONLY_TUPLE;
    // 인덱스는 건드리지 않음 — 인덱스 entry 는 여전히 old_tuple ItemPointer
    return;

// 인덱스 조회 경로
on INDEX_LOOKUP(key):
    item_ptr = index_find(key);          // 옛 ItemPointer 가 나옴
    tuple = heap_get(item_ptr);
    // HOT chain 따라 visible 버전 탐색
    while tuple.flags & HEAP_HOT_UPDATED:
        next = tuple.t_ctid;
        if visible_to_me(heap_get(next)): return heap_get(next);
        tuple = heap_get(next);
    return tuple if visible_to_me(tuple) else NOT_VISIBLE;
```

**HOT Pruning**:
- 페이지 접근 시 dead HOT chain 의 중간 버전들을 inline 으로 정리 (full VACUUM 불필요)
- VACUUM 보다 가벼움 → update-heavy 테이블의 bloat 자체 억제

**시간/공간 복잡도**:
| 작업 | regular update | HOT update |
|------|---------------|-----------|
| Heap write | 1 | 1 |
| Index writes | N (인덱스 수) | **0** |
| WAL 양 | 큼 | 작음 |
| Bloat | 큼 | 작음 (chain pruning) |

**장점**:
- 인덱스 쓰기 amplification 제거
- VACUUM 부담 감소 (HOT pruning 으로 inline 정리)
- update-heavy 테이블에서 throughput 크게 증가

**단점**:
- 같은 페이지 free space 가 부족하면 fallback → fillfactor 튜닝 필요
- 인덱스에 포함된 컬럼을 UPDATE 하면 HOT 불가
- HOT chain 이 길어지면 lookup 비용 증가 (pruning 이 해소)

**실제 DB 매핑**:

| DB | 메커니즘 | 비고 |
|---|---|---|
| PostgreSQL | HOT (8.3+) | `pg_stat_user_tables.n_tup_hot_upd` |
| MySQL InnoDB | (구조적으로 불필요) | secondary index 가 PK 를 참조하므로 행 이동 시 secondary 미수정 |
| Oracle | (구조 다름) | row migration / row chaining |

**SQL 예제**:
```sql
-- PostgreSQL: fillfactor 로 페이지 여유 확보 → HOT 비율 ↑
CREATE TABLE counters (
  id    INT PRIMARY KEY,
  total BIGINT,
  updated_at TIMESTAMP
) WITH (fillfactor = 80);     -- 페이지 20% 비워둠

CREATE INDEX idx_counters_total ON counters(total);
-- ⚠ total 컬럼이 인덱스에 포함되어 있으므로 total UPDATE 는 HOT 불가

-- HOT 활용도 측정
SELECT relname,
       n_tup_upd      AS total_updates,
       n_tup_hot_upd  AS hot_updates,
       round(n_tup_hot_upd::numeric / NULLIF(n_tup_upd, 0), 3) AS hot_ratio
  FROM pg_stat_user_tables
 ORDER BY n_tup_upd DESC LIMIT 10;
```

**관련 알고리즘**: [MVCC Vacuum](#mvcc-vacuum), [Page Layout](#page-layout-slotted), [Buffer Pool](#buffer-pool)

---

## 카탈로그 간 교차 참조

- **인덱스 자료구조** → [db-indexes.md](db-indexes.md) (B+Tree, Hash, GIN, GiST, BRIN, Covering, Partial, Bitmap)
- **순수 자료구조** → [data-structures.md](data-structures.md) (B-Tree, Skip List, Bloom Filter, LRU)
- **동시성 원시** → [concurrent.md](concurrent.md) (MVCC, Hazard Pointer, RCU)
- **분산 합의** → [consensus.md](consensus.md) (Raft, Paxos — 복제 로그 합의)
- **분산 패턴** → [`../patterns/distributed.md`](../patterns/distributed.md) (Event Sourcing, Outbox, CDC)
- **검색 알고리즘** → [searching.md](searching.md) (Binary Search — SSTable 내부)
- **확률 자료구조** → [probabilistic.md](probabilistic.md) (Bloom Filter — SSTable filter block)
- **정렬** → [sorting.md](sorting.md) (External Merge Sort — compaction)
