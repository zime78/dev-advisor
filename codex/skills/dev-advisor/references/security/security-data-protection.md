# 데이터 보호 패턴 (Data Protection & Privacy Engineering)

저장(at rest) / 전송(in transit) / 처리(in use) 세 가지 상태에 걸친 민감 데이터 보호를 운영 / 아키텍처 레벨에서 다루는 패턴 모음. AES-GCM, RSA-OAEP 같은 cryptographic primitive 자체는 `algorithms/crypto.md` 에서 다루며, 본 문서는 **그 primitive 를 시스템에 어떻게 배치 · 운영 · 통합하는가** 라는 패턴 측면에 집중한다. 규제 기반: GDPR(EU 2016/679), PCI DSS v4.0, HIPAA, NIST SP 800-38G(FPE), NIST SP 800-188(De-identification), ISO/IEC 27018, Confidential Computing Consortium 정의.

---

## 1. Encryption at Rest (저장 데이터 암호화)

**목적**: 디스크 / DB / 백업 매체가 물리적으로 탈취되었을 때 평문 노출을 막기 위해 저장 계층에서 데이터를 암호화합니다. 키 관리(KMS / HSM)와 분리하여 "탈취된 매체 + 분리된 키" 모델을 강제합니다.

**특징**:
- 적용 계층 3 종: ① Disk-level (LUKS, BitLocker, FileVault, AWS EBS) ② Filesystem-level (eCryptfs, ZFS native encryption) ③ DB-level (TDE — Transparent Data Encryption)
- TDE: 페이지 / 테이블스페이스 단위 AES 암호화 — 애플리케이션 코드 변경 0
- Envelope encryption: DEK(Data Encryption Key) → KEK(Key Encryption Key in KMS) 2-tier 구조가 표준
- MongoDB / SQL Server / Oracle / PostgreSQL(pgcrypto/cybertec TDE) 지원
- 키 rotation 은 KEK 만 회전, DEK 재암호화는 lazy

**장점**:
- 물리 탈취 / 폐기 매체 누출 시 데이터 보호 (PCI DSS Req. 3.5, HIPAA §164.312(a)(2)(iv) 충족)
- 애플리케이션 투명 — 코드 변경 없이 적용 가능
- 백업 / 스냅샷이 자동으로 암호화 상속

**단점**:
- **메모리 / DB session 안에서는 평문** — SQL injection, 권한 상승, 메모리 덤프 공격에는 무력
- I/O 성능 5~15% 저하 (AES-NI 가속 시 무시할 수준)
- 키 분실 시 데이터 영구 손실 — KMS 가용성이 곧 데이터 가용성

**활용 예시**:
- AWS RDS / Azure SQL TDE 자동 활성화
- 사내 노트북 FileVault / BitLocker 의무화
- Backup volume LUKS 암호화 후 오프사이트 보관
- Kubernetes etcd encryption-at-rest (`EncryptionConfiguration`)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// AWS KMS Envelope Encryption — DEK 생성 후 평문 데이터를 AES-GCM 으로 암호화하고,
// DEK 자체는 KEK 으로 wrap 하여 함께 저장한다.
class EnvelopeEncryptor(private val kms: KmsClient, private val kekId: String) {

    fun encrypt(plaintext: ByteArray): EncryptedPayload {
        // 1) KMS 에 DEK 발급 요청 — 평문 DEK + KEK 으로 wrap 된 ciphertext DEK 동시 반환
        val dekResp = kms.generateDataKey {
            it.keyId(kekId).keySpec(DataKeySpec.AES_256)
        }
        val plaintextDek = dekResp.plaintext().asByteArray()
        val wrappedDek = dekResp.ciphertextBlob().asByteArray()

        // 2) 평문 DEK 로 데이터 AES-GCM 암호화 (12B IV, 16B tag)
        val iv = SecureRandom.getInstanceStrong().generateSeed(12)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
            init(Cipher.ENCRYPT_MODE, SecretKeySpec(plaintextDek, "AES"), GCMParameterSpec(128, iv))
        }
        val ciphertext = cipher.doFinal(plaintext)

