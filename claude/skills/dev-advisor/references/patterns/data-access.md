# 데이터 접근 패턴 (Data Access Patterns)

Martin Fowler 의 *Patterns of Enterprise Application Architecture*(PoEAA, 2002) 에서 정리된 객체-관계 매핑·데이터 접근 패턴 모음. 도메인 객체와 RDB 행(row) 사이의 변환 전략을 다루며, ORM·DAO·Repository 구현체 설계의 토대가 된다.

---

## 1. Repository

**목적**: 도메인 객체를 메모리 안의 컬렉션처럼 다룰 수 있도록 영속 저장소를 추상화합니다.

**특징**:
- 컬렉션 유사 인터페이스 (`add / remove / find`) 제공 (collection-like)
- 또는 영속 지향 인터페이스 (`save / delete / findById`) 제공 (persistence-oriented)
- 내부적으로 Data Mapper / Query Object 를 조합해 SQL 을 생성
- Fowler PoEAA Repository = 일반적 컬렉션 추상화. **DDD Repository** 는 여기에 *Aggregate 경계* 와 *ubiquitous language* 제약이 더해진 특수형 (자세한 도메인 측면은 `ddd-tactical.md` 참조)
- 두 스타일 모두 클라이언트에겐 저장 기술이 보이지 않는다

**장점**:
- 도메인 코드가 SQL/ORM 에 비의존
- 테스트용 in-memory 구현으로 교체 가능
- 쿼리 의도(`findActiveUsers()`)가 도메인 언어로 표현됨

**단점**:
- 단순 CRUD 만 필요할 땐 과한 추상화
- 컬렉션 vs 영속 지향 스타일 혼용 시 일관성 ↓
- 잘못 쓰면 generic DAO 로 회귀

**활용 예시**:
- Spring Data `JpaRepository`
- 도메인 주도 설계의 `OrderRepository`
- in-memory 구현으로 단위 테스트

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// collection-like 스타일
interface OrderRepository {
    fun add(order: Order)
    fun remove(order: Order)
    fun findById(id: OrderId): Order?
    fun findAll(spec: Spec<Order>): List<Order>
}

// persistence-oriented 스타일
interface OrderStore {
    fun save(order: Order)
    fun delete(id: OrderId)
    fun findById(id: OrderId): Order?
}
```

**관련 패턴**: Data Mapper, Query Object, Specification, Unit of Work

---

## 2. Unit of Work

**목적**: 비즈니스 트랜잭션 중에 발생한 객체 변경을 추적해, 커밋 시 일관된 순서로 한 번에 DB 에 반영합니다.

**특징**:
- New / Dirty / Removed 객체 목록을 내부적으로 관리
- 커밋 시 INSERT → UPDATE → DELETE 순서 조율
- 동일 ID 객체의 중복 영속 방지 (Identity Map 과 협력)
- 명시적(Transaction Script 가 등록) 또는 묵시적(Data Mapper 가 자동 등록) 운영

**장점**:
- 트랜잭션 경계 명확
- DB round-trip 최소화 (batch flush)
- 비즈니스 로직에서 트랜잭션 코드 분리

**단점**:
- 변경 추적 메커니즘 구현/디버깅 난이도
- 커밋 순서 오류 시 무결성 위반
- 메모리 사용량 증가 (대량 처리 시)

**활용 예시**:
- Hibernate / JPA `EntityManager`, EF Core `DbContext`
- 도메인 이벤트 발행을 커밋 시점에 묶기
- 스크립트 기반 데이터 마이그레이션

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class UnitOfWork(private val mapper: OrderMapper) {
    private val newOnes = mutableListOf<Order>()
    private val dirtyOnes = mutableListOf<Order>()
    private val removedOnes = mutableListOf<Order>()

    fun registerNew(o: Order) { newOnes += o }
    fun registerDirty(o: Order) { dirtyOnes += o }
    fun registerRemoved(o: Order) { removedOnes += o }

    fun commit() {
        newOnes.forEach { mapper.insert(it) }
        dirtyOnes.forEach { mapper.update(it) }
        removedOnes.forEach { mapper.delete(it) }
        newOnes.clear(); dirtyOnes.clear(); removedOnes.clear()
    }
}
```

**관련 패턴**: Identity Map, Data Mapper, Repository, Transaction Script

---

## 3. Active Record

**목적**: DB row 한 줄을 객체 하나에 대응시키고, 그 객체가 **자기 영속화 로직(CRUD)** 도 직접 책임지게 합니다.

