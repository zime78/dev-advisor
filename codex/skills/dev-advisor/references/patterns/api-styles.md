# API 스타일 (API Architectural Styles)

API 통신 스타일 9 종. [`api-design.md`](api-design.md) 가 "Pagination / Idempotency 같은 *설계 패턴*" 이라면 본 파일은 **API 스타일 자체** 의 의사결정 — REST vs GraphQL vs gRPC vs WebSocket vs Webhook 등 **언제 어느 스타일을 쓰는가**.

**원전·표준 참고**:
- Roy Fielding — *Architectural Styles and the Design of Network-based Software Architectures* (Ph.D. dissertation, 2000) — REST
- GraphQL Specification — https://spec.graphql.org/
- gRPC Documentation — https://grpc.io
- IETF RFC 6455 (WebSocket), RFC 7159 (JSON), RFC 9000 (QUIC)
- W3C SSE (HTML Living Standard)
- W3C WebTransport (draft)
- W3C SOAP 1.2

**의사결정 매트릭스** (스타일 ↔ 사용처):

| 스타일 | 방향 | 연결 | 형식 | 타입 강도 | 적합 |
|--------|------|------|------|----------|------|
| REST | Req/Resp | 단발 | JSON | 약함 | 일반 API, 캐시 친화 |
| GraphQL | Req/Resp | 단발 | JSON | 강함(schema) | 다양한 클라이언트, over/under-fetching |
| gRPC | Req/Resp + Stream | 단발/지속 | Protobuf | 매우 강함 | 서비스 간, 고성능 |
| WebSocket | Bidirectional | 지속 | text/binary | 약함 | 채팅, 실시간 협업 |
| SSE | Server→Client | 지속 | text | 약함 | 알림, 라이브 피드 |
| Webhook | Server→Server | 단발 | JSON | 약함 | 비동기 이벤트 통지 |
| JSON-RPC | Req/Resp | 단발 | JSON | 약함 | 간단 RPC, RPC over WS |
| SOAP | Req/Resp | 단발 | XML+WSDL | 강함 | 레거시 엔터프라이즈 |
| WebTransport | Bidi + Datagram | QUIC | binary | 약함 | 게임, 영상 (WebSocket 후속) |

**관련 카탈로그**:
- [api-design.md](api-design.md) — REST 성숙도 / Pagination / Idempotency 같은 설계 패턴 (스타일 위)
- [networking.md](networking.md) — HTTP/2/3, WebSocket, WebRTC (transport 본체)
- [`../security/security-api-web.md`](../security/security-api-web.md) — CSP / SRI / HSTS / CORS
- [distributed.md](distributed.md) — API Gateway / Service Mesh

---

<a id="rest"></a>

## 1. REST (Representational State Transfer)

**목적/정의**: Roy Fielding 의 2000 박사학위 논문에서 정립된 web 아키텍처 스타일. **Resource (URI)** 를 HTTP 메서드 (verb) 로 조작하는 stateless · cacheable · uniform interface 기반의 API 설계 양식. 오늘날 가장 광범위하게 채택된 API 스타일.

**메커니즘**:
- **Resource = URI**: `/users/42`, `/orders/2024/march` — 명사 중심 식별
- **HTTP Verb**: `GET` (조회, safe + idempotent) / `POST` (생성, non-idempotent) / `PUT` (전체 교체, idempotent) / `PATCH` (부분 수정) / `DELETE` (제거, idempotent)
- **Statelessness**: 서버는 client session 을 저장하지 않음. 모든 요청은 self-contained (인증 토큰 매번 포함)
- **Cacheability**: response 가 `Cache-Control`, `ETag`, `Last-Modified` 로 self-describing. 중간 proxy 가 캐싱 가능
- **Uniform Interface**: 동일 메서드·동일 의미. HATEOAS (Hypermedia As The Engine Of Application State) 는 Level 3 (Richardson Maturity Model) 의 핵심이나 현실에서는 거의 미적용
- **표현 협상**: `Accept: application/json` vs `Accept: application/xml` 로 representation 선택

**장점**:
- HTTP 인프라(proxy, CDN, gateway, browser) 와 완벽 호환 → 캐싱·로드밸런싱·관측성 무료
- 학습 곡선 낮음. 광대한 도구 (Postman, curl, OpenAPI/Swagger) 생태계
- Stateless → 수평 확장 용이
- Browser 가 first-class client (XHR / fetch 직접 호출)

**단점·트레이드오프**:
- Over-fetching / under-fetching: 화면 하나 그리려고 여러 endpoint 호출 → N+1 round-trip. GraphQL/BFF 의 동기
- 강한 타입·스키마 없음 → OpenAPI 로 보완하나 런타임 강제 어려움
- Versioning 곤란 (URL `/v1`, `/v2` vs Header `Accept-Version: ...` 종교 전쟁)
- HATEOAS 미적용 → 사실상 RPC over HTTP 로 전락 (Level 2)
- Bidirectional / streaming 불가 (long polling 으로 우회 → 비효율)

**활용 예시**:
- GitHub REST API, Stripe API, Twilio, AWS S3, Atlassian Jira
- 대부분의 SaaS 공개 API 의 default
- 모바일 앱 ↔ 백엔드 통신의 압도적 다수

