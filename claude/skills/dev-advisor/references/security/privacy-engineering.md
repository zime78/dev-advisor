# Privacy Engineering (프라이버시 엔지니어링)

GDPR / CCPA / 한국 개인정보보호법 운영을 위한 정평 있는 9 패턴. [`security-data-protection.md`](security-data-protection.md) (Encryption / Tokenization / FPE 같은 *기술적 보호*) 와 differentiate — 본 파일은 **operational privacy** + **사용자 권리 운영**.

**원전·표준 참고**:
- GDPR (EU 2016/679) — Art 5/7/15-22/25/30/32/35
- CCPA/CPRA (California Civil Code §1798)
- 한국 개인정보보호법 (PIPA, 2020/2024 개정)
- Ann Cavoukian — *7 Foundational Principles of Privacy by Design* (2010)
- NIST Privacy Framework v1.0 (2020)
- ISO/IEC 29100 (Privacy framework), ISO/IEC 27701 (PIMS)
- IAPP (International Association of Privacy Professionals) Body of Knowledge

**핵심 원칙**:
- **Privacy by Default** — 사용자가 별도 설정 없이도 최대 프라이버시
- **Purpose Specification & Use Limitation** — 수집 목적 명시 + 그 외 사용 금지
- **Accountability** — DPO / 처리 기록 (RoPA) / DPIA 의무

**관련 카탈로그**:
- [security-data-protection.md](security-data-protection.md) — 기술적 데이터 보호 (Tokenization / FPE / DP)
- [`compliance.md`](compliance.md) — GDPR / CCPA / HIPAA / PCI / SOC 2
- [`security-detect-respond.md`](security-detect-respond.md) — Audit Log (DSAR 대응 logs)
- [`security-authn.md`](security-authn.md) — Identity Governance (SCIM, JIT)

---

<a id="consent-ledger"></a>

## 1. Consent Ledger / Consent Management (동의 원장 / 동의 관리)

**목적**: 사용자가 언제 · 어떤 목적으로 · 어떤 범위의 동의를 부여했는지를 **변조 불가능한 append-only 로그** 로 기록하고, 모든 데이터 처리 시점에 유효한 동의를 조회할 수 있게 합니다. GDPR Art 7(1) "동의를 입증할 책임은 controller 에게 있다" 를 기술적으로 충족합니다.

**메커니즘**:
- 동의 이벤트는 **immutable** — 갱신 / 철회는 새 row 추가, 기존 row 절대 update/delete 금지
- 각 record: `subject_id` · `purpose_id` · `granted|withdrawn|expired` · `version_of_notice` · `timestamp` · `proof`(IP / UA / signed payload) · `legal_basis` (GDPR Art 6)
- **Purpose granularity** — "마케팅 푸시" / "제3자 제공 — 광고 파트너 X" / "이벤트 참여" 처럼 목적별로 분리. 통합 동의 금지(GDPR Art 7(2))
- **Withdrawal as easy as grant** (GDPR Art 7(3)) — 철회 UI 가 동의 UI 와 동등 노력으로 접근 가능
- 시점별 조회: `as_of(t)` 함수로 t 시점의 유효 동의 상태 reconstruct
- 표준: IAB TCF v2.2 (Transparency & Consent Framework), Google Consent Mode v2, W3C Privacy Preserving Attribution
- 구현: OneTrust, Cookiebot, Didomi, Usercentrics, Transcend, Ketch

**장점**:
- GDPR Art 7(1) 입증 책임 자동 충족 — 감사 시 ledger 제출
- 시점별 재구성 가능 — "2025-03-15 광고 노출 시점 동의 있었나?" 즉답
- 동의 변경 패턴 분석 → UX / 법적 위험 조기 식별

**단점·운영 비용**:
- 데이터 볼륨 증가 — 활성 사용자 1M × 평균 8 purposes × 변경 횟수 → 수억 row
- Append-only 보관 → backup / archive 정책 필수 (GDPR 5(1)(e) 와 충돌 주의 — ledger 자체도 retention 적용)
- 시스템 간 동의 동기화 지연 — eventual consistency 시점에 데이터 처리되면 위반

**규제 매핑**:
- **GDPR Art 7** — 동의 조건 (freely given · specific · informed · unambiguous · withdrawable)
- **GDPR Art 6(1)(a)** — 동의를 처리 legal basis 로 사용 시
- **CCPA §1798.135** — Opt-out of Sale/Share (GPC signal 준수)
- **한국 PIPA 제15조** — 개인정보 수집·이용 동의 (필수/선택 분리)
- **한국 PIPA 제17조** — 제3자 제공 별도 동의
- **한국 PIPA 제22조의2** (2024 개정) — 14세 미만 아동 법정대리인 동의

**Consent record schema 예제 (PostgreSQL, append-only)**:
```sql
CREATE TABLE consent_ledger (
  id              BIGSERIAL PRIMARY KEY,
  subject_id      UUID        NOT NULL,
  purpose_id      VARCHAR(64) NOT NULL,    -- 'marketing.push' / 'thirdparty.adX' / 'analytics.behavioral'
  state           VARCHAR(16) NOT NULL CHECK (state IN ('GRANTED','WITHDRAWN','EXPIRED')),
  legal_basis     VARCHAR(32) NOT NULL,    -- 'consent' / 'contract' / 'legitimate_interest' (GDPR Art 6)
  notice_version  VARCHAR(16) NOT NULL,    -- 'privacy-notice-v3.2' (당시 사용자에게 제시한 고지문)
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  proof_ip        INET,
  proof_user_agent TEXT,
  proof_signature BYTEA,                   -- HMAC(subject_id || purpose_id || state || occurred_at)
  source          VARCHAR(32) NOT NULL     -- 'web.banner' / 'mobile.onboarding' / 'csr.phone'
);

-- 절대 UPDATE/DELETE 금지 — DB-level rule
CREATE RULE consent_ledger_no_update AS ON UPDATE TO consent_ledger DO INSTEAD NOTHING;
CREATE RULE consent_ledger_no_delete AS ON DELETE TO consent_ledger DO INSTEAD NOTHING;

-- 시점별 유효 동의 조회 — 각 (subject, purpose) 의 가장 최근 이벤트만
CREATE OR REPLACE VIEW consent_current AS
SELECT DISTINCT ON (subject_id, purpose_id)
  subject_id, purpose_id, state, legal_basis, notice_version, occurred_at
FROM consent_ledger
ORDER BY subject_id, purpose_id, occurred_at DESC;
```