**특징**:
- 객체 = 테이블 row + 영속화 메서드
- `user.save()`, `User.findById(id)` 와 같이 정적/인스턴스 메서드로 DB 접근
- 스키마와 객체 구조가 거의 1:1
- 도메인 로직과 영속 로직이 같은 클래스에 공존

**장점**:
- 학습 곡선 낮고 구현 빠름
- 단순 CRUD 앱에서 코드량 최소
- ORM 마법 없이 직관적

**단점**:
- 도메인 로직과 영속 로직 결합 → SRP 위반
- 복잡한 도메인 모델에 부적합
- 단위 테스트 어려움 (DB 의존)

**활용 예시**:
- Ruby on Rails `ActiveRecord`
- Laravel Eloquent, Django ORM (부분적으로)
- 스크립트성 admin 도구

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class User(var id: Long?, var name: String, var email: String) {
    fun save() {
        if (id == null) DB.exec("INSERT INTO users(name,email) VALUES(?,?)", name, email)
        else DB.exec("UPDATE users SET name=?, email=? WHERE id=?", name, email, id)
    }
    fun delete() { DB.exec("DELETE FROM users WHERE id=?", id) }

    companion object {
        fun findById(id: Long): User? =
            DB.query("SELECT * FROM users WHERE id=?", id) { User(it.long("id"), it.str("name"), it.str("email")) }
    }
}
```

**관련 패턴**: Data Mapper(대안), Row Data Gateway, Table Module

---

## 4. Data Mapper

**목적**: 도메인 객체와 DB 사이를 **별도 매퍼 계층** 이 변환하여, 도메인 객체는 영속을 전혀 몰라도 되게 합니다.

**특징**:
- 도메인 모델 ↔ DB 의 양방향 매핑 책임을 Mapper 가 단독 보유
- 도메인 객체는 POJO (영속 메서드 없음)
- 스키마와 객체 구조가 달라도 됨 (impedance mismatch 해결)
- ORM 의 핵심 메커니즘

**장점**:
- 도메인 모델 순수성 유지 (테스트·재사용 용이)
- 복잡한 도메인 ↔ 정규화 스키마 매핑 가능
- 도메인 모델과 DB 가 독립적으로 진화

**단점**:
- 매핑 코드/설정 비용
- 잘못 쓰면 N+1 등 성능 함정
- ORM 마법으로 디버깅 난이도 ↑

**활용 예시**:
- Hibernate / JPA / EclipseLink
- .NET Entity Framework, SQLAlchemy ORM mode
- 수작업 매퍼 (MyBatis, jOOQ + mapper)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// 도메인 — 영속을 모름
data class Order(val id: OrderId, val total: Money)

// Mapper
class OrderMapper(private val db: Database) {
    fun findById(id: OrderId): Order? = db.query(
        "SELECT id, total_amount, total_currency FROM orders WHERE id=?", id.value
    ) { Order(OrderId(it.str("id")), Money(it.bd("total_amount"), Currency.getInstance(it.str("total_currency")))) }

    fun insert(o: Order) = db.exec(
        "INSERT INTO orders(id,total_amount,total_currency) VALUES(?,?,?)",
        o.id.value, o.total.amount, o.total.currency.currencyCode,
    )
}
```

**관련 패턴**: Active Record(대안), Unit of Work, Identity Map, Repository

---

## 5. Identity Map

**목적**: 한 세션 안에서 같은 ID 의 DB row 는 항상 **동일한 객체 인스턴스** 로 보장하여, 중복 로드와 일관성 문제를 막습니다.

**특징**:
- 세션/트랜잭션 scope 의 캐시 (Map<Id, Object>)
- 두 번째 이후의 `findById` 는 캐시 hit
- 같은 row 가 두 객체로 존재하지 않으므로 변경 충돌 방지
- 보통 Unit of Work / ORM 세션과 결합

**장점**:
- 객체 동일성 보장 (`==` 비교 안전)
- DB round-trip 절약
- Unit of Work 변경 추적의 기반

**단점**:
- 세션 lifetime 관리 필요 (메모리 누수 위험)
- 분산 캐시·다중 트랜잭션 환경에서 staleness 위험
- 멀티스레드 안전성 별도 설계 필요

