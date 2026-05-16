# DevSecOps SDLC 보안 패턴 (DevSecOps SDLC Security Patterns)

소프트웨어 개발 생명주기(SDLC) 각 단계에 보안 활동을 내재화하는 패턴 모음. "보안은 나중에" 문화에서 "Security by Design"으로 전환하기 위한 DevSecOps 실천법. OWASP SAMM / NIST SSDF / SLSA Framework를 기반으로 한다.

---

## 1. Threat Modeling (STRIDE / DREAD / PASTA)

**목적**: 설계 단계에서 시스템이 직면할 위협을 체계적으로 식별하고 우선순위를 매겨, 코드 작성 전에 보안 요구사항을 도출합니다.

**특징**:
- **STRIDE** (Microsoft): 위협 유형 분류 프레임워크
  - **S**poofing (위장): 타인 신원 사칭 → 대응: 인증(Authentication)
  - **T**ampering (변조): 데이터/코드 무단 수정 → 대응: 무결성 검증, 서명
  - **R**epudiation (부인): 행위 사실 부인 → 대응: 감사 로그, 디지털 서명
  - **I**nformation Disclosure (정보 유출): 민감 데이터 노출 → 대응: 암호화, 최소 권한
  - **D**enial of Service (서비스 거부): 가용성 침해 → 대응: Rate limiting, Circuit Breaker
  - **E**levation of Privilege (권한 상승): 불법 권한 획득 → 대응: 인가(Authorization), RBAC
- **DREAD**: 위험도 점수화 (Damage / Reproducibility / Exploitability / Affected users / Discoverability 각 1~10 점수)
- **CVSS v4**: 취약점 자체의 기술적 심각도. 네트워크 노출, 공격 복잡도, 권한, 사용자 상호작용, 기밀성/무결성/가용성 영향을 정량화
- **EPSS**: 실제 악용 가능성 예측 점수. CVSS가 높아도 EPSS가 낮으면 우선순위 조정 가능하지만, 인터넷 노출·민감 데이터·권한 상승이 있으면 보수적으로 상향
- **CISA KEV**: 이미 실제 악용된 취약점 목록. KEV 등재 항목은 기본 P1 release blocker로 취급
- **OWASP Risk Rating**: threat agent, vulnerability, technical impact, business impact를 분리해 제품 맥락을 반영
- **보정 축**: 데이터 민감도, blast radius, exploitability, compensating control, risk acceptance 만료일을 함께 기록
- **PASTA** (Process for Attack Simulation and Threat Analysis): 7단계 비즈니스 중심 위협 모델링
  1. 비즈니스 목표 정의 → 2. 기술 범위 정의 → 3. 애플리케이션 분해 → 4. 위협 분석
  5. 취약점 분석 → 6. 공격 모델링 → 7. 위험 분석 및 대응책
- **도구**: OWASP Threat Dragon, Microsoft Threat Modeling Tool, IriusRisk, Miro/Confluence 다이어그램

**장점**:
- 구현 전 설계 결함 발견 → 수정 비용이 수십~수백 배 낮음 (IBM 연구: 설계 단계 버그 수정 비용 = 운영 단계의 1/100)
- 개발팀이 보안 요구사항을 코드로 번역하기 전에 이해하게 됨
- 규제(PCI-DSS 6.3.2, ISO 27001 A.14.2) 요구 증적 자료로 활용

**단점**:
- 숙련된 퍼실리테이터 없으면 형식적 체크리스트로 전락
- 대규모 시스템에서 DFD(Data Flow Diagram) 작성에 상당한 시간 소요
- 아키텍처 변경 시 위협 모델 동기화 관리 필요

**활용 예시**:
- 신규 마이크로서비스 설계 리뷰 시 STRIDE 워크숍 (2시간)
- 결제 시스템 API 변경 전 PASTA 7단계 문서 작성
- Sprint 0에서 팀 전체가 DFD 기반 STRIDE 위협 식별

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**risk acceptance 기준**:
- 소유자, 만료일, 대체 통제, 재검토 조건이 없으면 risk acceptance로 인정하지 않는다.
- PII/결제/의료/권한 상승/공개 인터넷 노출이 있으면 acceptance보다 차단 또는 완화가 기본값이다.
- CVSS ≥ 7.0, EPSS 상위권, CISA KEV 등재, exploitability 높음 중 하나라도 있으면 `security-audit` 통합 severity는 최소 P1 후보로 올린다.

