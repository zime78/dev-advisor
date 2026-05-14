# 모바일 앱 운영 패턴 (Mobile App Operational Patterns)

iOS / Android / Flutter / React Native 공통의 **운영·생명주기·배포** 패턴. 앱 아키텍처(MVVM-C / VIPER — `architectural.md`)·모바일 보안(`security-mobile.md`) 와 별개로, **사용자 손에 들어간 뒤 발생하는** 운영 관심사 13 항목.

**핵심 관심사**: 생명주기 / 백그라운드 / 푸시·딥링크 / 결제·구독 / OTA · 배포 / 성능·전력 — 어느 하나라도 빠지면 출시 후 사고로 직결.

**관련 카탈로그**:
- [architectural.md](architectural.md) — MVVM-C, VIPER, Flux/Redux (앱 내부 구조)
- [`../security/security-mobile.md`](../security/security-mobile.md) — Certificate Pinning, App Attest, RASP, Secure Storage
- [observability.md](observability.md) — Crash & ANR 은 분산 트레이싱·SLO 와 결합

---

## 1. App Lifecycle State Machine (앱 생명주기 상태머신)

<a id="app-lifecycle"></a>

**목적**: OS 가 앱에 보내는 생명주기 이벤트(포그라운드 진입·백그라운드 진입·종료)를 단일 상태머신으로 모델링하여, 화면 상태 복원과 리소스 해제를 결정론적으로 처리합니다.

**핵심 메커니즘**:
- **Android**: `Created → Started → Resumed → Paused → Stopped → Destroyed` 6 상태 + `onSaveInstanceState` 로 process death 대비. `Lifecycle.Event` / `LifecycleOwner` / `repeatOnLifecycle(STARTED)`
- **iOS**: `Not Running / Inactive / Active / Background / Suspended` 5 상태. UIScene 도입 후 (iOS 13+) `UISceneDelegate` 가 앱 단위 → 씬 단위로 분리. `scene(_:willConnectTo:options:)`
- **Flutter**: `AppLifecycleState.resumed / inactive / paused / detached / hidden(3.13+)` — `WidgetsBindingObserver` 로 구독
- **Cold / Warm / Hot Start**: process 가 없는 진입(cold) vs 백그라운드 복귀(warm) vs 포그라운드 재활성(hot). 측정 지표가 모두 다름
- **Process Death**: Android 는 백그라운드에서 OS 가 임의 종료. SavedStateHandle / `rememberSaveable` 로 UI 상태 복원

**장점**:
- 화면 상태·구독·타이머의 누수 차단 (Resumed 일 때만 collect)
- 백그라운드 진입 시 비밀번호 마스킹·인증 만료 처리 가능
- A/B 테스트, 광고, 분석 SDK 의 세션 정의 일관화

**단점/주의**:
- iOS multi-scene 시 한 앱 인스턴스에 여러 씬이 공존 — "앱이 백그라운드" ≠ "모든 씬이 백그라운드"
- Android `onStop` 이후 process kill 까지 시간차가 있어 finalizer 의존 금지
- Flutter `paused` 는 iOS 의 background, Android 의 stopped 양쪽을 추상화 — 플랫폼 차이 코드는 별도 채널 필요

**활용 예시**: `androidx.lifecycle.repeatOnLifecycle`, `UIApplication.didEnterBackgroundNotification`, `WidgetsBindingObserver.didChangeAppLifecycleState`, RN `AppState`

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin (Android) 예제**:
```kotlin
class HomeFragment : Fragment() {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewLifecycleOwner.lifecycleScope.launch {
            // STARTED 동안만 collect — STOP 시 cancel, START 재진입 시 restart
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { render(it) }
            }
        }
    }
}

class SecureActivity : AppCompatActivity() {
    override fun onStop() {
        super.onStop()
        // 백그라운드 진입 시 민감 화면 가림 (Task Switcher 캐시 차단)
        window.setFlags(WindowManager.LayoutParams.FLAG_SECURE,
                        WindowManager.LayoutParams.FLAG_SECURE)
    }
}
```

**관련 패턴**: Crash & ANR Handling, App Cold/Warm/Hot Start, Permission Request UX

---

## 2. Background Task (백그라운드 작업)

<a id="background-task"></a>

**목적**: 앱이 포그라운드가 아닐 때도 데이터 동기화·업로드·정기 갱신을 수행하되, OS 의 배터리 보호 정책(Doze, App Standby) 을 위반하지 않도록 OS 스케줄러에 위임합니다.

**핵심 메커니즘**:
- **Android WorkManager**: 제약(network, charging, battery) 기반 deferred work. `OneTimeWorkRequest` / `PeriodicWorkRequest` / `Constraints.Builder`. Doze / App Standby 친화적
- **Android Foreground Service**: 사용자 인지 가능한 작업(음악 재생, 위치 추적). API 34+ 부터는 `foregroundServiceType` 명시 필수 (정책 위반 시 미게재)
- **iOS BGTaskScheduler**: `BGAppRefreshTask` (≤30s, ~수십 분 주기) vs `BGProcessingTask` (>1 분, 충전·네트워크 조건). `Info.plist` `BGTaskSchedulerPermittedIdentifiers` 등록
- **iOS Background Modes**: audio, location, voip, fetch, remote-notification, processing — Capability 명시 필요. 위반 시 리젝트
- **Doze / App Standby Buckets** (Android): Active / Working Set / Frequent / Rare / Restricted — 버킷이 낮을수록 work 실행 빈도 강제 감소
- 작업 멱등성 필수 — OS 가 임의 재시도/지연 실행

