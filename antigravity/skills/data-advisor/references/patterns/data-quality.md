# 데이터 품질·거버넌스 패턴 (Data Quality & Governance Patterns)

DAMA-DMBOK 2 *Data Management Body of Knowledge* (2017) Knowledge Area 10 (**Data Quality**) 와 ISO/IEC 25012:2008 *Software product Quality Requirements and Evaluation — Data quality model* 을 양대 표준으로 한다. 데이터 자산(asset)을 신뢰 가능한 의사결정·운영·AI/ML 파이프라인 입력으로 유지하기 위한 측정·추적·관리·검증 패턴 모음. Master Data Management(MDM)·Reference Data 가 *값* 의 단일 원천을 다룬다면, 본 카탈로그는 *값의 정확도·완전성·신뢰* 의 단일 원천을 다룬다(`patterns/master-data-management.md` cross-link).

데이터 품질 6 차원(6 Dimensions)·계보(Lineage)·카탈로그(Catalog)·스튜어드십(Stewardship)·OpenLineage 표준·검증 도구 매트릭스 6 anchor 로 구성된다. ISO/IEC 25012 의 15 특성과 DAMA-DMBOK 의 차원은 일부 중복되며, 산업 현장에서는 DAMA 6 차원을 default 로 채택하고 ISO 의 inherent/system-dependent 분류로 보강한다.

---

## 1. DQ 6 Dimensions (데이터 품질 6 차원)

<a id="dq-6-dimensions"></a>

**목적**: 데이터 품질을 측정 가능한 6 개 축으로 분해해 SLA·SLO 화한다. DAMA-DMBOK 2 KA10 *Data Quality* 의 표준 6 차원 정의(Accuracy / Completeness / Consistency / Timeliness / Validity / Uniqueness). ISO/IEC 25012 의 15 특성 중 inherent data quality 와 매핑된다(Accuracy↔Accuracy, Completeness↔Completeness, Consistency↔Consistency, Currentness↔Timeliness, Credibility↔Validity 보강).

**6 차원 × 측정 방법 × 도구 매트릭스**:

| 차원 (Dimension) | 정의 (Definition) | 측정 방법 (Measurement) | 임계값 예 | 대표 도구 |
|---|---|---|---|---|
| **Accuracy** (정확성) | 데이터가 실세계(real-world entity)를 정확히 반영하는 정도 | 표본 추출 후 신뢰 가능한 source-of-truth 와 비교(record-by-record reconciliation) → `accurate_count / total_count` | ≥ 99.0% | Great Expectations `expect_column_values_to_match_regex` / Soda `valid` / 수동 audit |
| **Completeness** (완전성) | 필수 필드/레코드가 누락 없이 채워진 정도 | `non_null_count / total_count` × 100, mandatory column missing rate | NULL ≤ 0.5% (PII), ≤ 5% (optional) | `expect_column_values_to_not_be_null` / dbt `not_null` test |
| **Consistency** (일관성) | 동일 사실이 시스템 간·시점 간 동일 표현 유지 | cross-system reconciliation, FK 무결성, 동기화 lag | violation = 0 | Soda `consistency check` / dbt `relationships` / cross-DB reconcile job |
| **Timeliness** (적시성) | 데이터가 사용 시점에 충분히 최신인지 | `current_ts - last_updated_ts` ≤ SLA, freshness delta | dashboard ≤ 1h, realtime ≤ 30s | Monte Carlo freshness monitor / `dbt source freshness` / Airflow SLA |
| **Validity** (유효성) | 정의된 형식·범위·도메인 규칙 준수 | regex / enum / range check 통과율(`valid_count / total_count`) | ≥ 99.5% | `expect_column_values_to_be_in_set` / Soda `valid_min/max` / JSON Schema |
| **Uniqueness** (유일성) | PK/business key 가 중복되지 않음 | `distinct_count / total_count` = 1, duplicate group count | duplicate = 0 | `expect_column_values_to_be_unique` / dbt `unique` / Anomalo |

