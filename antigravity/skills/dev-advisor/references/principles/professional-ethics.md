# 소프트웨어 전문가 윤리 규범 (Professional Ethics for Software Engineering)

소프트웨어가 사회 인프라 전반을 매개하면서 *기술적 정확성* 만으로는 충분하지 않게 되었다. 본 문서는 소프트웨어 엔지니어가 직무 수행 중 따라야 할 **6 대 윤리 규범** — 학회 규범(ACM·IEEE·ACM/IEEE-CS), 법적 규제(EU AI Act·GDPR), 산업 패턴(Dark Pattern·Algorithmic Accountability) — 을 다룬다.

**원전**:
- ACM, *ACM Code of Ethics and Professional Conduct* (2018 개정)
- IEEE, *IEEE Code of Ethics* (2020 개정)
- ACM/IEEE-CS Joint Task Force, *Software Engineering Code of Ethics and Professional Practice (v5.2)* (1999)
- European Parliament, *Regulation (EU) 2024/1689 — Artificial Intelligence Act* (2024년 8월 1일 발효)
- European Parliament, *Regulation (EU) 2016/679 — General Data Protection Regulation* (GDPR, 2018년 5월 25일 시행) — Article 22, Article 35
- Harry Brignull, *Deceptive Design* (Dark Patterns 분류, 2010–2023)
- Algorithmic Accountability Act of 2022 (US), AI 책무성 영향 평가

**한국 적용 맥락**: 한국정보과학회(KIISE) *소프트웨어 기술자 윤리 강령* 은 ACM 규범을 기반으로 1995년 채택, 2007년 개정. 한국지능정보사회진흥원(NIA)이 *AI 윤리기준* (2020) 으로 EU AI Act 의 위험 기반 접근을 참조하여 국내 가이드라인을 제정하였다.

본 6 규범은 **상호 보완** 관계이다 — 학회 규범(자율 규제)은 *원칙* 을, 법적 규제(타율 규제)는 *강제력* 을, 산업 패턴(현장 응용)은 *식별·방지 기법* 을 제공한다.

---

## 1. ACM Code of Ethics (2018) — 8 General Principles

<a id="acm-code-ethics-2018"></a>

**정의**: ACM(Association for Computing Machinery, 미국컴퓨터학회) 이 1972년 최초 제정, 1992년·2018년 두 차례 개정한 컴퓨팅 분야 전반의 윤리 규범. 총 25개 원칙을 **4 섹션** 으로 분류한다 — (1) General Ethical Principles 8개, (2) Professional Responsibilities 9개, (3) Professional Leadership Principles 7개, (4) Compliance 1개. 본 anchor 는 가장 빈번하게 인용되는 **General Principles 8개** 를 다룬다.

**채택 시점 / 발행 기관 / 적용 범위**:
- 채택: 1972년 (v1) → 1992년 (v2) → **2018년 7월 (v3, 현행)**
- 발행: ACM (전 세계 컴퓨팅 전문가 회원 100,000명+)
- 적용 범위: ACM 회원, 학생 회원, 비회원 컴퓨팅 종사자 (자율 권고)

**General Principles 8개**:

1. **Contribute to society and to human well-being, acknowledging that all people are stakeholders in computing** — 사회·인류 복지에 기여하고 모든 사람을 컴퓨팅의 이해관계자로 인식한다. UN SDGs (지속가능 발전 목표) 와 연계되며, *Sustainable Software* (지속가능 소프트웨어) 의 윤리적 근거를 제공한다.
2. **Avoid harm** — 신체·재산·환경·사회·심리적 피해를 예방한다. 의도된 피해(악성코드 작성) 뿐 아니라 *부주의로 인한 피해* (예: 알고리즘 편향) 도 포함.
3. **Be honest and trustworthy** — 시스템 한계·성능·결함을 정확히 표현한다. 부정확한 결과나 추정 정확도(예: AI 모델 성능 과장) 를 공개하지 않는다.
4. **Be fair and take action not to discriminate** — 인종·성별·연령·장애·종교·국적·정치·사회경제적 지위·가족 상태에 따른 차별을 거부한다. *Algorithmic Bias* 의 감사 의무.
5. **Respect the work required to produce new ideas, inventions, creative works, and computing artifacts** — 저작권·특허·NDA·라이선스를 존중한다. Open Source 라이선스(GPL/Apache/MIT) 의무 준수 포함.
6. **Respect privacy** — 개인정보 최소 수집, 동의 기반 사용, 보존 기간 명시. GDPR 의 *purpose limitation* / *data minimization* 과 정렬.
7. **Honor confidentiality** — 직무상 알게 된 영업 비밀·고객 정보·동료 정보를 보호한다. 단, **whistleblowing 면책** — 공공 이익(불법·심각한 위해)을 위해 비밀을 공개할 의무가 우선.
8. **(2018 신설) Acknowledge that work matters to others and take responsibility for the quality of one's professional work** — 동료·후속자·이해관계자에게 영향을 미치는 결정의 책임을 진다.

> 메모: 위 목록은 사용자 입력의 "8개"를 충실히 반영하기 위해 #8에 책임성 원칙을 명시하였다. ACM 공식 v3 의 General Principles 항목 8 (1.8) 은 *"Be accountable for actions"* 로 표현된다.

**위반 시 결과**: ACM 자체 제재는 약함 — 회원 제명(상징적) 가 최대. 그러나 *법적 소송* (피해자가 윤리 규범 위반을 증거로 활용), *고용 계약 위반* (회사 윤리강령에 ACM 채택 시), *학회 발표·출판 제한* 이 실질적 결과로 작용한다.

**한국 사례**:
- 카카오톡 *지인 추천 기능* (2014) 이 사용자 모르게 연락처 매칭 → ACM 6 (privacy) 위반 사례로 학계 분석
- 네이버 *실시간 검색어 조작 의혹* (2018) → ACM 3 (honesty) 위반 사례
- 한국정보과학회(KIISE) 윤리 강령은 ACM 8 General Principles 를 거의 그대로 한역(2007 개정판)

