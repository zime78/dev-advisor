# 보안 레퍼런스 (Security Reference)

dev-catalog의 4번째 도메인. 보안 메타 원리 + 12 sub-카테고리 + 규제 컴플라이언스. patterns/algorithms/languages 와 동급의 독립 도메인이다.

## 보안 카테고리 (15 파일, 106 항목)

| 카테고리 | 파일 | 항목 수 | 대표 |
|---------|------|--------:|------|
| [보안 메타 원리](security.md) | security.md | 4 | Defense in Depth, Zero Trust, Least Privilege, Secure by Default |
| [인증/Identity Governance](security-authn.md) | security-authn.md | 13 | OAuth2+PKCE, OIDC, SAML, FIDO2/Passkeys, MFA, Device Flow, Magic Link, Social Login, Refresh Rotation+Reuse Detection, ATO 방어, SCIM, JIT, PAM |
| [인가](security-authz.md) | security-authz.md | 7 | RBAC, ABAC, ReBAC(Zanzibar), Policy as Code(OPA/Cedar), Permission Boundary, Least Privilege(구현), JWT Claims Authz |
| [암호 운영](security-crypto-ops.md) | security-crypto-ops.md | 11 | KMS, HSM, Envelope, Key Rotation, PFS, PQC, Crypto Agility, OPAQUE, mTLS, Key Ceremony, HSM Runbook |
| [데이터 보호](security-data-protection.md) | security-data-protection.md | 8 | Encryption at Rest, Field-level Encryption, Tokenization, FPE, Data Masking, Pseudonymization, Differential Privacy, Confidential Computing(TEE) |
| [API/Web 보안](security-api-web.md) | security-api-web.md | 12 | per-Identity Rate Limit, HMAC Signing, IDOR/BOLA, SSRF, XXE, CSRF, Open Redirect, Mass Assignment, Race/TOCTOU, GraphQL, CSP/SRI/HSTS, CORS |
| [공급망 보안](security-supply-chain.md) | security-supply-chain.md | 8 | SBOM, Sigstore/Cosign, SLSA, Reproducible Build, Provenance, Secret Scanning, Slopsquatting 방어, AI 코드 Secret Leak 방어 |
| [플랫폼/컨테이너 보안](security-platform.md) | security-platform.md | 7 | Pod Security Standards, Image Signing, Network Policy, OPA/Gatekeeper, Falco, IaC Scan, CIS Benchmark |
| [DevSecOps SDLC](security-sdlc.md) | security-sdlc.md | 6 | Threat Modeling(STRIDE/DREAD), SAST, DAST, IAST, SCA, Pre-commit Secret Scan |
| [탐지/사고 대응](security-detect-respond.md) | security-detect-respond.md | 6 | SIEM, SOAR, Audit Log(tamper-evident), UEBA, MITRE ATT&CK Mapping, IR Playbook |
| [모바일 앱 보안](security-mobile.md) | security-mobile.md | 5 | Certificate Pinning, App Attest/Play Integrity, Jailbreak/Root Detection, RASP, Secure Storage |
| [AI 모델 보안](security-ai-model.md) | security-ai-model.md | 5 | Model Extraction/Theft, Membership Inference, Data Poisoning, Adversarial Inputs, Federated Learning 보안 |
| [Privacy Engineering](privacy-engineering.md) | privacy-engineering.md | 9 | Consent Ledger, Privacy by Design, DSAR, Retention Policy, Purpose Binding, DPIA, Privacy Notice, Data Minimization, Privacy Operations |
| [규제 컴플라이언스](compliance.md) | compliance.md | 5 | GDPR, CCPA/CPRA, PCI DSS v4.0, HIPAA, SOC 2 |

**총 15 파일, 106 항목.**

### Privacy Engineering (privacy-engineering.md) — 9