**장점**:
- 배터리·발열 사고 최소화 (OS 가 조율)
- Process 가 죽어도 OS 스케줄러가 책임지고 재실행
- 네트워크/전원 조건 제약을 선언적으로 표현

**단점/주의**:
- 정확한 실행 시각 보장 불가 — "1 시간에 한 번" 은 best-effort
- iOS BGTask 는 시뮬레이터 미동작 — 실기기 + lldb `e -l objc -- (void)[[BGTaskScheduler sharedScheduler] _simulateLaunchForTaskWithIdentifier:@"..."]`
- Foreground Service 남용 시 Play Console "과도한 배터리 사용" 경고 + 등재 정책 위반

**활용 예시**: WorkManager (Firestore 오프라인 sync), BGAppRefreshTask (뉴스피드 prefetch), BGProcessingTask (사진 백업)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin (Android WorkManager) 예제**:
```kotlin
class SyncWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result = try {
        SyncRepository.sync()  // 멱등 보장 필수
        Result.success()
    } catch (e: IOException) {
        Result.retry()         // 네트워크 일시 실패 → 지수 백오프
    } catch (e: Exception) {
        Result.failure()       // 영구 실패 → 큐 제거
    }
}

val req = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
    .setConstraints(
        Constraints.Builder()
            .setRequiredNetworkType(NetworkType.UNMETERED)
            .setRequiresBatteryNotLow(true)
            .build()
    )
    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
    .build()

WorkManager.getInstance(ctx)
    .enqueueUniquePeriodicWork("sync", ExistingPeriodicWorkPolicy.KEEP, req)
```

**관련 패턴**: App Lifecycle, Push Notification (silent push 로 sync 트리거), Battery & Performance Profiling

---

## 3. Push Notification Topology (푸시 알림 토폴로지)

<a id="push-notification"></a>

**목적**: 서버가 사용자 단말에 비동기로 메시지를 전달하기 위한 APNs / FCM 토폴로지를 구성하여, 토큰 수명·전달 보장·배터리 비용을 절충합니다.

**핵심 메커니즘**:
- **APNs (iOS)**: HTTP/2, JWT (`p8` key) 또는 인증서. payload ≤ 4 KB. `apns-priority: 10` (즉시) vs `5` (절전)
- **FCM (Android/cross-platform)**: HTTP v1 API (legacy server key 폐지), OAuth2 service account. data-only / notification / mixed message
- **Topic vs Token**: 토픽 구독은 broadcast 패턴(뉴스), 토큰 발신은 1:1 (예약 알림)
- **Silent / Background Push**: 사용자 비노출, 데이터 sync 트리거 — iOS `content-available: 1`, Android `priority: high` + data-only. 단말의 백그라운드 fetch 정책에 종속
- **Notification Service Extension (iOS)**: payload 도착 후 표시 직전 가로채서 미디어 첨부·복호화 가능 (≤30s)
- **Critical Alert (iOS)**: Do Not Disturb 무시. 특수 entitlement 필요 (의료·재난 한정 승인)
- **Token Refresh**: 앱 재설치·기기 복원·OS 업데이트 시 갱신. 서버에 token rotate 엔드포인트 필수

**장점**:
- 폴링 불필요 → 배터리·서버 비용 절감
- Critical 메시지(결제 완료, 매칭 알림) 의 빠른 도달
- Topic 으로 N 명에게 단일 호출로 발송

**단점/주의**:
- 전달 보장은 **best-effort** — 단말 종료/네트워크 단절 시 누락
- silent push 는 iOS Low Power Mode·Android Doze 에서 지연/드롭
- 사용자 비활성 토큰 누적 → DB 비대, APNs `410 Unregistered` / FCM `NotRegistered` 시 즉시 삭제

**활용 예시**: APNs `apns-push-type: background`, FCM `messages:send`, Notification Service Extension (E2EE 복호화)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Swift (APNs Notification Service Extension) 예제**:
```swift
import UserNotifications

class NotificationService: UNNotificationServiceExtension {
    var contentHandler: ((UNNotificationContent) -> Void)?
    var bestAttempt: UNMutableNotificationContent?

    override func didReceive(
        _ request: UNNotificationRequest,
        withContentHandler handler: @escaping (UNNotificationContent) -> Void
    ) {
        self.contentHandler = handler
        bestAttempt = (request.content.mutableCopy() as? UNMutableNotificationContent)

        // E2EE 복호화: 서버는 ciphertext 만 보내고 클라가 복호화
        if let cipher = request.content.userInfo["cipher"] as? String,
           let plain = MessageCrypto.decrypt(cipher) {
            bestAttempt?.body = plain
        }
        handler(bestAttempt ?? request.content)
    }

    override func serviceExtensionTimeWillExpire() {
        // 30s 한도 — 부분 결과라도 전달
        if let attempt = bestAttempt { contentHandler?(attempt) }
    }
}
```

**관련 패턴**: Background Task, Deep Link (notification tap → screen), Permission Request UX

---

## 4. Deep Link / Universal Link / App Link (딥링크)

<a id="deep-link"></a>

**목적**: URL 한 줄로 외부(이메일·푸시·웹·QR) 에서 앱 내 특정 화면을 열고, 미설치 시 스토어 또는 웹 fallback 으로 라우팅합니다.

