# 모바일 앱 보안 패턴 (Mobile App Security)

iOS/Android 앱 고유의 위협 모델 (장치 압수, MITM, 변조, 디바이스 무결성 실패) 에 대응하는 보안 패턴. OWASP MASVS (Mobile Application Security Verification Standard) 기반. Apple Platform Security Guide / Android Security Bulletins / OWASP Mobile Top 10 도 참조.

---

## 1. Certificate Pinning (인증서 핀닝)

**목적**: TLS 핸드셰이크 시 서버가 제출하는 인증서(또는 공개키)를 앱에 내장된 값과 비교·검증하여, CA(인증기관) 체계가 침해되거나 기기에 신뢰 CA가 설치되었을 때 발생하는 MITM(중간자) 공격을 방어합니다.

**특징**:
- **Leaf Pinning**: 서버 최종 인증서 고정 → 단순하지만 만료 시 앱 업데이트 필수
- **Intermediate Pinning**: 중간 CA 인증서 고정 → Leaf보다 수명 길고 갱신 유연
- **SPKI Hash Pinning (권장)**: 인증서가 아닌 SubjectPublicKeyInfo(공개키) SHA-256 해시 고정 → 인증서 재발급 시에도 동일 키 유지하면 핀 유효
- **Pin Rotation 전략**: 현재 핀 1개 + 백업 핀 1개 이상 → 백업 핀 활성화 후 현재 핀 교체, 앱 업데이트 강제 없이 교체 가능
- Android: OkHttp `CertificatePinner`, Conscrypt, Network Security Config XML
- iOS: `NSPinnedDomains` (Info.plist), `URLSession` custom `URLAuthenticationChallenge` 핸들러, TrustKit 라이브러리

**장점**:
- CA 시스템 전체 타협(예: DigiNotar 사건) 시에도 보호
- 프록시 툴(Charles, mitmproxy) + 사용자 설치 CA로 인한 트래픽 분석 차단
- 금융/의료 규제 환경에서 통신 무결성 보증

**단점**:
- 인증서 갱신·키 교체 시 앱 업데이트 또는 백업 핀 사전 배포 필요
- 방어적 우회(Frida, SSLUnpinning Xposed) 가능 — 루팅/탈옥 기기에선 핀닝 자체가 우회됨
- CDN 사용 시 적용 복잡 (CDN이 인증서 소유, SPKI 협의 필요)

**활용 예시**:
- 뱅킹·증권 앱 API 통신 보호
- 인증 토큰 발급 엔드포인트에만 선별 적용 (전체 적용은 운영 리스크 큼)
- 내부 MDM 관리 기기 앱

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin (Android) 예제 — OkHttp CertificatePinner + 백업 핀**:
```kotlin
import okhttp3.CertificatePinner
import okhttp3.OkHttpClient

// SPKI 해시 추출: openssl x509 -in cert.pem -pubkey -noout | openssl pkey -pubin -outform DER | openssl dgst -sha256 -binary | base64
private const val PIN_CURRENT = "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
private const val PIN_BACKUP  = "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="

/**
 * Certificate Pinning이 적용된 OkHttpClient 생성.
 * 두 개의 핀(현재 + 백업)을 등록하여 pin rotation 시 앱 업데이트 없이 교체 가능.
 */
fun buildPinnedHttpClient(): OkHttpClient {
    val pinner = CertificatePinner.Builder()
        .add("api.example.com", PIN_CURRENT, PIN_BACKUP) // 두 핀 중 하나 일치 시 통과
        .add("auth.example.com", PIN_CURRENT, PIN_BACKUP)
        .build()

    return OkHttpClient.Builder()
        .certificatePinner(pinner)
        // SSLPinningException 발생 시 앱이 사용자에게 "보안 연결 실패" 표시 권장
        .build()
}

// 핀 불일치(SSLPeerUnverifiedException) 시 처리
fun safeCall(client: OkHttpClient, request: okhttp3.Request): Result<String> = runCatching {
    client.newCall(request).execute().use { it.body!!.string() }
}.onFailure { e ->
    if (e is javax.net.ssl.SSLPeerUnverifiedException) {
        // 분석팀에 알람 발송 — 실제 MITM 공격 또는 핀 만료 신호
        securityEventBus.publish(SecurityEvent.PinMismatch(request.url.host, e.message))
    }
}
```

