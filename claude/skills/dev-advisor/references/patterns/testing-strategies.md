# 테스트 전략 패턴 (Testing Strategy Patterns)

기존 [`testing.md`](testing.md) (Test Pyramid / AAA / Test Double 같은 *단위 테스트 패턴*) 의 보강. **테스트 형태·전략·검증 방식** 10 패턴 — 단위에서 production 검증까지.

**원전·표준 참고**:
- Lisa Crispin, Janet Gregory — *Agile Testing: A Practical Guide* (2009)
- Kent C. Dodds — *Write tests. Not too many. Mostly integration.* (Test Trophy, 2018)
- Casey Rosenthal, Nora Jones — *Chaos Engineering: System Resiliency in Practice* (O'Reilly, 2020)
- Netflix — Principles of Chaos (principlesofchaos.org)
- Ron Kohavi, Diane Tang, Ya Xu — *Trustworthy Online Controlled Experiments* (2020) — A/B
- Spinnaker / Kayenta — Canary Analysis
- ISTQB Foundation Level Syllabus — Performance testing 분류

**관련 카탈로그**:
- [testing.md](testing.md) — Test Pyramid / AAA / Property-Based / Contract / Snapshot
- [deployment.md](deployment.md) — Canary / Blue-Green / Shadow / Dark Launch
- [`../principles/resilience-theory.md`](../principles/resilience-theory.md) — Chaos Engineering 이론

---

<a id="pyramid-trophy-diamond-honeycomb"></a>

## 1. Test Pyramid vs Test Trophy vs Test Diamond vs Test Honeycomb

**목적**: 동일한 "테스트 계층별 비율 결정" 문제에 대한 4 개 모델을 비교하여, 스택·아키텍처·팀 규모에 맞는 분포 전략을 선택합니다.

**4 모델 비교**:
| 모델 | 제안자 | 분포 (아래→위) | 강조점 | 적합 컨텍스트 |
|---|---|---|---|---|
| **Test Pyramid** | Mike Cohn (2009) | Unit (다수) → Integration (중간) → E2E (소수) | 빠른 피드백·CI 비용 최소화 | JVM 백엔드, 모놀리식, 도메인 로직 풍부 |
| **Test Trophy** | Kent C. Dodds (2018) | Static (lint/type) → Unit → **Integration (다수)** → E2E | 통합 신뢰도, 리팩토링 저항 | React/Node 같은 JS 스택, BFF |
| **Test Diamond** | (커뮤니티 변형) | Unit (소수) → **Integration (다수)** → E2E (소수) | 통합 비중↑, unit 거품 제거 | 마이크로서비스, API gateway 중심 |
| **Test Honeycomb** | Spotify (2018) | Implementation Details (소수) → **Integrated (다수)** → Integration (소수) | 외부 의존 mock 최소화 | 서비스 메시 환경, 큰 통합 표면 |

**Pyramid 의 한계**:
- 프런트엔드에서는 컴포넌트 unit 이 실제 통합 결함(라우팅·상태·이벤트)을 못 잡음
- 마이크로서비스에서는 단위 logic 이 얇고 통합 경계가 두꺼움 → 단위 테스트만으로는 신뢰 부족

**Trophy 의 강점**:
- "Write tests. Not too many. Mostly integration." — JS/React 처럼 의존성 그래프가 평평한 환경에서 ROI 최대
- Static 계층(TypeScript, ESLint, Prettier) 을 명시적 테스트 계층으로 포함

**Diamond 의 동기**:
- "Unit test bloat" 안티패턴 회피 — Mock 으로 도배된 unit 은 구현 변경에 깨지고 실제 결함은 못 잡음
- API 레벨 통합에서 비즈니스 가치 검증

**Honeycomb 의 특이점**:
- "Integrated" = 한 서비스 + 실 DB + 인메모리 stub
- "Implementation details" 는 의도적으로 적음 (private 함수 unit 회피)
- "Integration" 은 서비스 ↔ 서비스 경계 (Pact 같은 contract test)

**장점**:
- 스택·아키텍처별 적정 분포 가이드
- "왜 unit 만으로 부족한가" 에 대한 언어 제공

**단점**:
- 4 모델 모두 "느낌적 비율" — 통계적 근거 부족
- 팀이 매번 분포를 직접 측정·재조정해야 의미 있음
- 잘못 적용 시 "Ice Cream Cone" (E2E 만 비대) 또는 "Mock Iceberg" (Mock 만 비대)로 변질

**활용 예시**:
- JVM 백엔드(주문/결제 도메인) → **Pyramid**
- Next.js + Node BFF → **Trophy**
- Kubernetes 마이크로서비스 mesh → **Diamond** 또는 **Honeycomb**

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제 (Pyramid 분포 측정 유틸)**:
```kotlin
// Gradle 모듈별 테스트 수 집계로 현재 분포를 가시화
data class TestDistribution(
    val unit: Int,
    val integration: Int,
    val e2e: Int,
) {
    val total: Int get() = unit + integration + e2e
    fun ratio(): Triple<Double, Double, Double> =
        Triple(unit.toDouble() / total, integration.toDouble() / total, e2e.toDouble() / total)

    fun classify(): String = when {
        ratio().first > 0.6  -> "Pyramid"
        ratio().second > 0.5 -> "Trophy/Diamond"
        ratio().third > 0.3  -> "Ice Cream Cone (anti-pattern)"
        else                 -> "Mixed"
    }
}

fun main() {
    val dist = TestDistribution(unit = 480, integration = 120, e2e = 30)
    println("분포=${dist.ratio()} 분류=${dist.classify()}")
    // 분포=(0.76, 0.19, 0.05) 분류=Pyramid
}
```

**관련 패턴**: [testing.md#1](testing.md) Test Pyramid, [testing.md#6](testing.md) Contract Test, Shadow Traffic Testing

---

<a id="chaos-engineering"></a>

## 2. Chaos Engineering

**목적**: 프로덕션 환경에 의도적으로 장애(latency/crash/network partition)를 주입해 시스템이 *예상대로 회복*하는지 실험적으로 검증합니다.

**방법론·도구**:
- **Netflix Principles of Chaos** (5 원칙):
  1. 정상 상태(steady state) 가설 수립
  2. 변동성(real-world events) 다양화
  3. **프로덕션** 실험 (스테이징은 fidelity 부족)
  4. 지속적 자동화
  5. **Blast radius 최소화** — 처음엔 단일 인스턴스, 점진 확대
- **도구**: Chaos Monkey (단일 인스턴스 죽이기), Chaos Kong (region 전체), Gremlin, Litmus, AWS Fault Injection Simulator, Kubernetes `chaos-mesh`
- **실험 설계**:
  1. Hypothesis: "한 DB replica 가 죽어도 p99 latency 가 500ms 미만 유지"
  2. Method: replica 1 개에 SIGKILL
  3. Blast radius: 트래픽 5% 만 영향
  4. Abort condition: error rate > 1% 시 자동 중단
- **Game Day**: 분기 1 회 팀이 모여 대규모 장애 시나리오 실행

**장점**:
- "장애가 일어나기 전" 에 회복력 검증 — 새벽 3 시 페이지 콜 감소
- 숨겨진 single point of failure 발견
- 팀의 incident response 근육 강화

**단점**:
- 프로덕션 실험에 대한 조직적 신뢰·SRE 성숙도 필요
- Blast radius 통제 실패 시 실제 사고 (Chaos Monkey 가 prod 전체 죽인 사례 있음)
- "회복 가능" 가설을 사전 검증 못 하면 단순 사보타주
- Stateful 시스템(DB primary)에는 적용 신중

**활용 예시**:
- Netflix Chaos Monkey/Kong — AWS region failover 검증
- AWS Fault Injection Simulator — EC2 / RDS / network 장애 주입
- Kubernetes `chaos-mesh` — Pod kill, network delay, disk fill
- LinkedIn Waterbear — 분산 trace 와 결합

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**YAML 예제 (Chaos Mesh — Pod 강제 종료 실험)**:
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: payment-replica-kill
  namespace: chaos-testing
spec:
  action: pod-kill                         # 1. Method
  mode: one                                # 5. Blast radius (단일 pod)
  selector:
    namespaces: [payment]
    labelSelectors:
      app: payment-service
      role: replica                         # primary 보호
  scheduler:
    cron: "0 14 * * 1-5"                   # 평일 오후 2시 (peak 회피)
  duration: "30s"
# Abort condition 은 Prometheus AlertManager 와 연동:
# alert: ChaosAbort if error_rate > 0.01 → kubectl delete podchaos payment-replica-kill
```

**Kotlin 예제 (정상 상태 가설 검증)**:
```kotlin
data class SteadyStateHypothesis(
    val name: String,
    val metric: () -> Double,
    val tolerance: ClosedRange<Double>,
)

class ChaosExperiment(
    private val hypothesis: SteadyStateHypothesis,
    private val inject: () -> Unit,
    private val rollback: () -> Unit,
) {
    fun run(): Result<Unit> = runCatching {
        val before = hypothesis.metric()
        check(before in hypothesis.tolerance) { "사전 정상상태 위반: $before" }
        inject()
        try {
            repeat(10) {
                Thread.sleep(3_000)
                val now = hypothesis.metric()
                check(now in hypothesis.tolerance) { "실험 중 SLO 위반: $now → 자동 중단" }
            }
        } finally {
            rollback()
        }
    }
}
```

**관련 패턴**: Synthetic Monitoring, [reliability.md] Circuit Breaker / Bulkhead, [observability.md] Distributed Tracing

---

<a id="load-testing"></a>

## 3. Load Testing

**목적**: 예상 트래픽 수준에서 시스템이 SLA(latency·throughput·error rate) 를 만족하는지 검증합니다.

**방법론·도구**:
- **JMeter** — GUI 기반, 무료, JVM. 대규모 분산 부하 (controller + workers)
- **Gatling** — Scala DSL, 코드로 시나리오 기술, HTML 리포트 우수
- **k6** — Grafana Labs, JavaScript DSL, CI 친화적, Prometheus/Cloud 통합
- **Locust** — Python, 분산 worker, 동시 사용자 모델
- **Apache Bench (ab)** — 단순 HTTP 부하, smoke test
- **부하 패턴**:
  - **Ramp-up**: 0 → N users 점진 증가 (예: 5 분간 1000 명)
  - **Steady / Sustained load**: 목표 부하를 30 분~수 시간 유지
  - **Ramp-down**: 부하 해제 후 시스템 회복 시간 측정

**핵심 지표**:
- **Throughput** — req/sec, business tx/min
- **Latency** — p50 / p95 / p99 / p99.9 (평균값은 함정)
- **Error rate** — 5xx + timeout
- **Saturation** — CPU / memory / connection pool / GC pause

**장점**:
- Production capacity 사전 검증 → 트래픽 급증 대응
- 성능 회귀 감지 (릴리스마다 같은 시나리오 반복)
- 인프라 sizing 근거

**단점**:
- 실 사용자 행동 패턴 재현이 어려움 (think time, session, geographic 분포)
- 부하 발생기 자체가 병목 (k6 controller, JMeter 메모리)
- "1000 RPS 통과" 가 prod 성공을 보장하지는 않음 (trafic mix 차이)

**활용 예시**:
- 배포 전 staging 에 k6 smoke (1 분 / 100 RPS) — CI gate
- 분기별 prod 사이즈 capacity test
- 신규 API 출시 전 SLO 검증

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**JavaScript 예제 (k6 — ramp-up + steady load)**:
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const latency = new Trend('checkout_latency', true);

export const options = {
  scenarios: {
    rampUp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 200 },   // Ramp-up
        { duration: '10m', target: 200 },  // Sustained
        { duration: '1m',  target: 0 },    // Ramp-down
      ],
    },
  },
  thresholds: {
    'http_req_duration{name:checkout}': ['p(95)<400', 'p(99)<800'],
    'http_req_failed':                  ['rate<0.01'],
  },
};

export default function () {
  const res = http.post('https://api.example.com/checkout',
    JSON.stringify({ cartId: 'c-1', amount: 10000 }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'checkout' } });
  check(res, { 'status is 2xx': r => r.status >= 200 && r.status < 300 });
  latency.add(res.timings.duration);
  sleep(Math.random() * 2);  // think time
}
```

**관련 패턴**: Stress Testing, Spike Testing, Soak Testing, Synthetic Monitoring

---

<a id="stress-testing"></a>

## 4. Stress Testing

**목적**: 시스템을 *정격 부하 초과* 까지 밀어붙여 **breaking point** (장애가 시작되는 지점) 와 그 이후의 **degradation mode** 를 파악합니다.

**방법론·도구**:
- Load testing 도구 동일 (k6 / Gatling / JMeter) — 부하 패턴만 다름
- **Capacity planning 공식**:
  - Headroom = (Breaking point − Peak prod load) / Peak prod load
  - 권장 headroom: 100% (peak 의 2배 까지 견딤) — Netflix 가이드라인
- **Degradation 관찰**:
  - Graceful: latency 증가만, 에러율 유지 → 양호
  - Cascading: 한 서비스 죽으면 다른 서비스 연쇄 실패 → Circuit Breaker 필요
  - Catastrophic: OOM / Disk full / DB connection 고갈 → 인프라 한계

**Load vs Stress 차이**:
| 측면 | Load Test | Stress Test |
|---|---|---|
| 목표 부하 | 예상 peak (정격) | 정격의 2~10 배 |
| 성공 기준 | SLA 만족 | breaking point 발견 |
| 실행 빈도 | 매 릴리스 | 분기·반기 |
| 위험도 | 낮음 | 높음 (실제 시스템 다운 가능) |

**장점**:
- "어디서 깨지나" 정량 데이터 확보 → capacity planning 근거
- Auto-scaling 임계값 튜닝
- Failure mode 식별 (graceful vs catastrophic)

**단점**:
- prod 동일 환경 필요 (staging 은 사양 차이로 결과 왜곡)
- 부하 발생기 자체가 한계에 도달
- DB / 3rd-party API 가 함께 망가질 수 있음 (rate limit, contract)

**활용 예시**:
- 신규 인스턴스 타입 도입 시 capacity 측정
- Auto-scaling rule 의 scale-out threshold 결정
- Database connection pool 사이즈 검증

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**JavaScript 예제 (k6 — breaking point 탐색)**:
```javascript
import http from 'k6/http';

export const options = {
  scenarios: {
    findBreakingPoint: {
      executor: 'ramping-arrival-rate',
      startRate: 100,
      timeUnit: '1s',
      preAllocatedVUs: 500,
      maxVUs: 5000,
      stages: [
        { duration: '5m',  target: 500 },   // 정격 (baseline)
        { duration: '5m',  target: 1000 },  // 2x
        { duration: '5m',  target: 2000 },  // 4x
        { duration: '5m',  target: 4000 },  // 8x
        { duration: '5m',  target: 8000 },  // 16x — breaking point 예상 구간
      ],
    },
  },
  thresholds: {
    'http_req_failed': [{ threshold: 'rate<0.05', abortOnFail: true, delayAbortEval: '30s' }],
  },
};

export default function () { http.get('https://api.example.com/products'); }
// 결과 해석: error rate 가 5% 를 넘는 시점의 RPS = breaking point
```

**관련 패턴**: Load Testing, Spike Testing, [reliability.md] Circuit Breaker, [reliability.md] Bulkhead

---

<a id="spike-testing"></a>

## 5. Spike Testing

**목적**: 짧은 시간에 트래픽이 *수십~수백 배 급증* 했을 때 시스템이 (a) 견디는지 (b) 회복하는지 검증합니다.

**방법론·도구**:
- Load testing 도구 동일 — 시나리오만 spike 패턴
- **Spike 형태**:
  - **Single spike**: 0 → 10x → 0 (Black Friday 오픈, 티켓 오픈)
  - **Recurring spike**: 매 정시 spike (cron job, 알림 전송)
  - **Stepped spike**: 정격 → 10x → 정격 → 10x (광고 캠페인)
- **대응 메커니즘 검증**:
  - **Auto-scaling 반응 속도** — Pod 가 뜨는 30~60 초 사이의 cold start
  - **Queue / Buffer** — Spike 를 SQS / Kafka 가 흡수, downstream 은 평탄화 (Load Leveling)
  - **Rate Limiter** — 한도 초과 트래픽을 429 로 drop
  - **CDN cache** — Origin 보호

**Black Friday / 콘서트 티켓 / 수강 신청 시나리오**:
- 정상 부하의 50~200 배가 30 초 안에 발생
- Auto-scaling 만으로는 늦음 (cold start > 30 초) → pre-warm 또는 over-provision
- Queue + 결과 polling 패턴 (chat-style backpressure)

**장점**:
- 예측 가능 이벤트(블랙프라이데이, 이벤트 오픈) 대응 검증
- Auto-scaling rule + queue 흡수 능력 측정
- Rate limiter 정책 튜닝

**단점**:
- 실 spike 와 동일한 사용자 행동 재현 어려움 (사용자는 retry burst 까지 함)
- 3rd-party 의존(결제 PG, 인증)이 함께 spike 받음
- Auto-scaling 비용 검증과 trade-off

**활용 예시**:
- 콘서트 티켓 예매 오픈 (10x → 100x in 10s)
- Push notification fan-out (1M 명에게 동시 push → /api/feed spike)
- Live commerce 시작 시점

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**JavaScript 예제 (k6 — single spike)**:
```javascript
import http from 'k6/http';

export const options = {
  scenarios: {
    blackFriday: {
      executor: 'ramping-arrival-rate',
      startRate: 100,
      timeUnit: '1s',
      preAllocatedVUs: 200,
      maxVUs: 10000,
      stages: [
        { duration: '2m',  target: 100  },   // 평상시
        { duration: '30s', target: 5000 },   // 50x spike (티켓 오픈)
        { duration: '3m',  target: 5000 },   // spike 유지
        { duration: '30s', target: 100  },   // 정상 복귀
        { duration: '2m',  target: 100  },   // 회복 확인
      ],
    },
  },
};

export default function () {
  http.post('https://api.example.com/ticket/reserve',
    JSON.stringify({ eventId: 'concert-2026' }),
    { headers: { 'Content-Type': 'application/json' } });
}
// 검증: spike 구간에 5xx 비율, 정상 복귀 후 latency 가 baseline 으로 돌아오는 시간
```

**관련 패턴**: Load Testing, Stress Testing, [reliability.md] Rate Limiter, [workflow-jobs.md] Load Leveling Queue

---

<a id="soak-endurance-testing"></a>

## 6. Soak / Endurance Testing

**목적**: 중간 부하를 *수 시간~수 일* 유지하여 단기 테스트로 안 보이는 **memory leak, connection leak, log/disk 누적, 점진적 latency 증가** 등을 탐지합니다.

**방법론·도구**:
- Load testing 도구 동일 — 시나리오 duration 만 12~72 시간
- **관찰 대상**:
  - **Memory leak** — JVM heap, Node.js RSS, Go heap 의 우상향 추세
  - **GC pause** — Major GC 빈도 / pause time 증가
  - **Connection leak** — DB pool, HTTP keepalive 누수
  - **File handle / socket** — `ulimit` 초과로 점진 실패
  - **Log / disk** — 로그 rotation 미설정 → disk full
  - **Cache 효과** — Warm cache 후 정상 vs cold start
- **Profiling 결합**:
  - JVM: `jcmd <pid> GC.heap_info`, JFR(Java Flight Recorder)
  - Node.js: `--heap-prof`, clinic.js
  - Go: pprof heap profile

**Soak 가 잡는 결함의 예**:
- "ThreadLocal 에서 큰 객체 안 지움" → 12 시간 후 OOM
- "DB connection 을 try-with-resources 없이 사용" → 6 시간 후 connection pool 고갈
- "메트릭 라이브러리 cardinality 폭발" → 24 시간 후 Prometheus scrape 실패

**장점**:
- 단기 부하 테스트로 못 잡는 누적 결함 탐지
- 실 prod 의 24/7 동작에 가장 가까운 검증
- Release-blocking 결함을 staging 에서 차단

**단점**:
- 시간·비용 부담 (인프라 24~72 시간 점유)
- 결함 재현까지 너무 길어서 디버깅 느림
- "어디서 새는가" 는 별도 profiling 필요

**활용 예시**:
- 메이저 릴리스 (분기 1 회) staging soak 48 시간
- 라이브러리 메이저 업그레이드 후 (Spring Boot, Kotlin 등)
- 신규 DB 드라이버 / connection pool 변경 시

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제 (메모리 추세 모니터링)**:
```kotlin
import java.lang.management.ManagementFactory

class HeapTrendMonitor(private val sampleSec: Long = 60) {
    private val memBean = ManagementFactory.getMemoryMXBean()
    private val samples = ArrayDeque<Pair<Long, Long>>()  // (ts, used heap)

    fun start() = Thread {
        while (!Thread.interrupted()) {
            val used = memBean.heapMemoryUsage.used
            samples += System.currentTimeMillis() to used
            if (samples.size > 1440) samples.removeFirst()  // 최근 24h (1min sample)
            check(!isLeaking()) { "Soak 결함 의심: heap 우상향" }
            Thread.sleep(sampleSec * 1_000)
        }
    }.apply { isDaemon = true; start() }

    /** 최근 60 샘플의 선형 회귀 기울기가 양수 + 시작값의 20% 초과 시 누수 의심 */
    private fun isLeaking(): Boolean {
        if (samples.size < 60) return false
        val recent = samples.takeLast(60)
        val first = recent.first().second.toDouble()
        val last  = recent.last().second.toDouble()
        return last > first * 1.2
    }
}
```

**관련 패턴**: Load Testing, Stress Testing, [observability.md] Profiling, [observability.md] Metrics

---

<a id="ab-multivariate-testing"></a>

## 7. A/B Testing / Multivariate

**목적**: 두 개 이상의 변종(variant) 을 실 사용자에게 무작위 노출하여 **통계적으로 유의한 차이** 가 있는지 검증합니다. 제품 의사결정의 인과 추론 도구.

**방법론·도구**:
- **A/B (2 variant)**: Control(A) vs Treatment(B) — 단일 변수 변경
- **A/B/n**: 3+ variant, 1 차원 비교 (예: 버튼 색 5 종)
- **Multivariate (MVT)**: 다차원 동시 비교 (버튼 색 × 카피 × 위치) — 조합 폭발 주의
- **통계적 접근**:
  - **Frequentist** (전통): p-value < 0.05, sample size 사전 계산, peeking 금지
  - **Bayesian**: posterior probability ("B 가 A 보다 좋을 확률 95%"), early stopping 가능
- **Sample size 계산** (frequentist):
  - n ≈ 16 × σ² / δ² (per variant, α=0.05, power=0.8)
  - 일일 user 수 / variant 수 → 최소 실험 기간 계산
- **도구**: Optimizely, LaunchDarkly Experimentation, Statsig, Eppo, Amplitude Experiment, GrowthBook (OSS)

**원칙** (Kohavi *Trustworthy Experiments*):
1. **OEC (Overall Evaluation Criterion)** — 단일 북극성 지표 사전 선언
2. **SRM check** — Sample Ratio Mismatch (50:50 으로 할당했는데 실제 53:47?) → 실험 신뢰성 무효
3. **Peeking 금지** — frequentist 에서 p-value 를 계속 보면서 중단 → false positive 폭증
4. **Twyman's law** — "너무 좋은 결과는 의심하라"
5. **Long-term holdout** — 단기 metric 개선이 장기 retention 해칠 수 있음

**장점**:
- 인과 추론 (단순 상관 X) — A 가 B 의 원인임을 입증
- 데이터 기반 의사결정, HiPPO(Highest Paid Person's Opinion) 회피
- 위험 정량화

**단점**:
- Sample size 부족 → 결론 못 냄 (작은 서비스에 부적합)
- Network effect / spillover (소셜 기능) — A 가 B 의 결과에 영향
- Novelty effect — 신기능은 단기에 좋아 보이지만 곧 사라짐
- 비즈니스 metric 의 noise 가 커서 lift 5% 도 잡기 어려움

**활용 예시**:
- 결제 페이지 button 카피 변경 → 전환율
- 추천 알고리즘 A vs B → CTR / Watch time
- 가격 인상 / 할인 정책 변경

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Python 예제 (Bayesian A/B — beta-binomial)**:
```python
import numpy as np

def bayesian_ab(success_a: int, n_a: int, success_b: int, n_b: int, samples: int = 100_000) -> dict:
    """Beta(1,1) prior, posterior P(B > A) 추정"""
    # Posterior: Beta(success + 1, n - success + 1)
    post_a = np.random.beta(success_a + 1, n_a - success_a + 1, samples)
    post_b = np.random.beta(success_b + 1, n_b - success_b + 1, samples)
    return {
        "P(B>A)": float((post_b > post_a).mean()),
        "lift":   float((post_b - post_a).mean() / post_a.mean()),
        "ci_95":  np.percentile(post_b - post_a, [2.5, 97.5]).tolist(),
    }

# 결제 페이지: A=기존(전환율 12%), B=신규(전환율 13%)
print(bayesian_ab(success_a=1200, n_a=10_000, success_b=1300, n_b=10_000))
# {'P(B>A)': 0.987, 'lift': 0.083, 'ci_95': [0.001, 0.019]}
# → 98.7% 확률로 B 가 A 보다 우수. 단, 절대 lift 는 1%p
```

**Kotlin 예제 (트래픽 할당 + SRM check)**:
```kotlin
class ExperimentAssigner(private val seed: String, private val splits: Map<String, Double>) {
    init { require(splits.values.sum() in 0.99..1.01) { "split 합 != 1.0" } }

    fun assign(userId: String): String {
        val hash = (userId + seed).hashCode().toUInt().toDouble() / UInt.MAX_VALUE.toDouble()
        var cum = 0.0
        for ((variant, p) in splits) { cum += p; if (hash <= cum) return variant }
        return splits.keys.last()
    }
}

/** Sample Ratio Mismatch — chi-square 로 할당 비율 검증 */
fun srmCheck(observed: Map<String, Int>, expected: Map<String, Double>): Double {
    val total = observed.values.sum()
    return observed.entries.sumOf { (k, obs) ->
        val exp = expected.getValue(k) * total
        (obs - exp) * (obs - exp) / exp
    }
    // chi-square > 3.84 (df=1, p=0.05) 이면 SRM 의심
}
```

**관련 패턴**: Canary Analysis, [feature-flag] Feature Flag, Synthetic Monitoring

---

<a id="synthetic-monitoring"></a>

## 8. Synthetic Monitoring

**목적**: 실 사용자 트래픽 없는 시간에도 **합성(synthetic) 트래픽** 으로 24/7 사용자 시나리오를 실행하여 장애·성능 저하를 *사용자보다 먼저* 감지합니다.

**방법론·도구**:
- **Probe 형태**:
  - **Heartbeat / Uptime** — `/health` 1 분 간격 GET (가장 단순)
  - **API check** — 핵심 endpoint 의 응답·schema 검증
  - **Browser check** — Playwright/Puppeteer 로 로그인 → 결제 시나리오 실행
  - **Multi-step transaction** — 여러 endpoint 를 순차 실행 (장바구니 → 결제 → 확인)
- **글로벌 분산** — 여러 region 에서 동시 실행 (지역별 latency 차이)
- **도구**: Datadog Synthetics, New Relic Synthetics, Pingdom, Uptime.com, Checkly, AWS CloudWatch Synthetics, Grafana Synthetic Monitoring
- **Real User Monitoring (RUM) 과의 관계**:
  - Synthetic: 일관된 baseline, 알람용
  - RUM: 실 사용자 분포 측정, 분석용
  - 둘 다 필요 — synthetic 으로 알람 → RUM 으로 영향 범위 파악

**알람 정책**:
- 단일 실패는 무시 (network blip) → 3 consecutive failure 시 알람
- 다중 region 동시 실패 → 즉시 페이지
- p95 가 baseline 의 200% 초과 시 warning

**장점**:
- 새벽·휴일에도 장애 즉시 감지 — MTTD(Mean Time To Detect) 단축
- "사용자보다 먼저" — 첫 사용자 불편 전에 알람
- 글로벌 가용성 측정 (region 별 SLA)
- 3rd-party 의존(결제 PG) 의 외부 시점 모니터링

**단점**:
- 실 사용자 행동 분포와 차이 (synthetic 는 항상 같은 user-agent, IP)
- 비용 — 분당 수십 region × 수십 시나리오 = 월 수백 $
- False positive — synthetic probe 가 rate limit 에 걸림 / 봇 차단
- 시나리오 유지보수 — UI 변경 시 selector 깨짐

**활용 예시**:
- 로그인 → 메인 피드 로딩 시나리오 (5 분 간격, 3 region)
- 결제 PG 의 sandbox 결제 시도 (15 분 간격) — 외부 dependency health
- API 의 GET /products 응답 schema 검증 (1 분 간격)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**JavaScript 예제 (Playwright synthetic — 로그인 + 결제 시나리오)**:
```javascript
const { chromium } = require('playwright');
const { Counter, Histogram, register } = require('prom-client');

const stepSuccess = new Counter({ name: 'synth_step_success_total', help: '', labelNames: ['step'] });
const stepLatency = new Histogram({ name: 'synth_step_duration_seconds', help: '', labelNames: ['step'] });

async function runScenario() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    // Step 1: 로그인
    let t = Date.now();
    await page.goto('https://example.com/login');
    await page.fill('#email', process.env.SYNTH_USER);
    await page.fill('#password', process.env.SYNTH_PASS);
    await page.click('button[type=submit]');
    await page.waitForURL(/\/home/);
    stepSuccess.inc({ step: 'login' });
    stepLatency.observe({ step: 'login' }, (Date.now() - t) / 1000);

    // Step 2: 상품 페이지
    t = Date.now();
    await page.goto('https://example.com/products/sku-123');
    await page.waitForSelector('[data-testid=add-to-cart]');
    stepSuccess.inc({ step: 'product' });
    stepLatency.observe({ step: 'product' }, (Date.now() - t) / 1000);

    // Step 3: 결제 (sandbox)
    t = Date.now();
    await page.click('[data-testid=add-to-cart]');
    await page.click('[data-testid=checkout]');
    await page.waitForSelector('[data-testid=order-confirmed]', { timeout: 10_000 });
    stepSuccess.inc({ step: 'checkout' });
    stepLatency.observe({ step: 'checkout' }, (Date.now() - t) / 1000);
  } finally {
    await browser.close();
  }
}

setInterval(runScenario, 5 * 60 * 1000);   // 5 분 간격
```

**관련 패턴**: Canary Analysis, Chaos Engineering, [observability.md] SLI/SLO, A/B Testing

---

<a id="canary-analysis"></a>

## 9. Canary Analysis

**목적**: Canary 배포 시 신/구 버전 간 메트릭을 **자동·통계적으로 비교** 하여 promote / rollback 을 무인으로 결정합니다. ([deployment.md](deployment.md) Canary Release 의 분석 엔진).

**방법론·도구**:
- **Netflix Kayenta** (Spinnaker) — Mann-Whitney U test 로 canary vs baseline 메트릭 비교
- **Flagger** — Prometheus / Datadog / NewRelic 메트릭 기반, Istio/Linkerd traffic weight
- **Argo Rollouts AnalysisTemplate** — PromQL / Datadog / Kayenta provider
- **분석 절차**:
  1. **Baseline** = 현재 prod 의 같은 시간대 메트릭 (어제 동시간, 1 주일 전)
  2. **Canary** = 신버전 inst 의 메트릭
  3. **Statistical test** — Mann-Whitney U / Welch's t-test
  4. **Score** — Pass / Marginal / Fail (예: <60 fail, 60-75 marginal, >75 pass)
- **분석 지표 (NALSD)**:
  - **N**etwork — req rate, error rate
  - **A**vailability — success rate, 5xx 비율
  - **L**atency — p50, p95, p99
  - **S**aturation — CPU, memory, GC
  - **D**ata — business KPI (전환율, 결제 성공률)

**중요 원칙**:
- **같은 traffic mix** — Canary 도 같은 user segment 가 동일 비율로 향해야 비교 가능 (random split)
- **Baseline 도 canary 와 동일한 새 인스턴스** (Kayenta) — "코드만 다른 인스턴스" 끼리 비교 (old code on new instance vs new code on new instance)
- **분석 기간** — 최소 30 분 (cold start, cache warm-up 고려)

**장점**:
- 사람 개입 없이 통계 기반 promote / rollback
- "비슷해 보임" 같은 직관 의존 제거
- 야간 배포 가능 (자동화)

**단점**:
- 메트릭 수집 인프라(Prometheus + service mesh) 선행 필요
- 작은 trafic 에서는 통계 검정력 부족
- "메트릭 통과" ≠ "비즈니스 OK" (silent correctness bug)

**활용 예시**:
- Netflix Spinnaker + Kayenta — 일 1000+ 배포 자동 promote
- Flagger + Istio — Kubernetes 서비스 메시 환경
- LinkedIn Iris — 자체 canary analysis 시스템

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**YAML 예제 (Argo Rollouts AnalysisTemplate)**:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: canary-analysis
spec:
  args:
    - name: service-name
    - name: namespace
  metrics:
    - name: success-rate
      interval: 1m
      count: 30                              # 30 분 분석
      successCondition: result[0] >= 0.99
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{
              namespace="{{args.namespace}}",
              service="{{args.service-name}}",
              status!~"5..",
              version="canary"
            }[1m]))
            /
            sum(rate(http_requests_total{
              namespace="{{args.namespace}}",
              service="{{args.service-name}}",
              version="canary"
            }[1m]))
    - name: latency-p99
      interval: 1m
      count: 30
      successCondition: result[0] < 0.5      # 500ms
      failureLimit: 2
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_seconds_bucket{
                version="canary"
              }[1m])) by (le))
