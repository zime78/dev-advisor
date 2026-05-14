# 인증/세션/Identity Governance 패턴 (Authentication & Identity Governance)

사용자 신원 확인(Authentication), 세션 수명 주기, 그리고 조직 단위 Identity Governance(provisioning, privileged access, 위협 대응)를 다루는 패턴 모음. OAuth2 (RFC 6749) / PKCE (RFC 7636) / OIDC Core 1.0 / SAML 2.0 / WebAuthn (W3C Level 2) / TOTP (RFC 6238) / SCIM 2.0 (RFC 7644) / OAuth Device Flow (RFC 8628) / NIST SP 800-63B (Digital Identity Guidelines) 및 OWASP ASVS v4 인증 요구사항을 기반으로 한다.

---

## 1. OAuth2 Authorization Code + PKCE (RFC 7636)

**목적**: Public client(SPA, Mobile, Desktop)가 client_secret 없이 안전하게 Authorization Code를 Access Token으로 교환합니다. Authorization Code 가로채기 공격(authorization code interception)을 PKCE의 `code_verifier` / `code_challenge`로 방어합니다.

**특징**:
- `code_verifier`: 43~128자 random string (entropy ≥ 256bit 권장)
- `code_challenge`: `BASE64URL(SHA256(code_verifier))` — `method=S256` 강제
- Authorize 요청 시 `code_challenge` 전달, Token 교환 시 원본 `code_verifier` 검증
- Confidential client에서도 PKCE 적용 권장 (OAuth 2.1 draft 표준)
- Redirect URI 정확 일치 검증 — wildcard 금지

**장점**:
- client_secret 보관 불가능한 환경(브라우저/네이티브)에서도 표준 흐름 사용
- Authorization code 탈취 시에도 verifier 없으면 사용 불가
- OAuth 2.1에서 모든 흐름의 기본값으로 통합

**단점**:
- code_verifier를 client에 안전하게 보관 필요 (메모리 우선, storage는 위험)
- 흐름이 redirect-based이므로 모바일 deeplink 검증(Universal Link / App Link) 필수
- Authorization Server가 PKCE 강제(`require_pkce=true`)하지 않으면 의미 없음

**활용 예시**:
- SPA(React/Vue) → Auth0/Keycloak/Cognito
- iOS/Android 네이티브 앱 → 회사 IdP SSO
- VS Code/JetBrains IDE 로그인
- CLI 도구 (`gh auth login`)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Ktor client — PKCE 흐름
class PkceFlow(private val authServer: String, private val clientId: String) {
    fun startAuthorization(): AuthRequest {
        val verifier = randomString(64) // [A-Z a-z 0-9 -._~]
        val challenge = Base64.getUrlEncoder().withoutPadding()
            .encodeToString(MessageDigest.getInstance("SHA-256").digest(verifier.toByteArray()))
        val state = randomString(32)
        val url = "$authServer/authorize?response_type=code" +
            "&client_id=$clientId&redirect_uri=app://callback" +
            "&code_challenge=$challenge&code_challenge_method=S256" +
            "&state=$state&scope=openid+profile"
        return AuthRequest(url, verifier, state)
    }

    suspend fun exchange(code: String, verifier: String): TokenResponse =
        httpClient.submitForm("$authServer/token", parameters {
            append("grant_type", "authorization_code")
            append("code", code)
            append("redirect_uri", "app://callback")
            append("client_id", clientId)
            append("code_verifier", verifier) // 서버가 SHA256 후 challenge 비교
        }).body()
}
```

**관련 패턴**: OIDC, Refresh Token Rotation, Magic Link, OAuth Device Flow

---

## 2. OIDC (OpenID Connect Core 1.0)

**목적**: OAuth2의 권한 부여 위에 **인증(Authentication)** 레이어를 추가해, 사용자 신원 정보(ID Token)를 표준화된 JWT로 전달합니다. 표준 claim(`sub`, `email`, `name`, `aud`, `iss`)으로 IdP 간 상호 운용성을 확보합니다.

**특징**:
- `response_type=code` + `scope=openid` 시 ID Token + Access Token 발급
- ID Token 필수 claim: `iss`, `sub`, `aud`, `exp`, `iat`, `nonce`
- `nonce` claim: replay 공격 방어 — authorize 요청 시 생성, ID Token 검증 시 일치 확인
- Discovery: `/.well-known/openid-configuration`로 endpoint/JWKS 자동 탐색
- UserInfo Endpoint: Access Token으로 추가 프로필 조회
- `at_hash` claim: hybrid flow에서 Access Token 위변조 방지

**장점**:
- Authentication 표준화 — Google/Apple/Microsoft/Okta가 모두 OIDC compliant
- ID Token으로 backend가 stateless로 신원 검증
- Discovery + JWKS rotation 자동화로 운영 단순

**단점**:
- ID Token을 access token처럼 잘못 사용하는 anti-pattern 빈발 (ID Token은 인증 정보, Access Token은 API 호출용)
- `nonce` 미검증 시 replay 공격 노출
- Front-channel logout 표준 미흡 — SSO 로그아웃 동기화 어려움

**활용 예시**:
- "Sign in with Google/Apple/Microsoft" 버튼
- 사내 SSO (Okta/Keycloak/Azure AD)
- B2B SaaS의 enterprise SSO
- Kubernetes API Server OIDC 인증

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Security 6 — OIDC Relying Party
@Bean
fun jwtDecoder(@Value("\${oidc.issuer}") issuer: String): JwtDecoder {
    val decoder = JwtDecoders.fromIssuerLocation(issuer) as NimbusJwtDecoder
    val validators = OAuth2TokenValidatorFactory.combine(
        JwtValidators.createDefaultWithIssuer(issuer),
        JwtClaimValidator<String>("aud") { it == "my-client-id" },
        JwtClaimValidator<String>("nonce") { it != null } // OIDC nonce 필수
    )
    decoder.setJwtValidator(validators)
    return decoder
}
// application.yml
// spring.security.oauth2.client.registration.idp.scope: openid,profile,email
// spring.security.oauth2.client.provider.idp.issuer-uri: https://idp.example.com
```

