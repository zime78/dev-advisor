# DB 인덱스 유형 (Database Index Types)

알고리즘 도메인의 신규 카테고리. 기존 [`data-structures.md`](../../../dev-advisor/references/algorithms/data-structures.md) 의 B-Tree / Skip List / Hash 만으로는 실무 DB 인덱스 선택 의사결정에 부족. 정평 있는 DB 인덱스 8 유형.

**관련 카탈로그**:
- [data-structures.md](../../../dev-advisor/references/algorithms/data-structures.md) — B-Tree, Hash, Skip List (자료구조 본체)
- [`../patterns/data-access.md`](../../../dev-advisor/references/patterns/data-access.md) — Repository, Lazy Load, Query Object (접근 패턴)
- [string.md](../../../dev-advisor/references/algorithms/string.md) — Trie, Suffix Array (full-text 인덱스 본체)

## 알고리즘 목차

| ID | 알고리즘 | 시간 복잡도 | 공간 | 적용 |
|----|---------|-----------|------|------|
| [b-plus-tree](#b-plus-tree) | B+Tree | O(log n) | O(n) | 범용 |
| [hash-index](#hash-index) | Hash | O(1) avg | O(n) | equality |
| [bitmap-index](#bitmap-index) | Bitmap | O(n/8) | O(n·cardinality) | low-cardinality |
| [gin](#gin) | GIN | O(k log n) | O(n·avg_k) | 다값/JSONB |
| [gist](#gist) | GiST | O(log n) | O(n) | range/공간 |
| [brin](#brin) | BRIN | O(n) scan | O(n/page_size) | 자연 정렬 |
| [covering-index](#covering-index) | Covering | O(log n) | O(n+\|cols\|) | index-only |
| [partial-index](#partial-index) | Partial | O(log m) | O(m) where m<<n | sparse |

---

<a id="b-plus-tree"></a>
## 1. B+Tree Index (B+트리 인덱스)

**목적**: 정렬된 키 공간에서 point lookup, range scan, prefix lookup 을 모두 O(log n) 으로 지원하는 DB 표준 인덱스

**시간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Point lookup | O(log n) |
| Range scan | O(log n + k) (k = 결과 개수) |
| Insert / Delete | O(log n) |

**공간 복잡도**: O(n)

**특징**:
- 내부 노드는 라우팅 키만 보관, **잎(leaf) 노드에만 실제 데이터/RowID** 저장
- 잎 노드는 **doubly linked list** 로 연결 → range scan 시 트리를 다시 타지 않고 순차 이동
- fanout 이 높아 (수백 ~ 수천) 트리 깊이가 얕음 (수십억 row 도 3~4 단계)
- 페이지 단위 I/O 에 최적화 (B+Tree 한 노드 = 디스크 한 페이지)

**장점**:
- equality, range, prefix, ORDER BY, GROUP BY 모두 활용
- 디스크 친화적 (B-Tree 보다 잎이 분리되어 범위 스캔 효율)
- 모든 주요 RDBMS 의 기본 인덱스

**단점**:
- 다값 컬럼(array, JSONB) 에 직접 적용 불가
- 매우 큰 테이블 + 무작위 insert 시 페이지 분할 비용
- 인덱스 크기가 데이터의 10~30%

**사용처**:
- PK, FK, UNIQUE 제약
- `WHERE id = ?`, `WHERE created_at BETWEEN ? AND ?`
- `ORDER BY column`
- composite index (`(tenant_id, created_at)`)

**DB 별 지원**:

| DB | 키워드 | 기본 여부 |
|---|---|---|
| PostgreSQL | `USING btree` | 기본 (생략 시) |
| MySQL InnoDB | `BTREE` | 기본 (clustered = PK, secondary = B+Tree) |
| SQL Server | `CREATE INDEX` | 기본 |
| Oracle | `CREATE INDEX` | 기본 |

**SQL 예제**:
```sql
-- 단일 컬럼
CREATE INDEX idx_users_email ON users(email);

-- composite — 좌측 prefix 룰 적용
CREATE INDEX idx_orders_tenant_created
  ON orders(tenant_id, created_at DESC);

-- range query 활용
SELECT * FROM orders
 WHERE tenant_id = 42
   AND created_at >= NOW() - INTERVAL '7 days'
 ORDER BY created_at DESC;  -- 인덱스 정렬 그대로 사용
```

**관련 알고리즘**: [B-Tree](../../../dev-advisor/references/algorithms/data-structures.md#b-tree), [Covering Index](#covering-index), [Partial Index](#partial-index)

---

<a id="hash-index"></a>
## 2. Hash Index (해시 인덱스)

**목적**: equality lookup 만 평균 O(1) 으로 처리하는 최소 비용 인덱스. range 불가

**시간 복잡도**:
| 작업 | 평균 | 최악 |
|------|------|------|
| Point lookup | O(1) | O(n) (충돌) |
| Range scan | 불가 | — |
| Insert / Delete | O(1) | O(n) |

**공간 복잡도**: O(n)

**특징**:
- 키를 해시 함수로 변환 → 버킷 직접 접근
- **정렬 정보 없음** → `>`, `<`, `BETWEEN`, `ORDER BY` 활용 불가
- **부분 일치 불가** (`LIKE 'abc%'`)
- in-memory DB(Redis) 의 기본 자료구조, PostgreSQL 은 `USING hash` 명시 필요

**장점**:
- equality 에서 B+Tree 대비 상수배 빠름
- 인덱스 크기가 B+Tree 보다 작음
- 메모리 캐시 친화

**단점**:
- range / prefix / ORDER BY 완전 불가
- 해시 충돌 시 성능 저하
- composite index 지원 빈약 (대부분 단일 컬럼)
- PostgreSQL 에서는 9.x 까지 WAL 로깅 안 됨(복구 위험)이었고 10+ 부터 안전해졌으나 활용도 낮음

**사용처**:
- Redis, Memcached 같은 in-memory KV
- equality 만 사용하는 lookup 테이블
- PostgreSQL `USING hash` 는 UUID/세션 토큰 같은 high-cardinality equality 전용

**DB 별 지원**:

| DB | 키워드 | 비고 |
|---|---|---|
| PostgreSQL | `USING hash` | 10+ WAL safe |
| MySQL InnoDB | (자동) Adaptive Hash Index | 사용자 생성 불가, 엔진이 내부 관리 |
| MySQL MEMORY | `USING HASH` | MEMORY 엔진 기본 |
| SQL Server | Hash Index | In-Memory OLTP 테이블 전용 |
| Oracle | — | 명시적 hash index 없음 (Hash Cluster 별도) |

**SQL 예제**:
```sql
-- PostgreSQL: equality 전용 lookup
CREATE INDEX idx_sessions_token_hash
  ON sessions USING hash (token);

-- 이 쿼리는 hash index 사용
SELECT user_id FROM sessions WHERE token = 'abc123';

-- 이 쿼리는 hash index 사용 불가 (range)
SELECT * FROM sessions WHERE token > 'a'; -- Seq Scan 으로 fallback

-- MySQL MEMORY 엔진
CREATE TABLE cache (
  key VARCHAR(64) PRIMARY KEY,
  value TEXT,
  INDEX idx_key USING HASH (key)
) ENGINE=MEMORY;
```

**관련 알고리즘**: [Hash Table Search](../../../dev-advisor/references/algorithms/searching.md#hash-table-search), [B+Tree](#b-plus-tree)

---

<a id="bitmap-index"></a>
## 3. Bitmap Index (비트맵 인덱스)

**목적**: low-cardinality 컬럼(성별, 상태, 카테고리 등 distinct 값 수십개 이하)에 비트벡터 인덱스를 생성, 다중 조건을 비트 AND/OR/NOT 로 결합

**시간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Point lookup | O(n / 8) bit scan |
| Multi-condition AND/OR | O(n / 64) (워드 단위 비트 연산) |
| Insert / Update | 비싸다 — 전체 비트맵 재기록 |

**공간 복잡도**: O(n × cardinality) — 압축(WAH, EWAH, Roaring) 적용 시 훨씬 작음

**특징**:
- distinct value 마다 길이 n 의 비트벡터 1개 생성
- 예: `gender` 컬럼 → bitmap(M), bitmap(F), bitmap(NULL) 3개
- `WHERE gender='F' AND status='active'` 는 두 bitmap 의 비트 AND
- **DML 부하가 매우 큼** → OLTP 부적합, OLAP/DWH 전용

**장점**:
- 다중 조건 결합 쿼리가 매우 빠름
- low-cardinality 컬럼에서 B+Tree 보다 작음
- Roaring Bitmap 압축으로 sparse bitmap 도 효율적

**단점**:
- high-cardinality 컬럼에서는 인덱스 크기 폭발 (수백만 distinct → 수백만 bitmap)
- DML 시 lock 범위가 row 단위가 아닌 bitmap 단위 → 동시 쓰기 충돌
- PostgreSQL/MySQL 에는 정식 bitmap index 없음 (Oracle, DWH 전용)

**사용처**:
- Oracle DWH 의 fact table 차원 컬럼 (region, channel, status)
- Greenplum, Vertica, Druid 등 분석 DB
- 분석성 쿼리 `WHERE country='KR' AND device='mobile' AND status='active'`
- 읽기 전용 또는 batch update 테이블

**DB 별 지원**:

| DB | 키워드 | 비고 |
|---|---|---|
| Oracle | `CREATE BITMAP INDEX` | DWH 표준 |
| PostgreSQL | — | Bitmap Index Scan 은 있지만 영구 bitmap index 자료구조는 없음 (B+Tree 결과를 bitmap 으로 결합) |
| MySQL | — | 미지원 |
| SQL Server | — | columnstore 로 대체 |
| Greenplum / DuckDB / Druid | 지원 | 분석 DB |

**SQL 예제**:
```sql
-- Oracle: 차원 컬럼에 bitmap
CREATE BITMAP INDEX idx_sales_region
  ON sales(region);
CREATE BITMAP INDEX idx_sales_channel
  ON sales(channel);
CREATE BITMAP INDEX idx_sales_status
  ON sales(status);

-- 다중 조건 — bitmap AND 로 결합
SELECT COUNT(*) FROM sales
 WHERE region  = 'APAC'
   AND channel = 'mobile'
   AND status  = 'paid';

-- PostgreSQL: 영구 bitmap 은 없지만 plan 에 Bitmap Heap Scan 사용
EXPLAIN
SELECT * FROM logs
 WHERE level = 'ERROR' AND service = 'auth';
-- → BitmapAnd ( BitmapIndexScan idx_level, BitmapIndexScan idx_service )
```

**관련 알고리즘**: [B+Tree](#b-plus-tree), [Roaring Bitmap (probabilistic.md)](../../../dev-advisor/references/algorithms/probabilistic.md), columnstore

---

<a id="gin"></a>
## 4. GIN (Generalized Inverted Index)

**목적**: array, JSONB, tsvector(full-text), trigram 같은 **하나의 행에 여러 키가 있는 다값 컬럼**을 inverted index 구조로 인덱싱

**시간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Point lookup (key 포함 여부) | O(log n) |
| Multi-key containment | O(k log n) (k = 검색 키 수) |
| Insert / Update | O(k log n) — 다값이라 비쌈 (fastupdate 로 완화) |

**공간 복잡도**: O(n × avg_k) (avg_k = 행당 평균 키 수)

**특징**:
- inverted index — "키 → 그 키를 포함한 row 리스트"
- 한 row 가 여러 posting list 에 등장
- `@>`, `<@`, `?`, `?&`, `?|`, `@@` 같은 containment 연산자 지원
- B+Tree 와 달리 다값 컬럼이 메인 타겟

**장점**:
- JSONB 의 `data @> '{"status": "active"}'` 같은 containment 가 매우 빠름
- array 의 `tags && ARRAY['kotlin','flutter']` 도 인덱스 활용
- full-text search 의 사실상 표준 (`to_tsvector` + `@@`)

**단점**:
- DML(특히 update) 비용이 B+Tree 대비 큼
- 인덱스 빌드 시간 김
- equality / range / ORDER BY 활용 불가

**사용처**:
- PostgreSQL JSONB 컬럼 `data @> '{"k":"v"}'`
- 태그 검색 `tags @> ARRAY['kotlin']`
- full-text search `tsvector @@ tsquery`
- trigram 유사도 검색 (`pg_trgm` extension)

**DB 별 지원**:

| DB | 키워드 | 비고 |
|---|---|---|
| PostgreSQL | `USING gin` | 표준 (jsonb, array, tsvector, trgm) |
| MySQL | FULLTEXT | InnoDB FULLTEXT 가 inverted index 와 유사 |
| SQL Server | Full-Text Index | inverted index 기반 |
| Oracle | Oracle Text | CONTEXT/CTXSYS |

**SQL 예제**:
```sql
-- JSONB containment
CREATE INDEX idx_events_data_gin
  ON events USING gin (data jsonb_path_ops);

SELECT * FROM events
 WHERE data @> '{"type": "login", "result": "success"}';

-- array containment
CREATE INDEX idx_posts_tags_gin
  ON posts USING gin (tags);

SELECT * FROM posts
 WHERE tags @> ARRAY['postgres','index'];

-- full-text search
CREATE INDEX idx_docs_fts
  ON docs USING gin (to_tsvector('english', body));

SELECT * FROM docs
 WHERE to_tsvector('english', body) @@ to_tsquery('postgres & index');

-- trigram fuzzy match
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_names_trgm
  ON users USING gin (name gin_trgm_ops);

SELECT * FROM users WHERE name ILIKE '%john%';
```

**관련 알고리즘**: [Trie](../../../dev-advisor/references/algorithms/string.md#trie), [Inverted Index](../../../dev-advisor/references/algorithms/string.md), [Suffix Array](../../../dev-advisor/references/algorithms/string.md)

---

<a id="gist"></a>
## 5. GiST (Generalized Search Tree)

**목적**: 확장 가능한 트리 인덱스 프레임워크. R-Tree(공간), range type, full-text, exclusion constraint, 유사도 검색을 하나의 추상화로 지원

**시간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| 공간/range overlap | O(log n) 평균, 최악은 자료 분포 의존 |
| Insert / Update | O(log n) |
| KNN ordering | O(log n + k) |

**공간 복잡도**: O(n)

**특징**:
- 사용자 정의 자료형에 맞는 consistent/union/penalty/picksplit 함수만 구현하면 인덱스화
- 내부적으로 **R-Tree** 변형이라 공간 데이터 표준
- KNN 정렬 (`ORDER BY point <-> '(0,0)'`) 지원 — 거리 기반 정렬을 인덱스로 처리
- exclusion constraint 의 인덱스 backbone

**장점**:
- 공간 데이터(PostGIS) 의 사실상 표준
- range type 의 overlap 검색에 최적
- KNN 검색 (가까운 점 k 개) 을 별도 자료구조 없이 처리
- 다양한 자료형 확장 가능

**단점**:
- equality / 일반 정렬에는 B+Tree 보다 느림
- 인덱스 크기가 B+Tree 보다 큼
- GIN 보다 다값 컬럼에서 느림 (대신 GIN 보다 update 가 저렴)

**사용처**:
- PostGIS `ST_Intersects`, `ST_DWithin`, `ST_Contains`
- `tsrange`, `int4range`, `daterange` overlap (`&&`)
- exclusion constraint (예약 시스템에서 시간 범위 충돌 방지)
- 이미지 임베딩 KNN (`pgvector` 의 ivfflat/hnsw 전 단계)

**DB 별 지원**:

| DB | 키워드 | 비고 |
|---|---|---|
| PostgreSQL | `USING gist` | PostGIS, range type |
| MySQL | `SPATIAL INDEX` | R-Tree 기반 (GiST 와 별개 구현) |
| SQL Server | Spatial Index | grid 기반, R-Tree 와 다름 |
| Oracle | Spatial / R-Tree | Oracle Spatial |

**SQL 예제**:
```sql
-- 공간 인덱스
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE INDEX idx_shops_geo
  ON shops USING gist (location);  -- location geometry(Point)

SELECT id, name
  FROM shops
 WHERE ST_DWithin(location, ST_MakePoint(127.0, 37.5)::geography, 1000);

-- range type overlap (예약 충돌 방지)
CREATE TABLE bookings (
  room_id INT,
  during  tsrange,
  EXCLUDE USING gist (room_id WITH =, during WITH &&)
);

-- KNN: 가장 가까운 5개
SELECT id, name
  FROM shops
 ORDER BY location <-> ST_MakePoint(127.0, 37.5)
 LIMIT 5;
```

**관련 알고리즘**: R-Tree, [KNN (ml.md)](../../../dev-advisor/references/algorithms/ml.md), [Range Tree](../../../dev-advisor/references/algorithms/data-structures.md)

---

<a id="brin"></a>
## 6. BRIN (Block Range Index)

**목적**: 매우 큰 테이블 중 **물리적 순서가 데이터 값과 강한 상관관계**가 있을 때(시계열, append-only 로그), 블록 범위마다 min/max 메타만 저장하는 초경량 인덱스

**시간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Range lookup | O(n/page_size) — page 단위 skip |
| Insert (append) | O(1) — 마지막 블록 메타만 갱신 |
| Random insert | 인덱스 효율 급락 (correlation 깨짐) |

**공간 복잡도**: O(n / page_size) — B+Tree 의 **약 1/1000 ~ 1/10000**

**특징**:
- 페이지(예: 128 페이지 = 1MB) 범위마다 `(min, max)` 만 저장
- 쿼리 시 범위에 겹치지 않는 페이지 군을 통째로 skip
- 데이터가 정렬되어 있을수록 효율 폭증, 무작위면 효율 0

**장점**:
- 인덱스 크기가 극단적으로 작음 (수TB 테이블도 수MB 인덱스)
- 인덱스 빌드 / 유지보수 비용 최저
- append-only 시계열에 최적

**단점**:
- 데이터 물리 순서가 흐트러지면 효율 사라짐 (CLUSTER 명령 또는 BRIN 재구성 필요)
- 정확도 낮음 — bitmap heap scan 으로 후속 필터 필요
- equality lookup 은 B+Tree 보다 훨씬 느림

**사용처**:
- 시계열 테이블 `events(created_at)`, IoT 센서 로그
- append-only 데이터 웨어하우스 fact 테이블
- 수십억 row + range 쿼리 위주
- 디스크 비용 vs 쿼리 속도의 trade-off

**DB 별 지원**:

| DB | 키워드 | 비고 |
|---|---|---|
| PostgreSQL | `USING brin` | 9.5+ |
| MySQL | — | 미지원 |
| Oracle | Zone Maps | Exadata 한정 (유사 개념) |
| SQL Server | — | columnstore 가 대체 |
| Greenplum | BRIN | PostgreSQL 호환 |

**SQL 예제**:
```sql
-- 거대 append-only 테이블의 시간 컬럼
CREATE INDEX idx_events_created_brin
  ON events USING brin (created_at)
  WITH (pages_per_range = 128);  -- 1 entry per 128 pages (1MB)

-- 시계열 범위 쿼리
SELECT COUNT(*)
  FROM events
 WHERE created_at BETWEEN '2025-01-01' AND '2025-01-31';

-- correlation 깨졌을 때 복구
CLUSTER events USING idx_events_created_brin;
-- 또는 BRIN 재구성
REINDEX INDEX idx_events_created_brin;

-- 효과 비교 — 1TB events 테이블 기준
-- B+Tree(created_at):  ~30GB,  build 6h
-- BRIN(created_at):    ~30MB,  build 5min
```

**관련 알고리즘**: [B+Tree](#b-plus-tree), [Bitmap Index](#bitmap-index), Zone Maps

---

<a id="covering-index"></a>
## 7. Covering Index (Index-Only Scan)

**목적**: SELECT/WHERE 에 등장하는 모든 컬럼을 인덱스에 포함시켜, table heap 접근 없이 **인덱스만으로 쿼리 종료**(Index-Only Scan)

**시간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Lookup + projection | O(log n + k) (heap 접근 0회) |
| Insert / Update | O(log n) — 인덱스 크기 증가 영향 |

**공간 복잡도**: O(n + |included columns|)

**특징**:
- B+Tree 인덱스에 추가 컬럼을 `INCLUDE` (PostgreSQL/SQL Server) 또는 composite 의 trailing 컬럼으로 포함
- MySQL InnoDB 의 secondary index 는 모두 PK 를 포함 → secondary 만으로 PK 조회는 자동 covering
- 쿼리 플랜에 **Index Only Scan** 또는 `Using index` 표시됨
- visibility map(PostgreSQL) 이 최신 상태여야 효과 최대 (vacuum 필요)

**장점**:
- heap 접근 회피로 I/O 큰 폭 감소 (특히 wide row, SSD 가 아닌 환경)
- hot path 쿼리에 강력
- composite 인덱스의 자연스러운 확장

**단점**:
- 인덱스 크기 증가 → DML 비용 상승, 캐시 압박
- `INCLUDE` 컬럼은 정렬/탐색에 사용 안 됨 (단순 payload)
- 너무 많이 만들면 write amplification

**사용처**:
- 자주 호출되는 read-heavy API 의 hot query
- `SELECT a,b,c FROM t WHERE k=?` 류의 좁은 projection
- 카운트/존재 쿼리 `SELECT COUNT(*) FROM t WHERE k=?`
- 분석 쿼리에서 큰 row 의 일부 컬럼만 사용할 때

**DB 별 지원**:

| DB | 키워드 | 비고 |
|---|---|---|
| PostgreSQL | `INCLUDE (...)` | 11+ |
| SQL Server | `INCLUDE (...)` | 2005+ |
| MySQL InnoDB | (자동) | secondary index 가 PK 포함 — composite trailing 으로 확장 |
| Oracle | (자동) | optimizer 가 Index-Only access path 선택 |

**SQL 예제**:
```sql
-- PostgreSQL: INCLUDE 로 payload 추가
CREATE INDEX idx_orders_lookup
  ON orders(tenant_id, status)
  INCLUDE (total_amount, created_at);

-- 이 쿼리는 Index Only Scan 가능 (heap 접근 0)
SELECT total_amount, created_at
  FROM orders
 WHERE tenant_id = 42 AND status = 'paid';

-- SQL Server: 동일 문법
CREATE NONCLUSTERED INDEX idx_orders_lookup
  ON orders(tenant_id, status)
  INCLUDE (total_amount, created_at);

-- MySQL InnoDB: composite 으로 자연스럽게 covering
CREATE INDEX idx_orders_cover
  ON orders(tenant_id, status, total_amount, created_at);

-- EXPLAIN 으로 확인
EXPLAIN SELECT total_amount FROM orders
 WHERE tenant_id=42 AND status='paid';
-- PostgreSQL:  "Index Only Scan using idx_orders_lookup"
-- MySQL:       Extra: "Using index"
```

**관련 알고리즘**: [B+Tree](#b-plus-tree), [Partial Index](#partial-index)

---

<a id="partial-index"></a>
## 8. Partial Index / Filtered Index (부분 인덱스)

**목적**: `WHERE` 조건을 만족하는 row 만 인덱싱 → 인덱스 크기 축소, hot path 가속, soft-delete 패턴 최적

**시간 복잡도**:
| 작업 | 복잡도 |
|------|--------|
| Lookup (조건 일치 쿼리) | O(log m), m = 조건 일치 row 수 |
| Lookup (조건 외 쿼리) | 인덱스 미사용 → Seq Scan |
| Insert / Update | O(log m) — 조건 외 row 는 인덱스 변경 없음 |

**공간 복잡도**: O(m) where m << n

**특징**:
- B+Tree(또는 다른 인덱스) 의 변형 — **WHERE 절을 인덱스 정의에 포함**
- optimizer 가 쿼리의 WHERE 와 인덱스의 WHERE 를 비교해서 적용 가능 여부 판단
- 인덱스의 WHERE 가 쿼리의 WHERE 를 **포함**해야 사용 가능

**장점**:
- 인덱스 크기 1/10 ~ 1/100 가능
- 통계 분포가 skewed 한 컬럼에서 효과 큼 (예: `is_active=true` 99%, `false` 1%)
- soft-delete 패턴(`deleted_at IS NULL`) 의 hot path 가속
- write 비용 절감 (조건 외 row 는 인덱스 무관)

**단점**:
- 쿼리의 WHERE 가 인덱스의 WHERE 와 호환되지 않으면 사용 안 됨
- WHERE 조건 변경 시 인덱스 재생성
- MySQL 은 미지원 (workaround: generated column + 일반 인덱스)

**사용처**:
- soft-delete: `WHERE deleted_at IS NULL`
- 활성 사용자: `WHERE status = 'active'`
- 처리 대기 큐: `WHERE processed = false`
- 최근 기간: `WHERE created_at > NOW() - INTERVAL '30 days'`

**DB 별 지원**:

| DB | 키워드 | 비고 |
|---|---|---|
| PostgreSQL | `WHERE` 절 in CREATE INDEX | 표준 |
| SQL Server | Filtered Index `WHERE` | 2008+ |
| Oracle | Function-based + DECODE | 직접 partial 은 없음 — function index 로 우회 |
| MySQL | — | 미지원 (generated column 우회) |
| SQLite | `WHERE` 절 | 3.8+ |

**SQL 예제**:
```sql
-- PostgreSQL: soft-delete hot path
CREATE INDEX idx_users_active_email
  ON users(email)
  WHERE deleted_at IS NULL;

-- 이 쿼리는 partial index 사용
SELECT * FROM users
 WHERE email = 'a@b.com' AND deleted_at IS NULL;

-- 이 쿼리는 partial index 미사용 — 조건 불일치
SELECT * FROM users WHERE email = 'a@b.com';
-- (deleted_at IS NULL 누락)

-- 큐 처리 패턴
CREATE INDEX idx_jobs_pending
  ON jobs(priority DESC, created_at)
  WHERE status = 'pending';

SELECT * FROM jobs
 WHERE status = 'pending'
 ORDER BY priority DESC, created_at
 LIMIT 100;

-- SQL Server filtered index
CREATE INDEX idx_orders_unpaid
  ON orders(customer_id, created_at)
  WHERE status <> 'paid';

-- MySQL workaround: generated column
ALTER TABLE users
  ADD COLUMN active_email VARCHAR(255)
    GENERATED ALWAYS AS (IF(deleted_at IS NULL, email, NULL)) STORED;
CREATE INDEX idx_users_active_email ON users(active_email);
```

**관련 알고리즘**: [B+Tree](#b-plus-tree), [Covering Index](#covering-index)

---

## 인덱스 선택 가이드

| 쿼리 패턴 | 1순위 | 2순위 |
|----------|-------|-------|
| `WHERE pk = ?` (PK lookup) | [B+Tree](#b-plus-tree) | [Hash](#hash-index) (in-memory) |
| `WHERE col = ?` (equality) | [B+Tree](#b-plus-tree) | [Hash](#hash-index) |
| `WHERE col BETWEEN ?` (range) | [B+Tree](#b-plus-tree) | [BRIN](#brin) (시계열) |
| `WHERE low_card = ? AND ...` | [Bitmap](#bitmap-index) (OLAP) | [B+Tree](#b-plus-tree) (OLTP) |
| `WHERE jsonb @> ?` / `WHERE arr @> ?` | [GIN](#gin) | — |
| `WHERE tsvector @@ ?` (full-text) | [GIN](#gin) | [GiST](#gist) |
| `WHERE ST_DWithin(geo, ?, ?)` | [GiST](#gist) (PostGIS) | — |
| `WHERE range && ?` (range overlap) | [GiST](#gist) | — |
| `ORDER BY point <-> ?` (KNN) | [GiST](#gist) | — |
| 시계열 append-only + range | [BRIN](#brin) | [B+Tree](#b-plus-tree) |
| hot path narrow projection | [Covering](#covering-index) | [B+Tree](#b-plus-tree) |
| soft-delete / sparse filter | [Partial](#partial-index) | [B+Tree](#b-plus-tree) |

## 안티패턴

- **모든 컬럼에 단일 인덱스**: composite / covering 으로 통합. 단일 인덱스 남발은 write amplification
- **high-cardinality 컬럼에 Bitmap**: 인덱스 크기 폭발 — B+Tree 사용
- **무작위 insert 테이블에 BRIN**: correlation 없으면 효과 0 — B+Tree 사용
- **JSONB 컬럼에 B+Tree**: containment 활용 불가 — GIN 사용
- **공간 컬럼에 B+Tree**: 차원 정렬 불가 — GiST 사용
- **soft-delete 풀 인덱스**: 99% 무관 row 까지 인덱싱 — Partial 사용
- **`SELECT *` 쿼리에 Covering**: 모든 컬럼 INCLUDE 는 의미 없음 — narrow projection 으로 제한

## 관련 카탈로그

- [data-structures.md](../../../dev-advisor/references/algorithms/data-structures.md) — B-Tree, Skip List, Hash, Bloom Filter 자료구조 본체
- [searching.md](../../../dev-advisor/references/algorithms/searching.md) — Hash Table Search, Binary Search 등 탐색 알고리즘
- [string.md](../../../dev-advisor/references/algorithms/string.md) — Trie, Suffix Array, Inverted Index (full-text 본체)
- [`../patterns/data-access.md`](../../../dev-advisor/references/patterns/data-access.md) — Repository, Query Object 패턴
- [probabilistic.md](../../../dev-advisor/references/algorithms/probabilistic.md) — Roaring Bitmap, Bloom Filter
