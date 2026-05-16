# advisor 모드 예시 10개

dev-advisor `## 워크플로우` 9 모드 + 카탈로그 lookup 의 실제 호출/응답 예. SKILL.md 의 `## 예시 → references/examples.md` pointer 에서 참조.

상세 산출물 템플릿: [output_templates.md](output_templates.md)

---

## 예시

### A. 카탈로그 lookup 호출 — Singleton

```
User: /pattern singleton
```

응답:

```kotlin
// Kotlin Singleton 패턴
object DatabaseConnection {
    private var connection: Connection? = null
    fun getConnection(): Connection = connection ?: createConnection().also { connection = it }
    private fun createConnection(): Connection { /* 연결 생성 로직 */ return Connection() }
}
```

**적용 위치 제안**: `src/main/kotlin/com/yourpackage/data/DatabaseConnection.kt`
**관련 패턴**: Factory Method (객체 생성 분리), Prototype (인스턴스 복제)

상세 표준 산출물 템플릿은 [`output_templates.md`](output_templates.md) 참조.

---

### B. recommend 모드 — 결제 시스템 아키텍처 추천

```
User: /dev-advisor recommend "신용카드/페이팔/암호화폐 결제 통합, 월 1M 트랜잭션 예상"
```

**후보 매트릭스**:

| # | 패턴 ID | 적합 컨텍스트 | trade-off | score |
|---|---------|--------------|-----------|------:|
| 1 | [strategy](patterns/behavioral.md) + [factory-method](patterns/creational.md) | 결제 수단별 독립 알고리즘 + 신규 추가에 OCP | 추상화 클래스 ↑ | 5 |
| 2 | [chain-of-responsibility](patterns/behavioral.md) | 결제 전 단계 검증(잔액→사기 탐지→한도) 체이닝 | 디버깅 난이도 | 3 |
| 3 | [saga](patterns/distributed.md) | 결제+포인트 차감 분산 트랜잭션 | 보상 트랜잭션 설계 비용 | 4 |

