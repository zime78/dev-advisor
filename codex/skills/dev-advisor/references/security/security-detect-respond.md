# 보안 탐지 및 사고 대응 패턴 (Security Detection & Incident Response Patterns)

보안 이벤트를 수집·상관 분석하고, 위협을 탐지한 후 자동화된 플레이북으로 대응하는 패턴 모음. NIST SP 800-61 Rev.2 / MITRE ATT&CK / Sigma Rule 표준을 기반으로 한다. [observability/audit-trail.md]의 일반 감사 로그와 달리 이 문서는 tamper-evident 보안 측면에 집중한다.

---

## 1. SIEM (Security Information & Event Management)

**목적**: 분산된 시스템의 로그·이벤트를 중앙으로 집계하고 상관 분석(correlation)을 통해 개별 이벤트로는 식별 불가능한 공격 패턴을 탐지합니다.

**특징**:
- 로그 집계: syslog / Beats / Fluentd → Kafka 버퍼 → Elasticsearch / Splunk / Microsoft Sentinel 인덱싱
- 정규화(Normalization): 벤더별 다른 로그 포맷을 공통 스키마(ECS / OCSF)로 변환
- 상관 분석: 시간 윈도우 내 다수 이벤트 패턴 매핑 (예: 5분 내 10회 로그인 실패 후 성공)
- Baseline 학습: 정상 트래픽 패턴 수립 후 이탈(anomaly) 탐지
- 보존 정책(Retention): Hot(90일) / Warm(1년) / Cold(7년 아카이브) 계층화 — 규제 요건 준수
- SIEM 제품: Splunk Enterprise Security, Elastic SIEM, Microsoft Sentinel, IBM QRadar

**장점**:
- 단일 창구에서 멀티 소스 위협 가시성 확보
- 규제 감사(PCI-DSS, ISO 27001, SOC 2) 대응 원스톱
- 알려진 공격 패턴을 rule-based로 즉시 탐지

**단점**:
- 초기 튜닝 없으면 false positive 폭발 → alert fatigue
- 데이터 볼륨 증가 시 라이선스·인프라 비용 급증
- 고도화된 APT(Advanced Persistent Threat)는 정상 행위로 위장해 탐지 회피 가능

**활용 예시**:
- 브루트포스 탐지: 5분 내 동일 IP의 실패 인증 10회 이상 → 계정 잠금 알람
- 횡적 이동 탐지: 서버 A에서 B, C, D로 짧은 시간 내 SSH 연결 시도
- 데이터 유출 탐지: 업무 시간 외 대용량 파일 접근 + 외부 전송

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**예제 — Sigma Rule (generic detection rule) + Splunk SPL**:
```yaml
# Sigma Rule: 브루트포스 후 성공 로그인 탐지
title: Brute Force followed by Successful Login
id: a6f9c3e1-1234-4b5f-9d8a-abc123def456
status: stable
description: 5분 내 10회 이상 실패 후 같은 소스에서 로그인 성공
author: security-team
date: 2026-01-01
logsource:
  category: authentication
  product: linux
detection:
  selection_fail:
    event.action: "authentication_failed"
  selection_success:
    event.action: "authentication_success"
  timewindow:
    window: 5m
    groupby:
      - source.ip
      - user.name
    condition:
      - selection_fail | count >= 10
      - selection_success: true
  condition: timewindow
falsepositives:
  - 배치 계정의 재시도 정책
level: high
tags:
  - attack.credential_access
  - attack.t1110  # Brute Force
```

```spl
# Splunk SPL — 동일 패턴 상관 분석 (4시간 윈도우 기준)
index=auth_logs
| bucket _time span=4h
| stats
    count(eval(action="fail"))   AS fail_count
    count(eval(action="success")) AS success_count
    BY _time, src_ip, user
| where fail_count >= 10 AND success_count >= 1
| eval risk_score = fail_count * 2
| sort - risk_score
| table _time, src_ip, user, fail_count, success_count, risk_score
```

