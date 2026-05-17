# API/Web 보안 패턴 (API & Web Security)

REST/GraphQL API 와 Web 프론트엔드의 실제 공격 표면 (attack surface) 을 가정한 패턴 모음. **OWASP Top 10 (2021)** 과 **OWASP API Security Top 10 (2023)**, **OWASP ASVS 4.0**, **W3C CSP Level 3 / Trusted Types**, **RFC 6749/7235/6750** 을 기반으로 한다. `security.md` 가 인증·인가·통신·암호·운영의 5 레이어 일반 보안 원칙을 다룬다면, 이 파일은 **HTTP / API 요청-응답 경계와 브라우저 컨텍스트에서 발생하는 구체적 공격 클래스** 12 개를 다룬다.

---

## 1. per-Identity Rate Limiting (신원별 레이트 리미팅)

> **`reliability/rate-limiter.md` 와의 차이**: reliability 의 Rate Limiter 는 **다운스트림 capacity 보호** (과부하·비용 폭주 방지) 가 목적이라 보통 글로벌/서비스 단위 token bucket 이다. 본 패턴은 **abuse 방어 — credential stuffing, brute-force, scraping, free-tier 남용** 이 목적이라 per-user / per-API-key / per-IP / per-fingerprint 등 **identity 차원으로 키를 쪼개고**, 거부 정책에 account lockout, IP reputation, CAPTCHA escalation 까지 포함한다.

**목적**: 동일 신원이 단위 시간당 허용량을 초과하는 요청을 막아 무차별 대입 (brute-force), credential stuffing, scraping, account takeover 시도를 차단합니다.

**특징**:
- Key 차원: `user_id`, `api_key`, `client_ip`, `device_fingerprint`, `(endpoint, identity)` 조합
- 다층 limit: per-second (burst), per-minute (sustained), per-day (quota)
- Adaptive policy: 실패율 임계치 초과 시 잠금 강도 ↑ (slow-down → CAPTCHA → lock)
- Account lockout: N 회 연속 인증 실패 → 일정 시간 계정 잠금 (NIST SP 800-63B 권장)
- IP reputation: Tor exit, known abusers (Spamhaus / AbuseIPDB) 차단
- 응답에 `Retry-After`, `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` 헤더 (RFC 9239 draft)

**장점**:
- 자동화된 공격(봇·credential stuffing) 비용 급증
- 합법 사용자에게는 거의 영향 없음 (limit 이 충분히 크면)
- WAF 와 독립적으로 애플리케이션 로직 레이어에서 보장

**단점**:
- IP 만 키로 쓰면 NAT/대형 사업장에서 정상 사용자 차단 (false positive)
- 분산 환경에서 Redis 등 공유 카운터 필요 → latency 추가
- Distributed brute-force (botnet) 은 per-IP 만으로 막기 어려움 → device fingerprint 병행

**활용 예시**:
- 로그인 / 비밀번호 재설정 / OTP 검증 엔드포인트
- Public API 의 free-tier 사용자 quota
- 회원가입 / 이메일 발송 (스팸 차단)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Ktor + Redis (Lettuce) — per-identity sliding window + account lockout
class IdentityRateLimiter(private val redis: RedisCommands<String, String>) {

    data class Decision(val allow: Boolean, val retryAfter: Long = 0)

    /** [신원별 sliding window 카운터] */
    fun check(identity: String, limit: Int, windowSec: Long): Decision {
        val key = "rl:$identity:${System.currentTimeMillis() / (windowSec * 1000)}"
        val count = redis.incr(key)
        if (count == 1L) redis.expire(key, windowSec)
        return if (count <= limit) Decision(true)
        else Decision(false, retryAfter = windowSec)
    }

    /** [N회 인증 실패 시 계정 잠금 — NIST SP 800-63B] */
    fun recordAuthFailure(userId: String): Boolean {
        val key = "lock:$userId"
        val fails = redis.incr(key)
        if (fails == 1L) redis.expire(key, 900) // 15min window
        return fails >= 5  // 5회 실패 → 잠금
    }
}

