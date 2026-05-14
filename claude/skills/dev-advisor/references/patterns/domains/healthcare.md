# Healthcare 상호운용 패턴 (Healthcare Interoperability Patterns)

의료 시스템의 정평 있는 10 패턴. FHIR R5 / HL7 v2 / SMART on FHIR / IHE 표준 기반. **PHI(Protected Health Information)** 처리·EHR(전자의무기록) 통합·임상 의사결정 지원 영역.

**원전·표준 참고**:
- HL7 FHIR R5 (2023) — https://hl7.org/fhir/R5/
- HL7 v2.x — 메시징 표준 (90% 의료기관 채택)
- SMART on FHIR (2014~) — http://hl7.org/fhir/smart-app-launch/
- HIPAA Privacy Rule (45 CFR §164.502-514) + Security Rule (§164.302-318)
- 21st Century Cures Act (US, 2016) — Information Blocking 금지
- IHE Profiles (Integrating the Healthcare Enterprise) — XDS / PIX / PDQ
- DICOM (Digital Imaging and Communications in Medicine, NEMA PS3)
- ONC USCDI v4 (US Core Data for Interoperability)

**핵심 비기능 요구**:
- **PHI 보호** — 18 identifier (이름·SSN·MRN·생년월일·...) 접근 제어 + 감사
- **임상 안전 (Patient Safety)** — 오진·약물 상호작용 차단 (CDS)
- **상호운용 (Interoperability)** — 다중 EHR (Epic/Cerner/Allscripts) 표준 메시지
- **컴플라이언스** — HIPAA / HITECH (US) / GDPR Art 9 (EU sensitive data) / 한국 의료법

**관련 카탈로그**:
- [`../api-design.md`](../api-design.md) — FHIR 는 REST + Resource-Oriented 의 의료 도메인 구현
- [`../../security/security-data-protection.md`](../../security/security-data-protection.md) — De-identification, FPE
- [`../../security/compliance.md`](../../security/compliance.md) — HIPAA
- [`../../security/security-authn.md`](../../security/security-authn.md) — OAuth2 + PKCE (SMART)

---

## 1. FHIR R5 Resource Model — FHIR R5 리소스 모델

<a id="fhir-r5-resource"></a>

**목적**: 의료 데이터를 **REST 자원(Resource)** 단위로 표현하여 EHR·EMR·앱 간 상호운용 가능한 표준 데이터 모델을 제공합니다. HL7 FHIR R5(2023) 가 최신 정식 릴리스.

**메커니즘**:
- 약 150 종 리소스 타입 (`Patient` / `Practitioner` / `Observation` / `MedicationRequest` / `Encounter` / `Condition` / `AllergyIntolerance` / `DiagnosticReport` / `Procedure` / `Immunization` / ...)
- 직렬화: JSON (권장) · XML · Turtle
- REST API: `GET /Patient/123`, `POST /Observation`, `PUT /Patient/123`, `DELETE`, `GET /Patient?name=Kim&birthdate=1990-01-01`
- Search 표준: `_id`, `_lastUpdated`, `_include`, `_revinclude`, `_count`, modifier (`:exact`, `:contains`)
- Bundle — 트랜잭션·검색 결과 묶음
- Profile / StructureDefinition — 자국·기관 특화 제약 (예: US Core, KR Core)
- Extension — 표준 외 필드 (네임스페이스화된 URL)
- Reference — 다른 리소스 참조 (`{"reference":"Patient/123"}`)
- Terminology — LOINC (검사) / SNOMED CT (임상 용어) / RxNorm (약물) / ICD-10 (진단)

**장점**:
- REST·JSON 친화 → 모바일/웹 앱과 자연스러운 통합
- versioned read (`/Patient/123/_history/2`) — 변경 추적 내장
- 21st Century Cures Act + ONC 규제로 미국 EHR 의무 지원 (2022~)
- 한국도 FHIR R5 기반 의료 표준 채택 진행 중 (보건복지부 2023~)

**단점·주의**:
- 리소스 수 많고 spec 방대 (수천 페이지) — 학습 비용 큼
- HL7 v2 레거시 시스템과 매핑 필요 (FHIR Mapping Language)
- Implementation Guide (US Core / KR Core 등) 별 profile 충돌 가능
- 검색 파라미터 조합이 강력해서 N+1 query 폭주 위험

**컴플라이언스 매핑**:
- HIPAA §164.312(a)(1) — 접근 제어: FHIR consent + SMART scope 로 구현
- 21st Century Cures Act §4004 — Information Blocking 금지: USCDI v4 API 의무
- ISO 13606 EHRcom — FHIR 와 호환

**FHIR Patient Resource JSON 예제**:
```json
{
  "resourceType": "Patient",
  "id": "example-001",
  "meta": {
    "versionId": "2",
    "lastUpdated": "2026-05-14T09:30:00+09:00",
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
    ]
  },
  "identifier": [
    {
      "use": "official",
      "system": "urn:oid:1.2.410.200119.4",
      "value": "MRN-0001234"
    }
  ],
  "active": true,
  "name": [
    { "use": "official", "family": "Kim", "given": ["Min-jun"] }
  ],
  "telecom": [
    { "system": "phone", "value": "+82-10-1234-5678", "use": "mobile" }
  ],
  "gender": "male",
  "birthDate": "1990-01-15",
  "address": [
    { "city": "Seoul", "country": "KR" }
  ],
  "generalPractitioner": [
    { "reference": "Practitioner/dr-lee" }
  ]
}
```

**FHIR Observation (검사 결과) 예제 — 혈압**:
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [
    {
      "coding": [
        { "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs", "display": "Vital Signs" }
      ]
    }
  ],
  "code": {
    "coding": [
      { "system": "http://loinc.org", "code": "85354-9",
        "display": "Blood pressure panel" }
    ]
  },
  "subject": { "reference": "Patient/example-001" },
  "effectiveDateTime": "2026-05-14T08:15:00+09:00",
  "component": [
    {
      "code": {
        "coding": [{ "system": "http://loinc.org", "code": "8480-6",
                     "display": "Systolic blood pressure" }]
      },
      "valueQuantity": { "value": 128, "unit": "mmHg",
                         "system": "http://unitsofmeasure.org", "code": "mm[Hg]" }
    },
    {
      "code": {
        "coding": [{ "system": "http://loinc.org", "code": "8462-4",
                     "display": "Diastolic blood pressure" }]
      },
      "valueQuantity": { "value": 82, "unit": "mmHg",
                         "system": "http://unitsofmeasure.org", "code": "mm[Hg]" }
    }
  ]
}
```

**Kotlin 클라이언트 예제 (HAPI FHIR)**:
```kotlin
// HAPI FHIR client — ca.uhn.hapi.fhir:hapi-fhir-client
val ctx = FhirContext.forR5()
val client = ctx.newRestfulGenericClient("https://fhir.example.org/r5")

// READ
val patient = client.read()
    .resource(Patient::class.java)
    .withId("example-001")
    .execute()

// SEARCH — 이름 + 생년월일
val bundle: Bundle = client.search<Bundle>()
    .forResource(Patient::class.java)
    .where(Patient.NAME.matches().value("Kim"))
    .and(Patient.BIRTHDATE.exactly().day("1990-01-15"))
    .returnBundle(Bundle::class.java)
    .execute()

