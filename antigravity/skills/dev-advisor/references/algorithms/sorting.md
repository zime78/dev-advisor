# 정렬 알고리즘 (Sorting Algorithms)

배열이나 리스트의 요소들을 특정 순서로 정렬하는 알고리즘입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [bubble-sort](#bubble-sort) | Bubble Sort | 버블 정렬 | 낮음 |
| [selection-sort](#selection-sort) | Selection Sort | 선택 정렬 | 낮음 |
| [insertion-sort](#insertion-sort) | Insertion Sort | 삽입 정렬 | 낮음 |
| [merge-sort](#merge-sort) | Merge Sort | 병합 정렬 | 중간 |
| [quick-sort](#quick-sort) | Quick Sort | 퀵 정렬 | 중간 |
| [heap-sort](#heap-sort) | Heap Sort | 힙 정렬 | 중간 |
| [counting-sort](#counting-sort) | Counting Sort | 계수 정렬 | 낮음 |
| [radix-sort](#radix-sort) | Radix Sort | 기수 정렬 | 중간 |
| [bucket-sort](#bucket-sort) | Bucket Sort | 버킷 정렬 | 중간 |
| [shell-sort](#shell-sort) | Shell Sort | 셸 정렬 | 중간 |
| [tim-sort](#tim-sort) | Tim Sort | 팀 정렬 | 높음 |
| [intro-sort](#intro-sort) | Intro Sort | 인트로 정렬 | 높음 |
| [tree-sort](#tree-sort) | Tree Sort | 트리 정렬 | 중간 |
| [external-merge-sort](#external-merge-sort) | External Merge Sort | 외부 병합 정렬 | 높음 |
| [pancake-sort](#pancake-sort) | Pancake Sort | 팬케이크 정렬 | 낮음 |
| [cycle-sort](#cycle-sort) | Cycle Sort | 사이클 정렬 | 중간 |

---

<a id="bubble-sort"></a>
## 1. Bubble Sort (버블 정렬)

**목적**: 인접한 두 요소를 비교하여 정렬

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n) | O(n²) | O(n²) |

**공간 복잡도**: O(1)

**특징**:
- 제자리 정렬 (In-place)
- 안정 정렬 (Stable)
- 구현이 매우 단순

**장점**:
- 구현이 간단
- 이미 정렬된 경우 O(n)

**단점**:
- 대규모 데이터에서 비효율적
- 평균/최악 O(n²)

**활용 예시**:
- 교육용 목적
- 거의 정렬된 소규모 데이터

**난이도**: 낮음 | **사용 빈도**: ★☆☆☆☆

**Kotlin 코드**:
```kotlin
fun bubbleSort(arr: IntArray) {
    val n = arr.size
    for (i in 0 until n - 1) {
        var swapped = false
        for (j in 0 until n - i - 1) {
            if (arr[j] > arr[j + 1]) {
                arr[j] = arr[j + 1].also { arr[j + 1] = arr[j] }
                swapped = true
            }
        }
        if (!swapped) break // 최적화: 교환 없으면 종료
    }
}
```

**관련 알고리즘**: Selection Sort, Insertion Sort

---

<a id="selection-sort"></a>
## 2. Selection Sort (선택 정렬)

**목적**: 최소값을 찾아 맨 앞과 교환

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n²) | O(n²) | O(n²) |

**공간 복잡도**: O(1)

**특징**:
- 제자리 정렬
- 불안정 정렬 (Unstable)
- 비교 횟수 고정

**장점**:
- 구현이 간단
- 메모리 사용 최소

**단점**:
- 항상 O(n²)
- 불안정 정렬

**활용 예시**:
- 교환 비용이 높은 경우 (교환 횟수 최소)
- 소규모 데이터

**난이도**: 낮음 | **사용 빈도**: ★☆☆☆☆

**Kotlin 코드**:
```kotlin
fun selectionSort(arr: IntArray) {
    val n = arr.size
    for (i in 0 until n - 1) {
        var minIdx = i
        for (j in i + 1 until n) {
            if (arr[j] < arr[minIdx]) {
                minIdx = j
            }
        }
        arr[i] = arr[minIdx].also { arr[minIdx] = arr[i] }
    }
}
```

**관련 알고리즘**: Bubble Sort, Heap Sort

---

<a id="insertion-sort"></a>
## 3. Insertion Sort (삽입 정렬)

**목적**: 정렬된 부분에 새 요소를 올바른 위치에 삽입

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n) | O(n²) | O(n²) |

**공간 복잡도**: O(1)

**특징**:
- 제자리 정렬
- 안정 정렬
- 거의 정렬된 데이터에 효율적

**장점**:
- 구현이 간단
- 거의 정렬된 경우 O(n)
- 온라인 알고리즘 (데이터가 들어올 때마다 정렬 가능)

**단점**:
- 대규모 데이터에서 비효율적

**활용 예시**:
- 거의 정렬된 데이터
- 소규모 데이터
- Tim Sort의 부분 알고리즘

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
fun insertionSort(arr: IntArray) {
    for (i in 1 until arr.size) {
        val key = arr[i]
        var j = i - 1
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j]
            j--
        }
        arr[j + 1] = key
    }
}
```

**관련 알고리즘**: Shell Sort, Tim Sort

---

<a id="merge-sort"></a>
## 4. Merge Sort (병합 정렬)

**목적**: 분할 정복으로 배열을 반으로 나누고 병합하며 정렬

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n log n) | O(n log n) | O(n log n) |

**공간 복잡도**: O(n)

**특징**:
- 분할 정복 알고리즘
- 안정 정렬
- 항상 O(n log n) 보장

**장점**:
- 최악의 경우에도 O(n log n)
- 안정 정렬
- 연결 리스트 정렬에 적합

**단점**:
- O(n) 추가 메모리 필요
- 작은 배열에서는 오버헤드

**활용 예시**:
- 대규모 데이터 정렬
- 연결 리스트 정렬
- 외부 정렬 (External Sort)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
fun mergeSort(arr: IntArray, left: Int = 0, right: Int = arr.size - 1) {
    if (left < right) {
        val mid = (left + right) / 2
        mergeSort(arr, left, mid)
        mergeSort(arr, mid + 1, right)
        merge(arr, left, mid, right)
    }
}

fun merge(arr: IntArray, left: Int, mid: Int, right: Int) {
    val leftArr = arr.copyOfRange(left, mid + 1)
    val rightArr = arr.copyOfRange(mid + 1, right + 1)

    var i = 0; var j = 0; var k = left
    while (i < leftArr.size && j < rightArr.size) {
        arr[k++] = if (leftArr[i] <= rightArr[j]) leftArr[i++] else rightArr[j++]
    }
    while (i < leftArr.size) arr[k++] = leftArr[i++]
    while (j < rightArr.size) arr[k++] = rightArr[j++]
}
```

**관련 알고리즘**: Quick Sort, Tim Sort

---

<a id="quick-sort"></a>
## 5. Quick Sort (퀵 정렬)

**목적**: 피벗을 기준으로 분할하여 정렬

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n log n) | O(n log n) | O(n²) |

**공간 복잡도**: O(log n)

**특징**:
- 분할 정복 알고리즘
- 불안정 정렬
- 제자리 정렬 (추가 메모리 최소)

**장점**:
- 평균적으로 가장 빠름
- 캐시 효율이 좋음
- 제자리 정렬

**단점**:
- 최악의 경우 O(n²)
- 불안정 정렬
- 피벗 선택에 민감

**활용 예시**:
- 일반적인 정렬
- 시스템 정렬 함수의 기반

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
fun quickSort(arr: IntArray, low: Int = 0, high: Int = arr.size - 1) {
    if (low < high) {
        val pivotIdx = partition(arr, low, high)
        quickSort(arr, low, pivotIdx - 1)
        quickSort(arr, pivotIdx + 1, high)
    }
}

fun partition(arr: IntArray, low: Int, high: Int): Int {
    val pivot = arr[high]
    var i = low - 1
    for (j in low until high) {
        if (arr[j] < pivot) {
            i++
            arr[i] = arr[j].also { arr[j] = arr[i] }
        }
    }
    arr[i + 1] = arr[high].also { arr[high] = arr[i + 1] }
    return i + 1
}
```

**관련 알고리즘**: Merge Sort, Intro Sort

---

<a id="heap-sort"></a>
## 6. Heap Sort (힙 정렬)

**목적**: 힙 자료구조를 이용한 정렬

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n log n) | O(n log n) | O(n log n) |

**공간 복잡도**: O(1)

**특징**:
- 제자리 정렬
- 불안정 정렬
- 최악의 경우에도 O(n log n) 보장

**장점**:
- 최악의 경우 O(n log n)
- 제자리 정렬
- 우선순위 큐와 연관

**단점**:
- 캐시 효율이 낮음
- 불안정 정렬
- Quick Sort보다 느림

**활용 예시**:
- 최악 성능 보장이 필요할 때
- 우선순위 큐 구현
- K번째 큰/작은 요소 찾기

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
fun heapSort(arr: IntArray) {
    val n = arr.size

    // Build max heap
    for (i in n / 2 - 1 downTo 0) {
        heapify(arr, n, i)
    }

    // Extract elements from heap
    for (i in n - 1 downTo 1) {
        arr[0] = arr[i].also { arr[i] = arr[0] }
        heapify(arr, i, 0)
    }
}

fun heapify(arr: IntArray, n: Int, i: Int) {
    var largest = i
    val left = 2 * i + 1
    val right = 2 * i + 2

    if (left < n && arr[left] > arr[largest]) largest = left
    if (right < n && arr[right] > arr[largest]) largest = right

    if (largest != i) {
        arr[i] = arr[largest].also { arr[largest] = arr[i] }
        heapify(arr, n, largest)
    }
}
```

**관련 알고리즘**: Selection Sort, Priority Queue

---

<a id="counting-sort"></a>
## 7. Counting Sort (계수 정렬)

**목적**: 각 요소의 개수를 세어 정렬

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n+k) | O(n+k) | O(n+k) |

**공간 복잡도**: O(k) (k = 값의 범위)

**특징**:
- 비교 기반이 아닌 정렬
- 안정 정렬
- 정수 또는 제한된 범위의 값에만 적용

**장점**:
- 범위가 작으면 O(n)
- 안정 정렬

**단점**:
- 범위가 크면 메모리 낭비
- 정수만 가능

**활용 예시**:
- 정수 범위가 작은 경우 (나이, 점수)
- Radix Sort의 부분 알고리즘

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
fun countingSort(arr: IntArray): IntArray {
    if (arr.isEmpty()) return arr

    val max = arr.maxOrNull()!!
    val min = arr.minOrNull()!!
    val range = max - min + 1

    val count = IntArray(range)
    val output = IntArray(arr.size)

    // Count occurrences
    for (num in arr) count[num - min]++

    // Cumulative count
    for (i in 1 until range) count[i] += count[i - 1]

    // Build output array
    for (i in arr.size - 1 downTo 0) {
        output[count[arr[i] - min] - 1] = arr[i]
        count[arr[i] - min]--
    }

    return output
}
```

**관련 알고리즘**: Radix Sort, Bucket Sort

---

<a id="radix-sort"></a>
## 8. Radix Sort (기수 정렬)

**목적**: 자릿수별로 정렬 반복

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(d(n+k)) | O(d(n+k)) | O(d(n+k)) |

**공간 복잡도**: O(n+k)

**특징**:
- 비교 기반이 아닌 정렬
- 안정 정렬
- 자릿수(d)만큼 반복

**장점**:
- 자릿수가 적으면 매우 빠름
- 안정 정렬

**단점**:
- 자릿수가 많으면 비효율적
- 추가 메모리 필요

**활용 예시**:
- 고정 길이 정수/문자열
- 전화번호, 우편번호 정렬

**난이도**: 중간 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
fun radixSort(arr: IntArray) {
    val max = arr.maxOrNull() ?: return
    var exp = 1

    while (max / exp > 0) {
        countingSortByDigit(arr, exp)
        exp *= 10
    }
}

fun countingSortByDigit(arr: IntArray, exp: Int) {
    val n = arr.size
    val output = IntArray(n)
    val count = IntArray(10)

    for (num in arr) count[(num / exp) % 10]++
    for (i in 1 until 10) count[i] += count[i - 1]

    for (i in n - 1 downTo 0) {
        val digit = (arr[i] / exp) % 10
        output[count[digit] - 1] = arr[i]
        count[digit]--
    }

    for (i in 0 until n) arr[i] = output[i]
}
```

**관련 알고리즘**: Counting Sort, Bucket Sort

---

<a id="bucket-sort"></a>
## 9. Bucket Sort (버킷 정렬)

**목적**: 요소를 버킷에 분배 후 각 버킷 정렬

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n+k) | O(n+k) | O(n²) |

**공간 복잡도**: O(n+k)

**특징**:
- 분산 정렬 알고리즘
- 균등 분포에 효과적
- 버킷 내부 정렬 필요

**장점**:
- 균등 분포 시 O(n)
- 병렬화 가능

**단점**:
- 불균등 분포 시 비효율적
- 추가 메모리 필요

**활용 예시**:
- 균등 분포된 실수
- 외부 정렬

**난이도**: 중간 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
fun bucketSort(arr: FloatArray) {
    val n = arr.size
    if (n <= 0) return

    val buckets = Array(n) { mutableListOf<Float>() }

    // Put elements into buckets
    for (num in arr) {
        val idx = (n * num).toInt().coerceIn(0, n - 1)
        buckets[idx].add(num)
    }

    // Sort individual buckets
    for (bucket in buckets) bucket.sort()

    // Concatenate buckets
    var idx = 0
    for (bucket in buckets) {
        for (num in bucket) {
            arr[idx++] = num
        }
    }
}
```

**관련 알고리즘**: Counting Sort, Radix Sort

---

<a id="shell-sort"></a>
## 10. Shell Sort (셸 정렬)

**목적**: 간격(gap)을 두고 삽입 정렬 반복

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n log n) | O(n^1.5) | O(n²) |

**공간 복잡도**: O(1)

**특징**:
- 삽입 정렬의 개선판
- 제자리 정렬
- Gap sequence에 따라 성능 변화

**장점**:
- Insertion Sort보다 빠름
- 제자리 정렬
- 구현이 비교적 간단

**단점**:
- Gap sequence 선택이 중요
- 최적 성능 증명 어려움

**활용 예시**:
- 중간 크기 데이터
- 임베디드 시스템

**난이도**: 중간 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
fun shellSort(arr: IntArray) {
    var gap = arr.size / 2

    while (gap > 0) {
        for (i in gap until arr.size) {
            val temp = arr[i]
            var j = i
            while (j >= gap && arr[j - gap] > temp) {
                arr[j] = arr[j - gap]
                j -= gap
            }
            arr[j] = temp
        }
        gap /= 2
    }
}
```

**관련 알고리즘**: Insertion Sort

---

<a id="tim-sort"></a>
## 11. Tim Sort (팀 정렬)

**목적**: Merge Sort + Insertion Sort 하이브리드

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n) | O(n log n) | O(n log n) |

**공간 복잡도**: O(n)

**특징**:
- 하이브리드 정렬
- 안정 정렬
- 실제 데이터에 최적화

**장점**:
- 실제 데이터 패턴에 효율적
- 안정 정렬
- 최악에도 O(n log n)

**단점**:
- 구현 복잡
- 추가 메모리 필요

**활용 예시**:
- Python, Java의 기본 정렬
- 실제 프로덕션 환경

**난이도**: 높음 | **사용 빈도**: ★★★★★

**관련 알고리즘**: Merge Sort, Insertion Sort

---

<a id="intro-sort"></a>
## 12. Intro Sort (인트로 정렬)

**목적**: Quick Sort + Heap Sort + Insertion Sort 하이브리드

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n log n) | O(n log n) | O(n log n) |

**공간 복잡도**: O(log n)

**특징**:
- 하이브리드 정렬
- Quick Sort의 최악 케이스 방지
- C++ STL sort의 기반

**장점**:
- 최악에도 O(n log n) 보장
- 실용적 성능

**단점**:
- 불안정 정렬
- 구현 복잡

**활용 예시**:
- C++ STL sort()
- 성능 보장이 필요한 경우

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**관련 알고리즘**: Quick Sort, Heap Sort, Insertion Sort

---

<a id="tree-sort"></a>
## 13. Tree Sort (트리 정렬)

**목적**: BST에 삽입 후 중위 순회로 정렬

**시간 복잡도**:
| 최선 | 평균 | 최악 |
|------|------|------|
| O(n log n) | O(n log n) | O(n²) |

**공간 복잡도**: O(n)

**특징**:
- BST 기반 정렬
- 균형 트리 사용 시 O(n log n) 보장
- 온라인 정렬 가능

**장점**:
- 동적 데이터에 유용
- 중복 처리 용이

**단점**:
- 추가 메모리 필요
- 불균형 시 O(n²)

**활용 예시**:
- 동적 데이터 정렬
- BST 학습용

**난이도**: 중간 | **사용 빈도**: ★☆☆☆☆

**관련 알고리즘**: Heap Sort, BST

---

<a id="external-merge-sort"></a>
## 14. External Merge Sort (외부 병합 정렬)

**목적**: 메모리에 모두 올릴 수 없는 대용량 데이터를 디스크 기반으로 정렬

**시간 복잡도**: O(n log n) - 디스크 I/O 단위

**공간 복잡도**: O(M) 메모리 + O(n) 디스크

**특징**:
- Phase 1: 메모리 가득 채워 정렬하고 임시 파일(run)로 출력
- Phase 2: k-way 병합으로 run들을 점진적으로 합침
- 우선순위 큐로 k-way 병합 수행
- replacement selection으로 run 길이 2배 증가 가능

**장점**:
- 메모리 한계 초과 데이터 처리
- 디스크 시퀀셜 I/O 활용
- 분산 가능

**단점**:
- 디스크 I/O 비용
- 다중 패스 (메모리 작을수록 많아짐)
- 구현 복잡

**활용 예시**:
- 데이터베이스 ORDER BY (대용량)
- Hadoop/Spark 셔플
- 로그 정렬
- 외부 정렬 라이브러리

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.File
import java.util.PriorityQueue

object ExternalMergeSort {
    fun sortFile(input: File, output: File, chunkSize: Int) {
        // Phase 1: 청크 단위로 정렬해 run 파일 생성
        val runs = mutableListOf<File>()
        input.bufferedReader().use { reader ->
            val buffer = mutableListOf<Long>()
            var line = reader.readLine()
            while (line != null) {
                buffer.add(line.toLong())
                if (buffer.size >= chunkSize) {
                    runs.add(writeRun(buffer))
                    buffer.clear()
                }
                line = reader.readLine()
            }
            if (buffer.isNotEmpty()) runs.add(writeRun(buffer))
        }

        // Phase 2: k-way 병합
        kWayMerge(runs, output)
        runs.forEach { it.delete() }
    }

    private fun writeRun(buffer: MutableList<Long>): File {
        buffer.sort()
        val tmp = File.createTempFile("run", ".tmp")
        tmp.bufferedWriter().use { w ->
            for (v in buffer) { w.write(v.toString()); w.newLine() }
        }
        return tmp
    }

    private fun kWayMerge(runs: List<File>, output: File) {
        val readers = runs.map { it.bufferedReader() }
        val pq = PriorityQueue<Pair<Long, Int>>(compareBy { it.first })
        for ((i, r) in readers.withIndex()) {
            r.readLine()?.toLongOrNull()?.let { pq.add(it to i) }
        }
        output.bufferedWriter().use { w ->
            while (pq.isNotEmpty()) {
                val (v, i) = pq.poll()
                w.write(v.toString()); w.newLine()
                readers[i].readLine()?.toLongOrNull()?.let { pq.add(it to i) }
            }
        }
        readers.forEach { it.close() }
    }
}
```

**관련 알고리즘**: Merge Sort, Polyphase Merge, Replacement Selection

---

<a id="pancake-sort"></a>
## 15. Pancake Sort (팬케이크 정렬)

**목적**: 접두사 뒤집기(flip)만으로 정렬. 매 단계 최대값을 끝으로 보냄

**시간 복잡도**: O(n²) - 비교 횟수 O(n²), flip 수 ≤ 2n

**공간 복잡도**: O(1)

**특징**:
- 두 가지 연산: 최대 인덱스 찾기 + 접두사 뒤집기
- Selection Sort의 변형
- 이론적 흥미 (Bill Gates의 학부 논문)

**장점**:
- 단일 연산(flip)만 사용
- 제자리 정렬

**단점**:
- 비효율적 (O(n²))
- 실용성 낮음

**활용 예시**:
- 알고리즘 학습
- 이론적 연구 (네트워크 라우팅)
- 일부 하드웨어 정렬

**난이도**: 낮음 | **사용 빈도**: ★☆☆☆☆

**Kotlin 코드**:
```kotlin
fun pancakeSort(arr: IntArray) {
    val n = arr.size
    for (size in n downTo 2) {
        // 최대값 인덱스 찾기 (0..size-1)
        var maxIdx = 0
        for (i in 1 until size) {
            if (arr[i] > arr[maxIdx]) maxIdx = i
        }
        if (maxIdx == size - 1) continue
        // 최대값을 맨 앞으로 (필요 시)
        if (maxIdx != 0) flip(arr, maxIdx)
        // 맨 앞부터 size-1까지 뒤집어 끝에 안착
        flip(arr, size - 1)
    }
}

private fun flip(arr: IntArray, k: Int) {
    var l = 0; var r = k
    while (l < r) {
        val t = arr[l]; arr[l] = arr[r]; arr[r] = t
        l++; r--
    }
}
```

**관련 알고리즘**: Selection Sort, Reversal Sort

---

<a id="cycle-sort"></a>
## 16. Cycle Sort (사이클 정렬)

**목적**: 각 원소를 정확히 한 번씩만 이동시키며 정렬. 쓰기 횟수 최소화

**시간 복잡도**: O(n²)

**공간 복잡도**: O(1)

**특징**:
- 제자리 정렬
- 불안정 정렬
- 쓰기 횟수가 n - cycle 수
- 사이클 구조 활용

**장점**:
- 메모리 쓰기 최소 (EEPROM/플래시 메모리 친화)
- 제자리 정렬

**단점**:
- O(n²) 시간
- 동일 값 처리 신중

**활용 예시**:
- EEPROM/플래시 정렬 (쓰기 수명 보존)
- 영구 저장소 최소 갱신
- 알고리즘 교육

**난이도**: 중간 | **사용 빈도**: ★☆☆☆☆

**Kotlin 코드**:
```kotlin
fun cycleSort(arr: IntArray) {
    val n = arr.size
    for (cycleStart in 0 until n - 1) {
        var item = arr[cycleStart]

        // 들어갈 위치 찾기
        var pos = cycleStart
        for (i in cycleStart + 1 until n) {
            if (arr[i] < item) pos++
        }
        if (pos == cycleStart) continue

        // 중복 처리: 같은 값이면 한 칸 이동
        while (item == arr[pos]) pos++

        // 교환
        run { val t = arr[pos]; arr[pos] = item; item = t }

        // 사이클 마무리
        while (pos != cycleStart) {
            pos = cycleStart
            for (i in cycleStart + 1 until n) {
                if (arr[i] < item) pos++
            }
            while (item == arr[pos]) pos++
            run { val t = arr[pos]; arr[pos] = item; item = t }
        }
    }
}
```

**관련 알고리즘**: Selection Sort, Permutation Cycles
