# HCI 연구 방법론 (HCI Research Methodology)

사용자 중심 설계(User-Centered Design)를 실증적으로 수행하기 위한 **6 가지 정평 있는 연구·평가 방법론**. 본 문서는 *UI/UX 패턴* (→ [`../patterns/ui-ux.md`](../patterns/ui-ux.md)) 의 결과물이 아닌, **그 결과물을 도출·검증하는 절차 자체**에 집중한다. ISO 9241-210 (Human-centred design for interactive systems) 의 4 단계 — *Context of Use → Requirements → Design Solution → Evaluation* — 를 관통하는 방법론 묶음.

**원전·표준 참고**:
- ISO 9241-210:2019 — *Ergonomics of human-system interaction — Part 210: Human-centred design for interactive systems*
- ISO 9241-11:2018 — *Usability: Definitions and concepts*
- Alan Cooper — *The Inmates Are Running the Asylum* (1999), *About Face* (4th ed., 2014) — Persona 원전
- Adaptive Path — *Customer Experience Maps* (2011) — Journey Map 정립
- Donna Spencer — *Card Sorting: Designing Usable Categories* (Rosenfeld Media, 2009)
- Jakob Nielsen — *Usability Engineering* (1993), "10 Usability Heuristics for User Interface Design" (1994, rev. 2024)
- Ben Shneiderman — *Designing the User Interface* (6th ed., 2016) — 8 Golden Rules
- Donald A. Norman — *The Design of Everyday Things* (Revised & Expanded, 2013) — 6 Design Principles
- Cathleen Wharton et al. — "The Cognitive Walkthrough Method: A Practitioner's Guide" (1994)
- Anthony W. Ulwick — *Jobs to Be Done: Theory to Practice* (2016), *What Customers Want* (2005)
- Clayton Christensen — "Know Your Customers' Jobs to Be Done", *HBR* (2016)
- Nielsen Norman Group — *UX Research Methods* article series (nngroup.com)
- Sakichi Toyoda — Toyota Production System "5 Whys" 기법 (1930s, 후속 정리: Taiichi Ohno)

