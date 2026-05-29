# 규제 컴플라이언스 패턴 (Regulatory Compliance Patterns)

이 카테고리는 디자인 패턴이 아니라 **규제 통제 프레임**이다. `patterns/` 안에 두는 이유: 각 규제가 코드 구조·데이터 모델·API 설계·인프라 아키텍처에 직접 영향을 미치는 **설계 결정**을 강제하기 때문이다 (예: GDPR → 개인정보 필드 암호화 + 감사 로그 + 보존 기간 정책, PCI DSS → 카드번호 토큰화 → DB 스키마 변경). dev-catalog 통합 접근성을 위해 보안 패턴 카탈로그 내 배치한다.

---

## 1. GDPR (General Data Protection Regulation, EU 2016/679)

**목적**: EU 거주자의 개인 데이터 처리에 대한 법적 기반, 권리 보장, 위반 시 제재(전 세계 매출의 4% 또는 €2천만 중 큰 값)를 규정합니다.

**핵심 요구사항**:
- **Lawful Basis (적법 처리 근거)**: 동의(Consent) / 계약 이행 / 법적 의무 / 정당한 이익 중 하나 이상 명시
- **DPO (Data Protection Officer)**: 대규모 민감 데이터 처리 조직은 DPO 임명 의무
- **DPIA (Data Protection Impact Assessment)**: 고위험 처리(프로파일링, 민감 정보 대규모 처리) 전 영향 평가
- **Data Subject Rights**: 열람(Access) · 정정(Rectification) · 삭제(Erasure, "잊혀질 권리") · 이동성(Portability) · 처리 제한(Restriction) · 반대(Objection)
- **Breach Notification**: 침해 인지 후 **72시간** 이내 감독기관 신고, 고위험이면 당사자도 지체 없이 통지
- **Data Minimization**: 목적에 필요한 최소 데이터만 수집
- **Storage Limitation**: 목적 달성 후 보존 기간 정책에 따라 삭제
- **Cross-border Transfer**: EU 역외 이전 시 Adequacy Decision / SCCs / BCRs 필요

**코드·시스템 영향**:
| 요구사항 | 구현 |
|---------|------|
| 잊혀질 권리 | 개인 데이터 논리 삭제 + 연관 데이터 cascade / 익명화 |
| 데이터 이동성 | JSON/CSV export API |
| 감사 추적 | 모든 접근·수정에 `accessed_by`, `accessed_at`, `purpose` 기록 |
| 목적 제한 | 수집 목적 코드화, 목적 외 처리 시 차단 |
| 저장 제한 | 보존 기간 TTL + 자동 삭제 스케줄러 |
| 민감 필드 | 필드 레벨 암호화 (이름·이메일·주소·건강정보) |

**난이도**: 높음 | **적용 빈도**: ★★★★★ (EU 사용자 대상 모든 서비스)

**Kotlin 예제**:
```kotlin
/**
 * GDPR Article 17 — "잊혀질 권리" 처리.
 * 사용자 데이터를 완전 삭제하거나 익명화하고, 감사 로그를 남깁니다.
 */
@Service
@Transactional
class GdprErasureService(
    private val userRepo: UserRepository,
    private val orderRepo: OrderRepository,
    private val auditLog: AuditLogService,
) {
    fun eraseUser(userId: UUID, requestedBy: String) {
        val user = userRepo.findById(userId)
            ?: throw NotFoundException("User not found: $userId")

        // 주문 등 법적 보존 의무 데이터는 익명화 (완전 삭제 불가)
        orderRepo.anonymizeByUser(userId)   // name→"삭제됨", email→null, address→null

        // 나머지 개인 데이터 완전 삭제
        userRepo.delete(user)

        // 처리 기록 — 감독기관 제출용 (userId hash만 보관, 원문 미저장)
        auditLog.record(
            action      = "GDPR_ERASURE",
            subjectHash = userId.toString().sha256(),
            requestedBy = requestedBy,
            timestamp   = Instant.now(),
        )
    }
}

// 개인 데이터 필드 레벨 암호화 (AES-256-GCM, KMS 키 관리)
@Converter(autoApply = false)
class PersonalDataEncryptor(private val kms: KmsClient) : AttributeConverter<String?, String?> {
    override fun convertToDatabaseColumn(attribute: String?): String? =
        attribute?.let { kms.encrypt(it) }
    override fun convertToEntityAttribute(dbData: String?): String? =
        dbData?.let { kms.decrypt(it) }
}

@Entity
class UserProfile(
    @Convert(converter = PersonalDataEncryptor::class)
    val phoneNumber: String?,   // DB에는 암호문 저장
)
```

