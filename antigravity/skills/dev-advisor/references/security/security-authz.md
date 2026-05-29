# 인가 패턴 (Authorization Patterns)

인가(Authorization)는 인증된 주체(Principal)가 특정 리소스/액션에 접근할 권한이 있는지 판정하는 단계다. RBAC / ABAC / ReBAC 세 모델이 정책 표현력의 축을 이루고, Policy as Code (OPA / Cedar) 가 이를 코드로 외부화하며, Permission Boundary / Least Privilege / JWT Claims-based Authz 가 운영 레벨에서 권한을 제한·전달하는 패턴이다. NIST INCITS 359-2004 (RBAC), NIST SP 800-162 (ABAC), Google Zanzibar 논문 (Pang et al., USENIX ATC 2019, ReBAC), AWS IAM Permission Boundary, RFC 7519 (JWT) / RFC 8693 (Token Exchange) 등 표준을 기반으로 한다.

> 본 파일은 인가 도메인 전용 정본이다. `patterns/security.md` 의 기존 RBAC/ABAC 항목은 본 파일로 통합 이관되며 추후 제거된다.

---

## 1. RBAC (Role-Based Access Control)

**목적**: 사용자에게 직접 권한을 부여하지 않고 **역할(Role)** 을 매개로 권한을 묶어 관리합니다. NIST INCITS 359-2004 (구 NIST RBAC) 표준 모델 — Core / Hierarchical / Constrained (SoD) 4단계로 정의됩니다.

**특징**:
- 3-tuple: `User ─ Role ─ Permission` (User-Role assignment + Role-Permission assignment)
- Role Hierarchy: Senior Role 이 Junior Role 의 권한 상속 (예: `Admin > Manager > Employee`)
- SoD (Separation of Duty): 상호 배타적 역할 동시 보유 금지 (Static SoD / Dynamic SoD)
- 권한 판정: `hasRole(user, role)` + `roleHasPermission(role, perm)` 의 join
- 정책이 정적 — 사용자 속성·리소스 속성·시간/위치 조건 표현 불가

**장점**:
- 모델 단순 — 운영 직관적, 감사(audit) 추적 용이
- 조직도/직무 구조에 자연 매핑 (HR 시스템과 sync 쉬움)
- 변경 비용 낮음 — 권한 묶음을 Role 단위로 일괄 수정

**단점**:
- "이 문서 owner 만 수정 가능" 같은 인스턴스 단위 권한 표현 불가 → Role Explosion 발생
- 동적 조건 (IP, 시간, 디바이스 신뢰도) 표현 불가
- 조직이 커지면 Role 수가 사용자 수보다 빠르게 증가하는 안티패턴

**활용 예시**:
- 사내 어드민 콘솔 (Super Admin / Operator / Viewer)
- Kubernetes RBAC (ClusterRole / Role + RoleBinding)
- AWS IAM Group + Managed Policy
- 일반적 SaaS 의 "관리자/멤버/게스트" 3-tier

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Security 6 — Role Hierarchy + @PreAuthorize
@Configuration
@EnableMethodSecurity
class RbacConfig {
    @Bean
    fun roleHierarchy(): RoleHierarchy = RoleHierarchyImpl().apply {
        setHierarchy("ROLE_ADMIN > ROLE_MANAGER\nROLE_MANAGER > ROLE_EMPLOYEE")
    }

    @Bean
    fun methodSecurityExpressionHandler(rh: RoleHierarchy) =
        DefaultMethodSecurityExpressionHandler().apply { setRoleHierarchy(rh) }
}

@RestController
class ReportController {
    // ADMIN, MANAGER 둘 다 통과 (계층 상속)
    @PreAuthorize("hasRole('MANAGER')")
    @GetMapping("/reports")
    fun listReports(): List<Report> = ...

