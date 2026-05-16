# Scaled Agile Frameworks (대규모 애자일 프레임워크)

단일 Scrum 팀(5~9 명) 을 넘어서는 **다중 팀 / 다중 ART(Agile Release Train) / 다중 제품군** 단위에서 애자일·린 원칙을 유지하는 프레임워크 모음. "팀이 늘어나면 의사소통 채널이 n(n-1)/2 로 폭발한다" 는 Brooks 의 *Mythical Man-Month* 명제를 어떻게 구조적으로 흡수할지에 대한 서로 다른 답이다.

본 문서는 6 개 프레임워크 (SAFe / LeSS / Nexus·Scrum@Scale / Spotify Model / Disciplined Agile / Team Topologies) 를 각각 **창시자·도입 시점 → 구조 → 도입 사례 → 비판/한계** 순으로 정리하고, 끝에 **선택 매트릭스** 를 제공한다.

**원전**:
- Dean Leffingwell, *SAFe Reference Guide* (Scaled Agile, Inc., 2011~), https://scaledagileframework.com
- Craig Larman & Bas Vodde, *Large-Scale Scrum: More with LeSS* (Addison-Wesley, 2016), https://less.works
- Ken Schwaber, *The Nexus Guide* (Scrum.org, 2015~), https://scrum.org/resources/nexus-guide
- Jeff Sutherland, *Scrum@Scale Guide* (Scrum Inc., 2018~), https://scrumatscale.com
- Henrik Kniberg & Anders Ivarsson, *Scaling Agile @ Spotify with Tribes, Squads, Chapters & Guilds* (white paper, 2012)
- Mark Lines & Scott Ambler, *Choose Your WoW! A Disciplined Agile Delivery Handbook* (PMI, 2022 ed.)
- Matthew Skelton & Manuel Pais, *Team Topologies: Organizing Business and Technology Teams for Fast Flow* (IT Revolution, 2019)

> 관련 문서: [sdlc-models](./sdlc-models.md), [evolutionary-arch](./evolutionary-arch.md), [patterns/architectural](../patterns/architectural.md), [process-metrics](./process-metrics.md).

---

<a id="safe-framework"></a>
## 1. SAFe (Scaled Agile Framework)

**창시자 / 시점**: Dean Leffingwell, 2011 년 v1.0 공개 → 2025 년 현재 v6.0. Scaled Agile, Inc. 가 트레이드마크 보유 + 유료 인증(SPC / SA / SSM / SP) 발급.

**기본 명제**: "Agile 은 팀 레벨, Lean 은 흐름(flow) 레벨, Systems Thinking 은 솔루션 레벨." Scrum + XP + Kanban + Lean Product Development + DevOps 를 **4 단계 Configuration** 으로 묶어 엔터프라이즈 전체에 적용한다.

### 1.1 4 단계 Configuration (Essential → Large Solution → Portfolio → Full)

| 단계 | 범위 | 핵심 추가 요소 | 적합한 조직 규모 |
|------|------|--------------|---------------|
| **Essential** | 1 ART (50~125 명) | ART, PI Planning, System Demo, Inspect & Adapt | 단일 제품 |
| **Large Solution** | 다중 ART 1 솔루션 | Solution Train, Solution Architect, Capabilities | 항공/자동차/방산 |
| **Portfolio** | 가치 흐름 전체 | Lean Portfolio Management, Epics, Strategic Themes | 다중 제품군 |
| **Full** | 전사 | 위 3 단계 전부 + Government 영역 | 글로벌 엔터프라이즈 |

**핵심 판단**: ART (50~125 명, 보통 5~12 팀) 단위로 동기화된 PI(Program Increment, 8~12 주) 를 운영할 수 있는가? 모든 팀이 같은 cadence 로 PI Planning 에 모이는가? 의존성 보드(ROAM: Resolved/Owned/Accepted/Mitigated) 가 가시화되는가?

### 1.2 ART (Agile Release Train)

- **정의**: "Long-lived team of Agile teams" — 5~12 개 Scrum/Kanban 팀이 같은 비전·로드맵·릴리스 케이던스로 묶인 가상 조직.
- **역할**: Release Train Engineer (RTE, Chief Scrum Master), Product Management (Product Owner 들의 위), System Architect/Engineer, Business Owners.
- **이벤트**: PI Planning (2 일), ART Sync (주 1 회 SoS + PO Sync), System Demo (PI 끝), Inspect & Adapt (PI 회고 + 문제 해결 워크숍).

