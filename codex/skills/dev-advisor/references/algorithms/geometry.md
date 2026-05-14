# 계산 기하 알고리즘 (Computational Geometry)

점, 선, 다각형 등의 기하 객체에 대한 연산 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [ccw](#ccw) | CCW (Counter-Clockwise) | 외적 방향 판정 | 낮음 |
| [graham-scan](#graham-scan) | Convex Hull — Graham Scan | 그레이엄 스캔 | 중간 |
| [andrew-monotone-chain](#andrew-monotone-chain) | Convex Hull — Andrew's Monotone Chain | 앤드류 단조 체인 | 중간 |
| [line-segment-intersection](#line-segment-intersection) | Line Segment Intersection | 선분 교차 판정 | 중간 |
| [sweep-line](#sweep-line) | Sweep Line | 스위프 라인 (구간 합집합 길이) | 중간 |
| [rotating-calipers](#rotating-calipers) | Rotating Calipers | 회전하는 캘리퍼스 | 높음 |
| [point-in-polygon](#point-in-polygon) | Point-in-Polygon | 다각형 내부 판정 (Ray Casting) | 중간 |

---

<a id="ccw"></a>
## 1. CCW (Counter-Clockwise, 외적 방향 판정)

**목적**: 세 점의 방향(좌회전/우회전/일직선) 판정

**시간 복잡도**: O(1)

**공간 복잡도**: O(1)

**특징**:
- 외적(cross product) 부호로 판정
- 부호 > 0: 반시계, < 0: 시계, = 0: 일직선
- 모든 기하 알고리즘의 기본 연산

**장점**:
- 매우 빠름
- 부동소수점 없이 정수 연산 가능

**단점**:
- 오버플로우 주의 (Long 권장)

**활용 예시**:
- Convex Hull, 선분 교차 판정
- 다각형 내부 판정
- 정렬 기준 (angular sort)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
data class Point(val x: Long, val y: Long)

// > 0: 반시계, < 0: 시계, == 0: 일직선
fun ccw(a: Point, b: Point, c: Point): Long {
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
}

fun orientation(a: Point, b: Point, c: Point): Int {
    val v = ccw(a, b, c)
    return when {
        v > 0 -> 1   // 반시계
        v < 0 -> -1  // 시계
        else -> 0    // 일직선
    }
}
```

**관련 알고리즘**: Convex Hull, 선분 교차

---

<a id="graham-scan"></a>
## 2. Convex Hull — Graham Scan (그레이엄 스캔)

**목적**: 점 집합의 볼록 껍질(가장 바깥 다각형) 찾기

**시간 복잡도**: O(n log n) - 정렬 포함

**공간 복잡도**: O(n)

**특징**:
- 최하단 점 기준 각도 정렬
- 스택으로 좌회전만 유지
- 시계 반대 방향 결과

**장점**:
- 안정적 O(n log n)
- 구현 직관적

**단점**:
- 정렬 비교 함수 복잡 (각도 계산)
- 동일선상 점 처리 까다로움

**활용 예시**:
- 최소 둘레 다각형
- 충돌 판정 (게임)
- 패턴 인식

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
fun grahamScan(points: List<Point>): List<Point> {
    if (points.size < 3) return points.toList()

    // 1. 최하단(y 최소, 동률 시 x 최소) 점 선택
    val pivot = points.minWith(compareBy({ it.y }, { it.x }))
    val rest = points.filter { it != pivot }

    // 2. pivot 기준 각도 + 거리로 정렬
    val sorted = rest.sortedWith(Comparator { a, b ->
        val c = ccw(pivot, a, b)
        when {
            c > 0 -> -1
            c < 0 -> 1
            else -> {
                val da = (a.x - pivot.x) * (a.x - pivot.x) + (a.y - pivot.y) * (a.y - pivot.y)
                val db = (b.x - pivot.x) * (b.x - pivot.x) + (b.y - pivot.y) * (b.y - pivot.y)
                da.compareTo(db)
            }
        }
    })

    // 3. 스택으로 좌회전만 유지
    val hull = ArrayDeque<Point>()
    hull.addLast(pivot)
    for (p in sorted) {
        while (hull.size >= 2) {
            val top = hull.removeLast()
            val nextToTop = hull.last()
            if (ccw(nextToTop, top, p) > 0) {
                hull.addLast(top)
                break
            }
        }
        hull.addLast(p)
    }
    return hull.toList()
}
```

**관련 알고리즘**: Andrew's Monotone Chain, Jarvis March

---

<a id="andrew-monotone-chain"></a>
## 3. Convex Hull — Andrew's Monotone Chain (앤드류 단조 체인)

**목적**: 볼록 껍질을 상부/하부 체인으로 나눠 구성

**시간 복잡도**: O(n log n) - 정렬 포함, 정렬 후 O(n)

**공간 복잡도**: O(n)

**특징**:
- x좌표(동률 시 y) 기준 정렬
- 하부 체인 + 상부 체인 결합
- 각도 계산 불필요

**장점**:
- Graham보다 구현 단순
- 부동소수점 회피 가능
- 수치적으로 안정적

**단점**:
- 정렬이 병목

**활용 예시**:
- 경쟁 프로그래밍 표준 구현
- GIS (지리 정보 시스템)
- 군집 경계 추출

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
fun andrewMonotoneChain(input: List<Point>): List<Point> {
    val points = input.sortedWith(compareBy({ it.x }, { it.y }))
    val n = points.size
    if (n <= 1) return points

    val hull = ArrayList<Point>(2 * n)

    // 하부 체인
    for (p in points) {
        while (hull.size >= 2 && ccw(hull[hull.size - 2], hull[hull.size - 1], p) <= 0) {
            hull.removeAt(hull.size - 1)
        }
        hull.add(p)
    }

    // 상부 체인
    val lowerSize = hull.size + 1
    for (i in n - 2 downTo 0) {
        val p = points[i]
        while (hull.size >= lowerSize && ccw(hull[hull.size - 2], hull[hull.size - 1], p) <= 0) {
            hull.removeAt(hull.size - 1)
        }
        hull.add(p)
    }

    hull.removeAt(hull.size - 1) // 마지막은 시작점과 중복
    return hull
}
```

**관련 알고리즘**: Graham Scan, QuickHull

---

<a id="line-segment-intersection"></a>
## 4. Line Segment Intersection (선분 교차 판정)

**목적**: 두 선분이 서로 교차하는지 판정

**시간 복잡도**: O(1)

**공간 복잡도**: O(1)

**특징**:
- CCW 기반 판정
- 일반 위치 + 일직선 특수 처리
- Bounding box 보조 검사

**장점**:
- 매우 빠름
- 정수 연산 가능

**단점**:
- 끝점 일치 / 일직선 케이스 신중히

**활용 예시**:
- 충돌 판정
- 다각형 단순성 검사
- 시선 차단(LOS) 판정

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
data class Segment(val p1: Point, val p2: Point)

fun onSegment(p: Point, q: Point, r: Point): Boolean {
    return q.x in minOf(p.x, r.x)..maxOf(p.x, r.x) &&
           q.y in minOf(p.y, r.y)..maxOf(p.y, r.y)
}

fun segmentsIntersect(s1: Segment, s2: Segment): Boolean {
    val o1 = orientation(s1.p1, s1.p2, s2.p1)
    val o2 = orientation(s1.p1, s1.p2, s2.p2)
    val o3 = orientation(s2.p1, s2.p2, s1.p1)
    val o4 = orientation(s2.p1, s2.p2, s1.p2)

    // 일반 케이스
    if (o1 != o2 && o3 != o4) return true

    // 일직선 + 겹침 특수 케이스
    if (o1 == 0 && onSegment(s1.p1, s2.p1, s1.p2)) return true
    if (o2 == 0 && onSegment(s1.p1, s2.p2, s1.p2)) return true
    if (o3 == 0 && onSegment(s2.p1, s1.p1, s2.p2)) return true
    if (o4 == 0 && onSegment(s2.p1, s1.p2, s2.p2)) return true

    return false
}
```

**관련 알고리즘**: Sweep Line, Bentley-Ottmann

---

<a id="sweep-line"></a>
## 5. Sweep Line (스위프 라인 — 구간 합집합 길이)

**목적**: 1D/2D 평면을 가로지르는 라인을 이동하며 이벤트 처리

**시간 복잡도**: O(n log n)

**공간 복잡도**: O(n)

**특징**:
- 이벤트(시작/종료) 정렬
- 활성 구간 셋을 자료구조로 관리
- 다양한 문제(교차, 합집합, 가장 가까운 쌍)에 응용

**장점**:
- 다양한 문제에 일반화 가능
- O(n log n) 최적

**단점**:
- 이벤트 큐 + 활성 셋 구성 복잡
- 부동소수점 이슈

**활용 예시**:
- 구간 합집합 길이
- 직사각형 합집합 면적
- 선분 교차 모두 찾기 (Bentley-Ottmann)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// 1D 구간 합집합 길이
fun unionLength(intervals: List<Pair<Long, Long>>): Long {
    if (intervals.isEmpty()) return 0L

    // 이벤트: (좌표, type) type=+1 시작, -1 종료
    val events = mutableListOf<Pair<Long, Int>>()
    for ((l, r) in intervals) {
        events.add(l to 1)
        events.add(r to -1)
    }
    events.sortWith(compareBy({ it.first }, { -it.second }))

    var total = 0L
    var active = 0
    var lastStart = 0L

    for ((coord, type) in events) {
        if (active > 0) total += coord - lastStart
        active += type
        if (active > 0) lastStart = coord
    }
    return total
}

// 직사각형 합집합 면적 (좌표 압축 + 세그먼트 트리 변형)
data class Rect(val x1: Long, val y1: Long, val x2: Long, val y2: Long)

fun rectanglesArea(rects: List<Rect>): Long {
    if (rects.isEmpty()) return 0L

    // 이벤트: (x, y1, y2, type)
    data class Event(val x: Long, val y1: Long, val y2: Long, val type: Int)

    val events = rects.flatMap {
        listOf(Event(it.x1, it.y1, it.y2, 1), Event(it.x2, it.y1, it.y2, -1))
    }.sortedBy { it.x }

    // 활성 y 구간 카운트 맵 (간단 구현 - 좌표 압축 권장)
    val activeCount = sortedMapOf<Long, Int>()
    fun activeY(): Long {
        var total = 0L
        val ys = activeCount.entries.toList()
        var open = 0
        var prevY = 0L
        for ((y, delta) in ys) {
            if (open > 0) total += y - prevY
            open += delta
            prevY = y
        }
        return total
    }

    var area = 0L
    var prevX = events[0].x
    for (e in events) {
        area += activeY() * (e.x - prevX)
        activeCount.merge(e.y1, e.type) { a, b -> a + b }
        activeCount.merge(e.y2, -e.type) { a, b -> a + b }
        prevX = e.x
    }
    return area
}
```

**관련 알고리즘**: Bentley-Ottmann, Segment Tree

---

<a id="rotating-calipers"></a>
## 6. Rotating Calipers (회전하는 캘리퍼스 — 가장 먼 두 점)

**목적**: 볼록 껍질의 가장 먼 두 점(지름) 찾기

**시간 복잡도**: O(n) - Convex Hull 계산 후

**공간 복잡도**: O(n)

**특징**:
- 볼록 껍질 정점을 순회하며 두 포인터 회전
- 외적으로 평행한 변 찾기
- 다양한 응용(최대 두께, 최소 둘러싸기 사각형)

**장점**:
- 단순 O(n²)을 O(n)으로 개선
- 우아한 알고리즘

**단점**:
- 볼록 껍질이 선행 조건
- 일직선 케이스 처리 필요

**활용 예시**:
- 점 집합의 지름(diameter)
- 최소 둘러싸기 사각형
- 폭(width) 계산

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 거리 제곱 (정수 연산)
private fun distSq(a: Point, b: Point): Long {
    val dx = a.x - b.x
    val dy = a.y - b.y
    return dx * dx + dy * dy
}

private fun cross(o: Point, a: Point, b: Point): Long {
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
}

fun farthestPair(points: List<Point>): Pair<Point, Point> {
    val hull = andrewMonotoneChain(points)
    val n = hull.size
    if (n < 2) return hull[0] to hull[0]
    if (n == 2) return hull[0] to hull[1]

    var maxDist = 0L
    var best = hull[0] to hull[1]
    var j = 1

    for (i in 0 until n) {
        val ni = (i + 1) % n
        while (true) {
            val nj = (j + 1) % n
            // 변(i, ni)에 대해 j를 더 멀리 보낼 수 있나
            val a = cross(hull[i], hull[ni], hull[nj])
            val b = cross(hull[i], hull[ni], hull[j])
            if (kotlin.math.abs(a) > kotlin.math.abs(b)) j = nj
            else break
        }
        val d = distSq(hull[i], hull[j])
        if (d > maxDist) {
            maxDist = d
            best = hull[i] to hull[j]
        }
    }
    return best
}
```

**관련 알고리즘**: Convex Hull, Closest Pair

---

<a id="point-in-polygon"></a>
## 7. Point-in-Polygon (다각형 내부 판정 — Ray Casting)

**목적**: 점이 다각형 내부에 있는지 판정

**시간 복잡도**: O(n) - n: 다각형 정점 수

**공간 복잡도**: O(1)

**특징**:
- 점에서 무한대로 수평 광선 발사
- 광선이 변과 교차하는 횟수가 홀수면 내부
- 정점/변 위 케이스 별도 처리

**장점**:
- 임의 단순 다각형 지원
- 구현 비교적 단순

**단점**:
- 광선이 정점을 정확히 지나면 모호
- 일직선 변 처리 까다로움

**활용 예시**:
- GIS 영역 포함 판정
- 게임 충돌 영역
- 마우스 클릭 영역 판정

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
fun pointInPolygon(p: Point, polygon: List<Point>): Boolean {
    val n = polygon.size
    var inside = false
    var j = n - 1

    for (i in 0 until n) {
        val a = polygon[i]
        val b = polygon[j]
        // 점이 정확히 변 위에 있는지 (선택적)
        if (orientation(a, b, p) == 0 &&
            p.x in minOf(a.x, b.x)..maxOf(a.x, b.x) &&
            p.y in minOf(a.y, b.y)..maxOf(a.y, b.y)) {
            return true // 경계도 내부로 간주
        }
        val cond = (a.y > p.y) != (b.y > p.y)
        if (cond) {
            // 정수 오버플로우 회피를 위해 교차 x 계산을 비교 형태로
            // x_intersect = a.x + (p.y - a.y) * (b.x - a.x) / (b.y - a.y)
            val lhs = (p.x - a.x) * (b.y - a.y)
            val rhs = (b.x - a.x) * (p.y - a.y)
            if ((b.y - a.y > 0 && lhs < rhs) || (b.y - a.y < 0 && lhs > rhs)) {
                inside = !inside
            }
        }
        j = i
    }
    return inside
}

// 부호 있는 면적 (Shoelace) — 다각형 방향 + 면적
fun signedArea(polygon: List<Point>): Double {
    val n = polygon.size
    var s = 0L
    for (i in 0 until n) {
        val a = polygon[i]
        val b = polygon[(i + 1) % n]
        s += a.x * b.y - b.x * a.y
    }
    return s / 2.0
}
```

**관련 알고리즘**: Winding Number, Shoelace Formula

---
