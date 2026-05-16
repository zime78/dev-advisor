# DB 쿼리 옵티마이저 알고리즘 (Database Query Optimizer Algorithms)

알고리즘 도메인의 신규 카테고리. RDBMS 옵티마이저가 SQL 을 물리 실행 계획(physical plan)으로 변환할 때 사용하는 **5개 핵심 정평 알고리즘** — Join 3종 / CBO vs Heuristic / Plan Cache / Statistics & Cardinality / EXPLAIN 분석. 기존 [`db-indexes.md`](db-indexes.md) (인덱스 구조) 와 [`db-storage-engines.md`](db-storage-engines.md) (스토리지·트랜잭션) 가 "어디에 데이터를 두는가" 라면 본 문서는 "**어떻게 데이터를 읽을지 결정하는가**" 영역.

**원전·표준 참고**:
- Selinger, Astrahan, Chamberlin, Lorie, Price — *Access Path Selection in a Relational Database Management System* (SIGMOD, 1979) — System R 옵티마이저
- Goetz Graefe — *Query Evaluation Techniques for Large Databases* (ACM Computing Surveys, 1993)
- Goetz Graefe — *The Cascades Framework for Query Optimization* (IEEE Data Eng Bull, 1995)
- Leis, Gubichev, Mirchev, Boncz, Kemper, Neumann — *How Good Are Query Optimizers, Really?* (VLDB, 2015)
- Mannino — *Database Design, Application Development, and Administration* (8판)
- *PostgreSQL Internals* (Egor Rogov, 2023)
- Database Internals (Alex Petrov, 2019)
- 공식 매뉴얼: PostgreSQL Planner, MySQL Optimizer, Oracle CBO White Paper, SQL Server Query Processor

**관련 카탈로그**:
- [`db-indexes.md`](db-indexes.md) — B+Tree / Hash / Bitmap / BRIN / Covering / Partial (인덱스 구조 8종)
- [`db-storage-engines.md`](db-storage-engines.md) — WAL / LSM / MVCC / Buffer Pool (스토리지·로깅·트랜잭션)
- [`../principles/database-fundamentals.md`](../principles/database-fundamentals.md) — 격리 수준 / ACID·BASE / CAP / Replication (이론 기반)
- [`../patterns/data-modeling.md`](../patterns/data-modeling.md) — 정규화·역정규화 (옵티마이저가 처리할 스키마 설계)
- [`../patterns/data-warehousing-bi.md`](../patterns/data-warehousing-bi.md) — OLAP / Star Schema / Lakehouse (대규모 분석 쿼리)
- [`searching.md`](searching.md) — Binary Search / Interpolation Search (옵티마이저의 lookup 기반)
- [`sorting.md`](sorting.md) — Merge Sort / External Sort (Sort-Merge Join 기반)

## 알고리즘 목차