### 1.3 PI Planning (Program Increment Planning)

8~12 주 단위 페이스메이커 이벤트. 2 일에 걸쳐:
- Day 1: Business Context → Product Vision → Architecture Vision → Planning Context → 팀별 Breakout (1 차)
- Day 2: Breakout (2 차) → Draft Plan Review → Management Review → Final Plan Review → Confidence Vote (fist of five)

**산출물**: Team PI Objectives, Program Board (의존성 + 마일스톤), Risks (ROAMed).

```text
# PI Planning 결과 시각화 예 (Program Board)
Sprint  | Team-A           | Team-B           | Team-C           | Milestone
--------|------------------|------------------|------------------|----------
PI.S1   | Feature X (1)    | API contract (2)→Team A | UI shell    | -
PI.S2   | Feature X (2)    | Feature Y (1)    | UI integration   | Beta cut
PI.S3   | Refactor         | Feature Y (2)    | Perf tuning      | -
PI.S4   | Feature Z        | Feature Y (3)    | A/B test         | -
PI.S5   | Hardening (IP)   | Hardening (IP)   | Hardening (IP)   | PI Release
```

### 1.4 도입 사례

- **금융**: Capital One, Fidelity, ING, BMW Bank — 컴플라이언스·감사 추적성 요건이 SAFe Portfolio Kanban + WSJF 우선순위와 잘 맞음.
- **국방/항공**: Lockheed Martin, Northrop Grumman, Airbus — 다중 ART · 하드웨어 통합 시간축이 PI cadence 와 정합.
- **통신**: Telstra, AT&T — 다중 제품군 + 외주 비율 높음.

### 1.5 비판 / 한계

- **무게**: 가장 무거운 프레임워크. "Agile-by-the-book" 으로 변질 위험.
- **사전 정의된 역할의 과다**: RTE, STE, Solution Architect, Business Owner 등 — 작은 조직엔 과잉.
- **Cargo Cult 위험**: 컨설팅사 주도 도입 시 *프로세스만 도입* 하고 Lean 사고는 빠짐. *"SAFe-washing"* 비판 (Ron Jeffries, Martin Fowler 등 — XP 진영의 강한 비판).
- **PI 케이던스의 경직성**: 8~12 주 고정 → 진짜 emergent design 어려움. 시장 변화 빠른 SaaS 에 부적합.
- **인증 비즈니스 의존**: Scaled Agile, Inc. 의 트레이닝 매출이 본질. 컨설팅 시장이 프레임워크를 떠받침.

**난이도**: 매우 높음 | **사용 빈도**: ★★★★☆ (대형 엔터프라이즈)

**관련 원칙 / 패턴**: [sdlc-models](./sdlc-models.md), [evolutionary-arch](./evolutionary-arch.md), Lean Portfolio Management, WSJF (Weighted Shortest Job First).

---

<a id="less-large-scale-scrum"></a>
## 2. LeSS (Large-Scale Scrum)

**창시자 / 시점**: Craig Larman & Bas Vodde, 2005 년 Nokia Networks 경험에서 출발 → 2013 *Practices for Scaling Lean & Agile Development* / 2016 *Large-Scale Scrum: More with LeSS*.

**기본 명제**: "Scrum 을 *확장* 하는 게 아니라 *원본 Scrum 을 더 많은 팀에 적용* 한다 — Less is more." 추가 역할 / 추가 이벤트를 최소화. **하나의 제품, 하나의 Product Owner, 하나의 Product Backlog, 하나의 Definition of Done, 하나의 잠재적 출하 가능한 Increment**.

### 2.1 2 단계 Configuration

| 단계 | 팀 수 | 추가 요소 |
|------|------|----------|
| **Basic LeSS** | 2~8 팀 (~50 명) | Sprint Planning One/Two, Overall Retrospective, Multi-Team PBR |
| **LeSS Huge** | 8 팀 초과 (수백~수천 명) | Requirement Area (RA), Area Product Owner (APO) |

### 2.2 LeSS 의 핵심 이벤트

