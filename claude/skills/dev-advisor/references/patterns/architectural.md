# 아키텍처 패턴 (Architectural Patterns)

Presentation 계층과 Backend 계층의 전반적 구조를 결정하는 패턴. GoF 23은 클래스/객체 수준 디자인 패턴인 반면 아키텍처 패턴은 시스템 수준 분리.

---

## 1. MVC (Model-View-Controller)

**목적**: 애플리케이션을 Model(데이터), View(표현), Controller(입력 처리)의 세 역할로 분리하여 관심사를 격리합니다.

**특징**:
- View는 Model을 직접 관찰하거나 Controller가 중개
- Controller는 사용자 입력 → Model 갱신 → View 갱신을 지휘
- 가장 오래된 GUI 아키텍처 패턴 (Smalltalk-80)

**장점**:
- Model과 View의 독립적 변경 가능
- 동일 Model에 다른 View 부착 용이
- 단위 테스트 용이 (Model/Controller 분리)

**단점**:
- Controller가 비대해지기 쉬움 (Massive View Controller)
- View와 Model의 결합도가 높아질 수 있음

**활용 예시**:
- 전통적 웹 프레임워크 (Spring MVC, Ruby on Rails, Django)
- ASP.NET MVC
- 초기 iOS UIViewController

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
data class User(val name: String)

class UserModel { var user: User = User("Anon") }

class UserView { fun render(user: User) = println("Hello, ${user.name}") }

class UserController(private val model: UserModel, private val view: UserView) {
    fun onNameInput(name: String) {
        model.user = User(name)
        view.render(model.user)
    }
}
```

**관련 패턴**: MVP, MVVM, Observer

---

## 2. MVP (Model-View-Presenter)

**목적**: MVC의 Controller를 Presenter로 대체하여 View를 수동적(Passive View)으로 만들고 테스트 가능성을 극대화합니다.

**특징**:
- View는 인터페이스로 추상화되어 Presenter가 호출
- Presenter는 Model 조회 후 View 메서드 직접 호출
- View ↔ Model 직접 의존 없음

**장점**:
- Presenter 단위 테스트 용이 (View Mock)
- View의 로직 거의 없음 → 플랫폼 종속성 격리
- 디버깅 추적 명확 (단방향 호출)

**단점**:
- Presenter 보일러플레이트 증가
- View 인터페이스마다 1:1 매핑 필요

**활용 예시**:
- 초기 Android 앱 (Square, Google 가이드)
- WinForms 애플리케이션
- GWT 기반 웹앱

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
interface LoginView {
    fun showError(message: String)
    fun navigateHome()
}

class LoginPresenter(private val view: LoginView, private val repo: UserRepo) {
    fun onLogin(id: String, pw: String) {
        if (repo.verify(id, pw)) view.navigateHome()
        else view.showError("Invalid credentials")
    }
}
```

**관련 패턴**: MVC, MVVM, Observer

---

## 3. MVVM (Model-View-ViewModel)

**목적**: ViewModel이 View의 상태를 노출하고, 양방향 데이터 바인딩으로 View ↔ ViewModel을 자동 동기화합니다.

**특징**:
- ViewModel은 View를 모름 (UI 프레임워크 비의존)
- 관찰 가능한 상태 (LiveData/StateFlow/Observable)
- 데이터 바인딩 프레임워크 활용

**장점**:
- ViewModel은 순수 코틀린/자바 단위 테스트 가능
- View 자동 갱신 → 보일러플레이트 감소
- Configuration change에 강함 (Android ViewModel)

**단점**:
- 양방향 바인딩 디버깅 어려움
- 간단한 화면에 과한 추상화
- 메모리 누수 위험 (Observable 구독 해제 누락)

**활용 예시**:
- Android Jetpack (ViewModel + LiveData/Compose)
- WPF, Xamarin, Avalonia
- Vue.js (reactive ref)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class CounterViewModel {
    private val _count = MutableStateFlow(0)
    val count: StateFlow<Int> = _count
    fun increment() { _count.value += 1 }
}

