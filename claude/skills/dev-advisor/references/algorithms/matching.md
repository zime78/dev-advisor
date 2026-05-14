# 매칭 알고리즘 (Matching Algorithms)

이분 그래프 매칭, 안정 매칭 등 짝짓기 문제를 해결하는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [bipartite-matching](#bipartite-matching) | Bipartite Matching | 이분 매칭 (Augmenting Path DFS) | 중간 |
| [hopcroft-karp](#hopcroft-karp) | Hopcroft-Karp | 홉크로프트-카프 | 높음 |
| [stable-marriage](#stable-marriage) | Stable Marriage (Gale-Shapley) | 안정 매칭 | 중간 |

---

<a id="bipartite-matching"></a>
## 1. Bipartite Matching (이분 매칭 — Augmenting Path DFS)

**목적**: 이분 그래프 좌/우 정점 간 최대 매칭 찾기

**시간 복잡도**: O(V * E)

**공간 복잡도**: O(V + E)

**특징**:
- 좌측 정점마다 DFS로 augmenting path 탐색
- 매칭 안 된 우측 정점 또는 재배치 가능한 우측 정점 찾기
- Hungarian 단순화 버전

**장점**:
- 구현 단순
- 작은~중간 그래프에 충분

**단점**:
- 대규모 그래프에서 느림
- Hopcroft-Karp가 점근적으로 더 빠름

**활용 예시**:
- 작업-기계 할당
- 학생-과목 배정
- 결혼 매칭 (단순)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
class BipartiteMatching(private val left: Int, private val right: Int) {
    private val graph = Array(left) { mutableListOf<Int>() }
    private val matchR = IntArray(right) { -1 }

    fun addEdge(u: Int, v: Int) {
        graph[u].add(v)
    }

    private fun dfs(u: Int, visited: BooleanArray): Boolean {
        for (v in graph[u]) {
            if (visited[v]) continue
            visited[v] = true
            if (matchR[v] == -1 || dfs(matchR[v], visited)) {
                matchR[v] = u
                return true
            }
        }
        return false
    }

    fun maxMatching(): Int {
        var result = 0
        for (u in 0 until left) {
            val visited = BooleanArray(right)
            if (dfs(u, visited)) result++
        }
        return result
    }

    fun matchingPairs(): List<Pair<Int, Int>> {
        val pairs = mutableListOf<Pair<Int, Int>>()
        for (v in 0 until right) {
            if (matchR[v] != -1) pairs.add(matchR[v] to v)
        }
        return pairs
    }
}
```

**관련 알고리즘**: Hopcroft-Karp, Hungarian, Max Flow

---

<a id="hopcroft-karp"></a>
## 2. Hopcroft-Karp (홉크로프트-카프)

**목적**: BFS로 여러 augmenting path를 동시에 찾는 이분 매칭

**시간 복잡도**: O(E * √V)

**공간 복잡도**: O(V + E)

**특징**:
- 단계마다 BFS로 level graph 구성
- DFS로 disjoint augmenting paths 동시 탐색
- 단위 용량 Dinic과 동치

**장점**:
- 이분 매칭에서 점근적으로 가장 빠름
- 대규모 그래프에 적합

**단점**:
- 구현 복잡
- 작은 그래프에선 오버킬

**활용 예시**:
- 대규모 이분 매칭
- 자원 할당 최적화
- 광고-슬롯 매칭

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.util.ArrayDeque

class HopcroftKarp(private val left: Int, private val right: Int) {
    private val graph = Array(left) { mutableListOf<Int>() }
    private val pairU = IntArray(left) { -1 }
    private val pairV = IntArray(right) { -1 }
    private val dist = IntArray(left)
    private val INF = Int.MAX_VALUE

    fun addEdge(u: Int, v: Int) {
        graph[u].add(v)
    }

    private fun bfs(): Boolean {
        val queue = ArrayDeque<Int>()
        for (u in 0 until left) {
            if (pairU[u] == -1) {
                dist[u] = 0
                queue.add(u)
            } else dist[u] = INF
        }
        var found = false
        while (queue.isNotEmpty()) {
            val u = queue.poll()
            for (v in graph[u]) {
                val pair = pairV[v]
                if (pair == -1) {
                    found = true
                } else if (dist[pair] == INF) {
                    dist[pair] = dist[u] + 1
                    queue.add(pair)
                }
            }
        }
        return found
    }

    private fun dfs(u: Int): Boolean {
        for (v in graph[u]) {
            val pair = pairV[v]
            if (pair == -1 || (dist[pair] == dist[u] + 1 && dfs(pair))) {
                pairU[u] = v
                pairV[v] = u
                return true
            }
        }
        dist[u] = INF
        return false
    }

    fun maxMatching(): Int {
        var matching = 0
        while (bfs()) {
            for (u in 0 until left) {
                if (pairU[u] == -1 && dfs(u)) matching++
            }
        }
        return matching
    }
}
```

**관련 알고리즘**: Dinic, Bipartite Matching

---

<a id="stable-marriage"></a>
## 3. Stable Marriage (Gale-Shapley, 안정 매칭)

**목적**: 양측 선호도 리스트가 주어졌을 때 안정 매칭(불안정 쌍 없음) 찾기

**시간 복잡도**: O(n²) - n: 한쪽 인원

**공간 복잡도**: O(n²)

**특징**:
- 한쪽이 제안, 다른 쪽이 수락/거절
- 제안자측에 최적, 피제안자측에 최악
- 항상 안정 매칭 존재

**장점**:
- 다항 시간 보장
- 결과의 안정성 수학적으로 증명됨

**단점**:
- 비대칭 (제안자 유리)
- 선호도 입력 크기 O(n²)

**활용 예시**:
- 의대 인턴-병원 매칭 (NRMP)
- 학교 배정
- 룸메이트 매칭 (변형 필요)

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.util.ArrayDeque

// menPref[i] = i번 남자의 선호 여자 순서 (인덱스 리스트)
// womenPref[j] = j번 여자의 선호 남자 순서
fun stableMarriage(
    menPref: Array<IntArray>,
    womenPref: Array<IntArray>
): IntArray {
    val n = menPref.size

    // 여자측 ranking: womenRank[j][i] = j번 여자가 매기는 i번 남자의 순위
    val womenRank = Array(n) { IntArray(n) }
    for (j in 0 until n) {
        for (rank in 0 until n) {
            womenRank[j][womenPref[j][rank]] = rank
        }
    }

    val nextProposal = IntArray(n) // 남자가 다음에 제안할 인덱스
    val womanPartner = IntArray(n) { -1 } // 여자 j의 현재 파트너

    val freeMen = ArrayDeque<Int>()
    for (i in 0 until n) freeMen.add(i)

    while (freeMen.isNotEmpty()) {
        val m = freeMen.poll()
        val w = menPref[m][nextProposal[m]]
        nextProposal[m]++

        val current = womanPartner[w]
        if (current == -1) {
            womanPartner[w] = m
        } else if (womenRank[w][m] < womenRank[w][current]) {
            womanPartner[w] = m
            freeMen.add(current)
        } else {
            freeMen.add(m)
        }
    }

    // manPartner[i] = i번 남자의 파트너 여자
    val manPartner = IntArray(n)
    for (w in 0 until n) {
        if (womanPartner[w] != -1) manPartner[womanPartner[w]] = w
    }
    return manPartner
}
```

**관련 알고리즘**: Hungarian, Bipartite Matching

---