**6 차원 추가 보강**:
- **Integrity** (무결성, ISO/IEC 25012): FK·CHECK 제약 위반 0 — Consistency 의 RDB 측면
- **Conformity / Standardization**: 코드 체계·단위 표준 준수 (예: ISO 4217 통화, ISO 3166 국가) — Validity 의 표준 측면
- **Reasonableness** (합리성): 통계적 outlier 탐지 (mean ± 3σ, z-score) — Anomalo / Monte Carlo ML 기반

**장점**:
- DQ SLA/SLO 정량화 가능 (예: "주문 테이블 Completeness ≥ 99.5% / Timeliness ≤ 5min")
- 차원별 owner·도구 매핑 명확 (RACI 와 결합 시 `dq-stewardship-raci`)
- ISO/IEC 25012 인증·감사 대응 추적 가능

**단점**:
- 차원 간 trade-off (Timeliness ↑ → Accuracy 검증 시간 ↓)
- Accuracy 는 외부 source-of-truth 필요 → 비용 ↑
- 비즈니스 맥락 의존적 임계값 — domain steward 합의 필수

**활용 예시**:
- 금융 KYC 데이터: Accuracy 99.9% / Completeness 100% / Validity 100%
- 마케팅 캠페인 데이터: Completeness 95% / Timeliness 1h 허용 (Accuracy 는 trade-off)
- AI/ML 학습셋: Uniqueness + Validity 가 모델 정확도와 직결 (data-centric AI)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**SQL 측정 예제 (Kotlin/JVM 기반 BigQuery)**:
```sql
-- Completeness: NULL 비율
SELECT
  COUNT(*) AS total,
  COUNTIF(email IS NULL) AS null_email,
  SAFE_DIVIDE(COUNTIF(email IS NOT NULL), COUNT(*)) AS completeness
FROM `prod.users`;

-- Validity: 이메일 regex 통과율
SELECT SAFE_DIVIDE(
  COUNTIF(REGEXP_CONTAINS(email, r'^[\w.+-]+@[\w-]+\.[\w.-]+$')),
  COUNT(*)
) AS validity
FROM `prod.users` WHERE email IS NOT NULL;

-- Uniqueness: PK 중복
SELECT user_id, COUNT(*) AS dup
FROM `prod.users` GROUP BY user_id HAVING dup > 1;

-- Timeliness: freshness lag
SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(updated_at), MINUTE) AS lag_min
FROM `prod.users`;
```

**관련 패턴**: `dq-validation-tools`(도구 매트릭스), `dq-stewardship-raci`(차원별 owner), `patterns/master-data-management.md#golden-record`(MDM Survivorship 의 정확도 차원)

**Cross-link**:
- `principles/database-fundamentals.md#acid`(Consistency 차원의 ACID Consistency 와 구분)
- ISO/IEC 25012:2008 inherent vs system-dependent quality
- DAMA-DMBOK 2 KA10 *Data Quality* (Mosley et al., 2017)

---

## 2. Data Lineage (데이터 계보)

<a id="data-lineage"></a>

**목적**: 데이터의 origin → transformation → destination 경로를 추적해 impact analysis(영향 범위 분석), root cause analysis(원인 추적), 규제 보고(GDPR Article 30 처리 기록, SOX 감사 추적)를 지원한다. Wang & Madnick *Polygen Model* (1990) 에서 출발해 OpenLineage / OpenMetadata 시대에 표준화되었다.

**4 단계 + 2 관점 분류**:

| 구분 | 정의 | 추적 단위 | 도구 예 |
|---|---|---|---|
| **Upstream Lineage** | 현재 데이터가 어디서 왔는가 (source → here) | 원본 시스템, 추출 시각, 변환 규칙 | Marquez backward trace |
| **Downstream Lineage** | 이 데이터가 어디로 흘러가는가 (here → consumer) | 후속 테이블/대시보드/ML 모델 | OpenMetadata forward trace |
| **Column-level (Field-level) Lineage** | 컬럼/필드 단위의 derivation 추적 | `users.email` → `mart.user_summary.email_domain` 변환식 | dbt `--column-lineage`, Astronomer Cosmos |
| **Table/Dataset-level Lineage** | 테이블·데이터셋 단위 의존성 그래프 | DAG of tables/datasets | Airflow DAG, dbt manifest |
| **Operational Lineage** | 어떤 job/run 이 어떤 데이터를 만들었나 (실행 instance 단위) | run_id, job_id, started_at, ended_at | OpenLineage RunEvent |
| **Business Lineage** | 비즈니스 용어(BI metric) → 물리적 데이터 매핑 | KPI "MAU" → `mart.fact_login` source | OpenMetadata Glossary |

