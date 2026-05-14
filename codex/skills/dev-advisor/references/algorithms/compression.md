# 압축 알고리즘 (Compression Algorithms)

데이터를 더 적은 비트로 표현하는 무손실 압축 알고리즘입니다.

> Huffman Coding은 [greedy.md](greedy.md#2-huffman-coding-허프만-코딩)에 별도 정리되어 있습니다. 본 카테고리에서는 그 외 압축 기법을 다룹니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [rle](#rle) | Run-Length Encoding (RLE) | 런 길이 부호화 | 낮음 |
| [lz77](#lz77) | LZ77 (Lempel-Ziv 1977) | 슬라이딩 윈도우 압축 | 중간 |
| [lzw](#lzw) | LZ78 / LZW | 사전 기반 압축 | 중간 |
| [arithmetic-coding](#arithmetic-coding) | Arithmetic Coding | 산술 부호화 | 높음 |
| [bwt](#bwt) | Burrows-Wheeler Transform | BWT 변환 | 높음 |

---

<a id="rle"></a>
## 1. Run-Length Encoding (RLE, 런 길이 부호화)

**목적**: 연속된 동일 값의 반복을 (값, 길이) 쌍으로 압축

**시간 복잡도**: O(n)

**공간 복잡도**: O(n) - 최악

**특징**:
- 가장 단순한 압축
- 연속 반복이 적은 데이터에서는 오히려 커짐
- 흑백 이미지, 단순 패턴에 효과적

**장점**:
- 구현 매우 간단
- 빠른 압축/해제
- 메모리 적게 사용

**단점**:
- 다양한 데이터(텍스트, 사진 등)에서는 비효율
- 반복 없으면 크기 증가

**활용 예시**:
- 팩스 (CCITT)
- BMP/TIFF 이미지
- 게임 스프라이트 압축
- 단순 로그 압축

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
fun rleEncode(input: String): String {
    if (input.isEmpty()) return ""
    val sb = StringBuilder()
    var count = 1
    for (i in 1..input.length) {
        if (i < input.length && input[i] == input[i - 1]) {
            count++
        } else {
            sb.append(input[i - 1]).append(count)
            count = 1
        }
    }
    return sb.toString()
}

fun rleDecode(encoded: String): String {
    val sb = StringBuilder()
    var i = 0
    while (i < encoded.length) {
        val ch = encoded[i]
        var j = i + 1
        while (j < encoded.length && encoded[j].isDigit()) j++
        val count = encoded.substring(i + 1, j).toInt()
        repeat(count) { sb.append(ch) }
        i = j
    }
    return sb.toString()
}

// 바이트 배열용 RLE
fun rleEncodeBytes(input: ByteArray): ByteArray {
    if (input.isEmpty()) return ByteArray(0)
    val output = mutableListOf<Byte>()
    var i = 0
    while (i < input.size) {
        val b = input[i]
        var run = 1
        while (i + run < input.size && input[i + run] == b && run < 255) run++
        output.add(run.toByte())
        output.add(b)
        i += run
    }
    return output.toByteArray()
}
```

**관련 알고리즘**: Huffman, LZ77

---

<a id="lz77"></a>
## 2. LZ77 (Lempel-Ziv 1977, 슬라이딩 윈도우)

**목적**: 슬라이딩 윈도우 내에서 반복되는 패턴을 (거리, 길이, 다음 문자) 토큰으로 치환

**시간 복잡도**: O(n * w) - w: 윈도우 크기

**공간 복잡도**: O(w)

**특징**:
- 백참조 (back-reference) 기반
- 사전(dictionary) 명시적 저장 불필요 (윈도우가 곧 사전)
- DEFLATE 알고리즘의 핵심

**장점**:
- 다양한 데이터에서 효과적
- 별도 사전 저장 불필요
- 점진적 압축 가능

**단점**:
- 윈도우 크기에 압축률 의존
- 패턴 탐색이 병목

**활용 예시**:
- gzip, zlib (DEFLATE = LZ77 + Huffman)
- PNG 이미지
- ZIP 파일
- HTTP Content-Encoding

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
data class LZ77Token(val distance: Int, val length: Int, val nextChar: Char)

fun lz77Encode(input: String, windowSize: Int = 20, lookahead: Int = 15): List<LZ77Token> {
    val tokens = mutableListOf<LZ77Token>()
    var i = 0
    while (i < input.length) {
        var bestLen = 0
        var bestDist = 0
        val windowStart = maxOf(0, i - windowSize)

        // 슬라이딩 윈도우에서 가장 긴 매칭 찾기
        for (j in windowStart until i) {
            var len = 0
            while (len < lookahead && i + len < input.length &&
                   input[j + len] == input[i + len]) {
                len++
            }
            if (len > bestLen) {
                bestLen = len
                bestDist = i - j
            }
        }

        val nextChar = if (i + bestLen < input.length) input[i + bestLen] else '\u0000'
        tokens.add(LZ77Token(bestDist, bestLen, nextChar))
        i += bestLen + 1
    }
    return tokens
}

fun lz77Decode(tokens: List<LZ77Token>): String {
    val sb = StringBuilder()
    for (t in tokens) {
        if (t.length > 0) {
            val start = sb.length - t.distance
            for (k in 0 until t.length) {
                sb.append(sb[start + k])
            }
        }
        if (t.nextChar != '\u0000') sb.append(t.nextChar)
    }
    return sb.toString()
}
```

**관련 알고리즘**: LZ78, LZSS, DEFLATE

---

<a id="lzw"></a>
## 3. LZ78 / LZW (사전 기반 압축)

**목적**: 명시적 사전을 점진적으로 구성하며 (사전 인덱스, 다음 문자) 또는 코드 출력

**시간 복잡도**: O(n)

**공간 복잡도**: O(d) - d: 사전 크기

**특징**:
- LZ78: (이전 인덱스, 다음 문자) 쌍
- LZW: 다음 문자 없이 코드만 출력 (사전 미리 초기화)
- 사전 크기 제한 시 reset 또는 LRU

**장점**:
- 사전 명시적이라 분석 용이
- 압축률 좋음
- 임의 접근 디코드 가능 (변형)

**단점**:
- 메모리 사용량
- 사전 동기화 필요 (압축/해제 양쪽)

**활용 예시**:
- GIF 이미지 (LZW)
- compress 유틸리티
- TIFF 압축
- PDF 스트림 (LZWDecode)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
fun lzwEncode(input: String): List<Int> {
    val dict = HashMap<String, Int>()
    for (i in 0..255) dict["${i.toChar()}"] = i
    var nextCode = 256

    val output = mutableListOf<Int>()
    var w = ""
    for (c in input) {
        val wc = w + c
        if (dict.containsKey(wc)) {
            w = wc
        } else {
            output.add(dict[w]!!)
            dict[wc] = nextCode++
            w = c.toString()
        }
    }
    if (w.isNotEmpty()) output.add(dict[w]!!)
    return output
}

fun lzwDecode(codes: List<Int>): String {
    val dict = HashMap<Int, String>()
    for (i in 0..255) dict[i] = "${i.toChar()}"
    var nextCode = 256

    val sb = StringBuilder()
    var prev = dict[codes[0]]!!
    sb.append(prev)

    for (k in 1 until codes.size) {
        val code = codes[k]
        val entry = when {
            dict.containsKey(code) -> dict[code]!!
            code == nextCode -> prev + prev[0]
            else -> error("Bad code $code")
        }
        sb.append(entry)
        dict[nextCode++] = prev + entry[0]
        prev = entry
    }
    return sb.toString()
}
```

**관련 알고리즘**: LZ77, Arithmetic Coding

---

<a id="arithmetic-coding"></a>
## 4. Arithmetic Coding (산술 부호화)

**목적**: 전체 메시지를 하나의 0과 1 사이 실수로 부호화. 심볼 확률에 따라 구간을 재귀 분할

**시간 복잡도**: O(n)

**공간 복잡도**: O(1) (스트리밍)

**특징**:
- Huffman의 정수 비트 제약을 넘어 fractional bit 가능
- 확률 모델과 부호화 분리
- 적응적 모델과 결합 가능

**장점**:
- 이론적 엔트로피에 매우 근접
- Huffman보다 압축률 우수
- 적응적 모델링 자연스러움

**단점**:
- 구현 복잡 (부동소수점 / 큰 정수 연산)
- 과거 특허 이슈 (현재는 만료)
- 디코딩 느림

**활용 예시**:
- JPEG2000
- H.264 / H.265 (CABAC)
- 7z, bzip2 (변형)
- PAQ 계열 압축기

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 학습용 단순 구현 (대형 메시지엔 정수 산술 + 재정규화 필요)
fun arithmeticEncode(input: String, frequencies: Map<Char, Int>): Pair<Double, Double> {
    val total = frequencies.values.sum().toDouble()
    val ranges = mutableMapOf<Char, Pair<Double, Double>>()
    var cum = 0.0
    for ((c, f) in frequencies.entries.sortedBy { it.key }) {
        val width = f / total
        ranges[c] = cum to (cum + width)
        cum += width
    }

    var low = 0.0
    var high = 1.0
    for (c in input) {
        val (lo, hi) = ranges[c] ?: error("missing $c")
        val range = high - low
        high = low + range * hi
        low = low + range * lo
    }
    return low to high
}

fun arithmeticDecode(code: Double, length: Int, frequencies: Map<Char, Int>): String {
    val total = frequencies.values.sum().toDouble()
    val ranges = mutableMapOf<Char, Pair<Double, Double>>()
    var cum = 0.0
    for ((c, f) in frequencies.entries.sortedBy { it.key }) {
        val width = f / total
        ranges[c] = cum to (cum + width)
        cum += width
    }

    val sb = StringBuilder()
    var value = code
    repeat(length) {
        val entry = ranges.entries.first { value >= it.value.first && value < it.value.second }
        val (lo, hi) = entry.value
        sb.append(entry.key)
        value = (value - lo) / (hi - lo)
    }
    return sb.toString()
}
```

**관련 알고리즘**: Huffman, Range Coding, ANS

---

<a id="bwt"></a>
## 5. Burrows-Wheeler Transform (BWT)

**목적**: 문자열을 가역 변환하여 같은 문자가 모이도록 재배열. 압축 전 단계로 사용

**시간 복잡도**: O(n²) 단순, O(n log n) 또는 O(n) 접미사 배열

**공간 복잡도**: O(n)

**특징**:
- 모든 회전 정렬 후 마지막 열 추출
- 가역 변환 (역변환 가능)
- 자체로는 압축 안 함 — RLE/Huffman/MTF와 조합

**장점**:
- 같은 문자가 모여 후속 압축 효과 극대화
- 텍스트 압축에서 매우 효과적
- bzip2의 핵심

**단점**:
- 전체 입력 필요 (블록 단위)
- 메모리 사용량
- 구현 복잡

**활용 예시**:
- bzip2 (BWT + MTF + Huffman)
- bwa, bowtie (DNA 정렬 인덱싱)
- FM-index
- 접미사 배열 응용

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
private const val BWT_SENTINEL = '\u0001'

// 정변환: 마지막 열 + 원본 행 인덱스 반환
fun bwtTransform(input: String): Pair<String, Int> {
    val s = input + BWT_SENTINEL
    val n = s.length
    val rotations = Array(n) { i -> s.substring(i) + s.substring(0, i) }
    val sorted = rotations.sortedArray()
    val last = sorted.map { it.last() }.joinToString("")
    val originalIdx = sorted.indexOf(s)
    return last to originalIdx
}

// 역변환: BWT 결과로부터 원본 복원
fun bwtInverse(last: String, originalIdx: Int): String {
    val n = last.length
    val table = Array(n) { "" }
    repeat(n) {
        for (i in 0 until n) {
            table[i] = last[i] + table[i]
        }
        table.sort()
    }
    return table[originalIdx].trimEnd(BWT_SENTINEL)
}

// Move-to-Front (BWT 후 자주 결합)
fun moveToFront(input: String, alphabet: List<Char>): List<Int> {
    val list = alphabet.toMutableList()
    val output = mutableListOf<Int>()
    for (c in input) {
        val idx = list.indexOf(c)
        output.add(idx)
        list.removeAt(idx)
        list.add(0, c)
    }
    return output
}
```

**관련 알고리즘**: Suffix Array, MTF, bzip2

---