        // 3) 메모리에서 평문 DEK 즉시 폐기 (Java 9+ Arrays.fill)
        Arrays.fill(plaintextDek, 0.toByte())

        // wrappedDek + iv + ciphertext 묶음을 디스크 / DB 컬럼에 저장
        return EncryptedPayload(wrappedDek, iv, ciphertext)
    }
}
```

**관련 패턴**: Field-level Encryption, Tokenization, Key Rotation, Envelope Encryption

---

## 2. Field-level Encryption (필드 단위 암호화)

**목적**: 전체 row 가 아닌 특정 컬럼(SSN, 주민번호, 카드번호, 이메일) 만 암호화하여 DB 접근 권한자라도 평문을 볼 수 없게 합니다. TDE 가 막지 못하는 "DB 관리자 / SQL injection" 위협 모델을 보완합니다.

**특징**:
- 클라이언트 측 암호화(Client-Side Field-Level Encryption, CSFLE) — 키가 애플리케이션에만 존재, DB 서버는 ciphertext 만 봄
- MongoDB CSFLE, AWS DynamoDB Encryption Client, Google Tink AEAD 가 표준 구현
- Deterministic encryption: 같은 평문 → 같은 ciphertext (등호 검색 가능, 단 frequency leakage)
- Randomized encryption: 보안 강하지만 검색 불가
- Searchable Symmetric Encryption (SSE) / Order-Preserving Encryption (OPE) 은 강한 leakage 존재 — CryptDB 공격 사례로 production 권장 X

**장점**:
- DB 관리자 / DBA 도 평문 접근 불가 (separation of duty)
- SQL injection 으로 dump 떠도 ciphertext 만 노출
- 컬럼별 다른 키 적용 가능 → blast radius 축소

**단점**:
- 검색 / 정렬 / JOIN / LIKE 가 ciphertext 위에선 불가능 (deterministic 만 equality 지원)
- 인덱스 효율 저하 — randomized 컬럼은 사실상 인덱싱 무의미
- 키 분실 시 해당 컬럼 영구 손실, 키 회전 비용 큼

**활용 예시**:
- MongoDB CSFLE — 의료 기록 PHI 필드 암호화 (HIPAA)
- AWS DynamoDB Encryption Client — 금융 거래 ID 컬럼
- 결제 시스템 PAN(Primary Account Number) 컬럼 보호 (PCI DSS Req. 3.4)
- 이메일 deterministic 암호화 후 등호 검색 허용, 노출 표면은 hash 로 대체

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Google Tink — AEAD 로 randomized field-level encryption
object FieldEncryptor {
    init { AeadConfig.register() }

    private val keysetHandle: KeysetHandle = KeysetHandle.read(
        JsonKeysetReader.withFile(File("/etc/keys/user_pii.json")),
        Aead::class.java.let { AwsKmsClient.getAead("aws-kms://arn:aws:kms:...") }
    )
    private val aead: Aead = keysetHandle.getPrimitive(Aead::class.java)

    // Associated Data (AAD) 로 row id 를 묶어 ciphertext copy-paste 공격 방지
    fun encryptSSN(ssn: String, userId: Long): ByteArray =
        aead.encrypt(ssn.toByteArray(Charsets.UTF_8), userId.toString().toByteArray())

    fun decryptSSN(ciphertext: ByteArray, userId: Long): String =
        String(aead.decrypt(ciphertext, userId.toString().toByteArray()), Charsets.UTF_8)
}
// 검색이 필요한 이메일은 별도로 HMAC-SHA256(email) 컬럼을 추가하여 deterministic lookup
```

**관련 패턴**: Tokenization, Format-Preserving Encryption, Envelope Encryption, Searchable Encryption(주의)

---

## 3. Tokenization (토큰화)

**목적**: 민감 데이터(카드번호, 주민번호)를 **수학적으로 무관한** 토큰으로 치환하고, 원본은 **token vault** 라는 격리된 안전 저장소에만 보관합니다. PCI DSS 가 카드 데이터 환경(CDE) 축소 수단으로 권장하는 1차 통제입니다.