fun Application.installRateLimit(limiter: IdentityRateLimiter) {
    intercept(ApplicationCallPipeline.Plugins) {
        val identity = call.principal<UserPrincipal>()?.id ?: call.request.origin.remoteHost
        val d = limiter.check(identity, limit = 60, windowSec = 60)
        if (!d.allow) {
            call.response.headers.append("Retry-After", d.retryAfter.toString())
            call.respond(HttpStatusCode.TooManyRequests, mapOf("error" to "rate_limited"))
            return@intercept finish()
        }
    }
}
```

**관련 패턴**: Rate Limiter (reliability), Account Lockout, CAPTCHA Escalation, IP Reputation

---

## 2. HMAC Request Signing (HMAC 요청 서명)

**목적**: 요청 본문/메서드/경로/타임스탬프를 비밀키로 서명하여 **출처 인증 + 무결성 + replay 방지**를 동시에 보장합니다. Bearer 토큰이 도난 시 그대로 재사용 가능한 약점을 보완합니다.

**특징**:
- 서명 대상: `HTTP method` + `path` + `query` + `body hash` + `timestamp` + `nonce` 의 canonical string
- 알고리즘: HMAC-SHA256 (대칭 키 공유) 또는 Ed25519 (비대칭)
- Timestamp skew window: 보통 ±5 분 (RFC 3161 timestamp tolerance 관행)
- Nonce 캐시: 만료 전 동일 nonce 재사용 거부 → replay 방어
- AWS SigV4: `AWS4-HMAC-SHA256` — 4 단계 key derivation (`date → region → service → "aws4_request"`)
- Stripe Webhook: `t=<ts>,v1=<sig>` 형식 헤더, `signed_payload = "{t}.{body}"`

**장점**:
- Bearer 토큰 도난 후 replay 불가 (timestamp + nonce 검증)
- TLS 종단 (proxy / WAF) 후에도 무결성 검증 가능
- Webhook / S2S 통신의 출처 위변조 차단

**단점**:
- Client SDK 구현 부담 — canonical string 정의가 미묘 (정렬/인코딩)
- 대칭 키 공유 시 양측 모두 secret 보유 → 둘 중 한쪽 유출 시 위험
- Body streaming 시 전체 hash 계산 후에야 첫 바이트 전송

**활용 예시**:
- AWS API 호출 (SigV4)
- Stripe / GitHub / Slack 의 Webhook payload 검증
- 모바일 앱 → 자체 API 의 anti-tampering
- 결제 / 송금 등 고가치 endpoint 의 추가 인증 layer

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Stripe Webhook signature 검증 — t=...,v1=...
class WebhookVerifier(private val secret: ByteArray, private val toleranceSec: Long = 300) {

    fun verify(rawBody: String, sigHeader: String): Boolean {
        val parts = sigHeader.split(",").associate {
            it.substringBefore("=") to it.substringAfter("=")
        }
        val t = parts["t"]?.toLongOrNull() ?: return false
        val v1 = parts["v1"] ?: return false

        // 1) timestamp skew window 검증 (replay 방어)
        val now = System.currentTimeMillis() / 1000
        if (kotlin.math.abs(now - t) > toleranceSec) return false

        // 2) HMAC-SHA256 비교 (constant-time)
        val signedPayload = "$t.$rawBody"
        val mac = Mac.getInstance("HmacSHA256").apply { init(SecretKeySpec(secret, "HmacSHA256")) }
        val expected = mac.doFinal(signedPayload.toByteArray()).toHex()
        return MessageDigest.isEqual(expected.toByteArray(), v1.toByteArray())
    }
}

// AWS SigV4 — 4단계 key derivation 핵심
fun deriveSigV4Key(secret: String, date: String, region: String, service: String): ByteArray {
    fun hmac(key: ByteArray, data: String) = Mac.getInstance("HmacSHA256")
        .apply { init(SecretKeySpec(key, "HmacSHA256")) }
        .doFinal(data.toByteArray())
    val kDate    = hmac("AWS4$secret".toByteArray(), date)
    val kRegion  = hmac(kDate, region)
    val kService = hmac(kRegion, service)
    return hmac(kService, "aws4_request")
}
```

**관련 패턴**: JWT, mTLS, Nonce / Replay Protection, Webhook

---

## 3. IDOR / BOLA 방어 (Broken Object Level Authorization)

**목적**: URL/payload 의 객체 식별자(`/orders/{id}`, `userId=42`) 만으로 다른 사용자의 자원에 접근하는 **OWASP API1:2023 — Broken Object Level Authorization** 을 차단합니다. API 보안 사고의 가장 흔한 1 위 유형.

**특징**:
- 모든 자원 접근 시 **(인증된 주체 ↔ 자원 ownership)** 매핑 검증
- 단순 인증 통과 ≠ 인가 — `request.user.id == order.owner_id` 같은 row-level 체크 필수
- 추측 불가능한 ID 사용 (UUID v4, ULID) — autoincrement 노출 금지 (보강책일 뿐, 본 방어는 ownership 체크)
- Tenant 격리: multi-tenant SaaS 는 `tenant_id` 까지 함께 검증
- ORM 차원 글로벌 필터: Hibernate `@Filter`, Spring Data JPA `@PostFilter`
- 정책 엔진 위임: Cedar, OPA (Open Policy Agent) Rego

**장점**:
- 가장 빈번한 API 침해 유형 차단
- 코드 리뷰/감사에서 명시적 검증 지점 형성

**단점**:
- 누락이 쉬워서 — 모든 endpoint 마다 일관 적용 필요 (한 곳 누락 = 전체 침해)
- 복잡한 sharing/collaboration 모델 (조직 공유, link share) 시 정책 폭증
- N+1 lookup (ownership 확인 쿼리) → 캐싱/단일쿼리로 최적화 필요

**활용 예시**:
- `/api/orders/{id}` — 본인 주문만 조회/취소
- `/api/files/{fileId}/download` — 소유자 또는 공유받은 사용자만
- 멀티 테넌트 SaaS — workspace 격리
- 의료/금융 등 PII 접근 — 감사 로그까지 묶기

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Boot + Spring Security — method security + 명시적 ownership 검증
@RestController
@RequestMapping("/api/orders")
class OrderController(private val repo: OrderRepository) {

    /** [GET /api/orders/{id} — 본인 주문만] */
    @GetMapping("/{id}")
    @PreAuthorize("@orderAuthz.canRead(authentication, #id)")
    fun get(@PathVariable id: UUID, auth: Authentication): OrderDto {
        val order = repo.findById(id).orElseThrow { NotFoundException() }
        // 방어 in depth — @PreAuthorize 통과해도 다시 체크
        require(order.ownerId == (auth.principal as UserPrincipal).id) { "forbidden" }
        return order.toDto()
    }
}

@Component("orderAuthz")
class OrderAuthz(private val repo: OrderRepository) {
    fun canRead(auth: Authentication, id: UUID): Boolean {
        val uid = (auth.principal as UserPrincipal).id
        // 단일 쿼리로 ownership 검증 — N+1 회피
        return repo.existsByIdAndOwnerId(id, uid)
    }
}