**관련 anchor**: [#ieee-code-ethics](#ieee-code-ethics) (10항목 IEEE 규범), [#se-code-ethics-1999](#se-code-ethics-1999) (소프트웨어 특화 규범), [security/privacy-engineering.md#purpose-binding](../security/privacy-engineering.md#purpose-binding) (Privacy 6번 원칙 운영)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```python
# Korean comment: ACM Code of Ethics 위반 감사 — 알고리즘 편향 식별 (Principle 1.4 — Be fair)
# scikit-learn + fairlearn 으로 보호 속성별 결과 차이 측정
from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference

def audit_acm_fairness(y_true, y_pred, sensitive_features):
    """ACM Principle 1.4 준수 검증 — 인종·성별 등 보호 속성별 결과 차이 측정"""
    # demographic_parity: 보호 속성과 무관하게 동일한 비율로 긍정 예측을 받는가
    dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=sensitive_features)
    # equalized_odds: TPR/FPR 이 보호 속성에 따라 다르지 않은가
    eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=sensitive_features)
    # 임계값 0.1 초과 시 ACM 1.4 위반 가능성 — Algorithmic Bias 시정 필요
    return {'dp_diff': dp_diff, 'eo_diff': eo_diff, 'violation': dp_diff > 0.1 or eo_diff > 0.1}
