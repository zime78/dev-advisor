# data-advisor 레퍼런스 인덱스

DMBOK KA 기반 데이터 관리 카탈로그. 49 항목 (patterns 18 / algorithms 23 / principles 8).

## 카테고리 진입점

| 카테고리 | 항목 수 | 파일 |
|---------|--------:|------|
| Master Data Management | 6 | [patterns/mdm.md](patterns/mdm.md) |
| Data Quality & Governance | 6 | [patterns/data-quality.md](patterns/data-quality.md) |
| Data Warehousing & BI | 6 | [patterns/data-warehousing.md](patterns/data-warehousing.md) |
| DB 인덱스 | 8 | [algorithms/db-indexes.md](algorithms/db-indexes.md) |
| DB 스토리지 엔진 | 10 | [algorithms/db-storage-engines.md](algorithms/db-storage-engines.md) |
| DB 쿼리 최적화 | 5 | [algorithms/db-query-optimizer.md](algorithms/db-query-optimizer.md) |
| DB 기초 원칙 | 8 | [principles/db-fundamentals.md](principles/db-fundamentals.md) |

## 알고리즘 ID 매핑

| ID | 영문명 | 한국어명 | 카테고리 | 링크 |
|----|--------|----------|----------|------|
| b-plus-tree | B+Tree Index | B+트리 인덱스 | DB 인덱스 | [algorithms/db-indexes.md#b-plus-tree](algorithms/db-indexes.md#b-plus-tree) |
| hash-index | Hash Index | 해시 인덱스 | DB 인덱스 | [algorithms/db-indexes.md#hash-index](algorithms/db-indexes.md#hash-index) |
| bitmap-index | Bitmap Index | 비트맵 인덱스 | DB 인덱스 | [algorithms/db-indexes.md#bitmap-index](algorithms/db-indexes.md#bitmap-index) |
| gin | GIN (Generalized Inverted Index) | 일반화 역색인 | DB 인덱스 | [algorithms/db-indexes.md#gin](algorithms/db-indexes.md#gin) |
| gist | GiST (Generalized Search Tree) | 일반화 검색 트리 | DB 인덱스 | [algorithms/db-indexes.md#gist](algorithms/db-indexes.md#gist) |
| brin | BRIN (Block Range Index) | 블록 범위 인덱스 | DB 인덱스 | [algorithms/db-indexes.md#brin](algorithms/db-indexes.md#brin) |
| covering-index | Covering Index | 커버링 인덱스 | DB 인덱스 | [algorithms/db-indexes.md#covering-index](algorithms/db-indexes.md#covering-index) |
| partial-index | Partial Index | 부분 인덱스 | DB 인덱스 | [algorithms/db-indexes.md#partial-index](algorithms/db-indexes.md#partial-index) |
| wal | Write-Ahead Log (WAL) | 선기록 로그 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#wal](algorithms/db-storage-engines.md#wal) |
| lsm-tree | LSM Tree | 로그 구조 머지 트리 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#lsm-tree](algorithms/db-storage-engines.md#lsm-tree) |
| sstable | SSTable | 정렬 문자열 테이블 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#sstable](algorithms/db-storage-engines.md#sstable) |
| compaction-strategy | Compaction Strategy | 컴팩션 전략 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#compaction-strategy](algorithms/db-storage-engines.md#compaction-strategy) |
| mvcc-vacuum | MVCC Vacuum / GC | MVCC 진공 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#mvcc-vacuum](algorithms/db-storage-engines.md#mvcc-vacuum) |
| buffer-pool | Buffer Pool / Page Cache | 버퍼 풀 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#buffer-pool](algorithms/db-storage-engines.md#buffer-pool) |
| page-layout-slotted | Slotted Page Layout | 슬롯 페이지 레이아웃 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#page-layout-slotted](algorithms/db-storage-engines.md#page-layout-slotted) |
| b-link-tree | B-Link Tree | 동시성 B-Tree | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#b-link-tree](algorithms/db-storage-engines.md#b-link-tree) |
| replication-log | Replication Log | 복제 로그 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#replication-log](algorithms/db-storage-engines.md#replication-log) |
| hot-update | HOT Update (Heap-Only Tuple) | 힙 전용 튜플 갱신 | DB 스토리지 엔진 | [algorithms/db-storage-engines.md#hot-update](algorithms/db-storage-engines.md#hot-update) |
| join-algorithms-hash-sortmerge-nestedloop | Join Algorithms (NLJ/SMJ/Hash) | Join 알고리즘 | DB 쿼리 최적화 | [algorithms/db-query-optimizer.md#join-algorithms-hash-sortmerge-nestedloop](algorithms/db-query-optimizer.md#join-algorithms-hash-sortmerge-nestedloop) |
| cbo-vs-heuristic-optimizer | CBO vs Heuristic Optimizer | 비용기반/규칙기반 옵티마이저 | DB 쿼리 최적화 | [algorithms/db-query-optimizer.md#cbo-vs-heuristic-optimizer](algorithms/db-query-optimizer.md#cbo-vs-heuristic-optimizer) |
| plan-cache | Plan Cache / Prepared Statement | 플랜 캐시 | DB 쿼리 최적화 | [algorithms/db-query-optimizer.md#plan-cache](algorithms/db-query-optimizer.md#plan-cache) |
| cardinality-estimation-statistics | Cardinality Estimation / Statistics | 카디널리티 추정 | DB 쿼리 최적화 | [algorithms/db-query-optimizer.md#cardinality-estimation-statistics](algorithms/db-query-optimizer.md#cardinality-estimation-statistics) |
| explain-analyze-guide | EXPLAIN ANALYZE 해석 가이드 | EXPLAIN ANALYZE | DB 쿼리 최적화 | [algorithms/db-query-optimizer.md#explain-analyze-guide](algorithms/db-query-optimizer.md#explain-analyze-guide) |

## 패턴 ID 매핑

### Master Data Management (patterns/mdm.md) — 6

| ID | 영문명 | 한국어명 |
|----|--------|----------|
| mdm-golden-record | Golden Record | 골든 레코드 |
| mdm-survivorship-rules | Survivorship Rules | 생존 규칙 |
| mdm-match-merge | Match-Merge | 매칭-병합 |
| mdm-data-steward | Data Steward | 데이터 스튜어드 |
| mdm-reference-data | Reference Data Management | 참조 데이터 관리 |
| mdm-hierarchy | Hierarchy Management | 계층 관리 |

### Data Quality & Governance (patterns/data-quality.md) — 6

| ID | 영문명 | 한국어명 |
|----|--------|----------|
| dq-6-dimensions | DQ 6 Dimensions | DQ 6 차원 |
| data-lineage | Data Lineage | 데이터 리니지 |
| data-catalog | Data Catalog | 데이터 카탈로그 |
| dq-stewardship-raci | DQ Stewardship RACI | DQ 스튜어드십 RACI |
| openlineage-standard | OpenLineage Standard | OpenLineage 표준 |
| dq-validation-tools | DQ Validation Tools | DQ 검증 도구 |

### Data Warehousing & BI (patterns/data-warehousing.md) — 6

| ID | 영문명 | 한국어명 |
|----|--------|----------|
| kimball-star-snowflake | Kimball Star / Snowflake Schema | 차원 모델링 |
| scd-types | Slowly Changing Dimensions | SCD 타입 |
| fact-table-types | Fact Table 4종 | 팩트 테이블 |
| olap-cube-tabular | OLAP Cube vs Tabular | OLAP 큐브 |
| lakehouse-iceberg-delta-hudi | Lakehouse (Iceberg/Delta/Hudi) | 레이크하우스 |
| dbt-modeling | dbt Modeling | dbt 모델링 |

## 원칙 ID 매핑

### DB 기초 원칙 (principles/db-fundamentals.md) — 8

| ID | 영문명 | 한국어명 |
|----|--------|----------|
| tx-isolation-levels | Transaction Isolation Levels | 트랜잭션 격리 수준 |
| ansi-sql-anomaly | ANSI SQL Anomalies | SQL 이상 현상 |
| normalization-1nf-bcnf | Normalization (1NF→BCNF) | 정규화 |
| acid-vs-base | ACID vs BASE | ACID/BASE |
| cap-pacelc | CAP / PACELC Theorem | CAP/PACELC |
| consistency-models | Consistency Models | 일관성 모델 |
| db-replication | DB Replication | DB 복제 |
| db-partitioning | DB Partitioning | DB 파티셔닝 |

## 별칭

| 별칭 | Primary ID | 설명 |
|------|-----------|------|
| mdm | mdm-golden-record | MDM 단축 (골든 레코드 진입점) |
| golden-record | mdm-golden-record | Golden Record |
| survivorship | mdm-survivorship-rules | Survivorship Rules |
| match-merge | mdm-match-merge | Match-Merge |
| reference-data | mdm-reference-data | Reference Data Management |
| dq | dq-6-dimensions | DQ 단축 (6차원 진입점) |
| data-quality | dq-6-dimensions | Data Quality |
| lineage | data-lineage | Data Lineage |
| catalog | data-catalog | Data Catalog |
| openlineage | openlineage-standard | OpenLineage |
| dbt | dbt-modeling | dbt |
| dwh | kimball-star-snowflake | DWH 단축 (Kimball 진입점) |
| kimball | kimball-star-snowflake | Kimball Star Schema |
| star-schema | kimball-star-snowflake | Star Schema |
| snowflake-schema | kimball-star-snowflake | Snowflake Schema |
| scd | scd-types | SCD 약어 |
| slowly-changing-dimensions | scd-types | SCD 정식 |
| fact-table | fact-table-types | Fact Table |
| lakehouse | lakehouse-iceberg-delta-hudi | Lakehouse |
| iceberg | lakehouse-iceberg-delta-hudi | Apache Iceberg |
| delta-lake | lakehouse-iceberg-delta-hudi | Delta Lake |
| hudi | lakehouse-iceberg-delta-hudi | Apache Hudi |
| relational-database | tx-isolation-levels | RDB 격리 진입점 |
| rdbms | tx-isolation-levels | RDBMS 격리 진입점 |
| db-fundamentals | tx-isolation-levels | DB 기초 진입점 |
| acid | acid-vs-base | ACID 격리·트랜잭션 |
| base | acid-vs-base | BASE (eventual consistency) |
| cap | cap-pacelc | Brewer CAP |
| pacelc | cap-pacelc | Abadi PACELC |
| normalization | normalization-1nf-bcnf | 정규화 |
| isolation-levels | tx-isolation-levels | 격리 수준 |
| sharding | db-partitioning | DB 샤딩 |
| db-sharding | db-partitioning | DB 샤딩 단축 |
| query-optimizer | cbo-vs-heuristic-optimizer | 쿼리 옵티마이저 |
| join | join-algorithms-hash-sortmerge-nestedloop | Join 알고리즘 |
| hash-join | join-algorithms-hash-sortmerge-nestedloop | Hash Join |
| sort-merge-join | join-algorithms-hash-sortmerge-nestedloop | Sort-Merge Join |
| nested-loop-join | join-algorithms-hash-sortmerge-nestedloop | Nested Loop Join |
| prepared-statement | plan-cache | Prepared Statement |
| explain-analyze | explain-analyze-guide | EXPLAIN ANALYZE |
