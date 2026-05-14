# GoF 디자인 패턴 코드 템플릿

각 패턴별 Kotlin, Java, Swift, Python 코드 템플릿입니다.

---

# 생성 패턴

## Singleton

### Kotlin
```kotlin
object Singleton {
    fun doSomething() {
        println("Hello from Singleton")
    }
}

// 사용
fun main() {
    Singleton.doSomething()
}
```

### Java
```java
public class Singleton {
    private static volatile Singleton instance;

    private Singleton() {}

    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }

    public void doSomething() {
        System.out.println("Hello from Singleton");
    }
}
```

### Swift
```swift
class Singleton {
    static let shared = Singleton()

    private init() {}

    func doSomething() {
        print("Hello from Singleton")
    }
}
```

### Python
```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def do_something(self):
        print("Hello from Singleton")
```

---

## Factory Method

### Kotlin
```kotlin
interface Product {
    fun use()
}

class ConcreteProductA : Product {
    override fun use() = println("Product A 사용")
}

class ConcreteProductB : Product {
    override fun use() = println("Product B 사용")
}

abstract class Creator {
    abstract fun factoryMethod(): Product

    fun operation() {
        val product = factoryMethod()
        product.use()
    }
}

class ConcreteCreatorA : Creator() {
    override fun factoryMethod(): Product = ConcreteProductA()
}

class ConcreteCreatorB : Creator() {
    override fun factoryMethod(): Product = ConcreteProductB()
}
```

### Java
```java
interface Product {
    void use();
}

class ConcreteProductA implements Product {
    @Override
    public void use() {
        System.out.println("Product A 사용");
    }
}

abstract class Creator {
    public abstract Product factoryMethod();

    public void operation() {
        Product product = factoryMethod();
        product.use();
    }
}

class ConcreteCreatorA extends Creator {
    @Override
    public Product factoryMethod() {
        return new ConcreteProductA();
    }
}
```

---

## Builder

### Kotlin
```kotlin
data class Pizza(
    val dough: String,
    val sauce: String,
    val topping: String
) {
    class Builder {
        private var dough: String = "기본 도우"
        private var sauce: String = "토마토"
        private var topping: String = "치즈"

        fun dough(dough: String) = apply { this.dough = dough }
        fun sauce(sauce: String) = apply { this.sauce = sauce }
        fun topping(topping: String) = apply { this.topping = topping }
        fun build() = Pizza(dough, sauce, topping)
    }
}

// 사용
val pizza = Pizza.Builder()
    .dough("씬 도우")
    .sauce("바베큐")
    .topping("페퍼로니")
    .build()
```

### Java
```java
public class Pizza {
    private final String dough;
    private final String sauce;
    private final String topping;

    private Pizza(Builder builder) {
        this.dough = builder.dough;
        this.sauce = builder.sauce;
        this.topping = builder.topping;
    }

    public static class Builder {
        private String dough = "기본 도우";
        private String sauce = "토마토";
        private String topping = "치즈";

        public Builder dough(String dough) {
            this.dough = dough;
            return this;
        }

        public Builder sauce(String sauce) {
            this.sauce = sauce;
            return this;
        }

        public Builder topping(String topping) {
            this.topping = topping;
            return this;
        }

        public Pizza build() {
            return new Pizza(this);
        }
    }
}
```

---

# 구조 패턴

## Adapter

### Kotlin
```kotlin
interface Target {
    fun request(): String
}

class Adaptee {
    fun specificRequest(): String = "Adaptee의 특수 기능"
}

class Adapter(private val adaptee: Adaptee) : Target {
    override fun request(): String = adaptee.specificRequest()
}

// 사용
fun main() {
    val adaptee = Adaptee()
    val adapter = Adapter(adaptee)
    println(adapter.request())
}
```

### Java
```java
interface Target {
    String request();
}

class Adaptee {
    public String specificRequest() {
        return "Adaptee의 특수 기능";
    }
}

class Adapter implements Target {
    private final Adaptee adaptee;

    public Adapter(Adaptee adaptee) {
        this.adaptee = adaptee;
    }

    @Override
    public String request() {
        return adaptee.specificRequest();
    }
}
```

---

## Decorator

