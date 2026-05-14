# Fintech / 결제 도메인 패턴 (Fintech & Payment Patterns)

결제·뱅킹·증권·송금 산업의 정평 있는 12 패턴. **돈을 다루는 도메인** 의 비기능 요구(정합성·감사·규제·복구) 가 일반 백엔드와 다른 패턴을 만듦.

**원전·표준 참고**:
- *Designing Financial Systems* (Stripe Engineering, blog series)
- *Streaming Systems* (Akidau/Chernyak/Lax, 2018) — exactly-once payment 의미론
- ISO 20022 (Universal financial industry message scheme)
- ISO 8583 (Card transaction messaging)
- PCI DSS v4.0 (Card data protection)
- EBA RTS on SCA (PSD2 — 유럽 강한 고객 인증)
- FATF Recommendations (AML)
- *Patterns of Enterprise Application Architecture* (Fowler, 2002) — Money pattern, Unit of Work
- KFTC (한국금융결제원) 오픈뱅킹 / 펌뱅킹 표준
- 한국 여신전문금융업법, 전자금융거래법

**핵심 비기능 요구**:
- **정확성 > 가용성** — 1원도 사라지면 안 됨 (CP 시스템). Strong consistency 우선
- **감사 가능 (Auditable)** — 모든 상태 변경에 trail. Append-only ledger
- **멱등성 (Idempotent)** — 네트워크 retry가 중복 결제 = 사고
- **정산 마감 (Cutoff)** — 일/주/월 마감 시점에 외부 시스템과 정합
- **규제 준수 (Compliance)** — PCI DSS / PSD2 / AML / KYC 가 아키텍처 결정에 직접 영향

**관련 카탈로그**:
- [`../distributed.md`](../distributed.md) — Saga (Payment Intent), Idempotency Key, Outbox
- [`../ddd-tactical.md`](../ddd-tactical.md) — Aggregate (Account), Domain Event (Funds Transferred), Value Object (Money)
- [`../../security/security-data-protection.md`](../../security/security-data-protection.md) — Tokenization, FPE (Format-Preserving Encryption)
- [`../../security/compliance.md`](../../security/compliance.md) — PCI DSS v4.0, PSD2, GDPR
- [`../../security/security-detect-respond.md`](../../security/security-detect-respond.md) — Fraud detection, anomaly

---

## 1. Double-Entry Bookkeeping (복식부기) <a id="double-entry-bookkeeping"></a>

**목적**: 모든 화폐 트랜잭션을 최소 두 개의 계정 항목(Debit + Credit) 의 쌍으로 기록하여, 시스템 전체 잔액 합이 항상 0 이 되도록 강제하는 회계 표준 패턴.

**메커니즘**:
- 1494 년 Luca Pacioli 가 *Summa de Arithmetica* 에서 정립한 500 년 회계 표준
- 자산(Asset) ↑ → Debit, 부채(Liability)·자본(Equity)·수익(Revenue) ↑ → Credit (그 반대도 대칭)
- 한 트랜잭션의 Debit 합 = Credit 합 (Σ debit = Σ credit, 부등 시 시스템 오류)
- "어디에서 와서 어디로 갔는가" 를 두 줄로 기록 → 단식부기의 "얼마 변했다" 보다 정보량이 많음
- 잔액(balance) 은 저장 값이 아니라 **모든 ledger entry 의 fold 로 derived** (Event Sourcing 과 동일 원리)

**장점**:
- 자기 검증 (self-verifying) — 합이 0 이 아니면 즉시 버그 탐지
- 모든 자금 흐름의 출처(source) 와 사용처(sink) 가 명시 → 감사 가능
- 한쪽만 기록되는 "lost money" 사고 원천 차단
- 회계사 / 감사인 / 세무 당국이 이해하는 표준 언어

**단점·주의**:
- 단순 CRUD 멘탈 모델로 접근하면 학습 곡선 가파름
- 잔액 조회 시 모든 entry fold → 성능 위해 snapshot / materialized view 필요
- 회계 계정(Account) 분류 체계(Chart of Accounts) 설계 사전 필요
- 잘못 설계한 ledger schema 는 사후 마이그레이션이 매우 비쌈

**컴플라이언스 영향**:
- **K-IFRS / IFRS / GAAP**: 복식부기는 모든 회계기준의 전제
- **전자금융거래법 (한국)**: 거래기록 5 년 보존 의무 → append-only ledger 가 자연 부합
- **SOX (미국 상장사)**: 재무 보고 무결성 — 복식부기가 1차 통제

**Kotlin / SQL 예제**:
```kotlin
// Ledger entry — 단일 트랜잭션이 N(>=2) 개 entry 로 구성
data class LedgerEntry(
    val transactionId: TransactionId,
    val accountId: AccountId,
    val direction: Direction,    // DEBIT or CREDIT
    val amount: Money,
    val occurredAt: Instant,
)

enum class Direction { DEBIT, CREDIT }

// invariant: 한 transaction 의 debit 합 = credit 합
fun postTransaction(entries: List<LedgerEntry>) {
    val byCurrency = entries.groupBy { it.amount.currency }
    byCurrency.forEach { (cur, list) ->
        val debit = list.filter { it.direction == DEBIT }.sumOf { it.amount.amount }
        val credit = list.filter { it.direction == CREDIT }.sumOf { it.amount.amount }
        require(debit == credit) { "unbalanced ledger: $cur debit=$debit credit=$credit" }
    }
    repo.insertAll(entries)
}

// 예: A → B 1000 원 송금
// transaction t1:
//   (account = A, direction = CREDIT, amount = 1000)  -- A 자산 ↓
//   (account = B, direction = DEBIT,  amount = 1000)  -- B 자산 ↑
```

```sql
-- ledger 테이블 schema (append-only)
CREATE TABLE ledger_entry (
    id            BIGSERIAL PRIMARY KEY,
    txn_id        UUID NOT NULL,
    account_id    BIGINT NOT NULL REFERENCES account(id),
    direction     CHAR(1) NOT NULL CHECK (direction IN ('D', 'C')),
    amount_minor  BIGINT NOT NULL CHECK (amount_minor > 0),  -- 최소단위 (분/원)
    currency      CHAR(3) NOT NULL,
    occurred_at   TIMESTAMPTZ NOT NULL,
    posted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (txn_id, account_id, direction)
);
CREATE INDEX ON ledger_entry (account_id, occurred_at);
-- balance 는 view 또는 snapshot 으로 derive
```

