# DDD 전략 패턴 (Strategic Domain-Driven Design)

Eric Evans *Domain-Driven Design: Tackling Complexity in the Heart of Software* (2003) Part IV "Strategic Design" + Vaughn Vernon *Implementing Domain-Driven Design* (2013) Part I 의 12 핵심 패턴. [`ddd-tactical.md`](ddd-tactical.md) (Entity / Aggregate / Value Object 등) 의 짝.

**원전·표준 참고**:
- Eric Evans — *Domain-Driven Design* (Addison-Wesley, 2003)
- Vaughn Vernon — *Implementing Domain-Driven Design* (2013)
- Vaughn Vernon — *Domain-Driven Design Distilled* (2016)
- Alberto Brandolini — *Introducing EventStorming* (LeanPub, 2021)
- Nick Tune blog — Strategic DDD patterns

**핵심 원칙**:
- **언어 일치** — 도메인 전문가 언어 = 코드 = 문서
- **경계 의식** — 같은 용어가 다른 컨텍스트에서 다른 의미를 가짐을 명시
- **투자 차등** — Core 에만 정성, Generic 은 사거나 외주

**Context Map 9 관계 표**:

| 관계 | 권력 구조 | 사용처 |
|------|----------|--------|
| Customer-Supplier | 평등 협상 | 두 팀 같은 회사 |
| Conformist | 하위 따름 | 외부 SaaS 의존 |
| Anti-Corruption Layer | 격리 | 레거시 통합 |
| Open Host Service | 공급자 | 다수 클라이언트 |
| Published Language | 표준화 | 산업 표준 (FHIR/EDI) |
| Shared Kernel | 공유 | 작은 핵심 |
| Partnership | 운명 공동체 | 양쪽 동시 변경 |
| Separate Ways | 분리 | 통합 가치 < 비용 |
| Big Ball of Mud | 통합 실패 | 안티패턴 (회피) |

**관련 카탈로그**:
- [ddd-tactical.md](ddd-tactical.md) — Entity / Aggregate / Domain Event 등 (전술)
- [anti-patterns.md](anti-patterns.md) — Big Ball of Mud
- [`../principles/evolutionary-arch.md`](../principles/evolutionary-arch.md) — Quanta ↔ Bounded Context

---

<a id="ubiquitous-language"></a>
## 1. Ubiquitous Language (편재 언어)

**정의**: Eric Evans Blue Book Chapter 2 의 토대 패턴. 도메인 전문가와 개발자가 공유하는 단일 어휘 체계로, 회의 · 화이트보드 · 문서 · 코드 모두에서 동일한 용어를 동일한 의미로 사용한다. "코드가 곧 모델이며, 모델이 곧 대화" 라는 DDD 의 기본 신조.

**메커니즘 / 관계 구조**:
- 도메인 전문가의 단어를 직접 클래스 · 메서드 · 변수명으로 사용
- 모호한 단어는 즉시 명시적 정의로 교체 ("주문" → "Pending Order" / "Confirmed Order")
- 용어집(glossary) 을 살아있는 문서로 유지, EventStorming · 도메인 워크숍에서 도출
- 모델 변경 = 언어 변경. 언어 변경 = 코드 변경. 세 가지가 항상 동기화
- Bounded Context 내부에서만 일관성 유지 (다른 context 에선 같은 단어가 다른 의미 가능)

**장점**:
- 번역 비용 제거 — 전문가가 "discount" 라고 말한 것이 코드에 그대로 `Discount` 클래스로 존재
- 요구사항 누수 감소 — 의미 전달 단계가 짧음
- 신규 팀원 온보딩 가속 — 도메인 문서 = 코드 구조
- 리팩토링 시 도메인 의도 보존

**단점·주의**:
- 도메인 전문가의 적극 참여 필수 — 없으면 개발자가 추측한 언어가 굳어버림
- 한국어 도메인을 영어 코드로 옮길 때 의미 손실 발생 가능 — KR / EN 글로서리 병기 권장
- 컨텍스트 경계를 흐리면 한 단어가 너무 많은 의미를 떠안음 ("Customer" 가 영업 / 결제 / 배송 모두)

**활용 예시**:
- 보험 도메인: "Claim", "Underwriting", "Coverage" 를 코드에 그대로 노출
- 항공사 도메인: "Itinerary" vs "Booking" vs "Ticket" 의 미묘한 차이를 코드에서 구분
- 의료: 의사가 말하는 "Encounter" 를 그대로 `Encounter` Aggregate 로

**Kotlin / pseudo-code 예제**:
```kotlin
// BAD — 개발자 추상 용어
class Item(val price: Double, val qty: Int) {
    fun process() { /* ... */ }
}

// GOOD — 도메인 전문가 언어 그대로
class LineItem(val unitPrice: Money, val orderedQuantity: Quantity) {
    fun isBackOrdered(): Boolean = orderedQuantity > stockOnHand()
    fun applyPromotion(promotion: Promotion): LineItem { /* ... */ }
}

// 글로서리 발췌
// - LineItem: 주문서 한 줄. SKU · 단가 · 수량의 묶음
// - BackOrder: 재고 부족으로 입고 대기 중인 상태
// - Promotion: 가격 / 수량 / 묶음에 적용되는 할인 정책
```

