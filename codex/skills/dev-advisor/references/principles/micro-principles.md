# 미시 원칙 (Micro Principles)

거시 원칙(SOLID/GRASP/ISO 25010/12-Factor)과 코드 스멜(Code Smells) 사이의 *간결한 격언* 20 항목. 짧지만 일상 코딩에서 가장 자주 인용되는 표준.

**구성**: 핵심 8 (DRY/KISS/YAGNI/LoD/SoC/Tell-Don't-Ask/Composition/SSoT) + 사회·조직·확장 10 (Conway / Inverse Conway / Hyrum / Postel / Brooks / Hollywood / Boy Scout / Pareto / Goodhart / Cunningham).

**참고**: 이 파일은 `verify-references.sh`의 무결성 카운트 대상에서 제외된다 (5 거시 원칙 + 22 스멜 = 56 합계 유지). 본문 헤더는 `## <원칙명>` 형식 (숫자 없음).

---

<a id="dry"></a>
## DRY (Don't Repeat Yourself, 반복 금지)

**원전**: Andy Hunt, Dave Thomas, *The Pragmatic Programmer* (1999), Tip 11
**한 줄 정의**: "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system."

**의도**: 지식(로직·규칙·데이터)의 복제를 금지한다. 코드 복사가 아닌 *지식 복사*가 DRY 위반의 본질이다. 같은 계산식이 두 곳에 있으면 한 쪽을 수정할 때 나머지를 빠뜨리는 순간 버그가 발생한다.

**적용 사례**:
- 할인율 계산 로직을 `DiscountCalculator` 하나에만 두고 주문·환불·쿠폰 모두 해당 메서드를 호출
- DB 스키마와 ORM 모델 중 하나를 단일 소스(예: sqlc/prisma)로 생성

**위반 사례**:
- 유효성 검사 정규식이 프론트엔드·백엔드·DB constraint 세 곳에 따로 선언됨
- 동일한 날짜 포맷 변환 함수가 서로 다른 패키지에 2개 이상 존재

**관련 표준/원칙**:
- [SRP](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) — 단일 책임 = 단일 변경 축 → 중복 제거와 동기화됨
- [Duplicate Code](code-smells.md#14-duplicate-code-중복-코드) — DRY 위반의 직접 코드 스멜

**코드 예제**:
```kotlin
// 위반: 할인율 계산이 두 곳에 중복
fun calcOrderTotal(price: Int, qty: Int) = price * qty * 0.9  // 10% 할인
fun calcRefundAmount(price: Int, qty: Int) = price * qty * 0.9 // 동일 로직 복사

// 준수: 단일 함수로 통합
fun applyDiscount(amount: Int): Int = (amount * 0.9).toInt()
fun calcOrderTotal(price: Int, qty: Int) = applyDiscount(price * qty)
fun calcRefundAmount(price: Int, qty: Int) = applyDiscount(price * qty)
```

---

<a id="kiss"></a>
## KISS (Keep It Simple, Stupid, 단순함 원칙)

**원전**: Kelly Johnson, Lockheed Skunk Works (1960년대); 소프트웨어 맥락은 *The Pragmatic Programmer* 에서 정착
**한 줄 정의**: "Most systems work best if they are kept simple rather than made complicated."

**의도**: 불필요한 복잡성을 도입하지 않는다. 현재 요구사항을 충족하는 가장 단순한 설계를 선택한다. 리팩토링으로 언제든 복잡성을 추가할 수 있지만, 단순화는 훨씬 어렵다.

**적용 사례**:
- 페이지네이션이 불필요한 내부 도구에 커서 기반 무한 스크롤 구현을 포기하고 단순 오프셋 방식 유지
- 전략 패턴 대신 if-else 2분기로 충분한 상황에서 패턴 미적용

**위반 사례**:
- 현재 사용하지 않는 플러그인 시스템·이벤트 버스·추상 팩토리를 "나중을 위해" 미리 설계
- 단순 CRUD에 CQRS + Event Sourcing 전체 스택 도입

**관련 표준/원칙**:
- [Speculative Generality](code-smells.md#18-speculative-generality-과잉-일반화) — KISS 위반의 대표 코드 스멜
- [OCP](solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙) — 확장성과 단순성의 균형점; 과한 추상화는 KISS 위반

---

<a id="yagni"></a>
## YAGNI (You Aren't Gonna Need It, 불필요 기능 금지)

**원전**: Kent Beck, *Extreme Programming Explained* (1999); Ron Jeffries 공동 정립
**한 줄 정의**: "Always implement things when you actually need them, never when you just foresee that you need them."

**의도**: 현재 요구사항에 없는 기능을 미리 구현하지 않는다. 예측 기반 구현은 90% 이상의 확률로 실제 요구와 다르게 쓰이거나 아예 쓰이지 않는다. 미사용 코드는 유지보수 비용만 높인다.

**적용 사례**:
- "다국어 지원이 필요할 수도 있다"는 이유로 현재 한국어만 쓰는 서비스에 i18n 레이어 미적용
- 캐시가 필요하다는 증거(프로파일링)가 없을 때 캐시 레이어 추가 보류

**위반 사례**:
- 요구사항에 없는 export CSV, export PDF, export Excel 세 기능을 모두 사전 구현
- 현재 싱글 리전인데 멀티 리전 고려해 추상화 레이어 선 도입

**관련 표준/원칙**:
- [Speculative Generality](code-smells.md#18-speculative-generality-과잉-일반화) — YAGNI 위반의 직접 스멜
- [Lazy Class](code-smells.md#15-lazy-class-게으른-클래스) — 미래를 위해 만든 클래스가 실제 쓰임 없이 남음

---

<a id="lod"></a>
## Law of Demeter (LoD, 최소 지식 원칙)

**원전**: Ian Holland, Northeastern University (1987); Karl Lieberherr, *Assuring Good Style for Object-Oriented Programs* (1989)
**한 줄 정의**: "Talk only to your immediate friends." — 객체는 직접 아는 객체하고만 대화해야 한다.

**의도**: 메서드 `m`은 다음 네 유형의 객체에만 메시지를 보낼 수 있다: (1) `m`을 가진 클래스 자신, (2) `m`의 파라미터, (3) `m` 안에서 생성된 객체, (4) 클래스의 직접 필드. 점(`.`) 체인은 모르는 낯선 객체에 접근하는 신호다.

**적용 사례**:
- `order.getCustomer().getAddress().getCity()` 대신 `order.getShippingCity()` 위임 메서드 제공
- 서비스 레이어가 Repository 반환 엔티티의 내부 컬렉션을 직접 순회하지 않고 메서드 위임

**위반 사례**:
- `a.b.c.d.doSomething()` 형태의 점 체인이 3단계 이상
- 테스트 더블을 여러 겹 stub해야만 테스트가 작동하는 경우

**관련 표준/원칙**:
- [Message Chains](code-smells.md#21-message-chains-메시지-체인) — LoD 위반의 직접 코드 스멜
- [Feature Envy](code-smells.md#19-feature-envy-기능-욕심) — 다른 객체 내부를 과도하게 참조하는 패턴
- [Low Coupling](grasp.md#4-low-coupling-낮은-결합도) — LoD 준수는 Low Coupling의 실천 수단

**코드 예제**:
```kotlin
// 위반: 낯선 객체 체인 탐색
fun printCity(order: Order) {
    println(order.customer.address.city)  // 3단계 체인
}

// 준수: Order가 city 조회 책임을 위임
fun printCity(order: Order) {
    println(order.shippingCity())  // Order만 알면 충분
}
```

---

<a id="soc"></a>
## Separation of Concerns (SoC, 관심사 분리)

**원전**: Edsger W. Dijkstra, *On the role of scientific thought* (1974) — "It is what I sometimes have called 'the separation of concerns'..."
**한 줄 정의**: "Separate different concerns in a program so that each section addresses only one aspect of the problem."

**의도**: 프로그램의 서로 다른 관심사(변경 이유)는 물리적으로 분리된 모듈/레이어/컴포넌트에 배치한다. 변경이 발생할 때 해당 관심사만 수정하면 되도록 격리한다. Clean Architecture/Hexagonal Architecture의 근간 원칙.

**적용 사례**:
- HTTP 파싱(Controller) / 비즈니스 규칙(UseCase) / 데이터 접근(Repository) 레이어 분리
- React 컴포넌트에서 UI 렌더링과 API 호출 로직을 custom hook으로 분리

**위반 사례**:
- Controller가 SQL 쿼리를 직접 실행하고 이메일도 발송
- ViewModel이 비즈니스 유효성 검사와 UI 상태 관리를 동시에 담당

**관련 표준/원칙**:
- [SRP](solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) — SRP는 클래스 수준의 SoC
- [High Cohesion](grasp.md#5-high-cohesion-높은-응집도) — 같은 관심사끼리 모으는 것이 High Cohesion

---

<a id="tell-dont-ask"></a>
## Tell, Don't Ask

**원전**: Alec Sharp, *Smalltalk by Example* (1997); Andy Hunt & Dave Thomas, *The Pragmatic Programmer* (1999)에서 "Tell, Don't Ask" 명칭 정착
**한 줄 정의**: "Tell objects what you want them to do; don't ask them questions about their state and then make the decision yourself."

**의도**: 객체의 상태를 꺼내어 외부에서 결정하지 말고, 객체에게 행동을 명령한다. 결정 로직은 데이터를 가진 객체 안에 있어야 한다. 이 원칙은 Information Expert(GRASP)의 행동 버전이다.

**적용 사례**:
- `if (account.balance > amount) account.balance -= amount` 대신 `account.withdraw(amount)` 호출
- 컬렉션의 내부 상태를 꺼내 외부 서비스가 필터링하는 대신, 컬렉션 객체에 `filterByStatus(status)` 메서드 추가

**위반 사례**:
- 서비스 레이어가 엔티티 필드를 getter로 꺼내 조건 판단 후 다시 setter로 세팅
- `user.isActive()` 확인 후 외부에서 포인트 계산 — 포인트 규칙이 User 밖에 누출

**관련 표준/원칙**:
- [Feature Envy](code-smells.md#19-feature-envy-기능-욕심) — 다른 객체 데이터를 과도하게 꺼내는 것은 Tell, Don't Ask 위반 신호
- [Information Expert](grasp.md#1-information-expert-정보-전문가) — 정보를 가진 객체가 행동도 가져야 한다는 GRASP 원칙

**코드 예제**:
```kotlin
// 위반: 상태를 꺼내 외부에서 결정
fun processWithdrawal(account: Account, amount: Int) {
    if (account.balance >= amount) {  // 외부에서 상태 질의 후 결정
        account.balance -= amount
    }
}

// 준수: 객체에 행동을 명령
fun processWithdrawal(account: Account, amount: Int) {
    account.withdraw(amount)  // Account 내부에서 잔액 검증·차감
}
```

---

<a id="composition-over-inheritance"></a>
## Composition over Inheritance

**원전**: Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides (Gang of Four), *Design Patterns: Elements of Reusable Object-Oriented Software* (1994), Chapter 1 — "Favor object composition over class inheritance."
**한 줄 정의**: "Favor object composition over class inheritance."

**의도**: 상속은 부모-자식 간 강한 결합(컴파일 타임 의존)을 만들고, 부모 변경이 자식 전체에 전파된다. 합성(Composition)은 런타임에 교체 가능한 약한 의존을 사용해 유연성·테스트 용이성을 높인다. "is-a" 관계가 명확할 때만 상속을 선택하고, "has-a" 또는 "can-do" 관계는 합성으로 표현한다.

**적용 사례**:
- 로깅 행동을 `LoggingMixin` 상속 대신 `Logger` 인터페이스 주입(DI)으로 구현
- Strategy 패턴: 정렬 알고리즘을 상속 계층 대신 `Sorter` 인터페이스 필드로 교체 가능하게

**위반 사례**:
- `SpecialOrder extends Order extends BaseEntity` 3단계 이상 상속 후 오버라이드 남용
- 테스트를 위해 프로덕션 클래스를 상속하고 메서드를 오버라이드해 동작 변경

**관련 표준/원칙**:
- [Refused Bequest](code-smells.md#8-refused-bequest-거절된-유산) — 자식이 부모 메서드 일부를 원치 않으면 상속이 잘못된 신호
- [LSP](solid.md#3-liskov-substitution-principle-lsp-리스코프-치환-원칙) — 상속 사용 시 LSP 준수 여부가 "is-a" 관계 적합성 판단 기준

---

<a id="ssot"></a>
## Single Source of Truth (SSoT, 단일 진실 공급원)

**원전**: 정보 관리 원칙으로 학계·산업계에서 광범위하게 사용; 소프트웨어 맥락에서는 *The Pragmatic Programmer* DRY 원칙의 데이터 버전으로 자리잡음
**한 줄 정의**: "Every piece of data must have a single, authoritative source; all other occurrences are derived or referenced from that source."

**의도**: 한 데이터 또는 설정 항목은 *유일한 공식 정의 위치* 하나만 가진다. 다른 위치의 값은 그 소스에서 파생(계산·참조)되어야 하며, 독립적으로 관리되면 불일치가 발생한다. DRY가 로직 복제를 다룬다면 SSoT는 *데이터·상태* 복제를 다룬다.

**적용 사례**:
- 사용자 역할(role)은 DB 하나에만 저장하고, JWT payload의 role은 매 요청마다 DB에서 파생
- 환경별 서버 URL은 `config.ini` 하나에만 선언하고 빌드 시 주입 (두 파일에 나눠 선언 금지)
- React 상태: 동일 데이터를 부모·자식 state에 각각 저장하지 않고 부모 하나에만 보관

**위반 사례**:
- 상품 가격이 `products` 테이블과 `order_items` 테이블 두 곳에 중복 저장되어 업데이트 불일치 발생
- 같은 Feature Flag 값이 DB·Redis·코드 상수 세 곳에 각각 정의됨

**관련 표준/원칙**:
- [Duplicate Code](code-smells.md#14-duplicate-code-중복-코드) — SSoT 위반의 데이터 버전 코드 스멜
- [12-Factor III Config](12-factor.md#3-config-설정) — 환경 설정의 단일 소스는 환경변수(또는 단일 config 파일)

---

<a id="conway-law"></a>
## Conway's Law

**원전**: Melvin E. Conway, *How Do Committees Invent?*, Datamation magazine (April 1968)
**한 줄 정의**: "Any organization that designs a system (defined broadly) will produce a design whose structure is a copy of the organization's communication structure."

**의도**: 시스템 아키텍처는 결국 그 시스템을 만드는 조직의 커뮤니케이션 구조를 그대로 반영한다. 4개 팀이 컴파일러를 만들면 4-pass 컴파일러가 나오고, 백엔드·프론트엔드·DB 팀이 따로 있으면 그대로의 3-tier 아키텍처가 나온다. 이는 *관찰 결과*이지 처방이 아니다.

**적용 사례**:
- 마이크로서비스 경계가 팀 경계와 일치하지 않으면 cross-team API 변경 비용이 폭증 — Team Topologies의 stream-aligned team으로 재편
- 모노리스를 분리할 때 코드 의존 그래프와 팀 조직도를 함께 그려 mismatch 영역 식별
- 단일 팀이 풀스택을 담당하면 자연스럽게 vertical slice(기능 단위) 아키텍처가 형성됨

**반례·오해**:
- "법칙이니 어쩔 수 없다"는 체념론은 오해. Conway는 *경향성*을 관찰한 것이며, Inverse Conway Maneuver로 의도적 조정이 가능하다
- 조직도만 바꾸면 아키텍처가 따라 바뀐다는 단순화도 오해 — 실제 변화는 *커뮤니케이션 경로* 변경에서 온다 (회의 빈도, Slack 채널, 코드 리뷰 그룹)
- "Conway의 법칙은 컴파일러 시대 이야기"라는 회의론도 잘못 — 2015년 Thoughtworks·Spotify·Netflix 사례에서 재확인됨

**관련 표준/원칙**:
- [Inverse Conway Maneuver](#inverse-conway-maneuver) — Conway의 처방적 활용
- [SoC](#separation-of-concerns-soc-관심사-분리) — 시스템 분리는 팀 분리와 동기화되어야 효과적
- [Low Coupling](grasp.md#4-low-coupling-낮은-결합도) — 팀 간 결합도와 모듈 간 결합도가 일치

---

<a id="inverse-conway-maneuver"></a>
## Inverse Conway Maneuver

**원전**: ThoughtWorks Technology Radar (2015); Matthew Skelton, Manuel Pais, *Team Topologies: Organizing Business and Technology Teams for Fast Flow* (2019)
**한 줄 정의**: "Evolve your team and organizational structure to promote your desired architecture." — 원하는 아키텍처를 얻기 위해 조직 구조를 *먼저* 설계한다.

**의도**: Conway's Law를 처방적으로 뒤집어 사용한다. 마이크로서비스·서버리스·플랫폼 아키텍처를 목표로 한다면, 그에 대응하는 팀 구조(stream-aligned, platform, enabling, complicated-subsystem)를 먼저 만들고 그 안에서 아키텍처가 자연 발생하도록 한다.

**적용 사례**:
- 결제·재고·배송 도메인별 마이크로서비스를 원하면 → 3개 stream-aligned team으로 재편 후 각 팀이 자기 서비스만 책임
- 플랫폼 엔지니어링: 공통 인프라(K8s, CI/CD, observability)를 platform team이 self-service 형태로 제공해 stream team이 인프라 결합도 없이 작동
- Spotify 모델: Squad(stream-aligned) + Tribe + Chapter + Guild 구조로 의도된 마이크로서비스 토폴로지 유도

**반례·오해**:
- "조직 개편이 만능"이라는 오해. 코드와 조직을 *함께* 움직여야 하며, 일방적 조직 변경은 혼란만 야기
- Team Topologies는 4 team type + 3 interaction mode(collaboration, X-as-a-Service, facilitating)의 정합성이 핵심 — 팀 이름만 바꾸고 상호작용 모드를 정의하지 않으면 실패
- 모든 조직에 마이크로서비스가 적합하다는 가정은 오해. 팀이 5명 미만이면 모놀리스가 인지 부하·운영 비용 측면에서 우월

**관련 표준/원칙**:
- [Conway's Law](#conway-law) — 본 기법의 토대
- [SoC](#separation-of-concerns-soc-관심사-분리) — 팀 경계와 모듈 경계의 동기화
- [Bounded Context (DDD)](#) — stream-aligned team의 자연스러운 경계 단위

---

<a id="hyrum-law"></a>
## Hyrum's Law

**원전**: Hyrum Wright (Google), *Software Engineering at Google* (Titus Winters et al., O'Reilly 2020), Chapter 1; 자체 사이트 [hyrumslaw.com](https://www.hyrumslaw.com/)
**한 줄 정의**: "With a sufficient number of users of an API, it does not matter what you promise in the contract: all observable behaviors of your system will be depended on by somebody."

**의도**: API의 *명세된* 동작뿐 아니라 *관찰 가능한 모든 부수 효과*(반환 순서, 에러 메시지 문자열, 응답 latency, 함수의 우연한 idempotency 등)가 충분한 사용자가 있는 순간 누군가의 의존성이 된다. 즉, 모든 implementation detail은 결국 contract가 된다.

**적용 사례**:
- Map 자료구조의 iteration 순서를 보장하지 않아도 사용자는 특정 순서에 의존 → Java HashMap → LinkedHashMap 마이그레이션 시 깨짐
- HTTP 에러 응답의 JSON 필드 순서를 단순 리팩토링했더니 정규식으로 파싱하던 클라이언트가 깨짐
- sort 알고리즘을 unstable → stable로 바꿨더니 동률 정렬에 의존한 테스트 다수 실패

**반례·오해**:
- "그러면 절대 바꾸지 말라"는 의미가 아니다. *변경의 비용을 예측* 하고, deprecation·feature flag·canary 등으로 관리하라는 뜻
- 내부 API에는 적용되지 않는다는 오해 — 100명 이상 사용하는 사내 라이브러리도 동일하게 작동
- 명세를 강하게 쓰면 회피된다는 오해 — 명세가 아무리 강해도 *관찰 가능*하면 누군가 의존함 (Google은 `RANDOM_HASH_SALT`로 Map 순서를 매 빌드마다 랜덤화해서 의존을 방지)

**관련 표준/원칙**:
- [Postel's Law](#postel-law) — 입력 관용성과 출력 엄격성의 균형이 Hyrum 영향 완화 도구
- [OCP](solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙) — 확장에 열리고 수정에 닫힌 설계가 Hyrum 표면적 축소
- [Speculative Generality](code-smells.md#18-speculative-generality-과잉-일반화) — 과한 확장점은 관찰 가능 동작을 증가시켜 Hyrum 부담 가중

---

<a id="postel-law"></a>
## Postel's Law (Robustness Principle)

**원전**: Jon Postel, *RFC 793: Transmission Control Protocol* (September 1981), Section 2.10 — "TCP implementations should follow a general principle of robustness: be conservative in what you do, be liberal in what you accept from others."
**한 줄 정의**: "Be conservative in what you send, be liberal in what you accept." (자주 인용되는 압축형)

**의도**: 시스템 간 상호작용에서 (1) *송신*은 명세에 엄격히 따라 예측 가능하게 보내고, (2) *수신*은 가능한 한 관용적으로 파싱한다. 인터넷 프로토콜이 다양한 구현 환경에서 견고하게 작동하도록 만든 핵심 원리.

**적용 사례**:
- HTTP 서버: 헤더 이름 case-insensitive 처리(관용 수신), 응답은 항상 RFC 권장 case로 송신(엄격 송신)
- JSON API: 알 수 없는 필드는 무시하고 알려진 필드만 처리(관용 수신), 응답에는 명세에 없는 필드를 넣지 않음(엄격 송신)
- 날짜 파싱: ISO 8601 다양한 변형(`Z`, `+00:00`, 마이크로초 유무)을 모두 수용, 송신은 한 형식으로 통일

**반례·오해**:
- 최근 IETF에서는 *과한 관용*이 보안 취약점과 상호운용성 저하를 일으킨다는 비판이 있다 (RFC 9413, Martin Thomson 2023). XSS·HTTP request smuggling·SQL injection 다수가 "관용적 파싱" 결과
- "모든 입력을 받아들여라"는 의미가 아니다 — *명세상 모호한* 부분을 너그럽게 처리하라는 것. 명백히 잘못된 입력은 거부해야 함
- 송신측이 엄격하면 수신측이 관용적일 필요가 없어진다는 주장(엄격성 일관 적용)도 일리 있음 — 현대 API 설계는 양측 모두 엄격한 경향

**관련 표준/원칙**:
- [Hyrum's Law](#hyrum-law) — 관용 수신은 Hyrum 표면적을 늘려 후속 변경을 어렵게 함
- [DIP](solid.md#5-dependency-inversion-principle-dip-의존-역전-원칙) — 추상화에 의존해 송수신 양쪽의 변동성 흡수
- [Defensive Programming] — Postel은 외부 경계 방어 코딩의 철학적 기반

---

<a id="brooks-law"></a>
## Brooks's Law

**원전**: Fred Brooks, *The Mythical Man-Month: Essays on Software Engineering* (Addison-Wesley 1975), Chapter 2
**한 줄 정의**: "Adding manpower to a late software project makes it later."

**의도**: 늦은 소프트웨어 프로젝트에 인력을 추가하면 더 늦어진다. 이유는 (1) 신규 인력의 ramp-up 시간이 기존 인력의 시간을 빼앗고, (2) 커뮤니케이션 경로가 n(n-1)/2로 폭증하며, (3) 분할 불가능한 작업은 인력 추가로도 단축되지 않기 때문. *"9명의 여자를 동원해 1개월 만에 아이를 낳을 수는 없다"* (Brooks의 비유).

**적용 사례**:
- 마감 임박 프로젝트에 신규 개발자 투입 대신 *스코프 축소* 또는 *기존 인력 집중*으로 대응
- 인력 추가가 불가피하다면 ramp-up 비용이 회수되는 시점(통상 2~3개월 후) 이후에만 가속 효과 기대
- 큰 팀을 작은 stream-aligned team으로 쪼개 커뮤니케이션 폭증을 차단

**반례·오해**:
- "절대 인력을 추가하지 말라"는 의미가 아니다. *늦은 프로젝트의 끝에서* 추가하면 역효과라는 것 — 초기에 충분한 인력 배치는 별개
- 작업이 잘 분할되고 커뮤니케이션 오버헤드가 낮다면 Brooks 법칙이 약화됨. 명확히 독립적인 모듈을 신규 팀이 담당하면 가속 가능 (Brooks 본인도 *No Silver Bullet*에서 인정)
- "AI/도구가 해결한다"는 주장은 부분적으로만 맞음 — 코드 작성 속도는 빨라져도 도메인 이해·코드베이스 학습 시간은 동일

**관련 표준/원칙**:
- [Conway's Law](#conway-law) — 커뮤니케이션 구조가 시스템과 일정 양쪽에 영향
- [KISS](#kiss-keep-it-simple-stupid-단순함-원칙) — 복잡도 감축이 인력 추가보다 효과적
- [No Silver Bullet] — Brooks의 1986년 후속 논문, 본질적 복잡도와 우연적 복잡도 구분

---

<a id="hollywood-principle"></a>
## Hollywood Principle / Inversion of Control (IoC)

**원전**: 1980년대 후반 Smalltalk·Lisp 커뮤니티에서 유래; Richard E. Sweet, *The MESA Programming Language* (1985) 부근에서 "Don't call us, we'll call you" 표현 정착. Martin Fowler, *Inversion of Control* (2005) 정리
**한 줄 정의**: "Don't call us, we'll call you." — 사용자 코드가 framework를 호출하는 대신, framework가 사용자 코드를 호출한다.

**의도**: 일반적인 라이브러리는 *사용자 코드가 라이브러리 함수를 호출* 하지만, framework·플랫폼은 *framework가 사용자 코드를 호출* 한다. 이 흐름 반전(inversion)이 framework의 정체성이다. Spring DI, React 컴포넌트 lifecycle, AWS Lambda 핸들러, Android Activity 모두 같은 패턴.

**적용 사례**:
- React: 사용자가 `render()`를 직접 호출하지 않고, React가 적절 시점에 컴포넌트 함수를 호출
- Spring: 객체 생성·주입을 컨테이너가 담당, 사용자는 `@Component`·`@Autowired`로 선언만
- Event-driven: callback·observer·promise는 모두 IoC의 한 형태
- Plugin 시스템: 호스트가 정해진 인터페이스에 따라 플러그인의 메서드를 호출

**반례·오해**:
- IoC ≠ DI (Dependency Injection). DI는 IoC의 *한 형태* (Fowler 2005). IoC가 더 넓은 개념
- "framework는 좋고 라이브러리는 나쁘다"는 오해. IoC는 통제권 비용을 동반 — 디버깅·추적이 어려워지고 magic이 늘어남
- 모든 콜백이 IoC라는 단순화도 부정확 — 사용자가 직접 호출하는 콜백(예: `Array.map(callback)`)은 부분 inversion에 가까움

**관련 표준/원칙**:
- [DIP](solid.md#5-dependency-inversion-principle-dip-의존-역전-원칙) — IoC의 클래스 수준 구현 원칙
- [Composition over Inheritance](#composition-over-inheritance) — 합성 + DI가 IoC의 실천 수단
- [Template Method](#) — Hollywood Principle의 고전적 GoF 패턴

---

<a id="boy-scout-rule"></a>
## Boy Scout Rule

**원전**: Robert C. Martin (Uncle Bob), *Clean Code: A Handbook of Agile Software Craftsmanship* (Prentice Hall 2008), Chapter 1 — 미국 보이스카우트 규칙 "Leave the campground cleaner than you found it"의 코딩 응용
**한 줄 정의**: "Always leave the code cleaner than you found it." — 만진 코드는 원래보다 깨끗하게 두고 떠난다.

**의도**: 모든 개발자가 자신이 작업한 코드를 *조금이라도* 더 좋게 만들고 떠나면 코드베이스는 시간이 갈수록 좋아진다. 대규모 리팩토링이 아니라 *작은 개선* — 이름 명확화, 중복 제거, 죽은 코드 삭제, 주석 갱신 등 — 의 누적 효과를 노린다.

**적용 사례**:
- 버그 수정 PR에 그 함수의 변수명 명확화 1개 끼워넣기
- 매번 작업 시 잘못된 주석·dead code·미사용 import 정리
- TODO/FIXME 중 자기 작업 영역과 관련된 항목 처리
- 테스트 추가/누락 발견 시 즉시 보강

**반례·오해**:
- "리팩토링과 기능 변경을 한 PR에 섞으라"는 의미가 아니다. PR 분리가 원칙이며, Boy Scout Rule은 *기회 포착과 작은 개선의 습관화*가 핵심
- 모든 코드를 자기 취향으로 재작성하는 행위는 오해의 결과. 객관적 개선(이름의 모호함, 중복, dead code)에 한정
- "코드 소유권이 없는 곳까지 손대라"는 의미도 아니다 — 자신이 *맡은 작업의 맥락 내* 에서만 적용
- Linter·formatter로 자동화 가능한 부분은 도구에 위임 (수동 boy scout 행위로 PR 노이즈 증가 방지)

**관련 표준/원칙**:
- [Code Smells](code-smells.md) — boy scout가 발견·제거할 대상 카탈로그
- [DRY](#dry-dont-repeat-yourself-반복-금지) — 작업 중 발견된 중복 제거
- [Continuous Refactoring] — boy scout rule의 일상화된 형태

---

<a id="pareto-principle"></a>
## Pareto Principle (80/20 Rule)

**원전**: Vilfredo Pareto, 이탈리아 경제학자 (1896년 이탈리아 토지 소유 분포 관찰); Joseph M. Juran이 1940년대 품질 관리 맥락으로 일반화하며 "Pareto Principle" 명명
**한 줄 정의**: "Roughly 80% of consequences come from 20% of causes." — 결과의 80%는 원인의 20%에서 나온다.

**의도**: 효과·노력·문제·매출의 분포가 균등하지 않고 소수의 핵심 요인이 압도적 비중을 차지한다는 경험적 관찰. 소프트웨어 맥락에서는 우선순위 결정·성능 최적화·버그 수정 자원 배분의 기준이 된다.

**적용 사례**:
- 성능 최적화: 프로파일링으로 시간의 80%를 차지하는 hot path 20%를 식별해 집중 최적화
- 버그 수정: 80%의 사용자 영향은 20%의 버그에서 발생 — 영향도 기반 우선순위
- 기능 사용 분석: 80%의 사용자가 20%의 기능만 사용 — 나머지 기능은 단순화·제거 후보
- 코드 리뷰: 80%의 결함은 20%의 모듈에서 발생 — 리스크 모듈 중점 리뷰

**반례·오해**:
- 80/20은 *정확한 비율이 아니라 메타포* — 실제 분포는 70/30, 90/10, 99/1 등 다양. 핵심은 *비대칭성*이 존재한다는 것
- "20%만 잘 하면 된다"는 오해. 나머지 80%도 무시할 수 없는 경우 多 (예: 보안·접근성·법적 요구사항은 빈도가 낮아도 무시 불가)
- 측정 없이 "이게 20%일 것이다"라고 *추측*하면 위험 — 반드시 데이터(프로파일러, 사용량 로그, 버그 트래커)로 식별
- Goodhart의 법칙과 결합 시 위험: 80/20 측정이 KPI가 되면 게이밍 발생

**관련 표준/원칙**:
- [YAGNI](#yagni-you-arent-gonna-need-it-불필요-기능-금지) — 사용되지 않는 80% 기능 제거의 정당화 근거
- [Goodhart's Law](#goodhart-law) — Pareto 측정을 KPI로 만들 때의 부작용
- [Premature Optimization] — Pareto 식별 *전*의 최적화는 Knuth의 "premature optimization is the root of all evil"

---

<a id="goodhart-law"></a>
## Goodhart's Law

**원전**: Charles Goodhart, *Problems of Monetary Management: The U.K. Experience* (1975); Marilyn Strathern의 1997년 압축형이 더 유명 — "When a measure becomes a target, it ceases to be a good measure."
**한 줄 정의**: "When a measure becomes a target, it ceases to be a good measure." — 측정이 목표가 되는 순간 더 이상 좋은 측정이 아니다.

**의도**: 어떤 지표가 *목표*나 *보상의 기준*이 되면, 사람들이 그 지표를 최적화하기 위해 행동을 바꾸고, 결국 원래 측정하려던 것과 지표 사이의 상관관계가 깨진다. KPI·OKR·자동화된 보상 시스템의 근본 함정.

**적용 사례** (안티패턴 인식):
- 코드 커버리지를 KPI로 → 의미 없는 assertion(`assertNotNull(x)`)으로 커버리지만 채움
- 버그 수정 건수가 보상 기준 → 작은 버그 일부러 등록 후 자기 해결
- 응답 시간 SLA → 어려운 요청은 의도적 거부, 쉬운 요청만 처리
- LOC(코드 줄 수)로 생산성 측정 → 장황한 코드, 불필요한 추상화

**적용 사례** (대응 방법):
- 단일 지표가 아닌 *다중 균형 지표*(balanced scorecard) 사용 — 커버리지 + 변이 테스트(mutation testing) + 결함률 동시 추적
- 측정을 *진단 도구*로만 사용, *보상 기준*으로 만들지 않음
- 지표를 정기적으로 회전(rotation)해 게이밍 학습 방지

**반례·오해**:
- "그러면 측정하지 말라"는 의미가 아니다. 측정은 필수, *측정과 보상의 분리*가 핵심
- 모든 지표가 게이밍되는 것은 아니다 — *행위자 통제 가능*하고 *직접 보상 연결*된 지표만 위험
- "Campbell's Law"라는 유사 법칙도 있음 (사회과학 맥락, Donald T. Campbell 1976) — 더 일반적

**관련 표준/원칙**:
- [Pareto Principle](#pareto-principle) — 80/20 측정이 KPI화될 때의 Goodhart 위험
- [Hyrum's Law](#hyrum-law) — 관찰 가능한 측정 자체가 의존성/목표가 되는 유사 메커니즘
- [Speculative Generality](code-smells.md#18-speculative-generality-과잉-일반화) — LOC·복잡도 메트릭 KPI화의 부작용

---

<a id="cunningham-law"></a>
## Cunningham's Law

**원전**: Ward Cunningham (WikiWikiWeb 창시자, XP·TDD·Wiki의 아버지)의 격언; Steven McGeady가 Cunningham에게서 들었다며 인용 ([Wikipedia: Ward Cunningham](https://en.wikipedia.org/wiki/Ward_Cunningham))
**한 줄 정의**: "The best way to get the right answer on the internet is not to ask a question; it's to post the wrong answer."

**의도**: 사람들은 질문에 답하기보다 *틀린 답을 바로잡기*에 훨씬 적극적이다. 이 인지적 비대칭성을 이용해 Wiki·Stack Overflow·코드 리뷰 culture가 작동한다. 명시적 질문보다 *명확한 (틀릴 수도 있는) 가설*을 던지면 더 빠르게 정답에 수렴.

**적용 사례** (긍정적 활용):
- PR 본문에 "이렇게 구현했는데 X 측면에서 더 나은 방법이 있을지" 명시적 가설 제시 — 리뷰어가 구체적 피드백 가능
- RFC/Design Doc에 "현재 후보안: A"를 명확히 적고 검토 요청 — 막연한 "의견 주세요"보다 효과적
- TDD: *실패하는 테스트* 작성이 곧 "틀린 상태 게시" — 코드가 그 틀림을 바로잡는 행위
- 코드 리뷰에서 명확한 입장을 가진 의견이 침묵보다 더 많은 토론·개선을 유발

**반례·오해**:
- "고의로 틀린 정보를 퍼뜨리라"는 의미가 아니다. *진심으로 시도한 답*이 틀렸을 때의 피드백 효과를 활용하라는 의미
- 모든 도메인에서 작동하지 않음 — 잘못된 의료/법률 정보는 정정보다 확산이 우세할 수 있음 (피드백 메커니즘이 약한 도메인)
- "질문 자체가 무용하다"는 오해 — 잘 구성된 질문은 여전히 유효, Cunningham's Law는 *추가 도구*
- 동료를 가스라이팅하거나 일부러 잘못 적어 시간 낭비를 유발하는 행위는 안티패턴

**관련 표준/원칙**:
- [Boy Scout Rule](#boy-scout-rule) — 작은 정정의 누적 효과와 철학적 공명
- [TDD Red Phase] — 실패 테스트가 "틀린 상태"를 명시적으로 게시
- [Code Review Culture] — 명확한 가설 제시 → 구체적 피드백 → 빠른 수렴 사이클

---

## 거시 원칙·스멜 cross-link 매트릭스

| 미시 원칙 | 관련 거시 원칙 / 스멜 |
|----------|---------------------|
| DRY | [code-smells.md — Duplicate Code](code-smells.md), [solid.md — SRP](solid.md) |
| KISS | [code-smells.md — Speculative Generality](code-smells.md), [solid.md — OCP](solid.md) (과한 추상화 차단) |
| YAGNI | [code-smells.md — Speculative Generality](code-smells.md), [code-smells.md — Lazy Class](code-smells.md) |
| LoD | [code-smells.md — Message Chains](code-smells.md), [code-smells.md — Feature Envy](code-smells.md), [grasp.md — Low Coupling](grasp.md) |
| SoC | [solid.md — SRP](solid.md), [grasp.md — High Cohesion](grasp.md) |
| Tell, Don't Ask | [code-smells.md — Feature Envy](code-smells.md), [grasp.md — Information Expert](grasp.md) |
| Composition over Inheritance | [code-smells.md — Refused Bequest](code-smells.md), [solid.md — LSP](solid.md) |
| SSoT | [code-smells.md — Duplicate Code](code-smells.md), [12-factor.md — III Config](12-factor.md) |
| Conway's Law | [grasp.md — Low Coupling](grasp.md), [Inverse Conway Maneuver](#inverse-conway-maneuver) |
| Inverse Conway Maneuver | [Conway's Law](#conway-law), Team Topologies (Skelton & Pais 2019) |
| Hyrum's Law | [solid.md — OCP](solid.md), [code-smells.md — Speculative Generality](code-smells.md) |
| Postel's Law | [Hyrum's Law](#hyrum-law), [solid.md — DIP](solid.md) |
| Brooks's Law | [Conway's Law](#conway-law), [KISS](#kiss-keep-it-simple-stupid-단순함-원칙) |
| Hollywood Principle / IoC | [solid.md — DIP](solid.md), [Composition over Inheritance](#composition-over-inheritance) |
| Boy Scout Rule | [code-smells.md (전체)](code-smells.md), [DRY](#dry-dont-repeat-yourself-반복-금지) |
| Pareto Principle | [YAGNI](#yagni-you-arent-gonna-need-it-불필요-기능-금지), [Goodhart's Law](#goodhart-law) |
| Goodhart's Law | [Pareto Principle](#pareto-principle), [Hyrum's Law](#hyrum-law) |
| Cunningham's Law | [Boy Scout Rule](#boy-scout-rule), TDD Red Phase |

---

## 카테고리별 분류

| 카테고리 | 원칙 |
|----------|------|
| **코드 설계** | DRY · KISS · YAGNI · LoD · SoC · Tell-Don't-Ask · Composition over Inheritance · SSoT |
| **조직·사회 시스템** | Conway's Law · Inverse Conway Maneuver · Brooks's Law |
| **API·상호운용성** | Hyrum's Law · Postel's Law |
| **아키텍처 흐름** | Hollywood Principle (IoC) |
| **문화·습관** | Boy Scout Rule · Cunningham's Law |
| **경영·측정** | Pareto Principle · Goodhart's Law |

---

## 표준 인용

- Andy Hunt, Dave Thomas, *The Pragmatic Programmer* (1999) — DRY 원전
- Kent Beck, *Extreme Programming Explained* (1999) — YAGNI 원전
- Ian Holland, *Law of Demeter* (1987, Northeastern University)
- Edsger W. Dijkstra, *On the role of scientific thought* (1974) — SoC 원전
- Erich Gamma et al., *Design Patterns* (1994) — Composition over Inheritance 원전
- Alec Sharp, *Smalltalk by Example* (1997) — Tell, Don't Ask 원전
- Melvin Conway, *How Do Committees Invent?*, Datamation (April 1968) — Conway's Law 원전
- Matthew Skelton, Manuel Pais, *Team Topologies* (IT Revolution 2019) — Inverse Conway Maneuver 정립
- Titus Winters et al., *Software Engineering at Google* (O'Reilly 2020) — Hyrum's Law 정립
- Jon Postel, *RFC 793: Transmission Control Protocol* (September 1981) — Robustness Principle 원전
- Martin Thomson, *RFC 9413: Maintaining Robust Protocols* (IETF 2023) — Postel's Law 현대적 재평가
- Fred Brooks, *The Mythical Man-Month* (Addison-Wesley 1975) — Brooks's Law 원전
- Fred Brooks, *No Silver Bullet — Essence and Accident in Software Engineering* (1986)
- Martin Fowler, *Inversion of Control* (2005, martinfowler.com) — IoC 정리
- Robert C. Martin, *Clean Code* (Prentice Hall 2008) — Boy Scout Rule 정립
- Vilfredo Pareto, *Cours d'économie politique* (1896) — 80/20 분포 관찰
- Joseph M. Juran, *Quality Control Handbook* (1951) — Pareto Principle 명명
- Charles Goodhart, *Problems of Monetary Management: The U.K. Experience* (1975) — Goodhart's Law 원전
- Marilyn Strathern, *'Improving ratings': audit in the British University system*, European Review 5 (1997) — Goodhart 압축형 인용
- Ward Cunningham — Cunningham's Law (구두 격언, Steven McGeady 인용)

---

<a id="fallacies-distributed-computing"></a>
## Fallacies of Distributed Computing (분산 컴퓨팅의 오류 8가지)

**원전**: L. Peter Deutsch (Sun Microsystems, 1994)가 처음 7개를 정식화, James Gosling이 8번째(network is homogeneous)를 추가; Sun Fellow Bill Joy & Tom Lyon이 초기 4개 기여. 분석·확산은 Arnon Rotem-Gal-Oz, *Fallacies of Distributed Computing Explained* (2006). Deutsch가 Xerox PARC에서 작업하던 1991~1992년경 발상이라는 회고도 있으나, Sun에서의 1994년 정식화가 표준 인용.
**한 줄 정의**: "Essentially everyone, when they first build a distributed application, makes the following eight assumptions. All prove to be false in the long run and all cause big trouble and painful learning experiences." (Deutsch & Gosling)

**의도**: 네트워크로 연결된 분산 시스템을 처음 설계하는 거의 모든 개발자가 무의식적으로 가정하는 8가지 명제 — 모두 *장기적으로 거짓*이며 반드시 장애·데이터 손실·성능 붕괴로 이어진다. 단일 프로세스 안에서 당연하던 함수 호출의 보장(즉시성·신뢰성·무비용)을 네트워크 경계 너머에서도 유효하다고 착각하는 것이 핵심 오류다. 8가지를 명시적 체크리스트로 다뤄 *방어적 설계*(타임아웃·재시도·서킷 브레이커·암호화·관측성)를 강제하는 데 의의가 있다.

**8가지 오류와 현실·대응**:

1. **The network is reliable (네트워크는 신뢰할 수 있다)** — 현실: 패킷 손실·라우터 장애·케이블 단선·split-brain은 항상 발생한다. 대응: 타임아웃 + 재시도(exponential backoff + jitter), idempotency key로 중복 요청 안전화, at-least-once 전송 가정, 데드레터 큐.
2. **Latency is zero (지연은 0이다)** — 현실: 빛의 속도는 물리적 하한이며 대륙 간 RTT는 100ms 이상. 함수 호출처럼 원격 호출을 남발하면 N+1 round-trip이 누적 폭증. 대응: chatty → chunky 인터페이스(배치/coarse-grained), 데이터 지역성(co-location), 캐싱, 비동기·파이프라이닝.
3. **Bandwidth is infinite (대역폭은 무한하다)** — 현실: 링크 용량은 유한하고 페이로드 비대화는 혼잡·큐잉 지연을 부른다. 대응: 압축, 페이지네이션/필터링(필요 필드만 — GraphQL·field mask), 프로토콜 효율화(Protobuf/Avro 같은 바이너리), 백프레셔.
4. **The network is secure (네트워크는 안전하다)** — 현실: 도청·MITM·재전송·스푸핑이 상존. 대응: TLS/mTLS 전구간 암호화, 인증·인가(OAuth2/JWT), 입력 검증, zero-trust(경계 신뢰 폐기), 비밀 관리(secret rotation).
5. **Topology doesn't change (토폴로지는 변하지 않는다)** — 현실: 오토스케일·배포·노드 교체·IP 변경으로 토폴로지는 끊임없이 변한다. 대응: 하드코딩 주소 금지, 서비스 디스커버리(DNS/Consul/Eureka), 동적 로드밸런싱, 헬스체크 기반 라우팅.
6. **There is one administrator (관리자는 한 명이다)** — 현실: 다중 팀·다중 클라우드·서드파티 API가 얽혀 단일 통제점이 없다. 대응: 버전드 API + 후방 호환, 명시적 SLA/계약, 분산 추적(distributed tracing)으로 책임 경계 가시화, 변경 조율 프로토콜(deprecation 정책).
7. **Transport cost is zero (전송 비용은 0이다)** — 현실: 직렬화/역직렬화 CPU, 네트워크 대역폭 요금(특히 클라우드 egress), 마샬링 오버헤드가 실재한다. 대응: 페이로드 최소화, 효율적 직렬화 포맷, egress 비용 인식 설계(데이터 지역성), 호출 횟수 자체 감축.
8. **The network is homogeneous (네트워크는 균질하다)** — 현실: 서로 다른 OS·하드웨어·프로토콜·엔디안·문자셋·버전이 혼재한다. 대응: 표준 상호운용 포맷(JSON/Protobuf), 명시적 스키마·버전 협상, 인코딩 정규화(UTF-8), 벤더 중립 프로토콜.

**적용 사례**:
- 마이크로서비스 간 동기 HTTP 호출 체인에 타임아웃·재시도·서킷 브레이커(Resilience4j/Hystrix/Envoy)를 기본 장착 — 오류 1·2 대응
- gRPC + Protobuf + field mask로 페이로드를 최소화하고 스트리밍으로 round-trip 축소 — 오류 2·3·7·8 대응
- Service Mesh(Istio/Linkerd)로 mTLS·서비스 디스커버리·재시도·관측을 인프라 레벨에서 횡단 제공 — 오류 4·5·6 통합 대응
- 모든 쓰기 API에 idempotency key 강제 + at-least-once 메시징(Kafka/SQS) — 오류 1 대응
- 분산 추적(OpenTelemetry)으로 호출 그래프·지연·실패 지점을 가시화 — 오류 2·6 진단

**반례·오해**:
- "현대 클라우드/5G라서 네트워크가 충분히 빠르고 안정적이다"는 오해 — 가용성은 올랐지만 *물리 법칙(지연)·유한성(대역폭)·부분 실패(reliability)* 는 사라지지 않는다. 오히려 분산 규모가 커지며 부분 실패 확률은 증가
- "8개를 다 막으려고 모든 호출에 재시도·서킷·암호화를 거는 것"은 과잉 — 재시도가 비멱등 연산에 적용되면 중복 부작용을 유발하고, 무분별한 재시도는 retry storm(폭주)을 일으킨다. *멱등성 보장이 선행*되어야 재시도가 안전
- "RPC 프레임워크가 추상화해주니 로컬 호출처럼 써도 된다"는 것이 오류의 근원 — 투명 분산(transparent distribution)은 환상이며, 원격 호출은 명시적으로 *원격답게* 다뤄야 한다 (Waldo et al., *A Note on Distributed Computing*, 1994가 같은 결론)
- 단일 노드/단일 프로세스 애플리케이션에는 적용되지 않는다 — 네트워크 경계가 존재할 때만 유효한 법칙

**관련 표준/원칙**:
- [Postel's Law](#postel-law) — 오류 8(균질성 거짓)·오류 1에 대한 견고성 대응; 다양한 구현 환경 수용
- [Hyrum's Law](#hyrum-law) — 분산 API의 관찰 가능 동작(지연·에러·순서)에 사용자가 의존 → 오류 6(단일 관리자 부재)과 결합 시 변경 위험 가중
- [Conway's Law](#conway-law) — 오류 6(관리자 다수)의 조직적 뿌리; 분산 시스템 경계가 팀·소통 구조를 반영
- [Brooks's Law](#brooks-law) — 커뮤니케이션 경로 n(n-1)/2 폭증은 분산 노드 간 round-trip 폭증(오류 2)과 동형 구조
- [KISS](#kiss-keep-it-simple-stupid-단순함-원칙) — 불필요한 분산화는 8가지 오류 표면적을 키운다; 분산이 필수가 아니면 모놀리스가 우월
- [Resilience Patterns] — Circuit Breaker·Bulkhead·Retry·Timeout·Backpressure는 8가지 오류의 직접 방어 패턴군

---

<a id="end-to-end-argument"></a>
## End-to-End Argument (단대단 논증)

**원전**: J. H. Saltzer, D. P. Reed, D. D. Clark, *End-to-End Arguments in System Design*, ACM Transactions on Computer Systems 2(4) (November 1984), pp. 277–288 — 1981년 Second International Conference on Distributed Computing Systems 발표본을 확장
**한 줄 정의**: "The function in question can completely and correctly be implemented only with the knowledge and help of the application standing at the endpoints of the communication system. Therefore, providing that questioned function as a feature of the communication system itself is not possible."

**의도**: 어떤 기능(에러 복구, 중복 제거, 순서 보장, 암호화, 무결성 검증 등)은 통신의 *양 끝점(endpoint)에 있는 애플리케이션*만이 완전하고 정확하게 구현할 수 있다. 하위 계층(네트워크·전송 경로·중간 노드)이 그 기능을 제공해도 끝점은 어차피 한 번 더 검증해야 하므로, 하위 계층의 구현은 *그 자체로는 충분하지 않다*. 따라서 하위 계층에 기능을 두는 것은 (1) 끝점이 반드시 다시 확인해야 한다는 정확성 이유와 (2) 모든 응용이 그 비용을 강제로 부담한다는 효율 이유에서 일반적으로 정당화되지 않는다. **단, 하위 계층의 부분 구현이 *성능 최적화*(performance enhancement)로서 정당화될 수 있다** — 끝점 검증을 대체하는 것이 아니라 보완할 때에 한해서다.

**핵심 논거 (논문의 file transfer 사례)**:
- 두 호스트가 파일을 전송할 때, 디스크 읽기·메모리·OS·네트워크 카드 등 *어느 단계*에서도 비트가 손상될 수 있다. 네트워크 계층이 아무리 신뢰성 있는 전송을 보장해도, 디스크에서 메모리로 올리는 순간의 손상은 막지 못한다.
- 따라서 *완전한* 정확성은 오직 끝점이 파일 전체를 읽어 체크섬을 검증할 때만 달성된다. 네트워크 계층의 신뢰성 보장은 이 끝점 검증을 *없앨 수 없다* — 끝점이 어차피 검증한다면 하위 계층의 완벽한 보장은 중복 비용일 뿐이다.
- 하위 계층의 패킷 단위 재전송은 *전체를 다시 보내는 것보다 빠르게 만드는 성능 최적화*로서만 정당하다 (정확성의 원천이 아님).

**적용 사례**:
- **TCP 신뢰성**: 패킷 손실·순서 뒤바뀜·중복을 *끝점의 TCP 스택*이 시퀀스 번호·ACK·재전송으로 처리한다. IP(하위 계층)는 best-effort 전달만 하며, 신뢰성은 끝점이 책임진다.
- **종단간 암호화(E2EE)**: Signal·WhatsApp·iMessage는 *송수신 끝점*에서만 평문을 다룬다. 중간 서버·TLS 종단 프록시가 신뢰성·암호화를 제공해도 끝점은 신뢰하지 않고 직접 암복호화한다 — 중간 노드 침해 시에도 기밀성이 유지된다.
- **smart endpoints, dumb pipes** (마이크로서비스 격언, *Building Microservices* 맥락): 메시지 라우팅·변환·비즈니스 로직을 ESB 같은 똑똑한 미들웨어가 아니라 끝점 서비스에 두고, 통신 채널(메시지 브로커)은 단순 전달만 담당한다.
- **인터넷의 dumb network 설계 철학**: 네트워크 코어는 단순하게(라우팅만), 지능은 끝점에 — 이 원리가 인터넷이 임의의 새 응용(웹·VoIP·스트리밍)을 코어 변경 없이 수용한 확장성의 근원이다.
- **애플리케이션 레벨 무결성·재시도**: 멱등 키(idempotency key) 기반 재시도, 응답 본문 체크섬 검증 등은 네트워크가 "성공"이라 보고해도 끝점이 최종 정합성을 책임지는 형태.

**위반 사례 / 안티패턴**:
- 하위 계층(메시지 브로커·네트워크 어플라이언스)이 "exactly-once 전달"을 보장한다고 믿고 끝점에서 멱등성·중복 제거를 생략 — 끝점 장애·재시작 시 중복이 새어 들어온다 (완전한 exactly-once는 끝점 협력 없이는 불가).
- TLS(전송 구간 암호화)만으로 기밀성이 끝났다고 보고 끝점 저장·로깅 단계의 평문 노출을 방치 — TLS는 *구간* 보안일 뿐 *종단간* 보안이 아니다.
- ESB·스마트 미들웨어에 비즈니스 라우팅·검증 로직을 누적시켜 통신 인프라가 도메인 변경에 결합되는 구조 (smart pipes 안티패턴).
- 하위 계층의 부분 신뢰성 보장을 *정확성의 근거*로 오인해 끝점 검증을 제거 — 본 원칙이 명시적으로 금지하는 오용.

**반례·오해**:
- "하위 계층은 절대 기능을 가지면 안 된다"는 오해. 논문은 *성능 최적화로서의 부분 구현은 정당*하다고 명시한다. 무선 링크의 link-layer 재전송(높은 손실률 환경에서 TCP 재전송보다 효율적)이 대표 예 — 끝점 검증을 대체하지 않고 보완하는 한 허용된다.
- "끝점이 처리하니 하위 계층은 무조건 dumb이 최선"이라는 단순화도 부정확. Reed·Saltzer·Clark 자신이 후속 논의에서 비용·성능 트레이드오프에 따라 하위 계층 최적화가 합리적일 수 있음을 인정했다 (active networking·CDN·QoS 논쟁의 출발점).
- "smart endpoints dumb pipes = 미들웨어 전면 금지"라는 오해. 단순 전달·버퍼링·내구성(durability) 같은 *도메인 중립적* 기능은 파이프에 두어도 무방하다 — 금지 대상은 *비즈니스 의미를 가진 지능*이다.
- E2E argument가 "성능 무관 순수 정확성 원칙"이라는 오해. 실제 논문의 절반은 *효율 논거* — 모든 응용에 불필요한 기능을 하위 계층이 강제하면 그 기능이 필요 없는 응용까지 비용을 치른다는 점이 핵심 동기다.

**관련 표준/원칙**:
- [Postel's Law](#postel-law) — 둘 다 Jon Postel/인터넷 설계 계보. Postel이 *경계에서의 관용/엄격* 을 다룬다면 E2E는 *기능을 어느 계층에 둘 것인가* 를 다룬다 (상보적 인터넷 설계 원리)
- [Single Source of Truth](#ssot) — 정확성(무결성)의 권위 있는 검증 위치를 끝점 하나로 고정한다는 점에서 공명
- [SoC](#separation-of-concerns-soc-관심사-분리) — 통신 채널의 관심사(전달)와 응용의 관심사(정확성·보안)를 계층 분리
- [DIP](solid.md#5-dependency-inversion-principle-dip-의존-역전-원칙) — dumb pipes는 추상화된 전달 메커니즘에 의존하고 끝점이 정책을 소유 (제어 위치 역전과 유사한 구도)
- [Defensive Programming] — 끝점에서 하위 계층을 신뢰하지 않고 재검증하는 자세는 외부 경계 방어 코딩의 분산 시스템 버전