**언제 쓰지 말 것**:
- Bidirectional realtime (채팅, 협업 편집) → WebSocket
- 화면별 응답 형태가 다양해 endpoint 폭증 → GraphQL / BFF
- 마이크로서비스 간 low-latency 호출 → gRPC

**난이도**: 낮음

**예제** (Kotlin / Ktor server + curl client):
```kotlin
// Server
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.server.request.*
import io.ktor.http.*

fun Application.userApi() = routing {
    route("/api/v1/users") {
        get("{id}") {
            val id = call.parameters["id"]?.toIntOrNull() ?: return@get call.respond(HttpStatusCode.BadRequest)
            val user = repo.findById(id) ?: return@get call.respond(HttpStatusCode.NotFound)
            call.response.header(HttpHeaders.ETag, user.version.toString())
            call.response.header(HttpHeaders.CacheControl, "private, max-age=60")
            call.respond(user)
        }
        post {
            val req = call.receive<CreateUserRequest>()
            val created = repo.create(req)
            call.response.header(HttpHeaders.Location, "/api/v1/users/${created.id}")
            call.respond(HttpStatusCode.Created, created)
        }
        delete("{id}") {
            repo.delete(call.parameters["id"]!!.toInt())
            call.respond(HttpStatusCode.NoContent)
        }
    }
}
```

```bash
# Client
curl -X GET https://api.example.com/api/v1/users/42 \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer eyJhbGc...'

curl -X POST https://api.example.com/api/v1/users \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: 7c9e...' \
  -d '{"name":"Ada","email":"ada@x.io"}'
```