**Swift (iOS) 예제 — NSPinnedDomains (Info.plist)**:
```xml
<!-- Info.plist — NSAppTransportSecurity 아래 NSPinnedDomains 설정 -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSPinnedDomains</key>
    <dict>
        <key>api.example.com</key>
        <dict>
            <key>NSIncludesSubdomains</key><true/>
            <key>NSPinnedLeafIdentities</key>
            <array>
                <dict>
                    <key>SPKI-SHA256-BASE64</key>
                    <string>AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=</string>
                </dict>
                <!-- 백업 핀 -->
                <dict>
                    <key>SPKI-SHA256-BASE64</key>
                    <string>BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=</string>
                </dict>
            </array>
        </dict>
    </dict>
</dict>
```

**관련 패턴**: App Attest / Play Integrity, RASP, Jailbreak / Root Detection

---

## 2. App Attest / Play Integrity (앱·디바이스 무결성 증명)

**목적**: 클라이언트 앱이 변조되지 않은 공식 빌드인지, 탈옥·루팅되지 않은 정상 기기에서 실행 중인지를 플랫폼 제공 하드웨어 기반 증명(attestation)으로 서버에 검증합니다.

**특징**:
- **Apple App Attest (iOS 14+)**: Secure Enclave에서 앱 서명 기반 assertion key 생성 → Apple 서버에서 인증서 발급 → 앱이 서버에 assertion 제출 → 서버가 Apple 공개키로 검증
  - `DCAppAttestService.generateKey()` → `attestKey()` → 서버 등록 → 이후 요청마다 `generateAssertion()`
- **Google Play Integrity API (Android)**: Play Services에서 Integrity Token 발급 → 서버가 Google 서버로 token 검증 → `deviceIntegrity`, `appIntegrity`, `accountDetails` 판정 필드 반환
  - `MEETS_DEVICE_INTEGRITY`: 비루팅 정품 기기
  - `MEETS_STRONG_INTEGRITY`: 하드웨어 증명 지원 (픽셀 등)
  - `MEETS_VIRTUAL_INTEGRITY`: 에뮬레이터 (테스트 시 허용 결정 필요)
- **Fraud Signals**: 루팅 기기, 리패키징 앱, 에뮬레이터, ADB 디버깅 활성 등

**장점**:
- 플랫폼 HW(Secure Enclave / Titan M)에 루팅되어 있어 소프트웨어 우회 불가에 가까움
- 리패키징(앱 변조 후 재배포) 탐지
- 봇·자동화 스크립트의 API 남용 방어

**단점**:
- 네트워크 호출 필수 → 지연 추가 (assertion 생성: ~100ms)
- Apple의 경우 1일 어설션 키 사용 한도 존재 → 캐싱 설계 필요
- Google Play Services 미탑재 기기(국내 일부 기기, 구형 폰)에서 동작하지 않음
- Attestation 결과는 요청 시점 판정 — 앱 실행 중 상태 변화 미반영

