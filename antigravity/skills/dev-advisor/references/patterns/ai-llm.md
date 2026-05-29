# AI / LLM 애플리케이션 패턴 (AI / LLM Application Patterns)

2024~2026 LLM 애플리케이션 표준 어휘. Claude / GPT / Gemini / Llama 류 위에 RAG, Agent, Tool Use, Multi-Agent, Guardrails 등 production-grade 구조를 올릴 때 반복적으로 등장하는 12개 패턴.

---

## 1. RAG (Retrieval-Augmented Generation)

**목적**: 모델의 parametric knowledge에 의존하지 않고 외부 지식 베이스에서 검색한 컨텍스트를 prompt에 합성하여 환각(hallucination)을 줄이고 최신성을 확보합니다.

**특징**:
- 5단계 파이프라인: ① Chunking → ② Embedding → ③ Retrieval → ④ Reranking → ⑤ Prompt 합성
- 벡터 DB (Qdrant, pgvector, Weaviate, Pinecone) + BM25 hybrid search
- Reranker (Cohere rerank, BGE-reranker) 로 top-k 정제
- Lewis et al. 2020 "Retrieval-Augmented Generation for Knowledge-Intensive NLP" 원조

**장점**:
- 모델 재학습 없이 지식 갱신
- 출처(citation) 노출 가능 — 검증 가능성
- 도메인 특화 데이터 주입

**단점**:
- 검색 품질이 답변 품질을 결정 (garbage in, garbage out)
- chunk 경계가 의미 단위와 어긋나면 context fragmentation
- latency 증가 (embedding + retrieval round-trip)

**활용 예시**:
- 사내 위키 Q&A bot
- 법률/의료 문서 검색
- 코드베이스 Q&A (Cursor, Cody)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class RagPipeline(
    private val embedder: Embedder,
    private val vectorStore: VectorStore,
    private val reranker: Reranker,
    private val llm: AnthropicClient,
) {
    fun answer(question: String): String {
        // 1) Embedding
        val qVec = embedder.embed(question)
        // 2) Retrieval (top-20 candidates)
        val candidates = vectorStore.search(qVec, k = 20)
        // 3) Reranking → top-5
        val context = reranker.rerank(question, candidates, k = 5)
            .joinToString("\n---\n") { it.text }
        // 4) Prompt 합성
        val prompt = """
            다음 컨텍스트만 사용하여 질문에 답하세요. 모르면 "모릅니다"라고 답하세요.
            컨텍스트:
            $context
            질문: $question
        """.trimIndent()
        // 5) Generation
        return llm.messages().create(
            MessageCreateParams.builder()
                .model(Model.CLAUDE_OPUS_4_7)
                .maxTokens(1024)
                .addUserMessage(prompt)
                .build()
        ).content().first().text().get().text()
    }
}
```

**관련 패턴**: Memory (Semantic), Context Compaction, Guardrails

---

## 2. Tool Use (Function Calling)

**목적**: LLM이 외부 함수/API를 호출할 수 있도록 JSON Schema 기반 도구 정의를 prompt에 노출하고, 모델이 생성한 도구 호출 요청을 실행 엔진이 dispatch 합니다.

**특징**:
- OpenAI `tools` / Anthropic `tools` / Gemini `function_declarations` 표준
- JSON Schema 로 input parameter 정의
- 모델 응답이 `tool_use` block 일 때 실제 함수 실행 → 결과를 `tool_result` 로 재주입
- Parallel tool call 지원 (Claude 3.5 이상)

**장점**:
- 모델이 결정론적 행동(계산, DB 조회, API 호출)을 수행
- 환각 대신 실제 데이터 기반 응답
- 도구 추가만으로 기능 확장 — Open/Closed Principle

**단점**:
- 도구 정의 prompt 가 token 비용 증가
- 도구가 많아지면 모델이 잘못된 도구 선택 (tool confusion)
- 보안: 외부 입력이 도구 인자로 흘러가는 prompt injection 표면

**활용 예시**:
- ChatGPT plugins, Claude Computer Use
- Cursor의 file edit / shell 도구
- Slack/Jira 자동화 Bot

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
val getWeatherTool = Tool.builder()
    .name("get_weather")
    .description("주어진 도시의 현재 날씨를 반환합니다.")
    .inputSchema(
        Tool.InputSchema.builder()
            .putProperty("city", JsonValue.from(mapOf("type" to "string")))
            .addRequired("city")
            .build()
    ).build()

fun runWithTools(userMsg: String): String {
    var messages = listOf(MessageParam.builder().role("user").content(userMsg).build())
    while (true) {
        val resp = client.messages().create(
            MessageCreateParams.builder()
                .model(Model.CLAUDE_OPUS_4_7)
                .addTool(getWeatherTool)
                .messages(messages)
                .build()
        )
        val toolUse = resp.content().firstOrNull { it.isToolUse() } ?: return resp.text()
        val result = WeatherApi.get(toolUse.input()["city"].asString())
        messages = messages + resp.toAssistantMessage() + toolResultMessage(toolUse.id(), result)
    }
}
```

