# 테스트 패턴 (Testing Patterns)

테스트 코드의 구조·범위·격리·검증 전략을 결정하는 패턴 모음. 단위 테스트부터 E2E 까지 계층별 비율을 정하는 거시 전략(Test Pyramid)과, 한 테스트의 본문을 어떻게 쓸지에 대한 미시 전략(AAA, Given-When-Then)을 함께 다룬다. Meszaros 의 xUnit Test Patterns 분류와 Kent C. Dodds 의 Testing Trophy 같은 현대 변형까지 포괄한다.

---

## 1. Test Pyramid

**목적**: 테스트를 Unit(많음) → Integration(중간) → E2E(소수)로 계층화하여 빠른 피드백과 신뢰도를 동시에 확보합니다.

**특징**:
- Mike Cohn(2009)이 제시한 비율 모델 (대략 70:20:10)
- 아래 계층일수록 빠르고 격리되며 결정적(deterministic)
- 위 계층일수록 느리고 비결정적이지만 사용자 시나리오에 가까움
- "Ice Cream Cone" 안티패턴(E2E만 많음)의 대안

**장점**:
- 빠른 피드백 루프 (Unit 수 ms)
- CI 비용 최소화
- 회귀 위치 빠르게 특정

**단점**:
- "통합 결함"은 Unit 으로 못 잡음 → Integration 적정량 필요
- 프런트엔드/마이크로서비스에서 비율 가이드가 모호
- Kent C. Dodds 의 **Testing Trophy** 는 통합 테스트를 더 강조(Static → Unit → Integration → E2E, Integration 비중↑) — JS/React 처럼 통합 가치가 큰 스택에 적합

**활용 예시**:
- JVM 백엔드: JUnit5 다수 + Testcontainers 일부 + Selenium 소수
- 모바일: Unit(domain) + Robolectric/Instrumented + Espresso/XCUITest

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Unit (다수): 순수 도메인 로직
class PriceCalculatorTest {
    @Test fun `10% 할인 적용`() {
        assertEquals(900, PriceCalculator().apply(1000, 0.1))
    }
}

// Integration (중간): DB/HTTP 연계
@SpringBootTest
class OrderRepoIntegrationTest {
    @Autowired lateinit var repo: OrderRepository
    @Test fun `주문 저장 후 조회`() { /* Testcontainers Postgres */ }
}

// E2E (소수): 사용자 시나리오
class CheckoutE2ETest { /* Playwright/Selenium 으로 결제 흐름 */ }
```

**관련 패턴**: Testing Trophy, Test Double, Test Fixture

---

## 2. AAA (Arrange-Act-Assert)

**목적**: 테스트 본문을 준비(Arrange) → 실행(Act) → 검증(Assert) 세 블록으로 분리하여 가독성과 일관성을 확보합니다.

**특징**:
- Bill Wake 가 명명한 단위 테스트 구조 관용구
- 각 블록은 빈 줄 한 칸으로 시각 분리
- Act 는 보통 한 줄(SUT 의 단일 호출)이 이상적

**장점**:
- 테스트 의도를 빠르게 파악
- 리뷰어가 "어디서 실패했나"를 즉시 분간
- IDE/포매터와 잘 어울리는 단순 규칙

**단점**:
- 행위(behavior) 보다 기술적 단계에 집중 → 비즈니스 시나리오 표현은 부족
- 동일 Act 에 여러 Assert 가 붙으면 한 테스트 = 한 동작 원칙 흐려짐
- BDD 의 자연어 문장 표현력에는 못 미침(→ Given-When-Then 비교)

**활용 예시**:
- JUnit/kotest 단위 테스트의 기본 골격
- Microsoft, Google 의 단위 테스트 가이드라인

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class CartTest {
    @Test fun `상품 추가 시 총액이 증가한다`() {
        // Arrange
        val cart = Cart()
        val item = Item(name = "book", price = 1000)

        // Act
        cart.add(item)

        // Assert
        assertEquals(1000, cart.total)
    }
}
```

**관련 패턴**: Given-When-Then, Test Fixture, Object Mother

---

## 3. Given-When-Then (BDD 스타일)

**목적**: 테스트를 비즈니스 시나리오의 자연어 문장(맥락-행동-결과)으로 기술하여 도메인 전문가와 공유 가능한 명세로 만듭니다.

**특징**:
- Dan North 의 BDD(Behavior-Driven Development)에서 유래
- Given(전제 상태) / When(트리거 행위) / Then(관찰 가능한 결과)
- Cucumber/Gherkin 의 시나리오 DSL 또는 kotest BehaviorSpec 으로 표현
- AAA 와 1:1 대응되지만 **자연어 문장 형태**가 핵심 차이

