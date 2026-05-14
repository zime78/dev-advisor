# eCommerce 도메인 패턴 (eCommerce Domain Patterns)

온라인 커머스 정평 있는 12 패턴. Amazon / Shopify / Stripe Commerce / Magento 사례 + DDD eCommerce Bounded Context.

**원전·표준 참고**:
- Vaughn Vernon — *Implementing Domain-Driven Design* (2013), Chapter 13 eCommerce 사례
- Eric Evans — *Domain-Driven Design* (2003), Cargo shipping 사례 (eCommerce 와 인접)
- Sam Newman — *Building Microservices*, eCommerce 마이크로서비스 사례
- Shopify Engineering Blog, Stripe Engineering Blog
- IFRS / K-IFRS (수익 인식 — Loyalty Liability)

**핵심 도메인 컨텍스트** (DDD Bounded Context):
- **Catalog** — Product, Variant, SKU, Inventory
- **Cart & Checkout** — Cart, Address, Payment Intent
- **Order Management** — Order, Fulfillment, Returns
- **Pricing** — Promotion, Coupon, Tax
- **Customer** — Profile, Loyalty, Address Book

**관련 카탈로그**:
- [`../ddd-tactical.md`](../ddd-tactical.md) — Aggregate, Bounded Context, Domain Event
- [`./fintech.md`](./fintech.md) — Payment Intent / Refund / Subscription (eCommerce 결제 부분 cross-link)
- [`../distributed.md`](../distributed.md) — Saga (주문 분산 트랜잭션), Idempotency
- [`../caching.md`](../caching.md) — Product catalog cache

---

## 1. Cart Aggregate <a id="cart-aggregate"></a>

**목적**: 사용자가 구매 의향을 표현한 상품 묶음을 일관성 경계(Aggregate)로 보호하여, 추가·삭제·수량 변경의 invariant 와 가격 스냅샷을 안전하게 관리합니다.

**메커니즘**:
- **Cart Aggregate Root** = `CartId` 식별. 내부에 `CartItem` 컬렉션 (Entity 또는 Value Object)
- **Guest Cart vs User Cart** — 비로그인은 쿠키/디바이스 ID, 로그인 후 User Cart 와 merge
- **Cart Merge 전략** — (a) 합집합(quantity sum), (b) User Cart 우선 덮어쓰기, (c) 사용자에게 선택 요청. Shopify 는 합집합 + max(qty) 기본
- **TTL / Abandoned Cart** — guest cart 14~30 일, user cart 90 일 또는 영구. TTL 만료 시 abandoned cart 이벤트 → 마케팅 트리거
- **가격 스냅샷** — `CartItem.priceSnapshot` 으로 추가 시점 가격 보존. checkout 직전 재계산 vs 보존 정책 결정 필요
- **재고 hold 와 분리** — Cart 추가는 가벼움, hold 는 Checkout 진입 시 (`#inventory-reservation` 참조)

**장점**:
- 일관성 경계 분명 → 동시성 (다중 탭 추가) 충돌 최소화
- Abandoned cart 분석·리마케팅 데이터 소스
- 가격·프로모션 변경의 영향 범위 가시화

**단점·주의**:
- Aggregate 가 너무 커지면 (100+ items) 메모리·락 비용 증가 → 페이지네이션 또는 분할 Aggregate 고려
- Guest → User merge 충돌 시 사용자 confirmation UI 필수 (실제 분쟁 다발)
- 가격 스냅샷 vs 실시간 가격: checkout 시점에 항상 재검증해야 함 (스냅샷은 표시용)

**DDD 매핑**:
- **Aggregate Root**: `Cart`
- **Entity**: `CartItem`
- **Value Object**: `Money`, `Sku`, `Quantity`
- **Domain Event**: `ItemAddedToCart`, `CartAbandoned`, `CartsMerged`

**Kotlin 예제**:
```kotlin
class Cart(
    val id: CartId,
    val ownerId: CustomerId?,  // null = guest
    private val items: MutableMap<Sku, CartItem> = mutableMapOf(),
    var expiresAt: Instant = Instant.now().plus(30, DAYS),
) {
    fun addItem(sku: Sku, qty: Int, priceSnapshot: Money) {
        require(qty in 1..99) { "qty out of range" }
        items.compute(sku) { _, existing ->
            existing?.copy(qty = existing.qty + qty)
                ?: CartItem(sku, qty, priceSnapshot)
        }
    }

    fun removeItem(sku: Sku) { items.remove(sku) }

    fun merge(other: Cart): Cart {
        other.items.forEach { (sku, item) ->
            addItem(sku, item.qty, item.priceSnapshot)
        }
        return this
    }

    fun subtotal(): Money = items.values
        .map { it.priceSnapshot * it.qty }
        .reduceOrNull(Money::plus) ?: Money.ZERO_KRW

    fun isEmpty(): Boolean = items.isEmpty()
}

data class CartItem(val sku: Sku, val qty: Int, val priceSnapshot: Money)
```