| ID | 영문명 | 한글명 |
|----|--------|--------|
| consent-ledger | Consent Ledger | 동의 원장 |
| privacy-by-design | Privacy by Design | 설계 단계 프라이버시 |
| dsar | Data Subject Access Request | 정보주체 권리 요청 |
| retention-policy | Retention Policy | 보유 정책 |
| purpose-binding | Purpose Binding / Limitation | 목적 구속 |
| dpia | Data Protection Impact Assessment | 영향 평가 |
| privacy-notice | Privacy Notice | 처리방침 |
| data-minimization | Data Minimization | 최소화 원칙 |
| privacy-operations | Privacy Operations (PrivOps) | 운영 자동화 |

---

## Cross-link 규약

보안 항목은 dev-catalog 내 다른 도메인과 자주 연결된다. ownership 규칙:

| 영역 | Ownership | 보안 처리 |
|---|---|---|
| `algorithms/crypto.md` (SHA-256, HMAC, RSA, AES, Bcrypt, Argon2) | algorithms | primitive 유지. `security-crypto-ops.md`는 **운영 패턴**(KMS/rotation/agility)만 다룬다 |
| `patterns/observability.md` (Audit Trail) | patterns/observability | `security-detect-respond.md`는 cross-link, **tamper-evident/signing 관점**만 stub |
| `patterns/ai-llm.md` (Guardrails — Prompt Injection 방어) | patterns/ai-llm | `security-ai-model.md`는 모델 자체 공격 분류학(Extraction/Inference/Poisoning) 다룸 |
| `patterns/reliability.md` (Rate Limiter — capacity) | patterns/reliability | `security-api-web.md`의 rate limit은 **abuse 방어(per-identity, account lockout, IP reputation)** |

규칙: **primitive → algorithms / 운영 → security / 탐지 → observability** 삼각 cross-link.

## 보안 ID → 파일 매핑 (106개)

`/security <id>` 호출 시 SKILL.md → 본 표 → 보안 파일 `## N. <항목>` 헤더 순으로 lookup.

### 보안 메타 원리 (security.md) — 4
| ID | 영문명 | 한글명 |
|----|--------|--------|
| defense-in-depth | Defense in Depth | 다층 방어 |
| zero-trust | Zero Trust | 제로 트러스트 |
| least-privilege | Least Privilege | 최소 권한 |
| secure-by-default | Secure by Default | 기본값 보안 |

### 인증 (security-authn.md) — 13
| ID | 영문명 | 한글명 |
|----|--------|--------|
| oauth2-pkce | OAuth2 + PKCE | OAuth2 + PKCE |
| oidc | OIDC | OIDC |
| saml | SAML 2.0 | SAML |
| fido2-webauthn | FIDO2 / WebAuthn | 패스키 |
| mfa | MFA | 다중 인증 |
| oauth-device-flow | OAuth Device Flow | 디바이스 흐름 |
| magic-link | Magic Link | 매직 링크 |
| social-login | Social Login | 소셜 로그인 |
| refresh-rotation | Refresh Token Rotation | 토큰 로테이션 |
| ato-defense | Account Takeover Defense | 계정 탈취 방어 |
| scim | SCIM 2.0 | SCIM 프로비저닝 |
| jit-access | Just-In-Time Access | JIT 임시 권한 |
| pam | PAM | 특권 접근 관리 |

### 인가 (security-authz.md) — 7
| ID | 영문명 | 한글명 |
|----|--------|--------|
| rbac | RBAC | 역할 기반 |
| abac | ABAC | 속성 기반 |
| rebac | ReBAC (Zanzibar) | 관계 기반 |
| policy-as-code | Policy as Code | 정책 코드화 |
| permission-boundary | Permission Boundary | 권한 경계 |
| authz-least-privilege | Least Privilege (구현) | 최소 권한 구현 |
| jwt-claims-authz | JWT Claims Authorization | JWT 인가 |

### 암호 운영 (security-crypto-ops.md) — 11
| ID | 영문명 | 한글명 |
|----|--------|--------|
| kms | KMS | 키 관리 서비스 |
| hsm | HSM | 하드웨어 보안 모듈 |
| envelope-encryption | Envelope Encryption | 봉투 암호화 |
| key-rotation | Key Rotation | 키 로테이션 |
| pfs | Perfect Forward Secrecy | 완전 순방향 비밀성 |
| pqc | Post-Quantum Cryptography | 양자 내성 암호 |
| crypto-agility | Crypto Agility | 알고리즘 민첩성 |
| opaque | OPAQUE / aPAKE | OPAQUE 비번 인증 |
| mtls | mTLS | 상호 TLS |
| key-ceremony | Key Ceremony | 키 의식 |
| hsm-runbook | HSM Runbook | HSM 운영 절차 |