// CREATE Observation (혈압)
val obs = Observation().apply {
    status = Observation.ObservationStatus.FINAL
    subject = Reference("Patient/example-001")
    code = CodeableConcept().addCoding(
        Coding("http://loinc.org", "85354-9", "Blood pressure panel"))
}
client.create().resource(obs).execute()
```

**관련 패턴**: [SMART on FHIR](#smart-on-fhir), [CDS Hooks](#cds-hooks), [Consent Management](#consent-management-fhir), [`../api-design.md` REST Resource-Oriented](../api-design.md)

---

## 2. HL7 v2 Messaging — HL7 v2 메시징

<a id="hl7-v2-messaging"></a>

**목적**: 1989 년 표준화된 **pipe-delimited(`|`) 메시지 포맷**으로 EHR·LIS·RIS·PACS 간 환자 입퇴원·검사·처방을 비동기 전송합니다. 전 세계 의료기관 90% 이상이 운영 중인 사실상의 표준.

**메커니즘**:
- 메시지 단위: **MSH** (Header) + 트리거 이벤트별 세그먼트
- 세그먼트 구분자 — `\r` (CR), 필드 `|`, 컴포넌트 `^`, 반복 `~`, escape `\`, 서브컴포넌트 `&`
- 트리거 이벤트:
  - **ADT** (Admit/Discharge/Transfer) — `ADT^A01` (입원), `A03` (퇴원), `A04` (외래등록), `A08` (정보수정)
  - **ORM** (Order Entry) — `ORM^O01` (검사·처방 오더)
  - **ORU** (Observation Result) — `ORU^R01` (검사 결과)
  - **SIU** (Scheduling) — `SIU^S12` (예약)
  - **DFT** (Detailed Financial Transaction) — 청구
- 전송: TCP/IP + **MLLP** (Minimal Lower Layer Protocol, `<VT>...<FS><CR>` framing)
- 세그먼트 종류:
  - `MSH` — Message Header (sender, receiver, type, control id)
  - `PID` — Patient Identification
  - `PV1` — Patient Visit
  - `OBR` — Observation Request
  - `OBX` — Observation Result
  - `DG1` — Diagnosis
  - `RXE`/`RXR` — Pharmacy Encoded Order
- ACK/NACK 패턴 — 응답 메시지 `MSH...MSA|AA|<ctrlId>|`

**장점**:
- 의료기관 인프라 전반 침투 — 모든 주요 EHR (Epic / Cerner / 메디포커스 / EzCaretech) 지원
- TCP 위 단순 텍스트 — 방화벽·VPN 통과 용이
- 30년 운영 안정성 — 메시지 큐·라우터(Mirth Connect, Rhapsody) 생태계 성숙

**단점·주의**:
- 필드 의미 모호 (벤더별 해석 차이) — 통합 시 항상 매핑 명세 필요
- 한글·UTF-8 처리 — `MSH-18` (character set) 명시 필수 (`UNICODE UTF-8` / `ASCII`)
- 텍스트 파싱 오류 취약 — `|^` 가 데이터에 포함되면 escape 필수
- REST/JSON 친화 아님 → 신규 시스템은 FHIR R5 권장
- 메시지 손실 방지 — Mirth Connect 등 큐 + retry 필수

**컴플라이언스 매핑**:
- HIPAA §164.312(e)(1) — 전송 보안: MLLP over TLS (MLLPS) 권장
- 한국 의료법 시행규칙 §16 — 진료기록 전자 송수신 표준

**HL7 v2 ADT^A01 메시지 예제 (입원)**:
```
MSH|^~\&|HIS|HOSP_A|EHR|HOSP_B|20260514093000||ADT^A01^ADT_A01|MSG00001|P|2.5.1|||AL|NE|KOR|UNICODE UTF-8
EVN|A01|20260514093000|||DOCTOR^LEE^SOO-JIN
PID|1||MRN-0001234^^^HOSP_A^MR||KIM^MIN-JUN^^^^^L||19900115|M|||SEOUL^^^^06236^KOR||010-1234-5678|||||||||||||||||N
NK1|1|KIM^EUN-HEE|SPO|SEOUL||010-9876-5432
PV1|1|I|ICU01^301^A^HOSP_A||||DOC-001^LEE^SOO-JIN|||CAR||||1|||DOC-001^LEE^SOO-JIN|INP|VIP|||||||||||||||||||||HOSP_A||ADM|||20260514093000
DG1|1|I10|I21.4^Acute subendocardial myocardial infarction^I10|||A
```

세그먼트 해석:
- `MSH`: HIS→EHR, message ID `MSG00001`, HL7 v2.5.1, UTF-8
- `EVN`: A01 이벤트, 발생시각 2026-05-14 09:30:00, 담당의 Lee Soo-jin
- `PID`: MRN-0001234, 환자 Kim Min-jun, 남성, 1990-01-15
- `PV1`: 입원(`I`), 병실 ICU01-301-A, 주치의 DOC-001
- `DG1`: 진단 ICD-10 `I21.4` (급성 심근경색)

**ACK 응답 예제**:
```
MSH|^~\&|EHR|HOSP_B|HIS|HOSP_A|20260514093001||ACK^A01|MSG00002|P|2.5.1
MSA|AA|MSG00001|Message accepted
```
- `MSA|AA` — Application Accept (정상 처리)
- `MSA|AE` — Application Error
- `MSA|AR` — Application Reject

**Kotlin 파서 예제 (HAPI HL7 v2)**:
```kotlin
// ca.uhn.hapi:hapi-base + hapi-structures-v251
val context = DefaultHapiContext()
val parser: PipeParser = context.pipeParser

fun handleAdt(rawMessage: String) {
    val msg = parser.parse(rawMessage) as ADT_A01
    val pid = msg.pid
    val mrn = pid.getPatientIdentifierList(0).idNumber.value
    val name = pid.getPatientName(0).familyName.surname.value +
               " " + pid.getPatientName(0).givenName.value
    val birthDate = pid.dateTimeOfBirth.time.value  // yyyyMMddHHmmss

    val pv1 = msg.pV1
    val admitClass = pv1.patientClass.value   // I=Inpatient, O=Outpatient

    // FHIR Patient 로 변환하여 내부 시스템에 저장
    fhirGateway.upsertPatient(toFhirPatient(mrn, name, birthDate))

    // ACK 응답
    val ack = msg.generateACK()
    mllpClient.send(parser.encode(ack))
}
```

**관련 패턴**: [FHIR R5 Resource](#fhir-r5-resource), [IHE Profiles](#ihe-profiles), [`../integration.md` Adapter](../integration.md)

---

## 3. SMART on FHIR / OAuth2 Launch — SMART on FHIR 인증 위임

<a id="smart-on-fhir"></a>

**목적**: 환자·의료진 앱이 EHR 의 FHIR API 에 접근할 때 **OAuth2 + PKCE + OpenID Connect** 위에 의료 도메인 scope·launch context 를 정의한 프로파일입니다.

**메커니즘**:
- 두 가지 launch 모드:
  - **EHR Launch** — EHR 안에서 앱을 띄울 때 (의사가 진료 중 임상 앱 실행) — EHR 이 `iss` + `launch` token 전달
  - **Standalone Launch** — 환자가 모바일 앱에서 직접 시작 (예: Apple Health Records)
- OAuth2 Authorization Code + **PKCE 필수** (S256)
- 표준 scope:
  - `patient/Observation.read` — 현재 환자의 검사 결과 읽기
  - `user/Patient.read` — 사용자(의사) 권한 범위 환자
  - `system/*.read` — Backend Services (서버간)
  - `launch/patient` — launch context 에서 환자 ID 받기
  - `openid fhirUser` — OIDC 신원
- Discovery — `.well-known/smart-configuration` (authorization_endpoint, token_endpoint, capabilities)
- Token response 에 launch context 포함:
  ```json
  { "access_token": "...", "patient": "Patient/123",
    "encounter": "Encounter/456", "expires_in": 3600 }
  ```
- Backend Services (시스템간) — JWT client assertion (`client_credentials` + signed JWT, RS384)

**장점**:
- OAuth2 표준 위 → 라이브러리 재사용 (AppAuth-Android / iOS, Authlib)
- Epic / Cerner / Allscripts / Athena 모두 SMART on FHIR 지원 → 한 번 구현으로 다중 EHR 연동
- launch context 로 "현재 환자" 자동 주입 → UX 단절 없음
- HIPAA 접근 제어와 자연스러운 매핑

**단점·주의**:
- PKCE 미적용 = 보안 인증 실패 (mobile 앱 client_secret 보관 불가)
- EHR 마다 scope 미세 차이 존재 — 통합 테스트 필수
- refresh_token 처리 — 30분~1시간 access_token 만료 빈번
- `loopback redirect_uri` (모바일) 의도된 흐름 — 임의 호스트 막혀있음

**컴플라이언스 매핑**:
- HIPAA §164.312(d) — 사용자 인증
- 21st Century Cures Act ONC §170.315(g)(10) — SMART on FHIR 의무 (US EHR 인증)

**.well-known/smart-configuration 예제**:
```json
{
  "issuer": "https://fhir.example.org/r5",
  "authorization_endpoint": "https://auth.example.org/oauth2/authorize",
  "token_endpoint": "https://auth.example.org/oauth2/token",
  "code_challenge_methods_supported": ["S256"],
  "grant_types_supported": ["authorization_code", "client_credentials"],
  "scopes_supported": [
    "openid", "fhirUser",
    "launch", "launch/patient",
    "patient/*.read", "user/*.read", "system/*.read",
    "offline_access"
  ],
  "response_types_supported": ["code"],
  "capabilities": [
    "launch-ehr", "launch-standalone",
    "client-public", "client-confidential-symmetric",
    "sso-openid-connect",
    "context-passthrough-banner",
    "context-ehr-patient", "context-ehr-encounter",
    "permission-patient", "permission-user", "permission-offline"
  ]
}
```

**Authorization Request 예제 (Standalone Launch + PKCE)**:
```
GET /oauth2/authorize?
    response_type=code
    &client_id=my-app
    &redirect_uri=https%3A%2F%2Fapp.example.org%2Fcb
    &scope=launch%2Fpatient%20patient%2FObservation.read%20openid%20fhirUser%20offline_access
    &state=abc123
    &aud=https%3A%2F%2Ffhir.example.org%2Fr5
    &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
    &code_challenge_method=S256
```

**Kotlin 모바일 클라이언트 (AppAuth) 예제**:
```kotlin
// net.openid:appauth
val authConfig = AuthorizationServiceConfiguration(
    Uri.parse("https://auth.example.org/oauth2/authorize"),
    Uri.parse("https://auth.example.org/oauth2/token"),
)
val req = AuthorizationRequest.Builder(
    authConfig,
    /* clientId = */ "my-app",
    ResponseTypeValues.CODE,
    Uri.parse("com.example.myapp:/oauth2redirect"),
).setScopes(
    "launch/patient",
    "patient/Observation.read",
    "openid", "fhirUser", "offline_access",
).setAdditionalParameters(
    mapOf("aud" to "https://fhir.example.org/r5"),
).build()  // PKCE 자동 적용 (S256)

