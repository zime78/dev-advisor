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
| [binary-heap](#binary-heap) | Binary Heap / Priority Queue | 이진 힙 / 우선순위 큐 | 중간 |
| [persistent-data-structures](#persistent-data-structures) | Persistent Data Structures (Persistent Segment Tree) | 영속 자료구조 | 높음 |
| [treap-splay](#treap-splay) | Treap / Splay Tree | 트립 / 스플레이 트리 | 높음 |
| [hash-collision-resolution](#hash-collision-resolution) | Hash Table Collision Resolution | 해시 테이블 충돌 처리 | 중간 |
| [rope-gap-buffer](#rope-gap-buffer) | Rope / Gap Buffer / Piece Table | 로프 / 갭 버퍼 / 피스 테이블 | 중간 |
| [advanced-heaps](#advanced-heaps) | Advanced Heaps (Fibonacci / Binomial / Pairing) | 고급 힙 | 높음 |
| [order-statistics-tree](#order-statistics-tree) | Order-Statistics Tree / Interval Tree | 순위 통계 트리 / 구간 트리 | 높음 |
| [van-emde-boas](#van-emde-boas) | van Emde Boas Tree / y-fast Trie | 반 엠데 보아스 트리 | 높음 |

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

<a id="binary-heap"></a>
## 10. Binary Heap (이진 힙 / 우선순위 큐)

**목적**: 최소(최대) 원소를 O(1) 조회, 삽입/삭제를 O(log n)에 지원하는 우선순위 큐 자료구조

**시간 복잡도**: peek O(1), push/pop O(log n), build-heap O(n), decrease-key O(log n)

**공간 복잡도**: O(n) (배열 1개, 포인터 없음)

**특징**:
- 완전 이진 트리를 배열로 표현: 부모 i → 자식 2i+1, 2i+2
- 힙 속성: 부모 ≤ 자식(min-heap) 또는 부모 ≥ 자식(max-heap)
- sift-up(삽입), sift-down(삭제), Floyd build-heap O(n)
- d-ary heap(자식 d개)로 push 비용↓ pop 비용↑ 조정 가능
- JDK `java.util.PriorityQueue`, Kotlin 표준에 내장

**장점**:
- 간단한 배열 구현, 캐시 친화적
- Dijkstra / Prim / Huffman / 이벤트 시뮬레이션의 핵심 빌딩블록
- top-k, 스트리밍 중앙값(두 힙)에 활용

**단점**:
- 임의 원소 검색/삭제 O(n) (위치 인덱스 별도 관리 → indexed PQ)
- decrease-key 에 핸들 필요 (Fibonacci heap 이 이론상 O(1))
- 정렬 순회 불가(부분 순서만 보장)

**활용 예시**:
- Dijkstra / Prim 최단경로·MST 우선순위 큐
- 작업 스케줄러, 이벤트 큐
- top-k, 스트리밍 백분위수(min-heap + max-heap)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 배열 기반 이진 최소 힙
class BinaryMinHeap {
    private val data = ArrayList<Int>()
    val size get() = data.size
    fun peek(): Int = data[0]

    fun push(x: Int) { data.add(x); siftUp(data.size - 1) }

    fun pop(): Int {
        val top = data[0]
        val last = data.removeAt(data.size - 1)
        if (data.isNotEmpty()) { data[0] = last; siftDown(0) }
        return top
    }

    private fun siftUp(i0: Int) {
        var i = i0
        while (i > 0) {
            val p = (i - 1) / 2
            if (data[p] <= data[i]) break
            swap(i, p); i = p
        }
    }

    private fun siftDown(i0: Int) {
        var i = i0; val n = data.size
        while (true) {
            val l = 2 * i + 1; val r = 2 * i + 2; var s = i
            if (l < n && data[l] < data[s]) s = l
            if (r < n && data[r] < data[s]) s = r
            if (s == i) break
            swap(i, s); i = s
        }
    }

    private fun swap(i: Int, j: Int) { val t = data[i]; data[i] = data[j]; data[j] = t }

    companion object {
        // Floyd build-heap: O(n)
        fun heapify(arr: IntArray): BinaryMinHeap {
            val h = BinaryMinHeap()
            h.data.addAll(arr.toList())
            for (i in arr.size / 2 - 1 downTo 0) h.siftDown(i)
            return h
        }
    }
}

// 실무: java.util.PriorityQueue 사용 (Comparator 로 min/max 전환)
// val pq = java.util.PriorityQueue<Int>()                 // min-heap
// val maxPq = java.util.PriorityQueue<Int>(reverseOrder()) // max-heap
```

**관련 알고리즘**: Heap Sort, Dijkstra, Prim, Huffman, Quickselect

---

<a id="persistent-data-structures"></a>
## 11. Persistent Data Structures (Persistent Segment Tree) (영속 자료구조)

**목적**: 갱신할 때마다 이전 버전을 그대로 보존하여 임의 과거 버전을 그대로 조회할 수 있는 영속(persistent) 자료구조를 구축한다.

**시간 복잡도**: 갱신/조회 O(log n) per version (점 갱신 기준)

**공간 복잡도**: 갱신당 O(log n) 추가 (전체 m회 갱신 시 O(n + m log n))

**특징**:
- 경로 복사(path copying): 갱신 시 루트에서 잎까지의 경로 위 노드만 새로 만들고, 변경되지 않은 서브트리는 이전 버전 노드를 공유(shared)한다
- 각 버전은 자신만의 루트를 가지며, 버전 r의 루트로 진입하면 그 시점의 트리 전체를 불변(immutable)하게 본다
- 함수형 영속성(fully persistent의 부분 집합인 partially persistent): 과거 버전 읽기 가능, 일반적인 구현은 가장 최신 버전 기준으로 새 버전을 파생
- 노드는 한 번 만들면 수정하지 않으므로(immutable) 구조 공유가 안전하다
- 두 버전 루트의 차이(prefix sum 형태)를 이용하면 부분 배열에 대한 k번째 수(k-th smallest)를 O(log n)에 질의할 수 있다(merge sort tree 대안)

**장점**:
- 모든 과거 버전을 O(log n) 추가 공간으로 보존 — 전체 복사 O(n) 대비 메모리 효율적
- 버전 롤백/스냅샷이 포인터(루트) 교체만으로 O(1)
- 불변 구조라 동시성/함수형 환경에서 안전하게 공유 가능
- 정적 배열의 구간 k번째 수, 구간 distinct count 등 오프라인 난제를 온라인으로 해결

**단점**:
- 노드마다 자식 포인터를 명시 저장해야 하므로 일반 배열 기반 세그먼트 트리보다 상수 메모리가 큼
- 구현이 까다롭고(노드 풀 관리, 인덱스 누수) 디버깅이 어려움
- 영속 + lazy propagation(구간 갱신) 결합은 구현 복잡도가 크게 증가
- 캐시 지역성이 떨어져 동일 연산 대비 상수 인자가 큼

**활용 예시**:
- 구간 [l, r]의 k번째로 작은 수 질의 (정렬 후 prefix 버전 차이 이용)
- 버전 관리 에디터/DB의 시점 조회(point-in-time), undo/redo 스냅샷
- 함수형 언어(immutable) 컬렉션의 효율적 갱신
- 온라인 구간 통계(특정 값 이하 개수, distinct 개수 등)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 영속 세그먼트 트리: 노드 풀 기반, 경로 복사로 버전별 합 보존
class PersistentSegTree(private val n: Int) {
    private val left = ArrayList<Int>()   // 노드의 왼쪽 자식 인덱스
    private val right = ArrayList<Int>()   // 노드의 오른쪽 자식 인덱스
    private val sum = ArrayList<Long>()     // 서브트리 합
    val roots = ArrayList<Int>()            // roots[v] = 버전 v의 루트 노드

    private fun newNode(l: Int, r: Int, s: Long): Int {
        left.add(l); right.add(r); sum.add(s)
        return sum.size - 1
    }

    // 빈 트리(버전 0) 빌드
    private fun build(lo: Int, hi: Int): Int {
        if (lo == hi) return newNode(-1, -1, 0)
        val mid = (lo + hi) / 2
        val lc = build(lo, mid); val rc = build(mid + 1, hi)
        return newNode(lc, rc, 0)
    }

    init { roots.add(build(0, n - 1)) }

    // 이전 노드 prev 를 기반으로 pos 에 delta 를 더한 새 노드 반환(경로만 복사)
    private fun update(prev: Int, lo: Int, hi: Int, pos: Int, delta: Long): Int {
        if (lo == hi) return newNode(-1, -1, sum[prev] + delta)
        val mid = (lo + hi) / 2
        return if (pos <= mid) {
            val lc = update(left[prev], lo, mid, pos, delta)
            newNode(lc, right[prev], sum[lc] + sum[right[prev]])
        } else {
            val rc = update(right[prev], mid + 1, hi, pos, delta)
            newNode(left[prev], rc, sum[left[prev]] + sum[rc])
        }
    }

    // 최신 버전을 기반으로 새 버전 생성 후 roots 에 등록
    fun update(pos: Int, delta: Long) {
        roots.add(update(roots.last(), 0, n - 1, pos, delta))
    }

    private fun query(node: Int, lo: Int, hi: Int, l: Int, r: Int): Long {
        if (r < lo || hi < l) return 0
        if (l <= lo && hi <= r) return sum[node]
        val mid = (lo + hi) / 2
        return query(left[node], lo, mid, l, r) + query(right[node], mid + 1, hi, l, r)
    }

    // 버전 v 시점의 구간 [l, r] 합
    fun query(v: Int, l: Int, r: Int): Long = query(roots[v], 0, n - 1, l, r)
}
```

**관련 알고리즘**: Segment Tree, Fenwick Tree (Binary Indexed Tree), Merge Sort Tree, Wavelet Tree

---

<a id="treap-splay"></a>
## 12. Treap / Splay Tree (트립 / 스플레이 트리)

**목적**: 회전 기반 자기조정/랜덤화 BST로, 균형을 명시적으로 유지하지 않고도 기댓값/amortized O(log n) 연산을 보장

**시간 복잡도**: Treap O(log n) 기댓값, Splay O(log n) amortized (최악 O(n))

**공간 복잡도**: O(n) (재귀/스택 O(log n))

**특징**:
- Treap(Aragon & Seidel, 1989): 각 노드에 BST 키 + 랜덤 heap 우선순위를 부여 — 키로는 BST, 우선순위로는 heap 불변식을 동시 만족시켜 기댓값 균형 달성
- Splay Tree(Sleator & Tarjan, 1985): 접근한 노드를 zig / zig-zig / zig-zag 회전으로 루트까지 끌어올려(splay) amortized O(log n) 보장, 별도 균형 정보(색·높이·우선순위) 불필요
- Treap의 우선순위가 입력 순서와 무관하게 무작위로 정해지면, 트리 구조는 키를 우선순위 순으로 삽입한 무작위 BST와 동치 → 기댓값 높이 O(log n)
- Cartesian Tree: (키, 우선순위) 쌍으로부터 결정되는 트리 — Treap은 우선순위를 난수로 둔 Cartesian Tree이며, split/merge 연산의 기반 구조
- Splay는 최근 접근 원소가 루트 근처에 모이는 지역성(working-set) 이점이 있고, Treap은 split/merge로 구간 분할·병합·순위 질의에 유리

**장점**:
- 구현이 AVL/Red-Black보다 단순 (특히 Treap의 split/merge 기반 변형)
- Treap은 입력에 적대적 패턴이 와도 무작위 우선순위로 기댓값 균형 유지
- Splay는 자주 접근하는 원소에 빠르게 도달(지역성)하고 추가 균형 메타데이터가 없음

**단점**:
- 둘 다 최악의 경우 O(n)이 될 수 있음 (Treap은 확률적으로 희박, Splay는 단일 연산 기준)
- Splay는 읽기(검색)에도 트리 구조를 변경해 동시성/캐시·불변 공유에 불리
- Treap은 양질의 난수원이 필요하고, 상수 인자가 균형 트리보다 다소 큼

**활용 예시**:
- 순서 통계(k번째 원소)·구간 분할/병합이 필요한 동적 시퀀스 (Treap split/merge)
- 자주 조회되는 키가 편중된 캐시·심볼 테이블 (Splay의 지역성 활용)
- 랜덤화 자료구조 교육·경시(PS)에서 균형 BST 대체

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.random.Random

// Treap: BST 키 + 랜덤 heap 우선순위. split/merge 로 삽입·삭제 구현
class Treap {
    private class Node(val key: Int) {
        val priority = Random.nextInt()  // 무작위 heap 우선순위
        var left: Node? = null
        var right: Node? = null
    }

    private var root: Node? = null

    // 키 기준으로 t 를 (< key) 와 (>= key) 두 트리로 분할
    private fun split(t: Node?, key: Int): Pair<Node?, Node?> {
        if (t == null) return null to null
        return if (t.key < key) {
            val (l, r) = split(t.right, key)
            t.right = l
            t to r
        } else {
            val (l, r) = split(t.left, key)
            t.left = r
            l to t
        }
    }

    // a 의 모든 키 < b 의 모든 키 일 때 우선순위 heap 불변식 유지하며 병합
    private fun merge(a: Node?, b: Node?): Node? {
        if (a == null) return b
        if (b == null) return a
        return if (a.priority > b.priority) {
            a.right = merge(a.right, b); a
        } else {
            b.left = merge(a, b.left); b
        }
    }

    fun insert(key: Int) {
        val (l, r) = split(root, key)
        root = merge(merge(l, Node(key)), r)
    }

    fun contains(key: Int): Boolean {
        var cur = root
        while (cur != null) {
            cur = when {
                key == cur.key -> return true
                key < cur.key -> cur.left
                else -> cur.right
            }
        }
        return false
    }
}
```

**관련 알고리즘**: AVL Tree, Red-Black Tree, Cartesian Tree, Skip List

---

<a id="hash-collision-resolution"></a>
## 13. Hash Table Collision Resolution (해시 테이블 충돌 처리)

**목적**: 서로 다른 키가 같은 버킷으로 해싱될 때(충돌) 데이터를 안전하게 저장·탐색하도록 분리 연결 또는 개방 주소법으로 해결

**시간 복잡도**: 평균 O(1) 삽입/탐색/삭제, 최악 O(n) (Cuckoo는 탐색 최악 O(1))

**공간 복잡도**: O(n) (load factor에 따라 상수 배수 차이)

**특징**:
- Separate Chaining: 각 버킷에 연결 리스트(또는 트리)를 두어 충돌 키를 체인으로 연결, load factor 1 초과 허용
- Open Addressing: 충돌 시 정해진 probe 순서로 빈 슬롯 탐색 — Linear probing(d=1, primary clustering), Quadratic probing(d=i², 클러스터 완화), Double hashing(보조 해시로 보폭 결정)
- Cuckoo Hashing: 두 해시 함수로 각 키가 들어갈 후보 위치 2곳을 가지며, 충돌 시 기존 키를 다른 테이블로 밀어내(kick-out) 탐색을 worst-case O(1)로 보장
- Robin Hood Hashing: 개방 주소법에서 "부유한"(probe 거리 짧은) 키가 "가난한"(거리 긴) 키에게 자리를 양보하도록 displacement하여 probe 거리 분산을 균등화
- load factor(α = n/m)가 임계치(보통 0.75)를 넘으면 테이블 크기를 키워 재해싱(rehashing)으로 모든 키를 재배치

**장점**:
- Separate Chaining: 구현 단순, 삭제 용이, load factor 1 초과에도 동작
- Open Addressing: 포인터 없이 배열에 저장 → 캐시 지역성 우수, 메모리 효율적
- Cuckoo: 탐색이 항상 상수 시간(후보 2곳만 확인)
- Robin Hood: probe 거리 분산이 작아 평균·꼬리 지연(tail latency) 안정

**단점**:
- Separate Chaining: 포인터 오버헤드, 캐시 미스 증가
- Linear probing: primary clustering으로 성능 저하, load factor에 민감
- Cuckoo: 삽입 시 cycle 발생 가능 → 재해싱 필요, 두 테이블 관리 복잡
- Open Addressing 공통: 삭제 시 tombstone 처리 필요, load factor 1 도달 불가

**활용 예시**:
- 언어 표준 라이브러리 HashMap/dict 구현 (Java는 chaining + 트리화, Python dict는 open addressing)
- Rust hashbrown / Swift Dictionary의 Robin Hood / SwissTable 계열
- 네트워크 라우터의 고속 플로우 테이블(Cuckoo)
- 인메모리 캐시·심볼 테이블·집합(Set) 자료구조

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// Robin Hood Hashing (open addressing + probe 거리 균등화)
class RobinHoodHashMap<K, V>(initialCapacity: Int = 16) {
    private data class Slot<K, V>(var key: K, var value: V, var dist: Int)

    private var slots = arrayOfNulls<Slot<K, V>>(initialCapacity)
    private var size = 0

    private fun indexFor(key: K) = (key.hashCode() and Int.MAX_VALUE) % slots.size

    fun put(key: K, value: V) {
        if ((size + 1).toDouble() / slots.size > 0.75) resize()  // load factor 임계치 → 리해싱
        var entry = Slot(key, value, 0)
        var idx = indexFor(key)
        while (true) {
            val cur = slots[idx]
            if (cur == null) { slots[idx] = entry; size++; return }
            if (cur.key == entry.key) { cur.value = entry.value; return }  // 갱신
            if (cur.dist < entry.dist) {                 // 더 "가난한" 신참에게 자리 양보
                slots[idx] = entry; entry = cur
            }
            idx = (idx + 1) % slots.size                 // linear probe
            entry.dist++
        }
    }

    fun get(key: K): V? {
        var idx = indexFor(key)
        var dist = 0
        while (true) {
            val cur = slots[idx] ?: return null
            if (cur.key == key) return cur.value
            if (dist > cur.dist) return null             // 균등화 덕분에 조기 종료 가능
            idx = (idx + 1) % slots.size
            dist++
        }
    }

    private fun resize() {
        val old = slots
        slots = arrayOfNulls(old.size * 2)
        size = 0
        for (s in old) if (s != null) put(s.key, s.value)
    }
}
```

**관련 알고리즘**: Hash Table Search, Bloom Filter, Consistent Hashing, LRU Cache

---

<a id="rope-gap-buffer"></a>
## 14. Rope / Gap Buffer / Piece Table (로프 / 갭 버퍼 / 피스 테이블)

**목적**: 대용량 텍스트를 효율적으로 삽입·삭제·편집하기 위한 세 가지 텍스트 버퍼 자료구조와 그 트레이드오프

**시간 복잡도**: Rope 삽입/삭제/분할/연결 O(log n) · Gap Buffer 커서 위치 삽입/삭제 amortized O(1)·커서 이동 O(거리) · Piece Table 삽입/삭제 O(p) (p = piece 수, 균형 트리로 인덱싱 시 O(log p))

**공간 복잡도**: Rope O(n) · Gap Buffer O(n) (갭 포함) · Piece Table O(원본 + 추가분 + piece 메타데이터)

**특징**:
- Rope: 문자열 조각(leaf)을 균형 이진 트리로 묶고 내부 노드에 좌측 서브트리의 길이(weight)를 저장 — 인덱스 접근·삽입·삭제·split·concat이 모두 O(log n) (Boehm·Atkinson·Plass, 1995)
- Gap Buffer: 배열 중앙(커서 위치)에 빈 공간(gap)을 두어, 커서 근처 삽입/삭제를 gap 확장·축소로 처리. 커서 이동 시 gap을 memmove로 옮긴다 (Emacs의 기본 버퍼 구조)
- Piece Table: 불변(immutable) 원본 버퍼(original)와 append-only 추가 버퍼(add)를 두고, 실제 문서는 두 버퍼의 구간을 가리키는 piece 디스크립터 시퀀스로 표현 — 원본을 절대 수정하지 않아 undo·diff에 유리 (VS Code 텍스트 버퍼, 과거 Word에서도 사용)
- 세 구조 모두 큰 문자열의 가운데를 편집할 때 단일 연속 배열(O(n) 이동) 대비 비용을 줄이는 것이 핵심 목표
- Piece Table은 편집 위치가 분산될수록 piece 수가 늘어 조회가 느려지므로, 균형 트리/red-black tree로 piece 인덱스를 관리하는 구현이 일반적

**장점**:
- Rope: 어느 위치든 삽입/삭제/분할/연결이 O(log n)으로 일관되게 빠르고, 영속(persistent) 자료구조로 만들기 쉬워 undo·동시 편집에 강함
- Gap Buffer: 구현이 단순하고, 사람의 편집은 보통 한 지점에 집중되므로 그 지점에서 amortized O(1)로 매우 빠름. 메모리 지역성(locality)이 좋음
- Piece Table: 원본 버퍼가 불변이라 메모리 매핑(mmap)·로드 지연이 쉽고, 모든 편집이 add 버퍼에 누적되어 undo/redo와 변경 이력 추적이 자연스러움

**단점**:
- Rope: 노드 오버헤드·포인터 추적으로 작은 문자열엔 과하고, 캐시 지역성이 단순 배열보다 떨어짐
- Gap Buffer: 멀리 떨어진 위치로 커서가 점프하면 gap 이동에 O(거리) 비용 발생, 다중 커서/동시 편집에 부적합
- Piece Table: 편집이 흩어질수록 piece가 파편화되어 위치 조회가 느려지고(선형 구현 시 O(p)), 인덱싱용 보조 트리·주기적 병합(compaction)이 필요

**활용 예시**:
- Rope: SGI STL의 `rope`, JavaScript 엔진 일부의 문자열 연결, 대용량 로그·편집기 백엔드
- Gap Buffer: Emacs, Scintilla 등 단일 커서 중심 텍스트 에디터
- Piece Table: VS Code(Monaco) 텍스트 버퍼, AbiWord, 구형 Microsoft Word
- 공통: 수백 MB~GB급 파일을 다루는 코드 에디터·IDE의 문서 모델

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// Piece Table — 불변 원본(original) + append-only 추가(add) 버퍼.
// 문서는 (버퍼, 시작오프셋, 길이)를 가리키는 piece 리스트로 표현된다.
class PieceTable(original: String) {
    private enum class Src { ORIGINAL, ADD }
    private data class Piece(val src: Src, val start: Int, val length: Int)

    private val original = original          // 불변 원본 버퍼
    private val add = StringBuilder()        // append-only 추가 버퍼
    private val pieces = mutableListOf<Piece>()

    init {
        if (original.isNotEmpty()) pieces.add(Piece(Src.ORIGINAL, 0, original.length))
    }

    private fun buf(p: Piece) = if (p.src == Src.ORIGINAL) original else add.toString()

    // 논리적 위치 pos 에 text 삽입 (단순화 위해 piece 분할로 처리, O(p))
    fun insert(pos: Int, text: String) {
        if (text.isEmpty()) return
        val addStart = add.length
        add.append(text)
        val newPiece = Piece(Src.ADD, addStart, text.length)

        var offset = 0
        var i = 0
        while (i < pieces.size) {
            val p = pieces[i]
            if (pos <= offset + p.length) {
                val left = pos - offset                 // 현재 piece 내 분할 지점
                pieces.removeAt(i)
                var idx = i
                if (left > 0) pieces.add(idx++, p.copy(length = left))
                pieces.add(idx++, newPiece)
                if (left < p.length)
                    pieces.add(idx, p.copy(start = p.start + left, length = p.length - left))
                return
            }
            offset += p.length
            i++
        }
        pieces.add(newPiece) // 맨 끝 삽입
    }

    fun text(): String = buildString {
        for (p in pieces) append(buf(p), p.start, p.start + p.length)
    }
}
```

**관련 알고리즘**: B-Tree, Red-Black Tree, Skip List, AVL Tree

---

<a id="advanced-heaps"></a>
## 15. Advanced Heaps (Fibonacci / Binomial / Pairing) (고급 힙)

**목적**: decrease-key·merge 등 우선순위 큐 연산을 이진 힙보다 빠른 amortized 비용으로 지원해 Dijkstra/Prim 등 그래프 알고리즘의 이론적 한계를 끌어내리는 고급 힙 자료구조

**시간 복잡도**: Fibonacci — insert/decrease-key/merge O(1) amortized, extract-min O(log n) amortized / Binomial — insert O(1) amortized, merge/extract-min O(log n) / Pairing — insert/merge O(1), extract-min O(log n) amortized, decrease-key는 o(log n)~O(log n) 사이로 미해결

**공간 복잡도**: O(n) — 단, 노드마다 부모·자식·형제 포인터와 degree/mark 메타데이터를 가져 이진 힙(배열 1개)보다 상수배 큼

**특징**:
- Binomial heap(Vuillemin, 1978): 서로 다른 차수의 binomial tree 모음(이진수 표현과 동형), 두 힙 merge가 O(log n) — 이진 힙은 merge가 O(n)
- Fibonacci heap(Fredman & Tarjan, 1984): extract-min 시에만 트리를 정리(lazy consolidation), decrease-key는 cut + cascading cut으로 O(1) amortized 달성
- "Fibonacci"라는 이름은 차수 k 트리의 최소 크기가 피보나치 수 F(k+2) 이상이라는 분석에서 유래
- Pairing heap(Fredman 등, 1986): 단일 다항 트리 + 단순한 pairing merge, decrease-key의 정확한 amortized bound는 여전히 미해결(O(log n) 상한, Ω(log log n) 하한 알려짐)
- 셋 다 핸들(노드 참조)을 보관해야 decrease-key/delete를 직접 지원

**장점**:
- Fibonacci heap은 Dijkstra/Prim을 O(E + V log V)로 개선(이진 힙은 O(E log V)) — 밀집 그래프 이론 최적
- Binomial/Fibonacci heap은 두 힙을 O(log n)/O(1)에 합쳐 mergeable(meldable) 우선순위 큐 구현 가능
- Pairing heap은 구현이 단순하면서 실측 성능이 우수해 실무용 decrease-key 힙으로 자주 선택됨(예: Boost, LEMON)

**단점**:
- Fibonacci heap은 포인터 오버헤드·캐시 비친화·큰 상수로 실측에서 이진 힙/Pairing heap보다 느린 경우가 많음
- amortized 보장이라 단일 연산 최악 비용은 클 수 있어 실시간(worst-case 보장) 시스템에 부적합
- 구현 복잡도가 높고(특히 Fibonacci) 디버깅이 어려움 — 대부분의 실무에선 이진 힙으로 충분

**활용 예시**:
- 밀집 그래프에서의 Dijkstra 최단경로 / Prim 최소 신장 트리(이론적 최적 복잡도 분석)
- 자주 우선순위를 낮추는(decrease-key 빈번한) 시뮬레이션·스케줄러
- 여러 우선순위 큐를 병합해야 하는 mergeable heap 시나리오(Binomial/Fibonacci)

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// Pairing heap (min-heap): 단순하면서 실측 성능 우수, decrease-key 지원
class PairingHeap<T : Comparable<T>> {
    inner class Node(var key: T) {
        var child: Node? = null   // 첫 자식
        var sibling: Node? = null // 다음 형제
        var prev: Node? = null    // 부모 또는 이전 형제(decrease-key용)
    }

    var root: Node? = null
        private set

    fun isEmpty() = root == null
    fun peek(): T = root!!.key

    // 두 서브힙 병합: 키가 작은 쪽이 부모
    private fun merge(a: Node?, b: Node?): Node? {
        if (a == null) return b
        if (b == null) return a
        val (parent, child) = if (a.key <= b.key) a to b else b to a
        child.sibling = parent.child
        child.prev = parent
        parent.child?.prev = child
        parent.child = child
        parent.sibling = null
        parent.prev = null
        return parent
    }

    fun insert(key: T): Node {
        val node = Node(key)
        root = merge(root, node)
        return node // 핸들 반환 → decrease-key에 사용
    }

    // 형제들을 둘씩 묶어 병합(two-pass)
    private fun mergePairs(first: Node?): Node? {
        if (first?.sibling == null) return first
        val a = first
        val b = first.sibling
        val rest = b!!.sibling
        a.sibling = null; b.sibling = null
        return merge(merge(a, b), mergePairs(rest))
    }

    fun extractMin(): T {
        val min = root!!
        root = mergePairs(min.child)
        root?.prev = null
        return min.key
    }

    fun decreaseKey(node: Node, newKey: T) {
        require(newKey <= node.key) { "새 키가 더 커서는 안 됨" }
        node.key = newKey
        if (node === root) return
        // 부모/형제 연결에서 분리
        val p = node.prev
        if (p?.child === node) {
            p.child = node.sibling
        } else {
            p?.sibling = node.sibling
        }
        node.sibling?.prev = p
        node.sibling = null; node.prev = null
        root = merge(root, node)
    }
}
```

**관련 알고리즘**: Binary Heap, Dijkstra, Prim, Heap Sort

---

<a id="order-statistics-tree"></a>
## 16. Order-Statistics Tree / Interval Tree (순위 통계 트리 / 구간 트리)

**목적**: 균형 BST에 보조 정보를 증강(augment)하여 k번째 원소·rank 조회(Order-Statistics Tree)나 겹치는 구간 검색(Interval Tree)을 모두 O(log n)에 지원

**시간 복잡도**: 삽입/삭제/검색/select(k)/rank O(log n), 겹치는 구간 1개 찾기 O(log n), 겹치는 구간 전부 찾기 O((k+1) log n) - k: 결과 개수

**공간 복잡도**: O(n)

**특징**:
- CLRS의 증강 자료구조(augmented data structure) 대표 예시 — 보통 Red-Black Tree를 기반으로 증강
- Order-Statistics Tree: 각 노드에 서브트리 크기(size)를 저장 → i번째 작은 원소 select(i)와 임의 키의 rank를 O(log n)에 계산
- Interval Tree: 각 노드를 구간의 low 기준으로 정렬하고, 서브트리 내 최대 high 값(max)을 저장 → 주어진 구간과 겹치는 구간을 O(log n)에 탐색
- 회전(rotation) 시 증강 필드(size/max)는 해당 노드와 자식 정보만으로 O(1)에 갱신 가능해야 한다는 것이 증강의 핵심 조건
- Interval Tree의 겹침 판정은 [low1, high1]과 [low2, high2]가 `low1 ≤ high2 && low2 ≤ high1`일 때 겹친다는 성질을 이용

**장점**:
- 동적 집합에서 순위 쿼리(중앙값, 백분위, k번째)를 정렬 없이 O(log n)에 지원
- Interval Tree는 스케줄 충돌·구간 겹침 검색을 로그 시간에 처리
- 균형 BST 기반이라 최악의 경우에도 O(log n) 보장

**단점**:
- 증강 필드를 삽입/삭제/회전마다 정확히 유지해야 하므로 구현이 까다롭고 버그가 생기기 쉬움
- 정적 데이터의 단순 순위 쿼리만 필요하다면 정렬 배열·Fenwick/Segment Tree가 더 간단하고 상수가 작음
- 포인터 기반 노드 구조는 캐시 지역성이 배열 기반 구조보다 떨어짐

**활용 예시**:
- 실시간 리더보드의 순위/백분위 조회 (k번째 점수, 특정 점수의 등수)
- 슬라이딩 윈도우 중앙값, 동적 순위 통계
- 캘린더·회의실 예약의 시간대 충돌 검출 (Interval Tree)
- 유전체 구간 검색, 네트워크 패킷 분류기의 IP 범위 매칭

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// Order-Statistics Tree (서브트리 size 증강) — select(k), rank(key) 시연
// 균형은 생략(BST)하되 size 갱신 로직은 RB/AVL 증강과 동일한 원리
class OrderStatTree {
    private class Node(val key: Int) {
        var left: Node? = null
        var right: Node? = null
        var size: Int = 1           // 서브트리 노드 수 (증강 필드)
    }

    private var root: Node? = null
    private fun sizeOf(n: Node?): Int = n?.size ?: 0

    fun insert(key: Int) { root = insert(root, key) }
    private fun insert(n: Node?, key: Int): Node {
        if (n == null) return Node(key)
        if (key < n.key) n.left = insert(n.left, key)
        else if (key > n.key) n.right = insert(n.right, key)
        n.size = 1 + sizeOf(n.left) + sizeOf(n.right)  // O(1) 증강 갱신
        return n
    }

    // k번째(1-based) 작은 원소
    fun select(k: Int): Int? {
        var n = root
        var rank = k
        while (n != null) {
            val leftSize = sizeOf(n.left)
            when {
                rank == leftSize + 1 -> return n.key
                rank <= leftSize -> n = n.left
                else -> { rank -= leftSize + 1; n = n.right }
            }
        }
        return null
    }

    // key보다 작은 원소 수 + 1 (key의 등수)
    fun rank(key: Int): Int {
        var n = root; var r = 0
        while (n != null) {
            n = when {
                key < n.key -> n.left
                key > n.key -> { r += sizeOf(n.left) + 1; n.right }
                else -> return r + sizeOf(n.left) + 1
            }
        }
        return r + 1
    }
}
```

**관련 알고리즘**: Red-Black Tree, AVL Tree, Segment Tree, Fenwick Tree

---

<a id="van-emde-boas"></a>
## 17. van Emde Boas Tree / y-fast Trie (반 엠데 보아스 트리)

**목적**: 정수 키 우주 {0, 1, ..., u-1} 에서 insert/delete/member/successor/predecessor 를 O(log log u) 에 지원하는 정렬형 정수 자료구조

**시간 복잡도**: insert / delete / member / successor / predecessor 모두 O(log log u) (u: 키 우주 크기)

**공간 복잡도**: vEB 원형 O(u) / y-fast trie O(n) (n: 저장된 키 개수)

**특징**:
- 1975년 Peter van Emde Boas 가 고안. 우주를 √u 크기의 cluster √u 개로 재귀 분할하여 각 키 x 를 high(x)=x/√u, low(x)=x mod √u 로 나눈다
- 각 노드는 min/summary 를 별도로 보관해 재귀 호출을 한 방향(상위 cluster 또는 summary)으로만 진행 → 점화식 T(u)=T(√u)+O(1) ⇒ O(log log u)
- min 은 하위 cluster 에 중복 저장하지 않아 successor/predecessor 가 한 번의 재귀로 끝난다
- 원형 vEB 는 직접 인덱싱 배열로 O(u) 공간을 쓰므로, x-fast trie(비트 트라이 + 해시) 위에 √n 묶음 + 균형트리를 얹은 y-fast trie 로 공간을 O(n) 으로 낮춘다 (Willard, 1983)
- 정수(또는 고정 비트폭 키) 전용 — 비교 기반이 아니라 키의 비트 구조를 직접 이용한다

**장점**:
- 모든 연산이 O(log log u) 로 비교 기반 균형트리의 O(log n) 보다 빠르다 (u 가 다항적으로 제한될 때 우위)
- 정렬 순서 연산(succ/pred/min/max)을 모두 동일 복잡도로 지원
- y-fast trie 변형으로 공간을 O(n) 까지 절감 가능

**단점**:
- 정수/고정 비트 키에만 적용 가능 (일반 비교 가능 타입 불가)
- 원형 vEB 의 O(u) 공간과 재귀 구조 메모리 오버헤드가 크다
- 상수 인자와 구현 복잡도가 높아 실무에선 해시맵·균형트리·정렬배열이 더 실용적인 경우가 많다

**활용 예시**:
- 라우팅 테이블의 IP prefix / 포트 번호 등 제한된 정수 우주에서의 빠른 successor 질의
- 이산 이벤트 시뮬레이션의 우선순위 큐 (정수 시간키)
- Network flow, 그래프 알고리즘에서 정수 거리 키 관리
- 정수 정렬·범위 질의 보조 인덱스

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// 재귀형 van Emde Boas Tree (개념 시연). u 는 2의 거듭제곱 가정.
class VanEmdeBoas(private val u: Int) {
    var min = -1; private set   // 비어있으면 -1
    var max = -1; private set
    private val sqrtUp = 1 shl ((Integer.numberOfTrailingZeros(u) + 1) / 2) // 상위 √u
    private val sqrtLo = u / sqrtUp                                          // 하위 √u
    private val summary: VanEmdeBoas? = if (u > 2) VanEmdeBoas(sqrtUp) else null
    private val cluster: Array<VanEmdeBoas?>? =
        if (u > 2) arrayOfNulls(sqrtUp) else null

    private fun high(x: Int) = x / sqrtLo
    private fun low(x: Int) = x % sqrtLo
    private fun index(h: Int, l: Int) = h * sqrtLo + l
    private fun child(i: Int): VanEmdeBoas {
        if (cluster!![i] == null) cluster[i] = VanEmdeBoas(sqrtLo)
        return cluster[i]!!
    }

    fun member(x: Int): Boolean {
        if (x == min || x == max) return true
        if (u == 2) return false
        return cluster!![high(x)]?.member(low(x)) ?: false
    }

    fun insert(x: Int) {
        if (min == -1) { min = x; max = x; return }
        var v = x
        if (v < min) { val t = v; v = min; min = t } // 새 min 은 노드에 저장, 기존 min 하강
        if (u > 2) {
            val h = high(v); val c = child(h)
            if (c.min == -1) summary!!.insert(h)      // 빈 cluster 면 summary 갱신: O(1) 분기
            c.insert(low(v))
        }
        if (v > max) max = v
    }

    fun successor(x: Int): Int {           // x 보다 큰 최소 키, 없으면 -1
        if (u == 2) return if (x == 0 && max == 1) 1 else -1
        if (min != -1 && x < min) return min
        val h = high(x); val l = low(x)
        val c = cluster?.get(h)
        if (c != null && c.max != -1 && l < c.max) return index(h, c.successor(l))
        val nh = summary?.successor(h) ?: -1
        return if (nh == -1) -1 else index(nh, cluster!![nh]!!.min)
    }
}
```

**관련 알고리즘**: Trie, Y-fast Trie, Binary Indexed Tree, Skip List
