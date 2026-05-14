# 파싱 / 컴파일러 알고리즘 (Parsing & Compiler Algorithms)

문자열·토큰 스트림을 구조화된 표현(AST, IR)으로 변환하는 알고리즘입니다. 인터프리터·컴파일러·DSL·쿼리 엔진 구현 학습용 의사코드 + 핵심 타입 참조입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [lexing](#lexing) | Lexing / Tokenization | 어휘 분석 | 낮음 |
| [ll-k](#ll-k) | LL(k) Parsing | 상향-예측 파서 | 중간 |
| [lr-1](#lr-1) | LR(1) Parsing | 하향-표준 파서 | 높음 |
| [lalr](#lalr) | LALR Parsing | Look-Ahead LR | 높음 |
| [earley](#earley) | Earley Parser | 얼리 파서 | 높음 |
| [pratt](#pratt) | Pratt Parser | 프랫 파서 | 중간 |
| [peg](#peg) | PEG / Packrat | 파싱 표현 문법 | 중간 |
| [ast-traversal](#ast-traversal) | AST Traversal | AST 순회 | 낮음 |
| [ssa](#ssa) | SSA Form | 정적 단일 대입 | 높음 |
| [register-allocation](#register-allocation) | Register Allocation | 레지스터 할당 | 높음 |

---

<a id="lexing"></a>
## 1. Lexing / Tokenization (어휘 분석)

**목적**: 입력 문자열을 의미 단위(토큰)의 시퀀스로 분리

**시간 복잡도**: O(n) — 입력 길이

**공간 복잡도**: O(t) — 토큰 수

**특징**:
- DFA(결정론적 유한 오토마톤) 기반으로 구현
- 정규 표현식을 NFA → DFA 로 변환하여 테이블 생성
- 최장 일치(maximal munch) 원칙 적용
- 라인·컬럼 위치를 토큰에 부착해 오류 메시지에 활용

**장점**:
- 선형 시간 보장
- 단순하고 테스트하기 쉬움
- 컴파일러 프론트엔드의 첫 단계로 분리 명확

**단점**:
- 문맥 의존 토큰(예: Python 들여쓰기)은 추가 로직 필요
- 중첩 구조(문자열 안 문자열)는 DFA로 처리 불가

**활용 예시**:
- 모든 컴파일러/인터프리터 프론트엔드
- JSON/YAML/TOML 파서
- SQL 파서, 템플릿 엔진
- 로그 분석 파이프라인

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 토큰 타입 정의
enum class TokenType {
    NUMBER, IDENT, PLUS, MINUS, STAR, SLASH,
    LPAREN, RPAREN, EOF, UNKNOWN
}

data class Token(val type: TokenType, val lexeme: String, val line: Int, val col: Int)

class Lexer(private val source: String) {
    private var pos = 0
    private var line = 1
    private var col = 1

    fun tokenize(): List<Token> {
        val tokens = mutableListOf<Token>()
        while (pos < source.length) {
            skipWhitespace()
            if (pos >= source.length) break
            tokens += nextToken()
        }
        tokens += Token(TokenType.EOF, "", line, col)
        return tokens
    }

    private fun nextToken(): Token {
        val startCol = col
        return when (val c = advance()) {
            '+' -> Token(TokenType.PLUS, "+", line, startCol)
            '-' -> Token(TokenType.MINUS, "-", line, startCol)
            '*' -> Token(TokenType.STAR, "*", line, startCol)
            '/' -> Token(TokenType.SLASH, "/", line, startCol)
            '(' -> Token(TokenType.LPAREN, "(", line, startCol)
            ')' -> Token(TokenType.RPAREN, ")", line, startCol)
            in '0'..'9' -> readNumber(c, startCol)
            in 'a'..'z', in 'A'..'Z', '_' -> readIdent(c, startCol)
            else -> Token(TokenType.UNKNOWN, c.toString(), line, startCol)
        }
    }

    private fun readNumber(first: Char, startCol: Int): Token {
        val sb = StringBuilder(first.toString())
        while (pos < source.length && source[pos].isDigit()) sb.append(advance())
        return Token(TokenType.NUMBER, sb.toString(), line, startCol)
    }

    private fun readIdent(first: Char, startCol: Int): Token {
        val sb = StringBuilder(first.toString())
        while (pos < source.length && (source[pos].isLetterOrDigit() || source[pos] == '_')) sb.append(advance())
        return Token(TokenType.IDENT, sb.toString(), line, startCol)
    }

    private fun advance(): Char = source[pos++].also { if (it == '\n') { line++; col = 1 } else col++ }
    private fun skipWhitespace() { while (pos < source.length && source[pos].isWhitespace()) advance() }
}
```

**관련 알고리즘**: LL(k), LR(1), Pratt Parser

---

<a id="ll-k"></a>
## 2. LL(k) Parsing (상향-예측 파서)

**목적**: 입력을 왼쪽에서 오른쪽으로 읽고(Left-to-right), 좌단 유도(Leftmost derivation)로 k개 lookahead를 사용해 파스

**시간 복잡도**: O(n) — LL(1) 기준, k가 커지면 상수 배수 증가

**공간 복잡도**: O(d) — 재귀 깊이(파스 트리 깊이)

**특징**:
- FIRST / FOLLOW 집합으로 예측 테이블 구성
- 재귀 하강(recursive descent) 구현이 직관적
- 좌재귀(left recursion) 문법 직접 처리 불가 → 제거 필요
- LL(1)으로 처리 가능한 문법이 대부분의 프로그래밍 언어에 충분

**장점**:
- 손으로 쉽게 구현 가능(재귀 하강)
- 오류 메시지 품질이 높음
- 트리 구조가 명확

**단점**:
- 좌재귀·모호한 문법 처리 불가
- 예측 테이블 충돌 시 문법 재작성 필요

**활용 예시**:
- 대부분의 수동 작성 파서 (Go, Rust 컴파일러)
- 계산기, DSL 인터프리터
- 설정 파일 파서

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 간단한 수식 문법: expr → term (('+' | '-') term)*
// term → factor (('*' | '/') factor)*
// factor → NUMBER | '(' expr ')'
class LLParser(private val tokens: List<Token>) {
    private var pos = 0
    private fun peek() = tokens[pos]
    private fun consume(type: TokenType) = tokens[pos++].also {
        require(it.type == type) { "Expected $type at ${it.line}:${it.col}, got ${it.type}" }
    }

    fun parseExpr(): Int {
        var result = parseTerm()
        while (peek().type in listOf(TokenType.PLUS, TokenType.MINUS)) {
            val op = tokens[pos++].type
            val right = parseTerm()
            result = if (op == TokenType.PLUS) result + right else result - right
        }
        return result
    }

    private fun parseTerm(): Int {
        var result = parseFactor()
        while (peek().type in listOf(TokenType.STAR, TokenType.SLASH)) {
            val op = tokens[pos++].type
            val right = parseFactor()
            result = if (op == TokenType.STAR) result * right else result / right
        }
        return result
    }

    private fun parseFactor(): Int = when (peek().type) {
        TokenType.NUMBER -> consume(TokenType.NUMBER).lexeme.toInt()
        TokenType.LPAREN -> { consume(TokenType.LPAREN); parseExpr().also { consume(TokenType.RPAREN) } }
        else -> error("Unexpected token: ${peek()}")
    }
}
```

**관련 알고리즘**: Lexing, LR(1), Pratt Parser

---

<a id="lr-1"></a>
## 3. LR(1) Parsing (하향-표준 파서)

**목적**: 입력을 왼쪽에서 오른쪽으로 읽고, 우단 유도(Rightmost derivation)를 역순으로 구성. 1개 lookahead로 모든 LR(1) 문법 처리

**시간 복잡도**: O(n) — 테이블 기반

**공간 복잡도**: O(states × symbols) — 파싱 테이블 크기

**특징**:
- Shift / Reduce / Accept / Error 4가지 액션
- 아이템 집합(item sets)으로 상태 구성
- 스택 + 입력 + 테이블로 동작
- LR(0) < SLR < LALR < LR(1) 순으로 처리 가능한 문법 확장

**장점**:
- 모든 LR(1) 문법(대부분의 프로그래밍 언어) 처리 가능
- 결정론적, 선형 시간
- 오류 복구 지점 명확

**단점**:
- 테이블 크기가 매우 클 수 있음 (상태 수 폭발)
- 손으로 구현하기 어려움 → 도구 사용
- 오류 메시지 품질이 LL보다 낮을 수 있음

**활용 예시**:
- bison/flex 기반 언어 구현
- GCC (역사적으로 LR 기반)
- SQL 파서 (PostgreSQL)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// LR 파서 핵심 데이터 구조 (의사코드 수준)
sealed class LRAction {
    data class Shift(val nextState: Int) : LRAction()
    data class Reduce(val production: Int, val len: Int, val nonTerminal: String) : LRAction()
    object Accept : LRAction()
    object Error : LRAction()
}

class LRParser(
    private val actionTable: Map<Pair<Int, String>, LRAction>,
    private val gotoTable: Map<Pair<Int, String>, Int>
) {
    fun parse(tokens: List<Token>): Boolean {
        val stack = ArrayDeque<Int>()
        stack.addLast(0)
        var pos = 0

        while (true) {
            val state = stack.last()
            val lookahead = tokens.getOrNull(pos)?.lexeme ?: "\$"
            when (val action = actionTable[Pair(state, lookahead)] ?: LRAction.Error) {
                is LRAction.Shift -> { stack.addLast(action.nextState); pos++ }
                is LRAction.Reduce -> {
                    repeat(action.len) { stack.removeLast() }
                    val topState = stack.last()
                    stack.addLast(gotoTable[Pair(topState, action.nonTerminal)]
                        ?: error("GOTO 오류: state=$topState, nt=${action.nonTerminal}"))
                }
                LRAction.Accept -> return true
                LRAction.Error -> error("파싱 오류: state=$state, lookahead=$lookahead")
            }
        }
    }
}
// 실제 구현에서는 bison/yacc/ANTLR 등 도구로 actionTable/gotoTable 자동 생성
```

**관련 알고리즘**: LALR, LL(k), Earley

---

<a id="lalr"></a>
## 4. LALR Parsing (Look-Ahead LR)

**목적**: LR(1) 상태를 병합해 테이블 크기를 줄이면서도 대부분의 프로그래밍 언어 문법 처리

**시간 복잡도**: O(n) — 테이블 기반

**공간 복잡도**: O(states × symbols) — LR(1)보다 상태 수가 크게 줄어듦

**특징**:
- 코어가 같은 LR(1) 상태를 합쳐 상태 수 감소
- 병합 과정에서 reduce/reduce 충돌 발생 가능
- yacc / bison 의 기본 알고리즘
- 대부분의 산업용 파서 생성기가 LALR 사용

**장점**:
- LR(1)과 동등한 문법 처리력 (충돌 없는 경우)
- 테이블 크기 LR(1)의 수십~수백분의 1
- 도구(yacc, bison, ANTLR) 지원 완비

**단점**:
- 소수 문법에서 reduce/reduce 충돌
- LR(1) 충돌 없는 문법이 LALR에서 충돌 발생 가능
- 오류 진단 메시지 품질 낮음

**활용 예시**:
- yacc, GNU bison 기반 C/C++ 문법
- Ruby MRI 파서 (parse.y)
- PHP 파서
- 다수의 학술용 언어 구현

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// LALR 은 LR(1) 상태 병합 단계가 핵심 — 의사코드
// 1. LR(1) 아이템 집합 전체 생성
// 2. 코어(dot 위치 + production)가 동일한 상태 그룹화
// 3. 각 그룹의 lookahead 합집합 → 병합 상태
// 4. 병합된 상태로 액션/GOTO 테이블 재구성
// 5. reduce/reduce 충돌 검사 (같은 상태·같은 lookahead에 두 개의 reduce)

data class LR1Item(
    val production: Int,
    val dotPos: Int,
    val lookahead: String
)

// 코어: (production, dotPos) 쌍 — lookahead 제외
fun lr1Core(item: LR1Item) = Pair(item.production, item.dotPos)

fun mergeLR1States(states: List<Set<LR1Item>>): List<Set<LR1Item>> {
    // 코어가 같은 상태끼리 묶어 lookahead 합집합
    return states
        .groupBy { state -> state.map { lr1Core(it) }.toSet() }
        .values
        .map { group ->
            group.flatten()
                .groupBy { lr1Core(it) }
                .map { (core, items) ->
                    LR1Item(core.first, core.second, items.map { it.lookahead }.toSet().joinToString("/"))
                }
                .toSet()
        }
}
// 충돌 감지 후 문법 수정 또는 우선순위/결합성 선언으로 해소 (bison %left/%right/%nonassoc)
```

**관련 알고리즘**: LR(1), LL(k), Earley

---

<a id="earley"></a>
## 5. Earley Parser (얼리 파서)

**목적**: 모든 문맥 자유 문법(CFG) — 모호한 문법, 좌재귀 포함 — 을 처리

**시간 복잡도**: O(n³) 일반, O(n²) 단일 모호성, O(n) 비모호 문법

**공간 복잡도**: O(n²) — 얼리 차트

**특징**:
- 차트 파싱(chart parsing) 방식
- 각 입력 위치 i마다 "얼리 집합" S(i) 유지
- 세 가지 연산: Predict / Scan / Complete
- 모호한 문법의 모든 파스 트리를 열거 가능
- 임의 CFG에 적용 가능

**장점**:
- 좌재귀·모호한 문법 직접 처리
- 문법 제약 최소
- 자연어 처리 파서로 활용 가능

**단점**:
- 일반 경우 O(n³) — LL/LR의 O(n)보다 느림
- 실제 언어 구현에 잘 쓰이지 않음
- 구현 복잡도 높음

**활용 예시**:
- 자연어 처리(NLP) 파서
- Earley.js, nearley.js
- 프로토타입 언어 파서
- 모호한 문법 연구

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 코드**:
```kotlin
// 얼리 아이템: (production, dotPos, originPos)
data class EarleyItem(val production: Pair<String, List<String>>, val dot: Int, val origin: Int) {
    val lhs get() = production.first
    val rhs get() = production.second
    val isComplete get() = dot >= rhs.size
    val nextSymbol get() = if (isComplete) null else rhs[dot]
}

fun earleyParse(tokens: List<String>, grammar: Map<String, List<List<String>>>, start: String): Boolean {
    val n = tokens.size
    val chart = Array(n + 1) { mutableSetOf<EarleyItem>() }

    // 초기화
    grammar[start]?.forEach { rhs -> chart[0].add(EarleyItem(start to rhs, 0, 0)) }

    for (i in 0..n) {
        val worklist = ArrayDeque(chart[i].toList())
        while (worklist.isNotEmpty()) {
            val item = worklist.removeFirst()
            when {
                item.isComplete -> {
                    // Complete: item.origin 위치의 아이템 중 item.lhs 기대하는 것 전진
                    chart[item.origin].filter { it.nextSymbol == item.lhs }.forEach { prev ->
                        val next = prev.copy(dot = prev.dot + 1)
                        if (chart[i].add(next)) worklist.add(next)
                    }
                }
                item.nextSymbol in grammar -> {
                    // Predict: 비단말 → 해당 production 추가
                    grammar[item.nextSymbol!!]?.forEach { rhs ->
                        val pred = EarleyItem(item.nextSymbol to rhs, 0, i)
                        if (chart[i].add(pred)) worklist.add(pred)
                    }
                }
                i < n && item.nextSymbol == tokens[i] -> {
                    // Scan: 단말 일치 → 다음 집합으로 전진
                    chart[i + 1].add(item.copy(dot = item.dot + 1))
                }
            }
        }
    }
    return chart[n].any { it.lhs == start && it.isComplete && it.origin == 0 }
}
```

**관련 알고리즘**: LR(1), Pratt, PEG

---

<a id="pratt"></a>
## 6. Pratt Parser (연산자 우선순위 하향 파싱)

**목적**: 연산자 우선순위와 결합성을 우아하게 처리하는 하향식 파서

**시간 복잡도**: O(n)

**공간 복잡도**: O(d) — 재귀 깊이

**특징**:
- 토큰마다 NUD(null denotation, 앞 없음)와 LED(left denotation, 앞 있음) 함수 등록
- 바인딩 파워(binding power) 숫자로 우선순위 표현
- 좌재귀 불필요, 재귀 하강 + 테이블 조합
- 연산자 추가 시 기존 코드 수정 없이 등록만으로 확장

**장점**:
- 연산자 우선순위/결합성 처리가 매우 단순
- 확장성 뛰어남 (플러그인 방식)
- Pratt 자체가 표현식 파싱의 표준 답안

**단점**:
- 문(statement) 처리는 별도 전략 필요
- 개념이 처음에 낯섦

**활용 예시**:
- V8(JavaScript 엔진) 표현식 파서
- Rust nightly 파서 (구 버전)
- TypeScript 파서 내부
- Crafting Interpreters 예제

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// Pratt 파서 — 수식 파서 예시
typealias NudFn = (token: Token) -> Int
typealias LedFn = (token: Token, left: Int) -> Int

class PrattParser(private val tokens: List<Token>) {
    private var pos = 0
    private val nudMap = mutableMapOf<TokenType, NudFn>()
    private val ledMap = mutableMapOf<TokenType, Pair<Int, LedFn>>() // (bp, fn)

    init {
        // NUD 등록: 숫자 리터럴, 단항 연산자
        nudMap[TokenType.NUMBER] = { t -> t.lexeme.toInt() }
        nudMap[TokenType.MINUS] = { _ -> -parseExpr(100) } // 단항 마이너스 (bp=100)
        nudMap[TokenType.LPAREN] = { _ -> parseExpr(0).also { consume(TokenType.RPAREN) } }

        // LED 등록: (bp, 핸들러)
        ledMap[TokenType.PLUS]  = Pair(10) { _, l -> l + parseExpr(10) }
        ledMap[TokenType.MINUS] = Pair(10) { _, l -> l - parseExpr(10) }
        ledMap[TokenType.STAR]  = Pair(20) { _, l -> l * parseExpr(20) }
        ledMap[TokenType.SLASH] = Pair(20) { _, l -> l / parseExpr(20) }
    }

    fun parseExpr(minBp: Int = 0): Int {
        val token = tokens[pos++]
        var left = nudMap[token.type]?.invoke(token)
            ?: error("NUD 없음: ${token.type} at ${token.line}:${token.col}")

        while (true) {
            val next = tokens.getOrNull(pos) ?: break
            val (bp, ledFn) = ledMap[next.type] ?: break
            if (bp <= minBp) break
            pos++
            left = ledFn(next, left)
        }
        return left
    }

    private fun consume(type: TokenType) {
        require(tokens[pos++].type == type) { "Expected $type" }
    }
}
```

**관련 알고리즘**: LL(k), Lexing, AST Traversal

---

<a id="peg"></a>
## 7. PEG / Packrat Parser (파싱 표현 문법)

**목적**: 파싱 표현 문법(Parsing Expression Grammar)으로 모호성 없는 파서를 메모이제이션으로 선형 시간에 처리

**시간 복잡도**: O(n) — 메모이제이션(Packrat) 적용 시

**공간 복잡도**: O(n × rules) — 메모 테이블

**특징**:
- 순서 있는 선택(ordered choice `/`)으로 모호성 제거
- Packrat: 각 (위치, 규칙) 쌍 결과를 캐싱
- 좌재귀는 기본 PEG에서 금지 (확장 기법 존재)
- CFG와 달리 항상 결정론적 파스 결과

**장점**:
- 모호성이 없어 언어 명세가 명확
- 메모이제이션으로 지수 폭발 방지
- 어휘 분석과 구문 분석 통합 가능(scannerless)

**단점**:
- 메모 테이블 메모리 O(n × rules) — 대형 입력에서 부담
- 좌재귀 처리 복잡
- 언어 이론과 달리 "인식 언어 클래스" 불분명

**활용 예시**:
- PEG.js, Parsimmon (JavaScript)
- pest (Rust)
- LPEG (Lua)
- Python 3.9+ 새 파서 (PEG 기반)

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// Packrat 파서 핵심 구조
sealed class PEGResult {
    data class Success(val value: String, val nextPos: Int) : PEGResult()
    object Failure : PEGResult()
}

class PackratParser(private val input: String) {
    // 메모 테이블: (ruleId, pos) → 결과
    private val memo = HashMap<Pair<Int, Int>, PEGResult>()

    // 규칙 ID 상수
    companion object { const val RULE_DIGIT = 0; const val RULE_ALPHA = 1; const val RULE_IDENT = 2 }

    fun parse(ruleId: Int, pos: Int): PEGResult {
        val key = Pair(ruleId, pos)
        memo[key]?.let { return it }
        val result = when (ruleId) {
            RULE_DIGIT -> if (pos < input.length && input[pos].isDigit())
                PEGResult.Success(input[pos].toString(), pos + 1) else PEGResult.Failure
            RULE_ALPHA -> if (pos < input.length && input[pos].isLetter())
                PEGResult.Success(input[pos].toString(), pos + 1) else PEGResult.Failure
            RULE_IDENT -> {
                // ident ← alpha (alpha / digit)*
                val head = parse(RULE_ALPHA, pos)
                if (head is PEGResult.Failure) PEGResult.Failure
                else {
                    val sb = StringBuilder((head as PEGResult.Success).value)
                    var cur = head.nextPos
                    while (true) {
                        val r = parse(RULE_ALPHA, cur).let { if (it is PEGResult.Success) it else parse(RULE_DIGIT, cur) }
                        if (r is PEGResult.Failure) break
                        sb.append((r as PEGResult.Success).value); cur = r.nextPos
                    }
                    PEGResult.Success(sb.toString(), cur)
                }
            }
            else -> PEGResult.Failure
        }
        memo[key] = result
        return result
    }
}
```

**관련 알고리즘**: LL(k), Earley, Lexing

---

<a id="ast-traversal"></a>
## 8. AST Traversal (AST 순회)

**목적**: 파스 트리/AST를 순회하며 분석·변환·코드 생성을 수행

**시간 복잡도**: O(n) — 노드 수

**공간 복잡도**: O(d) — 트리 깊이 (재귀 스택)

**특징**:
- Visitor 패턴으로 순회 로직과 노드 구조 분리
- Pre-order(전위), Post-order(후위), In-order(중위) 세 가지 순서
- 다양한 패스(pass) 분리: 타입 검사, 최적화, 코드 생성
- 변환(transform)과 분석(analyze) 양쪽 모두 활용

**장점**:
- 관심사 분리로 각 패스를 독립적으로 구현
- 새 노드 타입 추가 시 Visitor만 수정
- 테스트·디버깅 용이

**단점**:
- 노드 타입 다수 시 Visitor 인터페이스가 방대해짐
- 상호 재귀 노드에서 방문 순서 관리 복잡

**활용 예시**:
- 타입 체커 (TypeScript, Kotlin 컴파일러)
- 코드 포매터 (Prettier)
- 린터 (ESLint, ktlint)
- Babel 플러그인 시스템

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// AST 노드 정의
sealed class ASTNode {
    data class Num(val value: Int) : ASTNode()
    data class BinOp(val op: String, val left: ASTNode, val right: ASTNode) : ASTNode()
    data class UnaryOp(val op: String, val operand: ASTNode) : ASTNode()
}

// Visitor 인터페이스
interface ASTVisitor<T> {
    fun visitNum(node: ASTNode.Num): T
    fun visitBinOp(node: ASTNode.BinOp): T
    fun visitUnaryOp(node: ASTNode.UnaryOp): T
}

fun <T> ASTNode.accept(visitor: ASTVisitor<T>): T = when (this) {
    is ASTNode.Num -> visitor.visitNum(this)
    is ASTNode.BinOp -> visitor.visitBinOp(this)
    is ASTNode.UnaryOp -> visitor.visitUnaryOp(this)
}

// 평가기 Visitor (후위 순회)
class EvalVisitor : ASTVisitor<Int> {
    override fun visitNum(node: ASTNode.Num) = node.value
    override fun visitBinOp(node: ASTNode.BinOp): Int {
        val l = node.left.accept(this); val r = node.right.accept(this)
        return when (node.op) { "+" -> l + r; "-" -> l - r; "*" -> l * r; "/" -> l / r; else -> error("unknown op") }
    }
    override fun visitUnaryOp(node: ASTNode.UnaryOp) =
        if (node.op == "-") -node.operand.accept(this) else node.operand.accept(this)
}

// 출력 Visitor (전위 순회)
class PrintVisitor : ASTVisitor<String> {
    override fun visitNum(node: ASTNode.Num) = node.value.toString()
    override fun visitBinOp(node: ASTNode.BinOp) =
        "(${node.op} ${node.left.accept(this)} ${node.right.accept(this)})"
    override fun visitUnaryOp(node: ASTNode.UnaryOp) = "(${node.op} ${node.operand.accept(this)})"
}
```

**관련 알고리즘**: Pratt Parser, SSA Form, LL(k)

---

<a id="ssa"></a>
## 9. SSA Form (Static Single Assignment, 정적 단일 대입)

**목적**: 각 변수가 딱 한 번만 정의되도록 IR(중간 표현)을 변환해 데이터 흐름 분석과 최적화를 단순화

**시간 복잡도**: O(n × α(n)) — 지배 프론티어 계산 포함 (거의 선형)

**공간 복잡도**: O(n) — 노드·엣지 수

**특징**:
- φ(phi) 함수로 제어 흐름 합류점에서 값 선택
- 지배 트리(dominator tree)와 지배 프론티어(dominance frontier) 계산 필요
- 변수 재정의 → 새 버전 생성 (x → x₀, x₁, x₂ …)
- 대부분의 현대 컴파일러 IR(LLVM IR, GCC GIMPLE)이 SSA 사용

**장점**:
- 사용-정의(use-def) 체인이 명확 → 상수 전파, 데드 코드 제거, GVN 등 최적화 단순화
- 레지스터 할당 품질 향상
- 병렬화 분석 용이

**단점**:
- 구성 복잡 (지배 프론티어 계산)
- φ 함수가 많아지면 코드 크기 증가
- SSA out-of-SSA(소거) 단계 추가 필요

**활용 예시**:
- LLVM IR (모든 LLVM 기반 언어)
- GCC GIMPLE
- V8 TurboFan, SpiderMonkey IonMonkey
- Kotlin/JVM bytecode 최적화 단계

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// SSA 핵심 데이터 구조 (의사코드 수준)
data class SSAValue(val name: String, val version: Int) {
    override fun toString() = "${name}_$version"
}

sealed class SSAInstr {
    data class Assign(val dest: SSAValue, val src: SSAValue) : SSAInstr()
    data class BinOp(val dest: SSAValue, val op: String, val l: SSAValue, val r: SSAValue) : SSAInstr()
    data class Phi(val dest: SSAValue, val choices: Map<String, SSAValue>) : SSAInstr() // 블록명 → 값
    data class Branch(val cond: SSAValue, val trueBlock: String, val falseBlock: String) : SSAInstr()
    data class Jump(val target: String) : SSAInstr()
}

data class BasicBlock(val label: String, val instrs: MutableList<SSAInstr> = mutableListOf())

// SSA 변환 의사코드:
// 1. CFG 구성 (basic blocks + edges)
// 2. 지배 트리 계산 (Lengauer-Tarjan 알고리즘)
// 3. 지배 프론티어 DF(n) 계산
// 4. φ 삽입: 각 변수 v에 대해 v 정의 블록 D에서 DF(D) 위치에 φ 삽입
// 5. 변수 버전 번호 부여: 스택 기반 rename 패스
//    - 블록 진입 시: 각 변수 스택에 새 버전 push
//    - 블록 탈출 시: 스택 pop (지배 범위 한정)
//
// 예시 변환:
//   원본:           SSA 변환 후:
//   if cond:        if cond_0:
//     x = 1            x_1 = 1
//   else:           else:
//     x = 2            x_2 = 2
//   y = x + 1      x_3 = φ(x_1, x_2)  ← 합류점
//                   y_0 = x_3 + 1
```

**관련 알고리즘**: Register Allocation, AST Traversal, LR(1)

---

<a id="register-allocation"></a>
## 10. Register Allocation (레지스터 할당)

**목적**: SSA/IR의 가상 레지스터(무한)를 물리 레지스터(유한)에 매핑. 부족 시 스택 스필(spill) 처리

**시간 복잡도**: 그래프 컬러링 O(n²) 최악, 선형 스캔 O(n log n)

**공간 복잡도**: O(n + e) — 간섭 그래프

**특징**:
- **그래프 컬러링(Chaitin)**: 간섭 그래프 구성 → k-색칠(k=레지스터 수) → 불가 시 스필
- **선형 스캔(Poletto)**: 라이브 인터벌 정렬 → 활성 인터벌 유지 → 겹치면 스필. JIT에 적합
- 합병(coalescing): copy 명령 양단이 간섭 없으면 같은 레지스터로 합병
- 스필 코드 생성: load/store 삽입

**장점**:
- 그래프 컬러링: 최적에 가까운 할당
- 선형 스캔: O(n log n), JIT 컴파일에 충분한 품질

**단점**:
- 그래프 컬러링: k-색칠 NP-complete → 휴리스틱 필요
- 선형 스캔: 최적 할당 아닐 수 있음
- 구현 복잡 (라이브니스 분석 선행 필요)

**활용 예시**:
- GCC, Clang/LLVM (그래프 컬러링 기반)
- V8, JVM HotSpot JIT (선형 스캔)
- Kotlin/Native 백엔드
- WebAssembly 런타임 JIT

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 라이브 인터벌 (선형 스캔용)
data class LiveInterval(val vreg: Int, val start: Int, val end: Int)

// 선형 스캔 레지스터 할당 의사코드
class LinearScanAllocator(private val numRegs: Int) {
    fun allocate(intervals: List<LiveInterval>): Map<Int, Int?> { // vreg → preg (null=스필)
        val sorted = intervals.sortedBy { it.start }
        val active = mutableListOf<LiveInterval>()   // 현재 활성 인터벌 (end 순 정렬)
        val freeRegs = (0 until numRegs).toMutableList()
        val allocation = mutableMapOf<Int, Int?>()

        for (interval in sorted) {
            // 만료된 인터벌 해제
            val expired = active.filter { it.end < interval.start }
            expired.forEach { exp ->
                active.remove(exp)
                allocation[exp.vreg]?.let { freeRegs.add(it) }
            }

            if (freeRegs.isEmpty()) {
                // 스필: 가장 끝이 긴 인터벌 or 현재 인터벌 스필
                val spill = active.maxByOrNull { it.end }!!
                if (spill.end > interval.end) {
                    allocation[interval.vreg] = allocation[spill.vreg]
                    allocation[spill.vreg] = null // spill
                    active.remove(spill)
                    active.add(interval)
                } else {
                    allocation[interval.vreg] = null // 현재를 스필
                }
            } else {
                allocation[interval.vreg] = freeRegs.removeFirst()
                active.add(interval)
                active.sortBy { it.end }
            }
        }
        return allocation
    }
}
// 그래프 컬러링 방식: 간섭 그래프 구성 → Chaitin simplify/spill/select 루프
```

**관련 알고리즘**: SSA Form, AST Traversal

---