    // SoD: ADMIN 이면서 AUDITOR 일 수 없음
    @PreAuthorize("hasRole('AUDITOR') and !hasRole('ADMIN')")
    @PostMapping("/audit/sign")
    fun signAudit(): Unit = ...
}
```

**관련 패턴**: ABAC (속성 확장), ReBAC (관계 기반), Permission Boundary

---

## 2. ABAC (Attribute-Based Access Control)

**목적**: 주체(Subject) / 액션(Action) / 리소스(Resource) / 환경(Environment) 의 **속성(Attribute)** 을 조합한 정책(Policy)으로 권한을 판정합니다. NIST SP 800-162 가이드와 OASIS XACML 3.0 이 표준 reference 입니다.

**특징**:
- 4-범주 속성: Subject (department, clearance), Resource (owner, classification), Action (read/write), Environment (time, IP, MFA 여부)
- PEP / PDP / PIP / PAP 4 컴포넌트 분리 (Enforcement / Decision / Information / Administration Point)
- 정책 표현: `permit if subject.dept == resource.dept AND env.time IN business_hours`
- Combining Algorithm: `permit-overrides`, `deny-overrides`, `first-applicable`
- 의사결정 결과: Permit / Deny / NotApplicable / Indeterminate

**장점**:
- Fine-grained — 인스턴스 단위 / 조건부 권한 표현 가능
- 동적 조건 (시간, 위치, 디바이스 상태, 리스크 점수) 자연스럽게 표현
- 정책 중앙화 → 코드 변경 없이 권한 룰 수정 (PAP 에서 배포)

**단점**:
- 정책 검증/디버깅 난이도 높음 — "왜 거부됐는가" 추적이 RBAC 보다 어려움
- 속성 조회 비용 (PIP latency) 이 매 요청마다 발생
- XACML XML 은 verbose — 실무에서는 OPA Rego / Cedar 같은 modern DSL 권장

**활용 예시**:
- 금융권 거래 승인 ("거래액 > 1억 이면 부서장 결재 + MFA + 9-18시")
- 의료 정보 시스템 (담당의 + 환자 동의 + 진료중 상태)
- 클라우드 리소스 ("태그가 env=prod 이면 production 그룹만 수정")
- 정부/방산 다단계 보안 (clearance level vs document classification)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// 간이 ABAC PDP — Subject/Resource/Action/Env 속성 평가
data class AbacRequest(
    val subject: Map<String, Any>,   // {id, dept, clearance, mfa}
    val resource: Map<String, Any>,  // {id, owner, classification}
    val action: String,              // "read" / "write" / "delete"
    val env: Map<String, Any>,       // {ip, time, riskScore}
)

sealed class Decision { object Permit : Decision(); object Deny : Decision() }

class FinancialPdp {
    fun evaluate(req: AbacRequest): Decision {
        val amount = req.resource["amount"] as? Long ?: 0
        val dept = req.subject["dept"] as? String
        val mfa = req.subject["mfa"] as? Boolean ?: false
        val hour = (req.env["time"] as java.time.LocalTime).hour

        // Policy: 1억 초과 거래는 finance 부서 + MFA + 9-18시
        if (req.action == "approve" && amount > 100_000_000) {
            if (dept != "finance" || !mfa || hour !in 9..18) return Decision.Deny
        }
        // Default: owner 만 자기 자원 수정
        if (req.action == "write" && req.subject["id"] != req.resource["owner"]) {
            return Decision.Deny
        }
        return Decision.Permit
    }
}
```

**관련 패턴**: Policy as Code (OPA/Cedar 로 정책 외부화), RBAC (속성으로 role 만 쓰면 RBAC 와 동일)

---

## 3. ReBAC (Relationship-Based Access Control)

**목적**: 주체와 객체 사이의 **관계 그래프(Relationship Graph)** 를 따라 권한을 판정합니다. Google Zanzibar 논문 (Pang et al., USENIX ATC 2019) 이 reference 모델이며, SpiceDB / OpenFGA / AuthZed 가 오픈소스 구현체입니다.

**특징**:
- 관계 튜플(Relation Tuple): `object#relation@user` (예: `document:report1#viewer@user:alice`)
- 관계 그래프 탐색으로 권한 판정 ("alice 가 report1 의 viewer 인가?")
- Userset Rewrite: `editor ⊆ viewer` (editor 면 자동으로 viewer)
- Computed Userset / Tuple-to-Userset 으로 폴더→문서 상속 표현
- Zookies (consistency token) 으로 stale 데이터 방지
- Google Drive / Docs / YouTube / Photos 의 공유 모델 구현체

**ReBAC vs RBAC vs ABAC 비교**:

| 측면 | RBAC | ABAC | ReBAC |
|---|---|---|---|
| 권한 표현 단위 | Role | Attribute 조합 | 관계 그래프 |
| 인스턴스 단위 권한 | 약함 (Role explosion) | 강함 (속성으로) | **강함 (튜플로)** |
| 동적 조건 (시간/IP) | 불가 | 강함 | 보통 (caveat 필요) |
| 상속/계층 | Role hierarchy | 정책으로 표현 | **그래프 자연 표현** |
| "친구의 친구" | 불가 | 어려움 | **자연** |
| 정책 디버깅 | 쉬움 | 어려움 | 보통 (그래프 시각화) |
| 대표 사례 | 어드민 콘솔 | 금융/의료 | Google Drive, GitHub |

**장점**:
- 공유/협업 모델 (Drive, Notion, Figma 류) 에 자연 매핑
- 인스턴스 단위 권한이 그래프 튜플로 깔끔하게 표현됨
- "팀의 멤버이면 팀이 소유한 모든 문서 view" 같은 전이적 권한이 native

**단점**:
- 정책 변경 시 grant/revoke 가 그래프 mutation — 일관성 관리 (Zookies) 필요
- 그래프 깊이가 깊으면 latency 증가 (Zanzibar 는 SLO p99 < 10ms 목표로 캐시 layer 보유)
- 동적 조건 (시간/IP) 표현이 ABAC 보다 약함 → OpenFGA 의 Contextual Tuples / SpiceDB Caveats 로 보완

**활용 예시**:
- Google Drive 공유 (folder → file 상속 + 직접 공유 + 그룹 공유)
- GitHub 권한 (org → team → repo → branch protection)
- Notion / Figma / Linear 의 workspace → page 권한
- SaaS multi-tenant ("이 워크스페이스의 admin 인 user")

**난이도**: 높음 | **사용 빈도**: ★★★☆☆ (B2B SaaS / 협업 도구에서 ★★★★★)

**Kotlin 예제**:
```kotlin
// OpenFGA Kotlin SDK 사용 — Zanzibar style check
val fga = OpenFgaClient(
    ClientConfiguration().apply {
        apiUrl = "http://localhost:8080"
        storeId = "01HXYZ..."
        authorizationModelId = "01HABC..."
    }
)

// 1) 권한 부여: alice 가 report1 의 editor
fga.write(ClientWriteRequest(writes = listOf(
    ClientTupleKey(user = "user:alice", relation = "editor", _object = "document:report1")
)))

// 2) 권한 검사: alice 가 report1 을 볼 수 있는가? (editor ⊆ viewer)
val allowed = fga.check(ClientCheckRequest(
    user = "user:alice",
    relation = "viewer",
    _object = "document:report1",
)).allowed
// → true (editor 면 viewer 자동 포함)

// 3) 그룹 멤버십 + 폴더 상속
// document:report1#parent@folder:q1, folder:q1#member@team:eng, team:eng#member@user:alice
// → alice 가 자동으로 report1 의 viewer
```

**관련 패턴**: RBAC (역할도 관계 튜플로 표현 가능), Policy as Code, Caveats (조건부 관계)

---

## 4. Policy as Code (OPA Rego / AWS Cedar)

**목적**: 권한 정책을 코드 외부의 **선언적 DSL** 로 분리하여 버전 관리·테스트·배포·감사를 코드처럼 운용합니다. CNCF Graduated 프로젝트 OPA (Open Policy Agent) 의 Rego, AWS 의 Cedar 가 대표 구현체입니다.

**특징**:
- 정책을 텍스트 파일로 분리 → Git 으로 review/diff/rollback
- PDP 외부화 — 애플리케이션은 정책 변경 시 재배포 불필요
- 단위 테스트 가능 (`opa test policy_test.rego`)
- 결정 로그(decision log) → 감사 추적
- OPA Rego: Datalog 기반, JSON in/out, side-effect 없는 pure function
- AWS Cedar: 정형 분석 가능(소수 결정 가능, formal verification), AWS Verified Permissions 매니지드 서비스

**장점**:
- 정책 변경에 코드 빌드/배포 불필요
- 정책 단위 테스트 → 정책 회귀 방지
- 다양한 워크로드 (Kubernetes Admission, API Gateway, microservice, Terraform plan) 통일된 PDP

**단점**:
- 별도 PDP 운영 부담 (sidecar / centralized service)
- Rego 학습 곡선 — Datalog 패러다임이 절차형 개발자에게 낯섦
- 잘못 설계하면 every-request OPA 호출이 latency 증가

