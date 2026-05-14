# Offline-First 앱 패턴 (Offline-First App Patterns)

인터넷 단절 상태에서도 동작하는 앱 8 패턴. **로컬 우선 (Local-First)** + **백그라운드 sync** 의 조합. PouchDB / RxDB / WatermelonDB / Realm Sync / Firebase Offline / Apollo Cache / Yjs / Automerge 사례.

**원전·표준 참고**:
- Martin Kleppmann et al. — *Local-First Software: You Own Your Data, in spite of the Cloud* (Ink & Switch, 2019)
- Martin Fowler & Pramod Sadalage — *NoSQL Distilled* (2012) — Eventual consistency 처리
- Apollo Client — Offline cache + optimistic UI 문서
- Realm Sync, Firebase Firestore Offline 문서
- CouchDB Replication Protocol

**핵심 원칙**:
- **Local-First** — 모든 읽기/쓰기는 로컬 DB 먼저, sync 는 백그라운드
- **Eventual Consistency** — 결국 수렴하지만 *언제* 일관성 회복 보장 없음
- **Conflict-aware UI** — 자동 머지 한계 인지, 사용자에게 노출

**관련 카탈로그**:
- [`../algorithms/distributed.md`](../algorithms/distributed.md) — CRDT (G/PN/OR/LWW Set), Vector Clock
- [mobile-app.md](mobile-app.md) — App Lifecycle / Background Task (sync 시점)
- [state-management.md](state-management.md) — CRDT-collab state, Optimistic Update
- [distributed.md](distributed.md) — Outbox Pattern (서버 측 대응)

---

## 1. Local-First Database (로컬 우선 데이터베이스)

<a id="local-first-db"></a>

**목적**: 모든 읽기/쓰기를 단말의 로컬 DB(SQLite · Realm · IndexedDB · WatermelonDB) 에 먼저 수행하고, 서버 동기화는 백그라운드에서 비동기로 처리합니다. 네트워크 의존성을 UX 경로에서 제거하여, 비행기·지하·공항·약한 셀룰러 환경에서도 앱이 즉시 반응합니다.

**핵심 메커니즘**:
- **단일 source of truth = 로컬 DB**: 화면은 항상 로컬 쿼리(reactive query) 를 구독. 네트워크 응답은 *로컬 DB 를 업데이트*할 뿐 직접 UI 로 보내지 않음
- **Storage 선택**: 모바일은 **SQLite (Room / GRDB / Drift)** 또는 **Realm**, 웹은 **IndexedDB (Dexie / RxDB)**, RN/Flutter 대용량은 **WatermelonDB**. Key-Value 만 필요하면 MMKV · AsyncStorage
- **Reactive Query**: 로컬 DB 변경 → Flow / Observable / `useLiveQuery` 로 UI 자동 갱신. SQLite 는 `update_hook` / Room `Flow<T>` / WatermelonDB `Q.observe()`
- **WAL (Write-Ahead Log) 모드**: SQLite 동시성 향상 필수. `PRAGMA journal_mode=WAL` — reader 가 writer 를 막지 않음
- **Schema versioning + migration**: 로컬 스키마가 서버보다 늦거나 빠를 수 있음. forward-compat 필요

**장점**:
- 네트워크 0ms — 즉각 UX
- 서버 장애 / 항공기 모드에서도 앱 사용 가능
- 배터리 절감 (network call 최소화)
- 서버 부하 분산 (사용자가 매번 fetch 하지 않음)

**단점·주의**:
- 디바이스 저장공간 소비 — 대용량 미디어는 lazy fetch
- 로컬 데이터의 staleness — TTL / refresh 정책 필요
- 단말 분실 시 데이터 노출 — Encrypted DB (SQLCipher, Realm encryption) 권장
- 멀티 디바이스 시 동기화 복잡도 폭증 (§2~§7 참조)