**활용 예시**:
- 금융 앱 로그인/거래 시 서버 사이드 attestation 검증
- 티켓팅 앱 — 봇 방지
- 고가치 게임 아이템 구매 API

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin (Android) 예제 — Play Integrity API 서버 검증 흐름**:
```kotlin
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.IntegrityTokenRequest

/**
 * Play Integrity 토큰 요청 → 서버 전달.
 * nonce는 서버가 생성한 challenge (재사용 방지).
 */
class IntegrityChecker(private val context: Context, private val api: BackendApi) {

    fun checkAndProceed(serverNonce: String, onSuccess: () -> Unit, onFail: (String) -> Unit) {
        val integrityManager = IntegrityManagerFactory.create(context)
        val request = IntegrityTokenRequest.builder()
            .setNonce(serverNonce)               // 서버 발급 1회용 nonce
            .setCloudProjectNumber(123456789L)   // Google Cloud 프로젝트 번호
            .build()

        integrityManager.requestIntegrityToken(request)
            .addOnSuccessListener { response ->
                // 서버에 토큰 전달 — 서버가 Google API로 검증
                api.verifyIntegrity(response.token()) { result ->
                    when (result.verdict) {
                        "MEETS_DEVICE_INTEGRITY" -> onSuccess()
                        "MEETS_VIRTUAL_INTEGRITY" -> onFail("에뮬레이터에서는 사용 불가")
                        else -> onFail("기기 무결성 검증 실패")
                    }
                }
            }
            .addOnFailureListener { e -> onFail("Integrity API 오류: ${e.message}") }
    }
}

// 서버 측 검증 (Kotlin/Go/Node 어디서든 동일)
// POST https://playintegrity.googleapis.com/v1/{packageName}:decodeIntegrityToken
// 응답의 deviceIntegrity.deviceRecognitionVerdict 배열로 판정
```

**관련 패턴**: Certificate Pinning, Jailbreak / Root Detection, RASP

---

## 3. Jailbreak / Root Detection (탈옥 및 루팅 탐지)

**목적**: iOS 탈옥(jailbreak) 또는 Android 루팅(root)된 기기를 탐지하여, 플랫폼 보안 모델이 훼손된 환경에서의 앱 실행을 차단하거나 고위험으로 분류합니다.

**특징**:
- **iOS Jailbreak 탐지 휴리스틱**:
  - 파일 시스템 흔적: `/Applications/Cydia.app`, `/usr/sbin/sshd`, `/etc/apt`, `/private/var/lib/apt/` 존재 여부
  - Sandbox escape 시도: `/private/jailbreak_test` 쓰기 성공 여부
  - URL scheme: `cydia://` 열기 응답 여부
  - Dynamic library 주입: `DYLD_INSERT_LIBRARIES` 환경변수, `dyld_get_image_name()` 으로 비서명 dylib 탐지
- **Android Root 탐지 휴리스틱**:
  - 파일 존재: `/system/app/Superuser.apk`, `/system/xbin/su`, `/sbin/su`
  - `su` 실행 가능 여부 (Process exception 또는 성공 여부)
  - Build 태그: `android.os.Build.TAGS.contains("test-keys")`
  - RootBeer / SafetyNet / Play Integrity 라이브러리 활용
- **중요**: 결정적 탐지는 불가능 — 모든 탐지 기법은 우회 수단 존재 (Frida, Magisk Hide, Liberty Lite)

**장점**:
- 대다수 일반 사용자의 무의식적 변조 환경 차단
- 층위 방어의 한 레이어 — 단독으로 믿어서는 안 됨
- 앱 스토어 가이드라인 준수 필요 시 환경 증거 수집

**단점**:
- 탐지 우회 도구(Magisk Hide, Shadow) 공개 존재 — 100% 신뢰 불가
- 정상 루팅 사용자(개발자, 커스텀 ROM) 차단으로 오탐 발생 가능
- Apple/Google 정책으로 일부 탐지 API 사용 제한
- 보안 연구자, 접근성 도구 사용자 차단 가능성

