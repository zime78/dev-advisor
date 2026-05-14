# 검색·랭킹 알고리즘 (Search & Ranking Algorithms)

Information Retrieval 분야의 정평 있는 8 알고리즘. Elasticsearch / OpenSearch / Lucene / Solr / Vespa 의 핵심. **full-text 검색 + 랭킹 + 자동완성** 의 표준.

**원전·표준 참고**:
- Stephen Robertson, Hugo Zaragoza — *The Probabilistic Relevance Framework: BM25 and Beyond* (FnTIR, 2009)
- Christopher Manning, Prabhakar Raghavan, Hinrich Schütze — *Introduction to Information Retrieval* (Cambridge, 2008)
- Bruce Croft, Donald Metzler, Trevor Strohman — *Search Engines: Information Retrieval in Practice* (2009)
- Burges, Shaked, Renshaw — *Learning to Rank using Gradient Descent* (ICML 2005) — RankNet
- Apache Lucene Documentation
- Elasticsearch — Practical BM25 (https://www.elastic.co/blog/practical-bm25-part-1-how-shards-affect-relevance-scoring-in-elasticsearch)

## 알고리즘 목차

| ID | 알고리즘 | 카테고리 | 용도 |
|----|---------|---------|------|
| [inverted-index](#inverted-index) | Inverted Index | Indexing | full-text 기초 |
| [tf-idf](#tf-idf) | TF-IDF | Scoring | 고전 가중치 |
| [bm25](#bm25) | BM25 | Scoring | 모던 standard |
| [vector-search](#vector-search) | Vector Search | Semantic | embedding |
| [hybrid-search](#hybrid-search) | Hybrid Search | Fusion | BM25 + Vector |
| [faceted-search](#faceted-search) | Faceted Aggregation | Filter | drill-down |
| [autocomplete](#autocomplete) | Autocomplete | Suggestion | type-ahead |
| [learning-to-rank](#learning-to-rank) | LTR | ML Ranking | Pairwise/Listwise |

**관련 카탈로그**:
- [string.md](string.md) — KMP / Aho-Corasick / Suffix Array / Trie (basic string matching)
- [ml.md](ml.md) — HNSW (Vector Search), Transformer (embedding)
- [`../patterns/domains/ecommerce.md`](../patterns/domains/ecommerce.md) — 검색·발견 응용

---

<a id="inverted-index"></a>
## 1. Inverted Index (역색인)

**목적**: term → posting list 매핑으로 full-text 검색 기초 구조. document → terms 의 forward index 를 뒤집어 term → documents 로 만든다. Lucene / Elasticsearch / Solr 의 핵심.

**시간 복잡도**:
- 색인 구축: O(N · L) — N: 문서 수, L: 문서당 평균 term 수
- 검색: O(|posting list|) — term lookup 은 O(1) hash 또는 O(log V) trie

**공간 복잡도**: O(N · L) — posting list + term dictionary

**특징**:
- 두 구성: term dictionary (정렬·해시) + posting list (문서 ID 리스트)
- posting 에 추가 정보 저장: term frequency, position, payload
- 압축 기법: Variable Byte Encoding, FOR (Frame of Reference), PFOR, Roaring Bitmap
- segment 기반 (Lucene): 불변 segment + merge 정책으로 쓰기 효율

**장점**:
- 키워드 검색 O(1) lookup
- 다수 term 교집합 빠름 (skip list / Roaring Bitmap)
- 압축률 우수 (delta encoding)

**단점**:
- 부정 쿼리 (`NOT term`) 비효율 — 전체 스캔 가능성
- 색인 갱신 비용 (Lucene 은 segment merge 로 비동기 처리)
- 동의어·오타 미지원 (별도 처리 필요)

**활용 예시**:
- Elasticsearch / OpenSearch / Solr
- DB full-text index (PostgreSQL `GIN`, MySQL `FULLTEXT`)
- 코드 검색 (Sourcegraph, GitHub search)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드** (간이 구현):
```kotlin
// 간이 inverted index — term → set of document IDs
class InvertedIndex {
    // term → posting list (docId, term frequency, positions)
    private val index = mutableMapOf<String, MutableMap<Int, Posting>>()

    data class Posting(
        val docId: Int,
        var tf: Int = 0,
        val positions: MutableList<Int> = mutableListOf(),
    )

    /** 문서 색인. 토큰화 + 정규화 (소문자) 후 posting 추가 */
    fun addDocument(docId: Int, content: String) {
        val tokens = tokenize(content)
        tokens.forEachIndexed { pos, term ->
            val postings = index.getOrPut(term) { mutableMapOf() }
            val posting = postings.getOrPut(docId) { Posting(docId) }
            posting.tf++
            posting.positions.add(pos)
        }
    }

    /** AND 쿼리: 모든 term 을 포함하는 문서. posting list 교집합 */
    fun searchAnd(query: String): Set<Int> {
        val terms = tokenize(query)
        if (terms.isEmpty()) return emptySet()

        // 짧은 posting list 부터 교집합 (선택성 최적화)
        val postingLists = terms.mapNotNull { index[it]?.keys }
            .sortedBy { it.size }
        if (postingLists.size < terms.size) return emptySet()

        return postingLists.reduce { acc, set -> acc.intersect(set) }
    }

    /** OR 쿼리: term 중 하나라도 포함하는 문서 */
    fun searchOr(query: String): Set<Int> =
        tokenize(query)
            .mapNotNull { index[it]?.keys }
            .flatten()
            .toSet()

    /** Phrase 쿼리: positions 활용. "machine learning" → 연속 위치 확인 */
    fun searchPhrase(phrase: String): Set<Int> {
        val terms = tokenize(phrase)
        if (terms.size < 2) return searchAnd(phrase)

        val firstPostings = index[terms[0]] ?: return emptySet()
        return firstPostings.keys.filter { docId ->
            // term[0].positions, term[1].positions+1, ... 이 공통 위치를 갖는가
            val firstPositions = firstPostings[docId]!!.positions
            firstPositions.any { startPos ->
                terms.drop(1).withIndex().all { (i, term) ->
                    index[term]?.get(docId)?.positions?.contains(startPos + i + 1) == true
                }
            }
        }.toSet()
    }

    private fun tokenize(text: String): List<String> =
        text.lowercase().split(Regex("\\W+")).filter { it.isNotEmpty() }
}
```

**관련 알고리즘**:
- [tf-idf](#tf-idf) — posting 의 `tf` 활용
- [bm25](#bm25) — Lucene/Elasticsearch 의 기본 scorer
- [string.md#trie](string.md#trie) — term dictionary 구현 가능
- [string.md#aho-corasick](string.md#aho-corasick) — 다중 패턴 매칭 (인덱스 없는 grep 류)

---

<a id="tf-idf"></a>
## 2. TF-IDF (Term Frequency · Inverse Document Frequency)

**목적**: term 이 문서에서 얼마나 중요한가를 정량화. 자주 등장하지만 (TF) 다른 문서엔 드물게 등장 (IDF) 하는 term 일수록 높은 가중치.

**수식**:
```
TF(t, d) = count(t in d) / |d|            (정규화 TF)
또는 TF(t, d) = 1 + log(count(t in d))    (log-normalized)

IDF(t, D) = log(N / df(t))
  N: 전체 문서 수
  df(t): term t 를 포함한 문서 수

TF-IDF(t, d, D) = TF(t, d) · IDF(t, D)
```

**시간 복잡도**: O(|q|) per document — posting list 순회

**공간 복잡도**: O(V) — V: vocabulary 크기 (df 저장)

**특징**:
- 1972년 Karen Spärck Jones 의 IDF 개념 (term specificity)
- BM25 의 *조상* — TF 가 무한히 커지지 않게 saturation 한 게 BM25
- vector space model: 문서를 |V| 차원 TF-IDF 벡터로 보고 cosine similarity 계산

**장점**:
- 직관적, 구현 간단
- 라이브러리 없이도 가능
- vector space 변환으로 cosine similarity, clustering 응용

**단점**:
- TF 가 선형 증가 — 같은 term 100번 등장이 10번의 10배 중요하지 않음 (BM25 가 해결)
- 문서 길이 보정 부족 (긴 문서일수록 TF 부풀려짐)
- semantic 미반영 (동의어, 다의어 처리 불가)
- modern Lucene/Elasticsearch 의 default 가 아님 (5.0+ BM25 default)

**활용 예시**:
- scikit-learn `TfidfVectorizer` (텍스트 분류 feature)
- 키워드 추출 (top-k TF-IDF term)
- 단순 검색 시스템, 학습용 baseline

**난이도**: 낮음 | **사용 빈도**: ★★★★

**Kotlin 코드**:
```kotlin
import kotlin.math.ln
import kotlin.math.sqrt

class TfIdfScorer(private val documents: List<List<String>>) {
    private val N = documents.size
    // df[term] = term 포함 문서 수
    private val df: Map<String, Int> = documents
        .flatMap { it.toSet() }
        .groupingBy { it }
        .eachCount()

    /** IDF = log(N / df(t)). df=0 일 때 0 반환 */
    fun idf(term: String): Double {
        val docFreq = df[term] ?: return 0.0
        return ln(N.toDouble() / docFreq)
    }

    /** TF = count(t,d) / |d| — 정규화 형식 */
    fun tf(term: String, doc: List<String>): Double {
        if (doc.isEmpty()) return 0.0
        return doc.count { it == term }.toDouble() / doc.size
    }

    /** 한 문서에 대한 query 점수 = sum_{t in q} TF(t,d) · IDF(t) */
    fun score(query: List<String>, docIndex: Int): Double {
        val doc = documents[docIndex]
        return query.sumOf { term -> tf(term, doc) * idf(term) }
    }

    /** 전체 문서를 점수 순으로 정렬 */
    fun search(query: List<String>, topK: Int = 10): List<Pair<Int, Double>> =
        documents.indices
            .map { it to score(query, it) }
            .sortedByDescending { it.second }
            .take(topK)

    /** Cosine similarity 용 TF-IDF 벡터 (vector space model) */
    fun vector(doc: List<String>): Map<String, Double> =
        doc.toSet().associateWith { term -> tf(term, doc) * idf(term) }

    fun cosineSimilarity(v1: Map<String, Double>, v2: Map<String, Double>): Double {
        val dot = v1.keys.intersect(v2.keys).sumOf { v1[it]!! * v2[it]!! }
        val norm1 = sqrt(v1.values.sumOf { it * it })
        val norm2 = sqrt(v2.values.sumOf { it * it })
        if (norm1 == 0.0 || norm2 == 0.0) return 0.0
        return dot / (norm1 * norm2)
    }
}
```

**관련 알고리즘**:
- [bm25](#bm25) — TF-IDF 의 직계 후손, production standard
- [inverted-index](#inverted-index) — TF 와 df 저장
- [ml.md#k-means](ml.md#k-means) — TF-IDF 벡터로 문서 군집화

---

<a id="bm25"></a>
## 3. BM25 (Okapi BM25)

**목적**: 1994년 Stephen Robertson 이 Okapi 검색 시스템에서 제안한 확률적 랭킹 함수. **Elasticsearch 5.0 이상의 default scorer**, Lucene 6.0+ default. TF-IDF 의 두 약점 (TF 무한 증가, 문서 길이 보정 부족) 해결.

**수식** (가장 일반적인 BM25 형태):
```
                         f(t, d) · (k1 + 1)
score(d, q) = Σ IDF(t) · ──────────────────────────────────
              t in q     f(t, d) + k1 · (1 - b + b · |d|/avgdl)

여기서:
  f(t, d)  : 문서 d 에서 term t 의 빈도 (TF)
  |d|      : 문서 d 의 길이 (term 수)
  avgdl    : 컬렉션 전체 문서의 평균 길이
  k1       : TF saturation 파라미터 (기본 1.2, 일반 [1.2, 2.0])
  b        : length normalization 파라미터 (기본 0.75, [0, 1])

IDF(t) = ln((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
  Lucene 의 BM25Similarity 정확 공식 (음수 방지를 위해 +1)
```

**파라미터 의미**:
- **k1**: TF saturation. 크면 TF 영향력 ↑, 0 이면 binary (등장 여부만). 일반 1.2 (Lucene default)
- **b**: 문서 길이 보정. 1 이면 완전 길이 정규화, 0 이면 길이 무시. 일반 0.75
- **avgdl**: 컬렉션 평균 길이 — `|d|/avgdl` 로 짧은 문서를 부풀려 긴 문서와 공정 비교

**시간 복잡도**: O(|q| · |posting|) — TF-IDF 와 동일

**공간 복잡도**: O(V) — IDF 사전, avgdl 캐시

**특징**:
- *Best Matching 25* — Okapi 시스템 25번째 실험 공식
- TF saturation: `f → ∞` 에서도 `score` 가 `IDF · (k1+1)` 로 수렴 → 키워드 스팸 방어
- 문서 길이 정규화: 긴 문서일수록 분모 ↑ → 점수 ↓ (공정성)
- variants: BM25F (multi-field, title 가중치), BM25+ (lower bound 추가)

**장점**:
- production-grade — Elasticsearch / OpenSearch / Lucene / Solr default
- TF-IDF 대비 ranking quality 우수 (TREC 평가)
- 파라미터 2개만 튜닝 (k1, b)
- field-level 가중치 (BM25F): title 3x, body 1x

**단점**:
- semantic 미반영 (동의어, 문맥 — Vector Search 보완)
- 짧은 query/문서에선 TF 신호 약함
- 도메인별 k1/b 튜닝 필요 (e-commerce vs 학술 문서 다름)
- OOV (Out-Of-Vocabulary) 에 약함 (subword tokenization 부족)

**활용 예시**:
- Elasticsearch / OpenSearch / Solr / Vespa default ranker
- e-commerce 상품 검색 (BM25F 로 title 가중)
- 학술 검색, 문서 검색 baseline
- RAG (Retrieval-Augmented Generation) 의 sparse retriever

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드** (Lucene BM25Similarity 호환 구현):
```kotlin
import kotlin.math.ln

class BM25Scorer(
    private val documents: List<List<String>>,
    private val k1: Double = 1.2,
    private val b: Double = 0.75,
) {
    private val N = documents.size
    private val avgdl: Double = documents.sumOf { it.size.toDouble() } / N
    private val df: Map<String, Int> = documents
        .flatMap { it.toSet() }
        .groupingBy { it }
        .eachCount()

    /** Lucene BM25Similarity IDF: ln((N - df + 0.5) / (df + 0.5) + 1) */
    fun idf(term: String): Double {
        val docFreq = (df[term] ?: 0).toDouble()
        return ln((N - docFreq + 0.5) / (docFreq + 0.5) + 1.0)
    }

    /** 단일 term 점수: IDF · (f·(k1+1)) / (f + k1·(1-b + b·|d|/avgdl)) */
    fun scoreTerm(term: String, doc: List<String>): Double {
        val f = doc.count { it == term }.toDouble()
        if (f == 0.0) return 0.0
        val docLen = doc.size.toDouble()
        val numerator = f * (k1 + 1.0)
        val denominator = f + k1 * (1.0 - b + b * docLen / avgdl)
        return idf(term) * numerator / denominator
    }

    /** 문서 점수 = sum over query terms */
    fun score(query: List<String>, docIndex: Int): Double {
        val doc = documents[docIndex]
        return query.sumOf { scoreTerm(it, doc) }
    }

    /** Top-K 검색 */
    fun search(query: List<String>, topK: Int = 10): List<Pair<Int, Double>> =
        documents.indices
            .map { it to score(query, it) }
            .filter { it.second > 0.0 }
            .sortedByDescending { it.second }
            .take(topK)
}

// BM25F: 다중 필드 + 필드별 boost
class BM25FScorer(
    private val documents: List<Map<String, List<String>>>,  // field → tokens
    private val fieldBoosts: Map<String, Double>,             // title=3.0, body=1.0
    private val k1: Double = 1.2,
    private val b: Double = 0.75,
) {
    private val N = documents.size
    private val avgdlPerField: Map<String, Double>
    private val df: Map<String, Int>

    init {
        val allFields = documents.flatMap { it.keys }.toSet()
        avgdlPerField = allFields.associateWith { field ->
            documents.sumOf { (it[field]?.size ?: 0).toDouble() } / N
        }
        // df: 어떤 필드든 term 을 포함하는 문서 수
        df = documents
            .flatMap { doc -> doc.values.flatMap { it.toSet() } }
            .groupingBy { it }
            .eachCount()
    }

    fun idf(term: String): Double {
        val docFreq = (df[term] ?: 0).toDouble()
        return ln((N - docFreq + 0.5) / (docFreq + 0.5) + 1.0)
    }

    fun score(query: List<String>, docIndex: Int): Double {
        val doc = documents[docIndex]
        return query.sumOf { term ->
            // 필드별 weighted TF 합산
            val weightedTf = doc.entries.sumOf { (field, tokens) ->
                val boost = fieldBoosts[field] ?: 1.0
                val f = tokens.count { it == term }.toDouble()
                val avgdl = avgdlPerField[field] ?: 1.0
                val norm = 1.0 - b + b * tokens.size / avgdl
                boost * f / norm
            }
            if (weightedTf == 0.0) 0.0
            else idf(term) * weightedTf * (k1 + 1.0) / (weightedTf + k1)
        }
    }
}
```

**Elasticsearch Query DSL**:
```json
GET /products/_search
{
  "query": {
    "multi_match": {
      "query": "wireless headphones",
      "fields": ["title^3", "description^1", "brand^2"],
      "type": "best_fields"
    }
  }
}

# k1, b 튜닝 (similarity 설정)
PUT /products
{
  "settings": {
    "similarity": {
      "custom_bm25": {
        "type": "BM25",
        "k1": 1.5,
        "b": 0.6
      }
    }
  },
  "mappings": {
    "properties": {
      "title": { "type": "text", "similarity": "custom_bm25" }
    }
  }
}
```

**관련 알고리즘**:
- [tf-idf](#tf-idf) — 직계 조상
- [inverted-index](#inverted-index) — posting list 위에서 동작
- [hybrid-search](#hybrid-search) — vector 와 결합
- [learning-to-rank](#learning-to-rank) — BM25 점수를 LTR feature 로 사용

---

<a id="vector-search"></a>
## 4. Vector Search (Dense Retrieval)

**목적**: 문서·쿼리를 고정 차원 dense vector (embedding) 로 인코딩 후 vector similarity (cosine, dot-product, Euclidean) 로 검색. semantic 의미 캡처. ANN (Approximate Nearest Neighbor) 인덱스로 대규모 컬렉션 처리.

**시간 복잡도**:
- 정확 NN: O(N · d) per query — N: 벡터 수, d: 차원
- HNSW ANN: O(log N · d) per query
- IVF (Inverted File): O((N/nlist + nprobe·N/nlist) · d)

**공간 복잡도**: O(N · d) — 압축 (Product Quantization) 으로 1/8~1/64

**특징**:
- 임베딩 모델: SBERT (Sentence-BERT), OpenAI text-embedding-3, Cohere embed-v3, BGE, E5
- distance metrics:
  - cosine: 정규화 후 dot-product 와 동치
  - dot-product: 모델이 normalize 안 했을 때
  - L2 (Euclidean): geometry 기반
- ANN 인덱스: HNSW (Hierarchical Navigable Small World), IVF, IVF-PQ, ScaNN
- 대표 라이브러리: FAISS (Meta), hnswlib, Annoy (Spotify), ScaNN (Google), Qdrant, Weaviate, Milvus, pgvector

**장점**:
- semantic 검색 ("car" 쿼리에 "automobile" 문서 매칭)
- 다국어 (multilingual embedding)
- 키워드 우회 (오타, 패러프레이즈)
- RAG, 추천, multi-modal (이미지/텍스트 cross)

**단점**:
- 정확한 키워드 매칭 약함 (제품 코드, 사람 이름 등)
- embedding 모델 의존성 — 모델 변경 시 전체 재색인
- 차원의 저주 (high-d 에서 거리 균질화)
- 색인 메모리 큼 (HNSW 는 OOM 위험)
- 학습 데이터 분포 밖 OOD (Out-of-Distribution) 약함

**활용 예시**:
- RAG (Retrieval-Augmented Generation) — LLM 의 context 검색
- 이미지·비디오 검색 (CLIP embedding)
- 추천 시스템 (user/item embedding)
- 중복 탐지, 표절 검출

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 코드** (정확 NN + cosine):
```kotlin
import kotlin.math.sqrt

class VectorIndex(private val dim: Int) {
    private val vectors = mutableListOf<FloatArray>()
    private val ids = mutableListOf<String>()
    private val norms = mutableListOf<Float>()

    /** 벡터 추가. norm 사전 계산해 cosine 가속 */
    fun add(id: String, vector: FloatArray) {
        require(vector.size == dim) { "dim mismatch: expected $dim, got ${vector.size}" }
        vectors.add(vector)
        ids.add(id)
        norms.add(l2Norm(vector))
    }

    /** Cosine similarity = (a · b) / (||a|| · ||b||) */
    fun cosineSearch(query: FloatArray, topK: Int = 10): List<Pair<String, Float>> {
        require(query.size == dim)
        val queryNorm = l2Norm(query)
        if (queryNorm == 0f) return emptyList()

        return vectors.indices
            .map { i ->
                val dot = dotProduct(query, vectors[i])
                val cosine = dot / (queryNorm * norms[i])
                ids[i] to cosine
            }
            .sortedByDescending { it.second }
            .take(topK)
    }

    /** Dot-product search (벡터가 이미 정규화됐다면 cosine 과 동치) */
    fun dotSearch(query: FloatArray, topK: Int = 10): List<Pair<String, Float>> =
        vectors.indices
            .map { i -> ids[i] to dotProduct(query, vectors[i]) }
            .sortedByDescending { it.second }
            .take(topK)

    /** L2 (Euclidean) — 거리이므로 작을수록 가까움 */
    fun l2Search(query: FloatArray, topK: Int = 10): List<Pair<String, Float>> =
        vectors.indices
            .map { i -> ids[i] to l2Distance(query, vectors[i]) }
            .sortedBy { it.second }
            .take(topK)

    private fun dotProduct(a: FloatArray, b: FloatArray): Float {
        var sum = 0f
        for (i in a.indices) sum += a[i] * b[i]
        return sum
    }

    private fun l2Norm(v: FloatArray): Float {
        var sum = 0f
        for (x in v) sum += x * x
        return sqrt(sum.toDouble()).toFloat()
    }

    private fun l2Distance(a: FloatArray, b: FloatArray): Float {
        var sum = 0f
        for (i in a.indices) {
            val d = a[i] - b[i]
            sum += d * d
        }
        return sqrt(sum.toDouble()).toFloat()
    }
}

// 실 사용: pgvector / Qdrant / Weaviate / FAISS 권장
// HNSW 구현은 ml.md#hnsw 참고
```

**Elasticsearch Vector Query** (dense_vector + kNN):
```json
# 매핑
PUT /products
{
  "mappings": {
    "properties": {
      "embedding": {
        "type": "dense_vector",
        "dims": 768,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}

# kNN 검색 (HNSW 기반)
GET /products/_search
{
  "knn": {
    "field": "embedding",
    "query_vector": [0.12, -0.45, ...],
    "k": 10,
    "num_candidates": 100
  }
}
```

**관련 알고리즘**:
- [ml.md#hnsw](ml.md#hnsw) — ANN 인덱스 핵심
- [ml.md#transformer](ml.md#transformer) — embedding 모델
- [ml.md#quantization](ml.md#quantization) — Product Quantization 으로 메모리 절감
- [hybrid-search](#hybrid-search) — BM25 와 결합

---

<a id="hybrid-search"></a>
## 5. Hybrid Search (BM25 + Vector Fusion)

**목적**: keyword (sparse, BM25) 와 semantic (dense, vector) 결과를 결합. 두 방식의 약점 상호 보완. production RAG 의 표준.

**수식 — RRF (Reciprocal Rank Fusion)**:
```
RRF_score(d) = Σ  1 / (k + rank_i(d))
              i ∈ {bm25, vector}

  rank_i(d) : 시스템 i 의 결과에서 문서 d 의 순위 (1부터 시작)
  k         : 상수 (Cormack 2009 권장 60)
  d ∉ top-N : rank 가 무한 → 항 제외 또는 0
```

**수식 — Weighted Linear Combination**:
```
score(d) = α · score_bm25(d) + (1 - α) · score_vector(d)

  α : [0, 1] 가중치
  점수 정규화 (min-max 또는 z-score) 필수 — BM25 와 cosine 의 스케일 다름
```

**시간 복잡도**: O(BM25 query + Vector ANN query + fusion)

**공간 복잡도**: 두 인덱스 합

**특징**:
- **RRF**: 점수 정규화 불필요 — rank 만 사용. 도메인 무관, 튜닝 거의 없음
- **Weighted**: α 튜닝 필요 (검증 셋으로 α=0.3~0.7 그리드 서치)
- **Cascade**: 1단계 BM25 로 후보 1000 추출 → 2단계 vector 로 재랭킹
- Elasticsearch 8.8+ RRF 네이티브 지원, OpenSearch hybrid query pipeline

**장점**:
- 키워드 정확도 + semantic 보강
- RRF 는 점수 스케일 무관 (production-friendly)
- 약한 쿼리 (오타·짧은 쿼리·OOV) 에 강함
- 다국어, multi-modal 확장

**단점**:
- 두 시스템 운영 비용 (BM25 인덱스 + Vector 인덱스 + embedding 추론)
- latency ↑ (병렬 호출로 일부 완화)
- α 튜닝 (Weighted 방식) — domain shift 시 재튜닝
- RRF 는 점수 절댓값 의미 소실 → threshold 기반 cutoff 어려움

**활용 예시**:
- RAG 시스템 (LangChain `EnsembleRetriever`, LlamaIndex `QueryFusionRetriever`)
- e-commerce 검색 (상품 코드 + 의미 검색)
- Enterprise search (Glean, Notion AI)
- 코드 검색 (Sourcegraph Cody)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드** (RRF + Weighted):
```kotlin
/** RRF (Reciprocal Rank Fusion) — Cormack et al. 2009 */
fun reciprocalRankFusion(
    rankedLists: List<List<String>>,  // 각 시스템의 top-K 결과 (docId)
    k: Int = 60,
    topK: Int = 10,
): List<Pair<String, Double>> {
    val scores = mutableMapOf<String, Double>()
    for (list in rankedLists) {
        list.forEachIndexed { rank, docId ->
            // rank 는 1-based: rank=0 → 1
            scores[docId] = (scores[docId] ?: 0.0) + 1.0 / (k + rank + 1.0)
        }
    }
    return scores.entries
        .sortedByDescending { it.value }
        .take(topK)
        .map { it.key to it.value }
}

/** Weighted linear combination — min-max 정규화 후 가중 합 */
fun weightedFusion(
    bm25Results: List<Pair<String, Double>>,  // (docId, BM25 score)
    vectorResults: List<Pair<String, Double>>, // (docId, cosine score)
    alpha: Double = 0.5,                       // BM25 가중치
    topK: Int = 10,
): List<Pair<String, Double>> {
    val bm25Norm = minMaxNormalize(bm25Results)
    val vectorNorm = minMaxNormalize(vectorResults)

    val allDocs = (bm25Norm.keys + vectorNorm.keys)
    return allDocs
        .map { docId ->
            val s = alpha * (bm25Norm[docId] ?: 0.0) +
                    (1 - alpha) * (vectorNorm[docId] ?: 0.0)
            docId to s
        }
        .sortedByDescending { it.second }
        .take(topK)
}

private fun minMaxNormalize(scores: List<Pair<String, Double>>): Map<String, Double> {
    if (scores.isEmpty()) return emptyMap()
    val values = scores.map { it.second }
    val min = values.min()
    val max = values.max()
    val range = max - min
    if (range == 0.0) return scores.associate { it.first to 1.0 }
    return scores.associate { (id, s) -> id to (s - min) / range }
}

/** Cascade — BM25 로 후보 N 추출 → Vector 로 재랭킹 */
class CascadeRetriever(
    private val bm25: BM25Scorer,
    private val vectorIndex: VectorIndex,
    private val embed: (String) -> FloatArray,
) {
    fun search(query: String, candidateN: Int = 100, finalK: Int = 10): List<String> {
        // 1단계: BM25 후보 추출
        val candidates = bm25.search(query.split(" "), topK = candidateN)
            .map { it.first.toString() }

        // 2단계: 후보에 대해서만 vector 재랭킹
        val queryVec = embed(query)
        return vectorIndex.cosineSearch(queryVec, topK = finalK)
            .filter { (id, _) -> id in candidates }
            .take(finalK)
            .map { it.first }
    }
}
```

**Elasticsearch RRF Query** (8.8+):
```json
GET /products/_search
{
  "retriever": {
    "rrf": {
      "retrievers": [
        {
          "standard": {
            "query": {
              "multi_match": {
                "query": "wireless headphones",
                "fields": ["title^3", "description"]
              }
            }
          }
        },
        {
          "knn": {
            "field": "embedding",
            "query_vector_builder": {
              "text_embedding": {
                "model_id": "sentence-transformer"
              }
            },
            "k": 50,
            "num_candidates": 200
          }
        }
      ],
      "rank_window_size": 50,
      "rank_constant": 60
    }
  }
}
```

**관련 알고리즘**:
- [bm25](#bm25) — sparse 컴포넌트
- [vector-search](#vector-search) — dense 컴포넌트
- [learning-to-rank](#learning-to-rank) — fusion 대신 ML 로 점수 결합

---

<a id="faceted-search"></a>
## 6. Faceted Search / Aggregation

**목적**: 검색 결과를 카테고리·속성별로 집계해 사용자에게 drill-down 필터 제공. "노트북" 검색 → 브랜드·가격대·평점 facet 표시 → 사용자가 필터로 결과 좁히기. e-commerce 의 필수 UX.

**시간 복잡도**:
- bucket count: O(|matched docs| · |facet fields|)
- inverted index 활용 시 O(|posting list intersection|)

**공간 복잡도**: O(|matched docs|) — per bucket counter

**특징**:
- bucket aggregation: terms (카테고리), histogram (가격), range (별점), date_histogram (시간)
- metric aggregation: avg, min, max, sum, percentile, cardinality
- nested aggregation: facet 안에 sub-facet (브랜드 → 모델)
- post_filter: facet 자체는 전체 결과로 집계하고 결과 목록만 필터링 (multi-select facet UX)

**장점**:
- 발견 가능성 ↑ (사용자가 어떤 필터가 있는지 모를 때 도움)
- 결과 분포 한눈에 (가격대 분포로 시장 감각)
- 다중 조건 조합 (브랜드 + 가격대 + 평점)

**단점**:
- high-cardinality field (수십만 카테고리) 에서 메모리 압박
- 정확도 vs 성능 tradeoff (`shard_size` 튜닝, `terms` aggregation 의 approximate count)
- multi-select 시 query 가 복잡해짐 (post_filter + filtered aggregation)

**활용 예시**:
- e-commerce 상품 필터 (Amazon, Coupang, eBay)
- 호텔·항공 검색 필터
- 로그·메트릭 대시보드 (Kibana, Grafana)
- 학술 논문 검색 (저자, 연도, 학회 facet)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드** (간이 faceted search):
```kotlin
data class Product(
    val id: String,
    val title: String,
    val brand: String,
    val category: String,
    val price: Double,
    val rating: Double,
)

data class FacetResult(
    val terms: Map<String, Map<String, Int>>,  // field → (value → count)
    val ranges: Map<String, Map<String, Int>>, // field → (rangeLabel → count)
)

class FacetedSearch(private val products: List<Product>) {

    /** 검색 + facet 집계 */
    fun search(
        query: String,
        filters: Map<String, Set<String>> = emptyMap(),  // 적용된 필터
        facetFields: List<String> = listOf("brand", "category"),
        priceRanges: List<Pair<Double, Double>> = listOf(
            0.0 to 100.0, 100.0 to 500.0, 500.0 to 1000.0, 1000.0 to Double.MAX_VALUE,
        ),
    ): Pair<List<Product>, FacetResult> {
        // 1. 텍스트 매칭
        val matched = products.filter { p ->
            query.isBlank() || p.title.contains(query, ignoreCase = true)
        }

        // 2. 필터 적용 (사용자가 facet 클릭한 결과)
        val filtered = matched.filter { p ->
            filters.all { (field, values) ->
                when (field) {
                    "brand" -> p.brand in values
                    "category" -> p.category in values
                    else -> true
                }
            }
        }

        // 3. Facet 집계
        // 핵심 규칙: 같은 field 의 필터는 *제외* 하고 집계 (multi-select UX)
        // brand=Apple 선택 시 brand facet 은 Apple 외 다른 brand 도 보여줘야 함
        val termFacets = facetFields.associateWith { field ->
            val activeFiltersExceptThis = filters.filterKeys { it != field }
            matched
                .filter { p ->
                    activeFiltersExceptThis.all { (f, vs) ->
                        when (f) {
                            "brand" -> p.brand in vs
                            "category" -> p.category in vs
                            else -> true
                        }
                    }
                }
                .groupingBy { p ->
                    when (field) {
                        "brand" -> p.brand
                        "category" -> p.category
                        else -> ""
                    }
                }
                .eachCount()
        }

        // 4. Range facet (가격)
        val priceBuckets = priceRanges.associate { (lo, hi) ->
            val label = if (hi == Double.MAX_VALUE) "${lo.toInt()}+" else "${lo.toInt()}-${hi.toInt()}"
            label to filtered.count { it.price in lo..hi }
        }

        return filtered to FacetResult(
            terms = termFacets,
            ranges = mapOf("price" to priceBuckets),
        )
    }
}
```

**Elasticsearch Aggregation**:
```json
GET /products/_search
{
  "query": {
    "match": { "title": "wireless headphones" }
  },
  "aggs": {
    "by_brand": {
      "terms": { "field": "brand.keyword", "size": 20 }
    },
    "by_price_range": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 100 },
          { "from": 100, "to": 500 },
          { "from": 500, "to": 1000 },
          { "from": 1000 }
        ]
      }
    },
    "avg_rating": {
      "avg": { "field": "rating" }
    },
    "by_category_then_brand": {
      "terms": { "field": "category.keyword" },
      "aggs": {
        "brands": {
          "terms": { "field": "brand.keyword" }
        }
      }
    }
  },
  "post_filter": {
    "term": { "brand.keyword": "Sony" }
  }
}
```

**관련 알고리즘**:
- [inverted-index](#inverted-index) — bucket count 가 posting 기반
- [bm25](#bm25) — 매칭 점수와 facet 동시 반환
- [`../patterns/domains/ecommerce.md`](../patterns/domains/ecommerce.md) — UX 패턴

---

<a id="autocomplete"></a>
## 7. Autocomplete / Type-ahead

**목적**: 사용자가 타이핑하는 동안 prefix 기반으로 완성 제안. 검색 의도 빠른 발견, 오타 방지. latency 50ms 이하 필수.

**시간 복잡도**:
- Trie prefix lookup: O(|prefix|)
- FST 디코드: O(|prefix| · log V)
- Edge N-gram (Elasticsearch): O(1) inverted lookup

**공간 복잡도**:
- Trie: O(V · L) — V: 단어 수, L: 평균 길이
- FST (Finite State Transducer): O(V · L / k) — k: 공유 prefix·suffix 압축률 (Lucene 사용)

**특징**:
- 전략:
  - **Prefix Trie**: 단순, 메모리 큼
  - **FST (Finite State Transducer)**: Lucene `CompletionField` 가 사용. prefix·suffix 공유로 압축
  - **Edge N-gram**: 색인 시 prefix 변종 모두 토큰화 (`car` → `c`, `ca`, `car`) — Elasticsearch `edge_ngram` analyzer
  - **Search-as-you-type**: Elasticsearch `search_as_you_type` field type — n-gram + prefix 결합
- 랭킹: 인기도 (query log frequency), 개인화, BM25 결합
- fuzzy: edit distance 1~2 허용 (오타 보정)

**장점**:
- 빠른 UX (사용자 노력 감소)
- query log 기반 인기 쿼리 제안
- 카테고리·이미지 등 풍부한 결과

**단점**:
- 색인 크기 증가 (edge n-gram 은 토큰 수 N배)
- ranking 데이터 필요 (cold-start 어려움)
- multi-language tokenization 복잡 (CJK 는 character n-gram)

**활용 예시**:
- 검색창 자동완성 (Google, Naver, Coupang)
- 코드 IDE 자동완성 (Trie + LSP)
- 메신저 멘션·이모지 완성
- 주소 자동완성 (Geocoding)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드** (인기도 가중 Trie):
```kotlin
/** prefix 기반 자동완성. 인기도 (frequency) 로 랭킹 */
class AutocompleteTrie {
    private class Node {
        val children = mutableMapOf<Char, Node>()
        var isWord: Boolean = false
        var word: String? = null
        var weight: Int = 0  // 인기도 (query log frequency)
        // Top-K caching: 이 노드 서브트리의 상위 K개 (속도 최적화)
        var topK: List<Pair<String, Int>> = emptyList()
    }

    private val root = Node()
    private val topKSize = 10

    /** 단어 추가 + 인기도 갱신 */
    fun add(word: String, weight: Int = 1) {
        var node = root
        for (c in word) {
            node = node.children.getOrPut(c) { Node() }
        }
        node.isWord = true
        node.word = word
        node.weight = maxOf(node.weight, weight)
    }

    /** Top-K 사전 계산 (모든 단어 add 후 호출). Suffix 서브트리의 상위 K 캐싱 */
    fun build() {
        buildTopK(root)
    }

    private fun buildTopK(node: Node): List<Pair<String, Int>> {
        val collected = mutableListOf<Pair<String, Int>>()
        if (node.isWord) collected.add(node.word!! to node.weight)
        for ((_, child) in node.children) {
            collected.addAll(buildTopK(child))
        }
        node.topK = collected.sortedByDescending { it.second }.take(topKSize)
        return node.topK
    }

    /** prefix 자동완성 — top-K 캐시로 즉시 반환 */
    fun suggest(prefix: String, k: Int = 10): List<String> {
        var node = root
        for (c in prefix) {
            node = node.children[c] ?: return emptyList()
        }
        return node.topK.take(k).map { it.first }
    }

    /** Fuzzy: edit distance 1 까지 허용 (오타 보정) */
    fun suggestFuzzy(prefix: String, k: Int = 10): List<String> {
        val candidates = mutableSetOf<Pair<String, Int>>()
        fun dfs(node: Node, depth: Int, edits: Int, path: StringBuilder) {
            if (depth == prefix.length) {
                candidates.addAll(node.topK)
                return
            }
            val c = prefix[depth]
            // 정확 매칭
            node.children[c]?.let {
                path.append(c); dfs(it, depth + 1, edits, path); path.deleteCharAt(path.length - 1)
            }
            // edit 1 허용 (substitution)
            if (edits < 1) {
                for ((ch, child) in node.children) {
                    if (ch == c) continue
                    path.append(ch)
                    dfs(child, depth + 1, edits + 1, path)
                    path.deleteCharAt(path.length - 1)
                }
            }
        }
        dfs(root, 0, 0, StringBuilder())
        return candidates.sortedByDescending { it.second }.take(k).map { it.first }
    }
}

// 사용
fun main() {
    val ac = AutocompleteTrie()
    ac.add("apple", 100)
    ac.add("application", 80)
    ac.add("apply", 50)
    ac.add("apricot", 30)
    ac.build()
    println(ac.suggest("app"))   // [apple, application, apply]
    println(ac.suggest("apr"))   // [apricot]
}
```

**Elasticsearch Autocomplete**:
```json
# Edge N-gram analyzer
PUT /products
{
  "settings": {
    "analysis": {
      "analyzer": {
        "autocomplete": {
          "tokenizer": "autocomplete_tokenizer",
          "filter": ["lowercase"]
        }
      },
      "tokenizer": {
        "autocomplete_tokenizer": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 20,
          "token_chars": ["letter", "digit"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "autocomplete",
        "search_analyzer": "standard"
      }
    }
  }
}

# Completion Suggester (FST 기반, 가장 빠름)
PUT /products
{
  "mappings": {
    "properties": {
      "suggest": {
        "type": "completion",
        "analyzer": "simple",
        "preserve_separators": true,
        "preserve_position_increments": true,
        "max_input_length": 50
      }
    }
  }
}

POST /products/_search
{
  "suggest": {
    "product-suggest": {
      "prefix": "wir",
      "completion": {
        "field": "suggest",
        "size": 10,
        "fuzzy": { "fuzziness": 1 }
      }
    }
  }
}
```

**관련 알고리즘**:
- [string.md#trie](string.md#trie) — prefix 검색 자료구조
- [inverted-index](#inverted-index) — edge n-gram 도 결국 inverted index
- [bm25](#bm25) — 인기도 외에 BM25 결합한 랭킹

---

<a id="learning-to-rank"></a>
## 8. Learning to Rank (LTR)

**목적**: 사람이 만든 ranking 공식 (BM25 등) 대신 **사용자 행동 데이터 + 머신러닝**으로 ranking 최적화. 클릭, 구매, 체류시간 등 신호로 학습. Pointwise / Pairwise / Listwise 3 패러다임.

**3 패러다임**:

```
Pointwise:   각 (query, doc) 쌍의 절대 점수 학습 (회귀)
              loss = (predicted - actual)^2
              단점: 같은 query 내 상대 순서 정보 손실

Pairwise:    같은 query 의 두 문서 (d_i, d_j) 비교 학습
              loss = -log σ(s_i - s_j)   if d_i > d_j
              대표: RankNet (Burges 2005), LambdaRank, LambdaMART
              현재 가장 널리 사용

Listwise:    전체 ranking list 의 metric (NDCG, MAP) 최적화
              ListNet, ListMLE
              loss 가 NDCG 와 직접 연관 → 이론적 우수
```

**핵심 metric — NDCG (Normalized Discounted Cumulative Gain)**:
```
DCG@k  = Σ  (2^rel_i - 1) / log2(i + 1)
        i=1..k

IDCG@k = DCG@k (ideal ordering)
NDCG@k = DCG@k / IDCG@k         ∈ [0, 1]

  rel_i : 위치 i 문서의 relevance label (0=irrelevant, 1=관련, 2=매우 관련, ...)
  log2 분모로 상위 순위 가중치 ↑
```

**시간 복잡도**:
- 학습: O(N·F·T) — N: 학습 샘플, F: feature 수, T: tree 수 (LambdaMART 가정)
- 추론: O(F + T·logL) — L: tree leaf 수 (트리당 O(logL))

**공간 복잡도**: 모델 크기 O(T · L)

**특징**:
- features:
  - **Query-Doc**: BM25, TF-IDF, vector similarity, term overlap
  - **Doc**: 상품 인기도, 평점, 가격, 신선도, CTR
  - **Query**: query length, type (navigational/informational), 언어
  - **Context**: 사용자 location, device, time
- 대표 모델:
  - **LambdaMART**: gradient boosted trees + pairwise (XGBoost `rank:pairwise`, LightGBM `lambdarank`)
  - **RankNet**: 신경망 + pairwise
  - **TF-Ranking**: TensorFlow listwise
- 학습 데이터: editorial label (사람이 5단 등급), implicit feedback (클릭/구매/체류)

**장점**:
- BM25/handcraft 보다 ranking 품질 ↑ (NDCG 5~30% 개선)
- 다양한 feature 결합 (가격, 평점, 개인화)
- A/B 테스트로 지속 개선
- production 검색 표준 (Amazon, Yelp, Yahoo, Bing)

**단점**:
- 학습 데이터 비용 (label 작업 또는 implicit 로그 파이프라인)
- feature engineering 노력
- offline NDCG 와 online CTR/conversion 의 간극 (selection bias)
- exploration vs exploitation 트레이드오프
- 모델 추론 latency (re-ranking 단계 한정)

**활용 예시**:
- e-commerce 상품 정렬 (Amazon A9, Coupang, Naver Shopping)
- 광고 랭킹 (구글 Ads QualityScore)
- 추천 시스템 (YouTube, Netflix re-ranking)
- 학술 검색 (Microsoft Academic, Google Scholar)
- Elasticsearch LTR plugin (OpenSearch `ltr` plugin)

**난이도**: 높음 | **사용 빈도**: ★★★★

**Kotlin 코드** (NDCG 평가 + 간이 pairwise 학습):
```kotlin
import kotlin.math.ln
import kotlin.math.pow
import kotlin.math.exp

/** NDCG@k — LTR 의 표준 평가 metric */
fun ndcg(relevances: List<Int>, k: Int): Double {
    fun dcg(rels: List<Int>): Double = rels
        .take(k)
        .withIndex()
        .sumOf { (i, rel) -> (2.0.pow(rel) - 1.0) / ln((i + 2).toDouble()) * ln(2.0) }
        // ln(i+2)/ln(2) = log2(i+2). i=0 위치 → log2(2)=1

    val dcg = dcg(relevances)
    val idcg = dcg(relevances.sortedDescending())
    return if (idcg == 0.0) 0.0 else dcg / idcg
}

/** Pairwise 학습용 데이터 구조 */
data class TrainingExample(
    val queryId: String,
    val docId: String,
    val features: DoubleArray,
    val relevance: Int,  // 0~4 등급
)

/** 간이 linear pairwise 모델 (RankNet 단순화)
 *  실 production 은 XGBoost (rank:pairwise), LightGBM (lambdarank) 사용 */
class LinearPairwiseRanker(numFeatures: Int) {
    private val weights = DoubleArray(numFeatures)

    fun predict(features: DoubleArray): Double =
        features.indices.sumOf { weights[it] * features[it] }

    /** pairwise gradient descent
     *  loss = -log σ(s_i - s_j)   if rel_i > rel_j
     *  gradient w.r.t. w_k = -σ(s_j - s_i) · (x_i_k - x_j_k) */
    fun train(
        examples: List<TrainingExample>,
        learningRate: Double = 0.01,
        epochs: Int = 100,
    ) {
        // query 별로 그룹화
        val byQuery = examples.groupBy { it.queryId }
        for (epoch in 0 until epochs) {
            for ((_, docs) in byQuery) {
                // 같은 query 내 모든 (i, j) 쌍 중 rel 차이 있는 쌍만 학습
                for (i in docs.indices) {
                    for (j in docs.indices) {
                        if (docs[i].relevance <= docs[j].relevance) continue
                        val si = predict(docs[i].features)
                        val sj = predict(docs[j].features)
                        // σ(s_j - s_i) — i 가 더 적합한데 j 점수가 높을수록 큼
                        val sigmoid = 1.0 / (1.0 + exp(si - sj))
                        for (k in weights.indices) {
                            val grad = -sigmoid * (docs[i].features[k] - docs[j].features[k])
                            weights[k] -= learningRate * grad
                        }
                    }
                }
            }
        }
    }
}

// 사용 — feature: [BM25, vector_sim, price_norm, rating, ctr]
fun main() {
    val examples = listOf(
        TrainingExample("q1", "d1", doubleArrayOf(0.8, 0.7, 0.5, 4.5, 0.12), relevance = 3),
        TrainingExample("q1", "d2", doubleArrayOf(0.6, 0.5, 0.4, 4.0, 0.08), relevance = 2),
        TrainingExample("q1", "d3", doubleArrayOf(0.3, 0.4, 0.3, 3.0, 0.02), relevance = 0),
        // ... 수천~수만 샘플
    )
    val model = LinearPairwiseRanker(numFeatures = 5)
    model.train(examples)

    // 추론 시: 1단계 BM25 로 후보 100 → 2단계 LTR 로 재랭킹
    val rels = listOf(3, 2, 0, 1)  // 모델이 정렬한 순서의 실제 rel
    println("NDCG@4 = ${ndcg(rels, 4)}")
}
```

**Elasticsearch LTR Plugin Query**:
```json
GET /products/_search
{
  "query": {
    "function_score": {
      "query": { "match": { "title": "wireless headphones" } },
      "rescore": {
        "window_size": 100,
        "query": {
          "rescore_query": {
            "sltr": {
              "params": { "keywords": "wireless headphones" },
              "model": "my_ltr_model"
            }
          }
        }
      }
    }
  }
}
```

**관련 알고리즘**:
- [bm25](#bm25) — LTR 의 가장 강한 feature
- [vector-search](#vector-search) — semantic similarity feature
- [hybrid-search](#hybrid-search) — LTR 은 fusion 의 ML 일반화
- [ml.md#gradient-descent](ml.md#gradient-descent) — pairwise 학습 핵심
- [`../patterns/domains/ecommerce.md`](../patterns/domains/ecommerce.md) — 응용 사례