**장점**:
- 비개발자(PM/QA)도 시나리오 검토 가능
- 살아있는 명세(Living Documentation) 역할
- 도메인 용어를 테스트에 직접 노출

**단점**:
- 단순 단위 테스트에는 과한 형식
- Gherkin glue code 유지보수 비용
- 잘못 쓰면 "AAA를 한국어로 옮긴" 수준에 그침

**활용 예시**:
- Cucumber-JVM, kotest BehaviorSpec/FeatureSpec
- 결제, 보험금 산정 등 도메인 규칙이 복잡한 영역의 인수 테스트

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**AAA vs Given-When-Then 비교**:
| 측면 | AAA | Given-When-Then |
|---|---|---|
| 청자 | 개발자 | 개발자 + 도메인 전문가 |
| 형식 | 코드 주석/블록 | 자연어 문장 (DSL) |
| 강점 | 단위 테스트 골격 | 인수/시나리오 테스트 |
| 도구 | JUnit, kotest | Cucumber, kotest BehaviorSpec |

**Kotlin 예제**:
```kotlin
class WithdrawalSpec : BehaviorSpec({
    given("잔액 10,000원 계좌") {
        val account = Account(balance = 10_000)
        `when`("5,000원 출금") {
            account.withdraw(5_000)
            then("잔액은 5,000원") {
                account.balance shouldBe 5_000
            }
        }
    }
})
```

**관련 패턴**: AAA, Test Fixture, Object Mother

---

## 4. Test Double (Stub / Mock / Spy / Fake / Dummy)

**목적**: SUT(System Under Test)의 협력자(collaborator)를 테스트용 대역으로 치환하여 외부 의존성을 격리하고 행위를 제어합니다.

**특징**:
- Gerard Meszaros 의 *xUnit Test Patterns* 분류 (Martin Fowler 의 "Mocks Aren't Stubs" 글로 대중화)
- "Test Double" 은 영화 스턴트 대역에서 빌려온 우산 용어
- Mockk, Mockito, fakes 라이브러리 등으로 구현

**5종 비교**:
| 종류 | 입력 응답 | 호출 검증 | 내부 상태 | 용도 |
|---|---|---|---|---|
| **Dummy** | 사용 안 함 | 안 함 | 없음 | 인자 자리 채우기용 (참조만 필요) |
| **Stub** | 미리 지정한 값 반환 | 안 함 | 없음/최소 | 간접 입력(indirect input) 제공 |
| **Spy** | Stub 처럼 응답 | **호출 기록 사후 검증** | 호출 로그 | 호출 횟수/인자 사후 확인 |
| **Mock** | 사전 기대(expectation) 설정 | **사전 정의대로 검증** | 기대 스크립트 | 행위 기반(behavior) 검증 |
| **Fake** | 실제 동작하는 경량 구현 | 안 함 | 실제 상태 보유 | 메모리 DB, in-memory queue |

**장점**:
- 외부 시스템(DB/HTTP/시간) 격리 → 결정적 테스트
- 실패 경로(예외/타임아웃) 시나리오 재현 용이
- 테스트 속도 향상

**단점**:
- 과한 Mock → 구현 세부에 결합(test rot, 리팩토링 저항)
- "Mockist vs Classicist" 논쟁: 상태 기반(Fake) 선호 vs 행위 기반(Mock) 선호
- Fake 가 진짜 구현과 미세하게 달라지면 false positive

**활용 예시**:
- Mockk `every {} returns ...`(Stub), `verify {}`(Mock/Spy)
- Spring `@MockBean`, H2 in-memory DB(Fake)
- WireMock(HTTP Fake/Stub)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제 (Mockk)**:
```kotlin
class OrderServiceTest {
    @Test fun `결제 실패 시 주문 취소`() {
        val payment = mockk<PaymentClient>()                  // Mock
        every { payment.charge(any()) } throws TimeoutException() // Stub 응답

        val log = spyk(InMemoryAuditLog())                    // Spy
        val service = OrderService(payment, log)

        assertThrows<OrderFailed> { service.place(Order(id = 1)) }
        verify(exactly = 1) { log.write(match { it.contains("cancel") }) } // Mock 검증
    }
}

// Fake 예시: 메모리 저장소
class FakeOrderRepo : OrderRepo {
    private val store = mutableMapOf<Long, Order>()
    override fun save(o: Order) { store[o.id] = o }
    override fun find(id: Long) = store[id]
}
```