val authService = AuthorizationService(ctx)
authService.performAuthorizationRequest(
    req,
    PendingIntent.getActivity(ctx, 0, Intent(ctx, CallbackActivity::class.java),
        PendingIntent.FLAG_MUTABLE),
)

// 토큰 응답 후 launch context 추출
fun onTokenResponse(resp: TokenResponse) {
    val patientId = resp.additionalParameters["patient"]    // Patient/123
    val encounterId = resp.additionalParameters["encounter"] // Encounter/456
    fhirSession.bind(resp.accessToken!!, patientId)
}
```

**Backend Services (system) JWT client assertion 예제**:
```json
// JWT header
{ "alg": "RS384", "typ": "JWT", "kid": "key-2026" }
// JWT payload
{
  "iss": "backend-app",
  "sub": "backend-app",
  "aud": "https://auth.example.org/oauth2/token",
  "exp": 1715645400,
  "jti": "550e8400-e29b-41d4-a716-446655440000"
}
```

**관련 패턴**: [FHIR R5 Resource](#fhir-r5-resource), [CDS Hooks](#cds-hooks), [`../../security/security-authn.md` OAuth2 + PKCE](../../security/security-authn.md)

---

## 4. CDS Hooks (Clinical Decision Support) — 임상 의사결정 지원 훅

<a id="cds-hooks"></a>

**목적**: EHR 이 진료 워크플로의 특정 시점(`patient-view`, `medication-prescribe`)에 외부 CDS 서비스를 동기 호출하고, 카드(card) 형태로 권고·경고를 응답받아 화면에 표시합니다. SMART 의 자매 표준 (Boston Children's Hospital + ONC).

**메커니즘**:
- Hook 시점:
  - `patient-view` — 환자 차트 열람
  - `order-sign` — 오더 서명 직전
  - `order-select` — 오더 선택 중
  - `medication-prescribe` (deprecated → `order-sign`)
  - `appointment-book` — 예약 직전
  - `encounter-start` / `encounter-discharge`
- Discovery — `GET /cds-services` → 지원 hook 목록 + prefetch template
- Invocation — `POST /cds-services/{id}` (body: context + prefetch)
- 응답 — `cards[]` (정보·권고·심각 경고) + `links[]` (SMART 앱 launch URL)
- **1초 budget 권장** — EHR UI 차단 방지 (Epic 은 5초 timeout)
- prefetch — EHR 이 자주 쓰는 FHIR resource 를 미리 동봉 (왕복 절감)
- FHIR Auth — Bearer token (CDS 가 EHR 의 FHIR API 호출 시)

**장점**:
- EHR 코드 수정 없이 정책·룰 외부 서비스로 추가 (drug-drug interaction / pneumonia bundle / sepsis alert)
- 단일 명세로 여러 EHR 에 동일 CDS 배포
- 카드 타입(`info` / `warning` / `critical`) 으로 alert fatigue 완화 가능

**단점·주의**:
- **Alert fatigue** — 카드 남발 시 의료진이 모두 무시 (임상 안전 역효과)
- 1초 budget 못 맞추면 EHR 이 CDS 결과 표시 안 함
- prefetch 누락 시 CDS 가 FHIR API 왕복 → 지연 폭증
- 동일 hook 다중 CDS 호출 → 카드 충돌·중복 권고 (EHR 측 정책 필요)

**컴플라이언스 매핑**:
- HIPAA §164.308(a)(1)(ii) — Risk analysis (CDS 가 PHI 수신)
- ONC §170.315(b)(11) — Decision support intervention

**Discovery 응답 예제**:
```json
{
  "services": [
    {
      "hook": "medication-prescribe",
      "title": "Drug-Drug Interaction Checker",
      "description": "Warns about clinically significant interactions",
      "id": "ddi-check",
      "prefetch": {
        "patient": "Patient/{{context.patientId}}",
        "medications": "MedicationRequest?patient={{context.patientId}}&status=active"
      }
    },
    {
      "hook": "patient-view",
      "title": "Sepsis Early Warning",
      "id": "sepsis-ews",
      "prefetch": {
        "observations": "Observation?patient={{context.patientId}}&category=vital-signs&_count=20"
      }
    }
  ]
}
```

**Invocation 요청 (EHR → CDS)**:
```json
{
  "hook": "medication-prescribe",
  "hookInstance": "d1577c69-dfbe-44ad-ba6d-3e05e953b2ea",
  "fhirServer": "https://fhir.example.org/r5",
  "fhirAuthorization": {
    "access_token": "eyJ...", "token_type": "Bearer",
    "expires_in": 3600, "scope": "patient/*.read",
    "subject": "cds-service-1"
  },
  "context": {
    "userId": "Practitioner/dr-lee",
    "patientId": "Patient/example-001",
    "encounterId": "Encounter/enc-789",
    "medications": {
      "resourceType": "Bundle",
      "entry": [{
        "resource": {
          "resourceType": "MedicationRequest",
          "intent": "order",
          "status": "draft",
          "medicationCodeableConcept": {
            "coding": [{ "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                         "code": "855332", "display": "Warfarin Sodium 5 MG" }]
          },
          "subject": { "reference": "Patient/example-001" }
        }
      }]
    }
  },
  "prefetch": {
    "patient": { "resourceType": "Patient", "id": "example-001", "...": "..." },
    "medications": { "resourceType": "Bundle", "...": "..." }
  }
}
```

**CDS 응답 — Warning Card**:
```json
{
  "cards": [
    {
      "summary": "Warfarin + Aspirin: bleeding risk",
      "indicator": "warning",
      "detail": "Co-administration increases bleeding risk by 2.4x (NEJM 2007). Consider PPI or reduce aspirin dose.",
      "source": {
        "label": "DDI Knowledge Base v3.2",
        "url": "https://ddi.example.org/warfarin-aspirin"
      },
      "suggestions": [
        {
          "label": "Replace with apixaban",
          "uuid": "sugg-001",
          "actions": [
            {
              "type": "delete",
              "description": "Remove warfarin order",
              "resource": { "resourceType": "MedicationRequest", "id": "draft-1" }
            }
          ]
        }
      ],
      "selectionBehavior": "any",
      "overrideReasons": [
        { "code": "patient-tolerates", "display": "Patient previously tolerated" }
      ]
    }
  ]
}
```

**Kotlin CDS Service 예제 (Ktor)**:
```kotlin
@Serializable data class CdsRequest(
    val hook: String, val hookInstance: String,
    val context: JsonObject, val prefetch: JsonObject? = null,
)

fun Route.cdsServices(checker: DdiChecker) {
    post("/cds-services/ddi-check") {
        val req = call.receive<CdsRequest>()
        val patientId = req.context["patientId"]!!.jsonPrimitive.content
        val medBundle = req.prefetch?.get("medications")?.let { fhirJson.decodeFromJsonElement<Bundle>(it) }
            ?: fhir.search<Bundle>("MedicationRequest?patient=$patientId&status=active")

        val newMed = extractDraftMedication(req.context)
        val interactions = checker.check(newMed, medBundle.entries)  // 200ms budget

        val cards = interactions.map { ddi ->
            Card(
                summary = "${ddi.drugA} + ${ddi.drugB}: ${ddi.risk}",
                indicator = if (ddi.severity == Severity.HIGH) "warning" else "info",
                detail = ddi.evidence,
                source = Source(label = "DDI KB v3.2"),
            )
        }
        call.respond(CdsResponse(cards = cards))
    }
}
```

**관련 패턴**: [FHIR R5 Resource](#fhir-r5-resource), [SMART on FHIR](#smart-on-fhir), [`../reliability.md` Timeout/Bulkhead](../reliability.md)

---

## 5. Consent Management (FHIR Consent) — 환자 동의 관리

<a id="consent-management-fhir"></a>

**목적**: 환자가 자신의 PHI 가 누구에게·어떤 목적으로·언제까지 공개될지 명시한 **법적 효력 동의(consent)** 를 구조화 데이터로 관리하고, 모든 데이터 접근 시점에 검증합니다.

**메커니즘**:
- FHIR `Consent` 리소스 — 환자 동의 표현 (legal basis, scope, policy, provision)
- 동의 구조:
  - **scope** — `patient-privacy` (privacy consent) / `treatment` (치료) / `research` (연구)
  - **category** — 동의 범주 (HIE / DNR / Advance Directive)
  - **policy** — 적용 법령·기관 정책 URI
  - **provision** — 허용/금지 규칙 (`permit` / `deny` + actor + action + period + dataPeriod)
- Opt-in (KR / EU 기본) vs Opt-out (US 일부 주)
- Granular scope — "심리상담 기록 제외", "특정 진료과만", "AIDS·약물중독 정보 제외 (42 CFR Part 2)"
- 시간 제약 — `provision.period` (동의 유효 기간)
- 검증 시점 — FHIR Read/Search 시점에 Consent Decision Service 가 평가 (PEP/PDP 분리)
- 철회 — `Consent.status = inactive` (versioned, audit log 남김)

**장점**:
- 환자 주권 보장 — 본인 정보 흐름 통제 가능 (GDPR Art. 7)
- 법적 증거 — `Consent.attester` 에 환자 서명·날짜 보존
- 세분화된 제어 — 진료 부서·정보 카테고리·기간별 분리
- Information Blocking 면제 사유 — "환자 동의 거부" 명시 가능

**단점·주의**:
- granular consent 평가 = 매 요청마다 정책 엔진 호출 → 캐시·성능 설계 필수
- 응급 상황(`break-the-glass`) 우회 절차 필요 — 일반적으로 사후 감사
- 미성년·후견인 동의 — `Consent.performer` (legal guardian) 별도 처리
- 동의 철회 후 이미 공유된 데이터 회수 불가 — 향후 공유만 차단

**컴플라이언스 매핑**:
- HIPAA §164.508 — Authorization for uses and disclosures
- GDPR Art. 7 — Conditions for consent
- 한국 개인정보보호법 §15·§17 — 수집·이용·제공 동의
- 42 CFR Part 2 — 약물·알코올 치료 기록 특별 보호

**FHIR Consent 예제 (연구 데이터 공유 동의)**:
```json
{
  "resourceType": "Consent",
  "status": "active",
  "scope": {
    "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                 "code": "research", "display": "Research" }]
  },
  "category": [
    { "coding": [{ "system": "http://loinc.org",
                   "code": "57016-8", "display": "Privacy policy acknowledgment" }] }
  ],
  "patient": { "reference": "Patient/example-001" },
  "dateTime": "2026-05-14T09:00:00+09:00",
  "performer": [{ "reference": "Patient/example-001" }],
  "policyRule": {
    "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/consentpolicycodes",
                 "code": "cric", "display": "Common Rule Informed Consent" }]
  },
  "provision": {
    "type": "permit",
    "period": {
      "start": "2026-05-14",
      "end": "2031-05-14"
    },
    "actor": [
      {
        "role": { "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
          "code": "CST", "display": "Custodian" }] },
        "reference": { "reference": "Organization/research-lab-42" }
      }
    ],
    "action": [
      { "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/consentaction",
                     "code": "disclose" }] }
    ],
    "purpose": [
      { "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
        "code": "HRESCH", "display": "Healthcare Research" }
    ],
    "provision": [
      {
        "type": "deny",
        "code": [{ "coding": [{ "system": "http://hl7.org/fhir/v3/ActCode",
                                "code": "BH", "display": "Behavioral Health" }] }]
      }
    ]
  }
}
```

해석:
- `provision.type = permit` — 기본 허용
- 5년간 (2026-05-14 ~ 2031-05-14)
- Research Lab 42 가 환자 데이터 disclose 가능
- 단, 정신건강 정보 (`BH`) 는 **deny** (nested provision)

**Kotlin Consent Decision Engine 예제**:
```kotlin
class ConsentEngine(private val fhir: FhirClient) {
    /**
     * 환자 PHI 접근 가부 결정.
     * @return Decision.PERMIT / DENY / NOT_APPLICABLE
     */
    fun check(req: AccessRequest): Decision {
        val consents = fhir.search<Bundle>(
            "Consent?patient=${req.patientId}&status=active"
        ).entries.map { it.resource as Consent }

        if (consents.isEmpty()) {
            // Opt-in 정책: 동의 없으면 거부
            return Decision.DENY(reason = "no-consent")
        }

        for (consent in consents) {
            val provision = consent.provision ?: continue
            if (!matchesActor(provision, req.actorId)) continue
            if (!matchesAction(provision, req.action)) continue
            if (!matchesPeriod(provision, req.timestamp)) continue
            if (!matchesPurpose(provision, req.purpose)) continue

            // Nested deny 확인 (e.g. Behavioral Health 제외)
            if (provision.provision.any { it.type == ConsentProvisionType.DENY
                    && categoryMatches(it, req.dataCategory) }) {
                return Decision.DENY(reason = "category-excluded")
            }
            return if (provision.type == ConsentProvisionType.PERMIT)
                Decision.PERMIT else Decision.DENY(reason = "explicit-deny")
        }
        return Decision.DENY(reason = "no-matching-provision")
    }
}

