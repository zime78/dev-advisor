# Code Smells (코드 스멜)

Martin Fowler 가 *Refactoring* (1999, 2018 2nd ed.) Chapter 3 "Bad Smells in Code" 에서 정리한 **22 가지 코드 스멜**. 코드를 직접 부수지는 않지만 **변경 비용 / 유지보수 비용을 상승시키는 신호** 다. 22 항목은 5 그룹(Bloaters / OO Abusers / Change Preventers / Dispensables / Couplers)으로 묶이며 각 스멜마다 권장 리팩토링 카탈로그가 매핑된다.

**원전**:
- Martin Fowler, *Refactoring: Improving the Design of Existing Code*, 2nd ed. (2018), Chapter 3 — 22 스멜 (현행 표준)
- Martin Fowler, William Opdyke, John Brant, Don Roberts, *Refactoring* 1st ed. (1999) — 22 스멜 원전 (Kent Beck 협업)
- Robert C. Martin, *Clean Code* (2008), Chapter 17 "Smells and Heuristics" — 보완 휴리스틱

**핵심 원칙**: 스멜은 *증상* 이고 리팩토링은 *처방* 이다. 모든 스멜을 항상 제거해야 하는 게 아니라 **변경 요구가 들어왔을 때** 같이 처리한다 ("opportunistic refactoring", Boy Scout Rule).

---

<a id="1-long-method"></a>
## 1. Long Method (긴 메서드)

**그룹**: Bloater

**식별 신호**:
- 단일 메서드가 **50 줄 이상** (Kotlin / Java 기준, 정량 임계값은 팀마다 다름 — Robert Martin 은 "screen 한 화면" 기준 20 줄 권장)
- 한 메서드 안에 주석으로 단락이 나뉘어 있음 (`// 1. 검증`, `// 2. 계산`, `// 3. 저장`)
- 들여쓰기 깊이 4 단계 이상, 변수 10 개 이상

**원인**: 절차적 사고가 그대로 코드에 남음. "지금만 추가" 가 누적되며 신규 분기·검증·로그가 같은 메서드에 쌓임.

**영향**: 가독성 ↓ (한 화면에 안 들어옴), 테스트 ↓ (분기 조합 폭증), 재사용 ↓ (부분 로직 추출 불가), 변경 위험 ↑ (한 줄 수정이 전체 흐름에 영향).

**권장 리팩토링**:
- **Extract Function** (가장 빈번한 처방, Fowler 카탈로그 1번)
- **Replace Temp with Query** (임시 변수 → 메서드)
- **Decompose Conditional** (조건문 블록 → 별도 메서드)
- **Introduce Parameter Object** (파라미터 다발 정리)
- **Replace Method with Method Object** (메서드 자체를 클래스로)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```kotlin
// Bad: 한 메서드에 검증·계산·저장·알림이 모두 섞임
fun processOrder(order: Order): Receipt {
    // 검증
    if (order.items.isEmpty()) throw IllegalArgumentException("빈 주문")
    if (order.customer.age < 18 && order.containsAlcohol()) throw IllegalStateException("주류 제한")
    // 할인 계산
    var total = 0.0
    for (item in order.items) total += item.price * item.qty
    if (order.customer.isVip) total *= 0.9
    if (order.coupon != null) total -= order.coupon.amount
    // 저장
    db.save(order)
    // 알림
    mailer.send(order.customer.email, "주문 완료 $total")
    return Receipt(order.id, total)
}

// Good: 의도 단위로 Extract Function
fun processOrder(order: Order): Receipt {
    validate(order)                       // 검증
    val total = calculateTotal(order)     // 계산
    persist(order)                        // 저장
    notify(order, total)                  // 알림
    return Receipt(order.id, total)
}
```

