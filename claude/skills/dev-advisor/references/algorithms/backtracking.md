# 백트래킹 (Backtracking)

가능한 모든 해를 탐색하면서 조건을 만족하지 않으면 되돌아가는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [n-queens](#n-queens) | N-Queens | N-퀸 | 중간 |
| [sudoku-solver](#sudoku-solver) | Sudoku Solver | 스도쿠 풀이 | 중간 |
| [graph-coloring](#graph-coloring) | Graph Coloring | 그래프 색칠 | 중간 |
| [hamiltonian-cycle](#hamiltonian-cycle) | Hamiltonian Cycle | 해밀턴 순환 | 높음 |
| [subset-sum](#subset-sum) | Subset Sum | 부분집합 합 | 중간 |

---

<a id="n-queens"></a>
## 1. N-Queens (N-퀸)

**목적**: N×N 체스판에 N개의 퀸을 서로 공격하지 않게 배치

**시간 복잡도**: O(N!)

**공간 복잡도**: O(N)

**특징**:
- 대표적인 백트래킹 문제
- 행 단위로 퀸 배치

**장점**:
- 가지치기로 탐색 공간 축소
- 다양한 최적화 가능

**단점**:
- 지수적 시간 복잡도

**활용 예시**:
- 조합 최적화
- 제약 만족 문제
- 스케줄링

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// 모든 해 찾기
fun solveNQueens(n: Int): List<List<String>> {
    val solutions = mutableListOf<List<String>>()
    val board = IntArray(n) { -1 } // board[row] = 퀸이 놓인 열

    fun isSafe(row: Int, col: Int): Boolean {
        for (prevRow in 0 until row) {
            val prevCol = board[prevRow]
            // 같은 열 또는 대각선 체크
            if (prevCol == col || kotlin.math.abs(prevRow - row) == kotlin.math.abs(prevCol - col)) {
                return false
            }
        }
        return true
    }

    fun solve(row: Int) {
        if (row == n) {
            // 해 찾음
            val solution = board.map { col ->
                ".".repeat(col) + "Q" + ".".repeat(n - col - 1)
            }
            solutions.add(solution)
            return
        }

        for (col in 0 until n) {
            if (isSafe(row, col)) {
                board[row] = col
                solve(row + 1)
                board[row] = -1 // 백트래킹
            }
        }
    }

    solve(0)
    return solutions
}

// 해의 개수만 카운트
fun countNQueens(n: Int): Int {
    var count = 0
    val cols = BooleanArray(n)
    val diag1 = BooleanArray(2 * n - 1) // 주대각선
    val diag2 = BooleanArray(2 * n - 1) // 부대각선

    fun solve(row: Int) {
        if (row == n) {
            count++
            return
        }

        for (col in 0 until n) {
            val d1 = row - col + n - 1
            val d2 = row + col

            if (!cols[col] && !diag1[d1] && !diag2[d2]) {
                cols[col] = true
                diag1[d1] = true
                diag2[d2] = true

                solve(row + 1)

                cols[col] = false
                diag1[d1] = false
                diag2[d2] = false
            }
        }
    }

    solve(0)
    return count
}

// 비트마스크 최적화
fun countNQueensBitmask(n: Int): Int {
    var count = 0
    val all = (1 shl n) - 1

    fun solve(cols: Int, diag1: Int, diag2: Int) {
        if (cols == all) {
            count++
            return
        }

        var available = all and (cols or diag1 or diag2).inv()
        while (available != 0) {
            val pos = available and (-available) // 가장 오른쪽 1비트
            available = available and (available - 1)

            solve(
                cols or pos,
                (diag1 or pos) shl 1,
                (diag2 or pos) shr 1
            )
        }
    }

    solve(0, 0, 0)
    return count
}
```

**관련 알고리즘**: Sudoku Solver, Graph Coloring

---

<a id="sudoku-solver"></a>
## 2. Sudoku Solver (스도쿠 풀이)

**목적**: 9×9 스도쿠 퍼즐 해결

**시간 복잡도**: O(9^(81)) 최악, 실제로는 훨씬 빠름

**공간 복잡도**: O(81)

**특징**:
- 제약 전파 + 백트래킹
- 빈 칸에 가능한 숫자 시도

**장점**:
- 어려운 스도쿠도 해결
- 다양한 최적화 가능

**단점**:
- 최악의 경우 느림

**활용 예시**:
- 퍼즐 게임
- 제약 만족 문제

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
fun solveSudoku(board: Array<IntArray>): Boolean {
    val empty = findEmpty(board) ?: return true
    val (row, col) = empty

    for (num in 1..9) {
        if (isValid(board, row, col, num)) {
            board[row][col] = num

            if (solveSudoku(board)) return true

            board[row][col] = 0 // 백트래킹
        }
    }

    return false
}

private fun findEmpty(board: Array<IntArray>): Pair<Int, Int>? {
    for (i in 0 until 9) {
        for (j in 0 until 9) {
            if (board[i][j] == 0) return i to j
        }
    }
    return null
}

private fun isValid(board: Array<IntArray>, row: Int, col: Int, num: Int): Boolean {
    // 행 검사
    if (num in board[row]) return false

    // 열 검사
    for (i in 0 until 9) {
        if (board[i][col] == num) return false
    }

    // 3×3 박스 검사
    val boxRow = (row / 3) * 3
    val boxCol = (col / 3) * 3
    for (i in boxRow until boxRow + 3) {
        for (j in boxCol until boxCol + 3) {
            if (board[i][j] == num) return false
        }
    }

    return true
}

// 최적화: 가능한 숫자 추적
class SudokuSolverOptimized {
    private val board = Array(9) { IntArray(9) }
    private val rowUsed = Array(9) { BooleanArray(10) }
    private val colUsed = Array(9) { BooleanArray(10) }
    private val boxUsed = Array(9) { BooleanArray(10) }

    fun solve(input: Array<IntArray>): Boolean {
        // 초기화
        for (i in 0 until 9) {
            for (j in 0 until 9) {
                board[i][j] = input[i][j]
                if (input[i][j] != 0) {
                    val num = input[i][j]
                    rowUsed[i][num] = true
                    colUsed[j][num] = true
                    boxUsed[(i / 3) * 3 + j / 3][num] = true
                }
            }
        }

        return backtrack()
    }

    private fun backtrack(): Boolean {
        val empty = findEmpty() ?: return true
        val (row, col) = empty
        val box = (row / 3) * 3 + col / 3

        for (num in 1..9) {
            if (!rowUsed[row][num] && !colUsed[col][num] && !boxUsed[box][num]) {
                board[row][col] = num
                rowUsed[row][num] = true
                colUsed[col][num] = true
                boxUsed[box][num] = true

                if (backtrack()) return true

                board[row][col] = 0
                rowUsed[row][num] = false
                colUsed[col][num] = false
                boxUsed[box][num] = false
            }
        }

        return false
    }

    private fun findEmpty(): Pair<Int, Int>? {
        for (i in 0 until 9) {
            for (j in 0 until 9) {
                if (board[i][j] == 0) return i to j
            }
        }
        return null
    }

    fun getBoard(): Array<IntArray> = board
}
```

**관련 알고리즘**: N-Queens, CSP

---

<a id="graph-coloring"></a>
## 3. Graph Coloring (그래프 색칠)

**목적**: 인접한 정점이 같은 색을 갖지 않도록 최소 색상으로 색칠

**시간 복잡도**: O(m^n) - m: 색상 수, n: 정점 수

**공간 복잡도**: O(n)

**특징**:
- NP-Complete 문제
- 백트래킹으로 해 탐색

**장점**:
- 정확한 해 찾기
- 색상 수 최소화 가능

**단점**:
- 지수적 시간 복잡도

**활용 예시**:
- 스케줄링 (시간표)
- 레지스터 할당
- 지도 색칠

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
fun graphColoring(graph: Map<Int, List<Int>>, n: Int, m: Int): IntArray? {
    val colors = IntArray(n) { 0 } // 0 = 미할당

    fun isSafe(node: Int, color: Int): Boolean {
        return graph[node]?.all { neighbor ->
            colors[neighbor] != color
        } ?: true
    }

    fun solve(node: Int): Boolean {
        if (node == n) return true

        for (color in 1..m) {
            if (isSafe(node, color)) {
                colors[node] = color

                if (solve(node + 1)) return true

                colors[node] = 0 // 백트래킹
            }
        }

        return false
    }

    return if (solve(0)) colors else null
}

// 최소 색상 수 찾기
fun chromaticNumber(graph: Map<Int, List<Int>>, n: Int): Int {
    for (m in 1..n) {
        if (graphColoring(graph, n, m) != null) {
            return m
        }
    }
    return n
}

// 그리디 색칠 (근사 알고리즘)
fun greedyColoring(graph: Map<Int, List<Int>>, n: Int): IntArray {
    val colors = IntArray(n) { -1 }

    for (node in 0 until n) {
        val usedColors = mutableSetOf<Int>()
        graph[node]?.forEach { neighbor ->
            if (colors[neighbor] != -1) {
                usedColors.add(colors[neighbor])
            }
        }

        // 사용되지 않은 가장 작은 색상 선택
        var color = 0
        while (color in usedColors) color++
        colors[node] = color
    }

    return colors
}

// Welsh-Powell 알고리즘 (정점 차수 순 정렬)
fun welshPowell(graph: Map<Int, List<Int>>, n: Int): IntArray {
    val colors = IntArray(n) { -1 }
    val degrees = IntArray(n) { node -> graph[node]?.size ?: 0 }
    val order = (0 until n).sortedByDescending { degrees[it] }

    var colorNum = 0

    for (node in order) {
        if (colors[node] != -1) continue

        val usedColors = mutableSetOf<Int>()
        graph[node]?.forEach { neighbor ->
            if (colors[neighbor] != -1) {
                usedColors.add(colors[neighbor])
            }
        }

        var color = 0
        while (color in usedColors) color++
        colors[node] = color
        colorNum = maxOf(colorNum, color + 1)
    }

    return colors
}
```

**관련 알고리즘**: N-Queens, Map Coloring

---

<a id="hamiltonian-cycle"></a>
## 4. Hamiltonian Cycle (해밀턴 순환)

**목적**: 모든 정점을 한 번씩 방문하고 시작점으로 돌아오는 경로 찾기

**시간 복잡도**: O(N!)

**공간 복잡도**: O(N)

**특징**:
- NP-Complete 문제
- TSP의 기본 형태

**장점**:
- 정확한 해 찾기
- 모든 경로 탐색

**단점**:
- 지수적 시간 복잡도

**활용 예시**:
- 외판원 문제 (TSP)
- 경로 계획
- 네트워크 설계

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
fun hamiltonianCycle(graph: Array<BooleanArray>): List<Int>? {
    val n = graph.size
    val path = mutableListOf<Int>()
    val visited = BooleanArray(n)

    path.add(0)
    visited[0] = true

    fun solve(): Boolean {
        if (path.size == n) {
            // 시작점으로 돌아갈 수 있는지 확인
            return graph[path.last()][0]
        }

        for (v in 1 until n) {
            if (!visited[v] && graph[path.last()][v]) {
                path.add(v)
                visited[v] = true

                if (solve()) return true

                path.removeAt(path.size - 1)
                visited[v] = false
            }
        }

        return false
    }

    return if (solve()) {
        path + 0 // 시작점 추가
    } else {
        null
    }
}

// 해밀턴 경로 (시작점으로 안 돌아가도 됨)
fun hamiltonianPath(graph: Array<BooleanArray>): List<Int>? {
    val n = graph.size

    for (start in 0 until n) {
        val path = mutableListOf<Int>()
        val visited = BooleanArray(n)

        path.add(start)
        visited[start] = true

        fun solve(): Boolean {
            if (path.size == n) return true

            for (v in 0 until n) {
                if (!visited[v] && graph[path.last()][v]) {
                    path.add(v)
                    visited[v] = true

                    if (solve()) return true

                    path.removeAt(path.size - 1)
                    visited[v] = false
                }
            }

            return false
        }

        if (solve()) return path
    }

    return null
}

// 모든 해밀턴 순환 찾기
fun allHamiltonianCycles(graph: Array<BooleanArray>): List<List<Int>> {
    val n = graph.size
    val result = mutableListOf<List<Int>>()
    val path = mutableListOf<Int>()
    val visited = BooleanArray(n)

    path.add(0)
    visited[0] = true

    fun solve() {
        if (path.size == n) {
            if (graph[path.last()][0]) {
                result.add(path.toList() + 0)
            }
            return
        }

        for (v in 1 until n) {
            if (!visited[v] && graph[path.last()][v]) {
                path.add(v)
                visited[v] = true

                solve()

                path.removeAt(path.size - 1)
                visited[v] = false
            }
        }
    }

    solve()
    return result
}
```

**관련 알고리즘**: TSP, Eulerian Path

---

<a id="subset-sum"></a>
## 5. Subset Sum (부분집합 합)

**목적**: 합이 특정 값이 되는 부분집합 찾기

**시간 복잡도**: O(2^n) 백트래킹, O(nS) DP

**공간 복잡도**: O(n)

**특징**:
- NP-Complete 문제
- DP로도 해결 가능

**장점**:
- 모든 해 탐색 가능
- 가지치기로 효율화

**단점**:
- 지수적 시간 복잡도

**활용 예시**:
- 자원 분배
- 예산 배분
- 암호학

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// 백트래킹 - 해 하나 찾기
fun subsetSum(nums: IntArray, target: Int): List<Int>? {
    val result = mutableListOf<Int>()

    fun solve(index: Int, currentSum: Int): Boolean {
        if (currentSum == target) return true
        if (index >= nums.size || currentSum > target) return false

        // 현재 원소 포함
        result.add(nums[index])
        if (solve(index + 1, currentSum + nums[index])) return true
        result.removeAt(result.size - 1)

        // 현재 원소 미포함
        return solve(index + 1, currentSum)
    }

    return if (solve(0, 0)) result else null
}

// 모든 부분집합 찾기
fun allSubsetSums(nums: IntArray, target: Int): List<List<Int>> {
    val results = mutableListOf<List<Int>>()
    val current = mutableListOf<Int>()

    fun solve(index: Int, currentSum: Int) {
        if (currentSum == target) {
            results.add(current.toList())
            return
        }
        if (index >= nums.size || currentSum > target) return

        // 포함
        current.add(nums[index])
        solve(index + 1, currentSum + nums[index])
        current.removeAt(current.size - 1)

        // 미포함 (중복 방지를 위해 같은 값 건너뛰기)
        var next = index + 1
        while (next < nums.size && nums[next] == nums[index]) next++
        solve(next, currentSum)
    }

    nums.sort()
    solve(0, 0)
    return results
}

// DP 방식 - 존재 여부만 확인
fun subsetSumExists(nums: IntArray, target: Int): Boolean {
    val dp = BooleanArray(target + 1)
    dp[0] = true

    for (num in nums) {
        for (j in target downTo num) {
            dp[j] = dp[j] || dp[j - num]
        }
    }

    return dp[target]
}

// DP 방식 - 부분집합 복원
fun subsetSumDP(nums: IntArray, target: Int): List<Int>? {
    val dp = Array(nums.size + 1) { BooleanArray(target + 1) }
    dp[0][0] = true

    for (i in 1..nums.size) {
        for (j in 0..target) {
            dp[i][j] = dp[i - 1][j]
            if (j >= nums[i - 1]) {
                dp[i][j] = dp[i][j] || dp[i - 1][j - nums[i - 1]]
            }
        }
    }

    if (!dp[nums.size][target]) return null

    // 역추적
    val result = mutableListOf<Int>()
    var i = nums.size
    var j = target

    while (i > 0 && j > 0) {
        if (dp[i][j] && !dp[i - 1][j]) {
            result.add(nums[i - 1])
            j -= nums[i - 1]
        }
        i--
    }

    return result
}

// 부분집합 합 개수 (DP)
fun countSubsetSums(nums: IntArray, target: Int): Int {
    val dp = IntArray(target + 1)
    dp[0] = 1

    for (num in nums) {
        for (j in target downTo num) {
            dp[j] += dp[j - num]
        }
    }

    return dp[target]
}
```

**관련 알고리즘**: Knapsack, Partition Problem

