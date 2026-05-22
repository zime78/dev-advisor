# 데이터베이스 기초 이론 (Database Fundamentals)

데이터 모델링 패턴([`../patterns/data-modeling.md`](../../../dev-advisor/references/patterns/data-modeling.md)) · 동시성 이론([`./concurrency-theory.md`](../../../dev-advisor/references/principles/concurrency-theory.md)) · 합의 알고리즘([`../algorithms/consensus.md`](../../../dev-advisor/references/algorithms/consensus.md)) 의 **이론적 기반** 8 항목. *트랜잭션·정합성·복제·파티셔닝* 의 기본 정의와 정형 보장.

**원전 참고**:
- Jim Gray — "The Transaction Concept: Virtues and Limitations", VLDB 1981
- Jim Gray, Andreas Reuter — *Transaction Processing: Concepts and Techniques* (1992)
- Hal Berenson, Phil Bernstein, Jim Gray, Jim Melton, Elizabeth O'Neil, Patrick O'Neil — "A Critique of ANSI SQL Isolation Levels", SIGMOD 1995
- Atul Adya, Barbara Liskov, Patrick O'Neil — "Generalized Isolation Level Definitions", ICDE 2000
- E. F. Codd — "A Relational Model of Data for Large Shared Data Banks", CACM 13(6), 1970
- E. F. Codd — "Further Normalization of the Data Base Relational Model", IBM Research 1971
- Raymond F. Boyce, E. F. Codd — "Recent Investigations into Relational Data Base Systems", IBM Research 1974
- Eric Brewer — "Towards Robust Distributed Systems", PODC 2000 keynote (CAP)
- Seth Gilbert, Nancy Lynch — "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services", SIGACT News 33(2), 2002
- Daniel Abadi — "Consistency Tradeoffs in Modern Distributed Database System Design: CAP is Only Part of the Story", IEEE Computer 45(2), 2012 (PACELC)
- Werner Vogels — "Eventually Consistent", CACM 52(1), 2009
- David K. Gifford — "Weighted Voting for Replicated Data", SOSP 1979 (Quorum)
- Giuseppe DeCandia et al. — "Dynamo: Amazon's Highly Available Key-value Store", SOSP 2007
- Martin Kleppmann — *Designing Data-Intensive Applications* (2017, O'Reilly)
- ISO/IEC 9075:2016 — *SQL Standard*

**핵심 가치**: 데이터베이스는 *데이터의 영속성·일관성·가용성* 을 동시에 만족시키려는 시도이며, 각 보장은 서로 *상충* 한다. 이 파일의 8 항목은 그 상충 관계를 *정의·정리·증명* 의 언어로 다루며, 패턴([data-modeling](../../../dev-advisor/references/patterns/data-modeling.md))이 "어떻게 만드느냐" 라면 본 문서는 "왜 그 보장이 성립/실패하는가" 의 근거.

**관련 카탈로그**:
- [`../patterns/data-modeling.md`](../../../dev-advisor/references/patterns/data-modeling.md) — 데이터 모델링 / CAP·PACELC 시스템 항목 / Replication 패턴 / Sharding 패턴
- [`./concurrency-theory.md`](../../../dev-advisor/references/principles/concurrency-theory.md) — Linearizability / Serializability / Snapshot Isolation / Causal Consistency / Eventual Consistency
- [`../algorithms/consensus.md`](../../../dev-advisor/references/algorithms/consensus.md) — 2PC / Paxos / Raft (replication 의 합의 기반)
- [`../algorithms/distributed.md`](../../../dev-advisor/references/algorithms/distributed.md) — Lamport / Vector Clock (causal ordering 의 기반)
- [`../patterns/distributed.md`](../../../dev-advisor/references/patterns/distributed.md) — 분산 시스템 패턴 (Saga / Outbox / Read-Through 등)

## 항목 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [tx-isolation-levels](#tx-isolation-levels) | Transaction Isolation Levels | 트랜잭션 격리 4단계 | 높음 |
| [ansi-sql-anomaly](#ansi-sql-anomaly) | ANSI SQL Anomalies | SQL 이상 현상 | 높음 |
| [normalization-1nf-bcnf](#normalization-1nf-bcnf) | Normalization 1NF~5NF | 정규화 | 중간 |
| [acid-vs-base](#acid-vs-base) | ACID vs BASE | ACID vs BASE | 중간 |
| [cap-pacelc](#cap-pacelc) | CAP Theorem & PACELC | CAP 정리 / PACELC | 높음 |
| [db-replication](#db-replication) | Database Replication | DB 복제 | 중간 |
| [consistency-models](#consistency-models) | Consistency Models | 일관성 모델 | 높음 |
| [db-partitioning](#db-partitioning) | Partitioning / Sharding | 파티셔닝 / 샤딩 | 중간 |

---

<a id="tx-isolation-levels"></a>
## 1. 트랜잭션 격리 4단계 (Transaction Isolation Levels)

### 정의
**ANSI/ISO SQL-92** 가 정의한 트랜잭션 *격리 수준(isolation level)* 은 동시 실행되는 트랜잭션이 서로의 중간 상태를 *얼마나 관측할 수 있는가* 의 단계적 약화. 강도가 높을수록 동시성 anomaly 가 제거되지만 처리량 비용이 증가한다.

> "Isolation is the property that determines how/when changes made by one operation become visible to other concurrent operations." — Jim Gray, *Transaction Processing* (1992)

### 표준 4단계

| 수준 (Level) | 한글명 | 차단되는 anomaly | 허용되는 anomaly |
|---|---|---|---|
| **Read Uncommitted** | 무커밋 읽기 | (없음) | Dirty Read, Non-Repeatable Read, Phantom |
| **Read Committed** | 커밋된 읽기 | Dirty Read | Non-Repeatable Read, Phantom |
| **Repeatable Read** | 반복 가능 읽기 | Dirty Read, Non-Repeatable Read | Phantom |
| **Serializable** | 직렬화 가능 | Dirty Read, Non-Repeatable Read, Phantom | (없음) |

Anomaly 의 정의는 [ANSI SQL Anomaly](#ansi-sql-anomaly) 참조.

### Snapshot Isolation (SI) — 확장
SQL-92 에 포함되지 않은 후속 모델. **트랜잭션 시작 시점의 일관된 스냅샷** 을 읽고, 커밋 시 *write-write* 충돌만 검사한다.
- 차단: Dirty Read, Non-Repeatable Read, Phantom
- 허용: **Write Skew** (Read-write 충돌 미검사)
- Berenson et al. (1995) 가 "Repeatable Read 보다 강하지만 Serializable 은 아닌" 별도 단계로 자리매김.

**Serializable Snapshot Isolation (SSI)** — PostgreSQL 9.1+ 의 `SERIALIZABLE` 구현. SI 위에 *dangerous structure* 탐지를 추가하여 write skew 까지 차단. 자세한 정형 정의는 [관련: Snapshot Isolation 이론](../../../dev-advisor/references/principles/concurrency-theory.md#snapshot-isolation) 참조.

### 구현 메커니즘

| 격리 수준 | 일반적 구현 | 예시 DB 기본값 |
|---|---|---|
| Read Uncommitted | No-lock read | (거의 미사용) |
| Read Committed | Row-level lock + statement-level snapshot | **PostgreSQL, Oracle, SQL Server** |
| Repeatable Read | Transaction-level snapshot (MVCC) | **MySQL InnoDB** |
| Snapshot Isolation | MVCC + write-write 충돌 검사 | Oracle, SQL Server (스냅샷 옵션) |
| Serializable | 2PL 또는 SSI | PostgreSQL SSI, SQL Server lock-based |

### 사용 예시 (PostgreSQL)
```sql
BEGIN;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
SELECT balance FROM account WHERE id = 1;
UPDATE account SET balance = balance - 100 WHERE id = 1;
COMMIT;  -- 충돌 시 ERROR: could not serialize access
```

### 정합성 모델 매핑
- Serializable ↔ [관련: Serializability 이론](../../../dev-advisor/references/principles/concurrency-theory.md#serializability)
- Strict Serializable ↔ [관련: Linearizability](../../../dev-advisor/references/principles/concurrency-theory.md#linearizability) (단일 객체 한정)

### 인용
- ANSI SQL-92, §4.28 Transaction isolation levels
- Berenson et al., "A Critique of ANSI SQL Isolation Levels", SIGMOD 1995
- PostgreSQL Documentation §13.2 Transaction Isolation

---

<a id="ansi-sql-anomaly"></a>
## 2. ANSI SQL Anomaly (이상 현상)

### 정의
*동시 트랜잭션 간 가시성(visibility) 위배* 로 인한 일관성 손상. ANSI SQL-92 는 3 가지를 정의했고, 이후 Berenson et al. (1995) 가 *Phantom* 의 정확한 정의와 **Lost Update / Read Skew / Write Skew** 를 추가했다.

### 핵심 메커니즘 — 매트릭스

| Anomaly | 정의 | 시나리오 (T1 / T2) | 허용 격리 수준 |
|---|---|---|---|
| **Dirty Read** (W→R) | 미커밋 데이터 읽기 | T1 write x → T2 read x → T1 rollback | Read Uncommitted |
| **Non-Repeatable Read** (R→W→R) | 동일 행 재읽기 시 값 변경 | T1 read x → T2 write+commit x → T1 read x' | Read Uncommitted, Read Committed |
| **Phantom Read** (R→W new row→R) | 동일 조건 재검색 시 행 집합 변경 | T1 SELECT WHERE p → T2 INSERT WHERE p+commit → T1 재검색 | RU, RC, RR (일부) |
| **Lost Update** | 동시 갱신 중 하나 손실 | T1 read x → T2 read x → T1 write → T2 write | RU, RC |
| **Write Skew** | 서로 다른 행을 읽고 *상호 의존 invariant* 깸 | T1 read y, write x; T2 read x, write y (둘 다 invariant 검사 후 커밋) | SI |
| **Read Skew** | 단일 트랜잭션 내 행 간 비일관 관측 | T1 read x → T2 update x,y +commit → T1 read y | RC |

### 매트릭스 (격리 × Anomaly)

| 격리 수준 | Dirty | NonRepeat | Phantom | Lost Update | Write Skew |
|---|---|---|---|---|---|
| Read Uncommitted | 허용 | 허용 | 허용 | 허용 | 허용 |
| Read Committed | 차단 | 허용 | 허용 | 허용(일부) | 허용 |
| Repeatable Read | 차단 | 차단 | 허용 (Berenson critique) | 차단 (lock 기반) | 허용 |
| Snapshot Isolation | 차단 | 차단 | 차단 | 차단 | **허용** |
| Serializable | 차단 | 차단 | 차단 | 차단 | 차단 |

### Write Skew 예시
의사 검사: "오늘 당직 의사가 최소 1명" invariant. 두 의사 (Alice, Bob) 가 동시에 "다른 의사가 1명 있으니 나는 빠져도 된다" 를 SI 하에서 commit → 0명. SSI 또는 명시적 `SELECT FOR UPDATE` 로 회피.

### 사용 예시 (회피 패턴)
```sql
-- Write skew 회피: 명시적 lock
BEGIN;
SELECT COUNT(*) FROM doctors WHERE on_call = TRUE FOR UPDATE;
UPDATE doctors SET on_call = FALSE WHERE id = :me;
COMMIT;
```

### 비교/대안
- **낙관적 동시성 제어 (OCC)** — SSI 가 사용. 충돌 시 재시도.
- **비관적 잠금 (2PL)** — 전통적 Serializable 구현. 데드락 위험.

### 인용
- Berenson et al., SIGMOD 1995
- Adya, Liskov, O'Neil, ICDE 2000 (Generalized Isolation Level Definitions)
- Kleppmann, *DDIA* Ch. 7

[관련: Concurrency 이론 매핑](../../../dev-advisor/references/principles/concurrency-theory.md#serializability) · [관련: MVCC 알고리즘](../../../dev-advisor/references/algorithms/concurrent.md)

---

<a id="normalization-1nf-bcnf"></a>
## 3. 정규화 1NF ~ BCNF / 4NF / 5NF (Normalization)

### 정의
**E. F. Codd (1970, 1971)** 가 도입한 *함수 종속성(functional dependency)* 기반 *스키마 분해* 절차. 갱신/삽입/삭제 anomaly 를 제거하기 위해 단계적으로 *중복(redundancy)* 을 제거한다. BCNF 는 Codd & Boyce (1974) 가 3NF 의 잔존 anomaly 를 해결하기 위해 강화한 변형.

### 단계별 정의

| 형식 (NF) | 한글명 | 조건 | 해결하는 anomaly |
|---|---|---|---|
| **1NF** | 제1정규형 | 모든 속성이 *원자값(atomic)*. 반복 그룹·다중값 금지 | 다중값으로 인한 검색·갱신 비효율 |
| **2NF** | 제2정규형 | 1NF + *부분 함수 종속(partial dependency)* 제거. 모든 비키 속성이 *후보키 전체* 에 종속 | 복합키 부분 종속 갱신 anomaly |
| **3NF** | 제3정규형 | 2NF + *이행 함수 종속(transitive dependency)* 제거. 비키 속성이 비키 속성에 종속되지 않음 | 이행 종속 갱신 anomaly |
| **BCNF** | Boyce-Codd 정규형 | 모든 함수 종속 `X → Y` 에서 `X` 가 *슈퍼키* | 3NF 의 잔존 (overlapping candidate keys) |
| **4NF** | 제4정규형 | BCNF + *다치 종속(multi-valued dependency)* 제거 | 독립 다치 속성 조합 폭발 |
| **5NF** | 제5정규형 (PJ/NF) | 4NF + *조인 종속(join dependency)* 제거 | 무손실 분해 불가능한 잔존 |

### 핵심 메커니즘

#### 함수 종속 (FD) 표기
`X → Y` : X 의 값이 결정되면 Y 의 값이 유일하게 결정됨.

#### BCNF vs 3NF 차이
3NF 는 *키의 일부에 비키가 종속* 되는 경우를 허용 → overlapping candidate keys 가 있을 때 anomaly 잔존. BCNF 는 이를 차단하지만 *종속성 보존(dependency-preserving)* 이 불가능할 수 있는 trade-off.

| 속성 | 3NF | BCNF |
|---|---|---|
| 무손실 조인 (lossless join) | 보장 | 보장 |
| 종속성 보존 (FD preservation) | 보장 | 불가능할 수 있음 |
| 중복 제거 강도 | 약 | 강 |

### 사용 예시

#### 비정규화 (0NF 유사)
```
Order(order_id, customer_id, customer_name, customer_phone,
      [(product_id, product_name, qty, price), ...])
```

#### 1NF 적용
```
Order(order_id, customer_id, customer_name, customer_phone)
OrderItem(order_id, product_id, product_name, qty, price)
```

#### 3NF 적용 (이행 종속 제거)
```
Order(order_id, customer_id)
Customer(customer_id, name, phone)
OrderItem(order_id, product_id, qty, price)
Product(product_id, name)
```

### Denormalization 결정 매트릭스

정규화의 *역방향*. 읽기 성능·집계 비용을 위해 의도적으로 중복을 도입.

| 시나리오 | 정규화 유지 | 비정규화 권장 |
|---|---|---|
| 쓰기 빈도 ≫ 읽기 빈도 | O | X |
| 읽기 빈도 ≫ 쓰기 빈도 + 조인 비용 큼 | X | O |
| 데이터 일관성 critical (금융·재고) | O | X |
| 분석/리포트용 read replica | X | O (materialized view) |
| 사용자 피드 (read-heavy, eventual OK) | X | O (denorm + CDC) |
| 강한 FK 무결성 필요 | O | X |

### 인용
- Codd, "A Relational Model of Data for Large Shared Data Banks", CACM 1970
- Codd, "Further Normalization of the Data Base Relational Model", IBM Research RJ909, 1971
- Boyce & Codd, IBM Research 1974
- Date, *An Introduction to Database Systems*, 8th ed. (2003)

[관련: 데이터 모델링 패턴](../../../dev-advisor/references/patterns/data-modeling.md) · [관련: 비정규화 시스템 적용](../../../dev-advisor/references/patterns/data-modeling.md#materialized-view)

---

<a id="acid-vs-base"></a>
## 4. ACID vs BASE

### 정의
**ACID** (Härder & Reuter, 1983) 는 전통적 RDBMS 트랜잭션의 4 보장. **BASE** (Pritchett, ACM Queue 2008) 는 분산 NoSQL 의 *완화된 보장* 으로, CAP 정리의 *AP* 선택을 운영적으로 표현한 약어.

### 비교 매트릭스

| 축 | ACID | BASE |
|---|---|---|
| 약어 | Atomicity · Consistency · Isolation · Durability | **B**asically **A**vailable · **S**oft state · **E**ventual consistency |
| 일관성 모델 | Strong (Serializable 또는 SI) | Eventual |
| 가용성 우선순위 | 일관성 > 가용성 | 가용성 > 일관성 |
| 트랜잭션 경계 | 명확 (begin/commit/rollback) | 명시적 트랜잭션 없거나 약함 |
| 대표 시스템 | PostgreSQL, Oracle, MySQL InnoDB | Cassandra, DynamoDB, Riak |
| 적합 도메인 | 금융·재고·결제·인증 | SNS feed, 추천, 로그, IoT, 카운터 |
| 장애 대응 | 트랜잭션 중단 → 사용자 재시도 | partition 중에도 read/write 계속 |

### ACID 4 보장
- **Atomicity** (원자성) — 트랜잭션은 *전부 commit* 되거나 *전부 rollback*. 부분 적용 없음.
- **Consistency** (일관성) — 트랜잭션 후 모든 *integrity constraint* 만족. (CAP 의 C 와 의미가 다름.)
- **Isolation** (격리성) — 동시 트랜잭션이 마치 *직렬 실행* 처럼 보임. 강도는 [Isolation Levels](#tx-isolation-levels) 가 정의.
- **Durability** (영속성) — commit 된 변경은 *crash 후에도* 보존 (WAL + fsync).

### BASE 3 속성
- **Basically Available** — 시스템은 *부분 실패 중에도 응답* (stale data 가능).
- **Soft state** — 클라이언트 input 없이도 *시간에 따라 상태 변경* (TTL, gossip).
- **Eventual consistency** — 입력이 없으면 결국 모든 노드가 동일 상태로 수렴.

### 사용 시나리오

| 시나리오 | 선택 |
|---|---|
| 은행 계좌 이체 | **ACID** (atomic transfer, no lost update) |
| 사용자 timeline / feed | **BASE** (stale OK, 낮은 지연 우선) |
| 재고 차감 (커머스 주문) | **ACID** (overselling 방지) |
| view count / like count | **BASE** (counter convergence) |
| 결제 처리 | **ACID** (commit semantics 필수) |
| 검색 인덱스 (Elasticsearch) | **BASE** (near-realtime, eventual) |
| 분산 트랜잭션 across services | **Saga** (ACID 시뮬레이션) — [관련 패턴](../../../dev-advisor/references/patterns/distributed.md) |

### 비교/대안
- **NewSQL** (Spanner, CockroachDB, YugabyteDB) — ACID 의 강한 일관성을 분산 환경에 확장. PACELC 의 EC (latency 대신 consistency) 선택.
- **Hybrid** (MongoDB 4.0+, DynamoDB transactions) — 단일 partition 내 ACID + 전체적으로 BASE.

### 인용
- Theo Härder, Andreas Reuter — "Principles of Transaction-Oriented Database Recovery", ACM Computing Surveys 15(4), 1983
- Dan Pritchett — "BASE: An Acid Alternative", ACM Queue 6(3), 2008
- Vogels, "Eventually Consistent", CACM 2009

[관련: 일관성 모델 상세](#consistency-models) · [관련: CAP/PACELC](#cap-pacelc) · [관련: 분산 데이터 모델링](../../../dev-advisor/references/patterns/data-modeling.md)

---

<a id="cap-pacelc"></a>
## 5. CAP 정리 & PACELC

### 정의
**CAP 정리** (Brewer 2000, Gilbert-Lynch 2002 증명): 네트워크 *분할(partition)* 이 발생한 분산 시스템은 *Consistency, Availability, Partition Tolerance* 중 **최대 2 개** 만 동시에 만족할 수 있다.

**PACELC** (Abadi 2012): CAP 의 한계 (partition 시 trade-off 만 정의) 를 보완. *분할이 없을 때(Else)* 도 *Latency vs Consistency* 의 trade-off 가 있음을 명시.

### CAP 정의

| 속성 | 의미 |
|---|---|
| **Consistency (C)** | 모든 노드가 *동일 시점에 동일 값* 반환 (≒ Linearizability) |
| **Availability (A)** | 모든 요청이 *유한 시간 내 응답* (실패 응답도 허용 아님) |
| **Partition Tolerance (P)** | 네트워크 *메시지 손실/지연* 에도 시스템 동작 |

### 핵심 메커니즘 — 분할 시 양자택일
실세계에서 *네트워크 분할은 불가피* → P 는 사실상 *주어진 조건*. 따라서 실질적 선택은 **CP vs AP**.

| 분류 | 선택 | 분할 시 동작 |
|---|---|---|
| **CP** | C + P (가용성 포기) | 일부 노드 거절 / blocking |
| **AP** | A + P (일관성 포기) | 모든 노드 응답하지만 stale 가능 |
| CA (이론상) | 분할 없는 단일 노드 / LAN cluster — 실분산에서는 불가능 |

### PACELC 매트릭스

> 분할(P) 시 A 또는 C, **Else(E) 시 L(latency) 또는 C(consistency)**

| 시스템 | P 시 | E 시 | 분류 |
|---|---|---|---|
| **Spanner** | C (CP) | C (EC) | **PC/EC** |
| **CockroachDB** | C | C | PC/EC |
| **PostgreSQL** (single primary) | C | C | PC/EC |
| **Cassandra** | A | L | **PA/EL** |
| **DynamoDB** | A | L | PA/EL |
| **Riak** | A | L | PA/EL |
| **MongoDB** (default) | C | L | PC/EL |
| **HBase** | C | L | PC/EL |

### 사용 예시

#### CP 선택 (Spanner)
```
- TrueTime API (GPS + atomic clock) 로 strict serializability
- partition 시 leader election 중 minority partition 거절
- 사용처: Google Ads 결제, F1 (광고 데이터베이스)
```

#### AP 선택 (Cassandra)
```
- Tunable consistency: R + W > N 으로 quorum 조정
- partition 시 hinted handoff + read repair 로 수렴
- 사용처: Netflix 시청 이력, Instagram timeline
```

### 비교/대안
- **CALM 정리** (Hellerstein 2010) — *monotonic computation* 은 분산에서 coordination 없이 일관성 보장.
- **CRDT** (Shapiro 2011) — eventual consistency 를 *결정론적으로* 수렴시키는 데이터 구조. [관련: 분산 알고리즘](../../../dev-advisor/references/algorithms/distributed.md)

### 인용
- Brewer, "Towards Robust Distributed Systems", PODC 2000 keynote
- Gilbert & Lynch, "Brewer's Conjecture...", SIGACT News 33(2), 2002
- Abadi, "Consistency Tradeoffs...", IEEE Computer 45(2), 2012
- Brewer, "CAP Twelve Years Later: How the Rules Have Changed", IEEE Computer 45(2), 2012

[관련: CAP 시스템 적용](../../../dev-advisor/references/patterns/data-modeling.md#cap-theorem) · [관련: PACELC 적용](../../../dev-advisor/references/patterns/data-modeling.md#pacelc) · [관련: 일관성 모델](#consistency-models)

---

<a id="db-replication"></a>
## 6. 데이터베이스 복제 (Replication)

### 정의
*동일 데이터를 다수 노드에 복사* 하여 (1) 가용성, (2) 읽기 처리량, (3) 지리적 지연 단축, (4) 백업/재해복구 를 확보하는 기법. 토폴로지·동기성·합의 방식에 따라 보장이 달라진다.

### 토폴로지 비교

| 토폴로지 | 한글명 | 쓰기 노드 | 장점 | 단점 |
|---|---|---|---|---|
| **Single-Leader** (Master-Slave) | 단일 리더 | 1 | 단순, strong consistency on leader | 리더 장애 시 failover, write 병목 |
| **Multi-Leader** (Master-Master) | 다중 리더 | N | 지리적 쓰기 분산, 부분 가용성 | 충돌 해결 필요, 인과 위반 가능 |
| **Leaderless** (Quorum) | 무리더 | 모든 노드 | 매우 높은 가용성 | tunable consistency, stale read |

### 동기성 비교

| 모드 | 정의 | 보장 | 장애 영향 |
|---|---|---|---|
| **Synchronous** | leader 가 *모든 follower ack* 후 commit | RPO=0, 강한 일관성 | follower 1 대 장애 시 전체 stall |
| **Asynchronous** | leader 가 *follower ack 없이* commit | RPO>0, eventual | follower 장애 무영향, leader 장애 시 데이터 손실 |
| **Semi-synchronous** | *최소 1 개* follower ack 후 commit | RPO 절충 | 균형 |

### Quorum 시스템 (Gifford 1979)
N 노드, write 시 W 노드 ack, read 시 R 노드 조회.

| 조건 | 보장 |
|---|---|
| `R + W > N` | strong consistency on overlap (read 가 최신 write 본 노드 1개 이상 포함) |
| `W + W > N` | conflict-free write |
| `R = N, W = 1` | 빠른 write / 느린 read |
| `R = 1, W = N` | 빠른 read / 느린 write |
| `R = (N+1)/2, W = (N+1)/2` | balanced quorum (Dynamo 기본) |

### 멀티 리더 충돌 해결
- **Last-Write-Wins (LWW)** — timestamp 기반. 시간 동기화 오차로 데이터 손실 가능.
- **Vector Clock** — causal ordering. concurrent write 는 client/app 이 merge.
- **CRDT** — 결정론적 merge 함수 (counter, set, ORSet).
- **자동 conflict reconciliation** — Riak `siblings`, CouchDB `_conflicts`.

### 사용 예시

| 시스템 | 토폴로지 | 동기성 |
|---|---|---|
| PostgreSQL streaming replication | Single-Leader | sync/async/semi-sync 선택 |
| MySQL Group Replication | Multi-Leader (Paxos) | sync |
| MongoDB replica set | Single-Leader (자동 failover) | semi-sync 가능 |
| Cassandra | Leaderless | tunable (CL.ONE / QUORUM / ALL) |
| DynamoDB Global Tables | Multi-Leader (region) | async + LWW |
| Spanner | Single-Leader per Paxos group | sync (Paxos) |

### 비교/대안
- **합의 알고리즘 (Paxos/Raft)** — 단일 리더 선출 + log replication 의 정확성 보장. [관련: 합의 알고리즘](../../../dev-advisor/references/algorithms/consensus.md)
- **Chain Replication** (van Renesse 2004) — 노드를 체인으로 묶어 sync replication 의 throughput 개선.
- **State Machine Replication (SMR)** — 결정론적 명령 시퀀스 복제. Raft 가 대표.

### 인용
- Gifford, "Weighted Voting for Replicated Data", SOSP 1979
- DeCandia et al., "Dynamo", SOSP 2007
- Diego Ongaro, John Ousterhout — "In Search of an Understandable Consensus Algorithm" (Raft), USENIX ATC 2014
- Kleppmann, *DDIA* Ch. 5

[관련: Single-Leader 패턴](../../../dev-advisor/references/patterns/data-modeling.md#single-leader-replication) · [관련: Multi-Leader 패턴](../../../dev-advisor/references/patterns/data-modeling.md#multi-leader-replication) · [관련: Leaderless](../../../dev-advisor/references/patterns/data-modeling.md#leaderless-replication) · [관련: 분산 패턴](../../../dev-advisor/references/patterns/distributed.md)

---

<a id="consistency-models"></a>
## 7. 일관성 모델 (Consistency Models)

### 정의
*분산/복제 데이터에 대한 관측 보장* 을 형식적으로 정의한 계층. *강도(strength)* 순서가 있으며, 강한 모델은 약한 모델을 함의(imply)한다.

### 강도 순서 (Strong → Weak)

```
Linearizability (≈ Strict Serializable for single-object)
       │
       ▼
Sequential Consistency
       │
       ▼
Causal Consistency  ←─ Read-Your-Writes + Monotonic Reads + Monotonic Writes + Writes-Follow-Reads (합쳐서 PRAM/Session)
       │
       ▼
Eventual Consistency
```

### 모델 비교 매트릭스

| 모델 | 정의 | 클라이언트 보장 | 구현 비용 | 대표 시스템 |
|---|---|---|---|---|
| **Linearizability** | 모든 연산이 *실시간 순서* 에 일치하는 직렬 history 존재 | 가장 강함 (real-time) | 매우 높음 (consensus) | Spanner, etcd, ZooKeeper |
| **Sequential Consistency** | 모든 노드가 *동일 순서* 관측 (실시간 무관) | 강함 | 높음 | (이론적; 분산 메모리) |
| **Causal Consistency** | *인과 관계 (happens-before)* 보존, 동시(concurrent) 연산은 임의 순서 | 중간 (인과 보존) | 중간 (vector clock) | COPS, AntidoteDB |
| **Read-Your-Writes** | 자신이 *방금 쓴 값* 을 자신이 읽을 때 반드시 관측 | 세션 보장 | 낮음 (sticky session) | 대부분 BASE 시스템에서 옵션 |
| **Monotonic Reads** | *시간을 거슬러 읽지 않음* (한번 본 값보다 옛 값 안 봄) | 세션 보장 | 낮음 | Cassandra (per-client) |
| **Monotonic Writes** | 동일 클라이언트 write 가 *순서대로* 적용 | 세션 보장 | 낮음 | (대부분 보장) |
| **Eventual Consistency** | 입력이 멈추면 *결국* 모든 노드 수렴 | 매우 약함 | 매우 낮음 | DynamoDB, Cassandra (default) |

### 핵심 메커니즘

#### Causal Consistency 가 *concurrent* 를 허용
- Alice write A → Bob read A → Bob write B  ⟹  `A happens-before B`, 모든 노드가 A 다음 B 순서로 관측해야 함.
- Carol write C (concurrent with A) ⟹  순서 자유.

#### Session 보장 4 종 (Terry et al. 1994, Bayou)
- **Read-Your-Writes (RYW)**
- **Monotonic Reads (MR)**
- **Monotonic Writes (MW)**
- **Writes-Follow-Reads (WFR)**

이 4 개를 모두 만족하면 **PRAM** (Pipelined RAM) consistency 또는 **session consistency** 라 부른다.

### 사용 시나리오

| 시나리오 | 권장 모델 |
|---|---|
| 분산 락 / 리더 선출 | Linearizability |
| 은행 계좌 잔액 조회 | Linearizability (또는 strict serializable) |
| 소셜 댓글 (원인 댓글 → 답글) | Causal |
| 사용자 본인 프로필 수정 후 본인 조회 | Read-Your-Writes |
| timeline scroll (페이지 넘김) | Monotonic Reads |
| 좋아요 카운트 | Eventual |

### 정합성 매핑 (격리 수준과의 관계)
- DB 의 *Serializable isolation* + 분산 시스템의 *Linearizability* = **Strict Serializability** (가장 강한 보장).
- Snapshot Isolation 은 일반적으로 *non-linearizable* (역행 read 가능).

### 비교/대안
- **CRDT** — eventual consistency 시스템이 *결정론적 수렴* 을 보장하도록 데이터 구조 자체에 merge 가환성 부여.
- **Bounded Staleness** — Cosmos DB / Azure Tables. "최대 K 버전 또는 T 시간 지연" 명시.

### 인용
- Herlihy & Wing, "Linearizability...", TOPLAS 1990
- Lamport, "How to Make a Multiprocessor...", IEEE TC 1979 (Sequential Consistency)
- Ahamad et al., "Causal Memory...", Distributed Computing 1995
- Doug Terry et al., "Session Guarantees for Weakly Consistent Replicated Data", PDIS 1994
- Vogels, "Eventually Consistent", CACM 2009

[관련: Linearizability 이론](../../../dev-advisor/references/principles/concurrency-theory.md#linearizability) · [관련: Causal Consistency 이론](../../../dev-advisor/references/principles/concurrency-theory.md#causal-consistency) · [관련: Eventual Consistency 이론](../../../dev-advisor/references/principles/concurrency-theory.md#eventual-consistency) · [관련: 시스템 적용 매핑](../../../dev-advisor/references/patterns/data-modeling.md#consistency-models-systems)

---

<a id="db-partitioning"></a>
## 8. 파티셔닝 / 샤딩 (Partitioning / Sharding)

### 정의
단일 노드의 *저장 용량·CPU·I/O 한계* 를 넘어서기 위해 데이터를 *수평 분할(horizontal partition)* 하여 다수 노드에 분산. *Sharding* 은 분산 DB 맥락의 partition 동의어 (Google Spanner / MongoDB 용어).

### 파티셔닝 전략

| 전략 | 한글명 | 키 매핑 | 장점 | 단점 |
|---|---|---|---|---|
| **Range Partitioning** | 범위 파티셔닝 | 키 범위 → 파티션 (e.g. A-F, G-M, ...) | 범위 스캔 효율, 정렬 유지 | hotspot (e.g. 최신 timestamp 만 쓰임) |
| **Hash Partitioning** | 해시 파티셔닝 | `hash(key) mod N` | 균일 분포 | 범위 쿼리 비효율 |
| **Consistent Hashing** | 일관성 해시 | 키·노드를 *원형 hash ring* 매핑 | 노드 추가/삭제 시 *재배치 최소* | 부하 불균형 (가상 노드로 완화) |
| **Directory-based** | 디렉터리 기반 | lookup table (key → partition id) | 임의 분할 정책 가능 | lookup 비용, 디렉터리 가용성 critical |
| **Composite** | 복합 | (range + hash) e.g. range on user_id, hash on time | 다축 분산 | 복잡도 |

### Range Partitioning 예시
```
shard_1: user_id A-F   shard_2: user_id G-M   shard_3: user_id N-S   shard_4: user_id T-Z
```

### Hash + Virtual Nodes (Dynamo style)
```
ring = hash 공간 (0 ~ 2^160 - 1)
각 물리 노드 → V 개 가상 노드 (V ≈ 100~256) → 균일성 향상
키 K 의 소속: hash(K) 이후 시계방향 첫 노드
```

### Resharding 전략

| 전략 | 메커니즘 | 다운타임 | 복잡도 |
|---|---|---|---|
| **Fixed number of partitions** | partition 수 고정, 노드 간 partition 이동만 | 낮음 | 낮음 (Couchbase, Riak) |
| **Dynamic partitioning** | partition 이 너무 커지면 split, 작으면 merge | 낮음 | 중간 (HBase, MongoDB) |
| **Hash-mod resharding** | `hash mod N` → N 변경 시 *대규모 재배치* (`N-1/N` 키 이동) | 높음 | 낮음 (구식, 피해야 함) |
| **Consistent hashing** | 노드 추가 시 *기존 노드 1 개의 일부 키* 만 이동 | 낮음 | 중간 (Dynamo, Cassandra) |
| **Online migration (split-merge)** | 트래픽 라이브 상태에서 점진적 이전 | 낮음 | 매우 높음 (Vitess, Spanner) |

### 보조 인덱스 (Secondary Indexes)

| 방식 | 정의 | trade-off |
|---|---|---|
| **Local index (document-partitioned)** | 각 partition 이 *자기 데이터의 인덱스만* 보유 | write 단순, read 시 scatter-gather |
| **Global index (term-partitioned)** | 인덱스를 별도 partition (term 기준) 으로 분할 | read 효율, write 시 분산 트랜잭션 |

### 사용 예시

| 시스템 | 전략 | 비고 |
|---|---|---|
| MongoDB | Range / Hash 선택 | `sh.shardCollection(..., { _id: "hashed" })` |
| Cassandra | Consistent Hashing (vnodes) | partition key + clustering key |
| DynamoDB | Hash on partition key | partition key 설계 중요 (hot partition 회피) |
| Vitess (YouTube) | Range + online resharding | MySQL 기반 |
| HBase | Range (region) + dynamic split | row key 설계 |
| Elasticsearch | Hash on `_routing` | shard 수는 인덱스 생성 시 고정 |

### 비교/대안
- **수직 분할 (Vertical Partitioning)** — 컬럼 또는 사용 빈도에 따라 별도 테이블. 수평 sharding 과 직교.
- **Functional Sharding** — 도메인별로 별개 DB (e.g. user DB / order DB / inventory DB). 마이크로서비스의 데이터 분리.

### 인용
- David Karger et al., "Consistent Hashing and Random Trees", STOC 1997
- DeCandia et al., "Dynamo", SOSP 2007
- Kleppmann, *DDIA* Ch. 6
- Google, "Spanner: Google's Globally-Distributed Database", OSDI 2012

[관련: Sharding 패턴 적용](../../../dev-advisor/references/patterns/data-modeling.md#sharding-partitioning) · [관련: Consistent Hashing 패턴](../../../dev-advisor/references/patterns/data-modeling.md#consistent-hashing-sharding) · [관련: 분산 알고리즘](../../../dev-advisor/references/algorithms/distributed.md) · [관련: 분산 시스템 패턴](../../../dev-advisor/references/patterns/distributed.md)

---

## 부록: 카탈로그 매핑

| 본 문서 항목 | 시스템 적용 | 알고리즘 기반 |
|---|---|---|
| Isolation Levels | (격리 수준은 DB 엔진별 설정) | MVCC, 2PL ([../algorithms/concurrent.md](../../../dev-advisor/references/algorithms/concurrent.md)) |
| ANSI SQL Anomaly | (위와 동일) | Snapshot Isolation ([./concurrency-theory.md#snapshot-isolation](../../../dev-advisor/references/principles/concurrency-theory.md#snapshot-isolation)) |
| Normalization | [../patterns/data-modeling.md](../../../dev-advisor/references/patterns/data-modeling.md) | — |
| ACID vs BASE | [../patterns/data-modeling.md](../../../dev-advisor/references/patterns/data-modeling.md), [../patterns/distributed.md](../../../dev-advisor/references/patterns/distributed.md) | — |
| CAP / PACELC | [../patterns/data-modeling.md#cap-theorem](../../../dev-advisor/references/patterns/data-modeling.md#cap-theorem), [../patterns/data-modeling.md#pacelc](../../../dev-advisor/references/patterns/data-modeling.md#pacelc) | — |
| Replication | [../patterns/data-modeling.md#single-leader-replication](../../../dev-advisor/references/patterns/data-modeling.md#single-leader-replication) 외 2 | Paxos / Raft ([../algorithms/consensus.md](../../../dev-advisor/references/algorithms/consensus.md)) |
| Consistency Models | [../patterns/data-modeling.md#consistency-models-systems](../../../dev-advisor/references/patterns/data-modeling.md#consistency-models-systems) | Linearizability / Causal ([./concurrency-theory.md](../../../dev-advisor/references/principles/concurrency-theory.md)) |
| Partitioning | [../patterns/data-modeling.md#sharding-partitioning](../../../dev-advisor/references/patterns/data-modeling.md#sharding-partitioning), [../patterns/data-modeling.md#consistent-hashing-sharding](../../../dev-advisor/references/patterns/data-modeling.md#consistent-hashing-sharding) | Consistent Hashing ([../algorithms/distributed.md](../../../dev-advisor/references/algorithms/distributed.md)) |

---

**관련 (P1 신설)**:
- [`../patterns/data-warehousing-bi.md`](../patterns/data-warehousing.md) — OLTP/ACID 원리의 OLAP 측면 — Kimball Star / SCD / Lakehouse / dbt 으로 분석 워크로드의 일관성 모델 결정 (Snapshot Isolation, Idempotent Materialization)

---

**문서 끝**. *원리* 가 흔들리면 *패턴* 도 무너지며, 결국 *시스템 보장* 의 거짓 광고로 이어진다 — 본 8 항목을 *증명의 언어* 로 다룰 때 비로소 트랜잭션·복제·파티셔닝의 trade-off 가 합의 가능한 설계 결정으로 환원된다.