// ORM 글로벌 필터 — 모든 query 에 tenant_id 자동 주입 (Hibernate)
@Entity @FilterDef(name = "tenant", parameters = [ParamDef(name = "tid", type = UUID::class)])
@Filter(name = "tenant", condition = "tenant_id = :tid")
class Order(/* ... */)
```

**관련 패턴**: RBAC, ABAC, Policy as Code (OPA), Multi-Tenancy

---

## 4. SSRF 방어 (Server-Side Request Forgery)

**목적**: 사용자가 입력한 URL 을 서버가 그대로 fetch 할 때, 내부망/메타데이터 endpoint 로 우회 호출되는 **OWASP A10:2021 — SSRF** 를 차단합니다. Capital One 2019 사고 (AWS metadata 169.254.169.254 노출로 7 억건 유출) 의 원인.

**특징**:
- 화이트리스트 우선: 허용된 host/scheme/port 만 통과 — 블랙리스트는 우회 가능
- 차단 대상 IP 대역:
  - Loopback `127.0.0.0/8`, IPv6 `::1`
  - Link-local `169.254.0.0/16` (AWS/GCP/Azure metadata: `169.254.169.254`, GCP 추가: `metadata.google.internal`)
  - Private `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
  - IPv6 ULA `fc00::/7`, IPv4-mapped `::ffff:0:0/96`
- DNS rebinding 방어: 호스트 resolve 후 IP 검증 → resolve 결과를 **연결 시점까지 고정** (pin)
- Redirect 추적 시 각 hop 마다 재검증 (3xx Location 헤더)
- Scheme 제한: `https://` 만 허용 — `file://`, `gopher://`, `dict://` 거부
- 클라우드 metadata 강화: IMDSv2 (AWS) — 세션 토큰 강제 → SSRF 단발 차단

**장점**:
- 내부 서비스 / 시크릿 누출 차단
- 클라우드 IAM 자격증명 탈취 방어 (가장 치명적 결과)
- 외부 webhook / URL preview 기능을 안전하게 제공

**단점**:
- DNS rebinding (TTL=0 두 번 resolve) 완전 방어는 connect-time IP 검증 필요
- HTTP redirect chain 검증 누락 시 우회 가능
- 정상 도메인이 사설 IP 로 resolve 되는 경우 차단 (예: split-horizon DNS)

