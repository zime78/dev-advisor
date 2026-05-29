# `security-audit` 모드 — STRIDE / OWASP / NIST 보안 점검

모듈/API에 대해 STRIDE 6 카테고리 위협 모델 + DREAD/CVSS/EPSS/KEV 위험도 + 컴플라이언스 매핑을 산출한다.

## 4단계 입출력

| 4단계 인풋 | 4단계 산출 |
|-----------|-----------|
| 모듈/API 필수 | STRIDE 6행 표 + DREAD/CVSS/EPSS/KEV 위험도 + 대응책 + 컴플라이언스 |

## 인용 references

- [`references/security/security-sdlc.md`](../security/security-sdlc.md) — STRIDE / DREAD / CVSS / EPSS / KEV / OWASP Risk Rating
- [`references/security/index.md`](../security/index.md) — 표준 매트릭스
- security 도메인 전체:
  - `security`, `security-authn`, `security-authz`
  - `security-crypto-ops`, `security-data-protection`
  - `security-api-web`, `security-supply-chain`
  - `security-platform`, `security-sdlc`, `security-detect-respond`
  - `security-mobile`, `security-ai-model`
  - `privacy-engineering`, `compliance`
- [`references/principles/12-factor.md`](../principles/12-factor.md) — 운영 보안

## 공통 6단계 절차

1. **입력 수집** — 모듈/API 필수
2. **컨텍스트 분류** — 언어 자동 감지, 데이터 민감도, blast radius, 노출 표면(public/internal)
3. **기준 매핑** — 위 "인용 references" 항목 식별
4. **분석/판정** — STRIDE 6행 표 + DREAD/CVSS/EPSS/KEV 위험도 + 대응책 + 컴플라이언스
5. **근거 산출 (필수)** — 아래 6 필드 템플릿
6. **검증/후속 계획** — `security-reviewer` (DREAD ≥ 8 / threat model 신규) + `verifier`

## 5단계 6 필드 공통 템플릿 (필수)

- **선택/판정**: 4단계 결과의 핵심 결론 1~2줄
- **근거 (Why)**: 왜 그렇게 판단했는가 — 정량/정성 신호
- **대안 비교**: A vs B vs C 형태로 대안 2~3개 + 각 trade-off
- **표준 인용**: OWASP / NIST / RFC / ISO 27001 / PCI-DSS 등 직접 anchor link
- **적용 조건**: 이 결정이 유효한 컨텍스트
- **비추천 조건**: 이 통제를 안 써야 할 때 (carve-out, risk acceptance 가능 시)

## 산출물 출력 스켈레톤

```
## Security Audit — <module|api>

### STRIDE 6행
| # | 카테고리 | 위협 | DREAD | CVSS | EPSS/KEV | 대응책 | 컴플라이언스 |

### 6 필드
선택/판정 / 근거 / 대안 비교 / 표준 인용 / 적용 조건 / 비추천 조건
```

## 공통 severity 정규화

| 등급 | 정의 |
|------|------|
| P1 | Critical/High, CVSS ≥ 7.0, EPSS 상위권, CISA KEV 등재, 민감 데이터 high, blast radius 큼, exploitability 높음 |
| P2 | Medium, OWASP Risk Rating Medium, 보완 통제 필요 |
| P3 | Low, exploitability 낮음, 승인된 risk acceptance |

보안 risk acceptance는 소유자, 만료일, 대체 통제, 재검토 조건을 포함해야 하며, 민감 데이터·공개 노출·권한 상승 가능성이 있으면 기본값은 P1이다.

## OMC hand-off 후보

- DREAD ≥ 8 / 컴플라이언스 carve-out / threat model 신규 → `security-reviewer`
- 변경 후 회귀 확인 → `verifier`
