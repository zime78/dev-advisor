# 알고리즘 레퍼런스

## 개요

소프트웨어 개발에서 자주 사용되는 알고리즘 모음입니다.

## 알고리즘 카테고리 (총 292개, 30 카테고리)

| 카테고리 | 알고리즘 수 | 파일 |
|---------|-----------|------|
| [정렬](sorting.md) | 17개 | Bubble, Selection, Insertion, Merge, Quick, Heap, Counting, Radix, Bucket, Shell, Tim, Intro, Tree, External Merge, Pancake, Cycle, Quickselect |
| [탐색](searching.md) | 13개 | Linear, Binary, Jump, Interpolation, Exponential, Fibonacci, Ternary, Hash, Two Pointers, Sliding Window, Sparse Table, Mo's, Parallel Binary Search |
| [그래프](graph.md) | 20개 | BFS, DFS, Dijkstra, Bellman-Ford, Floyd-Warshall, A*, Prim, Kruskal, Topological, Tarjan SCC, Kosaraju, Johnson, LCA, Articulation, Bridges, 2-SAT, Eulerian, Stoer-Wagner, HLD, Centroid Decomposition |
| [동적 프로그래밍](dynamic-programming.md) | 13개 | Fibonacci, LCS, LIS, Knapsack, Edit Distance, Matrix Chain, Coin Change, Rod Cutting, Bitmask, Tree, Digit, SOS, DP Optimizations |
| [분할 정복](divide-conquer.md) | 5개 | Binary Search, Merge Sort, Strassen, Closest Pair, Karatsuba |
| [탐욕](greedy.md) | 5개 | Activity Selection, Huffman, Fractional Knapsack, Job Sequencing, Optimal Merge |
| [백트래킹](backtracking.md) | 5개 | N-Queens, Sudoku, Graph Coloring, Hamiltonian, Subset Sum |
| [문자열](string.md) | 11개 | KMP, Rabin-Karp, Boyer-Moore, Z, Suffix Array, Trie, Aho-Corasick, Manacher, Suffix Automaton, Suffix Tree, Lyndon (Duval) |
| [수학](math.md) | 16개 | GCD, Sieve, Fast Exp, Modular, CRT, FFT, Simpson, Newton-Raphson, Factorization, Miller-Rabin, Extended Euclidean, Lucas, Pollard's Rho, Linear Sieve, Gaussian Elimination, DCT |
| [자료구조](data-structures.md) | 17개 | Union-Find, Segment Tree, Fenwick (BIT), AVL, Red-Black, B-Tree, Skip List, LRU Cache, Bloom Filter, Binary Heap, Persistent DS, Treap/Splay, Hash Collision, Rope/Gap/Piece, Advanced Heaps, Order-Statistics, van Emde Boas |
| [계산 기하](geometry.md) | 7개 | CCW, Graham Scan, Andrew's Monotone Chain, Segment Intersection, Sweep Line, Rotating Calipers, Point-in-Polygon |
| [네트워크 플로우](flow.md) | 4개 | Ford-Fulkerson, Edmonds-Karp, Dinic, Min-Cost Max-Flow |
| [매칭](matching.md) | 4개 | Bipartite Matching, Hopcroft-Karp, Stable Marriage, Hungarian |
| [암호/해시](crypto.md) | 12개 | SHA-256, HMAC, RSA, AES, Bcrypt, Argon2, ECC, Diffie-Hellman, ChaCha20-Poly1305, SHA-3, BLAKE2/3, scrypt/PBKDF2 |
| [압축](compression.md) | 5개 | RLE, LZ77, LZW, Arithmetic Coding, BWT |
| [게임/AI](game-ai.md) | 5개 | Minimax, Alpha-Beta, MCTS, Genetic, Simulated Annealing |
| [머신러닝](ml.md) | 15개 | K-Means, KNN, Linear/Logistic Regression, Gradient Descent, Naive Bayes, Transformer, Attention, HNSW, Quantization, Speculative Decoding, PageRank, Node2Vec, Decision Tree/RF/GBM, PCA/SVD |
| [확률/스트림](probabilistic.md) | 4개 | Fisher-Yates, Reservoir Sampling, Count-Min Sketch, HyperLogLog |
| [분산 합의](consensus.md) | 5개 | 2PC, Paxos, Raft, Byzantine/PBFT, Leader Election |
| [분산 알고리즘](distributed.md) | 14개 | Lamport Clock, Vector Clock, Hybrid Logical Clock, Gossip, SWIM, Anti-Entropy, CRDT(G/PN/OR/LWW), Consistent Hashing, Quorum, Chandy-Lamport, Phi Accrual |
| [동시성/락 알고리즘](concurrent.md) | 12개 | CAS, LL-SC, RCU, MVCC, Hazard Pointer, Lock-Free Queue, Work-Stealing, Seqlock, Memory Barriers, ABA Problem, 2PL+Deadlock, Queue Spinlocks |
| [파서/컴파일러](parsing.md) | 12개 | Lexing, LL(k), LR(1), LALR, Earley, Pratt, PEG/Packrat, AST Traversal, SSA, Register Allocation, Compiler Optimization, Formal Language Theory |
| [공간 인덱싱](spatial.md) | 8개 | R-Tree, R*-Tree, QuadTree, KD-Tree, Geohash, H3, S2, BVH |
| [검색·랭킹](search-systems.md) | 8개 | Inverted Index, TF-IDF, BM25, Vector Search, Hybrid Search, Faceted, Autocomplete, Learning to Rank |
| [부하 분산](load-balancing.md) | 8개 | Round Robin, WRR, Least Connections, Least Response Time, P2C, Consistent Hashing (LB), Maglev, EWMA |
| [OS 기초](os-foundations.md) | 15개 | Mark-Sweep GC, Generational GC, G1 GC, ZGC/Shenandoah, RR Scheduling, CFS, MLFQ, Slab, Buddy, epoll/kqueue/io_uring, Page Replacement, MESI, Disk Scheduling, Process vs Thread, Virtual Memory |
| [이미지 처리](image-processing.md) | 8개 | Convolution, Edge Detection, Hough, Morphology, Histogram Equalization, Segmentation, Feature Detection, Optical Flow |
| [코덱·미디어](codecs.md) | 9개 | JPEG, PNG, WebP/AVIF/HEIC, H.264, H.265/H.266/AV1, MP3/AAC, Opus, Entropy Coding, Error Correcting Codes |
| [신호 처리](signal-processing.md) | 9개 | FIR Filter, IIR Filter, STFT, Wavelet, Resampling, Kalman, EKF/UKF, Auto/Cross-correlation, Goertzel |
| [계산 복잡도·분석](complexity.md) | 6개 | Complexity Classes, Computability, Amortized Analysis, Master Theorem, Approximation, Randomized |

---

## 알고리즘 ID 매핑

전체 292개 알고리즘의 ID → 파일 매핑.