**관련 패턴**: [Ledger Pattern](#ledger-pattern), [Reconciliation](#reconciliation), Event Sourcing, Money (PoEAA Value Object)

---

## 2. Ledger Pattern (원장) <a id="ledger-pattern"></a>

**목적**: 모든 금융 거래를 append-only journal 에 immutable 하게 기록하고, 잔액·요약 정보는 ledger 에서 derive 하는 핵심 데이터 패턴.

**메커니즘**:
- **Journal (분개장)**: 트랜잭션 발생 시간 순서대로 기록되는 append-only 시퀀스
- **Ledger (원장)**: 계정(Account) 별로 entry 를 그룹핑한 뷰
- **UPDATE / DELETE 금지** — 정정은 반대 entry 발행(reversing entry) 으로만
- 잔액(balance) = Σ debit − Σ credit (계정 유형에 따라 부호 다름)
- Stripe / Modern Treasury / PayPal / Coinbase 가 모두 동일 패턴

**장점**:
- 시간 어느 시점이든 잔액을 정확히 재계산 가능 (point-in-time consistency)
- 감사 trail 이 데이터 모델 자체에 내장
- 동시성 충돌 영역이 좁음 (insert-only)
- 분석/리포팅이 ledger 위에서 자연스럽게 표현

**단점·주의**:
- 데이터 양 폭증 → snapshot / partitioning 전략 필수
- 잔액 조회가 O(N) → balance materialized view 또는 snapshot table 운영
- 정정(amendment) 표현이 직관적이지 않음 — reversing entry 패턴 학습 필요
- "현재 잔액 hot row" 패턴(`UPDATE balance SET amount = ...`) 으로 절대 회귀하지 말 것

**컴플라이언스 영향**:
- **전자금융거래법**: 거래 기록 보존(5년) — append-only 가 자연 부합
- **PCI DSS Req 10**: 모든 카드 데이터 접근 / 변경 audit log — ledger 와 시너지
- **AML/CFT Travel Rule**: 송금 출처·수취인 추적 — ledger 가 1차 데이터 소스

**Kotlin / SQL 예제**:
```kotlin
class Ledger(private val journal: JournalRepo, private val snapshot: BalanceSnapshotRepo) {
    fun post(txn: List<LedgerEntry>) {
        require(txn.isNotEmpty())
        journal.appendAll(txn)  // append-only
        // snapshot 은 비동기 갱신 (eventual consistency)
    }

    fun balance(account: AccountId, asOf: Instant = Instant.now()): Money {
        val snap = snapshot.latestBefore(account, asOf)
        val entries = journal.findAfter(account, snap?.checkpoint ?: Instant.EPOCH, asOf)
        return entries.fold(snap?.balance ?: Money.zero(KRW)) { acc, e ->
            when (e.direction) {
                DEBIT  -> acc + e.amount   // asset account 기준
                CREDIT -> acc - e.amount
            }
        }
    }

    // 정정: UPDATE 금지, reversing entry 발행
    fun reverse(originalTxnId: TransactionId, reason: String) {
        val original = journal.findByTxn(originalTxnId)
        val reversed = original.map {
            it.copy(
                transactionId = TransactionId.new(),
                direction = it.direction.opposite(),
                metadata = mapOf("reverses" to originalTxnId, "reason" to reason),
            )
        }
        journal.appendAll(reversed)
    }
}
```

```sql
-- balance snapshot (성능 최적화, 주기적 생성)
CREATE TABLE balance_snapshot (
    account_id    BIGINT NOT NULL,
    checkpoint    TIMESTAMPTZ NOT NULL,
    balance_minor BIGINT NOT NULL,
    currency      CHAR(3) NOT NULL,
    PRIMARY KEY (account_id, checkpoint)
);
-- 매일 자정 또는 N entries 마다 생성
```

**관련 패턴**: [Double-Entry Bookkeeping](#double-entry-bookkeeping), Event Sourcing, CQRS (read model 분리), Materialized View

---

## 3. Reconciliation (대사) <a id="reconciliation"></a>

**목적**: 내부 ledger 와 외부(PG / 카드사 / 은행) 정산서를 주기적으로 매칭하여 차이(break)를 발견·해결하는 패턴.

**메커니즘**:
- **3-way reconciliation**: (1) 내부 ledger, (2) 외부 정산 파일(NACHA / KFTC 펌뱅킹 결과 / Stripe Balance Transactions), (3) 은행 잔액 → 세 값이 일치해야 함
- 매칭 키: 거래 ID / 시간창 / 금액 / 통화 / 카드 마지막 4 자리
- **Matched / Unmatched (left) / Unmatched (right)** 세 버킷으로 분류
- Break 는 (a) 시간 차이(internal 먼저, external 늦게 도착) (b) 수수료 처리 누락 (c) 환율 / 라운딩 (d) 실제 사고 — 네 종류
- 자동화 70~95%, 수작업 resolution 5~30% (산업 평균)

**장점**:
- 내부 시스템 버그 / 외부 정산 오류 / 부정 거래 조기 발견
- 회계 결산 자동화 기반
- 일자 결산(daily close) 시 confidence
- 손실 사고 추적 / 책임 소재 명확

**단점·주의**:
- 외부 파일 포맷 다양 (CSV / XML / ISO 8583 / NACHA / EDI) → adapter 필요
- 시간대(timezone) 처리 실수 1 위 — UTC 기준 일관
- 라운딩 차이가 break 처럼 보임 → tolerance 정책 필요 (예: ±1 원 자동 매칭)
- 매칭 알고리즘이 너무 느슨하면 false match, 너무 빡빡하면 break 폭증

**컴플라이언스 영향**:
- **전자금융거래법 시행령**: 일일 정산 의무
- **PCI DSS Req 1.1.5**: 데이터 흐름 문서 — reconciliation 이 핵심 통제
- **AML/CFT**: unmatched 거래는 의심 거래 보고(SAR) 대상 후보

**Kotlin / SQL 예제**:
```kotlin
data class ReconciliationResult(
    val matched: List<MatchedPair>,
    val internalOnly: List<LedgerEntry>,   // 외부에 없음 = 발송 누락 / 미정산
    val externalOnly: List<ExternalRecord>, // 내부에 없음 = 미수 / 사고 / 환불 누락
)

class Reconciler(
    private val ledger: LedgerRepo,
    private val external: ExternalSettlementFile,
    private val tolerance: Money = Money(BigDecimal("1"), KRW),
) {
    fun reconcile(date: LocalDate): ReconciliationResult {
        val internal = ledger.findByDate(date).associateBy { it.externalRef }
        val ext = external.load(date)

        val matched = mutableListOf<MatchedPair>()
        val internalOnly = mutableListOf<LedgerEntry>()
        val externalOnly = mutableListOf<ExternalRecord>()

        ext.forEach { e ->
            val i = internal[e.referenceId]
            when {
                i == null -> externalOnly += e
                (i.amount - e.amount).abs() <= tolerance -> matched += MatchedPair(i, e)
                else -> externalOnly += e.copy(break_ = "amount_mismatch ${i.amount} vs ${e.amount}")
            }
        }
        internalOnly += internal.values.filter { matched.none { m -> m.internal.id == it.id } }

        return ReconciliationResult(matched, internalOnly, externalOnly)
    }
}
```

**관련 패턴**: [Ledger Pattern](#ledger-pattern), [Settlement / Clearing](#settlement-clearing), Outbox, Anti-Corruption Layer (외부 파일 포맷)

---

## 4. Settlement / Clearing <a id="settlement-clearing"></a>

**목적**: 거래 발생(authorization) 시점과 실제 자금 이동(settlement) 시점을 분리하여, 효율적 정산과 위험 관리를 가능하게 하는 패턴.

**메커니즘**:
- **Authorization (승인)**: 카드 결제 시 잔액 확보(hold). 즉시 실제 이체 X
- **Clearing (청산)**: 같은 카드망 내 거래를 모아 net amount 계산 (서로 상쇄)
- **Settlement (정산)**: 실제 자금 이동. 보통 T+1 (다음 영업일) ~ T+2
- 결제 사이클: **Auth → Capture → Clearing → Settlement → Funding**
- **RTGS (Real-Time Gross Settlement)** vs **Net Settlement**:
  - RTGS: 거래마다 즉시 전액 이체 (한국 한은금융망, SWIFT gpi). 큰 금액·은행 간
  - Net: 일정 주기 모아 차액만 (KFTC 펌뱅킹, 카드사 정산). 효율적이지만 신용 위험
- **T+N 의미**:
  - T+0: 당일 정산 (모바일 페이, 토스, RTGS)
  - T+1: 다음 영업일 (대부분 PG, 한국 카드)
  - T+2: 미국 증권 시장 (NYSE / NASDAQ), 국내 주식
  - T+3: 일부 국제 거래

**장점**:
- 거래량 ↑ 시에도 자금 이동 비용 절감 (netting)
- 위험 평가 시간 확보 (fraud check, chargeback window)
- 외환 / 환전 환율 묶기 가능 (FX hedging)

**단점·주의**:
- Counterparty risk — settlement 전까지 상대방 부도 위험
- T+N 동안 자금이 묶임 → 가맹점 cash flow 부담
- Auth 와 Capture 사이 시간 차 동안 한도 변경·취소 처리 복잡
- 환불 시점이 settlement 전후 인지에 따라 처리 흐름 분기

**컴플라이언스 영향**:
- **여신전문금융업법 (한국)**: 카드 가맹점 대금 지급 기한(보통 3 영업일 이내)
- **EU PSD2 SCT Inst**: 10 초 내 정산 의무 (즉시이체)
- **CPMI-IOSCO Principles for Financial Market Infrastructures**: 결제 시스템 위험 관리

**Kotlin 예제**:
```kotlin
sealed class PaymentState {
    object Authorized : PaymentState()       // 승인 (hold)
    object Captured : PaymentState()         // 청구 확정
    object Cleared : PaymentState()          // 청산 (net 계산 완료)
    object Settled : PaymentState()          // 실제 자금 이동 완료
    data class Failed(val reason: String) : PaymentState()
}

class SettlementBatch(
    val cycleDate: LocalDate,
    val transactions: List<CapturedTxn>,
) {
    // Net Settlement 계산
    fun netByMerchant(): Map<MerchantId, Money> = transactions
        .groupBy { it.merchantId }
        .mapValues { (_, txns) ->
            val gross = txns.sumOf { it.amount.amount }
            val fees = txns.sumOf { it.fee.amount }
            val refunds = txns.filter { it.isRefund }.sumOf { it.amount.amount }
            Money(gross - fees - refunds, KRW)
        }

    // T+1 settlement: 다음 영업일 자정 + α 에 자금 이동
    fun scheduledSettlementAt(): Instant {
        val nextBusinessDay = cycleDate.plusBusinessDays(1)
        return nextBusinessDay.atTime(11, 0).toInstant(KST)
    }
}
```

**관련 패턴**: [Ledger Pattern](#ledger-pattern), [Reconciliation](#reconciliation), [Idempotent Payment](#idempotent-payment), State (PaymentState 머신)

---

## 5. Idempotent Payment <a id="idempotent-payment"></a>

**목적**: 네트워크 retry / 클라이언트 더블 클릭 / timeout 재시도로 같은 결제 요청이 여러 번 도착해도 정확히 한 번만 과금되도록 강제하는 패턴.

**메커니즘**:
- 클라이언트가 요청마다 unique `Idempotency-Key` 헤더 전송 (UUIDv4 또는 client-generated nonce)
- 서버 알고리즘:
  1. key 로 기존 응답 조회
  2. **있으면**: cached response 그대로 반환 (단, 요청 본문 hash 일치 확인 — 다르면 422 에러)
  3. **없으면**: 트랜잭션 시작, 결제 처리, 결과를 key 와 함께 저장, 응답 반환
- 저장: (key, request_hash, response, status, created_at)
- **TTL 24 시간** (Stripe 표준) — 결제 도메인 retry 창은 보통 짧음
- 진행 중(in-flight) 상태 동시 요청 처리: distributed lock 또는 INSERT ON CONFLICT
- 클라이언트는 동일 트랜잭션을 retry 할 때 **반드시 같은 키** 재사용

**장점**:
- At-least-once 인프라(네트워크 / 메시지 큐) 위에서 exactly-once 결제 효과
- 카드 이중 결제 사고 원천 차단
- 클라이언트 UX 개선 (안심하고 retry)
- 시스템 retry / circuit breaker / saga 와 결합 안전

**단점·주의**:
- key 저장소 운영 비용 (Redis / DB)
- 요청 본문 hash 검증 누락 시: 같은 키로 다른 금액 결제 가능 (보안 사고)
- TTL 만료 후 같은 키 재사용은 거부해야 함
- 클라이언트가 키 생성을 잘못하면(예: 매 retry 마다 새 키) 효과 없음

**컴플라이언스 영향**:
- **PCI DSS Req 6.5**: 입력 검증 — request hash 비교가 표준
- **전자금융거래법 제7조**: 결제 정확성 의무
- **카드사 매뉴얼**: 중복 결제 분쟁 사유 1 위 → idempotency 가 사실상 필수

**Kotlin 예제**:
```kotlin
data class IdempotencyRecord(
    val key: String,
    val requestHash: String,
    val response: String,
    val statusCode: Int,
    val createdAt: Instant,
)

class IdempotentPaymentApi(
    private val store: IdempotencyStore,
    private val pg: PaymentGateway,
    private val ttl: Duration = Duration.ofHours(24),
) {
    fun charge(key: String, req: ChargeRequest): ChargeResponse {
        val requestHash = sha256(req.toJson())

        // 1. 기존 응답 조회
        store.get(key)?.let { existing ->
            require(existing.requestHash == requestHash) {
                throw IdempotencyConflictException(
                    "Idempotency-Key $key reused with different body"
                )
            }
            return Json.decodeFromString(existing.response)
        }

        // 2. 분산 락 — 동시 in-flight 요청 차단
        store.withLock(key, timeout = Duration.ofSeconds(30)) {
            // 락 획득 후 재확인 (double-checked)
            store.get(key)?.let { return@withLock Json.decodeFromString(it.response) }

            // 3. 실제 결제 처리
            val response = pg.charge(req)

            // 4. 응답 저장
            store.put(
                IdempotencyRecord(
                    key = key,
                    requestHash = requestHash,
                    response = Json.encodeToString(response),
                    statusCode = 200,
                    createdAt = Instant.now(),
                ),
                ttl = ttl,
            )
            return@withLock response
        }
    }
}
```

```sql
CREATE TABLE idempotency_key (
    key            VARCHAR(255) PRIMARY KEY,
    request_hash   CHAR(64) NOT NULL,
    response       JSONB NOT NULL,
    status_code    INTEGER NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at     TIMESTAMPTZ NOT NULL
);
CREATE INDEX ON idempotency_key (expires_at);  -- TTL cleanup
```

**관련 패턴**: [Payment Intent / Saga](#payment-intent-saga), [Reconciliation](#reconciliation), Idempotency Key (distributed.md §6), Retry, Distributed Lock

---

## 6. 3-D Secure (3DS) Authentication <a id="3ds-authentication"></a>

**목적**: 카드 발급사(Issuer) 가 결제 인증에 직접 참여하여 카드 정보 도용에 의한 부정 결제를 차단하고, 책임을 가맹점에서 발급사로 이전(liability shift) 하는 패턴.

**메커니즘**:
- 3 도메인: **Acquirer(매입사) / Issuer(발급사) / Interoperability(카드망: Visa·MC)**
- 흐름 (3DS 2.x):
  1. 가맹점 → 3DS Server 에 인증 요청 (PAN, 거래정보, device fingerprint)
  2. **Frictionless flow**: 카드사가 위험 점수 낮다고 판단 → 사용자 개입 없이 인증 완료 (95%)
  3. **Challenge flow**: 위험 점수 높음 → 사용자에게 OTP / 푸시 / 생체인증 요구 (5%)
  4. 결과를 CAVV / ECI 코드로 PG → Acquirer 전달, 카드망이 검증
- **SCA (Strong Customer Authentication, PSD2 RTS)**: 유럽은 €30 초과 거래에 3DS 2.x 의무 — 지식(PIN) + 소유(폰) + 존재(생체) 중 2 요소
- **Liability Shift**: 3DS 인증 거친 거래의 fraud chargeback 책임은 issuer 가 부담 (가맹점 보호)
- 3DS 1.0 (2001~2022, deprecated) → 3DS 2.x (EMVCo, 2017~) — UX 대폭 개선

**장점**:
- 카드 도용 부정 결제 70~90% 차감 (산업 데이터)
- Chargeback liability shift → 가맹점 손실 최소화
- PSD2 SCA 자동 충족 (유럽 의무)
- frictionless 흐름은 conversion 영향 미미

**단점·주의**:
- Challenge flow 시 conversion drop 5~15%
- 발급사 인증 시스템 가용성에 의존 (단일 장애점)
- 가맹점 코드 / device fingerprint / 거래 패턴이 카드사 risk engine 입력 → 데이터 품질 중요
- 일본·미국은 SCA 의무 없음 → 지역별 정책 분기 필요

**컴플라이언스 영향**:
- **PSD2 RTS on SCA (EU)**: €30 초과 거래 의무
- **EMV 3DS 2.2.0**: 모든 글로벌 카드망 표준
- **PCI DSS Req 6**: 결제 페이지 보안 — 3DS 통합 시 iframe 격리 권장

**Kotlin 예제**:
```kotlin
data class ThreeDsRequest(
    val pan: String,           // 카드번호 (tokenized 권장)
    val amount: Money,
    val deviceFingerprint: String,
    val browserInfo: BrowserInfo,
    val returnUrl: String,
)

sealed class ThreeDsResult {
    data class Frictionless(val cavv: String, val eci: String) : ThreeDsResult()
    data class Challenge(val challengeUrl: String, val transactionId: String) : ThreeDsResult()
    data class Rejected(val reason: String) : ThreeDsResult()
}

class ThreeDsAuthenticator(private val server: ThreeDsServer) {
    suspend fun authenticate(req: ThreeDsRequest): ThreeDsResult {
        val authResp = server.preAuth(req)
        return when (authResp.transStatus) {
            "Y" -> ThreeDsResult.Frictionless(authResp.cavv, authResp.eci)     // 인증 성공
            "C" -> ThreeDsResult.Challenge(authResp.acsUrl, authResp.transactionId) // 챌린지 필요
            "N" -> ThreeDsResult.Rejected("issuer denied")                     // 거부
            "U" -> ThreeDsResult.Rejected("technical_failure")                 // 시스템 장애
            else -> ThreeDsResult.Rejected("unknown_status: ${authResp.transStatus}")
        }
    }
}

// Liability shift 적용 조건 (Visa / MC 공통)
fun isLiabilityShifted(eci: String, scheme: CardScheme): Boolean = when (scheme) {
    CardScheme.VISA -> eci in setOf("05", "06")  // 05 = full auth, 06 = attempted
    CardScheme.MASTERCARD -> eci in setOf("02", "01")
    else -> false
}
```

**관련 패턴**: [Card Network 통합](#card-pci-scope-reduction), [Payment Intent / Saga](#payment-intent-saga), Authentication (security-authn.md), Strategy

---

## 7. Payment Intent / Saga <a id="payment-intent-saga"></a>

**목적**: 결제를 단일 함수 호출이 아닌 **다단계 상태 머신** 으로 모델링하여, 3DS 챌린지·SCA·webhook 비동기 흐름을 자연스럽게 표현하는 패턴.

**메커니즘**:
- Stripe 가 2019 년 PaymentIntent API 로 대중화. PSD2 SCA 대응이 직접 동기
- 상태 전이:
  ```
  created → requires_payment_method → requires_confirmation
        → requires_action (3DS)     → processing
        → succeeded | failed | canceled
  ```
- 각 상태 전이는 별도 API 호출 또는 webhook 으로 비동기 트리거
- Saga 보상 트랜잭션:
  - `processing` 에서 실패 → automatic refund or void
  - `succeeded` 후 timeout 환불 → reverse ledger entry
- 클라이언트(앱) 는 PaymentIntent ID 로 상태 polling 또는 webhook 수신
- 멱등성([§5](#idempotent-payment)) 과 결합 필수 — 같은 PaymentIntent 에 confirm 중복 호출 안전해야 함

**장점**:
- 3DS / SCA / Bank redirect 등 사용자 개입 흐름이 model 에 명시
- 부분 실패 시 정확한 보상 trigger 지점 제공
- 클라이언트 SDK 와 서버 webhook 흐름이 같은 추상화 공유
- 분쟁 / 환불 / 부분 환불 등 후속 작업 분기점 명확

**단점·주의**:
- 단순 결제(POS · 카드 한 번 긁기) 에는 과한 추상화
- 상태가 7~10 개로 늘어남 → 잘못된 전이(invalid transition) 차단 로직 필요
- Webhook delivery 보장이 적은 환경에서는 polling fallback 필요
- 분산 락 / outbox 패턴과 결합 안 하면 race condition

**컴플라이언스 영향**:
- **PSD2 SCA**: requires_action 상태가 SCA 분기점
- **PCI DSS Req 4.1**: 상태 전이 데이터는 모두 TLS 1.2+ 전송
- **GDPR Art 25**: 결제 의도(intent) 가 personal data 포함 → 최소 보유 원칙

**Kotlin 예제**:
```kotlin
enum class PaymentIntentStatus {
    REQUIRES_PAYMENT_METHOD, REQUIRES_CONFIRMATION, REQUIRES_ACTION,
    PROCESSING, SUCCEEDED, FAILED, CANCELED
}

data class PaymentIntent(
    val id: PaymentIntentId,
    val amount: Money,
    val status: PaymentIntentStatus,
    val clientSecret: String,           // 클라이언트가 confirm 할 때 사용
    val paymentMethod: PaymentMethod?,
    val nextAction: NextAction? = null,  // 3DS URL 등
    val lastError: String? = null,
)

class PaymentIntentSaga(
    private val repo: PaymentIntentRepo,
    private val pg: PaymentGateway,
    private val threeDs: ThreeDsAuthenticator,
    private val ledger: Ledger,
) {
    suspend fun create(amount: Money): PaymentIntent {
        val intent = PaymentIntent(
            id = PaymentIntentId.new(),
            amount = amount,
            status = REQUIRES_PAYMENT_METHOD,
            clientSecret = generateClientSecret(),
            paymentMethod = null,
        )
        repo.save(intent)
        return intent
    }

    suspend fun confirm(id: PaymentIntentId, pm: PaymentMethod): PaymentIntent {
        val intent = repo.findById(id) ?: error("not found")
        require(intent.status == REQUIRES_PAYMENT_METHOD || intent.status == REQUIRES_CONFIRMATION)

        // 3DS 분기
        val tds = threeDs.authenticate(ThreeDsRequest(pm.pan, intent.amount, ...))
        return when (tds) {
            is ThreeDsResult.Frictionless -> processCharge(intent, pm, tds.cavv)
            is ThreeDsResult.Challenge -> {
                val updated = intent.copy(
                    status = REQUIRES_ACTION,
                    nextAction = NextAction.RedirectToUrl(tds.challengeUrl),
                )
                repo.save(updated); updated
            }
            is ThreeDsResult.Rejected -> failIntent(intent, tds.reason)
        }
    }

    // 보상: charge 실패 시 ledger reverse
    private suspend fun processCharge(intent: PaymentIntent, pm: PaymentMethod, cavv: String): PaymentIntent {
        repo.save(intent.copy(status = PROCESSING))
        return runCatching { pg.charge(intent, pm, cavv) }
            .fold(
                onSuccess = { result ->
                    ledger.post(buildEntries(intent, result))  // double-entry post
                    repo.save(intent.copy(status = SUCCEEDED)).also { /* publish event */ }
                },
                onFailure = { e -> failIntent(intent, e.message ?: "unknown") },
            )
    }
}
```

**관련 패턴**: [Idempotent Payment](#idempotent-payment), [3-D Secure](#3ds-authentication), [Ledger Pattern](#ledger-pattern), Saga (distributed.md §3-4), State Machine

---

## 8. Multi-Currency / FX Handling <a id="multi-currency-fx"></a>

**목적**: 여러 통화의 거래를 정확히 처리하고, 환율 변환·라운딩·spread 를 표준화된 방식으로 다루는 패턴.

**메커니즘**:
- **Money Value Object** (Fowler PoEAA): `(amount: BigDecimal, currency: Currency)` — 절대 `double` 사용 금지
- **최소 단위(minor unit)** 저장: 원(KRW) 1 원 단위, USD 0.01 cent 단위 → 정수(`Long`) 로 저장. ISO 4217 minor unit digits 기준
- **Banker's Rounding (HALF_EVEN)**: 0.5 를 가장 가까운 짝수로 → 통계적으로 편향 없음. 금융권 표준
- **Bid / Ask Spread**: 매도호가(bid) < 매수호가(ask). 환전 시 고객에게는 ask 적용 (가맹점 마진)
- **변환 시점**: settlement-time vs transaction-time 환율 — 둘 다 ledger 에 보존
- **DCC (Dynamic Currency Conversion)**: 해외 카드 결제 시 가맹점이 환율 제시 → 사용자 선택. **MasterCard / Visa 환율보다 보통 불리** (사용자 보호 차원에서 의무 고지)
- **Negative Balance**: 환율 변동으로 환불 시 원금보다 많이 줄 수 있음 → 정책 정의 필수

**장점**:
- 글로벌 결제 / 송금 / 환전 / 암호화폐 거래에 필수
- 라운딩 오차 누적 사고 방지
- 회계 / 세무 / 감사 추적 가능

**단점·주의**:
- `BigDecimal` 사용 시 `equals()` vs `compareTo() == 0` 차이 함정 (`1.0 != 1.00` for equals)
- 통화 변환 후 검증: `convertedAmount.currency == targetCurrency` 항상 확인
- 환율 캐시 TTL 짧게 (분 단위) — 변동성
- 통화별 minor unit digits 다름: USD 2, KRW 0, JPY 0, BHD 3 — 하드코딩 금지, ISO 4217 라이브러리 사용

**컴플라이언스 영향**:
- **MiFID II (EU)**: FX 거래 best execution 의무
- **CFPB Remittance Rule (미국)**: 송금 환율 사전 공시
- **여신금융업 감독규정**: DCC 거래 환율 명시

**Kotlin 예제**:
```kotlin
data class Money(val amountMinor: Long, val currency: Currency) {
    init {
        require(amountMinor >= 0) { "Money amount must be >= 0" }
    }

    // 통화별 minor unit digits (ISO 4217)
    val major: BigDecimal
        get() = BigDecimal(amountMinor).movePointLeft(currency.defaultFractionDigits)

    operator fun plus(other: Money): Money {
        require(currency == other.currency) { "currency mismatch: $currency vs ${other.currency}" }
        return Money(amountMinor + other.amountMinor, currency)
    }

    fun convert(targetRate: ExchangeRate): Money {
        require(targetRate.from == currency) { "rate mismatch" }
        val fromDigits = currency.defaultFractionDigits
        val toDigits = targetRate.to.defaultFractionDigits

        // major 단위로 변환 → banker's rounding → target minor
        val sourceMajor = major
        val targetMajor = sourceMajor.multiply(targetRate.rate)
            .setScale(toDigits, RoundingMode.HALF_EVEN)
        val targetMinor = targetMajor.movePointRight(toDigits).toLong()
        return Money(targetMinor, targetRate.to)
    }
}

data class ExchangeRate(
    val from: Currency,
    val to: Currency,
    val rate: BigDecimal,        // ask price (고객 매수 환율)
    val bidRate: BigDecimal,     // bid price (참고 — spread 표현용)
    val quotedAt: Instant,
    val source: String,          // "ECB" / "KEB" / "internal"
)

// FX gain/loss 회계 처리
fun calculateFxGainLoss(
    originalCharge: Money,
    settlementRate: ExchangeRate,
    transactionRate: ExchangeRate,
): Money {
    // transaction-time 변환액
    val expectedSettlement = originalCharge.convert(transactionRate)
    // settlement-time 실제 입금액
    val actualSettlement = originalCharge.convert(settlementRate)
    return Money(
        actualSettlement.amountMinor - expectedSettlement.amountMinor,
        actualSettlement.currency,
    )
}
```

**관련 패턴**: [Double-Entry Bookkeeping](#double-entry-bookkeeping), [Settlement / Clearing](#settlement-clearing), Value Object (ddd-tactical.md §2), Money pattern (PoEAA)

---

## 9. Refund / Chargeback / Dispute <a id="refund-chargeback"></a>

**목적**: 정상 환불(가맹점 자발) 과 분쟁성 환불(카드사 강제) 의 흐름을 구분하여 처리하고, 증빙 / 보상 / 패널티를 관리하는 패턴.

**메커니즘**:
- **Refund (환불, voluntary)**:
  - 가맹점이 자발적으로 결제 취소
  - **Same-method refund**: 원 결제수단으로 환원 (카드 → 카드, 통장 → 통장) — 자금세탁 방지 의무
  - **Partial refund**: 부분 환불 — 원 거래 ID 참조 + 환불 금액 별도 ledger entry
  - **Refund window**: 카드사별 180일 (Visa/MC) ~ 540일 (Amex)
- **Chargeback (지급정지, involuntary)**:
  - 카드 소지자가 issuer 에 분쟁 신청 → issuer 가 acquirer 에게 자금 회수 요구
  - 가맹점에는 **Reason Code** (Visa 10.4, MC 4837 등) 와 함께 통보
  - 분쟁 사유: 사기(fraud) / 미배송 / 품질불량 / 이중결제 / 미인증
- **Dispute lifecycle**:
  ```
  Retrieval Request → First Chargeback → Representment → Pre-Arbitration → Arbitration
  ```
  - 각 단계마다 evidence 제출 데드라인 (보통 7~45일)
- **Win rate**: 산업 평균 25~40% (분쟁 사유·증빙·국가별 차이 큼)
- **Chargeback Ratio**: 거래 건수 대비 chargeback 비율 > 1% 시 카드사 패널티 / 가맹점 박탈 위험

**장점**:
- 소비자 보호 매커니즘 — 카드 결제 신뢰 기반
- 가맹점도 representment 로 부당한 chargeback 방어 가능
- 사기·서비스 실패 데이터로 product 개선 사이클

**단점·주의**:
- Chargeback fee (건당 $15~50) — win 해도 fee 는 반환 안 됨
- Reason code 별 증빙 요구가 달라 자동화 어려움
- Refund 와 Chargeback 이 동시 발생 시 이중 환불 사고 위험 → 락 / 멱등성 필수
- Friendly fraud (소비자가 받고 부인) — 산업 분쟁 1/3

**컴플라이언스 영향**:
- **Visa Dispute Monitoring Program (VDMP)**: Ratio 0.9% / 100 건 초과 시 경고, 1.8% 초과 시 패널티
- **Reg E (미국 Electronic Fund Transfer Act)**: 분쟁 응답 의무 시간
- **여신전문금융업법 시행규정 (한국)**: 카드 분쟁 처리 절차

**Kotlin 예제**:
```kotlin
sealed class RefundReason {
    object CustomerRequest : RefundReason()
    object Duplicate : RefundReason()
    object FraudPrevention : RefundReason()
}

class RefundService(
    private val ledger: Ledger,
    private val pg: PaymentGateway,
    private val lockManager: DistributedLockManager,
) {
    suspend fun refund(
        originalChargeId: ChargeId,
        amount: Money,
        reason: RefundReason,
        idempotencyKey: String,
    ): Refund {
        // 1. 원 거래 락 — chargeback / 다른 refund 동시 실행 방지
        return lockManager.withLock("charge:$originalChargeId", Duration.ofSeconds(30)) {
            val original = ledger.findCharge(originalChargeId)
                ?: error("charge not found")
            require(!original.isRefunded(amount)) { "already refunded" }
            require(amount <= original.refundableAmount()) { "refund exceeds remaining" }

            // 2. PG 환불 호출 (idempotent)
            val pgResult = pg.refund(
                chargeId = original.pgChargeId,
                amount = amount,
                idempotencyKey = idempotencyKey,
            )

            // 3. Ledger reverse entry — same-method refund 원칙
            ledger.post(listOf(
                LedgerEntry(
                    transactionId = TransactionId.new(),
                    accountId = original.merchantAccountId,
                    direction = CREDIT,            // 가맹점 자산 ↓
                    amount = amount,
                    metadata = mapOf("type" to "refund", "original" to originalChargeId),
                ),
                LedgerEntry(
                    transactionId = TransactionId.new(),
                    accountId = original.customerAccountId,
                    direction = DEBIT,             // 고객 환원 ↑
                    amount = amount,
                ),
            ))

            Refund(pgResult.refundId, originalChargeId, amount, reason)
        }
    }
}

// Chargeback 처리는 별도 흐름 — 카드사 webhook 수신
data class ChargebackEvent(
    val originalChargeId: ChargeId,
    val reasonCode: String,        // "10.4" (Visa fraud) 등
    val amount: Money,
    val respondByDeadline: Instant,
)

class ChargebackHandler(
    private val ledger: Ledger,
    private val evidenceCollector: EvidenceCollector,
) {
    fun onChargebackReceived(event: ChargebackEvent) {
        // 자금 회수 entry (가맹점 손실)
        ledger.post(buildChargebackEntries(event))
        // 증빙 수집 + 알림
        evidenceCollector.scheduleCollection(event)
    }
}
```

**관련 패턴**: [Idempotent Payment](#idempotent-payment), [Ledger Pattern](#ledger-pattern), [Reconciliation](#reconciliation), Distributed Lock, Outbox

---

## 10. Anti-Money Laundering (AML) / KYC <a id="aml-kyc"></a>

**목적**: 자금세탁·테러자금조달·제재 회피 거래를 탐지·차단·보고하기 위해 신원 검증(KYC)·제재 명단 스크리닝·거래 모니터링·의심거래 보고(SAR) 를 결합한 통제 패턴.

**메커니즘**:
- **KYC (Know Your Customer)**:
  - 계정 개설 시 신원 확인 — 신분증 + 주소 + 실명 인증
  - **CIP (Customer Identification Program)**: 미국 USA PATRIOT Act 의무
  - **eKYC**: 비대면 — 신분증 OCR + 셀카 + 라이브니스 검증
- **Sanctions Screening (제재 명단 스크리닝)**:
  - **OFAC SDN List** (미국 재무부), **UN Consolidated List**, **EU Sanctions**
  - 거래 상대방 이름·주소·국가가 명단과 fuzzy match (이름 표기 variant 처리)
  - **PEP (Politically Exposed Persons)**: 정치인·가족·측근 — 강화실사(EDD)
- **Transaction Monitoring**:
  - 룰 기반 (예: 단일 거래 > $10,000, 24시간 누적 > $5,000, 다수 소액 거래 = structuring)
  - ML 기반 — 행동 이상치(anomaly) 탐지
  - **CTR (Currency Transaction Report)**: 미국 $10,000 초과 의무 보고
- **SAR (Suspicious Activity Report)**: 의심 정황 발견 시 FIU(금융정보분석원) 보고 — 30 일 이내
- **Travel Rule (FATF Recommendation 16)**: $1,000 초과 송금에 발신·수신인 정보 동행 — 가상자산 포함

**장점**:
- 규제 위반 fine 회피 (10년간 글로벌 AML fine $40B+)
- 사기 / 부정 거래 탐지 효과 (cross-benefit)
- 금융 시스템 신뢰 유지

**단점·주의**:
- False positive 95~99% (산업 평균) — 알람 fatigue / 운영 비용 폭증
- 정상 사용자 friction (재인증 / 거래 보류)
- 데이터 수집 → GDPR / 개인정보보호법 충돌 — 최소 수집·목적 한정 원칙
- 제재 명단은 자주 갱신 (UN 주 1회, OFAC 수시) — 실시간 동기화 필요
- 의심거래 보고는 고객에게 사전 통지 금지 (tipping-off offence)

**컴플라이언스 영향**:
- **특정금융거래정보의보고 및 이용 등에 관한 법률 (한국)**: KYC + STR + CTR
- **BSA (Bank Secrecy Act, 미국)**: 1970~ 의 토대 법
- **6AMLD (EU)**: 2021~ 강화된 6차 AML 지침
- **FATF Recommendations 40 (2012~)**: 글로벌 표준

**Kotlin 예제**:
```kotlin
data class CustomerProfile(
    val id: CustomerId,
    val name: String,
    val dateOfBirth: LocalDate,
    val nationality: String,
    val address: Address,
    val riskScore: Int,           // 0~100
    val kycStatus: KycStatus,
    val isPep: Boolean,
)

enum class KycStatus { NOT_VERIFIED, BASIC, ENHANCED, REJECTED }

class AmlScreener(
    private val sanctionsList: SanctionsListRepo,
    private val pepList: PepListRepo,
    private val txnMonitor: TransactionMonitor,
) {
    fun screenCustomer(profile: CustomerProfile): ScreeningResult {
        val matches = mutableListOf<SanctionMatch>()

        // 1. Sanctions list (OFAC / UN / EU) — fuzzy name match
        sanctionsList.search(profile.name, threshold = 0.85).forEach {
            matches += SanctionMatch(it.listName, it.entryName, it.matchScore)
        }
        // 2. PEP screening
        if (pepList.contains(profile.name, profile.dateOfBirth)) {
            matches += SanctionMatch("PEP", profile.name, 1.0)
        }

        return when {
            matches.any { it.listName in setOf("OFAC", "UN") } ->
                ScreeningResult.Blocked(matches)
            matches.isNotEmpty() ->
                ScreeningResult.EnhancedDueDiligenceRequired(matches)
            else ->
                ScreeningResult.Clear
        }
    }

    fun monitorTransaction(txn: Transaction): MonitoringResult {
        val rules = listOf(
            // Rule 1: 단일 거래 임계치
            { if (txn.amount.major >= BigDecimal("10000")) "high_value_transaction" else null },
            // Rule 2: 24시간 구조화 (structuring)
            {
                val recent = txnMonitor.findRecent(txn.customerId, Duration.ofHours(24))
                if (recent.size >= 5 && recent.all { it.amount.major in BigDecimal("9000")..BigDecimal("9999") })
                    "potential_structuring" else null
            },
            // Rule 3: 고위험 국가
            { if (txn.counterpartyCountry in HIGH_RISK_COUNTRIES) "high_risk_country" else null },
        )

        val triggers = rules.mapNotNull { it() }
        return if (triggers.isNotEmpty()) {
            MonitoringResult.SarRequired(triggers)
        } else {
            MonitoringResult.Clear
        }
    }
}

// SAR 보고 — FIU 제출 (한국: KoFIU)
data class SuspiciousActivityReport(
    val customerId: CustomerId,
    val transactions: List<TransactionId>,
    val triggers: List<String>,
    val narrative: String,
    val reportedAt: Instant,
)
```

**관련 패턴**: [Ledger Pattern](#ledger-pattern) (감사 trail), Anti-Corruption Layer (제재 list 외부 통합), Specification (룰 조합), Authentication / KYC (security-authn.md)

---

## 11. Card Network 통합 (PCI DSS Scope 축소) <a id="card-pci-scope-reduction"></a>

**목적**: 카드 데이터(PAN, CVV, expiration) 가 우리 시스템에 닿지 않도록 격리하여, PCI DSS 적용 범위를 최소화하고 사고 위험·감사 비용을 줄이는 패턴.

**메커니즘**:
- **PCI DSS Scope = 카드 데이터를 저장·처리·전송하는 모든 시스템**. 범위가 클수록 감사 비용·breach 위험 ↑
- **Scope 축소 기법**:
  - **Hosted Payment Page**: PG 가 호스팅하는 결제 페이지로 redirect (Stripe Checkout, PayPal) — PCI SAQ A 적용
  - **Hosted Fields / Iframe**: 결제 폼 필드만 PG iframe 으로 임베드 (Stripe Elements, Braintree Hosted Fields) — PCI SAQ A-EP
  - **Network Tokenization**: PAN 대신 카드망(Visa·MC) 발급 token 사용. token 은 가맹점·디바이스·거래 유형에 묶여 유출돼도 재사용 불가
  - **PG-side Vault**: 카드 정보 저장은 PG 가 담당. 우리는 customer ID + payment method ID 만 보관
- **PCI DSS SAQ 등급**:
  - SAQ A: e-commerce, 모든 카드 데이터 처리 외부 위탁 — 22 문항
  - SAQ A-EP: iframe / direct post, partially outsource — 191 문항
  - SAQ D: 카드 데이터 직접 저장 / 처리 — 354 문항 + QSA 감사
- **EMVCo Payment Tokenization Specification (2014~)**: Apple Pay / Google Pay / 삼성페이의 기반

**장점**:
- 감사 비용 90%+ 절감 (SAQ D → SAQ A)
- 카드 데이터 breach 시 책임 / 손해 ↓
- 보안 사고 발생 가능 표면적(attack surface) 최소화
- 개발 속도 ↑ (보안 inspection 우회)

**단점·주의**:
- PG vendor lock-in — 마이그레이션 시 카드 vault export 협상 필요 (Network Tokenization 은 이식 가능)
- Hosted Page 는 UX 통제 제한 — 디자인 일관성 / 전환율 trade-off
- 카드 데이터 흐름이 우리를 안 거치므로 분석 / 사기 탐지 신호 부족 → PG 가 제공하는 risk signal API 활용
- iframe 통합 시에도 CSP / sub-resource integrity 등 frontend 보안 책임 잔존

**컴플라이언스 영향**:
- **PCI DSS v4.0 (2024 부터 의무)**: SAQ 자가진단 + ASV 스캔 + AOC 제출
- **PCI 3DS Core Security Standard**: 3DS 통합 시 추가
- **GDPR**: 카드 토큰은 pseudonymous data — 여전히 보호 대상이지만 직접 PAN 보다 약화

**Kotlin 예제**:
```kotlin
// ✅ 좋은 패턴: 우리는 PAN 을 절대 보지 않음
data class PaymentMethod(
    val id: PaymentMethodId,            // PG 가 발급한 ID (PCI scope 밖)
    val customerId: CustomerId,
    val type: PaymentMethodType,
    val card: CardSummary?,             // last4, brand, exp_month — non-PCI
)

data class CardSummary(
    val last4: String,                  // 안전 — 4자리는 PAN 아님
    val brand: CardBrand,
    val expMonth: Int,
    val expYear: Int,
    // PAN, CVV 절대 저장 금지
)

class CheckoutService(private val pg: PaymentGateway) {
    // 클라이언트 → PG SDK 가 직접 카드 정보 토큰화 → 우리는 token 만 수신
    suspend fun createPaymentMethod(
        customerId: CustomerId,
        pgToken: String,                // PG SDK 가 발급한 일회용 token
    ): PaymentMethod {
        val pmFromPg = pg.attachPaymentMethod(customerId.value, pgToken)
        return PaymentMethod(
            id = PaymentMethodId(pmFromPg.id),
            customerId = customerId,
            type = PaymentMethodType.CARD,
            card = CardSummary(
                last4 = pmFromPg.card.last4,
                brand = CardBrand.valueOf(pmFromPg.card.brand.uppercase()),
                expMonth = pmFromPg.card.expMonth,
                expYear = pmFromPg.card.expYear,
            ),
        )
    }
}

// ❌ 나쁜 패턴: PCI scope 폭발
class BadCheckoutService {
    // 절대 하지 말 것!
    fun chargeRawCard(
        pan: String,             // PCI 위반 — PAN 직접 수신
        cvv: String,             // PCI DSS Req 3.2: CVV 저장 절대 금지
        expMonth: Int,
        expYear: Int,
    ) = TODO("이 시그니처가 존재하면 SAQ D 적용 + 분기 QSA 감사 필요")
}
```

**프론트엔드 통합 (Stripe Elements 예)**:
```html
<!-- 카드 입력은 Stripe iframe 내부 — 우리 DOM 에서 PAN 접근 불가 -->
<form id="payment-form">
  <div id="card-element"></div>  <!-- Stripe iframe 마운트 지점 -->
  <button type="submit">결제</button>
</form>
<script>
  const stripe = Stripe('pk_live_...');
  const card = stripe.elements().create('card');
  card.mount('#card-element');
  // 우리 서버는 stripe.createToken() 의 결과 token 만 받음
</script>
```

**관련 패턴**: [3-D Secure](#3ds-authentication), [Payment Intent / Saga](#payment-intent-saga), Tokenization (security-data-protection.md), Anti-Corruption Layer

---

## 12. Subscription / Recurring Billing <a id="subscription-billing"></a>

**목적**: 정기 결제(구독·SaaS·멤버십) 의 갱신·실패·이연·해지·환불·요금제 변경을 정합성 있게 처리하는 패턴.

**메커니즘**:
- **구독 모델 요소**:
  - Plan (요금제) — 가격, 주기(monthly/yearly), trial 기간
  - Subscription (구독) — Customer + Plan + 시작일 + 다음 청구일
  - Invoice (청구서) — 청구 사이클별 1 건, line items 포함
  - Payment Attempt — 1 invoice 에 N 회 시도
- **Retry Waterfall (Dunning)**:
  - 실패 사유별 retry 정책 (insufficient_funds → 3일 후, expired_card → 알림 + 카드 갱신, do_not_honor → 1회만)
  - Stripe Smart Retries: ML 기반 retry 시점 최적화 (요일·시간대)
  - 통상 3~4회 시도 후 dunning email → 미해결 시 cancel
- **Proration (일할 계산)**: 사이클 중간 plan 변경 시 사용 일수 비례 청구
- **MRR / ARR**:
  - MRR (Monthly Recurring Revenue) = Σ(active subscription monthly price)
  - ARR (Annual Recurring Revenue) = MRR × 12
  - **Normalize**: 연간 plan → ÷ 12 로 monthly 환산
- **Churn**: voluntary (사용자 해지) vs involuntary (결제 실패로 강제 해지)
- **Network Tokenization** 결합: 카드 만료·재발급 시 token 자동 갱신 (Visa Token Service, MC MDES)

**장점**:
- 예측 가능한 매출 (revenue forecasting)
- 사용자 라이프타임 가치(LTV) 최적화 기반
- Smart retry 로 involuntary churn 30%+ 감소 (Stripe 데이터)

**단점·주의**:
- 환불·proration·plan 변경·trial 등 edge case 폭발 → 상태 머신 복잡
- 카드 만료가 의외로 큰 churn 원인 (월 0.5~1.5%) — account updater 서비스 활용
- 세금(VAT·GST·소비세) 처리는 국가별·plan 별 규정 필요 — 통합 어려움
- Failed payment 처리에 deliverability 좋은 이메일 / 푸시 인프라 필수

**컴플라이언스 영향**:
- **PSD2 SCA — Initial Mandate**: 첫 결제 SCA 인증, 이후 MIT (Merchant Initiated Transaction) 으로 면제
- **EU VAT MOSS / OSS**: B2C 디지털 구독 부가세 처리
- **소비자 보호법**: 자동 갱신 사전 고지 의무 (한국 / EU / CA SB-313)

**Kotlin 예제**:
```kotlin
data class Subscription(
    val id: SubscriptionId,
    val customerId: CustomerId,
    val planId: PlanId,
    val status: SubscriptionStatus,
    val currentPeriodStart: Instant,
    val currentPeriodEnd: Instant,
    val cancelAtPeriodEnd: Boolean = false,
)

enum class SubscriptionStatus {
    TRIALING, ACTIVE, PAST_DUE, CANCELED, UNPAID
}

class SubscriptionBilling(
    private val subscriptions: SubscriptionRepo,
    private val invoices: InvoiceRepo,
    private val payments: PaymentApi,
    private val ledger: Ledger,
) {
    // 사이클마다 호출 (cron / scheduler)
    suspend fun processCycle(now: Instant = Instant.now()) {
        val due = subscriptions.findDueForBilling(now)
        due.forEach { sub ->
            runCatching { processSingle(sub) }
                .onFailure { /* alert + retry queue */ }
        }
    }

    private suspend fun processSingle(sub: Subscription) {
        // 1. invoice 생성 (idempotent — 같은 period 에 중복 invoice 금지)
        val invoice = invoices.createIfAbsent(
            subscriptionId = sub.id,
            periodStart = sub.currentPeriodStart,
            periodEnd = sub.currentPeriodEnd,
        )

        // 2. 결제 시도
        val attempt = payments.charge(
            customerId = sub.customerId,
            amount = invoice.amount,
            idempotencyKey = "${invoice.id}:${invoice.attemptCount + 1}",
        )

        when (attempt.outcome) {
            PaymentOutcome.SUCCESS -> {
                ledger.post(buildRevenueEntries(invoice))
                subscriptions.advance(sub.id, sub.currentPeriodEnd)
            }
            PaymentOutcome.RETRY -> scheduleRetry(invoice, attempt)
            PaymentOutcome.FAIL -> {
                subscriptions.markPastDue(sub.id)
                notifyCustomer(sub, attempt.failureCode)
            }
        }
    }

    // Smart Retry Waterfall
    private fun scheduleRetry(invoice: Invoice, attempt: PaymentAttempt) {
        val delay = when (attempt.failureCode) {
            "insufficient_funds" -> Duration.ofDays(3)
            "card_declined"      -> Duration.ofDays(5)
            "expired_card"       -> Duration.ofDays(1) // 카드 갱신 요청
            else -> Duration.ofDays(7)
        }
        val maxAttempts = 4
        if (invoice.attemptCount < maxAttempts) {
            invoices.scheduleNextAttempt(invoice.id, Instant.now().plus(delay))
        }
    }

    // Plan 변경 — proration 계산
    fun changePlan(subId: SubscriptionId, newPlanId: PlanId, now: Instant): Money {
        val sub = subscriptions.findById(subId) ?: error("not found")
        val oldPlan = planRepo.findById(sub.planId)
        val newPlan = planRepo.findById(newPlanId)

        val totalDays = ChronoUnit.DAYS.between(sub.currentPeriodStart, sub.currentPeriodEnd)
        val usedDays = ChronoUnit.DAYS.between(sub.currentPeriodStart, now)
        val remainingDays = totalDays - usedDays

        // 잔여일 비례 환불 + 신규 plan 비례 청구
        val refundFromOld = oldPlan.price * (remainingDays.toDouble() / totalDays)
        val chargeForNew = newPlan.price * (remainingDays.toDouble() / totalDays)
        return chargeForNew - refundFromOld
    }
}

// MRR 계산
fun calculateMrr(activeSubscriptions: List<Subscription>): Money = activeSubscriptions
    .filter { it.status == ACTIVE || it.status == TRIALING }
    .sumOf {
        val plan = planRepo.findById(it.planId)
        when (plan.interval) {
            BillingInterval.MONTHLY -> plan.price.amountMinor
            BillingInterval.YEARLY  -> plan.price.amountMinor / 12
            BillingInterval.WEEKLY  -> plan.price.amountMinor * 4  // 근사
        }
    }.let { Money(it, KRW) }
```

**관련 패턴**: [Idempotent Payment](#idempotent-payment), [Payment Intent / Saga](#payment-intent-saga), [Card Network 통합](#card-pci-scope-reduction), [Ledger Pattern](#ledger-pattern), State Machine, Retry (reliability.md)

---

## 안티패턴 (피해야 할 패턴)

이 카테고리에서 자주 등장하는 실수.

### A1. `double` / `float` 로 금액 표현
- IEEE 754 부동소수 → `0.1 + 0.2 != 0.3` → 라운딩 오차 누적 → 1원 사고
- **항상 `BigDecimal` 또는 minor unit `Long`**

### A2. 잔액을 hot row 로 저장 (`UPDATE balance SET amount = ...`)
- 동시성 충돌 / 락 경쟁 / 감사 trail 손실
- **Append-only ledger + derived balance** ([§1](#double-entry-bookkeeping), [§2](#ledger-pattern))

### A3. 멱등성 없는 결제 API
- 클라이언트 재시도 → 이중 결제 → 분쟁
- **Idempotency-Key 의무** ([§5](#idempotent-payment))

### A4. PCI scope 폭발 — PAN / CVV 를 우리 DB 에 저장
- 감사 비용 폭발 + breach 시 책임
- **Tokenization / Hosted Fields 로 격리** ([§11](#card-pci-scope-reduction))

### A5. 환불을 다른 결제수단으로
- AML 위반 (자금세탁 vector)
- **Same-method refund 원칙** ([§9](#refund-chargeback))

### A6. Settlement 완료 전 가맹점에 자금 미리 송금
- Chargeback 발생 시 회수 불가 → 가맹점 부도 위험
- **T+N 정산 cycle 준수** ([§4](#settlement-clearing))

### A7. Reconciliation 자동화 없이 수작업
- 거래량 증가 시 폭발적 운영 비용, 사고 발견 지연
- **3-way reconciliation 파이프라인** ([§3](#reconciliation))

### A8. 제재 명단 스크리닝을 가입 시 1회만
- 명단은 매일 갱신 — 사후 등재된 고객 미탐지
- **주기적 재스크리닝 + 거래시 실시간 체크** ([§10](#aml-kyc))

---

## 패턴 선택 가이드

| 상황 | 우선 적용 패턴 |
|---|---|
| 회계 정합성·감사가 최우선 | [Double-Entry](#double-entry-bookkeeping) + [Ledger](#ledger-pattern) |
| 외부 PG 와 정합 맞춰야 함 | [Reconciliation](#reconciliation) + [Settlement](#settlement-clearing) |
| 결제 API 노출 | [Idempotent Payment](#idempotent-payment) 필수 |
| 카드 결제 + 유럽 사용자 | [3DS](#3ds-authentication) + [Payment Intent](#payment-intent-saga) |
| 비동기 흐름·webhook | [Payment Intent / Saga](#payment-intent-saga) |
| 글로벌·다통화 | [Multi-Currency](#multi-currency-fx) + Money VO |
| 환불·분쟁 처리 | [Refund / Chargeback](#refund-chargeback) |
| 규제 산업·국제 송금 | [AML / KYC](#aml-kyc) |
| 카드 데이터 처리 회피 | [PCI Scope 축소](#card-pci-scope-reduction) |
| SaaS·구독 비즈니스 | [Subscription Billing](#subscription-billing) |

---

## 표준·원전 색인

- **회계 표준**: K-IFRS, IFRS, US GAAP, Pacioli *Summa de Arithmetica* (1494)
- **결제 메시징**: ISO 20022 (XML), ISO 8583 (카드 거래), NACHA (미국 ACH), KFTC 펌뱅킹 전문
- **카드 보안**: PCI DSS v4.0, PCI 3DS Core, EMVCo 3DS 2.x, EMVCo Payment Tokenization
- **유럽 결제 규제**: PSD2, RTS on SCA, SCT Inst
- **AML 표준**: FATF Recommendations 40, BSA (US), 6AMLD (EU), 특정금융거래정보보고법 (한국)
- **블로그·서적**:
  - Stripe Engineering — *Designing Financial Systems* series
  - Fowler — *Patterns of Enterprise Application Architecture* (Money pattern)
  - Vernon — *Implementing Domain-Driven Design* (Aggregate 예시로 금융 도메인 자주 등장)
  - Modern Treasury — *The Ledger Engineering Handbook*

---

**관련 카탈로그 cross-reference**:
- 분산 트랜잭션 일반: [`../distributed.md`](../distributed.md)
- 도메인 모델링: [`../ddd-tactical.md`](../ddd-tactical.md)
- 토큰화 / 암호화: [`../../security/security-data-protection.md`](../../security/security-data-protection.md)
- PCI / PSD2 / GDPR: [`../../security/compliance.md`](../../security/compliance.md)
- 사기 탐지: [`../../security/security-detect-respond.md`](../../security/security-detect-respond.md)
- 데이터 액세스 (Repository): [`../data-access.md`](../data-access.md)
