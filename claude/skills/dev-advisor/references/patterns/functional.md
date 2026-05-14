# 함수형 프로그래밍 패턴 (Functional Programming Patterns)

Haskell / Scala / Kotlin Arrow / F# / OCaml 에서 정평 있는 11 함수형 패턴. OO 의 GoF 23 과 다른 *합성 가능한 추상*. **Type class + Higher-Kinded Type + Lambda calculus** 기반.

**원전 참고**:
- Bartosz Milewski — *Category Theory for Programmers* (2019)
- Paul Chiusano, Rúnar Bjarnason — *Functional Programming in Scala* (2014)
- Saunders Mac Lane — *Categories for the Working Mathematician* (1971) — Monad 의 수학 원전
- Eugenio Moggi — "Notions of Computation and Monads" (1991) — Monad 를 컴퓨테이션에 도입
- Edwin Brady — *Type-Driven Development with Idris* (2017)
- van Laarhoven, Twan — Lens 의 표현 (blog series)
- Plotkin & Pretnar — *Algebraic Effects* (2009)
- Wadler, Philip — "Monads for Functional Programming" (1995)
- Oleg Kiselyov — Tagless Final 의 표현 (2009~)

**핵심 가치**:
- **합성 (Composition)** — 함수의 합성으로 큰 프로그램 구축
- **불변성 (Immutability)** — 부수효과 격리
- **타입으로 표현 (Types as documentation)** — `Either<Error, A>` 같이 결과 가능성 자체를 타입으로
- **참조 투명성 (Referential Transparency)** — 같은 입력 → 같은 출력, 부수효과 없음
- **법칙 (Laws)** — 패턴이 만족해야 할 수학적 등식 (identity, associativity, composition)

**관련 카탈로그**:
- [`../principles/type-systems.md`](../principles/type-systems.md) — HKT / ADT / Linear / Effect (이론 기반)
- [behavioral.md](behavioral.md) — Iterator / Strategy / Command (OO 대응)
- [error-handling.md](error-handling.md) — Result/Either / Railway-Oriented (FP 에러 처리)
- [reactive-streams.md](reactive-streams.md) — Cold/Hot Stream / FRP

---

<a id="functor"></a>

## 1. Functor (펑터)

**정의**: "값을 담는 컨테이너" 위에서 *내부 값에 함수를 적용*하는 능력. `F<A>` 를 `F<B>` 로 *구조 보존* 하면서 변환한다. 가장 기본적인 합성 추상.

**타입 시그니처**:
```
trait Functor[F[_]] {
  def map[A, B](fa: F[A])(f: A => B): F[B]
}
```

**법칙 (Functor Laws)**:
1. **Identity** — `fa.map(x => x) == fa` — 항등 함수를 매핑해도 변화 없음
2. **Composition** — `fa.map(f).map(g) == fa.map(g compose f)` — 두 번 매핑은 합성과 같음

→ 이 두 법칙을 만족하지 않으면 **Functor 가 아니다**. 예: `set.map(f)` 에서 `f` 가 중복을 만들면 composition 법칙 깨짐 (엄밀히는 Set 은 Functor 가 아님).

**장점**:
- 컨테이너 종류와 무관하게 동일한 `map` 인터페이스
- 구조(`List` 의 순서, `Option` 의 유무, `Tree` 의 모양) 를 보존
- 합성 가능 — `f compose g` 가 `map(f) compose map(g)` 와 같음

**단점**:
- 독립적인 두 effect 합성 불가 (→ Applicative 필요)
- Sequential dependency 표현 불가 (→ Monad 필요)

**활용 예시**:
- `Option/Maybe` — null-safety
- `Either<E, A>` — 에러 가능성을 타입으로
- `List/Seq` — 컬렉션 변환
- `Future/Promise` — async 값
- `IO` — 부수효과 격리
- Kotlin `arrow.core.Option.map`, Scala cats `Functor`, Haskell `fmap`

**Kotlin (Arrow) 예제**:
```kotlin
import arrow.core.Option
import arrow.core.some
import arrow.core.none

// Option 은 Functor — map 으로 내부 값만 변환
val name: Option<String> = "Alice".some()
val upper: Option<String> = name.map { it.uppercase() } // Some("ALICE")

val empty: Option<String> = none()
val emptyUpper: Option<String> = empty.map { it.uppercase() } // None — 구조 보존

// 법칙 검증
// identity: name.map { it } == name  ✓
// composition: name.map(f).map(g) == name.map { g(f(it)) }  ✓
```

**Haskell 예제**:
```haskell
-- Functor type class
class Functor f where
  fmap :: (a -> b) -> f a -> f b

-- Maybe 의 Functor 인스턴스
instance Functor Maybe where
  fmap _ Nothing  = Nothing
  fmap f (Just x) = Just (f x)

-- 사용
fmap (+1) (Just 5)    -- Just 6
fmap (+1) Nothing     -- Nothing
fmap show [1, 2, 3]   -- ["1", "2", "3"]

-- <$> 는 fmap 의 중위 연산자
(+1) <$> Just 5       -- Just 6
```

