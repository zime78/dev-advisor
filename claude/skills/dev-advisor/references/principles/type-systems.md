# 타입 시스템 이론 (Type System Theory)

CS 기초. 정평 있는 타입 시스템 개념 10 항목. SOLID/GRASP 같은 OO 설계 원칙과 별개의 **언어 이론·컴파일러 영역**.

**원전 참고**:
- Benjamin C. Pierce — *Types and Programming Languages* (2002), MIT Press
- Benjamin C. Pierce ed. — *Advanced Topics in Types and Programming Languages* (2005)
- Simon Peyton Jones — *The Implementation of Functional Programming Languages* (1987)

**핵심 가치**: 타입 시스템은 **컴파일 시점에 클래스의 오류를 차단** 하는 가벼운 형식적 방법(formal method). 강력한 타입 시스템 = 적은 런타임 버그 + 자기-문서화 코드 + 안전한 리팩토링.

**관련 카탈로그**:
- [solid.md](solid.md) — OO 설계 5 원칙
- [`../patterns/functional.md`](../patterns/functional.md) — Monad/Functor (HKT 활용)
- [`../languages/index.md`](../languages/index.md) — 75 언어 별 타입 시스템 비교
- [concurrency-theory.md](concurrency-theory.md) — Concurrency 도 type 으로 표현 가능 (effect system)

---

<a id="1-static-dynamic-typing"></a>
## 1. Static vs Dynamic Typing (정적 vs 동적 타이핑)

**정의**: 타입 검사 시점이 **컴파일 시점**(static) 인가 **런타임**(dynamic) 인가의 분류. Pierce *TAPL* §1.1 에서 "A type system is a tractable syntactic method for proving the absence of certain program behaviors" 로 정의 — static 타입 시스템은 *프로그램 실행 전* 에 특정 오류 부재를 증명한다.

**특징**:
- Static: 변수·표현식·함수 시그니처에 타입이 부착. 컴파일러가 검사 (`Java`, `Kotlin`, `Rust`, `Haskell`, `TypeScript`)
- Dynamic: 값(value) 에만 타입이 있고 변수는 어떤 값이든 담음. 인터프리터가 런타임에 검사 (`Python`, `Ruby`, `JavaScript`, `Lisp`)
- Static 은 *프로그램 행동의 상한선* 을 제한 — 가능한 런타임 동작 집합이 좁아짐
- Dynamic 은 *late binding* 으로 메타프로그래밍·duck typing 이 자연스러움
- "Static ⇒ Strong" 이 아님 (C 는 static + weak), "Dynamic ⇒ Weak" 도 아님 (Python 은 dynamic + strong)

**장점**:
- Static: 컴파일 시점 오류 차단, IDE 자동완성·리팩토링 지원, 실행 성능 (JIT/AOT 최적화), 자기-문서화
- Dynamic: 빠른 프로토타이핑, REPL·notebook 워크플로우, 메타프로그래밍 자유도, 짧은 시그니처

**단점/한계**:
- Static: 표현력 제약 (타입으로 표현 못하는 패턴은 차선책), 컴파일러 학습 곡선, generic·variance 같은 추가 복잡도
- Dynamic: 런타임 `TypeError` 만연, 큰 코드베이스 리팩토링 위험, IDE 보조 약함, 성능 손실

**언어 예시**:
- Static: `Java`, `C/C++`, `Kotlin`, `Swift`, `Rust`, `Go`, `Haskell`, `OCaml`, `F#`, `Scala`, `TypeScript`
- Dynamic: `Python`, `Ruby`, `JavaScript`, `PHP`, `Lua`, `Lisp`, `Clojure`, `Erlang`, `Smalltalk`
- Gradual (혼합): `TypeScript` (any 탈출구), `Python + mypy`, `PHP 7+ type hints`, `Dart` (sound mode), `Flow`

**난이도**: 낮음 (개념), 중간 (gradual typing 시스템 설계)

```kotlin
// Static (Kotlin) — 컴파일 시점 차단
fun greet(name: String): String = "Hello, $name"
greet(42)  // 컴파일 에러: Type mismatch — Required: String, Found: Int

// Static + 추론 — 명시 없어도 타입 보장
val n = 42       // 컴파일러: Int 로 추론
val s = "hello"  // 컴파일러: String 으로 추론
// n.toUpperCase()  // 컴파일 에러
```

```python
# Dynamic (Python) — 런타임 검사
def greet(name):
    return "Hello, " + name

greet(42)  # 런타임 TypeError: can only concatenate str (not "int") to str
# 코드를 실행하기 전까지 발견되지 않음
```