---
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: payment-service
spec:
  strategy:
    canary:
      steps:
        - setWeight: 5
        - pause: { duration: 5m }
        - analysis:                          # 자동 분석
            templates: [{ templateName: canary-analysis }]
            args:
              - { name: service-name, value: payment }
              - { name: namespace,    value: prod }
        - setWeight: 50
        - pause: { duration: 5m }
        - analysis: { templates: [{ templateName: canary-analysis }] }
        - setWeight: 100
```

**Kotlin 예제 (Mann-Whitney U test — 간이 구현)**:
```kotlin
/** 두 표본 분포의 위치 차이 검정. p-value < 0.05 이면 차이 있음. */
fun mannWhitneyU(baseline: DoubleArray, canary: DoubleArray): Double {
    val merged = baseline.map { it to "B" } + canary.map { it to "C" }
    val ranked = merged.sortedBy { it.first }
        .mapIndexed { i, (v, g) -> Triple(v, g, i + 1.0) }
    val sumB = ranked.filter { it.second == "B" }.sumOf { it.third }
    val n1 = baseline.size; val n2 = canary.size
    val u = sumB - n1 * (n1 + 1) / 2.0
    val mean = n1 * n2 / 2.0
    val sd = kotlin.math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12.0)
    val z = (u - mean) / sd
    return 2 * (1 - normalCdf(kotlin.math.abs(z)))
}
```

**관련 패턴**: [deployment.md] Canary Release, A/B Testing, Synthetic Monitoring, Shadow Traffic Testing

---

<a id="shadow-traffic-testing"></a>

## 10. Shadow Traffic / Dark Launch Testing

**목적**: 프로덕션 트래픽을 **신규 시스템에 복제(mirror)** 하여 사용자 영향 없이 *실 데이터·실 부하* 에서 검증합니다.

**방법론·도구**:
- **Shadow / Mirroring**: 요청을 신/구에 동시 전송, 사용자에게는 구버전 응답만 반환
- **Dark Launch**: 신규 기능을 *코드만 배포* 하고 feature flag 로 비활성. 일부 internal user 에게만 노출
- **도구**:
  - **Istio VirtualService `mirror`** — gateway 가 트래픽 복제
  - **Envoy `request_mirror_policies`**
  - **Nginx `mirror`** 모듈
  - **AWS VPC Traffic Mirroring** — L3/L4 패킷 복제
  - **Diffy** (Twitter OSS) — old/new 응답 자동 diff
- **검증 방식**:
  - **Response diff** — 신/구 응답을 비교 (Diffy 가 noise field 자동 학습)
  - **메트릭 비교** — Canary Analysis 와 동일하지만 사용자 영향 0
  - **에러율** — 신규 시스템의 5xx, exception 발생률

**Shadow vs Canary vs A/B**:
| 측면 | Shadow | Canary | A/B |
|---|---|---|---|
| 사용자 영향 | 없음 (응답 버림) | 일부 사용자 | 일부 사용자 |
| 응답 비교 | 자동 diff | 메트릭만 | 비즈니스 KPI |
| 목적 | 회귀·정확성 | 성능·안정성 | 비즈니스 의사결정 |
| 위험 | 매우 낮음 | 낮음 | 중간 |
| Side effect | **주의** (DB write, 외부 API) | 정상 | 정상 |

**Side effect 주의** (가장 큰 함정):
- POST /order 를 mirror 하면 **신규 시스템도 결제 호출** → 사용자 1 회 결제가 2 회로
- 해결: (a) read-only endpoint 만 mirror, (b) shadow 시스템은 외부 호출을 mock, (c) idempotency key 로 dedup
- DB write 도 동일 — shadow 는 별도 DB / 별도 schema 사용 권장

**장점**:
- 사용자 영향 0 → 가장 안전한 실 환경 검증
- 실 트래픽 분포·edge case 노출 (synthetic 가 못 잡는 long tail)
- 신/구 응답 직접 비교 → 회귀 정확히 식별

**단점**:
- Side effect 처리 복잡 (DB write, payment, email)
- 인프라 비용 2 배 (shadow 시스템 + diff 분석)
- 응답 시간 분석은 의미 약함 (shadow 는 사용자 wait 없음)

**활용 예시**:
- 추천 알고리즘 v2 를 shadow 로 실 사용자 요청에 돌려서 v1 과 결과 diff
- 결제 처리 엔진 교체 — 새 엔진은 mock 결제, 결과 검증만
- 데이터 마이그레이션 후 신/구 DB 동시 조회 → 결과 비교 (consistency check)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**YAML 예제 (Istio VirtualService — Shadow / mirror)**:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: recommendation-shadow
spec:
  hosts: [recommendation]
  http:
    - route:
        - destination:
            host: recommendation
            subset: v1                       # 사용자 응답은 v1 에서
          weight: 100
      mirror:
        host: recommendation
        subset: v2                           # v2 에는 mirror — 응답 버림
      mirrorPercentage:
        value: 10.0                          # 10% 만 shadow (점진 확대)
```

