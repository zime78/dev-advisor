# 에러 처리 패턴 (Error Handling Patterns)

SWEBOK KA3 Construction Fundamentals 의 핵심 영역. 정평 있는 11 에러 처리 전략. 함수 시그니처·트랜잭션 경계·외부 호출 어느 곳에서 어떤 패턴을 쓸지 결정.

**원전 참고**:
- Joshua Bloch — *Effective Java*, 3rd ed., Items 69-77 (Exception)
- Scott Wlaschin — *Domain Modeling Made Functional* (2018), Chapter 10 (Railway-Oriented)
- Roy Osherove — *The Art of Unit Testing* (Fail-Fast 논의)
- Rust *Programming Language* — Chapter 9 "Error Handling"

**핵심 원칙**:
- **Errors are values** (Rob Pike, Go) — 예외를 값으로 다루기
- **Validate at the boundary** — 외부 입력 경계에서 한 번만 검증, 내부 trust
- **Recoverable vs unrecoverable 분리** — 비즈니스 오류(예: 잔액 부족) vs 시스템 오류(예: OOM)

**관련 카탈로그**:
- [reliability.md](reliability.md) — Circuit Breaker / Retry / Bulkhead / Timeout (런타임 실패 회복)
- [distributed.md](distributed.md) — Saga / Outbox / Idempotency Key
- [`../principles/code-smells.md`](../principles/code-smells.md) — Catch & Ignore 안티패턴

---

<a id="exception-checked-unchecked"></a>
## 1. Exception (체크/언체크)

**목적**: 정상 흐름과 분리된 별도 채널로 비정상 상황을 상위 호출자에게 전파합니다. 스택 unwinding 으로 호출 경로의 자원 해제와 컨텍스트 보존을 함께 처리합니다.

**특징**:
- **Checked (Java)**: 컴파일러가 `throws` 선언과 try-catch 를 강제. 호출자가 명시적으로 처리해야 함
- **Unchecked (RuntimeException)**: 선언 의무 없음. 프로그래밍 오류 / 복구 불가능 상황에 사용
- Kotlin / Swift / Python / C# 은 **unchecked only** 모델 — checked 의 시그니처 오염을 회피
- `Throwable` 계층: `Error` (JVM 자원 고갈 등 복구 불가) vs `Exception` (애플리케이션 처리 영역)

**장점**:
- 정상 경로 코드가 깨끗하게 유지 (return code 분기가 사라짐)
- 스택 트레이스 자동 수집 — 디버깅 정보 풍부
- 자원 해제 (`try-with-resources` / `use {}`) 와 결합 자연스러움

**단점**:
- Checked 는 시그니처 오염 — 호환성 끊김, "throws 폭탄"
- 예외 던지기 비용 — JVM 에서 stack trace 수집은 비용 큼 (control flow 로 쓰면 안 됨)
- 비즈니스 로직 오류(잔액 부족 등)에 예외를 쓰면 **정상 흐름이 흐려진다** (Effective Java Item 69)

**활용 예시**:
- IO 오류, 네트워크 timeout, DB connection 실패
- 인자 검증 실패 (`IllegalArgumentException`)
- 프로그래밍 버그 표시 (`IllegalStateException`)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Bad: 비즈니스 오류를 예외로 — 정상 흐름을 더럽힘
class InsufficientFundsException : RuntimeException()
fun withdraw(account: Account, amount: Int): Account {
    if (account.balance < amount) throw InsufficientFundsException()
    return account.copy(balance = account.balance - amount)
}

// Good: 시스템 오류만 예외, 비즈니스 오류는 값
class DbConnectionException(cause: Throwable) : RuntimeException(cause)
sealed class WithdrawResult {
    data class Ok(val account: Account) : WithdrawResult()
    object InsufficientFunds : WithdrawResult()
}
fun withdraw(account: Account, amount: Int): WithdrawResult =
    if (account.balance < amount) WithdrawResult.InsufficientFunds
    else WithdrawResult.Ok(account.copy(balance = account.balance - amount))
