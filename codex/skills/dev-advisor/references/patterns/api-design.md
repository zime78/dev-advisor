# API 설계 패턴 (API Design Patterns)

REST / gRPC / GraphQL 같은 *프로토콜* 과 별개의 **API 설계 의사결정** 14 항목. JJ Geewax *API Design Patterns* (Manning, 2021) + Google API Design Guide (AIP) 표준.

**원전 참고**:
- JJ Geewax — *API Design Patterns* (Manning, 2021)
- Google API Improvement Proposals — https://google.aip.dev
- Roy Fielding — *Architectural Styles and the Design of Network-based Software Architectures* (Ph.D. dissertation, 2000)
- IETF RFC 7807 (Problem Details), RFC 8594 (Sunset header)
- Microsoft REST API Guidelines

**관련 카탈로그**:
- [distributed.md](distributed.md) — API Gateway / BFF / Service Mesh / Idempotency Key (이미 있음 — cross-link)
- [reliability.md](reliability.md) — Rate Limiter / Backpressure
- [`../security/security-api-web.md`](../security/security-api-web.md) — per-Identity Rate Limit / HMAC Signing
- [`../algorithms/distributed.md`](../algorithms/distributed.md) — Consistent Hashing (rate limit 분산)

---

<a id="1-richardson-maturity"></a>
## 1. Richardson Maturity Model (Level 0~3)

**목적**: REST API의 RESTful 성숙도를 4 단계(0~3)로 측정하여, 어느 수준까지 REST 원칙을 적용할지를 명시적으로 결정합니다. Leonard Richardson(2008) 제안, Martin Fowler가 정리.

**메커니즘**:
- **Level 0 — The Swamp of POX**: 단일 endpoint + HTTP를 RPC 터널로만 사용. 모든 요청이 `POST /api`로 가고 body로 함수명을 전달. SOAP / XML-RPC 가 전형.
- **Level 1 — Resources**: 리소스마다 별개 URI. `POST /orders/123` / `POST /users/456`. HTTP method 는 여전히 POST 만 사용.
- **Level 2 — HTTP Verbs**: HTTP method (GET/POST/PUT/PATCH/DELETE)와 status code (200/201/204/400/404/409/500)를 의미적으로 사용. 대부분 "REST API"는 여기에 머무름.
- **Level 3 — Hypermedia Controls (HATEOAS)**: 응답에 다음에 가능한 action 의 hyperlink 포함. 클라이언트가 URI 구조를 hard-code 하지 않음.

**장점**:
- 팀의 REST 이해도를 객관적으로 진단할 수 있는 척도 제공
- Level 2 = "well-behaved HTTP API" 의 최소 합의선
- Level 3 = HATEOAS 로 클라이언트-서버 디커플링 극대화

**단점/주의**:
- Level 3 (HATEOAS) 의 ROI 는 논쟁적. 대부분 SPA / Mobile 클라이언트는 OpenAPI spec 으로 URI 를 hard-code 하는 게 현실
- 본 모델은 "성숙도" 라는 단어 때문에 마치 Level 3 가 항상 옳다는 오해를 부름. Fielding 본인은 "Level 3 가 아니면 REST 가 아니다"라는 입장이지만, Geewax 는 실용적 trade-off 를 인정

