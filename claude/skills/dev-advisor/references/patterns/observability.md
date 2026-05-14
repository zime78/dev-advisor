# 관찰 가능성 패턴 (Observability Patterns)

분산 시스템 내부 상태를 외부에서 측정 가능한 신호(Logs / Metrics / Traces)로 추론할 수 있도록 설계하는 패턴군. 단순 모니터링(이미 알고 있는 실패 조건 감시)을 넘어 "알 수 없는 미지(unknown unknowns)"까지 사후 진단 가능하게 만드는 것을 목표로 한다.

---

<a id="three-pillars"></a>

## 1. Three Pillars (Logs / Metrics / Traces)

**목적**: 관찰 가능성을 세 가지 상호 보완적 신호 — 로그(Logs), 메트릭(Metrics), 트레이스(Traces) — 로 분해하여 각 신호의 강점에 맞는 도구와 저장소를 분리합니다.

**특징**:
- **Logs**: 개별 이벤트의 시간순 텍스트 기록. 카디널리티 높음, 검색 비용 비쌈.
- **Metrics**: 시간 윈도우당 집계된 수치 (counter / gauge / histogram). 저비용, 카디널리티 제한.
- **Traces**: 단일 요청이 여러 서비스를 횡단하는 인과 경로. span 트리 구조.
- 세 축은 동일한 `trace_id` / `span_id` 로 상호 참조 가능해야 함 (correlation).

**장점**:
- 각 신호에 특화된 백엔드 선택 가능 (Loki / Prometheus / Tempo)
- 비용-카디널리티 트레이드오프를 신호별로 분리 결정
- 알람(metric) → 트레이스(span) → 로그(line) 드릴다운 워크플로우 자연스러움

**단점**:
- 세 저장소 운영 부담 (수집기 / 보존정책 / 쿼리언어 모두 상이)
- 신호 간 correlation 이 자동 보장되지 않음 — 명시적 ID 주입 필요
- "세 축으로 충분한가" 논쟁: events / profiles / dumps 추가 주장 (이른바 Observability 2.0 / wide events)

**활용 예시**:
- Grafana Stack: Loki(Logs) + Mimir(Metrics) + Tempo(Traces)
- Elastic Stack: ECS Logs + APM Metrics + APM Traces
- Datadog / New Relic / Honeycomb 통합 SaaS

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// OpenTelemetry 로 세 축을 하나의 SDK 로 발행
import io.opentelemetry.api.OpenTelemetry
import io.opentelemetry.api.trace.Tracer
import io.opentelemetry.api.metrics.Meter
import org.slf4j.LoggerFactory

class OrderService(otel: OpenTelemetry) {
    private val tracer: Tracer = otel.getTracer("order-service")
    private val meter: Meter = otel.getMeter("order-service")
    private val log = LoggerFactory.getLogger(javaClass)

    private val orderCounter = meter.counterBuilder("orders.created").build()