### 데이터 보호 (security-data-protection.md) — 8
| ID | 영문명 | 한글명 |
|----|--------|--------|
| encryption-at-rest | Encryption at Rest | 저장 데이터 암호화 |
| field-level-encryption | Field-level Encryption | 필드 수준 암호화 |
| tokenization | Tokenization | 토큰화 |
| fpe | Format-Preserving Encryption | 형식 보존 암호화 |
| data-masking | Data Masking | 데이터 마스킹 |
| pseudonymization | Pseudonymization | 가명화 |
| differential-privacy | Differential Privacy | 차등 프라이버시 |
| confidential-computing | Confidential Computing | 기밀 컴퓨팅 |

### API/Web 보안 (security-api-web.md) — 12
| ID | 영문명 | 한글명 |
|----|--------|--------|
| per-identity-rate-limit | per-Identity Rate Limiting | 신원별 레이트 제한 |
| hmac-request-signing | HMAC Request Signing | HMAC 요청 서명 |
| idor-bola | IDOR / BOLA | 객체 권한 우회 방어 |
| ssrf | SSRF Defense | SSRF 방어 |
| xxe | XXE Defense | XXE 방어 |
| csrf | CSRF | CSRF 방어 |
| open-redirect | Open Redirect | 오픈 리다이렉트 방어 |
| mass-assignment | Mass Assignment | 매스 어사인먼트 |
| race-toctou | Race / TOCTOU | 경합 조건 |
| graphql-security | GraphQL Security | GraphQL 보안 |
| csp-sri-hsts | CSP / SRI / HSTS | Web 콘텐츠 보안 헤더 |
| cors-cookie | CORS / SameSite | cross-origin 정책 |

### 공급망 보안 (security-supply-chain.md) — 8
| ID | 영문명 | 한글명 |
|----|--------|--------|
| sbom | SBOM | 소프트웨어 자재명세서 |
| sigstore-cosign | Sigstore / Cosign | 키없는 서명 |
| slsa | SLSA Framework | SLSA 단계 |
| reproducible-build | Reproducible Build | 재현 가능한 빌드 |
| provenance-attestation | Provenance Attestation | 출처 증명 |
| secret-scanning | Secret Scanning | 시크릿 스캔 |
| slopsquatting | Slopsquatting Defense | 환각 패키지 방어 |
| ai-secret-leak-defense | AI Code Secret Leak Defense | AI 코드 시크릿 방어 |

### 플랫폼/컨테이너 (security-platform.md) — 7
| ID | 영문명 | 한글명 |
|----|--------|--------|
| pod-security-standards | Pod Security Standards | Pod 보안 표준 |
| image-signing | Image Signing | 이미지 서명 |
| network-policy | Network Policy | 네트워크 정책 |
| opa-gatekeeper | OPA / Gatekeeper | 정책 게이트키퍼 |
| runtime-falco | Runtime Security (Falco) | 런타임 보안 |
| iac-scanning | IaC Scanning | IaC 스캐닝 |
| hardening-baseline | Hardening Baseline (CIS) | 하드닝 |

### DevSecOps SDLC (security-sdlc.md) — 6
| ID | 영문명 | 한글명 |
|----|--------|--------|
| threat-modeling | Threat Modeling | 위협 모델링 |
| sast | SAST | 정적 분석 |
| dast | DAST | 동적 분석 |
| iast | IAST | 인터랙티브 분석 |
| sca | SCA | 의존성 분석 |
| pre-commit-secret-scan | Pre-commit Secret Scan | 커밋 전 시크릿 스캔 |

