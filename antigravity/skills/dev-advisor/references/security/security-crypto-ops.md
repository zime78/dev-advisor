# 암호 운영 패턴 (Crypto & Key Operations)

암호 키의 생성·보관·배포·rotation·폐기와 같은 **운영(Operations) 패턴**을 다룬다. 이 카테고리는 알고리즘 primitive(SHA-256, AES, RSA, HMAC, Bcrypt, Argon2 등 — `algorithms/crypto.md` 참조)와는 다른 층위에 있다. Primitive 가 "어떤 수학적 연산을 적용할지"를 정의한다면, 본 문서의 패턴은 "그 키와 ciphertext 를 조직 차원에서 어떻게 안전하게 다루는지"를 정의한다. 표준 근거: NIST SP 800-57(Key Management), FIPS 140-3(Crypto Module), FIPS 203/204/205(PQC), RFC 8446(TLS 1.3), RFC 9380(OPAQUE draft).

---

## 1. KMS (Key Management Service)

**목적**: 마스터 키(KEK)를 application 외부의 관리형 서비스에 보관하고, 모든 암·복호화 호출을 API 로 위임하여 키 노출 표면을 0 으로 만듭니다.

**특징**:
- AWS KMS / GCP Cloud KMS / Azure Key Vault — multi-tenant FIPS 140-3 Level 2 (CloudHSM 은 Level 3)
- KMS 가 노출하는 핵심 API: `Encrypt`, `Decrypt`, `GenerateDataKey`, `ReEncrypt`, `Sign`, `Verify`
- 키는 KMS 경계를 절대 떠나지 않음 — application 은 ciphertext 만 보유
- IAM policy + Key policy 이중 권한 모델 (AWS), CloudTrail/Cloud Audit Logs 로 모든 키 사용 기록
- Customer Master Key (CMK) 종류: AWS-managed, Customer-managed (CMK), Customer-provided (XKS/BYOK)

**장점**:
- 키 자체가 디스크/메모리에 평문으로 존재하지 않음 → 코드 dump/log/heap snapshot 유출 시에도 안전
- 권한 분리 — 개발자는 ciphertext 만, 운영자만 IAM 으로 키 사용 권한 부여
- 감사 추적 자동 — 누가 언제 어느 키로 무엇을 했는지 KMS 측 로그로 보존

**단점**:
- 호출당 latency (~5-30ms) 와 비용 ($0.03/10k requests + $1/key/month)
- KMS region outage 시 모든 암·복호화 마비 — multi-region key replication 필요
- API rate limit (AWS KMS default 5,500-30,000 RPS per region) — 대량 트래픽엔 Envelope Encryption 강제

**활용 예시**:
- S3 / EBS / RDS server-side encryption (SSE-KMS)
- Secrets Manager / Parameter Store 의 backing key
- 사용자 PII column 단위 암호화 (database envelope encryption)
- TLS private key 보관 + Sign API 로 handshake 만 위임

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// AWS KMS — 직접 Encrypt/Decrypt (작은 payload < 4KB 만 권장)
import software.amazon.awssdk.services.kms.KmsClient
import software.amazon.awssdk.services.kms.model.*
import software.amazon.awssdk.core.SdkBytes

class KmsEncryptor(private val kms: KmsClient, private val keyId: String) {
    /** 평문을 KMS 로 직접 암호화. payload < 4KB 일 때만 사용 (그 이상은 Envelope) */
    fun encrypt(plaintext: ByteArray, ctx: Map<String, String> = emptyMap()): ByteArray {
        val req = EncryptRequest.builder()
            .keyId(keyId)
            .plaintext(SdkBytes.fromByteArray(plaintext))
            .encryptionContext(ctx)  // AAD — 복호화 시 동일해야 성공
            .build()
        return kms.encrypt(req).ciphertextBlob().asByteArray()
    }