    fun create(orderId: String) {
        val span = tracer.spanBuilder("createOrder").startSpan()
        try {
            // Logs: 이벤트 단건 — trace_id 가 MDC 로 자동 주입됨
            log.info("creating order id={}", orderId)
            // Metrics: 집계 카운터 증가
            orderCounter.add(1)
            // Traces: span 자체가 인과 경로
            span.setAttribute("order.id", orderId)
        } finally {
            span.end()
        }
    }
}
```

**관련 패턴**: Distributed Tracing, Structured Logging, Correlation ID

---

## 2. Distributed Tracing

**목적**: 단일 요청이 여러 서비스 / 큐 / DB 를 횡단할 때, 각 구간(span)을 인과 관계가 있는 하나의 트리(trace)로 묶어 latency hotspot 과 의존 그래프를 가시화합니다.

**특징**:
- **Trace**: 하나의 논리적 요청. `trace_id` (16 byte) 로 식별.
- **Span**: trace 내 한 단위 작업. `span_id` (8 byte), 부모 `parent_span_id` 보유.
- **Context Propagation**: HTTP / gRPC / Kafka 헤더로 trace context 를 다음 hop 에 전달.
- **W3C TraceContext 표준 헤더**:
  - `traceparent: 00-{trace_id_32hex}-{span_id_16hex}-{trace_flags_2hex}` (예: `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`)
  - `tracestate: vendor1=value1,vendor2=value2` (벤더별 확장)
- **Sampling**: head-based (요청 시작 시 결정) / tail-based (전체 trace 수집 후 결정).

**장점**:
- 마이크로서비스 간 latency 의 어느 hop 이 병목인지 즉시 식별
- N+1 쿼리 / fan-out 폭발 / 순차 호출 anti-pattern 가시화
- exception → root cause span 직접 매핑

**단점**:
- 모든 서비스가 propagation 코드를 구현해야 함 (한 hop 만 빠져도 trace 끊김)
- 저장 비용 큼 — sampling 필수, 그러나 sampling 시 희귀 에러 trace 손실 위험
- Async 경계(메시지큐, 스레드풀)에서 context 전파 누락이 흔한 버그

**활용 예시**:
- OpenTelemetry SDK (현 표준, OpenTracing + OpenCensus 통합)
- Jaeger / Zipkin / Tempo / AWS X-Ray / GCP Cloud Trace
- Istio / Envoy 사이드카 자동 instrumentation

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// W3C TraceContext 전파 — HTTP client 에 헤더 자동 주입
import io.opentelemetry.api.OpenTelemetry
import io.opentelemetry.context.Context
import io.opentelemetry.context.propagation.TextMapSetter

class TracedHttpClient(private val otel: OpenTelemetry) {
    private val tracer = otel.getTracer("http-client")
    private val propagator = otel.propagators.textMapPropagator

    fun get(url: String): String {
        val span = tracer.spanBuilder("HTTP GET $url").startSpan()
        try {
            val headers = mutableMapOf<String, String>()
            // 현재 context 의 traceparent / tracestate 를 headers 맵에 주입
            propagator.inject(Context.current().with(span), headers,
                TextMapSetter { carrier, k, v -> carrier!![k] = v })
            // headers["traceparent"] == "00-{trace_id}-{span_id}-01"
            return httpGet(url, headers)
        } finally {
            span.end()
        }
    }

    private fun httpGet(url: String, headers: Map<String, String>): String = TODO()
}
```

**관련 패턴**: Correlation ID, Three Pillars, Sidecar

---

## 3. Correlation ID

**목적**: 분산 시스템에서 하나의 사용자 요청을 식별하는 단일 ID(`request_id` / `correlation_id`) 를 모든 로그·메트릭·downstream 호출에 일관되게 전파하여 사후 추적을 가능하게 합니다.

**특징**:
- 진입점(gateway / 첫 서비스) 에서 ID 생성 (UUID v4 / ULID / Snowflake) 또는 클라이언트 헤더 수용.
- HTTP `X-Request-ID` / `X-Correlation-ID` 헤더로 hop 간 전파. (W3C TraceContext 도입 시 `traceparent` 가 사실상 동일 역할 수행)
- 모든 로그 라인에 ID 가 자동 포함되도록 logging context(MDC / NDC) 에 설정.
- 비동기 작업 / 메시지큐로 넘어갈 때 message header 에 동봉.

**장점**:
- 장애 발생 시 단일 ID 검색으로 모든 서비스 로그 통합 조회
- 사용자 지원 — "이 에러 ID 알려주세요" 워크플로우
- Distributed Tracing 까지 가지 않더라도 최소한의 인과 추적 제공

**단점**:
- ID 전파 누락 시 trace 끊김 (특히 thread pool / coroutine context switch)
- 헤더 이름 표준 부재 — 조직마다 상이 (`X-Request-ID` / `X-Correlation-ID` / `X-Trace-ID`)
- 보안 — ID 자체가 enumeration 공격 벡터가 되지 않게 추측 불가능해야 함

**활용 예시**:
- API Gateway (Kong, AWS API Gateway, Envoy) 의 자동 헤더 생성
- Spring Cloud Sleuth 의 traceId / spanId MDC 주입
- Nginx `$request_id` 변수

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import org.slf4j.MDC
import java.util.UUID