### 탐지/사고 대응 (security-detect-respond.md) — 6
| ID | 영문명 | 한글명 |
|----|--------|--------|
| siem | SIEM | 보안 정보 이벤트 관리 |
| soar | SOAR | 보안 오케스트레이션 |
| audit-log-tamper-evident | Audit Log (Tamper-Evident) | 변조 방지 감사 로그 |
| ueba | UEBA | 사용자 행동 분석 |
| mitre-attack-mapping | MITRE ATT&CK Mapping | MITRE 매핑 |
| ir-playbook | IR Playbook | 사고 대응 플레이북 |

### 모바일 앱 보안 (security-mobile.md) — 5
| ID | 영문명 | 한글명 |
|----|--------|--------|
| certificate-pinning | Certificate Pinning | 인증서 고정 |
| app-attest | App Attest / Play Integrity | 어테스테이션 |
| jailbreak-root-detection | Jailbreak / Root Detection | 탈옥/루팅 탐지 |
| rasp | RASP | 런타임 자가 보호 |
| mobile-secure-storage | Secure Storage | 보안 저장소 |

### AI 모델 보안 (security-ai-model.md) — 5
| ID | 영문명 | 한글명 |
|----|--------|--------|
| model-extraction | Model Extraction | 모델 추출/탈취 |
| membership-inference | Membership Inference | 멤버십 추론 |
| data-poisoning | Data Poisoning | 데이터 오염 |
| adversarial-inputs | Adversarial Inputs | 적대적 입력 |
| federated-learning-security | Federated Learning Security | 연합 학습 보안 |

### Privacy Engineering (privacy-engineering.md) — 9
| ID | 영문명 | 한글명 |
|----|--------|--------|
| consent-ledger | Consent Ledger | 동의 원장 |
| privacy-by-design | Privacy by Design | 설계 단계 프라이버시 |
| dsar | Data Subject Access Request | 정보주체 권리 요청 |
| retention-policy | Retention Policy | 보유 정책 |
| purpose-binding | Purpose Binding / Limitation | 목적 구속 |
| dpia | Data Protection Impact Assessment | 영향 평가 |
| privacy-notice | Privacy Notice | 처리방침 |
| data-minimization | Data Minimization | 최소화 원칙 |
| privacy-operations | Privacy Operations (PrivOps) | 운영 자동화 |

### 규제 컴플라이언스 (compliance.md) — 5
| ID | 영문명 | 한글명 |
|----|--------|--------|
| gdpr | GDPR | EU 개인정보 |
| ccpa-cpra | CCPA / CPRA | 캘리포니아 |
| pci-dss | PCI DSS v4.0 | 카드 결제 |
| hipaa | HIPAA | 미국 의료정보 |
| soc-2 | SOC 2 | 서비스 조직 통제 |

---

## 표준 인용 매트릭스

- 인증/인가: NIST SP 800-63, RFC 6749/7519/7636/8628/8693/9068, W3C WebAuthn, SCIM RFC 7644
- 암호 운영: NIST SP 800-57/130, FIPS 140-3, FIPS 203/204/205 (PQC)
- 데이터 보호: NIST SP 800-38G (FPE), GDPR Art 25/32, NIST Privacy Framework
- API/Web: OWASP Top 10, OWASP API Top 10, RFC 6750
- 공급망: SLSA Framework, NIST SP 800-218 (SSDF), Executive Order 14028
- 플랫폼: CIS Benchmarks, NIST SP 800-53, K8s Pod Security Standards
- SDLC: OWASP SAMM, BSIMM, NIST SP 800-218
- 탐지/IR: NIST SP 800-61 Rev.2, MITRE ATT&CK, Sigma format
- 모바일: OWASP MASVS
- AI/LLM: OWASP LLM Top 10 2025, MITRE ATLAS, NIST AI RMF
- 프라이버시: NIST Privacy Framework, GDPR, CCPA/CPRA, ISO/IEC 27701

## Semantic validation 후보

카탈로그 변경 시 단순 링크 검증 외에 다음 의미 검증을 추가 후보로 둔다.