**관련 패턴**: OAuth2 PKCE, JWT Verification, Social Login, SAML 2.0

---

## 3. SAML 2.0 (Security Assertion Markup Language)

**목적**: 엔터프라이즈 환경에서 IdP(Identity Provider)와 SP(Service Provider) 간 XML 기반 SSO를 표준화합니다. OIDC 등장 이전부터 사용된 엔터프라이즈 SSO 표준.

**특징**:
- XML 기반 Assertion (Authentication / Attribute / Authorization Decision)
- SP-Initiated SSO: SP → IdP redirect(`AuthnRequest`) → IdP 인증 → SAML Response POST
- IdP-Initiated SSO: IdP가 직접 SP에 Assertion 전송 (CSRF 위험 — RelayState 검증 필수)
- HTTP-Redirect / HTTP-POST / HTTP-Artifact binding
- XML Digital Signature (XMLDSig) 필수 — Assertion 또는 Response 서명
- Audience Restriction, NotBefore/NotOnOrAfter 검증으로 replay 방어

**장점**:
- 엔터프라이즈 IdP(ADFS, PingFederate, Okta, OneLogin)와 호환
- Attribute statement로 group/role 등 프로필 풍부하게 전달
- 정부/금융 규제 환경에서 검증된 표준

**단점**:
- XML 파싱 복잡도 — XML Signature Wrapping(XSW) 공격, XXE 취약점 빈발
- 모바일/SPA에 부적합 (redirect + POST form 흐름 무거움)
- Logout(SLO) 표준이 IdP마다 호환성 떨어짐
- 신규 도입은 OIDC 권장, SAML은 legacy 통합용

**활용 예시**:
- 대기업 사내 시스템 SSO (ADFS 기반)
- B2B SaaS의 "Enterprise SSO" 옵션 (Salesforce, Slack, GitHub Enterprise)
- 정부/공공기관 통합 인증