// Servlet Filter — 요청마다 correlation ID 발급/수용 후 MDC 에 주입
class CorrelationIdFilter : jakarta.servlet.Filter {
    override fun doFilter(
        req: jakarta.servlet.ServletRequest,
        res: jakarta.servlet.ServletResponse,
        chain: jakarta.servlet.FilterChain
    ) {
        val httpReq = req as jakarta.servlet.http.HttpServletRequest
        val httpRes = res as jakarta.servlet.http.HttpServletResponse
        val cid = httpReq.getHeader("X-Correlation-ID") ?: UUID.randomUUID().toString()
        MDC.put("correlation_id", cid)
        httpRes.setHeader("X-Correlation-ID", cid)
        try {
            chain.doFilter(req, res) // 이후 모든 log.info 에 correlation_id 자동 포함
        } finally {
            MDC.remove("correlation_id")
        }
    }
}
```

**관련 패턴**: Distributed Tracing, Structured Logging, API Gateway

---

## 4. Structured Logging

**목적**: 로그를 자유 형식 텍스트가 아닌 구조화된 key-value (JSON / Logfmt) 로 출력하여 grep 대신 쿼리·집계·인덱싱을 가능하게 합니다.

**특징**:
- **JSON**: `{"ts":"...","level":"INFO","msg":"...","user_id":"u1","duration_ms":42}` — 중첩 가능, 기계 친화적.
- **Logfmt**: `ts=... level=INFO msg="..." user_id=u1 duration_ms=42` — 사람도 읽기 쉬움 (Heroku 기원).
- 메시지 템플릿과 데이터 분리 — `log.info("user logged in", "user_id", id)` (parameterized).
- timestamp / level / service / version / trace_id 등 공통 필드 강제.
- 비대칭 데이터(stack trace, request body) 는 별도 필드로 분리.

**장점**:
- Loki / Elasticsearch / BigQuery / CloudWatch Logs Insights 등에서 SQL/LogQL 로 직접 쿼리
- 알람·대시보드를 로그 필드 기반으로 구성
- 다국어 로그 메시지 변경에도 머신 파싱 안정적

**단점**:
- 사람 가독성 저하 — 개발 환경엔 pretty-print 별도 필요
- 로그 크기 증가 (key 이름 반복) — 압축 / 단축 키 고려
- 필드 폭주 — 새 필드 무분별 추가 시 인덱싱 비용 폭발

**활용 예시**:
- SLF4J + Logback `LogstashEncoder` / `JsonEncoder`
- Go: zap, zerolog, slog
- Python: structlog
- AWS Lambda Powertools, GCP Cloud Logging

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Logback 설정 (logback-spring.xml) — JSON encoder
// <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>

import net.logstash.logback.argument.StructuredArguments.kv
import org.slf4j.LoggerFactory

class PaymentService {
    private val log = LoggerFactory.getLogger(javaClass)

    fun charge(userId: String, amountKrw: Long) {
        val start = System.currentTimeMillis()
        try {
            // ...
            log.info("payment charged",
                kv("user_id", userId),
                kv("amount_krw", amountKrw),
                kv("duration_ms", System.currentTimeMillis() - start))
            // 출력: {"ts":"...","level":"INFO","msg":"payment charged",
            //        "user_id":"u1","amount_krw":10000,"duration_ms":42,
            //        "correlation_id":"...","trace_id":"..."}
        } catch (e: Exception) {
            log.error("payment failed", kv("user_id", userId), kv("error_class", e.javaClass.name), e)
        }
    }
}
```

**관련 패턴**: Correlation ID, Three Pillars, Audit Trail

---

## 5. RED Method (Rate / Errors / Duration)

**목적**: 모든 서비스(요청-응답 처리 단위) 에 대해 동일한 세 지표 — Rate(초당 요청수), Errors(실패율), Duration(latency 분포) — 만 측정하여 운영 대시보드를 표준화합니다.