// View (Compose)
@Composable
fun CounterView(vm: CounterViewModel) {
    val c by vm.count.collectAsState()
    Button(onClick = vm::increment) { Text("Count: $c") }
}
```

**관련 패턴**: MVP, MVI, Observer

---

## 4. MVI (Model-View-Intent)

**목적**: 사용자 의도(Intent)를 입력으로 받아 불변 상태(State)를 출력하는 단방향 데이터 흐름을 강제합니다.

**특징**:
- View → Intent → Reducer → State → View 순환
- 모든 상태가 불변 객체
- 시간 여행 디버깅 (Time-travel debugging) 가능

**장점**:
- 예측 가능한 상태 전이
- 동시성 이슈 최소화 (불변)
- 재현 가능한 버그 (Intent 시퀀스 재생)

**단점**:
- 객체 할당 증가 (모든 상태 새로 생성)
- 작은 변경에도 전체 상태 발행 → 오버헤드

**활용 예시**:
- Android (Orbit, MVIKotlin)
- Cycle.js, Elm Architecture
- Compose UI 상태 패턴

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
sealed class Intent { object Increment : Intent(); object Decrement : Intent() }
data class State(val count: Int = 0)

class CounterStore {
    private val _state = MutableStateFlow(State())
    val state: StateFlow<State> = _state
    fun dispatch(intent: Intent) {
        _state.value = when (intent) {
            Intent.Increment -> _state.value.copy(count = _state.value.count + 1)
            Intent.Decrement -> _state.value.copy(count = _state.value.count - 1)
        }
    }
}
```

**관련 패턴**: Flux/Redux, MVVM, Command

---

## 5. MVVM-C (MVVM + Coordinator)

**목적**: MVVM에서 화면 전환 책임을 ViewModel에서 분리하여 Coordinator가 네비게이션 흐름을 전담합니다.

**특징**:
- Coordinator가 화면 스택 및 라우팅 관리
- ViewModel은 네비게이션 콜백/이벤트만 발행
- Deep link / 흐름 분기에 유리

**장점**:
- ViewModel이 네비게이션 의존성에서 해방
- 복잡한 사용자 여정(가입, 결제) 재사용 용이
- A/B 테스트로 흐름 교체 쉬움

**단점**:
- Coordinator 계층 추가 → 코드량 증가
- 작은 앱에는 과한 설계

**활용 예시**:
- iOS 대형 앱 (Uber, Airbnb 변형)
- Android Compose Navigation + Coordinator 변형
- Cross-platform 네비게이션 레이어

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
interface Coordinator { fun start() }

class LoginCoordinator(private val nav: Navigator) : Coordinator {
    override fun start() {
        nav.push(LoginScreen(onSuccess = { HomeCoordinator(nav).start() }))
    }
}
```

**관련 패턴**: MVVM, Mediator, Facade

---

## 6. VIPER (View-Interactor-Presenter-Entity-Router)

**목적**: Clean Architecture를 iOS 화면 단위에 적용하여 단일 책임을 극단까지 분리합니다.

**특징**:
- View: 표현 / Interactor: 비즈니스 로직 / Presenter: View ↔ Interactor 조율 / Entity: 도메인 모델 / Router: 네비게이션
- 다섯 컴포넌트 모두 프로토콜 기반 의존성 역전
- 화면당 평균 5~7개 파일 생성

**장점**:
- 각 컴포넌트 단위 테스트 매우 용이
- 대규모 팀에서 책임 경계 명확
- 의존성 역전 철저

**단점**:
- 보일러플레이트 폭증
- 작은 앱에는 명백히 오버킬
- 학습 곡선 가파름

**활용 예시**:
- 대형 iOS 엔터프라이즈 앱
- 멀티팀 협업 코드베이스
- Mutual Mobile 가이드라인

**난이도**: 매우 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
interface UserView { fun render(name: String) }
interface UserInteractor { fun fetch(id: String): User }
interface UserRouter { fun navigateToDetail(id: String) }

class UserPresenter(
    private val view: UserView,
    private val interactor: UserInteractor,
    private val router: UserRouter,
) {
    fun onLoad(id: String) = view.render(interactor.fetch(id).name)
    fun onTap(id: String) = router.navigateToDetail(id)
}
```

**관련 패턴**: Clean Architecture, MVP, MVVM-C

---

<a id="7-flux--redux"></a>

## 7. Flux / Redux

**목적**: 단일 Store에 불변 상태를 보관하고, Action → Reducer → Store → View 의 순환 단방향 흐름으로 상태를 갱신합니다.

**특징**:
- Single source of truth (단일 Store)
- 순수 함수 Reducer
- 모든 변경은 Action 발행으로만 발생