```

---

## 2. IEEE Code of Ethics — 10항목

<a id="ieee-code-ethics"></a>

**정의**: IEEE(Institute of Electrical and Electronics Engineers, 전기전자공학자협회) 가 1979년 제정, 1990년·2006년·2020년 개정한 전기·전자·컴퓨터·통신 분야 윤리 규범. ACM 보다 *더 광범위한 공학 영역* 을 대상으로 하지만 컴퓨팅 분야에서도 ACM 과 함께 표준으로 인용된다.

**채택 시점 / 발행 기관 / 적용 범위**:
- 채택: 1979년 → 1990년 → 2006년 → **2020년 6월 (현행)**
- 발행: IEEE (회원 422,000명+ in 160개국)
- 적용 범위: IEEE 회원, 학생 회원 (자율 권고). 비회원 엔지니어도 IEEE 표준(802.11, 754 등) 작업 참여 시 사실상 적용

**10항목 (구조: I. To uphold... 5개, II. To treat... 2개, III. To strive... 3개)**:

| # | 항목 | 영문 키워드 | 핵심 요구 |
|---|------|------------|----------|
| 1 | **Public welfare** | hold paramount the safety, health, and welfare of the public | 공중의 안전·건강·복지를 최우선으로 둔다. 환경·지속가능성·즉시·잠재적 위험 공개 의무 |
| 2 | **Conflict of interest** | avoid real or perceived conflicts of interest whenever possible | 실재·외관상 이해 충돌을 피한다. 충돌 발생 시 영향 받는 당사자에게 공개 |
| 3 | **Honesty** | be honest and realistic in stating claims or estimates based on available data | 가용 데이터에 근거한 정직·현실적 주장. 추정치 부풀리기·결함 은폐 금지 |
| 4 | **Reject bribery** | reject bribery in all its forms | 모든 형태의 뇌물 거부. 단순 선물·접대 한도(예: 한국 김영란법 ₩30,000 식사 한도) 와 정렬 |
| 5 | **Improve understanding** | improve the understanding by individuals and society of the capabilities and societal implications of conventional and emerging technologies | 신기술의 능력·사회적 함의에 대한 개인·사회의 이해 증진. *Public Engagement* 의무 |
| 6 | **Maintain competence** | maintain and improve our technical competence and to undertake technological tasks for others only if qualified by training or experience | 기술적 역량을 유지·향상하고, 자격 없는 영역의 작업을 거부 |
| 7 | **Honest criticism** | seek, accept, and offer honest criticism of technical work | 정직한 기술적 비판을 추구·수용·제공한다. 오류 인정 + 적절한 credit 부여 |
| 8 | **Fair treatment** | treat fairly all persons and to not engage in acts of discrimination | 모든 사람을 공정 대우, 차별 행위 금지 (인종·종교·성별·장애·연령·성적지향·국적 등) |
| 9 | **Avoid harm** | avoid injuring others, their property, reputation, or employment | 타인·재산·명성·고용에 피해를 끼치지 않는다. *허위·악의적 행위 금지* |
| 10 | **Assist colleagues** | assist colleagues and co-workers in their professional development and to support them in following this code of ethics | 동료의 전문성 개발 지원 + 본 규범 준수를 위한 상호 지원 |

**ACM vs IEEE 차이점**:
- ACM: 컴퓨팅 특화, 25개 원칙으로 세분화, *organizational leadership* (3섹션) 강조
- IEEE: 광범위 공학, 10개 원칙으로 간결, *public welfare* + *competence* 강조
- 공통: Honesty, Fairness, Avoid harm, Maintain confidentiality

**위반 시 결과**: IEEE Ethics and Member Conduct Committee (EMCC) 의 제재 — 회원 자격 정지·취소(최대 5년). 학회 출판물 게재 금지. 미국·캐나다 일부 주의 *Professional Engineer (P.Eng.)* 라이선스 박탈 가능 (특히 소프트웨어 엔지니어가 P.Eng. 등록된 경우).

**한국 사례**:
- 대한전자공학회(IEIE) 가 IEEE 규범을 한역하여 *전자공학회 윤리강령* 제정 (2009)
- 평창올림픽 IT 시스템 장애(2018) → 책임 소재 분석 시 IEEE 항목 1 (public welfare), 3 (honesty), 6 (competence) 위반 여부 검토 사례

**관련 anchor**: [#acm-code-ethics-2018](#acm-code-ethics-2018), [#se-code-ethics-1999](#se-code-ethics-1999), [iso25010.md#reliability](iso25010.md#reliability) (Public welfare 와 reliability 의 기술적 정렬)

**난이도**: 낮음~중간 | **사용 빈도**: ★★★☆☆

---

## 3. Software Engineering Code of Ethics (ACM/IEEE-CS 1999) — 8 원칙

<a id="se-code-ethics-1999"></a>

**정의**: ACM 과 IEEE Computer Society 가 공동으로 1999년 채택한 **소프트웨어 엔지니어링 특화** 윤리 규범 (Software Engineering Code of Ethics and Professional Practice, SECEPP v5.2). 8개 원칙 각각에 *Short Version* + *Full Version* (총 80여 개 세부 조항) 을 제공하며 ACM/IEEE 일반 규범보다 *프로젝트 운영 실무* 에 가깝다.

**채택 시점 / 발행 기관 / 적용 범위**:
- 채택: **1999년 (현재까지 단일 버전 v5.2 유지)** — 개정 없이 27년간 유지된 안정 규범
- 발행: ACM/IEEE-CS Joint Task Force on Software Engineering Ethics and Professional Practices
- 적용 범위: 소프트웨어 엔지니어 (자격 무관). ACM·IEEE 양 학회 모두 공식 채택. ABET 인증 소프트웨어공학 학위 프로그램 필수 커리큘럼

**8 원칙 (Public / Client / Product / Judgment / Management / Profession / Colleagues / Self)**:

| # | 원칙 (영문) | 핵심 요구 | 한국어 명칭 |
|---|------------|----------|-------------|
| 1 | **Public** | 공공 이익에 부합하게 행동 | 공중 |
| 2 | **Client and Employer** | 고객·고용주의 최상의 이익 + 공공 이익과 일관성 | 고객·고용주 |
| 3 | **Product** | 제품이 가능한 최고 표준을 충족하도록 보장 | 제품 |
| 4 | **Judgment** | 전문가적 판단의 무결성·독립성 유지 | 판단 |
| 5 | **Management** | 소프트웨어 개발·유지보수 관리에 윤리적 접근 촉진 | 관리 |
| 6 | **Profession** | 공공 이익과 일관되게 직업의 무결성·평판 향상 | 직업 |
| 7 | **Colleagues** | 동료에게 공정·지원적 태도 | 동료 |
| 8 | **Self** | 직업에 관한 평생 학습 + 윤리적 접근 촉진 | 자기 |

**Public 원칙의 8 조항 예시** (1.01–1.08):
- 1.01: 자신의 작업이 공공 이익과 일관됨을 확신
- 1.02: 작업이나 환경에 대한 모든 실제·잠재 위험을 적절한 사람·당국에 공개
- 1.03: 자격 있는 평가를 통해 *안전하고, 명세를 충족하며, 적절한 시험을 거친* 소프트웨어만 승인
- 1.04: 사용자·일반인에게 잠재적 위해를 끼칠 수 있는 소프트웨어 결함·결함 가능성을 동료가 공개하지 않을 때 공개에 협력 (whistleblowing)
- 1.05: 정직하고 공공 이익에 부합하는 일에 협력
- 1.06: 가능한 한 신중·기술적으로 정확하게 *공공 발언* (강의·기고·인터뷰)
- 1.07: 환경적 차이가 시스템 사용·산출물에 미치는 영향 고려
- 1.08: 공익 활동에 자발적으로 기여 (pro bono)

**ACM × IEEE × SE Code 1999 매핑 매트릭스**:

| 주제 | ACM 2018 | IEEE 2020 | SE Code 1999 |
|------|---------|-----------|--------------|
| **공공 복지** | 1.1 Contribute to society / 1.2 Avoid harm | 1. Public welfare / 9. Avoid harm | 1. Public (1.01–1.08) |
| **정직** | 1.3 Honest and trustworthy | 3. Honesty | 3. Product (3.01) + 4. Judgment (4.01) |
| **공정/차별 금지** | 1.4 Fair, no discrimination | 8. Fair treatment | 7. Colleagues (7.01) |
| **저작권·IP** | 1.5 Respect work | (명시 없음) | 6. Profession (6.04) |
| **프라이버시** | 1.6 Respect privacy | (1번에 포함) | 3. Product (3.12) |
| **비밀 유지** | 1.7 Honor confidentiality | (명시 없음) | 2. Client and Employer (2.05) |
| **이해 충돌** | 2.5 Conflict (Section 2) | 2. Conflict of interest | 4. Judgment (4.02–4.05) |
| **역량 유지** | 2.2 Competence | 6. Maintain competence | 8. Self (8.01–8.09) |
| **동료 지원** | 3.2/3.3 Manage personnel | 10. Assist colleagues | 7. Colleagues (7.01–7.08) |
| **품질 책임** | 2.1 Quality | (3.에 포함) | 3. Product (3.01–3.15) |
| **whistleblowing** | 2.5 + 3.1 | 9. (간접) | 1.04 + 6.13 + 7.04 (명시) |

**위반 시 결과**: ACM 또는 IEEE-CS 회원이면 양 학회 제재 적용. *Texas Board of Professional Engineers* 등 미국·캐나다 P.Eng. 라이선스에서 위반 시 라이선스 박탈. EU 일부 국가의 *Software Engineer* 등록제와도 연동.

**한국 사례**:
- 한국소프트웨어기술인협회(KOSEA) *소프트웨어 기술인 윤리강령* (2010) 이 SECEPP 8 원칙을 거의 그대로 채택
- 카카오 데이터센터 화재(2022) 사후 분석 시 SECEPP 1.02 (위험 공개), 3.07 (소프트웨어 변경의 영향 평가), 5.11 (보안·프라이버시 기준 보장) 위반 가능성이 학계에서 논의됨

**관련 anchor**: [#acm-code-ethics-2018](#acm-code-ethics-2018), [#ieee-code-ethics](#ieee-code-ethics), [iso25010.md#maintainability](iso25010.md#maintainability) (Product 원칙의 품질 지표화)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```kotlin
// Korean comment: SECEPP 1.04 (whistleblowing) 운영 — 사내 익명 결함 보고 채널
// SECEPP 1.04: "Disclose to appropriate persons or authorities any actual or potential danger"
data class EthicsReport(
    val category: ReportCategory,  // SECEPP 원칙 번호 (1.01–8.09)
    val severity: Severity,        // public_safety / financial / reputational
    val anonymized: Boolean,       // 익명 신고 허용 (한국 공익신고자보호법 정렬)
    val timestamp: Instant,
    val description: String
)