    fun decrypt(ciphertext: ByteArray, ctx: Map<String, String> = emptyMap()): ByteArray {
        val req = DecryptRequest.builder()
            .ciphertextBlob(SdkBytes.fromByteArray(ciphertext))
            .encryptionContext(ctx)
            .build()
        return kms.decrypt(req).plaintext().asByteArray()
    }
}
```

**관련 패턴**: Envelope Encryption, Key Rotation, HSM, Crypto Agility

---

## 2. HSM (Hardware Security Module)

**목적**: tamper-resistant 하드웨어 안에서만 키 생성/저장/연산을 수행하여 물리적 추출조차 불가능하게 만듭니다.

**특징**:
- FIPS 140-3 Level 3+ 인증 — tamper-evident 케이스, 침입 시 키 자동 zeroize
- 표준 인터페이스: PKCS#11 (Cryptoki), KMIP, JCE provider (`SunPKCS11`)
- 종류: 온프레미스 appliance (Thales Luna, Utimaco), Cloud HSM (AWS CloudHSM, Azure Dedicated HSM), Nitro Enclaves
- Single-tenant — 다른 고객과 절대 자원 공유 안 함
- 키 export 불가 (`CKA_EXTRACTABLE=false`) — Sign/Decrypt operation 만 외부에 노출

**장점**:
- 물리적 보안 — 키가 RAM/디스크에 평문으로 존재한 적 자체가 없음
- 컴플라이언스 — PCI-DSS Level 1, eIDAS QSCD, FIPS 140-3 Level 3 충족
- 공인인증서 / Code-signing CA / Root CA 의 root key 보관 표준

**단점**:
- 비용 — CloudHSM 약 $1.45/hour (~$1,060/월/cluster), 온프레미스는 수천만 원/대
- Latency 가 KMS 보다 높을 수 있음, throughput 도 hardware spec 에 종속
- HA 구성 시 cluster + sync 필요 (CloudHSM 은 자동 2-node 이상)

**활용 예시**:
- PKI Root CA private key (한 번 ceremony 후 평생 HSM 안에 봉인)
- 결제 시스템 PIN translation, payment HSM (Thales payShield)
- 정부/금융권 전자서명 sign-only endpoint
- Code-signing for OS kernel modules / firmware

**난이도**: 매우 높음 | **사용 빈도**: ★★

**Kotlin 예제**:
```kotlin
// PKCS#11 via SunPKCS11 provider — CloudHSM/Luna 공통
import java.security.*
import javax.crypto.Cipher

object HsmService {
    private val provider: Provider = run {
        // pkcs11-config.conf 에 library path, slot, pin 명시
        val cfg = "/etc/cloudhsm/pkcs11-config.conf"
        Security.getProvider("SunPKCS11").configure(cfg).also(Security::addProvider)
    }
    private val ks: KeyStore = KeyStore.getInstance("PKCS11", provider).apply {
        load(null, System.getenv("HSM_PIN").toCharArray())
    }

    /** HSM 안의 private key 로 서명. key 는 HSM 을 떠나지 않음 */
    fun sign(alias: String, data: ByteArray): ByteArray {
        val key = ks.getKey(alias, null) as PrivateKey
        return Signature.getInstance("SHA256withRSA", provider).run {
            initSign(key); update(data); sign()
        }
    }
}
```

**관련 패턴**: KMS, Key Ceremony, HSM Runbook, PKI

---

## 3. Envelope Encryption (DEK + KEK 2단 구조)

**목적**: 대용량 데이터를 빠르게 암호화하기 위해 데이터당 고유한 Data Encryption Key(DEK)를 사용하고, DEK 자체는 Key Encryption Key(KEK)로 한 번 더 감싸 보관합니다.

**특징**:
- 2-layer: 평문 → AES-GCM(DEK) → ciphertext, 그리고 DEK → KMS.Encrypt(KEK) → encrypted DEK
- KMS `GenerateDataKey` 한 번의 호출로 (평문 DEK, 암호화된 DEK) 동시 반환
- 저장 시: `[encrypted DEK][nonce][ciphertext][tag]` 봉투 구조로 묶어 보관
- 평문 DEK 는 메모리에서만 존재, 사용 직후 zero-fill 후 폐기
- 동일 KEK 으로 무한히 많은 DEK 발급 가능 → KMS 호출 횟수 절감

**장점**:
- 성능 — AES-GCM 은 GB/s 수준, KMS 호출은 DEK 발급/unwrap 시 한 번씩만
- 비용 — KMS 호출이 데이터 크기와 무관
- 키 격리 — DEK 가 유출되어도 해당 한 건의 ciphertext 만 영향

**단점**:
- 봉투 포맷 직접 설계 — 잘못 만들면 nonce 재사용 / AAD 누락으로 취약점
- DEK 메모리 lifetime 관리 책임 (GC 전 zero-fill)
- 복호화 시 매번 KMS unwrap 호출 — caching 전략 필요 (단, cached DEK 의 lifetime/scope 통제 필수)

**활용 예시**:
- S3 SSE-KMS, EBS volume encryption 내부 구현
- Database column 단위 encryption (큰 BLOB 컬럼)
- 로그 파일 / 백업 압축본 암호화
- E2E messaging 의 message key wrapping

**난이도**: 중간-높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// AWS KMS GenerateDataKey + AES-GCM envelope
import software.amazon.awssdk.services.kms.KmsClient
import software.amazon.awssdk.services.kms.model.GenerateDataKeyRequest
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import java.security.SecureRandom

class EnvelopeEncryptor(private val kms: KmsClient, private val kekId: String) {
    private val rng = SecureRandom()

    fun seal(plaintext: ByteArray, aad: ByteArray): ByteArray {
        // 1. KMS 에서 256-bit DEK 발급 (평문 + KEK-encrypted 둘 다 받음)
        val dk = kms.generateDataKey(GenerateDataKeyRequest.builder()
            .keyId(kekId).keySpec("AES_256").build())
        val dekPlain = dk.plaintext().asByteArray()
        val dekCipher = dk.ciphertextBlob().asByteArray()
        try {
            // 2. AES-GCM 으로 본문 암호화
            val nonce = ByteArray(12).also(rng::nextBytes)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
                init(Cipher.ENCRYPT_MODE, SecretKeySpec(dekPlain, "AES"),
                     GCMParameterSpec(128, nonce))
                updateAAD(aad)
            }
            val body = cipher.doFinal(plaintext)
            // 3. envelope = [4B dekLen][dekCipher][12B nonce][body+tag]
            return java.nio.ByteBuffer.allocate(4 + dekCipher.size + 12 + body.size)
                .putInt(dekCipher.size).put(dekCipher).put(nonce).put(body).array()
        } finally {
            dekPlain.fill(0)  // 평문 DEK 즉시 zeroize
        }
    }
}
```