**관련 패턴**: [Applicative](#applicative-functor), [Monad](#monad), [Lens](#lens-optics), Iterator (OO)

---

<a id="applicative-functor"></a>

## 2. Applicative Functor (애플리커티브 펑터)

**정의**: Functor 의 확장. *독립적인* effect 들을 합성. 두 개 이상의 `F<A>`, `F<B>` 를 받아 `F<C>` 를 만든다. Functor 와 Monad 사이의 추상.

**타입 시그니처**:
```
trait Applicative[F[_]] extends Functor[F] {
  def pure[A](a: A): F[A]                       // lift — 일반 값을 F 로
  def ap[A, B](ff: F[A => B])(fa: F[A]): F[B]   // apply — F 안의 함수를 F 안의 값에
}
```

**법칙 (Applicative Laws)**:
1. **Identity** — `pure(id) <*> v == v`
2. **Composition** — `pure(compose) <*> u <*> v <*> w == u <*> (v <*> w)`
3. **Homomorphism** — `pure(f) <*> pure(x) == pure(f(x))`
4. **Interchange** — `u <*> pure(y) == pure($ y) <*> u`

**장점**:
- 독립 effect 의 병렬 합성 (Monad 와 달리 순서 의존성 없음)
- Validation 누적 (여러 에러를 한 번에 모음)
- Parallel applicative — Future/IO 의 병렬 실행 가능

**단점**:
- Sequential dependency 표현 불가 — `flatMap` 이 없음
- `ap` 가 직관적이지 않음 (보통 `mapN` / `zipWith` 로 감싼다)

**활용 예시**:
- Validation 누적 (Cats `Validated`, Arrow `Validated`, Haskell `Validation`)
- Parser combinator (Haskell `parsec` 의 `<*>`)
- Form validation — 모든 필드 에러를 한 번에
- Parallel async — `(future1, future2).mapN { a, b -> ... }`

**Kotlin (Arrow) 예제**:
```kotlin
import arrow.core.Validated
import arrow.core.ValidatedNel
import arrow.core.invalidNel
import arrow.core.validNel
import arrow.core.zip

data class User(val name: String, val age: Int, val email: String)

fun validateName(s: String): ValidatedNel<String, String> =
    if (s.isNotBlank()) s.validNel() else "name is blank".invalidNel()

fun validateAge(a: Int): ValidatedNel<String, Int> =
    if (a in 0..150) a.validNel() else "age out of range".invalidNel()

fun validateEmail(e: String): ValidatedNel<String, String> =
    if (e.contains("@")) e.validNel() else "invalid email".invalidNel()

// Applicative — 세 validation 을 독립적으로 실행, 에러를 모두 누적
val user: ValidatedNel<String, User> =
    validateName("").zip(validateAge(200), validateEmail("bad")) { n, a, e ->
        User(n, a, e)
    }
// Invalid(NonEmptyList("name is blank", "age out of range", "invalid email"))
// Monad 였다면 첫 에러("name is blank") 에서 멈췄을 것
```

**Haskell 예제**:
```haskell
-- (<*>) :: Applicative f => f (a -> b) -> f a -> f b
data User = User { name :: String, age :: Int }

mkUser :: Maybe User
mkUser = User <$> Just "Alice" <*> Just 30
-- User <$> Just "Alice"  →  Just (User "Alice")  (부분 적용)
-- ... <*> Just 30         →  Just (User "Alice" 30)
```

**관련 패턴**: [Functor](#functor), [Monad](#monad), [Pattern Matching](#pattern-matching-adt)

---

<a id="monad"></a>

## 3. Monad (모나드)

**정의**: Applicative 의 확장. *순차적으로 의존하는* effect 합성. 이전 단계의 결과(`A`)에 *의존*하는 다음 effect (`F<B>`) 를 만든다. `bind` / `flatMap` 이 핵심.

**타입 시그니처**:
```
trait Monad[F[_]] extends Applicative[F] {
  def flatMap[A, B](fa: F[A])(f: A => F[B]): F[B]
  // = bind, >>= in Haskell
}
```

**법칙 (Monad Laws)**:
1. **Left Identity** — `pure(a).flatMap(f) == f(a)`
2. **Right Identity** — `m.flatMap(pure) == m`
3. **Associativity** — `m.flatMap(f).flatMap(g) == m.flatMap(x => f(x).flatMap(g))`

→ 결합 법칙이 핵심. `do`-notation / `for`-comprehension 이 가능한 이유.

**대표 Monad**:
| Monad | 표현하는 effect |
|---|---|
| `Maybe / Option` | 실패 가능성 (null) |
| `Either / Result` | 에러 처리 |
| `List` | 비결정성 (여러 결과) |
| `IO` | 부수효과 격리 |
| `State` | 가변 상태 |
| `Reader` | 의존성 주입 (환경) |
| `Writer` | 로그 누적 |
| `Future / Task` | 비동기 |
| `Cont` | 연속 |

**장점**:
- 순차 의존성을 함수 합성으로 표현 (`do`-notation)
- 부수효과를 타입으로 명시 (`IO[A]` ≠ `A`)
- Stack-safe 한 effect 합성 (trampolined monad)

**단점**:
- Monad 들이 합성이 안 됨 (→ Monad Transformer 또는 Tagless Final 필요)
- Sequential 강제 — 병렬 가능한데 `flatMap` 쓰면 직렬화
- "What color is your function" — Monad 안 의 코드와 밖 의 코드 분리

**활용 예시**:
- Kotlin Arrow `Either.flatMap` — 첫 에러에서 short-circuit (Railway-Oriented)
- Scala cats `IO` — 부수효과 격리, async, error handling
- Haskell `IO Monad` — Pure 언어에서 부수효과 표현
- F# `Result Computation Expression`
- Rust `?` operator — `Result` Monad 의 sugar

**Kotlin (Arrow) 예제 — for-comprehension 스타일**:
```kotlin
import arrow.core.Either
import arrow.core.raise.either

fun parseInt(s: String): Either<String, Int> =
    s.toIntOrNull()?.let { Either.Right(it) } ?: Either.Left("not int: $s")

fun divide(a: Int, b: Int): Either<String, Int> =
    if (b == 0) Either.Left("div by zero") else Either.Right(a / b)

// Monad — flatMap chain (sequential dependency)
val result1: Either<String, Int> =
    parseInt("100").flatMap { a ->
        parseInt("5").flatMap { b ->
            divide(a, b)                  // 20
        }
    }

// 동일 — Arrow 의 either { } DSL (= do-notation)
val result2: Either<String, Int> = either {
    val a = parseInt("100").bind()        // 100
    val b = parseInt("5").bind()          // 5
    divide(a, b).bind()                   // 20
}
// 어느 단계든 Left 면 즉시 short-circuit
```

**Haskell 예제 — do-notation**:
```haskell
-- Maybe Monad
safeDivide :: Int -> Int -> Maybe Int
safeDivide _ 0 = Nothing
safeDivide a b = Just (a `div` b)

compute :: Maybe Int
compute = do
  a <- safeDivide 100 5      -- Just 20
  b <- safeDivide a 4         -- Just 5
  safeDivide b 0              -- Nothing — 여기서 끝
-- 결과: Nothing

-- IO Monad
main :: IO ()
main = do
  putStrLn "Name?"
  name <- getLine
  putStrLn ("Hello, " ++ name)
```

**Scala 예제 — for-comprehension**:
```scala
import cats.effect.IO

val program: IO[Unit] = for {
  _    <- IO.println("Name?")
  name <- IO.readLine
  _    <- IO.println(s"Hello, $name")
} yield ()
// for-comprehension 은 flatMap chain 의 syntax sugar
```

**관련 패턴**: [Free Monad](#free-monad), [Tagless Final](#tagless-final), [CPS](#cps), [Applicative](#applicative-functor), Strategy (OO 대응)

---

<a id="free-monad"></a>

## 4. Free Monad (자유 모나드)

**정의**: *명령어를 데이터 구조로* 표현하고, 나중에 *인터프리터로* 실행. AST 를 직접 다루는 Monad. eDSL (embedded DSL) 구축의 정석.

**핵심 아이디어**: Monad 의 instance 를 *공짜로* 얻는다 — Functor 만 있으면. 명령어 ADT 를 만들고 `Free` 로 감싸면 자동으로 Monad.

**타입 시그니처**:
```haskell
data Free f a
  = Pure a
  | Free (f (Free f a))

instance Functor f => Monad (Free f) where
  return = Pure
  (Pure a)   >>= k = k a
  (Free fa) >>= k = Free (fmap (>>= k) fa)
```

**구조**:
```
1. Algebra 정의      — sealed class Cmd<A>
2. 명령어를 Free 로  — Free<Cmd, A>
3. 프로그램 작성     — for { x <- get(); _ <- put(x+1) } yield x
4. 인터프리터 구현    — Cmd ~> IO (또는 State, Test)
5. 실행              — program.foldMap(interpreter)
```

**장점**:
- 프로그램(데이터)와 실행(인터프리터) 분리
- 동일 프로그램을 여러 인터프리터로 (Production = IO, Test = State, Log = Writer)
- 명령어 단위 최적화 가능 (program 을 분석/재작성)
- 테스트 용이 — pure interpreter 만으로

**단점**:
- 보일러플레이트 ↑ (명령어 ADT + smart constructor + interpreter)
- 성능 — Free 의 tree traversal 비용
- → 실무에서는 **Tagless Final** 이 더 자주 쓰임 (성능·보일러플레이트 모두 우위)

**활용 예시**:
- Scalaz / Cats `Free`
- Doobie (DB SQL eDSL)
- Cats Effect 초기 버전
- Haskell `free` 패키지
- 인터프리터 패턴 (OO 대응)

**Scala (Cats) 예제**:
```scala
import cats.free.Free
import cats.{Id, ~>}

// 1. Algebra — 명령어 ADT
sealed trait KVStore[A]
case class Put(key: String, value: String) extends KVStore[Unit]
case class Get(key: String)                extends KVStore[Option[String]]
case class Delete(key: String)             extends KVStore[Unit]

// 2. Smart constructor — Free 로 감싸기
type KVS[A] = Free[KVStore, A]
def put(k: String, v: String): KVS[Unit]      = Free.liftF(Put(k, v))
def get(k: String): KVS[Option[String]]        = Free.liftF(Get(k))
def delete(k: String): KVS[Unit]               = Free.liftF(Delete(k))

// 3. 프로그램 — 데이터로서의 프로그램
val program: KVS[Option[String]] = for {
  _    <- put("alice", "30")
  age  <- get("alice")
  _    <- delete("alice")
} yield age

// 4. Interpreter — production
val prodInterp: KVStore ~> Id = new (KVStore ~> Id) {
  val store = scala.collection.mutable.Map.empty[String, String]
  def apply[A](fa: KVStore[A]): Id[A] = fa match {
    case Put(k, v)   => store(k) = v
    case Get(k)      => store.get(k)
    case Delete(k)   => store.remove(k); ()
  }
}

// 4'. Interpreter — test (로그만 누적)
val testInterp: KVStore ~> Id = new (KVStore ~> Id) {
  def apply[A](fa: KVStore[A]): Id[A] = fa match {
    case Put(k, v) => println(s"PUT $k=$v")
    case Get(k)    => println(s"GET $k"); Some("30")
    case Delete(k) => println(s"DELETE $k"); ()
  }
}

// 5. 실행 — 같은 program 을 다른 interpreter 로
program.foldMap(prodInterp)  // 실제 저장소
program.foldMap(testInterp)  // 로그 출력
```

**관련 패턴**: [Monad](#monad), [Tagless Final](#tagless-final), Interpreter (OO), Command (OO)

---

<a id="lens-optics"></a>

## 5. Lens / Optics (렌즈 / 옵틱스)

**정의**: 불변(immutable) 자료구조의 *깊은 필드 접근/갱신*을 합성 가능하게 표현. `get` 과 `set` 을 한 쌍으로 묶은 추상.

**해결하려는 문제**: 중첩된 record 의 한 필드만 바꾸려면 모든 부모를 copy 해야 한다 (deep copy hell).

**Before — deep copy 지옥**:
```kotlin
data class Address(val city: String, val zip: String)
data class Company(val name: String, val address: Address)
data class Employee(val name: String, val company: Company)

val e: Employee = ...
val updated = e.copy(
    company = e.company.copy(
        address = e.company.address.copy(
            city = "Seoul"          // ← 한 필드만 바꾸려고 3중 copy
        )
    )
)
```

**After — Lens 합성**:
```kotlin
import arrow.optics.optics

@optics data class Address(val city: String, val zip: String)  { companion object }
@optics data class Company(val name: String, val address: Address) { companion object }
@optics data class Employee(val name: String, val company: Company) { companion object }

val cityLens = Employee.company.address.city   // Lens 합성
val updated = cityLens.set(e, "Seoul")          // 한 줄
val city    = cityLens.get(e)                   // get 도 가능
```

**타입 시그니처 (van Laarhoven)**:
```haskell
-- 표면형
data Lens s a = Lens { get :: s -> a, set :: a -> s -> s }

-- van Laarhoven (Functor 기반, 합성·확장 우수)
type Lens s a = forall f. Functor f => (a -> f a) -> s -> f s
```

**Optics 종류**:
| 종류 | 용도 | 예시 |
|---|---|---|
| **Lens** | 항상 존재하는 필드 | `Employee.name` |
| **Prism** | Sum type 의 한 case | `Either.Right` |
| **Optional** | 있을 수도 없을 수도 | `Map[K, V] at key` |
| **Traversal** | 0개 이상 | `List<A>` 의 모든 원소 |
| **Iso** | 양방향 변환 | `String <-> List<Char>` |

**Lens 법칙**:
1. **Get-Set** — `set(get(s), s) == s` — 같은 값 set 은 변화 없음
2. **Set-Get** — `get(set(a, s)) == a` — set 한 값을 get 하면 그대로
3. **Set-Set** — `set(b, set(a, s)) == set(b, s)` — 마지막 set 만 유효

**장점**:
- 합성 — `outer.inner.field` 처럼 점 표기
- 재사용 — 한 번 정의한 Lens 를 여러 곳에서
- 자동 생성 — Arrow `@optics`, Haskell `makeLenses` TH

**단점**:
- 학습 곡선 (Prism / Traversal / Iso 까지 가면 깊음)
- 컴파일 시간 (Arrow `@optics` 의 KSP 생성)
- 디버깅 — 합성된 Lens 의 stack trace 가 길다

**활용 예시**:
- Kotlin Arrow Optics
- Haskell `lens` 패키지 (Edward Kmett)
- Scala Monocle
- TypeScript `monocle-ts`
- Redux Reselect (간이 Lens)
- Persistent 상태 관리

**관련 패턴**: [Functor](#functor), [Persistent Data Structures](#persistent-data-structures), Memento (OO)

---

<a id="tagless-final"></a>

## 6. Tagless Final (태그리스 파이널)

**정의**: Effect 를 *type class* 로 추상화. Free Monad 의 alternative — 보일러플레이트 적고 성능 좋음. *프로그램은 타입 매개변수 F[_] 로 추상화*, 인터프리터는 *type class instance*.

**핵심 차이 — Free vs Tagless Final**:
| | Free Monad | Tagless Final |
|---|---|---|
| 표현 | 명령어를 데이터 | 명령어를 함수 |
| 추가 명령어 | ADT 확장 | type class 추가 |
| 성능 | tree allocation | direct call |
| 보일러플레이트 | 많음 (smart ctor) | 적음 |
| 디버깅 | trace 어려움 | stack trace 자연스러움 |

**구조 (MTL 스타일)**:
```scala
// 1. Algebra — type class
trait KVStore[F[_]] {
  def put(k: String, v: String): F[Unit]
  def get(k: String): F[Option[String]]
  def delete(k: String): F[Unit]
}

// 2. 프로그램 — F[_] 추상화
def program[F[_]: Monad: KVStore]: F[Option[String]] = for {
  _   <- KVStore[F].put("alice", "30")
  age <- KVStore[F].get("alice")
  _   <- KVStore[F].delete("alice")
} yield age

// 3. Instance — production
implicit val ioInstance: KVStore[IO] = new KVStore[IO] {
  def put(k: String, v: String) = IO { /* DB call */ }
  def get(k: String)            = IO { /* SELECT */ }
  def delete(k: String)         = IO { /* DELETE */ }
}

// 4. Instance — test
implicit val testInstance: KVStore[State[Map[String, String], *]] = ...

// 5. 실행
program[IO].unsafeRunSync()                    // production
program[State[...]].run(Map.empty).value       // test
```

**장점**:
- 성능 — direct call, allocation 없음
- 보일러플레이트 ↓
- type class 합성 자연스러움 (`F[_]: Monad: KVStore: Logger`)
- F 를 다양하게 — `IO`, `Task`, `Resource[IO, *]`, `Kleisli` 등

**단점**:
- type class 추상이 깊어지면 컴파일 오류 메시지 난해
- `F[_]` 의 의미 명세가 약함 (Free Monad 는 algebra 가 명시적)
- "MTL hell" — `F[_]: Monad: MonadError[E, *]: Sync: Async: ...` 누적 시 어려움

**활용 예시**:
- Cats Effect 의 `Sync`, `Async`, `Resource` type class
- ZIO 의 service pattern (`Has[Service]`)
- Haskell `mtl` (Monad Transformer Library)
- Scala Doobie / http4s — `F[_]: Sync` 스타일

**Kotlin Arrow 유사 패턴**:
```kotlin
interface KVStore<F> {
    fun put(k: String, v: String): Kind<F, Unit>
    fun get(k: String): Kind<F, Option<String>>
}

// IO instance
val ioKVStore: KVStore<ForIO> = object : KVStore<ForIO> {
    override fun put(k: String, v: String): IO<Unit> = IO { /* ... */ }
    override fun get(k: String): IO<Option<String>>  = IO { /* ... */ }
}
```

**관련 패턴**: [Free Monad](#free-monad), [Monad](#monad), Strategy (OO), Dependency Injection

---

<a id="effect-handlers"></a>

## 7. Effect Handlers / Algebraic Effects (대수적 효과)

**정의**: 부수효과를 *first-class 시민*으로 다루는 새 패러다임. 효과 *발생*과 효과 *처리*를 분리. `resume` (continuation) 으로 효과 사용처에 값을 반환. async/await, generator, exception 의 *이론적 기반*.

**역사**:
- Plotkin & Pretnar (2009) — 이론 정립
- **Eff** 언어 (2012) — 첫 구현
- **Koka** (Microsoft Research, 2014~) — 산업급 구현
- **OCaml 5.0** (2022) — Multicore + Algebraic Effects
- **Unison**, **Idris 2**, **Frank** — 다양한 구현

**구조**:
```
1. Effect 선언  — effect Log { log: String -> Unit }
2. Effect 발생  — log("hello")          ← 효과 trigger
3. Handler 정의 — handle { log(msg) => ... resume(()) }
4. 실행         — handler에서 효과를 처리
```

**핵심 능력 — `resume`**:
효과 발생 지점으로 *값을 들고 돌아간다*. exception 은 *던지고 끝* 이지만 effect 는 *resume 가능*.

```
async/await    — 한 번 resume        (one-shot)
generator      — 여러 번 resume      (multi-shot)
backtrack      — 여러 번 resume      (Prolog 스타일)
exception      — resume 없음
```

**장점**:
- "What color is your function" 문제 해결 — async/sync 일관 처리
- effect 합성 자유 (Monad 와 달리 transformer 불필요)
- Handler 교체로 테스트 (실제 IO vs Mock)
- Multi-shot continuation — 비결정 / 백트래킹

**단점**:
- 언어 지원 필요 (Koka, OCaml 5, Unison)
- Stack 표현 변경 — 런타임 복잡도 ↑
- 정적 분석 어려움 (어떤 effect 가 어디서 처리되는가)

**활용 예시**:
- OCaml 5 의 동시성 (eio, riot)
- Koka 의 모든 effect 시스템
- React Suspense — algebraic effect 의 JS 흉내
- Unison — distributed computation

**Koka 예제**:
```koka
// 1. Effect 선언
effect log {
  fun log(msg: string): ()
}

effect ask<a> {
  fun ask(): a
}

// 2. Effect 사용 — 함수 시그니처에 effect 명시
fun greet(): <log, ask<string>> () {
  val name = ask()
  log("Hello, " ++ name)
}

// 3. Handler 정의 — production
fun run-prod(action: () -> <log, ask<string>> a): a {
  with handler {
    fun log(msg) { println(msg); resume(()) }
    fun ask()    { resume("Alice") }
  }
  action()
}

// 4. Handler — test
fun run-test(action: () -> <log, ask<string>> a): (a, list<string>) {
  var logs := []
  with handler {
    fun log(msg) { logs := Cons(msg, logs); resume(()) }
    fun ask()    { resume("TestUser") }
  }
  (action(), logs)
}
```

**OCaml 5 예제**:
```ocaml
(* Effect 선언 *)
type _ Effect.t += Log : string -> unit Effect.t

(* Effect 사용 *)
let greet () =
  let name = "Alice" in
  Effect.perform (Log ("Hello, " ^ name))

(* Handler *)
let () =
  try greet () with
  | effect (Log msg) k ->
    print_endline msg;
    Effect.Deep.continue k ()    (* resume *)
```

**관련 패턴**: [Monad](#monad), [CPS](#cps), [Free Monad](#free-monad), Strategy (OO)

---

<a id="cps"></a>

## 8. Continuation-Passing Style (CPS, 연속 전달 방식)

**정의**: 함수가 *결과를 return* 하는 대신, *다음 할 일(continuation)* 을 인자로 받아 *호출*. `A` 대신 `(A → R) → R` 을 반환. async/await, generator 의 컴파일 결과.

**변환 공식**:
```
일반:   f: A → B
CPS:    f: A → (B → R) → R

일반:   val y = f(x); g(y)
CPS:    f(x, y => g(y, k))    // k 는 최종 continuation
```

**예시 변환**:
```scala
// Direct style
def add(a: Int, b: Int): Int = a + b
def main(): Unit = {
  val x = add(1, 2)
  val y = add(x, 3)
  println(y)
}

// CPS
def addCps(a: Int, b: Int, k: Int => Unit): Unit = k(a + b)
def mainCps(): Unit = {
  addCps(1, 2, x =>
    addCps(x, 3, y =>
      println(y)
    )
  )
}
```

**왜 쓰는가**:
- **비동기** — `k` 를 즉시 호출 안 하고 콜백으로 → async/await 의 desugar
- **Coroutine** — Kotlin coroutine 은 CPS 변환 + state machine
- **Generator** — `yield` 는 continuation 을 외부에 노출
- **Tail call** — 모든 호출이 tail position → stack 안 쌓임 (trampolined CPS)
- **Backtrack** — continuation 을 저장했다가 다시 호출 → Prolog
- **call/cc** — Scheme 의 first-class continuation

**장점**:
- 비동기·동시성·예외·백트래킹을 *균일* 하게 표현
- 컴파일러 IR 로 매우 적합 (SML/NJ, Scheme)
- Tail call 자동 (CPS 변환 시)

**단점**:
- *읽기* 어려움 — callback hell
- 사람이 직접 작성하지는 않음 (컴파일러가 생성)
- Stack trace 가 평탄해져서 디버깅 어려움

**활용 예시**:
- Kotlin Coroutine 컴파일러 (`suspend fun` → CPS + state machine)
- JS async/await desugar
- Scheme `call/cc`
- Node.js callback (수동 CPS)
- Trampolining 의 기반

**Kotlin coroutine 의 CPS 변환** (개념):
```kotlin
// 작성한 코드 (suspend)
suspend fun fetchUser(id: Int): User {
    val u = api.get(id)          // suspend point
    val p = api.permissions(u)   // suspend point
    return User(u, p)
}

// 컴파일러가 변환 (개념적)
fun fetchUser(id: Int, k: Continuation<User>) {
    api.get(id) { u ->                              // continuation 1
        api.permissions(u) { p ->                   // continuation 2
            k.resume(User(u, p))                    // 최종 resume
        }
    }
}
// 실제로는 state machine 으로 평탄화
```

**관련 패턴**: [Effect Handlers](#effect-handlers), [Trampolining](#trampolining), [Monad](#monad) (Cont monad), Observer (OO)

---

<a id="trampolining"></a>

## 9. Trampolining (트램폴린)

**정의**: Recursive call 을 *명시적 데이터 구조* 로 변환하여 *stack overflow 회피*. Tail call optimization 이 없는 언어(JVM, JS) 에서 깊은 재귀를 안전하게.

**문제**: JVM 은 Tail Call Optimization (TCO) 가 없다. 다음 재귀는 stack overflow:
```scala
def even(n: Long): Boolean = if (n == 0) true else odd(n - 1)
def odd(n: Long): Boolean  = if (n == 0) false else even(n - 1)
even(1_000_000)   // StackOverflowError
```

**해결 — Trampoline**:
재귀를 *return* 으로 바꾸고 *외부 루프*가 결과를 따라간다.

**구조**:
```scala
sealed trait Trampoline[A] {
  def run: A = {
    var t: Trampoline[A] = this
    while (true) t match {
      case Done(a)        => return a
      case More(thunk)    => t = thunk()
      case FlatMap(sub, k) => sub match {
        case Done(a)        => t = k(a)
        case More(thunk)    => t = FlatMap(thunk(), k)
        case FlatMap(s2, k2) => t = FlatMap(s2, (x: Any) => FlatMap(k2(x), k))
      }
    }
    throw new AssertionError()
  }
}
case class Done[A](a: A)                                        extends Trampoline[A]
case class More[A](thunk: () => Trampoline[A])                   extends Trampoline[A]
case class FlatMap[A, B](sub: Trampoline[A], k: A => Trampoline[B]) extends Trampoline[B]
```

**사용**:
```scala
def even(n: Long): Trampoline[Boolean] =
  if (n == 0) Done(true)  else More(() => odd(n - 1))

def odd(n: Long): Trampoline[Boolean] =
  if (n == 0) Done(false) else More(() => even(n - 1))

even(1_000_000).run   // true — stack-safe
```

**장점**:
- TCO 없는 언어에서 안전한 재귀
- Monadic 구조와 합성 가능 (FlatMap 케이스)
- Cats `Eval`, Scalaz `Trampoline`, Kotlin Arrow `Eval`

**단점**:
- 성능 — heap allocation 비용 (stack 보다 비쌈)
- 코드 작성 ↑ — 일반 재귀보다 verbose
- Tail call 이 *상호 재귀* 일 때만 의미 있음 — 단순 재귀는 `@tailrec` 으로 해결

**활용 예시**:
- Cats `Eval` (Now / Later / Always / Defer)
- Kotlin Arrow `Eval`
- Free Monad 의 stack-safe 실행
- State Monad 의 누적 (`runState` 가 깊을 때)
- Parser combinator 의 깊은 grammar

**Kotlin Arrow Eval 예제**:
```kotlin
import arrow.core.Eval

fun even(n: Long): Eval<Boolean> =
    if (n == 0L) Eval.now(true) else Eval.defer { odd(n - 1) }

fun odd(n: Long): Eval<Boolean> =
    if (n == 0L) Eval.now(false) else Eval.defer { even(n - 1) }

even(1_000_000L).value()  // true — stack-safe
```

**관련 패턴**: [CPS](#cps), [Monad](#monad), [Free Monad](#free-monad)

---

<a id="pattern-matching-adt"></a>

## 10. Pattern Matching (ADT + Exhaustive)

**정의**: *Algebraic Data Type (ADT)* 를 *case 분기* 로 분해. 컴파일러가 *exhaustiveness* 를 검사 (모든 case 처리 여부). FP 의 핵심 control flow.

**ADT 의 두 축**:
- **Product type** — 모든 필드가 *동시에* 존재 (`tuple`, `record`, `data class`)
- **Sum type** — 여러 *대안 중 하나* (`sealed class`, `enum`, `Either`)

**Sum + Product 의 조합으로 도메인 표현**:
```kotlin
// 결제 상태를 ADT 로
sealed class Payment {
    object Pending : Payment()
    data class Authorized(val txId: String, val amount: Money) : Payment()
    data class Failed(val reason: String, val code: Int) : Payment()
    data class Refunded(val original: Authorized, val refundId: String) : Payment()
}

// 패턴 매칭 — Kotlin when (sealed → exhaustive)
fun describe(p: Payment): String = when (p) {
    is Payment.Pending     -> "결제 대기 중"
    is Payment.Authorized  -> "${p.amount} 결제 완료 (${p.txId})"
    is Payment.Failed      -> "실패: ${p.reason}"
    is Payment.Refunded    -> "환불됨 (원거래: ${p.original.txId})"
}
// 새 case 추가 시 컴파일러가 모든 when 검사 — 처리 누락 검출
```

**핵심 가치 — Exhaustiveness**:
*컴파일 타임에* 모든 case 처리 여부 검사. case 가 추가되면 컴파일 에러로 *처리 빠진 곳을 모두 찾아준다* — 도메인 안전성의 결정타.

**고급 — nested / guard / destructure**:
```scala
def describe(p: Payment): String = p match {
  case Pending                              => "대기"
  case Authorized(txId, Money(amt, "KRW")) if amt > 1_000_000
                                            => s"고액 결제 $amt 원 ($txId)"
  case Authorized(txId, Money(amt, cur))    => s"$cur $amt 결제 ($txId)"
  case Failed(reason, code) if code >= 500  => s"서버 오류: $reason"
  case Failed(reason, _)                    => s"클라이언트 오류: $reason"
  case Refunded(Authorized(orig, _), rid)    => s"환불 ($orig → $rid)"
}
```

**장점**:
- *컴파일러* 가 case 누락 검출 — 런타임 버그 → 컴파일 에러
- 자료구조의 *모양* 으로 분기 (instance check + getter 의 조합 불필요)
- Refactoring 안전 — case 추가/제거 시 모든 사용처가 컴파일 에러
- 도메인 모델링과 자연스럽게 결합

**단점**:
- 데이터 vs 동작 — Visitor 와 정반대 trade-off. 새 *case* 추가는 쉽지만, 새 *연산* 은 모든 패턴 매칭을 수정해야
- 깊은 nested pattern 은 가독성 ↓
- 일부 언어(Java < 21) 는 sealed/pattern 미지원

**활용 예시**:
- Rust `match` — exhaustive, guard, nested 완벽 지원
- Scala 3 `match` — Kotlin/Java 와 비교 시 가장 풍부
- Kotlin `when (sealed)` — exhaustive 강제 (Kotlin 1.7+)
- Haskell / OCaml — FP 의 기본
- Java 21 `switch` pattern — record + sealed
- Domain Modeling — DDD 의 Aggregate State 표현

**Haskell 예제**:
```haskell
data Tree a = Leaf | Node (Tree a) a (Tree a)

depth :: Tree a -> Int
depth Leaf         = 0
depth (Node l _ r) = 1 + max (depth l) (depth r)

-- exhaustive: -fwarn-incomplete-patterns 로 누락 case 경고
```

**관련 패턴**: [Functor](#functor), [Monad](#monad), Visitor (OO 대응 — trade-off 반대), Strategy (OO)

---

<a id="persistent-data-structures"></a>

## 11. Persistent Data Structures (지속 자료구조)

**정의**: 갱신 시 *기존 버전을 보존* 하면서 새 버전을 만드는 immutable 자료구조. *Structural sharing* 으로 O(log n) ~ O(1) 갱신.

**핵심 — Structural Sharing**:
```
원본 List:    [1, 2, 3, 4, 5]
prepend 0:    [0]──┐
                   ├──[1, 2, 3, 4, 5]   ← 공유
원본 그대로:  [1, 2, 3, 4, 5]
```
"복사" 가 아니라 *공유 + 차분*. 메모리·시간 모두 효율적.

**주요 구조와 복잡도**:
| 구조 | get | update | append | prepend |
|---|---|---|---|---|
| **Persistent List** (cons) | O(n) | O(n) | O(n) | O(1) |
| **Persistent Vector (HAMT)** | O(log32 n) ≈ O(1) | O(log32 n) | O(log32 n) | O(log32 n) |
| **Persistent HashMap (HAMT)** | O(log32 n) | O(log32 n) | — | — |
| **Finger Tree** | O(log n) | O(log n) | O(1) amortized | O(1) amortized |
| **Red-Black Tree** | O(log n) | O(log n) | O(log n) | O(log n) |

**HAMT (Hash Array Mapped Trie)**:
Clojure / Scala / Kotlin Arrow / Immutable.js 의 핵심. 32-way trie 로 hash 의 5비트씩 소비. log32 n ≈ depth 7 (n=10억) → 거의 상수.

**Finger Tree**:
Haskell `Data.Sequence` 의 기반. 양 끝 amortized O(1), 중간 split/concat O(log n).

**장점**:
- 시간 여행 — 모든 이전 버전 보존
- Thread-safe 자동 (immutable)
- Equality 가 자연스러움 (값 비교)
- Undo/Redo / Event Sourcing 구현 쉬움
- React `useState`, Redux 의 기반

**단점**:
- 갱신 비용 — mutable 보다 1~10x 느림 (HAMT 도 cache locality 약함)
- 메모리 — 노드 객체 오버헤드
- 학습 곡선 — Vector / Seq / HashMap 의 trade-off 이해 필요

**활용 예시**:
- **Clojure** `vector` / `map` / `set` — HAMT 기반 표준
- **Scala** `Vector` / `HashMap` — HAMT
- **Kotlin** `kotlinx.collections.immutable` — PersistentList / PersistentMap
- **Haskell** `Data.Sequence` (Finger Tree), `Data.Map` (Red-Black Tree)
- **Immutable.js** — JS HAMT 라이브러리
- **React** — 가상 DOM diff
- **Redux** — state 의 immutable 갱신
- **Git** — commit tree 의 structural sharing

**Kotlin 예제**:
```kotlin
import kotlinx.collections.immutable.persistentListOf
import kotlinx.collections.immutable.persistentMapOf

val v1 = persistentListOf(1, 2, 3, 4, 5)
val v2 = v1.add(6)           // [1,2,3,4,5,6] — v1 은 그대로
val v3 = v1.set(0, 100)       // [100,2,3,4,5] — v1, v2 모두 그대로

println(v1)  // [1, 2, 3, 4, 5]
println(v2)  // [1, 2, 3, 4, 5, 6]
println(v3)  // [100, 2, 3, 4, 5]

val m1 = persistentMapOf("a" to 1, "b" to 2)
val m2 = m1.put("c", 3)       // m1 그대로
```

**Clojure 예제**:
```clojure
(def v1 [1 2 3 4 5])
(def v2 (conj v1 6))     ; [1 2 3 4 5 6]
(def v3 (assoc v1 0 100)) ; [100 2 3 4 5]
;; v1, v2, v3 모두 다른 버전이면서 메모리 공유
```

**관련 패턴**: [Lens](#lens-optics), [Functor](#functor), Memento (OO), Prototype (OO)

---

## 요약 — Functional Patterns 선택 가이드

| 상황 | 패턴 |
|---|---|
| 컨테이너 안 값 변환 | [Functor](#functor) |
| 독립 effect 합성, 에러 누적 | [Applicative](#applicative-functor) |
| 순차 effect, IO/State 격리 | [Monad](#monad) |
| 프로그램·실행 분리, eDSL | [Free Monad](#free-monad) / [Tagless Final](#tagless-final) |
| 깊은 record 의 한 필드 갱신 | [Lens](#lens-optics) |
| async/await, generator, exception 일관 처리 | [Effect Handlers](#effect-handlers) |
| 콜백·코루틴의 컴파일 결과 | [CPS](#cps) |
| 깊은 재귀 stack overflow 회피 | [Trampolining](#trampolining) |
| Sum type 분기, 도메인 모델링 | [Pattern Matching](#pattern-matching-adt) |
| Immutable + 효율적 갱신 | [Persistent Data Structures](#persistent-data-structures) |

**패턴 간 의존 관계**:
```
Functor
  └─ Applicative
       └─ Monad
            ├─ Free Monad
            └─ Tagless Final  ─── alternative
       └─ Effect Handlers     ─── alternative (algebraic)

CPS ────── Trampolining ────── Free Monad (stack-safe 구현)

Pattern Matching + ADT ────── 모든 패턴의 기반 자료 표현
Persistent Data Structures ── Lens 의 효율적 갱신 기반
```
