# 요구공학 패턴 (Requirements Engineering Patterns)

요구사항 *수집* + *표현* + *관리* 의 정평 있는 10 패턴. **무엇을 만들지** 정의하는 단계. SWEBOK KA1 "Software Requirements".

**원전·표준 참고**:
- Mike Cohn — *User Stories Applied* (2004)
- Ron Jeffries — "Card, Conversation, Confirmation" (3 C)
- Bill Wake — INVEST Criteria (2003)
- Alistair Cockburn — *Writing Effective Use Cases* (2000)
- Alan Klement — *When Coffee and Kale Compete* (Job Stories)
- Alberto Brandolini — *Introducing EventStorming* (LeanPub, 2021)
- Matt Wynne — *Example Mapping* (Cucumber blog)
- Gojko Adzic — *Impact Mapping* (2012)
- DSDM Consortium — MoSCoW Method
- IEEE 29148:2018 (Requirements engineering)
- BABOK Guide v3 (IIBA)

**관련 카탈로그**:
- [testing.md](testing.md) — Given-When-Then / Gherkin (BDD 본체)
- [`../principles/sw-economics.md`](../principles/sw-economics.md) — Story Point / WSJF / RICE (요구사항 산정)
- [ddd-strategic.md](ddd-strategic.md) — Ubiquitous Language / Bounded Context (도메인 모델링)
- [api-design.md](api-design.md) — Resource modeling

---

## 1. User Story
<a id="user-story"></a>

**목적**: 사용자 관점에서 소망하는 기능을 *역할 + 욕구 + 가치* 한 문장으로 표현하여, 개발자·기획자·도메인 전문가가 동일한 언어로 요구사항을 협의할 수 있게 합니다.

**형식·템플릿**:
```
As a   <역할 / 페르소나>,
I want <원하는 기능 / 행동>,
so that <얻고자 하는 가치 / 비즈니스 결과>.
```

**3 C (Ron Jeffries)**:
| C | 의미 |
|---|---|
| **Card** | 인덱스 카드 한 장에 들어가는 짧은 제목·요약 (요구의 *증표*) |
| **Conversation** | 카드만으로 부족한 세부는 *대화*로 채움 (살아있는 협의) |
| **Confirmation** | 완료 정의(DoD) = *수용 기준(Acceptance Criteria)* |

**장점**:
- 비즈니스 가치(so that)를 명시하여 우선순위 토의가 쉬움
- 짧고 가벼워 백로그 진입 비용이 낮음
- 대화를 전제로 하므로 *문서가 아닌 협업*에 무게중심

**단점·반패턴**:
- "As a user, I want X" 처럼 역할을 뭉뚱그리면 페르소나 의미 상실
- so that 누락 → "기능 카탈로그"로 전락
- 비기능 요구사항(성능, 보안)은 User Story 단일 형식으로 표현하기 어색 → 별도 컨스트레인트 카드 필요
- 거대 스토리(Epic)를 INVEST 위반 상태로 백로그에 두면 추정·분할 비용 폭증

**활용 예시**:
- Scrum/XP 백로그 단위
- Jira/Linear/ClickUp 의 "Story" 이슈 타입
- LeSS, SAFe 같은 scaling 프레임워크의 PI Planning 기본 단위

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Markdown 예제**:
```markdown
## US-142 회원 등급별 무료 배송

**Story**:
> As a 프리미엄 회원,
> I want 5만원 미만 주문에서도 배송비 면제를 받고 싶다,
> so that 등급 혜택을 체감하고 재구매하게 된다.

**Acceptance Criteria** (Confirmation):
- [ ] 회원 등급 = PREMIUM 이면 주문 금액과 무관하게 배송비 0원
- [ ] 일반/실버 회원은 기존 정책 유지 (5만원 이상 면제)
- [ ] 등급 변경 즉시 결제 화면에 반영 (cache TTL ≤ 5초)

**Conversation 노트**:
- 도서 산간 추가 배송비는? → 별도 스토리로 분리 (US-148)
- 프리미엄 종료 시점 처리는? → 결제 시점 등급 기준
```