**관련 패턴**: KMS, Key Rotation, AEAD (algorithms/crypto.md)

---

## 4. Key Rotation (자동/수동)

**목적**: 키 유출 시 영향 범위와 시간 창을 제한하기 위해 키를 정기적으로 교체합니다 (NIST SP 800-57 cryptoperiod 정책).

**특징**:
- AWS KMS automatic rotation — Customer-managed CMK 기본 365일 (현재는 1~10년 설정 가능, 2024+ 도입)
- 키 자체 ID 는 유지, 내부 backing key material 만 회전 (ciphertext 재암호화 불필요)
- 수동 rotation: 새 키 생성 → alias 재할당 → 구 키는 grace period 후 disable → destroy
- Envelope encryption 의 KEK rotation 은 DEK 재암호화 불필요 (DEK 가 구 KEK 으로 wrap 되었어도 KMS 가 알아서 unwrap)
- DEK rotation 은 별도 — re-encryption job 으로 전체 DEK 를 신규 KEK 으로 ReEncrypt

**장점**:
- 키 유출 시 노출 시간 창을 cryptoperiod 만큼으로 제한
- 컴플라이언스 — PCI-DSS 3.6.4, NIST SP 800-57 권고 충족
- AWS KMS automatic rotation 은 ciphertext 호환성 보장 — 운영 무중단

**단점**:
- 수동 rotation 은 alias / config / cache 동기화 누락 시 복호화 실패 발생
- DEK 재암호화 job 은 대용량 storage 에선 며칠~몇 주 소요
- Asymmetric key rotation 은 public key 배포까지 코디네이션 필요