**Kotlin 예제 — 동의 검증 게이트**:
```kotlin
class ConsentGate(private val repo: ConsentLedgerRepo) {

    /**
     * 데이터 처리 전 매번 호출 — 유효 동의가 없으면 처리 거부.
     * GDPR Art 7(1) 입증 책임에 따라 모든 호출은 audit log 에 기록.
     */
    fun requireConsent(subjectId: UUID, purpose: Purpose): ConsentDecision {
        val record = repo.findCurrent(subjectId, purpose.id)
            ?: return ConsentDecision.Deny(reason = "no_consent_record")

        return when {
            record.state == ConsentState.WITHDRAWN -> ConsentDecision.Deny("withdrawn")
            record.state == ConsentState.EXPIRED -> ConsentDecision.Deny("expired")
            // 고지문 버전이 현재 정책보다 오래되었으면 재동의 필요
            record.noticeVersion < purpose.minNoticeVersion ->
                ConsentDecision.Reaffirm("notice_outdated")
            else -> ConsentDecision.Allow(record)
        }.also { auditLog.write(subjectId, purpose, it) }
    }
}
```

**관련 패턴**: [Privacy Notice](#privacy-notice), [Purpose Binding](#purpose-binding), [Privacy Operations](#privacy-operations), [DSAR](#dsar)

---

<a id="privacy-by-design"></a>

## 2. Privacy by Design (PbD)

**목적**: 시스템 설계 초기 단계부터 프라이버시를 **기본값(default)** 으로 내장하여, 사후 보강이 아닌 아키텍처 수준의 보호를 달성합니다. GDPR Art 25 가 법적 의무로 격상시킨 원칙입니다.

**메커니즘**: Ann Cavoukian 의 7 Foundational Principles
1. **Proactive not Reactive; Preventative not Remedial** — 사고 발생 후 대응이 아닌 사전 방지
2. **Privacy as the Default Setting** — 사용자가 아무것도 안 해도 최대 보호 (opt-in default)
3. **Privacy Embedded into Design** — 별도 add-on 이 아닌 핵심 기능에 포함
4. **Full Functionality — Positive-Sum, not Zero-Sum** — 보안 vs 기능 trade-off 가 아닌 양립
5. **End-to-End Security — Full Lifecycle Protection** — 수집부터 폐기까지 전 주기
6. **Visibility and Transparency** — Keep it Open (감사 가능 · 검증 가능)
7. **Respect for User Privacy** — User-Centric (control / consent / notice)

**구현 패턴**:
- **Threat modeling** with privacy-specific frameworks: **LINDDUN** (Linking / Identifying / Non-repudiation / Detecting / Data disclosure / Unawareness / Non-compliance)
- **Data flow mapping** — 모든 PII 입출력 경로를 다이어그램화 (RoPA 와 연계)
- **Default privacy settings**: 위치 공유 OFF, 광고 추적 OFF, 프로필 공개 범위 최소
- **PETs (Privacy Enhancing Technologies)** 1차 검토: pseudonymization → encryption → tokenization → DP → MPC
- **Privacy review checkpoint** — 디자인 / 코드 리뷰 / launch 게이트에 prioritized 질문지 삽입

**장점**:
- 사후 retrofit 비용 회피 (일반적으로 사후 비용은 사전 설계 비용의 10~100배)
- GDPR Art 25 의무 자동 충족 — Data Protection by Design and by Default
- 사용자 신뢰 향상 — Apple 의 ATT(App Tracking Transparency) 가 시장 사례

**단점·운영 비용**:
- 프로덕트 매니저 / 엔지니어 PbD 트레이닝 필요
- 정량 평가 어려움 — "얼마나 더 안전한가" 측정 모호
- Positive-sum 가정이 항상 성립하지 않음 — 일부 기능은 PII 수집 없이 불가

**규제 매핑**:
- **GDPR Art 25** — Data protection by design and by default
- **GDPR Art 25(2)** — 처리 목적에 필요한 최소한의 개인정보만 default 로 처리
- **CCPA §1798.100(c)** — 명시된 목적 외 사용 금지 원칙과 정렬
- **한국 PIPA 제3조** — 개인정보 보호 원칙 (수집 목적 명확화 · 최소 수집)
- **NIST Privacy Framework** — Identify-P / Govern-P / Control-P / Communicate-P / Protect-P 기능

**LINDDUN 위협 모델 체크리스트 예제 (YAML)**:
```yaml
# 신규 피처 'friend recommendation' 의 LINDDUN 분석
feature: friend_recommendation_v1
data_flows:
  - source: user_contacts_upload
    sink: recommendation_engine
    pii: [phone_number, email, name]

threats:
  L_linking:
    description: "익명 사용자와 contact 의 phone 이 연결 가능한가?"
    mitigation: "Bloom filter 기반 PSI(Private Set Intersection) 사용 — raw phone 미저장"
    pet: private_set_intersection
    risk_after_mitigation: low

  I_identifying:
    description: "추천 결과로 미가입자 식별 가능?"
    mitigation: "미가입 phone 은 hash 만 보관 · 30일 후 자동 삭제"
    risk_after_mitigation: medium

  N_nonrepudiation:
    description: "사용자가 추천 거부 사실을 부인할 수 있어야 함"
    mitigation: "거부 액션은 audit log 만 · cryptographic proof 미보관"
    risk_after_mitigation: low

  D_detecting:
    description: "특정 user 가 contact 업로드했는지 외부에서 탐지 가능?"
    mitigation: "TLS + 동일 endpoint 로 dummy 트래픽 padding"
    risk_after_mitigation: low

  D_disclosure:
    description: "DB 유출 시 contact graph 노출?"
    mitigation: "Field-level encryption + pepper 별도 KMS 보관"
    risk_after_mitigation: low

  U_unawareness:
    description: "미가입 contact 가 자신의 phone 이 업로드됐는지 모름"
    mitigation: "Notice on signup: '친구가 당신 번호로 초대했을 수 있음' 고지"
    risk_after_mitigation: medium # 완전 해소 어려움

  N_noncompliance:
    description: "GDPR Art 6 legal basis?"
    mitigation: "업로드자 consent + 미가입자 legitimate interest (LIA 수행)"
    risk_after_mitigation: low

privacy_default:
  contact_upload: opt_in     # 기본 OFF
  retention_days: 30
  share_with_third_party: false

approver: dpo@example.com
approved_at: 2026-04-12
```

**관련 패턴**: [DPIA](#dpia), [Data Minimization](#data-minimization), [Purpose Binding](#purpose-binding), [Privacy Notice](#privacy-notice)

---

<a id="dsar"></a>

## 3. DSAR (Data Subject Access Request) / 정보주체 권리 요청

**목적**: 정보주체가 자신의 개인정보에 대해 행사하는 **접근 · 정정 · 삭제 · 이동 · 처리 제한 · 자동의사결정 거부** 권리를 운영 가능한 워크플로우로 처리합니다. GDPR Art 15-22 가 정의한 6 권리를 SLA 내에 회신해야 합니다.

**메커니즘**:
- 7 요청 타입: **Access(Art 15)** · **Rectification(Art 16)** · **Erasure / Right to be Forgotten(Art 17)** · **Restriction(Art 18)** · **Portability(Art 20)** · **Object(Art 21)** · **Automated Decision-Making(Art 22)**
- **신원 확인 게이트** — 무차별 요청 방어. 본인 인증 후 토큰 발급 → 요청 진행
- **시스템 전체 fanout** — 1 요청 → N 시스템(prod DB / DW / 백업 / 로그 / 분석 / 3rd-party processor) 으로 작업 분기 → 모두 완료 후 회신
- **회신 기한**: GDPR 30일(복잡 시 +60일 연장 + 사유 고지) / CCPA 45일(+45일 연장) / 한국 PIPA 10일(+10일 연장)
- **Erasure 예외**: 법적 보관 의무 / 정당한 이익 / 공익 / 자유 표현 → 거부 사유 명시 필요
- **Portability format**: 구조화·기계가독·상호운용(JSON / XML / CSV) — proprietary binary 금지
- 도구: Transcend, OneTrust, DataGrail, BigID, Securiti

**장점**:
- 법적 의무 SLA 자동 추적 — 위반 시 GDPR Art 83 과징금 (전세계 매출 4% 또는 €20M)
- 사용자 신뢰 강화 — Apple Data & Privacy portal 이 마케팅 자산화 사례
- Data lineage 가시화 부산물 — 어디에 무엇이 있는지 자동 발견

**단점·운영 비용**:
- 시스템 통합 비용 큼 — 모든 PII 저장소에 DSAR API 필요
- Backup / archive 에서 erasure 가 기술적으로 어려움 (immutable storage)
- 악성 / 봇 요청 대응 — rate limit + 신원 확인 강화
- 3rd-party processor 전파 — sub-processor 까지 chain 처리 필요 (GDPR Art 28)

**규제 매핑**:
- **GDPR Art 12** — Transparent information, communication and modalities (1개월 회신)
- **GDPR Art 15** — Right of access
- **GDPR Art 17** — Right to erasure ("right to be forgotten")
- **GDPR Art 20** — Right to data portability
- **CCPA §1798.100** — Right to Know
- **CCPA §1798.105** — Right to Delete
- **CCPA §1798.110/115** — Right to Know specifics (categories / sources / purposes / third parties)
- **한국 PIPA 제35조** — 개인정보 열람권 (10일)
- **한국 PIPA 제36조** — 정정·삭제권
- **한국 PIPA 제37조** — 처리정지권

**DSAR 처리 흐름 (sequence)**:
```
+----------+      +-----------+      +----------+      +----------+      +-------------+
| Subject  |      | DSAR Hub  |      | IDV      |      | Fanout   |      | System N    |
+----+-----+      +-----+-----+      +----+-----+      +----+-----+      +------+------+
     |                  |                 |                 |                   |
     | 1. POST /dsar    |                 |                 |                   |
     | (type=erasure)   |                 |                 |                   |
     +----------------->|                 |                 |                   |
     |                  | 2. verify(email)|                 |                   |
     |                  +---------------->|                 |                   |
     |                  |  3. challenge   |                 |                   |
     |<------(email link, MFA)------------|                 |                   |
     | 4. verify token  |                 |                 |                   |
     +----------------->|                 |                 |                   |
     |                  | 5. ticket #4271 |                 |                   |
     |<-----------------|                 |                 |                   |
     |                  | 6. enqueue --------------------->|                   |
     |                  |                                  | 7. fanout to N    |
     |                  |                                  +------------------>|
     |                  |                                  |  8. erase + ack   |
     |                  |                                  |<------------------+
     |                  |                                  | 9. report status  |
     |                  | 10. all done (SLA tracked: 30d) |                   |
     |                  |<---------------------------------|                   |
     | 11. Completion   |                                  |                   |
     |    notice + log  |                                  |                   |
     |<-----------------|                                  |                   |
```

**Kotlin 예제 — DSAR 오케스트레이션**:
```kotlin
class DsarOrchestrator(
    private val systems: List<DsarHandler>,   // prod DB · DW · 로그 · 3rd-party connectors
    private val idv: IdentityVerifier,
    private val audit: AuditLog
) {
    /**
     * GDPR Art 12(3) — 1개월(필요 시 +2개월) SLA 내 회신.
     * 모든 시스템 fanout 결과를 집계하여 ticket close.
     */
    suspend fun handle(req: DsarRequest): DsarReceipt {
        // 1) 신원 확인 — 토큰 만료 / IP 일치 / MFA 확인
        require(idv.verify(req.subjectId, req.proofToken)) { "identity_unverified" }

        // 2) 법적 예외 사전 평가 (Art 17(3) — 표현의 자유 / 법적 의무 / 공익 / 분쟁)
        val exceptions = legalExceptionEngine.evaluate(req)

        // 3) 모든 시스템에 병렬 fanout (30일 SLA 안에서)
        val results: List<HandlerResult> = coroutineScope {
            systems.map { sys -> async { sys.execute(req, exceptions) } }.awaitAll()
        }

        // 4) 결과 집계 · 감사 로그 · 회신문 생성
        val receipt = DsarReceipt(
            ticketId = req.ticketId,
            type = req.type,
            completedAt = Instant.now(),
            systemsTouched = results.map { it.system to it.outcome },
            exceptions = exceptions
        )
        audit.write(receipt)
        return receipt
    }
}
```

**관련 패턴**: [Consent Ledger](#consent-ledger), [Privacy Operations](#privacy-operations), [Retention Policy](#retention-policy), [Privacy Notice](#privacy-notice)

---

<a id="retention-policy"></a>

## 4. Retention Policy (보관 기간 정책)

**목적**: 개인정보를 **수집 목적 달성에 필요한 최소 기간** 만 보관하고, 기한 도과 시 자동 삭제·익명화합니다. GDPR Art 5(1)(e) "storage limitation" 원칙을 운영 가능한 자동화 job 으로 구현합니다.

**메커니즘**:
- **Retention schedule** — `(data_category, purpose, legal_basis) → retention_days` 매트릭스
- **삭제 방식 3 종**:
  - **Hard delete** — row 물리 삭제 (DB / blob / cache 동시)
  - **Crypto-shredding** — 데이터별 DEK 폐기 → ciphertext 복호화 불가 (백업 / immutable storage 에서 유용)
  - **Anonymization** — k-anonymity / DP 처리 후 보관 (통계 목적 보존)
- **Trigger** 3 유형: 절대 시각 (`created_at + N days`) / 이벤트 (`account_deleted_at + 30d`) / 활동 기반 (`last_login + 2y → 휴면`)
- **Backup / Archive 처리** — write-once 매체 위에선 crypto-shredding 또는 retention 종료 시 backup tape 폐기
- **Legal hold** — 소송 / 규제 조사 중인 record 는 retention 정지 (litigation hold)
- 도구: BigID, Securiti, OpenDLP, Apache Atlas (lineage)

**장점**:
- GDPR Art 5(1)(e) 자동 충족 — 감사 시 schedule + 실행 로그 제출
- Breach blast radius 축소 — 적게 보관할수록 유출 시 영향 작음
- 스토리지 비용 절감 — 5년치 user log 폐기로 PB 단위 절약 사례

**단점·운영 비용**:
- 카테고리 정의 누락 시 미삭제 데이터 잔존 (특히 dev / staging / data lake 사본)
- 참조 무결성 — FK 로 묶인 row 삭제 cascade 설계 필요
- Backup retention vs 삭제 충돌 — backup 보관기간 동안 erasure 권리 충돌 (crypto-shredding 해결)
- 휴면 계정 통지 의무 (한국 PIPA 휴면 1년 → 분리보관 또는 파기) — 2023 개정으로 유효기간제 폐지됐으나 별도 보관 분리 정책 권장

**규제 매핑**:
- **GDPR Art 5(1)(e)** — Storage limitation principle
- **GDPR Art 13(2)(a)** — 보관기간 고지 의무
- **CCPA §1798.100(a)(3)** — Retention period 고지 (CPRA 추가)
- **한국 PIPA 제21조** — 개인정보 파기 (목적 달성 후 지체 없이)
- **한국 PIPA 시행령 제16조** — 파기 방법 (복원 불가능)
- **신용정보법 제20조의2** — 신용정보 5년 보관

**Retention schedule 예제 (YAML)**:
```yaml
# retention_schedule.yaml — DPO 승인 + 매년 검토
version: 2026.1
reviewed_by: dpo@example.com
reviewed_at: 2026-01-15

categories:
  account_profile:
    description: "이름 · 이메일 · 전화 · 생년월일"
    retention: account_lifetime + 30d
    legal_basis: GDPR.6.1.b   # contract performance
    deletion_method: hard_delete
    cascade: [auth_credentials, consent_ledger.subject_id_index]

  payment_records:
    description: "결제 이력 · 청구서 · 환불"
    retention: 5y             # 한국 전자상거래법 제6조 / 미국 IRS 7y는 별도
    legal_basis: GDPR.6.1.c   # legal obligation (세법)
    deletion_method: hard_delete
    legal_hold_aware: true

  marketing_engagement:
    description: "캠페인 클릭 · 푸시 열람"
    retention: 1y
    legal_basis: GDPR.6.1.a   # consent
    deletion_method: hard_delete
    early_deletion_on_consent_withdrawal: true

  access_logs:
    description: "로그인 / API 호출 로그 (audit + security)"
    retention: 6m
    legal_basis: GDPR.6.1.f   # legitimate interest (보안)
    deletion_method: anonymization  # IP / UA 만 hash, timestamp + status 유지
    rationale: "보안 통계 보존 필요 · 개인 재식별 차단"

  dormant_account:
    description: "1년 무로그인 계정"
    retention: 1y_since_last_login
    action: separate_storage  # 한국 PIPA — 분리 보관
    deletion_method: hard_delete after additional 4y

  backups:
    description: "DB 풀백업 (S3 Glacier)"
    retention: 90d
    deletion_method: crypto_shredding   # tape / immutable storage
    key_destroyed_after_90d: true
```

**Kotlin 예제 — 일일 retention sweeper**:
```kotlin
// 매일 02:00 KST 실행 — DPO 가 승인한 retention_schedule.yaml 기반
@Scheduled(cron = "0 0 2 * * *", zone = "Asia/Seoul")
fun sweep() {
    val schedule = RetentionSchedule.load()
    schedule.categories.forEach { cat ->
        val expired = repo.findExpired(category = cat.name, cutoff = cat.cutoffInstant())
        expired
            .filterNot { legalHoldService.isHeld(it.subjectId) }   // 소송 hold 제외
            .chunked(1_000)
            .forEach { batch ->
                when (cat.deletionMethod) {
                    HARD_DELETE -> repo.hardDelete(batch.map { it.id })
                    CRYPTO_SHRED -> kms.destroyDek(batch.map { it.dekId })
                    ANONYMIZATION -> repo.anonymize(batch, cat.anonymizationPolicy)
                }
                audit.write(
                    action = "retention.sweep",
                    category = cat.name,
                    count = batch.size,
                    method = cat.deletionMethod
                )
            }
    }
}
```

**관련 패턴**: [DSAR](#dsar) (erasure 권리), [Data Minimization](#data-minimization), [Privacy Operations](#privacy-operations), [Consent Ledger](#consent-ledger)

---

<a id="purpose-binding"></a>

## 5. Purpose Binding / Purpose Limitation (목적 제한)

**목적**: 데이터를 수집 시 명시한 목적 외 용도로 사용하지 못하도록 **데이터 자체에 목적 메타데이터를 결합** 하고, 처리 시점마다 목적 일치를 검증합니다. GDPR Art 5(1)(b) "purpose limitation" 의 기술적 강제.

**메커니즘**:
- **Purpose taxonomy** — 조직 전체에서 합의된 목적 ID 카탈로그 (`marketing.email` / `analytics.product` / `fraud.detection` ...)
- **Sticky policy** — 데이터 row / payload 에 `collected_for: [purpose_id, ...]` 메타데이터 첨부, 시스템 간 이동 시에도 유지
- **Compatible use** (GDPR Art 6(4)) — 원래 목적과 양립 가능한 추가 처리만 허용 (compatibility test: 맥락 · 데이터 성격 · 결과 · 안전조치)
- **Policy enforcement point (PEP)** — 데이터 접근 게이트가 caller 의 declared purpose 와 데이터의 collected purpose 일치 검증
- **Purpose-specific 격리** — 동일 사용자 데이터라도 목적별로 다른 DB / schema / encryption key 분리
- 학술: Mont et al. *Sticky Policies* (HP Labs), W3C ODRL (Open Digital Rights Language)
- 구현: Immuta, Privacera, Apache Ranger row/column filters with purpose tags

**장점**:
- 사용자 신뢰 — "내 데이터가 약속한 용도로만 쓰인다" 입증 가능
- GDPR Art 5(1)(b) 자동 충족
- ML 학습 시 데이터 부적격 자동 차단 (ex: 결제 목적 데이터를 광고 모델 학습 input 으로 사용 시도 차단)

**단점·운영 비용**:
- Purpose taxonomy 합의 비용 — 부서간 정치 발생
- "Compatible use" 판정 자동화 어려움 — 법률 검토 인적 자원 필요
- 메타데이터 전파 — legacy 시스템 / 3rd-party export 시 sticky 깨지기 쉬움
- 분석 / ML 사용성 vs 엄격 binding trade-off

**규제 매핑**:
- **GDPR Art 5(1)(b)** — Purpose limitation
- **GDPR Art 6(4)** — Compatibility test for further processing
- **GDPR Art 13(3) / 14(4)** — 추가 목적 처리 시 사전 고지
- **CCPA §1798.100(b)** — 수집 시점 목적 고지
- **CCPA §1798.121** — Right to limit sensitive PI use
- **한국 PIPA 제18조** — 개인정보의 목적 외 이용·제공 제한
- **한국 PIPA 제15조(3)** — 당초 수집 목적과 합리적으로 관련된 범위 내 추가 이용

**Purpose-tagged record 예제**:
```sql
CREATE TABLE user_event (
  id            BIGSERIAL PRIMARY KEY,
  subject_id    UUID NOT NULL,
  event_type    VARCHAR(64),
  payload       JSONB,
  -- Sticky purpose metadata — 데이터의 일부로 영속화
  collected_for TEXT[] NOT NULL,        -- {'analytics.product','recommendation.feed'}
  collected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  legal_basis   VARCHAR(32) NOT NULL,
  notice_version VARCHAR(16) NOT NULL
);

-- Purpose 별 row-level security 정책
CREATE POLICY analytics_only ON user_event
  FOR SELECT
  USING ('analytics.product' = ANY(collected_for)
         AND current_setting('app.purpose') = 'analytics.product');

ALTER TABLE user_event ENABLE ROW LEVEL SECURITY;
```

**Kotlin 예제 — Policy Enforcement Point**:
```kotlin
/**
 * 모든 데이터 read / write 가 통과하는 게이트.
 * Caller 는 자신이 수행 중인 처리의 declared purpose 를 함께 제출.
 */
class PurposeEnforcer(private val taxonomy: PurposeTaxonomy) {

    fun authorize(
        record: DataRecord,
        callerPurpose: PurposeId,
        operation: Operation
    ): Decision {
        // 1) Caller purpose 가 카탈로그에 등록되어 있는가
        val purpose = taxonomy.lookup(callerPurpose)
            ?: return Decision.Deny("unknown_purpose")

        // 2) 데이터 sticky purpose 와 일치하는가
        if (callerPurpose in record.collectedFor) return Decision.Allow

        // 3) Compatible use (GDPR Art 6(4)) — 사전 등록된 호환 관계만 허용
        if (taxonomy.isCompatible(from = record.collectedFor, to = callerPurpose)) {
            audit.write("compatible_use", record.id, callerPurpose, record.collectedFor)
            return Decision.Allow
        }

        // 4) 그 외 — 거부 + 위반 감사 로그 (DPO 알람)
        audit.violation(record.id, callerPurpose, record.collectedFor, operation)
        return Decision.Deny("purpose_mismatch")
    }
}
```

**관련 패턴**: [Consent Ledger](#consent-ledger), [Privacy by Design](#privacy-by-design), [Data Minimization](#data-minimization), [Privacy Notice](#privacy-notice)

---

<a id="dpia"></a>

## 6. DPIA (Data Protection Impact Assessment) / 개인정보 영향평가

**목적**: 고위험 처리 활동을 시작하기 **전** 에 잠재적 프라이버시 영향을 체계적으로 평가하고, 식별된 위험을 완화 조치로 줄입니다. GDPR Art 35 가 특정 처리에 대해 의무화한 사전 평가.

**메커니즘**:
- **DPIA 필수 조건** (GDPR Art 35(3) + EDPB Guidelines WP248):
  1. 자동 의사결정 + 법적 효력 (예: 신용평가 / 채용 스크리닝)
  2. 대규모 특수 카테고리 처리 (Art 9: 인종 / 종교 / 건강 / 성생활 / 생체)
  3. 공공장소 대규모 systematic monitoring (CCTV / 안면인식)
  - 9가지 기준 중 2가지 이상 해당 시 DPIA 의무
- **9 구성 요소** (Art 35(7)):
  1. 처리의 체계적 설명 + 목적
  2. 필요성 · 비례성 평가
  3. 정보주체 권리·자유에 대한 위험 평가
  4. 위험 대응 조치
  5. 자문 (DPO / 정보주체 의견 청취)
  6. 컴플라이언스 명시
  7. 적용 안전조치
  8. 잔존 위험 (residual risk)
  9. 모니터링 계획
- **사전 협의 (Prior Consultation)** — DPIA 결과 high residual risk 시 감독기구(예: CNIL / ICO / 개인정보보호위원회) 사전 협의 의무 (Art 36)
- 도구: OneTrust DPIA, TrustArc, RSA Archer, 자체 Notion / Confluence 템플릿

**장점**:
- 고비용 사고 사전 차단 — 출시 후 발견되는 위험은 retrofit 비용 큼
- GDPR Art 35 의무 충족 + 위반 시 과징금 (Art 83(4): 최대 €10M 또는 매출 2%)
- 의사결정 트레이스 — 왜 이 처리를 승인했는지 감사 가능

**단점·운영 비용**:
- 시간 소요 — 평균 2~6주 · 복잡 케이스 3개월
- 평가 품질 편차 — 평가자 역량 의존
- "DPIA 통과 = 위험 없음" 오해 — 잔존 위험 인지 필요
- 빠른 launch 압박과 충돌

**규제 매핑**:
- **GDPR Art 35** — Data Protection Impact Assessment
- **GDPR Art 36** — Prior consultation
- **GDPR Recital 90/91** — DPIA 적용 범위
- **EDPB Guidelines WP248** — DPIA 필수 9 기준
- **CCPA / CPRA §1798.185(a)(15)** — Risk assessment (CPPA 규정 진행 중)
- **한국 PIPA 제33조** — 개인정보 영향평가 (공공기관 의무, 민간 권장)
- **한국 영향평가 시행령** — 5만건 이상 민감정보 / 50만건 이상 일반정보 등 기준
- **NIST Privacy Framework** — Identify-P / Risk Assessment subcategory

**DPIA 템플릿 (Markdown 발췌)**:
```markdown
# DPIA — 채용 자동 스크리닝 시스템 v1
- DPIA ID: DPIA-2026-014
- Initiated: 2026-03-01
- DPO Review: pending
- Status: DRAFT

## 1. 처리 활동 설명
- 목적: 지원자 이력서를 NLP 모델로 점수화 → 1차 통과/탈락 자동 결정
- 데이터: 이력서 (이름 · 학력 · 경력 · 자기소개 · 사진)
- 정보주체: 채용 지원자 (연간 ~50,000명)
- Legal basis: GDPR Art 6(1)(f) legitimate interest + Art 22(2)(b) 명시 동의 + 인간 검토 권리

## 2. 필요성 · 비례성
- Q: 자동화 없이 인력으로 처리 가능한가? → 가능하나 비용 5배
- Q: 더 적은 데이터로 가능한가? → 이름 / 사진은 편향 위험, 제거 가능 → ADOPTED

## 3. 위험 평가 (likelihood × severity)
| 위험 | L | S | Score | 비고 |
|---|---|---|---|---|
| 알고리즘 편향 (성별 / 인종) | H | H | 9 | Art 22 + 차별금지법 |
| 학습 데이터 유출 | M | H | 6 | 이력서 dataset breach |
| 자동결정 거부권 미통지 | M | M | 4 | Art 22(3) |

## 4. 완화 조치
- 이름 / 사진 / 성별 / 나이 제거 (data minimization)
- Fairness audit 분기별 (demographic parity / equalized odds)
- 모든 자동 거부 결정에 대해 인간 검토 옵션 명시 + 1 click 요청
- 모델 가중치 KMS 암호화 + 접근 RBAC
- 학습 데이터 retention 2y · 익명화 후 3y 추가 보관

## 5. 잔존 위험
- Fairness audit 1차 결과: 성별 균등 0.94 (acceptable threshold 0.8 통과)
- 잔존 위험: medium → Prior Consultation 불필요로 판단

## 6. 자문
- DPO: pending
- Works council (EU): 협의 완료 2026-02-18
- 정보주체 대표 (지원자 패널) 의견 청취: 진행 중

## 7. 모니터링
- 분기별 fairness audit · DPO 보고
- 연간 DPIA 재검토 · 모델 retrain 시마다 재평가
- Sign-off required: DPO + CTO + Head of People
```

**관련 패턴**: [Privacy by Design](#privacy-by-design), [Data Minimization](#data-minimization), [Purpose Binding](#purpose-binding), [Privacy Notice](#privacy-notice)

---

<a id="privacy-notice"></a>

## 7. Privacy Notice (개인정보 처리방침)

**목적**: 처리 활동에 대해 정보주체에게 **투명하고 이해 가능한** 정보를 제공합니다. 단순 법적 문구 나열이 아니라 정보 비대칭을 해소하는 UX 자산.

**메커니즘**:
- **3 계층 구조 (Layered notice)**:
  - **Layer 1 (Just-in-time)** — 데이터 수집 시점 한 줄 ("위치는 길찾기에만 사용")
  - **Layer 2 (Summary / dashboard)** — 카드형 요약 + 관리 액션
  - **Layer 3 (Full policy)** — 법적 완전 문서
- **GDPR Art 13/14 필수 정보** 14개 항목:
  - controller / DPO 연락처 · 처리 목적 · legal basis · 정당한 이익 (LIA 시) · 수령자 · 제3국 이전 · 보관기간 · 정보주체 권리 · 동의 철회권 · 감독기구 진정권 · 제공 의무성 · 자동 의사결정 · 추가 목적 처리 · 출처 (Art 14)
- **Just-in-time notice** — 위치 / 카메라 / 연락처 권한 요청 시점에 inline 으로 노출
- **Plain language** — Flesch-Kincaid grade 9 이하 권장, 법률 용어 minimal
- **Versioning + diff** — 정책 변경 시 이전 버전 archive + 사용자에게 의미 있는 변경만 통지
- **Multilingual** — 서비스 제공 언어 모두에서 동등 품질
- 도구: Termly, iubenda, Cookiebot policy generator (legal review 필수)

**장점**:
- GDPR Art 12-14 / CCPA / PIPA 의무 충족
- 사용자 통제권 증대 → 신뢰 / 전환율 향상 (Apple privacy nutrition label 마케팅 효과)
- DSAR / 동의 분쟁 시 입증 자료

**단점·운영 비용**:
- 법무 검토 비용 — 정책 1회 작성 → 매 변경마다 재검토
- 다국어 동기화 누락 위험
- "Cookie banner fatigue" — UX 피로 → dark pattern 유혹

**규제 매핑**:
- **GDPR Art 12** — Transparent information (concise · transparent · intelligible · easily accessible · plain language)
- **GDPR Art 13** — Information collected from subject
- **GDPR Art 14** — Information not collected from subject (3rd party data)
- **GDPR Art 22(3)** — 자동 의사결정 고지
- **CCPA §1798.130** — Notice at collection
- **CCPA §1798.135** — Do Not Sell/Share notice
- **한국 PIPA 제30조** — 개인정보 처리방침 수립·공개 (필수 8 항목)
- **한국 PIPA 제15조(2)** — 수집·이용 동의 시 4 사항 고지

**Privacy notice metadata 예제 (JSON)**:
```json
{
  "policy_version": "3.2",
  "effective_from": "2026-05-01",
  "previous_version": "3.1",
  "languages": ["ko","en","ja"],
  "controller": {
    "name": "KakaoVX",
    "address": "Seoul, Republic of Korea",
    "dpo_email": "dpo@example.com"
  },
  "purposes": [
    {
      "id": "service.account",
      "title_ko": "회원 계정 운영",
      "title_en": "Account operation",
      "data_categories": ["email","phone","name","birthdate"],
      "legal_basis": "contract",
      "retention": "account_lifetime + 30d",
      "recipients": ["aws (data processor)","sendgrid (email)"],
      "international_transfer": {
        "country": "US",
        "safeguard": "SCCs 2021/914",
        "adequacy_decision": false
      },
      "automated_decision": false
    },
    {
      "id": "marketing.push",
      "title_ko": "맞춤형 마케팅 푸시",
      "title_en": "Personalized marketing push",
      "data_categories": ["device_token","app_usage","preferences"],
      "legal_basis": "consent",
      "retention": "1y_or_until_withdrawal",
      "withdraw_url": "/account/privacy/marketing",
      "automated_decision": true,
      "art22_human_review_available": true
    }
  ],
  "user_rights": {
    "access": "/dsar/access",
    "rectify": "/dsar/rectify",
    "erase": "/dsar/erase",
    "portability": "/dsar/export",
    "object": "/dsar/object",
    "complaint_authority": "https://www.pipc.go.kr"
  },
  "change_log": [
    {"version":"3.2","date":"2026-05-01","summary":"제3자 제공 — Sendgrid 추가 · 보관기간 명시"}
  ]
}
```

**Kotlin 예제 — Just-in-time notice 발행**:
```kotlin
class JustInTimeNoticeService(private val policy: PrivacyPolicy) {

    /**
     * 권한 요청 / 데이터 수집 액션 직전에 호출.
     * 현재 정책 버전 + 사용자가 이전에 본 버전을 비교하여 변경된 경우 강조.
     */
    fun renderNotice(action: SensitiveAction, locale: Locale, userLastSeen: PolicyVersion): Notice {
        val purpose = policy.purposeFor(action)
        return Notice(
            headline = purpose.shortTitle(locale),               // "위치는 길찾기에만 사용해요"
            detailUrl = "/policy#${purpose.id}",
            legalBasis = purpose.legalBasis,
            requiresConsent = purpose.legalBasis == LegalBasis.CONSENT,
            changedSinceLastSeen = policy.diff(userLastSeen).touches(purpose.id),
            withdrawAlwaysAvailableAt = purpose.withdrawUrl
        )
    }
}
```

**관련 패턴**: [Consent Ledger](#consent-ledger), [Privacy by Design](#privacy-by-design), [DSAR](#dsar), [Privacy Operations](#privacy-operations)

---

<a id="data-minimization"></a>

## 8. Data Minimization (개인정보 최소 수집)

**목적**: 목적 달성에 **반드시 필요한 최소 데이터** 만 수집·보관·처리합니다. GDPR Art 5(1)(c) 의 핵심 원칙 — "안 가진 데이터는 유출되지 않는다".

**메커니즘**:
- **Collection-time filtering** — 클라이언트 / 게이트웨이에서 불필요 필드 제거 (예: 이미지 EXIF GPS 자동 strip)
- **Field-level proportionality** — "정말 birthdate 풀(YYYY-MM-DD) 이 필요한가? age band 면 충분?"
- **Aggregation / abstraction**:
  - 정확 위치(±10m) → 시군구
  - 정확 나이 → 5세 band
  - IP 주소 → /24 prefix
- **Hash before store** — 식별만 필요하면 raw 보관 X, HMAC(salt, id) 만
- **Just-in-time collection** — 결제 정보는 결제 직전에만 수집, 가입 시점 X
- **Inference risk reduction** — quasi-identifier 조합으로 재식별 가능성 확인 (k-anonymity 평가)
- **Auto-delete on use** — 일회성 사용 후 즉시 폐기 (OTP / 본인확인 결과)

**장점**:
- Breach blast radius 축소 — 적게 가지면 적게 잃음
- 스토리지 / 컴퓨트 비용 절감
- GDPR Art 5(1)(c) / Art 25(2) 자동 충족
- 사용자 신뢰 (Apple ATT / Mozilla privacy 마케팅이 시장 사례)

**단점·운영 비용**:
- 비즈니스 부서 저항 — "혹시 모르니 다 받자"
- Retrofit 비용 — 기존 시스템에서 필드 제거는 dependency hunt 필요
- 합법적 추가 목적 발견 시 재수집 불가능 — 사용자 재동의 필요
- Analytics 정확도 trade-off — 정밀 location 없이 지역 통계 어려움

**규제 매핑**:
- **GDPR Art 5(1)(c)** — Data minimisation
- **GDPR Art 25(2)** — Data protection by default (필요한 최소 처리만)
- **GDPR Recital 39** — Adequate · relevant · limited to what is necessary
- **CCPA §1798.100(c)** — Necessary and proportionate to purposes
- **한국 PIPA 제3조(1)** — 개인정보의 처리 목적에 필요한 최소한의 개인정보만 수집
- **한국 PIPA 제16조** — 수집한 개인정보의 범위를 초과한 정보 처리 금지

**Data minimization audit 예제**:
```sql
-- 매월 collection log 분석 — 수집했지만 30일간 read 되지 않은 필드 식별
WITH field_read_stats AS (
  SELECT
    field_name,
    COUNT(DISTINCT subject_id) AS subjects_read,
    MAX(last_read_at) AS most_recent_read
  FROM data_access_log
  WHERE access_time > now() - INTERVAL '30 days'
  GROUP BY field_name
),
field_collection_stats AS (
  SELECT
    field_name,
    COUNT(DISTINCT subject_id) AS subjects_collected
  FROM data_collection_log
  WHERE collected_at > now() - INTERVAL '30 days'
  GROUP BY field_name
)
SELECT
  c.field_name,
  c.subjects_collected,
  COALESCE(r.subjects_read, 0) AS subjects_read,
  CASE
    WHEN r.subjects_read IS NULL THEN 'UNUSED — candidate for removal'
    WHEN r.subjects_read::float / c.subjects_collected < 0.01 THEN 'RARELY USED — review'
    ELSE 'ACTIVE'
  END AS recommendation
FROM field_collection_stats c
LEFT JOIN field_read_stats r ON r.field_name = c.field_name
ORDER BY subjects_read NULLS FIRST;
```

**Kotlin 예제 — 수집 게이트**:
```kotlin
/**
 * 모든 user input 이 통과하는 sanitizer.
 * 정책에 등록되지 않은 필드는 silently drop · DPO 알람.
 */
class MinimizationFilter(private val policy: CollectionPolicy) {

    fun sanitize(input: SignupForm, purpose: Purpose): SignupForm {
        val allowed = policy.allowedFields(purpose)
        val dropped = mutableListOf<String>()

        val cleaned = SignupForm(
            email = input.email.takeIf { "email" in allowed },
            phone = input.phone.takeIf { "phone" in allowed },
            // 생년월일 전체 대신 연도만 (age band 계산용)
            birthYear = input.birthdate?.year?.takeIf { "birth_year" in allowed },
            // 정확 위치 대신 시군구만
            region = input.gpsLocation?.let { geocoder.toRegion(it) }
                .takeIf { "region" in allowed }
        ).also {
            if (input.birthdate != null && "birthdate" !in allowed)
                dropped += "birthdate"
            if (input.gpsLocation != null && "gps" !in allowed)
                dropped += "gps"
        }

        if (dropped.isNotEmpty()) {
            audit.write("minimization.dropped", purpose, dropped)
            metrics.increment("minimization.drops", "purpose" to purpose.id)
        }
        return cleaned
    }
}
```

**관련 패턴**: [Privacy by Design](#privacy-by-design), [Purpose Binding](#purpose-binding), [Retention Policy](#retention-policy), [DPIA](#dpia)

---

<a id="privacy-operations"></a>

## 9. Privacy Operations (PrivOps)

**목적**: 프라이버시 의무 (consent · DSAR · retention · breach notification · 3rd-party DPA · DPIA) 를 **자동화된 운영 워크플로우** 로 묶어 매뉴얼 처리 의존도를 제거합니다. DevOps / SRE 패턴을 프라이버시에 적용한 모델.

**메커니즘**:
- **Privacy data lineage** — 모든 시스템에서 PII 흐름을 자동 발견 (Apache Atlas / DataHub / OpenLineage + 자동 classifier)
- **Automated DSAR fulfillment** — 1 요청 → 모든 시스템 fanout, 30일 SLA 추적 dashboard
- **Continuous compliance scanning** — 정책 위반 (만료된 retention / 미고지 신규 필드 / consent 없이 처리) 자동 탐지
- **Breach detection + 72h notification** — GDPR Art 33 의 72시간 감독기구 통보 자동화 (incident response runbook + DPO 알람 + 통보 초안 자동 작성)
- **Sub-processor monitoring** (GDPR Art 28) — 3rd-party DPA list / sub-processor 변경 자동 통지
- **Privacy KPI dashboard** — DSAR median completion / 동의 철회율 / retention 위반 건수 / breach MTTR
- **Privacy CI/CD** — 신규 PR 에 PII 필드 추가 시 자동 review trigger (linter + DPO 승인 게이트)
- 도구: Transcend, Securiti, BigID, DataGrail, OneTrust, Privacera, Immuta

**장점**:
- 매뉴얼 처리 누락 / 실수 제거 — 30일 SLA · 72h breach 자동 추적
- 감사 비용 절감 — 컴플라이언스 증거가 자동 생성
- 사용자 신뢰 / 마케팅 자산 (privacy dashboard 공개)
- DPO / Privacy Office 가 정책 / 협의에 집중 가능

**단점·운영 비용**:
- 도구 도입 비용 (Transcend / OneTrust enterprise tier 연 $100K+)
- 자동화 over-confidence — 자동화가 놓치는 edge case 잔존
- 시스템 통합 long-tail — legacy 시스템 / 분산 spreadsheet 통합 어려움
- "Compliance theater" 위험 — 자동화는 했으나 실제 보호 효과 미검증

**규제 매핑**:
- **GDPR Art 5(2)** — Accountability principle
- **GDPR Art 24** — Responsibility of the controller
- **GDPR Art 28** — Processor / sub-processor management
- **GDPR Art 30** — Records of Processing Activities (RoPA)
- **GDPR Art 32** — Security of processing
- **GDPR Art 33** — Breach notification to supervisory authority (72h)
- **GDPR Art 34** — Breach communication to data subject (high risk)
- **GDPR Art 37-39** — DPO
- **CCPA §1798.100-199** — 운영 의무 전반
- **한국 PIPA 제29조** — 안전조치 의무
- **한국 PIPA 제34조** — 개인정보 유출 통지 (72시간) / §39의4 (5일 — 1천명 이상)
- **한국 PIPA 제31조** — 개인정보 보호책임자 (CPO)

**RoPA (Records of Processing Activities) 예제 (YAML)**:
```yaml
# GDPR Art 30 — controller 가 유지해야 하는 처리 기록
ropa_version: 2026.1
controller:
  name: KakaoVX
  representative: example.com
  dpo: dpo@example.com

processing_activities:
  - id: PA-001
    name: 회원 가입 및 계정 관리
    purposes: [service.account, service.authentication]
    data_subjects: [registered_users]
    data_categories: [contact_info, credentials, profile]
    recipients: [aws_processor, sendgrid_processor]
    international_transfers:
      - country: US
        safeguard: SCCs 2021/914
        documents: [DPA-AWS-2024.pdf]
    retention: account_lifetime + 30d
    security_measures:
      - encryption_at_rest: AES-256-GCM
      - encryption_in_transit: TLS 1.3
      - access_control: RBAC + MFA
      - audit_log: enabled
    dpia_required: false
    dpia_link: null

  - id: PA-014
    name: 채용 자동 스크리닝
    purposes: [recruiting.screening]
    data_subjects: [job_applicants]
    data_categories: [resume, education, employment_history]
    recipients: []
    automated_decision: true
    art22_safeguards:
      - human_review_on_request
      - notice_in_application_form
    dpia_required: true
    dpia_link: DPIA-2026-014
    retention: 2y (anonymized after)
```

**Kotlin 예제 — 72h breach notification 자동 트리거**:
```kotlin
class BreachOrchestrator(
    private val supervisor: SupervisoryAuthorityClient,  // CNIL / ICO / 개보위 API
    private val dpo: DpoNotifier,
    private val clock: Clock
) {
    /**
     * GDPR Art 33 — 인지 후 72시간 이내 감독기구 통보.
     * "정보주체의 권리와 자유에 대한 위험" 평가 후 high 시 정보주체 통보 (Art 34).
     */
    suspend fun report(incident: SecurityIncident) {
        val detectedAt = incident.detectedAt
        val deadline = detectedAt.plus(Duration.ofHours(72))

        // 1) DPO 즉시 알람 (5분 SLA)
        dpo.urgentAlert(incident)

        // 2) 위험 평가 — affected subjects · data sensitivity · likelihood
        val riskAssessment = privacyRiskEngine.assess(incident)

        // 3) 72h 카운트다운 추적 — 미수행 시 자동 알람 escalation
        scheduler.schedule(deadline.minus(Duration.ofHours(12))) {
            if (!supervisor.hasReceived(incident.id)) {
                pager.escalate("BREACH_NOTIFICATION_DEADLINE_APPROACHING", level = P0)
            }
        }

        // 4) 통보문 초안 자동 작성 (Art 33(3) 4 요소: nature · contact · likely consequences · measures)
        val draft = NotificationDraft(
            incidentId = incident.id,
            nature = incident.summary,
            affectedCategories = incident.dataCategories,
            affectedCount = incident.subjectsAffected,
            likelyConsequences = riskAssessment.consequences,
            measuresTaken = incident.containmentActions,
            dpoContact = "dpo@example.com"
        )
        supervisor.submitDraft(draft)

        // 5) High risk 시 정보주체에게도 통보 (Art 34) — 1천명 이상이면 한국 PIPA 5일 SLA 별도
        if (riskAssessment.level == RiskLevel.HIGH) {
            subjectNotifier.enqueue(incident.affectedSubjects, draft.toSubjectFriendly())
        }

        audit.write("breach.reported", incident.id, clock.instant(), deadline)
    }
}
```

**관련 패턴**: [Consent Ledger](#consent-ledger), [DSAR](#dsar), [Retention Policy](#retention-policy), [DPIA](#dpia), [Privacy Notice](#privacy-notice), [Purpose Binding](#purpose-binding)

---
