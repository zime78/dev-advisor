# DDD 전술 패턴 (DDD Tactical Patterns)

Domain-Driven Design 의 전술 패턴은 도메인 모델 내부를 구성하는 빌딩블록이다. Eric Evans 의 Blue Book(2003) 과 Vaughn Vernon 의 IDDD(2013) 를 기준으로, Aggregate 경계와 ubiquitous language 를 코드로 표현하는 데 집중한다. Hexagonal/Onion/Clean Architecture 같은 전략·구조 패턴은 별도 카테고리(`architectural.md`) 에서 다룬다.

---

## 1. Entity

**목적**: 시간이 흘러도 동일성(identity)이 유지되는 도메인 객체를 표현하여 생명주기를 모델링합니다.

**특징**:
- 고유 식별자(ID)로 동등성 판단 (속성값이 바뀌어도 같은 Entity)
- 가변 상태를 가지지만 invariant 를 스스로 보호
- 생성 → 변경 → 삭제의 생명주기를 가짐
- ID 는 도메인 의미가 없는 surrogate 또는 비즈니스 의미가 있는 natural key

**장점**:
- 동일 객체의 상태 변화 추적이 명확
- 비즈니스 규칙을 객체 내부에 응집 가능 (anemic model 회피)
- ORM/Repository 와 자연스럽게 매핑

**단점**:
- 식별자 생성·중복 관리 부담
- 비동기/분산 환경에서 ID 경합 발생 가능

**활용 예시**:
- `Order`, `Customer`, `Invoice` 등 생명주기 있는 도메인 객체
- 사용자 계정 (id 동일 → 이메일 변경 가능)
- 주문 상태 머신

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class Order(val id: OrderId, private var status: OrderStatus) {
    fun ship() {
        require(status == OrderStatus.PAID) { "Only PAID order can ship" }
        status = OrderStatus.SHIPPED
    }

    override fun equals(other: Any?): Boolean =
        other is Order && other.id == this.id
    override fun hashCode(): Int = id.hashCode()
}

@JvmInline value class OrderId(val value: String)
```

**관련 패턴**: Value Object, Aggregate, Repository (DDD)

---

## 2. Value Object

**목적**: 식별자가 없고 속성값 자체로 의미를 가지며 불변인 도메인 개념을 표현합니다.

**특징**:
- 모든 속성이 같으면 동일한 객체로 취급 (structural equality)
- 불변(immutable) — 변경이 필요하면 새 인스턴스 생성
- side-effect-free 메서드만 가짐
- 다른 Value Object 와 자유롭게 교체·복제 가능

**장점**:
- 스레드 안전, 캐싱 친화적
- 도메인 개념(Money, Address)에 비즈니스 의미 부여
- primitive obsession 제거

**단점**:
- 잘못 사용하면 객체 폭증
- DB 매핑 시 embedded/JSON 컬럼 등 추가 설계 필요

**활용 예시**:
- `Money(amount, currency)`, `DateRange`, `Email`, `Address`
- 좌표(Point), 색상(RGB)
- 정책 임계값(Threshold)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
data class Money(val amount: BigDecimal, val currency: Currency) {
    init { require(amount >= BigDecimal.ZERO) { "amount must be >= 0" } }

    operator fun plus(other: Money): Money {
        require(currency == other.currency) { "currency mismatch" }
        return Money(amount + other.amount, currency)
    }
}
```

**관련 패턴**: Entity, Specification, Factory (DDD)

---

## 3. Aggregate

**목적**: 일관성 경계(consistency boundary) 안의 Entity·Value Object 묶음을 하나의 root 로 외부에 노출하여 invariant 를 보호합니다.

**특징**:
- Aggregate Root 만이 외부에서 참조 가능 (내부 객체는 root 를 통해 접근)
- 트랜잭션 단위 = 하나의 Aggregate (Vernon: "Modify one aggregate per transaction")
- 다른 Aggregate 는 ID 로만 참조 (객체 참조 금지)
- 작게 설계하기 (Small Aggregates 원칙)

**장점**:
- 강한 일관성 경계 → 동시성 충돌 최소화
- 비즈니스 invariant 가 코드 한 곳에 집약
- 분산/이벤트 기반 시스템과 자연스러운 매핑

**단점**:
- 경계 설계가 잘못되면 성능/락 문제 또는 일관성 누수
- 큰 Aggregate 는 메모리·동시성 hot spot 발생