**특징**:
- 암호학적 변환이 아니라 **임의 매핑**(random token + 1:1 lookup) — 키만으로 복원 불가, vault 가 있어야 복원
- Format-preserving 변형 가능 (e.g. 16자리 카드번호 → 16자리 토큰)
- Vault 는 격리된 micro-segment / HSM 백업 / strict RBAC + dual control
- PCI DSS scope 축소 효과 — 토큰만 다루는 시스템은 CDE 에서 제외 가능
- Stripe, Adyen, Braintree, AWS Payment Cryptography 가 PSP 토큰화 제공

**장점**:
- Vault 가 침해되지 않으면 토큰 자체로는 가치 0 (irreversible without vault)
- 컴플라이언스 scope 축소 → 감사 비용 절감
- 키 관리 부담이 vault 한 곳으로 집중

**단점**:
- Vault 자체가 SPOF / honeypot — 다중화 + DR 필수
- Vault round-trip 으로 latency 증가
- Token 검색 / 분석 시 매번 vault 호출 또는 token 자체에 통계 메타데이터 leakage 위험

**활용 예시**:
- 결제 시스템 — Stripe `tok_xxx`, Apple Pay DPAN(Device PAN)
- 사내 BI / 분석 환경에 주민번호 토큰만 전달, 원본은 vault 에 남김
- Salesforce Shield Platform Encryption tokenization
- 의료 EHR 시스템의 patient identifier 분리

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// 사내 Token Vault 클라이언트 — vault 는 별도 micro-service + HSM
interface TokenVault {
    fun tokenize(plaintext: String, dataType: DataType): String   // → "tok_4f8a92..."
    fun detokenize(token: String, callerId: String): String       // 권한 + 감사 로그 필수
}

class CardProcessor(private val vault: TokenVault, private val psp: PspClient) {

    fun authorize(card: String, amount: Money): AuthResult {
        // 1) 카드번호는 즉시 토큰화하고 메모리에서 제거
        val token = vault.tokenize(card, DataType.PAN)
        memset(card)  // String 은 immutable 이라 실제로는 CharArray 권장

        // 2) 이후 시스템은 token 만 사용 — 원장 / 로그 / 분석 DB 모두 token 저장
        ledger.recordPending(token, amount)

        // 3) PSP 호출 직전에만 vault 에서 detokenize, 호출 후 즉시 폐기
        val pan = vault.detokenize(token, callerId = "payment-service")
        return try {
            psp.authorize(pan, amount)
        } finally {
            memset(pan)
        }
    }
}
```

**관련 패턴**: Field-level Encryption, Format-Preserving Encryption, Vault (HashiCorp), PCI DSS scope reduction

---

## 4. Format-Preserving Encryption (FPE)

**목적**: 평문의 길이와 문자 집합(domain) 을 그대로 유지하면서 암호화합니다. 16자리 카드번호 → 16자리 숫자 ciphertext. 기존 DB 스키마(CHAR(16))나 레거시 시스템 입력 검증을 깨지 않고 암호화를 도입할 수 있습니다.

**특징**:
- NIST SP 800-38G 표준: **FF1** (Feistel structure, 가변 도메인), **FF3-1** (FF3 의 취약점 패치 버전)
- FF2 / FF3 원본은 취약점 발견 후 사용 금지 (2017 Durak-Vaudenay 공격)
- AES 를 round function 으로 사용하는 Feistel 네트워크
- Tweak 값(non-secret context, e.g. row id)으로 같은 평문 → 다른 ciphertext 보장
- Voltage SecureData / Thales CipherTrust / AWS Payment Cryptography 제공
- **Tokenization 과 차이**: vault 불필요 — 키만 있으면 복원 가능. 단, 강한 cryptographic guarantee.

**장점**:
- 레거시 시스템 / 컬럼 길이 제약 그대로 — 마이그레이션 비용 최소
- Vault round-trip 불필요 — stateless, 분산 가능
- 카드번호 마지막 4자리 보존(4-12-4 split) 가능 → 사용자 식별 UX 유지

**단점**:
- 도메인이 작으면(<2^20) 보안 마진 감소 — 권장 도메인 크기 명세 필요
- 구현 복잡도 높음 — 자체 구현 금지, 인증 라이브러리 필수
- Authenticated encryption 아님 — tag 별도 보호 필요

**활용 예시**:
- 카드번호 16자리 중 처음 6 + 마지막 4 평문 유지, 가운데 6자리만 FPE 암호화 → "411111-XXXXXX-1111"
- 주민번호 형식 보존 암호화 후 기존 13자리 DB 컬럼 재사용
- 의료보험 ID, 사번 등 fixed-format identifier 의 in-place 암호화
- 데이터 마스킹과 결합 — 실제 운영은 FPE, 비프로덕션은 결정적 마스킹

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// Bouncy Castle FPE FF1 (AES-256 기반)
class CardNumberFpe(masterKey: ByteArray) {
    private val engine = FPEFF1Engine(AESEngine())
    private val key = KeyParameter(masterKey)
    // 도메인: 숫자 0-9, radix = 10
    private val radix = 10

    /**
     * 카드번호의 가운데 6자리만 FPE 암호화 — BIN(6) 과 last4 는 평문 보존.
     * @param tweak row id 등 non-secret context (같은 평문 → 다른 ciphertext)
     */
    fun encrypt(card: String, tweak: ByteArray): String {
        require(card.length == 16 && card.all(Char::isDigit))
        val bin = card.substring(0, 6)
        val last4 = card.substring(12, 16)
        val middle = card.substring(6, 12).map { Character.digit(it, 10).toByte() }.toByteArray()

        val out = ByteArray(middle.size)
        engine.init(true, FPEParameters(key, radix, tweak))
        engine.processBlock(middle, 0, middle.size, out, 0)

        val enc = out.joinToString("") { it.toString() }
        return "$bin$enc$last4"   // 길이 16 유지, 숫자만 유지 → 레거시 스키마 호환
    }
}
```