**활용 예시**:
- Hibernate 1차 캐시(session cache)
- EF Core ChangeTracker
- 단일 요청 scope DI 컨테이너의 entity 캐시

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class OrderIdentityMap(private val mapper: OrderMapper) {
    private val cache = mutableMapOf<OrderId, Order>()

    fun findById(id: OrderId): Order? = cache.getOrPut(id) {
        mapper.findById(id) ?: return null
    }

    fun evict(id: OrderId) { cache.remove(id) }
    fun clear() = cache.clear()
}
```

**관련 패턴**: Unit of Work, Data Mapper, Repository

---

## 6. Lazy Load

**목적**: 객체의 일부 데이터를 **실제 접근 시점까지 로드를 지연** 시켜 초기 로딩 비용을 줄입니다.

**특징**:
- 구현 방식: Lazy Initialization / Virtual Proxy / Value Holder / Ghost
- 컬렉션·연관 관계에 가장 자주 적용
- 접근 시점에 자동으로 DB 조회 트리거
- ORM 이 프록시 객체로 구현

**장점**:
- 큰 객체 그래프의 초기 비용 절감
- 사용 안 하는 데이터는 영영 로드 안 됨
- API 시그니처를 바꾸지 않고 적용 가능

**단점**:
- **N+1 쿼리** 의 주범
- 세션 종료 후 접근 시 LazyInitializationException
- 디버깅 시점 추적 어려움

**활용 예시**:
- Hibernate `@OneToMany(fetch = LAZY)` 컬렉션
- 큰 BLOB/CLOB 필드 지연 로드
- Kotlin `by lazy { }`, Java `Supplier<T>`

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class Order(val id: OrderId, private val mapper: OrderLineMapper) {
    val lines: List<OrderLine> by lazy {
        println("loading lines for $id")
        mapper.findByOrder(id)
    }
}

// 사용
val o = Order(OrderId("o-1"), mapper)
// 이 시점엔 lines 미조회
println(o.lines.size) // 여기서 처음 SELECT 발생
```

**관련 패턴**: Virtual Proxy, Ghost, Data Mapper

---

## 7. Query Object

**목적**: SQL 문자열을 직접 만드는 대신, **쿼리 자체를 객체** 로 표현하여 조립·재사용·테스트 가능하게 합니다.

**특징**:
- 도메인 언어로 조건을 표현 (`OrderQuery().placedAfter(d).total(>=, 100)`)
- 내부적으로 SQL/JPQL/Criteria 생성
- 컴파일 타임 타입 안전성 확보 가능 (jOOQ, QueryDSL)
- 동적 쿼리·검색 화면에 적합

**장점**:
- 문자열 SQL 의존 ↓ (오타·인젝션 방지)
- 쿼리 부분 재사용 (조건 조합)
- 도메인 의도가 코드로 드러남

**단점**:
- 구현/학습 비용
- 추상화가 두꺼우면 생성된 SQL 추적 어려움
- 매우 동적인 쿼리엔 한계

**활용 예시**:
- jOOQ DSL, QueryDSL, Spring Data Specifications
- JPA `CriteriaBuilder`
- Django QuerySet, ActiveRecord Relation

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
class OrderQuery {
    private val conditions = mutableListOf<String>()
    private val params = mutableListOf<Any>()

    fun placedAfter(t: Instant) = apply {
        conditions += "placed_at > ?"; params += t
    }
    fun minTotal(amount: BigDecimal) = apply {
        conditions += "total_amount >= ?"; params += amount
    }
    fun execute(db: Database): List<Order> {
        val where = if (conditions.isEmpty()) "" else "WHERE " + conditions.joinToString(" AND ")
        return db.query("SELECT * FROM orders $where", *params.toTypedArray()) { /* map */ TODO() }
    }
}
```

**관련 패턴**: Specification, Repository, Interpreter

---

## 8. Specification (Query)

**목적**: 도메인 규칙 표현용 Specification 을 DB 쿼리 조건으로도 사용하여, "어떤 객체를 원하는가?" 를 한 곳에 정의합니다.

**특징**:
- DDD Specification 의 쿼리 확장 (Evans 가 PoEAA 의 Repository 와 결합 제안)
- `isSatisfiedBy(o)` (in-memory) + `toSqlClause()` (DB) 양쪽 지원
- `and / or / not` 조합 가능
- Spring Data `Specification<T>` 가 대표 구현

**장점**:
- 도메인 규칙과 쿼리 조건의 단일 소스
- in-memory 테스트와 DB 조회 동일 규칙 재사용
- 조건 재조합 자유로움

**단점**:
- 두 표현(객체 검증 + SQL 생성) 유지 비용
- DB 함수/조인 등 표현 한계
- 단순 쿼리엔 과함

**활용 예시**:
- Spring Data JPA `Specification<Order>`
- 검색 필터 조립 (관리자 검색 화면)
- 비즈니스 규칙 + DB 인덱싱 정책 공유

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
interface QuerySpec<T> {
    fun isSatisfiedBy(t: T): Boolean
    fun toSql(): Pair<String, List<Any>>
    infix fun and(other: QuerySpec<T>): QuerySpec<T> = object : QuerySpec<T> {
        override fun isSatisfiedBy(t: T) = this@QuerySpec.isSatisfiedBy(t) && other.isSatisfiedBy(t)
        override fun toSql(): Pair<String, List<Any>> {
            val (a, ap) = this@QuerySpec.toSql(); val (b, bp) = other.toSql()
            return "($a) AND ($b)" to (ap + bp)
        }
    }
}

class OverdueSpec(val asOf: Instant) : QuerySpec<Order> {
    override fun isSatisfiedBy(o: Order) = o.dueAt.isBefore(asOf) && !o.isPaid
    override fun toSql() = "due_at < ? AND is_paid = false" to listOf(asOf)
}
```