**관련 패턴**: SOAR, UEBA, MITRE ATT&CK Mapping, Audit Log Pattern

---

## 2. SOAR (Security Orchestration, Automation & Response)

**목적**: SIEM 알람을 트리거로 사전 정의된 플레이북을 자동 실행하여 대응 속도를 높이고 인적 오류를 줄입니다. 반복적인 초동 대응(triage, enrichment, containment)을 자동화합니다.

**특징**:
- 플레이북(Playbook): 조건 분기(if/else) + 병렬 액션으로 구성된 대응 워크플로우
- Enrichment: IP/도메인/해시를 VirusTotal / Shodan / AbuseIPDB / 내부 CMDB와 연계 조회
- Containment 액션: 방화벽 차단, EDR isolation, AD 계정 비활성화, Slack 알림 자동화
- Case Management: 인시던트 티켓 자동 생성 (Jira / ServiceNow)
- 제품: Palo Alto XSOAR, Splunk SOAR (Phantom), Microsoft Sentinel Automation, Shuffle (오픈소스)

**장점**:
- MTTR(Mean Time To Respond) 수십 분 → 수 초 단축
- Tier-1 SOC 분석가의 반복 업무 90% 자동화
- 일관된 대응 — 분석가마다 다른 대응 절차 표준화

**단점**:
- 잘못 설계된 플레이북은 정상 시스템 차단 (false positive 위험)
- 플레이북 유지보수 비용 (환경 변화 시 업데이트 필요)
- 완전 자동 차단은 고위험 — 단계별 승인 게이트 권장

**활용 예시**:
- 피싱 이메일 자동 분석 + 삭제
- 랜섬웨어 감지 시 호스트 즉시 격리
- 클라우드 미설정(misconfiguration) 자동 교정

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**예제 — 피싱 이메일 대응 플레이북 (의사코드)**:
```yaml
# SOAR Playbook: Phishing Email Response
name: Phishing Email Auto-Response
trigger:
  source: SIEM
  rule_id: PHISH-001
  severity: [high, critical]

steps:
  # 1단계: 분류 및 초기 데이터 수집
  - name: extract_indicators
    actions:
      - parse: [sender_email, sender_domain, urls, attachments_hash]
      - extract_headers: [reply-to, x-originating-ip, received-from]

  # 2단계: Enrichment (병렬 실행)
  - name: enrich_parallel
    parallel: true
    actions:
      - virustotal_lookup: { targets: [urls, attachments_hash] }
      - abuseipdb_check:   { target: x-originating-ip }
      - whois_lookup:      { target: sender_domain }
      - internal_cmdb:     { query: "has anyone received from {sender_domain}?" }

  # 3단계: 자동 판정
  - name: auto_triage
    condition:
      if: virustotal_score >= 3 OR abuseipdb_confidence >= 80
      then: verdict = "malicious"
      else: verdict = "suspicious"

  # 4단계: Containment (malicious 판정 시 자동 실행)
  - name: contain_if_malicious
    condition: verdict == "malicious"
    actions:
      - email_gateway: { action: quarantine_all_copies, sender: sender_email }
      - ad_lookup:     { find_recipients: true }
      - notify_recipients:
          channel: slack
          message: "피싱 이메일 수신 확인됨. 첨부파일/링크 클릭 금지."
      - create_jira_ticket:
          project: SEC
          priority: high
          summary: "Phishing: {sender_email} — {subject}"

  # 5단계: 분석가 확인 (suspicious 판정 시)
  - name: analyst_review
    condition: verdict == "suspicious"
    actions:
      - create_jira_ticket: { priority: medium, assignee: soc-tier1 }
      - wait_for_approval:  { timeout: 30m, fallback: escalate }
```

**관련 패턴**: SIEM, Incident Response Playbook, MITRE ATT&CK Mapping

---

## 3. Audit Log Pattern — Tamper-Evident (보안 관점 감사 로그)