**활용 예시**:
- 뱅킹 앱: 탐지 시 앱 실행 차단 또는 기능 제한
- MDM 관리 기업 앱: 탈옥 기기는 업무 프로파일 미적용
- 게임 앱: 루팅 탐지 → 치트 방지 레이어 활성화

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin (Android) 예제 — 다계층 Root 탐지**:
```kotlin
import java.io.File

/**
 * Android root 탐지 — 여러 휴리스틱을 조합해 신뢰도를 점수로 표현.
 * 단일 신호보다 복수 신호 중첩 시 차단 결정 권장.
 */
object RootDetector {

    private val SU_PATHS = listOf(
        "/system/bin/su", "/system/xbin/su", "/sbin/su",
        "/system/su", "/system/bin/.ext/.su", "/system/usr/we-need-root/su-backup",
    )
    private val KNOWN_ROOT_APPS = listOf(
        "/system/app/Superuser.apk", "/system/app/SuperSU.apk",
        "/data/app/eu.chainfire.supersu", "/data/app/com.topjohnwu.magisk",
    )

    /** 루트 위험 점수 반환 (0 = 정상, 100+ = 고위험) */
    fun calculateRiskScore(): Int {
        var score = 0

        // 1) su 바이너리 존재 확인
        if (SU_PATHS.any { File(it).exists() }) score += 40

        // 2) 루트 앱 APK 존재 확인
        if (KNOWN_ROOT_APPS.any { File(it).exists() }) score += 30

        // 3) build 태그 확인 (test-keys = AOSP 개발빌드 or 루팅 가능성)
        if (android.os.Build.TAGS?.contains("test-keys") == true) score += 20

        // 4) su 명령 실행 가능 여부 (예외 없이 실행되면 루팅됨)
        score += try {
            Runtime.getRuntime().exec(arrayOf("su", "-c", "id"))
            50  // 실행됨 → 루팅 강력 신호
        } catch (e: Exception) {
            0   // 실패 → 정상 신호
        }

        // 5) /system 파티션 쓰기 가능 여부
        score += try {
            val file = File("/system/jailbreak_test_${System.currentTimeMillis()}")
            file.createNewFile().also { file.delete() }
            50  // 쓰기 성공 → 루팅됨
        } catch (e: Exception) {
            0
        }

        return score.coerceAtMost(100)
    }

    fun isHighRisk(): Boolean = calculateRiskScore() >= 60
}
```

**Swift (iOS) 예제 — Jailbreak 탐지**:
```swift
// iOS Jailbreak 탐지 — 주요 파일 경로 + sandbox escape 시도
import UIKit

struct JailbreakDetector {
    static let jailbreakPaths = [
        "/Applications/Cydia.app",
        "/Library/MobileSubstrate/MobileSubstrate.dylib",
        "/bin/bash", "/usr/sbin/sshd", "/etc/apt",
        "/private/var/lib/apt/",
    ]

    /// 탈옥 위험 점수 (0~100). 50 이상 시 고위험 처리 권장.
    static func riskScore() -> Int {
        var score = 0
        // 파일 경로 존재 확인
        if jailbreakPaths.contains(where: { FileManager.default.fileExists(atPath: $0) }) {
            score += 40
        }
        // Sandbox escape 시도: /private에 쓰기
        let testPath = "/private/jb_probe_\(Int.random(in: 0..<9999))"
        if (try? "test".write(toFile: testPath, atomically: true, encoding: .utf8)) != nil {
            try? FileManager.default.removeItem(atPath: testPath)
            score += 50
        }
        // URL scheme — Cydia 설치 여부
        if UIApplication.shared.canOpenURL(URL(string: "cydia://")!) { score += 30 }
        return min(score, 100)
    }
}
```

**관련 패턴**: App Attest / Play Integrity, RASP, Certificate Pinning

---

## 4. RASP (Runtime Application Self-Protection)

**목적**: 앱 런타임 내부에서 함수 훅(hook), 코드 주입(injection), 디버거 연결, 메모리 변조 등을 실시간으로 탐지하고, 이상 행위 발생 시 앱을 즉각 종료·보호합니다.