**관련 패턴**: [INVEST](#invest), [Job Stories](#job-stories), [Three Amigos](#three-amigos), [Gherkin / Given-When-Then](#gherkin-given-when-then)

---

## 2. INVEST 원칙
<a id="invest"></a>

**목적**: User Story 가 *건강한지* 6 가지 기준으로 진단합니다. Bill Wake(2003) 제시. 백로그 정제(refinement) 시 체크리스트로 활용합니다.

**형식·템플릿**:
| 글자 | 기준 | 진단 질문 |
|---|---|---|
| **I**ndependent | 다른 스토리에 묶이지 않고 독립적으로 진행 가능 | 다른 스토리 완료를 기다려야 시작 가능한가? |
| **N**egotiable | 세부는 *대화*로 정해질 여지가 있음 (계약 아님) | 카드 본문이 이미 구현 명세처럼 굳어있는가? |
| **V**aluable | 사용자/고객 가치를 직접 전달 | "DB 인덱스 추가"처럼 가치가 모호하지 않은가? |
| **E**stimable | 팀이 크기(상대 추정)를 잡을 수 있음 | 너무 모호해서 추정 자체가 불가능한가? |
| **S**mall | 한 스프린트(보통 ≤ 1주) 안에 끝낼 만큼 작음 | Epic 수준이라 분할이 필요한가? |
| **T**estable | 수용 기준이 검증 가능한 형태 | "사용성 좋게"처럼 측정 불가능한 표현인가? |

**장점**:
- 백로그 품질을 정량적으로 진단
- 페어 정제 시 공통 어휘 제공
- Epic ↔ Story ↔ Task 분해 의사결정의 근거

**단점·반패턴**:
- 모든 스토리를 6 기준으로 평가하려 들면 정제 회의가 과도하게 길어짐 → 의심되는 카드만
- "Small" 기준이 팀마다 다름 → 팀 velocity 기준으로 합의 필요
- Independent 를 과하게 강조하면 자연스러운 의존(스파이크 → 본 구현)도 분해해 노이즈 증가

**활용 예시**:
- 스프린트 플래닝 직전 백로그 그루밍 체크리스트
- 신규 Story 가 Ready 컬럼으로 이동할 때 게이트
- "이 스토리가 왜 분할 안 되나" 코칭 질문 셋

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Markdown 예제**:
```markdown
## INVEST 진단 — US-205 "검색 결과 무한 스크롤"

| 기준 | 평가 | 메모 |
|---|---|---|
| Independent | ⚠️  | US-201 검색 API 페이징 선행 필요 → 분할 권장 |
| Negotiable | ✅   | 스크롤 임계 픽셀은 협의 가능 |
| Valuable | ✅   | 모바일 체류시간 +12% 가설 (PM A/B 테스트) |
| Estimable | ✅   | 비슷한 기능 US-180 5pt 참고 |
| Small | ❌   | iOS·Android·Web 3 채널 → 채널별 분할 |
| Testable | ⚠️  | "끊김 없이"를 fps 60 으로 측정 가능하게 재작성 |

**결론**: 채널별로 3 분할 + 검색 API 페이징(US-201) 선행. 수용 기준 정량화 필요.
```

**관련 패턴**: [User Story](#user-story), [MoSCoW Prioritization](#moscow), [Three Amigos](#three-amigos)

---

## 3. MoSCoW Prioritization
<a id="moscow"></a>

**목적**: 요구사항을 *반드시 / 해야 / 하면 좋고 / 안 할*  4 단계로 분류하여 출시 범위(scope)를 시각적으로 합의합니다. DSDM(Dynamic Systems Development Method)에서 정립.

**형식·템플릿**:
| 코드 | 의미 | 합의 사항 |
|---|---|---|
| **M**ust have | 이번 릴리스에 *반드시* — 빠지면 출시 불가 | 합의된 시간/예산 안에 100% 완성 |
| **S**hould have | 중요하지만 *대안 우회 가능* | 시간 허락 시 포함, 빠져도 출시 가능 |
| **C**ould have | 있으면 좋음 — *nice to have* | 여유 시간에 진행, 빠지면 다음 릴리스 |
| **W**on't have (this time) | 이번에는 *명시적으로 제외* | 향후 백로그로 기록만, 이번 범위 아님 |

**비율 가이드** (DSDM 권장): Must ≤ 60% / Should ~20% / Could ~20% (effort 기준).

**장점**:
- "전부 다 P0" 라는 흔한 함정을 막음 (가시적 분포 강제)
- "Won't have" 를 명시화 → 이해관계자가 *제외 사실*을 인지
- 릴리스 일정 위기 시 어디부터 잘라낼지 사전 합의

**단점·반패턴**:
- 모든 항목을 Must 로 욱여넣으면 우선순위 도구가 작동 안 함
- Must 가 60% 초과 → 일정 위기 시 잘라낼 안전마진 없음
- 시간이 지나면서 Should/Could 가 Must 로 자동 승격되는 *priority creep*
- 정량 점수(WSJF, RICE)와 결합하지 않으면 정치적 판단으로 흐름

**활용 예시**:
- 릴리스 계획(Release Planning) 워크숍
- MVP 범위 정의 회의
- DSDM/Agile Project Framework 의 표준 우선순위 기법

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Markdown 예제**:
```markdown
## 2026 Q3 릴리스 MoSCoW (총 effort 100pt)

### Must have (55pt — 55%)
- US-142 프리미엄 무료 배송 (12pt)
- US-203 결제 PG 신규 연동 (20pt)
- US-211 회원 가입 약관 개정 반영 (8pt)
- US-220 OWASP Top10 보안 패치 (15pt)

### Should have (22pt — 22%)
- US-225 검색 자동완성 (10pt) — 빠지면 키워드 입력 우회 가능
- US-230 푸시 알림 카테고리 (12pt) — 일괄 발송으로 우회

### Could have (18pt — 18%)
- US-240 다크 모드 (10pt)
- US-242 알림 사운드 커스텀 (8pt)

### Won't have (this time)
- 신용카드 분할 결제 → 2026 Q4 로 명시 이연
- 영어 외 다국어 → 별도 글로벌화 프로젝트로 분리
```

**관련 패턴**: [INVEST](#invest), [Impact Mapping](#impact-mapping), `../principles/sw-economics.md#wsjf`

---

## 4. Use Case
<a id="use-case"></a>

**목적**: 시스템과 **액터(actor)** 가 특정 *목표*를 달성하기 위해 주고받는 상호작용을 시나리오 형태로 명세합니다. Ivar Jacobson(OOSE, 1992) 제시, UML 표준에 포함.

**형식·템플릿** (Alistair Cockburn *Fully Dressed* 양식):
```
Use Case 명     : <동사 + 명사>  예) "Place Order"
주요 액터        : <시스템과 직접 상호작용하는 외부 주체>
이해관계자/관심사 : <영향을 받는 모든 주체와 그 관심사>
사전 조건       : <시작 전에 참이어야 하는 조건>
사후 조건(성공)  : <성공 시 시스템 상태>
사후 조건(실패)  : <실패/취소 시 시스템 상태>
주 시나리오(MSS) : 1. ...
                  2. ...
                  3. ...
확장 시나리오    : 2a. ...  (대안/예외 흐름)
                  3a. ...
```

**UML Use Case Diagram 요소**:
- 액터(Actor) — 스틱맨
- 유즈케이스(Use Case) — 타원
- 시스템 경계(System Boundary) — 사각형
- `<<include>>` — 항상 포함되는 하위 유즈케이스
- `<<extend>>` — 특정 조건에서만 확장되는 유즈케이스
- Generalization — 액터/유즈케이스 상속

**장점**:
- 시스템 *경계*와 외부 액터를 명시 → 범위 합의가 명확
- 예외/대안 흐름(Extension)을 1급 시민으로 다룸 → 행복 경로만 그리는 함정 회피
- 한 시나리오에 *전체 사용자 여정*을 담아 컨텍스트 손실이 적음

**단점·반패턴**:
- 자세히 쓰면 분량 폭증 → "Use Case 작성에만 한 분기" 사고
- UML 도식이 과해지면 그림 관리 자체가 비용
- 작은 변경마다 본문·확장 시나리오 다 갱신해야 하는 유지보수 부담
- Agile 환경에서는 User Story 로 분해하는 단계가 따로 필요

**활용 예시**:
- RUP(Rational Unified Process), ICONIX 프로세스
- 규제 산업(금융/의료)의 *공식 명세* 요구
- 복잡한 권한·예외 흐름이 많은 백오피스/관리자 화면

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Markdown 예제** (Cockburn fully dressed):
```markdown
## UC-007 "Place Order"

**주요 액터**: 회원(Customer)
**이해관계자/관심사**:
- 회원: 빠르고 정확한 결제, 재고 확인
- 가맹점(Merchant): 결제 실패율 최소화
- 결제 PG: 정확한 거래 데이터
- 재고 시스템: 정확한 차감

**사전 조건**:
- 회원이 로그인 상태
- 장바구니에 1개 이상 상품 존재
- 모든 상품이 판매 가능 상태(soft-delete 아님)

**사후 조건 (성공)**:
- 주문이 PAID 상태로 생성
- 재고 차감 완료
- 결제 영수증 이메일 발송

**사후 조건 (실패)**:
- 주문이 생성되지 않거나 CANCELLED 상태
- 재고 차감되지 않음
- 결제 금액 환불 또는 미청구

**주 시나리오(MSS)**:
1. 회원이 "주문하기" 버튼 클릭
2. 시스템이 장바구니 항목·합계·배송지 표시
3. 회원이 결제 수단 선택 후 "결제" 클릭
4. 시스템이 재고를 확인하고 임시 점유
5. 시스템이 PG 에 결제 요청
6. PG 가 승인 응답
7. 시스템이 주문을 PAID 로 확정·재고 영구 차감
8. 시스템이 영수증 이메일 발송, 완료 화면 표시

**확장 시나리오**:
4a. 일부 상품 재고 부족
    1. 시스템이 부족 상품을 표시
    2. 회원이 수량 조정 또는 항목 제거
    3. 단계 4 부터 재개
6a. PG 결제 거절
    1. 시스템이 거절 사유 표시
    2. 회원이 다른 결제 수단 선택 → 단계 3 부터 재개
    3. 회원이 취소 → 임시 점유 재고 해제, 주문 CANCELLED

**빈도**: 1,000 회/분 (피크)
**우선순위**: M (Must have)
```

**관련 패턴**: [User Story](#user-story), [Event Storming](#event-storming), `../patterns/ddd-strategic.md`

---

## 5. Job Stories
<a id="job-stories"></a>

**목적**: User Story 의 "역할(role)" 중심 표현이 페르소나에 갇히는 한계를 보완하기 위해, *상황(situation)* 중심으로 사용자 동기를 기술합니다. Alan Klement 가 Intercom 블로그(2013)에서 제안, JTBD(Jobs-to-be-Done) 이론에 기반.

**형식·템플릿**:
```
When   <상황 / 트리거>,
I want to <동기 / 행동>,
so I can <기대 결과 / 외부에 보일 변화>.
```

**User Story 와의 차이**:
| 측면 | User Story | Job Story |
|---|---|---|
| 시작점 | 페르소나 (Who) | 상황 (When) |
| 가정 | 사용자 유형이 행동을 결정 | 상황이 행동을 결정 |
| 디자인 함의 | 페르소나별 UI 분기 유도 | 상황 인식 UI 유도 (모달/온보딩/푸시) |
| 적합한 곳 | 명확한 사용자 그룹 분리 | 상황 다양도가 큰 SaaS / 모바일 |

**장점**:
- "20대 여성 회원" 같은 인구통계 가정에서 자유로움
- 동일 사용자라도 *상황별로* 다른 동기를 갖는다는 현실 반영
- 트리거(when)가 명확하면 푸시/이메일/온보딩 카피 그대로 활용 가능

**단점·반패턴**:
- "When using the app" 처럼 상황을 무의미하게 두면 User Story 보다 못함
- 페르소나가 *진짜로* 중요한 도메인(B2B 역할 기반)에서는 오히려 정보 손실
- 팀이 둘 중 어느 양식을 쓸지 합의되지 않으면 백로그가 두 양식 혼재

**활용 예시**:
- Intercom, Basecamp 같은 JTBD 신봉 회사
- 모바일 앱 온보딩/푸시 알림 카피 도출
- B2C SaaS 의 churn 분석 → 이탈 유발 *상황* 도출

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Markdown 예제**:
```markdown
## JS-088 "결제 직전 가격 변동 알림"

**Job Story**:
> When 장바구니에 담아둔 상품의 가격이 결제 직전에 인상되었을 때,
> I want to 변동 사실을 결제 화면 진입 즉시 알아채고 싶다,
> so I can 인상 전 가격을 기대하다 당황하는 일을 피하고 결제 여부를 다시 판단할 수 있다.

**Acceptance Criteria**:
- [ ] 장바구니 담은 시점 가격과 현재 가격이 다르면 결제 화면 상단 배너 표시
- [ ] 배너에 "이전 가격 → 현재 가격" + 차액 표시
- [ ] "장바구니로 돌아가기" / "현재 가격으로 진행" 2 액션 제공
- [ ] 변동 미감지 시 배너 미노출

**비고**: 페르소나 무관(신규/단골/프리미엄 모두 동일 상황 인지 필요).
```

**관련 패턴**: [User Story](#user-story), [Impact Mapping](#impact-mapping), [Event Storming](#event-storming)

---

## 6. Event Storming
<a id="event-storming"></a>

**목적**: 도메인 전문가와 개발자가 한 벽에 *도메인 이벤트*를 시간 순으로 붙여가며 시스템의 흐름·경계·규칙을 빠르게 발견합니다. Alberto Brandolini(2013) 제안, DDD 진영의 사실상 표준 워크숍.

**3 단계 (Brandolini *Introducing EventStorming*)**:
| Level | 목적 | 산출물 |
|---|---|---|
| **Big Picture** | 전체 흐름 파악, 경영진 포함 | 시간 순으로 늘어선 *Domain Event* 벽 |
| **Process Modeling** | 정책·읽기 모델·외부 시스템 식별 | Command + Policy + Read Model 추가 |
| **Software Design** | Aggregate / Bounded Context 도출 | DDD 구현 모델 |

**6 색 sticky note 표준**:
| 색 | 의미 | 예시 |
|---|---|---|
| 🟧 **Orange** | Domain Event (과거 분사형) | "주문이 결제됨", "회원 가입함" |
| 🟪 **Purple** | Policy (이벤트 → 명령 트리거 규칙) | "결제 성공 시 영수증 발송" |
| 🟦 **Blue** | Command (액터의 명령) | "결제하기", "주문 취소하기" |
| 🟨 **Yellow** | Actor / User (누가 명령했나) | 회원, 관리자, 시스템 |
| 🟩 **Green** | Read Model (UI 가 보는 데이터) | 주문 상세 화면, 대시보드 |
| 🟥 **Pink (Hot Spot)** | 문제·미해결·논쟁 영역 | "환불 정책 미정", "동시성 충돌?" |

**장점**:
- *코드 없이* 도메인 전체를 단시간(반나절~2일)에 가시화
- 도메인 전문가가 동일 벽 앞에서 동등하게 기여 (Ubiquitous Language 형성)
- Bounded Context 후보가 자연스럽게 드러남 (이벤트 군집)
- Hot Spot 가 *명시적*으로 보임 → 회피되던 난제가 1급 시민화

**단점·반패턴**:
- 퍼실리테이터 역량에 결과 품질이 크게 좌우됨
- 원격 진행 시 도구(Miro/Mural) 학습 비용 + 몰입도 저하
- 이벤트가 *명사형*("주문")으로 적히면 흐름이 무너짐 — 반드시 *과거 분사형*("주문이 생성됨")
- Big Picture 단계를 건너뛰고 바로 Software Design 으로 들어가면 경계 오류

**활용 예시**:
- 신규 도메인 진입 시 *최초의 모델 발견* 워크숍
- 레거시 모놀리스 분해 → Bounded Context 식별
- DDD 기반 마이크로서비스 설계의 첫 단계

**난이도**: 중간~높음 | **사용 빈도**: ★★★★☆

**Markdown / 텍스트 보드 예제** (시간 순으로 좌→우):
```markdown
## 주문 도메인 — Big Picture (발췌)

🟨 회원
   ↓ 🟦 [상품을 장바구니에 추가]
🟧 상품이 장바구니에 담김
   ↓ 🟦 [결제하기]
🟧 결제가 시도됨
   ↓ 🟪 (정책: 재고 임시 점유)
🟧 재고가 임시 점유됨
   ↓ (외부 시스템: PG)
🟧 결제가 승인됨
   ↓ 🟪 (정책: 영수증 발송, 재고 영구 차감)
🟧 주문이 PAID 로 확정됨
🟧 영수증이 발송됨
🟩 [주문 상세 화면]
🟩 [관리자 대시보드 — 일 매출]

🟥 Hot Spot:
- 결제 실패 시 점유 재고를 언제 해제? (timeout? webhook?)
- 부분 환불은 별도 흐름?
- 결제 PG 응답 지연 ≥ 10s 일 때 UX?

## Process Modeling 으로 발전
- 명령(Blue): "결제하기" → 정책(Purple): "재고 임시 점유"
- 정책의 트리거 조건과 실패 시 보상 트랜잭션 식별

## Software Design — Bounded Context 후보
[Ordering] : 주문이 생성됨, PAID 로 확정됨, CANCELLED
[Inventory]: 재고가 임시 점유됨, 영구 차감됨, 해제됨
[Billing]  : 결제가 시도됨, 승인됨, 거절됨, 환불됨
[Notification]: 영수증이 발송됨
```

**관련 패턴**: [Use Case](#use-case), [Example Mapping](#example-mapping), `ddd-strategic.md` (Bounded Context / Context Map)

---

## 7. Example Mapping
<a id="example-mapping"></a>

**목적**: 한 User Story 를 짧은(20~30분) 워크숍으로 *규칙(Rule)* 과 *구체 예시(Example)* 로 분해하여, 모호한 부분과 미결정 질문을 드러냅니다. Matt Wynne(2015, Cucumber blog) 제안.

**4 색 카드 표준**:
| 색 | 의미 | 위치 |
|---|---|---|
| 🟨 **Yellow** | Story (중심 토픽) | 보드 중앙 상단 |
| 🟦 **Blue** | Rule (수용 기준 / 비즈니스 규칙) | Story 아래 가로 배열 |
| 🟩 **Green** | Example (각 Rule 의 구체 사례) | 각 Rule 아래 세로 배열 |
| 🟥 **Red** | Question (미결정 / 가정) | 우측 별도 영역 |

**진행 절차** (≤ 30분):
1. **Story 한 장** 보드 중앙에 놓기
2. 팀이 떠올리는 **Rule** 을 노랑 카드 아래 가로로 나열
3. 각 Rule 마다 **Green Example** ("주어진 ~, ~할 때, ~이다") 1~3장
4. 답할 수 없는 질문은 **Red** 로 옆에 쌓아두기
5. Red 가 많으면 → Story 미숙. Blue 가 너무 많으면 → 분할 필요. Green 이 충분하면 → Ready

**장점**:
- BDD 의 Gherkin 시나리오 작성 *직전*에 합의를 만든다
- "30분 한도" 라는 강한 제약이 디테일 폭주를 막음
- Question(Red) 을 *비난 없이* 드러내는 안전한 형식
- Three Amigos 회의의 구조화된 진행 도구

**단점·반패턴**:
- 시간 제약을 무시하면 단순한 요구사항 회의로 회귀
- Example 이 사실은 Rule (일반화 누락) 인 경우 흔함
- 진행자가 Question 을 "다음에 정해요" 로 무한정 미루면 백로그 부채만 누적

**활용 예시**:
- BDD 도입 팀의 스토리 정제 표준
- Three Amigos 회의의 진행 양식
- Gherkin `.feature` 파일 작성 직전 협업 단계

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★☆

**Markdown 예제** (Story → Rules → Examples → Questions):
```markdown
## Example Mapping — US-142 "프리미엄 회원 무료 배송"

🟨 Story: 프리미엄 회원은 주문 금액과 무관하게 무료 배송

🟦 Rule 1: 등급 = PREMIUM 이면 배송비 0원
   🟩 Example: 프리미엄, 주문 10,000원 → 배송비 0원
   🟩 Example: 프리미엄, 주문 100,000원 → 배송비 0원

🟦 Rule 2: 일반/실버 회원은 5만원 이상이면 무료, 미만이면 3,000원
   🟩 Example: 일반, 주문 49,999원 → 배송비 3,000원
   🟩 Example: 일반, 주문 50,000원 → 배송비 0원
   🟩 Example: 실버, 주문 30,000원 → 배송비 3,000원

🟦 Rule 3: 등급 변경 즉시 결제 화면에 반영 (cache TTL ≤ 5초)
   🟩 Example: 결제 화면 진입 후 등급 강등 → 5초 이내 새로고침 시 배송비 재계산

🟥 Question:
- 도서 산간 추가 배송비도 프리미엄 면제 대상? → 별도 스토리 분할 합의
- 프리미엄 종료 *직전* 결제는 어떤 등급으로 처리? → 결제 시도 시점 등급 기준
- 환불 후 재주문 시 등급 카운트? → 도메인 전문가 추가 확인 필요
```

**관련 패턴**: [User Story](#user-story), [Gherkin / Given-When-Then](#gherkin-given-when-then), [Three Amigos](#three-amigos)

---

## 8. Gherkin / Given-When-Then
<a id="gherkin-given-when-then"></a>

**목적**: 비즈니스 시나리오를 *기계가 실행 가능한* 자연어 명세로 표현하여, 도메인 전문가가 읽고 검토할 수 있는 *살아있는 문서(Living Documentation)* 이자 자동화 테스트로 동시에 활용합니다. Cucumber(2008) 가 도입한 Gherkin 문법.

**기본 문법 (Gherkin keyword)**:
```gherkin
Feature: <기능 이름>
  <기능에 대한 자유 서술 — 비즈니스 가치/배경>

  Background:
    Given <모든 시나리오에 공통인 전제 조건>

  Scenario: <시나리오 한 줄 제목>
    Given <전제 상태>
    And   <추가 전제>
    When  <트리거 행위>
    Then  <관찰 가능한 결과>
    And   <추가 결과>

  Scenario Outline: <매개변수화된 시나리오>
    Given 주문 금액 <amount> 원
    And   회원 등급 <tier>
    When  결제 화면을 연다
    Then  배송비는 <fee> 원이다

    Examples:
      | amount | tier     | fee   |
      | 10000  | PREMIUM  | 0     |
      | 49999  | STANDARD | 3000  |
      | 50000  | STANDARD | 0     |
```

**Given-When-Then 의 역할**:
| 단계 | 책임 | 안티패턴 |
|---|---|---|
| **Given** | 시작 *상태* 만 기술. UI 클릭 금지 | "Given 사용자가 로그인 버튼을 클릭한다" → When 침범 |
| **When** | 검증 대상 행위 *한 줄* | 여러 When 연쇄 → 시나리오 분할 필요 |
| **Then** | 관찰 가능한 *결과* | 내부 구현 검증(SQL row 수) → 행위가 아닌 구조 결합 |

**장점**:
- `.feature` 파일이 *명세 + 테스트 + 문서* 3 역할 동시 수행
- 도메인 전문가가 시나리오 검토·기여 가능
- 회귀 테스트가 *비즈니스 언어* 그대로 실행되어 신뢰도↑
- Scenario Outline 으로 동치 클래스 테이블 검증

**단점·반패턴**:
- "Gherkin = AAA 의 한국어 번역" 으로 그치면 비용만 증가
- glue code(Step Definition) 가 비대해지면 유지보수 지옥
- UI 좌표/CSS 셀렉터를 Then 에 노출 → 구현 변경에 깨짐
- 시나리오 수가 폭증하면 실행 시간 비대 → 단위/통합/E2E 비율 재조정

**활용 예시**:
- Cucumber-JVM, Cucumber.js, SpecFlow(.NET), pytest-bdd
- 규제 산업(금융/보험)의 *공식 인수 기준*
- DDD + BDD 결합한 도메인 핵심 모듈

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Gherkin `.feature` 파일 예제**:
```gherkin
# language: ko
기능: 회원 등급별 배송비 산정
  프리미엄 회원의 충성도를 높이기 위해 무조건 무료 배송을 제공한다.
  일반/실버 회원은 5만원 이상 주문 시에만 무료 배송을 받는다.

  배경:
    전제 회원이 로그인 상태이다
    그리고 장바구니에 상품이 있다

  시나리오: 프리미엄 회원은 금액 무관하게 무료 배송
    전제 회원 등급은 "PREMIUM" 이다
    그리고 주문 금액은 10000 원이다
    언제 결제 화면을 연다
    그러면 배송비는 0 원이다
    그리고 "프리미엄 회원 무료 배송" 배지가 표시된다

  시나리오 개요: 등급·금액 조합에 따른 배송비
    전제 회원 등급은 "<tier>" 이다
    그리고 주문 금액은 <amount> 원이다
    언제 결제 화면을 연다
    그러면 배송비는 <fee> 원이다

    예:
      | tier     | amount | fee   |
      | PREMIUM  | 10000  | 0     |
      | PREMIUM  | 100000 | 0     |
      | STANDARD | 49999  | 3000  |
      | STANDARD | 50000  | 0     |
      | SILVER   | 30000  | 3000  |
      | SILVER   | 70000  | 0     |
```

**Step Definition (Kotlin / Cucumber-JVM)**:
```kotlin
class ShippingFeeSteps {
    private lateinit var checkout: CheckoutScreen
    private var fee: Int = -1

    @Given("회원 등급은 {string} 이다") fun setTier(tier: String) {
        checkout = CheckoutScreen(tier = Tier.valueOf(tier))
    }

    @Given("주문 금액은 {int} 원이다") fun setAmount(amount: Int) {
        checkout.setOrderAmount(amount)
    }

    @When("결제 화면을 연다") fun open() {
        fee = checkout.calculateShippingFee()
    }

    @Then("배송비는 {int} 원이다") fun assertFee(expected: Int) {
        fee shouldBe expected
    }
}
```

**관련 패턴**: [Example Mapping](#example-mapping), [User Story](#user-story), [testing.md#3-given-when-then-bdd-스타일](testing.md)

---

## 9. Impact Mapping
<a id="impact-mapping"></a>

**목적**: 비즈니스 *목표(Goal)* → 영향받는 *액터(Actor)* → 액터에게 만들어야 할 *행동 변화(Impact)* → 그 변화를 만들 *산출물(Deliverable)* 의 4 단계 마인드맵으로, "왜 만드는가" 를 시각화하여 *제대로 된 것을 만드는지* 검증합니다. Gojko Adzic(2012) 제안.

**형식·템플릿** (마인드맵):
```
                    [Goal: 측정 가능한 비즈니스 목표]
                      ├── Why?
                      │
       ┌──────────────┼──────────────┐
       │              │              │
   [Actor 1]      [Actor 2]      [Actor 3]
   (Who?)         (Who?)         (Who?)
       │
   ┌───┴────┐
   │        │
[Impact A] [Impact B]   ← 액터의 행동을 어떻게 바꿔야?
(How?)     (How?)
   │
┌──┴──┐
[Deliv 1] [Deliv 2]    ← 어떤 산출물이 그 변화를 만드는가?
(What?)   (What?)
```

**4 질문**:
| 단계 | 질문 | 산출물 형태 |
|---|---|---|
| **Goal** | Why? — 우리는 왜 이걸 하나? | 측정 가능한 비즈니스 목표 1개 |
| **Actor** | Who? — 누구의 행동이 바뀌어야 하나? | 사용자/내부 직원/외부 시스템 |
| **Impact** | How? — 그들의 행동이 어떻게 바뀌나? | 행동 변화 동사형 ("더 자주 ~", "처음으로 ~") |
| **Deliverable** | What? — 그 변화를 위해 무엇을 만들거나 할까? | 기능, 캠페인, 정책 변경 |

**장점**:
- *기능 백로그*가 아닌 *결과 가설*에서 출발 → 헛수고 방지
- 동일 Goal 에 대해 *여러 Impact 경로*를 시각적으로 비교 (대안 모색)
- "이 기능이 어떤 Impact 의 어떤 Goal 에 기여?" 라는 질문에 추적 가능
- Deliverable 을 *가설*로 다루므로 잘라내거나 교체하기 쉬움

**단점·반패턴**:
- Goal 이 측정 불가("사용성 향상")하면 전체 트리가 무의미
- 모든 백로그를 Impact Map 에 매핑하려 들면 *행정 비용*
- Deliverable 까지만 그리고 학습 루프(가설 검증)를 안 돌면 단순한 마인드맵
- Impact 와 Deliverable 의 경계가 모호하면 "기능 트리" 로 변질

**활용 예시**:
- 분기 OKR 수립과 백로그 연계
- 신규 제품 발견(discovery) 단계
- "이 기능 정말 필요?" 라는 질문을 *구조적으로* 던지는 도구

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Markdown 예제** (들여쓰기 마인드맵):
```markdown
## Impact Map — 2026 Q3

### Goal (Why?)
**모바일 앱 첫 결제 전환율을 30% → 40% 로 향상 (2026/09/30 까지)**

### Actor 1 — 신규 가입 회원 (Who?)
- **Impact 1.1**: 가입 후 첫 결제까지 평균 7일 → 2일로 단축 (How?)
  - **Deliverable A**: 가입 직후 첫 결제 쿠폰 자동 발급 (What?)
  - **Deliverable B**: 온보딩 3단계 마지막에 "지금 결제하면 ~" 푸시
  - **Deliverable C**: 빈 장바구니 24h 후 알림
- **Impact 1.2**: 결제 실패 후 재시도율 20% → 50%
  - **Deliverable D**: 결제 실패 사유별 가이드 (한도/카드 만료/PG 점검)
  - **Deliverable E**: 다른 결제 수단 원클릭 전환

### Actor 2 — CS 상담사 (Who?)
- **Impact 2.1**: 결제 실패 문의 처리 시간 5분 → 2분
  - **Deliverable F**: 상담사 화면에 결제 실패 사유 실시간 노출
  - **Deliverable G**: 보상 쿠폰 즉시 발급 권한

### Actor 3 — 결제 PG (Who?)
- **Impact 3.1**: 승인율 92% → 96%
  - **Deliverable H**: 카드사별 라우팅 룰 최적화
  - **Deliverable I**: 재시도 정책 (15초 후 1회 자동)

### 가설 검증 루프
- Deliverable A 출시 후 2주 → 첫 결제까지 일수 변화 측정
- 효과 없으면 B/C 우선 검토, A 는 보류
- 모든 Deliverable 은 *가설* — Goal 미달성 시 교체 대상
```

**관련 패턴**: [User Story](#user-story), [Job Stories](#job-stories), [MoSCoW Prioritization](#moscow), `../principles/sw-economics.md#rice`

---

## 10. Three Amigos
<a id="three-amigos"></a>

**목적**: 한 User Story 의 *수용 기준*을 합의하기 위해 **비즈니스 분석(BA) + 개발(Dev) + 품질(QA)** 세 관점을 한 자리에 모아 30~60분 안에 모호함을 제거합니다. Matt Wynne(2014) 정립, Jeff Patton 의 "Three Amigos" 용어 채택.

**세 역할의 관점**:
| 역할 | 던지는 질문 |
|---|---|
| **BA (Product / 도메인)** | "이 기능이 *왜* 필요한가? 비즈니스 규칙은?" |
| **Dev (개발자)** | "이걸 *어떻게* 구현할 수 있나? 기술적 제약은?" |
| **QA (테스터)** | "어떤 경우에 *실패*할까? 엣지 케이스는?" |

세 관점이 만나는 곳에 *진짜 요구사항*이 있다. 한 관점만 있으면 다음과 같이 편향:
- BA 만 → 구현 불가능한 이상론
- Dev 만 → 비즈니스 가치 누락된 기술 명세
- QA 만 → 행복 경로 누락된 예외 더미

**진행 절차** (≤ 60분, 보통 30분):
1. **Story 와 초안 수용 기준** 공유 (5분)
2. **각 관점의 질문**을 자유롭게 던지기 (15~20분)
3. **Example Mapping** 보드로 Rule + Example + Question 정리 (15분)
4. **합의된 수용 기준**을 Gherkin 시나리오 초안으로 기록 (10분)
5. **남은 Question(Red 카드)** 은 담당자와 마감일 지정 후 백로그

**장점**:
- 스프린트 *후반*에 발견될 모호함을 *시작 전에* 제거
- BA-Dev-QA 사일로를 가로지르는 공통 어휘 형성
- "이거 인수 기준에 없었잖아?" 분쟁의 사전 차단
- *문서가 아닌 협업*이라는 Agile 원칙의 실천 형태

**단점·반패턴**:
- BA/Dev/QA 한 명이라도 빠지면 의미 없음 → 일정 조율 부담
- 너무 잦으면(매 스토리마다 1시간) 회의 피로
- "BA 가 말하면 Dev/QA 가 듣기만" 하는 일방 회의로 변질되면 본래 가치 손실
- 원격 진행 시 비동기로 흐를 위험 → 짧은 동기 미팅 + 비동기 추가 노트 권장

**활용 예시**:
- BDD 도입 팀의 Story Ready 게이트
- 백로그 정제(Refinement) 세션의 기본 형식
- Jeff Patton 의 Story Mapping 워크숍 후속 단계

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Markdown 예제** (회의록):
```markdown
## Three Amigos — US-142 "프리미엄 무료 배송"
참석: BA(Hana), Dev(Min), QA(Soo) | 일시: 2026-05-14 14:00~14:35

### 초안 수용 기준
- 프리미엄 회원은 주문 금액과 무관하게 무료 배송

### 관점별 질문 / 합의

**BA (Hana)**:
> Q. 프리미엄 종료 *직전* 결제는 어떤 등급?
> A. 결제 시도 시점 등급 기준 (합의)
> Q. 도서 산간 추가 배송비도 면제?
> A. 이번 범위 아님 (별도 스토리 US-148 로 분리)

**Dev (Min)**:
> Q. 등급 캐시 TTL?
> A. 현재 60초 → 결제 화면에서는 5초로 단축 (합의)
> Q. 회원 등급 조회 실패 시?
> A. 기본 정책(STANDARD) 적용 + 에러 로그 (합의)

**QA (Soo)**:
> Q. 결제 도중 등급 강등되면?
> A. 결제 시도 시점 등급 우선 — 강등 후 5초 이내는 이전 등급 유지 가능 (합의)
> Q. 등급 변경 후 환불·재주문 시 새 등급?
> A. 새 결제 시점의 등급 기준 (합의)
> Q. 회원이 비프리미엄 → 프리미엄 *업그레이드* 직후 결제?
> A. 즉시 무료 배송 적용 (캐시 5초 내 반영)

### Red (미결정 / Follow-up)
- 환불 시 발생한 배송비는 회수? → CS 팀과 확인 (담당: Hana, ~05/17)

### Gherkin 초안 (별도 .feature 작성)
- 위 §8 예제 참조
```

**관련 패턴**: [Example Mapping](#example-mapping), [User Story](#user-story), [Gherkin / Given-When-Then](#gherkin-given-when-then), [INVEST](#invest)

---

## 카탈로그 메모

- 본 카탈로그는 *요구사항 정의* 단계 패턴만 다룬다. 도출된 요구를 *도메인 모델*로 구체화하는 단계는 [ddd-strategic.md](ddd-strategic.md) / [ddd-tactical.md](ddd-tactical.md) 참고.
- *우선순위 산정의 정량 기법*(Story Point, WSJF, RICE, Cost of Delay)은 [`../principles/sw-economics.md`](../principles/sw-economics.md) 에 분리.
- BDD 의 *테스트 실행* 측면은 [testing.md](testing.md) 의 Given-When-Then 항목, *요구 명세* 측면은 본 카탈로그 §7~§8 에서 다룬다.
- IEEE 29148:2018 / BABOK v3 같은 *공식 표준*은 본 카탈로그가 다루는 패턴들의 상위 메타 분류 참조.
