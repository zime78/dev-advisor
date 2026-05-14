# Sustainable / Green Software (지속가능 SW)

Green Software Foundation 표준 8 핵심 원칙. **탄소 효율** + **에너지 효율** + **하드웨어 효율** 3 축에서 SW 운영 영향을 측정·감축.

**원전·표준 참고**:
- Green Software Foundation — *Principles of Green Software Engineering* (https://learn.greensoftware.foundation)
- Asim Hussain et al. — *Software Carbon Intensity Specification* (ISO/IEC 21031:2024)
- The Carbon Aware SDK (https://github.com/Green-Software-Foundation/carbon-aware-sdk)
- WattTime / electricityMap — 실시간 grid carbon intensity API
- Microsoft — *Sustainability Cloud* (2024)
- Akamai — *Edge Carbon Reporting*
- *Cloud Carbon Footprint* (open source, https://www.cloudcarbonfootprint.org)

**핵심 원칙 (Green Software Foundation)**:
- **Carbon efficiency** — emit less per unit work
- **Energy efficiency** — use less energy per work
- **Carbon awareness** — do more when electricity is cleaner
- **Hardware efficiency** — emit less embodied carbon
- **Measurement** — what you can measure, you can improve

**SCI 공식 (ISO/IEC 21031)**:

```
SCI = ((E * I) + M) per R

E = Energy consumed (kWh)
I = Carbon intensity (gCO2eq/kWh)
M = Embodied emissions (gCO2eq)
R = Functional unit (per request / per user / per device)
```

**관련 카탈로그**:
- [12-factor.md](12-factor.md) — Disposability, Concurrency (efficiency 와 연관)
- [`../patterns/finops.md`](../patterns/finops.md) — Cost ↔ Carbon (강한 상관)
- [`../patterns/caching.md`](../patterns/caching.md) — Edge cache (전송 감축)
- [`../algorithms/concurrent.md`](../algorithms/concurrent.md) — Efficient concurrency

---

<a id="1-carbon-aware-computing"></a>

## 1. Carbon-Aware Computing (탄소 인지 컴퓨팅)

**정의**: 전력 grid 의 *carbon intensity* (gCO2eq/kWh) 가 시간·지역별로 다르다는 사실을 이용해, *깨끗한 전력이 풍부할 때 / 풍부한 곳* 에서 작업을 수행하도록 스케줄링하는 운영 방식. "Do more when the grid is clean, do less when it is dirty."

**메커니즘**:
- WattTime / electricityMap / ENTSO-E 등의 실시간 grid intensity API 를 조회
- 마감 시한이 느슨한(non-urgent) 작업을 *저탄소 윈도우* 로 이동
- 멀티 리전 배포 시 그 시각 가장 깨끗한 리전으로 라우팅
- Carbon-Aware SDK (Green Software Foundation) 가 forecast / current / best-window 3 종 API 제공

**측정 방법**:
- baseline: 기존 24h 평균 intensity 로 곱한 작업당 배출량
- after: 실제 실행 시각·리전의 intensity 로 곱한 배출량
- 감축률 = `(baseline - after) / baseline * 100%`
- 일반적으로 **15~40% 감축** 보고 (Microsoft Xbox 업데이트 사례)

**장점**:
- 코드 로직 변경 없이 **스케줄링만으로** 탄소 감축
- 비용에도 종종 유리 (peak 시간 회피 → 스팟·off-peak 가격)
- Net-Zero 목표 보고에 직접 기여

**한계·trade-off**:
- 실시간 / 지연 민감 작업(API, 채팅, 결제) 에는 적용 불가
- 사용자가 multi-region 으로 흩어지면 데이터 sovereignty / latency 충돌
- intensity API 자체에 API 호출 비용 발생 (캐싱 필요)

**실무 적용**: ML 학습, batch ETL, 백업, 인덱싱, 영상 인코딩, 이메일 발송, 리포트 생성, 컨테이너 이미지 빌드.

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```kotlin
// Carbon Aware SDK 호출 (REST API) — 가장 깨끗한 1 시간 윈도우 찾기
data class CarbonWindow(val start: Instant, val end: Instant, val intensityGco2PerKwh: Double)

suspend fun findGreenestWindow(
    region: String,           // e.g. "eastus", "westeurope"
    durationHours: Int = 1,
    deadlineHours: Int = 24,
): CarbonWindow {
    val now = Instant.now()
    val deadline = now.plus(deadlineHours.toLong(), ChronoUnit.HOURS)
    val resp = httpClient.get(
        "https://carbon-aware-api/emissions/forecasts/current" +
        "?location=$region&windowSize=$durationHours&dataStartAt=$now&dataEndAt=$deadline"
    )
    val best = resp.body<List<ForecastDto>>().minBy { it.value }
    return CarbonWindow(best.timestamp, best.timestamp.plus(durationHours.toLong(), ChronoUnit.HOURS), best.value)
}

// 사용 예: 야간 백업을 가장 깨끗한 시간대로 미루기
val window = findGreenestWindow(region = "westeurope", durationHours = 2, deadlineHours = 8)
scheduler.scheduleAt(window.start) { runDatabaseBackup() }
```

**관련 항목**: [Demand Shifting](#6-demand-shifting), [Region-aware Deployment](#5-region-aware-deployment), [SCI](#4-sci-software-carbon-intensity).

---

<a id="2-energy-efficiency"></a>

## 2. Energy Efficiency (에너지 효율)

**정의**: 단위 작업당 *소비 에너지(J 또는 kWh)* 를 최소화. 같은 결과를 더 적은 CPU/GPU 사이클·메모리 access·네트워크 호출로 달성하는 것.

**메커니즘**:
- 알고리즘 복잡도 / 데이터 구조 선택 (O(N²) → O(N log N))
- 언어·런타임 효율 (C/Rust/Go > JVM > Python — 동일 작업 기준 5~50배 차이, *Energy Efficiency across Programming Languages* 2017)
- 컴파일 최적화 (link-time optimization, profile-guided optimization)
- I/O 배치 / 메모리 할당 최소화 / 캐시 친화 layout
- 불필요한 polling 제거, event-driven 으로 전환

**측정 방법**:
- **RAPL** (Intel Running Average Power Limit) — `perf stat -e power/energy-pkg/`
- **NVIDIA NVML** — `nvidia-smi --query-gpu=power.draw`
- **Cloud Carbon Footprint** — 시간당 vCPU·메모리·스토리지·네트워크 사용량 → kWh 추정
- **Joule/op** = 총 Joule / 처리 건수

**장점**:
- 탄소·비용·하드웨어 수명 3 가지를 동시 개선
- 사용자 단말(모바일/IoT) 의 *배터리 수명* 직접 향상
- 데이터센터 PUE / 냉각 부담 감소

**한계·trade-off**:
- 최적화 비용 (개발자 시간) vs 절감 효과 trade-off — Pareto 80/20 적용
- 가독성·유지보수성 희생 위험 — premature optimization 경계
- 언어 교체 비용 vs 절감 효과는 long-term 으로만 회수

**실무 적용**: hot-path 프로파일링 후 상위 5% 함수 집중 최적화, polling → push, JSON → 바이너리 직렬화(protobuf), debug log 제거, lazy initialization.

**난이도**: 중간~높음 | **사용 빈도**: ★★★★★

```kotlin
// 비효율: 매 요청마다 전체 리스트 정렬 (O(N log N) 반복)
fun topItemsInefficient(items: List<Item>, k: Int): List<Item> =
    items.sortedByDescending { it.score }.take(k)   // 매번 N log N

// 효율: heap 으로 top-k 만 유지 (O(N log k))
fun topItemsEfficient(items: List<Item>, k: Int): List<Item> {
    val heap = PriorityQueue<Item>(compareBy { it.score })
    for (item in items) {
        if (heap.size < k) heap.offer(item)
        else if (item.score > heap.peek().score) { heap.poll(); heap.offer(item) }
    }
    return heap.toList().sortedByDescending { it.score }
}
// 1M items, k=10 기준 ~20배 빠름 → 대략 같은 비율로 에너지 감소
```

**관련 항목**: [Hardware Efficiency](#3-hardware-efficiency), [SCI](#4-sci-software-carbon-intensity), [`../algorithms/`](../algorithms/index.md) (알고리즘 선택).

---

<a id="3-hardware-efficiency"></a>

## 3. Hardware Efficiency (하드웨어 효율 / Embodied Carbon)

**정의**: 하드웨어 *제조·운송·폐기* 단계에서 발생한 *내재 탄소(embodied carbon, M)* 를 분산·감축. 단순히 운영 중 전력만이 아니라 "이 칩을 만들 때 배출된 탄소"를 작업 단위에 분배해 본다.

**메커니즘**:
- 하드웨어 수명 연장 (refresh cycle 3년 → 5년 / 7년)
- 한 장비에 더 많은 워크로드 packing (utilization ↑ → M/R ↓)
- 사용자 단말 다양성 지원 (구형 디바이스 호환 → 교체 강요 회피)
- 회수·refurbish 프로그램, 부품 표준화로 재사용 촉진
- e-waste 절감 (재활용 가능 부품 우선)

**측정 방법**:
- **Embodied carbon per device** — 제조사 PCF (Product Carbon Footprint) 보고서 (Dell, HP, Apple, AWS 공개)
- **Amortized M** = `M_total / (lifespan_years * usage_factor)`
- SCI 공식의 **M 항목** — 예: AWS m6i 인스턴스 1 시간당 약 6~30 gCO2eq embodied (Cloud Carbon Footprint 데이터)
- 클라이언트 측: 앱이 N 년 이상 된 디바이스에서도 동작하는가? 평균 사용자 디바이스 교체 주기?

**장점**:
- 데이터센터 전체 탄소의 **30~70%** 가 embodied — 운영 전력만큼 큰 비중 (Apple Carbon Report, Microsoft Sustainability Report)
- 비용·공급망 안정성 개선
- ESG 보고에 직접 반영 (Scope 3)

**한계·trade-off**:
- 구형 하드웨어 보존 ↔ 최신 칩의 운영 효율 (효율 격차가 클 때는 교체가 오히려 친환경)
- 클라이언트 호환성 유지 비용 (구형 OS / 저성능 디바이스 테스트)
- 클라우드 사용자는 M 을 직접 통제하기 어려움 — 클라우드사 공시에 의존

**실무 적용**: serverless / FaaS 로 utilization ↑, 멀티 테넌시 / 컨테이너 packing, 모바일 앱의 minimum OS 버전 신중히 결정 (iOS 14+, Android 7+ 정도로 폭넓게 유지), Progressive Web App 으로 OS 다양성 흡수.

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

```kotlin
// SCI 공식의 M 항목 계산 — 인스턴스 시간당 embodied 분배
data class HardwareSpec(
    val totalEmbodiedGco2: Double,      // 제조사 PCF (e.g. 1200 kg CO2eq)
    val expectedLifespanHours: Long,    // 4 years * 365 * 24 = 35040
    val utilizationFactor: Double,      // 0.0 ~ 1.0 (공유 정도)
)

fun embodiedPerHour(spec: HardwareSpec): Double =
    (spec.totalEmbodiedGco2 * 1000.0) / (spec.expectedLifespanHours * spec.utilizationFactor)
//  ^ kg -> g 변환

// 예: AWS m6i.large, 4 년 수명, 0.25 utilization (4 VM packing)
val server = HardwareSpec(
    totalEmbodiedGco2 = 1200.0,
    expectedLifespanHours = 35_040L,
    utilizationFactor = 0.25,
)
val mPerHour = embodiedPerHour(server)  // ~137 gCO2eq/hour
// → utilization 0.5 로 올리면 절반(~68) — packing 의 직접 효과
```

**관련 항목**: [SCI](#4-sci-software-carbon-intensity), [Energy Efficiency](#2-energy-efficiency), [`../patterns/finops.md`](../patterns/finops.md) (right-sizing).

---

<a id="4-sci-software-carbon-intensity"></a>

## 4. Software Carbon Intensity (SCI) — ISO/IEC 21031

**정의**: Green Software Foundation 이 정의하고 ISO/IEC 21031:2024 로 표준화된 *SW 탄소 강도 메트릭*. **단위 작업당 탄소 배출량** (gCO2eq per functional unit). 절대값이 아니라 *비율(rate)* 이라는 점이 핵심 — 더 큰 시스템이 항상 더 나쁜 게 아니라 *효율* 을 본다.

**공식**:

```
SCI = ((E * I) + M) per R

E = Operational energy consumed (kWh)
I = Location-based marginal carbon intensity (gCO2eq/kWh)
M = Embodied emissions of the hardware (gCO2eq, amortized to time window)
R = Functional unit — per request / per API call / per user / per device-hour
```

**메커니즘**:
- 명확한 *boundary* (예: 한 API 서비스, 한 ML 모델 추론 파이프라인)
- *functional unit (R)* 정의 — 가장 비교 가능한 단위 선택 (request, user, transaction)
- E / I / M 각각을 실측 또는 표준 데이터셋(electricityMap, Cloud Carbon Footprint)에서 가져옴
- 같은 boundary·같은 R 단위로 *시계열 추적*. SCI 값이 줄어드는 방향이 개선

**측정 방법**:
- **E**: 클라우드 청구서의 vCPU 시간 × 코어 wattage 추정, RAPL/NVML 실측
- **I**: 리전·시간대별 carbon intensity (real-time grid 데이터)
- **M**: 인스턴스의 amortized embodied (Cloud Carbon Footprint, AWS Customer Carbon Footprint Tool, Azure Emissions Impact Dashboard)
- **R**: 메트릭 시스템에서 가져옴 (Prometheus request_total 등)

**장점**:
- 표준화된 비교 단위 — 팀·서비스·릴리스 간 객관적 비교
- offset / RECs 가 *공식에 포함되지 않음* → "그린워싱" 방지 (실제 감축만 인정)
- DevOps KPI 처럼 *지속 추적* 가능

**한계·trade-off**:
- 측정 정확도 한계 — E·I·M 모두 추정치, 실측 인프라 구축 비용
- M 데이터를 클라우드 사용자가 직접 얻기 어려움 (제공사 공시 의존)
- R 단위가 달라지면 비교 불가 — 정의 일관성 유지가 어려움

**실무 적용**: 핵심 서비스마다 SCI 대시보드, CI 단계에서 새 릴리스의 SCI 회귀 차단, 기능 추가 시 *SCI budget* 도입.

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

```kotlin
// SCI = ((E * I) + M) / R  구현 — 시간 윈도우 한 단위 기준
data class SciInputs(
    val energyKwh: Double,           // E
    val carbonIntensityGco2: Double, // I  (gCO2eq/kWh)
    val embodiedGco2: Double,        // M  (amortized to same window)
    val functionalUnits: Long,       // R  (e.g. requests served)
)

data class SciResult(val scoreGco2PerUnit: Double, val opsGco2: Double, val embGco2: Double)

fun computeSci(inputs: SciInputs): SciResult {
    require(inputs.functionalUnits > 0) { "R must be > 0" }
    val opsEmissions = inputs.energyKwh * inputs.carbonIntensityGco2   // (E * I)
    val total = opsEmissions + inputs.embodiedGco2                     // + M
    return SciResult(
        scoreGco2PerUnit = total / inputs.functionalUnits,
        opsGco2 = opsEmissions,
        embGco2 = inputs.embodiedGco2,
    )
}

// 예: 한 API 서비스, 1 시간 윈도우
val r = computeSci(SciInputs(
    energyKwh = 0.42,              // 측정/추정
    carbonIntensityGco2 = 320.0,   // 그 시간대 그 리전
    embodiedGco2 = 137.0,          // amortized
    functionalUnits = 120_000L,    // 1h 요청 수
))
println("SCI = ${r.scoreGco2PerUnit} gCO2eq/request")
// → 회귀 감지: 다음 릴리스 SCI 가 5% 이상 악화 시 CI fail
```

**관련 항목**: 모든 다른 7 원칙은 SCI 의 E·I·M·R 중 하나를 개선하는 수단. 특히 [Energy Efficiency](#2-energy-efficiency) (E), [Carbon-Aware](#1-carbon-aware-computing) (I), [Hardware Efficiency](#3-hardware-efficiency) (M).

---

<a id="5-region-aware-deployment"></a>

## 5. Region-aware Deployment (지역 인지 배포)

**정의**: 클라우드 리전별 *전력 mix* 차이를 활용. 같은 워크로드라도 리전 carbon intensity 가 10배 이상 차이 — 저탄소 지역(수력·원자력·풍력 중심)을 우선 선택.

**메커니즘**:
- 리전 후보 별 연평균 carbon intensity 비교
- 데이터 sovereignty / latency / 비용 제약과 trade-off
- 멀티 리전 active-active 시 가중치를 carbon intensity 로 조정
- 정적(연평균) 선택 + 동적(실시간) 라우팅 두 layer

**측정 방법**:
- **electricityMap** annual averages — 2024 기준 대표값:
  - 매우 깨끗 (< 50 gCO2/kWh): Iceland, Quebec (캐나다), Sweden, Norway, Switzerland, France (원자력)
  - 깨끗 (50~200): UK, Spain, Brazil 일부, Pacific Northwest (Oregon, BC)
  - 중간 (200~400): 미국 평균, 독일, 일본
  - 더러움 (400~700): 인도, 중국 일부, 호주, 폴란드
  - 매우 더러움 (> 700): 일부 석탄 의존 지역
- AWS Sustainability Pillar — "us-west-2 (Oregon), eu-north-1 (Stockholm), ca-central-1 (Montreal)" 권장
- Azure Emissions Impact Dashboard 의 리전별 비교

**장점**:
- 단일 결정으로 **5~10배** 탄소 감축 가능 (Stockholm vs Mumbai)
- 정적 결정이라 운영 복잡도 낮음
- 비용·latency 함께 최적화 가능한 경우 많음 (북유럽 = 저렴한 전기)

**한계·trade-off**:
- 데이터 sovereignty (GDPR / 한국 개인정보) — 한국 사용자 데이터를 Stockholm 으로 못 보낼 수 있음
- Latency — 사용자 위치에서 멀어지면 UX 손해
- 리전별 서비스 가용 차이 (모든 리전이 모든 SaaS 제공 X)

**실무 적용**: 배치 / 데이터 가공 / ML 학습은 깨끗한 리전 우선, latency-critical edge 는 사용자 근처. 한국 서비스라면 KR/JP 중 JP (원자력 비중) 가 KR (석탄 비중)보다 낮은 carbon — 단 데이터 sovereignty 점검 필요.

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★☆

```yaml
# Terraform — 카본 인지 리전 선택
# 컴플라이언스(데이터 거주) 통과 후보 중 가장 깨끗한 리전을 우선
locals {
  candidate_regions = [
    { name = "eu-north-1",    annual_gco2_per_kwh =  30, latency_ms_seoul = 280 },  # Stockholm 수력
    { name = "ca-central-1",  annual_gco2_per_kwh =  35, latency_ms_seoul = 180 },  # Montreal 수력
    { name = "us-west-2",     annual_gco2_per_kwh = 120, latency_ms_seoul = 130 },  # Oregon 풍력
    { name = "ap-northeast-2",annual_gco2_per_kwh = 430, latency_ms_seoul =  10 },  # Seoul (석탄 비중)
  ]
  # 배치 워크로드: latency 무관 → 최저 carbon
  batch_region = local.candidate_regions[index(local.candidate_regions.*.annual_gco2_per_kwh,
    min(local.candidate_regions.*.annual_gco2_per_kwh...))].name
  # 실시간 API: latency 200ms 이내 중 최저 carbon
  api_region = "ca-central-1"  # 한국 사용자에 latency 가용 + 저탄소
}
```

**관련 항목**: [Carbon-Aware Computing](#1-carbon-aware-computing), [Demand Shifting](#6-demand-shifting), [`../patterns/finops.md`](../patterns/finops.md).

---

<a id="6-demand-shifting"></a>

## 6. Demand Shifting (수요 이동 / Temporal & Spatial)

**정의**: *시간* 또는 *공간* 축으로 작업을 옮겨 더 깨끗한 전력에 맞추는 것. Carbon-Aware Computing 의 실행 패턴 — "더 깨끗할 때까지 / 더 깨끗한 곳으로 미룬다".

**메커니즘**:
- **Temporal shifting**: 작업 마감 시한 내에서 grid 가 가장 깨끗한 시점으로 이동 (예: 야간 풍력 풍부 시간대)
- **Spatial shifting**: 같은 시각이지만 더 깨끗한 리전으로 작업 이동 (예: 유럽 batch 를 Stockholm 으로)
- 사전 조건: 작업이 *지연 허용* (deadline > now + epsilon) + *위치 가변* (데이터 거주 통과)
- 스케줄링: cron + carbon intensity API → "다음 24h 중 최저 intensity 시간대"

**측정 방법**:
- baseline: 즉시 실행했을 때 배출량
- shifted: 실제 실행 시각·리전 배출량
- 감축률 보고 — Microsoft Xbox 업데이트: **~30%**, Google ML 학습: **~40%** 보고 사례

**장점**:
- 코드 거의 변경 없이 스케줄러만 교체
- 비용 동반 절감 가능 (off-peak / 스팟 가격)
- 명확한 KPI 측정 가능

**한계·trade-off**:
- 실시간성 요구 작업 적용 불가
- 사용자에게 일관된 작업 시작 시각 제공 불가 (UX 분산)
- intensity forecast 오류 시 의도와 다른 시간대 실행

**실무 적용**: 야간 배치 ETL, ML 학습/하이퍼파라미터 탐색, 백업, 영상 트랜스코딩, 정기 리포트, 이메일 캠페인 발송.

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```kotlin
// Temporal + Spatial 결합 demand shifting
data class ShiftCandidate(
    val region: String,
    val startAt: Instant,
    val forecastGco2PerKwh: Double,
    val estimatedKwh: Double,
) {
    val expectedEmissionsG: Double get() = forecastGco2PerKwh * estimatedKwh
}

suspend fun pickBestSlot(
    workEnergyKwh: Double,
    deadline: Instant,
    candidateRegions: List<String>,
    isAllowedRegion: (String) -> Boolean,  // 데이터 sovereignty 게이트
): ShiftCandidate {
    val now = Instant.now()
    val candidates = candidateRegions
        .filter(isAllowedRegion)
        .flatMap { region ->
            val forecasts = carbonApi.forecast(region, from = now, to = deadline, windowH = 1)
            forecasts.map { ShiftCandidate(region, it.start, it.value, workEnergyKwh) }
        }
    return candidates.minBy { it.expectedEmissionsG }
}

// 사용: 8h 내, EU 리전만 허용, 즉시 실행 대비 감축률 보고
val best = pickBestSlot(
    workEnergyKwh = 5.0,
    deadline = Instant.now().plusSeconds(8 * 3600),
    candidateRegions = listOf("eu-north-1", "eu-west-1", "eu-central-1"),
    isAllowedRegion = { it.startsWith("eu-") },
)
scheduler.scheduleAt(best.startAt, region = best.region) { runEtl() }
```

**관련 항목**: [Carbon-Aware Computing](#1-carbon-aware-computing), [Region-aware Deployment](#5-region-aware-deployment), [Demand Shaping](#7-demand-shaping) (수요 자체를 변경).

---

<a id="7-demand-shaping"></a>

## 7. Demand Shaping (수요 형성 / Eco Mode)

**정의**: grid 가 더러울 때 *작업의 양과 품질을 사용자 동의 하에 줄여* 수요 자체를 변형. Shifting 이 "언제·어디서" 라면, Shaping 은 "얼마나·어떤 품질로" 의 축.

**메커니즘**:
- 사용자에게 carbon 상태를 노출하고 *low-carbon mode* 옵션 제공
- 자동 degradation: 고탄소 시간대에는 동영상 품질 1080p → 720p, ML 모델을 작은 distilled 버전으로
- 빈도 감축: 백그라운드 sync 주기 5분 → 30분
- 비핵심 기능 일시 비활성 (애니메이션, 자동 미리보기)
- *사용자 동의·투명성* 이 핵심 — 몰래 품질 떨어뜨리면 신뢰 깨짐

**측정 방법**:
- 사용자 채택률 (eco mode 켠 사용자 비율 / 자동 모드 미수정 비율)
- 기능별 SCI 감축률 (1080p → 720p 가 평균 carbon 을 몇 % 줄였는가)
- UX 메트릭 회귀 확인 (engagement, retention)

**장점**:
- 시간·공간 shifting 으로 못 줄이는 *실시간 워크로드* 의 carbon 도 줄임
- 사용자 참여형 — ESG 스토리텔링에 강함
- 비상 시 (grid 위기 / 정전 경고) 수요 제한 도구

**한계·trade-off**:
- UX 손상 위험 — 잘못 설계하면 사용자 이탈
- 측정 곡선이 복잡 (사용자 행동 변화 + carbon 양쪽 trace)
- 사용자 동의·디자인 가이드라인 필요 (BBC Sustainability Guidelines 참고)

**실무 적용**: 비디오 스트리밍의 carbon-aware bitrate, ML 추론의 동적 모델 선택 (큰 모델 vs distilled), 모바일 앱의 다크 모드 권장 (OLED 디스플레이 에너지 감축), 백그라운드 sync 간격 조정.

**난이도**: 중간~높음 | **사용 빈도**: ★★★☆☆

```kotlin
// Demand Shaping — 그리드 상태 기반 동적 품질 조정 (사용자 동의 전제)
enum class CarbonState { GREEN, YELLOW, RED }   // < 200 / 200~500 / > 500 gCO2/kWh

fun decideVideoQuality(
    userPref: String,                  // "auto" / "1080p" / "720p"
    state: CarbonState,
): String = when {
    userPref != "auto" -> userPref     // 사용자 명시 선택은 존중
    state == CarbonState.GREEN -> "1080p"
    state == CarbonState.YELLOW -> "720p"
    state == CarbonState.RED -> "480p"
}

fun decideSyncIntervalMinutes(state: CarbonState): Int = when (state) {
    CarbonState.GREEN -> 5
    CarbonState.YELLOW -> 15
    CarbonState.RED -> 60
}

// UI 가 사용자에게 carbon state 와 적용된 결정을 *투명하게* 노출
data class EcoModeStatus(
    val state: CarbonState,
    val appliedQuality: String,
    val appliedSyncMinutes: Int,
    val estimatedReductionPct: Double,  // 사용자에게 보이는 "기여도"
)
```

**관련 항목**: [Demand Shifting](#6-demand-shifting), [Energy Efficiency](#2-energy-efficiency), [Efficient Data Storage & Transmission](#8-efficient-data-storage) (낮은 화질 → 전송 감축).

---

<a id="8-efficient-data-storage"></a>

## 8. Efficient Data Storage & Transmission (효율적 데이터 저장·전송)

**정의**: 데이터의 *저장(at rest)* 과 *전송(in transit)* 양 축에서 탄소를 감축. 저장은 hot/warm/cold tiering + lifecycle policy + 보존 기간 관리, 전송은 압축 + CDN edge cache + payload 다이어트.

**메커니즘**:
- **Storage tiering**: hot (SSD) → warm (HDD) → cold (S3 IA / Glacier / Deep Archive) → 만료 삭제
- **Lifecycle policy**: 90 일 후 자동 cold, 365 일 후 삭제 — 데이터 보존 정책과 결합
- **압축**: gzip(레거시) → zstd / brotli, 이미지 JPEG → WebP / AVIF, 동영상 H.264 → H.265 / AV1
- **CDN edge cache**: origin 요청 감소 → 데이터센터 전력 ↓ + 사용자 latency ↓
- **Payload 다이어트**: 불필요 필드 제거, 페이지네이션, GraphQL field selection, HTTP/2·3 헤더 압축
- **Image / video adaptive**: 디바이스·뷰포트별 적합 해상도 (`<picture>` `srcset`, HLS / DASH)
- **De-dup / chunking** — 클라우드 백업, 컨테이너 image layer

**측정 방법**:
- 스토리지 GB-월 × 클래스별 carbon factor (S3 Standard ~ 0.5 g/GB-mo, Glacier ~ 0.03 g/GB-mo, 추정치)
- CDN cache hit ratio (목표 > 90%)
- 평균 페이지 transfer size — Website Carbon Calculator (https://www.websitecarbon.com) 기준 < 1MB
- byte / 요청 — payload 분석 도구 (Lighthouse, WebPageTest)

**장점**:
- 비용·탄소·UX 3 가지를 동시 개선
- 큰 데이터 시스템(미디어 / 백업) 에서 절대값 효과 큼
- 신규 코드 적게 — 설정·정책 변경 위주

**한계·trade-off**:
- 압축 CPU 비용 (zstd / brotli 는 gzip 보다 더 무거움 — 단 ratio 도 좋음)
- Cold storage 의 retrieval 비용 / latency
- 캐시 무효화의 복잡도 증가
- 적극적 lifecycle 삭제는 *법적 보존 의무* 와 충돌 가능

**실무 적용**: S3 Lifecycle, CloudFront / Akamai cache key 튜닝, `Cache-Control` 헤더 정책 표준화, Brotli / Zstd 활성, modern image format 사용, 백업 압축·de-dup.

**난이도**: 중간 | **사용 빈도**: ★★★★★

```kotlin
// HTTP 응답 — modern compression + cache header + CDN edge
fun Application.installGreenHttp() {
    install(Compression) {
        // gzip 보다 ratio 좋은 brotli / zstd 우선
        encoder(BrotliEncoder, priority = 10.0, minSize = 1024)
        encoder(GzipEncoder, priority = 1.0, minSize = 1024)
    }
    install(ConditionalHeaders)   // 304 응답으로 body 재전송 방지
    install(CachingHeaders) {
        options { _, content ->
            when (content.contentType?.withoutParameters()) {
                // 정적 자원 — CDN long-cache, immutable
                ContentType.Image.Any -> CachingOptions(
                    cacheControl = CacheControl.MaxAge(maxAgeSeconds = 31_536_000, visibility = Public),
                )
                // 동적 API — 짧은 edge cache
                ContentType.Application.Json -> CachingOptions(
                    cacheControl = CacheControl.MaxAge(maxAgeSeconds = 60, visibility = Public),
                )
                else -> null
            }
        }
    }
}
```

```yaml
# S3 Lifecycle — hot → warm → cold → 만료
Rules:
  - Id: tier-down-then-expire
    Status: Enabled
    Filter: { Prefix: logs/ }
    Transitions:
      - Days:  30; StorageClass: STANDARD_IA       # warm
      - Days:  90; StorageClass: GLACIER_IR        # cold
      - Days: 180; StorageClass: DEEP_ARCHIVE      # archive
    Expiration: { Days: 730 }                       # 2 년 후 삭제 (보존 정책과 결합)
```

**관련 항목**: [Energy Efficiency](#2-energy-efficiency), [Demand Shaping](#7-demand-shaping), [`../patterns/caching.md`](../patterns/caching.md), [`../patterns/finops.md`](../patterns/finops.md).

---

### 원칙 간 의존 관계

8 원칙은 독립적이지 않다. 측정(SCI)이 모든 의사결정의 *공통 좌표계* 역할을 하고, 나머지 7 개는 SCI 공식의 어떤 항목을 줄이는지로 분류된다.

```
                    ┌─────────────────────────────────────┐
                    │     [4] SCI = ((E*I)+M) / R         │
                    │      (측정 · 공통 좌표계)            │
                    └──┬──────┬──────────┬──────────┬─────┘
                       │      │          │          │
              E 감축   │      │ I 감축   │ M 감축   │ R 형성
                       │      │          │          │
        ┌──────────────┘      └────┐     │          │
        ▼                          ▼     ▼          ▼
   [2] Energy           [1] Carbon-Aware   [3] Hardware   [7] Demand
   Efficiency           Computing          Efficiency     Shaping
        │                     │                │              │
        │                ┌────┴────┐           │              │
        ▼                ▼         ▼           ▼              ▼
   [8] Efficient    [5] Region- [6] Demand   embodied     UX/품질
   Storage &        aware       Shifting     packing      degradation
   Transmission     Deployment  (time+space) 수명         사용자 동의
```

핵심 관계:
- **측정(4) 없이 나머지 7 개는 검증 불가** — SCI 가 baseline 과 개선 효과를 정량화
- **(2) Energy + (8) Storage** → E 감축의 두 축 (계산·전송)
- **(1) Carbon-Aware** 이 (5) Region-aware (공간) + (6) Demand Shifting (시간) 의 상위 추상화
- **(7) Demand Shaping** 만 *사용자 동의* 가 전제 — 다른 7 개는 운영자 단독 결정 가능
- **(3) Hardware Efficiency** 는 클라우드 사용자가 직접 통제하기 어려움 — 공급사 PCF 의존

---

### 도입 단계 권장 순서

조직의 sustainability 여정은 보통 4 단계로 진행한다.

| 단계 | 목표 | 핵심 활동 | 기대 효과 |
|------|------|----------|----------|
| **1. Inventory** | 현재 배출량 측정 baseline 확보 | Cloud Carbon Footprint / AWS CCFT / Azure EID 활성, 주요 서비스 boundary 정의 | 객관적 출발점 |
| **2. Quick Wins** | 비용·탄소 동시 절감 | (8) Storage tiering, (5) Region 검토, idle 인스턴스 정리, (2) hot-path 최적화 | 10~30% 감축 |
| **3. Carbon-Aware** | 시간·공간 shifting 도입 | (1) Carbon-Aware SDK, (6) Demand Shifting, 배치 워크로드부터 시작 | 추가 10~40% |
| **4. SCI 거버넌스** | 회귀 방지 + 신기능 SCI budget | (4) CI 통합, 서비스별 대시보드, OKR 편입, (7) Demand Shaping 사용자 UX | 지속 가능한 개선 |

각 단계는 다음 단계로 가는 *전제* — Inventory 없이 Carbon-Aware 가면 효과 입증 불가. SCI 거버넌스는 1~3 단계 완료 후에야 의미 있음.

---

### 자주 마주치는 함정

| 함정 | 증상 | 원인 | 해결 |
|------|------|------|------|
| Carbon offset 으로 그린워싱 | 실제 emissions 감소 없이 RECs / offset 구매로 net-zero 주장 | SCI 가 offset 을 *공식에 포함하지 않음* 을 무시 | (4) SCI 메트릭으로 실제 감축만 추적, offset 은 별도 보고 |
| Latency · UX 희생 후폭풍 | Region 이동으로 사용자 체감 속도 저하 | (5) 적용 시 latency budget 미정의 | latency SLO 를 *동등 우선* 으로 명시, (1)(5) 결정 시 multi-objective 최적화 |
| 측정 자체가 carbon 소비 | 메트릭 수집 인프라가 너무 무거움 | Prometheus + 카본 API + ML 추정 모두 항상 켬 | 샘플링·집계 주기 조정, 메트릭 시스템도 SCI 측정 대상 |
| Premature optimization | 절감 효과 < 개발 비용 | (2) 적용 시 Pareto 무시 | Profile-first — hot-path 상위 5% 만 손댄다 |
| 데이터 sovereignty 위반 | 한국 사용자 데이터를 다른 리전으로 이동 후 컴플라이언스 위반 | (5)(6) 적용 시 거주성 게이트 누락 | 리전 후보를 *컴플라이언스 통과 집합* 으로 사전 필터 |
| 사용자 동의 없는 degradation | (7) 적용 시 몰래 화질 하락 → 신뢰 손상 | UX 디자인 가이드라인 부재 | Eco mode 토글 + 사용자에게 carbon 상태·결과 *투명* 노출 |
| Embodied 무시 | 운영 전력만 줄이고 H/W 교체 빈도 ↑ → 총 carbon 증가 | (3) 측정 누락 | refresh cycle 결정 시 amortized M 포함, 클라이언트 minimum-OS 보수적으로 |

---

### 8 원칙 컴플라이언스 체크리스트

| # | 원칙 | 검증 방법 | 1차 KPI |
|---|------|----------|---------|
| 1 | Carbon-Aware Computing | 작업의 N% 가 carbon-aware 스케줄러 경유 | shift 적용률, baseline 대비 감축률 |
| 2 | Energy Efficiency | Hot-path 프로파일 + Joule/op 계측 | kWh / 요청 |
| 3 | Hardware Efficiency | 인스턴스 utilization > X%, 디바이스 lifespan ≥ N년 | M / 요청 (amortized) |
| 4 | SCI | 주요 서비스마다 SCI 대시보드, CI 회귀 가드 | gCO2eq / functional unit |
| 5 | Region-aware Deployment | 컴플라이언스 통과 리전 중 최저 carbon 선택 근거 문서화 | 리전 연평균 carbon intensity |
| 6 | Demand Shifting | 지연 허용 작업의 N% 이상이 shifted | baseline 대비 emission 감축% |
| 7 | Demand Shaping | Eco mode 채택률, carbon-state 별 품질 분기 구현 | 사용자 옵트인율, 기능별 감축률 |
| 8 | Efficient Data Storage & Transmission | Lifecycle policy 적용률, CDN cache hit ratio | bytes / 요청, GB-mo / tier |

---

## 표준 인용

- Green Software Foundation, *Principles of Green Software Engineering* (https://learn.greensoftware.foundation)
- Asim Hussain et al., *Software Carbon Intensity Specification* — ISO/IEC 21031:2024
- Green Software Foundation, *Carbon Aware SDK* (https://github.com/Green-Software-Foundation/carbon-aware-sdk)
- *Cloud Carbon Footprint* (https://www.cloudcarbonfootprint.org) — 멀티 클라우드 carbon 추정 오픈소스
- WattTime (https://www.watttime.org), electricityMap (https://www.electricitymaps.com) — 실시간 grid intensity API
- Microsoft, *Sustainability Cloud* / Emissions Impact Dashboard (2024)
- AWS, *Sustainability Pillar — AWS Well-Architected Framework* (2024)
- Google Cloud, *Carbon Footprint Reporting* (2024)
- *Energy Efficiency across Programming Languages* — Pereira et al., SLE 2017
- BBC, *Sustainability in Design — Designing for a Greener Internet*
- Website Carbon Calculator (https://www.websitecarbon.com)