**예제 — STRIDE 위협 매핑 테이블 (결제 API)**:
```markdown
| 컴포넌트         | 위협 유형 | 위협 시나리오                          | DREAD 점수 | 대응책                          |
|-----------------|----------|--------------------------------------|-----------|--------------------------------|
| POST /payments  | Spoofing  | 타인 JWT 토큰 재사용                   | 7.2       | jti claim 검증, 짧은 만료시간   |
| Payment DB      | Tampering | DML 직접 실행으로 금액 변조            | 9.0       | DB 감사 로그, ORM only 접근     |
| 결제 로그       | Repudiation| 거래 사실 부인                        | 6.5       | 불변 감사 로그(S3 WORM)         |
| 카드 번호 필드  | Info Disc  | 응답에 PAN 평문 노출                   | 9.5       | 토크나이제이션, PCI-DSS 마스킹  |
| 결제 게이트웨이 | DoS       | 외부 PG 지연으로 스레드 고갈           | 7.0       | Circuit Breaker, Timeout       |
| 관리자 API      | EoP       | 일반 사용자가 환불 승인 API 접근       | 8.5       | RBAC, Scope 검증               |
```

**관련 패턴**: SAST, DAST, SCA, OAuth2/OIDC (security.md)

---

## 2. SAST (Static Application Security Testing)

**목적**: 소스코드 또는 바이트코드를 실행하지 않고 정적으로 분석하여, SQL Injection / XSS / 하드코딩 자격증명 / 안전하지 않은 암호화 알고리즘 등의 취약점을 코드 리뷰/CI 단계에서 발견합니다.

**특징**:
- **Semgrep**: 경량 패턴 매칭 기반, 커스텀 룰 작성 용이, 100+ 언어 지원, CI 통합 속도 빠름
- **SonarQube**: 코드 품질 + 보안 통합, Security Hotspot / Vulnerability 구분, 게이트 정책
- **CodeQL** (GitHub): 코드를 데이터베이스로 변환 후 SQL 유사 쿼리로 취약점 패턴 탐색, 복잡한 taint analysis 가능
- Taint Analysis: 외부 입력(source) → 위험 함수(sink) 경로 추적 (SQL query 파라미터, eval() 등)
- SARIF (Static Analysis Results Interchange Format): 도구 간 결과 표준화 포맷 → GitHub Security tab 통합

**장점**:
- 코드 실행 환경 불필요 — PR 단계에서 즉시 피드백
- 수천 줄 코드베이스를 수 분 안에 전수 검사
- 개발자 IDE 플러그인(SonarLint, Semgrep VS Code)으로 코딩 중 실시간 탐지

**단점**:
- False Positive 비율 높음 — 억제(suppression) 관리 없으면 노이즈로 전락
- 비즈니스 로직 취약점(IDOR, 권한 우회)은 탐지 어려움 — DAST/수동 리뷰 보완 필요
- CodeQL은 분석 시간 길고(대형 프로젝트 30분+), Actions 무료 플랜 제한

**활용 예시**:
- PR 생성 시 Semgrep으로 OWASP Top 10 패턴 자동 스캔, 인라인 코멘트
- SonarQube Quality Gate: 신규 코드 취약점 0개 통과 조건 설정
- 야간 CodeQL 분석 → Security Advisories 자동 생성

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**GitHub Actions YAML 예제**:
```yaml
name: SAST Security Scan

on:
  pull_request:
  push:
    branches: [main]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep
    steps:
      - uses: actions/checkout@v4

      - name: Semgrep OWASP / 하드코딩 자격증명 스캔
        run: |
          semgrep scan \
            --config "p/owasp-top-ten" \
            --config "p/secrets" \
            --config "p/kotlin" \
            --sarif \
            --output semgrep.sarif \
            --error          # 취약점 발견 시 exit 1 (CI 블로킹)
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}

      - name: SARIF → GitHub Security tab 업로드
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: semgrep.sarif

  codeql:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: CodeQL 초기화
        uses: github/codeql-action/init@v3
        with:
          languages: java-kotlin
          queries: security-extended   # 기본보다 확장된 보안 쿼리 세트

      - name: AutoBuild
        uses: github/codeql-action/autobuild@v3

      - name: CodeQL 분석
        uses: github/codeql-action/analyze@v3
```