**관련 패턴**: security-data-protection.md, Least Privilege, compliance.md#HIPAA

---

## 2. CCPA / CPRA (California Consumer Privacy Act / California Privacy Rights Act)

**목적**: 캘리포니아 거주자에게 개인정보 관련 권리를 부여하고, 영리 기업의 개인정보 판매·공유를 규제합니다 (2020년 CCPA → 2023년 CPRA로 강화).

**핵심 요구사항**:
- **Opt-out of Sale / Sharing**: "Do Not Sell or Share My Personal Information" 링크 의무 제공
- **GPC (Global Privacy Control)**: 브라우저 GPC 신호를 자동 opt-out으로 처리 (CPRA)
- **Data Subject Rights**: 알 권리(Know) · 삭제 권리(Delete) · 정정 권리(Correct, CPRA 추가) · 이동 권리(Portability) · opt-out · 차별 금지
- **Sensitive Personal Information (SPI)**: 사회보장번호·금융·건강·생체·성적 지향 등 — 사용 목적 제한 + opt-out 제공
- **Contractual Requirement**: 개인정보를 공유받는 제3자와 계약서에 CCPA 준수 조항 명시
- **Opt-in for Minors**: 16세 미만은 판매에 opt-in 동의 필요 (13세 미만은 부모 동의)
- **Enforcement**: California Privacy Protection Agency (CPPA) — 위반 시 $2,500(비의도적) / $7,500(의도적)

**코드·시스템 영향**:
| 요구사항 | 구현 |
|---------|------|
| opt-out 기록 | `sale_opt_out` boolean + timestamp 필드 |
| GPC 감지 | HTTP 요청 `Sec-GPC: 1` 헤더 파싱 → 자동 opt-out |
| 데이터 분류 | SPI 필드 태깅, 처리 파이프라인에서 분기 |
| 삭제 요청 | GDPR 잊혀질 권리와 유사, 45일 처리 SLA |
| 데이터 카탈로그 | 수집 항목·목적·공유 대상 문서화 |

**난이도**: 중간 | **적용 빈도**: ★★★★☆ (미국 서비스 필수)

**Kotlin 예제**:
```kotlin
/**
 * CCPA — GPC 신호 감지 및 opt-out 자동 처리.
 * Sec-GPC: 1 헤더가 있으면 해당 사용자를 판매 opt-out으로 처리합니다.
 */
@Component
class GpcOptOutInterceptor(private val privacyService: PrivacyService) : HandlerInterceptor {
    override fun preHandle(request: HttpServletRequest, response: HttpServletResponse, handler: Any): Boolean {
        if (request.getHeader("Sec-GPC") == "1") {
            val userId = (SecurityContextHolder.getContext().authentication?.principal as? UserDetails)?.username
            userId?.let { privacyService.recordSaleOptOut(it, source = "GPC_HEADER") }
        }
        return true
    }
}

@Service
class PrivacyService(private val repo: PrivacyPreferenceRepository) {
    fun recordSaleOptOut(userId: String, source: String) {
        repo.upsert(
            userId     = userId,
            saleOptOut = true,
            optOutAt   = Instant.now(),
            source     = source,   // "USER_REQUEST" | "GPC_HEADER" | "MINOR_AUTO"
        )
    }

    // SPI(민감 개인정보) 파이프라인 분기 — 목적 외 사용 차단
    fun assertAllowedUse(dataCategory: DataCategory, purpose: ProcessingPurpose) {
        val sensitiveCategories = setOf(DataCategory.SSN, DataCategory.HEALTH, DataCategory.BIOMETRIC)
        if (dataCategory in sensitiveCategories && purpose !in dataCategory.allowedPurposes) {
            throw PolicyViolationException("SPI 사용 목적 제한 위반: $dataCategory for $purpose")
        }
    }
}
```

**관련 패턴**: compliance.md#GDPR, security-data-protection.md

---

## 3. PCI DSS (Payment Card Industry Data Security Standard)

**목적**: 카드 결제 데이터(Cardholder Data)를 처리·저장·전송하는 모든 조직이 준수해야 하는 보안 표준. PCI SSC(Security Standards Council)가 관리하며 Visa/Mastercard/Amex 등 카드 브랜드가 강제 적용합니다 (현재 버전: PCI DSS v4.0.1, 2024).