| 검증 후보 | 기준 |
|---|---|
| OWASP Web/API/Mobile/LLM 매핑 | `standards-mapping.md`의 Top 10 항목이 `security/index.md` 실제 ID와 연결되어야 함 |
| AI/LLM 보안 매핑 | Prompt Injection, Excessive Agency, Vector/Embedding Weakness, System Prompt Leakage가 `security-ai-model.md` 또는 `patterns/ai-llm.md` 중 하나 이상에 연결되어야 함 |
| Privacy/Compliance 매핑 | DSAR, retention, DPIA, data minimization이 privacy 항목과 compliance 항목 양쪽에서 참조 가능해야 함 |
| Risk scoring | STRIDE/DREAD만 단독 사용하지 않고 CVSS v4, EPSS, KEV, OWASP Risk Rating, 데이터 민감도, blast radius, exploitability, risk acceptance 기준 중 필요한 축을 병행해야 함 |
- AI 모델: MITRE ATLAS, OWASP LLM Top 10
- 규제: GDPR, CCPA/CPRA, PCI DSS v4.0, HIPAA, SOC 2 TSP 100

---

## OWASP Top 10 시리즈 ID 매핑

dev-advisor 보안 카탈로그(106 항목)는 OWASP 4 시리즈를 1차 참조 표준으로 채택한다. 본 섹션은 각 OWASP ID 가 어느 dev-advisor sub-파일의 어느 anchor 에 매핑되는지 명시한다. **매핑 표기**: ● 정확 매핑 / ◐ 부분 매핑(보완 자료 필요) / ✗ 미매핑(추후 추가 예정 또는 별도 카탈로그).

### OWASP Web Top 10 (2021)

웹 애플리케이션의 가장 빈번한 보안 위험 10 종. dev-advisor `security-api-web.md` / `security-authz.md` / `security-crypto-ops.md` / `security-supply-chain.md` / `security-sdlc.md` / `security-detect-respond.md` 에 분산 매핑.

| OWASP ID | 이름 | 매핑 | dev-advisor anchor | 추가 참조 |
|---|---|:--:|---|---|
| A01:2021 | Broken Access Control | ● | `security-authz.md#1-rbac-role-based-access-control`, `#2-abac-attribute-based-access-control`, `#3-rebac-relationship-based-access-control`, `#5-permission-boundary`, `security-api-web.md#3-idor--bola-방어-broken-object-level-authorization` | `security-authn.md#12-just-in-time-jit-access` (JIT 임시 권한) |
| A02:2021 | Cryptographic Failures | ● | `security-crypto-ops.md#1-kms-key-management-service`, `#3-envelope-encryption-dek--kek-2단-구조`, `#5-perfect-forward-secrecy-pfs`, `#7-crypto-agility`, `security-data-protection.md#1-encryption-at-rest-저장-데이터-암호화`, `#2-field-level-encryption-필드-단위-암호화` | `compliance.md` (GDPR Art 32) |
| A03:2021 | Injection | ◐ | `security-api-web.md#5-xxe-방어-xml-external-entity`, `#10-graphql-보안` (SQLi/XSS 일반론은 `patterns/` 도메인 ownership) | `security-sdlc.md#2-sast-static-application-security-testing` |
| A04:2021 | Insecure Design | ● | `security-sdlc.md#1-threat-modeling-stride--dread--pasta`, `security.md` (Defense in Depth / Secure by Default) | `privacy-engineering.md#2-privacy-by-design-pbd` |
| A05:2021 | Security Misconfiguration | ● | `security-platform.md#7-hardening-baseline-cis`, `security-api-web.md#11-csp--sri--hsts--trusted-types-web-보안-헤더`, `#12-cors--cookie-정책-samesite--referrer-policy--permissions-policy` | `security-platform.md#6-iac-scanning` |
| A06:2021 | Vulnerable and Outdated Components | ● | `security-supply-chain.md#1-sbom-software-bill-of-materials`, `security-sdlc.md#5-sca-software-composition-analysis` | `security-supply-chain.md#7-slopsquatting--hallucinated-package-defense` |
| A07:2021 | Identification and Authentication Failures | ● | `security-authn.md#1-oauth2-authorization-code--pkce-rfc-7636`, `#4-fido2--webauthn--passkeys`, `#5-mfa-multi-factor-authentication-totp--push--webauthn-2nd-factor`, `#9-session--refresh-token-rotation--reuse-detection`, `#10-account-takeover-ato-defense` | `security-crypto-ops.md#8-opaque--apake-augmented-password-authenticated-key-exchange` |
| A08:2021 | Software and Data Integrity Failures | ● | `security-supply-chain.md#2-sigstore--cosign-keyless-artifact-signing`, `#3-slsa-framework-supply-chain-levels-for-software-artifacts`, `#5-provenance-attestation-in-toto`, `security-detect-respond.md#3-audit-log-pattern--tamper-evident-보안-관점-감사-로그` | `security-supply-chain.md#4-reproducible-build-bit-for-bit-reproducible-build` |
| A09:2021 | Security Logging and Monitoring Failures | ● | `security-detect-respond.md#1-siem-security-information--event-management`, `#3-audit-log-pattern--tamper-evident-보안-관점-감사-로그`, `#4-ueba-user--entity-behavior-analytics`, `#6-incident-response-playbook-nist-sp-800-61-rev2` | `patterns/observability.md` (Audit Trail 일반론) |
| A10:2021 | Server-Side Request Forgery (SSRF) | ● | `security-api-web.md#4-ssrf-방어-server-side-request-forgery` | `security-platform.md#3-network-policy` (egress 제한) |