**목적**: 감사 로그 자체가 위·변조되었는지 암호학적으로 검증할 수 있게 하여, 침해 사고 후 포렌식과 부인 방지(non-repudiation)를 보장합니다.

> **observability/audit-trail.md와 소유권 분리**: observability 문서는 일반 운영 감사(누가 언제 무엇을 했는가)를 다룹니다. 이 항목은 그것을 전제로 **tamper-evident 속성** (hash chain, WORM 저장, 서명)에 집중합니다.

**특징**:
- Hash Chain: 각 로그 엔트리에 `HMAC(이전 엔트리 해시 + 현재 내용)`를 포함 → 중간 삭제·수정 즉시 탐지
- Append-Only 강제: DB row 수정·삭제 금지 (INSERT only), 소프트 삭제도 금지
- WORM Storage: AWS S3 Object Lock / Azure Immutable Blob / Write-Once 테이프 아카이브
- 디지털 서명: 로그 배치(batch)마다 서버 private key로 서명 → 외부 검증자가 public key로 확인
- 타임스탬프 신뢰성: RFC 3161 Trusted Timestamping (TSA)
- 보존 정책: 규제별 최소 보존 기간 (PCI-DSS: 1년, HIPAA: 6년, GDPR: 처리 목적 기간)

**장점**:
- 포렌식 신뢰성 — 법정·감사에서 로그 무결성 증명 가능
- 내부자 위협 탐지 — DBA가 로그 삭제 시도 → chain 파손으로 탐지
- 규제 컴플라이언스 (SOX, PCI-DSS 10.5.5) 직접 충족

**단점**:
- Hash Chain은 순차 쓰기 강제 → 분산 병렬 환경에서 설계 복잡
- 서명 키 관리 추가 필요 (HSM/Vault)
- 오래된 엔트리 삭제 불가 → GDPR "잊혀질 권리" 이행 시 별도 설계 (암호화 후 키 삭제)

**활용 예시**:
- 금융 거래 감사 로그 (거래 발생 → chain 엔트리 → 일별 서명)
- 의료 기록 접근 로그 (HIPAA)
- 클라우드 관리자 콘솔 작업 이력
- 암호화폐 거래소 내부 원장

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제 — HMAC Hash Chain + 서명**:
```kotlin
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import java.security.MessageDigest
import java.util.Base64

data class AuditEntry(
    val id: Long,
    val timestamp: Long,      // epoch ms
    val actor: String,
    val action: String,
    val resource: String,
    val prevHash: String,     // 이전 엔트리의 hash
    val entryHash: String,    // HMAC(prevHash + payload)
)

class TamperEvidentAuditLogger(
    private val hmacKey: ByteArray,   // HSM/Vault에서 주입 — 코드에 하드코딩 금지
    private val db: AuditRepository,
) {
    private val hmac = Mac.getInstance("HmacSHA256")

    /**
     * 새 감사 이벤트를 hash chain에 append.
     * prevHash = 직전 엔트리의 entryHash (첫 엔트리는 genesis hash 고정값).
     */
    fun append(actor: String, action: String, resource: String): AuditEntry {
        val prev = db.findLatest()
        val prevHash = prev?.entryHash ?: "GENESIS:0000000000000000"

        val payload = "$prevHash|${System.currentTimeMillis()}|$actor|$action|$resource"
        val entryHash = computeHmac(payload)

        val entry = AuditEntry(
            id        = db.nextId(),
            timestamp = System.currentTimeMillis(),
            actor     = actor,
            action    = action,
            resource  = resource,
            prevHash  = prevHash,
            entryHash = entryHash,
        )
        db.insertOnly(entry)   // UPDATE/DELETE 금지 — DB 제약으로 강제
        return entry
    }

    /** 지정 범위의 chain 무결성 검증 — 포렌식/감사 시 호출 */
    fun verify(from: Long, to: Long): VerifyResult {
        val entries = db.findRange(from, to)
        var expected = entries.first().prevHash
        for (e in entries) {
            val payload = "${e.prevHash}|${e.timestamp}|${e.actor}|${e.action}|${e.resource}"
            val computed = computeHmac(payload)
            if (computed != e.entryHash) {
                return VerifyResult.Tampered(e.id, expected, e.entryHash)
            }
            expected = e.entryHash
        }
        return VerifyResult.Ok(entries.size)
    }

    private fun computeHmac(data: String): String {
        hmac.init(SecretKeySpec(hmacKey, "HmacSHA256"))
        return Base64.getEncoder().encodeToString(hmac.doFinal(data.toByteArray()))
    }
}

sealed class VerifyResult {
    data class Ok(val count: Int) : VerifyResult()
    data class Tampered(val atId: Long, val expected: String, val actual: String) : VerifyResult()
}
```