**Kotlin 예제 — Semgrep 커스텀 룰 (SQL Injection)**:
```yaml
# .semgrep/custom-rules.yaml
rules:
  - id: kotlin-raw-sql-injection
    languages: [kotlin]
    severity: ERROR
    message: "원시 SQL 문자열에 외부 입력 직접 삽입 — SQL Injection 위험. JPA/QueryDSL 파라미터 바인딩을 사용하세요."
    pattern: |
      val $QUERY = "... $INPUT ..."
      $DATASOURCE.query($QUERY, ...)
    metadata:
      cwe: "CWE-89"
      owasp: "A03:2021"
```

**관련 패턴**: DAST, SCA, Pre-commit Secret Scan, Threat Modeling

---

## 3. DAST (Dynamic Application Security Testing)

**목적**: 실행 중인 애플리케이션에 악성 입력을 주입하고 응답을 분석하여, 정적 분석으로 발견하기 어려운 런타임 취약점(XSS, CSRF, XXE, 인증 우회 등)을 발견합니다.

**특징**:
- **OWASP ZAP** (Zed Attack Proxy): 무료 오픈소스, Active/Passive Scan, API 스캔(OpenAPI/GraphQL), CI 통합용 CLI/Docker 이미지 제공
- **Burp Suite Professional**: 업계 표준 수동 + 자동 펜테스트 도구, Burp Collaborator(OOB 탐지), BChecks 커스텀 스캔
- **Nuclei**: 템플릿 기반 고속 스캐너, 7000+ 커뮤니티 템플릿, CVE/misconfiguration 특화
- Passive Scan: 트래픽 관찰만, 서비스 영향 없음 — QA 환경 상시 실행 가능
- Active Scan: 실제 공격 페이로드 전송 — 반드시 격리된 테스트 환경에서만 실행
- API Security Testing: OpenAPI spec 기반 자동 퍼징 (ZAP API Scan, Burp Scan)

**장점**:
- 인증된 세션에서 실제 취약점 재현 — SAST 오탐 검증 수단
- 빌드/배포 완료 후 운영 환경과 동일한 조건에서 검사
- 비즈니스 로직 취약점(가격 변조, 권한 우회) 발견 가능

**단점**:
- Active Scan은 DB 오염, 서비스 중단 유발 가능 — 전용 테스트 환경 필수
- 복잡한 인증 흐름(OAuth2, MFA) 설정이 까다롭고 오류 발생 쉬움
- 자동화 스캔 커버리지 한계 — 중요 기능은 수동 펜테스트 병행 필요

**활용 예시**:
- 스테이징 배포 후 ZAP Baseline Scan으로 OWASP Top 10 자동 검증
- Burp Suite로 분기 1회 외부 펜테스트 수행
- Nuclei로 신규 CVE 템플릿 릴리즈 후 자사 인프라 즉시 스캔

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**GitHub Actions YAML 예제**:
```yaml
name: DAST — ZAP Scan

on:
  push:
    branches: [main]       # staging 배포 후 트리거

jobs:
  zap-scan:
    runs-on: ubuntu-latest
    steps:
      - name: 스테이징 서버 헬스체크 대기
        run: |
          for i in {1..30}; do
            curl -sf https://staging.example.com/api/v1/healthz && break
            echo "헬스체크 대기 중... ${i}/30"
            sleep 10
          done

      - name: ZAP Baseline Scan (Passive — 서비스 영향 없음)
        uses: zaproxy/action-baseline@v0.12.0
        with:
          target: "https://staging.example.com"
          rules_file_name: ".zap/rules.tsv"    # 억제 규칙
          cmd_options: "-a"                     # Alpha passive rules 포함
          fail_action: true                     # 경고 이상 발견 시 CI 실패

      - name: ZAP API Scan (OpenAPI spec 기반)
        uses: zaproxy/action-api-scan@v0.7.0
        with:
          target: "https://staging.example.com/api/v1/openapi.json"
          format: openapi
          fail_action: true

      - name: 스캔 리포트 아티팩트 저장
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: zap-report
          path: report_html.html
```