**난이도**: 매우 높음 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Spring Security SAML2 — Service Provider 설정
@Configuration
class Saml2Config {
    @Bean
    fun relyingPartyRegistrations(): RelyingPartyRegistrationRepository {
        val registration = RelyingPartyRegistrations
            .fromMetadataLocation("https://idp.example.com/metadata.xml")
            .registrationId("okta")
            .entityId("https://sp.example.com")
            .assertionConsumerServiceLocation("https://sp.example.com/login/saml2/sso/okta")
            .signingX509Credentials { it.add(spSigningCredential()) }
            .assertingPartyDetails { ap ->
                ap.wantAuthnRequestsSigned(true)
                  .verificationX509Credentials { it.add(idpVerificationCredential()) }
            }
            .build()
        return InMemoryRelyingPartyRegistrationRepository(registration)
    }
    // SecurityFilterChain — http.saml2Login {} + saml2Logout {}
    // XSW 방어: OpenSAML 5 + SecurityPolicyResolver로 서명 위치 강제
}
```

**관련 패턴**: OIDC (현대적 대체), JWT Verification, Audit Trail

---

## 4. FIDO2 / WebAuthn / Passkeys

**목적**: 비대칭 키 기반 패스워드리스 인증으로 phishing / credential stuffing / replay 공격을 원천 차단합니다 (W3C WebAuthn Level 2). 사용자 디바이스에 private key가 영구 보관되고, Relying Party 서버는 public key만 저장합니다.

**특징**:
- **Registration**: `navigator.credentials.create()` → authenticator가 키쌍 생성, public key + attestation을 RP에 전송
- **Authentication**: `navigator.credentials.get()` → RP가 보낸 challenge에 private key로 서명, RP가 public key로 검증
- **Passkeys**: iCloud Keychain / Google Password Manager로 다기기 동기화되는 WebAuthn credential
- Origin binding — phishing 사이트는 RP ID 불일치로 자동 거부
- User Verification(UV): biometric/PIN — `userVerification: "required"`로 강제
- Attestation: `direct` / `indirect` / `none` — 엔터프라이즈는 attestation 검증으로 device 식별

**장점**:
- Phishing 면역 (origin binding)
- Server breach 시에도 public key만 유출 → 재사용 불가
- 패스워드 입력/저장/재설정 UX 제거
- NIST SP 800-63B AAL3 달성 (hardware-backed)

**단점**:
- Authenticator 분실/리셋 시 복구 절차 필수 (다중 등록 또는 백업 코드)
- 구형 브라우저/디바이스 미지원 — fallback 흐름 병행 필요
- Enterprise attestation 정책 운영 복잡 (FIDO MDS 통합)

**활용 예시**:
- GitHub / Google / Apple 계정 passkey 로그인
- 금융 앱 거래 인증 (생체 + WebAuthn)
- 관리자 콘솔 hardware key(YubiKey) MFA
- 패스워드 완전 제거 흐름

**난이도**: 높음 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// webauthn4j — Authentication assertion 검증
class WebAuthnVerifier(private val rpId: String, private val origin: String) {
    private val manager = WebAuthnManager.createNonStrictWebAuthnManager()

    fun verify(request: AssertionRequest, storedKey: ByteArray, storedCounter: Long): VerifiedAssertion {
        val serverProperty = ServerProperty(
            Origin(origin), rpId,
            Challenge { request.challenge }, null
        )
        val authParam = AuthenticationParameters(
            serverProperty,
            Authenticator.builder(storedKey).counter(storedCounter).build(),
            null,
            true // userVerificationRequired
        )
        val data = manager.parse(request.toAuthenticationRequest())
        val result = manager.validate(data, authParam)
        // counter 역행 시 cloned authenticator 의심 → 즉시 폐기
        require(result.authenticatorData.signCount > storedCounter) { "counter regression" }
        return VerifiedAssertion(result.authenticatorData.signCount)
    }
}
```

**관련 패턴**: MFA, Account Takeover Defense, OIDC

---

## 5. MFA (Multi-Factor Authentication: TOTP / Push / WebAuthn 2nd Factor)

**목적**: "아는 것(password)" + "가진 것(device/token)" + "본인(biometric)" 중 2개 이상을 결합해 단일 인증 요소 탈취만으로는 침해되지 않도록 합니다 (NIST SP 800-63B AAL2 이상).

**특징**:
- **TOTP (RFC 6238)**: HMAC-SHA1(secret, floor(time/30s)) → 6자리 코드, Google Authenticator/1Password 호환
- **HOTP (RFC 4226)**: counter 기반 (TOTP의 시간 대신 이벤트 카운터)
- **Push approval**: 등록된 모바일 앱에 알림 → "승인/거부" — MFA fatigue 방어 필요(number matching)
- **WebAuthn 2nd factor**: password + security key 결합
- **SMS OTP는 비권장** (SS7/SIM swap 취약, NIST 2017년부터 deprecated)
- 백업 코드(recovery codes): 1회용, hash 저장

**장점**:
- 패스워드 유출만으로는 로그인 불가
- TOTP는 오프라인 동작 — 네트워크 무관
- 단계적 도입 가능 (관리자 → 일반 사용자)

**단점**:
- TOTP secret 등록 시 QR 코드 노출 — 등록 후 재표시 금지
- Push fatigue 공격 — 무한 알림으로 사용자가 "승인" 누르도록 유도
- 시간 동기화 어긋나면 TOTP 거부 (±30초 허용)
- 복구 절차가 가장 약한 고리 — social engineering 표적

**활용 예시**:
- 관리자 계정 강제 MFA
- 금융/의료 규제 대상 시스템
- GitHub/AWS Console MFA
- Slack/Notion 워크스페이스 보안 정책

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// TOTP (RFC 6238) — 검증기
class TotpVerifier(private val period: Long = 30, private val digits: Int = 6) {
    fun verify(secret: ByteArray, code: String, skew: Int = 1): Boolean {
        val now = Instant.now().epochSecond / period
        return (-skew..skew).any { generate(secret, now + it) == code }
    }