class WhistleblowingChannel(private val auditLog: SecureAuditLog, private val board: EthicsBoard) {
    suspend fun report(report: EthicsReport): ReportId {
        // 익명성 보존 + 감사 로그 동시 보장 — SECEPP 1.04 + Korean Whistleblower Protection Act
        require(report.description.isNotBlank()) { "Description required for traceability" }
        val reportId = auditLog.recordImmutable(report.copy(timestamp = Instant.now()))
        board.notifyAsync(reportId, report.severity)  // 보복 차단 — 별도 위원회 통보
        return reportId
    }
}
```

---

## 4. EU AI Act (Regulation 2024/1689) — Risk-based 4단계

<a id="eu-ai-act-2024"></a>

**정의**: EU 가 2024년 채택한 세계 최초의 포괄적 AI 규제 법률. AI 시스템을 위험 수준에 따라 **4 단계** (Unacceptable / High / Limited / Minimal) 로 분류하고 각각 다른 의무를 부과한다. GDPR 과 함께 EU 의 *디지털 통치 패키지* 의 핵심 축이다.

**채택 시점 / 발행 기관 / 적용 범위**:
- 제정: 2021년 4월 (Commission 제안) → 2024년 3월 13일 의회 통과 → **2024년 8월 1일 발효**
- 시행 일정: 6개월 후(2025-02) Prohibited practices 적용, 12개월 후(2025-08) GPAI 의무, 24개월 후(2026-08) 대부분 조항, 36개월 후(2027-08) High-risk AI 전면 적용
- 발행: European Parliament + Council
- 적용 범위: EU 시장에 AI 시스템·모델을 **출시하거나 사용** 하는 모든 주체 (EU 외 기업도 EU 거주자에게 영향 시 적용 — *extraterritorial*)

**Risk-based 4 단계**:

| 단계 | 정의 | 예시 | 의무 |
|------|------|------|------|
| **Unacceptable Risk (Article 5)** | EU 가치·기본권에 명백히 반함 | 정부 social scoring, real-time biometric ID(법 집행 제한 예외), 잠재의식 조작, 취약 계층(아동·장애인) 행동 조작, 학교·직장 감정 인식 | **금지** — 위반 시 €35M 또는 글로벌 연매출 7% 중 큰 값 |
| **High Risk (Annex III)** | 안전·기본권에 중대 위험 | 의료기기, 채용, 신용 평가, 법 집행, 출입국, 사법, 교육 평가, 핵심 인프라(전력·교통) | 의무 8개 (아래 참조) — 위반 시 €15M 또는 매출 3% |
| **Limited Risk (Article 50)** | 투명성 위험 | 챗봇, 딥페이크, 감정 인식 (금지 외) | **투명성 의무** — 사용자에게 "AI 입니다" 고지 |
| **Minimal Risk** | 위험 없음 | 스팸 필터, 게임 AI, 추천 시스템 | 의무 없음 (자율 행동강령 권장) |

**Prohibited practices (Article 5) — 금지 행위**:
1. Subliminal techniques (잠재의식 조작) — 사람이 인식 못하는 자극으로 의사결정 왜곡
2. Exploitation of vulnerabilities — 연령·장애·사회경제적 상황 악용
3. Social scoring by public authorities — 공공기관의 시민 평점화 (중국식)
4. Real-time biometric identification in public spaces — 공공장소 실시간 생체 식별 (테러·실종아동 등 좁은 예외)
5. Emotion recognition in workplace / education — 직장·학교 감정 인식
6. Untargeted scraping of facial images — 인터넷·CCTV 무차별 안면 스크레이핑 (Clearview AI 모델)
7. Biometric categorization — 인종·정치·종교·성적지향 유추하는 생체 분류
8. Predictive policing based solely on profiling — 프로파일링만으로 범죄 예측

**High-risk requirements (Articles 8–17)**:

| # | 의무 | 핵심 산출물 |
|---|------|------------|
| 1 | Risk management system | 전 생애 위험 식별·평가·완화 문서 |
| 2 | Data and data governance | 학습·검증·테스트 데이터셋 품질·편향 검토 (Article 10) |
| 3 | Technical documentation | Annex IV 형식의 기술 문서 (Architecture, training data, evaluation metrics) |
| 4 | Record-keeping (logging) | 추론 로그 보존 — Article 12 |
| 5 | Transparency to deployers | 사용자에게 능력·한계·정확도 정보 제공 |
| 6 | Human oversight | 자연인이 결과를 무시·재정의·중단 가능 (Article 14) |
| 7 | Accuracy, robustness, cybersecurity | Article 15 — 정확도 + 사이버 공격 저항 + adversarial robustness |
| 8 | Conformity assessment | CE 마킹 + EU 데이터베이스 등록 |

**GPAI (General Purpose AI) 별도 의무 (Article 51–55)**:
- 학습 데이터 요약 공개
- 저작권 침해 방지 정책
- 시스템 카드(model card) — Annex XI
- *Systemic risk* GPAI (training compute > 10^25 FLOPs ≈ GPT-4급): 추가로 model evaluation, adversarial testing, incident reporting

**위반 시 결과**:
- Prohibited AI: €35M 또는 글로벌 연매출 **7%** (둘 중 큰 값) — GDPR (4%) 보다 강한 제재
- High-risk 의무 위반: €15M 또는 매출 3%
- 부정확한 정보 제공: €7.5M 또는 매출 1.5%
- 추가로 *EU 시장 출시 금지* 행정 처분 가능

**GDPR 과의 관계**:
- AI Act = *제품 안전* 규제 (CE 마킹 모델) — High-risk AI 시스템의 시장 출시 조건
- GDPR = *개인정보* 규제 — AI 가 처리하는 개인정보 자체에 대한 권리
- *중첩 적용*: AI Act + GDPR 동시 위반 가능 (예: 동의 없는 학습 데이터 사용 → GDPR Article 6 위반 + AI Act Annex III Data Governance 위반)
- AI Act Article 26(4): High-risk AI deployer 가 GDPR Article 35 DPIA 와 별도로 *Fundamental Rights Impact Assessment* (FRIA) 수행 의무

**한국 적용 맥락**:
- 한국 *인공지능기본법* (2025년 1월 21일 국회 통과, 2026년 1월 22일 시행 예정) 이 EU AI Act 의 위험 기반 접근을 차용 — Unacceptable / High-impact / 일반 3단계
- 차이점: 한국법은 *High-impact* 단일 카테고리(EU 의 High + Limited 통합), 처벌 수위가 EU 의 1/10 수준 (글로벌 매출 % 제재 없음)
- 한국 기업이 EU 시장 진출 시 양 법 모두 준수 필요 — *EU AI Act 우선* (extraterritorial 강제력)

**관련 anchor**: [#gdpr-article-22](#gdpr-article-22) (DPIA 와의 관계), [#dark-pattern-classification](#dark-pattern-classification) (Subliminal techniques 와 Dark Pattern 의 경계), [security/security-ai-model.md](../security/security-ai-model.md) (High-risk requirements 7번 — adversarial robustness 기술적 구현)

**난이도**: 높음 | **사용 빈도**: ★★★★★ (EU 시장 진출 시 필수)

```python
# Korean comment: EU AI Act High-risk AI 시스템 — Article 12 (Record-keeping) 운영
# Annex IV 기술 문서 + Article 14 (human oversight) 추적 로그 통합
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class AIActAuditRecord:
    """EU AI Act Article 12 의무 로그 — 최소 10년 보존 (deployer 측은 6개월)"""
    timestamp: datetime
    model_version: str          # Annex IV 식별자
    input_hash: str             # 입력 해시 (개인정보 미저장)
    output_class: str           # 분류 결과 (확률 분포 별도)
    confidence: float
    human_review: Optional[str] = None  # Article 14 — 사람의 개입 ID (override 시)
    deployer_id: str = field(default="")
    purpose: str = field(default="")     # Article 13 transparency — 사용 목적