**관련 패턴**: Agent Loop, Multi-Agent Orchestration, Guardrails

---

## 3. Agent Loop (ReAct)

**목적**: LLM이 Reasoning(생각) → Acting(도구 호출) → Observation(결과 관찰) 을 반복하며 목표를 달성하도록 합니다. Yao et al. 2022 "ReAct: Synergizing Reasoning and Acting in Language Models" 가 원조.

**특징**:
- Thought / Action / Observation triplet 을 prompt 에 누적
- 종료 조건: 모델이 `final_answer` 도구를 호출하거나 max_iterations 도달
- Tool Use 와 결합되어 사용 — Agent Loop 는 controller, Tool Use 는 mechanism
- Reflexion (Shinn et al. 2023) 으로 실패 후 자기 반성 추가 가능

**장점**:
- 다단계 문제 해결 (multi-hop QA, code debugging)
- 중간 추론이 trace 로 남아 디버깅 용이
- 도구 조합으로 일반화

**단점**:
- 무한 루프 / context window 폭주 위험
- 한 번 잘못된 추론이 누적되면 회복 어려움
- token 비용이 단발 prompt 대비 5~20×

**활용 예시**:
- LangChain AgentExecutor
- Anthropic Claude Computer Use
- AutoGPT, BabyAGI

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class ReActAgent(private val llm: AnthropicClient, private val tools: List<Tool>) {
    fun run(goal: String, maxSteps: Int = 10): String {
        var messages = mutableListOf<MessageParam>(userMessage(goal))
        repeat(maxSteps) { step ->
            val resp = llm.messages().create(
                MessageCreateParams.builder()
                    .model(Model.CLAUDE_OPUS_4_7)
                    .tools(tools)
                    .messages(messages)
                    .build()
            )
            messages.add(resp.toAssistantMessage())
            val toolCall = resp.content().firstOrNull { it.isToolUse() }
                ?: return resp.text() // final answer
            val observation = ToolRegistry.execute(toolCall)
            messages.add(toolResultMessage(toolCall.id(), observation))
        }
        return "[max_steps reached]"
    }
}
```

**관련 패턴**: Tool Use, Self-Critique, Multi-Agent Orchestration

---

## 4. Multi-Agent Orchestration

**목적**: 단일 agent 의 인지 부하를 분산하기 위해 역할이 다른 여러 agent 를 협조시켜 작업을 분할 정복합니다.

**특징**:
- **Supervisor / Worker**: 1개 supervisor 가 task 를 worker 에게 routing, 결과 집계
- **Hierarchical**: supervisor 가 또 다른 sub-supervisor 를 가짐 (트리 구조)
- **Peer-to-peer (A2A)**: agent 들이 직접 메시지 교환, Google A2A protocol
- 대표 프레임워크: AutoGen (Microsoft), CrewAI, LangGraph, OpenAI Swarm

**장점**:
- 역할 분리로 prompt 가 짧고 명확
- 병렬 worker 로 throughput 증가
- 도메인 특화 sub-agent (researcher, coder, reviewer) 조합 가능

**단점**:
- 메시지 패싱 overhead → latency 증가
- agent 간 통신 프로토콜 설계 필요
- 무한 ping-pong 루프 위험

**활용 예시**:
- Anthropic 의 oh-my-claudecode `team` 모드 (explore + architect + executor)
- AutoGen GroupChat
- Devin (Cognition AI) sub-agent fleet

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class Supervisor(private val workers: Map<String, Agent>) {
    fun solve(task: String): String {
        val plan = planner.decompose(task) // List<SubTask(role, instruction)>
        val results = plan.map { sub ->
            val worker = workers[sub.role] ?: error("no worker for ${sub.role}")
            sub.role to worker.run(sub.instruction)
        }.toMap()
        return aggregator.merge(task, results)
    }
}
// Hierarchical: 위 Supervisor 자체를 다른 Supervisor 의 worker 로 등록 가능
```