**활용 예시**:
- TLS 인증서 자동 갱신 (Let's Encrypt 90일, ACME)
- DB encryption key 연 1회 rotation
- API signing key 90일 rotation + dual-key grace period
- JWT signing key — JWKS endpoint 로 신구 key 동시 노출 (`kid` 매칭)

**난이도**: 중간 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// JWT signing key rotation — JWKS 에 신/구 키 동시 게시
data class SigningKey(val kid: String, val key: PrivateKey, val notBefore: Instant, val notAfter: Instant)

class RotatingJwtSigner(private val keys: List<SigningKey>) {
    /** 현재 시각 기준 active 키로 서명. notAfter 가 가장 늦은 것 선택 */
    fun sign(claims: JWTClaimsSet): String {
        val now = Instant.now()
        val active = keys.filter { now in it.notBefore..it.notAfter }
            .maxByOrNull { it.notAfter } ?: error("no active signing key")
        return JWSObject(
            JWSHeader.Builder(JWSAlgorithm.RS256).keyID(active.kid).build(),
            Payload(claims.toJSONObject())
        ).apply { sign(RSASSASigner(active.key)) }.serialize()
    }

    /** JWKS endpoint 응답 — 검증 측이 신/구 모두 받아둘 수 있도록 grace period 동안 함께 노출 */
    fun jwks(): Map<String, Any> = mapOf("keys" to keys.map { it.toJwkJson() })
}
```

**관련 패턴**: KMS, Envelope Encryption, Crypto Agility, JWT Verification

---

## 5. Perfect Forward Secrecy (PFS)

**목적**: 장기 private key 가 미래에 유출되더라도, 과거에 캡처된 trafficfaqs 의 복호화를 불가능하게 만듭니다.

**특징**:
- 매 세션마다 ephemeral key pair 를 새로 생성 — ECDHE / DHE
- TLS 1.3 (RFC 8446) 은 PFS 가 **유일한 선택** — RSA key exchange 제거됨
- 핸드셰이크 직후 ephemeral private key 폐기 → 세션 키는 어디에도 평문으로 남지 않음
- Session Resumption (PSK) 은 master secret 을 재사용하므로 PFS 부분 약화 — TLS 1.3 은 `psk_ke` vs `psk_dhe_ke` 구분
- 0-RTT (early data) 는 replay 가능 + first-flight PFS 없음 → 멱등 요청에만 허용

**장점**:
- 사후 키 유출(예: HSM 압수, subpoena)에도 과거 트래픽 안전
- 컴플라이언스 — Mozilla Modern profile, BSI TR-02102 강제
- 별도 키 관리 없이 매 세션 자동 적용

**단점**:
- ECDHE handshake 가 RSA-KE 보다 CPU 사용 증가 (modern HW 에선 무시 가능)
- 0-RTT 사용 시 PFS 와 replay-resistance trade-off 명시적으로 인지 필요
- 패킷 캡처 후 오프라인 분석(legitimate IDS) 가 불가능 — TLS visibility appliance 별도 운영

**활용 예시**:
- HTTPS (TLS 1.3) — 모든 modern 브라우저/서버 기본
- SSH (Ephemeral DH 옵션)
- Signal/WhatsApp E2E messaging (Double Ratchet — Session 단위 PFS + Per-message ratchet)
- WireGuard VPN — 매 세션 Curve25519 ECDH

**난이도**: 낮음 (대부분 server config 만) | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Ktor / Netty — TLS 1.3 + ECDHE-only cipher suite 강제
import io.ktor.network.tls.*

fun secureTlsConfig() = TLSConfigBuilder().apply {
    // TLS 1.3 만 허용 (이미 PFS 강제됨)
    // TLS 1.2 도 지원해야 한다면 ECDHE suite 만 화이트리스트
    cipherSuites = listOf(
        CIOCipherSuites.TLS_AES_128_GCM_SHA256,   // TLS 1.3 — PFS 내장
        CIOCipherSuites.TLS_AES_256_GCM_SHA384,
        CIOCipherSuites.TLS_CHACHA20_POLY1305_SHA256
        // RSA_WITH_* / TLS_DH_* (static DH) 제외 — PFS 없음
    )
}
// JVM 전역 강제: -Djdk.tls.disabledAlgorithms="TLSv1, TLSv1.1, RSA keyExchange"
```

**관련 패턴**: TLS, Crypto Agility, Post-Quantum Cryptography

---

## 6. Post-Quantum Cryptography (PQC)

**목적**: 충분히 큰 양자 컴퓨터가 등장했을 때 Shor's algorithm 으로 깨질 RSA/ECDSA/ECDH 를 격자(lattice)/해시 기반 알고리즘으로 대체합니다.

**특징**:
- NIST PQC 표준화 (2024-08 최종 확정):
  - **FIPS 203 — ML-KEM** (CRYSTALS-Kyber 기반): Key Encapsulation Mechanism, TLS handshake 대체
  - **FIPS 204 — ML-DSA** (CRYSTALS-Dilithium 기반): Digital Signature, RSA/ECDSA 대체
  - **FIPS 205 — SLH-DSA** (SPHINCS+ 기반): Hash-based stateless Signature, long-term archival
- "Harvest now, decrypt later" 위협 모델 — 지금 캡처된 트래픽이 미래에 복호화될 수 있으므로 장기 비밀 데이터부터 우선 마이그레이션
- Hybrid mode 가 transition 표준 — `X25519+ML-KEM-768`, `ECDSA+ML-DSA-65` 같이 classical + PQC 동시 적용
- Key/signature size 증가: ML-DSA-65 public key 1,952B, signature 3,309B (vs ECDSA 32B/64B)

**장점**:
- 양자 내성 — Shor's algorithm 으로 해결되지 않는 lattice/hash 문제 기반
- NIST 공식 표준 — 컴플라이언스 로드맵 명확 (CNSA 2.0: 2030년까지 PQC 전환)
- Hybrid 로 classical 강도 동시 유지 — 한쪽이 깨져도 다른 쪽이 방어

**단점**:
- Key/ciphertext/signature 크기가 10-100배 증가 → handshake 대역폭, TCP MTU 압박
- 구현체 성숙도 낮음 — 사이드채널/실수 risk, library 안정성 검증 진행 중
- Algorithm agility 가 전제 — 표준 변경 가능성 (FrodoKEM, BIKE backup 등)

**활용 예시**:
- TLS 1.3 hybrid key exchange (Cloudflare, Chrome 124+ 가 `X25519MLKEM768` 활성)
- Code signing — Linux kernel, OpenSSH (`ssh-mldsa` 도입 검토)
- 장기 보관 문서 서명 — SLH-DSA (stateless, 매우 보수적 보안 가정)
- Smart card / Passport 의 ML-DSA 인증서 (eIDAS 2.0 검토)

**난이도**: 매우 높음 | **사용 빈도**: ★★ (2026 기준 도입 초기)

**Kotlin 예제**:
```kotlin
// Bouncy Castle 1.78+ — ML-KEM (FIPS 203) key encapsulation
import org.bouncycastle.jcajce.spec.MLKEMParameterSpec
import java.security.*

fun mlKemHandshake() {
    Security.addProvider(org.bouncycastle.jce.provider.BouncyCastleProvider())

    // Receiver: ML-KEM-768 keypair 생성
    val kpg = KeyPairGenerator.getInstance("ML-KEM", "BC").apply {
        initialize(MLKEMParameterSpec.ml_kem_768)
    }
    val (pub, priv) = kpg.generateKeyPair().let { it.public to it.private }

    // Sender: pub 으로 encapsulate → (shared secret, ciphertext) 생성
    val kem = KEM.getInstance("ML-KEM", "BC")
    val enc = kem.newEncapsulator(pub).encapsulate()
    val senderSecret: SecretKey = enc.key()   // 양측 동일한 32B AES 키
    val ct: ByteArray = enc.encapsulation()    // 1,088B — Receiver 에게 전송

    // Receiver: priv 로 decapsulate → 동일한 shared secret 복원
    val receiverSecret = kem.newDecapsulator(priv).decapsulate(ct)
    require(senderSecret.encoded.contentEquals(receiverSecret.encoded))

    // 실전: 단독 사용 금지 — X25519 와 hybrid 로 결합
    // hybridSecret = HKDF(X25519_ss || MLKEM_ss, salt, info)
}
```

**관련 패턴**: Crypto Agility, PFS, Key Rotation, TLS

---

## 7. Crypto Agility

**목적**: 알고리즘이 깨지거나 표준이 바뀌었을 때 application 코드 변경 없이 즉시 교체할 수 있도록, 키/ciphertext/프로토콜에 algorithm version 을 명시합니다.

**특징**:
- Ciphertext header 에 algorithm ID + version 포함 — 예: `{"alg":"AES-GCM-256","v":2,"kek_id":"...","nonce":"..."}`
- Versioned KEK — KEK 마다 어떤 알고리즘 family 인지 metadata 보존
- Negotiation protocol — TLS cipher suite, SSH KexAlgorithms, JWT `alg` header
- Deprecation timeline — `[announced → deprecated → disabled → removed]` 4단계 lifecycle
- Backward read / forward write — 신규 데이터는 새 알고리즘으로 쓰되, 구 알고리즘 ciphertext 도 일정 기간 읽기는 지원

**장점**:
- Heartbleed / SHA-1 collision / RC4 weakness 같은 emergency 대응이 deploy 한 번
- PQC 전환 같은 대규모 마이그레이션을 점진적으로 수행
- 컴플라이언스 변경(예: CNSA 1.0 → 2.0)에 코드 베이스 변경 없이 대응

**단점**:
- 모든 ciphertext 가 header overhead (수 십 바이트) 보유
- 알고리즘 화이트리스트 / 우선순위 / fallback 정책을 명확히 안 짜면 downgrade 공격 발생
- 구 알고리즘 코드 경로가 영구히 남음 — 보안 audit 가 더 복잡

**활용 예시**:
- JWT `alg` header — 알고리즘 화이트리스트 강제하여 `alg:none` 공격 차단
- TLS cipher suite negotiation (priority order + signature_algorithms extension)
- Signal Sesame protocol — message header 에 protocol version
- AWS KMS — `EncryptionAlgorithm` parameter 로 명시 선택

**난이도**: 중간 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Algorithm-tagged envelope — 알고리즘 family 마다 별도 codec 등록
enum class AlgVersion(val id: Byte) {
    AES_GCM_256_V1(0x01),
    XCHACHA20_POLY1305_V1(0x02),
    AES_GCM_256_V2_AAD(0x03);  // V2: AAD 필수화

    companion object {
        fun of(b: Byte) = values().firstOrNull { it.id == b }
            ?: error("unknown alg version $b — refusing to decrypt")
    }
}

interface Codec { fun seal(pt: ByteArray, aad: ByteArray): ByteArray; fun open(ct: ByteArray, aad: ByteArray): ByteArray }

class AgileCrypto(private val codecs: Map<AlgVersion, Codec>, private val writeAlg: AlgVersion) {
    fun seal(pt: ByteArray, aad: ByteArray): ByteArray {
        val body = codecs.getValue(writeAlg).seal(pt, aad)
        return byteArrayOf(writeAlg.id) + body          // 첫 바이트 = algorithm tag
    }
    fun open(envelope: ByteArray, aad: ByteArray): ByteArray {
        val v = AlgVersion.of(envelope[0])
        val codec = codecs[v] ?: error("alg $v deprecated and removed")
        return codec.open(envelope.copyOfRange(1, envelope.size), aad)
    }
}
// Deprecation 정책: AES_GCM_256_V1 는 2026-12 부터 read-only, 2027-06 부터 removed.
```

**관련 패턴**: Key Rotation, Post-Quantum Cryptography, JWT Verification

---

## 8. OPAQUE / aPAKE (Augmented Password-Authenticated Key Exchange)

**목적**: 사용자 패스워드를 **서버에 절대 전송하지 않고** 인증과 세션 키 합의를 동시에 수행하여, 서버 측 패스워드 데이터베이스 유출이 발생해도 offline brute-force 가 불가능하게 만듭니다.

**특징**:
- RFC 9380 / CFRG draft `draft-irtf-cfrg-opaque` — IRTF CFRG 권고 aPAKE
- 서버가 저장하는 것: oblivious key 와 envelope (패스워드 hash 가 아닌, 패스워드 기반 암호화된 사용자 secret)
- 등록 흐름: client → blinded password → server (OPRF) → client envelope 생성 후 server 에 저장
- 로그인 흐름: client → blinded password → server (OPRF + envelope return) → client local decrypt → mutual auth + session key
- Zero-knowledge — 서버는 어느 순간에도 패스워드/패스워드 hash 를 보지 못함

**장점**:
- 서버 DB 통째 유출되어도 offline dictionary attack 차단 — OPRF key 없으면 unblinding 불가
- TLS 와 결합하면 phishing-resistant — server impersonation 차단
- bcrypt/Argon2 의 한계(서버 측 hash 자체가 brute-force 가능) 해결

**단점**:
- 구현체 성숙도 낮음 — production-ready library 가 제한적 (Cloudflare 의 opaque-ke 가 Rust 레퍼런스)
- TLS 위에서 동작해야 하며, 패스워드 reset 흐름은 별도 OOB 채널 필요
- 추가 round-trip — 1~2 RTT 증가

**활용 예시**:
- WhatsApp Multi-Device 의 device linking (registration without server-known password)
- Password manager 의 master password verification (1Password SRP — OPAQUE 의 전 세대)
- 정부/금융권 high-assurance 로그인 (subjective trust 가 0 에 가까운 환경)

**난이도**: 매우 높음 | **사용 빈도**: ★ (현재 driver: WhatsApp, Cloudflare; 일반 web 도입 초기)

**Kotlin 예제**:
```kotlin
// 개념 흐름 — opaque-ke 같은 binding 또는 JVM port 가정.
// 실제 구현은 Ristretto255 + Argon2id + HKDF 가 필수.
interface OpaqueClient {
    /** 등록: 패스워드 → blinded 요청. 서버 응답으로 envelope 생성 */
    fun registerStart(password: String): ClientRegistrationRequest
    fun registerFinish(serverResp: ServerRegistrationResponse, password: String): RegistrationRecord

    /** 로그인: blinded 요청 + ephemeral key */
    fun loginStart(password: String): ClientLoginRequest
    fun loginFinish(serverResp: ServerLoginResponse, password: String): LoginResult  // sessionKey + serverAuth
}

// 서버는 oprfKey 와 registrationRecord 만 저장. password / pwd-hash 보관 일절 없음
class OpaqueServer(private val oprfKey: ByteArray, private val records: Map<String, RegistrationRecord>) {
    fun loginStart(userId: String, req: ClientLoginRequest): ServerLoginResponse {
        val rec = records[userId] ?: throw IllegalArgumentException("불명")  // user enumeration 방지 — dummy record 반환
        return Opaque.serverLogin(oprfKey, rec, req)  // envelope + serverEphemeral 반환
    }
}
```

**관련 패턴**: PFS, Zero Trust, Argon2 (algorithms/crypto.md)

---

## 9. mTLS (Mutual TLS)

**목적**: 일반 TLS 가 서버 측만 인증서를 제시하는 것과 달리, 양측 모두 X.509 인증서로 자신의 신원을 증명하여 service-to-service 통신을 인증합니다.

**특징**:
- TLS handshake 의 `CertificateRequest` + client `Certificate` + `CertificateVerify` 메시지로 client 인증
- 인증서 chain 검증: leaf → intermediate → root CA, 매 단계 signature + validity + revocation 확인
- Revocation: CRL (Certificate Revocation List), OCSP, OCSP stapling (TLS 1.3 에서 stapling 가 기본)
- SPIFFE/SPIRE — workload identity 표준: `spiffe://<trust-domain>/ns/<ns>/sa/<sa>` URI 를 SAN 에 넣은 X.509-SVID 또는 JWT-SVID
- 인증서 lifetime 단축 — Let's Encrypt 90일, SPIRE 는 1시간 단위로 자동 회전

**장점**:
- Network 침투 가정에서도 service identity 강제 (Zero Trust)
- 사후 감사 — 모든 연결에 client 신원이 cryptographically 증명됨
- Service mesh (Istio, Linkerd) 가 sidecar 로 투명 적용 가능

**단점**:
- 인증서 발급/배포/rotation 자동화 안 되면 운영 부담 폭증 — SPIRE/cert-manager 필수
- Client certificate revocation 전파 지연 (CRL 폴링 주기, OCSP cache TTL)
- 인증서 만료 사고 — 대규모 outage 의 흔한 원인 (모니터링 + 알림 필수)

**활용 예시**:
- Kubernetes 내 service mesh — Istio mutual TLS, Linkerd automatic mTLS
- 금융권 API B2B 통신 (PASETO/mTLS hybrid)
- IoT device → cloud 통신 (AWS IoT Core mTLS)
- 사내 RPC (gRPC + mTLS, Twitch 의 OSS twirp 등)

**난이도**: 중간-높음 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Ktor server — client certificate 검증 + SPIFFE ID 추출
import io.ktor.network.tls.*
import java.security.cert.X509Certificate

fun Application.mtlsServer() {
    install(Authentication) {
        // X.509 cert chain 검증은 JVM TrustManager 가 수행
        // 추가로 SAN 의 SPIFFE URI 화이트리스트 적용
    }
    routing {
        get("/internal/jobs") {
            val cert = call.request.tlsCertificate() as? X509Certificate
                ?: return@get call.respond(HttpStatusCode.Unauthorized)
            val spiffeId = cert.subjectAlternativeNames
                ?.firstOrNull { it[0] == 6 /* URI */ }
                ?.get(1) as? String
            require(spiffeId == "spiffe://corp.io/ns/jobs/sa/runner") { "wrong workload" }
            call.respond(processJob())
        }
    }
}

// HttpClient (client) — keystore + truststore 둘 다 지정
val tls = TLSConfigBuilder().apply {
    addKeyStore(myKeyStore, keystorePwd.toCharArray())   // client cert + private key
    trustManager = customTrustManager                      // 신뢰 CA bundle
}
```

**관련 패턴**: PFS, KMS, HSM, Zero Trust Architecture, Key Rotation

---

## 10. Key Ceremony

**목적**: Root CA / Master KEK 같은 **최고 가치 키**를 생성·activation 할 때, 단일 신뢰점이 없도록 다수 참석자·물리 보안·녹화·M-of-N split 으로 의식화된 절차를 수행합니다.

**특징**:
- 참석자: Key Custodian (M of N), Security Officer, Auditor, Notary, 최소 2명 이상 — separation of duties
- 물리 보안: Faraday-cage 룸, air-gap, 카메라 녹화, 시퀀스 번호가 있는 봉인 봉투
- M-of-N split — Shamir's Secret Sharing (algorithms/crypto.md `Shamir Secret Sharing` 참조) 으로 master key 를 N 개 share 로 나눠 M 명 이상 모여야 재구성 가능
- HSM 안에서 직접 생성 — host RAM/디스크에 평문이 절대 닿지 않음
- 산출물: ceremony script (사전 작성, 단계별 사인), 녹화 영상, audit log, 각 share 의 봉인된 카드 (smartcard / paper / HSM PED key)

**장점**:
- Insider threat 방어 — 단일 인물이 root key 를 단독으로 활용 불가
- 규제 대응 — WebTrust for CA, CA/Browser Forum BR, eIDAS 인증 요건
- 재현 가능 — script + 영상 + audit log 로 사후 검증

**단점**:
- 매우 무거움 — 1회 실행에 수 시간~수 일, 비용 수천만 원
- M-of-N 의 M-1 명이 동시 부재 / 사망 / 퇴사 시 root key 영구 lost (disaster recovery share 보관 정책 필수)
- 모든 참여자의 신원/배경조사가 사전 수행되어야 함

**활용 예시**:
- Public Root CA 생성 (DigiCert, GlobalSign, Let's Encrypt ISRG Root X1)
- DNSSEC Root KSK Ceremony — IANA 가 분기마다 공개 진행, 인터넷 root trust anchor 갱신
- 결제 시스템 Zone Master Key (ZMK) 생성 (PCI-PIN HSM)
- 기업 PKI Root CA, Code-signing CA root

**난이도**: 매우 높음 | **사용 빈도**: ★ (조직당 root 키 종류만큼만)

**Kotlin 예제**:
```kotlin
// 코드 자체보다 절차가 본질. HSM 측 PKCS#11 호출 흐름의 골격만 표현.
class KeyCeremonyOrchestrator(private val hsm: Pkcs11Hsm) {
    /**
     * 의식 절차 (사전 인쇄 script):
     *  1) 참석자 신원 확인 + 봉인봉투 개봉 영상 기록
     *  2) HSM tamper seal 확인
     *  3) HSM 안에서 직접 RSA-4096 / ECDSA-P384 keypair 생성 — CKA_EXTRACTABLE=false
     *  4) Public key 만 HSM 외부로 export, CSR 작성 후 self-sign root cert 생성
     *  5) HSM 의 backup 을 5-of-7 smartcard split 으로 분할 (HSM 내부 split — Luna PED, AWS CloudHSM cloning)
     *  6) 각 smartcard 봉인 → 별도 금고/지역에 보관 (사본 1개는 disaster recovery)
     *  7) Audit log 출력 + 모든 참석자 서명 + 영상 sealing
     */
    fun generateRootKey(ceremonyId: String, custodians: List<Custodian>): CeremonyReceipt {
        require(custodians.size >= MIN_CUSTODIANS) { "M-of-N: 최소 ${MIN_CUSTODIANS}명 필요" }
        val attrs = mapOf("CKA_TOKEN" to true, "CKA_EXTRACTABLE" to false,
                          "CKA_SENSITIVE" to true, "CKA_LABEL" to "root-ca-$ceremonyId")
        val pubKey = hsm.generateKeyPair("RSA", 4096, attrs)
        val cert = hsm.selfSignRootCert(pubKey, validityYears = 25)
        // backup split 은 HSM vendor 별 API (Luna: ped key clone, CloudHSM: clusterBackup)
        return CeremonyReceipt(ceremonyId, cert, custodians, Instant.now())
    }
    companion object { const val MIN_CUSTODIANS = 5 }
}
```

**관련 패턴**: HSM, HSM Runbook, KMS, Shamir Secret Sharing (algorithms/crypto.md)

---

## 11. HSM Runbook / Key Lifecycle Operations

**목적**: NIST SP 800-57 의 key state machine (Pre-Activation / Active / Suspended / Deactivated / Compromised / Destroyed) 을 따라 키의 운영 상태 전이를 표준화하고, compromise 발생 시 사고 대응 절차를 사전에 코드/문서화합니다.

**특징**:
- Key state machine (NIST SP 800-57 Part 1):
  - **Pre-Activation**: 생성됐으나 사용 불가 (Ceremony 직후)
  - **Active**: encrypt / sign 등 모든 operation 가능
  - **Suspended**: 임시 사용 중지 (조사 중) — 복귀 가능
  - **Deactivated**: 신규 protect 불가, 기존 ciphertext 검증/복호화만 가능
  - **Compromised**: 모든 사용 즉시 중지, 영향 범위 식별 및 재암호화
  - **Destroyed**: zeroize 후 복구 불가 — audit log 만 잔존
- 각 상태 전이는 권한자(M-of-N) 서명 + 감사 로그 필수
- Compromise 대응 시나리오 사전 작성: detection → contain → revoke → re-encrypt → root cause → post-mortem
- HSM 측 명령: `activate`, `deactivate`, `delete`, `clone` — PKCS#11 / vendor CLI 로 수행
- Backup 정책: HSM-encrypted backup 만 허용, off-site 보관, restore 도 ceremony 절차

**장점**:
- 사고 발생 시 의사결정 시간 단축 — runbook 따라 분 단위 실행
- 컴플라이언스 — SOC2, ISO 27001 A.10, PCI-DSS 3.5/3.6 충족
- Audit 가능성 — 모든 상태 전이가 영구 보존

**단점**:
- Runbook 작성/훈련 비용 — table-top exercise + quarterly drill 필요
- Compromise 후 re-encryption job 이 storage 크기에 비례한 시간
- "Destroyed" 후 발견된 의존성은 복구 불가 — dependency mapping 사전 필수

**활용 예시**:
- PKI CA 운영 (Active CA → Deactivate → Decommission 까지 수년)
- KMS CMK lifecycle (AWS `ScheduleKeyDeletion` 7-30 day waiting period 가 본 패턴의 구현)
- 결제 HSM 의 ZMK rotation 절차서
- 개인정보 암호화 키 destroy 시 영향받는 모든 column re-encryption job

**난이도**: 높음 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// NIST SP 800-57 key state machine 의 코드화
enum class KeyState { PRE_ACTIVATION, ACTIVE, SUSPENDED, DEACTIVATED, COMPROMISED, DESTROYED }

data class ManagedKey(val id: String, val state: KeyState, val activatedAt: Instant?,
                     val deactivatedAt: Instant?, val compromisedAt: Instant?)

class KeyLifecycleService(private val hsm: Pkcs11Hsm, private val audit: AuditLog,
                          private val approver: MofNApprover) {

    /** 정상 흐름: Pre-Activation → Active */
    fun activate(keyId: String, ticket: ChangeTicket): ManagedKey {
        approver.require(ticket, minApprovals = 2)
        val k = load(keyId).requireState(KeyState.PRE_ACTIVATION)
        audit.record("ACTIVATE", keyId, ticket)
        return k.copy(state = KeyState.ACTIVE, activatedAt = Instant.now()).also(::save)
    }

    /** 일반 만료: 신규 encrypt 차단, 복호화만 허용 */
    fun deactivate(keyId: String, ticket: ChangeTicket): ManagedKey {
        approver.require(ticket, minApprovals = 2)
        val k = load(keyId).requireState(KeyState.ACTIVE)
        audit.record("DEACTIVATE", keyId, ticket)
        return k.copy(state = KeyState.DEACTIVATED, deactivatedAt = Instant.now()).also(::save)
    }

    /** Compromise 대응: 즉시 모든 사용 차단 + 영향 받은 ciphertext 식별 job 시작 */
    fun markCompromised(keyId: String, incident: IncidentReport): ManagedKey {
        approver.require(incident.ticket, minApprovals = 3)  // 더 높은 임계
        val k = load(keyId)
        audit.record("COMPROMISE", keyId, incident)
        hsm.disable(keyId)  // PKCS#11 CKA_PRIVATE=true 유지하되 사용 불가 플래그
        incidentResponse.startReEncryptionJob(keyId)  // 의존 ciphertext 신규 KEK 으로 ReEncrypt
        return k.copy(state = KeyState.COMPROMISED, compromisedAt = Instant.now()).also(::save)
    }

    /** 최종 폐기 — waiting period 후에만 가능, 복구 불가 */
    fun destroy(keyId: String, ticket: ChangeTicket): ManagedKey {
        approver.require(ticket, minApprovals = 3)
        val k = load(keyId).requireState(KeyState.DEACTIVATED, KeyState.COMPROMISED)
        require(Duration.between(k.deactivatedAt ?: k.compromisedAt, Instant.now()) >= WAITING)
        hsm.zeroize(keyId)
        audit.record("DESTROY", keyId, ticket)
        return k.copy(state = KeyState.DESTROYED).also(::save)
    }
    companion object { val WAITING: Duration = Duration.ofDays(30) }
}
```

**관련 패턴**: HSM, Key Ceremony, KMS, Key Rotation, Crypto Agility

---
