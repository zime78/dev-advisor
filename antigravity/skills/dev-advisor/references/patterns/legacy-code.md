# 레거시 코드 작업 패턴 (Legacy Code Working Patterns)

Michael C. Feathers *Working Effectively with Legacy Code* (Prentice Hall, 2004) 의 정평 있는 10 기법. Feathers 정의: **레거시 코드 = 테스트가 없는 코드**. 본 파일은 그 정의 위에서 *안전하게 테스트를 붙이고 → 변경하는* 방법.

**원전 참고**:
- Michael C. Feathers — *Working Effectively with Legacy Code* (Prentice Hall, 2004)
- Daniel Brolund, Ola Ellnestam — *The Mikado Method* (Manning, 2014)
- Martin Fowler — *Refactoring* 2nd ed. (2018)
- Andy Hunt & Dave Thomas — *The Pragmatic Programmer* 20th anniv. ed. (2019)

**핵심 원칙**:
- **테스트 먼저, 변경 나중** — Characterization test 로 현재 동작 잠근 뒤 리팩토링
- **Sprout & Wrap** — 기존 코드를 *직접 수정* 하지 않고 *옆에* 만들기
- **Seam 식별 우선** — 변경 가능한 *틈* 을 찾아야 의존성을 끊을 수 있음

**관련 카탈로그**:
- [`../principles/code-smells.md`](../principles/code-smells.md) — 22 스멜 (탐지)
- [`../principles/refactoring-techniques.md`](../principles/refactoring-techniques.md) — Fowler 25 기법 (테스트 있을 때)
- [testing.md](testing.md) — Test Pyramid / AAA / Test Double
- [anti-patterns.md](anti-patterns.md) — Lava Flow / Big Ball of Mud (레거시 안티패턴 본체)

**Feathers Legacy Code Dilemma**:
> "변경하려면 테스트가 필요하다. 테스트를 붙이려면 변경해야 한다." — *Working Effectively with Legacy Code*, p. 16

본 카탈로그 10 기법은 이 딜레마를 깨는 표준 도구다. 1~2 번은 *인식 / 안전망*, 3~5 번은 *기존 코드 보존 + 추가*, 6~9 번은 *의존성 끊기*, 10 번은 *큰 변경 전략*.

---

<a id="seam-types"></a>
## 1. Seam (Object / Preprocessing / Link)

**언제 적용**: 테스트할 코드가 *떼어내기 어려운* 의존성에 묶여 있을 때 — DB 연결, 정적 메서드, 외부 API, 파일 시스템, 시계(`System.currentTimeMillis()`). 변경하기 전에 *어디를 잘라서 테스트할 수 있을지* 결정해야 함.

**기법 요약**: Feathers 정의 — *Seam* = "코드를 편집하지 않고도 그 지점의 동작을 바꿀 수 있는 위치". 모든 seam 에는 *enabling point* (어느 동작이 적용될지 결정하는 곳) 가 있음. 3 종 분류:

- **Object Seam** (OO 언어에서 가장 흔함): 객체 메서드 호출 지점. enabling point = 객체 주입 시점. 인터페이스 / 가상 메서드 / DI 로 교체.
- **Preprocessing Seam** (C/C++): 전처리기 매크로로 동작 교체. enabling point = `#define` / `#include` 순서. `#ifdef TEST` 로 함수 치환.
- **Link Seam** (C/C++/JVM 모두): 링커가 어떤 binary 를 묶는지로 동작 교체. enabling point = build script / classpath. 테스트 시 다른 jar / .o 를 링크.