**Lineage 수집 방식**:
- **Code parsing**: SQL parser (sqlparse, ZetaSQL) 로 SELECT 의 source/dest 추출
- **Log parsing**: query log / Spark event log 분석
- **Instrumentation**: dbt / Spark / Airflow 가 OpenLineage 이벤트 emit (push 방식)
- **Crawling**: catalog crawler 가 정기 스캔 (pull 방식, `data-catalog` 의 passive metadata)

**장점**:
- Impact analysis: "이 컬럼 스키마 변경 시 영향받는 dashboard 12 개" 즉시 파악
- Incident triage: "어제 매출 지표 이상 → upstream `orders` 테이블 ETL 실패" 5 분 내 추적
- GDPR/CCPA 권리 행사 대응: 개인정보가 거쳐간 모든 시스템 추적

**단점**:
- Stored procedure / dynamic SQL / Python pandas 파이프라인은 자동 추출 어려움 (수동 보완 필요)
- Column-level lineage 는 메타데이터 폭증 (테이블당 수십~수백 컬럼 × DAG node 수천)
- Real-time stream lineage 는 표준화 미성숙 (Flink·Kafka 측 OpenLineage 통합 진행 중)

**활용 예시**:
- 금융권 BCBS 239 (Risk Data Aggregation) 규제 대응
- AI/ML feature store: feature 가 어떤 raw 데이터에서 파생됐는지 추적 → 학습/추론 일관성
- Schema migration: deprecated 컬럼 영향 범위 자동 분석

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**관련 패턴**: `openlineage-standard`(표준 사양), `data-catalog`(lineage 저장소), `dq-stewardship-raci`(lineage steward)

**Cross-link**:
- `patterns/master-data-management.md#golden-record-survivorship`(survivorship rule 도 lineage 의 일종)
- `principles/database-fundamentals.md#replication`(replication topology = physical lineage)

---

## 3. Data Catalog (데이터 카탈로그)

<a id="data-catalog"></a>

**목적**: 조직 내 모든 데이터 자산(테이블·dashboard·ML model·pipeline)의 메타데이터를 중앙 인벤토리화하고 검색·발견(discovery)·이해(understanding)·신뢰(trust)·협업(collaboration)의 5 가지 capability 를 제공한다. Gartner *Data and Analytics Trends* (2019~) 의 핵심 카테고리.

**Active vs Passive Metadata** (Gartner 분류):

| 구분 | Passive Metadata | Active Metadata |
|---|---|---|
| 수집 | crawler 가 주기적 스캔 (pull) | event-driven push (OpenLineage / pipeline hook) |
| 갱신 | 일 1회~주 1회 | near-realtime (< 1 min) |
| 내용 | schema, owner, tag (정적) | query usage, lineage, freshness, anomaly, popularity (동적·행위 기반) |
| 활용 | 검색·문서화 | 자동화·추천·anomaly 알림·governance |
| 도구 예 | Apache Atlas, Amundsen v1 | DataHub, OpenMetadata, Atlan, Collibra v3 |

**3 핵심 컴포넌트**:

1. **Crawler / Connector**
   - 메타데이터 ingest: Snowflake / BigQuery / Redshift / Kafka / Tableau / Looker 등 connector 수십 개
   - Schema, table stats, column stats, owner, tag 수집
   - JDBC `INFORMATION_SCHEMA`, Spark Catalog API, BigQuery `__TABLES__`, Snowflake `ACCOUNT_USAGE`