### Kotlin
```kotlin
interface Coffee {
    fun cost(): Double
    fun description(): String
}

class SimpleCoffee : Coffee {
    override fun cost() = 1.0
    override fun description() = "커피"
}

abstract class CoffeeDecorator(private val coffee: Coffee) : Coffee {
    override fun cost() = coffee.cost()
    override fun description() = coffee.description()
}

class Milk(coffee: Coffee) : CoffeeDecorator(coffee) {
    override fun cost() = super.cost() + 0.5
    override fun description() = super.description() + " + 우유"
}

class Sugar(coffee: Coffee) : CoffeeDecorator(coffee) {
    override fun cost() = super.cost() + 0.2
    override fun description() = super.description() + " + 설탕"
}

// 사용
fun main() {
    var coffee: Coffee = SimpleCoffee()
    coffee = Milk(coffee)
    coffee = Sugar(coffee)
    println("${coffee.description()}: ${coffee.cost()}원")
}
```

---

## Proxy

### Kotlin
```kotlin
interface Image {
    fun display()
}

class RealImage(private val fileName: String) : Image {
    init {
        loadFromDisk()
    }

    private fun loadFromDisk() {
        println("Loading $fileName from disk...")
    }

    override fun display() {
        println("Displaying $fileName")
    }
}

class ProxyImage(private val fileName: String) : Image {
    private var realImage: RealImage? = null

    override fun display() {
        if (realImage == null) {
            realImage = RealImage(fileName)
        }
        realImage?.display()
    }
}

// 사용 - 이미지가 실제로 표시될 때만 로드됨
val image = ProxyImage("photo.jpg")
image.display()  // 이때 로드됨
image.display()  // 캐시된 이미지 사용
```

---

# 행위 패턴

## Observer

### Kotlin
```kotlin
interface Observer {
    fun update(message: String)
}

class Subject {
    private val observers = mutableListOf<Observer>()

    fun attach(observer: Observer) {
        observers.add(observer)
    }

    fun detach(observer: Observer) {
        observers.remove(observer)
    }

    fun notifyObservers(message: String) {
        observers.forEach { it.update(message) }
    }
}

class ConcreteObserver(private val name: String) : Observer {
    override fun update(message: String) {
        println("$name 수신: $message")
    }
}

// 사용
fun main() {
    val subject = Subject()
    val observer1 = ConcreteObserver("Observer1")
    val observer2 = ConcreteObserver("Observer2")

    subject.attach(observer1)
    subject.attach(observer2)
    subject.notifyObservers("Hello!")
}
```

### Java
```java
import java.util.ArrayList;
import java.util.List;

interface Observer {
    void update(String message);
}

class Subject {
    private List<Observer> observers = new ArrayList<>();

    public void attach(Observer observer) {
        observers.add(observer);
    }

    public void notifyObservers(String message) {
        for (Observer observer : observers) {
            observer.update(message);
        }
    }
}
```

---

## Strategy

### Kotlin
```kotlin
interface PaymentStrategy {
    fun pay(amount: Int)
}

class CreditCardStrategy(private val cardNumber: String) : PaymentStrategy {
    override fun pay(amount: Int) {
        println("${amount}원을 신용카드($cardNumber)로 결제")
    }
}

class KakaoPayStrategy(private val phoneNumber: String) : PaymentStrategy {
    override fun pay(amount: Int) {
        println("${amount}원을 카카오페이($phoneNumber)로 결제")
    }
}

class ShoppingCart {
    private var paymentStrategy: PaymentStrategy? = null

    fun setPaymentStrategy(strategy: PaymentStrategy) {
        paymentStrategy = strategy
    }

    fun checkout(amount: Int) {
        paymentStrategy?.pay(amount)
    }
}

// 사용
fun main() {
    val cart = ShoppingCart()

    cart.setPaymentStrategy(CreditCardStrategy("1234-5678"))
    cart.checkout(10000)

    cart.setPaymentStrategy(KakaoPayStrategy("010-1234-5678"))
    cart.checkout(20000)
}
```

---

## Command