**관련 패턴**: Tokenization, Field-level Encryption, Data Masking, AES-NI

---

## 5. Data Masking (데이터 마스킹)

**목적**: 운영 데이터를 비프로덕션 환경(개발 / QA / 분석) 으로 복제할 때 민감 필드를 **비복원 가능한 대체값**으로 치환합니다. 개발자 / 분석가가 실 데이터 없이도 사실에 가까운 데이터로 작업하게 합니다.

**특징**:
- **정적 마스킹(Static Data Masking, SDM)**: ETL 시점에 영구 치환 — 비프로덕션 DB 자체가 마스킹된 상태
- **동적 마스킹(Dynamic Data Masking, DDM)**: 쿼리 시점에 권한 기반 redaction — DB 원본은 평문, view 가 마스킹
- 마스킹 기법: 문자 치환(`123-45-6789` → `XXX-XX-6789`), 셔플링, 평균 대체, 합성 데이터 생성
- 참조 무결성 유지 필수 — userId FK 가 마스킹 후에도 동일하게 매핑되어야 JOIN 동작
- Delphix / Informatica / Oracle DDM / SQL Server Dynamic Data Masking 제공

**장점**:
- 개발 / 분석 환경에서 실 데이터 노출 차단 — GDPR Art. 32 안전 조치 인정
- 운영 DB 의 부하 / 위험 없이 사실적 테스트 데이터 확보
- DDM 은 애플리케이션 코드 변경 0

**단점**:
- DDM 은 우회 가능 (`WHERE` clause inference attack) — 강한 보호 아님, 권장은 SDM
- 참조 무결성 유지 비용 — 분산된 시스템 간 일관된 마스킹 매핑 필요
- 합성 데이터는 ML 모델 학습 시 통계 분포 왜곡 가능

**활용 예시**:
- 운영 DB → 개발 환경 sanitized snapshot 매주 갱신
- 분석가에게 이메일 도메인만 남기고 local part 마스킹 (`xxxx@kakaovx.com`)
- 사용자 화면에서 권한 없으면 `010-XXXX-1234` 동적 마스킹
- HIPAA Safe Harbor 18개 식별자 제거 후 연구용 dataset 배포

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// 정적 마스킹 — 운영 dump → dev DB ETL pipeline
object StaticMasker {

    // 참조 무결성 유지: 같은 email 은 항상 같은 가짜 email 로 매핑
    private val emailMap = ConcurrentHashMap<String, String>()
    private val faker = Faker()

