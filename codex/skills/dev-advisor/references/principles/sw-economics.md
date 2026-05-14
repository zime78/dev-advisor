# SW 경제·추정 (Software Economics & Estimation)

SWEBOK KA11 *Software Engineering Economics* 의 핵심 10 기법. 작업 산정 / 우선순위 결정 / 기술부채 정량화. 추정은 *예측* 이 아니라 *합의* + *보정 가능 모델* — 정량과 정성 결합.

**원전·표준**:
- Allan Albrecht — "Measuring Application Development Productivity" (IBM, 1979) — Function Points
- Barry Boehm — *Software Cost Estimation with COCOMO II* (2000)
- Mike Cohn — *Agile Estimating and Planning* (2005)
- Don Reinertsen — *The Principles of Product Development Flow* (2009) — CoD, WSJF
- Daniel Kahneman — *Thinking, Fast and Slow* (2011) — Reference Class Forecasting
- Martin Fowler — "TechnicalDebtQuadrant" (martinfowler.com, 2009)
- IEEE SWEBOK v4 — KA11 Software Engineering Economics
- SAFe Framework — WSJF 공식 가이드
- IFPUG — *Function Point Counting Practices Manual* (CPM 4.3.1)

**핵심 원칙**:
- **단일 숫자보다 분포 (3-point estimate)** — Best/Likely/Worst case, PERT 공식 `(B + 4M + W) / 6`
- **상대 추정 > 절대 추정** — Story Point 가 person-day 보다 안정적 (Cohn)
- **Reference class > expert judgment** — 외부 사례 평균이 내부 직관보다 정확 (Flyvbjerg)
- **Anchor effect 경계** — Planning Poker 의 익명 카드는 anchoring 회피
- **부채는 *증상* 이 아니라 *원인* 분류** — Fowler quadrant 는 *왜 생겼는가* 로 처방 결정

**관련 카탈로그**:
- [iso25010.md](iso25010.md) — 품질 특성 (maintainability 측정과 연계)
- [code-smells.md](code-smells.md) — 기술 부채 *증상*
- [`refactoring-techniques.md`](refactoring-techniques.md) — 부채 *처방*
- [12-factor.md](12-factor.md) — 운영 부채를 줄이는 설계
- [grasp.md](grasp.md) — 추정 정확도를 높이는 설계 분할 (Low Coupling / High Cohesion)

---

<a id="1-function-points"></a>
## 1. Function Points (FP — 기능 점수)

**정의**: Allan Albrecht (IBM, 1979) 가 제안한 **언어·기술 비종속** 규모 측정 단위. 시스템이 사용자에게 제공하는 *기능량* 을 5 가지 type 로 분해해 가중치 합산. IFPUG (International Function Point Users Group) 가 표준화한 CPM (Counting Practices Manual) 이 사실상 ISO/IEC 20926 표준.

**핵심 판단**: 코드 라인 수(LOC) 가 아니라 **사용자 관점 기능 단위** 로 규모를 추정. 같은 기능이라도 언어·프레임워크에 따라 LOC 가 5~10× 다르지만 FP 는 일정.

**5 가지 기능 type**:

| Type | 약어 | 의미 | 예시 |
|---|---|---|---|
| External Input | EI | 시스템 내부 데이터를 변경하는 입력 | 회원 가입, 주문 생성 |
| External Output | EO | 가공된 데이터 출력 (계산·요약 포함) | 매출 리포트, 차트 |
| External Inquiry | EQ | 단순 조회 (가공 없음) | 회원 정보 보기 |
| Internal Logical File | ILF | 시스템 내부에서 관리하는 데이터 그룹 | 회원 테이블, 주문 테이블 |
| External Interface File | EIF | 외부 시스템에서 참조하는 데이터 그룹 | 외부 결제사 API |

**복잡도 가중치** (IFPUG 표준):

| Type | Low | Average | High |
|---|---|---|---|
| EI | 3 | 4 | 6 |
| EO | 4 | 5 | 7 |
| EQ | 3 | 4 | 6 |
| ILF | 7 | 10 | 15 |
| EIF | 5 | 7 | 10 |

**공식**:
```
UFP (Unadjusted Function Point) = Σ (각 type 카운트 × 복잡도 가중치)
VAF (Value Adjustment Factor)   = 0.65 + 0.01 × Σ(14 GSC factor, 0~5)
AFP (Adjusted Function Point)   = UFP × VAF
Effort (person-month)            = AFP / Productivity (조직 평균)
```

GSC (General System Characteristic) 14 인자: 데이터 통신, 분산 처리, 성능, 트랜잭션 비율, 온라인 입력, 사용자 효율성, 온라인 업데이트, 복잡한 처리, 재사용성, 설치 용이성, 운영 용이성, 다중 사이트, 변경 용이성, end-user 효율성.

**사용처**: 대규모 계약 산정(SI 발주), 언어 간 생산성 비교, 정부·금융권 외주 견적, COCOMO 입력값.

**장점**:
- 언어·기술 비종속 → 발주처-수주처 공통 합의 가능
- 요구사항 단계에서 산정 가능 (코드 없이도)
- 역사적 데이터 풍부 (ISBSG 데이터베이스)
- ISO 표준화

**한계·주의**:
- 카운팅에 숙련 필요 (IFPUG 자격증 CFPS)
- 알고리즘 복잡도(수학·AI·실시간) 반영 약함 → COSMIC FP, Mark II FP 등 변종 등장
- Agile 환경에서 user story 와 매핑 모호
- 비기능 요구(성능·보안)는 GSC 로만 보정 → 충분치 않음

**실무 예시** — 단순 회원·주문 시스템:

| 기능 | Type | 복잡도 | UFP |
|---|---|---|---|
| 회원 가입 | EI | Average | 4 |
| 회원 로그인 | EI | Low | 3 |
| 주문 생성 | EI | High | 6 |
| 주문 목록 조회 | EQ | Average | 4 |
| 매출 리포트 | EO | High | 7 |
| 회원 테이블 | ILF | Average | 10 |
| 주문 테이블 | ILF | Average | 10 |
| 결제사 API | EIF | Low | 5 |
| **합계 (UFP)** | | | **49** |
| VAF (GSC 합 40 가정) | | | 1.05 |
| **AFP** | | | **51.45** |

