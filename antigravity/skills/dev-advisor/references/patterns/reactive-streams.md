# Reactive Streams & FRP (Reactive Streams & Functional Reactive Programming)

Reactive Streams JVM spec / RxJava 3 / Reactor / Akka Streams / Kotlin Flow / RxJS / Bacon.js 의 정평 있는 8 패턴. 비동기 데이터 스트림을 **합성 가능한 연산자** 로 다루는 영역. *Backpressure 가 first-class*.

**원전 참고**:
- Reactive Streams JVM Spec — https://www.reactive-streams.org/
- JDK 9+ `java.util.concurrent.Flow` (Reactive Streams 인터페이스 표준화)
- Erik Meijer — "Reactive 4 R's" (Responsive / Resilient / Elastic / Message-Driven, *Reactive Manifesto*)
- ReactiveX — Marble Diagram convention (http://reactivex.io)
- Conal Elliott & Paul Hudak — *Functional Reactive Animation* (ICFP 1997) — FRP 원전
- Roman Elizarov — Kotlin Flow design notes

**핵심 비기능 요구**:
- **Backpressure first** — 구독자 능력에 맞춰 발행 제어 (request(n))
- **합성 (Composition)** — operator chain 으로 큰 스트림 구축
- **시간 (Time)** — 비동기·이벤트·지연이 first-class

**관련 카탈로그**:
- [concurrency.md](concurrency.md) — Reactor / Proactor / Future-Promise / Structured Concurrency
- [reliability.md](reliability.md) — Backpressure 본체 (구현 관점)
- [functional.md](functional.md) — Monad / Functor (operator 의 수학 배경)
- [integration.md](integration.md) — Pub-Sub / Aggregator / Splitter

---

<a id="1-reactive-streams-spec"></a>
## 1. Reactive Streams Spec (리액티브 스트림즈 사양)

**정의**: 비동기 스트림 처리의 표준 인터페이스. 4 개의 핵심 타입(`Publisher` / `Subscriber` / `Subscription` / `Processor`)과 30 여 개의 TCK 규칙으로 구성. JDK 9+ 에서 `java.util.concurrent.Flow` 로 표준화.

**메커니즘**:
- `Publisher.subscribe(Subscriber)` — 구독 시작. Publisher 가 `Subscriber.onSubscribe(Subscription)` 콜백 호출
- `Subscription.request(n)` — 구독자가 발행자에게 *최대 n 개* 요청 (pull-based backpressure)
- `Subscriber.onNext(item)` — 발행자가 요청량 한도 내에서 데이터 push
- `Subscriber.onError(t)` / `Subscriber.onComplete()` — terminal 신호 (한 번만 호출)
- `Subscription.cancel()` — 구독자가 언제든 취소

**Marble diagram**:
```
Publisher:   ---a---b---c---d---|-->
                                ^
                                onComplete
Subscriber:  request(2)         request(2)
             receives a,b       receives c,d
```

**장점**:
- 라이브러리 간 상호운용성 (RxJava ↔ Reactor ↔ Akka Streams ↔ JDK Flow)
- backpressure 가 인터페이스에 내장
- terminal 신호 규약이 명확 (error 후 onNext 금지 등 TCK 강제)

**단점**:
- 인터페이스 단독으론 빈약 — operator (`map`, `filter`) 는 라이브러리 책임
- 초보자에게 onSubscribe → request → onNext 흐름이 직관적이지 않음
- 규약 위반 시 silent failure (TCK 검증 필수)

**활용 예시**:
- Spring WebFlux (Reactor 기반 `Mono` / `Flux` — Publisher 구현)
- MongoDB / R2DBC reactive driver
- JDK 9+ `Flow.Publisher` 표준 (라이브러리가 변환 어댑터 제공)

**Reactor 예제**:
```kotlin
import reactor.core.publisher.Flux
import org.reactivestreams.Subscriber
import org.reactivestreams.Subscription

val publisher: Flux<Int> = Flux.range(1, 100)

publisher.subscribe(object : Subscriber<Int> {
    private lateinit var sub: Subscription
    override fun onSubscribe(s: Subscription) {
        sub = s
        sub.request(10) // 첫 batch 요청
    }
    override fun onNext(item: Int) {
        println("got $item")
        if (item % 10 == 0) sub.request(10) // 다음 batch
    }
    override fun onError(t: Throwable) = t.printStackTrace()
    override fun onComplete() = println("done")
})
```

**TCK 핵심 규칙 (Reactive Streams Specification §1~§3)**:
- `Publisher` 는 `Subscriber.onSubscribe` 를 **정확히 한 번** 호출 (§1.9)
- `onNext` 발행 수는 **누적 request(n) 합계 이하** (§1.1)
- `onError` / `onComplete` 후 추가 신호 금지 (§1.7)
- `Subscription.request(n)` 은 *non-blocking* 이어야 함 (§3.4)
- `Subscription.cancel()` 후 자원은 *eventually* 해제 (§3.5)
- `Publisher` 가 throw 하면 안 됨 — 모든 오류는 `onError` 로 신호 (§1.2)

**JDK Flow 와 Reactive Streams 의 관계**:
- JDK 9 부터 `java.util.concurrent.Flow.{Publisher, Subscriber, Subscription, Processor}` 표준 도입
- *동일한 4 인터페이스* 를 `org.reactivestreams` 와 `java.util.concurrent.Flow` 두 패키지에 중복 정의 (역사적 사정)
- `FlowAdapters.toPublisher(flowPublisher)` 로 변환 가능 — 라이브러리 마이그레이션 시 사용

**관련 패턴**: [Backpressure 전략](#5-backpressure-strategy), [Operator Composition](#6-operator-composition), [reliability.md / Backpressure](reliability.md), [Cold/Hot Stream](#2-cold-hot-stream)

---

<a id="2-cold-hot-stream"></a>
## 2. Cold vs Hot Stream (콜드 / 핫 스트림)

**정의**: 구독 시점에 emission 이 시작되고 구독자마다 독립적인 stream 이 **cold**, 구독과 무관하게 emission 이 진행되고 모든 구독자가 공유하는 stream 이 **hot**.

**메커니즘**:
- **Cold** — `Flux.create` / `Flux.range` / `flow { }` (Kotlin) — 구독마다 producer 블록 재실행. HTTP 호출, DB 쿼리처럼 idempotent 한 데이터 소스 모델링
- **Hot** — `Sinks.Many.multicast()` / `MutableSharedFlow` — producer 가 외부 이벤트 (마우스 이동, WebSocket 메시지) 를 multicast. 구독 전 emission 은 손실
- `share()` / `publish().refCount()` / `shareIn()` — cold → hot 변환 연산자

**Marble diagram**:
```
Cold (구독 2회 → 각자 1부터 emission):
  Sub1: ---1---2---3---|-->
  Sub2:        ---1---2---3---|-->  (3초 뒤 구독, 자기 1부터)

Hot (구독 2회 → 공유 stream, 늦은 구독자는 손실):
  Source: ---a---b---c---d---e---f-->
  Sub1:   ---a---b---c---d---e---f-->
  Sub2:           ^-----c---d---e---f-->  (c 부터 봄, a·b 손실)
```

**장점**:
- Cold — 재시도 / replay 가 자연스러움, 사이드이펙트 격리
- Hot — 외부 이벤트 소스 (UI, WebSocket, sensor) 모델링에 자연스러움
- 변환 연산자로 둘 사이를 유연하게 전환

**단점**:
- Cold 를 무심코 여러 번 구독하면 *중복 부작용* (HTTP 호출 N 번)
- Hot 은 늦은 구독자에 데이터 손실 — replay 필요 시 [Subject](#3-subject-types) 필수
- "왜 두 번 호출되지?" 디버깅이 어려움 (cold 의 구독 모델)

**활용 예시**:
- Cold — REST API 호출 (`webClient.get()`), DB query (`R2dbcRepository.findById`)
- Hot — UI 이벤트 (`MutableStateFlow` 클릭), Kafka consumer broadcast, real-time chart tick
- 변환 — REST 응답을 여러 위젯이 공유 (`shareIn(scope, WhileSubscribed())`)

**Kotlin Flow 예제**:
```kotlin
import kotlinx.coroutines.flow.*

// Cold: 구독마다 1·2·3 새로 발행 (println "fetching" 2회)
val cold: Flow<Int> = flow {
    println("fetching")
    emit(1); emit(2); emit(3)
}
suspend fun useCold() {
    cold.collect { println("A: $it") }
    cold.collect { println("B: $it") } // "fetching" 다시 출력
}

// Hot: 단일 producer, 모든 구독자 공유
val hot: SharedFlow<Int> = MutableSharedFlow<Int>(replay = 0)
suspend fun useHot(scope: kotlinx.coroutines.CoroutineScope) {
    val coldShared = cold.shareIn(scope, SharingStarted.Eagerly, replay = 1)
    // 첫 구독자는 1·2·3 전부, 늦은 구독자는 마지막 replay 1개만
}
```

**관련 패턴**: [Subject](#3-subject-types), [Operator Composition](#6-operator-composition), [observability.md / Event Stream](observability.md)

---

<a id="3-subject-types"></a>
## 3. Subject (BehaviorSubject / ReplaySubject / PublishSubject)

**정의**: `Publisher` 이면서 동시에 `Subscriber` 인 *bridge* 타입. 외부 명령형 코드에서 `onNext(x)` 를 호출하면 모든 구독자에게 multicast. 종류별로 구독 시점 동작이 다름.

**메커니즘**:
- **PublishSubject** — 구독 이후의 emission 만 전달. 이전 데이터는 손실
- **BehaviorSubject** — 마지막 값 1개를 cache, 신규 구독자에 즉시 전달 (초기값 필수 또는 nullable)
- **ReplaySubject** — N 개 또는 모든 emission 을 buffer, 신규 구독자에 모두 replay
- **AsyncSubject** — `onComplete` 시점의 마지막 값만 전달 (RxJava 한정)
- Kotlin 대응: `MutableSharedFlow(replay=N)` ≈ ReplaySubject, `MutableStateFlow` ≈ BehaviorSubject

**Marble diagram**:
```
Publish:     ---a---b---c---d-->
Sub1 join ^                   (a,b,c,d)
Sub2          join ^          (c,d만)

Behavior(seed=0): 0--a---b---c-->
Sub1 join ^             (0,a,b,c)
Sub2         join ^     (a,b,c)   ← 즉시 마지막값 a 받음

Replay(buf=2):  ---a---b---c-->
Sub1 join ^             (a,b,c)
Sub2         join ^     (b,c,...)  ← b,c replay 후 신규 emission
```

**장점**:
- 명령형 → reactive 경계의 *유일한 정답* (외부 콜백 → stream 변환)
- BehaviorSubject 는 "현재 상태 + 변경 stream" 모델링에 완벽 (Android ViewModel, Redux store)
- ReplaySubject 로 늦은 구독자에 history 제공

**단점**:
- ReplaySubject 의 unbounded buffer 는 OOM 위험 (`createWithSize(n)` 권장)
- 남용 시 reactive 흐름이 명령형으로 회귀 (`subject.onNext()` 가 곳곳에 흩어짐)
- 동시성 — `onNext` 가 멀티스레드에서 호출되면 serialization 필요 (`.toSerialized()` / SharedFlow 자동)

**활용 예시**:
- Android `MutableStateFlow<UiState>` — ViewModel 의 표준 패턴
- Redux/Flux 의 store ≈ BehaviorSubject
- 채팅 메시지 history — ReplaySubject (최근 50개)
- 클릭 이벤트 forwarding — PublishSubject

**RxJava 예제**:
```kotlin
import io.reactivex.rxjava3.subjects.*

val publish = PublishSubject.create<String>()
publish.onNext("a") // 구독자 없음 → 손실
publish.subscribe { println("A: $it") }
publish.onNext("b") // A: b

val behavior = BehaviorSubject.createDefault("init")
behavior.onNext("x")
behavior.subscribe { println("B: $it") } // B: x (마지막값 즉시)
behavior.onNext("y") // B: y

val replay = ReplaySubject.createWithSize<Int>(2)
replay.onNext(1); replay.onNext(2); replay.onNext(3)
replay.subscribe { println("R: $it") } // R: 2, R: 3 (마지막 2개 replay)
```

**관련 패턴**: [Cold/Hot Stream](#2-cold-hot-stream), [state-management.md / Redux](state-management.md), [behavioral.md / Observer](behavioral.md)

---

<a id="4-marble-diagram"></a>
## 4. Marble Diagram (마블 다이어그램)

**정의**: 시간을 가로축으로, emission 을 marble (도형) 로 시각화한 *industry-standard* reactive 다이어그램. ReactiveX 가 표준화. 연산자 동작 학습·문서화·테스트 명세에 사용.

**메커니즘**:
- 가로 화살표 — 시간 축 (좌 → 우)
- 원/사각형 marble — emission 값
- `|` — `onComplete` (terminal success)
- `X` — `onError` (terminal failure)
- 점선 박스 — 연산자 (operator). 입력 stream(상단) → 출력 stream(하단)
- 점선 — 연산자 내부 mapping 화살표

**Marble diagram 예시**:
```
Source:      ---1---2---3---4---5---|-->
                            map(x*10)
Output:      ---10--20--30--40--50--|-->

Source:      ---1---2---X-->          (3번째 자리에 에러)
                            map(...)
Output:      ---10--20--X-->          (error 전파)

Source A:    ---a---------b---c--|-->
Source B:    -----1---2---3-----|-->
                            merge
Output:      ---a-1---2---b-3-c-|-->
```

**장점**:
- 100+ 개 연산자(`map`, `flatMap`, `zip`, `combineLatest`...) 의 동작을 *한 그림* 으로 전달
- 시간성 (지연, 동시성) 을 시각화 — 텍스트로 설명하기 어려운 영역
- 테스트 DSL 의 입력 (RxJS `TestScheduler` 의 marble syntax: `"--a--b--|"`)
- 라이브러리 간 일관 — Rx, Reactor, RxJS, Akka Streams 모두 동일 표기

**단점**:
- 표준은 *비공식적* — `|` 위치, multi-line layout 이 라이브러리마다 미세하게 다름
- 복잡한 연산자 (`window`, `groupBy`) 는 nested marble 이 필요해 가독성 저하
- 텍스트(ascii) 표기는 폰트 폭에 의존 — 정렬이 깨지기 쉬움

**활용 예시**:
- RxJS / RxJava 공식 문서의 연산자 페이지 (https://rxmarbles.com 인터랙티브 시각화)
- RxJS `TestScheduler` 의 marble syntax — `cold("--a--b--|", { a: 1, b: 2 })`
- 코드 리뷰 시 reactive flow 설명용 ascii 다이어그램
- 신규 연산자 명세 / 합성 디자인 문서

**Marble test 예제 (RxJS Jasmine)**:
```typescript
import { TestScheduler } from 'rxjs/testing';
import { map } from 'rxjs/operators';

const scheduler = new TestScheduler((actual, expected) => {
    expect(actual).toEqual(expected);
});

scheduler.run(({ cold, expectObservable }) => {
    const source$ = cold('--1--2--3--|', { 1: 1, 2: 2, 3: 3 });
    const result$ = source$.pipe(map(x => x * 10));
    expectObservable(result$).toBe('--a--b--c--|', { a: 10, b: 20, c: 30 });
});
```

**복합 연산자 marble 예시**:
```
debounceTime(20ms):
  Input:   -a-b-c----d----e-f-|-->
  Output:  -------c----d-------f-|-->
  (마지막 emission 후 20ms 정적이면 통과)

throttleTime(30ms):
  Input:   -a-b-c-d-e-f-g-h-|-->
  Output:  -a-----d-----g---|-->
  (첫 emission 후 30ms 동안 추가 emission 무시)

window(2):
  Input:   -a-b-c-d-e-|-->
  Output:  -[a,b]-[c,d]-[e]-|-->
  (n 개씩 group)
```

**marble syntax 표기 규칙**:
- `-` — 가상 시간 1 프레임 (보통 10ms)
- `|` — onComplete (terminal success)
- `#` 또는 `X` — onError (terminal failure)
- `^` — subscription point
- `()` — 동일 프레임 내 다중 emission (`(ab)` 는 a, b 가 같은 시점)
- value 매핑은 dictionary 로 (`{ a: 1, b: 2 }`)

**관련 패턴**: [Operator Composition](#6-operator-composition), [testing.md / Behavior Test](testing.md), [Cold/Hot Stream](#2-cold-hot-stream)

---

<a id="5-backpressure-strategy"></a>
## 5. Backpressure 전략 (Buffer / Drop / Latest / Error / Sample)

**정의**: 구독자가 발행 속도를 따라가지 못할 때 *발행자가 취할 행동* 의 5 가지 표준 정책. [reliability.md / Backpressure](reliability.md) 가 *시스템 전반의 흐름제어* 라면, 본 항목은 **reactive operator 레벨의 즉시 정책**.

**메커니즘**:
- **Buffer** — 모든 emission 을 bounded/unbounded queue 에 보관. 가장 단순, OOM 위험
- **Drop (DROP_LATEST)** — 버퍼 가득 시 *새로 도착한* item 폐기
- **Drop_Oldest / Latest** — 가장 오래된 item 폐기. 최신 N 개 유지
- **Error** — 오버플로우 발생 즉시 `MissingBackpressureException` 으로 stream 종료
- **Sample / Throttle** — 시간 윈도우당 1 개만 발행 (rate-based, 다른 정책과 차원이 다름)

**Marble diagram**:
```
Fast source: -1-2-3-4-5-6-7-8-9-|-->
Slow consumer (1 item/sec)

buffer(capacity=3):
  drop fail at 4: -1-2-3-X (Error)
  drop latest:    -1-2-3-(4,5,6,7,8,9 drop)-|->
  drop oldest:    -7-8-9-|-> (앞 6개 폐기)
  conflate:       -1---9-|-> (consumer 가 가져갈 때만 latest)
  sample(1s):     -1---5---9-|-> (1초마다 latest 1개)
```

**장점**:
- 상황별 정책 선택 — UI 이벤트 (Latest), 결제 (Error), 로그 (Buffer)
- 종단간 메모리 안정성 보장 (bounded 정책)
- 연산자 chain 의 가시적 위치에 명시 (`.onBackpressureBuffer(1000, DROP_LATEST)`)

**단점**:
- 정책 선택 실수가 silent data loss / OOM 으로 직결
- Error 정책은 retry / circuit breaker 와 조합 필수
- 분산 환경 — operator 레벨 정책은 *프로세스 내부* 만 보호 (외부 흐름은 reliability.md / Backpressure 참고)

**활용 예시**:
- UI tick stream — `conflate()` / `sample()` (마지막 값만 의미)
- 결제 이벤트 — `Error` (절대 손실 불가, 별도 retry 로 처리)
- 로그 / 메트릭 — `buffer(capacity=10000, DROP_OLDEST)` (최신성 우선)
- 마우스 좌표 — `MutableStateFlow` (자동 conflate, 항상 최신 1개)

**Reactor 예제**:
```kotlin
import reactor.core.publisher.Flux
import java.time.Duration

val fast = Flux.interval(Duration.ofMillis(10)).take(1000)

// 1) Buffer: bounded + drop latest 정책
fast.onBackpressureBuffer(100) { dropped -> log.warn("dropped $dropped") }
    .publishOn(reactor.core.scheduler.Schedulers.parallel(), 1)
    .subscribe { Thread.sleep(50); println("got $it") }

// 2) Latest: 항상 최신 1개만
fast.onBackpressureLatest()
    .publishOn(reactor.core.scheduler.Schedulers.boundedElastic(), 1)
    .subscribe { Thread.sleep(50); println("latest $it") }

// 3) Sample: 100ms 윈도우 마지막 값
fast.sample(Duration.ofMillis(100))
    .subscribe { println("sampled $it") }
```

**Kotlin Flow 예제**:
```kotlin
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.channels.BufferOverflow

val source = flow { repeat(1_000) { emit(it); kotlinx.coroutines.delay(1) } }

// buffer: 64 capacity, drop oldest
source.buffer(64, onBufferOverflow = BufferOverflow.DROP_OLDEST)
      .collect { kotlinx.coroutines.delay(50); println(it) }

// conflate: latest 1개만 유지
source.conflate().collect { kotlinx.coroutines.delay(50); println(it) }
```

**관련 패턴**: [reliability.md / Backpressure](reliability.md), [reliability.md / Rate Limiter](reliability.md), [Stream Fusion](#8-stream-fusion)

---

<a id="6-operator-composition"></a>
## 6. Operator Composition (map / flatMap / concatMap / switchMap / merge)

**정의**: stream 을 다른 stream 으로 변환·결합하는 *함수형 합성* 연산. 4 개 핵심 연산자(`map` / `flatMap` / `concatMap` / `switchMap`) 의 차이를 이해하면 90% 의 reactive 코드가 쓰여진다.

**메커니즘**:
- **map** — `T → R`. 1:1 동기 변환. 차원 변화 없음
- **flatMap** — `T → Publisher<R>`. inner stream 을 *동시 (concurrent)* 으로 평탄화. 순서 보장 안 됨
- **concatMap** — `T → Publisher<R>`. inner stream 을 *순차적* 으로 평탄화. 앞 stream 종료 대기
- **switchMap** — `T → Publisher<R>`. 새 emission 시 *이전 inner stream cancel*. 검색 자동완성의 정답
- **merge** — 여러 stream 을 동시에 합침 (순서 X)
- **concat** — 여러 stream 을 순차로 합침 (앞 stream 완료 대기)
- **zip / combineLatest** — 2개+ stream 의 각 emission 을 짝지음 (zip: 같은 index 쌍 / combineLatest: 둘 중 하나만 변해도 최신 조합)

**Marble diagram**:
```
Source:        ---a---b---c-->
               flatMap(x → [x1, x2])
flatMap:       ---a1-a2-b1-b2-c1-c2-->  (interleave 가능)

Source:        ---a---b---c-->
               concatMap(x → [x1, x2])
concatMap:     ---a1-a2-b1-b2-c1-c2-->  (순차 보장)

Source:        ---a---b---c-->
               switchMap(x → ---x1---x2---x3-->)
switchMap:     ---a1-(cancel)-b1-(cancel)-c1-c2-c3-->
                                              ^ 마지막만 완주

Source A:      ---1-------2-------3-->
Source B:      -----a-------b-->
               zip
zip:           ---(1,a)---(2,b)-->
               combineLatest
combineLatest: ----(1,a)-(2,a)-(2,b)-->
```

**장점**:
- 거의 모든 reactive 코드가 4 개 연산자 합성으로 표현 가능
- 명령형 callback hell 을 평탄한 chain 으로 변환
- 합성이 referentially transparent — 부분 추출 / 테스트 용이

**단점**:
- `flatMap` 의 inner 동시성 한도 (`flatMap(maxConcurrency = 4)`) 누락이 흔한 OOM 원인
- `switchMap` 은 cancel 시 부작용 (HTTP, file write) 이 *중도 실행됨* — 멱등성 필수
- `combineLatest` 는 모든 source 가 첫 emission 해야 시작 — 한 source 가 비어있으면 영영 안 흐름

**활용 예시**:
- 검색 자동완성 — `searchInput.debounce(300ms).switchMap { api.search(it) }`
- 병렬 API 호출 — `userIds.flatMap(8) { api.fetchUser(it) }` (동시성 8)
- 순차 결제 단계 — `concatMap { validate(it) }` → `concatMap { authorize(it) }`
- WebSocket reconnect — `connect().switchMap { messages(it) }`

**Kotlin Flow 예제**:
```kotlin
import kotlinx.coroutines.flow.*

val userIds: Flow<Long> = flowOf(1L, 2L, 3L)

// map: 1:1 동기
userIds.map { it.toString() } // Flow<String>

// flatMapMerge: 동시 변환 (concurrency=4)
userIds.flatMapMerge(concurrency = 4) { id -> api.fetchUserFlow(id) }

// flatMapConcat: 순차 변환
userIds.flatMapConcat { id -> api.fetchUserFlow(id) }

// flatMapLatest: switchMap 대응 — 검색 자동완성
val query: Flow<String> = searchInput()
query.debounce(300).flatMapLatest { q -> api.search(q) }
     .collect { showResults(it) }

// zip / combine
val a: Flow<Int> = flowOf(1, 2, 3)
val b: Flow<String> = flowOf("a", "b", "c")
a.zip(b) { x, y -> "$x$y" }    // 1a, 2b, 3c
a.combine(b) { x, y -> "$x$y" } // 최신 조합
```

**관련 패턴**: [Cold/Hot Stream](#2-cold-hot-stream), [Marble Diagram](#4-marble-diagram), [functional.md / Monad](functional.md)

---

<a id="7-frp"></a>
## 7. Functional Reactive Programming (FRP — Behaviors + Events)

**정의**: Conal Elliott 와 Paul Hudak (1997) 의 원전 — *시간 의존 값* 을 두 1급 시민으로 모델링한 함수형 패러다임. **Behavior** (연속 시간 함수 `Time → α`) 와 **Event** (이산 발생 `[(Time, α)]`) 의 합성으로 인터랙티브 시스템을 선언적으로 표현.

**메커니즘**:
- **Behavior** `α` — 모든 시점에 값이 있는 *연속* 신호. 마우스 좌표, 시간 진행, animation easing
- **Event** `α` — 이산 시점에 발생하는 *불연속* 신호. 클릭, 키 입력, message
- **lift** — pure function 을 behavior 위로 끌어올림. `lift2 (+) behX behY : Behavior Number`
- **switcher** — event 발생 시 behavior 를 다른 behavior 로 교체. 모드 전환 표현
- **integral** / **derivative** — 시간에 대한 적분·미분 (물리 시뮬레이션)
- Modern 구현 — Sodium (Haskell/Java), reflex-frp (Haskell), Elm signal (초기 버전), Rx 의 sub-set 으로 흡수

**Marble diagram**:
```
Behavior (연속):
  mouseX: ───────/‾‾‾‾\____/‾─────  (t → x position)
              (모든 t 에 값 존재)

Event (이산):
  click:  --x---------x------x---->
          (특정 t 에만 occurrence)

lift2 (+):
  bX:     ────/‾‾\____/‾──
  bY:     ────\__/‾‾\___/──
  bX+bY:  연속 합성 결과
```

**장점**:
- *값* 으로서 시간을 다룸 — 콜백 / 상태 머신의 비명시성 제거
- 합성 가능 — `lift` 로 pure 함수 재활용
- 선언적 — "X 가 변할 때마다 Y 계산" 을 직접 표현 (애니메이션, 게임 로직)
- 시간 의존 버그 (정렬, race condition) 가 *언어 수준* 에서 사라짐

**단점**:
- **공간 누수 (space leak)** — naive 구현에선 모든 history 보존. push-pull 구현 (Elliott 2009) 으로 해결되었지만 라이브러리마다 차이
- 학습 곡선 — Rx 의 stream 모델보다 추상도가 높음
- 주류 라이브러리 (RxJava, Reactor) 는 Event 만 모델링 — Behavior 는 BehaviorSubject 로 *근사*
- Kotlin / Java 에 정통 FRP 구현은 드뭄 (Sodium 정도)

**활용 예시**:
- 게임 / 애니메이션 — Elm initial version, reflex-frp 의 GUI
- 시뮬레이션 — 물리 엔진의 속도 ↔ 위치 (integral 합성)
- 함수형 GUI — Haskell `reflex-dom`, Scala `scala.rx`
- Modern 영향 — SolidJS / Svelte 의 *signal* 모델은 FRP behavior 의 후예

**Sodium (Java) 예제**:
```java
import nz.sodium.*;

// Behavior — 연속 시간 합성
Cell<Integer> width = new Cell<>(100);
Cell<Integer> height = new Cell<>(50);
Cell<Integer> area = width.lift(height, (w, h) -> w * h);
area.listen(a -> System.out.println("area = " + a));

// Event — 이산 발생
StreamSink<String> clicks = new StreamSink<>();
clicks.listen(c -> System.out.println("click: " + c));
clicks.send("button1");

// Event → Cell (현재값 보존)
Cell<String> lastClick = clicks.hold("none");
```

**Kotlin 의사코드 (signal-style)**:
```kotlin
// SolidJS-like signal — FRP behavior 의 모던 변형
val mouseX = signal(0)
val mouseY = signal(0)
val distance = derived { Math.hypot(mouseX().toDouble(), mouseY().toDouble()) }
effect { println("distance = ${distance()}") }
mouseX.set(100) // distance 자동 재계산
```

**FRP vs Rx 비교**:
| 측면 | Classic FRP (Elliott) | Rx / Reactive Streams |
|---|---|---|
| 시간 모델 | Behavior (연속) + Event (이산) 분리 | Stream 단일 (모두 이산) |
| 합성 | `lift`, `switcher`, `integral` | `map`, `flatMap`, `merge` |
| 의미론 | denotational (수학적 정의 우선) | operational (구현 우선) |
| 공간 누수 | 핵심 난제 (push-pull 로 해결) | backpressure 로 해결 |
| 대표 구현 | Sodium, reflex-frp | RxJava, Reactor, Kotlin Flow |
| 학습 곡선 | 높음 (Haskell 배경) | 중간 |
| 주류 채택 | 낮음 (niche) | 매우 높음 |

**현대적 부활 — Signal**:
- Solid.js / Svelte 5 / Vue 3 Composition API / Angular Signal — 모두 FRP behavior 의 후예
- *fine-grained reactivity* — 의존성 그래프를 컴파일 시간 추적, 변경된 부분만 재계산
- React 의 `useState` 는 component re-render 기반이라 *coarse-grained* — FRP 와 거리가 멈

**관련 패턴**: [Cold/Hot Stream](#2-cold-hot-stream), [Subject](#3-subject-types), [state-management.md / Signal](state-management.md), [functional.md / Pure Function](functional.md)

---

<a id="8-stream-fusion"></a>
## 8. Stream Fusion / Operator Fusion (스트림 융합)

**정의**: 연산자 chain (`source.map(f).filter(p).map(g)`) 을 컴파일·런타임에 *단일 loop 로 통합* 하여 중간 collection / boxing / virtual call 을 제거하는 최적화. Haskell `vector` 라이브러리(Coutts et al. 2007) 의 *short-cut fusion* 이 원전. Reactor / RxJava 3 / Kotlin Sequence 가 채택.

**메커니즘**:
- **Naive 평가** — 각 연산자가 중간 `List`/`Publisher` 생성. N stage 면 N 개 임시 collection
- **Fusion** — 컴파일/런타임에 연산자 정보를 inspect, 동일 루프로 inline. `map → map` 은 `map(g . f)` 로 결합
- **Macro-fusion (Reactor)** — `Flux.range(1,n).map(...).filter(...)` 가 single Fuseable Subscriber 로 압축
- **Micro-fusion** — `queueSubscription` 인터페이스로 inner queue 공유, scheduling overhead 제거
- **Kotlin Sequence** — `asSequence().map(...).filter(...).toList()` 가 단일 iteration

**Marble diagram**:
```
Naive:   source ── [map List] ── [filter List] ── [map List] ── sink
                  중간 3개 List 할당

Fused:   source ── 단일 loop (map∘filter∘map) ── sink
                  중간 List 0개
```

**장점**:
- 메모리 할당 / GC 압력 대폭 감소 (특히 hot path)
- CPU cache 친화 — 단일 loop 가 vectorization / SIMD 친화
- 사용자는 *연산자 합성* 의 가독성을 유지하면서 단일 loop 수준 성능

**단점**:
- 모든 연산자가 fusable 하진 않음 — `flatMap`, `groupBy`, scheduler 경계는 fusion barrier
- 디버깅 시 stack trace 가 inline 으로 합쳐져 식별 어려움
- 성능 측정 — fusion 적용 여부는 micro-benchmark / flight recorder 로 확인
- Java collection stream (`Stream<T>`) 은 lazy 하지만 fusion 은 제한적 — JIT 인라이닝에 의존

**활용 예시**:
- Reactor `Flux.range(0, 1_000_000).map { it * 2 }.filter { it > 10 }` — 내부적으로 fused
- Kotlin `Sequence` — 100만개 데이터 처리 시 `List` 사용 대비 10배+ 빠름
- Haskell `vector` 라이브러리 — `V.map f . V.filter p . V.map g` 가 단일 loop
- ScalaBlitz / Akka Streams operator fusion

**Kotlin Sequence vs List 비교**:
```kotlin
// 1) List: 각 연산마다 중간 List 3개 생성
val resultList = (1..1_000_000).toList()
    .map { it * 2 }       // List 1
    .filter { it > 100 }  // List 2
    .map { it.toString() } // List 3

// 2) Sequence: 단일 iteration, 중간 List 0개
val resultSeq = (1..1_000_000).asSequence()
    .map { it * 2 }
    .filter { it > 100 }
    .map { it.toString() }
    .toList()             // terminal 시점에만 한 번 collect
```

**Reactor fusion 예제**:
```kotlin
import reactor.core.publisher.Flux

// Fuseable 한 source + Fuseable operator → 내부 단일 loop
val fused = Flux.range(1, 1_000_000)
    .map { it * 2 }
    .filter { it % 3 == 0 }
    .map { it.toString() }
    .subscribe()

// flatMap 은 fusion barrier — inner Publisher 별도
val barrier = Flux.range(1, 100)
    .flatMap { Flux.just(it, it * 2) } // fusion 깨짐
    .subscribe()
```

**Fusion 가능 / 불가능 연산자 (Reactor 기준)**:
- **Fusable** — `map`, `filter`, `take`, `skip`, `distinct` (single subscriber 한정), `concatMap` (특정 조건)
- **Fusion barrier** — `flatMap`, `groupBy`, `publishOn` / `subscribeOn` (scheduler 경계), `share`, `replay`, `cache`
- 일반 규칙 — *inner Publisher 를 생성* 하거나 *thread 경계를 넘는* 연산자는 barrier

**성능 측정 가이드**:
- JMH (Java Microbenchmark Harness) 로 fused vs non-fused 비교
- async-profiler 의 wall-clock + allocation profile 로 중간 객체 할당 확인
- Reactor `Hooks.onOperatorDebug()` — fusion 적용 여부 로그 확인 (개발 시에만)
- Kotlin Flow 는 fusion 보다 *coroutine 의 suspension overhead* 가 hot path 의 주요 비용 — `flowOn` 의 scheduler 경계 비용 측정 필수

**관련 패턴**: [Operator Composition](#6-operator-composition), [Backpressure 전략](#5-backpressure-strategy), [functional.md / Lazy Evaluation](functional.md)

---