**특징**:
- **Anti-Debug**: `ptrace(PT_DENY_ATTACH)` (iOS), `prctl(PR_SET_DUMPABLE, 0)` (Android) — 디버거 연결 거부
- **Native Library 무결성**: 로드된 dylib/so 파일의 해시를 기동 시 검증 → 악성 삽입 탐지
- **Hook 탐지**: Frida/Substrate 특유의 메모리 패턴, `__JAILBREAK__` 심볼 탐지
- **Memory Tampering Detection**: 중요 변수(인증 상태, 잔액 등)를 이중 보관 후 불일치 탐지
- **Code Integrity Check**: 앱 바이너리 체크섬을 런타임에 재계산하여 리패키징 탐지
- 상용 RASP: Guardsquare DexGuard (Android), iXGuard (iOS), Arxan, Appdome

**장점**:
- 리버싱 도구(Frida, Cycript) 실시간 탐지로 동적 분석 방해
- 변조된 바이너리의 런타임 자가 진단 → 체인 신뢰 보강
- App Attest는 실행 시점만 검증; RASP는 실행 중 지속 감시

**단점**:
- 숙련된 공격자의 Frida-Gadget + custom script로 RASP 자체 우회 가능
- 과도한 무결성 체크는 앱 성능 저하
- 합법적인 디버깅/테스트 환경에서 오동작 → 빌드 플래그로 분리 필수

**활용 예시**:
- 금융 앱: Frida 기반 잔액 조작 시도 탐지 → 즉시 로그아웃
- 게임 앱: 메모리 핵 도구 탐지 → 세션 종료 + 서버 신고
- DRM 콘텐츠 앱: 미디어 복호화 직전 변조 탐지

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin (Android) 예제 — Anti-Debug + Frida 탐지**:
```kotlin
/**
 * RASP 핵심 탐지 로직.
 * 기동 시 + 민감 액션 직전에 호출. 탐지 시 앱 종료 또는 서버 신고 후 종료.
 */
object RASPGuard {

    /**
     * 디버거 연결 탐지 (복수 방법 교차 확인).
     * android.os.Debug.isDebuggerConnected() 단독 사용 시 쉽게 우회됨.
     */
    fun isDebuggerPresent(): Boolean {
        // 1) Android Debug API
        if (android.os.Debug.isDebuggerConnected()) return true
        // 2) /proc/self/status의 TracerPid 확인 — ptrace 연결 여부
        try {
            val status = java.io.File("/proc/self/status").readText()
            val tracerPid = status.lines()
                .firstOrNull { it.startsWith("TracerPid:") }
                ?.substringAfter(":")?.trim()?.toIntOrNull() ?: 0
            if (tracerPid != 0) return true
        } catch (_: Exception) {}
        // 3) Debug flag in BuildConfig (release 빌드는 항상 false)
        if (BuildConfig.DEBUG) return true
        return false
    }

    /**
     * Frida / 인스트루멘테이션 프레임워크 탐지.
     * 포트 27042(Frida 기본 포트) 리슨 여부 + 메모리 패턴으로 탐지.
     */
    fun isFridaPresent(): Boolean {
        // 1) Frida 기본 서버 포트 로컬 리슨 확인
        try {
            java.net.Socket("127.0.0.1", 27042).use { return true }
        } catch (_: Exception) {}
        // 2) /proc/self/maps에서 Frida agent so 패턴 탐지
        try {
            val maps = java.io.File("/proc/self/maps").readText()
            if (maps.contains("frida") || maps.contains("gadget")) return true
        } catch (_: Exception) {}
        return false
    }

    /** 앱 무결성 종합 점검 — 기동 시 + 중요 액션 직전 호출 */
    fun enforceIntegrity(activity: android.app.Activity) {
        if (isDebuggerPresent() || isFridaPresent() || RootDetector.isHighRisk()) {
            // 서버에 변조 신호 전송 후 즉시 종료
            reportTamperingAsync(activity)
            activity.finishAffinity()
            android.os.Process.killProcess(android.os.Process.myPid())
        }
    }

    private fun reportTamperingAsync(context: android.content.Context) {
        // 비동기 신고 — 종료 전 best-effort
        Thread {
            runCatching {
                securityApi.reportTampering(deviceId = getDeviceId(context), signals = collectSignals())
            }
        }.start()
    }
}
```