**특징**:
- **Rate**: requests per second (RPS), counter rate.
- **Errors**: error rate (실패 요청수 / 전체 요청수) 또는 errors per second.
- **Duration**: latency histogram — p50 / p95 / p99 (단순 평균 사용 금지 — long tail 은닉).
- Tom Wilkie (Weaveworks → Grafana Labs) 가 명명. 마이크로서비스 표준 대시보드의 사실상 기본.
- 서비스 단위(service-level) — 외부에서 본 동작 측정.

**장점**:
- 모든 서비스에 동일 대시보드 / 알람 템플릿 적용 가능 (mass production)
- 신규 서비스 온보딩 시 측정 항목 고민 불필요
- USE 와 함께 쓰면 service ↔ resource 양면 커버

**단점**:
- 내부 큐 깊이 / 백프레셔 / 리소스 포화 같은 자원 측면은 측정 불가 → USE Method 보완 필요
- batch / streaming / 백그라운드 작업처럼 "요청" 단위가 모호한 경우 부적합
- "Error" 정의 — HTTP 5xx 만 셀지, 4xx 도 셀지, 비즈니스 실패도 셀지 합의 필요

**활용 예시**:
- Grafana 공식 마이크로서비스 대시보드
- Istio / Envoy 의 기본 서비스 메트릭 (이름 그대로 RED)
- Spring Boot Actuator + Micrometer `http.server.requests`

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import io.micrometer.core.instrument.MeterRegistry
import io.micrometer.core.instrument.Timer

class OrderApi(registry: MeterRegistry) {
    // Rate + Errors 는 Timer 의 count / 태그로 자동 산출됨
    private val timer = Timer.builder("http.server.requests")
        .tag("uri", "/orders")
        .publishPercentiles(0.5, 0.95, 0.99) // Duration: p50/p95/p99
        .publishPercentileHistogram()
        .register(registry)

    fun handle(): String {
        val sample = Timer.start()
        var status = "200"
        try {
            return doWork()
        } catch (e: Exception) {
            status = "500"
            throw e
        } finally {
            // 동일 timer 에 status 태그 분리 — errors 비율 계산용
            sample.stop(timer.tags("status", status) as Timer)
        }
    }

    private fun doWork(): String = "ok"
}
// 알람 예: rate(http_server_requests_seconds_count{status=~"5.."}[5m])
//        / rate(http_server_requests_seconds_count[5m]) > 0.01
```

**관련 패턴**: USE Method, Golden Signals, SLO / Error Budget

---

## 6. USE Method (Utilization / Saturation / Errors)

**목적**: 모든 리소스(CPU / Memory / Disk / Network / 스레드풀 / 커넥션풀) 에 대해 동일한 세 지표 — Utilization(사용률), Saturation(포화·대기열), Errors(에러 카운트) — 를 측정하여 시스템 병목을 신속히 식별합니다.

**특징**:
- **Utilization**: 리소스가 바쁜 시간 비율 (CPU %, 대역폭 사용률).
- **Saturation**: 리소스가 처리 못해 대기열에 쌓인 양 (run queue length, swap usage, thread pool queue size).
- **Errors**: 에러 이벤트 카운트 (disk I/O error, NIC drop count, OOM kill).
- Brendan Gregg (Netflix) 가 제안. 성능 분석 체크리스트 형식.
- 리소스 단위(resource-level) — 내부에서 본 동작 측정.

**장점**:
- 시스템 병목을 체계적·완전 망라적으로 점검 (체크리스트화 가능)
- RED 가 놓치는 큐 포화 / OS 레벨 문제 포착
- "느려졌다" 는 호소 시 어느 자원이 원인인지 즉시 좁힘

**단점**:
- 리소스 목록을 직접 열거해야 함 — 시스템마다 다름
- Saturation 측정이 까다로움 — OS 가 직접 노출 안 하는 큐가 많음 (예: filesystem dirty page)
- 비즈니스 의미 직접 매핑 어려움 — RED 와 병용 필수

**활용 예시**:
- node_exporter / cAdvisor (Prometheus) — CPU / Mem / Disk / Net 의 USE
- JVM: HikariCP active/idle/pending (커넥션풀 USE), ThreadPoolExecutor queue size
- Linux `vmstat` `iostat` `mpstat` 의 컬럼이 대부분 USE 의 직접 측정

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import io.micrometer.core.instrument.MeterRegistry
import io.micrometer.core.instrument.Gauge
import java.util.concurrent.ThreadPoolExecutor

class ThreadPoolMetrics(pool: ThreadPoolExecutor, registry: MeterRegistry) {
    init {
        // Utilization: 활성 스레드 / 코어 수
        Gauge.builder("threadpool.utilization") { pool.activeCount.toDouble() / pool.corePoolSize }
            .register(registry)
        // Saturation: 큐에 대기 중인 작업 수
        Gauge.builder("threadpool.saturation") { pool.queue.size.toDouble() }
            .register(registry)
        // Errors: rejected execution count
        Gauge.builder("threadpool.errors") { pool.rejectedExecutionHandler.let { 0.0 } /* RejectedHandler 카운터 */ }
            .register(registry)
    }
}
// RED (요청 측) + USE (자원 측) 를 동일 대시보드에 두면
// "외부 latency p99 증가" + "thread pool saturation 폭증" → 워커 부족 확정
```