```

**관련 패턴**: [Result / Either](#result-either-monad), [Option / Maybe](#option-maybe), [Fail-Fast](#fail-fast-safe)

---

<a id="error-code-sentinel"></a>
## 2. Error Code / Sentinel Value

**목적**: 호출 결과를 반환값에 인코딩합니다. 성공/실패 분기를 호출자가 명시적으로 검사하도록 강제합니다.

**특징**:
- **Errno 스타일 (C)**: 함수 return 은 -1 / NULL, 전역 `errno` 에 실패 코드
- **Tuple 반환 (Go)**: `value, err := f()` — 다중 반환값으로 둘을 동시에
- **Sentinel value**: `-1`, `NULL`, `""`, `NaN` 같은 "이 값은 실패를 의미" 약속
- **상태 코드 반환**: HTTP `4xx/5xx`, POSIX `EEXIST` 같은 enum

**장점**:
- 오버헤드 없음 — 스택 unwinding 비용 zero
- 시그니처에 실패 가능성이 명시됨 (Go 의 `error` 인터페이스)
- 비예외 언어 (C, embedded) 에서 유일한 선택지

**단점**:
- **Sentinel 무시** 가 쉬움 — `read()` 의 -1 을 안 보면 silent corruption
- 정상 데이터와 sentinel 의 충돌 가능 (`-1` 이 실제 valid 값일 수 있음)
- Error code 가 호출 stack 따라 hand-propagate — 반복 boilerplate
- Go 의 `if err != nil { return err }` 도배 → 가독성 비판

**활용 예시**:
- C 시스템 콜 (`read`, `write`, `malloc`)
- Go 의 `os.Open`, `json.Unmarshal`
- POSIX `errno` / Windows `GetLastError`
- HTTP API 응답 코드

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Bad: Sentinel (-1) — 정상값과 충돌 위험 + 무시 가능
fun findUserId(name: String): Int {
    val u = repo.find(name) ?: return -1
    return u.id // 실제 id 가 -1 이면? user 가 검색 안된 것과 구별 불가
}

// Good: tuple-like (Pair) — Go 스타일. 컴파일러가 두 값 모두 강제
fun findUser(name: String): Pair<User?, String?> {
    return runCatching { repo.find(name) }
        .fold(
            onSuccess = { it to null },
            onFailure = { null to (it.message ?: "unknown") }
        )
}
// Caller
val (user, err) = findUser("alice")
if (err != null) log.warn("lookup failed: $err") else user?.let { process(it) }
```