### Kotlin
```kotlin
interface Command {
    fun execute()
    fun undo()
}

class Light {
    fun on() = println("불이 켜졌습니다")
    fun off() = println("불이 꺼졌습니다")
}

class LightOnCommand(private val light: Light) : Command {
    override fun execute() = light.on()
    override fun undo() = light.off()
}

class LightOffCommand(private val light: Light) : Command {
    override fun execute() = light.off()
    override fun undo() = light.on()
}

class RemoteControl {
    private val history = mutableListOf<Command>()

    fun execute(command: Command) {
        command.execute()
        history.add(command)
    }

    fun undo() {
        if (history.isNotEmpty()) {
            history.removeLast().undo()
        }
    }
}

// 사용
fun main() {
    val light = Light()
    val remote = RemoteControl()

    remote.execute(LightOnCommand(light))
    remote.execute(LightOffCommand(light))
    remote.undo()  // 불이 다시 켜짐
}
```

---

## State

### Kotlin
```kotlin
interface State {
    fun handle(context: Context)
}

class Context {
    var state: State = ConcreteStateA()

    fun request() {
        state.handle(this)
    }
}

class ConcreteStateA : State {
    override fun handle(context: Context) {
        println("State A 처리 → State B로 전이")
        context.state = ConcreteStateB()
    }
}

class ConcreteStateB : State {
    override fun handle(context: Context) {
        println("State B 처리 → State A로 전이")
        context.state = ConcreteStateA()
    }
}

// 사용
fun main() {
    val context = Context()
    context.request()  // State A → B
    context.request()  // State B → A
    context.request()  // State A → B
}
```

---

## Template Method

### Kotlin
```kotlin
abstract class DataMiner {
    // 템플릿 메서드 (final로 선언하여 오버라이드 방지)
    fun mine(path: String) {
        val file = openFile(path)
        val rawData = extractData(file)
        val data = parseData(rawData)
        val analysis = analyzeData(data)
        sendReport(analysis)
        closeFile(file)
    }

    abstract fun openFile(path: String): String
    abstract fun extractData(file: String): String
    abstract fun parseData(rawData: String): String

    // 기본 구현 제공 (선택적 오버라이드)
    open fun analyzeData(data: String): String = "분석 결과: $data"
    open fun sendReport(analysis: String) = println("Report: $analysis")
    open fun closeFile(file: String) = println("파일 닫기")
}

class PDFDataMiner : DataMiner() {
    override fun openFile(path: String) = "PDF: $path"
    override fun extractData(file: String) = "PDF 데이터"
    override fun parseData(rawData: String) = "파싱된 $rawData"
}

class CSVDataMiner : DataMiner() {
    override fun openFile(path: String) = "CSV: $path"
    override fun extractData(file: String) = "CSV 데이터"
    override fun parseData(rawData: String) = "파싱된 $rawData"
}
```

---

# Android 특화 패턴 적용

## Repository 패턴 (MVVM + Clean Architecture)

### Kotlin
```kotlin
// Domain Layer
interface UserRepository {
    suspend fun getUser(id: String): User
    suspend fun saveUser(user: User)
}

// Data Layer
class UserRepositoryImpl(
    private val localDataSource: UserLocalDataSource,
    private val remoteDataSource: UserRemoteDataSource
) : UserRepository {

    override suspend fun getUser(id: String): User {
        return try {
            remoteDataSource.getUser(id).also { user ->
                localDataSource.saveUser(user)
            }
        } catch (e: Exception) {
            localDataSource.getUser(id)
        }
    }

    override suspend fun saveUser(user: User) {
        localDataSource.saveUser(user)
        remoteDataSource.saveUser(user)
    }
}
```

## ViewModel + StateFlow (Observer 패턴)

### Kotlin
```kotlin
class UserViewModel(
    private val getUserUseCase: GetUserUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    fun loadUser(id: String) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            try {
                val user = getUserUseCase(id)
                _uiState.value = UiState.Success(user)
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message)
            }
        }
    }

    sealed class UiState {
        object Loading : UiState()
        data class Success(val user: User) : UiState()
        data class Error(val message: String?) : UiState()
    }
}
```

## DI with Hilt (Factory + Singleton)

### Kotlin
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "app.db"
        ).build()
    }

    @Provides
    fun provideUserDao(database: AppDatabase): UserDao {
        return database.userDao()
    }

    @Provides
    @Singleton
    fun provideUserRepository(
        localDataSource: UserLocalDataSource,
        remoteDataSource: UserRemoteDataSource
    ): UserRepository {
        return UserRepositoryImpl(localDataSource, remoteDataSource)
    }
}
```