**관련 패턴**: RED Method, Golden Signals, Bulkhead

---

## 7. Golden Signals (Latency / Traffic / Errors / Saturation)

**목적**: Google SRE 가 제안한 "사용자 관점에서 단 4개만 측정해도 시스템 건강을 90% 알 수 있다" 는 핵심 신호 — Latency / Traffic / Errors / Saturation — 를 모든 서비스의 기본 대시보드로 강제합니다.

**특징**:
- **Latency**: 요청 처리 시간 (성공/실패 분리 필수 — 빠르게 실패하는 에러가 정상 latency 를 가리지 않게).
- **Traffic**: 시스템 부하 측정치 (RPS, 메시지/초, 활성 세션 수).
- **Errors**: 명시적 실패 + 묵시적 실패 (200 응답이지만 잘못된 내용) + 정책 실패.
- **Saturation**: 시스템 한계 대비 여유 — "가장 제약된 자원이 얼마나 가득 찼는가".
- 출처: Google SRE Book Chapter 6 "Monitoring Distributed Systems".

**장점**:
- RED + USE 의 핵심만 추려 4축으로 단순화 — 임원/온콜 모두 이해
- 모든 서비스에 동일 알람 정책 표준화 가능
- Saturation 을 포함해 capacity planning 연결

**단점**:
- 4축 정의가 서비스마다 약간씩 다름 — 합의 비용
- batch 작업처럼 traffic / latency 정의가 모호한 경우 변형 필요

**RED 와의 관계**:
- **RED = Rate, Errors, Duration**  ⊂  **Golden Signals = Latency(=Duration) + Traffic(=Rate) + Errors + Saturation**
- 즉 Golden Signals 는 RED 의 **superset** — RED 에 Saturation 한 축을 더 얹은 형태로 이해하면 정확.
- 다만 시점이 다름: RED 는 "서비스의 입력-출력 관점" / Saturation 은 "자원 여유 관점" → Golden Signals 는 RED(service slice) + USE 의 Saturation(resource slice) 합성.

**활용 예시**:
- Google SRE Workbook 의 모든 예시 대시보드
- AWS Well-Architected Reliability Pillar
- Datadog / New Relic 의 service overview 페이지

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
import io.micrometer.core.instrument.MeterRegistry
import io.micrometer.core.instrument.Timer
import io.micrometer.core.instrument.Gauge

class GoldenSignals(registry: MeterRegistry, private val pool: java.util.concurrent.ThreadPoolExecutor) {
    // Latency + Traffic + Errors — RED 의 Timer 로 동시 수집
    val latency: Timer = Timer.builder("svc.requests")
        .publishPercentiles(0.5, 0.95, 0.99)
        .register(registry)

