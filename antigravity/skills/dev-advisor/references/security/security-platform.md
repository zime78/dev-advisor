# 플랫폼/컨테이너 보안 패턴 (Platform & Container Security Patterns)

Kubernetes, 컨테이너 런타임, 클라우드 인프라 레이어를 대상으로 한 보안 패턴 모음. CIS Benchmark / NIST SP 800-190 / NSA Kubernetes Hardening Guide를 기반으로 한다. 애플리케이션 코드 외부의 실행 환경 자체를 강화하는 데 초점을 맞춘다.

---

## 1. Pod Security Standards (Kubernetes)

**목적**: Kubernetes Pod 실행 시 허용되는 보안 수준을 클러스터/네임스페이스 단위로 선언적으로 제어하여 과도한 권한의 컨테이너 실행을 차단합니다.

**특징**:
- PSP(Pod Security Policy) 폐기(v1.25) 후 내장 Admission Controller로 통합된 세 가지 표준 프로파일
  - `privileged`: 제한 없음 — 시스템 컴포넌트 전용
  - `baseline`: 알려진 권한 상승 벡터(hostNetwork, hostPID, privileged) 차단
  - `restricted`: Baseline + `runAsNonRoot`, seccomp RuntimeDefault, capabilities drop ALL 강제
- 네임스페이스 레이블로 적용 모드 지정: `enforce` / `audit` / `warn`
- 정책 위반 시 enforce 모드는 Pod 생성 거부, audit은 apiserver 감사 로그만 기록

**장점**:
- 추가 도구 없이 kube-apiserver 내장으로 동작 — 운영 오버헤드 최소
- `warn` → `audit` → `enforce` 단계적 마이그레이션으로 서비스 중단 없이 도입
- OPA Gatekeeper / Kyverno와 병행 사용 가능

**단점**:
- `restricted`는 기존 컨테이너 이미지 대부분이 root로 실행되어 즉시 적용 어려움
- 프로파일이 세 가지뿐 — 세밀한 커스텀 정책은 OPA나 Kyverno 필요
- 네임스페이스 레이블을 RBAC으로 보호하지 않으면 우회 가능

**활용 예시**:
- 프로덕션 네임스페이스 전체에 `restricted` 적용, 시스템 네임스페이스(kube-system)는 `privileged` 유지
- CI/CD 파이프라인에서 `warn` 모드로 정책 위반 조기 발견
- 멀티테넌트 클러스터에서 테넌트별 네임스페이스에 `baseline` 강제

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**YAML 예제**:
```yaml
# 네임스페이스 레이블로 PSA 적용 (Kubernetes v1.25+)
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # enforce: 위반 Pod 생성 거부
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    # audit: apiserver 감사 로그 기록
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
    # warn: kubectl 응답에 경고 메시지
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
---
# restricted 프로파일을 통과하는 Pod 예시
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault        # restricted 필수 항목
  containers:
    - name: app
      image: my-app:1.0
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]           # restricted 필수 항목
        readOnlyRootFilesystem: true
```

**관련 패턴**: OPA/Gatekeeper, Runtime Security (Falco), Hardening Baseline

---

## 2. Image Signing (Cosign + Notary)

**목적**: 컨테이너 이미지에 암호화 서명을 부착하여 공급망(supply chain) 무결성을 보장하고, 서명되지 않거나 신뢰되지 않은 이미지의 클러스터 배포를 Admission Controller 단계에서 차단합니다.

**특징**:
- **Cosign** (Sigstore 프로젝트): OCI 레지스트리에 서명을 별도 태그(`sha256-<digest>.sig`)로 저장, Keyless 서명(Fulcio CA + Rekor 투명성 로그) 지원
- **Notary v2 (notation)**: OCI Distribution Spec 1.1 referrers API 활용, 엔터프라이즈 PKI 통합에 적합
- Admission Controller 통합: **Connaisseur**, **Kyverno** ImagePolicy, **Sigstore policy-controller**
- SBOM(Software Bill of Materials) 첨부도 같은 서명 메커니즘으로 배포 가능
- 키 관리: KMS (AWS KMS / GCP KMS / HashiCorp Vault) 연동으로 개인키 노출 없이 서명

**장점**:
- SolarWinds류 공급망 공격 방어 — 레지스트리 compromise 후 이미지 위변조 탐지
- CI/CD 파이프라인 서명 → 클러스터 검증의 단방향 신뢰 체인 구축
- Keyless 서명은 OIDC 기반이라 장기 키 관리 부담 없음

