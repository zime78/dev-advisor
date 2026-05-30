# 계산 복잡도·분석 알고리즘 (Complexity & Analysis)

계산 복잡도 이론, 계산 가능성, 알고리즘 분석 기법 모음입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [complexity-classes](#complexity-classes) | Computational Complexity Classes & NP-completeness | 복잡도 클래스·NP-완전성 | 높음 |
| [computability](#computability) | Computability & Decidability | 계산 가능성·결정 가능성 | 높음 |
| [amortized-analysis](#amortized-analysis) | Amortized Analysis | 분할 상환 분석 | 중간 |
| [master-theorem](#master-theorem) | Master Theorem & Recurrence Solving | 마스터 정리·점화식 해법 | 중간 |
| [approximation-algorithms](#approximation-algorithms) | Approximation Algorithms | 근사 알고리즘 | 높음 |
| [randomized-algorithms](#randomized-algorithms) | Randomized Algorithms (Las Vegas / Monte Carlo) | 무작위 알고리즘 분류 | 중간 |

---

<a id="complexity-classes"></a>
## 1. Computational Complexity Classes & NP-completeness (복잡도 클래스·NP-완전성)

**목적**: 결정 문제를 자원(시간·공간) 소요량으로 분류하고, 다항시간 환원으로 문제 간 난이도 순서를 정의하여 "효율적으로 풀 수 있는가"를 판별하는 이론 틀

**시간 복잡도**: 클래스별 정의 — P = ∪ₖ DTIME(nᵏ), EXPTIME = ∪ₖ DTIME(2^(nᵏ)). 다항시간 환원(many-one) 자체는 O(poly(n))

**공간 복잡도**: PSPACE = ∪ₖ DSPACE(nᵏ). 알려진 포함 관계: P ⊆ NP ⊆ PSPACE ⊆ EXPTIME (P ⊊ EXPTIME 은 시간 위계 정리로 증명됨)

**특징**:
- P: 결정형 튜링 기계로 다항시간에 푸는 결정 문제. NP: 비결정형으로 다항시간, 동치로 다항 크기 인증서(certificate)를 다항시간에 검증 가능한 문제
- NP-hard: NP의 모든 문제를 다항시간 many-one 환원으로 받는 문제(NP 소속은 불요). NP-complete: NP-hard ∩ NP
- Cook–Levin 정리(Cook 1971, Levin 1973): SAT(불리언 충족 가능성)가 최초의 NP-complete 문제임을 증명 — 이후 환원의 출발점
- co-NP: 여집합이 NP인 문제(예: TAUTOLOGY, UNSAT). P = NP 와 NP = co-NP 는 모두 미해결(2026 기준)
- 결정 문제(yes/no)와 탐색 문제(해 자체 구성)는 self-reducibility 로 NP-complete 에서 다항시간 동치

**장점**:
- 무수한 문제의 난이도를 환원으로 한 줄에 정렬 — SAT 가 어려우면 환원받은 문제도 어렵다는 하향 보장
- "다항시간 알고리즘이 존재할 가능성이 낮다"는 객관적 근거 제공 → 휴리스틱/근사/파라미터화로 전환 결정에 유용
- 인증서 검증이라는 통일된 NP 정의로 실무 검증 코드 설계와 직결

**단점**:
- P vs NP 미해결로 "절대 불가능"이 아닌 "현재 알려진 다항해 없음"만 보장 (조건부 하한)
- 점근적·최악 케이스 분류라 평균적으로 잘 풀리는 실무 인스턴스(SAT 솔버 등)와 괴리 가능
- 환원 구성 자체가 비직관적이고 오류가 잦음

**활용 예시**:
- 신규 문제가 NP-hard 임을 SAT/3-SAT/Subset Sum 환원으로 증명해 정확해 대신 근사·ILP·SAT 솔버 선택
- TSP(결정형) · 0/1 Knapsack(결정형) · Graph Coloring 등 NP-complete 판정 후 분기한정/DP-의사다항 적용
- 컴파일러 레지스터 할당(그래프 채색), 스케줄링, 검증(model checking, PSPACE) 난이도 사전 평가

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 다항시간 환원 시연: 3-SAT ≤ₚ Independent Set (Karp 1972)
// 절(clause)마다 리터럴 3개를 삼각형으로, 서로 모순(x 와 ¬x)인 리터럴끼리 간선.
// => m개 절의 식이 충족 가능 ⇔ 정점 m개짜리 독립집합 존재.
data class Lit(val varId: Int, val neg: Boolean)            // neg=true 면 ¬varId

class IndependentSet(val n: Int) {
    val adj = Array(n) { BooleanArray(n) }
    fun edge(a: Int, b: Int) { adj[a][b] = true; adj[b][a] = true }
    // 크기 k 독립집합 존재 여부(검증/탐색용 브루트포스 — NP 검증의 동작 시연)
    fun hasIndependentSet(k: Int): Boolean {
        val pick = IntArray(k)
        fun rec(start: Int, depth: Int): Boolean {
            if (depth == k) return true
            for (v in start until n) {
                if ((0 until depth).all { !adj[pick[it]][v] }) {
                    pick[depth] = v
                    if (rec(v + 1, depth + 1)) return true
                }
            }
            return false
        }
        return rec(0, 0)
    }
}

// clauses[i] = 3개 리터럴. 반환: (그래프, 절 개수 m). m-독립집합 존재 ⇔ 식 충족 가능.
fun reduce3SatToIndependentSet(clauses: List<List<Lit>>): Pair<IndependentSet, Int> {
    val flat = clauses.flatten()                           // 정점 = 모든 리터럴 출현
    val g = IndependentSet(flat.size)
    for (c in clauses.indices)                             // 절 내부 삼각형 간선
        for (i in 0..2) for (j in i + 1..2)
            g.edge(c * 3 + i, c * 3 + j)
    for (a in flat.indices) for (b in a + 1 until flat.size) // 모순 리터럴 간선
        if (flat[a].varId == flat[b].varId && flat[a].neg != flat[b].neg)
            g.edge(a, b)
    return g to clauses.size
}

fun isSatisfiable(clauses: List<List<Lit>>): Boolean {
    val (g, m) = reduce3SatToIndependentSet(clauses)       // 다항시간 환원
    return g.hasIndependentSet(m)                          // 환원된 문제로 판정
}
```

**관련 알고리즘**: 2-SAT, Knapsack, Subset Sum, Hamiltonian

---

<a id="computability"></a>
## 2. Computability & Decidability (계산 가능성·결정 가능성)

**목적**: 어떤 문제가 알고리즘으로 풀 수 있는지(계산 가능), 항상 종료하는 결정 절차가 존재하는지(결정 가능)를 형식적으로 규정하고, 환원으로 결정불가능성을 증명하는 이론적 토대

**시간 복잡도**: 결정 문제는 정의상 종료(전역 함수)를 요구하나 복잡도 상한은 없음 — Halting Problem 등은 어떤 시간 안에도 결정 불가(non-recursive)

**공간 복잡도**: 모델(Turing Machine) 자체는 무한 테이프를 전제 — 유한 입력당 사용량은 가변, 결정 불가능 문제엔 유의미한 상한 없음

**특징**:
- Turing Machine(Turing 1936): 무한 테이프 + 상태 전이로 정의된 보편 계산 모델, λ-계산·일반 재귀 함수와 계산력 동치
- Church-Turing 명제: "효과적으로 계산 가능한 함수 = Turing 계산 가능 함수" — 증명 대상이 아닌 정의/논제(thesis)
- 재귀 집합(decidable, R): 멤버십을 항상 종료해 판정. 재귀 열거 가능(recursively enumerable, RE): 속하는 원소만 인식(yes는 종료, no는 무한 루프 가능)
- Halting Problem: 임의의 (프로그램, 입력)이 정지하는지 판정하는 문제는 결정 불가능(undecidable) — 대각화(diagonalization)로 증명
- Rice 정리(1953): 부분 계산 함수의 "비자명한 의미적 속성"은 모두 결정 불가능 (구문적 속성은 예외)
- 환원(reduction) A ≤ B: A를 B로 변환 가능하면 "B 결정 가능 ⇒ A 결정 가능". 대우로 A가 결정 불가능이면 B도 결정 불가능 — 결정불가능성 전파의 표준 도구

**장점**:
- 풀 수 없는 문제를 헛되이 시도하는 것을 사전에 차단(이론적 불가능성 증명)
- 환원 한 번으로 새 문제의 결정불가능성을 기존 결과로부터 전파 가능
- 정지성 검증·타입 추론·정적 분석의 근본적 한계(불완전성)를 명확히 설명

**단점**:
- 결과가 부정적·구성 불가능(어떤 알고리즘도 존재하지 않음을 말할 뿐 대안을 주지 않음)
- 실무 코드로의 직접 적용보다 한계·불가능성 인식 도구에 가까움
- 점근 비용으로 표현되지 않아 일반 복잡도 분석과 결이 다름

**활용 예시**:
- 정적 분석기·컴파일러: 완벽한 정지성/도달성 판정 불가 ⇒ 보수적 근사(over-approximation)로 우회
- 타입 시스템: 일반 타입 추론(예: System F)·의존 타입의 결정불가능성 인식
- 바이러스 탐지: "이 프로그램이 악성 동작을 하는가"는 Rice 정리상 일반 해 불가 ⇒ 휴리스틱/시그니처 사용
- Hilbert 10번 문제(디오판토스 방정식 정수해 존재)·PCP(Post 대응 문제) 등 결정불가능 문제 식별

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// 1) 보편 계산 모델(Turing Machine) 시뮬레이터 — Church-Turing 명제의 구체화
//    delta: (상태, 읽은 기호) -> (다음 상태, 쓸 기호, 이동 방향 +1/-1)
class TuringMachine(
    private val delta: Map<Pair<String, Char>, Triple<String, Char, Int>>,
    private val accept: String,
    private val reject: String,
    private val blank: Char = '_'
) {
    // 입력을 시뮬레이션. 정지하면 true(accept)/false(reject), 정지하지 않으면 영원히 반환 없음(결정불가능성의 근원)
    fun run(input: String, maxSteps: Int = 100_000): Boolean? {
        val tape = HashMap<Int, Char>()
        input.forEachIndexed { i, c -> tape[i] = c }
        var head = 0; var state = "start"; var steps = 0
        while (state != accept && state != reject) {
            if (steps++ > maxSteps) return null            // 정지 여부를 외부에서 일반 판정할 수 없음
            val sym = tape.getOrDefault(head, blank)
            val (next, write, move) = delta[state to sym] ?: return false
            tape[head] = write; state = next; head += move
        }
        return state == accept
    }
}

// 2) Halting Problem 결정불가능성 — 대각화(귀류법)를 코드로 시연
//    "정지 판정기 halts 가 존재한다"는 가정이 모순을 낳음을 보인다.
fun halts(program: (String) -> Unit, input: String): Boolean =
    throw IllegalStateException("정지 판정기는 존재할 수 없음 (Turing 1936): 아래 paradox 가 모순")

// 만약 halts 가 존재한다면 다음 paradox 를 구성할 수 있다:
//   paradox(p): if (halts(p, p)) loopForever() else return
// 이때 paradox(paradox) 를 평가하면:
//   - 정지한다고 판정 -> loopForever() 로 무한 루프(정지하지 않음)  ── 모순
//   - 정지 안 한다고 판정 -> 즉시 return(정지함)                    ── 모순
// 어느 쪽도 일관될 수 없으므로 halts 는 존재하지 않는다 ⇒ Halting Problem 은 결정 불가능.

// 3) 환원(reduction): Halting ≤ TotalityProblem 스케치
//    "모든 입력에서 정지하는가"(Totality)가 결정 가능하다고 가정하면,
//    임의의 (M, w)에 대해 "입력을 무시하고 M(w)를 흉내내는 기계 M'"를 만들어
//    M'의 Totality 판정 = M(w)의 Halting 판정이 되어 Halting 이 결정 가능해진다(모순).
//    따라서 Totality 도 결정 불가능. (대우: A≤B, A undecidable ⇒ B undecidable)
```

**관련 알고리즘**: 2-SAT, Subset Sum, N-Queens, Sudoku Solver

---

<a id="amortized-analysis"></a>
## 3. Amortized Analysis (분할 상환 분석)

**목적**: 일련의 연산을 묶어 전체 비용을 연산 수로 나눈 평균 비용(worst-case 평균)을 보장함으로써, 가끔 비싼 연산이 섞여도 연산당 비용을 타이트하게 분석하는 기법

**시간 복잡도**: 연산당 amortized 비용 (예: 동적 배열 push_back O(1) amortized, 스플레이 트리 연산 O(log n) amortized) — 단일 연산 worst-case와 구분됨

**공간 복잡도**: O(1) (분석 기법 자체는 추가 공간 불필요, 잠재함수·크레딧은 개념적 장부)

**특징**:
- Aggregate(집계) 방법: n개 연산의 총비용 T(n)을 직접 상한한 뒤 T(n)/n을 amortized 비용으로 정의. 모든 연산에 동일한 평균 비용을 부여
- Accounting(회계/Banker) 방법: 각 연산에 실제 비용과 다른 amortized 요금을 매기고, 차액을 크레딧(credit)으로 자료구조에 저장. 누적 크레딧이 항상 비음수면 amortized 합이 실제 합의 상한이 됨
- Potential(잠재) 방법: 자료구조 상태에 잠재함수 Φ(D)를 정의(Φ(D₀)=0, 항상 Φ≥Φ(D₀)). i번째 amortized 비용 = 실제 비용 cᵢ + Φ(Dᵢ) − Φ(Dᵢ₋₁). 합산 시 망원합(telescoping)으로 Σĉᵢ = Σcᵢ + Φ(Dₙ) − Φ(D₀) ≥ Σcᵢ
- 확률적 평균(average-case)과 다름: 입력 분포 가정 없이 worst-case 연산열에 대해 성립하는 결정론적 보장
- 단일 연산의 worst-case(예: 동적 배열의 재할당은 O(n))는 여전히 클 수 있으며, amortized 보장은 연산열 전체에 한정됨

**장점**:
- 가끔 발생하는 비싼 연산을 다수의 싼 연산에 분산시켜 평균 비용을 타이트하게 증명
- worst-case 단일 연산 상한보다 현실적이고 엄밀한 성능 보장 제공 (입력 분포 가정 불필요)
- 잠재함수 방법은 복잡한 자료구조(스플레이 트리, Fibonacci heap)의 비용을 통일된 틀로 분석

**단점**:
- 실시간(real-time)·저지연 시스템에는 부적합 — 개별 연산의 긴 지연(예: 재할당 stall)을 숨기지 못함
- 적절한 잠재함수 Φ나 크레딧 배정을 찾는 것이 비자명하고 통찰을 요구
- amortized O(1)이라도 단일 연산 worst-case는 클 수 있어, 보장의 의미를 오해하기 쉬움

**활용 예시**:
- 동적 배열(ArrayList/vector) 용량 2배 확장: push n회 총비용 O(n) → push당 O(1) amortized
- 스플레이 트리(Splay tree): 접근 시 회전으로 노드를 루트로 이동, 연산당 O(log n) amortized
- Fibonacci heap: decrease-key O(1) amortized, extract-min O(log n) amortized (Dijkstra·Prim 가속)
- Union-Find(경로 압축+랭크): 연산당 거의 상수 O(α(n)) amortized, 동적 테이블 축소/확장

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// 동적 배열 용량 2배 확장 — push당 O(1) amortized 시연
// Potential 방법: Φ = 2*size - capacity (가득 차면 Φ=size, 확장 직후 Φ=0)
class DynamicArray<T> {
    private var data = arrayOfNulls<Any?>(1)
    private var size = 0
    var totalCopies = 0L       // 누적 실제 복사 횟수(비싼 연산 측정용)
        private set

    val length: Int get() = size

    // amortized O(1): 확장은 가끔 일어나며 복사 비용이 이후 push들에 분산됨
    fun push(value: T) {
        if (size == data.size) grow()   // 가득 차면 용량 2배로 재할당
        data[size++] = value
    }

    @Suppress("UNCHECKED_CAST")
    fun get(i: Int): T {
        require(i in 0 until size) { "index out of bounds: $i" }
        return data[i] as T
    }

    // 비싼 연산: 새 배열에 전체 복사 → 단일 연산 worst-case O(n)
    private fun grow() {
        val newData = arrayOfNulls<Any?>(data.size * 2)
        for (i in 0 until size) {
            newData[i] = data[i]
            totalCopies++
        }
        data = newData
    }
}

fun main() {
    val arr = DynamicArray<Int>()
    val n = 1_000_000
    for (i in 0 until n) arr.push(i)
    // 용량 2배 전략의 총 복사 횟수는 약 2n 미만(기하급수 합) → push당 O(1) amortized
    println("n=$n, totalCopies=${arr.totalCopies}, ratio=${arr.totalCopies.toDouble() / n}")
}
```

**관련 알고리즘**: Treap/Splay, Advanced Heaps (Fibonacci/Pairing), Union-Find, Big-O Notation

---

<a id="master-theorem"></a>
## 4. Master Theorem & Recurrence Solving (마스터 정리·점화식 해법)

**목적**: `T(n) = aT(n/b) + f(n)` 형태의 분할 정복 점화식을 닫힌 형태(closed-form) 점근 복잡도로 푸는 정리와 보조 기법(치환·재귀 트리·Akra-Bazzi) 모음

**시간 복잡도**: 분석 대상 — 마스터 정리 판정 자체는 O(1) (세 경우 비교). 도출 결과는 점화식에 따라 Θ(n^log_b a), Θ(n^log_b a · log n) 등

**공간 복잡도**: 분석 기법 — 재귀 트리 전개 시 트리 높이 O(log_b n)

**특징**:
- 표준형 `T(n) = aT(n/b) + f(n)` (a ≥ 1, b > 1)에서 임계 지수(critical exponent) `c_crit = log_b a`와 f(n)의 다항 차수를 비교해 세 경우로 분류
- Case 1 (재귀가 지배): `f(n) = O(n^(c_crit − ε))`, ε > 0 → `T(n) = Θ(n^(log_b a))`
- Case 2 (균형): `f(n) = Θ(n^c_crit · log^k n)`, k ≥ 0 → `T(n) = Θ(n^(log_b a) · log^(k+1) n)`
- Case 3 (합치기가 지배): `f(n) = Ω(n^(c_crit + ε))` 이고 정칙성 조건(regularity) `a·f(n/b) ≤ c·f(n)` (어떤 c < 1) 성립 → `T(n) = Θ(f(n))`
- 치환법(substitution): 답을 추측 후 수학적 귀납법으로 증명 / 재귀 트리(recursion-tree): 각 레벨 비용 합산으로 직관적 추정 / Akra-Bazzi: 부분 문제 크기가 불균등하거나 마스터 정리 적용 불가 시 일반화된 적분 공식으로 해결

**장점**:
- 분할 정복 알고리즘의 복잡도를 암기·기계적 판정으로 빠르게 도출
- 재귀 트리는 마스터 정리가 안 되는 점화식의 답을 추측하는 직관 제공
- Akra-Bazzi는 비대칭 분할(예: `T(n)=T(n/3)+T(2n/3)+n`)까지 포괄

**단점**:
- 마스터 정리는 Case 사이의 "간극"(예: `f(n)=Θ(n^c_crit / log n)`처럼 다항적 차이가 아닌 경우)에는 적용 불가
- Case 3은 정칙성 조건을 별도로 검증해야 하며 누락 시 오답
- 비정수 분할·감산형 점화식(`T(n)=T(n−1)+f(n)`)에는 부적합 — 치환/재귀 트리 또는 다른 정리 필요

**활용 예시**:
- Merge Sort `T(n)=2T(n/2)+Θ(n)` → Case 2 (k=0) → Θ(n log n)
- Binary Search `T(n)=T(n/2)+Θ(1)` → Case 2 (k=0) → Θ(log n)
- Karatsuba `T(n)=3T(n/2)+Θ(n)` → log₂3 ≈ 1.585 > 1 → Case 1 → Θ(n^1.585)
- Strassen `T(n)=7T(n/2)+Θ(n²)` → log₂7 ≈ 2.807 > 2 → Case 1 → Θ(n^2.807)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import kotlin.math.ln
import kotlin.math.abs

// 표준형 T(n) = a·T(n/b) + f(n), 여기서 f(n) = Θ(n^fExp · log^logK n)
data class Recurrence(val a: Int, val b: Int, val fExp: Double, val logK: Int = 0)

// 마스터 정리 세 경우를 판정해 점근 복잡도 문자열을 반환
fun masterTheorem(r: Recurrence): String {
    require(r.a >= 1 && r.b > 1) { "표준형 조건 위반: a≥1, b>1" }
    val cCrit = ln(r.a.toDouble()) / ln(r.b.toDouble())  // c_crit = log_b a
    val eps = 1e-9
    return when {
        // Case 1: f(n) = O(n^(c_crit − ε)) → 재귀가 지배
        r.fExp < cCrit - eps ->
            "Theta(n^${"%.3f".format(cCrit)})  [Case 1]"
        // Case 2: f(n) = Theta(n^c_crit · log^k n) → 균형, log 한 단계 추가
        abs(r.fExp - cCrit) <= eps ->
            "Theta(n^${"%.3f".format(cCrit)} * log^${r.logK + 1} n)  [Case 2]"
        // Case 3: f(n) = Omega(n^(c_crit + ε)) → 정칙성 조건 가정 시 합치기가 지배
        else ->
            "Theta(n^${"%.3f".format(r.fExp)}" +
                (if (r.logK > 0) " * log^${r.logK} n" else "") + ")  [Case 3, 정칙성 가정]"
    }
}

fun main() {
    println(masterTheorem(Recurrence(a = 2, b = 2, fExp = 1.0)))  // Merge Sort → Case 2
    println(masterTheorem(Recurrence(a = 1, b = 2, fExp = 0.0)))  // Binary Search → Case 2
    println(masterTheorem(Recurrence(a = 3, b = 2, fExp = 1.0)))  // Karatsuba → Case 1
    println(masterTheorem(Recurrence(a = 7, b = 2, fExp = 2.0)))  // Strassen → Case 1
}
```

**관련 알고리즘**: Merge Sort (병합 정렬), Strassen's Matrix Multiplication (스트라센 행렬 곱셈), Karatsuba Multiplication (카라츠바 곱셈), DP Optimizations (DP 최적화 기법)

---

<a id="approximation-algorithms"></a>
## 5. Approximation Algorithms (근사 알고리즘)

**목적**: NP-hard 최적화 문제를 다항 시간에 풀되, 최적해 대비 보장된 비율(approximation ratio) 안의 근사해를 반환

**시간 복잡도**: 알고리즘별 상이 — 대부분 다항 시간 (예: Vertex Cover 2-approx O(V + E), Set Cover greedy O(요소·집합 곱에 비례))

**공간 복잡도**: 알고리즘별 상이 — 일반적으로 O(입력 크기)

**특징**:
- approximation ratio c: 모든 입력에서 (근사해 비용) ≤ c·OPT (최소화) 또는 ≥ c·OPT (최대화) 를 보장하는 c-approximation
- PTAS(Polynomial-Time Approximation Scheme): 임의의 ε>0 에 대해 (1+ε)-근사를, n 다항이지만 ε 에 대해서는 임의 의존(예: O(n^(1/ε)))으로 제공
- FPTAS(Fully PTAS): 실행 시간이 n 과 1/ε 모두에 대해 다항 (예: Knapsack 의 동적계획 기반 FPTAS)
- 대표 결과: metric TSP 의 Christofides 알고리즘(1976)은 1.5-approx, Set Cover 의 greedy 는 (ln n + 1)-approx (조화수 H_n 상계)
- inapproximability: P≠NP 가정 하에서, 일반(비-metric) TSP 는 임의 상수 비율로도 근사 불가, Set Cover 는 (1-o(1))·ln n 보다 잘 근사 불가(Dinur–Steurer 2014), MAX-3SAT 는 PCP 정리로 7/8 초과 근사 불가

**장점**:
- NP-hard 문제에서 최적해를 포기하는 대신 품질의 수학적 하한/상한을 보장
- 휴리스틱과 달리 최악의 경우 성능이 증명되어 있어 신뢰 가능
- 다항 시간으로 대규모 입력에도 실용적

**단점**:
- 보장 비율은 최악 경우 기준이라 실제 평균보다 비관적일 수 있음
- 문제마다 알고리즘·증명 기법이 달라 일반화된 레시피가 없음
- inapproximability 한계로 인해 특정 문제는 좋은 비율 자체가 불가능

**활용 예시**:
- 시설 배치·센서 배치 등 Set Cover/Vertex Cover 류 자원 최소화
- 물류 경로(metric TSP) 의 Christofides 기반 근사 투어
- Knapsack 의 FPTAS 로 예산·자원 할당 근사 최적화
- 클러스터링(k-center) 의 2-approx greedy

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 1) Vertex Cover 2-approx: 임의의 미커버 간선 (u,v) 의 양 끝점을 모두 채택.
//    채택된 정점 집합은 OPT 의 2배 이하임이 보장됨 (간선 disjoint matching 하계 논증).
fun vertexCover2Approx(n: Int, edges: List<Pair<Int, Int>>): Set<Int> {
    val cover = HashSet<Int>()
    for ((u, v) in edges) {
        if (u !in cover && v !in cover) {  // 아직 커버되지 않은 간선
            cover.add(u); cover.add(v)     // 양 끝점 동시 채택 → 비율 2 보장
        }
    }
    return cover
}

// 2) Set Cover greedy (ln n)-approx: 매 단계 미커버 원소를 가장 많이 덮는 집합을 선택.
//    반환 집합 수 ≤ H_n · OPT (H_n = 1 + 1/2 + ... + 1/n ≈ ln n).
fun setCoverGreedy(universe: Set<Int>, sets: List<Set<Int>>): List<Int> {
    val uncovered = HashSet(universe)
    val chosen = mutableListOf<Int>()
    while (uncovered.isNotEmpty()) {
        // 미커버 원소를 최대로 덮는 집합 인덱스 선택
        var bestIdx = -1; var bestGain = 0
        for (i in sets.indices) {
            val gain = sets[i].count { it in uncovered }
            if (gain > bestGain) { bestGain = gain; bestIdx = i }
        }
        if (bestIdx == -1) break          // 더 덮을 수 없음 (불완전 커버 입력 방어)
        chosen.add(bestIdx)
        uncovered.removeAll(sets[bestIdx])
    }
    return chosen
}
```

**관련 알고리즘**: Knapsack, Hamiltonian Cycle, Hungarian, Fractional Knapsack

---

<a id="randomized-algorithms"></a>
## 6. Randomized Algorithms (Las Vegas / Monte Carlo) (무작위 알고리즘 분류)

**목적**: 난수를 알고리즘 내부 결정에 사용해 평균 성능을 끌어올리거나 결정론적으로 어려운 문제를 확률적으로 해결하는 기법 분류

**시간 복잡도**: 알고리즘마다 다름 — 기댓값(expected) 기준 (예: random-pivot Quicksort O(n log n) 기댓값, Miller-Rabin O(k log³ n))

**공간 복잡도**: 알고리즘마다 다름 (예: Miller-Rabin O(1), random-pivot Quicksort O(log n) 기댓값 스택)

**특징**:
- Las Vegas: 결과는 항상 정확, 실행 시간만 난수에 의존(기댓값 시간). 예: random-pivot Quicksort, Randomized Quickselect
- Monte Carlo: 실행 시간은 고정(또는 한계 보장)되지만 결과가 일정 확률로 틀릴 수 있음. 예: Miller-Rabin, Karger min-cut
- one-sided error: 한쪽 답만 틀림 — Miller-Rabin은 "합성수"를 "소수(probably prime)"로 잘못 볼 수 있으나 "소수"를 "합성수"로 보지는 않음 (RP 클래스 형태)
- two-sided error: 양쪽 답 모두 틀릴 수 있음 (BPP 클래스). 독립 반복으로 오류 확률을 지수적으로 감소
- 복잡도 클래스: RP(one-sided, 다항시간), BPP(two-sided, 오류 < 1/3), ZPP(Las Vegas, 기댓값 다항시간). ZPP = RP ∩ co-RP 가 성립

**장점**:
- 결정론적 최악 케이스 입력(adversarial input)을 난수로 회피 — random-pivot이 정렬된 배열의 O(n²) 함정을 피함
- Miller-Rabin처럼 결정론 알고리즘보다 훨씬 빠르고 단순한 구현 가능
- 반복 시행으로 Monte Carlo 오류 확률을 원하는 만큼 낮출 수 있음 (k회 반복 → 오류 ≤ 2⁻ᵏ 수준)

**단점**:
- Monte Carlo는 결과가 확률적으로 틀릴 수 있어 정확성 검증이 필요한 영역에선 부적합할 수 있음
- 좋은 난수원(PRNG/CSPRNG) 품질에 성능·안전성이 의존
- 동일 입력에 비결정적 동작 → 디버깅·재현이 어려움 (시드 고정으로 완화)

**활용 예시**:
- 정렬/선택: random-pivot Quicksort, Randomized Quickselect (최악 케이스 회피)
- 암호·정수론: Miller-Rabin 소수 판정으로 RSA 키 생성 시 대형 소수 탐색
- 그래프: Karger min-cut (간선 contraction 반복으로 최소 컷을 확률적으로 탐색)
- 해싱/추정: universal hashing, Bloom filter, HyperLogLog 같은 확률적 자료구조

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import kotlin.random.Random

// Las Vegas: random-pivot Quicksort — 결과는 항상 정확, 시간만 난수 의존
fun lasVegasQuicksort(a: IntArray, lo: Int = 0, hi: Int = a.size - 1) {
    if (lo >= hi) return
    val p = Random.nextInt(lo, hi + 1)          // 무작위 피벗 선택
    a[p] = a[hi].also { a[hi] = a[p] }          // 피벗을 끝으로 이동
    val pivot = a[hi]
    var i = lo
    for (j in lo until hi) {
        if (a[j] < pivot) { a[i] = a[j].also { a[j] = a[i] }; i++ }
    }
    a[i] = a[hi].also { a[hi] = a[i] }
    lasVegasQuicksort(a, lo, i - 1)
    lasVegasQuicksort(a, i + 1, hi)
}

// Monte Carlo: Miller-Rabin 소수 판정 — one-sided error (합성수를 소수로 오판 가능)
fun isProbablyPrime(n: Long, k: Int = 20): Boolean {
    if (n < 2) return false
    for (p in longArrayOf(2, 3, 5, 7, 11, 13)) {
        if (n == p) return true
        if (n % p == 0L) return false
    }
    var d = n - 1; var r = 0
    while (d % 2 == 0L) { d /= 2; r++ }         // n-1 = d * 2^r
    repeat(k) {                                  // k회 반복 → 오류 확률 ≤ 4^-k
        val aRand = Random.nextLong(2, n - 1)
        var x = modPow(aRand, d, n)
        if (x == 1L || x == n - 1) return@repeat // 이 증인 통과 → 다음 시행
        var composite = true
        run repeatInner@{
            repeat(r - 1) {
                x = mulMod(x, x, n)
                if (x == n - 1) { composite = false; return@repeatInner }
            }
        }
        if (composite) return false              // 확실한 합성수
    }
    return true                                  // probably prime
}

private fun mulMod(a: Long, b: Long, m: Long): Long {
    return (a.toBigInteger() * b.toBigInteger() % m.toBigInteger()).toLong()
}

private fun modPow(base: Long, exp: Long, m: Long): Long {
    var result = 1L; var b = base % m; var e = exp
    while (e > 0) {
        if (e and 1L == 1L) result = mulMod(result, b, m)
        b = mulMod(b, b, m); e = e shr 1
    }
    return result
}
```

**관련 알고리즘**: Quick Sort, Miller-Rabin Primality Test, Quickselect, Min Cut — Stoer-Wagner