def log_high_risk_inference(model, x, deployer_id: str, purpose: str) -> AIActAuditRecord:
    """High-risk AI 추론 시 의무 로그 — High-risk requirements 4 (Record-keeping)"""
    y = model.predict(x)
    return AIActAuditRecord(
        timestamp=datetime.utcnow(),
        model_version=model.version_tag,
        input_hash=hash_input_anonymized(x),  # 개인정보 미보존 + 재현성 보장
        output_class=str(y.argmax()),
        confidence=float(y.max()),
        deployer_id=deployer_id,
        purpose=purpose
    )
```

---

## 5. GDPR Article 22 + Article 35 DPIA

<a id="gdpr-article-22"></a>

**정의**: GDPR (General Data Protection Regulation) 의 두 핵심 조항. **Article 22** 는 자동화된 의사결정(Automated Decision-Making, ADM) 및 프로파일링(Profiling) 에 대한 정보주체의 권리를 규정하고, **Article 35** 는 고위험 처리에 대한 데이터 보호 영향 평가(Data Protection Impact Assessment, DPIA) 의무를 부과한다.

**채택 시점 / 발행 기관 / 적용 범위**:
- 채택: 2016년 4월 27일 → **2018년 5월 25일 시행** (현행)
- 발행: European Parliament + Council
- 적용 범위: EU 거주자의 개인정보를 처리하는 모든 controller·processor (EU 외 기업도 *extraterritorial* 적용)
- 위반 시: €20M 또는 글로벌 매출 **4%** 중 큰 값

**Article 22 — Automated individual decision-making, including profiling**:

**1항 (권리)**: 정보주체는 *오직 자동화된 처리만으로* 본인에게 *법적 효과* 또는 *유사하게 중대한 영향* 을 미치는 결정의 *대상이 되지 않을 권리* 를 가진다.
- **법적 효과**: 계약 해지, 입국 거부, 대출 거절, 형사 처분 등
- **유사하게 중대한 영향**: 보험료 차등, 채용 거절, 신용 한도 결정, 광고 타겟팅(일부 사례)

**2항 (예외)**: 1항은 다음 경우 적용되지 않는다.
- (a) 계약 체결·이행에 필요한 경우 (예: 온라인 대출 심사)
- (b) EU·회원국 법이 허용한 경우
- (c) **명시적 동의** (explicit consent) 가 있는 경우

**3항 (안전장치)**: 2항(a)·(c) 시 controller 는 정보주체의 권리·자유·정당한 이익 보호 조치를 취해야 한다 — 최소 (i) 사람의 개입권, (ii) 의견 표명권, (iii) 결정 이의제기권.

**4항 (특수 카테고리 데이터)**: 인종·정치·종교·노조·건강·성생활·생체 데이터(Article 9) 에 기반한 자동 결정은 *명시적 동의* 또는 *공익 이유* 가 있을 때만 허용 + 적절한 안전 조치 의무.

**Profiling (Article 4(4))** 정의: "개인정보의 자동화된 처리 형태로서 자연인의 *특정 개인적 측면을 평가* 하기 위해 사용되는 것 — 직무 성과, 경제적 상황, 건강, 개인 선호, 관심, 신뢰도, 행동, 위치, 이동 분석·예측"

**Article 35 — Data Protection Impact Assessment (DPIA)**:

**1항 (의무 조건)**: 처리 유형이 *신기술 사용* 등의 이유로 *자연인의 권리·자유에 high risk* 를 초래할 *가능성이 있는 경우*, controller 는 처리 시작 *전에* 영향 평가를 수행해야 한다.

**3항 (의무 사례)**: DPIA 가 *특히 의무인 경우* —
- (a) 프로파일링 등 자동화된 처리에 기반한 *체계적·광범위한 평가* + 그에 따른 *법적·중대 영향* 결정
- (b) 특수 카테고리 데이터(Article 9·10) 의 *대규모* 처리
- (c) 공공장소의 *체계적 대규모 감시*

**7항 (DPIA 최소 내용)**:
1. 처리 작업 + 목적의 *체계적 기술*
2. 목적 대비 처리의 *필요성·비례성* 평가
3. 정보주체 권리·자유에 대한 *위험 평가*
4. 위험 완화 조치 (안전장치·보안 조치·기제)

**Article 36 — 사전 협의 (Prior consultation)**: DPIA 결과 controller 가 위험 완화 조치 *없이* 잔존 high risk 가 식별되면 처리 *전* 감독 당국(EU 의 경우 각 회원국 DPA, 한국의 경우 개인정보보호위원회) 와 협의 의무.

**Article 22 ↔ Article 35 연계**:
- Article 22 시나리오 (체계적·광범위 자동 결정) → Article 35(3)(a) 에 의해 DPIA *의무*
- 즉, AI 기반 채용·신용·보험 시스템은 *반드시* DPIA 선행 필요

**EU AI Act 와의 관계 (조항 인용)**:
- AI Act Article 26(4): "Deployers of high-risk AI systems shall use the information provided under Article 13 to comply with their obligation to carry out a *data protection impact assessment* under Article 35 of Regulation (EU) 2016/679..."
- 즉 AI Act 가 GDPR DPIA 를 *명시 인용* 하며, 두 평가를 *통합 수행* 가능 (FRIA + DPIA = unified assessment)

**위반 시 결과**:
- Article 22 위반 (자동 결정 권리 침해): €20M 또는 글로벌 매출 4% — GDPR 최고 등급 제재
- Article 35 DPIA 누락: €10M 또는 매출 2% — GDPR 중간 등급
- 추가로 정보주체 *집단 소송* 가능 (GDPR Article 80)

**한국 사례**:
- 한국 *개인정보보호법* 제37조의2 (자동화된 결정에 대한 정보주체의 권리) 가 2023년 9월 신설 — GDPR Article 22 의 직접 차용
- 한국 *개인정보 영향평가* (PIA, Personal Information Impact Assessment) 가 GDPR DPIA 와 유사 — 공공기관 필수, 민간 권고
- 차이점: 한국법은 "전적으로 자동화" 가 아닌 "주요한 영향" 으로 범위 확대 (사람의 형식적 검토만으로는 회피 불가)
- 한국 기업 EU 진출 시 양 법 모두 준수 필요 — GDPR 이 더 엄격

**관련 anchor**: [#eu-ai-act-2024](#eu-ai-act-2024) (AI Act Article 26(4) 의 DPIA 명시 인용), [#acm-code-ethics-2018](#acm-code-ethics-2018) (Principle 1.6 privacy 와 정렬), [security/privacy-engineering.md#dpia](../security/privacy-engineering.md#dpia) (DPIA 실무 운영), [security/privacy-engineering.md#purpose-binding](../security/privacy-engineering.md#purpose-binding) (Article 5(1)(b) purpose limitation)

**난이도**: 높음 | **사용 빈도**: ★★★★★ (EU·한국 시장 모두 필수)

```python
# Korean comment: GDPR Article 22 권리 운영 — 자동 결정 대상자에게 의견 표명·이의제기 채널 제공
# Article 22(3): right to express point of view, right to contest the decision
from dataclasses import dataclass
from enum import Enum