**관련 패턴**: SAST, IAST, Threat Modeling

---

## 4. IAST (Interactive Application Security Testing)

**목적**: 애플리케이션 내부에 에이전트를 삽입하여 실제 실행 경로(테스트 / QA / 운영 트래픽)를 관찰하고, SAST와 DAST의 맹점인 런타임 데이터 흐름 취약점을 정밀하게 탐지합니다.

**특징**:
- **Contrast Security**: JVM / .NET / Node.js / Python 에이전트, Assess(IAST) + Protect(RASP) 모드
- **Seeker (Synopsys)**: Java/Python/Node.js 지원, CI/CD 통합, SCA 연동
- **HCL AppScan IAST**: 엔터프라이즈급, 다양한 언어/프레임워크 지원
- 에이전트 동작: 바이트코드 인스트루멘테이션(Bytecode Instrumentation) — 소스코드 수정 불필요
- **Taint Tracking**: 외부 입력이 JVM 런타임에서 어떤 메서드를 거쳐 sink에 도달하는지 실시간 추적 → False Positive 거의 없음
- **RASP** (Runtime Application Self-Protection): Protect 모드에서 공격 탐지 즉시 차단 (프로덕션 적용 가능)

**장점**:
- SAST 대비 False Positive 90% 이상 감소 — 실제 실행 경로만 분석
- 기능 테스트 실행 중 동시에 보안 검사 — 별도 보안 테스트 시간 절약
- 코드 수정 불필요 — 에이전트 JVM 옵션 추가만으로 활성화

**단점**:
- 상용 도구 라이선스 비용 높음 (Contrast Security 연간 수천만 원 규모)
- 에이전트 오버헤드 5~15% CPU/메모리 증가 — 프로덕션 적용 시 부하 테스트 선행 필수
- 에이전트가 지원하지 않는 JVM 버전/프레임워크에서 미동작

**활용 예시**:
- QA 환경 통합 테스트 실행 시 Contrast Assess 에이전트로 동시에 취약점 탐지
- 프로덕션에 Contrast Protect(RASP) 적용으로 제로데이 공격 실시간 차단
- 레거시 코드베이스에 SAST 도입 전 빠른 취약점 현황 파악

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin (Spring Boot) 예제 — Contrast 에이전트 적용**:
```kotlin
// build.gradle.kts — 에이전트 다운로드 태스크
tasks.register("downloadContrastAgent") {
    doLast {
        // Contrast Security Maven 저장소에서 에이전트 다운로드
        val agentUrl = "https://repo.contrastsecurity.com/repository/..." +
            "contrast-agent-${contrastVersion}.jar"
        // CI에서 CONTRAST_API_KEY 환경변수로 인증
    }
}

// JVM 옵션으로 에이전트 삽입 (소스코드 수정 불필요)
// bootRun { jvmArgs("-javaagent:/path/to/contrast.jar") }
```

```yaml
# Docker Compose — IAST 에이전트 탑재 QA 환경
services:
  app-iast:
    image: myapp:latest
    environment:
      JAVA_TOOL_OPTIONS: >-
        -javaagent:/opt/contrast/contrast.jar
        -Dcontrast.application.name=myapp-qa
        -Dcontrast.server.name=qa-server
      CONTRAST__API__URL: "https://app.contrastsecurity.com/Contrast"
      CONTRAST__API__API_KEY: "${CONTRAST_API_KEY}"
      CONTRAST__API__SERVICE_KEY: "${CONTRAST_SERVICE_KEY}"
      CONTRAST__API__USER_NAME: "${CONTRAST_USER}"
    volumes:
      - contrast-agent:/opt/contrast:ro

volumes:
  contrast-agent:
    external: true
```

**관련 패턴**: SAST, DAST, SCA

---

## 5. SCA (Software Composition Analysis)