- **Sprint Planning One**: 모든 팀의 대표 + PO 가 함께 PBI 를 팀에 배분. 한 팀에 하나의 PBI 가 아니라 **여러 팀이 같은 PBI 에 협업** 가능 (feature team 원칙).
- **Sprint Planning Two**: 각 팀 내부 — 일반 Scrum 과 동일.
- **Daily Scrum 후 Scout**: 다른 팀의 Daily 에 *옵저버* 로 참석하여 의존성 흡수.
- **Sprint Review**: *Bazaar 형식* — 마켓 부스처럼 팀별 데모.
- **Overall Retrospective**: PO + 모든 SM + 팀 대표 — 전체 시스템 개선.

### 2.3 Feature Team (LeSS 의 정수)

| Component Team | Feature Team (LeSS 주장) |
|---------------|-------------------------|
| 한 컴포넌트 (UI / API / DB) 에 종속 | 고객 가치 1 개를 처음부터 끝까지 |
| 의존성 폭증, 부분 최적화 | end-to-end 책임, 시스템 최적화 |
| Conway's Law 의 *희생자* | Conway 역으로 활용 (Inverse Conway Maneuver) |

### 2.4 도입 사례

- **JP Morgan Chase**: 70+ 팀, 2015~ LeSS Huge.
- **BMW Group IT**: 일부 도메인.
- **Bose**, **Cisco** 일부 BU, **Booking.com** 초기 일부 트라이브.

### 2.5 비판 / 한계

- **PO 1 인 부담**: 8 팀 = 70+ 명을 1 PO 가 우선순위 결정 → *현실적으로 불가능* 비판.
- **Feature Team 전제의 어려움**: 레거시 모놀리식 + 컴포넌트 팀 조직을 feature team 으로 재편하는 *조직 수술* 이 전제. 1~2 년의 통증.
- **LeSS Huge 의 모호성**: 8 팀 초과 시 Area 구분이 결국 SAFe ART 와 비슷해진다는 비판.
- **확장 가이드의 빈약**: SAFe 대비 *너무 적게 지시* → 컨설팅·내재화 의존도 높음.

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**관련 원칙 / 패턴**: [sdlc-models](./sdlc-models.md), Conway's Law, Inverse Conway Maneuver, [evolutionary-arch](./evolutionary-arch.md).

---

<a id="nexus-scrum-at-scale"></a>
## 3. Nexus / Scrum@Scale / Scrum of Scrums / FAST Agile (4 비교)

Scrum 의 *공식적 확장* 트랙 3 개 + 그래스루트 1 개. 모두 "Scrum 본체를 거의 그대로 두고 협업 레이어를 더한다" 는 공통 철학.

### 3.1 Nexus (Scrum.org / Ken Schwaber, 2015)

- **범위**: 3~9 개 Scrum 팀이 *하나의 통합된 Increment* 산출.
- **추가 요소**: Nexus Integration Team (NIT), Nexus Sprint Planning, Nexus Daily Scrum, Nexus Sprint Review, Nexus Sprint Retrospective, Nexus Sprint Backlog.
- **공식 출처**: *The Nexus Guide* (Scrum.org, 2021 개정).
- **특징**: PSK / PSM 와 일관된 어휘. NIT 가 통합 책임 + 코칭.

### 3.2 Scrum@Scale (Scrum Inc. / Jeff Sutherland, 2018)

- **범위**: 무제한 (이론상 회사 전체).
- **핵심 모델**: **Scrum of Scrums (SoS)** + **Executive Action Team (EAT)** + **Executive MetaScrum (EMS)** — 두 개의 사이클(How vs What) 을 별도로 운영.
  - SoS / Scrum of Scrum of Scrums (SoSoS) → SM 사이클 (How — 장애물 제거)
  - MetaScrum / EMS → PO 사이클 (What — 우선순위)
- **5 가지 Scaling Components**: Team-Level Process, SoS, EAT, MetaScrum, EMS.

### 3.3 SoS (Scrum of Scrums) — 가장 오래된 패턴

- **출처**: Jeff Sutherland 가 1996 IDX Systems 에서 처음 적용. 어떤 프레임워크에도 들어가는 *원시 패턴*.
- **형식**: 각 팀에서 SM(또는 대표) 1 명 → 주 2~3 회 15~30 분 회의 → 의존성 / 통합 / 장애물 공유.

### 3.4 FAST Agile (Fluid Scaling Technology)

