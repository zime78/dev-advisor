# 보안 패턴 메타 원리 (Security Meta-Principles)

보안 설계의 근본 원리 4가지. 개별 기술 패턴(OAuth2, mTLS, RBAC 등)은 아래 sub-카테고리 파일에 분리되어 있으며, 이 파일은 **모든 sub-카테고리가 공유하는 메타 원리**만 다룬다.

## 보안 Sub-카테고리 카탈로그

| Sub-카테고리 | 파일 |
|-------------|------|
| 인증 | security-authn.md |
| 인가 | security-authz.md |
| 암호 운영 | security-crypto-ops.md |
| 데이터 보호 | security-data-protection.md |
| API/Web | security-api-web.md |
| 공급망 | security-supply-chain.md |
| 플랫폼 | security-platform.md |
| DevSecOps SDLC | security-sdlc.md |
| 탐지/사고 대응 | security-detect-respond.md |
| 모바일 | security-mobile.md |
| AI 모델 보안 | security-ai-model.md |
| 규제 컴플라이언스 | compliance.md |

---

## 1. Defense in Depth (다층 방어)

**목적**: 단일 보안 통제 실패에 대비하여 네트워크 / 호스트 / 애플리케이션 / 데이터 / 인적 레이어 각각에 독립적인 통제를 중첩 배치합니다.

**특징**:
- Redundant controls — 한 layer 우회되어도 다음 layer가 차단
- Layer별 다른 메커니즘 (WAF + Input validation + Parameterized query)
- 탐지(Detective) + 예방(Preventive) + 대응(Corrective) 통제 조합
- Assumed breach 가정 — 침해 발생 시 blast radius 최소화
- 레이어 간 독립성: 한 레이어의 구현 언어/벤더/메커니즘을 다른 레이어와 다르게 선택

**장점**:
- 단일 zero-day 취약점 노출 영향 완화
- 컴플라이언스 요구사항 자연스럽게 충족 (PCI DSS, ISO 27001)
- 공격 비용 증가 → 표적 가치 하락

**단점**:
- 운영 복잡도 증가, 통제 간 충돌 가능
- 비용 누적
- 잘못 설계 시 false sense of security (실효성 없는 layer 누적)

**활용 예시**:
- Web 서비스: CDN/WAF → LB TLS → App input validation → DB parameterized query → DB encryption at rest
- 컨테이너: Image scan → Admission controller → RuntimeSec(Falco) → NetworkPolicy
- 사내 데이터 유출 방지: DLP + Endpoint EDR + Email gateway + 사내 교육

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Boot — 단일 endpoint에 4개 layer 적용
@RestController
class TransferController(private val svc: TransferService) {
    @PostMapping("/transfer")
    @PreAuthorize("hasRole('USER') and #req.fromAccount == authentication.name") // Layer 3: 인가
    fun transfer(
        @Valid @RequestBody req: TransferRequest,            // Layer 2: Bean Validation
        @RequestHeader("X-CSRF-Token") csrf: String,         // Layer 1: CSRF
    ): TransferResult {
        require(rateLimiter.tryAcquire(req.fromAccount))     // Layer 4: Rate limit
        return svc.transferEncrypted(req)                    // Layer 5: 저장 시 암호화
    }
}
// + 외곽: WAF (SQLi / XSS rule), TLS 1.3, mTLS to DB
```

**관련 패턴**: Zero Trust Architecture, Least Privilege, security-api-web.md, security-sdlc.md

---

## 2. Zero Trust Architecture (ZTA)

**목적**: "Never trust, always verify" 원칙으로, 네트워크 위치(사내/사외)에 무관하게 모든 요청을 인증/인가/암호화합니다 (NIST SP 800-207).

**특징**:
- Perimeter security(방화벽) 모델 폐기 — 내부망도 untrusted
- 모든 요청: identity 검증 + device posture + context (시간/위치/risk score)
- Policy Decision Point(PDP) + Policy Enforcement Point(PEP) 분리
- Micro-segmentation — 워크로드 단위 최소 권한 통신
- Continuous verification — 세션 중에도 재평가
- Implicit trust zone 없음 — VPN 내부도 동일 기준 적용

**장점**:
- Lateral movement(횡적 이동) 공격 차단 — 침해된 1개 노드 → 전체 침투 방지
- Remote work / BYOD / Cloud-native 환경에 적합
- 감사/규제 대응 강화 (모든 접근 로깅)

**단점**:
- 초기 도입 비용 큼 — IdP, PEP, SIEM, Service Mesh 모두 필요
- 잘못 설계하면 latency 누적
- 조직 차원 거버넌스 합의 필수

**활용 예시**:
- Google BeyondCorp (no VPN)
- Cloudflare Access / Zscaler Private Access
- Kubernetes + Istio + OPA 조합으로 사내 SaaS 보호
- 금융권 망분리 대안

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// PEP — Spring Cloud Gateway에서 PDP(OPA) 호출
class ZeroTrustFilter(private val opa: OpaClient) : GlobalFilter {
    override fun filter(exchange: ServerWebExchange, chain: GatewayFilterChain): Mono<Void> {
        val jwt = exchange.request.headers.getFirst("Authorization")?.removePrefix("Bearer ")
        val devicePosture = exchange.request.headers.getFirst("X-Device-Posture") // MDM 발급
        val context = mapOf(
            "subject" to (jwt?.let(::decodeSub) ?: return unauthorized(exchange)),
            "device"  to devicePosture,
            "path"    to exchange.request.path.value(),
            "method"  to exchange.request.method?.name(),
            "ip"      to exchange.request.remoteAddress?.address?.hostAddress,
        )
        return opa.evaluate("/data/authz/allow", context)
            .flatMap { allowed -> if (allowed) chain.filter(exchange) else forbidden(exchange) }
    }
}
```

