# 자료구조 알고리즘 (Data Structure Algorithms)

분리 집합, 구간 쿼리, 균형 트리, 확률적 자료구조 등 고급 자료구조 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [union-find](#union-find) | Union-Find (Disjoint Set) | 분리 집합 | 낮음 |
| [segment-tree](#segment-tree) | Segment Tree | 세그먼트 트리 | 중간 |
| [fenwick-tree](#fenwick-tree) | Fenwick Tree (Binary Indexed Tree, BIT) | 펜윅 트리 | 중간 |
| [avl-tree](#avl-tree) | AVL Tree | AVL 트리 | 높음 |
| [red-black-tree](#red-black-tree) | Red-Black Tree | 레드-블랙 트리 | 높음 |
| [b-tree](#b-tree) | B-Tree | B-트리 | 높음 |
| [skip-list](#skip-list) | Skip List | 스킵 리스트 | 중간 |
| [lru](#lru) | LRU Cache | LRU 캐시 | 중간 |
| [bloom-filter](#bloom-filter) | Bloom Filter | 블룸 필터 | 중간 |

---

<a id="union-find"></a>
## 1. Union-Find (Disjoint Set, 분리 집합)

**목적**: 서로소 집합을 효율적으로 합치고 같은 집합 여부를 판정

**시간 복잡도**: O(α(n)) - 거의 상수 (Ackermann 역함수)

**공간 복잡도**: O(n)

**특징**:
- 경로 압축 (path compression)
- 랭크 기반 합치기 (union by rank)
- 트리로 집합 표현

**장점**:
- 거의 상수 시간 연산
- 구현 간단

**단점**:
- 분리(split) 연산 어려움
- 트리 구조 직접 추적 어려움

**활용 예시**:
- Kruskal MST
- 네트워크 연결성
- 동적 그래프 컴포넌트

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
class UnionFindDS(n: Int) {
    private val parent = IntArray(n) { it }
    private val rank = IntArray(n) { 0 }
    private val size = IntArray(n) { 1 }
    var components: Int = n
        private set

    fun find(x: Int): Int {
        if (parent[x] != x) {
            parent[x] = find(parent[x]) // 경로 압축
        }
        return parent[x]
    }

    fun union(x: Int, y: Int): Boolean {
        val px = find(x)
        val py = find(y)
        if (px == py) return false

        // rank가 큰 쪽을 루트로
        when {
            rank[px] < rank[py] -> {
                parent[px] = py
                size[py] += size[px]
            }
            rank[px] > rank[py] -> {
                parent[py] = px
                size[px] += size[py]
            }
            else -> {
                parent[py] = px
                size[px] += size[py]
                rank[px]++
            }
        }
        components--
        return true
    }

    fun connected(x: Int, y: Int): Boolean = find(x) == find(y)

    fun componentSize(x: Int): Int = size[find(x)]
}
```

**관련 알고리즘**: Kruskal MST, 동적 연결성

---

<a id="segment-tree"></a>
## 2. Segment Tree (세그먼트 트리)

**목적**: 구간 합/최소/최대 쿼리와 점 갱신을 모두 O(log n)에 처리

**시간 복잡도**:
| 구축 | 쿼리 | 갱신 |
|------|------|------|
| O(n) | O(log n) | O(log n) |

**공간 복잡도**: O(4n) ≈ O(n)

**특징**:
- 이진 트리 구조
- 구간 합/최소/최대/GCD 지원
- Lazy propagation 변형으로 구간 갱신도 O(log n)

**장점**:
- 빠른 구간 쿼리 + 갱신
- 다양한 모노이드 연산 지원

**단점**:
- Fenwick보다 메모리 4배
- 구현 길이

**활용 예시**:
- 구간 합/최소값 쿼리
- RMQ (Range Minimum Query)
- 누적 통계 추적

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
class SegmentTree(private val n: Int) {
    private val tree = LongArray(4 * n)

    fun build(arr: LongArray, node: Int = 1, start: Int = 0, end: Int = n - 1) {
        if (start == end) {
            tree[node] = arr[start]
            return
        }
        val mid = (start + end) / 2
        build(arr, node * 2, start, mid)
        build(arr, node * 2 + 1, mid + 1, end)
        tree[node] = tree[node * 2] + tree[node * 2 + 1]
    }

    fun update(idx: Int, value: Long, node: Int = 1, start: Int = 0, end: Int = n - 1) {
        if (start == end) {
            tree[node] = value
            return
        }
        val mid = (start + end) / 2
        if (idx <= mid) update(idx, value, node * 2, start, mid)
        else update(idx, value, node * 2 + 1, mid + 1, end)
        tree[node] = tree[node * 2] + tree[node * 2 + 1]
    }

    fun query(l: Int, r: Int, node: Int = 1, start: Int = 0, end: Int = n - 1): Long {
        if (r < start || end < l) return 0L
        if (l <= start && end <= r) return tree[node]
        val mid = (start + end) / 2
        return query(l, r, node * 2, start, mid) +
               query(l, r, node * 2 + 1, mid + 1, end)
    }
}

// Lazy propagation 변형 (구간 갱신)
class LazySegmentTree(private val n: Int) {
    private val tree = LongArray(4 * n)
    private val lazy = LongArray(4 * n)

    private fun push(node: Int, start: Int, end: Int) {
        if (lazy[node] != 0L) {
            tree[node] += (end - start + 1) * lazy[node]
            if (start != end) {
                lazy[node * 2] += lazy[node]
                lazy[node * 2 + 1] += lazy[node]
            }
            lazy[node] = 0L
        }
    }

    fun updateRange(l: Int, r: Int, value: Long, node: Int = 1, start: Int = 0, end: Int = n - 1) {
        push(node, start, end)
        if (r < start || end < l) return
        if (l <= start && end <= r) {
            lazy[node] += value
            push(node, start, end)
            return
        }
        val mid = (start + end) / 2
        updateRange(l, r, value, node * 2, start, mid)
        updateRange(l, r, value, node * 2 + 1, mid + 1, end)
        tree[node] = tree[node * 2] + tree[node * 2 + 1]
    }

    fun query(l: Int, r: Int, node: Int = 1, start: Int = 0, end: Int = n - 1): Long {
        if (r < start || end < l) return 0L
        push(node, start, end)
        if (l <= start && end <= r) return tree[node]
        val mid = (start + end) / 2
        return query(l, r, node * 2, start, mid) +
               query(l, r, node * 2 + 1, mid + 1, end)
    }
}
```

**관련 알고리즘**: Fenwick Tree, Sparse Table

---

<a id="fenwick-tree"></a>
## 3. Fenwick Tree (Binary Indexed Tree, BIT)

**목적**: 1D 배열의 prefix sum과 점 갱신을 O(log n)에 처리

**시간 복잡도**:
| 구축 | 쿼리 | 갱신 |
|------|------|------|
| O(n log n) | O(log n) | O(log n) |

**공간 복잡도**: O(n)

**특징**:
- 비트 연산(`i & -i`)으로 부모/자식 인덱싱
- 누적 합 전용 구조
- 1-indexed

**장점**:
- 매우 작은 메모리 (Segment Tree의 1/4)
- 구현 매우 짧음
- 캐시 효율 좋음

**단점**:
- 최소/최대 쿼리에는 부적합
- 구간 갱신은 추가 트릭 필요

**활용 예시**:
- 누적 합 쿼리
- 역순 쌍(inversion) 계산
- 좌표 압축 후 카운팅

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
class FenwickTree(private val n: Int) {
    private val tree = LongArray(n + 1)

    // 인덱스 i에 delta 더하기
    fun update(i: Int, delta: Long) {
        var x = i + 1 // 1-indexed
        while (x <= n) {
            tree[x] += delta
            x += x and -x
        }
    }

    // [0..i] 합
    fun prefix(i: Int): Long {
        var x = i + 1
        var sum = 0L
        while (x > 0) {
            sum += tree[x]
            x -= x and -x
        }
        return sum
    }

    // [l..r] 합
    fun range(l: Int, r: Int): Long = prefix(r) - if (l > 0) prefix(l - 1) else 0L
}

// 역순 쌍 카운트 예시
fun countInversions(arr: IntArray): Long {
    val sorted = arr.toSortedSet().toList()
    val rank = sorted.withIndex().associate { (i, v) -> v to i }
    val bit = FenwickTree(sorted.size)
    var inversions = 0L

    for (i in arr.indices.reversed()) {
        val r = rank[arr[i]]!!
        if (r > 0) inversions += bit.prefix(r - 1)
        bit.update(r, 1L)
    }
    return inversions
}
```

**관련 알고리즘**: Segment Tree, Merge Sort (역순 쌍)

---

<a id="avl-tree"></a>
## 4. AVL Tree (AVL 트리)

**목적**: 모든 노드의 좌우 서브트리 높이 차가 1 이하인 자가 균형 BST

**시간 복잡도**: O(log n) - 삽입/삭제/탐색 모두

**공간 복잡도**: O(n)

**특징**:
- 균형 인수 ∈ {-1, 0, 1}
- 회전 4종: LL, RR, LR, RL
- Red-Black보다 더 엄격한 균형

**장점**:
- 탐색이 매우 빠름 (더 균형잡힘)
- 읽기 위주 작업에 유리

**단점**:
- 삽입/삭제 시 회전 빈번
- 구현 복잡

**활용 예시**:
- 데이터베이스 인덱스
- 메모리 내 정렬된 컬렉션
- 범위 쿼리

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class AVLTree {
    class Node(var key: Int) {
        var height = 1
        var left: Node? = null
        var right: Node? = null
    }

    var root: Node? = null
        private set

    private fun height(n: Node?): Int = n?.height ?: 0
    private fun balanceFactor(n: Node?): Int = (n?.let { height(it.left) - height(it.right) }) ?: 0

    private fun updateHeight(n: Node) {
        n.height = 1 + maxOf(height(n.left), height(n.right))
    }

    private fun rotateRight(y: Node): Node {
        val x = y.left!!
        val t2 = x.right
        x.right = y
        y.left = t2
        updateHeight(y)
        updateHeight(x)
        return x
    }

    private fun rotateLeft(x: Node): Node {
        val y = x.right!!
        val t2 = y.left
        y.left = x
        x.right = t2
        updateHeight(x)
        updateHeight(y)
        return y
    }

    fun insert(key: Int) {
        root = insertRec(root, key)
    }

    private fun insertRec(node: Node?, key: Int): Node {
        if (node == null) return Node(key)

        when {
            key < node.key -> node.left = insertRec(node.left, key)
            key > node.key -> node.right = insertRec(node.right, key)
            else -> return node // 중복 허용 안 함
        }

        updateHeight(node)
        val bf = balanceFactor(node)

        // LL
        if (bf > 1 && key < node.left!!.key) return rotateRight(node)
        // RR
        if (bf < -1 && key > node.right!!.key) return rotateLeft(node)
        // LR
        if (bf > 1 && key > node.left!!.key) {
            node.left = rotateLeft(node.left!!)
            return rotateRight(node)
        }
        // RL
        if (bf < -1 && key < node.right!!.key) {
            node.right = rotateRight(node.right!!)
            return rotateLeft(node)
        }
        return node
    }

    fun contains(key: Int): Boolean {
        var cur = root
        while (cur != null) {
            cur = when {
                key < cur.key -> cur.left
                key > cur.key -> cur.right
                else -> return true
            }
        }
        return false
    }
}
```

**관련 알고리즘**: Red-Black Tree, Splay Tree

---

<a id="red-black-tree"></a>
## 5. Red-Black Tree (레드-블랙 트리)

**목적**: 색상 속성으로 균형을 유지하는 BST. AVL보다 회전이 적음

**시간 복잡도**: O(log n) - 삽입/삭제/탐색

**공간 복잡도**: O(n)

**특징**:
- 5가지 속성: (1) 모든 노드는 빨강/검정 (2) 루트는 검정 (3) 모든 NIL leaf는 검정 (4) 빨강 노드의 자식은 검정 (5) 임의의 노드에서 leaf까지 검정 노드 수 동일
- 삽입/삭제 후 색상 변경 + 회전으로 속성 복원
- 최대 높이 = 2 log2(n+1)

**장점**:
- 삽입/삭제 회전이 AVL보다 적음
- 쓰기 빈번한 작업에 유리

**단점**:
- AVL보다 탐색 약간 느림
- 구현 복잡 (case 분류 많음)

**활용 예시**:
- Java TreeMap/TreeSet
- C++ std::map/std::set
- Linux 커널 스케줄러

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
class RedBlackTree {
    enum class Color { RED, BLACK }

    class Node(var key: Int, var color: Color = Color.RED) {
        var left: Node? = null
        var right: Node? = null
        var parent: Node? = null
    }

    var root: Node? = null

    private fun rotateLeft(x: Node) {
        val y = x.right ?: return
        x.right = y.left
        y.left?.parent = x
        y.parent = x.parent
        when {
            x.parent == null -> root = y
            x === x.parent!!.left -> x.parent!!.left = y
            else -> x.parent!!.right = y
        }
        y.left = x
        x.parent = y
    }

    private fun rotateRight(x: Node) {
        val y = x.left ?: return
        x.left = y.right
        y.right?.parent = x
        y.parent = x.parent
        when {
            x.parent == null -> root = y
            x === x.parent!!.right -> x.parent!!.right = y
            else -> x.parent!!.left = y
        }
        y.right = x
        x.parent = y
    }

    fun insert(key: Int) {
        val z = Node(key)
        var y: Node? = null
        var x = root
        while (x != null) {
            y = x
            x = if (z.key < x.key) x.left else x.right
        }
        z.parent = y
        when {
            y == null -> root = z
            z.key < y.key -> y.left = z
            else -> y.right = z
        }
        fixInsert(z)
    }

    private fun fixInsert(z0: Node) {
        var z = z0
        while (z.parent?.color == Color.RED) {
            val parent = z.parent!!
            val grand = parent.parent ?: break
            if (parent === grand.left) {
                val uncle = grand.right
                if (uncle?.color == Color.RED) {
                    parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    grand.color = Color.RED
                    z = grand
                } else {
                    if (z === parent.right) {
                        z = parent
                        rotateLeft(z)
                    }
                    z.parent!!.color = Color.BLACK
                    grand.color = Color.RED
                    rotateRight(grand)
                }
            } else {
                val uncle = grand.left
                if (uncle?.color == Color.RED) {
                    parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    grand.color = Color.RED
                    z = grand
                } else {
                    if (z === parent.left) {
                        z = parent
                        rotateRight(z)
                    }
                    z.parent!!.color = Color.BLACK
                    grand.color = Color.RED
                    rotateLeft(grand)
                }
            }
        }
        root?.color = Color.BLACK
    }
}
```

**관련 알고리즘**: AVL Tree, 2-3-4 Tree

---

<a id="b-tree"></a>
## 6. B-Tree (B-트리)

**목적**: 한 노드에 다수 키를 저장하는 m차 균형 다진 트리. 디스크 I/O 최소화 목적

**시간 복잡도**: O(log_m n) - 탐색/삽입/삭제

**공간 복잡도**: O(n)

**특징**:
- 분기 수 m ∈ [⌈m/2⌉, m]
- 모든 leaf의 깊이 동일
- split: 키 m개 이상이면 중간 키를 부모로 올림
- merge: 키 ⌈m/2⌉-1 미만이면 형제와 병합

**장점**:
- 디스크 친화적 (블록 단위 I/O)
- 노드 당 키 다수 → 트리 깊이 얕음
- 범위 쿼리에 적합

**단점**:
- 메모리 내에서는 BST보다 오버헤드
- 구현 복잡

**활용 예시**:
- 데이터베이스 인덱스 (MySQL InnoDB, PostgreSQL)
- 파일 시스템 (NTFS, ext4, HFS+)
- B+Tree (leaf만 데이터 보관 변형)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class BTree(private val t: Int) { // 최소 차수
    class Node(val leaf: Boolean) {
        val keys = mutableListOf<Int>()
        val children = mutableListOf<Node>()
    }

    var root: Node = Node(true)

    fun search(key: Int): Boolean = search(root, key)

    private fun search(node: Node, key: Int): Boolean {
        var i = 0
        while (i < node.keys.size && key > node.keys[i]) i++
        if (i < node.keys.size && key == node.keys[i]) return true
        if (node.leaf) return false
        return search(node.children[i], key)
    }

    fun insert(key: Int) {
        val r = root
        if (r.keys.size == 2 * t - 1) {
            val s = Node(false)
            s.children.add(r)
            splitChild(s, 0)
            root = s
            insertNonFull(s, key)
        } else {
            insertNonFull(r, key)
        }
    }

    private fun splitChild(parent: Node, idx: Int) {
        val y = parent.children[idx]
        val z = Node(y.leaf)
        // 우측 t-1개 키 z로 이동
        z.keys.addAll(y.keys.subList(t, 2 * t - 1))
        if (!y.leaf) {
            z.children.addAll(y.children.subList(t, 2 * t))
            repeat(t) { y.children.removeAt(y.children.size - 1) }
        }
        val midKey = y.keys[t - 1]
        // y는 좌측 t-1개만 유지
        repeat(t) { y.keys.removeAt(y.keys.size - 1) }

        parent.children.add(idx + 1, z)
        parent.keys.add(idx, midKey)
    }

    private fun insertNonFull(node: Node, key: Int) {
        var i = node.keys.size - 1
        if (node.leaf) {
            while (i >= 0 && key < node.keys[i]) i--
            node.keys.add(i + 1, key)
        } else {
            while (i >= 0 && key < node.keys[i]) i--
            i++
            if (node.children[i].keys.size == 2 * t - 1) {
                splitChild(node, i)
                if (key > node.keys[i]) i++
            }
            insertNonFull(node.children[i], key)
        }
    }
}
```

**관련 알고리즘**: B+Tree, LSM Tree

---

<a id="skip-list"></a>
## 7. Skip List (스킵 리스트)

**목적**: 확률적으로 균형을 유지하는 정렬된 연결 리스트. 다층 인덱스로 O(log n) 탐색

**시간 복잡도**: O(log n) 기대값 - 탐색/삽입/삭제

**공간 복잡도**: O(n) 기대값

**특징**:
- 각 노드를 확률 p(보통 0.5)로 상위 레벨 승급
- 균형 트리 없이 O(log n) 달성
- 락프리 동시성 구현에 유리

**장점**:
- 균형 트리보다 구현 단순
- 동시성 제어 용이
- 캐시 친화적

**단점**:
- 확률적 보장 (최악 O(n) 가능)
- 메모리 오버헤드 (포인터 다수)

**활용 예시**:
- Redis Sorted Set (zset)
- LevelDB MemTable
- 동시성 정렬 컬렉션

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.random.Random

class SkipList(private val maxLevel: Int = 16, private val p: Double = 0.5) {
    class Node(val key: Int, level: Int) {
        val forward: Array<Node?> = arrayOfNulls(level + 1)
    }

    private val head = Node(Int.MIN_VALUE, maxLevel)
    private var level = 0

    private fun randomLevel(): Int {
        var lvl = 0
        while (Random.nextDouble() < p && lvl < maxLevel) lvl++
        return lvl
    }

    fun search(key: Int): Boolean {
        var cur: Node = head
        for (i in level downTo 0) {
            while (cur.forward[i]?.let { it.key < key } == true) {
                cur = cur.forward[i]!!
            }
        }
        cur = cur.forward[0] ?: return false
        return cur.key == key
    }

    fun insert(key: Int) {
        val update = arrayOfNulls<Node>(maxLevel + 1)
        var cur: Node = head
        for (i in level downTo 0) {
            while (cur.forward[i]?.let { it.key < key } == true) {
                cur = cur.forward[i]!!
            }
            update[i] = cur
        }

        val lvl = randomLevel()
        if (lvl > level) {
            for (i in level + 1..lvl) update[i] = head
            level = lvl
        }

        val newNode = Node(key, lvl)
        for (i in 0..lvl) {
            newNode.forward[i] = update[i]!!.forward[i]
            update[i]!!.forward[i] = newNode
        }
    }

    fun delete(key: Int): Boolean {
        val update = arrayOfNulls<Node>(maxLevel + 1)
        var cur: Node = head
        for (i in level downTo 0) {
            while (cur.forward[i]?.let { it.key < key } == true) {
                cur = cur.forward[i]!!
            }
            update[i] = cur
        }
        val target = cur.forward[0] ?: return false
        if (target.key != key) return false

        for (i in 0..level) {
            if (update[i]!!.forward[i] !== target) break
            update[i]!!.forward[i] = target.forward[i]
        }
        while (level > 0 && head.forward[level] == null) level--
        return true
    }
}
```

**관련 알고리즘**: Balanced BST, B-Tree

---

<a id="lru"></a>
## 8. LRU Cache (LRU 캐시)

**목적**: 가장 최근에 사용되지 않은 항목을 우선 제거하는 캐시. O(1) get/put

**시간 복잡도**: O(1) - get/put 모두

**공간 복잡도**: O(capacity)

**특징**:
- HashMap + Doubly Linked List 조합
- get/put 시 노드를 list head로 이동
- capacity 초과 시 tail 노드 제거

**장점**:
- 모든 연산 O(1)
- 시간 지역성 활용

**단점**:
- 메모리 오버헤드 (포인터 2개/노드)
- 단순 빈도 기반 정책엔 부적합 (LFU 별도)

**활용 예시**:
- HTTP 응답 캐시
- DB 쿼리 캐시
- 페이지 교체 알고리즘

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
class LRUCache<K, V>(private val capacity: Int) {
    private class DLNode<K, V>(val key: K, var value: V) {
        var prev: DLNode<K, V>? = null
        var next: DLNode<K, V>? = null
    }

    private val map = HashMap<K, DLNode<K, V>>()
    private val head = DLNode<K, V>(dummyKey(), dummyValue())
    private val tail = DLNode<K, V>(dummyKey(), dummyValue())

    init {
        head.next = tail
        tail.prev = head
    }

    @Suppress("UNCHECKED_CAST")
    private fun dummyKey(): K = null as K
    @Suppress("UNCHECKED_CAST")
    private fun dummyValue(): V = null as V

    private fun remove(node: DLNode<K, V>) {
        node.prev!!.next = node.next
        node.next!!.prev = node.prev
    }

    private fun addToHead(node: DLNode<K, V>) {
        node.prev = head
        node.next = head.next
        head.next!!.prev = node
        head.next = node
    }

    fun get(key: K): V? {
        val node = map[key] ?: return null
        remove(node)
        addToHead(node)
        return node.value
    }

    fun put(key: K, value: V) {
        val existing = map[key]
        if (existing != null) {
            existing.value = value
            remove(existing)
            addToHead(existing)
            return
        }
        if (map.size == capacity) {
            val lru = tail.prev!!
            remove(lru)
            map.remove(lru.key)
        }
        val node = DLNode(key, value)
        addToHead(node)
        map[key] = node
    }

    fun size(): Int = map.size
}
```

**관련 알고리즘**: LFU Cache, ARC

---

<a id="bloom-filter"></a>
## 9. Bloom Filter (블룸 필터)

**목적**: 집합에 원소가 있는지 확률적으로 판정. "없음"은 확실, "있음"은 false positive 가능

**시간 복잡도**: O(k) - k: 해시 함수 개수

**공간 복잡도**: O(m) - m: 비트 배열 크기

**특징**:
- k개의 서로 다른 해시 함수
- 비트 배열에 모두 1로 표시
- false positive 확률 ≈ (1 - e^(-kn/m))^k
- 삭제 불가 (Counting Bloom Filter 별도)

**장점**:
- 메모리 매우 효율적
- 빠른 멤버십 테스트
- 추가는 O(k)

**단점**:
- false positive 존재
- 삭제 불가능 (기본형)
- 정확한 원소 복원 불가

**활용 예시**:
- 캐시 미스 사전 차단
- 중복 URL 필터 (웹 크롤러)
- DB join 사전 필터링 (BigQuery, Cassandra)
- 비밀번호 유출 검사

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.BitSet

class BloomFilter(private val size: Int, private val numHashes: Int) {
    private val bits = BitSet(size)

    private fun hash(value: String, seed: Int): Int {
        var h = seed
        for (c in value) {
            h = h * 31 + c.code
        }
        return ((h % size) + size) % size
    }

    fun add(value: String) {
        for (i in 0 until numHashes) {
            bits.set(hash(value, i + 1))
        }
    }

    fun mightContain(value: String): Boolean {
        for (i in 0 until numHashes) {
            if (!bits.get(hash(value, i + 1))) return false
        }
        return true // false positive 가능
    }

    fun estimatedFalsePositiveRate(insertedCount: Int): Double {
        // (1 - e^(-k * n / m))^k
        val exp = kotlin.math.exp(-numHashes.toDouble() * insertedCount / size)
        return kotlin.math.pow(1.0 - exp, numHashes.toDouble())
    }

    companion object {
        // 원하는 false positive rate과 예상 원소 수로 최적 파라미터 계산
        fun optimalParameters(expectedItems: Int, falsePositiveRate: Double): Pair<Int, Int> {
            val m = (-expectedItems * kotlin.math.ln(falsePositiveRate) /
                     (kotlin.math.ln(2.0) * kotlin.math.ln(2.0))).toInt()
            val k = ((m.toDouble() / expectedItems) * kotlin.math.ln(2.0)).toInt()
            return m to k.coerceAtLeast(1)
        }
    }
}
```

**관련 알고리즘**: Cuckoo Filter, Count-Min Sketch

---
