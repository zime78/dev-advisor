# 확률/스트림 알고리즘 (Probabilistic & Streaming Algorithms)

랜덤성, 스트림 처리, 근사 통계를 위한 확률적 자료구조와 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [fisher-yates-shuffle](#fisher-yates-shuffle) | Fisher-Yates Shuffle | 피셔-예이츠 셔플 | 낮음 |
| [reservoir-sampling](#reservoir-sampling) | Reservoir Sampling | 리저버 샘플링 | 중간 |
| [count-min-sketch](#count-min-sketch) | Count-Min Sketch | 카운트-민 스케치 | 중간 |
| [hyperloglog](#hyperloglog) | HyperLogLog | 하이퍼로그로그 | 높음 |

---

<a id="fisher-yates-shuffle"></a>
## 1. Fisher-Yates Shuffle (피셔-예이츠 셔플)

**목적**: 배열을 균등 분포로 무작위 섞기. 모든 n! 순열이 동일 확률로 나옴

**시간 복잡도**: O(n)

**공간 복잡도**: O(1) - 제자리 셔플

**특징**:
- 뒤에서 앞으로 진행
- 각 위치 i에 대해 [0..i]에서 무작위 인덱스 선택 후 교환
- Knuth shuffle이라고도 함

**장점**:
- 진정한 균등 분포 보장
- 제자리 (in-place)
- 매우 빠름

**단점**:
- 좋은 난수 생성기 필요
- 순차 접근 (병렬화 어려움)

**활용 예시**:
- 카드 게임
- 데이터셋 무작위 분할
- A/B 테스트 그룹 배정
- 무작위 샘플링

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import kotlin.random.Random

fun <T> fisherYatesShuffle(arr: Array<T>, rng: Random = Random.Default) {
    for (i in arr.size - 1 downTo 1) {
        val j = rng.nextInt(i + 1)
        val tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp
    }
}

fun fisherYatesInt(arr: IntArray, rng: Random = Random.Default) {
    for (i in arr.size - 1 downTo 1) {
        val j = rng.nextInt(i + 1)
        arr[i] = arr[j].also { arr[j] = arr[i] }
    }
}

// 잘못된 구현 (편향됨): rng.nextInt(arr.size) 사용 - 절대 금지
// 올바른 구현: rng.nextInt(i + 1) - [0..i] 범위
```

**관련 알고리즘**: Reservoir Sampling, Random Permutation

---

<a id="reservoir-sampling"></a>
## 2. Reservoir Sampling (리저버 샘플링)

**목적**: 전체 크기 N을 모르는 스트림에서 균등 확률로 k개 샘플링

**시간 복잡도**: O(n)

**공간 복잡도**: O(k)

**특징**:
- Algorithm R (Vitter)
- i번째 원소를 k/i 확률로 reservoir에 채택, 기존 원소를 균등 교체
- 모든 원소가 k/N 확률로 최종 선택됨

**장점**:
- 스트림 한 번 통과로 완료
- 전체 크기 사전 지식 불필요
- 메모리 O(k)만 사용

**단점**:
- 가중 샘플링은 변형 필요
- 분산 환경에선 추가 처리 필요

**활용 예시**:
- 로그 스트림 샘플링
- 빅데이터 임의 샘플
- 무한 스트림 통계
- 데이터베이스 무작위 행

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import kotlin.random.Random

class ReservoirSampler<T>(private val k: Int) {
    private val reservoir = arrayOfNulls<Any?>(k)
    private var count = 0
    private val rng = Random.Default

    @Suppress("UNCHECKED_CAST")
    fun add(item: T) {
        if (count < k) {
            reservoir[count] = item
        } else {
            val j = rng.nextInt(count + 1)
            if (j < k) reservoir[j] = item
        }
        count++
    }

    @Suppress("UNCHECKED_CAST")
    fun sample(): List<T> {
        val size = minOf(count, k)
        return List(size) { reservoir[it] as T }
    }
}

// 가중 샘플링 (Algorithm A-Res, Efraimidis–Spirakis)
data class Weighted<T>(val item: T, val weight: Double)

fun <T> weightedReservoir(stream: Iterable<Weighted<T>>, k: Int): List<T> {
    val rng = Random.Default
    // (key, item) 우선순위 큐 — key가 작은 것 제거
    val heap = java.util.PriorityQueue<Pair<Double, T>>(compareBy { it.first })
    for (w in stream) {
        val key = Math.pow(rng.nextDouble(), 1.0 / w.weight)
        if (heap.size < k) {
            heap.add(key to w.item)
        } else if (key > heap.peek().first) {
            heap.poll()
            heap.add(key to w.item)
        }
    }
    return heap.map { it.second }
}
```

**관련 알고리즘**: Fisher-Yates, Weighted Sampling

---

<a id="count-min-sketch"></a>
## 3. Count-Min Sketch (카운트-민 스케치)

**목적**: 스트림에서 각 원소의 빈도를 sublinear 메모리로 근사 추정

**시간 복잡도**: O(d) - d: 해시 함수 개수

**공간 복잡도**: O(w * d) - w: 너비, d: 깊이

**특징**:
- 2D 카운터 배열 + d개 독립 해시 함수
- update: 각 행에 카운터 +1
- estimate: 각 행 카운터의 최솟값
- 오차 ≤ ε * 총빈도, 확률 1-δ

**장점**:
- 매우 작은 메모리
- 빠른 update/query
- 병렬화/분산 합산 쉬움

**단점**:
- 과대 추정 (절대 과소 추정 안 함)
- 빈도가 낮은 원소 부정확
- 음의 카운트는 변형 필요 (Count-Min-Log)

**활용 예시**:
- 네트워크 트래픽 heavy hitter
- 검색 쿼리 빈도
- 추천 시스템 인기도
- DDoS 탐지

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.math.E
import kotlin.math.ceil
import kotlin.math.ln

class CountMinSketch(epsilon: Double, delta: Double) {
    val width: Int = ceil(E / epsilon).toInt()
    val depth: Int = ceil(ln(1.0 / delta)).toInt()
    private val table = Array(depth) { IntArray(width) }
    private val seeds = IntArray(depth) { it * 0x9E3779B9.toInt() + 0x12345 }

    private fun hash(item: String, seed: Int): Int {
        var h = seed
        for (c in item) h = h * 31 + c.code
        return ((h % width) + width) % width
    }

    fun add(item: String, count: Int = 1) {
        for (i in 0 until depth) {
            table[i][hash(item, seeds[i])] += count
        }
    }

    fun estimate(item: String): Int {
        var minCount = Int.MAX_VALUE
        for (i in 0 until depth) {
            minCount = minOf(minCount, table[i][hash(item, seeds[i])])
        }
        return minCount
    }

    fun merge(other: CountMinSketch) {
        require(width == other.width && depth == other.depth)
        for (i in 0 until depth) for (j in 0 until width) {
            table[i][j] += other.table[i][j]
        }
    }
}
```

**관련 알고리즘**: Bloom Filter, HyperLogLog, Count Sketch

---

<a id="hyperloglog"></a>
## 4. HyperLogLog (하이퍼로그로그)

**목적**: 스트림에서 서로 다른 원소(distinct count, 카디널리티)를 sublinear 메모리로 추정

**시간 복잡도**: O(1) - 원소당

**공간 복잡도**: O(2^p * 5비트) - p: 정밀도 (보통 14)

**특징**:
- 각 해시 값의 leading zero 개수 활용
- 2^p 개 버킷, 각 버킷은 최대 leading zero
- 추정: αₘ * m² / Σ 2^(-Mⱼ)
- 표준 오차 ≈ 1.04/√m

**장점**:
- 매우 작은 메모리 (수 KB로 수십억 카디널리티)
- 합산(merge) 가능 (분산 환경)
- 빠름

**단점**:
- 정확한 카운트 불가
- 작은 카디널리티에서 오차 큼 (linear counting 보완)
- 원소 자체 복원 불가

**활용 예시**:
- Unique 방문자 수
- Redis PFCOUNT
- BigQuery APPROX_COUNT_DISTINCT
- 분산 데이터베이스

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import kotlin.math.ln
import kotlin.math.pow

class HyperLogLog(private val p: Int = 14) {
    private val m: Int = 1 shl p
    private val registers = ByteArray(m)
    private val alpha: Double = when (m) {
        16 -> 0.673
        32 -> 0.697
        64 -> 0.709
        else -> 0.7213 / (1 + 1.079 / m)
    }

    private fun hash64(item: String): Long {
        var h = 0xcbf29ce484222325UL.toLong()
        val prime = 0x100000001b3UL.toLong()
        for (c in item) {
            h = h xor c.code.toLong()
            h *= prime
        }
        return h
    }

    fun add(item: String) {
        val h = hash64(item)
        val idx = (h ushr (64 - p)).toInt() and (m - 1)
        val w = (h shl p) or (1L shl (p - 1)) // 패딩으로 leading zero 한도 보장
        val leading = java.lang.Long.numberOfLeadingZeros(w) + 1
        if (leading.toByte() > registers[idx]) registers[idx] = leading.toByte()
    }

    fun cardinality(): Long {
        var sum = 0.0
        var zeros = 0
        for (r in registers) {
            sum += 2.0.pow(-r.toInt().toDouble())
            if (r.toInt() == 0) zeros++
        }
        var estimate = alpha * m * m / sum

        // Small range correction (linear counting)
        if (estimate <= 2.5 * m && zeros != 0) {
            estimate = m * ln(m.toDouble() / zeros)
        }
        return estimate.toLong()
    }

    fun merge(other: HyperLogLog) {
        require(p == other.p)
        for (i in 0 until m) {
            if (other.registers[i] > registers[i]) registers[i] = other.registers[i]
        }
    }
}
```

**관련 알고리즘**: LogLog, LinearCounting, MinHash

---