**관련 패턴**: Agent Loop, Mediator, Chain of Responsibility

---

## 5. Prompt Template

**목적**: prompt 를 hardcoded 문자열 결합이 아닌 변수 슬롯이 있는 템플릿으로 관리하여 재사용성, 버전 관리, 다국어 대응을 확보합니다.

**특징**:
- Jinja2 / Handlebars / f-string 류 변수 치환
- Role-aware: system / user / assistant 메시지 분리
- 템플릿 파일 (`.j2`, `.prompt`, `.txt`) 을 코드와 분리
- LangChain `PromptTemplate`, Anthropic prompt caching 과 결합

**장점**:
- 비개발자(PM, PO) 가 prompt 수정 가능
- A/B 테스트 / 버전 diff 용이
- prompt injection 방어 표면 축소 (변수 escape)

**단점**:
- 단순 1회용 prompt 에는 과한 추상화
- 템플릿 엔진 학습 비용

**활용 예시**:
- LangChain `ChatPromptTemplate`
- Anthropic Workbench prompt 저장소
- Replit Ghostwriter

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class PromptTemplate(private val template: String) {
    fun render(vars: Map<String, String>): String =
        vars.entries.fold(template) { acc, (k, v) -> acc.replace("{{$k}}", v) }
}

val tmpl = PromptTemplate("""
    당신은 {{role}} 입니다.
    사용자 질문: {{question}}
    {{language}} 로 답변하세요.
""".trimIndent())

val prompt = tmpl.render(mapOf(
    "role" to "시니어 백엔드 엔지니어",
    "question" to "Kafka rebalance 가 자주 일어납니다",
    "language" to "한국어"
))
```

**관련 패턴**: Few-Shot Prompting, Template Method (GoF)

---

## 6. Few-Shot Prompting

**목적**: prompt 에 입력→출력 예시 몇 개를 포함시켜 모델에게 원하는 출력 포맷/스타일/추론 방식을 in-context 로 학습시킵니다.

**특징**:
- Zero-shot (0개) → One-shot (1개) → Few-shot (2~5개)
- Chain-of-Thought (CoT) 와 결합: 예시에 추론 과정 포함 (Wei et al. 2022)
- 예시 순서가 성능에 영향 (recency bias)
- Dynamic few-shot: 질문과 유사한 예시를 벡터 검색으로 선택

**장점**:
- 미세조정 없이 task 적응
- 출력 포맷 강제 (JSON 구조, 톤)
- Edge case 학습

**단점**:
- 예시가 context window 차지 — token 비용 증가
- 예시 편향 (예시 도메인 외 일반화 약화)

**활용 예시**:
- 분류 task (감성 분석, 의도 분류)
- 구조화 출력 (JSON 추출)
- 코드 변환 / 번역 스타일 지정

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
val fewShotPrompt = """
    영화 리뷰의 감성을 POSITIVE / NEGATIVE / NEUTRAL 로 분류하세요.

    리뷰: "연기는 좋았지만 시나리오가 아쉽다"
    감성: NEUTRAL

    리뷰: "올해 본 영화 중 최고였다"
    감성: POSITIVE

    리뷰: "시간이 아깝다. 결말이 허무하다"
    감성: NEGATIVE

    리뷰: "{{input}}"
    감성:
""".trimIndent()

fun classify(review: String): String =
    llm.complete(fewShotPrompt.replace("{{input}}", review)).trim()
```

