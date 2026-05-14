# Refactoring 기법 (Refactoring Techniques)

Martin Fowler *Refactoring: Improving the Design of Existing Code*, 2nd ed. (2018) Chapter 6~12 catalog 60+ 항목 중 **핵심 25 기법**. [`code-smells.md`](code-smells.md) (증상 22) 와 짝을 이루는 *처방* 카탈로그.

**원전**:
- Martin Fowler — *Refactoring: Improving the Design of Existing Code*, 2nd ed. (2018), Addison-Wesley
- Martin Fowler — *Refactoring* 1st ed. (1999)
- Joshua Kerievsky — *Refactoring to Patterns* (2004)
- Michael Feathers — *Working Effectively with Legacy Code* (2004) (보강)

**핵심 원칙**:
- **작은 단계 (Small Steps)** — 각 리팩토링은 *행동 보존* (behavior-preserving) 변환. 테스트 PASS 상태 유지.
- **2 hat (Two Hats)** — *기능 추가* 와 *리팩토링* 을 동시 진행 금지. 한 번에 하나의 모자만.
- **Opportunistic** — 변경이 들어왔을 때 같이 정리 (Boy Scout Rule).

**Smell → Technique 매핑**:

| 스멜 | 권장 기법 |
|------|----------|
| Long Method | Extract Function / Replace Temp with Query / Decompose Conditional |
| Large Class | Extract Class / Extract Superclass / Extract Subclass |
| Long Parameter List | Introduce Parameter Object / Preserve Whole Object |
| Duplicated Code | Extract Function / Pull Up Method / Form Template Method |
| Switch Statement | Replace Conditional with Polymorphism / Replace Type Code with Subclasses |
| Feature Envy | Move Function / Move Field / Extract Function |
| Data Class | Encapsulate Record / Push Down Method |
| Refused Bequest | Push Down Method/Field / Replace Subclass with Delegate |
| Primitive Obsession | Replace Primitive with Object / Replace Type Code with Subclasses |
| Middle Man | Remove Middle Man / Inline Function |
| Message Chains | Hide Delegate / Extract Function |
| Comments | Extract Function / Rename Variable / Change Function Declaration |

---

<a id="extract-function"></a>
## 1. Extract Function