**관련 패턴**: Defense in Depth, Least Privilege, security-authn.md, security-authz.md

---

## 3. Least Privilege (최소 권한 원칙)

**목적**: 모든 주체(사용자/서비스/프로세스)에게 작업 수행에 필요한 최소 권한만 부여하여 침해 시 폭발 반경을 최소화합니다 (Saltzer & Schroeder 1975).

**특징**:
- Default Deny — 명시적으로 허용된 것만 가능
- Just-in-Time (JIT) — 평소 권한 없음, 승인 시 한시적 부여
- Just-Enough-Access (JEA) — 작업에 정확히 필요한 권한만
- Privilege separation — 단일 프로세스 권한 분리 (root → unprivileged)
- 정기적 access review (분기 1회 권장)
- 인간 계정뿐 아니라 서비스 계정·CI/CD 봇·컨테이너·DB 유저에도 동일 원칙 적용

**장점**:
- 침해 시 lateral movement / data exfiltration 범위 축소
- Insider threat 영향 감소
- 컴플라이언스 (PCI DSS 7, SOC 2 CC6) 기본 요구사항

**단점**:
- 운영 마찰 — 권한 요청/승인 프로세스 필요
- 과도하게 적용하면 "shadow IT" 유도
- Role 설계 정밀도 요구

**활용 예시**:
- AWS IAM — `*` 권한 금지, action 단위 명시
- Kubernetes — Pod SecurityContext `runAsNonRoot`, ReadOnly filesystem
- Linux capabilities — `CAP_NET_BIND_SERVICE`만 부여 (전체 root 회피)
- DB user — read-only / write / admin 분리
- CI/CD 봇 — 배포 대상 repo와 환경만 접근 허용

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Dockerfile + Kubernetes Pod — non-root, read-only FS, capability 최소화
// Dockerfile:
//   FROM eclipse-temurin:21-jre-alpine
//   RUN addgroup -S app && adduser -S app -G app
//   USER app:app
//   COPY --chown=app:app app.jar /app/app.jar
//   ENTRYPOINT ["java", "-jar", "/app/app.jar"]
//
// k8s deployment.yaml (excerpt):
//   securityContext:
//     runAsNonRoot: true
//     runAsUser: 10001
//     readOnlyRootFilesystem: true
//     allowPrivilegeEscalation: false
//     capabilities: { drop: ["ALL"] }

