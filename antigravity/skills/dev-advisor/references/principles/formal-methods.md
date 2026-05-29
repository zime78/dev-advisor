# 정형기법 (Formal Methods)

소프트웨어 / 하드웨어의 정확성을 **수학적으로 증명** 하거나 **유한 모델로 완전 탐색** 하는 5 대 정형기법(Formal Methods) 을 다룬다. TLA+ / Alloy 는 *명세 + 모델 검사기* 계열, Hoare Logic 은 *연역 증명* 계열, Model Checking 은 *시간 논리 자동 탐색*, Z notation / Spin / NuSMV 는 *서로 다른 표기 / 도구 비교* 다. 본 문서는 안전 필수(safety-critical) / 분산 합의 / 동시성 알고리즘 검증의 산업 도입 사례까지 포함한다. 검증 단계의 **V-Model 위치** 는 [sdlc-v-model](sdlc-models.md#sdlc-v-model) 의 우측 날개(System / Acceptance Verification) 와 직접 매핑된다.

**원전**:
- Leslie Lamport, *Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers* (Addison-Wesley, 2002)
- Daniel Jackson, *Software Abstractions: Logic, Language, and Analysis* revised ed. (MIT Press, 2012) — Alloy
- C.A.R. Hoare, "An Axiomatic Basis for Computer Programming", *Communications of the ACM* 12 (10) 576-580, 1969
- Edmund M. Clarke, Orna Grumberg, Daniel Kroening, Doron Peled, Helmut Veith, *Model Checking* 2nd ed. (MIT Press, 2018)
- J. M. Spivey, *The Z Notation: A Reference Manual* 2nd ed. (Prentice Hall, 1992)
- Gerard J. Holzmann, *The SPIN Model Checker: Primer and Reference Manual* (Addison-Wesley, 2003)
- Jean-Raymond Abrial, *Modeling in Event-B: System and Software Engineering* (Cambridge UP, 2010)

---

## 1. TLA+ (Temporal Logic of Actions) <a id="formal-tla-plus"></a>

**정의**: Leslie Lamport 가 1994 년 발표한 **상태 기반 정형 명세 언어**. 시스템의 **상태 변환(action)** 과 시간 논리(temporal logic) 를 결합해 *모든 가능한 실행* 을 수학적으로 정의한다. 1차 논리 + 집합론 + ZF 기반으로, "프로그램 코드 아닌 *시스템 자체*" 를 기술한다. TLC(Temporal Logic Checker) Model Checker 와 TLAPS(증명기) 두 도구가 공식 검증을 지원한다.

**표기법 / 의미론**:
- `Init` 술어: 초기 상태 집합 정의 (예: `Init == x = 0 /\ y = 0`)
- `Next` 술어: 단일 스텝 변환 (예: `Next == x' = x + 1 /\ y' = y`) — `prime(x')` 은 다음 상태 값
- `Spec`: `Init /\ [][Next]_<<x,y>> /\ WF_<<x,y>>(Next)` — 안전성 + 활성(weak fairness)
- 시간 연산자: `[]P` (always), `<>P` (eventually), `~>` (leads-to), `<>[]P` (eventually-always)
- PlusCal: TLA+ 를 절차형 의사코드처럼 쓰는 알고리즘 언어 — TLA+ 로 자동 번역

**의미론**: 시스템은 **상태의 무한 시퀀스(behavior)** 집합. 명세 = 그 집합. 검증 = 명세가 *원하는 속성* (invariant + 활성) 을 모든 behavior 에서 만족하는지 자동 탐색.

**도구**:
| 도구 | 역할 | 한계 |
|---|---|---|
| **TLC** | 유한 상태 공간 BFS / DFS 탐색 | 상태 폭증 (state explosion) |
| **TLAPS** | Hilbert 스타일 연역 증명 — 무한 상태 OK | 사람이 증명 단계 작성 |
| **TLA+ Toolbox / VS Code Plugin** | IDE — 명세 편집 / TLC 실행 / 반례 트레이스 시각화 | - |
| **Apalache** | SMT-기반 symbolic checker (Z3 백엔드) | TLC 보완재 |

**산업 도입 사례 (AWS)**:
- DynamoDB: 다중 영역 복제 프로토콜 — 7 개의 미발견 결함 사전 검출 (Newcombe et al., CACM 58 (4), 2015, "How Amazon Web Services Uses Formal Methods")
- S3: 다중 객체 트랜잭션 — 강한 일관성 보장 검증
- EBS: 볼륨 복제 프로토콜 — leader election 정확성 증명
- Cosmos DB (Microsoft): 5 단계 일관성 모델 — TLA+ 로 사양 작성
- Elastic Block Store (AWS): garbage collection 알고리즘 — 라이브락 검출

**한계**:
- 상태 폭증: TLC 는 유한 상태에서만 자동 탐색, 큰 시스템은 abstraction 필요
- 학습 곡선: 시간 논리 + 집합론 + ZF 의 형식 의미론 진입 장벽
- 코드 ≠ 명세: TLA+ 는 *명세* 만 검증 — 실제 구현이 명세를 따르는지는 별도 검증
- 활성 속성(liveness) 검증은 fairness 가정 필수 (WF / SF)

**관련**:
- [paxos](../algorithms/consensus.md#paxos), [raft](../algorithms/consensus.md#raft) — Paxos / Raft 합의는 모두 TLA+ 명세가 공식 배포되어 있음
- [consistency-models](../../../data-advisor/references/principles/db-fundamentals.md#consistency-models) — Cosmos DB 의 5 단계 일관성은 TLA+ 명세로 정의
- [linearizability](concurrency-theory.md#linearizability) — 선형화 가능성은 TLA+ refinement 로 증명

**표준 인용**:
- Lamport, *Specifying Systems* (2002) — TLA+ 정본
- Newcombe et al., "How Amazon Web Services Uses Formal Methods", CACM 58 (4), 2015
- Lamport, "The Temporal Logic of Actions", *ACM TOPLAS* 16 (3) 1994

---

## 2. Alloy (관계 논리 기반 명세) <a id="formal-alloy"></a>

**정의**: MIT Daniel Jackson 이 2002 년 발표한 **1차 관계 논리(first-order relational logic)** 기반 정형 명세 언어 + 분석기. TLA+ 가 시간 / 상태 변환 중심이라면 Alloy 는 **구조 / 데이터 모델 / 관계** 중심. *Scope-bounded analysis* (유한 도메인 한정 SAT) 로 반례를 빠르게 찾는다.

**표기법 / 의미론**:
- `sig`: 원자(atom) 집합 정의 (`sig User { friends: set User }`)
- `fact`: 항상 참인 제약 (`fact { all u: User | u not in u.friends }` — 자기 자신은 친구 아님)
- `pred`: 술어 — 조건부 (`pred addFriend[u, v: User] { ... }`)
- `assert`: 검증할 단언문 (`assert NoSelfFriend { all u: User | u not in u.^friends }`)
- `run` / `check`: 분석 — `check NoSelfFriend for 5` (scope=5, 즉 atom 5 개 이내 모든 가능성 탐색)
- 관계 연산: `.` (join), `->` (cross product), `^` (transitive closure), `*` (reflexive closure), `~` (transpose)

**의미론**: 모든 명세는 **유한 관계의 집합** 으로 변환 → SAT solver (MiniSat / Glucose / Plingeling) 로 해 / 반례 탐색.

**Alloy Analyzer 도구 흐름**:
1. `.als` 파일 작성 (signature + facts + predicates)
2. `run` 명령으로 인스턴스 생성 (만족 가능한 모델) 또는 `check` 로 반례 탐색
3. SAT solver 가 KodKod (관계 → 명제 변환) 거쳐 CNF 로 변환 후 풀이
4. 시각화: 그래프 형태로 atom + 관계 표시

**산업 / 학술 도입 사례**:
- Chord DHT (MIT): peer-to-peer routing 정확성 검증 — Alloy 로 ring 구조 invariant 증명
- Mondex Smart Card: 전자 화폐 프로토콜 — Alloy + Z 병용
- Microsoft Wireless USB: 디바이스 페어링 프로토콜 검증
- Pamela (Intel): firmware 동기화 프로토콜
- AWS IAM 정책: 권한 분석 — Zelkova / Tiros 의 기반
- Margrave: XACML 정책 분석

**한계**:
- Scope-bounded: 작은 scope 에서 반례 없음 ≠ 모든 scope 에서 안전 (small scope hypothesis 가정 — *Jackson 가설* 에 의존)
- 시간적 속성 표현 한계 (Alloy 6 에서 temporal 지원 추가, 하지만 TLA+ 보다 빈약)
- 무한 도메인 정량화는 검증 불가
- 성능: scope 가 커지면 SAT 시간 폭증

**관련**:
- [hoare-logic](#hoare-logic) — Hoare 는 무한 도메인 연역 증명, Alloy 는 유한 도메인 자동 탐색 (상호 보완)
- [model-checking](#model-checking) — Alloy 는 *구조* 모델 검사, NuSMV / SPIN 은 *시간 / 상태* 모델 검사

**표준 인용**:
- Daniel Jackson, *Software Abstractions* revised ed., MIT Press, 2012
- Jackson, "Alloy: A Lightweight Object Modelling Notation", *ACM TOSEM* 11 (2) 2002

---

## 3. Hoare Logic (호어 논리) <a id="hoare-logic"></a>

**정의**: C.A.R. Hoare 가 1969 년 CACM 논문에서 제시한 **연역 증명** 기반 프로그램 정확성 검증 체계. **삼중자(triple)** `{P} C {Q}` — 사전조건 P 가 성립할 때 명령 C 를 실행하면 사후조건 Q 가 성립 — 를 공리계로 도출한다. 정형기법의 *수학적 기초*.

**표기법 / 의미론**:
- 삼중자: `{P} C {Q}` 또는 `[P] C [Q]`
- `P`: 사전조건(precondition) — 1차 논리 술어
- `C`: 명령(command) — while 언어 또는 IMP
- `Q`: 사후조건(postcondition) — 1차 논리 술어

**부분 정확성 vs 전체 정확성**:
| 종류 | 표기 | 의미 |
|---|---|---|
| **Partial correctness** | `{P} C {Q}` | P 성립 + C 가 *종료한다면* Q 성립 (종료 보장 X) |
| **Total correctness** | `[P] C [Q]` | P 성립이면 C 가 *반드시 종료* 하며 Q 성립 |

**핵심 추론 규칙**:
```
                                                         {P} C1 {R}   {R} C2 {Q}
[Assign]  {P[E/x]} x := E {P}                   [Seq]  ─────────────────────────
                                                              {P} C1; C2 {Q}

          {P /\ B} C1 {Q}   {P /\ ~B} C2 {Q}              {I /\ B} C {I}
[If]   ─────────────────────────────────         [While]  ───────────────────────
        {P} if B then C1 else C2 {Q}                       {I} while B do C {I /\ ~B}

          P' => P   {P} C {Q}   Q => Q'
[Cons]  ──────────────────────────────────       (I = loop invariant)
                {P'} C {Q'}
```

**전체 정확성용 While 규칙** (variant 함수 V 가 well-founded 순서로 감소):
- `{I /\ B /\ V = z} C {I /\ V < z}` (단조 감소) + V >= 0 → 종료 보장

**도구**:
| 도구 | 베이스 | 특징 |
|---|---|---|
| **Dafny** | Microsoft, .NET | 명령형 언어 + Hoare-style annotation + Z3 자동 증명 |
| **Why3** | INRIA | WhyML 중간 언어 + 다중 백엔드 (Coq / Alt-Ergo / CVC4 / Z3) |
| **Frama-C / WP plugin** | CEA | C 코드 + ACSL annotation → WP (Weakest Precondition) 계산 |
| **VeriFast** | KU Leuven | C / Java + Separation Logic |
| **KeY** | TU Darmstadt | Java + JML + dynamic logic |
| **VCC** | Microsoft | C concurrent code (Hyper-V kernel 검증에 사용) |

**산업 도입 사례**:
- Hyper-V hypervisor (Microsoft): VCC 로 100K LoC 동시성 코드 검증
- Paris Métro Line 14 (CBTC): B-Method (Hoare 계열) — 인명 사고 0건 운행
- AWS s2n TLS 라이브러리: Frama-C / Coq 로 핸드셰이크 정확성 증명
- IronFleet (Microsoft Research): Dafny 로 분산 시스템 (Paxos / 키밸류 스토어) 검증
- seL4 microkernel: Isabelle/HOL (Hoare logic 기반) 로 9000 LoC 전체 검증

**한계**:
- annotation 부담: loop invariant / variant / 사전·사후조건 모두 사람이 작성
- 자동 증명기 한계: 비선형 정수 / 부동소수점 / heap 처리는 SMT 도 어려움
- Separation Logic (O'Hearn / Reynolds 2002) 이 heap / pointer 문제 보완
- 동시성: 표준 Hoare logic 은 sequential — Concurrent Separation Logic 으로 확장

**관련**:
- [formal-tla-plus](#formal-tla-plus) — TLA+ 는 *시스템 명세*, Hoare 는 *코드 검증* (보완)
- [model-checking](#model-checking) — Hoare 는 연역(무한), Model Checking 은 탐색(유한)
- [sdlc-v-model](sdlc-models.md#sdlc-v-model) — V-Model 의 Unit Test 단계에 Hoare-style annotation + Dafny 가 직접 매핑

**표준 인용**:
- C.A.R. Hoare, "An Axiomatic Basis for Computer Programming", CACM 12 (10) 576-580, 1969
- Edsger W. Dijkstra, "Guarded Commands, Nondeterminacy and Formal Derivation of Programs", CACM 18 (8) 1975 — wp 계산
- P. O'Hearn, J. Reynolds, H. Yang, "Local Reasoning about Programs that Alter Data Structures", CSL 2001 — Separation Logic

---

## 4. Model Checking (모델 검사) <a id="model-checking"></a>

**정의**: 시스템을 **유한 상태 전이 구조(Kripke structure)** 로 표현하고, 시간 논리(CTL / LTL / CTL\*) 로 명세한 속성을 **모든 가능한 실행 경로에서 자동 검증**. 1981 년 Clarke / Emerson(미국) 과 Queille / Sifakis(프랑스) 가 독립 발견 — 2007 년 Turing Award 수상.

**Kripke 구조**:
- 4 원소 `M = (S, S0, R, L)`
  - S: 상태 집합 (유한)
  - S0 ⊆ S: 초기 상태
  - R ⊆ S × S: 전이 관계 (좌-totality 가정 — 모든 상태에 후속자)
  - L: S → 2^AP: 라벨링 함수 (각 상태에서 참인 원자 명제 집합)

**시간 논리 비교**:
| 논리 | 의미론 | 연산자 | 표현력 |
|---|---|---|---|
| **LTL** (Linear Temporal Logic) | 단일 경로 (path 기반) | `X` (next), `F` (eventually), `G` (always), `U` (until), `R` (release) | 공정성(fairness) 표현 용이 |
| **CTL** (Computation Tree Logic) | 분기 (branching tree) | `AX / EX / AF / EF / AG / EG / AU / EU` (A=all paths, E=some path) | 분기 표현 — `EF p` (어떤 경로에서 p 도달 가능) |
| **CTL\*** | LTL + CTL 통합 | 양자화 자유 | 표현력 최대 — 검증 복잡도 높음 |

**핵심 알고리즘**:
- **Explicit-state**: 상태 그래프 BFS / DFS — 작은 시스템에 빠름 (SPIN)
- **Symbolic (BDD)**: Binary Decision Diagram 으로 상태 집합 표현 — 10^20 상태까지 처리 (McMillan 1992, SMV)
- **Bounded Model Checking (BMC)**: k-step 까지만 SAT 인코딩 → 짧은 반례 빠르게 발견 (Biere 1999)
- **CEGAR** (Counterexample-Guided Abstraction Refinement): 추상 → 검사 → 가짜 반례 → 정교화 (Clarke 2000) — SLAM / BLAST

**대표 도구**:
| 도구 | 입력 언어 | 백엔드 | 강점 / 사용 사례 |
|---|---|---|---|
| **NuSMV** / **nuXmv** | SMV 모듈러 언어 | BDD + BMC + IC3 | 하드웨어 검증 / RUAG / Rockwell |
| **SPIN** | Promela | Explicit + Partial Order Reduction | 분산 프로토콜 (TCP / 우주선 — JPL Deep Space 1) |
| **SLAM** (MS) | C → boolean program | CEGAR + BDD | Windows 드라이버 (SDV 도구) — 4000+ 결함 발견 |
| **BLAST** | C | CEGAR + Predicate Abstraction | Linux 커널 드라이버 |
| **CBMC** | C / C++ | BMC + SAT/SMT | embedded software / Boolector |
| **UPPAAL** | Timed Automata | Zone-based | 실시간 시스템 (자동차 ECU / 의료기기) |
| **PRISM** | PRISM language | Probabilistic | 확률론적 시스템 / Markov chain |

**산업 도입 사례**:
- Intel Pentium FDIV bug (1994 $475M 손실) 이후 Intel 은 모든 부동소수점 유닛에 모델 검사 적용 — Symbolic Trajectory Evaluation (Forte)
- IBM RuleBase: PowerPC / zSeries 프로세서 검증
- NASA Deep Space 1: SPIN 으로 5 개 동시성 버그 발견 (Holzmann)
- Microsoft SLAM / Static Driver Verifier: Windows 7 이후 모든 WDF 드라이버 의무
- ARM Cortex-A53: CSP / FDR 모델 검사로 cache coherence 검증

**한계**:
- 상태 폭증: 변수 n 개 × 도메인 d → d^n 상태 — 가장 큰 한계
- 무한 상태 시스템: abstraction / induction 필요
- 명세 작성 난이도: CTL / LTL 학습 곡선
- 모델 ≠ 구현: 모델이 정확해도 구현이 다르면 무효 (model extraction / refinement check 필요)

**관련**:
- [formal-tla-plus](#formal-tla-plus) — TLC 는 explicit-state 모델 검사기
- [z-notation-spin-nusmv](#z-notation-spin-nusmv) — SPIN / NuSMV / Z 비교
- [paxos](../algorithms/consensus.md#paxos), [raft](../algorithms/consensus.md#raft) — 합의 프로토콜의 SPIN / TLA+ 검증 사례
- [sdlc-v-model](sdlc-models.md#sdlc-v-model) — V-Model 우측 날개 System Verification 단계의 자동화 수단

**표준 인용**:
- Clarke, Grumberg, Kroening, Peled, Veith, *Model Checking* 2nd ed., MIT Press, 2018
- E. Clarke, E. A. Emerson, "Design and Synthesis of Synchronization Skeletons Using Branching Time Temporal Logic", *LNCS* 131, 1981
- J. P. Queille, J. Sifakis, "Specification and Verification of Concurrent Systems in CESAR", *Symposium on Programming*, 1982
- A. Biere, A. Cimatti, E. Clarke, Y. Zhu, "Symbolic Model Checking without BDDs", TACAS 1999 — BMC 원논문
- E. Clarke, O. Grumberg, S. Jha, Y. Lu, H. Veith, "Counterexample-Guided Abstraction Refinement", CAV 2000

---

## 5. Z Notation + Spin + NuSMV (도구 / 표기법 비교) <a id="z-notation-spin-nusmv"></a>

**정의**: 정형기법의 *3 대 패밀리* 를 한 곳에서 비교한다.
- **Z**: ZFC 집합론 + 1차 논리 기반 **상태 명세 언어** (Oxford PRG / Spivey)
- **SPIN**: Promela 입력 + LTL 속성 검증 **explicit-state** 분산 시스템 모델 검사기 (Holzmann / Bell Labs)
- **NuSMV / nuXmv**: SMV 입력 + CTL/LTL **symbolic (BDD)** 모델 검사기 (CMU / FBK-IRST)

**표기법 비교 (간략 예시)**:

```
Z notation (상태 schema):                                 Promela (SPIN):

ATM                                                       active [3] proctype Customer() {
══════════════════                                          do
balance: N                                                  :: card?ok -> withdraw!amount;
amount?: N                                                       balance?b -> printf("OK %d\n",b)
══════════════════                                          :: card?invalid -> printf("Invalid\n")
amount? <= balance                                          od
balance' = balance - amount?                              }
══════════════════
                                                          ltl safety { [] (balance >= 0) }


SMV (NuSMV):

MODULE main
  VAR
    state : {idle, withdraw, locked};
    balance : 0..1000;
  ASSIGN
    init(state) := idle;
    next(state) := case
                     state = idle & balance > 0 : withdraw;
                     state = withdraw           : idle;
                     TRUE                       : state;
                   esac;
  LTLSPEC G (balance >= 0)
  CTLSPEC AG EF (state = idle)
```

**세 도구 비교 표**:

| 항목 | Z Notation | SPIN | NuSMV |
|---|---|---|---|
| 패밀리 | 명세 언어 (증명 대상) | Explicit-state MC | Symbolic (BDD) MC |
| 표기 | ZFC + 스키마 (수학 기호) | Promela (C-like) | SMV modular |
| 검증 방식 | 정리 증명기(ProofPower / Z/EVES) | LTL + DFS + Partial Order Reduction | CTL/LTL + BDD + BMC + IC3 |
| 강점 | 상세한 데이터 명세 / 정련(refinement) | 분산 / 동시성 프로토콜 | 하드웨어 / large state space |
| 약점 | 자동화 부족 (사람 증명 부담) | 큰 상태 공간 한계 | 비결정성 / 데이터 풍부 시스템 |
| 산업 사례 | CICS (IBM) / Mondex / 영국 NHS | NASA Deep Space 1 / TCP / Plan 9 | Rockwell Collins / Intel |
| 표준 | ISO/IEC 13568:2002 | LTL — IEEE / non-standard | CTL — Clarke / Emerson |

**B-Method (RATP / SNCF 사례)**:
- Z 의 산업 친화 후속 — Jean-Raymond Abrial (Z 공동 창시자) 가 1996 년 *The B-Book* 발표
- 추상 기계(Abstract Machine) → 정련(Refinement) → 구현(Implementation) 3 단계
- Atelier B / ProB / Rodin (Event-B IDE)
- **RATP Paris Métro Line 14 (1998 개통)**: CBTC (Communications-Based Train Control) — B-Method 로 110K LoC 전체 검증 → 인명 사고 0건 (개통 후 27년)
- **SNCF KVB / KVB-P**: 신호 시스템 검증
- **Siemens Charles de Gaulle Airport CDGVAL**: 무인 셔틀 — B-Method
- **Alstom Roissy CDG Métro Line 1 자동화 개조 (2012)**: Event-B

**정리증명기(Theorem Prover) 비교 — Coq / Lean / Isabelle**:

| 도구 | 베이스 | 자동화 | 산업 사례 |
|---|---|---|---|
| **Coq** | Calculus of Inductive Constructions (CIC) | tactic-based 반자동 | CompCert (Inria 검증 C 컴파일러), Iris (separation logic) |
| **Lean 4** | Calculus of Constructions (Type theory + dependent types) | macro / metaprogramming | mathlib4 (수학 정리 라이브러리), Microsoft / AWS |
| **Isabelle/HOL** | Higher-Order Logic (Church/HOL) | sledgehammer + Sledgehammer + auto | seL4 microkernel (NICTA / Data61 9000 LoC kernel 전체 검증), AFP archive |
| **PVS** | classical higher-order + subtypes | model + decision procedures | NASA / SRI 임무 critical |
| **Agda** | Martin-Löf type theory | 거의 수동 | 학술 / 의존타입 연구 |
| **HOL Light** | minimal HOL + 강력한 자동화 | 자동화 우수 | Flyspeck (Kepler 추측 / Hales 2014) |

**한계**:
- Z: 자동 도구 약화 (1990 년대 이후 B-Method / Event-B / Alloy 로 흡수)
- SPIN: 데이터-rich 시스템에서 상태 폭증 — symbolic 전환 어려움
- NuSMV: 비동기 / 동시성 모델 표현이 SPIN 보다 불편
- 모든 형식 도구: **명세가 정확해야** 검증 의미 있음 (GIGO — Garbage In, Garbage Out 원칙)
- 사회적 비용: 도메인 전문가 + 형식 전문가 협업 비용 큼

**관련**:
- [formal-tla-plus](#formal-tla-plus) — TLA+ 는 Z 의 시간 / 변환 확장으로 볼 수 있음
- [model-checking](#model-checking) — SPIN / NuSMV 는 model checking 의 대표 구현
- [hoare-logic](#hoare-logic) — B-Method / Event-B / Coq 는 Hoare-style 정련 + 증명 결합
- [paxos](../algorithms/consensus.md#paxos), [raft](../algorithms/consensus.md#raft) — Paxos 는 Z / Event-B / TLA+ 명세 모두 존재
- [consistency-models](../../../data-advisor/references/principles/db-fundamentals.md#consistency-models) — 데이터베이스 일관성 모델은 Z / TLA+ 로 정형 명세
- [sdlc-v-model](sdlc-models.md#sdlc-v-model) — V-Model 의 좌측(요구 / 설계) ↔ 우측(검증) 매핑은 Z + B-Method 의 *정련 사슬* 과 동형

**표준 인용**:
- ISO/IEC 13568:2002, *Information technology — Z formal specification notation — Syntax, type system and semantics*
- J. M. Spivey, *The Z Notation: A Reference Manual* 2nd ed., Prentice Hall, 1992
- Gerard J. Holzmann, *The SPIN Model Checker: Primer and Reference Manual*, Addison-Wesley, 2003
- A. Cimatti, E. Clarke, E. Giunchiglia, F. Giunchiglia, M. Pistore, M. Roveri, R. Sebastiani, A. Tacchella, "NuSMV 2: An OpenSource Tool for Symbolic Model Checking", CAV 2002
- Jean-Raymond Abrial, *The B-Book: Assigning Programs to Meanings*, Cambridge UP, 1996
- Jean-Raymond Abrial, *Modeling in Event-B: System and Software Engineering*, Cambridge UP, 2010
- G. Klein et al., "seL4: Formal Verification of an OS Kernel", SOSP 2009 — Isabelle/HOL 사례
- Xavier Leroy, "Formal Verification of a Realistic Compiler", CACM 52 (7) 2009 — Coq / CompCert

---

## 통합 비교 매트릭스 (5 정형기법)

| 기법 | 의미론 베이스 | 자동화 수준 | 상태 공간 | 산업 도입 영역 | V-Model 위치 |
|---|---|---|---|---|---|
| TLA+ | 시간 논리 + 집합론 | TLC 자동 / TLAPS 반자동 | 유한(TLC) / 무한(TLAPS) | 분산 시스템 (AWS / Azure) | 시스템 설계 ↔ 시스템 검증 |
| Alloy | 1차 관계 논리 (SAT) | 완전 자동 (scope-bounded) | 유한 (scope) | 데이터 모델 / 정책 / 프로토콜 | 설계 ↔ 통합 검증 |
| Hoare Logic | 1차 논리 + wp 계산 | Dafny / Why3 반자동 | 무한 (연역) | 안전 critical SW (Hyper-V / seL4) | 모듈 설계 ↔ 단위 검증 |
| Model Checking | 시간 논리 + Kripke | 완전 자동 | 유한 (BDD 10^20) | HW 검증 / 드라이버 / 프로토콜 | 통합 ↔ 시스템 검증 |
| Z / B / Event-B | ZFC + 정련 + Hoare | 도구별 (ProB / Atelier B) | 무한 (정련) | 철도 신호 (RATP / SNCF) | 요구 ↔ 인수 검증 (V 양 끝) |

## 한계 및 사회적 비용

- **GIGO 원칙**: 명세가 틀리면 검증도 무효 — 도메인 전문가 + 형식 전문가 협업 필수
- **비용**: B-Method (RATP Line 14) 는 일반 SW 대비 약 25% 추가 비용 (인명 사고 0건 가치와 trade-off)
- **추출 vs 정련**: 코드 → 모델 추출(verification by model extraction) vs 모델 → 코드 정련(refinement) 의 선택
- **사회적 수용**: 의료기기 (IEC 62304 Class C), 항공 (DO-178C DAL A/B), 철도 (EN 50128 SIL 4) 만 *실질적 의무*
- **AI 시대**: ML 모델 검증은 아직 미해결 — 통계적 검증 / probabilistic model checking (PRISM) 으로 부분 대응

## 표준 인용 (종합)

- ISO/IEC 13568:2002 — Z notation
- ISO/IEC 24744 — Software engineering modeling
- IEC 62304 — Medical device software (Class C 안전 필수)
- RTCA DO-178C — Software Considerations in Airborne Systems (DAL A 안전 필수)
- CENELEC EN 50128:2011 — Railway applications (SIL 4 안전 필수)
- IEEE Std 1012-2016 — System, Software, and Hardware Verification and Validation
- E. M. Clarke, O. Grumberg, D. Kroening, D. Peled, H. Veith, *Model Checking* 2nd ed., MIT Press, 2018
- Leslie Lamport, *Specifying Systems*, Addison-Wesley, 2002
- Daniel Jackson, *Software Abstractions* revised ed., MIT Press, 2012
- C.A.R. Hoare, "An Axiomatic Basis for Computer Programming", CACM 12 (10) 1969
- J. M. Spivey, *The Z Notation: A Reference Manual* 2nd ed., Prentice Hall, 1992
- Gerard Holzmann, *The SPIN Model Checker*, Addison-Wesley, 2003
- Jean-Raymond Abrial, *The B-Book*, Cambridge UP, 1996
- Jean-Raymond Abrial, *Modeling in Event-B*, Cambridge UP, 2010
- Newcombe, Rath, Zhang, Munteanu, Brooker, Deardeuff, "How Amazon Web Services Uses Formal Methods", CACM 58 (4) 2015

---

## 카탈로그 매핑

- `principles/concurrency-theory.md`: [linearizability](concurrency-theory.md#linearizability), [serializability](concurrency-theory.md#serializability), [liveness-safety](concurrency-theory.md#liveness-safety) — 본 문서의 시간 논리(safety / liveness) 정의와 직접 연결
- `principles/sdlc-models.md`: [sdlc-v-model](sdlc-models.md#sdlc-v-model) — 안전 critical 검증 단계의 정형기법 도입 매핑
- `principles/database-fundamentals.md`: [consistency-models](../../../data-advisor/references/principles/db-fundamentals.md#consistency-models) — DB 일관성 모델은 TLA+ / Z 정형 명세의 산업 적용
- `algorithms/consensus.md`: [paxos](../algorithms/consensus.md#paxos), [raft](../algorithms/consensus.md#raft) — 합의 알고리즘의 TLA+ / SPIN / B-Method 형식 증명 사례