**관련 패턴**: [Exception](#exception-checked-unchecked), [Result / Either](#result-either-monad), [Option / Maybe](#option-maybe)

---

<a id="result-either-monad"></a>
## 3. Result / Either 모나드

**목적**: 성공값과 실패값을 **하나의 타입 안에 합쳐서 반환**합니다. 컴파일 타임에 실패 처리를 강제하면서도 함수 합성을 지원합니다.

**특징**:
- **Rust** `Result<T, E>` — `Ok(T)` 또는 `Err(E)` 의 sum type
- **Haskell / Scala** `Either[L, R]` — 관습적으로 `Left = 실패`, `Right = 성공`
- **Kotlin** `kotlin.Result<T>` (예외만 담음) / Arrow `Either<L, R>`
- **Swift** `Result<Success, Failure>`
- `map` / `flatMap` (=bind) 으로 함수 합성 — 실패는 자동 전파 (short-circuit)

**장점**:
- 시그니처에 가능한 실패 타입이 노출 — 자기 문서화
- 호출자가 무시할 수 없음 (Rust 는 `#[must_use]` 강제)
- 합성 가능 — exception 의 try-catch 중첩 해소
- 비용 zero (allocation 만, stack unwinding 없음)

**단점**:
- 라이브러리 의존 (Kotlin 의 표준 `Result` 는 `E` 가 Throwable 고정 — Arrow 필요)
- 비-FP 개발자에게 학습 곡선
- 깊은 합성은 `map` / `flatMap` 체인이 길어짐 (→ Railway-Oriented + do-notation 으로 완화)

**활용 예시**:
- Rust 전 표준 라이브러리 (`File::open`, `str::parse`)
- Domain layer 의 비즈니스 검증 결과
- Functional Kotlin (Arrow), Scala Cats
- HTTP layer 의 응답 wrapping

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제** (Arrow Either):
```kotlin
import arrow.core.Either
import arrow.core.left
import arrow.core.right

sealed class WithdrawError {
    object InsufficientFunds : WithdrawError()
    data class DbFailure(val cause: Throwable) : WithdrawError()
}

fun loadAccount(id: String): Either<WithdrawError, Account> =
    runCatching { repo.load(id) }
        .fold({ it.right() }, { WithdrawError.DbFailure(it).left() })

fun withdraw(account: Account, amount: Int): Either<WithdrawError, Account> =
    if (account.balance < amount) WithdrawError.InsufficientFunds.left()
    else account.copy(balance = account.balance - amount).right()

// 합성 — 실패는 자동 전파
fun pay(id: String, amount: Int): Either<WithdrawError, Account> =
    loadAccount(id).flatMap { withdraw(it, amount) }
```

**관련 패턴**: [Railway-Oriented](#railway-oriented), [Option / Maybe](#option-maybe), [Error Aggregation](#error-aggregation)

---

<a id="railway-oriented"></a>
## 4. Railway-Oriented Programming

**목적**: 함수 합성 파이프라인을 두 트랙(성공 / 실패) 의 철도로 모델링합니다. 각 단계는 성공 트랙에서 처리되거나 실패 트랙으로 분기하며, 한번 실패 트랙으로 가면 끝까지 short-circuit 됩니다.

**특징**:
- Scott Wlaschin (2018, *Domain Modeling Made Functional*) 가 정립한 패턴 — F# / FP 커뮤니티에서 유래
- 핵심 콤비네이터: `bind` (=`flatMap`), `map`, `mapError`
- 입력 `T → Result<U, E>` 함수를 **연결**하는 어댑터 (`>>=`)
- 비즈니스 로직 검증·변환·저장의 **선형 파이프라인** 에 적합
- 도메인 에러를 sealed type 으로 모델링하여 모든 실패 경로를 컴파일러가 검증

**장점**:
- 흐름이 평탄 (try-catch 중첩 없음)
- 모든 가능한 실패가 타입에 노출 — 케이스 누락 시 컴파일 오류
- 단위 함수가 작고 합성 가능 (테스트 용이)
- 도메인 언어와 일치 — "검증 → 변환 → 저장" 이 코드로 보임

**단점**:
- 단일 실패 모드 가정 — 여러 에러 동시 수집은 [Error Aggregation](#error-aggregation) 필요
- 부수효과 (IO) 함수는 별도 lifting 필요
- 팀 학습 비용

**활용 예시**:
- 입력 검증 → 비즈니스 규칙 → DB 저장 파이프라인
- Domain Service 의 use-case 합성
- HTTP request → response 변환 흐름

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제** (Arrow Either, Sign-up 파이프라인):
```kotlin
import arrow.core.Either
import arrow.core.flatMap
import arrow.core.right
import arrow.core.left

sealed class SignupError {
    object EmailInvalid : SignupError()
    object PasswordTooWeak : SignupError()
    object EmailDuplicate : SignupError()
    data class DbFailure(val cause: Throwable) : SignupError()
}

// 각 단계: T -> Either<SignupError, U>
fun validateEmail(raw: String): Either<SignupError, Email> =
    Email.parse(raw)?.right() ?: SignupError.EmailInvalid.left()

fun validatePassword(raw: String): Either<SignupError, Password> =
    Password.parse(raw)?.right() ?: SignupError.PasswordTooWeak.left()

fun checkDuplicate(email: Email): Either<SignupError, Email> =
    if (userRepo.existsByEmail(email)) SignupError.EmailDuplicate.left()
    else email.right()

fun persist(email: Email, password: Password): Either<SignupError, User> =
    runCatching { userRepo.save(email, password) }
        .fold({ it.right() }, { SignupError.DbFailure(it).left() })

// Railway 합성 — 한 곳에서 실패하면 나머지는 skip
fun signup(rawEmail: String, rawPwd: String): Either<SignupError, User> =
    validateEmail(rawEmail)
        .flatMap { email -> checkDuplicate(email) }
        .flatMap { email -> validatePassword(rawPwd).map { pwd -> email to pwd } }
        .flatMap { (email, pwd) -> persist(email, pwd) }
```

**관련 패턴**: [Result / Either](#result-either-monad), [Error Aggregation](#error-aggregation), [Fail-Fast](#fail-fast-safe)

---

<a id="option-maybe"></a>
## 5. Option / Maybe

**목적**: 값의 **존재 여부**를 타입 시스템으로 표현합니다. `null` 의 무차별 사용 ("the billion-dollar mistake", Tony Hoare) 을 대체하여 NPE 를 컴파일 타임에 차단합니다.

**특징**:
- `Option<T>` (Scala / Rust) / `Optional<T>` (Java 8+) / `Maybe a` (Haskell)
- 두 상태: `Some(v)` / `None` (또는 `Just v` / `Nothing`)
- Kotlin / Swift / C# 8+ 는 **언어 차원 nullable** (`T?`) — Optional wrapper 없이 같은 효과
- `map` / `flatMap` / `getOrElse` / `?:` 콤비네이터로 안전 합성

**장점**:
- NPE 컴파일 타임 방지
- 시그니처에서 "없을 수 있음" 이 명시 — 자기 문서화
- 합성 가능 (chain 의 어느 단계가 None 이어도 안전 전파)

**단점**:
- **Java `Optional`** 은 필드 / 메서드 인자에 쓰지 말 것 (Brian Goetz 가이드 — return 값 전용)
- `Optional<Optional<T>>` 같은 wrapping 폭주
- "왜 없는지" 이유 정보가 사라짐 — 이유가 필요하면 `Result<T, E>` 로 격상

**활용 예시**:
- DB lookup (`findById` 가 없을 수 있음)
- Map 의 키 조회
- 옵션 설정 값
- 파싱 결과 (`String.toIntOrNull()`)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Bad: null 반환 + 호출자가 잊으면 NPE
fun findUser(id: String): User = repo.find(id)!! // force unwrap

// Good: nullable + safe operators
fun findUser(id: String): User? = repo.find(id)

// 합성 — 어느 단계가 null 이어도 전체가 null
val displayName: String = findUser(id)
    ?.profile
    ?.nickname
    ?.takeIf { it.isNotBlank() }
    ?: "anonymous"

// "왜 없는지" 가 필요하면 Either 로 격상
sealed class LookupError { object NotFound : LookupError(); object Forbidden : LookupError() }
fun loadUser(id: String, viewer: User): Either<LookupError, User> = when {
    !viewer.canView(id) -> LookupError.Forbidden.left()
    else -> repo.find(id)?.right() ?: LookupError.NotFound.left()
}
```

**관련 패턴**: [Result / Either](#result-either-monad), [Error Code](#error-code-sentinel), [Defensive Copying](#defensive-copying)

---

<a id="fail-fast-safe"></a>
## 6. Fail-Fast vs Fail-Safe

**목적**: 오류 발생 시 두 가지 상반된 정책 — 즉시 중단으로 **빠르게 노출** 할지, 가능한 한 동작을 이어가며 **안전하게 fallback** 할지를 선택합니다.

**특징**:
- **Fail-Fast**: 비정상 상태를 발견하면 즉시 예외 / panic / abort. 손상 전파 방지
  - Java `Iterator` 의 `ConcurrentModificationException`
  - `assert` / `require` / `check`
  - 부팅 시 설정 검증 (Spring `@PostConstruct` 검증)
- **Fail-Safe**: 오류를 흡수하고 default / cached / partial 결과로 진행
  - Java `ConcurrentHashMap` 의 weakly consistent iterator
  - Stale-while-revalidate 캐시
  - Default 설정으로 fallback

**장점 (Fail-Fast)**:
- 버그 조기 발견 — 디버깅 위치가 실제 원인과 가까움
- 손상 데이터의 추가 전파 차단
- 시스템 invariant 보존

**장점 (Fail-Safe)**:
- 가용성 (availability) 우선
- 부분 장애 시에도 핵심 기능 유지
- 사용자 체감 안정성

**단점**:
- Fail-Fast: 사소한 오류로 전체 중단 → 가용성 저하
- Fail-Safe: 오류 누적 → silent corruption / 디버깅 난이도 폭증

**활용 예시**:
- **Fail-Fast 적용**: 설정 로드, 인자 검증, invariant 검사, 도메인 일관성, 결제 트랜잭션
- **Fail-Safe 적용**: 추천 / 광고 / 분석 로그 (없어도 동작), 캐시 miss → fallback, 비핵심 위젯 렌더

**판단 기준**: "이 데이터로 잘못된 결과를 만드는 것" 과 "결과를 못 만드는 것" 중 어느 쪽이 더 나쁜가? 결제는 fail-fast (잘못된 결과 ≫ 못 만드는 것), 추천은 fail-safe (사용자에게 빈 화면 보이느니 stale 추천).

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Fail-Fast: 도메인 invariant 검사
data class Money(val amount: Long, val currency: String) {
    init {
        require(amount >= 0) { "amount must be non-negative: $amount" }
        require(currency.matches(Regex("[A-Z]{3}"))) { "invalid currency: $currency" }
    }
}

// Fail-Safe: 추천 시스템 (없어도 화면이 동작)
suspend fun loadRecommendations(userId: String): List<Item> =
    runCatching {
        withTimeout(500) { recommendApi.fetch(userId) }
    }.getOrElse {
        log.warn("recommendation failed, falling back to top-100: ${it.message}")
        cachedTop100() // graceful degradation
    }

// 잘못된 적용: 결제에 fail-safe 쓰면 안 됨
suspend fun charge(req: PayRequest): PayResult =
    runCatching { pg.charge(req) }
        .getOrElse { PayResult.Success(amount = 0) } // 🚨 silent corruption
```

**관련 패턴**: [Defensive Copying](#defensive-copying), [Exception](#exception-checked-unchecked), [Retry + Circuit](#retry-backoff-circuit)

---

<a id="compensating-transaction"></a>
## 7. Compensating Transaction (보상 트랜잭션)

**목적**: 분산 시스템에서 ACID 트랜잭션을 사용할 수 없을 때, **이미 commit 된 작업의 효과를 의미적으로 되돌리는** 역방향 작업을 실행하여 일관성을 복구합니다.

**특징**:
- ACID rollback 의 대체 — Saga 패턴의 핵심 메커니즘
- "취소" 가 아닌 **새로운 트랜잭션** — 원본 commit 은 그대로 보존, 부수효과는 별도 작업으로 무효화
- 모든 작업이 **보상 가능** 해야 함 (예: 이메일 발송은 보상 불가 → "취소 이메일" 발송으로 의미 보상)
- 보상이 보상하는 동안 발생한 변경은 어떻게? → 일반적으로 **semantic lock** (예: 주문 상태 PENDING) 으로 격리

**장점**:
- 분산 트랜잭션 (2PC) 의 코디네이터 / 락 비용 회피
- 마이크로서비스 자율성 보존
- 부분 실패에 대한 명시적 복구 정책

**단점**:
- 보상 로직이 정상 로직만큼 복잡 (2배 코드)
- 의미적 일관성만 보장 — 중간 상태가 외부에 노출될 수 있음
- 보상의 보상 (실패의 실패) 처리가 까다로움 — DLQ + 운영 개입 필요
- 모든 작업이 **idempotent** 해야 안전한 재시도 가능

**활용 예시**:
- 호텔+항공+렌터카 결합 예약 — 항공 실패 시 호텔 취소
- 분산 결제 — 카드 승인 후 inventory 부족 → 카드 환불
- Kafka Streams 의 exactly-once 와 결합

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
class TravelBookingSaga(
    private val flight: FlightService,
    private val hotel: HotelService,
    private val email: EmailService,
) {
    suspend fun book(req: BookingRequest): BookingResult {
        var flightRes: FlightBooking? = null
        var hotelRes: HotelBooking? = null
        return try {
            flightRes = flight.book(req)             // step 1
            hotelRes = hotel.book(req)               // step 2
            email.sendConfirmation(req.userEmail)    // step 3 (보상 불가 → 의미 보상으로 cancel mail)
            BookingResult.Ok(flightRes, hotelRes)
        } catch (t: Throwable) {
            // 역순 보상
            hotelRes?.let { runCatching { hotel.cancel(it.id) } }
            flightRes?.let { runCatching { flight.cancel(it.id) } }
            // step 3 의 의미 보상
            if (flightRes != null) email.sendCancelNotice(req.userEmail)
            BookingResult.Failed(t.message ?: "unknown")
        }
    }
}
```

**관련 패턴**: Saga ([distributed.md](distributed.md)), [Idempotency](distributed.md), [Retry + Circuit](#retry-backoff-circuit), [Panic / Recover](#panic-recover)

---

<a id="error-aggregation"></a>
## 8. Error Aggregation / Multi-Error

**목적**: 검증 / 처리에서 **모든 오류를 수집** 한 뒤 한 번에 반환합니다. 첫 오류에서 중단 (fail-fast) 하지 않아 사용자가 한 번의 라운드트립으로 모든 문제를 알 수 있게 합니다.

**특징**:
- `Validated[E, A]` (Scala Cats), `ValidatedNel[E, A]` — Either 와 시그니처는 같지만 합성 시 에러를 **누적**
- Applicative 합성 — `bind` 가 short-circuit 이라면 `ap` 는 병렬 누적
- Kotlin Arrow `EitherNel<E, A>` / `Validated<NonEmptyList<E>, A>`
- 폼 검증 / 배치 처리 / API 입력 검증 의 표준

**장점**:
- 사용자 경험 향상 — 여러 필드 오류를 한 번에 표시
- API 라운드트립 절감
- 검증 규칙이 독립적으로 표현됨 (합성)

**단점**:
- 단계 간 의존이 있으면 부적합 — A 검증 통과 후 B 검증인 경우 [Railway-Oriented](#railway-oriented) 가 맞음
- Applicative vs Monad 의 구분 이해 필요
- 누적 결과 자료구조 (NonEmptyList) 필요

**활용 예시**:
- 회원가입 폼 — 이메일·비번·이름 동시 검증
- API 입력 DTO 의 필드별 검증
- 배치 import — 각 라인 독립 검증 후 실패 라인 모음

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제** (Arrow EitherNel — applicative accumulation):
```kotlin
import arrow.core.EitherNel
import arrow.core.NonEmptyList
import arrow.core.left
import arrow.core.right
import arrow.core.raise.either
import arrow.core.raise.zipOrAccumulate

sealed class SignupError {
    data class EmailInvalid(val raw: String) : SignupError()
    data class PasswordTooWeak(val reason: String) : SignupError()
    data class NicknameTaken(val raw: String) : SignupError()
}

fun validateEmail(raw: String): EitherNel<SignupError, Email> =
    Email.parse(raw)?.right() ?: NonEmptyList.of(SignupError.EmailInvalid(raw)).left()

fun validatePassword(raw: String): EitherNel<SignupError, Password> =
    Password.parse(raw)?.right()
        ?: NonEmptyList.of(SignupError.PasswordTooWeak("min 8 chars + digit")).left()

fun validateNickname(raw: String): EitherNel<SignupError, Nickname> =
    if (nicknameRepo.exists(raw)) NonEmptyList.of(SignupError.NicknameTaken(raw)).left()
    else Nickname(raw).right()

// 세 검증을 모두 실행하여 실패를 누적 — Either flatMap 와 달리 short-circuit 하지 않음
fun signup(rawEmail: String, rawPwd: String, rawNick: String): EitherNel<SignupError, Signup> =
    either {
        zipOrAccumulate(
            { validateEmail(rawEmail).bind() },
            { validatePassword(rawPwd).bind() },
            { validateNickname(rawNick).bind() },
        ) { email, pwd, nick -> Signup(email, pwd, nick) }
    }
// 입력이 모두 잘못이면 결과 = Left(NEL(EmailInvalid, PasswordTooWeak, NicknameTaken))
```

**관련 패턴**: [Result / Either](#result-either-monad), [Railway-Oriented](#railway-oriented), [Fail-Fast](#fail-fast-safe)

---

<a id="panic-recover"></a>
## 9. Panic / Recover

**목적**: **복구 불가능한 프로그램 상태** 를 표현하고 정상 흐름과 명확히 분리합니다. 일반 예외 처리에서 잡지 않도록 구분된 채널을 제공하여 "절대 일어나면 안 되는 일" 의 의미를 보존합니다.

**특징**:
- **Go**: `panic()` / `recover()` (deferred only) — runtime panic 은 goroutine 단위 종료
- **Rust**: `panic!()` — stack unwind 또는 abort. `catch_unwind` 로 격리 가능 (FFI 경계)
- **Java**: `Error` 계층 (`OutOfMemoryError`, `StackOverflowError`) — 일반 catch 대상이 아님
- Erlang "let it crash" 철학 — 프로세스 단위 격리 + supervisor 재시작
- "프로그래밍 버그" 와 "예상 가능한 실패" 의 분리

**장점**:
- 의도가 분명 — "여기서는 잡지 마라"
- 손상된 invariant 의 추가 전파 차단
- supervisor / orchestrator 가 격리 단위로 재시작 가능

**단점**:
- 남용하면 일반 예외와 구분이 사라짐
- FFI / 외부 콜백 경계에서 unwind 가 UB 유발 가능 (Rust `catch_unwind` 필수)
- Go 의 panic 은 라이브러리 경계에서는 일반적으로 error 로 변환해야 함

**활용 예시**:
- 배열 인덱스 out of bounds, integer overflow (debug mode)
- 도달 불가능 case (`unreachable!()` / `error("unreachable")`)
- 초기화 실패로 프로그램이 의미 있는 동작을 할 수 없을 때 (`require` / `check` violation)
- Erlang / Akka actor 의 supervisor 패턴

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// 도달 불가능 case — sealed when 의 누락 방어 + 의도 명시
sealed class PaymentMethod {
    object Card : PaymentMethod()
    object Bank : PaymentMethod()
    object Cash : PaymentMethod()
}

fun fee(m: PaymentMethod): Int = when (m) {
    PaymentMethod.Card -> 30
    PaymentMethod.Bank -> 10
    PaymentMethod.Cash -> 0
    // when 이 exhaustive 가 아닐 때만 필요. sealed 면 컴파일러가 강제하므로 보통 생략
}

// invariant violation — 복구 시도 금지
class StateMachine {
    private var state = "INIT"
    fun transition(to: String) {
        val ok = state == "INIT" && to == "RUNNING"
        check(ok) { "illegal transition: $state -> $to (programming bug)" }
        state = to
    }
}

// FFI / 외부 콜백 경계 — panic 격리
suspend fun runUserScript(script: String): Either<String, JsonElement> =
    runCatching {
        sandbox.eval(script)
    }.fold(
        onSuccess = { it.right() },
        onFailure = { t ->
            // OutOfMemoryError 같은 Error 는 다시 throw — 잡으면 안 됨
            if (t is Error && t !is AssertionError) throw t
            (t.message ?: "script failed").left()
        }
    )
```

**관련 패턴**: [Fail-Fast](#fail-fast-safe), [Exception](#exception-checked-unchecked), [Defensive Copying](#defensive-copying)

---

<a id="defensive-copying"></a>
## 10. Defensive Copying / Boundary Validation

**목적**: **외부 입력의 경계에서만** 검증·복사하고, 검증된 값은 내부에서 신뢰합니다. 검증 책임을 한 곳에 모아 중복 검사를 제거하고 invariant 를 컴파일러가 보장하게 합니다.

**특징**:
- "Parse, don't validate" (Alexis King) — 검증 결과를 **타입으로 인코딩**
- Effective Java Item 50: 가변 객체 생성자 / getter 에서 방어적 복사
- DDD 의 Value Object — 생성자에서 검증, 이후 불변
- "Make illegal states unrepresentable" — 잘못된 상태를 타입으로 표현 불가능하게

**장점**:
- 검증 코드의 중복 제거 — 내부 코드가 깨끗
- invariant 보존이 컴파일러 책임으로 이전
- 보안 — 외부 변경으로부터 내부 상태 보호
- 도메인 의도가 타입에 노출

**단점**:
- 초기 설계 비용 (Value Object 클래스 다수)
- 방어적 복사는 메모리 / GC 비용
- "어디가 boundary 인가" 의 합의 필요

**활용 예시**:
- HTTP DTO → Domain Entity 변환 (DDD anti-corruption layer)
- 가변 컬렉션을 생성자에서 `List.copyOf` / `toList()`
- 파싱: `String → Email`, `String → Url`, `Int → Age`
- Date / Time API 의 immutable wrapper

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Bad: 검증을 호출자마다 반복, 가변 컬렉션 공유로 invariant 깨짐
class Order(
    val id: String,
    val items: MutableList<Item>, // 외부에서 변경 가능 — 위험
) {
    init {
        require(id.length == 36) // 호출자가 검증해도 또 검사
    }
}

// Good: Parse, don't validate + 방어적 복사
@JvmInline
value class OrderId(val raw: String) {
    init { require(raw.matches(uuidRegex)) { "invalid order id: $raw" } }
    companion object { private val uuidRegex = Regex("[0-9a-f-]{36}") }
}

@JvmInline
value class Email(val raw: String) {
    init { require(raw.contains("@")) { "invalid email: $raw" } }
}

class Order private constructor(
    val id: OrderId,
    val email: Email,
    items: List<Item>,
) {
    private val _items: List<Item> = items.toList() // 방어적 복사
    val items: List<Item> get() = _items            // 외부 노출도 불변

    companion object {
        fun create(rawId: String, rawEmail: String, items: List<Item>): Order =
            Order(OrderId(rawId), Email(rawEmail), items) // 경계에서 한 번만 검증
    }
}

// 내부 코드는 검증 없이 신뢰 — 컴파일러가 보장
fun sendInvoice(order: Order) {
    // order.email 은 이미 Email 타입 → 다시 검증할 필요 없음
    mailer.send(order.email.raw, generateInvoice(order))
}
```

**관련 패턴**: [Option / Maybe](#option-maybe), [Fail-Fast](#fail-fast-safe), [Result / Either](#result-either-monad)

---

<a id="retry-backoff-circuit"></a>
## 11. Retry with Exponential Backoff + Circuit Breaker

**목적**: 일시적 (transient) 실패를 지수 증가 대기 시간 + jitter 로 재시도하면서, 영속적 (persistent) 실패는 회로 차단으로 즉시 fail-fast 하여 두 종류의 오류를 **다르게 처리**합니다.

**특징**:
- 단순 Retry / Circuit Breaker 는 [reliability.md](reliability.md) 에서 다룸
- 본 항목은 **에러 처리 관점** — "어떤 에러를 어떤 정책으로?" 의 분류
- **재시도 가능 (retryable)**: timeout, 5xx, connection reset, lock contention
- **재시도 불가 (terminal)**: 4xx (인증 실패, 잘못된 입력), domain validation error
- **회로 차단 트리거**: 일정 시간 창에서 retryable 실패 비율이 임계 초과
- 멱등성 (idempotency) 보장이 전제 — 비멱등 호출은 [Idempotency Key](distributed.md) 와 조합

**장점**:
- 일시적 오류는 자동 흡수 → 사용자에게 노출 안 됨
- 영속적 오류는 즉시 fail-fast → 자원 낭비 차단
- 회로가 열린 동안 다운스트림은 회복 시간 확보 (thundering herd 방지에 jitter 필수)
- 에러 분류가 명시적 — 라이브러리 / 도메인 정책으로 분리

**단점**:
- 에러 분류가 잘못되면 (4xx 를 retry) 무한 시도 → DoS
- 비멱등 호출에 retry 적용 시 중복 실행
- 회로 임계치 / backoff 인자 튜닝 비용
- 호출 stack 의 여러 레이어에서 retry 중첩 시 retry storm

**활용 예시**:
- 외부 결제 게이트웨이 호출 (Stripe, Toss)
- 메시지 큐 consumer (Kafka, SQS)
- 분산 DB 락 획득
- AWS SDK 의 default retry policy + circuit

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
sealed class CallError {
    object Retryable : CallError()     // 5xx, timeout, network reset
    object Terminal : CallError()      // 4xx, validation, auth
    object CircuitOpen : CallError()   // 회로 차단 상태
}

class ResilientClient(
    private val maxRetries: Int = 3,
    private val initialDelayMs: Long = 100,
    private val factor: Double = 2.0,
    private val circuit: CircuitBreaker,
) {
    suspend fun <T> call(block: suspend () -> T): Either<CallError, T> {
        if (circuit.isOpen()) return CallError.CircuitOpen.left()

        var delay = initialDelayMs
        repeat(maxRetries) { attempt ->
            val result = runCatching { block() }
            result.onSuccess { value ->
                circuit.recordSuccess()
                return value.right()
            }
            val err = result.exceptionOrNull()!!
            when (classify(err)) {
                CallError.Terminal -> {
                    // 재시도하지 않음 — 도메인 / 인증 오류
                    return CallError.Terminal.left()
                }
                CallError.Retryable -> {
                    circuit.recordFailure()
                    if (circuit.isOpen()) return CallError.CircuitOpen.left()
                    if (attempt < maxRetries - 1) {
                        // jitter 추가 — thundering herd 방지
                        val jitter = (0..delay.toInt()).random()
                        kotlinx.coroutines.delay(delay + jitter)
                        delay = (delay * factor).toLong()
                    }
                }
                CallError.CircuitOpen -> return CallError.CircuitOpen.left()
            }
        }
        return CallError.Retryable.left()
    }

    private fun classify(t: Throwable): CallError = when {
        t is HttpException && t.code in 500..599 -> CallError.Retryable
        t is HttpException && t.code in 400..499 -> CallError.Terminal
        t is java.io.IOException -> CallError.Retryable
        t is IllegalArgumentException -> CallError.Terminal
        else -> CallError.Retryable
    }
}
```

**관련 패턴**: Retry / Circuit Breaker / Timeout ([reliability.md](reliability.md)), [Idempotency Key](distributed.md), [Compensating Transaction](#compensating-transaction), [Fail-Fast](#fail-fast-safe)
