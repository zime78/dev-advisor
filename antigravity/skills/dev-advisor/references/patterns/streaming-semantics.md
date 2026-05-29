# 스트림 처리 의미론 (Stream Processing Semantics)

Tyler Akidau *Streaming Systems* (O'Reilly, 2018) 의 9 핵심 의미론. **Apache Beam / Flink / Kafka Streams / Spark Structured Streaming / Pulsar Functions** 의 기반.

**원전·표준 참고**:
- Tyler Akidau, Slava Chernyak, Reuven Lax — *Streaming Systems* (O'Reilly, 2018)
- Apache Beam Programming Guide — https://beam.apache.org/documentation/programming-guide/
- Apache Flink Documentation — Event Time, Watermarks, Windows
- The Dataflow Model (Akidau et al., VLDB 2015)
- Tyler Akidau — "Streaming 101 / 102" blog (O'Reilly)
- Chandy-Lamport algorithm (1985) — distributed snapshot

**핵심 4 질문 (Akidau)**:
- **What** results are calculated? — Aggregation
- **Where** in event time are they calculated? — Windowing
- **When** in processing time are they materialized? — Triggering + Watermarks
- **How** do refinements relate? — Accumulation modes

**관련 카탈로그**:
- [integration.md](integration.md) — Pub-Sub / Aggregator / Splitter (EIP)
- [reactive-streams.md](reactive-streams.md) — Cold/Hot, Backpressure (reactive 본체)
- [reliability.md](reliability.md) — Backpressure 구현 패턴
- [`../algorithms/concurrent.md`](../algorithms/concurrent.md) — Chandy-Lamport 알고리즘
- [`../principles/concurrency-theory.md`](../principles/concurrency-theory.md) — Linearizability / Causal Consistency

---

<a id="1-delivery-semantics"></a>
## 1. Delivery Semantics (전달 의미론 — At-Most-Once / At-Least-Once / Exactly-Once)

**정의**: 스트림 처리 시스템이 각 레코드를 **몇 번 처리·전달하는지** 에 대한 보장 수준. 3 단계로 구분되며 강도가 높을수록 비용·복잡도 증가. Akidau *Streaming Systems* Ch.5 의 핵심 주제.

**메커니즘**:

| 의미론 | 보장 | 메커니즘 | 실패 시 |
|---|---|---|---|
| **At-Most-Once** | 0 또는 1회 | fire-and-forget. ACK 없음 | 메시지 유실 가능 |
| **At-Least-Once** | 1회 이상 | producer retry + consumer ACK. **중복 가능** | 재처리로 중복 |
| **Exactly-Once** | 정확히 1회 (effectively-once) | idempotent producer + transactional commit (input offset + state + output 원자성) | 자동 복구, 결과 1회 |

**Exactly-Once 의 진실 (Akidau Ch.5)**:
- 네트워크 분할 상황에서 "메시지 전달 1회" 는 FLP impossibility 로 **불가능**
- 실제로는 **effectively-once** — 외부 관측 결과가 1회처럼 보이도록 보장
- 핵심: **idempotent side-effect** + **트랜잭션 커밋** (input offset commit + state checkpoint + output emit 을 한 트랜잭션)

**Kafka Exactly-Once (KIP-98 / KIP-129)**:
```
Producer:  enable.idempotence=true (PID + seq number → broker 중복 제거)
           transactional.id="tx-1" (producer fencing)
Consumer:  isolation.level=read_committed (aborted tx 건너뛰기)
Stream:    processing.guarantee="exactly_once_v2"
           → consume(input) + produce(output) + commit(offset) 원자성
```

**Flink Exactly-Once (Two-Phase Commit Sink)**:
```
1. Checkpoint barrier 흐름 → 모든 operator state snapshot
2. Sink: preCommit (외부 시스템에 pending write)
3. JobManager 가 모든 ack 수신 → commit (외부 시스템에 visible)
4. 실패 시: 마지막 성공 checkpoint 에서 재시작, pending 은 abort
```

**장점**:
- Exactly-Once: 비즈니스 로직이 멱등성 신경 안 써도 됨
- At-Least-Once: 비용 낮음, 멱등 sink (UPSERT/SET) 와 조합하면 충분
- At-Most-Once: 최고 처리량, metric/log 수집처럼 유실 허용 시

**단점·trade-off**:
- Exactly-Once: 처리량 20-40% 하락 (transactional commit 오버헤드), latency 증가 (transaction timeout 단위)
- At-Least-Once: 다운스트림 멱등성 책임 전가 (DB UPSERT, dedup table)
- At-Most-Once: 모니터링·결제 시스템에 부적합

**실제 구현**:
- **Kafka Streams** — `processing.guarantee="exactly_once_v2"` (default at-least-once)
- **Flink** — TwoPhaseCommitSinkFunction 기반 Kafka/JDBC/File sink
- **Beam** — runner 별 (Dataflow: exactly-once, Flink runner: 설정)
- **Pulsar Functions** — `--processing-guarantees EFFECTIVELY_ONCE`

**Kafka 예제 (Exactly-Once Stream)**:
```kotlin
import org.apache.kafka.streams.StreamsConfig
import org.apache.kafka.streams.kstream.KStream

val props = Properties().apply {
    put(StreamsConfig.APPLICATION_ID_CONFIG, "order-processor")
    put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2)
    put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092")
    // transactional.id 자동 생성, isolation.level=read_committed 자동 설정
}

val builder = StreamsBuilder()
val orders: KStream<String, Order> = builder.stream("orders")
orders
    .filter { _, order -> order.amount > 0 }
    .mapValues { order -> order.copy(processedAt = Instant.now()) }
    .to("processed-orders")
// consume + transform + produce + commit 이 한 transaction 으로 묶임
```

**관련 패턴**: [Checkpoint / Savepoint](#8-checkpoint-savepoint), [Stateful Stream](#7-stateful-stream), [reliability.md / Idempotency](reliability.md)

---

<a id="2-event-time-processing-time"></a>
## 2. Event Time vs Processing Time (이벤트 시각 vs 처리 시각)

**정의**: 스트림에서 *시각* 의 두 가지 정의.
- **Event time**: 사건이 *실제 발생한* 시각 (센서·모바일·로그 생성 시각, payload 안에 들어있음)
- **Processing time**: 사건이 시스템에서 *관측된* 시각 (스트림 엔진의 wall clock)

Akidau *Streaming Systems* Ch.1 의 첫 챕터 주제. **Dataflow Model (VLDB 2015)** 이 처음 1급 시민으로 분리.

**메커니즘**:
```
실제 세계 (event time):
  09:00 -- e1 --
  09:01 -- e2 -- (네트워크 지연 5분)
  09:02 -- e3 --

시스템 관측 (processing time):
  09:00 -- e1 도착 --
  09:02 -- e3 도착 --
  09:06 -- e2 도착 ★ late arrival
              ↑
        event time 09:01 인데 processing time 09:06
        skew = 5 분
```

**왜 둘이 다른가**:
- 모바일 오프라인 → 온라인 복귀 시 batch 업로드 (수 시간 skew)
- 네트워크 지연·재전송
- 분산 시스템에서 출발 시각과 처리 시각이 다른 머신

**Event time 처리의 핵심 도전**:
1. **순서가 뒤섞임** — late event 가 나중에 도착
2. **완결성 알 수 없음** — "더 이상 늦은 이벤트 안 올 거야" 를 어떻게 판단? → **Watermark**
3. **무한 버퍼링 불가능** — 언제까지 기다리지? → **Allowed Lateness + GC**

**장점 (Event time 사용)**:
- 비즈니스 의미가 정확함 (실제 발생 시각 기준 집계)
- 재처리 (reprocessing) 가능 — 같은 입력 → 같은 출력 (deterministic)
- A/B test, billing, fraud detection 에 필수

**단점 (Processing time 만 사용 시)**:
- "오전 9시 매출" 이 도착 지연 데이터 때문에 부정확
- 시스템 부하·네트워크 상태에 따라 결과 변동 (non-deterministic)
- 재처리 시 다른 결과 (wall clock 다름)

**실제 구현**:
- **Beam** — `Window.into(FixedWindows.of(...))` 가 기본 event time, processing time 은 명시적 설정
- **Flink** — `env.setStreamTimeCharacteristic(EventTime)`, `assignTimestampsAndWatermarks(...)`
- **Kafka Streams** — `TimestampExtractor` 인터페이스 (default: record timestamp, custom: payload extract)

**Flink 예제 (event time 추출 + watermark)**:
```kotlin
import org.apache.flink.streaming.api.windowing.time.Time
import org.apache.flink.streaming.api.functions.timestamps.BoundedOutOfOrdernessTimestampExtractor

data class ClickEvent(val userId: String, val timestamp: Long, val url: String)

val clicks: DataStream<ClickEvent> = env
    .addSource(kafkaSource)
    .assignTimestampsAndWatermarks(
        // event time 추출 + 5초 out-of-order 허용
        WatermarkStrategy
            .forBoundedOutOfOrderness<ClickEvent>(Duration.ofSeconds(5))
            .withTimestampAssigner { event, _ -> event.timestamp }
    )

// 이후 window 연산은 event time 기반
clicks
    .keyBy { it.userId }
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    .sum("count")
```

**Processing time vs Event time 의사결정**:

| 케이스 | 선택 | 이유 |
|---|---|---|
| 실시간 알림 (5초 내) | Processing time | 정확성보다 latency 우선 |
| 일/시간별 집계 (billing) | Event time | 정확성 필수, 재처리 가능해야 |
| 모니터링 metric | Processing time | 시스템 상태 측정이 목적 |
| 사용자 행동 분석 | Event time | 모바일 오프라인 데이터 정확히 |

**관련 패턴**: [Watermark](#3-watermark), [Windowing](#4-windowing-patterns), [Allowed Lateness](#6-allowed-lateness)

---

<a id="3-watermark"></a>
## 3. Watermark (워터마크)

**정의**: "**event time T 이전 데이터는 (대부분) 도착 완료** 됐다" 를 시스템이 표시하는 **단조 증가 시각 마크**. Akidau *Streaming Systems* Ch.3 의 핵심 도구. *언제 window 를 닫고 결과를 emit 할지* 의 신호.

**메커니즘**:
- Watermark = 현재 시점에서 시스템이 추정한 *event time 의 진행도*
- 단조 증가 (절대 뒤로 가지 않음)
- Watermark(T) 가 흐르면 → event time ≤ T 인 모든 window 의 트리거 발생
- Watermark 통과 후 도착하는 이벤트 = **late event** (별도 처리)

**Perfect Watermark vs Heuristic Watermark (Akidau Ch.3.2)**:

| 종류 | 정의 | 적용 |
|---|---|---|
| **Perfect** | 모든 데이터를 정확히 안다 (유한 batch, 강한 ordering 보장) | Kafka 단일 파티션 + ordered key, replay from log |
| **Heuristic** | 추정값. late event 가능성 인정 | 대부분의 실시간 스트림 (Pub-Sub 등 unordered) |

대부분의 실시간 시스템은 **heuristic** — late event 처리 정책 (`allowedLateness`) 이 필수.

**Bounded Out-of-Orderness (Flink 표준 전략)**:
```
Watermark(t) = max(observed_event_time) - max_out_of_orderness

예) 최근 관측된 event time = 12:00:30
    max_out_of_orderness = 5초
    → Watermark = 12:00:25
    → window [12:00:00, 12:00:25) 는 닫혀도 됨
```

**Watermark 흐름 다이어그램**:
```
Event time:    09:00   09:01   09:02   09:03   09:04   09:05
                 |       |       |       |       |       |
이벤트 도착:    e1 ────► e3 ────► e5 ──── e2 (late!) ────► e4
                 (09:00)  (09:02)  (09:04)  (09:01)        (09:03)
                                            ↑
                                            watermark 09:03 이후 도착
                                            → late event

Watermark:     w1=08:55 ─► w2=08:57 ─► w3=09:00 ─► w4=09:03 ─► ...
                            (max_event - 5초)
```

**Watermark 의 두 면**:
1. **완결성 신호 (Completeness)** — 이 시각 이전 데이터는 다 봤다고 가정
2. **진행도 신호 (Progress)** — 다운스트림 operator 에게 "여기까지 진행됐어" 알림 (timer 트리거)

**장점**:
- event time 처리의 *완결성 추정* 을 정형화
- window 트리거의 정확한 기준 제공
- multi-stage 파이프라인에서 stage 간 진행도 전파

**단점·trade-off**:
- Heuristic 은 *틀릴 수 있음* — late event 발생 → allowed lateness 필요
- watermark 가 너무 보수적 (느림) → 결과 latency 증가
- watermark 가 너무 공격적 (빠름) → late event 다수 발생

**실제 구현**:
- **Flink** — `WatermarkStrategy` (`forBoundedOutOfOrderness`, `forMonotonousTimestamps`, custom)
- **Beam** — runner 가 source 별로 watermark 추정 (Kafka, Pub/Sub 등)
- **Kafka Streams** — stream time 개념 (per-partition max event time, watermark 의 단순화 버전)
- **Spark Structured Streaming** — `withWatermark("eventTime", "10 minutes")` API

**Flink 예제 (커스텀 watermark)**:
```kotlin
val watermarkStrategy = WatermarkStrategy
    .forGenerator<Event> { _ ->
        object : WatermarkGenerator<Event> {
            private var maxTimestamp = Long.MIN_VALUE
            private val outOfOrderness = 3000L // 3초

            override fun onEvent(event: Event, eventTimestamp: Long, output: WatermarkOutput) {
                maxTimestamp = maxOf(maxTimestamp, eventTimestamp)
            }

            override fun onPeriodicEmit(output: WatermarkOutput) {
                // 200ms 마다 자동 호출
                output.emitWatermark(Watermark(maxTimestamp - outOfOrderness - 1))
            }
        }
    }
    .withTimestampAssigner { event, _ -> event.timestamp }

env.fromSource(source, watermarkStrategy, "events")
```

**Idle source 문제**: 한 파티션이 데이터 안 보내면 (kafka idle partition) 그 파티션의 watermark 가 멈춰서 전체 진행 정지. → `withIdleness(Duration.ofSeconds(30))` 로 idle source 무시 설정.

**관련 패턴**: [Event Time](#2-event-time-processing-time), [Triggering](#5-triggering), [Allowed Lateness](#6-allowed-lateness)

---

<a id="4-windowing-patterns"></a>
## 4. Windowing 패턴 (윈도잉 — Tumbling / Sliding / Session / Hopping / Global)

**정의**: 무한 스트림을 **유한 단위로 자르는** 방법. Akidau "Streaming 102" 의 *Where* 질문 (in event time, where are results calculated?). Beam 의 `Window` PTransform 이 5 가지 표준 형태 제공.

**5 종 window 비교**:

| Window 종류 | 정의 | 겹침 | 사용 사례 |
|---|---|---|---|
| **Tumbling (Fixed)** | 고정 크기, 비중첩 | 없음 | 시간당 매출, 분당 PV |
| **Sliding (Hopping)** | 크기 W, 슬라이드 S (S < W) | 있음 | 5분 이동평균 (1분마다) |
| **Session** | 비활동 간격으로 자동 분할 | 없음 | 사용자 세션, 차량 운행 |
| **Global** | 전체 = 한 window | - | trigger 로 제어 시 |
| **Custom** | 사용자 정의 | 임의 | 도메인 특화 |

**Tumbling Window 다이어그램**:
```
event time:  09:00          09:05          09:10          09:15
                |              |              |              |
                |── window 1 ──|── window 2 ──|── window 3 ──|
                  [09:00,09:05)  [09:05,09:10)  [09:10,09:15)
                  각 5분, 비중첩
```

**Sliding Window 다이어그램** (크기 10분, 슬라이드 5분):
```
event time:  09:00     09:05     09:10     09:15
                |─────w1─────|
                          |─────w2─────|
                                    |─────w3─────|
한 이벤트가 여러 window 에 속함
```

**Session Window 다이어그램** (gap 5분):
```
events:    09:01  09:02  09:04 .....gap..... 09:15  09:17
            └─── session 1 ───┘             └ session 2 ┘
            (자동 병합)                       (5분 이상 빈 후 새 세션)
```

**장점·사용처**:
- **Tumbling**: 가장 단순. 시간/분/일 단위 집계 (가장 흔함)
- **Sliding**: smooth metric, fraud detection (60분 동안 발생한 트랜잭션을 1분마다)
- **Session**: 사용자 활동 그룹화 (Beam 의 강력한 무기, batch 로는 표현 어려움)
- **Global**: trigger 로 제어할 때, 또는 unbounded → bounded 변환

**단점·trade-off**:
- **Sliding**: 한 이벤트가 N 개 window 에 속함 → state 비용 N 배
- **Session**: dynamic merging 필요 → state backend 부담
- **Tumbling**: 경계 효과 (boundary effect) — 09:04:59 와 09:05:01 은 다른 window

**실제 구현**:
- **Beam** — `Window.into(FixedWindows.of(Duration.standardMinutes(5)))`, `Sessions.withGapDuration(...)`
- **Flink** — `TumblingEventTimeWindows`, `SlidingEventTimeWindows`, `EventTimeSessionWindows`
- **Kafka Streams** — `TimeWindows.of(...)`, `SessionWindows.with(...)`
- **Spark Structured Streaming** — `window(col("ts"), "5 minutes", "1 minute")`

**Beam 예제 (5 window 모두)**:
```kotlin
import org.apache.beam.sdk.transforms.windowing.*

// 1. Tumbling: 5분 고정
input.apply(Window.into(FixedWindows.of(Duration.standardMinutes(5))))

// 2. Sliding: 10분 크기, 1분 슬라이드
input.apply(Window.into(
    SlidingWindows.of(Duration.standardMinutes(10))
        .every(Duration.standardMinutes(1))
))

// 3. Session: 10분 비활동 gap
input.apply(Window.into(Sessions.withGapDuration(Duration.standardMinutes(10))))

// 4. Global: + trigger 로 제어 필수
input.apply(Window.into<KV<String, Long>>(GlobalWindows())
    .triggering(AfterPane.elementCountAtLeast(100))
    .discardingFiredPanes())

// 5. Calendar window (custom): 매월 1일 기준
input.apply(Window.into(CalendarWindows.months(1)))
```

**Window assignment timing**: 이벤트가 들어오면 *즉시* window 에 할당 (event time 기반). 트리거가 발생할 때까지 buffer 에 누적, watermark 통과 시 emit.

**관련 패턴**: [Event Time](#2-event-time-processing-time), [Triggering](#5-triggering), [Stateful Stream](#7-stateful-stream)

---

<a id="5-triggering"></a>
## 5. Triggering (트리거 — When to emit)

**정의**: window 의 결과를 *언제* 출력할지 결정. Akidau 의 4 질문 중 *When* (in processing time, when are results materialized?). Beam 의 trigger 시스템이 표준 모델.

**왜 trigger 가 필요한가**:
- watermark 만으로는 부족 — late event 후 update 발행할지, early peek (preview) 할지 선택권 필요
- 실시간 대시보드 (1초마다 preview) vs 정확한 일 집계 (watermark 후 1회) 모두 같은 window 위에서 표현

**3 종 trigger 타이밍 (Beam 표준)**:

| Trigger 종류 | 의미 | 사용처 |
|---|---|---|
| **Early firing** | watermark *이전* 에 미리 출력 (preview) | 실시간 대시보드 |
| **On-time firing** | watermark 통과 시 정식 출력 | 표준 case |
| **Late firing** | watermark *이후* late event 도착 시 추가 출력 | 정확성 보정 |

**Accumulation Mode (Akidau 의 *How* 질문)**:

| 모드 | 동작 |
|---|---|
| **Accumulating** | 매 firing 시 *지금까지 누적된* 결과 출력. 다운스트림이 마지막 값 사용 (idempotent update) |
| **Discarding** | 매 firing 시 *직전 firing 이후 새 데이터* 만 출력. 다운스트림이 합산 (additive merge) |
| **Accumulating & Retracting** | 이전 firing 을 *철회 (retract)* + 새 firing 발행. 다운스트림이 정확히 재계산 |

**Trigger 시나리오 다이어그램**:
```
event time:        09:00 ─────────── 09:05 ───── 09:08 (window 종료)
                                                  |
processing time:   09:00   09:02   09:05  09:10  09:15
                   |       |       |      |       |
                   e1,e2   e3      WM≈09:05 e4(late)
                                          (late event)
                                          ↓
events:            [e1,e2] [e3]   [WM]  [e4 late arrival]

Trigger 출력:
  Early (1분마다):   t=09:01: sum={e1,e2}
                    t=09:02: sum={e1,e2,e3}
  On-time:          t=09:05: sum={e1,e2,e3}        ← watermark 통과 시
  Late:             t=09:10: sum={e1,e2,e3,e4}     ← late event 도착 시
```

**장점**:
- Latency vs Completeness vs Cost trade-off 를 *코드 차원* 에서 표현
- 같은 window 정의로 batch 처럼 1회 emit, streaming 처럼 N회 emit 모두 가능
- late data 정확도 보정 (retraction mode) 가능

**단점·trade-off**:
- 다운스트림이 *멱등성 / 누적* 둘 중 하나를 정확히 구현해야 함
- Accumulating mode: 매 firing 시 전체 누적 결과 → state 보존 + bandwidth 비용
- Discarding mode: 다운스트림 합산 로직 필요, late 시 의미 불명확
- Retraction: 가장 정확하지만 가장 복잡 (downstream sink 가 retract 지원해야)

**실제 구현**:
- **Beam** — `.triggering(AfterWatermark.pastEndOfWindow().withEarlyFirings(...).withLateFirings(...))`
- **Flink** — `Trigger` 인터페이스 (CONTINUE / FIRE / PURGE / FIRE_AND_PURGE)
- **Kafka Streams** — `suppress(Suppressed.untilWindowCloses(...))` (단순화된 trigger)

**Beam 예제 (Early + On-time + Late trigger)**:
```kotlin
import org.apache.beam.sdk.transforms.windowing.*

input.apply(
    Window.into<KV<String, Long>>(FixedWindows.of(Duration.standardMinutes(5)))
        .triggering(
            AfterWatermark.pastEndOfWindow()
                // Early: 1분마다 미리 출력 (preview)
                .withEarlyFirings(
                    AfterProcessingTime.pastFirstElementInPane()
                        .plusDelayOf(Duration.standardMinutes(1))
                )
                // Late: 30분간 late event 도착할 때마다 update
                .withLateFirings(AfterPane.elementCountAtLeast(1))
        )
        .withAllowedLateness(Duration.standardMinutes(30))
        .accumulatingFiredPanes() // 매 firing 시 누적 합계 출력
)
.apply(Sum.longsPerKey())
```

**Pane info (각 firing 의 메타데이터)**:
- `PaneInfo.isFirst` / `isLast` — 첫/마지막 firing 여부
- `PaneInfo.getTiming()` — `EARLY` / `ON_TIME` / `LATE` / `UNKNOWN`
- `PaneInfo.getIndex()` — 0부터 시작하는 firing 순번

**관련 패턴**: [Watermark](#3-watermark), [Allowed Lateness](#6-allowed-lateness), [Windowing](#4-windowing-patterns)

---

<a id="6-allowed-lateness"></a>
## 6. Allowed Lateness (허용 지연)

**정의**: watermark 통과 *이후* 에 도착하는 late event 를 **얼마나 오래** 받아줄지의 기간. 이 기간이 지나면 해당 window state 는 GC 되고, late event 는 *drop* 된다. Akidau Ch.3 의 GC vs Accuracy trade-off.

**메커니즘**:
```
window [09:00, 09:05)
   ↓
watermark = 09:05 통과 (on-time fire)
   ↓
window state 유지 시작 (allowed lateness 동안)
   ↓
이 기간 동안 도착한 late event → late firing 발생
   ↓
allowed lateness 만료 (예: 09:05 + 30분 = 09:35)
   ↓
window state GC → 이후 late event 는 drop
```

**왜 lateness 한도가 필요한가**:
- 무한 state 보관 불가능 (메모리·디스크 비용)
- 24시간 전 데이터까지 받으면 window state 가 무한 증가
- 비즈니스 의미: "어제 데이터까지만 보정, 그 이후는 무시" 같은 정책

**Lateness vs Watermark vs Out-of-Orderness 의 관계**:
```
event time T 에서:
  ├─ out-of-orderness (5초): watermark 가 보수적이 되도록 조정 (heuristic 의 안전 마진)
  ├─ watermark (heuristic): 이 시각 이전 이벤트는 *대부분* 도착 완료라고 추정
  ├─ on-time fire: watermark 통과 시 1차 결과 출력
  └─ allowed lateness (30분): watermark 이후에도 30분간 late event 받아 보정 firing
       └─ 만료 → window state GC, 이후 late event drop
```

**장점**:
- 무한 state 방지 (메모리 안정성)
- late event 보정과 GC 정책의 trade-off 를 명시적으로 제어
- SLA 와 비즈니스 정책 매핑 (예: "30분 늦은 데이터까지만 매출에 반영")

**단점·trade-off**:
- 너무 짧음 → 정확성 손실 (모바일 오프라인 데이터 drop)
- 너무 김 → state 비용 증가, 다운스트림이 오래된 retraction 처리 필요
- 적절한 값 산정 어려움 (실측 기반 P99 lateness 측정 필요)

**산정 방법론**:
1. 운영 단계에서 *실제 lateness* 측정 (`event_time - processing_time` 분포)
2. P99 또는 P99.9 lateness 를 allowed lateness 로 설정
3. 비즈니스 정책 (billing cutoff 등) 과 비교하여 더 짧은 쪽 채택
4. 주기적 재측정 (트래픽 패턴 변화 시)

**실제 구현**:
- **Beam** — `Window.withAllowedLateness(Duration)` + `accumulatingFiredPanes()` / `discardingFiredPanes()`
- **Flink** — `.allowedLateness(Time.minutes(30))` + side output for super-late
- **Spark Structured Streaming** — `withWatermark("eventTime", "30 minutes")` (lateness 포함)
- **Kafka Streams** — `TimeWindows.grace(Duration.ofMinutes(30))` (grace period)

**Flink 예제 (lateness + side output for super-late)**:
```kotlin
import org.apache.flink.util.OutputTag

val lateOutputTag = OutputTag<Event>("super-late-events")

val result = input
    .keyBy { it.userId }
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .allowedLateness(Time.minutes(30)) // 30분간 late event 받아서 다시 fire
    .sideOutputLateData(lateOutputTag) // 30분 초과 super-late 는 별도 stream 으로
    .reduce { a, b -> Event(a.userId, a.count + b.count) }

// super-late 처리: 별도 sink 로 저장하거나 alert
val superLate: DataStream<Event> = result.getSideOutput(lateOutputTag)
superLate.addSink(deadLetterQueueSink)
```

**Lateness 정책 결정 매트릭스**:

| 케이스 | allowed lateness | 사유 |
|---|---|---|
| Real-time alert | 0 (없음) | 빠른 응답 우선, 정확성 양보 |
| 시간별 매출 | 30분 ~ 1시간 | 결제 지연 흡수 |
| 일별 billing | 24시간 | 모바일 오프라인 데이터 포함 |
| Click stream A/B | 7일 | 모든 사용자 행동 캡처 |

**관련 패턴**: [Watermark](#3-watermark), [Triggering](#5-triggering), [Event Time](#2-event-time-processing-time)

---

<a id="7-stateful-stream"></a>
## 7. State Management (스테이트풀 스트림 — Keyed state, RocksDB)

**정의**: 스트림 operator 가 *과거 이벤트* 의 정보를 보관하면서 새 이벤트 처리에 활용하는 상태. 집계·조인·세션·deduplication·머신러닝 feature store 등 거의 모든 비-trivial 스트림 처리는 stateful. Akidau Ch.7 의 핵심 주제.

**State 의 종류 (Flink 분류)**:

| 종류 | 정의 | 사용처 |
|---|---|---|
| **Keyed State** | 키별로 격리된 state. `keyBy()` 이후만 접근 가능 | 사용자별 누적, 키별 집계 |
| **Operator State** | 키 무관, operator instance 별 state | Kafka source 의 offset, broadcast state |
| **Broadcast State** | 모든 task 에 복제되는 state | rule engine, dynamic config |

**Keyed State 의 primitive (Flink)**:
- `ValueState<T>` — 단일 값 (마지막 본 timestamp 등)
- `ListState<T>` — append-only list (이벤트 버퍼링)
- `MapState<K, V>` — key-value (사용자별 feature 맵)
- `ReducingState<T>` — auto-reduce (running sum)
- `AggregatingState<IN, OUT>` — 커스텀 aggregation

**State Backend 비교 (Flink)**:

| Backend | 저장 위치 | 특징 |
|---|---|---|
| **HashMapStateBackend** | JVM heap | 빠름, 크기 제한 (heap) |
| **EmbeddedRocksDBStateBackend** | local disk (RocksDB) | TB 단위 state 가능, 약간 느림 |

대규모 stateful job 은 거의 항상 **RocksDB backend**. Akidau 책에서 강조하는 *terabyte-scale state* 의 핵심.

**State 의 도전 (Akidau Ch.7)**:
1. **Scale** — TB 단위 state (사용자 1억명 × feature 100개)
2. **Fault tolerance** — checkpoint 로 복구
3. **TTL** — 오래된 state GC (state.cleanupInBackground)
4. **Re-keying** — 스케일 변경 시 state 재분배 (key group sharding)

**장점**:
- 무한 스트림 위에서 *기억* 을 갖는 처리 가능 (세션, 조인, ML feature)
- RocksDB 로 heap 한계 초월
- exactly-once 와 결합 시 정확한 상태 복구

**단점·trade-off**:
- State 가 잘못 설계되면 자원 폭발 (key cardinality 폭발)
- TTL 설정 안 하면 영원히 누적
- State migration (스키마 변경) 시 savepoint 호환성 이슈
- Hot key 문제 (한 키에 트래픽 집중)

**실제 구현**:
- **Flink** — KeyedProcessFunction 의 `getRuntimeContext().getState(...)`
- **Kafka Streams** — `KStream.aggregate(...)` 내부적으로 RocksDB state store
- **Beam** — `StateSpec<ValueState<T>>` + `@StateId` annotation
- **Spark Structured Streaming** — `mapGroupsWithState` / `flatMapGroupsWithState`

**Flink 예제 (사용자별 세션 길이 추적)**:
```kotlin
import org.apache.flink.api.common.state.ValueStateDescriptor
import org.apache.flink.streaming.api.functions.KeyedProcessFunction
import org.apache.flink.api.common.state.StateTtlConfig
import org.apache.flink.api.common.time.Time

class SessionDurationFn : KeyedProcessFunction<String, ClickEvent, SessionResult>() {
    private lateinit var lastSeenState: ValueState<Long>
    private lateinit var sessionStartState: ValueState<Long>

    override fun open(parameters: Configuration) {
        val ttl = StateTtlConfig.newBuilder(Time.hours(24))
            .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
            .cleanupInBackground() // 백그라운드 GC
            .build()

        val descriptor = ValueStateDescriptor("lastSeen", Types.LONG).apply {
            enableTimeToLive(ttl)
        }
        lastSeenState = runtimeContext.getState(descriptor)
        sessionStartState = runtimeContext.getState(
            ValueStateDescriptor("sessionStart", Types.LONG)
        )
    }

    override fun processElement(
        event: ClickEvent,
        ctx: Context,
        out: Collector<SessionResult>
    ) {
        val now = event.timestamp
        val last = lastSeenState.value() ?: now
        val gap = now - last

        if (gap > Duration.ofMinutes(30).toMillis()) {
            // 새 세션 시작
            sessionStartState.update(now)
        }
        lastSeenState.update(now)

        out.collect(SessionResult(
            userId = event.userId,
            duration = now - (sessionStartState.value() ?: now)
        ))
    }
}
```

**State TTL 의 중요성**: TTL 설정 없는 keyed state 는 시간이 지날수록 무한 증가. 거의 모든 production state 는 TTL 필수.

**관련 패턴**: [Checkpoint / Savepoint](#8-checkpoint-savepoint), [Windowing](#4-windowing-patterns), [Exactly-Once](#1-delivery-semantics)

---

<a id="8-checkpoint-savepoint"></a>
## 8. Checkpoint / Savepoint (체크포인트 / 세이브포인트 — Chandy-Lamport)

**정의**: 분산 스트림 처리에서 *전체 시스템의 일관된 snapshot* 을 만들어 fault tolerance 와 정확한 복구를 보장하는 메커니즘. **Chandy-Lamport algorithm (1985)** 의 스트림 처리 적용. Flink 가 대표적 구현체. Akidau Ch.5 의 *exactly-once* 의 기반.

**Chandy-Lamport algorithm 의 핵심**:
- 분산 시스템에서 전역 일관 snapshot 을 *blocking 없이* 만드는 방법
- **Marker (barrier)** 를 채널에 흘려보내 snapshot 경계 설정
- 모든 프로세스가 marker 를 받은 시점의 local state 저장 → 전역 snapshot

**Flink 의 Asynchronous Barrier Snapshotting (ABS)**:
```
JobManager 가 source 에 checkpoint barrier 주입
       ↓
Source ─ barrier ─► Op1 ─ barrier ─► Op2 ─ barrier ─► Sink
                     ↓                ↓                ↓
                  state n1         state n2         state n3
                  (async upload)   (async upload)   (async upload)
                     ↓                ↓                ↓
                  외부 저장소 (S3, HDFS, GCS)
                     ↓
                  JobManager: 모든 task ack → checkpoint n 완료
```

**barrier alignment vs unaligned**:

| 방식 | 동작 | trade-off |
|---|---|---|
| **Aligned** (기본) | 여러 input 의 barrier 가 모두 도착할 때까지 기다림 | exactly-once, 약간의 latency |
| **Unaligned** | barrier 즉시 통과, in-flight 데이터를 state 에 포함 | back-pressure 시에도 빠른 checkpoint, state 크기 증가 |

**Checkpoint vs Savepoint**:

| 항목 | Checkpoint | Savepoint |
|---|---|---|
| 트리거 | 자동 (주기적) | 수동 (사용자 명령) |
| 용도 | 장애 복구 | 의도적 중단·재시작·업그레이드 |
| 보관 | 짧음 (최근 N개) | 영구 (명시적 삭제까지) |
| 포맷 | 엔진 내부 | 안정적 포맷 (버전 호환) |
| 비용 | 가벼움 (incremental) | 무거움 (full) |

**Exactly-Once 와의 연결**:
- Source: checkpoint 시점에 offset 저장
- Operator: state snapshot 저장
- Sink: TwoPhaseCommitSinkFunction — preCommit (pending) → commit (visible)
- 실패 시: 마지막 checkpoint 로 rollback. offset 도 되돌아감 → 같은 입력 재처리. pending sink 는 abort.

**장점**:
- 분산 시스템에서 일관된 fault tolerance
- 무중단 업그레이드 (savepoint → 코드 변경 → 같은 savepoint 에서 재시작)
- A/B test 가능 (같은 savepoint 에서 두 버전 동시 실행)
- exactly-once 의 기술적 기반

**단점·trade-off**:
- Aligned barrier 는 back-pressure 상황에서 checkpoint 지연
- 큰 state 의 checkpoint 비용 (network·storage)
- Incremental checkpoint 가 도움되지만 compaction 비용 존재
- Savepoint 의 schema migration 은 까다로움

**실제 구현**:
- **Flink** — Asynchronous Barrier Snapshotting, RocksDB incremental checkpoint
- **Spark Structured Streaming** — micro-batch + WAL 기반 (Chandy-Lamport 아님, 다른 모델)
- **Kafka Streams** — changelog topic 으로 state 복구 (checkpoint 가 토픽 그 자체)
- **Beam** — runner 별 (Dataflow: 자체 구현, Flink runner: ABS 사용)

**Flink 예제 (checkpoint 설정)**:
```kotlin
val env = StreamExecutionEnvironment.getExecutionEnvironment()

env.enableCheckpointing(60_000) // 60초 간격
env.checkpointConfig.apply {
    setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE)
    setMinPauseBetweenCheckpoints(30_000) // 최소 간격
    setCheckpointTimeout(300_000) // 5분 timeout
    setMaxConcurrentCheckpoints(1)
    setExternalizedCheckpointCleanup(
        ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION
    )
    enableUnalignedCheckpoints(true) // back-pressure 대응
}

// RocksDB state backend + S3 저장
env.stateBackend = EmbeddedRocksDBStateBackend(true) // incremental=true
env.checkpointStorage = FileSystemCheckpointStorage("s3://flink-checkpoints/")

// 운영 명령어 (CLI):
// flink savepoint <jobId> s3://savepoints/    # 수동 savepoint
// flink run -s s3://savepoints/savepoint-xxx ./job.jar  # savepoint 에서 재시작
```

**Checkpoint barrier 시각화**:
```
Source 1: ──e1──e2──[barrier-n]──e3──e4──[barrier-n+1]──►
                       │
                       ▼  barrier alignment (aligned mode)
Op:                  [barrier-n] 도착 시 snapshot 시작
                       │
                       ▼
Source 2: ──f1──[barrier-n]──f2──f3──[barrier-n+1]──►
                  │
                  ▼  먼저 도착해도 Op 는 Source 1 의 barrier-n 도착까지 buffer
```

**관련 패턴**: [Exactly-Once](#1-delivery-semantics), [Stateful Stream](#7-stateful-stream), [`../algorithms/concurrent.md` / Chandy-Lamport](../algorithms/concurrent.md)

---

<a id="9-backpressure-stream"></a>
## 9. Backpressure in Stream (스트림 백프레셔 — Kafka lag, Flink credit-based)

**정의**: 스트림 처리 파이프라인에서 *downstream 의 처리 능력 < upstream 의 생산 속도* 일 때 발생하는 압력. 해소되지 않으면 메모리 폭발 → OOM. Reactive Streams 의 backpressure 와 같은 개념이지만 *분산·persistent* 환경에서의 구현은 다름. Akidau Ch.5 의 latency 분석에서 다룸.

**스트림 시스템에서 backpressure 가 발생하는 지점**:
1. **Source → 첫 operator**: source 가 너무 빨리 emit
2. **Operator → Operator**: 다음 operator 가 느림 (예: 외부 API 호출)
3. **Sink**: 외부 시스템 (DB, S3) 이 느림
4. **Cross-node network**: 직렬화·네트워크 한계

**Kafka Consumer Lag (가장 흔한 측정 지표)**:
```
consumer lag = log_end_offset - consumer_committed_offset

partition 0:
  ├─ producer ───► [m1][m2][m3][m4][m5][m6][m7][m8]
  │                                       ▲           ▲
  │                                       │           │
  │                              committed (3)    LEO (8)
  │                                       │
  │                              consumer 위치    lag = 5
  └─ consumer ─────────────────►
```

**lag 가 증가하면**:
- 처리 latency 증가 (오래된 이벤트 처리 중)
- watermark progress 정지 (event time 안 흐름)
- 다운스트림 timeout, SLA 위반

**Flink Credit-based Flow Control**:
- 각 receiver 가 *credit* (수용 가능 buffer 개수) 을 sender 에게 광고
- Sender 는 credit 범위 내에서만 전송
- Receiver 가 처리하면 credit 회복 → sender 에게 추가 신호
- Reactive Streams 의 `request(n)` 과 본질적으로 같은 메커니즘, 분산 환경 적용

```
Sender                              Receiver
  │                                    │
  │  ◄── credit(5) ────────────────────│  "5개 받을 수 있어"
  │                                    │
  │  ──── data[1..5] ─────────────────►│
  │                                    │  처리 중...
  │                                    │  buffer 비움
  │  ◄── credit(3) ────────────────────│  "3개 더 받을 수 있어"
  │  ──── data[6..8] ─────────────────►│
```

**Buffered vs Non-Buffered backpressure 대응**:

| 전략 | 동작 | 사용처 |
|---|---|---|
| **Buffer expand** | 메모리 buffer 늘림 | 일시적 burst 흡수 |
| **Slow down source** | source 의 polling rate 감소 | Kafka consumer pause |
| **Persist to disk** | spill-to-disk (Kafka 자체가 이 역할) | log-based source 라면 자연스러움 |
| **Drop / Sample** | 일부 이벤트 drop | 메트릭·로그 (정확성 양보) |
| **Scale out** | 다운스트림 task 추가 | 영구 부하 증가 시 |

**Kafka 의 자연스러운 backpressure**:
- Kafka topic 자체가 *persistent buffer* — 메시지가 디스크에 보관됨
- Consumer 가 느려도 producer 는 영향 안 받음 (lag 증가만 됨)
- → "Kafka 가 곧 backpressure 흡수 layer" 라는 architectural 선택
- 단점: retention 초과하면 데이터 손실, latency 누적

**장점**:
- OOM 방지, 시스템 안정성
- credit-based 는 fine-grained control
- Kafka 기반 시스템은 무료로 buffer 제공

**단점·trade-off**:
- backpressure 가 누적되면 watermark 정지 → event time 처리 멈춤
- Slow source 한 개가 전체 pipeline 영향
- Diagnostic 어려움 (어디서 발생했는지 추적)

**모니터링 지표**:
- **Kafka**: consumer lag (per partition), records-lag-max
- **Flink**: `flink_taskmanager_job_task_buffers_outputQueueLength`, backpressure detection UI
- **Kafka Streams**: `process-rate`, `commit-rate` 의 변화

**실제 구현**:
- **Kafka Consumer** — `max.poll.records`, `fetch.max.bytes` 로 가져오는 양 조절
- **Flink** — credit-based flow control (1.5+ 기본), backpressure detection (web UI)
- **Kafka Streams** — `max.poll.records` + 내부 buffer
- **Spark Structured Streaming** — `maxOffsetsPerTrigger` (micro-batch rate limit)

**Kafka 예제 (consumer rate 조절)**:
```kotlin
val props = Properties().apply {
    put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092")
    put(ConsumerConfig.GROUP_ID_CONFIG, "slow-processor")
    // 한 번에 최대 100개만 (backpressure 자기 제어)
    put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 100)
    put(ConsumerConfig.FETCH_MAX_BYTES_CONFIG, 1024 * 1024) // 1MB
    // poll 간격 초과하면 rebalance → 너무 느린 처리 감지
    put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, 300_000)
}

val consumer = KafkaConsumer<String, Event>(props)
consumer.subscribe(listOf("events"))

while (true) {
    val records = consumer.poll(Duration.ofMillis(100))
    for (record in records) {
        slowExternalCall(record.value()) // 느린 처리
    }
    consumer.commitSync() // at-least-once
}
```

**Cross-link 와 Reactive Streams**:
- Reactive Streams 의 `Subscription.request(n)` = Flink credit-based 의 credit
- 둘 다 *pull-based / demand-driven* 방식
- 차이: Reactive Streams 는 *in-process*, Flink 는 *cross-node* + persistent buffer

**Backpressure 대응 결정 트리**:
```
backpressure 발생
   │
   ├─ 일시적 burst? ─── YES ──► Kafka buffer 흡수 (no action)
   │
   ├─ 영구 부하 증가? ─ YES ──► 다운스트림 task 증설 (scale out)
   │
   ├─ slow external API? YES ─► async I/O + retry budget + circuit breaker
   │
   └─ data skew (hot key)? YES ─► key 재분배 (salt key, 2-stage agg)
```

**관련 패턴**: [reactive-streams.md / Backpressure Strategy](reactive-streams.md), [reliability.md / Bulkhead](reliability.md), [Watermark](#3-watermark), [Stateful Stream](#7-stateful-stream)

---
