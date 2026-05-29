# 공급망 보안 패턴 (Software Supply Chain Security)

소스 코드 → 빌드 → 의존성 → 아티팩트 → 배포 전 과정에서 발생하는 무결성/출처/비밀(secret) 위협을 다루는 패턴 모음. **SLSA Framework** (Supply-chain Levels for Software Artifacts, Google + OpenSSF) 와 **US Executive Order 14028** (Improving the Nation's Cybersecurity, 2021), **NIST SSDF (SP 800-218, Secure Software Development Framework)** 를 표준 기반으로 한다. SolarWinds(2020), Codecov(2021), Log4Shell(2021), xz-utils backdoor(2024) 사고 이후 산업 전반에서 필수 통제로 자리잡았다.

---

## 1. SBOM (Software Bill of Materials)

**목적**: 소프트웨어 아티팩트에 포함된 모든 컴포넌트(직접/전이 의존성, 라이선스, 버전, 해시)를 기계가 읽을 수 있는 표준 포맷으로 명세하여, 취약점 발견 시 영향 범위를 즉시 식별하고 라이선스 컴플라이언스를 보장한다.

**특징**:
- 표준 포맷: **CycloneDX** (OWASP, JSON/XML/Protobuf), **SPDX** (Linux Foundation, ISO/IEC 5962:2021)
- 컴포넌트 식별자: PURL (Package URL), CPE (Common Platform Enumeration), SWID
- 빌드 시점 자동 생성 후 아티팩트와 함께 배포 (in-toto attestation 으로 서명)
- 취약점 스캐너 (Grype, Trivy, Dependency-Track) 가 SBOM 을 입력으로 CVE 매칭
- US EO 14028 §4(e) 에 따라 연방정부 납품 SW 필수 제출 요건

**장점**:
- Log4Shell 같은 zero-day 시 "우리 제품에 영향 있나?" 를 분 단위로 답변
- 라이선스 위반 (GPL contamination) 사전 감지
- M&A / 보안 감사 시 due diligence 산출물로 활용

**단점**:
- 전이 의존성 깊이가 깊으면 SBOM 크기 폭증 (수천~수만 컴포넌트)
- 동적 로드/리플렉션 사용 라이브러리는 정적 스캔으로 누락 가능
- SBOM 신선도(freshness) 관리 — 의존성 업데이트마다 재생성 필요

**활용 예시**:
- npm 프로젝트: `@cyclonedx/cyclonedx-npm` 로 CycloneDX JSON 생성
- Gradle: `org.cyclonedx.bom` 플러그인 → `build/reports/bom.json`
- Maven: `cyclonedx-maven-plugin`
- 컨테이너 이미지: `syft packages docker:myimage:tag -o cyclonedx-json`

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**예제** (CycloneDX JSON):
```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "timestamp": "2026-05-13T09:00:00Z",
    "component": { "type": "application", "name": "billing-api", "version": "1.4.0" }
  },
  "components": [
    {
      "type": "library",
      "bom-ref": "pkg:maven/org.springframework/spring-core@6.1.5",
      "name": "spring-core",
      "version": "6.1.5",
      "purl": "pkg:maven/org.springframework/spring-core@6.1.5",
      "hashes": [{ "alg": "SHA-256", "content": "9a1f..." }],
      "licenses": [{ "license": { "id": "Apache-2.0" } }]
    }
  ]
}
```

```bash
# Gradle 빌드 시 SBOM 자동 생성 + Dependency-Track 업로드
./gradlew cyclonedxBom
curl -X POST "https://dtrack.example.com/api/v1/bom" \
  -H "X-Api-Key: $DTRACK_TOKEN" \
  -F "project=$PROJECT_UUID" -F "bom=@build/reports/bom.json"
```

**관련 패턴**: Provenance Attestation, SLSA Framework, Secret Scanning

---

## 2. Sigstore / Cosign (Keyless Artifact Signing)

**목적**: 장기 보관용 개인 키 없이 OIDC identity 기반으로 컨테이너 이미지 / 바이너리 / SBOM 등 아티팩트에 서명하고, 공개 투명성 로그에 기록하여 누구나 출처를 검증할 수 있게 한다 (OpenSSF + Linux Foundation).

**특징**:
- **Fulcio**: 단기(10분) X.509 인증서 발급 CA, OIDC token(GitHub Actions / Google / SSO) 으로 신원 확인
- **Rekor**: append-only 투명성 로그 (Merkle tree, RFC 6962 Certificate Transparency 모델)
- **Cosign**: CLI — `cosign sign`, `cosign verify`, `cosign attest`
- 키 없는(keyless) 서명 = 키 유출 위험 제거, 서명 시점의 GitHub workflow run ID 까지 인증서에 박힘
- Sigstore policy controller (Kubernetes admission webhook) 로 미서명 이미지 배포 차단

**장점**:
- Long-lived 비밀 키 관리/회전 부담 없음
- 공개 감사 가능 — 누가 언제 무엇에 서명했는지 Rekor 에서 누구나 조회
- GitHub Actions OIDC 와 결합 시 build provenance 자동 입증

**단점**:
- Rekor public log 에 서명 메타데이터가 공개됨 (private 프로젝트는 self-hosted Rekor 필요)
- OIDC IdP 장애 시 서명 불가
- Air-gapped 환경에선 Fulcio/Rekor 자체 호스팅 필요

**활용 예시**:
- Kubernetes 컨테이너 이미지 admission control
- GitHub Release 바이너리 서명 (`cosign sign-blob`)
- SBOM/attestation 첨부 (`cosign attach sbom`)
- Distroless / Wolfi base image 검증

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**예제** (GitHub Actions keyless signing):
```yaml
# .github/workflows/release.yml
permissions:
  id-token: write    # OIDC token 발급 (Fulcio 가 받는다)
  contents: read
  packages: write

jobs:
  build-and-sign:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: sigstore/cosign-installer@v3
      - name: Build & push
        run: |
          IMAGE="ghcr.io/${{ github.repository }}:${{ github.sha }}"
          docker buildx build --push -t "$IMAGE" .
          DIGEST=$(docker buildx imagetools inspect "$IMAGE" --format '{{.Manifest.Digest}}')
          echo "IMAGE_REF=ghcr.io/${{ github.repository }}@${DIGEST}" >> $GITHUB_ENV
      - name: Keyless sign
        run: cosign sign --yes "$IMAGE_REF"     # OIDC → Fulcio → Rekor 자동
      - name: Attach SBOM
        run: |
          syft "$IMAGE_REF" -o cyclonedx-json > sbom.json
          cosign attest --yes --predicate sbom.json --type cyclonedx "$IMAGE_REF"
```

```bash
# 운영 측 검증 — 특정 GitHub workflow 에서 빌드된 것만 통과
cosign verify ghcr.io/acme/billing@sha256:abc... \
  --certificate-identity-regexp "^https://github.com/acme/billing/.github/workflows/release.yml@refs/tags/v.*$" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

**관련 패턴**: SLSA Framework, Provenance Attestation, SBOM

---

## 3. SLSA Framework (Supply-chain Levels for Software Artifacts)

**목적**: 빌드 파이프라인의 무결성/추적성/위변조 저항성을 4단계로 점진 향상시키는 표준 성숙도 모델. OpenSSF 가 Google 의 내부 Borg/SLSA 운영 경험을 공개한 것 (현재 v1.0).

**특징**:
- **Level 1 (Documented)**: 빌드 프로세스 문서화 + provenance 생성 (자동/수동 무관)
- **Level 2 (Hosted, Tampered-resistant)**: hosted 빌드 서비스(GitHub Actions, Tekton 등) 사용 + provenance 서명
- **Level 3 (Hardened, Non-falsifiable)**: 빌드 환경 격리, provenance 위조 방지 (key 격리, ephemeral runner)
- **Level 4 (deprecated v1.0 → 'Build L3 + Source/Deps tracks')**: 이전 정의는 hermetic + two-person review + reproducible
- Tracks: **Build** (현재 가장 성숙), **Source**, **Dependencies** (v1.1+ 작업 중)

**장점**:
- 산업 표준 — 성숙도 점수로 공급사 평가/요구 명확화
- 점진적 도입 가능 (L1 → L2 → L3)
- 가장 흔한 공격(빌드 시스템 침해)을 단계적으로 제거

**단점**:
- L3 도달엔 인프라 투자(ephemeral isolated runner, signing key 분리) 필요
- Build track 외엔 아직 표준화 미완 (Source/Deps 는 작업중)
- "Level N 달성" 자가 선언 → 외부 감사 부재 시 신뢰도 제한

**활용 예시**:
- GitHub Actions + `slsa-github-generator` → L3 provenance 자동 생성
- Tekton Chains → Kubernetes-native L2~L3 빌드
- npm provenance (npm 9.5+, GitHub Actions 연동) → 자동 L2
- 공공 부문/금융권 SBOM + SLSA L3 동반 요구 사례 증가

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**예제** (GitHub Actions SLSA L3 generator):
```yaml
# .github/workflows/slsa-release.yml
on:
  push:
    tags: ['v*']

permissions: read-all

jobs:
  build:
    outputs:
      digest: ${{ steps.hash.outputs.digest }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./gradlew :app:bootJar
      - id: hash
        run: |
          DIGEST=$(sha256sum build/libs/app.jar | awk '{print $1}')
          echo "digest=$DIGEST" >> $GITHUB_OUTPUT

  provenance:
    needs: [build]
    permissions:
      id-token: write
      contents: write
      actions: read
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.0.0
    with:
      base64-subjects: "${{ needs.build.outputs.digest }}"
      upload-assets: true   # GitHub Release 에 provenance.intoto.jsonl 첨부
```

```bash
# 운영 측 검증 (slsa-verifier)
slsa-verifier verify-artifact app.jar \
  --provenance-path app.jar.intoto.jsonl \
  --source-uri github.com/acme/billing \
  --source-tag v1.4.0
```

**관련 패턴**: Provenance Attestation, Sigstore/Cosign, Reproducible Build

---

## 4. Reproducible Build (Bit-for-Bit Reproducible Build)

**목적**: 동일한 소스 + 동일한 빌드 환경 → 동일한 바이너리(바이트 단위 동일) 를 누구나 독립적으로 재현하여, 빌드 서버 침해를 통한 백도어 삽입을 외부 검증으로 차단한다 (reproducible-builds.org).

**특징**:
- 비결정성 원인 제거: timestamp, build path, locale, file ordering, random seeds, parallel build race
- `SOURCE_DATE_EPOCH` 환경변수 (Reproducible Builds 표준) → embedded timestamp 고정
- 도구: **Bazel** (hermetic builds), **Nix/NixOS** (input-addressed store), **Guix**, **Buildah --timestamp**
- Debian, Tails OS, Arch Linux 가 패키지 reproducibility 비율을 공개 dashboard 로 추적 (95%+)
- 검증 방식: 두 독립 빌더가 동일 해시 산출 → diff 시 위조 의심

**장점**:
- "trusting trust" 공격 (Ken Thompson, 1984) 의 실용적 대응
- SLSA L4 의 핵심 요건
- 빌드 캐시 효율 — 입력 동일 시 캐시 hit 100%

**단점**:
- 빌드 시스템 전반의 비결정성 제거가 어려움 (Go 는 기본 제공, Java 는 jar 압축 timestamp 등 조정 필요)
- 외부 의존성 (Maven Central) 의 비결정성에 영향받음
- 초기 도입 비용 (toolchain pinning, hermetic env)

**활용 예시**:
- Bazel: `--stamp=no --workspace_status_command=` 로 timestamp 제거
- Go: `go build -trimpath -ldflags="-buildid="` 기본 reproducible
- Maven: `reproducible-build-maven-plugin` + `project.build.outputTimestamp`
- Debian dpkg: `SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)`

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**예제** (Go + Java reproducible build):
```bash
#!/usr/bin/env bash
# build-reproducible.sh
set -euo pipefail

export SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)
export TZ=UTC
export LC_ALL=C.UTF-8