    fun maskEmail(email: String): String = emailMap.computeIfAbsent(email) {
        "${faker.name().username()}@example.test"
    }

    fun maskPhone(phone: String): String = phone.replaceFirst(
        Regex("""(\d{3})-?(\d{4})-?(\d{4})"""), "$1-XXXX-$3"
    )

    fun maskSSN(ssn: String): String = ssn.replaceFirst(
        Regex("""(\d{6})-?(\d{7})"""), "$1-XXXXXXX"
    )
}

// 동적 마스킹 — Spring AOP 로 권한 기반 redaction
@Aspect
@Component
class DynamicMaskingAspect {
    @AfterReturning(pointcut = "@annotation(Maskable)", returning = "user")
    fun mask(user: UserDto) {
        if (!SecurityContextHolder.getContext().authentication.hasRole("PII_READ")) {
            user.phone = StaticMasker.maskPhone(user.phone)
            user.ssn = StaticMasker.maskSSN(user.ssn)
        }
    }
}
```

**관련 패턴**: Pseudonymization, Tokenization, Synthetic Data Generation, RBAC

---

## 6. Pseudonymization (가명처리)

**목적**: 개인 식별자를 **추가 정보 없이는 특정 개인을 식별할 수 없는 가명**으로 대체합니다. GDPR Article 4(5) 의 공식 정의에 부합하며, 데이터 보호 의무를 완화하는(Art. 25 / Art. 32) 핵심 기법입니다.

**특징**:
- **Reversible (가역)**: 키 / 매핑 테이블로 원본 복원 가능 — tokenization 이 한 사례
- **Irreversible (비가역)**: 일방향 함수(HMAC, salted hash) — 추가 정보 없이 복원 불가
- 익명화(anonymization) 와 구분 — 가명처리는 여전히 "개인정보" 로 간주(GDPR), 추가 정보가 분리 보관됨이 핵심
- 통계적 보장 기법: **k-anonymity** (각 record 가 최소 k-1 개와 quasi-identifier 동일), **l-diversity** (민감 속성 다양성), **t-closeness**
- ARX, Amnesia, sdcMicro 가 학술 / 의료 dataset 비식별화 도구

**장점**:
- GDPR 준수 입증 핵심 안전 조치 (Art. 32(1)(a))
- 익명화보다 데이터 유용성 보존 (분석 / ML 학습 가능)
- 비가역 가명은 데이터 유출 시에도 재식별 어려움

**단점**:
- 외부 dataset 결합 시 재식별 위험(Netflix Prize 사례) — quasi-identifier 통제 필수
- k-anonymity 만으로는 동질성 공격(homogeneity attack) 방어 불가 → l-diversity 보강 필요
- 통계 분포 왜곡 가능 — 분석 정확도 trade-off

**활용 예시**:
- 의료 연구용 EHR dataset — patient ID 를 HMAC-SHA256(salt, id) 로 가명화
- 광고 식별자 — Apple IDFA / Google AAID 가 비가역 가명
- A/B 테스트 분석 — user_id 를 salted hash 로 치환 후 데이터 팀에 전달
- 로그 수집 — 이메일 / IP 가명화 후 SIEM 적재

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// GDPR 호환 비가역 가명처리 + k-anonymity 검증
object Pseudonymizer {
    private val mac = Mac.getInstance("HmacSHA256").apply {
        // pepper 는 별도 KMS 보관 — 분리 보관 원칙 (GDPR Art. 4(5))
        init(SecretKeySpec(System.getenv("PSEUDO_PEPPER").toByteArray(), "HmacSHA256"))
    }

    fun pseudonymize(identifier: String): String =
        Base64.getUrlEncoder().withoutPadding().encodeToString(
            mac.doFinal(identifier.toByteArray(Charsets.UTF_8))
        )
}

// k-anonymity 검증 — quasi-identifier(나이대 / 우편번호 앞3자리 / 성별) 조합이
// 최소 k 개 row 와 동일해야 출력 허용
fun enforceKAnonymity(rows: List<Row>, k: Int = 5): List<Row> {
    val grouped = rows.groupBy { Triple(it.ageBand, it.zip3, it.gender) }
    return grouped.filter { it.value.size >= k }.values.flatten()
}
```

