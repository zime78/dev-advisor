# 워크플로우·잡 실행 패턴 (Workflow & Job Execution Patterns)

비동기 작업·장기 실행 워크플로우 정평 있는 9 패턴. **단발 잡** (Queue) 부터 **다단계 분산 워크플로우** (Temporal) 까지. Temporal / Airflow / Argo / Sidekiq / Celery / Quartz / DBOS 사례.

**원전·표준 참고**:
- Temporal Documentation — https://docs.temporal.io
- Apache Airflow — https://airflow.apache.org
- Argo Workflows — https://argoproj.github.io/argo-workflows/
- Sidekiq Documentation, Celery Documentation
- Maxim Fateev (Temporal CEO) — *Designing a Workflow Engine* (talks)
- Akka Persistence / Lagom Event Sourcing (durable workflow 변형)

**핵심 분류**:
- **Code-as-workflow** vs **DAG-as-workflow** — Temporal vs Airflow
- **Push** vs **Pull** queue — SQS push notification vs Sidekiq pull
- **One-shot job** vs **Long-running workflow** — 5 분 작업 vs 30 일 retry 가능

**관련 카탈로그**:
- [distributed.md](distributed.md) — Saga (Choreography/Orchestration) — workflow 관점은 본 파일
- [integration.md](integration.md) — Process Manager / Routing Slip (EIP 관점)
- [reliability.md](reliability.md) — Retry / Timeout / Idempotency Key

---

<a id="durable-workflow"></a>
## 1. Durable Workflow (지속성 워크플로우)

**목적**: 워크플로우 실행 상태를 이벤트 시퀀스로 영속화하고, 장애·재시작 후 replay 로 동일 지점에서 재개합니다. Temporal / Cadence / DBOS 의 핵심 모델.

**메커니즘**:
- 워크플로우 코드는 일반 프로그래밍 언어로 작성 (code-as-workflow)
- 워커가 각 단계 결과를 **Event History** 에 append-only 로 기록
- 재시작 시 History 를 처음부터 replay 하여 결정론적으로 동일 상태 복원
- **Determinism 강제**: `System.currentTimeMillis()` / `UUID.randomUUID()` / `random` / 외부 I/O 직접 호출 금지 — replay 때 다른 값이 나오면 history 와 불일치
- 이런 비결정적 작업은 **Activity** (별도 메서드, 결과를 history 에 기록) 로 분리

**장점**:
- 워크플로우를 **일반 코드** 처럼 작성 (if/else/loop/try-catch) — DSL 학습 불필요
- 장기 실행 (수일~수개월) 가능 — 프로세스 죽어도 다른 워커가 이어받음
- 자동 재시도·타임아웃·취소를 SDK 가 처리
- 시간 여행 디버깅·감사 로그 자동

**단점·주의**:
- **Determinism 위반은 silent bug** — 코드 리뷰·정적 검사 필수
- Event History 크기 제한 (Temporal 50K event / 50MB) → 큰 워크플로우는 Continue-As-New 로 분할
- 로컬 변수·정적 필드·전역 상태 사용 시 replay 깨짐
- 학습 곡선 가파름 (Activity vs Workflow 경계, signal/query, side-effect)

**활용 예시**:
- Temporal.io 워크플로우 (Uber, Snap, Coinbase 등 운영)
- Cadence (Uber 원조)
- Microsoft Durable Functions
- DBOS (PostgreSQL 기반 신생)
- 결제 청구·구독 갱신·여행 예약 (다단계 + 보상)

**Kotlin 예제 (Temporal SDK)**:
```kotlin
import io.temporal.workflow.*
import io.temporal.activity.*
import java.time.Duration

@WorkflowInterface
interface OrderWorkflow {
    @WorkflowMethod
    fun process(orderId: String): String
}

@ActivityInterface
interface OrderActivities {
    fun charge(orderId: String): String     // 외부 결제 게이트웨이 호출
    fun ship(orderId: String): String       // 배송 시스템 호출
    fun refund(orderId: String): Unit       // 보상 트랜잭션
}

class OrderWorkflowImpl : OrderWorkflow {
    // 결정론적 — Activity stub 만 보유, 외부 호출 없음
    private val activities = Workflow.newActivityStub(
        OrderActivities::class.java,
        ActivityOptions.newBuilder()
            .setStartToCloseTimeout(Duration.ofMinutes(5))
            .setRetryOptions(RetryOptions.newBuilder().setMaximumAttempts(3).build())
            .build()
    )

    override fun process(orderId: String): String {
        // 비결정적 작업(시간·랜덤·HTTP) 은 Activity 로 위임
        val chargeId = activities.charge(orderId)
        try {
            // Workflow 가 죽어도 다른 워커가 history replay 로 이 지점에서 재개
            Workflow.sleep(Duration.ofHours(1))  // 결정론적 sleep — SDK 가 처리
            return activities.ship(orderId)
        } catch (e: ActivityFailure) {
            activities.refund(orderId)            // 보상
            throw e
        }
    }
}

// 금지 예시 — 워크플로우 안에서 직접 호출 시 replay 깨짐
// val now = System.currentTimeMillis()    // X — Workflow.currentTimeMillis() 사용
// val id = UUID.randomUUID()              // X — Workflow.randomUUID() 또는 Activity 위임
// httpClient.get("...")                   // X — Activity 로 분리 필수
```