**Kotlin 예제 (Diffy 스타일 응답 비교)**:
```kotlin
import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper

class ResponseDiffer(
    private val mapper: ObjectMapper = ObjectMapper(),
    /** noise field — timestamp, request id 같이 항상 다른 필드는 무시 */
    private val ignorePaths: Set<String> = setOf("/timestamp", "/requestId", "/traceId"),
) {
    fun diff(primary: String, shadow: String): List<Diff> {
        val p = mapper.readTree(primary)
        val s = mapper.readTree(shadow)
        return walk(p, s, "")
    }

    private fun walk(p: JsonNode, s: JsonNode, path: String): List<Diff> {
        if (path in ignorePaths) return emptyList()
        if (p.nodeType != s.nodeType) return listOf(Diff(path, p.toString(), s.toString()))
        if (p.isValueNode) return if (p == s) emptyList() else listOf(Diff(path, "$p", "$s"))
        return when {
            p.isObject -> p.fieldNames().asSequence().flatMap { f ->
                walk(p[f], s[f] ?: mapper.nullNode(), "$path/$f").asSequence()
            }.toList()
            p.isArray  -> p.zip(s).flatMapIndexed { i, (a, b) -> walk(a, b, "$path/$i") }
            else       -> emptyList()
        }
    }

    data class Diff(val path: String, val primary: String, val shadow: String)
}

fun main() {
    val differ = ResponseDiffer()
    val diffs = differ.diff(
        primary = """{"id":1,"items":[{"sku":"A","price":1000}],"timestamp":"2026-05-14T01:00:00Z"}""",
        shadow  = """{"id":1,"items":[{"sku":"A","price":1100}],"timestamp":"2026-05-14T01:00:01Z"}""",
    )
    println(diffs)   // [Diff(path=/items/0/price, primary=1000, shadow=1100)]
    // → 가격 계산 회귀 발견. timestamp 는 ignorePaths 라 무시됨.
}
```