**관련 스멜 / 원칙**:
- [code-smell-large-class](#2-large-class-aka-god-class) (긴 메서드 모임)
- [code-smell-comments](#13-comments) (단락 주석은 Extract Function 신호)
- [srp](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙), [high-cohesion](grasp.md#5-high-cohesion)

---

<a id="2-large-class"></a>
## 2. Large Class (aka God Class)

**그룹**: Bloater

**식별 신호**:
- 클래스가 **500 줄 이상**, 또는 필드 **10 개 이상**, public 메서드 **20 개 이상**
- 클래스 이름이 `Manager`, `Processor`, `Util`, `Helper` 처럼 모호
- 책임이 여러 액터(회계·HR·운영) 의 변경 요구를 한 곳에서 받음

**원인**: 처음 도메인 모델을 작게 시작했다가 신규 요구가 누적되며 "여기 추가하면 편하니까" 로 비대해짐. SRP 미준수 + Extract Class 미수행.

**영향**: 변경 충돌 ↑ (여러 개발자가 같은 클래스 수정), 테스트 ↓ (의존성 다발), 재사용 ↓ (부분 책임만 떼낼 수 없음), 인지 부하 ↑.

**권장 리팩토링**:
- **Extract Class** (응집된 책임 묶음 → 새 클래스)
- **Extract Superclass** (공통 부분 → 부모 클래스)
- **Extract Subclass** (조건 분기 → 서브클래스 다형성)
- **Replace Type Code with Subclasses** (type field 다형성화)

**난이도**: 중간 | **사용 빈도**: ★★★★★

```java
// Bad: User 클래스가 인증·프로필·결제·알림을 모두 보유
class User {
    String email, password, name, address;
    CreditCard card; int loyaltyPoints;
    public boolean login(String pwd) { /* 인증 */ }
    public void updateProfile(String name, String addr) { /* 프로필 */ }
    public void chargeCard(double amount) { /* 결제 */ }
    public void sendEmail(String body) { /* 알림 */ }
    // ... 30 개 더
}

// Good: Extract Class 로 책임 분리
class User {
    private Credentials credentials;   // 인증 책임
    private Profile profile;           // 프로필 책임
    private Wallet wallet;             // 결제 책임
    private Notifier notifier;         // 알림 책임
}
class Credentials { boolean login(String pwd) { /* ... */ } }
class Profile { void update(String name, String addr) { /* ... */ } }
```

**관련 스멜 / 원칙**:
- [code-smell-divergent-change](#10-divergent-change), [code-smell-feature-envy](#19-feature-envy)
- [srp](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙), [high-cohesion](grasp.md#5-high-cohesion)
- 별칭: God Class (Riel, 1996)

---

<a id="3-primitive-obsession"></a>

## 3. Primitive Obsession (기본 타입 집착)

**그룹**: Bloater

**식별 신호**:
- 도메인 개념을 **`String` / `int` / `Map<String,String>`** 같은 원시 타입으로만 표현 (예: 전화번호, 이메일, 통화금액)
- 검증 로직이 사용처마다 반복 (`if (email.contains("@"))`)
- 같은 단위의 숫자를 헷갈려 버그 발생 (USD vs KRW, meters vs feet)

**원인**: 작은 도메인 객체를 "굳이 클래스로 만들 필요 없다" 고 판단. 타입 안정성보다 단순성 우선.

**영향**: 검증 분산, 단위 혼동 버그, 도메인 의미 손실, IDE 자동완성 빈약.

**권장 리팩토링**:
- **Replace Primitive with Object** (Money, EmailAddress 같은 Value Object 도입)
- **Replace Type Code with Subclasses** (status string → enum/sealed class)
- **Replace Type Code with State/Strategy** (상태 전이 로직 캡슐화)
- **Extract Class** (관련 primitive 다발 → 클래스)

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★★

```kotlin
// Bad: 모든 게 String / Double — 통화 단위 혼동 가능
fun transfer(fromEmail: String, toEmail: String, amount: Double, currency: String) {
    if (!fromEmail.contains("@")) throw IllegalArgumentException()
    if (amount <= 0) throw IllegalArgumentException()
    // amount 가 USD 인지 KRW 인지 함수마다 추적해야 함
}

// Good: Value Object 로 도메인 개념 캡슐화
data class Email(val value: String) {
    init { require(value.contains("@")) { "잘못된 이메일" } }
}
data class Money(val amount: BigDecimal, val currency: Currency) {
    init { require(amount > BigDecimal.ZERO) { "양수여야 함" } }
}
fun transfer(from: Email, to: Email, money: Money) { /* 단위 혼동 불가 */ }
```

**관련 스멜 / 원칙**:
- [code-smell-data-clumps](#5-data-clumps), [code-smell-data-class](#16-data-class)
- DDD Value Object, [information-expert](grasp.md#1-information-expert)

---

<a id="4-long-parameter-list"></a>
## 4. Long Parameter List (긴 파라미터 리스트)

**그룹**: Bloater

**식별 신호**:
- 함수 파라미터 **5 개 이상** (Robert Martin: 3 개 초과 시 의심, 4 개부터 reconsider)
- 같은 파라미터 묶음이 여러 함수에 반복 (Data Clumps 동반)
- boolean flag 파라미터 (`save(user, true, false, null)`)

**원인**: 함수 책임이 비대 + 의존성 주입 회피 + Value Object 미사용. "한 번에 다 받자" 식 시그니처.

**영향**: 호출부 가독성 ↓, 인자 순서 실수 ↑, 리팩토링 어려움 (시그니처 변경 전파), IDE 자동완성 활용 불가.

**권장 리팩토링**:
- **Introduce Parameter Object** (관련 인자 → 클래스/Record)
- **Preserve Whole Object** (분해된 필드 대신 전체 객체 전달)
- **Replace Parameter with Query** (호출자가 계산해 넘기는 값을 함수 내부 query 로)
- **Remove Flag Argument** (boolean → 별도 함수)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```java
// Bad: 8 개 파라미터, 순서 헷갈리기 쉬움
void createOrder(String customerId, String productId, int qty,
                 double price, String currency, String address,
                 boolean express, boolean giftWrap) { /* ... */ }

// Good: Introduce Parameter Object
record OrderRequest(Customer customer, LineItem item, Money price,
                    ShippingAddress address, ShippingOptions options) {}
void createOrder(OrderRequest req) { /* ... */ }

// Bad: boolean flag
void render(Report report, boolean toPdf) { /* ... */ }
// Good: Remove Flag Argument — 별도 함수
void renderPdf(Report report) { /* ... */ }
void renderHtml(Report report) { /* ... */ }
```

**관련 스멜 / 원칙**:
- [code-smell-data-clumps](#5-data-clumps), [code-smell-primitive-obsession](#3-primitive-obsession)
- [low-coupling](grasp.md#4-low-coupling)

---

## 5. Data Clumps (데이터 뭉치)

**그룹**: Bloater

**식별 신호**:
- 같은 필드 묶음 (예: `street, city, zip, country`) 이 **3 군데 이상**에 반복 등장
- 함수 시그니처에서 같은 파라미터 그룹이 함께 다님
- 한 필드를 추가하면 같이 다니던 다른 필드도 같은 곳에 추가됨

**원인**: Value Object 인식 부족. 처음에는 2~3 개로 시작했다가 늘면서도 묶지 않음.

**영향**: 변경 산탄총 효과 (필드 추가 시 모든 사용처 수정), 검증 로직 분산, 도메인 개념 묻힘.

**권장 리팩토링**:
- **Extract Class** (필드 묶음 → 새 클래스)
- **Introduce Parameter Object** (함수 인자 묶음 → 클래스)
- **Preserve Whole Object** (개별 필드 대신 객체 통째 전달)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```kotlin
// Bad: street/city/zip/country 가 여러 함수에 흩어져 다님
fun shipTo(street: String, city: String, zip: String, country: String) { }
fun bill(name: String, street: String, city: String, zip: String, country: String) { }
fun validate(street: String, city: String, zip: String, country: String) { }

// Good: Extract Class — Address 라는 도메인 개념 발견
data class Address(val street: String, val city: String, val zip: String, val country: String) {
    fun validate(): Boolean = zip.isNotBlank() && country.isNotBlank()
}
fun shipTo(addr: Address) { }
fun bill(name: String, addr: Address) { }
```

**관련 스멜 / 원칙**:
- [code-smell-primitive-obsession](#3-primitive-obsession), [code-smell-long-parameter-list](#4-long-parameter-list)
- [information-expert](grasp.md#1-information-expert)

---

<a id="6-repeated-switches"></a>
## 6. Repeated Switches (반복되는 switch)

**그룹**: OO Abuser

**식별 신호**:
- **같은 조건 분기 (switch / when / if-else chain)** 가 코드베이스 여러 곳에 반복 등장
- 새 case 추가 시 여러 파일을 동시에 수정해야 함 (Shotgun Surgery 와 결합)
- 분기 키가 type code (`type == "card"`, `kind == "admin"`)

**원인**: Fowler 가 1st ed. 의 "Switch Statements" 를 2nd ed. 에서 "Repeated Switches" 로 재명명한 이유 — *반복* 자체가 문제. 한 곳의 switch 는 괜찮지만 같은 키로 도는 switch 가 여러 군데 있으면 다형성 부재 신호.

**영향**: OCP 위반 (확장 시 기존 코드 수정), 새 case 누락 위험, 조건 키와 동작이 결합되어 응집도 ↓.

**권장 리팩토링**:
- **Replace Conditional with Polymorphism** (분기 → 서브클래스 다형성)
- **Replace Type Code with Subclasses** (type field → 서브클래스 계층)
- **Replace Type Code with State/Strategy** (상태/전략 패턴)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```kotlin
// Bad: 같은 type 분기가 3 곳에서 반복
fun salary(emp: Employee) = when (emp.type) {
    "ENG" -> 5000.0; "MGR" -> 7000.0; "EXEC" -> 10000.0; else -> 0.0
}
fun bonus(emp: Employee) = when (emp.type) {
    "ENG" -> 500.0; "MGR" -> 1000.0; "EXEC" -> 3000.0; else -> 0.0
}
fun vacationDays(emp: Employee) = when (emp.type) {
    "ENG" -> 15; "MGR" -> 20; "EXEC" -> 30; else -> 10
}

// Good: 다형성 — 신규 직급 추가 시 클래스 하나만 추가
sealed class Employee {
    abstract fun salary(): Double; abstract fun bonus(): Double; abstract fun vacation(): Int
}
class Engineer : Employee() { /* 5000, 500, 15 */ }
class Manager : Employee()  { /* 7000, 1000, 20 */ }
class Executive : Employee(){ /* 10000, 3000, 30 */ }
```

**관련 스멜 / 원칙**:
- [code-smell-switch-statements](#7-switch-statements), [code-smell-shotgun-surgery](#11-shotgun-surgery)
- [ocp](solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙), [polymorphism](grasp.md#6-polymorphism)

---

<a id="7-switch-statements"></a>
## 7. Switch Statements (조건 분기)

**그룹**: OO Abuser

**식별 신호**:
- 단일 switch / when 블록이 **case 5 개 이상**, 또는 매우 긴 분기
- enum / type code 에 따라 동작이 갈리는 거대 분기
- 동일한 switch 가 한 곳에만 있어도 type code 기반이면 의심

**원인**: OO 도입 전 절차적 사고. 행위(verb) 가 데이터(noun) 의 type 에 종속되어 있음. 다형성 미활용.

**영향**: 새 case 추가 시 분기 수정 (OCP 위반), case 누락 가능, 분기 안 로직이 비대해지면 Long Method 동반.

**권장 리팩토링**:
- **Replace Conditional with Polymorphism**
- **Replace Type Code with State/Strategy**
- **Introduce Special Case** (null/특수 case → 객체로)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```java
// Bad: switch 안에서 type 별 처리
double charge(Customer c, int days) {
    switch (c.getType()) {
        case REGULAR:  return days * 1.5;
        case CHILD:    return days * 1.0;
        case NEW_RELEASE: return days * 3.0;
        default: throw new IllegalStateException();
    }
}

// Good: 다형성
abstract class Customer { abstract double charge(int days); }
class Regular extends Customer    { double charge(int d){ return d * 1.5; } }
class Child extends Customer      { double charge(int d){ return d * 1.0; } }
class NewRelease extends Customer { double charge(int d){ return d * 3.0; } }
```

**관련 스멜 / 원칙**:
- [code-smell-repeated-switches](#6-repeated-switches) (반복 시 위험도 ↑)
- [ocp](solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙), Strategy, State

---

<a id="8-refused-bequest"></a>
<a id="8-refused-bequest-거절된-유산"></a>
## 8. Refused Bequest (거부된 유산)

**그룹**: OO Abuser

**식별 신호**:
- 자식 클래스가 부모의 메서드 / 필드를 **사용하지 않거나, override 해서 예외 던짐**
- "is-a" 가 아닌데 코드 재사용 목적으로 상속
- 부모 인터페이스가 자식의 실제 능력보다 크다 (`Penguin.fly()`)

**원인**: 상속을 *재사용 메커니즘* 으로 오용. 행위 호환성보다 코드 재사용 우선.

**영향**: LSP 위반 → 다형성 무너짐. 부모 타입 변수로 받은 코드가 자식 인스턴스에서 예외 발생. 안전한 polymorphic 사용 불가.

**권장 리팩토링**:
- **Replace Inheritance with Delegation** (상속 → 위임)
- **Push Down Method/Field** (부모 → 자식으로 이동)
- **Extract Superclass** (공통 부분만 새 부모로)

**난이도**: 중간~높음 | **사용 빈도**: ★★★☆☆

```kotlin
// Bad: ReadOnlyList 가 List 를 상속해 add() 거부
open class MutableList<T> {
    open fun add(item: T) { /* ... */ }
    open fun get(i: Int): T { /* ... */ TODO() }
}
class ReadOnlyList<T> : MutableList<T>() {
    override fun add(item: T) { throw UnsupportedOperationException() }  // LSP 위반
}

// Good: 위임 + 인터페이스 분리
interface Readable<T> { fun get(i: Int): T }
interface Writable<T> { fun add(item: T) }
class MutableList<T> : Readable<T>, Writable<T> { /* ... */ }
class ReadOnlyList<T>(private val src: Readable<T>) : Readable<T> by src  // 위임
```

**관련 스멜 / 원칙**:
- [lsp](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙), [isp](solid.md#4-interface-segregation-principle-isp-인터페이스-분리-원칙)
- Composition over Inheritance

---

<a id="9-alternative-classes-with-different-interfaces"></a>

## 9. Alternative Classes with Different Interfaces (다른 인터페이스의 대체 클래스)

**그룹**: OO Abuser

**식별 신호**:
- 두 클래스가 **거의 같은 일** 을 하는데 **메서드 이름 / 시그니처가 다름** (`User.fetchAll()` vs `Customer.getList()`)
- 호출 측이 클래스 별로 분기해 다른 API 호출
- 같은 도메인 개념인데 팀이 달라서 따로 만든 흔적

**원인**: 의사소통 부족, 코드 베이스 발견 실패, 외부 라이브러리 wrapping 시 표준화 누락.

**영향**: 통일된 polymorphism 불가, 중복 학습 비용, 한쪽 변경 시 다른 쪽도 따로 수정.

**권장 리팩토링**:
- **Rename Function** + **Move Function** 으로 시그니처 통일
- **Extract Superclass** 또는 **Extract Interface** 로 공통 추상 도입
- 통일 후 **Replace Conditional with Polymorphism** 적용 가능

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

```java
// Bad: 같은 역할인데 API 가 다름
class JsonReader { public Data read(String path) { /* ... */ } }
class XmlLoader  { public Data load(File f)     { /* ... */ } }
// 호출: if (type == "json") jr.read(p); else xl.load(new File(p));

// Good: 공통 인터페이스 도입 + 시그니처 통일
interface DataSource { Data read(String path); }
class JsonReader implements DataSource { public Data read(String p) { /* ... */ } }
class XmlReader   implements DataSource { public Data read(String p) { /* ... */ } }
```

**관련 스멜 / 원칙**:
- [code-smell-duplicate-code](#14-duplicate-code)
- [ocp](solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙), Strategy

---

<a id="10-divergent-change"></a>
## 10. Divergent Change (발산하는 변경)

**그룹**: Change Preventer

**식별 신호**:
- "DB 컬럼 추가하려면 X 클래스, 결제 규칙 바꾸려면 X 클래스, UI 라벨 바꾸려면 X 클래스" — **한 클래스가 여러 변경 축에 의해 수정됨**
- 같은 클래스 commit log 에 무관한 이유들이 섞임 (`feat(db)`, `feat(ui)`, `feat(payment)`)

**원인**: SRP 위반. 클래스가 여러 액터의 요구를 한꺼번에 처리.

**영향**: 변경 시 무관한 책임에 회귀 위험, 테스트 격리 불가, 병렬 작업 시 머지 충돌.

**권장 리팩토링**:
- **Split Phase** (단계별 분리: 파싱 → 검증 → 처리)
- **Move Function** (다른 클래스로 이동)
- **Extract Class** (책임 축 별로 분리)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```kotlin
// Bad: OrderService 가 DB 스키마/결제 규칙/포맷 모두 의존
class OrderService {
    fun save(o: Order) {
        // DB 스키마 변경 시 수정
        db.execute("INSERT INTO orders(id, total, ...) VALUES(...)")
        // 결제 규칙 변경 시 수정
        val fee = if (o.total > 10000) o.total * 0.02 else 100.0
        // UI 포맷 변경 시 수정
        log.info("주문 ${o.id}: ${"%,d".format(o.total)}원")
    }
}

// Good: 책임 축 별 분리
class OrderRepository    { fun save(o: Order) { /* DB */ } }
class FeeCalculator      { fun calculate(o: Order): Double { /* 결제 */ } }
class OrderLogFormatter  { fun format(o: Order): String { /* UI */ } }
class OrderService(val repo: OrderRepository, val fee: FeeCalculator, val fmt: OrderLogFormatter)
```

**관련 스멜 / 원칙**:
- [code-smell-shotgun-surgery](#11-shotgun-surgery) (정반대 — 한 변경이 여러 클래스에 퍼지는 경우)
- [srp](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙)

---

<a id="11-shotgun-surgery"></a>
## 11. Shotgun Surgery (산탄총 수술)

**그룹**: Change Preventer

**식별 신호**:
- **한 가지 변경** 을 위해 **여러 클래스 / 파일을 동시에 수정** 해야 함 (예: 통화 형식 바꾸려면 30 파일 수정)
- IDE 의 "Find Usages" 결과가 항상 두 자릿수
- 같은 키 (예: type code) 가 여러 곳에 흩어져 있음

**원인**: 응집도 부족 + Divergent Change 의 정반대 — 같이 변할 코드가 여기저기 흩어짐.

**영향**: 변경 누락 위험 (한 곳을 빼먹음), 테스트 범위 추정 어려움, 신규 개발자 학습 비용 ↑.

**권장 리팩토링**:
- **Move Function / Move Field** (같이 변할 코드를 한 곳에 모음)
- **Combine Functions into Class** (분산된 함수 → 클래스)
- **Inline Function / Inline Class** (불필요한 분산 제거)
- **Split Phase** 후 같은 단계끼리 모음

**난이도**: 중간~높음 | **사용 빈도**: ★★★★☆

```kotlin
// Bad: 통화 포맷이 5 군데에 흩어짐
class OrderView   { fun render(o: Order) = "₩${"%,d".format(o.total)}" }
class InvoicePdf  { fun amount(o: Order) = "₩${"%,d".format(o.total)}" }
class EmailNotice { fun body(o: Order) = "총 ₩${"%,d".format(o.total)}" }
class SmsNotice   { fun text(o: Order) = "${"%,d".format(o.total)}원" }
class Receipt     { fun line(o: Order) = "₩${"%,d".format(o.total)}" }
// 통화를 USD 도 지원하려면 5 군데 수정

// Good: 한 곳에 모음
object MoneyFormatter { fun format(money: Money) = "${money.symbol}${"%,d".format(money.amount)}" }
// 모든 호출자가 MoneyFormatter.format(o.total) 한 줄로 통일
```

**관련 스멜 / 원칙**:
- [code-smell-divergent-change](#10-divergent-change), [code-smell-repeated-switches](#6-repeated-switches)
- [high-cohesion](grasp.md#5-high-cohesion)

---

<a id="12-parallel-inheritance-hierarchies"></a>
## 12. Parallel Inheritance Hierarchies (평행 상속 계층)

**그룹**: Change Preventer

**식별 신호**:
- 한 상속 계층에 서브클래스를 추가하면 **다른 상속 계층에도 대응되는 서브클래스 를 같이 추가** 해야 함
- `Employee → Engineer/Manager` 와 `EmployeeView → EngineerView/ManagerView` 가 1:1 로 늘어남
- 두 계층의 prefix / suffix 가 동일

**원인**: 두 계층을 같이 변경하게 강제하는 분리 — 시스템이 같이 자라는 두 축을 *상속* 으로 표현해 결합도 ↑.

**영향**: Shotgun Surgery 가 상속 형태로 굳어짐. 한쪽 계층 변경 시 다른 쪽 수정 누락 위험.

**권장 리팩토링**:
- **Move Function / Move Field** 로 한쪽 계층의 책임을 다른 쪽에 흡수
- **Replace Inheritance with Delegation**
- Visitor 패턴 (계층 분리 유지하며 행위만 외부화)

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

```java
// Bad: 두 계층이 평행으로 자람
abstract class Shape { /* ... */ }
class Circle extends Shape { } class Square extends Shape { }
abstract class ShapeRenderer { /* ... */ }
class CircleRenderer extends ShapeRenderer { } class SquareRenderer extends ShapeRenderer { }
// 신규 Triangle 추가 시 TriangleRenderer 도 강제로 추가

// Good: Visitor 또는 Shape 내부에 render 흡수
abstract class Shape { abstract void render(Canvas c); }
class Circle extends Shape { void render(Canvas c) { /* ... */ } }
class Square extends Shape { void render(Canvas c) { /* ... */ } }
```

**관련 스멜 / 원칙**:
- [code-smell-shotgun-surgery](#11-shotgun-surgery)
- [lsp](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙), Visitor

---

## 13. Comments (불필요한 주석)

**그룹**: Dispensable

**식별 신호**:
- 주석이 **코드가 *무엇을* 하는지 설명** (코드를 그대로 한국어로 번역)
- 메서드 안의 단락 주석 (`// 검증`, `// 계산`) — Long Method 신호
- 오래된 주석이 현 코드와 불일치 (deodorant comment, Fowler)

**원인**: 자명한 이름·구조로 표현하지 못해 주석으로 메움. "주석을 쓰자" 는 의도는 좋지만 *코드 개선의 대체재* 가 되면 안 됨.

**영향**: 주석 ↔ 코드 불일치 (주석은 컴파일러가 검증하지 않음), 가독성 ↓ (시각적 잡음), 유지보수 시 양쪽 동기화 부담.

**권장 리팩토링**:
- **Extract Function** (단락 주석 → 자명한 이름의 메서드)
- **Rename Variable** (의도가 이름에 드러나게)
- **Introduce Assertion** (전제 조건 주석 → 실행 가능한 검증)

**예외**: *왜* (의도, 이유, 외부 제약, 라이선스) 를 적는 주석은 가치 있음. AGENTS.md 정책상 *한국어 함수 docstring* 은 필수.

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

```kotlin
// Bad: 코드가 무엇을 하는지 한국어로 재진술
fun calc(o: Order): Double {
    // 모든 아이템의 가격을 합산
    var total = 0.0
    for (item in o.items) total += item.price
    // VIP 면 10% 할인
    if (o.customer.isVip) total *= 0.9
    return total
}

// Good: 의도가 드러나는 이름 — 주석 불필요
fun calculateTotal(o: Order): Double {
    val subtotal = o.items.sumOf { it.price }
    return applyVipDiscount(subtotal, o.customer)
}
```

**관련 스멜 / 원칙**:
- [code-smell-long-method](#1-long-method) (단락 주석은 Extract Function 신호)
- Self-Documenting Code (Robert Martin, *Clean Code*)

---

## 14. Duplicate Code (중복 코드)

**그룹**: Dispensable

**식별 신호**:
- 같은 코드 블록이 **2 곳 이상** 에 복사 (DRY 위반)
- 비슷하지만 변수명만 다른 코드 (구조적 중복)
- 같은 알고리즘이 다른 메서드에 흩어짐

**원인**: 빠른 추가 ("일단 복붙"), 추출 위치 결정 어려움, 같은 도메인 개념을 못 본 채 작업.

**영향**: 버그 수정 누락 (한쪽만 고치고 다른 쪽 못 봄), 변경 비용 ↑, 일관성 ↓.

**권장 리팩토링**:
- **Extract Function** (같은 클래스 내 중복)
- **Pull Up Method** (자매 클래스 간 중복 → 부모로)
- **Form Template Method** (구조 동일·세부만 다른 경우)
- **Substitute Algorithm** (다른 알고리즘이지만 동일 결과 — 통합)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```python
# Bad: 같은 검증 로직 3 곳
def create_user(email, age):
    if "@" not in email: raise ValueError("이메일 형식 오류")
    if age < 0: raise ValueError("나이는 음수 불가")
    # ...
def update_user(email, age):
    if "@" not in email: raise ValueError("이메일 형식 오류")
    if age < 0: raise ValueError("나이는 음수 불가")
    # ...
def import_user(email, age):
    if "@" not in email: raise ValueError("이메일 형식 오류")
    if age < 0: raise ValueError("나이는 음수 불가")
    # ...

# Good: Extract Function
def validate_user_input(email: str, age: int) -> None:
    """사용자 입력 공통 검증 — 이메일 형식 및 나이 범위 확인"""
    if "@" not in email: raise ValueError("이메일 형식 오류")
    if age < 0: raise ValueError("나이는 음수 불가")

def create_user(email, age): validate_user_input(email, age); # ...
def update_user(email, age): validate_user_input(email, age); # ...
def import_user(email, age): validate_user_input(email, age); # ...
```

**관련 스멜 / 원칙**:
- [code-smell-alternative-classes-with-different-interfaces](#9-alternative-classes-with-different-interfaces)
- DRY (Don't Repeat Yourself, Pragmatic Programmer)

---

<a id="15-lazy-class"></a>
<a id="15-lazy-class-게으른-클래스"></a>
## 15. Lazy Class (게으른 클래스, aka Lazy Element)

**그룹**: Dispensable

**식별 신호**:
- 클래스가 **너무 작아서** 별도 존재 가치가 없음 (메서드 1~2 개, 단순 위임만)
- 한때 필요했지만 리팩토링으로 책임이 줄어들어 빈껍데기만 남음
- 이름만 있고 동작은 다른 클래스로 통째 위임

**원인**: 과도한 추상화, Speculative Generality 의 잔재, 리팩토링 후 정리 누락.

**영향**: 인지 부하 ↑ (필요 없는 클래스 학습), 네비게이션 비용 ↑.

**권장 리팩토링**:
- **Inline Class** (다른 클래스에 흡수)
- **Collapse Hierarchy** (불필요한 부모/자식 합침)

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

```java
// Bad: 단순 위임만 하는 빈껍데기
class CustomerName {
    private String value;
    public String getValue() { return value; }
}
class Customer {
    private CustomerName name;
    public String getName() { return name.getValue(); }  // 위임만
}

// Good: Inline Class
class Customer {
    private String name;
    public String getName() { return name; }
}
```

**관련 스멜 / 원칙**:
- [code-smell-speculative-generality](#18-speculative-generality), [code-smell-middle-man](#22-middle-man)
- YAGNI

---

<a id="16-data-class"></a>
## 16. Data Class (데이터 클래스)

**그룹**: Dispensable

**식별 신호**:
- 클래스가 **필드 + getter/setter 만** 보유, 동작 없음
- 다른 클래스가 이 클래스 필드를 가져다 모든 계산 수행 (Feature Envy 동반)
- Anemic Domain Model (Fowler 표현)

**원인**: 절차적 사고 + ORM/JSON binding 의 부산물. 데이터와 행위의 분리.

**영향**: 도메인 로직이 외부로 누출, 캡슐화 ↓, 같은 검증·계산이 여러 클라이언트에 중복.

**권장 리팩토링**:
- **Move Function** (이 클래스 필드를 쓰는 함수를 이 클래스로 이동)
- **Encapsulate Field** (직접 노출 → 캡슐화)
- **Encapsulate Collection** (mutable 컬렉션 노출 차단)
- **Remove Setting Method** (불변성 도입)

**예외**: **DTO / Record** 는 의도된 데이터 전송 객체이므로 스멜이 아님. 도메인 객체에서만 문제.

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```kotlin
// Bad: Order 는 데이터, 모든 로직이 외부 OrderService 에
class Order(val items: MutableList<Item>, var discount: Double, var status: String)
class OrderService {
    fun total(o: Order) = o.items.sumOf { it.price } * (1 - o.discount)
    fun cancel(o: Order) { o.status = "CANCELED" }
}

// Good: 행위를 도메인 객체로 이동
class Order(private val items: List<Item>, private val discount: Double) {
    var status: OrderStatus = OrderStatus.PENDING; private set
    fun total(): Double = items.sumOf { it.price } * (1 - discount)
    fun cancel() {
        require(status != OrderStatus.SHIPPED) { "배송 후 취소 불가" }
        status = OrderStatus.CANCELED
    }
}
```

**관련 스멜 / 원칙**:
- [code-smell-feature-envy](#19-feature-envy), [code-smell-primitive-obsession](#3-primitive-obsession)
- DDD Rich Domain Model, [information-expert](grasp.md#1-information-expert)

---

<a id="17-dead-code"></a>
## 17. Dead Code (죽은 코드)

**그룹**: Dispensable

**식별 신호**:
- **호출되지 않는** 함수 / 클래스 / 필드 / 변수
- 주석 처리된 코드 블록 (`// 이전 구현 ...`)
- feature flag 가 영구 off 인데 코드가 남음
- 도달 불가 분기 (조건이 항상 false)

**원인**: 리팩토링 후 정리 누락, "혹시 나중에" 보존 본능, 버전 관리 불신 (git 이 있는데도 주석 처리).

**영향**: 가독성 ↓, 학습 비용 ↑, IDE 검색 잡음, 유지보수 회의감.

**권장 리팩토링**:
- **Remove Dead Code** (그냥 삭제 — git 이 있으니 안전)
- IDE 의 "Unused" 경고 활용
- 정적 분석 도구 (detekt, SonarQube, ESLint `no-unused-vars`)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

```kotlin
// Bad: 호출 없는 함수, 주석 처리된 블록
class UserService {
    fun register(user: User) { /* ... */ }
    fun registerLegacy(user: User) { /* 어디서도 호출 안 됨 */ }
    /*
    fun registerV2(user: User) {
        // 옛날 구현, 혹시 모르니 남겨둠
    }
    */
    private val unusedField = 42
}

// Good: 그냥 삭제 (필요하면 git history 에서 복구)
class UserService {
    fun register(user: User) { /* ... */ }
}
```

**관련 스멜 / 원칙**:
- [code-smell-speculative-generality](#18-speculative-generality)
- YAGNI, Boy Scout Rule

---

<a id="18-speculative-generality"></a>
<a id="18-speculative-generality-과잉-일반화"></a>
## 18. Speculative Generality (추측성 일반화)

**그룹**: Dispensable

**식별 신호**:
- "나중에 필요할 수도 있으니" 만들어 둔 추상 클래스 / 인터페이스 / 훅 메서드
- 구현체가 **하나뿐인 인터페이스** (테스트 mock 제외)
- 사용되지 않는 generic 파라미터, 호출되지 않는 protected 메서드
- "확장 가능" 한 설계인데 확장된 적 없음

**원인**: "미래 대비" 라는 좋은 의도. 그러나 미래는 예측 불가하고 비대해진 추상은 *현재 코드를 복잡하게* 만든다.

**영향**: 인지 부하 ↑, 네비게이션 비용 ↑, 잘못된 방향으로 미리 추상화되어 *실제 변경* 시 더 큰 리팩토링 필요.

**권장 리팩토링**:
- **Collapse Hierarchy** (불필요한 상속 계층 제거)
- **Inline Function / Inline Class**
- **Remove Dead Code**
- **Change Function Declaration** (사용되지 않는 파라미터 제거)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```java
// Bad: "확장 대비" 추상 — 구현체는 하나뿐
abstract class AbstractReportGenerator<T extends Report, U extends Format> {
    abstract T generate(U format);
    protected void preHook() { } protected void postHook() { }
}
class PdfReportGenerator extends AbstractReportGenerator<PdfReport, PdfFormat> {
    PdfReport generate(PdfFormat f) { /* ... */ }
}
// 다른 Format/Report 가 추가된 적 없음

// Good: 단순화
class PdfReportGenerator {
    PdfReport generate() { /* ... */ }
}
// 실제로 두 번째 구현체가 필요해질 때 그때 추상화 (Rule of Three)
```

**관련 스멜 / 원칙**:
- [code-smell-lazy-class](#15-lazy-class), [code-smell-dead-code](#17-dead-code)
- YAGNI, Rule of Three

---

<a id="19-feature-envy"></a>
## 19. Feature Envy (기능 욕심)

**그룹**: Coupler

**식별 신호**:
- 메서드가 **자기 클래스보다 다른 클래스의 데이터** 를 더 많이 사용
- `other.getX() + other.getY() * other.getZ()` 같은 패턴
- 한 메서드가 다른 객체의 getter 를 3 회 이상 호출

**원인**: 정보가 있는 곳에 행위를 두지 않음 (Information Expert 위반). 절차적 사고 + Data Class 동반.

**영향**: 낮은 응집도, 높은 결합도, 도메인 객체의 빈혈 (Anemic Model).

**권장 리팩토링**:
- **Move Function** (해당 메서드를 데이터가 있는 클래스로 이동)
- **Extract Function** + **Move Function** (관련 부분만 이동)
- **Move Field** (필드 자체를 다른 클래스로)

**예외**: Strategy / Visitor 패턴은 의도적으로 데이터와 행위를 분리 — 스멜이 아니라 설계 의도.

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★★

```kotlin
// Bad: Invoice 가 Customer 의 데이터를 다 가져와 계산
class Customer(val name: String, val country: String, val loyalty: Int)
class Invoice {
    fun discount(c: Customer): Double {
        var d = 0.0
        if (c.country == "KR") d += 0.05
        if (c.loyalty > 100) d += 0.05
        if (c.loyalty > 500) d += 0.1
        return d
    }
}

// Good: Move Function — Customer 가 자기 할인을 계산
class Customer(val name: String, val country: String, val loyalty: Int) {
    fun discountRate(): Double {
        var d = 0.0
        if (country == "KR") d += 0.05
        if (loyalty > 100) d += 0.05
        if (loyalty > 500) d += 0.1
        return d
    }
}
class Invoice { fun discount(c: Customer) = c.discountRate() }
```

**관련 스멜 / 원칙**:
- [code-smell-data-class](#16-data-class), [code-smell-inappropriate-intimacy](#20-inappropriate-intimacy)
- [information-expert](grasp.md#1-information-expert), [low-coupling](grasp.md#4-low-coupling)

---

<a id="20-inappropriate-intimacy"></a>
## 20. Inappropriate Intimacy (부적절한 친밀성)

**그룹**: Coupler

**식별 신호**:
- 두 클래스가 **서로의 private 필드 / 내부 구조에 의존**
- 양방향 참조 (`A.b: B`, `B.a: A`)
- friend / package-private 노출이 과도

**원인**: 책임 분배 모호, 리팩토링 누락, 양방향 관계가 도메인 요구라기보다 기술 편의.

**영향**: 한쪽 변경이 다른 쪽에 즉시 전파, 단독 테스트 불가, 순환 참조로 모듈화 어려움.

**권장 리팩토링**:
- **Move Function / Move Field** (책임 재배치)
- **Change Bidirectional Association to Unidirectional** (양방향 → 단방향)
- **Extract Class** (공통 책임 → 제3 클래스)
- **Hide Delegate** (위임 캡슐화)
- **Replace Inheritance with Delegation** (상속 관계의 친밀성)

**난이도**: 중간~높음 | **사용 빈도**: ★★★☆☆

```kotlin
// Bad: Order 와 Customer 가 서로의 내부 상태에 직접 접근
class Customer(val id: String) {
    val orders = mutableListOf<Order>()
    fun totalSpend() = orders.sumOf { it.itemsInternal.sumOf { it.price } }  // 내부 접근
}
class Order(val customer: Customer) {
    val itemsInternal = mutableListOf<Item>()  // 노출됨
    init { customer.orders.add(this) }         // 양방향
}

// Good: 단방향 + 캡슐화
class Customer(val id: String) {
    fun totalSpend(orders: List<Order>) = orders.filter { it.customerId == id }.sumOf { it.total() }
}
class Order(val customerId: String, private val items: List<Item>) {
    fun total() = items.sumOf { it.price }  // 내부 비공개
}
```

**관련 스멜 / 원칙**:
- [code-smell-feature-envy](#19-feature-envy), [code-smell-message-chains](#21-message-chains)
- [low-coupling](grasp.md#4-low-coupling), [dip](solid.md#5-dependency-inversion-principle-dip-의존-역전-원칙)

---

<a id="21-message-chains"></a>
## 21. Message Chains (메시지 체인)

**그룹**: Coupler

**식별 신호**:
- `a.getB().getC().getD().getName()` 같은 **3 단계 이상 체이닝**
- "Law of Demeter" 위반 ("자신의 친구하고만 이야기하라")
- 호출자가 중간 객체들의 타입을 모두 알아야 함

**원인**: 캡슐화 부족, 도우미 메서드 미제공, 자료구조를 그대로 노출.

**영향**: 중간 객체의 구조가 바뀌면 호출자 모두 영향. 결합도 ↑, 단위 테스트 어려움 (mock 체인 필요).

**권장 리팩토링**:
- **Hide Delegate** (중간 객체를 숨기는 메서드 추가)
- **Extract Function** (체인 부분 추출 후 의미 있는 이름)
- **Move Function** (체인 끝의 행위를 시작 객체 쪽으로 이동)

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★☆

```java
// Bad: 4 단계 체인 — Demeter 위반
String managerName = order.getCustomer().getCompany().getManager().getName();

// 중간 객체 (Customer, Company, Manager) 의 구조가 바뀌면 호출부 다 수정

// Good: Hide Delegate
class Order {
    public String getManagerName() { return customer.getManagerName(); }
}
class Customer {
    public String getManagerName() { return company.getManagerName(); }
}
class Company {
    public String getManagerName() { return manager.getName(); }
}
// 호출: order.getManagerName()
```

**관련 스멜 / 원칙**:
- [code-smell-inappropriate-intimacy](#20-inappropriate-intimacy), [code-smell-middle-man](#22-middle-man) (Hide Delegate 가 과하면 Middle Man 됨)
- Law of Demeter, [low-coupling](grasp.md#4-low-coupling)
- 별칭: Spaghetti Code (체인이 전반에 퍼진 경우)

---

<a id="22-middle-man"></a>
## 22. Middle Man (중개자)

**그룹**: Coupler

**식별 신호**:
- 클래스의 메서드 **절반 이상이 단순 위임** (`return delegate.doX()`)
- 클래스가 자신의 행위는 없고 다른 객체로 forwarding 만 함
- "껍데기" 같은 wrapper

**원인**: Hide Delegate 를 과하게 적용, 리팩토링 잔재, 잘못된 Facade 적용.

**영향**: 추가 호출 비용, 인지 부하 (위임만 하는 클래스 학습 필요).

**권장 리팩토링**:
- **Remove Middle Man** (호출자가 직접 delegate 와 통신)
- **Inline Function** (위임 메서드 인라인)
- **Replace Superclass with Delegate** (잘못된 상속 → 위임)

**예외**: **Proxy / Decorator / Adapter / Facade** 는 의도된 중개 — 횡단 관심사(로깅·인증)나 인터페이스 변환이 있으면 스멜이 아님.

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

```java
// Bad: Person 의 메서드 대부분이 Department 로 단순 위임
class Person {
    private Department department;
    public Manager getManager()   { return department.getManager(); }
    public String getDeptName()   { return department.getName(); }
    public String getDeptCode()   { return department.getCode(); }
    public int getDeptHeadCount() { return department.getHeadCount(); }
}

// Good: Remove Middle Man — 호출자가 직접
class Person {
    public Department getDepartment() { return department; }
}
// 호출: person.getDepartment().getName()
// 단, Demeter 가 걱정되면 Person 에 *의미 있는* 메서드만 남기고 나머지는 제거
```

**관련 스멜 / 원칙**:
- [code-smell-message-chains](#21-message-chains) (Hide Delegate 과용의 반대 극단)
- [code-smell-lazy-class](#15-lazy-class)

---

<a id="5-그룹-진입점"></a>
### 5 그룹 진입점

| 그룹 | 의미 | 스멜 |
|------|------|------|
| Bloaters | 비대화: 코드가 너무 커진 상태 | Long Method (1), Large Class (2), Primitive Obsession (3), Long Parameter List (4), Data Clumps (5) |
| OO Abusers | OO 원리 위반 | Repeated Switches (6), Switch Statements (7), Refused Bequest (8), Alternative Classes with Different Interfaces (9) |
| Change Preventers | 변경 시 비용 폭증 | Divergent Change (10), Shotgun Surgery (11), Parallel Inheritance Hierarchies (12) |
| Dispensables | 없어도 되는 코드 | Comments (13), Duplicate Code (14), Lazy Class (15), Data Class (16), Dead Code (17), Speculative Generality (18) |
| Couplers | 과도한 결합 | Feature Envy (19), Inappropriate Intimacy (20), Message Chains (21), Middle Man (22) |

---

## 표준 인용

- Martin Fowler, *Refactoring: Improving the Design of Existing Code*, 2nd ed. (2018), Chapter 3 "Bad Smells in Code", Addison-Wesley
- Martin Fowler, William Opdyke, John Brant, Don Roberts, *Refactoring* 1st ed. (1999) — 22 스멜 원전
- Kent Beck — *Implementation Patterns* (2007) — Fowler 인용 source
- Robert C. Martin, *Clean Code* (2008) — 코드 스멜 + 휴리스틱 17 카테고리 (참조 cross-reference)