생산성 5 FP/PM 가정 → 51.45 / 5 ≈ **10.3 person-month**.

**관련 기법**: [cocomo-ii](#2-cocomo-ii) (FP 를 입력 size 로 사용), [story-point](#3-story-point) (agile 대체), [reference-class-forecasting](#10-reference-class-forecasting) (ISBSG 외부 기준).

**난이도**: 높음 | **사용 빈도**: ★★★☆☆ (대형 SI / 정부 사업 중심, agile 팀은 낮음)

---

<a id="2-cocomo-ii"></a>
## 2. COCOMO II (Constructive Cost Model)

**정의**: Barry Boehm (USC) 가 1981 년 COCOMO 81 을 발표하고 2000 년 COCOMO II 로 개정한 **파라메트릭 비용 추정 모델**. 코드 규모(KSLOC 또는 FP) 를 입력으로 effort, schedule, staffing 을 산출. 700+ 프로젝트 데이터로 calibration.

**핵심 판단**: FP 가 *규모* 만 본다면 COCOMO II 는 *규모 + 프로젝트 특성* 으로 **effort (person-month)** 를 직접 산출. 모델이 *비선형* — 규모가 2배가 되면 effort 는 보통 2.2~2.5배 (diseconomy of scale).

**3 단계 모델**:

1. **Application Composition** — 초기 prototyping, GUI 빌더 활용 시 (Object Points 사용)
2. **Early Design** — 아키텍처 미정, 거시 추정 (Function Points → KSLOC 변환)
3. **Post-Architecture** — 상세 설계 후 (KSLOC + 17 Effort Multiplier)

**Post-Architecture 공식**:
```
Effort (Person-Month, PM) = A × Size^E × Π(EM_i)

Size = KSLOC (Kilo Source Lines of Code) — FP 에서 변환 가능
A    = 2.94 (calibrated constant)
E    = B + 0.01 × Σ(SF_j),   B = 0.91
SF_j = 5 Scale Factor (각 0~5 점)
EM_i = 17 Effort Multiplier (각 ~0.7 ~ ~1.5)

Schedule (Time-to-Develop, TDEV) = C × Effort^F
C    = 3.67
F    = D + 0.2 × (E - B),   D = 0.28
```

**5 Scale Factor (E 지수에 영향)**:

| 약어 | 의미 |
|---|---|
| PREC | Precedentedness (유사 프로젝트 경험) |
| FLEX | Development Flexibility (요구사항 유연성) |
| RESL | Architecture / Risk Resolution |
| TEAM | Team Cohesion |
| PMAT | Process Maturity (CMMI level) |

**17 Effort Multiplier 카테고리**:
- **Product**: RELY, DATA, CPLX, RUSE, DOCU
- **Platform**: TIME, STOR, PVOL
- **Personnel**: ACAP, PCAP, PCON, APEX, PLEX, LTEX
- **Project**: TOOL, SITE, SCED

**사용처**: 정부 / 항공우주 / 방산 SW 산정, 대규모 프로젝트 ROI 분석, FP 와 결합한 산정.

**장점**:
- 정량적·calibrated 모델 (수십 년 데이터)
- Scale factor / EM 으로 프로젝트 특성 반영
- 일정·인력·비용을 한 모델에서 산출
- COCOMO II tool / USC COCOMO 무료 제공

**한계·주의**:
- KSLOC 입력이 불확실 (역설적 — effort 추정에 size 가 필요)
- Agile / iterative 적합도 낮음 (Boehm 본인이 *Agile COCOMO* 별도 제안)
- EM 추정에 주관 개입
- Diseconomy of scale 가정이 마이크로서비스·모듈 분리에는 과추정

**실무 예시** — 5 KSLOC 중규모 시스템:
```
Size = 5 KSLOC
Scale Factor 합 = 15 (Nominal)
  → E = 0.91 + 0.01 × 15 = 1.06
EM 합 = 1.0 (모두 Nominal)
  → Effort = 2.94 × 5^1.06 × 1.0 ≈ 16.0 PM
  → TDEV  = 3.67 × 16.0^(0.28 + 0.2 × 0.15) ≈ 3.67 × 16.0^0.31 ≈ 8.5 개월
  → 평균 인력 = Effort / TDEV ≈ 1.9 명
```

**FP → KSLOC 변환** (Capers Jones 표 일부):

| 언어 | SLOC / FP |
|---|---|
| Assembly | 320 |
| C | 128 |
| Java | 53 |
| Python / Ruby | 27 |
| SQL | 13 |
| Smalltalk / Lisp | 21 |

**관련 기법**: [function-points](#1-function-points) (입력 size), [reference-class-forecasting](#10-reference-class-forecasting) (calibration 보강), [planning-poker](#4-planning-poker) (agile 대체).

**난이도**: 매우 높음 | **사용 빈도**: ★★☆☆☆ (정부 / 대형 SI 중심)

---

<a id="3-story-point"></a>
## 3. Story Point (Relative Sizing)

**정의**: Mike Cohn (Mountain Goat Software) 가 정립한 **상대 복잡도 추정 단위**. 절대 시간(person-day) 대신 *기준 스토리 대비 몇 배 복잡한가* 로 산정. Fibonacci 수열 (`1, 2, 3, 5, 8, 13, 21, 34, 100`) 사용 — 큰 숫자일수록 불확실성이 빠르게 커진다는 *심리적 비선형성* 반영.

**핵심 판단**: "이건 며칠?" 이 아니라 "이건 다른 스토리 X 대비 몇 배?". 시간은 사람·환경에 따라 다르지만 *상대 복잡도* 는 팀 내 안정적. 시간 환산은 **velocity** (sprint 당 완료 SP) 평균이 자동 수행.

**Fibonacci 사용 이유**:
- 작은 숫자(1, 2, 3) 는 차이가 명확 → 정밀 산정
- 큰 숫자(13, 21) 는 간격이 넓어짐 → "이건 너무 큼" 신호 (split 권장)
- 인접 숫자 (5 vs 8) 사이 갭이 *유의미한 복잡도 차이* 를 강제

**고려 3 차원**:
- **Effort (노력)**: 양 — 얼마나 많은 작업?
- **Complexity (복잡도)**: 인지 부하 — 얼마나 까다로운 알고리즘·통합?
- **Uncertainty (불확실성)**: 모르는 것 — 새 기술, 외부 의존?

**기준 스토리 (Reference Story)**:
팀이 합의한 1 SP 또는 3 SP 짜리 *대표 스토리* 를 보드에 게시. 새 스토리는 항상 기준 대비 비교 — anchor 역할.

**Velocity 공식**:
```
Velocity = 최근 3~5 sprint 완료 SP 의 평균 (또는 median)
예상 완료 sprint 수 = 잔여 backlog SP / Velocity

신뢰구간 (PERT-like):
  Optimistic     = max sprint velocity
  Pessimistic    = min sprint velocity
  Most Likely    = 평균
  3-point estimate = (O + 4M + P) / 6
```

**사용처**: Scrum / SAFe / Kanban backlog 산정, sprint planning, release planning, 팀 capacity 관리.

**장점**:
- 시간 추정 안 함 → 추정 시간 단축 (10~30분 / sprint)
- 팀 합의 도출 → 공유 이해 형성
- Velocity 가 평균화하므로 *개인 능력 차이* 가 자동 보정
- 새 팀원 합류 / 휴가 시 velocity 가 자연 조정

**한계·주의**:
- **팀 간 비교 금지** — A팀 5 SP ≠ B팀 5 SP (상대값이므로)
- 경영진이 SP → 시간 환산을 강요하면 가치 손실 (Goodhart's law)
- 신규 팀은 reference story 정착 전 변동 큼 (3~5 sprint 안정화 필요)
- "Story Point Inflation" — 협상 회피로 점수 부풀리기 발생 가능

**실무 예시** — Sprint Planning (팀 velocity = 25 SP / 2주 sprint):

| Story | 비교 기준 | SP |
|---|---|---|
| 로그인 폼 추가 (기준) | — | 3 |
| 회원가입 + 이메일 인증 | 로그인 2배 + 외부 의존 | 8 |
| 로그인 UI 컬러 변경 | 기준 절반 | 1 |
| 결제 통합 (Stripe) | 큰 외부 의존 + 불확실 | 13 |
| 매출 대시보드 신규 | 다중 화면 + 차트 라이브러리 | 13 |
| **Sprint 합계** | | **38 → 25 로 조정 필요** |

13 SP 두 개 중 하나는 다음 sprint 로 이월 결정.

**관련 기법**: [planning-poker](#4-planning-poker) (SP 합의 도구), [t-shirt-sizing](#5-t-shirt-sizing) (더 거친 추정), [wsjf](#6-wsjf) (SP 를 Job Size 입력으로).

**난이도**: 중간 | **사용 빈도**: ★★★★★ (현대 agile 팀 표준)

---

<a id="4-planning-poker"></a>
## 4. Planning Poker (Wideband Delphi)

**정의**: James Grenning (2002) 이 XP 환경에서 제안하고 Mike Cohn 이 대중화한 **합의 기반 추정 게임**. 팀원 각자가 Fibonacci 카드를 *동시에* 공개해 anchoring effect (먼저 말한 사람에 끌림) 를 회피. 의견 격차가 크면 토론 후 재투표.

**핵심 판단**: 추정 정확도는 **다양한 관점의 합의** 에서 나온다 — Delphi method 의 wideband 변형. 가장 *낙관* 한 사람과 가장 *비관* 한 사람의 격차가 곧 *모르는 영역* 의 크기.

**진행 절차**:

```
1. Product Owner 가 user story 설명
2. 팀이 질문·요구사항 명확화
3. 각자 Fibonacci 카드 1장을 *비공개* 로 선택
4. 동시에 카드 공개 (anchoring 회피)
5. 격차가 크면 (예: 2 vs 13):
   - 최저 추정자: 왜 작다고 봤는가? (잊은 작업은?)
   - 최고 추정자: 왜 크다고 봤는가? (모르는 함정은?)
6. 토론 후 재투표
7. 합의 도달까지 반복 (보통 2~3 라운드)
8. 시간 box (스토리당 2~5분), 초과 시 split 또는 spike 결정
```

**카드 추가 표기**:
- `0` — 이미 끝났거나 trivial
- `1/2` — 매우 작음
- `?` — 정보 부족 (spike 필요)
- `∞` — 너무 커서 split 필요
- ☕ (커피컵) — 휴식 요청

**사용처**: Scrum sprint planning, refinement (grooming) 미팅, SAFe PI Planning, 분산 팀 (Planning Poker 온라인 도구 — Scrum Poker Online, PlanITPoker).

**장점**:
- Anchoring bias 회피 (동시 공개)
- 침묵하는 주니어 의견도 반영 (카드는 평등)
- 합의 과정에서 *요구사항 누락* 발견 (질문 trigger)
- 추정 정확도 ↑ (Cohn 사례 연구: 단일 expert 대비 ±20% 개선)

**한계·주의**:
- 시간 소비 (스토리 30개 산정 = 1~2 시간)
- 팀 규모 7~9명 이상이면 비효율 (의견 폭주)
- 원격에서는 도구 의존 (카드 동시 공개 보장)
- *권위자* 가 있으면 anchoring 재발 (제품 책임자가 먼저 의견 내면 X)

**실무 예시** — 5명 팀, "사용자 비밀번호 재설정" 스토리:

| Round | 멤버 A | B | C | D | E | 토론 |
|---|---|---|---|---|---|---|
| 1 | 3 | 5 | 13 | 5 | 2 | E: "기존 이메일 모듈 재사용" / C: "보안 검증 + rate limit 새로 만들어야" |
| 2 | 5 | 5 | 8 | 5 | 5 | 추가 보안 작업 합의 |
| 3 | 5 | 5 | 5 | 8 | 5 | C: "edge case 우려" → SP 5 + 위험 태그로 합의 |

최종: **5 SP + 위험 노트 "rate limit 외부 통합 확인 필요"**.

**관련 기법**: [story-point](#3-story-point) (Fibonacci 카드 단위), [reference-class-forecasting](#10-reference-class-forecasting) (외부 사례를 토론 자료로), [t-shirt-sizing](#5-t-shirt-sizing) (더 빠른 대안).

**난이도**: 낮음 (운영), 중간 (퍼실리테이션) | **사용 빈도**: ★★★★★

---

<a id="5-t-shirt-sizing"></a>
## 5. T-Shirt Sizing (의류 사이즈 추정)

**정의**: 항목을 `XS / S / M / L / XL / XXL` 6 단계로 분류하는 **초간단 거친 추정** 기법. 숫자가 아닌 *질적* 라벨 — 정밀도 포기 대신 속도 확보. Epic, theme, 분기 로드맵 등 **macro-level** 산정에 사용.

**핵심 판단**: Fibonacci 21 vs 34 를 두고 30분 토론하느니, "L 인가 XL 인가" 한 마디로 분류. 분기 로드맵에 100+ 항목이면 SP 산정은 비현실적 — T-shirt 가 적합.

**라벨 매핑 (팀별 합의)**:

| Size | SP 환산 | Sprint 수 | 의미 |
|---|---|---|---|
| XS | 1~2 | < 1 sprint | trivial, 한 사람 1~2일 |
| S | 3~5 | < 1 sprint | 작은 기능, 한 사람 며칠 |
| M | 5~13 | 1 sprint | 표준 기능, 한 팀 1 sprint |
| L | 13~34 | 1~2 sprint | 큰 기능, split 권장 |
| XL | 34~ | 2~4 sprint | epic, 반드시 split |
| XXL | ∞ | 1+ 분기 | initiative, 별도 디스커버리 필요 |

**사용처**:
- Quarterly roadmap planning
- Pre-PI (Program Increment) sizing in SAFe
- Idea backlog triage (포기할지·정밀 산정할지 판단)
- 영업·기획 단계 *초기* 견적 (계약 전)
- 신기능 prioritization 매트릭스 (RICE / WSJF) 의 effort 입력

**장점**:
- 매우 빠름 (스토리당 30초 이내)
- 비기술 이해관계자도 참여 가능 (숫자 부담 없음)
- 격차가 크게 보이므로 *split 필요성* 즉각 인지 (XL → 여러 M 으로)
- Anchoring 영향 작음 (이산 라벨)

**한계·주의**:
- 정밀도 낮음 — sprint planning 에는 부적합 (반드시 SP 로 재추정)
- 팀마다 라벨 매핑이 다름 → 조직 간 비교 금지
- "L" 과 "XL" 경계가 모호 (15 SP 는 어디?)
- Inflation 위험 (모두 M 이 되면 정보 없음)

**실무 예시** — 분기 로드맵 (40 epic, 4 시간 워크숍):

| Epic | T-shirt | 비고 |
|---|---|---|
| 회원 등급 시스템 신설 | L | 다중 화면 + 배지 + 정책 |
| 다국어 지원 (영·일) | XL | 전 화면 + l10n 파이프라인 |
| 다크 모드 | M | 디자인 토큰 분기 |
| 로그인 페이지 리뉴얼 | S | 디자인만 |
| 보안 감사 대응 | XXL | 전사 영향, discovery 필요 |
| ... | ... | |

XL / XXL 8 건은 **discovery sprint** 로 분리, M·L 32 건만 분기 capacity 에 포함.

**관련 기법**: [story-point](#3-story-point) (T-shirt → SP refinement), [wsjf](#6-wsjf) (T-shirt 를 Job Size 입력으로), [rice-score](#7-rice-score) (Effort 점수 입력).

**난이도**: 매우 낮음 | **사용 빈도**: ★★★★☆

---

<a id="6-wsjf"></a>
## 6. WSJF (Weighted Shortest Job First)

**정의**: Don Reinertsen 의 *flow 경제학* 이 기반이며 SAFe (Scaled Agile Framework) 가 표준 채택한 **우선순위 정량화 공식**. 짧고 가치 큰 작업을 먼저 — 큐 이론의 *최소 지연 비용* 원리.

**핵심 판단**: "중요도" 가 아니라 **"기다리는 시간당 손실"** 로 정렬. 같은 가치라면 짧은 작업이 *시간당 수익률* 높음.

**공식**:
```
WSJF = Cost of Delay (CoD) / Job Size

CoD = User & Business Value + Time Criticality + Risk Reduction & Opportunity Enablement
       (각 항목은 Fibonacci 1, 2, 3, 5, 8, 13, 20 척도)

Job Size = 작업량 (Story Point 합 또는 T-shirt 환산)
```

**3 개 CoD 컴포넌트**:
- **User & Business Value (UBV)** — 완료 시 사용자·매출 가치. "사용자가 얼마나 좋아할까?"
- **Time Criticality (TC)** — 시간이 지나면 가치 감소. 마감, 시즌, 규제 등. "지금 안 하면 의미가 떨어지는가?"
- **Risk Reduction & Opportunity Enablement (RR/OE)** — 기술적 위험 감소 + 다른 기능 가능하게 함. "기반 작업 / 학습 가치"

**WSJF 정규화 절차** (Fibonacci 척도 활용):
1. 각 컴포넌트별로 *상대* 점수만 (가장 작은 것 = 1)
2. 항목 간 비교만 가능 — 절대값 의미 없음
3. WSJF 점수 큰 것부터 처리

**사용처**: SAFe PI Planning 의 backlog 정렬, 분기 로드맵 우선순위, OKR 백로그 정렬, 다중 팀 공유 백로그 조율.

**장점**:
- 정량적 — *왜 이게 먼저인가* 설명 가능
- "급하다"고 외치는 stakeholder 압력 무력화 (TC 항목으로 객관화)
- Job Size 작은 quick win 노출
- 기술 부채·인프라 작업이 RR/OE 로 포함되어 우선순위 진입

**한계·주의**:
- 점수 매기는 사람의 편향 (각 컴포넌트 1~20)
- CoD 컴포넌트 가중치를 동일하게 합산 — 실제로는 도메인별 다를 수 있음
- "Job Size" 가 큰 epic 은 항상 후순위 → split 필요
- 정치적 사용 (점수 조작) 위험

**실무 예시** — 분기 5 epic 우선순위:

| Epic | UBV | TC | RR/OE | CoD | Job Size | WSJF | 순위 |
|---|---|---|---|---|---|---|---|
| 결제 통합 (Stripe) | 13 | 8 | 5 | 26 | 13 | 2.00 | 1 |
| 다크 모드 | 5 | 2 | 3 | 10 | 5 | 2.00 | 1 |
| GDPR 규제 대응 | 8 | 13 | 8 | 29 | 20 | 1.45 | 3 |
| 다국어 (KO/EN/JA) | 8 | 5 | 5 | 18 | 13 | 1.38 | 4 |
| 회원 등급 시스템 | 13 | 5 | 8 | 26 | 20 | 1.30 | 5 |

→ 결제 / 다크 모드 동률 1위, GDPR 은 TC 높지만 Job Size 큰 영향. 다크 모드가 의외로 상위 (작은 Job Size 효과).

**관련 기법**: [cost-of-delay](#8-cost-of-delay) (CoD 직접 활용), [rice-score](#7-rice-score) (대안 공식), [story-point](#3-story-point) (Job Size 입력).

**난이도**: 중간 | **사용 빈도**: ★★★★☆ (SAFe 환경에서 표준)

---

<a id="7-rice-score"></a>
## 7. RICE Score (Reach · Impact · Confidence · Effort)

**정의**: Intercom (Sean McBride, 2017) 가 제품 우선순위 도구로 공개한 **4 인자 합성 점수**. WSJF 가 SAFe / 엔터프라이즈 향이라면 RICE 는 **제품팀·SaaS** 향. "얼마나 많은 사용자에게 (Reach), 얼마나 큰 영향을 (Impact), 얼마나 확신을 갖고 (Confidence), 얼마나 적은 노력으로 (Effort)" 한다.

**공식**:
```
RICE = (Reach × Impact × Confidence) / Effort

Reach        = 일정 기간 영향받는 사용자/이벤트 수 (실수)
                예: 분기당 사용자 수, 월 트랜잭션 수
Impact       = 사용자 1명당 영향 강도 (이산 점수)
                3 = Massive, 2 = High, 1 = Medium, 0.5 = Low, 0.25 = Minimal
Confidence   = 추정 신뢰도 (백분율 → 소수)
                100% = High (데이터 + UX 검증), 80% = Medium, 50% = Low
Effort       = 완료 person-month (또는 SP 환산)
```

**인자 척도**:

| Impact | 점수 | 의미 |
|---|---|---|
| Massive | 3 | 전 사용자 행동 패턴 변화 |
| High | 2 | 핵심 지표 크게 개선 |
| Medium | 1 | 명확한 개선 |
| Low | 0.5 | 작은 개선 |
| Minimal | 0.25 | 거의 미미 |

| Confidence | 점수 | 근거 |
|---|---|---|
| High | 100% | 데이터 + 사용자 테스트 + 유사 사례 |
| Medium | 80% | 데이터 *또는* 사용자 의견 |
| Low | 50% | 직감 / 기획자 가설만 |

**사용처**: 제품팀 quarterly roadmap, A/B 테스트 후보 정렬, feature flag rollout 우선순위, growth experiment backlog.

**장점**:
- Confidence 인자가 *불확실성을 명시적으로 페널티* → 직감 우선순위 견제
- Reach 가 절대수 → 사용자 규모 자동 반영
- WSJF 보다 *제품* 컨텍스트에 직관적 (사용자 수 / 영향 / 확신 / 비용)
- 스프레드시트로 운영 가능

**한계·주의**:
- Impact 척도가 주관적 (Medium vs High 경계)
- Reach 측정이 어려운 신기능 (사용 데이터 없음)
- Confidence 가 50% 미만이면 사실상 spike / discovery 필요 신호
- B2B / enterprise 처럼 사용자 수가 작으면 Reach 가 무의미 — 가중치 변형 필요

**실무 예시** — SaaS 제품 4 기능:

| 기능 | Reach (분기 user) | Impact | Confidence | Effort (PM) | RICE | 순위 |
|---|---|---|---|---|---|---|
| 검색 자동완성 | 50,000 | 2 (High) | 0.8 | 2 | 40,000 | 1 |
| 다크 모드 | 80,000 | 0.5 (Low) | 1.0 | 1 | 40,000 | 1 |
| AI 추천 시스템 | 30,000 | 3 (Massive) | 0.5 | 5 | 9,000 | 4 |
| 다국어 (영·일) | 5,000 | 2 (High) | 1.0 | 3 | 3,333 | 5 |
| 무료 평가판 흐름 개선 | 20,000 | 2 (High) | 0.8 | 1 | 32,000 | 3 |

→ AI 추천은 Massive 라도 Confidence 0.5 페널티 + Effort 큼 → 후순위. 다크 모드가 의외 상위 (낮은 effort + 데이터 확실).

**WSJF vs RICE 비교**:

| 측면 | WSJF | RICE |
|---|---|---|
| 출처 | SAFe / Reinertsen | Intercom |
| 가치 차원 | 3 (UBV / TC / RR) | 2 (Reach / Impact) |
| 불확실성 | 별도 처리 | Confidence 인자 |
| 적합 환경 | 엔터프라이즈 | 제품팀 / SaaS |
| 단위 | 상대 Fibonacci | 절대수 + 상대 |

**관련 기법**: [wsjf](#6-wsjf) (대안 공식), [cost-of-delay](#8-cost-of-delay) (RICE 의 가치 차원), [reference-class-forecasting](#10-reference-class-forecasting) (Confidence 보정).

**난이도**: 중간 | **사용 빈도**: ★★★★★ (제품팀 사실상 표준)

---

<a id="8-cost-of-delay"></a>
## 8. Cost of Delay (CoD — 지연 비용)

**정의**: Don Reinertsen 이 *The Principles of Product Development Flow* (2009) 에서 강조한 **"1주 지연의 화폐 가치 손실"**. 의사결정의 *시간* 차원을 명시적으로 화폐화 — "어차피 다 해야 할 일" 이 아니라 *어느 것을 미루면 가장 손해인가* 를 묻는다.

**핵심 판단**: 모든 의사결정은 *암묵적으로* CoD 를 가정함. 명시화하면 (1) 우선순위가 객관화되고 (2) 더 비싼 사람·자원 투입이 정당화될 수 있다 (CoD 가 인건비를 초과하면 인력 추가).

**공식 (단순)**:
```
CoD (per week) = 1주 늦어졌을 때 기대 손실 (USD / KRW)

CD3 (Cost of Delay Divided by Duration) = CoD / Duration
                                         → WSJF 의 정량 버전
```

**CoD 4 패턴 (Reinertsen)**:

```
1. Urgent (긴급)         ─ 즉시 시작해야, 시간이 지나면 가치 급락
   예: 마감일 있는 규제 대응
   |───┐
   |   └────────── 가치 = 0 이후
   └──────────────→ time

2. Standard (표준)       ─ 일정한 가치, 늦어도 동일 수익
   예: 안정적 SaaS 기능
   |─────────────
   |
   └──────────────→ time

3. Fixed Date (고정일자)  ─ 특정일까지 안 끝나면 0
   예: 블랙프라이데이 캠페인
   |             |
   |             └ 0
   └──────────────→ time

4. Expedite (긴급 통과)   ─ 매우 큰 가치 + 짧은 윈도우
   예: 경쟁사 출시 차단
   |▲
   ||
   ||\___________
   └──────────────→ time
```

**CoD 추정 절차**:
1. 1주 지연 시 손실 항목 나열:
   - 매출 손실 (지연된 출시 → 미실현 수익)
   - 시장점유율 손실 (경쟁사가 먼저)
   - 운영 비용 (구버전 유지 비용)
   - 기회 비용 (다른 기능 못함)
   - 평판 / 고객 이탈
2. 각 항목의 화폐 환산
3. 신뢰구간으로 표시 (low / mid / high)

**사용처**: 우선순위 결정의 *기저* 인자, [wsjf](#6-wsjf) 의 CoD 입력, 인력 추가·외주 결정, 출시일 vs 품질 trade-off 결정.

**장점**:
- 의사결정이 *화폐* 로 비교 가능 (사과 vs 오렌지 ↓)
- 인력 추가가 *수익성* 으로 정당화됨
- 진정한 "긴급" 과 "최근 받은 압력" 구분
- 인터럽트의 *진짜 비용* 노출 ("이 미팅이 1주 지연시키면 $50K")

**한계·주의**:
- 화폐 환산이 어려운 영역 (보안·기술 부채)
- 추정 오차 큼 → 신뢰구간 함께 사용
- 단기 CoD 만 보면 장기 가치 (학습·기반) 무시
- 외부 변수 (경쟁사 출시 시점) 추측

**실무 예시** — 4 기능 CoD:

| 기능 | CoD 시나리오 | 1주 지연 손실 | 패턴 |
|---|---|---|---|
| 결제 통합 (Stripe) | 매출 30% 증가 예상, 월 $100K → 주 $25K | $25,000 / week | Standard |
| 블랙프라이데이 캠페인 | 마감일 후 가치 0, 캠페인 매출 $200K | $50,000 / week (마감 전), $200K (마감 후) | Fixed Date |
| GDPR 규제 대응 | 마감 후 벌금 매출의 4%, $5M | $0 / week → $5M (마감 후) | Fixed Date / Urgent |
| 다크 모드 | 사용자 만족, 이탈 0.5% 감소 → $5K MRR | $1,250 / week | Standard |

→ 블랙프라이데이 + GDPR 은 *마감 전* 까지는 CoD 낮지만 마감 *순간* 폭발. 결제는 매주 $25K 누적.

**관련 기법**: [wsjf](#6-wsjf) (CoD 입력), [rice-score](#7-rice-score) (Impact × Reach 가 CoD 의 근사), [reference-class-forecasting](#10-reference-class-forecasting) (CoD 손실 추정).

**난이도**: 높음 | **사용 빈도**: ★★★☆☆ (사용자 적지만 영향 큼)

---

<a id="9-technical-debt-quadrant"></a>
## 9. Technical Debt Quadrant (Fowler 기술부채 4분면)

**정의**: Martin Fowler 가 *TechnicalDebtQuadrant* (martinfowler.com, 2009) 에서 제시한 **부채 발생 *원인* 의 2×2 분류**. Ward Cunningham 이 처음 비유한 "technical debt" 를 *어떻게 생겼는가* 기준으로 4 유형화 — 같은 부채라도 처방이 다름.

**핵심 판단**: 부채를 *증상* (코드 스멜) 으로 분류하면 처방이 흐려진다. *왜 / 어떻게 생겼는가* 로 분류해야 (1) 책임 추궁이 아닌 *재발 방지* 로 연결되고 (2) *고의 부채* 와 *무지 부채* 의 우선순위가 갈린다.

**2×2 매트릭스**:

```
                    Reckless (무모)              Prudent (신중)
                  ┌─────────────────────────┬─────────────────────────┐
   Deliberate    │  ① 무모 + 의도          │  ② 신중 + 의도          │
   (의도)        │                         │                         │
                 │  "테스트 안 해도 돼,    │  "지금 출시하고          │
                 │   우린 천재야"          │   리팩토링 나중에"       │
                 │                         │                         │
                 │  → 가장 위험             │  → 합리적 거래 (가능)    │
                  ├─────────────────────────┼─────────────────────────┤
   Inadvertent  │  ③ 무모 + 비의도        │  ④ 신중 + 비의도        │
   (비의도)      │                         │                         │
                 │  "Layer 가 뭐예요?"     │  "이제 어떻게 했어야     │
                 │                         │   했는지 알겠다"         │
                 │                         │                         │
                 │  → 교육·코치 필요        │  → 학습의 자연 결과      │
                  └─────────────────────────┴─────────────────────────┘
```

**4 분면 상세**:

**① Reckless + Deliberate (무모 + 의도)** — *"디자인 따위, 시간이 없어"*
- 알면서도 무시. "테스트 작성 시간 없음", "그냥 짜자"
- **가장 해로움** — 빠른 출시 ≠ 빠른 가치 (디버깅 비용 증가)
- 처방: 즉시 중단, 페어 / 코드 리뷰 강제, 팀 문화 개입

**② Prudent + Deliberate (신중 + 의도)** — *"지금 출시해야 함, 리팩토링 빚을 진다"*
- 의식적 trade-off. 시장 검증 우선 + 부채 명시화
- **가장 건강한 부채** — TODO 명시, 백로그 등록, 이자 추적
- 처방: 부채 등록부 (debt register), 갚을 deadline / criteria 설정

**③ Reckless + Inadvertent (무모 + 비의도)** — *"Layer 가 뭐예요?"*
- 무지 + 빠른 진행. 신입·외주·시간 압박 팀에서 발생
- **위험하지만 회복 가능** — 처방은 교육
- 처방: 멘토링, 코드 리뷰, 아키텍처 가이드 문서, 페어

**④ Prudent + Inadvertent (신중 + 비의도)** — *"이제 어떻게 했어야 하는지 알겠다"*
- 출시 후 깨달음. 도메인 학습의 자연 결과
- **불가피한 부채** — 좋은 팀에서도 발생
- 처방: 정기 리팩토링 sprint, 회고에서 패턴 추출, 차기 프로젝트에 반영

**부채 등록부 (Debt Register) 항목**:

| 필드 | 예시 |
|---|---|
| ID | DEBT-042 |
| 분면 | Prudent + Deliberate |
| 설명 | "결제 라이브러리 v1 직접 의존, v2 추상화 미실시" |
| 발생일 | 2025-Q3 |
| 추정 이자 | 매 결제사 추가 시 +3 PD |
| 갚을 조건 | 결제사 3개 이상 통합 시점 |
| 우선순위 | High |
| 담당 | @payment-team |

**사용처**: 회고 (retrospective) 에서 부채 분류, 부채 등록부 관리, 코드 리뷰 PR description, 아키텍처 결정 기록 (ADR) 의 trade-off 섹션.

**장점**:
- 책임 추궁 대신 *원인 분석* 으로 전환
- 의도적 부채를 *합리적* 으로 인정 (모두가 죄책감 X)
- 처방이 분명 (분면별 다른 액션)
- 신규 입사자 교육 자료로 유용

**한계·주의**:
- 자기 분류 편향 (자기 부채를 ② Prudent + Deliberate 로 봄)
- 분면 경계 모호 (③ vs ④)
- 분류만 하고 *상환* 안 하면 무용
- *이자율* 정량화 어려움 (실제 시간 비용 측정 필요)

**관련 기법**: [code-smells.md](code-smells.md) (부채 *증상*), [`refactoring-techniques.md`](refactoring-techniques.md) (부채 *처방*), [iso25010.md#7-maintainability-유지보수성](iso25010.md#7-maintainability-유지보수성) (부채가 영향 주는 품질 차원).

**난이도**: 중간 (분류), 높음 (이자 정량화) | **사용 빈도**: ★★★★☆

---

<a id="10-reference-class-forecasting"></a>
## 10. Reference Class Forecasting (RCF — 외부 사례 기반 예측)

**정의**: Daniel Kahneman & Amos Tversky 가 prospect theory 에서 제시하고 Bent Flyvbjerg (Oxford) 가 거대 인프라 프로젝트에 적용한 **outside view 기법**. 내부 직관 (inside view) 대신 *유사 과거 프로젝트 집합* 의 통계로 보정 — "Planning Fallacy" (낙관 편향) 대응.

**핵심 판단**: 사람은 자기 프로젝트를 **예외** 로 본다 → 항상 낙관. Kahneman: "사람들이 *자기 프로젝트가 평균보다 나을* 거라 믿는 정도가, 실제로 나아지는 정도보다 훨씬 크다". 해결책 — *자기 프로젝트가 평균* 이라고 가정하고 시작.

**3 단계 절차**:

```
1. Reference Class 선정
   유사한 과거 프로젝트 집합을 정의
   예: "지난 3년 우리 회사의 결제 통합 프로젝트 10건"

2. Distribution 산출
   해당 집합의 *실제* 결과 분포 (mean, median, percentile)
   예: 평균 4 PM, p50 = 3 PM, p90 = 8 PM

3. Specific Adjustment
   현재 프로젝트가 평균보다 나을·나쁠 근거가 있는가?
   대부분 없음 → mean 사용. 근거 있을 때만 ±20% 보정
```

**Reference class 데이터 소스**:

| 영역 | 데이터 |
|---|---|
| SW 산정 | ISBSG (International Software Benchmarking Standards Group) — 9000+ 프로젝트 FP·effort |
| 인프라 | Flyvbjerg DB (Oxford) — 11,000+ 메가프로젝트 |
| 사내 | 과거 프로젝트 retrospective 데이터, Jira time tracking, git commit 기록 |
| 공개 | GitHub Issue duration 통계, Stack Overflow developer survey |

**Planning Fallacy 강도** (Flyvbjerg 메가프로젝트 연구):

| 영역 | 비용 초과 | 일정 초과 |
|---|---|---|
| IT 프로젝트 | +27% | +33% |
| 도로 | +20% | +25% |
| 댐 | +96% | +44% |
| 철도 | +45% | +38% |

→ IT 프로젝트도 평균 비용 *27%* / 일정 *33%* 초과 → "내 추정의 1.3배" 가 baseline.

**사용처**: 신규 프로젝트 초기 견적, 사내 1차 산정 보정, 일정 약속 전 sanity check, 경영진 보고용 confidence interval.

**장점**:
- 낙관 편향 자동 보정 (개인 의지 불필요)
- 정량적 — *왜 그 일정인가* 데이터로 답변
- 새 팀원이 즉시 활용 (사내 데이터 베이스 있을 때)
- 다른 추정 기법 (FP / COCOMO / SP) 의 sanity check 역할

**한계·주의**:
- Reference class 정의가 어려움 (유사성 판단 주관)
- 사내 데이터 미비 (작은 회사) → 공개 DB 의존
- *진짜로* 예외적인 프로젝트 (혁신 기술) 에는 reference 없음
- 정치적 저항 — "우리 팀은 다르다" 반발

**실무 예시** — "결제사 통합" 신규 프로젝트:

```
1. Reference class: 지난 2년 결제사 통합 7건 (Stripe / Toss / KakaoPay / NaverPay /
   Inicis / KCP / NicePay)

2. Distribution:
   - mean effort: 4 PM
   - p50 (median): 3 PM
   - p90: 8 PM
   - 평균 일정 초과율: 35%

3. 내부 추정: 2 PM
   외부 보정: median 3 PM × (1 + 35%) ≈ 4 PM
   p90 시나리오 (위험 통신용): 8 PM
```

→ 경영진 보고: "**Median 4 PM, 90% 신뢰구간 [3, 8] PM**" — 단일 숫자가 아닌 *분포* 로 약속.

**3-Point Estimate (PERT) 결합**:
```
Optimistic (O)   = Reference class p10 = 2 PM
Most Likely (M)  = Reference class median = 3 PM
Pessimistic (P)  = Reference class p90 = 8 PM

PERT = (O + 4M + P) / 6 = (2 + 12 + 8) / 6 = 3.67 PM
σ    = (P - O) / 6 = 1.0 PM
95% CI = PERT ± 2σ = [1.67, 5.67] PM
```

**관련 기법**: [function-points](#1-function-points) (ISBSG 데이터), [cocomo-ii](#2-cocomo-ii) (calibration 데이터), [planning-poker](#4-planning-poker) (토론 시 reference 제시), [cost-of-delay](#8-cost-of-delay) (CoD 손실 추정).

**난이도**: 중간 (데이터 있을 때), 높음 (데이터 수집부터) | **사용 빈도**: ★★★☆☆ (정착 시 ★★★★★)

---

## 종합 매트릭스

10 기법의 *언제 사용하나* 한눈 정리.

| 기법 | 단계 | 단위 | 정밀도 | 시간 비용 | 적합 환경 |
|---|---|---|---|---|---|
| Function Points | 요구사항 ~ 설계 | FP | 중상 | 중상 | 대형 SI / 정부 |
| COCOMO II | 설계 | PM | 중 | 높음 | 정부 / 항공우주 |
| Story Point | 백로그 ~ sprint | SP | 중 | 낮음 | 모든 agile 팀 |
| Planning Poker | sprint planning | SP (운영) | 중상 | 중 | Scrum 팀 |
| T-Shirt Sizing | 분기 / epic | XS~XXL | 낮음 | 매우 낮음 | 로드맵 / 분기 |
| WSJF | 우선순위 | 순위 | 중 | 중 | SAFe / 엔터프라이즈 |
| RICE Score | 우선순위 | 순위 | 중 | 중 | 제품팀 / SaaS |
| Cost of Delay | 우선순위 *기저* | 화폐 | 낮음~중 | 중상 | 의사결정 기저 |
| Tech Debt Quadrant | 회고 | 분류 | — | 낮음 | 부채 관리 |
| Reference Class Forecasting | 모든 단계 | 분포 | 높음 (데이터 시) | 중 | sanity check |

## 워크플로우 — 단계별 기법 조합

**Pre-계약 / 초기 견적**:
1. T-Shirt Sizing (분기 로드맵 거친 분류)
2. Function Points (FP 산정)
3. COCOMO II (FP → PM 변환)
4. Reference Class Forecasting (sanity check)

**분기 / Release Planning**:
1. RICE 또는 WSJF (우선순위)
2. Cost of Delay (CoD 명시화)
3. T-Shirt → Story Point refinement

**Sprint Planning**:
1. Planning Poker
2. Velocity 기반 capacity 확인
3. Reference Class Forecasting (팀 평균 velocity)

**회고 / 부채 관리**:
1. Tech Debt Quadrant (분류)
2. 부채 등록부 + 이자 추적
3. Reference Class Forecasting (다음 추정 보정)

## 표준 인용

- ISO/IEC 20926 — Function Points (IFPUG)
- ISO/IEC 25010 — 품질 모델 (사이즈/추정과 별개)
- IEEE SWEBOK v4 — KA11 Software Engineering Economics
- COCOMO II Reference Manual — USC Center for Systems and Software Engineering
- SAFe 6.0 — Weighted Shortest Job First (공식 가이드)
- Boehm, B. (2000). *Software Cost Estimation with COCOMO II*. Prentice Hall.
- Cohn, M. (2005). *Agile Estimating and Planning*. Addison-Wesley.
- Reinertsen, D. (2009). *The Principles of Product Development Flow*. Celeritas.
- Flyvbjerg, B. & Gardner, D. (2023). *How Big Things Get Done*. Currency.
- Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.
- Fowler, M. (2009). "TechnicalDebtQuadrant". https://martinfowler.com/bliki/TechnicalDebtQuadrant.html
- McBride, S. (2017). "RICE: Simple prioritization for product managers". Intercom blog.
- ISBSG — International Software Benchmarking Standards Group. https://www.isbsg.org

## 안티패턴

- **단일 숫자 약속** — 분포 / 신뢰구간 없이 "3 PM 입니다" → planning fallacy 폭발
- **Story Point → 시간 환산 강요** — 경영진이 "1 SP = 1 day" 고정 시 가치 상실
- **팀 간 SP 비교** — A팀 velocity > B팀 → 의미 없음 (상대값)
- **WSJF / RICE 점수 조작** — 통과시키고 싶은 항목 점수 부풀리기 (Goodhart's law)
- **부채 분류만 하고 상환 없음** — Quadrant 워크숍이 회고 의식으로만 남음
- **Inside view 만 사용** — 외부 reference 없이 직감 추정 → 평균 30% 초과
- **CoD 를 매출만으로 환산** — 학습·기반·평판 가치 누락
- **Function Points 인플레이션** — 가중치 임의 상향으로 FP 부풀리기 (감사 필수)
- **T-shirt 가 모두 M** — 분류 의미 없어짐, 정보 손실
- **Reference class 가 너무 좁음 / 넓음** — "마찬가지" 7건 vs "유사" 100건의 적정 균형 필요
