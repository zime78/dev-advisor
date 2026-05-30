# Logistics / 배송 도메인 패턴 (Logistics & Delivery Patterns)

물류·배송·운송 산업 정평 있는 10 패턴. Uber Engineering / Lyft / Doordash / FedEx / 쿠팡 등 사례. **실시간 위치 + 라우팅 + 차량 배차** 가 핵심.

**원전·표준 참고**:
- Uber Engineering Blog — Dispatch / ETA / Map Matching
- Doordash Engineering — Dasher routing, Demand forecasting
- Toth & Vigo — *Vehicle Routing: Problems, Methods, and Applications* (2nd ed., 2014)
- Google Or-Tools — VRP 솔버
- ISO 27005 (운송 보안), GS1 EPCIS (Track & Trace 표준)

**핵심 비기능 요구**:
- **실시간 (Real-time)** — GPS event 수십만/초, 1s 미만 처리
- **공간 (Spatial)** — Geo-spatial index (R-Tree / H3 / Geohash) 필수
- **확장성 (Scalability)** — Fleet 수십만 + Demand 수백만 동시
- **신뢰성 (Reliability)** — 배송 실패 = 매출 손실, idempotent operation

**관련 카탈로그**:
- [`../../algorithms/graph.md`](../../algorithms/graph.md) — Dijkstra / A* / Floyd-Warshall (라우팅 본체)
- [`../../algorithms/matching.md`](../../algorithms/matching.md) — Hungarian / Stable Marriage (배차)
- [`../../algorithms/ml.md`](../../algorithms/ml.md) — ML 예측 (ETA, Demand)
- [`../observability.md`](../observability.md) — 실시간 트래킹 의 분산 트레이싱

---