**관련 패턴**: SIEM, Incident Response Playbook, Secrets Vault

---

## 4. UEBA (User & Entity Behavior Analytics)

**목적**: 사용자와 시스템 엔티티의 정상 행위 baseline을 통계적으로 학습하고, 이탈 패턴(anomaly)을 점수화하여 내부자 위협, 계정 탈취, APT를 탐지합니다.

**특징**:
- Peer Group Analysis: 동일 부서/역할 그룹과 행동 비교 — 절대값이 아닌 상대적 이상 탐지
- Impossible Travel: 서울 로그인 → 2시간 후 뉴욕 로그인 → 물리적으로 불가 → 계정 탈취 신호
- Off-hours Access: 업무 시간 외 민감 데이터 대량 접근 → 내부자 유출 신호
- Risk Score 누적: 단일 이상 신호는 낮은 점수, 복수 신호 중첩 시 임계값 초과 → 알람
- 학습 기간: 최소 30일 정상 행위 학습 후 탐지 활성화 (cold start 문제)
- 제품: Microsoft Sentinel UEBA, Splunk UBA, Exabeam, Gurucul

**장점**:
- 서명(signature) 없는 알려지지 않은(zero-day) 공격 탐지 가능
- 내부자 위협에 특히 효과적 (권한 있는 사용자의 악용)
- 점진적 위험 누적으로 false positive 감소

**단점**:
- 학습 기간 동안 공격에 취약 (cold start)
- 행동 패턴 변화(부서 이동, 재택근무 확대)로 오탐 발생
- 대규모 사용자 환경에서 모델 유지보수 비용 높음
- 개인정보 보호 우려 — 직원 행동 모니터링 법적 검토 필요