**단점**:
- 레지스트리가 OCI 1.1 referrers를 지원해야 서명 저장 가능 (ECR: 지원, old DockerHub: 불완전)
- Admission Controller 장애 시 배포 파이프라인 전체 블로킹 — HA 구성 필수
- 기존 이미지에 소급 서명은 새 digest 생성 → 태그 재배포 필요

**활용 예시**:
- GitHub Actions에서 빌드 직후 `cosign sign --key aws-kms://...` 자동 서명
- ArgoCD 배포 전 Kyverno ImagePolicy로 서명 검증
- Harbor 레지스트리에 Notary v2 내장 서명 정책 적용

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**bash/YAML 예제**:
```bash
# CI에서 cosign으로 이미지 서명 (KMS 키 사용)
IMAGE="ghcr.io/myorg/myapp@sha256:abc123..."

cosign sign \
  --key "awskms:///arn:aws:kms:ap-northeast-2:123456789:key/my-signing-key" \
  "${IMAGE}"

# Keyless 서명 (GitHub Actions OIDC 환경)
cosign sign \
  --yes \
  --oidc-issuer "https://token.actions.githubusercontent.com" \
  "${IMAGE}"

# 서명 검증
cosign verify \
  --key "awskms:///arn:aws:kms:..." \
  "${IMAGE}"
```

```yaml
# Kyverno ClusterPolicy — 서명되지 않은 이미지 배포 거부
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-image-signature
      match:
        any:
          - resources:
              kinds: [Pod]
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/myorg/*"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: "https://rekor.sigstore.dev"
```

**관련 패턴**: IaC Scanning, OPA/Gatekeeper, Pod Security Standards

---

## 3. Network Policy (Kubernetes)

**목적**: Kubernetes 네임스페이스/파드 간 트래픽을 레이블 셀렉터 기반으로 화이트리스트 방식으로 제어하여, 취약한 서비스가 침해되더라도 횡적 이동(lateral movement)을 최소화합니다.

**특징**:
- L3/L4 (IP/Port) 제어 — L7 제어는 서비스 메시(Istio/Linkerd) 필요
- `podSelector`: 정책 적용 대상 Pod 선택 (빈 값이면 네임스페이스 전체)
- `namespaceSelector`: 트래픽을 허용할 네임스페이스 지정
- `policyTypes: [Ingress, Egress]`: 명시하지 않은 방향은 암묵 허용 — 반드시 양방향 명시
- Default Deny: 빈 `podSelector` + 빈 ingress/egress 규칙 → 네임스페이스 전체 트래픽 차단
- CNI 플러그인 의존 — Calico / Cilium / Weave만 Network Policy 실제 구현; Flannel 미지원

**장점**:
- 선언형 YAML로 트래픽 정책 코드화 → GitOps로 리뷰/버전 관리 가능
- 마이크로서비스별 최소 권한 네트워크 접근 — Zero Trust 기반
- 네임스페이스 격리로 멀티테넌트 환경 보호

**단점**:
- CNI 플러그인 교체 없이는 정책이 무시됨 (적용 여부 명시적 검증 필요)
- Egress DNS 허용 복잡 (CoreDNS UDP/TCP 53 별도 허용 필수)
- IPv6 dual-stack 환경에서 IPv4/IPv6 각각 정책 필요