**핵심 메커니즘**:
- **Custom URI Scheme**: `myapp://product/123` — 가장 오래된 방식. 다른 앱이 같은 scheme 등록 시 충돌·하이재킹 위험
- **iOS Universal Link**: `https://app.example.com/product/123` — 도메인 소유 검증 파일 `apple-app-site-association` (`.well-known/`, HTTPS, JSON, MIME `application/json`)
- **Android App Link**: `https://...` — `assetlinks.json` (`.well-known/`, SHA-256 signing cert fingerprint). `autoVerify=true` 인 intent-filter
- **Deferred Deep Link**: 앱 미설치 → 스토어 이동 → 설치 후 첫 실행 시 의도된 화면 진입. Branch / AppsFlyer / Firebase Dynamic Links(2025 종료) 같은 attribution SDK 필요
- **Hierarchy**: Universal Link / App Link 가 검증 실패하면 Safari·Chrome 에서 웹으로 떨어짐 — silent failover
- **Test**: iOS `xcrun simctl openurl booted https://...`, Android `adb shell am start -W -a android.intent.action.VIEW -d "https://..."`

**장점**:
- 사용자 한 번의 탭으로 정확한 화면 도달
- 마케팅 채널·노출 위치를 query string 으로 측정
- 웹 fallback 으로 미설치 사용자도 컨텐츠 소비

**단점/주의**:
- 도메인 검증 파일 누락·캐싱 문제로 Universal Link 가 사파리에서 열리는 사고 빈번
- Android 12+ 부터 `autoVerify` 검증 실패 시 영원히 비활성 — 출시 후 첫 검증이 중요
- Deferred Deep Link 는 클립보드·IP fingerprint 등 fragile 기법에 의존

**활용 예시**: 마케팅 캠페인 링크, 푸시 알림 tap, QR 스캔, 카카오톡/Slack 공유 미리보기

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Swift (iOS Universal Link 처리) 예제**:
```swift
// SceneDelegate
func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
    guard userActivity.activityType == NSUserActivityTypeBrowsingWeb,
          let url = userActivity.webpageURL else { return }

    // https://app.example.com/product/123?utm_source=push
    let path = url.pathComponents  // ["/", "product", "123"]
    if path.count >= 3, path[1] == "product" {
        let id = path[2]
        Router.shared.push(.productDetail(id: id, utm: url.queryParam("utm_source")))
    } else {
        Router.shared.fallbackToWeb(url)  // 라우팅 불가 시 in-app browser
    }
}
```

**관련 패턴**: Navigation Pattern, Push Notification, App Signing & Distribution (cert fingerprint 가 assetlinks 검증에 사용)

---

## 5. Navigation Pattern (네비게이션 패턴)

<a id="navigation-pattern"></a>

**목적**: Stack / Tab / Modal / Drawer 의 조합으로 화면 전환과 back stack 을 관리하여, 사용자가 "뒤로 가기" 를 누를 때 예측 가능한 경로로 복귀하게 합니다.

**핵심 메커니즘**:
- **Android Navigation Component / Jetpack Compose Navigation**: `NavController` + nav graph XML/Kotlin DSL. SavedStateHandle 로 인자 전달, deep link integration
- **iOS NavigationStack (iOS 16+) / UINavigationController**: declarative path binding (`@State path: [Route]`) vs imperative `pushViewController`. SwiftUI 의 `NavigationLink(value:)` 패턴
- **Flutter GoRouter / Navigator 2.0**: declarative URL-based routing. `ShellRoute` 로 Tab + Stack 중첩, `redirect` 로 인증 가드
- **React Native React Navigation**: Stack / Tab / Drawer Navigator 합성, linking config 로 딥링크 자동 처리
- **Back Stack 정책**: Android `OnBackPressedDispatcher` 로 화면별 가로채기. iOS `swipe-back` (left edge pan), 시스템 default 와 충돌 주의
- **Tab + Stack 중첩**: 각 탭이 독립 stack — 탭 전환 시 stack 보존 vs 리셋 정책 선택

**장점**:
- 화면 그래프를 한 곳에서 선언 → 라우팅 시각화·테스트 용이
- 딥링크 / 푸시 tap → 직접 화면 진입을 같은 API 로 처리
- 인자·결과 전달이 타입 안전 (Compose Navigation type-safe args, Swift Codable enum)

**단점/주의**:
- 중첩 Navigator(탭+스택+모달) 의 back stack 모델이 복잡 — "뒤로 가기" 동작에 대한 일관 규칙 필요
- iOS interactive pop gesture 와 custom gesture 충돌 시 좌측 edge 스와이프가 죽음
- Modal 화면에서 외부 딥링크 도착 시 모달 우선 닫기 정책 명시 필요

**활용 예시**: GoRouter (Flutter QGlobal 프로젝트 — `screen_usa`), Compose Navigation, SwiftUI NavigationStack, React Navigation

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin (Compose Navigation) 예제**:
```kotlin
@Serializable data object Home
@Serializable data class ProductDetail(val id: String)
@Serializable data object Cart

@Composable
fun AppNav() {
    val navController = rememberNavController()
    NavHost(navController, startDestination = Home) {
        composable<Home> {
            HomeScreen(onProductClick = { id ->
                navController.navigate(ProductDetail(id))
            })
        }
        composable<ProductDetail> { entry ->
            val args: ProductDetail = entry.toRoute()
            ProductDetailScreen(args.id, onCheckout = {
                navController.navigate(Cart) {
                    popUpTo(Home)  // back stack 정리: Home → Cart
                }
            })
        }
        composable<Cart> { CartScreen() }
    }
}
```

**관련 패턴**: Deep Link, App Lifecycle (process death → back stack 복원), Permission Request UX (인증 가드)

---

## 6. App Cold/Warm/Hot Start 최적화 (앱 시작 시간 최적화)

<a id="app-startup"></a>

