# 분할 정복 (Divide and Conquer)

문제를 작은 부분 문제로 분할하고, 각각을 해결한 후 결과를 결합하는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [binary-search-dc](#binary-search-dc) | Binary Search | 이진 탐색 | 낮음 |
| [merge-sort-dc](#merge-sort-dc) | Merge Sort | 병합 정렬 | 중간 |
| [strassen](#strassen) | Strassen's Matrix Multiplication | 스트라센 행렬 곱셈 | 높음 |
| [closest-pair](#closest-pair) | Closest Pair of Points | 최근접 점 쌍 | 높음 |
| [karatsuba](#karatsuba) | Karatsuba Multiplication | 카라츠바 곱셈 | 높음 |

---

<a id="binary-search-dc"></a>
## 1. Binary Search (이진 탐색)

> 표준 구현은 [searching.md#binary-search](../algorithms/searching.md#binary-search) 참조. 본 카테고리는 분할 정복 관점에서의 변형/해석을 다룬다.

**목적**: 정렬된 배열에서 효율적인 검색

**시간 복잡도**: O(log n)

**공간 복잡도**: O(1) 반복, O(log n) 재귀

**특징**:
- 분할 정복의 기본
- 탐색 범위를 절반으로 축소

**장점**:
- 매우 빠른 탐색
- 구현이 간단

**단점**:
- 정렬된 데이터 필요

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 반복 방식
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

// 재귀 방식 (분할 정복)
fun binarySearchRecursive(arr: IntArray, target: Int, left: Int = 0, right: Int = arr.size - 1): Int {
    if (left > right) return -1

    val mid = left + (right - left) / 2
    return when {
        arr[mid] == target -> mid
        arr[mid] < target -> binarySearchRecursive(arr, target, mid + 1, right)
        else -> binarySearchRecursive(arr, target, left, mid - 1)
    }
}
```

**관련 알고리즘**: Merge Sort, Quick Sort

---

<a id="merge-sort-dc"></a>
## 2. Merge Sort (병합 정렬)

> 표준 구현은 [sorting.md#merge-sort](sorting.md#merge-sort) 참조. 본 카테고리는 분할 정복 관점에서의 점화식/마스터 정리 해석을 다룬다.

**목적**: 배열을 분할하고 병합하여 정렬

**시간 복잡도**: O(n log n)

**공간 복잡도**: O(n)

**특징**:
- 안정 정렬
- 분할 → 정복 → 결합

**장점**:
- 항상 O(n log n) 보장
- 연결 리스트 정렬에 효율적

**단점**:
- 추가 메모리 O(n) 필요

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
fun mergeSort(arr: IntArray): IntArray {
    if (arr.size <= 1) return arr

    val mid = arr.size / 2
    val left = mergeSort(arr.sliceArray(0 until mid))
    val right = mergeSort(arr.sliceArray(mid until arr.size))

    return merge(left, right)
}

private fun merge(left: IntArray, right: IntArray): IntArray {
    val result = IntArray(left.size + right.size)
    var i = 0
    var j = 0
    var k = 0

    while (i < left.size && j < right.size) {
        if (left[i] <= right[j]) {
            result[k++] = left[i++]
        } else {
            result[k++] = right[j++]
        }
    }

    while (i < left.size) result[k++] = left[i++]
    while (j < right.size) result[k++] = right[j++]

    return result
}

// In-place 병합 정렬 (인덱스 기반)
fun mergeSortInPlace(arr: IntArray, left: Int = 0, right: Int = arr.size - 1) {
    if (left < right) {
        val mid = left + (right - left) / 2
        mergeSortInPlace(arr, left, mid)
        mergeSortInPlace(arr, mid + 1, right)
        mergeInPlace(arr, left, mid, right)
    }
}

private fun mergeInPlace(arr: IntArray, left: Int, mid: Int, right: Int) {
    val leftArr = arr.sliceArray(left..mid)
    val rightArr = arr.sliceArray((mid + 1)..right)

    var i = 0
    var j = 0
    var k = left

    while (i < leftArr.size && j < rightArr.size) {
        if (leftArr[i] <= rightArr[j]) {
            arr[k++] = leftArr[i++]
        } else {
            arr[k++] = rightArr[j++]
        }
    }

    while (i < leftArr.size) arr[k++] = leftArr[i++]
    while (j < rightArr.size) arr[k++] = rightArr[j++]
}
```

**관련 알고리즘**: Quick Sort, Tim Sort

---

<a id="strassen"></a>
## 3. Strassen's Matrix Multiplication (스트라센 행렬 곱셈)

**목적**: 행렬 곱셈을 더 빠르게 수행

**시간 복잡도**: O(n^2.807)

**공간 복잡도**: O(n²)

**특징**:
- 7번의 곱셈으로 2×2 행렬 곱 수행
- 일반적인 8번 → 7번으로 감소

**장점**:
- 큰 행렬에서 효율적
- 이론적으로 중요

**단점**:
- 작은 행렬에서 오버헤드
- 수치적 불안정성

**난이도**: 높음 | **사용 빈도**: ★☆☆☆☆

**Kotlin 코드**:
```kotlin
typealias Matrix = Array<IntArray>

fun strassen(a: Matrix, b: Matrix): Matrix {
    val n = a.size
    if (n == 1) {
        return arrayOf(intArrayOf(a[0][0] * b[0][0]))
    }

    val half = n / 2

    // 행렬 분할
    val a11 = subMatrix(a, 0, 0, half)
    val a12 = subMatrix(a, 0, half, half)
    val a21 = subMatrix(a, half, 0, half)
    val a22 = subMatrix(a, half, half, half)

    val b11 = subMatrix(b, 0, 0, half)
    val b12 = subMatrix(b, 0, half, half)
    val b21 = subMatrix(b, half, 0, half)
    val b22 = subMatrix(b, half, half, half)

    // 7개의 곱셈 (Strassen's 핵심)
    val m1 = strassen(add(a11, a22), add(b11, b22))
    val m2 = strassen(add(a21, a22), b11)
    val m3 = strassen(a11, subtract(b12, b22))
    val m4 = strassen(a22, subtract(b21, b11))
    val m5 = strassen(add(a11, a12), b22)
    val m6 = strassen(subtract(a21, a11), add(b11, b12))
    val m7 = strassen(subtract(a12, a22), add(b21, b22))

    // 결과 조합
    val c11 = add(subtract(add(m1, m4), m5), m7)
    val c12 = add(m3, m5)
    val c21 = add(m2, m4)
    val c22 = add(subtract(add(m1, m3), m2), m6)

    return combine(c11, c12, c21, c22)
}

private fun subMatrix(m: Matrix, row: Int, col: Int, size: Int): Matrix {
    return Array(size) { i -> IntArray(size) { j -> m[row + i][col + j] } }
}

private fun add(a: Matrix, b: Matrix): Matrix {
    val n = a.size
    return Array(n) { i -> IntArray(n) { j -> a[i][j] + b[i][j] } }
}

private fun subtract(a: Matrix, b: Matrix): Matrix {
    val n = a.size
    return Array(n) { i -> IntArray(n) { j -> a[i][j] - b[i][j] } }
}

private fun combine(c11: Matrix, c12: Matrix, c21: Matrix, c22: Matrix): Matrix {
    val half = c11.size
    val n = half * 2
    val result = Array(n) { IntArray(n) }

    for (i in 0 until half) {
        for (j in 0 until half) {
            result[i][j] = c11[i][j]
            result[i][j + half] = c12[i][j]
            result[i + half][j] = c21[i][j]
            result[i + half][j + half] = c22[i][j]
        }
    }

    return result
}
```

**관련 알고리즘**: 일반 행렬 곱셈

---

<a id="closest-pair"></a>
## 4. Closest Pair of Points (최근접 점 쌍)

**목적**: 2D 평면에서 가장 가까운 두 점 찾기

**시간 복잡도**: O(n log n)

**공간 복잡도**: O(n)

**특징**:
- 분할 정복으로 O(n log n) 달성
- Brute Force O(n²)보다 효율적

**장점**:
- 효율적인 기하 알고리즘
- 실제 응용에 유용

**단점**:
- 구현이 복잡

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
import kotlin.math.sqrt
import kotlin.math.min
import kotlin.math.abs

data class Point(val x: Double, val y: Double)

fun closestPair(points: List<Point>): Double {
    val sortedByX = points.sortedBy { it.x }
    return closestPairRec(sortedByX)
}

private fun closestPairRec(points: List<Point>): Double {
    val n = points.size
    if (n <= 3) return bruteForce(points)

    val mid = n / 2
    val midPoint = points[mid]

    val leftDist = closestPairRec(points.subList(0, mid))
    val rightDist = closestPairRec(points.subList(mid, n))
    var minDist = min(leftDist, rightDist)

    // 중간 영역 점들
    val strip = points.filter { abs(it.x - midPoint.x) < minDist }
        .sortedBy { it.y }

    // 스트립 내 최소 거리
    for (i in strip.indices) {
        var j = i + 1
        while (j < strip.size && strip[j].y - strip[i].y < minDist) {
            minDist = min(minDist, distance(strip[i], strip[j]))
            j++
        }
    }

    return minDist
}

private fun bruteForce(points: List<Point>): Double {
    var minDist = Double.MAX_VALUE
    for (i in points.indices) {
        for (j in i + 1 until points.size) {
            minDist = min(minDist, distance(points[i], points[j]))
        }
    }
    return minDist
}

private fun distance(p1: Point, p2: Point): Double {
    val dx = p1.x - p2.x
    val dy = p1.y - p2.y
    return sqrt(dx * dx + dy * dy)
}
```

**관련 알고리즘**: Convex Hull

---

<a id="karatsuba"></a>
## 5. Karatsuba Multiplication (카라츠바 곱셈)

**목적**: 큰 정수의 곱셈을 효율적으로 수행

**시간 복잡도**: O(n^1.585)

**공간 복잡도**: O(n)

**특징**:
- 3번의 곱셈으로 계산
- 일반적인 4번 → 3번으로 감소

**장점**:
- 큰 수 곱셈에 효율적
- 분할 정복의 좋은 예

**단점**:
- 작은 수에서 오버헤드

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
import java.math.BigInteger
import kotlin.math.max

fun karatsuba(x: BigInteger, y: BigInteger): BigInteger {
    val n = max(x.bitLength(), y.bitLength())

    // 베이스 케이스
    if (n <= 32) return x.multiply(y)

    val half = (n + 1) / 2

    // x = x1 * 2^half + x0
    // y = y1 * 2^half + y0
    val x1 = x.shiftRight(half)
    val x0 = x.subtract(x1.shiftLeft(half))
    val y1 = y.shiftRight(half)
    val y0 = y.subtract(y1.shiftLeft(half))

    // 3번의 재귀 곱셈
    val z2 = karatsuba(x1, y1)              // x1 * y1
    val z0 = karatsuba(x0, y0)              // x0 * y0
    val z1 = karatsuba(x1.add(x0), y1.add(y0))
        .subtract(z2).subtract(z0)           // (x1 + x0)(y1 + y0) - z2 - z0

    // 결과 조합: z2 * 2^(2*half) + z1 * 2^half + z0
    return z2.shiftLeft(2 * half)
        .add(z1.shiftLeft(half))
        .add(z0)
}

// 문자열 기반 구현 (이해를 위해)
fun karatsubaString(num1: String, num2: String): String {
    val n = max(num1.length, num2.length)
    if (n < 10) return (num1.toBigInteger() * num2.toBigInteger()).toString()

    // 같은 길이로 맞춤
    val x = num1.padStart(n, '0')
    val y = num2.padStart(n, '0')

    val half = n / 2

    val x1 = x.substring(0, n - half)
    val x0 = x.substring(n - half)
    val y1 = y.substring(0, n - half)
    val y0 = y.substring(n - half)

    val z2 = karatsubaString(x1, y1)
    val z0 = karatsubaString(x0, y0)
    val z1 = (karatsubaString(
        (x1.toBigInteger() + x0.toBigInteger()).toString(),
        (y1.toBigInteger() + y0.toBigInteger()).toString()
    ).toBigInteger() - z2.toBigInteger() - z0.toBigInteger()).toString()

    val result = z2.toBigInteger() * BigInteger.TEN.pow(2 * half) +
                 z1.toBigInteger() * BigInteger.TEN.pow(half) +
                 z0.toBigInteger()

    return result.toString()
}
```

**관련 알고리즘**: FFT 곱셈, Toom-Cook