- **창시자**: Ron Quartel, 2017~. ~600 명 보험사 컨설팅에서 출발.
- **핵심**: *고정 팀 없음*. 2 주마다 "Marketplace" 에서 자율적으로 팀을 재구성. Tribes 와 Stewards 만 영속.
- **특징**: 가장 *Open Space Technology* 적. Spotify 가 폐기하는 방향의 극단적 버전.

### 3.5 4 프레임워크 비교

| 항목 | Nexus | Scrum@Scale | SoS | FAST |
|------|-------|------------|-----|------|
| 권위 출처 | Scrum.org | Scrum Inc. | (패턴) | Ron Quartel |
| 팀 수 한도 | 3~9 | 무제한 | 무제한 | 무제한 |
| 추가 역할 | NIT | EAT, EMS | - | Steward |
| Increment 통합 | NIT 책임 | 각 팀 + SoS | 비공식 | Marketplace 재조정 |
| 인증 | SPS | SaS Practitioner | - | (없음) |
| 적합한 맥락 | 단일 제품 중간 규모 | 전사 + 임원층 가시화 필요 | 임시 확장 | 변동성 매우 큰 R&D |

**난이도**: 중간 (Nexus/SoS) ~ 높음 (Scrum@Scale) | **사용 빈도**: ★★★☆☆