**핵심 12개 요구사항**:
| # | 도메인 | 핵심 통제 |
|---|--------|----------|
| 1 | 네트워크 보안 | 방화벽 + DMZ, 카드데이터 환경(CDE) 격리 |
| 2 | 기본값 변경 | 벤더 기본 비밀번호 변경, 불필요 서비스 제거 |
| 3 | CHD 보호 | PAN 저장 최소화, 저장 시 암호화(AES-256), PAN 마스킹 표시 |
| 4 | 전송 암호화 | TLS 1.2+ (1.3 권장), 취약 프로토콜 비활성화 |
| 5 | 악성코드 방어 | AV/EDR, 정기 스캔 |
| 6 | 시스템 보안 | 보안 개발 수명주기, 취약점 패치 (critical 1개월, high 3개월) |
| 7 | 접근 제한 | Least Privilege, need-to-know 원칙 |
| 8 | 인증 | MFA, 공유 계정 금지, 암호 복잡도 |
| 9 | 물리 보안 | 서버실 접근 통제, 미디어 파기 |
| 10 | 로깅/모니터링 | 모든 CDE 접근 로그, 최소 12개월 보존 |
| 11 | 취약점 테스트 | 분기 ASV 외부 스캔, 연간 침투테스트 |
| 12 | 정책 | 보안 정책 문서화, 연간 교육, IR 계획 |

**Scope Reduction — 핵심 전략**:
- **토큰화 (Tokenization)**: PAN을 irreversible token으로 대체 → token만 자체 서버에 저장, 실제 PAN은 PCI 인증 토큰 서비스(Stripe, Braintree)에 위임 → CDE 범위 최소화
- **Hosted Fields / iFrame**: 결제 UI를 외부 PCI 준수 SDK로 렌더링 → 자사 JS가 PAN에 접촉 안 함

**난이도**: 높음 | **적용 빈도**: ★★★★☆ (결제 처리 서비스)

**Kotlin 예제**:
```kotlin
/**
 * PCI DSS Req. 3 — PAN 토큰화.
 * 자사 서버에는 토큰만 저장하고, 실제 PAN은 PCI 인증 토큰 볼트에 위임합니다.
 * CDE(Card Data Environment) 범위를 최소화하여 감사 부담을 줄입니다.
 */
@Service
class PaymentTokenService(private val vault: PciTokenVaultClient) {

    // 결제 처리 — PAN 대신 토큰만 자사 DB에 저장
    fun tokenize(pan: String): String {
        require(luhnCheck(pan)) { "유효하지 않은 카드번호" }
        return vault.tokenize(pan)  // 토큰 반환, PAN은 볼트에만 존재
    }

    // PAN은 마지막 4자리만 표시 (PCI DSS Req. 3.3.1)
    fun maskPan(pan: String): String =
        "*".repeat(pan.length - 4) + pan.takeLast(4)  // ************1234

    // 로그에 PAN이 흘러나오지 않도록 MDC에 토큰만 기록
    fun chargeWithToken(token: String, amount: Long) {
        MDC.put("payment_token", token)  // PAN 절대 MDC 기록 금지
        try {
            vault.charge(token, amount)
            auditLog.record("PAYMENT_SUCCESS", token, amount)
        } finally {
            MDC.remove("payment_token")
        }
    }

    private fun luhnCheck(pan: String): Boolean {
        val digits = pan.filter { it.isDigit() }.map { it.digitToInt() }
        return digits.reversed().mapIndexed { i, d ->
            if (i % 2 == 1) (d * 2).let { if (it > 9) it - 9 else it } else d
        }.sum() % 10 == 0
    }
}

// Req. 10 — CDE 접근 감사 로그 (최소 12개월 보존)
@Entity
@Table(name = "cde_access_log")
data class CdeAccessLog(
    @Id val id: UUID = UUID.randomUUID(),
    val userId: String,
    val action: String,        // "TOKENIZE" | "CHARGE" | "REFUND"
    val tokenRef: String,      // PAN 아님 — 토큰 참조
    val ipAddress: String,
    val timestamp: Instant = Instant.now(),
    val retentionExpiry: Instant = Instant.now().plus(365, ChronoUnit.DAYS),  // 12개월
)
```

**관련 패턴**: security-data-protection.md, security-crypto-ops.md, security-detect-respond.md

---

## 4. HIPAA (Health Insurance Portability and Accountability Act, US 1996)

**목적**: 미국에서 PHI(Protected Health Information, 보호 건강 정보)를 처리하는 의료 기관·비즈니스 파트너의 보안·개인정보 보호 요건을 규정합니다.

**핵심 개념**:
- **PHI (Protected Health Information)**: 개인 식별 가능한 18개 식별자(Safe Harbor) 중 하나라도 포함된 건강 정보
  - 이름·주소·날짜(생년월일 제외 가능)·전화·이메일·SSN·의무기록번호·IP주소·생체정보 등