**활용 예시**:
- M&A 전 내부자 데이터 유출 탐지
- 금융권 — 거래 담당자의 비정상 거래 접근 패턴
- 클라우드 자격증명 탈취 — 보통 사용하지 않는 리전에서 API 호출
- 퇴직 예정자 데이터 대량 다운로드 탐지

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**예제 — Impossible Travel 탐지 로직 (Kotlin)**:
```kotlin
import kotlin.math.*

data class LoginEvent(
    val userId: String,
    val timestamp: Long,      // epoch ms
    val latitude: Double,
    val longitude: Double,
    val ipAddress: String,
    val country: String,
)

class ImpossibleTravelDetector(
    private val maxSpeedKmh: Double = 900.0,  // 비행기 최대 속도 기준
    private val riskStore: RiskScoreStore,
    private val alertBus: AlertBus,
) {
    /**
     * 신규 로그인 이벤트 처리.
     * 이전 로그인과의 이동 거리 / 시간 간격으로 물리적 불가 여부 판정.
     */
    fun evaluate(current: LoginEvent) {
        val previous = riskStore.getLastLogin(current.userId) ?: run {
            riskStore.saveLogin(current)
            return
        }

        val elapsedHours = (current.timestamp - previous.timestamp) / 3_600_000.0
        if (elapsedHours <= 0) return

        val distKm = haversineKm(
            previous.latitude, previous.longitude,
            current.latitude,  current.longitude,
        )
        val requiredSpeedKmh = distKm / elapsedHours

        if (requiredSpeedKmh > maxSpeedKmh) {
            val riskDelta = when {
                requiredSpeedKmh > 5_000 -> 80  // 초음속 — 사실상 불가
                requiredSpeedKmh > 2_000 -> 50
                else -> 30
            }
            riskStore.addScore(current.userId, riskDelta)
            alertBus.publish(
                UEBAAlert(
                    userId        = current.userId,
                    type          = "IMPOSSIBLE_TRAVEL",
                    detail        = "%.0f km in %.1f h (%.0f km/h)".format(distKm, elapsedHours, requiredSpeedKmh),
                    prevCountry   = previous.country,
                    currentCountry= current.country,
                    riskScore     = riskStore.getScore(current.userId),
                )
            )
        }

        riskStore.saveLogin(current)
    }

    // Haversine 공식으로 구면 거리 계산
    private fun haversineKm(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
        val r = 6371.0
        val dLat = Math.toRadians(lat2 - lat1)
        val dLon = Math.toRadians(lon2 - lon1)
        val a = sin(dLat / 2).pow(2) +
                cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) * sin(dLon / 2).pow(2)
        return 2 * r * asin(sqrt(a))
    }
}
```

**관련 패턴**: SIEM, MITRE ATT&CK Mapping, Incident Response Playbook

---

## 5. MITRE ATT&CK Mapping (적대 행위 분류 프레임워크)

**목적**: 실제 공격자 행위를 Tactic(목적) → Technique(방법) → Procedure(구체 구현)의 3계층으로 분류하고, 탐지 룰과 방어 통제를 체계적으로 매핑합니다.

**특징**:
- **계층 구조**:
  - **Tactic(전술/Why)**: 공격자의 목적 — TA0001(Initial Access) ~ TA0040(Impact) 14개 Tactic
  - **Technique(기술/How)**: 목적 달성 방법 — T1566(Phishing) 등 600+ Technique
  - **Sub-technique**: 구체 변형 — T1566.001(Spearphishing Attachment)
  - **Procedure(절차/What)**: 특정 그룹/툴의 실제 구현 사례
- **주요 Tactic 흐름**: Initial Access → Execution → Persistence → Privilege Escalation → Defense Evasion → Credential Access → Discovery → Lateral Movement → Collection → Exfiltration / Impact
- **Detection Coverage Matrix**: ATT&CK Navigator로 방어 통제 적용 범위 시각화
- **Sigma → ATT&CK**: Sigma rule tag(`attack.tXXXX`)로 탐지 룰을 Technique에 매핑
- 제품: MITRE ATT&CK Navigator, VECTR, AttackIQ, Atomic Red Team(테스트)

**장점**:
- 공격자 시각으로 방어 공백(gap) 가시화
- 위협 인텔리전스 보고서와 공통 언어 — "TA0006 T1555 확인됨"
- Red team / Purple team 연습의 공통 프레임워크
- 탐지 커버리지 정량화 가능

**단점**:
- 600+ Technique 전체 커버 불가 — 우선순위 선정 필요
- Procedure 레벨은 공격자마다 달라 재현 어려움
- 신규 기법은 데이터베이스 업데이트 주기(분기별) 차이 존재

