# 마스터 데이터 관리 패턴 (Master Data Management Patterns)

조직 전사 단위의 핵심 비즈니스 엔터티(Customer / Product / Vendor / Employee / Location 등)를 **단일 진실 원천(Single Source of Truth, SSoT)** 으로 통합·관리하는 6 패턴. DAMA-DMBOK 2 (Data Management Body of Knowledge 2nd ed., 2017) Knowledge Area 9 — *Reference and Master Data Management* 기반.

**원전·표준 참고**:
- DAMA International — *DAMA-DMBOK: Data Management Body of Knowledge, 2nd Edition* (2017) — Chapter 10 (Reference and Master Data)
- ISO 8000-110 — *Data quality — Part 110: Master data: Exchange of characteristic data: Syntax, semantic encoding, and conformance to data specification* (2021)
- ISO 8000-115 — *Master data quality identifiers* (2018)
- Allen Dreibelbis et al. — *Enterprise Master Data Management: An SOA Approach to Managing Core Information* (IBM Press, 2008)
- David Loshin — *Master Data Management* (Morgan Kaufmann, 2009)
- Aaron Zornes — *MDM Institute* 산업 분류 (Registry / Coexistence / Consolidation / Centralized)
- Gartner — *Magic Quadrant for Master Data Management Solutions* (연간)
- William E. Winkler — "Overview of Record Linkage and Current Research Directions" (US Census Bureau, 2006) — Fellegi-Sunter 모델
- Ivan P. Fellegi & Alan B. Sunter — "A Theory for Record Linkage" (*JASA* 1969) — 확률적 매칭의 형식 이론

**MDM 구현 4 아키텍처 스타일 (Aaron Zornes 분류)**:

| 스타일 | 원천 시스템 권한 | Hub 역할 | 적용 |
|--------|------------------|----------|------|
| Registry | 원천 보존 | ID 매핑만 | 변경 최소 / 분석용 |
| Coexistence | 양방향 동기 | 황금 레코드 + 원천 갱신 | 점진 도입 |
| Consolidation | 원천 보존 | 황금 레코드 read-only | DW / 분석 우선 |
| Centralized (Transaction) | Hub 단일 권한 | CRUD 본체 | 신규 도입 / 클린 슬레이트 |

**관련 카탈로그**:
- [`data-modeling.md`](../../../dev-advisor/references/patterns/data-modeling.md) — CAP / Replication / CDC / Materialized View (분산 일관성 본체)
- [`data-quality-governance.md`](data-quality.md) — DQ 6 Dimensions / Lineage / Catalog / Stewardship RACI (병렬 카탈로그)
- [`../principles/database-fundamentals.md`](../principles/db-fundamentals.md) — ACID / BASE / 격리 / 정규화 (이론 본체)
- [`ddd-strategic.md`](../../../dev-advisor/references/patterns/ddd-strategic.md) — Bounded Context / Context Map (MDM 경계 식별)

---

<a id="mdm-golden-record"></a>

## 1. Golden Record (황금 레코드 / Single Source of Truth)

**정의**: 여러 원천 시스템(CRM, ERP, e-Commerce, Billing 등)에 흩어진 동일 엔터티의 인스턴스를 통합해, 조직 전사가 합의한 **단일 권위 표현(authoritative representation)** 으로 만든 통합 레코드. ISO 8000-110 의 *master data* 정의("data held by an organization that describes the entities that are both independent and fundamental for that organization") 의 운영 형태이며, DMBOK 2 KA 10 의 핵심 산출물이다.