**관련 패턴**: [Aggregate](../ddd-tactical.md), [Domain Event](../ddd-tactical.md), [Inventory Reservation](#inventory-reservation), [Checkout Flow](#checkout-flow)

---

## 2. Inventory Reservation / Soft Hold <a id="inventory-reservation"></a>

**목적**: 한정된 재고를 여러 사용자가 동시에 구매하려 할 때 oversell(초과판매) 을 방지하면서, checkout 진행 중에는 다른 사용자가 그 수량을 가져가지 못하도록 임시 점유합니다.

**메커니즘**:
- **3 단계 stock state**: `available` / `reserved` / `committed`
- **Cart add** → stock 영향 없음 (가벼움)
- **Checkout 진입** → `reserve(sku, qty, ttl=10min)` 호출 → `available -= qty`, `reserved += qty`
- **결제 성공** → `commit(reservationId)` → `reserved -= qty`, `committed += qty`
- **TTL 만료 / 결제 실패** → `release(reservationId)` → `reserved -= qty`, `available += qty`
- **동시성 처리**: (a) DB pessimistic lock (`SELECT ... FOR UPDATE`), (b) optimistic lock + version 컬럼, (c) Redis `DECR` + Lua script, (d) 외부 inventory service (Redis Cluster 또는 전용 서비스)
- **분산 환경**: Saga 패턴으로 reservation → payment → fulfillment 트랜잭션 분해

**장점**:
- Black Friday / 한정판 드롭 같은 동시성 폭주에서 oversell 차단
- 사용자 신뢰 ↑ (장바구니에 담았는데 결제 시점에 품절 회피)
- 회계·물류와 재고 상태 명확히 분리

**단점·주의**:
- TTL 너무 짧으면 결제 중 release 되어 사용자 이탈, 너무 길면 가용재고 고갈
- Redis 만 쓰면 영속성 / failover 시 reservation 유실 → DB persist 백업 필수
- "Cart 에 담은 순간 hold" 정책은 봇·다중탭 사용자가 재고 고갈시킴 → 추천하지 않음
- oversell 이 비즈니스적으로 허용되는 경우 (예: 예약판매 / 백오더) 는 별도 모델

**DDD 매핑**:
- **Aggregate Root**: `StockItem` (per SKU)
- **Entity**: `Reservation`
- **Value Object**: `ReservationId`, `Quantity`
- **Domain Event**: `StockReserved`, `StockReleased`, `StockCommitted`, `OversellAttempted`

**Kotlin 예제**:
```kotlin
class StockItem(
    val sku: Sku,
    private var available: Int,
    private val reservations: MutableMap<ReservationId, Reservation> = mutableMapOf(),
    @Version private var version: Long = 0,  // optimistic lock
) {
    fun reserve(qty: Int, ttl: Duration): ReservationId {
        require(qty > 0)
        if (available < qty) throw OutOfStockException(sku, requested = qty, have = available)
        val id = ReservationId.new()
        reservations[id] = Reservation(id, qty, expiresAt = Instant.now() + ttl)
        available -= qty
        return id
    }

    fun commit(id: ReservationId) {
        val r = reservations.remove(id) ?: throw IllegalStateException("unknown reservation")
        if (r.isExpired()) throw ReservationExpiredException(id)
        // committed counter 는 별도 집계 (또는 outbox 이벤트)
    }

    fun release(id: ReservationId) {
        val r = reservations.remove(id) ?: return
        available += r.qty
    }
}

data class Reservation(val id: ReservationId, val qty: Int, val expiresAt: Instant) {
    fun isExpired() = Instant.now().isAfter(expiresAt)
}
```

**관련 패턴**: [Cart Aggregate](#cart-aggregate), [Order State Machine](#order-state-machine), [Saga](../distributed.md), [Optimistic Lock](../concurrency.md)

---

## 3. Product Catalog (계층 카탈로그) <a id="product-catalog"></a>

**목적**: 수만~수천만 개의 상품을 카테고리·variant·SKU 의 계층으로 조직화하여 탐색·검색·재고 관리를 모두 효율화합니다.

**메커니즘**:
- **Category Tree** — 다단계 카테고리 (Electronics > Phones > Smartphones). 모델: (a) Adjacency List(parent_id), (b) Nested Set Model, (c) Materialized Path, (d) Closure Table
- **Product** — 사용자 관점의 상품 entity (e.g. "갤럭시 S24")
- **Variant** — 선택 가능한 옵션 조합 (color=black, size=256GB)
- **SKU (Stock Keeping Unit)** — 재고·가격·바코드의 최소 단위. variant 1:1 매핑
- **Faceted Navigation** — 카테고리 + 필터(가격/브랜드/색상) 조합. 검색 인덱스에 facet 필드 미리 인덱싱 (`#search-discovery` 참조)
- **Attribute Schema** — EAV(Entity-Attribute-Value) 또는 JSONB 컬럼. EAV 는 검색 어려움 → JSONB + GIN 인덱스 또는 별도 검색 엔진 권장
- **DDD 관점**: Catalog 와 Inventory 는 별도 Bounded Context — 같은 `Product` 이름이지만 다른 모델

**장점**:
- 사용자 탐색 경로 다양화 (카테고리 / 검색 / facet)
- variant 별 재고·가격 독립 관리
- SEO 친화적 URL 구조 (/electronics/phones/galaxy-s24)

**단점·주의**:
- 카테고리 트리 깊이가 너무 깊으면 (>5) 사용자 인지 부하 ↑
- variant 폭발 (5색 × 4용량 × 3통신사 = 60 SKU) → 관리 부담
- EAV 남용 → 쿼리 성능 저하. 자주 검색되는 속성은 컬럼화

**DDD 매핑**:
- **Aggregate Root**: `Product` (with variants), `Category`
- **Entity**: `Variant`
- **Value Object**: `Sku`, `Money`, `AttributeSet`
- **Domain Event**: `ProductPublished`, `VariantPriceChanged`, `ProductDiscontinued`

**Kotlin 예제**:
```kotlin
class Product(
    val id: ProductId,
    val name: String,
    val categoryPath: CategoryPath,  // e.g. "electronics/phones/smartphones"
    private val variants: MutableList<Variant> = mutableListOf(),
) {
    fun addVariant(attrs: Map<String, String>, sku: Sku, price: Money) {
        require(variants.none { it.attributes == attrs }) { "duplicate variant" }
        variants += Variant(VariantId.new(), sku, attrs, price)
    }

    fun variantFor(attrs: Map<String, String>): Variant? =
        variants.firstOrNull { it.attributes == attrs }

    fun priceRange(): ClosedRange<Money> {
        val prices = variants.map { it.price }
        return prices.min()..prices.max()
    }
}

data class Variant(
    val id: VariantId,
    val sku: Sku,
    val attributes: Map<String, String>,  // color=black, size=256GB
    val price: Money,
)

@JvmInline value class CategoryPath(val value: String) {
    fun ancestors(): List<CategoryPath> = value.split("/")
        .scan("") { acc, seg -> if (acc.isEmpty()) seg else "$acc/$seg" }
        .filter { it.isNotEmpty() }
        .map(::CategoryPath)
}
```

**관련 패턴**: [Bounded Context](../ddd-tactical.md), [Search & Discovery](#search-discovery), [Pricing](#pricing-promotion-engine), [Caching](../caching.md)

---

## 4. Pricing & Promotion Engine <a id="pricing-promotion-engine"></a>

**목적**: 정가·할인·쿠폰·세금이 결합된 최종 가격을 결정하는 규칙을 코드 변경 없이 유연하게 구성·우선순위·스택 가능하게 만듭니다.

**메커니즘**:
- **Rule-based** — `Promotion` 이 `Condition` + `Action` 으로 구성. e.g. "Cart 합계 5만원 이상이면 5천원 할인"
- **Discount Type**: (a) percentage off, (b) fixed amount off, (c) BOGO (Buy One Get One), (d) free shipping, (e) gift item
- **Coupon vs Auto-apply** — 코드 입력형 (`SUMMER10`) vs 조건 만족 시 자동 적용
- **Stacking Rule**: (a) only-one (가장 큰 할인만), (b) stackable (모두 적용), (c) category 기반 (배송 + 가격 동시 OK)
- **Tax Inclusion** — 한국 / EU 는 부가세 포함 표시 (VAT-inclusive), 미국은 별도 (sales tax exclusive). `Money` 가 `taxIncluded` flag 보유
- **순서**: catalog price → product discount → cart discount → coupon → tax → shipping → loyalty redemption. 각 단계 결과는 audit log
- **Idempotency** — 같은 cart + 같은 coupon = 같은 결과여야 함 (시간 외 변수 의존 금지)

**장점**:
- 마케팅 팀이 운영 도구에서 프로모션 신설 (개발 배포 불필요)
- 적용 이유 audit log 로 CS 대응 용이
- A/B 테스트 친화적

**단점·주의**:
- Rule 수가 늘면 디버깅 어려움 → 규칙 ID 와 적용 순서 항상 로깅
- Stacking 폭주로 마진 손실 발생 가능 → "max discount cap" 필수
- 부동소수점 사용 금지. 항상 `BigDecimal` + 통화 단위(원/센트) 정수 변환
- 통화 변환 시 환율 시점 (주문 생성 시점 고정 vs 결제 시점) 정책 명시 필요

**DDD 매핑**:
- **Aggregate Root**: `Promotion`, `Coupon`
- **Value Object**: `Discount`, `Money`, `TaxRate`
- **Domain Service**: `PricingService` (여러 Aggregate 조합)
- **Domain Event**: `PromotionApplied`, `CouponRedeemed`, `DiscountCapExceeded`

**Kotlin 예제**:
```kotlin
sealed interface Discount {
    fun apply(line: CartLine): Money

    data class Percentage(val pct: BigDecimal) : Discount {
        override fun apply(line: CartLine) = line.subtotal * pct / BigDecimal(100)
    }
    data class FixedAmount(val amount: Money) : Discount {
        override fun apply(line: CartLine) = amount.min(line.subtotal)
    }
}

data class Promotion(
    val id: PromotionId,
    val name: String,
    val condition: Spec<Cart>,
    val discount: Discount,
    val stackable: Boolean,
    val priority: Int,  // 낮을수록 먼저
)

class PricingService(private val promos: List<Promotion>) {
    fun price(cart: Cart, appliedCoupons: List<Coupon>): PricedCart {
        var working = cart.toPriced()
        val log = mutableListOf<PriceAdjustment>()

        promos.filter { it.condition.isSatisfiedBy(cart) }
            .sortedBy { it.priority }
            .takeWhile { it.stackable || log.isEmpty() }
            .forEach { promo ->
                val before = working.total
                working = working.applyDiscount(promo.discount)
                log += PriceAdjustment(promo.id, before - working.total)
            }
        return working.copy(adjustments = log)
    }
}
```

**관련 패턴**: [Specification](../ddd-tactical.md), [Domain Service](../ddd-tactical.md), [Cart Aggregate](#cart-aggregate), [Loyalty](#loyalty-rewards)

---

## 5. Order State Machine <a id="order-state-machine"></a>

**목적**: 주문이 거치는 모든 상태와 전이 규칙을 명시적 state machine 으로 표현하여, 잘못된 상태 전이를 컴파일 타임 또는 런타임에 차단합니다.

**메커니즘**:
- **표준 상태 흐름**:

```
┌─────────┐   place    ┌────────┐  authorize   ┌──────────┐
│ Created ├───────────►│Pending ├─────────────►│ Paid     │
└─────────┘            │Payment │              └────┬─────┘
     │                 └────┬───┘                   │ pick
     │ cancel               │ fail                  ▼
     ▼                      ▼                  ┌──────────┐
┌─────────┐            ┌──────────┐  pack      │ Picked   │
│Cancelled│            │  Failed  │            └────┬─────┘
└─────────┘            └──────────┘                 │ ship
                                                    ▼
                       ┌─────────┐  return    ┌──────────┐
                       │Returned │◄───────────┤ Shipped  │
                       └─────────┘            └────┬─────┘
                                                   │ deliver
                                                   ▼
                                              ┌──────────┐
                                              │Delivered │
                                              └──────────┘
```

- **Guard**: 각 전이에 사전조건. `Paid → Picked` 는 재고 commit + 창고 작업자 할당 필요
- **불변 상태**: `Delivered`, `Cancelled`, `Returned` 는 terminal — 더 이상 전이 불가
- **State 표현**: (a) enum + when 분기, (b) sealed class 상태별 데이터 분리, (c) state pattern (각 state 가 class)
- **History 보존**: state 전이 시 `OrderStateTransition` 이벤트 → audit log
- **재진입성 (Idempotency)**: 동일 입력에 동일 상태 (재시도 안전)

**장점**:
- 잘못된 상태 전이 (e.g. `Created → Shipped`) 차단
- CS 가 주문 상태를 한눈에 파악
- 분산 시스템에서 state 동기화 기준

**단점·주의**:
- 상태가 너무 많아지면 (>15) state explosion → 하위 sub-state machine 으로 분리
- "Partial Shipment" / "Backorder" 같은 변종은 별도 state 또는 OrderLine 단위 state machine 필요
- 결제 cancel + refund + return 의 흐름은 별도 (Refund / RMA 참조)

**DDD 매핑**:
- **Aggregate Root**: `Order`
- **Entity**: `OrderLine`, `Shipment`
- **Value Object**: `OrderStatus`, `Money`
- **Domain Event**: `OrderPlaced`, `OrderPaid`, `OrderShipped`, `OrderDelivered`, `OrderCancelled`

**Kotlin 예제**:
```kotlin
sealed interface OrderStatus {
    object Created : OrderStatus
    object PendingPayment : OrderStatus
    object Paid : OrderStatus
    object Picked : OrderStatus
    object Shipped : OrderStatus
    object Delivered : OrderStatus
    data class Cancelled(val reason: String) : OrderStatus
    data class Returned(val rmaId: RmaId) : OrderStatus
}

class Order(val id: OrderId, private var status: OrderStatus = OrderStatus.Created) {
    private val events = mutableListOf<DomainEvent>()

    fun authorizePayment(): Result<Unit> {
        require(status == OrderStatus.Created) { "cannot authorize from $status" }
        status = OrderStatus.PendingPayment
        events += PaymentAuthorizationRequested(id)
        return Result.success(Unit)
    }

    fun markPaid() {
        require(status == OrderStatus.PendingPayment) { "cannot mark paid from $status" }
        status = OrderStatus.Paid
        events += OrderPaid(id)
    }

    fun ship(trackingNo: String) {
        require(status == OrderStatus.Picked) { "ship requires Picked, was $status" }
        status = OrderStatus.Shipped
        events += OrderShipped(id, trackingNo)
    }

    fun cancel(reason: String) {
        require(status !is OrderStatus.Shipped && status !is OrderStatus.Delivered)
        status = OrderStatus.Cancelled(reason)
        events += OrderCancelled(id, reason)
    }
}
```

**관련 패턴**: [Aggregate](../ddd-tactical.md), [Domain Event](../ddd-tactical.md), [Saga](../distributed.md), [Returns / RMA](#returns-rma)

---

## 6. Checkout Flow <a id="checkout-flow"></a>

**목적**: 사용자가 cart 에서 결제 완료까지의 단계를 안내하면서, 주소·배송·결제·약관 동의를 수집하고 최종 주문을 생성합니다.

**메커니즘**:
- **Single-page vs Multi-step**:
  - Single-page (Amazon-style) — 모든 입력을 한 화면에 모음. 빠르지만 모바일에 부담
  - Multi-step (Shopify default) — Information → Shipping → Payment → Review. 진행률 표시
- **Guest Checkout** — 비로그인 결제 허용. 이메일·주소만 받고 계정 생성은 선택. 전환율 ↑ 핵심
- **Address Validation** — (a) Google Address Autocomplete, (b) Loqate / Smarty 등 정형화, (c) 우편번호 → 시/구 자동 채움 (한국 우편번호 API)
- **Address Book** — 로그인 사용자는 저장된 주소 선택. 기본 배송지 + 청구지 분리 가능
- **Idempotency Key** — checkout submit 시 client UUID 전달 → 중복 제출 방지 (네트워크 끊김 / 더블 클릭)
- **Inventory hold + Payment Intent 동시 수행** — Stripe `PaymentIntent` 생성 + reservation 생성 → 둘 다 성공해야 주문 생성
- **약관 동의** — 한국은 7세 미만 / 14세 미만 분리, 마케팅 동의 별도

**장점**:
- 단계별 검증으로 입력 오류 조기 발견
- guest checkout 으로 신규 사용자 전환율 +30~50% (업계 평균)
- idempotency key 로 중복 결제 사고 차단

**단점·주의**:
- 단계가 많을수록 cart abandonment ↑ → 모바일은 3 단계 이하 권장
- 주소 자동완성 API 비용 (월 수만 건이면 무료, 초과 시 과금)
- "결제는 됐는데 주문 생성 실패" 시나리오: Saga + outbox 패턴으로 일관성 확보
- 한국 PG 사 결제는 redirect-based → checkout state 보존 어려움 → server-side cart snapshot

**DDD 매핑**:
- **Aggregate Root**: `Checkout` (또는 `CheckoutSession`)
- **Entity**: `Order` (생성 결과)
- **Value Object**: `Address`, `ShippingMethod`, `PaymentMethod`, `IdempotencyKey`
- **Domain Event**: `CheckoutStarted`, `CheckoutCompleted`, `CheckoutAbandoned`

**Kotlin 예제**:
```kotlin
class CheckoutSession(
    val id: CheckoutId,
    val cartSnapshot: Cart,
    val idempotencyKey: IdempotencyKey,
) {
    var shippingAddress: Address? = null
    var billingAddress: Address? = null
    var shippingMethod: ShippingMethod? = null
    var paymentMethod: PaymentMethod? = null

    fun complete(orderService: OrderService): Order {
        requireNotNull(shippingAddress) { "shipping address required" }
        requireNotNull(paymentMethod) { "payment method required" }
        return orderService.placeOrder(
            cart = cartSnapshot,
            shipping = shippingAddress!!,
            billing = billingAddress ?: shippingAddress!!,
            payment = paymentMethod!!,
            idempotencyKey = idempotencyKey,
        )
    }
}

data class Address(
    val recipient: String,
    val phone: String,
    val zipCode: String,
    val line1: String,
    val line2: String?,
    val city: String,
    val country: CountryCode,
) {
    init {
        require(phone.matches(Regex("^[0-9+\\-]{8,15}$"))) { "invalid phone" }
        require(zipCode.isNotBlank()) { "zip required" }
    }
}
```

**관련 패턴**: [Cart Aggregate](#cart-aggregate), [Inventory Reservation](#inventory-reservation), [Order State Machine](#order-state-machine), [Idempotency](../distributed.md)

---

## 7. Fulfillment / Warehouse Pick-Pack-Ship <a id="fulfillment-warehouse"></a>

**목적**: 결제 완료된 주문을 창고에서 picking → packing → shipping 으로 처리하면서, 복수 창고 분할 배송과 작업 효율을 최적화합니다.

**메커니즘**:
- **Pick List** — 창고 작업자가 들고 다닐 picking 작업 목록. SKU 위치(랙/통로/선반) 순서로 정렬 → 동선 최소화
- **Wave Picking** — 여러 주문을 한 번에 picking → packing 단계에서 주문별 재분류. 처리량 ↑
- **Multi-warehouse Split Shipment** — 주문 항목들이 다른 창고에 있으면 분할 배송. (a) 동시 배송 (사용자 만족 ↑, 비용 ↑), (b) 한 창고로 transfer 후 통합 배송 (비용 ↓, 시간 ↑)
- **Allocation Strategy**: (a) nearest warehouse to customer, (b) cheapest shipping cost, (c) balance inventory across warehouses, (d) priority + SLA
- **Pack 단계**: 박스 사이즈 결정 (bin-packing 알고리즘), 동봉물 (영수증, 쿠폰), 송장 출력
- **Carrier Integration**: 한국 — CJ대한통운 / 한진택배 / 우체국, 글로벌 — FedEx / UPS / DHL. Tracking number 발급 → 사용자에게 알림
- **Returns 처리는 별도 흐름** (`#returns-rma` 참조)

**장점**:
- Wave picking 으로 worker 효율 2~3 배
- multi-warehouse 로 SLA 단축 (lastmile 거리 ↓)
- 박스 최적화로 운임 절감

**단점·주의**:
- 복잡한 allocation 알고리즘은 maintenance 부담 → 단순 규칙부터 시작 (nearest warehouse first)
- 작업자 실수 (잘못된 SKU 픽업) → 바코드 스캔 의무화
- 분할 배송 시 사용자 혼란 → UI 에서 "2 packages" 명시
- 국가 간 배송은 통관·관세 (`Incoterms`: DDP vs DDU)

**DDD 매핑**:
- **Aggregate Root**: `Shipment`, `Warehouse`
- **Entity**: `PickTask`, `PackTask`
- **Value Object**: `TrackingNumber`, `BoxDimensions`, `BinLocation`
- **Domain Event**: `PickListGenerated`, `OrderPicked`, `OrderPacked`, `ShipmentDispatched`

**Kotlin 예제**:
```kotlin
class Shipment(
    val id: ShipmentId,
    val orderId: OrderId,
    val warehouseId: WarehouseId,
    val items: List<ShipmentItem>,
    private var status: ShipmentStatus = ShipmentStatus.Pending,
    private var trackingNo: TrackingNumber? = null,
) {
    fun startPicking(workerId: WorkerId): PickList {
        require(status == ShipmentStatus.Pending)
        status = ShipmentStatus.Picking
        return PickList(
            shipmentId = id,
            workerId = workerId,
            tasks = items
                .map { PickTask(it.sku, it.qty, it.binLocation) }
                .sortedBy { it.binLocation.sortKey() },  // 동선 최적
        )
    }

    fun dispatch(carrier: Carrier, trackingNo: TrackingNumber) {
        require(status == ShipmentStatus.Packed)
        this.trackingNo = trackingNo
        status = ShipmentStatus.Dispatched
    }
}

data class BinLocation(val zone: String, val aisle: Int, val rack: Int, val shelf: Int) {
    fun sortKey() = listOf(zone, aisle.toString().padStart(3, '0'), rack, shelf).joinToString("-")
}
```

**관련 패턴**: [Order State Machine](#order-state-machine), [Inventory Reservation](#inventory-reservation), [Knapsack](../../algorithms/dynamic-programming.md#knapsack), [Domain Event](../ddd-tactical.md)

---

## 8. Returns / RMA (Return Merchandise Authorization) <a id="returns-rma"></a>

**목적**: 사용자가 받은 상품을 반품·교환할 때 사유 분류·환불 정책·창고 복원 흐름을 표준화하여, CS 부담과 재고 손실을 동시에 관리합니다.

**메커니즘**:
- **RMA Number 발급** — 반품 신청 시 고유 번호 발급 → 송장 부착 + tracking
- **Return Reason Taxonomy**:
  - 단순 변심 (사용자 부담) — 한국 전자상거래법: 수령 후 7 일 이내
  - 상품 결함 (판매자 부담) — 사진 첨부 의무화
  - 배송 오류 (판매자 부담) — 잘못된 상품 도착
  - 사이즈 / 색상 불일치 — 교환 우선 제안
- **Refund vs Store Credit** — 현금 환불 vs 적립금. 적립금은 미사용 시 ledger 부채로 남음 (`#loyalty-rewards` 참조)
- **Partial Return** — 주문 전체가 아닌 일부 SKU 만 반품
- **Restocking Fee** — 단순 변심 시 10~20% 차감 (정책에 따라). 사전 고지 의무
- **재입고 가능성 판단**:
  - 미개봉 새것 → re-stock as available
  - 개봉 / 사용 흔적 → second-hand 매대 또는 폐기
  - 결함 → 공급사 반품 또는 폐기
- **환불 처리**: 원 결제수단 환불 (Stripe `Refund`), 부분환불, 환불 SLA 명시 (영업일 3~5)

**장점**:
- 명확한 정책으로 CS dispute 감소
- 반품 데이터 분석 → 품질 issue 발견 (특정 SKU 반품률 ↑ → 공급사 피드백)
- 환불 SLA 준수로 신뢰 ↑

**단점·주의**:
- 결함 사진 첨부 의무화 — 모바일 업로드 UX 필수
- 일부 카테고리 (식품 / 위생용품) 는 반품 불가 — 사전 고지 + UI 명시
- 한국 전자상거래법 7 일 청약철회권 — 사업자가 임의로 단축 불가
- 반품 사기 (사용 후 환불) — 사진 / 박스 상태 검수 절차 필요

**DDD 매핑**:
- **Aggregate Root**: `ReturnRequest` (RMA)
- **Entity**: `ReturnItem`, `Refund`
- **Value Object**: `RmaId`, `ReturnReason`, `RefundAmount`
- **Domain Event**: `ReturnRequested`, `ReturnApproved`, `RefundIssued`, `ItemRestocked`

**Kotlin 예제**:
```kotlin
sealed interface ReturnReason {
    val refundResponsibility: Responsibility
    object CustomerRemorse : ReturnReason { override val refundResponsibility = Responsibility.Customer }
    object DefectiveItem : ReturnReason { override val refundResponsibility = Responsibility.Merchant }
    object WrongItemShipped : ReturnReason { override val refundResponsibility = Responsibility.Merchant }
    data class SizeMismatch(val preferred: String) : ReturnReason {
        override val refundResponsibility = Responsibility.Customer
    }
}

class ReturnRequest(
    val id: RmaId,
    val orderId: OrderId,
    val items: List<ReturnItem>,
    val reason: ReturnReason,
    private var status: ReturnStatus = ReturnStatus.Requested,
) {
    fun approve(refundMethod: RefundMethod): Refund {
        require(status == ReturnStatus.Requested)
        status = ReturnStatus.Approved
        val amount = items.sumOf { it.refundAmount }
        val fee = if (reason.refundResponsibility == Responsibility.Customer)
            amount * BigDecimal("0.10") else Money.ZERO_KRW
        return Refund(orderId, amount - fee, refundMethod)
    }

    fun receiveItems(condition: ItemCondition) {
        require(status == ReturnStatus.Approved)
        status = when (condition) {
            ItemCondition.Pristine -> ReturnStatus.RestockedNew
            ItemCondition.Opened -> ReturnStatus.RestockedSecondHand
            ItemCondition.Damaged -> ReturnStatus.Discarded
        }
    }
}
```

**관련 패턴**: [Order State Machine](#order-state-machine), [Refund (fintech)](./fintech.md), [Loyalty / Store Credit](#loyalty-rewards), [Domain Event](../ddd-tactical.md)

---

## 9. Search & Discovery <a id="search-discovery"></a>

**목적**: 수십만~수억 건의 상품 카탈로그를 키워드·facet·정렬·필터로 빠르게 탐색하면서, 오타 허용·동의어·자동완성을 통해 사용자 의도를 보완합니다.

**메커니즘**:
- **검색 엔진**: Elasticsearch / OpenSearch / Algolia / Meilisearch / Typesense
- **인덱싱 전략**:
  - Product 단위 vs Variant 단위 — variant 단위는 정확하나 인덱스 크기 ↑
  - 색인 갱신: (a) sync (저지연 필수, ES `refresh_interval=1s`), (b) async outbox + queue (느슨하지만 안정)
- **Faceted Search** — 카테고리 / 브랜드 / 가격 / 평점 등 다차원 필터. ES `aggregations` 활용
- **Autocomplete** — 입력 중 제안. (a) edge n-gram 토크나이저, (b) completion suggester, (c) 별도 자동완성 인덱스
- **Synonym** — "휴대폰" = "스마트폰" = "핸드폰". synonym dictionary 운영 필요 (한국어 형태소 분석 + 사용자 검색 로그 분석)
- **Typo Tolerance** — Levenshtein distance ≤ 2 (Algolia 기본). ES 는 `fuzzy` query 또는 phonetic analyzer
- **Ranking**:
  - 텍스트 매칭 (BM25)
  - 인기도 (판매량, 클릭률, 평점) — boost
  - 개인화 (사용자 과거 행동) — 별도 ranking 모델 (`#recommendation-personalization` 참조)
  - 비즈니스 부스트 (광고 / promoted listing)
- **Zero-result 처리** — 빈 결과 시 "did you mean" + 유사 카테고리 제안

**장점**:
- 카테고리 탐색만으로 도달 어려운 상품을 키워드로 즉시 접근
- facet 필터로 사용자 의사결정 단축 (가격대 / 색상 빠르게 좁힘)
- 검색 로그 → 트렌드 / 상품 기획 데이터

**단점·주의**:
- 검색 엔진 운영 비용 (메모리 ↑, 인덱스 동기화)
- "Catalog DB" 와 "Search Index" 의 일관성 (eventually consistent) → UI 에 캐싱 안내
- 다국어 — 한국어 형태소 분석기 (nori, mecab-ko) 별도 튜닝
- 동의어 사전은 유지보수 노동 — 검색 로그 기반 반자동화 권장

**DDD 매핑**:
- **Bounded Context**: `Search` (별도) — Catalog 의 read model
- **Value Object**: `SearchQuery`, `Facet`, `RankingSignal`
- **Domain Event**: `ProductIndexed`, `SearchPerformed` (분석용)

**Kotlin 예제**:
```kotlin
data class SearchQuery(
    val keyword: String?,
    val facets: Map<String, List<String>> = emptyMap(),  // brand=[apple,samsung]
    val priceRange: ClosedRange<Money>? = null,
    val sort: SortOrder = SortOrder.Relevance,
    val page: Int = 1,
    val pageSize: Int = 20,
)

interface ProductSearchEngine {
    fun search(q: SearchQuery): SearchResult
    fun autocomplete(prefix: String, limit: Int = 10): List<Suggestion>
}

data class SearchResult(
    val products: List<ProductSummary>,
    val totalHits: Long,
    val facetCounts: Map<String, Map<String, Long>>,  // brand -> {apple: 23, samsung: 17}
    val didYouMean: String? = null,
)

class ElasticProductSearch(private val client: ElasticsearchClient) : ProductSearchEngine {
    override fun search(q: SearchQuery): SearchResult {
        val req = co.elastic.clients.elasticsearch._types.query_dsl.Query.of { qb ->
            qb.bool { b ->
                q.keyword?.let { kw ->
                    b.must { it.multiMatch { mm -> mm.query(kw).fields("name^3", "description", "brand^2") } }
                }
                q.facets.forEach { (field, values) ->
                    b.filter { it.terms { t -> t.field(field).terms { tv -> tv.value(values.map(FieldValue::of)) } } }
                }
                b
            }
        }
        val response = client.search({ s -> s.index("products").query(req).size(q.pageSize) }, ProductDoc::class.java)
        return SearchResult(
            products = response.hits().hits().map { it.source()!!.toSummary() },
            totalHits = response.hits().total()!!.value(),
            facetCounts = emptyMap(),  // aggregations 매핑은 생략
        )
    }
}
```

**관련 패턴**: [Product Catalog](#product-catalog), [Recommendation](#recommendation-personalization), [CQRS](../architectural.md), [Caching](../caching.md)

---

## 10. Recommendation (Personalization) <a id="recommendation-personalization"></a>

**목적**: 사용자의 과거 행동·유사 사용자 행동·상품 메타데이터를 결합하여 "당신을 위한" 상품을 추천하여 전환율과 객단가를 높입니다.

**메커니즘**:
- **Collaborative Filtering (CF)**:
  - User-based: "당신과 비슷한 사용자가 산 상품"
  - Item-based: "이 상품을 산 사람이 같이 산 상품" (Amazon classic — "Customers who bought this also bought")
  - Matrix Factorization (SVD, ALS) — 잠재 요인 모델
- **Content-based Filtering** — 사용자 과거 선호 상품의 속성(카테고리, 브랜드)과 유사한 상품
- **Hybrid** — CF + Content. cold start 문제 (신규 사용자/상품) 완화
- **"Frequently Bought Together" (FBT)** — 동일 주문 내 함께 구매된 상품 쌍의 confidence. 장바구니 추가 시 노출
- **Real-time Personalization** — 세션 내 클릭/뷰 기반 즉시 추천 갱신 (`session-based recommendation`)
- **Re-ranking 모델** — 후보군 추출 (CF/CBF) → 사용자 context 로 reorder (LambdaMART, DLRM)
- **A/B Testing** — 추천 알고리즘 비교 (CTR / 전환율 / GMV)
- **Cold Start 전략**: 신규 사용자 → 인기 상품 / 카테고리 기반 popular, 신규 상품 → 속성 매칭

**장점**:
- 전환율 +10~30% (업계 평균)
- 사용자 engagement / retention ↑
- 롱테일 상품 노출 ↑

**단점·주의**:
- 필터 버블 — 사용자 시야 좁아짐 → diversity / serendipity 균형 필요
- 신선도 — 어제 산 상품을 또 추천하는 실수 (recently purchased filter 필수)
- 개인정보 — GDPR / 한국 PIPA. 추천 데이터 보관·삭제 정책
- 어린이 보호 — 청소년에게 부적절한 상품 필터링

**DDD 매핑**:
- **Bounded Context**: `Recommendation` (별도)
- **Value Object**: `RecommendationContext`, `RecommendationScore`
- **Domain Event**: `RecommendationServed`, `RecommendationClicked`, `RecommendationConverted`

**Kotlin 예제**:
```kotlin
data class RecommendationContext(
    val userId: CustomerId?,
    val currentProductId: ProductId? = null,  // PDP 추천용
    val currentCart: List<ProductId> = emptyList(),  // FBT 용
    val sessionEvents: List<SessionEvent> = emptyList(),  // 실시간
)

interface RecommendationEngine {
    fun recommend(ctx: RecommendationContext, slot: Slot, limit: Int = 10): List<Recommendation>
}

enum class Slot {
    HOME_FOR_YOU,           // 홈 "당신을 위한"
    PDP_SIMILAR,            // 상품 상세 "유사 상품"
    PDP_FBT,                // 상품 상세 "함께 구매"
    CART_FBT,               // 장바구니 "함께 구매"
    CHECKOUT_UPSELL,        // 결제 직전 업셀
    POST_PURCHASE,          // 구매 후 "다음에 살 것"
}

class HybridRecommender(
    private val cfEngine: CollaborativeFiltering,
    private val cbEngine: ContentBased,
    private val popularEngine: PopularityRanker,
) : RecommendationEngine {
    override fun recommend(ctx: RecommendationContext, slot: Slot, limit: Int): List<Recommendation> {
        val userId = ctx.userId
        val candidates = if (userId == null || cfEngine.coldStart(userId)) {
            popularEngine.topN(limit * 3)  // cold start
        } else {
            (cfEngine.recommend(userId, limit * 2) + cbEngine.recommend(userId, limit * 2)).distinct()
        }
        return candidates
            .filterNot { it.productId in ctx.currentCart }  // 이미 cart 에 있으면 제외
            .take(limit)
    }
}
```

**관련 패턴**: [Search & Discovery](#search-discovery), [Cart Aggregate](#cart-aggregate), [A/B Testing](../testing.md), [Caching](../caching.md)

---

## 11. Marketplace Multi-Seller <a id="marketplace-multi-seller"></a>

**목적**: 다수의 vendor 가 상품을 등록·판매·배송하는 marketplace 에서 onboarding·수수료·정산·분쟁을 관리합니다.

**메커니즘**:
- **Vendor Onboarding** — 사업자 등록·통신판매업 신고·KYC. 한국은 통신판매업 신고증, 미국은 EIN, 글로벌은 W-8/W-9. 자동화 가능한 부분은 Stripe Connect 등 활용
- **Catalog Ownership** — vendor 별 상품 등록 또는 카탈로그 공유 (한 상품을 여러 vendor 가 판매 — Amazon style). 후자는 buy box 알고리즘 필요
- **Commission Split**:
  - Flat percentage (e.g. 10%)
  - Category-based (전자제품 7%, 의류 15%)
  - Tiered (월 판매액 ↑ → 수수료 ↓)
- **Payout Schedule** — 정산 주기 (주 1회 / 월 2회 / 즉시 — Stripe Express). 환불·반품 dispute 가능성 때문에 hold period (7~14 일) 두는 게 일반적
- **Marketplace Liability** — 일부 국가는 marketplace 가 판매자 대신 부가세 징수·신고 의무 (EU Marketplace Facilitator, 한국은 vendor 책임)
- **Dispute Resolution** — 사용자 ↔ vendor 분쟁 시 marketplace 가 중재. 증거 (사진 / 송장 / 채팅 로그) 수집 → 환불 결정
- **Rating / Review** — vendor 평점 시스템. 평점 낮은 vendor 노출 ↓

**장점**:
- 직접 매입 없이 카탈로그 확장 (asset-light)
- vendor 간 경쟁으로 가격·품질 ↑
- 글로벌 확장 시 현지 vendor 확보 용이

**단점·주의**:
- Trust & Safety 비용 ↑ — 가짜 상품 / 사기 vendor
- 정산·세무 복잡 (vendor 별 ledger, 다국가 세금)
- Buy box 알고리즘은 공정성 / 투명성 논란 가능
- vendor 와의 계약서·약관 정합성 (한국 표준약관 활용)

**DDD 매핑**:
- **Aggregate Root**: `Vendor`, `VendorPayout`
- **Entity**: `VendorListing` (vendor 의 상품 등록)
- **Value Object**: `CommissionRate`, `PayoutSchedule`, `KycStatus`
- **Domain Event**: `VendorOnboarded`, `CommissionCalculated`, `PayoutInitiated`, `DisputeRaised`

**Kotlin 예제**:
```kotlin
class Vendor(
    val id: VendorId,
    val businessName: String,
    private var kycStatus: KycStatus = KycStatus.Pending,
    private var commissionRate: CommissionRate = CommissionRate.Flat(BigDecimal("0.10")),
    private val payouts: MutableList<VendorPayout> = mutableListOf(),
) {
    fun completeKyc(verified: KycVerification) {
        require(kycStatus == KycStatus.Pending)
        kycStatus = if (verified.passed) KycStatus.Approved else KycStatus.Rejected(verified.reason)
    }

    fun canSell(): Boolean = kycStatus is KycStatus.Approved

    fun computeCommission(orderTotal: Money, category: CategoryId): Money = when (val r = commissionRate) {
        is CommissionRate.Flat -> orderTotal * r.pct
        is CommissionRate.CategoryBased -> orderTotal * r.rateFor(category)
        is CommissionRate.Tiered -> orderTotal * r.rateFor(monthlySalesSoFar())
    }

    private fun monthlySalesSoFar(): Money = payouts
        .filter { it.period.contains(LocalDate.now()) }
        .map { it.grossAmount }
        .reduceOrNull(Money::plus) ?: Money.ZERO_KRW
}

sealed interface CommissionRate {
    data class Flat(val pct: BigDecimal) : CommissionRate
    data class CategoryBased(val map: Map<CategoryId, BigDecimal>) : CommissionRate {
        fun rateFor(c: CategoryId) = map[c] ?: BigDecimal("0.10")
    }
    data class Tiered(val tiers: List<Pair<Money, BigDecimal>>) : CommissionRate {
        fun rateFor(sales: Money): BigDecimal = tiers.lastOrNull { sales >= it.first }?.second ?: BigDecimal("0.15")
    }
}
```

**관련 패턴**: [Bounded Context](../ddd-tactical.md), [Saga (Payout)](../distributed.md), [Pricing & Promotion](#pricing-promotion-engine), [Audit Log](../observability.md)

---

## 12. Loyalty / Rewards Program <a id="loyalty-rewards"></a>

**목적**: 사용자의 구매·활동에 대해 포인트·등급·혜택을 제공하여 retention 과 LTV(Lifetime Value) 를 높이면서, 회계상 부채로 관리합니다.

**메커니즘**:
- **Points Accrual** — 구매 금액의 일정 비율 적립 (e.g. 1%). 단순 비율 외에 카테고리 boost / 이벤트 boost
- **Tier System** — Bronze / Silver / Gold / Platinum 등 등급. 누적 구매액 또는 연간 구매액으로 산정. 등급별 혜택: 적립률 ↑, 무료 배송, 전용 쿠폰
- **Burn (Redemption)** — 포인트로 결제 (`1 P = 1 KRW`), 상품 교환, 쿠폰 전환. 최소 사용 단위 (e.g. 1000 P 부터)
- **Burn Rate 모니터링** — 발행 대비 사용 비율. 너무 낮으면 매력 부족, 너무 높으면 마진 압박
- **Expiration** — 미사용 포인트 만료 (한국 표준 5 년). 만료 30 / 7 일 전 알림 의무
- **Liability Accounting** — 발행된 포인트는 회계상 부채 (IFRS 15 — 별도 수행의무). 사용 추정치 (breakage) 를 차감한 순부채로 인식. 외부감사 대상 기업은 actuarial 추정 필요
- **Fraud 방지** — 다중 계정 가입·취소 후 재가입으로 가입 보너스 반복 수령 차단
- **회계 처리**:
  - 적립 시: `매출` 일부를 `포인트 부채` 로 인식
  - 사용 시: `포인트 부채` 감소 + `매출` 인식
  - 만료 시: `포인트 부채` 감소 + `기타수익` 인식

**장점**:
- Retention / repeat purchase rate ↑
- 사용자 데이터 수집 동의 인센티브
- tier 시스템으로 high-value customer 식별

**단점·주의**:
- Liability 누적 — 회계 관리 필수. 미사용 포인트 = 미실현 부채
- 사용자 만료 정책에 민감 — 일방적 단축은 분쟁 / 평판 손상
- "포인트 인플레이션" — 과도한 적립률로 마진 잠식
- 한국 — 5 년 미사용 시 만료 가능하나 사용 약관 명시 + 사전 고지 필수

**DDD 매핑**:
- **Aggregate Root**: `LoyaltyAccount` (per customer), `PointsLedger`
- **Entity**: `PointTransaction`
- **Value Object**: `Points`, `Tier`, `EarnRate`
- **Domain Event**: `PointsEarned`, `PointsRedeemed`, `PointsExpired`, `TierUpgraded`, `TierDowngraded`

**Kotlin 예제**:
```kotlin
@JvmInline value class Points(val value: Long) {
    operator fun plus(other: Points) = Points(value + other.value)
    operator fun minus(other: Points) = Points(value - other.value)
    operator fun compareTo(other: Points) = value.compareTo(other.value)
    companion object { val ZERO = Points(0) }
}

enum class Tier(val earnRate: BigDecimal, val annualThreshold: Money) {
    BRONZE(BigDecimal("0.01"), Money(BigDecimal.ZERO, KRW)),
    SILVER(BigDecimal("0.02"), Money(BigDecimal(500_000), KRW)),
    GOLD(BigDecimal("0.03"), Money(BigDecimal(2_000_000), KRW)),
    PLATINUM(BigDecimal("0.05"), Money(BigDecimal(10_000_000), KRW)),
}

class LoyaltyAccount(
    val id: LoyaltyAccountId,
    val customerId: CustomerId,
    private val transactions: MutableList<PointTransaction> = mutableListOf(),
    private var tier: Tier = Tier.BRONZE,
) {
    fun balance(): Points = transactions
        .filterNot { it.isExpired() }
        .fold(Points.ZERO) { acc, t -> acc + t.signedAmount() }

    fun earn(fromOrder: OrderId, orderTotal: Money) {
        val amount = Points((orderTotal.amount * tier.earnRate).toLong())
        transactions += PointTransaction.Earned(
            id = TxId.new(),
            amount = amount,
            sourceOrder = fromOrder,
            occurredAt = Instant.now(),
            expiresAt = Instant.now().plus(365 * 5, DAYS),  // 5 년 만료
        )
    }

    fun redeem(amount: Points, forOrder: OrderId) {
        require(balance() >= amount) { "insufficient points" }
        transactions += PointTransaction.Redeemed(
            id = TxId.new(),
            amount = amount,
            sourceOrder = forOrder,
            occurredAt = Instant.now(),
        )
    }

    fun recomputeTier(annualSpend: Money) {
        val newTier = Tier.values().lastOrNull { annualSpend >= it.annualThreshold } ?: Tier.BRONZE
        tier = newTier
    }
}

sealed interface PointTransaction {
    val id: TxId
    val amount: Points
    val occurredAt: Instant
    fun signedAmount(): Points
    fun isExpired(): Boolean = false

    data class Earned(
        override val id: TxId, override val amount: Points,
        val sourceOrder: OrderId, override val occurredAt: Instant,
        val expiresAt: Instant,
    ) : PointTransaction {
        override fun signedAmount() = amount
        override fun isExpired() = Instant.now().isAfter(expiresAt)
    }
    data class Redeemed(
        override val id: TxId, override val amount: Points,
        val sourceOrder: OrderId, override val occurredAt: Instant,
    ) : PointTransaction {
        override fun signedAmount() = Points(-amount.value)
    }
}
```

**관련 패턴**: [Pricing & Promotion](#pricing-promotion-engine), [Returns / RMA](#returns-rma), [Event Sourcing (Ledger)](../architectural.md), [Audit Log](../observability.md)

---