**활용 예시**:
- SOC Detection 로드맵: 현재 커버 Technique 히트맵 → 공백 우선 보완
- IR 보고서: "공격자는 T1078(Valid Accounts) → T1021.002(SMB/Admin Shares) 경로 사용"
- Red Team 시나리오 설계
- 위협 인텔 공유 (STIX/TAXII 형식)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**예제 — MITRE ATT&CK 매핑 Sigma Rule + 탐지 커버리지 집계**:
```yaml
# Sigma Rule — T1078 Valid Accounts: 휴면 계정 사용 탐지
title: Dormant Account Activation
id: b2c1d4e5-5678-4c6d-a0b1-def789abc012
status: stable
description: 90일 이상 로그인 없던 계정의 갑작스러운 인증 성공
author: security-team
date: 2026-01-01
logsource:
  category: authentication
  product: windows
detection:
  selection:
    EventID: 4624
    LogonType: 3          # Network logon
  filter_recent:
    # 참조 테이블: accounts.last_login > now - 90d 는 여기서 제외
    AccountName|contains: "$"   # 컴퓨터 계정 제외
  condition: selection and not filter_recent
falsepositives:
  - 서비스 계정 장기 미사용 후 배치 재활성화
level: medium
tags:
  - attack.initial_access   # TA0001
  - attack.persistence      # TA0003
  - attack.t1078            # Valid Accounts
```

```bash
# Bash — MITRE ATT&CK 탐지 커버리지 집계 (Sigma rule tag 분석)
# 전제: sigma rules 폴더 내 모든 .yml에서 attack.t 태그 추출

echo "=== ATT&CK Technique Coverage ==="
grep -rh "attack\.t[0-9]" ./sigma-rules/ \
  | grep -oP 'attack\.t\d{4}(\.\d{3})?' \
  | sort | uniq -c | sort -rn \
  | awk '{ printf "%-6s %s\n", $1, $2 }' \
  | head -20

echo ""
echo "=== Total unique techniques covered ==="
grep -rh "attack\.t[0-9]" ./sigma-rules/ \
  | grep -oP 'attack\.t\d{4}' \
  | sort -u | wc -l

echo ""
echo "=== Coverage by Tactic (TA) ==="
# TA0001=Initial Access, TA0002=Execution, ... 매핑 테이블 필요
grep -rh "attack\." ./sigma-rules/ \
  | grep -oP 'attack\.(initial_access|execution|persistence|privilege_escalation|defense_evasion|credential_access|discovery|lateral_movement|collection|exfiltration|impact|command_and_control)' \
  | sort | uniq -c | sort -rn
```

**관련 패턴**: SIEM, SOAR, Incident Response Playbook, UEBA

---

## 6. Incident Response Playbook (NIST SP 800-61 Rev.2)

**목적**: 보안 침해 사고 발생 시 혼란을 최소화하고 체계적으로 대응·복구하기 위한 6단계 프로세스를 표준화합니다. NIST SP 800-61 Rev.2를 근거로 합니다.

**특징 — 6단계**:
1. **Preparation(준비)**: IR 팀 구성, playbook 문서화, 연락처/권한 매트릭스, 툴킷(포렌식 이미지, 네트워크 탭), 연습(tabletop exercise)
2. **Detection & Analysis(탐지·분석)**: 사고 식별, IOC(Indicator of Compromise) 수집, 심각도 분류, MITRE ATT&CK 매핑
3. **Containment(봉쇄)**: 피해 확산 차단 — 즉각(네트워크 격리), 단기(비밀번호 재설정), 장기(패치)
4. **Eradication(근절)**: 악성코드 제거, 취약점 패치, 백도어 제거, 재감염 경로 차단
5. **Recovery(복구)**: 시스템 복원, 서비스 재개, 모니터링 강화, 정상화 확인
6. **Lessons Learned(교훈)**: 사고 후 72시간 내 회고, 타임라인 재구성, 탐지/대응 개선 항목 도출

**장점**:
- 사고 중 의사결정 마비 방지 — 역할별 행동 지침 명확
- 포렌식 증거 보존 절차 내재화 → 법적 대응 가능
- 반복 사고 방지 (교훈 단계)

**단점**:
- 훈련 없이 문서만 있으면 실전에서 절차 누락
- 초기 탐지 → 봉쇄 간 시간이 MTTD(Mean Time To Detect)에 비례해 피해 증가
- 클라우드·컨테이너 환경에서 전통적 포렌식 이미지 수집 한계