**관련 패턴**: Tokenization, Data Masking, Differential Privacy, k-anonymity / l-diversity

---

## 7. Differential Privacy (차분 프라이버시)

**목적**: 통계 쿼리 / ML 학습 결과에 수학적으로 보정된 노이즈를 주입하여, **개별 record 가 dataset 에 포함되었는지 여부를 통계적으로 구분할 수 없도록** 보장합니다. ε(epsilon) 으로 privacy budget 을 정량화하는 유일한 기법입니다.

**특징**:
- 정의(Dwork 2006): 인접 dataset D, D′(한 record 만 다름) 에 대해 임의의 출력 집합 S 가 `Pr[M(D)∈S] ≤ exp(ε) · Pr[M(D′)∈S]`
- ε 값: 0.1~1 (강한 보호) / 1~10 (약한 보호) — Apple 은 ε=2~8 사용
- 노이즈 메커니즘: **Laplace** (count / sum 같은 numeric query), **Gaussian** (vector / ML gradient), **Exponential** (선택형 출력)
- **Local DP**: 클라이언트에서 노이즈 추가 후 서버로 전송 (Apple iOS 텔레메트리, Google RAPPOR)
- **Central DP**: 서버에서 신뢰 후 집계 결과에 노이즈 (US Census 2020)
- ML 학습용 DP-SGD (Abadi et al. 2016) — gradient 에 Gaussian 노이즈 + clipping
- OpenDP, TensorFlow Privacy, PyTorch Opacus, IBM diffprivlib 라이브러리

**장점**:
- 수학적으로 증명된 privacy guarantee — 사후 정보 결합에도 robust
- 재식별 / 멤버십 추론 공격(Membership Inference) 방어
- Privacy budget 으로 reuse 정량 관리 가능

**단점**:
- 정확도 ↔ 프라이버시 trade-off 명확 — 작은 dataset 에선 노이즈 비율 큼
- ε 선택의 정답 없음, 도메인 expertise 필요
- 구현 미세 버그가 보장 무력화 — 검증된 라이브러리 필수

**활용 예시**:
- Apple iOS 키보드 / 이모지 / Safari 텔레메트리 (Local DP)
- Google Chrome RAPPOR — 홈페이지 분포 수집
- US Census 2020 — 인구 통계 공개에 DP 적용
- DP-SGD 로 의료 영상 학습 — 환자 정보 보호 + 공유 모델

**난이도**: 매우 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// Laplace 메커니즘 — count query 에 ε-DP 적용
class DifferentiallyPrivateCount(private val epsilon: Double) {
    private val random = SecureRandom.getInstanceStrong()

    /**
     * Sensitivity = 1 (한 record 추가/삭제로 count 가 최대 1 변동).
     * 노이즈 = Laplace(0, sensitivity/ε)
     */
    fun noisyCount(trueCount: Long): Long {
        val scale = 1.0 / epsilon
        val u = random.nextDouble() - 0.5
        val noise = -scale * Math.signum(u) * Math.log(1 - 2 * Math.abs(u))
        return (trueCount + noise).roundToLong().coerceAtLeast(0)
    }
}

// Privacy budget tracker — 동일 dataset 에 ε 누적 소비 추적
class PrivacyBudget(private val total: Double) {
    private var consumed = 0.0
    @Synchronized
    fun spend(epsilon: Double): Boolean {
        if (consumed + epsilon > total) return false  // budget 초과 시 쿼리 거부
        consumed += epsilon
        return true
    }
}