**목적**: 사용자가 앱 아이콘을 탭한 순간부터 첫 의미있는 화면이 보이기까지 걸리는 시간(TTID / TTFD) 을 단축하여, 이탈률·앱 평점·OS 가 부여하는 우선순위를 개선합니다.

**핵심 메커니즘**:
- **Cold start**: process 미존재 → 새 프로세스 fork → Application/AppDelegate → 첫 Activity/Scene. 가장 무거움(보통 1~3s 목표)
- **Warm start**: process 존재, 일부 객체 GC. Activity/Scene 재생성만
- **Hot start**: 백그라운드 → 포그라운드 복귀. < 200ms 목표
- **TTID** (Time To Initial Display): 첫 프레임 그려진 시각. **TTFD** (Time To Fully Drawn): 데이터 로드 후 의미있는 콘텐츠 표시. Android `reportFullyDrawn()` / Macrobenchmark
- **Android App Startup library**: 여러 SDK 의 ContentProvider 초기화를 단일 `InitializationProvider` 로 통합 (병렬·지연 가능)
- **iOS Pre-main time**: `DYLD_PRINT_STATISTICS=1`. dylib 수, ObjC class load, +load 메서드 시간 측정
- **Splash 화면**: Android 12+ `core-splashscreen` (windowSplashScreen) — 가짜 splash Activity 금지. iOS LaunchScreen.storyboard (정적)
- **Lazy DI**: 첫 화면이 필요로 하지 않는 의존성 lazy 초기화. Hilt `@Singleton` 의 `provides` 람다, GetIt `Lazy` (Flutter)

**장점**:
- TTID 100ms 단축 시 retention 측정상 1~3 % 개선 사례
- Play Vitals / App Store Analytics 의 "slow start" 카테고리 회피
- 첫 화면 골든 패스가 빨라야 광고·딥링크 attribution 도 정확

**단점/주의**:
- main thread 에서 SDK 초기화 → 첫 프레임 지연 — 모든 third-party SDK 의 init 비용 측정 필수
- 가짜 splash Activity 는 Play 정책 위반 (Android 12+) + 추가 cold start 비용
- Hot start 가 느리면 사실은 백그라운드에서 process 가 죽은 것 — warm 으로 잘못 진단 주의

**활용 예시**: Macrobenchmark (`startup` benchmark), Firebase Performance, Instruments App Launch, Flutter DevTools timeline

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin (Android App Startup) 예제**:
```kotlin
// 1) 즉시 필요한 분석 SDK
class AnalyticsInitializer : Initializer<Analytics> {
    override fun create(context: Context): Analytics =
        Analytics.init(context).also { GlobalAnalytics.instance = it }
    override fun dependencies(): List<Class<out Initializer<*>>> = emptyList()
}

// 2) Analytics 가 준비된 후 crash reporter
class CrashInitializer : Initializer<CrashReporter> {
    override fun create(context: Context): CrashReporter =
        CrashReporter.init(context, GlobalAnalytics.instance)
    override fun dependencies() = listOf(AnalyticsInitializer::class.java)
}

// 3) 첫 화면이 그려진 뒤 lazy 로딩 (Activity.onResume 에서 트리거)
fun Activity.deferredInit() = lifecycleScope.launch(Dispatchers.IO) {
    AppStartup.getInstance(this@deferredInit)
        .initializeComponent(HeavySdkInitializer::class.java)
}
```

**관련 패턴**: App Lifecycle, Crash & ANR Handling, App Size (작은 binary → dyld 빠름)

---

## 7. Crash & ANR Handling (크래시·ANR 처리)

<a id="crash-anr"></a>

**목적**: 앱이 예외로 강제 종료되거나 메인 스레드가 멈춰 ANR(Application Not Responding) 다이얼로그가 뜨는 사고를 자동 수집·심볼리케이트·집계하여, 우선순위가 높은 안정성 회귀를 빠르게 식별합니다.

**핵심 메커니즘**:
- **Crashlytics / Sentry / Bugsnag**: native + managed exception, breadcrumb, session, user context 자동 수집. dSYM / Proguard mapping 업로드 → 심볼리케이트
- **Android ANR**: 메인 스레드가 5s 이상 입력 응답 못 하거나 BroadcastReceiver 가 10s 초과 시. `/data/anr/traces.txt` 와 Play Vitals 가 집계
- **StrictMode (Android)**: 메인 스레드의 디스크/네트워크 I/O, leaked closable, untagged socket 등 위반을 dev build 에서 즉시 노출
- **OOM (Out Of Memory)**: 큰 비트맵·메모리 누수가 누적되면 OS 가 즉시 kill. Crashlytics 는 사후 추적, LeakCanary 는 dev build 에서 leak 탐지
- **JNI / native crash (Android NDK, iOS C++)**: signal handler 필요. Crashlytics NDK / breakpad
- **Symbolicate**: 빌드 시 생성되는 dSYM(iOS) / mapping.txt(R8) 를 backend 에 업로드. 미업로드 시 stack 이 사람이 못 읽는 mangled 상태
- **Watchdog (iOS)**: 앱이 main thread 에서 일정 시간(launch ~20s, run ~10s) 응답 못 하면 OS 가 0x8badf00d 로 강제 종료

**장점**:
- 사용자가 신고하지 않은 사고도 자동 집계
- breadcrumb 으로 재현 시나리오 복원
- Play Vitals / App Store Connect 의 안정성 metric 이 검색 랭킹·featuring 에 영향

**단점/주의**:
- 심볼 파일 업로드 누락 → stack 분석 불가 (CI 에 강제 단계 추가 필요)
- ANR 은 stack 만 보고는 원인 추정 어려움 — Perfetto / Systrace 병행
- crash reporter 자체가 main thread init 에 시간 소요 → cold start 영향 주의