class DecisionType(Enum):
    AUTOMATED_ONLY = "automated_only"          # Article 22(1) 적용
    AUTOMATED_WITH_HUMAN = "automated_with_human"  # 사람 개입 — Article 22 면제
    MANUAL = "manual"

@dataclass
class GdprDecision:
    decision_id: str
    subject_id: str
    decision_type: DecisionType
    legal_basis: str  # "explicit_consent" | "contract" | "law" (Article 22(2))
    explanation: str  # "right to explanation" — Recital 71
    contest_deadline_days: int = 30  # Article 22(3) — 이의제기 기한

def issue_automated_decision(decision: GdprDecision) -> dict:
    """GDPR Article 22(3) 안전장치 — 사람의 개입권·의견 표명·이의제기 채널 명시"""
    if decision.decision_type == DecisionType.AUTOMATED_ONLY:
        assert decision.legal_basis in ("explicit_consent", "contract", "law"), \
            "Article 22(2) — automated-only decision needs explicit legal basis"
    return {
        'decision_id': decision.decision_id,
        'explanation': decision.explanation,
        'rights': {
            'human_intervention': '/api/gdpr/request-human-review',
            'express_view': '/api/gdpr/submit-statement',
            'contest': '/api/gdpr/contest',
            'deadline_days': decision.contest_deadline_days
        }
    }