**관련 패턴**: Jailbreak / Root Detection, App Attest / Play Integrity, Secure Storage

---

## 5. Secure Storage (안전한 로컬 저장소)

**목적**: 기기 분실·도난 또는 루팅·탈옥된 환경에서도 인증 자격증명, API 키, 개인정보 등 민감 데이터를 하드웨어 기반 암호화로 보호합니다.

**특징**:
- **iOS Keychain**:
  - `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` (권장): 기기 잠금 해제 중, 이 기기에서만 접근. iCloud 백업 비포함.
  - `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly`: 재부팅 후 첫 잠금해제 후부터 — 백그라운드 앱에 적합
  - Secure Enclave 기반 암호화 키(SEP) — 기기 고유, 추출 불가
  - **iOS Data Protection Class** (파일/Keychain 모두 적용):

    | 클래스 | 상수 | 접근 가능 시점 | 권장 용도 |
    |---|---|---|---|
    | Complete | `NSFileProtectionComplete` / `kSecAttrAccessibleWhenUnlocked` | 잠금 해제 중만 | 결제·인증 데이터 |
    | Complete Unless Open | `NSFileProtectionCompleteUnlessOpen` | 파일 열린 동안 잠금 가능 | 업로드 임시 파일 |
    | Until First Auth | `NSFileProtectionCompleteUntilFirstUserAuthentication` | 첫 인증 후 재부팅까지 | 백그라운드 알림 토큰 |
    | None | `NSFileProtectionNone` | 항상 (비권장) | 사용 금지 |
- **Android Keystore**:
  - `StrongBox` (Pixel 3+): 분리된 보안 칩(SE/Titan M)에 키 저장 — 루팅해도 키 추출 불가
  - `TEE-backed` (대부분 기기): Trusted Execution Environment — 일반 OS와 격리
  - `KeyGenParameterSpec`: 사용 조건 지정 — 생체인증 필요, 잠금해제 필요, 만료 설정
- **Biometric-Gated Access**: 키 사용 시마다 지문/얼굴 인증 요구 (일회성 인증 후 무제한 아님)
- **EncryptedSharedPreferences / EncryptedFile (Jetpack Security)**: 일반 SharedPreferences/File을 AES-GCM으로 감싸는 Jetpack 라이브러리 — Keystore 키 사용

**장점**:
- 하드웨어 격리로 루팅 환경에서도 키 추출 원천 차단 (StrongBox/Secure Enclave)
- 생체인증 연동으로 UX 저하 없이 강한 인증 적용
- 앱 삭제 시 자동 키 삭제 (Keychain: `kSecAttrSynchronizable false`)

**단점**:
- StrongBox 미지원 기기(저가 Android)에서는 TEE만으로 fallback
- Keychain 접근 그룹 오설정 시 다른 앱에 데이터 노출 가능
- 생체인증 강제 시 생체 미등록 사용자 UX 문제
- 기기 초기화 시 데이터 손실 — 백업 전략 별도 필요 (서버 side key escrow)