# Go: -trimpath 가 빌드 경로 제거, -buildid= 가 unique id 제거
go build -trimpath -ldflags="-buildid= -X main.BuildTime=$SOURCE_DATE_EPOCH" \
  -o build/server ./cmd/server

# Java: Maven reproducible plugin
mvn -B clean package \
  -Dproject.build.outputTimestamp=$(date -u -r $SOURCE_DATE_EPOCH +%Y-%m-%dT%H:%M:%SZ)

# 두 번 빌드해서 해시 비교 (CI 에서 자동화)
sha256sum build/server > hash1.txt
go build -trimpath -ldflags="-buildid= -X main.BuildTime=$SOURCE_DATE_EPOCH" \
  -o build/server2 ./cmd/server
sha256sum build/server2 | awk '{print $1}' > hash2.txt
diff <(awk '{print $1}' hash1.txt) hash2.txt || { echo "NOT REPRODUCIBLE"; exit 1; }
```

**관련 패턴**: SLSA Framework, Provenance Attestation, Hermetic Build

---

## 5. Provenance Attestation (in-toto)

**목적**: 아티팩트의 출처(누가, 어떤 소스로, 어떤 빌더로, 어떤 파라미터로 만들었는지)를 암호학적으로 서명된 statement 로 첨부하여, 배포 시점의 trust decision 을 데이터 기반으로 만든다 (in-toto.io, CNCF graduated).

**특징**:
- **in-toto attestation framework**: `subject` (대상 아티팩트 해시) + `predicate` (메타데이터) + signature
- **Predicate types**: SLSA Provenance, SPDX SBOM, CycloneDX SBOM, Vulnerability, Test Result, Custom
- DSSE (Dead Simple Signing Envelope) 로 직렬화 후 Sigstore/Cosign 서명
- Builder identity (예: GitHub Actions workflow URL), source commit, build params, materials (input artifacts) 명시
- OPA / Kyverno / Sigstore Policy Controller 가 admission 단계에서 attestation 검증

**장점**:
- "어디서 왔는지" 와 "무엇으로 만들었는지" 가 분리 검증 가능
- 여러 predicate 를 하나의 아티팩트에 attach (provenance + SBOM + scan result)
- 정책 결정의 입력 데이터화 (PaC, Policy as Code)

**단점**:
- Attestation 저장소 관리 필요 (OCI registry 의 referrers API, Rekor 등)
- Predicate 표준화 진행중 — 벤더별 dialect 존재
- 검증 정책 작성/유지 비용

**활용 예시**:
- `cosign attest --predicate provenance.json --type slsaprovenance`
- Kyverno `verifyImages` rule 로 admission 차단
- ArgoCD image updater + attestation 검증
- npm 의 `provenance: true` (npm publish 시 자동 attest)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**예제** (SLSA provenance + Kyverno admission):
```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [{
    "name": "ghcr.io/acme/billing",
    "digest": { "sha256": "abc123..." }
  }],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": {
    "buildDefinition": {
      "buildType": "https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1",
      "externalParameters": {
        "workflow": {
          "ref": "refs/tags/v1.4.0",
          "repository": "https://github.com/acme/billing",
          "path": ".github/workflows/release.yml"
        }
      }
    },
    "runDetails": {
      "builder": { "id": "https://github.com/actions/runner/github-hosted" },
      "metadata": { "invocationId": "https://github.com/acme/billing/actions/runs/9876543210" }
    }
  }
}
```

```yaml
# Kyverno admission policy — signed + SLSA L3 provenance 필수
apiVersion: kyverno.io/v2beta1
kind: ClusterPolicy
metadata: { name: require-slsa-attestation }
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-provenance
      match: { any: [{ resources: { kinds: [Pod] } }] }
      verifyImages:
        - imageReferences: ["ghcr.io/acme/*"]
          attestations:
            - type: https://slsa.dev/provenance/v1
              conditions:
                - all:
                    - key: "{{ buildDefinition.externalParameters.workflow.repository }}"
                      operator: Equals
                      value: "https://github.com/acme/billing"
