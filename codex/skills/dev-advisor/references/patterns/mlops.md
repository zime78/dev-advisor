# MLOps 패턴 (MLOps Patterns)

Machine Learning Operations 정평 있는 10 패턴. [`ai-llm.md`](ai-llm.md) (RAG / Agent Loop / Prompt Template — *LLM 앱 패턴*) 와 differentiate. 본 파일은 **ML 모델 학습 → 배포 → 운영** 의 lifecycle.

**원전·표준 참고**:
- Sculley et al. — *Hidden Technical Debt in Machine Learning Systems* (NeurIPS 2015)
- Mitchell, Wu, Zaldivar et al. — *Model Cards for Model Reporting* (FAT* 2019)
- Andrew Jones — *Driving Data Quality with Data Contracts* (2024)
- Google — *MLOps: Continuous delivery and automation pipelines in machine learning* (whitepaper, 2020)
- Feast Documentation (https://docs.feast.dev)
- MLflow / Kubeflow / Airflow / Dagster / Metaflow
- Evidently AI Drift Detection guide

**핵심 비기능 요구**:
- **재현성 (Reproducibility)** — 데이터 + 코드 + hyperparameter 모두 versioning
- **데이터 = 코드 = 모델** 통합 lifecycle
- **Drift 자동 탐지 + 재학습 트리거** — production 모델은 결국 부패

**관련 카탈로그**:
- [ai-llm.md](ai-llm.md) — RAG / Tool Use / Agent Loop (LLM 앱)
- [`../algorithms/ml.md`](../algorithms/ml.md) — K-Means / KNN / Linear Regression / Transformer (모델 본체)
- [observability.md](observability.md) — Three Pillars, Golden Signals (ML 메트릭 보강)
- [data-modeling.md](data-modeling.md) — CDC / Data Mesh (data lifecycle)
- [`../security/security-ai-model.md`](../security/security-ai-model.md) — Model Extraction / Data Poisoning

---

<a id="feature-store"></a>

## 1. Feature Store

**목적**: 모델 학습(training)과 서빙(serving) 양쪽에서 동일한 feature 정의·계산 로직을 공유하고, online(저지연 KV) / offline(대용량 분석) 두 저장소를 동시에 제공하여 **training-serving skew** 를 제거합니다.

**특징**:
- **Online Store** (Redis, DynamoDB, Cassandra) — ms 단위 서빙 latency, 최신 값만
- **Offline Store** (S3 + Parquet, BigQuery, Snowflake, Delta Lake) — 대용량 historical, time-travel 지원
- **Feature View / Feature Set** — entity (예: `user_id`) 기준으로 묶인 feature 그룹의 선언적 정의
- **Point-in-Time Correctness** — 학습 데이터 추출 시 label 시점 이전의 feature 값만 join 하여 **data leakage** 방지
- 대표 시스템: **Feast** (오픈소스), **Tecton** (SaaS, 원조 Uber Michelangelo 출신), **Databricks Feature Store**, **Hopsworks**, **Vertex AI Feature Store**, **SageMaker Feature Store**

**장점**:
- training-serving skew 제거 — 동일 feature 계산 코드를 두 번 작성하지 않음
- feature 재사용 — 한 팀의 feature 를 다른 팀이 그대로 학습/서빙에 사용
- point-in-time join 으로 미래 정보 누설 차단
- feature discovery — 카탈로그 형태로 feature lineage / freshness / owner 가시화

**단점**:
- 운영 부담 — online + offline 두 저장소 sync 관리 (typically streaming + batch dual write)
- 작은 팀에서는 over-engineering — 단일 모델 1개에는 과함
- backfill 비용 큼 — 새 feature 추가 시 전체 historical 재계산 필요
- entity key 가 변경되면 (예: user_id 체계 개편) 전 시스템 재구축

**활용 예시**:
- Uber Michelangelo — 이름의 어원 (Feature Store 패턴의 원조, 2017 공개)
- Airbnb Zipline
- Netflix Axion (real-time + batch)
- 금융 사기 탐지 (real-time scoring + nightly batch retraining)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Python 예제 (Feast)**:
```python
# feature_repo/features.py
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64
from datetime import timedelta

# 1) Entity 정의 — 모든 feature 의 join key
user = Entity(name="user_id", join_keys=["user_id"])

# 2) Offline source — historical parquet
user_stats_source = FileSource(
    path="s3://lake/features/user_stats.parquet",
    timestamp_field="event_timestamp",
)

# 3) Feature View — Feast 가 online + offline 양쪽으로 동기화
user_stats_fv = FeatureView(
    name="user_stats",
    entities=[user],
    ttl=timedelta(days=30),
    schema=[
        Field(name="purchase_count_7d", dtype=Int64),
        Field(name="avg_order_value", dtype=Float32),
    ],
    source=user_stats_source,
    online=True,
)

# 4) 학습 시 — point-in-time join (label 시점 이전 값만)
from feast import FeatureStore
store = FeatureStore(repo_path=".")
training_df = store.get_historical_features(
    entity_df=labels_df,  # ['user_id', 'event_timestamp', 'label']
    features=["user_stats:purchase_count_7d", "user_stats:avg_order_value"],
).to_df()

# 5) 서빙 시 — online store (Redis) 에서 ms 단위 조회
features = store.get_online_features(
    features=["user_stats:purchase_count_7d", "user_stats:avg_order_value"],
    entity_rows=[{"user_id": 42}],
).to_dict()
```

**관련 패턴**: [Data Contract](#data-contract), [ML Pipeline (DAG)](#ml-pipeline-dag), [Online vs Batch Inference](#online-batch-inference), [Data Drift Detection](#data-drift)

---

<a id="model-registry"></a>

## 2. Model Registry

**목적**: 학습된 모델을 단순 파일 (`model.pkl`) 로 던지는 대신, **버전 + 메타데이터 + 단계(stage)** 로 카탈로그화하여 어느 모델이 어디서 학습되어 어느 데이터로 검증되었는지 추적 가능하게 합니다.

**특징**:
- **Version**: 자동 증가 (v1, v2, ...) — 매 학습마다 새 버전
- **Stage**: `None` → `Staging` → `Production` → `Archived` 의 단계 전이 (Promotion)
- **Metadata**: 학습 데이터 hash, hyperparameter, metric (accuracy / AUC / F1), git commit, MLflow run_id
- **Lineage**: 어떤 dataset + code + parameter 로 만들어졌는지 역추적
- 대표 시스템: **MLflow Model Registry**, **Weights & Biases Artifacts**, **SageMaker Model Registry**, **Vertex AI Model Registry**, **Neptune.ai**

**장점**:
- "production 에 있는 모델 = registry 의 Production stage" 단일 진실
- A/B 테스트 시 두 버전을 동시에 가리킬 수 있음 (Champion = v3, Challenger = v4)
- 롤백 즉시 가능 — 이전 Production 버전을 다시 promote
- 컴플라이언스 (GDPR, EU AI Act) 가 요구하는 모델 이력 자동 충족

**단점**:
- registry 자체가 SPOF — 다운되면 배포 파이프라인 정지
- 모델 artifact 가 크면 (LLM 수십 GB) 저장 비용 폭증
- stage 전이 권한 관리 (RBAC) 가 없으면 누구나 production 으로 올림 — 거버넌스 필수

**활용 예시**:
- MLflow + Databricks 의 표준 워크플로우
- 금융 모델 거버넌스 — 모델 위원회 승인 후 Production 전이
- 의료 ML — FDA 제출용 모델 이력 자동 보관

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Python 예제 (MLflow)**:
```python
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://mlflow.internal:5000")
mlflow.set_experiment("churn-prediction")

# 1) 학습 + 로깅 + 등록
with mlflow.start_run() as run:
    mlflow.log_param("max_depth", 5)
    mlflow.log_metric("val_auc", 0.847)
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name="churn_v1",  # registry 에 등록
    )

# 2) Stage 전이 (Staging → Production)
client = MlflowClient()
client.transition_model_version_stage(
    name="churn_v1",
    version=3,
    stage="Production",
    archive_existing_versions=True,  # 기존 Production → Archived
)

# 3) 서빙 시 stage 로 모델 로드 — 버전 번호 hardcoding 안 함
model = mlflow.pyfunc.load_model("models:/churn_v1/Production")
prediction = model.predict(input_df)

# 4) 롤백 — 이전 버전 재 promote
client.transition_model_version_stage(
    name="churn_v1", version=2, stage="Production",
)
```

**관련 패턴**: [Model Card](#model-card), [ML Pipeline (DAG)](#ml-pipeline-dag), [Shadow Model / Champion-Challenger](#shadow-champion-challenger)

---

<a id="model-card"></a>

## 3. Model Card

**목적**: 모델을 사용·재배포·감사하는 모든 stakeholder 가 **모델의 의도된 용도, 학습 데이터 출처, 성능, 한계, 편향**을 한 페이지로 파악할 수 있도록 표준화된 문서를 모델과 함께 배포합니다.

**특징**:
- Mitchell et al. 2019 *Model Cards for Model Reporting* (FAT* 학회) 원조
- 9 섹션 표준: ① Model Details, ② Intended Use, ③ Factors (sub-population), ④ Metrics, ⑤ Evaluation Data, ⑥ Training Data, ⑦ Quantitative Analyses (disaggregated by factor), ⑧ Ethical Considerations, ⑨ Caveats & Recommendations
- 마크다운 / YAML 표준 — Hugging Face Hub 가 `README.md` 자동 렌더링
- 유사 표준: **Datasheets for Datasets** (Gebru et al. 2018), **System Cards** (OpenAI), **Responsible AI Scorecard** (Microsoft)
- EU AI Act / NIST AI RMF / ISO/IEC 23894 가 요구하는 문서화 의무를 충족하는 실질적 수단

**장점**:
- 모델 오용 방지 — "이 모델은 X 용도가 아닙니다" 명시
- 편향 / 한계 공개로 다운스트림 사용자가 위험 평가 가능
- 감사 / 규제 대응 산출물 — 동일 카드를 컴플라이언스 제출에 재사용
- 인수인계 비용 절감 — 원 저자 부재 시에도 모델 컨텍스트 유지

**단점**:
- 작성 비용 — 정성적 평가 항목이 많아 자동 생성 불가
- 갱신 누락 — 모델만 재학습되고 카드가 stale 해지면 misinformation
- "성능 좋게 보이려" 한 평가만 기록하는 cherry-picking 위험

**활용 예시**:
- Hugging Face Hub 의 모든 모델 (의무는 아니나 사실상 표준)
- Google Cloud Model Cards Toolkit
- OpenAI GPT-4 System Card (확장형)
- Anthropic Claude Model Card

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**YAML 예제 (Hugging Face style)**:
```yaml
# model_card.yaml — 모델 artifact 옆에 함께 배포
model_details:
  name: churn-classifier
  version: 3.2.0
  date: 2026-04-12
  type: gradient_boosted_trees (XGBoost 2.0)
  paper: "internal-doc://ml-churn-v3"
  citation: "DS Team, KakaoVX (2026)"
  license: proprietary
  contact: ml-team@example.com

intended_use:
  primary_uses:
    - "고객 이탈 위험 점수 계산 (B2C 구독)"
  out_of_scope:
    - "B2B 고객 대상 사용 금지 — 학습 데이터에 미포함"
    - "법적 / 금융 의사결정의 단독 근거로 사용 금지"

factors:
  demographic_groups: [region, age_bucket, plan_tier]
  evaluation_factors: "위 세 축 disaggregated 평가 수행"

metrics:
  performance:
    - {name: "AUC", value: 0.847, ci_95: "[0.832, 0.862]"}
    - {name: "F1", value: 0.71}
  decision_threshold: 0.55
  disaggregated:
    region_kr: {AUC: 0.86}
    region_jp: {AUC: 0.81}  # ← 일본 지역 성능 낮음 — 주의

training_data:
  source: "events.user_activity (2024-01-01 ~ 2025-12-31)"
  size: 4_200_000_rows
  preprocessing: "PII 제거, k-anonymity k=5"

ethical_considerations:
  - "지역별 성능 격차 존재 → JP 시장 단독 적용 비권장"
  - "False negative 비용 > False positive — threshold 보수적 설정"

caveats:
  - "휴면 회원 정의가 바뀌면 (90일 → 60일) 재학습 필요"
  - "신규 plan_tier 추가 시 OOD — 카테고리 인코딩 재학습"
```

**관련 패턴**: [Model Registry](#model-registry), [Data Contract](#data-contract)

---

<a id="data-drift"></a>

## 4. Data Drift Detection

**목적**: production 입력 데이터(`X`) 의 분포가 학습 데이터와 통계적으로 달라졌는지 자동으로 탐지하여, 성능 저하 **이전에** 재학습 / 알람 / 차단을 트리거합니다.

**특징**:
- **Covariate Shift** — `P(X)` 분포 변화만 의미 (X→Y 관계는 그대로). Concept Drift 와 구별
- 통계 검정:
  - **Kolmogorov-Smirnov (KS)** — 연속 변수, 두 분포의 CDF 최대 거리. 비모수.
  - **Population Stability Index (PSI)** — 신용평가 산업 표준. `PSI < 0.1` 안정, `0.1 ~ 0.25` 경미, `> 0.25` 심각
  - **Chi-square** — 범주형 변수
  - **Jensen-Shannon Divergence** — 대칭 KL, 부드러운 측정
  - **Maximum Mean Discrepancy (MMD)** — 고차원 / 다변량 대응
- **Schema Drift** — 컬럼 추가/삭제, 타입 변경 (예: int → string) — 통계 검정 이전 단계
- 대표 도구: **Evidently AI**, **Arize Phoenix**, **WhyLabs / whylogs**, **NannyML**, **Alibi Detect**, **Great Expectations** (schema)

**장점**:
- 라벨 수집 지연(ground truth lag) 없이도 입력 분포만으로 조기 경보
- 재학습 비용 절감 — drift 발생 시점에만 trigger
- 책임 분담 — drift 알림은 데이터 엔지니어, 성능 저하는 ML 엔지니어

**단점**:
- 다변량 drift 는 단변량 검정의 단순 합으로 탐지 불가 — 변수 간 상관 변화는 별도 탐지
- **False alarm** — 통계적 유의성 ≠ 비즈니스 유의성. 큰 표본에서는 미세 변화도 p<0.05
- 데이터 양이 적으면 검정력 부족 — sliding window 크기 튜닝 필요

**활용 예시**:
- 금융 사기 탐지 — 사기 수법 분포 변화 즉시 감지
- 추천 시스템 — 신규 콘텐츠 카테고리 등장 시 alert
- IoT 센서 — 계절성 / 장비 노후로 분포 변화

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Python 예제 (Evidently)**:
```python
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
from scipy.stats import ks_2samp
import numpy as np

# 1) Sliding 단순 KS — 단일 feature 빠른 점검
def ks_drift(reference: np.ndarray, current: np.ndarray, alpha: float = 0.01):
    stat, p_value = ks_2samp(reference, current)
    return {
        "ks_statistic": stat,
        "p_value": p_value,
        "drift": p_value < alpha,
    }

# 2) PSI 계산 — 산업 표준 (신용평가)
def population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10):
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
    breakpoints[0], breakpoints[-1] = -np.inf, np.inf
    e_pct = np.histogram(expected, breakpoints)[0] / len(expected)
    a_pct = np.histogram(actual, breakpoints)[0] / len(actual)
    # epsilon 으로 zero-division 방어
    e_pct, a_pct = np.clip(e_pct, 1e-6, 1), np.clip(a_pct, 1e-6, 1)
    psi = np.sum((a_pct - e_pct) * np.log(a_pct / e_pct))
    severity = "stable" if psi < 0.1 else "moderate" if psi < 0.25 else "severe"
    return {"psi": psi, "severity": severity}

# 3) 전체 데이터셋 — Evidently Report
report = Report(metrics=[DataDriftPreset()])
report.run(reference_data=train_df, current_data=production_df)
result = report.as_dict()

drifted_features = [
    m["column_name"]
    for m in result["metrics"][0]["result"]["drift_by_columns"].values()
    if m["drift_detected"]
]
if len(drifted_features) > len(train_df.columns) * 0.3:
    trigger_retraining_pipeline()  # 30% 이상 drift → 재학습
```

**관련 패턴**: [Concept Drift Detection](#concept-drift), [Model Monitoring](#model-monitoring), [Data Contract](#data-contract), [ML Pipeline (DAG)](#ml-pipeline-dag)

---

<a id="concept-drift"></a>

## 5. Concept Drift Detection

**목적**: 입력 `X` 와 라벨 `Y` 사이의 **관계 `P(Y|X)` 자체가 변화**하는 현상을 탐지합니다. Data Drift 가 입력 분포 변화라면, Concept Drift 는 **세상의 규칙이 바뀐 것** — 같은 입력에 다른 정답.

**특징**:
- 분류:
  - **Sudden** (개념 급변, 예: 정책 변경)
  - **Gradual** (점진, 예: 계절 트렌드)
  - **Incremental** (느린 누적)
  - **Recurring** (주기적 — 명절 / 월말)
- 탐지 알고리즘:
  - **DDM** (Drift Detection Method, Gama 2004) — 분류 에러율 + 표준편차 추적
  - **EDDM** (Early DDM) — 두 분류 에러 사이 거리 추적
  - **ADWIN** (Adaptive Windowing, Bifet & Gavalda 2007) — 가변 window 통계 비교
  - **Page-Hinkley Test** — 누적 평균 변화 탐지
- 라벨이 늦게 들어옴(ground truth lag) → **proxy 신호** 활용: 사용자 행동 (클릭률 하락), confidence score 분포 등
- 대표 도구: **river** (online ML), **Alibi Detect**, **NannyML** (label-free)

**장점**:
- 모델 성능 저하의 **근본 원인 분리** — Data Drift 인지 Concept Drift 인지
- 재학습 효과 예측 — Concept Drift 라면 단순 재학습으로 회복 가능, Data Drift + 동일 관계라면 transfer 가능
- 비즈니스 신호 (정책 변경, 시장 변화) 와 모델 동작 연결

**단점**:
- 라벨 지연 — 정답이 늦게 들어와 사후 탐지가 됨 (의료 진단: 수개월)
- proxy 신호의 신뢰성 — 사용자 행동 변화가 drift 인지 다른 원인인지 모호
- 데이터 양 작으면 sudden vs noise 구분 어려움

**활용 예시**:
- COVID-19 — 모든 e-commerce / 여행 / 교통 모델이 sudden concept drift
- 신용평가 — 경기 사이클별 재학습
- 콘텐츠 추천 — 트렌드 변화 (예: 챌린지 유행)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Python 예제 (river ADWIN)**:
```python
from river import drift
import numpy as np

# 1) ADWIN — 라벨이 있는 경우 (분류 에러율 stream)
adwin = drift.ADWIN(delta=0.002)  # 더 작을수록 보수적
for x, y_true in production_stream:
    y_pred = model.predict_one(x)
    error = int(y_pred != y_true)
    adwin.update(error)
    if adwin.drift_detected:
        print(f"Concept drift detected at sample (error mean shift)")
        trigger_retraining_pipeline()
        model = retrain_with_recent_window()

# 2) Page-Hinkley — 누적 평균 shift
ph = drift.PageHinkley(min_instances=30, delta=0.005, threshold=50)
for sample in stream:
    ph.update(model.score(sample))
    if ph.drift_detected:
        alert("Score distribution shift — investigate")

# 3) Label-free (NannyML CBPM) — 라벨 부재 시 모델 confidence 로 추정
# (간략화) confidence 분포 shift → 성능 저하 예측
from scipy.stats import entropy
ref_conf_hist = np.histogram(reference_confidences, bins=20, density=True)[0]
cur_conf_hist = np.histogram(current_confidences, bins=20, density=True)[0]
js_div = 0.5 * entropy(ref_conf_hist, 0.5 * (ref_conf_hist + cur_conf_hist)) + \
         0.5 * entropy(cur_conf_hist, 0.5 * (ref_conf_hist + cur_conf_hist))
if js_div > 0.1:
    alert("Confidence drift — possible concept drift, awaiting ground truth")
```

**관련 패턴**: [Data Drift Detection](#data-drift), [Model Monitoring](#model-monitoring), [Shadow Model / Champion-Challenger](#shadow-champion-challenger)

---

<a id="shadow-champion-challenger"></a>

## 6. Shadow Model / Champion-Challenger

**목적**: 신규 모델(Challenger)을 production 트래픽에 노출하지 않은 채 **동일 입력을 복제 전송**하여 실제 prediction 분포 / latency / cost 를 기존 Champion 과 비교 검증한 뒤, 안전이 확인되면 점진적으로 promote 합니다.

**특징**:
- **Shadow Mode**: Challenger 의 prediction 은 사용자 응답에 반영되지 않음. 로그만 남김
- **A/B Test**: 트래픽 일부 (5% → 25% → 50%) 만 Challenger 응답 사용
- **Canary**: A/B 와 동일하나 **단계적 ramp-up + 자동 rollback** 기준 명시
- **Multi-Armed Bandit** — 통계적으로 우월한 모델로 트래픽을 동적 배분 (Thompson Sampling)
- 비교 지표: business metric (전환율) + technical metric (latency p99, cost / inference) + statistical (prediction 분포 KS test)
- 인프라: **service mesh** (Istio mirror), **feature flag** (LaunchDarkly, Unleash), **Seldon Core**, **KServe canary**

**장점**:
- production 데이터로 검증 — 학습/검증 데이터셋의 한계 극복
- 사용자 영향 0 (Shadow) — fail-safe
- A/B 결과로 모델 효과를 비즈니스 KPI 로 정량화 — 단순 AUC 보다 강력
- 자동 rollback 으로 사고 영향 최소화

**단점**:
- 인프라 복잡도 — 트래픽 복제 / 라우팅 / 결과 비교 파이프라인 필요
- **비용 2배** — Shadow 도 동일 인퍼런스 비용 발생
- 사용자 영향이 0이 아닌 경우 (예: 외부 API 호출하는 도구 사용) — Shadow 라도 부작용
- 통계적 유의성 확보까지 시간 — 효과 작으면 수 주 소요

**활용 예시**:
- 광고 CTR 모델 — 매 분기 challenger 띄우기
- 추천 시스템 — Multi-Armed Bandit 으로 자동 트래픽 배분
- 사기 탐지 — Shadow 로 false positive 비율 검증 후 promote

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Python 예제 (Shadow + Canary)**:
```python
from dataclasses import dataclass
import random
import time

@dataclass
class PredictionResult:
    label: int
    confidence: float
    latency_ms: float
    model_version: str

class ShadowDeployment:
    def __init__(self, champion, challenger, canary_pct: float = 0.0):
        self.champion = champion
        self.challenger = challenger
        self.canary_pct = canary_pct  # 0.0 = Shadow only, 0.05 = 5% canary

    def predict(self, x) -> PredictionResult:
        # 1) Champion — 사용자 응답에 사용
        t0 = time.perf_counter()
        champ_pred = self.champion.predict(x)
        champ_lat = (time.perf_counter() - t0) * 1000

        # 2) Challenger — 비동기 shadow (async 으로 별도 워커)
        shadow_executor.submit(self._shadow_eval, x, champ_pred, champ_lat)

        # 3) Canary 비율만큼 Challenger 응답 사용
        if random.random() < self.canary_pct:
            t1 = time.perf_counter()
            chal_pred = self.challenger.predict(x)
            chal_lat = (time.perf_counter() - t1) * 1000
            return PredictionResult(chal_pred, self.challenger.confidence(x), chal_lat, "challenger")

        return PredictionResult(champ_pred, self.champion.confidence(x), champ_lat, "champion")

    def _shadow_eval(self, x, champ_pred, champ_lat):
        chal_pred = self.challenger.predict(x)
        metrics_logger.log({
            "agree": champ_pred == chal_pred,
            "champ_lat_ms": champ_lat,
            # 분포 비교 / 비용 / 행동 분기 등 추가 기록
        })

# 자동 rollback 기준
if shadow_metrics.disagreement_rate() > 0.15:
    alert("Challenger disagreement > 15% — manual review required")
if shadow_metrics.p99_latency_increase() > 0.30:
    rollback_canary()
```

**관련 패턴**: [Model Registry](#model-registry), [Online vs Batch Inference](#online-batch-inference), [Model Monitoring](#model-monitoring)

---

<a id="ml-pipeline-dag"></a>

## 7. ML Pipeline (DAG)

**목적**: 데이터 수집 → 전처리 → feature 생성 → 학습 → 검증 → 배포 → 모니터링까지의 단계를 **DAG (Directed Acyclic Graph)** 로 선언하여 의존성 / 재현성 / 재실행 / 부분 캐시를 자동화합니다.

**특징**:
- **Step** (Task / Op) — 단일 동작 (전처리 1개, 학습 1개)
- **DAG** — step 간 의존 관계. cycle 금지
- **Idempotency** — 같은 입력으로 재실행 시 같은 출력
- **Caching / Memoization** — 입력 hash 가 같으면 step skip
- **Backfill** — 과거 일자 재실행
- **Trigger** — schedule (cron), event (S3 PutObject), sensor (data ready), manual
- 대표 시스템:
  - **Kubeflow Pipelines** — Kubernetes-native, ML 특화
  - **Airflow** — 범용 워크플로우, ML 의 사실상 표준
  - **Dagster** — software-defined assets, 데이터 lineage 강함
  - **Metaflow** — Netflix 출신, Python decorator 기반
  - **Argo Workflows** / **Prefect** / **MLflow Pipelines** / **TFX** (TensorFlow Extended) / **ZenML**

**장점**:
- 재현성 — 같은 DAG + 입력 데이터 hash → 같은 모델
- 부분 재실행 — 학습만 실패하면 학습 step 부터 resume (전처리 캐시 활용)
- 분산 실행 — step 단위로 Kubernetes pod / Spark job 분산
- lineage — 모델이 어떤 데이터 + 코드 + parameter 에서 나왔는지 자동 기록

**단점**:
- 학습 곡선 — DSL / decorator / SDK 차이가 많음
- 작은 모델은 DAG 가 과함 — Jupyter notebook 으로 충분
- step 간 데이터 전달 — pickle / parquet / S3 path 등 직렬화 비용
- 디버깅 어려움 — 원격 실행 + 로그 분산

**활용 예시**:
- Airbnb Bighead, Netflix Metaflow, Spotify Klio
- 매일 batch retraining (cron)
- 이벤트 기반 — 새 데이터 도착 즉시 재학습 (Airflow + S3 sensor)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Python 예제 (Metaflow)**:
```python
from metaflow import FlowSpec, step, Parameter, conda, retry, catch, batch

class ChurnFlow(FlowSpec):
    """매일 새벽 02:00 KST 트리거 (cron @daily) — 이탈 예측 모델 재학습"""

    snapshot_date = Parameter("date", default="latest")
    max_depth = Parameter("max_depth", default=5, type=int)

    @step
    def start(self):
        self.next(self.extract, self.validate_schema)

    @step
    def extract(self):
        from data_layer import load_events
        self.df = load_events(date=self.snapshot_date)
        self.next(self.preprocess)

    @retry(times=3)
    @step
    def validate_schema(self):
        # Great Expectations 검증 — schema drift 조기 차단
        from gx_suite import validate
        validate(self.df)
        self.next(self.preprocess)

    @step
    def preprocess(self, inputs):
        self.merge_artifacts(inputs)
        self.X, self.y = transform(self.df)
        self.next(self.train)

    @batch(cpu=8, memory=32_000, gpu=1)  # AWS Batch 에서 분산
    @step
    def train(self):
        import xgboost as xgb
        self.model = xgb.XGBClassifier(max_depth=self.max_depth).fit(self.X, self.y)
        self.next(self.evaluate)

    @step
    def evaluate(self):
        from sklearn.metrics import roc_auc_score
        self.auc = roc_auc_score(self.y_val, self.model.predict_proba(self.X_val)[:, 1])
        self.next(self.register)

    @catch(var="register_error")
    @step
    def register(self):
        if self.auc > 0.80:
            mlflow_register(self.model, stage="Staging")
        else:
            raise ValueError(f"AUC {self.auc:.3f} below threshold 0.80")
        self.next(self.end)

    @step
    def end(self):
        print(f"Run complete. AUC={self.auc:.3f}")

if __name__ == "__main__":
    ChurnFlow()
```

**관련 패턴**: [Feature Store](#feature-store), [Model Registry](#model-registry), [Data Contract](#data-contract)

---

<a id="online-batch-inference"></a>

## 8. Online vs Batch Inference

**목적**: 모델 서빙을 **요청-응답 즉시 (Online)** 와 **사전 계산 / 대량 (Batch)** 두 모드 중 사용 사례에 맞게 분리 설계하여 latency / throughput / cost 트레이드오프를 명시적으로 관리합니다.

**특징**:
- **Online (Real-time)**:
  - 단건 요청 ms 응답 (target: p99 < 100ms)
  - REST / gRPC API, 항상 hot
  - 비용: idle 시에도 인스턴스 점유
  - Feature 도 online store (Redis) 에서 가져옴
- **Batch (Offline)**:
  - 대량 (수백만 행) 한 번에 처리
  - 사전 계산 → 결과 테이블로 적재 → 서빙은 단순 KV lookup
  - 비용: 사용한 만큼만 (Spot 인스턴스 활용 가능)
- **Streaming (준-실시간)** — Kafka / Flink 로 마이크로배치 (수 초~수 분 지연)
- **Hybrid** — frequently accessed 는 batch 사전 계산, long-tail 은 online 실시간
- 대표 서빙 시스템: **TensorFlow Serving**, **TorchServe**, **Triton Inference Server**, **BentoML**, **KServe**, **Seldon**, **SageMaker Endpoints** / **Batch Transform**

**장점**:
- **Online**: 사용자 입력 즉시 반영 (검색, 추천 클릭, 사기 탐지)
- **Batch**: 비용 효율적 (off-peak 자원 활용), throughput 최대
- 두 모드 분리로 **각 모드 SLA 독립 관리** — online 다운돼도 batch 영향 없음

**단점**:
- **Online**: 비용 큼, autoscaling 필수, cold start 지연
- **Batch**: 결과가 stale (수 시간~1일 지연) — 새 사용자 미반영
- 두 모드 코드 중복 — 같은 모델을 두 환경에 배포 + 일관성 검증 부담

**활용 예시**:
- **Online**: 검색 랭킹, 광고 CTR, 결제 사기 탐지, 실시간 추천
- **Batch**: 일일 이메일 추천, 월간 churn risk score, A/B test 사전 segment
- **Hybrid**: 핵심 user 1M 명 batch precompute + 신규 user online compute

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Python 예제 (BentoML — Online + Batch 동시 노출)**:
```python
import bentoml
from bentoml.io import JSON, NumpyNdarray
import numpy as np

# 1) 학습된 모델을 BentoML store 에 저장
# (학습 코드에서 `bentoml.sklearn.save_model("churn", model)` 호출 가정)
churn_runner = bentoml.sklearn.get("churn:latest").to_runner()

svc = bentoml.Service("churn_service", runners=[churn_runner])

# 2) Online endpoint — REST 단건
@svc.api(input=JSON(), output=JSON())
async def predict_one(payload: dict) -> dict:
    # Online store (Redis) 에서 feature 조회
    features = await online_feature_store.get(payload["user_id"])
    x = np.array([features]).reshape(1, -1)
    proba = await churn_runner.predict_proba.async_run(x)
    return {"user_id": payload["user_id"], "score": float(proba[0, 1])}

# 3) Batch endpoint — 동일 모델, NumpyNdarray 로 대량 처리
@svc.api(input=NumpyNdarray(), output=NumpyNdarray(), batchable=True, batch_dim=0)
async def predict_batch(features: np.ndarray) -> np.ndarray:
    return await churn_runner.predict_proba.async_run(features)

# 4) Batch transform — Airflow 에서 호출되는 일일 사전 계산
# (별도 PySpark / Pandas job — Bento 모델을 import 해 동일 weight 사용)
"""
def daily_precompute(spark, date):
    df = spark.table("features.user_features").where(f"dt='{date}'")
    pdf = df.toPandas()
    scores = svc.predict_batch.run(pdf.to_numpy())  # 동일 BentoML 모델
    write_to_bigquery(pdf['user_id'], scores, table="churn.daily_scores")
"""
```

**관련 패턴**: [Feature Store](#feature-store), [Model Monitoring](#model-monitoring), [Shadow Model / Champion-Challenger](#shadow-champion-challenger)

---

<a id="data-contract"></a>

## 9. Data Contract

**목적**: 데이터 생산자(서비스 / 이벤트 publisher)와 소비자(ML 학습 / BI / 추천) 간 **스키마 + 의미론 + SLA 를 명시적 계약** 으로 묶고, CI 단계에서 자동 검증하여 schema drift 와 의미 오해석을 사전 차단합니다.

**특징**:
- Andrew Jones — *Driving Data Quality with Data Contracts* (2024, O'Reilly) 가 정식화
- 계약 요소:
  - **Schema** (필드 타입, nullability, default)
  - **Semantic** (`user_id` 가 회원 ID 인가 게스트 세션 ID 인가)
  - **Quality** (% non-null, 범위, freshness, uniqueness)
  - **SLA / SLO** (지연, 가용성)
  - **Owner / Steward** (담당자 — 변경 시 사전 협의)
  - **Versioning** (semver, deprecation 기간)
- 기술 스택:
  - **Schema Registry** (Confluent, AWS Glue) — Avro / Protobuf / JSON Schema
  - **Great Expectations** / **Soda Core** / **dbt tests** — quality 검증
  - **OpenLineage** — lineage 표준
  - **Monte Carlo** / **Bigeye** — observability
- shift-left — 데이터 품질을 production 사후가 아닌 publish 직전 검증

**장점**:
- ML 학습 실패의 가장 흔한 원인 (upstream schema 변경) 제거
- 데이터 소비자가 신뢰 가능 — 계약된 SLA 기반 의사결정
- 거버넌스 — 누가 어떤 데이터를 어떤 의미로 쓰는지 가시화
- Data Mesh 의 핵심 빌딩블록 — domain 간 인터페이스

**단점**:
- 도입 마찰 — 생산자 측 추가 비용, 조직적 합의 필요
- 계약 진화 비용 — breaking change 시 deprecation 윈도우 운영
- over-spec 위험 — 너무 strict 한 quality 가 false positive 폭증

**활용 예시**:
- GoCardless / Adevinta / PayPal 의 production data contract 도입 사례
- Kafka topic 마다 Avro schema + Confluent Schema Registry
- dbt 모델 출력에 column-level tests + freshness contract

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**YAML 예제 (Data Contract Spec)**:
```yaml
# contracts/events_user_signup.yaml
dataContractSpecification: 1.1.0
id: events.user_signup
info:
  title: User Signup Events
  version: 2.3.0
  owner: identity-team
  status: active
  contact:
    name: Identity Team
    email: identity-team@example.com

terms:
  usage: |
    회원 가입 완료 이벤트. ML 학습(이탈 예측 v3)이 의존.
    Breaking change 는 최소 30일 deprecation notice 필수.
  limitations: |
    PII (email, phone) 는 hash 처리 후 publish. raw 값 제공 금지.
  billing: free
  noticePeriod: P30D

servers:
  production:
    type: kafka
    host: kafka.internal:9092
    topic: events.user_signup.v2

models:
  signup_event:
    type: object
    fields:
      user_id:
        type: string
        required: true
        unique: false
        description: "내부 회원 UUID v4. 게스트 세션 ID 아님."
      signup_at:
        type: timestamp
        required: true
        description: "UTC ISO-8601. 클라이언트 시각이 아닌 서버 수신 시각."
      plan_tier:
        type: string
        enum: [free, basic, pro, enterprise]
        required: true
      country_code:
        type: string
        pattern: "^[A-Z]{2}$"  # ISO 3166-1 alpha-2
        required: true

quality:
  - type: sql
    description: "user_id 중복 < 0.01%"
    query: |
      SELECT 1.0 * COUNT(*) FILTER (WHERE cnt > 1) / COUNT(*)
      FROM (SELECT user_id, COUNT(*) cnt FROM signup_event GROUP BY 1) t
    mustBeLessThan: 0.0001
  - type: freshness
    description: "이벤트 도착 지연 p99 < 5분"
    field: signup_at
    mustBeLessThan: PT5M

servicelevels:
  availability:
    description: "Kafka 토픽 99.9% 가용"
    percentage: "99.9%"
  retention:
    description: "데이터 90일 보관"
    period: P90D
```

**관련 패턴**: [Feature Store](#feature-store), [Data Drift Detection](#data-drift), [ML Pipeline (DAG)](#ml-pipeline-dag), [Model Card](#model-card)

---

<a id="model-monitoring"></a>

## 10. Model Monitoring (Prediction Quality)

**목적**: production 모델의 **prediction 분포, 성능 지표, 비즈니스 KPI** 를 실시간으로 수집·시각화·알람화하여 drift / decay / 사고를 조기 발견합니다. infrastructure 메트릭(CPU / latency) 만 보는 일반 APM 과 differentiate — **모델 품질** 자체를 관측.

**특징**:
- 관측 4 계층:
  - **Service health** — latency, throughput, error rate ([Three Pillars](observability.md#three-pillars) 와 동일)
  - **Data quality** — input feature 의 null / range / distribution ([Data Drift](#data-drift))
  - **Prediction quality** — output 분포, confidence, decision rate
  - **Business KPI** — 전환율, 매출, churn — 모델이 만든 실제 가치
- **Ground Truth Lag** — 라벨이 늦게 들어옴 (광고: 분 단위, 의료: 개월 단위). proxy metric 으로 보강
- prediction 분포 비교 — Population Stability Index, KL divergence
- 슬라이스 모니터링 — 전체 평균 OK 라도 sub-population (특정 국가, 연령대) 에서 저하 가능
- 대표 도구: **Evidently AI**, **Arize AI**, **WhyLabs**, **Fiddler**, **Aporia**, **Datadog ML monitoring**, **Grafana + Prometheus + custom exporters**

**장점**:
- 모델 부패 (model decay) 조기 발견 — AUC 5% 하락 전에 prediction 분포 shift 가 먼저 보임
- 비즈니스 임팩트 정량화 — 모델 변경이 매출에 어떻게 영향?
- 사고 후속 분석 — 어느 슬라이스에서 무엇이 잘못됐는지 역추적
- 자동 재학습 트리거의 신호원

**단점**:
- 라벨 지연으로 직접 성능 메트릭 (accuracy, AUC) 은 항상 후행
- 카디널리티 폭발 — feature × slice 조합이 수천 시리즈가 됨
- false alarm — 통계 유의성과 실용 유의성 구분 필요
- ground truth 의 신뢰성 — feedback loop (모델이 만든 추천이 다시 라벨이 되는 selection bias)

**활용 예시**:
- Uber Manifold (예측 분포 시각화)
- Netflix Atlas — 모델 + 인프라 통합 모니터링
- 광고 — 시간대별 CTR predicted vs actual 분리 모니터링
- 의료 — 진단 모델 prediction 분포 + 6개월 후 ground truth backfill

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Python 예제 (Evidently + Prometheus)**:
```python
from evidently.report import Report
from evidently.metric_preset import RegressionPreset, ClassificationPreset
from prometheus_client import Gauge, Histogram, Counter
import pandas as pd

# 1) Prometheus 게이지 — Grafana / Alertmanager 와 통합
PRED_SCORE_HIST = Histogram(
    "model_pred_score",
    "Prediction score distribution",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    labelnames=["model_version", "slice"],
)
GROUND_TRUTH_LAG = Gauge(
    "model_ground_truth_lag_seconds",
    "Time between prediction and label arrival",
    labelnames=["model_version"],
)
SLICE_AUC = Gauge(
    "model_slice_auc",
    "AUC per slice (label-arrived window)",
    labelnames=["model_version", "slice"],
)

# 2) 실시간 prediction 로깅 — 매 호출
def log_prediction(user_id: str, score: float, slice_: str, model_version: str):
    PRED_SCORE_HIST.labels(model_version, slice_).observe(score)
    prediction_log.append({
        "user_id": user_id, "score": score, "slice": slice_,
        "model_version": model_version, "predicted_at": now(),
    })

# 3) Ground truth 도착 시 (지연 콜백) — 슬라이스별 성능 갱신
def on_label_arrival(user_id: str, label: int):
    rec = prediction_log.find(user_id)
    if rec is None:
        return
    lag = (now() - rec["predicted_at"]).total_seconds()
    GROUND_TRUTH_LAG.labels(rec["model_version"]).set(lag)
    labeled_buffer.append({**rec, "label": label})

# 4) 윈도우별 슬라이스 AUC 계산 (1시간마다 batch)
def hourly_evaluate():
    df = pd.DataFrame(labeled_buffer.drain_last_hour())
    for slice_, group in df.groupby("slice"):
        if len(group) < 100:  # 표본 부족 — skip
            continue
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(group["label"], group["score"])
        SLICE_AUC.labels(group["model_version"].iloc[0], slice_).set(auc)
        if auc < SLA_THRESHOLD[slice_]:
            alert(f"Slice {slice_} AUC {auc:.3f} below SLA")

# 5) Evidently 리포트 — 일일 종합 (drift + performance)
def daily_report():
    ref = pd.read_parquet("s3://lake/reference/train.parquet")
    cur = pd.read_parquet(f"s3://lake/serving/{today}.parquet")
    report = Report(metrics=[ClassificationPreset()])
    report.run(reference_data=ref, current_data=cur)
    report.save_html(f"s3://reports/model_monitor/{today}.html")
```

**관련 패턴**: [Data Drift Detection](#data-drift), [Concept Drift Detection](#concept-drift), [Shadow Model / Champion-Challenger](#shadow-champion-challenger), [Three Pillars](observability.md#three-pillars)

---
