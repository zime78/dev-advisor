# 게임/탐색 AI 알고리즘 (Game & Search AI)

게임 트리 탐색, 메타휴리스틱 최적화 등 AI 의사결정 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [minimax](#minimax) | Minimax | 미니맥스 | 중간 |
| [alpha-beta](#alpha-beta) | Alpha-Beta Pruning | 알파-베타 가지치기 | 중간 |
| [mcts](#mcts) | Monte Carlo Tree Search | 몬테카를로 트리 탐색 | 높음 |
| [genetic-algorithm](#genetic-algorithm) | Genetic Algorithm | 유전 알고리즘 | 중간 |
| [simulated-annealing](#simulated-annealing) | Simulated Annealing | 시뮬레이티드 어닐링 | 중간 |

---

<a id="minimax"></a>
## 1. Minimax (미니맥스)

**목적**: 두 플레이어 제로섬 게임에서 최적 수 결정. MAX는 최대화, MIN은 최소화

**시간 복잡도**: O(b^d) - b: 분기 계수, d: 깊이

**공간 복잡도**: O(b * d)

**특징**:
- 게임 트리 완전 탐색
- 평가 함수 + 깊이 제한
- 항상 최적 (트리 완전 탐색 시)

**장점**:
- 개념 명확
- 최적성 보장 (완전 탐색)

**단점**:
- 분기 많으면 비현실적
- 평가 함수 설계 중요

**활용 예시**:
- Tic-Tac-Toe, Connect 4
- 체스/체커 (얕은 깊이)
- 보드게임 AI 입문

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
interface GameState {
    fun isTerminal(): Boolean
    fun evaluate(): Int           // MAX 관점
    fun children(): List<GameState>
    val isMaxTurn: Boolean
}

fun minimax(state: GameState, depth: Int): Int {
    if (depth == 0 || state.isTerminal()) return state.evaluate()

    return if (state.isMaxTurn) {
        var best = Int.MIN_VALUE
        for (child in state.children()) {
            best = maxOf(best, minimax(child, depth - 1))
        }
        best
    } else {
        var best = Int.MAX_VALUE
        for (child in state.children()) {
            best = minOf(best, minimax(child, depth - 1))
        }
        best
    }
}

// 최선의 자식 선택
fun <S : GameState> bestMove(state: S, depth: Int): S? {
    var best: S? = null
    var bestScore = if (state.isMaxTurn) Int.MIN_VALUE else Int.MAX_VALUE
    for (child in state.children()) {
        @Suppress("UNCHECKED_CAST")
        val c = child as S
        val score = minimax(c, depth - 1)
        if (state.isMaxTurn && score > bestScore) {
            bestScore = score; best = c
        } else if (!state.isMaxTurn && score < bestScore) {
            bestScore = score; best = c
        }
    }
    return best
}
```

**관련 알고리즘**: Alpha-Beta, Negamax, MCTS

---

<a id="alpha-beta"></a>
## 2. Alpha-Beta Pruning (알파-베타 가지치기)

**목적**: Minimax 결과를 바꾸지 않으면서 탐색 가지치기

**시간 복잡도**: O(b^(d/2)) 이상적, O(b^d) 최악

**공간 복잡도**: O(b * d)

**특징**:
- α: MAX가 보장받은 최소값
- β: MIN이 보장받은 최대값
- β ≤ α이면 가지치기 (cut-off)
- 자식 순서가 좋으면 효율 극대화

**장점**:
- Minimax와 동일한 결과
- 평균 분기 √b로 감소
- 깊이 2배까지 가능

**단점**:
- 자식 순서 휴리스틱 중요
- 최악은 여전히 O(b^d)

**활용 예시**:
- 체스 엔진 (Stockfish 초기 버전)
- 오목, 바둑 (얕은 탐색)
- 보드게임 일반

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
fun alphaBeta(
    state: GameState,
    depth: Int,
    alpha: Int = Int.MIN_VALUE,
    beta: Int = Int.MAX_VALUE
): Int {
    if (depth == 0 || state.isTerminal()) return state.evaluate()

    var a = alpha
    var b = beta

    if (state.isMaxTurn) {
        var value = Int.MIN_VALUE
        for (child in state.children()) {
            value = maxOf(value, alphaBeta(child, depth - 1, a, b))
            a = maxOf(a, value)
            if (a >= b) break // β cut-off
        }
        return value
    } else {
        var value = Int.MAX_VALUE
        for (child in state.children()) {
            value = minOf(value, alphaBeta(child, depth - 1, a, b))
            b = minOf(b, value)
            if (b <= a) break // α cut-off
        }
        return value
    }
}

// Negamax 변형 (코드 단순화)
fun negamax(state: GameState, depth: Int, alpha: Int, beta: Int, color: Int): Int {
    if (depth == 0 || state.isTerminal()) return color * state.evaluate()

    var a = alpha
    var value = Int.MIN_VALUE
    for (child in state.children()) {
        val v = -negamax(child, depth - 1, -beta, -a, -color)
        if (v > value) value = v
        if (v > a) a = v
        if (a >= beta) break
    }
    return value
}
```

**관련 알고리즘**: Minimax, Negamax, MTD(f)

---

<a id="mcts"></a>
## 3. Monte Carlo Tree Search (MCTS, 몬테카를로 트리 탐색)

**목적**: 무작위 시뮬레이션으로 게임 트리를 통계적으로 탐색

**시간 복잡도**: O(시뮬레이션 수 × 게임 길이)

**공간 복잡도**: O(노드 수)

**특징**:
- 4단계: Selection (UCB1) → Expansion → Simulation (rollout) → Backpropagation
- UCB1 = Q(v) + c * √(ln(N) / n(v))
- 평가 함수 없어도 동작
- 시간 늘릴수록 정확도 향상 (anytime)

**장점**:
- 평가 함수 불필요
- 분기 매우 큰 게임에 강함 (바둑)
- 점진적 개선

**단점**:
- 정확도가 시뮬레이션 횟수에 의존
- 잘못된 휴리스틱이 결과 왜곡

**활용 예시**:
- AlphaGo, AlphaZero (정책망/가치망과 결합)
- 19x19 바둑
- 일반 게임 플레이어 (General Game Playing)
- 의사결정 시뮬레이션

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import kotlin.math.ln
import kotlin.math.sqrt
import kotlin.random.Random

interface MctsState {
    fun isTerminal(): Boolean
    fun legalMoves(): List<MctsState>
    fun result(): Double // 0..1 (현재 플레이어 승률)
    fun randomMove(): MctsState?
}

class MctsNode(val state: MctsState, val parent: MctsNode? = null) {
    val children = mutableListOf<MctsNode>()
    var visits = 0
    var wins = 0.0
    private val untried = state.legalMoves().toMutableList()

    val isFullyExpanded: Boolean get() = untried.isEmpty()

    fun selectChild(c: Double = 1.41): MctsNode {
        return children.maxByOrNull {
            it.wins / it.visits + c * sqrt(ln(visits.toDouble()) / it.visits)
        }!!
    }

    fun expand(): MctsNode {
        val next = untried.removeAt(untried.size - 1)
        val child = MctsNode(next, this)
        children.add(child)
        return child
    }

    fun simulate(): Double {
        var cur = state
        while (!cur.isTerminal()) {
            cur = cur.randomMove() ?: break
        }
        return cur.result()
    }

    fun backprop(result: Double) {
        var n: MctsNode? = this
        var r = result
        while (n != null) {
            n.visits++
            n.wins += r
            r = 1.0 - r // 상대 관점 반전
            n = n.parent
        }
    }
}

fun mctsBestMove(root: MctsNode, iterations: Int): MctsNode? {
    repeat(iterations) {
        var node = root
        // Selection
        while (node.isFullyExpanded && node.children.isNotEmpty()) {
            node = node.selectChild()
        }
        // Expansion
        if (!node.state.isTerminal() && !node.isFullyExpanded) {
            node = node.expand()
        }
        // Simulation
        val result = node.simulate()
        // Backpropagation
        node.backprop(result)
    }
    return root.children.maxByOrNull { it.visits.toDouble() }
}
```

**관련 알고리즘**: Minimax, UCT, AlphaZero

---

<a id="genetic-algorithm"></a>
## 4. Genetic Algorithm (유전 알고리즘)

**목적**: 자연 선택을 모방한 메타휴리스틱 최적화

**시간 복잡도**: O(g * p * f) - g: 세대, p: 인구, f: 평가 비용

**공간 복잡도**: O(p)

**특징**:
- 5단계: Population → Fitness → Selection → Crossover → Mutation
- 선택: 룰렛, 토너먼트
- 교차: one-point, uniform
- 변이: bit flip, swap, gaussian

**장점**:
- 미분 불필요
- 전역 탐색에 강함
- 병렬화 자연스러움

**단점**:
- 수렴 보장 없음
- 파라미터 튜닝 필요
- 평가 함수가 좋아야 함

**활용 예시**:
- 일정 계획, TSP 근사
- 신경망 구조 탐색
- 게임 AI 행동 최적화
- 안테나 형상 설계 (NASA)

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.random.Random

class GeneticAlgorithm(
    private val populationSize: Int,
    private val geneLength: Int,
    private val mutationRate: Double = 0.01,
    private val eliteCount: Int = 2
) {
    private val rng = Random.Default

    fun run(
        fitness: (IntArray) -> Double,
        generations: Int
    ): IntArray {
        var pop = Array(populationSize) { IntArray(geneLength) { rng.nextInt(2) } }

        repeat(generations) {
            val scored = pop.map { it to fitness(it) }.sortedByDescending { it.second }
            val newPop = mutableListOf<IntArray>()

            // Elitism
            for (i in 0 until eliteCount) newPop.add(scored[i].first.copyOf())

            // 새 세대 생성
            while (newPop.size < populationSize) {
                val p1 = tournamentSelect(scored)
                val p2 = tournamentSelect(scored)
                val (c1, c2) = crossover(p1, p2)
                newPop.add(mutate(c1))
                if (newPop.size < populationSize) newPop.add(mutate(c2))
            }
            pop = newPop.toTypedArray()
        }

        return pop.maxByOrNull(fitness)!!
    }

    private fun tournamentSelect(scored: List<Pair<IntArray, Double>>, k: Int = 3): IntArray {
        return (0 until k).map { scored[rng.nextInt(scored.size)] }
            .maxByOrNull { it.second }!!.first
    }

    private fun crossover(a: IntArray, b: IntArray): Pair<IntArray, IntArray> {
        val point = rng.nextInt(geneLength)
        val c1 = a.copyOf(point) + b.copyOfRange(point, geneLength)
        val c2 = b.copyOf(point) + a.copyOfRange(point, geneLength)
        return c1 to c2
    }

    private fun mutate(gene: IntArray): IntArray {
        for (i in gene.indices) {
            if (rng.nextDouble() < mutationRate) gene[i] = 1 - gene[i]
        }
        return gene
    }
}
```

**관련 알고리즘**: Simulated Annealing, PSO, ES

---

<a id="simulated-annealing"></a>
## 5. Simulated Annealing (시뮬레이티드 어닐링)

**목적**: 금속 어닐링을 모방한 확률적 최적화. 초기엔 나쁜 해도 수용, 점차 엄격해짐

**시간 복잡도**: O(반복 횟수 × 평가 비용)

**공간 복잡도**: O(1)

**특징**:
- 온도 T가 점차 감소 (cooling schedule)
- 새 해가 나쁘면 exp(-Δ/T) 확률로 수용
- 지역 최적점 탈출 가능

**장점**:
- 단순한 구현
- 지역 최적 탈출
- 광범위한 문제 적용

**단점**:
- 온도 스케줄 튜닝 필요
- 수렴 느림
- 결정적이지 않음

**활용 예시**:
- TSP 근사
- VLSI 배치
- 일정 계획
- 그래프 분할

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.math.exp
import kotlin.random.Random

fun simulatedAnnealing(
    initial: DoubleArray,
    energy: (DoubleArray) -> Double,
    neighbor: (DoubleArray) -> DoubleArray,
    initialTemp: Double = 1000.0,
    coolingRate: Double = 0.995,
    minTemp: Double = 1e-3
): DoubleArray {
    var current = initial.copyOf()
    var currentEnergy = energy(current)
    var best = current.copyOf()
    var bestEnergy = currentEnergy
    var temp = initialTemp
    val rng = Random.Default

    while (temp > minTemp) {
        val candidate = neighbor(current)
        val candidateEnergy = energy(candidate)
        val delta = candidateEnergy - currentEnergy

        // 좋아졌거나 확률적으로 수용
        if (delta < 0 || rng.nextDouble() < exp(-delta / temp)) {
            current = candidate
            currentEnergy = candidateEnergy
            if (currentEnergy < bestEnergy) {
                best = current.copyOf()
                bestEnergy = currentEnergy
            }
        }

        temp *= coolingRate
    }

    return best
}

// TSP 예시 사용
fun tspNeighbor(tour: IntArray): IntArray {
    val n = tour.size
    val i = Random.nextInt(n)
    var j = Random.nextInt(n)
    while (j == i) j = Random.nextInt(n)
    val copy = tour.copyOf()
    copy[i] = tour[j]
    copy[j] = tour[i]
    return copy
}
```

**관련 알고리즘**: Hill Climbing, Tabu Search, Genetic Algorithm

---
