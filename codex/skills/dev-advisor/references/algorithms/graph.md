# 그래프 알고리즘 (Graph Algorithms)

그래프 자료구조에서 탐색, 최단 경로, 최소 신장 트리 등을 구하는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [bfs](#bfs) | BFS (Breadth-First Search) | 너비 우선 탐색 | 낮음 |
| [dfs](#dfs) | DFS (Depth-First Search) | 깊이 우선 탐색 | 낮음 |
| [dijkstra](#dijkstra) | Dijkstra | 다익스트라 | 중간 |
| [bellman-ford](#bellman-ford) | Bellman-Ford | 벨만-포드 | 중간 |
| [floyd-warshall](#floyd-warshall) | Floyd-Warshall | 플로이드-워셜 | 중간 |
| [a-star](#a-star) | A* | 에이스타 | 높음 |
| [prim](#prim) | Prim | 프림 | 중간 |
| [kruskal](#kruskal) | Kruskal | 크루스칼 | 중간 |
| [topological-sort](#topological-sort) | Topological Sort | 위상 정렬 | 중간 |
| [tarjan-scc](#tarjan-scc) | Tarjan's SCC | 타잔 강결합 요소 | 높음 |
| [kosaraju](#kosaraju) | Kosaraju | 코사라주 | 중간 |
| [johnson](#johnson) | Johnson | 존슨 | 높음 |
| [lca](#lca) | LCA (Lowest Common Ancestor) | 최소 공통 조상 | 중간 |
| [articulation-points](#articulation-points) | Articulation Points | 단절점 | 중간 |
| [bridges](#bridges) | Bridges | 단절선 | 중간 |
| [2-sat](#2-sat) | 2-SAT | 2-Satisfiability | 높음 |
| [eulerian-path](#eulerian-path) | Eulerian Path / Circuit | 오일러 경로/회로 (Hierholzer) | 중간 |
| [stoer-wagner](#stoer-wagner) | Min Cut — Stoer-Wagner | 전역 최소 컷 | 높음 |
| [heavy-light-decomposition](#heavy-light-decomposition) | Heavy-Light Decomposition (HLD) | 헤비-라이트 분해 | 높음 |
| [centroid-decomposition](#centroid-decomposition) | Centroid Decomposition | 센트로이드 분할 | 높음 |

---

<a id="bfs"></a>
## 1. BFS (Breadth-First Search, 너비 우선 탐색)

**목적**: 시작 정점에서 가까운 정점부터 탐색

**시간 복잡도**: O(V + E)

**공간 복잡도**: O(V)

**특징**:
- 큐(Queue) 사용
- 레벨 순서대로 탐색
- 최단 경로 보장 (무가중치 그래프)

**장점**:
- 최단 경로 찾기에 적합 (무가중치)
- 목표가 가까우면 빠름

**단점**:
- 메모리 사용량이 많음
- 가중치 그래프에서는 최단 경로 보장 안됨

**활용 예시**:
- 최단 경로 (무가중치)
- 소셜 네트워크 친구 추천
- 웹 크롤링

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import java.util.LinkedList
import java.util.Queue

fun bfs(graph: Map<Int, List<Int>>, start: Int): List<Int> {
    val visited = mutableSetOf<Int>()
    val result = mutableListOf<Int>()
    val queue: Queue<Int> = LinkedList()

    queue.add(start)
    visited.add(start)

    while (queue.isNotEmpty()) {
        val node = queue.poll()
        result.add(node)

        graph[node]?.forEach { neighbor ->
            if (neighbor !in visited) {
                visited.add(neighbor)
                queue.add(neighbor)
            }
        }
    }

    return result
}

// 최단 거리 계산
fun bfsShortestPath(graph: Map<Int, List<Int>>, start: Int, end: Int): Int {
    val visited = mutableSetOf<Int>()
    val queue: Queue<Pair<Int, Int>> = LinkedList() // (node, distance)

    queue.add(start to 0)
    visited.add(start)

    while (queue.isNotEmpty()) {
        val (node, dist) = queue.poll()
        if (node == end) return dist

        graph[node]?.forEach { neighbor ->
            if (neighbor !in visited) {
                visited.add(neighbor)
                queue.add(neighbor to dist + 1)
            }
        }
    }

    return -1 // 경로 없음
}
```

**관련 알고리즘**: DFS, Dijkstra

---

<a id="dfs"></a>
## 2. DFS (Depth-First Search, 깊이 우선 탐색)

**목적**: 한 경로를 끝까지 탐색 후 백트래킹

**시간 복잡도**: O(V + E)

**공간 복잡도**: O(V)

**특징**:
- 스택(Stack) 또는 재귀 사용
- 깊이 방향으로 탐색
- 경로 탐색에 적합

**장점**:
- 메모리 효율적 (깊이만큼만 사용)
- 경로 존재 여부 확인에 적합

**단점**:
- 최단 경로 보장 안됨
- 무한 루프 가능성 (사이클 처리 필요)

**활용 예시**:
- 미로 탐색
- 위상 정렬
- 사이클 검출
- 연결 요소 찾기

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 재귀 방식
fun dfsRecursive(
    graph: Map<Int, List<Int>>,
    node: Int,
    visited: MutableSet<Int> = mutableSetOf(),
    result: MutableList<Int> = mutableListOf()
): List<Int> {
    visited.add(node)
    result.add(node)

    graph[node]?.forEach { neighbor ->
        if (neighbor !in visited) {
            dfsRecursive(graph, neighbor, visited, result)
        }
    }

    return result
}

// 스택 방식 (반복)
fun dfsIterative(graph: Map<Int, List<Int>>, start: Int): List<Int> {
    val visited = mutableSetOf<Int>()
    val result = mutableListOf<Int>()
    val stack = ArrayDeque<Int>()

    stack.addLast(start)

    while (stack.isNotEmpty()) {
        val node = stack.removeLast()
        if (node in visited) continue

        visited.add(node)
        result.add(node)

        graph[node]?.reversed()?.forEach { neighbor ->
            if (neighbor !in visited) {
                stack.addLast(neighbor)
            }
        }
    }

    return result
}

// 사이클 검출
fun hasCycle(graph: Map<Int, List<Int>>, n: Int): Boolean {
    val visited = mutableSetOf<Int>()
    val recStack = mutableSetOf<Int>()

    fun dfs(node: Int): Boolean {
        visited.add(node)
        recStack.add(node)

        graph[node]?.forEach { neighbor ->
            if (neighbor !in visited && dfs(neighbor)) return true
            if (neighbor in recStack) return true
        }

        recStack.remove(node)
        return false
    }

    for (i in 0 until n) {
        if (i !in visited && dfs(i)) return true
    }
    return false
}
```

**관련 알고리즘**: BFS, Topological Sort, Tarjan SCC

---

<a id="dijkstra"></a>
## 3. Dijkstra (다익스트라)

**목적**: 단일 출발점에서 모든 정점까지의 최단 경로 (양수 가중치)

**시간 복잡도**: O((V + E) log V) - 우선순위 큐 사용

**공간 복잡도**: O(V)

**특징**:
- 우선순위 큐(최소 힙) 사용
- 그리디 알고리즘
- 음수 가중치 불가

**장점**:
- 효율적인 최단 경로 계산
- 양수 가중치에서 정확한 결과

**단점**:
- 음수 가중치 처리 불가
- 우선순위 큐 필요

**활용 예시**:
- GPS 내비게이션
- 네트워크 라우팅
- 지도 서비스

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import java.util.PriorityQueue

data class Edge(val to: Int, val weight: Int)

fun dijkstra(graph: Map<Int, List<Edge>>, start: Int, n: Int): IntArray {
    val dist = IntArray(n) { Int.MAX_VALUE }
    dist[start] = 0

    // (distance, node)
    val pq = PriorityQueue<Pair<Int, Int>>(compareBy { it.first })
    pq.add(0 to start)

    while (pq.isNotEmpty()) {
        val (d, u) = pq.poll()
        if (d > dist[u]) continue

        graph[u]?.forEach { edge ->
            val newDist = dist[u] + edge.weight
            if (newDist < dist[edge.to]) {
                dist[edge.to] = newDist
                pq.add(newDist to edge.to)
            }
        }
    }

    return dist
}

// 경로 복원
fun dijkstraWithPath(
    graph: Map<Int, List<Edge>>,
    start: Int,
    end: Int,
    n: Int
): Pair<Int, List<Int>> {
    val dist = IntArray(n) { Int.MAX_VALUE }
    val prev = IntArray(n) { -1 }
    dist[start] = 0

    val pq = PriorityQueue<Pair<Int, Int>>(compareBy { it.first })
    pq.add(0 to start)

    while (pq.isNotEmpty()) {
        val (d, u) = pq.poll()
        if (d > dist[u]) continue

        graph[u]?.forEach { edge ->
            val newDist = dist[u] + edge.weight
            if (newDist < dist[edge.to]) {
                dist[edge.to] = newDist
                prev[edge.to] = u
                pq.add(newDist to edge.to)
            }
        }
    }

    // 경로 복원
    val path = mutableListOf<Int>()
    var current = end
    while (current != -1) {
        path.add(current)
        current = prev[current]
    }

    return dist[end] to path.reversed()
}
```

**관련 알고리즘**: Bellman-Ford, A*, Floyd-Warshall

---

<a id="bellman-ford"></a>
## 4. Bellman-Ford (벨만-포드)

**목적**: 단일 출발점에서 모든 정점까지의 최단 경로 (음수 가중치 허용)

**시간 복잡도**: O(VE)

**공간 복잡도**: O(V)

**특징**:
- 음수 가중치 허용
- 음수 사이클 검출 가능
- 모든 간선을 V-1번 반복

**장점**:
- 음수 가중치 처리 가능
- 음수 사이클 검출

**단점**:
- Dijkstra보다 느림

**활용 예시**:
- 음수 가중치 그래프
- 차익 거래 감지 (금융)
- 네트워크 라우팅 (RIP)

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
data class EdgeBF(val from: Int, val to: Int, val weight: Int)

fun bellmanFord(edges: List<EdgeBF>, n: Int, start: Int): IntArray? {
    val dist = IntArray(n) { Int.MAX_VALUE }
    dist[start] = 0

    // V-1번 반복
    repeat(n - 1) {
        edges.forEach { edge ->
            if (dist[edge.from] != Int.MAX_VALUE) {
                val newDist = dist[edge.from] + edge.weight
                if (newDist < dist[edge.to]) {
                    dist[edge.to] = newDist
                }
            }
        }
    }

    // 음수 사이클 검출
    edges.forEach { edge ->
        if (dist[edge.from] != Int.MAX_VALUE &&
            dist[edge.from] + edge.weight < dist[edge.to]) {
            return null // 음수 사이클 존재
        }
    }

    return dist
}

// 음수 사이클이 영향을 미치는 정점 찾기
fun bellmanFordWithNegativeCycle(
    edges: List<EdgeBF>,
    n: Int,
    start: Int
): Pair<LongArray, Set<Int>> {
    val dist = LongArray(n) { Long.MAX_VALUE }
    dist[start] = 0L
    val negCycleNodes = mutableSetOf<Int>()

    repeat(n - 1) {
        edges.forEach { edge ->
            if (dist[edge.from] != Long.MAX_VALUE) {
                val newDist = dist[edge.from] + edge.weight
                if (newDist < dist[edge.to]) {
                    dist[edge.to] = newDist
                }
            }
        }
    }

    // 음수 사이클 영향받는 노드 찾기
    repeat(n) {
        edges.forEach { edge ->
            if (dist[edge.from] != Long.MAX_VALUE &&
                dist[edge.from] + edge.weight < dist[edge.to]) {
                dist[edge.to] = Long.MIN_VALUE
                negCycleNodes.add(edge.to)
            }
        }
    }

    return dist to negCycleNodes
}
```

**관련 알고리즘**: Dijkstra, SPFA

---

<a id="floyd-warshall"></a>
## 5. Floyd-Warshall (플로이드-워셜)

**목적**: 모든 정점 쌍 간의 최단 경로

**시간 복잡도**: O(V³)

**공간 복잡도**: O(V²)

**특징**:
- 동적 프로그래밍
- 모든 쌍 최단 경로
- 음수 가중치 허용 (음수 사이클 제외)

**장점**:
- 구현이 간단
- 모든 쌍 한번에 계산

**단점**:
- O(V³) 시간 복잡도
- 큰 그래프에서 비효율적

**활용 예시**:
- 모든 쌍 최단 경로
- 그래프 도달 가능성
- 전이 폐쇄(Transitive Closure)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
fun floydWarshall(graph: Array<IntArray>): Array<IntArray> {
    val n = graph.size
    val dist = Array(n) { i -> graph[i].copyOf() }

    for (k in 0 until n) {
        for (i in 0 until n) {
            for (j in 0 until n) {
                if (dist[i][k] != Int.MAX_VALUE &&
                    dist[k][j] != Int.MAX_VALUE) {
                    val newDist = dist[i][k] + dist[k][j]
                    if (newDist < dist[i][j]) {
                        dist[i][j] = newDist
                    }
                }
            }
        }
    }

    return dist
}

// 경로 복원 포함
fun floydWarshallWithPath(
    graph: Array<IntArray>
): Pair<Array<IntArray>, Array<IntArray>> {
    val n = graph.size
    val dist = Array(n) { i -> graph[i].copyOf() }
    val next = Array(n) { i -> IntArray(n) { j -> if (graph[i][j] != Int.MAX_VALUE) j else -1 } }

    for (k in 0 until n) {
        for (i in 0 until n) {
            for (j in 0 until n) {
                if (dist[i][k] != Int.MAX_VALUE &&
                    dist[k][j] != Int.MAX_VALUE) {
                    val newDist = dist[i][k] + dist[k][j]
                    if (newDist < dist[i][j]) {
                        dist[i][j] = newDist
                        next[i][j] = next[i][k]
                    }
                }
            }
        }
    }

    return dist to next
}

fun reconstructPath(next: Array<IntArray>, start: Int, end: Int): List<Int> {
    if (next[start][end] == -1) return emptyList()
    val path = mutableListOf(start)
    var current = start
    while (current != end) {
        current = next[current][end]
        path.add(current)
    }
    return path
}
```

**관련 알고리즘**: Dijkstra, Johnson

---

<a id="a-star"></a>
## 6. A* (A-star, 에이스타)

**목적**: 휴리스틱을 이용한 효율적인 경로 탐색

**시간 복잡도**: O(E) - 휴리스틱에 따라 다름

**공간 복잡도**: O(V)

**특징**:
- f(n) = g(n) + h(n)
- g(n): 시작점에서 현재까지 비용
- h(n): 현재에서 목표까지 추정 비용 (휴리스틱)

**장점**:
- Dijkstra보다 빠름 (좋은 휴리스틱 시)
- 최단 경로 보장 (허용 가능 휴리스틱)

**단점**:
- 휴리스틱 설계 필요
- 메모리 사용량 증가

**활용 예시**:
- 게임 AI 경로 찾기
- 로봇 내비게이션
- 지도 서비스

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.PriorityQueue
import kotlin.math.abs

data class Node(val x: Int, val y: Int)
data class AStarNode(
    val node: Node,
    val g: Int,     // 시작점에서 현재까지 비용
    val f: Int      // g + h (총 추정 비용)
)

// 맨해튼 거리 휴리스틱
fun heuristic(a: Node, b: Node): Int {
    return abs(a.x - b.x) + abs(a.y - b.y)
}

fun aStar(
    grid: Array<IntArray>,
    start: Node,
    goal: Node
): List<Node>? {
    val rows = grid.size
    val cols = grid[0].size
    val directions = listOf(0 to 1, 1 to 0, 0 to -1, -1 to 0)

    val openSet = PriorityQueue<AStarNode>(compareBy { it.f })
    val cameFrom = mutableMapOf<Node, Node>()
    val gScore = mutableMapOf<Node, Int>().withDefault { Int.MAX_VALUE }

    gScore[start] = 0
    openSet.add(AStarNode(start, 0, heuristic(start, goal)))

    while (openSet.isNotEmpty()) {
        val current = openSet.poll()

        if (current.node == goal) {
            // 경로 복원
            val path = mutableListOf<Node>()
            var node: Node? = goal
            while (node != null) {
                path.add(node)
                node = cameFrom[node]
            }
            return path.reversed()
        }

        for ((dx, dy) in directions) {
            val nx = current.node.x + dx
            val ny = current.node.y + dy
            val neighbor = Node(nx, ny)

            if (nx !in 0 until rows || ny !in 0 until cols) continue
            if (grid[nx][ny] == 1) continue // 장애물

            val tentativeG = gScore.getValue(current.node) + 1

            if (tentativeG < gScore.getValue(neighbor)) {
                cameFrom[neighbor] = current.node
                gScore[neighbor] = tentativeG
                val fScore = tentativeG + heuristic(neighbor, goal)
                openSet.add(AStarNode(neighbor, tentativeG, fScore))
            }
        }
    }

    return null // 경로 없음
}
```

**관련 알고리즘**: Dijkstra, BFS, IDA*

---

<a id="prim"></a>
## 7. Prim (프림)

**목적**: 최소 신장 트리 (MST) 구성

**시간 복잡도**: O(E log V) - 우선순위 큐 사용

**공간 복잡도**: O(V)

**특징**:
- 정점 기반 MST
- 우선순위 큐 사용
- 밀집 그래프에 적합

**장점**:
- 밀집 그래프에서 효율적
- 하나의 트리에서 시작

**단점**:
- 희소 그래프에서 Kruskal보다 느림

**활용 예시**:
- 네트워크 설계
- 클러스터링
- 근사 TSP

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.PriorityQueue

data class PrimEdge(val to: Int, val weight: Int)

fun prim(graph: Map<Int, List<PrimEdge>>, n: Int): List<Pair<Int, Int>> {
    val mst = mutableListOf<Pair<Int, Int>>() // (from, to)
    val visited = BooleanArray(n)
    val pq = PriorityQueue<Triple<Int, Int, Int>>(compareBy { it.third }) // (from, to, weight)

    // 0번 정점에서 시작
    visited[0] = true
    graph[0]?.forEach { edge ->
        pq.add(Triple(0, edge.to, edge.weight))
    }

    var totalWeight = 0

    while (pq.isNotEmpty() && mst.size < n - 1) {
        val (from, to, weight) = pq.poll()
        if (visited[to]) continue

        visited[to] = true
        mst.add(from to to)
        totalWeight += weight

        graph[to]?.forEach { edge ->
            if (!visited[edge.to]) {
                pq.add(Triple(to, edge.to, edge.weight))
            }
        }
    }

    return mst
}

// MST 총 가중치 반환
fun primMSTWeight(graph: Map<Int, List<PrimEdge>>, n: Int): Int {
    val visited = BooleanArray(n)
    val pq = PriorityQueue<Pair<Int, Int>>(compareBy { it.second }) // (node, weight)

    pq.add(0 to 0)
    var totalWeight = 0

    while (pq.isNotEmpty()) {
        val (node, weight) = pq.poll()
        if (visited[node]) continue

        visited[node] = true
        totalWeight += weight

        graph[node]?.forEach { edge ->
            if (!visited[edge.to]) {
                pq.add(edge.to to edge.weight)
            }
        }
    }

    return totalWeight
}
```

**관련 알고리즘**: Kruskal, Dijkstra

---

<a id="kruskal"></a>
## 8. Kruskal (크루스칼)

**목적**: 최소 신장 트리 (MST) 구성

**시간 복잡도**: O(E log E)

**공간 복잡도**: O(V)

**특징**:
- 간선 기반 MST
- Union-Find 사용
- 희소 그래프에 적합

**장점**:
- 희소 그래프에서 효율적
- 구현이 직관적

**단점**:
- 간선 정렬 필요

**활용 예시**:
- 네트워크 설계
- 이미지 분할
- 클러스터링

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
data class KruskalEdge(val from: Int, val to: Int, val weight: Int)

class UnionFind(n: Int) {
    private val parent = IntArray(n) { it }
    private val rank = IntArray(n) { 0 }

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

        // 랭크 기반 합치기
        when {
            rank[px] < rank[py] -> parent[px] = py
            rank[px] > rank[py] -> parent[py] = px
            else -> {
                parent[py] = px
                rank[px]++
            }
        }
        return true
    }
}

fun kruskal(edges: List<KruskalEdge>, n: Int): List<KruskalEdge> {
    val mst = mutableListOf<KruskalEdge>()
    val sortedEdges = edges.sortedBy { it.weight }
    val uf = UnionFind(n)

    for (edge in sortedEdges) {
        if (uf.union(edge.from, edge.to)) {
            mst.add(edge)
            if (mst.size == n - 1) break
        }
    }

    return mst
}

// MST 총 가중치 반환
fun kruskalMSTWeight(edges: List<KruskalEdge>, n: Int): Int {
    val sortedEdges = edges.sortedBy { it.weight }
    val uf = UnionFind(n)
    var totalWeight = 0
    var edgeCount = 0

    for (edge in sortedEdges) {
        if (uf.union(edge.from, edge.to)) {
            totalWeight += edge.weight
            edgeCount++
            if (edgeCount == n - 1) break
        }
    }

    return totalWeight
}
```

**관련 알고리즘**: Prim, Union-Find

---

<a id="topological-sort"></a>
## 9. Topological Sort (위상 정렬)

**목적**: DAG(방향 비순환 그래프)의 정점을 선형 순서로 정렬

**시간 복잡도**: O(V + E)

**공간 복잡도**: O(V)

**특징**:
- DAG에서만 가능
- 의존성 순서 결정
- 여러 유효한 순서 가능

**장점**:
- 의존성 해결에 적합
- 선형 시간 복잡도

**단점**:
- DAG에서만 사용 가능

**활용 예시**:
- 빌드 시스템 (의존성 해결)
- 작업 스케줄링
- 과목 선수 과목 결정

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.LinkedList
import java.util.Queue

// Kahn's Algorithm (BFS 기반)
fun topologicalSortKahn(graph: Map<Int, List<Int>>, n: Int): List<Int>? {
    val inDegree = IntArray(n)
    graph.values.flatten().forEach { inDegree[it]++ }

    val queue: Queue<Int> = LinkedList()
    for (i in 0 until n) {
        if (inDegree[i] == 0) queue.add(i)
    }

    val result = mutableListOf<Int>()

    while (queue.isNotEmpty()) {
        val node = queue.poll()
        result.add(node)

        graph[node]?.forEach { neighbor ->
            inDegree[neighbor]--
            if (inDegree[neighbor] == 0) {
                queue.add(neighbor)
            }
        }
    }

    return if (result.size == n) result else null // null = 사이클 존재
}

// DFS 기반
fun topologicalSortDFS(graph: Map<Int, List<Int>>, n: Int): List<Int>? {
    val visited = IntArray(n) // 0: 미방문, 1: 방문중, 2: 완료
    val result = mutableListOf<Int>()

    fun dfs(node: Int): Boolean {
        if (visited[node] == 1) return false // 사이클 발견
        if (visited[node] == 2) return true

        visited[node] = 1
        graph[node]?.forEach { neighbor ->
            if (!dfs(neighbor)) return false
        }
        visited[node] = 2
        result.add(node)
        return true
    }

    for (i in 0 until n) {
        if (visited[i] == 0 && !dfs(i)) return null
    }

    return result.reversed()
}
```

**관련 알고리즘**: DFS, Kahn's Algorithm

---

<a id="tarjan-scc"></a>
## 10. Tarjan's SCC (타잔 강결합 요소)

**목적**: 방향 그래프에서 강결합 요소(SCC) 찾기

**시간 복잡도**: O(V + E)

**공간 복잡도**: O(V)

**특징**:
- DFS 기반
- 단일 패스로 SCC 탐지
- low-link 값 활용

**장점**:
- 효율적인 SCC 탐지
- 한 번의 DFS로 완료

**단점**:
- 구현이 복잡

**활용 예시**:
- 소셜 네트워크 분석
- 2-SAT 문제
- 데드락 감지

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class TarjanSCC(private val n: Int, private val graph: Map<Int, List<Int>>) {
    private var index = 0
    private val indices = IntArray(n) { -1 }
    private val lowlink = IntArray(n) { -1 }
    private val onStack = BooleanArray(n)
    private val stack = ArrayDeque<Int>()
    private val sccs = mutableListOf<List<Int>>()

    fun findSCCs(): List<List<Int>> {
        for (v in 0 until n) {
            if (indices[v] == -1) {
                strongconnect(v)
            }
        }
        return sccs
    }

    private fun strongconnect(v: Int) {
        indices[v] = index
        lowlink[v] = index
        index++
        stack.addLast(v)
        onStack[v] = true

        graph[v]?.forEach { w ->
            if (indices[w] == -1) {
                strongconnect(w)
                lowlink[v] = minOf(lowlink[v], lowlink[w])
            } else if (onStack[w]) {
                lowlink[v] = minOf(lowlink[v], indices[w])
            }
        }

        // SCC의 루트인 경우
        if (lowlink[v] == indices[v]) {
            val scc = mutableListOf<Int>()
            do {
                val w = stack.removeLast()
                onStack[w] = false
                scc.add(w)
            } while (w != v)
            sccs.add(scc)
        }
    }
}

fun findSCCs(graph: Map<Int, List<Int>>, n: Int): List<List<Int>> {
    return TarjanSCC(n, graph).findSCCs()
}
```

**관련 알고리즘**: Kosaraju, DFS

---

<a id="kosaraju"></a>
## 11. Kosaraju (코사라주)

**목적**: 방향 그래프에서 강결합 요소(SCC) 찾기

**시간 복잡도**: O(V + E)

**공간 복잡도**: O(V)

**특징**:
- 두 번의 DFS 사용
- 역방향 그래프 활용
- 이해하기 쉬운 구조

**장점**:
- 구현이 직관적
- 이해하기 쉬움

**단점**:
- 두 번의 DFS 필요
- 역방향 그래프 구성 필요

**활용 예시**:
- SCC 찾기
- 그래프 축약

**난이도**: 중간 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
fun kosarajuSCC(graph: Map<Int, List<Int>>, n: Int): List<List<Int>> {
    // 1. 정방향 DFS로 종료 순서 기록
    val visited = BooleanArray(n)
    val finishOrder = mutableListOf<Int>()

    fun dfs1(v: Int) {
        visited[v] = true
        graph[v]?.forEach { w ->
            if (!visited[w]) dfs1(w)
        }
        finishOrder.add(v)
    }

    for (i in 0 until n) {
        if (!visited[i]) dfs1(i)
    }

    // 2. 역방향 그래프 구성
    val reverseGraph = mutableMapOf<Int, MutableList<Int>>()
    graph.forEach { (from, neighbors) ->
        neighbors.forEach { to ->
            reverseGraph.getOrPut(to) { mutableListOf() }.add(from)
        }
    }

    // 3. 역방향 DFS로 SCC 찾기
    visited.fill(false)
    val sccs = mutableListOf<List<Int>>()

    fun dfs2(v: Int, scc: MutableList<Int>) {
        visited[v] = true
        scc.add(v)
        reverseGraph[v]?.forEach { w ->
            if (!visited[w]) dfs2(w, scc)
        }
    }

    for (v in finishOrder.reversed()) {
        if (!visited[v]) {
            val scc = mutableListOf<Int>()
            dfs2(v, scc)
            sccs.add(scc)
        }
    }

    return sccs
}
```

**관련 알고리즘**: Tarjan SCC, DFS

---

<a id="johnson"></a>
## 12. Johnson (존슨)

**목적**: 희소 그래프에서 모든 쌍 최단 경로 (음수 가중치 허용)

**시간 복잡도**: O(V² log V + VE)

**공간 복잡도**: O(V²)

**특징**:
- Bellman-Ford + Dijkstra 조합
- 가중치 재조정(reweighting)으로 음수 가중치 제거

**장점**:
- 희소 그래프에서 Floyd-Warshall보다 빠름
- 음수 가중치 허용

**단점**:
- 구현이 복잡
- 밀집 그래프에서는 비효율적

**활용 예시**:
- 희소 그래프의 모든 쌍 최단 경로
- 음수 가중치가 있는 네트워크

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
import java.util.PriorityQueue

fun johnson(graph: Map<Int, List<Edge>>, n: Int): Array<IntArray>? {
    // 1. 새 정점 추가하고 모든 정점으로 가중치 0인 간선 연결
    val edges = mutableListOf<EdgeBF>()
    graph.forEach { (from, neighbors) ->
        neighbors.forEach { edge ->
            edges.add(EdgeBF(from, edge.to, edge.weight))
        }
    }
    for (v in 0 until n) {
        edges.add(EdgeBF(n, v, 0)) // 새 정점 n에서 모든 정점으로
    }

    // 2. Bellman-Ford로 h 값 계산
    val h = bellmanFord(edges, n + 1, n) ?: return null // 음수 사이클

    // 3. 가중치 재조정
    val reweightedGraph = mutableMapOf<Int, MutableList<Edge>>()
    graph.forEach { (from, neighbors) ->
        neighbors.forEach { edge ->
            val newWeight = edge.weight + h[from] - h[edge.to]
            reweightedGraph.getOrPut(from) { mutableListOf() }
                .add(Edge(edge.to, newWeight))
        }
    }

    // 4. 각 정점에서 Dijkstra 실행
    val dist = Array(n) { IntArray(n) }
    for (u in 0 until n) {
        val d = dijkstra(reweightedGraph, u, n)
        for (v in 0 until n) {
            if (d[v] == Int.MAX_VALUE) {
                dist[u][v] = Int.MAX_VALUE
            } else {
                // 원래 가중치로 복원
                dist[u][v] = d[v] - h[u] + h[v]
            }
        }
    }

    return dist
}
```

**관련 알고리즘**: Floyd-Warshall, Bellman-Ford, Dijkstra

---

<a id="lca"></a>
## 13. LCA (Lowest Common Ancestor, 최소 공통 조상)

**목적**: 트리에서 두 노드의 가장 깊은 공통 조상 찾기 (Binary Lifting 기반)

**시간 복잡도**: O(n log n) 전처리, O(log n) 쿼리

**공간 복잡도**: O(n log n)

**특징**:
- up[v][k] = v의 2^k번째 조상
- 동일 깊이로 맞춘 후 동시에 올림
- 오프라인 쿼리에는 Tarjan LCA(Union-Find)도 사용

**장점**:
- 빠른 쿼리
- 트리 경로 문제 일반화

**단점**:
- 전처리 O(n log n)
- 동적 트리에 부적합

**활용 예시**:
- 트리 경로 쿼리
- 트리 거리 계산
- Auto-LCA를 이용한 트리 DP

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
class BinaryLiftingLCA(private val n: Int, private val root: Int = 0) {
    private val log = (32 - Integer.numberOfLeadingZeros(n))
    private val up = Array(n) { IntArray(log + 1) { -1 } }
    private val depth = IntArray(n)
    private val adj = Array(n) { mutableListOf<Int>() }

    fun addEdge(u: Int, v: Int) {
        adj[u].add(v); adj[v].add(u)
    }

    fun build() {
        val stack = ArrayDeque<Int>()
        stack.addLast(root)
        val visited = BooleanArray(n)
        visited[root] = true
        depth[root] = 0
        // 반복 DFS
        while (stack.isNotEmpty()) {
            val u = stack.removeLast()
            for (v in adj[u]) {
                if (!visited[v]) {
                    visited[v] = true
                    depth[v] = depth[u] + 1
                    up[v][0] = u
                    stack.addLast(v)
                }
            }
        }
        for (k in 1..log) {
            for (v in 0 until n) {
                val mid = up[v][k - 1]
                if (mid != -1) up[v][k] = up[mid][k - 1]
            }
        }
    }

    fun lca(u0: Int, v0: Int): Int {
        var u = u0; var v = v0
        if (depth[u] < depth[v]) { val t = u; u = v; v = t }
        var diff = depth[u] - depth[v]
        for (k in 0..log) {
            if ((diff shr k) and 1 == 1) u = up[u][k]
        }
        if (u == v) return u
        for (k in log downTo 0) {
            if (up[u][k] != up[v][k]) {
                u = up[u][k]; v = up[v][k]
            }
        }
        return up[u][0]
    }

    fun distance(u: Int, v: Int): Int {
        val a = lca(u, v)
        return depth[u] + depth[v] - 2 * depth[a]
    }
}
```

**관련 알고리즘**: Tarjan LCA, Euler Tour + RMQ

---

<a id="articulation-points"></a>
## 14. Articulation Points (단절점)

**목적**: 무방향 그래프에서 제거 시 연결 컴포넌트가 늘어나는 정점 찾기

**시간 복잡도**: O(V + E)

**공간 복잡도**: O(V)

**특징**:
- DFS 기반 (Tarjan)
- discovery time + low-link
- 루트는 자식 ≥ 2개일 때 단절점
- 비루트 v는 자식 c에 대해 low[c] ≥ disc[v]면 단절점

**장점**:
- 선형 시간
- 한 번의 DFS

**단점**:
- 다중 간선 / 자기 루프 처리 주의

**활용 예시**:
- 네트워크 취약 노드 식별
- 통신망 안정성
- 그래프 분해

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class ArticulationFinder(private val n: Int, private val adj: Array<MutableList<Int>>) {
    private val disc = IntArray(n) { -1 }
    private val low = IntArray(n)
    private val isAp = BooleanArray(n)
    private var timer = 0

    fun find(): List<Int> {
        for (i in 0 until n) {
            if (disc[i] == -1) dfs(i, -1)
        }
        return (0 until n).filter { isAp[it] }
    }

    private fun dfs(u: Int, parent: Int) {
        disc[u] = timer
        low[u] = timer
        timer++
        var children = 0
        for (v in adj[u]) {
            if (v == parent) continue
            if (disc[v] == -1) {
                children++
                dfs(v, u)
                low[u] = minOf(low[u], low[v])
                if (parent != -1 && low[v] >= disc[u]) isAp[u] = true
            } else {
                low[u] = minOf(low[u], disc[v])
            }
        }
        if (parent == -1 && children >= 2) isAp[u] = true
    }
}
```

**관련 알고리즘**: Bridges, Tarjan SCC, Biconnected Components

---

<a id="bridges"></a>
## 15. Bridges (단절선)

**목적**: 무방향 그래프에서 제거 시 연결 컴포넌트가 늘어나는 간선 찾기

**시간 복잡도**: O(V + E)

**공간 복잡도**: O(V)

**특징**:
- Articulation과 거의 동일한 DFS
- 조건: low[v] > disc[u] (등호 없음)
- 다중 간선이 있으면 평행 간선은 bridge 아님

**장점**:
- 선형 시간
- 단절점과 동시 계산 가능

**단점**:
- 다중 간선 처리에 인덱스 추적 필요

**활용 예시**:
- 네트워크 백본 분석
- 최소 컷 후보
- 2-Edge-Connected Components

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class BridgeFinder(private val n: Int) {
    data class E(val to: Int, val idx: Int)
    private val adj = Array(n) { mutableListOf<E>() }
    private val disc = IntArray(n) { -1 }
    private val low = IntArray(n)
    private val bridges = mutableListOf<Pair<Int, Int>>()
    private var timer = 0
    private var edgeIdx = 0

    fun addEdge(u: Int, v: Int) {
        val id = edgeIdx++
        adj[u].add(E(v, id))
        adj[v].add(E(u, id))
    }

    fun find(): List<Pair<Int, Int>> {
        for (i in 0 until n) if (disc[i] == -1) dfs(i, -1)
        return bridges
    }

    private fun dfs(u: Int, parentEdge: Int) {
        disc[u] = timer
        low[u] = timer
        timer++
        for (e in adj[u]) {
            if (e.idx == parentEdge) continue
            if (disc[e.to] == -1) {
                dfs(e.to, e.idx)
                low[u] = minOf(low[u], low[e.to])
                if (low[e.to] > disc[u]) bridges.add(u to e.to)
            } else {
                low[u] = minOf(low[u], disc[e.to])
            }
        }
    }
}
```

**관련 알고리즘**: Articulation Points, Tarjan SCC

---

<a id="2-sat"></a>
## 16. 2-SAT (2-Satisfiability)

**목적**: 절(clause)이 2개 리터럴인 CNF의 충족 가능성 판정 + 할당 구성

**시간 복잡도**: O(V + E) - SCC 활용

**공간 복잡도**: O(V + E)

**특징**:
- 각 변수 x → 정점 x, ¬x
- 절 (a ∨ b)는 함의 ¬a → b, ¬b → a로 변환
- Tarjan SCC로 강결합 컴포넌트 계산
- 같은 SCC에 x와 ¬x 있으면 UNSAT

**장점**:
- 다항 시간 (3-SAT는 NP-complete)
- 명시적 충족 할당 추출

**단점**:
- 변수 인덱싱 까다로움 (2*i, 2*i+1)
- 절 변환 신중

**활용 예시**:
- 일정 충돌 해결
- 회로 검증
- 구간 충돌 배치
- 그래프 색칠 (이진)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class TwoSAT(private val n: Int) {
    // 변수 i → 정점 2*i (참), 2*i+1 (거짓)
    private val size = 2 * n
    private val graph = Array(size) { mutableListOf<Int>() }
    private val reverse = Array(size) { mutableListOf<Int>() }

    private fun nodeTrue(i: Int) = 2 * i
    private fun nodeFalse(i: Int) = 2 * i + 1
    private fun neg(v: Int) = v xor 1

    // (a ∨ b) 추가: ¬a → b, ¬b → a
    fun addClause(varA: Int, valA: Boolean, varB: Int, valB: Boolean) {
        val a = if (valA) nodeTrue(varA) else nodeFalse(varA)
        val b = if (valB) nodeTrue(varB) else nodeFalse(varB)
        graph[neg(a)].add(b); reverse[b].add(neg(a))
        graph[neg(b)].add(a); reverse[a].add(neg(b))
    }

    fun solve(): IntArray? {
        // Kosaraju
        val visited = BooleanArray(size)
        val order = mutableListOf<Int>()
        fun dfs1(u: Int) {
            visited[u] = true
            for (v in graph[u]) if (!visited[v]) dfs1(v)
            order.add(u)
        }
        for (i in 0 until size) if (!visited[i]) dfs1(i)

        val comp = IntArray(size) { -1 }
        var c = 0
        fun dfs2(u: Int) {
            comp[u] = c
            for (v in reverse[u]) if (comp[v] == -1) dfs2(v)
        }
        for (u in order.reversed()) if (comp[u] == -1) { dfs2(u); c++ }

        val assignment = IntArray(n)
        for (i in 0 until n) {
            if (comp[nodeTrue(i)] == comp[nodeFalse(i)]) return null // UNSAT
            assignment[i] = if (comp[nodeTrue(i)] > comp[nodeFalse(i)]) 1 else 0
        }
        return assignment
    }
}
```

**관련 알고리즘**: Tarjan SCC, Kosaraju, SAT Solvers

---

<a id="eulerian-path"></a>
## 17. Eulerian Path / Circuit (오일러 경로/회로 - Hierholzer)

**목적**: 모든 간선을 정확히 한 번씩 지나는 경로(회로) 찾기

**시간 복잡도**: O(V + E)

**공간 복잡도**: O(V + E)

**특징**:
- 무방향: 모든 정점이 짝수 차수 → 회로 / 정확히 두 정점이 홀수 차수 → 경로
- 방향: in-degree == out-degree → 회로
- Hierholzer: 막힐 때까지 가다가 막히면 결과 스택에 추가, 다른 분기에서 재진입

**장점**:
- 선형 시간
- 모든 간선 순회 보장

**단점**:
- 조건 미충족이면 불가
- 큰 그래프에서 메모리

**활용 예시**:
- DNA 시퀀싱 (de Bruijn 그래프)
- 우편 배달 경로 (CPP)
- 미로 일필휘지

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
fun hierholzerDirected(n: Int, edges: List<Pair<Int, Int>>): List<Int>? {
    val adj = Array(n) { ArrayDeque<Int>() }
    val inDeg = IntArray(n)
    val outDeg = IntArray(n)
    for ((u, v) in edges) {
        adj[u].addLast(v); outDeg[u]++; inDeg[v]++
    }

    // 시작 정점 결정
    var start = -1
    var startCount = 0
    var endCount = 0
    for (i in 0 until n) {
        val diff = outDeg[i] - inDeg[i]
        when {
            diff == 1 -> { start = i; startCount++ }
            diff == -1 -> endCount++
            diff != 0 -> return null
        }
    }
    if (!(startCount == 0 && endCount == 0) && !(startCount == 1 && endCount == 1)) return null
    if (start == -1) start = (0 until n).firstOrNull { outDeg[it] > 0 } ?: 0

    val stack = ArrayDeque<Int>()
    val path = mutableListOf<Int>()
    stack.addLast(start)
    while (stack.isNotEmpty()) {
        val u = stack.last()
        if (adj[u].isNotEmpty()) {
            stack.addLast(adj[u].removeFirst())
        } else {
            path.add(stack.removeLast())
        }
    }
    if (path.size != edges.size + 1) return null
    return path.reversed()
}
```

**관련 알고리즘**: Fleury, Chinese Postman, Hamiltonian Path

---

<a id="stoer-wagner"></a>
## 18. Min Cut — Stoer-Wagner (전역 최소 컷)

**목적**: 무방향 가중 그래프의 전역 최소 컷(global min cut) 찾기

**시간 복잡도**: O(V³) 또는 O(VE + V² log V)

**공간 복잡도**: O(V²)

**특징**:
- 최대 유량 없이 직접 계산
- 매 단계 maximum adjacency ordering
- 마지막 두 정점을 합치며 컷 후보 갱신
- 양의 가중치만

**장점**:
- 한 번의 실행으로 모든 (s, t) 쌍 중 최소 컷
- 구현 비교적 단순

**단점**:
- 음수 가중치 처리 불가
- 밀집 그래프에 적합

**활용 예시**:
- 이미지 분할
- 네트워크 신뢰성
- 클러스터링 (그래프 분할)
- VLSI 설계

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
fun stoerWagner(graph: Array<IntArray>): Int {
    val n = graph.size
    val w = Array(n) { graph[it].copyOf() }
    val vertices = (0 until n).toMutableList()
    var best = Int.MAX_VALUE

    while (vertices.size > 1) {
        val added = BooleanArray(n)
        val weights = IntArray(n)
        var prev = -1
        var last = vertices[0]
        added[vertices[0]] = true

        for (step in 1 until vertices.size) {
            // weights 갱신
            for (v in vertices) {
                if (!added[v]) weights[v] += w[last][v]
            }
            // 가장 큰 weights 정점 선택
            var sel = -1
            for (v in vertices) {
                if (!added[v] && (sel == -1 || weights[v] > weights[sel])) sel = v
            }
            added[sel] = true
            prev = last
            last = sel
        }

        // last의 cut-of-the-phase
        if (weights[last] < best) best = weights[last]

        // prev에 last 합치기
        for (v in vertices) {
            if (v != prev && v != last) {
                w[prev][v] += w[last][v]
                w[v][prev] += w[v][last]
            }
        }
        vertices.remove(last)
    }
    return best
}
```

**관련 알고리즘**: Max Flow Min Cut, Karger's

---

<a id="heavy-light-decomposition"></a>
## 19. Heavy-Light Decomposition (HLD) (헤비-라이트 분해)

**목적**: 트리의 경로/서브트리 쿼리(합·최댓값·갱신)를 O(log² n)에 처리하기 위해 트리를 heavy 체인들로 분해하고 Segment Tree와 결합

**시간 복잡도**: 전처리 O(n), 경로 쿼리/갱신 O(log² n) (체인 O(log n) × Segment Tree O(log n))

**공간 복잡도**: O(n)

**특징**:
- 각 정점에서 서브트리 크기가 가장 큰 자식으로 가는 간선을 heavy edge, 나머지를 light edge로 분류
- light edge를 따라 내려가면 서브트리 크기가 절반 이하로 줄어들므로 루트→정점 경로의 light edge 개수는 최대 O(log n)
- heavy edge가 연결된 연속 구간(체인)을 DFS 순서로 배열에 평탄화해 Segment Tree/Fenwick Tree 한 개로 인덱싱
- 두 정점 간 경로는 최대 O(log n)개의 연속 체인 구간으로 분해되고, 각 구간을 Segment Tree로 질의
- 분해 과정에서 두 정점을 같은 체인으로 끌어올리는 동작이 LCA 계산을 겸함

**장점**:
- 트리 경로 합/최댓값/갱신을 정적 자료구조(Segment Tree)로 통일해 처리
- 정점 가중치와 간선 가중치 모두 지원 (간선은 자식 정점에 가중치를 부여하는 방식)
- 서브트리 쿼리도 DFS 진입 시각 기반 연속 구간으로 동일 Segment Tree에서 해결 가능

**단점**:
- 구현이 복잡하고 인덱스 관리(heavy/체인 head/position) 실수가 잦음
- 경로 쿼리가 O(log² n)으로, 단일 LCA만 필요하면 Binary Lifting(O(log n))이 더 단순·빠름
- 트리 구조 변경(간선 삽입/삭제)에는 적합하지 않음 — 동적 트리는 Link-Cut Tree 필요

**활용 예시**:
- 트리 위 두 정점 경로의 합/최댓값/최솟값 쿼리
- 경로 위 모든 정점/간선 값 일괄 갱신 (lazy propagation 결합)
- 네트워크 토폴로지에서 경로 비용 집계, 계통도 조상 구간 질의

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// 정점 가중치 경로 합 쿼리용 HLD (Segment Tree 결합)
class HeavyLightDecomposition(private val n: Int, private val adj: Array<MutableList<Int>>) {
    private val parent = IntArray(n) { -1 }
    private val depth = IntArray(n)
    private val heavy = IntArray(n) { -1 }   // 각 정점의 heavy child
    private val size = IntArray(n)
    private val head = IntArray(n)            // 정점이 속한 체인의 head
    private val pos = IntArray(n)             // Segment Tree 내 위치
    private var cur = 0
    private val seg = LongArray(4 * n)        // 합 Segment Tree

    private fun dfsSize(u: Int): Int {        // 서브트리 크기 + heavy child 계산
        size[u] = 1
        var maxSub = 0
        for (v in adj[u]) if (v != parent[u]) {
            parent[v] = u; depth[v] = depth[u] + 1
            val s = dfsSize(v); size[u] += s
            if (s > maxSub) { maxSub = s; heavy[u] = v }
        }
        return size[u]
    }

    private fun decompose(u: Int, h: Int) {  // 체인 분해 + 평탄화
        head[u] = h; pos[u] = cur++
        if (heavy[u] != -1) decompose(heavy[u], h)        // heavy child는 같은 체인
        for (v in adj[u]) if (v != parent[u] && v != heavy[u]) decompose(v, v)
    }

    fun build(root: Int, weight: LongArray) {
        dfsSize(root); decompose(root, root)
        for (u in 0 until n) update(1, 0, n - 1, pos[u], weight[u])
    }

    private fun update(node: Int, l: Int, r: Int, idx: Int, value: Long) {
        if (l == r) { seg[node] = value; return }
        val m = (l + r) / 2
        if (idx <= m) update(2 * node, l, m, idx, value) else update(2 * node + 1, m + 1, r, idx, value)
        seg[node] = seg[2 * node] + seg[2 * node + 1]
    }

    private fun query(node: Int, l: Int, r: Int, ql: Int, qr: Int): Long {
        if (qr < l || r < ql) return 0
        if (ql <= l && r <= qr) return seg[node]
        val m = (l + r) / 2
        return query(2 * node, l, m, ql, qr) + query(2 * node + 1, m + 1, r, ql, qr)
    }

    fun pathSum(a: Int, b: Int): Long {       // a~b 경로 합 (LCA 자동 처리)
        var u = a; var v = b; var res = 0L
        while (head[u] != head[v]) {          // 서로 다른 체인이면 깊은 head를 끌어올림
            if (depth[head[u]] < depth[head[v]]) { val t = u; u = v; v = t }
            res += query(1, 0, n - 1, pos[head[u]], pos[u]); u = parent[head[u]]
        }
        if (depth[u] > depth[v]) { val t = u; u = v; v = t }
        res += query(1, 0, n - 1, pos[u], pos[v])   // 같은 체인의 LCA~v 구간
        return res
    }
}
```

**관련 알고리즘**: Segment Tree, LCA, Binary Lifting, Fenwick Tree

---

<a id="centroid-decomposition"></a>
## 20. Centroid Decomposition (센트로이드 분할)

**목적**: 트리의 무게중심(centroid)을 재귀적으로 제거하며 분할정복하여, 모든 정점쌍 경로를 O(n log n) 깊이의 센트로이드 트리로 분해해 경로 카운팅/거리 쿼리를 해결

**시간 복잡도**: O(n log n) (구축) — 작업당 O(n) × log n 레벨

**공간 복잡도**: O(n) (인접 리스트 + 보조 배열) / 센트로이드 트리 저장 시 O(n)

**특징**:
- 센트로이드: 제거 시 남는 모든 서브트리 크기가 ≤ n/2 인 정점 (모든 트리에 1~2개 존재)
- 센트로이드를 제거 → 분리된 서브트리마다 재귀 → 재귀 깊이가 O(log n) 으로 보장됨
- 모든 경로는 "정점쌍의 LCA에 해당하는 센트로이드"를 정확히 한 번 통과 → 경로를 센트로이드 기준으로 분류 가능
- 한 센트로이드를 지나는 경로 = (한 서브트리 경로) + (다른 서브트리 경로). 같은 서브트리 쌍은 중복 제거(inclusion-exclusion)로 차감
- 분할정복 on tree의 대표 기법. 정적 트리(간선 불변) 쿼리에 적합

**장점**:
- 트리 위 분할정복으로 O(n²) 경로 문제를 O(n log n)으로 단축
- 센트로이드 트리 깊이가 O(log n) 이라 lift/누적 쿼리에 활용 가능
- "길이 정확히 k 경로 수", "거리 ≤ k 쌍 수" 등 거리 기반 집계에 강력

**단점**:
- 구현 난도 높음 (서브트리 크기 재계산, 중복 차감, 방문 표시 관리)
- 동적(간선 추가/삭제) 트리에는 부적합 — 재구축 비용 큼
- 가중 거리·복잡한 합산은 부속 자료구조(Fenwick/Segment Tree) 결합 필요

**활용 예시**:
- 길이 정확히 k인 경로의 개수 세기
- 두 정점 거리 ≤ d 인 쌍의 수, 경로 통계 집계
- 트리 위 최근접/거리 쿼리(센트로이드 트리에 거리 캐싱)
- 분할정복 기반 트리 DP 문제

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// 길이가 정확히 k(간선 수)인 경로의 개수를 센트로이드 분할로 계산
class CentroidDecomposition(private val n: Int, private val k: Int) {
    private val adj = Array(n) { mutableListOf<Int>() }
    private val removed = BooleanArray(n)
    private val subSize = IntArray(n)
    private val cnt = IntArray(k + 1)   // 현재 센트로이드 기준 거리별 누적 개수
    var answer = 0L; private set

    fun addEdge(u: Int, v: Int) { adj[u].add(v); adj[v].add(u) }

    private fun calcSize(u: Int, parent: Int): Int {
        subSize[u] = 1
        for (w in adj[u]) if (w != parent && !removed[w])
            subSize[u] += calcSize(w, u)
        return subSize[u]
    }

    private fun findCentroid(u: Int, parent: Int, treeSize: Int): Int {
        for (w in adj[u]) if (w != parent && !removed[w])
            if (subSize[w] > treeSize / 2) return findCentroid(w, u, treeSize)
        return u
    }

    // 거리 d(0..k)별 정점 수를 cnt 에 모으되, add=true 면 누적 / false 면 제거
    private fun collect(u: Int, parent: Int, depth: Int, add: Boolean) {
        if (depth > k) return
        cnt[depth] += if (add) 1 else -1
        for (w in adj[u]) if (w != parent && !removed[w])
            collect(w, u, depth + 1, add)
    }

    // 한 서브트리의 깊이 d 정점이 (k - d) 짝과 이루는 경로 수 합산
    private fun countPairs(u: Int, parent: Int, depth: Int): Long {
        if (depth > k) return 0L
        var res = cnt[k - depth].toLong()
        for (w in adj[u]) if (w != parent && !removed[w])
            res += countPairs(w, u, depth + 1)
        return res
    }

    private fun decompose(entry: Int) {
        val total = calcSize(entry, -1)
        val c = findCentroid(entry, -1, total)
        removed[c] = true
        cnt[0] = 1  // 센트로이드 자신(거리 0)
        for (w in adj[c]) if (!removed[w]) {
            answer += countPairs(w, c, 1)  // 이전 서브트리들과의 쌍만 카운트(중복 방지)
            collect(w, c, 1, true)         // 그 후 현재 서브트리를 누적
        }
        for (d in 0..k) cnt[d] = 0          // 다음 센트로이드 위해 초기화
        for (w in adj[c]) if (!removed[w]) decompose(w)
    }

    fun solve(): Long { answer = 0L; decompose(0); return answer }
}
```

**관련 알고리즘**: Merge Sort, LCA, DFS, Segment Tree