2. **Profiler**
   - Column 단위 통계: min/max/null %/distinct count/histogram
   - Sample value (PII 마스킹 적용)
   - 자동 PII 탐지 (regex / ML classifier — 주민번호, 이메일, 카드번호)

3. **Search / Discovery UI**
   - Elasticsearch / OpenSearch 기반 fuzzy search
   - Faceted filter (domain, owner, tag, freshness)
   - Glossary / Wiki / Q&A (Slack-bot 통합)

**장점**:
- "이 데이터가 있긴 있나?" / "누구한테 물어봐야 하나?" 해소 (data discovery)
- 자산 owner / tier(Gold·Silver·Bronze) / SLA 명시 (trust)
- ROI: 데이터 분석가가 데이터 찾는 데 쓰는 시간 30%+ 단축 (Forrester 2022)

**단점**:
- 초기 ingest + 지속 유지 비용 (자산 수천~수십만 개)
- 메타데이터 freshness 자체가 DQ 문제로 회귀 (catalog 도 데이터다)
- 자동 PII 탐지 false positive/negative → 수동 검토 필요

**활용 예시**:
- Lyft Amundsen (오픈소스 시초, 2019)
- LinkedIn DataHub (active metadata 표준)
- Airbnb Dataportal (글꼴/wiki 통합형)

**난이도**: 중간~높음 | **사용 빈도**: ★★★★☆

**관련 패턴**: `data-lineage`(catalog 의 핵심 capability), `dq-stewardship-raci`(catalog 의 owner 필드)

**Cross-link**:
- `patterns/master-data-management.md#reference-data`(reference data 도 catalog 의 한 카테고리)
- DAMA-DMBOK 2 KA12 *Metadata Management*

---

## 4. Stewardship RACI (데이터 스튜어드십 RACI)

<a id="dq-stewardship-raci"></a>

**목적**: 데이터 자산별 책임·권한을 RACI 매트릭스(Responsible / Accountable / Consulted / Informed)로 명시해 "누가 결정·실행·승인하는가" 모호성을 제거한다. DAMA-DMBOK 2 KA1 *Data Governance* 의 핵심 패턴. ISO/IEC 38505-1 (Data Governance) 와 정렬.

**4 역할 + RACI 매핑**:

| 역할 | 정의 | 책임 범위 | DAMA 매핑 |
|---|---|---|---|
| **Data Owner** | 비즈니스 의사결정권자, 자산의 가치/위험 최종 책임 | 자산 등급, 접근 정책 승인, DQ SLA 합의 | Data Owner / Trustee |
| **Data Custodian** | 기술적 보관자, 시스템 운영 책임 | 백업/복구, 접근 제어 구현, 인프라 운영 | Data Custodian (IT 측) |
| **Data Steward** | 도메인 전문가, 데이터 의미·품질 일상 관리 | 표준 정의, DQ 측정, 이슈 triage, glossary 관리 | Business / Technical Steward |
| **Data Producer** | 데이터를 생성·수집하는 시스템·팀 | source 정확도, 스키마 변경 communication | Data Originator |
| **Data Consumer** | 데이터를 사용하는 분석가·ML 엔지니어·app | 사용 목적 명시, 이슈 피드백 | Information Consumer |

**RACI 매트릭스 예 (Customer 데이터)**:

| 활동 | Owner (CMO) | Steward (Marketing Analyst) | Custodian (DataPlatform) | Producer (CRM Team) | Consumer (BI) |
|---|---|---|---|---|---|
| DQ SLA 정의 | **A** | **R** | C | C | C |
| Schema 변경 승인 | **A** | C | **R** | C | I |
| Access Policy | **A** | C | **R** | I | I |
| DQ 이슈 triage | I | **A/R** | C | C | I |
| Incident 통보 | I | I | **R** | I | **A** |
| Glossary 정의 | C | **A/R** | I | I | C |

R = Responsible (실행), A = Accountable (최종 책임, 1인), C = Consulted, I = Informed