**관련 패턴**: [Saga (Workflow)](#saga-workflow), [Long-Running Activity](#long-running-activity), [Workflow Versioning](#workflow-versioning), Event Sourcing ([distributed.md](distributed.md))

---

<a id="dag-workflow"></a>
## 2. DAG-based Workflow (DAG 기반 워크플로우)

**목적**: 작업을 노드, 의존 관계를 엣지로 표현한 **방향성 비순환 그래프 (DAG)** 로 워크플로우를 정의합니다. 스케줄러가 의존성 충족 시 다음 노드를 실행. Airflow / Argo Workflows / Dagster / Prefect.

**메커니즘**:
- 워크플로우 = DAG (Python / YAML / Jsonnet 으로 선언)
- **Scheduler** 가 cron / 이벤트 트리거로 DAG run 시작
- 각 task 는 의존하는 task 가 success 면 실행, fail 이면 downstream skip
- **Backfill**: 과거 시점 DAG run 재실행 (스케줄 도입 전 데이터 채우기)
- **XCom / Artifact**: task 간 작은 데이터 전달 (큰 데이터는 외부 스토리지)

**장점**:
- 데이터 파이프라인 시각화 자연스러움 (UI 가 곧 그래프)
- Operator 생태계 풍부 (S3 / BigQuery / Spark / dbt 등 즉시 사용)
- 재실행·backfill·SLA 모니터링 내장
- DAG 자체를 코드 (PR) 로 리뷰 가능

**단점·주의**:
- **단기 실행에 최적** — task 가 분 단위 ~ 수시간. Temporal 같은 일·주 단위 stateful 워크플로우 부적합
- **Dynamic DAG** (런타임 task 수 결정) 은 어색 — Airflow 는 일부 지원, Argo 는 withItems 로 정적 fan-out
- task 간 큰 데이터는 외부 스토리지 필요 (XCom 제한)
- Airflow scheduler 가 자체 병목 (수천 DAG 시)

**활용 예시**:
- ETL / ELT 파이프라인 (Airflow, Dagster, Prefect)
- ML 학습 파이프라인 (Kubeflow Pipelines, Argo)
- CI/CD 빌드 그래프 (Argo Workflows)
- 매일 새벽 데이터 마트 빌드

**Python 예제 (Apache Airflow)**:
```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

def extract(**ctx):
    # S3 / DB 추출
    return {"rows": 1000}

def transform(**ctx):
    payload = ctx["ti"].xcom_pull(task_ids="extract")  # 이전 task 결과
    return payload["rows"] * 2

def load(**ctx):
    transformed = ctx["ti"].xcom_pull(task_ids="transform")
    print(f"Loaded {transformed} rows")

with DAG(
    dag_id="daily_etl",
    schedule="0 2 * * *",           # 매일 02:00
    start_date=datetime(2026, 1, 1),
    catchup=False,                   # 과거 미실행분 backfill 비활성
    default_args=default_args,
    tags=["etl"],
) as dag:
    t_extract   = PythonOperator(task_id="extract",   python_callable=extract)
    t_transform = PythonOperator(task_id="transform", python_callable=transform)
    t_load      = PythonOperator(task_id="load",      python_callable=load)

    # 의존성 = DAG 엣지
    t_extract >> t_transform >> t_load
```

**YAML 예제 (Argo Workflows)**:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: ml-pipeline-
spec:
  entrypoint: pipeline
  templates:
  - name: pipeline
    dag:
      tasks:
      - name: extract
        template: run-script
        arguments: { parameters: [{ name: cmd, value: "python extract.py" }] }
      - name: train
        dependencies: [extract]
        template: run-script
        arguments: { parameters: [{ name: cmd, value: "python train.py" }] }
      - name: evaluate
        dependencies: [train]
        template: run-script
        arguments: { parameters: [{ name: cmd, value: "python eval.py" }] }
  - name: run-script
    inputs:
      parameters: [{ name: cmd }]
    container:
      image: python:3.11
      command: [sh, -c]
      args: ["{{inputs.parameters.cmd}}"]
```

**관련 패턴**: [Durable Workflow](#durable-workflow), [Scheduled Job](#scheduled-job-cron), Pipes & Filters ([integration.md](integration.md))

---

<a id="job-queue"></a>
## 3. Job Queue (잡 큐)

**목적**: 비동기 단발 작업을 큐에 enqueue 하고 워커 풀이 dequeue 하여 처리합니다. **Push** (브로커가 워커에 전달) 와 **Pull** (워커가 polling) 두 모델. Sidekiq / Celery / BullMQ / Resque / Hangfire.

**메커니즘**:
- **Producer**: 작업을 직렬화하여 큐에 push (예: `OrderEmailJob.perform_async(order_id)`)
- **Worker pool**: 큐를 폴링·dequeue 하여 작업 실행 (Sidekiq = Redis BRPOP, Celery = RabbitMQ basic.get)
- **Retry**: 실패 시 지수 백오프로 retry queue 에 재삽입 (Sidekiq 25회 / 21일)
- **Dead Letter / Morgue**: 최대 재시도 초과 시 별도 영역 보관
- **Priority queue**: critical / default / low 다중 큐 가중치 폴링

**장점**:
- 웹 요청 → 응답 시간 단축 (느린 작업은 큐로 offload)
- 워커 수평 확장으로 처리량 선형 증가
- 실패 격리 (한 작업 실패가 큐 전체를 막지 않음)
- 운영 도구 풍부 (Sidekiq Web, Flower)

**단점·주의**:
- **Exactly-once 미보장** — 워커 crash 시 재실행 가능 → idempotency 필수 ([Idempotent Worker](#idempotent-worker) 참조)
- 작업 인자 직렬화 제약 (Sidekiq = JSON, Celery = pickle / json)
- 큐가 백로그 쌓이면 DB / API 폭주 (백프레셔 / Rate Limiter 필요)
- 작업 간 의존성 표현 어려움 — DAG 워크플로우 필요시 [DAG Workflow](#dag-workflow)

**활용 예시**:
- 이메일 / 푸시 발송
- 이미지·비디오 비동기 처리
- 청구서 PDF 생성
- 외부 API 후처리 (CRM 동기화, Slack 알림)

**Ruby 예제 (Sidekiq)**:
```ruby
# 워커 정의 — perform 메서드만 구현
class OrderEmailWorker
  include Sidekiq::Worker
  sidekiq_options queue: "default", retry: 5, dead: true

  def perform(order_id, template)
    order = Order.find(order_id)
    # 멱등성 보장 — 이미 보냈으면 skip
    return if order.email_sent_at.present?

    Mailer.send(order, template).deliver_now
    order.update!(email_sent_at: Time.current)
  end
end

# Producer (예: Rails controller)
OrderEmailWorker.perform_async(order.id, "confirmation")
# 지연 실행
OrderEmailWorker.perform_in(1.hour, order.id, "reminder")
```

**Python 예제 (Celery)**:
```python
from celery import Celery
from celery.exceptions import MaxRetriesExceededError

app = Celery("tasks", broker="redis://localhost:6379/0")

@app.task(bind=True, max_retries=5, default_retry_delay=60)
def send_order_email(self, order_id: int, template: str):
    try:
        order = Order.objects.get(id=order_id)
        if order.email_sent_at:           # 멱등성 가드
            return "already_sent"
        Mailer.send(order, template)
        order.email_sent_at = now()
        order.save()
    except MaxRetriesExceededError:
        # DLQ 로 보내거나 운영 알림
        raise
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# Producer
send_order_email.delay(order.id, "confirmation")
send_order_email.apply_async((order.id, "reminder"), countdown=3600)
```

**관련 패턴**: [Idempotent Worker](#idempotent-worker), [Worker Leasing](#worker-leasing), Competing Consumers / DLQ ([integration.md](integration.md))

---

<a id="saga-workflow"></a>
## 4. Saga (워크플로우 관점)

**목적**: 분산 트랜잭션을 다단계로 실행하고, 중간 단계 실패 시 **보상 트랜잭션 (compensating action)** 으로 역방향 롤백합니다. 워크플로우 엔진 (Temporal / Camunda / Step Functions) 으로 구현 시 보상 체인이 코드 흐름 자체로 표현됨.

> **참고**: 본 항목은 **워크플로우 엔진 구현 관점**. 분산 시스템의 Choreography vs Orchestration 비교는 [distributed.md §3, §4](distributed.md) 참조. EIP 의 Process Manager 와 유사하나 보상 로직이 핵심.

**메커니즘**:
- 각 단계 = (forward action, compensating action) 쌍
- Orchestrator (또는 워크플로우 코드) 가 순차 실행
- N 번째 단계 실패 시 1..N-1 단계의 보상 액션을 **역순** 호출
- 보상도 **idempotent** 해야 함 (보상 자체가 실패·재시도 가능)
- 비즈니스 의미상 **roll-forward** (다른 경로로 완료) 도 선택지

**장점**:
- 마이크로서비스 간 2PC (XA) 불필요
- 각 단계가 자기 DB 의 로컬 트랜잭션만 사용
- 워크플로우 엔진 사용 시 보상 로직 명시화·추적 용이

**단점·주의**:
- **Isolation 없음** — 보상 중 다른 트랜잭션이 중간 상태를 관찰 가능 (semantic lock 필요)
- 보상 액션 설계가 도메인 의존적 (환불 vs 차감 무효화 vs 알림만)
- 보상 실패 시 처리 정책 (수동 개입, alert, DLQ)
- "취소했는데 이미 배송 시작" — 시간 의존성 고려 필수

**활용 예시**:
- 여행 예약 (항공 + 호텔 + 렌터카) — 호텔 실패 시 항공 취소
- 주문 처리 (재고 차감 + 결제 + 배송 예약)
- 구독 가입 (계정 생성 + 결제 + 권한 부여)

**Kotlin 예제 (Temporal Saga)**:
```kotlin
import io.temporal.workflow.*
import io.temporal.activity.*

@ActivityInterface
interface TravelActivities {
    fun reserveFlight(req: BookingRequest): String
    fun cancelFlight(reservationId: String)
    fun reserveHotel(req: BookingRequest): String
    fun cancelHotel(reservationId: String)
    fun chargePayment(req: BookingRequest): String
    fun refundPayment(paymentId: String)
}

class TravelBookingWorkflowImpl : TravelBookingWorkflow {
    private val activities = Workflow.newActivityStub(TravelActivities::class.java, /* opts */)

    override fun book(req: BookingRequest): BookingResult {
        // Temporal SDK 내장 Saga — 보상 등록 후 실패 시 역순 호출
        val saga = Saga(Saga.Options.Builder().setParallelCompensation(false).build())
        try {
            val flightId = activities.reserveFlight(req)
            saga.addCompensation { activities.cancelFlight(flightId) }

            val hotelId = activities.reserveHotel(req)
            saga.addCompensation { activities.cancelHotel(hotelId) }

            val paymentId = activities.chargePayment(req)
            saga.addCompensation { activities.refundPayment(paymentId) }

            return BookingResult(flightId, hotelId, paymentId)
        } catch (e: Exception) {
            // 보상 역순 실행 — Temporal 이 retry / 영속성 보장
            saga.compensate()
            throw e
        }
    }
}
```

**관련 패턴**: [Durable Workflow](#durable-workflow), Saga Choreography/Orchestration ([distributed.md §3, §4](distributed.md)), Process Manager ([integration.md §14](integration.md))

---

<a id="scheduled-job-cron"></a>
## 5. Scheduled Job (스케줄드 잡 / Cron)

**목적**: 시간 기반 트리거 (cron expression, 고정 간격, 특정 시각) 로 작업을 자동 실행합니다. Unix cron / Quartz / Kubernetes CronJob / `node-cron` / Sidekiq-cron.

**메커니즘**:
- **Cron expression**: `분 시 일 월 요일` (5 또는 6 필드). 예) `0 2 * * *` = 매일 02:00
- 스케줄러가 매 분 (또는 더 자주) wake up → 매칭되는 잡 launch
- **Missed schedule policy**: 시스템 다운 중 스케줄 누락 시 처리 (skip / catch-up / startingDeadline)
- **Time zone**: UTC vs 로컬 — DST 전환 시 hour 2 회 / 0 회 실행 이슈
- **Jitter**: 동시 실행 부하 분산 (모든 인스턴스가 정각에 트리거 안 하도록 ±30s 무작위 지연)

**장점**:
- 운영 자동화 (백업, 리포트, 정리)
- 외부 트리거 (queue 메시지·이벤트) 불필요
- cron expression 으로 정밀 스케줄 표현

**단점·주의**:
- **Time zone 함정** — `0 3 * * *` UTC 인지 KST 인지 명시 필수. DST 적용 region 은 매년 2회 검증
- **Missed schedule** 정책 미설정 시 시스템 복구 후 폭주 (catch-up 누적 실행) 가능 — k8s `startingDeadlineSeconds` 필수
- **다중 인스턴스 중복 실행** — 단일 leader 필요 (DB lock / k8s CronJob singleton / Quartz cluster)
- 정각 시각에 외부 API 폭주 → **Jitter** 권장

**활용 예시**:
- 매일 새벽 백업 / 보고서 생성
- 주간 청구서 발송
- 만료 토큰 정리 (cleanup job)
- Kubernetes CronJob (`schedule: "*/15 * * * *"`)
- Quartz scheduler (Java enterprise)

**Kotlin 예제 (Quartz)**:
```kotlin
import org.quartz.*
import org.quartz.impl.StdSchedulerFactory
import java.util.TimeZone

class DailyReportJob : Job {
    override fun execute(context: JobExecutionContext) {
        val runId = context.fireInstanceId  // 멱등성 키로 활용 가능
        // 보고서 생성 — idempotent 하게 작성
        ReportService.generateDaily(runId)
    }
}

fun scheduleDailyReport() {
    val scheduler = StdSchedulerFactory.getDefaultScheduler()
    scheduler.start()

    val job = JobBuilder.newJob(DailyReportJob::class.java)
        .withIdentity("dailyReport", "reports")
        .build()

    val trigger = TriggerBuilder.newTrigger()
        .withIdentity("dailyReportTrigger", "reports")
        // 매일 02:00 KST, misfire 시 즉시 1회 실행 후 정상 스케줄 복귀
        .withSchedule(
            CronScheduleBuilder.cronSchedule("0 0 2 * * ?")
                .inTimeZone(TimeZone.getTimeZone("Asia/Seoul"))
                .withMisfireHandlingInstructionFireAndProceed()
        )
        .build()

    scheduler.scheduleJob(job, trigger)
}
```

**YAML 예제 (Kubernetes CronJob)**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-cleanup
spec:
  schedule: "0 3 * * *"               # 매일 03:00 UTC
  timeZone: "Asia/Seoul"               # k8s 1.27+ 명시 가능
  concurrencyPolicy: Forbid            # 이전 실행 미완료 시 신규 skip
  startingDeadlineSeconds: 600         # 10 분 내 시작 못 하면 missed 처리
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: cleanup
            image: cleanup-tool:1.4.0
            command: ["python", "/app/cleanup.py", "--mode=expired-tokens"]
```

**관련 패턴**: [Job Queue](#job-queue), [Idempotent Worker](#idempotent-worker), [Worker Leasing](#worker-leasing)

---

<a id="worker-leasing"></a>
## 6. Worker Leasing / Visibility Timeout (워커 리스 / 가시성 타임아웃)

**목적**: 메시지 큐에서 워커가 작업을 **임대 (lease)** 하는 동안 다른 워커에게는 보이지 않게 (invisible) 만들고, 정해진 timeout 내에 ack 가 없으면 자동 재가시화하여 다른 워커가 재처리합니다. SQS / Pub/Sub / Kafka rebalance / RabbitMQ ack 의 공통 모델.

**메커니즘**:
- 워커가 `receive` → 메시지가 lease 상태로 전환, **visibility timeout** 시작 (예: SQS 기본 30초)
- 워커가 timeout 내에 `ack` (delete) → 메시지 영구 삭제
- 워커가 timeout 내에 ack 못 함 (crash, OOM, GC pause) → 메시지 재가시화 → 다른 워커가 receive
- 처리 시간이 길면 워커가 주기적으로 `extend` 호출하여 lease 연장
- 결과: **at-least-once delivery** — 중복 처리 가능성 항상 존재 → idempotency 필수

**장점**:
- 워커 crash 시 작업 손실 없음 (자동 재할당)
- 운영자가 워커 추가/제거 자유로움
- 명시적 ack 로 처리 완료 보장

**단점·주의**:
- **Visibility timeout 튜닝 난이도** — 너무 짧으면 정상 작업도 중복 실행, 너무 길면 crash 후 재처리 지연
- 처리 시간 분산 큰 경우 — heartbeat / extend 패턴 필요
- **Poison pill** — 항상 실패하는 메시지가 무한 재시도. max receive count + DLQ 필수
- 워커가 timeout 직전 ack 했는데 네트워크 지연으로 재처리 → 멱등성으로 흡수

**활용 예시**:
- AWS SQS `VisibilityTimeout` (기본 30s, 최대 12h)
- Google Pub/Sub `ackDeadlineSeconds` (10s ~ 600s)
- Kafka consumer `max.poll.interval.ms` + rebalance
- RabbitMQ manual ack + consumer prefetch
- Temporal Activity heartbeat (long-running)

**Python 예제 (AWS SQS)**:
```python
import boto3
import time

sqs = boto3.client("sqs")
QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/123/orders"

def worker_loop():
    while True:
        resp = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,           # long polling
            VisibilityTimeout=60,          # 60초 동안 다른 워커에 invisible
        )
        for msg in resp.get("Messages", []):
            try:
                # 긴 작업이면 주기적으로 visibility 연장
                process_with_heartbeat(msg)

                # 성공 시 명시적 ack (삭제) — 미호출 시 60초 후 다른 워커가 재처리
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
            except PoisonMessageError:
                # DLQ 로 명시 이동 (또는 redrive policy 가 자동 처리)
                pass
            except Exception:
                # ack 하지 않음 → visibility timeout 후 재처리
                # max receive count 초과 시 DLQ 자동 이동
                pass

def process_with_heartbeat(msg):
    receipt = msg["ReceiptHandle"]
    deadline = time.time() + 300         # 최대 5분 처리 예상
    while time.time() < deadline:
        # 30초마다 visibility 60초 연장 (lease extension)
        sqs.change_message_visibility(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=receipt,
            VisibilityTimeout=60,
        )
        if do_chunk(msg):                # 작업 한 청크 처리
            return                        # 완료
        time.sleep(30)
    raise TimeoutError("processing exceeded budget")
```

**관련 패턴**: [Idempotent Worker](#idempotent-worker), [Long-Running Activity](#long-running-activity), DLQ / Competing Consumers ([integration.md](integration.md))

---

<a id="idempotent-worker"></a>
## 7. Idempotent Worker (멱등 워커)

**목적**: at-least-once delivery 환경에서 동일 메시지가 중복 도착해도 **부작용이 한 번만** 발생하도록 워커를 설계합니다. Job Queue / Worker Leasing 의 전제 조건.

**메커니즘**:
- 메시지에 **dedup key** (예: `messageId`, `idempotencyKey`, 비즈니스 키) 포함
- 워커는 처리 전 dedup store (Redis SET, DB unique index) 조회 → 이미 있으면 skip
- 또는 **자연 멱등성** 활용: `UPDATE ... WHERE status = 'pending'`, `INSERT ... ON CONFLICT DO NOTHING`
- dedup 결과 (성공/실패) 도 함께 저장하여 재요청 시 동일 응답 반환 가능
- TTL 로 dedup 키 만료 정책 설정 (메시지 retry 윈도우보다 길게)

**장점**:
- at-least-once 환경에서도 비즈니스 무결성 보장
- 운영 중 수동 재실행·재처리 안전
- Outbox / Saga 와 결합 자연스러움

**단점·주의**:
- dedup store 의 일관성·가용성이 워커 정확성에 직결
- **TTL 만료 후 늦은 중복** 처리 위험 (TTL 정책 신중)
- dedup 키 설계 실패 시 효과 없음 — payload hash vs business key 선택
- 외부 시스템 호출은 idempotent 하지 않을 수 있음 — provider 측 idempotency key 활용 (Stripe 등)

**활용 예시**:
- 결제 워커 (Stripe `Idempotency-Key` 헤더 + 내부 dedup)
- 이메일 발송 (수신자별 hash 로 dedup)
- 외부 시스템 동기화 (CRM upsert)
- Kafka exactly-once semantics 구현 보조

**Kotlin 예제**:
```kotlin
import java.time.Duration

interface DedupStore {
    /** 처음 본 키면 true 반환·등록. 이미 있으면 false. 원자적. */
    fun acquireOnce(key: String, ttl: Duration): Boolean
    fun saveResult(key: String, result: String, ttl: Duration)
    fun loadResult(key: String): String?
}

class OrderEmailWorker(
    private val dedup: DedupStore,
    private val mailer: Mailer,
) {
    fun process(msg: OrderEmailJob) {
        val key = "email:${msg.orderId}:${msg.template}"

        // 1. 이미 처리한 적 있으면 캐시된 결과 반환 (멱등)
        dedup.loadResult(key)?.let {
            logger.info("dedup hit: $key, skipping send")
            return
        }

        // 2. 원자적 락 획득 — 두 워커가 동시 처리 방지
        if (!dedup.acquireOnce(key, ttl = Duration.ofHours(24))) {
            logger.info("another worker is processing: $key")
            return
        }

        // 3. 실제 작업 — 외부 mailer 도 Idempotency-Key 전달
        val result = mailer.send(
            to = msg.email,
            template = msg.template,
            idempotencyKey = key,     // 외부 시스템 멱등성도 활용
        )

        // 4. 결과 저장 — 재처리 시 동일 응답
        dedup.saveResult(key, result.messageId, ttl = Duration.ofDays(7))
    }
}

// Redis 기반 DedupStore 구현 예시
class RedisDedupStore(private val redis: RedisClient) : DedupStore {
    override fun acquireOnce(key: String, ttl: Duration): Boolean =
        redis.set("$key:lock", "1", "NX", "PX", ttl.toMillis()) == "OK"

    override fun saveResult(key: String, result: String, ttl: Duration) {
        redis.setex("$key:result", ttl.seconds, result)
    }

    override fun loadResult(key: String): String? = redis.get("$key:result")
}
```

**관련 패턴**: [Job Queue](#job-queue), [Worker Leasing](#worker-leasing), Idempotency Key / Outbox ([distributed.md](distributed.md))

---

<a id="long-running-activity"></a>
## 8. Long-Running Activity (장기 실행 액티비티)

**목적**: 워크플로우 안에서 **수분~수시간** 걸리는 작업 (대용량 파일 처리, ML 추론, 사람 승인 대기) 을 안전하게 실행합니다. Heartbeat 로 살아있음을 알리고, cancellation 신호를 받아 graceful shutdown. Temporal Activity 의 핵심 패턴.

**메커니즘**:
- Activity 가 주기적으로 `heartbeat()` 호출 → 워크플로우 서버에 진행 상태 보고
- **Heartbeat timeout** (예: 30s) 안에 heartbeat 없으면 워크플로우가 Activity 를 dead 로 판단 → 다른 워커로 재할당
- Activity 는 heartbeat 와 함께 **progress payload** 저장 → 재시작 시 마지막 체크포인트부터 재개
- 워크플로우가 cancel 요청 → 다음 heartbeat 시 `ActivityCanceledError` 전파 → cleanup 수행 후 종료
- **Workflow 와 Activity 분리** — Activity 는 비결정적 (HTTP, 시간, 랜덤) 자유롭게 사용 가능

**장점**:
- 수시간 작업도 워커 crash 안전 (heartbeat 누락 시 자동 재할당)
- 진행률 UI 표시 가능 (heartbeat payload 활용)
- 명시적 cancellation 지원 → 사람 승인 / 타임아웃 워크플로우 자연스러움

**단점·주의**:
- **Heartbeat 빈도 vs 비용** — 너무 잦으면 서버 부하, 너무 드물면 재할당 지연
- Activity 가 stateless 해야 재시작 안전 — local 변수만 사용, DB / 외부 스토리지로 상태 영속화
- Cancellation 무시하는 코드 (catch 후 swallow) 는 위험 — finally 블록에서 cleanup
- 워크플로우는 Activity 결과만 history 에 저장 — 진행 중 데이터는 보존 안 됨

**활용 예시**:
- 대용량 파일 처리 (S3 multipart upload)
- ML 학습·추론 (분 단위 ~ 시간 단위)
- 사람 승인 워크플로우 (signal 대기, 수일 timeout)
- 외부 시스템 polling (배치 작업 완료 대기)

**Kotlin 예제 (Temporal Activity with Heartbeat)**:
```kotlin
import io.temporal.activity.*
import java.time.Duration

@ActivityInterface
interface VideoEncodeActivity {
    fun encode(videoUrl: String, format: String): String  // 결과 URL
}

class VideoEncodeActivityImpl : VideoEncodeActivity {
    override fun encode(videoUrl: String, format: String): String {
        val ctx = Activity.getExecutionContext()
        // 이전 시도가 남긴 체크포인트 복원 — 재시작 시 처음부터 안 함
        val resumeFromChunk = ctx.heartbeatDetails<Int>(Int::class.java).orElse(0)

        val totalChunks = countChunks(videoUrl)
        val result = StringBuilder()

        for (chunk in resumeFromChunk until totalChunks) {
            // 1. 취소 신호 확인 — 워크플로우가 cancel 요청 시 throw
            ctx.heartbeat(chunk)        // 진행률 보고 + cancel 체크
            // (heartbeat 가 ActivityCanceledException 던지면 catch 후 cleanup)

            // 2. 청크 처리 (수십 초 ~ 수 분 소요 가능)
            val encoded = encodeChunk(videoUrl, chunk, format)
            result.append(encoded)
        }

        return uploadResult(result.toString())
    }

    private fun countChunks(url: String): Int = TODO()
    private fun encodeChunk(url: String, idx: Int, format: String): String = TODO()
    private fun uploadResult(data: String): String = TODO()
}

// Workflow 측 Activity 등록
class VideoWorkflowImpl : VideoWorkflow {
    private val encode = Workflow.newActivityStub(
        VideoEncodeActivity::class.java,
        ActivityOptions.newBuilder()
            .setStartToCloseTimeout(Duration.ofHours(2))     // 전체 상한
            .setHeartbeatTimeout(Duration.ofSeconds(30))     // 30초 heartbeat 없으면 dead
            .setRetryOptions(RetryOptions.newBuilder()
                .setMaximumAttempts(3)
                .build())
            .build()
    )

    override fun process(url: String): String = encode.encode(url, "mp4")
}
```

**관련 패턴**: [Durable Workflow](#durable-workflow), [Worker Leasing](#worker-leasing), Health Check / Timeout ([reliability.md](reliability.md))

---

<a id="workflow-versioning"></a>
## 9. Workflow Versioning (워크플로우 버저닝)

**목적**: **실행 중인 워크플로우 인스턴스** 에 신규 코드를 적용할 때 determinism 을 깨지 않도록 버전 분기를 코드에 명시합니다. Durable Workflow 의 가장 까다로운 운영 문제.

**메커니즘**:
- 워크플로우 인스턴스는 **시작 시점 코드** 를 따름 (Event History replay 시)
- 이미 실행 중인 인스턴스가 있는 상태에서 워크플로우 코드를 수정하면 → replay 시 history 와 새 코드가 불일치 → **NonDeterministicException**
- 해결책 1: **GetVersion / Patched API** — 코드에 분기점 표시, history 에 사용한 버전 기록
- 해결책 2: **새 Task Queue** 로 워크플로우 분리, 기존 인스턴스는 v1 워커가, 신규는 v2 워커가 처리
- 해결책 3: **Continue-As-New** — 워크플로우를 짧게 끊고 새 인스턴스로 이어가기 (대규모 변경 시)

**장점**:
- 무중단 배포 가능 (실행 중 워크플로우 영향 없음)
- 점진적 마이그레이션 — 신규 인스턴스만 새 로직 적용
- 영구 호환성 보장 (5 년 전 시작한 워크플로우도 끝까지 완주)

**단점·주의**:
- **코드가 버전 분기로 오염** — `if (version >= 1)` 누적 → 청소 시기 결정 필요
- 모든 인스턴스가 v1 path 완료될 때까지 v1 코드 제거 불가 — 장기 실행 워크플로우는 수개월 코드 잔존
- 버전 분기 누락 시 production 에서 NonDeterministicException → 워크플로우 stuck
- 코드 리뷰·통합 테스트로 결정성 검증 필수

**활용 예시**:
- Temporal `Workflow.getVersion()` / `Workflow.patched()`
- Cadence GetVersion API
- 장기 구독 갱신 (1 년 워크플로우 중간에 로직 변경)
- 다단계 승인 흐름 변경 (이미 진행 중인 결재 보존)

**Kotlin 예제 (Temporal Workflow Versioning)**:
```kotlin
import io.temporal.workflow.Workflow

class OrderWorkflowImpl : OrderWorkflow {
    private val activities = Workflow.newActivityStub(OrderActivities::class.java, /* opts */)

    override fun process(orderId: String): String {
        // 기존 v1 코드 — 결제 후 배송
        val chargeId = activities.charge(orderId)

        // 신규: 사기 탐지 단계 추가 — getVersion 으로 분기
        // 첫 인자: change ID (코드 변경 식별자)
        // minSupported = -1 (= DEFAULT_VERSION, 기존 인스턴스)
        // maxSupported = 1 (현재 새 버전)
        val v = Workflow.getVersion("add-fraud-check", Workflow.DEFAULT_VERSION, 1)

        when (v) {
            Workflow.DEFAULT_VERSION -> {
                // 기존 인스턴스 — 사기 탐지 없이 바로 배송
                return activities.ship(orderId)
            }
            1 -> {
                // 신규 인스턴스 — 사기 탐지 후 배송
                val fraudOk = activities.checkFraud(orderId)
                if (!fraudOk) {
                    activities.refund(chargeId)
                    throw FraudDetectedException(orderId)
                }
                return activities.ship(orderId)
            }
            else -> error("unknown version: $v")
        }
    }
}

// 향후 모든 v0 인스턴스가 완료된 후에는 코드 청소 가능:
// - getVersion 호출 제거
// - DEFAULT_VERSION 분기 제거
// - 단, history replay 호환성 위해 getVersion 호출은 한참 더 유지 권장

// 대안: Continue-As-New — 워크플로우를 명시적으로 새 인스턴스로 전환
class SubscriptionRenewalWorkflowImpl : SubscriptionRenewalWorkflow {
    override fun run(subId: String, cycle: Int) {
        repeat(12) { month ->
            activities.bill(subId, month)
            Workflow.sleep(Duration.ofDays(30))
        }
        // history 가 커지기 전에 새 인스턴스로 이어감 — 신규 코드 적용 기회
        Workflow.continueAsNew(subId, cycle + 1)
    }
}
```

**관련 패턴**: [Durable Workflow](#durable-workflow), [Saga (Workflow)](#saga-workflow), Strangler Fig ([legacy-code.md](legacy-code.md))
