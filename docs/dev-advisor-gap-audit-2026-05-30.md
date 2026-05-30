# dev-advisor 카탈로그 갭 감사 보고서

> **알고리즘 · 아키텍처 · 컴퓨터 공학(CS) 기초 누락 항목 전수 점검**

| 항목 | 값 |
|---|---|
| 감사일 | 2026-05-30 |
| 대상 | `dev-advisor` 스킬 6중 카탈로그 (패턴 529 / 알고리즘 250 / 언어 75 / 보안 106 / 원칙 206 / 품질 20) |
| 방법 | 9개 도메인 finder가 정전(CLRS·TAOCP·DDIA·OSTEP·POSA·EIP·SEI·CS2023 등) 대비 후보 도출 → 각 후보를 dev-advisor·data-advisor 전체 grep으로 **부재 적대적 검증** |
| 규모 | 85 에이전트 / 1,158 tool 호출 / 2단계 파이프라인(Find→Verify) |
| 결과 | 진짜 누락 **71건** 확정 · 거짓 누락 **5건** 기각 |

이 보고서는 멀티에이전트 워크플로우 결과를 정리한 것으로, 각 누락 항목은 grep 기반 부재 검증을 통과했다. 거짓 누락(이미 다른 이름·파일·data-advisor에 존재) 5건은 §7에서 기각 사유와 함께 분리했다.

## 1. 커버리지 총평

| 축 | 평가 | 핵심 공백 |
|---|---|---|
| **알고리즘** | ★★★★☆ CP·고급까지 폭넓음 | 의외의 기본기 구멍: Quickselect · 이진 힙(Priority Queue) · 가우스 소거 부재 |
| **아키텍처** | ★★★★★ 529 패턴 압도적 | SEI 평가 방법론(ATAM/품질속성 시나리오/전술) 통째 부재, 일부 아키텍처 스타일 |
| **CS 기초** | ★★★★☆ '앱영향 시스템내부'는 강함 | 순수 이론 부재: 복잡도(P/NP) · 계산가능성 · OSI/라우팅 · 가상메모리 · CPU 구조 |
| **무결성** | 카운트 100% 일치하나 prose·링크 결함 | 깨진 cross-link + stale '273' (본 감사에서 P0 수정 완료) |

## 2. 무결성 결함 및 P0 수정 결과

감사 중 발견된 무결성 결함은 즉시 수정하여 3개 트리(claude/codex/antigravity)에 전파하고 `verify-all.sh` 263개 검사 전부 통과를 확인했다.

| # | 결함 | 조치 | 상태 |
|---|---|---|---|
| P0-1 | `algorithms/index.md:45,452` stale 카운트 '273개' (정본 250) | '250개' 로 정정 | ✅ 완료 |
| P0-2 | `verify-counts.sh` 가드 정규식이 prose '273개 알고리즘'(개+공백) 미탐지 | `273개? *알고리즘` 으로 하드닝 (음성테스트 통과) | ✅ 완료 |
| P0-3 | `logistics.md:293,809` → `ml.md` 비존재 항목 cross-link | 시계열(ARIMA/Prophet/LSTM/Quantile) prose 정정; Gradient Boosting 은 ML 항목 추가로 해소 | 🔄 진행(Wave2 연동) |

## 3. 알고리즘 누락

### 알고리즘 — 핵심(그래프/DP/문자열/수학/기하/플로우/매칭)

> 전반적으로 매우 충실한 카탈로그다. 그래프(18), 수학(14), 문자열(11)이 학부 CS와 CP 핵심을 잘 덮고 Tarjan, Stoer-Wagner, Hierholzer, Suffix Automaton, Manacher, Pollard-Rho 등 고급 항목까지 포함한다. grep 검증 결과 NTT, Matrix Exponentiation(matrixPow), Euler totient(phi), Zeta/Mobius transform은 다른 항목 본문 코드에 이미 구현되어 있어 정전 후보 다수가 이미 커버됨을 확인했다. 공백은 Quickselect 완전 누락, Hungarian 포인터만 존재, Gaussian Elimination 부재, DP 최적화 기법군과 HLD/Centroid/Persistent SegTree/Treap 본문 부재다.

| 중요도 | 항목 | 판정 | 근거(정전) |
|---|---|---|---|
| 🟠 HIGH | **Quickselect / Median of Medians (선택 알고리즘)** | 완전 부재 | CLRS Ch.9 Medians and Order Statistics; Sedgewick 2.5 |
| 🟠 HIGH | **Hungarian / Kuhn-Munkres (헝가리안 할당)** | 부분 커버(포인터/언급만) | CP-Algorithms Hungarian algorithm; Competitive Programmer's Handbook |
| 🟡 MEDIUM | **Gaussian Elimination / Gauss-Jordan (가우스 소거법)** | 완전 부재 | Sedgewick Algorithms; CLRS Ch.28 LUP; CP-Algorithms Gauss method |
| 🟡 MEDIUM | **DP Optimizations: Convex Hull Trick / Knuth / D&C DP (DP 최적화 기법군)** | 완전 부재 | Competitive Programmer's Handbook; CP-Algorithms Divide and Conquer DP / CHT and Li C… |
| 🟡 MEDIUM | **Heavy-Light Decomposition (헤비-라이트 분해)** | 완전 부재 | CP-Algorithms Heavy-light decomposition |
| 🟡 MEDIUM | **Centroid Decomposition (센트로이드 분할)** | 부분 커버(포인터/언급만) | CP-Algorithms Centroid Decomposition |
| ⚪ LOW | **Persistent Segment Tree (영속 세그먼트 트리)** | 완전 부재 | CP-Algorithms Persistent data structures; Okasaki PFDS |
| ⚪ LOW | **Treap / Cartesian Tree (트립 / 데카르트 트리)** | 완전 부재 | CP-Algorithms Treap; Sedgewick randomized BST |

<details><summary>상세 근거·권고</summary>

