# 탐욕 알고리즘 (Greedy Algorithms)

각 단계에서 지역적으로 최적인 선택을 하여 전체적으로 최적의 해를 구하는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [activity-selection](#activity-selection) | Activity Selection | 활동 선택 | 낮음 |
| [huffman](#huffman) | Huffman Coding | 허프만 코딩 | 중간 |
| [fractional-knapsack](#fractional-knapsack) | Fractional Knapsack | 분할 배낭 | 낮음 |
| [job-sequencing](#job-sequencing) | Job Sequencing with Deadlines | 작업 순서화 | 중간 |
| [optimal-merge-pattern](#optimal-merge-pattern) | Optimal Merge Pattern | 최적 병합 패턴 | 중간 |

---

<a id="activity-selection"></a>
## 1. Activity Selection (활동 선택)

**목적**: 겹치지 않는 최대 개수의 활동 선택

**시간 복잡도**: O(n log n) - 정렬 포함

**공간 복잡도**: O(1)

**특징**:
- 종료 시간 기준 정렬
- 탐욕적 선택 정당성 증명 가능

**장점**:
- 간단하고 효율적
- 최적해 보장

**단점**:
- 특정 조건에서만 최적

**활용 예시**:
- 회의실 배정
- 작업 스케줄링
- 자원 할당

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
data class Activity(val start: Int, val end: Int, val name: String = "")

fun activitySelection(activities: List<Activity>): List<Activity> {
    if (activities.isEmpty()) return emptyList()

    // 종료 시간 기준 정렬
    val sorted = activities.sortedBy { it.end }
    val selected = mutableListOf<Activity>()

    selected.add(sorted[0])
    var lastEnd = sorted[0].end

    for (i in 1 until sorted.size) {
        if (sorted[i].start >= lastEnd) {
            selected.add(sorted[i])
            lastEnd = sorted[i].end
        }
    }

    return selected
}

// 가중치가 있는 활동 선택 (DP 필요)
data class WeightedActivity(val start: Int, val end: Int, val weight: Int)

fun weightedActivitySelection(activities: List<WeightedActivity>): Int {
    if (activities.isEmpty()) return 0

    val sorted = activities.sortedBy { it.end }
    val n = sorted.size
    val dp = IntArray(n)

    dp[0] = sorted[0].weight

    for (i in 1 until n) {
        // 포함하지 않는 경우
        val exclude = dp[i - 1]

        // 포함하는 경우
        var include = sorted[i].weight
        val lastCompatible = findLastCompatible(sorted, i)
        if (lastCompatible != -1) {
            include += dp[lastCompatible]
        }

        dp[i] = maxOf(include, exclude)
    }

    return dp[n - 1]
}

private fun findLastCompatible(activities: List<WeightedActivity>, index: Int): Int {
    for (i in index - 1 downTo 0) {
        if (activities[i].end <= activities[index].start) {
            return i
        }
    }
    return -1
}
```

**관련 알고리즘**: Job Sequencing, Interval Scheduling

---

<a id="huffman"></a>
## 2. Huffman Coding (허프만 코딩)

**목적**: 가변 길이 접두사 코드로 데이터 압축

**시간 복잡도**: O(n log n)

**공간 복잡도**: O(n)

**특징**:
- 빈도 기반 최적 코딩
- 접두사 자유 코드

**장점**:
- 최적 압축률
- 무손실 압축

**단점**:
- 코드 테이블 저장 필요

**활용 예시**:
- 파일 압축 (ZIP, GZIP)
- JPEG 이미지 압축
- 데이터 전송

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import java.util.PriorityQueue

sealed class HuffmanNode : Comparable<HuffmanNode> {
    abstract val freq: Int

    data class Leaf(val char: Char, override val freq: Int) : HuffmanNode()
    data class Internal(
        val left: HuffmanNode,
        val right: HuffmanNode,
        override val freq: Int
    ) : HuffmanNode()

    override fun compareTo(other: HuffmanNode): Int = freq.compareTo(other.freq)
}

fun buildHuffmanTree(frequencies: Map<Char, Int>): HuffmanNode? {
    if (frequencies.isEmpty()) return null

    val pq = PriorityQueue<HuffmanNode>()
    frequencies.forEach { (char, freq) ->
        pq.add(HuffmanNode.Leaf(char, freq))
    }

    while (pq.size > 1) {
        val left = pq.poll()
        val right = pq.poll()
        pq.add(HuffmanNode.Internal(left, right, left.freq + right.freq))
    }

    return pq.poll()
}

fun generateCodes(root: HuffmanNode?): Map<Char, String> {
    val codes = mutableMapOf<Char, String>()

    fun traverse(node: HuffmanNode, code: String) {
        when (node) {
            is HuffmanNode.Leaf -> codes[node.char] = code.ifEmpty { "0" }
            is HuffmanNode.Internal -> {
                traverse(node.left, code + "0")
                traverse(node.right, code + "1")
            }
        }
    }

    root?.let { traverse(it, "") }
    return codes
}

fun huffmanEncode(text: String): Pair<String, HuffmanNode?> {
    val frequencies = text.groupingBy { it }.eachCount()
    val tree = buildHuffmanTree(frequencies)
    val codes = generateCodes(tree)

    val encoded = text.map { codes[it] ?: "" }.joinToString("")
    return encoded to tree
}

fun huffmanDecode(encoded: String, tree: HuffmanNode?): String {
    if (tree == null || encoded.isEmpty()) return ""

    val result = StringBuilder()
    var current = tree

    for (bit in encoded) {
        current = when (current) {
            is HuffmanNode.Internal -> {
                if (bit == '0') current.left else current.right
            }
            is HuffmanNode.Leaf -> {
                result.append(current.char)
                if (bit == '0') (tree as HuffmanNode.Internal).left
                else (tree as HuffmanNode.Internal).right
            }
        }

        if (current is HuffmanNode.Leaf) {
            result.append(current.char)
            current = tree
        }
    }

    return result.toString()
}
```

**관련 알고리즘**: Shannon-Fano, Arithmetic Coding

---

<a id="fractional-knapsack"></a>
## 3. Fractional Knapsack (분할 배낭)

**목적**: 물건을 분할하여 최대 가치 선택

**시간 복잡도**: O(n log n)

**공간 복잡도**: O(1)

**특징**:
- 물건 분할 가능
- 가치/무게 비율로 정렬

**장점**:
- 간단한 탐욕 해법
- 최적해 보장

**단점**:
- 0/1 배낭 문제에는 적용 불가

**활용 예시**:
- 자원 배분
- 투자 분산

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
data class Item(val weight: Double, val value: Double) {
    val ratio: Double = value / weight
}

fun fractionalKnapsack(items: List<Item>, capacity: Double): Double {
    // 가치/무게 비율로 내림차순 정렬
    val sorted = items.sortedByDescending { it.ratio }

    var remainingCapacity = capacity
    var totalValue = 0.0

    for (item in sorted) {
        if (remainingCapacity <= 0) break

        if (item.weight <= remainingCapacity) {
            // 전체 아이템 선택
            totalValue += item.value
            remainingCapacity -= item.weight
        } else {
            // 분할하여 선택
            totalValue += item.ratio * remainingCapacity
            remainingCapacity = 0.0
        }
    }

    return totalValue
}

// 선택한 아이템 추적
fun fractionalKnapsackWithItems(
    items: List<Item>,
    capacity: Double
): Pair<Double, List<Pair<Item, Double>>> {
    val sorted = items.sortedByDescending { it.ratio }
    val selected = mutableListOf<Pair<Item, Double>>()

    var remainingCapacity = capacity
    var totalValue = 0.0

    for (item in sorted) {
        if (remainingCapacity <= 0) break

        if (item.weight <= remainingCapacity) {
            totalValue += item.value
            remainingCapacity -= item.weight
            selected.add(item to 1.0) // 100% 선택
        } else {
            val fraction = remainingCapacity / item.weight
            totalValue += item.value * fraction
            remainingCapacity = 0.0
            selected.add(item to fraction)
        }
    }

    return totalValue to selected
}
```

**관련 알고리즘**: 0/1 Knapsack (DP)

---

<a id="job-sequencing"></a>
## 4. Job Sequencing with Deadlines (작업 순서화)

**목적**: 마감 시간 내에 최대 이익 작업 수행

**시간 복잡도**: O(n²) 또는 O(n log n) - Union-Find 사용

**공간 복잡도**: O(n)

**특징**:
- 이익 기준 정렬
- 가능한 가장 늦은 슬롯에 배치

**장점**:
- 최대 이익 보장
- 직관적인 해법

**단점**:
- O(n²) 기본 구현

**활용 예시**:
- 작업 스케줄링
- 마감일 관리

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
data class Job(val id: String, val deadline: Int, val profit: Int)

fun jobSequencing(jobs: List<Job>): Pair<Int, List<Job>> {
    // 이익 기준 내림차순 정렬
    val sorted = jobs.sortedByDescending { it.profit }
    val maxDeadline = jobs.maxOfOrNull { it.deadline } ?: 0

    val slots = arrayOfNulls<Job>(maxDeadline)
    var totalProfit = 0
    val scheduled = mutableListOf<Job>()

    for (job in sorted) {
        // 마감 시간 직전부터 빈 슬롯 찾기
        for (slot in (job.deadline - 1) downTo 0) {
            if (slots[slot] == null) {
                slots[slot] = job
                totalProfit += job.profit
                scheduled.add(job)
                break
            }
        }
    }

    return totalProfit to scheduled
}

// Union-Find 최적화 버전 O(n log n)
class JobSchedulerOptimized(maxDeadline: Int) {
    private val parent = IntArray(maxDeadline + 1) { it }

    fun find(x: Int): Int {
        if (parent[x] != x) {
            parent[x] = find(parent[x])
        }
        return parent[x]
    }

    fun getSlot(deadline: Int): Int {
        val slot = find(deadline)
        if (slot == 0) return -1 // 슬롯 없음
        parent[slot] = find(slot - 1)
        return slot
    }
}

fun jobSequencingOptimized(jobs: List<Job>): Pair<Int, List<Job>> {
    val sorted = jobs.sortedByDescending { it.profit }
    val maxDeadline = jobs.maxOfOrNull { it.deadline } ?: 0

    val scheduler = JobSchedulerOptimized(maxDeadline)
    var totalProfit = 0
    val scheduled = mutableListOf<Job>()

    for (job in sorted) {
        val slot = scheduler.getSlot(job.deadline)
        if (slot != -1) {
            totalProfit += job.profit
            scheduled.add(job)
        }
    }

    return totalProfit to scheduled
}
```

**관련 알고리즘**: Activity Selection, Union-Find

---

<a id="optimal-merge-pattern"></a>
## 5. Optimal Merge Pattern (최적 병합 패턴)

**목적**: 파일들을 최소 비용으로 병합

**시간 복잡도**: O(n log n)

**공간 복잡도**: O(n)

**특징**:
- 가장 작은 두 파일 먼저 병합
- 허프만 알고리즘과 유사

**장점**:
- 최적 병합 순서 도출
- 총 비용 최소화

**단점**:
- 특정 문제에만 적용

**활용 예시**:
- 파일 병합
- 외부 정렬

**난이도**: 중간 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
import java.util.PriorityQueue

fun optimalMerge(fileSizes: List<Int>): Int {
    if (fileSizes.size <= 1) return 0

    val pq = PriorityQueue<Int>()
    pq.addAll(fileSizes)

    var totalCost = 0

    while (pq.size > 1) {
        val first = pq.poll()
        val second = pq.poll()
        val merged = first + second

        totalCost += merged
        pq.add(merged)
    }

    return totalCost
}

// 병합 순서 추적
sealed class MergeTree {
    data class Leaf(val size: Int) : MergeTree()
    data class Node(val left: MergeTree, val right: MergeTree, val size: Int) : MergeTree()

    fun totalSize(): Int = when (this) {
        is Leaf -> size
        is Node -> size
    }
}

fun optimalMergeWithTree(fileSizes: List<Int>): Pair<Int, MergeTree?> {
    if (fileSizes.isEmpty()) return 0 to null
    if (fileSizes.size == 1) return 0 to MergeTree.Leaf(fileSizes[0])

    val pq = PriorityQueue<MergeTree>(compareBy { it.totalSize() })
    fileSizes.forEach { pq.add(MergeTree.Leaf(it)) }

    var totalCost = 0

    while (pq.size > 1) {
        val first = pq.poll()
        val second = pq.poll()
        val mergedSize = first.totalSize() + second.totalSize()

        totalCost += mergedSize
        pq.add(MergeTree.Node(first, second, mergedSize))
    }

    return totalCost to pq.poll()
}

// 병합 순서 출력
fun printMergeOrder(tree: MergeTree, indent: String = "") {
    when (tree) {
        is MergeTree.Leaf -> println("${indent}File(${tree.size})")
        is MergeTree.Node -> {
            println("${indent}Merge(${tree.size})")
            printMergeOrder(tree.left, "$indent  ")
            printMergeOrder(tree.right, "$indent  ")
        }
    }
}
```

**관련 알고리즘**: Huffman Coding, External Sorting