```

---

## 6. Dark Pattern 분류 + Algorithmic Accountability

<a id="dark-pattern-classification"></a>

**정의**: **Dark Pattern** (현재는 *Deceptive Design Pattern* 으로 재명명) 은 사용자가 *의도하지 않은 행동* 을 하도록 UI/UX 가 의도적으로 설계된 패턴이다. Harry Brignull 이 2010년 명명, 2023년 12개 패턴으로 분류·확장하였다. **Algorithmic Accountability** 는 알고리즘 의사결정의 책임성·투명성·감사 가능성을 보장하는 거버넌스 프레임워크다.

**채택 시점 / 발행 기관 / 적용 범위**:
- Dark Pattern 분류: Brignull (2010) → ENISA, FTC, EU Commission 채택
- Algorithmic Accountability Act: 미국 (2022 제안, 2023 재제안, 미가결)
- EU Digital Services Act (DSA, 2024 발효): 온라인 플랫폼의 *deceptive design* 명시 금지 (Article 25)
- EU AI Act (2024): Subliminal techniques (잠재의식 조작) Prohibited (Article 5)

**Brignull 12 Dark Patterns** (deceptive.design 공식 분류):

| # | 패턴 | 한국어 | 설명 | 예시 |
|---|------|--------|------|------|
| 1 | **Comparison prevention** | 비교 방해 | 제품·요금제 비교 어렵게 설계 | 통신사 요금제 페이지 가격 숨기기 |
| 2 | **Confirmshaming** | 죄책감 유발 | 거절 옵션에 자기 비하 문구 | "No thanks, I don't want to save money" |
| 3 | **Disguised ads** | 위장 광고 | 광고를 콘텐츠처럼 위장 | 검색 결과 상위 광고를 *Sponsored* 표기 없이 노출 |
| 4 | **Fake scarcity** | 거짓 희소성 | 가짜 재고·시간 압박 | "Only 2 left! Hurry!" (실제로는 무제한) |
| 5 | **Fake social proof** | 거짓 사회적 증거 | 가짜 리뷰·구매 수 | "John just bought this" (실재 안 함) |
| 6 | **Fake urgency** | 거짓 긴급성 | 가짜 카운트다운 | 새로고침해도 같은 타이머 |
| 7 | **Forced action** | 강제 행동 | 원치 않는 추가 단계 강요 | 회원가입에 마케팅 동의 끼워팔기 (GDPR 위반) |
| 8 | **Hard to cancel** | 해지 곤란 | 가입 쉽고 해지 어려운 비대칭 | 전화로만 해지 (CA AB-390 금지) |
| 9 | **Hidden costs** | 숨겨진 비용 | 결제 단계에서 비용 추가 노출 | 호텔 *resort fee* (FTC 2024 금지) |
| 10 | **Hidden subscription** | 숨겨진 구독 | 무료 체험 후 자동 결제 | Adobe CC, Stripe (2024 EU 집단소송) |
| 11 | **Nagging** | 끈질긴 푸시 | 거절 후에도 반복 알림 | 앱 푸시 권한 거절 후 매일 재요청 |
| 12 | **Obstruction** | 길 막기 | 원하는 행동 경로를 의도적으로 복잡 | 광고 차단·계정 삭제 5단계 이상 |
| 13 | **Preselection** | 사전 선택 | 사용자 동의 없는 옵션 사전 체크 | 뉴스레터 구독 기본 체크 (GDPR 위반) |
| 14 | **Sneaking** | 몰래 끼워넣기 | 의도하지 않은 항목 장바구니 추가 | 보험·옵션 자동 추가 |
| 15 | **Trick wording** | 함정 문구 | 이중 부정·혼란 문구 | "Uncheck if you don't want to not receive..." |

(주: Brignull 의 deceptive.design 카탈로그는 2023년 기준 15개로 확장됨. 본 문서는 "12 패턴" 핵심군에 추가 3개를 부록 형태로 제시.)

**Algorithmic Accountability 4 원칙** (FAT/ML 컨퍼런스 + 미국 ACM US Public Policy Council 2017):
1. **Transparency** (투명성): 알고리즘 작동 원리·입력·출력 공개
2. **Auditability** (감사 가능성): 제3자가 알고리즘 결과를 재현·검증 가능
3. **Explainability** (설명 가능성): 개별 결정의 이유를 정보주체에게 설명 (XAI — SHAP / LIME / Anchors)
4. **Accountability** (책임성): 잘못된 결정에 대한 책임 주체 명시 + 시정 절차

**Whistleblowing 경로**:
- 사내: 윤리위원회 → 감사실 → 이사회 (한국 *공익신고자보호법* 2011)
- 사외: 국민권익위원회(한국), Government Accountability Project(US), EU Whistleblower Directive(2019)
- 익명: GlobaLeaks, SecureDrop (Tor 기반 익명 신고 플랫폼)
- 미디어: 마지막 수단, 사전 사내 보고 시도 의무 (대부분 법에서 단계적 보호)

**Inclusive Design 4 원칙** (Microsoft Inclusive Design Toolkit):
1. **Recognize exclusion** (배제 인식): 누가 시스템에서 배제되는지 의도적 식별
2. **Solve for one, extend to many** (1인 해결 → 다수 확장): 극단 사례(장애·노인·언어 장벽) 해결책이 다수에게 이로움
3. **Learn from diversity** (다양성 학습): 사용자 다양성을 자원으로 활용
4. **WCAG 2.2 준수**: A / AA / AAA 등급 — Web Content Accessibility Guidelines

**위반 시 결과**:
- EU DSA (Article 25): VLOP(very large online platforms) 의 deceptive design 위반 → 글로벌 매출 6% 과징금
- EU AI Act (Article 5): Subliminal techniques → €35M 또는 매출 7%
- US FTC (2024 Click-to-Cancel rule): Hidden subscription 위반 → 행정 처분 + 환불 명령
- California Consumer Privacy Act (CCPA): Dark Pattern 으로 얻은 동의는 *무효* (Article 1798.140)
- 한국 *전자상거래법* 21조: 거짓·과장 표시 → 최대 1억원 과태료

**한국 사례**:
- 쿠팡 *로켓와우 자동결제* (2021) → 공정거래위원회 시정명령 + 과징금 (Hidden subscription)
- 카카오톡 *광고 비식별 표시* (2020) → Disguised ads 비판 → 카카오 자율 시정
- 한국 *다크패턴 자율규제 가이드라인* (2023, 공정위·KISO) — Brignull 분류를 한역하여 표준화

**관련 anchor**: [#acm-code-ethics-2018](#acm-code-ethics-2018) (Principle 1.3 honesty + 1.4 fairness 위반), [#eu-ai-act-2024](#eu-ai-act-2024) (Article 5 subliminal techniques 와 Dark Pattern 의 경계), [#gdpr-article-22](#gdpr-article-22) (Preselection 으로 얻은 동의의 GDPR 무효성), [security/privacy-engineering.md#privacy-by-design](../security/privacy-engineering.md#privacy-by-design) (Privacy by Design 7원칙과 Inclusive Design 의 정렬), [iso25010.md#usability](iso25010.md#usability) (Dark Pattern 은 ISO 25010 Usability 의 *user error protection* sub-특성 위반)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

```kotlin
// Korean comment: Dark Pattern 자동 감지 린트 — UI 코드에서 의심 패턴 식별
// Brignull 분류 중 Preselection / Confirmshaming / Hard to cancel 정적 분석
sealed class DarkPatternViolation(val pattern: String, val severity: Severity) {
    object Preselection : DarkPatternViolation("Preselection — checked by default without opt-in", Severity.HIGH)
    object Confirmshaming : DarkPatternViolation("Confirmshaming — guilt-tripping decline copy", Severity.MEDIUM)
    object HardToCancel : DarkPatternViolation("Hard to cancel — asymmetric signup vs cancel flow", Severity.HIGH)
}