```

**관련 패턴**: SLSA Framework, Sigstore/Cosign, SBOM

---

## 6. Secret Scanning (Pre-commit + Repository Audit)

**목적**: 소스 코드 / 커밋 히스토리 / CI 로그 / 이슈에 실수로 포함된 API key, password, private key, token 등을 자동 탐지하여 누출 전(또는 직후) 차단/회수한다.

**특징**:
- **Pre-commit** 단계: `gitleaks protect`, `detect-secrets` hook 으로 commit 차단
- **Push protection**: GitHub Secret Scanning Push Protection (Pro/Enterprise), GitLab Push Rules
- **Historical scan**: 전체 git history 스캔 — `gitleaks detect`, `trufflehog filesystem --git`
- **Validation**: 발견된 string 을 실제 API 에 호출해 active 여부 확인 (trufflehog `--only-verified`)
- **Entropy heuristic** + **regex pattern** + **service-specific format** (AWS AKIA*, GitHub ghp_*, Slack xoxb-*)
- 발견 시 즉시 **rotation** (단순 삭제는 git history 에 남아 무의미)

**장점**:
- 사고 발생 후 평균 비용 ($150K+ per leak, IBM 2023 report) 대비 도입 비용 매우 낮음
- 자동화 — 개발자 교육에만 의존 안 함
- Compliance (SOC2, ISO 27001) 요건 충족

**단점**:
- False positive (test fixture, example key) 처리 운영 부담
- Encoded/obfuscated secret 탐지 어려움 (base64, env interpolation)
- 발견 ≠ 회수 — rotation 워크플로우가 별도 필요

**활용 예시**:
- gitleaks pre-commit hook
- GitHub Advanced Security (organization-wide)
- AWS GuardDuty + IAM access analyzer (key 유출 후 anomalous use 탐지)
- HashiCorp Vault dynamic credentials → 정적 secret 자체 제거

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**예제** (gitleaks + lefthook + CI):
```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    secrets:
      run: gitleaks protect --staged --redact --verbose
      fail_text: "Secret detected. Remove or add to .gitleaksignore (false positive)."