    private fun generate(secret: ByteArray, counter: Long): String {
        val data = ByteBuffer.allocate(8).putLong(counter).array()
        val mac = Mac.getInstance("HmacSHA1").apply { init(SecretKeySpec(secret, "HmacSHA1")) }
        val hash = mac.doFinal(data)
        val offset = hash[hash.size - 1].toInt() and 0x0F
        val binary = ((hash[offset].toInt() and 0x7F) shl 24) or
                     ((hash[offset + 1].toInt() and 0xFF) shl 16) or
                     ((hash[offset + 2].toInt() and 0xFF) shl 8) or
                     (hash[offset + 3].toInt() and 0xFF)
        return (binary % 10.0.pow(digits).toInt()).toString().padStart(digits, '0')
    }
}
// 등록 시: otpauth://totp/Issuer:user@example.com?secret=BASE32&issuer=Issuer
```

**관련 패턴**: WebAuthn, Account Takeover Defense, JWT Verification

---

## 6. OAuth Device Flow (RFC 8628)

**목적**: 키보드/브라우저가 없거나 입력이 제한된 디바이스(IoT, Smart TV, CLI, 임베디드)가 별도의 사용자 디바이스(스마트폰/PC)를 통해 인증을 위임받습니다.

**특징**:
- Device가 `/device_authorization`에 POST → `device_code`, `user_code`, `verification_uri`, `interval` 수령
- 사용자에게 짧은 `user_code`(예: `WDJB-MJHT`) + 짧은 URL 표시
- 사용자가 별도 디바이스에서 `verification_uri` 접속 → 로그인 + 코드 입력 → 승인
- Device는 `interval` 간격으로 `/token`을 polling — `authorization_pending` / `slow_down` / `access_denied` / `expired_token` 응답 처리
- `user_code`는 짧고 사용자 친화적이어야 하며 entropy 보장 (8자 base32 권장)

**장점**:
- 키보드 없는 디바이스도 표준 OAuth2 흐름 사용
- Device에 client_secret 보관 불필요 (public client)
- 사용자 신뢰 디바이스에서 인증 — phishing 위험 낮음

**단점**:
- Polling 부담 — `interval` 준수 안 하면 IdP가 차단
- `user_code` brute force 방어 필요 (rate limit + 만료)
- 사용자가 코드를 다른 사이트에 입력하도록 유도되는 phishing 변종 존재

**활용 예시**:
- Apple TV / Roku의 Netflix/YouTube 로그인
- `gh auth login`, `aws sso login`, `gcloud auth login`
- Raspberry Pi / 산업용 IoT 게이트웨이 등록
- Docker CLI 로그인 (`docker login`)

**난이도**: 중간 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Device Flow — Polling loop
class DeviceFlowClient(private val authServer: String, private val clientId: String) {
    suspend fun authenticate(): TokenResponse {
        val init: DeviceAuthResponse = httpClient.submitForm("$authServer/device_authorization", parameters {
            append("client_id", clientId)
            append("scope", "openid profile")
        }).body()
        println("Visit ${init.verificationUri} and enter: ${init.userCode}")

        var interval = init.interval.toLong()
        val deadline = Instant.now().plusSeconds(init.expiresIn.toLong())
        while (Instant.now().isBefore(deadline)) {
            delay(interval * 1000)
            val resp = httpClient.submitForm("$authServer/token", parameters {
                append("grant_type", "urn:ietf:params:oauth:grant-type:device_code")
                append("device_code", init.deviceCode)
                append("client_id", clientId)
            })
            when (resp.status.value) {
                200 -> return resp.body()
                400 -> when (resp.body<ErrorBody>().error) {
                    "authorization_pending" -> continue
                    "slow_down" -> interval += 5
                    else -> error("denied: ${resp.body<ErrorBody>().error}")
                }
            }
        }
        error("expired_token")
    }
}
```

**관련 패턴**: OAuth2 PKCE, OIDC, Refresh Token Rotation

---

## 7. Magic Link / Passwordless

**목적**: 사용자 이메일(또는 SMS)로 1회용 서명된 링크를 보내, 패스워드 없이 소유권(email control)을 인증 요소로 사용합니다.

**특징**:
- 서버가 `(user_id, expiry, nonce)`를 HMAC 또는 JWT(서명)으로 토큰화 → 링크 임베드
- 토큰 만료: 5~15분 권장 (NIST: short-lived)
- 1회 사용 후 즉시 무효화 — DB의 `used_at` 또는 Redis SETNX
- Email enumeration 방지: 존재 여부와 무관하게 동일 응답("If your email exists, ...")
- 링크 클릭 디바이스 ≠ 요청 디바이스인 cross-device 시 추가 확인 권장
- Same-device 흐름은 redirect, cross-device는 OTP 코드 병행

**장점**:
- 패스워드 관리 부담 제거 (사용자/서버 모두)
- 가입 funnel 단축 — "비밀번호 만들기" 단계 생략
- 패스워드 reuse / credential stuffing 면역

**단점**:
- 이메일 계정이 보안의 단일 지점 — 이메일 탈취 시 모든 서비스 침해
- 메일 전송 지연/스팸 필터로 UX 저하
- 링크 prefetch(메일 클라이언트 보안 스캐너) 시 토큰 사전 소진 위험 — POST 확인 단계 추가
- Phishing — 가짜 magic link 이메일