**Quickselect / Median of Medians (선택 알고리즘)** (🟠 HIGH)
- 사유: k번째 순서통계량을 평균 O(n)에 찾는 학부 표준인데 카탈로그 전체 0건이다. top-k와 중앙값 등 실무 빈도가 높아 정렬 16개 중 선택 알고리즘 부재는 명백한 공백이다.
- 증거: 독립 항목으로 어디에도 존재하지 않음. 검색 증거: (1) `rg -rin -e "quickselect" -e "median of medians" -e "median-of-medians" -e "nth_element" -e "introselect" -e "BFPRT" -e "order.statistic" -e "선택 문제" -e "k-선택" dev-advisor/ data-advisor/` → flow.md:115 "프로젝트 선택 문제"(max-flow 맥락, 무관) 외 0건. (2) sorting.md 목차 표(17개 항목)에 Quickselect 없음 — "selection" 매칭은 전부 Selection Sort(…
- 권고: 신규 항목 추가 권고. dev-advisor/references/algorithms/sorting.md 또는 divide-conquer.md 에 "quickselect"(Quickselect / Hoare's Selection, 한글명: 퀵 선택) 독립 항목과 "median-of-medians"(BFPRT, 한글명: 중앙값의 중앙값) 항목을 추가하고, 평균 O(n)/최악 O(n²) vs 최악 보장 O(n), nth_element(C++ STL) 매핑을 명시. sorting.md:334 Heap Sort 활용 예시의 "K번째 큰/작은 요소 찾기" 와 quick-sort 의 partition 설명에서 신규 quickselect 항목으로 cross-link 추가. 별칭 표에 nth_element, kth smal…

**Hungarian / Kuhn-Munkres (헝가리안 할당)** (🟠 HIGH)
- 사유: matching.md와 flow.md 4곳에서 관련 알고리즘 포인터로만 등장하고 본문 항목이 없다. 최소비용 할당의 정전 표준이며 MCMF 우회 언급만으로는 부재를 메우지 못한다.
- 증거: dev-advisor references 에 Hungarian/Kuhn-Munkres 가 다수 등장하나 모두 "독립 카탈로그 항목"이 아닌 언급/교차참조/응용코드 수준임. - algorithms/matching.md:27 "Hungarian 단순화 버전" (Bipartite Matching 설명 중 지나가는 언급) - algorithms/matching.md:85, matching.md:266 "관련 알고리즘: ... Hungarian ..." (related-algorithm 푸터 cross-ref) - algorithms/flow.md:384 "관련 알고리즘: Hungarian, Edmonds-Karp" / flow…
- 권고: 신규 항목 추가 권장 — algorithms/matching.md (또는 flow.md, 비용 기반이므로 matching 이 적합) 에 `<a id="hungarian">` 앵커 + `## N. Hungarian (Kuhn-Munkres, 헝가리안 할당)` 독립 항목 신설. matching.md 목차·algorithms/index.md 항목 레지스트리(L168-170 인근)·"매칭 3개→4개" 카운트(L23, L471) 동기화 필요. 추가로 index.md 별칭 표(L520)에 `kuhn-munkres → hungarian`, `헝가리안 → hungarian` 별칭 등재. 근거: logistics.md 에서 실제 응용 코드(O(n³) 배차 최적화)로 쓰이고 matching/flow 양쪽에서 3회 cross-…

**Gaussian Elimination / Gauss-Jordan (가우스 소거법)** (🟡 MEDIUM)
- 사유: 수학 카테고리에 가우스 소거 0건이다(Gaussian 매칭은 모두 신호/이미지 필터·ML 문맥). 선형 연립방정식·역행렬·rank의 학부 선형대수 표준이며 BLAS/LAPACK을 cross-link하면서 기초 소거법 본문이 없는 것은 비대칭이다.
- 증거: dev-advisor 와 data-advisor 양 트리 전체에서 부재 확인. (1) algorithms/math.md 목차의 14개 알고리즘 = euclidean-gcd, sieve-of-eratosthenes, fast-exponentiation, modular-arithmetic, chinese-remainder-theorem, fast-fourier-transform, simpson-rule, newton-raphson, prime-factorization, miller-rabin, extended-euclidean, lucas-theorem, pollard-rho, linear-sieve — Gaussian/G…
- 권고: 신규 항목 추가 권고: algorithms/math.md 에 `gaussian-elimination` (가우스 소거법 / Gauss-Jordan, RREF) 항목 신설. 부분 피벗팅(partial pivoting), 후방대입(back-substitution), O(n^3) 복잡도, 연립 1차방정식·역행렬·행렬식 계산 활용을 포함하고, 별칭 표에 "Gaussian Elim / Gauss-Jordan / 가우스 소거 / 연립방정식 / row echelon / RREF" 등록. 기존 cross-link(BLAS/LAPACK LU)와 newton-raphson(수치해석), CRT(연립 합동식)와의 관계 링크 추가. 사용 빈도가 매우 높은 기초 수치선형대수 알고리즘이라 medium 중요도.

**DP Optimizations: Convex Hull Trick / Knuth / D&C DP (DP 최적화 기법군)** (🟡 MEDIUM)
- 사유: DP 12항목이 점화식은 덮지만 전이를 O(n^2)에서 O(n log n)/O(n)으로 줄이는 표준 최적화군(CHT, Knuth opt, D&C opt)이 모두 0건이다. CHT는 task 명시 후보이고 Knuth/D&C는 구간 DP 정전 가속 기법이라 실질적 공백이다.
- 증거: 양 트리 references 전체를 광범위 grep 한 결과, DP 최적화 기법군(Convex Hull Trick / Knuth optimization / Divide & Conquer DP / slope trick / Li Chao)은 어디에도 없음.  [부재 증거] - `grep -rni "convex hull trick|knuth optimization|divide and conquer optimization|quadrangle inequality|사각 부등식|slope trick|li chao|lichao|DP 최적화|DP optimization|aliens trick|lagrangian|wqs|divide-co…
- 권고: 신규 항목 추가 권고. dynamic-programming.md 에 "DP 최적화 기법군" 묶음 항목(예: dp-optimizations 또는 개별 convex-hull-trick / knuth-optimization / divide-conquer-dp)을 추가하고, 별칭으로 CHT, slope trick, Li Chao tree, quadrangle inequality(사각 부등식), monotonicity 등을 등록. 동시에 index.md 의 동적 프로그래밍 카운트(12→증가)와 알고리즘 테이블, 카테고리 요약(L14/L462) 동기화 필요.  중요도 medium 사유: 경쟁 프로그래밍/고급 최적화 영역의 표준 기법군이라 카탈로그 완전성 측면에서 의미 있으나, 일반 앱 개발 어드바이저 맥락에서 호출 빈…

**Heavy-Light Decomposition (헤비-라이트 분해)** (🟡 MEDIUM)
- 사유: 트리 경로 쿼리/갱신을 O(log^2 n)에 처리하는 정전 표준인데 카탈로그 전체 0건이다. LCA와 Segment Tree는 있으나 이를 결합한 트리 경로 쿼리 표준 기법이 빠져 공백이 있다.
- 증거: 두 reference 트리 전체(파일명·앵커·본문·별칭표) 검색 결과 어디에도 없음. 1) `rg -in "heavy.?light|HLD|헤비.?라이트|heavy.?path|chain decomposition|체인 분해" .../dev-advisor/references .../data-advisor/references` → 0 hits. 2) graph.md 목차(TOC, line 5-29)와 ## 헤더(line 31-1543)는 정확히 18개 항목(bfs, dfs, dijkstra, bellman-ford, floyd-warshall, a-star, prim, kruskal, topological-sort, tarja…
- 권고: 신규 항목 추가 권고: algorithms/graph.md 에 #19 "Heavy-Light Decomposition (헤비-라이트 분해, HLD)" 독립 항목 신설(트리 경로/서브트리 집계 쿼리 O(log²n), Segment Tree 결합). graph.md TOC + algorithms/index.md 매트릭스(트리 경로 집계 행) 등재. index.md 별칭표에 `hld → heavy-light-decomposition` 별칭 동시 등록. 같은 계열 미수록 기법(Centroid Decomposition, Link-Cut Tree)도 함께 보강 후보로 검토 권장. 중요도 medium: 경쟁/대용량 트리 쿼리에 핵심이나 일반 앱 개발 빈도는 LCA/Segment Tree 보다 낮음.

**Centroid Decomposition (센트로이드 분할)** (🟡 MEDIUM)
- 사유: dynamic-programming.md tree-dp의 관련 알고리즘에 포인터로만 있고 본문 부재다. 트리 경로 카운팅/거리 쿼리를 O(n log n)으로 푸는 분할정복 트리 기법의 정전 표준이다.
- 증거: 전수 grep 결과 dev-advisor/data-advisor 양 트리 243개 md 파일에서 "Centroid Decomposition" 독립 항목은 없음. 유일한 직접 언급: `dev-advisor/references/algorithms/dynamic-programming.md:1074` — "**관련 알고리즘**: Rerooting, Centroid Decomposition" (이 줄은 `## 10. Tree DP (트리 DP)` 섹션 끝의 한 줄짜리 관련-알고리즘 포인터일 뿐, 독립 헤딩/앵커/구현/복잡도 없음). 한글명 검색(`센트로이드|무게중심 분할|중심분할`) → 0건 (requirements-engine…
- 권고: 신규 독립 항목 추가 권장 — 위치는 algorithms/graph.md(트리 알고리즘 묶음, LCA 인근 #13~ 사이) 또는 algorithms/divide-conquer.md(트리 분할정복). 현재는 dynamic-programming.md:1074 의 "관련 알고리즘" 한 줄 name-drop만 있어 first-class 카탈로그 항목이 아님(검색·lookup 불가). 추가 시 한글명 "센트로이드 분할(무게중심 분할)", 복잡도 O(N log N) 전처리 / 경로 쿼리 O(log N), 별칭 "Centroid Decomposition / 무게중심 분할 / 중심 분할" 을 alias 표에 등록하고, 함께 부재인 Heavy-Light Decomposition·Euler Tour·DSU on Tree 도…

**Persistent Segment Tree (영속 세그먼트 트리)** (⚪ LOW)
- 사유: searching.md parallel-binary-search 항목의 관련 알고리즘 포인터로만 언급되고 본문이 없다. 버전별 불변 트리로 과거 상태 쿼리를 지원하는 정전 자료구조이자 함수형 자료구조 대표 예시다.
- 증거: 두 reference 트리 전체에서 "persistent"/"영속"/"persisten" 단어가 전혀 검색되지 않음. `rg --no-ignore -in "persistent|영속|persisten" dev-advisor/references data-advisor/references` → 출력 0줄(exit 0). 별도 검색 `rg --no-ignore -in "persistent segment"` 도 0줄. 기본(비영속) Segment Tree 만 존재: dev-advisor/references/algorithms/data-structures.md 항목 #2 "Segment Tree (세그먼트 트리)" (헤더 line…
- 권고: 신규 항목 추가는 선택 사항(우선순위 낮음). Persistent Segment Tree 는 경쟁 프로그래밍/구간 버전 쿼리(K-th in range, 과거 상태 조회)에서 쓰이는 고급 변형이나, 일반 앱 개발 카탈로그의 실무 빈도는 낮음. 추가한다면 data-structures.md 의 기존 segment-tree(#2) 바로 뒤에 별도 항목 또는 segment-tree 항목 내 "영속 변형(Persistent/Versioned Segment Tree)" 응용 서브섹션으로 편입하고, index.md 목차·결정 매트릭스(과거 버전/시점별 구간 쿼리 라인)에 별칭 등록 권장. 필수 추가 아님 — low priority backlog.

**Treap / Cartesian Tree (트립 / 데카르트 트리)** (⚪ LOW)
- 사유: AVL/Red-Black/B-Tree/Skip List는 있으나 randomized BST인 Treap과 Cartesian Tree가 0건이다(Splay/Cartesian Tree도 포인터로만). Treap은 implicit key로 배열 split/merge·구간 reverse를 지원하고 RMQ-Cartesian Tree 대응은 학부 표준 토픽이다.
- 증거: 두 references 트리(dev-advisor, data-advisor) 전체를 rg/grep 으로 광범위 검색한 결과 Treap / 트립 / Cartesian Tree / 데카르트 트리 정확 일치 0건 (grep 종료코드 1). - `data-structures.md` 목차 표(L7-20)의 트리 계열 항목: union-find, segment-tree, fenwick-tree, avl-tree, red-black-tree, b-tree, skip-list, lru, bloom-filter — Treap/Cartesian Tree 없음. - `algorithms/index.md` 별칭 표(L518-): knn, b…
- 권고: 신규 항목 추가 권고(우선순위 낮음). Treap 은 randomized Cartesian Tree 와 동일 구조이므로 단일 항목 `treap`(영문 Treap / Cartesian Tree, 한글 트립 / 데카르트 트리)으로 `data-structures.md` 의 균형 트리 계열(avl-tree, red-black-tree, skip-list 인근)에 추가하고, index.md 알고리즘 인덱스 및 별칭 표에 `cartesian-tree → treap`, `데카르트 트리 → treap` 별칭 등재. Skip List(확률적 BST)는 이미 있으나 그 randomized-BST 형제인 Treap 이 누락 상태. 다만 경쟁 프로그래밍 특화 구조로 앱 개발 카탈로그에서의 실무 빈도는 낮아 importance 는…

</details>

### 알고리즘 — 자료구조

> dev-advisor 의 자료구조 카탈로그(algorithms/data-structures.md, 9개 항목)는 Union-Find, Segment Tree(lazy 포함), Fenwick, AVL, Red-Black, B-Tree, Skip List, LRU, Bloom Filter 를 Kotlin 구현과 함께 충실히 다룬다. KD-Tree/R-Tree/QuadTree 등 공간 인덱스는 spatial.md, Suffix Tree/Array/Trie 는 string.md, Count-Min/HyperLogLog 는 probabilistic.md 로 적절히 분산되어 있어 중복 없이 잘 정리되어 있다. 다만 CLRS Part V(고급 자료구조)와 Open Data Structures(Morin)가 정전으로 다루는 핵심 항목 중 (1) 가장 기본인 Binary Heap/Priority Queue 자체가 독립 항목으로 없고(heap-sort 내 heapify 만 존재), (2) 고급 힙(Fibonacci/Binomial/Pairing 등)·(3) 해시 충돌 처리 상세(open addressing vs chaining, Cuckoo/Robin Hood)·(4) 자기조정/랜덤화 BST(Treap/Splay)·(5) 텍스트 에디터 자료구조(Rope/Gap B…

| 중요도 | 항목 | 판정 | 근거(정전) |
|---|---|---|---|
| 🟠 HIGH | **Binary Heap / Priority Queue (이진 힙 / 우선순위 큐)** | 완전 부재 | CLRS Ch.6 (Heapsort) / Ch.6.5 (Priority Queues); Open Data Structures Ch.10 (Heaps) |
| 🟡 MEDIUM | **Hash Table: Open Addressing vs Separate Chaining (해시 테이블 충돌 처리: 개방 주소법 vs 체이닝)** | 부분 커버(포인터/언급만) | CLRS Ch.11 (Hash Tables: chaining, open addressing); Open Data Structures Ch.5 |
| 🟡 MEDIUM | **Rope / Gap Buffer / Piece Table (로프 · 갭 버퍼 · 피스 테이블)** | 완전 부재 | Boehm, Atkinson & Plass 'Ropes: an Alternative to Strings' (1995); VS Code Piece Tabl… |
| ⚪ LOW | **Cuckoo Hashing & Robin Hood Hashing (쿠쿠 해싱 · 로빈 후드 해싱)** | 완전 부재 | Pagh & Rodler 'Cuckoo Hashing' (2001); Celis 'Robin Hood Hashing' (1986); 표준 해시 테이블 문… |
| ⚪ LOW | **Treap / Splay Tree (트립 · 스플레이 트리)** | 부분 커버(포인터/언급만) | Sleator & Tarjan 'Self-Adjusting Binary Search Trees' (1985, Splay); Aragon & Seidel… |
| ⚪ LOW | **Advanced Heaps: Fibonacci / Binomial / Pairing Heap (고급 힙: 피보나치 · 이항 · 페어링 힙)** | 완전 부재 | CLRS Ch.19 (Fibonacci Heaps), Ch.19 problems (Binomial); Fredman & Tarjan (1987) |
| ⚪ LOW | **Order-Statistics Tree / Interval Tree (순위 통계 트리 · 구간 트리)** | 완전 부재 | CLRS Ch.14 (Augmenting Data Structures: order-statistic trees, interval trees) |
| ⚪ LOW | **Persistent Data Structures / Persistent Segment Tree (영속 자료구조 · 영속 세그먼트 트리)** | 부분 커버(포인터/언급만) | Driscoll et al. 'Making Data Structures Persistent' (1989); Okasaki 'Purely Functiona… |
| ⚪ LOW | **van Emde Boas Tree / y-fast Trie (반 엠데 보아스 트리 · y-fast 트라이)** | 완전 부재 | CLRS Ch.20 (van Emde Boas Trees) |

<details><summary>상세 근거·권고</summary>

**Binary Heap / Priority Queue (이진 힙 / 우선순위 큐)** (🟠 HIGH)
- 사유: CLRS Ch.6 의 가장 기본 자료구조이자 Dijkstra/Prim/Huffman/이벤트 시뮬레이션의 전제인데, 독립 항목이 없고 heap-sort 내 heapify 코드로만 존재한다. push/pop/peek/build-heap/decrease-key 인터페이스와 array 기반 표현을 다루는 정식 항목이 없으면 고급 힙(아래 항목들)의 기준선도 설명할 수 없다.
- 증거: 독립 카탈로그 항목으로는 양 트리 어디에도 없음. (1) algorithms/data-structures.md 목차 표(9-18행)는 정확히 9개 항목(union-find, segment-tree, fenwick-tree, avl-tree, red-black-tree, b-tree, skip-list, lru, bloom-filter)만 보유 — heap/priority-queue 앵커(<a id="binary-heap"> 등) 없음. (2) algorithms/index.md:20 마스터 카탈로그 "자료구조 9개" 동일 9개 명시. (3) index.md ID 표(148-156행)·별칭 표(519-530행)에 heap…
- 권고: 신규 항목 추가 권고 — algorithms/data-structures.md 에 binary-heap(또는 priority-queue) 독립 항목 신설(이진 힙 ADT: insert/extract-min·max O(log n), heapify O(n), d-ary heap 변형, min/max-heap). index.md 자료구조 카운트 9→10 갱신 + ID 표 1행 추가 + 별칭(priority-queue, min-heap, max-heap, pq) 등록. 동시에 load-balancing.md:29 의 dangling cross-link(#min-heap 앵커)와 graph.md(Dijkstra/Prim/A*)·sorting.md#heap-sort·probabilistic.md 의 PriorityQu…

**Hash Table: Open Addressing vs Separate Chaining (해시 테이블 충돌 처리: 개방 주소법 vs 체이닝)** (🟡 MEDIUM)
- 사유: searching.md 의 hash-table-search 는 탐색 관점의 개요만 다루고, separate chaining / open addressing(linear·quadratic probing) / load factor·resizing·tombstone 같은 충돌 처리 핵심 메커니즘을 비교하는 자료구조 항목이 전무하다. 해시 테이블 내부 동작은 실무 면접·CS 커리큘럼의 단골 주제다.
- 증거: 충돌 처리 기법(개방 주소법 vs 체이닝, 선형/이차 탐사, load factor, tombstone)을 실제로 설명하는 독립 항목은 양 트리 어디에도 없음. 다만 모항목 'Hash Table Search'는 존재하며 충돌 처리 필요성을 명시함.  발견 위치: - algorithms/searching.md #8 'Hash Table Search (해시 테이블 탐색)' (anchor: searching.md:442, 카탈로그 행 searching.md:16, index.md:72 hash-table-search). 본문(searching.md:453, 462)에 "충돌 처리 필요", "해시 충돌 처리 필요" 라고 *언급만…
- 권고: 신규 항목 추가 권장(단, 모항목 보강 형태). algorithms/searching.md 의 기존 'Hash Table Search(#8)' 항목이 "충돌 처리 필요"라고만 언급하고 기법을 비워 둠 → 같은 파일 또는 data-structures.md 에 'Open Addressing vs Separate Chaining' 하위 항목/별도 entry 를 추가하여 (a) 체이닝 vs 개방 주소법 트레이드오프, (b) 선형/이차 탐사·이중 해싱, (c) load factor 와 rehashing 임계값, (d) 개방 주소법의 tombstone(삭제 슬롯 마커) 을 채우는 것이 적절. 또는 최소한 index.md alias 표에 'open addressing/separate chaining/체이닝/개방 주소법'…

**Rope / Gap Buffer / Piece Table (로프 · 갭 버퍼 · 피스 테이블)** (🟡 MEDIUM)
- 사유: 텍스트 에디터/대용량 문자열 편집의 핵심 자료구조 3종이 전무하다(Rope 는 offline-first.md 에 'rope CRDT' 예시로만 스침). Gap Buffer(Emacs), Piece Table(VS Code, Word), Rope(균형 트리 기반 O(log n) 삽입/분할)는 에디터·IDE 구현의 정전 지식이다.
- 증거: dev-advisor/data-advisor 양 트리 전수 검색 결과 어느 이름·별칭·한글명으로도 부재 확인. 1) `rg -il -e '\brope\b' -e 'gap buffer' -e 'gap-buffer' -e 'piece table' -e 'piece-table' -e '피스 테이블' -e '갭 버퍼'` 을 /Users/zime/Git/dev-advisor/claude/skills/dev-advisor 전체와 /Users/zime/Git/dev-advisor/claude/skills/data-advisor 전체에 실행 → 매칭 파일 0개(no match). 2) 주장 위치 algorithms/data-struc…
- 권고: 신규 항목 추가 권고: algorithms/data-structures.md 에 "Rope / Gap Buffer / Piece Table (편집기 텍스트 버퍼 자료구조)" 를 #10 항목으로 추가하고 index.md 별칭 표(자료구조 카테고리)에 rope / gap-buffer / piece-table 3개 alias 등록. 텍스트 에디터·IDE·협업 편집기 구현 시 핵심 자료구조이므로 dev-advisor 범위에 적합. 다만 niche(편집기 도메인 한정)이므로 importance medium. data-advisor 가 아닌 dev-advisor 측 자료구조 카탈로그가 정위치.

**Cuckoo Hashing & Robin Hood Hashing (쿠쿠 해싱 · 로빈 후드 해싱)** (⚪ LOW)
- 사유: 최악 O(1) 조회를 보장하는 Cuckoo Hashing 과 분산을 균등화하는 Robin Hood Hashing 은 현대 고성능 해시맵(Rust hashbrown, F14 등) 구현의 정전 기법인데 전혀 없다. 개방 주소법 항목과 함께 묶어 다룰 수 있다.
- 증거: 두 트리 전체 재귀 grep 결과 독립 항목 부재 확인. (1) `grep -ri "cuckoo"` 의 유일 히트는 dev-advisor/references/algorithms/data-structures.md:936 "관련 알고리즘: Cuckoo Filter, Count-Min Sketch" — 이는 §9 Bloom Filter 의 관련 알고리즘 name-drop 이며, Cuckoo *Filter*(확률적 멤버십 자료구조)는 Cuckoo *Hashing*(해시테이블 충돌 해결 기법)과 다른 개념. Cuckoo Filter 조차 독립 항목 아님. (2) `grep -ri "robin"` 히트는 전부 무관: Round R…
- 권고: 신규 항목 추가 권고(우선순위 낮음). dev-advisor/references/algorithms/data-structures.md 또는 searching.md §8(Hash Table Search) 확장으로, open-addressing 충돌해결 기법 묶음(Linear/Quadratic Probing, Cuckoo Hashing, Robin Hood Hashing, Hopscotch Hashing, Swiss Table/SwissMap) 을 단일 또는 소수 항목으로 추가. 한글 별칭(쿠쿠 해싱/로빈 후드 해싱/홉스카치 해싱)과 영문 alias 를 index.md alias 표에 등록. 단, 앱 개발 실무 빈도가 낮은 저수준 자료구조이므로 critical/high 카탈로그 보강 이후 처리해도 무방.

**Treap / Splay Tree (트립 · 스플레이 트리)** (⚪ LOW)
- 사유: AVL·Red-Black 외의 균형 BST 계열로 Treap(랜덤화 BST, 구현 단순·split/merge 용이)과 Splay Tree(자기조정, 접근 지역성·amortized O(log n))는 CLRS/Sedgewick 정전 항목이다. Splay 는 현재 본문 없이 AVL 항목의 '관련 알고리즘' cross-reference 로만 언급되어 링크가 깨진 상태다.
- 증거: 검색 대상: /Users/zime/Git/dev-advisor/claude/skills/dev-advisor/references 전체 + /Users/zime/Git/dev-advisor/claude/skills/data-advisor/references 전체.  [Splay Tree] 유일한 실질 매치 1건 — `dev-advisor/references/algorithms/data-structures.md:411` 의 AVL 트리 항목 말미 "**관련 알고리즘**: Red-Black Tree, Splay Tree" (단순 cross-reference). 독립 항목 부재: 앵커(`<a id="splay-tree">`)…
- 권고: 신규 항목 추가 권고(단, 우선순위 낮음). Splay Tree 는 data-structures.md:411 에 이름만 cross-link 되어 있을 뿐 독립 카탈로그 항목이 아니므로, 자가 조정 BST(amortized O(log n), 최근 접근 노드를 루트로 올리는 splaying — 캐시/LRU 유사 지역성 활용)로 정식 섹션(앵커 `splay-tree` + 목차 행 + index.md 등록)을 추가하면 좋다. Treap(=Cartesian Tree + 무작위 우선순위 randomized BST, 구현 단순·기대 O(log n))은 완전 부재이므로 함께 신규 항목으로 추가 가능. 다만 이미 AVL/Red-Black/B-Tree/Skip List 로 균형·확률적 BST 계열이 충분히 커버되어 실무 중복…

**Advanced Heaps: Fibonacci / Binomial / Pairing Heap (고급 힙: 피보나치 · 이항 · 페어링 힙)** (⚪ LOW)
- 사유: mergeable heap 계열이 전무하다. Fibonacci Heap 은 decrease-key O(1) amortized 로 Dijkstra/Prim 의 이론적 최적 복잡도 O(E + V log V) 를 가능케 하는 CLRS 정식 항목이고, Binomial/Pairing Heap 은 그 비교 대상이다. 우선순위 큐의 decrease-key·merge 가 필요한 그래프 알고리즘과 직접 연결된다.
- 증거: 두 트리(dev-advisor/references, data-advisor/references) 전체를 grep -rin 으로 검색. 핵심 명령: `grep -rin -E "fibonacci|binomial|pairing|leftist|skew heap|d-ary|decrease.?key|meldable|mergeable heap" dev-advisor/references/ data-advisor/references/` → 고급 힙 항목 0건. (a) data-structures.md 의 9개 카탈로그(union-find, segment-tree, fenwick-tree, avl-tree, red-black-tree,…
- 권고: 신규 항목 추가 권장하되 우선순위는 낮음. data-structures.md 에 "Advanced/Mergeable Heaps (Fibonacci · Binomial · Pairing · Leftist)" 단일 항목으로 추가하고, index.md 별칭 표에 `fibonacci-heap / binomial-heap / pairing-heap / mergeable-heap / decrease-key` 별칭 등록, graph.md 의 Dijkstra·Prim 항목에 "decrease-key O(1) amortized → Fibonacci heap 으로 O(E + V log V)" cross-link 추가가 이상적. 단 (1) 실무 빈도가 낮고 표준 라이브러리 미제공(대부분 binary heap/PriorityQu…

**Order-Statistics Tree / Interval Tree (순위 통계 트리 · 구간 트리)** (⚪ LOW)
- 사유: CLRS Ch.14(Augmenting Data Structures)의 두 대표 예시. Order-Statistics Tree 는 k번째 원소 select·rank 를 O(log n)에 지원(증강 BST), Interval Tree 는 겹치는 구간 검색을 지원한다. Segment Tree(점 인덱스 기반)와 달리 동적 구간 집합/순위 쿼리를 다루는 별도 구조로 부재하다.
- 증거: 두 레퍼런스 트리 전역에서 order-statistic / interval-tree / 순위 통계 / 구간 트리 / augmented tree / rank tree 검색 결과 0건. dev-advisor/references/algorithms/data-structures.md 의 자료구조 카탈로그는 정확히 9개(헤더 grep: Union-Find, Segment Tree, Fenwick Tree, AVL Tree, Red-Black Tree, B-Tree, Skip List, LRU Cache, Bloom Filter)뿐이며 해당 항목 없음. index.md:20 및 별칭표 index.md:148-156, alias 표…
- 권고: 신규 항목 추가는 선택 사항(우선순위 낮음). Order-Statistics Tree(augmented BST 의 rank/select — i번째 원소·원소 순위 O(log n))와 Interval Tree(구간 겹침·stabbing 쿼리)는 기존 Segment/Fenwick Tree(구간 합·min/max)와 기능이 구별되므로 중복은 아니나, 실무 앱 개발 빈도는 낮음(★~★★). 추가 시 data-structures.md 에 10·11번 항목으로 등록하고 index.md 카탈로그 수(9→11)·별칭표·라우팅 표를 동기화. 별칭으로 order-statistic-tree→OST, interval-tree, augmented-bst, rank-select-tree 등록 권장. 비용 대비 효익이 낮으면 조치 불…

**Persistent Data Structures / Persistent Segment Tree (영속 자료구조 · 영속 세그먼트 트리)** (⚪ LOW)
- 사유: 함수형/버전 관리 관점의 영속(persistent) 자료구조(path copying, fat node)와 그 대표인 Persistent Segment Tree(과거 버전 쿼리, k번째 작은 수)가 부재하다. Persistent Segment Tree 는 searching.md 의 cross-reference 로만 언급된다. functional.md 에 immutability 개념은 있으나 자료구조 구현 관점은 빠져 있다.
- 증거: 상위 개념 "Persistent Data Structures (지속 자료구조)"는 dev-advisor 에 정식 카탈로그 항목으로 존재. 단, 주장된 위치(algorithms/data-structures.md)가 아니라 patterns/functional.md 에 있음: - patterns/functional.md:921-980 — "## 11. Persistent Data Structures (지속 자료구조)", structural sharing, Persistent List/Vector(HAMT)/HashMap, Finger Tree, Red-Black Tree, 시간 여행·undo/redo·event sourcin…
- 권고: 조치 불필요(상위 개념은 covered) + 선택적 별칭/cross-link 보강. (1) 거짓 누락 방지 원칙상 "Persistent Data Structures" 는 이미 patterns/functional.md#persistent-data-structures 정식 항목이므로 신규 추가 불필요. (2) 단, 알고리즘적 "Persistent Segment Tree"(path copying / fat node / 버전별 구간쿼리)는 진짜 부재 — 경쟁 프로그래밍/version-query 수요가 있다면 algorithms/data-structures.md 의 segment-tree 항목에 "영속 세그먼트 트리(persistent segment tree, path copying)" 변형 1~2문단을 별도 sub…

**van Emde Boas Tree / y-fast Trie (반 엠데 보아스 트리 · y-fast 트라이)** (⚪ LOW)
- 사유: 정수 키 universe 에서 successor/predecessor 를 O(log log u)에 처리하는 정전 항목(CLRS Ch.20). y-fast trie 는 공간 최적화 변형. 실무 빈도는 낮지만 CS 커리큘럼/정전 완전성 관점에서 정수 자료구조의 대표로 점검 대상. 부재 확인됨.
- 증거: 두 스킬 트리 전체를 적대적으로 검색했으나 어디에도 없음. 1) 정밀 패턴 풀트리 스윕(별칭/매트릭스/인덱스 포함): `grep -rin -E "van.?emde|emde.?boas|y-?fast|x-?fast|\bveb\b|엠데|보아스" /Users/zime/Git/dev-advisor/claude/skills/dev-advisor` → 0건. data-advisor 트리도 동일 명령 → 0건. 2) 주장된 위치 algorithms/data-structures.md 의 실제 목차는 정확히 9개 항목뿐: 1.Union-Find 2.Segment Tree 3.Fenwick Tree(BIT) 4.AVL Tree 5.Red-…
- 권고: 신규 항목 추가는 선택(낮은 우선순위). vEB 트리/x-fast·y-fast 트라이는 정수 키 우주(universe) 위 O(log log u) successor/predecessor 질의가 핵심인 고급 이론 자료구조로, 앱 개발 실무 활용도가 낮아 dev-advisor 카탈로그 핵심 보강 대상은 아니다. 만약 정수 후속자 질의 카테고리를 보강하려면 data-structures.md 에 fusion tree / x-fast·y-fast trie 와 함께 한 개 항목으로 묶어 추가하고, 별칭 표에 'vEB', 'van Emde Boas', '반 엠데 보아스 트리', 'integer successor structure' 동의어 등록 권장. 그 전까지는 조치 불필요.

</details>

### 알고리즘 — 시스템(동시성/분산/OS/부하분산)

> 전반적으로 매우 충실하다. concurrent.md(CAS/LL-SC/RCU/MVCC/Hazard Pointer/Lock-Free Queue/Work-Stealing/Seqlock/Memory Barriers/ABA), distributed.md(Lamport/Vector/HLC clock, Gossip, SWIM, Anti-Entropy+Merkle, CRDT 4종, Consistent Hashing, Quorum+Sloppy+Read Repair+Hinted Handoff), os-foundations.md(GC 4계열, RR/CFS/MLFQ + EEVDF/Lottery/Stride 언급, Slab/Buddy, epoll/kqueue/io_uring, Page Replacement LRU/Clock/LFU/ARC + 2Q/LIRS/CAR/Clock-Pro/MGLRU 언급, MESI+MOESI+MESIF), load-balancing.md(RR/WRR/LC/LRT/P2C/Consistent Hash/Maglev/EWMA) 까지 OSTEP·DDIA·The Art of Multiprocessor Programming의 핵심을 폭넓게 포함한다. Rendezvous/Jump hash, Phi Accrual, 2Q/LIRS 등 다수 변형은 본문은 없어도…

| 중요도 | 항목 | 판정 | 근거(정전) |
|---|---|---|---|
| 🟡 MEDIUM | **Chandy-Lamport Distributed Snapshot (찬디-램포트 분산 스냅샷)** | 부분 커버(포인터/언급만) | Distributed Systems(van Steen-Tanenbaum) Ch.8 Global State / Chandy-Lamport 1985; 카탈로… |
| 🟡 MEDIUM | **Byzantine Fault Tolerant Consensus / PBFT (비잔틴 장애 허용 합의)** | 부분 커버(포인터/언급만) | Distributed Systems(van Steen-Tanenbaum) fault model 분류; Castro-Liskov PBFT(OSDI 1999… |
| 🟡 MEDIUM | **Two-Phase Locking / 2PL + Deadlock Detection (2단계 잠금 + 교착 검출)** | 부분 커버(포인터/언급만) | The Art of Multiprocessor Programming(Herlihy-Shavit) / OSTEP 동시성편 deadlock; 카탈로그 내 2… |
| 🟡 MEDIUM | **Queue-based Spinlocks: Ticket / MCS / CLH Lock (큐 기반 스핀락)** | 완전 부재 | The Art of Multiprocessor Programming(Herlihy-Shavit) Ch.7 Spin Locks and Contention;… |
| 🟡 MEDIUM | **Leader Election — Bully / Ring Algorithm (리더 선출 — 불리/링)** | 완전 부재 | Distributed Systems(van Steen-Tanenbaum) Ch.6 Election Algorithms (Bully/Ring, Garcia… |
| 🟡 MEDIUM | **Phi Accrual Failure Detector (파이 누적 장애 감지기)** | 부분 커버(포인터/언급만) | Hayashibara et al. 'The phi Accrual Failure Detector'(2004), Cassandra/Akka 표준 채택; 카탈… |
| 🟡 MEDIUM | **Disk / I-O Scheduling — SCAN / C-SCAN / SSTF (디스크 스케줄링)** | 완전 부재 | OSTEP Ch.37 Hard Disk Drives / I/O scheduling; algorithms/ 디렉터리 grep 결과 0건 |

<details><summary>상세 근거·권고</summary>

**Chandy-Lamport Distributed Snapshot (찬디-램포트 분산 스냅샷)** (🟡 MEDIUM)
- 사유: patterns/streaming-semantics.md 가 Chandy-Lamport 본문을 algorithms/concurrent.md 로 두 번(line 23, 759) cross-link 하지만 concurrent.md 에는 본문이 전혀 없어 dead link 다. 분산 시스템 정전의 기초 알고리즘(global consistent snapshot, deadlock/termination detection 의 기반)이며 Flink checkpoint 의 이론적 토대로 카탈로그에 본문이 있어야 한다.
- 증거: 개념 자체는 dev-advisor 에 존재함. patterns/streaming-semantics.md 8번 항목 "Checkpoint / Savepoint (체크포인트 / 세이브포인트 — Chandy-Lamport)"(L657-719)에서 정의·marker(barrier) 메커니즘·blocking 없는 전역 일관 snapshot·distributed snapshot(1985)·Flink ABS 적용을 실질적으로 서술. 추가로 streaming-semantics.md L11 "Chandy-Lamport algorithm (1985) — distributed snapshot", L23/L759 에 cross-link 존재…
- 권고: 독립 알고리즘 항목 신규 추가 권장. algorithms/distributed.md 에 "Chandy-Lamport Distributed Snapshot (찬디-램포트 분산 스냅샷)" 항목을 13번으로 추가(Lamport Clock·Vector Clock 와 동일 계열, marker/consistent global cut 알고리즘)하고 algorithms/index.md 카탈로그 row 등록. 동시에 patterns/streaming-semantics.md L23·L759 의 dangling cross-link 를 concurrent.md → distributed.md#chandy-lamport-snapshot 로 수정 필요(현재 가리키는 concurrent.md 에 섹션 부재). 별칭: distribute…

**Byzantine Fault Tolerant Consensus / PBFT (비잔틴 장애 허용 합의)** (🟡 MEDIUM)
- 사유: consensus.md 의 2PC/Paxos/Raft 는 모두 crash-fault 모델만 다루고 비잔틴(악의적/임의) 장애 합의는 없다. PBFT 는 patterns/blockchain.md 의 블록체인 합의 메커니즘 비교 표에만 한 줄 등장할 뿐 알고리즘 본문(3-phase pre-prepare/prepare/commit, 3f+1 quorum, O(n^2) 통신)이 없다. 블록체인·permissioned ledger·Tendermint/HotStuff 의 기반으로 합의 카테고리에 본문이 필요하다.
- 증거: 주장된 위치 algorithms/consensus.md(10.4K)에는 PBFT/Byzantine 독립 항목이 없음 — 해당 파일은 2PC(#2pc)/Paxos(#paxos)/Raft(#raft) 3개만 포함, 목차·앵커 모두 동일. algorithms/index.md:29 "분산 합의 | 3개 | 2PC, Paxos, Raft" 로 확정. 단, PBFT는 블록체인 패턴의 하위 항목으로 실질 서술됨: patterns/blockchain.md:30 `## 1. Consensus Mechanism 비교 (PoW / PoS / PBFT / DPoS / PoA)`, :37 "PBFT (Practical Byzantine Fau…
- 권고: 별칭 등록 + (선택) 신규 항목 검토. PBFT 의 메커니즘·장단점·변종(HotStuff/Tendermint)이 blockchain.md 에 충분히 서술되어 있으므로 '완전 부재'는 아님. 다만 개념상 합의 알고리즘 카탈로그(algorithms/consensus.md, Paxos/Raft 옆)에 독립 항목으로 없는 점이 finder 가 누락으로 인지한 원인. 권고: (1) 최소 조치 — algorithms/index.md 와 blockchain.md cross-link 에 'pbft'/'byzantine fault tolerance' 검색 별칭을 추가해 consensus-blockchain 항목으로 라우팅. (2) 강화 조치(선택) — algorithms/consensus.md 에 PBFT 를 #pbft…

**Two-Phase Locking / 2PL + Deadlock Detection (2단계 잠금 + 교착 검출)** (🟡 MEDIUM)
- 사유: 2PL 은 concurrent.md MVCC 의 '관련 알고리즘' 과 principles/concurrency-theory.md 이론 언급에만 등장하고 본문(growing/shrinking phase, Strict 2PL, lock manager)이 없다. 동반 개념인 deadlock detection(wait-for graph 사이클 탐지, Banker's algorithm)도 알고리즘 본문이 전무하다. DB 동시성 제어의 양대 축(2PL vs MVCC) 중 한쪽만 본문이 있어 불균형하며 OSTEP/DB 교과서 정전 핵심이다.
- 증거: 두 트리 전체를 grep 검색한 결과 혼합 상태 확인. [2PL 측 — 독립 항목 부재] "2PL" 리터럴은 총 7회 등장하나 모두 지나가는 언급/교차참조일 뿐 전용 항목·앵커·heading 없음: dev-advisor/references/algorithms/concurrent.md:364 (MVCC 섹션의 "관련 알고리즘: RCU, Snapshot Isolation, HLC, 2PL" 한 줄 — 주장된 위치이나 concurrent.md 의 목차 10개 항목[cas/ll-sc/rcu/mvcc/hazard-pointer/lock-free-queue/work-stealing/seqlock/memory-barriers/aba…
- 권고: 신규 항목 추가 권장(범위 한정). Deadlock Detection/Banker's/wait-for graph 이론은 이미 concurrency-theory.md#deadlock-conditions 에 충분히 존재하므로 중복 추가 불필요. 다만 Two-Phase Locking 잠금 프로토콜 자체(2PL/Strict 2PL/Rigorous 2PL의 성장-수축 단계, lock point, lock manager, MVCC와의 비교)는 동시성 제어 알고리즘으로서 독립 설명이 부재하므로, algorithms/concurrent.md 에 "Two-Phase Locking (2PL)" 항목을 신규 추가하고 목차/index.md alias 표에 등재 권장. 추가 시 별칭 'strict 2pl/rigorous 2pl/비…

**Queue-based Spinlocks: Ticket / MCS / CLH Lock (큐 기반 스핀락)** (🟡 MEDIUM)
- 사유: concurrent.md 는 lock-free(CAS/LL-SC) 와 무락 자료구조는 다루지만 lock-based 동기화 프리미티브 자체가 없다. Ticket lock, MCS lock, CLH lock 은 The Art of Multiprocessor Programming 의 핵심 챕터로 캐시 일관성 트래픽 최소화(local spinning)와 공정성을 다룬다. Linux qspinlock(MCS 변형)의 기반이며 MESI 항목(false sharing)과 직접 연결되므로 본문 부재는 동시성 영역의 실질적 공백이다.
- 증거: 전체 트리 grep 결과 0건 (exit code 1). 명령: `grep -rin -E "spinlock|spin.lock|ticket.lock|\bMCS\b|\bCLH\b|qspinlock|queued.lock|test.and.set|backoff lock|local spinning|스핀락|스핀 락" /Users/zime/Git/dev-advisor/claude/skills/dev-advisor/references` → 매치 없음. data-advisor references 도 동일 검색 0건. concurrent.md 항목 표는 정확히 10개(cas, ll-sc, rcu, mvcc, hazard-pointer, l…
- 권고: 신규 항목 추가 권고. algorithms/concurrent.md 에 큐 기반 공정 스핀락(Ticket / MCS / CLH Lock) 항목을 신설하고 항목 표(ID: queue-spinlock 또는 mcs-clh-lock)에 등록. 현재 concurrent.md 는 lock-free/wait-free 비잠금 기법 위주이고 "락 기반 접근의 한계 극복"을 전제로 하나, 실제로는 NUMA/멀티코어에서 캐시라인 바운싱을 줄이는 확장성 락(MCS=local-spinning, CLH=implicit queue, Ticket=FIFO 공정성)이 lock-free 자료구조와 상보적으로 매우 중요(Linux qspinlock=MCS 변형이 커널 기본 스핀락). os-foundations.md 또는 concurrent.…

**Leader Election — Bully / Ring Algorithm (리더 선출 — 불리/링)** (🟡 MEDIUM)
- 사유: 리더 선출은 Raft 내부 election 으로만 언급되고 독립 분산 알고리즘(Bully algorithm, Ring algorithm)으로서의 본문이 없다. 합의와 분리된 일반 leader/coordinator election 은 Distributed Systems 교과서의 표준 주제이며 Raft 없이도 코디네이터 선출이 필요한 시스템(클러스터 매니저, lock service)에서 기대되는 항목이다.
- 증거: 두 트리 전체에서 "bully | garcia.molina | ring election | coordinator election" 매칭 파일 0개 (`/usr/bin/grep -rl -E "bully|garcia.molina|ring election|coordinator election" references/ ../data-advisor/references/ | wc -l` → 0). dev-advisor 카탈로그 TOC 확인 결과: algorithms/consensus.md 항목 3개(2PC/Paxos/Raft)뿐 — Bully/Ring 독립 항목 없음. algorithms/distributed.md 항목 12개(La…
- 권고: 신규 항목 추가 권고 — algorithms/consensus.md 에 Bully Algorithm 과 Ring (token-ring) Election 을 묶은 "Leader/Coordinator Election" 항목 신설(목차 표 + <a id> 앵커 + Garcia-Molina 1982 출처). 동시에 별칭 등록: "리더 선출", "코디네이터 선출", "불리 알고리즘", "링 선출", "garcia-molina". 단, Raft 의 내부 election 과 혼동되지 않도록 "비동기 peer 그룹에서 새 코디네이터 선출(합의 아님)" 임을 명시. 고전 CS 커리큘럼 항목이나 현대 실무 빈도는 Raft/Paxos 보다 낮아 importance medium.

**Phi Accrual Failure Detector (파이 누적 장애 감지기)** (🟡 MEDIUM)
- 사유: SWIM 항목의 '관련 알고리즘' 으로만 이름이 등장하고 본문이 없다. binary suspect/alive 가 아닌 연속적 suspicion level(phi) 을 산출하는 적응형 장애 감지기로 Cassandra/Akka 클러스터의 표준 구현이다. SWIM·Heartbeat 와 함께 분산 멤버십의 핵심 빌딩블록인데 본문이 부재하다.
- 증거: 독립 항목 부재 확정. dev-advisor/references/algorithms/distributed.md 의 목차(7~20행)는 12개 항목(lamport-clock ~ quorum)만 등재, Phi Accrual 없음. 전체 `## ` 헤더 grep 결과도 1~12번만 존재(13번 없음). 이름 등장은 단 2건이며 모두 포인터일 뿐 정의 아님: (1) distributed.md:363 Gossip Protocol 의사코드 주석 "// accrual failure detector 와 결합 → suspect 판단", (2) distributed.md:455 SWIM 항목의 "**관련 알고리즘**: Gossip Pro…
- 권고: 신규 항목 추가 권장. distributed.md 에 #13 항목으로 "Phi Accrual Failure Detector (파이 누적 장애 감지기)" 정식 등재 — 목적(연속적 의심도 φ 값 산출, binary suspect 대비 adaptive threshold), 시간/공간 복잡도, 동작 원리(heartbeat 도착 간격을 정규분포/지수분포로 모델링하여 φ = -log10(P(현재까지 미수신)) 계산), 활용 예시(Akka Cluster, Cassandra, Hazelcast)를 포함. SWIM(#5)·Gossip(#4)·Heartbeat 와의 cross-link 추가. 더불어 index.md 별칭 표에 "accrual-failure-detector → phi-accrual-failure-detecto…

**Disk / I-O Scheduling — SCAN / C-SCAN / SSTF (디스크 스케줄링)** (🟡 MEDIUM)
- 사유: os-foundations.md 는 CPU 스케줄러(RR/CFS/MLFQ)와 메모리(Slab/Buddy/Page Replacement), I/O 멀티플렉싱(epoll)은 다루지만 디스크 헤드 스케줄링(FCFS/SSTF/SCAN/C-SCAN/LOOK, Linux CFQ/deadline/BFQ/mq-deadline)은 전무하다. OSTEP I/O Devices 편의 표준 주제이나 SSD 보편화로 실무 중요도는 상대적으로 낮아 importance=low.
- 증거: 광범위 grep/rg 검색 결과 dev-advisor 및 data-advisor references 전체에서 0건. 검색 명령과 결과: 1) `rg -in "sstf|c-scan|cscan|scan algorithm|look algorithm|elevator|seek time|disk schedul|cfq|bfq|mq-deadline|디스크 스케줄"` (dev+data references) → 0 매치 2) `rg -rin "...|noop scheduler|kyber|디스크 입출력" claude/skills/` (전체 skills 트리) → 0 매치 3) `rg -rin "shortest seek|circular sc…
- 권고: 신규 항목 추가 권장. os-foundations.md 에 독립 알고리즘 항목으로 "Disk / I-O Scheduling — FCFS / SSTF / SCAN / C-SCAN / LOOK / C-LOOK (디스크 스케줄링)" 추가하고, Linux 블록 레이어 실무 스케줄러(mq-deadline / BFQ / Kyber / none, 레거시 CFQ/noop)와 SSD vs HDD seek 특성을 함께 다루면 OS-foundations 의 I/O 섹션이 멀티플렉싱(epoll/io_uring)에 더해 블록 디바이스 요청 스케줄링까지 포괄하게 됨. 중요도 medium 근거: 고전 OS 정평 알고리즘이며 스토리지 성능 튜닝(I/O scheduler 선택)에 실무 연관이 있으나, 앱 레벨에서 직접 구현하는 경우는 드…

</details>

### 알고리즘 — 특화(ML/암호/압축/코덱/DSP/공간/검색)

> 전반적으로 매우 풍부하다. 공간 인덱싱(8), 검색·랭킹(8), 코덱·미디어(8), 신호처리(8), 이미지처리(8), 파서/컴파일러(10)는 각 분야 정전 핵심을 거의 빠짐없이 다루고 production 라이브러리 매핑·원전 인용까지 갖춘 모범적 카탈로그다. 검색 분야는 RRF·IVF·PQ·ScaNN·BM25F·LTR까지 폭넓고, 신호처리는 카탈로그 말미에 미수록 항목(MFCC/Particle/Adaptive/Hilbert/Beamforming)을 명시적으로 "신설 예정"으로 선언해 누락을 인지하고 있다. 반면 두 영역에 구조적 약점이 있다. (1) 암호/해시는 6개 엔트리뿐으로 비대칭 영역이 RSA 단독 — 2026년 사실상 표준인 타원곡선(ECC/Ed25519/ECDH)·키교환(Diffie-Hellman)·AEAD 스트림(ChaCha20-Poly1305)·해시(SHA-3, BLAKE2/3)가 "관련 알고리즘" 언급으로만 존재하고 실제 엔트리가 없다. (2) ML은 13개로 트랜스포머·HNSW 등 LLM 인프라는 강하나 고전 ML 주력(Decision Tree/Random Forest/GBM, PCA/SVD)이 엔트리로 부재하며, DCT는 codecs/signal/mp3에서 math.md 앵커로 링크되지만 math.md에 실제 엔트리가 없어 깨…

| 중요도 | 항목 | 판정 | 근거(정전) |
|---|---|---|---|
| 🟠 HIGH | **Elliptic Curve Cryptography — ECDSA / Ed25519 / ECDH (타원곡선 암호 — 서명·키교환)** | 부분 커버(포인터/언급만) | Handbook of Applied Cryptography Ch.4; Serious Cryptography (Aumasson) Ch.12 — Ellipt… |
| 🟠 HIGH | **Diffie-Hellman Key Exchange (디피-헬먼 키 교환)** | 부분 커버(포인터/언급만) | Handbook of Applied Cryptography §12.6; Serious Cryptography Ch.11 — Diffie-Hellman |
| 🟠 HIGH | **Decision Tree / Random Forest / Gradient Boosting (XGBoost·LightGBM) (의사결정나무·랜덤포…** | 부분 커버(포인터/언급만) | Hastie/Tibshirani ESL Ch.9·10·15; Bishop PRML §14.4 — Tree-based Models; CS2023 KA AI… |
| 🟡 MEDIUM | **ChaCha20-Poly1305 (스트림 AEAD)** | 부분 커버(포인터/언급만) | RFC 8439 (ChaCha20-Poly1305); Serious Cryptography Ch.8 — Authenticated Encryption |
| 🟡 MEDIUM | **PCA / SVD (주성분 분석 / 특이값 분해)** | 완전 부재 | Bishop PRML Ch.12 — Continuous Latent Variables (PCA); Goodfellow DL §2.12 — SVD |
| 🟡 MEDIUM | **DCT — Discrete Cosine Transform (이산 코사인 변환)** | 부분 커버(포인터/언급만) | Oppenheim DSP; Salomon Data Compression §4 — Transform Coding; ITU-T T.81(JPEG) |
| 🟡 MEDIUM | **SHA-3 / Keccak (스펀지 구조 해시)** | 부분 커버(포인터/언급만) | NIST FIPS 202 (SHA-3); Serious Cryptography Ch.5 — Hash Functions (Keccak) |
| 🟡 MEDIUM | **BLAKE2 / BLAKE3 (고속 암호 해시)** | 부분 커버(포인터/언급만) | Serious Cryptography Ch.5 (BLAKE2); BLAKE3 spec (O'Connor et al. 2020); RFC 7693(BLAK… |
| 🟡 MEDIUM | **scrypt / PBKDF2 (메모리 하드·반복 기반 키 유도 함수)** | 부분 커버(포인터/언급만) | RFC 8018 (PBKDF2); Percival scrypt paper (2009); Serious Cryptography Ch.9 — KDF |
| 🟡 MEDIUM | **Goertzel Algorithm (괴르첼 — 단일 주파수 빈 검출)** | 완전 부재 | Oppenheim DSP §9 — Goertzel Algorithm; ITU-T Q.24 (DTMF) |

<details><summary>상세 근거·권고</summary>

**Elliptic Curve Cryptography — ECDSA / Ed25519 / ECDH (타원곡선 암호 — 서명·키교환)** (🟠 HIGH)
- 사유: 비대칭 암호 엔트리가 RSA 하나뿐이다. 2026년 TLS 1.3·JWT(ES256/EdDSA)·SSH·코드사이닝·블록체인 서명은 사실상 모두 타원곡선 기반이며 RSA를 대체 중이다. crypto.md에는 ECC/Ed25519/ECDH가 RSA의 '관련 알고리즘' 한 줄 언급으로만 존재하고 구현·복잡도·키 크기 비교가 없어, 실무자가 가장 자주 쓰는 비대칭 도구가 카탈로그에서 빠져 있다.
- 증거: 6개 finder 용어(ecdsa, ed25519, elliptic, ecdh, curve25519, x25519) 전체를 dev-advisor + data-advisor references 두 트리에 재귀 grep 한 결과, data-advisor 는 0건. dev-advisor 에서는 독립 항목이 아닌 부수적 언급만 존재: (1) algorithms/crypto.md:231 — RSA 항목의 '관련 알고리즘'에 "ECC" 만 포인터로 명시 (rg -n 'ECC' crypto.md → 1건). (2) algorithms/index.md:354 — 요약 테이블 행 "| 공개키 암호화 | RSA, ECC | 암호 |".…
- 권고: 신규 항목 추가 권고: algorithms/crypto.md 에 독립 항목 "ECC (ECDSA / Ed25519 / ECDH)" 를 신설하여 목차 테이블 행 + 앵커 + 목적·복잡도·장단점·Kotlin(java.security ECGenParameterSpec/EdDSA/KeyAgreement) 코드 본문을 추가. 현재는 RSA 의 '관련 알고리즘' 포인터와 PQC 항목의 레거시 비교 언급만 있어 /algorithm ecdsa 같은 lookup 으로 도달 불가. 추가 시 별칭 표에 ECDSA/Ed25519/ECDH/Curve25519/X25519/타원곡선 동의어 등록 필요. 모바일(Android KeyStore EC 키)·TLS 1.3·JWT(ES256/EdDSA)·SSH·코드사이닝 등 실무 빈도가 RSA…

**Diffie-Hellman Key Exchange (디피-헬먼 키 교환)** (🟠 HIGH)
- 사유: 공유 비밀 합의의 정전적 시초이자 모든 키교환(ECDH·PFS·TLS handshake)의 원형이다. crypto.md에는 RSA의 '관련 알고리즘'으로만 등장하고, security-crypto-ops.md의 PFS/mTLS는 운영 패턴이라 알고리즘 원리(이산로그 난해성, MITM 취약, 인증된 DH 필요성)를 다루지 않는다.
- 증거: 독립 항목으로는 부재. 전 트리에서 hyphen-aware 검색(`rg -in "diffie.?hellman|diffie hellman|\bDHE\b|\bECDHE\b"`)으로 dev-advisor/references + data-advisor/references 전체에 단 1건만 발견됨: /Users/zime/Git/dev-advisor/claude/skills/dev-advisor/references/algorithms/crypto.md:231 의 RSA 항목 하단 "**관련 알고리즘**: ECC, ElGamal, Diffie-Hellman" — 이는 cross-reference 포인터일 뿐 독립 카탈로그 항목 아님…
- 권고: 신규 항목 추가 권장. crypto.md 에 독립 알고리즘 항목으로 "Diffie-Hellman / ECDH(E) 키 교환"을 추가(목적·시간/공간 복잡도·DLP 기반 보안·MITM 방어 위한 인증 필요성·DHE/ECDHE 의 forward secrecy·X25519 권장·자체 구현 금지 Note 포함). TLS 키 교환의 핵심이며 RSA·AES 와 동급 빈도이므로 important. 별칭으로 DH, DHE, ECDH, ECDHE, X25519, 키 합의(key agreement)를 alias/목차에 등록. 현재는 RSA 의 관련 알고리즘 포인터로만 partial 언급되어 있어 lookup(/algorithm) 으로 도달 불가.

**Decision Tree / Random Forest / Gradient Boosting (XGBoost·LightGBM) (의사결정나무·랜덤포레스트·그래디언트…** (🟠 HIGH)
- 사유: 정형(tabular) 데이터에서 사실상 default이자 실무 분류/회귀의 주력 계열이 ml.md 엔트리에 전혀 없다. K-Means의 '관련 알고리즘' 언급과 mlops.md/logistics.md의 운영 코드 조각으로만 등장할 뿐, 알고리즘 원리(정보이득·지니·bagging·boosting·잔차학습)·복잡도가 카탈로그에 없다. 트랜스포머·HNSW 같은 LLM 인프라는 풍부하나 고전 ML 주력이 비어 있는 불균형이다.
- 증거: 독립 카탈로그 항목으로는 어디에도 없음, 그러나 cross-link/usage 형태로 다수 언급되어 partially_covered 로 보수 판정.  [부재 증거 — 카탈로그 항목 아님] - algorithms/ml.md 목차(line 5-21): 13개 ML 항목(k-means, knn, linear-regression, logistic-regression, gradient-descent, naive-bayes, transformer, attention, hnsw, quantization, speculative-decoding, pagerank, node2vec) — Decision Tree/Random Forest/…
- 권고: 신규 항목 추가 권장. Decision Tree / Random Forest / Gradient Boosting(XGBoost·LightGBM·CatBoost)은 tree-based supervised learning 의 핵심 3대 계열로, 현재 ml.md 13항목(군집·회귀·딥러닝·그래프 중심)에 명백한 공백. 특히 logistics.md:293, :809 가 이미 `algorithms/ml.md — Gradient Boosting` 으로 cross-link 하고 있으나 ml.md 에 실제 entry 가 없어 dangling 링크 상태 — 이것만으로도 항목 신설 또는 최소 ml.md 에 Gradient Boosting/Tree-based 섹션 추가가 필요. 추가 시 ml.md 본문 + algorithms/…

**ChaCha20-Poly1305 (스트림 AEAD)** (🟡 MEDIUM)
- 사유: TLS 1.3의 두 필수 AEAD 중 하나(AES-GCM과 동급 mandatory)이며, AES-NI 하드웨어 가속이 없는 모바일/임베디드에서 AES-GCM보다 빠르고 타이밍 공격에 강하다. WireGuard·QUIC·OpenSSH의 기본 cipher다. crypto.md의 AES 엔트리는 GCM만 다루고 ChaCha20-Poly1305는 AES의 '관련 알고리즘' 언급으로만 존재한다.
- 증거: 검색 명령: `grep -r -i -E 'chacha|poly1305|salsa20|xchacha' .../dev-advisor/references .../data-advisor/references`. dev-advisor 전체에서 단 2개 파일만 히트, data-advisor 트리는 0건. 1) algorithms/crypto.md 목차(line 7-14) 정식 항목은 SHA-256/HMAC/RSA/AES/Bcrypt/Argon2 6개뿐 — ChaCha20-Poly1305 독립 항목 없음. crypto.md:304 `**관련 알고리즘**: ChaCha20-Poly1305, Camellia, DES (deprecated…
- 권고: 신규 항목 추가 권장: algorithms/crypto.md 에 7번째 항목으로 ChaCha20-Poly1305(스트림 AEAD)를 독립 등재하고 목차 표에 추가. AES-GCM 의 대안(상수시간 SW 구현·모바일/저전력 환경 우위, RFC 8439, IETF nonce 96-bit, XChaCha20 24-byte nonce 변형 포함)으로서 가치가 충분. 별칭으로 'ChaCha20', 'XChaCha20-Poly1305', 'Salsa20(전신)', 'RFC 8439', 'AEAD 스트림 암호' 등록. 현재는 AES 항목의 관련 알고리즘 한 줄 + 코드 스니펫 enum 값으로만 언급되어 독립 가이드는 부재.

**PCA / SVD (주성분 분석 / 특이값 분해)** (🟡 MEDIUM)
- 사유: 차원 축소·시각화 전처리·특징 추출·잠재요인 분해의 정전적 표준 기법인데 ml.md에 엔트리가 없다. math.md는 FFT는 다루지만 PCA/SVD 엔트리가 없고(hpc-scientific.md 라이브러리 cross-link만 존재), ecommerce.md의 협업필터링 SVD는 응용 언급에 그친다. Bishop이 한 장을 통째로 할애하는 비지도 학습의 핵심이 빠져 있다.
- 증거: 독립 카탈로그 항목으로 양 트리(dev/data) 어디에도 부재. 검증: 1) ml.md(주장된 위치) 목차 13개 항목 = K-Means/KNN/Linear·Logistic Regression/Gradient Descent/Naive Bayes/Transformer/Attention/HNSW/Quantization/Speculative Decoding/PageRank/Node2Vec — PCA·SVD·차원축소·t-SNE·UMAP 전무 (ml.md:9-23). 2) catalog-index.json 의 'pca' alias 는 거짓 친구: target_id=pca-physical-audit = "PCA — Physica…
- 권고: 신규 항목 추가 권장: algorithms/ml.md 에 "PCA / SVD (차원 축소)" 독립 항목 신설 (주성분분석·특이값분해·차원의 저주·whitening·explained variance 포함, 보너스로 t-SNE/UMAP 비교 표 1개). 동시에 catalog-index.json 의 'pca' alias 충돌 해소 필요 — 현재 'pca' 가 pca-physical-audit(형상감사)로 매핑되어 있어 신규 PCA(주성분분석) 항목과 약어가 겹친다. 신규 항목 alias 는 'pca-dimreduction' / 'principal-component-analysis' / '주성분분석' 으로 등록하고, 형상감사 쪽은 'pca-audit' 로 명확화 권장. SVD 는 ecommerce(Matrix Fa…

**DCT — Discrete Cosine Transform (이산 코사인 변환)** (🟡 MEDIUM)
- 사유: JPEG·MPEG·H.264·MP3·AAC의 문자 그대로의 핵심 변환인데 math.md에 엔트리가 없다(섹션 헤더에 FFT만 존재). 더욱이 codecs.md(JPEG·H.264), signal-processing.md, mp3-aac 엔트리가 모두 [DCT](math.md)로 링크하지만 math.md에 앵커가 없어 깨진 cross-link을 형성한다 — 누락이 다수 파일의 참조 무결성까지 깨고 있다.
- 증거: 독립 카탈로그 항목으로는 부재: dev-advisor refs 전체에서 `id="dct"`/`id="discrete-cosine"`/`id="mdct"` 앵커 및 `#dct`/`#discrete-cosine`/`#mdct` 링크 타겟 grep 결과 0건(exit 1). 주장된 위치 algorithms/math.md 는 14개 항목(GCD, Sieve, Fast Exp, Modular, CRT, FFT, Simpson, Newton-Raphson, Factorization, Miller-Rabin, Extended Euclidean, Lucas, Pollard's Rho, Linear Sieve)만 보유 — 6번 섹션은…
- 권고: 신규 독립 항목 추가 권장(거짓 누락 아님, 부분 커버 보강 성격): algorithms/math.md 에 `<a id="dct"></a> ## N. Discrete Cosine Transform (이산 코사인 변환)` 섹션을 신설하여 FFT 와 나란히 1D/2D DCT-II·역변환·DCT↔FFT 관계·O(N log N) 고속 알고리즘·MDCT(overlap-add) 변형을 정리하고, index.md 전역 alias 표에 `dct | Discrete Cosine Transform | 이산 코사인 변환 | 수학 | math.md#dct` 행과 별칭 `discrete-cosine-transform`, `mdct`(→ codecs.md MDCT 또는 math.md#dct) 등록. 이렇게 하면 codecs.md 의…

**SHA-3 / Keccak (스펀지 구조 해시)** (🟡 MEDIUM)
- 사유: NIST FIPS 202 표준 해시로 SHA-2와 구조(스펀지 vs Merkle-Damgård)가 근본적으로 다르고 길이확장 공격 면역, SHAKE XOF 제공이라는 고유 특성을 가진다. crypto.md의 SHA-256 엔트리는 '관련 알고리즘: SHA-3' 한 줄로만 언급하고 스펀지 원리를 다루지 않는다. 블록체인(Ethereum Keccak-256)·post-SHA-2 마이그레이션에서 실무 비중이 있다.
- 증거: 독립 항목으로는 부재하나 이름이 교차참조로 언급됨. [언급 증거] crypto.md:87 `**관련 알고리즘**: SHA-1, SHA-3, BLAKE2` (SHA-256 항목 하단의 관련 알고리즘 줄), crypto.md:39 `양자 컴퓨터에 약해질 수 있음 (SHA-3 후보)`, patterns/blockchain.md:379 `keccak256(abi.encode(...))` (Solidity 코드 사용례). [독립 항목 부재 증거] crypto.md 상단 '알고리즘 목차' 표에는 sha-256/hmac/rsa/aes/bcrypt/argon2 6개만 존재(SHA-3/Keccak 행 없음). algorithms/ind…
- 권고: 신규 항목 추가 권고: crypto.md 에 `sha-3`(Keccak, 스펀지 구조) 독립 항목을 추가하고, 별칭으로 'keccak', 'sha3', 'sponge construction(스펀지 구조)'를 등록. 앵커 `<a id="sha-3">` 신설 + crypto.md 상단 목차 표와 algorithms/index.md(라인 24의 '6개→7개', 라인 171-176 마스터 목록)에 동기화. 현재는 SHA-256 의 '관련 알고리즘' 줄로만 이름이 노출되어 lookup(/algorithm sha-3)이나 카탈로그 매칭이 불가하므로, 표준 NIST 해시(SHA-256 과 동급)인 점을 감안하면 독립 항목화 가치가 있음. blockchain.md 의 keccak256 사용처에서 cross-link 연결…

**BLAKE2 / BLAKE3 (고속 암호 해시)** (🟡 MEDIUM)
- 사유: MD5/SHA-1보다 빠르면서 SHA-3 수준 보안을 제공하는 현대 고속 해시로, BLAKE3는 병렬 트리 구조로 콘텐츠 주소화·체크섬·Cargo/Bao 등에서 채택이 확산 중이다. crypto.md에는 SHA-256의 '관련 알고리즘' 언급뿐이다. SHA-3/ECC만큼 정전 필수는 아니나 실무 채택률 상승으로 medium 가치.
- 증거: grep -rin "blake" 로 양 트리 전수 검색 결과 BLAKE 관련 매치는 dev-advisor 에 단 1건뿐: `claude/skills/dev-advisor/references/algorithms/crypto.md:87` → "**관련 알고리즘**: SHA-1, SHA-3, BLAKE2" (SHA-256 항목 하단의 cross-reference 언급일 뿐 독립 카탈로그 항목 아님). BLAKE3 는 양 트리(dev/data) 모두 grep -ric "blake3" 결과 ZERO. crypto.md 목차(9~14행)는 sha-256/hmac/rsa/aes/bcrypt/argon2 6개만 등재 — blake2/…
- 권고: 신규 항목 추가 권장. crypto.md 에 독립 항목 `blake2` / `blake3` (예: BLAKE2b/2s, BLAKE3 — SHA-256 대비 고속, 병렬 트리 해시, MAC/KDF 겸용)을 추가하고 목차·index.md alias 표·카테고리 요약(6→8개)에 함께 반영. 최소한 BLAKE2 는 이미 SHA-256 의 관련 알고리즘으로 cross-ref 되어 있으므로 alias 등록 + 짧은 독립 항목화가 자연스러움. 우선순위는 medium — BLAKE3 가 콘텐츠 무결성/고속 체크섬(예: 동기화·CAS·dedup)에서 현업 채택이 늘고 있어 카탈로그 완전성 측면 가치가 있으나, SHA-256/HMAC/Argon2 가 핵심 use-case 를 이미 커버하므로 critical/high 까지는…

**scrypt / PBKDF2 (메모리 하드·반복 기반 키 유도 함수)** (🟡 MEDIUM)
- 사유: 비밀번호 해싱/KDF 계열에서 Bcrypt·Argon2는 엔트리가 있으나 PBKDF2(FIPS 표준, 디스크 암호화·WPA2·iOS Keychain 광범위)와 scrypt(Litecoin·Tarsnap)는 독립 엔트리가 없다. PBKDF2는 bcrypt 엔트리 코드 내에서 '대체 시연'으로만 등장하고 알고리즘 자체 설명(반복·HMAC 기반, GPU 취약성)이 정리돼 있지 않다.
- 증거: 검색 명령: `grep -rin "scrypt|pbkdf" dev-advisor/references` 및 data-advisor 전체. [발견 - dev-advisor] - algorithms/crypto.md:384 → Bcrypt 항목의 "관련 알고리즘: scrypt, Argon2, PBKDF2" (cross-reference) - algorithms/crypto.md:452 → Argon2 항목의 "관련 알고리즘: Bcrypt, scrypt, Balloon" - algorithms/crypto.md:298,342-366 → Argon2/Bcrypt 섹션 내 코드 예제로 PBKDF2 사용(표준 라이브러리 fallba…
- 권고: scrypt 와 PBKDF2 는 Bcrypt/Argon2 와 동급의 표준 KDF/비밀번호 해시 알고리즘이며, 이미 두 기존 항목의 "관련 알고리즘"으로 이름이 등장하고 PBKDF2 는 코드 예제까지 존재하나 독립 카탈로그 항목(heading + ID + 별칭표 행)은 없음. 권고: (1) algorithms/crypto.md 에 scrypt, PBKDF2 두 항목을 신규 추가하고 algorithms/index.md 별칭 표에 `scrypt`/`pbkdf2` ID 행 등록(요약 "6개"→"8개" 갱신). 또는 최소한 (2) Argon2/Bcrypt 항목 내 비교 섹션을 보강하고 별칭 표에 `scrypt`,`pbkdf2` → crypto.md#argon2 로 alias 등록하여 lookup 가능하게 함. 완전…

**Goertzel Algorithm (괴르첼 — 단일 주파수 빈 검출)** (🟡 MEDIUM)
- 사유: 특정 소수 주파수만 검출할 때 FFT보다 효율적인 표준 기법으로 DTMF(전화 톤) 디코딩·톤 검출의 정석이다. 카탈로그 전체에서 0 hit으로 완전 부재하며 signal-processing.md 말미의 '신설 예정' 목록에도 포함돼 있지 않다. 다만 응용 범위가 좁아 low 우선순위.
- 증거: 전 범위 재귀 grep 결과 어디에도 없음. (1) `command grep -rEin "goertzel|괴르|single[ -]?(tone|frequency|bin)|단일[ -]?(주파수|톤|빈)|DTMF" .../dev-advisor/references/` → EXIT 1 (무매치). (2) 동일 정규식 + `goertzel|괴르|DTMF` 로 `/Users/zime/Git/dev-advisor/` 전체 `*.md` (codex + claude 양 트리) → EXIT 1 (무매치). (3) data-advisor 전체(`.../data-advisor/`)에서도 EXIT 1; data-advisor 의 algorith…
- 권고: 신규 항목 추가 권장. 위치: algorithms/signal-processing.md (목차 표에 9번째 행 `goertzel` 추가 + 본문 섹션). Goertzel 은 STFT/FFT 와 명확히 구분되는 단일 빈 DFT(O(N)/bin, 전체 FFT 불필요)로 DTMF 톤 검출·실시간 주파수 존재 검사에 표준적으로 쓰이므로 독립 항목 가치가 있음. 별칭/검색어로 'goertzel', '괴르첼', 'single-tone detection', '단일 주파수 검출', 'DTMF' 등록 권장. (FFT 본체는 math.md 에 있으니 cross-link 추가.) 중요도 medium: DSP 정평 알고리즘이나 범용성은 FFT/필터류보다 niche.

</details>

## 4. 아키텍처 누락

### 아키텍처 — 패턴군

> 아키텍처 패턴군은 매우 풍부하게 커버되어 있다. 52 카테고리/529 패턴 규모로, GoF·POSA 동시성(Reactor/Proactor/Active Object/Monitor)·Richardson Microservices(Saga/CQRS/Event Sourcing/Outbox/BFF/API Gateway/Service Mesh/TCC + 분산 트랜잭션 선택 매트릭스)·Fowler PoEAA(데이터 접근/도메인)·Hohpe-Woolf EIP 16종·Nygard Release It!(Circuit Breaker/Bulkhead/Retry/Timeout/Backpressure)·Azure Cloud Design Patterns 다수가 이미 존재한다. 다만 (1) 아키텍처 스타일 분류 측면(Fundamentals of Software Architecture·POSA Vol.1)에서 Microkernel/Plugin·Space-Based·Pipeline·Broker·Blackboard 같은 정전 스타일이 빠져 있고, (2) Azure Cloud Design Patterns 중 Gateway 3종·Valet Key·Static Content Hosting·Gatekeeper·Async Request-Reply 등 운영 빈도 높은 항목이 명시적으로 없으며…

| 중요도 | 항목 | 판정 | 근거(정전) |
|---|---|---|---|
| 🟡 MEDIUM | **Microkernel / Plugin Architecture (마이크로커널/플러그인 아키텍처)** | 완전 부재 | Fundamentals of Software Architecture (Ford-Richards) Ch.12 Microkernel; POSA Vol.1 M… |
| 🟡 MEDIUM | **Valet Key (밸릿 키 / Pre-signed URL 패턴)** | 완전 부재 | Azure Cloud Design Patterns — Valet Key pattern |
| 🟡 MEDIUM | **Leader Election (리더 선출 — 분산 조정 패턴)** | 부분 커버(포인터/언급만) | Azure Cloud Design Patterns — Leader Election; POSA/SRE distributed coordination |
| 🟡 MEDIUM | **Deployment Stamps / Geode (배포 스탬프 / 지오드 — 멀티리전 확장 패턴)** | 완전 부재 | Azure Cloud Design Patterns — Deployment Stamps / Geode |
| 🟡 MEDIUM | **Messaging Gateway / Service Activator (메시징 게이트웨이 / 서비스 액티베이터 — EIP Endpoint)** | 완전 부재 | Enterprise Integration Patterns (Hohpe-Woolf) — Messaging Endpoints (Messaging Gatewa… |
| ⚪ LOW | **Space-Based Architecture (공간 기반 아키텍처 / In-Memory Data Grid)** | 완전 부재 | Fundamentals of Software Architecture (Ford-Richards) Ch.15 Space-Based Architecture |
| ⚪ LOW | **Broker Architecture Pattern (브로커 아키텍처 패턴, POSA)** | 부분 커버(포인터/언급만) | POSA Vol.1 (Buschmann et al.) Broker pattern |
| ⚪ LOW | **Gateway Aggregation / Offloading / Routing (게이트웨이 집계/오프로딩/라우팅)** | 부분 커버(포인터/언급만) | Azure Cloud Design Patterns — Gateway Aggregation / Gateway Offloading / Gateway Rout… |
| ⚪ LOW | **Steady State / Fail Fast (정상 상태 유지 / 빠른 실패 — Release It! 안정성 패턴)** | 부분 커버(포인터/언급만) | Release It! (Nygard) Stability Patterns — Steady State, Fail Fast |
| ⚪ LOW | **Gatekeeper (게이트키퍼 패턴)** | 완전 부재 | Azure Cloud Design Patterns — Gatekeeper pattern |

<details><summary>상세 근거·권고</summary>

**Microkernel / Plugin Architecture (마이크로커널/플러그인 아키텍처)** (🟡 MEDIUM)
- 사유: Fundamentals of Software Architecture(Ford-Richards)와 POSA Vol.1 이 정의하는 핵심 아키텍처 스타일이다. IDE(Eclipse/VSCode), 브라우저 확장, ERP 등 코어+플러그인 제품의 정전 패턴인데 architectural.md 16스타일에 빠져 있다. micro-frontend 의 plugin 언급만 있고 백엔드/데스크톱 코어-플러그인 스타일은 부재.
- 권고: 신규 항목 추가 권고: patterns/architectural.md 에 '## 18. Microkernel / Plugin Architecture (마이크로커널/플러그인 아키텍처)' 신설. 사유 — Layered/Microservices/Event-Driven/Serverless 등 동급의 system-level 아키텍처 스타일(Mark Richards/Garlan&Shaw 분류)인데 형제 스타일은 모두 수록되어 있으나 본 스타일만 누락. 대표 사례(Eclipse RCP/OSGi, IntelliJ/VSCode 확장, Jenkins/Chrome 확장, ELK 등)와 core-system+plugin-component+registry 구조, OCP 와의 연결을 기술. 추가 시 solid.md:77,90 의 '…

**Valet Key (밸릿 키 / Pre-signed URL 패턴)** (🟡 MEDIUM)
- 사유: Azure Cloud Design Patterns 의 핵심 패턴 — 클라이언트가 서버를 거치지 않고 제한된 권한 토큰(S3 presigned URL, SAS token)으로 스토리지에 직접 read/write. logistics.md 에 presigned URL 사용 사례 1건만 있을 뿐 대용량 업로드/다운로드 오프로딩의 정전 패턴으로 정형화되어 있지 않다. 미디어 업로드 아키텍처 설계 시 빈번히 필요.
- 권고: 신규 항목 추가 권고. patterns/distributed.md 또는 보안 관점이라면 security-authz.md 에 "Valet Key (밸릿 키)" 독립 항목 신설 — 클라이언트에 제한적·시한적 직접 접근 토큰(S3 Pre-signed URL, Azure SAS token)을 발급해 서버 경유 업/다운로드 부하를 우회하는 Azure 클라우드 디자인 패턴. 별칭 표에 Pre-signed URL, presigned URL, SAS token, Shared Access Signature, signed URL, 밸릿/발렛 키를 동의어로 등록. 중요도 medium: 클라우드 오브젝트 스토리지 기반 앱에서 매우 흔하지만 보안/성능 최적화 보조 패턴 성격이라 critical/high 까지는 아님.

**Leader Election (리더 선출 — 분산 조정 패턴)** (🟡 MEDIUM)
- 사유: Azure Cloud Design Patterns 의 독립 패턴이자 분산 시스템 조정의 필수 어휘다. 현재 Leader Election 은 algorithms/consensus.md(Raft/Paxos 하위 문제)로만 존재하고, patterns/ 에는 '단일 인스턴스가 작업 코디네이터 역할을 맡고 장애 시 재선출' 하는 조정 패턴(분산 락 기반 리더, 스케줄러 단일화)이 부재하다. Cron/배치 중복 실행 방지 등 실무 설계 시 자주 요구됨.
- 권고: 별칭 등록 권장(신규 독립 항목 불필요). Leader Election 은 이미 consensus.md 의 Raft 항목 안에 전용 의사코드·서브문제로 충실히 다뤄지므로 별도 패턴/알고리즘 항목 신설은 중복임. 다만 검색성(finder lookup) 향상을 위해 algorithms/index.md 의 raft 행 alias/keyword 에 "Leader Election / 리더 선출" 을 추가하고, consensus.md 의 Leader Election 섹션에 `<a id="leader-election">` 앵커를 부여해 cross-link(예: db-fundamentals.md:471 "분산 락/리더 선출" 에서 직접 deep-link)하는 것을 권장. 분산 락(distributed lock) 기반 리더…

**Deployment Stamps / Geode (배포 스탬프 / 지오드 — 멀티리전 확장 패턴)** (🟡 MEDIUM)
- 사유: Azure Cloud Design Patterns 의 멀티테넌시/지리적 분산 확장 패턴. Deployment Stamps(독립 배포 단위를 복제해 테넌트/리전 확장), Geode(geo-distributed 활성-활성 노드). data-modeling.md 의 Multi-Leader/Geo-replication 와 일부 겹치나 배포 토폴로지 패턴으로는 부재. SaaS 멀티리전 설계 시 참조 가치 있으나 빈도 낮아 low.
- 권고: 신규 항목 추가 권고: patterns/distributed.md(또는 data-modeling.md 인접) 에 "Deployment Stamps / Geode (배포 스탬프 / 지오드)" 를 멀티리전 확장·격리 아키텍처 패턴(Azure Architecture Center 의 Deployment Stamps + Geode 패턴; scale unit 단위 풀스택 복제, 리전별 독립 배포로 blast-radius 격리·지리적 지연 최소화)으로 신설. 동시에 cell-based architecture / bulkhead(reliability.md) / Sharding(data-modeling.md) 와 cross-link 하고, alias 표에 'deployment-stamp', 'stamp(주의: 기존 stam…

**Messaging Gateway / Service Activator (메시징 게이트웨이 / 서비스 액티베이터 — EIP Endpoint)** (🟡 MEDIUM)
- 사유: EIP(Hohpe-Woolf)의 Messaging Endpoint 계열 패턴(Messaging Gateway = 도메인 API 뒤로 메시징 숨김, Service Activator = 메시지를 도메인 서비스 호출로 연결)이 integration.md 16패턴(주로 라우팅/변환 계열)에 부재하다. Spring Integration/Camel 어휘의 기반이나, 다른 패턴들로 우회 표현 가능해 importance low.
- 권고: 신규 항목 추가 권고. integration.md가 명시적으로 EIP(Hohpe) 카탈로그 기반인데 EIP "Message Endpoint" 계열(Messaging Gateway, Service Activator, Polling Consumer, Event-Driven Consumer, Idempotent Receiver 등)이 통째로 빠져 있어 카탈로그 완결성 관점에서 누락이 명확. integration.md에 "Message Endpoint 패턴군"으로 묶어 추가하고, index.md alias 표에 messaging-gateway/service-activator/idempotent-receiver 등록 권장. importance는 medium — 핵심 EIP이긴 하나 Competing Consumers…

**Space-Based Architecture (공간 기반 아키텍처 / In-Memory Data Grid)** (⚪ LOW)
- 사유: Fundamentals of Software Architecture 의 독립 챕터(처리 유닛 + 가상화 미들웨어 + tuple space 로 DB 병목 제거, 극단적 탄력성)다. 고동시성·가변 부하 시스템(티켓팅/경매)의 정전 스타일인데 카탈로그 전체에 tuple space / data grid 개념이 전무하다.
- 권고: 신규 항목 추가(선택, 우선순위 낮음). architectural.md 에 "18. Space-Based Architecture (공간 기반 아키텍처 / In-Memory Data Grid)" 를 추가하고 index.md 의 architectural 나열·카운트(16→17)·별칭 표에 등록 권장. 다만 모바일/앱 개발 중심 카탈로그 특성상 실수요가 낮고(극단적 동시성·탄력 확장이 필요한 고부하 백엔드 한정 패턴), Hazelcast/Apache Ignite 등 IMDG 도구가 이미 distributed 알고리즘에서 부분 언급되므로 우선순위는 low. 추가 시 GigaSpaces/Apache Ignite/Hazelcast(tuple space, processing unit, virtualized middlew…

**Broker Architecture Pattern (브로커 아키텍처 패턴, POSA)** (⚪ LOW)
- 사유: POSA Vol.1 의 정전 아키텍처 패턴(분산 객체 위치 투명성 — CORBA/RMI/메시지 브로커의 이론적 기반). Message Broker(integration.md)는 메시징 미들웨어 관점이고 POSA Broker 는 분산 객체 중개 아키텍처 패턴으로 별개다. 다만 현대 실무 빈도가 낮아 importance 는 low.
- 권고: 조치 불필요(보수적). 명명된 POSA Broker 아키텍처 패턴은 독립 항목/별칭으로 부재하나, "intermediary 가 송수신을 분리"하는 핵심 개념은 Message Broker(integration.md §3/§17, alias 등록됨)로 사실상 커버되고, RPC 중개 측면은 SOA/Microservices/Proxy 항목으로 분산 커버됨. 추가 가치가 낮아(현대 앱 개발에서 CORBA-style 브로커 미들웨어 직접 구현 빈도 희소) 신규 항목 추가는 권장하지 않음. 굳이 한다면 integration.md 또는 architectural.md 별칭 표에 "Broker (POSA) → Message Broker / SOA 참조" 형태의 cross-link 별칭 1줄 추가로 충분.

**Gateway Aggregation / Offloading / Routing (게이트웨이 집계/오프로딩/라우팅)** (⚪ LOW)
- 사유: Azure Cloud Design Patterns 의 명시적 3종 Gateway 패턴이다. distributed.md 의 API Gateway(§8)는 통합 진입점만 다루고, 다운스트림 N콜을 1콜로 합치는 Aggregation, TLS종료/인증을 게이트웨이로 빼는 Offloading, 경로 기반 Routing 을 별도 의사결정 단위로 구분하지 않는다. 마이크로서비스 게이트웨이 설계의 표준 어휘인데 부재.
- 권고: 조치 불필요(보수적 판정). 핵심 의도(단일 진입점에서의 라우팅·집계·횡단관심사 오프로딩)는 이미 distributed.md "## 8. API Gateway" 에 충분히 흡수되어 있어 신규 독립 항목 추가는 카탈로그 중복·과세분화를 유발함. 검색 발견율 향상이 필요하다면 최소 비용 옵션으로 index.md 의 api-gateway 별칭 행에 동의어("Gateway Aggregation / Offloading / Routing")를 별칭으로 병기하거나, distributed.md API Gateway 항목 본문에 "(= Azure Gateway Aggregation / Offloading / Routing 통합)" 1줄 주석 추가 정도만 선택적으로 권장. 별도 항목 신설은 비권장.

**Steady State / Fail Fast (정상 상태 유지 / 빠른 실패 — Release It! 안정성 패턴)** (⚪ LOW)
- 사유: Nygard Release It! 의 핵심 Stability Pattern 인 Steady State(로그/세션/캐시 무한 증식 방지, 자가 정리)와 Fail Fast(요청 진입 시 선검증으로 자원 낭비 차단)가 reliability.md(9패턴: Circuit Breaker/Retry/Bulkhead/Timeout/Rate Limiter/Backpressure/Health/Sidecar/Ambassador)에 부재하다. Fail-Fast 는 error-handling.md 에 코드 수준으로만 있고 시스템 안정성 패턴 관점은 빠짐.
- 권고: 묶음 후보를 분리 처리. (1) Fail Fast: 조치 불필요 — patterns/error-handling.md#fail-fast-safe 에 이미 1급 항목·별칭(페일패스트)·cross-link 완비. (2) Steady State(Nygard): Chaos "Steady State Hypothesis" 와 명확히 다른 안정성 패턴이므로 신규 추가를 고려할 수 있으나 우선순위 낮음(low). 추가한다면 patterns/reliability.md 에 "Steady State (정상 상태 유지 — 자원 누적 방지/주기적 purge)" 항목 신설 + index.md 별칭 등록 권장. 단, 기존 카탈로그가 자원 고갈 측면을 Timeout/Bulkhead/Backpressure/Rate Limiter 로 이미…

**Gatekeeper (게이트키퍼 패턴)** (⚪ LOW)
- 사유: Azure Cloud Design Patterns 의 보안 격리 패턴 — 전용 호스트 인스턴스가 클라이언트와 백엔드 사이를 중개해 검증/위생화하고, 백엔드는 게이트키퍼만 신뢰. API Gateway/BFF 와 의도가 다르며(보안 표면 축소가 목적) 부재. 단 security 도메인과 경계가 겹쳐 importance low.
- 권고: 신규 항목 추가는 우선순위 낮음(low). 사유: (1) 핵심 검증/요청 차단 책임은 이미 API Gateway(distributed.md #8), BFF, Service Mesh, Anti-Corruption Layer 로 상당 부분 커버되며 실무에서 Gatekeeper 는 이들의 변형으로 다뤄지는 경우가 많음. (2) OPA/Gatekeeper 별칭(정책 게이트키퍼)이 존재해 finder 의 단순 키워드 검색에서 거짓 매칭 위험 큼 — 만약 추가한다면 반드시 OPA/Gatekeeper 와 명확히 구분되는 ID/한글명(예: `gatekeeper-broker | Gatekeeper (브로커) | 게이트키퍼 브로커`)을 부여해 혼동 방지 필요. 즉시 조치보다는, Valet Key 와 묶어 클라우드 보안 디자인…

</details>

### 아키텍처 — 원칙·이론

> 전반적으로 매우 충실하다. 진화적 아키텍처(evolutionary-arch.md: Fitness Function·Architectural Quanta·Static/Dynamic Coupling·Modularity Metric/LCOM·Bounded Context·LRM·Architecture-as-Hypothesis)와 탄력성 이론(resilience-theory.md: Brittleness/Robustness/Resilience·Drift·Safety-II·STAMP·Antifragility·Graceful Degradation·Chaos·4 Cornerstones)은 정전 수준으로 깊다. 데이터 일관성/복제/분산 트레이드오프는 concurrency-theory.md(Linearizability·Serializability·SI/SSI·Causal/Eventual·Happens-Before·Liveness/Safety·Deadlock·Race)와 patterns/data-modeling.md(CAP·PACELC·Consistency Models·Single/Multi/Leaderless Replication·Sharding) 양쪽에서 DDIA급으로 커버된다. 4+1 View(sdlc-models.md)·C4(documentation.md)·Co…

| 중요도 | 항목 | 판정 | 근거(정전) |
|---|---|---|---|
| 🟠 HIGH | **Byzantine Generals Problem & BFT theory (비잔틴 장군 문제 / 비잔틴 결함 허용 3f+1)** | 부분 커버(포인터/언급만) | Lamport, Shostak, Pease — 'The Byzantine Generals Problem' (ACM TOPLAS 1982); Castro-… |
| 🟠 HIGH | **Fallacies of Distributed Computing (분산 컴퓨팅의 오류 8가지 — Deutsch/Gosling)** | 완전 부재 | L. Peter Deutsch & James Gosling — Fallacies of Distributed Computing (Sun Microsyste… |
| 🟠 HIGH | **Amdahl's Law & Universal Scalability Law (확장성 정량 법칙 — 암달 법칙 / USL)** | 부분 커버(포인터/언급만) | Amdahl (AFIPS 1967); Neil Gunther — Guerrilla Capacity Planning (USL); 확장성 정량 분석의 표준 |
| 🟡 MEDIUM | **ATAM / SAAM / CBAM — Architecture Evaluation Methods (아키텍처 평가 방법)** | 완전 부재 | Bass, Clements, Kazman — Software Architecture in Practice (SEI, 4th ed.); Clements e… |
| 🟡 MEDIUM | **Quality Attribute Scenarios (품질속성 시나리오 — Source/Stimulus/Artifact/Environment/Re…** | 완전 부재 | Bass-Clements-Kazman — Software Architecture in Practice, Ch.4 'Understanding Quality… |
| 🟡 MEDIUM | **Architectural Tactics (아키텍처 전술 — availability/modifiability/performance/security…** | 완전 부재 | Bass-Clements-Kazman — Software Architecture in Practice (Part II: Quality Attributes… |
| 🟡 MEDIUM | **End-to-End Argument in System Design (단대단 논증 — Saltzer-Reed-Clark 1984)** | 완전 부재 | Saltzer, Reed, Clark — 'End-to-End Arguments in System Design' (ACM TOCS 1984) |
| 🟡 MEDIUM | **Harvest & Yield / AKF Scale Cube (가용성 세분화 + 확장 3축)** | 완전 부재 | Fox & Brewer — 'Harvest, Yield, and Scalable Tolerant Systems' (HotOS 1999); Abbott &… |

<details><summary>상세 근거·권고</summary>

**Byzantine Generals Problem & BFT theory (비잔틴 장군 문제 / 비잔틴 결함 허용 3f+1)** (🟠 HIGH)
- 사유: consensus.md 는 crash-fault 계열(2PC·Paxos·Raft)만 다루고 FLP 불가능성은 concurrency-theory.md 에 있으나, Lamport-Shostak-Pease(1982)의 Byzantine Generals Problem 과 BFT 정량 한계(3f+1 노드, 2/3 정직 다수)는 부재하다. PBFT 는 blockchain.md 에 '메커니즘 비교'로만 등장할 뿐 근저 이론(왜 3f+1 인가)이 없어, 비잔틴 환경 합의 설계의 정전 근거가 빠진다.
- 권고: 신규 항목 추가 권고. algorithms/consensus.md 에 4번째 항목 'byzantine'(Byzantine Generals Problem / PBFT)을 추가하고, 핵심 이론(3f+1 노드 하한, oral message 시 m+1 rounds·3m+1 노드 불가능성 — Lamport-Shostak-Pease 1982, signed message 차이, interactive consistency)을 의사코드와 함께 정식 entry 로 기술. consensus.md 목차/algorithms/index.md 별칭표(byzantine, pbft, bft, 3f+1, 비잔틴, 비잔틴장군)에 alias 등록. 기존 patterns/blockchain.md PBFT 라인과 cross-link. 사유: 현재…

**Fallacies of Distributed Computing (분산 컴퓨팅의 오류 8가지 — Deutsch/Gosling)** (🟠 HIGH)
- 사유: '네트워크는 신뢰할 수 있다·지연은 0·대역폭은 무한·토폴로지는 불변' 등 8가지 오류는 분산 시스템 설계자가 반드시 경계해야 할 정전 체크리스트인데 0건이다. micro-principles.md 에 Conway/Hyrum/Postel 등 사회·시스템 격언은 있으나 이 분산 고전이 빠져 있어, 분산 패턴(integration/reliability) 설계 시 흔한 함정 경고의 표준 인용처가 없다.
- 권고: 신규 항목 추가 권고. 가장 적합한 수록 위치는 principles/micro-principles.md(Conway's Law·Hyrum's Law·Postel's Law 등 named-law/원칙을 모으는 파일 — Fallacies of Distributed Computing은 동일 성격의 '명명된 분산 시스템 가정 오류 모음'). 8개 오류(1. The network is reliable / 2. Latency is zero / 3. Bandwidth is infinite / 4. The network is secure / 5. Topology doesn't change / 6. There is one administrator / 7. Transport cost is zero / 8. The networ…

**Amdahl's Law & Universal Scalability Law (확장성 정량 법칙 — 암달 법칙 / USL)** (🟠 HIGH)
- 사유: performance-metrics.md 는 Big-O·Latency·Percentile·Apdex 는 다루나 '병렬화·노드 추가가 처리량을 얼마나 올리는가'를 정량화하는 Amdahl's Law(직렬 부분 한계)와 Gunther 의 USL(경합+일관성 비용으로 인한 retrograde scalability)이 부재하다. evolutionary-arch.md 의 Scalability 특성이 '측정 대상'으로만 언급될 뿐 그 상한을 예측하는 정전 모델이 없어, 수평 확장 의사결정의 이론 근거가 빠진다.
- 권고: 신규 항목 추가 권고. performance-metrics.md 에 "Amdahl's Law & Universal Scalability Law" 독립 항목(#11)을 추가하라 — Amdahl 속도향상 상한(S=1/(s+(1-s)/P)), Gustafson 법칙(scaled speedup), Gunther USL(C(N)=N/(1+α(N-1)+βN(N-1)), α=contention/직렬화, β=coherency/crosstalk, retrograde scaling 변곡점 N*=√((1-α)/β)) 을 포함. 별칭 표에 amdahl/USL/gunther/gustafson/retrograde scalability 등록. hpc-scientific.md 의 기존 Amdahl 공식과 cross-link 연결. da…

**ATAM / SAAM / CBAM — Architecture Evaluation Methods (아키텍처 평가 방법)** (🟡 MEDIUM)
- 사유: Bass-Clements-Kazman 'Software Architecture in Practice'(SEI)와 ATAM(Architecture Tradeoff Analysis Method)은 본 작업이 지정한 정전이자 아키텍처 평가의 사실상 표준인데 카탈로그 전체에서 0건이다. recommend/validate 모드에서 '이 설계가 품질목표를 만족하는가'를 stakeholder 합의·utility tree·sensitivity/tradeoff point로 구조화하는 정전 절차가 없어, 아키텍처 평가가 ad-hoc 으로 남는다.
- 권고: 신규 항목 추가 권장. principles/evolutionary-arch.md 를 확장하기보다 별도 항목으로 다루는 편이 정합적 — evolutionary-arch 는 진화적/지속 평가(Fitness Function) 관점이고, ATAM/SAAM/CBAM 은 SEI 의 시나리오 기반 사전 아키텍처 심사(utility tree, sensitivity/tradeoff point, stakeholder workshop) 관점이라 패러다임이 다름. 신규 principles/architecture-evaluation.md (Kazman·Klein·Clements, *Evaluating Software Architecture*) 추가 후 별칭 `atam`/`saam`/`cbam`/`utility-tree` 를 pri…

**Quality Attribute Scenarios (품질속성 시나리오 — Source/Stimulus/Artifact/Environment/Response/Res…** (🟡 MEDIUM)
- 사유: evolutionary-arch.md 의 Architectural Characteristics(-ilities)와 iso25010.md 8 품질특성은 '무엇'을 정의하지만, 그것을 검증 가능한 6-part 시나리오(자극원·자극·아티팩트·환경·응답·응답측정)로 구체화하는 SEI 정전 형식이 없다. Fitness Function(evolutionary-arch.md)이 시나리오의 자동화 대상인데, 그 입력이 되는 정형 시나리오 표기가 빠져 비기능 요구가 측정식으로 떨어지는 다리가 끊긴다.
- 권고: 신규 항목 추가 권장. SEI/Bass-Clements 의 Quality Attribute Scenario(6-part: Source/Stimulus/Artifact/Environment/Response/Response Measure)는 아키텍처 평가(ATAM·utility tree)의 핵심 산출물로, 현재 카탈로그가 다루는 fitness function(evolutionary-arch.md)·ISO 25010 특성(iso25010.md)과 상호보완 관계다(특성을 측정 가능한 시나리오로 구체화 → fitness function 으로 코드화하는 다리). 권장 방안: (a) principles/iso25010.md 에 "Quality Attribute Scenario(6-part)" 섹션 추가 + fitness…

**Architectural Tactics (아키텍처 전술 — availability/modifiability/performance/security tactics)** (🟡 MEDIUM)
- 사유: Bass 의 Tactics 는 패턴(reliability.md 의 Circuit Breaker 등 구현)과 품질속성 사이의 정전적 중간 계층 — 예: availability(Ping/Echo·Heartbeat·Voting·Active Redundancy), modifiability(Encapsulate·Restrict Dependencies·Defer Binding), performance(Manage Resource Demand/Resources). 카탈로그의 'tactic' 매칭은 전부 MITRE ATT&CK(보안)·Coq proof tactic 으로 무관하다. 품질속성→전술→패턴 매핑이 없어 설계 결정의 정전 추론…
- 권고: 신규 항목 추가 권고 (단, medium 우선순위). Bass/Clements/Kazman "Software Architecture in Practice" 의 Architectural Tactics 카탈로그(availability: ping/echo·heartbeat·active/passive redundancy·rollback / modifiability: anticipate change·encapsulate·defer binding / performance: increase resources·introduce concurrency·bound execution times / security: detect/resist/react/recover-from attack)를 principles/ 에 추가하는 것이…

**End-to-End Argument in System Design (단대단 논증 — Saltzer-Reed-Clark 1984)** (🟡 MEDIUM)
- 사유: 기능을 어느 계층에 배치할지 결정하는 분산/네트워크 시스템 설계의 정전 원칙인데 부재하다. 카탈로그의 Saltzer 매칭은 전부 Saltzer & Schroeder(1975) 보안 8원칙(최소권한)으로 *다른 논문*이며, Saltzer-Reed-Clark(1984)의 end-to-end argument 와 무관하다. 신뢰성·기능 배치(예: 재전송/암호화/중복제거를 엔드포인트 vs 네트워크 중간에 둘지) 판단의 정전 기준이 빠진다.
- 권고: 신규 항목 추가 권장. 위치 — principles/micro-principles.md 에 독립 원칙으로 추가하거나(Postel's Law 와 같은 API·상호운용성 카테고리), patterns/distributed.md 의 설계 근거 원칙으로 cross-link. 핵심 명제(기능은 통신 시스템 양 끝(endpoint)에서 완전·정확히 구현되어야 하며 하위 계층은 성능 최적화 목적의 부분 구현만 정당화됨)와 현대적 후손(smart endpoints/dumb pipes 마이크로서비스 원칙, REST/HTTP over reliable transport 설계)을 함께 기술. 별칭 등록: "단대단 논증", "end-to-end principle", "smart endpoints dumb pipes", "Saltze…

**Harvest & Yield / AKF Scale Cube (가용성 세분화 + 확장 3축)** (🟡 MEDIUM)
- 사유: Fox & Brewer(1999)의 Harvest/Yield 는 CAP 를 '전부/전무'가 아닌 *부분 응답 품질(harvest)*과 *요청 성공률(yield)*로 세분화하는 정전 보완이고, AKF Scale Cube(X/Y/Z축 확장)는 확장 전략의 표준 분류다. CAP/PACELC 와 Graceful Degradation 은 풍부하나 이 둘은 0건이다. 중요도는 낮음 — 기존 항목으로 상당 부분 대체 추론 가능하나, 정전 인용처로서의 명시성은 없다.
- 권고: 신규 항목 추가 권장. (1) Harvest/Yield 모델(Fox & Brewer 1999) — data-modeling.md CAP(1번)/PACELC(2번) 다음에 'CAP 정련: 부분 가용성(Yield=응답된 요청 비율, Harvest=반영된 데이터 비율)' 서브섹션으로 추가하고 CAP 항목에서 cross-link. (2) AKF Scale Cube(Abbott & Fisher, The Art of Scalability) — 확장성 3축(X=수평 복제/cloning, Y=기능 분해, Z=데이터 파티셔닝)을 별도 패턴/원칙 항목으로 신설하고, 기존 Sharding/Partitioning(7번)·Consistent Hashing(8번)을 Z축에, Microservices/functional decompo…

</details>

## 5. 컴퓨터 공학(CS) 기초 누락

> **의도된 갭 존중**: DB 엔진/트랜잭션 이론(ACID/격리/2PL/WAL/B+tree)은 data-advisor로 이관되어 제외. PL 순수 의미론은 standards-mapping.md가 '응용 advisor 의도적 갭(◐)'으로 명시하여 제외.

### CS 기초 — 이론A(복잡도/계산이론/타입/형식기법)

> 타입 이론(type-systems.md 10항목: HM/ADT/variance/HKT/linear·affine/dependent/effect/nominal·structural)과 형식 기법(formal-methods.md 5항목: TLA+/Alloy/Hoare/Model Checking/Z+SPIN+NuSMV, Separation Logic·SAT/SMT는 도구 백엔드로 언급), 동시성 정합성(concurrency-theory.md: Linearizability/Serializability/Liveness-Safety/FLP/Deadlock), 파싱(parsing.md 10항목)은 정전 대비 풍부하게 커버되어 이 영역은 전반적으로 강하다. Big-O는 performance-metrics.md에서 형식 정의(Bachmann-Landau)+실용 복잡도 클래스 표로 잘 다뤄진다. 그러나 **계산 복잡도 이론**(P/NP/NP-complete/환원/Cook-Levin)과 **계산 가능성/형식 언어 이론**(Halting/Rice/Turing Machine/Chomsky/Pumping/CYK)은 정전이 핵심으로 기대하는 주제임에도 passing mention 수준이거나 완전 부재다. CS2023 FPL/MSF의 순수 이론(람다 칼큘러스·denotation…

| 중요도 | 항목 | 판정 | 근거(정전) |
|---|---|---|---|
| 🟡 MEDIUM | **Computational Complexity Classes & NP-completeness (복잡도 클래스·NP-완전성: P/NP/NP-comp…** | 부분 커버(포인터/언급만) | Sipser Ch.7 (Time Complexity) / CLRS Ch.34 (NP-Completeness) / CS2023 KA AL (Algorith… |
| 🟡 MEDIUM | **Computability & Decidability (계산 가능성: Halting Problem · Rice's Theorem · Turing…** | 완전 부재 | Sipser Ch.3-5 (Church-Turing, Decidability, Reducibility) / CS2023 KA FPL+AL |
| 🟡 MEDIUM | **Amortized Analysis (분할 상환 분석: Aggregate · Accounting · Potential Method)** | 완전 부재 | CLRS Ch.16 (Amortized Analysis) / CS2023 KA AL |
| 🟡 MEDIUM | **Master Theorem & Recurrence Solving (마스터 정리 + 점화식 해법: 3 cases, substitution, rec…** | 부분 커버(포인터/언급만) | CLRS Ch.4 (Divide-and-Conquer / Master Method) / CS2023 KA AL |
| 🟡 MEDIUM | **Approximation Algorithms (근사 알고리즘: approximation ratio, PTAS/FPTAS)** | 부분 커버(포인터/언급만) | CLRS Ch.35 (Approximation Algorithms) / Vazirani / CS2023 KA AL |
| 🟡 MEDIUM | **Lambda Calculus & System F (람다 대수: untyped/simply-typed λ-calculus, System F, Cu…** | 완전 부재 | TAPL(Pierce) Ch.5-9,23 (Untyped/Typed Lambda-Calculus, System F) / CS2023 KA FPL |
| ⚪ LOW | **Formal Language Theory (형식 언어: Chomsky Hierarchy · Pumping Lemma · Thompson Cons…** | 부분 커버(포인터/언급만) | Sipser Ch.1-2 (Regular & Context-Free Languages) / CLRS(parsing은 부록) / CS2023 KA FPL |
| ⚪ LOW | **Randomized Algorithms Classification (무작위 알고리즘: Las Vegas vs Monte Carlo, one/tw…** | 완전 부재 | CLRS Ch.5 (Probabilistic Analysis & Randomized Algorithms) / Motwani-Raghavan / CS202… |

<details><summary>상세 근거·권고</summary>

**Computational Complexity Classes & NP-completeness (복잡도 클래스·NP-완전성: P/NP/NP-complete/NP-ha…** (🟡 MEDIUM)
- 사유: 실무 알고리즘 의사결정의 핵심 — '이 문제가 NP-hard인가? 그럼 근사/휴리스틱으로 가야 하는가?'를 판단하는 기준 이론. 현재 graph.md('3-SAT는 NP-complete' 1줄), backtracking.md/dynamic-programming.md('NP-Complete/NP-Hard 문제' 불릿)에만 passing mention이고, P vs NP·환원·Cook-Levin·복잡도 클래스 정의를 다루는 전용 섹션이 전무하다. 250 알고리즘 카탈로그가 복잡도 이론 토대 없이 나열되어 있는 셈.
- 권고: 신규 항목 추가 권고(보수적 partially 판정). 복잡도 클래스 이론(P/NP/NP-complete/NP-hard/co-NP/PSPACE + 다항시간 환원 + Cook-Levin 정리)은 알고리즘 설계의 이론적 토대이나 현재 산발적 "NP-hard/NP-complete" 언급만 있고 통합 다룬 항목이 없음. 두 가지 배치 옵션: (1) algorithms/ 카테고리에 'complexity-theory'(복잡도 이론) 독립 항목 신설 후 index.md 카테고리/ID인덱스/별칭표 동기화, 또는 (2) principles/ 트리(formal-methods.md 인접)에 이론 항목으로 추가. 별칭으로 P-NP, NP-complete, NP-hard, Cook-Levin, complexity-class, 난해…

**Computability & Decidability (계산 가능성: Halting Problem · Rice's Theorem · Turing Machine ·…** (🟡 MEDIUM)
- 사유: 왜 정적 분석/타입 검사/종료 검출에 근본적 한계가 있는가의 이론적 근거. 정지 문제·Rice 정리는 '모든 비자명 의미적 속성은 결정 불가능'을 말해 린터·검증 도구의 한계를 설명한다. 카탈로그 전체에서 'undecidable'은 type-systems.md의 dependent type 각주 1회뿐이고 Turing Machine·Halting Problem·Rice's Theorem은 완전 부재. 형식 기법(formal-methods.md)이 '왜 자동 증명에 한계가 있는가'를 설명할 토대가 없다.
- 권고: 신규 항목 추가 권장. 위치는 algorithms/index.md(claimed) 보다 principles 트리의 신규 파일 또는 formal-methods.md 인접 섹션(이론적 한계의 근원)이 더 적합. 항목 구성: Turing Machine / Church-Turing thesis / Halting Problem(정지 문제, undecidable) / Rice's Theorem(라이스 정리) / Turing-completeness / decidability vs computability 구분. type-systems.md:671 의 "undecidable" 한 줄에서 신규 항목 앵커로 cross-link 연결 권장. 별칭 표에 한글명(정지 문제·라이스 정리·튜링 기계·계산 가능성·결정 가능성) 등록.

**Amortized Analysis (분할 상환 분석: Aggregate · Accounting · Potential Method)** (🟡 MEDIUM)
- 사유: 동적 배열·Union-Find·Fenwick·splay 등 카탈로그의 여러 자료구조가 amortized 비용으로만 정당화되는데, 'O(1) amortized'(concurrent.md, os-foundations.md ARC) 라벨만 붙어 있고 aggregate/accounting/potential 3대 분석법 자체의 설명이 없다. 왜 최악 단일 연산은 비싸지만 시퀀스 평균은 싼지를 증명하는 표준 기법이 부재해, 자료구조 복잡도 주장의 근거가 공중에 떠 있다.
- 권고: 신규 항목 추가 권고. algorithms/index.md 의 `## 복잡도 비교` 인접에 "알고리즘 분석 기법" 섹션을 신설하거나 data-structures.md 도입부에 분할 상환 분석(Aggregate · Accounting/Banker's · Potential Method, potential function Φ)을 독립 항목으로 추가. CLRS Ch.17 수준의 기초 분석 이론이며 이미 카탈로그에 존재하는 Union-Find(경로압축)·동적 배열·Splay Tree 의 amortized 상한 근거를 연결하면 교육적 완결성↑. index.md 별칭 표에 `분할 상환 분석 / amortized analysis / aggregate / accounting / potential method` alias 등…

**Master Theorem & Recurrence Solving (마스터 정리 + 점화식 해법: 3 cases, substitution, recursion-tre…** (🟡 MEDIUM)
- 사유: divide-conquer.md 인트로가 '점화식/마스터 정리 해석을 다룬다'고 선언하고 merge-sort 항목에서도 '마스터 정리 해석'을 표방하지만, 실제로 T(n)=aT(n/b)+f(n)의 3 cases 공식·a/b/f 비교 규칙·recursion tree/substitution 해법이 본문에 한 번도 서술되지 않는다(grep으로 case 1/2/3, log_b a 부재 확인). 분할정복 5항목(Strassen·Karatsuba 등)의 복잡도가 어떻게 도출되는지 독자가 따라갈 수 없다.
- 권고: 신규 항목 추가 권장(단, 거짓 누락 아님 — 명칭은 이미 divide-conquer.md:79 에 언급되어 있으므로 partially_covered). 권고 조치: divide-conquer.md 에 'master-theorem' (또는 'recurrence-solving') 앵커로 독립 항목을 신설하여 (a) Master Theorem 3 cases 와 T(n)=aT(n/b)+f(n) / log_b a 비교, (b) substitution method, (c) recursion-tree method 를 본문으로 채우고, TOC(라인 7-13)와 algorithms/index.md(라인 108-112)에 행을 추가. divide-conquer.md:79 의 기존 안내문이 실제 내용으로 뒷받침되도록 보완하는…

**Approximation Algorithms (근사 알고리즘: approximation ratio, PTAS/FPTAS)** (🟡 MEDIUM)
- 사유: NP-hard 문제(TSP·Vertex Cover·Set Cover·Knapsack)에 대한 실용 대응책인 근사 알고리즘이 토픽으로 부재. backtracking.md에 '그리디 색칠(근사 알고리즘)' 주석 1회뿐이고 approximation ratio·PTAS/FPTAS·근사 보장 개념이 없다. NP-completeness 갭과 짝을 이루는 부재 — '난해 문제를 만났을 때 무엇을 하는가'의 후속편이 비어 있다. 단 우선순위는 NP 이론 도입 이후로 낮음.
- 권고: 신규 독립 항목 추가 권장. approximation ratio / c-approximation / PTAS / FPTAS / inapproximability 같은 이론 골격이 카탈로그에 전무하므로, algorithms 카테고리(예: backtracking 또는 greedy 인접, 혹은 신규 "근사/난해(NP-hard) 알고리즘" 절)에 독립 항목으로 추가. 추가 시 기존 산재 언급(backtracking.md greedy coloring, game-ai/graph.md TSP 근사)을 cross-link 하여 통합. 별칭 표에 'approximation algorithm / 근사 알고리즘 / approximation ratio / 근사 비율 / PTAS / FPTAS / 2-approximation' 등록…

**Lambda Calculus & System F (람다 대수: untyped/simply-typed λ-calculus, System F, Curry-Howard…** (🟡 MEDIUM)
- 사유: type-systems.md가 HM·dependent type(λΠ-calculus 언급)·effect 등 고급 주제는 다루나, 그 토대인 untyped/simply-typed lambda calculus와 System F(polymorphic λ-calculus, HM의 상위), Curry-Howard 대응의 전용 설명이 없다(Curry-Howard는 dependent type 정의 안 1회·lean.md 1회 언급뿐). TAPL의 출발점이 비어 있어 타입 이론 항목들이 기초 없이 시작된다. 단 standards-mapping.md가 람다 칼큘러스 미커버를 '의도된 갭'으로 명시했으므로 우선순위 낮음.
- 권고: 신규 항목 추가 권고. references/principles/type-systems.md 에 "11. Lambda Calculus & System F (람다 대수: untyped → simply-typed λ-calculus → System F(polymorphic lambda) → Curry-Howard 대응)" 를 추가하여 기존 #4 Hindley-Milner / #7 HKT / #9 Dependent Types / #10 Effect System 의 이론적 토대(formal foundation)를 명시하는 것이 적절. 별칭 표에 람다 대수, 람다 계산, 시스템 F, 커리-하워드, polymorphic lambda, simply-typed lambda, propositions-as-types 등록 권장…

**Formal Language Theory (형식 언어: Chomsky Hierarchy · Pumping Lemma · Thompson Construction(정…** (⚪ LOW)
- 사유: 파싱 카탈로그(LL/LR/Earley/PEG 등 10항목)는 파서 구현은 풍부하나 그 밑의 언어 이론 토대가 비어 있다. DFA/NFA는 lexing의 구현 노트로만 등장하고, 정규식↔NFA 변환(Thompson), 펌핑 보조정리(언어 클래스 한계 증명), Chomsky 계층(정규/문맥자유/문맥의존/재귀가능열거), CYK(CFG 멤버십 O(n^3)) 모두 부재. '왜 정규식으로 중첩 괄호를 못 파싱하는가(=비정규)'를 설명할 이론이 없다.
- 권고: 제안된 4개 하위 주제(Chomsky Hierarchy·Pumping Lemma·Thompson Construction·CYK) 자체는 어디에도 독립 항목으로 없으므로 신규 추가 후보로 유효하나, dev-advisor algorithms 카탈로그는 의도적으로 "실용 파싱 알고리즘"에 한정되어 있고(이론 항목 미수록 일관 정책), parsing.md 가 이미 NFA→DFA 변환·CFG·Earley(CFG 인식)를 실용 맥락에서 다루므로 실무 advisor 관점 중요도는 낮음. 권고: (1) 신규 독립 항목 추가는 보류(이론 편중, advisor 실용 범위 밖). (2) 보강이 필요하면 parsing.md 의 Lexing 항목에 "Thompson construction" 명칭을, Earley 항목 관련 알고리즘…

**Randomized Algorithms Classification (무작위 알고리즘: Las Vegas vs Monte Carlo, one/two-sided er…** (⚪ LOW)
- 사유: probabilistic.md(Fisher-Yates/Reservoir/Count-Min/HyperLogLog)와 ml.md(MCTS)에 무작위 기법이 흩어져 있으나, Las Vegas(항상 정답·시간 랜덤) vs Monte Carlo(시간 고정·확률적 오답, one/two-sided error)라는 표준 분류 틀이 없다. Miller-Rabin(Monte Carlo)·Quick Sort 랜덤 피벗(Las Vegas)·Pollard's Rho 등을 통합 설명할 분류 개념이 부재해 '왜 이 알고리즘의 오류 확률을 반복으로 낮출 수 있는가'를 일관되게 다루지 못한다.
- 권고: 신규 항목 추가(선택, 낮은 우선순위): probabilistic.md 또는 index.md 의 알고리즘 개념 도입부에 'Randomized Algorithms Classification' 섹션을 추가하여 Las Vegas(항상 정답, 실행시간 확률적) vs Monte Carlo(빠른 고정시간, 오답 확률 존재) 및 one-sided/two-sided error taxonomy 를 정식화 권장. 기존 Miller-Rabin(Monte Carlo, one-sided)·Fisher-Yates(Las Vegas 성격)·Rabin-Karp 등 인스턴스와 cross-link 하면 분류 framework 로서 가치 상승. 단 개별 알고리즘 인스턴스는 이미 풍부하므로 교육적 보강 성격으로 importance=low.

</details>

### CS 기초 — 이론B(OS/네트워크/DB엔진/컴파일러/구조)

> 이 도메인은 dev-advisor에서 "앱 개발에 영향을 주는 시스템 내부" 관점으로 매우 풍부하게 커버되어 있다. OS는 GC 4종(Mark-Sweep/Generational/G1/ZGC-Shenandoah)·스케줄러 3종(RR/CFS/MLFQ)·메모리 할당자(Slab/Buddy)·I/O 멀티플렉싱(epoll/kqueue/io_uring)·페이지 교체(LRU/Clock/LFU/ARC)·MESI 캐시 일관성까지 os-foundations.md에 깊이 있게 있고, Deadlock 4조건/Banker's/prevention·avoidance는 concurrency-theory.md에 정식 항목으로 존재한다. 동시성은 CAS/LL-SC/RCU/MVCC/Hazard Pointer/Memory Barriers/Work-Stealing 등 concurrent.md에 정전급으로 충실하다. 네트워크는 networking.md가 TCP/UDP·혼잡제어(Reno/CUBIC/BBR)·QUIC·HTTP/1-2-3·TLS·DNS·NAT·WebSocket·WebRTC를 다룬다(transport/application 계층 위주). 컴파일러는 parsing.md에 lexing부터 LR/LALR/Earley/Pratt/PEG·AST·SSA·Register Allocation까…

| 중요도 | 항목 | 판정 | 근거(정전) |
|---|---|---|---|
| 🟡 MEDIUM | **Compiler Semantic Analysis & Optimization Passes (의미 분석 + IR 최적화 패스: data-flow a…** | 부분 커버(포인터/언급만) | Dragon Book (Aho-Lam-Sethi-Ullman) Ch.6·9 / Engineering a Compiler (Cooper-Torczon) C… |
| 🟡 MEDIUM | **OSI / TCP-IP Layering Model (OSI 7계층 ↔ TCP/IP 4계층 참조 모델)** | 완전 부재 | Kurose-Ross Top-Down Approach Ch.1.5 / Tanenbaum Computer Networks Ch.1 / CS2023 KA N… |
| 🟡 MEDIUM | **IP Routing Protocols (라우팅: Distance-Vector / Link-State / OSPF / BGP, IP forward…** | 완전 부재 | Kurose-Ross Ch.5 (Network Layer: Control Plane) / Tanenbaum Ch.5 / CS2023 KA NC |
| 🟡 MEDIUM | **Reliable Data Transfer / ARQ & Link-Layer Flow Control (Stop-and-Wait / Go-Back-…** | 부분 커버(포인터/언급만) | Kurose-Ross Ch.3.4 (Principles of Reliable Data Transfer) / Tanenbaum Ch.3 / CS2023 K… |
| 🟡 MEDIUM | **Amdahl's Law & Gustafson's Law (병렬 성능 법칙: speedup 상한·strong/weak scaling)** | 부분 커버(포인터/언급만) | Hennessy-Patterson Quantitative Approach Ch.1.9 / CSAPP Ch.5 / CS2023 KA AR·PDC(Paral… |
| 🟡 MEDIUM | **CPU Microarchitecture: Pipelining / Branch Prediction / Out-of-Order / SIMD Vect…** | 완전 부재 | Hennessy-Patterson Quantitative Approach Ch.3 / CSAPP Ch.4-5 / CS2023 KA AR(Architect… |
| 🟡 MEDIUM | **Process vs Thread Execution Model (프로세스 vs 스레드: 주소공간 공유·컨텍스트 스위치 비용·kernel/user/…** | 완전 부재 | OSTEP Ch.4·26 / Tanenbaum Modern OS Ch.2 / CS2023 KA OS |
| 🟡 MEDIUM | **Virtual Memory Mechanism (가상 메모리 메커니즘: Paging / Page Table / TLB / Segmentation…** | 완전 부재 | OSTEP Ch.13-22 (Virtualizing Memory) / Tanenbaum Modern OS Ch.3 / CS2023 KA OS / CSAP… |
| ⚪ LOW | **Error Detection & Correction Codes (오류 검출·정정: Checksum / CRC / Hamming Code / Pa…** | 부분 커버(포인터/언급만) | Kurose-Ross Ch.6.2 / Tanenbaum Ch.3.2 (Error Detection and Correction) / CSAPP Ch.6 (… |

<details><summary>상세 근거·권고</summary>

**Compiler Semantic Analysis & Optimization Passes (의미 분석 + IR 최적화 패스: data-flow analysis /…** (🟡 MEDIUM)
- 사유: parsing.md는 컴파일러 프론트엔드(lexing~parsing)와 SSA·Register Allocation까지 있으나, 그 사이의 의미 분석(심볼 테이블·스코프·타입 체크)과 미들엔드 최적화(데이터 흐름 분석, 상수 전파/폴딩, 데드 코드 제거, 루프 최적화, peephole)가 독립 항목 없이 SSA 항목 안에서 한 줄 언급만 된다. Dragon Book·Cooper의 컴파일러 파이프라인 절반(분석·최적화)이 비어 있어 컴파일러 학습 카탈로그로서 불완전하다.
- 권고: 신규 항목 추가 권장(보수적 partial 판정). parsing.md 가 컴파일러 프론트엔드(lexing→parsing→AST→SSA→regalloc)는 충실히 커버하나, 백엔드/미들엔드의 의미 분석 + IR 최적화 패스(data-flow analysis: reaching definitions/liveness/fixpoint, constant folding·propagation, dead-code elimination, loop optimization(LICM/unroll), peephole)는 독립 항목이 없다. SSA 항목(#9)이 이 개념들을 '동기'로 명명만 하고 있으므로, parsing.md 에 신규 항목 "Compiler Optimization Passes / Data-Flow Analysis"…

**OSI / TCP-IP Layering Model (OSI 7계층 ↔ TCP/IP 4계층 참조 모델)** (🟡 MEDIUM)
- 사유: networking.md는 transport(TCP/UDP)부터 application(HTTP/TLS/DNS)까지 패턴을 다루지만, 이들을 위치 짓는 OSI 7계층 / TCP-IP 4계층 참조 모델 자체를 설명하는 항목이 없다. 계층 모델은 네트워크 전 항목의 좌표계로, Kurose-Ross/Tanenbaum 모든 교재 1장의 정전이며 캡슐화·계층 분리 이해의 기반이다.
- 권고: 신규 항목 추가 권고 (단, 우선순위 medium). patterns/networking.md 에 "OSI 7계층 ↔ TCP/IP 4계층 참조 모델" 항목을 신설하고 계층별 매핑(Application/Transport/Network/Link)·encapsulation/decapsulation·각 기존 항목(TCP/UDP, TLS, HTTP, DNS)이 어느 계층에 속하는지 cross-link 하면 카탈로그의 개념적 기반(foundational concept)이 보강됨. index.md 의 networking 별칭 표에도 osi-tcpip-layering / OSI 7계층 / TCP-IP 4계층 별칭 등록 필요. medium 인 이유: 실무 패턴 권고보다는 교과서적 기반 개념이라 advisor 의 코드 진단(…

**IP Routing Protocols (라우팅: Distance-Vector / Link-State / OSPF / BGP, IP forwarding·subnet…** (🟡 MEDIUM)
- 사유: BGP는 CDN anycast 라우팅 맥락에서 한 줄 언급만 되고, distance-vector/link-state/OSPF/BGP 경로 알고리즘과 IP 포워딩·서브넷·CIDR이 독립적으로 다뤄지지 않는다. 네트워크 계층(L3) 라우팅은 인터넷 동작의 핵심이며, 알고리즘 카탈로그에 Dijkstra/Bellman-Ford는 graph.md에 있으나 네트워크 라우팅 프로토콜로의 응용 연결이 빠져 있다.
- 권고: 신규 항목 추가 권고: patterns/networking.md 에 "IP Routing & Forwarding" 항목(Distance-Vector vs Link-State, OSPF/IS-IS(IGP), BGP(EGP/path-vector), IP forwarding·longest-prefix-match, subnet/CIDR/넷마스크) 1건을 13번째 엔트리로 추가하고, patterns/index.md:71 카탈로그 목록 + 별칭 표(ip-routing → IP Routing & Forwarding → IP 라우팅/포워딩)에 등록. 기존 BGP(CDN anycast)·RIP(Bellman-Ford)·longest-prefix(trie) 부수 언급은 신규 항목으로 cross-link. 중요도 medium…

**Reliable Data Transfer / ARQ & Link-Layer Flow Control (Stop-and-Wait / Go-Back-N / Select…** (🟡 MEDIUM)
- 사유: ARQ는 KCP(Reliable UDP) 항목 안에서 '변형' 언급만, flow control은 TCP receive window 한 줄로만 나온다. Stop-and-Wait/Go-Back-N/Selective Repeat 신뢰적 전송 메커니즘과 슬라이딩 윈도우 흐름제어의 원리는 TCP·QUIC·KCP를 모두 떠받치는 정전 기초인데 독립 설명이 없다. (reactive-streams의 backpressure는 애플리케이션 흐름제어로 별개 개념.)
- 권고: 신규 항목 추가 권고(부분 보완): Stop-and-Wait / Go-Back-N / Selective Repeat / sliding-window flow control 의 RDT(reliable data transfer) 분류 자체는 독립 항목으로 부재하므로, patterns/networking.md 에 신규 섹션(예: "Reliable Data Transfer / ARQ & Sliding-Window Flow Control")을 추가해 KCP(섹션11)·TCP Congestion Control(섹션2)·receive-window flow control(섹션1)을 묶는 기초 개념으로 정식화 권고. 동시에 catalog-index.json 에 별칭(ARQ, automatic repeat request, st…

**Amdahl's Law & Gustafson's Law (병렬 성능 법칙: speedup 상한·strong/weak scaling)** (🟡 MEDIUM)
- 사유: Amdahl은 hpc-scientific.md의 OpenMP 항목 안에서 speedup 공식 한 줄로만 등장하고, Gustafson 법칙은 전혀 없다. performance-metrics.md는 Latency Numbers·Big-O·복잡도·percentile 위주이고 병렬 가속 상한 법칙을 독립 항목으로 다루지 않는다. 멀티코어·분산 성능 추론의 정량 기초(Hennessy-Patterson 1장)로 컴퓨터 구조·성능 메트릭 양쪽에서 기대되는 정전이다.
- 권고: 신규 독립 항목 추가 권장. principles/performance-metrics.md 에 "Amdahl's Law & Gustafson's Law (Speedup 상한 / Strong vs Weak Scaling / Efficiency η)" 섹션을 신설(예: 섹션 11)하라 — 이미 hpc-scientific.md:13 이 이 파일을 그 내용의 정식 home 으로 cross-link 하고 있어 그 깨진 링크를 동시에 정합화할 수 있다. 추가 시: Amdahl S=1/((1-p)+p/N) 상한, Gustafson S=N-(1-p)(N-1) weak scaling, Efficiency η=S/P, strong scaling(고정 문제크기) vs weak scaling(고정 코어당 작업량) 정의를 포함하고,…

**CPU Microarchitecture: Pipelining / Branch Prediction / Out-of-Order / SIMD Vectorization…** (🟡 MEDIUM)
- 사유: MESI 캐시 일관성은 os-foundations.md에 정식 항목으로 있으나, 그 외 CPU 마이크로아키텍처 핵심(명령어 파이프라인과 hazard, 분기 예측, 비순차/슈퍼스칼라 실행, SIMD/auto-vectorization)은 embedded·hpc·performance-metrics에 운영/언급 수준으로만 산재하고 응집된 본문 항목이 없다. 성능 튜닝(메모리 지역성·분기 비용·벡터화)의 멘탈 모델로 CSAPP 4-5장·Hennessy-Patterson 3장의 정전이다.
- 권고: 신규 항목 추가 권장. hpc-scientific.md 의 NUMA-aware/Roofline(#6) 섹션 직후에 "CPU Microarchitecture & SIMD Vectorization" 패턴을 신설(파이프라이닝·분기예측·비순차/슈퍼스칼라 실행·SIMD AVX-512/SVE/NEON 벡터화·prefetch·false sharing·data-oriented layout 통합)하고 카탈로그 요약표에 `cpu-microarch-simd` 같은 ID 로 등록. 동시에 별칭 표에 한글명(파이프라이닝/분기예측/비순차실행/벡터화)과 영문 동의어(ILP/superscalar/speculative execution)를 alias 로 등록해 finder 재검색 시 매칭되게 할 것. 단, 우선순위는 medium — 성능…

**Process vs Thread Execution Model (프로세스 vs 스레드: 주소공간 공유·컨텍스트 스위치 비용·kernel/user/green/virt…** (🟡 MEDIUM)
- 사유: concurrency.md는 동시성 패턴(Thread Pool/Actor/Reactor 등)이 풍부하나, 프로세스와 스레드의 본질적 차이(주소공간 공유 여부, PCB/TCB, 컨텍스트 스위치 비용, kernel vs user-level vs green vs virtual thread 모델)를 OS 기초로서 정리한 항목이 없다. context switch는 os-foundations의 Round-Robin에서 비용 변수로만 언급된다. 다만 동시성 응용 패턴이 충분하고 dev-advisor가 앱 개발 어드바이저인 점에서 우선순위 낮음.
- 권고: 신규 항목 추가 권고. 거처는 algorithms/os-foundations.md 가 적합(스케줄링·메모리 인접). 항목명 예: "Process vs Thread Execution Model (프로세스 vs 스레드 실행 모델)" — 주소공간 공유/격리, PCB vs TCB, 컨텍스트 스위치 비용(TLB flush 유무), 1:1/N:1/M:N 스레딩 모델, kernel/user/green/virtual thread(Project Loom)·fiber·coroutine 매핑을 1개 엔트리로 정리. algorithms/index.md 의 OS 기초 행과 alias 표(process-thread-model / 프로세스 스레드 / context switch / green thread / virtual thread)…

**Virtual Memory Mechanism (가상 메모리 메커니즘: Paging / Page Table / TLB / Segmentation / Demand P…** (🟡 MEDIUM)
- 사유: os-foundations.md는 Page Replacement(LRU/Clock/LFU/ARC)는 정식 항목으로 다루지만, 그 상위 메커니즘인 가상→물리 주소 변환(다단계 page table, TLB 캐싱), segmentation, demand paging, copy-on-write(fork/mmap)는 page-replacement 항목 안에서 page table walk 한 줄, mmap 한 줄로만 언급된다. 페이지 교체는 가상 메모리의 한 부분일 뿐이고 주소 변환·TLB·demand paging이 OSTEP 13-22장의 핵심 정전인데 본문 공백이다.
- 권고: 신규 항목 추가 권고: os-foundations.md 에 Memory 카테고리 독립 항목으로 "Virtual Memory / Address Translation Mechanism" 추가 (Paging, Multi-level/Inverted Page Table, TLB + TLB shootdown, Segmentation, Demand Paging, Copy-on-Write fork, page fault handling, working set/thrashing 포함). 인접 항목 page-replacement(#11, 교체 정책)와 slab/buddy(물리 할당)는 별개 주제이므로 흡수 불가. 추가 시 page-replacement·buddy-allocator 와 상호 cross-link 하고, page f…

**Error Detection & Correction Codes (오류 검출·정정: Checksum / CRC / Hamming Code / Parity)** (⚪ LOW)
- 사유: networking에 FEC/Reed-Solomon은 KCP 맥락에서만, signal-processing.md의 'Hamming window'는 DSP 윈도우 함수로 별개 개념이다. CRC(순환 중복 검사)·Hamming ECC·체크섬·패리티 같은 링크/저장 계층 오류 검출·정정 코드가 본문에 없다. 네트워크·스토리지 무결성의 기초이나 dev-advisor 앱 개발 관점에서는 우선순위 낮음.
- 권고: 조치 불필요(보수적 판정) 또는 경량 별칭 등록 권장. 사유: (a) 정정 측면(FEC/Reed-Solomon/parity packet)은 networking.md #11 에 이미 기능적으로 커버되어 완전 부재 아님. (b) CRC 는 c.md 에 동작 코드 예제 존재. (c) Checksum/CRC/Hamming code/Parity bit 를 묶은 "오류 검출·정정 코드 family" 의 독립적·알고리즘 수준 정식 항목은 부재하나, 이는 앱 개발 advisor 범위에서 우선순위 low. 만약 추가한다면 algorithms 트리(예: 신규 error-coding 항목)에 CRC32/Hamming(7,4)/parity bit/checksum 을 정리하고 networking FEC 와 cross-link, 한…

</details>

## 6. 정합성(무결성) 결함

> 카탈로그의 핵심 카운트(.counts.manifest 의 EXPECTED_* 6개 카테고리)는 실측과 100% 일치하여 데이터 무결성은 견고하다: PATTERNS=529(^## N. 헤더), ALGORITHMS=250(ID 매핑 표 행 + 카테고리 표 합), LANGUAGES=75(언어 .md 파일, index/domains 제외), SECURITY=106(13개 파일 numbered headers 97 + privacy-engineering <a id= 9), PRINCIPLES=206(micro 제외 ^## N.), QUALITY=20 모두 정확. 그러나 문서 신뢰도(prose 일관성) 차원에서 2건의 무결성 결함이 존재한다: (1) algorithms/index.md 가 헤더(line 7)에서는 정확한 "총 250개"를 쓰면서 본문 line 45/452 에서 stale 한 "273개"를 2회 사용 — verify-counts.sh 의 stale-token 가드(273 패턴)가 split-quote 로 자기 자신은 회피하지만 실제 본문의 이 2줄은 가드 패턴 '27''3 알고리즘'(공백 포함)과 매칭되지 않아 누락 탐지 실패. (2) catalog-index.json items 배열(1226) vs manifest EXPECTED_TOTAL_WITH_MICRO(1204) 의 22 차이는 데이터 손상이 아니라 정의 불일치 — gen…

- **algorithms/index.md 본문 stale 카운트 '273개' (헤더/정본은 250개) — Stale algorithm count in body prose** — 신규 항목 추가(수정 대상으로 등재) 권장. 이것은 카탈로그 '엔트리 누락' 이 아니라 데이터 무결성 결함이므로 카탈로그 별칭 등록 대상이 아니라 직접 수정 대상임. 조치: claude/codex/antigravity 3개 트리 모두에서 algorithms/index.md:45 와 :452 의 '273개' → '250개' 로 정정(정본 250 과 일치). 추가로 verify-references.sh 에 '헤더 카운트(250) == ID 매핑 행수 == 카테고리 합 == SKILL.md 선언치' 일치 검사를 넣어 재발 방지 권장(현재…
- **verify-counts.sh stale-token 가드가 index.md '273개 알고리즘' prose 를 탐지 못함 (guard regex가 실제 stale 토큰을 놓침)** — 신규 카탈로그 항목 추가 아님 — 이것은 패턴/알고리즘/언어/보안/원칙/품질 도메인 항목이 아니라 verify 스크립트의 실제 버그임. 조치: (A) verify-counts.sh:92 의 stale_pattern 에서 `27''3'' 알고리즘`(공백형)을 실제 prose 형태인 `27''3''개 알고리즘`(또는 `27''3''(개)? *알고리즘`)로 수정해 가드가 실제 stale 토큰을 잡도록 함. (B) 동시에 index.md:45,452 의 `273개 알고리즘` → 정확값 `250개 알고리즘`으로 prose 교정(현재 진짜 d…

## 7. 거짓 누락 — 검증으로 기각된 항목

적대적 grep이 '이미 존재'를 확인하여 추가 불필요로 판정한 항목. 검증 단계가 거짓 양성을 제대로 걸러냈음을 보여준다.

| 항목 | 판정 | 발견 위치/사유 |
|---|---|---|
| **B+ Tree (vs B-Tree) (B플러스 트리)** | data-advisor 에 존재 | data-advisor 에 완전한 독립 항목으로 존재. 1) `data-advisor/references/algorithms/db-indexes.md:25-26` — `<a id="b-plus-tree"></a>` + `## 1. B+Tree Index (B+트리 인덱스)` 독립 섹션.… |
| **LSM-Tree (Log-Structured Merge Tree) (로그 구조 병합 트리)** | data-advisor 에 존재 | data-advisor 에 독립 항목으로 완전히 존재함. (1) data-advisor/references/algorithms/db-storage-engines.md:124-125 — 전용 앵커 `<a id="lsm-tree"></a>` + 헤딩 `## 2. LSM Tree (Log-S… |
| **Pipeline Architecture (파이프라인 아키텍처 스타일)** | 이미 dev-advisor 존재 | Pipe-and-Filter(=파이프라인) 아키텍처 스타일은 dev-advisor 카탈로그에 독립 항목으로 이미 등록됨. - 본문 항목: patterns/integration.md:7 "## 1. Pipes & Filters (파이프 앤 필터)" — 목적/특징/장단점/활용예시/Kotli… |
| **Async Request-Reply (비동기 요청-응답 패턴)** | 이미 dev-advisor 존재 | dev-advisor 에 핵심 개념이 이미 독립 항목으로 존재. (1) patterns/api-design.md 섹션 8 "Long-Running Operation (LRO)" (anchor: 8-long-running-operation, 라인 614-715): 즉시 완료 불가 작업에… |
| **catalog-index.json items=1226 vs manifest EXPECTED_TOTAL_WITH_MICRO=12…** | 이미 dev-advisor 존재 | Δ22 는 버그가 아니라 "category 메타항목 22개" 로 이미 완전히 분해·문서화되어 있음. (1) scripts/state/catalog/meta.json:50-58 — principles 도메인이 `actual_count: 206`(실제 entry), `lookup_count… |

## 8. 권고 로드맵

| 단계 | 작업 | 노력 |
|---|---|---|
| **P0 (완료)** | 무결성 3건: stale '273'→'250', verify 가드 하드닝, dangling 링크 정정 | 소 |
| **P1** | 알고리즘 HIGH: Quickselect · Binary Heap · Hungarian · ECC · Diffie-Hellman · 트리계열 ML | 중 |
| **P2** | 아키텍처 HIGH: SEI 평가군 신설 + 분산 정전(Fallacies/Byzantine/Amdahl·USL) | 중 |
| **P3** | CS 순수이론(복잡도/계산가능성/네트워크 계층/가상메모리/CPU 구조) + 암호 MEDIUM(SHA-3/BLAKE/ChaCha/KDF) | 대 |

---

### 부록: 통계

- 중요도 분포: 🟠 HIGH 9건, 🟡 MEDIUM 46건, ⚪ LOW 16건
- 축 분포: 알고리즘 34건, 아키텍처 18건, CS 기초 17건, 정합성 2건
- 판정 분포: 완전 부재 40건, 부분 커버(포인터/언급만) 31건

*생성: dev-advisor-gap-audit 멀티에이전트 워크플로우 (Run ID wf_973660be-3ba) → 본 보고서.*

---

## 부록: 구현 완료 상태 (2026-05-30, 동일 세션)

본 감사 직후 **누락 71건 전수 반영**을 실행했다. 결과:

| Wave | 내용 | 카운트 변화 |
|---|---|---|
| **P0** | 무결성 3건 (stale "273" 정정, verify 가드 하드닝, logistics→ml dangling 해소) | — |
| **Wave 2** | 알고리즘 HIGH 6 (Quickselect·Binary Heap·Hungarian·ECC·Diffie-Hellman·Tree-based ML) | 알고리즘 250→256 |
| **Wave 3a** | 알고리즘 36 + 신규 `complexity` 카테고리 | 알고리즘 256→292 (29→30 카테고리) |
| **Wave 3b** | 패턴 14 (Microkernel·Space-Based·Broker·Valet Key·Deployment Stamps·Gateway Agg·Gatekeeper·Messaging Gateway·Steady State/Fail Fast·OSI/TCP-IP·IP Routing·ARQ·CPU Microarch·Harvest&Yield/AKF) | 패턴 529→543 |
| **Wave 3c** | 원칙 7 (Amdahl/USL·Lambda Calculus·Fallacies·E2E Argument) + 신규 `architecture-evaluation` 카테고리(ATAM/SAAM/CBAM·품질속성 시나리오·아키텍처 전술) | 원칙 206→211, 미시 18→20 |
| **부가** | antigravity 트리 노후화(stale 카운트 + research 모드 미등록) 정정 | — |

**최종 카탈로그**: 543 패턴 / 292 알고리즘 / 75 언어 / 106 보안 / 211 원칙 / 20 품질 + 20 미시 = **1,267 항목** (이전 1,204).

**검증**: claude·codex·antigravity 3트리 모두 `verify-all.sh` 263/263 통과, `catalog-index.json` 1290/1290 anchors valid, `generate --check` clean.