**활용 예시**:
- Kubernetes Admission Controller (Gatekeeper, Kyverno)
- API Gateway / Envoy ext_authz
- Terraform plan validation (정책 위반 plan 차단)
- AWS Cedar 로 멀티 테넌트 SaaS 권한 (Verified Permissions)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제 + Rego 정책**:
```rego
# policy.rego — "owner 거나 admin role 이면 허용, 단 production 리소스는 MFA 필수"
package authz

default allow := false

allow if {
    input.resource.owner == input.user.id
    not production_without_mfa
}
allow if {
    "admin" in input.user.roles
    not production_without_mfa
}
production_without_mfa if {
    input.resource.env == "prod"
    not input.user.mfa
}
```

```kotlin
// Kotlin → OPA REST API 호출 (sidecar @ localhost:8181)
class OpaAuthzClient(private val http: HttpClient) {
    suspend fun allow(user: Map<String, Any>, resource: Map<String, Any>): Boolean {
        val body = mapOf("input" to mapOf("user" to user, "resource" to resource))
        val res: OpaResponse = http.post("http://localhost:8181/v1/data/authz/allow") {
            contentType(ContentType.Application.Json); setBody(body)
        }.body()
        return res.result == true
    }
}
// Cedar 비교: policy { permit(principal, action, resource) when { principal == resource.owner }; }
// — Cedar 는 형식 검증(formal analysis)으로 "모든 deny 정책이 reachable 한가" 같은 검증 가능
```

**관련 패턴**: ABAC (정책 표현 모델), ReBAC (OPA + Zanzibar style), Permission Boundary (정책으로 표현)

---

## 5. Permission Boundary

**목적**: Identity 가 가질 수 있는 **최대 권한의 상한(upper bound)** 을 정책으로 제한하여, 위임된 관리자가 자기 권한을 초과하는 권한 부여를 못 하도록 막습니다. AWS IAM 의 Permissions Boundary 가 대표 사례입니다.

**특징**:
- 유효 권한(effective permissions) = `identity policy ∩ permission boundary` (교집합만 허용)
- 권한 위임 패턴 — junior admin 에게 "S3 boundary 안에서만 user 생성/정책 부여" 권한 위임
- explicit deny 와 함께 사용 시 deny 우선
- AWS 외에 GCP Org Policy, Azure Management Group Policy 도 유사 개념
- "권한이 있어도 boundary 가 없으면 차단" — 명시적 화이트리스트

**장점**:
- 위임 권한 안전망 — 위임받은 admin 의 권한 부여 실수/악의 방지
- Blast radius 최소화 — 침해된 identity 가 boundary 밖 리소스 침입 불가
- Compliance 요구(SOC2/ISO27001) 의 "최소 권한 검증" 자동 충족

**단점**:
- 디버깅 어려움 — "왜 권한이 있는데도 막혔는가" 는 boundary 미허용일 가능성
- AWS IAM 외에는 native 지원이 약함 — 자체 구현 시 복잡
- Boundary 정책 자체의 휴먼 에러 (너무 좁으면 운영 마비)

**활용 예시**:
- AWS 멀티 어카운트 — 개발팀 admin 에게 dev account 내 자원만 관리 가능하도록 boundary
- 외주 개발자 / 컨설턴트 임시 권한 — 기간 + 리소스 boundary 동시 적용
- SaaS 의 tenant admin — tenant 내 자원만 관리, 다른 tenant 접근 차단
- 침해 대응 — 침해 의심 identity 에 강제 boundary 적용해 격리

**난이도**: 중간 | **사용 빈도**: ★★★★☆ (클라우드 운영)

