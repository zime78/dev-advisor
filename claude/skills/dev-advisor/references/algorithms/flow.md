# 네트워크 플로우 알고리즘 (Network Flow Algorithms)

방향 가중 그래프에서 최대 유량, 최소 비용 유량 등을 계산하는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [ford-fulkerson](#ford-fulkerson) | Ford-Fulkerson | 포드-풀커슨 | 중간 |
| [edmonds-karp](#edmonds-karp) | Edmonds-Karp | 에드몬즈-카프 | 중간 |
| [dinic](#dinic) | Dinic | 디닉 | 높음 |
| [mcmf](#mcmf) | Min-Cost Max-Flow | 최소 비용 최대 유량 | 높음 |

---

<a id="ford-fulkerson"></a>
## 1. Ford-Fulkerson (포드-풀커슨)

**목적**: source에서 sink까지 최대 유량 계산 (DFS 기반 증가 경로)

**시간 복잡도**: O(E * f) - f: 최대 유량 값

**공간 복잡도**: O(V + E)

**특징**:
- 증가 경로(augmenting path)를 DFS로 탐색
- 잔여 그래프(residual graph) 사용
- 정수 용량에서만 종료 보장

**장점**:
- 개념적으로 가장 단순
- 구현 직관적

**단점**:
- 실수/큰 용량에서 종료 못할 수 있음
- f가 크면 매우 느림

**활용 예시**:
- 작은 네트워크의 최대 유량
- 이분 매칭 (단순 변형)
- 알고리즘 입문 학습

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
class FordFulkerson(private val n: Int) {
    private val capacity = Array(n) { IntArray(n) }
    private val graph = Array(n) { mutableListOf<Int>() }

    fun addEdge(from: Int, to: Int, cap: Int) {
        capacity[from][to] += cap
        graph[from].add(to)
        graph[to].add(from) // 역간선
    }

    private fun dfs(u: Int, t: Int, pushed: Int, visited: BooleanArray): Int {
        if (u == t) return pushed
        visited[u] = true
        for (v in graph[u]) {
            if (!visited[v] && capacity[u][v] > 0) {
                val d = dfs(v, t, minOf(pushed, capacity[u][v]), visited)
                if (d > 0) {
                    capacity[u][v] -= d
                    capacity[v][u] += d
                    return d
                }
            }
        }
        return 0
    }

    fun maxFlow(s: Int, t: Int): Int {
        var flow = 0
        while (true) {
            val visited = BooleanArray(n)
            val pushed = dfs(s, t, Int.MAX_VALUE, visited)
            if (pushed == 0) break
            flow += pushed
        }
        return flow
    }
}
```

**관련 알고리즘**: Edmonds-Karp, Dinic

---

<a id="edmonds-karp"></a>
## 2. Edmonds-Karp (에드몬즈-카프)

**목적**: BFS로 증가 경로를 찾는 Ford-Fulkerson 개선판

**시간 복잡도**: O(V * E²)

**공간 복잡도**: O(V + E)

**특징**:
- BFS로 최단 증가 경로 보장
- 정수가 아닌 용량에서도 종료 보장
- 인접 리스트 + 역간선 인덱스로 잔여 그래프 표현

**장점**:
- 다항 시간 종료 보장
- 구현 비교적 단순

**단점**:
- 밀집 그래프에서 느림
- Dinic보다 느림

**활용 예시**:
- 중간 규모 최대 유량
- 이분 매칭
- 프로젝트 선택 문제

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.ArrayDeque

class EdmondsKarp(private val n: Int) {
    data class FEdge(val to: Int, var cap: Int, val rev: Int)
    private val graph = Array(n) { mutableListOf<FEdge>() }

    fun addEdge(from: Int, to: Int, cap: Int) {
        graph[from].add(FEdge(to, cap, graph[to].size))
        graph[to].add(FEdge(from, 0, graph[from].size - 1))
    }

    fun maxFlow(s: Int, t: Int): Int {
        var flow = 0
        while (true) {
            val parent = IntArray(n) { -1 }
            val parentEdge = IntArray(n) { -1 }
            parent[s] = s
            val queue = ArrayDeque<Int>()
            queue.add(s)

            while (queue.isNotEmpty() && parent[t] == -1) {
                val u = queue.poll()
                for ((idx, e) in graph[u].withIndex()) {
                    if (parent[e.to] == -1 && e.cap > 0) {
                        parent[e.to] = u
                        parentEdge[e.to] = idx
                        queue.add(e.to)
                    }
                }
            }

            if (parent[t] == -1) break

            // 경로상 최소 용량 찾기
            var pushed = Int.MAX_VALUE
            var v = t
            while (v != s) {
                val u = parent[v]
                pushed = minOf(pushed, graph[u][parentEdge[v]].cap)
                v = u
            }

            // 증가 + 잔여 갱신
            v = t
            while (v != s) {
                val u = parent[v]
                val e = graph[u][parentEdge[v]]
                e.cap -= pushed
                graph[v][e.rev].cap += pushed
                v = u
            }

            flow += pushed
        }
        return flow
    }
}
```

**관련 알고리즘**: Ford-Fulkerson, Dinic

---

<a id="dinic"></a>
## 3. Dinic (디닉)

**목적**: Level graph + Blocking flow로 최대 유량 효율적 계산

**시간 복잡도**: O(V² * E) 일반, 단위 용량 그래프에서 O(E * √V)

**공간 복잡도**: O(V + E)

**특징**:
- BFS로 level graph 구성
- DFS로 blocking flow 추출
- 단위 용량 그래프(이분 매칭)에서 매우 빠름

**장점**:
- 실용적으로 가장 빠른 max flow 중 하나
- 이분 매칭에서 Hopcroft-Karp와 동급

**단점**:
- 구현이 길고 디버깅 어려움

**활용 예시**:
- 대규모 최대 유량
- 이분 매칭
- 프로젝트 선택, 영역 분할

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.util.ArrayDeque

class Dinic(private val n: Int) {
    data class FEdge(val to: Int, var cap: Long, val rev: Int)
    private val graph = Array(n) { mutableListOf<FEdge>() }
    private val level = IntArray(n)
    private val iter = IntArray(n)

    fun addEdge(from: Int, to: Int, cap: Long) {
        graph[from].add(FEdge(to, cap, graph[to].size))
        graph[to].add(FEdge(from, 0L, graph[from].size - 1))
    }

    private fun bfs(s: Int, t: Int): Boolean {
        level.fill(-1)
        level[s] = 0
        val q = ArrayDeque<Int>()
        q.add(s)
        while (q.isNotEmpty()) {
            val u = q.poll()
            for (e in graph[u]) {
                if (e.cap > 0 && level[e.to] == -1) {
                    level[e.to] = level[u] + 1
                    q.add(e.to)
                }
            }
        }
        return level[t] != -1
    }

    private fun dfs(u: Int, t: Int, pushed: Long): Long {
        if (u == t) return pushed
        while (iter[u] < graph[u].size) {
            val e = graph[u][iter[u]]
            if (e.cap > 0 && level[e.to] == level[u] + 1) {
                val d = dfs(e.to, t, minOf(pushed, e.cap))
                if (d > 0) {
                    e.cap -= d
                    graph[e.to][e.rev].cap += d
                    return d
                }
            }
            iter[u]++
        }
        return 0L
    }

    fun maxFlow(s: Int, t: Int): Long {
        var flow = 0L
        while (bfs(s, t)) {
            iter.fill(0)
            while (true) {
                val pushed = dfs(s, t, Long.MAX_VALUE)
                if (pushed == 0L) break
                flow += pushed
            }
        }
        return flow
    }
}
```

**관련 알고리즘**: Edmonds-Karp, Hopcroft-Karp

---

<a id="mcmf"></a>
## 4. Min-Cost Max-Flow (최소 비용 최대 유량)

**목적**: 최대 유량을 보내면서 총 비용 최소화 (SPFA + 증가 경로)

**시간 복잡도**: O(F * V * E) - F: 총 유량, SPFA 기반

**공간 복잡도**: O(V + E)

**특징**:
- 각 간선이 (용량, 비용) 보유
- SPFA(Bellman-Ford 변형)로 최단(최소 비용) 경로 탐색
- 음수 비용 가능 (역간선 비용은 음수)

**장점**:
- 비용 최적화까지 동시 해결
- 음수 비용 처리 가능

**단점**:
- 일반 max flow보다 느림
- 음수 사이클 있으면 동작 안 함

**활용 예시**:
- 할당 문제 (assignment)
- 운송 문제 (transportation)
- 작업 스케줄링 (비용 포함)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.util.ArrayDeque

class MinCostMaxFlow(private val n: Int) {
    data class CEdge(val to: Int, var cap: Int, val cost: Int, val rev: Int)
    private val graph = Array(n) { mutableListOf<CEdge>() }

    fun addEdge(from: Int, to: Int, cap: Int, cost: Int) {
        graph[from].add(CEdge(to, cap, cost, graph[to].size))
        graph[to].add(CEdge(from, 0, -cost, graph[from].size - 1))
    }

    fun minCostFlow(s: Int, t: Int): Pair<Int, Int> {
        var totalFlow = 0
        var totalCost = 0
        val INF = Int.MAX_VALUE / 4

        while (true) {
            // SPFA로 최소 비용 경로 찾기
            val dist = IntArray(n) { INF }
            val inQueue = BooleanArray(n)
            val prevNode = IntArray(n) { -1 }
            val prevEdge = IntArray(n) { -1 }
            dist[s] = 0
            val q = ArrayDeque<Int>()
            q.add(s)
            inQueue[s] = true

            while (q.isNotEmpty()) {
                val u = q.poll()
                inQueue[u] = false
                for ((idx, e) in graph[u].withIndex()) {
                    if (e.cap > 0 && dist[u] + e.cost < dist[e.to]) {
                        dist[e.to] = dist[u] + e.cost
                        prevNode[e.to] = u
                        prevEdge[e.to] = idx
                        if (!inQueue[e.to]) {
                            q.add(e.to)
                            inQueue[e.to] = true
                        }
                    }
                }
            }

            if (dist[t] == INF) break

            // 경로상 최소 용량
            var pushed = INF
            var v = t
            while (v != s) {
                val u = prevNode[v]
                pushed = minOf(pushed, graph[u][prevEdge[v]].cap)
                v = u
            }

            // 갱신
            v = t
            while (v != s) {
                val u = prevNode[v]
                val e = graph[u][prevEdge[v]]
                e.cap -= pushed
                graph[v][e.rev].cap += pushed
                v = u
            }

            totalFlow += pushed
            totalCost += pushed * dist[t]
        }

        return totalFlow to totalCost
    }
}
```

**관련 알고리즘**: Hungarian, Edmonds-Karp

---