| ID | 영문명 | 한글명 | 카테고리 | 링크 |
|----|--------|--------|---------|------|
| bubble-sort | Bubble Sort | 버블 정렬 | 정렬 | [sorting.md#bubble-sort](sorting.md#bubble-sort) |
| selection-sort | Selection Sort | 선택 정렬 | 정렬 | [sorting.md#selection-sort](sorting.md#selection-sort) |
| insertion-sort | Insertion Sort | 삽입 정렬 | 정렬 | [sorting.md#insertion-sort](sorting.md#insertion-sort) |
| merge-sort | Merge Sort | 병합 정렬 | 정렬 | [sorting.md#merge-sort](sorting.md#merge-sort) |
| quick-sort | Quick Sort | 퀵 정렬 | 정렬 | [sorting.md#quick-sort](sorting.md#quick-sort) |
| heap-sort | Heap Sort | 힙 정렬 | 정렬 | [sorting.md#heap-sort](sorting.md#heap-sort) |
| counting-sort | Counting Sort | 계수 정렬 | 정렬 | [sorting.md#counting-sort](sorting.md#counting-sort) |
| radix-sort | Radix Sort | 기수 정렬 | 정렬 | [sorting.md#radix-sort](sorting.md#radix-sort) |
| bucket-sort | Bucket Sort | 버킷 정렬 | 정렬 | [sorting.md#bucket-sort](sorting.md#bucket-sort) |
| shell-sort | Shell Sort | 셸 정렬 | 정렬 | [sorting.md#shell-sort](sorting.md#shell-sort) |
| tim-sort | Tim Sort | 팀 정렬 | 정렬 | [sorting.md#tim-sort](sorting.md#tim-sort) |
| intro-sort | Intro Sort | 인트로 정렬 | 정렬 | [sorting.md#intro-sort](sorting.md#intro-sort) |
| tree-sort | Tree Sort | 트리 정렬 | 정렬 | [sorting.md#tree-sort](sorting.md#tree-sort) |
| external-merge-sort | External Merge Sort | 외부 병합 정렬 | 정렬 | [sorting.md#external-merge-sort](sorting.md#external-merge-sort) |
| pancake-sort | Pancake Sort | 팬케이크 정렬 | 정렬 | [sorting.md#pancake-sort](sorting.md#pancake-sort) |
| cycle-sort | Cycle Sort | 사이클 정렬 | 정렬 | [sorting.md#cycle-sort](sorting.md#cycle-sort) |
| quickselect | Quickselect | 퀵 선택 (k번째 순서통계량, Median of Medians) | 정렬 | [sorting.md#quickselect](sorting.md#quickselect) |
| linear-search | Linear Search | 선형 탐색 | 탐색 | [searching.md#linear-search](searching.md#linear-search) |
| binary-search | Binary Search | 이진 탐색 | 탐색 | [searching.md#binary-search](searching.md#binary-search) |
| jump-search | Jump Search | 점프 탐색 | 탐색 | [searching.md#jump-search](searching.md#jump-search) |
| interpolation-search | Interpolation Search | 보간 탐색 | 탐색 | [searching.md#interpolation-search](searching.md#interpolation-search) |
| exponential-search | Exponential Search | 지수 탐색 | 탐색 | [searching.md#exponential-search](searching.md#exponential-search) |
| fibonacci-search | Fibonacci Search | 피보나치 탐색 | 탐색 | [searching.md#fibonacci-search](searching.md#fibonacci-search) |
| ternary-search | Ternary Search | 삼진 탐색 | 탐색 | [searching.md#ternary-search](searching.md#ternary-search) |
| hash-table-search | Hash Table Search | 해시 테이블 탐색 | 탐색 | [searching.md#hash-table-search](searching.md#hash-table-search) |
| two-pointers | Two Pointers | 투 포인터 | 탐색 | [searching.md#two-pointers](searching.md#two-pointers) |
| sliding-window | Sliding Window | 슬라이딩 윈도우 | 탐색 | [searching.md#sliding-window](searching.md#sliding-window) |
| binary-lifting | Binary Lifting / Sparse Table | 이진 점프 / 희소 테이블 | 탐색 | [searching.md#binary-lifting](searching.md#binary-lifting) |
| mo-algorithm | Mo's Algorithm | 모 알고리즘 | 탐색 | [searching.md#mo-algorithm](searching.md#mo-algorithm) |
| parallel-binary-search | Parallel Binary Search | 병렬 이진 탐색 | 탐색 | [searching.md#parallel-binary-search](searching.md#parallel-binary-search) |
| bfs | BFS (Breadth-First Search) | 너비 우선 탐색 | 그래프 | [graph.md#bfs](graph.md#bfs) |
| dfs | DFS (Depth-First Search) | 깊이 우선 탐색 | 그래프 | [graph.md#dfs](graph.md#dfs) |
| dijkstra | Dijkstra | 다익스트라 | 그래프 | [graph.md#dijkstra](graph.md#dijkstra) |
| bellman-ford | Bellman-Ford | 벨만-포드 | 그래프 | [graph.md#bellman-ford](graph.md#bellman-ford) |
| floyd-warshall | Floyd-Warshall | 플로이드-워셜 | 그래프 | [graph.md#floyd-warshall](graph.md#floyd-warshall) |
| a-star | A* | 에이스타 | 그래프 | [graph.md#a-star](graph.md#a-star) |
| prim | Prim | 프림 | 그래프 | [graph.md#prim](graph.md#prim) |
| kruskal | Kruskal | 크루스칼 | 그래프 | [graph.md#kruskal](graph.md#kruskal) |
| topological-sort | Topological Sort | 위상 정렬 | 그래프 | [graph.md#topological-sort](graph.md#topological-sort) |
| tarjan-scc | Tarjan's SCC | 타잔 강결합 요소 | 그래프 | [graph.md#tarjan-scc](graph.md#tarjan-scc) |
| kosaraju | Kosaraju | 코사라주 | 그래프 | [graph.md#kosaraju](graph.md#kosaraju) |
| johnson | Johnson | 존슨 | 그래프 | [graph.md#johnson](graph.md#johnson) |
| lca | LCA (Lowest Common Ancestor) | 최소 공통 조상 | 그래프 | [graph.md#lca](graph.md#lca) |
| articulation-points | Articulation Points | 단절점 | 그래프 | [graph.md#articulation-points](graph.md#articulation-points) |
| bridges | Bridges | 단절선 | 그래프 | [graph.md#bridges](graph.md#bridges) |
| 2-sat | 2-SAT | 2-Satisfiability | 그래프 | [graph.md#2-sat](graph.md#2-sat) |
| eulerian-path | Eulerian Path / Circuit | 오일러 경로/회로 (Hierholzer) | 그래프 | [graph.md#eulerian-path](graph.md#eulerian-path) |
| stoer-wagner | Min Cut — Stoer-Wagner | 전역 최소 컷 | 그래프 | [graph.md#stoer-wagner](graph.md#stoer-wagner) |
| heavy-light-decomposition | Heavy-Light Decomposition (HLD) | 헤비-라이트 분해 | 그래프 | [graph.md#heavy-light-decomposition](graph.md#heavy-light-decomposition) |
| centroid-decomposition | Centroid Decomposition | 센트로이드 분할 | 그래프 | [graph.md#centroid-decomposition](graph.md#centroid-decomposition) |
| fibonacci | Fibonacci | 피보나치 | 동적 프로그래밍 | [dynamic-programming.md#fibonacci](dynamic-programming.md#fibonacci) |
| lcs | LCS (Longest Common Subsequence) | 최장 공통 부분 수열 | 동적 프로그래밍 | [dynamic-programming.md#lcs](dynamic-programming.md#lcs) |
| lis | LIS (Longest Increasing Subsequence) | 최장 증가 부분 수열 | 동적 프로그래밍 | [dynamic-programming.md#lis](dynamic-programming.md#lis) |
| knapsack | Knapsack | 배낭 문제 | 동적 프로그래밍 | [dynamic-programming.md#knapsack](dynamic-programming.md#knapsack) |
| edit-distance | Edit Distance | 편집 거리 (Levenshtein Distance) | 동적 프로그래밍 | [dynamic-programming.md#edit-distance](dynamic-programming.md#edit-distance) |
| matrix-chain-multiplication | Matrix Chain Multiplication | 행렬 체인 곱셈 | 동적 프로그래밍 | [dynamic-programming.md#matrix-chain-multiplication](dynamic-programming.md#matrix-chain-multiplication) |
| coin-change | Coin Change | 동전 교환 | 동적 프로그래밍 | [dynamic-programming.md#coin-change](dynamic-programming.md#coin-change) |
| rod-cutting | Rod Cutting | 막대 자르기 | 동적 프로그래밍 | [dynamic-programming.md#rod-cutting](dynamic-programming.md#rod-cutting) |
| bitmask-dp | Bitmask DP | 비트마스크 DP | 동적 프로그래밍 | [dynamic-programming.md#bitmask-dp](dynamic-programming.md#bitmask-dp) |
| tree-dp | Tree DP | 트리 DP | 동적 프로그래밍 | [dynamic-programming.md#tree-dp](dynamic-programming.md#tree-dp) |
| digit-dp | Digit DP | 자릿수 DP | 동적 프로그래밍 | [dynamic-programming.md#digit-dp](dynamic-programming.md#digit-dp) |
| sos-dp | SOS DP (Sum over Subsets) | 부분집합 합 | 동적 프로그래밍 | [dynamic-programming.md#sos-dp](dynamic-programming.md#sos-dp) |
| dp-optimizations | DP Optimizations (Convex Hull Trick / Knuth / D&C DP) | DP 최적화 기법 | 동적 프로그래밍 | [dynamic-programming.md#dp-optimizations](dynamic-programming.md#dp-optimizations) |
| binary-search-dc | Binary Search | 이진 탐색 | 분할 정복 | [divide-conquer.md#binary-search-dc](divide-conquer.md#binary-search-dc) |
| merge-sort-dc | Merge Sort | 병합 정렬 | 분할 정복 | [divide-conquer.md#merge-sort-dc](divide-conquer.md#merge-sort-dc) |
| strassen | Strassen's Matrix Multiplication | 스트라센 행렬 곱셈 | 분할 정복 | [divide-conquer.md#strassen](divide-conquer.md#strassen) |
| closest-pair | Closest Pair of Points | 최근접 점 쌍 | 분할 정복 | [divide-conquer.md#closest-pair](divide-conquer.md#closest-pair) |
| karatsuba | Karatsuba Multiplication | 카라츠바 곱셈 | 분할 정복 | [divide-conquer.md#karatsuba](divide-conquer.md#karatsuba) |
| activity-selection | Activity Selection | 활동 선택 | 탐욕 | [greedy.md#activity-selection](greedy.md#activity-selection) |
| huffman | Huffman Coding | 허프만 코딩 | 탐욕 | [greedy.md#huffman](greedy.md#huffman) |
| fractional-knapsack | Fractional Knapsack | 분할 배낭 | 탐욕 | [greedy.md#fractional-knapsack](greedy.md#fractional-knapsack) |
| job-sequencing | Job Sequencing with Deadlines | 작업 순서화 | 탐욕 | [greedy.md#job-sequencing](greedy.md#job-sequencing) |
| optimal-merge-pattern | Optimal Merge Pattern | 최적 병합 패턴 | 탐욕 | [greedy.md#optimal-merge-pattern](greedy.md#optimal-merge-pattern) |
| n-queens | N-Queens | N-퀸 | 백트래킹 | [backtracking.md#n-queens](backtracking.md#n-queens) |
| sudoku-solver | Sudoku Solver | 스도쿠 풀이 | 백트래킹 | [backtracking.md#sudoku-solver](backtracking.md#sudoku-solver) |
| graph-coloring | Graph Coloring | 그래프 색칠 | 백트래킹 | [backtracking.md#graph-coloring](backtracking.md#graph-coloring) |
| hamiltonian-cycle | Hamiltonian Cycle | 해밀턴 순환 | 백트래킹 | [backtracking.md#hamiltonian-cycle](backtracking.md#hamiltonian-cycle) |
| subset-sum | Subset Sum | 부분집합 합 | 백트래킹 | [backtracking.md#subset-sum](backtracking.md#subset-sum) |
| kmp | KMP (Knuth-Morris-Pratt) | KMP 문자열 매칭 | 문자열 | [string.md#kmp](string.md#kmp) |
| rabin-karp | Rabin-Karp | 라빈-카프 | 문자열 | [string.md#rabin-karp](string.md#rabin-karp) |
| boyer-moore | Boyer-Moore | 보이어-무어 | 문자열 | [string.md#boyer-moore](string.md#boyer-moore) |
| z-algorithm | Z Algorithm | Z 알고리즘 | 문자열 | [string.md#z-algorithm](string.md#z-algorithm) |
| suffix-array | Suffix Array | 접미사 배열 | 문자열 | [string.md#suffix-array](string.md#suffix-array) |
| trie | Trie | 트라이 | 문자열 | [string.md#trie](string.md#trie) |
| aho-corasick | Aho-Corasick | 아호-코라식 | 문자열 | [string.md#aho-corasick](string.md#aho-corasick) |
| manacher | Manacher's Algorithm | 마나허 (가장 긴 회문) | 문자열 | [string.md#manacher](string.md#manacher) |
| suffix-automaton | Suffix Automaton | 접미사 자동자 | 문자열 | [string.md#suffix-automaton](string.md#suffix-automaton) |
| suffix-tree | Suffix Tree | 접미사 트리 (Ukkonen) | 문자열 | [string.md#suffix-tree](string.md#suffix-tree) |
| lyndon-decomposition | Lyndon Decomposition (Duval) | 린든 분해 | 문자열 | [string.md#lyndon-decomposition](string.md#lyndon-decomposition) |
| euclidean-gcd | Euclidean GCD | 유클리드 최대공약수 | 수학 | [math.md#euclidean-gcd](math.md#euclidean-gcd) |
| sieve-of-eratosthenes | Sieve of Eratosthenes | 에라토스테네스의 체 | 수학 | [math.md#sieve-of-eratosthenes](math.md#sieve-of-eratosthenes) |
| fast-exponentiation | Fast Exponentiation | 빠른 거듭제곱 | 수학 | [math.md#fast-exponentiation](math.md#fast-exponentiation) |
| modular-arithmetic | Modular Arithmetic | 모듈러 연산 | 수학 | [math.md#modular-arithmetic](math.md#modular-arithmetic) |
| chinese-remainder-theorem | Chinese Remainder Theorem | 중국인의 나머지 정리 | 수학 | [math.md#chinese-remainder-theorem](math.md#chinese-remainder-theorem) |
| fast-fourier-transform | Fast Fourier Transform | 고속 푸리에 변환 | 수학 | [math.md#fast-fourier-transform](math.md#fast-fourier-transform) |
| simpson-rule | Simpson's Rule | 심슨 적분법 | 수학 | [math.md#simpson-rule](math.md#simpson-rule) |
| newton-raphson | Newton-Raphson | 뉴턴-랩슨 | 수학 | [math.md#newton-raphson](math.md#newton-raphson) |
| prime-factorization | Prime Factorization | 소인수분해 | 수학 | [math.md#prime-factorization](math.md#prime-factorization) |
| miller-rabin | Miller-Rabin Primality Test | 밀러-라빈 소수 판정 | 수학 | [math.md#miller-rabin](math.md#miller-rabin) |
| extended-euclidean | Extended Euclidean | 확장 유클리드 | 수학 | [math.md#extended-euclidean](math.md#extended-euclidean) |
| lucas-theorem | Lucas Theorem | 뤼카 정리 | 수학 | [math.md#lucas-theorem](math.md#lucas-theorem) |
| pollard-rho | Pollard's Rho | 폴라드 로 인수분해 | 수학 | [math.md#pollard-rho](math.md#pollard-rho) |
| linear-sieve | Linear Sieve | 선형 소수 체 | 수학 | [math.md#linear-sieve](math.md#linear-sieve) |
| gaussian-elimination | Gaussian Elimination / Gauss-Jordan | 가우스 소거법 | 수학 | [math.md#gaussian-elimination](math.md#gaussian-elimination) |
| dct | Discrete Cosine Transform (DCT) | 이산 코사인 변환 | 수학 | [math.md#dct](math.md#dct) |
| union-find | Union-Find (Disjoint Set) | 분리 집합 | 자료구조 | [data-structures.md#union-find](data-structures.md#union-find) |
| segment-tree | Segment Tree | 세그먼트 트리 | 자료구조 | [data-structures.md#segment-tree](data-structures.md#segment-tree) |
| fenwick-tree | Fenwick Tree (Binary Indexed Tree, BIT) | 펜윅 트리 | 자료구조 | [data-structures.md#fenwick-tree](data-structures.md#fenwick-tree) |
| avl-tree | AVL Tree | AVL 트리 | 자료구조 | [data-structures.md#avl-tree](data-structures.md#avl-tree) |
| red-black-tree | Red-Black Tree | 레드-블랙 트리 | 자료구조 | [data-structures.md#red-black-tree](data-structures.md#red-black-tree) |
| b-tree | B-Tree | B-트리 | 자료구조 | [data-structures.md#b-tree](data-structures.md#b-tree) |
| skip-list | Skip List | 스킵 리스트 | 자료구조 | [data-structures.md#skip-list](data-structures.md#skip-list) |
| lru | LRU Cache | LRU 캐시 | 자료구조 | [data-structures.md#lru](data-structures.md#lru) |
| bloom-filter | Bloom Filter | 블룸 필터 | 자료구조 | [data-structures.md#bloom-filter](data-structures.md#bloom-filter) |
| binary-heap | Binary Heap / Priority Queue | 이진 힙 / 우선순위 큐 | 자료구조 | [data-structures.md#binary-heap](data-structures.md#binary-heap) |
| persistent-data-structures | Persistent Data Structures (Persistent Segment Tree) | 영속 자료구조 | 자료구조 | [data-structures.md#persistent-data-structures](data-structures.md#persistent-data-structures) |
| treap-splay | Treap / Splay Tree | 트립 / 스플레이 트리 | 자료구조 | [data-structures.md#treap-splay](data-structures.md#treap-splay) |
| hash-collision-resolution | Hash Table Collision Resolution | 해시 테이블 충돌 처리 | 자료구조 | [data-structures.md#hash-collision-resolution](data-structures.md#hash-collision-resolution) |
| rope-gap-buffer | Rope / Gap Buffer / Piece Table | 로프 / 갭 버퍼 / 피스 테이블 | 자료구조 | [data-structures.md#rope-gap-buffer](data-structures.md#rope-gap-buffer) |
| advanced-heaps | Advanced Heaps (Fibonacci / Binomial / Pairing) | 고급 힙 | 자료구조 | [data-structures.md#advanced-heaps](data-structures.md#advanced-heaps) |
| order-statistics-tree | Order-Statistics Tree / Interval Tree | 순위 통계 트리 / 구간 트리 | 자료구조 | [data-structures.md#order-statistics-tree](data-structures.md#order-statistics-tree) |
| van-emde-boas | van Emde Boas Tree / y-fast Trie | 반 엠데 보아스 트리 | 자료구조 | [data-structures.md#van-emde-boas](data-structures.md#van-emde-boas) |
| ccw | CCW (Counter-Clockwise) | 외적 방향 판정 | 계산 기하 | [geometry.md#ccw](geometry.md#ccw) |
| graham-scan | Convex Hull — Graham Scan | 그레이엄 스캔 | 계산 기하 | [geometry.md#graham-scan](geometry.md#graham-scan) |
| andrew-monotone-chain | Convex Hull — Andrew's Monotone Chain | 앤드류 단조 체인 | 계산 기하 | [geometry.md#andrew-monotone-chain](geometry.md#andrew-monotone-chain) |
| line-segment-intersection | Line Segment Intersection | 선분 교차 판정 | 계산 기하 | [geometry.md#line-segment-intersection](geometry.md#line-segment-intersection) |
| sweep-line | Sweep Line | 스위프 라인 (구간 합집합 길이) | 계산 기하 | [geometry.md#sweep-line](geometry.md#sweep-line) |
| rotating-calipers | Rotating Calipers | 회전하는 캘리퍼스 | 계산 기하 | [geometry.md#rotating-calipers](geometry.md#rotating-calipers) |
| point-in-polygon | Point-in-Polygon | 다각형 내부 판정 (Ray Casting) | 계산 기하 | [geometry.md#point-in-polygon](geometry.md#point-in-polygon) |
| ford-fulkerson | Ford-Fulkerson | 포드-풀커슨 | 네트워크 플로우 | [flow.md#ford-fulkerson](flow.md#ford-fulkerson) |
| edmonds-karp | Edmonds-Karp | 에드몬즈-카프 | 네트워크 플로우 | [flow.md#edmonds-karp](flow.md#edmonds-karp) |
| dinic | Dinic | 디닉 | 네트워크 플로우 | [flow.md#dinic](flow.md#dinic) |
| mcmf | Min-Cost Max-Flow | 최소 비용 최대 유량 | 네트워크 플로우 | [flow.md#mcmf](flow.md#mcmf) |
| bipartite-matching | Bipartite Matching | 이분 매칭 (Augmenting Path DFS) | 매칭 | [matching.md#bipartite-matching](matching.md#bipartite-matching) |
| hopcroft-karp | Hopcroft-Karp | 홉크로프트-카프 | 매칭 | [matching.md#hopcroft-karp](matching.md#hopcroft-karp) |
| stable-marriage | Stable Marriage (Gale-Shapley) | 안정 매칭 | 매칭 | [matching.md#stable-marriage](matching.md#stable-marriage) |
| hungarian | Hungarian (Kuhn-Munkres) | 헝가리안 할당 (최소 비용 할당) | 매칭 | [matching.md#hungarian](matching.md#hungarian) |
| sha-256 | SHA-256 | Secure Hash Algorithm 256-bit | 암호/해시 | [crypto.md#sha-256](crypto.md#sha-256) |
| hmac | HMAC | Hash-based Message Authentication Code | 암호/해시 | [crypto.md#hmac](crypto.md#hmac) |
| rsa | RSA | Rivest-Shamir-Adleman | 암호/해시 | [crypto.md#rsa](crypto.md#rsa) |
| aes | AES | Advanced Encryption Standard | 암호/해시 | [crypto.md#aes](crypto.md#aes) |
| bcrypt | Bcrypt | Blowfish-based password hashing | 암호/해시 | [crypto.md#bcrypt](crypto.md#bcrypt) |
| argon2 | Argon2 | 메모리 하드 비밀번호 해시 | 암호/해시 | [crypto.md#argon2](crypto.md#argon2) |
| ecc | ECC (ECDSA / Ed25519 / ECDH) | 타원곡선 암호 (서명·키교환) | 암호/해시 | [crypto.md#ecc](crypto.md#ecc) |
| diffie-hellman | Diffie-Hellman | 디피-헬먼 키 교환 | 암호/해시 | [crypto.md#diffie-hellman](crypto.md#diffie-hellman) |
| chacha20-poly1305 | ChaCha20-Poly1305 | 스트림 AEAD | 암호/해시 | [crypto.md#chacha20-poly1305](crypto.md#chacha20-poly1305) |
| sha-3 | SHA-3 / Keccak | SHA-3 스펀지 해시 | 암호/해시 | [crypto.md#sha-3](crypto.md#sha-3) |
| blake2-blake3 | BLAKE2 / BLAKE3 | 고속 암호 해시 | 암호/해시 | [crypto.md#blake2-blake3](crypto.md#blake2-blake3) |
| scrypt-pbkdf2 | scrypt / PBKDF2 | 키 유도 함수 (KDF) | 암호/해시 | [crypto.md#scrypt-pbkdf2](crypto.md#scrypt-pbkdf2) |
| rle | Run-Length Encoding (RLE) | 런 길이 부호화 | 압축 | [compression.md#rle](compression.md#rle) |
| lz77 | LZ77 (Lempel-Ziv 1977) | 슬라이딩 윈도우 압축 | 압축 | [compression.md#lz77](compression.md#lz77) |
| lzw | LZ78 / LZW | 사전 기반 압축 | 압축 | [compression.md#lzw](compression.md#lzw) |
| arithmetic-coding | Arithmetic Coding | 산술 부호화 | 압축 | [compression.md#arithmetic-coding](compression.md#arithmetic-coding) |
| bwt | Burrows-Wheeler Transform | BWT 변환 | 압축 | [compression.md#bwt](compression.md#bwt) |
| minimax | Minimax | 미니맥스 | 게임/AI | [game-ai.md#minimax](game-ai.md#minimax) |
| alpha-beta | Alpha-Beta Pruning | 알파-베타 가지치기 | 게임/AI | [game-ai.md#alpha-beta](game-ai.md#alpha-beta) |
| mcts | Monte Carlo Tree Search | 몬테카를로 트리 탐색 | 게임/AI | [game-ai.md#mcts](game-ai.md#mcts) |
| genetic-algorithm | Genetic Algorithm | 유전 알고리즘 | 게임/AI | [game-ai.md#genetic-algorithm](game-ai.md#genetic-algorithm) |
| simulated-annealing | Simulated Annealing | 시뮬레이티드 어닐링 | 게임/AI | [game-ai.md#simulated-annealing](game-ai.md#simulated-annealing) |
| k-means | K-Means Clustering | K-평균 군집화 | 머신러닝 기초 | [ml.md#k-means](ml.md#k-means) |
| k-nearest-neighbors | K-Nearest Neighbors (KNN) | K-최근접 이웃 | 머신러닝 기초 | [ml.md#k-nearest-neighbors](ml.md#k-nearest-neighbors) |
| linear-regression | Linear Regression | 선형 회귀 | 머신러닝 기초 | [ml.md#linear-regression](ml.md#linear-regression) |
| logistic-regression | Logistic Regression | 로지스틱 회귀 | 머신러닝 기초 | [ml.md#logistic-regression](ml.md#logistic-regression) |
| gradient-descent | Gradient Descent | 경사 하강법 | 머신러닝 기초 | [ml.md#gradient-descent](ml.md#gradient-descent) |
| naive-bayes | Naive Bayes | 나이브 베이즈 | 머신러닝 | [ml.md#naive-bayes](ml.md#naive-bayes) |
| transformer | Transformer | 트랜스포머 | 머신러닝 | [ml.md#transformer](ml.md#transformer) |
| attention | Attention Mechanism | 어텐션 메커니즘 | 머신러닝 | [ml.md#attention](ml.md#attention) |
| hnsw | HNSW (Hierarchical Navigable Small World) | 계층적 NSW 벡터 인덱스 | 머신러닝 | [ml.md#hnsw](ml.md#hnsw) |
| quantization | Quantization (INT8/INT4) | 양자화 | 머신러닝 | [ml.md#quantization](ml.md#quantization) |
| speculative-decoding | Speculative Decoding | 추측 디코딩 | 머신러닝 | [ml.md#speculative-decoding](ml.md#speculative-decoding) |
| pagerank | PageRank | 페이지랭크 | 머신러닝 | [ml.md#pagerank](ml.md#pagerank) |
| node2vec | Node2Vec | 노드투벡 | 머신러닝 | [ml.md#node2vec](ml.md#node2vec) |
| decision-tree | Decision Tree / Random Forest / Gradient Boosting | 트리 기반 모델 | 머신러닝 | [ml.md#decision-tree](ml.md#decision-tree) |
| pca-svd | PCA / SVD | 주성분 분석 / 특이값 분해 | 머신러닝 | [ml.md#pca-svd](ml.md#pca-svd) |
| fisher-yates-shuffle | Fisher-Yates Shuffle | 피셔-예이츠 셔플 | 확률/스트림 | [probabilistic.md#fisher-yates-shuffle](probabilistic.md#fisher-yates-shuffle) |
| reservoir-sampling | Reservoir Sampling | 리저버 샘플링 | 확률/스트림 | [probabilistic.md#reservoir-sampling](probabilistic.md#reservoir-sampling) |
| count-min-sketch | Count-Min Sketch | 카운트-민 스케치 | 확률/스트림 | [probabilistic.md#count-min-sketch](probabilistic.md#count-min-sketch) |
| hyperloglog | HyperLogLog | 하이퍼로그로그 | 확률/스트림 | [probabilistic.md#hyperloglog](probabilistic.md#hyperloglog) |
| 2pc | 2PC (Two-Phase Commit) | 2단계 커밋 | 분산 합의 | [consensus.md#2pc](consensus.md#2pc) |
| paxos | Paxos | Basic / Multi-Paxos | 분산 합의 | [consensus.md#paxos](consensus.md#paxos) |
| raft | Raft | 래프트 | 분산 합의 | [consensus.md#raft](consensus.md#raft) |
| byzantine-pbft | Byzantine Fault Tolerance (PBFT / Byzantine Generals) | 비잔틴 결함 허용 | 분산 합의 | [consensus.md#byzantine-pbft](consensus.md#byzantine-pbft) |
| leader-election | Leader Election (Bully / Ring) | 리더 선출 | 분산 합의 | [consensus.md#leader-election](consensus.md#leader-election) |
| lamport-clock | Lamport Clock | 램포트 시계 | 분산 알고리즘 | [distributed.md#lamport-clock](distributed.md#lamport-clock) |
| vector-clock | Vector Clock | 벡터 시계 | 분산 알고리즘 | [distributed.md#vector-clock](distributed.md#vector-clock) |
| hybrid-logical-clock | Hybrid Logical Clock (HLC) | 하이브리드 논리 시계 | 분산 알고리즘 | [distributed.md#hybrid-logical-clock](distributed.md#hybrid-logical-clock) |
| gossip-protocol | Gossip Protocol | 가십 프로토콜 | 분산 알고리즘 | [distributed.md#gossip-protocol](distributed.md#gossip-protocol) |
| swim | SWIM | SWIM 멤버십 | 분산 알고리즘 | [distributed.md#swim](distributed.md#swim) |
| anti-entropy | Anti-Entropy | 반-엔트로피 동기화 | 분산 알고리즘 | [distributed.md#anti-entropy](distributed.md#anti-entropy) |
| crdt-g-counter | CRDT — G-Counter | 증가 전용 카운터 CRDT | 분산 알고리즘 | [distributed.md#crdt-g-counter](distributed.md#crdt-g-counter) |
| crdt-pn-counter | CRDT — PN-Counter | 증감 카운터 CRDT | 분산 알고리즘 | [distributed.md#crdt-pn-counter](distributed.md#crdt-pn-counter) |
| crdt-or-set | CRDT — OR-Set | 관찰 제거 집합 CRDT | 분산 알고리즘 | [distributed.md#crdt-or-set](distributed.md#crdt-or-set) |
| crdt-lww-set | CRDT — LWW-Set | 마지막 쓰기 우선 집합 CRDT | 분산 알고리즘 | [distributed.md#crdt-lww-set](distributed.md#crdt-lww-set) |
| consistent-hashing | Consistent Hashing | 일관적 해싱 | 분산 알고리즘 | [distributed.md#consistent-hashing](distributed.md#consistent-hashing) |
| quorum | Quorum (R+W>N) | 정족수 합의 | 분산 알고리즘 | [distributed.md#quorum](distributed.md#quorum) |
| chandy-lamport | Chandy-Lamport Distributed Snapshot | 찬디-램포트 분산 스냅샷 | 분산 알고리즘 | [distributed.md#chandy-lamport](distributed.md#chandy-lamport) |
| phi-accrual | Phi Accrual Failure Detector | 파이 누적 장애 감지기 | 분산 알고리즘 | [distributed.md#phi-accrual](distributed.md#phi-accrual) |
| cas | CAS (Compare-And-Swap) | 비교 후 교환 | 동시성/락 | [concurrent.md#cas](concurrent.md#cas) |
| ll-sc | LL-SC (Load-Linked / Store-Conditional) | LL-SC | 동시성/락 | [concurrent.md#ll-sc](concurrent.md#ll-sc) |
| rcu | RCU (Read-Copy-Update) | 읽기-복제-갱신 | 동시성/락 | [concurrent.md#rcu](concurrent.md#rcu) |
| mvcc | MVCC | 다중 버전 동시성 제어 | 동시성/락 | [concurrent.md#mvcc](concurrent.md#mvcc) |
| hazard-pointer | Hazard Pointer | 위험 포인터 | 동시성/락 | [concurrent.md#hazard-pointer](concurrent.md#hazard-pointer) |
| lock-free-queue | Lock-Free Queue (Michael-Scott) | 무락 큐 | 동시성/락 | [concurrent.md#lock-free-queue](concurrent.md#lock-free-queue) |
| work-stealing | Work-Stealing | 작업 훔치기 | 동시성/락 | [concurrent.md#work-stealing](concurrent.md#work-stealing) |
| seqlock | Seqlock | 시퀀스 락 | 동시성/락 | [concurrent.md#seqlock](concurrent.md#seqlock) |
| memory-barriers | Memory Barriers | 메모리 배리어 | 동시성/락 | [concurrent.md#memory-barriers](concurrent.md#memory-barriers) |
| aba-problem | ABA Problem 해법 | ABA 문제 해법 | 동시성/락 | [concurrent.md#aba-problem](concurrent.md#aba-problem) |
| two-phase-locking | Two-Phase Locking + Deadlock Detection | 2단계 잠금 + 교착 검출 | 동시성/락 | [concurrent.md#two-phase-locking](concurrent.md#two-phase-locking) |
| queue-spinlock | Queue-based Spinlocks (Ticket / MCS / CLH) | 큐 기반 스핀락 | 동시성/락 | [concurrent.md#queue-spinlock](concurrent.md#queue-spinlock) |
| lexing | Lexing / Tokenization | 토큰화 | 파서/컴파일러 | [parsing.md#lexing](parsing.md#lexing) |
| ll-k | LL(k) Parsing | LL(k) 파싱 | 파서/컴파일러 | [parsing.md#ll-k](parsing.md#ll-k) |
| lr-1 | LR(1) Parsing | LR(1) 파싱 | 파서/컴파일러 | [parsing.md#lr-1](parsing.md#lr-1) |
| lalr | LALR Parsing | LALR 파싱 | 파서/컴파일러 | [parsing.md#lalr](parsing.md#lalr) |
| earley | Earley Parser | 얼리 파서 | 파서/컴파일러 | [parsing.md#earley](parsing.md#earley) |
| pratt | Pratt Parser | 프랫 파서 | 파서/컴파일러 | [parsing.md#pratt](parsing.md#pratt) |
| peg | PEG / Packrat Parser | PEG/패크랫 파서 | 파서/컴파일러 | [parsing.md#peg](parsing.md#peg) |
| ast-traversal | AST Traversal | AST 순회 | 파서/컴파일러 | [parsing.md#ast-traversal](parsing.md#ast-traversal) |
| ssa | SSA Form | 정적 단일 할당 | 파서/컴파일러 | [parsing.md#ssa](parsing.md#ssa) |
| register-allocation | Register Allocation | 레지스터 할당 | 파서/컴파일러 | [parsing.md#register-allocation](parsing.md#register-allocation) |
| compiler-optimization | Compiler Optimization Passes | 컴파일러 최적화 패스 | 파서/컴파일러 | [parsing.md#compiler-optimization](parsing.md#compiler-optimization) |
| formal-language-theory | Formal Language Theory | 형식 언어 이론 | 파서/컴파일러 | [parsing.md#formal-language-theory](parsing.md#formal-language-theory) |
| r-tree | R-Tree | R-트리 | 공간 인덱싱 | [spatial.md#r-tree](spatial.md#r-tree) |
| r-star-tree | R*-Tree | R*-트리 | 공간 인덱싱 | [spatial.md#r-star-tree](spatial.md#r-star-tree) |
| quadtree | QuadTree | 쿼드트리 | 공간 인덱싱 | [spatial.md#quadtree](spatial.md#quadtree) |
| kd-tree | KD-Tree | k차원 트리 | 공간 인덱싱 | [spatial.md#kd-tree](spatial.md#kd-tree) |
| geohash | Geohash | 지오해시 | 공간 인덱싱 | [spatial.md#geohash](spatial.md#geohash) |
| h3 | H3 (Hexagonal Hierarchical) | 육각 계층 인덱싱 | 공간 인덱싱 | [spatial.md#h3](spatial.md#h3) |
| s2 | S2 Geometry | S2 구면 셀 | 공간 인덱싱 | [spatial.md#s2](spatial.md#s2) |
| bvh | BVH (Bounding Volume Hierarchy) | 경계 볼륨 계층 | 공간 인덱싱 | [spatial.md#bvh](spatial.md#bvh) |
| inverted-index | Inverted Index | 역색인 | 검색·랭킹 | [search-systems.md#inverted-index](search-systems.md#inverted-index) |
| tf-idf | TF-IDF | 단어빈도-역문서빈도 | 검색·랭킹 | [search-systems.md#tf-idf](search-systems.md#tf-idf) |
| bm25 | BM25 (Okapi BM25) | BM25 랭킹 | 검색·랭킹 | [search-systems.md#bm25](search-systems.md#bm25) |
| vector-search | Vector Search (Dense Retrieval) | 벡터 검색 | 검색·랭킹 | [search-systems.md#vector-search](search-systems.md#vector-search) |
| hybrid-search | Hybrid Search (BM25 + Vector Fusion) | 하이브리드 검색 | 검색·랭킹 | [search-systems.md#hybrid-search](search-systems.md#hybrid-search) |
| faceted-search | Faceted Search / Aggregation | 패싯 검색 / 집계 | 검색·랭킹 | [search-systems.md#faceted-search](search-systems.md#faceted-search) |
| autocomplete | Autocomplete / Type-ahead | 자동완성 | 검색·랭킹 | [search-systems.md#autocomplete](search-systems.md#autocomplete) |
| learning-to-rank | Learning to Rank (LTR) | 랭킹 학습 | 검색·랭킹 | [search-systems.md#learning-to-rank](search-systems.md#learning-to-rank) |
| round-robin | Round Robin (RR) | 라운드 로빈 | 부하 분산 | [load-balancing.md#round-robin](load-balancing.md#round-robin) |
| weighted-round-robin | Weighted Round Robin (WRR) | 가중 라운드 로빈 | 부하 분산 | [load-balancing.md#weighted-round-robin](load-balancing.md#weighted-round-robin) |
| least-connections | Least Connections (LC) | 최소 연결 | 부하 분산 | [load-balancing.md#least-connections](load-balancing.md#least-connections) |
| least-response-time | Least Response Time (LRT) | 최소 응답시간 | 부하 분산 | [load-balancing.md#least-response-time](load-balancing.md#least-response-time) |
| power-of-two-choices | Power of Two Choices (P2C) | 둘 중 적은 쪽 선택 | 부하 분산 | [load-balancing.md#power-of-two-choices](load-balancing.md#power-of-two-choices) |
| consistent-hashing-lb | Consistent Hashing (LB) | 일관 해싱 (LB 관점) | 부하 분산 | [load-balancing.md#consistent-hashing-lb](load-balancing.md#consistent-hashing-lb) |
| maglev-hashing | Maglev Hashing | 매글레브 해싱 | 부하 분산 | [load-balancing.md#maglev-hashing](load-balancing.md#maglev-hashing) |
| ewma | EWMA (Exponentially Weighted Moving Average) | 지수 가중 이동평균 | 부하 분산 | [load-balancing.md#ewma](load-balancing.md#ewma) |
| mark-sweep-gc | Mark-Sweep GC | 마크-스윕 가비지 컬렉션 | OS 기초 | [os-foundations.md#mark-sweep-gc](os-foundations.md#mark-sweep-gc) |
| generational-gc | Generational GC | 세대별 가비지 컬렉션 | OS 기초 | [os-foundations.md#generational-gc](os-foundations.md#generational-gc) |
| g1-gc | G1 GC (Garbage First) | G1 가비지 컬렉터 | OS 기초 | [os-foundations.md#g1-gc](os-foundations.md#g1-gc) |
| zgc-shenandoah | ZGC / Shenandoah | 서브밀리초 일시정지 GC | OS 기초 | [os-foundations.md#zgc-shenandoah](os-foundations.md#zgc-shenandoah) |
| round-robin-scheduling | Round-Robin Scheduling | 라운드 로빈 스케줄링 | OS 기초 | [os-foundations.md#round-robin-scheduling](os-foundations.md#round-robin-scheduling) |
| cfs | CFS (Completely Fair Scheduler) | 완전 공정 스케줄러 | OS 기초 | [os-foundations.md#cfs](os-foundations.md#cfs) |
| mlfq | MLFQ (Multi-Level Feedback Queue) | 다단계 피드백 큐 | OS 기초 | [os-foundations.md#mlfq](os-foundations.md#mlfq) |
| slab-allocator | Slab Allocator | 슬랩 할당자 | OS 기초 | [os-foundations.md#slab-allocator](os-foundations.md#slab-allocator) |
| buddy-allocator | Buddy Allocator | 버디 할당자 | OS 기초 | [os-foundations.md#buddy-allocator](os-foundations.md#buddy-allocator) |
| epoll-kqueue-iouring | epoll / kqueue / io_uring | I/O 멀티플렉싱 | OS 기초 | [os-foundations.md#epoll-kqueue-iouring](os-foundations.md#epoll-kqueue-iouring) |
| page-replacement | Page Replacement (LRU / Clock / LFU / ARC) | 페이지 교체 알고리즘 | OS 기초 | [os-foundations.md#page-replacement](os-foundations.md#page-replacement) |
| mesi-cache-coherence | MESI Cache Coherence | MESI 캐시 일관성 | OS 기초 | [os-foundations.md#mesi-cache-coherence](os-foundations.md#mesi-cache-coherence) |
| disk-scheduling | Disk / I/O Scheduling (SCAN / C-SCAN / SSTF) | 디스크 스케줄링 | OS 기초 | [os-foundations.md#disk-scheduling](os-foundations.md#disk-scheduling) |
| process-vs-thread | Process vs Thread Execution Model | 프로세스 vs 스레드 | OS 기초 | [os-foundations.md#process-vs-thread](os-foundations.md#process-vs-thread) |
| virtual-memory | Virtual Memory (Paging / TLB / CoW) | 가상 메모리 | OS 기초 | [os-foundations.md#virtual-memory](os-foundations.md#virtual-memory) |
| convolution-kernel | Convolution / Kernel Filtering | 합성곱 / 커널 필터링 | 이미지 처리 | [image-processing.md#convolution-kernel](image-processing.md#convolution-kernel) |
| edge-detection | Edge Detection (Sobel / Canny / Laplacian) | 엣지 검출 | 이미지 처리 | [image-processing.md#edge-detection](image-processing.md#edge-detection) |
| hough-transform | Hough Transform | 허프 변환 | 이미지 처리 | [image-processing.md#hough-transform](image-processing.md#hough-transform) |
| morphology | Morphological Operations | 형태학적 연산 | 이미지 처리 | [image-processing.md#morphology](image-processing.md#morphology) |
| histogram-equalization | Histogram Equalization | 히스토그램 평활화 | 이미지 처리 | [image-processing.md#histogram-equalization](image-processing.md#histogram-equalization) |
| image-segmentation | Image Segmentation | 이미지 분할 | 이미지 처리 | [image-processing.md#image-segmentation](image-processing.md#image-segmentation) |
| feature-detection | Feature Detection (Harris / SIFT / ORB) | 특징점 검출 | 이미지 처리 | [image-processing.md#feature-detection](image-processing.md#feature-detection) |
| optical-flow | Optical Flow (Lucas-Kanade / Farneback) | 광학 흐름 | 이미지 처리 | [image-processing.md#optical-flow](image-processing.md#optical-flow) |
| jpeg | JPEG (DCT-based) | JPEG 이미지 코덱 | 코덱·미디어 | [codecs.md#jpeg](codecs.md#jpeg) |
| png | PNG (DEFLATE-based) | PNG 무손실 이미지 코덱 | 코덱·미디어 | [codecs.md#png](codecs.md#png) |
| webp-avif-heic | WebP / AVIF / HEIC | 차세대 이미지 코덱 | 코덱·미디어 | [codecs.md#webp-avif-heic](codecs.md#webp-avif-heic) |
| h264 | H.264 / AVC | H.264 비디오 코덱 | 코덱·미디어 | [codecs.md#h264](codecs.md#h264) |
| h265-h266-av1 | H.265 (HEVC) / H.266 (VVC) / AV1 | 차세대 비디오 코덱 | 코덱·미디어 | [codecs.md#h265-h266-av1](codecs.md#h265-h266-av1) |
| mp3-aac | MP3 / AAC | 인지 기반 오디오 코덱 | 코덱·미디어 | [codecs.md#mp3-aac](codecs.md#mp3-aac) |
| opus | Opus (RFC 6716) | Opus 오디오 코덱 | 코덱·미디어 | [codecs.md#opus](codecs.md#opus) |
| entropy-coding | Entropy Coding (Arithmetic / Range / ANS) | 엔트로피 부호화 | 코덱·미디어 | [codecs.md#entropy-coding](codecs.md#entropy-coding) |
| error-correcting-codes | Error Detection & Correction Codes | 오류 검출·정정 부호 | 코덱·미디어 | [codecs.md#error-correcting-codes](codecs.md#error-correcting-codes) |
| fir-filter | FIR Filter | 유한 임펄스 응답 필터 | 신호 처리 | [signal-processing.md#fir-filter](signal-processing.md#fir-filter) |
| iir-filter | IIR Filter | 무한 임펄스 응답 필터 | 신호 처리 | [signal-processing.md#iir-filter](signal-processing.md#iir-filter) |
| stft | STFT | 단시간 푸리에 변환 | 신호 처리 | [signal-processing.md#stft](signal-processing.md#stft) |
| wavelet | Wavelet Transform | 웨이블릿 변환 | 신호 처리 | [signal-processing.md#wavelet](signal-processing.md#wavelet) |
| resampling | Resampling | 리샘플링 | 신호 처리 | [signal-processing.md#resampling](signal-processing.md#resampling) |
| kalman-filter | Kalman Filter | 칼만 필터 | 신호 처리 | [signal-processing.md#kalman-filter](signal-processing.md#kalman-filter) |
| extended-kalman | Extended / Unscented Kalman | EKF / UKF | 신호 처리 | [signal-processing.md#extended-kalman](signal-processing.md#extended-kalman) |
| autocorrelation | Auto/Cross-correlation | 자기/교차 상관 | 신호 처리 | [signal-processing.md#autocorrelation](signal-processing.md#autocorrelation) |
| goertzel | Goertzel Algorithm | 괴르첼 알고리즘 | 신호 처리 | [signal-processing.md#goertzel](signal-processing.md#goertzel) |
| complexity-classes | Computational Complexity Classes & NP-completeness | 복잡도 클래스·NP-완전성 | 계산 복잡도·분석 | [complexity.md#complexity-classes](complexity.md#complexity-classes) |
| computability | Computability & Decidability | 계산 가능성·결정 가능성 | 계산 복잡도·분석 | [complexity.md#computability](complexity.md#computability) |
| amortized-analysis | Amortized Analysis | 분할 상환 분석 | 계산 복잡도·분석 | [complexity.md#amortized-analysis](complexity.md#amortized-analysis) |
| master-theorem | Master Theorem & Recurrence Solving | 마스터 정리·점화식 해법 | 계산 복잡도·분석 | [complexity.md#master-theorem](complexity.md#master-theorem) |
| approximation-algorithms | Approximation Algorithms | 근사 알고리즘 | 계산 복잡도·분석 | [complexity.md#approximation-algorithms](complexity.md#approximation-algorithms) |
| randomized-algorithms | Randomized Algorithms (Las Vegas / Monte Carlo) | 무작위 알고리즘 분류 | 계산 복잡도·분석 | [complexity.md#randomized-algorithms](complexity.md#randomized-algorithms) |

---

## 알고리즘 선택 가이드

### 상황별 추천 알고리즘

| 상황 | 추천 알고리즘 | 카테고리 |
|------|-------------|---------|
| 배열 정렬 (일반) | Quick Sort, Merge Sort | 정렬 |
| 거의 정렬된 배열 | Insertion Sort, Tim Sort | 정렬 |
| 정수 범위가 작은 정렬 | Counting Sort, Radix Sort | 정렬 |
| 메모리에 안 들어가는 정렬 | External Merge Sort | 정렬 |
| 정렬된 배열에서 검색 | Binary Search | 탐색 |
| 해시 테이블 검색 | Hash Search | 탐색 |
| 연속 부분배열 쿼리 | Sliding Window, Two Pointers | 탐색 |
| 구간 합 쿼리 (정적) | Sparse Table, Prefix Sum | 탐색 |
| 구간 합 쿼리 (동적) | Segment Tree, Fenwick Tree | 자료구조 |
| 디스조인트 집합 | Union-Find | 자료구조 |
| 캐싱 (최근 사용) | LRU Cache | 자료구조 |
| 멤버십 확률적 판정 | Bloom Filter | 자료구조 |
| 최단 경로 (양수 가중치) | Dijkstra | 그래프 |
| 최단 경로 (음수 가중치) | Bellman-Ford | 그래프 |
| 모든 쌍 최단 경로 | Floyd-Warshall | 그래프 |
| 경로 탐색 (게임 AI) | A* | 그래프 |
| 최소 신장 트리 | Prim, Kruskal | 그래프 |
| 의존성 해결 | Topological Sort | 그래프 |
| 트리 LCA | Binary Lifting | 그래프 |
| 단절점/단절선 | Articulation, Bridges | 그래프 |
| 최대 유량 | Edmonds-Karp, Dinic | 네트워크 플로우 |
| 최소 컷 (전역) | Stoer-Wagner | 그래프 |
| 이분 매칭 | Hopcroft-Karp, Bipartite Matching | 매칭 |
| 안정 매칭 | Gale-Shapley | 매칭 |
| 최적 부분 구조 문제 | 동적 프로그래밍 | DP |
| TSP (작은 n) | Bitmask DP | DP |
| 트리 통계 | Tree DP | DP |
| 문자열 비교 | Edit Distance | DP |
| 문자열 패턴 매칭 | KMP, Boyer-Moore | 문자열 |
| 여러 패턴 동시 검색 | Aho-Corasick | 문자열 |
| 접두사 검색 | Trie | 문자열 |
| 회문 | Manacher | 문자열 |
| 부분문자열 인덱스 | Suffix Array, Suffix Automaton | 문자열 |
| 볼록 껍질 | Graham Scan, Andrew's Monotone Chain | 계산 기하 |
| 다각형 내부 판정 | Ray Casting | 계산 기하 |
| 선분 교차 | CCW + Segment Intersection | 계산 기하 |
| 소수 판별 | Miller-Rabin | 수학 |
| 소수 목록 생성 | Linear Sieve, Sieve | 수학 |
| 최대공약수 | Euclidean GCD | 수학 |
| 모듈러 역원 | Extended Euclidean | 수학 |
| 큰 합성수 인수분해 | Pollard's Rho | 수학 |
| nCr mod p (큰 n) | Lucas Theorem | 수학 |
| 데이터 압축 | LZ77, Huffman, BWT | 압축 |
| 해시/무결성 | SHA-256, HMAC | 암호 |
| 비밀번호 저장 | Argon2, Bcrypt | 암호 |
| 대칭키 암호화 | AES-GCM | 암호 |
| 공개키 암호화 | RSA, ECC | 암호 |
| 게임 트리 탐색 | Alpha-Beta, MCTS | 게임 AI |
| 메타휴리스틱 최적화 | Genetic, Simulated Annealing | 게임 AI |
| 군집화 | K-Means | 머신러닝 |
| 분류 (간단) | KNN, Naive Bayes, Logistic Regression | 머신러닝 |
| 회귀 | Linear Regression | 머신러닝 |
| 신경망 학습 | Gradient Descent | 머신러닝 |
| 균등 셔플 | Fisher-Yates | 확률 |
| 스트림 샘플링 | Reservoir Sampling | 확률 |
| 스트림 빈도 추정 | Count-Min Sketch | 확률 |
| 스트림 distinct count | HyperLogLog | 확률 |
| 분산 트랜잭션 | 2PC | 분산 합의 |
| 분산 로그 복제 | Raft | 분산 합의 |
| 분산 합의 (일반) | Paxos, Raft | 분산 합의 |

---

## 복잡도 비교

### 정렬 알고리즘

| 알고리즘 | 최선 | 평균 | 최악 | 공간 | 안정성 |
|---------|------|------|------|------|--------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | O |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | X |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | O |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | O |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | X |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | X |
| Counting Sort | O(n+k) | O(n+k) | O(n+k) | O(k) | O |
| Radix Sort | O(d(n+k)) | O(d(n+k)) | O(d(n+k)) | O(n+k) | O |
| Tim Sort | O(n) | O(n log n) | O(n log n) | O(n) | O |
| External Merge | O(n log n) I/O | O(n log n) I/O | O(n log n) I/O | O(M) | O |

### 탐색 알고리즘

| 알고리즘 | 시간 복잡도 | 공간 복잡도 | 요구 조건 |
|---------|-----------|-----------|---------|
| Linear Search | O(n) | O(1) | 없음 |
| Binary Search | O(log n) | O(1) | 정렬됨 |
| Jump Search | O(sqrt n) | O(1) | 정렬됨 |
| Interpolation Search | O(log log n) ~ O(n) | O(1) | 균등 분포 |
| Hash Search | O(1) 평균 | O(n) | 해시 테이블 |
| Sparse Table | O(1) 쿼리 | O(n log n) | 정적, idempotent |
| Mo's Algorithm | O((n+q)√n) | O(n+q) | 오프라인 |

### 그래프 알고리즘

| 알고리즘 | 시간 복잡도 | 공간 복잡도 | 용도 |
|---------|-----------|-----------|------|
| BFS | O(V+E) | O(V) | 최단 경로 (무가중치) |
| DFS | O(V+E) | O(V) | 경로 탐색, 사이클 검출 |
| Dijkstra | O((V+E) log V) | O(V) | 최단 경로 (양수 가중치) |
| Bellman-Ford | O(VE) | O(V) | 최단 경로 (음수 가중치) |
| Floyd-Warshall | O(V³) | O(V²) | 모든 쌍 최단 경로 |
| A* | O(E) | O(V) | 휴리스틱 탐색 |
| Prim / Kruskal | O(E log V) | O(V) | MST |
| LCA (Binary Lifting) | O(log n) 쿼리 | O(n log n) | 트리 조상 |
| Edmonds-Karp | O(VE²) | O(V+E) | 최대 유량 |
| Dinic | O(V²E) | O(V+E) | 최대 유량 |
| Stoer-Wagner | O(V³) | O(V²) | 전역 최소 컷 |

---

## 알고리즘 학습 순서 추천

### 초급
1. Linear Search → Binary Search
2. Bubble Sort → Selection Sort → Insertion Sort
3. BFS → DFS
4. Euclidean GCD
5. Two Pointers, Sliding Window

### 중급
1. Merge Sort → Quick Sort → Heap Sort
2. Dijkstra → Bellman-Ford
3. 동적 프로그래밍 기초 (Fibonacci, LCS, LIS)
4. KMP 문자열 매칭
5. Union-Find, Segment Tree, Fenwick Tree
6. K-Means, KNN
7. Fisher-Yates, Reservoir Sampling

### 고급
1. A* 탐색, MCTS
2. Floyd-Warshall, Johnson, Stoer-Wagner
3. Suffix Array, Aho-Corasick, Suffix Automaton, Manacher
4. FFT, Miller-Rabin, Pollard's Rho
5. Convex Hull (Andrew, Graham)
6. Bitmask DP, Tree DP, Digit DP, SOS DP
7. Network Flow (Edmonds-Karp, Dinic, MCMF)
8. Hopcroft-Karp, Stable Marriage
9. Bloom Filter, HyperLogLog, Count-Min Sketch
10. Raft, Paxos (분산 합의)

---

## 알고리즘 ID 인덱스

292개 알고리즘의 전체 ID → 파일 매핑은 [#알고리즘-id-매핑](#알고리즘-id-매핑) 참조.
프로그래밍 언어 reference 는 [`../languages/`](../languages/) 별도 카탈로그 참조.

카테고리 진입점:

| 카테고리 | 개수 | 파일 |
|---------|------|------|
| 정렬 | 17 | [./sorting.md](./sorting.md) |
| 탐색 | 13 | [./searching.md](./searching.md) |
| 그래프 | 20 | [./graph.md](./graph.md) |
| 동적 프로그래밍 | 13 | [./dynamic-programming.md](./dynamic-programming.md) |
| 분할 정복 | 5 | [./divide-conquer.md](./divide-conquer.md) |
| 탐욕 | 5 | [./greedy.md](./greedy.md) |
| 백트래킹 | 5 | [./backtracking.md](./backtracking.md) |
| 문자열 | 11 | [./string.md](./string.md) |
| 수학 | 16 | [./math.md](./math.md) |
| 자료구조 | 17 | [./data-structures.md](./data-structures.md) |
| 계산 기하 | 7 | [./geometry.md](./geometry.md) |
| 네트워크 플로우 | 4 | [./flow.md](./flow.md) |
| 매칭 | 4 | [./matching.md](./matching.md) |
| 암호/해시 | 12 | [./crypto.md](./crypto.md) |
| 압축 | 5 | [./compression.md](./compression.md) |
| 게임/AI | 5 | [./game-ai.md](./game-ai.md) |
| 머신러닝 | 15 | [./ml.md](./ml.md) |
| 확률/스트림 | 4 | [./probabilistic.md](./probabilistic.md) |
| 분산 합의 | 5 | [./consensus.md](./consensus.md) |
| 분산 알고리즘 | 14 | [./distributed.md](./distributed.md) |
| 동시성/락 알고리즘 | 12 | [./concurrent.md](./concurrent.md) |
| 파서/컴파일러 | 12 | [./parsing.md](./parsing.md) |
| 공간 인덱싱 | 8 | [./spatial.md](./spatial.md) |
| 검색·랭킹 | 8 | [./search-systems.md](./search-systems.md) |
| 부하 분산 | 8 | [./load-balancing.md](./load-balancing.md) |
| OS 기초 | 15 | [./os-foundations.md](./os-foundations.md) |
| 이미지 처리 | 8 | [./image-processing.md](./image-processing.md) |
| 코덱·미디어 | 9 | [./codecs.md](./codecs.md) |
| 신호 처리 | 9 | [./signal-processing.md](./signal-processing.md) |
| 계산 복잡도·분석 | 6 | [./complexity.md](./complexity.md) |

각 카테고리 md 의 `## 알고리즘 목차` 표에서 알고리즘별 anchor 점프 가능.

## 알고리즘 ID 명명 규칙

1. **기본**: 영문명을 kebab-case 변환 (공백·언더스코어 → `-`, 대문자 → 소문자).
   - `Quick Sort` → `quick-sort`
   - `Boyer-Moore` → `boyer-moore`
2. **약어 알고리즘**: lowercase 유지.
   - `KMP` → `kmp`, `BFS` → `bfs`, `DFS` → `dfs`, `LCS` → `lcs`, `LIS` → `lis`, `MCMF` → `mcmf`, `MCTS` → `mcts`, `LRU` → `lru`, `BWT` → `bwt`, `RLE` → `rle`, `LZ77` → `lz77`, `LZW` → `lzw`, `2PC` → `2pc`
3. **특수문자 변환**:
   - `*` → `-star` (예: `A*` → `a-star`)
   - 숫자가 앞에 와도 그대로 (`2-SAT` → `2-sat`)
   - 하이픈은 그대로 유지 (`K-Means` → `k-means`)
   - apostrophe / 괄호 안 약어는 ID 에서 제외 (`Fenwick Tree (BIT)` → `fenwick-tree`, BIT 는 별칭 표에 별도)
4. **카테고리 간 충돌 해소**: 동일 영문명이 두 카테고리에 등장하면 secondary 쪽에 `-<category-suffix>` 부여. 현재 사용 중인 suffix:
   - `-dc` (divide-conquer): `merge-sort-dc`, `binary-search-dc`
   - 향후 추가 시: `-gr` (graph), `-bt` (backtracking) 등 카테고리 첫 두 글자
5. **별칭(alias)**: 약어 ↔ 풀네임, 한국식 ↔ 영문식 같이 다른 명칭이 공존하면 별칭 표에 등재. ID 자체는 단일이고 별칭은 [### 알고리즘 별칭](#알고리즘-별칭) 표에서 resolve.

## `/algorithm <id>` 호출 동작

1. 사용자가 `/algorithm <id>` 또는 자연어("X 알고리즘 구현해줘") 호출.
2. ID resolve:
   - [### 알고리즘 별칭](#알고리즘-별칭) 표에서 별칭이면 primary ID 로 치환.
   - [#알고리즘-id-매핑](#알고리즘-id-매핑) 표에서 `(file, anchor)` lookup.
3. `./<file>.md#<anchor>` 본문 로드 — 헤더 `## N. ...` 부터 다음 `---` 까지가 알고리즘 1개.
4. 프로젝트 언어 자동 감지 후 Kotlin 코드를 해당 언어로 변환 또는 그대로 제공.
5. 적용 위치 제안 + 관련 알고리즘 cross-link 안내.

### 알고리즘 별칭

| 별칭 | Primary ID | 카테고리 파일 |
|------|-----------|------------|
| knn | k-nearest-neighbors | ml.md |
| bit | fenwick-tree | data-structures.md |
| rb-tree | red-black-tree | data-structures.md |
| disjoint-set | union-find | data-structures.md |
| a-star-search | a-star | graph.md |
| lru-cache | lru | data-structures.md |
| breadth-first-search | bfs | graph.md |
| depth-first-search | dfs | graph.md |
| nth-element | quickselect | sorting.md |
| kth-smallest | quickselect | sorting.md |
| median-of-medians | quickselect | sorting.md |
| selection-problem | quickselect | sorting.md |
| bfprt | quickselect | sorting.md |
| priority-queue | binary-heap | data-structures.md |
| min-heap | binary-heap | data-structures.md |
| max-heap | binary-heap | data-structures.md |
| d-ary-heap | binary-heap | data-structures.md |
| kuhn-munkres | hungarian | matching.md |
| assignment-problem | hungarian | matching.md |
| ecdsa | ecc | crypto.md |
| ed25519 | ecc | crypto.md |
| ecdh | ecc | crypto.md |
| x25519 | ecc | crypto.md |
| eddsa | ecc | crypto.md |
| elliptic-curve | ecc | crypto.md |
| dh | diffie-hellman | crypto.md |
| dhe | diffie-hellman | crypto.md |
| ecdhe | diffie-hellman | crypto.md |
| key-agreement | diffie-hellman | crypto.md |
| random-forest | decision-tree | ml.md |
| gradient-boosting | decision-tree | ml.md |
| xgboost | decision-tree | ml.md |
| lightgbm | decision-tree | ml.md |
| gbm | decision-tree | ml.md |
| catboost | decision-tree | ml.md |
| gauss-jordan | gaussian-elimination | math.md |
| row-reduction | gaussian-elimination | math.md |
| rref | gaussian-elimination | math.md |
| discrete-cosine-transform | dct | math.md |
| idct | dct | math.md |
| mdct | dct | math.md |
| convex-hull-trick | dp-optimizations | dynamic-programming.md |
| cht | dp-optimizations | dynamic-programming.md |
| knuth-optimization | dp-optimizations | dynamic-programming.md |
| divide-and-conquer-dp | dp-optimizations | dynamic-programming.md |
| li-chao-tree | dp-optimizations | dynamic-programming.md |
| hld | heavy-light-decomposition | graph.md |
| heavy-path-decomposition | heavy-light-decomposition | graph.md |
| centroid-decomp | centroid-decomposition | graph.md |
| persistent-segment-tree | persistent-data-structures | data-structures.md |
| path-copying | persistent-data-structures | data-structures.md |
| treap | treap-splay | data-structures.md |
| splay-tree | treap-splay | data-structures.md |
| cartesian-tree | treap-splay | data-structures.md |
| open-addressing | hash-collision-resolution | data-structures.md |
| separate-chaining | hash-collision-resolution | data-structures.md |
| cuckoo-hashing | hash-collision-resolution | data-structures.md |
| robin-hood-hashing | hash-collision-resolution | data-structures.md |
| linear-probing | hash-collision-resolution | data-structures.md |
| rope | rope-gap-buffer | data-structures.md |
| gap-buffer | rope-gap-buffer | data-structures.md |
| piece-table | rope-gap-buffer | data-structures.md |
| fibonacci-heap | advanced-heaps | data-structures.md |
| binomial-heap | advanced-heaps | data-structures.md |
| pairing-heap | advanced-heaps | data-structures.md |
| order-statistic-tree | order-statistics-tree | data-structures.md |
| interval-tree | order-statistics-tree | data-structures.md |
| augmented-bst | order-statistics-tree | data-structures.md |
| veb | van-emde-boas | data-structures.md |
| veb-tree | van-emde-boas | data-structures.md |
| y-fast-trie | van-emde-boas | data-structures.md |
| distributed-snapshot | chandy-lamport | distributed.md |
| global-snapshot | chandy-lamport | distributed.md |
| marker-algorithm | chandy-lamport | distributed.md |
| phi-accrual-failure-detector | phi-accrual | distributed.md |
| accrual-failure-detector | phi-accrual | distributed.md |
| pbft | byzantine-pbft | consensus.md |
| byzantine-fault-tolerance | byzantine-pbft | consensus.md |
| bft | byzantine-pbft | consensus.md |
| byzantine-generals | byzantine-pbft | consensus.md |
| bully-algorithm | leader-election | consensus.md |
| ring-election | leader-election | consensus.md |
| coordinator-election | leader-election | consensus.md |
| 2pl | two-phase-locking | concurrent.md |
| deadlock-detection | two-phase-locking | concurrent.md |
| wait-for-graph | two-phase-locking | concurrent.md |
| strict-2pl | two-phase-locking | concurrent.md |
| ticket-lock | queue-spinlock | concurrent.md |
| mcs-lock | queue-spinlock | concurrent.md |
| clh-lock | queue-spinlock | concurrent.md |
| mcs | queue-spinlock | concurrent.md |
| clh | queue-spinlock | concurrent.md |
| sstf | disk-scheduling | os-foundations.md |
| c-scan | disk-scheduling | os-foundations.md |
| elevator-algorithm | disk-scheduling | os-foundations.md |
| thread-model | process-vs-thread | os-foundations.md |
| green-thread | process-vs-thread | os-foundations.md |
| virtual-thread | process-vs-thread | os-foundations.md |
| paging | virtual-memory | os-foundations.md |
| tlb | virtual-memory | os-foundations.md |
| copy-on-write | virtual-memory | os-foundations.md |
| demand-paging | virtual-memory | os-foundations.md |
| chacha20 | chacha20-poly1305 | crypto.md |
| poly1305 | chacha20-poly1305 | crypto.md |
| xchacha20 | chacha20-poly1305 | crypto.md |
| sha3 | sha-3 | crypto.md |
| keccak | sha-3 | crypto.md |
| shake | sha-3 | crypto.md |
| blake2 | blake2-blake3 | crypto.md |
| blake3 | blake2-blake3 | crypto.md |
| scrypt | scrypt-pbkdf2 | crypto.md |
| pbkdf2 | scrypt-pbkdf2 | crypto.md |
| svd | pca-svd | ml.md |
| principal-component-analysis | pca-svd | ml.md |
| goertzel-algorithm | goertzel | signal-processing.md |
| data-flow-analysis | compiler-optimization | parsing.md |
| dead-code-elimination | compiler-optimization | parsing.md |
| constant-folding | compiler-optimization | parsing.md |
| chomsky-hierarchy | formal-language-theory | parsing.md |
| pumping-lemma | formal-language-theory | parsing.md |
| cyk | formal-language-theory | parsing.md |
| crc | error-correcting-codes | codecs.md |
| hamming-code | error-correcting-codes | codecs.md |
| checksum | error-correcting-codes | codecs.md |
| np-complete | complexity-classes | complexity.md |
| np-hard | complexity-classes | complexity.md |
| p-vs-np | complexity-classes | complexity.md |
| cook-levin | complexity-classes | complexity.md |
| halting-problem | computability | complexity.md |
| rice-theorem | computability | complexity.md |
| turing-machine | computability | complexity.md |
| decidability | computability | complexity.md |
| potential-method | amortized-analysis | complexity.md |
| accounting-method | amortized-analysis | complexity.md |
| aggregate-analysis | amortized-analysis | complexity.md |
| recurrence-solving | master-theorem | complexity.md |
| akra-bazzi | master-theorem | complexity.md |
| approximation-ratio | approximation-algorithms | complexity.md |
| ptas | approximation-algorithms | complexity.md |
| fptas | approximation-algorithms | complexity.md |
| las-vegas | randomized-algorithms | complexity.md |
| monte-carlo | randomized-algorithms | complexity.md |
| randomized-algorithm | randomized-algorithms | complexity.md |