**목적**: 프로젝트가 의존하는 오픈소스 라이브러리의 알려진 CVE(취약점), 라이선스 위반, deprecated 패키지를 자동으로 탐지하고, 수정 버전으로의 업그레이드를 제안합니다.

**특징**:
- **Snyk**: Developer-first SCA, IDE/CLI/CI 통합, 자동 Fix PR 생성, Container/IaC 스캔 통합
- **Dependabot** (GitHub 내장): `dependabot.yml` 설정만으로 의존성 업그레이드 PR 자동 생성, Security Advisories 연동
- **OSV-Scanner** (Google): [osv.dev](https://osv.dev) CVE DB 기반, 무료/오픈소스, SBOM 파일 스캔 지원
- **OWASP Dependency-Check**: NIST NVD 기반, Java/JavaScript/Python 등 지원, HTML/XML 리포트
- **SBOM** (Software Bill of Materials): CycloneDX / SPDX 포맷으로 의존성 트리 문서화 — 공급망 보안의 기반
- Transitive Dependency: 직접 의존성보다 간접(transitive) 의존성에서 취약점 발생 빈도 높음

**장점**:
- Log4Shell, Spring4Shell 류 대형 취약점 발생 시 수천 개 저장소를 수 분 안에 전수 검사
- Dependabot은 GitHub 무료 플랜도 사용 가능 — 진입 비용 없음
- SBOM 생성으로 규제(미 행정명령 EO 14028) 대응

**단점**:
- Dependabot 자동 PR이 테스트 없이 머지되면 breaking change 유발 → 자동 머지 정책 주의
- CVE DB 오탐 및 동일 취약점 중복 보고 — 억제 파일(`snyk policy`, `.dependency-check-suppression.xml`) 관리 필요
- Java Gradle multi-module 프로젝트에서 의존성 그래프 분석 오류 발생 가능

**활용 예시**:
- 모든 PR에서 Snyk 스캔, CVSS ≥ 7.0 발견 시 CI 블로킹
- Dependabot으로 patch 버전 업그레이드 PR 자동 생성, CI 통과 시 자동 머지
- 주간 OSV-Scanner 스캔 → 신규 CVE Slack 알림

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**GitHub Actions YAML 예제**:
```yaml
name: SCA — 의존성 취약점 스캔

on:
  pull_request:
  schedule:
    - cron: "0 9 * * 1"    # 매주 월요일 09:00 UTC

jobs:
  snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Snyk 의존성 취약점 스캔
        uses: snyk/actions/gradle@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: >-
            --severity-threshold=high
            --sarif-file-output=snyk.sarif
            --fail-on=upgradable      # 업그레이드 가능한 취약점만 블로킹

      - name: SARIF 업로드
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: snyk.sarif

  osv-scanner:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: OSV-Scanner (Google — 무료)
        uses: google/osv-scanner-action@v1
        with:
          scan-args: |-
            --format=sarif
            --output=osv-results.sarif
            -r
            ./

      - name: SBOM 생성 (CycloneDX)
        run: |
          npm install -g @cyclonedx/cyclonedx-npm
          cyclonedx-npm --output-file sbom.json
          # 또는 Gradle: ./gradlew cyclonedxBom

      - uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.json
```

```yaml
# .github/dependabot.yml — 자동 의존성 업그레이드 PR
version: 2
updates:
  - package-ecosystem: gradle
    directory: "/"
    schedule:
      interval: weekly
      day: monday
    open-pull-requests-limit: 10
    groups:
      spring-boot:
        patterns: ["org.springframework.boot*"]
    ignore:
      - dependency-name: "com.example:legacy-lib"
        update-types: ["version-update:semver-major"]

  - package-ecosystem: docker
    directory: "/"
    schedule:
      interval: weekly
```

**관련 패턴**: SAST, Pre-commit Secret Scan, Image Signing (security-platform.md)

---

## 6. Pre-commit Secret Scan (gitleaks / trufflehog)

**목적**: API 키, 비밀번호, 개인키, JWT 서명 키 등 시크릿이 Git 커밋에 포함되기 전, 개발자 로컬 머신의 pre-commit hook 단계에서 차단합니다.

**특징**:
- **gitleaks**: Go 기반 고속 스캐너, 정규식 + 엔트로피 분석 기반, 전체 Git 히스토리 스캔 가능
  - `gitleaks protect` — 스테이징 된 변경사항 pre-commit 검사
  - `gitleaks detect` — 전체 저장소 히스토리 스캔
- **trufflehog**: 엔트로피 분석 특화, 유효성 검증(실제 API 호출로 시크릿 작동 여부 확인), AWS/Slack/GitHub 토큰 자동 인식
- **pre-commit framework**: `.pre-commit-config.yaml`으로 팀 전체에 동일한 hook 버전 배포
- GitHub Actions Secret Scanning: 푸시 후 즉시 GitHub이 알림 발송 (Public 저장소 무료, Private는 GHAS)
- 히스토리 정리: 시크릿이 이미 커밋되었으면 `git filter-repo` + 시크릿 즉시 rotate (히스토리 삭제만으로는 불충분 — cached/forked 복사본 존재 가능)

**장점**:
- 커밋 전 차단 — 이미 푸시된 시크릿은 rotate해도 히스토리에 영구 기록됨
- 팀 전체 설치: `pre-commit install` 한 줄로 통일된 정책 강제
- gitleaks는 오픈소스 무료, 커스텀 룰 확장 용이

**단점**:
- 개발자가 `--no-verify`로 hook을 우회 가능 → CI에도 동일 검사 필수
- 정규식 기반 탐지는 커스텀 내부 시크릿 포맷 미탐지 (커스텀 패턴 추가 필요)
- 이미 커밋된 히스토리 정리는 협업자 로컬 저장소 업데이트 강제 — 운영 비용 높음

**활용 예시**:
- 모든 개발자 로컬에 `pre-commit install` 의무화, 신규 개발 환경 세팅 스크립트에 포함
- GitHub Actions에서도 gitleaks 실행 — `--no-verify` 우회 방어
- `.gitleaks.toml`에 내부 API 토큰 패턴 추가 (예: `KAKAO_API_KEY_[A-Z0-9]{32}`)

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**bash / YAML 예제**:
```bash
# 1. pre-commit 설치 (macOS)
brew install pre-commit
cd /your/project
pre-commit install           # .git/hooks/pre-commit 자동 설치
pre-commit install --hook-type commit-msg   # 커밋 메시지 검사도 필요 시

# 2. 전체 히스토리 gitleaks 스캔 (최초 도입 시)
gitleaks detect --source . --verbose --log-opts="HEAD~100..HEAD"

# 3. 시크릿 발견 시 rotate 후 히스토리 정리
git filter-repo --path secrets.env --invert-paths --force
# ⚠️  force push 후 모든 collaborator에게 fresh clone 요청 필수
```

```yaml
# .pre-commit-config.yaml — 팀 공유 hook 설정
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.88.2
    hooks:
      - id: trufflehog
        name: trufflehog (staged 변경만)
        entry: trufflehog git file://.
        args:
          - "--since-commit"
          - "HEAD"
          - "--only-verified"   # 실제 작동하는 시크릿만 보고
          - "--fail"
```

```yaml
# GitHub Actions — CI에서도 동일 검사 (--no-verify 우회 방어)
name: Secret Scan

on: [push, pull_request]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0        # 전체 히스토리 스캔을 위해 full clone

      - name: gitleaks — 시크릿 유출 검사
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}  # 상용 기능 사용 시
```

```toml
# .gitleaks.toml — 내부 커스텀 패턴 추가
title = "Gitleaks Custom Rules"

[[rules]]
id = "kakao-internal-api-key"
description = "Kakao 내부 API 키 패턴"
regex = '''KAKAO_[A-Z_]+_KEY_[A-Za-z0-9]{32,}'''
tags = ["kakao", "api-key"]

[[rules]]
id = "jira-api-token"
description = "Atlassian API 토큰 패턴"
regex = '''ATATT3xFfGF0[A-Za-z0-9+/]{100,}'''
tags = ["atlassian", "jira"]

[allowlist]
description = "테스트용 더미 시크릿 억제"
regexes = [
  '''DUMMY_KEY_FOR_TESTING''',
  '''example\.com/fake-token''',
]
```

**관련 패턴**: SAST, SCA, IaC Scanning (security-platform.md)