**장점**:
- 디버깅과 로깅 단순 (Action 로그만 보면 됨)
- Hot reload / Time-travel 가능
- 다중 컴포넌트 상태 공유 단순화

**단점**:
- 작은 변경에도 보일러플레이트
- Action/Reducer 파일 증식
- 비동기는 별도 미들웨어 필요 (Thunk, Saga, Epic)

**활용 예시**:
- React + Redux 웹앱
- Facebook Flux (오리지널)
- ngrx (Angular), Vuex (Vue)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
data class AppState(val todos: List<String> = emptyList())
sealed class Action { data class Add(val text: String) : Action() }

fun reduce(state: AppState, action: Action): AppState = when (action) {
    is Action.Add -> state.copy(todos = state.todos + action.text)
}

class Store(initial: AppState) {
    private val _state = MutableStateFlow(initial)
    val state: StateFlow<AppState> = _state
    fun dispatch(a: Action) { _state.value = reduce(_state.value, a) }
}
```

**관련 패턴**: MVI, Observer, Command

---

## 8. Layered Architecture (N-tier)

**목적**: 시스템을 Presentation / Application / Domain / Infrastructure 등 수평 계층으로 분리하고, 상위 계층만 하위 계층에 의존하게 합니다.

**특징**:
- 상위 → 하위 단방향 의존 (역참조 금지)
- 각 계층은 인터페이스로 추상화
- 가장 보편적이고 입문 친화적

**장점**:
- 이해와 도입 쉬움
- 계층별 책임 명확
- 단위 테스트 가능 (Mock 주입)

**단점**:
- 계층 통과 로직이 단순 pass-through일 수 있음
- 비즈니스 변경이 여러 계층을 동시에 건드림
- 도메인이 인프라에 묶이기 쉬움

**활용 예시**:
- Spring Boot 표준 구조 (controller/service/repository)
- 전통적 엔터프라이즈 자바
- 기본 백엔드 템플릿 다수

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// presentation
class UserController(private val service: UserService) {
    fun get(id: String) = service.find(id)
}
// application
class UserService(private val repo: UserRepository) {
    fun find(id: String) = repo.findById(id)
}
// infrastructure
class UserRepository { fun findById(id: String): User = TODO() }
```

**관련 패턴**: Clean Architecture, Hexagonal, MVC

---

## 9. Clean Architecture

**목적**: 도메인을 가장 안쪽 원에 두고, 의존성이 외부에서 내부로만 향하도록 강제하여 비즈니스 규칙을 프레임워크/DB로부터 격리합니다.

**특징**:
- Entities ← Use Cases ← Interface Adapters ← Frameworks & Drivers
- DIP를 통한 의존성 역전 (Boundary 인터페이스)
- Uncle Bob (Robert C. Martin) 정립

**장점**:
- 프레임워크 교체에 강건 (DB, Web, UI)
- 비즈니스 규칙 단위 테스트 매우 용이
- 장기 유지보수성 높음

**단점**:
- 초기 보일러플레이트 큼
- 작은 프로젝트엔 과도
- DTO ↔ Entity 매핑 코드 증가

**활용 예시**:
- 엔터프라이즈 도메인 헤비 시스템
- Android 공식 권장 아키텍처 변형
- 결제, 금융, ERP 백엔드

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// domain (entity)
data class Order(val id: String, val amount: Int)

// use case
interface OrderRepository { fun save(o: Order) }
class PlaceOrder(private val repo: OrderRepository) {
    fun execute(o: Order) = repo.save(o)
}

// infrastructure (adapter)
class SqlOrderRepository : OrderRepository { override fun save(o: Order) = TODO() }
```

**관련 패턴**: Hexagonal, Onion, DDD

---

## 10. Hexagonal Architecture (Ports & Adapters)

**목적**: 도메인 코어를 중앙에 두고, 외부와의 모든 상호작용을 Port(인터페이스)와 Adapter(구현)로 분리하여 도메인을 환경 독립적으로 만듭니다.

**특징**:
- Driving Port (사용자 → 도메인) / Driven Port (도메인 → 외부)
- 도메인은 Port 인터페이스만 알고 Adapter 모름
- Alistair Cockburn 제안

**장점**:
- 테스트 시 In-memory Adapter로 빠른 검증
- 외부 시스템(DB, MQ, API) 교체 용이
- 도메인 순수성 유지

**단점**:
- Port/Adapter 매핑 보일러플레이트
- 추상화 비용 증가
- 초보자에게 직관성 낮음

**활용 예시**:
- 마이크로서비스 도메인 코어
- DDD 기반 백엔드
- 결제, 인증 코어 모듈

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// driving port
interface PayUseCase { fun pay(amount: Int): Boolean }

// domain
class PayService(private val pg: PaymentGatewayPort) : PayUseCase {
    override fun pay(amount: Int) = pg.charge(amount)
}

// driven port + adapter
interface PaymentGatewayPort { fun charge(amount: Int): Boolean }
class StripeAdapter : PaymentGatewayPort { override fun charge(a: Int) = true }
```