**관련 원칙 / 패턴**: [sdlc-models](./sdlc-models.md), [team-topologies](#team-topologies), Open Space Technology.

---

<a id="spotify-model"></a>
## 4. Spotify Model (역사적 정확성 포함)

**창시자 / 시점**: Henrik Kniberg & Anders Ivarsson, 2012 년 white paper *"Scaling Agile @ Spotify with Tribes, Squads, Chapters & Guilds"* 공개. **주의**: 이 문서는 "처방(prescription)" 이 아니라 *2012 년의 스냅샷* 으로 의도되었다.

### 4.1 4 가지 조직 단위

| 단위 | 정의 | 평균 크기 | 책임 |
|------|------|---------|------|
| **Squad** | 자율 cross-functional 팀 (Scrum 팀과 유사) | 6~12 명 | 미션 영역의 end-to-end |
| **Tribe** | 관련 Squad 들의 집합 | 40~150 명 | 같은 비즈니스 영역 (Dunbar's number) |
| **Chapter** | 같은 직군이 가로지르는 라인 | 5~10 명 | 기술 표준, 평가, 1on1 |
| **Guild** | 관심사 기반 자유 커뮤니티 | 자유 | 지식 공유 (Lunch & Learn) |

```text
Tribe (Music Player)
├─ Squad A (재생) ──┐
├─ Squad B (큐) ────┤── Chapter: Frontend (cross-squad line manager)
├─ Squad C (오프라인) ┘── Chapter: Backend
└─ Squad D (라이브러리)

Guild: Web Performance Guild (전사, 누구나 참여 가능)
```

### 4.2 핵심 원칙

- **Servant Leadership**: 매니저 = Chapter Lead = 코치 + 1on1.
- **Squad 의 자율성**: 도구·프로세스·릴리스 주기 모두 자율.
- **Loosely coupled, tightly aligned**: 정렬은 미션·OKR, 결합은 최소.
- **Failure recovery > failure avoidance**: 안전한 실패 환경.

### 4.3 역사적 정확성 — "Spotify 가 폐기한 사실"

**가장 중요한 사실**: *Spotify 자신도 더 이상 "Spotify Model" 을 그대로 쓰지 않는다*. 그러나 외부에서는 여전히 가장 인기 있는 비공식 프레임워크.

근거가 되는 발언 / 사례:
- **Joakim Sundén** (전 Spotify Agile Coach, 2017 GOTO Berlin): "We never had it as we described it. The white paper described the *aspirations*, not the *reality*."
- **Henrik Kniberg** (2024 인터뷰, *Lean Enterprise Institute*): "I regret naming it a 'model.' It was a snapshot. People copied the structure but missed the culture."
- **Jeremiah Lee** (전 Spotify PM, 2020 *jeremiahlee.com* 블로그 "Failed #SquadGoals"): "Cross-squad collaboration didn't scale. We had de facto matrix management. Chapters became weak."
- 2017~2019 사이 Spotify 는 **Mission > Tribe / Bet > Squad** 개념으로 점진 이행. 2022~ 는 더 큰 **Mission / Initiative** 구조로 재편.

### 4.4 도입 사례 (외부)

- **ING Bank** (네덜란드): 2015~ 본사 IT 전면 도입. 가장 큰 성공 사례로 자주 인용. 다만 ING 도 점진적 변형 적용.
- **Pets at Home, LEGO Digital, JP Morgan 일부 BU**.
- **Bosch, SAP, Volvo** 부분 도입.

### 4.5 비판 / 한계

- **"Spotify 가 안 쓰는 모델"**: 가장 큰 아이러니. 원본 paper 가 *목표가 아닌 처방* 처럼 소비됨.
- **Chapter Lead 의 모호한 권위**: line manager 인지 멘토인지 불명확 — Jeremiah Lee 의 회고에서 핵심 문제로 지적.
- **의존성 관리 부재**: SAFe 같은 명시적 PI Planning 이 없어 squad 간 의존성이 *암묵적* 처리.
- **Guild 의 자발성 함정**: 의무화하면 Guild 가 아니고, 자발에 맡기면 시들어 사라짐.
- **인용 편향 (Cargo Culting)**: 이미 *Spotify-shaped* 인 조직만 흉내 가능. 전통 기업이 도입하면 *이름만 squad* 인 매트릭스로 변질.

**난이도**: 중간 (구조) / 매우 높음 (문화) | **사용 빈도**: ★★★★☆ (대중적이나 정확한 도입은 드묾)

**관련 원칙 / 패턴**: [team-topologies](#team-topologies), Servant Leadership, Conway's Law.

---

<a id="disciplined-agile"></a>
## 5. Disciplined Agile (DA / DAD)

**창시자 / 시점**: Scott Ambler & Mark Lines, 2009 년 *Disciplined Agile Delivery (DAD)* 출발 → 2019 PMI 가 인수 → 2022 *Choose Your WoW! 2nd ed.* 출판.

**기본 명제**: "There is no one-size-fits-all in agile. Choose your Way of Working (WoW)." — 단일 프레임워크가 아닌 **goal-driven 의사결정 hybrid toolkit**. Scrum / XP / Kanban / SAFe / LeSS / Spotify 의 실천을 *상황에 맞게 조합* 한다.

### 5.1 DA 4 Layers

| Layer | 범위 | 내용 |
|-------|------|------|
| **Foundation** | 마인드셋 | DA Mindset (8 principles, 7 promises, 8 guidelines) |
| **Disciplined DevOps** | 운영 | 빌드/배포/보안/데이터 관리 |
| **Value Stream** | 가치 흐름 | Lean Portfolio Management, Strategy |
| **Disciplined Agile Enterprise** | 전사 | 마케팅, HR, 재무까지 |

### 5.2 4 Lifecycles (선택 가능)

DA 의 가장 큰 특징은 **프로젝트 성격에 따라 lifecycle 을 고르는 것**:

| Lifecycle | 적합 상황 | 기반 |
|-----------|---------|------|
| **Agile** | 명확한 요구 + 안정 팀 | Scrum 기반 + 추가 가이드 |
| **Lean** | 빠른 흐름 + 작은 단위 | Kanban 기반 |
| **Continuous Delivery: Agile** | 성숙한 팀 + 자동화 | Scrum + CD |
| **Continuous Delivery: Lean** | 최고 성숙도 | Kanban + CD |
| **Exploratory** (별도) | 신제품 발견 | Lean Startup + Hypothesis |
| **Program** (별도) | 다중 팀 큰 솔루션 | LeSS / SAFe 와 유사 |

### 5.3 Process Goals (21 개)

DAD 는 **"How to do X?"** 질문에 대한 의사결정 차트(decision tree) 제공:
- Inception: *Form Initial Team*, *Identify Architecture Strategy*, *Develop Initial Release Plan*, …
- Construction: *Produce a Potentially Consumable Solution*, *Improve Quality*, …
- Transition: *Deploy the Solution*, *Release Management*, …

각 goal 마다 *선택지 + 트레이드오프* 가 카드 형태로 제공 — *해야 한다* 가 아니라 *고를 수 있다*.

### 5.4 도입 사례

- **PMI** 자체 (PMI 가 인수했으므로 dogfooding).
- **IBM** (Scott Ambler 가 IBM Rational 출신 → 일부 컨설팅 자산 흡수).
- **금융권**: Royal Bank of Scotland, Barclays 일부.
- 도입이 *눈에 띄지 않는* 이유: 다른 프레임워크와 섞여 *meta-framework* 로 쓰이기 때문.

### 5.5 비판 / 한계

- **무거움 + 학습 곡선**: 21 process goals × 다중 선택지 = 인지 부담. *"choose your WoW"* 자체가 선택 마비.
- **컨설팅 / PMI 자격증 의존**: DASM / DASSM / DAC 인증 사업이 본질에 가까움.
- **차별점의 모호함**: Scrum + Kanban 을 안다면 굳이 DA 가 필요한가? — 자주 나오는 의문.
- **커뮤니티 작음**: SAFe / Scrum 대비 컨퍼런스·블로그·예제 규모 1~2 자릿수 작음.

**난이도**: 매우 높음 | **사용 빈도**: ★★☆☆☆

**관련 원칙 / 패턴**: [sdlc-models](./sdlc-models.md), Hybrid Agile, [process-metrics](./process-metrics.md).

---

<a id="team-topologies"></a>
## 6. Team Topologies

**창시자 / 시점**: Matthew Skelton & Manuel Pais, 2019 *Team Topologies: Organizing Business and Technology Teams for Fast Flow* (IT Revolution Press). 이후 *Team Topologies Academy* 운영.

**기본 명제**: "팀을 *프로젝트* 단위가 아니라 *흐름(flow)* 단위로 구성하라. Conway's Law 를 *피하지 말고 의도적으로 활용* 하라 (Inverse Conway Maneuver)." 프레임워크라기보다 *조직 디자인 언어*.

### 6.1 4 가지 팀 유형 (Fundamental Team Topologies)

| 팀 유형 | 책임 | 인지 부하 | 예시 |
|--------|------|---------|------|
| **Stream-aligned Team** | 가치 흐름 1 개 end-to-end | High | 결제 팀, 검색 팀, 추천 팀 |
| **Platform Team** | 내부 플랫폼 product (self-service) | Medium | DevEx, K8s Platform, Data Platform |
| **Enabling Team** | 한시적 코칭 (다른 팀 역량 강화) | Low | SRE 코칭, 보안 코칭, Testing 코칭 |
| **Complicated-Subsystem Team** | 깊은 전문성 필요 영역 | High (전문성) | 코덱, ML 모델, 실시간 거래 엔진 |

**가장 중요한 비율**: 전형적 조직에서 **Stream-aligned ≥ 70%** 이고 나머지 3 종은 보조. 모두 Stream-aligned 팀의 *흐름을 빠르게 만들기 위해* 존재.

### 6.2 3 가지 Interaction Modes

| 모드 | 정의 | 기간 | 시각화 |
|------|------|------|--------|
| **X-as-a-Service** | 제공자가 product 처럼 service 제공 | 장기 (영구) | Platform → Stream |
| **Collaboration** | 두 팀이 일정 기간 같이 일함 | 단기 (수주~수개월) | Stream ↔ Complicated-Subsystem |
| **Facilitating** | 한 팀이 다른 팀의 학습을 도움 | 단기 (한정) | Enabling → Stream |

**원칙**: 같은 두 팀이 동시에 여러 모드일 수 없다. 모드는 *명시적이고 일시적* 이어야 함.

### 6.3 인지 부하 (Cognitive Load) — Team Topologies 의 가장 큰 기여

- 출처: John Sweller 의 *Cognitive Load Theory* (1988) 를 팀 단위로 확장.
- 3 가지 부하: **Intrinsic** (기술 자체) + **Extraneous** (환경 / 도구) + **Germane** (학습 / 도메인 진짜 일).
- **팀의 인지 한계** 를 *조직 설계 제약* 으로 인정 → 책임 영역 / Platform 추상화 수준의 의사결정 근거.

```text
인지 부하 진단 (1~5 척도, 팀별)
- 우리 팀이 책임지는 도메인 수: 1(단일) ~ 5(많음)
- 우리 팀이 사용해야 하는 도구 / 플랫폼 수: 1(소수) ~ 5(다수)
- 도메인 변경 빈도: 1(안정) ~ 5(매주)
→ 합계 9+ : 인지 과부하 위험. 책임 분리 또는 Platform 추상화 필요.
```

### 6.4 Inverse Conway Maneuver (역 Conway 기동)

- **Conway's Law** (1968): "Organizations design systems that mirror their communication structure."
- **Inverse Conway**: 원하는 *아키텍처를 먼저 결정* → 그 아키텍처가 자연스럽게 나오도록 *조직을 재편*.
- 예: 마이크로서비스 아키텍처를 원함 → 컴포넌트팀(UI/DB/API 분리) 을 stream-aligned (서비스별) 로 재편.

### 6.5 도입 사례

- **uSwitch (영국 비교 쇼핑)**: 저자 Manuel Pais 의 사례. Stream-aligned + Platform 전환.
- **Hibri Marzook / Cloud Native Foundation 자료**: AstraZeneca, Sky Betting.
- **Spotify 의 후기 진화** 가 Team Topologies 와 매우 유사한 방향: Mission → Stream-aligned, Platform Tribes → Platform Teams.

### 6.6 비판 / 한계

- **프레임워크가 아닌 어휘**: 구체적 *프로세스* 없음 → SAFe / Scrum 과 *조합* 해야 함. 단독으로 "Team Topologies 도입" 이라 말하기 어려움.
- **Platform Team 의 함정**: 사용자(stream-aligned) 가 *고객* 임을 잊고 *통제자* 가 되면 platform 이 *Centralized IT* 로 회귀.
- **인지 부하 측정의 주관성**: 정량 지표가 부족.
- **조직 변혁 비용**: 4 유형으로 매핑하면 *Component Team 해체* 가 필연 → LeSS 와 같은 통증.

**난이도**: 중간 (개념) / 매우 높음 (조직 변혁) | **사용 빈도**: ★★★★☆ (최근 5 년 가장 빠르게 확산)

**관련 원칙 / 패턴**: [evolutionary-arch](./evolutionary-arch.md), [patterns/architectural](../patterns/architectural.md), Conway's Law, [sdlc-models](./sdlc-models.md), DDD Bounded Context.

---

## 선택 매트릭스 — 어떤 프레임워크를 고를까?

| 차원 | SAFe | LeSS | Nexus / Scrum@Scale | Spotify Model | Disciplined Agile | Team Topologies |
|------|------|------|---------------------|--------------|------------------|----------------|
| **권장 팀 수** | 5~12 팀/ART, 다중 ART | 2~8 (Basic), 8+ (Huge) | 3~9 / 무제한 | 임의 (Tribe ≤ 150) | 무제한 (선택 가능) | 임의 (어휘) |
| **권장 인원** | 50~수천 | 50~수백 | 30~수백 | 임의 | 임의 | 임의 |
| **복잡도** | 최고 | 중-상 | 중 / 중-상 | 중 (구조) / 매우 높음 (문화) | 매우 높음 | 중 |
| **규제 / 컴플라이언스** | ★★★★★ (가장 적합) | ★★★ | ★★★ | ★★ | ★★★★ | ★★★ |
| **빠른 시장 변화** | ★★ (PI 경직) | ★★★★ | ★★★★ | ★★★★★ | ★★★★ | ★★★★★ |
| **임원 가시화** | ★★★★★ | ★★★ | ★★★★ (Scrum@Scale) | ★★ | ★★★★ | ★★★ |
| **기존 컴포넌트 팀 적합** | ★★★★ | ★ (재편 필수) | ★★★ | ★★ | ★★★ | ★ (재편 필수) |
| **인증/공식성** | ★★★★★ (유료) | ★★★ | ★★★★ (Scrum.org/Inc.) | ★ (비공식) | ★★★★ (PMI) | ★★ (책 + 아카데미) |
| **컨설팅 시장 규모** | 매우 큼 | 중 | 큼 (Scrum 본가) | 작음 | 중 | 빠른 성장 |
| **다른 프레임워크와 조합** | 가능 (Lean Portfolio + Scrum) | 어려움 (순혈) | 쉬움 | 어려움 (문화 종속) | 매우 쉬움 (toolkit) | 매우 쉬움 (어휘) |
| **가장 적합한 산업** | 금융 / 항공 / 방산 / 통신 | 통신 / 임베디드 | 일반 IT | 디지털 / SaaS | 컨설팅 / 다국적 | 디지털 / 플랫폼 비즈니스 |

### 의사결정 흐름

```text
시작
├─ 팀 ≤ 1 ? → 그냥 Scrum / XP / Kanban (이 문서 범위 밖)
├─ 팀 2~8 + 단일 제품 ? 
│   ├─ 순수 Scrum 고수 → LeSS Basic
│   ├─ 점진 도입 → Nexus
│   └─ 가벼운 패턴만 → SoS
├─ 팀 5~12 + 강한 규제 / 임원층 가시화 필요 ? → SAFe Essential
├─ 다중 ART / 솔루션 / 포트폴리오 ? → SAFe Large Solution / Portfolio
├─ 디지털 + 자율 문화 + 작은 인지 부하 ? → Team Topologies + Spotify-inspired (단, *복사* 금지)
├─ 임원 + 팀 양쪽 사이클 분리 필요 ? → Scrum@Scale
└─ 상황별로 다 다름 ? → Disciplined Agile (toolkit)
```

> **참고**: 가장 흔한 *현실의 답* 은 **Team Topologies (어휘) + SAFe 또는 LeSS (프로세스) + Scrum/Kanban (팀 레벨) 의 하이브리드**.

---

## 안티 패턴 / 공통 함정

| 안티 패턴 | 증상 | 처방 |
|---------|------|------|
| **Cargo Cult Scaling** | 이벤트·역할만 도입, 흐름 측정 없음 | 흐름 메트릭(Lead Time, WIP) 부터 |
| **Framework 종교화** | 프레임워크 *옹호* 가 목표가 됨 | retrospective 에서 프레임워크 자체를 비판 가능하게 |
| **PI Planning 마라톤** | 2 일 회의가 *연극* | Confidence Vote 가 4 이하면 *재계획*, 형식 회의화 차단 |
| **Squad 의 자율성 신화** | Squad 마다 다른 기술 스택 → 사일로 | Chapter / Platform Team 이 표준 제공 |
| **Platform Team 의 ivory tower** | 사용자(Stream-aligned) 의 피드백 무시 | platform 도 *product* — DevEx 메트릭 (DORA + SPACE) |
| **무한 Guild / Chapter 회의** | 매일 회의, 코드 못 씀 | 회의 시간 cap, Guild 는 자발성 보장 |

---

## 표준 인용

- Leffingwell, D. *SAFe Reference Guide 6.0*. Scaled Agile, 2024. https://scaledagileframework.com
- Larman, C. & Vodde, B. *Large-Scale Scrum: More with LeSS*. Addison-Wesley, 2016. https://less.works
- Schwaber, K. *The Nexus Guide*. Scrum.org, 2021. https://scrum.org/resources/nexus-guide
- Sutherland, J. *The Scrum@Scale Guide*. Scrum Inc., 2022. https://scrumatscale.com
- Kniberg, H. & Ivarsson, A. *Scaling Agile @ Spotify with Tribes, Squads, Chapters & Guilds*. 2012.
- Lee, J. "Failed #SquadGoals: Spotify doesn't use the Spotify Model and neither should you." 2020. https://www.jeremiahlee.com/posts/failed-squad-goals/
- Sundén, J. "There Is No Spotify Model." GOTO Berlin, 2017.
- Ambler, S. & Lines, M. *Choose Your WoW! A Disciplined Agile Delivery Handbook for Optimizing Your Way of Working*. 2nd ed. PMI, 2022.
- Skelton, M. & Pais, M. *Team Topologies: Organizing Business and Technology Teams for Fast Flow*. IT Revolution, 2019. https://teamtopologies.com
- Conway, M. "How Do Committees Invent?" *Datamation*, 1968.
- Brooks, F. *The Mythical Man-Month*. Addison-Wesley, 1975.
- Sweller, J. "Cognitive Load During Problem Solving." *Cognitive Science*, 1988.

---

## 관련 dev-advisor 문서

- [sdlc-models](./sdlc-models.md) — SDLC 모델(Waterfall / V / Spiral / Agile) 과 본 문서의 관계
- [evolutionary-arch](./evolutionary-arch.md) — Conway's Law, Inverse Conway, fitness function
- [process-metrics](./process-metrics.md) — DORA / SPACE / Flow Metrics (확장 검증 도구)
- [patterns/architectural](../patterns/architectural.md) — Microservices, Modular Monolith (Inverse Conway 결과)
- [grasp](./grasp.md) — Information Expert / Low Coupling (팀 책임 분배 근거)
- [sw-economics](./sw-economics.md) — WSJF (Weighted Shortest Job First), Cost of Delay