**메커니즘**:
- **수집(Ingest)** — 모든 원천 시스템에서 동일 엔터티의 변종(variants) 을 ETL/CDC 로 수집
- **표준화(Standardize)** — 주소 정규화(USPS / KISA 도로명), 전화번호 E.164, 이름 대소문자/특수문자 통일
- **매칭(Match)** — 같은 실세계 엔터티를 가리키는 레코드 식별 ([3번 Match-Merge](#mdm-match-merge))
- **병합(Merge)** — 매칭된 레코드들을 [Survivorship 규칙](#mdm-survivorship-rules) 으로 황금 레코드 1개 생성
- **유지(Sustain)** — 원천 갱신 시 황금 레코드 동기화 + Data Steward 큐레이션
- **공급(Syndicate)** — 황금 레코드를 다운스트림 (DW, BI, ML feature store, 다른 OLTP) 으로 전파

**SSoT vs SSoF**:
- **SSoT (Single Source of Truth)** — 황금 레코드 자체. 모든 다운스트림이 참조하는 표준
- **SSoF (Single Source of Facts)** — Lineage 까지 보존한 원천 추적 (어느 시스템의 어느 필드에서 왔는가)

**장점**:
- 사일로 통합으로 인한 보고서 불일치(예: 영업/회계의 매출 차이) 해소
- 360° 고객 뷰 / 다채널 마케팅 / 컴플라이언스 보고 가능
- 신규 시스템 도입 시 마스터 참조점 명확

**단점·trade-off**:
- 초기 매칭 임계값 튜닝 비용 큼 (over-match → 다른 사람 병합, under-match → 중복 잔존)
- 권위 시스템(authoritative source) 정치 — 누가 "진짜" 인가 합의 어려움
- 황금 레코드 갱신 지연 시 다운스트림과의 일시적 불일치 (eventual consistency — [`data-modeling.md#cap-theorem`](../../../dev-advisor/references/patterns/data-modeling.md#cap-theorem))

**실제 도구**:
- **SAP MDG** — SAP S/4HANA Customer / Material / Supplier / Finance Master
- **Informatica MDM** — Multi-Domain Hub + Customer 360
- **Reltio Connected Data Platform** — 그래프 기반 SaaS
- **IBM InfoSphere MDM** — Initiate Patient 360 기원
- **오픈소스** — Pimcore PIM, Apache Unomi (CXS)

**Kotlin / pseudo-code 예제**:
```kotlin
// 황금 레코드 도메인 모델 (DDD Aggregate Root)
data class GoldenCustomer(
    val masterId: String,           // MDM Hub 가 발급한 전사 단일 ID
    val name: String,
    val email: String,
    val phone: String,
    val address: Address,
    val sources: List<SourceLink>,  // SSoF — 원천 시스템 + 외부 ID + 신뢰도
    val lastMergedAt: Instant,
    val stewardOverrides: Map<String, FieldOverride> = emptyMap()
)

data class SourceLink(
    val system: String,        // "CRM", "ERP", "BILLING"
    val externalId: String,
    val confidence: Double,    // 0.0 ~ 1.0 (Fellegi-Sunter m-probability)
    val lastSeenAt: Instant
)

// Steward 가 수동 override 한 필드는 자동 머지에서 보호
data class FieldOverride(
    val value: String,
    val stewardId: String,
    val reason: String,
    val frozenUntil: Instant?
)
```

**관련 패턴**: [Survivorship Rules](#mdm-survivorship-rules), [Match-Merge](#mdm-match-merge), [Data Steward](#mdm-data-steward)

---

<a id="mdm-survivorship-rules"></a>

## 2. Survivorship Rules (생존 규칙 / Trust Rules)

**정의**: 매칭된 후보 레코드들에서 황금 레코드 각 필드의 **생존 값(surviving value)** 을 선택하는 규칙 집합. Loshin (2009) Chapter 8 — *Identity Resolution and Information Quality* 의 핵심으로, DMBOK 2 KA 10.3.2 *Identify Sources of Master Data* 이후 단계. 필드별로 다른 규칙을 적용하는 **Field-Level Survivorship** 이 표준이다.

**메커니즘 (4 대표 전략)**:

| 전략 | 규칙 | 적용 필드 예시 | 위험 |
|------|------|--------------|------|
| **Most-Recent** | `MAX(lastUpdatedAt)` 의 값 채택 | 주소, 전화번호 (자주 변함) | 잘못된 최근 갱신 → 황금 레코드 오염 |
| **Source-Priority** | 시스템 신뢰 순위표 우선 (예: ERP > CRM > Web) | 회계 코드, 세금 ID | 우선순위 정치 + 변경 어려움 |
| **Confidence-Score** | 원천별 + 필드별 신뢰도 가중합 | 이메일, 휴대전화 | 점수 캘리브레이션 필요 |
| **Field-Level** | 각 필드마다 다른 전략 (혼합) | 표준 권장 | 규칙 관리 복잡 |
| **Most-Frequent** | 최다 출현 값 | 이름 표기 | 다수결의 폭정 |
| **Longest / Most-Complete** | 가장 긴 / null 아닌 값 | 주소 line 2 | "긴 값=좋은 값" 가정 위험 |
| **Steward Override** | 수동 잠금 ([Data Steward](#mdm-data-steward) 결정) | 분쟁 필드 | 수동 부담 |

**Hierarchy of Trust (신뢰 계층)**:
1. Steward Override (frozen) — 항상 최우선
2. Authoritative Source (특정 필드 한정) — ERP 의 세금 ID 등
3. Confidence-weighted aggregation
4. Most-Recent (fallback)

**장점**:
- 룰 기반이라 audit / 회귀 추적 용이 (왜 이 값이 살아남았는가?)
- 필드별 차등 — 휴대전화는 최신, 세금 ID 는 ERP 만, 등

**단점·trade-off**:
- 규칙 폭발(rule explosion) — 도메인 × 필드 × 원천 조합으로 수십~수백 규칙
- 잘못된 최신값 (전산 오류 / 가짜 데이터) 이 황금 레코드 오염
- ML 기반 confidence 도입 시 설명가능성 저하

**실제 도구**:
- **Informatica MDM** — Trust Score (필드별 source weighting + decay)
- **Reltio** — Survivorship Rules UI (no-code 룰 빌더)
- **SAP MDG** — Active Hierarchies + Best Record Calculation
- **Talend MDM** — Survivorship Rule Configurator (Cleansing → Match → Merge 파이프라인)

**Kotlin 예제 — Confidence-Score Survivorship**:
```kotlin
data class Candidate<T>(
    val value: T,
    val source: String,
    val updatedAt: Instant,
    val baseConfidence: Double // 원천 시스템 신뢰도
)

class FieldSurvivor<T>(
    private val priorities: Map<String, Double>, // 원천별 가중치
    private val decayHalfLifeDays: Long = 90     // 시간 감쇠
) {
    fun pick(candidates: List<Candidate<T>>): T {
        require(candidates.isNotEmpty())
        val now = Instant.now()
        return candidates.maxBy { c ->
            val ageDays = ChronoUnit.DAYS.between(c.updatedAt, now)
            val decay = Math.pow(0.5, ageDays.toDouble() / decayHalfLifeDays)
            val sourceWeight = priorities[c.source] ?: 0.5
            c.baseConfidence * sourceWeight * decay
        }.value
    }
}
```

**관련 패턴**: [Golden Record](#mdm-golden-record), [Match-Merge](#mdm-match-merge), [Data Steward](#mdm-data-steward) (Override)

---

<a id="mdm-match-merge"></a>

## 3. Match-Merge (매칭·병합 / Record Linkage / Entity Resolution)

**정의**: 서로 다른 원천에서 들어온 두 레코드가 **같은 실세계 엔터티를 가리키는지** 판정하고, 판정된 그룹을 하나의 황금 레코드로 합치는 과정. Fellegi-Sunter (1969) 의 *probabilistic record linkage* 이론과 William Winkler (US Census Bureau) 의 *Jaro-Winkler* 거리 측도가 산업 표준이다. ISO/IEC 11179-3 의 metadata registry 와 결합해 의미적 매칭을 수행한다.

**메커니즘 (3 매칭 기법)**:

| 기법 | 알고리즘 | 정확도 | 설명가능성 |
|------|---------|--------|----------|
| **Deterministic** | exact match (이메일, 세금 ID, 전화번호) | 100% (있을 때) | 100% |
| **Probabilistic** | Fellegi-Sunter + 거리 측도 | 95~98% | 중간 (m/u-probability 수식) |
| **ML-based** | Siamese NN / DeepER / ditto (BERT) | 98~99% | 낮음 (블랙박스) |

**거리 측도 / 문자열 유사도** (DMBOK 2 표준):

| 측도 | 정의 | 특성 |
|------|------|------|
| **Edit Distance / Levenshtein** | 삽입/삭제/치환 최소 횟수 | 일반적, 한국어 자소단위 적용 가능 |
| **Damerau-Levenshtein** | Levenshtein + transposition | 오타 (ab → ba) 강건 |
| **Jaro** | 공통 문자 + transposition 비율 | 짧은 문자열 (이름) 강건 |
| **Jaro-Winkler** | Jaro + prefix 가중치 | 이름 매칭 표준 (Winkler 1990 US Census) |
| **Soundex / Metaphone** | 발음 기반 코드 | 영어권 이름 (Catherine ~ Katherine) |
| **n-gram / Jaccard** | 문자 n-gram 집합 유사도 | 회사명 (LLC / Inc.) |
| **Cosine (TF-IDF)** | 토큰 가중 벡터 | 긴 주소, 회사명 |

**Blocking / Indexing** — 후보 쌍 줄이기:
- **Standard Blocking** — 우편번호 / 생년월일 등 키로 grouping
- **Sorted Neighborhood** — 정렬 후 sliding window
- **Canopy Clustering** — 빠른 측도로 1차 군집화 (McCallum et al. 2000)
- **LSH (Locality-Sensitive Hashing)** — MinHash / SimHash

**Fellegi-Sunter 결정 룰**:
- `m-probability` = 같은 엔터티일 때 필드가 일치할 확률
- `u-probability` = 다른 엔터티일 때 필드가 일치할 확률
- `weight = log2(m/u)` 합산 → **upper threshold** 초과 = MATCH, **lower threshold** 미만 = NON-MATCH, 중간 = **POSSIBLE MATCH** (스튜어드 검토)

**장점**:
- Deterministic + Probabilistic 혼합으로 정확도/recall 균형
- 블로킹으로 O(N²) → O(N·k) 까지 줄임 (N=레코드 수, k=블록 크기)

**단점·trade-off**:
- 임계값 튜닝 = ground truth 필요 (수동 라벨링 비용)
- false positive (다른 사람 병합) 는 unmerge 비용 매우 큼
- 한국어 한자/한글 혼용, 회사명 약어 등 도메인 특수 규칙 필요

**실제 도구**:
- **Splink** (UK MoJ, 오픈소스) — Fellegi-Sunter + Spark, EM 알고리즘으로 m/u 자동 추정
- **Zingg** (오픈소스) — ML 기반, label-by-active-learning
- **Dedupe.io** (Python, 오픈소스 + SaaS)
- **Informatica MDM** — Identity Resolution Engine
- **Reltio Match Rules** — no-code 룰 + ML 보조
- **Apache Spark + Soundex/JaroWinkler UDF** — 대량 배치

**Kotlin 예제 — Jaro-Winkler + 블로킹**:
```kotlin
import org.apache.commons.text.similarity.JaroWinklerSimilarity

class RecordMatcher(
    private val jw: JaroWinklerSimilarity = JaroWinklerSimilarity(),
    private val threshold: Double = 0.92
) {
    // 블로킹 — 우편번호 5자리로 1차 군집
    fun block(records: List<Customer>): Map<String, List<Customer>> =
        records.groupBy { it.postalCode.take(5) }

    fun isMatch(a: Customer, b: Customer): MatchResult {
        // Deterministic 단계
        if (a.taxId.isNotBlank() && a.taxId == b.taxId) return MatchResult.MATCH
        // Probabilistic 단계
        val nameSim  = jw.apply(a.name, b.name)
        val addrSim  = jw.apply(a.address, b.address)
        val phoneSim = if (a.phone == b.phone) 1.0 else 0.0
        val score = 0.5 * nameSim + 0.3 * addrSim + 0.2 * phoneSim
        return when {
            score >= threshold      -> MatchResult.MATCH
            score >= threshold - 0.1 -> MatchResult.REVIEW  // Possible Match → Steward 큐
            else                    -> MatchResult.NON_MATCH
        }
    }
}
```

**관련 패턴**: [Golden Record](#mdm-golden-record), [Survivorship Rules](#mdm-survivorship-rules), [Data Steward](#mdm-data-steward) — POSSIBLE MATCH 큐 검토

---

<a id="mdm-data-steward"></a>

## 4. Data Steward (데이터 스튜어드 / Stewardship Operating Model)

**정의**: 마스터 데이터의 정의·품질·라이프사이클을 책임지는 **사람과 거버넌스 조직**. DMBOK 2 KA 1 *Data Governance* 에서 정의된 역할로, 단순 운영자(operator) 가 아니라 **비즈니스 의미의 권위(authority over business meaning)** 를 가진다. ISO/IEC 38505-1 *Governance of data* 의 EDM(Evaluate-Direct-Monitor) 모델과 결합한다.

**Stewardship 3 모델 (DMBOK 2 Figure 22)**:

| 모델 | 구조 | 장점 | 단점 |
|------|------|------|------|
| **Centralized** | CDO 산하 단일 팀 | 일관성 / 표준화 강함 | 비즈니스 도메인 이해 약함 |
| **Federated** | 도메인별 (LoB) 스튜어드 + 중앙 정책 | 도메인 전문성 + 조직 정렬 | 도메인 간 충돌 / 일관성 약함 |
| **Hybrid (권장)** | 중앙 표준 + 도메인 운영 (Hub & Spoke) | 양쪽 장점 | 거버넌스 오버헤드 |

**역할 분류 (DMBOK 2 KA 1.2.3)**:
- **Executive Sponsor** — C-level (CDO / COO) — 자원 / 의사결정 권한
- **Chief Data Steward** — 전사 표준 + 정책
- **Business Steward** — 도메인 (Customer / Product) 의 의미적 권위
- **Technical Steward** — 시스템·스키마·파이프라인 책임
- **Operational Steward** — 일상 큐레이션 (POSSIBLE MATCH 검토, 오류 수정)

**RACI 매트릭스 (마스터 데이터 활동 × 역할)**:

| 활동 | Executive | Chief | Business | Technical | Operational |
|------|-----------|-------|----------|-----------|-------------|
| 표준 정책 승인 | A | R | C | C | I |
| 신규 도메인 추가 | A | R | C | C | I |
| 도메인 모델 정의 | I | A | R | C | I |
| 매칭 룰 튜닝 | I | C | A | R | C |
| POSSIBLE MATCH 큐 검토 | I | I | A | C | R |
| 황금 레코드 Override | I | I | A | C | R |
| 데이터 품질 KPI 보고 | I | A | R | C | C |

(A=Accountable, R=Responsible, C=Consulted, I=Informed)

**거버넌스 의식 / 회의체**:
- **Data Governance Council** — 분기, Executive + Chief — 정책 승인
- **Data Stewardship Forum** — 월간, Business + Technical Steward — 운영 이슈
- **Steward Working Group** — 주간, Operational Steward — 큐 처리

**장점**:
- 비즈니스 의미와 기술 구현의 정렬
- 분쟁 시 명확한 의사결정 경로
- 황금 레코드 권위(authority) 확립

**단점·trade-off**:
- 거버넌스 오버헤드 (회의·문서·승인)
- Steward 인력 수급 어려움 (도메인 + 데이터 양쪽 능력)
- 정치적 갈등 (어느 LoB 가 권위?)

**실제 도구·프레임**:
- **Collibra Data Governance** — Stewardship 워크플로우 + 글로서리
- **Alation Data Catalog** — 협업 기반 스튜어드십
- **Informatica Axon** — Business Glossary + Stewardship
- **Apache Atlas + Ranger** — 오픈소스 거버넌스 + 정책
- **DataHub (LinkedIn)** — 오픈소스 카탈로그 + 스튜어드 ownership

**관련 패턴**: [Golden Record](#mdm-golden-record) — Override, [Survivorship Rules](#mdm-survivorship-rules) — 분쟁 해결, [Match-Merge](#mdm-match-merge) — REVIEW 큐. 데이터 품질 KPI 는 [`data-quality-governance.md`](data-quality.md) 의 *Stewardship RACI* 항목과 연결.

---

<a id="mdm-reference-data"></a>

## 5. Reference Data Management (참조 데이터 관리)

**정의**: 마스터 데이터와 구분되는, **유한하고 자주 변하지 않는 분류 / 코드 / 표준값** 의 관리. DMBOK 2 는 *master* 와 *reference* 를 분리 정의: 마스터는 비즈니스 엔터티(Customer/Product), 참조는 분류 코드(Country, Currency, Unit, Industry Code, Status Code). ISO 표준(ISO 3166 국가코드 / ISO 4217 통화 / ISO 8601 날짜 / UCUM 단위) 을 1차 권위로 사용한다.

**메커니즘 (참조 데이터 5 유형)**:

| 유형 | 표준 | 예시 |
|------|------|------|
| **국가/지역 코드** | ISO 3166-1/2 | KR, US-CA, JP-13 (도쿄) |
| **통화** | ISO 4217 | KRW, USD, JPY (alpha-3) + 숫자 코드 |
| **단위** | UCUM / SI / ISO 80000 | kg, m/s², °C |
| **언어 / Locale** | ISO 639 / BCP 47 | ko-KR, en-US-x-icu |
| **산업 분류** | NAICS / KSIC / NACE / ISIC | 51 정보통신업 (KSIC) |
| **의료 / 보건** | ICD-11 / SNOMED CT / LOINC / RxNorm | I10 (본태성 고혈압) |
| **금융** | ISIN / LEI / SWIFT BIC / IBAN | KR7005930003 (삼성전자) |
| **내부 분류** | (조직 자체) Status / Reason Code | "ACTIVE", "CANCELLED" |

**Cross-Reference (코드 매핑) 패턴**:
- **Code Set Versioning** — ICD-9 → ICD-10 → ICD-11 마이그레이션 매핑 보존
- **Source Code → Canonical Code** — 시스템별 다른 "활성" 코드 ("ACT", "1", "Y") 를 표준 ("ACTIVE") 로 매핑
- **Many-to-Many Crosswalks** — NAICS ↔ KSIC 매핑 (Concordance 표)
- **Effective Dating** — 코드의 시작/종료 날짜 (`valid_from`, `valid_to`)

**Reference Data Architecture (Loshin 2009)**:
1. **Inline (테이블 내 enum)** — 작은 정적 — 한국 17 시도 등
2. **Lookup Table** — RDBMS 의 `countries` 테이블 + FK
3. **Code Set Service (REST/gRPC)** — `GET /codes/iso-3166?as_of=2025-01-01`
4. **Dedicated RDM Hub** — Collibra / TopBraid RDM / EDM Council FIBO

**장점**:
- 마스터 데이터보다 거버넌스 비용 낮음 (변경 빈도 낮음)
- 외부 표준 채택으로 상호운용성 확보
- 다국가 시스템의 i18n 기반

**단점·trade-off**:
- 외부 표준 갱신 시점 추적 부담 (ISO 3166 알바니아 분리 등)
- 내부 분류와 외부 표준의 동기 (수동 매핑 필요)
- Effective Dating 미적용 시 과거 보고서 재계산 불가

**실제 도구**:
- **Collibra Reference Data Manager** — 표준 + 사용자 정의 + crosswalk
- **TopBraid RDM** — 시맨틱 (RDF/SKOS) 기반 참조 데이터
- **EDM Council FIBO** (Financial Industry Business Ontology) — 금융 표준
- **HL7 Terminology Server** — ICD/SNOMED/LOINC (의료)
- **CLDR (Unicode Common Locale Data Repository)** — Locale / 통화 / 시간대
- **오픈소스** — `pycountry` (ISO 3166/4217/639/15924), `gettext` (Locale)

**Kotlin 예제 — Effective Dating 적용 참조 코드**:
```kotlin
data class CountryCode(
    val alpha2: String,      // KR
    val alpha3: String,      // KOR
    val numeric: Int,        // 410
    val nameKo: String,
    val nameEn: String,
    val validFrom: LocalDate,
    val validTo: LocalDate?  // null = 현재 유효
)

class CountryCodeRepository {
    fun lookup(alpha2: String, asOf: LocalDate = LocalDate.now()): CountryCode? =
        codes.firstOrNull {
            it.alpha2 == alpha2 &&
            asOf >= it.validFrom &&
            (it.validTo == null || asOf <= it.validTo)
        }
}
```

**관련 패턴**: [Hierarchy Management](#mdm-hierarchy) (분류 코드의 계층), [Golden Record](#mdm-golden-record) (참조 코드로 마스터 표준화)

---

<a id="mdm-hierarchy"></a>

## 6. Hierarchy Management (계층 관리 / Hierarchies + SCD)

**정의**: 마스터 데이터의 **다대다·시간변화·다관점 계층** 표현·유지. 조직도(Employee → Manager), 제품 분류(Product → Category → Department), 지역(City → State → Country), 비용 센터(Cost Center → BU → LoB) 등이 대표적. DMBOK 2 KA 10.2 *Master Data Hierarchies* 와 Kimball *Data Warehouse Toolkit* (3rd ed., 2013) Chapter 7 *Inventory* 의 **Slowly Changing Dimensions (SCD)** 가 결합되어야 시간 정합성이 확보된다.

**메커니즘 (3 계층 토폴로지)**:

| 토폴로지 | 정의 | 예시 | RDB 모델 |
|---------|------|------|---------|
| **Balanced (균형)** | 모든 leaf 가 동일 깊이 | 회계연도 → 분기 → 월 → 일 | 정규화 컬럼 / 별도 dim |
| **Ragged (비균형)** | leaf 깊이 다름 (일부 중간 노드 누락) | 국가 → (주) → 도시 (한국엔 주 없음) | 1) Bridge Table 2) Path Enumeration |
| **Network (네트워크)** | 다부모(multi-parent) — DAG | 제품 → 다중 카테고리 (스마트폰 ∈ 가전 ∩ 모바일) | Many-to-Many bridge + weight |
| **Recursive** | self-referencing parent_id | 조직도 | Adjacency List / CTE 재귀쿼리 |

**계층 저장 4 패턴**:
1. **Adjacency List** — `parent_id` 컬럼 (가장 단순, 재귀 CTE 필요)
2. **Path Enumeration** — `/root/Asia/Korea/Seoul` 문자열
3. **Nested Set** — `lft`, `rgt` (Joe Celko, *Trees and Hierarchies*, 2004) — 읽기 빠름 / 쓰기 느림
4. **Closure Table** — 모든 조상-자손 쌍 별도 테이블 — 쿼리 유연성 최고

**Slowly Changing Dimensions (SCD) — Kimball 분류**:

| SCD Type | 정의 | 적용 |
|----------|------|------|
| **Type 0** | 변경 무시 (immutable) | 생년월일, 고객 가입일 |
| **Type 1** | overwrite (이력 없음) | 오타 수정 |
| **Type 2 (표준)** | 새 행 + `effective_from`/`effective_to` + `is_current` | 이력 추적 필수 (주소, 부서) |
| **Type 3** | `prev_value` + `current_value` 컬럼 | 직전값만 필요 |
| **Type 4** | History Table 분리 | 변경 빈도 매우 높음 |
| **Type 6 (1+2+3 hybrid)** | Type 2 + current 컬럼 + previous 컬럼 | 복잡한 보고 |
| **Type 7** | Surrogate Key (현재) + Natural Key (이력) 이중 차원 | BI 양쪽 시점 보고 |

**시점 보고 (As-Was vs As-Is)**:
- **As-Is** — 현재 계층으로 과거 데이터 집계 ("현재 조직 기준 작년 매출")
- **As-Was** — 당시 계층으로 당시 데이터 집계 ("작년 조직 그대로 작년 매출")
- SCD Type 2 + 계층의 effective dating 필수

**Alternate Hierarchies (대체 계층)**:
- 같은 마스터를 여러 계층으로 분류 (예: 제품을 회계 분류 / 영업 분류 / 물류 분류)
- 각 계층은 독립 effective date

**장점**:
- 시점 정합성 보장 (As-Was 보고)
- 다관점 분석 (Alternate Hierarchies)
- 조직 개편 / 분류 변경 시 과거 보고서 안정

**단점·trade-off**:
- 쿼리 복잡도 증가 (재귀 / Bridge Join)
- 저장 비용 (SCD Type 2 의 행 증가)
- Reorg 시 계층 재계산 (Closure Table 의 trigger 부담)

**실제 도구**:
- **SAP MDG** — Active Hierarchies (Type 2 + alternate)
- **Reltio** — Multi-Hierarchy + temporal
- **Snowflake / BigQuery** — `CONNECT BY` / 재귀 CTE 지원
- **dbt** — SCD Type 2 매크로 (`dbt_utils.slowly_changing_dimension`)
- **Apache Hive / Iceberg** — Time Travel (snapshot) 으로 As-Was 보고

**Kotlin 예제 — Ragged Hierarchy + SCD Type 2 조회**:
```kotlin
data class OrgUnit(
    val unitId: String,
    val name: String,
    val parentId: String?,    // ragged — null 가능
    val effectiveFrom: LocalDate,
    val effectiveTo: LocalDate?,  // null = 현재
    val isCurrent: Boolean
)

class HierarchyService(private val repo: OrgUnitRepository) {
    // As-Was 조회 — 특정 시점의 계층
    fun ancestorsAsOf(unitId: String, asOf: LocalDate): List<OrgUnit> {
        val chain = mutableListOf<OrgUnit>()
        var current = repo.findValidAt(unitId, asOf) ?: return emptyList()
        chain += current
        while (current.parentId != null) {
            current = repo.findValidAt(current.parentId!!, asOf) ?: break
            chain += current
        }
        return chain
    }

    // 현재 계층의 As-Is 조회
    fun ancestorsAsIs(unitId: String): List<OrgUnit> =
        ancestorsAsOf(unitId, LocalDate.now())
}
```

**관련 패턴**: [Reference Data Management](#mdm-reference-data) — 분류 코드 자체의 계층, [Golden Record](#mdm-golden-record) — 마스터 엔터티의 계층 소속, [`data-modeling.md#cdc`](../../../dev-advisor/references/patterns/data-modeling.md#cdc) — SCD 변경 캡처. 데이터 품질 차원 *Timeliness* 와 결합은 [`data-quality-governance.md`](data-quality.md) 참조.

---

## MDM 도구 비교 매트릭스

오픈소스 / 상용 MDM 플랫폼의 도메인 강점, 통합 패턴, Stewardship 지원, 매칭 엔진 비교. Gartner *Magic Quadrant for Master Data Management* (2024) + Forrester Wave + 자체 조사 종합.

| 도구 | 라이선스 | 도메인 강점 | 통합 패턴 | 매칭 엔진 | 계층 지원 | Stewardship UI |
|------|---------|------------|----------|----------|---------|----------------|
| **SAP MDG** | 상용 | Customer / Material / Supplier / Finance (SAP ECC/S4 통합) | Centralized + Coexistence | 룰 기반 + Fuzzy | Active Hierarchies | Fiori UX |
| **Informatica MDM** | 상용 | Customer 360 / Multi-Domain | All 4 styles | Identity Resolution Engine (Probabilistic) | Multi-tree | Provisioning Tool |
| **Reltio** | 상용 SaaS | Connected Customer / Life Sciences | Cloud-Native + API-first | Graph + ML | Multi-Hierarchy | Modern UX |
| **IBM InfoSphere MDM** | 상용 | Healthcare (Patient 360) / Banking | Registry → Centralized | Probabilistic (PME) | Yes | Initiate UI |
| **TIBCO EBX** | 상용 | Reference Data + MDM 통합 | Hub + 모델 자유도 | 룰 + Fuzzy | Excellent | Web Studio |
| **Talend MDM** | 상용 (구 오픈소스) | ETL 통합 | Coexistence | Survivorship Rule Configurator | Yes | Talend Web UI |
| **Pimcore PIM** | 오픈소스 GPL | Product Information (PIM) 특화 | Centralized | 룰 기반 | Yes | Symfony UI |
| **Apache Unomi (CXS)** | 오픈소스 Apache | Customer Experience (CDP 성격) | Registry | 룰 | Limited | API |
| **Apache Atlas** | 오픈소스 Apache | Metadata Governance + Lineage | Catalog | N/A (메타 only) | Classification | Web UI |
| **DataHub (LinkedIn)** | 오픈소스 Apache | Catalog + Discovery | Federated | N/A (메타 only) | Yes (Domains/Tags) | React UI |
| **Amundsen (Lyft)** | 오픈소스 Apache | Data Discovery | Federated | N/A | Limited | Flask UI |
| **OpenMetadata** | 오픈소스 Apache | Catalog + Governance (Atlas/Amundsen 대안) | Federated | N/A | Yes | Modern UX |
| **Splink** | 오픈소스 MIT | Record Linkage 엔진 (MDM 부품) | Engine only | Fellegi-Sunter + Spark | N/A | N/A |
| **Zingg** | 오픈소스 AGPL | ML 기반 Entity Resolution | Engine only | ML (active learning) | N/A | CLI |

**선택 결정 트리**:
1. **Product Information 중심** → Pimcore (오픈소스) / SAP MDG (SAP 환경) / Stibo STEP
2. **Customer 360 중심** → Reltio (Cloud) / Informatica MDM (On-prem) / IBM (Healthcare)
3. **Reference Data 중심** → Collibra RDM / TIBCO EBX / TopBraid RDM
4. **Metadata Catalog (MDM 아님, 거버넌스 보조)** → DataHub / OpenMetadata / Atlas / Amundsen ([`data-quality-governance.md`](data-quality.md) 의 Catalog 항목 참조)
5. **매칭 엔진만 필요** (자체 MDM 구축) → Splink (Fellegi-Sunter) / Zingg (ML) / Dedupe.io
6. **오픈소스 우선** → Pimcore + Apache Atlas + Splink 조합

**Open Source vs Commercial Trade-off**:

| 축 | 오픈소스 | 상용 |
|---|---------|------|
| 초기 비용 | 낮음 (라이선스 0) | 높음 (수억 라이선스) |
| 운영 비용 | 높음 (자체 운영 / 컨설팅) | 낮음 (벤더 지원) |
| 매칭 정확도 | 자체 튜닝 필요 | OOTB 엔진 우수 |
| 도메인 모델 자유도 | 높음 | 중간 (벤더 메타모델) |
| 거버넌스 / Stewardship UI | 부족 (자체 구축) | 우수 |
| 컴플라이언스 (감사 / SOX) | 자체 인증 | 벤더 인증 |
| 적합 조직 | 데이터 엔지니어 인력 풍부 / 도메인 특수 | 거버넌스 우선 / 빠른 도입 |

---

## 한 줄 요약

MDM 6 패턴은 **Golden Record 를 생성·유지하는 파이프라인의 6 단계**: ① SSoT 정의 → ② Survivorship 규칙으로 필드별 값 결정 → ③ Match-Merge 로 동일 엔터티 통합 → ④ Data Steward 가 정책·예외 관리 → ⑤ Reference Data 로 분류 / 표준 정렬 → ⑥ Hierarchy + SCD 로 시간·다관점 정합성 보존. DMBOK 2 KA 10 + ISO 8000 + Fellegi-Sunter 가 표준 이론이며, 도구는 도메인(Product/Customer/Reference) 과 통합 스타일(Registry/Coexistence/Centralized) 로 선택한다. 데이터 품질 차원·거버넌스 RACI 는 [`data-quality-governance.md`](data-quality.md), 분산 일관성·CDC 는 [`data-modeling.md`](../../../dev-advisor/references/patterns/data-modeling.md), ACID/정규화 이론은 [`../principles/database-fundamentals.md`](../principles/db-fundamentals.md), Hierarchy 시간 차원 SCD 의 DWH 구현은 [`data-warehousing-bi.md#scd-types`](data-warehousing.md#scd-types) (P1 신설) 참조.