**활용 예시**:
- 랜섬웨어 감염: 즉시 격리 → 스냅샷 보존 → 백업 복원 순서 확정
- 데이터 유출: 유출 범위 산정 → 규제 통보(GDPR 72시간) 타이밍 관리
- DDoS: CDN/WAF 대응 → ISP 블랙홀 라우팅 → 용량 확장 계획

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**예제 — IR 플레이북 체크리스트 (랜섬웨어 시나리오, Kotlin DSL 스타일)**:
```kotlin
/**
 * 랜섬웨어 인시던트 대응 플레이북 (NIST SP 800-61 6단계)
 * 실제 실행은 SOAR 시스템에서 트리거. 이 코드는 자동화 가능한 단계를 코드로 표현.
 */
object RansomwarePlaybook {

    /** Phase 1: Detection & Analysis — 1시간 내 완료 목표 */
    fun detectAndAnalyze(alert: SIEMAlert): IncidentCase {
        val ioc = extractIOCs(alert)      // 파일 해시, C2 IP, 레지스트리 키
        val severity = triageSeverity(ioc) // CRITICAL / HIGH / MEDIUM
        val case = IncidentCase.create(
            type     = "RANSOMWARE",
            severity = severity,
            iocs     = ioc,
            attkMap  = listOf("T1486", "T1490"),  // Data Encrypted, Inhibit Recovery
        )
        notifyIRTeam(case)   // PagerDuty/Slack 즉시 알람
        return case
    }

    /** Phase 2: Containment — 피해 확산 차단 (자동화 우선) */
    fun contain(case: IncidentCase, hosts: List<String>) {
        // 즉각 봉쇄: 감염 호스트 네트워크 격리 (EDR API)
        hosts.forEach { host ->
            edrClient.isolateHost(host)           // 인터넷/내부망 차단
            snapshotService.captureForensic(host) // 이미지 보존 (증거)
        }
        // 단기 봉쇄: 관련 계정 비활성화
        case.suspectedAccounts.forEach { adClient.disable(it) }
        // SIEM 탐지 룰 강화
        siemClient.addBlocklist(case.iocs.c2Ips)
    }

    /** Phase 3: Eradication — 악성코드 제거 */
    fun eradicate(case: IncidentCase) {
        case.affectedHosts.forEach { host ->
            edrClient.runFullScan(host)
            edrClient.removeThreats(host, case.iocs.fileHashes)
            patchManager.applyEmergencyPatches(host, case.relatedCVEs)
        }
        // 백도어/지속성 항목 제거 확인
        require(edrClient.scanClean(case.affectedHosts)) {
            "Eradication incomplete — escalate to forensics team"
        }
    }

    /** Phase 4: Recovery — 서비스 복원 (백업 기준) */
    fun recover(case: IncidentCase) {
        val backupPoint = backupService.findLastClean(case.detectionTime)
        case.affectedSystems.forEach { sys ->
            backupService.restore(sys, backupPoint)
            monitoringService.heightenAlerts(sys, Duration.ofDays(14))
        }
        case.status = IncidentStatus.RECOVERING
    }

    /** Phase 5: Lessons Learned — 72시간 내 회고 리포트 */
    fun lessonsLearned(case: IncidentCase): LessonsReport {
        return LessonsReport(
            timeline        = case.buildTimeline(),    // 발생 → 탐지 → 봉쇄 → 복구 타임라인
            rootCause       = case.rootCauseAnalysis,
            mttd            = case.mttdMinutes(),      // Mean Time To Detect
            mttr            = case.mttrMinutes(),      // Mean Time To Respond
            improvements    = case.identifiedGaps,     // 탐지 룰, 패치 주기, 교육 등
            regulatoryNotify= case.gdprNotificationRequired(), // 72시간 통보 여부
        )
    }
}
```

**관련 패턴**: SOAR, SIEM, MITRE ATT&CK Mapping, Audit Log Pattern

---