// 애플리케이션 레벨: DB user 분리
@Configuration
class DataSourceConfig {
    @Bean("readDs")  fun read():  DataSource = hikari(user = "app_read",  ro = true)
    @Bean("writeDs") fun write(): DataSource = hikari(user = "app_write", ro = false)
    // 보고서 모듈은 readDs만 주입받음 → write 실수 원천 차단
}
```

**관련 패턴**: Zero Trust Architecture, Defense in Depth, security-authz.md, compliance.md#SOC2

---

## 4. Secure by Default (기본값 보안 원칙)

**목적**: 시스템의 초기 상태와 기본 설정이 안전해야 하며, 위험 기능은 사용자가 명시적으로 opt-in해야만 활성화됩니다 (OWASP Secure by Design, NIST SP 800-160).

**특징**:
- 기본값 = 최소 노출: 불필요한 포트·서비스·기능은 기본 비활성화
- Opt-in 위험 노출: 위험한 기능(debug mode, verbose logging, HTTP, anonymous access)은 코드 변경 없이 환경변수/설정으로만 열 수 있게 명시적 설계
- Fail-safe defaults: 오류 발생 시 허용이 아닌 거부로 기본 처리
- 벤더 기본 자격증명 금지: 초기 비밀번호/키는 랜덤 생성 또는 첫 실행 시 강제 변경
- 보안 헤더 기본 활성화: HSTS, X-Content-Type-Options, CSP 등 기본 ON
- 의존성 최소화: 필요 없는 라이브러리/플러그인은 기본 미포함

**장점**:
- 설정 미숙 사용자도 안전한 상태로 시작
- "설정 실수"로 인한 침해 표면 감소 (예: debug endpoint 실수 노출 방지)
- 컴플라이언스 감사에서 기본 구성 안전성 입증 용이

**단점**:
- 편의성·개발 생산성과 충돌 가능 (예: localhost HTTPS 강제)
- 레거시 통합 시 기본 비활성화 기능을 하나하나 열어야 하는 마찰
- 지나치면 "security theater" — 실제 위협 경로가 아닌 곳만 잠금

**활용 예시**:
- Spring Boot Actuator — 기본 `/actuator/**` 전체 비활성화, 필요 endpoint만 `management.endpoints.web.exposure.include`로 명시 허용
- Docker — 기본 root로 실행 → `USER` 명시 없으면 빌드 파이프라인 거부
- Database — 초기 설치 시 `root` 비밀번호 없음 → 첫 접속 시 강제 변경
- API — 인증 없는 endpoint는 `@PermitAll` 명시 필요, 기본은 인증 필수

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Boot — Secure by Default 설정 예시
@Configuration
@EnableWebSecurity
class SecureByDefaultConfig {

    @Bean
    fun securityFilterChain(http: HttpSecurity): SecurityFilterChain = http
        // 기본: 모든 요청 인증 필수 (Secure by Default)
        .authorizeHttpRequests { auth ->
            auth
                .requestMatchers("/health", "/ready").permitAll()  // 명시적 공개만 허용
                .anyRequest().authenticated()                       // 나머지 기본 인증 필요
        }
        // 보안 헤더 기본 활성화 (HSTS, X-Frame-Options, CSP 등)
        .headers { headers ->
            headers
                .httpStrictTransportSecurity { hsts ->
                    hsts.maxAgeInSeconds(31536000).includeSubDomains(true)
                }
                .contentSecurityPolicy { csp ->
                    csp.policyDirectives("default-src 'self'; script-src 'self'")
                }
                .frameOptions { it.deny() }
        }
        // CSRF 기본 활성화 (API-only면 stateless JWT와 함께 비활성화 가능 — 명시적)
        .csrf { csrf -> csrf.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()) }
        .build()
}

// Actuator — 기본 전체 비활성화, 필요 endpoint만 명시 허용
// application.yml:
//   management:
//     endpoints:
//       web:
//         exposure:
//           include: health,info   # 명시적 허용만 활성화
//     endpoint:
//       health:
//         show-details: never      # 기본 상세 비공개

// 환경변수 기반 위험 기능 opt-in — 코드 분기 없이 설정으로만 제어
@ConditionalOnProperty(name = ["debug.endpoints.enabled"], havingValue = "true", matchIfMissing = false)
@RestController
@RequestMapping("/internal/debug")
class DebugController {
    // 기본 비활성화, 환경변수 `DEBUG_ENDPOINTS_ENABLED=true` 명시 시에만 등록
    @GetMapping("/heap-dump") fun heapDump(): ResponseEntity<ByteArray> = TODO()
}
```

**관련 패턴**: Defense in Depth, Least Privilege, security-sdlc.md, security-platform.md

---