**Data Domain → Steward 매핑 예**:
- Customer domain → Marketing Analytics Steward
- Product domain → Catalog Manager Steward
- Finance domain → FP&A Steward
- HR domain → HR BP Steward

**장점**:
- "데이터 문제 → 누구한테?" 해소 (incident MTTR 단축)
- 의사결정 추적 가능 (audit trail)
- DQ SLA 와 owner 결합 시 책임 명확

**단점**:
- 조직 변경 시 RACI 재정의 부담
- Accountable 1인 원칙 violation 빈번 (실제로 "공동 책임" 으로 흐려짐)
- Steward 의 시간 25%+ 확보 필요 → 인력 투입 정당화 어려움

**활용 예시**:
- 금융 BCBS 239 / SOX 데이터 governance 보고
- GDPR Article 24 Controller / 28 Processor 매핑
- 의료 HIPAA Privacy Officer 역할 (Custodian 의 특수형)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**관련 패턴**: `dq-6-dimensions`(각 차원의 owner = steward), `data-catalog`(owner/steward 필드 저장), `patterns/master-data-management.md#mdm-steward`(MDM steward 와 통합)

**Cross-link**:
- DAMA-DMBOK 2 KA1 *Data Governance* RACI 템플릿
- ISO/IEC 38505-1:2017 *Governance of data*
- `principles/database-fundamentals.md`(custodian 의 기술 책임 영역)

---

## 5. OpenLineage Standard (OpenLineage 표준)

<a id="openlineage-standard"></a>

**목적**: 데이터 파이프라인 lineage 를 vendor-neutral 표준 이벤트 모델로 정의해 dbt·Airflow·Spark·Flink 등 이종 도구 간 lineage 통합을 가능케 한다. Linux Foundation AI & Data 산하 프로젝트 (2021~), spec v1.x. 출발은 Marquez(WeWork, 2018) 의 모델을 표준화한 것이다.

**핵심 객체 모델**:

```
RunEvent
├── eventType: START | RUNNING | COMPLETE | ABORT | FAIL
├── eventTime: ISO-8601 timestamp
├── run: { runId: UUID, facets: {...} }
├── job: { namespace, name, facets: {...} }
├── inputs: [ Dataset, ... ]      // 이 run 이 읽은 데이터셋
├── outputs: [ Dataset, ... ]     // 이 run 이 쓴 데이터셋
└── producer: URI (OL emitter)

Dataset
├── namespace (예: "bigquery://project")
├── name (예: "dataset.table")
└── facets: { schema, dataSource, columnLineage, dataQualityMetrics, ... }
```

**3 핵심 이벤트 유형**:
1. **Job**: 정의(어떤 변환을 하는가, 코드 SHA, SQL)
2. **Run**: 실행 인스턴스(언제, 얼마나 걸렸나, 성공/실패)
3. **Dataset**: 입출력 데이터셋(어떤 테이블/파일/스트림)

**Facet 시스템** (확장 가능 metadata):
- `schema`: 컬럼 목록·타입
- `columnLineage`: 컬럼-수준 derivation
- `dataQualityMetrics`: row count, null rate, distinct count
- `dataQualityAssertions`: Great Expectations / dbt test 결과
- `ownership`: dataset owner
- `dataSource`: connection 정보

**RunEvent JSON 예 1 (dbt 모델 실행 완료)**:
```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-05-16T12:34:56.789Z",
  "producer": "https://github.com/OpenLineage/OpenLineage/tree/1.18.0/integration/dbt",
  "run": {
    "runId": "3f5e1a2b-7c8d-4e9f-a012-b34567890abc",
    "facets": {
      "nominalTime": { "nominalStartTime": "2026-05-16T12:30:00Z" }
    }
  },
  "job": {
    "namespace": "dbt-prod",
    "name": "marketing.user_summary",
    "facets": {
      "sql": { "query": "SELECT user_id, COUNT(*) FROM events GROUP BY 1" }
    }
  },
  "inputs": [{
    "namespace": "bigquery://acme-prod",
    "name": "raw.events",
    "facets": {
      "schema": {
        "fields": [
          { "name": "user_id", "type": "STRING" },
          { "name": "event_ts", "type": "TIMESTAMP" }
        ]
      }
    }
  }],
  "outputs": [{
    "namespace": "bigquery://acme-prod",
    "name": "marketing.user_summary",
    "facets": {
      "columnLineage": {
        "fields": {
          "user_id": {
            "inputFields": [
              { "namespace": "bigquery://acme-prod", "name": "raw.events", "field": "user_id" }
            ]
          }
        }
      }
    }
  }]
}
```

