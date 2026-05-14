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

## 보안 ID → 파일 매핑 (97개)

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
- AI 모델: MITRE ATLAS, OWASP LLM Top 10
- 규제: GDPR, CCPA/CPRA, PCI DSS v4.0, HIPAA, SOC 2 TSP 100