**관련 패턴**: [Bounded Context](#bounded-context-strategic), [Context Map](#context-map), [Entity](ddd-tactical.md#1-entity), [Value Object](ddd-tactical.md#2-value-object)

---

<a id="subdomain-classification"></a>
## 2. Subdomain 분류 (Core / Supporting / Generic)

**정의**: Evans Blue Book Chapter 15 · Vernon IDDD Chapter 2. 비즈니스 도메인을 세 가지 하위 영역으로 분류하여 투자 우선순위를 결정하는 패턴. 모든 코드가 동등한 가치를 갖지 않음을 명시적으로 인정한다.

**메커니즘 / 관계 구조**:

```
┌──────────────────────────────────────────────┐
│              Business Domain                 │
├──────────────┬──────────────┬────────────────┤
│ Core         │ Supporting   │ Generic        │
│ Subdomain    │ Subdomain    │ Subdomain      │
├──────────────┼──────────────┼────────────────┤
│ 경쟁 우위    │ 필수지만     │ 어디나 동일    │
│ 차별화       │ 차별화 X     │ 범용 기능      │
│ 직접 구현    │ 직접 또는    │ COTS / SaaS    │
│ 최고 개발자  │ 외주 가능    │ 구매 권장      │
└──────────────┴──────────────┴────────────────┘
```

- **Core Subdomain** — 회사 존재 이유. 경쟁사와의 차별점. DDD 의 모든 정교한 패턴을 여기에 집중
- **Supporting Subdomain** — Core 를 지원하지만 자체 차별점은 없음. 단순 구현으로 충분
- **Generic Subdomain** — 인증 · 결제 · 알림 등 산업 공통. SaaS / 오픈소스 / 외주 우선

**장점**:
- 한정된 시니어 개발자 자원의 합리적 분배
- "모든 곳에 Clean Architecture" 같은 과잉 설계 회피
- Buy vs Build 의사결정의 명시적 기준
- 인수합병 · 매각 전략 수립의 기초

**단점·주의**:
- 분류는 시간에 따라 변함 — 어제의 Core 가 오늘의 Generic (예: 검색 엔진)
- 정치적 갈등 발생 — 모두가 자기 영역을 Core 라 주장
- Generic 으로 분류한 SaaS 가 비즈니스 핵심으로 변질되면 lock-in 위험

**활용 예시**:
- Netflix: 추천 알고리즘 (Core) / 콘텐츠 메타데이터 관리 (Supporting) / 결제 (Generic — Stripe)
- 은행: 리스크 평가 (Core) / 고객 관리 (Supporting) / 메일 발송 (Generic)
- 우버: 매칭 알고리즘 · 동적 가격 (Core) / 기사 등록 (Supporting) / 지도 (Generic — Google Maps)

**Kotlin / pseudo-code 예제**:
```kotlin
// CORE — 정교한 DDD 패턴 총동원
package com.acme.pricing  // 다이나믹 프라이싱 = 경쟁 우위
class Pricing(
    private val demandModel: DemandModel,
    private val competitorIntelligence: CompetitorIntelligence,
) {
    fun quote(item: Sku, context: MarketContext): Quote = /* 복잡한 도메인 로직 */
}

// SUPPORTING — 단순 CRUD 로도 충분
package com.acme.catalog
class Product(val id: ProductId, val name: String, val description: String)

// GENERIC — 외부 SaaS 호출만
package com.acme.notification
class NotificationService(private val sendgrid: SendGridClient) {
    fun send(to: Email, template: TemplateId) = sendgrid.send(to, template)
}
```

**관련 패턴**: [Bounded Context](#bounded-context-strategic), [Context Map](#context-map), [Separate Ways](#separate-ways)

---

<a id="bounded-context-strategic"></a>
## 3. Bounded Context (전략적 관점)

**정의**: Evans Blue Book Chapter 14 의 핵심 패턴. 특정 도메인 모델과 ubiquitous language 가 일관되게 적용되는 명시적 경계. [`ddd-tactical.md` 의 Bounded Context](ddd-tactical.md#8-bounded-context) 가 모델 · 모듈 측면이라면, 전략 관점은 **팀 · 조직 · 통합 협상** 의 단위로 본다.

**메커니즘 / 관계 구조**:
- 하나의 BC = 하나의 모델 = 하나의 언어 = (이상적으로) 하나의 팀
- BC 간 통신은 명시적 통합 패턴 ([Context Map](#context-map) 의 9 관계 중 하나) 으로
- 같은 회사 안에서도 BC 마다 다른 기술 스택 · 다른 DB · 다른 배포 주기 가능
- Conway's Law 의 의도적 활용 — 팀 구조와 BC 경계를 정렬
- 마이크로서비스 분해의 1차 단위 (단, BC ≠ 마이크로서비스. BC 가 더 큰 개념)

**장점**:
- 모델 단순화 — "Customer" 가 영업 · 결제 · 배송 모두를 떠안지 않음
- 팀 자율성 확보 — 다른 BC 의 변경이 우리 코드에 영향 없음
- 마이크로서비스 분해 기준 제공 (Sam Newman *Building Microservices*)
- Polyglot persistence 정당화 — BC 마다 최적 DB 선택

**단점·주의**:
- BC 경계 설계 실패 = 분산 모놀리스 (서비스는 분리됐는데 의존성은 그대로)
- 모든 BC 를 분리하려는 욕망 → "모듈 폭증" → 통합 비용 폭발
- BC 간 트랜잭션 = eventual consistency. 강한 일관성 요구되는 영역엔 부적합
- 작은 회사에선 모듈러 모놀리스 (한 코드베이스 안의 BC) 가 더 적합

**활용 예시**:
- 전자상거래: Sales / Pricing / Inventory / Shipping / Billing — 5 개 BC 가 같은 "Order" 개념을 각자의 모델로
- 의료: Patient (등록) / Encounter (진료) / Billing (청구) — "Patient" 가 BC 마다 다른 속성
- 보험: Policy Issuance / Underwriting / Claims — 위험 평가 vs 사고 처리는 완전히 다른 모델

**Context Map 다이어그램**:
```
┌────────────┐         ┌─────────────┐
│   Sales    │────────>│   Billing   │
│  Context   │ U     D │   Context   │
└────────────┘         └─────────────┘
      │ D                     │ U
      │                       │
      v                       v
┌────────────┐         ┌─────────────┐
│ Inventory  │<───ACL──│  Legacy     │
│  Context   │         │  ERP        │
└────────────┘         └─────────────┘

U = Upstream, D = Downstream, ACL = Anti-Corruption Layer
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Sales BC — Customer 는 "구매자"
package sales.domain
class Customer(
    val id: CustomerId,
    val name: String,
    val preferredPaymentMethod: PaymentMethod,
    val purchaseHistory: List<OrderId>,
)

// Support BC — Customer 는 "지원 대상"
package support.domain
class Customer(
    val id: CustomerId,
    val tier: SupportTier,
    val openTickets: List<TicketId>,
    val satisfactionScore: Score,
)

// 두 BC 는 같은 "고객" 을 가리키지만, 모델은 완전히 다름
// 통합은 CustomerId 동기화 + 이벤트 (CustomerRegistered) 로
```

**관련 패턴**: [Context Map](#context-map), [Ubiquitous Language](#ubiquitous-language), [Anti-Corruption Layer (전략)](#anti-corruption-layer-strategic), [BC (전술)](ddd-tactical.md#8-bounded-context)

---

<a id="context-map"></a>
## 4. Context Map

**정의**: Evans Blue Book Chapter 14 · Vernon IDDD Chapter 3. 시스템의 모든 Bounded Context 와 그 사이 관계를 시각화한 다이어그램 · 문서. 통합 전략을 의식적으로 선택하기 위한 도구.

**메커니즘 / 관계 구조**:
- 각 BC 는 박스로, 관계는 화살표 + 패턴명 (Customer-Supplier / Conformist / ACL / OHS / Published Language / Shared Kernel / Partnership / Separate Ways)
- 화살표 방향 = upstream(U) → downstream(D). Upstream 변경은 downstream 에 전파됨
- 권력 관계 표시 — 누가 누구의 일정을 좌우하는가
- 살아있는 문서로 유지 — 새 통합이 생기면 즉시 갱신
- EventStorming · Domain Storytelling 의 산출물로 자주 만들어짐

**장점**:
- 통합 패턴이 무의식적 결정에서 명시적 선택으로 전환
- Conway's Law 와 조직 구조 정합성 검토 가능
- 변경 영향도 추정 — upstream 변경 시 영향받을 downstream 목록
- 신규 팀원이 시스템 전체 구조를 한 페이지로 파악

**단점·주의**:
- 문서로만 머무르고 코드에 반영 안 되면 무의미 (architecture-as-code, ADR 병행 필요)
- 큰 조직 (50+ BC) 에선 가독성 한계 — 계층적 분할 필요
- 정치적 도구로 변질 위험 — "우리 BC 가 upstream" 다툼

**Context Map 9 관계 표** (요약):

| 관계 | 권력 구조 | 사용처 |
|------|----------|--------|
| Customer-Supplier | 평등 협상 | 두 팀 같은 회사 |
| Conformist | 하위 따름 | 외부 SaaS 의존 |
| Anti-Corruption Layer | 격리 | 레거시 통합 |
| Open Host Service | 공급자 | 다수 클라이언트 |
| Published Language | 표준화 | 산업 표준 (FHIR/EDI) |
| Shared Kernel | 공유 | 작은 핵심 |
| Partnership | 운명 공동체 | 양쪽 동시 변경 |
| Separate Ways | 분리 | 통합 가치 < 비용 |
| Big Ball of Mud | 통합 실패 | 안티패턴 (회피) |

**활용 예시**:
- 마이크로서비스 dependency 다이어그램 + 통합 패턴 주석
- 팀 간 API 계약 협상 시 upstream / downstream 식별
- 레거시 → 신규 시스템 마이그레이션 전략 수립 (Strangler Fig)

**Context Map 다이어그램 예시**:
```
                     ┌──────────────┐
                     │   Identity   │ (Open Host Service)
                     │   Provider   │  Published Language: OIDC
                     └──────┬───────┘
                            │ U
                ┌───────────┼───────────┐
                v D         v D         v D
        ┌───────────┐ ┌──────────┐ ┌──────────┐
        │   Sales   │ │ Billing  │ │ Support  │
        │ (Core)    │ │(Support.)│ │(Generic) │
        └─────┬─────┘ └────┬─────┘ └──────────┘
              │ U          │ U
              │ Partnership│
              v            v
        ┌──────────────────────┐
        │   Inventory          │
        │   (Core)             │
        └──────────┬───────────┘
                   │ D
                   │ ACL
                   v
        ┌──────────────────────┐
        │   Legacy ERP         │  (Separate Ways 후보)
        │   (Big Ball of Mud)  │
        └──────────────────────┘
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Context Map 은 본질적으로 문서. 코드는 통합 지점만 표현
// 예: Identity (OHS) → Sales (Conformist)

// Identity BC — Published Language (DTO 공개)
interface IdentityOpenHostApi {
    fun authenticate(token: String): UserDto       // PL: OIDC ID Token
    fun getProfile(userId: UserId): ProfileDto
}

// Sales BC — Conformist (Identity 의 모델을 그대로 수용)
class SalesAuthAdapter(private val identity: IdentityOpenHostApi) {
    fun currentBuyer(token: String): Buyer {
        val user = identity.authenticate(token)
        return Buyer(id = BuyerId(user.id), email = Email(user.email))
    }
}
```

**관련 패턴**: [Bounded Context](#bounded-context-strategic), [Customer-Supplier](#customer-supplier), [Conformist](#conformist), [Open Host Service](#open-host-service)

---

<a id="customer-supplier"></a>
## 5. Customer-Supplier 관계

**정의**: Evans Blue Book Chapter 14. 두 Bounded Context 가 upstream(공급자) - downstream(소비자) 관계에 있되, downstream 의 요구사항이 upstream 의 계획에 반영되는 협상 가능한 관계. 한 회사 내 두 팀의 일반적 통합 패턴.

**메커니즘 / 관계 구조**:
- Upstream 팀이 API · 스키마 · 이벤트를 제공
- Downstream 팀이 요구사항을 제기하면 upstream 의 백로그에 반영
- 양 팀은 정기 회의 (sprint planning · 분기 로드맵) 에서 우선순위 협상
- Downstream 의 통합 테스트가 upstream 의 CI 에 포함됨 ("Consumer-Driven Contract")
- 동일 회사 · 동일 경영진 산하라는 권력 균형이 전제

**장점**:
- Downstream 의 비즈니스 요구가 upstream 에 반영됨 — 다운스트림이 일방적으로 당하지 않음
- 통합 회귀 조기 발견 (CDC 테스트)
- 팀 간 신뢰 형성

**단점·주의**:
- Upstream 팀의 협조 의지 필수. 거부하면 사실상 [Conformist](#conformist) 로 전락
- 협상 비용 증가 — downstream 가 많아질수록 upstream 의 회의 부담
- 권력 비대칭 시 (upstream 이 매출 책임 팀) 협상 형식만 남고 실질은 conformist

**활용 예시**:
- 결제 플랫폼 팀 (upstream) ↔ 다수 상품팀 (downstream)
- ID 플랫폼 (upstream) ↔ 각 서비스 (downstream)
- 데이터 플랫폼 (upstream) ↔ 분석 / ML 팀 (downstream)

**Context Map 다이어그램**:
```
┌──────────────┐  Customer-Supplier  ┌──────────────┐
│  Payment     │<────── (협상) ──────│   Sales      │
│  Platform    │  U                D │   Team       │
│  (Upstream)  │                     │ (Downstream) │
└──────────────┘                     └──────────────┘
        │
        │ CDC tests run in upstream CI
        v
┌──────────────────────────────┐
│  Consumer Contract: Sales    │
│  - POST /payments {orderId}  │
│  - 200: {paymentId, status}  │
└──────────────────────────────┘
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Upstream: Payment Platform
@RestController
class PaymentController {
    @PostMapping("/payments")
    fun createPayment(@RequestBody req: CreatePaymentRequest): PaymentResponse =
        paymentService.create(req).toResponse()
}

// Downstream: Sales — Consumer-Driven Contract test
@PactConsumerTest("payment-platform")
class SalesPaymentContractTest {
    @Pact(consumer = "sales")
    fun pact(builder: PactDslWithProvider): RequestResponsePact = builder
        .uponReceiving("create payment for order")
        .path("/payments").method("POST")
        .body(""" {"orderId":"O-1","amount":1000} """)
        .willRespondWith().status(200)
        .body(""" {"paymentId":"P-1","status":"PENDING"} """)
        .toPact()
}
// 이 계약이 Payment Platform 의 CI 에서 검증되어야 customer-supplier 성립
```

**관련 패턴**: [Context Map](#context-map), [Conformist](#conformist), [Open Host Service](#open-host-service), [Published Language](#published-language)

---

<a id="conformist"></a>
## 6. Conformist 관계

**정의**: Evans Blue Book Chapter 14. Downstream 팀이 upstream 의 모델을 그대로 받아들이고 자기 모델로 변환하지 않는 통합 패턴. 협상력이 없거나 협상이 부가가치를 만들지 못할 때의 합리적 선택.

**메커니즘 / 관계 구조**:
- Upstream 의 DTO · 용어 · 데이터 구조를 downstream 코드에 그대로 사용
- 변환 layer 없음 — [ACL](#anti-corruption-layer-strategic) 과 정반대
- Upstream 의 변경이 downstream 에 직접 전파
- Upstream 이 외부 SaaS / 대형 플랫폼 / 표준 규격일 때 자연스러움
- "공급자가 우리를 위해 변경하지 않을 것을 받아들임" 이 핵심 인정

**장점**:
- 변환 코드 · 이중 모델 유지 비용 제로
- 빠른 통합 — 외부 SaaS 통합 시 며칠 만에 완료
- 단순성 — 가장 적은 코드량

**단점·주의**:
- Upstream 의 어휘 · 개념이 우리 ubiquitous language 를 오염시킴
- Upstream 변경 시 우리 코드 광범위 수정 (테스트 · 도메인 로직까지)
- Vendor lock-in — upstream 교체 시 사실상 재작성
- Core Subdomain 에 적용하면 차별화 불가 — 반드시 Generic / Supporting 에만

**활용 예시**:
- Stripe API 통합 — Stripe 의 `Charge` · `Customer` 객체 그대로 사용
- Google Maps SDK — `LatLng` · `Place` 를 우리 도메인 객체로 그대로
- Salesforce CRM 통합 — Salesforce 의 `Account` · `Opportunity` 그대로

**Context Map 다이어그램**:
```
┌──────────────┐  Conformist  ┌──────────────┐
│  External    │              │   Our        │
│  SaaS        │─────U────────│   Service    │
│  (Stripe)    │              │   (D, 그대로)│
└──────────────┘              └──────────────┘
                              협상 없음, 변환 없음
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Conformist: Stripe 의 모델을 그대로 받아들임
import com.stripe.model.Charge
import com.stripe.model.Customer as StripeCustomer

class BillingService(private val stripeClient: StripeClient) {
    // 우리 도메인 코드가 Stripe 의 Charge 객체에 직접 의존
    fun chargeCustomer(stripeCustomer: StripeCustomer, amount: Long): Charge {
        return stripeClient.charges.create(
            mapOf(
                "customer" to stripeCustomer.id,
                "amount"   to amount,
                "currency" to "usd",
            )
        )
        // 반환된 Charge 객체가 우리 서비스 전반에 그대로 흘러다님
    }
}

// 비교: ACL 을 썼다면 우리 도메인 객체 Payment 로 변환했을 것
// → Conformist 는 의도적으로 그 변환을 포기. 변경 비용 < 변환 비용.
```

**관련 패턴**: [Context Map](#context-map), [Customer-Supplier](#customer-supplier), [Anti-Corruption Layer (전략)](#anti-corruption-layer-strategic), [Subdomain 분류](#subdomain-classification)

---

<a id="anti-corruption-layer-strategic"></a>
## 7. Anti-Corruption Layer (전략적 관점)

**정의**: Evans Blue Book Chapter 14. Downstream BC 가 upstream 의 모델을 자기 도메인 언어로 번역하는 격리 layer. [`ddd-tactical.md` 의 ACL](ddd-tactical.md#7-anti-corruption-layer-acl) 이 코드 패턴(Adapter · Facade · Translator 조합) 이라면, **전략 관점은 "팀 간 정치적 결정"** — "우리 도메인 모델의 순도를 보호하기 위해 변환 비용을 감수한다" 는 의식적 선택.

**메커니즘 / 관계 구조**:
- Downstream 측에 변환 layer 배치 — upstream 은 ACL 의 존재를 모름
- Upstream 변경 시 ACL 만 수정 → 도메인 코어 무영향
- 단방향이 일반적 (외부 → 내부). 양방향 시 outbound translator 추가
- [Conformist](#conformist) 와 정반대 선택 — 같은 상황에서 변환 비용을 감수할지 결정
- Strangler Fig 패턴의 핵심 도구 — 레거시를 ACL 뒤에 격리하고 점진적 교체

**장점**:
- Upstream 모델의 침투 차단 — 우리 ubiquitous language 보호
- Upstream 교체 시 ACL 만 재작성, 도메인 로직 무수정
- 레거시 시스템 점진적 교체 (Strangler Fig) 의 토대
- 외부 변경의 폭발 반경 최소화

**단점·주의**:
- 변환 코드 · 이중 모델 유지 비용
- 성능 오버헤드 (모든 호출에 변환 발생)
- Generic Subdomain 에 적용하면 과잉 설계 — Conformist 가 적합
- ACL 자체가 비대해지면 그 자체로 Big Ball of Mud 위험

**활용 예시**:
- 레거시 ERP → 신규 마이크로서비스 마이그레이션 (Strangler Fig)
- Core Subdomain 에서 외부 SaaS 호출 시
- 인수합병 후 두 회사 시스템 통합 중간 단계

**Context Map 다이어그램**:
```
┌──────────────┐         ┌──────┐    ┌──────────────┐
│  Legacy      │   raw   │ ACL  │ 도메인 │   Our      │
│  ERP         │────────>│Trans-│─────>│   Domain   │
│  (Big Ball   │  DTO    │lator │ 객체  │   (보호됨) │
│   of Mud)    │         │      │      │            │
└──────────────┘         └──────┘    └──────────────┘
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Upstream: Legacy ERP — 우리가 통제할 수 없는 모델
data class LegacyCustomerDto(
    val cust_no: String,
    val nm: String,
    val tier_cd: String,   // "01" = Platinum, "02" = Gold, ...
    val crt_dt: String,    // yyyyMMdd
)

// ACL — Translator
class LegacyCustomerAcl(private val legacyApi: LegacyErpApi) {
    fun fetchCustomer(id: CustomerId): Customer {
        val dto = legacyApi.getCustomer(id.value)
        return Customer(
            id = CustomerId(dto.cust_no),
            name = CustomerName(dto.nm),
            tier = mapTier(dto.tier_cd),
            registeredAt = LocalDate.parse(dto.crt_dt, BASIC_ISO_DATE),
        )
    }
    private fun mapTier(code: String): Tier = when (code) {
        "01" -> Tier.Platinum
        "02" -> Tier.Gold
        else -> Tier.Standard
    }
}

// 우리 도메인 — ACL 의 존재를 모름. CustomerId · Tier 만 안다.
class LoyaltyService(private val customers: CustomerRepository) {
    fun computeRewards(id: CustomerId): RewardPoints =
        customers.findById(id).tier.baseRewardRate * /* ... */
}
```

**관련 패턴**: [Context Map](#context-map), [Conformist](#conformist), [ACL (전술)](ddd-tactical.md#7-anti-corruption-layer-acl), [Strangler Fig](legacy-code.md), [Bounded Context](#bounded-context-strategic)

---

<a id="open-host-service"></a>
## 8. Open Host Service (OHS)

**정의**: Evans Blue Book Chapter 14. 다수의 downstream BC 가 접근할 것이 예상되는 upstream BC 가 공통 프로토콜 · API 를 정의하여 모든 클라이언트에 동일하게 제공하는 패턴. "공급자가 통합 비용을 한 번에 부담" 하는 전략.

**메커니즘 / 관계 구조**:
- Upstream 이 명시적 공개 API (REST · gRPC · 이벤트 스트림) 를 정의
- 모든 downstream 은 동일한 API 사용 — 클라이언트별 커스터마이즈 거부
- API 는 [Published Language](#published-language) 와 함께 정의됨
- 버전 관리 · 호환성 정책을 upstream 이 책임짐
- 1:N 통합에서 1:1 협상 비용 (Customer-Supplier × N) 을 피하기 위한 선택

**장점**:
- Upstream 의 통합 비용이 N 개 downstream 에 분산
- 신규 downstream 의 빠른 onboarding (문서만 보고 통합 가능)
- 표준화된 모니터링 · 감사 · 보안
- 외부 파트너 · 공개 API 로 확장 가능

**단점·주의**:
- Upstream API 설계 부담 — 모든 사용 사례를 미리 예측 필요
- API 변경의 폭발 반경 — N 개 downstream 모두에 영향
- 호환성 유지를 위한 버전 누적 (v1, v2, v3 ...) → 기술 부채
- 특수 케이스의 downstream 은 OHS 만으로 부족 → 별도 협의 필요

**활용 예시**:
- AWS / GCP 의 모든 서비스 API — 명확한 OHS 의 예
- 회사 내부 결제 플랫폼이 모든 사업부에 동일 API 제공
- ID 플랫폼 (OIDC / SAML) — 모든 서비스가 동일 프로토콜 사용
- Stripe · Twilio 같은 SaaS 자체가 OHS

**Context Map 다이어그램**:
```
              ┌──────────────────┐
              │  Identity        │ (Open Host Service)
              │  Provider        │  Published Language: OIDC
              └────────┬─────────┘
                       │ U
            ┌──────────┼──────────┐
            v D        v D        v D
        ┌───────┐  ┌───────┐  ┌───────┐
        │Sales  │  │Billing│  │Support│
        └───────┘  └───────┘  └───────┘
        (N 개 downstream, 동일 API 사용)
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Open Host Service: Identity Provider
// 모든 downstream 이 동일한 OIDC 프로토콜로 접근
@RestController
@RequestMapping("/oauth2")
class OAuth2OpenHostService {
    @PostMapping("/token")
    fun token(@RequestBody req: TokenRequest): TokenResponse =
        authService.issueToken(req)

    @GetMapping("/userinfo")
    fun userinfo(@RequestHeader("Authorization") token: String): UserInfo =
        authService.getUserInfo(token)

    // 클라이언트별 커스터마이즈 거부 — 모든 downstream 이 동일 API 사용
}

// Downstream A (Sales) — OHS 사용
class SalesAuthGuard(private val oauth: OAuth2Client) {
    fun authorize(token: String): Buyer = oauth.userinfo(token).let { Buyer(BuyerId(it.sub)) }
}

// Downstream B (Billing) — 동일한 OHS, 동일한 호출 방식
class BillingAuthGuard(private val oauth: OAuth2Client) {
    fun authorize(token: String): Payer = oauth.userinfo(token).let { Payer(PayerId(it.sub)) }
}
```

**관련 패턴**: [Published Language](#published-language), [Customer-Supplier](#customer-supplier), [Conformist](#conformist), [Context Map](#context-map)

---

<a id="published-language"></a>
## 9. Published Language

**정의**: Evans Blue Book Chapter 14. 두 BC 간 통신을 위해 사용되는 공통 모델 · 어휘 · 스키마. 산업 표준 (FHIR · HL7 · EDI · ISO 20022) 이거나 회사 내부의 공식 통합 스키마. [Open Host Service](#open-host-service) 와 짝을 이룸.

**메커니즘 / 관계 구조**:
- BC 내부 모델과 **분리된** 공식 통합 모델
- 명세는 JSON Schema / OpenAPI / Protobuf / Avro / XSD 로 코드화
- 버전 관리 정책 (semver · 호환성 매트릭스) 포함
- 산업 표준 채택 시 외부 통합 비용 급감
- Schema Registry (Confluent · Apicurio) 로 중앙 관리 가능

**장점**:
- 다수 BC / 외부 시스템과 통합 가능 — N:M 통합의 공통 분모
- 산업 표준 채택 시 외부 파트너와 zero-cost 통합
- 명세가 코드로 강제됨 (Schema validation, contract test)
- 시스템 진화의 안정 축 — 내부 모델은 변해도 통합 모델은 안정

**단점·주의**:
- Published Language 자체가 lowest common denominator 가 되어 어색해질 수 있음
- 버전 호환성 유지 비용 — 한번 published 되면 쉽게 못 바꿈
- BC 내부 모델 ↔ Published Language 변환 코드 필요 ([ACL](#anti-corruption-layer-strategic) 의 일종)
- 산업 표준이 우리 도메인에 안 맞으면 억지로 끼워 맞춤 위험

**활용 예시**:
- 의료: HL7 FHIR — 모든 의료 시스템 간 환자 데이터 교환
- 금융: ISO 20022 — 은행 간 결제 메시지
- 유통: EDI (X12 · EDIFACT) — 공급망 거래 문서
- 회사 내부: Customer Master Data Schema — 모든 BC 가 따르는 고객 데이터 표준

**Context Map 다이어그램**:
```
┌────────────┐    Published Language (HL7 FHIR)    ┌────────────┐
│ Hospital A │<─────────────────────────────────────│ Hospital B │
│  (OHS)     │     Patient · Encounter · Claim      │ (Conformist│
└────────────┘                                      └────────────┘
       │
       └─────> External Insurance Provider
              (동일 FHIR 모델로 통합)
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Published Language — HL7 FHIR (의료 산업 표준)
// 우리 BC 내부 모델 ≠ FHIR 모델. 변환 필요.

// 내부 도메인 모델
class Patient(
    val id: PatientId,
    val name: KoreanName,        // 한국 특화: 성·이름 분리
    val rrn: ResidentRegistrationNumber,  // 한국 특화: 주민번호
    val visits: List<EncounterId>,
)

// Published Language — FHIR Patient resource
data class FhirPatient(
    val resourceType: String = "Patient",
    val id: String,
    val identifier: List<FhirIdentifier>,
    val name: List<FhirHumanName>,
    val birthDate: String?,
)

// 변환 layer — 내부 모델 ↔ Published Language
class PatientPublishedLanguageMapper {
    fun toFhir(patient: Patient): FhirPatient = FhirPatient(
        id = patient.id.value,
        identifier = listOf(FhirIdentifier(system = "urn:rrn", value = patient.rrn.masked())),
        name = listOf(FhirHumanName(family = patient.name.family, given = listOf(patient.name.given))),
        birthDate = patient.rrn.toBirthDate().toString(),
    )
}
```

**관련 패턴**: [Open Host Service](#open-host-service), [Context Map](#context-map), [Conformist](#conformist), [Anti-Corruption Layer (전략)](#anti-corruption-layer-strategic)

---

<a id="shared-kernel"></a>
## 10. Shared Kernel

**정의**: Evans Blue Book Chapter 14. 두 (또는 소수) BC 팀이 공유하는 작은 도메인 모델 · 코드 모듈. 양 팀이 모두 합의해야 변경 가능한 "공동 자산". 매우 신중히 사용해야 하는 패턴 — Evans 가 직접 경고.

**메커니즘 / 관계 구조**:
- 공유 라이브러리 · 패키지 · 모듈로 구현
- 변경 시 양 팀 합의 필수 (PR 리뷰에 양 팀 reviewer 지정)
- 보통 핵심 식별자 · Value Object · Domain Event 정의 등 작은 범위
- 빌드 · 배포 파이프라인 공유 또는 명확한 버전 관리
- 너무 커지면 [Partnership](#partnership) 이나 별도 BC 로 분리

**장점**:
- 핵심 개념 (예: CustomerId · Money) 의 표준화
- 변환 코드 절감 — 양 BC 가 같은 객체 사용
- 강한 일관성 — 어느 팀이든 같은 의미

**단점·주의**:
- 변경 비용 큼 — 양 팀 합의 + 양쪽 배포 + 호환성 검토
- 한 팀의 변경이 다른 팀의 일정을 좌우 — 자율성 침해
- 작게 유지하지 않으면 사실상 [Big Ball of Mud](anti-patterns.md) 로
- Conway's Law 와 충돌 — 팀 경계와 코드 경계가 어긋남

**활용 예시**:
- 회사 공용 ID 타입 (`CustomerId`, `OrderId`) 라이브러리
- 회사 공용 Money / Currency 타입
- 핵심 Domain Event 정의 모듈 (이벤트 발행 / 구독 양 팀 공유)
- 보안 토큰 검증 라이브러리

**Context Map 다이어그램**:
```
┌──────────────┐                       ┌──────────────┐
│   Sales BC   │                       │  Billing BC  │
│              │                       │              │
└──────┬───────┘                       └──────┬───────┘
       │                                      │
       │       ┌──────────────────┐           │
       └──────>│  Shared Kernel    │<──────────┘
               │  (commons-domain) │
               │  · CustomerId     │
               │  · Money          │
               │  · Currency       │
               └──────────────────┘
              양 팀 합의 시에만 변경 가능
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Shared Kernel — 별도 모듈 (commons-domain)
package com.acme.commons.domain

@JvmInline value class CustomerId(val value: String)
@JvmInline value class OrderId(val value: String)

data class Money(val amount: BigDecimal, val currency: Currency) {
    operator fun plus(other: Money): Money {
        require(currency == other.currency) { "currency mismatch" }
        return Money(amount + other.amount, currency)
    }
}

// Sales BC 사용
package com.acme.sales
import com.acme.commons.domain.CustomerId
import com.acme.commons.domain.Money
class Order(val customerId: CustomerId, val total: Money) { /* ... */ }

// Billing BC 사용 — 같은 CustomerId · Money 타입
package com.acme.billing
import com.acme.commons.domain.CustomerId
import com.acme.commons.domain.Money
class Invoice(val customerId: CustomerId, val amount: Money) { /* ... */ }

// commons-domain 의 변경 → 양 팀 PR 승인 필수
```

**관련 패턴**: [Partnership](#partnership), [Bounded Context](#bounded-context-strategic), [Customer-Supplier](#customer-supplier), [Separate Ways](#separate-ways)

---

<a id="partnership"></a>
## 11. Partnership

**정의**: Vernon IDDD Chapter 3 에서 명시화된 관계 (Evans 의 Blue Book 에선 암묵적). 두 BC 팀이 운명 공동체로서 양쪽 모두 성공하지 않으면 어느 쪽도 성공 못하는 강한 결합 관계. 양쪽 동시 변경 · 동시 배포 · 동시 일정 협상.

**메커니즘 / 관계 구조**:
- 두 팀이 같은 비즈니스 이니셔티브를 위해 묶임
- API · 이벤트 · 데이터 모델 변경 시 양쪽 동시 협상
- 일정 · 우선순위 · 릴리스 계획을 통합 관리
- Customer-Supplier 보다 강한 결합 — upstream / downstream 구분 모호
- 보통 두 BC 가 짝을 이뤄 하나의 비즈니스 능력을 제공할 때

**장점**:
- 강한 협력으로 복잡한 비즈니스 능력 구현 가능
- 상호 이해도 높음 — 일정 추정 정확
- 통합 이슈 조기 발견

**단점·주의**:
- 자율성 손실 — 한 팀이 진행하려면 다른 팀이 준비돼야 함
- 한 팀 지연 = 양쪽 지연
- 장기간 유지 시 결국 하나의 BC 로 합쳐지는 게 합리적일 수 있음
- 다른 BC 와의 관계까지 동조화되는 부작용

**활용 예시**:
- 결제 BC ↔ 정산 BC — 결제 모델 변경 시 정산도 즉시 변경 필요
- 매칭 BC ↔ 가격 BC (우버) — 매칭 알고리즘 변경이 동적 가격에 즉각 영향
- 주문 BC ↔ 재고 BC — 주문 흐름 변경이 재고 차감 로직과 일체

**Context Map 다이어그램**:
```
┌──────────────┐                       ┌──────────────┐
│   Order      │     Partnership       │  Inventory   │
│   BC         │<────────────────────>│   BC          │
│              │   양쪽 동시 변경     │              │
└──────────────┘                       └──────────────┘
        │                                      │
        └──────── 통합 sprint planning ─────────┘
                 통합 릴리스 일정
                 양 팀 PM 협력
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Partnership: Order BC ↔ Inventory BC
// 양 팀이 함께 정의한 통합 이벤트 + 트랜잭션 흐름

// Order BC
class OrderService(private val inventory: InventoryClient) {
    fun place(cart: Cart): Order {
        // Partnership: 두 팀이 함께 설계한 reservation 프로토콜
        val reservation = inventory.reserve(cart.items, ttl = 5.minutes)
        // ... 결제 처리 ...
        inventory.commit(reservation.id)  // 또는 cancel()
        return Order(/* ... */)
    }
}

// Inventory BC — Order BC 와 같은 모델 · 같은 일정으로 진화
class InventoryService {
    fun reserve(items: List<ItemRequest>, ttl: Duration): Reservation = /* ... */
    fun commit(id: ReservationId) { /* ... */ }
    fun cancel(id: ReservationId) { /* ... */ }
}

// 두 BC 가 함께 변경하지 않으면 reservation 프로토콜 자체가 깨짐
// → 통합 sprint, 통합 contract test, 양 팀 PM 협력 필수
```

**관련 패턴**: [Customer-Supplier](#customer-supplier), [Shared Kernel](#shared-kernel), [Context Map](#context-map), [Bounded Context](#bounded-context-strategic)

---

<a id="separate-ways"></a>
## 12. Separate Ways

**정의**: Evans Blue Book Chapter 14. 두 BC 간 통합의 비용이 가치보다 큰 경우, 의도적으로 통합하지 않고 각자 갈 길을 가는 선택. "통합 안 함" 도 명시적 통합 패턴의 하나라는 인식이 핵심.

**메커니즘 / 관계 구조**:
- 두 BC 가 데이터 · API · 이벤트 어떤 채널로도 연결되지 않음
- 필요 시 수동 작업 · CSV export · 분기당 한 번의 ETL 등 비공식 통합으로 충분
- Context Map 에 명시적으로 "Separate Ways" 로 표기 — 무지가 아닌 결정
- 자주 [Big Ball of Mud](anti-patterns.md) 레거시와의 관계에 적용
- 시간이 지나 가치가 커지면 [ACL](#anti-corruption-layer-strategic) · [OHS](#open-host-service) 로 승격 가능

**장점**:
- 통합 비용 제로 — 가장 단순하고 저렴
- 양 BC 의 자율성 최대 — 어느 한 쪽 변경이 다른 쪽에 영향 없음
- 의식적 결정 — "우리는 통합 안 한다" 가 명시되어 향후 혼란 방지
- 작은 회사 · 초기 단계에서 합리적

**단점·주의**:
- 비즈니스 가치 발생 시 뒤늦은 통합 비용 폭발
- 데이터 일관성 없음 — 회사 차원 분석 · 보고 어려움
- 수동 작업 누적 → 사람 의존 프로세스
- 정치적으로 "포기" 처럼 보일 수 있음 — 의도적 결정임을 문서화 필수

**활용 예시**:
- 사내 위키 (Generic) ↔ 핵심 비즈니스 시스템 (Core) — 통합 가치 없음
- 인수합병 후 두 회사 ERP — 통합 비용 > 가치, 각자 운영 후 점진적 sunset
- 실험적 신규 BC — 본격 통합 전 검증 단계
- 레거시 시스템 — 신규 시스템이 ACL 뒤에서 점진적 인계, 그 사이 레거시는 separate ways

**Context Map 다이어그램**:
```
┌──────────────┐                       ┌──────────────┐
│   Internal   │                       │  Legacy      │
│   Wiki       │      Separate Ways    │  Reporting   │
│   (Generic)  │     (통합 안 함)      │  Tool        │
└──────────────┘                       └──────────────┘

연결 없음. 필요 시 분기 한 번 CSV export.
```

**Kotlin / pseudo-code 예제**:
```kotlin
// Separate Ways 는 "코드 없음" 이 정답
// 명시적 문서화만 코드로 표현

/**
 * Context: Internal Wiki ↔ Sales BC
 *
 * Relationship: SEPARATE WAYS (intentional)
 *
 * Rationale:
 * - 분기당 1회 매출 보고를 위키에 수동 게시
 * - 자동 통합 가치 < 통합 시스템 유지 비용 (현 시점)
 * - 가치 발생 시 ACL + OHS 로 승격 검토
 *
 * Last reviewed: 2026-Q1
 * Next review:   2026-Q4
 *
 * @see context-map.md §3.4
 */
object WikiSalesIntegration  // 의도적 빈 객체 — 문서 anchor 용도

// 비교: 만약 통합한다면 ACL 이 필요
// class WikiPublishAcl(private val wiki: WikiApi, private val sales: SalesQuery) {
//     fun publishQuarterlyReport(quarter: Quarter) { /* ... */ }
// }
// → 현재는 이 비용을 의도적으로 피한다.
```

**관련 패턴**: [Subdomain 분류](#subdomain-classification), [Context Map](#context-map), [Big Ball of Mud](anti-patterns.md), [Anti-Corruption Layer (전략)](#anti-corruption-layer-strategic)

---

## 종합 체크리스트

전략적 DDD 도입 시 점검:

- [ ] 도메인 전문가가 참여하는 [Ubiquitous Language](#ubiquitous-language) 글로서리가 존재하는가?
- [ ] 각 BC 의 [Subdomain 분류](#subdomain-classification) (Core / Supporting / Generic) 가 명시되어 있는가?
- [ ] Core Subdomain 에 시니어 개발자 · 정교한 패턴이 집중되어 있는가?
- [ ] Generic Subdomain 을 SaaS / 오픈소스로 대체했는가?
- [ ] [Context Map](#context-map) 이 그려져 있고 정기 갱신되는가?
- [ ] 각 통합 관계가 9 관계 중 어느 것인지 명시되어 있는가?
- [ ] [Conformist](#conformist) 가 Core Subdomain 에 적용되어 있지 않은가? (안티패턴)
- [ ] 외부 시스템 통합에 [ACL](#anti-corruption-layer-strategic) 또는 의도적 [Conformist](#conformist) 결정이 있는가?
- [ ] 다수 downstream 이 있는 upstream 은 [Open Host Service](#open-host-service) 인가?
- [ ] [Shared Kernel](#shared-kernel) 이 작게 유지되고 양 팀 합의 프로세스가 있는가?
- [ ] [Partnership](#partnership) 관계가 장기간 지속되면 BC 합병을 검토했는가?
- [ ] [Separate Ways](#separate-ways) 결정이 의도적이며 문서화되어 있는가?

---

## 참고 자료

- Eric Evans — *Domain-Driven Design: Tackling Complexity in the Heart of Software* (Addison-Wesley, 2003), Part IV "Strategic Design"
- Vaughn Vernon — *Implementing Domain-Driven Design* (Addison-Wesley, 2013), Part I
- Vaughn Vernon — *Domain-Driven Design Distilled* (Addison-Wesley, 2016)
- Alberto Brandolini — *Introducing EventStorming* (LeanPub, 2021)
- Nick Tune — *Strategic Domain-Driven Design* (blog series, https://nick-tune.netlify.app)
- Sam Newman — *Building Microservices*, 2nd ed. (O'Reilly, 2021) — BC ↔ 마이크로서비스 매핑
- Mat Wall · Nick Tune — *Architecture Modernization* (Manning, 2024) — Context Map 의 현대적 활용
