# 안티패턴 (Anti-Patterns)

"해야 할 패턴" 의 대칭. Brown, Malveau, McCormick, Mowbray *AntiPatterns: Refactoring Software, Architectures, and Projects in Crisis* (1998) 의 표준 분류 + 후속 산업 사례. 변경/유지보수 비용을 폭증시키는 구조적 결함과 그 **리팩토링 처방** 을 함께 제시.

**핵심 원칙**: 안티패턴은 **증상 + 원인 + 처방** 3 요소 묶음. "이건 안티패턴이야" 만으로는 부족. *어떻게 빠져나오는가* 가 카탈로그의 가치.

**원전 / 출처**:
- William J. Brown, Raphael C. Malveau, Hays W. McCormick III, Thomas J. Mowbray, *AntiPatterns: Refactoring Software, Architectures, and Projects in Crisis* (Wiley, 1998) — 40 안티패턴 원전
- Brian Foote, Joseph Yoder, *Big Ball of Mud* (PLoP, 1997) — 구조 부재 안티패턴
- Martin Fowler, *Patterns of Enterprise Application Architecture* (2002), *Refactoring* 2nd ed. (2018) — Anemic Domain Model, 후속 처방
- Donald Knuth, "Structured Programming with go to Statements" (1974) — Premature Optimization
- Sam Newman, *Building Microservices* 2nd ed. (2021) — Distributed Monolith
- Robert C. Martin, *Clean Code* (2008), Chapter 17 — Magic Numbers, Hard Coding 휴리스틱

**관련 카탈로그**:
- [code-smells.md](../principles/code-smells.md) — Fowler 22 코드 스멜 (메서드/클래스 단위)
- [solid.md](../principles/solid.md) — SRP/OCP/LSP/ISP/DIP (안티패턴의 근본 원인 대다수가 SOLID 위반)
- [grasp.md](../principles/grasp.md) — High Cohesion / Low Coupling (Big Ball of Mud / Spaghetti Code 대칭)
- 본 파일 — **시스템/아키텍처 단위** 안티패턴 18 종

---

<a id="1-big-ball-of-mud"></a>
## 1. Big Ball of Mud

**식별 신호**:
- 모듈/패키지 경계가 사실상 없음 — 어디서든 어디로든 호출 가능
- 한 클래스를 열면 10 개 이상 패키지의 import 가 섞임
- 의존성 그래프에 순환(cycle) 다수 존재
- "이 기능 어디 있어요?" 에 답할 수 있는 사람이 한 명도 없음
- 새 기능 추가 시 영향 범위 추정 불가 → 회귀 버그 빈발

**원인**: 단기 납기·인력 교대·요구사항 불명확이 누적된 결과. **아키텍처 의도 부재** + 리팩토링 시간 미확보. Foote & Yoder (1997) 은 "현실 세계에서 가장 흔한 아키텍처" 라 지적.