**활용 예시**:
- Slack 워크스페이스 로그인 ("Send me a link")
- Notion / Medium / Substack
- 1회성 게스트 액세스 (공유 문서 보기)
- B2B onboarding 초대 링크

**난이도**: 낮음 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// Magic Link — 발급 + 검증
class MagicLinkService(private val secret: ByteArray, private val store: TokenStore) {
    fun issue(email: String): String {
        val jti = UUID.randomUUID().toString()
        val exp = Instant.now().plusSeconds(600)
        val claims = mapOf("sub" to email, "exp" to exp.epochSecond, "jti" to jti)
        store.put(jti, exp) // 1회용 — used 시 delete
        val jwt = Jwts.builder().setClaims(claims)
            .signWith(Keys.hmacShaKeyFor(secret), SignatureAlgorithm.HS256).compact()
        return "https://app.example.com/auth/magic?token=$jwt"
    }

    fun consume(token: String): String {
        val claims = Jwts.parserBuilder().setSigningKey(secret).build()
            .parseClaimsJws(token).body
        val jti = claims["jti"] as String
        require(store.invalidate(jti)) { "token already used or expired" } // atomic
        return claims.subject
    }
}
// Email enumeration 방지: 이메일 미존재 시에도 200 OK + 동일 응답시간
```

**관련 패턴**: OIDC, MFA, Account Takeover Defense

---

## 8. Social Login (OIDC Consumer Pattern)

**목적**: Google/Apple/GitHub/Microsoft 같은 외부 Identity Provider의 OIDC를 소비해, 자체 회원가입 부담 없이 신원 확인을 위탁합니다.

**특징**:
- 표준 OIDC 흐름 — Authorization Code + PKCE
- IdP별 quirk: Apple은 `name`/`email`을 최초 1회만 전달, GitHub은 OIDC가 아닌 OAuth2 + `/user` endpoint
- Account linking: 같은 사용자가 Google/Apple로 각각 로그인 시 단일 계정으로 병합 (email verified 기반)
- "Sign in with Apple"은 이메일 hide(private relay) 지원 — 매번 다른 relay 이메일
- IdP 차단/추가 정책: 회사 도메인 강제(GSuite hosted domain)
- `email_verified=true`만 신뢰 — false면 계정 takeover 위험

**장점**:
- 회원가입 마찰 제거 (1-click)
- 패스워드 저장/리셋 책임 IdP에 위임
- 사용자가 이미 가진 MFA 정책 자동 상속

**단점**:
- IdP 정책 변경 위험 (예: Apple의 private relay 이메일 정책)
- IdP 장애 시 로그인 마비 — 다중 IdP 또는 fallback(magic link) 권장
- Email 미검증 IdP(GitHub no-reply) account linking에 사용 시 takeover

**활용 예시**:
- 일반 소비자 앱(쇼핑, 콘텐츠, 게임)의 "Continue with Google"
- 개발자 도구의 GitHub 로그인 (Vercel, Netlify)
- iOS 앱의 Sign in with Apple (App Store 요건)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Security — 다중 social provider
@Bean
fun clientRegistrations(): ClientRegistrationRepository =
    InMemoryClientRegistrationRepository(
        ClientRegistration.withRegistrationId("google")
            .clientId(env["GOOGLE_CLIENT_ID"]).clientSecret(env["GOOGLE_CLIENT_SECRET"])
            .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
            .redirectUri("{baseUrl}/login/oauth2/code/{registrationId}")
            .scope("openid", "profile", "email")
            .issuerUri("https://accounts.google.com")
            .build(),
        ClientRegistration.withRegistrationId("apple")
            .clientId(env["APPLE_CLIENT_ID"]).clientSecret(buildAppleClientSecret()) // JWT (ES256)
            .scope("name", "email").issuerUri("https://appleid.apple.com").build()
    )

// Account linking — email_verified 검증 후 병합
fun linkOrCreate(claims: OidcUser): User {
    require(claims.getClaimAsBoolean("email_verified") == true) { "email unverified" }
    return userRepo.findByEmail(claims.email) ?: userRepo.create(claims.email, claims.subject)
}
```

**관련 패턴**: OIDC, OAuth2 PKCE, Account Takeover Defense

---

## 9. Session / Refresh Token Rotation + Reuse Detection

**목적**: 장기 세션을 유지하면서도 refresh token 탈취 시 즉시 감지하고 family 전체를 폐기합니다 (OAuth 2.0 Security BCP, draft-ietf-oauth-security-topics).

**특징**:
- Access Token: short-lived (5~15분), Refresh Token: long-lived (수일~수주)
- Rotation: refresh token 사용 시마다 신규 발급 + 기존 토큰 즉시 무효화
- **Reuse Detection**: 이미 사용된(rotated) refresh token이 다시 등장하면 → 같은 family의 모든 token revoke + 사용자 강제 로그아웃 + 알림
- Family 추적: `family_id` 칼럼으로 rotation chain 그룹화
- Sliding expiration vs Absolute expiration trade-off
- Storage: HttpOnly + Secure + SameSite=Lax cookie 권장 (XSS 차단)