**관련 패턴**: Specification (DDD), Query Object, Repository

---

## 9. Table Module

**목적**: 테이블 하나당 클래스 하나를 두되, **인스턴스 단위가 아니라 테이블 전체** 의 비즈니스 로직을 담는 컴포넌트로 다룹니다.

**특징**:
- 한 테이블 = 한 클래스, 단일 인스턴스
- 메서드는 row id 또는 result set 을 인자로 받음 (`OrderTable.markShipped(orderId)`)
- 도메인 객체 없이 RecordSet / DataTable 기반 처리
- Active Record 와 달리 row 가 객체가 아니므로 "Domain Model 없는 시트 처리" 에 가까움

**장점**:
- RecordSet 친화 환경에서 코드량 최소
- 테이블 단위 일괄 처리에 자연스러움
- ORM 부담 없음

**단점**:
- 복잡한 도메인 로직 표현 어려움
- 행(row) 단위 invariant 적용이 산만
- 객체지향의 이점 거의 못 누림

**활용 예시**:
- 고전 .NET DataSet + TableAdapter 스타일
- VB / classic ASP / Delphi 시대 LOB 앱
- 통계·집계 위주 ETL 모듈

**난이도**: 낮음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
// 한 테이블에 대한 모든 비즈니스 로직 — 단일 모듈
class OrderTable(private val db: Database) {
    fun totalRevenue(month: YearMonth): BigDecimal =
        db.queryOne("SELECT SUM(total_amount) FROM orders WHERE TO_CHAR(placed_at,'YYYY-MM')=?", month.toString())
            ?.bd("sum") ?: BigDecimal.ZERO

    fun markShipped(orderId: String) =
        db.exec("UPDATE orders SET status='SHIPPED' WHERE id=?", orderId)

    fun overdue(asOf: Instant): ResultSet =
        db.queryRaw("SELECT * FROM orders WHERE due_at<? AND status<>'PAID'", asOf)
}
```

**관련 패턴**: Active Record, Transaction Script, Row Data Gateway

---

## 10. Row Data Gateway

**목적**: DB row 하나에 대응하는 **순수 게이트웨이 객체** 를 두어 SQL 호출을 캡슐화하되, 비즈니스 로직은 담지 않습니다.

**특징**:
- 한 객체 = 한 row, 메서드는 단순 CRUD + getter/setter
- 비즈니스 로직 X (Active Record 와의 가장 큰 차이)
- 보통 Finder 별도 클래스가 새 인스턴스를 생성
- Table Data Gateway(테이블 단위) 와 한 쌍을 이루는 row 단위 변형

**장점**:
- DB 접근 코드와 비즈니스 로직 분리
- 단순·예측 가능
- 코드 생성 도구로 자동 생성 쉬움

**단점**:
- 비즈니스 로직을 어디 둘지 별도 결정 필요 (Transaction Script 등과 결합)
- 객체가 빈약 → anemic 모델로 흐르기 쉬움
- 매핑 코드 중복

**활용 예시**:
- 코드 생성기로 만든 DAO 클래스
- legacy LOB 시스템의 row 객체
- Repository 내부 구현 보조

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
class OrderGateway(
    val id: String,
    var totalAmount: BigDecimal,
    var status: String,
) {
    fun insert(db: Database) =
        db.exec("INSERT INTO orders(id,total_amount,status) VALUES(?,?,?)", id, totalAmount, status)
    fun update(db: Database) =
        db.exec("UPDATE orders SET total_amount=?, status=? WHERE id=?", totalAmount, status, id)
    fun delete(db: Database) =
        db.exec("DELETE FROM orders WHERE id=?", id)

    companion object Finder {
        fun load(db: Database, id: String): OrderGateway? = db.queryOne(
            "SELECT id,total_amount,status FROM orders WHERE id=?", id
        ) { OrderGateway(it.str("id"), it.bd("total_amount"), it.str("status")) }
    }
}
```

**관련 패턴**: Active Record, Table Data Gateway, Data Mapper, Transaction Script