**활용 예시**:
- `Order` (root) → `OrderLine` (내부 Entity)
- `Cart` (root) → `CartItem`
- `Auction` (root) → `Bid`

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class Order(
    val id: OrderId,
    private val lines: MutableList<OrderLine> = mutableListOf(),
) {
    fun addLine(sku: Sku, qty: Int, price: Money) {
        require(qty > 0)
        lines += OrderLine(sku, qty, price)
    }

    fun total(): Money = lines
        .map { it.price * it.qty }
        .reduce(Money::plus)

    fun lines(): List<OrderLine> = lines.toList() // 방어적 복사
}
```

**관련 패턴**: Entity, Domain Event, Repository (DDD), Unit of Work

---

## 4. Domain Event

**목적**: 도메인에서 의미 있는 사실 발생(과거형)을 일급 객체로 표현하여 시스템 간 결합도를 낮춥니다.

**특징**:
- 과거형 명명 (`OrderPlaced`, `PaymentReceived`)
- 불변·timestamp 포함
- Aggregate 가 자기 변경 결과로 이벤트를 발행
- 이벤트 핸들러는 다른 Aggregate/Bounded Context 가 구독

**장점**:
- Aggregate 간 결합도 ↓ (직접 호출 대신 이벤트)
- Event Sourcing / CQRS 기반 마련
- 감사 로그·재현 가능성 향상

**단점**:
- eventual consistency → 디버깅·테스트 난이도 증가
- 이벤트 스키마 진화 관리 부담

**활용 예시**:
- 주문 완료 시 결제·재고·알림 분리 처리
- 회원 가입 → 환영 메일·포인트 적립 fan-out
- 마이크로서비스 간 통합

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
sealed interface DomainEvent { val occurredAt: Instant }

data class OrderPlaced(
    val orderId: OrderId,
    val total: Money,
    override val occurredAt: Instant = Instant.now(),
) : DomainEvent

class Order(val id: OrderId) {
    private val _events = mutableListOf<DomainEvent>()
    val events: List<DomainEvent> get() = _events

    fun place(total: Money) {
        _events += OrderPlaced(id, total)
    }
}
```

**관련 패턴**: Aggregate, Event Sourcing, Saga, Observer

---

## 5. Domain Service

**목적**: 특정 Entity·Value Object 어디에도 자연스럽게 속하지 않는 도메인 로직을 stateless 한 서비스로 표현합니다.

**특징**:
- 도메인 언어로 명명 (`TransferService`, `PricingPolicy`)
- 무상태(stateless), 부수효과 최소
- 여러 Aggregate 를 조율(orchestrate) 하지만 직접 수정은 Aggregate 에 위임
- Application Service 와 구분: Domain Service 는 도메인 규칙, Application Service 는 use-case orchestration

**장점**:
- "어디에 둘지 애매한" 로직의 표준 자리 제공
- Aggregate 의 책임을 과도하게 늘리지 않음

**단점**:
- 남용 시 anemic domain model 회귀 (모든 로직이 service 로 빠짐)
- Application Service 와 혼동되기 쉬움

**활용 예시**:
- 계좌 간 이체 (`TransferService`: 두 Account aggregate 조정)
- 환율 변환, 세금 계산
- 매칭/배차 로직

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class TransferService {
    fun transfer(from: Account, to: Account, amount: Money) {
        from.withdraw(amount)
        try {
            to.deposit(amount)
        } catch (e: Exception) {
            from.deposit(amount) // compensate
            throw e
        }
    }
}
```

**관련 패턴**: Aggregate, Specification, Application Service

---

## 6. Specification

**목적**: "어떤 조건을 만족하는가?" 라는 도메인 규칙을 객체로 캡슐화하여 조합·재사용·테스트할 수 있게 합니다.

**특징**:
- `isSatisfiedBy(candidate): Boolean` 단일 메서드
- `and / or / not` 으로 조합 가능 (Composite)
- 검증·선택·생성 세 가지 용도 (Evans)
- Repository 와 결합 시 Query Specification 으로 확장

**장점**:
- 비즈니스 규칙을 if 블록에서 객체로 추출 → 재사용·테스트 ↑
- 규칙 변경 시 한 곳만 수정
- 도메인 언어로 표현되어 가독성 좋음

**단점**:
- 단순 조건엔 과한 추상화
- DB 조회용으로 사용하면 ORM 매핑 복잡

**활용 예시**:
- `PremiumCustomerSpec`, `OverdueInvoiceSpec`
- 할인 정책 조합
- 검색 필터 빌더

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
fun interface Spec<T> {
    fun isSatisfiedBy(candidate: T): Boolean
    infix fun and(other: Spec<T>) = Spec<T> { isSatisfiedBy(it) && other.isSatisfiedBy(it) }
}

val premium = Spec<Customer> { it.totalSpent > Money(BigDecimal(10_000), KRW) }
val active  = Spec<Customer> { it.lastOrderAt.isAfter(Instant.now().minus(90, DAYS)) }

val targetSpec = premium and active
```