**활용 예시**: Notion (CRDT-based local cache), Linear (SQLite + sync engine), Figma (rope CRDT), Bear (CoreData + iCloud), Obsidian (markdown file + sync)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin (Android Room + Flow) 예제**:
```kotlin
@Entity(tableName = "notes")
data class NoteEntity(
    @PrimaryKey val id: String,
    val title: String,
    val body: String,
    val updatedAt: Long,
    val syncState: String, // "synced" | "pending" | "conflict"
)

@Dao
interface NoteDao {
    @Query("SELECT * FROM notes ORDER BY updatedAt DESC")
    fun observeAll(): Flow<List<NoteEntity>>          // reactive — UI 가 구독

    @Upsert
    suspend fun upsert(note: NoteEntity)               // 로컬 즉시 반영
}

class NoteRepository(private val dao: NoteDao, private val syncQueue: SyncQueue) {
    fun observeNotes(): Flow<List<NoteEntity>> = dao.observeAll()

    suspend fun saveNote(note: NoteEntity) {
        // 1) 로컬 DB 즉시 쓰기 — UI 가 reactive 로 갱신됨
        dao.upsert(note.copy(syncState = "pending", updatedAt = System.currentTimeMillis()))
        // 2) sync queue 에 등록 (네트워크 복귀 시 전송)
        syncQueue.enqueue(SyncOp.Upsert(note.id))
    }
}
```

**TypeScript (RxDB) 예제**:
```typescript
const db = await createRxDatabase({ name: 'notes', storage: getRxStorageDexie() });
await db.addCollections({
  notes: { schema: noteSchema }
});

// reactive query — UI 자동 갱신
db.notes.find().sort({ updatedAt: 'desc' }).$.subscribe(notes => render(notes));

// 로컬 즉시 쓰기
await db.notes.upsert({ id, title, body, updatedAt: Date.now(), syncState: 'pending' });
```