**5단계 "왜"**:
- **선택**: Strategy + Factory Method (#1)
- **근거**: 결제 수단이 *액터별 변경* — [SRP](principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) + [OCP](principles/solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙). 향후 결제 수단 추가 시 기존 코드 무수정.
- **대안 비교**: switch 분기(#1 위반→ Shotgun Surgery) vs Strategy(#1) vs CoR(#2, 결제 자체보다 검증 단계 책임)
- **표준 인용**: [SOLID OCP](principles/solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙), [GoF Strategy](patterns/behavioral.md), ISO 25010 Modifiability
- **적용 조건**: 결제 수단 3종 이상, 향후 추가 예상
- **비추천 조건**: 결제 수단 1~2종에 고정 → KISS 위반, 단순 분기로 충분

**6단계 후속**: 트랜잭션 1M/월 → [saga](patterns/distributed.md) 별도 검토. 아키텍처 영향 ≥ 3 파일 예상 → `architect` 에이전트 hand-off.

---

### C. validate 모드 — SOLID 위반 검증

```
User: /dev-advisor validate src/order/OrderProcessor.kt
```

**위반 항목 표**:

| 위치 | 표준 | 심각도 | 영향 | 조치 |
|------|------|:-----:|------|------|
| OrderProcessor.kt:1~340 | [SRP](principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) | **P1** | 회계+재고+알림 3 액터 변경이 한 클래스로 집중 → 회귀 위험 | [Extract Class](principles/code-smells.md#2-large-class) — Accounting/Inventory/Notification 분리 |
| OrderProcessor.process():L120~L210 (90줄) | [Long Method](principles/code-smells.md#1-long-method) | P2 | 가독성/테스트성 저하 | Extract Function 6~8회 |
| `new MySqlOrderRepo()` 직접 호출 L45 | [DIP](principles/solid.md#5-dependency-inversion-principle-dip-의존-역전-원칙) | P2 | 단위 테스트 mock 주입 불가 | Repository 인터페이스 추출 + DI |
| switch(orderType) L180 | [OCP](principles/solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙) / [Switch Statements](principles/code-smells.md#7-switch-statements) | P3 | 신규 주문 타입 추가 시 분기 확장 | Replace Conditional with Polymorphism |

**5단계 "왜"** (alias: 예외·면제 조건):
- **판정**: P1 1건 + P2 2건 → SRP/DIP 위반 시급, refactor 모드 hand-off 권장
- **근거**: 액터 3종 식별 (회계→가격/세금, 재고→차감/롤백, 알림→이메일/SMS) — 변경 이력 90일 분석 시 3 액터 각자 5회 이상 OrderProcessor 수정
- **대안 비교**: Big-bang 분리 vs 점진적 Extract Class vs Strangler Fig
- **표준 인용**: [SOLID SRP/DIP](principles/solid.md), [Fowler 2nd ed.](principles/code-smells.md)
- **적용 조건**: 변경 빈도 ≥ 월 3회 클래스
- **예외·면제 조건**: 단일 액터 + LOC < 100 인 작은 클래스는 분리 강제 안 함

**6단계**: refactor 모드 hand-off → `code-reviewer` 에이전트 PR 검토.

---

### D. refactor 모드 — God Class 분해

```
User: /dev-advisor refactor src/order/OrderProcessor.kt:process()
```

**변환 플랜**:

| 단계 | 변경 | 위험 | 롤백 포인트 |
|------|------|------|-----------|
| 1 | 회계 책임 추출 → `PricingCalculator` 신규 + 위임 호출 | 낮음 | git revert |
| 2 | 재고 책임 추출 → `InventoryService` 신규 + Repository DIP | 중 | 재고 동시성 회귀 — 통합 테스트 필수 |
| 3 | 알림 책임 추출 → `OrderNotifier` 신규 + 이벤트 발행 | 낮음 | 메시지 큐 비활성화 |
| 4 | OrderProcessor 를 Use Case Orchestrator 로 축소 (~60줄) | 중 | 단계 1~3 commit pin |

**Before** (요지):
```kotlin
class OrderProcessor {
    fun process(order: Order) {
        val price = order.items.sumOf { it.price * (1 + TAX) }  // 회계 책임
        val repo = MySqlOrderRepo()                              // DIP 위반
        repo.deductInventory(order.items)                        // 재고 책임
        EmailService().send(order.user.email, "주문 완료")        // 알림 책임
    }
}
```

**After** (요지):
```kotlin
class OrderProcessor(
    private val pricing: PricingCalculator,
    private val inventory: InventoryService,
    private val notifier: OrderNotifier
) {
    fun process(order: Order) {
        val priced = pricing.apply(order)
        inventory.deduct(priced.items)
        notifier.notifyComplete(priced)
    }
}
```

**5단계 "왜"**: SOLID SRP + DIP 동시 해결. 회계/재고/알림 단위 테스트 격리. **비추천 조건**: 변경 빈도 낮은 레거시 클래스는 ROI 부족.
**6단계 hand-off**: `code-reviewer` PR 리뷰 → `verifier` 회귀 테스트.

---

### E. maintain 모드 — 기술 부채 점검

```
User: /dev-advisor maintain src/legacy/
```

**부채 표**:

| 위치 | 스멜 | 그룹 | 영향 × 발생빈도 | 권장 리팩토링 |
|------|------|------|----------------|--------------|
| UserService.kt:L1~520 (520줄, 47 메서드) | [Large Class](principles/code-smells.md#2-large-class) | Bloater | 5×5 = P1 | Extract Class × 4 |
| process(req: Request, user: User, ctx: Ctx, cfg: Cfg, log: Log, ...) | [Long Parameter List](principles/code-smells.md#4-long-parameter-list) | Bloater | 4×5 = P1 | Introduce Parameter Object |
| getUser().getAddress().getCity().getZip() L88 | [Message Chains](principles/code-smells.md#21-message-chains) | Coupler | 3×4 = P2 | Hide Delegate |
| // TODO: 2020 변경 — 더 이상 사용 안 함 (L312~318) | [Dead Code](principles/code-smells.md#17-dead-code) | Dispensable | 2×3 = P3 | Remove Dead Code |
| `if (level == "ADMIN") ... else if ("USER") ...` × 7곳 | [Repeated Switches](principles/code-smells.md#6-repeated-switches) | OO Abuser | 4×5 = P1 | Replace Conditional with Polymorphism |

**5 그룹 분포**: Bloaters 2 / Couplers 1 / Dispensables 1 / OO Abusers 1

**5단계 "왜"** (alias: 수용 가능 조건):
- **판정**: P1 3건 우선 — Large Class, Long Parameter List, Repeated Switches
- **근거**: 변경 빈도 (월 8회) × 영향 범위 (47 메서드) 결합
- **대안 비교**: 전체 재작성 vs 점진적 Extract vs Strangler Fig (점진 권장)
- **표준 인용**: [Fowler 22 스멜](principles/code-smells.md), [SOLID SRP](principles/solid.md), [ISO 25010 Maintainability](principles/iso25010.md#7-maintainability-유지보수성)
- **적용 조건**: P1 부채 = sprint 우선순위 큐 진입
- **수용 가능 조건**: deprecated 예정 모듈 또는 외부 contract 고정 → 부채 그대로 둬도 OK

**6단계 hand-off**: `/oh-my-claudecode:ai-slop-cleaner` deslop → `code-reviewer` PR 리뷰.

---

### F. security-audit 모드 — 결제 API 보안 점검

```
User: /dev-advisor security-audit api/payment/handler.go
```

**STRIDE 위협 매트릭스**:

| 컴포넌트 | 위협 유형 | 시나리오 | DREAD | 대응책 |
|---------|----------|----------|------:|--------|
| POST /payments | Spoofing | 타인 JWT 토큰 재사용 | 7.2 | jti claim 검증, 짧은 만료시간 ([RFC 7519](security/security-authn.md)) |
| Payment DB | Tampering | DML 직접 실행으로 금액 변조 | 9.0 | DB 감사 로그, ORM only 접근 |
| 결제 로그 | Repudiation | 거래 사실 부인 | 6.5 | 불변 감사 로그 (S3 WORM) |
| 카드 번호 필드 | Info Disclosure | 응답에 PAN 평문 노출 | 9.5 | 토크나이제이션, PCI-DSS 마스킹 |
| 결제 게이트웨이 | DoS | 외부 PG 지연으로 스레드 고갈 | 7.0 | [Circuit Breaker](patterns/reliability.md), Timeout |
| 관리자 API | Elevation of Privilege | 일반 사용자가 환불 승인 호출 | 8.5 | RBAC, Scope 검증 |

**컴플라이언스 매핑**:

| 요구사항 | 표준 조항 | 적합 | 증거 |
|---------|----------|:----:|------|
| 카드 데이터 마스킹 | PCI-DSS 3.4 | ❌ | handler.go:L88 PAN 평문 응답 — **P1 즉시 수정** |
| 거래 로그 1년 보존 | PCI-DSS 10.7 | ✅ | S3 lifecycle 365d |
| TLS 1.2+ | PCI-DSS 4.1 | ✅ | nginx config |
| MFA (관리자) | PCI-DSS 8.4 | ⚠️ | TOTP 적용, FIDO2 권장 ([WebAuthn](security/security-authn.md)) |

**5단계 "왜"**:
- **판정**: DREAD ≥ 8 인 위협 3건 (Tampering 9.0 / Info Disclosure 9.5 / EoP 8.5) — P1
- **근거**: 결제는 금전 영향 직결 — STRIDE 6 카테고리 전 영역 노출
- **대안 비교**: API Gateway 통합 vs 핸들러 내 직접 검증 vs Sidecar (API Gateway 권장)
- **표준 인용**: [OWASP API Top 10](security/security-api-web.md), [NIST SP 800-63](security/security-authn.md), [PCI-DSS 4.0](security/compliance.md)
- **적용 조건**: 카드 데이터 / 금전 트랜잭션 처리 API 전체
- **비추천 조건**: 내부 전용 admin tool (외부 노출 안 됨) → STRIDE 일부만 적용

**6단계 hand-off**: `security-reviewer` 정식 threat model 확정 → `verifier` 회귀 확인.

상세 산출물 마크다운 스켈레톤은 [`output_templates.md`](output_templates.md) 참조.

---

### G. full 모드 — 예약 시스템 모듈 종합 점검

Flutter 프로젝트의 예약 도메인 핵심 Repository 단일 파일을 7 기본 advisor 모드 전체로 순차 점검하는 종합 진단. 단일 모드로는 놓치기 쉬운 도메인 cross-cutting 이슈(아키텍처 ↔ 보안 ↔ 품질 ↔ 부채)를 한 번에 식별한다.

```
User: /dev-advisor full packages/data/lib/src/repositories/booking_repository_impl.dart
```

**7 sub-섹션 출력**:

**1) RECOMMEND 단계** — 현재 패턴 적합도 평가 + 대안 후보:

| # | 패턴 ID | 현재 상태 | 대안 trade-off | score |
|---|---------|----------|---------------|------:|
| 1 | [repository](patterns/structural.md) | 적용됨 (단일 BookingRepositoryImpl) | 6 책임 누적 → SRP 한계 도달 | 2 |
| 2 | [data-mapper](patterns/structural.md) | 미적용 | DTO↔Entity 변환 명시적 분리 | 4 |
| 3 | [cqrs](patterns/architectural.md) | 미적용 | read/write 분리, 1000+ TPS 시 필수 | 4 |
| 4 | sub-Repository 분리 (Aggregate 단위) | 미적용 | Booking/Slot/Payment 3 Aggregate 분리 | **5** |

**2) VALIDATE 단계** — 위반 항목:

| 위치 | 표준 | 심각도 |
|------|------|:-----:|
| BookingRepositoryImpl 6 책임 (예약/슬롯/결제/알림/PII 로깅/이력) | [SRP](principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙) | **P1** |
| `import 'package:ui/...'` L12 (data → ui 역방향 의존) | [Clean Architecture 의존성 규칙](patterns/architectural.md#9-clean-architecture) | **P1** |
| `new DioClient()` 직접 호출 L45 | [DIP](principles/solid.md#5-dependency-inversion-principle-dip-의존-역전-원칙) | P2 |
| createBooking() 152줄 | [Long Method](principles/code-smells.md#1-long-method) | P2 |
| Aggregate 경계 모호 (Slot 직접 update) | [DDD Aggregate](patterns/ddd-tactical.md#3-aggregate) | P2 |
| switch(bookingType) L210 | [OCP](principles/solid.md#2-openclosed-principle-ocp-개방-폐쇄-원칙) | P3 |
| 매직 넘버 90 (TTL) | [Magic Number](principles/code-smells.md) | P3 |
| 미사용 import × 4 | [Dead Code](principles/code-smells.md#17-dead-code) | P3 |
| getter 체이닝 4단 L188 | [Message Chains](principles/code-smells.md#21-message-chains) | P3 |

**3) SECURITY-AUDIT 단계** — STRIDE 매트릭스:

| 위협 유형 | 시나리오 | DREAD | 대응 |
|----------|----------|------:|------|
| Spoofing | JWT 재사용 가능 (jti 미검증) | 7.5 | jti + 짧은 exp ([RFC 7519](security/security-authn.md)) |
| Tampering | idempotency-key 미적용 → 중복 결제 | 8.5 | UUID idempotency-key + DB unique |
| Info Disclosure | `log.info(user.email)` L89 평문 PII 로깅 | **9.5** | [pseudonymization](security/security-data-protection.md#6-pseudonymization-가명처리) — hash/mask |
| Repudiation | 예약 변경 이력 없음 | 6.0 | 불변 audit log |
| DoS | 슬롯 조회 캐시 없음 | 5.5 | Redis cache + rate limit |
| EoP | 타 유저 예약 cancel 가능 (ownership 미검증) | 8.0 | 리소스 소유권 검증 미들웨어 |

**4) QA 단계** — 프로세스 품질:

| QA 항목 | 판정 | 근거 |
|---------|------|------|
| [requirements-traceability](quality/qa.md#qa-requirements-traceability) | GAP | 예약 취소 ownership 요구사항에 테스트 연결 없음 |
| [test-strategy](quality/qa.md#qa-test-strategy) | CONDITIONAL | 보안/회귀 경로는 있으나 idempotency 테스트 전략 누락 |
| [release-readiness](quality/qa.md#qa-release-readiness) | FAIL | P1 보안 결함 3건으로 go/no-go 보류 |

**5) QC 단계** — 실행 증거:

| QC 항목 | 판정 | 차단 여부 |
|---------|------|----------|
| [test-execution-evidence](quality/qc.md#qc-test-execution-evidence) | GAP | 결제 중복 방지 테스트 실행 증거 없음 |
| [quality-gate](quality/qc.md#qc-quality-gate) | FAIL | PII 로깅 scanner 실패 |
| [post-release-smoke](quality/qc.md#qc-post-release-smoke) | N/A | 릴리즈 전 단계 |

**6) MAINTAIN 단계** — 5 그룹 부채 분포:

| 위치 | 스멜 | 그룹 | 영향 × 빈도 |
|------|------|------|------------|
| BookingRepositoryImpl 510줄 | Large Class | Bloater | 5×5 = P1 |
| createBooking 152줄 | Long Method | Bloater | 4×4 = P1 |
| Booking/Slot/Payment 강결합 | Inappropriate Intimacy | Coupler | 4×3 = P2 |
| 미사용 helper × 5 | Dead Code | Dispensable | 2×3 = P3 |
| switch(bookingType) | Repeated Switches | OO Abuser | 3×4 = P2 |

**5 그룹 분포**: Bloaters 2 / Couplers 1 / Dispensables 1 / OO Abusers 1

**7) REFACTOR 단계** — Top 3 부채 Before/After:

| 단계 | 변경 | 위험 |
|------|------|------|
| 1 | PII 로깅 제거 → `log.info(user.id.hash)` | 낮음 |
| 2 | Aggregate 분리 → BookingRepo / SlotRepo / PaymentRepo | 중 |
| 3 | data → ui 의존 제거 (Result type 도입) | 중 |

**Before** (L89):
```dart
log.info('booking created for ${user.email}'); // PII 평문
```

**After**:
```dart
log.info('booking created for user=${user.id.hashed}'); // 의사익명화
```

**통합 우선순위 Top 10** (P1 across all domains):
1. [P1, Security] PII 평문 로깅 — booking_repository_impl.dart:89
2. [P1, Architecture] data → ui 역방향 의존 — clean-arch 의존성 규칙 위반
3. [P1, Security] idempotency-key 미적용 — 중복 결제 위험 (DREAD 8.5)
4. [P1, SOLID] BookingRepositoryImpl 6 책임 — SRP 위반
5. [P1, Maintain] 510줄 Large Class — 변경 빈도 월 8회
6. [P1, Security] 리소스 소유권 미검증 — EoP DREAD 8.0
7. [P2, SOLID] DioClient 직접 호출 — DIP 위반
8. [P2, DDD] Aggregate 경계 모호 — Slot 직접 update
9. [P2, Maintain] createBooking 152줄 — Long Method
10. [P2, QA/QC] idempotency 회귀 테스트 전략/실행 증거 누락 — release readiness 차단

**통합 6 필드 산출**:
- **선택/판정**: Repository 패턴 적용했으나 6 책임 누적 → Booking/Slot/Payment Aggregate 분리 권장 + PII 즉시 차단
- **근거**: SRP + GRASP Low Coupling + DDD Aggregate 모두 위반 + ISO 25010 Maintainability/Security 영향
- **대안 비교**: A) 6개 sub-Repo 분리 (Aggregate 단위) / B) Use Case 추출 (Application Service 도입) / C) CQRS (read/write 분리) — TPS 1000+ 시 C 필수
- **표준 인용**: [solid.md#srp](principles/solid.md#1-single-responsibility-principle-srp-단일-책임-원칙), [ddd-tactical.md#aggregate](patterns/ddd-tactical.md#3-aggregate), [security-data-protection.md#pseudonymization](security/security-data-protection.md#6-pseudonymization-가명처리), [clean-architecture.md](patterns/architectural.md#9-clean-architecture), [iso25010.md#maintainability](principles/iso25010.md#7-maintainability-유지보수성)
- **적용 조건**: 동시 사용자 1000+ AND PII 보유 시 → 즉시 진행. PII만 있고 트래픽 낮으면 1순위 (PII) 만 즉시
- **비추천/예외/품질 차단 조건**: prototype/POC 단계 AND PII 미보유 → 부분 적용 가능. PII scanner 또는 quality gate 실패 시 릴리즈 차단.

**6단계 hand-off**: `security-reviewer` (P1 PII 가장 시급, DREAD 9.5) → `architect` (data 계층 재설계 + Aggregate 분리 설계) → `executor` (단계별 refactor) → `verifier` (회귀 테스트).

---

### H. swarm 모드 — 동일 모듈 병렬 심층 분석

`full` 모드와 동일한 7 기본 모드를 단일 context 순차가 아닌 **7 Claude Code 서브에이전트 병렬 + 1 reviewer 통합** 으로 실행하는 심층 audit. 각 모드가 독립 context 를 가져 깊이가 더해지지만 OMC `ultrawork` 의존 + 토큰 비용 ↑.

```
User: /dev-advisor swarm packages/data/lib/src/repositories/booking_repository_impl.dart
```

**ULW 발사** (7 + 1 = 8 Claude Code 서브에이전트 병렬):

```text
Task(subagent_type="oh-my-claudecode:executor", model="opus", description="recommend", prompt="recommend booking_repository_impl") — 후보 매트릭스 4행
Task(subagent_type="oh-my-claudecode:executor", model="opus", description="validate", prompt="validate booking_repository_impl") — 위반 P1×3, P2×6, P3×11
Task(subagent_type="oh-my-claudecode:executor", model="opus", description="security-audit", prompt="security-audit booking_repository_impl") — STRIDE 6 + DREAD
Task(subagent_type="oh-my-claudecode:executor", model="opus", description="qa", prompt="qa booking_repository_impl") — traceability / release readiness
Task(subagent_type="oh-my-claudecode:executor", model="opus", description="qc", prompt="qc booking_repository_impl") — quality gate / test evidence
Task(subagent_type="oh-my-claudecode:executor", model="opus", description="maintain", prompt="maintain booking_repository_impl") — 부채 9행 + 5 그룹 분포
Task(subagent_type="oh-my-claudecode:executor", model="opus", description="refactor", prompt="refactor booking_repository_impl") — Top 5 부채 Before/After
Task(subagent_type="oh-my-claudecode:verifier", model="opus", description="synthesis", prompt="통합 우선순위 정렬 + cross-link 매트릭스") — 7 결과 reviewer
```

**reviewer 통합 결과**:

**Top 10 우선순위** (P1×6, P2×3, P3×1) — full 보다 P1 비중 ↑ (독립 분석으로 누락 이슈 발굴):
1. [P1, Security/Maintain] PII 평문 로깅 — DREAD 9.5 + Maintain Code Smell 양쪽 검출
2. [P1, Architecture/SOLID] data → ui 의존 — Clean Arch + DIP 양쪽 검출
3. [P1, Security] idempotency-key 미적용 — Tampering 8.5
4. [P1, SOLID/DDD] 6 책임 누적 — SRP + Aggregate 경계 양쪽 검출
5. [P1, Maintain/SOLID] 510줄 Large Class — Bloater + SRP 결합
6. [P1, Security] EoP (리소스 소유권 미검증) — DREAD 8.0
7. [P2, Refactor] createBooking 152줄 → 6개 함수 분해
8. [P2, DDD] Slot 직접 update — Aggregate Root 위반
9. [P2, OO Abuser] switch(bookingType) 7곳 — Polymorphism
10. [P3, Dispensable] 미사용 helper × 5 — Dead Code

**도메인 cross-link 매트릭스** (swarm 고유 산출 — full 에서는 누락):

| 이슈 | Security | Architecture | Refactor | Maintain | SOLID |
|------|:--------:|:------------:|:--------:|:--------:|:-----:|
| PII 평문 로깅 | ✅ P1 | - | ✅ P1 | ✅ P1 | - |
| data → ui 의존 | - | ✅ P1 | ✅ P2 | - | ✅ P1 |
| 6 책임 누적 | - | ✅ P1 | ✅ P1 | ✅ P1 | ✅ P1 |
| idempotency 미적용 | ✅ P1 | - | ✅ P2 | - | - |
| Aggregate 경계 | - | ✅ P2 | ✅ P2 | - | ✅ P2 |

cross-link ≥ 3 도메인 검출 = 시스템 영향 광범위 → architect/security-reviewer 합동 검토 권장.

**통합 6 필드** (7 Claude Code 서브에이전트 의견 종합):
- **선택/판정**: full 모드 결론과 동일 (Aggregate 분리 + PII 차단) + **신규 발견**: 6 책임 중 PII/idempotency/ownership 3건이 Security ↔ Maintain ↔ SOLID 교차 → 단일 refactor 로 3 도메인 동시 개선 가능
- **근거**: 독립 7 context 분석 → 단일 context 에서 우선순위가 묻혔던 P2 이슈 (Aggregate 경계, OCP, test evidence gap) 가 cross-link 매트릭스에서 P1 영향도로 재평가
- **대안 비교**: full 모드 vs swarm 모드 — swarm 은 cross-link 매트릭스 + 독립 분석 깊이, full 은 단일 context 일관성
- **표준 인용**: full 모드와 동일 + [GRASP Low Coupling/High Cohesion](principles/grasp.md), [12-Factor #III Config](principles/12-factor.md)
- **적용 조건**: 단일 모듈이 핵심 비즈니스 도메인 AND 변경 빈도 ≥ 월 5회 AND OMC ultrawork 및 Claude Code 서브에이전트 사용 가능
- **비추천 조건**: 단순 CRUD / utility 모듈 → full 또는 단일 모드로 충분, swarm 은 over-engineering

**6단계 hand-off**: cross-link P1 6건 → `security-reviewer` + `architect` 합동 → `executor` (Aggregate 분리 PR 분할) → `verifier` (단계별 회귀).

---

### full vs swarm 비교 표

| 측면 | full | swarm |
|------|------|-------|
| 실행 방식 | 7 기본 모드 순차 (단일 context) | 7 기본 모드 병렬 Claude Code 서브에이전트 + 1 reviewer |
| 토큰 비용 | 7만~14만 | 8만~16만 |
| 시간 | 5분 (순차) | 1.5분 (병렬) |
| 깊이 | 중간 (단일 context 일관성) | 높음 (독립 분석 + cross-link 매트릭스) |
| 누락 위험 | P2 가 묻힐 수 있음 | cross-link 로 재평가 |
| 의존성 | 없음 | OMC `ultrawork` 필요 |
| 적합 | 빠른 종합 점검, 단일 모듈 1차 audit | 핵심 비즈니스 도메인 심층 audit |
| 산출물 차이 | 통합 우선순위 Top 10 | + 도메인 cross-link 매트릭스 |

**선택 가이드**:
- 1차 종합 점검 / 시간 우선 / 토큰 절약 → **full**
- 핵심 도메인 / 변경 빈도 ≥ 월 5회 / 깊이 우선 → **swarm**
- ultrawork 미사용 환경 → **full** (swarm 사용 불가)

상세 산출물 마크다운 스켈레톤은 [`output_templates.md`](output_templates.md) 참조.

---

### I. qa 모드 — 릴리즈 전 품질 보증 점검

```
User: /dev-advisor qa src/checkout
```

**QA 점검 표**:

| QA 항목 | 판정 | 보완 조치 |
|---------|------|----------|
| [requirements-traceability](quality/qa.md#qa-requirements-traceability) | GAP | 결제 실패/환불 요구사항에 테스트 ID 연결 |
| [test-strategy](quality/qa.md#qa-test-strategy) | PASS | 단위/통합/E2E/보안 경계 분리 |
| [release-readiness](quality/qa.md#qa-release-readiness) | CONDITIONAL | P2 known issue 승인 기록 필요 |

**5단계 "왜"**:
- **판정**: CONDITIONAL. 요구사항 추적성 2건 누락, 릴리즈 승인 조건 1건 필요.
- **근거**: critical payment path는 테스트 전략이 있으나 refund edge case가 traceability matrix에서 비어 있음.
- **대안 비교**: 릴리즈 보류 vs 조건부 승인 vs 범위 축소.
- **표준 인용**: [Quality QA](quality/qa.md), [ISO 25010](principles/iso25010.md), [SDLC Models](principles/sdlc-models.md)
- **적용 조건**: 결제/환불처럼 금전 영향이 있는 릴리즈.
- **승인·면제 조건**: P2 known issue는 owner 승인과 rollback plan이 있을 때만 조건부 승인.

---

### J. qc 모드 — 품질 게이트와 테스트 실행 증거 검증

```
User: /dev-advisor qc src/checkout
```

**QC 증거 표**:

| QC 항목 | 증거 | 판정 | 차단 |
|---------|------|------|------|
| [build-verification](quality/qc.md#qc-build-verification) | CI #1842 / artifact checkout-1.8.0 | PASS | NO |
| [test-execution-evidence](quality/qc.md#qc-test-execution-evidence) | junit.xml + coverage 84% | PASS | NO |
| [quality-gate](quality/qc.md#qc-quality-gate) | SAST high 1건 | FAIL | YES |

**5단계 "왜"**:
- **판정**: FAIL. SAST high 1건으로 release blocker.
- **근거**: 빌드와 테스트는 통과했지만 quality gate가 release policy의 필수 차단 조건을 위반.
- **대안 비교**: gate 수정 후 재실행 vs 예외 승인 vs 릴리즈 보류.
- **표준 인용**: [Quality QC](quality/qc.md), [Testing Strategies](patterns/testing-strategies.md), [Process Metrics](principles/process-metrics.md)
- **적용 조건**: merge/release gate와 CI 증거가 있는 배포 후보.
- **차단·재검증 조건**: high severity scanner failure, critical path test failure, 증거 누락.