**관련 패턴**: [deployment.md] Canary Release, [deployment.md] Dark Launch, Canary Analysis, A/B Testing

---

## 카탈로그 요약

| # | 패턴 | 적용 시점 | 사용자 영향 | 난이도 |
|---|---|---|---|---|
| 1 | Pyramid / Trophy / Diamond / Honeycomb | 개발 시 (테스트 작성 전략) | 없음 | 낮음 |
| 2 | Chaos Engineering | 프로덕션 | **제어된 영향** | 높음 |
| 3 | Load Testing | 릴리스 전 (staging) | 없음 | 중간 |
| 4 | Stress Testing | 분기·반기 capacity 계획 | 없음 (별도 환경) | 높음 |
| 5 | Spike Testing | 이벤트 직전 | 없음 (별도 환경) | 중간 |
| 6 | Soak / Endurance Testing | 메이저 릴리스 전 | 없음 | 중간 |
| 7 | A/B Testing | 프로덕션 | 일부 사용자 | 높음 |
| 8 | Synthetic Monitoring | 24/7 운영 | 없음 | 중간 |
| 9 | Canary Analysis | 배포 시 | 5~50% 사용자 | 높음 |
| 10 | Shadow / Dark Launch | 배포 검증 | 없음 | 높음 |

**선택 가이드**:
- 새 서비스 → **1** 로 분포 결정 → **3** baseline → **4** breaking point
- 배포 자동화 → **9** + **8** + **2** (단계적 도입)
- 신규 알고리즘 검증 → **10** (회귀 0%) → **7** (비즈니스 lift)
- 이벤트 대비 → **5** (spike) + **6** (long-running)