```

```toml
# .gitleaks.toml — 커스텀 규칙 + allowlist
[extend]
useDefault = true

[[rules]]
id = "internal-jira-token"
description = "Internal Jira PAT"
regex = '''ATATT3[A-Za-z0-9_-]{180,}'''
secretGroup = 0
entropy = 4.5

[allowlist]
description = "Test fixtures only"
paths = ['''testdata/.*''', '''(.*)?_test\.go''']
regexTarget = "match"
regexes = ['''sk-test-[A-Z0-9]{20}''']
```

```bash
# CI 에서 PR diff 만 스캔 (full scan 보완)
gitleaks detect --source . --log-opts="$(git merge-base origin/main HEAD)..HEAD" \
  --report-format sarif --report-path gitleaks.sarif --exit-code 1

# 발견 직후 회수 절차 (rotation 필수)
aws iam delete-access-key --access-key-id AKIA...    # 1) 즉시 비활성화
git filter-repo --invert-paths --path leaked.env     # 2) history 정리 (협업자 재clone 필요)
# 3) 새 key 발급 후 vault/secret manager 에 저장
```

**관련 패턴**: Pre-commit Hook, Vault Dynamic Secrets, AI-Assisted Code Secret Leak Defense

---

## 7. Slopsquatting / Hallucinated Package Defense

**목적**: LLM 코드 어시스턴트가 **존재하지 않는 패키지명을 환각**(hallucinate)하여 코드에 import 로 삽입하면, 공격자가 그 이름으로 악성 패키지를 선점 배포하는 **2024년부터 본격 등장한 새로운 공격 벡터**를 차단한다 ("slopsquatting" = typosquatting 의 AI slop 변종, Vulcan Cyber 명명).

**특징**:
- 학계 연구 (Lasso Security, 2024): GPT-4 가 Python 패키지 추천 시 약 **5%** 가 환각, 동일 prompt 반복 시 약 **43%** 가 재현 가능 (= 공격자가 예측 가능)
- 실제 사례: `huggingface-cli` → `huggingface_hub` (정상) / 환각 변종 `huggingfaceCli` 같은 가짜
- 환각 패턴: 비슷한 이름 조합(`requests-async`), 줄임 변형(`tf-keras`), 다른 언어 컨벤션 차용 (Python에 npm식 hyphen 작명)
- 방어층: **lockfile** (npm `package-lock.json`, pip `requirements.txt --hash`, Go `go.sum`), **allowlist registry mirror** (Artifactory, Nexus, AWS CodeArtifact), **package signing 검증** (npm provenance, PyPI Sigstore 2024+)
- 정책: AI 가 추천한 패키지는 **사람이 PyPI/npm 에서 직접 존재 확인 + 다운로드 수/maintainer 검증** 후 lockfile 추가

**장점**:
- 새 공격이지만 기존 supply chain 패턴(lockfile, allowlist, provenance) 조합으로 방어 가능
- AI 코드 어시스턴트 도입 가속 시기에 비용 대비 효과 큼
- 신규 패키지 추가만 통제 → 일상 개발 마찰 최소

**단점**:
- AI 어시스턴트 사용자에게 추가 검증 절차 요구 → 생산성 마찰
- Private/internal mirror 구축 비용
- 신규 정상 패키지 도입 시 allowlist 갱신 lag

**활용 예시**:
- Artifactory Remote Repository proxy + allowlist
- `pip install --require-hashes -r requirements.txt`
- npm `--ignore-scripts` 기본화 (postinstall 악성 코드 차단)
- IDE plugin: AI 추천 import 를 registry lookup 으로 사전 검증

**난이도**: 중간 | **사용 빈도**: ★★★★☆ (AI 코딩 도구 도입 조직에서 급상승)

**예제** (Python 환경 — lockfile + hash + mirror):
```bash
# 1) AI 가 추천한 패키지를 사람이 직접 검증
PKG="requests-async"
curl -sf "https://pypi.org/pypi/${PKG}/json" \
  | jq '{name: .info.name, downloads: .urls[0].downloads, maintainer: .info.author, created: .urls[0].upload_time}' \
  || { echo "DOES NOT EXIST — likely AI hallucination"; exit 1; }