**장점**:
- 탈취 토큰과 정상 토큰이 동시에 사용되면 즉시 침해 감지
- Access token 짧게 유지하면서도 UX(재로그인 없음) 유지
- Family revoke로 침해 범위 자동 격리

**단점**:
- 동시성 이슈 — 여러 탭에서 동시 refresh 시 정상 흐름이 reuse로 오탐될 수 있음 (grace window 또는 mutex 필요)
- Refresh token DB 저장 → stateful (Redis 권장)
- Mobile 앱 백그라운드 토큰 갱신 중 네트워크 끊김 → race condition

**활용 예시**:
- 모바일 앱 장기 로그인 유지
- SPA의 silent refresh (iframe 또는 fetch)
- Banking 앱(짧은 access token + 강제 reuse detection)
- B2B SaaS 데스크탑 클라이언트

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Refresh Token Rotation with Reuse Detection
class RefreshTokenService(private val repo: RefreshTokenRepo) {
    @Transactional
    fun rotate(rawToken: String): TokenPair {
        val hash = sha256(rawToken)
        val token = repo.findByHash(hash) ?: throw InvalidToken()

        if (token.revokedAt != null) {
            // 이미 회전된 토큰 재사용 — family 전체 침해 의심
            repo.revokeFamily(token.familyId, reason = "reuse_detected")
            alertSecurity(token.userId, token.familyId)
            throw TokenReuseDetected()
        }
        if (token.expiresAt.isBefore(Instant.now())) throw ExpiredToken()

        token.revokedAt = Instant.now()
        val newToken = RefreshToken(
            familyId = token.familyId, // family 유지
            userId = token.userId,
            hash = sha256(generate()),
            expiresAt = Instant.now().plus(30, DAYS)
        )
        repo.save(token); repo.save(newToken)
        return TokenPair(issueAccessToken(token.userId), newToken.raw)
    }
}
```

**관련 패턴**: OAuth2 PKCE, JWT Verification, Account Takeover Defense

---

## 10. Account Takeover (ATO) Defense

**목적**: Credential Stuffing / Password Spraying / Brute Force / Impossible Travel / Session Hijacking을 다층 방어로 차단합니다 (NIST SP 800-63B § 5.2.2, OWASP ASVS V2).

**특징**:
- **Rate limiting**: IP + account + device fingerprint 다차원 (단순 IP는 우회 쉬움)
- **Account lockout**: N회 실패 시 점진적 지연(exponential backoff) — 영구 잠금은 DoS 위험
- **Password breach check**: HIBP(Have I Been Pwned) k-anonymity API로 노출 password 거부
- **Risk-based authentication**: 새 디바이스/IP/국가 → step-up MFA 요구
- **Impossible travel**: 마지막 로그인 위치 → 현재 위치 도달이 물리적으로 불가능한 속도(> 1000km/h)면 차단
- **Device fingerprinting**: UA + ASN + TLS fingerprint(JA3) + canvas
- **Bot detection**: CAPTCHA(reCAPTCHA v3, Turnstile) — 의심 스코어 임계값 기반
- **Notification**: 새 디바이스 로그인 시 이메일/푸시 알림

**장점**:
- Credential stuffing(타 사이트 유출 password) 자동 차단
- 정상 사용자 마찰 최소화 (위험 기반 — 평소엔 매끄럽게)
- 침해 감지를 사용자에게 위임 (알림 수신 → 즉시 신고)

**단점**:
- False positive — VPN/모바일 IP 변경/여행 시 정상 사용자 차단
- Risk scoring 모델 운영 — 신호 수집 + 임계값 튜닝 지속 작업
- Bot 진화 — CAPTCHA bypass 서비스 존재

**활용 예시**:
- 금융/은행 로그인 (impossible travel + step-up)
- 게임 계정(고가치 자산) 보호
- 관리자 콘솔 — 신규 IP 시 강제 MFA
- e-commerce 결제 시 risk score 기반 3DS 호출

**난이도**: 매우 높음 | **사용 빈도**: ★★★★

**Kotlin 예제**:
```kotlin
// 다층 ATO 방어
class LoginGuard(
    private val rateLimiter: RateLimiter,
    private val breachCheck: PwnedPasswordsClient,
    private val geoIp: GeoIpService,
    private val mfa: MfaService
) {
    suspend fun preAuthorize(email: String, ip: String, pwHash: String, prevLogin: LoginEvent?): RiskDecision {
        if (!rateLimiter.tryAcquire("ip:$ip", 10, perMinutes = 1)) return RiskDecision.BLOCK
        if (!rateLimiter.tryAcquire("acct:$email", 5, perMinutes = 5)) return RiskDecision.BLOCK
        if (breachCheck.isPwned(pwHash, threshold = 1)) return RiskDecision.REJECT_BREACHED

        val cur = geoIp.locate(ip)
        prevLogin?.let { prev ->
            val speedKmH = haversine(prev.location, cur) / hours(prev.at, Instant.now())
            if (speedKmH > 1000) return RiskDecision.STEP_UP // impossible travel
        }
        if (prevLogin?.deviceFingerprint != currentFingerprint()) return RiskDecision.STEP_UP
        return RiskDecision.ALLOW
    }
}
```

**관련 패턴**: MFA, WebAuthn, Refresh Token Rotation, Audit Trail

---

## 11. SCIM 2.0 (System for Cross-domain Identity Management)

**목적**: IdP(Okta, Azure AD, OneLogin)와 SP(SaaS) 간 사용자/그룹 lifecycle(생성/수정/비활성화/삭제)을 표준 REST API로 자동 동기화합니다 (RFC 7644).

**특징**:
- 표준 endpoint: `/Users`, `/Groups`, `/ServiceProviderConfig`, `/Schemas`
- HTTP 동사: GET / POST / PUT / PATCH / DELETE
- 표준 schema: `urn:ietf:params:scim:schemas:core:2.0:User` (userName, emails, name, active, groups)
- 확장 schema: `urn:ietf:params:scim:schemas:extension:enterprise:2.0:User` (department, manager, costCenter)
- Filter 쿼리: `?filter=userName eq "alice@example.com"`
- Bulk 작업: `/Bulk` endpoint
- Authentication: Bearer token (대부분의 IdP) 또는 OAuth2

**장점**:
- 입사/퇴사/부서이동 시 IdP에서 한 번만 변경 → 모든 SaaS에 자동 반영
- 퇴사자 access 즉시 차단(deprovisioning) — 보안 + 컴플라이언스
- 표준화로 IdP 교체 시에도 SP 코드 변경 최소

**단점**:
- IdP마다 표준 해석 미세 차이 — PATCH 연산 호환성 이슈
- 대규모 그룹 sync 시 rate limit / pagination 운영 필요
- Soft delete(`active=false`) vs Hard delete 정책 합의 필요

**활용 예시**:
- 엔터프라이즈 SaaS의 "Enterprise plan" feature (Slack, Notion, GitHub Enterprise)
- HR 시스템(Workday) → IdP → 모든 SaaS 자동 provisioning
- 부서 이동 시 그룹 권한 자동 재할당

**난이도**: 중간 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// Ktor — SCIM 2.0 Users endpoint
fun Route.scimUsers(service: UserService) = route("/scim/v2/Users") {
    install(BearerAuth)

    post {
        val user = call.receive<ScimUser>()
        val created = service.provision(user)
        call.response.header(HttpHeaders.Location, "/scim/v2/Users/${created.id}")
        call.respond(HttpStatusCode.Created, created.toScim())
    }

    patch("{id}") {
        val ops = call.receive<ScimPatchOp>() // [{op:"replace", path:"active", value:false}]
        val updated = service.applyPatch(call.parameters["id"]!!, ops)
        call.respond(updated.toScim())
    }

    get { // ?filter=userName eq "alice@example.com" & startIndex=1 & count=50
        val filter = call.parameters["filter"]?.let { ScimFilter.parse(it) }
        val page = service.search(filter, call.parameters["startIndex"]?.toInt() ?: 1)
        call.respond(ScimListResponse(page.totalResults, page.items.map { it.toScim() }))
    }
}
```