- **Covered Entity**: 병원, 클리닉, 보험사, 의료 데이터 교환소
- **Business Associate (BA)**: PHI를 처리하는 IT 서비스·클라우드 공급자
- **BAA (Business Associate Agreement)**: BA와 반드시 체결해야 하는 계약 (PHI 보호 의무 위임)
- **Safe Harbor De-identification**: 18개 식별자 모두 제거 → 더 이상 PHI 아님, HIPAA 적용 제외

**Privacy Rule vs Security Rule**:
| 규칙 | 범위 | 핵심 통제 |
|------|------|----------|
| Privacy Rule | 모든 PHI (종이 포함) | 사용·공개 제한, 환자 권리 (접근·정정·공개 제한) |
| Security Rule | 전자 PHI (ePHI) | 관리적·물리적·기술적 세이프가드 |
| Breach Notification Rule | 침해 발생 시 | 60일 내 환자 통지, 500명 이상 시 즉시 HHS 신고 |

**기술적 세이프가드 (Security Rule)**:
- 접근 통제: 고유 사용자 ID, 자동 로그오프, 암호화/복호화
- 감사 로그: ePHI에 대한 모든 접근 기록
- 무결성 통제: 전송/저장 중 ePHI 위변조 탐지
- 전송 보안: TLS 암호화

**난이도**: 높음 | **적용 빈도**: ★★★☆☆ (미국 의료/헬스테크)

**Kotlin 예제**:
```kotlin
/**
 * HIPAA Security Rule — ePHI 접근 감사 로그 + 자동 로그오프.
 * 모든 PHI 조회/수정은 감사 추적을 남겨야 합니다.
 */
@Aspect
@Component
class PhiAccessAuditAspect(private val auditRepo: PhiAuditRepository) {

    // PHI 데이터 접근 메서드에 @PhiAccess 애노테이션 → 자동 감사 로그
    @Around("@annotation(phiAccess)")
    fun auditPhiAccess(pjp: ProceedingJoinPoint, phiAccess: PhiAccess): Any? {
        val user = SecurityContextHolder.getContext().authentication?.name ?: "ANONYMOUS"
        val startTime = Instant.now()
        return try {
            val result = pjp.proceed()
            auditRepo.save(PhiAuditEntry(
                userId       = user,
                action       = phiAccess.action,
                resourceType = phiAccess.resource,
                timestamp    = startTime,
                outcome      = "SUCCESS",
                ipAddress    = RequestContextHolder.currentRequestAttributes()
                                   .let { (it as? ServletRequestAttributes)?.request?.remoteAddr ?: "unknown" },
            ))
            result
        } catch (ex: Exception) {
            auditRepo.save(PhiAuditEntry(
                userId = user, action = phiAccess.action, resourceType = phiAccess.resource,
                timestamp = startTime, outcome = "FAILURE", errorCode = ex.javaClass.simpleName,
            ))
            throw ex
        }
    }
}

@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
annotation class PhiAccess(val action: String, val resource: String)

// 사용 예
@Service
class PatientRecordService(private val repo: PatientRecordRepository) {
    @PhiAccess(action = "READ", resource = "PATIENT_RECORD")
    fun getRecord(patientId: UUID): PatientRecord = repo.findById(patientId)

    // Safe Harbor — 18개 식별자 제거 후 연구용 데이터 제공
    @PhiAccess(action = "DEIDENTIFY", resource = "PATIENT_RECORD")
    fun getDeidentified(patientId: UUID): AnonymizedRecord {
        val record = repo.findById(patientId)
        return AnonymizedRecord(
            // 이름, 주소, 날짜, 전화, 이메일, SSN 등 18개 식별자 모두 제거
            diagnosisCode = record.diagnosisCode,
            ageRange      = record.age.let { when { it < 30 -> "<30"; it < 50 -> "30-49"; else -> "50+" } },
            // 기타 임상 데이터만 유지
        )
    }
}
```

**관련 패턴**: compliance.md#GDPR, security-data-protection.md, security-detect-respond.md

---

## 5. SOC 2 (Service Organization Control 2, AICPA)

**목적**: 서비스 조직이 고객 데이터를 안전하게 관리함을 독립 감사인이 검증하는 인증 프레임워크. SaaS B2B 거래에서 사실상 필수 신뢰 증명입니다 (AICPA TSC, Trust Service Criteria).