**관련 패턴**: Clean Architecture, Onion, Adapter

---

## 11. Onion Architecture

**목적**: 도메인 모델을 가장 안쪽 원으로 두고, 도메인 서비스 → 애플리케이션 서비스 → 인프라/UI 순으로 동심원을 구성합니다.

**특징**:
- 모든 의존성이 안쪽 원을 향함
- Domain Model이 외부 인터페이스(Repository)를 정의
- Clean Architecture와 유사하나 더 단순한 표현

**장점**:
- 도메인 중심 사고 강제
- 외부 의존성 격리
- 테스트 가능성 높음

**단점**:
- Clean Architecture와 차이 모호
- 매핑 레이어 증가
- 의사결정 비용 (어떤 원에 둘 것인가)

**활용 예시**:
- .NET 엔터프라이즈 백엔드
- Jeffrey Palermo 정립 사례
- DDD + CQRS 결합 시스템

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제**:
```kotlin
// domain core
data class Customer(val id: String, val name: String)
interface CustomerRepository { fun find(id: String): Customer? }

// domain service
class CustomerService(private val repo: CustomerRepository) {
    fun greet(id: String) = repo.find(id)?.let { "Hello, ${it.name}" }
}

// infra (outer ring) implements inner port
class InMemoryCustomerRepository : CustomerRepository {
    override fun find(id: String) = Customer(id, "Alice")
}
```

**관련 패턴**: Clean Architecture, Hexagonal, DDD

---

## 12. Modular Monolith

**목적**: 단일 배포 단위 내부에서 모듈 경계(소유권, 데이터, API)를 엄격히 분리하여 마이크로서비스의 운영 비용 없이 모듈성을 확보합니다.

**특징**:
- 모듈 간 통신은 명시적 API/이벤트만 허용
- DB 스키마/테이블 모듈별 소유
- 단일 배포, 단일 프로세스

**장점**:
- 운영 단순 (단일 배포/모니터링)
- 트랜잭션 일관성 보장 용이
- 모듈을 향후 서비스로 분리 쉬움

**단점**:
- 경계 위반 유혹 (동일 프로세스이므로)
- 모듈별 독립 스케일 불가
- 빌드 시간 증가 가능

**활용 예시**:
- Shopify 초기 아키텍처
- Modulith (Spring)
- 본 프로젝트의 Server (Modular Monolith로 정립)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// module boundary via package + interface
package billing
interface BillingApi { fun charge(orderId: String): Boolean }

package shipping
class ShippingService(private val billing: billing.BillingApi) {
    fun ship(orderId: String) { if (billing.charge(orderId)) println("Shipped") }
}
```

**관련 패턴**: Microservices, Hexagonal, DDD

---

## 13. Microservices

**목적**: 시스템을 비즈니스 능력(capability) 단위로 분리된 독립 배포 가능한 작은 서비스들로 구성합니다.

**특징**:
- 서비스마다 독립 DB, 독립 배포
- HTTP/gRPC/메시지 큐로 통신
- 서비스별 기술 스택 자유

**장점**:
- 독립 스케일링 및 배포
- 장애 격리
- 팀 자율성 (Conway's Law)

**단점**:
- 분산 시스템 복잡성 (네트워크, 일관성)
- 운영 부담 (관측성, CI/CD, 인프라)
- 데이터 분산 → 분산 트랜잭션 문제

**활용 예시**:
- Netflix, Amazon, Uber
- Spring Cloud / Istio 기반 시스템
- 대규모 SaaS 백엔드

**난이도**: 매우 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// order-service exposes REST
fun Application.orderModule() {
    routing {
        post("/orders") {
            val req = call.receive<CreateOrder>()
            // publish event to message bus
            EventBus.publish("order.created", req)
            call.respond(HttpStatusCode.Created)
        }
    }
}
```