    init {
        // Saturation — 가장 제약된 자원: thread pool queue
        Gauge.builder("svc.saturation") {
            pool.queue.size.toDouble() / (pool.queue.size + pool.queue.remainingCapacity()).toDouble()
        }.register(registry)
    }
}
// 알람 4종 (Google SRE 권장):
//  - Latency: p99 > SLO
//  - Traffic: rate 가 평소 대비 ±50% 이탈
//  - Errors: 5xx 비율 > 1%
//  - Saturation: queue 사용률 > 80% 지속 5분
```

**관련 패턴**: RED Method, USE Method, SLO / Error Budget

---

## 8. SLO / Error Budget

**목적**: 가용성·latency 등 핵심 지표에 대해 **계약 가능한 목표치(SLO)** 를 명시하고, 그 미달분(Error Budget) 의 소진 속도에 따라 release 속도·운영 우선순위를 자동 조절합니다.

**특징**:
- **SLI** (Service Level Indicator): 측정 가능한 지표. 예 — `successful_requests / total_requests`.
- **SLO** (Service Level Objective): SLI 의 목표치. 예 — "30일 윈도우에서 99.9% 성공률".
- **SLA** (Service Level Agreement): 고객과의 계약 + 위반 시 페널티. 보통 SLO 보다 느슨하게 설정.
- **Error Budget** = `1 - SLO`. 99.9% SLO → 30일 동안 43.2분 다운 허용.
- **Burn Rate Alert**: budget 소진 속도 알람. 빠른 소진(예: 1시간 안에 budget 의 2% 소모 = burn rate 14.4) → 페이저, 느린 소진 → 티켓.
  - 다중 윈도우 burn rate 알람 (Google SRE Workbook Chapter 5): short window(예: 5m) + long window(예: 1h) 동시 burn rate 초과 시만 알람 → 단발 spike false-positive 제거.

**장점**:
- "100% 가용성" 의 비현실성 제거 — 의도적으로 budget 소비 가능
- 개발팀과 SRE 사이의 release 속도 vs 안정성 논쟁을 수치로 환원
- budget 소진 시 "feature freeze" 같은 자동 정책 결정

**단점**:
- SLI 정의가 어렵다 — "성공"의 정의가 endpoint 마다 다름
- 윈도우 선택(rolling 28d / calendar month) 에 따라 결론 달라짐
- 사용자 영향 ≠ SLI 인 경우 많음 — multi-region partial outage 등

**활용 예시**:
- Google SRE Workbook (Implementing SLOs)
- Sloth / OpenSLO / Nobl9 (SLO-as-code)
- Prometheus + Grafana SLO 대시보드 (slo-libsonnet)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// SLI 계산: 30일 rolling window 의 성공률
// PromQL: sum(rate(http_requests_total{status!~"5.."}[30d]))
//       / sum(rate(http_requests_total[30d]))

// Multi-window burn rate alert (Google SRE Workbook 권고):
// SLO = 99.9% → error budget = 0.1%
// Page (긴급): burn_rate(1h) > 14.4 AND burn_rate(5m) > 14.4   (2% budget / 1h 소진)
// Page (느림): burn_rate(6h) > 6   AND burn_rate(30m) > 6      (5% budget / 6h 소진)
// Ticket:      burn_rate(3d) > 1   AND burn_rate(6h) > 1       (10% budget / 3일 소진)

import io.micrometer.core.instrument.MeterRegistry
class SloRecorder(registry: MeterRegistry) {
    private val good = registry.counter("slo.events", "result", "good")
    private val bad  = registry.counter("slo.events", "result", "bad")

    fun record(success: Boolean) {
        if (success) good.increment() else bad.increment()
    }
}
// Error budget 소진 정책 예시:
//  - budget > 50% 남음 → 모든 release 허용
//  - 50% > budget > 10% → canary 강제, rollback 자동화 확인
//  - budget < 10% → feature freeze, 안정화 작업만
```

**관련 패턴**: Golden Signals, RED Method, Canary Release

---

## 9. Health Endpoint Monitoring