**활용 예시**: Firebase Crashlytics, Sentry Mobile, Bugsnag, LeakCanary, Perfetto trace

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin (StrictMode + Crashlytics 통합) 예제**:
```kotlin
class App : Application() {
    override fun onCreate() {
        super.onCreate()

        if (BuildConfig.DEBUG) {
            // Main thread I/O / leaked closable 즉시 노출
            StrictMode.setThreadPolicy(
                StrictMode.ThreadPolicy.Builder()
                    .detectAll()
                    .penaltyLog()
                    .build()
            )
            StrictMode.setVmPolicy(
                StrictMode.VmPolicy.Builder()
                    .detectLeakedClosableObjects()
                    .detectActivityLeaks()
                    .penaltyLog()
                    .build()
            )
        }

        // Uncaught exception 을 crashlytics 에 위임
        val default = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            Firebase.crashlytics.recordException(throwable)
            Firebase.crashlytics.setCustomKey("thread", thread.name)
            default?.uncaughtException(thread, throwable)
        }
    }
}
```

**관련 패턴**: App Lifecycle, App Startup (crash reporter init 비용), Battery & Performance Profiling

---

## 8. In-App Purchase / Subscription (인앱 결제·구독)

<a id="iap-subscription"></a>

**목적**: 디지털 상품·구독을 스토어 결제 시스템(StoreKit / Play Billing) 으로 처리하되, 영수증을 **서버에서 검증**하여 entitlement 를 부여하고, 환불·갱신·grace period 를 정확히 반영합니다.

**핵심 메커니즘**:
- **StoreKit 2 (iOS 15+)**: async/await API, `Transaction.currentEntitlements`, JWS 서명 영수증(서버에서 Apple public key 로 검증). StoreKit 1 receipt 도 동시 지원 필요
- **Google Play Billing v6 (2023+)**: `BillingClient`, `queryProductDetailsAsync`, `launchBillingFlow`, `acknowledgePurchase`. 구입 후 3 일 내 acknowledge 안 하면 자동 환불
- **서버 검증 필수**: 클라이언트 receipt 위변조 가능 — Apple App Store Server API / Google Play Developer API 로 서버가 직접 verify
- **Subscription**: auto-renew, free trial, intro price, billing retry, grace period, account hold — 각 상태별 entitlement 분기
- **Webhook (Server-to-Server)**: Apple App Store Server Notifications v2 (JWS), Google Real-Time Developer Notifications (Pub/Sub) — 갱신·환불·취소를 push 로 수신
- **Restore Purchases**: 사용자 기기 변경/재설치 시 entitlement 복원 버튼 의무 (Apple 가이드라인 3.1.1)
- **수수료**: 15% (Small Business / 1 년 이상 구독) / 30% — pricing 결정 시 반영

**장점**:
- OS 결제 UI 사용 → 결제수단·환불 정책 위탁
- Family Sharing / Ask to Buy 자동 지원
- Sandbox 계정으로 환불·갱신 흐름 테스트 가능

**단점/주의**:
- 영수증 서버 검증 누락 시 무료 사용 jailbreak / patched APK 로 우회됨
- Play Billing v6 의 `Pending` 상태(가족 승인·캐시 결제) 처리 누락 시 즉시 entitlement 부여 사고
- Apple 의 외부 결제 링크 허용은 미국·EU 한정·수수료 별도 — 지역별 정책 분기

**활용 예시**: StoreKit 2 `Transaction.updates`, Play Billing `BillingClient.queryPurchasesAsync`, RevenueCat / Adapty (cross-platform abstraction)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Swift (StoreKit 2 + 서버 검증) 예제**:
```swift
import StoreKit

@MainActor
final class SubscriptionStore: ObservableObject {
    @Published var entitled = false

    init() {
        Task { await observeTransactions() }
    }

    func purchase(_ product: Product) async throws {
        let result = try await product.purchase()
        switch result {
        case .success(let verification):
            let tx = try checkVerified(verification)
            // 서버에 JWS 전송 → Apple public key 로 검증 → DB entitlement 갱신
            try await Backend.verifyAndUnlock(jws: verification.jwsRepresentation)
            await tx.finish()
            entitled = true
        case .userCancelled, .pending: break
        @unknown default: break
        }
    }

    private func observeTransactions() async {
        for await update in Transaction.updates {
            if case .verified(let tx) = update {
                await tx.finish()
                entitled = await Backend.hasActiveEntitlement()
            }
        }
    }

    private func checkVerified<T>(_ r: VerificationResult<T>) throws -> T {
        switch r {
        case .verified(let v): return v
        case .unverified: throw StoreError.failedVerification
        }
    }
}
```

**관련 패턴**: App Signing (영수증 검증은 bundle id + team id 검증 포함), Push Notification (구독 만료 푸시), `security-mobile.md` (receipt anti-tamper)

---

## 9. OTA Update / Code Push (OTA 업데이트)

<a id="ota-update"></a>

**목적**: 스토어 심사 우회 없이 JS 번들·Dart AOT snapshot·이미지·설정을 무선으로 갱신하여, 핫픽스와 A/B 실험을 즉시 반영합니다.

**핵심 메커니즘**:
- **Expo EAS Update (React Native)**: 채널/브랜치 모델, runtime version 일치 시에만 적용. 자동 rollback
- **App Center CodePush (deprecated 2025-03)**: Microsoft 가 EOL. 새 프로젝트는 EAS Update / Shorebird 사용
- **Flutter Shorebird**: AOT-compiled Dart code 의 patch (Dart code 만 — 네이티브·assets 는 스토어 빌드 필요)
- **Capacitor Live Updates (Ionic)**: web bundle (HTML/JS/CSS) OTA
- **스토어 정책 경계**:
  - Apple: 4.7 조항 — JavaScriptCore 로 실행되는 코드만 OTA 허용. 네이티브 binary 교체 금지
  - Google: 더 관대하지만 Play Integrity 와 충돌 가능