**관련 패턴**: Modular Monolith, Event-Driven, API Gateway, Service Mesh

---

## 14. Service-Oriented Architecture (SOA)

**목적**: 재사용 가능한 비즈니스 서비스들을 ESB(Enterprise Service Bus)를 통해 조율하여 엔터프라이즈 통합을 달성합니다.

**특징**:
- ESB가 라우팅, 변환, 오케스트레이션 담당
- 서비스 계약을 WSDL/SOAP로 정의
- 마이크로서비스보다 굵은 단위(coarse-grained)

**장점**:
- 레거시 시스템 통합 용이
- 비즈니스 서비스 재사용
- 표준화된 계약

**단점**:
- ESB가 단일 장애점 / 병목
- 무거운 미들웨어
- 마이크로서비스로 대체되는 추세

**활용 예시**:
- 2000년대 엔터프라이즈 통합
- IBM WebSphere, Oracle Fusion
- 금융권 레거시 미들웨어

**난이도**: 높음 | **사용 빈도**: ★★☆☆☆

**Kotlin 예제**:
```kotlin
// pseudo-ESB routing
class EnterpriseServiceBus {
    private val routes = mutableMapOf<String, (Any) -> Any>()
    fun register(topic: String, handler: (Any) -> Any) { routes[topic] = handler }
    fun send(topic: String, payload: Any): Any? = routes[topic]?.invoke(payload)
}
```

**관련 패턴**: Microservices, API Gateway, Mediator

---

## 15. Event-Driven Architecture

**목적**: 컴포넌트 간 결합을 이벤트 발행/구독으로 대체하여 비동기 확장성과 느슨한 결합을 달성합니다.

**특징**:
- Producer → Broker(Kafka, RabbitMQ) → Consumer
- 명령형 호출 대신 이벤트 알림
- Pub/Sub 또는 Event Streaming

**장점**:
- 느슨한 결합 (Producer는 Consumer를 모름)
- 비동기 처리로 처리량 증가
- 새 Consumer 추가가 기존 코드 변경 없음

**단점**:
- 흐름 추적 어려움 (분산 트레이싱 필수)
- 이벤트 순서/중복 처리 필요
- 디버깅 난이도 높음

**활용 예시**:
- Kafka 기반 스트리밍 파이프라인
- IoT / 센서 데이터 처리
- 도메인 이벤트(DDD) 발행

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
data class OrderCreated(val orderId: String, val amount: Int)

object EventBus {
    private val subs = mutableMapOf<String, MutableList<(Any) -> Unit>>()
    fun subscribe(topic: String, handler: (Any) -> Unit) {
        subs.getOrPut(topic) { mutableListOf() }.add(handler)
    }
    fun publish(topic: String, event: Any) { subs[topic]?.forEach { it(event) } }
}
```

**관련 패턴**: Observer, CQRS, Event Sourcing, Saga

---

## 16. Serverless Architecture

**목적**: 인프라 관리 없이 함수 단위(FaaS) + 관리형 백엔드(BaaS) 조합으로 이벤트 트리거에 따라 자동 스케일되는 시스템을 구성합니다.

**특징**:
- 함수는 무상태(stateless)
- 사용한 만큼 과금 (idle 비용 0)
- 이벤트 트리거 (HTTP, S3, DynamoDB Stream, Cron)

**장점**:
- 인프라 운영 비용 사실상 0
- 트래픽 0~수천 RPS 자동 스케일
- 빠른 시제품 개발

**단점**:
- Cold start latency
- 벤더 락인 (AWS Lambda, GCP Functions)
- 장기 실행 작업 부적합 (15분 제한 등)

**활용 예시**:
- AWS Lambda + API Gateway + DynamoDB
- 이미지 리사이즈, 알림 전송
- 이벤트 기반 ETL

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// AWS Lambda handler (Kotlin)
class OrderHandler : RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {
    override fun handleRequest(
        event: APIGatewayProxyRequestEvent,
        ctx: Context,
    ): APIGatewayProxyResponseEvent {
        val body = event.body ?: "{}"
        return APIGatewayProxyResponseEvent().withStatusCode(200).withBody("ok:$body")
    }
}
```

**관련 패턴**: Microservices, Event-Driven, BFF