**Trust Service Criteria (TSC) — 5개 영역**:
| 영역 | 약자 | 핵심 내용 |
|------|------|----------|
| Security (보안) | CC | 모든 SOC 2에 필수. 접근 통제·암호화·취약점 관리·인시던트 대응 |
| Availability (가용성) | A | SLA, 장애 대응, 백업/복구 |
| Processing Integrity (처리 무결성) | PI | 데이터 처리 완전성·정확성·적시성 |
| Confidentiality (기밀성) | C | 기밀 데이터 식별·보호·파기 |
| Privacy (개인정보) | P | AICPA 개인정보 원칙 (GDPR/CCPA 매핑 가능) |

**Type I vs Type II**:
| 구분 | 검증 내용 | 기간 |
|------|----------|------|
| Type I | 특정 시점의 통제 설계 적절성 | 단일 시점 |
| Type II | 통제가 실제로 운영됨 (효과성) | **최소 6개월** (12개월 권장) |

> B2B 고객은 대부분 **Type II**를 요구합니다.

**Security (CC) 주요 통제**:
- CC6.1: 논리적 접근 통제 (MFA, 최소 권한)
- CC6.2: 인증 요소 관리 (비밀번호 정책)
- CC6.3: 접근 권한 프로비저닝/디프로비저닝 프로세스
- CC7.1: 취약점 탐지 (ASV 스캔, SAST/DAST)
- CC7.2: 모니터링/경보
- CC9.2: 벤더/공급망 리스크 관리

**코드·시스템 영향**:
| TSC 통제 | 구현 |
|---------|------|
| CC6.1 MFA | TOTP/WebAuthn 강제, 예외 없음 |
| CC6.3 온보딩/오프보딩 | IAM 자동화 (Terraform, SCIM) |
| CC7.1 취약점 | CI/CD SAST(Semgrep), SCA(Dependabot), 이미지 스캔 |
| CC7.2 모니터링 | SIEM 알림, 비정상 접근 탐지 |
| A1 가용성 | 99.9% SLA 대시보드, RTO/RPO 문서 |
| C1 기밀성 | 데이터 분류 정책, DLP |

**난이도**: 높음 | **적용 빈도**: ★★★★☆ (B2B SaaS)

**Kotlin 예제**:
```kotlin
/**
 * SOC 2 CC6.3 — 사용자 접근 권한 자동 프로비저닝/디프로비저닝.
 * 퇴직/부서 이동 시 즉시 권한 회수, 감사 추적 유지.
 */
@Service
class AccessLifecycleService(
    private val iamClient: IamClient,
    private val auditLog: ComplianceAuditLog,
    private val notifier: SecurityNotifier,
) {
    // CC6.3 — 계정 디프로비저닝 (퇴직/계약 종료)
    fun deprovision(userId: String, reason: DeprovisionReason) {
        // 1. 즉시 세션 무효화
        iamClient.revokeAllSessions(userId)

        // 2. 모든 접근 권한 회수
        val revokedRoles = iamClient.listRoles(userId)
        iamClient.revokeAllRoles(userId)

        // 3. API 키 비활성화
        val revokedKeys = iamClient.listApiKeys(userId).also { keys ->
            keys.forEach { iamClient.revokeApiKey(it.id) }
        }

        // 4. 감사 기록 (SOC 2 감사인 제출용)
        auditLog.record(AccessAuditEvent(
            eventType     = "USER_DEPROVISIONED",
            userId        = userId,
            reason        = reason.name,
            revokedRoles  = revokedRoles.map { it.name },
            revokedKeyIds = revokedKeys.map { it.id },
            performedBy   = SecurityContextHolder.getContext().authentication?.name ?: "SYSTEM",
            timestamp     = Instant.now(),
        ))

        // 5. Security 팀 통지 (CC7.2)
        if (reason == DeprovisionReason.TERMINATION) {
            notifier.alertSecurityTeam("즉시 디프로비저닝 완료: $userId")
        }
    }

    // CC6.1 — 분기 접근 권한 리뷰 (Access Review)
    @Scheduled(cron = "0 0 9 1 */3 *")  // 분기 1회 월요일 09:00
    fun quarterlyAccessReview() {
        val usersWithExcessiveAccess = iamClient.findUsersExceedingLeastPrivilege()
        usersWithExcessiveAccess.forEach { user ->
            auditLog.record(AccessAuditEvent(
                eventType = "ACCESS_REVIEW_FINDING",
                userId    = user.id,
                finding   = "Excess privilege: ${user.unusedRoles}",
                timestamp = Instant.now(),
            ))
        }
        notifier.sendAccessReviewReport(usersWithExcessiveAccess)
    }
}

enum class DeprovisionReason { TERMINATION, CONTRACT_END, ROLE_CHANGE, SECURITY_INCIDENT }
```

**관련 패턴**: Least Privilege, security-detect-respond.md, security-sdlc.md, compliance.md#GDPR

---