**관련 패턴**: Prompt Template, RAG (dynamic few-shot)

---

## 7. Self-Critique / Self-Refine

**목적**: 모델이 생성한 출력을 같은 모델(또는 다른 모델) 이 비판(critic) 하고 그 피드백을 바탕으로 재생성하여 품질을 개선합니다.

**특징**:
- Generator → Critic → Refiner 3-pass (Madaan et al. 2023 "Self-Refine")
- Critic 은 별도 prompt 로 rubric 기반 평가
- 수렴 조건: critic score ≥ threshold 또는 max_iterations
- Constitutional AI (Anthropic) 의 self-critique step 동일 메커니즘

**장점**:
- 추가 학습 없이 출력 품질 향상
- 글쓰기, 코드, 수학 추론에서 효과 검증됨
- 사용자 개입 없이 자동 개선

**단점**:
- 같은 모델의 blind spot 은 critic 도 못 잡음
- token 비용 2~3×
- critic 이 generator 보다 약하면 noise

**활용 예시**:
- 글쓰기 도구 (Notion AI revise)
- 코드 리뷰 자동화
- Anthropic Constitutional AI 학습 데이터 생성

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
class SelfRefine(private val llm: AnthropicClient, private val maxIter: Int = 3) {
    fun generate(task: String): String {
        var draft = llm.complete("Task: $task\nDraft:")
        repeat(maxIter) {
            val critique = llm.complete("""
                다음 draft 를 다음 기준으로 비판하세요: 명확성, 사실성, 완결성.
                Draft: $draft
                비판:
            """.trimIndent())
            if ("문제 없음" in critique) return draft
            draft = llm.complete("""
                Draft: $draft
                받은 비판: $critique
                위 비판을 반영하여 개선된 버전을 작성하세요.
            """.trimIndent())
        }
        return draft
    }
}
```

**관련 패턴**: Evaluator-Optimizer, Agent Loop

---

## 8. Memory: Episodic & Semantic

**목적**: 대화의 단기 컨텍스트(episodic) 와 누적된 사용자/도메인 지식(semantic) 을 분리하여 저장하고, 필요 시 prompt 에 주입합니다.

**특징**:
- **Episodic memory**: 최근 N 턴 대화 — token buffer / FIFO
- **Semantic memory**: 사실/선호/관계 — 벡터 DB + 구조화 KV store
- 인지 과학의 Tulving (1972) episodic vs semantic 구분 차용
- 대표 구현: MemGPT, Letta, mem0, Anthropic memory tool

**장점**:
- 장기 사용자 컨텍스트 유지 (personalization)
- 대화 재개 시 자연스러운 연속성
- semantic 부분은 검색 기반으로 무한 확장

**단점**:
- 메모리 추출/요약 자체가 또 다른 LLM 호출 — 비용
- 잘못된 사실 저장 시 지속적 환각 (memory poisoning)
- 프라이버시: 개인정보 저장 책임

**활용 예시**:
- ChatGPT memory 기능
- Anthropic Claude `memory` tool
- 챗봇의 사용자 프로파일

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class HybridMemory(private val vectorStore: VectorStore) {
    private val episodic = ArrayDeque<Turn>(20) // 최근 20턴

    fun remember(turn: Turn) {
        episodic.addLast(turn)
        if (episodic.size > 20) episodic.removeFirst()
        // semantic 추출: fact 만 별도 저장
        val facts = factExtractor.extract(turn)
        facts.forEach { vectorStore.upsert(it.text, it.toEmbedding()) }
    }

    fun buildContext(query: String): String {
        val recent = episodic.joinToString("\n") { "${it.role}: ${it.text}" }
        val relevant = vectorStore.search(query.toEmbedding(), k = 5)
            .joinToString("\n") { "- ${it.text}" }
        return "## 최근 대화\n$recent\n\n## 관련 사실\n$relevant"
    }
}
```

