# Data Warehousing & BI Patterns

데이터 웨어하우스(DW) / 비즈니스 인텔리전스(BI) 분야에서 검증된 6대 모델링·저장·변환 패턴 묶음. **Kimball Group**(Ralph Kimball, *The Data Warehouse Toolkit* 3판, 2013) + **Inmon CIF**(Bill Inmon, *Building the Data Warehouse* 4판, 2005) + **Data Vault 2.0**(Dan Linstedt, 2013) 3대 학파를 비교 축으로 삼고, 현대 Lakehouse(Iceberg/Delta/Hudi) + dbt(data build tool) 모델링 표준을 통합 정리한다.

**카테고리 위치**: `patterns/`. 분석계(OLAP) 데이터 모델링은 본 문서, 운영계(OLTP) 정규화는 [`principles/database-fundamentals.md#normalization-1nf-bcnf`](../principles/database-fundamentals.md#normalization-1nf-bcnf), 마스터/참조 데이터는 [`patterns/master-data-management.md`](master-data-management.md), 품질·계보는 [`patterns/data-quality-governance.md`](data-quality-governance.md), CAP/replication/CDC 는 [`patterns/data-modeling.md`](data-modeling.md) 분리.

**Kimball vs Inmon vs Data Vault 비교**:

| 축 | Kimball (Dimensional / Star) | Inmon CIF (3NF EDW) | Data Vault 2.0 |
|---|---|---|---|
| 목표 | 분석·BI 우선 (bottom-up data marts) | 전사 단일 정합성 (top-down EDW + marts) | 감사·이력 보존 + agile 통합 |
| 모델 | Star/Snowflake (denormalized) | 3NF normalized | Hub / Link / Satellite |
| 적재 | ETL → mart 직접 | ETL → EDW → marts | EDW raw vault → business vault → marts |
| 변경 추적 | SCD Type 1/2/3/4/6 | 별도 history 테이블 | Satellite 가 변경 hash 자동 보존 |
| 사용처 | 마트·리포트·OLAP 큐브 | 보험/금융 EDW | 규제 산업 (감사·계보·재현) |

본 문서는 Kimball 디멘셔널 모델링을 주축으로 하되, Data Vault 는 6번 항목 마지막에 cross-link 로 언급한다.

---

## 1. Kimball Star / Snowflake Schema — 차원 모델링 4단계 설계

<a id="kimball-star-snowflake"></a>

### 정의

분석계 데이터를 **Fact (측정값)** + **Dimension (분석 축)** 두 테이블 종류로 비정규화하여 조회 성능과 가독성을 최우선으로 설계하는 모델링 방식. Star(차원 1단계, 비정규화) vs Snowflake(차원 N단계, 일부 정규화) 변형이 있다.

### 메커니즘 — Kimball 4단계 (Four-Step Design Process)

Kimball Group 공식 4단계 (*The Data Warehouse Toolkit* 3rd, Ch.3):

1. **Choose the Business Process** (분석 대상 비즈니스 프로세스 선정): 주문, 결제, 클릭, 의료 진료 등 **단일 이벤트 흐름** 하나만 선정. "전체 마케팅" 같은 추상 범위는 금지.
2. **Declare the Grain** (그레인 = 사실 1행이 의미하는 단위 선언): "주문 1건당 1행" vs "주문 라인 아이템 1건당 1행" vs "일별 매출 집계 1행". **그레인을 먼저 못 박은 뒤** 차원/사실을 결정.
3. **Identify the Dimensions** (그 그레인에서 분석 가능한 축 식별): Who(고객) / What(상품) / When(날짜) / Where(매장) / Why(프로모션) / How(채널). 보통 4~15개.
4. **Identify the Facts** (그레인에서 측정 가능한 숫자 식별): quantity, amount, discount, tax, profit. **반드시 그레인과 일치**하는 가산 가능(Additive) 측정값을 우선.

### SQL 예시 (Star Schema)

```sql
-- Fact: 일별 매출 (그레인: 주문 라인 아이템 1건)
CREATE TABLE fact_sales (
  order_id              BIGINT       NOT NULL,
  line_item_id          INT          NOT NULL,
  date_key              INT          NOT NULL REFERENCES dim_date(date_key),
  customer_key          BIGINT       NOT NULL REFERENCES dim_customer(customer_key),
  product_key           BIGINT       NOT NULL REFERENCES dim_product(product_key),
  store_key             INT          NOT NULL REFERENCES dim_store(store_key),
  quantity              INT          NOT NULL,
  unit_price            DECIMAL(18,2) NOT NULL,
  discount_amount       DECIMAL(18,2) NOT NULL DEFAULT 0,
  net_amount            DECIMAL(18,2) NOT NULL,  -- = quantity * unit_price - discount
  PRIMARY KEY (order_id, line_item_id)
);

-- Dimension: 고객 (Type 2 SCD — surrogate key + valid_from/to)
CREATE TABLE dim_customer (
  customer_key          BIGINT       PRIMARY KEY,    -- surrogate
  customer_id           VARCHAR(50)  NOT NULL,        -- natural / business key
  name                  VARCHAR(200) NOT NULL,
  tier                  VARCHAR(20)  NOT NULL,        -- silver/gold/platinum
  region                VARCHAR(50)  NOT NULL,
  valid_from            DATE         NOT NULL,
  valid_to              DATE         NOT NULL DEFAULT DATE '9999-12-31',
  is_current            BOOLEAN      NOT NULL DEFAULT TRUE
);
```

### Star vs Snowflake 비교

| 축 | Star | Snowflake |
|---|---|---|
| 차원 정규화 | 비정규화 (1단계) | 정규화 (N단계, 차원 → 서브차원) |
| 조회 SQL | 1 join | N joins |
| 스토리지 | 중복 큼 | 중복 작음 |
| 성능 | 빠름 (column store + denorm) | 느림 (join 폭증) |
| 가독성 | 높음 (BI 툴 친화) | 낮음 |
| 사용처 | 기본 권장 (Kimball) | 차원이 매우 크거나 계층 깊을 때만 |

**현대 권장**: column-store(Snowflake, BigQuery, Redshift) 환경에서는 **Star 가 거의 항상 우세**. Snowflake schema 는 차원이 1억 행 이상이고 계층 (예: 상품 카테고리 5단계) 이 깊을 때만 부분 적용.

### 출처

- Ralph Kimball, Margy Ross, *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling* 3rd ed., Wiley 2013 (Ch.1~3)
- Kimball Group Reader, *Relentlessly Practical Tools for Data Warehousing and Business Intelligence*, Wiley 2010
- Kimball Group, [Dimensional Modeling Techniques](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)

---

## 2. SCD (Slowly Changing Dimensions) Type 1/2/3/4/6 + Bridge Table

<a id="scd-types"></a>

### 정의

차원 테이블의 속성이 시간에 따라 천천히 변경될 때 변경 이력을 어떻게 보존할지 정의한 표준 패턴. Kimball 이 Type 1~3 을 1996년 제안, 이후 Type 4 / 6 / 7 이 추가되어 현재 공식 표준은 **Type 0~7 + Hybrid**.

### Type 비교표 (메커니즘)

| Type | 변경 시 동작 | 이력 보존 | 쿼리 복잡도 | 사용처 |
|---|---|---|---|---|
| **0** | 변경 무시 (immutable) | 없음 | 가장 단순 | 생년월일, 가입일 |
| **1** | 덮어쓰기 (overwrite) | 없음 | 단순 | 오타 정정, 분석 불필요 |
| **2** | 새 행 추가 (surrogate key + valid_from/to) | **전체 보존** | 중간 (point-in-time join 필요) | **가장 흔함**. 고객 tier, 주소 |
| **3** | 새 컬럼 추가 (current_value + previous_value) | 직전 1개만 | 단순 | "이전 부서명" 1단계 추적 |
| **4** | 분리 테이블 (current + history) | 전체 (분리) | 중간 (history 테이블 join) | 매우 큰 차원, 자주 변경 |
| **6** | Type 1+2+3 결합 (현재값 + surrogate + 직전값) | 전체 | 가장 복잡 | 양쪽 보고서 모두 필요 |
| **7** | Type 1 (현재) + Type 2 (이력) **이중 PK** | 전체 (이중 뷰) | 복잡 | BI 도구가 "현재" / "당시" 선택 |

### SQL 예시 — Type 2 변경 적용

```sql
-- 고객 tier 가 silver → gold 로 변경된 경우 (2026-05-16)
BEGIN;
  -- 기존 행 expire
  UPDATE dim_customer
     SET valid_to = DATE '2026-05-15',
         is_current = FALSE
   WHERE customer_id = 'C-1001'
     AND is_current = TRUE;

  -- 새 행 insert
  INSERT INTO dim_customer
    (customer_key, customer_id, name, tier, region, valid_from, valid_to, is_current)
  VALUES
    (nextval('dim_customer_seq'), 'C-1001', 'Alice Kim', 'gold', 'KR-SE',
     DATE '2026-05-16', DATE '9999-12-31', TRUE);
COMMIT;

-- Point-in-time join (2026-03-01 시점의 tier)
SELECT f.order_id, f.net_amount, d.tier
  FROM fact_sales f
  JOIN dim_customer d
    ON d.customer_id = f.customer_business_id
   AND DATE '2026-03-01' BETWEEN d.valid_from AND d.valid_to;
```

### Bridge Table — 다대다 차원

차원이 다대다 관계일 때 (예: 환자 ↔ 진단명 N:M, 직원 ↔ 역할 N:M) Fact 와 Dimension 사이에 **Bridge Table** 을 두어 weighting factor (가중치) 로 합계 왜곡을 방지.

```sql
CREATE TABLE bridge_patient_diagnosis (
  patient_key       BIGINT  NOT NULL REFERENCES dim_patient(patient_key),
  diagnosis_group   BIGINT  NOT NULL,   -- 그룹 ID
  diagnosis_key     BIGINT  NOT NULL REFERENCES dim_diagnosis(diagnosis_key),
  weighting_factor  DECIMAL(5,4) NOT NULL,  -- 가중치 합 = 1.0 per 그룹
  PRIMARY KEY (patient_key, diagnosis_group, diagnosis_key)
);
```

### 출처

- Kimball Group, [Slowly Changing Dimensions, Part 1 & 2](https://www.kimballgroup.com/2008/08/slowly-changing-dimensions-part-1/) (Type 0~7 공식 정의)
- *The Data Warehouse Toolkit* 3rd ed., Ch.5 (Procurement) — Type 2 / Type 3 / Bridge
- *The Kimball Group Reader* Ch.10 — Hybrid SCD (Type 6/7)

---

## 3. Fact Table 4종 — Transaction / Periodic Snapshot / Accumulating Snapshot / Factless

<a id="fact-table-types"></a>

### 정의

Fact Table 은 측정값 + 차원 외래키를 보유한 분석계의 중심 테이블. Kimball 은 그레인 성격에 따라 4가지 표준 유형으로 분류한다.

### 4종 비교표

| 유형 | 그레인 | 적재 방식 | 측정값 가산성 | 대표 사례 |
|---|---|---|---|---|
| **Transaction Fact** | 이벤트 1건 | append-only insert | 완전 가산 (Sum 가능) | 주문, 클릭, 결제 |
| **Periodic Snapshot** | 정해진 주기 (일/월) | 주기마다 일괄 insert | 반가산 (Semi-additive, 시간 차원 Sum 금지) | 일별 재고, 월별 잔고 |
| **Accumulating Snapshot** | 프로세스 1건 (수명 전체) | insert 후 단계마다 UPDATE | 일부 가산 | 주문→결제→배송→완료 |
| **Factless Fact** | 이벤트 발생 자체 (측정값 없음) | append-only insert (counter 컬럼만) | count 만 | 출석, 약속 등록, 노출 |

### SQL 예시

**Transaction Fact** — 결제 이벤트 1건 = 1행:
```sql
CREATE TABLE fact_payment_transaction (
  payment_id     BIGINT PRIMARY KEY,
  date_key       INT NOT NULL,
  customer_key   BIGINT NOT NULL,
  payment_method_key INT NOT NULL,
  amount         DECIMAL(18,2) NOT NULL    -- ✅ Sum/Avg/Min/Max 모두 가능
);
```

**Periodic Snapshot** — 매일 23:59 기준 재고:
```sql
CREATE TABLE fact_inventory_daily_snapshot (
  date_key       INT NOT NULL,
  product_key    BIGINT NOT NULL,
  warehouse_key  INT NOT NULL,
  quantity_on_hand INT NOT NULL,    -- ⚠️ 반가산: 제품·창고는 Sum 가능, 시간은 Sum 금지 (월별 평균만)
  PRIMARY KEY (date_key, product_key, warehouse_key)
);
```

**Accumulating Snapshot** — 주문 1건당 1행, 단계마다 UPDATE:
```sql
CREATE TABLE fact_order_accumulating (
  order_id            BIGINT PRIMARY KEY,
  order_date_key      INT,          -- 1단계
  payment_date_key    INT,          -- 2단계 (NULL → 채워짐)
  ship_date_key       INT,          -- 3단계
  delivery_date_key   INT,          -- 4단계
  days_order_to_ship  INT,          -- 계산 컬럼
  days_ship_to_deliver INT,
  total_amount        DECIMAL(18,2) NOT NULL
);
```

**Factless Fact** — 학생 출석:
```sql
CREATE TABLE fact_student_attendance (
  date_key      INT NOT NULL,
  student_key   BIGINT NOT NULL,
  class_key     INT NOT NULL,
  attended_flag TINYINT NOT NULL DEFAULT 1,  -- 0/1 만 (count 분석)
  PRIMARY KEY (date_key, student_key, class_key)
);
```

### 가산성 (Additivity) 3분류 — 반드시 명시

| 분류 | 모든 차원 Sum 가능? | 예시 |
|---|---|---|
| Additive (완전 가산) | ✅ | quantity, amount |
| Semi-additive (반가산) | 일부 차원만 ✅ | balance (시간 X), inventory (시간 X) |
| Non-additive (비가산) | ❌ (Sum 불가, Avg/Ratio 만) | 비율, 단가, percentage |

### 출처

- *The Data Warehouse Toolkit* 3rd ed., Ch.4 (Inventory) — Periodic Snapshot
- *The Data Warehouse Toolkit* 3rd ed., Ch.6 (Order Management) — Accumulating Snapshot
- Kimball Group, [Three Fundamental Fact Table Grains](https://www.kimballgroup.com/2008/11/fact-tables/)

---

## 4. OLAP Cube vs Tabular — MOLAP / ROLAP / HOLAP / Tabular(Vertipaq) 비교

<a id="olap-cube-tabular"></a>

### 정의

OLAP(Online Analytical Processing) 은 사전 집계 + 다차원 분석을 위한 저장 엔진. 전통적 큐브(SSAS Multidimensional, Essbase) 와 현대 Tabular(SSAS Tabular, Power BI, Tableau) 로 양분된다.

### 4종 비교표

| 엔진 | 저장 방식 | 집계 방식 | 압축 | 응답 시간 | 사용처 |
|---|---|---|---|---|---|
| **MOLAP** (Multidimensional) | 다차원 배열 (proprietary cube) | 사전 집계(pre-aggregation) | 중간 | 가장 빠름 (~ms) | Essbase, SSAS Cube |
| **ROLAP** (Relational) | RDB 의 Star Schema | 쿼리 시 GROUP BY | DB 의존 | 느림 (~초) | MicroStrategy, MSTR |
| **HOLAP** (Hybrid) | MOLAP + ROLAP 혼합 | 핫 데이터는 MOLAP, 콜드는 ROLAP | 중간 | 중간 | SSAS Multidimensional + ROLAP partition |
| **Tabular** (Vertipaq) | 컬럼 저장(in-memory column store) | DAX 동적 + 자동 캐시 | **매우 높음**(10~100x) | 빠름 (~ms~수백ms) | SSAS Tabular, **Power BI**, Tableau Hyper |

### Tabular (Vertipaq) 메커니즘

Microsoft Vertipaq (xVelocity) 의 핵심:

1. **컬럼 스토리지**: 컬럼별 분리 저장 → cardinality 낮은 컬럼은 dictionary encoding (정수 ID 매핑) 으로 1~2 byte 까지 압축.
2. **RLE (Run-Length Encoding)**: 정렬된 데이터의 연속 값을 (값, 반복횟수) 로 압축.
3. **In-memory**: 전체 모델을 RAM 에 상주 → SSD 디스크 I/O 제거.
4. **DAX (Data Analysis Expressions)**: 동적 계산 표현식. `CALCULATE(SUM(Sales[Amount]), FILTER(...))` 같은 컨텍스트 변경 함수가 핵심.

### MDX vs DAX

- **MDX** (Multidimensional Expressions): MOLAP 큐브 표준. `SELECT [Measures].[Sales] ON COLUMNS, [Date].[Year].Members ON ROWS FROM [Sales Cube]`.
- **DAX** (Data Analysis Expressions): Tabular 표준. `Sales Total := SUMX(Sales, Sales[Quantity] * Sales[Unit Price])`. Excel 함수 문법과 유사.

### 12 OLAP 연산 (Codd, 1993)

Roll-up / Drill-down / Slice / Dice / Pivot / Drill-through / Drill-across / Hierarchy navigation / Time-series analysis / Top-N / Sub-totaling / Ranking — 모든 OLAP 엔진이 지원해야 하는 표준 12 연산.

### 출처

- E.F. Codd, S.B. Codd, C.T. Salley, *Providing OLAP to User-Analysts: An IT Mandate*, 1993 (OLAP 용어 + 12 규칙 창시)
- Marco Russo, Alberto Ferrari, *The Definitive Guide to DAX* 2nd ed., Microsoft Press 2019 (Vertipaq Ch.17)
- Microsoft Docs, [Tabular Model Solutions](https://learn.microsoft.com/analysis-services/tabular-models/tabular-models-ssas) / [Vertipaq Analyzer](https://www.sqlbi.com/tools/vertipaq-analyzer/)

---

## 5. Lakehouse — Apache Iceberg / Delta Lake / Apache Hudi 비교

<a id="lakehouse-iceberg-delta-hudi"></a>

### 정의

**Lakehouse** 는 Data Lake (Parquet/ORC 파일 + S3/HDFS) 위에 **ACID 트랜잭션 / time-travel / schema evolution / partition evolution** 을 부여하는 메타데이터 레이어. Databricks 가 2020년 *"Lakehouse: A New Generation of Open Platforms"* 논문에서 정의. 3대 구현체: **Apache Iceberg** (Netflix, 2018), **Delta Lake** (Databricks, 2019), **Apache Hudi** (Uber, 2017).

### 3종 비교표

| 축 | **Apache Iceberg** | **Delta Lake** | **Apache Hudi** |
|---|---|---|---|
| 시작 | 2018 (Netflix) | 2019 (Databricks) | 2017 (Uber) |
| 거버넌스 | Apache Foundation (vendor-neutral) | Linux Foundation (Databricks 주도) | Apache Foundation |
| 메타데이터 | metadata.json + manifest list + manifest files | `_delta_log/` (JSON + checkpoint Parquet) | `.hoodie/` (timeline = `.commit` + `.deltacommit` 등) |
| ACID | ✅ 스냅샷 격리 (SI) | ✅ 직렬화 격리 (SR) + optimistic concurrency | ✅ MVCC + optimistic |
| Time-travel | ✅ snapshot-id / timestamp / branch / tag | ✅ version / timestamp | ✅ instant time |
| Schema evolution | ✅ add/drop/rename/reorder/promote | ✅ add/drop (rename 제한) | ✅ add/drop (특정 type 제한) |
| **Partition evolution** | ✅ **(고유 강점)** rewrite 없이 hidden partition 변경 | ❌ (rewrite 필요) | ❌ (rewrite 필요) |
| Hidden partitioning | ✅ (`PARTITIONED BY (days(ts))`) | ❌ (Generated columns 우회) | ❌ (Partition path 명시) |
| Update/Delete | Copy-on-Write (CoW) + Merge-on-Read (MoR, v2) | CoW 기본, Deletion Vectors (v3) | **CoW + MoR 양쪽 1급** |
| Streaming | Flink/Spark structured streaming | Spark structured streaming | **Spark + Flink + Kafka Connect** (스트리밍 1급) |
| 카탈로그 | REST / Hive / Glue / Nessie / Polaris | Unity Catalog / Hive / Glue | Hive / Glue |
| 엔진 호환 | **최광** (Spark, Trino, Flink, Snowflake, BigQuery, DuckDB, ClickHouse) | Spark, Trino (제한), Databricks 우선 | Spark, Flink, Hive, Trino |

### Iceberg 메커니즘 (요약)

```
table_metadata.json (current snapshot 포인터)
        ↓
manifest_list.avro (스냅샷의 모든 manifest 목록 + partition stats)
        ↓
manifest_file.avro (각 데이터 파일 메타 + min/max 통계)
        ↓
data file (Parquet/ORC)
```

핵심 강점:
- **Snapshot Isolation**: 모든 읽기는 특정 스냅샷 ID 를 고정 → 동시 쓰기 영향 없음.
- **Partition Evolution**: `ALTER TABLE t SET PARTITION SPEC (days(ts))` → 과거 데이터 rewrite 불필요. metadata 만 변경.
- **Hidden Partitioning**: 사용자는 `WHERE ts > '2026-01-01'` 만 작성, Iceberg 가 자동으로 partition pruning.

### Delta Lake 메커니즘

```
_delta_log/
  00000000000000000000.json   (txn 0 — AddFile / RemoveFile / MetaData)
  00000000000000000001.json   (txn 1)
  ...
  00000000000000000010.checkpoint.parquet  (10 txn 마다 체크포인트)
```

- **Optimistic Concurrency Control**: 트랜잭션 충돌 시 conflict resolution rule (PutIfAbsent on S3) 로 재시도.
- **Deletion Vectors** (v3, 2024): 행 단위 삭제 시 파일 rewrite 회피 → MoR 효과.
- **Unity Catalog 통합**: Databricks 환경에서 RBAC + lineage + audit 자동.

### Hudi 메커니즘

- **Copy-on-Write (CoW)**: write 마다 새 Parquet 파일 생성. 읽기 성능 우수.
- **Merge-on-Read (MoR)**: 로그 파일(`.log.*`, Avro) 에 변경 누적 → 주기적 compaction. **upsert 빈도 높을 때** 유리.
- **DeltaStreamer**: Kafka / Kinesis / DFS 에서 자동 ingestion → Hudi 테이블에 upsert 적재.

### 선택 기준

| 상황 | 권장 |
|---|---|
| 멀티 엔진 호환 (Snowflake/BQ/Trino 등) | **Iceberg** |
| Partition 정책 자주 변경 | **Iceberg** (partition evolution) |
| Databricks 환경 + Unity Catalog | **Delta Lake** |
| 실시간 upsert (CDC, 스트리밍) | **Hudi** (MoR) 또는 Iceberg v2 |
| 행 단위 update/delete 빈도 매우 높음 | **Hudi MoR** > Delta v3 (DV) > Iceberg v2 |

### 출처

- Michael Armbrust et al., *Lakehouse: A New Generation of Open Platforms that Unify Data Warehousing and Advanced Analytics*, CIDR 2021 (Databricks)
- Apache Iceberg, [Iceberg Table Spec v3](https://iceberg.apache.org/spec/) (2024)
- Delta Lake, [Delta Transaction Log Protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md)
- Apache Hudi, [Concepts](https://hudi.apache.org/docs/concepts) (CoW / MoR / timeline)

---

## 6. dbt (data build tool) — 모델 / Snapshot / Test / Macro / Seed + Layer 패턴

<a id="dbt-modeling"></a>

### 정의

**dbt** 는 SQL + Jinja 템플릿으로 분석계 변환(T in ELT) 을 코드로 관리하는 오픈소스 도구. dbt Labs(구 Fishtown Analytics) 가 2016년부터 개발. **"Analytics Engineering"** 직군의 표준 도구로, 버전 관리·테스트·문서화·DAG 실행을 한 묶음으로 제공.

### 5대 구성 요소

| 요소 | 역할 | 파일 형식 |
|---|---|---|
| **Model** | SELECT 문 = 한 테이블/뷰. 의존성은 `{{ ref('other_model') }}` 로 명시 | `models/**/*.sql` |
| **Snapshot** | Type 2 SCD 자동화. `unique_key + strategy(check/timestamp)` 지정 | `snapshots/**/*.sql` |
| **Test** | 데이터 품질 검증 (not_null, unique, accepted_values, relationships) + Singular SQL test + Generic macro | `models/schema.yml` + `tests/**/*.sql` |
| **Macro** | Jinja 매크로 = 재사용 SQL 함수. 패키지(`dbt_utils`, `dbt_expectations`) 로 공유 | `macros/**/*.sql` |
| **Seed** | CSV → 테이블 적재. 매핑 테이블, 작은 reference data 용 | `seeds/**/*.csv` |

### Layer 패턴 — staging / intermediate / marts (dbt 공식 권장)

dbt Labs 공식 *"How we structure our dbt projects"* (2021~2024) 가이드의 3 레이어:

```
models/
├── staging/        # 1. source 와 1:1 매핑, 컬럼명 표준화·타입 캐스팅만
│   ├── stripe/
│   │   ├── stg_stripe__charges.sql
│   │   └── stg_stripe__customers.sql
│   └── _stripe__sources.yml
├── intermediate/   # 2. 비즈니스 로직 조합, 재사용 building blocks (다른 mart 가 참조)
│   ├── int_orders_joined_to_customers.sql
│   └── int_payments_pivoted.sql
└── marts/          # 3. 비즈니스 부서별 최종 테이블 (BI 도구 직접 조회)
    ├── finance/
    │   ├── fct_payments.sql
    │   └── dim_customers.sql
    └── marketing/
        └── fct_attributions.sql
```

**규칙**:
- `staging` → `intermediate` → `marts` **단방향** 의존 (역방향 금지).
- `staging` 파일명: `stg_<source>__<entity>.sql` (이중 underscore).
- `marts` 파일명: `fct_<entity>.sql` (Fact) / `dim_<entity>.sql` (Dimension).
- `staging` 는 보통 **view**, `intermediate`/`marts` 는 **table** materialization.

### SQL 예시 — Model + Test + Snapshot

**Model** (`models/marts/finance/fct_orders.sql`):
```sql
{{ config(materialized='table', partition_by={'field': 'order_date', 'data_type': 'date'}) }}

SELECT
    o.order_id,
    o.customer_id,
    DATE(o.created_at)              AS order_date,
    SUM(li.quantity * li.unit_price) AS gross_amount,
    SUM(li.discount_amount)          AS discount_amount,
    SUM(li.quantity * li.unit_price - li.discount_amount) AS net_amount
FROM {{ ref('stg_shopify__orders') }} o
LEFT JOIN {{ ref('stg_shopify__line_items') }} li
       ON li.order_id = o.order_id
GROUP BY 1, 2, 3
```

**Test** (`models/marts/finance/schema.yml`):
```yaml
version: 2
models:
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      - name: net_amount
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1000000
```

**Snapshot** (`snapshots/dim_customers_snapshot.sql`):
```sql
{% snapshot dim_customers_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key='customer_id',
    strategy='check',
    check_cols=['tier', 'region', 'email']
  )
}}
SELECT * FROM {{ ref('stg_shopify__customers') }}
{% endsnapshot %}
```

→ dbt 가 `dbt_valid_from / dbt_valid_to / dbt_scd_id` 컬럼을 자동 추가 (Type 2 SCD 자동 구현).

### 명령어 핵심

```bash
dbt run                          # 전체 모델 실행 (DAG 순서)
dbt run --select staging+        # staging 와 그 하위 의존 모두
dbt test                         # 모든 test 실행
dbt snapshot                     # snapshot 갱신
dbt docs generate && dbt docs serve  # 자동 lineage 문서 생성
dbt build                        # run + test + snapshot 한 번에
```

### Cross-link

- 데이터 품질 테스트 (dbt test / dbt_expectations / Great Expectations) 전반은 [`patterns/data-quality-governance.md#dq-validation-tools`](data-quality-governance.md#dq-validation-tools) 참조.
- Lineage / OpenLineage 표준은 [`patterns/data-quality-governance.md#openlineage-standard`](data-quality-governance.md#openlineage-standard) 참조.
- Master/Reference data 와의 join 전략은 [`patterns/master-data-management.md#mdm-reference-data`](master-data-management.md#mdm-reference-data) 참조.
- CDC / Materialized View 등 Lambda/Kappa 아키텍처는 [`patterns/data-modeling.md#lambda-kappa-htap`](data-modeling.md#lambda-kappa-htap) 참조.

### Data Vault 2.0 (참고)

본 문서는 Kimball 디멘셔널 중심이지만, **규제 산업(보험·금융·의료)** 에서는 Linstedt 의 **Data Vault 2.0** 이 EDW 1차 계층으로 자주 채택된다:
- **Hub**: 비즈니스 키 (예: `Hub_Customer.customer_id`).
- **Link**: Hub 간 관계 (예: `Link_Order_Customer`).
- **Satellite**: 시간별 변경 속성 (Hub/Link 마다 N 개 satellite, hash diff 기반 자동 이력).

특징: 감사·재현 가능성 최상, agile 통합 (새 source 추가 시 기존 모델 미영향), **Raw Vault → Business Vault → Information Marts** 3단 적재. Kimball 마트는 보통 Information Marts 단에서 Star 로 노출.

### 출처

- dbt Labs, [Best practices guides — How we structure our dbt projects](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
- Tristan Handy, *The Analytics Engineering Guide*, dbt Labs (online)
- Claire Carroll, *"How we structure our dbt projects"*, dbt Discourse 2021
- Dan Linstedt, Michael Olschimke, *Building a Scalable Data Warehouse with Data Vault 2.0*, Morgan Kaufmann 2015 (Data Vault 비교 참고)

---

## 통합 Cross-Link 맵

| 본 문서 anchor | 연결 대상 | 관계 |
|---|---|---|
| `kimball-star-snowflake` | `principles/database-fundamentals.md#normalization-1nf-bcnf` | OLTP 정규화 vs OLAP 비정규화 대비 |
| `scd-types` | `patterns/master-data-management.md#mdm-golden-record` | MDM Golden Record 의 시간 차원 = SCD Type 2 |
| `fact-table-types` | `patterns/data-modeling.md#cdc` | Accumulating Snapshot 의 update 소스 = CDC |
| `olap-cube-tabular` | `patterns/data-modeling.md#materialized-view` | MOLAP pre-aggregation = MV 의 분석계 확장 |
| `lakehouse-iceberg-delta-hudi` | `patterns/data-modeling.md#data-mesh-lakehouse` | 메타데이터 레이어 깊이 (본 문서) vs 조직/소유권 (data-mesh) |
| `dbt-modeling` | `patterns/data-quality-governance.md#dq-validation-tools` | dbt test 가 DQ 검증 도구의 한 종류 |
| `dbt-modeling` | `patterns/data-quality-governance.md#openlineage-standard` | dbt 가 OpenLineage 자동 emit 지원 |
| 전체 | `principles/database-fundamentals.md#acid-vs-base` | Lakehouse 의 ACID 보장 = OLTP ACID 의 OLAP 확장 |

## 참고 도서·표준 (요약)

- Ralph Kimball, Margy Ross, *The Data Warehouse Toolkit* 3rd ed., Wiley 2013
- Bill Inmon, *Building the Data Warehouse* 4th ed., Wiley 2005
- Dan Linstedt, Michael Olschimke, *Building a Scalable Data Warehouse with Data Vault 2.0*, MK 2015
- Michael Armbrust et al., *Lakehouse* paper, CIDR 2021
- Marco Russo, Alberto Ferrari, *The Definitive Guide to DAX* 2nd ed., Microsoft Press 2019
- Apache Iceberg / Delta Lake / Apache Hudi 공식 사양 문서
- dbt Labs *Best practices* 가이드
