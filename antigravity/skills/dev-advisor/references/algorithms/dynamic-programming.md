# 동적 프로그래밍 (Dynamic Programming)

복잡한 문제를 작은 부분 문제로 나누어 해결하고, 그 결과를 저장하여 재사용하는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [fibonacci](#fibonacci) | Fibonacci | 피보나치 | 낮음 |
| [lcs](#lcs) | LCS (Longest Common Subsequence) | 최장 공통 부분 수열 | 중간 |
| [lis](#lis) | LIS (Longest Increasing Subsequence) | 최장 증가 부분 수열 | 중간 |
| [knapsack](#knapsack) | Knapsack | 배낭 문제 | 중간 |
| [edit-distance](#edit-distance) | Edit Distance | 편집 거리 (Levenshtein Distance) | 중간 |
| [matrix-chain-multiplication](#matrix-chain-multiplication) | Matrix Chain Multiplication | 행렬 체인 곱셈 | 높음 |
| [coin-change](#coin-change) | Coin Change | 동전 교환 | 중간 |
| [rod-cutting](#rod-cutting) | Rod Cutting | 막대 자르기 | 중간 |
| [bitmask-dp](#bitmask-dp) | Bitmask DP | 비트마스크 DP | 높음 |
| [tree-dp](#tree-dp) | Tree DP | 트리 DP | 중간 |
| [digit-dp](#digit-dp) | Digit DP | 자릿수 DP | 높음 |
| [sos-dp](#sos-dp) | SOS DP (Sum over Subsets) | 부분집합 합 | 높음 |
| [dp-optimizations](#dp-optimizations) | DP Optimizations (Convex Hull Trick / Knuth / D&C DP) | DP 최적화 기법 | 높음 |

---

<a id="fibonacci"></a>
## 1. Fibonacci (피보나치)

**목적**: 피보나치 수열의 n번째 값 계산

**시간 복잡도**: O(n)

**공간 복잡도**: O(n) 메모이제이션, O(1) 반복

**특징**:
- DP의 가장 기본적인 예시
- 메모이제이션 또는 타뷸레이션
- 중복 계산 제거

**장점**:
- 지수 시간을 선형 시간으로 개선
- 이해하기 쉬운 DP 입문

**단점**:
- 단순한 문제에서는 오버헤드

**활용 예시**:
- 피보나치 수열
- 계단 오르기 문제

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 메모이제이션 (Top-Down)
fun fibMemo(n: Int, memo: MutableMap<Int, Long> = mutableMapOf()): Long {
    if (n <= 1) return n.toLong()
    if (n in memo) return memo[n]!!

    memo[n] = fibMemo(n - 1, memo) + fibMemo(n - 2, memo)
    return memo[n]!!
}

// 타뷸레이션 (Bottom-Up)
fun fibTabulation(n: Int): Long {
    if (n <= 1) return n.toLong()

    val dp = LongArray(n + 1)
    dp[0] = 0
    dp[1] = 1

    for (i in 2..n) {
        dp[i] = dp[i - 1] + dp[i - 2]
    }

    return dp[n]
}

// 공간 최적화 O(1)
fun fibOptimized(n: Int): Long {
    if (n <= 1) return n.toLong()

    var prev2 = 0L
    var prev1 = 1L

    for (i in 2..n) {
        val current = prev1 + prev2
        prev2 = prev1
        prev1 = current
    }

    return prev1
}

// 행렬 거듭제곱 O(log n)
fun fibMatrix(n: Int): Long {
    if (n <= 1) return n.toLong()

    fun multiply(a: Array<LongArray>, b: Array<LongArray>): Array<LongArray> {
        return arrayOf(
            longArrayOf(
                a[0][0] * b[0][0] + a[0][1] * b[1][0],
                a[0][0] * b[0][1] + a[0][1] * b[1][1]
            ),
            longArrayOf(
                a[1][0] * b[0][0] + a[1][1] * b[1][0],
                a[1][0] * b[0][1] + a[1][1] * b[1][1]
            )
        )
    }

    fun power(matrix: Array<LongArray>, p: Int): Array<LongArray> {
        if (p == 1) return matrix
        if (p % 2 == 0) {
            val half = power(matrix, p / 2)
            return multiply(half, half)
        }
        return multiply(matrix, power(matrix, p - 1))
    }

    val base = arrayOf(longArrayOf(1, 1), longArrayOf(1, 0))
    val result = power(base, n)
    return result[0][1]
}
```

**관련 알고리즘**: LIS, LCS

---

<a id="lcs"></a>
## 2. LCS (Longest Common Subsequence, 최장 공통 부분 수열)

**목적**: 두 문자열의 가장 긴 공통 부분 수열 찾기

**시간 복잡도**: O(mn)

**공간 복잡도**: O(mn), 최적화 시 O(min(m, n))

**특징**:
- 부분 수열은 연속일 필요 없음
- 2차원 DP 테이블

**장점**:
- 문자열 비교에 효과적
- diff 도구의 기반

**단점**:
- 긴 문자열에서 메모리 사용량

**활용 예시**:
- diff 도구 (Git)
- DNA 서열 비교
- 파일 비교

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// LCS 길이
fun lcsLength(s1: String, s2: String): Int {
    val m = s1.length
    val n = s2.length
    val dp = Array(m + 1) { IntArray(n + 1) }

    for (i in 1..m) {
        for (j in 1..n) {
            if (s1[i - 1] == s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1
            } else {
                dp[i][j] = maxOf(dp[i - 1][j], dp[i][j - 1])
            }
        }
    }

    return dp[m][n]
}

// LCS 문자열 복원
fun lcs(s1: String, s2: String): String {
    val m = s1.length
    val n = s2.length
    val dp = Array(m + 1) { IntArray(n + 1) }

    for (i in 1..m) {
        for (j in 1..n) {
            if (s1[i - 1] == s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1
            } else {
                dp[i][j] = maxOf(dp[i - 1][j], dp[i][j - 1])
            }
        }
    }

    // 역추적으로 LCS 복원
    val result = StringBuilder()
    var i = m
    var j = n

    while (i > 0 && j > 0) {
        when {
            s1[i - 1] == s2[j - 1] -> {
                result.append(s1[i - 1])
                i--
                j--
            }
            dp[i - 1][j] > dp[i][j - 1] -> i--
            else -> j--
        }
    }

    return result.reverse().toString()
}

// 공간 최적화 (길이만)
fun lcsLengthOptimized(s1: String, s2: String): Int {
    val m = s1.length
    val n = s2.length
    var prev = IntArray(n + 1)
    var curr = IntArray(n + 1)

    for (i in 1..m) {
        for (j in 1..n) {
            if (s1[i - 1] == s2[j - 1]) {
                curr[j] = prev[j - 1] + 1
            } else {
                curr[j] = maxOf(prev[j], curr[j - 1])
            }
        }
        val temp = prev
        prev = curr
        curr = temp
        curr.fill(0)
    }

    return prev[n]
}
```

**관련 알고리즘**: LIS, Edit Distance

---

<a id="lis"></a>
## 3. LIS (Longest Increasing Subsequence, 최장 증가 부분 수열)

**목적**: 가장 긴 증가하는 부분 수열 찾기

**시간 복잡도**: O(n²) 또는 O(n log n)

**공간 복잡도**: O(n)

**특징**:
- 부분 수열은 연속일 필요 없음
- 이진 탐색으로 최적화 가능

**장점**:
- O(n log n) 최적화 가능
- 다양한 문제에 응용

**단점**:
- O(n²) 기본 구현은 느림

**활용 예시**:
- 주식 투자 전략
- 박스 쌓기 문제
- 최적 스케줄링

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// O(n²) 기본 구현
fun lisBasic(arr: IntArray): Int {
    val n = arr.size
    if (n == 0) return 0

    val dp = IntArray(n) { 1 }

    for (i in 1 until n) {
        for (j in 0 until i) {
            if (arr[j] < arr[i]) {
                dp[i] = maxOf(dp[i], dp[j] + 1)
            }
        }
    }

    return dp.max()
}

// O(n log n) 이진 탐색 최적화
fun lis(arr: IntArray): Int {
    val n = arr.size
    if (n == 0) return 0

    val tails = mutableListOf<Int>()

    for (num in arr) {
        val pos = tails.binarySearch(num).let {
            if (it < 0) -(it + 1) else it
        }

        if (pos == tails.size) {
            tails.add(num)
        } else {
            tails[pos] = num
        }
    }

    return tails.size
}

// LIS 실제 수열 복원
fun lisWithSequence(arr: IntArray): List<Int> {
    val n = arr.size
    if (n == 0) return emptyList()

    val tails = mutableListOf<Int>()
    val indices = mutableListOf<Int>()
    val prev = IntArray(n) { -1 }

    for (i in arr.indices) {
        val pos = tails.binarySearch(arr[i]).let {
            if (it < 0) -(it + 1) else it
        }

        if (pos == tails.size) {
            tails.add(arr[i])
            indices.add(i)
        } else {
            tails[pos] = arr[i]
            indices[pos] = i
        }

        if (pos > 0) {
            prev[i] = indices[pos - 1]
        }
    }

    // 역추적
    val result = mutableListOf<Int>()
    var idx = indices.last()
    while (idx != -1) {
        result.add(arr[idx])
        idx = prev[idx]
    }

    return result.reversed()
}

// Lower Bound 직접 구현
fun lowerBound(list: List<Int>, target: Int): Int {
    var left = 0
    var right = list.size

    while (left < right) {
        val mid = left + (right - left) / 2
        if (list[mid] < target) {
            left = mid + 1
        } else {
            right = mid
        }
    }

    return left
}
```

**관련 알고리즘**: LCS, 이진 탐색

---

<a id="knapsack"></a>
## 4. Knapsack (배낭 문제)

**목적**: 제한된 용량에서 최대 가치 선택

**시간 복잡도**: O(nW) - n: 아이템 수, W: 용량

**공간 복잡도**: O(nW), 최적화 시 O(W)

**특징**:
- 0/1 배낭 문제 (각 아이템 한 번만)
- 무한 배낭 문제 (아이템 무제한)
- NP-Hard 문제의 유사 다항 시간 해법

**장점**:
- 최적 부분 구조
- 다양한 최적화 문제에 적용

**단점**:
- 큰 용량에서 메모리 사용

**활용 예시**:
- 자원 할당
- 투자 포트폴리오
- 화물 적재

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 0/1 배낭 문제
fun knapsack01(weights: IntArray, values: IntArray, capacity: Int): Int {
    val n = weights.size
    val dp = Array(n + 1) { IntArray(capacity + 1) }

    for (i in 1..n) {
        for (w in 0..capacity) {
            dp[i][w] = dp[i - 1][w] // 아이템 선택 안함

            if (weights[i - 1] <= w) {
                dp[i][w] = maxOf(
                    dp[i][w],
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                )
            }
        }
    }

    return dp[n][capacity]
}

// 0/1 배낭 - 공간 최적화
fun knapsack01Optimized(weights: IntArray, values: IntArray, capacity: Int): Int {
    val dp = IntArray(capacity + 1)

    for (i in weights.indices) {
        for (w in capacity downTo weights[i]) {
            dp[w] = maxOf(dp[w], dp[w - weights[i]] + values[i])
        }
    }

    return dp[capacity]
}

// 선택한 아이템 추적
fun knapsack01WithItems(
    weights: IntArray,
    values: IntArray,
    capacity: Int
): Pair<Int, List<Int>> {
    val n = weights.size
    val dp = Array(n + 1) { IntArray(capacity + 1) }

    for (i in 1..n) {
        for (w in 0..capacity) {
            dp[i][w] = dp[i - 1][w]

            if (weights[i - 1] <= w) {
                dp[i][w] = maxOf(
                    dp[i][w],
                    dp[i - 1][w - weights[i - 1]] + values[i - 1]
                )
            }
        }
    }

    // 역추적
    val items = mutableListOf<Int>()
    var w = capacity
    for (i in n downTo 1) {
        if (dp[i][w] != dp[i - 1][w]) {
            items.add(i - 1)
            w -= weights[i - 1]
        }
    }

    return dp[n][capacity] to items.reversed()
}

// 무한 배낭 문제 (아이템 무제한)
fun unboundedKnapsack(weights: IntArray, values: IntArray, capacity: Int): Int {
    val dp = IntArray(capacity + 1)

    for (w in 1..capacity) {
        for (i in weights.indices) {
            if (weights[i] <= w) {
                dp[w] = maxOf(dp[w], dp[w - weights[i]] + values[i])
            }
        }
    }

    return dp[capacity]
}
```

**관련 알고리즘**: Coin Change, Subset Sum

---

<a id="edit-distance"></a>
## 5. Edit Distance (편집 거리, Levenshtein Distance)

**목적**: 한 문자열을 다른 문자열로 변환하는 최소 연산 수

**시간 복잡도**: O(mn)

**공간 복잡도**: O(mn), 최적화 시 O(min(m, n))

**특징**:
- 삽입, 삭제, 치환 연산
- LCS와 관련

**장점**:
- 문자열 유사도 측정
- 오타 교정에 활용

**단점**:
- 긴 문자열에서 느림

**활용 예시**:
- 맞춤법 검사
- DNA 서열 정렬
- 자연어 처리

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 기본 편집 거리
fun editDistance(s1: String, s2: String): Int {
    val m = s1.length
    val n = s2.length
    val dp = Array(m + 1) { IntArray(n + 1) }

    // 베이스 케이스
    for (i in 0..m) dp[i][0] = i
    for (j in 0..n) dp[0][j] = j

    for (i in 1..m) {
        for (j in 1..n) {
            if (s1[i - 1] == s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1]
            } else {
                dp[i][j] = 1 + minOf(
                    dp[i - 1][j],     // 삭제
                    dp[i][j - 1],     // 삽입
                    dp[i - 1][j - 1]  // 치환
                )
            }
        }
    }

    return dp[m][n]
}

// 공간 최적화
fun editDistanceOptimized(s1: String, s2: String): Int {
    val m = s1.length
    val n = s2.length
    var prev = IntArray(n + 1) { it }
    var curr = IntArray(n + 1)

    for (i in 1..m) {
        curr[0] = i
        for (j in 1..n) {
            if (s1[i - 1] == s2[j - 1]) {
                curr[j] = prev[j - 1]
            } else {
                curr[j] = 1 + minOf(prev[j], curr[j - 1], prev[j - 1])
            }
        }
        val temp = prev
        prev = curr
        curr = temp
    }

    return prev[n]
}

// 연산 추적
sealed class EditOp {
    data class Insert(val char: Char, val pos: Int) : EditOp()
    data class Delete(val pos: Int) : EditOp()
    data class Replace(val char: Char, val pos: Int) : EditOp()
    object Match : EditOp()
}

fun editDistanceWithOps(s1: String, s2: String): Pair<Int, List<EditOp>> {
    val m = s1.length
    val n = s2.length
    val dp = Array(m + 1) { IntArray(n + 1) }

    for (i in 0..m) dp[i][0] = i
    for (j in 0..n) dp[0][j] = j

    for (i in 1..m) {
        for (j in 1..n) {
            if (s1[i - 1] == s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1]
            } else {
                dp[i][j] = 1 + minOf(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
            }
        }
    }

    // 역추적
    val ops = mutableListOf<EditOp>()
    var i = m
    var j = n

    while (i > 0 || j > 0) {
        when {
            i > 0 && j > 0 && s1[i - 1] == s2[j - 1] -> {
                ops.add(EditOp.Match)
                i--
                j--
            }
            i > 0 && j > 0 && dp[i][j] == dp[i - 1][j - 1] + 1 -> {
                ops.add(EditOp.Replace(s2[j - 1], i - 1))
                i--
                j--
            }
            j > 0 && dp[i][j] == dp[i][j - 1] + 1 -> {
                ops.add(EditOp.Insert(s2[j - 1], i))
                j--
            }
            else -> {
                ops.add(EditOp.Delete(i - 1))
                i--
            }
        }
    }

    return dp[m][n] to ops.reversed()
}
```

**관련 알고리즘**: LCS, Hamming Distance

---

<a id="matrix-chain-multiplication"></a>
## 6. Matrix Chain Multiplication (행렬 체인 곱셈)

**목적**: 행렬 곱셈 순서를 최적화하여 최소 연산 수 계산

**시간 복잡도**: O(n³)

**공간 복잡도**: O(n²)

**특징**:
- 괄호화 최적화
- 구간 DP의 대표 문제

**장점**:
- 연산 비용 최소화
- 다양한 최적화 문제에 응용

**단점**:
- 구현이 복잡

**활용 예시**:
- 행렬 계산 최적화
- 파서 최적화
- 다각형 삼각분할

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 최소 곱셈 횟수 계산
fun matrixChainMultiplication(dims: IntArray): Int {
    val n = dims.size - 1
    val dp = Array(n) { IntArray(n) { 0 } }

    // 길이가 2 이상인 부분 문제
    for (len in 2..n) {
        for (i in 0..n - len) {
            val j = i + len - 1
            dp[i][j] = Int.MAX_VALUE

            for (k in i until j) {
                val cost = dp[i][k] + dp[k + 1][j] +
                           dims[i] * dims[k + 1] * dims[j + 1]
                dp[i][j] = minOf(dp[i][j], cost)
            }
        }
    }

    return dp[0][n - 1]
}

// 최적 괄호화 출력
fun matrixChainWithParenthesis(dims: IntArray): Pair<Int, String> {
    val n = dims.size - 1
    val dp = Array(n) { IntArray(n) { 0 } }
    val split = Array(n) { IntArray(n) { 0 } }

    for (len in 2..n) {
        for (i in 0..n - len) {
            val j = i + len - 1
            dp[i][j] = Int.MAX_VALUE

            for (k in i until j) {
                val cost = dp[i][k] + dp[k + 1][j] +
                           dims[i] * dims[k + 1] * dims[j + 1]
                if (cost < dp[i][j]) {
                    dp[i][j] = cost
                    split[i][j] = k
                }
            }
        }
    }

    fun buildParenthesis(i: Int, j: Int): String {
        if (i == j) return "M${i + 1}"
        return "(${buildParenthesis(i, split[i][j])} × ${buildParenthesis(split[i][j] + 1, j)})"
    }

    return dp[0][n - 1] to buildParenthesis(0, n - 1)
}
```

**관련 알고리즘**: 구간 DP, Optimal BST

---

<a id="coin-change"></a>
## 7. Coin Change (동전 교환)

**목적**: 주어진 금액을 만드는 최소 동전 수 또는 방법 수

**시간 복잡도**: O(nS) - n: 동전 종류, S: 목표 금액

**공간 복잡도**: O(S)

**특징**:
- 무한 배낭 문제의 변형
- 최소 개수 또는 조합 수

**장점**:
- 효율적인 해법
- 다양한 변형 가능

**단점**:
- 큰 금액에서 메모리 사용

**활용 예시**:
- 거스름돈 계산
- 환전
- 자원 분배

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 최소 동전 개수
fun coinChangeMin(coins: IntArray, amount: Int): Int {
    val dp = IntArray(amount + 1) { amount + 1 }
    dp[0] = 0

    for (i in 1..amount) {
        for (coin in coins) {
            if (coin <= i) {
                dp[i] = minOf(dp[i], dp[i - coin] + 1)
            }
        }
    }

    return if (dp[amount] > amount) -1 else dp[amount]
}

// 동전 조합 수 (순서 상관 없음)
fun coinChangeWays(coins: IntArray, amount: Int): Int {
    val dp = IntArray(amount + 1)
    dp[0] = 1

    for (coin in coins) {
        for (i in coin..amount) {
            dp[i] += dp[i - coin]
        }
    }

    return dp[amount]
}

// 동전 순열 수 (순서 상관 있음)
fun coinChangePermutations(coins: IntArray, amount: Int): Int {
    val dp = IntArray(amount + 1)
    dp[0] = 1

    for (i in 1..amount) {
        for (coin in coins) {
            if (coin <= i) {
                dp[i] += dp[i - coin]
            }
        }
    }

    return dp[amount]
}

// 사용된 동전 추적
fun coinChangeWithCoins(coins: IntArray, amount: Int): List<Int>? {
    val dp = IntArray(amount + 1) { amount + 1 }
    val parent = IntArray(amount + 1) { -1 }
    dp[0] = 0

    for (i in 1..amount) {
        for (coin in coins) {
            if (coin <= i && dp[i - coin] + 1 < dp[i]) {
                dp[i] = dp[i - coin] + 1
                parent[i] = coin
            }
        }
    }

    if (dp[amount] > amount) return null

    val result = mutableListOf<Int>()
    var remaining = amount
    while (remaining > 0) {
        result.add(parent[remaining])
        remaining -= parent[remaining]
    }

    return result
}
```

**관련 알고리즘**: Knapsack, Rod Cutting

---

<a id="rod-cutting"></a>
## 8. Rod Cutting (막대 자르기)

**목적**: 막대를 잘라서 최대 이익 얻기

**시간 복잡도**: O(n²)

**공간 복잡도**: O(n)

**특징**:
- 무한 배낭 문제의 변형
- 분할 최적화 문제

**장점**:
- 최적 분할 전략 도출
- 직관적인 DP 적용

**단점**:
- 큰 길이에서 시간 증가

**활용 예시**:
- 재료 절단 최적화
- 자원 분배

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 최대 이익 계산
fun rodCutting(prices: IntArray, n: Int): Int {
    val dp = IntArray(n + 1)

    for (i in 1..n) {
        for (j in 1..i) {
            if (j <= prices.size) {
                dp[i] = maxOf(dp[i], prices[j - 1] + dp[i - j])
            }
        }
    }

    return dp[n]
}

// 절단 위치 추적
fun rodCuttingWithCuts(prices: IntArray, n: Int): Pair<Int, List<Int>> {
    val dp = IntArray(n + 1)
    val cuts = IntArray(n + 1)

    for (i in 1..n) {
        for (j in 1..minOf(i, prices.size)) {
            if (prices[j - 1] + dp[i - j] > dp[i]) {
                dp[i] = prices[j - 1] + dp[i - j]
                cuts[i] = j
            }
        }
    }

    // 절단 복원
    val result = mutableListOf<Int>()
    var remaining = n
    while (remaining > 0) {
        result.add(cuts[remaining])
        remaining -= cuts[remaining]
    }

    return dp[n] to result
}

// 절단 비용이 있는 경우
fun rodCuttingWithCost(prices: IntArray, n: Int, cutCost: Int): Int {
    val dp = IntArray(n + 1)

    for (i in 1..n) {
        // 자르지 않는 경우
        if (i <= prices.size) {
            dp[i] = prices[i - 1]
        }

        // 자르는 경우 (비용 차감)
        for (j in 1 until i) {
            dp[i] = maxOf(dp[i], dp[j] + dp[i - j] - cutCost)
        }
    }

    return dp[n]
}
```

**관련 알고리즘**: Knapsack, Coin Change

---

<a id="bitmask-dp"></a>
## 9. Bitmask DP (비트마스크 DP)

**목적**: 부분 집합 상태를 비트마스크로 표현하는 DP. 대표 예제 TSP

**시간 복잡도**: O(2^n * n²) - TSP 기준

**공간 복잡도**: O(2^n * n)

**특징**:
- 상태 = (방문 집합 mask, 현재 위치)
- n ≤ 약 20까지 실용
- 비트 연산으로 부분집합 효율 순회

**장점**:
- NP-Hard 문제도 작은 n에선 최적해
- 상태 정의 단순

**단점**:
- 2^n 메모리/시간
- n이 조금만 커도 불가

**활용 예시**:
- TSP (외판원 문제)
- 부분집합 분할
- 비트 DP 일반화

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// TSP: 0번에서 출발해 모든 도시 한 번씩 방문 후 복귀, 최소 비용
fun tspBitmask(dist: Array<IntArray>): Int {
    val n = dist.size
    val INF = Int.MAX_VALUE / 2
    val dp = Array(1 shl n) { IntArray(n) { INF } }
    dp[1][0] = 0 // 0번만 방문, 현재 0

    for (mask in 1 until (1 shl n)) {
        for (u in 0 until n) {
            if ((mask and (1 shl u)) == 0) continue
            if (dp[mask][u] == INF) continue
            for (v in 0 until n) {
                if ((mask and (1 shl v)) != 0) continue
                val nm = mask or (1 shl v)
                val nc = dp[mask][u] + dist[u][v]
                if (nc < dp[nm][v]) dp[nm][v] = nc
            }
        }
    }

    val full = (1 shl n) - 1
    var ans = INF
    for (u in 1 until n) {
        if (dp[full][u] != INF) ans = minOf(ans, dp[full][u] + dist[u][0])
    }
    return ans
}
```

**관련 알고리즘**: Held-Karp, SOS DP

---

<a id="tree-dp"></a>
## 10. Tree DP (트리 DP)

**목적**: 트리 구조에서 서브트리 단위 DP. 대표 예: 서브트리 합/크기

**시간 복잡도**: O(n)

**공간 복잡도**: O(n)

**특징**:
- post-order 순회로 자식 결과 누적
- 루트 변경 트릭(rerooting)으로 모든 루트 결과 O(n)
- 서브트리 합/크기/지름 등 다양

**장점**:
- 선형 시간
- 트리 문제 만능 도구

**단점**:
- 트리 깊이 깊으면 재귀 스택 문제 (반복 DFS 필요)

**활용 예시**:
- 서브트리 합/노드 수
- 트리 지름
- 트리 매칭
- 트리 색칠

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// 각 노드의 서브트리 가중치 합 + 노드 수
class TreeDP(private val n: Int) {
    private val adj = Array(n) { mutableListOf<Int>() }
    val weight = IntArray(n)
    val subSum = LongArray(n)
    val subSize = IntArray(n)

    fun addEdge(u: Int, v: Int) { adj[u].add(v); adj[v].add(u) }

    fun compute(root: Int = 0) {
        val parent = IntArray(n) { -1 }
        val order = mutableListOf<Int>()
        val stack = ArrayDeque<Int>()
        stack.addLast(root)
        parent[root] = root
        while (stack.isNotEmpty()) {
            val u = stack.removeLast()
            order.add(u)
            for (v in adj[u]) {
                if (v != parent[u]) {
                    parent[v] = u
                    stack.addLast(v)
                }
            }
        }
        // post-order
        for (u in order.reversed()) {
            subSum[u] = weight[u].toLong()
            subSize[u] = 1
            for (v in adj[u]) {
                if (v != parent[u]) {
                    subSum[u] += subSum[v]
                    subSize[u] += subSize[v]
                }
            }
        }
    }
}

// 트리 지름: 가장 먼 두 노드 거리
fun treeDiameter(n: Int, edges: List<Pair<Int, Int>>): Int {
    val adj = Array(n) { mutableListOf<Int>() }
    for ((u, v) in edges) { adj[u].add(v); adj[v].add(u) }

    var best = 0
    fun dfs(u: Int, parent: Int): Int {
        var top1 = 0
        var top2 = 0
        for (v in adj[u]) {
            if (v == parent) continue
            val d = dfs(v, u) + 1
            if (d > top1) { top2 = top1; top1 = d }
            else if (d > top2) top2 = d
        }
        best = maxOf(best, top1 + top2)
        return top1
    }
    dfs(0, -1)
    return best
}
```

**관련 알고리즘**: Rerooting, Centroid Decomposition

---

<a id="digit-dp"></a>
## 11. Digit DP (자릿수 DP)

**목적**: 자릿수 범위 [a, b] 내에서 특정 조건을 만족하는 정수 개수를 셈

**시간 복잡도**: O(자릿수 * 상태) - 일반적으로 매우 빠름

**공간 복잡도**: O(자릿수 * 상태)

**특징**:
- 상태: (위치, tight, 사용자 정의 상태)
- tight=true: 상한과 같은 prefix 유지 중
- f(b) - f(a-1)로 범위 처리

**장점**:
- 매우 큰 범위(10^18)도 처리
- 다양한 조건 일반화

**단점**:
- 상태 설계 까다로움
- 메모이제이션 키 신중

**활용 예시**:
- 자릿수 합 조건 카운트
- 특정 숫자 등장 횟수
- 회문 숫자
- 디지털 합 합산

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 1..n 중 각 자리수의 합이 target인 수 개수
fun countWithDigitSum(n: Long, target: Int): Long {
    val digits = n.toString().map { it - '0' }
    val len = digits.size
    // memo[pos][sumSoFar][tight] - tight는 별도 분기로 처리
    val memo = Array(len) { LongArray(target + 1) { -1L } }

    fun dp(pos: Int, sumSoFar: Int, tight: Boolean): Long {
        if (sumSoFar > target) return 0L
        if (pos == len) return if (sumSoFar == target) 1L else 0L
        if (!tight && memo[pos][sumSoFar] != -1L) return memo[pos][sumSoFar]

        val limit = if (tight) digits[pos] else 9
        var result = 0L
        for (d in 0..limit) {
            result += dp(pos + 1, sumSoFar + d, tight && d == limit)
        }
        if (!tight) memo[pos][sumSoFar] = result
        return result
    }

    return dp(0, 0, true)
}
```

**관련 알고리즘**: 일반 DP, 조합론

---

<a id="sos-dp"></a>
## 12. SOS DP (Sum over Subsets, 부분집합 합)

**목적**: f(mask) = Σ g(sub) for sub ⊆ mask 를 O(n * 2^n)에 계산

**시간 복잡도**: O(n * 2^n)

**공간 복잡도**: O(2^n)

**특징**:
- 각 비트 차원에 대해 1D 누적 합
- subset sum convolution 기본 도구
- Zeta/Mobius transform과 동치

**장점**:
- 단순 2^(2n)에서 n * 2^n로 개선
- 다양한 부분집합 DP 빠르게

**단점**:
- n > 약 22면 메모리 한계
- 상태 정의 익숙해져야 함

**활용 예시**:
- 부분집합 최대값/최소값/합
- 비트마스크 조합
- 형제 부분집합 통계
- AC 자체 부분집합 합 응용

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// dp[mask] = sum of a[sub] for all sub subset of mask
fun sosDP(a: IntArray): IntArray {
    val n = a.size
    val bits = 32 - Integer.numberOfLeadingZeros(n - 1)
    val dp = a.copyOf()
    for (i in 0 until bits) {
        for (mask in 0 until n) {
            if ((mask and (1 shl i)) != 0) {
                dp[mask] += dp[mask xor (1 shl i)]
            }
        }
    }
    return dp
}

// 역변환 (Mobius): a[mask] = sum of (-1)^|mask\sub| * dp[sub]
fun sosInverse(dp: IntArray): IntArray {
    val n = dp.size
    val bits = 32 - Integer.numberOfLeadingZeros(n - 1)
    val a = dp.copyOf()
    for (i in 0 until bits) {
        for (mask in 0 until n) {
            if ((mask and (1 shl i)) != 0) {
                a[mask] -= a[mask xor (1 shl i)]
            }
        }
    }
    return a
}
```

**관련 알고리즘**: Zeta/Mobius Transform, Subset Sum Convolution

---

<a id="dp-optimizations"></a>
## 13. DP Optimizations (Convex Hull Trick / Knuth / D&C DP) (DP 최적화 기법)

**목적**: 점화식의 전이(transition) 비용을 줄여 O(n²) DP를 O(n log n) 또는 O(n)으로 가속하는 기법 모음

**시간 복잡도**: 기법별 — CHT O(n) (단조) / O(n log n) (Li Chao·동적), Knuth O(n²) (기존 O(n³)에서), D&C DP O(kn log n) (기존 O(kn²)에서)

**공간 복잡도**: O(n) ~ O(n²) (DP 테이블 차원에 의존)

**특징**:
- Convex Hull Trick(CHT): `dp[i] = min_j(a[j]·x[i] + b[j])` 형태의 선형 전이를 직선들의 하한 포락선(lower envelope)으로 관리. 기울기 단조 + 쿼리 단조면 deque로 amortized O(1) 전이
- Knuth 최적화: 비용이 사각 부등식(quadrangle inequality, QI)과 단조성을 만족하면 최적 분할점이 `opt[i][j-1] ≤ opt[i][j] ≤ opt[i+1][j]` 범위로 좁혀져 구간 DP가 O(n³)→O(n²)
- Divide & Conquer DP: 최적 결정점 `opt(i)`가 i에 대해 단조 증가할 때(monotonicity), 분할 정복으로 각 층을 O(n log n)에 계산 → O(kn²)→O(kn log n)
- Li Chao Tree: 기울기·쿼리가 단조가 아닐 때도 임의 순서로 직선/선분을 삽입하고 한 점 최솟값을 O(log C)에 질의하는 CHT 일반화 자료구조
- 핵심 전제는 비용 함수의 볼록성(convexity)·QI·결정 단조성이며, 성립 여부 증명이 적용의 선결 조건

**장점**:
- 제약이 큰 입력(n ≥ 10⁵)에서 기존 이차/삼차 DP를 실행 가능 범위로 단축
- CHT·Li Chao는 자료구조로 모듈화되어 다양한 선형 전이에 재사용 가능
- D&C DP는 구현이 비교적 짧고 분할 정복 골격이 명료

**단점**:
- 적용 조건(볼록성/QI/단조성) 검증이 까다롭고, 조건 불성립 시 오답
- CHT의 deque 버전은 기울기·쿼리 단조 가정에 의존(깨지면 Li Chao 필요)
- 부동소수·오버플로(직선 교점, 곱셈) 처리에 주의 필요

**활용 예시**:
- 작업/케이블 분할 비용 최소화, 수열 분할 DP (D&C DP, Knuth)
- 이동·운송 비용 누적 최적화 (CHT)
- 최적 BST·구간 병합 비용 (Knuth 최적화)
- 비단조 기울기를 갖는 선형 전이 일반화 (Li Chao Tree)

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// Convex Hull Trick (기울기 내림차순 삽입 + 쿼리 단조) — amortized O(n)
// dp[i] = min_j ( slope[j] * x + intercept[j] ) 형태 전이 가속
class ConvexHullTrick {
    private val slopes = ArrayDeque<Long>()      // 직선 기울기 (내림차순)
    private val intercepts = ArrayDeque<Long>()  // 직선 절편

    // 교점 비교: 직선3이 직선1·직선2의 교점을 덮어 직선2를 불필요하게 만드는가
    private fun bad(m1: Long, b1: Long, m2: Long, b2: Long, m3: Long, b3: Long): Boolean =
        (b3 - b1) * (m1 - m2) <= (b2 - b1) * (m1 - m3)  // 교차 곱(오버플로 주의)

    // 기울기 단조 감소 순서로 직선 추가
    fun addLine(m: Long, b: Long) {
        var nm = m; var nb = b
        while (slopes.size >= 2) {
            val s = slopes.size
            if (bad(slopes[s - 2], intercepts[s - 2], slopes[s - 1], intercepts[s - 1], nm, nb)) {
                slopes.removeLast(); intercepts.removeLast()
            } else break
        }
        slopes.addLast(nm); intercepts.addLast(nb)
    }

    // x가 증가하는 순서로만 호출 시 deque 앞에서 amortized O(1)
    fun query(x: Long): Long {
        while (slopes.size >= 2 &&
            slopes[0] * x + intercepts[0] >= slopes[1] * x + intercepts[1]) {
            slopes.removeFirst(); intercepts.removeFirst()
        }
        return slopes[0] * x + intercepts[0]
    }
}
```

**관련 알고리즘**: Edit Distance (DP), LCS, Matrix Chain Multiplication, Segment Tree
