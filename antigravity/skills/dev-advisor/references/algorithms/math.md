# 수학 알고리즘 (Math Algorithms)

수학적 연산과 수론 문제를 해결하는 알고리즘입니다.

**관련 카탈로그**:
- [`../patterns/hpc-scientific.md#blas-lapack-scalapack`](../patterns/hpc-scientific.md#blas-lapack-scalapack) — BLAS / LAPACK / ScaLAPACK (선형대수 라이브러리 — GEMM/LU/QR/SVD 의 HPC 표준 구현, 본 카테고리의 수치 알고리즘 운영 인터페이스)

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [euclidean-gcd](#euclidean-gcd) | Euclidean GCD | 유클리드 최대공약수 | 낮음 |
| [sieve-of-eratosthenes](#sieve-of-eratosthenes) | Sieve of Eratosthenes | 에라토스테네스의 체 | 낮음 |
| [fast-exponentiation](#fast-exponentiation) | Fast Exponentiation | 빠른 거듭제곱 | 낮음 |
| [modular-arithmetic](#modular-arithmetic) | Modular Arithmetic | 모듈러 연산 | 중간 |
| [chinese-remainder-theorem](#chinese-remainder-theorem) | Chinese Remainder Theorem | 중국인의 나머지 정리 | 높음 |
| [fast-fourier-transform](#fast-fourier-transform) | Fast Fourier Transform | 고속 푸리에 변환 | 높음 |
| [simpson-rule](#simpson-rule) | Simpson's Rule | 심슨 적분법 | 중간 |
| [newton-raphson](#newton-raphson) | Newton-Raphson | 뉴턴-랩슨 | 중간 |
| [prime-factorization](#prime-factorization) | Prime Factorization | 소인수분해 | 낮음 |
| [miller-rabin](#miller-rabin) | Miller-Rabin Primality Test | 밀러-라빈 소수 판정 | 높음 |
| [extended-euclidean](#extended-euclidean) | Extended Euclidean | 확장 유클리드 | 중간 |
| [lucas-theorem](#lucas-theorem) | Lucas Theorem | 뤼카 정리 | 높음 |
| [pollard-rho](#pollard-rho) | Pollard's Rho | 폴라드 로 인수분해 | 높음 |
| [linear-sieve](#linear-sieve) | Linear Sieve | 선형 소수 체 | 중간 |

---

<a id="euclidean-gcd"></a>
## 1. Euclidean GCD (유클리드 최대공약수)

**목적**: 두 수의 최대공약수 계산

**시간 복잡도**: O(log(min(a, b)))

**공간 복잡도**: O(1) 반복, O(log n) 재귀

**특징**:
- 가장 오래된 알고리즘 중 하나
- 나눗셈 기반

**장점**:
- 매우 효율적
- 구현 간단

**단점**:
- 큰 수에서 오버플로우 주의

**활용 예시**:
- 분수 약분
- 암호학 (RSA)
- 모듈러 역원

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 재귀 방식
fun gcd(a: Long, b: Long): Long {
    return if (b == 0L) a else gcd(b, a % b)
}

// 반복 방식
fun gcdIterative(a: Long, b: Long): Long {
    var x = a
    var y = b
    while (y != 0L) {
        val temp = y
        y = x % y
        x = temp
    }
    return x
}

// 최소공배수
fun lcm(a: Long, b: Long): Long {
    return a / gcd(a, b) * b
}

// 확장 유클리드 알고리즘 (ax + by = gcd(a, b))
fun extendedGcd(a: Long, b: Long): Triple<Long, Long, Long> {
    if (b == 0L) return Triple(a, 1L, 0L)

    val (g, x1, y1) = extendedGcd(b, a % b)
    val x = y1
    val y = x1 - (a / b) * y1

    return Triple(g, x, y)
}

// 모듈러 역원 (a * x ≡ 1 (mod m))
fun modInverse(a: Long, m: Long): Long? {
    val (g, x, _) = extendedGcd(a, m)
    if (g != 1L) return null // 역원 존재하지 않음
    return ((x % m) + m) % m
}

// 여러 수의 GCD
fun gcdMultiple(numbers: List<Long>): Long {
    return numbers.reduce { acc, n -> gcd(acc, n) }
}
```

**관련 알고리즘**: LCM, 확장 유클리드

---

<a id="sieve-of-eratosthenes"></a>
## 2. Sieve of Eratosthenes (에라토스테네스의 체)

**목적**: 특정 범위 내 모든 소수 찾기

**시간 복잡도**: O(n log log n)

**공간 복잡도**: O(n)

**특징**:
- 고대 그리스 알고리즘
- 배수 제거 방식

**장점**:
- 매우 효율적
- 구현 간단

**단점**:
- 메모리 사용량

**활용 예시**:
- 소수 목록 생성
- 소인수분해
- 암호학

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 기본 에라토스테네스의 체
fun sieveOfEratosthenes(n: Int): List<Int> {
    if (n < 2) return emptyList()

    val isPrime = BooleanArray(n + 1) { true }
    isPrime[0] = false
    isPrime[1] = false

    var i = 2
    while (i * i <= n) {
        if (isPrime[i]) {
            var j = i * i
            while (j <= n) {
                isPrime[j] = false
                j += i
            }
        }
        i++
    }

    return isPrime.indices.filter { isPrime[it] }
}

// 세그먼트 체 (큰 범위)
fun segmentedSieve(low: Long, high: Long): List<Long> {
    val limit = kotlin.math.sqrt(high.toDouble()).toLong() + 1
    val basePrimes = sieveOfEratosthenes(limit.toInt())

    val isPrime = BooleanArray((high - low + 1).toInt()) { true }

    for (prime in basePrimes) {
        val p = prime.toLong()
        var start = ((low + p - 1) / p) * p
        if (start == p) start += p

        var j = start
        while (j <= high) {
            isPrime[(j - low).toInt()] = false
            j += p
        }
    }

    if (low == 1L) isPrime[0] = false

    return isPrime.indices
        .filter { isPrime[it] }
        .map { it + low }
}

// 최소 소인수 저장 (빠른 소인수분해용)
fun sieveWithSpf(n: Int): IntArray {
    val spf = IntArray(n + 1) { it } // 최소 소인수

    var i = 2
    while (i * i <= n) {
        if (spf[i] == i) { // 소수
            var j = i * i
            while (j <= n) {
                if (spf[j] == j) spf[j] = i
                j += i
            }
        }
        i++
    }

    return spf
}

// SPF를 이용한 빠른 소인수분해
fun factorize(n: Int, spf: IntArray): List<Int> {
    val factors = mutableListOf<Int>()
    var num = n

    while (num > 1) {
        factors.add(spf[num])
        num /= spf[num]
    }

    return factors
}
```

**관련 알고리즘**: Miller-Rabin, 소인수분해

---

<a id="fast-exponentiation"></a>
## 3. Fast Exponentiation (빠른 거듭제곱)

**목적**: a^n을 효율적으로 계산

**시간 복잡도**: O(log n)

**공간 복잡도**: O(1) 반복, O(log n) 재귀

**특징**:
- 이진 분할
- 모듈러 연산 적용 가능

**장점**:
- 매우 빠름
- 큰 지수도 처리 가능

**단점**:
- 오버플로우 주의

**활용 예시**:
- 모듈러 거듭제곱
- 행렬 거듭제곱
- RSA 암호화

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 일반 거듭제곱
fun power(base: Long, exp: Long): Long {
    var result = 1L
    var b = base
    var e = exp

    while (e > 0) {
        if (e and 1L == 1L) {
            result *= b
        }
        b *= b
        e = e shr 1
    }

    return result
}

// 모듈러 거듭제곱
fun modPow(base: Long, exp: Long, mod: Long): Long {
    var result = 1L
    var b = base % mod
    var e = exp

    while (e > 0) {
        if (e and 1L == 1L) {
            result = (result * b) % mod
        }
        b = (b * b) % mod
        e = e shr 1
    }

    return result
}

// 재귀 방식
fun modPowRecursive(base: Long, exp: Long, mod: Long): Long {
    if (exp == 0L) return 1L

    val half = modPowRecursive(base, exp / 2, mod)
    val halfSquared = (half * half) % mod

    return if (exp % 2 == 0L) {
        halfSquared
    } else {
        (halfSquared * (base % mod)) % mod
    }
}

// 행렬 거듭제곱
typealias Matrix = Array<LongArray>

fun matrixMultiply(a: Matrix, b: Matrix, mod: Long): Matrix {
    val n = a.size
    val result = Array(n) { LongArray(n) }

    for (i in 0 until n) {
        for (j in 0 until n) {
            for (k in 0 until n) {
                result[i][j] = (result[i][j] + a[i][k] * b[k][j]) % mod
            }
        }
    }

    return result
}

fun matrixPow(matrix: Matrix, exp: Long, mod: Long): Matrix {
    val n = matrix.size
    var result = Array(n) { i -> LongArray(n) { j -> if (i == j) 1L else 0L } }
    var base = matrix
    var e = exp

    while (e > 0) {
        if (e and 1L == 1L) {
            result = matrixMultiply(result, base, mod)
        }
        base = matrixMultiply(base, base, mod)
        e = e shr 1
    }

    return result
}
```

**관련 알고리즘**: 피보나치 (행렬), 모듈러 역원

---

<a id="modular-arithmetic"></a>
## 4. Modular Arithmetic (모듈러 연산)

**목적**: 나머지 연산 기반 계산

**시간 복잡도**: 연산에 따라 다름

**공간 복잡도**: O(1)

**특징**:
- 오버플로우 방지
- 암호학 기반

**장점**:
- 큰 수 처리 가능
- 사이클 성질 활용

**단점**:
- 나눗셈 직접 불가

**활용 예시**:
- 조합론
- 암호학
- 해싱

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
class ModularArithmetic(private val mod: Long) {

    fun add(a: Long, b: Long): Long = ((a % mod) + (b % mod)) % mod

    fun subtract(a: Long, b: Long): Long = ((a % mod) - (b % mod) + mod) % mod

    fun multiply(a: Long, b: Long): Long = ((a % mod) * (b % mod)) % mod

    // 페르마의 소정리: a^(p-1) ≡ 1 (mod p) → a^(-1) ≡ a^(p-2)
    fun inverse(a: Long): Long = modPow(a, mod - 2, mod)

    fun divide(a: Long, b: Long): Long = multiply(a, inverse(b))

    // nCr mod p
    fun combination(n: Int, r: Int): Long {
        if (r > n) return 0L
        if (r == 0 || r == n) return 1L

        val numerator = factorial(n)
        val denominator = multiply(factorial(r), factorial(n - r))
        return divide(numerator, denominator)
    }

    private val factorialCache = mutableMapOf<Int, Long>()

    fun factorial(n: Int): Long {
        if (n <= 1) return 1L
        return factorialCache.getOrPut(n) {
            multiply(n.toLong(), factorial(n - 1))
        }
    }

    // nCr 테이블 (Pascal's triangle)
    fun buildCombinationTable(maxN: Int): Array<LongArray> {
        val C = Array(maxN + 1) { LongArray(maxN + 1) }

        for (n in 0..maxN) {
            C[n][0] = 1
            for (r in 1..n) {
                C[n][r] = add(C[n - 1][r - 1], C[n - 1][r])
            }
        }

        return C
    }
}

// 뤼카 정리 (큰 n, r에 대한 nCr mod p)
fun lucasTheorem(n: Long, r: Long, p: Long): Long {
    if (r == 0L) return 1L
    return (lucasTheorem(n / p, r / p, p) *
            smallCombination((n % p).toInt(), (r % p).toInt(), p)) % p
}

private fun smallCombination(n: Int, r: Int, p: Long): Long {
    if (r > n) return 0L
    if (r == 0 || r == n) return 1L

    var num = 1L
    var den = 1L

    for (i in 0 until r) {
        num = (num * (n - i)) % p
        den = (den * (i + 1)) % p
    }

    return (num * modPow(den, p - 2, p)) % p
}
```

**관련 알고리즘**: 빠른 거듭제곱, 페르마 소정리

---

<a id="chinese-remainder-theorem"></a>
## 5. Chinese Remainder Theorem (중국인의 나머지 정리)

**목적**: 연립 합동식의 해 찾기

**시간 복잡도**: O(n log M)

**공간 복잡도**: O(n)

**특징**:
- 서로소인 모듈러들 필요
- 유일한 해 존재

**장점**:
- 큰 모듈러 연산 분해
- 병렬 계산 가능

**단점**:
- 서로소 조건 필요

**활용 예시**:
- RSA 최적화
- 큰 수 연산
- 스케줄링

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// x ≡ a_i (mod m_i) 시스템 풀기
fun chineseRemainderTheorem(
    remainders: List<Long>,
    moduli: List<Long>
): Long {
    val M = moduli.reduce { acc, m -> acc * m }
    var result = 0L

    for (i in remainders.indices) {
        val Mi = M / moduli[i]
        val yi = modInverse(Mi, moduli[i])!!

        result += remainders[i] * Mi * yi
        result %= M
    }

    return (result + M) % M
}

// 확장 CRT (서로소가 아닐 수도 있음)
fun extendedCRT(
    a1: Long, m1: Long,
    a2: Long, m2: Long
): Pair<Long, Long>? {
    val (g, p, _) = extendedGcd(m1, m2)

    if ((a2 - a1) % g != 0L) return null // 해 없음

    val lcm = m1 / g * m2
    val diff = ((a2 - a1) / g * p % (m2 / g) + m2 / g) % (m2 / g)
    val x = (a1 + m1 * diff) % lcm

    return (x + lcm) % lcm to lcm
}

// 여러 합동식에 대한 확장 CRT
fun solveCongruences(
    remainders: List<Long>,
    moduli: List<Long>
): Pair<Long, Long>? {
    if (remainders.isEmpty()) return null

    var result = remainders[0] to moduli[0]

    for (i in 1 until remainders.size) {
        result = extendedCRT(
            result.first, result.second,
            remainders[i], moduli[i]
        ) ?: return null
    }

    return result
}
```

**관련 알고리즘**: 확장 유클리드, 모듈러 역원

---

<a id="fast-fourier-transform"></a>
## 6. Fast Fourier Transform (고속 푸리에 변환)

**목적**: 다항식 곱셈, 신호 처리

**시간 복잡도**: O(n log n)

**공간 복잡도**: O(n)

**특징**:
- 분할 정복
- 복소수 연산

**장점**:
- 매우 빠른 다항식 곱셈
- 신호 처리에 필수

**단점**:
- 구현 복잡
- 부동소수점 오차

**활용 예시**:
- 다항식 곱셈
- 큰 수 곱셈
- 오디오 처리

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

data class Complex(val re: Double, val im: Double) {
    operator fun plus(other: Complex) = Complex(re + other.re, im + other.im)
    operator fun minus(other: Complex) = Complex(re - other.re, im - other.im)
    operator fun times(other: Complex) = Complex(
        re * other.re - im * other.im,
        re * other.im + im * other.re
    )
}

fun fft(a: List<Complex>, invert: Boolean = false): List<Complex> {
    val n = a.size
    if (n == 1) return a

    val a0 = a.filterIndexed { i, _ -> i % 2 == 0 }
    val a1 = a.filterIndexed { i, _ -> i % 2 == 1 }

    val y0 = fft(a0, invert)
    val y1 = fft(a1, invert)

    val angle = 2 * PI / n * (if (invert) -1 else 1)
    var w = Complex(1.0, 0.0)
    val wn = Complex(cos(angle), sin(angle))

    val y = MutableList(n) { Complex(0.0, 0.0) }

    for (k in 0 until n / 2) {
        val t = w * y1[k]
        y[k] = y0[k] + t
        y[k + n / 2] = y0[k] - t
        w = w * wn
    }

    return if (invert) y.map { Complex(it.re / 2, it.im / 2) } else y
}

// 다항식 곱셈
fun multiplyPolynomials(a: List<Long>, b: List<Long>): List<Long> {
    var n = 1
    while (n < a.size + b.size) n *= 2

    val fa = a.map { Complex(it.toDouble(), 0.0) } +
             List(n - a.size) { Complex(0.0, 0.0) }
    val fb = b.map { Complex(it.toDouble(), 0.0) } +
             List(n - b.size) { Complex(0.0, 0.0) }

    val ya = fft(fa)
    val yb = fft(fb)

    val yc = ya.zip(yb) { x, y -> x * y }
    val c = fft(yc, true)

    return c.take(a.size + b.size - 1).map { (it.re + 0.5).toLong() }
}

// NTT (Number Theoretic Transform) - 정수 연산
fun ntt(a: LongArray, invert: Boolean, mod: Long, g: Long): LongArray {
    val n = a.size
    if (n == 1) return a

    var j = 0
    for (i in 1 until n) {
        var bit = n shr 1
        while (j and bit != 0) {
            j = j xor bit
            bit = bit shr 1
        }
        j = j or bit
        if (i < j) {
            val temp = a[i]
            a[i] = a[j]
            a[j] = temp
        }
    }

    var len = 2
    while (len <= n) {
        val w = if (invert) {
            modPow(g, (mod - 1) / len, mod)
        } else {
            modPow(modPow(g, (mod - 1) / len, mod), mod - 2, mod)
        }

        var i = 0
        while (i < n) {
            var wn = 1L
            for (jj in 0 until len / 2) {
                val u = a[i + jj]
                val v = a[i + jj + len / 2] * wn % mod
                a[i + jj] = (u + v) % mod
                a[i + jj + len / 2] = (u - v + mod) % mod
                wn = wn * w % mod
            }
            i += len
        }
        len *= 2
    }

    if (invert) {
        val nInv = modPow(n.toLong(), mod - 2, mod)
        for (i in 0 until n) {
            a[i] = a[i] * nInv % mod
        }
    }

    return a
}
```

**관련 알고리즘**: Karatsuba, NTT

---

<a id="simpson-rule"></a>
## 7. Simpson's Rule (심슨 적분법)

**목적**: 정적분 수치 계산

**시간 복잡도**: O(n)

**공간 복잡도**: O(1)

**특징**:
- 포물선 근사
- 고정밀도

**장점**:
- 높은 정확도
- 구현 간단

**단점**:
- 함수 연속성 필요

**활용 예시**:
- 면적 계산
- 물리 시뮬레이션
- 기하 문제

**난이도**: 중간 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// 기본 심슨 규칙
fun simpsonRule(f: (Double) -> Double, a: Double, b: Double, n: Int): Double {
    require(n % 2 == 0) { "n must be even" }

    val h = (b - a) / n
    var sum = f(a) + f(b)

    for (i in 1 until n) {
        val x = a + i * h
        sum += if (i % 2 == 0) 2 * f(x) else 4 * f(x)
    }

    return sum * h / 3
}

// 적응형 심슨 (Adaptive Simpson)
fun adaptiveSimpson(
    f: (Double) -> Double,
    a: Double,
    b: Double,
    eps: Double = 1e-10
): Double {
    val m = (a + b) / 2
    val s1 = simpson(f, a, b)
    val s2 = simpson(f, a, m) + simpson(f, m, b)

    return if (kotlin.math.abs(s2 - s1) < 15 * eps) {
        s2 + (s2 - s1) / 15
    } else {
        adaptiveSimpson(f, a, m, eps / 2) + adaptiveSimpson(f, m, b, eps / 2)
    }
}

private fun simpson(f: (Double) -> Double, a: Double, b: Double): Double {
    val m = (a + b) / 2
    return (b - a) / 6 * (f(a) + 4 * f(m) + f(b))
}
```

**관련 알고리즘**: 사다리꼴 규칙, 몬테카를로 적분

---

<a id="newton-raphson"></a>
## 8. Newton-Raphson (뉴턴-랩슨)

**목적**: 방정식의 근 찾기

**시간 복잡도**: O(log n) 수렴 시

**공간 복잡도**: O(1)

**특징**:
- 접선 이용
- 이차 수렴

**장점**:
- 빠른 수렴
- 높은 정밀도

**단점**:
- 초기값 의존
- 발산 가능

**활용 예시**:
- 제곱근 계산
- 최적화
- 수치 해석

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 일반 뉴턴-랩슨
fun newtonRaphson(
    f: (Double) -> Double,
    df: (Double) -> Double,
    x0: Double,
    eps: Double = 1e-10,
    maxIter: Int = 100
): Double? {
    var x = x0

    repeat(maxIter) {
        val fx = f(x)
        if (kotlin.math.abs(fx) < eps) return x

        val dfx = df(x)
        if (kotlin.math.abs(dfx) < eps) return null // 기울기가 0

        x = x - fx / dfx
    }

    return null // 수렴 실패
}

// 제곱근 계산
fun sqrt(n: Double, eps: Double = 1e-10): Double {
    if (n < 0) throw IllegalArgumentException("Negative number")
    if (n == 0.0) return 0.0

    var x = n
    while (kotlin.math.abs(x * x - n) > eps) {
        x = (x + n / x) / 2
    }
    return x
}

// 정수 제곱근 (이진 탐색)
fun intSqrt(n: Long): Long {
    if (n < 0) throw IllegalArgumentException()
    if (n < 2) return n

    var low = 1L
    var high = n / 2

    while (low <= high) {
        val mid = low + (high - low) / 2
        val sq = mid * mid

        when {
            sq == n -> return mid
            sq < n -> low = mid + 1
            else -> high = mid - 1
        }
    }

    return high
}

// n차 근 계산
fun nthRoot(n: Double, k: Int, eps: Double = 1e-10): Double {
    var x = n / k // 초기 추정

    repeat(100) {
        val xNew = ((k - 1) * x + n / kotlin.math.pow(x, (k - 1).toDouble())) / k
        if (kotlin.math.abs(xNew - x) < eps) return xNew
        x = xNew
    }

    return x
}
```

**관련 알고리즘**: 이분법, 할선법

---

<a id="prime-factorization"></a>
## 9. Prime Factorization (소인수분해)

**목적**: 정수를 소수의 곱으로 분해

**시간 복잡도**: O(√n)

**공간 복잡도**: O(log n)

**특징**:
- 기본적 수론 연산
- 암호학 기반

**장점**:
- 직관적 구현
- 다양한 응용

**단점**:
- 큰 수에서 느림

**활용 예시**:
- RSA 암호
- GCD/LCM 계산
- 약수 개수

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 기본 소인수분해
fun primeFactors(n: Long): Map<Long, Int> {
    val factors = mutableMapOf<Long, Int>()
    var num = n

    // 2로 나누기
    while (num % 2 == 0L) {
        factors[2] = factors.getOrDefault(2, 0) + 1
        num /= 2
    }

    // 홀수로 나누기
    var i = 3L
    while (i * i <= num) {
        while (num % i == 0L) {
            factors[i] = factors.getOrDefault(i, 0) + 1
            num /= i
        }
        i += 2
    }

    // 남은 수가 소수인 경우
    if (num > 1) {
        factors[num] = 1
    }

    return factors
}

// 소인수 리스트 (중복 포함)
fun primeFactorsList(n: Long): List<Long> {
    val factors = mutableListOf<Long>()
    var num = n

    var d = 2L
    while (d * d <= num) {
        while (num % d == 0L) {
            factors.add(d)
            num /= d
        }
        d++
    }

    if (num > 1) factors.add(num)

    return factors
}

// 약수 개수 (소인수분해 이용)
fun countDivisors(n: Long): Int {
    val factors = primeFactors(n)
    return factors.values.fold(1) { acc, exp -> acc * (exp + 1) }
}

// 약수 합
fun sumDivisors(n: Long): Long {
    val factors = primeFactors(n)
    var sum = 1L

    for ((p, e) in factors) {
        // p^0 + p^1 + ... + p^e = (p^(e+1) - 1) / (p - 1)
        var term = 0L
        var power = 1L
        repeat(e + 1) {
            term += power
            power *= p
        }
        sum *= term
    }

    return sum
}

// 모든 약수 생성
fun allDivisors(n: Long): List<Long> {
    val factors = primeFactors(n)
    val primes = factors.keys.toList()
    val exponents = factors.values.toList()
    val divisors = mutableListOf<Long>()

    fun generate(index: Int, current: Long) {
        if (index == primes.size) {
            divisors.add(current)
            return
        }

        var power = 1L
        for (e in 0..exponents[index]) {
            generate(index + 1, current * power)
            power *= primes[index]
        }
    }

    generate(0, 1)
    return divisors.sorted()
}
```

**관련 알고리즘**: 에라토스테네스의 체, Pollard's Rho

---

<a id="miller-rabin"></a>
## 10. Miller-Rabin Primality Test (밀러-라빈 소수 판정)

**목적**: 큰 수의 소수 여부 확률적 판정

**시간 복잡도**: O(k log³ n)

**공간 복잡도**: O(1)

**특징**:
- 확률적 알고리즘
- 결정적 변형 가능

**장점**:
- 매우 빠름
- 큰 수 처리 가능

**단점**:
- 확률적 (오류 가능)

**활용 예시**:
- RSA 키 생성
- 소수 생성
- 암호학

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.math.BigInteger
import java.util.Random

// 밀러-라빈 소수 판정
fun millerRabin(n: Long, k: Int = 10): Boolean {
    if (n < 2) return false
    if (n == 2L || n == 3L) return true
    if (n % 2 == 0L) return false

    // n - 1 = 2^r * d
    var d = n - 1
    var r = 0
    while (d % 2 == 0L) {
        d /= 2
        r++
    }

    val random = Random()

    repeat(k) {
        val a = 2 + (random.nextLong().let {
            if (it < 0) -it else it
        } % (n - 3))

        var x = modPow(a, d, n)

        if (x == 1L || x == n - 1) return@repeat

        var composite = true
        repeat(r - 1) {
            x = modPow(x, 2, n)
            if (x == n - 1) {
                composite = false
                return@repeat
            }
        }

        if (composite) return false
    }

    return true
}

// 결정적 밀러-라빈 (특정 witness 사용)
fun millerRabinDeterministic(n: Long): Boolean {
    if (n < 2) return false
    if (n == 2L || n == 3L) return true
    if (n % 2 == 0L) return false

    var d = n - 1
    var r = 0
    while (d % 2 == 0L) {
        d /= 2
        r++
    }

    // 64비트 정수에 대해 충분한 witness
    val witnesses = longArrayOf(2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)

    for (a in witnesses) {
        if (a >= n) continue

        var x = modPow(a, d, n)
        if (x == 1L || x == n - 1) continue

        var composite = true
        repeat(r - 1) {
            x = modPow(x, 2, n)
            if (x == n - 1) {
                composite = false
                return@repeat
            }
        }

        if (composite) return false
    }

    return true
}

// BigInteger 버전
fun millerRabinBig(n: BigInteger, k: Int = 10): Boolean {
    if (n < BigInteger.TWO) return false
    if (n == BigInteger.TWO) return true
    if (n.mod(BigInteger.TWO) == BigInteger.ZERO) return false

    var d = n - BigInteger.ONE
    var r = 0
    while (d.mod(BigInteger.TWO) == BigInteger.ZERO) {
        d = d.divide(BigInteger.TWO)
        r++
    }

    val random = Random()

    repeat(k) {
        val a = BigInteger(n.bitLength() - 1, random) + BigInteger.TWO

        var x = a.modPow(d, n)
        if (x == BigInteger.ONE || x == n - BigInteger.ONE) return@repeat

        var composite = true
        repeat(r - 1) {
            x = x.modPow(BigInteger.TWO, n)
            if (x == n - BigInteger.ONE) {
                composite = false
                return@repeat
            }
        }

        if (composite) return false
    }

    return true
}
```

**관련 알고리즘**: 페르마 소수 판정, AKS

---

<a id="extended-euclidean"></a>
## 11. Extended Euclidean (확장 유클리드)

**목적**: gcd(a, b)와 함께 ax + by = gcd(a, b)를 만족하는 (x, y) 동시 계산

**시간 복잡도**: O(log(min(a, b)))

**공간 복잡도**: O(log(min(a, b))) - 재귀

**특징**:
- 베주(Bezout) 항등식: ax + by = gcd
- 모듈러 역원 계산의 핵심
- 음수 계수 가능

**장점**:
- 모듈러 역원 일반화 (소수 아닌 모듈러도 동작)
- 디오판토스 방정식 해법

**단점**:
- 큰 수에서 오버플로우 주의 (Long 권장)
- 음수 정규화 필요

**활용 예시**:
- 모듈러 역원
- 디오판토스 방정식
- 중국인의 나머지 정리 (CRT)
- RSA 키 생성 (d = e⁻¹ mod φ)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// (gcd, x, y) 반환: a*x + b*y = gcd(a, b)
fun extGcd(a: Long, b: Long): Triple<Long, Long, Long> {
    if (b == 0L) return Triple(a, 1L, 0L)
    val (g, x1, y1) = extGcd(b, a % b)
    return Triple(g, y1, x1 - (a / b) * y1)
}

// 반복 버전 (스택 안전)
fun extGcdIter(a: Long, b: Long): Triple<Long, Long, Long> {
    var oldR = a; var r = b
    var oldS = 1L; var s = 0L
    var oldT = 0L; var t = 1L
    while (r != 0L) {
        val q = oldR / r
        val tmpR = r; r = oldR - q * r; oldR = tmpR
        val tmpS = s; s = oldS - q * s; oldS = tmpS
        val tmpT = t; t = oldT - q * t; oldT = tmpT
    }
    return Triple(oldR, oldS, oldT)
}

// 모듈러 역원 (m이 소수가 아니어도 gcd(a, m) = 1이면 동작)
fun modInverseExt(a: Long, m: Long): Long? {
    val (g, x, _) = extGcd(((a % m) + m) % m, m)
    if (g != 1L) return null
    return ((x % m) + m) % m
}

// 디오판토스 방정식 ax + by = c
fun solveDiophantine(a: Long, b: Long, c: Long): Triple<Long, Long, Long>? {
    val (g, x0, y0) = extGcd(a, b)
    if (c % g != 0L) return null
    val factor = c / g
    return Triple(g, x0 * factor, y0 * factor)
}
```

**관련 알고리즘**: Euclidean GCD, CRT, 모듈러 역원

---

<a id="lucas-theorem"></a>
## 12. Lucas Theorem (뤼카 정리)

**목적**: 큰 n, r에 대해 nCr mod p를 p의 자릿수 단위로 분해해 계산 (p는 소수)

**시간 복잡도**: O(p + log_p n)

**공간 복잡도**: O(p) 팩토리얼 캐시

**특징**:
- nCr mod p = ∏ (nᵢCrᵢ) mod p, n = Σ nᵢ p^i
- 각 자릿수 단위로 작은 조합 계산
- p가 소수일 때만

**장점**:
- 매우 큰 n (10^18)도 처리
- 페르마로 작은 nCr 빠르게

**단점**:
- p가 소수여야 함
- p가 크면 팩토리얼 캐시 메모리

**활용 예시**:
- 조합론 mod 소수
- 격자 경로 수 mod 소수
- 동적 계획에서 빈번한 nCr

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class LucasCalculator(private val p: Long) {
    private val fact: LongArray = LongArray(p.toInt())

    init {
        fact[0] = 1L
        for (i in 1 until p.toInt()) {
            fact[i] = fact[i - 1] * i % p
        }
    }

    private fun smallC(n: Int, r: Int): Long {
        if (r > n) return 0L
        // nCr = n! / (r! * (n-r)!) mod p
        // 페르마 소정리로 역원
        val denom = fact[r] * fact[n - r] % p
        return fact[n] * modPow(denom, p - 2, p) % p
    }

    fun lucas(n: Long, r: Long): Long {
        if (r == 0L) return 1L
        return smallC((n % p).toInt(), (r % p).toInt()) * lucas(n / p, r / p) % p
    }
}
```

**관련 알고리즘**: Chinese Remainder Theorem, Granville Formulas

---

<a id="pollard-rho"></a>
## 13. Pollard's Rho (폴라드 로 인수분해)

**목적**: 큰 합성수의 인수분해를 확률적으로 O(n^(1/4))에 수행

**시간 복잡도**: O(n^(1/4)) 기대값

**공간 복잡도**: O(1)

**특징**:
- f(x) = x² + c (mod n) 사이클 찾기
- Floyd's tortoise-and-hare 또는 Brent 변형
- Miller-Rabin과 결합하여 완전 분해

**장점**:
- 시행 분할(trial division)보다 훨씬 빠름
- 50비트 이상 합성수도 처리

**단점**:
- 확률적, 재시도 필요
- 매우 큰 소수의 곱(RSA 모듈러)은 여전히 불가

**활용 예시**:
- 정수 인수분해 (수십~수백 비트)
- 암호학 분석
- 수론 경쟁 프로그래밍

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.math.BigInteger

object PollardRho {
    private fun mulMod(a: Long, b: Long, mod: Long): Long {
        // 오버플로우 방지 (BigInteger 또는 Math.floorMod 활용)
        return (BigInteger.valueOf(a) * BigInteger.valueOf(b))
            .mod(BigInteger.valueOf(mod)).toLong()
    }

    private fun gcd(a: Long, b: Long): Long = if (b == 0L) a else gcd(b, a % b)

    fun rho(n: Long): Long {
        if (n % 2L == 0L) return 2L
        val rng = java.util.Random()
        while (true) {
            var x = (rng.nextLong() % (n - 2) + 2) and Long.MAX_VALUE
            var y = x
            val c = (rng.nextLong() % (n - 1) + 1) and Long.MAX_VALUE
            var d = 1L
            while (d == 1L) {
                x = (mulMod(x, x, n) + c) % n
                y = (mulMod(y, y, n) + c) % n
                y = (mulMod(y, y, n) + c) % n
                d = gcd(if (x > y) x - y else y - x, n)
            }
            if (d != n) return d
        }
    }

    fun factor(n: Long, result: MutableList<Long> = mutableListOf()): List<Long> {
        if (n == 1L) return result
        if (millerRabinDeterministic(n)) {
            result.add(n); return result
        }
        var d = n
        while (d == n) d = rho(n)
        factor(d, result)
        factor(n / d, result)
        return result
    }
}
```

**관련 알고리즘**: Miller-Rabin, Quadratic Sieve, ECM

---

<a id="linear-sieve"></a>
## 14. Linear Sieve (선형 소수 체)

**목적**: 1..n의 모든 소수 + 최소 소인수(SPF)를 O(n)에 계산

**시간 복잡도**: O(n)

**공간 복잡도**: O(n)

**특징**:
- 각 합성수가 최소 소인수에 의해 정확히 한 번 표시됨
- Eratosthenes의 O(n log log n)을 O(n)으로 개선
- 곱셈적 함수(φ, μ 등) 동시 계산 가능

**장점**:
- 진정한 선형 시간
- SPF 부산물로 빠른 인수분해
- 곱셈적 함수 계산에 이상적

**단점**:
- 일반 Eratosthenes보다 약간 느린 상수
- 메모리 약간 더 사용

**활용 예시**:
- 대량 소수 + SPF 동시 생성
- 오일러 함수, 뫼비우스 함수 일괄 계산
- 수론 경쟁 프로그래밍

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
data class LinearSieveResult(val primes: List<Int>, val spf: IntArray)

fun linearSieve(n: Int): LinearSieveResult {
    val spf = IntArray(n + 1)
    val primes = mutableListOf<Int>()
    for (i in 2..n) {
        if (spf[i] == 0) {
            spf[i] = i
            primes.add(i)
        }
        for (p in primes) {
            if (p > spf[i] || i.toLong() * p > n) break
            spf[i * p] = p
        }
    }
    return LinearSieveResult(primes, spf)
}

// 오일러 함수 phi(i)를 동시에 계산
fun linearSieveWithPhi(n: Int): Pair<List<Int>, IntArray> {
    val spf = IntArray(n + 1)
    val phi = IntArray(n + 1)
    phi[1] = 1
    val primes = mutableListOf<Int>()
    for (i in 2..n) {
        if (spf[i] == 0) {
            spf[i] = i
            phi[i] = i - 1
            primes.add(i)
        }
        for (p in primes) {
            if (p > spf[i] || i.toLong() * p > n) break
            val idx = i * p
            spf[idx] = p
            phi[idx] = if (i % p == 0) phi[i] * p else phi[i] * (p - 1)
        }
    }
    return primes to phi
}
```

**관련 알고리즘**: Sieve of Eratosthenes, Euler's Totient