**관련 카탈로그**:
- [`../patterns/ui-ux.md`](../patterns/ui-ux.md) — UI/UX 결과물 패턴 (Atomic Design, A11y/WCAG, i18n 등)
- [`../patterns/requirements-engineering.md`](../patterns/requirements-engineering.md) — User Story / Job Stories / Event Storming (요구 표현)
- [iso25010.md](iso25010.md#usability) — Usability 품질 특성 (방법론으로 측정하는 대상)
- [professional-ethics.md](professional-ethics.md#dark-pattern-classification) — Dark Pattern 분류 + Inclusive Design 윤리 연계

---

## 1. Persona — User / Buyer / 행위 기반 / Anti-Persona
<a id="persona-method"></a>

**정의**: 실제 사용자 집단을 대표하는 **가상의 인물 프로파일**. Alan Cooper(1999)가 *The Inmates Are Running the Asylum* 에서 도입했으며, ISO 9241-210 의 *Context of Use* 산출물로 표준화되었다. "사용자 모두"라는 추상을 *구체적 한 사람*으로 좁혀 설계 의사결정을 명료화한다.

**4 가지 변형**:

| 유형 | 초점 | 사용 시점 | 핵심 필드 |
|---|---|---|---|
| **User Persona** | 제품을 *직접 사용*하는 사람 | UX/UI 설계, 기능 우선순위 | 목표, Pain Point, 사용 시나리오, 디지털 숙련도 |
| **Buyer Persona** | 구매 의사결정자 (B2B 특히 중요) | 마케팅·세일즈·가격 정책 | 예산 권한, 의사결정 단계, 정보 소스, KPI |
| **행위 기반 Persona (Behavioral)** | *행동 패턴 빈도*로 분류 | 데이터 풍부한 성숙 제품 | 사용 빈도, 기능 사용 클러스터, churn 위험 |
| **Anti-Persona** | *우리가 타겟이 아닌* 사용자 | 범위 축소, 기능 거절 근거 | 거절 이유, 잘못된 기대, 부적합 사용 사례 |

**절차 (Cooper 모델)**:
1. **사용자 인터뷰 수집** — 정성 인터뷰 6~12 명 / 페르소나 후보군당
2. **행동 변수 식별** — 활동·태도·동기·숙련도 5~7 축
3. **변수 매핑** — 각 인터뷰이를 축 위에 배치, 클러스터 식별
4. **페르소나 통합** — 클러스터마다 1 명의 가상 인물로 합성 (이름·사진·인용구·시나리오)
5. **검증** — 실 사용자 대상 "이 사람이 우리 같은가?" 확인

**산출물**: 페르소나 시트(1~2 페이지) — 이름·나이·직업·사진·목표·좌절·시나리오·인용구·핵심 task 3~5 개.

**도구**: Xtensio Persona Templates, HubSpot Make My Persona, UXPressia, Miro/FigJam 템플릿.

**한계**:
- 정성 데이터 기반 → 표본 편향, 작성자 추측("design-by-imagination") 가능
- *Proto-persona* (인터뷰 없이 가설로 만든 페르소나) 는 빠르지만 검증 없으면 위험
- 행위 기반 페르소나는 충분한 telemetry/로그 누적 후에만 의미

**Anti-Persona 활용 예시**: "엔터프라이즈 IT 관리자 페르소나에 대해, *Anti-Persona = 단독 사용자 / 무료 도구 추구자* — 이들의 요구는 거절"

**Cross-link**: [User Story](../patterns/requirements-engineering.md#user-story) (페르소나가 As a 의 역할 슬롯에 들어감), [JTBD 인터뷰](#cognitive-walkthrough) (페르소나의 약점을 보완).

---

## 2. Journey Map — Customer Journey / Service Blueprint / Experience Map / Empathy Map
<a id="journey-map"></a>

**정의**: 사용자가 *목표 달성* 을 위해 거치는 **시간순 접점(touchpoint) 흐름**을 시각화. Adaptive Path 가 2011 년 *Experience Maps* 백서로 정립했고, Nielsen Norman Group 이 4 변형을 표준화했다.

**4 변형 비교**:

| 종류 | 범위 | 관점 | 주요 레이어 | 사용 시점 |
|---|---|---|---|---|
| **Customer Journey Map** | 단일 제품 / 단일 페르소나 | 외부(고객) | Stage / Action / Touchpoint / Thought / Emotion / Pain | 기능 개선, friction 식별 |
| **Service Blueprint** | 전체 서비스 | 내·외부 (frontstage/backstage) | Customer Action / Frontstage / Backstage / Support Process / Evidence | 운영·CS 포함 서비스 설계 |
| **Experience Map** | 제품 무관 일반 경험 | 외부 (보편적 행동) | Phases / Doing / Thinking / Feeling | 시장 진입 전 도메인 학습 |
| **Empathy Map** | 단일 페르소나 *심리 단면* | 외부 (감각·심리) | Says / Thinks / Does / Feels (+ Pain/Gain) | 페르소나 보강, 시간축 불필요 |

**Customer Journey Map 절차**:
1. **페르소나 선정 + 시나리오 설정** — "프리미엄 회원 X 가 모바일에서 첫 주문"
2. **단계(Stage) 정의** — Awareness → Consideration → Purchase → Use → Advocacy 등
3. **각 단계 행동·접점·생각·감정 채집** — 인터뷰·세션 리플레이·CS 티켓·NPS 코멘트
4. **감정 곡선(Emotion Curve) 작성** — 단계별 만족도(-3 ~ +3) 라인 차트
5. **Pain Point / Opportunity 마킹** — 곡선 저점에 개선 기회 라벨
6. **이해관계자 워크숍 검증** — 영업·CS·운영 팀과 사실 확인

**산출물**: A0~A1 크기 가로 매트릭스 — 가로축 = 단계/시간, 세로축 = 행동·접점·thought·emotion·opportunity 레이어.

**도구**: Miro, FigJam, UXPressia, Smaply, Mural.

**한계**:
- 페르소나 1 명 기준 → 다중 페르소나는 별도 맵 필요 (통합 시 가독성 손실)
- 작성 비용 큼 (워크숍 1~2 일) → "stale map" 위험, 분기 1 회 갱신 권장
- Emotion 데이터의 정량화는 NPS·CSAT 등 외부 측정과 교차 검증 필요

**Cross-link**: [User Story](../patterns/requirements-engineering.md#user-story) (Journey 의 각 단계가 백로그 진입), [Impact Mapping](../patterns/requirements-engineering.md#impact-mapping) (Journey 의 opportunity → 측정 가능한 impact 로 전환).

---

## 3. Card Sort — Open / Closed / Hybrid + 정보 구조(IA) 도구
<a id="card-sort"></a>

**정의**: 사용자에게 **콘텐츠 카드들을 의미적으로 묶게(grouping)** 함으로써 정보 구조(Information Architecture, IA) 를 사용자 멘탈 모델에 정렬시키는 정량·정성 혼합 기법. Donna Spencer 가 *Card Sorting: Designing Usable Categories* (2009) 로 정립.

**3 변형**:

| 종류 | 카테고리 | 라벨 | 용도 | 산출 |
|---|---|---|---|---|
| **Open Sort** | 사용자가 자유롭게 생성 | 사용자 작성 | 새 IA 탐색, 어휘 발견 | 카테고리 후보 + 사용자 어휘 |
| **Closed Sort** | 사전 정의된 카테고리 | 고정 | 기존 IA 검증·평가 | 분류 정확도 매트릭스 |
| **Hybrid Sort** | 일부 고정 + 자유 추가 | 혼합 | 부분 IA 확정, 확장 영역만 탐색 | 정착 카테고리 + 신규 후보 |

**절차 (원격 — OptimalSort 기준)**:
1. **카드 준비** — 30~60 개 (너무 많으면 피로, 적으면 통계 부족); 콘텐츠·기능·용어 단위
2. **참가자 모집** — Open Sort 15~30 명, Closed Sort 30~50 명 (Tullis & Wood 권장)
3. **실시 (15~30 분/명)** — 카드를 드래그하여 그룹핑, 각 그룹에 라벨링
4. **분석**:
   - **유사도 매트릭스 (Similarity Matrix)** — 카드 쌍이 같은 그룹에 묶인 빈도
   - **덴드로그램 (Dendrogram)** — 계층적 클러스터링 시각화
   - **Standardization Grid** — 같은 의미에 사용된 다른 라벨 통합
5. **카테고리 확정 + 라벨 명명** — 사용자 어휘 우선, 전문용어 회피

**Tree Test (Treejack) 와 결합**: Card Sort 로 *생성*한 IA 를 Tree Test 로 *검증* (사용자가 트리 navigation 으로 task 찾기 성공률).

**산출물**: IA 트리(2~3 레벨), 라벨 사전, 분류 신뢰도 매트릭스(0~100% per pair).

**도구**:
- **OptimalSort** (Optimal Workshop) — 원격 카드 정렬 표준 도구, 자동 클러스터링
- **Treejack** (Optimal Workshop) — Tree Test 페어 도구
- **UserZoom**, **Maze** — 통합 UX 리서치 플랫폼
- **물리 카드** (Post-it / 인덱스 카드) — 워크숍·교실용

**한계**:
- 카드 *세트 자체*에 편향이 들어가면 결과 왜곡 (작성자의 IA 가정이 카드에 녹아있음)
- 사용자 멘탈 모델 ≠ 도메인 정확성 (예: 사용자가 "전기차"를 "친환경" 아래 묶지만 카탈로그상으로는 "차종"이 맞을 수 있음)
- Closed Sort 는 *카테고리가 이미 옳다*는 전제가 깔려 있음 — Open + Closed 순서 진행 권장

**Cross-link**: [i18n](../patterns/ui-ux.md#i18n) (다국어 라벨은 언어별 Card Sort 필요), [A11y/WCAG 2.4 Navigable](../patterns/ui-ux.md#a11y-wcag) (IA 가 스크린리더 탐색 구조의 기반).

---

## 4. Think-Aloud Protocol — Concurrent / Retrospective + Cognitive Walkthrough 차이
<a id="think-aloud-protocol"></a>

**정의**: 사용자에게 task 수행 중 **생각·의도·혼란을 소리내어 말하게(verbalize)** 하여 *행동의 이유*를 포착하는 사용성 평가 기법. Ericsson & Simon (*Protocol Analysis*, 1984) 이 인지심리학에서 체계화했고, Nielsen 이 사용성 테스트의 표준 절차로 보급했다.

**2 변형**:

| 종류 | 시점 | 장점 | 단점 |
|---|---|---|---|
| **Concurrent Think-Aloud (CTA)** | task 수행 *중* 실시간 발화 | 사고와 행동의 시간 일치, 망각 없음 | 발화 부하 → task 시간 25~50% 증가, 멀티태스킹 부담 |
| **Retrospective Think-Aloud (RTA)** | task 종료 *후* 화면 녹화 재생하며 발화 | task 자연스러움 보존, 정확한 task 시간 측정 가능 | 회상 편향, 누락, 사후 합리화 (rationalization) |

**절차 (Concurrent, 1 인 60~90 분)**:
1. **사전 브리핑** — "정답·평가가 아니라 *제품*을 검증, 자유롭게 말해주세요" + 연습 task 1 개
2. **task 부여 (5~8 개)** — 시나리오 기반, 솔루션 노출 금지 ("프리미엄 가입을 시도해보세요")
3. **관찰** — 진행자는 *최소 개입* (3~5 초 침묵 시 "지금 무슨 생각 중이세요?" 정도만)
4. **녹화** — 화면 + 얼굴 + 음성 (윤리 동의 필수)
5. **post-task 인터뷰** — SEQ (Single Ease Question, 1~7 점), SUS (System Usability Scale, 10 문항)
6. **분석** — 발화·행동 타임라인 코딩, *Pain Point* / *Aha Moment* / *Error Recovery* 태깅

**Cognitive Walkthrough 와의 결정적 차이**:

| 항목 | Think-Aloud | Cognitive Walkthrough |
|---|---|---|
| **참가자** | 실 사용자 | 전문가(설계자·UX 평가자) |
| **데이터** | 실 발화·행동 | 전문가의 추론 |
| **목적** | *실증 검증* | *학습 가능성 예측* (특히 초보자) |
| **비용** | 인터뷰 + 분석 (1 task 약 8~12 h) | 워크숍 (수 시간) |
| **시점** | 프로토타입~출시 | 설계 *초기*, 사용자 모으기 전 |
| **약점** | Hawthorne 효과 (관찰됨 의식) | 전문가 편향, 사용자 멘탈 모델 미반영 |

→ 둘은 *대체재 아닌 보완재*. Walkthrough → Think-Aloud 순서가 표준.

**산출물**: 발화 transcript, 행동 타임라인, Pain Point 우선순위 표(빈도 × 심각도), SUS/SEQ 점수.

**도구**: Lookback.io, UserTesting.com, Maze, dscout, Zoom 녹화 + Otter.ai transcription, Loop11.

**한계**:
- 발화 부하 → 정량 지표(task 시간·오류율) 왜곡 (RTA 로 보완)
- 자기 검열·합리화 — 실제 행동과 발화 불일치 가능 → 행동을 *우선* 데이터로 채택
- 5 명 표본으로 사용성 문제의 ~85% 발견 (Nielsen & Landauer, 1993) — 그러나 *발견율* 이지 *심각도 합의* 는 아님

**Cross-link**: [Heuristic Evaluation](#heuristic-evaluation) (전문가 평가 후 Think-Aloud 로 실증), [Cognitive Walkthrough](#cognitive-walkthrough).

---

## 5. Heuristic Evaluation — Nielsen 10 / Shneiderman 8 / Norman 6
<a id="heuristic-evaluation"></a>

**정의**: **전문가가 정평 있는 휴리스틱 체크리스트** 에 비추어 UI 의 위반점을 찾는 *비용 효율적* 평가 기법. Nielsen & Molich (1990) 가 제안, *Usability Engineering* (1993) 에서 5 명 평가자 × 2~3 회 패스로 *문제의 ~75%* 를 발견할 수 있음을 실증.

**Nielsen 10 Usability Heuristics (1994, rev. 2024 — Nielsen Norman Group)**:

| # | 휴리스틱 | 한 줄 정의 |
|---|---|---|
| 1 | Visibility of system status | 사용자에게 현재 상태를 적시 피드백 (로딩, 진행, 결과) |
| 2 | Match between system and real world | 사용자 언어·관습·실세계 메타포 사용 (전문용어 회피) |
| 3 | User control and freedom | 실수에서 빠져나갈 비상구 (Undo, Cancel, 뒤로) |
| 4 | Consistency and standards | 같은 의미는 같은 표현, 플랫폼 컨벤션 준수 |
| 5 | Error prevention | 실수 *예방* 이 회복보다 우선 (확인, 제약, 제안) |
| 6 | Recognition rather than recall | 인지 부담 최소화 — 보이게 하라, 기억하게 말라 |
| 7 | Flexibility and efficiency of use | 초보자·숙련자 동시 만족 (단축키, 매크로) |
| 8 | Aesthetic and minimalist design | 관련 없는 정보 제거, 중요 정보 가시화 |
| 9 | Help users recognize, diagnose, recover from errors | 오류는 평이한 언어 + 진단 + 해결 제안 |
| 10 | Help and documentation | 필요할 때 검색 가능한 도움말, task 단위 |

**Shneiderman 8 Golden Rules** (*Designing the User Interface*, 6th ed., 2016):

1. **Strive for consistency** — 일관된 sequence·terminology·color·typography
2. **Seek universal usability** — 신규/전문/장애/문화 차이 모두 포용
3. **Offer informative feedback** — 모든 사용자 행동에 시스템 응답
4. **Design dialogs to yield closure** — 시작-중간-종료 단계, 완료 만족감
5. **Prevent errors** — 메뉴 회색화, 형식 강제, 위험 행동 확인
6. **Permit easy reversal of actions** — 단위 행동·소그룹·전체 task 단위 Undo
7. **Keep users in control (internal locus of control)** — 시스템이 *사용자에게 응답*
8. **Reduce short-term memory load** — 7±2 chunk, 인지 부담 분산

**Norman 6 Design Principles** (*The Design of Everyday Things*, Revised 2013):

| 원칙 | 정의 | 예 |
|---|---|---|
| **Visibility (Discoverability)** | 가능한 행동이 보여야 함 | 스크롤바 visible, hover 시 affordance |
| **Feedback** | 행동의 결과가 즉시 신호 | 버튼 클릭 시 색 변화, 햅틱 |
| **Constraints** | 가능한 행동을 *제한* (물리·논리·문화·의미) | USB-C는 한 방향만, 전화번호 입력은 숫자만 |
| **Mapping** | 컨트롤과 효과의 *공간적/논리적 대응* | 가스레인지 노브 ↔ 화구 위치 일치 |
| **Consistency** | 같은 의미는 같은 표현 | 모든 화면의 저장 아이콘 동일 |
| **Affordance** | 객체가 *어떻게 쓰일 수 있는지* 자체적으로 시사 | 문 손잡이 모양이 push/pull 시사 |

**절차 (Heuristic Evaluation)**:
1. **평가자 모집** — *3~5 명* (Nielsen — 1 명 35%, 5 명 75% 발견)
2. **사전 학습** — 평가자에게 도메인·페르소나 브리핑 (1 시간)
3. **개별 평가 1 회차** — 각 평가자가 *독립적*으로 화면을 돌며 휴리스틱 위반 기록 (1~2 시간)
4. **개별 평가 2 회차** — 1 회차의 시야로 다시 깊이 평가
5. **종합 워크숍** — 발견 사항 통합, 중복 제거, 심각도(severity) 합의
   - Severity Rating Scale: 0 (no problem) / 1 (cosmetic) / 2 (minor) / 3 (major) / 4 (catastrophe)
6. **보고서 작성** — 위반 → 휴리스틱 ID → 심각도 → 권장 수정

**산출물**: 위반 목록 (화면·휴리스틱 ID·심각도·근거·수정안), 우선순위 매트릭스.

**도구**: Nielsen Norman 휴리스틱 cheat sheet, Userlytics Heuristic Evaluation Templates, Notion/Confluence 평가 시트.

**한계**:
- 전문가 평가 → 실 사용자 발견을 대체 못함 (Think-Aloud 와 결합 권장)
- *False positive* 빈번 — 휴리스틱 위반이지만 실 사용자가 인지 못하는 경우
- 도메인 특화 (의료·금융·접근성)는 일반 휴리스틱 부족 → 도메인 휴리스틱 보강 필요 (예: WCAG 2.2 for A11y)

**Cross-link**: [A11y/WCAG](../patterns/ui-ux.md#a11y-wcag) (접근성 휴리스틱), [Empty/Error/Loading State](../patterns/ui-ux.md#empty-error-loading-state) (#9 오류 회복), [iso25010 Usability](iso25010.md#usability) (휴리스틱은 Usability 특성의 평가 수단).

---

## 6. Cognitive Walkthrough — 4 질문 + JTBD 인터뷰 + 5 Whys
<a id="cognitive-walkthrough"></a>

**정의**: **사용자 *학습 가능성(learnability)* 을 *전문가가 시나리오 기반으로 추론*** 하는 평가 기법. Wharton, Rieman, Lewis & Polson (1994) — *The Cognitive Walkthrough Method: A Practitioner's Guide* — 가 정립. 신규 사용자·*walk-up-and-use* 시스템(키오스크·ATM·공공 시스템) 평가에 특히 강점.

**Wharton 4 질문 프로토콜** (각 task 의 *각 step* 마다 질문):

| # | 질문 | 검증 대상 |
|---|---|---|
| **Q1** | 사용자가 *올바른 행동을 시도*할까? | 동기·목표 명확성 (Mental Model alignment) |
| **Q2** | 사용자가 *올바른 컨트롤*을 인지할까? | Affordance / Discoverability (Norman) |
| **Q3** | 사용자가 *컨트롤과 의도 사이의 매핑* 을 이해할까? | Mapping / Labeling 명료성 |
| **Q4** | 사용자가 *피드백 후 progress* 를 해석할까? | Feedback 가시성 / 진행 신호 |

→ 4 질문 중 *하나라도 NO* 면 해당 step 은 *learnability failure point*. NO 의 근거(왜 NO 인가)가 곧 결함 보고.

**절차 (워크숍, 4~6 시간)**:
1. **준비** — 페르소나 1~3 명, task 시나리오 3~5 개, 인터페이스 명세(화면 plan 또는 프로토타입)
2. **task 분해** — 각 task 를 *atomic step* (1 클릭/1 입력 단위) 으로 분해
3. **워크스루** — 평가자 그룹(3~5 명)이 step 별 4 질문을 *소리내어* 토의
4. **기록** — 각 NO 에 대해: step·질문·이유·심각도·권장 수정
5. **종합** — task 별 success path 와 failure point 매트릭스

**Jobs to Be Done (JTBD) 인터뷰** — Anthony Ulwick (Outcome-Driven Innovation, 2005, 2016):

**핵심 가설**: 사용자는 제품을 *구매·사용*하는 것이 아니라, *원하는 진전(progress)을 위해 제품을 채용(hire)*한다.

**Job Statement 형식**:
```
When <상황·맥락>,
I want to <동기·기능적 목적>,
so I can <원하는 결과·감정적 결과>.
```

**Ulwick 5 단계 JTBD 인터뷰 프로토콜**:
1. **First Thought** — "이 제품을 처음 떠올린 순간은 언제·왜?"
2. **Passive Looking** — "어떤 사건이 *대안을 찾게 만들었나*?" (trigger)
3. **Active Looking** — "구체적으로 *비교한 옵션·기준*은?" (set of candidates)
4. **Deciding** — "선택의 *결정 요인·압력*은?" (push / pull / habit / anxiety)
5. **Onboarding** — "사용 시작 후 *기대 vs 실제*?"

→ 5 단계는 *사고의 4 가지 힘* (Forces of Progress: Push of Situation / Pull of New / Anxiety of New / Habit of Present) 을 채집하는 구조.

**5 Whys** (Toyota Production System, 사카치 도요다, 1930s):
- *Root Cause Analysis* 의 가장 단순한 기법 — 발견된 문제에 "왜?" 를 5 회 반복하여 표면 증상에서 근본 원인으로 추적
- HCI 적용: Cognitive Walkthrough 의 NO 발견 → 5 Whys → *근본적 설계 결함* (예: "왜 Q2 실패? → 버튼이 안 보임 → 왜? → 색 대비 부족 → 왜? → 디자인 토큰의 muted 색 → 왜? → 토큰 설계 시 A11y 미고려 → 왜? → 토큰 가이드라인 부재")
- 한계: 단일 원인 가정 (실제 다인자 문제는 *Ishikawa Diagram* 등으로 보완)

**산출물**: task × step × 4 질문 매트릭스, failure point 보고, JTBD job statement 카드, 5 Whys 인과 트리.

**도구**: Mural/FigJam 워크스루 템플릿, Notion/Confluence JTBD 인터뷰 가이드, Strategyn ODI 도구 (Ulwick 회사 상용 도구).

**한계**:
- 전문가 추론 기반 → *실 사용자* 검증 불가 (Think-Aloud 결합 필수)
- 4 질문이 *동기적 차원* (예: 감정·신뢰·맥락 외 요인) 을 누락
- JTBD 의 "감정적 결과" 는 정성 코딩에 의존 — 정량화 어려움
- 5 Whys 의 *5* 는 절대 횟수 아님 (3~7 회 적정) — 원인이 더 깊을 수 있음

**Cross-link**: [Think-Aloud Protocol](#think-aloud-protocol) (Walkthrough 후 실 사용자 검증), [Heuristic Evaluation](#heuristic-evaluation) (Q2/Q3 은 Nielsen #2/#4/#6 과 의미 중첩), [Job Stories](../patterns/requirements-engineering.md#job-stories) (JTBD 의 백로그 표현 형식), [Persona](#persona-method) (Walkthrough 의 가정 사용자), [Dark Pattern Classification](professional-ethics.md#dark-pattern-classification) (5 Whys 가 dark pattern 의 *의도성* 을 추적할 때 활용).

---

## 방법론 선택 매트릭스

| 의문 / 단계 | 추천 방법론 |
|---|---|
| 사용자가 *누구* 인지 모름 | Persona (Open) + 행위 데이터 |
| 사용자의 *전체 여정* 이 흐릿함 | Customer Journey Map / Service Blueprint |
| 정보 구조 (메뉴·카테고리) 가 사용자에 안 맞음 | Card Sort (Open → Closed) + Tree Test |
| 프로토타입에 *실 사용자* 반응이 궁금함 | Think-Aloud (CTA / RTA) |
| 빠르고 저렴하게 명백한 결함 식별 | Heuristic Evaluation (Nielsen 10) |
| 신규 사용자가 *처음 배울 때* 의 막힘 | Cognitive Walkthrough (Wharton 4Q) |
| 사용자가 *왜* 그 행동을 하는지 모름 | JTBD 인터뷰 (Ulwick 5 단계) |
| 발견된 문제의 *근본 원인* | 5 Whys + Ishikawa |

**ISO 9241-210 단계 매핑**:
- *Context of Use* — Persona, Empathy Map
- *Requirements* — Journey Map, JTBD, Card Sort (라벨링)
- *Design Solution* — Heuristic Evaluation (반복), Cognitive Walkthrough
- *Evaluation* — Think-Aloud, SUS/SEQ, A/B (→ [`../patterns/ui-ux.md`](../patterns/ui-ux.md))

---

**참고 자료**:
- ISO 9241-210:2019 *Human-centred design for interactive systems* (clauses 5.2 Context, 5.3 Requirements, 5.4 Solution, 5.5 Evaluation)
- ISO 9241-11:2018 *Usability: Definitions and concepts* (effectiveness × efficiency × satisfaction)
- Cooper, Reimann, Cronin & Noessel — *About Face: The Essentials of Interaction Design*, 4th ed. (Wiley, 2014)
- Spencer — *Card Sorting* (Rosenfeld Media, 2009)
- Nielsen — "Severity Ratings for Usability Problems" (NN/g, 1994)
- Wharton et al. — "The Cognitive Walkthrough Method: A Practitioner's Guide", in *Usability Inspection Methods* (Wiley, 1994)
- Ulwick — *Jobs to Be Done: Theory to Practice* (Idea Bite Press, 2016)
- Ericsson & Simon — *Protocol Analysis: Verbal Reports as Data*, rev. ed. (MIT Press, 1993)
- Nielsen Norman Group, *UX Research Methods* article series, https://www.nngroup.com/articles/