**적용 절차**:
1. 변경하려는 코드 단락을 식별
2. 그 단락이 *외부* 와 통신하는 모든 지점 나열 (메서드 호출, static call, new, 전역 변수, 매크로)
3. 각 지점이 어떤 seam 종류인지 분류 — Object seam 이 가장 다루기 쉬움
4. enabling point 를 통해 *교체 가능한가* 확인 — 불가능하면 [Extract Interface](#extract-interface-testability) / [Subclass and Override Method](#subclass-and-override-method) 로 새 seam 만들기
5. 테스트에서 enabling point 를 조작해 fake / mock 주입

**난이도**: 중간 (seam 식별은 경험 필요) | **사용 빈도**: ★★★★★ (모든 레거시 작업의 출발점)

**Kotlin 예제** — Object Seam 만들기:
```kotlin
// Before — 의존성이 직접 묶임. 테스트 불가
class OrderService {
    fun place(order: Order): Receipt {
        val now = System.currentTimeMillis()              // 정적 의존 (테스트 어려움)
        val db = DriverManager.getConnection("jdbc:...")   // 직접 생성
        db.insert(order, now)
        return Receipt(order.id, now)
    }
}

// After — Object Seam 도입. 생성자 매개변수가 enabling point
interface Clock { fun nowMillis(): Long }
interface OrderRepository { fun insert(order: Order, at: Long) }

class OrderService(
    private val clock: Clock,           // ← seam
    private val repo: OrderRepository,  // ← seam
) {
    fun place(order: Order): Receipt {
        val now = clock.nowMillis()
        repo.insert(order, now)
        return Receipt(order.id, now)
    }
}

// 테스트 — enabling point (생성자 인자) 로 fake 주입
@Test fun `place uses provided clock`() {
    val service = OrderService(
        clock = object : Clock { override fun nowMillis() = 1_700_000_000_000L },
        repo  = InMemoryOrderRepository(),
    )
    val receipt = service.place(Order("A-1"))
    assertEquals(1_700_000_000_000L, receipt.placedAt)
}
```

**Java 예제** — Link Seam (어떤 jar 가 링크되는지로 동작 교체):
```java
// 프로덕션 빌드: production classpath 에 LoggerImpl.class (실제 파일 I/O)
// 테스트 빌드:   test classpath 에 LoggerImpl.class (in-memory 버전, 같은 FQCN)
// 호출 코드는 변경 없음. classpath 순서가 enabling point.
public class AuditService {
    public void record(String event) {
        Logger.log(event);  // ← Link Seam. 어떤 Logger.class 가 우선 로드되는지로 교체
    }
}
```

**관련 기법 / 스멜**:
- [extract-interface-testability](#extract-interface-testability), [subclass-and-override-method](#subclass-and-override-method), [extract-and-override](#extract-and-override) — 새 seam 만들기
- [characterization-test](#characterization-test) — seam 으로 잘랐다면 그 자리에 테스트
- [dip](../principles/solid.md#5-dependency-inversion-principle-dip-의존성-역전-원칙) — Object seam 의 이론적 기반

---

<a id="characterization-test"></a>
## 2. Characterization Test

**언제 적용**: 명세 / 문서가 없거나 신뢰할 수 없는 코드를 변경해야 할 때. "이 코드가 *무엇을 해야 하는가* (what should be)" 는 아무도 모르지만, "지금 *무엇을 하고 있는가* (what is)" 는 코드가 보여줌. 그것을 *잠그는* 테스트.

**기법 요약**: 코드의 *현재 동작* 을 가능한 한 많이 호출해 보고 그 출력을 그대로 단언으로 박아넣은 테스트. 명세를 검증하는 게 아니라 *행위를 화석화* 하는 것. 일단 묶고 나면 그 위에서 안전하게 리팩토링 가능. Feathers 는 "**실수가 발견될 때까지** characterization test 가 옳다고 가정한다" 고 명시 — 잘못된 동작을 잠갔다면 그건 *버그 발견* 이고, 별도 의사결정으로 처리.

**변형**:
- **Gold Master** — 출력 전체를 텍스트 / json 파일로 저장하고 diff 비교. 큰 보고서 / 직렬화 결과 / SQL dump 에 유용
- **Approval Test** — Gold Master 의 라이브러리화 (e.g. ApprovalTests, Approvaltests.Combinations). 첫 실행 시 *received* 파일 → 사람이 검토 → *approved* 파일로 승인
- **Snapshot Test** (Jest 등) — 같은 아이디어의 UI 컴포넌트 적용 → [testing.md#snapshot-test](testing.md)

**적용 절차**:
1. SUT 호출 — 무엇이든 호출해서 결과를 확인
2. 결과값 (반환값 / 부수효과 / 호출 시퀀스 / 로그) 을 *그대로* assert 에 박음 — "이 값이 옳은가" 는 따지지 않음
3. 테스트 실패 → 출력 확인 → assert 값 갱신 → 다시 실행해서 PASS
4. 입력 경계값 / 분기 조건을 늘려가며 테스트 추가 (커버리지 도구 활용)
5. 충분히 커버되면 그 위에서 리팩토링 / 변경 시작
6. 리팩토링 후에도 모든 characterization test 가 PASS 여야 함 (행동 보존)

**난이도**: 낮음 (지적 부담은 큼 — "옳지 않을 수도 있는 동작을 잠그는" 불편함을 견뎌야) | **사용 빈도**: ★★★★★

**Kotlin 예제** — 명세 불명의 함수에 characterization 추가:
```kotlin
// 운영 코드 (의도 불명. 주석 없음. 작성자 퇴사)
fun discountFor(amount: Int, code: String?): Int {
    if (amount < 0) return 0
    val base = if (code == "VIP") amount * 30 / 100 else amount / 10
    return if (base > 5000) 5000 else base
}

// Step 1 — 무엇이든 호출해서 결과 관찰
class DiscountForCharacterizationTest {
    @Test fun `amount 1000, no code`()      = assertEquals(100,  discountFor(1000, null))
    @Test fun `amount 1000, VIP code`()     = assertEquals(300,  discountFor(1000, "VIP"))
    @Test fun `amount 100000, VIP capped`() = assertEquals(5000, discountFor(100000, "VIP"))
    @Test fun `negative amount returns 0`() = assertEquals(0,    discountFor(-50, "VIP"))
    @Test fun `unknown code falls to 10%`() = assertEquals(100,  discountFor(1000, "GOLD"))
    // "이게 옳은가?" 는 묻지 않음. "지금 이렇게 동작한다" 를 잠그는 것.
}

// Step 2 — 이제 안전하게 내부 변경 가능
fun discountFor(amount: Int, code: String?): Int {
    if (amount < 0) return 0
    val rate = if (code == "VIP") 0.30 else 0.10
    return ((amount * rate).toInt()).coerceAtMost(5000)
}
// 모든 characterization test PASS → 행동 보존 확인
```

**Gold Master 변형 예제**:
```kotlin
@Test fun `report output matches gold master`() {
    val actual = ReportGenerator.run(testFixture)
    val expected = File("src/test/resources/report.approved.txt").readText()
    assertEquals(expected, actual)
    // 첫 실행 시 expected 가 없으면 actual 을 .received.txt 로 저장 → 사람이 검토 후 .approved.txt 로 rename
}
```

**Anti-pattern 주의**:
- **"옳은 동작" 으로 가정하지 말 것** — 명세 기반 테스트가 아님. 잠근 동작이 버그였다면 별도 티켓으로 처리
- **테스트 이름은 "현재 동작 묘사"** — `discountFor returns 100 for amount 1000 with no code`. *의도* 가 아닌 *현상* 표현
- **너무 많은 입력 한꺼번에 잠그지 말 것** — 한 번에 한 분기. 잠근 곳부터 리팩토링하며 다음 분기로

**관련 기법 / 스멜**:
- [seam-types](#seam-types) — 의존성이 있으면 먼저 seam 으로 잘라서 테스트 환경 만들기
- [sensing-variable](#sensing-variable) — 반환값으로 검증이 안 될 때
- [testing.md#snapshot-test](testing.md) — UI 컴포넌트 적용
- [Refactor 안전망](../principles/refactoring-techniques.md) — characterization 위에서 Fowler 기법 적용

---

<a id="sprout-method-class"></a>
## 3. Sprout Method / Sprout Class

**언제 적용**: 기존의 *테스트 불가능한* 메서드에 새 기능을 추가해야 하지만, 기존 메서드 전체를 안전하게 잡을 수 있는 characterization test 가 아직 없을 때. 기존을 건드리지 않고 *새 메서드 / 새 클래스를 옆에 만들어* 호출만 추가.

**기법 요약**:
- **Sprout Method**: 새 동작을 *새 메서드* 로 작성하고 (테스트 가능하게), 기존 메서드에서 그 새 메서드를 호출하는 한 줄만 추가
- **Sprout Class**: 새 동작이 여러 메서드 / 자체 상태를 요구하면 *새 클래스* 를 만듦. 기존 클래스에서 인스턴스화 + 호출 한 줄만

기존 코드 본체는 *안 건드림* — 변경 영향 반경 최소화. 새 코드는 처음부터 깨끗하게 테스트 가능한 형태로 작성. 트레이드오프: 기존 메서드는 여전히 레거시. 시간이 지나면 sprout 가 충분히 자라서 [Extract Class](../principles/refactoring-techniques.md) 로 본격 분리.

**적용 절차**:
1. 추가할 기능이 *기존 메서드 안 어느 지점* 에서 호출되어야 하는지 식별 (보통 시작 / 끝 / 특정 조건 후)
2. 새 메서드를 *별도로* 작성 — 가능한 한 static / pure / 의존성 없음. TDD 로 작성 가능
3. 기존 메서드의 식별된 지점에 새 메서드 호출 한 줄 추가
4. 기존 메서드 전체에 대한 characterization test 가 *없어도* 일단 진행 가능 — 새 코드 자체는 단위 테스트로 보호됨
5. 사람 눈으로 호출 위치만 검토 (변경이 한 줄이라 리뷰 부담 적음)

**난이도**: 낮음 | **사용 빈도**: ★★★★★ (가장 자주 쓰는 레거시 전술)

**Kotlin 예제** — Sprout Method:
```kotlin
// Before — 거대한 기존 메서드. 테스트 없음. 직접 수정 위험
class TransactionGate {
    fun postEntries(entries: List<Entry>) {
        // ... 200 줄의 검증 / 로깅 / DB 쓰기 / 메시지 발행 ...
        for (e in entries) {
            // ... 복잡한 처리 ...
            ledger.write(e)
        }
        // ... 후처리 200 줄 ...
    }
}

// 추가 요구사항: "entries 에 중복 ID 있으면 발견 즉시 reject 한다"
// 기존 메서드를 통째로 잡을 characterization test 가 아직 없음 → Sprout Method

// After — 새 메서드를 옆에 만들고 한 줄로 호출
class TransactionGate {
    fun postEntries(entries: List<Entry>) {
        val unique = uniqueEntries(entries)   // ← Sprout. 추가된 한 줄
        // ... 기존 200 줄 그대로. unique 사용으로만 교체 ...
        for (e in unique) {
            ledger.write(e)
        }
    }

    // 새 메서드 — 완전히 독립적이고 테스트 가능
    internal fun uniqueEntries(entries: List<Entry>): List<Entry> {
        val seen = mutableSetOf<String>()
        return entries.filter { seen.add(it.id) }
    }
}

// 새 메서드만 깨끗하게 TDD
class UniqueEntriesTest {
    private val gate = TransactionGate()
    @Test fun `keeps first occurrence`() {
        val result = gate.uniqueEntries(listOf(Entry("A"), Entry("B"), Entry("A")))
        assertEquals(listOf(Entry("A"), Entry("B")), result)
    }
    @Test fun `empty input`() = assertEquals(emptyList(), gate.uniqueEntries(emptyList()))
}
```

**Kotlin 예제** — Sprout Class (새 동작이 다수 메서드 / 상태 가질 때):
```kotlin
// 추가 요구사항: "entries 처리 중 retry 정책 (3회 + 지수 backoff)" — Sprout Class
class TransactionGate(private val retryPolicy: RetryPolicy = RetryPolicy()) {
    fun postEntries(entries: List<Entry>) {
        for (e in entries) {
            retryPolicy.execute { ledger.write(e) }   // ← Sprout Class 호출
        }
    }
}

class RetryPolicy(val maxAttempts: Int = 3, val baseDelayMs: Long = 100) {
    fun <T> execute(block: () -> T): T {
        var attempt = 0
        while (true) {
            try { return block() }
            catch (e: Exception) {
                attempt++
                if (attempt >= maxAttempts) throw e
                Thread.sleep(baseDelayMs * (1L shl (attempt - 1)))
            }
        }
    }
}
// RetryPolicy 는 처음부터 깨끗하게 단위 테스트
```

**Anti-pattern 주의**:
- 새 메서드 안에서 *또* 기존 레거시 메서드를 호출하면 격리 효과 사라짐
- Sprout 가 점점 커져서 sprout 가 다시 레거시화되지 않게. 일정 크기 이상이면 Sprout Class 로 전환

**관련 기법 / 스멜**:
- [wrap-method-class](#wrap-method-class) — 호출 전후로 *감싸기* 가 필요할 때 (Sprout 는 *추가*, Wrap 은 *감싸기*)
- [extract-function](../principles/refactoring-techniques.md#extract-function) — characterization 이 갖춰지면 본격 추출로 전환
- [code-smell-long-method](../principles/code-smells.md#1-long-method-긴-메서드) — 거대 메서드의 점진적 해체 전략

---

<a id="wrap-method-class"></a>
## 4. Wrap Method / Wrap Class

**언제 적용**: 기존 메서드가 호출되는 *모든 자리* 에서 *추가 동작* 이 필요할 때 (감사 로깅, 메트릭, 알림, 캐싱, 권한 검사). Sprout 가 *특정 지점에 새 동작 추가* 라면, Wrap 은 *기존 동작 전체를 감싸* 새 책임을 얹는 것.

**기법 요약**:
- **Wrap Method**: 기존 메서드를 같은 이름의 새 메서드로 교체. 새 메서드는 (a) 추가 동작 (b) 기존 메서드 호출 둘을 함. 원본 기존 메서드는 *이름만 바꾸어* private 으로 숨김
- **Wrap Class**: Decorator 패턴의 레거시 적용. 기존 클래스를 같은 인터페이스의 *데코레이터* 로 감쌈. 모든 클라이언트가 데코레이터를 사용하게 전환

핵심: 호출 측 코드는 *변경 없음*. 추가 책임은 wrapper 에 격리되어 테스트 가능.

**적용 절차** (Wrap Method):
1. 감쌀 기존 메서드의 이름을 결정 (예: `pay`)
2. 기존 메서드를 *이름 변경* — `pay` → `payCore` / `payImpl` (private)
3. 새 `pay` 메서드를 같은 시그니처로 작성: 추가 동작 + `payCore()` 호출
4. 컴파일 — 모든 외부 호출자는 변경 없이 자동으로 새 `pay` 를 호출
5. 새 동작에 대한 테스트 작성 (payCore 가 mock 또는 sprout class 면 testable)

**적용 절차** (Wrap Class):
1. 기존 클래스가 구현하는 *인터페이스 추출* — 없으면 [Extract Interface](#extract-interface-testability) 먼저
2. 같은 인터페이스의 새 클래스 작성. 생성자에서 기존 클래스를 받음
3. 모든 메서드를 위임 + 필요한 곳에 추가 동작
4. DI / 팩토리에서 기존 인스턴스를 wrapper 로 교체

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★

**Kotlin 예제** — Wrap Method:
```kotlin
// Before — 메서드에 감사 로깅 추가 요구. 모든 호출 자리 일일이 못 바꿈
class PaymentService {
    fun pay(account: Account, amount: Long) {
        // ... 결제 처리 ...
    }
}

// After — Wrap Method
class PaymentService(private val auditLog: AuditLog) {
    fun pay(account: Account, amount: Long) {
        auditLog.record("pay.start", account.id, amount)   // ← 추가 동작 (전)
        try {
            payCore(account, amount)                        // ← 기존 동작
            auditLog.record("pay.success", account.id, amount)
        } catch (e: Exception) {
            auditLog.record("pay.failure", account.id, amount, e.message)
            throw e
        }
    }

    // 기존 메서드는 이름만 바뀐 채 그대로
    private fun payCore(account: Account, amount: Long) {
        // ... 결제 처리 (변경 없음) ...
    }
}
// 호출 측 코드 `service.pay(...)` 는 한 줄도 변경 없음
```

**Kotlin 예제** — Wrap Class (Decorator 변형):
```kotlin
// Before
interface UserRepository { fun findById(id: String): User? }
class SqlUserRepository(private val db: Database) : UserRepository {
    override fun findById(id: String): User? = db.query("SELECT ... WHERE id = ?", id)
}

// 요구: 모든 조회에 캐시 추가
// After — Wrap Class. SqlUserRepository 는 변경 없음
class CachingUserRepository(
    private val delegate: UserRepository,
    private val cache: Cache<String, User> = Cache(),
) : UserRepository {
    override fun findById(id: String): User? =
        cache.getOrPut(id) { delegate.findById(id) }
}

// DI 변경 — 한 줄
// 기존: bind<UserRepository>() with singleton { SqlUserRepository(db) }
// 신규: bind<UserRepository>() with singleton { CachingUserRepository(SqlUserRepository(db)) }
```

**Sprout vs Wrap 결정 매트릭스**:

| 요구 | 사용 기법 |
|------|----------|
| 기존 메서드 *내부 특정 지점* 에서 추가 동작 1회 | Sprout Method |
| 추가 동작이 자체 상태 / 다수 메서드 | Sprout Class |
| 기존 메서드 *전체를 호출하는 모든 자리* 에 동작 추가 | Wrap Method |
| 기존 클래스 *전체 인터페이스* 를 감싸야 함 | Wrap Class |

**Anti-pattern 주의**:
- Wrap Method 에서 wrapper 와 core 가 *같은 책임* 을 분담하면 응집도 무너짐 — wrapper 는 *직교 관심사* (감사 / 캐시 / 권한) 만
- Wrap Class 가 점점 두꺼워져서 또 다른 leg acy 가 되지 않게

**관련 기법 / 스멜**:
- [sprout-method-class](#sprout-method-class) — 추가 동작이 *지점* 일 때
- [extract-interface-testability](#extract-interface-testability) — Wrap Class 는 인터페이스 분리 선행
- [decorator](structural.md) — Wrap Class 의 GoF 본가 패턴

---

<a id="sensing-variable"></a>
## 5. Sensing Variable

**언제 적용**: 메서드의 *내부 동작* 을 검증하고 싶지만 반환값이 없거나 (`void`) 외부 상태로 드러나지 않을 때. 부수효과만 있는 메서드, private 헬퍼의 호출 여부 / 순서 / 횟수 검증 등.

**기법 요약**: 테스트가 *관찰* 할 수 있도록 클래스 내부에 *센싱용 필드* 를 임시로 추가하고, 운영 코드의 핵심 지점에서 그 필드에 값을 기록. 테스트는 메서드 호출 후 필드를 읽어 검증. Mock 객체를 도입하기 어렵거나, mock 도입 자체가 큰 변경일 때 *최소 침습* 대안.

**제약**: 이 기법은 *임시* — characterization 이 충분히 갖춰지면 sensing variable 을 제거하고 정식 mock / Test Double 로 대체. Production 코드에 영구히 남기지 않는다 (대안: `@VisibleForTesting`).

**적용 절차**:
1. 검증하고 싶은 *내부 사건* 식별 (특정 분기 진입, private 메서드 호출 횟수, 외부 호출 여부 등)
2. 클래스에 *protected* / *package-private* 필드 추가 — `internal var sensedThing: Int = 0` (Kotlin) / `protected int sensedThing` (Java)
3. 사건 발생 지점에서 필드 갱신 — `sensedThing++` 또는 `lastCall = "X"`
4. 테스트에서 메서드 호출 후 필드 검증
5. 더 나은 seam 이 생기면 mock / Test Double 로 교체하고 sensing variable 제거

**난이도**: 낮음 | **사용 빈도**: ★★ (응급 처치 성격. 정식 mock 대체가 우선)

**Kotlin 예제**:
```kotlin
// Before — void 메서드. 내부 분기 검증 불가
class Cleanup(private val store: Store) {
    fun sweep() {
        val items = store.findAll()
        for (item in items) {
            if (item.expired()) {
                store.delete(item.id)
                // 알림 / 로그 / 메트릭 — 외부에서 관찰 불가
            }
        }
    }
}

// After — Sensing Variable 추가
class Cleanup(private val store: Store) {
    @VisibleForTesting internal var deletedCount: Int = 0
    @VisibleForTesting internal val deletedIds: MutableList<String> = mutableListOf()

    fun sweep() {
        val items = store.findAll()
        for (item in items) {
            if (item.expired()) {
                store.delete(item.id)
                deletedCount++
                deletedIds += item.id
            }
        }
    }
}

// 테스트 — sensing variable 로 검증
@Test fun `sweep deletes only expired items`() {
    val store = InMemoryStore(listOf(
        Item("A", expired = false),
        Item("B", expired = true),
        Item("C", expired = true),
    ))
    val cleanup = Cleanup(store)

    cleanup.sweep()

    assertEquals(2, cleanup.deletedCount)
    assertEquals(listOf("B", "C"), cleanup.deletedIds)
}

// 다음 단계 (시간 허용 시): store 를 Spy / Mock 으로 교체하고 sensing variable 제거
```

**Anti-pattern 주의**:
- Sensing variable 이 *production 동작에 영향* 을 미치면 안 됨 — 순수 관찰자
- 영구 잔존 금지. characterization 보강 후 정식 Test Double 로 마이그레이션
- 동시성 코드에서는 sensing variable 도 thread-safe 해야 (volatile / AtomicInteger)

**관련 기법 / 스멜**:
- [characterization-test](#characterization-test) — sensing variable 은 characterization 의 검증 수단
- [testing.md#test-double](testing.md) — 정식 대체. Spy 가 sensing variable 의 OO 본가
- [extract-and-override](#extract-and-override) — protected 추출로 더 자연스러운 sensing 가능

---

<a id="extract-interface-testability"></a>
## 6. Extract Interface (for testability)

**언제 적용**: 구체 클래스에 직접 의존하는 코드를 mock 으로 교체하고 싶을 때. 원본 클래스의 변경 권한이 없거나 (서드파티), 다른 곳에서 직접 인스턴스화하고 있어 인터페이스 도입 자체가 큰 변경일 때.

**기법 요약**: 구체 클래스에서 *사용 중인 공개 메서드들* 만 골라 인터페이스로 추출. 의존 측 코드는 인터페이스에 의존하도록 변경. 원본 클래스는 새 인터페이스를 구현하게 함. 테스트는 인터페이스를 fake / mock 으로 구현.

Fowler 의 *Extract Interface* 와 동일하지만, Feathers 는 *테스트 가능성* 이라는 동기를 강조 — 완전한 인터페이스가 아니라 *내가 호출하는 것만* 추출하는 게 핵심 (ISP).

**적용 절차**:
1. 의존 측 코드에서 구체 클래스의 *실제 호출 메서드* 만 식별 (전체 public API 다 추출 X)
2. 새 인터페이스 작성 — 식별된 메서드 시그니처만
3. 원본 클래스가 새 인터페이스를 `implements` / `: Interface` 하게 한 줄 추가
4. 의존 측 코드의 타입을 구체 → 인터페이스로 변경
5. 테스트에서 인터페이스를 fake / mock 으로 구현해 주입
6. (선택) 시간이 지나며 다른 호출자가 같은 인터페이스를 쓰게 통합

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제** — 서드파티 구체 클래스 격리:
```kotlin
// Before — 서드파티 SDK 의 구체 클래스에 직접 의존. mock 불가능
class NotificationService(private val sdk: VendorPushSdk) {
    fun notifyUser(userId: String, msg: String) {
        sdk.connect()
        val token = sdk.lookupToken(userId)
        sdk.send(token, msg)
    }
}

// After — Extract Interface (사용하는 3 개 메서드만)
interface PushClient {
    fun connect()
    fun lookupToken(userId: String): String
    fun send(token: String, msg: String)
}

// 어댑터 — 원본 SDK 를 인터페이스에 맞춤
class VendorPushClientAdapter(private val sdk: VendorPushSdk) : PushClient {
    override fun connect() = sdk.connect()
    override fun lookupToken(userId: String): String = sdk.lookupToken(userId)
    override fun send(token: String, msg: String) = sdk.send(token, msg)
}

// 의존 측은 인터페이스로
class NotificationService(private val push: PushClient) {
    fun notifyUser(userId: String, msg: String) {
        push.connect()
        val token = push.lookupToken(userId)
        push.send(token, msg)
    }
}

// 테스트 — fake 구현
@Test fun `notify uses token from lookup`() {
    val sent = mutableListOf<Pair<String, String>>()
    val fake = object : PushClient {
        override fun connect() {}
        override fun lookupToken(userId: String) = "token-$userId"
        override fun send(token: String, msg: String) { sent += token to msg }
    }
    NotificationService(fake).notifyUser("u-1", "hi")
    assertEquals(listOf("token-u-1" to "hi"), sent)
}
```

**ISP 와 결합** — 호출하는 메서드만 추출:
```kotlin
// VendorPushSdk 가 50 개 메서드를 노출해도, NotificationService 가 쓰는 3 개만 PushClient 에 둠
// → 다른 곳에서 PushClient 를 구현할 때 부담 최소화 (ISP)
// → 향후 다른 vendor 어댑터 추가 비용 낮음
```

**Anti-pattern 주의**:
- 원본 구체 클래스의 *모든* public API 를 인터페이스로 옮기지 않음 (ISP 위반)
- 인터페이스 이름은 *사용 측 관점* — `PushClient` ✓, `VendorPushSdkInterface` ✗
- 추출 후 원본 구체 클래스를 어디서도 *직접* 참조하지 않게 (IDE 의 Find Usages 로 확인)

**관련 기법 / 스멜**:
- [seam-types](#seam-types) — Object Seam 의 가장 흔한 형태
- [wrap-method-class](#wrap-method-class) — Extract Interface 후 데코레이터 적용
- [dip](../principles/solid.md#5-dependency-inversion-principle-dip-의존성-역전-원칙), [isp](../principles/solid.md#4-interface-segregation-principle-isp-인터페이스-분리-원칙)
- [adapter](structural.md) — VendorPushClientAdapter 는 GoF Adapter

---

<a id="extract-and-override"></a>
## 7. Extract and Override

**언제 적용**: 한 메서드 내부의 *특정 호출* (생성자, static 호출, getter) 만 테스트에서 교체하고 싶은데, 그 호출이 너무 깊이 박혀 있어 Extract Interface 가 과한 변경일 때. 짧은 작업으로 *임시 seam* 을 만드는 가장 가벼운 수단.

**기법 요약**: 교체하고 싶은 *한 줄 호출* 을 같은 클래스의 새 protected 메서드로 추출. 테스트에서는 그 클래스를 서브클래싱하고 protected 메서드를 override 해 fake 동작 반환. 운영 코드의 변경은 *한 줄 추출* 뿐.

Feathers 의 *Extract and Override Call* / *Extract and Override Factory Method* / *Extract and Override Getter* 의 통합 카테고리.

**적용 절차**:
1. 테스트에서 교체하고 싶은 표현식 식별 (예: `new Connection(...)`, `SystemClock.now()`)
2. 그 표현식을 같은 클래스의 *protected* / *open* 메서드로 추출 — `protected fun createConnection(): Connection = Connection(...)`
3. 원래 자리는 `createConnection()` 호출로 교체
4. 테스트에서 SUT 의 *Testing Subclass* 작성 — `createConnection()` 을 override 해 fake 반환
5. SUT 의 다른 동작은 그대로

**난이도**: 낮음 | **사용 빈도**: ★★★★

**Java 예제** — Extract and Override Factory Method:
```java
// Before — 메서드 안에서 직접 new. 테스트가 실제 DB 에 연결 시도
public class ReportService {
    public Report generate(String userId) {
        Connection conn = new Connection("jdbc:postgresql://prod/...");  // 직접 생성
        try {
            return new Report(conn.query(userId));
        } finally {
            conn.close();
        }
    }
}

// After — Extract Factory Method
public class ReportService {
    public Report generate(String userId) {
        Connection conn = createConnection();   // ← 추출된 호출
        try {
            return new Report(conn.query(userId));
        } finally {
            conn.close();
        }
    }

    protected Connection createConnection() {
        return new Connection("jdbc:postgresql://prod/...");
    }
}

// 테스트 — Testing Subclass
class ReportServiceTest {
    @Test
    void generateProducesReportFromFakeConnection() {
        ReportService sut = new ReportService() {
            @Override
            protected Connection createConnection() {
                return new FakeConnection(Map.of("u-1", "fake row"));
            }
        };
        Report report = sut.generate("u-1");
        assertEquals("fake row", report.body());
    }
}
```

**Kotlin 예제** — Extract and Override Getter:
```kotlin
// Before — static 시계 의존
class SessionTracker {
    fun isExpired(session: Session): Boolean =
        System.currentTimeMillis() - session.startedAt > SESSION_TTL_MS
}

// After — Extract and Override Getter
open class SessionTracker {
    fun isExpired(session: Session): Boolean =
        currentTimeMillis() - session.startedAt > SESSION_TTL_MS

    protected open fun currentTimeMillis(): Long = System.currentTimeMillis()
}

// 테스트
@Test fun `expired when start older than TTL`() {
    val tracker = object : SessionTracker() {
        override fun currentTimeMillis() = 10_000L
    }
    val session = Session(startedAt = 0L)
    assertTrue(tracker.isExpired(session))   // 10_000 - 0 > TTL
}
```

**Extract and Override vs Extract Interface 결정**:

| 상황 | 선택 |
|------|------|
| 교체할 호출이 1~2 군데 + 임시 분리 | Extract and Override (가벼움) |
| 같은 인터페이스를 여러 곳에서 사용 | Extract Interface (영구 분리) |
| 클래스가 final / sealed 라 상속 불가 | Extract Interface 필수 |
| 의존성이 한 객체가 아니라 *분리된 호출 묶음* | Extract and Override |

**Anti-pattern 주의**:
- Testing Subclass 가 *production 동작* 을 변경하면 안 됨 — 테스트용 override 만
- Kotlin 에서는 클래스 / 메서드 모두 `open` 이어야 — final-by-default 정책 위반 정당화 필요
- 영구화될 의존성이라면 Extract Interface 로 전환 (Extract and Override 는 *임시 도구*)

**관련 기법 / 스멜**:
- [extract-interface-testability](#extract-interface-testability) — 영구적 분리가 필요하면
- [subclass-and-override-method](#subclass-and-override-method) — 의존 *객체* 자체를 교체할 때
- [seam-types](#seam-types) — Object Seam 의 minimal 변형
- [template-method](behavioral.md) — protected hook 의 패턴 본가

---

<a id="subclass-and-override-method"></a>
## 8. Subclass and Override Method

**언제 적용**: 의존 *객체* 의 특정 메서드 동작만 교체하고 싶을 때. 그 객체를 fake 로 처음부터 작성하기엔 동작 대부분이 그대로 필요할 때.

**기법 요약**: 의존 객체 클래스를 *테스트 안에서* 서브클래스로 확장하고 *교체하려는 메서드만* override. 나머지 동작은 super 의 것 그대로 사용. Mock 라이브러리의 *partial mock* / *spy* 의 OO 본가.

Extract and Override 가 *SUT 자신의 메서드 추출* 이라면, Subclass and Override Method 는 *SUT 가 의존하는 객체의 메서드 override*. 둘은 자주 짝지어 쓰임.

**적용 절차**:
1. 의존 객체 클래스 식별 — 상속 가능해야 (open / non-final)
2. 교체할 메서드 식별 — protected 또는 public, virtual / open 이어야
3. 테스트 안에서 anonymous subclass 또는 inner class 작성. 해당 메서드만 override
4. SUT 에 이 subclass 인스턴스 주입
5. 나머지 동작은 원본 그대로 (super 호출 또는 비-override)

**난이도**: 낮음~중간 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// 의존 객체 — 대부분 동작은 그대로 두고 한 메서드만 fake
open class PaymentGateway {
    open fun authorize(card: String, amount: Long): AuthResult = /* 실제 HTTP 호출 */
    open fun capture(authId: String): CaptureResult = /* 실제 HTTP */
    fun formatAmount(amount: Long): String = "$%.2f".format(amount / 100.0)  // 그대로 쓰고 싶음
}

// SUT
class CheckoutService(private val gateway: PaymentGateway) {
    fun checkout(cart: Cart, card: String): CheckoutResult {
        val auth = gateway.authorize(card, cart.total())
        if (!auth.ok) return CheckoutResult.Declined(gateway.formatAmount(cart.total()))
        val cap = gateway.capture(auth.id)
        return CheckoutResult.Success(cap.transactionId)
    }
}

// 테스트 — authorize 만 fake, formatAmount 는 원본
@Test fun `declined cart formats amount via real gateway helper`() {
    val gateway = object : PaymentGateway() {
        override fun authorize(card: String, amount: Long) = AuthResult(ok = false, id = "")
        override fun capture(authId: String): CaptureResult = error("should not be called")
        // formatAmount 는 override 안 함 → 원본 구현 사용
    }
    val service = CheckoutService(gateway)
    val result = service.checkout(Cart(items = listOf(Item(price = 12345))), card = "...")
    assertEquals(CheckoutResult.Declined("$123.45"), result)
}
```

**Mockito Spy 와의 관계** (Java):
```java
// 같은 효과를 mockito 로
PaymentGateway gateway = Mockito.spy(new PaymentGateway());
Mockito.doReturn(new AuthResult(false, ""))
       .when(gateway).authorize(anyString(), anyLong());
// formatAmount 는 자동으로 real method 호출
```

**Anti-pattern 주의**:
- Override 한 메서드가 원본 동작을 *추정* 으로 재현하면 위험 — *완전히 다른 동작* 으로 만들거나, *원본 + 부가 동작* (super 호출) 이거나
- final / sealed 클래스에는 적용 불가 → Extract Interface 우회
- override 한 메서드와 super 사이에 의존이 있으면 (template method 형태) super 호출 누락 시 깨짐

**관련 기법 / 스멜**:
- [extract-and-override](#extract-and-override) — SUT 자신의 메서드 교체
- [extract-interface-testability](#extract-interface-testability) — 상속 불가능할 때 대안
- [testing.md#test-double](testing.md) — Spy / Partial Mock 의 카테고리
- [lsp](../principles/solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙) — override 는 LSP 위반 위험

---

<a id="break-out-method-object"></a>
## 9. Break Out Method Object

**언제 적용**: 한 메서드가 수백 줄에 달하고, 지역 변수 / 매개변수가 너무 많아 [Extract Function](../principles/refactoring-techniques.md#extract-function) 으로 쪼개려 해도 변수 의존성 때문에 매개변수 지옥에 빠지는 경우.

**기법 요약**: Kent Beck *Smalltalk Best Practice Patterns* 의 *Method Object* 를 Feathers 가 레거시 맥락으로 가져온 것. *그 메서드 하나만을 위한 새 클래스* 를 만들어 매개변수와 지역 변수를 인스턴스 필드로 옮김. 이후 그 클래스 내부에서 자유롭게 메서드 추출 가능 (필드 공유 → 매개변수 없이).

**적용 절차**:
1. 추출 대상 메서드 식별 (보통 100+ 줄, 지역 변수 10+ 개)
2. 새 클래스 이름 결정 — 메서드의 *목적* 을 명사화 (`calculateInvoice()` → `class InvoiceCalculator`)
3. 새 클래스의 생성자에 원본 메서드의 *모든 매개변수* + 호출 컨텍스트 객체 추가
4. 원본 메서드의 *지역 변수* 를 모두 인스턴스 필드로 승격
5. 원본 메서드 본문을 새 클래스의 단일 메서드 (`compute()` / `run()` / `execute()`) 로 복사
6. 원본 메서드는 새 클래스 인스턴스화 + 호출로 위임 (한 줄)
7. 이제 새 클래스 안에서 자유롭게 [Extract Function](../principles/refactoring-techniques.md#extract-function) 적용

**난이도**: 중간 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Before — 200 줄짜리 메서드. 지역 변수 15 개. 추출하려면 매개변수 8 개씩 받아야
class InvoiceService {
    fun calculate(order: Order, customer: Customer, rates: TaxRates, today: LocalDate): Invoice {
        var subtotal = 0L
        var taxableSubtotal = 0L
        var discount = 0L
        var vipBonus = 0L
        val lineItems = mutableListOf<LineItem>()
        // ... 200 줄: 라인 아이템 빌드, 할인 계산, 세금 계산, 배송비, 통화 변환, ...
        return Invoice(/* ... */)
    }
}

// After — Method Object 로 분해
class InvoiceService {
    fun calculate(order: Order, customer: Customer, rates: TaxRates, today: LocalDate): Invoice =
        InvoiceCalculator(order, customer, rates, today).compute()
}

// 새 클래스 — 매개변수와 지역 변수가 모두 필드로
class InvoiceCalculator(
    private val order: Order,
    private val customer: Customer,
    private val rates: TaxRates,
    private val today: LocalDate,
) {
    private var subtotal: Long = 0
    private var taxableSubtotal: Long = 0
    private var discount: Long = 0
    private var vipBonus: Long = 0
    private val lineItems = mutableListOf<LineItem>()

    fun compute(): Invoice {
        buildLineItems()
        applyDiscounts()
        applyVipBonus()
        calculateTaxes()
        return Invoice(/* ... */)
    }

    // 이제 매개변수 없이 자유롭게 추출 가능 (필드 공유)
    private fun buildLineItems() {
        for (item in order.items) {
            val li = LineItem(item.sku, item.qty, item.price)
            lineItems += li
            subtotal += li.amount
            if (item.taxable) taxableSubtotal += li.amount
        }
    }
    private fun applyDiscounts() { /* ... 필드만 사용 ... */ }
    private fun applyVipBonus()  { /* ... */ }
    private fun calculateTaxes() { /* ... */ }
}
```

**테스트 가능성 향상**:
- 새 클래스의 각 private 메서드는 [Extract and Override](#extract-and-override) 로 더 쪼갤 수 있음
- 인스턴스 상태가 명시화되어 *중간 상태 검증* 가능 ([sensing-variable](#sensing-variable) 과 결합)
- 새 클래스는 처음부터 *생성자 주입* 으로 의존성을 받을 수 있어 mock 적용 자연스러움

**Anti-pattern 주의**:
- 새 클래스가 *재사용성* 을 추구하지 않음 — *그 메서드를 위한* 클래스. SRP 가 한 메서드 단위로 좁혀짐
- 인스턴스를 두 번 재사용하지 말 것 (상태가 누적됨). 한 번 쓰고 버리는 *consumable* 객체
- 외부에서 인스턴스화하지 않게 — 생성자를 internal / package-private 으로 (호출은 InvoiceService 만)

**관련 기법 / 스멜**:
- [extract-function](../principles/refactoring-techniques.md#extract-function), [extract-class](../principles/refactoring-techniques.md) — Method Object 후 안전한 환경에서 적용
- [code-smell-long-method](../principles/code-smells.md#1-long-method-긴-메서드), [code-smell-long-parameter-list](../principles/code-smells.md) — 본 기법의 일차 적용 대상
- [command](behavioral.md) — Method Object 는 Command 패턴의 변형 (execute() 단일 메서드)
- [srp](../principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) — 추출된 클래스의 책임은 *그 한 메서드* 로 좁혀짐

---

<a id="mikado-method"></a>
## 10. Mikado Method

**언제 적용**: 단일 변경이 *광범위한 사전 변경* 을 요구하는 큰 리팩토링 (인터페이스 변경, 아키텍처 재편, 라이브러리 이주). "그냥 시작했다가 빌드가 일주일 깨져 있는" 사태를 막아야 할 때.

**기법 요약**: Daniel Brolund & Ola Ellnestam (2010~2014) 이 정립. 핵심 명령 — **"항상 빌드가 통과하는 상태로 돌아갈 수 있어야 한다"** (always green). 목표를 노드로, *그 목표를 달성하기 위해 먼저 해야 할 일* 들을 자식 노드로 그려 의존성 그래프 (Mikado Graph) 를 만들고, **leaf** 부터 작업.

이름의 유래: 일본/유럽의 막대 게임 *미카도*. 막대 더미에서 다른 막대를 건드리지 않고 하나씩 빼내는 게임. 큰 변경을 leaf 부터 *건드리지 않고* 빼내는 비유.

**Mikado Graph 구조**:
```
              [GOAL: Replace ORM with new DAO layer]
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
[Add IOrderDao] [Add IUserDao]  [Replace transaction  [Migrate 3rd
        │               │       boundary calls]      party plugin]
        │               │               │              │
   ┌────┴────┐    [Extract User    [Move tx start to   [Find replacement
   │         │     interface from   service layer]     for legacy plugin]
[Extract  [Add test    User entity]
 Order    coverage
 interface] for Order]
   │
[Add test
 coverage]
```

Leaf (밑줄 노드) 부터 작업. 각 leaf 완료 후 commit → 빌드 PASS 확인 → 다음 leaf.

**적용 절차**:
1. **목표 (Goal)** 를 종이 / Miro / Mermaid 에 적음 — root node
2. *순진하게* (naively) 시작: 직접 변경 시도
3. 변경 시 **컴파일 에러 / 테스트 실패 / 런타임 에러** 가 발견되면 → 그게 *prerequisite (사전 조건)* 임. 자식 노드로 추가
4. **변경 되돌리기 (revert)** — 빌드를 green 으로 되돌림
5. prerequisite 중 하나 선택 (leaf 우선) → 재귀적으로 2~5 반복
6. 그래프의 leaf 가 *실제로 수행 가능* (다른 prerequisite 없음) 하면 → 실행 → commit → 그 노드 *cross-off*
7. 그래프가 비워질 때까지 반복. 마지막에 root 변경이 *trivial* 하게 적용됨

**핵심 규칙**:
- **항상 revert 가능** — naive 시도 후 발견만 하고 *바로 되돌린다*. 시도를 누적해 빌드가 깨진 상태로 두지 않음
- **Leaf 우선** — 깊이 우선 (DFS) 으로 leaf 까지 내려가 거기서부터 위로 올라옴
- **각 leaf 가 독립 commit** — 작은 commit 으로 PR / revert 가능성 유지
- **그래프는 살아있는 문서** — 작업 진행 중 새 prerequisite 발견 시 노드 추가

**난이도**: 중간~높음 | **사용 빈도**: ★★★★ (큰 리팩토링의 *유일하게 안전한* 방법)

**예제** — 모놀리스 모듈을 별도 서비스로 분리:

```
GOAL: Move Notification logic to separate service
  ├─ Decouple Notification from User aggregate          [leaf 후보]
  │   ├─ Extract NotificationPreference value object   [LEAF ★]
  │   └─ Remove direct DB join in UserRepository       [leaf 후보]
  │       └─ Add NotificationPreference table         [LEAF ★]
  ├─ Replace direct Notification calls with event publish
  │   ├─ Add domain event NotificationRequested        [LEAF ★]
  │   └─ Wire event bus in 4 callsites                 [leaf 후보]
  │       └─ Install in-memory event bus               [LEAF ★]
  └─ Move Notification module to /services/notification
      └─ (depends on all above)                        [non-leaf]
```

**작업 순서** (cross-off):
1. `Extract NotificationPreference VO` → commit → green
2. `Add NotificationPreference table` (migration) → commit → green
3. `Remove direct DB join` → commit → green
4. `Decouple Notification from User aggregate` → commit → green
5. `Add domain event NotificationRequested` → commit → green
6. `Install in-memory event bus` → commit → green
7. `Wire event bus in 4 callsites` → commit → green
8. `Replace direct calls with event publish` → commit → green
9. `Move Notification module to /services/notification` → commit → green ← root 달성

각 단계는 *한 PR 단위*. 중간에 일이 끊겨도 시스템은 항상 동작 상태.

**도구**:
- 종이 + 포스트잇 (Brolund 권장 — 빠르고 그래프 갱신 자연스러움)
- Mermaid `graph TD` 또는 Excalidraw / Miro / Whimsical
- 텍스트 outline (vim / markdown) — leaf 표시는 `[x]` 체크박스

**다른 패턴과의 비교**:

| 큰 변경 전략 | 작동 방식 | 적용 시점 |
|--------------|----------|----------|
| **Mikado Method** | leaf-first, always green, revert often | 의존성 그래프 그릴 수 있는 *체계적* 변경 |
| **Branch by Abstraction** | 새/구 구현을 인터페이스 뒤에 공존 → 점진 교체 | 라이브러리 이주, 구현 swap |
| **Strangler Fig** | 새 시스템을 옆에 키워 기존을 점진 흡수 | 모놀리스 → 마이크로서비스 |
| **Big Bang Rewrite** | 멈추고 전부 다시 작성 | (지양 — *Joel on Software* "Things You Should Never Do") |

Mikado 는 위 다른 전략들과 *결합* 가능 — Branch by Abstraction 으로 가는 길 자체를 Mikado Graph 로 그려서 진행.

**Anti-pattern 주의**:
- **그래프 안 그리고 시작** — Mikado 의 핵심은 *그래프*. 머릿속으로만 하면 의존성 누락
- **leaf 가 아닌 노드를 먼저 작업** — 다른 prerequisite 미해결 상태로 진행 → 빌드 깨짐
- **revert 하지 않고 시도 누적** — "조금만 더 하면 될 것 같은데" 가 가장 위험
- **commit 단위가 너무 큼** — leaf 하나 = commit 하나가 원칙. 큰 commit 은 revert 비용 증가

**관련 기법 / 스멜**:
- [characterization-test](#characterization-test) — Mikado 의 각 leaf 전에 안전망
- [sprout-method-class](#sprout-method-class), [wrap-method-class](#wrap-method-class) — leaf 작업 시 자주 결합
- [strangler-fig](deployment.md), [branch-by-abstraction](deployment.md) — 상위 전략 패턴
- [anti-patterns.md#big-ball-of-mud](anti-patterns.md) — Mikado 가 빠져나오는 본격 anti-pattern
- [ddd-tactical.md](ddd-tactical.md) — Bounded Context 식별이 Mikado 그래프의 자연스러운 leaf 후보

---

## 부록 A. 기법 선택 가이드

| 상황 | 권장 기법 |
|------|----------|
| 어디부터 시작할지 모름 | [Seam 식별](#seam-types) → [Characterization Test](#characterization-test) |
| 명세 없는 메서드를 변경해야 함 | [Characterization Test](#characterization-test) |
| 거대 메서드에 새 기능 추가 | [Sprout Method](#sprout-method-class) |
| 거대 메서드에 새 *모듈* 추가 | [Sprout Class](#sprout-method-class) |
| 모든 호출자에 동작 추가 | [Wrap Method](#wrap-method-class) |
| 클래스 전체를 데코레이트 | [Wrap Class](#wrap-method-class) |
| void 메서드의 내부 동작 검증 | [Sensing Variable](#sensing-variable) |
| 서드파티 SDK 분리 | [Extract Interface](#extract-interface-testability) |
| 한 줄 호출만 교체 | [Extract and Override](#extract-and-override) |
| 의존 객체의 일부 동작만 교체 | [Subclass and Override Method](#subclass-and-override-method) |
| 200+ 줄 메서드 해체 | [Break Out Method Object](#break-out-method-object) |
| 광범위한 사전 변경 필요 | [Mikado Method](#mikado-method) |

## 부록 B. Feathers 6 단계 작업 흐름

*Working Effectively with Legacy Code* Chapter 3 의 표준 워크플로우:

1. **변경할 지점 식별** — change point. 어디를 건드릴지
2. **테스트 지점 식별** — test point. characterization 을 어디에 둘지 (보통 change point 보다 *바깥쪽*)
3. **의존성 끊기** — break dependencies. 위 [seam-types](#seam-types) / [extract-interface](#extract-interface-testability) / [extract-and-override](#extract-and-override) / [subclass-and-override](#subclass-and-override-method) 사용
4. **테스트 작성** — [characterization-test](#characterization-test). 현재 동작 잠금
5. **변경 + 리팩토링** — 테스트가 PASS 인 상태에서. [refactoring-techniques.md](../principles/refactoring-techniques.md) 의 Fowler 기법 자유롭게 적용
6. **테스트 재실행** — 모든 characterization 이 여전히 PASS 여야. 깨졌다면 의도된 변경인지 회귀인지 판별

큰 변경이면 1~6 을 [Mikado Method](#mikado-method) 의 각 leaf 에 적용.

## 부록 C. 언어별 도구 참고

| 언어 | 도움 도구 |
|------|----------|
| Java | Mockito spy, AssertJ, Approvaltests-java, ArchUnit, JaCoCo (coverage) |
| Kotlin | MockK, kotest, Approvaltests-java (호환), `@VisibleForTesting`, Kover |
| C# | Moq, NSubstitute, ApprovalTests.NET, NCrunch |
| C/C++ | googletest, googlemock, link seam 활용, `#define` preprocessing seam |
| JavaScript / TypeScript | Jest snapshot, sinon spy, msw (network seam), nyc coverage |
| Python | unittest.mock, pytest, approvaltests-python, coverage.py |
| Ruby | RSpec doubles, vcr (network seam), simplecov |
| Go | interface-based seam (compiler 가 implicit 구현), gomock, golden file test |

---

*본 카탈로그는 Feathers 의 모든 기법을 다루지 않는다. 원전에는 24+ 기법이 있으며, 본 10 항목은 한국어 환경에서 가장 자주 마주치는 패턴 중심. 더 깊은 학습은 *Working Effectively with Legacy Code* (Prentice Hall, 2004) 직접 참조.*
