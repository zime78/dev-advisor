# 공간 인덱싱 알고리즘 (Spatial Indexing Algorithms)

2D/3D 공간·지리 데이터 인덱싱 정평 있는 8 알고리즘. PostGIS / MongoDB Geo / Uber H3 / Google S2 / Geohash / Elasticsearch Geo 사례. **포인트·다각형의 근접 검색·범위 검색** 을 O(log n) 으로.

**원전 참고**:
- Antonin Guttman — *R-trees: A Dynamic Index Structure for Spatial Searching* (SIGMOD 1984)
- Beckmann, Kriegel, Schneider, Seeger — *The R*-tree: An Efficient and Robust Access Method* (SIGMOD 1990)
- Hanan Samet — *Foundations of Multidimensional and Metric Data Structures* (2006)
- Jon Bentley — *Multidimensional Binary Search Trees* (CACM 1975) — KD-Tree
- Raphael Finkel & Jon Bentley — *Quad Trees: A Data Structure for Retrieval on Composite Keys* (Acta Informatica 1974)
- Gustavo Niemeyer — Geohash (2008)
- Uber Engineering — H3 (https://h3geo.org/, 2018)
- Google — S2 Geometry (https://s2geometry.io/)

## 알고리즘 목차

| ID | 영문명 | 한글명 | 시간 복잡도 | 적용 |
|----|--------|--------|------------|------|
| [r-tree](#r-tree) | R-Tree | R-트리 | O(log n) | 범용 공간 |
| [r-star-tree](#r-star-tree) | R*-Tree | R*-트리 | O(log n) | 최적화 R-Tree |
| [quadtree](#quadtree) | QuadTree | 쿼드트리 | O(log n) | 2D 4분할 |
| [kd-tree](#kd-tree) | KD-Tree | KD-트리 | O(log n) | k차원 NN |
| [geohash](#geohash) | Geohash | 지오해시 | O(1) lookup | lat/lon string |
| [h3](#h3) | H3 (Hexagonal Hierarchical) | 헥사고날 계층 인덱스 | O(1) lookup | hexagon grid |
| [s2](#s2) | S2 Geometry | S2 지오메트리 | O(1) lookup | sphere cell |
| [bvh](#bvh) | BVH (Bounding Volume Hierarchy) | 경계 볼륨 계층 | O(log n) | 3D / 레이트레이싱 |

**관련 카탈로그**:
- [geometry.md](geometry.md) — CCW / Convex Hull / Sweep Line (기하 기초)
- [data-structures.md](data-structures.md) — B-Tree (R-Tree 기반)
- [`../patterns/domains/logistics.md`](../patterns/domains/logistics.md) — Geofencing (응용)

---

<a id="r-tree"></a>
## 1. R-Tree (R-트리)

**목적**: 다차원 직사각형(MBR, Minimum Bounding Rectangle)을 B-Tree 처럼 디스크 페이지에 저장하여 공간 범위·근접 검색 효율화

**시간 복잡도**: O(log n) 평균, O(n) 최악 (MBR 겹침이 심한 경우)

**공간 복잡도**: O(n)

**특징**:
- B-Tree 의 다차원 확장 — 각 노드가 자식들의 MBR 합집합을 보관
- 리프 노드는 실제 객체의 MBR, 내부 노드는 자식 노드들의 MBR
- 한 노드는 m ≤ children ≤ M 개의 자식 (B-Tree 와 동일 균형 제약)
- MBR 이 겹칠 수 있어 같은 좌표에 대해 여러 경로 탐색 발생 가능

**알고리즘**:
```
검색(q_rect):
  1. 루트부터 시작
  2. 현재 노드의 모든 자식 MBR 중 q_rect 와 겹치는 것 찾기
  3. 겹치는 자식 모두 재귀 (∴ 여러 경로 동시 탐색)
  4. 리프면 실제 객체 MBR 검사 후 결과 반환

삽입(obj):
  1. ChooseSubtree: MBR 확장 비용이 최소인 자식 선택 (탐욕)
  2. 리프에 도달, 객체 추가
  3. 노드 overflow 시 분할 (Quadratic / Linear split)
  4. 부모로 전파하며 MBR 갱신
```

**MBR 구조 다이어그램**:
```
Root MBR  [───────────────────────────]
           │                            │
        ┌──┴───┐                  ┌─────┴─────┐
        │ MBR1 │                  │   MBR2    │
        ├──────┤                  ├───────────┤
        │ obj  │ obj │ obj        │ obj │ obj │
```

**장점**:
- 범용 공간 인덱싱 (점·선·다각형 모두 지원)
- 디스크 페이지와 잘 맞아 DBMS 표준
- 동적 삽입·삭제 효율적

**단점**:
- MBR 겹침으로 인한 탐색 효율 저하
- 노드 분할 휴리스틱에 성능이 크게 좌우됨
- 데이터 편향(skew) 에 취약

**실제 사용**:
- PostgreSQL/PostGIS GiST 인덱스 (기본)
- MySQL `SPATIAL INDEX`
- SQLite R*Tree 확장
- Oracle Spatial
- Java `java.awt.geom` 영역 지원

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 의사코드**:
```kotlin
data class Rect(val minX: Double, val minY: Double, val maxX: Double, val maxY: Double) {
    fun intersects(o: Rect): Boolean =
        !(maxX < o.minX || minX > o.maxX || maxY < o.minY || minY > o.maxY)

    fun union(o: Rect): Rect = Rect(
        minOf(minX, o.minX), minOf(minY, o.minY),
        maxOf(maxX, o.maxX), maxOf(maxY, o.maxY)
    )

    fun area(): Double = (maxX - minX) * (maxY - minY)
    fun enlargement(o: Rect): Double = union(o).area() - area()
}

sealed class RNode {
    abstract val mbr: Rect
}

data class RLeaf(override val mbr: Rect, val data: Any) : RNode()
class RInternal(var children: MutableList<RNode>) : RNode() {
    override val mbr: Rect
        get() = children.map { it.mbr }.reduce { a, b -> a.union(b) }
}

class RTree(private val M: Int = 4) {
    var root: RInternal = RInternal(mutableListOf())

    fun search(q: Rect, node: RNode = root, out: MutableList<Any> = mutableListOf()): List<Any> {
        when (node) {
            is RLeaf -> if (node.mbr.intersects(q)) out.add(node.data)
            is RInternal -> for (child in node.children)
                if (child.mbr.intersects(q)) search(q, child, out)
        }
        return out
    }

    // 삽입은 ChooseSubtree(확장 비용 최소 자식 선택) + 분할 로직 필요 — 생략
}
```

**SQL 예제 (PostGIS R-Tree GiST 인덱스)**:
```sql
CREATE TABLE stores (id SERIAL, geom GEOMETRY(Point, 4326));
CREATE INDEX idx_stores_geom ON stores USING GIST (geom);

-- 범위 검색: 사용자 위치 반경 1km 매장
SELECT id FROM stores
WHERE ST_DWithin(geom, ST_MakePoint(127.0, 37.5)::geography, 1000);
```

**관련 알고리즘**: R*-Tree, B-Tree, QuadTree

---

<a id="r-star-tree"></a>
## 2. R*-Tree (R*-트리, R-Tree 의 최적화)

**목적**: R-Tree 의 노드 분할·삽입 휴리스틱을 개선해 MBR 겹침·둘레·면적을 동시에 최소화

**시간 복잡도**: O(log n) — R-Tree 와 동일하지만 상수 효율 30~50% 개선

**공간 복잡도**: O(n)

**특징**:
- ChooseSubtree 시 리프 직전 단계에서는 **겹침(overlap) 증가량 최소** 자식 선택 (R-Tree 는 면적 확장만)
- Forced Reinsert — 노드 분할 전 일부 엔트리를 재삽입하여 트리 재배열
- 분할 시 **둘레(margin) → 면적 겹침 → 면적** 3단계 기준
- 동일 데이터로 R-Tree 보다 쿼리 성능 30~50% 향상

**알고리즘**:
```
삽입(obj):
  1. ChooseSubtree:
     - 리프 직전 단계: 자식 MBR 중 obj 추가 시 overlap 증가가 최소인 것
     - 그 외: area 확장 최소 자식
  2. 리프 도달 후 객체 추가
  3. Overflow 시:
     a. 처음 overflow 면 → Forced Reinsert (엔트리의 30% 재삽입)
     b. 두 번째 overflow → 분할 (margin → overlap → area 순)
```

**장점**:
- R-Tree 와 동일 API, 동일 디스크 레이아웃
- 쿼리 성능 우수
- 표준 알고리즘 — 라이브러리 다수

**단점**:
- 삽입 비용이 R-Tree 보다 큼 (forced reinsert 오버헤드)
- 구현 복잡

**실제 사용**:
- PostgreSQL/PostGIS GiST (R-Tree 변형으로 R*-Tree 휴리스틱 일부 채택)
- libspatialindex (Python, C++)
- Boost.Geometry `rtree` 의 `rstar<>` 변형
- ELKI (data mining), SpatiaLite

**난이도**: 매우 높음 | **사용 빈도**: ★★★★☆

**Python 예제 (rtree library)**:
```python
from rtree import index

# R*-Tree 사용 (rstar variant)
p = index.Property()
p.variant = index.RT_Star  # R*-Tree 휴리스틱 활성화
p.dimension = 2

idx = index.Index(properties=p)
idx.insert(1, (0.0, 0.0, 1.0, 1.0))   # id=1, MBR
idx.insert(2, (2.0, 2.0, 3.0, 3.0))
idx.insert(3, (0.5, 0.5, 2.5, 2.5))

# 범위 검색
hits = list(idx.intersection((0.0, 0.0, 2.0, 2.0)))
# → [1, 3]

# 최근접 k개
nearest = list(idx.nearest((1.5, 1.5, 1.5, 1.5), num_results=2))
```

**R-Tree vs R*-Tree 비교**:

| 항목 | R-Tree | R*-Tree |
|------|--------|---------|
| 분할 기준 | area 만 | margin → overlap → area |
| Reinsert | 없음 | Forced Reinsert (overflow 시) |
| 쿼리 성능 | baseline | +30~50% |
| 삽입 비용 | 낮음 | 30% ↑ |
| 구현 난이도 | 중상 | 높음 |

**관련 알고리즘**: R-Tree, X-Tree, Hilbert R-Tree

---

<a id="quadtree"></a>
## 3. QuadTree (쿼드트리, 2D 4분할 재귀)

**목적**: 2D 평면을 재귀적으로 4분할하여 sparse 한 점/객체 분포를 효율 저장

**시간 복잡도**: O(log n) 균등 분포, O(n) 최악 (한 영역에 집중)

**공간 복잡도**: O(n) ~ O(n log n)

**특징**:
- 한 노드의 객체 수가 임계값(capacity, 보통 4) 초과 시 4분할
- 4 자식 = NW(북서), NE(북동), SW(남서), SE(남동)
- Point QuadTree (Finkel & Bentley 1974) — 점만 저장
- Region QuadTree — 영역(이미지 픽셀) 저장
- PMR/PR QuadTree — 다각형 저장

**4분할 구조**:
```
       ┌─────────┬─────────┐
       │   NW    │   NE    │
       │ ●  ●    │         │
       │   ●     │  ●      │
       ├─────────┼─────────┤
       │   SW    │   SE    │
       │         │  ●   ●  │
       │   ●     │      ●  │
       └─────────┴─────────┘
       NW 가 다시 4분할 → 재귀
```

**알고리즘**:
```
insert(node, point):
  1. node 의 영역에 point 가 없으면 false
  2. node.points.size < capacity 이고 leaf 면 추가
  3. 아니면 subdivide() 호출 (한 번만)
  4. 4 자식 중 하나에 재귀 삽입

queryRange(node, range, found):
  1. node.boundary 와 range 가 겹치지 않으면 return
  2. node.points 검사 후 range 안의 점 추가
  3. divided 면 4 자식 모두 재귀
```

**장점**:
- 구현 단순
- sparse 한 분포에 매우 효율적
- 이미지 압축·게임 충돌 표준
- 적응형 — 밀집 영역만 깊게 분할

**단점**:
- 데이터 편향에 매우 취약 (한 점에 몰리면 무한 분할)
- 점 1개라도 깊은 트리 생성 가능 — max depth 제한 필요
- 좌표가 정확히 경계에 있으면 모호

**실제 사용**:
- 게임 충돌 판정 (대규모 sprite)
- 이미지 압축 (JPEG2000)
- GIS 영역 인덱싱
- 천체 시뮬레이션 (Barnes-Hut N-body)
- Minecraft 청크 관리

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
data class QPoint(val x: Double, val y: Double)
data class Boundary(val cx: Double, val cy: Double, val hw: Double, val hh: Double) {
    fun contains(p: QPoint) =
        p.x >= cx - hw && p.x < cx + hw && p.y >= cy - hh && p.y < cy + hh

    fun intersects(other: Boundary): Boolean =
        !(other.cx - other.hw > cx + hw || other.cx + other.hw < cx - hw ||
          other.cy - other.hh > cy + hh || other.cy + other.hh < cy - hh)
}

class QuadTree(val boundary: Boundary, val capacity: Int = 4) {
    private val points = mutableListOf<QPoint>()
    private var divided = false
    private var nw: QuadTree? = null
    private var ne: QuadTree? = null
    private var sw: QuadTree? = null
    private var se: QuadTree? = null

    fun insert(p: QPoint): Boolean {
        if (!boundary.contains(p)) return false
        if (points.size < capacity && !divided) {
            points.add(p); return true
        }
        if (!divided) subdivide()
        return nw!!.insert(p) || ne!!.insert(p) ||
               sw!!.insert(p) || se!!.insert(p)
    }

    private fun subdivide() {
        val hw = boundary.hw / 2; val hh = boundary.hh / 2
        nw = QuadTree(Boundary(boundary.cx - hw, boundary.cy - hh, hw, hh), capacity)
        ne = QuadTree(Boundary(boundary.cx + hw, boundary.cy - hh, hw, hh), capacity)
        sw = QuadTree(Boundary(boundary.cx - hw, boundary.cy + hh, hw, hh), capacity)
        se = QuadTree(Boundary(boundary.cx + hw, boundary.cy + hh, hw, hh), capacity)
        divided = true
    }

    fun queryRange(range: Boundary, found: MutableList<QPoint> = mutableListOf()): List<QPoint> {
        if (!boundary.intersects(range)) return found
        for (p in points) if (range.contains(p)) found.add(p)
        if (divided) {
            nw!!.queryRange(range, found); ne!!.queryRange(range, found)
            sw!!.queryRange(range, found); se!!.queryRange(range, found)
        }
        return found
    }
}
```

**관련 알고리즘**: Octree (3D), R-Tree, KD-Tree

---

<a id="kd-tree"></a>
## 4. KD-Tree (k차원 binary tree, NN 검색)

**목적**: k차원 점 데이터를 binary tree 로 분할하여 nearest neighbor·범위 검색 O(log n) 으로

**시간 복잡도**:
- 균형 트리 구성: O(n log² n) (median 선택)
- 검색: O(log n) 평균, O(n) 최악 (고차원)
- NN 검색: O(log n) 저차원, O(n) 고차원 (curse of dimensionality)

**공간 복잡도**: O(n)

**특징**:
- 각 깊이마다 분할 축(axis) 을 순환 (depth % k) — x, y, z, ...
- 분할 기준은 median 좌표 — 좌측에 < median, 우측에 ≥ median
- Binary Tree 라 구현 단순
- k > 10~20 에서 효율 급격히 저하 (curse of dimensionality)

**구조 다이어그램** (2D, 깊이 0 = x축, 깊이 1 = y축):
```
              (7, 2) — split x = 7
             /        \
        (5, 4)         (9, 6)  — split y
        /    \          /
   (2, 3) (4, 7)   (8, 1)
```

**알고리즘**:
```
build(points, depth):
  if points.empty: return null
  axis = depth % k
  points.sortBy { it[axis] }
  median = points.size / 2
  return Node(
      point = points[median],
      axis = axis,
      left = build(points[0..median-1], depth + 1),
      right = build(points[median+1..end], depth + 1)
  )

nearestNeighbor(node, query, best):
  if node == null: return best
  if dist(query, node.point) < dist(query, best):
      best = node.point
  // 쿼리 점이 분할면의 어느 쪽인지
  diff = query[node.axis] - node.point[node.axis]
  (near, far) = if (diff < 0) (node.left, node.right) else (node.right, node.left)
  best = nearestNeighbor(near, query, best)
  // 반대편도 탐색해야 하는지 (분할면까지 거리 < 현재 최선)
  if (diff² < dist(query, best)):
      best = nearestNeighbor(far, query, best)
  return best
```

**장점**:
- 구현 단순
- 정적 데이터에 매우 빠름
- nearest neighbor 검색에 표준

**단점**:
- 동적 삽입/삭제 시 균형 깨짐 — rebuild 필요
- 고차원에서 효율 저하 (k > 20 권장 안 함)
- 메모리 기반 — 디스크 친화 ↓

**실제 사용**:
- scikit-learn `KDTree`, `NearestNeighbors`
- SciPy `scipy.spatial.KDTree`
- 머신러닝 KNN 분류
- 광선 추적 (보조)
- 3D 모델 충돌 (저차원)
- ANN(Approximate NN) 의 기반

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
data class KdPoint(val coords: DoubleArray) {
    operator fun get(i: Int) = coords[i]
    val k: Int get() = coords.size
}

class KdNode(val point: KdPoint, val axis: Int, var left: KdNode? = null, var right: KdNode? = null)

class KdTree(points: List<KdPoint>) {
    private val k = points[0].k
    val root: KdNode? = build(points.toMutableList(), 0)

    private fun build(points: MutableList<KdPoint>, depth: Int): KdNode? {
        if (points.isEmpty()) return null
        val axis = depth % k
        points.sortBy { it[axis] }
        val median = points.size / 2
        return KdNode(
            point = points[median],
            axis = axis,
            left = build(points.subList(0, median).toMutableList(), depth + 1),
            right = build(points.subList(median + 1, points.size).toMutableList(), depth + 1)
        )
    }

    private fun distSq(a: KdPoint, b: KdPoint): Double {
        var s = 0.0
        for (i in 0 until k) {
            val d = a[i] - b[i]; s += d * d
        }
        return s
    }

    fun nearest(query: KdPoint): KdPoint? {
        var best: KdPoint? = null
        var bestDist = Double.MAX_VALUE

        fun search(node: KdNode?) {
            if (node == null) return
            val d = distSq(query, node.point)
            if (d < bestDist) { bestDist = d; best = node.point }
            val diff = query[node.axis] - node.point.coords[node.axis]
            val (near, far) = if (diff < 0) node.left to node.right
                              else node.right to node.left
            search(near)
            if (diff * diff < bestDist) search(far)
        }
        search(root)
        return best
    }
}
```

**Python 예제 (scikit-learn)**:
```python
from sklearn.neighbors import KDTree
import numpy as np

X = np.array([[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]])
tree = KDTree(X, leaf_size=2)
dist, idx = tree.query([[0.5, 0.5]], k=2)
# → idx = [[0, 1]], dist = [[0.707, 0.707]]
```

**관련 알고리즘**: Ball Tree, BKD-Tree (Lucene), VP-Tree, Annoy/HNSW (고차원 대체)

---

<a id="geohash"></a>
## 5. Geohash (지오해시 — lat/lon → base32 string)

**목적**: 위도·경도를 base32 문자열로 인코딩하여 prefix 매칭으로 공간 근접 검색

**시간 복잡도**:
- 인코딩/디코딩: O(precision) — 보통 O(1)
- prefix 검색: O(1) 인덱스 lookup

**공간 복잡도**: O(precision) per hash — 보통 8~12 bytes

**특징**:
- 위도·경도를 비트 단위로 interleave 하여 base32 인코딩
- precision 1자(±2500km) ~ 12자(±3.7cm) 까지 조정 가능
- **prefix 가 같으면 공간적으로 인접** — `wydm` 시작 = 인천 일대
- 단순 문자열이라 일반 B-Tree, Hash, Redis Sorted Set 어디에나 인덱싱 가능
- 단점: **경계 효과(edge effect)** — Hash 가 달라도 물리적으로 가까울 수 있음 (예: `wydm9` 와 `wydmd` 는 인접하지만 다른 prefix)

**Precision 표**:

| 길이 | 위경도 오차 | 셀 크기 (적도) |
|------|-----------|--------------|
| 1 | ±23° | 5000 × 5000 km |
| 4 | ±0.18° | 39.1 × 19.5 km |
| 5 | ±0.022° | 4.89 × 4.89 km |
| 6 | ±0.0027° | 1.22 × 0.61 km |
| 7 | ±0.00034° | 153 × 153 m |
| 8 | ±0.000042° | 38.2 × 19.1 m |
| 9 | ±0.0000053° | 4.77 × 4.77 m |
| 12 | ±~1e-8° | 3.7 × 1.9 cm |

**인코딩 알고리즘**:
```
encode(lat, lon, precision):
  latRange = [-90, 90]
  lonRange = [-180, 180]
  bits = []

  while bits.size < precision * 5:
    if (bits.size + 1) is odd:  // 홀수 비트 = lon
      mid = (lonRange[0] + lonRange[1]) / 2
      if lon >= mid: bits.add(1); lonRange[0] = mid
      else:          bits.add(0); lonRange[1] = mid
    else:                       // 짝수 비트 = lat
      mid = (latRange[0] + latRange[1]) / 2
      if lat >= mid: bits.add(1); latRange[0] = mid
      else:          bits.add(0); latRange[1] = mid

  return base32(bits, "0123456789bcdefghjkmnpqrstuvwxyz")
```

**Base32 알파벳** (혼동 방지 — `a/i/l/o` 제외):
```
0  1  2  3  4  5  6  7  8  9
b  c  d  e  f  g  h  j  k  m
n  p  q  r  s  t  u  v  w  x
y  z
```

**장점**:
- 단순 문자열 — 어디서나 인덱싱 가능 (RDB, Redis, Elasticsearch)
- prefix 매칭으로 범위 검색
- precision 조정으로 zoom level 표현
- URL/공유 가능

**단점**:
- 경계 효과 — 인접 셀의 prefix 가 완전히 다를 수 있음 → **8 인접 셀(neighbors) 까지 함께 검색** 필요
- 적도/극 근처 셀 크기 비균등 (적도 대비 극지방이 작음)
- 직사각형 셀 — 거리 측정 부정확

**실제 사용**:
- Elasticsearch `geohash_grid` aggregation
- Redis Geo commands (`GEOADD`, `GEORADIUS`)
- Couchbase, MongoDB(과거)
- DynamoDB GSI 공간 키
- 음식 배달 앱의 driver-rider 매칭 (Hashed neighbor 검색)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
object Geohash {
    private const val BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

    fun encode(lat: Double, lon: Double, precision: Int = 9): String {
        var latRange = -90.0 to 90.0
        var lonRange = -180.0 to 180.0
        val bits = StringBuilder()
        var even = true

        while (bits.length < precision * 5) {
            if (even) {  // lon
                val mid = (lonRange.first + lonRange.second) / 2
                if (lon >= mid) { bits.append('1'); lonRange = mid to lonRange.second }
                else            { bits.append('0'); lonRange = lonRange.first to mid }
            } else {     // lat
                val mid = (latRange.first + latRange.second) / 2
                if (lat >= mid) { bits.append('1'); latRange = mid to latRange.second }
                else            { bits.append('0'); latRange = latRange.first to mid }
            }
            even = !even
        }

        return bits.toString().chunked(5)
            .joinToString("") { BASE32[it.toInt(2)].toString() }
    }

    fun decode(hash: String): Pair<Double, Double> {
        var latRange = -90.0 to 90.0
        var lonRange = -180.0 to 180.0
        var even = true
        for (c in hash) {
            val idx = BASE32.indexOf(c)
            val bits = idx.toString(2).padStart(5, '0')
            for (b in bits) {
                if (even) {  // lon
                    val mid = (lonRange.first + lonRange.second) / 2
                    lonRange = if (b == '1') mid to lonRange.second else lonRange.first to mid
                } else {
                    val mid = (latRange.first + latRange.second) / 2
                    latRange = if (b == '1') mid to latRange.second else latRange.first to mid
                }
                even = !even
            }
        }
        return ((latRange.first + latRange.second) / 2) to ((lonRange.first + lonRange.second) / 2)
    }
}

// 사용 예
val hash = Geohash.encode(37.5665, 126.9780, 7)
// → "wydm9qg" (서울 시청 근처)

// prefix 매칭으로 1.2km 셀 내 검색
val seoulPrefix = hash.substring(0, 6)  // "wydm9q"
// DB: SELECT * FROM places WHERE geohash LIKE 'wydm9q%'
```

**SQL 예제 (Redis Geo)**:
```redis
GEOADD restaurants 126.9780 37.5665 "myeongdong-pasta"
GEOADD restaurants 126.9820 37.5703 "gwanghwamun-sushi"

GEORADIUS restaurants 126.9800 37.5680 500 m WITHCOORD WITHDIST
# → 두 매장 모두 반환 (500m 이내)
```

**경계 효과 해결 — 8 neighbors**:
```
       ┌─────┬─────┬─────┐
       │ NW  │  N  │ NE  │
       ├─────┼─────┼─────┤
       │  W  │self │  E  │   ← 검색 시 self + 8 neighbors 모두 쿼리
       ├─────┼─────┼─────┤
       │ SW  │  S  │ SE  │
       └─────┴─────┴─────┘
```

**관련 알고리즘**: H3, S2, Z-order curve, Hilbert curve

---

<a id="h3"></a>
## 6. H3 (Hexagonal Hierarchical, Uber 2018)

**목적**: 지구 표면을 16 단계 해상도의 hexagon 셀로 분할하여 균등 분포 공간 인덱싱

**시간 복잡도**:
- 인코딩/디코딩: O(1)
- 인접 셀 조회: O(1)
- k-ring 검색: O(k²)

**공간 복잡도**: 셀당 64 bit (8 bytes) — `H3Index`

**특징**:
- 12면체(icosahedron) 기반 hexagon tiling — 122 base cell 에서 시작해 7-aperture 로 재귀
- **해상도 0** (4250 km²/cell) ~ **해상도 15** (0.9 m²/cell)
- 모든 hexagon 의 6 이웃이 등거리 — **균등 분포** (R-Tree·Geohash 의 직사각형 비균등 보완)
- 단점: 12 개의 pentagon 셀 (정십이면체 꼭짓점) — 일부 영역에 hexagon 대신 pentagon
- 계층적 — 자식 7개로 분할 (Geohash 32 분할보다 부드러움)

**Hexagon vs 직사각형 비교**:
```
직사각형(Geohash):           Hexagon(H3):
  ┌──┬──┬──┐                  ⬡ ⬡ ⬡
  │  │  │  │                 ⬡ ⬡ ⬡ ⬡
  ├──┼──┼──┤                  ⬡ ⬡ ⬡
  │  │  │  │
  └──┴──┴──┘                 모든 이웃이 등거리
  4 이웃 / 4 대각선
  (대각선 거리가 다름)
```

**해상도 표** (자주 쓰이는 범위):

| Resolution | 평균 면적 | 평균 변 길이 | 용도 |
|------------|---------|------------|------|
| 0 | 4,250,547 km² | 1107 km | 대륙 |
| 4 | 1,770 km² | 22.6 km | 도시 권역 |
| 6 | 36.1 km² | 3.23 km | 도시 |
| 7 | 5.16 km² | 1.22 km | 동/구 |
| 8 | 0.737 km² | 461 m | 동네 |
| 9 | 0.105 km² | 174 m | 블록 |
| 10 | 0.015 km² | 65.9 m | 매장 |
| 11 | 0.00214 km² | 24.9 m | 건물 |
| 12 | 0.000306 km² | 9.42 m | 방 |
| 15 | 0.895 m² | 0.51 m | 보행자 |

**알고리즘 핵심**:
```
latLngToCell(lat, lng, resolution) -> H3Index:
  1. 지구를 icosahedron 으로 투영
  2. (lat, lng) 가 속한 face 결정 (20면 중 하나)
  3. face 내 좌표를 IJK (hexagon 좌표계) 로 변환
  4. resolution 단계까지 7-aperture 자식 추적
  5. (face, resolution, IJK path) 를 64bit 정수로 인코딩

cellToLatLng(h3Index) -> (lat, lng):
  1. 64bit 정수에서 (face, resolution, IJK path) 추출
  2. IJK → 평면 좌표 → 구면 좌표 역변환

kRing(center, k):  // 중심에서 k 거리 이내 모든 셀
  1. 단계별로 인접 hexagon 6개씩 확장 (BFS)
  2. pentagon 도착 시 한 방향 누락 처리
```

**장점**:
- 모든 이웃이 등거리 → 거리 기반 분석 정확
- 균등 분포 — 클러스터링·집계에 적합
- 계층적 — zoom in/out 단순
- 공식 라이브러리 — Java/Python/JavaScript/Go/Rust/C
- Uber·Foursquare·Airbnb 등 대규모 검증

**단점**:
- 12 개 pentagon 셀 — edge case 처리 필요
- 자식 셀이 부모를 완전히 덮지 않음 (overlap/gap 있음) — 영역 합산 시 보정 필요
- Geohash 만큼 prefix 매칭이 자연스럽지 않음 (셀 ID 가 비트 패킹 정수)

**실제 사용**:
- Uber driver-rider 매칭
- Foursquare visit attribution
- Airbnb price heatmap
- CARTO 공간 분석 플랫폼
- BigQuery `carto.H3_*` 함수
- 한국 카카오 모빌리티 (택시 수요 예측)

**난이도**: 중간 (라이브러리 사용) / 매우 높음 (직접 구현) | **사용 빈도**: ★★★★★

**Python 예제 (uber-h3)**:
```python
import h3

# 위경도 → H3 cell
cell = h3.geo_to_h3(37.5665, 126.9780, resolution=9)
# → '8930e1d8723ffff' (서울 시청 부근, 174m 변)

# H3 cell → 위경도 (중심)
lat, lng = h3.h3_to_geo(cell)

# k-ring: 반경 k 셀 이내 (k=2 → 19개 셀)
neighbors = h3.k_ring(cell, k=2)

# Polygon → H3 셀 집합
polygon_geojson = {
    "type": "Polygon",
    "coordinates": [[[126.97, 37.55], [126.99, 37.55],
                     [126.99, 37.57], [126.97, 37.57], [126.97, 37.55]]]
}
cells = h3.polyfill(polygon_geojson, res=9)

# 계층 — 부모/자식
parent = h3.h3_to_parent(cell, res=7)        # 한 단계 상위
children = h3.h3_to_children(cell, res=11)   # 두 단계 하위 (49개)
```

**Kotlin 예제 (uber-h3-java)**:
```kotlin
import com.uber.h3core.H3Core

val h3 = H3Core.newInstance()

val cell: Long = h3.geoToH3(37.5665, 126.9780, 9)
val center: GeoCoord = h3.h3ToGeo(cell)
val ring: List<Long> = h3.kRing(cell, 2)  // 19개 인접 셀

// 거리 — 셀 단위
val distance: Int = h3.h3Distance(cellA, cellB)
```

**관련 알고리즘**: S2, Geohash, Octree

---

<a id="s2"></a>
## 7. S2 Geometry (Google, sphere cell + Hilbert curve)

**목적**: 지구를 6면 cube 로 투영 후 Hilbert curve 로 셀을 1D 공간 채움 곡선에 매핑하여 공간 인덱싱

**시간 복잡도**:
- CellId 인코딩/디코딩: O(1)
- Cell ↔ 위경도: O(1)
- 범위 cover: O(log n) — 다각형을 셀 집합으로 근사

**공간 복잡도**: CellId 당 64 bit

**특징**:
- 지구 표면 = cube 6 면 (icosahedron 의 H3 와 다름)
- 각 면은 4분할 quadtree 로 재귀 → **30 level** (level 0 = 1/6 of Earth, level 30 = 1 cm²)
- **Hilbert space-filling curve** 로 셀에 1D 순번 부여 — 공간적으로 가까운 셀이 1D 에서도 가까움
- 64bit CellId = face(3 bit) + level(0~30 quadtree path) + sentinel
- **CellId 가 정수라 B-Tree 인덱스 직접 사용 가능** (Geohash 의 문자열보다 효율적)

**Hilbert curve 효과**:
```
좌표를 1D 로 변환할 때:
  - Z-order (Morton): 점프 발생 ───┐
                                    └─ 비효율
  - Geohash:        점프 발생 (경계)
  - Hilbert (S2):   연속적 ───────── 효율적 cache locality
```

**구조 다이어그램**:
```
Earth → Cube 6 faces → Quadtree 30 levels
                       Each level = 4× more cells
                       Cell ID = 64 bit Hilbert index
```

**Level 표**:

| Level | 평균 면적 | 변 길이 (적도) |
|-------|---------|--------------|
| 0 | 85,011,012 km² | 7842 km |
| 4 | 332,072 km² | 487 km |
| 8 | 1,297 km² | 30.5 km |
| 10 | 81 km² | 7.6 km |
| 12 | 5 km² | 1.9 km |
| 14 | 0.32 km² | 477 m |
| 16 | 0.02 km² | 119 m |
| 20 | 78 m² | 7.4 m |
| 24 | 0.30 m² | 0.46 m |
| 30 | 0.74 cm² | 0.7 cm |

**Region Coverer 알고리즘** (다각형을 cell 집합으로):
```
RegionCoverer.getCovering(region):
  1. min_level, max_level, max_cells 지정
  2. region 을 포함하는 가장 큰 셀에서 시작
  3. 각 셀에 대해:
     - 셀이 region 에 완전히 들어가면 그대로 추가
     - 일부만 겹치면 4 자식으로 분할 후 재귀
     - max_cells 도달 시 분할 중단
  4. 결과: 셀 ID 의 정렬된 집합
```

**장점**:
- CellId 가 64bit 정수 — 표준 B-Tree 인덱스 직접 사용
- Hilbert curve 로 범위 쿼리가 1D 범위 쿼리로 환원
- 30 level — H3 보다 세밀한 zoom
- 정확한 구면 기하 (대원 거리, 다각형 면적)
- Google Maps·Foursquare 검증

**단점**:
- Cube → sphere 투영으로 셀 크기 약간 비균등
- 직사각형 cell — H3 의 hexagon 보다 인접 거리 비균등
- 라이브러리 의존성 (C++/Java/Python/Go)

**실제 사용**:
- Google Maps 백엔드
- Foursquare 장소 검색
- MongoDB `2dsphere` 인덱스 (S2 기반)
- Pokémon Go 셀 시스템 (Niantic — L12/L14/L17)
- Wayfair 배송 권역
- Tinder 위치 매칭 (과거)

**난이도**: 매우 높음 (직접 구현) / 중간 (라이브러리) | **사용 빈도**: ★★★★☆

**Python 예제 (s2sphere)**:
```python
import s2sphere

# 위경도 → S2 CellId
ll = s2sphere.LatLng.from_degrees(37.5665, 126.9780)
cell_id = s2sphere.CellId.from_lat_lng(ll)         # level 30 (최대 정밀)
cell = s2sphere.Cell(cell_id.parent(14))            # level 14 (≈ 477m)
print(cell.id().to_token())
# → '35654b'

# 영역 cover
region = s2sphere.LatLngRect(
    s2sphere.LatLng.from_degrees(37.55, 126.97),
    s2sphere.LatLng.from_degrees(37.58, 127.00),
)
coverer = s2sphere.RegionCoverer()
coverer.min_level = 12
coverer.max_level = 14
coverer.max_cells = 8
covering = coverer.get_covering(region)
# → [CellId, ...] 8 셀 이하로 영역 근사
```

**SQL 예제 (MongoDB 2dsphere)**:
```javascript
db.places.createIndex({ location: "2dsphere" })

db.places.find({
  location: {
    $near: {
      $geometry: { type: "Point", coordinates: [126.9780, 37.5665] },
      $maxDistance: 1000  // 1km
    }
  }
})
// 내부적으로 S2 셀 인덱싱 사용
```

**H3 vs S2 비교**:

| 항목 | H3 | S2 |
|------|----|----|
| 셀 모양 | Hexagon | Rectangle |
| 투영 | Icosahedron | Cube |
| 인접 거리 | 모두 동일 | 4 변 / 4 대각선 (다름) |
| Pentagon 예외 | 12개 (특수 처리) | 없음 |
| 셀 ID | 64bit (face + IJK) | 64bit (face + Hilbert) |
| Level 수 | 16 (0~15) | 30 (0~30) |
| Space-filling curve | 비공식 | Hilbert (공식) |
| 범위 쿼리 | k-ring | 1D Hilbert range |
| 대표 사용처 | Uber, Foursquare | Google Maps, MongoDB |

**관련 알고리즘**: H3, Geohash, Hilbert curve, Z-order curve

---

<a id="bvh"></a>
## 8. BVH (Bounding Volume Hierarchy, 3D 레이트레이싱 표준)

**목적**: 3D 객체의 AABB(Axis-Aligned Bounding Box) 트리로 광선 교차·충돌 판정 가속

**시간 복잡도**:
- 구성: O(n log n) — SAH (Surface Area Heuristic)
- 광선 교차: O(log n) 평균
- 충돌 판정: O(log n) 평균

**공간 복잡도**: O(n)

**특징**:
- AABB(Axis-Aligned Bounding Box) — 축 정렬 직육면체 — 가장 빠른 교차 판정
- 리프 = 실제 객체(또는 객체의 작은 묶음), 내부 노드 = 자식들의 AABB 합집합
- **SAH (Surface Area Heuristic)** — 분할 비용 = 좌측 AABB 표면적 × 좌측 객체 수 + 우측 표면적 × 우측 객체 수, 이를 최소화하는 분할면 선택
- **GPU 친화** — flat array 로 저장 가능, 광선 추적 하드웨어(RT core) 가 직접 가속
- R-Tree 와 유사하나 **3D + 정적 + 광선 트레이싱** 최적화

**Ray-AABB 교차 알고리즘** (slab method):
```
rayAABBIntersect(ray, aabb) -> (tMin, tMax) 또는 miss:
  tMin = -inf; tMax = +inf
  for axis in [x, y, z]:
    if abs(ray.dir[axis]) < epsilon:
      // 광선이 이 축에 평행 — 시작점이 slab 안에 있는지만 검사
      if ray.origin[axis] < aabb.min[axis] || ray.origin[axis] > aabb.max[axis]:
        return miss
    else:
      t1 = (aabb.min[axis] - ray.origin[axis]) / ray.dir[axis]
      t2 = (aabb.max[axis] - ray.origin[axis]) / ray.dir[axis]
      if t1 > t2: swap(t1, t2)
      tMin = max(tMin, t1)
      tMax = min(tMax, t2)
      if tMin > tMax: return miss
  return (tMin, tMax)
```

**BVH 트리 traversal**:
```
traverse(node, ray, best):
  if !rayAABBIntersect(ray, node.aabb): return
  if node.isLeaf:
    for obj in node.objects:
      hit = rayObjectIntersect(ray, obj)
      if hit.t < best.t: best = hit
  else:
    // 가까운 자식부터 (조기 종료 가능성)
    (near, far) = sortByDistance(node.left, node.right, ray)
    traverse(near, ray, best)
    if far.aabb.tMin < best.t:  // 가지치기
      traverse(far, ray, best)
```

**SAH (Surface Area Heuristic) 분할 비용**:
```
cost(split) = traversalCost +
              (leftSA / parentSA) × leftCount × intersectCost +
              (rightSA / parentSA) × rightCount × intersectCost

→ 가능한 모든 분할 면에 대해 cost 계산, 최소 cost 선택
   휴리스틱: object median, spatial median 이 더 빠르지만 품질 ↓
```

**장점**:
- 광선 추적 표준 — Embree, OptiX, RT core 모두 사용
- 동적 씬도 refit 으로 빠른 갱신
- 균형 트리 — 최악 O(n) 회피
- 메모리 효율 — flat array (cache locality)

**단점**:
- AABB 가 비효율적인 객체(긴 대각선 막대) 에 약함 — OBB 대안
- 정적 구성이 가장 빠르고, 동적 씬은 refit/rebuild 필요
- SAH 구성 시간 O(n log² n) — 게임에서는 더 빠른 휴리스틱

**실제 사용**:
- Embree (Intel CPU 광선 추적)
- NVIDIA OptiX / RT core (RTX GPU)
- Unity / Unreal 충돌 판정
- Bullet Physics, PhysX 광역 검색 (broadphase)
- Blender Cycles 렌더러
- Pixar RenderMan

**난이도**: 매우 높음 | **사용 빈도**: ★★★★☆ (3D 그래픽스에서)

**Kotlin 의사코드**:
```kotlin
data class Vec3(val x: Double, val y: Double, val z: Double)
data class AABB(val min: Vec3, val max: Vec3) {
    fun union(o: AABB) = AABB(
        Vec3(minOf(min.x, o.min.x), minOf(min.y, o.min.y), minOf(min.z, o.min.z)),
        Vec3(maxOf(max.x, o.max.x), maxOf(max.y, o.max.y), maxOf(max.z, o.max.z))
    )
    fun surfaceArea(): Double {
        val d = Vec3(max.x - min.x, max.y - min.y, max.z - min.z)
        return 2 * (d.x * d.y + d.y * d.z + d.z * d.x)
    }
}

data class Ray(val origin: Vec3, val dir: Vec3) {
    val invDir = Vec3(1.0 / dir.x, 1.0 / dir.y, 1.0 / dir.z)
}

fun rayAABB(ray: Ray, aabb: AABB): Pair<Double, Double>? {
    val t1x = (aabb.min.x - ray.origin.x) * ray.invDir.x
    val t2x = (aabb.max.x - ray.origin.x) * ray.invDir.x
    val t1y = (aabb.min.y - ray.origin.y) * ray.invDir.y
    val t2y = (aabb.max.y - ray.origin.y) * ray.invDir.y
    val t1z = (aabb.min.z - ray.origin.z) * ray.invDir.z
    val t2z = (aabb.max.z - ray.origin.z) * ray.invDir.z

    val tMin = maxOf(minOf(t1x, t2x), minOf(t1y, t2y), minOf(t1z, t2z))
    val tMax = minOf(maxOf(t1x, t2x), maxOf(t1y, t2y), maxOf(t1z, t2z))
    return if (tMax >= maxOf(tMin, 0.0)) tMin to tMax else null
}

interface Hittable {
    val aabb: AABB
    fun hit(ray: Ray): Double?  // t 값, null = miss
}

sealed class BvhNode {
    abstract val aabb: AABB
}
class BvhLeaf(val objects: List<Hittable>) : BvhNode() {
    override val aabb = objects.map { it.aabb }.reduce { a, b -> a.union(b) }
}
class BvhInternal(val left: BvhNode, val right: BvhNode) : BvhNode() {
    override val aabb = left.aabb.union(right.aabb)
}

fun buildBvh(objects: List<Hittable>, leafSize: Int = 4): BvhNode {
    if (objects.size <= leafSize) return BvhLeaf(objects)

    // 가장 긴 축 선택 후 median 분할 (간이 휴리스틱)
    val parentAABB = objects.map { it.aabb }.reduce { a, b -> a.union(b) }
    val dx = parentAABB.max.x - parentAABB.min.x
    val dy = parentAABB.max.y - parentAABB.min.y
    val dz = parentAABB.max.z - parentAABB.min.z
    val axis = if (dx > dy && dx > dz) 0 else if (dy > dz) 1 else 2

    val sorted = objects.sortedBy {
        when (axis) {
            0 -> it.aabb.min.x; 1 -> it.aabb.min.y; else -> it.aabb.min.z
        }
    }
    val mid = sorted.size / 2
    return BvhInternal(
        buildBvh(sorted.subList(0, mid), leafSize),
        buildBvh(sorted.subList(mid, sorted.size), leafSize)
    )
}

fun intersect(node: BvhNode, ray: Ray, best: Double = Double.MAX_VALUE): Double {
    val hit = rayAABB(ray, node.aabb) ?: return best
    if (hit.first > best) return best  // 가지치기
    return when (node) {
        is BvhLeaf -> {
            var b = best
            for (obj in node.objects) {
                val t = obj.hit(ray) ?: continue
                if (t in 0.0..b) b = t
            }
            b
        }
        is BvhInternal -> {
            // 가까운 자식부터
            val lHit = rayAABB(ray, node.left.aabb)?.first ?: Double.MAX_VALUE
            val rHit = rayAABB(ray, node.right.aabb)?.first ?: Double.MAX_VALUE
            val (near, far) = if (lHit < rHit) node.left to node.right
                              else node.right to node.left
            var b = intersect(near, ray, best)
            b = intersect(far, ray, b)
            b
        }
    }
}
```

**BVH vs R-Tree 비교**:

| 항목 | BVH | R-Tree |
|------|-----|--------|
| 차원 | 주로 3D | 주로 2D |
| 구성 | 정적 (offline) | 동적 (online) |
| 분할 | SAH 휴리스틱 | Quadratic/Linear split |
| 저장 | flat array (메모리) | 디스크 페이지 |
| 핵심 쿼리 | 광선 교차 | 범위 검색 |
| 가속 | GPU/RT core | CPU/DB |
| 사용처 | 렌더링, 게임 | DBMS, GIS |

**관련 알고리즘**: KD-Tree, Octree, R-Tree, SAH

---

## 알고리즘 선택 가이드

### 시나리오별 추천

| 시나리오 | 1순위 | 2순위 | 사유 |
|---------|------|------|------|
| RDBMS 공간 인덱스 (PostGIS, MySQL) | R-Tree (R*-Tree 변형) | — | DBMS 표준 |
| 위경도 prefix 검색, Redis 지원 | Geohash | — | 문자열 + Redis Geo |
| 균등 분포 셀 집계 (heatmap, demand zone) | H3 | S2 | hexagon 등거리 |
| MongoDB / Google Maps 백엔드 | S2 | H3 | 1D Hilbert 범위 쿼리 |
| 머신러닝 KNN | KD-Tree | Ball Tree | 저차원 NN |
| 2D 게임 충돌 (대량 sprite) | QuadTree | R-Tree | sparse 분포 적합 |
| 3D 광선 추적 / 렌더링 | BVH | KD-Tree | RT core 친화 |
| 3D 충돌 (broadphase) | BVH | Octree | 동적 갱신 |
| 시 단위 권역 분석 | H3 res 6~7 | S2 level 10~12 | 적정 셀 크기 |
| 실시간 배달 매칭 (1km) | Geohash precision 6 + 8 neighbors | H3 res 8 | 단순/성능 |

### 차원별 권장

| 차원 | 권장 |
|------|------|
| 2D (지도) | R-Tree / Geohash / H3 / S2 / QuadTree |
| 3D (게임/렌더링) | BVH / Octree |
| k차원 (k ≤ 10, ML) | KD-Tree / Ball Tree |
| k차원 (k > 20, embedding) | **공간 인덱스 부적합** → ANN (HNSW, Annoy, FAISS) |

### 정적 vs 동적 데이터

| 데이터 패턴 | 권장 |
|------------|------|
| 정적 + 광선 교차 | BVH (SAH 구성) |
| 정적 + 범위 검색 | KD-Tree, BVH |
| 동적 (잦은 삽입/삭제) | R-Tree / R*-Tree |
| Append-only + 분산 | H3 / S2 / Geohash (셀 ID 만 인덱싱) |

### Geohash vs H3 vs S2 빠른 선택

```
prefix 매칭 필요? (URL, 단순 RDB)
  └─ YES → Geohash
  └─ NO ↓
hexagon 균등 분포 필요? (heatmap, 거리 분석)
  └─ YES → H3
  └─ NO ↓
1D 범위 쿼리 / B-Tree 인덱스 직접 활용?
  └─ YES → S2
```

---

## 공통 함정

### 1. 경계 효과 (Geohash, 직사각형 셀)
인접 셀의 prefix 가 다를 수 있음 — 검색 시 반드시 **8 neighbors 까지 포함**

### 2. 적도 vs 극지 (Geohash, S2 cube)
적도와 극지방의 셀 크기가 다름 — 거리 분석 시 보정 필요. H3 는 이 문제가 작지만 pentagon 셀이 있음

### 3. 좌표계 (SRID)
- WGS84 (EPSG:4326) — 위경도, GPS 표준
- Web Mercator (EPSG:3857) — Google Maps 타일
- UTM — 지역별 미터 단위

R-Tree 인덱스 생성 시 SRID 일치 필수. PostGIS `ST_DWithin` 은 `geography` 타입(미터) vs `geometry`(좌표계 단위) 구분.

### 4. 부동소수점 정밀도
- Geohash precision 12 = ±~1e-8°, double precision 한계 근처
- BVH AABB 의 좁은 슬랩에서 floating point 에러로 광선 누락 가능 — `tMin` 에 작은 양수 epsilon 더하기

### 5. 차원의 저주 (KD-Tree, BVH)
k > 20 에서 NN 검색이 brute force 와 다를 바 없어짐 → ANN(HNSW, FAISS) 대체

### 6. R-Tree 분할 휴리스틱 의존
잘못된 분할로 MBR 겹침이 누적되면 쿼리 효율 급락 → R*-Tree 의 forced reinsert 사용

### 7. 모든 인덱스는 데이터 분포에 민감
- skew → QuadTree 무한 분할
- 클러스터링 → KD-Tree 불균형
- 해법: max depth 제한, 주기적 rebuild

---

## 참고 자료

- **R-Tree 원전**: Guttman, A. (1984). *R-trees: A dynamic index structure for spatial searching*. SIGMOD '84.
- **R*-Tree 원전**: Beckmann, N., Kriegel, H. P., Schneider, R., & Seeger, B. (1990). *The R*-tree: an efficient and robust access method for points and rectangles*. SIGMOD '90.
- **KD-Tree 원전**: Bentley, J. L. (1975). *Multidimensional binary search trees used for associative searching*. Communications of the ACM.
- **QuadTree 원전**: Finkel, R. A., & Bentley, J. L. (1974). *Quad trees: A data structure for retrieval on composite keys*. Acta Informatica.
- **Hanan Samet**: *Foundations of Multidimensional and Metric Data Structures* (Morgan Kaufmann, 2006) — 공간 자료구조의 정전
- **H3 공식 문서**: https://h3geo.org/
- **S2 공식 문서**: https://s2geometry.io/
- **Geohash 사양**: https://en.wikipedia.org/wiki/Geohash
- **Embree (Intel BVH)**: https://www.embree.org/
- **NVIDIA OptiX BVH**: https://developer.nvidia.com/optix
- **PostGIS GiST**: https://postgis.net/docs/using_postgis_dbmanagement.html
- **Uber H3 blog**: https://www.uber.com/blog/h3/