**관련 패턴**: [Sync Queue / Outbox](#sync-queue-outbox-client), [Optimistic UI with Rollback](#optimistic-ui-rollback), [Tombstone](#tombstone)

---

## 2. Sync Queue / Outbox (클라이언트 측 동기화 큐)

<a id="sync-queue-outbox-client"></a>

**목적**: 오프라인 상태에서 발생한 모든 변경(create / update / delete) 을 영속화된 큐에 순차 저장하고, 네트워크 복귀 시 서버로 순서대로 전송합니다. 서버 측 Outbox Pattern (DB ↔ 메시지 브로커) 과 대비되는 **클라이언트 ↔ 서버 outbox**.

**핵심 메커니즘**:
- **Persistent queue**: 단말 재시작 / process kill 에도 살아남아야 — SQLite 테이블, WorkManager + Room, Apollo `MutationQueue`
- **순서 보장**: 같은 entity 의 update 는 FIFO 로. 다른 entity 는 parallel 가능. `dependencies` 그래프로 표현
- **At-least-once 전달**: 멱등성 키 (Idempotency-Key) 필수 — 서버에서 중복 제거. distributed.md §6 참조
- **Exponential backoff retry**: `1s → 2s → 4s → 8s → 30s → 1min ...` 상한 (e.g. 5min). Jitter 추가로 thundering herd 방지
- **Dead Letter Queue (DLQ)**: 일정 횟수 초과 시 별도 테이블로 격리, 사용자에게 노출
- **트랜잭션 분리**: DB 쓰기와 큐 enqueue 를 **단일 트랜잭션** 으로 — 한쪽만 성공하는 상태 방지

**장점**:
- 오프라인 변경 손실 0
- 네트워크 복귀 시 자동 복원
- 사용자가 직접 retry 누를 필요 없음

**단점·주의**:
- 큐가 너무 길어지면 sync 폭발 (1000+ pending) — 압축 / coalescing 필요
- 같은 record 의 update 가 N 회 쌓이면 N-1 번이 낭비 — **coalescing** (마지막 상태만 전송)
- 큐 손상 시 사용자 데이터 유실 → DB 자체에 저장 (별도 파일 X)
- 인증 토큰 만료 시 전 큐가 stuck — 큐 재시작 메커니즘

**활용 예시**: Apollo `MutationQueue`, Firebase Firestore offline writes, AWS Amplify DataStore, WatermelonDB sync, Mailbox (legacy iOS), Trello (mobile)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin (WorkManager + Room) 예제**:
```kotlin
@Entity(tableName = "sync_queue")
data class SyncOp(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val opType: String,           // "create" | "update" | "delete"
    val entityType: String,
    val entityId: String,
    val payload: String,          // JSON
    val idempotencyKey: String,   // UUID
    val attempts: Int = 0,
    val createdAt: Long,
)

@Dao
interface SyncQueueDao {
    @Query("SELECT * FROM sync_queue ORDER BY id ASC LIMIT :n")
    suspend fun take(n: Int): List<SyncOp>

    @Query("DELETE FROM sync_queue WHERE id = :id")
    suspend fun ack(id: Long)

    @Query("UPDATE sync_queue SET attempts = attempts + 1 WHERE id = :id")
    suspend fun bump(id: Long)
}

class SyncWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val queue: SyncQueueDao = AppGraph.queueDao
        val api: Api = AppGraph.api
        queue.take(50).forEach { op ->
            try {
                api.dispatch(op.entityType, op.opType, op.payload, op.idempotencyKey)
                queue.ack(op.id)
            } catch (e: IOException) {
                queue.bump(op.id)
                return Result.retry()   // exponential backoff (WorkManager 자동)
            }
        }
        return Result.success()
    }
}

// 등록 — Constraints 로 네트워크 복귀 시 자동 트리거
val request = OneTimeWorkRequestBuilder<SyncWorker>()
    .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
    .build()
WorkManager.getInstance(ctx).enqueueUniqueWork("sync", ExistingWorkPolicy.APPEND, request)
```

**관련 패턴**: [Idempotency Key (distributed.md §6)](distributed.md), [Optimistic UI with Rollback](#optimistic-ui-rollback), [Network State Detection](#network-state-detection)

---

## 3. Conflict Resolution (충돌 해결 전략)

<a id="conflict-resolution"></a>

**목적**: 같은 record 가 여러 디바이스에서 오프라인으로 동시 수정되어 서버에 올라올 때, 어떤 값을 채택할지 결정하는 정책. 정답이 없으며 **도메인이 정책을 결정** 합니다.

**핵심 메커니즘 (4 가지 전략)**:

| 전략 | 설명 | 적용 도메인 |
|---|---|---|
| **Last-Write-Wins (LWW)** | timestamp 큰 쪽이 이김 | 프로필 nickname, 단순 설정 |
| **Three-way Merge** | base + local + remote 셋을 비교, field 별 머지 | Git, 노트 메타데이터 |
| **Operational Transform (OT)** | 작업(operation) 자체를 변환 (insert/delete) 하여 적용 순서 무관 | Google Docs (legacy) |
| **CRDT** | 자료구조 자체가 commutative — 어떤 순서로 머지해도 동일 결과 | Notion, Linear, Figma |

- **LWW 위험**: timestamp 가 거짓일 수 있음 (clock skew). HLC (Hybrid Logical Clock) 사용 권장 — `../algorithms/distributed.md §3`
- **Three-way merge**: 공통 ancestor (base) 가 있어야 작동 → 클라이언트가 last-synced version 보관 필수
- **OT vs CRDT**: OT 는 중앙 서버가 transform 책임, CRDT 는 P2P 가능. OT 는 trickier 하지만 메타데이터 적음
- **Vector Clock**: 두 변경이 concurrent 인지 causal 인지 판정. concurrent 면 사용자에게 노출 (§6 Conflict UI)

**장점**:
- LWW: 단순, 메타데이터 작음
- Three-way: 직관적, Git mental model
- CRDT: 자동 머지, P2P, offline-first 의 정답
- OT: 텍스트 협업에 검증됨

**단점·주의**:
- **LWW**: silent data loss — 더 늦게 쓴 변경이 덮어씀 (사용자가 모름)
- **Three-way**: 필드별 머지 로직을 도메인마다 작성해야 함
- **OT**: 구현 난이도 매우 높음, 모든 op 에 대해 transform 함수 작성
- **CRDT**: 메타데이터 오버헤드 (text 1KB → CRDT 5-10KB), tombstone GC 정책 필요
- **혼용 금지**: 한 entity 에 두 전략 섞이면 일관성 깨짐

**활용 예시**:
- LWW: Cassandra, DynamoDB, Redis CRDT, Firebase
- Three-way: Git, Dropbox (file-level)
- OT: Google Docs (2017 이전), ShareDB
- CRDT: Yjs, Automerge, Notion, Linear, Riak, Redis CRDT

**난이도**: 매우 높음 | **사용 빈도**: ★★★★☆

**Kotlin (LWW + HLC) 예제**:
```kotlin
data class VersionedRecord<T>(val value: T, val hlc: HybridLogicalClock)

fun <T> resolveLww(local: VersionedRecord<T>, remote: VersionedRecord<T>): VersionedRecord<T> =
    if (remote.hlc > local.hlc) remote else local
```

**TypeScript (Three-way Merge) 예제**:
```typescript
type Note = { title: string; body: string; tags: string[] };

function threeWayMerge(base: Note, local: Note, remote: Note): Note {
  const result: Note = { ...base };
  // field-by-field — local 또는 remote 만 바뀌었으면 그쪽 채택, 둘 다 바뀌었으면 conflict
  for (const key of Object.keys(base) as (keyof Note)[]) {
    const localChanged = !deepEq(local[key], base[key]);
    const remoteChanged = !deepEq(remote[key], base[key]);
    if (localChanged && remoteChanged && !deepEq(local[key], remote[key])) {
      throw new ConflictError(key, { base: base[key], local: local[key], remote: remote[key] });
    }
    (result as any)[key] = localChanged ? local[key] : remote[key];
  }
  return result;
}
```

**TypeScript (CRDT - Yjs) 예제**:
```typescript
import * as Y from 'yjs';

const doc = new Y.Doc();
const text = doc.getText('content');
text.insert(0, 'Hello, world');

// 다른 디바이스의 update 가 도착하면 자동 머지 — 충돌 없음
const update = /* 네트워크로 받음 */ new Uint8Array();
Y.applyUpdate(doc, update);
```

**관련 패턴**: [Conflict UI Pattern](#conflict-ui-pattern), [`../algorithms/distributed.md` §2 Vector Clock](../algorithms/distributed.md), [`../algorithms/distributed.md` §7~§10 CRDT](../algorithms/distributed.md), [state-management.md §8 CRDT-collab state](state-management.md)

---

## 4. Tombstone Pattern (묘비 패턴)

<a id="tombstone"></a>

**목적**: 분산 환경에서 **삭제** 를 안전하게 전파하기 위해, record 를 즉시 제거하지 않고 `deleted = true` 마커(tombstone) 로 표시하여 동기화 후 GC 합니다. 단순 hard delete 는 "삭제됨 vs 아직 안 받음" 을 구분할 수 없어, 다른 디바이스가 부활(resurrect) 시키는 사고가 발생합니다.

**핵심 메커니즘**:
- **Soft delete column**: `deleted_at` timestamp 또는 `is_deleted` boolean 컬럼 추가. row 자체는 유지
- **모든 쿼리에 `WHERE deleted_at IS NULL`** — 또는 view 로 감춤
- **Sync 시 tombstone 도 전송** — 다른 디바이스가 삭제를 인지
- **GC after TTL**: 모든 디바이스가 tombstone 을 확인 후 (e.g. 30 일) 실제 삭제. 너무 빨리 GC 하면 "삭제 전파 누락" 발생
- **CRDT OR-Set**: tombstone 의 정식 일반화 — add tag 와 remove tag 가 공존. `../algorithms/distributed.md §9` 참조
- **Versioning**: tombstone 도 HLC / Vector Clock 부여 → resurrect 시 누가 이기는지 결정

**장점**:
- 분실된 동기화 메시지 (e.g. offline 디바이스) 가 복귀해도 삭제가 보존됨
- Undo 기능 자연 지원 — `UPDATE SET deleted_at = NULL`
- Audit log 부분 대체

**단점·주의**:
- 저장공간 증가 — GC 안 하면 무한 누적
- 모든 쿼리에 filter 추가 — 누락 시 삭제된 데이터가 노출됨
- GC 타이밍 결정 어려움 (TTL 너무 짧으면 oldest device 가 못 따라옴)
- Unique constraint 와 충돌 — 삭제된 row 가 unique key 점유 (`deleted_at IS NULL` 인덱스로 우회)

**활용 예시**: CouchDB `_deleted: true`, DynamoDB TTL, Cassandra tombstone (실제 internal mechanism), Firebase Firestore field deletion sentinel

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**SQL (Postgres / SQLite) 예제**:
```sql
-- Soft delete column + partial unique index
CREATE TABLE notes (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  body TEXT,
  deleted_at INTEGER,            -- NULL = alive, timestamp = tombstone
  updated_at INTEGER NOT NULL
);

CREATE UNIQUE INDEX notes_title_alive
  ON notes(title) WHERE deleted_at IS NULL;   -- 살아있는 row 만 unique

-- 삭제 = soft delete
UPDATE notes SET deleted_at = unixepoch(), updated_at = unixepoch() WHERE id = ?;

-- 모든 read 는 WHERE deleted_at IS NULL
SELECT * FROM notes WHERE deleted_at IS NULL ORDER BY updated_at DESC;

-- GC after 30 days (모든 디바이스가 tombstone 확인 가정)
DELETE FROM notes WHERE deleted_at < unixepoch() - 30*86400;
```

**Kotlin (Room) 예제**:
```kotlin
@Dao
interface NoteDao {
    @Query("SELECT * FROM notes WHERE deleted_at IS NULL ORDER BY updatedAt DESC")
    fun observeAlive(): Flow<List<NoteEntity>>

    @Query("UPDATE notes SET deleted_at = :now, updatedAt = :now, syncState = 'pending' WHERE id = :id")
    suspend fun softDelete(id: String, now: Long = System.currentTimeMillis())

    @Query("DELETE FROM notes WHERE deleted_at IS NOT NULL AND deleted_at < :threshold")
    suspend fun gc(threshold: Long)
}
```

**관련 패턴**: [Conflict Resolution](#conflict-resolution), [Delta Sync](#delta-sync), [`../algorithms/distributed.md` §9 OR-Set](../algorithms/distributed.md)

---

## 5. Delta Sync (증분 동기화)

<a id="delta-sync"></a>

**목적**: 매번 전체 데이터를 fetch 하지 않고, 마지막 동기화 시점 이후의 변경분만 주고받아 네트워크·CPU·배터리를 절감합니다. 첫 sync 는 full snapshot, 이후는 모두 incremental.

**핵심 메커니즘**:
- **`last_synced_at` 또는 `cursor`**: 클라이언트가 마지막 sync 시점을 저장. 다음 요청 시 `?since=<cursor>` 로 서버에 전달
- **서버 측 `updated_at` 인덱스**: `WHERE updated_at > :since ORDER BY updated_at LIMIT n` — index range scan
- **HLC / Vector Clock cursor**: timestamp 단독은 clock skew 위험. HLC 또는 monotonic sequence (LSN) 권장
- **HTTP 표준 활용**: `ETag` + `If-None-Match` (304 Not Modified), `Last-Modified` + `If-Modified-Since`
- **Pagination + cursor**: 한 번에 모두 받지 않고 `next_cursor` 로 페이지네이션
- **Tombstone 포함**: §4 와 결합 — `deleted_at > :since` 도 전송
- **Snapshot fallback**: cursor 가 너무 오래되어 서버가 추적 못하면 full snapshot 으로 fallback

**장점**:
- 네트워크 90%+ 절감 (typical)
- 배터리 절감
- 서버 부하 감소
- 큰 데이터셋도 점진적 sync 가능

**단점·주의**:
- 서버 측 변경 추적 인프라 필요 (`updated_at` 인덱스, CDC stream, change feed)
- Clock skew 시 데이터 누락 위험 — HLC 또는 sequence 권장
- 삭제 추적 필요 — tombstone 패턴 결합 필수
- 스키마 마이그레이션 시 cursor 무효화 (full re-sync)

**활용 예시**: CouchDB replication protocol, Firebase Firestore `onSnapshot` (since cursor 내부 관리), Apollo Client polling with `lastSyncedAt`, iCloud CKFetchChangesOperation

**난이도**: 중간 | **사용 빈도**: ★★★★★

**TypeScript (REST + cursor) 예제**:
```typescript
type SyncResponse<T> = { items: T[]; nextCursor: string; hasMore: boolean };

async function pullDelta() {
  const cursor = await db.kv.get('sync:cursor:notes') ?? '0';
  let hasMore = true;
  let nextCursor = cursor;

  while (hasMore) {
    const res = await fetch(`/api/notes/sync?since=${nextCursor}&limit=200`);
    const data: SyncResponse<NoteDto> = await res.json();

    await db.transaction('rw', db.notes, async () => {
      for (const item of data.items) {
        if (item.deletedAt) await db.notes.delete(item.id);
        else await db.notes.put(item);
      }
    });

    nextCursor = data.nextCursor;
    hasMore = data.hasMore;
  }
  await db.kv.put('sync:cursor:notes', nextCursor);
}
```

**HTTP (ETag / If-None-Match) 예제**:
```http
GET /api/notes/123 HTTP/1.1
If-None-Match: "v42"

HTTP/1.1 304 Not Modified          ← 변경 없음, 본문 0 bytes
```

**Kotlin (Server-side) 예제**:
```kotlin
@GetMapping("/api/notes/sync")
fun syncNotes(
    @RequestParam since: String,        // HLC string
    @RequestParam(defaultValue = "200") limit: Int,
): SyncResponse<NoteDto> {
    val cursor = HybridLogicalClock.parse(since)
    val rows = noteRepo.findChangedSince(cursor, limit + 1)        // n+1 trick
    val hasMore = rows.size > limit
    val items = rows.take(limit)
    val nextCursor = items.lastOrNull()?.hlc?.toString() ?: since
    return SyncResponse(items.map { it.toDto() }, nextCursor, hasMore)
}
```

**관련 패턴**: [Tombstone](#tombstone), [`../algorithms/distributed.md` §3 HLC](../algorithms/distributed.md), [`../algorithms/distributed.md` §6 Anti-Entropy / Merkle Tree](../algorithms/distributed.md)

---

## 6. Conflict UI Pattern (충돌 사용자 노출 패턴)

<a id="conflict-ui-pattern"></a>

**목적**: 자동 머지(LWW / CRDT) 가 도메인적으로 안전하지 않은 경우, 충돌 자체를 사용자에게 노출하여 사용자가 결정하게 만듭니다. 결제 금액, 의료 기록, 법적 문서처럼 silent merge 가 위험한 영역에서 필수.

**핵심 메커니즘**:
- **3-way 표시**: "Yours" (local) / "Theirs" (remote) / "Merged" (제안된 자동 머지) 세 컬럼 노출
- **Inline diff**: 글자/필드 단위 diff highlight (red / green) — Git diff 와 동일 mental model
- **선택지 제공**: `Keep Yours`, `Keep Theirs`, `Merge Both` (필드별), `Edit Manually`
- **Conflict 상태 entity**: 충돌 중인 record 는 `syncState = "conflict"` 로 마킹, 일반 리스트에서 분리 표시
- **Notification / Badge**: 충돌 발생 시 사용자에게 즉시 알림 — 묻히면 의미 없음
- **Audit trail**: 충돌 해결 이력 저장 — 누가 어느 버전을 선택했는지

**장점**:
- 도메인 안전성 — silent data loss 없음
- 사용자 신뢰 — "내가 안 한 변경" 이 자동 적용되지 않음
- 협업 투명성 — 누가 무엇을 바꿨는지 노출

**단점·주의**:
- UX 복잡도 — 일반 사용자가 diff 를 읽기 어려움
- 충돌이 잦으면 사용자 피로 — CRDT 로 자동 머지 우선이 원칙
- 모바일 작은 화면에서 3-way diff 가 어려움 — 텍스트 짧을 때만 시도
- "나중에 결정" 옵션이 필요 — 강제하면 사용자가 앱을 떠남

**활용 예시**: Dropbox (`Conflicted copy` 파일 생성), Git merge conflict markers, Apple Notes (충돌 시 두 노트로 분리), Bear (sync conflict 알림)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**TypeScript (React + diff) 예제**:
```tsx
type ConflictView<T> = { base: T; yours: T; theirs: T; suggested: T };

function ConflictDialog<T extends Record<string, any>>({
  conflict, onResolve,
}: { conflict: ConflictView<T>; onResolve: (chosen: T) => void }) {
  return (
    <Dialog>
      <h3>이 항목이 다른 기기에서도 변경되었습니다</h3>
      <Tabs>
        <Tab label="내 변경">{renderFields(conflict.yours, conflict.base)}</Tab>
        <Tab label="다른 기기 변경">{renderFields(conflict.theirs, conflict.base)}</Tab>
        <Tab label="자동 병합 (권장)">{renderFields(conflict.suggested, conflict.base)}</Tab>
      </Tabs>
      <Actions>
        <Button onClick={() => onResolve(conflict.yours)}>내 변경 사용</Button>
        <Button onClick={() => onResolve(conflict.theirs)}>다른 기기 변경 사용</Button>
        <Button primary onClick={() => onResolve(conflict.suggested)}>자동 병합 적용</Button>
      </Actions>
    </Dialog>
  );
}

function renderFields<T extends Record<string, any>>(version: T, base: T) {
  return Object.entries(version).map(([k, v]) => {
    const changed = !deepEq(v, base[k]);
    return <Field key={k} label={k} value={String(v)} highlighted={changed} />;
  });
}
```

**Kotlin (Conflict marking) 예제**:
```kotlin
suspend fun handleSyncResponse(remote: NoteEntity) {
    val local = dao.byId(remote.id) ?: run { dao.upsert(remote); return }
    val base = dao.lastSyncedSnapshot(remote.id)
    val localChanged = local != base
    val remoteChanged = remote != base
    if (localChanged && remoteChanged && local != remote) {
        // 충돌 — UI 에 노출
        dao.upsert(local.copy(syncState = "conflict"))
        conflictBus.emit(Conflict(local, remote, base))
    } else {
        dao.upsert(if (remoteChanged) remote else local)
    }
}
```

**관련 패턴**: [Conflict Resolution](#conflict-resolution), [Tombstone](#tombstone), [Optimistic UI with Rollback](#optimistic-ui-rollback)

---

## 7. Optimistic UI with Rollback (낙관적 UI + 롤백)

<a id="optimistic-ui-rollback"></a>

**목적**: 서버 응답을 기다리지 않고 UI 에 즉시 변경을 반영하되, 서버가 실패를 반환하면 정확히 이전 상태로 되돌립니다. 인터넷 단절 / 약한 셀룰러 환경에서도 앱이 빠르게 반응한다는 인상을 제공합니다.

**핵심 메커니즘**:
- **즉시 UI 반영**: mutation 호출 시 local store / cache 에 변경 즉시 적용 → render
- **Mutation history / Rollback log**: `{ id, prevState, nextState }` 를 별도 저장 — 실패 시 prev 복원
- **Idempotency Key 동반**: 재시도 시 중복 처리 방지 (distributed.md §6)
- **Rollback 시 UX**: silent revert 금지 — toast / banner 로 "변경 실패, 되돌렸음" 명시
- **Optimistic ID**: 서버 생성 ID 대기 불가 → 클라이언트 UUID 로 생성, 서버 응답에서 실제 ID 와 매핑 (또는 client UUID 를 그대로 PK 로 사용)
- **Re-fetch on conflict**: 서버가 "version mismatch" (HTTP 409) 반환 시 latest 를 fetch 한 후 다시 시도
- **TanStack Query / Apollo**: `onMutate` + `onError` + `onSettled` 라이프사이클로 표준화

**장점**:
- 체감 응답 0ms
- 네트워크 약해도 UX 유지
- offline-first 의 자연스러운 결합

**단점·주의**:
- Rollback 로직 누락 시 stale data 누적 → 사용자 혼란
- 실패 시 사용자가 변경한 *이후* 입력까지 잃을 수 있음 — careful UX 필요
- 연쇄 의존성 (mutation A → mutation B) 시 A 실패 → B 도 rollback 해야 함
- 서버 응답까지 "되돌릴 수 없음" 표시 (e.g. 결제 완료 메시지) 절대 금지

**활용 예시**: TanStack Query `onMutate` + context, Apollo Client `optimisticResponse`, SWR `mutate(data, false)`, Redux Toolkit Query `updateQueryData`, Facebook Relay

**난이도**: 중간 | **사용 빈도**: ★★★★★

**TypeScript (TanStack Query) 예제**:
```typescript
const queryClient = useQueryClient();

const mutation = useMutation({
  mutationFn: (note: Note) => api.updateNote(note),

  onMutate: async (newNote) => {
    // 1) 진행 중인 refetch 취소 → 우리 optimistic update 덮어쓰이지 않음
    await queryClient.cancelQueries({ queryKey: ['notes', newNote.id] });

    // 2) rollback 용 snapshot
    const previous = queryClient.getQueryData<Note>(['notes', newNote.id]);

    // 3) optimistic update — UI 즉시 반영
    queryClient.setQueryData(['notes', newNote.id], newNote);

    return { previous };       // context 로 onError 에 전달
  },

  onError: (err, newNote, context) => {
    // rollback
    if (context?.previous) {
      queryClient.setQueryData(['notes', newNote.id], context.previous);
    }
    toast.error('저장 실패, 변경을 되돌렸습니다');
  },

  onSettled: (data, error, variables) => {
    queryClient.invalidateQueries({ queryKey: ['notes', variables.id] });
  },
});
```

**Kotlin (수동 구현) 예제**:
```kotlin
class NoteViewModel(private val repo: NoteRepository) : ViewModel() {
    fun update(note: Note) = viewModelScope.launch {
        val prev = repo.byId(note.id)             // snapshot for rollback
        repo.saveLocal(note)                       // optimistic
        try {
            repo.pushToServer(note)
        } catch (e: ServerError) {
            prev?.let { repo.saveLocal(it) }       // rollback
            _events.emit(Event.RollbackToast("저장 실패"))
        }
    }
}
```

**관련 패턴**: [Sync Queue / Outbox](#sync-queue-outbox-client), [`../patterns/state-management.md` §9 Optimistic Update](state-management.md), [Conflict Resolution](#conflict-resolution)

---

## 8. Network State Detection (네트워크 상태 감지)

<a id="network-state-detection"></a>

**목적**: 단말이 실제로 인터넷에 접근 가능한지 정확히 판정하여, sync queue flush / UI banner 표시 / fetch retry 를 적절한 순간에 트리거합니다. "WiFi 연결됨 ≠ 인터넷 가능" — captive portal, 라우터 단절, DNS 실패 등이 흔합니다.

**핵심 메커니즘**:
- **OS Connectivity API**: Android `ConnectivityManager.NetworkCallback`, iOS `NWPathMonitor`, Web `navigator.onLine` + `online` / `offline` 이벤트, Flutter `connectivity_plus`, RN `@react-native-community/netinfo`
- **Reachability ping**: OS 가 "connected" 라 해도 실제 도달 가능성 별도 확인 — `HEAD https://my-api/health` (gzip 본문 없는 경량 endpoint)
- **Captive portal 감지**: 호텔·공항 WiFi 의 강제 로그인 페이지 — OS 가 자동 감지 (Android `NET_CAPABILITY_VALIDATED`, iOS Network framework)
- **Quality 분류**: `cellular / wifi / ethernet`, `metered (정량제) / unmetered`, `2G / 3G / 4G / 5G` — 큰 파일 다운로드 정책에 사용
- **Debounce**: 짧은 단절 (수 초) 에 즉시 반응 X — 3~5 초 debounce 후 상태 변경
- **Background callback**: 앱이 백그라운드여도 OS 가 콜백 — Doze mode 시 제한
- **VPN 감지**: VPN on/off 도 connectivity 변경 — 일부 정책에서 무시 필요

**장점**:
- sync 큐 flush 시점 정확
- 사용자에게 "오프라인" 배너 정확 표시
- 비싼 fetch 를 metered network 에서 자동 보류
- 배터리 절감 (불필요한 fetch 회피)

**단점·주의**:
- `navigator.onLine` (웹) 은 false positive 많음 — 라우터 연결만 확인, 인터넷 도달 여부 X
- HEAD ping 도 captive portal HTML 을 200 으로 반환할 수 있음 — body 검증 필요
- 너무 잦은 ping 은 배터리 낭비 — passive 감지 우선, 능동 ping 은 transition 시점에만
- VPN, Proxy 환경에서 잘못된 quality 정보 제공 가능

**활용 예시**: Android `NetworkCallback` + WorkManager constraint, iOS `NWPathMonitor` + URLSessionConfiguration, Slack desktop offline banner, Notion sync indicator

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin (Android NetworkCallback) 예제**:
```kotlin
class NetworkObserver(ctx: Context) {
    private val cm = ctx.getSystemService(ConnectivityManager::class.java)
    private val _state = MutableStateFlow<NetState>(NetState.Unknown)
    val state: StateFlow<NetState> = _state.asStateFlow()

    private val callback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) {
            // 단순 onAvailable 만으론 captive portal 미감지 — VALIDATED 확인
        }
        override fun onCapabilitiesChanged(network: Network, caps: NetworkCapabilities) {
            val validated = caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
            val metered = !caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED)
            _state.value = if (validated) NetState.Online(metered) else NetState.CaptivePortal
        }
        override fun onLost(network: Network) { _state.value = NetState.Offline }
    }

    fun start() {
        val req = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()
        cm.registerNetworkCallback(req, callback)
    }
    fun stop() = cm.unregisterNetworkCallback(callback)
}

sealed class NetState {
    data object Unknown : NetState()
    data object Offline : NetState()
    data object CaptivePortal : NetState()
    data class Online(val metered: Boolean) : NetState()
}

// sync trigger
viewModelScope.launch {
    netObserver.state.collect { s ->
        if (s is NetState.Online) syncQueue.flushAsync()
        showOfflineBanner.value = s !is NetState.Online
    }
}
```

**Swift (iOS NWPathMonitor) 예제**:
```swift
import Network

final class NetworkMonitor: ObservableObject {
    @Published var isOnline = false
    @Published var isMetered = false
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "net.monitor")

    func start() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isOnline = path.status == .satisfied
                self?.isMetered = path.isExpensive || path.isConstrained
            }
        }
        monitor.start(queue: queue)
    }
}
```

**관련 패턴**: [Sync Queue / Outbox](#sync-queue-outbox-client), [mobile-app.md Background Task](mobile-app.md), [Optimistic UI with Rollback](#optimistic-ui-rollback)