**Web 커버리지**: 10/10 (A03 Injection 만 ◐ — SQLi/XSS primitive 는 `patterns/` 영역에 속함)

### OWASP API Top 10 (2023)

API 전용 위험. 다수가 `security-api-web.md` + `security-authz.md` + `security-authn.md` 에 매핑.

| OWASP ID | 이름 | 매핑 | dev-advisor anchor | 추가 참조 |
|---|---|:--:|---|---|
| API1:2023 | Broken Object Level Authorization (BOLA) | ● | `security-api-web.md#3-idor--bola-방어-broken-object-level-authorization` | `security-authz.md#3-rebac-relationship-based-access-control` |
| API2:2023 | Broken Authentication | ● | `security-authn.md#1-oauth2-authorization-code--pkce-rfc-7636`, `#9-session--refresh-token-rotation--reuse-detection`, `#10-account-takeover-ato-defense` | `security-authn.md#5-mfa-multi-factor-authentication-totp--push--webauthn-2nd-factor` |
| API3:2023 | Broken Object Property Level Authorization | ● | `security-api-web.md#8-mass-assignment-방어` | `security-authz.md#7-jwt-claims-based-authorization` |
| API4:2023 | Unrestricted Resource Consumption | ● | `security-api-web.md#1-per-identity-rate-limiting-신원별-레이트-리미팅` | `patterns/reliability.md` (Rate Limiter capacity) |
| API5:2023 | Broken Function Level Authorization | ● | `security-authz.md#1-rbac-role-based-access-control`, `#4-policy-as-code-opa-rego--aws-cedar`, `#5-permission-boundary` | `security-authz.md#6-least-privilege-구현-패턴-just-enough-access--time-bound` |
| API6:2023 | Unrestricted Access to Sensitive Business Flows | ◐ | `security-api-web.md#1-per-identity-rate-limiting-신원별-레이트-리미팅` (abuse 방어), `security-detect-respond.md#4-ueba-user--entity-behavior-analytics` | `security-authn.md#10-account-takeover-ato-defense` |
| API7:2023 | Server-Side Request Forgery | ● | `security-api-web.md#4-ssrf-방어-server-side-request-forgery` | `security-platform.md#3-network-policy` |
| API8:2023 | Security Misconfiguration | ● | `security-api-web.md#11-csp--sri--hsts--trusted-types-web-보안-헤더`, `#12-cors--cookie-정책-samesite--referrer-policy--permissions-policy`, `security-platform.md#7-hardening-baseline-cis` | `security-platform.md#6-iac-scanning` |
| API9:2023 | Improper Inventory Management | ◐ | `security-supply-chain.md#1-sbom-software-bill-of-materials` (API 인벤토리 ≠ SBOM, 부분 매핑) | ✗ API Catalog/Discovery 별도 카탈로그 필요 |
| API10:2023 | Unsafe Consumption of APIs | ◐ | `security-api-web.md#2-hmac-request-signing` (downstream 검증), `security-crypto-ops.md#9-mtls-mutual-tls` | ✗ 3rd-party API trust boundary 추후 추가 예정 |

