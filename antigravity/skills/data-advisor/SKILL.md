---
name: data-advisor
description: DMBOK KA 기반 데이터 관리 카탈로그 스킬. SWEBOK(소프트웨어 공학)이 아니라 DAMA-DMBOK(데이터 관리) 어휘 체계만 수용한다.
---

# data-advisor

DMBOK KA 기반 데이터 관리 카탈로그 스킬.
SWEBOK(소프트웨어 공학)이 아니라 DAMA-DMBOK(데이터 관리) 어휘 체계만 수용한다.

## Scope (In-scope)

DMBOK KA2/3/7/8/10 및 거버넌스 영역:
- **KA2 Data Architecture**: 정규화, CAP/PACELC, 격리 수준, ACID/BASE, 복제, 파티셔닝 (`principles/db-fundamentals.md`)
- **KA3 Data Storage & Operations**: DB 인덱스(B+Tree/Hash/Bitmap/GIN/GiST/BRIN/Covering/Partial) (`algorithms/db-indexes.md`), 스토리지 엔진(WAL/LSM/SSTable/MVCC/Buffer Pool 등) (`algorithms/db-storage-engines.md`), 쿼리 옵티마이저(Join/CBO/Plan Cache/Cardinality/EXPLAIN) (`algorithms/db-query-optimizer.md`)
- **KA7 Reference & Master Data**: Golden Record, Survivorship, Match-Merge, Data Steward, Reference Data, Hierarchy (`patterns/mdm.md`)
- **KA8 Data Warehousing & BI**: Kimball Star/Snowflake, SCD, Fact Table, OLAP, Lakehouse, dbt (`patterns/data-warehousing.md`)
- **KA10 Data Quality**: DQ 6 Dimensions, Data Lineage, Data Catalog, Stewardship RACI, OpenLineage, DQ Validation Tools (`patterns/data-quality.md`)

## Out-of-scope

- **분산 일관성 / 복제 / 샤딩** → dev-advisor `patterns/data-modeling.md` (CAP 실무 패턴)
- **OO 영속성 / 데이터 접근 패턴** → dev-advisor `patterns/data-access.md`
- **공간·검색 알고리즘** → dev-advisor `algorithms/spatial.md`, `algorithms/search-systems.md`
- **데이터 보안** → dev-advisor `security/security-data-protection.md`
- **ML/AI 데이터 파이프라인** → dev-advisor `patterns/mlops.md`

"SWEBOK KA가 아니라 DMBOK KA에 매핑되는 어휘만 수용"

## 호출 방법 (lookup-only, advisor 모드 없음)

```
/data list                     # 전체 항목 나열
/data search <키워드>           # 키워드 검색
/data <id>                     # 항목 직접 조회 (예: /data mdm-golden-record)
/mdm                           # Master Data Management 항목
/dwh                           # Data Warehousing & BI 항목
/dq                            # Data Quality 항목
```

> 내부 실행: 위 `/data ...` 명령은 `scripts/lookup-catalog.py <id|list|search <kw>>` 로 매핑된다. dev-advisor 와 달리 **도메인 prefix 없이** 부명령(`list`/`search`/`<id>`)을 바로 받는다 (예: `python3 scripts/lookup-catalog.py mdm-golden-record`).

## 트리거 키워드

`data-advisor`, `/data`, `/mdm`, `/dwh`, `/dq`,
`MDM`, `마스터 데이터`, `골든 레코드`, `데이터 품질`, `데이터 웨어하우스`,
`Kimball`, `SCD`, `dbt`, `Data Lineage`, `DMBOK`,
`B+Tree`, `LSM Tree`, `WAL`, `MVCC`, `Buffer Pool`,
`쿼리 옵티마이저`, `EXPLAIN ANALYZE`, `db-indexes`, `db-storage-engines`
