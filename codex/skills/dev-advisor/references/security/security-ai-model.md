# AI 모델 보안 (AI/LLM Model Security)

AI/ML 모델 자체를 대상으로 하는 공격 분류학(Attack Taxonomy). `ai-llm/guardrails.md`가 다루는 Prompt Injection · 출력 필터링 같은 **입출력 레이어 방어**와는 달리, 이 카테고리는 **모델 파라미터·학습 데이터·추론 결과 자체**를 공격 표면으로 삼는 위협을 다룬다.

참조 프레임워크: MITRE ATLAS (Adversarial Threat Landscape for AI Systems), OWASP LLM Top 10 2025, NIST AI RMF 1.0.

**관련 원칙·규제 (P0 신설)**: [`../principles/professional-ethics.md#eu-ai-act-2024`](../principles/professional-ethics.md#eu-ai-act-2024) — EU AI Act 2024 의 위험 분류 (Unacceptable / High / Limited / Minimal) · 고위험 시스템 의무 (적합성 평가 · 데이터 거버넌스 · 인적 감시 · 로그 보존) — AI 모델 보안 통제의 규제·법적 근거. [`../principles/professional-ethics.md#acm-code-ethics-2018`](../principles/professional-ethics.md#acm-code-ethics-2018) — ACM 윤리 코드 (2018) 의 AI 책임 원칙도 함께 참조.

## LLM/Agent 보안 확장 범위

LLM 앱과 에이전트 시스템은 모델 공격과 애플리케이션 보안 경계가 겹친다. `security-audit`에서는 아래 항목을 별도 체크리스트로 본다.

| 항목 | 점검 기준 | 관련 도메인 |
|---|---|---|
| Prompt Injection | 직접/간접 injection, instruction hierarchy 우회, hidden content 처리 | `security-ai-model.md#4-adversarial-inputs-evasion-attack-적대적-입력-회피-공격`, `patterns/ai-llm.md` |
| Tool Permission | tool allowlist, scoped token, human approval, destructive action gating | `security-authz.md#authz-least-privilege`, `security-sdlc.md#1-threat-modeling-stride-dread-pasta` |
| RAG / Vector DB 격리 | tenant isolation, embedding ACL, metadata filter, retrieval audit | `security-data-protection.md`, `algorithms/search-systems.md#vector-search` |
| Output Handling | structured validation, escaping, unsafe code/SQL/shell output 차단 | `security-api-web.md`, `patterns/ai-llm.md` |
| System Prompt Leakage | prompt/secret 분리, prompt exposure 테스트, 모델 추출 방어 | `security-ai-model.md#1-model-extraction-theft-모델-복제-공격` |
| Agent Audit / Evals | tool call log, eval set, red-team replay, regression threshold | `security-detect-respond.md#audit-log-tamper-evident`, `quality/qc.md#qc-test-execution-evidence` |

위 항목은 OWASP LLM Top 10 2025와 MITRE ATLAS를 보조 기준으로 사용하되, 실제 판정은 데이터 민감도, 권한 범위, tool side effect, blast radius를 함께 본다.

---

## 1. Model Extraction / Theft (모델 복제 공격)

**목적/위협**: 공개 API를 대량 쿼리하여 응답만으로 내부 모델을 근사한 "student model"을 훈련, 지적재산(모델 가중치)을 탈취합니다. MITRE ATLAS AML.T0044 (ML Model Inference API Access).

**특징**:
- 공격자는 정상 사용자처럼 다양한 입력을 API에 전달하고 출력(logit/label/임베딩)을 수집
- Knockoff-Net, CopyCat-CNN 등 학술 공격이 실제 API에도 적용됨
- OWASP LLM10:2025 Unbounded Consumption — 무제한 쿼리 허용 시 API 비용 폭발 + 복제 위험 동시 존재
- 완전 복제보다는 **기능 근사(functional clone)**를 목표로 하는 경우가 많음
- LLM의 경우 fine-tuning 방향 추론, 내부 system prompt 역공학도 포함

**장점 (방어 시)**:
- Query budget 제한으로 공격 비용 증가
- 응답 perturbation으로 student model 정확도 저하 가능

**단점 (방어 시)**:
- 정상 사용 vs 추출 공격 구분 어려움
- API 완전 오픈인 SaaS에서 쿼리 제한이 사용자 경험과 충돌

**활용 예시**:
- 상용 감정 분석 API → student model 학습 후 자체 서비스 오픈
- 의료 진단 AI API 반복 쿼리 → 유사 모델 복제
- GPT-4 API 대규모 쿼리로 소형 오픈소스 모델 fine-tuning

**난이도**: 중간 | **사용 빈도 (공격)**: ★★★★☆

**방어 코드 예제 (Kotlin — API Query Budget Enforcement)**:
```kotlin
/**
 * 클라이언트별 일일 쿼리 예산을 강제하여 모델 복제 공격 비용을 증가시킵니다.
 * Redis 슬라이딩 윈도우 기반 rate limiter.
 */
@Service
class ModelQueryBudgetService(private val redis: ReactiveRedisTemplate<String, Long>) {

    private val dailyLimit = 1_000L          // 일반 tier: 일 1000회
    private val extractionThreshold = 500L   // 500회 이후 응답 perturbation 시작

    fun checkAndRecord(clientId: String): QueryDecision {
        val key = "model:query:$clientId:${LocalDate.now()}"
        val count = redis.opsForValue()
            .increment(key)
            .doOnNext { cnt -> if (cnt == 1L) redis.expire(key, Duration.ofDays(1)) }
            .block() ?: 0L

        return when {
            count > dailyLimit         -> QueryDecision.REJECT
            count > extractionThreshold -> QueryDecision.RESPOND_WITH_NOISE  // logit perturbation
            else                       -> QueryDecision.ALLOW
        }
    }
}

enum class QueryDecision { ALLOW, RESPOND_WITH_NOISE, REJECT }

// 컨트롤러에서 RESPOND_WITH_NOISE 시 응답 confidence에 epsilon noise 주입
fun addPerturbation(probs: FloatArray, epsilon: Float = 0.05f): FloatArray =
    probs.map { p -> (p + Random.nextFloat() * epsilon).coerceIn(0f, 1f) }.toFloatArray()
```

**관련 패턴**: Least Privilege, Defense in Depth, Membership Inference Attack

---

## 2. Membership Inference Attack (멤버십 추론 공격)

**목적/위협**: 특정 데이터 포인트(예: 개인 의료 기록, 이메일)가 모델의 학습 데이터셋에 포함되었는지를 모델 출력(confidence score)만으로 추론합니다. MITRE ATLAS AML.T0024.

**특징**:
- 학습 데이터는 모델이 "외운" 패턴에 대해 더 높은 confidence를 반환하는 경향 이용
- Shadow model 공격: 공격자가 유사 분포 데이터로 shadow model을 훈련 → in/out membership 구분 classifier 학습
- LLM에서는 verbatim memorization 탐지에 응용 (학습 텍스트 정확히 재현 여부 확인)
- GDPR "잊혀질 권리" 위반 가능성 — 특정 개인 데이터가 모델에 남아 있음을 증명할 수 있음

**장점 (방어 시)**:
- Differential Privacy로 멤버십 구분 정보 통계적 제거 가능
- Label smoothing, confidence clipping으로 신호 약화

**단점 (방어 시)**:
- Differential Privacy 강도(epsilon) 높일수록 모델 정확도 하락 trade-off
- 이미 배포된 모델에 소급 적용 불가

**활용 예시**:
- 의료 AI — "이 환자 기록이 학습에 쓰였는가?" 추론 → 개인정보 침해
- 금융 모델 — 특정 거래 데이터 포함 여부 추론
- LLM 저작권 소송 — 특정 저작물이 학습 데이터에 있었음을 소명

**난이도**: 높음 | **사용 빈도 (공격)**: ★★★☆☆

**방어 코드 예제 (Python — Differential Privacy with TensorFlow Privacy)**:
```python
# TensorFlow Privacy — DP-SGD로 학습, 멤버십 추론 신호 억제
# MITRE ATLAS AML.T0024 완화 통제

import tensorflow as tf
from tensorflow_privacy.privacy.optimizers.dp_optimizer_keras import DPKerasSGDOptimizer
from tensorflow_privacy.privacy.analysis import compute_dp_sgd_privacy

# epsilon: 프라이버시 예산 (낮을수록 강한 보호, 낮을수록 정확도 하락)
# delta:   개인정보 누출 확률 상한 (1e-5 권장)
DP_EPSILON = 3.0
DP_DELTA   = 1e-5
NOISE_MULT = 1.1    # 그래디언트 노이즈 배수
L2_CLIP    = 1.0    # 그래디언트 클리핑 norm

optimizer = DPKerasSGDOptimizer(
    l2_norm_clip=L2_CLIP,
    noise_multiplier=NOISE_MULT,
    num_microbatches=1,
    learning_rate=0.01,
)

model.compile(optimizer=optimizer, loss="categorical_crossentropy", metrics=["accuracy"])

# 학습 후 소비된 프라이버시 예산 계산
eps, _ = compute_dp_sgd_privacy(
    n=TRAIN_SIZE,
    batch_size=BATCH_SIZE,
    noise_multiplier=NOISE_MULT,
    epochs=EPOCHS,
    delta=DP_DELTA,
)
assert eps <= DP_EPSILON, f"프라이버시 예산 초과: ε={eps:.2f}"
```

**관련 패턴**: Data Poisoning, Model Extraction, compliance.md#GDPR

---

## 3. Data Poisoning (학습 데이터 오염 공격)

**목적/위협**: 학습 데이터에 악의적으로 조작된 샘플을 삽입하여, 특정 입력(trigger)에 대해 공격자가 원하는 출력을 내도록 모델에 backdoor를 심거나 전반적 성능을 저하시킵니다. MITRE ATLAS AML.T0020.

**특징**:
- **Backdoor(Trojan) Attack**: 특정 trigger 패턴(예: 이미지 구석의 흰 점)이 있을 때만 오분류 유도. trigger 없으면 정상 동작
- **Label Flipping**: 특정 클래스 데이터의 레이블을 의도적으로 뒤집어 삽입
- **Gradient-Matching Poison**: 특정 테스트 샘플에 대해 그래디언트 방향을 조작한 독성 샘플 생성 (clean-label 공격 — 레이블은 올바름)
- LLM fine-tuning 데이터 오염: 특정 prompt에 대해 유해 응답을 내도록 훈련 데이터 조작
- 공개 데이터셋 poisoning — Hugging Face, Common Crawl 기여 데이터에 독성 삽입

**장점 (방어 시)**:
- 학습 전 데이터 정제(cleansing)로 독성 샘플 제거 가능
- Spectral Signatures, Activation Clustering으로 backdoor 탐지

**단점 (방어 시)**:
- Clean-label 공격은 레이블 검증만으론 탐지 불가
- 외부 데이터셋 사용 시 전수 검증 현실적 어려움

**활용 예시**:
- 안면 인식 모델 — 선글라스 착용 시 항상 특정 인물로 인식
- 악성코드 탐지 AI — 특정 문자열 있으면 항상 양성으로 분류
- LLM RLHF 데이터 조작 — 특정 주제 질문에 편향 응답 유도

**난이도**: 높음 | **사용 빈도 (공격)**: ★★★☆☆

**방어 코드 예제 (Python — Activation Clustering 기반 Backdoor 탐지)**:
```python
# ART(Adversarial Robustness Toolbox) — Activation Clustering으로 backdoor 탐지
# MITRE ATLAS AML.T0020 완화 통제

from art.defences.detector.poison import ActivationDefence
import numpy as np

def detect_backdoor(model, x_train: np.ndarray, y_train: np.ndarray) -> tuple[np.ndarray, dict]:
    """
    활성화 벡터 클러스터링으로 독성 샘플(backdoor trigger 포함)을 탐지합니다.
    정상 샘플과 독성 샘플은 마지막 은닉층 활성화 패턴이 다른 군집을 형성합니다.
    """
    defence = ActivationDefence(
        classifier=model,
        x_train=x_train,
        y_train=y_train,
    )
    report, is_clean = defence.detect_poison(
        nb_clusters=2,          # 클래스당 2 군집 (정상 vs 독성)
        nb_dims=10,             # PCA 차원 축소
        reduce="PCA",
    )
    poison_indices = np.where(~is_clean.astype(bool))[0]
    return poison_indices, report

# 독성 샘플 제거 후 재학습
poison_idx, report = detect_backdoor(model, x_train, y_train)
x_clean = np.delete(x_train, poison_idx, axis=0)
y_clean = np.delete(y_train, poison_idx, axis=0)
print(f"독성 샘플 {len(poison_idx)}개 제거 후 재학습")
```

**관련 패턴**: Defense in Depth, Membership Inference Attack, security-supply-chain.md

---

## 4. Adversarial Inputs / Evasion Attack (적대적 입력 / 회피 공격)

**목적/위협**: 사람 눈에는 정상으로 보이는 미세한 perturbation을 입력에 가해 모델이 잘못 분류하도록 유도합니다. MITRE ATLAS AML.T0015 (Evade ML Model).

**특징**:
- **White-box 공격 (그래디언트 접근 가능)**:
  - FGSM (Fast Gradient Sign Method): `x_adv = x + ε · sign(∇_x L(θ, x, y))`
  - PGD (Projected Gradient Descent, Madry et al.): FGSM 반복 적용 + norm 제약
  - C&W Attack: 최적화 기반, L0/L2/L∞ norm 최소화
- **Black-box 공격 (API 접근만)**:
  - Transfer Attack: 다른 모델에서 만든 adversarial sample 이전
  - Square Attack, NES (Natural Evolution Strategy) 쿼리 기반
- **물리 세계 공격**: 정지 표지판에 스티커 → 자율주행 오인식
- LLM에서는 token-level perturbation → 안전 필터 우회

**장점 (방어 시)**:
- Adversarial Training(적대적 훈련)으로 robustness 향상 가능
- Certified Defense (randomized smoothing) — 수학적 robustness 보증

**단점 (방어 시)**:
- Adversarial Training은 학습 비용 2~10배 증가
- 특정 공격에 강해지면 다른 공격에 취약해지는 trade-off 존재
- 완전한 방어는 이론상 불가능 (No Free Lunch)

**활용 예시**:
- 이미지 분류 API — FGSM 적용 이미지로 콘텐츠 필터 우회
- 안면 인식 — 특수 안경 착용으로 타인 행세
- 악성코드 탐지 우회 — 바이너리 미세 조작으로 ML 탐지기 회피
- 스팸 필터 우회 — 단어 교체/typo 삽입

**난이도**: 높음 | **사용 빈도 (공격)**: ★★★★☆

**방어 코드 예제 (Python — PGD Adversarial Training)**:
```python
# PGD 적대적 훈련 — MITRE ATLAS AML.T0015 완화 통제
# 학습 시 adversarial sample 생성 후 정상 sample과 함께 학습

import torch
import torch.nn.functional as F

def pgd_attack(
    model: torch.nn.Module,
    x: torch.Tensor,
    y: torch.Tensor,
    epsilon: float = 8/255,   # L∞ perturbation 한계
    alpha: float   = 2/255,   # 스텝 크기
    steps: int     = 10,
) -> torch.Tensor:
    """
    PGD(Projected Gradient Descent) 공격으로 적대적 샘플을 생성합니다.
    Adversarial Training에서 학습 배치마다 호출됩니다.
    """
    x_adv = x.clone().detach().requires_grad_(True)
    for _ in range(steps):
        loss = F.cross_entropy(model(x_adv), y)
        loss.backward()
        x_adv = x_adv + alpha * x_adv.grad.sign()
        x_adv = torch.clamp(x_adv, x - epsilon, x + epsilon)  # ε-ball projection
        x_adv = torch.clamp(x_adv, 0, 1).detach().requires_grad_(True)
    return x_adv

def adversarial_train_step(model, optimizer, x_batch, y_batch):
    """정상 샘플과 적대적 샘플 혼합 학습"""
    x_adv = pgd_attack(model, x_batch, y_batch)
    optimizer.zero_grad()
    loss = 0.5 * F.cross_entropy(model(x_batch), y_batch) \
         + 0.5 * F.cross_entropy(model(x_adv),   y_batch)
    loss.backward()
    optimizer.step()
    return loss.item()
```

**관련 패턴**: Defense in Depth, Data Poisoning, ai-llm/guardrails.md

---

## 5. Federated Learning 보안 (분산 학습 위협과 방어)

**목적/위협**: 여러 참여자(클라이언트)가 데이터를 공유하지 않고 로컬 그래디언트만 집계하는 Federated Learning(FL)에서 발생하는 보안 위협과 방어 패턴. MITRE ATLAS AML.T0020 (악성 ML 아티팩트), AML.T0024 (추론 공격).

**특징**:
- **Byzantine 공격**: 악성 클라이언트가 조작된 그래디언트/가중치를 집계 서버에 전송 → 글로벌 모델 오염
  - Data Poisoning + Model Poisoning 동시 가능
- **그래디언트 역공학 (Gradient Inversion)**: 집계 전 다른 참여자의 그래디언트에서 원본 학습 데이터 복원 (DLG, R-GAP 공격)
- **Free-rider 공격**: 기여 없이 글로벌 모델만 다운로드하는 참여자
- **집계 알고리즘 취약점**: 단순 FedAvg는 Byzantine 내성 없음

**방어 기법**:
| 위협 | 방어 |
|------|------|
| Byzantine 공격 | Byzantine-robust 집계 (Krum, Trimmed Mean, FLTrust) |
| 그래디언트 역공학 | Secure Aggregation (MPC), Differential Privacy |
| 모델 poisoning | Contribution evaluation + 이상 클라이언트 제거 |
| 통신 도청 | TLS + Secure Aggregation |

**장점 (방어 시)**:
- Differential Privacy + Secure Aggregation 조합이 현재 가장 검증된 접근
- Byzantine-robust 집계로 악성 클라이언트 비율 f < 1/2 이하면 수렴 보장 (일부 알고리즘)

**단점 (방어 시)**:
- Secure Aggregation(MPC)은 통신 오버헤드 O(n²) 가능
- DP noise 강도와 모델 유용성 trade-off
- Byzantine-robust 집계는 non-IID 데이터에서 성능 저하

**활용 예시**:
- 병원 간 FL 암 진단 모델 (데이터 공유 불가 규제 환경)
- 모바일 키보드 예측 모델 (Google GBoard FL)
- 금융 기관 간 사기 탐지 공동 학습

**난이도**: 매우 높음 | **사용 빈도**: ★★☆☆☆

**방어 코드 예제 (Python — Trimmed Mean Byzantine-Robust 집계)**:
```python
# Byzantine-robust 집계 — Trimmed Mean
# MITRE ATLAS AML.T0020 완화: 악성 클라이언트 그래디언트 제거

import numpy as np
from typing import Sequence

def trimmed_mean_aggregate(
    client_gradients: Sequence[np.ndarray],
    trim_ratio: float = 0.1,  # 상/하위 10% 제거
) -> np.ndarray:
    """
    각 파라미터 차원별로 상/하위 trim_ratio 비율의 값을 제거하고
    나머지 평균으로 집계합니다. Byzantine 클라이언트 영향을 제한합니다.
    """
    stacked = np.stack(client_gradients, axis=0)   # (n_clients, param_dim)
    n = stacked.shape[0]
    k = max(1, int(n * trim_ratio))                # 제거할 개수

    sorted_grads = np.sort(stacked, axis=0)
    trimmed = sorted_grads[k: n - k]              # 상/하위 k개 제거
    return trimmed.mean(axis=0)

def secure_aggregate_with_dp(
    client_gradients: Sequence[np.ndarray],
    noise_scale: float = 0.01,  # DP noise sigma
    clip_norm: float   = 1.0,   # 그래디언트 클리핑
) -> np.ndarray:
    """
    Differential Privacy + 클리핑 적용 후 집계.
    그래디언트 역공학(DLG) 공격에 대한 방어.
    """
    clipped = []
    for g in client_gradients:
        norm = np.linalg.norm(g)
        clipped.append(g / max(1.0, norm / clip_norm))

    aggregated = np.mean(clipped, axis=0)
    noise = np.random.normal(0, noise_scale, aggregated.shape)
    return aggregated + noise  # DP noise 주입
```

**관련 패턴**: Data Poisoning, Membership Inference Attack, Defense in Depth, compliance.md#GDPR

---