**언제 적용**: [Long Method](code-smells.md#1-long-method-긴-메서드) / [Duplicate Code](code-smells.md#14-duplicate-code-중복-코드) / [Comments](code-smells.md#13-comments-불필요한-주석) — 코드 단락을 주석으로 구분하고 있다면 그 자체가 추출 신호.

**기법 요약**: 한 메서드 안의 *목적이 분리된* 코드 블록을 새 메서드(함수)로 빼내고 원래 위치는 호출문으로 대체. Fowler 가 *"가장 자주 쓰는 리팩토링"* 으로 꼽은 1번 기법. "코드를 보고 *무엇을* 하는지 즉시 이해되지 않으면 추출하라."

**적용 절차**:
1. 새 함수를 만들고 *의도* 를 드러내는 이름을 붙임 (구현이 아니라 목적 기반)
2. 추출할 코드를 원본에서 새 함수로 복사
3. 추출된 코드 내부의 지역 변수 / 매개변수를 새 함수 시그니처에 반영 (외부 변수 → 인자, 새로 만들어진 값 → 반환값)
4. 컴파일
5. 원본 위치를 새 함수 호출문으로 교체
6. 테스트 PASS 확인

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Before
fun printOwing(invoice: Invoice) {
    println("***** Customer Owes *****")
    println("Name: ${invoice.customer.name}")

    // calculate outstanding
    var outstanding = 0.0
    for (o in invoice.orders) outstanding += o.amount
    println("Amount: $outstanding")
}

// After
fun printOwing(invoice: Invoice) {
    printBanner()
    val outstanding = calculateOutstanding(invoice)
    printDetails(invoice, outstanding)
}

private fun printBanner() {
    println("***** Customer Owes *****")
}

private fun calculateOutstanding(invoice: Invoice): Double =
    invoice.orders.sumOf { it.amount }

private fun printDetails(invoice: Invoice, outstanding: Double) {
    println("Name: ${invoice.customer.name}")
    println("Amount: $outstanding")
}
```

**역리팩토링**: [Inline Function](#inline-function)

**관련 기법 / 스멜**:
- [code-smell-long-method](code-smells.md#1-long-method-긴-메서드), [code-smell-duplicate-code](code-smells.md#14-duplicate-code-중복-코드)
- [Replace Temp with Query] (본 카탈로그 외 Fowler 항목)
- [srp](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙), [high-cohesion](grasp.md#5-high-cohesion)

---

<a id="inline-function"></a>
## 2. Inline Function

**언제 적용**: 함수 본문이 *이름만큼 명확* 하거나 더 명확할 때 / 잘못 추출한 함수가 추상화에 도움이 안 될 때 / 여러 작은 함수 사이에서 책임이 흩어져 가독성이 더 떨어졌을 때.

**기법 요약**: 호출문을 함수 본문으로 치환하고 함수 정의 제거. Extract Function 의 역방향. 추출이 과한 경우의 교정 수단이자 *대규모 재구성 전 일단 한 곳으로 모아 다시 추출* 하는 전처리로도 쓰임.

**적용 절차**:
1. 다형 메서드(서브클래스 오버라이드) 가 아닌지 확인 — 다형이면 inline 금지
2. 모든 호출 위치를 찾음
3. 각 호출문을 함수 본문으로 치환
4. 매 치환마다 테스트
5. 모든 호출 치환 완료 후 함수 정의 삭제

**난이도**: 낮음~중간 (다형 / 재귀 / 다중 return 시 중간) | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Before — 함수가 본문보다 더 길게 설명되지 않음
fun getRating(driver: Driver): Int =
    if (moreThanFiveLateDeliveries(driver)) 2 else 1

private fun moreThanFiveLateDeliveries(driver: Driver): Boolean =
    driver.numberOfLateDeliveries > 5

// After — Inline 으로 의도 직접 노출
fun getRating(driver: Driver): Int =
    if (driver.numberOfLateDeliveries > 5) 2 else 1
```

**역리팩토링**: [Extract Function](#extract-function)

**관련 기법 / 스멜**:
- [code-smell-middle-man](code-smells.md#22-middle-man-중개자), [code-smell-speculative-generality](code-smells.md#18-speculative-generality-추측성-일반화)
- [Remove Middle Man](#remove-middle-man)

---

<a id="extract-variable"></a>
## 3. Extract Variable

**언제 적용**: 복잡한 표현식 (산술 / boolean / 메서드 체인) 의 *부분 의미* 를 드러내고 싶을 때. *Introduce Explaining Variable* 의 새 이름. 디버깅에서 중간 값 관찰이 필요할 때도 유용.

**기법 요약**: 표현식의 일부에 의미 있는 이름의 지역 변수를 도입. 원전 표현식 자리에 변수 참조로 치환. 코드 자체를 *주석으로 풀어 쓰기* 와 같은 효과.

**적용 절차**:
1. 표현식이 부수효과 없는지 확인
2. 변경 불가(immutable) 지역 변수 선언 후 표현식 일부 대입
3. 원래 표현식 자리에 변수 참조 치환
4. 테스트

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Before — 한 줄에 4개의 산술 + 비교 + 단가 + 할인
fun price(order: Order): Double =
    order.quantity * order.itemPrice -
        maxOf(0, order.quantity - 500) * order.itemPrice * 0.05 +
        minOf(order.quantity * order.itemPrice * 0.1, 100.0)

// After — Extract Variable
fun price(order: Order): Double {
    val basePrice = order.quantity * order.itemPrice
    val quantityDiscount = maxOf(0, order.quantity - 500) * order.itemPrice * 0.05
    val shipping = minOf(basePrice * 0.1, 100.0)
    return basePrice - quantityDiscount + shipping
}
```

**역리팩토링**: [Inline Variable](#inline-variable)

**관련 기법 / 스멜**:
- [code-smell-comments](code-smells.md#13-comments-불필요한-주석), [code-smell-long-method](code-smells.md#1-long-method-긴-메서드)
- [Extract Function](#extract-function) — 변수 범위를 메서드 밖으로 확장하고 싶을 때

---

<a id="inline-variable"></a>
## 4. Inline Variable

**언제 적용**: 변수 이름이 표현식 자체보다 더 설명적이지 않을 때 / 변수가 다른 리팩토링을 방해할 때 (예: Change Function Declaration 전에 임시 정리).

**기법 요약**: 변수 참조를 모두 원래 표현식으로 치환하고 변수 선언 삭제. Extract Variable 의 역방향.

**적용 절차**:
1. 변수에 대입되는 값이 *변경 없는 단일 표현식* 인지 확인
2. 첫 대입 이후 변수가 *재할당되지 않는지* 확인 (Kotlin `val` 권장)
3. 모든 참조를 원본 표현식으로 치환
4. 변수 선언 삭제
5. 테스트

**난이도**: 낮음 | **사용 빈도**: ★★

**Kotlin 예제**:
```kotlin
// Before — basePrice 가 한 줄짜리 표현식 그대로
fun isOverPriced(order: Order): Boolean {
    val basePrice = order.basePrice
    return basePrice > 1000
}

// After — Inline Variable
fun isOverPriced(order: Order): Boolean =
    order.basePrice > 1000
```

**역리팩토링**: [Extract Variable](#extract-variable)

**관련 기법 / 스멜**:
- [code-smell-comments](code-smells.md#13-comments-불필요한-주석) (불필요 변수 이름이 *주석성 noise* 일 때)
- [Change Function Declaration](#change-function-declaration) 전 전처리

---

<a id="change-function-declaration"></a>
## 5. Change Function Declaration

**언제 적용**: 함수 이름이 의도를 못 살릴 때 / 매개변수가 잘못된 수준의 추상화 / 매개변수 추가·삭제·재정렬이 필요할 때. *Rename Function*, *Add Parameter*, *Remove Parameter*, *Change Signature* 를 통합한 상위 카테고리.

**기법 요약**: 함수의 시그니처(이름·매개변수·반환 타입)를 변경. *단순 절차* (호출자 ≤ 5) 와 *마이그레이션 절차* (호출자 다수·외부 API) 두 가지가 있음.

**적용 절차** (마이그레이션 절차 — 안전):
1. 함수 본문의 사용처가 호출자에게 영향을 주지 않게 추출(Extract Function) 가능하면 추출
2. **새 함수** 를 새 이름·새 시그니처로 추가 (옛 함수 본문은 새 함수에 위임)
3. 옛 함수에 `@Deprecated` 표시
4. 호출자를 한 번에 하나씩 새 함수로 옮김. 매 호출자마다 테스트
5. 옛 함수 삭제
6. 새 함수가 옛 이름이 더 어울리면 다시 rename

**적용 절차** (단순 절차):
1. IDE Rename / Change Signature refactoring 사용
2. 컴파일 + 테스트

**난이도**: 낮음(IDE) ~ 중간(마이그레이션) | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Before
fun circum(radius: Double): Double = 2 * Math.PI * radius

// After — 이름이 의도를 드러내도록 변경
fun circumference(radius: Double): Double = 2 * Math.PI * radius

// 매개변수 추가 — 마이그레이션 절차
// Step 1: 새 함수 추가, 옛 함수 위임
@Deprecated("Use addressFor(customer, country)", ReplaceWith("addressFor(customer, country)"))
fun addressFor(customer: Customer): Address =
    addressFor(customer, defaultCountry)

fun addressFor(customer: Customer, country: Country): Address {
    // 새 본문
    return Address(customer.street, customer.city, country)
}
```

**역리팩토링**: 없음 (역방향도 동일하게 *Change Function Declaration*)

**관련 기법 / 스멜**:
- [code-smell-long-parameter-list](code-smells.md#4-long-parameter-list-긴-파라미터-리스트), [code-smell-data-clumps](code-smells.md#5-data-clumps-데이터-뭉치)
- [Introduce Parameter Object](#introduce-parameter-object), [Rename Variable](#rename-variable)

---

<a id="encapsulate-variable"></a>
## 6. Encapsulate Variable

**언제 적용**: 전역 / 모듈 수준 변수에 직접 접근하는 코드가 곳곳에 있을 때 / 자료 구조 변경을 앞두고 *경계 통제* 가 필요할 때. *Self-Encapsulate Field* 의 일반화.

**기법 요약**: 데이터 직접 접근을 *getter / setter* (또는 property) 경유로 통일. 캡슐화는 *데이터 구조 변경의 디딤돌* — 게이트가 있어야 형태 변환을 한 곳에서 처리 가능.

**적용 절차**:
1. getter / setter 함수를 추가 (Kotlin 의 경우 `private set` + 백킹 필드 패턴)
2. 모든 직접 참조를 getter / setter 호출로 치환. 매 치환마다 테스트
3. 변수의 접근자를 private 로 좁힘
4. 컴파일 / 테스트
5. 자료 구조 변경이 목적이면 이제 안전하게 진행 (Encapsulate Record / Encapsulate Collection 으로 이어짐)

**난이도**: 낮음 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Before — 전역 가변 데이터에 직접 접근
object DefaultOwner {
    var data = mutableMapOf("name" to "Martin", "id" to "1234")
}
// 호출처
DefaultOwner.data["name"] = "Rebecca"

// After — Encapsulate Variable
object DefaultOwner {
    private var _data = mutableMapOf("name" to "Martin", "id" to "1234")

    fun get(): Map<String, String> = _data.toMap()    // 방어 복사
    fun set(arg: Map<String, String>) {
        _data = arg.toMutableMap()
    }
}
// 호출처 — getter / setter 경유
DefaultOwner.set(DefaultOwner.get() + ("name" to "Rebecca"))
```

**역리팩토링**: 없음 (캡슐화 해제는 권장되지 않음)

**관련 기법 / 스멜**:
- [code-smell-data-class](code-smells.md#16-data-class-데이터-클래스)
- [Encapsulate Record](#encapsulate-record), [Encapsulate Collection](#encapsulate-collection)
- [information-expert](grasp.md#1-information-expert), [protected-variations](grasp.md#9-protected-variations)

---

<a id="rename-variable"></a>
## 7. Rename Variable

**언제 적용**: 변수 / 필드 / 매개변수 / 함수 이름이 의도를 못 드러낼 때. *코드는 사람을 위해 쓴다* 는 Fowler 의 신조에서 가장 작은 단위의 실천.

**기법 요약**: 식별자 이름을 의미가 명확한 이름으로 변경. IDE refactoring 으로 안전하게 일괄 처리.

**적용 절차**:
1. 변수의 사용 범위 확인 (지역 / 필드 / public API)
2. **지역 범위**: IDE rename → 컴파일 → 테스트
3. **public 필드/매개변수**: Encapsulate Variable 먼저 적용해 게이트 확보 후 rename, 외부에는 옛 이름 alias 유지
4. 매 단계마다 테스트

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Before — 의도 불명확
fun process(a: List<Int>): Int {
    var s = 0
    for (i in a) s += i
    return s
}

// After — Rename Variable
fun process(numbers: List<Int>): Int {
    var total = 0
    for (n in numbers) total += n
    return total
}
```

**역리팩토링**: 없음 (역방향도 *Rename Variable*)

**관련 기법 / 스멜**:
- [code-smell-comments](code-smells.md#13-comments-불필요한-주석) (이름이 좋으면 주석 불필요)
- [Change Function Declaration](#change-function-declaration) (함수 이름 변경의 상위 카테고리)

---

<a id="introduce-parameter-object"></a>
## 8. Introduce Parameter Object

**언제 적용**: [Long Parameter List](code-smells.md#4-long-parameter-list-긴-파라미터-리스트) / [Data Clumps](code-smells.md#5-data-clumps-데이터-뭉치) — 매개변수 묶음이 함수 간에 같이 다닐 때.

**기법 요약**: 함께 다니는 매개변수들을 *Value Object* (Kotlin `data class`, Java `record`) 로 묶고 그 객체를 단일 매개변수로 전달. 묶음이 *도메인 개념* 임을 발견하는 계기이기도 함.

**적용 절차**:
1. 매개변수 묶음을 표현할 클래스 / record 정의 (값 객체 — 불변 권장)
2. Change Function Declaration 으로 새 매개변수 추가
3. 호출자를 새 객체 전달 방식으로 한 곳씩 이행. 매 호출자마다 테스트
4. 함수 본문에서 옛 개별 매개변수 사용을 새 객체 프로퍼티 사용으로 치환
5. 옛 매개변수 제거
6. 묶음이 *동작* 도 가지면 메서드 이동(Move Function) 으로 확장

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Before — Date 범위 매개변수가 여러 함수에 반복
fun amountInvoicedIn(startDate: LocalDate, endDate: LocalDate): Money { /* ... */ }
fun amountReceivedIn(startDate: LocalDate, endDate: LocalDate): Money { /* ... */ }
fun amountOverdueIn(startDate: LocalDate, endDate: LocalDate): Money { /* ... */ }

// After — Introduce Parameter Object
data class DateRange(val start: LocalDate, val end: LocalDate) {
    init { require(!end.isBefore(start)) { "end >= start" } }
    fun includes(date: LocalDate): Boolean =
        !date.isBefore(start) && !date.isAfter(end)
}

fun amountInvoicedIn(range: DateRange): Money { /* ... */ }
fun amountReceivedIn(range: DateRange): Money { /* ... */ }
fun amountOverdueIn(range: DateRange): Money { /* ... */ }
```

**역리팩토링**: 없음 (해체는 Change Function Declaration 으로 수동)

**관련 기법 / 스멜**:
- [code-smell-long-parameter-list](code-smells.md#4-long-parameter-list-긴-파라미터-리스트), [code-smell-data-clumps](code-smells.md#5-data-clumps-데이터-뭉치), [code-smell-primitive-obsession](code-smells.md#3-primitive-obsession-기본-타입-집착)
- [Combine Functions into Class](#combine-functions-into-class), [Replace Primitive with Object](#replace-primitive-with-object)
- DDD Value Object, [information-expert](grasp.md#1-information-expert)

---

<a id="combine-functions-into-class"></a>
## 9. Combine Functions into Class

**언제 적용**: 여러 함수가 *동일한 데이터* 를 매개변수로 받아 다른 작업을 수행할 때. 함수들이 *동일한 정보 그룹* 위에서 동작하면 그것은 객체로 묶일 신호.

**기법 요약**: 같은 데이터 위에서 동작하는 함수들과 그 데이터를 함께 새 클래스로 이동. 매개변수가 *암묵적 객체* 임을 명시화. DDD 의 Aggregate 또는 도메인 서비스로 발전.

**적용 절차**:
1. 함수들이 공유하는 데이터를 식별
2. 새 클래스 생성, 공유 데이터를 필드로 둠
3. 공유 데이터를 받는 함수 중 하나를 새 클래스의 메서드로 옮김 (Move Function)
4. 매개변수에서 옮긴 데이터 제거 → 인스턴스 필드 참조로 치환
5. 다른 함수도 동일하게 이동. 매 이동마다 테스트
6. 호출자를 새 클래스 인스턴스 메서드 호출로 변경

**난이도**: 중간 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Before — reading 매개변수가 세 함수 모두에 반복
data class Reading(val customer: String, val quantity: Int, val month: Int, val year: Int)

fun baseRate(month: Int, year: Int): Double { /* ... */ TODO() }
fun base(reading: Reading): Double = baseRate(reading.month, reading.year) * reading.quantity
fun taxableCharge(reading: Reading): Double = maxOf(0.0, base(reading) - taxThreshold(reading.year))
fun calculateBaseCharge(reading: Reading): Double = base(reading)
private fun taxThreshold(year: Int): Double = TODO()

// After — Combine Functions into Class
class Reading2(
    val customer: String,
    val quantity: Int,
    val month: Int,
    val year: Int,
) {
    val baseCharge: Double
        get() = baseRate(month, year) * quantity

    val taxableCharge: Double
        get() = maxOf(0.0, baseCharge - taxThreshold(year))

    private fun baseRate(month: Int, year: Int): Double = TODO()
    private fun taxThreshold(year: Int): Double = TODO()
}
```

**역리팩토링**: Move Function (메서드를 다시 외부 함수로)

**관련 기법 / 스멜**:
- [code-smell-data-class](code-smells.md#16-data-class-데이터-클래스), [code-smell-feature-envy](code-smells.md#19-feature-envy-기능-욕심)
- [Move Function](#move-function), [Combine Functions into Transform](#combine-functions-into-transform)
- [high-cohesion](grasp.md#5-high-cohesion), [information-expert](grasp.md#1-information-expert)

---

<a id="combine-functions-into-transform"></a>
## 10. Combine Functions into Transform

**언제 적용**: 어떤 원천 데이터에서 *파생값* 을 계산하는 함수가 여러 개 흩어져 있을 때. 데이터를 입력받아 *파생 필드를 추가한 새 데이터* 를 반환하는 변환기로 통일.

**기법 요약**: 함수들이 같은 입력에서 각자 파생값을 계산하면, 입력을 받아 모든 파생값을 채워 *enriched* 출력을 반환하는 *transform 함수* 로 묶음. 파이프라인 / 함수형 스타일에 적합. Combine Functions into Class 의 *불변 데이터 버전*.

**적용 절차**:
1. 변환할 입력 데이터를 식별 (보통 read-only record / DTO)
2. 입력을 받아 *deep copy* (또는 record 복제) 해서 반환하는 transform 함수 작성
3. 각 파생 계산 함수를 transform 안으로 이동. 출력 record 에 파생 필드 추가
4. 옛 계산 함수의 호출자를 transform 결과의 필드 참조로 치환. 매 호출자마다 테스트
5. 옛 함수 제거

**난이도**: 중간 | **사용 빈도**: ★★

**Kotlin 예제**:
```kotlin
// Before — 파생값 함수가 각각 호출
data class Reading(val customer: String, val quantity: Int, val month: Int, val year: Int)

fun base(r: Reading): Double = 0.0
fun taxableCharge(r: Reading): Double = 0.0
// 호출처
val r = Reading("c1", 100, 5, 2026)
val total = base(r) + taxableCharge(r)

// After — Combine Functions into Transform
data class EnrichedReading(
    val customer: String,
    val quantity: Int,
    val month: Int,
    val year: Int,
    val baseCharge: Double,
    val taxableCharge: Double,
)

fun enrichReading(original: Reading): EnrichedReading {
    val baseCharge = original.quantity * baseRate(original.month, original.year)
    val taxable = maxOf(0.0, baseCharge - taxThreshold(original.year))
    return EnrichedReading(
        original.customer, original.quantity, original.month, original.year,
        baseCharge = baseCharge, taxableCharge = taxable,
    )
}
private fun baseRate(month: Int, year: Int): Double = 0.0
private fun taxThreshold(year: Int): Double = 0.0
```

**역리팩토링**: 없음 (개별 함수로 풀려면 Inline)

**관련 기법 / 스멜**:
- [code-smell-duplicate-code](code-smells.md#14-duplicate-code-중복-코드)
- [Combine Functions into Class](#combine-functions-into-class), [Split Phase](#split-phase)

---

<a id="split-phase"></a>
## 11. Split Phase

**언제 적용**: 한 함수가 *서로 다른 단계* (예: parse → transform → format) 의 일을 섞어서 처리할 때. 단계별로 변경 이유가 다르면(SRP 위반) 분리할 신호.

**기법 요약**: 한 처리 흐름을 *명시적 phase* 들로 분리하고 각 phase 가 자기 자료구조 (intermediate data structure) 위에서만 동작하게 함. compiler pipeline 의 lex → parse → codegen 처럼.

**적용 절차**:
1. 처리 흐름에서 *경계* 가 되는 지점 식별 (보통 자료 변환이 일어나는 곳)
2. 경계 이후 코드를 새 함수로 추출 (Extract Function)
3. 두 함수 사이를 흐르는 데이터를 *중간 데이터 구조* (보통 record/data class) 로 캡슐화
4. 첫 phase 의 입력 매개변수를 검토하여 두 번째 phase 가 정말 필요한 것만 남도록 정리
5. 테스트

**난이도**: 중간~높음 | **사용 빈도**: ★★

**Kotlin 예제**:
```kotlin
// Before — 한 함수에 가격 파싱 + 배송 계산 + 최종 출력 혼재
fun priceOrder(product: Product, quantity: Int, shippingMethod: ShippingMethod): Double {
    val basePrice = product.basePrice * quantity
    val discount = maxOf(quantity - product.discountThreshold, 0) *
        product.basePrice * product.discountRate
    val shippingPerCase = if (basePrice > shippingMethod.discountThreshold)
        shippingMethod.discountedFee else shippingMethod.feePerCase
    val shippingCost = quantity * shippingPerCase
    return basePrice - discount + shippingCost
}

// After — Split Phase: priceData(중간 구조) → applyShipping
data class PriceData(val basePrice: Double, val quantity: Int, val discount: Double)

fun priceOrder2(product: Product, quantity: Int, shippingMethod: ShippingMethod): Double {
    val priceData = calculatePricingData(product, quantity)   // phase 1
    return applyShipping(priceData, shippingMethod)            // phase 2
}

private fun calculatePricingData(product: Product, quantity: Int): PriceData {
    val basePrice = product.basePrice * quantity
    val discount = maxOf(quantity - product.discountThreshold, 0) *
        product.basePrice * product.discountRate
    return PriceData(basePrice, quantity, discount)
}

private fun applyShipping(p: PriceData, m: ShippingMethod): Double {
    val shippingPerCase = if (p.basePrice > m.discountThreshold) m.discountedFee else m.feePerCase
    val shippingCost = p.quantity * shippingPerCase
    return p.basePrice - p.discount + shippingCost
}
```

**역리팩토링**: 없음 (단계 통합은 Inline 으로 수동)

**관련 기법 / 스멜**:
- [code-smell-long-method](code-smells.md#1-long-method-긴-메서드), [code-smell-divergent-change](code-smells.md#10-divergent-change-발산하는-변경)
- [Combine Functions into Transform](#combine-functions-into-transform), [Extract Function](#extract-function)
- [srp](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙)

---

<a id="encapsulate-record"></a>
## 12. Encapsulate Record

**언제 적용**: 외부에 *raw record* (Map / dict / 익명 객체) 를 그대로 노출하고 있을 때. 자료 구조 변경의 영향이 곳곳에 퍼지는 위험을 사전 차단. *Replace Record with Data Class* 의 새 이름.

**기법 요약**: 가변 raw record 를 정식 클래스로 감싸 *getter / setter* 경유 접근. 내부 표현은 자유롭게 바꿀 수 있게 됨 (예: 필드 → 계산값, Map 키 → 강타입 enum).

**적용 절차**:
1. record 를 만드는 코드를 클래스 생성자 호출로 캡슐화
2. record 를 직접 참조하던 코드를 클래스의 getter / setter 호출로 치환
3. 클래스 내부의 raw record 노출을 막음 (필요시 deep copy 반환)
4. 컴파일 / 테스트
5. 이제 내부 표현을 자유롭게 변경 (Map → 필드, primitive → Value Object)

**난이도**: 중간 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Before — Map 으로 organization 데이터 노출
val organization = mapOf("name" to "Acme Gooseberries", "country" to "GB")
// 호출처
val name = organization["name"] as String
println("client: $name")

// After — Encapsulate Record
class Organization(name: String, country: String) {
    var name: String = name
        private set
    var country: String = country
        private set

    fun setName(arg: String) { name = arg }
    fun setCountry(arg: String) { country = arg }
}

val org = Organization("Acme Gooseberries", "GB")
println("client: ${org.name}")
```

**역리팩토링**: 없음 (raw 노출 복귀는 권장 안 됨)

**관련 기법 / 스멜**:
- [code-smell-data-class](code-smells.md#16-data-class-데이터-클래스), [code-smell-primitive-obsession](code-smells.md#3-primitive-obsession-기본-타입-집착)
- [Encapsulate Variable](#encapsulate-variable), [Encapsulate Collection](#encapsulate-collection)
- [protected-variations](grasp.md#9-protected-variations)

---

<a id="encapsulate-collection"></a>
## 13. Encapsulate Collection

**언제 적용**: 클래스가 컬렉션(List / Set / Map) 을 getter 로 *직접 노출* 하여 외부에서 마음대로 add / remove 하는 경우. 컬렉션 무결성(invariant) 보장이 불가능해짐.

**기법 요약**: getter 는 *방어 복사* 또는 *읽기 전용 뷰* 만 반환. 변경은 클래스의 `add` / `remove` 메서드로만 가능. 컬렉션의 invariant (예: 정렬, 중복 없음, 최대 크기) 를 클래스가 보호.

**적용 절차**:
1. 컬렉션의 모든 외부 *변경 호출* 을 식별
2. 클래스에 `addX(x)` / `removeX(x)` 메서드 추가
3. 외부에서 일어나던 변경을 모두 새 메서드 호출로 치환. 매 치환마다 테스트
4. getter 가 방어 복사(`toList()` / `toSet()`) 또는 불변 뷰(`unmodifiableList` / Kotlin `List`) 를 반환하도록 변경
5. 컴파일 / 테스트
6. setter 가 있었다면 제거 (또는 입력을 복사해서 저장)

**난이도**: 중간 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Before — courses 가 가변으로 노출, 외부에서 add 가능
class Person(name: String) {
    val name = name
    var courses: MutableList<Course> = mutableListOf()
}
// 호출처 — invariant 깨질 위험
val person = Person("Kent")
person.courses.add(Course("Smalltalk", false))   // 외부에서 직접 변경

// After — Encapsulate Collection
class Person2(val name: String) {
    private val _courses: MutableList<Course> = mutableListOf()

    val courses: List<Course>                    // 불변 뷰만 노출
        get() = _courses.toList()

    fun addCourse(course: Course) {
        // invariant 적용 가능 (중복 방지 등)
        if (_courses.none { it.name == course.name }) {
            _courses.add(course)
        }
    }

    fun removeCourse(course: Course) {
        _courses.remove(course)
    }
}
```

**역리팩토링**: 없음

**관련 기법 / 스멜**:
- [code-smell-data-class](code-smells.md#16-data-class-데이터-클래스), [code-smell-inappropriate-intimacy](code-smells.md#20-inappropriate-intimacy-부적절한-친밀성)
- [Encapsulate Record](#encapsulate-record), [Encapsulate Variable](#encapsulate-variable)
- [information-expert](grasp.md#1-information-expert), [protected-variations](grasp.md#9-protected-variations)

---

<a id="replace-primitive-with-object"></a>
## 14. Replace Primitive with Object

**언제 적용**: [Primitive Obsession](code-smells.md#3-primitive-obsession-기본-타입-집착) — 도메인 개념을 `String` / `int` / `double` 같은 원시 타입으로 표현. 같은 값에 검증 / 변환 / 포맷 로직이 반복.

**기법 요약**: 원시 값을 도메인 의미의 작은 클래스(Value Object) 로 승격. 검증·연산·포맷이 그 클래스 안으로 모임. `Replace Type Code with Class` 의 일반화.

**적용 절차**:
1. Encapsulate Variable 로 원시 값 접근을 getter / setter 로 통일
2. 단순한 wrapper 클래스 생성 (불변 권장, 생성자에서 검증)
3. setter 가 원시 값 대신 wrapper 인스턴스를 받도록 변경
4. getter 도 wrapper 를 반환하도록 변경 (또는 wrapper 의 raw 접근자 추가)
5. 호출자를 한 곳씩 wrapper 사용으로 옮김. 매 호출자마다 테스트

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Before — priority 가 단순 String
class Order(val priority: String)
// 호출처에 검증 분산
val orders = listOf(Order("high"), Order("normal"))
val highPriority = orders.count { it.priority == "high" || it.priority == "rush" }

// After — Replace Primitive with Object
class Priority private constructor(private val value: String) {
    init { require(value in legalValues) { "잘못된 priority: $value" } }

    override fun toString(): String = value
    fun higherThan(other: Priority): Boolean = index() > other.index()
    private fun index(): Int = legalValues.indexOf(value)

    companion object {
        private val legalValues = listOf("low", "normal", "high", "rush")
        fun of(value: String): Priority = Priority(value)
    }
}

class Order2(val priority: Priority)
val orders2 = listOf(Order2(Priority.of("high")), Order2(Priority.of("normal")))
val rush = Priority.of("rush")
val highCount = orders2.count { !it.priority.higherThan(rush).not() }
```

**역리팩토링**: 없음

**관련 기법 / 스멜**:
- [code-smell-primitive-obsession](code-smells.md#3-primitive-obsession-기본-타입-집착), [code-smell-data-clumps](code-smells.md#5-data-clumps-데이터-뭉치)
- [Replace Type Code with Subclasses](#replace-type-code-with-subclasses), [Introduce Parameter Object](#introduce-parameter-object)
- DDD Value Object, [information-expert](grasp.md#1-information-expert)

---

<a id="replace-conditional-with-polymorphism"></a>
## 15. Replace Conditional with Polymorphism

**언제 적용**: [Switch Statements](code-smells.md#7-switch-statements-조건-분기) / [Repeated Switches](code-smells.md#6-repeated-switches-반복되는-switch) — type 코드 / 상태에 따라 분기하는 conditional 이 여러 함수에 반복. 새 type 추가 시 분기들을 모두 찾아 고쳐야 할 때.

**기법 요약**: type 별 분기를 *클래스 계층의 다형성* 으로 대체. 새 변형은 새 서브클래스 추가로 처리 (OCP). Strategy / State 패턴의 기초.

**적용 절차**:
1. type 코드 사용 클래스를 *서브클래스* 로 분화 (Replace Type Code with Subclasses 선행 가능)
2. 클라이언트에서 객체 생성 시 적절한 서브클래스 인스턴스를 반환하는 팩토리 함수 도입
3. conditional 이 있는 메서드를 부모 클래스로 이동, 추상 메서드로 선언
4. 각 분기를 해당 서브클래스의 override 메서드로 옮김
5. 부모 메서드의 기본 분기는 부모 클래스의 default 구현으로 남기거나 abstract 로 둠
6. 매 분기 이동마다 테스트

**난이도**: 중간 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Before — type 코드에 따른 conditional
class Bird(val type: String, val numberOfCoconuts: Int = 0, val voltage: Int = 0) {
    val plumage: String
        get() = when (type) {
            "EuropeanSwallow" -> "average"
            "AfricanSwallow" -> if (numberOfCoconuts > 2) "tired" else "average"
            "NorwegianBlueParrot" -> if (voltage > 100) "scorched" else "beautiful"
            else -> "unknown"
        }
}

// After — Replace Conditional with Polymorphism
sealed class Bird2 {
    abstract val plumage: String
}

class EuropeanSwallow : Bird2() {
    override val plumage = "average"
}

class AfricanSwallow(val numberOfCoconuts: Int) : Bird2() {
    override val plumage: String
        get() = if (numberOfCoconuts > 2) "tired" else "average"
}

class NorwegianBlueParrot(val voltage: Int) : Bird2() {
    override val plumage: String
        get() = if (voltage > 100) "scorched" else "beautiful"
}
```

**역리팩토링**: 없음 (다형 → conditional 환원은 권장 안 됨)

**관련 기법 / 스멜**:
- [code-smell-switch-statements](code-smells.md#7-switch-statements-조건-분기), [code-smell-repeated-switches](code-smells.md#6-repeated-switches-반복되는-switch)
- [Replace Type Code with Subclasses](#replace-type-code-with-subclasses)
- [ocp](solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙), [lsp](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙), [polymorphism](grasp.md#6-polymorphism)

---

<a id="replace-type-code-with-subclasses"></a>
## 16. Replace Type Code with Subclasses

**언제 적용**: 클래스가 *type 필드* (String / int) 로 자기 종류를 표현하고 동작이 종류마다 달라질 때. *Replace Conditional with State/Strategy* 의 한 갈래로, 동작 분기가 더해질수록 다형성으로의 이행이 가치 있음.

**기법 요약**: type 값별로 서브클래스 신설, type 필드 제거. 객체 생성 시 type 인자를 받아 적절한 서브클래스를 반환하는 팩토리 도입. *Replace Conditional with Polymorphism* 의 구조적 선행 단계.

**적용 절차**:
1. type 필드를 Self-Encapsulate (Encapsulate Variable) 로 getter 경유 접근
2. type 값별로 서브클래스 생성 (보통 sealed class + data class / object)
3. 생성자 / 팩토리에서 type 인자를 보고 적절한 서브클래스 인스턴스 반환
4. type 필드 자체는 부모의 *추상 property* 로 변환, 서브클래스가 override
5. type 에 의존하던 conditional 을 [Replace Conditional with Polymorphism](#replace-conditional-with-polymorphism) 으로 이행
6. type 필드 제거

**난이도**: 중간 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Before — type 필드 + conditional
class Employee(val name: String, val type: String) {
    init { require(type in listOf("engineer", "manager", "salesman")) }
}

// After — Replace Type Code with Subclasses
sealed class Employee2(val name: String) {
    abstract val type: String
}
class Engineer(name: String) : Employee2(name) { override val type = "engineer" }
class Manager(name: String) : Employee2(name) { override val type = "manager" }
class Salesman(name: String) : Employee2(name) { override val type = "salesman" }

// 팩토리
fun createEmployee(name: String, type: String): Employee2 = when (type) {
    "engineer" -> Engineer(name)
    "manager" -> Manager(name)
    "salesman" -> Salesman(name)
    else -> error("unknown type: $type")
}
```

**역리팩토링**: [Remove Subclass](#remove-subclass)

**관련 기법 / 스멜**:
- [code-smell-primitive-obsession](code-smells.md#3-primitive-obsession-기본-타입-집착), [code-smell-switch-statements](code-smells.md#7-switch-statements-조건-분기)
- [Replace Conditional with Polymorphism](#replace-conditional-with-polymorphism), [Replace Primitive with Object](#replace-primitive-with-object)
- [polymorphism](grasp.md#6-polymorphism)

---

<a id="remove-subclass"></a>
## 17. Remove Subclass

**언제 적용**: 서브클래스가 *더 이상 차별화된 동작이 없을 때*. 처음엔 type 분기가 있었지만 시간이 지나며 동작이 부모로 흡수되어 빈 껍질만 남은 경우. *Inline Subclass* 라고도 함.

**기법 요약**: 서브클래스를 부모 클래스로 합치고 type 필드로 종류를 구분. *Replace Type Code with Subclasses* 의 역방향. *Speculative Generality* 스멜 처방.

**적용 절차**:
1. Self-Encapsulate Field 로 서브클래스 type 식별 게터 도입 (부모 클래스에)
2. 서브클래스의 동작을 *type 분기 조건* 으로 부모로 이동 (필요시)
3. 서브클래스 생성자 호출을 부모 생성자 + type 인자로 치환
4. 서브클래스 참조 타입을 부모 타입으로 일괄 교체
5. 매 단계마다 테스트
6. 서브클래스 정의 삭제

**난이도**: 중간 | **사용 빈도**: ★★

**Kotlin 예제**:
```kotlin
// Before — 서브클래스가 이름 결정만 다름
abstract class Person(val name: String) {
    abstract val genderCode: String
}
class Male(name: String) : Person(name) { override val genderCode = "M" }
class Female(name: String) : Person(name) { override val genderCode = "F" }

// After — Remove Subclass (동작 분화가 없어 가치 없음)
class Person2(val name: String, val genderCode: String = "X") {
    val isMale: Boolean get() = genderCode == "M"
    val isFemale: Boolean get() = genderCode == "F"
}
```

**역리팩토링**: [Replace Type Code with Subclasses](#replace-type-code-with-subclasses)

**관련 기법 / 스멜**:
- [code-smell-lazy-class](code-smells.md#15-lazy-class-게으른-클래스-aka-lazy-element), [code-smell-speculative-generality](code-smells.md#18-speculative-generality-추측성-일반화)
- [Inline Function](#inline-function)

---

<a id="extract-superclass"></a>
## 18. Extract Superclass

**언제 적용**: 두 클래스가 *비슷한 필드 / 메서드* 를 갖고 있어 중복 발생. 공통 책임이 도출되었을 때.

**기법 요약**: 공통 부분을 부모 클래스로 끌어올림 (Pull Up Field / Method). 자식 클래스는 차이만 남김. *Composition over Inheritance* 와의 트레이드오프 — 단순 데이터 / 동작 공유는 상속이 명료, 동작 변경이 잦으면 Delegation 으로.

**적용 절차**:
1. 빈 부모 클래스 생성, 두 자식이 이 부모를 상속하게 변경
2. 공통 필드를 부모로 이동 (Pull Up Field)
3. 공통 생성자 코드를 부모 생성자로 이동
4. 공통 메서드를 부모로 이동 (Pull Up Method) — 일치하지 않으면 먼저 [Change Function Declaration](#change-function-declaration) 으로 시그니처 맞춤
5. 호출자가 어디서나 부모 타입으로 다룰 수 있는지 확인 (LSP)
6. 매 단계마다 테스트

**난이도**: 중간 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Before — Department 와 Employee 가 name 과 totalAnnualCost 중복
class Employee(val name: String, val id: String, val monthlyCost: Double) {
    val annualCost: Double get() = monthlyCost * 12
}
class Department(val name: String, val staff: List<Employee>) {
    val totalAnnualCost: Double get() = staff.sumOf { it.annualCost }
}

// After — Extract Superclass
abstract class Party(val name: String) {
    abstract val annualCost: Double
    val monthlyCost: Double get() = annualCost / 12
}

class Employee2(name: String, val id: String, val monthlyRate: Double) : Party(name) {
    override val annualCost: Double get() = monthlyRate * 12
}

class Department2(name: String, val staff: List<Employee2>) : Party(name) {
    override val annualCost: Double get() = staff.sumOf { it.annualCost }
}
```

**역리팩토링**: *Collapse Hierarchy* (Fowler 카탈로그, 본 25 외)

**관련 기법 / 스멜**:
- [code-smell-duplicate-code](code-smells.md#14-duplicate-code-중복-코드), [code-smell-large-class](code-smells.md#2-large-class-aka-god-class)
- [Replace Inheritance with Delegation](#replace-inheritance-with-delegation)
- [lsp](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙), [high-cohesion](grasp.md#5-high-cohesion)

---

<a id="replace-inheritance-with-delegation"></a>
## 19. Replace Inheritance with Delegation

**언제 적용**: 서브클래스가 부모의 *일부* 만 사용 / 부모 인터페이스의 *대부분을 거부* ([Refused Bequest](code-smells.md#8-refused-bequest-거부된-유산)) / 상속 계층 깊이가 변경 비용을 키울 때. *Composition over Inheritance* 의 직접 실천.

**기법 요약**: 상속 관계를 *위임 관계* 로 변환. 서브였던 클래스는 부모였던 클래스의 *필드(delegate)* 를 갖고 필요한 메서드만 forwarding. is-a 가 아니라 has-a.

**적용 절차**:
1. 서브클래스에 *부모 타입* 필드 추가 (delegate)
2. 서브클래스 생성자에서 delegate 초기화 (보통 자기 자신을 전달했던 부분을 별도 인스턴스로)
3. 서브에서 사용 중인 부모 메서드 각각에 대해 *forwarding 메서드* 작성 (`fun foo() = delegate.foo()`)
4. 호출자가 부모 타입을 요구하지 않게 정리 (필요시 인터페이스 추출)
5. extends 관계 제거
6. 매 단계마다 테스트

**난이도**: 중간~높음 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Before — Stack 이 List 를 상속, 그러나 List 의 일부 API 만 의미 있음
class StackBad : ArrayList<Any>() {
    fun push(element: Any) { add(element) }
    fun pop(): Any = removeAt(size - 1)
}

// After — Replace Inheritance with Delegation
class Stack2 {
    private val storage: MutableList<Any> = mutableListOf()
    val size: Int get() = storage.size
    val isEmpty: Boolean get() = storage.isEmpty()

    fun push(element: Any) { storage.add(element) }
    fun pop(): Any = storage.removeAt(storage.size - 1)
    fun peek(): Any = storage.last()
}
```

**역리팩토링**: *Replace Delegation with Inheritance* (Fowler 카탈로그, 본 25 외)

**관련 기법 / 스멜**:
- [code-smell-refused-bequest](code-smells.md#8-refused-bequest-거부된-유산), [code-smell-inappropriate-intimacy](code-smells.md#20-inappropriate-intimacy-부적절한-친밀성)
- [Replace Subclass with Delegate](#replace-subclass-with-delegate), [Extract Superclass](#extract-superclass)
- [composition-over-inheritance](micro-principles.md), [low-coupling](grasp.md#4-low-coupling)

---

<a id="replace-subclass-with-delegate"></a>
## 20. Replace Subclass with Delegate

**언제 적용**: 서브클래스로 표현된 *변형* 이 런타임에 바뀌어야 할 때 (예: 인원 → 회원/비회원, 등급 변경) / 다중 차원의 변형이 있어 상속 계층이 폭발할 때 / 동작 변형이 *합성으로 표현되어야* 자연스러울 때 (Strategy 패턴).

**기법 요약**: 서브클래스를 *delegate 객체* (Strategy / Policy) 로 변환. 부모 클래스가 delegate 필드를 갖고 변형 동작을 위임. 런타임 교체 가능, 다중 변형 합성 가능. 2018 2nd ed. 가 강력히 권장하는 *현대 OO 의 default 선택*.

**적용 절차**:
1. 서브클래스가 표현하던 *변형 동작* 의 인터페이스 정의 (delegate 계약)
2. 각 서브클래스를 그 인터페이스의 구현 클래스로 변환
3. 부모 클래스에 delegate 필드 추가, 생성자에서 주입
4. 변형 동작 호출을 delegate 호출로 변경
5. 호출자에서 서브클래스 직접 생성을 부모 + delegate 인스턴스 생성으로 치환
6. 서브클래스 제거

**난이도**: 높음 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Before — Booking 의 변형으로 PremiumBooking 서브클래스
open class Booking(val show: Show, val date: LocalDate) {
    open fun hasTalkback(): Boolean = show.hasOwnProperty("talkback") && !isPeakDay
    private val isPeakDay: Boolean get() = false
    open val basePrice: Double get() = show.price * (1 + saleableSeatsPercent)
    private val saleableSeatsPercent = 0.1
}
class PremiumBooking(show: Show, date: LocalDate, val extras: PremiumExtras) : Booking(show, date) {
    override fun hasTalkback(): Boolean = show.hasOwnProperty("talkback")
    override val basePrice: Double get() = super.basePrice + extras.premiumFee
}

// After — Replace Subclass with Delegate (Strategy)
interface PremiumDelegate {
    fun hasTalkback(superHas: Boolean): Boolean
    fun extendBasePrice(base: Double): Double
}

class StandardPremium(private val extras: PremiumExtras) : PremiumDelegate {
    override fun hasTalkback(superHas: Boolean): Boolean = true
    override fun extendBasePrice(base: Double): Double = base + extras.premiumFee
}

class Booking2(val show: Show, val date: LocalDate, private val premium: PremiumDelegate? = null) {
    fun hasTalkback(): Boolean {
        val superHas = show.hasOwnProperty("talkback") && !isPeakDay
        return premium?.hasTalkback(superHas) ?: superHas
    }
    val basePrice: Double
        get() {
            val base = show.price * 1.1
            return premium?.extendBasePrice(base) ?: base
        }
    private val isPeakDay = false
}
```

**역리팩토링**: 없음 (delegate → subclass 복귀는 권장 안 됨)

**관련 기법 / 스멜**:
- [code-smell-refused-bequest](code-smells.md#8-refused-bequest-거부된-유산), [code-smell-large-class](code-smells.md#2-large-class-aka-god-class)
- [Replace Inheritance with Delegation](#replace-inheritance-with-delegation), [Replace Conditional with Polymorphism](#replace-conditional-with-polymorphism)
- [composition-over-inheritance](micro-principles.md), [Strategy Pattern]

---

<a id="hide-delegate"></a>
## 21. Hide Delegate

**언제 적용**: [Message Chains](code-smells.md#21-message-chains-메시지-체인) — 클라이언트가 `a.b().c().d()` 처럼 내부를 줄줄이 타고 들어갈 때. 클라이언트가 서버의 *연쇄 구조* 에 결합되어 변경 비용 증가.

**기법 요약**: 클라이언트와 delegate 사이에 *서버 클래스* 가 중개 메서드를 제공. 클라이언트는 delegate 의 존재를 모름. Law of Demeter ("최소 지식 원칙") 의 직접적 처방.

**적용 절차**:
1. 클라이언트가 호출하는 delegate 의 각 메서드에 대해, 서버에 *동일 시그니처 forwarding 메서드* 추가
2. 클라이언트의 `server.delegate().foo()` 호출을 `server.foo()` 로 치환. 매 호출마다 테스트
3. 클라이언트가 더 이상 delegate 에 직접 접근하지 않으면, 서버에서 delegate getter 의 가시성을 낮춤 (private)

**난이도**: 낮음 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Before — Message Chain
class Department(val manager: Person)
class Person(val name: String, val department: Department)

val person = Person("Tom", Department(Person("Boss", Department(/* ... */))))
// 호출처
val mgrName = person.department.manager.name        // 체인

// After — Hide Delegate
class Person2(val name: String, private val department: Department2) {
    val managerName: String get() = department.manager.name   // 중개
}
class Department2(val manager: Person2)

val person2 = Person2("Tom", Department2(Person2("Boss", Department2(/* ... */))))
val mgrName2 = person2.managerName
```

**역리팩토링**: [Remove Middle Man](#remove-middle-man)

**관련 기법 / 스멜**:
- [code-smell-message-chains](code-smells.md#21-message-chains-메시지-체인), [code-smell-inappropriate-intimacy](code-smells.md#20-inappropriate-intimacy-부적절한-친밀성)
- [lod](micro-principles.md), [low-coupling](grasp.md#4-low-coupling), [tell-dont-ask](micro-principles.md)

---

<a id="remove-middle-man"></a>
## 22. Remove Middle Man

**언제 적용**: [Middle Man](code-smells.md#22-middle-man-중개자) — 클래스의 메서드 대부분이 *단순 forwarding* 뿐. Hide Delegate 의 과용으로 중개 메서드가 폭증.

**기법 요약**: 중개 메서드를 제거하고 클라이언트가 직접 delegate 와 통신. Hide Delegate 의 역방향. *언제든 한쪽으로 기울 수 있는 트레이드오프* — 매번 균형점이 다름.

**적용 절차**:
1. delegate 에 대한 *getter* 를 public 으로 노출 (또는 caller 에서 가져갈 수 있게)
2. 각 forwarding 메서드를 호출하던 클라이언트를 `server.delegate.method()` 로 치환. 매 치환마다 테스트
3. 모든 forwarding 호출이 사라지면 forwarding 메서드 삭제
4. 일부만 남기는 부분 적용도 가능 — 자주 쓰이는 forwarding 은 유지

**난이도**: 낮음 | **사용 빈도**: ★★

**Kotlin 예제**:
```kotlin
// Before — Person 이 Department 의 단순 forwarding 만
class Department3(val manager: Person3, val chargeCode: String)
class Person3(val name: String, val department: Department3) {
    val manager: Person3 get() = department.manager           // forwarding
    val chargeCode: String get() = department.chargeCode      // forwarding
}

// After — Remove Middle Man (delegate 노출)
class Department4(val manager: Person4, val chargeCode: String)
class Person4(val name: String, val department: Department4)   // forwarding 제거

// 호출처는 직접 접근
val person = Person4("Tom", Department4(Person4("Boss", /* ... */ Department4(/* ... */, "X")), "X"))
val mgr = person.department.manager
```

**역리팩토링**: [Hide Delegate](#hide-delegate)

**관련 기법 / 스멜**:
- [code-smell-middle-man](code-smells.md#22-middle-man-중개자), [code-smell-speculative-generality](code-smells.md#18-speculative-generality-추측성-일반화)
- [Inline Function](#inline-function)

---

<a id="move-field"></a>
## 23. Move Field

**언제 적용**: 필드가 *현재 소속 클래스보다 다른 클래스의 메서드에서 더 많이 사용* 될 때 / 같은 필드 묶음이 여러 클래스에 흩어져 변경이 산탄총 효과를 일으킬 때.

**기법 요약**: 필드를 더 적합한 클래스로 이동. 보통 [Move Function](#move-function) 과 짝을 이뤄 진행 — 데이터와 그 위에서 동작하는 함수가 함께 움직여야 응집성 유지.

**적용 절차**:
1. 소스 클래스의 필드 접근을 Encapsulate Variable (getter / setter) 로 통일
2. 타겟 클래스에 동일 필드 추가
3. 소스의 getter / setter 가 타겟 필드를 사용하도록 forwarding 변경 (양쪽이 잠시 공존)
4. 모든 직접 참조가 getter / setter 경유인지 재확인
5. 소스 클래스의 필드 삭제, 호출자가 직접 타겟의 필드를 참조하도록 정리
6. 매 단계마다 테스트

**난이도**: 중간 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Before — discountRate 가 Customer 에 있지만 사실 CustomerContract 의 책임
class Customer(val name: String, var discountRate: Double, val contract: CustomerContract)
class CustomerContract(val startDate: LocalDate)
// 호출처
val rate = customer.discountRate

// After — Move Field (Customer → CustomerContract)
class CustomerContract2(val startDate: LocalDate, var discountRate: Double)
class Customer2(val name: String, val contract: CustomerContract2) {
    val discountRate: Double                       // backward-compat getter (점진 마이그레이션)
        get() = contract.discountRate
}
// 새 호출처
val rate2 = customer.contract.discountRate
```

**역리팩토링**: [Move Field](#move-field) (역방향 이동)

**관련 기법 / 스멜**:
- [code-smell-feature-envy](code-smells.md#19-feature-envy-기능-욕심), [code-smell-shotgun-surgery](code-smells.md#11-shotgun-surgery-산탄총-수술)
- [Move Function](#move-function), [Encapsulate Variable](#encapsulate-variable)
- [high-cohesion](grasp.md#5-high-cohesion), [information-expert](grasp.md#1-information-expert)

---

<a id="move-function"></a>
## 24. Move Function

**언제 적용**: 함수가 *현재 클래스의 데이터보다 다른 클래스의 데이터를 더 많이 사용* 할 때 ([Feature Envy](code-smells.md#19-feature-envy-기능-욕심)) / 모듈 / 패키지 경계 정리 / 객체간 책임 재배치.

**기법 요약**: 함수를 더 적합한 컨텍스트(클래스 / 모듈 / 네임스페이스) 로 이동. *Information Expert* 원칙의 실천 — 데이터 옆에 동작을 둔다.

**적용 절차**:
1. 함수가 사용하는 모든 요소(필드 / 다른 함수 / 매개변수) 확인. 타겟 컨텍스트에서 접근 가능한지 점검
2. 함수의 사용자 모두 확인
3. 타겟에 함수 복사, 시그니처 조정 (소스의 `this` 가 매개변수로 들어와야 할 수도)
4. 소스의 원본 함수를 타겟 호출로 위임하는 *forwarding* 으로 일단 둠
5. 호출자를 한 곳씩 타겟의 함수로 직접 호출하도록 변경. 매 변경마다 테스트
6. 모든 호출자가 옮기면 소스의 forwarding 함수 삭제

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Before — overdraftCharge 가 Account 에 있지만 사실 AccountType 의 정책
class AccountType(val isPremium: Boolean)
class Account(val type: AccountType, var daysOverdrawn: Int) {
    val overdraftCharge: Double
        get() = if (type.isPremium) {
            val baseCharge = 10.0
            if (daysOverdrawn <= 7) baseCharge
            else baseCharge + (daysOverdrawn - 7) * 0.85
        } else {
            daysOverdrawn * 1.75
        }
}

// After — Move Function (Account → AccountType)
class AccountType2(val isPremium: Boolean) {
    fun overdraftCharge(daysOverdrawn: Int): Double =
        if (isPremium) {
            val baseCharge = 10.0
            if (daysOverdrawn <= 7) baseCharge
            else baseCharge + (daysOverdrawn - 7) * 0.85
        } else {
            daysOverdrawn * 1.75
        }
}
class Account2(val type: AccountType2, var daysOverdrawn: Int) {
    val overdraftCharge: Double
        get() = type.overdraftCharge(daysOverdrawn)        // forwarding (점진 마이그레이션)
}
```

**역리팩토링**: [Move Function](#move-function) (역방향 이동)

**관련 기법 / 스멜**:
- [code-smell-feature-envy](code-smells.md#19-feature-envy-기능-욕심), [code-smell-shotgun-surgery](code-smells.md#11-shotgun-surgery-산탄총-수술), [code-smell-divergent-change](code-smells.md#10-divergent-change-발산하는-변경)
- [Move Field](#move-field), [Combine Functions into Class](#combine-functions-into-class)
- [information-expert](grasp.md#1-information-expert), [high-cohesion](grasp.md#5-high-cohesion), [low-coupling](grasp.md#4-low-coupling)

---

<a id="decompose-conditional"></a>
## 25. Decompose Conditional (+ Consolidate Conditional Expression)

**언제 적용**:
- **Decompose Conditional**: 길고 복잡한 conditional 블록 (if/else 또는 when) 안에 *의도가 묻혀* 있을 때. 조건과 결과 분기 모두 풀어서 이해해야 할 때.
- **Consolidate Conditional Expression**: 서로 다른 조건들이 *동일한 결과* 를 낼 때. 조건 표현식이 분산되어 패턴 식별이 어려울 때.

**기법 요약**:
- *Decompose Conditional* — conditional 의 *조건부 / 진 분기 / 거짓 분기* 각각을 의도 있는 메서드로 추출. Extract Function 의 conditional 특화 적용.
- *Consolidate Conditional Expression* — 동일한 결과의 conditional 들을 *논리연산자 (OR / AND)* 로 합치고, 합쳐진 조건은 의도 있는 메서드로 추출.

**적용 절차** (Decompose):
1. 조건 표현식을 Extract Function 으로 의도 메서드로 추출 (예: `isSummer(date)`)
2. 진 분기 본문을 Extract Function (예: `summerCharge(quantity)`)
3. 거짓 분기 본문을 Extract Function (예: `regularCharge(quantity)`)
4. 원본 자리는 `if (isSummer(d)) summerCharge(q) else regularCharge(q)` 로 정리
5. 테스트

**적용 절차** (Consolidate):
1. 조건들에 부수효과가 없는지 확인
2. 동일 결과 분기들의 조건을 `||` (또는 `&&`) 로 합침
3. 합쳐진 조건을 Extract Function 으로 추출
4. 테스트

**난이도**: 낮음 | **사용 빈도**: ★★★★

**Kotlin 예제** — Decompose:
```kotlin
// Before
fun charge(date: LocalDate, quantity: Int): Double =
    if (!date.isBefore(summerStart) && !date.isAfter(summerEnd))
        quantity * summerRate
    else
        quantity * regularRate + summerServiceCharge

// After — Decompose Conditional
fun charge2(date: LocalDate, quantity: Int): Double =
    if (isSummer(date)) summerCharge(quantity) else regularCharge(quantity)

private fun isSummer(date: LocalDate): Boolean =
    !date.isBefore(summerStart) && !date.isAfter(summerEnd)
private fun summerCharge(quantity: Int): Double = quantity * summerRate
private fun regularCharge(quantity: Int): Double = quantity * regularRate + summerServiceCharge
```

**Kotlin 예제** — Consolidate:
```kotlin
// Before — 같은 결과를 세 번 분기
fun disabilityAmount(employee: Employee): Double {
    if (employee.seniority < 2) return 0.0
    if (employee.monthsDisabled > 12) return 0.0
    if (employee.isPartTime) return 0.0
    // 본 계산
    return employee.salary * 0.6
}

// After — Consolidate Conditional Expression
fun disabilityAmount2(employee: Employee): Double {
    if (isNotEligibleForDisability(employee)) return 0.0
    return employee.salary * 0.6
}
private fun isNotEligibleForDisability(employee: Employee): Boolean =
    employee.seniority < 2 ||
        employee.monthsDisabled > 12 ||
        employee.isPartTime
```

**역리팩토링**: Inline Function (Decompose 의 부분 환원)

**관련 기법 / 스멜**:
- [code-smell-long-method](code-smells.md#1-long-method-긴-메서드), [code-smell-duplicate-code](code-smells.md#14-duplicate-code-중복-코드), [code-smell-comments](code-smells.md#13-comments-불필요한-주석)
- [Extract Function](#extract-function), [Replace Conditional with Polymorphism](#replace-conditional-with-polymorphism)
- [srp](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙)

---

## 카테고리 별 정리

Fowler 2nd ed. Chapter 6~12 의 분류 기준:

| Chapter | 카테고리 | 포함 기법 (본 25 한정) |
|---------|---------|------------------------|
| Ch 6 | **A First Set of Refactorings** (기본 도구) | Extract Function (1), Inline Function (2), Extract Variable (3), Inline Variable (4), Change Function Declaration (5), Encapsulate Variable (6), Rename Variable (7), Introduce Parameter Object (8), Combine Functions into Class (9), Combine Functions into Transform (10), Split Phase (11) |
| Ch 7 | **Encapsulation** (캡슐화) | Encapsulate Record (12), Encapsulate Collection (13) |
| Ch 8 | **Moving Features** (책임 이동) | Move Function (24), Move Field (23) |
| Ch 9 | **Organizing Data** (데이터 정리) | Replace Primitive with Object (14) |
| Ch 10 | **Simplifying Conditional Logic** (조건 단순화) | Decompose Conditional (25), Consolidate Conditional Expression (25), Replace Conditional with Polymorphism (15) |
| Ch 11 | **Refactoring APIs** (API 정리) | Hide Delegate (21), Remove Middle Man (22) |
| Ch 12 | **Dealing with Inheritance** (상속 다루기) | Replace Type Code with Subclasses (16), Remove Subclass (17), Extract Superclass (18), Replace Inheritance with Delegation (19), Replace Subclass with Delegate (20) |

---

## 안전한 리팩토링 체크리스트

각 리팩토링 단계마다:

1. **테스트 PASS 상태에서 시작** — 깨진 상태로 리팩토링 시작 금지
2. **한 번에 한 가지 리팩토링만** — 여러 변환을 섞으면 어느 단계가 깨뜨렸는지 추적 불가
3. **매 단계마다 컴파일 + 테스트** — 작은 단계의 본질. "10초 단위 commit" 도 가능
4. **기능 추가와 분리** — 리팩토링 PR 과 기능 추가 PR 분리 (Two Hats)
5. **IDE refactoring 우선** — 수동 변환은 실수 위험. Kotlin/IDEA, Eclipse, ReSharper 의 자동 refactoring 사용
6. **WIP 백업** — 큰 변환 전 stash / 별도 브랜치
7. **검토 후 rebase** — 작은 commit 들을 의미 있는 단위로 squash

---

## 표준 인용

- Martin Fowler, *Refactoring: Improving the Design of Existing Code*, 2nd ed. (2018), Chapter 6~12, Addison-Wesley — 본 25 기법의 원전
- Martin Fowler, *Refactoring: Improving the Design of Existing Code* 1st ed. (1999), Addison-Wesley — Kent Beck, John Brant, William Opdyke, Don Roberts 공저
- Joshua Kerievsky, *Refactoring to Patterns* (2004), Addison-Wesley — Fowler 카탈로그 + GoF 패턴 결합 27 시퀀스
- Michael Feathers, *Working Effectively with Legacy Code* (2004), Prentice Hall — 테스트 없는 코드의 안전한 리팩토링 24 기법 (Seams, Sprout Method/Class, Wrap Method/Class)
- Robert C. Martin, *Clean Code* (2008), Chapter 5 "Formatting", Chapter 17 "Smells and Heuristics" — 리팩토링 휴리스틱 보강
- Kent Beck, *Implementation Patterns* (2007) — Fowler 가 자주 인용하는 *small steps* 의 source