**관련 패턴**: OIDC, SAML 2.0, JIT Access, RBAC

---

## 12. Just-In-Time (JIT) Access

**목적**: 영구 권한 부여(standing access) 대신, 필요한 순간에만 시간 제한된 권한을 발급해 공격 표면을 최소화합니다 (Zero Standing Privilege).

**특징**:
- 사용자가 access 요청 → 사유 입력 → 자동/수동 승인 → 만료 시간 권한 부여
- 만료 시 권한 자동 회수 (cron 또는 token TTL)
- 승인 정책: 자동(low-risk) / 1인 승인 / 2인 승인(four-eyes) / on-call manager
- 모든 요청/승인/사용 → audit log
- Break-glass: 긴급 시 사후 승인 흐름 (post-incident review 필수)
- IdP 그룹 멤버십 임시 부여 또는 cloud IAM role temporary assumption

**장점**:
- "Always-on" 권한이 없으므로 계정 탈취 피해 범위 축소
- 누가 언제 왜 권한을 사용했는지 audit 기록 자동화
- Least Privilege를 시간 축으로 확장

**단점**:
- 운영 마찰 — 매번 요청/승인 흐름 (긴급 상황 UX 중요)
- 승인자 부재 시 SPOF — 다중 승인자 + escalation 필요
- 자동 회수 실패 시 dangling permission

**활용 예시**:
- Production DB 접근 (사유 입력 + 1시간 만료)
- Cloud IAM "AssumeRole" (AWS STS, GCP impersonation)
- Kubernetes 운영 (kubectl exec / port-forward)
- 코드 배포 권한 (CI 트리거)