**관련 패턴**: Composite, Strategy, Query Object

---

## 7. Anti-Corruption Layer (ACL)

**목적**: 외부(legacy 또는 타 Bounded Context) 모델을 우리 도메인 모델로 변환하여, 외부 개념의 침투를 차단합니다.

**특징**:
- 경계에서 양방향 변환 (외부 DTO ↔ 내부 도메인)
- Adapter·Facade·Translator 의 조합으로 구현
- Hexagonal/Onion 의 outbound adapter 위치에 자주 배치됨 (port-adapter 경계에서 외부 모델 침투를 막는 layer)
- legacy 시스템 통합·외부 API 연동에 필수

**장점**:
- 외부 변경이 도메인 코어로 전파되지 않음
- ubiquitous language 보호
- 점진적 legacy 교체(strangler) 가능

**단점**:
- 변환 코드·이중 모델 유지 비용
- 성능 오버헤드 (DTO ↔ 도메인 매핑)

**활용 예시**:
- 모놀리스 → 마이크로서비스 분리 중간 단계
- 외부 Jira/Salesforce API 호출 wrapper
- 외부 결제사 webhook payload 변환

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// 외부 legacy 모델
data class LegacyOrderDto(val orderNo: String, val amt: Double, val cur: String)

// ACL: 외부 → 내부 도메인 변환
class LegacyOrderAcl(private val legacyApi: LegacyOrderApi) {
    fun fetch(id: OrderId): Order {
        val dto = legacyApi.get(id.value)
        return Order(
            id = OrderId(dto.orderNo),
            total = Money(BigDecimal(dto.amt), Currency.getInstance(dto.cur)),
        )
    }
}
```

**관련 패턴**: Adapter, Facade, Hexagonal Architecture (port-adapter), Bounded Context

---

## 8. Bounded Context

**목적**: 하나의 도메인 모델이 일관되게 유효한 명시적 경계를 정의하여 ubiquitous language 의 의미를 보호합니다.

**특징**:
- 같은 단어(예: "Customer") 가 context 마다 다른 의미를 가질 수 있음
- 한 팀·한 모델·한 언어 원칙
- 모듈/서비스/데이터베이스 경계와 정렬되는 경우가 많음
- 다른 context 와의 관계는 Context Map 으로 표현

**장점**:
- 도메인 모델의 결합도 ↓ → 독립적 진화
- 팀 자율성 확보
- 마이크로서비스 분해 기준 제공

**단점**:
- 경계 설계 실패 시 분산 모놀리스
- context 간 통합 비용 (이벤트, ACL 등)

**활용 예시**:
- 전자상거래: Sales / Billing / Shipping context 분리
- 동일 "Product" 가 Catalog 와 Inventory 에서 다른 책임
- 보험: Underwriting / Claims context

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Sales context
package sales
data class Product(val id: ProductId, val price: Money, val description: String)

// Inventory context — 같은 이름이지만 다른 모델
package inventory
data class Product(val id: ProductId, val stock: Int, val warehouse: WarehouseId)
```

**관련 패턴**: Context Map, Anti-Corruption Layer, Modular Monolith

---

## 9. Context Map

**목적**: 여러 Bounded Context 사이의 관계와 통합 패턴을 명시적으로 문서화하여 시스템 전체 구조를 가시화합니다.

**특징**:
- 관계 유형: Partnership / Customer-Supplier / Conformist / ACL / Open-Host Service / Published Language / Shared Kernel / Separate Ways
- 상류(upstream) ↔ 하류(downstream) 권력 관계 표현
- 다이어그램과 텍스트 문서의 결합