**관련 패턴**: Test Fixture, Object Mother, Page Object

---

## 5. Property-Based Test

**목적**: 구체적 입력 예시 대신 입력의 **속성(property)** 을 선언하고, 프레임워크가 무작위 입력을 대량 생성·축소(shrink)하여 반례를 찾게 합니다.

**특징**:
- Haskell QuickCheck(1999)에서 시작 → ScalaCheck, Hypothesis(Python), kotest property
- 실패 시 **shrinking** 으로 최소 반례 자동 축소
- 불변식(invariants), 왕복(round-trip), 멱등(idempotency) 검증에 강함

**장점**:
- 사람이 떠올리지 못한 edge case 발견 (빈 입력, 유니코드, 경계값)
- 한 줄 명세로 수천 케이스 커버
- 회귀 시 reproducer seed 저장 가능

**단점**:
- 적절한 generator 작성 학습 곡선
- 비결정적 실패 → 재현은 seed 로 가능하지만 디버깅 부담
- 모든 로직이 속성으로 표현되지 않음 (UI 흐름 등)

**활용 예시**:
- 직렬화 왕복: `decode(encode(x)) == x`
- 정렬 결과 길이/요소집합 불변
- 금융 계산의 결합/교환 법칙

**난이도**: 중간~높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제 (kotest property)**:
```kotlin
class JsonRoundTripSpec : StringSpec({
    "encode-decode 왕복은 동일하다" {
        checkAll(Arb.string(), Arb.int()) { name, age ->
            val original = User(name, age)
            Json.decodeFromString<User>(Json.encodeToString(original)) shouldBe original
        }
    }
})
```

**관련 패턴**: Test Double, Mutation Test, Snapshot Test

---

## 6. Contract Test (Consumer-Driven Contract)

**목적**: 소비자(Consumer)와 제공자(Provider) 사이의 API 계약을 양측이 합의한 명세로 자동 검증하여 마이크로서비스 통합 결함을 사전 차단합니다.

**특징**:
- Pact, Spring Cloud Contract 가 대표 도구
- Consumer 가 기대 응답을 **계약 파일**로 발행 → Provider 가 동일 계약으로 검증
- E2E 보다 빠르고 결정적, Unit 보다 통합 신뢰도 높음

**장점**:
- "내 변경이 누구를 깨뜨리나" 를 CI 에서 사전 감지
- Provider 가 한 곳에서 모든 Consumer 계약을 일괄 검증
- E2E 인프라(전체 환경) 없이 통합 신뢰 확보

**단점**:
- 계약 broker(Pact Broker) 운영 비용
- 비동기 메시지/스트리밍 계약은 도구 성숙도 편차
- 잘못 쓰면 단순한 schema test 로 전락

**활용 예시**:
- 모바일 앱(Consumer) ↔ Backend(Provider)
- BFF ↔ 내부 마이크로서비스
- 이벤트 스트림(Pact Message)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제 (Pact JVM, Consumer 측)**:
```kotlin
@ExtendWith(PactConsumerTestExt::class)
class UserApiContractTest {
    @Pact(consumer = "mobile-app", provider = "user-service")
    fun userPact(builder: PactDslWithProvider): RequestResponsePact =
        builder.given("user 1 exists")
            .uponReceiving("GET /users/1")
            .path("/users/1").method("GET")
            .willRespondWith().status(200)
            .body("""{"id":1,"name":"alice"}""")
            .toPact()

    @Test
    @PactTestFor(pactMethod = "userPact")
    fun `사용자 조회`(mockServer: MockServer) {
        val user = UserClient(mockServer.getUrl()).find(1)
        user.name shouldBe "alice"
    }
}
```

**관련 패턴**: Test Pyramid, Test Double, Schema Migration

---

## 7. Snapshot Test

**목적**: 출력(렌더링된 UI, 직렬화된 객체, 생성 코드 등)을 최초 실행 시 스냅샷 파일로 저장하고, 이후 실행에서 동일성을 비교하여 비의도적 변화를 감지합니다.

**특징**:
- Jest 가 대중화, Kotlin 진영은 kotest snapshot / approvaltests-java
- 첫 실행: 스냅샷 생성. 이후 실행: diff 검증
- 의도된 변화면 스냅샷 갱신(승인) 후 커밋

**장점**:
- assertion 작성 비용 절감 (대형 출력에 특히 유효)
- 의도치 않은 변경 즉시 가시화
- 리뷰 시 스냅샷 diff 가 곧 변경의 시각적 증거