- **Runtime version pinning**: 네이티브 API 가 바뀐 빌드에 구버전 JS 번들을 보내면 crash → 빌드별 runtime ID 매칭
- **Rollback**: 새 patch 가 crash 율 임계 초과하면 이전 stable 로 자동 복귀

**장점**:
- 핫픽스를 스토어 심사(보통 1~3 일) 우회로 즉시 배포
- A/B 실험·feature flag 와 결합해 점진 롤아웃 (10 % → 50 % → 100 %)
- 다국어 텍스트·이미지 교체에 새 빌드 불필요

**단점/주의**:
- 네이티브 코드(Swift/Kotlin/C++) 는 OTA 불가 — 새 빌드 + 스토어 심사 필수
- 스토어 정책 위반 시 앱 게재 중단 위험 (Apple 4.7 위반 사례 다수)
- patch 와 native 의 mismatch 가 crash 의 무거운 원인 — runtime version 엄격 관리

**활용 예시**: Expo EAS Update, Shorebird, Microsoft Hot Reload(개발 전용 — OTA 아님), Firebase Remote Config(설정만)

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin (Shorebird Flutter init) 예제**:
```dart
// pubspec.yaml: shorebird_code_push: ^1.x
import 'package:shorebird_code_push/shorebird_code_push.dart';

final updater = ShorebirdUpdater();

Future<void> checkForUpdate() async {
  final status = await updater.checkForUpdate();
  if (status == UpdateStatus.outdated) {
    try {
      await updater.update();          // 다운로드 + 검증
      // 다음 cold start 부터 새 patch 적용
    } on UpdateException catch (e) {
      log('shorebird update failed: $e');
    }
  }
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  checkForUpdate();                    // 비동기, 첫 프레임 차단 금지
  runApp(const MyApp());
}
```

**관련 패턴**: App Signing (OTA 채널 인증 필요), App Lifecycle (cold start 시점에 patch swap), Crash & ANR (rollback trigger)

---

## 10. App Signing & Distribution (앱 서명·배포)

<a id="app-signing"></a>

**목적**: 앱 binary 의 무결성·소유자·업그레이드 경로를 암호학적으로 보장하고, 스토어·내부 테스터·B2B 채널로 안전하게 배포합니다.

**핵심 메커니즘**:
- **Apple Distribution Cert + Provisioning Profile**: Distribution Certificate (.p12, 팀당) + App ID + Devices/Capabilities → `.mobileprovision`. App Store / Ad Hoc / Enterprise / Development 4 종류
- **Apple App Store Connect**: TestFlight (Internal ≤100, External ≤10,000 계정), Phased Release (7-day rollout), Approval queue
- **App Signing by Google Play**: 업로드 키(개발자 보관) + 앱 서명 키(Play 가 관리·재서명). 분실해도 Play Console 에서 reset 가능 (Play App Signing 가입 시)
- **Android Closed Testing → Open Testing → Production**: 20 명 이상 internal tester 14 일 누적 트래픽 필요(2023+ 신규 개인 개발자)
- **Internal App Sharing (Android)**: URL 한 줄로 즉시 설치 가능, 테스트 트랙 우회
- **Enterprise Distribution**: Apple Developer Enterprise Program (사내 직원 한정), Android private app via Play Console
- **App Bundle (.aab) 강제**: Google Play 는 2021-08 부터 신규 앱 aab 필수. APK 는 split-by-device-config 자동
- **Build Number / Version Code**: 단조 증가 필수. 한 번 올라간 번호는 재사용 불가

**장점**:
- 서명 검증으로 사용자가 변조된 앱 설치 방지
- Phased rollout 으로 회귀 발견 시 트래픽 차단
- Internal tester 채널로 빠른 QA 사이클

**단점/주의**:
- 업로드 키 분실 시 Play App Signing 미가입 상태에서는 앱 ID 변경 강제 (사실상 신규 앱 — 사용자 마이그레이션 사고)
- Apple Distribution Cert 만료 → 기존 사용자에게 영향 없음, 그러나 새 빌드 업로드 불가
- iOS Enterprise Cert 남용 (외부 사용자 배포) → Apple 이 인증서 일괄 revoke → 사용자 앱 전부 미실행 사고 (2019 Facebook·Google 사례)

**활용 예시**: `fastlane match`, Xcode Cloud, Gradle Play Publisher, App Store Connect API, Google Play Publishing API

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin (Android signingConfig + Play Publishing) 예제**:
```kotlin
// app/build.gradle.kts
android {
    signingConfigs {
        create("release") {
            // CI 환경변수에서 로드 — keystore 는 git 에 두지 않음
            storeFile = file(System.getenv("UPLOAD_KEYSTORE_PATH") ?: "upload.jks")
            storePassword = System.getenv("UPLOAD_KEYSTORE_PWD")
            keyAlias = System.getenv("UPLOAD_KEY_ALIAS")
            keyPassword = System.getenv("UPLOAD_KEY_PWD")
            enableV1Signing = false   // JAR signing 비활성
            enableV2Signing = true    // APK signing scheme v2
            enableV3Signing = true    // v3 (key rotation)
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = true
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
// CI: ./gradlew bundleRelease → .aab → Play Publishing API upload to "internal" track
```