**RunEvent JSON 예 2 (Great Expectations 검증 결과 facet)**:
```json
{
  "eventType": "COMPLETE",
  "run": { "runId": "9a8b7c6d-1e2f-3a4b-5c6d-7e8f9a0b1c2d" },
  "job": { "namespace": "ge-prod", "name": "users_validation" },
  "outputs": [{
    "namespace": "bigquery://acme-prod",
    "name": "prod.users",
    "facets": {
      "dataQualityAssertions": {
        "assertions": [
          { "assertion": "expect_column_values_to_not_be_null", "column": "email", "success": true },
          { "assertion": "expect_column_values_to_be_unique", "column": "user_id", "success": true },
          { "assertion": "expect_column_values_to_match_regex", "column": "email", "success": false }
        ]
      },
      "dataQualityMetrics": {
        "rowCount": 1842301,
        "columnMetrics": {
          "email": { "nullCount": 0, "distinctCount": 1842301 }
        }
      }
    }
  }]
}
```

**대표 구현체**:

| 도구 | 역할 | 특징 |
|---|---|---|
| **Marquez** | OpenLineage 의 reference backend | 그래프 DB, REST API, UI |
| **OpenMetadata** | 통합 catalog + lineage + quality | Active metadata, full-stack |
| **DataHub** | LinkedIn 의 metadata 플랫폼 | OpenLineage emitter 지원 |
| **Atlan / Collibra** | 상용 enterprise catalog | OpenLineage ingestion 지원 |

**장점**:
- Vendor lock-in 회피, 이종 도구 lineage 통합
- 표준 JSON → 분석 도구 자유 선택 (Marquez / DataHub / 자체 분석)
- dbt / Airflow / Spark / Flink 공식 integration 존재

**단점**:
- v1.x 는 still evolving, column-lineage facet 은 일부 producer 만 emit
- Streaming(Flink, Kafka) 통합 미성숙
- 자체 코드(Python pandas, custom ETL)는 manual emitter 작성 필요

**활용 예시**:
- dbt-core `dbt-ol` 플러그인으로 자동 lineage emit
- Airflow `openlineage-airflow` provider 로 DAG 자동 추적
- Spark `OpenLineageSparkListener` 로 job 자동 추적

**난이도**: 높음 | **사용 빈도**: ★★★☆☆ (빠르게 확산 중)

**관련 패턴**: `data-lineage`(추상 개념), `data-catalog`(consumer 측), `dq-validation-tools`(GE/dbt 가 OpenLineage 로 결과 publish)

**Cross-link**:
- `patterns/master-data-management.md#mdm-match-merge`(survivorship 의 lineage 추적)
- DAMA-DMBOK 2 KA12 *Metadata Management*
- Linux Foundation OpenLineage spec v1.x (`openlineage.io/spec`)

---

## 6. DQ Validation Tools Matrix (검증 도구 매트릭스)

<a id="dq-validation-tools"></a>

**목적**: DQ 6 차원을 실제 측정·검증하는 5 대 도구의 강점·약점·통합 지점 매핑. ISO/IEC 25012 의 inherent quality 측정과 DAMA-DMBOK 2 의 DQ rule library 를 구현 레벨에서 실현한다.

**5 대 도구 비교 매트릭스**:

| 도구 | 분류 | 운영 모델 | 강점 | 약점 | DQ 차원 커버 | OpenLineage |
|---|---|---|---|---|---|---|
| **Great Expectations (GE)** | OSS, Python | declarative expectation suite | 풍부한 expectation library(50+), HTML data docs 자동 생성, Pandas/Spark/SQL backend | YAML config 복잡, 대용량 성능 ↓, profiler 약함 | Validity, Completeness, Uniqueness, Accuracy(regex), Consistency(cross-table) | 공식 emitter |
| **Soda (SodaCL / Soda Core)** | OSS + Cloud | declarative YAML(SodaCL DSL) | 간결한 YAML 문법, anomaly detection(ML), Slack 통합, monitoring 중심 | OSS 기능 제한적, advanced 기능 cloud 유료 | Completeness, Validity, Uniqueness, Freshness | 공식 integration |
| **dbt tests** | OSS, SQL | model-side test (`schema.yml`) | dbt 파이프라인 내장, generic test 4종(unique/not_null/accepted_values/relationships), custom singular/generic test | dbt 사용 전제, profile 기능 없음, 실시간 부적합 | Uniqueness(unique), Completeness(not_null), Validity(accepted_values), Consistency(relationships) | dbt-ol 자동 |
| **Monte Carlo** | SaaS | ML-based observability | 자동 anomaly detection(no config), 5 pillar(Freshness/Volume/Schema/Quality/Lineage), incident management | 비용 ↑, ML false positive 튜닝 필요, 폐쇄 SaaS | Timeliness(Freshness), Completeness(Volume), Schema drift, Validity, lineage | 자체 lineage(OL 부분 통합) |
| **Anomalo** | SaaS | unsupervised ML | zero-config anomaly detection, root cause suggestion, no rule writing | 비용 ↑, custom rule 보조 필요, ML 모델 black-box | Accuracy(outlier), Completeness, Uniqueness, drift 탐지 | 부분 |

**5 pillar 모델 (Monte Carlo, 데이터 옵저버빌리티 표준)**:
1. **Freshness**: 데이터 적시성 (Timeliness 차원)
2. **Volume**: 레코드 수 이상 (Completeness 차원, drop/spike)
3. **Schema**: 스키마 변경 (drift 탐지)
4. **Quality**: 6 차원 rule 기반 검증
5. **Lineage**: 영향 범위 추적

**도구 선택 의사결정 트리**:

```
Q1: 파이프라인 스택?
├── dbt 사용 → dbt tests 기본 + GE/Soda 보강
├── Spark 위주 → GE (Spark backend) + Soda
└── 다양함 → Soda(통합) + Monte Carlo(observability)

Q2: 예산?
├── 무료/OSS 우선 → GE + Soda Core + dbt tests
└── 비용 OK → Monte Carlo / Anomalo (ML observability)

Q3: ML/anomaly 자동 탐지?
├── 필요 → Monte Carlo / Anomalo / Soda Cloud
└── rule 명시 OK → GE + Soda + dbt tests

Q4: lineage 통합?
├── OpenLineage 표준 필요 → GE / Soda / dbt(공식 emitter)
└── 자체 lineage OK → Monte Carlo
```

**Great Expectations 코드 예제 (Python)**:
```python
import great_expectations as gx

context = gx.get_context()
suite = context.add_or_update_expectation_suite("users_suite")
batch = context.sources.pandas_default.read_csv("users.csv")

# Validity: 이메일 regex
batch.expect_column_values_to_match_regex(
    "email", r"^[\w.+-]+@[\w-]+\.[\w.-]+$"
)
# Completeness: NULL 금지
batch.expect_column_values_to_not_be_null("user_id")
# Uniqueness: PK
batch.expect_column_values_to_be_unique("user_id")
# Validity: enum
batch.expect_column_values_to_be_in_set("status", ["active", "inactive", "pending"])

results = batch.validate()
# OpenLineage emitter 가 dataQualityAssertions facet 으로 publish
```

**dbt tests 예제 (YAML)**:
```yaml
# models/marts/users.yml
version: 2
models:
  - name: dim_users
    columns:
      - name: user_id
        tests:
          - unique
          - not_null
      - name: email
        tests:
          - not_null
          - dbt_utils.not_empty_string
      - name: status
        tests:
          - accepted_values:
              values: ['active', 'inactive', 'pending']
      - name: org_id
        tests:
          - relationships:
              to: ref('dim_organizations')
              field: org_id
```