// 사용 예: ε=1.0 으로 1주일 budget, 각 쿼리 ε=0.1 소비 → 최대 10회
val budget = PrivacyBudget(total = 1.0)
val dp = DifferentiallyPrivateCount(epsilon = 0.1)
if (budget.spend(0.1)) println(dp.noisyCount(activeUsers))
```

**관련 패턴**: Pseudonymization, k-anonymity, Federated Learning, DP-SGD

---

## 8. Confidential Computing (기밀 컴퓨팅)

**목적**: 데이터가 **사용 중(in use)** 인 상태, 즉 메모리에 평문으로 로드된 시점에도 OS / hypervisor / 클라우드 운영자 / co-tenant 로부터 격리합니다. TEE(Trusted Execution Environment) 하드웨어 + remote attestation 으로 신뢰 경계를 CPU 패키지 안쪽으로 옮깁니다.

**특징**:
- Confidential Computing Consortium(2019, Linux Foundation) 표준화
- 하드웨어 TEE 4 종:
  - **Intel SGX**: 프로세스 단위 enclave, 메모리 작음(EPC 256MB~512GB), 세분화된 격리
  - **Intel TDX**: VM 단위 enclave (Trust Domain) — VM 전체 캡슐화, 마이그레이션 부담 적음
  - **AMD SEV-SNP**: VM 메모리 암호화 + integrity (Secure Encrypted Virtualization)
  - **Arm CCA**: Realms — Arm v9 confidential VM
- **AWS Nitro Enclaves**: Nitro hypervisor 가 격리, vsock 으로만 통신 (네트워크/디스크/대화형 접근 차단)
- **Remote Attestation**: enclave 가 자신의 measurement(코드 hash) + 플랫폼 상태를 서명 → 검증자가 KMS 키 release 결정
- Google Confidential VM, Azure Confidential Computing, AWS Nitro Enclaves, Microsoft Open Enclave SDK

**장점**:
- 클라우드 운영자 / hypervisor / 권한 상승 공격에서도 메모리 평문 보호
- Multi-party computation — 서로 데이터 노출 없이 공동 분석 가능
- 키 release 가 enclave attestation 에 묶임 → 유출 시에도 다른 환경에서 복호화 불가

**단점**:
- 하드웨어 종속 + 성능 오버헤드 (SGX page swap, SEV memory encryption ~5~15%)
- Side-channel 공격 이력 (SGX: Foreshadow, ÆPIC Leak / SEV: SEV-ES bypass) — 모델은 강력하지만 완벽하지 않음
- Enclave 코드 검증 / 빌드 reproducibility 부담
- 디버깅 / 관찰 가능성 제한

**활용 예시**:
- 은행 간 자금세탁 탐지 협업 — 서로의 거래 데이터를 SGX enclave 에 결합
- AWS Nitro Enclaves 로 KMS key material 격리 + attestation 기반 release
- 의료 다기관 ML — 환자 데이터 노출 없이 enclave 내부에서 federated 학습
- Signal Contact Discovery (SGX) — 서버가 사용자 연락처를 평문으로 보지 못함
- Web3 / blockchain — oracle 의 confidential 외부 데이터 fetch

**난이도**: 매우 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// AWS Nitro Enclaves — parent EC2 에서 enclave 로 vsock 으로 데이터 전송 후
// enclave attestation document 를 KMS 에 제출하여 키 release 받는 흐름
class NitroEnclaveClient(private val cid: Int, private val port: Int) {

    fun decryptInEnclave(ciphertext: ByteArray, kmsKeyId: String): ByteArray {
        // 1) vsock 연결 — 일반 네트워크 / 디스크 / SSH 접근 불가능한 격리 채널
        val socket = VsockSocket(cid, port)

        // 2) Enclave 내부에서 자체 attestation document 생성
        //    measurement (PCR0=enclave image hash, PCR1=kernel, PCR2=app) 포함
        val request = AttestationRequest(
            ciphertext = ciphertext,
            kmsKeyId = kmsKeyId,
            // KMS 는 attestation 의 PCR 값을 정책과 비교 → 일치 시에만 plaintext key release
            attestationDoc = socket.requestAttestation()
        )
        socket.send(request)

        // 3) Enclave 가 KMS Decrypt 호출 — 평문 key 는 enclave 안에서만 존재
        //    parent EC2 root 권한자도 해당 메모리 접근 불가
        return socket.receivePlaintext()
    }
}

// 검증자 측 attestation policy (KMS Key Policy 의 condition)
// {
//   "Condition": {
//     "StringEqualsIgnoreCase": {
//       "kms:RecipientAttestation:ImageSha384":
//         "abc123...sha384_of_signed_enclave_image"
//     }
//   }
// }
```

**관련 패턴**: Remote Attestation, Envelope Encryption, Zero Trust, Multi-Party Computation, Federated Learning

---