**활용 예시**:
- OAuth Refresh Token → Keychain/Keystore 저장 (SharedPreferences/UserDefaults 저장 금지)
- API Key, 앱 서명 비밀 → Keystore StrongBox
- 생체인증 기반 빠른 로그인 → `BiometricPrompt` + Keystore CryptographicObject

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin (Android) 예제 — Keystore + BiometricPrompt 기반 Secure Storage**:
```kotlin
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import androidx.biometric.BiometricPrompt
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey

/**
 * Android Keystore + StrongBox + 생체인증 기반 민감 데이터 암·복호화.
 * 키는 생체인증 시에만 사용 가능 — 앱 자체가 키를 '가지는' 게 아님.
 */
class BiometricSecureStorage(private val context: Context) {

    private val KEY_ALIAS = "com.example.app.biometric_key"
    private val TRANSFORMATION = "AES/GCM/NoPadding"

    /** 생체인증 전용 AES-GCM 키 생성 (StrongBox 우선, fallback TEE) */
    fun generateKeyIfAbsent() {
        val keyStore = java.security.KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        if (keyStore.containsAlias(KEY_ALIAS)) return

        val keyGenSpec = KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setUserAuthenticationRequired(true)           // 생체인증 필수
            .setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG) // 매 사용마다 인증
            .setIsStrongBoxBacked(true)                    // StrongBox 우선 사용
            .setKeySize(256)
            .build()

        KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
            .apply { init(keyGenSpec) }
            .generateKey()
    }

    /**
     * 생체인증 성공 후 암호화 수행.
     * BiometricPrompt.AuthenticationResult에서 CryptoObject를 받아 Cipher 사용.
     */
    fun encryptWithBiometric(
        activity: androidx.fragment.app.FragmentActivity,
        plaintext: ByteArray,
        onSuccess: (ciphertext: ByteArray, iv: ByteArray) -> Unit,
        onFail: (String) -> Unit,
    ) {
        val cipher = Cipher.getInstance(TRANSFORMATION).apply {
            val key = getSecretKey()
            init(Cipher.ENCRYPT_MODE, key)
        }
        val prompt = BiometricPrompt(activity, object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                val enc = result.cryptoObject!!.cipher!!
                val ciphertext = enc.doFinal(plaintext)
                onSuccess(ciphertext, enc.iv)   // iv도 함께 저장해야 복호화 가능
            }
            override fun onAuthenticationError(code: Int, msg: CharSequence) = onFail(msg.toString())
            override fun onAuthenticationFailed() = onFail("생체인증 실패")
        })
        val info = BiometricPrompt.PromptInfo.Builder()
            .setTitle("인증이 필요합니다")
            .setSubtitle("저장된 데이터에 접근하려면 생체인증을 완료하세요")
            .setNegativeButtonText("취소")
            .build()
        prompt.authenticate(info, BiometricPrompt.CryptoObject(cipher))
    }

    private fun getSecretKey(): SecretKey {
        val keyStore = java.security.KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        return keyStore.getKey(KEY_ALIAS, null) as SecretKey
    }
}
```

**Swift (iOS) 예제 — Keychain + kSecAttrAccessibleWhenUnlockedThisDeviceOnly**:
```swift
import Security
import LocalAuthentication

/// iOS Keychain에 토큰 저장/조회 — ThisDeviceOnly + WhenUnlocked
struct KeychainManager {
    static let service = "com.example.app"

    /// 민감 데이터 Keychain 저장
    @discardableResult
    static func save(key: String, data: Data) -> Bool {
        let query: [CFString: Any] = [
            kSecClass:              kSecClassGenericPassword,
            kSecAttrService:        service,
            kSecAttrAccount:        key,
            kSecValueData:          data,
            kSecAttrAccessible:     kSecAttrAccessibleWhenUnlockedThisDeviceOnly, // iCloud 백업 제외
        ]
        SecItemDelete(query as CFDictionary)   // 중복 방지
        return SecItemAdd(query as CFDictionary, nil) == errSecSuccess
    }

    /// Keychain에서 데이터 조회 (생체인증 context 전달 시 Face ID/Touch ID 요구)
    static func load(key: String, context: LAContext? = nil) -> Data? {
        var query: [CFString: Any] = [
            kSecClass:           kSecClassGenericPassword,
            kSecAttrService:     service,
            kSecAttrAccount:     key,
            kSecReturnData:      true,
            kSecMatchLimit:      kSecMatchLimitOne,
        ]
        if let ctx = context { query[kSecUseAuthenticationContext] = ctx }
        var result: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess else { return nil }
        return result as? Data
    }
}
```

**관련 패턴**: RASP, App Attest / Play Integrity, Certificate Pinning

---