**관련 패턴**: RAG, Context Compaction

---

## 9. Guardrails

**목적**: LLM 시스템의 input(사용자) 와 output(모델) 양쪽에 검증/필터/차단 계층을 두어 prompt injection, PII 누출, 유해 콘텐츠, 정책 위반을 방어합니다.

**특징**:
- **Input filter**: prompt injection 탐지, jailbreak 패턴 매칭, allowlist
- **Output filter**: PII redaction, content safety (toxicity, self-harm), 형식 검증 (JSON schema)
- 구현: 정규식 + 분류기(distilbert) + LLM-as-judge 다층
- NVIDIA NeMo Guardrails, Guardrails AI, Llama Guard, Anthropic safety filter

**장점**:
- 보안/컴플라이언스 요건 충족 (HIPAA, GDPR)
- LLM 단독으로 막기 어려운 결정론적 정책 강제
- 감사 로그 자연스럽게 누적

**단점**:
- false positive 로 정상 요청 차단 (UX 저하)
- 필터 자체가 추가 latency
- adversarial bypass (간접 injection) 에 항상 취약

**활용 예시**:
- 금융/의료/법률 챗봇
- 사내 코드 어시스턴트의 소스코드 유출 방지
- 공공 chatbot 의 정치/혐오 발언 차단

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class GuardrailedLlm(private val llm: AnthropicClient) {
    fun ask(userInput: String): String {
        // 1) Input filter
        if (InjectionDetector.isPromptInjection(userInput))
            return "[차단됨] 의심스러운 입력입니다."
        val sanitized = PiiRedactor.redact(userInput)

        // 2) LLM 호출
        val raw = llm.complete(sanitized)

        // 3) Output filter
        if (ContentSafety.score(raw) > 0.8) {
            AuditLog.warn("unsafe_output", userInput, raw)
            return "[필터됨] 답변할 수 없습니다."
        }
        return PiiRedactor.redact(raw)
    }
}
```

**관련 패턴**: Circuit Breaker (Reliability), Decorator

---

## 10. Evaluator-Optimizer

**목적**: 생성기(generator) 와 평가 함수(scorer) 를 분리하여 후보들을 반복 평가하고 점수가 가장 높은 출력을 선택하거나 점수가 임계치를 넘을 때까지 개선합니다.

**특징**:
- Generator: N개 후보 생성 (temperature 조절 / sampling)
- Scorer: rubric / LLM-as-judge / unit test / metric 함수
- 최적화 루프: best-of-N, beam search, reinforcement-style refine
- Self-Critique 와 차이점: Evaluator-Optimizer 는 명시적 score function 과 후보 비교 존재

**장점**:
- 측정 가능한 품질 향상
- 도메인 메트릭(BLEU, ROUGE, 컴파일 성공률) 직접 최적화
- 모델 교체와 무관하게 평가 파이프라인 재사용

**단점**:
- 좋은 evaluator 설계가 어려움 (proxy metric 의 한계)
- N×iter 만큼 비용 증가
- evaluator 가 generator 와 같은 모델이면 bias

**활용 예시**:
- 코드 생성 (테스트 통과율로 평가)
- 카피라이팅 (engagement 예측 모델로 평가)
- prompt 자동 튜닝 (DSPy, PromptBreeder)

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
class EvaluatorOptimizer<T>(
    private val generator: (prompt: String) -> T,
    private val evaluator: (T) -> Double,
    private val threshold: Double = 0.9,
    private val maxIter: Int = 5,
) {
    fun optimize(prompt: String, n: Int = 4): T {
        repeat(maxIter) {
            val candidates = (1..n).map { generator(prompt) }
            val best = candidates.maxBy { evaluator(it) }
            if (evaluator(best) >= threshold) return best
        }
        return (1..n).map { generator(prompt) }.maxBy { evaluator(it) }
    }
}
// 예: 코드 생성기 + 컴파일+테스트 점수로 평가
```

**관련 패턴**: Self-Critique, Strategy, Agent Loop