**영향**: 변경 비용이 코드 크기에 **비선형** 으로 증가. 신규 인력 온보딩 수개월. 한 부분 수정이 무관해 보이는 다른 부분을 깨뜨림. 결국 "전면 재작성(rewrite)" 의 유혹에 빠지지만 [Stovepipe System](#18-stovepipe-system) 으로 옮겨갈 뿐.

**처방 / 리팩토링**:
- **Boundary 식별 우선** — 도메인 이벤트 / 변경 사유로 모듈 경계 그어보기 (Event Storming, DDD Context Mapping)
- **Strangler Fig Pattern** (Fowler) — 새 경계를 옆에 키워가며 기존 mud 를 점진적으로 흡수
- **Architecture Decision Record (ADR)** 도입 — 의도 명시 + 후속 결정의 근거 보존
- **의존성 방향 강제** — ArchUnit / Konsist / 정적 분석으로 "ui → domain → data" 같은 단방향 검증
- **Extract Module / Move Class** 반복 — 응집도 높은 묶음부터 별도 모듈로 추출

**난이도**: 높음 (조직 합의 필요) | **사용 빈도**: ★★★★★ (현실 코드베이스의 다수)

**예제** (Kotlin pseudo-code):
```kotlin
// Bad: 한 파일에서 UI / DB / HTTP / 비즈니스 로직이 뒤섞임
class OrderController {
    fun handle(req: HttpRequest) {
        val conn = DriverManager.getConnection("jdbc:...")  // DB 직접
        val user = conn.queryUser(req.userId)
        val html = "<div>${user.name}</div>"                 // UI 직접
        val client = HttpClient.newHttpClient()              // 외부 호출 직접
        client.send(/* 결제 게이트웨이 */)
        conn.update("INSERT INTO orders ...")                // 다시 DB
        respond(html)
    }
}

// Good: 경계 분리 (Hexagonal / Clean Architecture)
class OrderController(private val placeOrder: PlaceOrderUseCase) {
    fun handle(req: HttpRequest): HttpResponse {
        val cmd = OrderCommand.from(req)
        val result = placeOrder.execute(cmd)
        return HttpResponse.json(result)
    }
}
// PlaceOrderUseCase 는 도메인만 알고, Repository / PaymentGateway 는 인터페이스로 추상화
```

**관련 패턴/스멜**:
- [architectural.md — Hexagonal / Clean Architecture](architectural.md) (정상 대응 구조)
- [grasp.md — Low Coupling / High Cohesion](../principles/grasp.md)
- [9. Spaghetti Code](#9-spaghetti-code) (Big Ball of Mud 의 메서드 단위 표현)

---

<a id="2-god-object"></a>
## 2. God Object / God Class

**식별 신호**:
- 한 클래스가 **시스템 책임의 50% 이상** 을 소유 (예: `Manager`, `System`, `Engine`, `Controller`)
- 필드 30 개 이상, 메서드 50 개 이상, 줄 수 1,000 이상
- 다른 클래스들이 "데이터 보관소" 로만 사용됨 → 진짜 로직은 God Object 안에
- 단위 테스트가 사실상 불가능 (Mock 해야 할 의존성이 수십 개)
- 신규 기능은 무조건 이 클래스에 메서드 추가

**원인**: 절차적 사고 + 클래스를 "관련 함수 묶음" 으로 오인. "어디 둘지 모르겠으니 일단 여기" 가 누적. SRP 정면 위반.

**영향**: 변경 충돌 빈발 (여러 개발자가 같은 파일 수정). 회귀 버그 ↑ (한 메서드 수정이 무관해 보이는 메서드를 깨뜨림). 인지 부하 ↑ (한 화면에 안 들어옴). 코드 리뷰 사실상 포기.

**처방 / 리팩토링**:
- **Extract Class** (Fowler) — 응집된 책임 묶음을 별도 클래스로
- **Move Method / Move Field** — God 의 멤버를 적절한 협력자에게 이동
- **Replace Conditional with Polymorphism** — type field 기반 분기 → 다형성으로 분해
- **Information Expert (GRASP)** 적용 — 데이터를 가진 객체에게 책임 부여
- **CRC 카드 워크샵** — 역할/책임을 다시 그어 보고 God 의 책임을 재분배

**난이도**: 중간 (점진적 가능) | **사용 빈도**: ★★★★★

**예제** (Kotlin):
```kotlin
// Bad: GameEngine 이 입력·렌더링·물리·AI·네트워크·저장 전부 보유
class GameEngine {
    var players: MutableList<Player> = mutableListOf()
    var enemies: MutableList<Enemy> = mutableListOf()
    var renderer: Renderer? = null
    var physics: PhysicsWorld? = null
    fun handleInput(e: InputEvent) { /* 100 줄 */ }
    fun render() { /* 200 줄 */ }
    fun updatePhysics(dt: Float) { /* 150 줄 */ }
    fun updateAI() { /* 180 줄 */ }
    fun sendNetworkPacket() { /* 80 줄 */ }
    fun saveGame(path: String) { /* 90 줄 */ }
    // ... 60 개 더
}

// Good: 책임별 클래스로 분리 + GameEngine 은 조정자(Coordinator) 만 담당
class GameEngine(
    private val input: InputSystem,
    private val renderer: RenderSystem,
    private val physics: PhysicsSystem,
    private val ai: AISystem,
    private val net: NetworkSystem,
    private val save: SaveSystem,
) {
    fun tick(dt: Float) {
        input.poll(); physics.step(dt); ai.update(); renderer.draw()
    }
}
```

**관련 패턴/스멜**:
- [code-smells.md — Large Class](../principles/code-smells.md#2-large-class) (메서드/클래스 단위 동일 증상)
- [solid.md — SRP](../principles/solid.md) (정면 위반)
- [grasp.md — High Cohesion](../principles/grasp.md)

---

<a id="3-anemic-domain-model"></a>
## 3. Anemic Domain Model

**식별 신호**:
- 도메인 클래스가 getter/setter 만 있고 **행동(behavior)** 이 없음
- 모든 비즈니스 로직이 `XxxService` 에 procedure 처럼 모임
- 도메인 객체는 사실상 자료 구조(Struct) → JPA Entity 가 DTO 와 구분 안 됨
- 같은 비즈니스 규칙이 여러 Service 에 중복 산재 (예: "할인 계산" 이 OrderService / CartService / CheckoutService 에 각각)
- Service 가 도메인 객체의 내부 필드를 모두 꺼내 외부에서 조작 ([code-smells.md — Feature Envy](../principles/code-smells.md#19-feature-envy))

**원인**: ORM(Hibernate/JPA) 의 "Entity = 테이블 매핑" 사고 + Transaction Script 스타일 답습. Martin Fowler 가 2003 년 명명: "*객체 지향의 근본 원칙(데이터 + 행동) 을 위반하면서도 객체 지향처럼 보이게 한 가짜 OOP*".

**영향**: DDD 의 풍부한 도메인 모델 효익 상실 — 비즈니스 규칙의 단일 진실 소스(SSOT) 가 없음. 규칙 변경 시 N 곳을 동시에 고쳐야 함. 도메인 전문가와 코드가 격리됨.

**처방 / 리팩토링**:
- **Move Method (Service → Entity)** — Service 의 규칙을 도메인 객체에게 이동
- **Encapsulate Field** — public setter 제거, 의도 있는 메서드(`order.applyDiscount(coupon)`) 로 대체
- **Replace Anemic with Aggregate Root** — DDD Aggregate 도입, 불변식(invariant) 을 객체 안에서 보장
- **Value Object 도입** — primitive(Long, String) 을 Money, Email, OrderId 같은 의미 있는 타입으로
- **Tell, Don't Ask** 원칙 적용 — 묻지 말고 시켜라

**난이도**: 중간 | **사용 빈도**: ★★★★★ (Spring + JPA 프로젝트에서 매우 흔함)

**예제** (Kotlin):
```kotlin
// Bad: Order 는 데이터만, 로직은 Service 에
class Order {
    var status: String = "PENDING"
    var items: MutableList<Item> = mutableListOf()
    var total: Double = 0.0
    // getter/setter 만 가득
}
class OrderService {
    fun cancel(order: Order) {
        if (order.status != "PENDING") throw IllegalStateException()
        order.status = "CANCELLED"               // 외부에서 상태 변경
        order.total = 0.0
    }
    fun addItem(order: Order, item: Item) {
        order.items.add(item)
        order.total = order.items.sumOf { it.price }   // 불변식 외부 계산
    }
}

// Good: Order 자체가 규칙을 보장
class Order private constructor(
    val id: OrderId,
    private val items: MutableList<Item> = mutableListOf(),
    private var status: OrderStatus = OrderStatus.Pending,
) {
    val total: Money get() = items.fold(Money.ZERO) { acc, i -> acc + i.price }

    fun addItem(item: Item) {
        require(status == OrderStatus.Pending) { "확정된 주문은 변경 불가" }
        items.add(item)
    }
    fun cancel() {
        check(status == OrderStatus.Pending) { "PENDING 상태만 취소 가능" }
        status = OrderStatus.Cancelled
    }
}
```

**관련 패턴/스멜**:
- [ddd-tactical.md — Aggregate / Entity / Value Object](ddd-tactical.md)
- [code-smells.md — Data Class / Feature Envy](../principles/code-smells.md)
- [grasp.md — Information Expert](../principles/grasp.md)

---

<a id="4-distributed-monolith"></a>
## 4. Distributed Monolith

**식별 신호**:
- 마이크로서비스로 분리했지만 **모든 요청이 동기 HTTP/gRPC 체인** 으로 연결됨 (A → B → C → D, 한 곳 죽으면 다 죽음)
- 여러 서비스가 **같은 DB 스키마** 를 공유 → 한 테이블 변경이 N 개 서비스를 깨뜨림
- 배포가 항상 함께 일어나야 함 (서비스 X 배포 전 서비스 Y 가 먼저 나가야 함 등)
- 같은 도메인 모델 객체(`UserDto`) 가 서비스 간 공유 라이브러리로 배포됨
- 로컬 개발 환경에서 전체 서비스를 다 띄워야 한 기능 테스트 가능

**원인**: "마이크로서비스 하자" 가 목적이 되어 **경계 설계 없이** 모놀리스를 물리적으로만 쪼갬. 트랜잭션·데이터·배포 결합은 그대로 유지. Sam Newman (2021) 은 "*the worst of both worlds*" 라 지칭.

**영향**: 모놀리스의 결합도는 그대로면서 네트워크 지연·부분 실패·운영 복잡도(쿠버네티스/관측성) 만 추가됨. 장애 격리 실패 — cascading failure 빈발. ROI 음수.

**처방 / 리팩토링**:
- **Bounded Context 재정의** — DDD Context Mapping 으로 진짜 경계 식별 후 잘못 쪼갠 서비스 **재통합(merge back)**
- **Database per Service** — 공유 DB 해체, 각 서비스가 자기 데이터 소유
- **비동기 통신 도입** — 동기 체인을 Event Bus (Kafka / RabbitMQ) + Choreography 로
- **API 버전 관리 + Consumer-Driven Contract Testing** (Pact) — 독립 배포 가능성 확보
- **Saga Pattern** — 분산 트랜잭션을 Two-Phase Commit 대신 보상 트랜잭션으로

**난이도**: 매우 높음 (조직·인프라 변경 동반) | **사용 빈도**: ★★★★☆ (마이크로서비스 유행 이후 매우 흔함)

**예제** (의사 코드):
```
Bad: 동기 체인 + 공유 DB
  Client → OrderService(sync HTTP)→ PaymentService(sync HTTP)→ InventoryService
                                          ↓                              ↓
                                    [shared MySQL: orders, payments, stock]
  PaymentService 가 1 초 늦으면 OrderService 의 모든 응답이 1 초 늦어짐
  inventory 테이블 컬럼 추가 시 3 서비스 동시 배포 필요

Good: 이벤트 기반 + DB 분리
  Client → OrderService ── publish OrderPlaced ──→ Kafka
                                                     ├─→ PaymentService (own DB)
                                                     └─→ InventoryService (own DB)
  각 서비스가 자기 DB 보유, 비동기 처리, 부분 장애 시 재처리 큐로 복구
```

**관련 패턴/스멜**:
- [distributed.md — Saga / Event-Driven / CQRS](distributed.md)
- [integration.md — Event Bus / Outbox Pattern](integration.md)
- [17. Sequential Coupling](#17-sequential-coupling) (서비스 간 호출 순서 의존)

---

<a id="5-lava-flow"></a>
## 5. Lava Flow

**식별 신호**:
- "이거 뭐 하는 코드인지 모르겠는데 일단 두자" 가 곳곳에 화석처럼 굳어 있음
- 주석에 `// TODO 나중에 정리`, `// 김씨가 추가한 거 같은데 확인 필요`, `// 2018-XX-XX 임시` 가 다수
- 사용되지 않는 듯한 분기·플래그·feature toggle 이 production 에 살아있음
- 누구도 지우자고 자신 있게 말하지 못함 — "혹시 어디서 쓸까봐"
- 로그에 절대 찍히지 않는 분기, 호출되지 않는 메서드 다수

**원인**: 빠른 프로토타이핑 → production 으로 끌어올림. 인력 교체 시 지식 유실. 테스트 커버리지 부족으로 "안 쓰는 코드" 를 증명할 수 없음. 결과적으로 화산암(lava) 처럼 굳어 제거 불가.

**영향**: 코드베이스 부피 ↑ → 빌드/검색/리뷰 비용 ↑. 새 개발자가 lava 를 "현행 패턴" 으로 오인해 모방 ([7. Cargo Cult](#7-cargo-cult-programming) 유발). 보안 패치 누락 위험.

**처방 / 리팩토링**:
- **코드 커버리지 / dead code 정적 분석** (Detekt `UnusedPrivateMember`, IntelliJ Inspections) 도입
- **Feature Flag 만료 정책** — 모든 flag 에 expiry date, 만료 후 자동 제거 PR 생성
- **삭제를 두려워하지 않는 문화** — Git 이 있으니 필요하면 복구. 죽은 코드는 지운다
- **관찰(Observability) 강화** — Prometheus / Sentry 로 "정말 호출되는지" 측정 후 미호출 분기 제거
- **Boy Scout Rule** — 만질 때마다 주변의 죽은 코드 한 줄씩 정리

**난이도**: 낮음 (기술적) ~ 높음 (조직 합의) | **사용 빈도**: ★★★★★ (5 년 이상 된 프로젝트 거의 전부)

**예제** (Kotlin):
```kotlin
// Bad: 굳어버린 lava
class PaymentProcessor {
    fun process(amount: Money) {
        // TODO: 2019-03 김씨 — 레거시 호환 위해 둠, 신규에서는 안 씀
        if (System.getenv("USE_OLD_PATH") == "true") {
            legacyProcessV1(amount)
            return
        }
        // 임시로 추가한 디버그 로직 (2021-XX-XX). 빼도 될 듯한데 확신 못 함
        if (amount.value > 100_000) {
            sendSlackNotification("BIG PAYMENT")
        }
        modernProcess(amount)
    }
    private fun legacyProcessV1(amount: Money) { /* 호출되는지 불확실 */ }
}

// Good: 관찰 후 제거 + 명시적 feature toggle 관리
class PaymentProcessor(private val flags: FeatureFlags) {
    fun process(amount: Money) {
        // legacyProcessV1 은 6 개월 metric 결과 호출 0 → 제거됨
        // BIG_PAYMENT_NOTIFY 는 flag 로 관리, expiry 2026-12-31
        modernProcess(amount)
        if (flags.isOn(BIG_PAYMENT_NOTIFY) && amount.value > 100_000) {
            notifier.send("BIG PAYMENT")
        }
    }
}
```

**관련 패턴/스멜**:
- [code-smells.md — Dead Code / Speculative Generality](../principles/code-smells.md)
- [11. Boat Anchor](#11-boat-anchor) (사용 안 하는 의존성/모듈)
- [observability.md — Metrics / Tracing](observability.md)

---

<a id="6-golden-hammer"></a>
## 6. Golden Hammer

**식별 신호**:
- "내가 잘 아는 도구 X 로 다 풀자" — 망치를 든 사람에게 모든 게 못으로 보임 (Maslow)
- 단순 CRUD 인데 Kafka + Kubernetes + Microservices 풀스택 동원
- ML 이 답이 아닌 문제(Rule-based 로 99% 해결 가능) 에 ML 모델 도입
- ORM 으로 분석 쿼리(GROUP BY + Window Function) 까지 처리하려 함
- "X 가 트렌드니까" 가 주된 선택 근거

**원인**: 개발자의 학습 비용 회피 + 이력서 주도 개발(Resume-Driven Development) + 솔루션을 먼저 정하고 문제를 끼워 맞춤. 문제 분석 부재.

**영향**: 도구의 강점이 아닌 약점이 폭로됨. 운영 복잡도 폭증. 다른 더 적합한 해결책을 못 보게 됨. 팀 학습 자원이 비효율적으로 소모됨.

**처방 / 리팩토링**:
- **Problem-First Discovery** — 도구를 정하기 전에 제약 조건(데이터 크기·SLA·예산·팀 역량) 을 종이에 적기
- **Decision Records (ADR)** — 왜 X 를 골랐는지, 대안 Y/Z 를 왜 거부했는지 명문화
- **Spike / PoC** — 후보 도구별 작은 프로토타입으로 비용 측정 후 결정
- **YAGNI** — 지금 필요 없는 분산성·확장성·유연성을 미리 사지 않기
- **Catalog 학습** — [12-factor.md](../principles/12-factor.md) / [iso25010.md](../principles/iso25010.md) 같은 평가 축으로 도구 비교

**난이도**: 낮음 (사고의 전환) | **사용 빈도**: ★★★★☆

**예제**:
```
Bad: 일일 10 건의 회원 가입 알림 시스템
  → Kafka 클러스터 3-broker + Schema Registry + Kafka Connect + ksqlDB 도입
  → 운영 인력 2 명 필요, 월 클라우드 비용 $2k

Good: 일일 10 건이면
  → DB INSERT trigger 또는 cron + 단순 워커
  → 운영 무인, 비용 거의 0
  → "나중에 트래픽 1000 배 되면 Kafka 검토" 라는 명시적 마일스톤
```

**관련 패턴/스멜**:
- [7. Cargo Cult Programming](#7-cargo-cult-programming) (이유 모르고 모방)
- [12. Premature Optimization](#12-premature-optimization) (불필요한 미래 대비)
- [13. Reinventing the Wheel](#13-reinventing-the-wheel) (반대 극단)

---

<a id="7-cargo-cult-programming"></a>
## 7. Cargo Cult Programming

**식별 신호**:
- 패턴/프레임워크의 **형태만** 모방, **이유** 를 모름 (예: 모든 클래스에 `Factory` 접미사, 의미 없는 인터페이스 + 단일 구현체)
- "다른 프로젝트도 이렇게 했으니까" 가 유일한 근거
- StackOverflow 답변을 출처 확인 없이 복붙
- 단위 테스트가 있지만 assertion 이 빈약하거나 무의미 (`assertNotNull(result)`)
- Microservices 같은 아키텍처를 "용어 그대로" 적용

**원인**: 학습 깊이 부족 + 코드 리뷰 부재 + "동작하면 OK" 문화. Richard Feynman 이 이름 붙인 비유: 2 차대전 후 태평양 부족이 활주로·관제탑 모형을 만들면 비행기가 다시 올 거라 믿었던 데서 유래.

**영향**: 비용은 들고 효익은 없음. 진짜 문제(테스트 가능성·확장성) 는 그대로. 잘못된 패턴이 팀 표준으로 굳어짐 → 다음 [5. Lava Flow](#5-lava-flow) 의 씨앗.

**처방 / 리팩토링**:
- **"왜?" 5 번 묻기** — 모든 도입 결정에 5-Whys 적용
- **First Principles 학습** — 패턴 원전(Fowler / GoF / Brown) 직접 읽기, 블로그 요약 의존 줄이기
- **간소화 우선** — 단순 형태로 동작시킨 뒤 진짜 필요할 때만 패턴 도입 ("Rule of Three": 3 번 반복될 때 추상화)
- **코드 리뷰 강화** — "왜 이 패턴인가?" 가 PR 표준 질문
- **Pair / Mob programming** — 지식 공유로 모방 의존도 ↓

**난이도**: 중간 (문화 변화) | **사용 빈도**: ★★★★★ (주니어 비중 높은 팀에서 매우 흔함)

**예제** (Kotlin):
```kotlin
// Bad: 의미 없는 인터페이스 + Factory + DI — "다른 곳도 이렇게 함" 이 유일 근거
interface UserRepository { fun findById(id: Long): User? }
class UserRepositoryImpl : UserRepository {                  // 구현체 1 개뿐
    override fun findById(id: Long) = /* ... */ User(id, "x")
}
class UserRepositoryFactory {                                // Factory 도 1 개만 만듦
    fun create(): UserRepository = UserRepositoryImpl()
}
class UserService(repo: UserRepository = UserRepositoryFactory().create())

// Good: 정말 필요한 추상화만, 이유 명시
// (테스트에서 다른 구현이 필요할 때 인터페이스 도입. 그 전에는 클래스 그대로)
class UserRepository(private val db: Database) {
    fun findById(id: Long): User? = db.query("SELECT * FROM users WHERE id = ?", id)
}
class UserService(private val repo: UserRepository)
```

**관련 패턴/스멜**:
- [code-smells.md — Speculative Generality](../principles/code-smells.md) (불필요한 일반화)
- [6. Golden Hammer](#6-golden-hammer) (도구 차원의 모방)
- [solid.md — YAGNI / KISS](../principles/solid.md)

---

<a id="8-vendor-lock-in"></a>
## 8. Vendor Lock-in / Magic Pushbutton

**식별 신호**:
- 코드 전반이 특정 클라우드 / SDK / 데이터베이스의 **고유 API** 에 직접 의존 (예: AWS DynamoDB SDK 호출이 도메인 코드에 산재)
- 다른 벤더로 전환 비용 산정 시 "거의 전면 재작성" 답변
- UI 가 한 버튼 클릭으로 마법처럼 동작하지만 내부 흐름은 베이더 SDK 의 검은 상자 (Magic Pushbutton 유래)
- 가격 인상·서비스 종료(SaaS deprecation) 발표에 협상력 0
- 로컬 개발 환경 구성 불가 — 벤더 클라우드 없이는 한 줄도 못 돌림

**원인**: "벤더 X 의 편의 기능 활용" 이 단기 생산성으로는 빠름. 추상화 계층 도입 비용을 미루다 누적. 또는 영업 단계의 "통합 솔루션" 약속에 깊이 종속.

**영향**: 가격 협상력 상실, 멀티 클라우드 / 멀티 리전 전환 불가, 벤더 장애 시 비즈니스 함께 멈춤, 컴플라이언스 변경(데이터 주권) 대응 어려움.

**처방 / 리팩토링**:
- **Hexagonal Architecture / Ports & Adapters** — 도메인은 인터페이스만 알고, 벤더 SDK 는 adapter 에 격리
- **Anti-Corruption Layer (DDD)** — 외부 SDK 의 모델 vs 도메인 모델 분리
- **Open standards 우선** — SQL / S3 API / CloudEvents / OpenTelemetry 같은 표준 위주
- **벤더-중립 추상화** (단, [7. Cargo Cult](#7-cargo-cult-programming) 빠지지 않게 실제 전환 시나리오로 검증)
- **Exit Strategy 문서화** — 어떤 시점에 어떤 비용으로 빠져나올 수 있는지 시뮬레이션

**난이도**: 중간~높음 (이미 박혀 있을수록 비쌈) | **사용 빈도**: ★★★★☆

**예제** (Kotlin):
```kotlin
// Bad: 도메인 코드가 DynamoDB SDK 직접 사용
class OrderService(private val dynamo: AmazonDynamoDB) {
    fun place(order: Order) {
        val item = mapOf(
            "id" to AttributeValue(order.id.value),
            "total" to AttributeValue().withN(order.total.toString())
        )
        dynamo.putItem("orders", item)   // 도메인 ↔ AWS SDK 직결
    }
}

// Good: Port 인터페이스 + Adapter
interface OrderRepository { fun save(order: Order) }
class DynamoOrderRepository(private val dynamo: AmazonDynamoDB) : OrderRepository {
    override fun save(order: Order) { /* AWS 매핑은 여기서만 */ }
}
class OrderService(private val orders: OrderRepository) {
    fun place(order: Order) = orders.save(order)
    // 도메인은 AWS 를 모름 → 테스트 / 멀티 백엔드 가능
}
```

**관련 패턴/스멜**:
- [architectural.md — Hexagonal / Ports & Adapters](architectural.md)
- [12-factor.md — Backing Services](../principles/12-factor.md)
- [16. Hard Coding](#16-hard-coding) (벤더 endpoint 박힘)

---

<a id="9-spaghetti-code"></a>
## 9. Spaghetti Code

**식별 신호**:
- 흐름 제어가 `goto` / 이른 return / 깊은 중첩 if / 전역 변수 mutation 으로 얽힘
- 한 메서드에서 다른 모듈의 전역 상태를 수정 (전역 사이드이펙트)
- 호출 그래프에 순환 다수 (A → B → C → A)
- 디버거로 step-into 하다가 갑자기 "어디로 왔지?" 상태에 빠짐
- 메서드 이름이 동작을 설명 못 함 (`doStuff`, `handle`, `run`)

**원인**: 절차적 사고를 그대로 객체 지향 / 함수형으로 이식. 캡슐화 없이 전역 상태에 의존. Edsger Dijkstra (1968) "*Go To Statement Considered Harmful*" 의 정확한 반례.

**영향**: 정적 분석 어려움. 단위 테스트 불가 (실행 경로 폭증). 한 줄 수정이 어디로 전파될지 예측 불가. 리팩토링 시도 자체가 위험.

**처방 / 리팩토링**:
- **Extract Function** — 한 호흡 단위로 자르기 (메서드당 20 줄 이하 목표)
- **Replace Nested Conditional with Guard Clauses** — 중첩 if → early return
- **Encapsulate Field / Encapsulate Variable** — 전역 상태 → 객체 멤버
- **Replace Mutation with Immutable** — 가능한 곳은 불변 객체 + 함수형 변환
- **State Pattern** — 복잡한 상태 전이 → 명시적 상태 객체

**난이도**: 중간 | **사용 빈도**: ★★★★★

**예제** (Kotlin):
```kotlin
// Bad: 중첩 + 전역 mutation + 흐름 점프
var globalUser: User? = null
var globalCart: Cart? = null

fun handle(req: Request) {
    if (req.type == "LOGIN") {
        if (req.user != null) {
            if (req.user.isValid()) {
                globalUser = req.user
                if (globalCart == null) globalCart = Cart()
            } else { /* ... */ }
        }
    } else if (req.type == "ADD") {
        if (globalUser == null) return
        globalCart?.add(req.item)
        // ... 200 줄 더, 곳곳에서 globalUser / globalCart 변경
    }
}

// Good: 의도 단위 분리 + 명시적 상태 + early return
sealed interface Cmd { /* LoginCmd, AddItemCmd ... */ }
class Session(val user: User, val cart: Cart)

fun handle(cmd: Cmd, session: Session?): Session = when (cmd) {
    is LoginCmd -> Session(cmd.user.requireValid(), Cart())
    is AddItemCmd -> {
        requireNotNull(session) { "로그인 필요" }
        session.copy(cart = session.cart.add(cmd.item))
    }
}
```

**관련 패턴/스멜**:
- [1. Big Ball of Mud](#1-big-ball-of-mud) (모듈 수준 spaghetti)
- [code-smells.md — Long Method / Cyclomatic Complexity](../principles/code-smells.md)
- [behavioral.md — State Pattern](behavioral.md)

---

<a id="10-magic-numbers-strings"></a>
## 10. Magic Numbers / Magic Strings

**식별 신호**:
- 의미 없는 리터럴이 비즈니스 로직 한가운데 박혀 있음 (`if (status == 3)`, `if (type == "PRM_GLD")`)
- 같은 값이 코드 여러 곳에 중복 (`0.1` 부가세율, `86400` 하루 초)
- 주석으로만 의미 표시 (`val x = 7 // 일주일`)
- 값 변경 요구 시 grep + 수작업 치환 필요
- 코드 리뷰에서 "이 7 은 뭐임?" 질문 빈발

**원인**: 빠른 prototyping → 그대로 production. 상수 추출의 가치를 가볍게 봄. 또는 enum / sealed class 미사용으로 string code 가 직접 흩어짐.

**영향**: 의미 추적 불가, 변경 시 누락 ↑, 같은 값이지만 의미가 다른 경우 분리 안 됨 (예: 7 명 정원 vs 7 일 유효), 단위 혼동 버그 (km vs miles).

**처방 / 리팩토링**:
- **Replace Magic Literal with Symbolic Constant** (Fowler 카탈로그)
- **Replace Type Code with Subclasses / Enum / Sealed Class**
- **Introduce Named Parameter** (boolean / int flag → 의도 있는 이름)
- **Value Object** 도입 — 단위 + 의미를 타입에 박음 (`Duration.ofDays(7)`, `Money(amount, KRW)`)
- **Configuration 외부화** — 환경/플랜별 변하는 값은 코드 상수가 아닌 config

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**예제** (Kotlin):
```kotlin
// Bad: 의미 없는 숫자 / 문자열
fun calculate(order: Order): Double {
    if (order.status == 3) return 0.0                       // 3 == ?
    var total = order.itemsTotal
    if (order.customer.type == "PRM_GLD") total *= 0.9       // 10% 할인?
    total *= 1.1                                             // 부가세?
    if (order.daysSincePlaced > 7) total += 5000             // 연체료?
    return total
}

// Good: 의미를 타입과 상수에 박음
enum class OrderStatus { Pending, Paid, Cancelled, Refunded }
enum class CustomerTier(val discount: BigDecimal) {
    Regular(BigDecimal.ZERO),
    PremiumGold(BigDecimal("0.10")),
    PremiumPlatinum(BigDecimal("0.15")),
}
object PricingPolicy {
    val VAT_RATE = BigDecimal("0.10")
    val LATE_FEE = Money(BigDecimal(5000), KRW)
    val LATE_THRESHOLD = Duration.ofDays(7)
}

fun calculate(order: Order): Money {
    if (order.status == OrderStatus.Cancelled) return Money.ZERO
    val tier = order.customer.tier
    val base = order.itemsTotal * (BigDecimal.ONE - tier.discount)
    val withVat = base * (BigDecimal.ONE + PricingPolicy.VAT_RATE)
    return if (order.daysSincePlaced > PricingPolicy.LATE_THRESHOLD) withVat + PricingPolicy.LATE_FEE
           else withVat
}
```

**관련 패턴/스멜**:
- [code-smells.md — Primitive Obsession](../principles/code-smells.md#3-primitive-obsession)
- [16. Hard Coding](#16-hard-coding) (환경 의존 값에 한정한 변종)
- [solid.md — OCP](../principles/solid.md) (정책 변경 시 한 곳만 수정)

---

<a id="11-boat-anchor"></a>
## 11. Boat Anchor

**식별 신호**:
- 사용하지 않는데 의존성에 남은 라이브러리 (build.gradle / package.json 에 박혀 있음)
- "혹시 나중에 쓸까봐" 둔 모듈·서브프로젝트 (마지막 commit 2 년 전)
- 비활성화된 채로 production 코드에 포함된 admin 페이지 / debug endpoint
- 빌드 시간만 잡아먹는 generated code (실행되지 않음)
- 의미 없는 자원(데이터베이스 테이블·S3 버킷·Cron job) 이 운영비만 소모

**원인**: 제거의 두려움 ("혹시 다른 데서 쓰면 어쩌지"). 추적 부재. 인력 교체로 지식 유실. 영업/마케팅 요구로 도입했으나 무산된 기능의 잔재.

**영향**: 빌드/배포 시간 ↑, 의존성 보안 취약점 표면적 ↑, 신규 개발자 인지 부하 ↑ ("이거 뭐예요?" 답변 가능자 0 명), 운영비 누수.

**처방 / 리팩토링**:
- **의존성 정리 도구** — Gradle `dependencyInsight`, `unused-deps` 플러그인, `depcheck` (npm)
- **사용 추적** — 로그/메트릭으로 "정말 호출되는지" 측정 후 0 인 것 제거
- **삭제 PR 의 일상화** — 매 스프린트마다 "Dead Code Removal" 카드 1 개
- **자동화** — CI 에서 "0 호출 코드" 리포트 + 빌드 실패 옵션
- **YAGNI** — 미래의 가정으로 의존성 추가 금지

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**예제** (Gradle):
```kotlin
// Bad: 사용 안 함이 확인됐는데도 둠
dependencies {
    implementation("org.apache.commons:commons-collections4:4.4")   // 0 호출
    implementation("com.google.guava:guava:32.0.0-jre")              // 1 곳에서 1 줄만 — 표준 라이브러리로 대체 가능
    implementation("io.reactivex:rxjava:1.3.8")                      // RxJava1, RxJava3 마이그레이션 후 잔재
    implementation(project(":legacy-admin"))                          // 2 년 전부터 배포 안 됨
}

// Good: 사용처 / 대체 가능성 검토 후 제거
dependencies {
    // commons-collections4 제거 (사용 0)
    // guava → stdlib 의 Strings.padStart 등으로 대체 후 제거
    // rxjava1 제거, rxjava3 만 유지
    // legacy-admin 모듈 삭제 (Git 에 남아 있으니 필요 시 복구)
}
```

**관련 패턴/스멜**:
- [5. Lava Flow](#5-lava-flow) (코드 차원의 화석)
- [code-smells.md — Dead Code / Speculative Generality](../principles/code-smells.md)
- [iso25010.md — Maintainability](../principles/iso25010.md)

---

<a id="12-premature-optimization"></a>
## 12. Premature Optimization

**식별 신호**:
- 측정 결과 없이 "느릴 것 같다" 는 추측으로 복잡한 캐싱·인덱스·비동기화 도입
- 가독성을 희생한 비트 연산·매크로·custom allocator
- 단순 CRUD 에 분산 캐시(Redis) + L1/L2/L3 다단 캐시
- "이건 빠르게 해두는 게 좋잖아" 식 PR 코멘트 빈발
- 프로파일러를 켜 본 적이 없음

**원인**: 성능에 대한 막연한 불안 + 개발자 만족(나는 빠른 코드를 짠다) + 측정 도구 미숙. Donald Knuth (1974): "*premature optimization is the root of all evil (or at least most of it) in programming*".

**영향**: 가독성 ↓, 버그 ↑ (복잡도 추가가 곧 실수 표면), 진짜 병목은 다른 곳에 있는데 헛수고. 최적화한 부분이 실제 hot path 가 아닐 확률이 압도적.

**처방 / 리팩토링**:
- **Measure First** — 프로파일러 (async-profiler / JFR / py-spy) 결과 없이는 최적화 금지
- **80/20 룰** — hot path 20% 만 골라 최적화, 나머지는 가독성 우선
- **벤치마크 자동화** — JMH / wrk / k6 로 회귀 측정
- **Algorithmic 우선** — Big-O 개선이 micro-optimization 보다 항상 우선
- **YAGNI** — 지금 측정된 병목이 아니면 손대지 않기

**난이도**: 낮음 (사고 전환) | **사용 빈도**: ★★★★☆

**예제** (Kotlin):
```kotlin
// Bad: 매번 호출되는 함수도 아닌데 마이크로 최적화
fun greet(name: String): String {
    // StringBuilder 가 더 빠르다고 들었음 — 측정 안 함
    val sb = StringBuilder(7 + name.length)
    sb.append('H').append('e').append('l').append('l').append('o')
    sb.append(',').append(' ').append(name)
    return sb.toString()
}

// Good: 측정 후 필요하면 최적화, 아니면 가독성 우선
fun greet(name: String): String = "Hello, $name"

// 진짜 hot path 인 경우만:
//   1) 프로파일러로 입증
//   2) 벤치마크로 개선폭 측정 (JMH)
//   3) 주석으로 이유 명시 ("hot path, JMH 결과 30% 개선")
```

**관련 패턴/스멜**:
- [6. Golden Hammer](#6-golden-hammer) (도구 차원의 과잉 대비)
- [code-smells.md — Speculative Generality](../principles/code-smells.md)
- [observability.md — Profiling / Benchmarking](observability.md)

---

<a id="13-reinventing-the-wheel"></a>
## 13. Reinventing the Wheel / Not Invented Here

**식별 신호**:
- 표준 라이브러리 / 검증된 OSS 가 있는데 자체 구현 (자체 JSON 파서, 자체 Date util, 자체 ORM)
- "외부 라이브러리는 못 믿겠다" 가 도입 거부 근거
- 자체 구현 보안 코드 (자체 암호화·자체 인증·자체 토큰 발급)
- README 에 "We don't use X because Y" 가 다수
- 같은 문제를 매 프로젝트마다 다시 풂

**원인**: NIH 신드롬(Not Invented Here) — 외부 의존을 자존심 손상으로 인식. 라이선스/보안 검토 비용 회피. 또는 [6. Golden Hammer](#6-golden-hammer) 의 변종 — "내 도구로 다 풀자".

**영향**: 핵심 비즈니스가 아닌 곳에 자원 낭비. 자체 구현은 검증·보안 패치·문서화 부담을 전부 자기가 짐. 특히 **암호화 자체 구현은 거의 항상 취약점 동반**.

**처방 / 리팩토링**:
- **표준 라이브러리 / 사실상 표준(de facto)** 우선 — kotlinx.serialization, OkHttp, Spring Security 등
- **Build vs Buy 분석** — 자체 구현 비용 vs 도입+유지 비용 정량 비교
- **보안 영역 절대 금지** — 암호화·인증·토큰은 검증된 라이브러리만 사용 (BouncyCastle, Auth0, Keycloak)
- **의존성 보안 스캔** — Dependabot / Snyk 으로 외부 라이브러리도 안전하게 관리
- **반대 극단 경계** — 단순한 한 줄 유틸을 위해 거대 라이브러리 추가는 [11. Boat Anchor](#11-boat-anchor) 유발

**난이도**: 낮음 (사고 전환) ~ 중간 (보안 거버넌스) | **사용 빈도**: ★★★☆☆ (특정 조직 문화에서 강함)

**예제** (Kotlin):
```kotlin
// Bad: 자체 JWT 검증 구현
object MyJwtVerifier {
    fun verify(token: String, secret: String): Map<String, Any>? {
        val parts = token.split(".")
        if (parts.size != 3) return null
        val expected = hmacSha256("${parts[0]}.${parts[1]}", secret)
        if (expected != parts[2]) return null     // timing-attack 취약
        return parseBase64Json(parts[1])           // exp 검증 누락
    }
}

// Good: 검증된 라이브러리 (auth0/java-jwt, jjwt)
val verifier = JWT.require(Algorithm.HMAC256(secret))
    .withIssuer("my-app")
    .acceptLeeway(5)
    .build()
val decoded: DecodedJWT = verifier.verify(token)  // 서명·exp·iss 자동 검증
```

**관련 패턴/스멜**:
- [6. Golden Hammer](#6-golden-hammer) (반대 극단 — 외부 도구로 다 풀자)
- [iso25010.md — Security / Reliability](../principles/iso25010.md)
- [12-factor.md — Dependencies](../principles/12-factor.md)

---

<a id="14-yo-yo-problem"></a>
## 14. Yo-Yo Problem

**식별 신호**:
- 상속 계층이 5 단계 이상 (`Animal → Mammal → Carnivore → Feline → Cat → DomesticCat`)
- 메서드 호출 흐름 추적 시 부모 → 자식 → 부모 → 자식 으로 위아래 반복 점프
- 한 메서드가 어디서 override 되었는지 IDE 가 보여주는 후보 10 개 이상
- "이 메서드의 실제 구현이 어디 있지?" 가 일상 질문
- `super.super.method()` 같은 호출 패턴이 필요해짐

**원인**: 상속을 재사용 도구로 오용 (정확한 용도: 다형성 + LSP 만족). Template Method 패턴 남용. 또는 "공통 부분 빼자" 가 무한 누적되어 상속 계층 폭증. William Cook (1989) 명명.

**영향**: 추적 비용 ↑ (실제 동작 파악에 IDE 도움 필수), 변경 영향 예측 어려움 (한 부모 수정이 모든 자식에 전파), LSP 위반 잠재 ↑, 컴포지션 대비 결합도 ↑.

**처방 / 리팩토링**:
- **Replace Inheritance with Composition / Delegation** (Fowler)
- **Pull Up Method / Push Down Method** — 계층을 평탄화하거나 책임을 적절한 수준으로 이동
- **Strategy / Template Method 재검토** — 자식 클래스로 분기하던 부분을 인터페이스 + 전략으로
- **단일 책임 + Interface Segregation** — 상속 대신 작은 인터페이스 다중 구현
- **계층 깊이 제한** — 정적 분석 규칙 (Detekt `MaxClassHierarchy`) 으로 깊이 3 단 제한 권장

**난이도**: 중간 (리팩토링 영향 범위 큼) | **사용 빈도**: ★★★☆☆

**예제** (Kotlin):
```kotlin
// Bad: 깊은 상속 — 메서드 추적이 yo-yo
open class Entity { open fun render() { /* ... */ } }
open class LivingEntity : Entity() { override fun render() { super.render(); /* + life */ } }
open class Animal : LivingEntity() { override fun render() { super.render(); /* + animal */ } }
open class Mammal : Animal() { override fun render() { super.render(); /* + mammal */ } }
open class Feline : Mammal() { override fun render() { super.render(); /* + feline */ } }
class DomesticCat : Feline() { override fun render() { super.render(); /* + domestic */ } }

// Good: Composition + Strategy
class Entity(private val renderers: List<RenderComponent>) {
    fun render() = renderers.forEach { it.render() }
}
interface RenderComponent { fun render() }
class LifeRender : RenderComponent { override fun render() { /* ... */ } }
class FelineRender : RenderComponent { override fun render() { /* ... */ } }
// 생성: Entity(listOf(LifeRender(), FelineRender(), DomesticRender()))
```

**관련 패턴/스멜**:
- [solid.md — LSP / ISP](../principles/solid.md)
- [code-smells.md — Refused Bequest](../principles/code-smells.md)
- [structural.md — Decorator / Composite](structural.md)

---

<a id="15-copy-paste-programming"></a>
## 15. Copy-Paste Programming

**식별 신호**:
- 같은 로직 블록(검증·매핑·에러 처리) 이 N 곳에 거의 동일하게 복제
- 한 곳의 버그 수정이 다른 곳에는 반영되지 않아 동일 버그 재발
- IDE 의 "Duplicate Code" 인스펙션 다수 경고
- 정적 분석 (PMD CPD, SonarQube duplication ratio) 10% 이상
- 비슷한 클래스가 `OrderProcessorV1`, `OrderProcessorV2`, `OrderProcessorNew` 식으로 공존

**원인**: 시간 압박 + 추상화 시점 판단 미숙 + 코드 리뷰 부재. "한 번만 더 복사하면 끝나니까". 또는 두려움 ("공통 부분 추출했다가 다른 데 영향 갈까봐").

**영향**: DRY 위반 — 변경 시 N 곳을 모두 수정해야 함, 누락 시 버그. 코드 부피 ↑, 일관성 ↓, 신규 개발자가 "어느 버전이 정답?" 혼란.

**처방 / 리팩토링**:
- **Extract Function / Extract Method** — 가장 흔한 처방
- **Extract Class / Extract Module** — 같은 데이터 + 로직 묶음 단위
- **Template Method / Strategy** — 알고리즘 골격은 같고 일부만 다를 때
- **Parameterize Function** — 거의 같지만 일부 값만 다른 메서드를 파라미터화
- **Rule of Three** — 2 번까지는 복사 OK, 3 번째부터 추상화 (조기 추상화는 [7. Cargo Cult](#7-cargo-cult-programming) 유발)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**예제** (Kotlin):
```kotlin
// Bad: 거의 동일한 검증 로직 3 곳에 복제
fun createUser(req: CreateUserRequest) {
    if (req.email.isBlank() || !req.email.contains("@")) throw IllegalArgumentException("이메일")
    if (req.name.length < 2 || req.name.length > 50) throw IllegalArgumentException("이름")
    /* 저장 */
}
fun updateUser(id: Long, req: UpdateUserRequest) {
    if (req.email.isBlank() || !req.email.contains("@")) throw IllegalArgumentException("이메일")
    if (req.name.length < 2 || req.name.length > 50) throw IllegalArgumentException("이름")
    /* 갱신 */
}
fun adminCreateUser(req: AdminCreateUserRequest) {
    if (req.email.isBlank() || !req.email.contains("@")) throw IllegalArgumentException("이메일")
    if (req.name.length < 2 || req.name.length > 50) throw IllegalArgumentException("이름")
    /* 저장 */
}

// Good: Value Object 로 검증 일원화
@JvmInline value class Email(val value: String) {
    init { require(value.isNotBlank() && value.contains("@")) { "잘못된 이메일" } }
}
@JvmInline value class UserName(val value: String) {
    init { require(value.length in 2..50) { "이름 길이 2~50" } }
}
// 모든 진입점에서 Email / UserName 생성 시 자동 검증, 하류는 안심
```

**관련 패턴/스멜**:
- [code-smells.md — Duplicate Code (Fowler #1)](../principles/code-smells.md)
- [solid.md — DRY](../principles/solid.md)
- [3. Anemic Domain Model](#3-anemic-domain-model) (검증이 Service 에 흩어진 변종)

---

<a id="16-hard-coding"></a>
## 16. Hard Coding

**식별 신호**:
- 환경 의존 값(URL / API key / DB host / file path) 이 코드에 박힘 (`"https://api.prod.example.com"`)
- 환경별 분기를 if-else 로 처리 (`if (env == "prod") url = ...`)
- 비밀(secret) 이 소스 코드 / Git 히스토리에 노출
- "QA 환경 한번 배포해 볼게요" 가 코드 수정 + 재빌드를 의미
- 로컬 개발용 임시 path (`/Users/john/temp/`) 가 커밋됨

**원인**: 환경 분리 부재 + 설정 외부화의 가치를 가볍게 봄. 또는 "이건 변할 일 없잖아" 라는 단정. [10. Magic Numbers](#10-magic-numbers-strings) 의 환경-한정 변종.

**영향**: 환경 전환(dev/qa/prod) 불가 → 재빌드 필수. 비밀 노출 위험 (Git 히스토리 영구 기록). 12-Factor App 정면 위반. CI/CD 파이프라인 복잡화.

**처방 / 리팩토링**:
- **환경 변수 / Config 파일** — 12-Factor `III. Config`
- **Secret 전용 저장소** — AWS Secrets Manager / HashiCorp Vault / Kubernetes Secret
- **Profile-based config** (Spring `application-{profile}.yml`, Flutter `--dart-define` flavor)
- **타입 안전한 Config 객체** — `@ConfigurationProperties` (Spring), `kotlinx.serialization` 으로 검증
- **Git pre-commit hook** — gitleaks / git-secrets 로 비밀 커밋 차단

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**예제** (Kotlin / Spring):
```kotlin
// Bad: 환경별 값이 코드에 박힘 + 비밀 노출
@Service
class PaymentClient {
    private val baseUrl = "https://api.prod.tosspayments.com"   // prod 전용
    private val apiKey = "test_sk_..."                            // 코드에 비밀
    private val devLogPath = "/Users/zime/payments.log"           // 개인 경로
    fun charge(amount: Long) { /* baseUrl + apiKey 사용 */ }
}

// Good: 환경 변수 / Secret 분리
@ConfigurationProperties("payment")
data class PaymentConfig(
    val baseUrl: String,                  // application-{profile}.yml 에서 주입
    val apiKey: String,                   // Vault / Secret Manager 에서 주입
    val logPath: Path,                    // 환경별 path
)

@Service
class PaymentClient(private val cfg: PaymentConfig) {
    fun charge(amount: Long) { /* cfg.baseUrl + cfg.apiKey 사용 */ }
}
```

**관련 패턴/스멜**:
- [12-factor.md — Config / Backing Services](../principles/12-factor.md)
- [10. Magic Numbers / Strings](#10-magic-numbers-strings) (값 박힘의 일반화)
- [8. Vendor Lock-in](#8-vendor-lock-in) (벤더 endpoint 박힘으로 가속됨)

---

<a id="17-sequential-coupling"></a>
## 17. Sequential Coupling / Temporal Coupling

**식별 신호**:
- 메서드 호출 순서가 **암묵적 사전조건** (`init()` → `configure()` → `start()` 순서를 어기면 예외 또는 정의되지 않은 동작)
- 객체가 "단계별 상태" 를 내부 플래그로 추적 (`isInitialized`, `isConfigured`, `isStarted`)
- 문서에만 호출 순서가 적혀 있고 타입 시스템이 강제하지 않음
- 신규 개발자가 "왜 NullPointerException 이 뜨지?" → "configure() 먼저 호출해야 됨" 답을 듣는 일상
- 인터페이스 메서드들이 서로의 호출 순서에 묵시적으로 의존

**원인**: 절차적 사고를 클래스로 포장 + 상태 머신을 명시적으로 모델링하지 않음. Builder 가 필요한 곳에 단순 클래스 사용. Kent Beck 명명.

**영향**: 학습 곡선 ↑ (문서 의존 강함), 잘못된 순서 호출로 인한 런타임 버그 빈발, 리팩토링 위험 (호출 순서가 곧 계약), 테스트 setup 복잡화.

**처방 / 리팩토링**:
- **Builder Pattern** — 단계별 구성을 타입 시스템이 강제 (Step Builder / Type-State Pattern)
- **State Pattern** — 명시적 상태 객체로 전이 강제
- **Combine into Single Method** — 분리할 이유가 없으면 한 메서드로 합치기
- **Replace Method with Method Object** — 호출 순서가 복잡하면 별도 객체로 캡슐화
- **Type-State Programming** (Rust 흔함, Kotlin sealed class 로도 가능)

**난이도**: 중간 | **사용 빈도**: ★★★★☆ (특히 SDK / Library 설계 시)

**예제** (Kotlin):
```kotlin
// Bad: 호출 순서가 암묵적
class HttpClient {
    private var url: String? = null
    private var auth: String? = null
    private var started = false

    fun setUrl(url: String) { this.url = url }
    fun setAuth(auth: String) { this.auth = auth }
    fun start() {
        if (url == null) throw IllegalStateException("setUrl 먼저")
        // auth 는 옵셔널이지만, setAuth 호출 시점이 start 전이어야 함 (문서에만 적힘)
        started = true
    }
    fun send(req: Request) {
        if (!started) throw IllegalStateException("start 먼저")
    }
}

// Good: Type-State / Step Builder — 컴파일러가 순서 강제
class HttpClientBuilder {
    fun url(url: String): HttpClientWithUrl = HttpClientWithUrl(url)
}
class HttpClientWithUrl internal constructor(private val url: String) {
    fun auth(token: String): HttpClientWithUrl = this   // 선택, 체이닝
    fun build(): HttpClient = HttpClient(url)
}
class HttpClient internal constructor(private val url: String) {
    fun send(req: Request) { /* start 같은 명시 단계 없이 곧바로 사용 가능 */ }
}
// 사용: HttpClientBuilder().url("https://...").build().send(req)
// .url() 호출 전에는 build / send 가 컴파일 자체 안 됨
```

**관련 패턴/스멜**:
- [creational.md — Builder](creational.md)
- [behavioral.md — State Pattern](behavioral.md)
- [4. Distributed Monolith](#4-distributed-monolith) (서비스 간 호출 순서 의존)

---

<a id="18-stovepipe-system"></a>
## 18. Stovepipe System

**식별 신호**:
- 같은 조직에서 비슷한 기능의 시스템이 **부서/팀별로 별도** 로 자라남 (회계용 회원 DB, 마케팅용 회원 DB, 영업용 회원 DB)
- 시스템 간 데이터 정합성을 야간 배치 ETL 로 맞춤 (그리고 자주 깨짐)
- 통합 보고서 작성 시 N 개 시스템에서 추출 후 Excel 로 수작업 병합
- 한 시스템의 사용자 ID 가 다른 시스템에서는 다른 형식 (`U12345` vs `user-12345` vs `12345`)
- 새 기능 추가 시 "어느 시스템에 넣지?" 가 정치적 결정

**원인**: 부서별 독립 예산 + 통합 거버넌스 부재 + 단기 납기 우선. 각 부서가 "내 시스템" 을 별도로 발주 → 통합 고려 없이 자람. Brown et al. (1998) 의 원전 정의.

**영향**: 데이터 정합성 ↓ (한 회원의 정보가 시스템마다 다름), 통합 비용 폭증 (N×(N-1)/2 connector), 비즈니스 인텔리전스(BI) 신뢰도 ↓, 시스템 통폐합 시도 매번 정치적으로 실패.

**처방 / 리팩토링**:
- **Master Data Management (MDM)** — 회원/제품/계정 등 마스터 데이터의 단일 진실 소스 도입
- **Event-Driven Integration** — 시스템 간 변경을 이벤트로 broadcast (Kafka / Outbox Pattern)
- **API Gateway / Service Mesh** — 통합 진입점에서 정합성 강제
- **Bounded Context 재정의** — DDD 로 진짜 도메인 경계 식별 후 시스템 통폐합 / 분리 재설계
- **Strangler Fig** — 통합 시스템을 옆에 키우며 stovepipe 를 점진적 흡수
- **거버넌스 강화** — Architecture Review Board, ADR 의무화

**난이도**: 매우 높음 (조직·예산·정치 동반) | **사용 빈도**: ★★★★☆ (중견 이상 조직에서 매우 흔함)

**예제** (의사 코드 / 다이어그램):
```
Bad: 같은 회원이 시스템마다 별도 record
  Sales DB    : customer_id = "C-0001", email = "a@x.com", tier = "GOLD"
  Marketing DB: lead_id     = 12345,     email = "A@X.COM", segment = "premium"
  Accounting  : account     = "ACC0001", email = "a@x.com", grade  = "G1"
  - 한 회원의 등급 변경이 3 곳을 동시에 갱신해야 함 → 자주 어긋남
  - 야간 ETL 로 sync 시도 → 충돌·중복·유실 빈발

Good: Customer 도메인 마스터 + 이벤트 기반 sync
  ┌──────────────────────────────────┐
  │ Customer MDM (단일 진실)          │── publish CustomerUpdated ──┐
  │  id, email, tier, ...             │                              │
  └──────────────────────────────────┘                              │
                                                                     ↓
        ┌────────────────────┬────────────────────┬───────────────────────┐
        │ Sales Read Model   │ Marketing Segment  │ Accounting Account   │
        │ (cache, 자기 책임) │ (분석 전용 view)   │ (재무 추가 속성만)   │
        └────────────────────┴────────────────────┴───────────────────────┘
  - email / tier 의 단일 진실은 MDM 하나
  - 각 시스템은 자기 책임의 read model 만 보유 (CQRS Read-side 와 유사)
```

**관련 패턴/스멜**:
- [4. Distributed Monolith](#4-distributed-monolith) (반대 극단 — 통합 시도 후 강결합)
- [integration.md — Event Bus / Outbox / Saga](integration.md)
- [ddd-tactical.md — Bounded Context](ddd-tactical.md)

---

## 안티패턴 ↔ 처방 매트릭스 (빠른 참조)

| 안티패턴 | 핵심 처방 | 1차 카탈로그 링크 |
|---|---|---|
| 1. Big Ball of Mud | Strangler Fig, Hexagonal, ADR | [architectural.md](architectural.md) |
| 2. God Object | Extract Class, Move Method | [code-smells.md](../principles/code-smells.md#2-large-class) |
| 3. Anemic Domain Model | Move Method → Entity, Aggregate | [ddd-tactical.md](ddd-tactical.md) |
| 4. Distributed Monolith | DB per Service, Event Bus, Saga | [distributed.md](distributed.md) |
| 5. Lava Flow | Dead Code 분석, Feature Flag 만료 | [observability.md](observability.md) |
| 6. Golden Hammer | Problem-First, ADR, YAGNI | [iso25010.md](../principles/iso25010.md) |
| 7. Cargo Cult Programming | First Principles, Rule of Three | [solid.md](../principles/solid.md) |
| 8. Vendor Lock-in | Ports & Adapters, Anti-Corruption Layer | [architectural.md](architectural.md) |
| 9. Spaghetti Code | Extract Function, Guard Clause, State | [behavioral.md](behavioral.md) |
| 10. Magic Numbers / Strings | Symbolic Constant, Enum, Value Object | [code-smells.md](../principles/code-smells.md#3-primitive-obsession) |
| 11. Boat Anchor | 의존성 정리, 사용 추적 | [12-factor.md](../principles/12-factor.md) |
| 12. Premature Optimization | Measure First, 80/20 | [observability.md](observability.md) |
| 13. Reinventing the Wheel | 표준 라이브러리 우선, Build vs Buy | [iso25010.md](../principles/iso25010.md) |
| 14. Yo-Yo Problem | Composition over Inheritance | [structural.md](structural.md) |
| 15. Copy-Paste Programming | Extract Function, Rule of Three | [code-smells.md](../principles/code-smells.md) |
| 16. Hard Coding | 환경 변수, Secret Vault, 12-Factor Config | [12-factor.md](../principles/12-factor.md) |
| 17. Sequential Coupling | Builder, State, Type-State | [creational.md](creational.md) |
| 18. Stovepipe System | MDM, Event-Driven Integration, Bounded Context | [integration.md](integration.md) |