**Kotlin 예제** (자체 구현 모델):
```kotlin
// AWS IAM Permission Boundary 의미를 Kotlin 으로 모델링
data class Policy(val allowedActions: Set<String>, val allowedResources: Set<String>)

class BoundedAuthorizer(
    private val identityPolicy: Policy,
    private val boundary: Policy,  // 상한 (없으면 모든 권한 거부)
) {
    fun allow(action: String, resource: String): Boolean {
        val inIdentity = action in identityPolicy.allowedActions &&
                         resource in identityPolicy.allowedResources
        val inBoundary = action in boundary.allowedActions &&
                         resource in boundary.allowedResources
        return inIdentity && inBoundary   // 교집합만 허용
    }
}

// 예: junior admin 에게 "user 생성 권한" 부여했지만 boundary 는 "S3/dev-*" 만 허용
val identity = Policy(setOf("iam:CreateUser", "s3:*"), setOf("*"))
val boundary = Policy(setOf("s3:GetObject", "s3:PutObject"), setOf("arn:aws:s3:::dev-*"))
val authz = BoundedAuthorizer(identity, boundary)
authz.allow("iam:CreateUser", "*")                              // false — boundary 밖
authz.allow("s3:PutObject", "arn:aws:s3:::dev-logs/x.log")     // true
authz.allow("s3:PutObject", "arn:aws:s3:::prod-logs/x.log")    // false — boundary 밖
```

**관련 패턴**: Least Privilege, Policy as Code, Zero Trust

---

## 6. Least Privilege (구현 패턴: Just-Enough-Access / Time-Bound)

**목적**: 주체에게 **작업 수행에 꼭 필요한 최소 권한을 최소 시간 동안만** 부여합니다. Saltzer & Schroeder (1975) 의 8대 보안 설계 원칙 중 하나로, 현대에는 JEA (Just-Enough-Access) / JIT (Just-In-Time) 으로 구체화됩니다.

**특징**:
- Standing privilege (상시 권한) → Just-in-Time 권한으로 전환
- 권한 요청 → 승인 워크플로우 → 시간 제한(TTL) → 자동 회수
- 작업별 권한 분리 (read 작업은 read-only role 로만)
- Break-glass account: 비상 시에만 사용, 사용 즉시 감사 알림
- 권한 사용 로그 분석 → 미사용 권한 자동 회수 (right-sizing)
- 구현 예: Azure PIM, AWS IAM Identity Center + Permission Sets, Teleport, HashiCorp Boundary

**장점**:
- 침해 시 blast radius 최소화 — 침해된 계정의 권한이 적고 짧음
- Insider threat 완화 — 평소엔 권한 없음
- Compliance (SOC2/PCI-DSS/HIPAA) 의 "최소 권한" 요구 자동 충족
- 감사 로그 풍부 (누가/언제/왜 elevated 했는가)

**단점**:
- UX 마찰 — 권한 요청 승인 대기로 작업 흐름 끊김
- 승인 자동화 부재 시 운영 부담 폭증
- 비상 상황에서 break-glass 절차 정의 안 되면 장애 대응 지연

**활용 예시**:
- 프로덕션 DB 접근 — JIT 권한 (15분 TTL, 사유 + 승인자 1명 필수)
- AWS Console 의 sensitive action (IAM 변경) — MFA + 세션 시간 제한
- Kubernetes kubectl exec 권한 — Teleport 로 시간 제한 토큰 발급
- 외주 개발자 — PR 머지 시점에만 권한 활성

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// JIT(Just-In-Time) 권한 발급 시스템 — 사유/승인자/TTL 강제
data class JitGrant(
    val grantId: UUID,
    val user: String,
    val role: String,
    val reason: String,        // 필수, 감사 로그용
    val approver: String,      // 필수
    val expiresAt: Instant,    // TTL
    val mfaVerified: Boolean,
)