| ID | 알고리즘 (영문) | 시간 복잡도 | 메모리 | 적용 시나리오 |
|----|----|----|----|----|
| [join-algorithms-hash-sortmerge-nestedloop](#join-algorithms-hash-sortmerge-nestedloop) | Join Algorithms (Hash / Sort-Merge / Nested-Loop) | O(N+M) ~ O(N·M) | O(M) ~ O(N+M) | 모든 join |
| [cbo-vs-heuristic-optimizer](#cbo-vs-heuristic-optimizer) | Cost-Based vs Heuristic Optimizer | O(n!) → O(n²·2ⁿ) DP | 통계 메타데이터 | plan 선택 |
| [plan-cache](#plan-cache) | Plan Cache / Prepared Statement / Bind Peeking | O(1) hit, O(plan) miss | O(cache_size) | OLTP |
| [cardinality-estimation-statistics](#cardinality-estimation-statistics) | Statistics / Cardinality Estimation | O(n) sample, O(buckets) query | O(buckets·cols) | CBO 입력 |
| [explain-analyze-guide](#explain-analyze-guide) | EXPLAIN ANALYZE 해독 (PG / MySQL / Oracle / MSSQL) | — | — | 진단 |

---

<a id="join-algorithms-hash-sortmerge-nestedloop"></a>
## 1. Join Algorithms — Hash Join / Sort-Merge Join / Nested Loop Join

**정의 (Definition)**: 두 릴레이션 R, S 의 조인 조건 `R.a = S.b` (또는 `θ`-조건) 을 만족하는 튜플 쌍을 찾는 물리 연산자(physical operator). 옵티마이저는 입력 크기·인덱스·메모리·정렬 유무를 보고 **3가지 기본 알고리즘** 중 하나(또는 이들의 변형)를 선택한다.

**메커니즘 (Mechanism)**:

### Nested Loop Join (NLJ) — "이중 for-loop"

```
function NestedLoopJoin(R, S, predicate):
    for r in R:                      -- outer relation
        for s in S:                  -- inner relation (인덱스가 있으면 lookup)
            if predicate(r, s):
                yield (r, s)
```

- **Index Nested Loop Join (INLJ)**: inner 가 인덱스를 가지면 O(|R| · log|S|) 로 단축
- **Block Nested Loop**: outer 를 페이지/블록 단위로 읽어 buffer 절약
- Selinger(1979) 이래 가장 오래된 알고리즘 — 항상 동작 보장(fallback)

### Sort-Merge Join (SMJ) — "정렬 후 병합"

```
function SortMergeJoin(R, S, predicate):
    R_sorted = sort(R, by=R.a)       -- 이미 정렬돼 있으면 skip
    S_sorted = sort(S, by=S.b)
    i, j = 0, 0
    while i < |R| and j < |S|:
        if R[i].a == S[j].b: yield (R[i], S[j]); advance both with duplicates
        elif R[i].a < S[j].b: i += 1
        else: j += 1
```

- 양쪽이 **이미 정렬**되어 있거나(인덱스 스캔 / `ORDER BY`), 외부 정렬(External Sort) 비용을 감수할 만한 큰 데이터셋에서 유리
- equality + range(`<`, `<=`) 모두 지원 (등치만 가능한 Hash 와의 차이)

### Hash Join (HJ) — "build + probe"

```
function HashJoin(R, S, predicate):
    -- Build phase: 작은 쪽(R 가정)으로 hash table 구축
    H = HashMap()
    for r in R:
        H[hash(r.a)].append(r)
    -- Probe phase: 큰 쪽 스캔하며 lookup
    for s in S:
        for r in H[hash(s.b)]:
            if r.a == s.b: yield (r, s)
```

- **Grace Hash Join**: build 쪽이 메모리에 안 들어가면 양쪽을 동일 해시로 **partition 한 후** 각 partition 을 메모리 내에서 hash join (Kitsuregawa, 1983)
- **Hybrid Hash Join**: 첫 partition 은 메모리 보존 + 나머지는 디스크 (Oracle/SQL Server 기본)
- equality(`=`) 에만 적용 가능 — range/inequality 는 NLJ/SMJ 로 폴백

**시간/공간 복잡도 (Complexity)**:

| 알고리즘 | 시간 (평균) | 시간 (최악) | 메모리 | I/O |
|---|---|---|---|---|
| Nested Loop | O(\|R\| · \|S\|) | O(\|R\| · \|S\|) | O(1) | \|R\| · \|S\| / B |
| INLJ (인덱스) | O(\|R\| · log\|S\|) | O(\|R\| · log\|S\|) | O(1) | \|R\| · log\|S\| |
| Sort-Merge | O((\|R\| + \|S\|) · log) | O((\|R\| + \|S\|) · log) | O(B) buffer | 2·(\|R\| + \|S\|) sort + scan |
| Hash Join | O(\|R\| + \|S\|) | O(\|R\| · \|S\|) (skew) | O(\|R_build\|) | \|R\| + \|S\| (1 pass) |
| Grace Hash | O(\|R\| + \|S\|) | — | O(B) buffer | 3·(\|R\| + \|S\|) (read-write-read) |

(B = buffer pages, sort 의 log 베이스 = B)

**SQL / EXPLAIN 예시 (SQL Examples)**:

```sql
-- 시나리오: orders(10M rows) JOIN customers(1M rows) ON customer_id

-- (1) Nested Loop (PG default with small outer + indexed inner)
EXPLAIN ANALYZE
SELECT o.id, c.name
  FROM orders o JOIN customers c ON c.id = o.customer_id
 WHERE o.created_at > NOW() - INTERVAL '1 hour';
-- Expected plan:
--   Nested Loop  (cost=0.43..XXX rows=N)
--     -> Index Scan on orders_created_at_idx
--     -> Index Scan on customers_pkey (c.id = o.customer_id)

-- (2) Hash Join (대량 JOIN — 인덱스 없을 때)
EXPLAIN ANALYZE
SELECT c.country, SUM(o.amount)
  FROM orders o JOIN customers c ON c.id = o.customer_id
 GROUP BY c.country;
-- Expected plan:
--   HashAggregate
--     -> Hash Join  (hash cond: o.customer_id = c.id)
--          -> Seq Scan on orders
--          -> Hash
--               -> Seq Scan on customers

-- (3) Merge Join (양쪽 정렬된 인덱스 활용)
EXPLAIN ANALYZE
SELECT *
  FROM orders o JOIN customers c
       ON c.id = o.customer_id
 ORDER BY c.id;
-- Expected plan:
--   Merge Join  (merge cond: o.customer_id = c.id)
--     -> Index Scan on orders_customer_idx (sorted)
--     -> Index Scan on customers_pkey (sorted)
```

**DBMS 차이 (DBMS Differences)**:

| DBMS | NLJ 힌트 | Hash 힌트 | Merge 힌트 | 기본 선택 정책 |
|---|---|---|---|---|
| PostgreSQL | `SET enable_nestloop=on` | `enable_hashjoin` | `enable_mergejoin` | CBO — 행 추정·메모리(`work_mem`) 비교 |
| MySQL (8.0+) | 8.0.18 이전엔 NLJ 만 | 8.0.18+ Hash Join (default) | 미지원 (8.0 까지) | `optimizer_switch`, 8.0 부터 Hash |
| Oracle | `/*+ USE_NL(t1 t2) */` | `/*+ USE_HASH(t1 t2) */` | `/*+ USE_MERGE(t1 t2) */` | CBO — `*_AREA_SIZE` + `PGA_AGGREGATE_TARGET` |
| SQL Server | `INNER LOOP JOIN` | `INNER HASH JOIN` | `INNER MERGE JOIN` | CBO — Memory Grant Feedback |

**선택 기준 (Decision Matrix)**:

| 조건 | 권장 알고리즘 |
|---|---|
| outer 작고 inner 인덱스 존재 | **Index Nested Loop** (OLTP point lookup) |
| 양쪽 정렬됨 (인덱스 / `ORDER BY`) | **Sort-Merge** |
| 양쪽 큼 + 메모리 충분 + equality | **Hash Join** (OLAP/ETL 기본) |
| `JOIN ... ON r.a < s.b` (inequality) | NLJ 또는 SMJ (Hash 불가) |
| 한쪽이 페이지 수 ≤ buffer | Block Nested Loop |
| memory 부족 + equality + 대량 | **Grace Hash / Hybrid Hash** |

**관련 알고리즘**: [Sort-Merge 기반 정렬](sorting.md#merge-sort), [External Merge Sort](sorting.md#external-merge-sort), [Hash Table — data-structures 카탈로그](data-structures.md)

**Cross-link**: [`cbo-vs-heuristic-optimizer`](#cbo-vs-heuristic-optimizer) (옵티마이저가 어떤 join 알고리즘 선택), [`cardinality-estimation-statistics`](#cardinality-estimation-statistics) (행 추정 = 알고리즘 선택 입력)

---

<a id="cbo-vs-heuristic-optimizer"></a>
## 2. Cost-Based Optimizer vs Heuristic (Rule-Based) Optimizer

**정의 (Definition)**: SQL 의 논리적 동치(equivalent) plan 들 중 실행 비용이 **최소**인 plan 을 선택하는 의사결정 알고리즘. 두 학파:
- **Heuristic / Rule-Based Optimizer (RBO)** — 고정된 규칙(예: "인덱스 있으면 무조건 사용", "WHERE 절을 가장 먼저") 으로 plan 선택. Oracle 8 까지 표준
- **Cost-Based Optimizer (CBO)** — 통계 기반 비용 함수 `cost = α·CPU + β·I/O + γ·Memory` 를 추정해 최저 비용 plan 선택. **모든 현대 RDBMS 의 기본**

**메커니즘 (Mechanism)** — System R / Cascades 프레임워크 (Selinger 1979 / Graefe 1995):

```
function CostBasedOptimize(query):
    -- (1) Parsing & Binding
    ast = parse(query)
    logical = bind(ast, schema)           -- 객체 해석

    -- (2) Logical Rewriting (Heuristic 단계 — 항상 유리한 변환)
    logical = applyRules(logical, [
        predicate_pushdown,                -- WHERE 절을 join 아래로
        projection_pushdown,               -- SELECT 컬럼만 위로
        constant_folding,
        subquery_unnesting,
        view_merging,
        join_elimination
    ])

    -- (3) Cost-based Plan Enumeration (DP — Selinger algorithm)
    --     n-way join 의 순서를 (left-deep tree 기준) 동적 계획법으로 탐색
    --     상태 공간 = 2^n (모든 부분집합) × n (외부 릴레이션 후보)
    bestPlan = null
    bestCost = ∞
    for each plan in enumeratePlans(logical):
        cost = estimateCost(plan, statistics)
        if cost < bestCost:
            bestPlan = plan; bestCost = cost

    return bestPlan
```

**비용 추정 공식 (Cost Model)**:

```
cost(SeqScan)         = pages_read · seq_page_cost + rows · cpu_tuple_cost
cost(IndexScan)       = log(rows) · random_page_cost + matched_rows · cpu_index_tuple_cost
cost(NestedLoop R,S)  = cost(R) + |R| · cost(S_per_lookup)
cost(HashJoin R,S)    = cost(R) + cost(S) + (|R| + |S|) · cpu_tuple_cost
cost(SortMerge R,S)   = cost(R) + cost(S) + (|R|·log|R| + |S|·log|S|) · cpu_tuple_cost
```

**시간/공간 복잡도 (Complexity)**:

| 단계 | 복잡도 |
|---|---|
| Logical rewrite | O(rules · plan_size) |
| Plan enumeration (DP) | O(n² · 2ⁿ) (Selinger left-deep) |
| Plan enumeration (Cascades) | O(2ⁿ · 부분집합) — bushy tree 까지 |
| Cost estimation per plan | O(joins) |
| Heuristic 전체 | O(n²) (규칙 기반 그리디) |

n = join 대상 테이블 수. n ≥ 10 부터 DP 폭발 → **Genetic Query Optimizer** (PostgreSQL `geqo_threshold=12`) 또는 **greedy join enumeration** (Oracle `_optimizer_max_permutations`) 으로 폴백.

**비교표 (RBO vs CBO)**:

| 항목 | Heuristic (RBO) | Cost-Based (CBO) |
|---|---|---|
| 결정 근거 | 고정 규칙 (예: 인덱스 우선, WHERE 푸시다운) | 통계 기반 비용 추정 |
| 통계 필요 | 불필요 | **필수** (히스토그램, NDV, MCV 등) |
| 일관성 | 항상 동일 plan (재현 가능) | 통계 변화 시 plan 변화 (불안정) |
| 성능 | 단순 쿼리 빠름, 복잡 쿼리 부정확 | 복잡 쿼리에 우수 |
| 대표 DBMS | Oracle 8 이하, 일부 임베디드 | PostgreSQL / MySQL 8 / Oracle 10+ / SQL Server / DB2 |
| 단점 | 통계 무시 → 최악 plan 선택 가능 | 통계 부정확 시 더 나쁠 수 있음 (Leis 2015 *How Good Are Query Optimizers, Really?*) |

**SQL / EXPLAIN 예시**:

```sql
-- PostgreSQL — CBO 비용 출력
EXPLAIN (COSTS, BUFFERS) SELECT * FROM orders WHERE customer_id = 42;
-- Index Scan using orders_customer_idx on orders
--   (cost=0.43..8.45 rows=1 width=64)
--   Index Cond: (customer_id = 42)
--   Buffers: shared hit=4

-- Oracle — RBO 강제 (legacy, 권장 X)
ALTER SESSION SET OPTIMIZER_MODE=RULE;          -- Oracle 9i 까지
SELECT /*+ RULE */ * FROM orders WHERE customer_id = 42;

-- Oracle — CBO + 힌트
SELECT /*+ FIRST_ROWS(10) INDEX(o orders_customer_idx) */ *
  FROM orders o WHERE customer_id = 42;

-- SQL Server — Query Store 로 plan 안정화
ALTER DATABASE MyDB SET QUERY_STORE = ON;
-- (regressed plan 강제 가능: sp_query_store_force_plan)
```

**DBMS 차이 (DBMS Differences)**:

| DBMS | 옵티마이저 종류 | 통계 갱신 | 힌트 지원 | Plan 안정화 |
|---|---|---|---|---|
| PostgreSQL | CBO (System R 계열) | `ANALYZE table`, `autovacuum_analyze_*` | `pg_hint_plan` 확장 (미공식) | `pg_stat_statements`, plan_cache (no force) |
| MySQL 8 | CBO + 일부 Heuristic | `ANALYZE TABLE`, `innodb_stats_persistent` | `/*+ INDEX(t i) */` 인라인 (8.0+) | Optimizer Trace |
| Oracle | CBO (RBO 도 historical) | `DBMS_STATS.GATHER_*_STATS` | 풍부한 hint 문법 (40+종) | SQL Plan Management (SPM), SQL Profile, Baseline |
| SQL Server | CBO + Cascades 기반 | `UPDATE STATISTICS`, Auto Update | `OPTION(...)` + `QUERYTRACEON` | Query Store, Plan Guide, Force Plan |

**관련 알고리즘**: [Dynamic Programming — 카탈로그 진입](dynamic-programming.md), [Cardinality Estimation](#cardinality-estimation-statistics), [Genetic Algorithms](search-systems.md) (geqo)

**Cross-link**: [`cardinality-estimation-statistics`](#cardinality-estimation-statistics) (CBO 입력), [`plan-cache`](#plan-cache) (선택된 plan 보존), [`join-algorithms-hash-sortmerge-nestedloop`](#join-algorithms-hash-sortmerge-nestedloop) (CBO 출력)

---

<a id="plan-cache"></a>
## 3. Plan Cache — Statement Cache / Prepared Statement / Bind Variable Peeking / Plan Cache Pollution

**정의 (Definition)**: 옵티마이저가 만들어낸 실행 계획(plan)을 메모리 캐시에 보존해 동일 SQL 의 재컴파일을 피하는 메커니즘. OLTP 환경에서 **컴파일 비용(parse + bind + optimize) ≥ 실행 비용** 인 경우가 흔하므로 plan cache 적중률이 처리량을 좌우한다.

**메커니즘 (Mechanism)**:

```
function ExecuteSQL(sql, params):
    -- (1) Cache key 계산
    key = normalize(sql)         -- whitespace, case 등 정규화
                                  -- bind variable (?) 는 키에서 제거

    -- (2) Cache lookup
    if cache.contains(key):
        plan = cache.get(key)
        if plan.statistics_valid():
            return execute(plan, params)
        else:
            cache.invalidate(key)    -- 통계 무효화

    -- (3) Cache miss → 컴파일
    ast      = parse(sql)
    logical  = bind(ast, schema, params)
    physical = optimize(logical, statistics)
    cache.put(key, physical)
    return execute(physical, params)
```

### Bind Variable / Prepared Statement

```sql
-- ❌ Hard parse 매번 발생 (cache key 마다 다름)
SELECT * FROM orders WHERE id = 1;
SELECT * FROM orders WHERE id = 2;
SELECT * FROM orders WHERE id = 3;    -- 3 plans

-- ✅ Prepared statement — 단일 cache entry
PREPARE q AS SELECT * FROM orders WHERE id = $1;
EXECUTE q(1); EXECUTE q(2); EXECUTE q(3);   -- 1 plan, 3 executions
```

### Bind Variable Peeking (BVP)

Oracle 의 첫 번째 실행 시 bind 값을 **엿보아(peek)** 통계에 결합해 plan 을 만드는 기법. 첫 값이 비대표적이면 후속 실행에 부적합한 plan 이 캐시됨 → **Plan instability**.

```sql
-- 첫 실행: customer_id = 1 (selectivity 0.0001) → Index Scan 선택
EXECUTE q(1);
-- 후속 실행: customer_id = 999 (selectivity 0.5) → Index Scan 사용 (실제로는 Seq Scan 이 유리)
EXECUTE q(999);   -- 잘못된 plan 재사용
```

해결: **Adaptive Cursor Sharing** (Oracle 11g+), **Plan Stability via SPM**, **Re-prepare on stats change**.

### Plan Cache Pollution

- **literal flood**: bind 미사용 → 캐시가 거의 동일한 SQL 으로 가득 차 hit rate ↓
- **SQL injection 방지** 와 동일 원인 → bind 강제는 양쪽 모두 해결
- **cursor leak**: 미완료 cursor 가 cache slot 점유

**시간/공간 복잡도 (Complexity)**:

| 작업 | 복잡도 |
|---|---|
| Cache hit | O(1) hash + O(plan size) execute |
| Cache miss (hard parse) | O(parse + optimize) = O(n²·2ⁿ) for n joins |
| Bind | O(params) |
| Eviction (LRU) | O(1) amortized |

캐시 크기:
- Oracle Shared Pool: 수십 MB ~ 수 GB
- SQL Server Plan Cache: `sys.dm_exec_cached_plans`
- PostgreSQL: 세션별 prepared statement (PgBouncer transaction mode 시 무력화 주의)
- MySQL: 8.0 이후 Query Cache 제거 → prepared statement 만

**SQL / EXPLAIN 예시**:

```sql
-- PostgreSQL prepared statement
PREPARE get_order(int) AS
  SELECT * FROM orders WHERE id = $1;
EXPLAIN (ANALYZE, BUFFERS) EXECUTE get_order(42);
-- PostgreSQL 5번 실행 후 generic plan 으로 전환 (plan_cache_mode)

-- Oracle — Plan cache 조회
SELECT sql_id, plan_hash_value, executions, buffer_gets, parse_calls
  FROM v$sql
 WHERE sql_text LIKE 'SELECT * FROM orders%'
 ORDER BY parse_calls DESC;

-- SQL Server — Plan cache 조회
SELECT cp.objtype, cp.usecounts, cp.size_in_bytes, qt.text
  FROM sys.dm_exec_cached_plans cp
 CROSS APPLY sys.dm_exec_sql_text(cp.plan_handle) qt
 ORDER BY cp.usecounts DESC;

-- MySQL — Prepared statement
PREPARE q FROM 'SELECT * FROM orders WHERE id = ?';
EXECUTE q USING @id;
DEALLOCATE PREPARE q;
```

**DBMS 차이 (DBMS Differences)**:

| DBMS | 캐시 이름 | 강제 bind | BVP | 무효화 트리거 | 모니터 뷰 |
|---|---|---|---|---|---|
| PostgreSQL | Prepared statement (세션) | `PREPARE` 명시 | 5회 후 generic plan | `ANALYZE`, schema change | `pg_prepared_statements` |
| MySQL 8 | Prepared statement | `PREPARE ... USING` | 없음 (literal 우선) | DDL, ANALYZE | `performance_schema.prepared_statements_instances` |
| Oracle | Shared SQL Area | `CURSOR_SHARING=FORCE` | 11g+ Adaptive | `DBMS_STATS`, DDL, flush | `v$sql`, `v$sql_plan` |
| SQL Server | Plan Cache | `sp_executesql` | Parameter Sniffing | UPDATE STATISTICS, `DBCC FREEPROCCACHE` | `sys.dm_exec_cached_plans` |

**관련 알고리즘**: [LRU Cache](data-structures.md#lru), [Hash Table — data-structures 카탈로그](data-structures.md), [Memoization — Fibonacci DP](dynamic-programming.md#fibonacci)

**Cross-link**: [`cbo-vs-heuristic-optimizer`](#cbo-vs-heuristic-optimizer) (캐시되는 산출물), [`../patterns/data-modeling.md`](../patterns/data-modeling.md) (스키마 안정성과 cache 수명)

---

<a id="cardinality-estimation-statistics"></a>
## 4. Statistics / Cardinality Estimation — Histogram / MCV / Selectivity

**정의 (Definition)**: CBO 가 비용을 계산하려면 각 연산자가 처리할 **행 수(cardinality)** 와 **선택도(selectivity)** 를 알아야 한다. 통계는 테이블 / 컬럼 / 인덱스의 분포를 압축 표현(히스토그램, 샘플, MCV) 하여 옵티마이저 입력으로 제공한다. Leis(VLDB 2015)는 *현대 옵티마이저의 plan 오류 90% 이상이 cardinality 추정 실패* 임을 증명했다.

**메커니즘 (Mechanism)**:

### Equi-width Histogram (등폭 히스토그램)

```
buckets = [(min, min+w], (min+w, min+2w], ..., (max-w, max]]
selectivity(col BETWEEN a AND b) = Σ (overlap(bucket, [a,b]) / w) · bucket_freq / total
```

- 단순하지만 skew 큰 데이터에서 부정확

### Equi-depth (Equi-height) Histogram (등빈도 히스토그램)

```
-- 1) 데이터 정렬
sorted = sort(column_values)
-- 2) n 등분 — 각 버킷이 동일한 행 수
buckets = []
for i in 0..n-1:
    lo = sorted[i · |sorted|/n]
    hi = sorted[(i+1) · |sorted|/n - 1]
    buckets.append((lo, hi, |sorted|/n))
-- 3) selectivity = (matched buckets · rows_per_bucket) / total
```

- skew 데이터에서 정확도 ↑ — 모든 RDBMS 기본
- PostgreSQL `default_statistics_target = 100` (버킷 수)

### Sample (샘플링)

- 테이블 전체 스캔 비용 회피 — 30K~300K 행 무작위 추출
- Reservoir Sampling (한 번의 스캔으로 균등 샘플) — [`probabilistic.md`](probabilistic.md) 참조
- PostgreSQL `ANALYZE` 기본 30K · `default_statistics_target`

### Most Common Values (MCV)

- 상위 K 개 빈값을 빈도와 함께 별도 보존 — skew 처리
- 빈도가 임계 이상인 값은 히스토그램에서 빼고 MCV 로 분리 → 잔여만 히스토그램화
- PostgreSQL `pg_stats.most_common_vals`, `most_common_freqs`

### Selectivity 추정 공식

```
selectivity(col = constant):
    if constant ∈ MCV: return MCV.freq[constant]
    else: return (1 - Σ MCV.freq) / (n_distinct - |MCV|)

selectivity(col BETWEEN a AND b):
    return Σ histogram_bucket_overlap(a, b) / total

selectivity(p1 AND p2) ≈ s1 · s2    -- 독립 가정 (대부분 위반됨 → multivariate stats)
selectivity(p1 OR  p2) ≈ s1 + s2 - s1·s2
```

### 다변량 통계 (Multivariate Statistics)

`(city, country)` 같은 함수 종속(functional dependency) 컬럼은 독립 가정 위반 → 다변량 통계로 보정:
- PostgreSQL `CREATE STATISTICS s_city (dependencies) ON city, country FROM addresses;`
- SQL Server: multi-column statistics auto-created
- Oracle: `DBMS_STATS.CREATE_EXTENDED_STATS`

**시간/공간 복잡도 (Complexity)**:

| 작업 | 복잡도 |
|---|---|
| 히스토그램 구축 (sample) | O(s·log s) (s = sample size, 보통 30K) |
| 히스토그램 룩업 | O(log B) (B = bucket 수, binary search) |
| MCV 룩업 | O(log K) or O(1) hash |
| Selectivity 계산 | O(1) per predicate |
| 전체 통계 갱신 (`ANALYZE`) | O(n) 또는 O(sample) |

공간:
- 히스토그램 1 컬럼: O(B) ≈ 100 · (key_size + freq_size) ≈ 수 KB
- MCV: O(K · key_size) ≈ 수 KB
- 다변량 통계: O(B²) 또는 sketch 기반

**SQL / EXPLAIN 예시**:

```sql
-- PostgreSQL — pg_stats 뷰
SELECT attname, n_distinct, most_common_vals, most_common_freqs,
       histogram_bounds, correlation
  FROM pg_stats
 WHERE tablename = 'orders' AND attname = 'customer_id';

-- 통계 갱신
ANALYZE VERBOSE orders;
ANALYZE orders (customer_id, created_at);   -- 일부 컬럼만

-- 통계 정확도 향상 (버킷 수)
ALTER TABLE orders ALTER COLUMN customer_id SET STATISTICS 1000;
ANALYZE orders;

-- 다변량 통계
CREATE STATISTICS stat_city_country (dependencies, ndistinct)
  ON city, country FROM addresses;
ANALYZE addresses;

-- Oracle — DBMS_STATS
EXEC DBMS_STATS.GATHER_TABLE_STATS('SCHEMA', 'ORDERS',
       estimate_percent => DBMS_STATS.AUTO_SAMPLE_SIZE,
       method_opt => 'FOR ALL COLUMNS SIZE AUTO');

-- SQL Server — UPDATE STATISTICS
UPDATE STATISTICS orders WITH FULLSCAN;
DBCC SHOW_STATISTICS('orders', 'IX_orders_customer_id');

-- MySQL — InnoDB 분석
ANALYZE TABLE orders;
SHOW INDEX FROM orders;   -- Cardinality 컬럼 확인
SET GLOBAL innodb_stats_persistent_sample_pages = 100;
```

**DBMS 차이 (DBMS Differences)**:

| DBMS | 갱신 명령 | 자동 갱신 | 히스토그램 종류 | MCV | 다변량 |
|---|---|---|---|---|---|
| PostgreSQL | `ANALYZE` | autovacuum (행 10% 변경) | Equi-depth | `most_common_vals` 최대 100 | `CREATE STATISTICS` (10+) |
| MySQL 8 | `ANALYZE TABLE` | `innodb_stats_auto_recalc=ON` (10% 변경) | Equi-height (8.0+) | 없음 | 없음 |
| Oracle | `DBMS_STATS.GATHER_*` | Auto Task (야간) | Frequency / Top-K / Hybrid | implicit | Extended Statistics |
| SQL Server | `UPDATE STATISTICS` | Auto Update (20% + 500) | Step (200 step max) | 없음 (rare values) | Multi-column auto |

**관련 알고리즘**: [Histogram](probabilistic.md#count-min-sketch), [Reservoir Sampling](probabilistic.md#reservoir-sampling), [HyperLogLog](probabilistic.md#hyperloglog) (NDV 추정)

**Cross-link**: [`cbo-vs-heuristic-optimizer`](#cbo-vs-heuristic-optimizer) (통계 소비자), [`plan-cache`](#plan-cache) (통계 무효화 = 캐시 무효화), [`../principles/database-fundamentals.md`](../principles/database-fundamentals.md) (read consistency 와 통계 일관성)

---

<a id="explain-analyze-guide"></a>
## 5. EXPLAIN 분석 가이드 — PostgreSQL / MySQL / Oracle / SQL Server 해독

**정의 (Definition)**: `EXPLAIN` 계열 명령으로 옵티마이저가 선택한 실행 계획과 실측 비용을 출력해 **plan 회귀(plan regression)**, **카디널리티 misestimate**, **불필요한 I/O** 를 진단하는 표준 도구. 각 RDBMS 의 출력 포맷·키워드가 다르므로 통합 해독 능력이 SQL 튜닝의 핵심 스킬.

**메커니즘 (Mechanism)** — 4대 DBMS 공통 해독 절차:

```
function ReadExplain(plan):
    -- (1) 최하위 노드부터 (bottom-up) — 자식이 먼저 실행됨
    --     PostgreSQL: 들여쓰기 깊은 노드가 먼저
    --     SQL Server: 오른쪽 → 왼쪽

    -- (2) 각 노드별 5요소 확인
    for node in plan:
        check(node.operator)         -- Seq Scan / Index Scan / Hash Join 등
        check(node.estimated_rows)   -- 옵티마이저 추정
        check(node.actual_rows)      -- 실측 (ANALYZE 시만)
        check(node.cost)             -- 추정 비용
        check(node.timing)           -- 실측 시간 (ANALYZE 시만)

    -- (3) Red flag 검출
    --     - estimated_rows / actual_rows 비율 > 10× → 통계 부정확
    --     - Seq Scan on large table + low selectivity → 인덱스 누락
    --     - Nested Loop with high outer row count → Hash 로 전환 필요
    --     - Sort + Disk → work_mem 부족 (PG) / tempdb spill (MSSQL)
    --     - Hash Join with build > work_mem → Disk hash
```

**PostgreSQL `EXPLAIN ANALYZE` 해독**:

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT)
SELECT c.country, SUM(o.amount) AS total
  FROM orders o JOIN customers c ON c.id = o.customer_id
 WHERE o.created_at >= '2026-01-01'
 GROUP BY c.country;

-- 출력 예시:
-- HashAggregate  (cost=15234.56..15240.12 rows=12 width=40)
--                (actual time=234.567..234.890 rows=15 loops=1)
--   Group Key: c.country
--   Buffers: shared hit=12345 read=678
--   -> Hash Join  (cost=512.34..14890.12 rows=45678 width=24)
--                 (actual time=12.345..220.123 rows=46123 loops=1)
--        Hash Cond: (o.customer_id = c.id)
--        -> Seq Scan on orders o
--             (cost=0.00..14000.00 rows=45678 width=16)
--             (actual time=0.034..150.234 rows=46123 loops=1)
--             Filter: (created_at >= '2026-01-01')
--             Rows Removed by Filter: 953877
--        -> Hash  (cost=400.00..400.00 rows=1000 width=16)
--             -> Seq Scan on customers c (cost=0.00..400.00 rows=1000)
-- Planning Time: 1.234 ms
-- Execution Time: 235.567 ms
```

**해독 포인트**:
- `cost=15234..15240` — start_cost..total_cost (페이지 추정 단위)
- `rows=12` (estimated) vs `rows=15` (actual) — 비율 1.25, 양호
- `loops=1` — 노드 실행 횟수 (NLJ inner 는 outer rows 만큼)
- `Buffers: shared hit=12345 read=678` — buffer pool 적중 vs 디스크 read
- `Rows Removed by Filter: 953877` → **인덱스 미사용 신호** (95% 필터링됨)

**MySQL `EXPLAIN FORMAT=TREE` (8.0.18+) 해독**:

```sql
EXPLAIN FORMAT=TREE
SELECT c.country, SUM(o.amount)
  FROM orders o JOIN customers c ON c.id = o.customer_id
 WHERE o.created_at >= '2026-01-01'
 GROUP BY c.country;

-- 출력:
-- -> Group aggregate: sum(o.amount)
--    -> Sort: c.country
--       -> Stream results  (cost=18450.34 rows=46123)
--          -> Hash join (c.id = o.customer_id)  (cost=18450.34 rows=46123)
--             -> Table scan on c  (cost=100.45 rows=1000)
--             -> Hash
--                -> Filter: (o.created_at >= DATE'2026-01-01')  (cost=14000)
--                   -> Table scan on o  (cost=14000 rows=1000000)

-- EXPLAIN ANALYZE (8.0.18+) — 실측 추가
EXPLAIN ANALYZE SELECT ...;
-- -> Hash join (...)  (cost=18450.34 rows=46123)
--                     (actual time=12.345..220.123 rows=46123 loops=1)
```

**해독 포인트**:
- `actual time=START..END` — 첫 행 / 마지막 행 시간(ms)
- `rows=46123 loops=1` — 실측 행 수 / 반복 횟수
- `Using filesort` (legacy FORMAT) — 정렬 비용 발생
- `Using temporary` — 임시 테이블 사용 (GROUP BY 미스)
- `key=NULL` — 인덱스 미사용

**Oracle `DBMS_XPLAN` 해독**:

```sql
EXPLAIN PLAN FOR
SELECT c.country, SUM(o.amount)
  FROM orders o JOIN customers c ON c.id = o.customer_id
 WHERE o.created_at >= DATE '2026-01-01'
 GROUP BY c.country;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY(format => 'ALL +ALLSTATS LAST'));

-- 출력:
-- Plan hash value: 1234567890
-- ----------------------------------------------------------------
-- | Id  | Operation              | Name      | Rows  | Cost (%CPU)|
-- ----------------------------------------------------------------
-- |   0 | SELECT STATEMENT       |           |    12 |  15234   (1)|
-- |   1 |  HASH GROUP BY         |           |    12 |  15234   (1)|
-- |*  2 |   HASH JOIN            |           | 45678 |  14890   (1)|
-- |*  3 |    TABLE ACCESS FULL   | ORDERS    | 45678 |  14000   (1)|
-- |   4 |    TABLE ACCESS FULL   | CUSTOMERS |  1000 |    400   (1)|
-- ----------------------------------------------------------------
-- Predicate Information:
--   2 - access("C"."ID"="O"."CUSTOMER_ID")
--   3 - filter("O"."CREATED_AT">=TO_DATE('2026-01-01','YYYY-MM-DD'))

-- 실제 실행 + 통계 (V$SQL_PLAN_STATISTICS_ALL)
SELECT /*+ GATHER_PLAN_STATISTICS */ ...;
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(format => 'ALLSTATS LAST'));
```

**해독 포인트**:
- `Cost (%CPU)` — 옵티마이저 비용 + CPU 비중 (%)
- `*` 표시 — predicate 가 적용된 노드
- `Plan hash value` — plan 비교용 해시 (regression 추적)
- `A-Rows` vs `E-Rows` (ALLSTATS) — 추정 vs 실측 ratio

**SQL Server `SET SHOWPLAN_TEXT` / `SHOWPLAN_XML` 해독**:

```sql
-- Actual plan (실측)
SET STATISTICS PROFILE ON;
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SELECT c.country, SUM(o.amount)
  FROM orders o JOIN customers c ON c.id = o.customer_id
 WHERE o.created_at >= '2026-01-01'
 GROUP BY c.country;

-- 또는 GUI (SSMS Ctrl+M) → Actual Execution Plan

-- Text plan
SET SHOWPLAN_TEXT ON;
GO
SELECT ...;
-- |--Hash Match(Aggregate, HASH:([c].[country]) DEFINE:([Expr1004]=SUM([o].[amount])))
--    |--Hash Match(Inner Join, HASH:([c].[id])=([o].[customer_id]))
--       |--Table Scan(OBJECT:([customers] AS [c]))
--       |--Table Scan(OBJECT:([orders] AS [o]), WHERE:([created_at]>='2026-01-01'))

-- DMV 로 cached plan 조회
SELECT qs.execution_count, qs.total_logical_reads,
       qp.query_plan, qt.text
  FROM sys.dm_exec_query_stats qs
 CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
 CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle) qp
 ORDER BY qs.total_logical_reads DESC;
```

**해독 포인트**:
- Actual Execution Plan 의 굵은 화살표 = 행 수 많음
- 노란/빨간 경고 아이콘 = Missing Index / Implicit Conversion / No Statistics
- `Estimated Number of Rows` vs `Actual Number of Rows` 비율 → 통계 진단
- `Memory Grant` 부족 → tempdb spill 발생 가능

**진단 패턴 vs 처방 (Diagnosis Matrix)**:

| 증상 (EXPLAIN 단서) | 가능 원인 | 처방 |
|---|---|---|
| Seq Scan / Full Table Scan on large table | 인덱스 누락 / 통계 부정확 | `CREATE INDEX`, `ANALYZE` |
| `Rows Removed by Filter` 대량 | 인덱스 미사용 (함수 / 캐스팅) | functional index, query rewrite |
| Estimated rows ≪ Actual rows (10×+) | 통계 stale / multivariate dep | `ANALYZE`, `CREATE STATISTICS`, multi-column hist |
| Nested Loop with outer >100K rows | join order 오류 / 통계 부정확 | Hash Join 힌트, `ANALYZE`, work_mem 증가 |
| Sort with `disk` / `tempdb spill` | sort_mem 부족 | `work_mem` ↑ (PG), `tempdb` 분산 (MSSQL) |
| Hash join build > work_mem (batched/disk) | build 쪽이 너무 큼 | 작은 쪽이 build 되도록 join 순서 변경 |
| Plan hash value 변경 (Oracle) | plan regression | SPM Baseline, plan force |
| `Bitmap Heap Scan` + `Rows Removed by Filter` | bitmap recheck | 더 선택적인 인덱스 |

**시간/공간 복잡도 (Complexity)**:

| 명령 | 비용 |
|---|---|
| `EXPLAIN` (plan만) | 컴파일 비용만 (실행 X) |
| `EXPLAIN ANALYZE` | **실제 쿼리 실행** + 측정 오버헤드 (~10%) |
| `EXPLAIN (BUFFERS)` | buffer 카운터 활성화 — 추가 오버헤드 미미 |
| `STATISTICS PROFILE` (MSSQL) | per-row 측정 — 큰 결과셋에서 무거움 |

**DBMS 차이 (DBMS Differences)**:

| DBMS | 추정 plan | 실측 plan | 포맷 옵션 | Plan 식별자 | GUI |
|---|---|---|---|---|---|
| PostgreSQL | `EXPLAIN` | `EXPLAIN (ANALYZE, BUFFERS)` | TEXT / JSON / XML / YAML | (없음, pg_stat_statements id) | pgAdmin, depesz.com/explain |
| MySQL 8 | `EXPLAIN` | `EXPLAIN ANALYZE` (8.0.18+) | TRADITIONAL / JSON / TREE (8.0.16+) | (없음) | MySQL Workbench |
| Oracle | `EXPLAIN PLAN FOR ... ; DBMS_XPLAN.DISPLAY()` | `/*+ GATHER_PLAN_STATISTICS */` + `DISPLAY_CURSOR` | BASIC/TYPICAL/ALL/+ALLSTATS LAST | `plan_hash_value`, `sql_id` | SQL Developer, Tuning Pack |
| SQL Server | `SET SHOWPLAN_TEXT/XML ON` | `Ctrl+M` (Actual Plan) + `STATISTICS PROFILE` | XML / Text / Graphical | `plan_hash`, `query_hash` | SSMS, SQL Sentry Plan Explorer |

**모범 진단 워크플로우 (Best Practice)**:

```
1. EXPLAIN (plan 만) → 구조 파악
2. EXPLAIN ANALYZE → 실측 vs 추정 비교
3. estimated vs actual row count 비율 > 10× 노드 식별
4. 해당 노드의 통계 갱신 (ANALYZE / DBMS_STATS / UPDATE STATISTICS)
5. 인덱스 / 힌트 / 쿼리 재작성 검토
6. 변경 전후 plan hash 비교 → 회귀 방지
7. Plan baseline / Query Store 로 안정 plan 고정
```

**관련 알고리즘**: [Binary Search](searching.md#binary-search) (히스토그램 lookup), [Top-K](data-structures.md), [Profiling](concurrent.md)

**Cross-link**: 본 카탈로그 4개 항목과 모두 직접 연결됨 — [`join-algorithms-hash-sortmerge-nestedloop`](#join-algorithms-hash-sortmerge-nestedloop), [`cbo-vs-heuristic-optimizer`](#cbo-vs-heuristic-optimizer), [`plan-cache`](#plan-cache), [`cardinality-estimation-statistics`](#cardinality-estimation-statistics). 외부: [`db-indexes.md`](db-indexes.md) (인덱스 진단), [`db-storage-engines.md`](db-storage-engines.md) (Buffer Pool hit/miss 해석)

---

## 요약 매트릭스 (Summary Matrix)

| 항목 | 핵심 결정 | 측정 도구 |
|---|---|---|
| Join 알고리즘 | NLJ (소-인덱스) / SMJ (양쪽 정렬) / Hash (대량 equality) | EXPLAIN |
| 옵티마이저 | CBO (현대 표준) — 통계 의존 | plan_hash 추적 |
| Plan Cache | bind variable 강제 → cache pollution 회피 | `pg_prepared_statements`, `v$sql` |
| Statistics | Equi-depth + MCV + 다변량 | `pg_stats`, `DBMS_STATS` |
| EXPLAIN | estimated vs actual ratio < 10× 유지 | `EXPLAIN ANALYZE` |

**관련 카탈로그 (역방향 cross-link 의무)**:
- [`db-indexes.md`](db-indexes.md) — 옵티마이저가 선택할 인덱스 후보
- [`db-storage-engines.md`](db-storage-engines.md) — Buffer Pool / WAL / MVCC 가 plan 비용에 미치는 영향
- [`../principles/database-fundamentals.md`](../principles/database-fundamentals.md) — 격리 수준이 plan 선택에 미치는 영향 (snapshot vs read committed)
- [`../patterns/data-modeling.md`](../patterns/data-modeling.md) — 정규화/역정규화가 join 비용에 미치는 영향
- [`../patterns/data-warehousing-bi.md`](../patterns/data-warehousing-bi.md) — Star Schema 가 옵티마이저 join 순서에 미치는 영향 (star transformation)
