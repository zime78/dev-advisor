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