**목적**: 서비스 내부 상태를 외부 헬스체커가 가볍게 폴링할 수 있는 표준 HTTP 엔드포인트(`/healthz`, `/readyz`, `/livez`) 로 노출하여 로드밸런서·오케스트레이터의 자동화된 라우팅·재시작 결정을 지원합니다.

**특징**:
- Kubernetes 의 세 프로브가 사실상 표준 분류:
  - **Liveness Probe** — "프로세스가 살아있나? 데드락 아닌가?" 실패 시 → **컨테이너 재시작**.
  - **Readiness Probe** — "트래픽 받을 준비됐나? DB / 캐시 워밍업 끝났나?" 실패 시 → **Service endpoint 에서 제외** (재시작 안 함).
  - **Startup Probe** — "초기화 중인가?" 성공 전엔 liveness/readiness 비활성. **느린 시작(JVM warm-up, migration)** 의 false-positive 재시작 방지.
- HTTP 200 = healthy, 503 Service Unavailable = unhealthy 가 관례.
- Deep health check (`/healthz?deep=1`) — DB·외부 API 까지 점검, 보통 5xx 까지 propagate 하지 않고 메트릭에만 반영.

**Liveness vs Readiness vs Startup 차이**:

| Probe | 실패 시 행동 | 사용 시점 | 점검 대상 |
|---|---|---|---|
| Liveness | 컨테이너 kill + 재시작 | 평상시 지속 | "프로세스 자체가 회복 불가능한 상태인가" (deadlock, infinite loop) |
| Readiness | LB / Service endpoint 에서 제외 (재시작 안 함) | 평상시 지속 | "지금 이 순간 트래픽 받을 수 있는가" (warmup, dep 다운, 과부하) |
| Startup | startup 성공 전엔 liveness/readiness 평가 안 함 | 부팅 직후만 | "초기화 단계인가" — 느린 부팅을 liveness 가 죽이지 않게 보호 |

**장점**:
- 자동 복구 — 무응답 인스턴스 격리·재시작 자동화
- 무중단 배포 — readiness 가 빠지면 LB 가 트래픽 차단 후 종료
- 운영 표준화 — 모든 서비스가 동일 경로 노출

**단점**:
- Liveness 에 deep check 넣으면 **재시작 폭풍** — DB 장애가 모든 앱 재시작으로 증폭
- Readiness 가 너무 엄격하면 **gray failure** — 인스턴스가 전부 readiness 실패해 0대 가용 상태
- 인증 미적용 endpoint 면 정보 누출 (버전·내부 의존 상태)

**활용 예시**:
- Kubernetes `livenessProbe` / `readinessProbe` / `startupProbe`
- AWS ALB / GCP LB 의 헬스체크 경로
- Spring Boot Actuator `/actuator/health` (그룹: liveness / readiness)
- Consul / Eureka health check 핸들러

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Boot Actuator 사용 — 그룹 health 로 liveness / readiness 분리
// management.endpoint.health.probes.enabled=true
// management.endpoint.health.group.liveness.include=livenessState
// management.endpoint.health.group.readiness.include=readinessState,db,redis

import org.springframework.boot.actuate.health.Health
import org.springframework.boot.actuate.health.HealthIndicator
import org.springframework.stereotype.Component
import javax.sql.DataSource