object DarkPatternLinter {
    /**
     * 한국어 코멘트: Compose / SwiftUI / Jetpack 의 Checkbox·Toggle 기본값 검사.
     * GDPR Article 7(2) — 동의는 명시적·적극적·구별 가능 행동이어야 함.
     */
    fun checkPreselection(checkedByDefault: Boolean, label: String): DarkPatternViolation? {
        val isMarketingOrTracking = label.contains(Regex("(마케팅|광고|뉴스레터|마케팅 정보|개인정보 제3자)"))
        return if (checkedByDefault && isMarketingOrTracking) DarkPatternViolation.Preselection else null
    }

    /**
     * 한국어 코멘트: 거절 버튼 문구가 자기 비하인지 검사 — Brignull #2 Confirmshaming.
     */
    fun checkConfirmshaming(declineCopy: String): DarkPatternViolation? {
        val shamePatterns = listOf("No thanks, I", "I don't want to save", "절약하지 않을래요", "할인을 포기")
        return if (shamePatterns.any { declineCopy.contains(it, ignoreCase = true) }) {
            DarkPatternViolation.Confirmshaming
        } else null
    }
}
```

---

## 부록 A — 6 규범 통합 운영 체크리스트

신규 기능 출시 전 본 6 규범을 통합 검토하는 한 페이지 체크리스트.

| 단계 | 체크 | 근거 | 담당 |
|------|------|------|------|
| 1. 기획 | 공공 이익·취약 계층 영향 분석 | ACM 1.1 / IEEE 1 / SE 1 | Product / Architect |
| 2. 데이터 수집 | 동의·최소화·목적 명시 | GDPR Art 5 / ACM 1.6 | Privacy Engineer |
| 3. 모델 설계 | 편향 감사 + Fairness 지표 | ACM 1.4 / AI Act High-risk #2 | ML Engineer / Architect |
| 4. UI/UX | Dark Pattern 자동 린트 | Brignull / DSA Art 25 | Designer + Developer |
| 5. 자동 결정 | Human-in-the-loop + 이의제기 채널 | GDPR Art 22(3) / AI Act #6 | Architect |
| 6. 출시 전 | DPIA + FRIA 통합 | GDPR Art 35 / AI Act Art 26(4) | DPO + Legal |
| 7. 운영 | Audit log 6개월~10년 보존 | AI Act Art 12 | SRE |
| 8. 사고 시 | Whistleblowing 채널 + Incident report | SE 1.04 / AI Act Art 73 | Ethics Board |

---

## 부록 B — 한국 SE 윤리 규범 비교표

| 한국 규범 | 채택 | 근거 국제 규범 | 적용 |
|----------|------|--------------|------|
| 한국정보과학회 윤리 강령 | 1995 / 2007 개정 | ACM Code of Ethics | KIISE 회원 |
| 대한전자공학회 윤리강령 | 2009 | IEEE Code of Ethics | IEIE 회원 |
| 한국소프트웨어기술인협회 윤리강령 | 2010 | SECEPP 1999 | KOSEA 회원 |
| 개인정보보호법 제37조의2 (자동결정 권리) | 2023 시행 | GDPR Article 22 | 모든 개인정보처리자 |
| 인공지능기본법 | 2026 시행 예정 | EU AI Act 2024 | AI 시스템 운영자 |
| 다크패턴 자율규제 가이드라인 | 2023 | Brignull + EU DSA | 전자상거래 사업자 |
| 공익신고자보호법 | 2011 시행 | EU Whistleblower Directive | 모든 공·사기업 |

본 6 규범은 한국 법·규범으로 단계적 채택되고 있으며, **EU·한국·미국** 시장 동시 진출 시 *최고 기준* 인 EU 규제(GDPR + AI Act + DSA)를 따르면 한국·미국 요구를 대부분 충족한다.

---

## Cross-link Summary

- [iso25010.md#usability](iso25010.md#usability) — Dark Pattern 위반은 ISO 25010 Usability *user error protection* sub-특성 위반
- [iso25010.md#reliability](iso25010.md#reliability) — IEEE 1 (public welfare) 의 기술적 정렬
- [iso25010.md#maintainability](iso25010.md#maintainability) — SECEPP 3 (Product quality) 의 품질 지표화
- [security/privacy-engineering.md#purpose-binding](../security/privacy-engineering.md#purpose-binding) — GDPR Article 5(1)(b) purpose limitation 실무
- [security/privacy-engineering.md#dpia](../security/privacy-engineering.md#dpia) — GDPR Article 35 DPIA 운영 절차
- [security/privacy-engineering.md#privacy-by-design](../security/privacy-engineering.md#privacy-by-design) — Inclusive Design 과의 정렬
- [security/security-ai-model.md](../security/security-ai-model.md) — EU AI Act Article 15 (adversarial robustness) 기술적 구현