# 다운로드 수가 비정상 낮거나(< 100/주), 최근 생성된 패키지면 의심

# 2) pip-tools 로 lockfile + hash 강제 (재현 가능 + 변조 차단)
pip-compile --generate-hashes --output-file=requirements.txt requirements.in
pip install --require-hashes -r requirements.txt   # hash 불일치 시 설치 실패

# 3) 내부 mirror 강제 (Artifactory / AWS CodeArtifact)
cat > pip.conf <<EOF
[global]
index-url = https://artifactory.acme.com/api/pypi/pypi-allowlist/simple/
# 외부 PyPI 직접 차단 — allowlist 등록된 패키지만 통과
EOF
```

```yaml
# CI guard — PR 에서 새 의존성 추가 시 보안팀 review 요청
# .github/workflows/dep-guard.yml
on: { pull_request: { paths: ['requirements.txt', 'package-lock.json', 'go.sum'] } }
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Diff new packages
        run: |
          git fetch origin main
          NEW_PKGS=$(git diff origin/main -- requirements.txt | grep '^+' | grep -v '^+++' || true)
          if [ -n "$NEW_PKGS" ]; then
            echo "::warning::New dependencies require security review (slopsquatting risk):"
            echo "$NEW_PKGS"
            # 자동으로 보안팀 reviewer 추가
            gh pr edit ${{ github.event.pull_request.number }} --add-reviewer @acme/security
          fi
