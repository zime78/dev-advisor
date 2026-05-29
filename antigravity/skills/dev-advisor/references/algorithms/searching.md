# 탐색 알고리즘 (Searching Algorithms)

데이터 집합에서 특정 값을 찾는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [linear-search](#linear-search) | Linear Search | 선형 탐색 | 낮음 |
| [binary-search](#binary-search) | Binary Search | 이진 탐색 | 낮음 |
| [jump-search](#jump-search) | Jump Search | 점프 탐색 | 낮음 |
| [interpolation-search](#interpolation-search) | Interpolation Search | 보간 탐색 | 중간 |
| [exponential-search](#exponential-search) | Exponential Search | 지수 탐색 | 중간 |
| [fibonacci-search](#fibonacci-search) | Fibonacci Search | 피보나치 탐색 | 중간 |
| [ternary-search](#ternary-search) | Ternary Search | 삼진 탐색 | 중간 |
| [hash-table-search](#hash-table-search) | Hash Table Search | 해시 테이블 탐색 | 중간 |
| [two-pointers](#two-pointers) | Two Pointers | 투 포인터 | 낮음 |
| [sliding-window](#sliding-window) | Sliding Window | 슬라이딩 윈도우 | 중간 |
| [binary-lifting](#binary-lifting) | Binary Lifting / Sparse Table | 이진 점프 / 희소 테이블 | 중간 |
| [mo-algorithm](#mo-algorithm) | Mo's Algorithm | 모 알고리즘 | 높음 |
| [parallel-binary-search](#parallel-binary-search) | Parallel Binary Search | 병렬 이진 탐색 | 높음 |

---

<a id="linear-search"></a>
## 1. Linear Search (선형 탐색)

**목적**: 처음부터 끝까지 순차적으로 검색

**시간 복잡도**: O(n)

**공간 복잡도**: O(1)

**특징**:
- 가장 단순한 탐색
- 정렬 불필요
- 모든 자료구조에 적용 가능

**장점**:
- 구현이 매우 간단
- 전처리 불필요

**단점**:
- 대규모 데이터에서 비효율적

**활용 예시**:
- 소규모 데이터
- 정렬되지 않은 데이터

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
fun linearSearch(arr: IntArray, target: Int): Int {
    for (i in arr.indices) {
        if (arr[i] == target) return i
    }
    return -1
}
```

**관련 알고리즘**: Binary Search

---

<a id="binary-search"></a>
## 2. Binary Search (이진 탐색)

**목적**: 정렬된 배열에서 중간값 비교로 탐색 범위 절반씩 축소

**시간 복잡도**: O(log n)

**공간 복잡도**: O(1) 반복, O(log n) 재귀

**특징**:
- 분할 정복
- 정렬된 배열 필수
- 매우 효율적

**장점**:
- O(log n) 시간 복잡도
- 대규모 데이터에 효율적

**단점**:
- 정렬된 배열 필요
- 연결 리스트에서 비효율적

**활용 예시**:
- 정렬된 배열 검색
- Lower/Upper Bound 찾기
- 이분 탐색 문제

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
fun binarySearch(arr: IntArray, target: Int): Int {
    var left = 0
    var right = arr.size - 1

    while (left <= right) {
        val mid = left + (right - left) / 2
        when {
            arr[mid] == target -> return mid
            arr[mid] < target -> left = mid + 1
            else -> right = mid - 1
        }
    }
    return -1
}

// Lower Bound: target 이상인 첫 번째 위치
fun lowerBound(arr: IntArray, target: Int): Int {
    var left = 0
    var right = arr.size

    while (left < right) {
        val mid = left + (right - left) / 2
        if (arr[mid] < target) left = mid + 1
        else right = mid
    }
    return left
}
```

**관련 알고리즘**: Ternary Search, Exponential Search

---

<a id="jump-search"></a>
## 3. Jump Search (점프 탐색)

**목적**: 블록 단위로 점프하며 탐색 후 선형 탐색

**시간 복잡도**: O(sqrt(n))

**공간 복잡도**: O(1)

**특징**:
- Linear와 Binary의 중간
- 블록 크기는 sqrt(n)이 최적

**장점**:
- Binary Search보다 후진 이동 적음
- 구현이 비교적 간단

**단점**:
- Binary Search보다 느림

**활용 예시**:
- 후진 이동이 비싼 시스템

**난이도**: 낮음 | **사용 빈도**: ★☆☆☆☆

**Kotlin 코드**:
```kotlin
import kotlin.math.sqrt
import kotlin.math.min

fun jumpSearch(arr: IntArray, target: Int): Int {
    val n = arr.size
    val step = sqrt(n.toDouble()).toInt()
    var prev = 0

    while (arr[min(step, n) - 1] < target) {
        prev = step
        if (prev >= n) return -1
    }

    while (arr[prev] < target) {
        prev++
        if (prev == min(step, n)) return -1
    }

    return if (arr[prev] == target) prev else -1
}
```

**관련 알고리즘**: Binary Search, Linear Search

---

<a id="interpolation-search"></a>
## 4. Interpolation Search (보간 탐색)

**목적**: 값의 위치를 추정하여 탐색

**시간 복잡도**: O(log log n) 평균, O(n) 최악

**공간 복잡도**: O(1)

**특징**:
- 균등 분포 데이터에 최적
- Binary Search의 개선

**장점**:
- 균등 분포 시 매우 빠름

**단점**:
- 불균등 분포 시 O(n)
- 오버플로우 주의 필요

**활용 예시**:
- 균등하게 분포된 정렬 데이터
- 사전 검색

**난이도**: 중간 | **사용 빈도**: ★☆☆☆☆

**Kotlin 코드**:
```kotlin
fun interpolationSearch(arr: IntArray, target: Int): Int {
    var low = 0
    var high = arr.size - 1

    while (low <= high && target >= arr[low] && target <= arr[high]) {
        if (low == high) {
            return if (arr[low] == target) low else -1
        }

        val pos = low + ((target - arr[low]).toLong() * (high - low) /
                        (arr[high] - arr[low])).toInt()

        when {
            arr[pos] == target -> return pos
            arr[pos] < target -> low = pos + 1
            else -> high = pos - 1
        }
    }
    return -1
}
```

**관련 알고리즘**: Binary Search

---

<a id="exponential-search"></a>
## 5. Exponential Search (지수 탐색)

**목적**: 지수적으로 범위를 확장 후 Binary Search

**시간 복잡도**: O(log n)

**공간 복잡도**: O(1)

**특징**:
- 무한 배열에 적합
- 타겟이 앞쪽에 있으면 빠름

**장점**:
- 무한/대규모 배열에 효과적
- 타겟이 앞쪽일 때 빠름

**단점**:
- Binary Search보다 약간 느림

**활용 예시**:
- 무한 배열
- 크기를 모르는 정렬 배열

**난이도**: 중간 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
fun exponentialSearch(arr: IntArray, target: Int): Int {
    if (arr.isEmpty()) return -1
    if (arr[0] == target) return 0

    var i = 1
    while (i < arr.size && arr[i] <= target) {
        i *= 2
    }

    return binarySearchRange(arr, target, i / 2, minOf(i, arr.size - 1))
}

fun binarySearchRange(arr: IntArray, target: Int, left: Int, right: Int): Int {
    var l = left
    var r = right
    while (l <= r) {
        val mid = l + (r - l) / 2
        when {
            arr[mid] == target -> return mid
            arr[mid] < target -> l = mid + 1
            else -> r = mid - 1
        }
    }
    return -1
}
```

**관련 알고리즘**: Binary Search

---

<a id="fibonacci-search"></a>
## 6. Fibonacci Search (피보나치 탐색)

**목적**: 피보나치 수열을 이용한 분할 탐색

**시간 복잡도**: O(log n)

**공간 복잡도**: O(1)

**특징**:
- Binary Search의 변형
- 곱셈/나눗셈 대신 덧셈/뺄셈 사용

**장점**:
- 곱셈/나눗셈 없이 구현 가능
- CPU 캐시에 더 친화적

**단점**:
- 구현이 복잡
- 실제로 Binary Search와 큰 차이 없음

**활용 예시**:
- 하드웨어 최적화
- 곱셈이 비싼 시스템

**난이도**: 중간 | **사용 빈도**: ★☆☆☆☆

**Kotlin 코드**:
```kotlin
fun fibonacciSearch(arr: IntArray, target: Int): Int {
    val n = arr.size
    var fibM2 = 0  // (m-2)'th Fibonacci
    var fibM1 = 1  // (m-1)'th Fibonacci
    var fibM = fibM2 + fibM1  // m'th Fibonacci

    while (fibM < n) {
        fibM2 = fibM1
        fibM1 = fibM
        fibM = fibM2 + fibM1
    }

    var offset = -1

    while (fibM > 1) {
        val i = minOf(offset + fibM2, n - 1)

        when {
            arr[i] < target -> {
                fibM = fibM1
                fibM1 = fibM2
                fibM2 = fibM - fibM1
                offset = i
            }
            arr[i] > target -> {
                fibM = fibM2
                fibM1 -= fibM2
                fibM2 = fibM - fibM1
            }
            else -> return i
        }
    }

    if (fibM1 == 1 && offset + 1 < n && arr[offset + 1] == target) {
        return offset + 1
    }

    return -1
}
```

**관련 알고리즘**: Binary Search

---

<a id="ternary-search"></a>
## 7. Ternary Search (삼진 탐색)

**목적**: 배열을 3등분하여 탐색

**시간 복잡도**: O(log3 n) = O(log n)

**공간 복잡도**: O(1)

**특징**:
- Binary Search의 변형
- Unimodal 함수의 최대/최소값 찾기에 유용

**장점**:
- 최대/최소값 찾기에 유용
- Unimodal 함수에 적합

**단점**:
- 일반 검색은 Binary Search가 더 효율적

**활용 예시**:
- Unimodal 함수의 극값 찾기
- 최적화 문제

**난이도**: 중간 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// Unimodal 함수의 최대값 위치 찾기
fun ternarySearchMax(f: (Double) -> Double, left: Double, right: Double, eps: Double = 1e-9): Double {
    var l = left
    var r = right

    while (r - l > eps) {
        val m1 = l + (r - l) / 3
        val m2 = r - (r - l) / 3

        if (f(m1) < f(m2)) l = m1
        else r = m2
    }

    return (l + r) / 2
}

// 배열에서 값 검색
fun ternarySearch(arr: IntArray, target: Int): Int {
    var left = 0
    var right = arr.size - 1

    while (left <= right) {
        val mid1 = left + (right - left) / 3
        val mid2 = right - (right - left) / 3

        when {
            arr[mid1] == target -> return mid1
            arr[mid2] == target -> return mid2
            target < arr[mid1] -> right = mid1 - 1
            target > arr[mid2] -> left = mid2 + 1
            else -> {
                left = mid1 + 1
                right = mid2 - 1
            }
        }
    }
    return -1
}
```

**관련 알고리즘**: Binary Search

---

<a id="hash-table-search"></a>
## 8. Hash Table Search (해시 테이블 탐색)

**목적**: 해시 함수로 직접 위치 계산

**시간 복잡도**: O(1) 평균, O(n) 최악

**공간 복잡도**: O(n)

**특징**:
- 키-값 매핑
- 충돌 처리 필요
- 상수 시간 접근

**장점**:
- 평균 O(1) 검색
- 삽입/삭제도 O(1)

**단점**:
- 추가 메모리 필요
- 해시 충돌 처리 필요
- 정렬 순서 유지 안됨

**활용 예시**:
- 데이터베이스 인덱싱
- 캐싱
- 중복 검사

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// Kotlin의 HashMap 사용
fun hashTableExample() {
    val map = hashMapOf<String, Int>()

    // 삽입
    map["apple"] = 1
    map["banana"] = 2

    // 검색 - O(1)
    val value = map["apple"]  // 1

    // 존재 여부 확인
    val exists = map.containsKey("apple")  // true

    // 삭제
    map.remove("apple")
}

// 간단한 해시 테이블 구현
class SimpleHashTable<K, V>(private val capacity: Int = 16) {
    private val buckets = Array<MutableList<Pair<K, V>>>(capacity) { mutableListOf() }

    private fun hash(key: K): Int = (key.hashCode() and 0x7fffffff) % capacity

    fun put(key: K, value: V) {
        val bucket = buckets[hash(key)]
        val index = bucket.indexOfFirst { it.first == key }
        if (index >= 0) bucket[index] = key to value
        else bucket.add(key to value)
    }

    fun get(key: K): V? {
        return buckets[hash(key)].find { it.first == key }?.second
    }

    fun remove(key: K): Boolean {
        return buckets[hash(key)].removeIf { it.first == key }
    }
}
```

**관련 알고리즘**: BST Search

---

<a id="two-pointers"></a>
## 9. Two Pointers (투 포인터)

**목적**: 정렬된 배열/문자열에서 두 인덱스를 함께 움직이며 O(n)에 쿼리

**시간 복잡도**: O(n)

**공간 복잡도**: O(1)

**특징**:
- 좌/우 또는 동방향 포인터
- 합이 target보다 작으면 왼쪽 ↑, 크면 오른쪽 ↓
- 단조성 필요

**장점**:
- 매우 빠르고 단순
- 추가 메모리 없음

**단점**:
- 단조성 없으면 적용 불가
- 정렬된 입력 필요

**활용 예시**:
- 정렬 배열의 두 수 합 = target
- 회문 판정
- 컨테이너에 가장 많은 물 담기
- 정렬 배열 병합

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 정렬된 배열에서 두 수 합이 target
fun twoSumSorted(arr: IntArray, target: Int): Pair<Int, Int>? {
    var l = 0
    var r = arr.size - 1
    while (l < r) {
        val s = arr[l] + arr[r]
        when {
            s == target -> return l to r
            s < target -> l++
            else -> r--
        }
    }
    return null
}

// 회문 판정
fun isPalindrome(s: String): Boolean {
    var l = 0; var r = s.length - 1
    while (l < r) {
        if (s[l] != s[r]) return false
        l++; r--
    }
    return true
}

// 정렬된 두 배열 병합
fun merge(a: IntArray, b: IntArray): IntArray {
    val out = IntArray(a.size + b.size)
    var i = 0; var j = 0; var k = 0
    while (i < a.size && j < b.size) {
        if (a[i] <= b[j]) out[k++] = a[i++] else out[k++] = b[j++]
    }
    while (i < a.size) out[k++] = a[i++]
    while (j < b.size) out[k++] = b[j++]
    return out
}
```

**관련 알고리즘**: Sliding Window, Binary Search

---

<a id="sliding-window"></a>
## 10. Sliding Window (슬라이딩 윈도우)

**목적**: 연속 부분배열/부분문자열에 대한 쿼리를 O(n)에 처리

**시간 복잡도**: O(n)

**공간 복잡도**: O(k) - 윈도우 상태

**특징**:
- 고정 크기 또는 가변 크기 윈도우
- 오른쪽 확장 + 왼쪽 수축 패턴
- HashMap/Deque로 상태 유지

**장점**:
- 선형 시간
- 다양한 부분배열 문제에 일반화

**단점**:
- 상태 유지 자료구조 필요
- 윈도우 수축 조건 신중 설계

**활용 예시**:
- 가장 긴 중복 없는 부분문자열
- 합 ≥ target 인 가장 짧은 부분배열
- 최대값 슬라이딩 윈도우 (deque)
- 부분문자열 anagram

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 가장 긴 중복 없는 부분문자열
fun longestUniqueSubstring(s: String): Int {
    val seen = HashMap<Char, Int>()
    var left = 0
    var best = 0
    for (right in s.indices) {
        val c = s[right]
        seen[c]?.let { if (it >= left) left = it + 1 }
        seen[c] = right
        best = maxOf(best, right - left + 1)
    }
    return best
}

// 합 ≥ target 인 가장 짧은 부분배열
fun shortestSubarrayWithSum(arr: IntArray, target: Int): Int {
    var l = 0; var sum = 0; var best = Int.MAX_VALUE
    for (r in arr.indices) {
        sum += arr[r]
        while (sum >= target) {
            best = minOf(best, r - l + 1)
            sum -= arr[l++]
        }
    }
    return if (best == Int.MAX_VALUE) 0 else best
}

// 슬라이딩 윈도우 최대값 (Deque)
fun slidingMax(arr: IntArray, k: Int): IntArray {
    val n = arr.size
    val result = IntArray(n - k + 1)
    val dq = ArrayDeque<Int>() // index
    for (i in 0 until n) {
        while (dq.isNotEmpty() && dq.first() <= i - k) dq.removeFirst()
        while (dq.isNotEmpty() && arr[dq.last()] < arr[i]) dq.removeLast()
        dq.addLast(i)
        if (i >= k - 1) result[i - k + 1] = arr[dq.first()]
    }
    return result
}
```

**관련 알고리즘**: Two Pointers, Monotonic Deque

---

<a id="binary-lifting"></a>
## 11. Binary Lifting / Sparse Table (이진 점프 / 희소 테이블)

**목적**: 정적 배열에 대한 idempotent 구간 쿼리(min, max, gcd)를 O(1)에 처리

**시간 복잡도**: O(n log n) 전처리, O(1) 쿼리

**공간 복잡도**: O(n log n)

**특징**:
- sparse[k][i] = arr[i..i+2^k-1]의 min/max/gcd
- 두 개의 겹치는 구간으로 임의 구간 쿼리
- 갱신은 지원 안 함 (정적 데이터)

**장점**:
- O(1) 쿼리
- 구현 단순

**단점**:
- 갱신 불가
- 합처럼 idempotent 아닌 연산은 안 됨 (Fenwick 사용)

**활용 예시**:
- Range Minimum Query (RMQ)
- LCA (Euler Tour + RMQ)
- 정적 GCD 쿼리

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
class SparseTableMin(arr: IntArray) {
    private val n = arr.size
    private val log = IntArray(n + 1)
    private val table: Array<IntArray>

    init {
        for (i in 2..n) log[i] = log[i / 2] + 1
        val k = log[n] + 1
        table = Array(k) { IntArray(n) }
        for (i in 0 until n) table[0][i] = arr[i]
        for (j in 1 until k) {
            var i = 0
            while (i + (1 shl j) <= n) {
                table[j][i] = minOf(table[j - 1][i], table[j - 1][i + (1 shl (j - 1))])
                i++
            }
        }
    }

    fun query(l: Int, r: Int): Int {
        val j = log[r - l + 1]
        return minOf(table[j][l], table[j][r - (1 shl j) + 1])
    }
}
```

**관련 알고리즘**: Segment Tree, Fenwick Tree, LCA

---

<a id="mo-algorithm"></a>
## 12. Mo's Algorithm (모 알고리즘)

**목적**: 오프라인 구간 쿼리들을 √n 블록 단위로 정렬하여 O((n+q)√n)에 일괄 처리

**시간 복잡도**: O((n + q) * √n)

**공간 복잡도**: O(n + q)

**특징**:
- 쿼리를 (l/B, r) 기준 정렬 (B = √n)
- 포인터 l, r을 점진적으로 이동
- add/remove 연산이 O(1)이어야 효율적

**장점**:
- 다양한 오프라인 쿼리에 일반화
- 구현 비교적 단순

**단점**:
- 오프라인만 가능 (모든 쿼리 미리 받기)
- add/remove가 비싸면 효율 저하

**활용 예시**:
- 구간 내 distinct 원소 수
- 구간 내 빈도 통계
- 구간 곱/합 (다른 자료구조보다 단순)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.math.sqrt

data class MoQuery(val l: Int, val r: Int, val idx: Int)

class MoAlgorithm(private val arr: IntArray, private val maxVal: Int) {
    private val freq = IntArray(maxVal + 1)
    var distinctCount = 0
        private set

    private fun add(x: Int) {
        if (freq[x] == 0) distinctCount++
        freq[x]++
    }

    private fun remove(x: Int) {
        freq[x]--
        if (freq[x] == 0) distinctCount--
    }

    fun answer(queries: List<MoQuery>): IntArray {
        val n = arr.size
        val block = sqrt(n.toDouble()).toInt()
        val sorted = queries.sortedWith(
            compareBy({ it.l / block }, { if ((it.l / block) % 2 == 0) it.r else -it.r })
        )

        val answers = IntArray(queries.size)
        var l = 0; var r = -1
        for (q in sorted) {
            while (r < q.r) { r++; add(arr[r]) }
            while (l > q.l) { l--; add(arr[l]) }
            while (r > q.r) { remove(arr[r]); r-- }
            while (l < q.l) { remove(arr[l]); l++ }
            answers[q.idx] = distinctCount
        }
        return answers
    }
}
```

**관련 알고리즘**: Sqrt Decomposition, Segment Tree

---

<a id="parallel-binary-search"></a>
## 13. Parallel Binary Search (병렬 이진 탐색)

**목적**: 다수의 이진 탐색 쿼리를 한꺼번에 처리. 각 쿼리의 답을 동시에 절반씩 좁힘

**시간 복잡도**: O((n + q) * log(범위) * 단계비용)

**공간 복잡도**: O(n + q)

**특징**:
- log V회 반복, 각 반복마다 모든 쿼리에 대해 현재 mid에서 결정
- 시간 순으로 이벤트 적용 + 쿼리 분류
- offline 알고리즘

**장점**:
- 개별 이진 탐색을 O(log)배 빠르게
- 자료구조 재사용

**단점**:
- 오프라인만 가능
- 구현 복잡

**활용 예시**:
- "시간 t에 처음으로 조건 만족하는 순간" 쿼리들
- 동적 연결성에서 컴포넌트 합쳐지는 순간
- Kinetic event 처리

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// 의사코드 + 골격
// 입력: q개 쿼리, 각 쿼리의 답이 [1..T] 범위에 있음
// 매 단계 r:
//   각 쿼리를 현재 lo/hi의 mid에 따라 버킷에 분류
//   t=1..T 이벤트를 시간순으로 적용하며 mid에 도달한 쿼리 평가
//   평가 결과로 각 쿼리의 lo/hi 갱신
// log T 단계 후 각 쿼리의 lo == hi == 답

class ParallelBinarySearch(private val queryCount: Int, private val tMax: Int) {
    private val lo = IntArray(queryCount) { 1 }
    private val hi = IntArray(queryCount) { tMax }

    fun run(
        check: (queryId: Int, time: Int) -> Boolean,
        applyEvent: (time: Int) -> Unit,
        resetState: () -> Unit
    ): IntArray {
        repeat(32 - Integer.numberOfLeadingZeros(tMax)) {
            // 각 쿼리를 mid 별로 그룹화
            val buckets = HashMap<Int, MutableList<Int>>()
            for (q in 0 until queryCount) {
                if (lo[q] < hi[q]) {
                    val mid = (lo[q] + hi[q]) / 2
                    buckets.getOrPut(mid) { mutableListOf() }.add(q)
                }
            }
            resetState()
            for (t in 1..tMax) {
                applyEvent(t)
                buckets[t]?.forEach { q ->
                    if (check(q, t)) hi[q] = t
                    else lo[q] = t + 1
                }
            }
        }
        return lo
    }
}
```

**관련 알고리즘**: Offline Binary Search, Persistent Segment Tree
