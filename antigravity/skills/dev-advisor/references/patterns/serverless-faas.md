# 서버리스 / FaaS 패턴 (Serverless & Function-as-a-Service Patterns)

서버리스(FaaS, Function-as-a-Service) 환경에서 함수 실행 모델, 이벤트 소싱, 워크플로우 오케스트레이션, 콜드 스타트 완화, 운영 비용 최적화를 다루는 패턴 모음이다. AWS Lambda / Google Cloud Functions / Azure Functions / Cloudflare Workers 등 메이저 클라우드의 매니지드 컴퓨트 서비스를 대상으로 하며, 이벤트 기반 아키텍처(EDA, Event-Driven Architecture)와 함께 사용된다.

서버리스의 핵심 가치는 **자동 확장(0→N)**, **사용량 기반 과금(pay-per-invocation)**, **인프라 운영 부담 제거**다. 그러나 그 대가로 **콜드 스타트 지연**, **실행 시간 제한(AWS Lambda 15분 / Cloudflare Workers 30초 CPU)**, **상태 비저장(stateless)** 제약, **벤더 락인** 위험이 존재한다. 본 카탈로그는 이러한 트레이드오프를 명시적으로 다루며, CNCF Serverless Working Group의 [Serverless Whitepaper v1.0](https://github.com/cncf/wg-serverless/blob/master/whitepapers/serverless-overview/cncf_serverless_whitepaper_v1.0.pdf)을 기준 표준으로 사용한다.

관련 패턴:
- [`patterns/deployment.md`](deployment.md) — Blue-Green, Canary, Progressive Delivery (서버리스에서 alias/version 기반 트래픽 분할)
- [`patterns/integration.md#3-message-broker-메시지-브로커`](integration.md#3-message-broker-메시지-브로커) — Message Broker Selection Matrix (이벤트 소스 선정)
- [`patterns/distributed.md#3-saga-choreography`](distributed.md#3-saga-choreography) / [`distributed.md#4-saga-orchestration`](distributed.md#4-saga-orchestration) — 분산 트랜잭션, TCC(Try-Confirm-Cancel) 대비 Saga
- [`patterns/observability.md`](observability.md) — 분산 추적, 함수 단위 메트릭, X-Ray / Cloud Trace 활용
- [`patterns/finops.md`](finops.md) — Provisioned Concurrency 비용 모델, GB-second 과금 최적화

---

## 1. Cold Start Mitigation (콜드 스타트 완화)

<a id="faas-cold-start-mitigation"></a>

**정의**: 서버리스 함수가 유휴 상태에서 첫 호출을 받을 때 발생하는 **초기화 지연(Cold Start Latency)**을 측정·최소화하는 패턴. 이미 활성화된 함수 인스턴스(Warm)가 응답하는 경우는 1~10ms 수준인 반면, Cold Start는 100ms~수 초까지 늘어날 수 있어 P99 latency에 직접 영향을 준다.

**원인 분류**:

| 단계 | 발생 위치 | 평균 지연(AWS Lambda Node.js 기준) | 통제 가능성 |
|------|----------|---------------------------------|-----------|
| **컨테이너 프로비저닝(MicroVM)** | 클라우드 제어 영역 | 80~150ms (Firecracker MicroVM 생성) | 낮음 (벤더 의존) |
| **런타임 초기화** | 함수 인스턴스 | Node.js 50ms / Java 800ms / .NET 300ms | 중간 (런타임 선택) |
| **VPC ENI 어태치** | Lambda + VPC | 과거 ~10초 → 2019년 ENI 사전 생성 이후 ~250ms | 중간 (VPC 사용 시) |
| **패키지/이미지 다운로드** | 함수 코드 로드 | ZIP 50MB → ~200ms / OCI 10GB → ~1~3초 | 높음 (크기 최적화) |
| **사용자 코드 INIT** | 함수 main 외 코드 | 의존성 로드, DB 연결, SDK 초기화 | 높음 (lazy load) |

**메커니즘**:

1. **런타임 선택**: 컴파일 언어(Go, Rust)는 인터프리터 언어(Python, Node.js)보다 초기화가 빠르고, JVM(Java/Kotlin)은 가장 느리다. JVM은 [AWS Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)(Firecracker 스냅샷 복원)로 최대 10배 개선이 가능하지만, Java 17+ Corretto 런타임에 한정된다.
2. **패키지 최소화**: ZIP 50MB / unzipped 250MB 한도, 컨테이너 이미지 10GB 한도이지만 실제 콜드 스타트에 영향을 주는 건 코드 로드 시간이다. Tree-shaking, esbuild minify, Lambda Layer 분리로 200KB 이하 유지가 권장된다.
3. **ARM64 아키텍처(Graviton2)**: x86 대비 콜드 스타트 ~20% 단축 + 비용 20% 절감(Pinpoint 사례 [AWS 블로그](https://aws.amazon.com/blogs/aws/aws-lambda-functions-powered-by-aws-graviton2-processor-run-your-functions-on-arm-and-get-up-to-34-better-price-performance/)).
4. **Init 단계 활용**: AWS Lambda는 `INIT` 단계(handler 외부 코드)가 무료로 최대 10초까지 실행 가능. DB 커넥션 풀, SDK 클라이언트, 설정 캐시를 여기서 초기화한다.
5. **VPC 회피**: Lambda를 VPC 밖에 두거나, [VPC Lambda Hyperplane ENI](https://aws.amazon.com/blogs/compute/announcing-improved-vpc-networking-for-aws-lambda-functions/)(2019+)를 사용해 ENI 어태치 비용을 사전에 흡수.

**측정 (P99 latency)**:

```
콜드 스타트 측정 메트릭:
- AWS Lambda: CloudWatch INIT_DURATION 로그 필드
  REPORT RequestId: ... Init Duration: 234.56 ms
- GCP Cloud Functions: cloudfunctions.googleapis.com/function/execution_times (state=cold)
- Azure Functions: AzureFunctionsAppLogs Coldstart 카테고리

P99 측정 SLO 예시:
- Warm path P99: <50ms
- Cold path P99: <500ms (Node.js/Go) / <1500ms (Java SnapStart 없이)
- Cold start 비율 SLI: <1% of invocations
```

**비용 모델**:

| 완화 기법 | 추가 비용 | 콜드 스타트 영향 |
|----------|---------|---------------|
| ARM64 전환 | -20% 실행 비용 | -20% 콜드 스타트 |
| SnapStart (Java) | 캐시된 스냅샷당 1.25배 비용 (해당 invocation에만) | -90% (~5초 → ~500ms) |
| 패키지 최적화 (50MB→5MB) | 무료 (개발 시간) | -100~300ms |
| VPC 제거 + VPC Endpoint 사용 | VPC Endpoint 시간당 $0.01/h + GB당 $0.01 | -250ms |
| Init phase에서 의존성 lazy load | 무료 | -50~500ms |

**클라우드 차이**:

- **AWS Lambda**: SnapStart(Java/Python/.NET 일부), ARM64(Graviton2), Provisioned Concurrency, Lambda Layers, OCI 컨테이너 이미지(10GB) 모두 지원. Firecracker 기반.
- **Google Cloud Functions Gen2**: Cloud Run 기반으로 변경되어 컨테이너 이미지 기반 + min instances 제공. gVisor 보안 샌드박스 사용으로 시스템콜 오버헤드 존재.
- **Azure Functions**: Consumption Plan(콜드 스타트 있음) vs Premium Plan(Pre-warmed Instance) vs Dedicated Plan(콜드 스타트 없음, App Service). .NET Isolated Worker는 추가 IPC 오버헤드.
- **Cloudflare Workers**: V8 Isolate 기반으로 **콜드 스타트 ~5ms** (전통적 콜드 스타트 개념이 거의 없음). 단, CPU time 30초 / 메모리 128MB 제한이 엄격.

**활용 예시**:
- AWS Lambda Node.js 함수에서 `aws-sdk`를 handler 외부에서 import하여 INIT phase에 로드.
- Java Spring Boot Lambda를 SnapStart + AOT(GraalVM Native Image) 조합으로 500ms 미만 달성.
- Cloudflare Workers로 글로벌 엣지 API 구성 (콜드 스타트 사실상 0).

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제 (AWS Lambda + SnapStart)**:
```kotlin
// SnapStart 활용을 위해 init phase에 무거운 초기화 완료
import com.amazonaws.services.lambda.runtime.Context
import com.amazonaws.services.lambda.runtime.RequestHandler
import software.amazon.awssdk.services.dynamodb.DynamoDbClient

class OrderHandler : RequestHandler<Map<String, Any>, String> {
    // init phase: SnapStart가 스냅샷에 포함하는 정적 초기화
    companion object {
        // DynamoDB 클라이언트는 무거우므로 static init에서 한 번만 생성
        private val dynamoDb: DynamoDbClient = DynamoDbClient.builder()
            .region(software.amazon.awssdk.regions.Region.AP_NORTHEAST_2)
            .build()
            // ↑ SnapStart 비활성 환경에선 매 콜드 스타트마다 ~300ms 소요
            // ↑ SnapStart 활성화 시 스냅샷에서 복원되어 ~10ms
    }

    override fun handleRequest(input: Map<String, Any>, context: Context): String {
        // 함수 본체: 매 호출마다 실행 (warm path)
        val orderId = input["orderId"] as String
        val response = dynamoDb.getItem { it.tableName("Orders").key(mapOf("id" to ...)) }
        return response.item().toString()
    }
}
```

**Python 예제 (AWS Lambda + Lazy Loading)**:
```python
# 콜드 스타트 최적화: 무거운 import는 handler 내부로
import json  # 표준 라이브러리는 init phase OK

# AWS SDK 같은 무거운 import도 init phase에 두는 게 일반적
# 단, 사용 빈도가 낮은 경우 lazy load로 콜드 스타트 단축 가능
_db_client = None

def get_db_client():
    """DynamoDB 클라이언트를 lazy load — 처음 호출 시점에만 import."""
    global _db_client
    if _db_client is None:
        import boto3  # 200ms 절약 (모든 invocation이 DB를 쓰는 게 아니라면)
        _db_client = boto3.client("dynamodb")
    return _db_client

def handler(event, context):
    """Lambda 진입점 — Warm path는 _db_client 재사용."""
    if event.get("warm_check"):
        return {"statusCode": 200, "body": "warm"}  # DB 안 씀, lazy load 회피
    client = get_db_client()
    # 비즈니스 로직
    return {"statusCode": 200, "body": json.dumps({"ok": True})}
```

**표준 / 출처**:
- AWS Lambda Operator Guide: [Optimizing performance — cold starts](https://docs.aws.amazon.com/lambda/latest/operatorguide/performance-optimization.html)
- Cloudflare Workers: [How Workers works](https://developers.cloudflare.com/workers/reference/how-workers-works/)
- CNCF Serverless WG Whitepaper §4.4 Performance Characteristics

---

## 2. Provisioned Concurrency (사전 프로비저닝 동시성)

<a id="faas-provisioned-concurrency"></a>

**정의**: 서버리스 함수의 실행 인스턴스를 미리 워밍된(pre-warmed) 상태로 유지하여 **콜드 스타트를 사실상 0**으로 만드는 패턴. 트래픽이 없어도 지정된 수의 인스턴스를 항상 활성화 상태로 두므로 **사용량 기반 과금의 이점은 일부 포기**하되, **응답 지연의 예측 가능성(P99 SLO 준수)**을 얻는다.

**메커니즘**:

서버리스의 기본 모델은 "0→N 자동 스케일"이지만, Provisioned Concurrency는 "M→N 스케일"로 변형한다(M은 사전 프로비저닝된 최소 인스턴스 수). M개의 인스턴스는 클라우드가 24시간 유지하며, M을 초과하는 트래픽은 일반 On-Demand 인스턴스가 받아 콜드 스타트가 발생한다.

```
요청률 ↑
       │  ┌─ On-Demand (콜드 스타트 발생) ─┐
       │  │                                │
  M ───┼──┴───── Provisioned (Warm) ───────┴────► 시간
       │
       0
```

**측정 (P99 latency)**:

| 메트릭 | Provisioned 활성 | Provisioned 미활성 |
|--------|----------------|------------------|
| P50 응답 시간 | 10ms | 10ms |
| P99 응답 시간 | 50ms (warm path만) | 800ms (콜드 스타트 포함) |
| 콜드 스타트 비율 | <0.1% (M 초과 트래픽만) | 1~10% (트래픽 패턴 의존) |
| ProvisionedConcurrencyUtilization | <100% 유지 권장 (>90% 시 알람) | N/A |

**비용 모델**:

AWS Lambda 기준 (us-east-1, x86):
- **On-Demand**: $0.0000166667 / GB-second + $0.20 / 1M requests
- **Provisioned Concurrency**: $0.0000041667 / GB-second (24h 상시) + $0.0000097222 / GB-second (실제 실행 시) + $0.20 / 1M requests

손익분기점 계산:
```
Provisioned 시간당 비용 (1 인스턴스, 1GB 메모리):
  $0.0000041667 × 1GB × 3600s = $0.015/h

On-Demand 동일 시간 100% 활용도 비용:
  $0.0000166667 × 1GB × 3600s = $0.06/h

→ Utilization > 25% 일 때 Provisioned가 저렴
→ 24/7 트래픽이 일정한 워크로드에 유리
→ 야간 트래픽이 거의 없는 워크로드는 Application Auto Scaling 스케줄로
  업무 시간만 Provisioned 활성화하는 게 최적
```

**클라우드 차이**:

| 클라우드 | 명칭 | 최소 인스턴스 | 과금 모델 | 비고 |
|---------|------|------------|---------|------|
| **AWS Lambda** | Provisioned Concurrency | 1+ | Provisioned 시간 + 실행 시간 별도 | Application Auto Scaling 스케줄 지원, alias/version 별 설정 |
| **GCP Cloud Functions Gen2** | min instances | 0~1000 | Idle 시 50% 할인 (Tier 1 CPU) | Cloud Run 기반, gen2만 지원 |
| **Azure Functions** | Premium Plan Pre-warmed | 1+ | Premium Plan 시간당 정액 | EP1/EP2/EP3 SKU별 vCPU/메모리 |
| **Cloudflare Workers** | (해당 없음) | N/A | V8 Isolate 콜드 스타트 ~5ms로 충분 | Smart Placement만 별도 |

**활용 예시**:
- AWS Lambda Edge 함수에서 SLO P99 < 100ms 보장이 필요한 인증 함수.
- 매일 09:00에 트래픽이 급증하는 결제 API → Application Auto Scaling으로 08:55에 Provisioned 100으로 설정, 18:00에 0으로 복귀.
- GCP Cloud Run에서 일정한 백그라운드 작업 처리 시 min instances = 2로 항상 가용.

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Terraform 예제 (AWS Lambda Provisioned Concurrency + Scheduled Scaling)**:
```hcl
# Lambda 함수 정의
resource "aws_lambda_function" "payment_api" {
  function_name = "payment-api"
  runtime       = "nodejs20.x"
  # ... 기타 설정
  publish       = true  # Provisioned Concurrency는 version 또는 alias에 적용 필수
}

# Lambda alias (Provisioned Concurrency 적용 대상)
resource "aws_lambda_alias" "prod" {
  name             = "prod"
  function_name    = aws_lambda_function.payment_api.function_name
  function_version = aws_lambda_function.payment_api.version
}

# Application Auto Scaling 등록
resource "aws_appautoscaling_target" "lambda" {
  max_capacity       = 100
  min_capacity       = 10
  resource_id        = "function:${aws_lambda_function.payment_api.function_name}:prod"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

# 업무 시간(09~18 KST = 00~09 UTC) 스케일 업
resource "aws_appautoscaling_scheduled_action" "scale_up" {
  name               = "scale-up-business-hours"
  service_namespace  = aws_appautoscaling_target.lambda.service_namespace
  resource_id        = aws_appautoscaling_target.lambda.resource_id
  scalable_dimension = aws_appautoscaling_target.lambda.scalable_dimension
  schedule           = "cron(0 0 ? * MON-FRI *)"  # 매주 월-금 09:00 KST
  scalable_target_action {
    min_capacity = 100
    max_capacity = 200
  }
}
```

**표준 / 출처**:
- AWS Lambda Provisioned Concurrency: [공식 문서](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html)
- GCP Cloud Run min instances: [공식 문서](https://cloud.google.com/run/docs/configuring/min-instances)
- Azure Functions Premium Plan: [공식 문서](https://learn.microsoft.com/en-us/azure/azure-functions/functions-premium-plan)

---

## 3. Event-Source Mapping (이벤트 소스 매핑)

<a id="faas-event-source-mapping"></a>

**정의**: 서버리스 함수와 외부 이벤트 소스(메시지 큐, 스트림, 데이터베이스, HTTP)를 연결하여 **이벤트 발생 → 함수 호출**을 자동화하는 패턴. AWS Lambda의 Event Source Mapping(ESM), GCP Eventarc, Azure Event Grid Trigger가 대표적이며, 동기/비동기/스트림 처리 방식이 각각 다른 보장(at-least-once / exactly-once / ordering)을 제공한다.

**호출 방식 분류**:

| 호출 방식 | 보장 | 재시도 | 순서 | 사용처 |
|---------|------|------|------|-------|
| **동기 (Sync / RequestResponse)** | 응답 즉시 반환 | 클라이언트 책임 | N/A | API Gateway, ALB, Function URL |
| **비동기 (Async / Event)** | At-least-once | 자동 2회 + DLQ | 순서 보장 X | S3 Event, SNS, EventBridge |
| **풀 기반 스트림 (Poll-based)** | At-least-once | 자동 (체크포인트) | 샤드 내 순서 | SQS, Kinesis, DynamoDB Streams, MSK/Kafka |

**이벤트 소스별 특성**:

### SQS (Simple Queue Service) ↔ Lambda

- **호출 방식**: Lambda가 5초마다 long-polling으로 SQS를 폴링.
- **배치 크기**: 1~10 메시지 (Standard), 1~10000 (배치 크기 + 배치 윈도우 조합).
- **동시성**: SQS Standard는 함수 동시성과 1:1 매핑. SQS FIFO는 MessageGroupId별 1개 인스턴스 직렬 처리.
- **DLQ**: SQS Queue 자체에 RedrivePolicy 설정 → Lambda 실패 시 maxReceiveCount 도달 후 DLQ로 이동.
- **Visibility Timeout**: Lambda timeout × 6 이상 권장(공식: AWS Lambda Operator Guide).

### Kinesis Data Streams ↔ Lambda

- **호출 방식**: Lambda가 샤드당 1초마다 GetRecords API 호출.
- **배치 크기**: 1~10000 레코드 (기본 100), 배치 윈도우 0~300초.
- **순서 보장**: PartitionKey가 같은 메시지는 같은 샤드 → 순서 보장됨.
- **Enhanced Fan-Out**: 샤드당 2 컨슈머 한계 → Enhanced Fan-Out 활성화 시 컨슈머당 전용 2MB/s 처리량.
- **체크포인트**: Lambda 성공 시 자동 진행. 실패 시 BisectBatchOnFunctionError + MaximumRetryAttempts 조합으로 poison pill 처리.

### DynamoDB Streams ↔ Lambda

- **호출 방식**: Kinesis와 동일한 poll 모델, 별도 API(`GetRecords` for DDB Streams).
- **레코드 보존**: 24시간 (Kinesis는 24h~365일 설정 가능).
- **사용처**: CDC (Change Data Capture), 트리거, 재고 동기화.
- **StreamViewType**: `KEYS_ONLY` / `NEW_IMAGE` / `OLD_IMAGE` / `NEW_AND_OLD_IMAGES`.

### SNS (Simple Notification Service) ↔ Lambda

- **호출 방식**: SNS가 Lambda를 비동기 invoke. fan-out 패턴 (1 SNS → N Lambda 구독).
- **재시도**: AWS Lambda Async 재시도 정책(2회) + Lambda Destinations로 OnSuccess/OnFailure 라우팅.
- **사용처**: 알림, 다중 구독자, 이벤트 fan-out.

### EventBridge ↔ Lambda

- **호출 방식**: 룰 매칭 후 Lambda 비동기 invoke.
- **필터링**: JSON 패턴 매칭(서버 측 필터링)으로 Lambda 호출 비용 절감.
- **사용처**: SaaS 통합(Salesforce, Datadog, Auth0), 스케줄(Cron), AWS 서비스 이벤트.

**측정 (P99 latency)**:

```
SQS Lambda 처리 지연:
  enqueue_to_invoke_latency_p99:
    - Standard Queue: ~1~2초 (long-polling 주기)
    - FIFO Queue: ~1초

Kinesis Lambda 처리 지연:
  IteratorAge_p99:
    - 정상: < 1000ms
    - 누적 중: ↑ 증가 → 알람 임계값 5000ms

EventBridge 라우팅 지연:
  TargetInvocationLatency_p99: < 500ms (룰 매칭 → Lambda 호출)
```

**비용 모델**:

| 이벤트 소스 | 추가 비용 (Lambda 외) | 비고 |
|----------|-------------------|------|
| SQS | $0.40 / 1M requests (Standard) | Lambda가 폴링하는 ReceiveMessage도 과금 |
| Kinesis | $0.015/h/shard + $0.014/M PUT | Enhanced Fan-Out 추가 비용 |
| DynamoDB Streams | $0.02 / 100,000 stream reads | 첫 250만 reads/월 무료 |
| SNS | $0.50 / 1M deliveries | Lambda delivery 별도 과금 |
| EventBridge | $1.00 / 1M custom events | AWS 서비스 이벤트는 무료 |

**클라우드 차이**:

- **AWS**: 가장 많은 이벤트 소스 지원(SQS / Kinesis / DDB Streams / SNS / EventBridge / S3 / MSK / MQ).
- **GCP**: Eventarc + Pub/Sub + Cloud Storage 트리거 + Cloud Scheduler. Pub/Sub은 at-least-once 기본, exactly-once delivery는 옵트인(2022+).
- **Azure**: Event Grid Trigger + Service Bus Trigger + Event Hub Trigger + Cosmos DB Change Feed Trigger. Functions 런타임이 Trigger Binding 추상화.
- **Cloudflare Workers**: Queues / Cron Triggers / Email Workers / Durable Objects Alarms. 외부 소스는 HTTP 또는 R2/D1 Bindings.

**활용 예시**:
- SQS → Lambda → DynamoDB로 주문 큐 처리 (At-least-once + 멱등성 키).
- Kinesis → Lambda로 클릭 스트림 실시간 집계 (Enhanced Fan-Out).
- DynamoDB Streams → Lambda로 사용자 프로필 변경 → 검색 인덱스(OpenSearch) 동기화.
- EventBridge Schedule → Lambda로 매시간 배치 작업.

**난이도**: 중간 | **사용 빈도**: ★★★★★

**TypeScript 예제 (AWS Lambda + SQS Event Source Mapping with Idempotency)**:
```typescript
import { SQSEvent, SQSBatchResponse, SQSBatchItemFailure } from "aws-lambda";
import { DynamoDBClient, PutItemCommand } from "@aws-sdk/client-dynamodb";

const ddb = new DynamoDBClient({}); // init phase에서 SDK 클라이언트 초기화

// 부분 배치 응답 활성화: 함수 설정에서 ReportBatchItemFailures=true
export const handler = async (event: SQSEvent): Promise<SQSBatchResponse> => {
  const batchItemFailures: SQSBatchItemFailure[] = [];

  for (const record of event.Records) {
    try {
      const body = JSON.parse(record.body);
      // 멱등성 키 기반 처리: MessageDeduplicationId 또는 비즈니스 키 사용
      const idempotencyKey = body.orderId;

      // 조건부 쓰기로 중복 처리 방지 (DynamoDB Conditional Expression)
      await ddb.send(new PutItemCommand({
        TableName: "ProcessedOrders",
        Item: {
          orderId: { S: idempotencyKey },
          processedAt: { S: new Date().toISOString() },
          payload: { S: record.body },
        },
        ConditionExpression: "attribute_not_exists(orderId)",  // 이미 처리됐으면 실패
      }));
    } catch (err: any) {
      if (err.name === "ConditionalCheckFailedException") {
        // 이미 처리됨 → 성공으로 간주, SQS에서 삭제
        continue;
      }
      // 다른 에러는 batch item failure로 보고 → SQS visibility timeout 후 재시도
      batchItemFailures.push({ itemIdentifier: record.messageId });
    }
  }

  return { batchItemFailures };
};
```

**표준 / 출처**:
- AWS Lambda Event Source Mapping: [공식 문서](https://docs.aws.amazon.com/lambda/latest/dg/invocation-eventsourcemapping.html)
- CNCF CloudEvents v1.0 (이벤트 직렬화 표준): [cloudevents.io](https://cloudevents.io/)
- AWS Lambda Operator Guide: Error Handling for Async/Streaming/Polling
- 비교: 메시지 브로커 선정 매트릭스는 [`patterns/integration.md#3-message-broker-메시지-브로커`](integration.md#3-message-broker-메시지-브로커) 참고

---

## 4. Step Functions / Durable Functions / Workflow (워크플로우 오케스트레이션)

<a id="step-functions-durable-workflow"></a>

**정의**: 여러 서버리스 함수와 외부 서비스 호출을 **상태 기계(State Machine)**로 엮어 장기 실행 워크플로우를 신뢰성 있게 처리하는 패턴. AWS Step Functions(ASL, Amazon States Language), Azure Durable Functions, GCP Workflows가 대표적이며, **Choreography vs Orchestration** 트레이드오프 결정의 핵심이다.

**Choreography vs Orchestration**:

| 항목 | Choreography (안무) | Orchestration (오케스트레이션) |
|------|-------------------|-----------------------------|
| 제어 방식 | 분산 (각 서비스가 이벤트 발행/구독) | 중앙 (워크플로우 엔진이 호출) |
| 결합도 | 낮음 | 중간 (엔진에 결합) |
| 가시성 | 낮음 (분산 트레이싱 필수) | 높음 (Visual Workflow Studio) |
| 디버깅 | 어려움 (이벤트 추적 필요) | 쉬움 (상태 기계 시각화) |
| 신뢰성 | 외부 트랜잭션 보장 어려움 | 엔진이 재시도/타임아웃 처리 |
| 적합 상황 | 느슨한 결합, 다수 팀 | 명확한 비즈니스 프로세스, 보상 트랜잭션 |

**Saga 패턴 구현 (보상 트랜잭션, [`patterns/distributed.md#3-saga-choreography`](distributed.md#3-saga-choreography))**:

분산 환경에서 ACID 트랜잭션이 불가능할 때, 각 단계의 실패 시 이전 단계를 보상(rollback 대신 compensate)하는 패턴. Step Functions의 `Catch` + `Fallback` 상태로 자연스럽게 구현된다.

```
주문 → 결제 → 배송 → 완료
  ↓     ↓      ↓
실패 → 환불 ← 취소 (보상 트랜잭션)
```

TCC(Try-Confirm-Cancel)는 2PC와 Saga 사이의 절충안으로, Try 단계에서 자원을 예약하고 Confirm/Cancel로 확정 또는 취소한다. Saga에 비해 일시적 락이 있어 일관성이 강하지만 자원 예약 가능한 시스템에 한정된다.

**측정 (P99 latency)**:

```
Step Functions 워크플로우 메트릭:
- ExecutionTime_p99: 워크플로우 전체 종단 간 시간
- StateTransitionLatency_p99:  상태 전환 자체 지연 ~25ms
- LambdaTaskFailedCount: Lambda Task 실패 카운트
- ExecutionsTimedOut: 타임아웃된 실행 (TimeoutSeconds 미설정 시 1년 후)
```

**비용 모델**:

| 워크플로우 엔진 | 과금 단위 | 비용 (예시) |
|--------------|---------|----------|
| AWS Step Functions Standard | 상태 전환당 | $0.025 / 1000 state transitions |
| AWS Step Functions Express | 실행 시간 + 메모리 | $1.00 / 1M requests + $0.00001667 / GB-second |
| Azure Durable Functions | Lambda와 동일(Consumption) | + Storage 호출 비용 |
| GCP Workflows | 단계 실행 + 외부 호출 | $0.01 / 1000 internal steps + $0.025 / 1000 external steps |

**Standard vs Express (AWS Step Functions)**:
- **Standard**: 최대 1년 실행, 정확히 한 번(exactly-once), 시각화/감사 영구 보존. 인적 승인 워크플로우, 장기 비즈니스 프로세스.
- **Express**: 최대 5분 실행, 최소 한 번(at-least-once), CloudWatch Logs 기반 감사. 대량 이벤트 처리, IoT 데이터 파이프라인.

**클라우드 차이**:

- **AWS Step Functions**: ASL(JSON DSL), Visual Workflow Studio, 200+ AWS 서비스 직접 통합 (Lambda 없이 호출 가능), 인적 승인(Callback Pattern), Map 상태로 동적 병렬화, Parallel 상태로 고정 병렬화.
- **Azure Durable Functions**: C#/JavaScript/Python 코드로 작성 (DSL 없음), Orchestrator/Activity/Entity/Sub-Orchestration 패턴, 이벤트 소싱 기반 재실행 모델.
- **GCP Workflows**: YAML/JSON DSL, HTTP 호출 중심, Cloud Run/Functions/외부 API 통합. AWS Step Functions 대비 서비스 통합 폭이 좁다.
- **Cloudflare Workers**: Workflows(2024+) — TypeScript 코드 기반, durable execution + 자동 재시도.

**활용 예시**:
- 결제 → 재고 차감 → 배송 → 알림의 Saga.
- ML 학습 파이프라인: 데이터 검증 → 학습 → 평가 → 모델 등록.
- 인적 승인이 필요한 환불 프로세스(Callback Pattern: `waitForTaskToken`).
- ETL 파이프라인: S3 트리거 → Glue → EMR → Redshift COPY.

**난이도**: 중간~높음 | **사용 빈도**: ★★★★☆

**ASL (Amazon States Language) 예제 — 주문 Saga**:
```json
{
  "Comment": "주문 처리 Saga: 결제 → 재고 → 배송, 실패 시 보상",
  "StartAt": "ProcessPayment",
  "States": {
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "ProcessPayment", "Payload.$": "$"},
      "ResultPath": "$.payment",
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "PaymentFailed"}],
      "Next": "ReserveInventory"
    },
    "ReserveInventory": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "ReserveInventory", "Payload.$": "$"},
      "ResultPath": "$.inventory",
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "RefundPayment"}],
      "Next": "CreateShipment"
    },
    "CreateShipment": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "CreateShipment", "Payload.$": "$"},
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "ReleaseInventory"}],
      "End": true
    },
    "RefundPayment": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "RefundPayment", "Payload.$": "$"},
      "Next": "PaymentFailed"
    },
    "ReleaseInventory": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {"FunctionName": "ReleaseInventory", "Payload.$": "$"},
      "Next": "RefundPayment"
    },
    "PaymentFailed": {"Type": "Fail", "Error": "SagaFailed", "Cause": "주문 처리 실패"}
  }
}
```

**표준 / 출처**:
- AWS Step Functions ASL: [공식 사양](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html)
- Azure Durable Functions Patterns: [공식 문서](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview)
- Microservices.io Saga Pattern: [Chris Richardson](https://microservices.io/patterns/data/saga.html)
- TCC 패턴 비교: [`patterns/distributed.md`](distributed.md) — Saga vs TCC vs 2PC 매트릭스

---

## 5. Cold vs Hot Path (콜드/핫 패스 설계)

<a id="faas-cold-vs-hot-path"></a>

**정의**: 서버리스 함수의 **첫 호출(Cold Path)**과 **연속 호출(Hot Path)**을 명시적으로 구분하여, 각 경로에 다른 최적화 전략을 적용하는 패턴. Cold Path는 일회성 INIT 비용이 발생하지만, Hot Path는 동일 컨테이너에서 메모리, 커넥션 풀, 캐시를 재사용할 수 있어 성능 격차가 10~100배까지 벌어진다.

**메커니즘**:

| 경로 | 정의 | 최적화 초점 |
|------|------|----------|
| **Cold Path** | INIT phase + 첫 invoke (~100ms~수 초) | 패키지 크기, 런타임, 의존성 lazy load, SnapStart |
| **Hot Path** | 2번째 이후 invoke (같은 컨테이너) | 메모리 캐시, DB 커넥션 풀, SDK 클라이언트 재사용 |

**Hot Path 설계 원칙**:

1. **DB 커넥션 풀 외부화**: Lambda는 인스턴스당 1개 DB 커넥션이지만, 동시 인스턴스가 1000개면 DB에 1000개 커넥션 필요 → RDS Proxy(AWS), Cloud SQL Proxy(GCP), PgBouncer 사이드카로 멀티플렉싱.
2. **메모리 캐시**: 함수 인스턴스가 살아있는 동안(15분~1시간) 글로벌 변수에 캐시 유지. 단, 분산 환경에선 인스턴스 간 일관성 없음 → 짧은 TTL + Redis/ElastiCache 보조.
3. **HTTP 클라이언트 keep-alive**: AWS SDK는 기본 keep-alive 비활성화 → 명시적 활성화로 TCP 핸드셰이크 절감 (~30ms/call).
4. **DB pre-warming**: Provisioned Concurrency 활성화 시 INIT에서 DB ping 한 번 보내 커넥션 워밍.

**Cold Path 설계 원칙**:

1. **Lambda Layer 분리**: 큰 의존성(Pandas, NumPy)을 Layer로 분리하면 함수 코드 ZIP은 작게 유지하면서 Layer는 컨테이너 캐시 재사용.
2. **Container Image**: 10GB까지 가능. ECR에 푸시 → Lambda 콜드 스타트 시 청크 단위 lazy load(2020+ "Container Image Optimizations"). 대용량 모델 추론에 유리.
3. **SnapStart (Java)**: INIT 완료 시점에서 Firecracker 스냅샷 → 콜드 스타트 시 스냅샷 복원으로 90% 단축. 단, 스냅샷에 비결정적 데이터(타임스탬프, 랜덤) 포함되면 Hot path에서 문제 발생 → `Runtime.beforeCheckpoint()` / `Runtime.afterRestore()` 훅으로 처리.
4. **INIT phase 적극 활용**: AWS Lambda는 INIT phase에서 최대 10초까지 무료 CPU 사용 가능 → 무거운 초기화(설정 파일 로드, JIT 워밍, SDK 클라이언트)를 모두 여기서 완료.

**측정 (P99 latency)**:

```
Cold vs Hot 분리 측정:
  REPORT RequestId: abc Init Duration: 250ms Duration: 15ms Billed Duration: 16ms

  → Cold start invocation: 총 265ms (INIT 250ms + 실행 15ms)
  → Hot path invocation: 총 15ms

CloudWatch Logs Insights 쿼리:
  filter @message like /REPORT/
  | parse @message /Init Duration: (?<init_ms>\d+\.\d+) ms/
  | stats avg(init_ms) as avg_init, pct(init_ms, 99) as p99_init by bin(5m)

P99 SLO 분리:
  - Cold path P99: < 500ms (Node.js) / < 1500ms (Java SnapStart 없이)
  - Hot path P99: < 50ms
  - Cold start ratio: < 1% of invocations (Provisioned Concurrency 없이)
```

**비용 모델**:

| 최적화 기법 | Cold Path 영향 | Hot Path 영향 | 추가 비용 |
|----------|------------|------------|---------|
| Lambda Layer (의존성 분리) | -100~300ms | 무영향 | 무료 (5 layers / function) |
| Container Image | +200~500ms (첫 콜드 스타트) | 무영향 | ECR storage $0.10/GB/month |
| SnapStart (Java) | -90% | +5% (스냅샷 복원 후 JIT 재워밍) | 1.25× 실행 비용 |
| RDS Proxy | -50ms (Hot path도 TCP 핸드셰이크 절감) | -50ms | $0.015/h/vCPU |
| INIT phase에서 사전 워밍 | -100~500ms | 무영향 | 무료 (INIT은 최대 10초 무과금) |

**클라우드 차이**:

- **AWS Lambda**: INIT phase 명시적, SnapStart(Java/Python/.NET), Container Image, Layer 모두 지원.
- **GCP Cloud Functions Gen2**: Cloud Run 기반이라 컨테이너 이미지 필수. `min instances`로 Hot path 유지.
- **Azure Functions**: Premium Plan Pre-warmed Instance가 INIT 단계를 미리 완료해둠. SnapStart 같은 개념은 없으나 .NET Isolated Worker AOT(Native AOT) 지원.
- **Cloudflare Workers**: V8 Isolate 모델이라 콜드/핫 구분이 약함(콜드 ~5ms). 그 대신 모듈 import 시점에 실행되는 글로벌 코드는 매 isolate에서 1회 실행.

**활용 예시**:
- AWS Lambda Node.js: DynamoDB 클라이언트를 handler 외부에 선언 → Hot path에서 재사용.
- Java Spring Boot Lambda: SnapStart + AOT(GraalVM Native Image) 조합으로 콜드 스타트 200ms 미만.
- ML 추론 Lambda: 모델 파일(500MB)을 Container Image에 포함, INIT phase에서 메모리 로드.
- 다중 리전 Lambda Edge: RDS Proxy로 DB 커넥션 풀링.

**난이도**: 중간 | **사용 빈도**: ★★★★★

**TypeScript 예제 (Cold/Hot Path 명시 분리 + Keep-Alive)**:
```typescript
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { Agent } from "https";
import { NodeHttpHandler } from "@smithy/node-http-handler";

// ─────────────────────────────────────────
// COLD PATH (INIT phase) — 한 번만 실행
// ─────────────────────────────────────────
console.log("[INIT] Cold start: initializing SDK clients");

// HTTPS keep-alive 활성화 — Hot path에서 TCP 핸드셰이크 ~30ms/call 절감
const httpsAgent = new Agent({
  keepAlive: true,
  maxSockets: 50,
});

// DDB 클라이언트는 인스턴스 수명 동안 재사용
const ddb = new DynamoDBClient({
  region: "ap-northeast-2",
  requestHandler: new NodeHttpHandler({ httpsAgent }),
});

// 메모리 캐시 — 같은 인스턴스의 후속 호출에서 재사용
const configCache = new Map<string, any>();

// INIT phase 워밍: DB ping으로 커넥션 미리 확보
async function warmup() {
  try {
    await ddb.config.endpoint();  // SDK가 endpoint를 lazy resolve하므로 미리 호출
  } catch { /* ignore */ }
}
warmup().catch(() => {});

// ─────────────────────────────────────────
// HOT PATH (handler) — 매 invocation 실행
// ─────────────────────────────────────────
export const handler = async (event: any) => {
  const key = event.configKey ?? "default";

  // 메모리 캐시 hit → 1ms
  if (configCache.has(key)) {
    return { statusCode: 200, body: configCache.get(key) };
  }

  // 캐시 miss → DDB 조회 (커넥션은 keep-alive로 재사용)
  const result = await ddb.send(/* GetItemCommand */);
  configCache.set(key, result);

  return { statusCode: 200, body: result };
};
```

**표준 / 출처**:
- AWS Lambda Execution Environment Lifecycle: [공식 문서](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)
- AWS SDK Connection Reuse: [공식 블로그](https://aws.amazon.com/blogs/compute/optimizing-aws-lambda-function-performance-for-java/)
- SnapStart 동작 메커니즘: [Firecracker MicroVM Snapshots](https://github.com/firecracker-microvm/firecracker/blob/main/docs/snapshotting/snapshot-support.md)
- 비용 최적화 매트릭스: [`patterns/finops.md`](finops.md) — Lambda GB-second 과금 모델

---

## 종합 참고

**서버리스 적합성 체크리스트**:
- [ ] 실행 시간이 클라우드 한도 내인가? (Lambda 15분 / Workers CPU 30초 / GCF Gen2 60분)
- [ ] Stateless로 설계 가능한가? (상태는 DB/Redis/S3로 외부화)
- [ ] 트래픽 패턴이 spiky/idle 한가? (24/7 일정한 트래픽은 ECS/Cloud Run이 유리)
- [ ] 콜드 스타트 P99 SLO를 충족할 수 있는가? (못 한다면 Provisioned Concurrency)
- [ ] 벤더 락인 위험을 수용할 수 있는가? (서버리스 표준 없음, CNCF Knative만 일부)

**관련 표준 단체**:
- [CNCF Serverless Working Group](https://github.com/cncf/wg-serverless) — Whitepaper, CloudEvents
- [OpenFaaS](https://www.openfaas.com/) — 오픈소스 FaaS 프레임워크
- [Knative](https://knative.dev/) — Kubernetes 기반 서버리스 표준
- [AsyncAPI](https://www.asyncapi.com/) — 이벤트 기반 API 명세 표준