**Soda SodaCL 예제 (YAML)**:
```yaml
# checks for users
checks for prod.users:
  - row_count > 0
  - missing_count(email) = 0
  - duplicate_count(user_id) = 0
  - invalid_percent(email) < 1%:
      valid format: email
  - freshness(updated_at) < 1h
  - anomaly score for row_count < 0.7
```

**장점**:
- 도구별 강점 결합 시 6 차원 전체 커버 가능
- OpenLineage 통합 시 lineage + DQ 가 단일 catalog 에서 조회됨
- CI/CD 파이프라인에 통합 (PR 시 expectation 자동 실행)

**단점**:
- 도구 중복 → 운영 부담 (3개 이상 사용 시 alert fatigue)
- ML 기반 도구는 cold-start 기간(2~4 주 학습) 필요
- 도구 간 alert dedup 별도 구현 필요

**활용 예시**:
- Lyft / Airbnb: GE + Amundsen
- Vimeo / GitLab: Soda + dbt
- Fox / JetBlue: Monte Carlo enterprise

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**관련 패턴**: `dq-6-dimensions`(측정 대상), `openlineage-standard`(결과 publish 채널), `data-catalog`(통합 표시)

**Cross-link**:
- `patterns/master-data-management.md#mdm-match-merge`(MDM 의 match score 도 DQ 측정의 일종)
- `principles/database-fundamentals.md`(검증 도구가 DB 부하에 미치는 영향)
- ISO/IEC 25024:2015 *Measurement of data quality* (측정 방법론 표준)

---

## 참고문헌 (References)

- **DAMA International**, *DAMA-DMBOK: Data Management Body of Knowledge, 2nd Edition* (Mosley, Brackett, Earley, Henderson eds., Technics Publications, 2017). 특히 KA8 *Reference and Master Data*, KA10 *Data Quality*, KA12 *Metadata Management*, KA1 *Data Governance*.
- **ISO/IEC 25012:2008**, *Software engineering — Software product Quality Requirements and Evaluation (SQuaRE) — Data quality model*. 15 inherent/system-dependent 데이터 품질 특성.
- **ISO/IEC 25024:2015**, *Systems and software engineering — SQuaRE — Measurement of data quality*. 차원별 측정 방법론.
- **ISO/IEC 38505-1:2017**, *Information technology — Governance of IT — Governance of data — Part 1*.
- **Wang, R. Y., & Strong, D. M.** (1996). *Beyond Accuracy: What Data Quality Means to Data Consumers*. Journal of Management Information Systems, 12(4). — DQ 4 카테고리 16 차원 분류의 학술적 기원.
- **Linux Foundation OpenLineage**. `openlineage.io/spec` (v1.x). RunEvent / Job / Dataset / facet 표준 정의.
- **Marquez Project**. OpenLineage reference backend (WeWork, 2018; LF 이관 2021).
- **Great Expectations Documentation**. `docs.greatexpectations.io`.
- **Soda Documentation**. `docs.soda.io/soda-cl/soda-cl-overview.html`.
- **Monte Carlo Data**. *The Five Pillars of Data Observability* (whitepaper, 2021).
- **Gartner** (2021). *Market Guide for Active Metadata Management*.

## Cross-link Targets (역방향 링크 후보)

- `patterns/master-data-management.md` — Golden Record / Survivorship 의 DQ 측정 측면
- `principles/database-fundamentals.md` — Consistency / Replication / Isolation 의 DQ 영향
- `patterns/data-modeling.md` — Normalization / Constraints 가 DQ inherent quality 의 기반
- [`patterns/data-warehousing-bi.md#dbt-modeling`](data-warehousing.md#dbt-modeling) (P1 신설) — dbt 의 `tests:` / `data tests` / Snapshot 으로 DQ 6 차원을 변환 파이프라인에 정량 통합
- `security/index.md` — PII 탐지·접근 통제와 DQ 의 교차점
