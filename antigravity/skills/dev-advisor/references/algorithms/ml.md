# 머신러닝 기초 알고리즘 (Machine Learning Fundamentals)

데이터로부터 패턴을 학습하는 기초 머신러닝 알고리즘입니다. Production ML 시스템은 scikit-learn, TensorFlow, PyTorch 등 검증된 라이브러리 사용을 권장합니다 — 본 카테고리는 알고리즘 원리 학습용입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [k-means](#k-means) | K-Means Clustering | K-평균 군집화 | 중간 |
| [k-nearest-neighbors](#k-nearest-neighbors) | K-Nearest Neighbors (KNN) | K-최근접 이웃 | 낮음 |
| [linear-regression](#linear-regression) | Linear Regression | 선형 회귀 | 낮음 |
| [logistic-regression](#logistic-regression) | Logistic Regression | 로지스틱 회귀 | 중간 |
| [gradient-descent](#gradient-descent) | Gradient Descent | 경사 하강법 | 중간 |
| [naive-bayes](#naive-bayes) | Naive Bayes | 나이브 베이즈 | 낮음 |
| [transformer](#transformer) | Transformer | 트랜스포머 | 높음 |
| [attention](#attention) | Attention Mechanism | 어텐션 메커니즘 | 높음 |
| [hnsw](#hnsw) | HNSW | 계층적 근사 최근접 이웃 | 높음 |
| [quantization](#quantization) | Quantization | 모델 양자화 | 중간 |
| [speculative-decoding](#speculative-decoding) | Speculative Decoding | 투기적 디코딩 | 높음 |
| [pagerank](#pagerank) | PageRank | 페이지랭크 | 중간 |
| [node2vec](#node2vec) | Node2Vec | 노드투벡 | 중간 |

---

<a id="k-means"></a>
## 1. K-Means Clustering (K-평균 군집화)

**목적**: 데이터를 K개 군집으로 분할. 각 점을 가장 가까운 중심에 할당, 중심을 평균으로 재계산 반복

**시간 복잡도**: O(n * k * d * i) - n: 데이터, k: 군집, d: 차원, i: 반복

**공간 복잡도**: O((n + k) * d)

**특징**:
- 비지도 학습
- Lloyd's algorithm
- K 선택 필요 (elbow, silhouette)
- 초기화 중요 (K-means++)

**장점**:
- 단순하고 빠름
- 대규모 데이터 확장 가능
- 직관적 결과

**단점**:
- K 미리 지정해야 함
- 구형 군집만 잘 찾음
- 이상치에 민감
- 지역 최적에 빠질 수 있음

**활용 예시**:
- 고객 세분화
- 이미지 색상 양자화
- 문서 군집화
- 이상 탐지 전처리

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import kotlin.math.sqrt
import kotlin.random.Random

class KMeans(private val k: Int, private val maxIter: Int = 100) {
    var centroids: Array<DoubleArray> = emptyArray()
        private set

    private fun euclidean(a: DoubleArray, b: DoubleArray): Double {
        var sum = 0.0
        for (i in a.indices) {
            val d = a[i] - b[i]
            sum += d * d
        }
        return sqrt(sum)
    }

    // K-means++ 초기화
    private fun initCentroids(data: Array<DoubleArray>): Array<DoubleArray> {
        val rng = Random.Default
        val first = data[rng.nextInt(data.size)]
        val centers = mutableListOf(first.copyOf())
        while (centers.size < k) {
            val distSq = data.map { p ->
                centers.minOf { c -> euclidean(p, c).let { it * it } }
            }
            val total = distSq.sum()
            val target = rng.nextDouble() * total
            var cum = 0.0
            for (i in data.indices) {
                cum += distSq[i]
                if (cum >= target) {
                    centers.add(data[i].copyOf())
                    break
                }
            }
        }
        return centers.toTypedArray()
    }

    fun fit(data: Array<DoubleArray>): IntArray {
        val d = data[0].size
        centroids = initCentroids(data)
        val labels = IntArray(data.size)

        repeat(maxIter) {
            // Assign
            var changed = false
            for (i in data.indices) {
                val nearest = (0 until k).minBy { euclidean(data[i], centroids[it]) }
                if (labels[i] != nearest) {
                    labels[i] = nearest; changed = true
                }
            }

            // Update
            val sums = Array(k) { DoubleArray(d) }
            val counts = IntArray(k)
            for (i in data.indices) {
                counts[labels[i]]++
                for (j in 0 until d) sums[labels[i]][j] += data[i][j]
            }
            for (c in 0 until k) {
                if (counts[c] > 0) {
                    for (j in 0 until d) centroids[c][j] = sums[c][j] / counts[c]
                }
            }

            if (!changed) return labels
        }
        return labels
    }

    fun predict(point: DoubleArray): Int =
        (0 until k).minBy { euclidean(point, centroids[it]) }
}
```

**Note**: 실제로는 scikit-learn `KMeans` 또는 Spark MLlib 사용.

**관련 알고리즘**: DBSCAN, GMM, Hierarchical Clustering

---

<a id="k-nearest-neighbors"></a>
## 2. K-Nearest Neighbors (KNN, K-최근접 이웃)

**목적**: 새 데이터의 분류/회귀를 K개 가장 가까운 이웃의 다수결/평균으로 결정

**시간 복잡도**: O(n * d) 쿼리당 단순, O(log n) KD-Tree

**공간 복잡도**: O(n * d)

**특징**:
- 게으른 학습 (lazy learner)
- 비모수 (non-parametric)
- 거리 함수와 K 선택 중요
- 특성 스케일링 필수

**장점**:
- 학습 없음
- 단순하고 해석 가능
- 다중 클래스 자연스러움

**단점**:
- 예측 시 모든 데이터 거리 계산 필요
- 차원의 저주
- 메모리 많이 사용

**활용 예시**:
- 추천 시스템 (사용자 기반)
- 손글씨 인식
- 이상 탐지
- 결측치 보간

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import kotlin.math.sqrt

class KNN(private val k: Int) {
    private lateinit var X: Array<DoubleArray>
    private lateinit var y: IntArray

    fun fit(X: Array<DoubleArray>, y: IntArray) {
        this.X = X
        this.y = y
    }

    private fun distance(a: DoubleArray, b: DoubleArray): Double {
        var sum = 0.0
        for (i in a.indices) {
            val d = a[i] - b[i]
            sum += d * d
        }
        return sqrt(sum)
    }

    fun predict(point: DoubleArray): Int {
        // 가장 가까운 k개 인덱스
        val neighbors = X.indices
            .map { it to distance(point, X[it]) }
            .sortedBy { it.second }
            .take(k)
            .map { y[it.first] }

        return neighbors.groupingBy { it }.eachCount()
            .maxBy { it.value }.key
    }

    fun predictRegression(point: DoubleArray, targets: DoubleArray): Double {
        return X.indices
            .map { it to distance(point, X[it]) }
            .sortedBy { it.second }
            .take(k)
            .map { targets[it.first] }
            .average()
    }
}
```

**Note**: 대규모 데이터는 KD-Tree, Ball Tree, Annoy, FAISS 사용.

**관련 알고리즘**: K-Means, Decision Tree, KD-Tree

---

<a id="linear-regression"></a>
## 3. Linear Regression (선형 회귀)

**목적**: y = w·x + b로 연속 값 예측. 평균 제곱 오차 최소화

**시간 복잡도**: O(n * d² + d³) 정규방정식, O(i * n * d) 경사 하강

**공간 복잡도**: O(n * d)

**특징**:
- 닫힌 해: w = (XᵀX)⁻¹Xᵀy
- 경사 하강: w ← w - α∇L
- L2 정규화 변형: Ridge

**장점**:
- 해석 가능
- 빠른 학습/예측
- 닫힌 해 존재

**단점**:
- 선형 관계만 모델링
- 이상치에 민감
- 특성 공학 필요

**활용 예시**:
- 가격 예측
- 매출 예측
- 기준 모델 (baseline)
- 회귀 진단

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
class LinearRegression(
    private val learningRate: Double = 0.01,
    private val iterations: Int = 1000
) {
    private lateinit var weights: DoubleArray
    private var bias: Double = 0.0

    fun fit(X: Array<DoubleArray>, y: DoubleArray) {
        val n = X.size
        val d = X[0].size
        weights = DoubleArray(d)
        bias = 0.0

        repeat(iterations) {
            // 예측 + 오차
            val errors = DoubleArray(n) { i ->
                var pred = bias
                for (j in 0 until d) pred += weights[j] * X[i][j]
                pred - y[i]
            }

            // 그래디언트
            val gradW = DoubleArray(d)
            var gradB = 0.0
            for (i in 0 until n) {
                for (j in 0 until d) gradW[j] += errors[i] * X[i][j]
                gradB += errors[i]
            }

            // 갱신
            for (j in 0 until d) weights[j] -= learningRate * gradW[j] / n
            bias -= learningRate * gradB / n
        }
    }

    fun predict(x: DoubleArray): Double {
        var p = bias
        for (j in x.indices) p += weights[j] * x[j]
        return p
    }

    fun mse(X: Array<DoubleArray>, y: DoubleArray): Double {
        var sum = 0.0
        for (i in X.indices) {
            val e = predict(X[i]) - y[i]
            sum += e * e
        }
        return sum / X.size
    }
}
```

**Note**: 실제로는 scikit-learn `LinearRegression`, statsmodels 사용.

**관련 알고리즘**: Ridge, Lasso, Polynomial Regression

---

<a id="logistic-regression"></a>
## 4. Logistic Regression (로지스틱 회귀)

**목적**: 시그모이드 σ(w·x + b)로 이진 분류 확률 출력

**시간 복잡도**: O(i * n * d) - 경사 하강

**공간 복잡도**: O(n * d)

**특징**:
- σ(z) = 1 / (1 + e⁻ᶻ)
- 손실: binary cross-entropy
- 결정 경계: w·x + b = 0
- softmax로 다중 클래스 확장

**장점**:
- 확률 출력
- 해석 가능 (가중치 = 로그 odds)
- 빠르고 가벼움
- 정규화 적용 쉬움

**단점**:
- 선형 결정 경계만
- 이상치에 다소 민감
- 특성 상호작용 수동 추가 필요

**활용 예시**:
- 스팸 분류
- CTR 예측
- 신용 평가
- 의료 진단 (이진)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
import kotlin.math.exp
import kotlin.math.ln

class LogisticRegression(
    private val learningRate: Double = 0.1,
    private val iterations: Int = 1000
) {
    private lateinit var weights: DoubleArray
    private var bias: Double = 0.0

    private fun sigmoid(z: Double): Double = 1.0 / (1.0 + exp(-z))

    fun fit(X: Array<DoubleArray>, y: IntArray) {
        val n = X.size
        val d = X[0].size
        weights = DoubleArray(d)
        bias = 0.0

        repeat(iterations) {
            val gradW = DoubleArray(d)
            var gradB = 0.0
            for (i in 0 until n) {
                var z = bias
                for (j in 0 until d) z += weights[j] * X[i][j]
                val p = sigmoid(z)
                val err = p - y[i]
                for (j in 0 until d) gradW[j] += err * X[i][j]
                gradB += err
            }
            for (j in 0 until d) weights[j] -= learningRate * gradW[j] / n
            bias -= learningRate * gradB / n
        }
    }

    fun predictProba(x: DoubleArray): Double {
        var z = bias
        for (j in x.indices) z += weights[j] * x[j]
        return sigmoid(z)
    }

    fun predict(x: DoubleArray, threshold: Double = 0.5): Int =
        if (predictProba(x) >= threshold) 1 else 0

    fun crossEntropy(X: Array<DoubleArray>, y: IntArray): Double {
        var loss = 0.0
        for (i in X.indices) {
            val p = predictProba(X[i]).coerceIn(1e-15, 1 - 1e-15)
            loss += -(y[i] * ln(p) + (1 - y[i]) * ln(1 - p))
        }
        return loss / X.size
    }
}
```

**관련 알고리즘**: Linear Regression, Softmax Regression, SVM

---

<a id="gradient-descent"></a>
## 5. Gradient Descent (경사 하강법)

**목적**: 손실 함수 L(θ)의 그래디언트 반대 방향으로 파라미터 갱신 θ ← θ - α∇L

**시간 복잡도**: O(i * 평가 비용)

**공간 복잡도**: O(d) - 파라미터 크기

**특징**:
- Vanilla(batch): 전체 데이터로 그래디언트
- Mini-batch: 일부 샘플 (보통 32~256)
- Stochastic(SGD): 한 샘플
- 학습률 α 중요
- Momentum, Adam 등 가변 변형

**장점**:
- 일반적인 최적화 도구
- 메모리 효율 (SGD)
- GPU 병렬화 잘 됨

**단점**:
- 학습률 튜닝
- 지역 최적/안장점
- 수렴 보장 제한적

**활용 예시**:
- 신경망 학습 (필수)
- 로지스틱/선형 회귀
- Matrix Factorization
- 거의 모든 미분 가능 모델

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 배치 경사 하강
fun batchGradientDescent(
    grad: (DoubleArray) -> DoubleArray,
    init: DoubleArray,
    lr: Double = 0.01,
    iterations: Int = 1000
): DoubleArray {
    val theta = init.copyOf()
    repeat(iterations) {
        val g = grad(theta)
        for (i in theta.indices) theta[i] -= lr * g[i]
    }
    return theta
}

// 미니배치 SGD
fun miniBatchSGD(
    data: Array<DoubleArray>,
    targets: DoubleArray,
    gradOnBatch: (Array<DoubleArray>, DoubleArray, DoubleArray) -> DoubleArray,
    init: DoubleArray,
    lr: Double = 0.01,
    batchSize: Int = 32,
    epochs: Int = 50
): DoubleArray {
    val theta = init.copyOf()
    val n = data.size
    val indices = (0 until n).toMutableList()

    repeat(epochs) {
        indices.shuffle()
        var i = 0
        while (i < n) {
            val end = minOf(i + batchSize, n)
            val batchX = Array(end - i) { data[indices[i + it]] }
            val batchY = DoubleArray(end - i) { targets[indices[i + it]] }
            val g = gradOnBatch(batchX, batchY, theta)
            for (j in theta.indices) theta[j] -= lr * g[j]
            i = end
        }
    }
    return theta
}

// Momentum 변형
fun gdWithMomentum(
    grad: (DoubleArray) -> DoubleArray,
    init: DoubleArray,
    lr: Double = 0.01,
    momentum: Double = 0.9,
    iterations: Int = 1000
): DoubleArray {
    val theta = init.copyOf()
    val velocity = DoubleArray(theta.size)
    repeat(iterations) {
        val g = grad(theta)
        for (i in theta.indices) {
            velocity[i] = momentum * velocity[i] + lr * g[i]
            theta[i] -= velocity[i]
        }
    }
    return theta
}
```

**관련 알고리즘**: Adam, RMSProp, Newton's Method

---

<a id="naive-bayes"></a>
## 6. Naive Bayes (나이브 베이즈)

**목적**: 특성 독립 가정하에 베이즈 정리로 분류. P(y|x) ∝ P(y) ∏ P(xᵢ|y)

**시간 복잡도**: O(n * d) 학습, O(d * c) 예측

**공간 복잡도**: O(d * c) - c: 클래스 수

**특징**:
- 특성 독립 가정 (실제론 자주 깨짐)
- 변종: Gaussian, Multinomial, Bernoulli
- 학습 매우 빠름 (확률 카운팅만)

**장점**:
- 매우 빠른 학습/예측
- 적은 데이터로도 동작
- 다중 클래스 자연스러움
- 텍스트 분류에 강함

**단점**:
- 독립 가정 비현실적
- 결합 분포 무시
- 확률 값 자체는 부정확

**활용 예시**:
- 스팸 필터 (Multinomial NB)
- 감성 분석
- 문서 분류
- 의료 진단 빠른 baseline

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
import kotlin.math.ln
import kotlin.math.PI
import kotlin.math.exp
import kotlin.math.sqrt

// Gaussian Naive Bayes (연속 특성)
class GaussianNaiveBayes {
    private lateinit var classes: IntArray
    private lateinit var classPrior: DoubleArray
    private lateinit var mean: Array<DoubleArray>
    private lateinit var variance: Array<DoubleArray>

    fun fit(X: Array<DoubleArray>, y: IntArray) {
        classes = y.toSet().sorted().toIntArray()
        val d = X[0].size
        classPrior = DoubleArray(classes.size)
        mean = Array(classes.size) { DoubleArray(d) }
        variance = Array(classes.size) { DoubleArray(d) }

        for ((idx, c) in classes.withIndex()) {
            val members = (X.indices).filter { y[it] == c }
            classPrior[idx] = members.size.toDouble() / X.size

            for (j in 0 until d) {
                val values = members.map { X[it][j] }
                mean[idx][j] = values.average()
                val mu = mean[idx][j]
                variance[idx][j] = values.sumOf { (it - mu) * (it - mu) } / members.size + 1e-9
            }
        }
    }

    private fun logGaussian(x: Double, mu: Double, varv: Double): Double {
        return -0.5 * ln(2 * PI * varv) - (x - mu) * (x - mu) / (2 * varv)
    }

    fun predict(x: DoubleArray): Int {
        var bestC = classes[0]
        var bestLog = Double.NEGATIVE_INFINITY
        for ((idx, c) in classes.withIndex()) {
            var logP = ln(classPrior[idx])
            for (j in x.indices) {
                logP += logGaussian(x[j], mean[idx][j], variance[idx][j])
            }
            if (logP > bestLog) { bestLog = logP; bestC = c }
        }
        return bestC
    }
}

// Multinomial Naive Bayes (텍스트 카운트)
class MultinomialNaiveBayes(private val alpha: Double = 1.0) {
    private lateinit var classes: IntArray
    private lateinit var logPrior: DoubleArray
    private lateinit var logLikelihood: Array<DoubleArray>

    fun fit(X: Array<IntArray>, y: IntArray) {
        classes = y.toSet().sorted().toIntArray()
        val d = X[0].size
        logPrior = DoubleArray(classes.size)
        logLikelihood = Array(classes.size) { DoubleArray(d) }

        for ((idx, c) in classes.withIndex()) {
            val members = X.indices.filter { y[it] == c }
            logPrior[idx] = ln(members.size.toDouble() / X.size)
            val counts = IntArray(d)
            for (i in members) for (j in 0 until d) counts[j] += X[i][j]
            val total = counts.sum() + alpha * d
            for (j in 0 until d) logLikelihood[idx][j] = ln((counts[j] + alpha) / total)
        }
    }

    fun predict(x: IntArray): Int {
        var bestC = classes[0]
        var bestLog = Double.NEGATIVE_INFINITY
        for ((idx, c) in classes.withIndex()) {
            var logP = logPrior[idx]
            for (j in x.indices) logP += x[j] * logLikelihood[idx][j]
            if (logP > bestLog) { bestLog = logP; bestC = c }
        }
        return bestC
    }
}
```

**Note**: 실제로는 scikit-learn `GaussianNB`, `MultinomialNB`, `BernoulliNB` 사용.

**관련 알고리즘**: Logistic Regression, LDA, SVM

---

<a id="transformer"></a>
## 7. Transformer (트랜스포머)

**목적**: Self-Attention 기반으로 시퀀스 내 모든 위치 간 의존성을 병렬로 학습. Vaswani et al. "Attention Is All You Need" (2017)

**시간 복잡도**: O(n² · d) — n: 시퀀스 길이, d: 모델 차원 (Self-Attention)

**공간 복잡도**: O(n² + n · d) (어텐션 맵 + 임베딩)

**특징**:
- Encoder-Decoder 또는 Decoder-only 구조
- Positional Encoding 으로 순서 정보 주입
- Multi-Head Attention + Feed-Forward + Layer Norm 스택
- RNN 대비 병렬 학습 가능 (순서 의존 없음)

**장점**:
- 장거리 의존성 포착 탁월
- GPU 병렬화 친화적
- 대규모 pre-training → fine-tuning 패러다임의 기반

**단점**:
- 시퀀스 길이 n 에 대해 메모리 O(n²) — 긴 컨텍스트 비쌈
- 대용량 데이터/컴퓨트 필요
- 해석 어려움

**활용 예시**:
- LLM (GPT, BERT, LLaMA, Gemini)
- 번역 / 요약 / 코드 생성
- Vision Transformer (ViT), Audio (Whisper)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 의사코드**:
```kotlin
/** 트랜스포머 블록 (개념 의사코드) */
fun transformerBlock(x: Matrix, mask: Matrix?): Matrix {
    // Multi-Head Self-Attention
    val attn = multiHeadAttention(query = x, key = x, value = x, mask = mask)
    val x1 = layerNorm(x + attn)           // Add & Norm

    // Position-wise Feed-Forward
    val ff = relu(x1 * W1 + b1) * W2 + b2  // 2-layer MLP
    return layerNorm(x1 + ff)               // Add & Norm
}

fun multiHeadAttention(query: Matrix, key: Matrix, value: Matrix, mask: Matrix?): Matrix {
    val heads = (0 until numHeads).map { h ->
        val q = query * Wq[h]; val k = key * Wk[h]; val v = value * Wv[h]
        scaledDotProductAttention(q, k, v, mask)
    }
    return concat(heads) * Wo             // head 결합 후 projection
}

fun scaledDotProductAttention(q: Matrix, k: Matrix, v: Matrix, mask: Matrix?): Matrix {
    val scores = (q * k.T) / sqrt(dK.toDouble())  // 스케일된 내적
    val maskedScores = if (mask != null) scores + mask else scores
    return softmax(maskedScores) * v       // 어텐션 가중 합
}
```

**관련 알고리즘**: Attention Mechanism, HNSW (벡터 검색), Speculative Decoding

---

<a id="attention"></a>
## 8. Attention Mechanism (어텐션 메커니즘)

**목적**: 쿼리(Query)와 키(Key)의 유사도로 값(Value)을 가중 합산. 모델이 관련 위치에 "집중"하도록 합니다.

**시간 복잡도**: Scaled Dot-Product — O(n² · d); Linear Attention 변형 — O(n · d)

**공간 복잡도**: O(n² + n · d)

**특징**:
- Scaled Dot-Product Attention: softmax(QKᵀ / √dₖ) · V
- Multi-Head: h 개 헤드를 병렬 수행 후 concat
- Cross-Attention: 쿼리 ≠ 키/값 출처 (Encoder→Decoder)
- Causal Mask: 미래 토큰 차단 (autoregressive 디코딩)

**장점**:
- 위치 무관 의존성 포착
- 학습 가능한 soft alignment (Bahdanau 2015 → Vaswani 2017)
- KV-Cache 로 추론 시 반복 계산 제거

**단점**:
- Full attention 은 O(n²) 메모리 — FlashAttention 등으로 완화
- 절대적 위치 정보 부재 → Positional Encoding 별도 필요

**활용 예시**:
- LLM 모든 레이어
- Cross-attention (번역 decoder ↔ encoder)
- Diffusion 모델 U-Net (spatial attention)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 의사코드**:
```kotlin
import kotlin.math.sqrt

/**
 * Scaled Dot-Product Attention
 * @param q [seqLen × dK] 쿼리 행렬
 * @param k [seqLen × dK] 키 행렬
 * @param v [seqLen × dV] 값 행렬
 * @param mask 미래 토큰 차단용 causal mask (선택)
 */
fun scaledDotProductAttention(
    q: Array<DoubleArray>, k: Array<DoubleArray>, v: Array<DoubleArray>,
    mask: Array<BooleanArray>? = null
): Array<DoubleArray> {
    val dK = q[0].size
    val scale = sqrt(dK.toDouble())
    val n = q.size

    // scores[i][j] = q[i] · k[j] / √dK
    val scores = Array(n) { i ->
        DoubleArray(n) { j ->
            q[i].zip(k[j]).sumOf { (qi, kj) -> qi * kj } / scale
        }
    }

    // causal mask 적용 (autoregressive)
    mask?.let { m ->
        for (i in 0 until n) for (j in 0 until n)
            if (m[i][j]) scores[i][j] = Double.NEGATIVE_INFINITY
    }

    // row-wise softmax → weighted sum of v
    return Array(n) { i ->
        val expScores = DoubleArray(n) { j -> Math.exp(scores[i][j]) }
        val sumExp = expScores.sum()
        val weights = DoubleArray(n) { j -> expScores[j] / sumExp }
        DoubleArray(v[0].size) { d -> weights.indices.sumOf { j -> weights[j] * v[j][d] } }
    }
}
```

**관련 알고리즘**: Transformer, HNSW (벡터 유사도 검색)

---

<a id="hnsw"></a>
## 9. HNSW (Hierarchical Navigable Small World)

**목적**: 고차원 벡터 공간에서 근사 최근접 이웃(ANN)을 O(log n) 수준으로 탐색. Malkov & Yashunin 2018.

**시간 복잡도**: 빌드 O(n · log n · M²); 탐색 O(log n) 평균

**공간 복잡도**: O(n · M) — M: 레이어 당 최대 연결 수

**특징**:
- 계층적 근접 그래프 (상위 레이어 = 듬성, 하위 = 촘촘)
- 삽입 시 확률적 레이어 할당 (skip-list 유사)
- 탐색: 최상위 → 최하위 그리디 탐색 (ef_search 빔)
- 파라미터: M (연결 수), ef_construction (빌드 품질), ef_search (탐색 폭)

**장점**:
- 정확도-속도 트레이드오프 조절 가능 (ef_search)
- 동적 삽입 지원 (IVF 대비 유리)
- 실용 벡터 DB 에서 사실상 표준

**단점**:
- 메모리 상주 필요 (mmap 확장 가능)
- 삭제가 논리 삭제 후 재빌드 필요
- 고차원 저밀도 데이터에서 품질 저하

**활용 예시**:
- Qdrant, Weaviate, pgvector, Faiss (HNSW index)
- RAG 벡터 검색 (임베딩 유사도)
- 이미지/음성 유사 검색

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 의사코드**:
```kotlin
/**
 * HNSW 핵심 구조 (개념 의사코드)
 * 실제 구현은 hnswlib (C++) / Qdrant (Rust) 바인딩 사용 권장
 */
data class HNSWNode(val id: Int, val vector: DoubleArray) {
    // 레이어별 이웃 목록: layer → list of neighbor ids
    val neighbors: MutableMap<Int, MutableList<Int>> = mutableMapOf()
}

class HNSWIndex(private val M: Int = 16, private val efConstruction: Int = 200) {
    private val nodes = mutableListOf<HNSWNode>()
    private var entryPoint: HNSWNode? = null
    private val maxLayer get() = entryPoint?.neighbors?.keys?.maxOrNull() ?: 0

    /** 새 벡터 삽입 */
    fun insert(id: Int, vector: DoubleArray) {
        val level = randomLevel()          // 확률적 레이어 (기하분포)
        val newNode = HNSWNode(id, vector)
        nodes.add(newNode)

        var ep = entryPoint ?: run { entryPoint = newNode; return }

        // 상위 레이어: 그리디 탐색으로 entry point 갱신
        for (lc in maxLayer downTo level + 1)
            ep = greedySearch(ep, vector, lc, ef = 1).first()

        // 삽입 레이어~0: ef_construction 빔 탐색 + M개 연결
        for (lc in minOf(level, maxLayer) downTo 0) {
            val candidates = beamSearch(ep, vector, lc, ef = efConstruction)
            val selected = selectNeighbors(candidates, M)
            newNode.neighbors[lc] = selected.map { it.id }.toMutableList()
            selected.forEach { it.neighbors.getOrPut(lc) { mutableListOf() }.add(id) }
            ep = candidates.first()
        }
        if (level > maxLayer) entryPoint = newNode
    }

    /** ANN 탐색: 상위→하위 그리디, 최하위만 ef_search 빔 */
    fun search(query: DoubleArray, k: Int, efSearch: Int = 50): List<Int> {
        var ep = entryPoint ?: return emptyList()
        for (lc in maxLayer downTo 1) ep = greedySearch(ep, query, lc, ef = 1).first()
        return beamSearch(ep, query, 0, ef = efSearch).take(k).map { it.id }
    }

    private fun randomLevel(): Int {
        var l = 0
        while (Math.random() < 1.0 / M && l < 16) l++
        return l
    }

    // greedySearch / beamSearch / selectNeighbors 는 hnswlib 참조 구현
    private fun greedySearch(ep: HNSWNode, q: DoubleArray, layer: Int, ef: Int) = listOf(ep)
    private fun beamSearch(ep: HNSWNode, q: DoubleArray, layer: Int, ef: Int) = listOf(ep)
    private fun selectNeighbors(candidates: List<HNSWNode>, m: Int) = candidates.take(m)
}
```

**관련 알고리즘**: Attention Mechanism, Node2Vec (그래프 구조)

---

<a id="quantization"></a>
## 10. Quantization (모델 양자화)

**목적**: 부동소수점(FP32/BF16) 가중치를 저비트 정수(INT8/INT4)로 압축해 추론 메모리·속도를 개선합니다.

**시간 복잡도**: 추론 O(n·d) INT8 행렬곱 — FP32 대비 2~4× 빠름 (하드웨어 의존)

**공간 복잡도**: O(n·d / 압축비) — INT8 = FP32 의 1/4, INT4 = 1/8

**특징**:
- Post-Training Quantization (PTQ): 학습 후 적용, 빠름
- Quantization-Aware Training (QAT): 학습 중 fake-quant, 정확도↑
- 그룹 양자화: 가중치를 그룹별 scale/zero-point 관리
- AWQ (Activation-aware Weight Quantization): 중요 채널 보호
- GPTQ: 2차 Hessian 기반 최적화 양자화

**장점**:
- 메모리 대폭 절감 (70B 모델 → 35GB INT8)
- 추론 레이턴시 감소
- Edge / 온프레미스 배포 가능

**단점**:
- 정확도 소폭 손실 (특히 INT4)
- 하드웨어 INT8 연산 지원 필요 (CUDA, Apple Silicon)
- 양자화 후 fine-tuning 필요할 수 있음

**활용 예시**:
- llama.cpp (Q4_K_M, Q8_0)
- bitsandbytes (LLM.int8(), NF4)
- TensorRT, ONNX Runtime
- Ollama 로컬 모델 서빙

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 의사코드**:
```kotlin
/**
 * 대칭 INT8 양자화 / 역양자화 (개념 예시)
 * 실제 LLM 양자화는 bitsandbytes / llama.cpp / AWQ 라이브러리 사용
 */
object SymmetricInt8Quantizer {
    /**
     * FP32 가중치 텐서 → INT8 + scale 반환
     * scale = max(|w|) / 127
     */
    fun quantize(weights: FloatArray): Pair<ByteArray, Float> {
        val absMax = weights.maxOf { kotlin.math.abs(it) }.coerceAtLeast(1e-8f)
        val scale = absMax / 127f
        val quantized = ByteArray(weights.size) { i ->
            (weights[i] / scale).coerceIn(-127f, 127f).toInt().toByte()
        }
        return quantized to scale
    }

    /** INT8 + scale → FP32 복원 */
    fun dequantize(quantized: ByteArray, scale: Float): FloatArray =
        FloatArray(quantized.size) { i -> quantized[i] * scale }

    /**
     * INT8 행렬곱 (양자화 도메인)
     * 실제 하드웨어에서는 CUDA cublasSgemmEx / Apple ANE 사용
     */
    fun matMulInt8(a: Array<ByteArray>, b: Array<ByteArray>): Array<IntArray> {
        val m = a.size; val n = b[0].size; val k = b.size
        return Array(m) { i ->
            IntArray(n) { j ->
                (0 until k).sumOf { l -> a[i][l].toInt() * b[l][j].toInt() }
            }
        }
    }
}
```

**관련 알고리즘**: Speculative Decoding, Transformer

---

<a id="speculative-decoding"></a>
## 11. Speculative Decoding (투기적 디코딩)

**목적**: 작은 Draft 모델이 여러 토큰을 미리 생성하고, 큰 Target 모델이 병렬 검증하여 LLM 추론 속도를 높입니다.

**시간 복잡도**: 이론적 speedup = 1 / (1 - α·γ) — α: 수락률, γ: draft 길이; 실측 2~3× 향상

**공간 복잡도**: Draft + Target 모델 동시 로딩 필요 (메모리 증가)

**특징**:
- Draft 모델 (소형): γ 토큰 자기회귀 생성 (빠름)
- Target 모델 (대형): draft γ 토큰을 1-forward-pass 병렬 채점
- 거절 샘플링: draft 토큰이 target 분포와 불일치 시 거절 + 보정
- 수락된 토큰만 출력 → 품질 = target 모델과 동일 보장

**장점**:
- 출력 품질 무손실 (target 분포 유지)
- Autoregressive 병목 극복 (메모리 대역폭 → 계산 활용)
- Self-Speculative: 동일 모델의 초기 레이어를 draft 로 재활용 가능

**단점**:
- Draft 모델 추가 메모리 필요
- Draft 품질이 낮으면 수락률↓ → speedup 감소
- KV-Cache 관리 복잡도 증가

**활용 예시**:
- vLLM speculative decoding
- TensorRT-LLM draft model
- Google Medusa (multi-head draft)
- Apple MLX 로컬 추론

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 의사코드**:
```kotlin
/**
 * Speculative Decoding 루프 (개념 의사코드)
 * 실제 구현은 vLLM / TensorRT-LLM 참조
 */
fun speculativeDecoding(
    prompt: List<Int>,
    draftModel: LanguageModel,
    targetModel: LanguageModel,
    maxTokens: Int,
    gamma: Int = 4,          // draft 미리 생성 토큰 수
): List<Int> {
    val output = prompt.toMutableList()

    repeat(maxTokens) {
        // 1) Draft: 소형 모델로 γ 토큰 자기회귀 생성
        val draftTokens = mutableListOf<Int>()
        val draftLogits = mutableListOf<FloatArray>()
        var ctx = output.toList()
        repeat(gamma) {
            val logits = draftModel.forward(ctx)
            val token = sampleToken(logits)
            draftTokens += token
            draftLogits += logits
            ctx = ctx + token
        }

        // 2) Target: 1-forward-pass 로 γ+1 위치 병렬 채점
        val targetLogits = targetModel.forwardBatch(output + draftTokens) // γ+1 logits

        // 3) 거절 샘플링 — Leviathan et al. 2023
        var acceptedCount = 0
        for (i in 0 until gamma) {
            val pTarget = softmax(targetLogits[i])
            val pDraft  = softmax(draftLogits[i])
            val acceptProb = (pTarget[draftTokens[i]] / pDraft[draftTokens[i]]).coerceIn(0f, 1f)
            if (Math.random() < acceptProb) {
                output += draftTokens[i]
                acceptedCount++
            } else {
                // 거절: target 보정 분포에서 1토큰 샘플 후 중단
                val corrected = FloatArray(pTarget.size) { j ->
                    (pTarget[j] - pDraft[j]).coerceAtLeast(0f)
                }
                output += sampleToken(corrected)
                return@repeat
            }
        }
        // 전부 수락 시 target 의 γ+1 번째 토큰 추가
        if (acceptedCount == gamma) output += sampleToken(targetLogits[gamma])
    }
    return output
}

interface LanguageModel {
    fun forward(tokens: List<Int>): FloatArray
    fun forwardBatch(tokens: List<Int>): List<FloatArray>
}
fun sampleToken(logits: FloatArray): Int = logits.indices.maxByOrNull { logits[it] }!!
fun softmax(logits: FloatArray): FloatArray {
    val exp = FloatArray(logits.size) { Math.exp(logits[it].toDouble()).toFloat() }
    val sum = exp.sum(); return FloatArray(exp.size) { exp[it] / sum }
}
```

**관련 알고리즘**: Transformer, Quantization

---

<a id="pagerank"></a>
## 12. PageRank (페이지랭크)

**목적**: 방향 그래프에서 노드의 중요도(중심성)를 반복 전파로 계산. Brin & Page 1998 (Google 검색).

**시간 복잡도**: O(k · (V + E)) — k: 반복 횟수, V: 노드, E: 엣지; 수렴까지 보통 k=20~100

**공간 복잡도**: O(V + E)

**특징**:
- 랜덤 서퍼 모델: 링크를 따라 이동 + 확률 d 로 임의 점프
- 수식: PR(v) = (1-d)/N + d · Σ PR(u)/outDeg(u) (u → v 인 모든 u)
- 감쇠 인수(damping factor) d = 0.85 관례
- Dangling node (outlink 없음) 처리 필요

**장점**:
- 구조만으로 중요도 계산 (콘텐츠 불필요)
- 희소 행렬 power iteration → 대규모 그래프 확장
- 방향성 중요도 포착 (인용 수 + 인용자 중요도)

**단점**:
- 정적 그래프 가정 (실시간 업데이트 비쌈)
- Link farm / 스팸 조작 가능
- 느린 수렴 (역링크 많은 허브 노드)

**활용 예시**:
- 검색 엔진 링크 분석
- 학술 논문 인용 중요도 (CiteSeer)
- 소셜 그래프 인플루언서 탐지
- 지식 그래프 엔티티 중요도

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
/**
 * PageRank — power iteration
 * @param adjacency outEdges: nodeId → list of target nodeIds
 * @param d 감쇠 인수 (보통 0.85)
 * @param maxIter 최대 반복
 * @param tol 수렴 허용 오차
 */
fun pageRank(
    adjacency: Map<Int, List<Int>>,
    d: Double = 0.85,
    maxIter: Int = 100,
    tol: Double = 1e-6
): Map<Int, Double> {
    val nodes = adjacency.keys.toList()
    val n = nodes.size
    val outDeg = adjacency.mapValues { (_, v) -> v.size }

    // inEdges: 역방향 인덱스 (target → list of sources)
    val inEdges = mutableMapOf<Int, MutableList<Int>>()
    adjacency.forEach { (src, dests) -> dests.forEach { dst ->
        inEdges.getOrPut(dst) { mutableListOf() }.add(src)
    }}

    var rank = nodes.associateWith { 1.0 / n }.toMutableMap()

    repeat(maxIter) { iter ->
        val newRank = mutableMapOf<Int, Double>()
        var diff = 0.0

        for (v in nodes) {
            val incoming = inEdges[v] ?: emptyList()
            val contrib = incoming.sumOf { u ->
                rank[u]!! / outDeg[u]!!.coerceAtLeast(1)
            }
            newRank[v] = (1 - d) / n + d * contrib
            diff += kotlin.math.abs(newRank[v]!! - rank[v]!!)
        }

        rank = newRank
        if (diff < tol) return rank  // 수렴
    }
    return rank
}

// 사용 예
fun main() {
    val graph = mapOf(
        1 to listOf(2, 3),
        2 to listOf(3),
        3 to listOf(1),
        4 to listOf(3)
    )
    val scores = pageRank(graph)
    scores.entries.sortedByDescending { it.value }
        .forEach { (node, score) -> println("Node $node: %.4f".format(score)) }
}
```

**관련 알고리즘**: Node2Vec, HNSW (그래프 탐색)

---

<a id="node2vec"></a>
## 13. Node2Vec (노드투벡)

**목적**: 그래프 구조를 보존하는 저차원 노드 임베딩을 Random Walk + Word2Vec (Skip-Gram)으로 학습. Grover & Leskovec 2016.

**시간 복잡도**: Walk 생성 O(r · l · V); Skip-Gram 학습 O(r · l · V · d · k) — r: walk 수, l: walk 길이, k: window

**공간 복잡도**: O(V · d) — 임베딩 행렬

**특징**:
- BFS 편향(p 파라미터): 구조적 동등성 포착 (역할 유사)
- DFS 편향(q 파라미터): 커뮤니티/근접성 포착 (동일 커뮤니티)
- 2차 Random Walk: 현재 노드 + 이전 노드로 다음 노드 전이 확률 조정
- negative sampling 으로 Skip-Gram 학습 가속

**장점**:
- 비지도 학습 (레이블 불필요)
- 다운스트림 분류/링크 예측에 바로 활용
- p/q 로 탐색 바이어스 제어

**단점**:
- 전이 확률 사전 계산 메모리 O(V · avgDeg)
- 동적 그래프 대응 어려움 (재학습 필요)
- 하이퍼파라미터 (p, q, d, r, l) 튜닝 필요

**활용 예시**:
- 소셜 네트워크 커뮤니티 탐지
- 추천 시스템 (Pinterest PinSage 의 기반)
- 생물정보학 PPI 그래프 분석
- 지식 그래프 Entity 임베딩

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import kotlin.math.exp
import kotlin.random.Random

/**
 * Node2Vec — Biased Random Walk 생성 (핵심 로직)
 * Skip-Gram 학습은 Word2Vec 라이브러리(DL4J, gensim) 사용 권장
 */
class Node2Vec(
    private val graph: Map<Int, List<Int>>,
    private val p: Double = 1.0,   // return parameter (BFS 편향 ↓ = 구조적 동등성)
    private val q: Double = 1.0,   // in-out parameter (DFS 편향 ↓ = 커뮤니티)
    private val walkLen: Int = 80,
    private val numWalks: Int = 10
) {
    /**
     * 2차 Random Walk: prev → cur → next 전이 확률
     * - next == prev  : 1/p (되돌아가기)
     * - next ∈ N(prev): 1.0 (공통 이웃)
     * - 그 외         : 1/q (멀리 탐색)
     */
    private fun nextNode(prev: Int, cur: Int, rng: Random): Int {
        val neighbors = graph[cur] ?: return cur
        val prevNeighbors = graph[prev]?.toSet() ?: emptySet()

        val unnorm = neighbors.map { next ->
            when {
                next == prev             -> 1.0 / p
                next in prevNeighbors   -> 1.0
                else                    -> 1.0 / q
            }
        }
        val total = unnorm.sum()
        val probs = unnorm.map { it / total }

        // alias sampling (단순 구현 — 대규모 시 Alias Method 사용)
        val r = rng.nextDouble()
        var cumul = 0.0
        for ((i, prob) in probs.withIndex()) {
            cumul += prob
            if (r <= cumul) return neighbors[i]
        }
        return neighbors.last()
    }

    /** 모든 노드에서 numWalks 개 walk 생성 */
    fun generateWalks(seed: Long = 42L): List<List<Int>> {
        val rng = Random(seed)
        val nodes = graph.keys.toList()
        return buildList {
            repeat(numWalks) {
                nodes.shuffled(rng).forEach { start ->
                    val walk = mutableListOf(start)
                    while (walk.size < walkLen) {
                        val cur = walk.last()
                        val neighbors = graph[cur]
                        if (neighbors.isNullOrEmpty()) break
                        val next = if (walk.size == 1) {
                            neighbors[rng.nextInt(neighbors.size)]  // 첫 스텝: 균등
                        } else {
                            nextNode(walk[walk.size - 2], cur, rng)
                        }
                        walk += next
                    }
                    add(walk)
                }
            }
        }
    }
}

// 사용 예: walks 생성 → gensim Word2Vec 또는 DL4J Word2Vec 에 텍스트 형태로 전달
fun main() {
    val graph = mapOf(1 to listOf(2, 3), 2 to listOf(1, 3, 4), 3 to listOf(1, 2), 4 to listOf(2))
    val n2v = Node2Vec(graph, p = 0.5, q = 2.0, walkLen = 10, numWalks = 3)
    val walks = n2v.generateWalks()
    walks.take(3).forEach { println(it.joinToString(" ")) }
    // 이후: Word2Vec(walks, vectorSize=128, windowSize=5, minCount=1).train()
}
```

**관련 알고리즘**: PageRank, HNSW (그래프 기반 ANN)

---