**표준 인용**:
- Leonard Richardson — *Justice Will Take Us Millions Of Intricate Moves* (QCon 2008)
- Martin Fowler — [Richardson Maturity Model](https://martinfowler.com/articles/richardson-maturity-model.html) (2010)
- Geewax §1.2 — "RESTful API patterns"

**HTTP 예제** — Level 별 동일 기능 (주문 취소):

```http
# Level 0 — RPC tunnel
POST /api HTTP/1.1
Content-Type: application/json

{"method": "cancelOrder", "params": {"orderId": "ord_123"}}

# Level 1 — Resource URI but only POST
POST /orders/ord_123/cancel HTTP/1.1

# Level 2 — HTTP verbs + status codes
DELETE /orders/ord_123 HTTP/1.1
→ 204 No Content   (성공)
→ 404 Not Found    (없는 주문)
→ 409 Conflict     (이미 출고됨 — 취소 불가)

# Level 3 — HATEOAS (응답에 next-action link)
GET /orders/ord_123 HTTP/1.1
→ 200 OK
{
  "id": "ord_123",
  "status": "PAID",
  "_links": {
    "self":   { "href": "/orders/ord_123" },
    "cancel": { "href": "/orders/ord_123", "method": "DELETE" },
    "ship":   { "href": "/orders/ord_123/shipments", "method": "POST" }
  }
}
```

**관련 패턴**: [HATEOAS](#2-hateoas) · [Resource-Oriented Design](#3-resource-oriented-design) · [Resource Naming](#10-resource-naming)

---

<a id="2-hateoas"></a>
## 2. HATEOAS (Hypermedia as the Engine of Application State)

**목적**: 응답 본문에 "현재 상태에서 가능한 다음 action 의 link" 를 포함시켜, 클라이언트가 URI 구조나 상태 전이 규칙을 hard-code 하지 않고 서버 응답만 따라가도 동작하게 만듭니다. Fielding 박사학위 논문 §5.1.5 의 핵심.

**메커니즘**:
- 응답에 `_links` (HAL) / `links` (JSON:API) / `actions` (Siren) 필드를 포함
- 각 link 는 `rel` (관계명) + `href` (URI) + 선택적 `method` / `type` / `templated` 메타
- 클라이언트는 root endpoint (`/`) 만 알면 됨 — 나머지는 link 추적
- 상태 전이가 서버 응답에 명시 → 클라이언트는 "지금 무엇을 할 수 있는가" 만 보면 됨

**Hypermedia 포맷 3 종**:
- **HAL** (RFC draft, Mike Kelly) — `_links` 와 `_embedded` 두 reserved key. 가장 단순.
- **JSON:API** (jsonapi.org) — `links` / `relationships` / `included`. 데이터 + 관계 + 메타 명확 분리.
- **Siren** — `actions` 필드로 HTTP method/parameters 까지 표현. 가장 풍부하지만 무거움.

**장점**:
- 서버가 URI 구조를 변경해도 클라이언트가 깨지지 않음 (link 만 따라감)
- 상태 전이가 self-documenting — 별도 문서 없이 응답으로 "다음에 무엇을 할 수 있는지" 알 수 있음
- API discoverability 극대화

**단점/주의**:
- 대부분의 SPA / 모바일 클라이언트는 어차피 OpenAPI 로 URI 를 generate 하므로 ROI 가 낮음
- 응답 크기 증가 (link 메타데이터 overhead)
- 클라이언트 SDK 가 hypermedia-aware 해야 효과 — 단순 fetch + JSON.parse 로는 link 가 그저 잡음
- 검색·캐싱 친화도 떨어짐 (URI 가 응답마다 다를 수 있어 cache key 불안정)

**표준 인용**:
- Roy Fielding — *Architectural Styles* §5.1.5 (2000)
- IETF draft — *JSON Hypertext Application Language (HAL)* (Kelly, 2013)
- [jsonapi.org](https://jsonapi.org) v1.1
- [Siren spec](https://github.com/kevinswiber/siren)

**HTTP 예제** — HAL 포맷:

```http
GET /accounts/acc_42 HTTP/1.1
Accept: application/hal+json

→ 200 OK
Content-Type: application/hal+json

{
  "id": "acc_42",
  "balance": 12000,
  "currency": "KRW",
  "_links": {
    "self":     { "href": "/accounts/acc_42" },
    "deposit":  { "href": "/accounts/acc_42/deposits",    "method": "POST" },
    "withdraw": { "href": "/accounts/acc_42/withdrawals", "method": "POST" },
    "history":  { "href": "/accounts/acc_42/transactions", "templated": false }
  },
  "_embedded": {
    "owner": {
      "id": "usr_7",
      "name": "Jin",
      "_links": { "self": { "href": "/users/usr_7" } }
    }
  }
}
```

**관련 패턴**: [Richardson Maturity (Level 3)](#1-richardson-maturity) · [Resource-Oriented Design](#3-resource-oriented-design)

---

<a id="3-resource-oriented-design"></a>
## 3. Resource-Oriented Design (Google AIP)

**목적**: API 를 "리소스의 컬렉션" 으로 모델링하고, 모든 동작을 표준 5 method (List/Get/Create/Update/Delete) + 필요한 경우 custom method 로 표현합니다. Google Cloud API 전체가 이 패턴.

**메커니즘**:
- **Resource** = 명명 가능한 영속 entity. URI 가 곧 이름. (e.g. `publishers/p1/books/b1`)
- **Collection** = 같은 타입 리소스의 부모. URI 패턴 `<collection>/<id>/<collection>/<id>`
- **Standard methods** (AIP-131~135):
  - `List`   → `GET /publishers/p1/books`
  - `Get`    → `GET /publishers/p1/books/b1`
  - `Create` → `POST /publishers/p1/books` (body 에 리소스)
  - `Update` → `PATCH /publishers/p1/books/b1` (partial) / `PUT` (full replace)
  - `Delete` → `DELETE /publishers/p1/books/b1`
- **Custom methods** (AIP-136) — 표준 5 개로 표현 불가한 동작. URI 마지막에 `:verb` (colon prefix) 로 표시.
  - `POST /books/b1:publish`
  - `POST /books/b1:archive`
- Resource 이름은 **명사 복수형** (`books` not `book`). Verb 는 path 마지막 custom method 만.

**장점**:
- URI 가 일관됨 — 새 리소스를 추가해도 패턴이 같음
- AIP / Google Cloud SDK / gRPC transcoding 과 호환
- 자동 SDK 생성기 (OpenAPI Generator, protoc-gen-openapi) 가 잘 동작
- LSP/REST/gRPC 트랜스포트를 동일 리소스 모델로 매핑 가능

**단점/주의**:
- 모든 동작을 5 method 로 끼워맞추려다 보면 부자연스러운 모델링 발생 (e.g. "send email" 을 `EmailMessage` 리소스 create 로 표현)
- 도메인 동사가 강한 워크플로 (e.g. "approve / reject / escalate") 는 custom method 가 폭증
- Custom method colon syntax 가 일부 프록시 / WAF 에서 호환 이슈

**표준 인용**:
- Google AIP-121 — *Resource-oriented design*
- Google AIP-131~135 — Standard methods
- Google AIP-136 — Custom methods
- Geewax §3 — "API as resources"

**HTTP 예제**:

```http
# Standard methods
GET    /publishers/p1/books              # List
GET    /publishers/p1/books/b1           # Get
POST   /publishers/p1/books              # Create
PATCH  /publishers/p1/books/b1           # Update (partial)
DELETE /publishers/p1/books/b1           # Delete

# Custom methods (colon prefix, lowerCamelCase verb)
POST   /publishers/p1/books/b1:publish
POST   /publishers/p1/books/b1:archive
POST   /publishers/p1/books:batchCreate

# Hierarchical naming — publishers → books → reviews
GET    /publishers/p1/books/b1/reviews/r5
```

```kotlin
// Spring controller mapping
@RestController
@RequestMapping("/publishers/{publisherId}/books")
class BookController(private val repo: BookRepository) {
    @GetMapping              fun list(@PathVariable publisherId: String): List<Book> = repo.list(publisherId)
    @GetMapping("/{id}")     fun get(@PathVariable publisherId: String, @PathVariable id: String): Book = repo.get(publisherId, id)
    @PostMapping             fun create(@PathVariable publisherId: String, @RequestBody body: Book): Book = repo.create(publisherId, body)
    @PatchMapping("/{id}")   fun update(@PathVariable id: String, @RequestBody patch: BookPatch): Book = repo.patch(id, patch)
    @DeleteMapping("/{id}")  fun delete(@PathVariable id: String) = repo.delete(id)

    // Custom method — colon syntax handled by Spring path
    @PostMapping("/{id}:publish")
    fun publish(@PathVariable id: String): Book = repo.publish(id)
}
```

**관련 패턴**: [Resource Naming](#10-resource-naming) · [Richardson Maturity](#1-richardson-maturity) · [Long-Running Operation](#8-long-running-operation)

---

<a id="4-api-versioning"></a>
## 4. API Versioning

**목적**: API 의 breaking change 를 안전하게 도입하기 위해 버전을 명시적으로 관리하여, 기존 클라이언트가 깨지지 않으면서 새 버전을 병행 운영합니다.

**메커니즘 — 4 전략**:

| 전략 | 예시 | 장점 | 단점 |
|---|---|---|---|
| **URI Path** | `GET /v1/users/42` | 가장 직관적, curl/브라우저 친화 | URI 가 "리소스 이름" 이라는 REST 원칙 위배 (버전이 들어감) |
| **Custom Header** | `Accept: application/vnd.acme.v2+json` | URI 가 깨끗, 같은 리소스의 표현만 바뀌는 게 의미적으로 정확 | 디버깅 어려움, 캐시 키 복잡 |
| **Accept Header (media type)** | `Accept: application/vnd.github.v3+json` | HTTP 표준 content negotiation | 클라이언트 SDK 가 header 를 까먹기 쉬움 |
| **Query Parameter** | `GET /users/42?version=2` | 빠르게 토글 | 캐시 친화도 낮음, 일반적이지 않음 |

**SemVer for API**:
- **MAJOR** (v1 → v2): breaking change. 별도 endpoint 운영 + 마이그레이션 가이드 필수
- **MINOR**: backward-compatible addition (새 field / 새 endpoint). 기존 v1 안에서 처리
- **PATCH**: bug fix. 클라이언트 영향 없음

**Breaking change 정의** (Geewax §24):
- 필드 제거 / rename
- 응답 타입 변경 (string → int)
- 필수 파라미터 추가
- HTTP method / status code 의미 변경
- 에러 응답 구조 변경

**Non-breaking** (안전한 추가):
- optional 필드 추가
- 새 endpoint 추가
- 새 enum value 추가 (단, 클라이언트가 unknown enum 을 graceful 처리해야 함)

**장점**:
- 클라이언트 마이그레이션 시간 확보 (deprecation window)
- 신·구 버전 병행 운영 가능
- Breaking change 의 영향 범위 명시적

**단점/주의**:
- 버전 수만큼 코드 / 인프라 부담 증가
- 너무 자주 메이저 버전 올리면 클라이언트 피로 → 가능한 한 minor addition 으로 해결
- 내부 마이크로서비스 API 는 over-versioning 함정 — 모든 caller 가 같은 회사라면 trunk-based 가 더 간단

**표준 인용**:
- GitHub API — Accept header 방식 (`application/vnd.github.v3+json`)
- Stripe — URI path + 날짜 기반 (`2024-06-20`)
- Google Cloud — URI path (`/v1/`, `/v1beta1/`)
- Microsoft REST Guidelines §12 — Versioning

**HTTP 예제**:

```http
# URI Path versioning (가장 흔함)
GET /v1/users/42 HTTP/1.1
GET /v2/users/42 HTTP/1.1

# Custom Accept media type (GitHub style)
GET /users/42 HTTP/1.1
Accept: application/vnd.acme.v2+json

# Stripe-style 날짜 버전 (header)
GET /v1/charges/ch_123 HTTP/1.1
Stripe-Version: 2024-06-20

# Non-breaking addition — v1 에 새 field 추가 (버전 안 올림)
GET /v1/users/42 HTTP/1.1
→ {
    "id": 42,
    "name": "Jin",
    "preferredLanguage": "ko"   // v1.5 에서 추가됨, 기존 클라이언트는 무시
  }
```

```kotlin
// Spring — URI versioning
@RestController
class UserControllerV1 {
    @GetMapping("/v1/users/{id}")
    fun getV1(@PathVariable id: String): UserDtoV1 = ...
}

@RestController
class UserControllerV2 {
    @GetMapping("/v2/users/{id}")
    fun getV2(@PathVariable id: String): UserDtoV2 = ...   // breaking: name → firstName/lastName
}
```

**관련 패턴**: [API Deprecation & Sunset](#14-api-deprecation-sunset) · [Resource Naming](#10-resource-naming)

---

<a id="5-pagination-patterns"></a>
## 5. Pagination 패턴 3종 (Offset / Cursor / Keyset)

**목적**: 큰 컬렉션을 한 번에 전부 반환하지 않고 페이지 단위로 잘라 반환하여, 응답 크기 / 네트워크 비용 / DB 부하를 제어합니다.

**메커니즘 — 3 전략**:

### 5.1 Offset Pagination

```http
GET /books?offset=200&limit=50
```

- DB 쿼리: `SELECT * FROM books ORDER BY id LIMIT 50 OFFSET 200`
- **장점**: 직관적, "5 페이지로 점프" 가능, 총 개수 표시 쉬움
- **단점**:
  - **Deep page 비용**: `OFFSET 100000` 은 DB 가 10 만 행을 읽고 버림 (full scan)
  - **불안정**: 페이지를 넘기는 사이 새 행이 insert 되면 같은 항목이 두 번 나오거나 누락 (duplication / skipping)
  - 동적 데이터에 부적합

### 5.2 Cursor Pagination

```http
GET /books?cursor=eyJpZCI6MTAwMH0&limit=50
→ {
    "items": [...],
    "nextCursor": "eyJpZCI6MTA1MH0",
    "prevCursor": "eyJpZCI6OTUwfQ"
  }
```

- Cursor = 다음 페이지를 가리키는 **opaque token** (보통 base64-encoded JSON). 클라이언트는 내부 구조를 모름.
- **장점**:
  - 안정적 (cursor 가 정확한 위치를 가리킴 — duplication 없음)
  - 서버가 cursor 의미를 자유롭게 변경 가능 (opaque 라서)
  - 무한 스크롤 / 피드에 적합
- **단점**:
  - 임의 페이지 점프 불가 (next / prev 만)
  - 총 개수 알기 어려움
  - Cursor 위변조 방지 위해 서명 필요 (HMAC) — 비용

### 5.3 Keyset Pagination (Seek)

```http
GET /books?afterId=1000&limit=50
```

- DB 쿼리: `SELECT * FROM books WHERE id > 1000 ORDER BY id LIMIT 50`
- Cursor 와 유사하지만 cursor 가 **명시적인 indexed column 값** (id, created_at).
- **장점**:
  - 인덱스 활용 → deep page 도 O(log n)
  - 매우 빠름 (DB 가 OFFSET 건너뛰지 않음)
  - 안정적
- **단점**:
  - 정렬 기준이 고정되어야 함 (다중 정렬 어려움)
  - Tie-breaker 필요 (`created_at` 같으면 `id` 도 같이 비교)
  - 클라이언트가 cursor 의미를 알게 됨 (opaque 아님)

**선택 기준**:
- 관리자 대시보드 / 페이지 번호 UI → **Offset**
- 사용자 피드 / 무한 스크롤 → **Cursor**
- 대용량 데이터 + 단순 정렬 → **Keyset**

**표준 인용**:
- Google AIP-158 — *Pagination* (page_token / page_size)
- Twitter API — Cursor-based (since_id / max_id)
- Stripe API — Cursor-based (`starting_after` / `ending_before`)
- Markus Winand — *SQL Performance Explained* §7 (Keyset pagination 원전)

**HTTP 예제** — Keyset (가장 효율적):

```http
# 첫 요청
GET /books?orderBy=createdAt&limit=20 HTTP/1.1
→ 200 OK
{
  "items": [{ "id": "b_1", "createdAt": "2024-01-01" }, ...],
  "next": "/books?orderBy=createdAt&afterCreatedAt=2024-01-20&afterId=b_20&limit=20"
}

# 다음 페이지 — 서버가 준 next link 그대로 사용
GET /books?orderBy=createdAt&afterCreatedAt=2024-01-20&afterId=b_20&limit=20 HTTP/1.1
```

```kotlin
// Keyset pagination 구현
data class BookPage(val items: List<Book>, val nextCursor: String?)

fun listBooks(afterId: String?, limit: Int = 20): BookPage {
    val rows = if (afterId == null)
        db.query("SELECT * FROM books ORDER BY id LIMIT ?", limit + 1)
    else
        db.query("SELECT * FROM books WHERE id > ? ORDER BY id LIMIT ?", afterId, limit + 1)

    val hasMore = rows.size > limit
    val items = rows.take(limit)
    return BookPage(items, if (hasMore) items.last().id else null)
}
```

**관련 패턴**: [Filter/Sort/Field Selection](#11-filter-sort-fieldsel) · [Resource-Oriented Design](#3-resource-oriented-design)

---

<a id="6-idempotency-key-api"></a>
## 6. Idempotency Key (API 설계 관점)

**목적**: POST 처럼 본질적으로 비멱등한 메서드의 재시도 안전성을 확보하기 위해, 클라이언트가 발급한 unique key 를 HTTP 헤더로 전달하면 서버가 (key, response) 를 캐시하여 중복 요청을 한 번만 처리합니다. Stripe 가 표준 헤더 이름 `Idempotency-Key` 를 보편화.

> **distributed.md 의 Idempotency Key 와 차이**: distributed.md/§6 은 **시스템 관점** (Redis 캐시, TTL, exactly-once 보장). 본 항목은 **API 설계 관점** — HTTP 헤더 이름·response 헤더 표준·body hash 검증·response replay·status code 의미.

**메커니즘**:
- 클라이언트가 요청마다 unique key 생성 (UUIDv4 권장) → `Idempotency-Key: <uuid>` 헤더로 전송
- 서버가 (key, response body, response status) 를 저장소(Redis) 에 TTL 24h 로 캐시
- **첫 요청**: 정상 처리 후 결과를 저장. 응답에 `Idempotency-Replayed: false` 또는 동등 표시
- **재시도**: 같은 key 로 다시 오면 저장된 응답을 그대로 replay. status code 도 동일.
- **본문 검증 필수**: 같은 key 인데 body 가 다르면 → `422 Unprocessable Entity` (key 재사용 공격 방지)

**Stripe 의 추가 규칙** (산업 표준):
- TTL: 24 시간
- 멱등 응답에 `Idempotent-Replayed: true` 추가
- key 길이 제한: 1~255 자
- 4xx 응답도 캐시 (재시도해도 같은 4xx)
- 5xx 는 캐시 안 함 (다음 재시도가 성공할 수 있게)

**장점**:
- 결제 / 주문 같은 critical write API 의 네트워크 재시도 안전
- 클라이언트가 timeout 후 재시도해도 중복 결제 없음
- exactly-once 효과 (semantic, not transport)

**단점/주의**:
- key 저장소 필요 (Redis / DynamoDB) + 운영 부담
- **body hash 검증 누락 시 보안 취약** — 공격자가 다른 본문으로 같은 key 를 보내 cached response 를 훔쳐볼 수 있음
- TTL 너무 짧으면 재시도 안전성 약화, 너무 길면 메모리 폭증
- DELETE / PUT 같은 본래 멱등한 메서드에는 불필요

**표준 인용**:
- [Stripe API — Idempotent Requests](https://stripe.com/docs/api/idempotent_requests)
- [IETF draft-ietf-httpapi-idempotency-key-header](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)
- Geewax §27 — *Idempotency*

**HTTP 예제**:

```http
# 첫 요청
POST /v1/charges HTTP/1.1
Idempotency-Key: 8e3a4f8c-7b9d-4c2a-9e1f-1234567890ab
Content-Type: application/json

{ "amount": 5000, "currency": "krw", "source": "tok_visa" }

→ 200 OK
Idempotent-Replayed: false
{ "id": "ch_1Abc", "status": "succeeded", "amount": 5000 }

# 네트워크 타임아웃 후 재시도 — 같은 key, 같은 body
POST /v1/charges HTTP/1.1
Idempotency-Key: 8e3a4f8c-7b9d-4c2a-9e1f-1234567890ab
Content-Type: application/json

{ "amount": 5000, "currency": "krw", "source": "tok_visa" }

→ 200 OK
Idempotent-Replayed: true
{ "id": "ch_1Abc", "status": "succeeded", "amount": 5000 }   ← 같은 응답 (한 번만 결제됨)

# 같은 key, 다른 body — 공격 또는 클라이언트 버그
POST /v1/charges HTTP/1.1
Idempotency-Key: 8e3a4f8c-7b9d-4c2a-9e1f-1234567890ab
Content-Type: application/json

{ "amount": 999999, "currency": "krw", "source": "tok_evil" }

→ 422 Unprocessable Entity
{ "type": "idempotency_error", "message": "Body hash mismatch for given Idempotency-Key" }
```

```kotlin
// Ktor server interceptor
fun Application.idempotency(store: IdempotencyStore) {
    intercept(ApplicationCallPipeline.Plugins) {
        val key = call.request.header("Idempotency-Key") ?: return@intercept
        val bodyHash = call.receiveText().sha256()
        val cached = store.get(key)
        if (cached != null) {
            if (cached.bodyHash != bodyHash) {
                call.respond(HttpStatusCode.UnprocessableEntity, mapOf("type" to "idempotency_error"))
                finish(); return@intercept
            }
            call.response.header("Idempotent-Replayed", "true")
            call.respondText(cached.response, status = HttpStatusCode.fromValue(cached.status))
            finish()
        }
    }
}
```

**관련 패턴**: [distributed.md/§6 Idempotency Key](distributed.md#6-idempotency-key) (시스템 관점) · [Bulk/Batch Operation](#7-bulk-batch-operation)

---

<a id="7-bulk-batch-operation"></a>
## 7. Bulk / Batch Operation

**목적**: 같은 종류의 동작을 N 번 호출하는 대신 한 번의 요청으로 묶어 처리하여, 네트워크 round-trip / 인증 비용 / 트랜잭션 overhead 를 줄입니다.

**메커니즘 — 2 변형**:

### 7.1 Atomic Batch (all-or-nothing)
- 한 트랜잭션으로 묶어 모두 성공 또는 모두 실패
- 응답: 단일 status code (`200` / `4xx`)
- 적합: 회계 transfer, 인벤토리 차감

### 7.2 Partial Failure Batch (per-item result)
- 항목별로 독립 처리 → 일부 성공 / 일부 실패 가능
- HTTP status: `207 Multi-Status` (WebDAV) 또는 `200 OK` 으로 통일 후 body 에 per-item result
- 적합: 메시지 발송, 알림, bulk import

**Google AIP-231~233 의 batch 표준**:
- `:batchGet` — 여러 리소스 동시 조회
- `:batchCreate` — 여러 리소스 동시 생성 (atomic)
- `:batchDelete` — 여러 리소스 동시 삭제
- Custom method 로 colon prefix 표시
- 요청 body 에 `requests: [...]` 배열

**장점**:
- 네트워크 효율 (N 회 → 1 회)
- 인증 / rate-limit / observability overhead 절감
- 트랜잭션 묶음으로 일관성 보장 (atomic 변형)

**단점/주의**:
- Partial failure 처리 복잡도 증가 (어느 항목이 실패했는지 클라이언트가 매핑해야 함)
- 응답 크기 폭증 가능 — 페이지네이션과 결합 어려움
- 단일 거대 요청이 timeout / 메모리 폭발 위험 → 최대 batch size 제한 필수 (e.g. 1000 items)
- 부분 실패 시 재시도 전략이 까다로움 (성공한 것은 건너뛰고 실패한 것만)

**표준 인용**:
- Google AIP-231 (`Batch methods: Get`), AIP-232 (`Batch methods: Create`)
- WebDAV RFC 4918 §11 — `207 Multi-Status`
- Geewax §18 — *Batch Operations*

**HTTP 예제**:

```http
# Atomic batch — all-or-nothing
POST /v1/publishers/p1/books:batchCreate HTTP/1.1
Content-Type: application/json

{
  "requests": [
    { "book": { "title": "Book A" } },
    { "book": { "title": "Book B" } },
    { "book": { "title": "Book C" } }
  ]
}

→ 200 OK   (모두 성공)
{ "books": [ { "id": "b1", ... }, { "id": "b2", ... }, { "id": "b3", ... } ] }

→ 400 Bad Request   (하나라도 실패 시 전체 롤백)
{ "type": "validation_error", "failedIndex": 1, "message": "title required" }

# Partial-failure batch — per-item status
POST /v1/notifications:batchSend HTTP/1.1

{
  "requests": [
    { "userId": "u1", "message": "hi" },
    { "userId": "u2", "message": "hello" },
    { "userId": "u_invalid", "message": "x" }
  ]
}

→ 207 Multi-Status
{
  "results": [
    { "index": 0, "status": 200, "messageId": "m1" },
    { "index": 1, "status": 200, "messageId": "m2" },
    { "index": 2, "status": 404, "error": { "type": "user_not_found" } }
  ]
}
```

```kotlin
// Partial-failure batch handler
data class BatchSendRequest(val requests: List<NotificationRequest>)
data class BatchItemResult(val index: Int, val status: Int, val messageId: String? = null, val error: Map<String, Any>? = null)

fun batchSend(req: BatchSendRequest): List<BatchItemResult> = req.requests.mapIndexed { i, item ->
    runCatching { notificationService.send(item) }
        .fold(
            onSuccess = { BatchItemResult(i, 200, messageId = it.id) },
            onFailure = { BatchItemResult(i, mapToHttpStatus(it), error = mapOf("type" to it.javaClass.simpleName)) }
        )
}
```

**관련 패턴**: [Long-Running Operation](#8-long-running-operation) (배치가 비동기여야 할 때) · [Problem Details](#9-problem-details-rfc7807)

---

<a id="8-long-running-operation"></a>
## 8. Long-Running Operation (LRO)

**목적**: 즉시 완료할 수 없는 작업(대용량 export, 머신러닝 train, 비디오 인코딩)을 HTTP 동기 응답으로 기다리지 않고, `Operation` 리소스를 반환한 뒤 클라이언트가 polling 또는 webhook 으로 결과를 받게 합니다.

**메커니즘**:
- 클라이언트가 작업 시작 요청 → 서버는 즉시 `202 Accepted` + `Operation` 리소스 반환
- `Operation` 리소스는 `name`, `done`, `metadata`, `response` / `error` 필드 포함
- 클라이언트 옵션:
  - **Polling**: `GET /operations/{name}` 을 주기적으로 호출. `done: true` 가 될 때까지 반복.
  - **Webhook**: 작업 시작 시 `callbackUrl` 등록 → 완료 시 서버가 POST.
  - **Server-Sent Events / WebSocket**: 진행률 스트림.
- `Operation.name` 은 `operations/{uuid}` 형식 (AIP-151)

**Operation resource 스키마** (AIP-151):
```typescript
interface Operation {
  name: string;              // "operations/abc123"
  done: boolean;             // false = 진행 중, true = 완료
  metadata?: object;         // 진행률, 예상 완료 시각 등
  response?: object;         // done && success 시 결과
  error?: ProblemDetails;    // done && failure 시 에러
}
```

**장점**:
- HTTP timeout 의 영향 받지 않음 (작업 자체는 BG 에서 계속)
- 클라이언트 / 모바일이 네트워크를 끊었다 다시 붙어도 결과 회수 가능
- 진행률 / 취소 / 부분 결과 노출 가능

**단점/주의**:
- 구현 복잡도 증가 (Operation 저장소, polling endpoint, expiration)
- Polling 빈도 trade-off — 너무 자주 = 부하, 너무 드물 = 응답 지연
- Webhook 은 클라이언트가 public endpoint 를 가져야 함 (모바일 / SPA 어려움)
- Operation 의 lifetime 관리 (TTL, archival)

**표준 인용**:
- Google AIP-151 — *Long-running operations*
- Google Cloud Storage `objects.compose` 등 대부분의 long task 가 이 패턴
- AWS S3 multipart upload 의 `Upload-ID`
- Geewax §17 — *Long-running operations*

**HTTP 예제**:

```http
# 1) 작업 시작 — 즉시 202 응답
POST /v1/videos/vid_1:encode HTTP/1.1

→ 202 Accepted
Location: /v1/operations/op_abc123
{
  "name": "operations/op_abc123",
  "done": false,
  "metadata": {
    "@type": "type.googleapis.com/EncodeMetadata",
    "progressPercent": 0,
    "estimatedCompletion": "2024-06-20T15:30:00Z"
  }
}

# 2) Polling (10s 간격)
GET /v1/operations/op_abc123 HTTP/1.1

→ 200 OK
{
  "name": "operations/op_abc123",
  "done": false,
  "metadata": { "progressPercent": 45 }
}

# 3) 완료 후 polling
GET /v1/operations/op_abc123 HTTP/1.1

→ 200 OK
{
  "name": "operations/op_abc123",
  "done": true,
  "response": {
    "@type": "type.googleapis.com/EncodeResult",
    "outputUrl": "https://cdn.example.com/vid_1.mp4",
    "duration": "1h23m"
  }
}

# 4) 취소
POST /v1/operations/op_abc123:cancel HTTP/1.1
→ 204 No Content
```

```kotlin
// Client-side polling helper
suspend fun <T> awaitOperation(
    client: HttpClient,
    operationName: String,
    pollInterval: Duration = Duration.ofSeconds(5),
    timeout: Duration = Duration.ofMinutes(30),
): T {
    val deadline = Instant.now().plus(timeout)
    while (Instant.now() < deadline) {
        val op = client.get("/v1/$operationName").body<Operation<T>>()
        if (op.done) {
            op.error?.let { throw OperationFailedException(it) }
            return op.response!!
        }
        delay(pollInterval.toMillis())
    }
    throw TimeoutException("Operation $operationName did not complete within $timeout")
}
```

**관련 패턴**: [Webhook/Async API](#13-webhook-async-api) · [Bulk/Batch Operation](#7-bulk-batch-operation) · [Resource-Oriented Design](#3-resource-oriented-design)

---

<a id="9-problem-details-rfc7807"></a>
## 9. Error Response Standard (RFC 7807 Problem Details)

**목적**: HTTP API 에러 응답에 표준 구조(`application/problem+json`)를 사용하여, 모든 API 가 일관된 에러 포맷을 갖게 하고 클라이언트가 에러를 기계적으로 파싱·분기할 수 있게 합니다.

**메커니즘 — RFC 7807 필드**:

| 필드 | 타입 | 설명 |
|---|---|---|
| `type` | URI | 에러 종류를 식별하는 URI. 문서 링크 권장 (e.g. `https://example.com/errors/out-of-credit`) |
| `title` | string | 사람이 읽을 짧은 요약. 같은 `type` 의 모든 인스턴스에서 동일 |
| `status` | integer | HTTP status code (응답 라인과 중복이지만 body 만으로도 알 수 있게) |
| `detail` | string | 이 특정 발생에 대한 상세 설명 |
| `instance` | URI | 이 에러 발생을 식별하는 URI (e.g. `/orders/123/errors/err_abc`) |

추가 필드는 자유롭게 확장 가능 (e.g. `balance`, `accounts`, `validationErrors`).

**Content-Type**: `application/problem+json` (JSON) 또는 `application/problem+xml` (XML).

**장점**:
- 모든 endpoint 가 같은 에러 구조 → SDK 가 한 번만 파싱 코드 작성
- 디버깅 / 로깅 일관됨
- 표준이라 OpenAPI / 모니터링 도구 (Sentry, Datadog) 가 자동 인식
- `type` URI 로 에러 문서 직접 링크 가능

**단점/주의**:
- 기존 API 에 retro-fit 비용 큼 (모든 에러 응답 변경)
- 너무 자세한 `detail` 은 정보 노출 위험 (DB 에러 메시지를 그대로 노출 금지)
- HTTP status code 와 `type` 의 의미가 중복되어 혼란 가능 — `status` 가 transport-level, `type` 이 application-level
- 일부 클라이언트 SDK 가 `Content-Type: application/problem+json` 를 일반 `application/json` 으로 자동 파싱하지 못함

**표준 인용**:
- [IETF RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) — *Problem Details for HTTP APIs* (Nottingham, 2016)
- 후속: [RFC 9457](https://datatracker.ietf.org/doc/html/rfc9457) (2023, 마이너 개정)
- Geewax §5 — *Errors*

**HTTP 예제**:

```http
# 단일 validation 에러
POST /v1/transfers HTTP/1.1
Content-Type: application/json

{ "from": "acc_a", "to": "acc_b", "amount": 150 }

→ 403 Forbidden
Content-Type: application/problem+json

{
  "type":   "https://api.example.com/errors/out-of-credit",
  "title":  "You do not have enough credit",
  "status": 403,
  "detail": "Your current balance is 30, but that costs 50.",
  "instance": "/account/12345/transactions/abc",
  "balance": 30,
  "accounts": ["/account/12345", "/account/67890"]
}

# 다중 validation 에러 (확장 필드)
→ 400 Bad Request
Content-Type: application/problem+json

{
  "type":   "https://api.example.com/errors/validation",
  "title":  "Your request is not valid",
  "status": 400,
  "detail": "Multiple fields failed validation",
  "instance": "/transfers/req_xyz",
  "validationErrors": [
    { "field": "from",   "code": "required" },
    { "field": "amount", "code": "min",      "min": 1 }
  ]
}
```

```kotlin
// Spring 6 / Spring Boot 3 — ProblemDetail (RFC 7807 내장)
@ExceptionHandler(InsufficientCreditException::class)
fun handleInsufficientCredit(e: InsufficientCreditException): ProblemDetail {
    val pd = ProblemDetail.forStatusAndDetail(
        HttpStatus.FORBIDDEN,
        "Your current balance is ${e.balance}, but that costs ${e.cost}."
    )
    pd.type = URI.create("https://api.example.com/errors/out-of-credit")
    pd.title = "You do not have enough credit"
    pd.setProperty("balance", e.balance)
    pd.setProperty("accounts", e.accounts)
    return pd
}
```

**관련 패턴**: [API Versioning](#4-api-versioning) (에러 포맷 변경은 breaking) · [Bulk/Batch Operation](#7-bulk-batch-operation)

---

<a id="10-resource-naming"></a>
## 10. Resource Naming Convention

**목적**: URI / endpoint / field 의 이름 규칙을 통일하여, 같은 회사 / 같은 플랫폼 안의 모든 API 가 일관된 외형을 갖게 만듭니다. 일관성은 학습 비용을 가장 크게 줄이는 단일 요인.

**메커니즘 — 핵심 규칙 (Google AIP-122, Microsoft REST §7)**:

### 10.1 컬렉션은 명사 복수형
```
✓ /books          /users          /orders
✗ /book           /user           /Order   (단수 / PascalCase 금지)
```

### 10.2 계층 = 부모/자식 컬렉션
```
✓ /publishers/p1/books/b1/reviews/r5
✗ /reviews?bookId=b1&publisherId=p1   (계층을 query 로 표현 금지)
```

### 10.3 Verb 는 URI 마지막 custom method 만
```
✓ GET    /orders/o1
✓ POST   /orders/o1:cancel            (custom method, colon prefix)
✗ POST   /cancelOrder?id=o1           (URI 가 동사로 시작 금지)
✗ POST   /orders/o1/actions/cancel    (action 컬렉션 흉내 금지)
```

### 10.4 ID 는 stable, opaque, URL-safe
```
✓ /users/usr_2GxK8mPq      (prefix + opaque ID, Stripe style)
✓ /users/123e4567-e89b-12d3-a456-426614174000   (UUID)
✗ /users/jin@example.com   (이메일 = URL-unsafe + PII)
✗ /users/Jin               (display name = 변경 가능)
```

### 10.5 Field 는 lowerCamelCase 또는 snake_case (한 API 안에서 통일)
```
✓ { "userId": "u1", "createdAt": "2024-06-20" }     (lowerCamelCase, Google AIP)
✓ { "user_id": "u1", "created_at": "2024-06-20" }   (snake_case, Stripe / GitHub)
✗ { "UserId": "u1", "Created_At": "2024-06-20" }    (혼용 금지)
```

### 10.6 Boolean field 는 긍정 + `is` / `has` prefix 금지 논쟁
- Google AIP: `is_published`, `has_avatar` (prefix 권장)
- 일부 가이드: `published`, `avatar_present` (prefix 금지) — 일관성만 유지하면 OK

### 10.7 Timestamp 는 RFC 3339 / ISO 8601 + UTC
```
✓ "createdAt": "2024-06-20T15:30:00Z"
✗ "createdAt": "06/20/2024 15:30"            (포맷 모호)
✗ "createdAt": 1718896200                    (epoch 사용 시 별도 field 명: createdAtEpoch)
```

**장점**:
- 신규 개발자 / 신규 클라이언트의 학습 비용 최소화
- SDK 자동 생성 도구 (OpenAPI, gRPC) 가 깔끔한 코드 생성
- 코드 리뷰가 "이 이름이 맞나?" 가 아니라 "이 동작이 맞나?" 에 집중 가능

**단점/주의**:
- 기존 API 의 naming 변경은 항상 breaking — 새 API 부터 적용 가능
- 두 가이드 (Google AIP vs Microsoft) 가 미세하게 다름 — 회사 내부 표준 채택 필요
- 도메인 용어가 영어가 아닐 때 (한국어 도메인) 어색한 직역 발생 가능

**표준 인용**:
- Google AIP-122 — *Resource names*
- Google AIP-140 — *Field names*
- Microsoft REST API Guidelines §7~9
- Stripe API Naming (snake_case + `obj_` ID prefix)

**HTTP 예제**:

```http
# Good — Google AIP style (lowerCamelCase fields, colon custom verb)
GET /v1/publishers/p1/books/b1
→ {
    "name": "publishers/p1/books/b1",
    "title": "Domain-Driven Design",
    "publishedAt": "2003-08-22T00:00:00Z",
    "authorIds": ["author_eric_evans"]
  }

POST /v1/publishers/p1/books/b1:archive

# Good — Stripe style (snake_case, prefix ID)
GET /v1/customers/cus_NeZwdNA0KAfYAB
→ {
    "id": "cus_NeZwdNA0KAfYAB",
    "object": "customer",
    "created": 1680893993,
    "email": "jin@example.com"
  }

# Bad — 혼합 + verb in path
POST /api/CancelOrder?orderId=o1&user_id=u1   (PascalCase + verb + query 로 식별)
```

**관련 패턴**: [Resource-Oriented Design](#3-resource-oriented-design) · [API Versioning](#4-api-versioning)

---

<a id="11-filter-sort-fieldsel"></a>
## 11. Filtering / Sorting / Field Selection

**목적**: List endpoint 에서 클라이언트가 (a) 어떤 항목을 가져올지(filter), (b) 어떤 순서로(sort), (c) 어떤 필드만(field selection) 받을지 query parameter 로 표준화하여 표현합니다.

**메커니즘 — 3 축**:

### 11.1 Filtering — Google AIP-160 `filter`
- 단일 `filter` query parameter 에 표현식 문자열을 담음 (Common Expression Language, CEL 기반 부분집합)
- 예: `filter=status="ACTIVE" AND createdAt>"2024-01-01"`
- 장점: 표현력 (AND/OR/비교 연산자 / 함수)
- 단점: 파싱 / 검증 / SQL injection 방지 비용 — 별도 파서 필요

대안 — **field-per-query** (단순):
- `?status=ACTIVE&createdAfter=2024-01-01`
- 장점: 구현 단순, OpenAPI 로 명세 가능
- 단점: 복잡한 OR 표현 불가

### 11.2 Sorting — Google AIP-132 `orderBy`
- `orderBy=field1,field2 desc,field3 asc`
- 콤마 구분, 필드명 + 선택적 `asc` / `desc` (기본 asc)
- 다중 정렬 키 지원

### 11.3 Field Selection (Sparse Fieldsets) — Google AIP-157 `readMask`
- `fields=id,title,author.name`  (JSON:API style)
- `readMask=id,title,author.name`  (Google AIP, FieldMask)
- 점(.)으로 nested field 지정
- 응답에 명시된 field 만 포함 → 응답 크기 절감

**장점**:
- 클라이언트가 자신에게 필요한 데이터만 요청 → 네트워크 / 모바일 배터리 절감
- 같은 endpoint 가 다양한 use case 를 커버 → 새 endpoint 추가 불필요
- N+1 / over-fetch 문제 완화

**단점/주의**:
- 모든 query parameter 조합을 인덱스로 커버하기 어려움 — DB 성능 함정
- `filter` 표현식 파싱이 복잡 (CEL 풀 구현은 무거움)
- 캐시 키가 query parameter 조합으로 폭증 → CDN 캐시 효율 저하
- `readMask` 가 보안 필드(예: passwordHash) 를 우회로 노출하지 않도록 whitelist 필수

**표준 인용**:
- Google AIP-160 — *Filtering*
- Google AIP-132 — *List methods* (`orderBy`)
- Google AIP-157 — *Partial responses* (`readMask` / FieldMask)
- JSON:API §6 — Sparse Fieldsets (`fields[type]=...`)
- Stripe — field-per-query filter style

**HTTP 예제**:

```http
# Google AIP style — filter + orderBy + readMask
GET /v1/books?filter=author="Evans"+AND+publishedAt>"2003-01-01"&orderBy=publishedAt+desc&readMask=id,title HTTP/1.1

→ 200 OK
{
  "books": [
    { "id": "b1", "title": "Domain-Driven Design" }
    // author / publishedAt 등 제외됨 (readMask 에 없으니)
  ]
}

# Simple field-per-query style
GET /v1/orders?status=PAID&createdAfter=2024-06-01&orderBy=createdAt+desc&fields=id,total,customerEmail

# JSON:API sparse fieldsets
GET /articles?fields[articles]=title,body&fields[people]=name
```

```kotlin
// Spring — sparse fieldsets with @JsonView
@RestController
class BookController(private val repo: BookRepository) {
    @GetMapping("/v1/books")
    fun list(
        @RequestParam(required = false) status: String?,
        @RequestParam(defaultValue = "createdAt desc") orderBy: String,
        @RequestParam(required = false) fields: String?,
    ): MappingJacksonValue {
        val books = repo.find(status, parseSortKeys(orderBy))
        val mapped = MappingJacksonValue(mapOf("books" to books))
        if (fields != null) {
            val filter = SimpleBeanPropertyFilter.filterOutAllExcept(*fields.split(",").toTypedArray())
            mapped.filters = SimpleFilterProvider().addFilter("bookFilter", filter)
        }
        return mapped
    }
}
```

**관련 패턴**: [Pagination](#5-pagination-patterns) · [Resource-Oriented Design](#3-resource-oriented-design)

---

<a id="12-api-rate-limiting"></a>
## 12. API Rate Limiting & Quota

**목적**: 클라이언트의 호출 빈도를 제한하여 (a) 서비스 보호 (DoS 완화), (b) 공정한 자원 분배 (multi-tenant), (c) 비용 통제 (pay-per-call SaaS) 를 달성합니다.

**메커니즘 — 알고리즘 4 종**:

### 12.1 Token Bucket
- bucket 에 token 이 일정 rate 로 채워짐 (e.g. 10/sec)
- 요청마다 token 1 개 소비. bucket 이 비면 거절.
- **burst 허용** — bucket 크기만큼 순간 폭발 허용
- 가장 흔함 (AWS, GCP, Stripe)

### 12.2 Leaky Bucket
- 요청이 큐에 들어가고 일정 rate 로 처리됨
- 큐가 가득 차면 거절
- burst 흡수하되 출력은 평탄화

### 12.3 Fixed Window Counter
- 1 분 window 안에 N 회 카운트
- 단순하지만 window 경계에서 burst (e.g. 59초에 100 + 61초에 100 = 2초간 200)

### 12.4 Sliding Window Log / Counter
- 정확한 sliding window — 마지막 60초 안의 요청 수
- 메모리 비용 큼 (모든 요청 timestamp 저장) → counter 변형 사용

**HTTP 헤더 표준** (`RFC 6585` + draft `RateLimit Header Fields for HTTP`):

| 헤더 | 의미 |
|---|---|
| `X-RateLimit-Limit` | window 당 허용 횟수 |
| `X-RateLimit-Remaining` | 현재 window 의 남은 횟수 |
| `X-RateLimit-Reset` | window 리셋 시각 (epoch 또는 RFC 3339) |
| `Retry-After` | (429 응답에) 몇 초 후 재시도 가능 |

**Quota 차원**:
- per-IP (DoS 방어)
- per-API-key / per-user (공정성)
- per-endpoint (비싼 endpoint 만 더 엄격)
- per-tenant + per-endpoint 결합 (SaaS)

**장점**:
- 악성 클라이언트로부터 서비스 보호
- 멀티테넌트 환경의 noisy neighbor 완화
- SLA 보장 가능 (예측 가능한 부하)
- 비용 통제 (특히 LLM API 등 비싼 단가)

**단점/주의**:
- 분산 환경에서 rate counter 동기화 비용 (Redis lua script 또는 sliding window 추정)
- 정직한 클라이언트가 burst 로 끊김 → exponential backoff + jitter 가이드 필수
- IP 기반은 NAT / 사무실 환경에서 부정확 → API key 기반 권장
- per-IP 만으로는 IPv6 / proxy 우회 가능

**표준 인용**:
- IETF RFC 6585 §4 — `429 Too Many Requests`
- IETF draft `draft-ietf-httpapi-ratelimit-headers`
- AWS API Gateway, Cloudflare Rate Limiting, Kong rate-limiting plugin
- Stripe Rate Limits documentation

**HTTP 예제**:

```http
# 정상 응답 (한도 안)
GET /v1/charges HTTP/1.1
Authorization: Bearer sk_live_...

→ 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1718896200
{ "data": [...] }

# 한도 초과
GET /v1/charges HTTP/1.1

→ 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1718896260
Retry-After: 60
Content-Type: application/problem+json

{
  "type":   "https://api.example.com/errors/rate-limit-exceeded",
  "title":  "Too Many Requests",
  "status": 429,
  "detail": "You have exceeded 100 requests per minute. Retry after 60s.",
  "instance": "/v1/charges"
}
```

```kotlin
// Token bucket with Redis (per-API-key)
class TokenBucketLimiter(private val redis: RedisCommands<String, String>) {
    fun tryAcquire(key: String, ratePerSec: Int, burst: Int): RateResult {
        val script = """
            local bucket = redis.call('HMGET', KEYS[1], 'tokens', 'lastRefill')
            local now = tonumber(ARGV[1]); local rate = tonumber(ARGV[2]); local burst = tonumber(ARGV[3])
            local tokens = tonumber(bucket[1]) or burst
            local last = tonumber(bucket[2]) or now
            tokens = math.min(burst, tokens + (now - last) * rate / 1000)
            local allowed = tokens >= 1
            if allowed then tokens = tokens - 1 end
            redis.call('HMSET', KEYS[1], 'tokens', tokens, 'lastRefill', now)
            redis.call('EXPIRE', KEYS[1], 3600)
            return { allowed and 1 or 0, math.floor(tokens) }
        """.trimIndent()
        val result = redis.eval<List<Long>>(script, ScriptOutputType.MULTI,
            arrayOf("rate:$key"),
            System.currentTimeMillis().toString(), ratePerSec.toString(), burst.toString())
        return RateResult(allowed = result[0] == 1L, remaining = result[1].toInt())
    }
}
```

**관련 패턴**: [Webhook/Async API](#13-webhook-async-api) (webhook 도 rate limit 가능) · [reliability.md](reliability.md) Backpressure · [security-api-web.md](../security/security-api-web.md) per-Identity Rate Limit

---

<a id="13-webhook-async-api"></a>
## 13. Async API Pattern (Webhook / Callback)

**목적**: 서버가 클라이언트에게 능동적으로 이벤트를 push 하기 위해, 클라이언트가 등록한 callback URL 로 HTTP POST 를 발송합니다. polling 의 반대 방향 — "서버 → 클라이언트 fire-and-forget".

**메커니즘**:
- 클라이언트가 webhook endpoint URL 을 등록 (UI 또는 API)
- 이벤트 발생 시 서버가 해당 URL 로 HTTP POST + JSON payload + 서명 헤더
- 클라이언트는 빠르게 `2xx` 응답 후 비동기 처리
- 실패 (4xx/5xx/timeout) 시 서버가 exponential backoff 으로 재시도
- 일정 횟수 이상 실패하면 webhook 비활성화 + 알림

**필수 보안 — HMAC 서명**:
- 서버가 payload 를 secret key 로 HMAC-SHA256 서명 → `X-Signature` 헤더로 전송
- 클라이언트가 같은 secret 으로 검증 → 위조 / 재생 공격 방지
- timestamp 헤더 (`X-Timestamp`) 동봉 + 5분 이내 검증 → replay 방지

**재시도 정책 (Stripe / GitHub 표준)**:
- 초기: 즉시
- 1차 실패: 5분 후
- 2차: 15분 후 (exponential)
- ... 최대 72시간 동안 N 회

**Idempotency 보장 책임**:
- 서버는 at-least-once 만 보장 (네트워크 재시도)
- 클라이언트는 event ID (`Webhook-ID` 헤더) 기반 dedup 필수

**장점**:
- 폴링 대비 효율적 (이벤트 없으면 호출 없음)
- 실시간성 우수 (수 초 이내)
- 클라이언트 / 서버 디커플링

**단점/주의**:
- 클라이언트가 public HTTPS endpoint 필요 → 모바일 / SPA 부적합 (대안: SSE / WebSocket / push notification)
- 발신 측 IP whitelist 필요할 수 있음 (방화벽 환경)
- 재시도 / dead-letter / 통계 인프라 구축 비용
- 클라이언트 endpoint 의 SLA 가 서버 메시지 손실 위험과 직결

**표준 인용**:
- [Stripe Webhooks](https://stripe.com/docs/webhooks) — 산업 표준 reference
- [GitHub Webhooks](https://docs.github.com/en/webhooks)
- [CNCF CloudEvents](https://cloudevents.io) — webhook payload 표준
- [StandardWebhooks.com](https://www.standardwebhooks.com) — 헤더 / 서명 통일 운동

**HTTP 예제**:

```http
# 서버 → 클라이언트로 발송하는 webhook POST
POST /webhooks/stripe HTTP/1.1
Host: client.example.com
Content-Type: application/json
Stripe-Signature: t=1718896200,v1=5257a869e7ecebeda32affa62cdca3fa51cad7e77a0e56ff536d0ce8e108d8bd
Webhook-ID: evt_1Abc123

{
  "id": "evt_1Abc123",
  "type": "charge.succeeded",
  "data": { "object": { "id": "ch_1Xyz", "amount": 5000 } },
  "created": 1718896200
}

# 클라이언트 응답
→ 200 OK   (서버는 성공으로 간주)
또는
→ 500 Internal Server Error   (서버가 backoff 으로 재시도)
```

```kotlin
// 클라이언트 측 webhook 검증
@PostMapping("/webhooks/stripe")
fun handleStripeWebhook(
    @RequestBody payload: String,
    @RequestHeader("Stripe-Signature") signature: String,
    @RequestHeader("Webhook-ID") eventId: String,
): ResponseEntity<Void> {
    // 1) 서명 검증
    if (!verifyHmacSha256(payload, signature, secret = WEBHOOK_SECRET, toleranceSec = 300)) {
        return ResponseEntity.status(401).build()
    }
    // 2) Dedup (at-least-once 대응)
    if (eventStore.exists(eventId)) {
        return ResponseEntity.ok().build()   // 이미 처리됨 — 멱등
    }
    // 3) 빠른 응답 후 비동기 처리 (webhook timeout 회피)
    queue.enqueue(WebhookEvent(eventId, payload))
    return ResponseEntity.ok().build()
}

fun verifyHmacSha256(payload: String, sigHeader: String, secret: String, toleranceSec: Long): Boolean {
    val parts = sigHeader.split(",").associate { it.split("=").let { (k, v) -> k to v } }
    val t = parts["t"]?.toLongOrNull() ?: return false
    val v1 = parts["v1"] ?: return false
    if (Math.abs(System.currentTimeMillis() / 1000 - t) > toleranceSec) return false
    val expected = HmacUtils(HmacAlgorithms.HMAC_SHA_256, secret).hmacHex("$t.$payload")
    return MessageDigest.isEqual(expected.toByteArray(), v1.toByteArray())
}
```

**관련 패턴**: [Long-Running Operation](#8-long-running-operation) (대안: polling) · [distributed.md/Outbox](distributed.md) (webhook 발송의 at-least-once 보장) · [security-api-web.md](../security/security-api-web.md) HMAC Signing

---

<a id="14-api-deprecation-sunset"></a>
## 14. API Deprecation & Sunset

**목적**: 더 이상 권장하지 않는 endpoint / 필드 / 버전을 단계적으로 제거하기 위해, 표준 HTTP 헤더와 명시적 정책으로 클라이언트에게 충분한 마이그레이션 시간을 주고 제거 시점을 약속합니다.

**메커니즘 — 4 단계 라이프사이클**:

### 14.1 Active
- 정상 지원 상태. 새 클라이언트 사용 권장.

### 14.2 Deprecated
- 사용 가능하나 더 이상 권장하지 않음
- 응답에 `Deprecation` 헤더 추가 (RFC 9745 draft)
- 가능하면 `Link: <new-url>; rel="successor-version"` 으로 후속 버전 안내

### 14.3 Sunset Announced
- 제거 날짜 확정 + `Sunset` 헤더로 일자 안내 (RFC 8594)
- 보통 3~12 개월 전 공지
- 클라이언트별 사용량 모니터링 → 잔존 클라이언트 직접 연락

### 14.4 Removed
- 응답 `410 Gone` 또는 `404 Not Found`
- 응답 body 에 마이그레이션 가이드 링크

**Deprecation Window 권장치**:
- **Public API** (외부 개발자): 최소 12 개월
- **Internal API** (같은 회사): 3~6 개월
- **Critical** (결제, 인증): 18~24 개월
- **Stripe API**: 영구 호환성 보장 (날짜 버전 고정) — 가장 강한 약속
- **Google Cloud**: 1 년 (Public GA) / 즉시 (Beta)

**Backward compatibility 의 종류**:
- **Wire-compatible**: 같은 요청/응답으로 작동
- **Source-compatible**: 클라이언트 코드 컴파일 가능
- **Semantic-compatible**: 같은 의미 (동작 결과)

**장점**:
- 클라이언트가 마이그레이션 일정을 예측 가능
- 신뢰 형성 (갑작스러운 제거 없음)
- 잔존 사용자 명시적 추적
- 표준 헤더로 도구 (모니터링, SDK) 가 자동 경고 가능

**단점/주의**:
- 긴 deprecation window = 코드 중복 부담 (두 버전 동시 유지)
- `Sunset` 헤더를 무시하는 클라이언트가 sunset 시점에 깨짐 → 사용량 추적 + 직접 연락 필수
- Beta / Preview API 는 deprecation window 면제 명시 필요
- 무료 API 는 deprecation 책임이 약함 → SLA 명시 권장

**표준 인용**:
- IETF RFC 8594 — *The Sunset HTTP Header Field* (Wilde, 2019)
- IETF draft — *The Deprecation HTTP Response Header Field*
- Geewax §24 — *Versioning and compatibility*
- Stripe API versioning (영구 호환 정책)
- Google Cloud Deprecation Policy

**HTTP 예제**:

```http
# Deprecated 단계 — 사용 가능하나 권장 안 함
GET /v1/users/42 HTTP/1.1

→ 200 OK
Deprecation: @1717200000                              ; deprecated 시각 (epoch 또는 RFC 3339)
Link: </v2/users/42>; rel="successor-version"
Sunset: Wed, 31 Dec 2025 23:59:59 GMT
Warning: 299 - "Use /v2/users — /v1 will be removed on 2025-12-31"

{ "id": 42, "name": "Jin" }

# Sunset 직전 — 같은 헤더 + 강한 경고 로그
# 사용량이 임계치 이하면 제거 진행

# Removed 단계
GET /v1/users/42 HTTP/1.1

→ 410 Gone
Content-Type: application/problem+json

{
  "type":   "https://api.example.com/errors/version-removed",
  "title":  "API version removed",
  "status": 410,
  "detail": "Version v1 was sunset on 2025-12-31. Please migrate to v2.",
  "migrationGuide": "https://docs.example.com/migrate-v1-to-v2"
}
```

```kotlin
// Spring filter — deprecation header 자동 부착
@Component
class DeprecationFilter : Filter {
    private val deprecatedPaths = mapOf(
        "/v1/users"     to DeprecationInfo(successor = "/v2/users",     sunset = "2025-12-31T23:59:59Z"),
        "/v1/orders"    to DeprecationInfo(successor = "/v2/orders",    sunset = "2025-12-31T23:59:59Z"),
    )

    override fun doFilter(req: ServletRequest, res: ServletResponse, chain: FilterChain) {
        val httpReq = req as HttpServletRequest
        val httpRes = res as HttpServletResponse
        deprecatedPaths.entries.firstOrNull { httpReq.requestURI.startsWith(it.key) }?.let { (_, info) ->
            httpRes.setHeader("Deprecation", "true")
            httpRes.setHeader("Sunset", info.sunset)
            httpRes.setHeader("Link", "<${info.successor}>; rel=\"successor-version\"")
            httpRes.setHeader("Warning", "299 - \"Use ${info.successor} — sunset ${info.sunset}\"")
            metrics.counter("api.deprecated.usage", "path", httpReq.requestURI).increment()
        }
        chain.doFilter(req, res)
    }
}
```

**관련 패턴**: [API Versioning](#4-api-versioning) · [Problem Details](#9-problem-details-rfc7807) (410 응답 body) · [Resource Naming](#10-resource-naming)

---