@Component
class DbReadinessIndicator(private val ds: DataSource) : HealthIndicator {
    override fun health(): Health = try {
        ds.connection.use { it.isValid(1) }
        Health.up().build()
    } catch (e: Exception) {
        // Readiness 만 실패시킴 — liveness 는 별도, DB 다운으로 재시작 폭풍 방지
        Health.outOfService().withException(e).build()
    }
}
// k8s manifest 예:
//  startupProbe:    httpGet /actuator/health/liveness  failureThreshold=30 periodSeconds=10  // 5분 부팅 허용
//  livenessProbe:   httpGet /actuator/health/liveness  failureThreshold=3
//  readinessProbe:  httpGet /actuator/health/readiness failureThreshold=3
```

**관련 패턴**: Circuit Breaker, Bulkhead, Graceful Shutdown

---

## 10. Audit Trail

**목적**: 보안·규제·포렌식 목적에 필요한 행위(누가 / 언제 / 무엇을 / 어떻게) 를 일반 운영 로그와 **분리된 append-only 저장소** 에 변조 방지(tamper-resistant) 형태로 영구 기록합니다.

**특징**:
- **Append-only**: 수정·삭제 API 불제공. 백엔드 자체가 immutable (예: object storage WORM, S3 Object Lock, append-only DB table with revoke UPDATE/DELETE).
- **Tamper-resistant**: 해시 체인(이전 레코드 hash 를 다음 레코드에 포함) 또는 서명(HMAC / KMS-signed) 으로 후소급 변조 탐지.
- **Retention 정책**: 규제 기반 보존 기간 명시 (PCI-DSS 1년 / SOX 7년 / GDPR 정당 사유 한정). 동시에 GDPR "잊혀질 권리" 와 충돌하므로 PII 가명화·암호화 + 키 폐기로 우회.
- **High-cardinality OK**: 일반 로그와 달리 user_id / resource_id 를 풀로 보존 (집계 아님).
- **분리된 권한**: 일반 ops 가 읽기/쓰기 못 함 — 작성은 시스템 계정, 조회는 보안/감사팀만.
- **표준 필드**: `who(actor_id)`, `when(ts UTC)`, `what(action)`, `where(resource_id)`, `how(method/ip/user_agent)`, `result(success/failure)`, `correlation_id`.

**장점**:
- 보안 사고 시 공격 경로 재구성 가능
- 규제 감사 대응 (SOX / HIPAA / PCI-DSS / GDPR / K-ISMS)
- 내부 부정 탐지 — 관리자 권한 오남용 추적

**단점**:
- 저장 비용 — 보존 기간 길고 삭제 불가
- PII 보호와 충돌 — 가명화·암호화·키 lifecycle 관리 추가 부담
- write 경로가 핵심 트랜잭션과 묶이면 latency·가용성 증가 — outbox / async 발행 패턴 필요

**활용 예시**:
- AWS CloudTrail / GCP Cloud Audit Logs / Azure Activity Log
- 금융권 거래 원장 — append-only ledger
- Linux `auditd`, Kubernetes audit policy
- 의료기록 EMR 의 access log

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
import com.fasterxml.jackson.databind.ObjectMapper
import java.security.MessageDigest
import java.time.Instant

data class AuditRecord(
    val ts: Instant,
    val actorId: String,
    val action: String,            // "user.delete", "config.update"
    val resourceId: String,
    val ip: String,
    val result: String,            // "success" | "failure"
    val correlationId: String,
    val prevHash: String,          // 직전 레코드 hash → 해시 체인
    val hash: String               // sha256(prevHash || canonicalJson(this without hash))
)

class AuditWriter(
    private val store: AuditStore,   // append-only 백엔드 (e.g. S3 Object Lock)
    private val mapper: ObjectMapper
) {
    @Synchronized
    fun write(actor: String, action: String, resource: String, ip: String,
              result: String, cid: String) {
        val prev = store.latestHash() ?: "GENESIS"
        val partial = mapOf(
            "ts" to Instant.now().toString(),
            "actor_id" to actor, "action" to action, "resource_id" to resource,
            "ip" to ip, "result" to result, "correlation_id" to cid,
            "prev_hash" to prev
        )
        val bytes = mapper.writeValueAsBytes(partial)
        val hash = MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }
        store.append(partial + ("hash" to hash))
        // 후소급 변조 시 어느 레코드부터 체인이 깨졌는지 검증 가능
    }
}

interface AuditStore {
    fun latestHash(): String?
    fun append(record: Map<String, Any>)
}
// Retention 정책 예시:
//  - 금융 거래: 10년 (자금세탁방지법)
//  - 접근 로그: 2년 (개인정보보호법)
//  - PII 필드: KMS data-key 로 암호화 → 보존 종료 시 키 폐기로 사실상 삭제(crypto-shredding)
```

**관련 패턴**: Structured Logging, Event Sourcing, Correlation ID

---