## 패턴 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [vrp-route-optimization](#vrp-route-optimization) | Vehicle Routing Problem | 차량 라우팅 최적화 | 매우 높음 |
| [realtime-tracking](#realtime-tracking) | Real-time Tracking | 실시간 위치 추적 | 중간 |
| [eta-calculation](#eta-calculation) | ETA Calculation | 도착 예상 시간 계산 | 높음 |
| [geofencing](#geofencing) | Geofencing | 지오펜싱 | 중간 |
| [fleet-dispatch](#fleet-dispatch) | Fleet Dispatch / Driver Matching | 차량·기사 배차 | 높음 |
| [last-mile-delivery](#last-mile-delivery) | Last-Mile Delivery | 라스트 마일 배송 | 높음 |
| [reverse-logistics](#reverse-logistics) | Reverse Logistics | 역물류 (반품 회수) | 중간 |
| [multi-hop-cross-docking](#multi-hop-cross-docking) | Multi-Hop / Cross-Docking | 다단계 환적 / 크로스도킹 | 높음 |
| [capacity-planning](#capacity-planning) | Capacity Planning / Demand Forecasting | 수요 예측 / 캐파 플래닝 | 높음 |
| [track-and-trace](#track-and-trace) | Track & Trace (Chain of Custody) | 추적·관리 연속성 | 중간 |

---

<a id="vrp-route-optimization"></a>
## 1. VRP (Vehicle Routing Problem) / Route Optimization

**목적**: 단일 depot(또는 다중 depot)에서 출발한 여러 차량이 N 개의 배송지를 방문하고 복귀할 때, **총 이동 거리·시간·비용을 최소화** 하는 경로 집합을 결정합니다. TSP(Traveling Salesman Problem)의 다중 차량 확장.

**메커니즘**:
- **VRP 기본형**: M 대 차량 × N 배송지 → 각 배송지를 정확히 1 회 방문 + 차량별 depot 시작·종료
- **CVRP** (Capacitated VRP): 차량 적재 용량 제약 추가 (e.g. 트럭당 1000kg)
- **VRPTW** (VRP with Time Windows): 배송지별 시간 창 (e.g. 09:00~12:00) 제약
- **PDPTW** (Pickup and Delivery with TW): 픽업·배송 쌍 + 시간 창 (Uber/Doordash 형)
- **MDVRP** (Multi-Depot VRP): 여러 창고에서 출발

**알고리즘**:
| 접근 | 적용 규모 | 비고 |
|------|----------|------|
| Branch-and-Cut (정확해) | N < 50 | CPLEX / Gurobi |
| Savings Algorithm (Clarke-Wright) | N < 200 | Heuristic, 빠른 초기해 |
| Tabu Search / Simulated Annealing | N < 1000 | Metaheuristic |
| LNS (Large Neighborhood Search) | N < 10000 | Or-Tools 기본 전략 |
| Genetic Algorithm + Local Search | N < 5000 | 병렬화 용이 |

**장점**:
- 운영 비용 5~20% 절감 (UPS ORION 사례: 연간 1억 마일 절감)
- 차량 활용률 ↑, 운전자 피로 ↓
- 동적 재계획 가능 (Real-time VRP)

**단점·주의**:
- NP-hard — 정확해는 N 작을 때만 가능
- 실제 도로 거리 ≠ 직선 거리 → distance matrix 사전 계산 필요 (OSRM / Google Distance Matrix)
- Time window 위반 처리 정책 (hard / soft) 사전 결정
- 동적 환경(주문 추가, 차량 고장)에서 re-routing 비용 ↑

**Kotlin / pseudo-code 예제** (Google Or-Tools 호출):
```kotlin
import com.google.ortools.constraintsolver.*

class VrpSolver(
    private val distanceMatrix: Array<LongArray>,  // N x N (단위: meter)
    private val demands: IntArray,                  // 각 배송지 수요
    private val vehicleCapacities: LongArray,       // 차량별 용량
    private val depot: Int = 0,
) {
    fun solve(): List<List<Int>> {
        val manager = RoutingIndexManager(distanceMatrix.size, vehicleCapacities.size, depot)
        val routing = RoutingModel(manager)

        // 비용 함수 = 거리
        val transitCb = routing.registerTransitCallback { from, to ->
            val a = manager.indexToNode(from); val b = manager.indexToNode(to)
            distanceMatrix[a][b]
        }
        routing.setArcCostEvaluatorOfAllVehicles(transitCb)

        // 용량 제약
        val demandCb = routing.registerUnaryTransitCallback { idx ->
            demands[manager.indexToNode(idx)].toLong()
        }
        routing.addDimensionWithVehicleCapacity(
            demandCb, 0, vehicleCapacities, true, "Capacity"
        )

        val params = main.defaultRoutingSearchParameters().toBuilder()
            .setFirstSolutionStrategy(FirstSolutionStrategy.Value.PATH_CHEAPEST_ARC)
            .setLocalSearchMetaheuristic(LocalSearchMetaheuristic.Value.GUIDED_LOCAL_SEARCH)
            .setTimeLimit(com.google.protobuf.Duration.newBuilder().setSeconds(30).build())
            .build()

        val solution = routing.solveWithParameters(params) ?: error("No solution")
        return (0 until vehicleCapacities.size).map { v ->
            val route = mutableListOf<Int>()
            var idx = routing.start(v)
            while (!routing.isEnd(idx)) {
                route.add(manager.indexToNode(idx))
                idx = solution.value(routing.nextVar(idx))
            }
            route
        }
    }
}
```

**실무 팁**:
- Distance matrix 는 Haversine 직선거리로 시작하지 말고 **실제 도로 거리** 사용 — OSRM `/table` 또는 Google Distance Matrix
- 1000+ 배송지 규모는 **clustering 선처리** (k-means / DBSCAN) → 클러스터 단위 VRP → 글로벌 stitching
- 운전자 break time 은 별도 dimension 으로 모델링 (`addDimension` 으로 누적 운행 시간 추적 + slack)
- Cost 함수에 **fixed cost** (차량 구동 자체 비용) + **variable cost** (km 당 연료비) 분리
- 솔버 시간 한도 → "good enough fast" 가 "best slow" 보다 운영에서 유리

**관련 패턴·알고리즘**:
- `algorithms/graph.md` — Dijkstra / A* (distance matrix 사전 계산)
- `algorithms/dynamic-programming.md` — Held-Karp TSP (N < 20 정확해)
- [`fleet-dispatch`](#fleet-dispatch) (동적 배차 결과를 VRP 입력으로)
- [`capacity-planning`](#capacity-planning) (차량 수 결정)

---

<a id="realtime-tracking"></a>
## 2. Real-time Tracking (실시간 위치 추적)

**목적**: 운행 중인 차량·기사·화물의 GPS 좌표를 **수 초 단위로 수집·저장·조회** 하여 고객·관제 화면·VRP 재계산에 공급합니다.

**메커니즘**:
- **이벤트 인제스천**: 차량당 5~30s 간격 GPS 핑 → Kafka / MQTT broker
- **저장소 이중화**:
  - **Last Known Location** (Redis / DynamoDB): 차량 ID → 최신 위치 1 건 (조회 P99 < 10ms)
  - **Trail (Time-series)**: TimescaleDB / InfluxDB / S3 Parquet (감사·복기·분석)
- **압축**: Trail 은 Douglas-Peucker 알고리즘으로 단순화 (직선 구간 sparse 저장)
- **Map Matching**: Raw GPS → 실제 도로 segment 매핑 (Hidden Markov Model)

**장점**:
- 실시간 ETA 갱신 가능
- 분실·도난 추적
- 운행 패턴 분석 (idle time, 과속 등)
- 보험·법적 감사 증거

**단점·주의**:
- GPS drift (도심 협곡, 터널): Kalman Filter 또는 Map Matching 필수
- 배터리·데이터 비용 (모바일 단말): 적응형 샘플링 (정지 시 30s, 주행 시 5s)
- 개인정보(PII): 운행 외 시간 추적 금지, 보존 기간 정책 (GDPR / PIPA)
- Time-series cardinality 폭발: 차량 ID + 시간 → partition key 설계 주의

**Kotlin / pseudo-code 예제**:
```kotlin
data class GpsEvent(
    val vehicleId: String,
    val lat: Double, val lon: Double,
    val speedKmh: Float, val heading: Float,
    val timestamp: Instant,
)

class TrackingService(
    private val lastKnown: RedisClient,         // Hot path
    private val trailStore: TimescaleClient,    // Cold path
    private val mapMatcher: MapMatcher,
) {
    suspend fun ingest(event: GpsEvent) {
        // 1) Map Matching — 도로 segment 매핑 (선택)
        val matched = mapMatcher.snapToRoad(event.lat, event.lon) ?: event

        // 2) Hot path: 최신 위치만 덮어쓰기
        lastKnown.set(
            "veh:${event.vehicleId}",
            Json.encodeToString(matched),
            ttl = Duration.ofMinutes(5),
        )

        // 3) Cold path: trail 누적 (배치 flush)
        trailStore.appendAsync(matched)
    }

    suspend fun current(vehicleId: String): GpsEvent? =
        lastKnown.get("veh:$vehicleId")?.let { Json.decodeFromString(it) }

    suspend fun trail(vehicleId: String, from: Instant, to: Instant): List<GpsEvent> =
        trailStore.query(vehicleId, from, to)
}
```

**실무 팁**:
- Last Known Location 은 **Redis Hash** (`HSET veh:{id} lat ... lon ...`) — TTL 로 dead vehicle 자동 정리
- Trail Time-series 는 hot (24h, TimescaleDB) + warm (30d, S3 Parquet) + cold (1y, Glacier) 3-tier
- Douglas-Peucker `epsilon` = 10~20m (도시) / 50~100m (고속도로)
- 차량별 **device clock drift** 보정 — server 수신 시각도 함께 기록
- **Privacy by design** — 운행 종료 후 N 분 뒤 위치 추적 자동 중단 (운전자 사생활 보호)

**관련 패턴·알고리즘**:
- `algorithms/ml.md` — Kalman Filter (위치 노이즈 제거), HMM (map matching)
- [`eta-calculation`](#eta-calculation) (실시간 위치 → ETA 갱신 입력)
- [`geofencing`](#geofencing) (위치 변화 → 영역 진입/이탈 판정)
- `../observability.md` — 분산 트레이싱과 동일한 ingest pipeline

---

<a id="eta-calculation"></a>
## 3. ETA Calculation (도착 예상 시간)

**목적**: 출발지 → 목적지 도착 예상 시각을 **실제 교통 상황 + 과거 패턴 + 운전자 특성** 으로 보정해 산출합니다. Uber/Lyft/Doordash 의 핵심 신뢰 지표.

**메커니즘**:
- **레이어 구조**:
  1. **Baseline ETA** = 도로 그래프 + 자유속도 → Dijkstra/A* (수 ms)
  2. **Traffic-adjusted** = 현재 교통 속도(HERE/Google/Mapbox traffic API) 가중
  3. **ML-corrected** = Gradient Boosting (XGBoost / LightGBM) 잔차 학습
- **Feature**:
  - 시간 (요일·시각·휴일), 날씨, 출발지·목적지 클러스터
  - 운전자 평균 속도, 차종, 화물 무게
  - 실시간 traffic congestion score
- **Uncertainty Buffer**: P50 ETA + P90 buffer (e.g. "12~18 분")

**장점**:
- 고객 만족도 직결 (예측 vs 실제 차이가 핵심 KPI)
- 동적 가격(surge pricing) 입력
- VRP / 배차 의사결정 입력

**단점·주의**:
- 데이터 편향: 학습 시간대와 다른 시간대(새벽·심야)에서 정확도 ↓
- "Self-fulfilling prophecy" — ETA 가 너무 짧으면 무리한 주행 유발
- 라스트 마일(주차·엘리베이터·고객 응답)이 거시적 모델로 안 잡힘 → 별도 가산
- 모델 staleness: weekly 재학습 필요

**Kotlin / pseudo-code 예제**:
```kotlin
data class EtaRequest(
    val originLat: Double, val originLon: Double,
    val destLat: Double, val destLon: Double,
    val vehicleType: VehicleType,
    val departAt: Instant,
)

data class EtaResult(val p50Sec: Int, val p90Sec: Int)

class EtaService(
    private val router: RoadGraphRouter,
    private val trafficClient: TrafficApi,
    private val mlModel: GradientBoostingModel,  // XGBoost wrapper
) {
    suspend fun estimate(req: EtaRequest): EtaResult {
        // 1) Baseline (자유속도)
        val route = router.shortestPath(req.originLat, req.originLon, req.destLat, req.destLon)
        val freeSec = route.segments.sumOf { it.distanceM / it.freeFlowSpeedMps }

        // 2) Traffic 가중
        val traffic = trafficClient.fetch(route.segmentIds, req.departAt)
        val trafficSec = route.segments.sumOf { seg ->
            val factor = traffic[seg.id]?.congestionFactor ?: 1.0
            (seg.distanceM / seg.freeFlowSpeedMps) * factor
        }

        // 3) ML 잔차 보정
        val features = featurize(req, route, traffic)
        val correction = mlModel.predict(features)  // 분 단위 가감
        val p50 = (trafficSec + correction * 60).toInt()

        // 4) P90 buffer (모델 quantile prediction)
        val p90 = (p50 * mlModel.quantileFactor(0.9)).toInt()

        return EtaResult(p50, p90)
    }
}
```

**실무 팁**:
- 사용자에게 보여줄 때는 **버킷팅** (e.g. "5분 미만 단위 반올림") — 분 단위 변동이 신뢰 ↓
- A/B 테스트 핵심 KPI: **MAE (Mean Absolute Error)** + **P90 underrun** (예측보다 늦은 비율)
- 차량 종류별 보정 계수 분리 (트럭 vs 오토바이 vs 자전거)
- Pre-trip ETA(주문 시점) vs Post-trip ETA(픽업 후) 모델을 분리 학습
- Hour-of-day, day-of-week 특성은 cyclic encoding (sin / cos) 으로 변환

**관련 패턴·알고리즘**:
- `algorithms/graph.md` — Dijkstra / A* / Contraction Hierarchies (도로 그래프)
- `algorithms/ml.md` — Gradient Boosting (잔차 보정 회귀); Quantile Regression 으로 P10/P90 구간 추정
- [`realtime-tracking`](#realtime-tracking) (실시간 위치 → ETA 재계산 트리거)
- [`vrp-route-optimization`](#vrp-route-optimization) (ETA 가 distance matrix 의 시간 축)

---

<a id="geofencing"></a>
## 4. Geofencing (지오펜싱)

**목적**: 지리적 다각형(또는 원) 영역을 정의해 두고, 차량·기사의 위치 변화가 **영역 진입 / 이탈 / 체류(dwell)** 이벤트를 발생시켜 알림·자동화 워크플로우를 트리거합니다.

**메커니즘**:
- **Fence 정의**: Polygon (다각형) 또는 Circle (중심+반경)
- **Spatial Index**: R-Tree / Quad-Tree / H3 hexagon / S2 cell — fence 가 많을 때 candidate fence 후보 빠르게 추림
- **이벤트 타입**:
  - **Enter** — 외부 → 내부 전이 (배차 알림, 도착 알림 push)
  - **Exit** — 내부 → 외부 전이 (출발 확정, 화물 인수 완료)
  - **Dwell** — 내부 체류가 N 분 초과 (지연 경보)
- **Point-in-Polygon**: Ray casting (O(n)) 또는 Winding number 알고리즘

**장점**:
- 자동화 트리거 (도착 5km 전 고객 알림 등)
- 운영 비용 절감 (수동 콜 → 자동 push)
- 출입 통제 (창고·항만 보안)
- 마케팅 (특정 상권 진입 시 쿠폰)

**단점·주의**:
- GPS jitter 로 인한 false enter/exit: hysteresis(이력) 적용 — enter 1 회 + 30s 유지 시에만 발화
- 배터리: 모바일 단말은 OS native geofence API 활용 (iOS CoreLocation / Android GeofencingClient)
- 다각형 자가 교차 / 자오선(180°) 횡단 등 edge case
- 영역 수 ↑ 시 spatial index 갱신 비용

**Kotlin / pseudo-code 예제**:
```kotlin
data class Fence(val id: String, val polygon: List<LatLng>, val dwellSec: Int = 0)

class GeofenceEngine(
    private val rtree: RTree<Fence>,       // Bounding box index
    private val state: GeofenceStateStore,  // vehicleId → set of inside fenceIds
    private val eventBus: EventBus,
) {
    fun onLocation(vehicleId: String, point: LatLng, ts: Instant) {
        // 1) bbox 로 candidate fence 추림 (O(log n))
        val candidates = rtree.search(point.boundingBox(margin = 0.001))

        // 2) 정확한 PIP 검사
        val nowInside = candidates.filter { pointInPolygon(point, it.polygon) }.map { it.id }.toSet()
        val wasInside = state.get(vehicleId)

        // 3) 차집합으로 enter/exit 도출
        val entered = nowInside - wasInside
        val exited = wasInside - nowInside

        entered.forEach { eventBus.emit(FenceEnter(vehicleId, it, ts)) }
        exited.forEach { eventBus.emit(FenceExit(vehicleId, it, ts)) }

        state.set(vehicleId, nowInside)
    }

    // Ray casting algorithm
    private fun pointInPolygon(p: LatLng, poly: List<LatLng>): Boolean {
        var inside = false
        var j = poly.size - 1
        for (i in poly.indices) {
            val xi = poly[i].lon; val yi = poly[i].lat
            val xj = poly[j].lon; val yj = poly[j].lat
            if ((yi > p.lat) != (yj > p.lat) &&
                p.lon < (xj - xi) * (p.lat - yi) / (yj - yi) + xi) {
                inside = !inside
            }
            j = i
        }
        return inside
    }
}
```

**실무 팁**:
- **Hysteresis margin** 1~3 % 적용 — fence 경계 부근 GPS jitter 로 인한 flapping 방지
- 모바일 단말은 native API (Android `GeofencingClient`, iOS `CLCircularRegion`) 위임 — 서버 polling 보다 배터리 효율 ↑
- H3 hexagon (Uber 발표) — 6각형 grid 가 사각형보다 인접 거리 균일 (k-ring lookup 용이)
- Fence polygon 은 GeoJSON 으로 저장 → PostGIS `ST_Contains`, `ST_DWithin` 활용
- 100k+ fence 환경에서는 R-Tree bulk loading (STR — Sort-Tile-Recursive) 으로 query latency P99 < 20ms

**관련 패턴·알고리즘**:
- `algorithms/spatial.md` (신설 예정) — R-Tree / Quad-Tree / H3 indexing
- `algorithms/geometry.md` — Point-in-Polygon, Ray casting, Winding number
- [`realtime-tracking`](#realtime-tracking) (위치 핑이 trigger)
- [`last-mile-delivery`](#last-mile-delivery) (도착 알림 trigger)

---

<a id="fleet-dispatch"></a>
## 5. Fleet Dispatch / Driver Matching (차량·기사 배차)

**목적**: 신규 운송 요청이 들어왔을 때 **가용 차량·기사 풀에서 최적 매칭** 을 실시간으로 결정합니다. Uber/Lyft 의 핵심 기술.

**메커니즘**:
- **단순 Nearest Driver**: 반경 N km 내 ETA 최단 기사 → 지연 ↓, 효율 ↓
- **Batch Matching**: T 초 윈도우 (e.g. 5s) 동안 요청·기사 모음 → Hungarian Algorithm 으로 글로벌 최적화 (Lyft 의 방식)
- **Auction-based**: 다수 기사에게 broadcast → 첫 수락자 (택시 콜 앱 초기형)
- **Cost 함수**:
  - ETA (기사→픽업지)
  - 운행 가격 / 수수료
  - 기사 평점, 차종 적합도
  - 미래 가치 (deadheading 회피, 다음 콜 받기 좋은 위치)

**알고리즘**:
| 매칭 방식 | 시간 복잡도 | 적용 |
|----------|------------|------|
| Greedy Nearest | O(N) per request | 단일 요청 즉시 |
| Hungarian Algorithm | O(N³) | Batch (수십~수백 쌍) |
| Min-cost Max-flow | O(N²·M) | 대규모 배차 |
| Reinforcement Learning | trained policy | 장기 가치 최적화 (Doordash 시도) |

**장점**:
- 픽업 시간 단축 (Batch 가 Greedy 대비 평균 10~20% 단축)
- 기사 수익 증가 (long-term 가치 고려)
- Surge pricing 입력 (수요·공급 gap)

**단점·주의**:
- Batch 윈도우 ↑ → 사용자 대기 ↑, 윈도우 ↓ → 최적화 효과 ↓ (보통 2~10s)
- 기사 cancel 율: 매칭 후 거절 시 보복 매칭 / 페널티
- 공정성: 특정 기사에게 콜 편중되지 않도록 fairness constraint
- Cold start: 신규 지역·신규 시간대에 데이터 부족

**Kotlin / pseudo-code 예제** (Hungarian Algorithm):
```kotlin
data class Request(val id: String, val pickup: LatLng)
data class Driver(val id: String, val location: LatLng, val rating: Double)

class BatchDispatcher(
    private val eta: EtaService,
    private val window: Duration = Duration.ofSeconds(5),
) {
    suspend fun match(requests: List<Request>, drivers: List<Driver>): Map<Request, Driver> {
        if (requests.isEmpty() || drivers.isEmpty()) return emptyMap()

        val n = maxOf(requests.size, drivers.size)
        // cost[i][j] = request i 를 driver j 에게 할당하는 비용
        val cost = Array(n) { DoubleArray(n) { Double.MAX_VALUE / 2 } }

        for (i in requests.indices) for (j in drivers.indices) {
            val etaSec = eta.estimate(
                EtaRequest(drivers[j].location.lat, drivers[j].location.lon,
                           requests[i].pickup.lat, requests[i].pickup.lon,
                           VehicleType.CAR, Instant.now())
            ).p50Sec
            // Cost = ETA - rating bonus
            cost[i][j] = etaSec - drivers[j].rating * 30
        }

        val assignment = HungarianAlgorithm(cost).solve()  // O(n^3)
        return requests.mapIndexedNotNull { i, r ->
            val j = assignment[i]
            if (j < drivers.size) r to drivers[j] else null
        }.toMap()
    }
}
```

**실무 팁**:
- 첫 도입 시 **Greedy 부터 시작** (운영·디버깅 단순) → A/B 비교 후 batch 도입
- **Re-matching** 허용 윈도우 — 매칭 후 30s 내 더 좋은 매칭 발견 시 swap (UX 영향 신중 평가)
- 기사 측 latency: 배차 알림 push → 수락까지 시간을 별도 KPI 로 추적
- Surge cap (e.g. 평균의 3배) 로 가격 폭주 방지 + 회귀 테스트
- "이중 매칭" 방지: Redis 분산 락 또는 optimistic locking (driver version 컬럼)

**관련 패턴·알고리즘**:
- `algorithms/matching.md` — Hungarian, Bipartite Matching, Stable Marriage
- `algorithms/flow.md` — Min-cost Max-flow
- [`vrp-route-optimization`](#vrp-route-optimization) (배차 후 다중 stop 라우팅)
- [`eta-calculation`](#eta-calculation) (cost function 입력)

---

<a id="last-mile-delivery"></a>
## 6. Last-Mile Delivery (라스트 마일)

**목적**: 물류 hub → 최종 고객 주소까지의 **마지막 구간** 을 처리합니다. 전체 물류 비용의 28~53% 차지 (가장 비싼 구간).

**메커니즘**:
- **Delivery Slot**: 고객이 선호 시간대 (2h 윈도우) 선택 → VRPTW 입력
- **Proof of Delivery (PoD)**:
  - 사진 (현관 앞 두기)
  - 서명 (귀중품)
  - OTP / QR (lock-box)
  - 안면 인식 / 본인 확인 (의약품·주류)
- **Failed Delivery**:
  - 1차 실패 → 다음 날 재시도 또는 픽업 포인트 이관
  - N 회 실패 → return-to-sender
- **Drop-off Variants**: 직접 전달 / 비대면 (contactless) / 락커 (PUDO point)

**장점**:
- 고객 만족도 (시간 정확성, 사진 증빙)
- 분실·도난 분쟁 감소
- 재시도 비용 절감

**단점·주의**:
- Failed delivery 율 5~15% — 비용 폭발 원인
- PoD 사진 저장 비용 / GDPR (배경에 타인 얼굴 등)
- 시간 윈도우 협소화 → 차량 활용률 ↓ 트레이드오프
- 도심 주차·엘리베이터 대기 → ETA 예측 어려움
- 운전자 안전 (개·우범 지역)

**Kotlin / pseudo-code 예제**:
```kotlin
enum class PodMethod { PHOTO, SIGNATURE, OTP, FACE }

data class DeliveryAttempt(
    val orderId: String, val driverId: String,
    val attemptedAt: Instant,
    val outcome: DeliveryOutcome,
    val pod: ProofOfDelivery? = null,
)

sealed class DeliveryOutcome {
    object Delivered : DeliveryOutcome()
    data class Failed(val reason: FailReason) : DeliveryOutcome()
}

enum class FailReason { NO_ANSWER, ADDRESS_INVALID, REFUSED, DAMAGED }

class LastMileService(
    private val orderRepo: OrderRepo,
    private val podStore: PodStorage,
    private val notifier: CustomerNotifier,
    private val retryPolicy: RetryPolicy,
) {
    suspend fun recordAttempt(attempt: DeliveryAttempt) {
        when (val o = attempt.outcome) {
            is DeliveryOutcome.Delivered -> {
                requireNotNull(attempt.pod) { "PoD required for delivered" }
                podStore.persist(attempt.orderId, attempt.pod)
                orderRepo.markDelivered(attempt.orderId, attempt.attemptedAt)
                notifier.sendDeliveredConfirmation(attempt.orderId, attempt.pod)
            }
            is DeliveryOutcome.Failed -> {
                val attempts = orderRepo.incrementAttempt(attempt.orderId)
                if (attempts < retryPolicy.maxAttempts && o.reason.isRetryable()) {
                    orderRepo.scheduleNext(attempt.orderId, retryPolicy.nextSlot(attempts))
                    notifier.sendRetryScheduled(attempt.orderId)
                } else {
                    orderRepo.markReturnToSender(attempt.orderId, o.reason)
                    notifier.sendReturnNotice(attempt.orderId, o.reason)
                }
            }
        }
    }

    private fun FailReason.isRetryable() = this in setOf(NO_ANSWER, REFUSED)
}
```

**실무 팁**:
- PoD 사진은 **얼굴 자동 블러** (OpenCV / MediaPipe) — GDPR 대응
- 사진 저장은 **S3 + presigned URL** + 객체별 lifecycle (90일 후 Glacier)
- OTP는 4자리 숫자(고객 입력 부담 ↓) + 단일 사용 + 5분 TTL
- "안전 배송 지점" 사진 학습 (특정 우편함·문 앞) — 재방문 효율
- Failed delivery 의 **next-action prompt** — 자동 SMS "지금 가능하신가요? 1: 재시도, 2: 대신 받으실 분, 3: 픽업"

**관련 패턴·알고리즘**:
- [`geofencing`](#geofencing) (도착 알림 트리거)
- [`vrp-route-optimization`](#vrp-route-optimization) (VRPTW 로 slot 만족)
- [`track-and-trace`](#track-and-trace) (PoD 가 chain of custody 마지막 노드)

---

<a id="reverse-logistics"></a>
## 7. Reverse Logistics (역물류 / 반품 회수)

**목적**: 고객 → 창고로 흐르는 **역방향 물류** 를 처리합니다. 전자상거래 반품, 리스 장비 회수, A/S 수리품, 친환경 재활용.

**메커니즘**:
- **Trigger**: 고객 반품 요청 / 보증 만료 / 리스 종료 / 리콜
- **Pickup 방식**:
  - **Customer-initiated drop-off** (PUDO 락커, 편의점) — 가장 저렴
  - **Carrier pickup** (택배사 방문 수거) — 중간 비용
  - **In-house fleet** (자체 차량) — 비싸지만 SLA·검수 우수
- **Reverse VRP**: pickup 들을 묶어 routing — 정방향 VRP 와 동일 알고리즘이나 수요가 **휘발성** (취소 잦음)
- **Triage**: 회수 후 검수 → 재판매 / 재고화 / 폐기 / 부품 회수

**장점**:
- CX (반품 쉬움) ↔ 매출 (LTV) 양의 상관 (Zappos 사례)
- 환경 규제(WEEE, EPR) 대응
- 부품·소재 회수로 재사용

**단점·주의**:
- 순방향 대비 단가 ↑ (역방향 적재 효율 ↓, 검수 인건비)
- 반품 사기 (swap fraud) — 시리얼 번호 검증 필수
- 수요 예측 어려움 (계절성 ↑, 광고/리뷰 영향)
- 재고 시스템 (WMS) 와의 이중 동기화

**Kotlin / pseudo-code 예제**:
```kotlin
sealed class ReturnTrigger {
    data class CustomerReturn(val orderId: String, val reason: ReturnReason) : ReturnTrigger()
    data class WarrantyRepair(val productId: String) : ReturnTrigger()
    data class LeaseEnd(val contractId: String) : ReturnTrigger()
}

enum class TriageOutcome { RESELL_AS_NEW, RESELL_USED, REFURBISH, PARTS, RECYCLE, DISPOSE }

class ReverseLogisticsService(
    private val pickupScheduler: PickupScheduler,
    private val inspector: InspectionService,
    private val wms: WarehouseSystem,
    private val refundService: RefundService,
) {
    suspend fun initiate(trigger: ReturnTrigger, customerAddress: Address) {
        val pickupOption = chooseChannel(customerAddress, trigger)
        val ticket = pickupScheduler.create(trigger, customerAddress, pickupOption)

        // 회수 도착 후 콜백
        ticket.onReceived { items ->
            items.forEach { item ->
                val report = inspector.inspect(item)  // 시리얼·외관·기능
                val outcome = decideTriage(report)
                wms.intake(item, location = wms.binFor(outcome))

                if (trigger is ReturnTrigger.CustomerReturn) {
                    refundService.issueIfEligible(trigger.orderId, report)
                }
            }
        }
    }

    private fun chooseChannel(addr: Address, t: ReturnTrigger) = when {
        t is ReturnTrigger.CustomerReturn && t.reason == ReturnReason.SIZE -> PickupChannel.PUDO
        t is ReturnTrigger.LeaseEnd -> PickupChannel.IN_HOUSE
        addr.isMetro -> PickupChannel.CARRIER
        else -> PickupChannel.PUDO
    }
}
```

**실무 팁**:
- 반품 사유 categorization (FREE TEXT 금지) → 데이터 분석 가능 + 사기 탐지
- 시리얼·IMEI 검증을 **회수 직전** 모바일 단말로 (회수 후 swap 사기 방지)
- 정방향 차량의 **빈 적재 칸** 활용 — 동일 경로 픽업과 합본 (Pickup-and-Delivery)
- 분쟁 발생률 ↓ 를 위해 회수 시점도 **PoD 사진 + 시리얼 QR** 동시 기록
- 친환경 마케팅 (재활용·중고 판매) 연계 — ESG 보고 자료

**관련 패턴·알고리즘**:
- [`vrp-route-optimization`](#vrp-route-optimization) (Reverse VRP)
- [`last-mile-delivery`](#last-mile-delivery) (정방향과 합본 경로 가능 — pickup-and-delivery)
- [`track-and-trace`](#track-and-trace) (역방향 chain of custody)

---

<a id="multi-hop-cross-docking"></a>
## 8. Multi-Hop / Cross-Docking (다단계 환적 / 크로스도킹)

**목적**: 화물을 **창고에 적재하지 않고** 입고 → 분류 → 출고를 수 시간 내에 통과시키는 hub-and-spoke 모델. FedEx Memphis hub, Amazon sortation center, 쿠팡 캠프 모델.

**메커니즘**:
- **Hub-and-Spoke**: 지역 spoke → 중앙 hub 집결 → 재분류 → 목적지 spoke (FedEx)
- **Cross-Dock**: 입고 트럭 → 정렬 컨베이어 → 출고 트럭 (재고 보관 ≤ 24h)
- **Sortation**:
  - **Manual** — 인력 분류
  - **Sortation conveyor** — 바코드 스캔 + 슬라이드 chute
  - **AGV / AMR** — Kiva-type 로봇 (Amazon)
- **운송 모드**:
  - **TL** (Truckload) — full 트럭, 환적 없음
  - **LTL** (Less-than-Truckload) — 다수 화주 결합, hub 환적
  - **Parcel** — 소포, 다단 hub

**장점**:
- 재고 보관 비용 ↓
- 회전율 ↑ (당일 배송 가능)
- 차량 적재율 ↑ (LTL 결합)

**단점·주의**:
- Hub 가 단일 장애점 (FedEx Memphis 폭설 → 전국 지연)
- 분류 오류 (mis-sort) → 잘못된 트럭 적재 → 배송 지연
- 입고·출고 트럭 도착 동기화 실패 시 dock 정체
- 시스템 (WMS / TMS) 의존도 ↑

**Kotlin / pseudo-code 예제**:
```kotlin
data class Parcel(val id: String, val origin: String, val destination: String, val barcode: String)

data class DockAssignment(val parcelId: String, val outboundDock: String, val truckId: String)

class CrossDockSorter(
    private val routingTable: RoutingTable,     // destination -> outbound dock
    private val truckSchedule: TruckSchedule,    // outbound dock -> next departure
    private val conveyor: ConveyorController,
    private val tracer: TraceService,
) {
    suspend fun onInboundScan(parcel: Parcel): DockAssignment {
        val dock = routingTable.lookup(parcel.destination)
            ?: error("Unknown destination: ${parcel.destination}")
        val truck = truckSchedule.nextDeparture(dock)

        // 1) Track & Trace event
        tracer.emit(ScanEvent(parcel.id, location = dock, ts = Instant.now()))

        // 2) Conveyor diverter 명령
        conveyor.divert(parcel.barcode, targetChute = dock)

        // 3) DB 기록
        return DockAssignment(parcel.id, dock, truck.id).also { persist(it) }
    }

    suspend fun reconcileMissort(parcel: Parcel, actualDock: String) {
        // Conveyor scan 후 actual != assigned 면 mis-sort
        tracer.emit(MissortEvent(parcel.id, expected = ..., actual = actualDock))
        // 재진입 conveyor 로 회수
        conveyor.recirculate(parcel.barcode)
    }
}
```

**실무 팁**:
- Inbound dock 스케줄 — 트럭 도착 시간 30 분 단위 슬롯 예약제 (no-show 페널티)
- Mis-sort rate KPI: 0.5% 미만 목표 (Amazon 공개 자료 기준)
- Conveyor 컨베이어 속도 vs 스캐너 정확도 트레이드오프 (속도 ↑ → 카메라 모션블러)
- Sortation 정전 대비 — UPS + manual fallback 절차 정기 훈련
- Hub backup — 1차 hub 장애 시 2차 hub 자동 라우팅 (FedEx 의 Indianapolis backup)

**관련 패턴·알고리즘**:
- `algorithms/graph.md` — Hub location problem (시설 위치 결정)
- [`vrp-route-optimization`](#vrp-route-optimization) (hub → spoke linehaul)
- [`track-and-trace`](#track-and-trace) (각 hop 마다 scan event)
- [`capacity-planning`](#capacity-planning) (dock / conveyor 용량 결정)

---

<a id="capacity-planning"></a>
## 9. Capacity Planning / Demand Forecasting (수요 예측 / 캐파)

**목적**: 시간·지역 단위 **수요를 예측** 하고 그에 맞춰 차량·기사·창고 인력의 capacity 를 미리 배치합니다. Doordash 의 Dasher dispatch 핵심.

**메커니즘**:
- **예측 horizon**:
  - Short-term (분 단위 ~ 1h) — 실시간 surge / cooldown
  - Mid-term (일/주) — Driver shift scheduling
  - Long-term (월/년) — 창고 확장, 차량 구매
- **모델**:
  - **Time-series**: ARIMA, SARIMA, Prophet (계절성 처리)
  - **ML**: Gradient Boosting (외생 변수 — 날씨, 이벤트, 프로모션)
  - **Deep Learning**: LSTM / Transformer (다변량 시계열)
  - **Hierarchical Forecasting**: 전국 → 권역 → 지점 일관성 (MinT reconciliation)
- **Capacity 배치**:
  - 인센티브 (수요 ↑ 지역에 추가 보수)
  - Pre-positioning (차량을 수요 예측 지역에 사전 이동)
  - Shift offer (요일·시간 묶음을 기사에게 제안)

**장점**:
- 응답 시간 단축 (수요 ↑ 전 미리 공급)
- 운영 비용 ↓ (overcapacity 회피)
- 가격 안정 (surge 발동 빈도 ↓)

**단점·주의**:
- 예측 오차 → 손실 (overcapacity = 유휴 비용, undercapacity = 매출 손실)
- Concept drift: 코로나 같은 외생 충격에 모델 무력
- Causal vs Correlational: 프로모션·날씨가 진짜 원인인지 검증 필요
- Reinforcing loop: 예측 → 공급 ↑ → 수요 변화 → 예측 오차 (feedback)

**Kotlin / pseudo-code 예제**:
```kotlin
data class DemandWindow(val region: String, val start: Instant, val end: Instant, val expected: Int)

class DemandForecaster(
    private val historical: TimeSeriesStore,  // 과거 수요
    private val weatherApi: WeatherApi,
    private val eventCalendar: EventCalendar,  // 콘서트·스포츠
    private val mlModel: GradientBoostingModel,
) {
    suspend fun forecast(region: String, horizon: Duration): List<DemandWindow> {
        val now = Instant.now()
        val slots = (0 until horizon.toHours()).map {
            val start = now.plus(Duration.ofHours(it))
            val end = start.plus(Duration.ofHours(1))

            val features = buildFeatures(
                region = region,
                ts = start,
                historical = historical.lookup(region, lagDays = listOf(1, 7, 14)),
                weather = weatherApi.forecast(region, start),
                events = eventCalendar.between(region, start, end),
            )
            val expected = mlModel.predict(features).toInt()
            DemandWindow(region, start, end, expected)
        }
        return slots
    }
}

class CapacityAllocator(
    private val forecaster: DemandForecaster,
    private val driverPool: DriverPool,
    private val incentive: IncentiveEngine,
) {
    suspend fun plan(region: String, horizon: Duration) {
        val demand = forecaster.forecast(region, horizon)
        demand.forEach { window ->
            val available = driverPool.expectedAvailable(region, window.start)
            val gap = window.expected - available
            if (gap > 0) {
                incentive.offerBonus(region, window, perDriverBonus = gap * 0.5)
            }
        }
    }
}
```

**실무 팁**:
- Forecast 모델은 **regional → national hierarchical** 구조 → MinT (Hyndman) 으로 일관성 reconciliation
- Backtesting frame: rolling-origin cross-validation (단순 train/test split 금지)
- Cold start 지역은 **유사 지역 transfer learning** (인구·소득·반경 1km POI 유사도)
- Forecast 적중률 KPI: MAPE (Mean Absolute Percentage Error) 권역별 + 전체
- Incentive engine 은 **회귀 한도** (예산 cap) 설정 — 폭주 방지

**관련 패턴·알고리즘**:
- `algorithms/ml.md` — Gradient Boosting (수요 회귀); 시계열 보강은 ARIMA / Prophet / LSTM 계열
- `algorithms/dynamic-programming.md` — Shift scheduling DP
- [`fleet-dispatch`](#fleet-dispatch) (실시간 surge 의 입력)
- [`vrp-route-optimization`](#vrp-route-optimization) (차량 수 결정 입력)

---

<a id="track-and-trace"></a>
## 10. Track & Trace (Chain of Custody)

**목적**: 화물이 거치는 모든 hop 에서 **스캔 이벤트** 를 누적해 누가 언제 어디서 보관·이동·인수했는지의 연속 기록을 만듭니다. 분쟁 해결·법규 준수·고객 가시성의 기반.

**메커니즘**:
- **식별자**: Bar code / QR / RFID / NFC tag — 단품(SKU) / 박스 / 팔레트 / 컨테이너 4 레벨
- **Scan event**:
  - **PICKED_UP** (출하)
  - **IN_TRANSIT** (이동 중)
  - **ARRIVED_HUB** (hub 입고)
  - **OUT_FOR_DELIVERY** (배송 출발)
  - **DELIVERED** (배송 완료)
  - **EXCEPTION** (분실·손상·반품)
- **Tamper-evident log**: 이벤트 시퀀스의 hash chain (블록체인까지는 아니어도 append-only + 서명)
- **표준**: GS1 EPCIS 4 W (What / Where / When / Why)
- **고객 노출**: tracking page URL + push 알림

**장점**:
- 분실·도난 책임 소재 명확
- 콜드체인 (의약품·식품) 온도 로그 결합
- HS code · 원산지 증명 (국제 무역)
- 고객 anxiety 감소 (배송 가시성)

**단점·주의**:
- Scan 누락 (인력 실수, 장비 고장) → trace 단절
- RFID/바코드 위조 — anti-tamper hardware 필요
- Event 폭증 — billion 단위 (FedEx 사례) → time-series store + cold storage 분리
- 다국가 거래 시 표준 차이 (EPCIS vs UPU)

**Kotlin / pseudo-code 예제**:
```kotlin
data class ScanEvent(
    val parcelId: String,
    val type: ScanType,
    val location: LocationCode,    // ISO 3166 + GLN
    val timestamp: Instant,
    val operatorId: String,
    val prevHash: String,           // chain previous event hash
)

enum class ScanType { PICKED_UP, IN_TRANSIT, ARRIVED_HUB, OUT_FOR_DELIVERY, DELIVERED, EXCEPTION }

class TraceService(
    private val eventStore: ScanEventStore,   // Append-only
    private val signer: HmacSigner,
    private val notifier: CustomerNotifier,
) {
    suspend fun emit(event: ScanEvent): String {
        val prev = eventStore.latest(event.parcelId)
        val withChain = event.copy(prevHash = prev?.let { hash(it) } ?: "GENESIS")
        val signed = signer.sign(withChain)
        eventStore.append(signed)

        // 고객 노출 트리거
        when (event.type) {
            ScanType.OUT_FOR_DELIVERY -> notifier.notifyOutForDelivery(event.parcelId)
            ScanType.DELIVERED -> notifier.notifyDelivered(event.parcelId)
            ScanType.EXCEPTION -> notifier.notifyException(event.parcelId)
            else -> {}
        }
        return signed.hash
    }

    suspend fun traceHistory(parcelId: String): List<ScanEvent> {
        val events = eventStore.findAll(parcelId)
        // Verify hash chain integrity
        events.zipWithNext { a, b ->
            require(b.prevHash == hash(a)) { "Chain broken between ${a.timestamp} and ${b.timestamp}" }
        }
        return events
    }

    private fun hash(e: ScanEvent): String =
        sha256("${e.parcelId}|${e.type}|${e.location}|${e.timestamp}|${e.operatorId}|${e.prevHash}")
}
```

**실무 팁**:
- Tracking page URL 은 **stateless token** (서명된 JWT) — DB 조회 없이 검증 + 만료
- Push 알림 빈도 = 4~5건 (PICKED_UP / OUT_FOR_DELIVERY / DELIVERED / EXCEPTION) — 과다 알림 = 구독 해지
- 대량 발송 시 **batch trace event** (1초 윈도우 모음 → 1 transaction)
- 콜드체인은 **온도 센서** scan event 와 결합 → temperature breach 시 자동 alert
- 국제 거래 표준 — EPCIS 4.0 / UPU EDI / IATA Cargo XML 매핑 미리 결정

**관련 패턴·알고리즘**:
- `algorithms/crypto.md` — HMAC / SHA-256 (tamper-evident chain)
- `../observability.md` — 분산 트레이싱과 동일한 인과 추적 사상
- [`multi-hop-cross-docking`](#multi-hop-cross-docking) (각 hop 마다 scan 발생원)
- [`last-mile-delivery`](#last-mile-delivery) (DELIVERED + PoD)
- [`reverse-logistics`](#reverse-logistics) (역방향 chain)

---
