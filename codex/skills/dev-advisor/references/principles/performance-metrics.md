# 성능 메트릭·측정 (Performance Metrics & Measurement)

10 성능 측정 표준. Latency 수치 / 복잡도 메트릭 / Profiling / Tail latency / Apdex.

**원전·표준 참고**:
- Jeff Dean — "Numbers Every Programmer Should Know" (Stanford talk, 2010)
- Thomas McCabe — *A Complexity Measure* (IEEE TSE, 1976)
- Maurice Halstead — *Elements of Software Science* (1977)
- Brendan Gregg — *Systems Performance: Enterprise and the Cloud*, 2nd ed. (2020)
- Brendan Gregg — Flame Graph methodology
- Jeff Dean, Luiz Barroso — *The Tail at Scale* (CACM 2013)
- Peter Sevcik — Apdex (Application Performance Index Alliance)
- SonarSource — Cognitive Complexity whitepaper (2018)

**Latency Numbers (2020 수치, ns → 인간 시간 환산)**:

| 작업 | 시간 | 인간 환산 (×10⁹) |
|------|------|----------------|
| L1 cache reference | 0.5 ns | 0.5 초 |
| Branch mispredict | 5 ns | 5 초 |
| L2 cache reference | 7 ns | 7 초 |
| Mutex lock/unlock | 25 ns | 25 초 |
| Main memory reference | 100 ns | 1.7 분 |
| Send 1KB over 1Gbps | 10 μs | 2.7 시간 |
| Read 1MB sequentially from SSD | 250 μs | 2.9 일 |
| Round trip in datacenter | 500 μs | 5.8 일 |
| Read 1MB sequentially from disk | 30 ms | 1 년 |
| Coast-to-coast roundtrip | 150 ms | 4.8 년 |

**관련 카탈로그**:
- [iso25010.md](iso25010.md) — Performance Efficiency 품질 특성
- [code-smells.md](code-smells.md) — Comments, Long Method (간접)
- [`../patterns/observability.md`](../patterns/observability.md) — USE/RED/Golden Signals 본체
- [`../patterns/testing-strategies.md`](../patterns/testing-strategies.md) — Load / Stress / Spike

---

<a id="latency-numbers"></a>
## 1. Latency Numbers Every Programmer Should Know

**정의**: Jeff Dean (Google) 이 2010 Stanford talk 에서 정리한 *컴퓨터 시스템의 기본 latency 상수 표*. L1 cache 0.5 ns 부터 Coast-to-coast 150 ms 까지 7~9 자릿수의 격차를 인지하게 한다. Peter Norvig 가 1998 *Teach Yourself Programming in Ten Years* 에서 처음 표 형태로 정리하고, Jeff Dean 이 갱신·전파.

**핵심 통찰**: **단위 차이가 의사결정을 바꾼다**. L1 (0.5 ns) ↔ Main memory (100 ns) = 200 배, Memory (100 ns) ↔ SSD (250 μs) = 2,500 배, SSD ↔ Disk (30 ms) = 120 배, Datacenter RTT (500 μs) ↔ Coast-to-coast (150 ms) = 300 배. **Memory hierarchy 한 단계 내려갈 때마다 2~3 자릿수 페널티**.

**원전 수치 (2020 기준)**: 표 본문 위 헤더 표 참조. CPU clock 은 ns 단위이고 disk·network 는 μs/ms 단위라는 *자릿수 직관* 이 핵심.

**측정 도구**: `perf stat`, `lmbench`, `sysbench`, Intel `MLC` (Memory Latency Checker), `iperf3` (network), `fio` (disk)

**장점**:
- 후보 설계의 *상한 성능* 을 종이 위에서 즉시 추산 가능 (back-of-envelope 계산)
- DB call vs in-memory cache vs CDN 선택 시 *어림셈으로 비교*
- 신입 엔지니어 멘토링의 표준 도구