**활용 예시**:
- 프론트엔드 Pod → 백엔드 Pod만 허용, DB Pod는 백엔드만 접근 허용
- `monitoring` 네임스페이스의 Prometheus만 각 네임스페이스 metrics 포트 수집 허용
- 외부 인터넷으로의 Egress를 허용 목적지 IP 블록으로 제한

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**YAML 예제**:
```yaml
# 1. Default Deny All (네임스페이스 전체 격리)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}          # 네임스페이스 내 모든 Pod
  policyTypes:
    - Ingress
    - Egress
---
# 2. 백엔드 → DB 허용 (레이블 셀렉터 기반)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-to-db
  namespace: production
spec:
  podSelector:
    matchLabels:
      role: database
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: backend
      ports:
        - protocol: TCP
          port: 5432
---
# 3. Egress DNS 허용 (CoreDNS 필수)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

**관련 패턴**: Pod Security Standards, Runtime Security (Falco), OPA/Gatekeeper

---

## 4. OPA / Gatekeeper (Open Policy Agent)

**목적**: Kubernetes Admission Webhook에 정책 엔진을 연결하여, 리소스 생성/수정 시 조직 정책을 코드(Rego 언어)로 표현하고 자동 강제합니다.

**특징**:
- **OPA**: 범용 정책 엔진 (Rego 언어), Kubernetes 외 Envoy / Terraform / CI 파이프라인에도 적용
- **Gatekeeper**: OPA의 Kubernetes 전용 operator — ValidatingWebhookConfiguration 자동 관리
- **ConstraintTemplate**: 정책 스키마 + Rego 로직 정의 (CRD로 등록)
- **Constraint**: ConstraintTemplate 인스턴스 — 어떤 리소스에 적용할지 + 파라미터 지정
- Audit 모드: 기존 리소스도 주기적으로 정책 위반 검사 → `status.violations` 보고
- Mutation Webhook: 리소스 생성 시 자동 수정 (Assign/AssignMetadata CRD)

**장점**:
- 정책을 코드로 관리 (Policy-as-Code) — GitOps, PR 리뷰, 테스트 가능
- PSA로 표현 불가능한 복잡한 규칙 (네이밍 컨벤션, 리소스 제한 강제 등) 구현 가능
- OPA Conftest로 Terraform/Helm 차트도 동일 정책으로 사전 검증

**단점**:
- Rego 언어 학습 곡선이 높음
- Webhook 레이턴시가 API 응답 시간에 직접 영향 — 타임아웃 튜닝 필요
- Gatekeeper 장애 시 `failurePolicy: Fail`이면 클러스터 운영 불가 → HA 필수

**활용 예시**:
- 모든 Deployment에 `resource.limits.cpu/memory` 강제
- 특정 레지스트리(ghcr.io/myorg) 외 이미지 배포 차단
- `latest` 태그 사용 금지 정책

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**YAML 예제**:
```yaml
# ConstraintTemplate: 허용된 레지스트리 외 이미지 차단
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: allowedregistries
spec:
  crd:
    spec:
      names:
        kind: AllowedRegistries
      validation:
        openAPIV3Schema:
          properties:
            registries:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package allowedregistries

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not any_allowed(container.image, input.parameters.registries)
          msg := sprintf("이미지 '%v'는 허용된 레지스트리가 아닙니다", [container.image])
        }

        any_allowed(image, registries) {
          registry := registries[_]
          startswith(image, registry)
        }
---
# Constraint: 실제 정책 인스턴스
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: AllowedRegistries
metadata:
  name: prod-allowed-registries
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production"]
  parameters:
    registries:
      - "ghcr.io/myorg/"
      - "123456789.dkr.ecr.ap-northeast-2.amazonaws.com/"