// PEP — FHIR endpoint 에서 모든 read 전에 호출
suspend fun ApplicationCall.requireConsent(req: AccessRequest) {
    when (val d = consentEngine.check(req)) {
        is Decision.PERMIT -> { /* proceed */ }
        is Decision.DENY -> {
            auditLog.record(req, "DENY", d.reason)
            respond(HttpStatusCode.Forbidden, OperationOutcome.error("Consent: ${d.reason}"))
        }
    }
}
```

**관련 패턴**: [PHI Audit Trail](#phi-audit-trail), [FHIR R5 Resource](#fhir-r5-resource), [`../../security/security-authz.md` PBAC](../../security/security-authz.md)

---

## 6. PHI Audit Trail (HIPAA §164.312) — PHI 접근 감사 추적

<a id="phi-audit-trail"></a>

**목적**: PHI 가 **언제·누가·무엇을·어디서·어떻게** 접근했는지 위변조 불가능한 로그로 보존하여 HIPAA Security Rule 의 audit control 의무를 충족합니다.

**메커니즘**:
- 기록 항목 (FHIR `AuditEvent` resource 또는 ATNA — IHE Audit Trail and Node Authentication):
  - **who** — actor (Practitioner / Patient / System) + `Device`
  - **what** — accessed resource + action (`R` read / `C` create / `U` update / `D` delete / `E` execute)
  - **when** — `recorded` timestamp (UTC, ms 정밀도)
  - **where** — source IP / device ID / facility
  - **why** — purpose of use (`TREAT` / `PAYMENT` / `OPERATIONS` / `RESEARCH`)
  - **outcome** — `0` success / `4` minor failure / `8` serious / `12` major
- 위변조 방지:
  - **Append-only** — 수정·삭제 불가
  - 해시 체인 (block N+1 의 hash = SHA-256(block N || data N+1))
  - 외부 WORM 스토리지 (S3 Object Lock, Azure Immutable Blob, AWS QLDB)
  - 정기 백업 + offsite
- 보존 기간:
  - HIPAA — **6년 이상** (최종 변경일 기준)
  - 한국 의료법 시행규칙 §15 — 진료기록 10년 / 진단서 3년
- 분리된 로그 시스템 — 운영 DB 와 별도 (운영자도 로그 수정 불가)
- 실시간 모니터링 — 같은 환자에게 비정상 다중 접근 / 비번 외 시간 접근 alert

**장점**:
- HIPAA 감사 + breach investigation 핵심 증거
- Snooping (직원이 유명인·지인 차트 무단 열람) 탐지 가능
- Information Blocking 미발생 증명 자료
- 환자 본인 열람 요청 시 access log 제출

**단점·주의**:
- 모든 read 까지 기록 — 데이터량 폭증 (대형 EHR 일 10GB+) → 저장·인덱스 설계 부담
- 검색 성능 — patient_id 인덱스 + 시간 파티셔닝 필수
- "응급 break-the-glass" 절차 — 사후 review 워크플로 별도 필요
- 로그 자체가 PHI 포함 → 로그도 암호화·접근통제 대상

**컴플라이언스 매핑**:
- HIPAA Security Rule §164.312(b) — Audit controls
- HIPAA Privacy Rule §164.528 — Accounting of disclosures (환자 요청 시 6년)
- ONC §170.315(d)(2) — Auditable events and tamper-resistance
- 한국 개인정보보호법 §29 — 안전성 확보조치 (접속기록 1년 보존)
- ISO 27001 A.12.4 — Logging and monitoring

**FHIR AuditEvent 예제 (PHI 조회)**:
```json
{
  "resourceType": "AuditEvent",
  "type": {
    "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
    "code": "rest", "display": "RESTful Operation"
  },
  "subtype": [
    { "system": "http://hl7.org/fhir/restful-interaction",
      "code": "read", "display": "read" }
  ],
  "action": "R",
  "recorded": "2026-05-14T10:23:45.123+09:00",
  "outcome": "0",
  "purposeOfEvent": [
    { "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                   "code": "TREAT", "display": "Treatment" }] }
  ],
  "agent": [
    {
      "type": { "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                             "code": "AUT" }] },
      "who": { "reference": "Practitioner/dr-lee" },
      "requestor": true,
      "network": { "address": "10.42.7.103", "type": "2" },
      "purposeOfUse": [
        { "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                       "code": "TREAT" }] }
      ]
    },
    {
      "type": { "coding": [{ "code": "DEV", "display": "Device" }] },
      "who": { "identifier": { "value": "EHR-WORKSTATION-12" } },
      "requestor": false
    }
  ],
  "source": {
    "site": "Hospital A — Cardiology Ward",
    "observer": { "reference": "Device/audit-collector-1" },
    "type": [{ "code": "4", "display": "Application Server" }]
  },
  "entity": [
    {
      "what": { "reference": "Patient/example-001" },
      "type": { "system": "http://hl7.org/fhir/resource-types",
                "code": "Patient" },
      "role": { "code": "1", "display": "Patient" }
    }
  ]
}
```

**Kotlin 해시 체인 audit logger 예제**:
```kotlin
class TamperEvidentAuditLog(private val store: AppendOnlyStore) {

    /** 직전 블록의 hash 를 chaining 하여 위변조 시 후속 블록 모두 hash 불일치. */
    suspend fun append(event: AuditEvent): String {
        val prev = store.tail()?.hash ?: GENESIS_HASH
        val payload = canonicalJson(event).toByteArray(Charsets.UTF_8)
        val seq = (store.tail()?.seq ?: 0L) + 1L

        val body = "$prev|$seq|${event.recorded}|${sha256(payload).toHex()}"
        val hash = sha256(body.toByteArray()).toHex()

        val block = AuditBlock(seq, event.recorded, prev, hash, payload)
        store.append(block)               // S3 Object Lock / QLDB
        return hash
    }

    /** 주기적 무결성 검증 — 어느 블록 하나라도 변조되면 후속 hash 모두 불일치. */
    suspend fun verifyChain(): VerifyResult {
        var prev = GENESIS_HASH
        store.scan { block ->
            val expected = sha256(
                "$prev|${block.seq}|${block.recorded}|${sha256(block.payload).toHex()}"
                    .toByteArray()
            ).toHex()
            if (expected != block.hash) {
                return VerifyResult.Tampered(at = block.seq)
            }
            prev = block.hash
        }
        return VerifyResult.Ok
    }
}

// FHIR endpoint interceptor — 모든 read/write 후 호출
suspend fun ApplicationCall.recordAudit(req: AccessRequest, outcome: String) {
    auditLog.append(AuditEvent(
        action = req.action,
        recorded = Instant.now(),
        agent = listOf(Agent(who = "Practitioner/${req.userId}", network = request.origin.remoteHost)),
        entity = listOf(Entity(what = "${req.resourceType}/${req.resourceId}")),
        outcome = outcome,
        purposeOfEvent = listOf(req.purpose),
    ))
}
```

**관련 패턴**: [Consent Management](#consent-management-fhir), [De-identification](#de-identification), [`../../security/security-detect-respond.md` SIEM](../../security/security-detect-respond.md)

---

## 7. De-identification / Safe Harbor — PHI 비식별화

<a id="de-identification"></a>

**목적**: PHI 가 포함된 데이터를 연구·분석·통계 목적으로 활용하기 위해 HIPAA **Safe Harbor 18 identifier** 를 제거하거나 **Expert Determination** 방법으로 재식별 위험을 정량적으로 ≤ small 수준까지 낮춥니다.

**메커니즘**:
- 두 가지 비식별 방법 (HIPAA §164.514):
  - **Safe Harbor (§164.514(b)(2))** — 정해진 18 identifier 모두 제거 + 재식별 인지 없음 attestation
  - **Expert Determination (§164.514(b)(1))** — 통계학자가 재식별 위험 "very small" 입증
- **Safe Harbor 18 identifier**:
  1. 이름, 2. 지역(주 이하 — ZIP 첫 3자리는 인구 20,000 초과 시 가능),
  3. 연·월·일 (89세 초과는 "90+" 로 통합), 4. 전화, 5. FAX, 6. 이메일,
  7. SSN, 8. MRN, 9. 보험번호, 10. 계좌번호, 11. 자격번호 (면허·자격증),
  12. 차량 식별번호 (VIN, plate), 13. 디바이스 식별자/일련번호,
  14. URL, 15. IP, 16. 생체정보 (지문·홍채), 17. 사진 (전면 얼굴),
  18. 기타 고유 식별 코드 / 특성
- 기법:
  - **Suppression** — 값 자체 삭제 또는 NULL
  - **Generalization** — 정밀도 낮춤 (생년월일 → 연령구간, ZIP 5 → ZIP 3)
  - **Pseudonymization** — 키 매핑 (`MRN-0001234` → `P-7f3a9c`) — **재식별 가능 (linked)**
  - **Tokenization / FPE** — 형식 보존 암호화 (Format-Preserving Encryption, AES-FF1)
  - **k-Anonymity** — 같은 quasi-identifier 그룹에 k 명 이상 (k ≥ 5 권장)
  - **l-Diversity** — 그룹 내 민감 속성도 l 가지 이상
  - **t-Closeness** — 그룹 내 분포가 전체와 t 이내 유사
  - **Differential Privacy** — Laplace/Gaussian noise (ε ≤ 1.0 추천)
- Re-identification key — 별도 보안 보관소 (HIPAA 에서는 키 보유 자체는 허용)

**장점**:
- Safe Harbor 적용 후 데이터는 **PHI 가 아님** (HIPAA 적용 제외) → 자유로운 연구 활용
- AI/ML 학습 데이터셋 구축 가능 (MIMIC-IV, CheXpert)
- 외부 협력기관 데이터 공유 가능 — DUA(Data Use Agreement) 만으로

**단점·주의**:
- 과도한 generalization → 통계 가치 손실 (utility-privacy tradeoff)
- Quasi-identifier (성별 + 우편번호 + 생년월일) 조합으로 재식별 (Latanya Sweeney 87% 사례)
- 자유 텍스트 (clinical note) — NER + scrubbing 필수, 100% 완벽 어려움
- 의약품·진단명 자체가 희귀질환이면 식별자 — Expert Determination 권장

**컴플라이언스 매핑**:
- HIPAA §164.514(a)(b) — De-identification standards
- GDPR Art. 4(5) — Pseudonymisation (PHI 로 계속 분류) vs Anonymisation (적용 제외)
- 한국 개인정보보호법 §28-2 — 가명정보 처리 특례
- 한국 보건의료데이터 활용 가이드라인 (2023, 복지부)

**Safe Harbor 처리 전후 비교**:
```json
// BEFORE — PHI 포함 원본
{
  "name": "Kim Min-jun",
  "mrn": "MRN-0001234",
  "birthDate": "1990-01-15",
  "address": { "city": "Seoul", "postalCode": "06236" },
  "phone": "+82-10-1234-5678",
  "email": "minjun@example.com",
  "encounterDate": "2026-05-14",
  "diagnosis": "I21.4 Acute MI",
  "age": 36
}

// AFTER — Safe Harbor 적용 (18 identifier 제거)
{
  "subjectId": "P-7f3a9c",        // pseudonym (linked dataset)
  "birthYear": 1990,               // 연 단위만
  "ageGroup": "30-39",             // 연령 구간
  "region": "062",                 // ZIP 3자리 (인구 20,000+ 확인)
  "encounterMonth": "2026-05",     // 월 단위
  "diagnosis": "I21.4 Acute MI"    // 진단명 유지 — 흔한 진단이라 OK
}
```

**Kotlin 비식별 파이프라인 예제**:
```kotlin
class DeidentificationEngine(
    private val fpeKey: SecretKey,
    private val noteScrubber: NerScrubber,
) {
    fun safeHarbor(patient: Patient): DeidentifiedRecord {
        val pseudoId = fpe(patient.mrn)                              // 11. ID -> pseudonym
        val birthYear = patient.birthDate.year                       // 3. date -> year
        val age = Period.between(patient.birthDate, LocalDate.now()).years
            .coerceAtMost(90)                                        // 3. 89+ -> 90+
        val zip3 = patient.address.postalCode.take(3)
            .takeIf { isLargePopulation(it) } ?: "000"               // 2. ZIP3 only

        return DeidentifiedRecord(
            subjectId = pseudoId,
            birthYear = birthYear,
            ageGroup = "${(age / 10) * 10}-${(age / 10) * 10 + 9}",
            region = zip3,
            // 1, 4-10, 12-17 모두 suppressed
        )
    }

    /** Format-Preserving Encryption (NIST SP 800-38G FF1, AES-128 base). */
    private fun fpe(input: String): String =
        Ff1Cipher(fpeKey).encrypt(input)

    /** Clinical note — NER 로 PHI span 검출 후 [REDACTED] 치환. */
    fun scrubNote(note: String): String {
        val spans = noteScrubber.detect(note)  // Stanford NER / cTAKES / Philter
        return spans.foldRight(note) { span, acc ->
            acc.replaceRange(span.start, span.end, "[REDACTED:${span.type}]")
        }
    }
}

// k-Anonymity 검증 — quasi-identifier 그룹 크기 확인
fun assertKAnonymity(records: List<DeidentifiedRecord>, k: Int = 5) {
    records.groupBy { Triple(it.birthYear / 5, it.ageGroup, it.region) }
        .forEach { (qi, group) ->
            require(group.size >= k) {
                "k-anonymity violation: $qi has only ${group.size} records (< $k)"
            }
        }
}
```

**관련 패턴**: [PHI Audit Trail](#phi-audit-trail), [`../../security/security-data-protection.md` Tokenization/FPE](../../security/security-data-protection.md)

---

## 8. DICOM Imaging Pipeline — DICOM 영상 파이프라인

<a id="dicom-pipeline"></a>

**목적**: 의료영상(CT / MRI / X-ray / 초음파 / 병리)을 **DICOM (Digital Imaging and Communications in Medicine)** 표준으로 모달리티 → PACS → 뷰어까지 일관되게 송수신·저장·조회합니다.

**메커니즘**:
- DICOM 객체 — 이미지 + **DICOM tag** 메타데이터 (수천 개)
  - `(0010,0010)` PatientName, `(0010,0020)` PatientID
  - `(0008,0060)` Modality (`CT` / `MR` / `CR` / `US` / `SC`)
  - `(0020,000D)` StudyInstanceUID, `(0020,000E)` SeriesInstanceUID, `(0008,0018)` SOPInstanceUID
  - `(0028,0010)` Rows, `(0028,0011)` Columns
- 계층: **Patient → Study → Series → Instance(Image)**
- 통신 프로토콜:
  - **DIMSE-C** (전통적 DICOM) — TCP/IP, AE Title 기반
    - **C-STORE** — 영상 저장 (모달리티 → PACS)
    - **C-FIND** — 메타데이터 검색
    - **C-MOVE** / **C-GET** — 영상 회수
    - **C-ECHO** — DICOM ping
  - **DICOMweb** (RESTful) — HTTP + JSON/multipart
    - **STOW-RS** (Store) — `POST /studies`
    - **QIDO-RS** (Query) — `GET /studies?PatientID=...&00080060=CT`
    - **WADO-RS** (Retrieve) — `GET /studies/{uid}/series/{uid}/instances/{uid}`
    - **WADO-URI** — 단일 이미지 URL
- 뷰어:
  - **Cornerstone.js / OHIF Viewer** — 웹 기반 (DICOMweb 사용)
  - **OsiriX / Horos** — macOS 데스크탑
  - **3D Slicer** — 연구용
- Tile-based rendering — 거대 병리 슬라이드(40K × 40K px) 는 deep zoom (DZI / DICOM-DPDS) 으로 타일링
- 압축 — JPEG 2000 (lossless) / JPEG-LS / RLE / HTJ2K (R2 신표준)
- PHI 처리 — 픽셀에 burned-in 환자 정보 (초음파 화면 캡처) → OCR + 마스킹 필수

**장점**:
- 단일 표준으로 전 세계 영상 장비·PACS·뷰어 호환
- 메타데이터(촬영 파라미터, 환자 ID, 진단)와 영상 한 객체에 통합
- DICOMweb 으로 모바일·웹 뷰어 통합 용이
- AI 추론 결과 → DICOM SR (Structured Report) / DICOM Seg (Segmentation) 로 회신 표준

**단점·주의**:
- 객체 크기 큼 (CT 1 study 500MB ~ 2GB) — 네트워크·스토리지 비용
- DICOM tag VR (Value Representation) 다양 → 파싱 라이브러리 필수 (pydicom / dcm4che / fo-dicom)
- private tag (벤더 확장) 호환성 문제
- 픽셀 데이터 PHI — DICOM 헤더만 지워도 burned-in text 잔존 위험

**컴플라이언스 매핑**:
- DICOM PS3.15 — Security and System Management Profiles (TLS, DICOM Audit)
- HIPAA — DICOM 헤더의 PatientName/ID 는 PHI
- IHE Profile — Radiology Scheduled Workflow (SWF) / Cross-Enterprise Document Sharing for Imaging (XDS-I)

**DICOMweb STOW-RS 요청 예제**:
```
POST /dicomweb/studies HTTP/1.1
Host: pacs.example.org
Content-Type: multipart/related; type="application/dicom"; boundary=boundary123
Accept: application/dicom+json
Authorization: Bearer eyJ...

--boundary123
Content-Type: application/dicom

<binary DICOM Part 10 file>
--boundary123
Content-Type: application/dicom

<binary DICOM Part 10 file>
--boundary123--
```

**QIDO-RS 응답 예제 (Study 검색)**:
```json
[
  {
    "00080020": { "vr": "DA", "Value": ["20260514"] },
    "00080050": { "vr": "SH", "Value": ["ACC-2026-0042"] },
    "00080061": { "vr": "CS", "Value": ["CT"] },
    "00100010": { "vr": "PN", "Value": [{ "Alphabetic": "KIM^MIN-JUN" }] },
    "00100020": { "vr": "LO", "Value": ["MRN-0001234"] },
    "00100030": { "vr": "DA", "Value": ["19900115"] },
    "0020000D": { "vr": "UI", "Value": ["1.2.840.113619.2.55.3.604688.123.1715645000.42"] },
    "00201206": { "vr": "IS", "Value": ["3"] },
    "00201208": { "vr": "IS", "Value": ["1024"] }
  }
]
```
- `(0008,0061)` ModalitiesInStudy = `CT`
- `(0020,1206)` NumberOfSeriesRelatedInstances = 3
- `(0020,1208)` NumberOfStudyRelatedInstances = 1024 (1024 슬라이스)

**Kotlin DICOMweb 클라이언트 예제 (dcm4che)**:
```kotlin
// org.dcm4che:dcm4che-core + dcm4che-net
class DicomWebClient(private val base: String, private val token: String) {
    private val http = HttpClient.newHttpClient()

    /** QIDO-RS — 환자의 모든 study 검색. */
    fun queryStudies(patientId: String, modality: String? = null): List<StudyMeta> {
        val params = buildString {
            append("?PatientID=").append(URLEncoder.encode(patientId, UTF_8))
            modality?.let { append("&00080061=").append(it) }
            append("&includefield=00201206&includefield=00201208")
        }
        val req = HttpRequest.newBuilder(URI("$base/studies$params"))
            .header("Accept", "application/dicom+json")
            .header("Authorization", "Bearer $token")
            .GET().build()
        val resp = http.send(req, BodyHandlers.ofString())
        return parseStudyJson(resp.body())
    }

    /** WADO-RS — 단일 instance 다운로드. */
    fun retrieveInstance(studyUid: String, seriesUid: String, instanceUid: String): Attributes {
        val url = "$base/studies/$studyUid/series/$seriesUid/instances/$instanceUid"
        val req = HttpRequest.newBuilder(URI(url))
            .header("Accept", "multipart/related; type=\"application/dicom\"")
            .header("Authorization", "Bearer $token")
            .GET().build()
        val resp = http.send(req, BodyHandlers.ofInputStream())
        DicomInputStream(resp.body()).use { return it.readDataset() }
    }

    /** PHI 마스킹 — DICOM 헤더 + 픽셀 burned-in text. */
    fun deidentify(ds: Attributes): Attributes {
        DeIdentificationProfile().apply(ds)        // PS3.15 Basic De-id Profile
        ds.setString(Tag.PatientName, VR.PN, "ANONYMOUS")
        ds.setString(Tag.PatientID, VR.LO, fpe(ds.getString(Tag.PatientID)))
        // 픽셀 OCR 마스킹은 별도 (e.g. CTP DicomPixelAnonymizer)
        return ds
    }
}
```

**관련 패턴**: [IHE Profiles](#ihe-profiles), [De-identification](#de-identification), [`../caching.md` Tile/CDN](../caching.md)

---

## 9. IHE Profiles (XDS / XCA / PIX) — IHE 통합 프로파일

<a id="ihe-profiles"></a>

**목적**: HL7·DICOM 같은 기반 표준 위에 **실무 워크플로별 구체 사용법(profile)** 을 정의하여 다기관 의료데이터 공유·환자 식별 일치를 보장합니다. IHE(Integrating the Healthcare Enterprise, 1998~) 가 관리.

**메커니즘**:
- 핵심 프로파일:
  - **XDS.b** (Cross-Enterprise Document Sharing) — 기관 간 임상문서(CDA / PDF / FHIR) 등록·검색·회수
    - 액터: Document Source / Repository / Registry / Consumer
    - 트랜잭션: ITI-41 (Provide and Register), ITI-18 (Registry Stored Query), ITI-43 (Retrieve)
  - **XCA** (Cross-Community Access) — 다른 community(HIE) 간 연합 검색
  - **PIX** (Patient Identifier Cross-Reference) — 기관마다 다른 MRN 을 enterprise ID 로 매핑
    - 트랜잭션: ITI-8 (PIX Feed), ITI-9 (PIX Query)
  - **PDQ** (Patient Demographics Query) — 이름·생년월일·전화로 환자 검색
  - **ATNA** (Audit Trail and Node Authentication) — 위 모든 트랜잭션의 audit + TLS mutual auth
  - **CT** (Consistent Time) — NTP 동기화 (audit timestamp 일관성)
  - **MHD** (Mobile access to Health Documents) — XDS 의 FHIR/RESTful 버전 (모바일 친화)
- 문서 포맷:
  - **CDA R2** (Clinical Document Architecture) — XML 임상문서 (CCD / Discharge Summary)
  - **FHIR Document Bundle** — 신규 시스템 권장
- 환자 식별:
  - **Domain Identifier** — 기관 OID + local MRN
  - **Enterprise Identifier** — PIX Manager 가 발급
  - **Cross-reference** — PIX Query 로 모든 매핑된 ID 회수

**장점**:
- 다기관 의료정보교류 (HIE / 한국 진료의뢰회송 시스템) 표준 청사진
- HL7·DICOM 의 모호한 부분을 실무 시나리오로 구체화
- 정부·보험사 입찰 요구사항 (한국 보건복지부 진료정보교류사업, EU eHealth DSI)

**단점·주의**:
- ebXML Registry 등 구식 SOAP 기반 — 신규 시스템은 MHD (FHIR) 권장
- 메타데이터 코드셋 복잡 (Class / Type / Format / HealthcareFacility / Practice / Confidentiality)
- 프로파일 간 의존성 — XDS 단독 운영 불가, ATNA + CT 필수

**컴플라이언스 매핑**:
- HIPAA §164.314 — Business Associate (HIE = BA)
- 21st Century Cures — TEFCA (Trusted Exchange Framework, 2024 가동)
- 한국 진료정보교류 표준 (KOLAS 인증 대상)

**XDS Document Registry — Stored Query 예제 (SOAP)**:
```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <query:AdhocQueryRequest xmlns:query="urn:oasis:names:tc:ebxml-regrep:xsd:query:3.0">
      <query:ResponseOption returnComposedObjects="true" returnType="LeafClass"/>
      <rim:AdhocQuery id="urn:uuid:14d4debf-8f97-4251-9a74-a90016b0af0d"
                      xmlns:rim="urn:oasis:names:tc:ebxml-regrep:xsd:rim:3.0">
        <rim:Slot name="$XDSDocumentEntryPatientId">
          <rim:ValueList>
            <rim:Value>'MRN-0001234^^^&amp;1.2.410.200119.4&amp;ISO'</rim:Value>
          </rim:ValueList>
        </rim:Slot>
        <rim:Slot name="$XDSDocumentEntryStatus">
          <rim:ValueList>
            <rim:Value>('urn:oasis:names:tc:ebxml-regrep:StatusType:Approved')</rim:Value>
          </rim:ValueList>
        </rim:Slot>
        <rim:Slot name="$XDSDocumentEntryClassCode">
          <rim:ValueList>
            <rim:Value>('11488-4^^2.16.840.1.113883.6.1')</rim:Value>
          </rim:ValueList>
        </rim:Slot>
      </rim:AdhocQuery>
    </query:AdhocQueryRequest>
  </soap:Body>
</soap:Envelope>
```

해석:
- 환자 ID `MRN-0001234` (assigning authority OID `1.2.410.200119.4` ISO)
- Status = Approved (게시된 문서만)
- Class = LOINC `11488-4` (Consultation Note)

**MHD (FHIR) 버전 — 모바일/웹 친화**:
```
GET /fhir/DocumentReference?
    patient=Patient/example-001
    &status=current
    &type=http://loinc.org|11488-4
    &date=ge2025-01-01
HTTP/1.1
Accept: application/fhir+json
Authorization: Bearer eyJ...
```

응답 (FHIR Bundle):
```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 2,
  "entry": [
    {
      "resource": {
        "resourceType": "DocumentReference",
        "status": "current",
        "type": {
          "coding": [{ "system": "http://loinc.org", "code": "11488-4",
                       "display": "Consultation Note" }]
        },
        "subject": { "reference": "Patient/example-001" },
        "date": "2026-05-12T14:30:00+09:00",
        "author": [{ "reference": "Practitioner/dr-lee" }],
        "custodian": { "reference": "Organization/hosp-a" },
        "content": [{
          "attachment": {
            "contentType": "application/pdf",
            "url": "https://docs.example.org/Binary/cons-001",
            "size": 524288, "hash": "Q5Z9..."
          }
        }]
      }
    }
  ]
}
```

**Kotlin PIX Query 예제 (HAPI HL7 v2 PIX V3)**:
```kotlin
class PixCrossReference(private val pixMgr: PixManagerClient) {
    /**
     * 다른 기관 MRN → enterprise ID + 모든 매핑된 ID 반환.
     * IHE ITI-9 (PIX Query).
     */
    suspend fun resolveAllIds(domainOid: String, localMrn: String): List<PatientIdentifier> {
        val q = QBP_Q21().apply {
            qpd.messageQueryName.identifier.value = "IHE PIX Query"
            qpd.getField(3, 0).apply {     // QPD-3 Person Identifier
                (this as CX).idNumber.value = localMrn
                assigningAuthority.universalID.value = domainOid
                assigningAuthority.universalIDType.value = "ISO"
            }
            // QPD-4 What Domains Returned — 모든 도메인
        }
        val ack = pixMgr.send(q) as RSP_K23
        return ack.queryResponse.pid.patientIdentifierList.map { cx ->
            PatientIdentifier(
                value = cx.idNumber.value,
                system = "urn:oid:${cx.assigningAuthority.universalID.value}",
            )
        }
    }
}
```

**관련 패턴**: [FHIR R5 Resource](#fhir-r5-resource), [HL7 v2 Messaging](#hl7-v2-messaging), [DICOM Pipeline](#dicom-pipeline), [PHI Audit Trail](#phi-audit-trail)

---

## 10. Telehealth Session Pattern — 원격진료 세션 패턴

<a id="telehealth-session"></a>

**목적**: 의사·환자의 실시간 화상/음성 진료 세션을 **WebRTC** 로 매개하고, 진료 내용을 EHR 에 FHIR `Encounter` + `Observation` 로 write-back 하여 일반 대면 진료와 동등한 임상 기록을 남깁니다.

**메커니즘**:
- 세션 생명주기:
  1. **예약** — FHIR `Appointment` (status `booked`)
  2. **사전 동의** — FHIR `Consent` (녹화 / 데이터 활용)
  3. **Pre-check** — 카메라·마이크·네트워크 (RTCStats `mediaSourceStats`)
  4. **Signaling** — WebSocket / SIP (SDP offer/answer + ICE candidate)
  5. **Media** — WebRTC (DTLS-SRTP) 직접 P2P 또는 SFU (Janus / mediasoup / LiveKit)
  6. **In-call EHR write** — vital sign 입력, 사진 첨부, 처방 작성
  7. **종료 + 청구** — `Encounter.status = finished`, `Claim` 생성
- 컴포넌트:
  - **STUN/TURN** — NAT 통과 (TURN over TLS:443 필수 — 사내망 우회)
  - **SFU** — 다자 진료 (보호자 동참, 통역) 시 미디어 라우팅
  - **녹화** — 별도 동의 + 추가 보존 정책 (보통 진료 종료 후 7일 ~ 6년)
  - **자막/번역** — 외국인 환자용 (Whisper / Google Cloud Speech)
  - **백그라운드 필터링** — 의료진 환경 노출 방지
- 클라이언트 흐름:
  - 환자: SMART on FHIR Standalone Launch → 동의 → 입장
  - 의사: EHR Launch → 환자 차트 옆 화상 패널
- 보안:
  - DTLS-SRTP — 미디어 E2E 암호화 (서버는 키 미보유, P2P 또는 selective forwarding 만)
  - TURN 인증 — 단명 자격증명 (TURN REST API, HMAC-SHA1)
  - **녹화 시점만 평문 디코딩** — 키 분리 보관 (KMS)
- 청구 (US):
  - CPT code 99421-99423 (online digital), 99441-99443 (phone)
  - HCPCS G2010 (store-and-forward)
- 한국 — 비대면진료 시범사업 (2023~) — Encounter Class 코드 `VR` (Virtual)

**장점**:
- 도서산간·이동제약 환자 접근성
- COVID-19 이후 보험 수가 인정 확대 (US Medicare, 한국 시범)
- EHR 통합으로 일반 진료와 동일한 임상 기록 유지

**단점·주의**:
- 처방 제약 — 마약류·정신과 약물은 비대면 제한 (한국 의료법 §17-2)
- HIPAA 위반 위험 — Zoom 일반 버전 사용 금지, **HIPAA-eligible** 플랜·BAA 체결 필수
- 진료 품질 — 청진·촉진 불가 → 적응증 제한
- 녹화 보존·삭제 정책 명문화 필요 (환자 본인 사본 요청권)

**컴플라이언스 매핑**:
- HIPAA §164.308(b) — Business Associate Agreement (Twilio, LiveKit, AWS Chime SDK 모두 BAA 가능)
- HIPAA §164.312(e)(2)(ii) — Transmission encryption: DTLS-SRTP 충족
- 한국 의료법 §17-2 (시행규칙) — 비대면진료 가능 대상·약물 제한
- ONC §170.315(g)(7) — Application access for patients

**WebRTC SDP offer 예제 (의료진 측 — video + audio)**:
```
v=0
o=- 4611732710 2 IN IP4 0.0.0.0
s=-
t=0 0
a=group:BUNDLE 0 1
a=msid-semantic: WMS telemed-session-abc
a=ice-options:trickle
m=audio 9 UDP/TLS/RTP/SAVPF 111 103 104
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:F1y7
a=ice-pwd:VnGSeqRGr7eUgsa2dCVeJvCp
a=fingerprint:sha-256 4A:AD:B9:B1:3F:82:18:3B:54:02:12:DF:3E:5D:49:6B:19:E5:7C:AB:46:8D:75:4B:D5:CE:F1:0D:C6:DC:69:31
a=setup:actpass
a=mid:0
a=sendrecv
a=rtpmap:111 opus/48000/2
a=fmtp:111 minptime=10;useinbandfec=1
m=video 9 UDP/TLS/RTP/SAVPF 96 97
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:F1y7
a=ice-pwd:VnGSeqRGr7eUgsa2dCVeJvCp
a=fingerprint:sha-256 4A:AD:B9:B1:3F:82:18:3B:54:02:12:DF:3E:5D:49:6B:19:E5:7C:AB:46:8D:75:4B:D5:CE:F1:0D:C6:DC:69:31
a=setup:actpass
a=mid:1
a=sendrecv
a=rtpmap:96 VP8/90000
a=rtpmap:97 rtx/90000
a=fmtp:97 apt=96
```

**FHIR Encounter (Virtual) write-back 예제**:
```json
{
  "resourceType": "Encounter",
  "status": "finished",
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "VR", "display": "Virtual"
  },
  "type": [
    { "coding": [{ "system": "http://snomed.info/sct",
                   "code": "448337001",
                   "display": "Telemedicine consultation with patient" }] }
  ],
  "subject": { "reference": "Patient/example-001" },
  "participant": [
    {
      "type": [{ "coding": [{ "code": "PPRF",
                              "display": "primary performer" }] }],
      "individual": { "reference": "Practitioner/dr-lee" }
    }
  ],
  "period": {
    "start": "2026-05-14T10:00:00+09:00",
    "end":   "2026-05-14T10:18:34+09:00"
  },
  "reasonCode": [
    { "coding": [{ "system": "http://snomed.info/sct",
                   "code": "25064002", "display": "Headache" }] }
  ],
  "extension": [
    {
      "url": "http://example.org/fhir/StructureDefinition/telehealth-session",
      "extension": [
        { "url": "platform", "valueCode": "livekit-room-abc-123" },
        { "url": "recordingId", "valueReference": { "reference": "DocumentReference/rec-789" } },
        { "url": "consent", "valueReference": { "reference": "Consent/cons-456" } }
      ]
    }
  ]
}
```

**Kotlin 세션 오케스트레이터 예제**:
```kotlin
class TelehealthSession(
    private val fhir: FhirClient,
    private val signaling: SignalingServer,
    private val turn: TurnCredentialsProvider,
    private val audit: TamperEvidentAuditLog,
) {

    suspend fun start(appointmentId: String, doctorId: String, patientId: String): SessionHandle {
        // 1. Consent 사전 확인
        val consent = fhir.search<Bundle>(
            "Consent?patient=$patientId&category=telehealth&status=active"
        ).entries.firstOrNull() ?: error("missing telehealth consent")

        // 2. Encounter 생성 (in-progress)
        val encounter = fhir.create(Encounter().apply {
            status = EncounterStatus.INPROGRESS
            classElement = Coding("http://terminology.hl7.org/CodeSystem/v3-ActCode", "VR", "Virtual")
            subject = Reference("Patient/$patientId")
            addParticipant().apply {
                individual = Reference("Practitioner/$doctorId")
            }
            period = Period().apply { start = Date() }
        })

        // 3. 단명 TURN credentials (HMAC-SHA1)
        val turnCreds = turn.issue(ttl = Duration.ofMinutes(60), user = "session-${encounter.id}")

        // 4. Signaling room 오픈 (DTLS fingerprint 교환)
        val room = signaling.openRoom(encounter.id, listOf(doctorId, patientId))

        audit.append(AuditEvent.start(encounter.id, doctorId, patientId))
        return SessionHandle(encounter.id, room, turnCreds)
    }

    suspend fun finish(handle: SessionHandle, vitals: List<Observation>, note: String) {
        // vital sign FHIR write-back
        vitals.forEach { fhir.create(it.apply { encounter = Reference("Encounter/${handle.encounterId}") }) }
        // 진료 노트
        fhir.create(DocumentReference().apply {
            type = CodeableConcept().addCoding(
                Coding("http://loinc.org", "34109-9", "Note"))
            subject = handle.encounter.subject
            content = listOf(DocumentReferenceContent(Attachment().apply {
                contentType = "text/plain"
                data = note.toByteArray()
            }))
        })
        // Encounter 종료
        fhir.update(handle.encounterId) {
            status = EncounterStatus.FINISHED
            period.end = Date()
        }
        audit.append(AuditEvent.finish(handle.encounterId))
        signaling.closeRoom(handle.room)
    }
}
```

**관련 패턴**: [FHIR R5 Resource](#fhir-r5-resource), [SMART on FHIR](#smart-on-fhir), [Consent Management](#consent-management-fhir), [PHI Audit Trail](#phi-audit-trail), [`../../security/security-data-protection.md` E2E DTLS-SRTP](../../security/security-data-protection.md)