**한계**:
- 2010 표는 modern hardware 와 다름 — DDR5, NVMe Gen5, 100 Gbps 네트워크 등 발전
- 클라우드 환경의 추가 hop (LB, sidecar, mesh) 미반영
- 분산 시스템의 *tail latency* 까지는 못 잡음 (→ [Latency Percentile](#latency-percentile) 참조)

**실무 적용**:
- 새 기능 설계 회의에서 "DB call 3 회 = 약 3 ms × 3 = 9 ms" 같은 napkin math
- 캐시 도입 ROI 추산: L2 cache hit (~7 ns) vs DB query (~수 ms) → 100,000× 차이
- 분산 트랜잭션 vs 단일 노드 처리 비교 시 RTT 비용 산입

```kotlin
// Latency Numbers 활용 — 캐시 도입 결정의 napkin math
// 시나리오: 사용자 프로필 조회 — 호출 빈도 1,000 RPS, p99 응답 목표 50 ms
//
// Without cache:
//   DB query (datacenter RTT + query exec) ≈ 5 ms × 1,000 RPS
//   DB CPU 사용량 ≈ 100%, p99 latency ≈ 30~80 ms (불안정)
//
// With Redis cache (in-DC):
//   Cache hit  : RTT 500 μs + Redis exec 100 μs ≈ 0.6 ms  (cache hit 95%)
//   Cache miss : 5 ms (DB) + 0.6 ms (set)       ≈ 5.6 ms  (5%)
//   가중평균   : 0.95 × 0.6 + 0.05 × 5.6 ≈ 0.85 ms
//   → DB 부하 95% 감소, p99 ≈ 5~10 ms (안정)
//
// With in-process LRU cache:
//   L2 cache reference ≈ 7 ns + map lookup ≈ ~100 ns ≈ 0.0001 ms
//   → Redis 대비 다시 8,500× 빠름, 단 멀티 인스턴스 invalidation 비용 발생
//
// 결론: 캐시 hit rate 가 90%+ 보장되고 stale tolerance 가 있으면 Redis,
//       데이터가 instance-local 이고 mutation 이 드물면 in-process.
fun getUser(id: String): User =
    inMemoryCache.getIfPresent(id)             // ~100 ns
        ?: redis.get("user:$id")?.also { ... } // ~600 μs
        ?: db.findUser(id).also { ... }        // ~5 ms
```

**관련 항목**: [iso-performance-efficiency](iso25010.md#2-performance-efficiency), [Big-O Notation](#big-o-practical), [Latency Percentile](#latency-percentile), [Profiling 기법](#profiling-techniques)

---

<a id="big-o-practical"></a>
## 2. Big-O Notation 실용편

**정의**: 알고리즘 자원 사용량의 *점근적 상한* 을 표현하는 표기법 (Bachmann–Landau, 1894). `f(n) = O(g(n))` 은 충분히 큰 n 에 대해 `|f(n)| ≤ c·|g(n)|` 인 상수 c 가 존재함을 의미. 실무에서는 **시간 복잡도 / 공간 복잡도 모두**에 적용.

**핵심 통찰**: **n 의 절대값이 클 때만 차이가 의미 있다**. n = 10 에서는 O(n²) 도 100, O(n log n) 도 33 — 무관. n = 10⁶ 에서는 O(n²) = 10¹² (수 시간), O(n log n) = 2×10⁷ (수십 ms). **데이터 크기가 다음 자릿수로 갈 때마다 알고리즘이 살아남는지 재검토**.

**대표 클래스 비교 (n = 10⁶ 기준, 1 ns/op 가정)**:

| 복잡도 | 명칭 | n=10⁶ 시 연산 수 | 시간 (1 ns/op) | 예시 |
|--------|------|---------------:|--------------:|------|
| O(1) | 상수 | 1 | 1 ns | HashMap lookup, array index |
| O(log n) | 로그 | 20 | 20 ns | Binary search, B-tree lookup |
| O(√n) | 제곱근 | 1,000 | 1 μs | 소수 판정 |
| O(n) | 선형 | 10⁶ | 1 ms | 배열 scan |
| O(n log n) | 선형로그 | 2×10⁷ | 20 ms | Merge sort, Quick sort 평균 |
| O(n²) | 이차 | 10¹² | 16.6 분 | Bubble sort, naive nested loop |
| O(n³) | 삼차 | 10¹⁸ | 31 년 | Floyd-Warshall, 행렬 곱 (naive) |
| O(2ⁿ) | 지수 | 10³⁰¹⁰³⁰ | 우주 나이 초과 | 부분집합 brute-force |
| O(n!) | 계승 | 10⁵⁵⁶⁵⁷⁰⁰ | 우주 나이 초과 | 외판원 brute-force |

**측정 도구**: 단위 테스트의 input 크기 ramp (n=10², 10³, 10⁴, 10⁵, 10⁶ 별 측정), `benchmark.js`, `JMH` (Java Microbenchmark Harness), `pytest-benchmark`

**장점**:
- 입력 크기 증가 시 *어디서 무너질지* 사전 예측
- 코드 리뷰에서 즉시 의사결정 가능 ("이 nested loop 은 n² — 입력 max 100K 이면 위험")
- 알고리즘 교체의 효과 추정 (sort 알고리즘 교체, hash 도입)

**한계**:
- **상수 무시** — `100·n` 과 `n` 이 같은 O(n). 작은 n 에서는 상수 차가 결정적
- **lower-order term 무시** — `n² + 1000·n` 도 O(n²) — n 작을 때는 `1000n` 이 지배
- 실측 cache behavior, branch prediction, memory bandwidth 미반영
- 최선/평균/최악 구분 필요 — quicksort 평균 O(n log n), 최악 O(n²)

**실무 적용**:
- API 응답 시간 SLA 가 100 ms 이고 n=10⁶ 데이터를 처리하면 → O(n log n) 이상 금지
- 신규 자료구조 도입 시 측정 단위 테스트로 *경험적 O 곡선* 확인
- LeetCode / 코딩 인터뷰의 "최적해" 기준 — naive O(n²) → O(n log n) 또는 O(n)

```kotlin
// Big-O 실용 비교 — 중복 검사 3 방식
// n = 데이터 크기, 측정은 JMH 또는 단위 테스트의 ramp 로

// (1) O(n²) — naive nested loop, n=10⁶ 에서 사실상 불가
fun hasDuplicateNaive(arr: IntArray): Boolean {
    for (i in arr.indices) {
        for (j in i + 1 until arr.size) {
            if (arr[i] == arr[j]) return true       // n × (n-1) / 2 비교
        }
    }
    return false
}

// (2) O(n log n) — sort 후 인접 비교, n=10⁶ 에서 ~수십 ms
fun hasDuplicateSorted(arr: IntArray): Boolean {
    val sorted = arr.sortedArray()                  // O(n log n)
    return (1 until sorted.size).any { sorted[it] == sorted[it - 1] }
}

// (3) O(n) 평균 — HashSet, n=10⁶ 에서 ~수 ms
fun hasDuplicateHash(arr: IntArray): Boolean {
    val seen = HashSet<Int>(arr.size)               // hash 충돌 무시하면 O(n)
    return arr.any { !seen.add(it) }                // add 가 false 이면 중복
}

// 의사결정:
//   n ≤ 1,000     : (1) 가장 단순 — premature optimization 회피
//   n ≤ 100,000   : (2) 메모리 추가 비용 없음
//   n ≥ 1,000,000 : (3) 시간 우선, 메모리 비용 감수
```

**관련 항목**: [iso-performance-efficiency](iso25010.md#2-performance-efficiency), [Latency Numbers](#latency-numbers), [Cyclomatic Complexity](#cyclomatic-complexity)

---

<a id="cyclomatic-complexity"></a>
## 3. Cyclomatic Complexity (V(G))

**정의**: Thomas McCabe 가 *A Complexity Measure* (IEEE TSE, 1976) 에서 정의한 **메서드의 독립 실행 경로 수**. control flow graph (CFG) 의 edge - node + 2, 또는 *분기 수 + 1* 로 계산. V(G) 가 클수록 테스트 케이스 수도 비례.

**핵심 수식**:
```
V(G) = E - N + 2P
       (E = edge 수, N = node 수, P = connected component 수)
또는
V(G) = (분기 결정점 수: if, for, while, case, catch, &&, ||) + 1
```

**McCabe 권장 임계값**:

| V(G) | 위험도 | 권장 조치 |
|------|--------|----------|
| 1~4 | 단순 | OK |
| 5~7 | 양호 | 모니터링 |
| 8~10 | **상한선** | 리팩토링 검토 |
| 11~20 | 복잡 | 분할 필수 |
| 20+ | 매우 위험 | 즉시 분할, 테스트 어려움 |

**측정 도구**: SonarQube, PMD, Checkstyle, `radon` (Python), `gocyclo` (Go), `lizard` (다국어), `eslint-complexity` (JS)

**장점**:
- **최소 단위 테스트 케이스 수** 의 lower bound (V(G) 개의 독립 경로 모두 cover 필요)
- IDE / CI 에서 자동 측정 — 객관 임계값으로 게이트 가능
- 50 년간 검증된 산업 표준 (NIST, NASA, DO-178C 항공 표준에 채택)

**한계**:
- **선형 구조 코드 만 측정** — 디스패치 / 다형성 / 콜백 깊이 미반영
- 한 거대한 switch 문도, 잘 분리된 strategy pattern 도 동일 V(G) 측정 가능 → [Cognitive Complexity](#cognitive-complexity) 보완
- 단일 메서드 내부 만 — 클래스 / 모듈 수준 응집도 측정 불가

**실무 적용**:
- CI 에서 V(G) > 10 메서드 PR 차단
- 레거시 코드 우선순위 — 결함률과 V(G) 상관관계 0.7~0.9 (논문 실증)
- 리팩토링 후 V(G) 감소 측정 — Extract Function 효과 정량화

```kotlin
// Cyclomatic Complexity 측정 예시
//
// (1) V(G) = 1 — 분기 없음, 단일 경로
fun greet(name: String): String = "Hello, $name"

// (2) V(G) = 4 — if 2 + && 1 + 기본 1
fun classifyAge(age: Int): String {
    return if (age < 0) "invalid"                   // 분기 1
    else if (age < 18 && age >= 0) "minor"          // 분기 2 + && 분기 3
    else "adult"
}

// (3) V(G) = 11 — 임계값 초과, 리팩토링 대상
fun calculateDiscount(order: Order): Double {
    var d = 0.0
    if (order.isVip) d += 0.1                       // +1
    if (order.amount > 100_000) d += 0.05           // +1
    if (order.itemCount >= 10) d += 0.05            // +1
    if (order.coupon != null) d += order.coupon.rate // +1
    if (order.season == "summer") d += 0.03         // +1
    when (order.region) {                            // +case 수
        "KR" -> d += 0.02                           // +1
        "JP" -> d += 0.03                           // +1
        "US" -> d += 0.01                           // +1
        "EU" -> d += 0.025                          // +1
    }
    if (d > 0.3) d = 0.3                            // +1
    return d                                        // base +1 = 11
}

// 리팩토링: Strategy / Rule pipeline 으로 분할 (각 V(G) ≤ 3)
data class DiscountRule(val name: String, val apply: (Order) -> Double)
val rules = listOf(
    DiscountRule("vip")     { if (it.isVip) 0.1 else 0.0 },
    DiscountRule("amount")  { if (it.amount > 100_000) 0.05 else 0.0 },
    // ...
)
fun calculateDiscount2(order: Order): Double =
    rules.sumOf { it.apply(order) }.coerceAtMost(0.3)
```

**관련 항목**: [code-smell-long-method](code-smells.md#1-long-method), [Cognitive Complexity](#cognitive-complexity), [iso-maintainability](iso25010.md#maintainability)

---

<a id="cognitive-complexity"></a>
## 4. Cognitive Complexity

**정의**: SonarSource 가 2018 년 G. Ann Campbell 의 whitepaper *Cognitive Complexity: A new way of measuring understandability* 에서 정의. **코드를 읽고 이해하는 데 드는 인간의 인지 부담** 을 측정. Cyclomatic 의 *기계 경로* 가 아닌 *인간 가독성* 에 초점.

**핵심 통찰**: **중첩 (nesting) 이 cognitive 부담의 핵심 요인**. 같은 분기 수라도 평면 if-else 보다 중첩 if-else 가 훨씬 어렵게 읽힘. Cyclomatic 은 동일하게 계산하지만 Cognitive 는 중첩 깊이에 가중치 부여.

**계산 규칙 (요약)**:

| 항목 | 가산 |
|------|-----|
| Break in linear flow (`if`, `else`, `switch`, `for`, `while`, `catch`, `goto`, ternary) | +1 |
| Nesting increment (each level 가산) | +1 (per nesting level) |
| `else if`, `else` (linear flow break 만 — nesting 없음) | +1 |
| Boolean composition (`&&`, `||` 시퀀스 첫 발생) | +1 (시퀀스 당) |
| Recursion | +1 |

**Cyclomatic vs Cognitive 비교 예시**:

| 코드 패턴 | Cyclomatic | Cognitive |
|-----------|----------:|---------:|
| 단순 `if` × 5 (평면) | 6 | 5 |
| `if` 중첩 5 level | 6 | 1+2+3+4+5 = 15 |
| `switch` 10 case (평면) | 11 | 1 (`switch` 만) |
| `&&` 5 개 시퀀스 | 6 | 1 |

**측정 도구**: SonarQube (cognitive_complexity rule), SonarCloud, IntelliJ IDEA inspection, `eslint-plugin-sonarjs`, Code Climate

**장점**:
- 인간 가독성 직접 측정 — code review 시 *진짜 어려운 코드* 식별
- 큰 switch (평면) 와 깊은 nested if (계층) 를 차별 평가 — Cyclomatic 의 약점 보완
- 권장 임계값 **메서드당 15 이하** (SonarSource 기본)

**한계**:
- 비교적 신생 메트릭 (2018) — Cyclomatic 만큼 산업 채택 부족
- 도구별 계산 세부 차이 있음 — 같은 코드에 다른 값
- 함수형 / 선언적 코드 (Stream API, RxJava 체이닝) 측정 부정확

**실무 적용**:
- SonarQube 기본 임계값 15 — 초과 시 리뷰 강제
- 신규 / 복잡 알고리즘은 Cognitive 우선 (Cyclomatic 보다 인간 친화적)
- 리팩토링 KPI: Cognitive 50% 감소 등 명시적 목표

```kotlin
// Cognitive Complexity 비교
//
// (a) Cyclomatic 6, Cognitive 15 — 5-level nested
fun validateBad(order: Order): String? {
    if (order.items.isNotEmpty()) {              // +1, nest=1
        if (order.customer != null) {            // +1+1=+2, nest=2
            if (order.customer.age >= 18) {      // +1+2=+3, nest=3
                if (order.payment != null) {     // +1+3=+4, nest=4
                    if (order.payment.isValid) { // +1+4=+5, nest=5
                        return null              // OK
                    }
                }
            }
        }
    }
    return "invalid"                              // 총 15
}

// (b) Cyclomatic 6, Cognitive 5 — guard clause 평탄화
fun validateGood(order: Order): String? {
    if (order.items.isEmpty()) return "empty"        // +1
    if (order.customer == null) return "no customer" // +1
    if (order.customer.age < 18) return "minor"      // +1
    if (order.payment == null) return "no payment"   // +1
    if (!order.payment.isValid) return "invalid"     // +1
    return null                                       // 총 5
}
// 같은 Cyclomatic, 3× cognitive 차이 — Cognitive 가 *진짜 가독성* 차이를 포착
```

**관련 항목**: [Cyclomatic Complexity](#cyclomatic-complexity), [code-smell-long-method](code-smells.md#1-long-method), [iso-usability](iso25010.md#usability) (간접, 개발자 사용성)

---

<a id="halstead-metrics"></a>
## 5. Halstead Metrics

**정의**: Maurice Halstead 가 *Elements of Software Science* (1977) 에서 정의한 *소프트웨어 과학* 의 최초 정량 메트릭. 코드를 **operator (연산자) 와 operand (피연산자)** 의 어휘로 보고 vocabulary, length, volume, difficulty, effort 를 계산.

**핵심 수식 (4 기본 카운트)**:
```
n₁ = 고유 연산자 수 (distinct operators)
n₂ = 고유 피연산자 수 (distinct operands)
N₁ = 총 연산자 출현 수
N₂ = 총 피연산자 출현 수
```

**파생 메트릭**:

| 메트릭 | 수식 | 의미 |
|--------|------|------|
| Vocabulary | n = n₁ + n₂ | 코드의 어휘 크기 |
| Length | N = N₁ + N₂ | 코드의 토큰 수 |
| Volume | V = N · log₂(n) | 정보 이론적 코드 크기 (bits) |
| Difficulty | D = (n₁/2) · (N₂/n₂) | 코드 이해 / 작성 난이도 |
| Effort | E = D · V | 작성에 필요한 정신적 노력 (elementary mental discriminations) |
| Time | T = E / 18 | 추정 작성 시간 (초, 18 = Stroud 상수) |
| Bugs | B = V / 3000 또는 E^(2/3) / 3000 | 추정 결함 수 |

**측정 도구**: `radon raw` (Python), `eclipse-metrics`, `analizo` (multi-language), 대부분 LOC 기반 도구 부수 출력

**장점**:
- 코드 사이즈를 *LOC 보다 의미 있는* 단위로 측정 — 공백 / 주석 무관
- 정보 이론 기반 — 수학적 근거가 있음 (Shannon entropy 적용)
- Bug 예측 추정값 제공 — 실증 데이터와 0.6~0.8 상관

**한계**:
- **현대 언어에서 정확도 낮음** — generic, lambda, type inference 시대에 operator/operand 정의 모호
- Cyclomatic / Cognitive 만큼 단순하지 않아 IDE 채택률 낮음
- 같은 Halstead Volume 의 코드도 가독성 천차만별

**실무 적용**:
- 레거시 코드 *덩치 측정* — LOC 보다 객관적
- 모듈 비교 — 비슷한 LOC 라도 Volume 이 2× 차이면 복잡도 차이 시사
- 안전 critical 도메인 (의료, 항공) 에서 정량 game-keeper 로 채택 (NASA, ESA)

```python
# Halstead Metrics 계산 예시 (Python)
#
# 코드:
#   def f(x, y):
#       z = x + y
#       return z * 2
#
# 연산자 분석:
#   def, =, +, *, return  → n₁ = 5
#   def(1), =(1), +(1), *(1), return(1) → N₁ = 5
#
# 피연산자 분석:
#   f, x, y, z, 2  → n₂ = 5
#   f(1), x(2), y(2), z(2), 2(1) → N₂ = 8
#
# 파생값:
#   n  = n₁ + n₂ = 10
#   N  = N₁ + N₂ = 13
#   V  = N · log₂(n) = 13 · 3.32 = 43.2 bits
#   D  = (n₁/2) · (N₂/n₂) = 2.5 · 1.6 = 4.0
#   E  = D · V = 4.0 · 43.2 = 172.8
#   T  = E / 18 = 9.6 초
#   B  = V / 3000 = 0.014 (0 bug 예측)

import math

def halstead(distinct_ops, distinct_operands, total_ops, total_operands):
    n1, n2, N1, N2 = distinct_ops, distinct_operands, total_ops, total_operands
    n = n1 + n2
    N = N1 + N2
    V = N * math.log2(n)
    D = (n1 / 2) * (N2 / n2)
    E = D * V
    T = E / 18                # 초
    B = V / 3000              # 결함 추정
    return dict(n=n, N=N, V=V, D=D, E=E, T_sec=T, B=B)

# 산업 활용: 모듈별 V 측정 → 평균 대비 3σ 초과 모듈 우선 리팩토링
```

**관련 항목**: [Cyclomatic Complexity](#cyclomatic-complexity), [Cognitive Complexity](#cognitive-complexity), [iso-maintainability](iso25010.md#maintainability)

---

<a id="n-plus-1-query"></a>
## 6. N+1 Query Problem

**정의**: ORM 의 lazy loading 으로 인해 **1 개의 부모 쿼리 + N 개의 자식 쿼리** 가 발생하는 안티패턴. 1973 년 시스템 설계에서부터 알려진 문제로, Hibernate / Active Record / Django ORM 등의 대중화와 함께 *가장 흔한 성능 결함* 중 하나가 됨.

**핵심 시나리오**:
```
1. SELECT * FROM users LIMIT 100                  -- 1 query, N=100 행
2. for each user:
     SELECT * FROM orders WHERE user_id = ?       -- 100 queries
   → 총 101 queries (1 + 100)
```

**성능 영향**: Datacenter RTT 500 μs × 100 = 50 ms 추가 — 단일 쿼리 (수 ms) 의 10~50× 페널티. 사용자가 1,000 명이면 1,000 + 1 = 1,001 queries, 5 초+ 응답.

**식별 신호**:
- APM 에서 같은 쿼리 패턴이 100~1000× 반복
- p99 latency 가 데이터 크기에 *선형 비례* (1 user = 50 ms, 100 users = 5 s)
- DB connection pool 고갈 / `Too many connections` 에러
- 로컬 dev 에서는 빠른데 prod 에서 느림 (데이터 양 차이)

**측정 도구**: Hibernate `show_sql=true` + 카운터, Django Debug Toolbar, ActiveRecord `bullet` gem, p6spy (JDBC proxy), APM (Datadog, New Relic) span analysis

**해결책 4 종**:

| 방법 | 적용 | 예시 |
|------|-----|------|
| **Eager loading (JOIN)** | 자식이 항상 필요 | `SELECT u.*, o.* FROM users u JOIN orders o ON ...` |
| **Batch fetch (IN clause)** | 자식이 가끔 필요 | `SELECT * FROM orders WHERE user_id IN (1,2,...,100)` |
| **DataLoader pattern** | GraphQL / 비동기 | per-request 배치 + 캐시 |
| **CQRS / Denormalization** | 읽기 모델 최적화 | read-side view table |

**장점 (해결 시)**:
- DB round trip 99% 감소 — p99 latency 수 배 개선
- DB connection pool 사용량 비례 감소 → 동시성 향상

**한계 (Eager loading 의 부작용)**:
- Eager loading 은 *Cartesian product 폭발* 위험 — User 1:N Orders 1:N Items 다중 join 시 행 수 폭증
- DataLoader 는 inflight 윈도우 (보통 한 tick) 내 요청만 배치 — 정밀 튜닝 필요

**실무 적용**:
- CI 에서 N+1 detector 활성화 — Hibernate `BlazePersistence`, Django `nplusone`
- API 응답 시 *고정 쿼리 수* 예산 정의 — 1 endpoint = max 5 queries
- GraphQL 은 DataLoader 필수 패턴

```kotlin
// (Bad) N+1: 1 + 100 queries
fun listUsersWithOrders(): List<UserDto> {
    val users = userRepo.findAll()                 // 1 query
    return users.map { u ->
        val orders = orderRepo.findByUserId(u.id)  // ← per-user query, N 회
        UserDto(u.id, u.name, orders.map { it.id })
    }
}

// (Good 1) Eager loading via JOIN FETCH
@Query("SELECT u FROM User u LEFT JOIN FETCH u.orders")
fun findAllWithOrders(): List<User>                // 1 query

// (Good 2) Batch fetch via IN clause
fun listUsersWithOrders2(): List<UserDto> {
    val users = userRepo.findAll()                          // 1 query
    val userIds = users.map { it.id }
    val ordersByUser = orderRepo.findByUserIdIn(userIds)    // 1 query
        .groupBy { it.userId }
    return users.map { u ->
        UserDto(u.id, u.name, (ordersByUser[u.id] ?: emptyList()).map { it.id })
    }                                                        // 총 2 queries
}

// (Good 3) DataLoader (GraphQL)
class OrderDataLoader(private val orderRepo: OrderRepo) {
    val loader = DataLoader.newDataLoader<Long, List<Order>> { userIds ->
        // userIds 가 한 tick 분 모인 후 단일 IN 쿼리
        val orders = orderRepo.findByUserIdIn(userIds)
        userIds.map { id -> orders.filter { it.userId == id } }
    }
}
```

**관련 항목**: [iso-performance-efficiency](iso25010.md#2-performance-efficiency), [Latency Numbers](#latency-numbers), [Profiling 기법](#profiling-techniques), [code-smell-shotgun-surgery](code-smells.md#11-shotgun-surgery) (간접)

---

<a id="profiling-techniques"></a>
## 7. Profiling 기법

**정의**: 실행 중 프로그램의 *시간 / 메모리 / I/O* 자원 사용을 측정하는 기법 집합. Brendan Gregg 의 *Systems Performance* (2020) 2nd ed. 가 현행 산업 표준 텍스트. 3 대 축은 **Sampling / Tracing / Instrumentation**.

**기법 분류**:

| 기법 | 원리 | 오버헤드 | 정밀도 | 도구 |
|------|------|---------|-------:|------|
| **Sampling** | 주기적 stack snapshot (10~100 Hz) | 매우 낮음 (~1%) | 통계적 | `perf record`, async-profiler, pyspy, `py-spy` |
| **Tracing** | 모든 이벤트 (function entry/exit, syscall) 기록 | 높음 (10~50%) | 정밀 | `strace`, `ltrace`, `bpftrace`, `dtrace` |
| **Instrumentation** | 코드에 측정점 삽입 | 중간 | 정밀 | JMH, JFR (Java Flight Recorder), opentelemetry |
| **Heap dump** | 메모리 snapshot | one-shot | 정밀 | `jmap`, `pprof`, Heaptrack |
| **Flame Graph** | sampling 결과 시각화 | (선행 기법 의존) | 시각적 | Brendan Gregg 의 `flamegraph.pl`, `speedscope` |

**Flame Graph (Brendan Gregg, 2011)**:
- **x 축**: 알파벳 순 (시간 순 아님) — 가로 폭 = CPU 시간 비율
- **y 축**: stack 깊이 (아래 = root caller, 위 = leaf)
- **색**: 일반적으로 의미 없음 (시각 구분만), 변형 (differential) 은 빨강/파랑 = 증가/감소
- **읽는 법**: 위쪽이 *넓고 평평한 plateau* = bottleneck (해당 함수가 자체 CPU 많이 씀)

**핵심 통찰**:
- **Premature optimization is the root of all evil** (Donald Knuth, 1974) — *측정* 후 최적화
- 일반적으로 95% 의 시간은 5% 의 코드에서 소비 (Pareto)
- **Allocation profiling** 은 CPU profiling 만큼 중요 — GC overhead 가 hidden cost

**장점**:
- **추측 제거** — 어디가 느린지 정확히 지목
- 회귀 추적 가능 — release 전후 flame graph diff
- Production 진단 — async-profiler / py-spy 는 운영 중 부착 가능

**한계**:
- Sampling 은 *짧은 burst* 함수 놓침 — 트레이싱 필요
- Tracing 은 오버헤드로 *측정 행위가 결과 왜곡* (observer effect)
- I/O bound 워크로드는 CPU profile 만으로 부족 — off-CPU analysis 별도 필요

**실무 적용**:
- 사고 대응 (incident response) 의 표준 도구 — production load 부착
- 신규 기능 release 전 baseline flame graph 비교
- CI 에 마이크로벤치 (JMH / pytest-benchmark) 통합 — 회귀 차단

```kotlin
// Profiling 워크플로우 — JVM 예시
//
// 1. async-profiler 부착 (production safe, sampling)
//    $ ./profiler.sh -d 60 -f profile.html <pid>
//    → 60 초 동안 stack sample → HTML flame graph 출력
//
// 2. JFR (Java Flight Recorder, JDK 11+ 무료)
//    $ jcmd <pid> JFR.start duration=60s filename=app.jfr
//    → app.jfr 를 JDK Mission Control 에서 분석
//
// 3. JMH 마이크로벤치
@Benchmark
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 3, time = 1)
@Measurement(iterations = 5, time = 1)
fun benchmarkParse(state: BenchmarkState): Result {
    return jsonParser.parse(state.input)
}
// → 평균 / p99 ns 단위 측정, 회귀 시 CI 차단
//
// 4. Allocation profiling
//    async-profiler: -e alloc 옵션 → 어디서 메모리 할당 많은지
//    Flame graph 가 plateau 인 함수 = GC pressure source

// 일반 의사결정 흐름:
//   Slow request → APM trace 로 어느 endpoint?
//                → flame graph 로 어느 함수?
//                → benchmark 로 micro-optimize
//                → diff flame graph 로 검증
```

**관련 항목**: [Latency Numbers](#latency-numbers), [Latency Percentile](#latency-percentile), [USE/RED/Golden Signals](#use-red-golden-summary), [iso-performance-efficiency](iso25010.md#2-performance-efficiency)

---

<a id="latency-percentile"></a>
## 8. Latency Percentile (P50 / P90 / P99 / P99.9)

**정의**: 응답 시간 분포의 **percentile** — `Pₓ = N% 의 요청이 이 시간 이하로 처리됨`. 평균 (mean) 은 *분포 정보를 손실* 하므로 latency 표현에서 신뢰성 낮음. 핵심 원전: Jeff Dean & Luiz Barroso, *The Tail at Scale* (CACM, 2013).

**핵심 통찰: "평균은 거짓말"**:
- 100 요청 중 99 개가 10 ms, 1 개가 1000 ms → 평균 = 19.9 ms (괜찮아 보임)
- **실제**: 1% 사용자가 1 초 — 실제 UX 는 매우 나쁨
- p99 = 1000 ms 가 *진실* 을 드러냄

**대표 percentile**:

| Percentile | 의미 | 사용처 |
|-----------|------|--------|
| P50 (median) | 중앙값 | 일반적 응답 시간 |
| P90 | 90% 이하 | "보통" 사용자 경험 |
| P95 | 95% 이하 | SLO 기본 |
| P99 | 99% 이하 | tail latency 시작 |
| P99.9 (3-nines) | 99.9% 이하 | mission-critical SLO |
| P99.99 (4-nines) | 99.99% 이하 | telecom / finance |

**Tail amplification (The Tail at Scale)**:
- 단일 서버 p99 = 10 ms 일 때, 10 개 서버 fan-out 후 *전체 p99*:
  - 1 서버 p99 = 10 ms (1% slow)
  - 10 서버 중 *하나라도 slow*: 1 - 0.99¹⁰ = **9.6%** → p90.4 가 10 ms
  - **fan-out 이 클수록 tail 이 평균을 지배**
- 100 fan-out: 1 - 0.99¹⁰⁰ = **63%** → p37 만 10 ms 이하
- → 분산 시스템에서 p99 가 *훨씬 중요*, 단일 서버 평균은 의미 없음

**측정 도구**: HDR Histogram (Gil Tene), Prometheus `histogram_quantile`, Datadog `quantile()`, Grafana percentile panel

**장점**:
- **사용자 체감 정확 반영** — slow tail 이 churn / 이탈의 주범
- SLO / SLA 계약 단위 — "99% requests under 200 ms"
- 회귀 조기 발견 — 평균은 안정해 보여도 p99 가 먼저 깨짐

**한계**:
- **Naive averaging 불가** — `avg(p99_per_minute)` 는 *전체 p99 가 아님*. HDR Histogram 등 정밀 자료구조 필요
- 데이터 양이 적으면 high percentile 신뢰도 낮음 (1000 샘플 미만 p99 의미 없음)
- **Co-ordinated omission** (Gil Tene) — load generator 가 백프레셔로 정직한 분포 못 잡음 → HDR Histogram, wrk2 사용

**실무 적용**:
- SLO 정의는 *항상* p99 또는 p99.9 기준 — 평균 / max 금지
- 알람 임계값 — p99 가 baseline × 2 초과 시 page
- Capacity planning — p99 응답이 SLO 이내인 throughput 의 80% 가 운영 한계

```kotlin
// Latency Percentile 측정 — HDR Histogram (Gil Tene)
//
// dependency: org.hdrhistogram:HdrHistogram

import org.HdrHistogram.Histogram
import java.util.concurrent.TimeUnit

val histogram = Histogram(TimeUnit.MINUTES.toNanos(1), 3)
// 최대 1 분, 정밀도 3 (significant digits)

fun handleRequest(req: Request): Response {
    val start = System.nanoTime()
    try {
        return process(req)
    } finally {
        histogram.recordValue(System.nanoTime() - start)  // ns
    }
}

// 주기적 출력 (e.g. 1 분마다 metrics scrape)
fun reportPercentiles() {
    println("p50  = ${histogram.getValueAtPercentile(50.0) / 1e6} ms")
    println("p90  = ${histogram.getValueAtPercentile(90.0) / 1e6} ms")
    println("p99  = ${histogram.getValueAtPercentile(99.0) / 1e6} ms")
    println("p99.9= ${histogram.getValueAtPercentile(99.9) / 1e6} ms")
    println("max  = ${histogram.maxValue / 1e6} ms")
    histogram.reset()                                    // 다음 윈도우 초기화
}

// Prometheus 통합:
//   histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
//
// 알람 (Grafana / Alertmanager):
//   p99 > 500 ms for 5 minutes → page on-call
```

**관련 항목**: [Latency Numbers](#latency-numbers), [Apdex Score](#apdex-score), [USE/RED/Golden Signals](#use-red-golden-summary), [iso-performance-efficiency](iso25010.md#2-performance-efficiency), [iso-reliability](iso25010.md#reliability)

---

<a id="use-red-golden-summary"></a>
## 9. USE / RED / Golden Signals (요약)

**정의**: 3 가지 정평 있는 *observability 메트릭 분류 프레임워크*. 본 문서는 요약 / cross-link 용. **본체 본문은 [`../patterns/observability.md`](../patterns/observability.md)** 참조.

**3 프레임워크 비교**:

| 프레임워크 | 저자·연도 | 대상 | 메트릭 |
|----------|---------|------|--------|
| **USE Method** | Brendan Gregg, 2012 | Resources (CPU, memory, disk, network) | **U**tilization · **S**aturation · **E**rrors |
| **RED Method** | Tom Wilkie (Weaveworks), 2015 | Request-driven services | **R**ate · **E**rrors · **D**uration |
| **Golden Signals** | Google SRE Book, 2016 | User-facing services | Latency · Traffic · Errors · Saturation |

**메트릭 매핑 매트릭스**:

| 메트릭 종류 | USE | RED | Golden Signals |
|-----------|-----|-----|---------------|
| Throughput / 요청 수 | - | Rate | Traffic |
| 응답 시간 | - | Duration | Latency |
| 에러 수 / 비율 | Errors | Errors | Errors |
| 자원 사용률 | Utilization | - | Saturation (부분) |
| 자원 포화도 (queue 길이) | Saturation | - | Saturation |

**선택 기준**:

| 상황 | 권장 프레임워크 |
|------|---------------|
| 인프라 / OS / 하드웨어 진단 | **USE** (Gregg) |
| 마이크로서비스 / API 진단 | **RED** (Wilkie) |
| 사용자 facing 종합 SLO | **Golden Signals** (Google SRE) |
| 종합 (모든 layer) | 3 개 동시 — USE for infra, RED for services, Golden for SLO |

**핵심 권장**:
- 모든 서비스에 RED 최소 — Rate, Errors, Duration (p99) 3 메트릭은 기본
- 모든 resource 에 USE — CPU / Memory / Disk / Network 4 자원 × 3 항목 = 12 시계열
- SLO / SLA 정의는 Golden Signals 기반

**측정 도구**:
- Metrics: Prometheus, Datadog, New Relic, CloudWatch
- Dashboards: Grafana (Golden Signals 템플릿 다수 공개)
- SLO: Sloth (Prometheus SLO generator), Nobl9, Datadog SLO

**장점 / 한계 / 실무 적용**: → [`../patterns/observability.md`](../patterns/observability.md) 본문 참조

```kotlin
// RED 메트릭 — Spring Boot + Micrometer 예시
//
// dependency: io.micrometer:micrometer-registry-prometheus

@RestController
class OrderController(
    private val meterRegistry: MeterRegistry,
    private val orderService: OrderService,
) {
    @PostMapping("/orders")
    fun createOrder(@RequestBody req: OrderRequest): Order {
        val timer = Timer.start(meterRegistry)
        val tags = mutableListOf<Tag>(Tag.of("endpoint", "createOrder"))

        return try {
            val order = orderService.create(req)
            tags += Tag.of("status", "success")
            // R(Rate): timer.count() — 자동 카운트
            // E(Errors): status tag 로 분리
            order
        } catch (e: Exception) {
            tags += Tag.of("status", "error")
            tags += Tag.of("error_type", e.javaClass.simpleName)
            throw e
        } finally {
            // D(Duration): 분포 측정 (히스토그램)
            timer.stop(
                Timer.builder("http.request.duration")
                    .tags(tags)
                    .publishPercentiles(0.5, 0.9, 0.99)   // p50/p90/p99
                    .register(meterRegistry)
            )
        }
    }
}

// Prometheus 쿼리:
//   R: rate(http_request_duration_seconds_count[1m])
//   E: rate(http_request_duration_seconds_count{status="error"}[1m])
//        / rate(http_request_duration_seconds_count[1m])
//   D: histogram_quantile(0.99, http_request_duration_seconds_bucket)
```

**관련 항목**: [`../patterns/observability.md`](../patterns/observability.md) (본체), [Latency Percentile](#latency-percentile), [Apdex Score](#apdex-score), [Profiling 기법](#profiling-techniques), [iso-reliability](iso25010.md#reliability)

---

<a id="apdex-score"></a>
## 10. Apdex Score (Application Performance Index)

**정의**: Peter Sevcik 이 2004 년 Apdex Alliance 에서 표준화한 **사용자 만족도 단일 점수**. 응답 시간 분포를 *Satisfied / Tolerating / Frustrated* 3 영역으로 분류 후 0~1 점수로 압축. APM 도구 (New Relic, AppDynamics) 의 기본 KPI.

**핵심 수식**:
```
Apdex_T = (Satisfied_count + (Tolerating_count / 2)) / Total_count

T = target time (사용자 만족 임계값, 초)
Satisfied   : response_time ≤ T              (만족)
Tolerating  : T < response_time ≤ 4T         (참을만함)
Frustrated  : response_time > 4T  OR  error  (불만)
```

**점수 해석**:

| Apdex | 등급 | 의미 |
|-------|------|------|
| 0.94 ~ 1.00 | Excellent | 거의 모든 사용자 만족 |
| 0.85 ~ 0.93 | Good | 대다수 만족, 작은 부분 tolerating |
| 0.70 ~ 0.84 | Fair | 절반 정도만 만족 |
| 0.50 ~ 0.69 | Poor | 많은 사용자 frustrated |
| 0.00 ~ 0.49 | Unacceptable | 즉시 대응 필요 |

**T 임계값 예시** (도메인별):

| 서비스 | T (초) | 4T (frustrated 경계) |
|--------|-------:|------------------:|
| Static page | 0.5 | 2.0 |
| API endpoint (typical) | 1.0 | 4.0 |
| Search query | 2.0 | 8.0 |
| Report generation | 5.0 | 20.0 |
| Batch / long-running | 30.0 | 120.0 |

**측정 도구**: New Relic Apdex panel, AppDynamics, Datadog APM Apdex, Dynatrace, Pingdom

**장점**:
- **단일 숫자로 종합 표현** — stakeholder communication 에 강력 (CEO 도 이해)
- 응답 시간뿐 아니라 *에러 까지 frustrated 로 포함* — UX 전체 반영
- 시계열 추적 용이 — 0.91 → 0.85 같은 변화로 즉시 회귀 인지

**한계**:
- **T 임계값 선택이 자의적** — 같은 시스템도 T=1 vs T=2 점수 차이 큼
- 정보 손실 — 0.90 이 *어떻게* 0.90 인지 (전부 tolerating? 일부 frustrated?) 불명
- 분포 형태 무시 — 같은 0.90 이라도 p99 차이 큼 → percentile 보완 필수
- 산업 표준이지만 *Apdex Alliance 자체는 2020 년 비활성화* (도구는 계속 사용)

**실무 적용**:
- **공식 SLO 보조 지표** — 주 지표는 p99 latency, 보조로 Apdex (이해관계자 보고용)
- 신규 endpoint 출시 시 baseline Apdex 측정 → 회귀 차단
- 도메인별 T 임계값 협의 — UX 팀 / 비즈니스 / 엔지니어링 합의

```kotlin
// Apdex Score 계산 예시
//
// dependency: 측정은 in-memory counter 또는 Prometheus

data class ApdexSample(val durationMs: Long, val isError: Boolean)

class ApdexCalculator(private val targetMs: Long) {
    private val frustratedMs = targetMs * 4L

    private val total = AtomicLong()
    private val satisfied = AtomicLong()
    private val tolerating = AtomicLong()
    // frustrated 는 total - satisfied - tolerating

    fun record(sample: ApdexSample) {
        total.incrementAndGet()
        if (sample.isError) {
            // error → frustrated (카운트 안 함)
            return
        }
        when {
            sample.durationMs <= targetMs -> satisfied.incrementAndGet()
            sample.durationMs <= frustratedMs -> tolerating.incrementAndGet()
            // else: frustrated
        }
    }

    fun score(): Double {
        val t = total.get()
        if (t == 0L) return 1.0
        return (satisfied.get() + tolerating.get() / 2.0) / t
    }

    fun reset() {
        total.set(0); satisfied.set(0); tolerating.set(0)
    }
}

// 사용:
val apdex = ApdexCalculator(targetMs = 1000)        // T = 1 초
apdex.record(ApdexSample(durationMs = 500, isError = false))  // satisfied
apdex.record(ApdexSample(durationMs = 2500, isError = false)) // tolerating
apdex.record(ApdexSample(durationMs = 5000, isError = false)) // frustrated
apdex.record(ApdexSample(durationMs = 100, isError = true))   // frustrated (error)
println(apdex.score())  // (1 + 0.5) / 4 = 0.375 — Unacceptable

// Prometheus 쿼리:
//   sum(rate(http_request_duration_seconds_bucket{le="1"}[5m]))    -- satisfied
//   + sum(rate(http_request_duration_seconds_bucket{le="4"}[5m]))
//     - sum(rate(http_request_duration_seconds_bucket{le="1"}[5m]))) / 2
//   ─────────────────────────────────────────────────────────────────────────
//   sum(rate(http_request_duration_seconds_count[5m]))
```

**관련 항목**: [Latency Percentile](#latency-percentile), [USE/RED/Golden Signals](#use-red-golden-summary), [iso-performance-efficiency](iso25010.md#2-performance-efficiency), [iso-usability](iso25010.md#usability)

---

## 종합 의사결정 매트릭스

| 상황 | 우선 메트릭 |
|------|------------|
| 신규 알고리즘 설계 | [Big-O](#big-o-practical) → [Latency Numbers](#latency-numbers) napkin math |
| API SLO 정의 | [Latency Percentile](#latency-percentile) (p99) → [Apdex](#apdex-score) 보조 |
| 인프라 자원 진단 | [USE Method](#use-red-golden-summary) — Utilization / Saturation / Errors |
| 마이크로서비스 진단 | [RED Method](#use-red-golden-summary) — Rate / Errors / Duration |
| 사용자 체감 종합 | [Golden Signals](#use-red-golden-summary) + [Apdex](#apdex-score) |
| 느린 요청 원인 분석 | [Profiling](#profiling-techniques) — sampling → flame graph |
| ORM / DB 성능 결함 | [N+1 Query Problem](#n-plus-1-query) detector |
| 코드 복잡도 한계 | [Cyclomatic](#cyclomatic-complexity) ≤ 10, [Cognitive](#cognitive-complexity) ≤ 15 |
| 레거시 모듈 우선순위 | [Halstead Volume](#halstead-metrics) + [Cyclomatic](#cyclomatic-complexity) 결합 |
| 분산 fan-out 최적화 | [Latency Percentile](#latency-percentile) — Tail at Scale, hedged requests |

## Cross-link 인덱스

- 본 카탈로그 외부:
  - [iso25010.md](iso25010.md) — Performance Efficiency, Reliability 본체
  - [`../patterns/observability.md`](../patterns/observability.md) — USE/RED/Golden Signals 본체
  - [`../patterns/caching.md`](../patterns/caching.md) — N+1 / Latency 해소 패턴
  - [`../patterns/testing-strategies.md`](../patterns/testing-strategies.md) — Load / Stress / Soak / Spike
  - [`../algorithms/`](../algorithms/) — Big-O 별 알고리즘 분류
  - [code-smells.md](code-smells.md) — Long Method, Large Class (간접 — 측정 결과의 신호)