---

## 11. Context Compaction

**목적**: 대화 길이가 token budget 을 초과하지 않도록 이전 턴을 요약/압축하여 context window 를 관리합니다.

**특징**:
- **Rolling summary**: 오래된 N턴을 LLM 으로 요약하여 1개 메시지로 대체
- **Sliding window**: 최근 K턴만 유지, 그 이전은 버림
- **Hierarchical summary**: 최근 = 원문, 중간 = 요약, 옛날 = 요약의 요약
- token budget 모니터링 — Anthropic context window 200k, GPT-4o 128k 한계
- Claude Code 자동 context compaction, MemGPT 의 main-context vs archival

**장점**:
- 무한 길이 대화 지원
- context window 비용 통제
- 중요 정보 우선 유지 (importance-aware compaction)

**단점**:
- 요약 과정에서 정보 손실
- 요약 자체에 LLM 호출 비용
- 요약 품질이 대화 품질을 결정

**활용 예시**:
- Claude Code의 자동 context compaction
- LangChain `ConversationSummaryMemory`
- 장시간 chatbot 세션

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class ContextCompactor(
    private val llm: AnthropicClient,
    private val budgetTokens: Int = 100_000,
    private val keepRecent: Int = 10,
) {
    fun compact(history: List<Turn>): List<Turn> {
        val currentTokens = history.sumOf { it.tokenCount }
        if (currentTokens < budgetTokens) return history

        val recent = history.takeLast(keepRecent)
        val older = history.dropLast(keepRecent)
        val summary = llm.complete("""
            다음 대화를 핵심 사실/결정/미해결 질문 중심으로 요약하세요.
            ${older.joinToString("\n") { "${it.role}: ${it.text}" }}
        """.trimIndent())
        return listOf(Turn(role = "system", text = "[이전 요약]\n$summary")) + recent
    }
}
```

**관련 패턴**: Memory (Episodic), RAG, Sliding Window

---

## 12. Human-in-the-Loop (HITL)

**목적**: LLM 의 결정/출력에 사람의 승인, 수정, 거부 단계를 끼워 넣어 고위험 작업의 안전성을 확보하고, 동시에 피드백을 학습 데이터로 수집합니다.

**특징**:
- **Approval queue**: 위험 액션(DB write, 외부 결제, 코드 머지) 전 사람 승인 대기
- **Escalation policy**: confidence 가 낮거나 정책에 걸리면 사람에게 위임
- **Audit log**: 사람 결정과 모델 출력 쌍을 영구 저장 → RLHF / DPO dataset
- async (티켓 큐) vs sync (UI prompt) 두 형태

**장점**:
- 비가역 액션의 사고 방지
- 규제 산업 (의료, 금융, 법률) 요건 충족
- 학습 데이터 자연스럽게 누적 (preference pair)

**단점**:
- 사람 응답 대기로 latency 폭증
- 사람이 병목 → 처리량 한계
- 검토 피로 (alert fatigue) 로 자동 승인 남발

**활용 예시**:
- GitHub Copilot Workspace 의 plan 승인
- ClickUp/Jira 의 자동화 액션 승인 단계
- Anthropic Claude Computer Use 의 위험 작업 confirm

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
sealed class Decision { object Approve : Decision(); object Reject : Decision()
    data class Edit(val newPayload: String) : Decision() }

class HitlGateway(private val approvalQueue: ApprovalQueue, private val audit: AuditLog) {
    suspend fun executeWithApproval(action: AgentAction): ActionResult {
        if (action.risk < RiskLevel.HIGH) return action.execute() // 자동 통과

        val ticket = approvalQueue.enqueue(action)
        val decision = ticket.await(timeout = 1.hours) // 사람 응답 대기
        audit.record(action, decision)

        return when (decision) {
            is Decision.Approve -> action.execute()
            is Decision.Edit -> action.copy(payload = decision.newPayload).execute()
            Decision.Reject -> ActionResult.rejected("user_declined")
        }
    }
}
```

**관련 패턴**: Guardrails, Saga (Distributed), Circuit Breaker

---