**난이도**: 높음 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// JIT Access — Request → Approve → Grant → Auto-revoke
class JitAccessService(
    private val grants: GrantRepo,
    private val iam: IamProvider,
    private val approval: ApprovalEngine,
    private val audit: AuditLogger
) {
    suspend fun request(req: AccessRequest): GrantId {
        val decision = approval.evaluate(req) // policy: role + risk + approvers
        audit.log("jit.requested", req)
        return when (decision) {
            is AutoApprove -> grant(req, ttl = req.duration)
            is RequireApproval -> {
                approval.notify(decision.approvers, req)
                grants.savePending(req)
            }
        }
    }

    suspend fun approve(grantId: GrantId, approver: UserId) {
        val req = grants.markApproved(grantId, approver)
        grant(req, ttl = req.duration)
        scheduler.scheduleAt(Instant.now() + req.duration) { revoke(grantId) }
        audit.log("jit.approved", grantId, approver)
    }

    private suspend fun grant(req: AccessRequest, ttl: Duration): GrantId {
        iam.addTemporaryRole(req.subject, req.role, ttl) // 예: AWS AssumeRole DurationSeconds
        return grants.saveActive(req, expiresAt = Instant.now() + ttl)
    }
}
```

**관련 패턴**: PAM, RBAC, Audit Trail, Least Privilege

---

## 13. PAM (Privileged Access Management)

**목적**: 관리자/루트/DB superuser 같은 특권 계정을 격리·교체·감사해, 가장 강력한 자격증명의 노출과 오용을 방지합니다 (NIST SP 800-53 AC-6, CIS Controls v8 § 5/6).

**특징**:
- **Credential Vault**: 특권 계정 패스워드/SSH key를 vault(HashiCorp Vault, CyberArk, AWS Secrets Manager)에 보관 — 사용자는 평문 접근 불가
- **Ephemeral Credentials**: 매 세션마다 단명 자격증명 발급 (예: SSH CA 서명 인증서, DB 동적 사용자)
- **Session Recording**: 모든 특권 세션(SSH/RDP/DB)을 비디오 또는 keystroke + command log로 기록
- **Session Proxy/Bastion**: 직접 접근 차단, bastion host 경유 강제
- **Password rotation**: 사용 후 즉시 회전 (one-time use)
- **Approval workflow**: 특권 세션 시작 전 승인자 알림
- **Anomaly detection**: 평소와 다른 명령 패턴 → 실시간 경보

**장점**:
- 특권 자격증명이 사용자/스크립트/CI에 영구 노출되지 않음
- 사고 발생 시 정확한 책임 추적 (session recording)
- 패스워드 rotation 자동화로 운영 부담 감소
- 컴플라이언스 요구사항(PCI-DSS § 8, SOX, ISO 27001) 충족

**단점**:
- 도입/운영 비용 높음 — vault + bastion + recording 인프라
- 긴급 상황의 break-glass 절차 설계가 어렵다
- Session recording은 PII/저장 비용/법적 이슈 동반
- Bastion 자체가 새 SPOF — HA 필수

**활용 예시**:
- Production DB root 계정 — vault 발급 + 30분 TTL
- 운영 서버 SSH — CA 서명 단명 인증서 (Teleport, Vault SSH)
- Cloud root account — break-glass + hardware MFA
- DevOps CI 배포 키 — vault에서 ephemeral STS token 발급

**난이도**: 매우 높음 | **사용 빈도**: ★★★

**Kotlin 예제**:
```kotlin
// PAM — Vault 기반 ephemeral DB credential 발급
class PrivilegedDbAccess(private val vault: VaultClient, private val audit: AuditLogger) {
    suspend fun openSession(user: UserId, db: DbId, reason: String, ttl: Duration = 30.minutes): DbSession {
        require(reason.length >= 10) { "reason required for audit" }
        audit.log("pam.session.start", user, db, reason)

        // Vault Database Secrets Engine — 단명 사용자 자동 생성
        val creds = vault.read("database/creds/${db.role}") // {username, password, lease_id, lease_duration}

        val session = DbSession(
            id = SessionId.new(),
            user = user, db = db, reason = reason,
            credentials = creds,
            expiresAt = Instant.now() + ttl,
            recorder = SessionRecorder.start(user, db) // keystroke + query log
        )
        scheduler.scheduleAt(session.expiresAt) {
            vault.revoke(creds.leaseId) // DB 사용자 자동 제거
            session.recorder.close()
            audit.log("pam.session.end", user, db)
        }
        return session
    }
}
// 평문 password는 사용자가 보지 못함 — proxy가 대신 connect, 사용자는 proxy port로만 접속
```

**관련 패턴**: JIT Access, Secrets Vault, Audit Trail, Least Privilege, Zero Trust

---