**API 커버리지**: 10/10 (API6 / API9 / API10 부분 매핑 ◐)

### OWASP Mobile Top 10 (2024)

2024 개정판은 **인증/인가가 M1 으로 격상**되고, Insufficient Cryptography → M10 으로 재배치된 것이 핵심 변경.

| OWASP ID | 이름 | 매핑 | dev-advisor anchor | 추가 참조 |
|---|---|:--:|---|---|
| M1:2024 | Insecure Authentication / Authorization | ● | `security-authn.md#1-oauth2-authorization-code--pkce-rfc-7636`, `#4-fido2--webauthn--passkeys`, `security-authz.md#1-rbac-role-based-access-control` | `security-mobile.md#2-app-attest--play-integrity-앱디바이스-무결성-증명` |
| M2:2024 | Inadequate Supply Chain Security | ● | `security-supply-chain.md#1-sbom-software-bill-of-materials`, `#2-sigstore--cosign-keyless-artifact-signing`, `#3-slsa-framework-supply-chain-levels-for-software-artifacts` | `security-mobile.md#2-app-attest--play-integrity-앱디바이스-무결성-증명` |
| M3:2024 | Insecure Authentication / Authorization | ● | (M1 과 동일 매핑 — 2024 카테고리 통합) `security-authn.md`, `security-authz.md` 전반 | — |
| M4:2024 | Insufficient Input/Output Validation | ◐ | `security-api-web.md#8-mass-assignment-방어`, `#10-graphql-보안` | ✗ 모바일 IPC/Deep Link validation 추후 추가 예정 |
| M5:2024 | Insecure Communication | ● | `security-mobile.md#1-certificate-pinning-인증서-핀닝`, `security-crypto-ops.md#9-mtls-mutual-tls`, `#5-perfect-forward-secrecy-pfs` | `security-api-web.md#11-csp--sri--hsts--trusted-types-web-보안-헤더` |
| M6:2024 | Inadequate Privacy Controls | ● | `privacy-engineering.md#2-privacy-by-design-pbd`, `#5-purpose-binding--purpose-limitation-목적-제한`, `#8-data-minimization-개인정보-최소-수집` | `compliance.md` (GDPR/CCPA) |
| M7:2024 | Insufficient Binary Protections | ● | `security-mobile.md#3-jailbreak--root-detection-탈옥-및-루팅-탐지`, `#4-rasp-runtime-application-self-protection` | `security-mobile.md#2-app-attest--play-integrity-앱디바이스-무결성-증명` |
| M8:2024 | Security Misconfiguration | ◐ | `security-platform.md#7-hardening-baseline-cis` (서버 위주), `security-mobile.md#5-secure-storage-안전한-로컬-저장소` | ✗ 모바일 manifest/entitlement 검수 추후 추가 |
| M9:2024 | Insecure Data Storage | ● | `security-mobile.md#5-secure-storage-안전한-로컬-저장소`, `security-data-protection.md#2-field-level-encryption-필드-단위-암호화` | `security-crypto-ops.md#1-kms-key-management-service` |
| M10:2024 | Insufficient Cryptography | ● | `security-crypto-ops.md#7-crypto-agility`, `#6-post-quantum-cryptography-pqc`, `security-data-protection.md#1-encryption-at-rest-저장-데이터-암호화` | `algorithms/crypto.md` (primitive 선택) |

**Mobile 커버리지**: 10/10 (M4 / M8 부분 매핑 ◐, M3 는 M1 과 통합 매핑)

### OWASP LLM Top 10 (2025)

LLM 애플리케이션 전용 위험. 대부분 `security-ai-model.md` + `patterns/ai-llm.md` 와 cross-link.