**관련 패턴**: Deep Link (App Link 검증에 cert fingerprint), OTA Update, `security-mobile.md` (anti-tampering)

---

## 11. App Size 최적화 (앱 용량 최적화)

<a id="app-size"></a>

**목적**: download / install size 를 줄여서 셀룰러 데이터 환경에서의 설치 포기율을 낮추고, 저장공간·OS 캐시 압박을 줄입니다.

**핵심 메커니즘**:
- **Android App Bundle (.aab) + Dynamic Delivery**: 사용자 기기에 맞는 ABI · density · language 만 split APK 로 전달. 평균 20~50 % 감소
- **R8 / ProGuard**: dead code 제거, identifier shrinking, inline. Kotlin stdlib·코루틴은 keep rule 주의
- **iOS App Thinning**: bitcode (Xcode 14 부터 deprecated) / on-demand resources / app slicing — 기기별 binary slice
- **Tree Shaking**: Flutter / React Native 의 미사용 코드·assets 제거. `flutter build apk --tree-shake-icons` (Material Icons 만 사용분 포함)
- **Dynamic Feature Module (Android)**: 일부 화면(스캐너·고가용 기능) 을 install-time 이 아닌 on-demand 다운로드
- **Asset Catalog (iOS) / Vector Drawable (Android)**: PNG 다해상도 대신 single asset. SVG → VectorDrawable 변환
- **WebP / AVIF**: PNG/JPEG 대비 20~50 % 절감 (Android 4.0+ / iOS 14+)
- **Font subsetting**: 한글·CJK 폰트는 수십 MB — 사용 글리프만 추출
- **Native lib 분할**: `arm64-v8a` only (32-bit 미지원 결정 시) → 절반 감소

**장점**:
- Play 통계 "100 MB 미만" 앱은 셀룰러 자동 설치 (구 25/100/150 MB 임계는 폐지·완화됨)
- 첫 설치 / 업데이트 다운로드 시간 단축
- OS 가 저장공간 부족 시 우선 삭제 대상에서 제외될 가능성 증가

**단점/주의**:
- R8 over-shrinking → reflection 기반 코드(Gson / Moshi 의 일부) crash. keep rule 누락 사고 빈번
- Dynamic Feature 의 다운로드 실패 처리·UX 추가 작업 필요
- Bitcode deprecate 이후 iOS thinning 효과 축소 — universal binary 가 default

**활용 예시**: Android Studio APK Analyzer, Bundletool, `flutter build apk --analyze-size`, Emerge Tools / DexGuard

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Kotlin (R8 keep rules + bundletool 검증) 예제**:
```
# proguard-rules.pro
# Moshi reflection — 모델 클래스 보존
-keepclasseswithmembers class * {
    @com.squareup.moshi.JsonClass <fields>;
}
-keep @com.squareup.moshi.JsonClass class *

# Crashlytics 가 line number 로 stack 매핑 → 보존 필수
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Kotlin metadata 일부 보존 (reflection 사용 라이브러리)
-keep class kotlin.Metadata { *; }

# 검증: 빌드 산출물의 device-specific split 확인
# $ bundletool build-apks --bundle=app-release.aab --output=out.apks \
#       --device-spec=device.json
# $ bundletool extract-apks --apks=out.apks --output-dir=extracted \
#       --device-spec=device.json
# → install size 확인
```

**관련 패턴**: App Startup (작은 binary → 빠른 시작), OTA Update (assets 만 OTA 로 빠짐), App Signing (split APK 도 서명 필요)

---

## 12. Permission Request UX (권한 요청 UX)

<a id="permission-ux"></a>

**목적**: 위치·카메라·알림 등 민감 권한을 요청할 때, 사용자가 거부하면 복구가 어려운 OS 다이얼로그를 함부로 띄우지 않고, 사용 맥락이 명확한 순간에 사전 설명을 거쳐 정중하게 요청합니다.

**핵심 메커니즘**:
- **Just-in-time Request**: 앱 진입 즉시가 아니라 **해당 기능을 사용하려는 순간** 요청. 예) 카메라 권한은 QR 스캔 화면 진입 시
- **Pre-permission Rationale**: OS 다이얼로그 전에 in-app 설명 화면 → "허용하기" 탭 시에만 OS 다이얼로그 표시. 거부율 50% 이상 감소 사례
- **Android `shouldShowRequestPermissionRationale()`**: true → rationale 표시 후 재요청. false 가 두 번째로 떨어지면 "Don't ask again" 상태 → 설정 앱으로 이동 유도
- **iOS Authorization Status**: `.notDetermined` (요청 가능) / `.denied` (재요청 불가, 설정으로) / `.restricted` (페어런털 컨트롤) / `.authorized` / `.limited` (사진 일부만, iOS 14+)
- **Android 13+ Notification Permission**: `POST_NOTIFICATIONS` 가 runtime permission 으로 승격. iOS 와 동일하게 거부 가능
- **One-time / Approximate Location**: iOS 14+ precise / approximate 분리, Android 12+ COARSE / FINE 사용자 선택 UI
- **App Tracking Transparency (iOS 14.5+)**: IDFA 사용 시 별도 다이얼로그. 거부 시 IDFA 0 으로 fallback

**장점**:
- 거부율 감소 → 핵심 기능 동작률 상승
- "Don't ask again" 사고 회피 → 설정 앱 이동 안내 UX 명확화
- App Store / Play 의 "권한 남용" 리젝트 / Privacy nutrition label 부담 감소