**장점**:
- 통합 전략을 의식적으로 선택
- 조직-시스템 정렬 (Conway's law)
- 변경 영향도 추정 가능

**단점**:
- 문서로 머무르고 코드에 반영 안 되면 무의미
- 큰 조직에선 유지 비용 큼

**활용 예시**:
- 마이크로서비스 dependency 다이어그램
- 팀 간 API 계약 협상
- legacy 통합 전략 수립

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// Context Map 은 코드보단 문서이지만, integration 지점은 코드로 표현된다
// Open-Host Service: Sales context 가 공개 API 제공
interface SalesOpenHostApi {
    fun getProductCatalog(): List<ProductDto>  // Published Language (DTO)
}

// Downstream Conformist: Recommendation context 가 그대로 수용
class RecommendationService(private val salesApi: SalesOpenHostApi) {
    fun recommend() = salesApi.getProductCatalog().take(10)
}
```

**관련 패턴**: Bounded Context, Anti-Corruption Layer, Published Language

---

## 10. Factory (DDD-style)

**목적**: 복잡한 Aggregate 나 Value Object 의 생성 로직을 캡슐화하여, 클라이언트가 invariant 위반 없이 객체를 만들도록 합니다.

**특징**:
- Aggregate Root 의 정적 메서드 또는 별도 Factory 클래스
- 생성 시점의 invariant 검증을 한 곳에 집약
- 도메인 언어로 명명 (`Order.place(...)`, `AccountFactory.openFor(customer)`)
- GoF Factory Method/Abstract Factory 와는 의도가 다름 — DDD Factory 는 "올바른 도메인 객체 생성" 이 초점

**장점**:
- 생성자 폭발(constructor overloading) 회피
- Aggregate 가 절대 invalid 상태로 존재하지 않도록 보장
- 복잡한 그래프 생성 캡슐화

**단점**:
- 단순 생성엔 과함
- 다른 Aggregate 의 정보가 필요하면 Domain Service 와 책임이 겹침

**활용 예시**:
- `Order.place(customer, items)` 정적 팩토리
- `AccountFactory.openSavingAccount(...)`
- 이벤트 소싱 재구성: `Order.replay(events)`

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
class Order private constructor(val id: OrderId, val lines: List<OrderLine>) {
    companion object {
        fun place(customer: Customer, cart: Cart): Order {
            require(cart.isNotEmpty()) { "empty cart" }
            require(customer.isActive()) { "inactive customer" }
            return Order(
                id = OrderId(UUID.randomUUID().toString()),
                lines = cart.items.map { OrderLine(it.sku, it.qty, it.price) },
            )
        }
    }
}
```

**관련 패턴**: Aggregate, Domain Service, Builder, GoF Factory Method

---

## 11. Repository (DDD-style)

**목적**: Aggregate Root 의 영속화·재구성을 인메모리 컬렉션처럼 추상화하여, 도메인 코드가 저장 기술을 모르게 합니다.

**특징**:
- **Aggregate 단위로만** 제공 (`OrderRepository` O, `OrderLineRepository` X)
- 인터페이스는 도메인 layer, 구현은 infrastructure layer
- 메서드명은 도메인 언어 (`findOverdueOrders()`)
- 단순 CRUD 가 아니라 도메인 의도가 드러나야 함
- Fowler 의 PoEAA Repository 는 collection-like 추상화 일반이지만, DDD Repository 는 **Aggregate 경계** 와 **ubiquitous language** 를 추가 요구한다 (자세한 collection-like / persistence-oriented 구분은 `data-access.md` 참조)

**장점**:
- 도메인이 DB·ORM 에 비의존 → 테스트(in-memory) 용이
- Aggregate 경계가 코드로 명시
- 저장 기술 교체 가능 (RDB → 이벤트 스토어)

**단점**:
- N+1 등 성능 이슈를 추상화가 가릴 수 있음
- 잘못 설계하면 generic DAO 로 회귀

**활용 예시**:
- `OrderRepository.findById(id)`, `OrderRepository.save(order)`
- `CustomerRepository.findActivePremiumCustomers()`
- Event-sourced aggregate 재구성

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// 도메인 layer — 인터페이스만
interface OrderRepository {
    fun findById(id: OrderId): Order?
    fun save(order: Order)
    fun findOverdue(asOf: Instant): List<Order>
}

// infrastructure layer — 구현
class JpaOrderRepository(private val em: EntityManager) : OrderRepository {
    override fun findById(id: OrderId): Order? = em.find(OrderEntity::class.java, id.value)?.toDomain()
    override fun save(order: Order) { em.merge(OrderEntity.from(order)) }
    override fun findOverdue(asOf: Instant): List<Order> =
        em.createQuery("...", OrderEntity::class.java).resultList.map { it.toDomain() }
}
```

**관련 패턴**: Aggregate, Specification, Unit of Work, Repository (PoEAA)