**단점**:
- "rubber stamp" 위험 (변경되면 무지성 갱신)
- 비결정적 출력(타임스탬프/난수) 처리 필요
- 스냅샷 파일이 비대해지면 PR diff 가독성 저하

**활용 예시**:
- React/Vue 컴포넌트 렌더링 결과
- 코드 생성기 산출물(OpenAPI generator)
- ADF/Markdown 변환기 출력(예: jira-auto-analyze 의 adf → md)

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제 (approvaltests-java)**:
```kotlin
class MarkdownRendererTest {
    @Test fun `복잡한 ADF 를 markdown 으로 변환`() {
        val adf = loadFixture("complex.json")
        val md = MarkdownRenderer().render(adf)
        Approvals.verify(md) // .approved.txt 와 비교; 첫 실행은 .received.txt 검토 후 승인
    }
}
```

**관련 패턴**: Test Fixture, Property-Based Test, Mutation Test

---

## 8. Mutation Test

**목적**: 프로덕션 코드를 자동으로 변이(mutation)시킨 뒤 테스트가 그 변이를 잡아내는지 측정하여, **테스트의 실제 효력(mutation score)** 을 평가합니다.

**특징**:
- Pitest(JVM), Stryker(JS/.NET), mutmut(Python) 등
- 변이 예: `>` → `>=`, `+` → `-`, `return x` → `return null`
- "killed" (테스트 실패 → 좋음) vs "survived" (테스트 통과 → 테스트 부실)

**장점**:
- 라인 커버리지의 거짓 안심을 깨뜨림 (커버되었지만 assert 없는 경우 적발)
- 약한 assertion 을 정량적으로 드러냄
- 테스트 강화 우선순위 도출

**단점**:
- 실행 시간 매우 김 (변이 N개 × 테스트 N개)
- "equivalent mutant" (의미 동등한 변이) 노이즈
- CI 매 빌드 실행은 비현실적 → 야간/주간 잡 권장

**활용 예시**:
- 금융 계산 코어 모듈의 테스트 품질 정량화
- 라이브러리 릴리스 전 테스트 보강 가이드
- Pitest + Maven/Gradle plugin

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제 (Pitest gradle)**:
```kotlin
// build.gradle.kts
plugins { id("info.solidsoft.pitest") version "1.15.0" }
pitest {
    targetClasses.set(listOf("com.example.pricing.*"))
    mutators.set(listOf("STRONGER"))
    threads.set(4)
    mutationThreshold.set(80) // 80% 미만이면 빌드 실패
}
// ./gradlew pitest → build/reports/pitest/ 에 HTML 리포트
```

**관련 패턴**: Property-Based Test, Test Pyramid, Test Double

---

## 9. Test Fixture (Setup / Teardown / SUT)

**목적**: 테스트가 의존하는 사전 상태(데이터, 객체 그래프, 외부 리소스)를 일관되게 구축·해체하는 메커니즘을 정의합니다.

**특징**:
- Meszaros 분류: Inline / Delegated / Implicit / Shared Fixture
- SUT(System Under Test) = 테스트 대상, fixture = 그 주변 환경
- JUnit5 `@BeforeEach/@AfterEach`, kotest `beforeTest/afterTest`, Testcontainers `@Container`

**장점**:
- 테스트 간 격리(Fresh Fixture) → 순서 의존 제거
- 셋업 코드 중복 제거
- 무거운 리소스(DB 컨테이너)는 Shared Fixture 로 재사용 가능

**단점**:
- Implicit Fixture(`@BeforeEach`) 남용 → 테스트가 멀리 있는 setup 에 묵시 의존
- Shared Fixture 는 테스트 간 오염 위험
- Fixture 가 비대해지면 가독성 저하 → Object Mother 로 분리