| OWASP ID | 이름 | 매핑 | dev-advisor anchor | 추가 참조 |
|---|---|:--:|---|---|
| LLM01:2025 | Prompt Injection | ◐ | `patterns/ai-llm.md` (Guardrails ownership), `security-ai-model.md#4-adversarial-inputs--evasion-attack-적대적-입력--회피-공격` | ✗ Prompt Injection 전용 anchor 는 `patterns/ai-llm.md` ownership |
| LLM02:2025 | Sensitive Information Disclosure | ● | `security-data-protection.md#5-data-masking-데이터-마스킹`, `#6-pseudonymization-가명처리`, `privacy-engineering.md#8-data-minimization-개인정보-최소-수집` | `security-supply-chain.md#8-ai-assisted-code-secret-leak-defense` |
| LLM03:2025 | Supply Chain | ● | `security-supply-chain.md#1-sbom-software-bill-of-materials`, `#7-slopsquatting--hallucinated-package-defense`, `#8-ai-assisted-code-secret-leak-defense` | `security-supply-chain.md#3-slsa-framework-supply-chain-levels-for-software-artifacts` |
| LLM04:2025 | Data and Model Poisoning | ● | `security-ai-model.md#3-data-poisoning-학습-데이터-오염-공격` | `security-ai-model.md#5-federated-learning-보안-분산-학습-위협과-방어` |
| LLM05:2025 | Improper Output Handling | ◐ | `security-api-web.md#11-csp--sri--hsts--trusted-types-web-보안-헤더` (output sanitization 일반), `patterns/ai-llm.md` (Output Validation) | ✗ LLM 출력 → downstream injection 전용 가이드 추후 추가 |
| LLM06:2025 | Excessive Agency | ◐ | `security-authz.md#5-permission-boundary`, `#6-least-privilege-구현-패턴-just-enough-access--time-bound` | ✗ Agent tool-use scope 제한 별도 카탈로그 필요 |
| LLM07:2025 | System Prompt Leakage | ✗ | — | ✗ 추후 추가 예정 — `patterns/ai-llm.md` 와 협의 |
| LLM08:2025 | Vector and Embedding Weaknesses | ◐ | `security-ai-model.md#2-membership-inference-attack-멤버십-추론-공격` (vector inversion 유사) | ✗ Vector DB 격리/임베딩 무결성 추후 추가 |
| LLM09:2025 | Misinformation | ◐ | `security-ai-model.md#3-data-poisoning-학습-데이터-오염-공격` (학습 데이터 무결성 측면) | ✗ Hallucination grounding/RAG citation 검증은 `patterns/ai-llm.md` ownership |
| LLM10:2025 | Unbounded Consumption | ● | `security-api-web.md#1-per-identity-rate-limiting-신원별-레이트-리미팅`, `security-ai-model.md#1-model-extraction--theft-모델-복제-공격` | `patterns/reliability.md` (Rate Limiter / Token Bucket) |

**LLM 커버리지**: 9/10 (LLM01 / LLM05 / LLM06 / LLM08 / LLM09 부분 매핑 ◐, LLM07 미매핑 ✗ — Prompt 시스템 분리·System Prompt 보호 항목 추후 카탈로그 추가 예정)

### 시리즈 합산 커버리지 요약

| 시리즈 | 정확(●) | 부분(◐) | 미매핑(✗) | 총 커버 |
|---|:--:|:--:|:--:|:--:|
| Web Top 10 (2021) | 9 | 1 | 0 | 10/10 |
| API Top 10 (2023) | 7 | 3 | 0 | 10/10 |
| Mobile Top 10 (2024) | 8 | 2 | 0 | 10/10 |
| LLM Top 10 (2025) | 4 | 5 | 1 | 9/10 |
| **합계** | **28** | **11** | **1** | **39/40** |

**보완 우선순위**: LLM07 (System Prompt Leakage) → LLM 전용 anchor 신설이 최우선. 다음으로 API9/API10 (API Inventory / 3rd-party Trust), M4/M8 (Mobile IPC validation / manifest 검수), LLM05/LLM06/LLM08 (Output handling / Agent scope / Vector DB).