```

**관련 패턴**: SBOM, Provenance Attestation, AI-Assisted Code Secret Leak Defense

---

## 8. AI-Assisted Code Secret Leak Defense

**목적**: GitHub Copilot / Cursor / Codeium / Codex 등 AI 코드 어시스턴트가 IDE 의 **prompt context** 로 secret(API key, DB password, customer PII) 을 외부 모델 서버에 전송하거나, 학습 데이터에 secret 이 포함되어 다른 사용자에게 **suggest** 로 흘러나오는 경로를 차단한다.

**특징**:
- 위협 모델 3가지:
  1. **Outbound leak**: IDE 가 열려있는 `.env`, `secrets.yaml` 을 prompt context 로 전송
  2. **Suggestion leak**: 과거 학습 데이터(공개 GitHub repo 의 leaked secret) 가 다른 사용자 IDE 에서 자동완성으로 출현 (GitHub Copilot 의 2021년 사례)
  3. **Telemetry leak**: 코드 본문이 학습 / 품질 개선 / debugging 명목으로 벤더 서버에 보관
- 방어층:
  - **`.copilotignore` / `.cursorignore` / `.aiexclude`**: 컨텍스트 송신 제외 패턴
  - **Vendor 설정**: GitHub Copilot Business/Enterprise `Code Referencing` 필터, `Telemetry: off`
  - **Secret redaction proxy**: IDE → 모델 사이에 redaction 게이트웨이 (예: Lasso, Portkey, 사내 LiteLLM proxy)
  - **Pre-commit secret scan** (패턴 6) 과 결합 — IDE 가 secret 을 자동 생성/suggest 해도 commit 차단
- **Post-incident rotation**: 의심 secret 은 즉시 회수 — AI 모델 캐시/학습에 들어갔다고 가정하고 대응

**장점**:
- 기존 secret scanning + ignore 파일 표준 조합으로 즉시 적용 가능
- Vendor SLA 의존 부분(telemetry off) 과 클라이언트측 통제(ignore) 를 이중화
- 조직 전체에 정책 일관 적용 가능 (org-level policy)

**단점**:
- AI 어시스턴트 효용 일부 감소 (context 가 좁아짐)
- Vendor 가 ignore 파일을 100% 존중한다는 보장은 SLA 에 의존
- Telemetry 정책은 vendor 변경에 취약

**활용 예시**:
- GitHub Copilot Business + `.copilotignore`
- Cursor `.cursorignore` + Privacy Mode (코드 미저장)
- AI 코드 어시스턴트 사용 시 secret 파일 제외 정책(예: .gitignore, 사내 exclude 정책) + project-level 환경변수 redaction
- 사내 LLM gateway 에서 정규식 기반 redaction (`OPENAI_API_KEY=...` → `REDACTED`)

**난이도**: 낮음~중간 | **사용 빈도**: ★★★★☆ (AI 도입 조직 필수)

**예제** (Copilot/Cursor ignore + redaction proxy):
```gitignore
# .copilotignore  (GitHub Copilot Business 가 context 송신 제외)
# .cursorignore   (Cursor 동일 의미)
**/.env
**/.env.*
**/secrets/**
**/*.pem
**/*.key
**/credentials.json
**/*_token*
**/*password*
configs/*-config.ini            # 본 프로젝트의 INI secret
configs/server-config*.ini
~/Library/Application Support/JiraAutoAnalyze/**
```

```yaml
# 조직 정책 — GitHub Copilot Business org settings (Terraform)
resource "github_organization_settings" "copilot" {
  copilot_business {
    public_code_suggestions = "blocked"   # 학습 데이터의 공개 코드 1:1 매칭 차단
    telemetry              = "off"         # 코드 본문 telemetry 차단
    chat_history_retention = "0"           # 채팅 즉시 폐기
  }
}
```

```python
# 사내 LLM gateway — 송신 전 redaction (Portkey/LiteLLM proxy 패턴)
import re

SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|secret|token|password)\s*=\s*["\']?([A-Za-z0-9/_+\-]{16,})["\']?'),
     r'\1=<REDACTED>'),
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), '<REDACTED_OPENAI_KEY>'),
    (re.compile(r'xox[baprs]-[A-Za-z0-9-]{10,}'), '<REDACTED_SLACK_TOKEN>'),
    (re.compile(r'AKIA[0-9A-Z]{16}'), '<REDACTED_AWS_KEY>'),
    (re.compile(r'ATATT3[A-Za-z0-9_-]{180,}'), '<REDACTED_JIRA_PAT>'),
]

def redact_prompt(text: str) -> str:
    """IDE → LLM 송신 전 호출. 매칭 발견 시 audit log 도 함께 남긴다."""
    for pattern, replacement in SECRET_PATTERNS:
        text, n = pattern.subn(replacement, text)
        if n > 0:
            audit_log.warning("secret_redacted", count=n, pattern=pattern.pattern[:30])
    return text
```

**Incident response checklist** (AI 컨텍스트에 secret 이 들어갔다고 판단 시):
1. 해당 secret 즉시 rotation (회수만으론 부족 — vendor 캐시 가정)
2. Vendor 에 데이터 삭제 요청 (GDPR Art. 17, GitHub Copilot Data Subject Request)
3. 영향받은 리소스의 audit log 조회 — anomalous access 탐지
4. `.copilotignore` / `.cursorignore` 보강하여 재발 차단
5. 사내 정책에 패턴 추가, 모든 개발자에게 공지

**관련 패턴**: Secret Scanning, Slopsquatting Defense, Zero Trust Architecture, Data Loss Prevention