**활용 예시**:
- Spring `@SpringBootTest` + Testcontainers Postgres
- kotest `TestListener` 로 공용 컨테이너 lifecycle 관리
- E2E 의 사용자 계정 seeding

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class OrderRepoTest {
    private lateinit var db: Database
    private lateinit var sut: OrderRepository

    @BeforeEach fun setUp() {
        db = Database.connect("jdbc:h2:mem:test;DB_CLOSE_DELAY=-1")
        transaction(db) { SchemaUtils.create(Orders) }
        sut = OrderRepository(db)
    }

    @AfterEach fun tearDown() {
        transaction(db) { SchemaUtils.drop(Orders) }
    }

    @Test fun `저장된 주문을 ID 로 조회한다`() {
        val id = sut.save(Order(amount = 1000))
        sut.find(id)?.amount shouldBe 1000
    }
}
```

**관련 패턴**: Object Mother, Test Double, AAA

---

## 10. Object Mother / Test Data Builder

**목적**: 테스트 데이터(특히 복잡한 도메인 객체) 생성을 한 곳에 모아 재사용하고, 테스트 본문에서 "의미 있는 차이"만 강조합니다.

**특징**:
- **Object Mother**: `aValidCustomer()`, `aPremiumOrder()` 같은 팩토리 함수 (Martin Fowler)
- **Test Data Builder**: `OrderBuilder().withPremiumCustomer().withItems(...).build()` 빌더 패턴 (Nat Pryce & Steve Freeman)
- 둘 다 "기본값 + 일부 override" 가 핵심

**장점**:
- 테스트가 시나리오의 본질에만 집중
- 도메인 변경 시 생성 코드 한 곳만 수정
- 무의미한 필드 노이즈 제거 (가독성↑)

**단점**:
- Mother 가 비대해지면 신규 시나리오 추가 시 영향 범위 큼
- Builder 는 코드량이 많아짐 (보일러플레이트)
- 잘못 쓰면 "어디서 만든 데이터인지" 추적 어려움

**활용 예시**:
- 복잡한 주문/계약/사용자 객체
- 통합 테스트의 seed 데이터
- Faker 라이브러리와 결합

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Object Mother
object CustomerMother {
    fun aValidCustomer(name: String = "alice") =
        Customer(id = 1, name = name, tier = Tier.STANDARD, country = "KR")
    fun aPremiumCustomer() = aValidCustomer().copy(tier = Tier.PREMIUM)
}

// Test Data Builder (DSL)
class OrderBuilder {
    private var customer = CustomerMother.aValidCustomer()
    private var items = mutableListOf(Item("book", 1000))
    fun withCustomer(c: Customer) = apply { customer = c }
    fun withItems(vararg i: Item) = apply { items = i.toMutableList() }
    fun build() = Order(customer, items.toList())
}
fun anOrder(block: OrderBuilder.() -> Unit = {}) = OrderBuilder().apply(block).build()

// 사용
@Test fun `프리미엄 고객은 무료 배송`() {
    val order = anOrder { withCustomer(CustomerMother.aPremiumCustomer()) }
    ShippingPolicy().fee(order) shouldBe 0
}
```

**관련 패턴**: Test Fixture, Builder(GoF), AAA

---

## 11. Page Object (UI 테스트 추상화)

**목적**: UI 페이지/화면을 객체로 감싸서 선택자(selector)와 상호작용 로직을 한 곳에 캡슐화하고, 테스트는 사용자 행위만 기술하도록 합니다.

**특징**:
- Selenium 진영에서 정립(Martin Fowler, Selenium wiki)
- 페이지마다 클래스 1개, 사용자가 할 수 있는 행위가 메서드
- 셀렉터 변경 시 Page Object 만 수정 → 테스트 무영향
- Playwright, Espresso, XCUITest 에 동일 개념 적용

**장점**:
- DRY: 동일 화면 다수 테스트가 한 selector 정의 공유
- 가독성: 테스트가 비즈니스 행위 시퀀스로 읽힘
- 리팩토링 내성: UI 변경의 폭발 반경 축소

**단점**:
- Page Object 가 비대해지면 신(scene)/컴포넌트 단위 분할 필요
- "assert 를 Page Object 에 둘 것인가" 합의 필요(보통 테스트 측 권장)
- 동적 UI(가상 스크롤 등)에서 selector 안정화 작업 추가

**활용 예시**:
- Selenium/Playwright 웹 E2E
- Android Espresso, iOS XCUITest
- jira-auto-analyze 의 worker-ui / admin-ui Wails 앱 E2E(향후 도입 시)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제 (Playwright for Java/Kotlin)**:
```kotlin
class LoginPage(private val page: Page) {
    private val idInput = page.locator("input[name=id]")
    private val pwInput = page.locator("input[name=pw]")
    private val submit  = page.locator("button[type=submit]")

    fun open() = apply { page.navigate("https://app.example.com/login") }
    fun loginAs(id: String, pw: String): HomePage {
        idInput.fill(id); pwInput.fill(pw); submit.click()
        return HomePage(page)
    }
}

class LoginE2ETest {
    @Test fun `정상 로그인 후 홈 진입`() {
        val home = LoginPage(page).open().loginAs("alice", "secret")
        home.welcomeText() shouldContain "alice"
    }
}
```

**관련 패턴**: Test Fixture, MVP/MVVM(생산 코드 측), AAA
