# FinOps / 비용 공학 패턴 (FinOps & Cost Engineering Patterns)

FinOps Foundation 표준 + 클라우드 비용 최적화 8 패턴. **비즈니스 가치 / 비용 의 비율** 을 정량 관리. AWS/Azure/GCP 공통 적용.

**원전·표준 참고**:
- FinOps Foundation — *FinOps Framework* (https://www.finops.org)
- J.R. Storment & Mike Fuller — *Cloud FinOps*, 2nd ed. (O'Reilly, 2023)
- AWS Well-Architected Framework — Cost Optimization Pillar
- Google Cloud Cost Management — Active Assist, Recommender
- Microsoft Azure Cost Management

**핵심 원칙**:
- **Visibility before optimization** — 측정 안 되면 줄일 수 없음
- **Ownership** — 엔지니어가 비용을 소유 (DevOps culture 의 일부)
- **Variable cost ≠ infinite** — 클라우드 의 가변 비용은 한도 없이 증가 가능

**관련 카탈로그**:
- [12-factor.md](../principles/12-factor.md) — Disposability, Stateless processes (autoscaling 친화)
- [reliability.md](reliability.md) — Auto-scaling, Backpressure (비용 보호)
- [observability.md](observability.md) — Cost as observable metric

---

## 1. Unit Economics (Unit Cost) <a id="unit-economics"></a>

**목적**: 인프라 총비용을 비즈니스 단위(요청, 사용자, 거래, 주문, 분당 스트리밍 등) 로 나눈 **단위 비용** 을 추적하여, 클라우드 지출이 비즈니스 성장과 정량적으로 정렬되는지 검증합니다.

**특징**:
- 대표 지표: Cost per Request (CPR), Cost per Active User (CPAU), Cost per Transaction (CPT), Cost per GB Egress
- **Gross Margin** = (매출 − COGS(원가, 클라우드 포함)) / 매출. SaaS 는 보통 70~80% 가 건강 영역
- 비용은 사용량과 선형 비례가 아님 — 트래픽 ↑ 일 때 단위 비용 ↓ 가 정상(scale economy), 반대로 ↑ 면 architecture smell
- CUR (AWS Cost and Usage Report), Azure Cost Management Exports, GCP Billing Export → BigQuery 로 집계
- KPI 는 dashboard 에 매일 노출 — 엔지니어 가 자기 서비스 의 CPR 을 외울 정도

**장점**:
- 클라우드 비용 을 **비즈니스 언어** 로 번역 → 경영진·재무 와 공통 어휘 확보
- 비용 회귀 (cost regression) 를 빠르게 감지 — "어제부터 CPR 이 1.4 배" 같은 알람
- 신규 피처 의 ROI 를 사전·사후 비교 가능

**단점·주의**:
- 단위 정의 가 모호하면 의미 없음 (예: "Active User" 의 D1/D7/D30 차이)
- 공유 자원 (DB, ELB) 의 allocation 룰 결정 필요 — tag 기반 분배
- 단기 변동 (캠페인, 트래픽 스파이크) 와 구조적 회귀 를 구분 해야 함

**활용 예시**:
- SaaS 스타트업 의 "$ per MAU" 추적 (CFO 보고용)
- 게임 서버 의 "원/CCU·시간" 비교 (장비 교체 의사결정)
- LLM API 의 "Cost per 1K tokens completed" (모델 라우팅 의사결정)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**메트릭**:
- `cost_per_request` = daily_total_cost / daily_request_count
- `cost_per_active_user` = monthly_total_cost / MAU
- `gross_margin_percent` = (revenue − cogs) / revenue × 100
- `cost_to_revenue_ratio` = cloud_cost / revenue (목표: SaaS 10~15% 미만)

**SQL 예제 (AWS CUR on Athena)**:
```sql
-- 서비스별 일일 Cost per Request 산출
-- CUR 의 line_item_unblended_cost 를 service tag 별로 집계 후
-- CloudWatch 또는 application metrics 의 request_count 와 join
WITH daily_cost AS (
    SELECT
        line_item_usage_start_date AS day,
        resource_tags_user_service  AS service,
        SUM(line_item_unblended_cost) AS cost_usd
    FROM   cur.report
    WHERE  line_item_usage_start_date >= current_date - interval '30' day
      AND  resource_tags_user_env = 'prod'
    GROUP BY 1, 2
),
daily_traffic AS (
    SELECT
        day,
        service,
        SUM(request_count) AS requests
    FROM   metrics.app_requests_daily
    WHERE  day >= current_date - interval '30' day
    GROUP BY 1, 2
)
SELECT
    c.day,
    c.service,
    c.cost_usd,
    t.requests,
    ROUND(c.cost_usd / NULLIF(t.requests, 0) * 1000000, 4)
        AS cost_per_million_requests_usd
FROM   daily_cost c
JOIN   daily_traffic t ON (c.day = t.day AND c.service = t.service)
ORDER BY c.day DESC, cost_per_million_requests_usd DESC;
```

**Kotlin 예제 (단위 비용 알람)**:
```kotlin
data class UnitCostSnapshot(
    val service: String,
    val day: java.time.LocalDate,
    val totalCostUsd: Double,
    val requests: Long,
)

class UnitCostRegressionDetector(private val threshold: Double = 1.30) {
    fun detect(today: UnitCostSnapshot, baseline7d: List<UnitCostSnapshot>): String? {
        val cprToday = today.totalCostUsd / today.requests
        val baselineAvg = baseline7d.map { it.totalCostUsd / it.requests }.average()
        val ratio = cprToday / baselineAvg
        return if (ratio >= threshold)
            "${today.service}: CPR regression ${"%.2f".format(ratio)}x " +
            "(today=${"%.6f".format(cprToday)} vs 7d=${"%.6f".format(baselineAvg)})"
        else null
    }
}
```

**관련 패턴**: [Tagging & Cost Allocation](#tagging-allocation), [FinOps Lifecycle](#finops-lifecycle), [Budget Guardrails](#budget-guardrails)

---

## 2. Rightsizing <a id="rightsizing"></a>

**목적**: 인스턴스/컨테이너/DB 의 실제 사용량(CPU, memory, IOPS, network) 과 프로비저닝된 용량 의 격차를 측정하여 **워크로드 에 맞는 최소 크기** 로 조정합니다. 과대 프로비저닝 (over-provisioning) 은 가장 흔한 cloud waste.

**특징**:
- 관찰 기간: 최소 P95 기준 7~14 일 (주간 패턴 포함). 1 일짜리 데이터 로 결정하면 weekend spike 누락
- 두 차원: **vertical** (instance size 변경 m5.2xlarge → m5.xlarge) + **horizontal** (replica count 조정)
- 클라우드 별 추천 도구:
  - AWS — Compute Optimizer, Trusted Advisor
  - GCP — Active Assist Recommender, VM rightsizing
  - Azure — Advisor Cost recommendations
- 컨테이너: Kubernetes VPA (Vertical Pod Autoscaler) 가 historical usage 기반 권고
- DB: Aurora Serverless v2 / Azure SQL Hyperscale 같은 serverless 모드 로 전환도 rightsizing 의 한 형태

**장점**:
- 평균 20~50% 비용 절감 (FinOps Foundation 사례 평균)
- 즉시 효과 — instance type 변경만으로 다음 청구 부터 반영
- 코드 변경 없음 (infrastructure-only)

**단점·주의**:
- 너무 작게 잡으면 CPU throttle / OOM kill → SLO 위반
- **P95/P99 + headroom 20~30%** 가 안전 마진. average 만 보면 spike 시 장애
- Reserved Instance / Savings Plan 이 걸린 인스턴스 는 변경 시 commitment 손실 검토 필요
- Memory-bound vs CPU-bound 구분 — 잘못된 family 변경은 오히려 비용 증가

**활용 예시**:
- 야간 트래픽이 낮은 batch 워커 의 인스턴스 family 변경 (compute → general purpose)
- 개발/스테이징 환경 의 인스턴스 사이즈 다운그레이드 (prod 와 동일 크기 불필요)
- HPA + VPA 조합 으로 Pod resource 자동 조정

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**메트릭**:
- `cpu_utilization_p95` — 목표 60~70% (여유 30~40%)
- `memory_utilization_p95` — 목표 70~80%
- `rightsizing_savings_potential_usd_monthly` — Compute Optimizer 권고 합계
- `rightsizing_coverage_percent` — 분석된 리소스 / 전체 리소스

**Kubernetes VPA 예제 (YAML)**:
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-server-vpa
  namespace: prod
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  updatePolicy:
    # "Auto" = VPA 가 pod 재시작하며 권고 적용
    # "Off"  = recommendation 만 노출, 적용은 수동 (안전한 시작점)
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
      - containerName: '*'
        minAllowed:
          cpu: 100m
          memory: 256Mi
        maxAllowed:
          cpu: 2000m
          memory: 4Gi
        controlledResources: ["cpu", "memory"]
```

**Terraform 예제 (rightsized EC2)**:
```hcl
# rightsizing 결정 후 m5.2xlarge → m5.xlarge 다운사이즈
# Compute Optimizer 의 "underutilized" 권고 기반
resource "aws_instance" "api_server" {
  # AS-IS: instance_type = "m5.2xlarge"  # CPU p95 = 18%, memory p95 = 35%
  instance_type = "m5.xlarge"             # rightsized — 예상 절감 50%

  ami           = data.aws_ami.al2023.id
  subnet_id     = aws_subnet.private.id

  tags = {
    Name         = "api-server"
    Env          = "prod"
    Rightsized   = "2026-05"
    PreviousType = "m5.2xlarge"
  }
}
```

**관련 패턴**: [Autoscaling Cost Optimization](#autoscaling-cost), [Reserved / Savings Plans](#reserved-savings-plans), [Unit Economics](#unit-economics)

---

## 3. Reserved / Savings Plans / Commitment <a id="reserved-savings-plans"></a>

**목적**: 1~3 년 단위 사용량 약정 (commitment) 의 대가 로 시간당 단가를 최대 ~70% 할인 받습니다. 안정적 baseline 워크로드 에 적용.

**특징**:
- 클라우드 별 약정 상품:
  - AWS — Reserved Instances (RI), Compute Savings Plans (가장 유연), EC2 Instance Savings Plans, SageMaker Savings Plans
  - GCP — Committed Use Discounts (CUD): resource-based, spend-based (Flexible CUD)
  - Azure — Reserved VM Instances, Azure Savings Plans
- 기간 / 결제 옵션:
  - **1 년 No Upfront** — 진입 장벽 낮음, ~30% 할인
  - **3 년 All Upfront** — 최대 할인 (~72%) 이지만 lock-in 크
- 두 핵심 지표:
  - **Coverage** = covered_usage / total_usage — 약정 이 실제 사용량 의 몇 % 를 커버하나
  - **Utilization** = used_commitment / total_commitment — 산 약정 의 몇 % 를 실제 썼나
- 목표: Coverage 70~80% (전부 약정 X — flexibility 마진 남김), Utilization 95%+ (산 건 다 써야 함)

**장점**:
- 안정적 워크로드 에 대해 최대 72% 할인
- 예산 예측성 ↑ (선결제 또는 월정액)
- Compute Savings Plans 는 instance family / region 변경 가능 — RI 보다 유연

**단점·주의**:
- **약정 lock-in 리스크** — 워크로드 가 사라지거나 다른 클라우드 로 이전 시 손실
- 잘못된 사이즈 / family 약정 시 utilization 떨어지면 효과 무 — rightsizing 을 먼저
- Marketplace 재판매 (RI marketplace) 는 가능 하지만 가격 회수 율 낮음
- 신규 인스턴스 family (예: Graviton4) 출시 시 기존 약정 이 발목 잡힐 수 있음

**활용 예시**:
- prod baseline workload 의 70% 를 3 년 Compute Savings Plans 로 커버
- 야간/주말 spike 는 on-demand + Spot 으로 흡수
- 스타트업 초기엔 약정 보류 → 사용 패턴 안정 후 (보통 6~12 개월) 약정

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**메트릭**:
- `savings_plan_coverage_percent` — 목표 70~80%
- `savings_plan_utilization_percent` — 목표 95%+
- `effective_savings_rate_percent` — (on-demand 가격 − 실제 결제) / on-demand 가격
- `commitment_expiry_days` — 만료 90 일 전 부터 갱신 검토

**Terraform 예제 (AWS Savings Plans)**:
```hcl
# AWS Savings Plans 는 Terraform 직접 리소스 가 없어 (구매 = 일회성 액션)
# 보통 AWS Cost Management 콘솔 또는 SDK 로 구매
# 여기서는 RI 의 declarative 예시 + utilization 모니터링 알람

resource "aws_cloudwatch_metric_alarm" "savings_plan_under_utilization" {
  alarm_name          = "savings-plan-utilization-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Utilization"
  namespace           = "AWS/SavingsPlans"
  period              = 86400 # 1 day
  statistic           = "Average"
  threshold           = 90
  alarm_description   = "Savings Plan utilization below 90% — 산 약정을 다 못 쓰고 있음"
  alarm_actions       = [aws_sns_topic.finops_alerts.arn]
}
```

**Python 예제 (Coverage / Utilization 조회)**:
```python
"""
AWS Cost Explorer API 로 Savings Plans Coverage / Utilization 계산
"""
import boto3
from datetime import date, timedelta

ce = boto3.client("ce")
end = date.today()
start = end - timedelta(days=30)

# 1) Coverage — Savings Plan 이 실제 사용량의 몇 % 를 커버했나
cov = ce.get_savings_plans_coverage(
    TimePeriod={"Start": str(start), "End": str(end)},
    Granularity="MONTHLY",
)
for m in cov["SavingsPlansCoverages"]:
    period = m["TimePeriod"]["Start"]
    pct = float(m["Coverage"]["CoveragePercentage"])
    print(f"{period} Coverage: {pct:.1f}%")

# 2) Utilization — 산 commitment 의 몇 % 를 실제 썼나
util = ce.get_savings_plans_utilization(
    TimePeriod={"Start": str(start), "End": str(end)},
    Granularity="MONTHLY",
)
for m in util["SavingsPlansUtilizationsByTime"]:
    period = m["TimePeriod"]["Start"]
    pct = float(m["Utilization"]["UtilizationPercentage"])
    print(f"{period} Utilization: {pct:.1f}%")
    # 90% 미만이면 commitment 가 과다 — 다음 약정 시 축소 검토
```

**관련 패턴**: [Rightsizing](#rightsizing), [Spot Instances](#spot-preemptible), [Unit Economics](#unit-economics)

---

## 4. Spot / Preemptible Instances <a id="spot-preemptible"></a>

**목적**: 클라우드 의 여유 capacity 를 80~90% 할인 가격으로 사용 — 단, 클라우드 가 언제든 회수 (interrupt / preempt) 할 수 있음. **stateless / batch / fault-tolerant** 워크로드 에 적합.

**특징**:
- 클라우드 별 명칭:
  - AWS — Spot Instances (2 분 사전 통지)
  - GCP — Preemptible VMs / Spot VMs (30 초 통지)
  - Azure — Spot Virtual Machines
- **Interruption 신호** 를 미리 받고 graceful shutdown 처리 필수
  - AWS: `http://169.254.169.254/latest/meta-data/spot/instance-action` 폴링
  - GCP: shutdown script 실행
- **Diversification 전략**: 단일 instance type / AZ 에 집중하면 동시 회수 위험 — 여러 family / AZ 로 분산 (Spot Fleet, EC2 Fleet, Karpenter)
- Hybrid: on-demand baseline + Spot 으로 burst 흡수 가 가장 흔한 패턴

**장점**:
- 최대 90% 비용 절감 — 가장 큰 할인 폭
- Stateless / batch workload 에 거의 부작용 없음
- Karpenter / Cluster Autoscaler 가 Spot 자동 관리

**단점·주의**:
- **Stateful / latency-sensitive** 워크로드 부적합 (DB, 사용자 face 트래픽)
- Interrupt 처리 코드 가 없으면 데이터 손실 / 사용자 영향
- Spot 가격 변동 — capacity 수요 폭주 시 가격 급등 또는 capacity 부족
- 검사 / job retry / checkpoint 메커니즘 필요

**활용 예시**:
- Kubernetes 의 stateless API 노드 풀 (graceful drain 으로 회수 처리)
- ML 학습 잡 (checkpoint + resume)
- 영상 인코딩, 데이터 ETL batch
- CI 빌드 러너 (GitHub Actions self-hosted Spot)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**메트릭**:
- `spot_savings_vs_on_demand_percent` — 일반적으로 70~90%
- `spot_interruption_rate_per_day` — instance pool 별 회수 빈도
- `workload_spot_percent` — 워크로드 중 Spot 비중 (목표: stateless 80%+)
- `graceful_drain_success_rate` — interrupt 받고 정상 drain 한 비율

**Karpenter Provisioner 예제 (YAML)**:
```yaml
# Karpenter — Spot diversification 자동 관리
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: spot-pool
spec:
  template:
    spec:
      requirements:
        # capacity-type: spot 우선, 부족하면 on-demand fallback
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        # 다양한 family / size 로 diversification
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
            - m5.large
            - m5a.large
            - m6i.large
            - c5.large
            - c6i.large
        # 여러 AZ 분산
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["us-east-1a", "us-east-1b", "us-east-1c"]
      taints:
        - key: spot
          effect: NoSchedule
  disruption:
    consolidationPolicy: WhenUnderutilized
    expireAfter: 720h # 30 일 후 강제 교체 (long-running node 누적 방지)
```

**Kotlin 예제 (Spot interrupt handler)**:
```kotlin
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.net.URI
import java.time.Duration

/**
 * AWS EC2 Spot interrupt 감지 — instance metadata 의 spot/instance-action 폴링.
 * 2 분 통지 받으면 graceful shutdown 시작.
 */
class SpotInterruptHandler(
    private val onInterrupt: () -> Unit,
) {
    private val client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(1))
        .build()

    private val request = HttpRequest.newBuilder()
        .uri(URI.create("http://169.254.169.254/latest/meta-data/spot/instance-action"))
        .timeout(Duration.ofSeconds(1))
        .GET()
        .build()

    fun pollLoop() {
        while (true) {
            val res = runCatching {
                client.send(request, HttpResponse.BodyHandlers.ofString())
            }.getOrNull()
            // 200 = interrupt 예정 (2 분 후 회수), 404 = 정상
            if (res?.statusCode() == 200) {
                onInterrupt() // drain pod, flush buffer, checkpoint
                return
            }
            Thread.sleep(5_000)
        }
    }
}
```

**관련 패턴**: [Rightsizing](#rightsizing), [Autoscaling Cost Optimization](#autoscaling-cost), [Reserved / Savings Plans](#reserved-savings-plans)

---

## 5. Autoscaling Cost Optimization <a id="autoscaling-cost"></a>

**목적**: 트래픽/부하 의 시간적 패턴에 맞춰 capacity 를 자동으로 늘리고 줄여서 **idle 자원 의 비용** 을 제거합니다. 비용 의 가변화 (variable cost) 가 클라우드 의 본질적 가치.

**특징**:
- 세 가지 스케일링 전략:
  - **Target tracking** — 목표 metric (CPU 60%, RPS 100) 유지 — 가장 일반적, 단순
  - **Step scaling** — 임계치 구간 별 step 크기 정의 — 트래픽 spike 에 빠른 대응
  - **Scheduled scaling** — cron 기반 — 예측 가능한 주기 (출근 시간, 이벤트 시작)
- **Scale-to-zero**: 트래픽 없을 때 0 으로 (serverless, KEDA, Knative). cold start 트레이드오프
- **Predictive scaling** (AWS Predictive, GCP) — ML 기반 사전 예측 (cold start 회피)
- Scale-out 은 빠르게, scale-in 은 천천히 (cooldown) — flapping 방지

**장점**:
- Idle 비용 제거 — 야간 / 주말 / 비수기 자동 축소
- 트래픽 spike 자동 대응 — 사람 개입 불필요
- 비용 의 변동 = 매출 의 변동 과 동조 (unit economics 안정)

**단점·주의**:
- 스케일 임계치 잘못 설정 시 flapping (scale-out/in 반복) — cooldown 필수
- Scale-out 의 cold start 가 latency SLO 침해 — 사전 예측 또는 buffer pool 필요
- Stateful workload (DB, cache) 는 autoscaling 어려움 (replica 동기화)
- License-based SW (코어당 라이선스) 는 scale-out 시 비용 폭증

**활용 예시**:
- Web tier 의 HPA (RPS / CPU 기반)
- Batch 큐 길이 기반 KEDA scale-out (queue empty 시 → 0)
- Lambda / Cloud Run (요청당 과금 = 자동 scale-to-zero)
- DB read replica 의 시간대별 추가/제거

**난이도**: 중간 | **사용 빈도**: ★★★★★

**메트릭**:
- `avg_capacity_utilization_percent` — 목표 60~75% (여유 + flapping 방지)
- `scaling_events_per_day` — 과도하면 (>30) flapping 의심
- `cold_start_p99_ms` — scale-out 시 latency
- `cost_per_request_hourly` — 시간대별 변동 — autoscaling 효과 검증

**HPA + Scheduled Scaling 예제 (YAML)**:
```yaml
# Kubernetes HPA — CPU target tracking
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 3   # baseline (SLO 보장 최소)
  maxReplicas: 50
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 65 # 65% 유지 — 여유 35%
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0   # spike 에 즉시 반응
      policies:
        - type: Percent
          value: 100              # 한번에 최대 2 배
          periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300 # 5 분 안정화 후 축소 (flapping 방지)
      policies:
        - type: Percent
          value: 25               # 한번에 최대 25% 만 축소
          periodSeconds: 60
---
# KEDA — 큐 길이 기반 scale-to-zero
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: worker-scaler
spec:
  scaleTargetRef:
    name: worker-deployment
  minReplicaCount: 0   # 큐 비면 0 까지 — Scale-to-zero
  maxReplicaCount: 30
  triggers:
    - type: aws-sqs-queue
      metadata:
        queueURL: https://sqs.us-east-1.amazonaws.com/123/jobs
        queueLength: "10" # 메시지 10 개당 1 replica
        awsRegion: us-east-1
```

**관련 패턴**: [Spot Instances](#spot-preemptible), [Rightsizing](#rightsizing), [Unit Economics](#unit-economics)

---

## 6. Tagging & Cost Allocation <a id="tagging-allocation"></a>

**목적**: 모든 클라우드 리소스 에 일관된 **tag 분류 체계 (taxonomy)** 를 강제하여, 청구서 를 팀 / 제품 / 환경 / 피처 차원으로 분해 (cost allocation) 합니다. **태그 가 없으면 ownership 도 없음**.

**특징**:
- 표준 tag taxonomy (모든 리소스 강제):
  - **owner** — 팀 이름 (예: `team:platform`, `team:checkout`)
  - **env** — 환경 (`prod`, `staging`, `dev`)
  - **product** — 제품/서비스 (`product:api`, `product:web`)
  - **feature** — 피처 플래그 / 마이크로서비스 (`feature:recommendations`)
  - **cost_center** — 회계 비용 센터 (예: `cc:engineering-platform`)
- **Showback vs Chargeback**:
  - **Showback** — 비용 을 팀별로 *가시화* (책임 의식). 회계 이전 단계
  - **Chargeback** — 비용 을 팀 예산 에서 *실제 차감*. 강한 강제력, 정치적 부담
- 강제 도구:
  - AWS — Tag Policies (Organizations), Service Control Policies (SCP) 로 untagged 차단
  - GCP — Organization Policies, Labels
  - Azure — Azure Policy `Require a tag`
- IaC (Terraform) 의 default_tags 로 일괄 부여

**장점**:
- 청구서 를 비즈니스 차원 으로 분해 (Cost Explorer Group By Tag)
- Untagged 리소스 = ownerless = waste 후보 — 빠른 정리
- Showback dashboard 가 팀에 비용 의식 (cost consciousness) 심음

**단점·주의**:
- Tag taxonomy 가 자주 바뀌면 historical 분석 깨짐 — taxonomy 는 보수적 으로
- 모든 리소스 가 tag-aware 가 아님 (네트워크 transit 비용 등 일부 unallocable)
- Retroactive tagging 어려움 — Day 1 부터 정책 강제 가 핵심
- 너무 많은 tag (>10) 는 운영 부담 — 5~7 개 가 sweet spot

**활용 예시**:
- "Team checkout 의 이번 달 클라우드 지출은 $42K, 전월 대비 +18%" 같은 보고
- Cost anomaly 발생 시 tag drill-down 으로 원인 팀 식별
- 무주 (untagged) 리소스 매월 정리 cron

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**메트릭**:
- `tag_coverage_percent` — 필수 tag 가 채워진 리소스 비율 (목표 95%+)
- `untagged_cost_usd_monthly` — 미할당 비용 (목표 5% 미만)
- `cost_per_team_usd_monthly` — 팀별 분해 비용
- `cost_anomaly_attribution_time_minutes` — 알람 → 책임 팀 식별 까지 소요

**Terraform 예제 (default_tags + tag policy)**:
```hcl
# 모든 리소스 에 자동 부여되는 default_tags
provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Owner       = var.team
      Env         = var.env
      Product     = var.product
      ManagedBy   = "terraform"
      Repo        = "github.com/myorg/${var.repo}"
      CostCenter  = var.cost_center
    }
  }
}

# AWS Organizations Tag Policy — 필수 tag 누락 차단
resource "aws_organizations_policy" "required_tags" {
  name = "require-finops-tags"
  type = "TAG_POLICY"
  content = jsonencode({
    tags = {
      Owner = {
        tag_key   = { "@@assign" = "Owner" }
        tag_value = { "@@assign" = ["team:platform", "team:checkout", "team:ml"] }
        enforced_for = { "@@assign" = ["ec2:instance", "rds:db", "s3:bucket"] }
      }
      Env = {
        tag_key   = { "@@assign" = "Env" }
        tag_value = { "@@assign" = ["prod", "staging", "dev"] }
        enforced_for = { "@@assign" = ["ec2:instance", "rds:db", "s3:bucket"] }
      }
    }
  })
}
```

**SQL 예제 (팀별 Showback)**:
```sql
-- 팀별 월간 비용 분해 — Showback dashboard
SELECT
    DATE_TRUNC('month', line_item_usage_start_date) AS month,
    COALESCE(resource_tags_user_owner, '<untagged>') AS team,
    product_servicecode                              AS service,
    ROUND(SUM(line_item_unblended_cost), 2)          AS cost_usd
FROM   cur.report
WHERE  line_item_usage_start_date >= DATE_TRUNC('month', current_date) - interval '6' month
  AND  resource_tags_user_env = 'prod'
GROUP BY 1, 2, 3
ORDER BY month DESC, cost_usd DESC;
```

**관련 패턴**: [Unit Economics](#unit-economics), [FinOps Lifecycle](#finops-lifecycle), [Budget Guardrails](#budget-guardrails)

---

## 7. FinOps Lifecycle (Inform / Optimize / Operate) <a id="finops-lifecycle"></a>

**목적**: FinOps Foundation 이 정의한 **3 단계 반복 사이클** 로 조직 의 비용 관리 성숙도 를 단계적으로 끌어올립니다. 한 번에 모든 최적화 를 하지 않고 단계별 진화.

**특징**:
- **Phase 1: Inform** — 가시화 단계
  - tag taxonomy 표준화 + 강제
  - 청구 dashboard 구축 (Cost Explorer, Cost Management, Looker Studio)
  - 단위 비용 (CPR, CPAU) 정의 및 baseline 측정
  - 팀별 showback 시작
- **Phase 2: Optimize** — 최적화 단계
  - Rightsizing 시행 (Compute Optimizer 권고 적용)
  - Savings Plans / RI / CUD 구매
  - Spot / Preemptible 전환
  - Autoscaling 도입, scale-to-zero
  - Storage tiering (S3 IA / Glacier 등)
- **Phase 3: Operate** — 정착·자동화 단계
  - 알람·anomaly detection 자동화
  - 정책 (policy-as-code) — Tag policy, Budget policy
  - CI/CD 단계 에서 비용 검증 (Infracost, OpenCost)
  - 월간 FinOps review meeting (Eng + Finance + Product)
- **Maturity 단계 — Crawl / Walk / Run**:
  - **Crawl** — 청구서 만 본다. tag 없음. 절감 ad-hoc
  - **Walk** — tag 강제, dashboard 운영, 약정 시작
  - **Run** — automation, ML-based forecasting, unit economics 가 OKR

**장점**:
- 단계별 진입 — 한 번에 모든 도구 도입 불필요
- 조직 의 현재 위치 (maturity) 진단 가능
- 부서 간 공통 어휘 (Eng + Finance) — FinOps 자체 가 공통 언어

**단점·주의**:
- Inform 없이 Optimize 시도 시 잘못된 곳 을 최적화 — 측정 먼저
- 단계 가 선형 이 아닌 반복 (cycle) — 새 서비스 마다 Inform 부터
- Operate 단계 의 자동화 가 미숙 하면 비용 통제 실패 (anomaly 늦게 발견)

**활용 예시**:
- 스타트업 — Inform 만 (대시보드 + tag)
- 중견 — Walk (Savings Plans 도입, monthly review)
- 대기업 — Run (Infracost CI integration, FinOps team 전담)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**메트릭**:
- `finops_maturity_level` — Crawl / Walk / Run 자체평가
- `forecast_accuracy_percent` — 월말 실측 / 월초 예측 (목표 95%+)
- `optimization_actions_per_quarter` — 분기당 적용한 최적화 수
- `time_to_anomaly_resolution_hours` — 알람 → 조치 완료

**Kotlin 예제 (Lifecycle 자가진단)**:
```kotlin
enum class FinOpsPhase { CRAWL, WALK, RUN }

data class FinOpsMaturitySignals(
    val tagCoveragePercent: Double,
    val savingsPlanCoverage: Double,
    val anomalyDetectionEnabled: Boolean,
    val unitCostInOKR: Boolean,
    val infracostInCi: Boolean,
)

fun assess(s: FinOpsMaturitySignals): FinOpsPhase = when {
    s.tagCoveragePercent < 50 || !s.anomalyDetectionEnabled -> FinOpsPhase.CRAWL
    s.unitCostInOKR && s.infracostInCi && s.savingsPlanCoverage > 70 -> FinOpsPhase.RUN
    else -> FinOpsPhase.WALK
}

fun nextActions(phase: FinOpsPhase): List<String> = when (phase) {
    FinOpsPhase.CRAWL -> listOf(
        "Tag taxonomy 정의 + 강제 정책 적용",
        "Cost Explorer dashboard 구축",
        "단위 비용 baseline 측정 (CPR, CPAU)",
    )
    FinOpsPhase.WALK -> listOf(
        "Compute Savings Plans / CUD 구매 (Coverage 70%)",
        "Rightsizing — Compute Optimizer 권고 적용",
        "Monthly FinOps review meeting 정착",
    )
    FinOpsPhase.RUN -> listOf(
        "Infracost CI integration — PR 단계 비용 검증",
        "ML 기반 anomaly detection — Cost Anomaly Detection 활성",
        "Unit cost 를 팀 OKR 로 — Cost per Request 분기 목표",
    )
}
```

**관련 패턴**: [Unit Economics](#unit-economics), [Tagging & Cost Allocation](#tagging-allocation), [Budget Guardrails](#budget-guardrails)

---

## 8. Budget Guardrails & Anomaly Detection <a id="budget-guardrails"></a>

**목적**: 비용 이 임계치 / 예측치 를 벗어나면 **알람** 또는 **자동 차단** 으로 폭주 (runaway cost) 를 방어합니다. 클라우드 의 가변 비용 은 한도 없이 증가 가능 — guardrail 이 없으면 사고 한 건 으로 월 예산 의 수 배 결제 가능.

**특징**:
- **Budget alerts** — 절대값 또는 예측 기반 임계 (50/80/100/120%) 도달 시 SNS/Slack/Email
- **Hard caps** — 일정 한도 초과 시 자동 조치:
  - 신규 리소스 생성 차단 (SCP / IAM policy)
  - 비핵심 워크로드 자동 종료 (Lambda + tag 기반)
- **ML-based Anomaly Detection** — 시계열 정상 패턴 학습 후 이탈 감지
  - AWS Cost Anomaly Detection (무료, SageMaker 기반)
  - GCP Recommender, Azure Anomaly Detection
- **Detection scope** — service 단위 / linked account 단위 / tag (cost category) 단위
- Sandbox / dev account 는 더 엄격한 hard cap (예: 일 $50)

**장점**:
- 한 건 의 사고 (오설정 EC2, 무한 루프 Lambda, exfiltration) 를 분 단위 로 차단
- ML 기반 detection 은 임계치 수동 조정 불필요
- Sandbox / dev 의 폭주 를 prod 와 격리

**단점·주의**:
- False positive — 캠페인 / 마이그레이션 같은 정당한 spike 가 알람
- Detection latency — 보통 24 시간 지연 (CUR 일 1 회 갱신) → 분 단위 감지 어려움
- Hard cap 이 너무 빡빡 하면 정상 운영 차단 (예: prod 에서 신규 리소스 못 만듦)
- Anomaly root cause 분석 은 여전히 사람 일

**활용 예시**:
- 월 예산 80% 도달 시 Slack 알람
- Dev account 의 일 $100 hard cap (초과 시 신규 EC2 생성 차단)
- ML anomaly — 특정 서비스 의 일 비용 이 3σ 이탈 시 자동 ticket 생성
- Forgotten resources — 30 일 이상 untouched + tag 없는 리소스 자동 정리 ticket

**난이도**: 중간 | **사용 빈도**: ★★★★★

**메트릭**:
- `budget_burn_rate_percent` — 월 예산 의 몇 % 를 며칠 만에 소진했나
- `anomaly_alerts_per_month` — 너무 많으면 (>20) threshold 재조정 필요
- `forecasted_month_end_cost_usd` — AWS Cost Forecasting 기반 월말 예측
- `time_to_remediate_anomaly_hours` — 알람 → 원인 해결

**Terraform 예제 (Budget + Anomaly Detection)**:
```hcl
# AWS Budget — 월 예산 + 임계 알람 (50/80/100/120%)
resource "aws_budgets_budget" "monthly_cost" {
  name              = "monthly-cost-budget"
  budget_type       = "COST"
  limit_amount      = "10000"
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = "2026-01-01_00:00"

  dynamic "notification" {
    for_each = [50, 80, 100, 120]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = notification.value >= 100 ? "ACTUAL" : "FORECASTED"
      subscriber_email_addresses = ["finops@example.com"]
      subscriber_sns_topic_arns  = [aws_sns_topic.finops_alerts.arn]
    }
  }
}

# AWS Cost Anomaly Detection — ML 기반 이상 탐지
resource "aws_ce_anomaly_monitor" "service_monitor" {
  name              = "service-anomaly-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_ce_anomaly_subscription" "alerts" {
  name             = "anomaly-alerts"
  frequency        = "IMMEDIATE"
  monitor_arn_list = [aws_ce_anomaly_monitor.service_monitor.arn]
  subscriber {
    type    = "SNS"
    address = aws_sns_topic.finops_alerts.arn
  }
  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      match_options = ["GREATER_THAN_OR_EQUAL"]
      values        = ["500"] # $500 이상 이탈 만 알람
    }
  }
}

# Sandbox account hard cap — Lambda + EventBridge 로 일 $50 초과 시 EC2 종료
resource "aws_budgets_budget" "sandbox_hard_cap" {
  name              = "sandbox-daily-hardcap"
  budget_type       = "COST"
  limit_amount      = "50"
  limit_unit        = "USD"
  time_unit         = "DAILY"
  time_period_start = "2026-01-01_00:00"

  cost_filter {
    name   = "LinkedAccount"
    values = ["111122223333"] # sandbox account id
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_sns_topic_arns  = [aws_sns_topic.sandbox_killswitch.arn]
  }
}
```

**Python 예제 (Anomaly 자동 ticket)**:
```python
"""
AWS Cost Anomaly Detection 의 SNS 알람 을 Lambda 로 처리:
ticket 생성 + Slack 알림 + tag 기반 책임 팀 식별
"""
import json
import os
import urllib.request

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]

def lambda_handler(event, context):
    for record in event["Records"]:
        anomaly = json.loads(record["Sns"]["Message"])
        service   = anomaly.get("dimensionValue", "unknown")
        impact    = float(anomaly.get("impact", {}).get("totalImpact", 0))
        root_cause = anomaly.get("rootCauses", [{}])[0]
        linked_account = root_cause.get("linkedAccount", "unknown")
        usage_type    = root_cause.get("usageType", "unknown")

        text = (
            f":rotating_light: *Cost Anomaly Detected*\n"
            f"> Service: `{service}`\n"
            f"> Account: `{linked_account}`\n"
            f"> Usage Type: `{usage_type}`\n"
            f"> Impact: *${impact:,.2f}*\n"
            f"> Action: Investigate within 24h — assign to service owner via Tag `Owner`."
        )
        payload = json.dumps({"text": text}).encode()
        req = urllib.request.Request(
            SLACK_WEBHOOK,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    return {"status": "ok"}
```

**관련 패턴**: [Unit Economics](#unit-economics), [Tagging & Cost Allocation](#tagging-allocation), [FinOps Lifecycle](#finops-lifecycle)

---

## 패턴 선택 가이드

| 상황 | 우선 검토할 패턴 |
|---|---|
| FinOps 처음 시작 | [Tagging & Cost Allocation](#tagging-allocation) → [Unit Economics](#unit-economics) → [FinOps Lifecycle](#finops-lifecycle) |
| 청구서 가 갑자기 2 배 | [Budget Guardrails](#budget-guardrails) + [Tagging](#tagging-allocation) 으로 책임 팀 식별 |
| 즉시 절감 (30 일 내) | [Rightsizing](#rightsizing) — 코드 변경 없이 사이즈 다운 |
| 6 개월 이상 안정 워크로드 | [Reserved / Savings Plans](#reserved-savings-plans) — Coverage 70% 목표 |
| Batch / stateless 워크로드 | [Spot Instances](#spot-preemptible) — 80~90% 절감 |
| 트래픽 가 시간대별 편차 큼 | [Autoscaling Cost Optimization](#autoscaling-cost) — scale-to-zero 검토 |
| 팀별 비용 책임 부여 | [Tagging](#tagging-allocation) Showback → Chargeback |
| 비용 사고 재발 방지 | [Budget Guardrails](#budget-guardrails) + Anomaly Detection |

## 안티패턴 (피해야 할 것)

- **Optimize before Inform** — tag/dashboard 없이 절감부터 시도 → 잘못된 곳 최적화
- **모든 워크로드 100% Savings Plans 커버** — flexibility 마진 없음, 워크로드 변경 시 손실
- **Stateful 워크로드 에 Spot** — DB / 사용자 face traffic 은 절대 금지
- **Untagged 리소스 방치** — ownerless = waste. tag policy 로 Day 1 부터 강제
- **Anomaly 만 보고 root cause 분석 생략** — automation 이 사람 일 을 대체 하지 않음
- **Budget alert 만 두고 hard cap 없음** — 알람 무시 시 사고 폭주
- **단위 비용 정의 모호** — "Active User" 가 D1 인지 D30 인지 합의 안 됨

---

**카탈로그 갱신 시 체크리스트**:
- [ ] 새 패턴 추가 시 anchor `<a id="kebab-name"></a>` 부여
- [ ] **목적 / 특징 / 장점 / 단점·주의 / 활용 예시 / 메트릭 / 코드 예제 / 관련 패턴** 8 블록 모두 포함
- [ ] 클라우드 공급자 (AWS / GCP / Azure) 별 명칭 차이 명시
- [ ] 패턴 선택 가이드 표 갱신
- [ ] index.md (`references/patterns/index.md`) 의 카테고리 색인 업데이트
