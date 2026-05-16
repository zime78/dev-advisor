# 빌드·버전 관리 패턴 (Build & Versioning Patterns)

소스 관리 + 버전 + 빌드 + 의존성의 9 정평 있는 패턴. Monorepo / Polyrepo / SemVer / CalVer / Hermetic / Reproducible Build 표준.

**원전·표준 참고**:
- Tom Preston-Werner — *Semantic Versioning 2.0* (https://semver.org)
- Bert Belder, Mahmoud Hashemi — *CalVer* (https://calver.org)
- Mahmoud Hashemi — *ZeroVer* (https://0ver.org)
- Google — *Software Engineering at Google* (Winters, Manshreck, Wright, 2020) — Monorepo 사례
- Bazel Documentation — Hermetic & Reproducible Build
- Reproducible Builds project (https://reproducible-builds.org)
- NixOS — Hermetic package management

**Monorepo vs Polyrepo 의사결정**:

| 기준 | Monorepo | Polyrepo |
|------|----------|----------|
| Atomic cross-service refactor | ✓ 쉬움 | ✗ 어려움 |
| 팀 자율성 | △ 통제 필요 | ✓ 독립 |
| CI 비용 | △ selective build 필요 | ✓ 자연 분할 |
| 코드 검색 | ✓ 한 곳 | △ N 곳 |
| 의존성 관리 | ✓ 단일 lockfile | △ N lockfile |
| 적합 | 강한 cohesion 팀 | 마이크로서비스 |

**관련 카탈로그**:
- [deployment.md](deployment.md) — Canary / Blue-Green / Feature Flag
- [`../principles/process-metrics.md`](../principles/process-metrics.md) — Trunk-Based Development / GitOps
- [`../security/security-supply-chain.md`](../security/security-supply-chain.md) — Reproducible Build (보안 관점)

---

<a id="monorepo"></a>

## 1. Monorepo (단일 저장소)

**목적**: 여러 프로젝트·서비스·라이브러리를 하나의 버전 관리 저장소에 모아 atomic cross-cut 변경, 통일된 빌드/테스트 파이프라인, 공유 코드의 즉시 반영을 가능하게 합니다.

**메커니즘**:
- 모든 코드가 단일 repository (`/services/`, `/libs/`, `/apps/` 등으로 분리)
- 빌드 도구가 의존성 그래프를 인식해 변경 영향 범위만 선택적으로 빌드/테스트 (Bazel `bazel test //...`, Nx `nx affected`, Turborepo `turbo run build --filter=...[HEAD~1]`)
- 단일 커밋으로 라이브러리 + 모든 사용처 동시 수정 (atomic refactor)
- 코드 소유권은 `CODEOWNERS` 파일로 디렉토리 기반 관리
- 공통 lint/format/test rule을 root에서 일괄 적용
- 도구: **Bazel** (Google), **Buck/Buck2** (Meta), **Pants** (Twitter), **Nx** (TypeScript/Node), **Turborepo** (Vercel), **Lerna** (legacy JS), **Rush** (Microsoft), **pnpm workspaces**, **Cargo workspaces**, **Go workspaces**

**장점**:
- Atomic cross-cut refactor: 라이브러리 API 변경 시 모든 사용처를 한 커밋에 수정 (Polyrepo는 각 repo 별로 PR + lockfile 갱신 + 배포 순서 조율)
- 단일 lockfile로 의존성 버전 통일 (diamond dependency 회피)
- 코드 검색·grep이 한 곳 (`rg "FooBar" .` 한 번)
- 공통 코드 재사용 마찰 최소 (path import만 추가, publish 불필요)
- CI/CD 파이프라인 일원화

**단점**:
- Repository 크기 폭증 → git clone/fetch 시간 증가 (Meta는 Mercurial + VFS, Google은 Piper + CitC)
- 빌드 그래프 관리 도구(Bazel 등) 학습 비용 — 변경 영향만 빌드하지 않으면 전체 빌드가 수십 분 소요
- 권한 분리가 디렉토리 단위라 미세 제어 어려움 (전체 repo read access 부여 시 보안 문제)
- IDE 인덱싱 부하 (수만 파일)
- 작은 팀에서는 over-engineering

**활용 예시**:
- Google `google3` 모노레포 (수십억 LOC, Piper + Bazel)
- Meta `fbsource` (Mercurial + Buck2)
- Microsoft Office, Windows 일부
- Vercel Turborepo 기반 Next.js + 디자인 시스템 + 문서 공존
- Babel, Jest 등 OSS의 패키지 모음

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제** — Nx 스타일 affected build 결정 로직:
```kotlin
// 변경된 파일 기반으로 영향받는 프로젝트만 빌드하는 스케줄러 (Nx affected의 단순화)
data class Project(
    val name: String,
    val path: String,                    // "/libs/auth"
    val dependsOn: Set<String> = emptySet(),  // 의존하는 프로젝트 name 집합
)

class AffectedProjectResolver(
    private val projects: List<Project>,
    private val changedFiles: List<String>,  // git diff --name-only HEAD~1
) {
    fun resolve(): Set<String> {
        // 1. 변경된 파일을 포함하는 프로젝트 직접 매칭
        val directlyChanged = projects
            .filter { p -> changedFiles.any { it.startsWith(p.path) } }
            .map { it.name }
            .toSet()

        // 2. 의존 그래프 역방향 전파 (영향받는 모든 프로젝트)
        val affected = directlyChanged.toMutableSet()
        var added = true
        while (added) {
            added = false
            for (p in projects) {
                if (p.name in affected) continue
                if (p.dependsOn.any { it in affected }) {
                    affected.add(p.name); added = true
                }
            }
        }
        return affected
    }
}

fun main() {
    val resolver = AffectedProjectResolver(
        projects = listOf(
            Project("auth", "/libs/auth"),
            Project("api-server", "/apps/api", dependsOn = setOf("auth")),
            Project("web", "/apps/web", dependsOn = setOf("auth")),
            Project("docs", "/apps/docs"),  // 의존성 없음
        ),
        changedFiles = listOf("/libs/auth/src/jwt.kt"),  // auth만 변경
    )
    println("빌드 대상: ${resolver.resolve()}")
    // → [auth, api-server, web]  (docs는 영향 없음 → 빌드 skip)
}
```

**관련 패턴**: Polyrepo (반대 전략), Build Caching, Dependency Resolution

---

<a id="polyrepo"></a>

## 2. Polyrepo (다중 저장소)

**목적**: 각 서비스/라이브러리를 독립된 저장소에 두어 팀 자율성, 명확한 책임 경계, 권한 분리를 달성합니다.

**메커니즘**:
- 1 service = 1 repository (또는 1 library = 1 repo)
- 각 repo가 자체 CI/CD, lockfile, 버전, lifecycle 보유
- 라이브러리 공유는 package registry 경유 (npm registry, Maven Central, PyPI, crates.io, 사내 Artifactory/Nexus)
- 버전 호환성은 SemVer 또는 lockfile로 명시
- 도구: GitHub/GitLab repo per project, Renovate/Dependabot으로 의존성 자동 PR

**장점**:
- 팀 자율성 최대 — 각 팀이 자기 repo의 release cadence, 도구, 컨벤션 결정
- 권한 분리 자연스러움 (repo 단위 access control)
- CI 비용 자연 분할 — 한 repo의 빌드가 다른 repo에 영향 없음
- Git clone/fetch 빠름 (repo가 작음)
- 마이크로서비스 아키텍처와 1:1 매핑

**단점**:
- Cross-repo refactor 고통 — 라이브러리 API 변경 시 N개 repo에 PR + 머지 + 배포 순서 조율 필요
- Diamond dependency 위험: A→C(v1), B→C(v2), A+B 동시 사용 시 충돌
- 코드 검색 어려움 (각 repo 따로 검색, GitHub Search/Sourcegraph 의존)
- 공통 패턴(lint, CI 템플릿) 동기화 어려움 (각 repo가 따로 진화)
- 신규 라이브러리 publish 마찰 → 코드 복사로 우회하는 안티패턴 발생

**활용 예시**:
- Netflix (수천 개 마이크로서비스 = 수천 개 repo)
- Spotify backend
- 대부분의 SaaS 스타트업 초기 → 성장하면 Monorepo로 전환 검토
- OSS 생태계 (각 라이브러리가 독립 repo)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제** — Polyrepo 환경의 cross-repo dependency 업데이트 자동화:
```kotlin
// Renovate/Dependabot 스타일: 라이브러리 새 버전 publish 시 사용 repo에 PR 생성
data class DependencyUpdate(
    val library: String,        // "com.example:auth-lib"
    val fromVersion: String,    // "1.2.3"
    val toVersion: String,      // "1.3.0"
    val targetRepos: List<String>,  // 이 라이브러리를 쓰는 모든 repo
)

class CrossRepoUpdater(
    private val createPullRequest: (repo: String, branch: String, title: String) -> Unit,
) {
    fun rollout(update: DependencyUpdate) {
        update.targetRepos.forEach { repo ->
            val branch = "deps/${update.library.replace(':', '-')}-${update.toVersion}"
            val title = "chore(deps): ${update.library} ${update.fromVersion} → ${update.toVersion}"
            println("[Polyrepo] $repo 에 PR 생성: $title")
            createPullRequest(repo, branch, title)
            // 각 repo의 CI가 독립적으로 호환성 검증
            // 머지 순서/일정은 각 팀이 결정
        }
    }
}

fun main() {
    val updater = CrossRepoUpdater(
        createPullRequest = { repo, branch, title ->
            println("  → gh pr create -R $repo -H $branch -t \"$title\"")
        },
    )
    updater.rollout(DependencyUpdate(
        library = "com.example:auth-lib",
        fromVersion = "1.2.3",
        toVersion = "1.3.0",
        targetRepos = listOf("org/api-server", "org/web", "org/mobile-bff"),
    ))
}
```

**관련 패턴**: Monorepo (반대 전략), Dependency Resolution, SemVer

---

<a id="semver"></a>

## 3. Semantic Versioning (SemVer 2.0)

**목적**: 버전 번호 `MAJOR.MINOR.PATCH`로 변경의 영향 범위(breaking / additive / fix)를 명시적으로 통신해 의존성 호환성을 기계적으로 추론합니다.

**메커니즘** (https://semver.org):
- **MAJOR**: 하위 호환되지 않는 API 변경 (breaking change)
- **MINOR**: 하위 호환되는 기능 추가
- **PATCH**: 하위 호환되는 버그 수정
- Pre-release: `1.0.0-alpha.1`, `1.0.0-rc.1` (정식 릴리스 이전)
- Build metadata: `1.0.0+20130313144700` (`+` 뒤는 비교 시 무시)
- `0.y.z`는 초기 개발 단계 — 어떤 변경이든 허용 (1.0.0 도달이 "안정화" 선언)
- 의존성 명시 시 range 사용: npm `^1.2.3` (MAJOR 고정, MINOR/PATCH 허용), `~1.2.3` (MINOR 고정, PATCH만 허용)

**장점**:
- 자동 의존성 해결의 기반 — `^1.2.3` range로 안전한 자동 업그레이드 가능
- API 사용자가 breaking change를 사전 인지 (MAJOR 증가)
- 라이브러리 생태계 표준 (npm, Cargo, Maven, Composer 모두 채택)
- 변경 영향을 commit/PR/changelog에서 일관되게 분류

**단점**:
- "breaking change" 정의가 주관적 — 버그 수정이 의존 코드를 깨뜨리는 경우 발생 (Hyrum's Law: "충분한 사용자가 있으면 관찰 가능한 모든 동작이 누군가에게는 contract")
- 빈번한 MAJOR 증가는 생태계 분열 야기 (Python 2→3, Angular 1→2)
- 0.y.z 단계가 길어지면 사실상 모든 MINOR가 breaking이 되어 SemVer 무의미화 → **ZeroVer** 안티패턴
- 날짜·릴리스 주기 정보 없음 → **CalVer**로 보완 가능

**활용 예시**:
- npm `package.json`의 `"dependencies": { "react": "^18.2.0" }`
- Cargo `Cargo.toml`의 `serde = "1.0"` (SemVer ^ range 기본값)
- Maven `<version>1.2.3</version>` (range는 별도 문법)
- Go modules (Go 1.11+) — `v2+`는 import path에 `/v2` 포함 필수
- 모든 주요 OSS 라이브러리

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제** — SemVer 파싱 및 호환성 판정:
```kotlin
// SemVer 2.0 파서 + range 매처 (npm ^/~ 동작 모사)
data class SemVer(val major: Int, val minor: Int, val patch: Int, val preRelease: String? = null) : Comparable<SemVer> {
    override fun compareTo(other: SemVer): Int = when {
        major != other.major -> major.compareTo(other.major)
        minor != other.minor -> minor.compareTo(other.minor)
        patch != other.patch -> patch.compareTo(other.patch)
        // pre-release가 있으면 정식 버전보다 낮음
        preRelease == null && other.preRelease != null -> 1
        preRelease != null && other.preRelease == null -> -1
        else -> (preRelease ?: "").compareTo(other.preRelease ?: "")
    }

    companion object {
        private val PATTERN = Regex("""^(\d+)\.(\d+)\.(\d+)(?:-([\w.]+))?$""")
        fun parse(s: String): SemVer {
            val m = PATTERN.matchEntire(s) ?: error("잘못된 SemVer 형식: $s")
            return SemVer(m.groupValues[1].toInt(), m.groupValues[2].toInt(),
                m.groupValues[3].toInt(), m.groupValues[4].ifEmpty { null })
        }
    }
}

/** npm ^1.2.3 → MAJOR 고정, MINOR/PATCH 자동 허용 (1.x.x 범위) */
fun caretRange(base: SemVer, candidate: SemVer): Boolean =
    candidate.major == base.major && candidate >= base

/** npm ~1.2.3 → MINOR 고정, PATCH만 자동 허용 (1.2.x 범위) */
fun tildeRange(base: SemVer, candidate: SemVer): Boolean =
    candidate.major == base.major && candidate.minor == base.minor && candidate >= base

fun main() {
    val base = SemVer.parse("1.2.3")
    listOf("1.2.4", "1.3.0", "2.0.0", "1.2.3-rc.1").forEach { v ->
        val c = SemVer.parse(v)
        println("$v: ^range=${caretRange(base, c)}, ~range=${tildeRange(base, c)}")
    }
    // 1.2.4: ^range=true, ~range=true
    // 1.3.0: ^range=true, ~range=false   (MINOR 변경 → ~ 거부)
    // 2.0.0: ^range=false, ~range=false  (MAJOR 변경 → 모두 거부)
    // 1.2.3-rc.1: pre-release → 정식 1.2.3보다 낮음
}
```

**관련 패턴**: CalVer (대체 전략), ZeroVer (안티패턴), Dependency Resolution

---

<a id="calver"></a>

## 4. Calendar Versioning (CalVer)

**목적**: 버전 번호에 릴리스 날짜를 직접 인코딩해 "언제 릴리스되었는가"를 명확히 하고, 시간 의존적 소프트웨어(timezone DB, 데이터 스냅샷 등)의 신선도를 표현합니다.

**메커니즘** (https://calver.org):
- 일반 형식: `YY.MM` / `YY.MM.MICRO` / `YYYY.MM.DD` / `YYYY.0M.0D` (zero-padded)
- 예시:
  - Ubuntu `24.04` (LTS), `24.10` — YY.MM
  - JetBrains IntelliJ `2024.3.1` — YYYY.MINOR.PATCH
  - pip `24.0`, `24.1` — YY.MINOR (2023 이후 CalVer 채택)
  - pytz `2024.1` — 시간대 DB 스냅샷 날짜
  - PyCharm, PyPI 일부 라이브러리
- SemVer의 MAJOR/MINOR/PATCH 의미를 시간 정보로 대체
- 일부 프로젝트는 hybrid 사용: `YYYY.MM.PATCH` (CalVer + PATCH는 SemVer 의미)

**장점**:
- 릴리스 시기가 버전에서 즉시 보임 → EOL 정책·보안 패치 대상 식별 용이
- 빠른 릴리스 주기(monthly/weekly)에서 MAJOR 증가의 의미 상실 문제 회피
- "최신인가?" 판단이 직관적 (`24.10` > `24.04`)
- 시간 의존 데이터(timezone, currency rate, ML model)와 자연스럽게 매핑

**단점**:
- 변경의 영향 범위(breaking 여부) 정보가 버전에서 사라짐 → 별도 CHANGELOG 필수
- 자동 의존성 range 표현 어려움 (`^24.04`의 의미가 모호)
- 릴리스가 미뤄지면 버전 번호와 실제 릴리스 시점 불일치 (예: `24.04`가 2024년 5월 릴리스)
- 라이브러리(특히 API 제공)에는 부적합 — SemVer가 더 적합

**활용 예시**:
- **Ubuntu** `24.04 LTS` — YY.MM, 짝수 해 4월이 LTS
- **JetBrains IDEs** `2024.3.x` — major.minor가 출시 분기
- **pip** `24.0` — 2024년 첫 릴리스
- **pip-tools**, **pytz**, **black** (Python formatter, `24.10.0`)
- **Unity** `2023.2.x` LTS
- **Windows 10** `21H2`, **Windows 11** `23H2` — half-year notation

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제** — CalVer 파서 + 신선도 검사:
```kotlin
// CalVer YYYY.MM.MICRO 형식 파서 + EOL 정책 계산
import java.time.LocalDate
import java.time.temporal.ChronoUnit

data class CalVer(val year: Int, val month: Int, val micro: Int = 0) : Comparable<CalVer> {
    /** 해당 버전의 릴리스 추정일 (해당 월의 1일) */
    fun releaseDate(): LocalDate = LocalDate.of(year, month, 1)

    /** 릴리스 후 경과 일수 */
    fun ageInDays(now: LocalDate = LocalDate.now()): Long =
        ChronoUnit.DAYS.between(releaseDate(), now)

    override fun compareTo(other: CalVer): Int = compareValuesBy(
        this, other, { it.year }, { it.month }, { it.micro }
    )

    companion object {
        private val PATTERN = Regex("""^(\d{4})\.(\d{1,2})(?:\.(\d+))?$""")
        fun parse(s: String): CalVer {
            val m = PATTERN.matchEntire(s) ?: error("CalVer 형식 오류: $s")
            return CalVer(
                m.groupValues[1].toInt(),
                m.groupValues[2].toInt(),
                m.groupValues[3].ifEmpty { "0" }.toInt(),
            )
        }
    }
}

/** EOL 정책: 릴리스 후 N일 경과 시 EOL */
fun isEol(version: CalVer, eolAfterDays: Long = 365): Boolean =
    version.ageInDays() > eolAfterDays

fun main() {
    val v = CalVer.parse("2024.04.1")  // Ubuntu 24.04.1 LTS
    println("릴리스 추정일: ${v.releaseDate()}")
    println("경과일: ${v.ageInDays()} 일")
    println("EOL 여부 (1년 정책): ${isEol(v)}")
}
```

**관련 패턴**: SemVer (대체 전략), ZeroVer

---

<a id="zerover"></a>

## 5. ZeroVer (0ver — "Zero-based Versioning")

**목적**: 의도적으로 `0.y.z` 영역에 머물러 "stable API 약속 없음"을 명시하면서도 실용적 릴리스를 진행합니다. SemVer 1.0의 무게에서 벗어나려는 비공식 패턴.

**메커니즘** (https://0ver.org):
- 버전을 절대로 `1.0.0`에 도달시키지 않음 — `0.x.y` 또는 `0.x` 영구 유지
- SemVer 명세상 `0.y.z`는 모든 변경이 breaking 허용 → 호환성 보장 책임 회피
- 사용자에게 "API가 언제든 바뀔 수 있다"는 신호
- 일부 프로젝트는 의도적으로, 일부는 1.0의 부담을 미루다 관습화

**장점**:
- API 변경에 대한 보장 책임 없음 — 빠른 iteration 가능
- "production-ready" 약속 회피 (사용자 기대치 관리)
- 1.0.0 release 마케팅·심사 부담 없음
- 작은 라이브러리·내부 도구에 적합

**단점**:
- **안티패턴 위험**: 충분히 안정화된 프로젝트가 0.x에 머물면 사용자 혼란 (사실상 production에서 쓰는데 "unstable" 라벨)
- npm `^0.y.z`는 `~0.y.z`처럼 동작 (`^0.2.3` → `0.2.x`만 허용) — 의존성 range 의미 약화
- 보안·감사 대상에서 "0.x 의존성 = 미성숙"으로 분류될 수 있음
- 1.0.0 도달이 영구히 미뤄지면 SemVer 시스템의 의미 부정

**활용 예시**:
- **Sentry SDK** (일부 언어 SDK는 한때 0.x 유지)
- **AWS CLI v1** — 오랫동안 0.x 단계 유지 후 v1, 현재 v2
- **HashiCorp Terraform providers** (일부 community provider)
- **Apache Kafka client libraries** (초기)
- **연구·실험 프로젝트** — 의도적 unstable 라벨

**난이도**: 낮음 | **사용 빈도**: ★★☆☆☆ (의도적 패턴으로는 드물지만 안티패턴으로 흔함)

**Kotlin 예제** — ZeroVer 의존성 range 동작:
```kotlin
// npm semver: 0.y.z range는 caret(^)도 tilde(~)처럼 좁게 해석됨
data class ZeroVer(val minor: Int, val patch: Int) : Comparable<ZeroVer> {
    val major: Int = 0  // 항상 0

    override fun compareTo(other: ZeroVer): Int = compareValuesBy(
        this, other, { it.minor }, { it.patch }
    )

    companion object {
        fun parse(s: String): ZeroVer {
            require(s.startsWith("0.")) { "ZeroVer는 0.x.y 형식만 허용" }
            val parts = s.split(".")
            return ZeroVer(parts[1].toInt(), parts.getOrNull(2)?.toInt() ?: 0)
        }
    }
}

/**
 * npm caret range 동작:
 * - ^1.2.3 → 1.x.x 허용 (MAJOR 고정)
 * - ^0.2.3 → 0.2.x만 허용 (사실상 tilde)
 * - ^0.0.3 → 0.0.3 정확히 (MAJOR=0, MINOR=0이면 PATCH도 고정)
 *
 * 즉 ZeroVer 영역에서는 caret range가 거의 의미 없음 — 자동 업그레이드 통로 좁아짐
 */
fun caretRangeZero(base: ZeroVer, candidate: ZeroVer): Boolean =
    candidate.minor == base.minor && candidate >= base

fun main() {
    val base = ZeroVer.parse("0.2.3")
    listOf("0.2.4", "0.3.0", "0.2.3").forEach { v ->
        val c = ZeroVer.parse(v)
        println("$v: ^range=${caretRangeZero(base, c)}")
    }
    // 0.2.4: ^range=true   (PATCH 변경)
    // 0.3.0: ^range=false  (MINOR 변경 → ZeroVer 영역에서는 breaking 취급)
    // 0.2.3: ^range=true   (동일)
    println("\n결론: 0.x에서는 ^range가 ~range와 동일 → 자동 업그레이드 범위가 좁음")
}
```

**관련 패턴**: SemVer (기반 표준), CalVer (대안)

---

<a id="build-caching"></a>

## 6. Build Caching (빌드 캐싱)

**목적**: 빌드 산출물을 입력 해시 기반으로 캐시·재사용하여 동일 입력은 두 번 다시 빌드하지 않습니다. Hermetic Build를 전제로 한 dramatic build time 단축의 핵심 기법.

**메커니즘**:
- 각 빌드 단계(target)의 입력(소스, 의존성, 컴파일러 버전, 환경 변수)을 해시화
- 해시 → 산출물 매핑을 local cache + remote cache (공유)에 저장
- 동일 해시의 빌드 요청 시 산출물을 fetch만 하고 실제 컴파일 skip
- **Local cache**: 개발자 머신의 `~/.bazel-cache`, `~/.gradle/caches`
- **Remote cache**: 팀 공유 (Bazel Remote Cache, Gradle Build Cache Node, Turborepo Remote Cache, Nx Cloud)
- Hermetic Build 전제 필수 — 외부 상태(시스템 시계, 사용자 환경 변수, 네트워크)가 입력에 포함되면 같은 입력에 다른 출력 발생해 cache 무효화
- 도구: **Bazel** (가장 정교한 캐시 모델), **Buck2**, **Gradle Build Cache**, **Turborepo**, **Nx Cloud**, **sccache** (Rust/C++), **ccache** (C/C++)

**장점**:
- Cross-developer / cross-CI 캐시 공유로 빌드 시간 90%+ 단축 (실측 케이스)
- CI 워밍 비용 절감
- Incremental build의 한계(다른 머신에서 재빌드)를 극복
- 변경되지 않은 의존성의 재빌드 회피

**단점**:
- Cache invalidation 버그 — 입력 해시가 실제로 모든 입력을 포착하지 못하면 stale cache hit으로 잘못된 산출물 사용 (Phil Karlton: "캐시 무효화는 컴퓨터 과학 2대 난제 중 하나")
- Remote cache 인프라 비용 (S3 등)
- Hermetic build 전제가 깨지면 cache 신뢰 불가 (`__DATE__` 매크로, 절대 경로 등)
- 캐시 poisoning 공격 위험 — 누군가 악의적 산출물을 remote cache에 push 가능 (signed cache 필요)

**활용 예시**:
- Google internal: Bazel remote cache + remote execution (RBE) → 빌드 시간 분 단위 → 초 단위
- Vercel Turborepo Remote Cache (npm 모노레포)
- Gradle Enterprise Build Cache Node (사내)
- GitHub Actions `actions/cache`로 의존성 캐시
- Nx Cloud (TypeScript/Node)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제** — 콘텐츠 해시 기반 빌드 캐시:
```kotlin
// Bazel/Turborepo 스타일: 입력 해시 → 산출물 매핑 캐시
import java.security.MessageDigest

data class BuildInput(
    val sourceFiles: Map<String, String>,   // path → content
    val dependencies: List<String>,         // 의존 라이브러리 + 버전
    val toolchainVersion: String,           // 컴파일러 버전 (hermetic 보장)
) {
    /** 모든 입력을 모아 SHA-256 해시 — cache key */
    fun cacheKey(): String {
        val md = MessageDigest.getInstance("SHA-256")
        sourceFiles.entries.sortedBy { it.key }.forEach { (path, content) ->
            md.update(path.toByteArray()); md.update(content.toByteArray())
        }
        dependencies.sorted().forEach { md.update(it.toByteArray()) }
        md.update(toolchainVersion.toByteArray())
        return md.digest().joinToString("") { "%02x".format(it) }.take(16)
    }
}

interface BuildCache {
    fun get(key: String): ByteArray?
    fun put(key: String, artifact: ByteArray)
}

class InMemoryBuildCache : BuildCache {
    private val store = mutableMapOf<String, ByteArray>()
    override fun get(key: String): ByteArray? = store[key]?.also { println("  cache HIT: $key") }
    override fun put(key: String, artifact: ByteArray) {
        store[key] = artifact; println("  cache STORE: $key (${artifact.size} bytes)")
    }
}

class CachedBuilder(private val cache: BuildCache, private val compile: (BuildInput) -> ByteArray) {
    fun build(input: BuildInput): ByteArray {
        val key = input.cacheKey()
        cache.get(key)?.let { return it }       // cache hit → skip compile
        val artifact = compile(input)            // cache miss → compile
        cache.put(key, artifact)
        return artifact
    }
}

fun main() {
    val cache = InMemoryBuildCache()
    val builder = CachedBuilder(cache, compile = { input ->
        println("  실제 컴파일 실행: ${input.sourceFiles.keys}")
        "binary-for-${input.cacheKey()}".toByteArray()
    })
    val input = BuildInput(
        sourceFiles = mapOf("Main.kt" to "fun main() {}"),
        dependencies = listOf("kotlin-stdlib:1.9.0"),
        toolchainVersion = "kotlinc-1.9.0",
    )
    builder.build(input)  // miss → 컴파일
    builder.build(input)  // hit → skip
}
```

**관련 패턴**: Hermetic Build (전제), Reproducible Build, Monorepo

---

<a id="hermetic-build"></a>

## 7. Hermetic Build (격리 빌드)

**목적**: 빌드 결과가 호스트 환경(설치된 컴파일러, PATH, 시스템 라이브러리, 네트워크 상태)에 의존하지 않도록 모든 입력을 명시적으로 선언하고 격리합니다. Reproducible Build와 Build Caching의 전제 조건.

**메커니즘**:
- 모든 의존성(컴파일러, SDK, 시스템 라이브러리, 외부 도구)을 빌드 정의에서 명시적으로 pin
- 네트워크 접근 차단 또는 사전 fetch만 허용 (빌드 중 외부 다운로드 금지)
- 환경 변수 화이트리스트만 노출 (`USER`, `HOSTNAME` 등 노출 금지)
- 빌드 sandbox에서 실행 (`/tmp` 격리, 절대 경로 차단)
- 시스템 시계(`__DATE__`, `__TIME__`) 등 비결정적 입력 회피
- 도구: **Bazel** (sandboxed execution + toolchain pinning), **NixOS / Nix** (모든 의존성을 store hash로 pin), **Docker reproducible builds**, **Buck2**, **Pants**

**장점**:
- 동일 입력 → 동일 출력 보장 (Reproducible Build 가능)
- Build Caching의 cache key 신뢰성 확보 (입력이 명시적이라 해시 가능)
- "내 머신에선 되는데"(works on my machine) 문제 제거
- CI ↔ 개발자 환경 차이 제거 → 디버깅 시간 단축
- 공급망 보안 — 모든 의존성이 명시되어 SBOM 생성 용이

**단점**:
- 초기 설정 비용 큼 — 시스템 라이브러리까지 모두 pin 필요
- 빌드 시스템 학습 곡선 (Bazel, Nix)
- 일부 도구는 hermetic 환경에서 동작 불가 (네이티브 컴파일 시 시스템 헤더 필요 등)
- 디스크 사용량 증가 (각 빌드가 자체 sandbox로 격리)
- Legacy 빌드 시스템 마이그레이션 비용

**활용 예시**:
- Google internal Blaze/Bazel → 모든 의존성이 third_party/에 vendored
- NixOS — 시스템 전체가 hermetic (각 패키지가 격리된 store path)
- **bazel** + **rules_docker** — Hermetic Docker image 생성
- **Reproducible Builds project** — Debian 패키지 reproducible 만들기
- Apple Xcode build (sandbox-exec)
- Chromium 빌드 시스템 (GN + Ninja + sysroot)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제** — Hermetic 환경 검증기:
```kotlin
// 빌드 시작 전 환경이 hermetic한지 검증 (실패 시 빌드 중단)
class HermeticEnvironmentChecker {
    data class Violation(val rule: String, val detail: String)

    fun check(env: Map<String, String>, declaredInputs: Set<String>): List<Violation> {
        val violations = mutableListOf<Violation>()

        // 1. 환경 변수 화이트리스트 외 값 노출 금지
        val allowedEnvKeys = setOf("PATH_TO_TOOLCHAIN", "BAZEL_WORKSPACE")
        env.keys.filter { it !in allowedEnvKeys }.forEach {
            violations.add(Violation("env-leak", "허용되지 않은 환경 변수 노출: $it"))
        }

        // 2. 의존성이 모두 declared inputs에 있는지 검증
        val systemDeps = setOf("/usr/bin/gcc", "/opt/homebrew/bin/cmake")
        systemDeps.forEach { dep ->
            if (dep !in declaredInputs) {
                violations.add(Violation("undeclared-dep", "선언되지 않은 시스템 의존성: $dep"))
            }
        }

        // 3. 네트워크 접근 의심 패턴
        if (env["HTTP_PROXY"] != null || env["HTTPS_PROXY"] != null) {
            violations.add(Violation("network-access", "빌드 중 네트워크 접근 가능 — sandbox에서 차단 필요"))
        }

        return violations
    }
}

fun main() {
    val checker = HermeticEnvironmentChecker()
    val env = mapOf(
        "PATH_TO_TOOLCHAIN" to "/opt/bazel/toolchain",
        "USER" to "alice",                    // ← 위반
        "HTTPS_PROXY" to "http://proxy:8080", // ← 위반
    )
    val declaredInputs = setOf("/opt/bazel/toolchain/bin/gcc")  // /usr/bin/gcc 누락
    val violations = checker.check(env, declaredInputs)
    if (violations.isEmpty()) {
        println("Hermetic 검증 통과 → 빌드 진행")
    } else {
        println("Hermetic 검증 실패:")
        violations.forEach { println("  [${it.rule}] ${it.detail}") }
        // 빌드 중단
    }
}
```

**관련 패턴**: Build Caching (의존), Reproducible Build (조합), Dependency Resolution

---

<a id="reproducible-build"></a>

## 8. Reproducible Build (재현 가능 빌드)

**목적**: 동일한 소스 코드 + 동일한 빌드 환경에서 누가, 언제, 어디서 빌드하더라도 **bit-for-bit 동일한 산출물**을 생성합니다. 공급망 보안의 핵심 — 배포된 binary가 공개된 소스에서 정직하게 만들어졌음을 독립 검증 가능.

**메커니즘** (https://reproducible-builds.org):
- Hermetic Build 위에 비결정성(non-determinism) 제거 추가
- **타임스탬프 정규화**: `__DATE__`/`__TIME__` 매크로 제거, archive 내 파일 mtime을 fixed value(`SOURCE_DATE_EPOCH` 환경 변수)로 설정
- **파일 순서 정규화**: 디렉토리 순회 결과를 정렬 후 처리 (FS 순서 의존 제거)
- **랜덤 시드 제거**: ASLR 주소, UUID 생성, 임시 파일명 등
- **절대 경로 제거**: 빌드 경로(`/home/alice/...`)가 산출물에 박히지 않도록 `-fdebug-prefix-map` 등 사용
- **컴파일러 출력 정규화**: 병렬 컴파일 순서 의존 제거
- 검증: 두 머신에서 빌드 → `sha256sum`이 같은지 비교 (`diffoscope`로 차이 분석)
- 도구: **Debian Reproducible Builds**, **Fedora**, **NixOS**, **Bazel** (`stamp = False`), **Bitcoin Core Gitian**, **rules_docker** reproducible mode

**장점**:
- **공급망 보안의 근간** — 빌드 서버가 해킹돼도 독립 빌드로 산출물 검증 가능 (SolarWinds 사건 방지)
- 산출물 무결성을 cryptographic hash로 증명
- 누구나 빌드 검증 참여 가능 (분산 신뢰)
- Build cache의 정합성 보장
- SBOM(Software Bill of Materials) 정확성 확보

**단점**:
- 비결정성 제거 작업이 매우 디테일 — 수십 개의 미세한 원인 (mtime, sort order, locale, parallelism)
- 일부 컴파일러·도구가 inherently non-deterministic (수정 PR 필요)
- 디버깅 어려움 — 차이 분석을 `diffoscope`로 수작업
- 빌드 시간 약간 증가 (정렬, 정규화 overhead)
- Code signing은 reproducible 검증 후 별도 적용 필요

**활용 예시**:
- **Debian** — 전체 패키지의 95%+가 reproducible (2024 기준)
- **Tor Browser** — reproducible 빌드 의무화
- **Bitcoin Core** — Gitian builder + 다중 빌더 서명
- **NixOS** — store hash가 곧 reproducibility 보증
- **Apple notarization + transparency log** (Sigstore 유사)
- **SLSA Level 4** (Supply-chain Levels for Software Artifacts) 요구 조건

**난이도**: 매우 높음 | **사용 빈도**: ★★★☆☆ (보안 중요 도메인에서 필수)

**Kotlin 예제** — Reproducible archive 생성기:
```kotlin
// JAR/ZIP 생성 시 reproducibility 보장: 파일 순서 정렬 + mtime 고정 + 사용자 정보 제거
import java.io.ByteArrayOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class ReproducibleArchiveBuilder(
    /** SOURCE_DATE_EPOCH — 모든 파일의 mtime을 이 값으로 고정 */
    private val sourceDateEpoch: Long = 1577836800L,  // 2020-01-01 UTC
) {
    fun build(files: Map<String, ByteArray>): ByteArray {
        val out = ByteArrayOutputStream()
        ZipOutputStream(out).use { zip ->
            // 핵심: 파일 순서를 이름순으로 정렬 (FS 순회 순서 의존 제거)
            files.entries.sortedBy { it.key }.forEach { (path, content) ->
                val entry = ZipEntry(path).apply {
                    time = sourceDateEpoch * 1000  // mtime 고정
                    // creationTime/lastAccessTime도 명시적으로 고정
                    creationTime = java.nio.file.attribute.FileTime.fromMillis(sourceDateEpoch * 1000)
                    lastAccessTime = java.nio.file.attribute.FileTime.fromMillis(sourceDateEpoch * 1000)
                }
                zip.putNextEntry(entry)
                zip.write(content)
                zip.closeEntry()
            }
        }
        return out.toByteArray()
    }
}

fun sha256(bytes: ByteArray): String =
    java.security.MessageDigest.getInstance("SHA-256")
        .digest(bytes).joinToString("") { "%02x".format(it) }.take(16)

fun main() {
    val builder = ReproducibleArchiveBuilder()
    val files = mapOf(
        "Main.class" to "binary-content-A".toByteArray(),
        "Lib.class" to "binary-content-B".toByteArray(),
    )

    // 두 번 빌드 → 동일 해시 확인
    val hash1 = sha256(builder.build(files))
    Thread.sleep(100)  // 시간 차이가 있어도 mtime이 고정되므로 무관
    val hash2 = sha256(builder.build(files))

    println("빌드 1: $hash1")
    println("빌드 2: $hash2")
    println("Reproducible: ${hash1 == hash2}")
    // 보안 관점은 `../security/security-supply-chain.md` 의 SLSA·서명·SBOM 항목 참고
}
```

**관련 패턴**: Hermetic Build (전제), Build Caching, Supply Chain Security ([`../security/security-supply-chain.md`](../security/security-supply-chain.md))

---

<a id="dependency-resolution"></a>

## 9. Dependency Resolution (의존성 해결)

**목적**: 프로젝트가 선언한 의존성과 그 transitive(전이) 의존성 사이의 버전 충돌을 해결하고, lockfile로 정확한 버전 그래프를 고정해 재현 가능한 빌드를 보장합니다.

**메커니즘**:
- 선언된 의존성: `dependencies` (직접) + transitive (간접)
- **Version range**: SemVer `^1.2.3`, `~1.2.3`, `>=1.0,<2.0` 등 허용 범위 명시
- **Resolution algorithm**:
  - npm/yarn: nearest-wins (트리에서 가장 가까운 의존성이 우선)
  - Cargo: SemVer-aware unification (compatible range는 가장 높은 버전으로 통합)
  - Maven: nearest-wins + dependency mediation
  - pip: backtracking resolver (2020-)
- **Lockfile**: 해결된 정확한 버전 그래프를 파일로 저장 → 팀원·CI가 동일 그래프 재현
  - `package-lock.json` (npm), `yarn.lock` (Yarn), `Cargo.lock` (Cargo), `poetry.lock` (Poetry), `Gemfile.lock` (Bundler), `pnpm-lock.yaml`, `requirements.txt` (pip-tools compile)
- **Diamond dependency**: A→C v1, B→C v2, A+B 동시 사용 시 두 버전 공존 또는 강제 통합
  - npm: 두 버전 둘 다 설치 (nested node_modules) — 디스크 비용
  - Maven/Cargo: 강제 통합 (호환 가능하면 higher version, 아니면 에러)

**장점**:
- Lockfile로 빌드 재현성 보장 (오늘 빌드 == 6개월 후 빌드)
- 버전 충돌을 빌드 시간에 자동 감지 (런타임 ClassNotFoundException 방지)
- 보안 패치 적용 시 transitive까지 자동 갱신 (Dependabot/Renovate 활용)
- Vendor lock-in 없이 의존성 표준 관리

**단점**:
- Lockfile 머지 충돌 빈번 (큰 PR일수록 lockfile diff가 큼)
- Transitive dependency가 폭발 — `node_modules` 수천 패키지
- Version range 정책 따라 자동 업그레이드가 깨질 수 있음 (caret range가 minor bump 받아옴)
- Diamond dependency가 풀리지 않으면 강제 override 필요 (npm `overrides`, Yarn `resolutions`)
- 사슬 보안 취약점 — transitive에 취약점이 있어도 lockfile에 박혀 자동 갱신 안 됨

**활용 예시**:
- npm/yarn `package.json` + `package-lock.json` / `yarn.lock`
- Cargo `Cargo.toml` + `Cargo.lock` — Rust 표준
- Go modules `go.mod` + `go.sum` (해시 포함으로 무결성 검증)
- Maven Central + `pom.xml` (lockfile은 별도 `dependency-lock-maven-plugin`)
- Python `pyproject.toml` + `poetry.lock` 또는 `requirements.txt` (pip-tools compile)
- Renovate / Dependabot 자동 PR

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제** — nearest-wins resolution + lockfile 생성:
```kotlin
// 의존성 그래프를 풀어 단일 버전 매핑으로 변환 (npm nearest-wins 모사)
data class Dependency(val name: String, val version: String, val deps: List<Dependency> = emptyList())

class NearestWinsResolver {
    /** BFS로 의존성 트리를 순회하면서 처음 만난 버전을 채택 */
    fun resolve(root: Dependency): Map<String, String> {
        val resolved = mutableMapOf<String, String>()
        val queue = ArrayDeque<Dependency>().apply { add(root) }
        while (queue.isNotEmpty()) {
            val d = queue.removeFirst()
            if (d.name !in resolved) {
                resolved[d.name] = d.version  // nearest-wins: 처음 만난 버전 채택
                queue.addAll(d.deps)
            }
            // 이미 결정된 이름은 skip (transitive에서 다른 버전 와도 무시)
        }
        return resolved
    }
}

/** 해결된 버전 그래프를 lockfile 형식으로 직렬화 */
fun toLockfile(resolved: Map<String, String>): String =
    "# Auto-generated lockfile — do not edit\n" +
    resolved.entries.sortedBy { it.key }.joinToString("\n") { "${it.key} == ${it.value}" }

fun main() {
    // 예: my-app → react@18.2.0, my-app → redux@4.2.0 → react@17.0.0 (transitive)
    // nearest-wins: my-app의 직접 의존성 react@18.2.0이 우선
    val root = Dependency("my-app", "1.0.0", listOf(
        Dependency("react", "18.2.0"),
        Dependency("redux", "4.2.0", listOf(
            Dependency("react", "17.0.0"),  // transitive → 무시됨
        )),
    ))
    val resolved = NearestWinsResolver().resolve(root)
    println("Resolved versions:")
    println(toLockfile(resolved))
    // my-app == 1.0.0
    // react == 18.2.0   (17.0.0은 transitive라 채택되지 않음)
    // redux == 4.2.0
}
```

**관련 패턴**: SemVer (range 의미), Monorepo (단일 lockfile), Polyrepo (lockfile per repo), Build Caching

> **관련 (P1 신설)**: 빌드·릴리스의 형상 관리 측면은 [`../principles/configuration-management.md#baseline-three-types`](../principles/configuration-management.md#baseline-three-types) (Functional / Allocated / Product Baseline 3종) 와 [`../principles/configuration-management.md#scmp-ieee-828`](../principles/configuration-management.md#scmp-ieee-828) (IEEE 828 SCMP) 참조 — CI 식별·Baseline 확립의 표준.

---