class JitAuthorizer(
    private val clock: Clock,
    private val store: GrantStore,
    private val auditLog: AuditLog,
) {
    fun requestElevation(req: ElevationRequest): JitGrant {
        require(req.reason.length >= 10) { "사유 10자 이상 필수" }
        require(req.ttl <= Duration.ofMinutes(60)) { "최대 1시간" }
        require(req.mfaVerified) { "MFA 필수" }

        val grant = JitGrant(
            grantId = UUID.randomUUID(),
            user = req.user, role = req.role, reason = req.reason,
            approver = req.approver,
            expiresAt = clock.instant().plus(req.ttl),
            mfaVerified = true,
        )
        store.save(grant)
        auditLog.write("JIT_GRANTED", grant)
        return grant
    }

    fun isActive(user: String, role: String): Boolean =
        store.findActive(user, role, clock.instant()) != null
}
// 만료된 grant 는 cron 으로 회수 + 사용 안 한 standing 권한은 right-sizing 보고서로 노출
```

**관련 패턴**: Permission Boundary, JWT Claims-based (`exp` 로 TTL), Zero Trust

---

## 7. JWT Claims-based Authorization

**목적**: JWT (RFC 7519) 의 **claims (scope / aud / role / 커스텀 속성)** 을 인가 결정의 입력으로 사용해 stateless 한 권한 판정을 수행합니다. OAuth2 Resource Server 의 표준 패턴입니다.

**특징**:
- 표준 claim: `iss` (발급자), `sub` (주체), `aud` (대상 audience), `exp` (만료), `scope` (OAuth2 권한 범위, RFC 8693)
- 커스텀 claim: `roles`, `permissions`, `tenant_id`, `mfa_level`, `risk_score`
- Scope 검증 — coarse-grained ("이 API 를 부를 수 있는가")
- Role/Permission claim — fine-grained ("어떤 액션을 수행할 수 있는가")
- `aud` 검증 필수 — 다른 audience 에 발급된 토큰 재사용 차단 (Confused Deputy 방지)
- Token 크기 제한 — claim 이 많으면 HTTP header 크기 폭증 (8KB 한계)

**장점**:
- Stateless — DB 조회 없이 토큰만으로 권한 판정 (latency 짧음)
- 분산 시스템 — microservice 간 user context 전파 (token relay)
- 표준 (RFC 7519 / 8693 / 9068) 광범위 지원

**단점**:
- 즉시 폐기 불가 — 권한 회수가 토큰 만료까지 지연 (revocation list / short TTL + refresh 로 보완)
- Token bloat — claim 많이 넣으면 header 크기 폭증
- Token 도난 시 만료까지 악용 — sender-constrained token (DPoP, mTLS) 으로 보완

**활용 예시**:
- API Gateway 에서 `scope` 검증 후 backend 로 user context 전달
- Microservice 간 service-to-service (Client Credentials grant + `aud` 분리)
- Mobile / SPA 가 REST API 호출 (`Authorization: Bearer <jwt>`)
- 멀티 테넌트 SaaS — `tenant_id` claim 으로 row-level filter

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Spring Security 6 — Resource Server: scope + aud + custom claim 검증
@Configuration
@EnableMethodSecurity
class JwtAuthzConfig {
    @Bean
    fun securityFilterChain(http: HttpSecurity): SecurityFilterChain =
        http
            .oauth2ResourceServer { oauth2 ->
                oauth2.jwt { jwt ->
                    jwt.jwtAuthenticationConverter(jwtConverter())
                }
            }
            .authorizeHttpRequests { it.anyRequest().authenticated() }
            .build()

    /** JWT 의 `roles` / `scope` 를 Spring Authority 로 매핑 */
    private fun jwtConverter(): JwtAuthenticationConverter =
        JwtAuthenticationConverter().apply {
            setJwtGrantedAuthoritiesConverter { jwt ->
                val scopes = jwt.getClaimAsStringList("scope").orEmpty()
                    .map { SimpleGrantedAuthority("SCOPE_$it") }
                val roles = jwt.getClaimAsStringList("roles").orEmpty()
                    .map { SimpleGrantedAuthority("ROLE_$it") }
                scopes + roles
            }
        }

    /** aud claim 검증 — 다른 audience 토큰 재사용 차단 */
    @Bean
    fun jwtDecoder(): JwtDecoder {
        val decoder = NimbusJwtDecoder
            .withJwkSetUri("https://idp.example.com/.well-known/jwks.json")
            .build()
        decoder.setJwtValidator(DelegatingOAuth2TokenValidator(
            JwtValidators.createDefaultWithIssuer("https://idp.example.com"),
            JwtClaimValidator<List<String>>("aud") { aud -> "api.example.com" in aud },
        ))
        return decoder
    }
}

@RestController
class OrderController {
    // OAuth2 scope 기반
    @PreAuthorize("hasAuthority('SCOPE_orders:read')")
    @GetMapping("/orders") fun list(): List<Order> = ...

    // Custom claim 으로 tenant 격리
    @GetMapping("/orders/{id}")
    fun get(@PathVariable id: Long, @AuthenticationPrincipal jwt: Jwt): Order {
        val tenantId = jwt.getClaimAsString("tenant_id")
        return orderRepo.findByIdAndTenantId(id, tenantId) ?: throw NotFoundException()
    }
}
```

**관련 패턴**: OAuth2 / OIDC, RBAC (roles claim), ABAC (custom claim 으로 속성 전달), Least Privilege (`exp` TTL)

---