**활용 예시**:
- URL preview, OG tag fetcher (Slack, Discord)
- Webhook 등록 / outbound HTTP call
- PDF/이미지 변환 (headless Chrome) — 내부 URL 차단
- OAuth `redirect_uri` 검증

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// SSRF-safe HTTP client — allowlist + DNS pinning + IP 검증
class SafeFetcher(
    private val allowedHosts: Set<String>,
    private val httpClient: HttpClient = HttpClient.newHttpClient(),
) {

    fun fetch(rawUrl: String): String {
        val uri = URI.create(rawUrl).normalize()
        require(uri.scheme == "https")              { "scheme not allowed" }
        require(uri.host in allowedHosts)            { "host not in allowlist" }

        // [DNS resolve 후 IP 검증 — rebinding 방어를 위해 결과 pin]
        val addrs = InetAddress.getAllByName(uri.host)
        addrs.forEach { ip ->
            require(!ip.isPrivateOrMetadata()) { "blocked ip: ${ip.hostAddress}" }
        }
        val pinned = addrs.first()

        // [resolve 결과를 강제 — 동일 host 로 다시 lookup 하지 않도록]
        val req = HttpRequest.newBuilder(URI("https://${pinned.hostAddress}${uri.rawPath}"))
            .header("Host", uri.host)
            .header("User-Agent", "safe-fetcher/1.0")
            .timeout(Duration.ofSeconds(5))
            .build()
        return httpClient.send(req, BodyHandlers.ofString()).body()
    }

    private fun InetAddress.isPrivateOrMetadata(): Boolean =
        isLoopbackAddress || isLinkLocalAddress || isSiteLocalAddress ||
        isAnyLocalAddress || isMulticastAddress ||
        hostAddress == "169.254.169.254" ||                 // AWS/GCP/Azure metadata
        hostAddress.startsWith("fd") || hostAddress.startsWith("fc")  // IPv6 ULA
}
```

**관련 패턴**: Input Sanitization, Egress Filtering, Zero Trust Network, IMDSv2

---

## 5. XXE 방어 (XML External Entity)

**목적**: XML 파서가 외부 entity 참조를 처리할 때 발생하는 **파일 유출 / SSRF / DoS** (`OWASP A05:2021 — Security Misconfiguration`) 를 차단합니다.

**특징**:
- 공격 페이로드: `<!DOCTYPE x [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>`
- Billion laughs DoS: 재귀 entity (`&lol9;`) 로 메모리 폭주
- 안전 설정 — **DOCTYPE 자체를 거부**:
  - JAXP: `XMLConstants.FEATURE_SECURE_PROCESSING = true`
  - `disallow-doctype-decl = true`
  - `external-general-entities = false`, `external-parameter-entities = false`
  - `load-external-dtd = false`
- SAX / DOM / StAX 모두 동일 설정 필요
- 가능하면 XML 대신 JSON 사용 — XML 입력을 받지 않는 것이 최상의 방어
- SVG, DOCX/XLSX(OOXML), SAML, RSS, SOAP 가 모두 XML 기반 → 같은 위험

**장점**:
- 단순 설정 변경으로 거의 모든 XXE 차단
- 라이브러리 수준 적용 — 코드 분기 불필요

**단점**:
- 레거시 XML library (Apache XMLBeans, Xerces 일부 버전) 는 기본값이 unsafe
- DTD 가 정말 필요한 도메인 (XBRL, 일부 EDI) 은 별도 sandbox 필요
- SAML 같이 외부 spec 이 entity 를 쓰는 경우 fine-grained 조정 필요

**활용 예시**:
- SOAP / SAML / OData endpoint
- 파일 업로드 (SVG, DOCX, XLSX)
- RSS / Atom feed parser
- 설정 import (Eclipse, IntelliJ 등)

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// JAXP — DocumentBuilderFactory / SAXParserFactory / XMLInputFactory 모두 강화
object SafeXmlFactories {

    fun documentBuilder(): DocumentBuilder = DocumentBuilderFactory.newInstance().apply {
        // [필수] DOCTYPE 자체 거부 — 가장 안전
        setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)
        setFeature("http://xml.org/sax/features/external-general-entities", false)
        setFeature("http://xml.org/sax/features/external-parameter-entities", false)
        setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false)
        setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true)
        isXIncludeAware = false
        isExpandEntityReferences = false
    }.newDocumentBuilder()

    fun saxParser(): SAXParser = SAXParserFactory.newInstance().apply {
        setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)
        setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true)
    }.newSAXParser()

    fun staxReader(input: InputStream): XMLStreamReader =
        XMLInputFactory.newInstance().apply {
            setProperty(XMLInputFactory.SUPPORT_DTD, false)
            setProperty("javax.xml.stream.isSupportingExternalEntities", false)
        }.createXMLStreamReader(input)
}
```

**관련 패턴**: Input Sanitization, Defense in Depth, Library Hardening

---

## 6. CSRF 방어 (Cross-Site Request Forgery)

**목적**: 인증된 사용자의 브라우저가 다른 사이트로부터 발급된 요청을 무의식적으로 실행하는 **OWASP A01:2021** 카테고리의 CSRF 공격을 차단합니다.

**특징**:
- 일차 방어: **`SameSite` Cookie 속성** — `Strict` / `Lax` / `None`
  - `Strict`: 외부 origin 에서 들어오는 모든 요청에 cookie 미동봉 (UX 영향 큼)
  - `Lax` (브라우저 기본값): top-level navigation GET 만 허용
  - `None`: 동봉 — 반드시 `Secure` 와 함께
- 이차 방어: **CSRF Token** — 서버가 발급한 토큰을 요청에 동봉
  - Synchronizer Token Pattern: 서버 세션에 저장, 응답 시 form/header 에 포함
  - Double Submit Cookie: 토큰을 cookie 와 header 양쪽에 — 서버는 두 값이 일치하는지만 확인 (stateless)
- 추가 방어:
  - `Origin` / `Referer` 헤더 검증
  - JSON content-type 강제 (form-urlencoded 거부) — 일부 CSRF 가 multipart 로 우회
- SPA: CSRF Token 을 `XSRF-TOKEN` cookie → `X-XSRF-TOKEN` header 로 echo
- REST API 가 Bearer 토큰만 받으면 (cookie 인증 미사용) CSRF 위험은 거의 없음

**장점**:
- 표준 라이브러리 (Spring Security, Django) 기본 제공
- 비용 거의 0 — 서버 메모리/연산 부담 미미
- 명확한 위협 모델 → 검증 쉬움

**단점**:
- SPA + cookie 인증 조합에서 SameSite=None 강제 시 위험 확대
- 멀티 도메인 (예: `app.example.com` ↔ `api.example.com`) 시 토큰 동기화 복잡
- Login CSRF (피해자 로그인 강제) 는 별도 대응 필요 (pre-session token)

**활용 예시**:
- 전통적 form-based 웹앱 (Spring MVC, Django, Rails)
- 관리자 콘솔 (cookie session 기반)
- 결제 / 환불 등 상태 변경 endpoint

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Security 6 — Double Submit Cookie + SameSite + Origin 검증
@Configuration
class CsrfConfig {

    @Bean
    fun securityFilterChain(http: HttpSecurity): SecurityFilterChain = http
        .csrf { csrf ->
            // [Double Submit Cookie — XSRF-TOKEN cookie ↔ X-XSRF-TOKEN header]
            csrf.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
                .csrfTokenRequestHandler(XorCsrfTokenRequestAttributeHandler())
        }
        .sessionManagement { it.sessionFixation { f -> f.migrateSession() } }
        .build()

    /** [Cookie SameSite + Secure + HttpOnly 강제] */
    @Bean
    fun cookieSerializer(): CookieSerializer = DefaultCookieSerializer().apply {
        setSameSite("Lax")            // top-level GET 만 동봉
        setUseSecureCookie(true)
        setUseHttpOnlyCookie(true)
        setCookieName("SESSION")
    }
}

// Origin 헤더 검증 (보강책)
@Component
class OriginCheckFilter(@Value("\${app.origins}") private val allowed: List<String>) : OncePerRequestFilter() {
    override fun doFilterInternal(req: HttpServletRequest, res: HttpServletResponse, chain: FilterChain) {
        if (req.method !in setOf("GET", "HEAD", "OPTIONS")) {
            val origin = req.getHeader("Origin") ?: req.getHeader("Referer")
            if (origin != null && allowed.none { origin.startsWith(it) }) {
                res.sendError(HttpServletResponse.SC_FORBIDDEN, "bad origin"); return
            }
        }
        chain.doFilter(req, res)
    }
}
```

**관련 패턴**: SameSite Cookie, CORS, Synchronizer Token, Defense in Depth

---

## 7. Open Redirect 방어

**목적**: 사용자가 신뢰하는 도메인의 URL 을 거쳐 악성 사이트로 자동 이동되는 공격을 차단합니다. 피싱 / OAuth 인가 코드 탈취 / XSS 페이로드 우회의 발판이 됩니다.

**특징**:
- 취약 패턴: `https://safe.com/login?next=https://evil.com` → 로그인 후 무검증 redirect
- 검증 원칙:
  - **상대 경로만 허용** (`/dashboard`) 이 가장 안전
  - 절대 URL 허용 시: scheme + host 화이트리스트
  - `//evil.com` (scheme-relative) 차단 — 일부 파서는 이를 origin 으로 해석
  - `\\evil.com`, `https:evil.com`, `https:/evil.com` 등 mis-parsing 우회 차단
- Signed redirect: redirect 대상을 HMAC 으로 서명 → 변조 차단
- OAuth `redirect_uri`: spec 상 **사전 등록된 정확 일치 매칭** (RFC 6749 §3.1.2) — prefix match 금지
- Mailer link 의 unsubscribe / tracking: 항상 signed URL

**장점**:
- 단순 검증으로 차단 가능
- 피싱 표면 대폭 축소

**단점**:
- 다중 도메인 (브랜드별 도메인 N 개) 시 화이트리스트 유지 부담
- URL parser 구현차 (Java `URI` vs `URL` vs 브라우저) — 가장 strict 한 검증 필요

**활용 예시**:
- 로그인 후 `?next=` / `?returnUrl=` 처리
- OAuth `redirect_uri`
- 이메일 인증 / 비밀번호 재설정 링크
- 광고 / 트래킹 클릭 추적

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// Open Redirect 방지 — 상대 경로 우선 + 절대 URL allowlist + HMAC signed
class RedirectGuard(
    private val allowedHosts: Set<String> = setOf("app.example.com"),
    private val hmacKey: ByteArray,
) {

    /** [입력된 next 가 안전한지 판단 — 안전하지 않으면 기본값 반환] */
    fun sanitize(next: String?, default: String = "/"): String {
        if (next.isNullOrBlank()) return default
        // 1) scheme-relative `//evil.com` / 백슬래시 차단
        if (next.startsWith("//") || next.startsWith("\\") || next.contains("\\")) return default
        // 2) 상대 경로 — 가장 안전
        if (next.startsWith("/") && !next.startsWith("//")) return next
        // 3) 절대 URL — host 화이트리스트
        return try {
            val uri = URI.create(next)
            if (uri.scheme == "https" && uri.host in allowedHosts) next else default
        } catch (e: Exception) { default }
    }

    /** [HMAC 서명된 redirect — 변조 차단] */
    fun sign(target: String): String {
        val mac = Mac.getInstance("HmacSHA256").apply { init(SecretKeySpec(hmacKey, "HmacSHA256")) }
        val sig = mac.doFinal(target.toByteArray()).toBase64UrlNoPad()
        return "/r?u=${URLEncoder.encode(target, "UTF-8")}&s=$sig"
    }

    fun verify(target: String, sig: String): Boolean {
        val mac = Mac.getInstance("HmacSHA256").apply { init(SecretKeySpec(hmacKey, "HmacSHA256")) }
        val expected = mac.doFinal(target.toByteArray()).toBase64UrlNoPad()
        return MessageDigest.isEqual(expected.toByteArray(), sig.toByteArray())
    }
}
```

**관련 패턴**: Input Sanitization, HMAC Signing, OAuth `redirect_uri` 검증

---

## 8. Mass Assignment 방어

**목적**: 클라이언트가 제출한 JSON/form 의 모든 필드를 도메인 객체에 자동 바인딩할 때, 의도하지 않은 필드 (`isAdmin`, `role`, `creditBalance`) 까지 덮어쓰여지는 **OWASP API6:2023 — Mass Assignment** 를 차단합니다. GitHub 2012 사고 (`rails`-style mass assignment 로 임의 user 의 권한 변경) 가 원조.

**특징**:
- 원인: ORM/binder 가 외부 입력을 도메인 entity 에 직접 매핑
- 방어:
  - **DTO 분리** — 입력 전용 record/data class 를 두고 entity 와 분리
  - Whitelist binding — Spring 의 `@InitBinder` 로 허용 필드만 명시
  - Jackson `@JsonIgnore` / `@JsonProperty(access = WRITE_ONLY)` — 응답 노출도 차단
  - Bean Validation 으로 형식/범위 함께 검증
- "Strong Parameters" (Rails 용어) ↔ "Allowlist Binding" (Spring 용어) — 같은 개념
- GraphQL 의 `input` 타입은 자연스럽게 분리되어 있지만, resolver 에서 entity 로 변환 시 같은 위험

**장점**:
- 권한 상승 (privilege escalation) 차단
- 도메인 모델과 API 표면의 명시적 분리 → 리팩터링 안전성 향상

**단점**:
- DTO ↔ Entity 매핑 코드 boilerplate (MapStruct, Kotlin `apply` 로 완화)
- 필드 추가 시 양쪽 동기화 누락 위험

**활용 예시**:
- 사용자 프로필 수정 (`role`, `tenantId`, `verified` 차단)
- 주문 생성 (`status`, `paymentVerified` 차단)
- 관리자 endpoint 와 일반 endpoint 의 입력 DTO 분리

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// DTO 분리 — Entity 의 민감 필드 보호
@Entity
class User(
    @Id val id: UUID = UUID.randomUUID(),
    var email: String,
    var displayName: String,
    @Enumerated(EnumType.STRING) var role: Role,           // 외부 변경 금지
    var creditBalance: Long = 0,                            // 외부 변경 금지
    var verified: Boolean = false,                          // 외부 변경 금지
)

/** [입력 전용 DTO — 허용 필드만 명시] */
data class UpdateProfileRequest(
    @field:Email val email: String,
    @field:Size(min = 1, max = 50) val displayName: String,
)

@RestController
@RequestMapping("/api/me")
class ProfileController(private val repo: UserRepository) {

    @PatchMapping
    fun update(@RequestBody @Valid req: UpdateProfileRequest, auth: Authentication): UserDto {
        val user = repo.findById((auth.principal as UserPrincipal).id).orElseThrow()
        // 명시적 필드만 복사 — role / creditBalance / verified 는 절대 손대지 않음
        user.email = req.email
        user.displayName = req.displayName
        return repo.save(user).toDto()
    }
}

// Spring 의 폼 바인딩이라면 — @InitBinder 로 화이트리스트
@ControllerAdvice
class BindingConfig {
    @InitBinder("user")
    fun init(binder: WebDataBinder) {
        binder.setAllowedFields("email", "displayName")    // 외엔 전부 무시
    }
}
```

**관련 패턴**: DTO Pattern, Input Validation, Least Privilege

---

## 9. Race Condition / TOCTOU 방어 (Time-Of-Check-To-Time-Of-Use)

**목적**: "확인 시점" 과 "사용 시점" 사이의 동시성 갭으로 인한 중복 결제 / 이중 출금 / 재고 음수 같은 비즈니스 무결성 위반을 차단합니다. OWASP API 보안 외에 비즈니스 로직 취약점 (BLT) 으로 분류됩니다.

**특징**:
- 전형 패턴:
  ```
  if (balance >= amount) {           // ← T1: check
      balance -= amount              // ← T2: use   (T1~T2 사이에 다른 트랜잭션이 잔액 차감 가능)
  }
  ```
- 방어 전략 (3 가지):
  1. **Atomic Check-and-Act** (DB 차원): `UPDATE ... WHERE balance >= ?` 후 `affectedRows` 확인
  2. **Pessimistic Lock**: `SELECT ... FOR UPDATE` — 트랜잭션 내 행 잠금
  3. **Optimistic Lock**: `@Version` 컬럼 + `UPDATE ... WHERE version = ?` — 충돌 시 retry
- HTTP 레이어: **Idempotency Key** — 클라이언트가 UUID 헤더로 동일 요청 보장 (Stripe `Idempotency-Key` 표준)
- Distributed lock: Redis Redlock, ZooKeeper — DB 외부 자원 보호 시
- 이중 클릭 / 네트워크 재시도로 인한 중복 요청은 idempotency 로, 동시 사용자는 lock 으로 — 두 layer 가 다름

**장점**:
- 금융 / 재고 / 쿠폰 등 핵심 무결성 보장
- Idempotency 는 client retry 정책과 조합 시 매우 강력

**단점**:
- Pessimistic lock 은 처리량 저하 / 데드락 위험
- Optimistic lock 은 충돌 시 retry 로직 필요 → exponential backoff
- Distributed lock 은 fencing token 없으면 split-brain 위험

**활용 예시**:
- 결제 / 송금 / 환불
- 한정수량 쿠폰 발급, 선착순 이벤트
- 재고 차감 (e-commerce)
- 동시 가입 / 닉네임 선점

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// (1) Atomic Check-and-Act — 가장 단순하고 안전
@Repository
interface AccountRepo : JpaRepository<Account, UUID> {
    @Modifying
    @Query("UPDATE Account a SET a.balance = a.balance - :amt WHERE a.id = :id AND a.balance >= :amt")
    fun debit(id: UUID, amt: Long): Int   // affectedRows = 0 이면 잔액 부족
}

// (2) Optimistic Lock — @Version 으로 동시 수정 검출
@Entity class Order(
    @Id val id: UUID,
    var status: OrderStatus,
    @Version var version: Long = 0,   // JPA 가 UPDATE ... WHERE version = ? 자동
)

// (3) Idempotency Key — HTTP layer 의 중복 요청 차단
@RestController
class PaymentController(private val service: PaymentService, private val redis: StringRedisTemplate) {

    @PostMapping("/api/payments")
    fun pay(
        @RequestHeader("Idempotency-Key") key: String,
        @RequestBody req: PayRequest,
    ): PayResult {
        val cacheKey = "idem:$key"
        // [동일 key 가 이전에 처리되었으면 같은 결과 재반환 — Stripe 방식]
        redis.opsForValue().get(cacheKey)?.let { return jsonMapper.readValue(it) }

        // [SET NX — 첫 요청만 실행 권한 획득]
        val acquired = redis.opsForValue().setIfAbsent(cacheKey, "PENDING", Duration.ofMinutes(10)) ?: false
        if (!acquired) throw ConflictException("in-flight: $key")

        return runCatching {
            service.charge(req).also { redis.opsForValue().set(cacheKey, jsonMapper.writeValueAsString(it), Duration.ofHours(24)) }
        }.onFailure { redis.delete(cacheKey) }.getOrThrow()
    }
}
```

**관련 패턴**: Idempotency Key, Distributed Lock, Optimistic / Pessimistic Locking, Saga

---

<a id="graphql-security"></a>
## 10. GraphQL 보안

**목적**: GraphQL 의 유연한 query 모델이 가져오는 고유 공격 표면 — **무한 깊이 query / N+1 / cost-bomb / introspection 노출 / authorization bypass** — 을 차단합니다. OWASP GraphQL Cheat Sheet 기반.

**특징**:
- **Depth Limiting**: query nesting 최대 깊이 제한 (보통 7~10)
- **Query Complexity Analysis**: 각 필드에 cost 부여 → 총합 임계치 초과 시 거부
  ```graphql
  type Query {
    users(first: Int!): [User] @cost(complexity: 2, multipliers: ["first"])
  }
  ```
- **Introspection 비활성화** (운영 환경): `__schema`, `__type` 조회 차단 — 공격자 정찰 표면 축소
- **Persisted Queries**: 클라이언트가 hash 만 보내고 서버가 사전 등록된 query 만 실행 — 임의 query 차단
- **Field-level Authorization**: `@auth` directive 또는 resolver 별 인가 체크 (인증 ≠ 인가)
- **Batching limit**: 단일 HTTP 요청의 query 개수 제한 (DoS 방어)
- **Rate limit by cost**: 호출 수 대신 누적 cost 기준 limit
- N+1 회피: DataLoader 로 batch + cache
- Error masking: 운영 환경에서 stack trace / SQL error 노출 차단

**장점**:
- GraphQL 특유의 cost-bomb 차단
- 클라이언트 유연성과 서버 보호의 균형
- Persisted query 는 보안 + 캐시 효율 동시 달성

**단점**:
- Cost 계산 룰 설계 난이도 — 너무 빡빡하면 정상 query 거부
- Field-level authz 는 코드 폭증 → directive / OPA 위임 필요
- Subscription (WebSocket) 보안은 별도 추가 작업

**활용 예시**:
- 공개 GraphQL API (GitHub, Shopify, Contentful)
- BFF (Backend For Frontend) — Apollo / Relay
- 내부 마이크로서비스 schema federation

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// graphql-kotlin + DGS / Spring GraphQL — 깊이/복잡도/인가 통합
@Configuration
class GraphQLSecurityConfig {

    @Bean
    fun graphQL(schema: GraphQLSchema): GraphQL = GraphQL.newGraphQL(schema)
        .instrumentation(ChainedInstrumentation(listOf(
            // [1] 깊이 제한 — 최대 10
            MaxQueryDepthInstrumentation(10),
            // [2] 복잡도 제한 — 총 cost 1000 이내
            MaxQueryComplexityInstrumentation(1000),
        )))
        .build()

    /** [운영 환경에선 introspection 차단] */
    @Bean
    @Profile("prod")
    fun disableIntrospection(): RuntimeWiringConfigurer = RuntimeWiringConfigurer { wiring ->
        wiring.fieldVisibility(NoIntrospectionGraphqlFieldVisibility.NO_INTROSPECTION_FIELD_VISIBILITY)
    }
}

// Field-level authorization — directive 기반
class AuthDirectiveWiring : SchemaDirectiveWiring {
    override fun onField(env: SchemaDirectiveWiringEnvironment<GraphQLFieldDefinition>): GraphQLFieldDefinition {
        val field = env.element
        val requiredRole = env.directive.getArgument("role").argumentValue.value as String
        val original = env.codeRegistry.getDataFetcher(env.fieldsContainer, field)
        env.codeRegistry.dataFetcher(env.fieldsContainer, field, DataFetcher { dfe ->
            val auth = dfe.graphQlContext.get<Authentication>("auth")
            require(auth.authorities.any { it.authority == "ROLE_$requiredRole" }) { "forbidden" }
            original.get(dfe)
        })
        return field
    }
}

/* schema.graphqls
directive @auth(role: String!) on FIELD_DEFINITION
type Query {
  adminStats: Stats @auth(role: "ADMIN")
  users(first: Int!): [User] @cost(complexity: 2, multipliers: ["first"])
}
*/
```

**관련 패턴**: Rate Limiter, RBAC, Cost-based Quota, DataLoader

---

## 11. CSP / SRI / HSTS / Trusted Types (Web 보안 헤더)

**목적**: 브라우저에 정책을 강제 주입하여 XSS / 코드 주입 / 클릭재킹 / 다운그레이드 / 서드파티 변조를 다층 방어합니다. W3C CSP Level 3, MDN Web Security 기준.

**특징**:
- **CSP (Content Security Policy)** — script 실행 출처 제한:
  - `script-src 'self' 'nonce-{random}'` — nonce-based (권장)
  - `script-src 'self' 'sha256-{hash}'` — hash-based (정적 inline)
  - `script-src 'strict-dynamic' 'nonce-...'` — nonce 받은 스크립트가 동적 로드한 것까지 허용
  - `'unsafe-inline'`, `'unsafe-eval'` 절대 사용 금지 (legacy 회피책)
  - `report-to` / `report-uri` 로 위반 신고 수집
- **SRI (Subresource Integrity)** — CDN 변조 차단:
  ```html
  <script src="https://cdn.example.com/lib.js"
          integrity="sha384-{base64}" crossorigin="anonymous"></script>
  ```
- **HSTS (HTTP Strict Transport Security)** — TLS 다운그레이드 차단:
  ```
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  ```
  - preload list 등재 시 첫 방문조차 HTTPS 강제
- **Trusted Types** (Chrome/Edge) — DOM XSS sink 강제:
  ```
  Content-Security-Policy: require-trusted-types-for 'script'
  ```
  - `innerHTML`, `eval` 같은 dangerous sink 에 일반 string 할당 시 throw
- 기타: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Embedder-Policy: require-corp`

**장점**:
- 인젝션 / XSS 가 발생해도 실행 자체를 차단
- 코드 변경 없이 헤더로 강제 가능
- CSP report 로 in-the-wild 공격/오탐 가시화

**단점**:
- Inline script / 동적 script 가 많은 legacy 사이트에 적용 어려움
- nonce 발급은 server-rendered HTML 마다 동기화 필요 (SSR 친화)
- SRI 는 콘텐츠 변경 시 hash 재발급 → 빌드 파이프라인 통합 필요

**활용 예시**:
- 모든 공개 웹앱 (기본 표준)
- 금융 / 의료 / 정부 사이트 (compliance baseline)
- 브라우저 확장 / Electron 앱

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Security — strict CSP + Trusted Types + HSTS 통합 헤더
@Configuration
class WebSecurityHeaders {

    @Bean
    fun headersFilter(): SecurityFilterChain = TODO()  // 위치 표시용

    /** [각 응답마다 nonce 생성 → CSP 헤더 + Thymeleaf 변수 주입] */
    @Bean
    fun cspNonceFilter() = OncePerRequestFilter { req, res, chain ->
        val nonce = ByteArray(16).also { SecureRandom().nextBytes(it) }
            .toBase64NoPad()
        req.setAttribute("cspNonce", nonce)

        res.setHeader("Content-Security-Policy", listOf(
            "default-src 'self'",
            "script-src 'self' 'nonce-$nonce' 'strict-dynamic'",
            "style-src 'self' 'nonce-$nonce'",
            "img-src 'self' data: https:",
            "connect-src 'self' https://api.example.com",
            "frame-ancestors 'none'",                       // clickjacking
            "base-uri 'self'",
            "form-action 'self'",
            "require-trusted-types-for 'script'",           // DOM XSS sink 강제
            "trusted-types default app#html",
            "report-to csp-endpoint",
        ).joinToString("; "))

        // HSTS — 2년 + preload (한 번 적용 후 되돌리기 어려우니 신중)
        res.setHeader("Strict-Transport-Security",
            "max-age=63072000; includeSubDomains; preload")
        res.setHeader("X-Content-Type-Options", "nosniff")
        res.setHeader("Cross-Origin-Opener-Policy", "same-origin")
        res.setHeader("Cross-Origin-Embedder-Policy", "require-corp")
        chain.doFilter(req, res)
    }
}

/* HTML 측 — SRI + nonce */
/*
<script nonce="${cspNonce}"
        src="https://cdn.example.com/app.v123.js"
        integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9G8GZ1B4i6/6jPv/B5+Hb1xS3Cw1uvP+IbnH4Z"
        crossorigin="anonymous"></script>
*/
```

**관련 패턴**: Defense in Depth, XSS 방어, Trusted Types, mTLS

---

## 12. CORS / Cookie 정책 (SameSite / Referrer-Policy / Permissions-Policy)

**목적**: 브라우저의 cross-origin 호출 정책과 자격증명/정보 누설 정책을 정밀하게 제어하여 정보 누출과 무권한 호출을 차단합니다. RFC 6454 (Origin), Fetch Spec, MDN.

**특징**:
- **CORS (Cross-Origin Resource Sharing)**:
  - Preflight (`OPTIONS`) — non-simple 요청 (Content-Type: application/json 등) 에서 발생
  - `Access-Control-Allow-Origin` — **절대 `*` + `Allow-Credentials: true` 동시 금지** (브라우저가 거부하지만 spec 위반)
  - Origin echo (요청 Origin 을 그대로 응답) 시 화이트리스트 검증 필수
  - `Allow-Methods` / `Allow-Headers` / `Expose-Headers` 명시
  - `Access-Control-Max-Age` 로 preflight 캐시
- **SameSite Cookie**: `Strict` / `Lax` / `None` (Section 6 참조)
- **Referrer-Policy**:
  - `no-referrer` — 가장 안전
  - `strict-origin-when-cross-origin` — 일반 권장 (cross-origin 엔 origin 만)
  - URL 의 query string 에 token 이 있으면 referrer 로 유출
- **Permissions-Policy** (구 Feature-Policy): browser 기능 차단
  - `geolocation=()`, `camera=()`, `microphone=()`, `payment=()`, `usb=()`
  - 본인 origin 만 허용: `geolocation=(self)`
- **COOP / COEP / CORP**: Spectre 등 cross-origin isolation 방어

**장점**:
- 정보 leak / token 노출 차단 (referrer)
- 권한 부여 안 한 브라우저 API 차단
- preflight 로 잘못된 cross-origin 호출 차단

**단점**:
- 와일드카드 (`*.example.com`) 정책은 CORS spec 미지원 → origin echo + 검증 필요
- 정책 누락 시 보안 효과 0, 너무 엄격하면 정상 SPA 가 깨짐
- 모바일 WebView / 자체 client 는 CORS 우회 → 서버측 인가가 본방어 (CORS 는 브라우저만 강제)

**활용 예시**:
- SPA + 별도 도메인 API 서버
- 임베드 위젯 / 결제 SDK
- 공개 광고 / 분석 스크립트

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Security 6 — strict CORS + Referrer / Permissions Policy
@Configuration
class CorsAndPolicyConfig {

    @Bean
    fun corsSource(): UrlBasedCorsConfigurationSource {
        val cfg = CorsConfiguration().apply {
            allowedOrigins = listOf(
                "https://app.example.com",
                "https://admin.example.com",
                // 절대 `*` 와 allowCredentials = true 동시 금지
            )
            allowedMethods = listOf("GET", "POST", "PUT", "PATCH", "DELETE")
            allowedHeaders = listOf("Authorization", "Content-Type", "Idempotency-Key")
            exposedHeaders = listOf("X-Request-Id", "RateLimit-Remaining")
            allowCredentials = true
            maxAge = 3600                     // preflight 캐시
        }
        return UrlBasedCorsConfigurationSource().apply { registerCorsConfiguration("/api/**", cfg) }
    }

    @Bean
    fun securityHeaders() = OncePerRequestFilter { req, res, chain ->
        // Referrer-Policy — query token 노출 방지
        res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin")
        // Permissions-Policy — 사용 안 하는 강력 기능은 전부 차단
        res.setHeader("Permissions-Policy", listOf(
            "geolocation=()", "camera=()", "microphone=()",
            "payment=()", "usb=()", "magnetometer=()",
            "accelerometer=()", "gyroscope=()", "interest-cohort=()",
        ).joinToString(", "))
        chain.doFilter(req, res)
    }
}

// 와일드카드가 정말 필요하면 — origin echo + suffix 검증 (CORS spec 우회 X, 안전한 echo)
@Component
class WildcardCorsFilter : OncePerRequestFilter() {
    private val allowedSuffixes = listOf(".example.com", ".example-cdn.com")
    override fun doFilterInternal(req: HttpServletRequest, res: HttpServletResponse, chain: FilterChain) {
        val origin = req.getHeader("Origin")
        if (origin != null) {
            val host = URI.create(origin).host ?: ""
            if (allowedSuffixes.any { host.endsWith(it) }) {
                res.setHeader("Access-Control-Allow-Origin", origin)
                res.setHeader("Vary", "Origin")
                res.setHeader("Access-Control-Allow-Credentials", "true")
            }
        }
        chain.doFilter(req, res)
    }
}
```

**관련 패턴**: CSP, SameSite Cookie, CSRF, Origin Validation, Defense in Depth

---
