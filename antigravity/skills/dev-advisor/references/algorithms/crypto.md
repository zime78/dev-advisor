# 암호/해시 알고리즘 (Cryptography & Hashing)

데이터 무결성, 인증, 기밀성을 위한 암호학적 알고리즘입니다. 실제 production 코드는 반드시 검증된 표준 라이브러리(`java.security`, `javax.crypto`)나 BouncyCastle을 사용해야 하며, 직접 구현은 금지합니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [sha-256](#sha-256) | SHA-256 | Secure Hash Algorithm 256-bit | 중간 |
| [hmac](#hmac) | HMAC | Hash-based Message Authentication Code | 중간 |
| [rsa](#rsa) | RSA | Rivest-Shamir-Adleman | 높음 |
| [aes](#aes) | AES | Advanced Encryption Standard | 중간 |
| [bcrypt](#bcrypt) | Bcrypt | Blowfish-based password hashing | 중간 |
| [argon2](#argon2) | Argon2 | 메모리 하드 비밀번호 해시 | 높음 |
| [ecc](#ecc) | ECC (ECDSA/Ed25519/ECDH) | 타원곡선 암호 | 높음 |
| [diffie-hellman](#diffie-hellman) | Diffie-Hellman | 디피-헬먼 키 교환 | 높음 |
| [chacha20-poly1305](#chacha20-poly1305) | ChaCha20-Poly1305 | 스트림 AEAD | 중간 |
| [sha-3](#sha-3) | SHA-3 / Keccak | SHA-3 스펀지 해시 | 중간 |
| [blake2-blake3](#blake2-blake3) | BLAKE2 / BLAKE3 | 고속 암호 해시 | 중간 |
| [scrypt-pbkdf2](#scrypt-pbkdf2) | scrypt / PBKDF2 | 키 유도 함수 (KDF) | 중간 |

---

<a id="sha-256"></a>
## 1. SHA-256 (Secure Hash Algorithm 256-bit)

**목적**: 임의 길이 입력을 256비트 고정 길이 해시로 변환

**시간 복잡도**: O(n) - n: 입력 바이트 수

**공간 복잡도**: O(1)

**특징**:
- 메시지 → 패딩 → 512비트 블록 분할 → 64라운드 압축 함수
- 단방향 해시 (역함수 계산 불가)
- 충돌 저항성 / 두 번째 원상 저항성

**장점**:
- NIST 표준, 광범위한 지원
- 충돌 발견된 사례 없음
- 빠르고 안정적

**단점**:
- 비밀번호 해싱에는 부적합 (Bcrypt/Argon2 사용)
- 양자 컴퓨터에 약해질 수 있음 (SHA-3 후보)

**활용 예시**:
- 파일 무결성 검증
- 디지털 서명
- 블록체인 (Bitcoin)
- HMAC 기반 메시지

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import java.security.MessageDigest

fun sha256(input: ByteArray): ByteArray {
    val digest = MessageDigest.getInstance("SHA-256")
    return digest.digest(input)
}

fun sha256Hex(input: String): String {
    val bytes = sha256(input.toByteArray(Charsets.UTF_8))
    return bytes.joinToString("") { "%02x".format(it) }
}

// 큰 파일 스트리밍 해싱 (메모리 적게 사용)
fun sha256Streaming(stream: java.io.InputStream): ByteArray {
    val digest = MessageDigest.getInstance("SHA-256")
    val buffer = ByteArray(8192)
    while (true) {
        val read = stream.read(buffer)
        if (read <= 0) break
        digest.update(buffer, 0, read)
    }
    return digest.digest()
}

// 알고리즘 단계 (개념용):
// 1. 패딩: 메시지 끝에 1 비트, 0들, 마지막 64비트에 원본 길이
// 2. 512비트 블록 단위로 처리
// 3. 각 블록을 64개 워드로 확장 (W[0..63])
// 4. 8개 워킹 변수 a..h 초기화 (이전 해시 값)
// 5. 64 라운드: T1 = h + Σ1(e) + Ch(e,f,g) + K[t] + W[t], T2 = Σ0(a) + Maj(a,b,c)
// 6. 새 해시 = (이전 해시 + a..h)
// 표준 K 상수 64개 + 초기 H 상수 8개는 RFC 6234 참조
```

**Note**: 직접 구현 금지. `MessageDigest`만 사용하세요.

**관련 알고리즘**: SHA-1, SHA-3, BLAKE2

---

<a id="hmac"></a>
## 2. HMAC (Hash-based Message Authentication Code)

**목적**: 공유 비밀키를 사용한 메시지 무결성 + 인증 코드

**시간 복잡도**: O(n) - n: 메시지 길이

**공간 복잡도**: O(1)

**특징**:
- HMAC(K, m) = H((K ⊕ opad) || H((K ⊕ ipad) || m))
- ipad = 0x36 반복, opad = 0x5C 반복
- 키 길이가 블록보다 길면 해시 적용

**장점**:
- 길이 확장 공격 방어
- 표준화 (RFC 2104)
- 단순 H(K||m)보다 안전

**단점**:
- 키 관리 필요
- 키 노출 시 무력화

**활용 예시**:
- JWT 서명 (HS256)
- API 요청 인증 (AWS Signature)
- TLS / IPSec
- Webhook 검증

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

fun hmacSha256(key: ByteArray, message: ByteArray): ByteArray {
    val mac = Mac.getInstance("HmacSHA256")
    mac.init(SecretKeySpec(key, "HmacSHA256"))
    return mac.doFinal(message)
}

fun hmacSha256Hex(key: String, message: String): String {
    val mac = hmacSha256(
        key.toByteArray(Charsets.UTF_8),
        message.toByteArray(Charsets.UTF_8)
    )
    return mac.joinToString("") { "%02x".format(it) }
}

// 상수 시간 비교 (타이밍 공격 방어)
fun constantTimeEquals(a: ByteArray, b: ByteArray): Boolean {
    if (a.size != b.size) return false
    var result = 0
    for (i in a.indices) {
        result = result or (a[i].toInt() xor b[i].toInt())
    }
    return result == 0
}
```

**Note**: 직접 구현 금지. `javax.crypto.Mac` 사용.

**관련 알고리즘**: SHA-256, CMAC, KMAC

---

<a id="rsa"></a>
## 3. RSA (Rivest-Shamir-Adleman)

**목적**: 큰 소수의 인수분해 난해성에 기반한 공개키 암호 시스템

**시간 복잡도**: O(k³) - k: 키 비트 길이 (모듈러 지수승 기준)

**공간 복잡도**: O(k)

**특징**:
- 키 생성: 두 큰 소수 p, q 선택, n = pq, φ(n) = (p-1)(q-1), e와 gcd(e, φ)=1, d = e⁻¹ mod φ
- 암호화: c = m^e mod n
- 복호화: m = c^d mod n
- 공개키 (n, e), 비밀키 d

**장점**:
- 검증된 보안
- 디지털 서명 + 암호화 모두 가능
- 광범위한 인프라

**단점**:
- 느림 (대칭키보다 수백~수천 배)
- 큰 키 크기 (2048비트 이상 권장)
- 직접 큰 평문 암호화 부적합 (하이브리드 사용)

**활용 예시**:
- TLS/SSL 키 교환
- PGP/GPG 이메일 암호화
- SSH 키
- 디지털 서명 (코드 사이닝)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import java.security.KeyPairGenerator
import java.security.KeyPair
import javax.crypto.Cipher
import java.security.interfaces.RSAPublicKey
import java.security.interfaces.RSAPrivateKey

fun generateRsaKeyPair(bits: Int = 2048): KeyPair {
    val gen = KeyPairGenerator.getInstance("RSA")
    gen.initialize(bits)
    return gen.generateKeyPair()
}

fun rsaEncrypt(publicKey: RSAPublicKey, plain: ByteArray): ByteArray {
    val cipher = Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding")
    cipher.init(Cipher.ENCRYPT_MODE, publicKey)
    return cipher.doFinal(plain)
}

fun rsaDecrypt(privateKey: RSAPrivateKey, cipherBytes: ByteArray): ByteArray {
    val cipher = Cipher.getInstance("RSA/ECB/OAEPWithSHA-256AndMGF1Padding")
    cipher.init(Cipher.DECRYPT_MODE, privateKey)
    return cipher.doFinal(cipherBytes)
}

// 수식 표현 (학습용, 작은 수만)
// 키 생성
//   p, q: 큰 소수
//   n = p * q
//   φ(n) = (p - 1) * (q - 1)
//   e: gcd(e, φ) = 1, 보통 65537
//   d: e * d ≡ 1 (mod φ)
// 암호화: c = m^e mod n
// 복호화: m = c^d mod n
// 서명: s = m^d mod n, 검증: m = s^e mod n
```

**Note**: 직접 구현 금지. `KeyPairGenerator` + `Cipher` 사용. 패딩은 OAEP/PSS 사용.

**관련 알고리즘**: ECC, ElGamal, Diffie-Hellman

---

<a id="aes"></a>
## 4. AES (Advanced Encryption Standard)

**목적**: 대칭키 블록 암호. 128/192/256비트 키 지원

**시간 복잡도**: O(n) - n: 평문 길이

**공간 복잡도**: O(1)

**특징**:
- 128비트 블록, SubBytes/ShiftRows/MixColumns/AddRoundKey 라운드
- 키 크기별 라운드: 128→10, 192→12, 256→14
- 모드: ECB (금지), CBC, CTR, GCM (AEAD 권장)

**장점**:
- 표준화, 하드웨어 가속 (AES-NI)
- 매우 빠름
- 충분히 안전

**단점**:
- 모드/패딩/IV 선택 잘못하면 취약
- 키 관리 어려움 (KMS 권장)

**활용 예시**:
- 디스크 암호화 (BitLocker, FileVault)
- TLS 대칭 채널
- 데이터베이스 컬럼 암호화
- VPN

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import java.security.SecureRandom

fun generateAesKey(bits: Int = 256): SecretKey {
    val gen = KeyGenerator.getInstance("AES")
    gen.init(bits)
    return gen.generateKey()
}

// AES-GCM (AEAD - 무결성 + 기밀성)
fun aesGcmEncrypt(key: SecretKey, plain: ByteArray): ByteArray {
    val iv = ByteArray(12).also { SecureRandom().nextBytes(it) }
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    cipher.init(Cipher.ENCRYPT_MODE, key, GCMParameterSpec(128, iv))
    val cipherText = cipher.doFinal(plain)
    return iv + cipherText // IV는 평문이어도 안전 (재사용만 금지)
}

fun aesGcmDecrypt(key: SecretKey, ivAndCipher: ByteArray): ByteArray {
    val iv = ivAndCipher.sliceArray(0..11)
    val cipherBytes = ivAndCipher.sliceArray(12 until ivAndCipher.size)
    val cipher = Cipher.getInstance("AES/GCM/NoPadding")
    cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, iv))
    return cipher.doFinal(cipherBytes)
}

// 비밀번호에서 키 유도는 PBKDF2/Argon2 별도 사용
fun keyFromBytes(bytes: ByteArray): SecretKey = SecretKeySpec(bytes, "AES")
```

**Note**: ECB 모드 절대 금지. AEAD(GCM) 권장. IV 재사용 금지.

**관련 알고리즘**: ChaCha20-Poly1305, Camellia, DES (deprecated)

---

<a id="bcrypt"></a>
## 5. Bcrypt (Blowfish-based password hashing)

**목적**: 비밀번호 해싱 전용. cost factor로 의도적으로 느린 계산

**시간 복잡도**: O(2^cost) - cost factor에 지수적

**공간 복잡도**: O(1)

**특징**:
- Blowfish 키 셋업의 변형
- salt 자동 포함 (해시 문자열 내 포함)
- cost factor (work factor) 조정 가능 (보통 10~12)

**장점**:
- 무차별 대입 공격에 강함
- salt 처리 내장
- 검증된 오랜 역사

**단점**:
- GPU/ASIC 공격에는 Argon2가 더 강함
- 72바이트 이상은 무시됨
- 메모리 hard가 아님

**활용 예시**:
- 사용자 비밀번호 저장 (DB)
- 인증 시스템
- API 키 해싱

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 표준 JDK에는 Bcrypt 없음 — spring-security-crypto 또는 jbcrypt 사용
// 여기선 표준 라이브러리만 사용 가능한 PBKDF2로 대체 시연
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec
import java.security.SecureRandom
import java.util.Base64

fun pbkdf2Hash(password: CharArray, iterations: Int = 100_000, keyBits: Int = 256): String {
    val salt = ByteArray(16).also { SecureRandom().nextBytes(it) }
    val spec = PBEKeySpec(password, salt, iterations, keyBits)
    val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
    val hash = factory.generateSecret(spec).encoded

    val b64 = Base64.getEncoder()
    return "pbkdf2_sha256\$$iterations\$${b64.encodeToString(salt)}\$${b64.encodeToString(hash)}"
}

fun pbkdf2Verify(password: CharArray, stored: String): Boolean {
    val parts = stored.split("$")
    if (parts.size != 4 || parts[0] != "pbkdf2_sha256") return false
    val iter = parts[1].toInt()
    val salt = Base64.getDecoder().decode(parts[2])
    val expected = Base64.getDecoder().decode(parts[3])

    val spec = PBEKeySpec(password, salt, iter, expected.size * 8)
    val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
    val actual = factory.generateSecret(spec).encoded

    // 상수 시간 비교
    if (actual.size != expected.size) return false
    var diff = 0
    for (i in actual.indices) diff = diff or (actual[i].toInt() xor expected[i].toInt())
    return diff == 0
}

// 실제 Bcrypt 사용 (Spring Security):
//   val encoder = BCryptPasswordEncoder(12)
//   val hash = encoder.encode(password)
//   val ok = encoder.matches(password, hash)
```

**Note**: 직접 구현 금지. Spring Security `BCryptPasswordEncoder` 또는 jbcrypt 사용.

**관련 알고리즘**: scrypt, Argon2, PBKDF2

---

<a id="argon2"></a>
## 6. Argon2 (메모리 하드 비밀번호 해시)

**목적**: 메모리 + 시간 비용을 모두 조정 가능한 비밀번호 해싱. 2015 PHC 우승

**시간 복잡도**: O(t * m) - t: 반복 횟수, m: 메모리 크기

**공간 복잡도**: O(m) - 의도적으로 큰 메모리 사용

**특징**:
- 변종: Argon2d (GPU 저항), Argon2i (사이드 채널 저항), Argon2id (혼합, 권장)
- 파라미터: t (iterations), m (memory KB), p (parallelism)
- 권장: m=64MB, t=3, p=1 (인터랙티브)

**장점**:
- GPU/ASIC 공격에 가장 강함
- 현 시점 최선의 비밀번호 해시
- OWASP 권장 (2025 기준)

**단점**:
- 메모리 많이 사용
- 표준 JDK에 없음 (외부 라이브러리 필요)
- 파라미터 튜닝 필요

**활용 예시**:
- 신규 시스템 비밀번호 저장
- 고가치 자격 증명
- 디스크 암호화 키 유도

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// 표준 JDK에는 Argon2 없음 — argon2-jvm, BouncyCastle 1.78+ 등 사용
// 인터페이스 시연 (실제 호출 가능한 라이브러리 wrapper)
interface PasswordHasher {
    fun hash(password: CharArray): String
    fun verify(password: CharArray, hash: String): Boolean
}

// 권장 파라미터
data class Argon2Params(
    val iterations: Int = 3,
    val memoryKB: Int = 65536,    // 64MB
    val parallelism: Int = 1,
    val hashBytes: Int = 32,
    val saltBytes: Int = 16
)

// 출력 형식 (PHC string):
// $argon2id$v=19$m=65536,t=3,p=1$<base64-salt>$<base64-hash>
//
// 실제 사용 (de.mkammerer:argon2-jvm):
//   val argon2 = Argon2Factory.create(Argon2Types.ARGON2id)
//   val hash = argon2.hash(3, 65536, 1, password)
//   try {
//       val ok = argon2.verify(hash, password)
//   } finally {
//       argon2.wipeArray(password)
//   }
```

**Note**: 직접 구현 절대 금지. `argon2-jvm` 또는 BouncyCastle 사용. 비밀번호 char array는 사용 후 wipe.

**관련 알고리즘**: Bcrypt, scrypt, Balloon

---

<a id="ecc"></a>
## 7. ECC (Elliptic Curve Cryptography — ECDSA / Ed25519 / ECDH)

**목적**: 타원곡선 이산로그 문제(ECDLP) 기반 공개키 암호 — 서명(ECDSA/EdDSA)과 키 교환(ECDH)

**시간 복잡도**: 키 생성·서명·검증 모두 스칼라 곱 O(키 비트 길이) — RSA 대비 동등 보안에서 키·연산이 수 배 작음

**공간 복잡도**: 키 256-bit (RSA 3072-bit 와 동등 보안)

**특징**:
- 동등 보안에서 키가 훨씬 작음: ECC 256-bit ≈ RSA 3072-bit ≈ AES-128
- ECDSA(P-256 / secp256k1), EdDSA(Ed25519, RFC 8032), ECDH / X25519(RFC 7748)
- TLS 1.3 · JWT(ES256/EdDSA) · SSH · 코드사이닝 · 블록체인 서명의 사실상 표준
- Ed25519 는 결정적 서명(난수 재사용 취약 회피) · 상수시간 구현으로 권장

**장점**:
- 작은 키·서명·빠른 연산 (모바일/IoT 유리)
- forward secrecy 키 교환(ECDHE)에 적합
- Ed25519 는 misuse-resistant

**단점**:
- 곡선·구현 선택 민감 (약한 곡선·nonce 재사용 시 키 유출)
- ECDSA 는 난수 품질에 취약(PS3 사고) → RFC 6979 결정적 nonce 권장
- 직접 구현 금지(사이드채널)

**활용 예시**:
- TLS 1.3 핸드셰이크(X25519 + Ed25519/ECDSA)
- JWT 서명(ES256/EdDSA), SSH 키, 코드사이닝
- 블록체인 지갑 서명(secp256k1)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import java.security.*
import java.security.spec.ECGenParameterSpec

// ECDSA (P-256) 서명/검증 — JCA 표준
fun ecdsaDemo(data: ByteArray): Boolean {
    val kpg = KeyPairGenerator.getInstance("EC").apply {
        initialize(ECGenParameterSpec("secp256r1")) // P-256
    }
    val kp = kpg.generateKeyPair()

    val signer = Signature.getInstance("SHA256withECDSA")
    signer.initSign(kp.private); signer.update(data)
    val sig = signer.sign()

    val verifier = Signature.getInstance("SHA256withECDSA")
    verifier.initVerify(kp.public); verifier.update(data)
    return verifier.verify(sig)
}

// ECDH 키 합의 (공유 비밀 도출) — javax.crypto.KeyAgreement
fun ecdhShared(self: KeyPair, peerPub: PublicKey): ByteArray {
    val ka = javax.crypto.KeyAgreement.getInstance("ECDH")
    ka.init(self.private); ka.doPhase(peerPub, true)
    return ka.generateSecret() // 이후 HKDF 로 세션키 유도
}
// Ed25519: KeyPairGenerator.getInstance("Ed25519") + Signature.getInstance("Ed25519") (JDK 15+)
```

**Note**: 직접 구현 금지 — JCA / BouncyCastle / libsodium 사용. ECDSA 는 RFC 6979 결정적 nonce, 키 교환은 X25519 권장. nonce/난수 재사용은 개인키 유출로 직결된다.

**관련 알고리즘**: RSA, Diffie-Hellman, SHA-256, AES

---

<a id="diffie-hellman"></a>
## 8. Diffie-Hellman (디피-헬먼 키 교환)

**목적**: 공개 채널에서 사전 공유 비밀 없이 두 당사자가 공통 대칭키를 합의 (이산로그 난해성 기반)

**시간 복잡도**: 모듈러 거듭제곱 O(log n) 지수 연산

**공간 복잡도**: O(키 비트 길이)

**특징**:
- 모든 키 교환의 원형 (Diffie-Hellman 1976) — g^a, g^b → g^ab
- 유한체 DH(FFDHE) vs 타원곡선 DH(ECDH / X25519)
- 임시(ephemeral) DHE / ECDHE 로 forward secrecy 제공
- 미인증 DH 는 중간자(MITM) 취약 → 서명/인증서로 인증 필요

**장점**:
- 사전 공유 비밀 불필요, forward secrecy(임시 키)
- TLS · IPsec · Signal 등 키 합의의 토대

**단점**:
- 미인증 시 MITM 취약 (반드시 인증된 DH 사용)
- 약한 파라미터(작은/공유 소수)·Logjam 공격 → ≥2048-bit FFDHE 또는 X25519
- 직접 구현 금지

**활용 예시**:
- TLS 1.3 키 합의(ECDHE / X25519)
- VPN/IPsec, Signal 프로토콜(X3DH)
- 종단간 암호화 세션 키 수립

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import javax.crypto.KeyAgreement
import java.security.KeyPairGenerator

// X25519 키 합의 (JDK 11+) — 권장 ECDH 변형
fun x25519Shared(): ByteArray {
    val kpg = KeyPairGenerator.getInstance("X25519")
    val alice = kpg.generateKeyPair()
    val bob = kpg.generateKeyPair()

    val ka = KeyAgreement.getInstance("X25519")
    ka.init(alice.private)
    ka.doPhase(bob.public, true)
    return ka.generateSecret()   // 32바이트 공유 비밀 → HKDF 로 세션키 유도
}
// 고전 유한체 DH: KeyPairGenerator.getInstance("DH") + DHParameterSpec(≥2048-bit)
```

**Note**: 미인증 DH 는 MITM 에 무력 — 서명/인증서로 양단 인증 필수. 임시키(ECDHE/DHE)로 forward secrecy 확보. 파라미터는 X25519 또는 ≥2048-bit FFDHE.

**관련 알고리즘**: ECC, RSA, AES, HMAC

---

<a id="chacha20-poly1305"></a>
## 9. ChaCha20-Poly1305 (스트림 AEAD)

**목적**: ChaCha20 스트림 암호와 Poly1305 MAC을 결합해 기밀성·무결성·인증을 한 번에 제공하는 AEAD(인증 암호화) 구성

**시간 복잡도**: O(n) - n: 평문 바이트 수 (블록당 고정 라운드 수)

**공간 복잡도**: O(1) - 256-bit key, 320-bit state, 256-bit Poly1305 누적기 (입출력 버퍼 제외)

**특징**:
- RFC 8439 표준 AEAD. ChaCha20(Daniel J. Bernstein, 2008, Salsa20 변형)으로 키스트림 생성 + Poly1305로 인증 태그(16바이트) 생성
- ChaCha20은 ARX 연산(Add-Rotate-XOR, 20라운드)만 사용 — AES 하드웨어(AES-NI) 없이도 소프트웨어에서 상수시간 구현이 용이
- 기본 nonce는 96-bit(12바이트), 블록 카운터 32-bit. AAD(Additional Authenticated Data)는 암호화하지 않고 인증만 수행
- 변형 XChaCha20-Poly1305는 192-bit(24바이트) nonce를 사용 — HChaCha20으로 서브키를 파생해 nonce 무작위 생성을 안전하게 허용 (RFC 표준은 아니나 libsodium 등에서 널리 채택)
- 복호화 시 태그를 먼저 검증하고 불일치하면 평문을 반환하지 않음 (encrypt-then-MAC 구조)

**장점**:
- AES-NI 같은 전용 하드웨어가 없는 환경(모바일·저전력·임베디드)에서 AES-GCM보다 빠르고 전력 효율이 좋음
- 타이밍 공격 저항성 — 테이블 룩업이 없어 소프트웨어 상수시간 구현이 자연스러움
- AES-GCM의 nonce 충돌만큼 치명적이지 않은 단순한 카운터 설계, RFC 8439로 명세가 명확

**단점**:
- nonce 재사용 시 키스트림이 동일해져 평문이 노출되고 Poly1305 키가 드러나 위조까지 가능 (96-bit nonce는 무작위 사용 시 충돌 위험)
- 96-bit nonce는 동일 키로 안전하게 처리 가능한 메시지 수에 한계가 있어 키 로테이션 또는 XChaCha20 필요
- AES-NI가 있는 서버 CPU에서는 하드웨어 가속 AES-GCM이 더 빠를 수 있음

**활용 예시**:
- TLS 1.3 암호 스위트 (TLS_CHACHA20_POLY1305_SHA256), 특히 모바일 클라이언트
- WireGuard VPN, SSH, QUIC 등 최신 프로토콜의 기본/대체 AEAD
- libsodium 기반 애플리케이션 레벨 암호화 (메시지·파일 봉인)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import javax.crypto.Cipher
import javax.crypto.spec.SecretKeySpec
import javax.crypto.spec.IvParameterSpec
import java.security.SecureRandom

// JDK 11+ 내장 "ChaCha20-Poly1305" 프로바이더 사용 (직접 구현 금지)
// key: 32바이트(256-bit), nonce: 12바이트(96-bit) — nonce는 키당 절대 재사용 금지
object ChaCha20Poly1305Aead {
    private const val NONCE_SIZE = 12          // 96-bit nonce

    fun newKey(): ByteArray = ByteArray(32).also { SecureRandom().nextBytes(it) }

    // 암호화: 평문 -> nonce || ciphertext+tag (태그 16바이트는 ciphertext 끝에 부착됨)
    fun encrypt(key: ByteArray, plaintext: ByteArray, aad: ByteArray): ByteArray {
        val nonce = ByteArray(NONCE_SIZE).also { SecureRandom().nextBytes(it) }
        val cipher = Cipher.getInstance("ChaCha20-Poly1305")
        cipher.init(Cipher.ENCRYPT_MODE, SecretKeySpec(key, "ChaCha20"), IvParameterSpec(nonce))
        cipher.updateAAD(aad)                  // AAD는 인증만, 암호화하지 않음
        return nonce + cipher.doFinal(plaintext)
    }

    // 복호화: 태그 검증 실패 시 AEADBadTagException 발생 -> 평문 미반환
    fun decrypt(key: ByteArray, blob: ByteArray, aad: ByteArray): ByteArray {
        val nonce = blob.copyOfRange(0, NONCE_SIZE)
        val ct = blob.copyOfRange(NONCE_SIZE, blob.size)
        val cipher = Cipher.getInstance("ChaCha20-Poly1305")
        cipher.init(Cipher.DECRYPT_MODE, SecretKeySpec(key, "ChaCha20"), IvParameterSpec(nonce))
        cipher.updateAAD(aad)
        return cipher.doFinal(ct)              // 태그 불일치면 예외
    }
}
```

**Note**: AEAD 구성을 직접 구현하지 말고 JDK 11+ 내장 프로바이더, libsodium, BouncyCastle 등 검증된 라이브러리를 사용한다. 가장 치명적인 실수는 동일 key로 nonce를 재사용하는 것 — 평문 노출과 태그 위조로 이어지므로 nonce는 카운터 또는 안전한 난수로 유일성을 보장하고, 무작위 nonce 충돌이 우려되면 192-bit nonce의 XChaCha20-Poly1305를 사용한다.

**관련 알고리즘**: AES-GCM, AES, HMAC, SHA-256

---

<a id="sha-3"></a>
## 10. SHA-3 / Keccak (SHA-3 스펀지 해시)

**목적**: 임의 길이 입력을 스펀지(sponge) 구조로 흡수·압출해 고정 길이 해시(또는 가변 길이 출력)로 변환

**시간 복잡도**: O(n) - n: 입력 바이트 수

**공간 복잡도**: O(1) - 1600비트 고정 상태(state) 사용

**특징**:
- Keccak 이 NIST SHA-3 공모전 우승(2012), FIPS 202 로 표준화(2015) — 설계: Bertoni, Daemen, Peeters, Van Assche
- 스펀지 구조: 1600비트 상태를 rate r + capacity c 로 분할, absorb(입력을 r 비트씩 XOR 후 permutation) → squeeze(r 비트씩 출력) 두 단계
- 코어 순열 Keccak-f[1600] 은 θ·ρ·π·χ·ι 다섯 단계를 24라운드 반복 (SHA-2 의 Merkle-Damgård 압축 함수와 전혀 다른 설계)
- capacity 부분(c 비트)은 절대 외부로 출력되지 않아 길이 확장 공격(length-extension)에 면역 — SHA-2 와의 핵심 차이
- 변형별 rate/capacity: SHA3-256(r=1088, c=512), SHA3-512(r=576, c=1024); capacity = 출력×2 로 충돌 저항성 확보. SHAKE128/SHAKE256 은 가변 길이 출력 XOF

**장점**:
- 길이 확장 공격에 구조적으로 안전 (HMAC 없이도 키 접두 MAC 가능)
- SHA-2 와 설계 계열이 달라 암호 다양성(diversity) 확보 — SHA-2 가 깨져도 대안
- SHAKE XOF 로 임의 길이 출력 지원 (KDF, 마스크 생성, 스트림 등)

**단점**:
- 소프트웨어 처리량이 SHA-256/BLAKE2 보다 느린 편 (전용 하드웨어·SHA-3 명령에서 개선)
- 아직 SHA-256 만큼 광범위하게 배포·내장되지는 않음
- 직접 구현 시 비트 정렬·순열 상수 오류로 보안이 쉽게 깨짐

**활용 예시**:
- 길이 확장 면역이 필요한 무결성·서명 (Ethereum 은 Keccak-256 변형 사용)
- SHAKE256 기반 키 유도·마스크 생성(MGF)·난수 확장
- 포스트양자 서명(SPHINCS+ 등)·KMAC(SHA-3 기반 MAC)의 내부 구성 요소
- SHA-2 와 병행한 다중 해시 무결성 검증

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.security.MessageDigest

// SHA3-256: JDK 9+ 표준 SUN 프로바이더에 내장
fun sha3_256(input: ByteArray): ByteArray {
    val digest = MessageDigest.getInstance("SHA3-256")
    return digest.digest(input)
}

fun sha3_256Hex(input: String): String {
    val bytes = sha3_256(input.toByteArray(Charsets.UTF_8))
    return bytes.joinToString("") { "%02x".format(it) }
}

// 큰 파일 스트리밍 해싱 (스펀지 absorb 단계가 update 로 반복됨)
fun sha3Streaming(stream: java.io.InputStream): ByteArray {
    val digest = MessageDigest.getInstance("SHA3-512")
    val buffer = ByteArray(8192)
    while (true) {
        val read = stream.read(buffer)
        if (read <= 0) break
        digest.update(buffer, 0, read)   // absorb
    }
    return digest.digest()               // pad → squeeze
}

// 알고리즘 단계 (개념용 — 직접 구현 금지):
// 1. 1600비트 상태 = rate r + capacity c (SHA3-256: r=1088, c=512)
// 2. absorb: 입력을 r 비트 블록으로 나눠 상태 앞 r 비트에 XOR 후 Keccak-f[1600] 적용
// 3. 패딩: 다중비율 패딩 pad10*1 (SHA-3 은 도메인 구분자 0x06, SHAKE 는 0x1F)
// 4. squeeze: 상태 앞 r 비트를 출력으로 꺼내고 부족하면 다시 permutation 반복
// 5. capacity c 비트는 절대 출력 안 함 → 길이 확장 공격 면역
// 6. Keccak-f 순열 = θ·ρ·π·χ·ι 5단계 × 24라운드

// SHAKE128/256(XOF, 가변 길이 출력)은 BouncyCastle 필요:
//   val xof = org.bouncycastle.crypto.digests.SHAKEDigest(256)
//   xof.update(msg, 0, msg.size)
//   val out = ByteArray(64); xof.doFinal(out, 0, out.size)
```

**Note**: 직접 구현 금지. SHA3-224/256/384/512 는 JDK 9+ 의 `MessageDigest` 사용, SHAKE128/256 XOF 나 KMAC 은 BouncyCastle 사용. 참고로 Ethereum 의 keccak256 은 패딩 도메인 구분자가 다른 원본 Keccak 으로, FIPS 202 SHA3-256 과 출력이 다르다.

**관련 알고리즘**: SHA-256, BLAKE2, HMAC, KMAC

---

<a id="blake2-blake3"></a>
## 11. BLAKE2 / BLAKE3 (고속 암호 해시)

**목적**: SHA-2/SHA-3 수준의 보안을 유지하면서 더 빠른 속도로 메시지 다이제스트를 생성하고, keyed 모드로 MAC·KDF·XOF까지 겸하기

**시간 복잡도**: O(n) - n: 입력 바이트 수 (BLAKE3는 트리 구조로 멀티코어 병렬화 가능)

**공간 복잡도**: O(1) - 고정 크기 내부 상태 (BLAKE3 트리는 추가로 O(log n) 체인 스택)

**특징**:
- BLAKE2는 SHA-3 최종 후보였던 BLAKE에서 파생(2012), ChaCha 기반 압축 함수를 사용하며 BLAKE2b(64비트 워드, 최대 512비트 출력)와 BLAKE2s(32비트 워드, 최대 256비트 출력)로 나뉨
- BLAKE2는 별도 HMAC 구성 없이 keyed mode로 MAC을 직접 지원하고, salt·personalization·트리 해싱 파라미터를 내장
- BLAKE3(2020)는 1KiB 청크 단위 Merkle 트리 해시 구조로 멀티코어·SIMD(AVX-512, NEON) 병렬 처리를 지원
- BLAKE3는 단일 알고리즘으로 일반 해시, keyed hash(MAC), KDF(derive_key), XOF(임의 길이 출력)를 모두 제공하며 기본 출력은 256비트
- 모든 변형은 length-extension 공격에 면역(SHA-256 같은 plain Merkle-Damgård와 달리 안전)

**장점**:
- SHA-256 대비 소프트웨어에서 수 배 빠르며, BLAKE3는 병렬화로 대용량 입력에서 특히 우수
- length-extension 안전, keyed/salt/personalization 등 실무 기능 내장
- BLAKE3는 증분·병렬·검증 가능한(verified streaming) 트리 구조 제공

**단점**:
- SHA-2/SHA-3만큼 표준화·하드웨어 가속(AES-NI 유사)이 보편적이지 않음 (BLAKE2는 RFC 7693 존재)
- 일부 규제·인증 환경(FIPS 등)에서 미승인일 수 있어 채택 제약
- 암호 해시이므로 비밀번호 저장에는 부적합 — Argon2/bcrypt 같은 의도적 느린 KDF 필요

**활용 예시**:
- 파일 무결성 검증·콘텐츠 주소 지정(content-addressed storage), 중복 제거
- Git 류 버전 관리·CDN의 대용량 객체 해싱(BLAKE3 병렬성 활용)
- keyed mode를 이용한 메시지 인증(MAC)과 키 파생(KDF)

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 개념 시연: BLAKE2b 핵심(G 함수 + 압축)을 단순화해 보여준다.
// 실제 서비스에는 검증된 라이브러리(BouncyCastle Blake2bDigest / blake3 lib) 사용 권장.
object Blake2bDemo {
    // BLAKE2b IV (SHA-512 IV와 동일)
    private val IV = longArrayOf(
        0x6a09e667f3bcc908L, -0x4498517a7b3558c5L, 0x3c6ef372fe94f82bL, -0x5ab00ac5a0e2c90fL,
        0x510e527fade682d1L, -0x64fa9773d4c193e1L, 0x1f83d9abfb41bd6bL, 0x5be0cd19137e2179L
    )
    // 메시지 워드 순열(SIGMA) 한 라운드 예시(전체 12라운드 중 일부 개념만)
    private val SIGMA0 = intArrayOf(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)

    // G 혼합 함수: a,b,c,d 워드를 메시지 x,y와 섞는다 (회전 상수 32,24,16,63)
    private fun g(v: LongArray, a: Int, b: Int, c: Int, d: Int, x: Long, y: Long) {
        v[a] += v[b] + x; v[d] = (v[d] xor v[a]).rotateRight(32)
        v[c] += v[d];     v[b] = (v[b] xor v[c]).rotateRight(24)
        v[a] += v[b] + y; v[d] = (v[d] xor v[a]).rotateRight(16)
        v[c] += v[d];     v[b] = (v[b] xor v[c]).rotateRight(63)
    }

    // 한 블록(128B = 16 워드) 압축의 핵심 1라운드 시연
    fun compressRound(h: LongArray, m: LongArray): LongArray {
        val v = LongArray(16) { if (it < 8) h[it] else IV[it - 8] }
        val s = SIGMA0
        // 열 단위 혼합
        g(v, 0, 4,  8, 12, m[s[0]],  m[s[1]])
        g(v, 1, 5,  9, 13, m[s[2]],  m[s[3]])
        g(v, 2, 6, 10, 14, m[s[4]],  m[s[5]])
        g(v, 3, 7, 11, 15, m[s[6]],  m[s[7]])
        // 대각선 단위 혼합
        g(v, 0, 5, 10, 15, m[s[8]],  m[s[9]])
        g(v, 1, 6, 11, 12, m[s[10]], m[s[11]])
        g(v, 2, 7,  8, 13, m[s[12]], m[s[13]])
        g(v, 3, 4,  9, 14, m[s[14]], m[s[15]])
        return LongArray(8) { h[it] xor v[it] xor v[it + 8] }
    }
}
```

**Note**: 암호 해시를 직접 구현하지 말고 RFC 7693(BLAKE2)·공식 BLAKE3 명세 기반의 검증된 라이브러리(BouncyCastle, blake3-jvm 등)를 사용하라. 비밀번호 해싱에는 BLAKE 계열이 아니라 Argon2/bcrypt 같은 의도적으로 느린 전용 KDF를 써야 한다.

**관련 알고리즘**: SHA-256, SHA-3 / Keccak, HMAC, Argon2

---

<a id="scrypt-pbkdf2"></a>
## 12. scrypt / PBKDF2 (키 유도 함수 (KDF))

**목적**: 저엔트로피 비밀번호를 의도적으로 느리고(비용 조절 가능) 충돌 저항적인 암호 키/해시로 변환하는 패스워드 기반 KDF — PBKDF2(반복 HMAC)와 scrypt(메모리 하드)

**시간 복잡도**: PBKDF2 = O(c · L) — c: 반복 횟수, L: 출력 블록 수 / scrypt = O(N · r) PRF 호출 (N: 비용 파라미터)

**공간 복잡도**: PBKDF2 = O(1) / scrypt = O(N · r · 128) 바이트 — 의도적으로 큰 메모리 사용

**특징**:
- PBKDF2 (RFC 8018, PKCS#5 v2.1): DK = T₁‖T₂‖… , Tᵢ = F(P, S, c, i), F는 HMAC을 c회 반복 XOR 누적 — FIPS 140 승인 알고리즘
- scrypt (RFC 7914, Percival 2009): PBKDF2(HMAC-SHA256)로 초기 블록 생성 → ROMix/BlockMix(Salsa20/8 코어)로 N개의 의사난수 블록을 메모리에 채워 무작위 접근 → 메모리 점유 강제
- PBKDF2는 CPU-bound만 가능해 GPU/ASIC 병렬화에 상대적으로 약하고, scrypt는 메모리 대역폭을 강제해 GPU/ASIC 병렬 비용을 끌어올림 (memory-hard)
- scrypt 파라미터: N(CPU/메모리 비용, 2의 거듭제곱), r(블록 크기), p(병렬화) — 권장 N=2^15(32768), r=8, p=1
- Argon2(2015 PHC 우승)가 메모리·시간·병렬성을 독립 조정하며 더 강력 — 신규 시스템은 Argon2id 우선, PBKDF2/scrypt는 FIPS 요구·레거시 호환 시 사용

**장점**:
- PBKDF2: FIPS/NIST 승인, 표준 JDK(`SecretKeyFactory`) 내장, 광범위한 라이브러리 지원
- scrypt: 메모리 하드로 GPU/ASIC 대량 공격 비용 급증
- 둘 다 salt + 반복 비용으로 레인보우 테이블·무차별 대입 방어
- 비용 파라미터를 하드웨어 발전에 맞춰 상향 조정 가능

**단점**:
- PBKDF2: 메모리 하드가 아니라 GPU/ASIC 병렬 공격에 scrypt/Argon2보다 취약
- scrypt: 메모리·시간·병렬성을 단일 N으로 묶어 Argon2보다 튜닝 유연성 낮음, 표준 JDK 미포함(외부 라이브러리 필요)
- 파라미터를 낮게 잡으면 보호 효과 무력화 — 주기적 상향 필요
- 직접 구현 시 타이밍·구현 결함 위험

**활용 예시**:
- 사용자 비밀번호 저장 (DB) 및 인증 시스템
- 비밀번호 기반 디스크/파일 암호화 키 유도 (예: 암호화폐 지갑, scrypt 사용 사례)
- WPA2 PSK(PBKDF2-HMAC-SHA1), 1Password/LastPass 등 비밀번호 관리자
- FIPS 준수가 요구되는 정부·금융 시스템(PBKDF2)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec
import java.security.SecureRandom
import java.util.Base64

// PBKDF2 — 표준 JDK(SecretKeyFactory)로 직접 호출 가능
fun pbkdf2Hash(password: CharArray, iterations: Int = 600_000, keyBits: Int = 256): String {
    val salt = ByteArray(16).also { SecureRandom().nextBytes(it) }
    val spec = PBEKeySpec(password, salt, iterations, keyBits)       // F = HMAC을 c회 반복
    val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
    val dk = factory.generateSecret(spec).encoded
    val b64 = Base64.getEncoder()
    return "pbkdf2_sha256\$$iterations\$${b64.encodeToString(salt)}\$${b64.encodeToString(dk)}"
}

fun pbkdf2Verify(password: CharArray, stored: String): Boolean {
    val (algo, iterStr, saltB64, hashB64) = stored.split("$").let {
        if (it.size != 4) return false; it
    }
    if (algo != "pbkdf2_sha256") return false
    val salt = Base64.getDecoder().decode(saltB64)
    val expected = Base64.getDecoder().decode(hashB64)
    val spec = PBEKeySpec(password, salt, iterStr.toInt(), expected.size * 8)
    val actual = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
        .generateSecret(spec).encoded
    // 상수 시간 비교 (타이밍 공격 방어)
    if (actual.size != expected.size) return false
    var diff = 0
    for (i in actual.indices) diff = diff or (actual[i].toInt() xor expected[i].toInt())
    return diff == 0
}

// scrypt 는 표준 JDK 미포함 — BouncyCastle 사용 (개념 시연):
//   import org.bouncycastle.crypto.generators.SCrypt
//   val salt = ByteArray(16).also { SecureRandom().nextBytes(it) }
//   val dk = SCrypt.generate(passwordBytes, salt, 32768, 8, 1, 32) // N=2^15, r=8, p=1
```

**Note**: 직접 구현 금지 — PBKDF2는 `SecretKeyFactory("PBKDF2WithHmacSHA256")`, scrypt는 BouncyCastle을 사용하세요. 반드시 충분한 비용 파라미터(PBKDF2 ≥ OWASP 권장 600,000회, scrypt N≥2^15)와 무작위 salt(≥16바이트)를 적용하고, 신규 시스템은 가능하면 Argon2id를 우선 고려하세요.

**관련 알고리즘**: Argon2, Bcrypt, HMAC, SHA-256