**관련 항목**:
- [strong-weak-typing](#2-strong-weak-typing) — 직교 축
- [hindley-milner](#4-hindley-milner) — static 추론 시스템
- [code-smell-primitive-obsession](code-smells.md#3-primitive-obsession) — static 환경에서 타입을 충분히 활용하지 않는 안티패턴
- [solid SRP](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) — static 타입은 책임 경계의 1차 문서

---

<a id="2-strong-weak-typing"></a>
## 2. Strong vs Weak Typing (강 vs 약 타이핑)

**정의**: 타입 위반에 대한 **암묵 변환(implicit coercion) 의 엄격성**. Strong 은 타입 불일치 시 변환 거부, Weak 는 자동 변환·재해석 허용. "Type safety" 와 거의 동의어로 쓰이며, *static vs dynamic* 축과 직교.

**특징**:
- Strong: `"5" + 3` 같은 표현식이 컴파일/런타임 에러 (`Python`, `Haskell`, `Rust`)
- Weak: 동일 표현식이 `"53"` 또는 `8` 같은 결과로 강제 변환 (`JavaScript`, `PHP`, `C`)
- C 의 포인터 캐스팅·union 은 weak typing 의 극단 — 비트 패턴 재해석 허용
- "Strong" 의 엄격성은 스펙트럼 — Haskell 이 가장 엄격, Java 는 numeric promotion 일부 허용
- Strong 타입 시스템도 명시적 변환(explicit cast) 은 제공 (`(int) x`, `x as Int`, `x.toInt()`)

**장점**:
- 의도하지 않은 변환 차단 → 데이터 손실·정밀도 손실 버그 예방
- 표현식 의미가 명확 → 코드 리뷰 부담 감소
- "garbage in, garbage out" 대신 fail-fast

**단점/한계**:
- 짧은 스크립트에서 명시적 변환이 장황
- DSL·템플릿 코드에서 boilerplate 증가
- 외부 데이터(JSON/CSV) 처리 시 명시적 파싱 코드 필요

**언어 예시**:
- 강력한 Strong: `Haskell`, `Rust`, `OCaml`, `Elm`, `Idris`
- 실용적 Strong: `Python`, `Ruby`, `Kotlin`, `Swift`, `Go`, `Java` (numeric promotion 예외)
- Weak: `JavaScript`, `PHP`, `Perl`, `VBScript`, `C/C++` (cast/union 영역)

**난이도**: 낮음

```javascript
// Weak (JavaScript) — 자동 강제 변환
console.log('5' + 3)      // '53'  (문자열 결합)
console.log('5' - 3)      // 2     (숫자 차감)
console.log(true + 1)     // 2     (boolean → number)
console.log([] == false)  // true  (배열 → 문자열 → 숫자 비교)
console.log(null == undefined)  // true (특수 케이스)
// === (strict equality) 만 strong 비교
```

```python
# Strong (Python) — 암묵 변환 거부
print('5' + 3)
# TypeError: can only concatenate str (not "int") to str

# 명시적 변환 필수
print('5' + str(3))   # '53'
print(int('5') + 3)   # 8
```

```rust
// Strong + Static (Rust) — 가장 엄격
let x: i32 = 5;
let y: i64 = x;       // 컴파일 에러: expected i64, found i32
let y: i64 = x as i64;  // 명시적 cast 필수
```

**관련 항목**:
- [static-dynamic-typing](#1-static-dynamic-typing) — 직교 축
- [nominal-structural-typing](#3-nominal-structural-typing) — 타입 동등성 판정
- [code-smell-primitive-obsession](code-smells.md#3-primitive-obsession) — weak typing 환경에서 빈발하는 매직 값/원시값 남용과 연결

---

<a id="3-nominal-structural-typing"></a>
## 3. Nominal vs Structural Typing (명목적 vs 구조적 타이핑)

**정의**: 두 타입이 "같다" 를 판정하는 기준. **Nominal** 은 *이름(declaration)* 일치, **Structural** 은 *형태(shape)* 일치. Pierce *TAPL* §19 "Recursive Types" 에서 양 시스템을 비교.

**특징**:
- Nominal: 같은 이름·같은 상속 계층만 호환. `class A` 와 `class B` 가 동일 메서드 셋을 가져도 별개의 타입 (`Java`, `Kotlin`, `C#`, `Rust`, `Swift`)
- Structural: 메서드/필드 시그니처가 일치하면 호환. *Duck Typing* 의 정적 버전 (`TypeScript`, `Go` interface, `OCaml`, `Scala` 의 structural type)
- Hybrid: `Scala` 는 클래스는 nominal, refinement type 은 structural. `Kotlin` 은 일반 클래스는 nominal 이지만 lambda 타입은 structural
- Structural 의 이론적 기반은 **subtype relation** — "B 의 멤버 집합이 A 의 부분집합이면 B 는 A 의 서브타입"

**장점**:
- Nominal: 의도된 인터페이스 일치만 허용 → 의도 표현 명확, "우연한 일치" 차단
- Structural: 라이브러리 간 결합 없이도 호환 → 모듈 간 결합도 감소, 가벼운 mock 작성 용이
- Structural 은 retrofit 에 강함 — 기존 클래스에 *새 interface 선언만으로* 호환 처리

**단점/한계**:
- Nominal: 동일한 형태의 서드파티 타입끼리 어댑터 코드 필요, "boilerplate interface" 양산
- Structural: 의도하지 않은 매칭 위험 (시그니처는 같지만 의미는 다른 두 타입), 이름이 없어 IDE refactor 보조 약함
- Structural 의 오용은 [LSP](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙) 위반과 유사한 의미 충돌 유발

**언어 예시**:
- Nominal: `Java`, `Kotlin`, `C#`, `C++`, `Swift`, `Rust`, `Haskell` (newtype 으로 nominal 강화)
- Structural: `Go` (interface), `TypeScript`, `OCaml` (object type), `Scala` (refinement), `Python` (`typing.Protocol`)
- Duck Typing (Structural 의 dynamic 변형): `Python`, `Ruby`, `JavaScript`, `Smalltalk`

**난이도**: 중간

```kotlin
// Nominal (Kotlin) — 이름 일치 필요
interface Quacker { fun quack() }
class Duck { fun quack() {} }
class RealDuck : Quacker { override fun quack() {} }

fun feed(q: Quacker) { q.quack() }
feed(Duck())       // 컴파일 에러: Type mismatch (Duck 은 Quacker 아님)
feed(RealDuck())   // OK — Quacker 를 명시적으로 구현
```

```typescript
// Structural (TypeScript) — 형태 일치만으로 충분
interface Quacker { quack(): void }
class Duck {
  quack() { console.log("quack") }
}

function feed(q: Quacker) { q.quack() }
feed(new Duck())  // OK — Duck 이 Quacker 와 구조적으로 일치
// "implements Quacker" 선언 없이도 매칭됨
```

```go
// Go interface — 암묵적 structural
type Quacker interface { Quack() }
type Duck struct{}
func (d Duck) Quack() { fmt.Println("quack") }

func feed(q Quacker) { q.Quack() }
feed(Duck{})  // OK — Duck 이 Quack() 보유
// "implements" 키워드 자체가 없음
```

**관련 항목**:
- [static-dynamic-typing](#1-static-dynamic-typing) — Duck Typing 은 dynamic + structural
- [variance](#6-variance) — subtype relation 의 일반화
- [solid LSP](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙) — 행위 호환성 (structural 일치만으로는 부족)
- [solid ISP](solid.md#4-interface-segregation-principle-isp-인터페이스-분리-원칙) — role interface 와 자연스러운 시너지

---

<a id="4-hindley-milner"></a>
## 4. Hindley-Milner Type Inference (HM 타입 추론)

**정의**: J. Roger Hindley(1969) 와 Robin Milner(1978) 가 독립적으로 발견한 **let-polymorphic 타입 추론 알고리즘**. 명시적 타입 선언 없이도 표현식의 가장 일반적인 타입(principal type) 을 다항 시간에 추론. **Algorithm W** 가 표준 구현.

**특징**:
- 입력: 타입 annotation 없는 람다 항(λ-calculus term)
- 출력: principal type (가능한 모든 타입 중 가장 일반적인 형태)
- 핵심 기법: **unification** (타입 변수의 substitution 을 점진 누적)
- `let x = e1 in e2` 에서 `x` 가 **다형(polymorphic)** 으로 일반화 — `let id = λx.x` 의 `id` 는 `∀α. α → α`
- HM 자체는 *prenex polymorphism* 만 지원 — `(∀α. α→α) → Int` 같은 *rank-2* 이상은 별도 확장 필요

**장점**:
- 타입 annotation 부담 거의 없음 → 보일러플레이트 감소
- principal type 보장 → 추론 결과의 유일성·예측 가능성
- soundness + completeness 동시 성립 (HM 영역 내)
- 코드 변경 시 타입이 자동 재추론 → 리팩토링 용이

**단점/한계**:
- *Higher-rank polymorphism* 미지원 (Haskell GHC 의 `RankNTypes` 확장 필요)
- Subtyping 과 자연스럽게 결합 안 됨 → OO 언어 적용 어려움
- Overloading (ad-hoc polymorphism) 부재 → Haskell 은 typeclass 로 보완
- 오류 메시지가 종종 난해 — unification 실패 지점이 실제 버그 위치와 다를 수 있음

**언어 예시**:
- 순수 HM 후예: `ML`, `OCaml`, `F#`, `Standard ML`
- HM + typeclass: `Haskell`, `PureScript`, `Elm`
- HM 영향 (부분 채택): `Rust` (로컬 추론), `Scala` (제한적), `Swift` (로컬), `Kotlin` (로컬)
- 비-HM: `Java` (Var 추론은 로컬만), `C++` (`auto` 는 단방향), `TypeScript` (flow analysis 기반)

**난이도**: 높음 (이론), 낮음 (사용)

```haskell
-- Haskell — 타입 annotation 없이 HM 이 추론
compose f g x = f (g x)
-- 추론: compose :: (b -> c) -> (a -> b) -> a -> c

map' f []     = []
map' f (x:xs) = f x : map' f xs
-- 추론: map' :: (a -> b) -> [a] -> [b]

-- let-polymorphism: id 가 호출마다 다른 타입으로 인스턴스화
demo = let id' = \x -> x
       in (id' 42, id' "hello")
-- id' :: ∀a. a → a   (다형)
-- 첫 호출: Int → Int / 둘째 호출: String → String
```

```ocaml
(* OCaml — 동일한 HM 추론 *)
let rec map f = function
  | []      -> []
  | x :: xs -> f x :: map f xs
(* val map : ('a -> 'b) -> 'a list -> 'b list *)
```

```rust
// Rust — 로컬 추론 (HM 영향, 함수 시그니처는 명시 필수)
fn main() {
    let v = vec![1, 2, 3];           // Vec<i32> 추론
    let s = v.iter().sum::<i32>();   // turbofish 로 타입 힌트
    let doubled = v.iter().map(|x| x * 2).collect::<Vec<_>>();
    // 시그니처에는 타입 명시 필요 (HM 후예와 다른 점)
}
```

**관련 항목**:
- [static-dynamic-typing](#1-static-dynamic-typing) — HM 은 static 추론의 정점
- [adt](#5-adt) — HM 과 ADT 결합으로 표현력 극대화
- [hkt](#7-hkt) — HM 의 자연스러운 확장
- [effect-system](#10-effect-system) — Koka/Eff 는 HM 위에 effect row 추론

---

<a id="5-adt"></a>
## 5. Algebraic Data Types (대수적 데이터 타입, ADT)

**정의**: **Sum type** (`A | B`, 합집합) + **Product type** (`A × B`, 곱집합) 을 결합해 만드는 합성 타입. "대수적" 이라는 이름은 타입을 *대수 구조* 로 보는 데서 유래 — Sum 은 `+`, Product 는 `×` 로 표현. Pierce *TAPL* §11.

**특징**:
- **Product type**: tuple, record, struct. 모든 필드 동시 보유 — `(Int, String)`, `data Point = Point { x: Int, y: Int }`
- **Sum type**: variant, tagged union, sealed hierarchy. *정확히 하나의 케이스* 만 보유 — `data Shape = Circle Double | Rectangle Double Double`
- **Pattern matching** 과 짝 — 케이스별 분기 + **exhaustiveness check** (모든 케이스 처리 강제)
- `Option<T>` / `Maybe a` / `Either<E, A>` / `Result<T, E>` 가 모두 sum type 의 표준 예
- ADT 는 *closed* — 새 케이스 추가 시 모든 패턴 매칭 코드 재컴파일. OO 의 *open* 다형성과 trade-off

**장점**:
- "잘못된 상태를 표현 불가능하게(Make illegal states unrepresentable)" — Yaron Minsky 의 design rule
- Exhaustive pattern matching 으로 케이스 누락 컴파일 시점 차단
- `null` 폐기 — `Option<T>` 가 부재를 명시적으로 표현
- 도메인 모델링과 자연스러운 매칭 — DDD 의 *Algebraic Domain Modeling* 표준

**단점/한계**:
- 새 케이스 추가가 invasive (Expression Problem 의 한 측면)
- OO 의 *visitor 없이 다형성* 패턴과 trade-off — ADT 는 *데이터 종류 추가* 가 어렵고, *연산 추가* 가 쉬움 (OO 는 반대)
- 깊은 nested sum type 은 가독성 저하 — flatten 또는 named variant 권장

**언어 예시**:
- 순수 ADT: `Haskell`, `OCaml`, `Elm`, `PureScript`, `Idris`, `Agda`
- Strong ADT: `Rust` (enum), `Scala` (sealed trait), `F#` (discriminated union), `Swift` (enum with associated values)
- 부분 ADT: `Kotlin` (sealed class/interface — 명시 sealed 필요), `TypeScript` (discriminated union), `Java 21+` (sealed + pattern matching)
- 부재: `Go` (interface + type switch 로 우회), `Python` (`match` 가 3.10+ 지원하나 exhaustiveness 미보장)

**난이도**: 중간

```rust
// Rust — sum + product 결합
enum Shape {
    Circle(f64),                          // 1 필드 product
    Rectangle { width: f64, height: f64 },// named product
    Triangle(f64, f64, f64),              // 3 필드 product
}

fn area(s: &Shape) -> f64 {
    match s {
        Shape::Circle(r) => std::f64::consts::PI * r * r,
        Shape::Rectangle { width, height } => width * height,
        Shape::Triangle(a, b, c) => {
            let s = (a + b + c) / 2.0;
            (s * (s - a) * (s - b) * (s - c)).sqrt()
        }
        // 케이스 빠뜨리면 컴파일 에러 — exhaustiveness
    }
}

// Option/Result — 표준 ADT
fn parse(s: &str) -> Result<i32, String> {
    s.parse::<i32>().map_err(|e| e.to_string())
}
```

```haskell
-- Haskell — 가장 순수한 ADT
data Maybe a = Nothing | Just a
data Either a b = Left a | Right b

-- 재귀 ADT
data List a = Nil | Cons a (List a)

-- 패턴 매칭 (exhaustive 강제)
length' :: List a -> Int
length' Nil         = 0
length' (Cons _ xs) = 1 + length' xs
```

```kotlin
// Kotlin — sealed class 로 ADT 흉내
sealed class Shape {
    data class Circle(val r: Double) : Shape()
    data class Rectangle(val w: Double, val h: Double) : Shape()
}

fun area(s: Shape): Double = when (s) {
    is Shape.Circle    -> Math.PI * s.r * s.r
    is Shape.Rectangle -> s.w * s.h
    // sealed 라 else 불필요 — exhaustive
}
```

**관련 항목**:
- [hindley-milner](#4-hindley-milner) — HM 과 ADT 는 정통 함수형 언어의 두 축
- [hkt](#7-hkt) — `Maybe`, `Either` 등 ADT 의 일반화
- [grasp Polymorphism](grasp.md#6-polymorphism) — OO 다형성과 대조되는 sum type 다형성
- [code-smell-switch-statements](code-smells.md#7-switch-statements) — ADT + pattern matching 은 switch 안티패턴의 해독제

---

<a id="6-variance"></a>
## 6. Generics & Variance (제네릭 변성)

**정의**: 제네릭 타입 `F<T>` 에 대해 `T1 <: T2` 일 때 `F<T1>` 과 `F<T2>` 의 부타입 관계. **Covariant** (보존: `F<T1> <: F<T2>`), **Contravariant** (역전: `F<T2> <: F<T1>`), **Invariant** (무관계), **Bivariant** (양방향 — unsound). Pierce *TAPL* §15.

**특징**:
- **Covariant**: `Producer<Cat>` → `Producer<Animal>` (생산자는 더 일반적 타입으로 본 안전)
- **Contravariant**: `Consumer<Animal>` → `Consumer<Cat>` (소비자는 더 구체적 타입으로 본 안전)
- **Invariant**: `List<Cat>` ↔ `List<Animal>` 호환 불가 (읽기·쓰기 모두 가능한 mutable 컨테이너)
- **PECS** (Producer Extends, Consumer Super) — Joshua Bloch *Effective Java* §31. Java `? extends T` (covariant out), `? super T` (contravariant in)
- **Declaration-site** variance: Kotlin/Scala — 타입 선언 시 `out T` / `in T` 로 한 번 결정 (`class Producer<out T>`)
- **Use-site** variance: Java — 사용 시점에 `? extends`/`? super` (wildcard) 로 결정

**장점**:
- 호환 가능한 타입을 정확히 표현 → 안전한 다형 컨테이너
- mutable/immutable 차이를 타입 시스템에 반영 — read-only 는 covariant, write-only 는 contravariant 가능
- PECS 패턴으로 API 설계 일관성 확보

**단점/한계**:
- 변성 규칙은 직관과 어긋남 (특히 contravariant) — 학습 곡선
- 잘못된 변성 표기는 [LSP](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙) 위반 (Java 배열의 unsound covariance — `Object[] arr = new String[1]; arr[0] = 42` 가 런타임 `ArrayStoreException`)
- mutable 컨테이너는 거의 항상 invariant — 사용성 떨어짐
- Higher-kinded 와 결합 시 복잡도 폭증

**언어 예시**:
- Declaration-site: `Kotlin` (`out`/`in`), `Scala` (`+T`/`-T`), `C#` (`out`/`in`)
- Use-site: `Java` (`? extends`/`? super`), `Kotlin` (use-site도 지원)
- 모두 invariant 기본: `Rust` (variance 추론하나 명시 사용 드묾), `TypeScript` (구조적 매칭으로 우회)
- Unsound covariant: `Java 배열` (역사적 결정 — 1.5 의 제네릭이 invariant 인 이유)

**난이도**: 높음

```kotlin
// Kotlin — declaration-site variance
class Producer<out T>(private val value: T) {
    fun produce(): T = value   // T 는 out 위치만 허용
    // fun consume(t: T) {}    // 컴파일 에러: in 위치 금지
}

class Consumer<in T> {
    fun consume(t: T) { println(t) }
    // fun produce(): T = ...  // 컴파일 에러: out 위치 금지
}

open class Animal
class Cat : Animal()

fun demo() {
    val p1: Producer<Cat> = Producer(Cat())
    val p2: Producer<Animal> = p1   // OK — covariant

    val c1: Consumer<Animal> = Consumer()
    val c2: Consumer<Cat> = c1      // OK — contravariant
}

// PECS — Producer Extends, Consumer Super
fun <T> copy(from: List<out T>, to: MutableList<in T>) {
    for (x in from) to.add(x)
}
```

```scala
// Scala — +T (covariant) / -T (contravariant)
trait Function1[-A, +R] {
    def apply(a: A): R
}
// 입력은 contravariant, 출력은 covariant — 함수 타입의 표준 변성
```

```java
// Java — use-site (wildcard)
List<? extends Animal> producers = new ArrayList<Cat>();  // covariant
Animal a = producers.get(0);  // OK — 읽기 가능
// producers.add(new Cat());   // 컴파일 에러 — 쓰기 금지

List<? super Cat> consumers = new ArrayList<Animal>();    // contravariant
consumers.add(new Cat());  // OK — 쓰기 가능
// Cat c = consumers.get(0); // 컴파일 에러 — Cat 보장 못함 (Object 만 안전)
```

**관련 항목**:
- [nominal-structural-typing](#3-nominal-structural-typing) — subtype 관계의 기초
- [hkt](#7-hkt) — variance + HKT 결합 시 polarity 추적 필요
- [solid LSP](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙) — 변성 위반은 LSP 위반
- [solid OCP](solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙) — 정확한 변성 표기 = 확장 안전성

---

<a id="7-hkt"></a>
## 7. Higher-Kinded Types (고차 종류 타입, HKT)

**정의**: 타입 변수가 **타입 생성자(type constructor)** 자체를 받을 수 있는 시스템. `F<_>` 같은 *kind* 를 가진 추상 — `F` 가 어떤 타입 생성자든 추상화 가능. **Kind** 는 "타입의 타입" — `Int` 의 kind 는 `*`, `List` 의 kind 는 `* → *`, `Map` 의 kind 는 `* → * → *`.

**특징**:
- HKT 없이는 `Functor`, `Monad`, `Traversable` 같은 *F 가 무엇이든* 통하는 추상 정의 불가
- Haskell `class Functor f where fmap :: (a -> b) -> f a -> f b` — 여기 `f` 가 HKT (`* → *`)
- Scala 의 `F[_]`, Haskell 의 `f a` — 둘 다 1-arity 타입 생성자 자리표시자
- Kotlin/Java 는 부재 — *Arrow-kt* 같은 라이브러리가 type alias + 트릭으로 흉내
- `Monad` 일반화는 `do-notation`/`for-comprehension`/`async-await` 의 이론적 근거

**장점**:
- 컨테이너 무관 추상 작성 가능 — 같은 `map`/`flatMap` 코드가 `List`, `Option`, `Future`, `IO` 에 통일 작동
- 라이브러리 추상화 수준 한 단계 상승 — `cats` (Scala), `fp-ts` (TypeScript), `Arrow` (Kotlin)
- 도메인 추상을 *effect 무관* 으로 표현 가능 — Tagless Final 스타일

**단점/한계**:
- 학습 곡선 가파름 — Functor → Applicative → Monad → MonadTransformer 의 layered abstraction
- 컴파일 오류 메시지 난해 — kind mismatch 진단이 일반 type mismatch 보다 어려움
- 추론 능력 한계 — Scala 의 partial application 트릭(`type Lambda[A] = Either[String, A]`) 필요
- 과한 추상화는 [Speculative Generality](code-smells.md#18-speculative-generality) 와 직결

**언어 예시**:
- 1급 HKT: `Haskell`, `PureScript`, `Idris`, `Agda`
- 실용 HKT: `Scala` (full), `OCaml` (functor 로 우회)
- 라이브러리 HKT: `TypeScript` + `fp-ts`, `Kotlin` + `Arrow-kt`
- 부재: `Java`, `Go`, `Rust` (GAT 로 부분 보완), `C#`, `Swift`

**난이도**: 매우 높음

```haskell
-- Haskell — Functor type class (HKT 의 정수)
class Functor f where
    fmap :: (a -> b) -> f a -> f b

-- 인스턴스 — 같은 fmap 시그니처가 List/Maybe/Either 에 통일 적용
instance Functor [] where
    fmap = map

instance Functor Maybe where
    fmap _ Nothing  = Nothing
    fmap g (Just x) = Just (g x)

instance Functor (Either e) where
    fmap _ (Left x)  = Left x
    fmap g (Right x) = Right (g x)

-- Monad — flatMap 의 추상화
class Monad m where
    return :: a -> m a
    (>>=)  :: m a -> (a -> m b) -> m b
```

```scala
// Scala — F[_] 로 HKT 표현
trait Functor[F[_]] {
    def map[A, B](fa: F[A])(f: A => B): F[B]
}

implicit val optionFunctor: Functor[Option] = new Functor[Option] {
    def map[A, B](fa: Option[A])(f: A => B): Option[B] = fa.map(f)
}

implicit val listFunctor: Functor[List] = new Functor[List] {
    def map[A, B](fa: List[A])(f: A => B): List[B] = fa.map(f)
}

// F 무관 일반 함수
def double[F[_]](fa: F[Int])(implicit F: Functor[F]): F[Int] =
    F.map(fa)(_ * 2)

double(List(1, 2, 3))    // List(2, 4, 6)
double(Some(5))           // Some(10)
```

```kotlin
// Kotlin — HKT 부재. Arrow-kt 로 흉내
// 실무에서는 결국 인터페이스를 효과(effect) 별로 따로 작성하는 게 일반적
interface Functor<F> {  // F 는 marker — 실제 HKT 아님
    fun <A, B> map(fa: Kind<F, A>, f: (A) -> B): Kind<F, B>
}
// Kind<F, A> 는 *type-level eraser* 트릭 — 진짜 HKT 와는 다름
```

**관련 항목**:
- [adt](#5-adt) — Option/Either 등이 HKT 의 주요 인스턴스
- [hindley-milner](#4-hindley-milner) — HM 위에 HKT 가 자연 확장
- [effect-system](#10-effect-system) — `IO`/`Task` 같은 effect 타입이 HKT 의 핵심 응용
- [`../patterns/functional.md`](../patterns/functional.md) — Functor/Monad 패턴

---

<a id="8-linear-types"></a>
## 8. Linear / Affine / Substructural Types (선형·아핀 타입)

**정의**: 값의 **사용 횟수** 를 타입으로 제한하는 시스템. 표준 타입 시스템(λ-calculus) 의 *구조 규칙* (weakening = 사용 안함 / contraction = 중복 사용) 을 제한하기에 **substructural type system** 으로 분류. 1987 년 Jean-Yves Girard 의 *Linear Logic* 이 이론적 기원.

**특징**:
- **Linear**: 값은 **정확히 1회** 사용 (버리지도 복제도 안 됨)
- **Affine**: 값은 **최대 1회** 사용 (버려도 OK, 복제는 금지)
- **Relevant**: 값은 **최소 1회** 사용 (복제 OK, 버리는 건 금지)
- **Ordered**: 사용 순서까지 강제
- Rust 의 *ownership* 은 사실상 **affine type** — 변수는 한 번 move 되면 사용 불가, 사용 안 해도 OK (drop)
- `Borrow` 는 affine 의 임시 완화 — `&T` (공유 빌림) / `&mut T` (배타적 빌림)

**장점**:
- 자원 안전성 컴파일 시점 보장 — 파일 핸들·소켓·메모리의 use-after-free / double-free 차단
- GC 없이 메모리 안전 (Rust 의 핵심 가치 명제)
- 동시성 안전 — `Send`/`Sync` 가 affine 위에 구축
- "Effect once" 패턴 (트랜잭션 commit 1회, channel close 1회) 표현 가능

**단점/한계**:
- 학습 곡선 — Rust 의 "borrow checker fight" 가 대표 사례
- 함수형 패턴 일부 제약 (자유로운 alias·shared mutable state 불가)
- 자료구조 설계 패러다임 전환 필요 (`Rc<RefCell<T>>`, `Arc<Mutex<T>>` 같은 우회로 빈번)
- Linear Haskell 은 *옵트인* — 기존 코드와 호환성 위해 일반 함수와 공존

**언어 예시**:
- Affine 정통: `Rust` (ownership = affine)
- Linear 옵트인: `Linear Haskell` (GHC 9.0+, `%1 ->`), `Idris 2` (quantitative types)
- 연구 언어: `Clean` (uniqueness types), `ATS`, `Granule`
- 영향 받음: `Swift` (consume/borrow 키워드 추가 중), `Kotlin` (move semantics 논의 단계)

**난이도**: 높음

```rust
// Rust — affine type (ownership)
fn take(s: String) {
    println!("{}", s);
}  // s drop

fn main() {
    let s = String::from("hello");
    take(s);
    // println!("{}", s);  // 컴파일 에러: value borrowed after move
    //                       (s 는 take 호출로 move 됨 — affine)
}

// Borrow 로 affine 완화
fn read(s: &String) {
    println!("{}", s);
}

fn main2() {
    let s = String::from("hello");
    read(&s);
    read(&s);   // OK — &s 는 affine 위반 아님
    println!("{}", s);  // OK — s 의 ownership 유지
}

// Use-once 의 효용 — 파일 핸들
use std::fs::File;
fn process(f: File) -> std::io::Result<()> {
    // f 가 move 됨 — 호출자는 더 이상 f 사용 못함
    // 파일이 process 안에서 정확히 한 번 소비됨을 타입이 보장
    Ok(())
}
```

```haskell
-- Linear Haskell (GHC 9.0+)
{-# LANGUAGE LinearTypes #-}

-- %1 -> : linear arrow (정확히 1회 사용)
useOnce :: a %1 -> a
useOnce x = x  -- OK

-- duplicate :: a %1 -> (a, a)
-- duplicate x = (x, x)  -- 컴파일 에러: x 가 2회 사용됨

-- 자원 사용 패턴
withFile :: FilePath -> (Handle %1 -> IO r) -> IO r
-- Handle 이 1회만 사용됨을 보장 — 누수 차단
```

**관련 항목**:
- [effect-system](#10-effect-system) — 자원 관리는 effect 와 자주 결합
- [code-smell-alternative-classes](code-smells.md#9-alternative-classes-with-different-interfaces) — linear/affine 은 mutable 상태 경계가 달라지는 타입 설계를 명시화
- [solid SRP](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) — 자원 소유 책임의 명시
- [concurrency-theory Ownership](concurrency-theory.md) — Send/Sync 의 기반

---

<a id="9-dependent-types"></a>
## 9. Dependent Types (의존 타입)

**정의**: **값(value)** 에 의존하는 타입. `Vec<T, n>` 처럼 길이 `n` (값) 이 타입의 일부. λΠ-calculus 가 이론적 기반 — 타입과 값의 구분이 흐려지며, *프로그램 = 증명* 의 Curry-Howard 대응이 정점에 도달.

**특징**:
- 일반 제네릭: `Vec<T>` (타입 매개변수)
- 의존 타입: `Vec<T, n: Nat>` (타입 + 값 매개변수) — `concat : Vec<T, m> -> Vec<T, n> -> Vec<T, m+n>`
- **Π-type** (의존 함수): `(x : A) -> B(x)` — B 가 입력 x 에 의존
- **Σ-type** (의존 쌍): `(x : A, B(x))` — 두 번째 요소의 타입이 첫 번째 값에 의존
- **Totality checker** 필수 — 모든 함수가 종료해야 (HALT 해야) 타입 검사 신뢰 가능
- 정리 증명(theorem proving) 과 프로그래밍의 통합 — Coq, Lean, Agda

**장점**:
- 타입으로 *불변식* 직접 표현 — "정렬된 리스트", "비어있지 않은 트리", "행렬 곱셈 호환 차원" 등
- 런타임 검사 제거 가능 — 컴파일 시점에 사양 만족 증명
- 형식 검증(formal verification) 과 일상 코딩의 통합 — seL4 마이크로커널, CompCert C 컴파일러
- 라이브러리 사양을 타입에 인코딩 → 잘못된 사용 차단

**단점/한계**:
- 학습 곡선 가장 가파름 — type theory 배경 지식 필요
- 컴파일 시간 폭증 (특히 증명 자동화 부족 시)
- 코드 양 증가 — 단순 함수도 증명 의무 발생
- 실무 도구 미성숙 — 디버거·프로파일러·IDE 보조 부족
- Decidability trade-off — 완전한 의존 타입은 type checking 자체가 undecidable 가능

**언어 예시**:
- 1급 의존 타입: `Idris 2`, `Agda`, `Coq`, `Lean 4`, `F*`
- 부분 의존 타입: `Haskell` (GADT + DataKinds + TypeFamilies), `TypeScript` (literal type + template literal)
- 의존 타입 흉내: `Rust` (const generics — 값에 의존하나 제한적), `C++` (template metaprogramming)
- 비-의존: `Java`, `Go`, `Kotlin`, `Swift`, `Python`

**난이도**: 매우 높음

```idris
-- Idris 2 — 의존 타입의 정수
-- Vec : (n : Nat) -> (a : Type) -> Type
-- 길이가 타입의 일부

-- 빈 벡터와 cons
data Vec : Nat -> Type -> Type where
    Nil  : Vec Z a
    (::) : a -> Vec n a -> Vec (S n) a

-- append : 길이의 합을 타입이 보장
append : Vec m a -> Vec n a -> Vec (m + n) a
append Nil       ys = ys
append (x :: xs) ys = x :: append xs ys

-- 빈 벡터의 head 호출은 컴파일 에러 — 타입이 빈 케이스를 차단
head : Vec (S n) a -> a
head (x :: _) = x
-- head Nil  -- 컴파일 에러: Nil 은 Vec Z a 이지 Vec (S n) a 가 아님
```

```typescript
// TypeScript — 제한적 의존 타입 (template literal + literal types)
type StringLength<S extends string> =
    S extends `${string}${infer Rest}` ? [unknown, ...StringLength<Rest>]['length'] : 0;

type L1 = StringLength<"hello">;  // 5 (컴파일 시점 추론)

// Route param 추출 — 타입이 문자열 값에 의존
type ExtractParams<S extends string> =
    S extends `${string}/:${infer Param}/${infer Rest}` ? Param | ExtractParams<`/${Rest}`> :
    S extends `${string}/:${infer Param}` ? Param :
    never;

type Params = ExtractParams<"/users/:id/posts/:postId">;
//   ^? "id" | "postId"
```

```haskell
-- Haskell — DataKinds + GADT 로 부분 의존 타입
{-# LANGUAGE DataKinds, GADTs, TypeFamilies #-}

data Nat = Z | S Nat

data Vec (n :: Nat) a where
    VNil  :: Vec 'Z a
    VCons :: a -> Vec n a -> Vec ('S n) a

-- 길이 타입 안전 head
vhead :: Vec ('S n) a -> a
vhead (VCons x _) = x
-- vhead VNil  -- 컴파일 에러
```

**관련 항목**:
- [hkt](#7-hkt) — 의존 타입은 HKT 의 자연스러운 일반화
- [adt](#5-adt) — GADT (Generalized ADT) 는 의존 타입의 부분 표현
- [linear-types](#8-linear-types) — Idris 2 는 dependent + quantitative (linear) 통합

---

<a id="10-effect-system"></a>
## 10. Effect System / Algebraic Effects (효과 시스템)

**정의**: 함수의 **부수효과(side effect)** — I/O, 예외, 상태 변경, async, 비결정성 — 를 타입 시그니처에 명시하는 시스템. *순수 함수* (effect 없음) 와 *효과를 가진 함수* (I/O, throws, async, …) 를 컴파일러가 구분. **Algebraic Effects** 는 Plotkin & Power(2003) 가 정식화한 모델 — effect 를 *연산자(operation)* + *handler* 로 분해.

**특징**:
- 함수 시그니처에 effect 가 *어떤 종류인지* 명시 — `read : String -> {io} String`
- 자바의 `throws IOException` 은 가장 단순한 effect system (checked exception)
- Kotlin 의 `suspend` 는 *async effect* 의 1급 표현
- Haskell 의 `IO a` monad 는 모든 effect 를 `IO` 안에 봉인 — 흑백 분리 (pure vs IO)
- **Algebraic Effects + Handlers**: effect 의 *해석* 을 호출 지점에서 결정 — exception 의 일반화
- **Row polymorphism**: Koka 같은 언어가 사용 — `f : Int -> <io, exn> Int` (effect row 가 다형성 지원)

**장점**:
- 효과를 명시하면 *어떤 코드가 무엇을 하는지* 타입만 봐도 파악 — 자기-문서화
- 순수 함수 격리 → 테스트·추론·병렬화 용이
- Algebraic effects 는 `async/await`, `generators`, `exception` 을 **하나의 메커니즘으로 통합** 가능
- React 의 *hooks* / OCaml 5 의 *effect handlers* — algebraic effects 의 실용 적용

**단점/한계**:
- Java checked exception 의 부정적 경험 — effect 폭증 / wrapping 강제
- 효과 추론이 부정확하면 보일러플레이트 증가 ("effect inference" 가 핵심 연구 주제)
- monad transformer 스택은 작성·읽기 어려움 (Haskell)
- Algebraic effects 는 자료구조에 비해 도입 사례 적음 — 산업 채택 진행 중

**언어 예시**:
- 명시적 effect: `Haskell` (IO/State/Reader monad), `Koka`, `Eff`, `Frank`, `Unison`, `Effekt`
- 부분 effect: `Java` (checked exception), `Kotlin` (`suspend`, `Throws`), `Scala` (`ZIO`/`cats-effect` 의 effect type)
- Algebraic effects 1급: `Koka`, `OCaml 5`, `Eff`, `Frank`
- 흉내: `JavaScript`/`TypeScript` (async/await + Promise), `Python` (typing.Awaitable + raise)
- 부재: `Go` (effect 추적 부재 — panic 으로 우회), `C` (none)

**난이도**: 높음

```haskell
-- Haskell — IO monad (effect 봉인)
getLine :: IO String         -- 시그니처가 I/O effect 명시
putStrLn :: String -> IO ()
pure :: a -> IO a            -- 순수 값을 IO 로 lift

-- 순수 함수 — effect 없음
double :: Int -> Int
double x = x * 2

-- effect 함수 — do notation
greet :: IO ()
greet = do
    putStrLn "What's your name?"
    name <- getLine                 -- IO effect
    putStrLn ("Hello, " ++ name)

-- main 만 IO 진입점 — 나머지는 가능한 한 순수
```

```kotlin
// Kotlin — suspend (async effect)
suspend fun fetchUser(id: Int): User {
    delay(100)  // suspend 만 호출 가능
    return api.get("/users/$id")
}

fun loadAndProcess(): User =
    fetchUser(1)  // 컴파일 에러: suspend 호출은 coroutine context 안에서만
```

```koka
// Koka — Algebraic effects + row polymorphism
fun lookup(name : string) : <exn, io> int {
    if name == "" then throw("empty") else parse-int(read-file(name))
}

// 시그니처가 <exn, io> 두 effect 를 row 로 표현
// caller 가 어떤 effect handler 를 제공할지 결정 가능

effect ask<a>
    fun ask() : a

fun example() : <ask<int>> int
    val x = ask()        // effect 호출
    x * 2

// handler — effect 의 해석 지정
fun runWithFive(action : () -> <ask<int>|e> int) : e int
    handle action
        fun ask() resume(5)   // ask 가 호출되면 5 반환

runWithFive(example)  // 결과: 10
```

```scala
// Scala — ZIO effect type
import zio.*

val program: ZIO[Console, IOException, Unit] =
    for {
        _    <- Console.printLine("Name?")
        name <- Console.readLine
        _    <- Console.printLine(s"Hello $name")
    } yield ()

// 시그니처가 (1) 의존성 (Console) (2) 가능한 에러 (IOException) (3) 결과 (Unit) 명시
// effect 가 모두 type 으로 추적
```

**관련 항목**:
- [hkt](#7-hkt) — IO/Task/ZIO 등 effect 타입은 HKT 의 핵심 응용
- [adt](#5-adt) — `Either`/`Result` 는 exception effect 의 sum type 표현
- [linear-types](#8-linear-types) — 자원 effect 와 결합 (use-once handler)
- [concurrency-theory](concurrency-theory.md) — async effect 가 concurrency 모델 결정
- [`../patterns/functional.md`](../patterns/functional.md) — Monad / Free Monad / Tagless Final

---

## 표준 인용

- Benjamin C. Pierce — *Types and Programming Languages* (2002), MIT Press — 정평 있는 표준 교과서
- Benjamin C. Pierce ed. — *Advanced Topics in Types and Programming Languages* (2005), MIT Press
- Robin Milner — "A Theory of Type Polymorphism in Programming" (1978), *JCSS* 17 — HM 원전
- J. Roger Hindley — "The Principal Type-Scheme of an Object in Combinatory Logic" (1969) — HM 원전 (독립)
- Jean-Yves Girard — "Linear Logic" (1987), *Theoretical Computer Science* 50 — Linear types 원전
- Barbara H. Liskov, Jeannette M. Wing — "A Behavioral Notion of Subtyping" (1994), *TOPLAS* 16 — Variance/LSP 결합
- Gordon Plotkin, John Power — "Algebraic Operations and Generic Effects" (2003) — Algebraic effects 원전
- Edwin Brady — *Type-Driven Development with Idris* (2017), Manning — 의존 타입 실용서
- Joshua Bloch — *Effective Java* 3rd ed. (2018), §31 — PECS 변성 패턴
- Bartosz Milewski — *Category Theory for Programmers* (2019) — HKT / Functor / Monad 카테고리 이론 배경

---

<a id="lambda-calculus"></a>
## 11. Lambda Calculus & System F (람다 대수 / System F)

**정의**: Alonzo Church(1936) 가 *계산 가능성(computability)* 을 형식화하기 위해 고안한 **함수 추상·적용만으로 모든 계산을 표현하는 최소 형식 체계**. 항(term) 은 세 가지뿐 — 변수 `x`, 추상 `λx.M` (함수 정의), 적용 `M N` (함수 호출). Turing machine 과 동치(Church-Turing thesis). 여기에 타입을 부착하면 **simply-typed λ-calculus**(STLC, Church 1940) 가 되고, 타입 변수를 1급으로 양화(quantify) 하면 **System F**(Jean-Yves Girard 1972 / John Reynolds 1974 가 독립 발견) 가 된다 — *parametric polymorphism* 의 이론적 정수. Pierce *TAPL* §5(untyped), §9(STLC), §23(System F).

**특징**:
- **Untyped λ-calculus** 의 3 연산:
  - **α-conversion** (알파 변환): 묶인 변수 이름 바꾸기 — `λx.x` ≡ `λy.y` (이름은 무의미)
  - **β-reduction** (베타 환원): 함수 적용 = 치환 — `(λx.M) N → M[x := N]` (계산의 본질)
  - **η-conversion** (에타 변환): `λx.(f x) ≡ f` (외연성, extensionality — 같은 입력에 같은 출력이면 같은 함수)
- **Church 인코딩**: 데이터를 순수 함수로 표현 — 숫자 `n` 을 "f 를 n 번 적용" 으로 (`0 = λf.λx.x`, `1 = λf.λx.f x`, `SUCC = λn.λf.λx.f (n f x)`), boolean 을 선택자로 (`TRUE = λx.λy.x`, `FALSE = λx.λy.y`)
- **Y combinator**: `Y = λf.(λx.f (x x)) (λx.f (x x))` — *재귀 없는 언어에서 재귀를 만드는* fixpoint 연산자. `Y g = g (Y g)` 를 만족. untyped 에서만 잘 동작 (STLC 에서는 타입 불가)
- **STLC**: 모든 항에 타입(`τ ::= base | τ → τ`) 부여 → **strong normalization** (모든 환원이 반드시 종료). 대가로 **Turing-incomplete** — Y combinator 표현 불가
- **System F**: `Λα.M` (타입 추상) + `M [τ]` (타입 적용) + `∀α.τ` (전칭 타입) 추가 → `id = Λα.λx:α.x : ∀α.α→α` 하나가 모든 타입에 통함. **2차 람다 대수(second-order λ-calculus)** 라고도 함
- **Parametricity** (Reynolds 1983): `∀α.α→α` 타입 함수는 *반드시* identity — 타입 시그니처만으로 동작이 강제됨 ("theorems for free", Wadler 1989)

**장점**:
- 모든 함수형 언어(Lisp, ML, Haskell, OCaml) 의 *수학적 기반* — `let`/`lambda`/closure 가 직접 대응
- β-reduction 은 컴파일러 *inlining·partial evaluation* 의 이론 모델
- System F 의 다형성으로 **타입 안전한 코드 재사용** — `id`, `map`, `compose` 를 타입마다 재작성할 필요 없음
- Curry-Howard 대응으로 *증명을 프로그램으로* 자동 추출 가능 (Coq `Extraction`, Agda)
- STLC 의 strong normalization = 타입 검사가 *전체성(totality)* 의 첫 보증

**단점/한계**:
- Untyped λ-calculus 는 표현력은 완전하나 *오류 차단 0* — `(λx.x x)(λx.x x)` 같은 무한 루프를 막지 못함
- STLC 는 안전하지만 *표현력 부족* — 다형성·재귀·데이터 타입을 별도 확장으로 추가해야 실용 언어가 됨
- **System F 의 타입 추론은 undecidable** (Wells 1994) — 그래서 실무 언어는 [Hindley-Milner](#4-hindley-milner) 같은 *제한된 단편(rank-1 prenex)* 만 자동 추론하고, 나머지는 명시 annotation 요구
- Church 인코딩은 이론적 우아함과 달리 *실행 성능 끔찍* — 실무는 primitive/네이티브 타입 사용
- 순수 λ-calculus 에는 부수효과·상태가 없음 — 실제 언어는 monad/effect 로 보강 (참조: [effect-system](#10-effect-system))

**언어 예시**:
- λ-calculus 직계: `Lisp`/`Scheme` (1958, 최초의 λ 기반 언어), `Haskell`, `OCaml`, `ML`, `F#`, `Scala`, `Clojure`
- System F 를 코어 IR 로 채택: `Haskell` (GHC 의 *System FC* — System F + coercion), `Scala` (DOT 계산), `Idris`
- System F 명시 다형성 노출: `Java` 제네릭(`<T>`), `C#`(`<T>`), `Rust`(`<T>`), `TypeScript`(`<T>`), `Swift`(`<T>`) — 모두 System F 의 부분 채택
- 클로저·1급 함수로 λ 직접 표현: 거의 모든 현대 언어 (`Python` `lambda`, `JavaScript` 화살표 함수, `Kotlin` 람다)
- 정리 증명기(Curry-Howard 정점): `Coq` (CIC), `Agda`, `Lean 4`, `Idris 2`

**난이도**: 높음 (이론), 낮음 (λ/closure 사용)

```haskell
-- Untyped λ-calculus — Church 인코딩 (Haskell 로 흉내)
-- Church 숫자: n = "f 를 n 번 적용"
zero  = \f x -> x            -- λf.λx.x
one   = \f x -> f x          -- λf.λx.f x
two   = \f x -> f (f x)      -- λf.λx.f (f x)
succ' = \n f x -> f (n f x)  -- λn.λf.λx.f (n f x)

-- Church boolean: 선택자
true'  = \x y -> x           -- λx.λy.x
false' = \x y -> y           -- λx.λy.y

-- β-reduction 예: (λx.x) 42 → 42
-- 검증: (succ' zero) (+1) 0 == 1
```

```haskell
-- Y combinator — 재귀 없이 재귀 (untyped 에서만 타입 가능)
-- Y = λf.(λx.f (x x)) (λx.f (x x))
-- Haskell 은 typed 라 newtype 우회 필요
newtype Mu a = Mu (Mu a -> a)
y :: (a -> a) -> a
y f = (\(Mu x) -> f (x (Mu x))) (Mu (\(Mu x) -> f (x (Mu x))))

fact = y (\rec n -> if n == 0 then 1 else n * rec (n - 1))
-- fact 5 == 120  —  Y 가 factorial 의 fixpoint 를 구성
```

```haskell
-- System F — 명시적 타입 추상/적용 (GHC RankNTypes 확장)
{-# LANGUAGE RankNTypes, TypeApplications #-}

-- id : ∀α. α → α  —  하나의 정의가 모든 타입에 통함
identity :: forall a. a -> a   -- Λα. λx:α. x
identity x = x

-- 타입 적용 (System F 의 M [τ])
demo1 = identity @Int 42        -- id [Int] 42
demo2 = identity @String "hi"   -- id [String] "hi"

-- rank-2: ∀ 가 인자 위치에 — HM 으론 추론 불가, System F 필요
applyToBoth :: (forall a. a -> a) -> (Int, String)
applyToBoth f = (f 1, f "x")
-- f 가 호출 안에서 두 타입으로 인스턴스화 — System F 의 표현력
```

```typescript
// System F 의 부분 채택 — TypeScript 제네릭
// ∀T. T → T  를 명시 (rank-1 prenex polymorphism)
function identity<T>(x: T): T { return x; }

identity<number>(42);      // 타입 적용 명시
identity("hello");          // 타입 추론 (HM 류 로컬 추론)

// compose : ∀A B C. (B→C) → (A→B) → A→C
const compose = <A, B, C>(f: (b: B) => C, g: (a: A) => B) =>
  (x: A): C => f(g(x));
```

**Curry-Howard 대응 (증명 = 프로그램)**: 타입 = 명제(proposition), 프로그램 = 증명(proof) 의 동형. `A → B` (함수 타입) = "A 이면 B" (함의), `(A, B)` (곱 타입) = "A 그리고 B" (논리곱), `Either A B` (합 타입) = "A 또는 B" (논리합), `∀α.τ` (System F) = "모든 α 에 대해" (전칭 양화). 프로그램이 *타입 검사를 통과* = 대응 명제가 *증명됨*. STLC ↔ 직관주의 명제 논리, System F ↔ 2차 직관주의 논리, 의존 타입 ↔ 1차/고차 술어 논리. 이 대응이 Coq/Agda/Lean 같은 *증명 보조기* 의 근간이다.

**관련 항목**:
- [hindley-milner](#4-hindley-milner) — HM 은 System F 의 *결정 가능한 단편*(rank-1 prenex). System F 전체 추론은 undecidable 이라 HM 으로 타협
- [adt](#5-adt) — sum/product 타입은 Curry-Howard 의 ∨/∧ 에 대응 (`Either` = ∨, tuple = ∧)
- [hkt](#7-hkt) — System Fω (kind 까지 양화한 확장) 가 HKT 의 이론적 기반
- [dependent-types](#9-dependent-types) — λΠ-calculus 는 System F 를 *값 의존* 으로 일반화, Curry-Howard 가 정점에 도달
- [effect-system](#10-effect-system) — 순수 λ-calculus 에 없는 부수효과를 monad/effect 로 보강
- [static-dynamic-typing](#1-static-dynamic-typing) — STLC 는 static 타이핑의 최소 형식 모델
- [`../patterns/functional.md`](../patterns/functional.md) — closure / partial application / currying 의 직접 구현