```

**관련 패턴**: Pod Security Standards, Image Signing, Network Policy

---

## 5. Runtime Security (Falco)

**목적**: 컨테이너 런타임 중 시스템 콜(syscall)을 실시간 모니터링하여 이상 행위(셸 실행, 민감 파일 접근, 네트워크 연결 변화)를 탐지하고 알림을 발송합니다.

**특징**:
- **커널 드라이버**: 전통적 커널 모듈(`falco-driver`) 또는 **eBPF 프로브** (커널 5.8+, 권장) — eBPF는 커널 빌드 불필요, 안전한 샌드박스 실행
- Rule 언어: YAML 기반, `condition` (필터 표현식) + `output` (알림 포맷) + `priority` 정의
- 기본 룰셋: 500+ 규칙 포함 (터미널 셸, /etc 수정, 컨테이너 탈출 시도 등)
- **falcosidekick**: 알림을 Slack / PagerDuty / Elasticsearch / SIEM으로 라우팅하는 사이드카
- Falco Talon: 자동 대응 엔진 (Pod 격리, 프로세스 종료 등)

**장점**:
- 코드 변경 없이 배포된 컨테이너에 즉시 적용 — 애플리케이션 투명
- 제로데이 공격 패턴도 syscall 수준에서 탐지 가능
- MITRE ATT&CK 매핑 지원 — 인시던트 분류 자동화

**단점**:
- 커널 버전/배포판에 따라 드라이버 호환성 문제 발생 가능
- 기본 룰셋 오탐(False Positive)율 높음 — 초기 튜닝 비용 상당
- eBPF probe는 권한 있는 init 컨테이너 또는 DaemonSet 필요

**활용 예시**:
- 프로덕션 Pod 내 `bash`/`sh` 실행 감지 → Slack 긴급 알림
- `/etc/shadow`, `/proc/*/mem` 접근 탐지
- 예상치 못한 outbound 연결(C2 통신 패턴) 감지

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**YAML 예제**:
```yaml
# Falco 커스텀 룰 — 프로덕션 컨테이너 내 셸 실행 탐지
- rule: Shell Spawned in Production Container
  desc: 프로덕션 컨테이너에서 대화형 셸이 실행됨 (공격자 침투 가능성)
  condition: >
    spawned_process
    and container
    and container.label.env = "production"
    and proc.name in (shell_binaries)
    and not proc.pname in (known_shell_parents)
  output: >
    프로덕션 컨테이너 셸 실행 탐지
    (user=%user.name container=%container.name
     image=%container.image.repository:%container.image.tag
     cmd=%proc.cmdline parent=%proc.pname)
  priority: CRITICAL
  tags: [mitre_execution, container]

- macro: shell_binaries
  condition: proc.name in (bash, sh, zsh, fish, dash)

- macro: known_shell_parents
  condition: proc.pname in (containerd-shim, runc)
---
# falcosidekick values (Helm) — Slack 알림 라우팅
customRules: {}
falcosidekick:
  enabled: true
  config:
    slack:
      webhookurl: "https://hooks.slack.com/services/..."
      minimumpriority: "warning"
      messageformat: |
        *[Falco Alert]* `{{ .Rule }}`
        Priority: *{{ .Priority }}*
        Container: `{{ index .OutputFields "container.name" }}`
```

**관련 패턴**: Runtime Security와 Network Policy 병행, OPA/Gatekeeper (예방), Pod Security Standards

---

## 6. IaC Scanning (Checkov / tfsec / Trivy)

**목적**: Terraform / CloudFormation / Kubernetes YAML / Dockerfile 등 Infrastructure as Code 파일을 CI 파이프라인에서 정적 분석하여, 배포 전 잘못된 보안 설정(misconfiguration)을 발견합니다.

**특징**:
- **Checkov**: Terraform, CloudFormation, ARM, Kubernetes, Helm, Dockerfile 지원, 700+ 내장 체크, CIS 벤치마크 매핑
- **tfsec**: Terraform 전용, 빠른 속도, Trivy에 흡수 통합됨 (tfsec → Trivy misconfig)
- **Trivy**: 이미지 취약점 + IaC misconfig + SBOM + 시크릿 스캔 통합 도구 (CNCF 졸업 프로젝트)
- SARIF 출력으로 GitHub Security tab / Defect Dojo 연동
- PR 단위 인라인 코멘트 지원 (GitHub Actions, GitLab CI)
- 커스텀 정책: OPA Rego (Checkov) 또는 `--config` YAML (tfsec)

**장점**:
- 배포 전 차단 — 잘못된 S3 퍼블릭 ACL, 암호화 비활성, 과도한 IAM 권한을 배포 전 발견
- 코드 리뷰와 통합되어 개발자 즉시 피드백
- 무료 오픈소스, 로컬 실행 가능 — 외부 서비스 의존 없음

**단점**:
- 오탐(False Positive)이 많아 `.checkov.yaml` 억제 파일 관리 비용 발생
- 동적 Terraform 값(변수, 데이터 소스 참조)은 정적 분석 한계
- Helm 차트는 render 후 스캔 필요 (`helm template` 선행)

**활용 예시**:
- PR 머지 전 Checkov 실패 시 CI 블로킹
- Trivy로 ECR 이미지 daily 스캔 후 CVE 리포트 Slack 발송
- Terraform plan JSON을 checkov로 검사하여 drift 탐지

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**GitHub Actions YAML 예제**:
```yaml
name: IaC Security Scan

on:
  pull_request:
    paths:
      - "terraform/**"
      - "k8s/**"
      - "Dockerfile"

jobs:
  checkov:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Checkov — Terraform 보안 검사
        uses: bridgecrewio/checkov-action@master
        with:
          directory: terraform/
          framework: terraform
          output_format: sarif
          output_file_path: results/checkov.sarif
          soft_fail: false          # 취약점 발견 시 CI 실패
          skip_check: CKV_AWS_144  # 억제 예시 (S3 cross-region replication)
        env:
          PRISMA_API_URL: ""        # 오프라인 모드

      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results/checkov.sarif

  trivy-iac:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Trivy — K8s manifest 스캔
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: config
          scan-ref: k8s/
          format: sarif
          output: trivy-iac.sarif
          severity: CRITICAL,HIGH
          exit-code: 1
```

**관련 패턴**: Image Signing, Hardening Baseline, SAST (security-sdlc.md)

---

## 7. Hardening Baseline (CIS Benchmark / STIG)

**목적**: CIS(Center for Internet Security) Benchmark와 STIG(Security Technical Implementation Guide)이 정의한 OS/Kubernetes/클라우드 설정 기준선(baseline)을 자동화 도구로 측정하고 지속적으로 준수 상태를 유지합니다.

**특징**:
- **CIS Benchmark**: 레벨 1(필수 최소 보안) / 레벨 2(심층 방어, 성능 trade-off 감수) 구분
  - CIS Kubernetes Benchmark v1.9: API 서버 플래그, etcd 암호화, kubelet 설정 등 250+ 체크
  - CIS Amazon EKS Benchmark: EKS 전용 managed node/control plane 항목 포함
- **kube-bench**: CIS Kubernetes Benchmark 자동 검사 CLI/Job, 결과 JSON/JUnit 출력
- **OpenSCAP / scap-security-guide**: RHEL/CentOS STIG 자동화 (Ansible remediation 생성 가능)
- **Lynis**: 범용 Linux 보안 감사 도구 (CI 통합 가능)
- Compliance as Code: InSpec / Chef Compliance profiles

**장점**:
- 업계 표준 기준 — 규제 감사(SOC 2, PCI-DSS, HIPAA) 증적 자료로 직접 활용
- 자동화 도구로 수천 대 서버에 일관된 기준 적용 가능
- 수정 방법이 Benchmark 문서에 명시되어 있어 remediation 명확

**단점**:
- Level 2 적용 시 서비스 성능 저하 / 일부 기능 비활성화 trade-off 검토 필수
- STIG는 미 국방부 기준으로 과도하게 보수적 — 상업 서비스 전면 적용 어려움
- Benchmark 버전과 실제 클러스터 버전 불일치 시 체크 항목 오류 발생

**활용 예시**:
- kube-bench를 Kubernetes Job으로 주기 실행, 실패 항목 Slack 보고
- OpenSCAP으로 EC2 AMI 빌드 파이프라인에 STIG 검증 통합
- Terraform AWS CIS module로 신규 계정 생성 시 기준선 자동 적용

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**bash / YAML 예제**:
```bash
# kube-bench — CIS Kubernetes Benchmark 실행 (마스터 노드)
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job-master.yaml
kubectl logs job/kube-bench-master | grep -E "^\[FAIL\]" | head -20

# 결과 예시 출력
# [FAIL] 1.1.1 Ensure that the API server pod specification file permissions are set to 600 (Automated)
# [FAIL] 1.2.6 Ensure that the --kubelet-certificate-authority argument is set (Automated)

# OpenSCAP — RHEL9 CIS Level 1 점수 측정
oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --results /tmp/scan-results.xml \
  --report /tmp/scan-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Ansible remediation playbook 생성 (OpenSCAP)
oscap xccdf generate fix \
  --fix-type ansible \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --output remediate-cis.yml \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

```yaml
# GitHub Actions — kube-bench 주기 실행 워크플로우
name: CIS Kubernetes Benchmark

on:
  schedule:
    - cron: "0 2 * * 1"    # 매주 월요일 02:00 UTC

jobs:
  kube-bench:
    runs-on: self-hosted    # 클러스터 접근 가능한 runner
    steps:
      - name: kube-bench 실행
        run: |
          kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
          kubectl wait --for=condition=complete job/kube-bench --timeout=120s
          FAILURES=$(kubectl logs job/kube-bench | grep -c "^\[FAIL\]" || true)
          echo "CIS 벤치마크 실패 항목: ${FAILURES}개"
          kubectl logs job/kube-bench > kube-bench-report.txt

      - name: 결과를 Slack으로 발송
        if: always()
        run: |
          curl -X POST "${{ secrets.SLACK_WEBHOOK }}" \
            -H 'Content-type: application/json' \
            --data "{\"text\": \"kube-bench 스캔 완료 — 실패 항목 확인 필요\"}"
```

**관련 패턴**: IaC Scanning, Pod Security Standards, Runtime Security (Falco)