**관련 패턴**: [GraphQL](#graphql) (대안), [JSON-RPC](#json-rpc) (RPC 변형), [api-design.md / Richardson Maturity Model](api-design.md), [distributed.md / API Gateway](distributed.md), [networking.md / HTTP semantics](networking.md)

---

<a id="graphql"></a>

## 2. GraphQL

**목적/정의**: Facebook 이 2012 내부 사용 → 2015 공개한 query language for APIs + runtime. **단일 endpoint (`POST /graphql`)** 에 schema 기반 query 를 전송하면 클라이언트가 원하는 필드만 선택해 받음. REST 의 over/under-fetching 을 schema-level 로 해결.

**메커니즘**:
- **Schema (SDL)**: `type User { id: ID! name: String posts: [Post!]! }` — 강한 타입 + nullability 명시
- **3종 operation**: Query (조회, idempotent) / Mutation (변경) / Subscription (서버 push, WebSocket 위)
- **Resolver**: 각 필드별 데이터 fetch 함수. `Query.user(id)` → DB / `User.posts` → 별도 resolver
- **N+1 problem + DataLoader**: 부모 1건 + 자식 N건의 N+1 쿼리 → DataLoader 가 batch + cache 로 해결
- **Persisted Query**: query 본문 해시 등록 → 클라이언트는 해시만 전송 → CDN 캐시 + 보안 (임의 query 차단)
- **Federation (Apollo)**: 여러 GraphQL 서비스를 super-graph 로 합성. `@key`, `@external` directive 로 서비스 간 entity 공유
- **Introspection**: `__schema` 쿼리로 schema 자체 조회 가능 (개발 편의 ↔ 공격 표면)

**장점**:
- Over/under-fetching 해소: 클라이언트가 필요 필드만 선택
- 단일 endpoint → API 버전 관리 단순 (deprecation directive 로 점진적 전환)
- 강한 타입 schema → IDE 자동완성, codegen, type-safe client
- 다양한 클라이언트 (모바일·웹·TV) 가 동일 backend 사용 (BFF 대체 가능)

**단점·트레이드오프**:
- HTTP 캐싱과 상극 (모든 요청이 `POST /graphql`) → CDN 활용 어려움 (persisted query 로 우회)
- Query 복잡도 공격 (depth bomb, alias bomb) → depth limit, query cost analysis 필수
- N+1 문제는 schema 가 아니라 resolver 가 해결해야 함
- File upload, binary 처리 비표준 (multipart spec 별도)
- 학습 곡선 (resolver, DataLoader, Federation) + 운영 복잡도

**활용 예시**:
- GitHub GraphQL API v4 (REST 와 병행 제공)
- Shopify, Netflix, Airbnb, Atlassian
- Apollo Server / Apollo Client, Hasura, Relay
- BFF 계층의 흔한 선택 (디바이스별 응답 조립)

**언제 쓰지 말 것**:
- 단순 CRUD + 단일 클라이언트 → REST 가 충분
- 파일 업로드 / binary 중심 → REST (multipart) 또는 gRPC
- 강한 캐싱 필요 (정적 자원) → REST + CDN

**난이도**: 중간

**예제** (Schema + Kotlin server + curl):
```graphql
# Schema
type User {
  id: ID!
  name: String!
  posts(limit: Int = 10): [Post!]!
}
type Post { id: ID!  title: String!  author: User! }
type Query { user(id: ID!): User }
type Mutation { createPost(title: String!, authorId: ID!): Post! }
type Subscription { postCreated(authorId: ID!): Post! }
```

```kotlin
// Resolver (graphql-kotlin)
@Component
class UserResolver(private val repo: UserRepo, private val postRepo: PostRepo) : Query {
    suspend fun user(id: String): User? = repo.find(id)
}

@Component
class UserFieldResolver(private val loader: PostDataLoader) {
    suspend fun posts(user: User, limit: Int): List<Post> =
        loader.load(user.id).take(limit)  // DataLoader batches N+1
}
```

```bash
curl -X POST https://api.example.com/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ user(id:\"42\") { name posts(limit:5){ title } } }"}'
```

**관련 패턴**: [REST](#rest) (대안), [distributed.md / BFF](distributed.md), [api-design.md / Pagination (cursor)](api-design.md), [WebSocket](#websocket-api) (Subscription transport)

---

<a id="grpc"></a>

## 3. gRPC

**목적/정의**: Google 이 2015 공개한 고성능 RPC 프레임워크. **Protocol Buffers (Protobuf)** 로 schema·serialization 을 정의하고 **HTTP/2** 위에서 binary 로 전송. 서비스 간 (특히 마이크로서비스) low-latency · strongly-typed 통신의 표준.

**메커니즘**:
- **Protobuf IDL** (`.proto`): `service UserSvc { rpc GetUser(GetUserReq) returns (User); }` — code generation 으로 client/server stub 생성
- **HTTP/2 multiplexing**: 단일 TCP connection 위 여러 stream 병렬 → HoL blocking 완화
- **4 RPC 유형**:
  - **Unary**: 1 req → 1 resp (전통 RPC)
  - **Server streaming**: 1 req → N resp (e.g. 검색 결과 stream)
  - **Client streaming**: N req → 1 resp (e.g. 로그 업로드)
  - **Bidirectional streaming**: N req ↔ N resp (e.g. 채팅, 실시간 가격)
- **Binary serialization**: JSON 대비 30-100배 작음·빠름. wire format 은 tag-length-value
- **Deadline propagation**: client 가 `deadline` 설정 → 모든 downstream call 에 전파 (cascading cancellation)
- **Status code**: HTTP code 가 아닌 gRPC code (`OK`, `NOT_FOUND`, `DEADLINE_EXCEEDED`, `UNAVAILABLE` 등 16종)
- **gRPC-Web**: 브라우저에서 직접 호출 가능 (proxy 통해 HTTP/1.1 ↔ HTTP/2 변환)

**장점**:
- 매우 빠름 (binary + HTTP/2). REST/JSON 대비 latency 50-70% 감소 보고 (Uber, Netflix)
- 강한 타입 + codegen → 컴파일 타임 안전성. 다국어 (10+ 언어) client 자동 생성
- 양방향 streaming 1급 지원 → WebSocket 없이도 realtime 가능
- Deadline / cancellation / retry / load balancing 이 client lib 에 내장

**단점·트레이드오프**:
- Browser 직접 호출 불가 (gRPC-Web proxy 필요, 또한 streaming 제한)
- 사람이 읽기 어려운 binary → 디버깅 시 `grpcurl` 같은 도구 필요
- HTTP 캐싱 (proxy / CDN) 불가
- Schema breaking change 관리 필요 (field tag 변경 금지 등 Protobuf evolution 규칙)
- 방화벽 / 일부 corporate proxy 가 HTTP/2 차단

**활용 예시**:
- Google internal (Stubby → gRPC 의 전신)
- Kubernetes (kubelet ↔ container runtime: CRI)
- etcd, CockroachDB, Dgraph, Envoy xDS
- Netflix, Square, Lyft 내부 마이크로서비스
- Mobile (Android/iOS): gRPC-Java, gRPC-Swift

**언제 쓰지 말 것**:
- 공개 API (외부 개발자 대상) → REST/GraphQL 이 호환성 우수
- Browser 가 주 클라이언트 (gRPC-Web proxy 부담)
- Schema-less / 빠른 prototyping → JSON 이 유리

**난이도**: 중간~높음

**예제** (Protobuf + Kotlin gRPC server + client):
```protobuf
// user.proto
syntax = "proto3";
package user.v1;

service UserSvc {
  rpc GetUser(GetUserReq) returns (User);
  rpc WatchUsers(WatchReq) returns (stream UserEvent);  // server stream
  rpc Chat(stream ChatMsg) returns (stream ChatMsg);    // bidi stream
}

message GetUserReq { string id = 1; }
message User { string id = 1; string name = 2; int32 age = 3; }
```

```kotlin
// Server (Kotlin coroutines)
class UserService : UserSvcGrpcKt.UserSvcCoroutineImplBase() {
    override suspend fun getUser(req: GetUserReq): User =
        repo.find(req.id)?.toProto() ?: throw StatusException(Status.NOT_FOUND)

    override fun watchUsers(req: WatchReq): Flow<UserEvent> =
        repo.changeFeed(req.filter)  // server streams as Flow
}

// Client
val channel = ManagedChannelBuilder.forAddress("user-svc", 50051).usePlaintext().build()
val stub = UserSvcGrpcKt.UserSvcCoroutineStub(channel)
    .withDeadlineAfter(2, TimeUnit.SECONDS)

val user: User = stub.getUser(getUserReq { id = "42" })
stub.watchUsers(watchReq {}).collect { event -> println(event) }
```

**관련 패턴**: [REST](#rest) / [GraphQL](#graphql) (대안), [networking.md / HTTP/2](networking.md), [`../security/security-crypto-ops.md` / mTLS](../security/security-crypto-ops.md), [reliability.md / Circuit Breaker](reliability.md)

---

<a id="websocket-api"></a>

## 4. WebSocket

**목적/정의**: IETF RFC 6455 (2011) 가 정의한 단일 TCP connection 위의 **full-duplex bidirectional** 통신 프로토콜. HTTP/1.1 Upgrade handshake 로 시작 → frame 기반 양방향 메시지. 채팅·실시간 협업·라이브 시세의 표준 transport.

> [networking.md / WebSocket](networking.md) 가 transport 본체 (RFC 6455 frame 구조) 를 다룬다면 본 항목은 **API 스타일** 관점 — Socket.IO / Phoenix Channels / STOMP 같은 application-layer 프레임워크 선택.

**메커니즘**:
- **Handshake**: `GET /chat HTTP/1.1` + `Upgrade: websocket` + `Sec-WebSocket-Key` → 서버 `101 Switching Protocols` + `Sec-WebSocket-Accept`
- **Frame**: opcode (text / binary / ping / pong / close) + payload. masking (client→server 필수)
- **Subprotocol**: `Sec-WebSocket-Protocol: stomp, wamp, graphql-ws` 로 application protocol 협상
- **Keep-alive**: ping/pong frame 으로 idle connection 유지 + dead detection
- **Application 프레임워크**:
  - **Socket.IO**: auto-reconnect, fallback (long-polling), room/namespace 추상화 — Node 진영
  - **Phoenix Channels**: Elixir, presence tracking + pub/sub 내장
  - **STOMP** (Spring): pub/sub 의미론을 frame 으로 표준화
  - **graphql-ws / graphql-transport-ws**: GraphQL Subscription transport

**장점**:
- True bidirectional + low latency (handshake 1회 후 frame 만 주고받음)
- Browser native 지원 (`new WebSocket(url)`)
- HTTP 인프라 통과 (port 80/443 + Upgrade handshake)
- 텍스트 / binary 모두 가능

**단점·트레이드오프**:
- Stateful → 수평 확장 시 sticky session 또는 외부 pub/sub (Redis) 필요
- HTTP 캐싱 / proxy 와 호환성 떨어짐
- 재연결 / 메시지 순서 / 중복 처리 직접 구현 (Socket.IO 가 일부 해결)
- 부하 분산 시 connection draining 어려움 (deploy 마다 dropped)
- Mobile 환경: 배터리 / 절전 모드에서 connection 끊김 빈번

**활용 예시**:
- Slack, Discord, WhatsApp Web — 채팅
- Figma, Google Docs — 협업 편집 (CRDT + WebSocket)
- Coinbase / Binance — 실시간 시세
- GraphQL Subscription (Apollo, graphql-ws)

**언제 쓰지 말 것**:
- Server → client 단방향 알림 → SSE 가 더 단순
- Request/response 만 필요 → REST 또는 gRPC
- 매우 짧은 메시지 + 매우 많은 클라이언트 (수십만) → MQTT, raw TCP, 또는 [WebTransport](#webtransport) 고려

**난이도**: 중간

**예제** (Kotlin Ktor + browser client):
```kotlin
// Server (Ktor)
fun Application.chat() = install(WebSockets) {
    pingPeriod = Duration.ofSeconds(15)
    timeout = Duration.ofSeconds(60)
}.let {
    routing {
        val sessions = ConcurrentHashMap<String, DefaultWebSocketServerSession>()
        webSocket("/ws/chat/{room}") {
            val room = call.parameters["room"]!!
            val id = UUID.randomUUID().toString()
            sessions[id] = this
            try {
                for (frame in incoming) {
                    if (frame is Frame.Text) {
                        val msg = frame.readText()
                        sessions.values.forEach { it.send("[$id] $msg") }  // broadcast
                    }
                }
            } finally {
                sessions.remove(id)
            }
        }
    }
}
```

```javascript
// Browser
const ws = new WebSocket('wss://api.example.com/ws/chat/general');
ws.onopen = () => ws.send('hello');
ws.onmessage = (e) => console.log(e.data);
ws.onclose = (e) => console.log('closed', e.code, e.reason);
```

**관련 패턴**: [SSE](#server-sent-events) (단방향 대안), [WebTransport](#webtransport) (QUIC 후속), [networking.md / WebSocket transport](networking.md), [GraphQL Subscription](#graphql)

---

<a id="server-sent-events"></a>

## 5. Server-Sent Events (SSE)

**목적/정의**: HTML5 표준 (Living Standard, EventSource API) 이 정의한 **server→client 단방향 long-lived HTTP stream**. `Content-Type: text/event-stream` 으로 텍스트 이벤트를 흘려보내는 가장 단순한 streaming 스타일. 자동 재연결·event ID resume 내장.

**메커니즘**:
- **HTTP response 가 끝나지 않음**: 서버가 `Content-Type: text/event-stream` + chunked transfer 로 응답 → connection 유지하며 event 송신
- **이벤트 형식** (텍스트):
  ```
  id: 42
  event: priceUpdate
  data: {"symbol":"BTC","price":67000}

  ```
  (빈 줄로 이벤트 구분)
- **Auto-reconnect**: 브라우저 `EventSource` 가 disconnect 시 자동 재연결 (기본 3초). 서버는 `retry: 5000` 으로 override 가능
- **Resume**: 마지막 받은 `id` 를 `Last-Event-ID` 헤더로 재요청 → 서버가 그 지점부터 재전송
- **Text only**: binary 불가 (base64 인코딩 우회)
- **HTTP/1.1 한계**: 브라우저당 6 connection 제한 → HTTP/2 위에서는 multiplexing 으로 완화

**장점**:
- 매우 단순. WebSocket 대비 학습 / 구현 비용 압도적으로 낮음
- Browser native (`EventSource`) + auto-reconnect + resume 내장
- HTTP 그대로 → proxy / firewall / CDN / observability 모두 호환
- Stateless 에 가깝게 운영 가능 (event store + Last-Event-ID 로 resume)

**단점·트레이드오프**:
- 단방향 (client→server 는 별도 POST 필요)
- Text only (binary 비효율)
- HTTP/1.1 환경에서 connection 6개 제한
- IE / 일부 corporate proxy 가 long-lived connection 차단
- 메시지 순서·중복·신뢰성 직접 보장 필요

**활용 예시**:
- ChatGPT 응답 streaming (OpenAI API `stream=true`)
- Anthropic Claude API streaming
- GitHub Actions log streaming
- Twitter / Mastodon firehose
- Server-side notification / 시세 push

**언제 쓰지 말 것**:
- 양방향 실시간 (채팅, 협업) → WebSocket
- Binary 대용량 stream → gRPC server-streaming
- 일회성 응답 → 일반 REST

**난이도**: 낮음

**예제** (Kotlin Ktor + browser EventSource):
```kotlin
// Server
fun Application.sseRoute() = routing {
    get("/sse/prices") {
        call.respondTextWriter(ContentType.parse("text/event-stream")) {
            var id = 0
            while (true) {
                val price = priceFeed.next()  // suspending
                write("id: ${++id}\n")
                write("event: priceUpdate\n")
                write("data: ${price.toJson()}\n\n")
                flush()
            }
        }
    }
}
```

```javascript
// Browser
const es = new EventSource('/sse/prices');
es.addEventListener('priceUpdate', (e) => {
  const p = JSON.parse(e.data);
  console.log(p.symbol, p.price);
});
es.onerror = (e) => console.warn('reconnecting...');  // auto-reconnect by browser
```

```bash
# curl
curl -N -H 'Accept: text/event-stream' https://api.example.com/sse/prices
```

**관련 패턴**: [WebSocket](#websocket-api) (양방향 대안), [Webhook](#webhook) (server→server push), [ai-llm.md / Streaming response](ai-llm.md)

---

<a id="webhook"></a>

## 6. Webhook (HTTP Push / Reverse API)

**목적/정의**: 서버가 클라이언트(보통 다른 서버) 의 HTTP endpoint 로 이벤트를 **POST 로 push** 하는 비동기 통보 패턴. "API 의 반대" — 호출 방향이 거꾸로. polling 을 push 로 전환하는 가장 흔한 수단.

**메커니즘**:
- **등록**: 수신자가 URL 등록 (`https://my.app/webhooks/stripe`)
- **이벤트 발생 시**: 발행자가 `POST URL` + JSON body 로 전송
- **인증**: 보통 HMAC signature (`X-Hub-Signature-256: sha256=...`) 또는 mTLS. body + 비밀키로 HMAC 계산 → 수신자가 검증
- **Retry policy**: 5xx / timeout 시 재시도 (exponential backoff). GitHub 은 ~5회, Stripe 는 3일간 재시도
- **At-least-once + idempotency**: 중복 도착 가능 → 수신자가 이벤트 ID 로 dedupe
- **Replay attack 방어**: timestamp 헤더 + tolerance window (Stripe 5분)
- **Verification challenge**: 등록 시 수신 URL 에 GET / POST 로 echo challenge 보내 소유 확인 (Slack, Facebook 패턴)
- **Synchronous vs async**: 수신자는 즉시 2xx 반환 → 본 처리는 백그라운드 queue 로 (timeout 회피)

**장점**:
- Polling 제거 → 트래픽·지연 감소 (이벤트 발생 즉시 통보)
- 발행자·수신자 decoupled (수신자가 자신의 URL 만 등록)
- HTTP 인프라 그대로 사용 → 별도 protocol 학습 불필요
- 외부 SaaS 통합의 사실상 표준

**단점·트레이드오프**:
- 수신자가 public endpoint 필요 → 사내 시스템은 reverse tunnel (ngrok, Cloudflare Tunnel) 또는 polling 으로 우회
- At-least-once → idempotency 필수
- Signature verification 누락 시 위장 공격 (random POST 가능)
- 재시도 중 ordering 보장 어려움 → 수신자가 sequence number 처리
- 수신자 다운 시 backlog → DLQ + replay 메커니즘 필요
- 디버깅 어려움 (서버에서 발생, 추적 도구 부족)

**활용 예시**:
- GitHub webhook (push / PR / issue 이벤트)
- Stripe webhook (payment_intent.succeeded 등)
- Slack Event API, Discord, Twilio
- CI/CD 트리거, payment gateway 통보

**언제 쓰지 말 것**:
- Bidirectional / interactive → WebSocket
- Browser 가 수신자 → SSE (브라우저는 inbound 불가)
- 수십만 수신자 fan-out → pub/sub broker (Kafka, SNS)

**난이도**: 낮음~중간 (signature / retry / idempotency 가 모든 함정의 집합)

**예제** (Stripe webhook 수신 — Kotlin Ktor):
```kotlin
fun Application.stripeWebhook(secret: String) = routing {
    post("/webhooks/stripe") {
        val sig = call.request.header("Stripe-Signature") ?: return@post call.respond(HttpStatusCode.Unauthorized)
        val body = call.receiveText()

        // HMAC-SHA256 verify
        val (t, v1) = sig.split(",").map { it.split("=") }
            .associate { it[0] to it[1] }.let { it["t"]!! to it["v1"]!! }
        val payload = "$t.$body"
        val expected = Mac.getInstance("HmacSHA256").apply {
            init(SecretKeySpec(secret.toByteArray(), "HmacSHA256"))
        }.doFinal(payload.toByteArray()).joinToString("") { "%02x".format(it) }
        if (!MessageDigest.isEqual(expected.toByteArray(), v1.toByteArray()))
            return@post call.respond(HttpStatusCode.Unauthorized)

        // Replay window (5분)
        if (System.currentTimeMillis() / 1000 - t.toLong() > 300)
            return@post call.respond(HttpStatusCode.BadRequest)

        val event = Json.decodeFromString<StripeEvent>(body)
        if (eventStore.exists(event.id)) {  // idempotency
            return@post call.respond(HttpStatusCode.OK)
        }
        eventStore.save(event.id)
        queue.enqueue(event)  // process async
        call.respond(HttpStatusCode.OK)
    }
}
```

**관련 패턴**: [SSE](#server-sent-events) (browser inbound 대안), [integration.md / Pub-Sub · DLQ](integration.md), [distributed.md / Idempotency Key · Outbox](distributed.md), [`../security/security-crypto-ops.md` / HMAC](../security/security-crypto-ops.md)

---

<a id="json-rpc"></a>

## 7. JSON-RPC 2.0

**목적/정의**: JSON-RPC Working Group 의 2010 표준. **JSON 으로 method 호출**을 캡슐화한 가벼운 RPC 프로토콜. transport agnostic (HTTP / WebSocket / TCP / stdio 모두 가능). MCP (Model Context Protocol), Ethereum JSON-RPC, LSP (Language Server Protocol) 의 base.

**메커니즘**:
- **Request**:
  ```json
  {"jsonrpc":"2.0","method":"subtract","params":[42,23],"id":1}
  ```
  - `method`: 호출할 함수명
  - `params`: positional (`[..]`) 또는 named (`{..}`)
  - `id`: 요청 식별자 (정수 / 문자열)
- **Response (success)**: `{"jsonrpc":"2.0","result":19,"id":1}`
- **Response (error)**: `{"jsonrpc":"2.0","error":{"code":-32601,"message":"Method not found"},"id":1}`
- **Notification**: `id` 없는 request → 응답 없음 (fire-and-forget)
- **Batch**: request 를 array 로 묶어 한 번에 전송 → 동일 array 의 response 받음 (notification 은 응답 제외)
- **Error codes**: -32700 (Parse error), -32600 (Invalid request), -32601 (Method not found), -32602 (Invalid params), -32603 (Internal error), -32000~-32099 (구현 정의)

**장점**:
- 매우 단순한 spec (10페이지). 학습 / 구현 비용 최저
- Transport 독립 → HTTP, WebSocket, stdio (CLI tool) 어디서나
- Notification + Batch 지원 → fire-and-forget + round-trip 절약
- 사람이 읽기 쉬운 JSON

**단점·트레이드오프**:
- 강한 타입 없음 (JSON Schema 별도)
- REST 의 캐싱 / HTTP 의미론 (`GET` idempotency 등) 활용 불가
- 메타데이터 (auth, content-type) 는 transport 가 따로 처리
- 대량 데이터 / streaming 비효율 (단순 req/resp)

**활용 예시**:
- **MCP (Model Context Protocol)** — Anthropic, 2024. Claude 와 외부 도구 간 JSON-RPC over stdio / SSE
- **LSP (Language Server Protocol)** — Microsoft, VS Code ↔ 언어 서버 (stdio)
- **Ethereum JSON-RPC** — geth, Infura, Alchemy
- **DAP (Debug Adapter Protocol)**
- Bitcoin Core RPC, ZeroMQ + JSON-RPC

**언제 쓰지 말 것**:
- 공개 web API → REST/GraphQL 이 HTTP 의미론·캐싱 활용
- High-throughput 서비스 간 통신 → gRPC (binary + HTTP/2)
- Browser 가 직접 호출하는 application API → REST/GraphQL 이 도구 생태계 우세

**난이도**: 낮음

**예제** (Kotlin server over HTTP + curl):
```kotlin
@Serializable
data class JsonRpcReq(val jsonrpc: String = "2.0", val method: String,
                     val params: JsonElement? = null, val id: JsonElement? = null)
@Serializable
data class JsonRpcResp(val jsonrpc: String = "2.0", val result: JsonElement? = null,
                      val error: RpcError? = null, val id: JsonElement?)
@Serializable
data class RpcError(val code: Int, val message: String)

fun Application.jsonRpc(methods: Map<String, suspend (JsonElement?) -> JsonElement>) = routing {
    post("/rpc") {
        val req = call.receive<JsonRpcReq>()
        val fn = methods[req.method]
            ?: return@post call.respond(JsonRpcResp(error = RpcError(-32601, "Method not found"), id = req.id))
        try {
            val result = fn(req.params)
            if (req.id != null) call.respond(JsonRpcResp(result = result, id = req.id))
            // else: notification, no response
        } catch (e: Exception) {
            call.respond(JsonRpcResp(error = RpcError(-32603, e.message ?: "Internal error"), id = req.id))
        }
    }
}
```

```bash
curl -X POST https://api.example.com/rpc \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"subtract","params":[42,23],"id":1}'

# Batch
curl -X POST https://api.example.com/rpc \
  -H 'Content-Type: application/json' \
  -d '[
    {"jsonrpc":"2.0","method":"sum","params":[1,2,4],"id":"1"},
    {"jsonrpc":"2.0","method":"notify_hello","params":[7]},
    {"jsonrpc":"2.0","method":"subtract","params":[42,23],"id":"2"}
  ]'
```

**관련 패턴**: [REST](#rest) / [gRPC](#grpc) (대안), [ai-llm.md / Tool Use · MCP](ai-llm.md), [WebSocket](#websocket-api) (transport)

---

<a id="soap"></a>

## 8. SOAP (Simple Object Access Protocol)

**목적/정의**: W3C 가 표준화한 (1.1 = 2000, 1.2 = 2003) **XML 기반 메시지 프로토콜**. WSDL (Web Services Description Language) 로 service contract 를 정의하고 WS-* 확장 (Security / Transaction / Addressing / ReliableMessaging) 으로 엔터프라이즈 요구사항을 처리. REST 이전 web service 의 주류였고 현재는 레거시·금융·정부 시스템에 잔존.

**메커니즘**:
- **SOAP Envelope** (XML):
  ```xml
  <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
    <soap:Header>
      <wsse:Security>...</wsse:Security>
    </soap:Header>
    <soap:Body>
      <m:GetUser xmlns:m="http://example.com/user"><id>42</id></m:GetUser>
    </soap:Body>
  </soap:Envelope>
  ```
- **WSDL**: service / port / binding / operation / message / type 을 XML 로 기술. codegen 으로 client/server stub 생성 (`wsimport`, `svcutil`)
- **Transport**: 주로 HTTP POST, 단 SMTP / JMS / TCP 도 가능 (binding 으로 추상화)
- **WS-Security**: XML signature + encryption + UsernameToken / SAML / X.509 token. transport TLS 와 별개로 message-level security
- **WS-Transaction**: 분산 트랜잭션 (WS-AtomicTransaction)
- **WS-ReliableMessaging**: at-least-once / exactly-once
- **WS-Addressing**: routing / correlation header
- **SOAP fault**: `<soap:Fault>` 표준 오류 구조

**장점**:
- 강한 타입 (WSDL + XSD) + codegen → 컴파일 타임 안전성
- WS-Security 로 message-level 종단간 보안 (transport 중간 holder 가 일부 header 만 검사 가능)
- 분산 트랜잭션·신뢰성 메시징을 표준으로 지원
- 자동화된 client 생성 도구 (.NET, Java) 가 강력

**단점·트레이드오프**:
- XML 의 verbose 함 → payload 큼, parsing 비용 큼 (JSON 의 5-10배)
- WSDL · WS-* spec 의 복잡도 → 학습 곡선 매우 가파름
- Browser 친화적이지 않음 (XML parsing, CORS 처리 비표준)
- 표준 간 호환성 문제 (WCF ↔ JAX-WS interop 함정 다수)
- 도구 / 인력 풀 축소 → 신규 채택 거의 없음

**활용 예시**:
- 은행 SWIFT 게이트웨이, 결제 / 신용평가 (FICO, Experian)
- 정부 / 공공 (한국: 정부24, 미국: IRS / SSA)
- 의료 (HL7 일부)
- Salesforce SOAP API (REST 와 병행)
- 레거시 ESB (BizTalk, MuleSoft, WebSphere)

**언제 쓰지 말 것**:
- 신규 공개 API → REST / GraphQL
- 모바일 / web client → JSON 기반
- 마이크로서비스 간 호출 → gRPC
- 신규 프로젝트에서 enterprise 요구사항 (transaction / security) 이 진짜 필요한 경우는 거의 없음. 만약 필요해도 saga + JWT + mTLS 조합으로 대체

**난이도**: 높음

**예제** (Kotlin / JAX-WS client + WSDL 일부):
```xml
<!-- WSDL (발췌) -->
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" ...>
  <types>
    <xs:schema targetNamespace="http://example.com/user">
      <xs:element name="GetUser"><xs:complexType><xs:sequence>
        <xs:element name="id" type="xs:int"/>
      </xs:sequence></xs:complexType></xs:element>
    </xs:schema>
  </types>
  <portType name="UserPort">
    <operation name="GetUser">
      <input message="tns:GetUserRequest"/>
      <output message="tns:GetUserResponse"/>
    </operation>
  </portType>
</definitions>
```

```kotlin
// JAX-WS client (Java/Kotlin, generated by wsimport)
val service = UserService(URL("http://example.com/user?wsdl"))
val port = service.userPort
val user: User = port.getUser(42)
println("${user.name} (${user.age})")
```

```bash
# Raw SOAP request
curl -X POST https://example.com/user \
  -H 'Content-Type: application/soap+xml; charset=utf-8' \
  -H 'SOAPAction: "http://example.com/user/GetUser"' \
  -d '<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Body><GetUser xmlns="http://example.com/user"><id>42</id></GetUser></soap:Body>
</soap:Envelope>'
```

**관련 패턴**: [REST](#rest) (현대 대체), [gRPC](#grpc) (강한 타입 RPC 대체), [`../security/security-api-web.md`](../security/security-api-web.md), [integration.md / ESB](integration.md)

---

<a id="webtransport"></a>

## 9. WebTransport

**목적/정의**: W3C 가 표준화 중인 (Working Draft 2024) **QUIC 위의 차세대 양방향 통신 API**. WebSocket 의 후속 — HTTP/3 (QUIC) 의 multiplexed stream + unreliable datagram 을 브라우저 API 로 노출. 단일 transport 로 reliable streams + unreliable datagrams 동시 제공.

**메커니즘**:
- **Transport**: QUIC (RFC 9000) over UDP. TLS 1.3 통합 + 0-RTT + multi-stream (HoL blocking 없음)
- **API 표면**:
  - `WebTransport(url)` — 연결
  - `transport.createBidirectionalStream()` — TCP-like reliable stream
  - `transport.createUnidirectionalStream()` — server→client 또는 client→server
  - `transport.datagrams.writable / readable` — UDP-like unreliable datagram
- **Multi-stream**: 단일 connection 위 수백개 stream 병렬 → 한 stream 의 loss 가 다른 stream 에 영향 없음 (WebSocket / HTTP/1.1 의 HoL blocking 해결)
- **Datagram**: 손실 / 순서 뒤바뀜 허용, low-latency (게임 위치 update, 영상 프레임)
- **0-RTT resumption**: 이전 연결 정보로 즉시 데이터 전송 (단, replay 위험 있는 요청은 1-RTT 강제)
- **Connection migration**: IP / network 변경 (Wi-Fi → 모바일) 시 connection 유지

**장점**:
- HoL blocking 없음 → 다양한 우선순위 데이터 병렬 전송 (큰 파일 + 실시간 채팅 동시)
- Reliable + unreliable 한 transport 에서 선택 가능 (게임에 이상적)
- 0-RTT + connection migration → 모바일 환경 우수
- HTTP/3 인프라 (CDN, load balancer) 와 호환

**단점·트레이드오프**:
- Spec draft (2024 기준 Working Draft). 안정성·호환성 진행 중
- 브라우저 지원: Chrome 97+, Edge, 일부. Safari/Firefox 늦음
- 서버 측 구현 미성숙 (aioquic, quiche, msquic, Java net.javacrumbs)
- UDP 차단 환경 (corporate firewall) 에서 fallback 필요
- 디버깅 도구 부족 (Wireshark QUIC dissector 가 점차 개선)
- 학습 / 운영 곡선 가파름 (QUIC + multi-stream 의미론)

**활용 예시**:
- **Cloud Gaming**: GeForce Now, Xbox Cloud Gaming (저지연 게임 stream)
- **Video conferencing**: Zoom, Google Meet 일부 transport (WebRTC + WebTransport hybrid)
- **Real-time multiplayer game** (브라우저 기반)
- **Large file transfer + 동시 control channel**
- **HTTP/3 기반 raw streaming** (브라우저 ↔ media server)

**언제 쓰지 말 것**:
- 폭넓은 호환성 필요 (Safari / 구형 브라우저 / corporate 환경) → WebSocket 또는 SSE
- 단순 req/resp → REST / gRPC
- 서버 인프라가 HTTP/3 미지원 → 도입 시기상조

**난이도**: 매우 높음

**예제** (JavaScript browser + Kotlin server with aioquic-equivalent):
```javascript
// Browser (Chrome 97+)
const transport = new WebTransport('https://game.example.com:4433/play');
await transport.ready;

// Reliable bidirectional stream (chat / control)
const stream = await transport.createBidirectionalStream();
const writer = stream.writable.getWriter();
await writer.write(new TextEncoder().encode('JOIN room42'));

const reader = stream.readable.getReader();
const { value } = await reader.read();
console.log(new TextDecoder().decode(value));

// Unreliable datagram (player position 60Hz)
setInterval(async () => {
  const writer = transport.datagrams.writable.getWriter();
  await writer.write(new Float32Array([player.x, player.y, player.z]).buffer);
  writer.releaseLock();
}, 16);

// Receive datagrams
const dgReader = transport.datagrams.readable.getReader();
while (true) {
  const { value, done } = await dgReader.read();
  if (done) break;
  applyOpponentPosition(new Float32Array(value));
}
```

```kotlin
// Server (pseudo, using a QUIC library)
val server = QuicServerBuilder()
    .bind(InetSocketAddress(4433))
    .tlsCert("server.crt", "server.key")
    .alpn("h3", "wt")  // WebTransport via HTTP/3
    .build()

server.onConnection { conn ->
    conn.onBidirectionalStream { stream ->
        scope.launch {
            stream.readUntil('\n').let { msg ->
                stream.write("ack: $msg\n".toByteArray())
            }
        }
    }
    conn.onDatagram { bytes ->
        broadcastToRoom(conn.room, bytes)  // unreliable fan-out
    }
}
```

**관련 패턴**: [WebSocket](#websocket-api) (현 대안 + 후속 관계), [networking.md / QUIC · HTTP/3](networking.md), [game-dev.md / Netcode](game-dev.md), [networking.md / Reliable UDP](networking.md)