**단점/주의**:
- iOS 의 `.denied` 는 코드로 복구 불가 — 설정 앱 deep link 만 가능 (`UIApplication.openSettingsURLString`)
- Android 11+ 부터 "Don't ask again" 의 자동 동작이 강화 (2번 거부 = denied permanently 와 유사)
- 권한 요청 화면에서 사용자 이탈 시 재진입 시 다시 안내 — 상태 머신 필요

**활용 예시**: `ActivityResultContracts.RequestPermission`, `PHPhotoLibrary.requestAuthorization(for: .readWrite)`, Flutter `permission_handler`, RN `react-native-permissions`

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin (Compose + rationale + 설정 fallback) 예제**:
```kotlin
@Composable
fun CameraGate(onGranted: () -> Unit) {
    val context = LocalContext.current
    var showRationale by remember { mutableStateOf(false) }
    var deniedPermanently by remember { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) onGranted()
        else {
            val activity = context as Activity
            // false → 두 번째 거부 (permanent denied)
            deniedPermanently = !ActivityCompat.shouldShowRequestPermissionRationale(
                activity, Manifest.permission.CAMERA
            )
        }
    }

    when {
        deniedPermanently -> SettingsRedirectDialog(
            onConfirm = {
                context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                    .setData(Uri.fromParts("package", context.packageName, null)))
            }
        )
        showRationale -> RationaleDialog(
            onAllow = { showRationale = false; launcher.launch(Manifest.permission.CAMERA) },
            onDeny = { showRationale = false }
        )
        else -> Button(onClick = { showRationale = true }) {
            Text("QR 스캔 시작")
        }
    }
}
```

**관련 패턴**: Push Notification (Android 13+ POST_NOTIFICATIONS), Navigation (권한 화면 라우팅), App Lifecycle (설정에서 복귀 시 권한 재확인)

---

## 13. Battery & Performance Profiling (배터리·성능 프로파일링)

<a id="battery-profiling"></a>

**목적**: CPU·GPU·네트워크·radio 사용량과 프레임 렌더링 시간을 정량 측정하여, 발열·배터리·jank(끊김) 의 회귀를 PR 단계에서 자동 차단합니다.

**핵심 메커니즘**:
- **iOS Energy Impact (Instruments)**: Energy Log + CPU + Network + Location + Background time. Xcode Organizer 에 실사용자 metric 자동 집계
- **Android Battery Historian / Profile GPU Rendering**: `adb bugreport` → battery-historian. wake lock, alarm, sync, GPS 사용 라인별 시각화
- **Frame Timing**: Android Choreographer + `FrameMetricsAggregator` / Jetpack Macrobenchmark `FrameTimingMetric`, iOS `CADisplayLink` + Instruments `Time Profiler`
- **Jank Metric**: P50 / P90 / P99 frame time. 16.6ms (60 fps) / 8.3ms (120 fps ProMotion) 초과율
- **Doze / App Standby Bucket (Android)**: `adb shell dumpsys battery unplug` + `adb shell dumpsys deviceidle force-idle` 로 시뮬레이션
- **Network 효율**: radio tail (3G 5~10s, LTE 1~2s) — 작은 요청을 묶어 보내야 radio 가 sleep. WorkManager 의 `setRequiresBatteryNotLow` 활용
- **Thermal State**: iOS `ProcessInfo.thermalState`, Android `PowerManager.getCurrentThermalStatus()` — `severe` 이상에서 비필수 작업 throttle
- **Flutter DevTools Performance / Frame chart**: build / layout / paint / raster 단계별 시간. 60 fps 미달 프레임 hot spot 자동 표시

**장점**:
- 사용자 리뷰의 "배터리 빨리 닳음" / "렉 걸림" 보고를 PR 차단으로 사전 방지
- Macrobenchmark 결과를 CI 에 게이트 (성능 회귀 5 % 이상이면 빌드 실패)
- 발열로 인한 OS throttling → 추가 성능 저하의 악순환 차단

**단점/주의**:
- 시뮬레이터·에뮬레이터 성능은 실기기와 무관 — 반드시 실기기 측정
- 64-bit / mid-tier / low-end 3 등급 디바이스 풀 필요 (low-end 가 사용자의 30~50%)
- 측정 자체가 overhead — 프로덕션 빌드에서는 sampling 비율 조절

**활용 예시**: Instruments (Time Profiler / Energy Log), Android Profiler / Macrobenchmark, Perfetto, Firebase Performance, Flutter DevTools

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin (Macrobenchmark + ThermalState 감지) 예제**:
```kotlin
// benchmark 모듈: src/androidTest/.../StartupBenchmark.kt
@RunWith(AndroidJUnit4::class)
class StartupBenchmark {
    @get:Rule val benchmarkRule = MacrobenchmarkRule()

    @Test fun coldStartup() = benchmarkRule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(StartupTimingMetric(), FrameTimingMetric()),
        iterations = 10,
        startupMode = StartupMode.COLD,
    ) {
        pressHome()
        startActivityAndWait()
    }
}

// 런타임 thermal throttling: severe 이상에서 동영상 인코딩 보류
class VideoEncoder(ctx: Context) {
    private val pm = ctx.getSystemService(Context.POWER_SERVICE) as PowerManager
    fun shouldThrottle(): Boolean = when (pm.currentThermalStatus) {
        PowerManager.THERMAL_STATUS_SEVERE,
        PowerManager.THERMAL_STATUS_CRITICAL,
        PowerManager.THERMAL_STATUS_EMERGENCY,
        PowerManager.THERMAL_STATUS_SHUTDOWN -> true
        else -> false
    }
}
```

**관련 패턴**: App Startup (StartupTimingMetric), Background Task (radio tail 최적화), Crash & ANR (jank 누적 → ANR 위험)
