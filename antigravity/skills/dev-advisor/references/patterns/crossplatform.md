# 크로스플랫폼 앱 패턴 (Cross-Platform App Patterns)

Flutter / React Native / Kotlin Multiplatform (KMP) / Expo / Capacitor / Tauri / Compose Multiplatform 의 정평 있는 10 공통 패턴. **하나의 코드베이스로 다중 플랫폼** 을 목표하지만 각 프레임워크의 *추상화 레벨*·*native interop 방식*·*UI 렌더링* 이 다름.

**원전·표준 참고**:
- Flutter Documentation — https://docs.flutter.dev
- React Native Documentation — https://reactnative.dev (New Architecture 2024)
- Kotlin Multiplatform — https://kotlinlang.org/docs/multiplatform.html
- Expo Documentation — https://docs.expo.dev
- Capacitor Documentation — https://capacitorjs.com
- Tauri Documentation — https://tauri.app
- Compose Multiplatform — https://www.jetbrains.com/lp/compose-multiplatform/

**비교축**:
- **UI 렌더링**: Native widget (RN) / Skia (Flutter, CMP) / WebView (Capacitor) / Native + Hybrid (Tauri)
- **언어**: Dart (Flutter) / JS+TS (RN, Expo, Capacitor) / Kotlin (KMP, CMP) / Rust (Tauri 백엔드)
- **OTA 가능**: Yes (Expo Updates, CodePush 변형, EAS Update) / No (CMP native)

**관련 카탈로그**:
- [mobile-app.md](mobile-app.md) — 모바일 운영 패턴 (Lifecycle / Push / Deep Link 등 공통)
- [state-management.md](state-management.md) — Flutter / RN 상태 관리 (계열별)
- [`../languages/index.md`](../languages/index.md) — Dart / Kotlin / TypeScript

---

## 1. Flutter State Management (Flutter 상태 관리)

<a id="flutter-state-management"></a>

**목적**: Flutter 의 `Widget`/`Element`/`RenderObject` 3-tree 위에서 *UI ↔ 상태* 의존 그래프를 명시적으로 모델링하여, 무분별한 `setState()` 재빌드를 막고 테스트 가능한 상태 레이어를 분리합니다.

**메커니즘**:
- **InheritedWidget** — Flutter 내장. 부모가 자식 트리에 데이터를 "수직 주입" 하고, `dependOnInheritedWidgetOfExactType()` 로 구독한 위젯만 재빌드. 모든 외부 라이브러리의 기반
- **Provider** — `InheritedWidget` 의 ergonomics 래퍼. `ChangeNotifier`/`ValueNotifier` 와 통합. 공식 권장 (Flutter 팀 endorsement)
- **Riverpod** — Provider 후속작. *컴파일 타임 안전*, `BuildContext` 의존 제거, code generation (`@riverpod`) 으로 boilerplate 감소. v2 부터 `AsyncValue<T>`/`Notifier`/`AsyncNotifier` 3계열
- **Bloc / Cubit** — Stream 기반 단방향 (Event → State). `flutter_bloc` 의 `BlocProvider` + `BlocBuilder`/`BlocListener`. Cubit 은 Bloc 의 경량 버전 (Event 생략)
- **GetX** — Reactive (`.obs`) + 의존성 주입 + 라우팅 + i18n 의 4-in-1. ergonomics 우수하지만 magic 많음
- **Signals (signals.dart)** — Preact-style fine-grained reactivity. 2024+ 신규 흐름

**장점**:
- 위젯 트리 외부에 상태 보관 → 테스트 가능 (Widget Test 없이 unit test)
- 재빌드 범위를 부분 트리로 축소 (불필요 재빌드 방지)
- Hot Reload 친화 (상태 보존 가능)

**단점/주의**:
- `setState()` 직접 사용은 *지역 UI 토글* 에만 한정. 공유 상태에 쓰면 lift-up 지옥
- `BuildContext` 가 dispose 된 뒤 비동기 콜백에서 접근 → `mounted` 가드 필수
- Riverpod 의 `ref.watch` vs `ref.read` 혼동 — `watch` 는 재빌드 구독, `read` 는 1회 조회

**활용 예시**: Provider (소규모 앱, 공식 가이드), Riverpod (테스트·타입 안전 중시), Bloc (이벤트 추적·로깅 필요), GetX (rapid prototyping)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Dart 예제 (Riverpod 2.x)**:
```dart
import 'package:riverpod_annotation/riverpod_annotation.dart';
part 'cart.g.dart';

@riverpod
class Cart extends _$Cart {
  @override
  List<String> build() => [];        // 초기 상태

  void addItem(String id) {
    state = [...state, id];           // 불변 갱신 → 구독자 알림
  }
}

// View
class CartBadge extends ConsumerWidget {
  @override
  Widget build(BuildContext ctx, WidgetRef ref) {
    final count = ref.watch(cartProvider).length;  // 부분 구독
    return Text('$count');                          // 상태 변경 시 이 위젯만 재빌드
  }
}
```

**Dart 예제 (Bloc)**:
```dart
sealed class CartEvent {}
class AddItem extends CartEvent { final String id; AddItem(this.id); }

class CartBloc extends Bloc<CartEvent, List<String>> {
  CartBloc() : super([]) {
    on<AddItem>((event, emit) => emit([...state, event.id]));
  }
}

// View
BlocBuilder<CartBloc, List<String>>(
  builder: (ctx, items) => Text('${items.length}'),
);
```

**관련 패턴**: [state-management.md#single-store](state-management.md), [Flux/Redux](architectural.md#7-flux--redux), Hot Reload / Fast Refresh

---

## 2. Flutter Platform Channel (Flutter 플랫폼 채널)

<a id="flutter-platform-channel"></a>

**목적**: Dart 코드에서 호스트 플랫폼의 네이티브 API (Kotlin/Java on Android, Swift/Objective-C on iOS) 를 호출하기 위한 *비동기 메시지 채널*. Dart ↔ Native 사이를 binary message 로 직렬화 전달합니다.

**메커니즘**:
- **MethodChannel** — RPC 스타일. Dart `invokeMethod('name', args)` → Native `setMethodCallHandler` → 결과 반환. 가장 일반적
- **EventChannel** — 단방향 스트림. Native → Dart 의 연속 이벤트 (센서 값, 위치 업데이트). Dart 측은 `Stream` 으로 구독
- **BasicMessageChannel** — 양방향 비정형 메시지. `StandardMessageCodec` / `JSONMessageCodec` / `StringCodec` / `BinaryCodec`
- **Pigeon** — Flutter 공식 codegen. interface 정의(`.dart` schema) → Dart/Kotlin/Swift 코드 자동 생성. *타입 안전* + boilerplate 제거 (2024+ 권장)
- **FFI (`dart:ffi`)** — C/C++ 네이티브 라이브러리 직접 호출. Platform Channel 보다 빠름 (메시지 직렬화 없음), 단 ABI 호환성 주의

**장점**:
- Flutter 가 제공하지 않는 OS API (Bluetooth, Camera2, HealthKit 등) 접근
- Pigeon 사용 시 컴파일 타임 타입 안전
- Dart UI ↔ Native 경계가 명확

**단점/주의**:
- 메시지 직렬화 비용 — 고빈도 호출 (60fps 센서) 은 EventChannel + 배치 또는 FFI 권장
- Channel 명 충돌 방지 위해 *역 도메인* 네이밍 (`com.example.app/battery`) 관례
- 결과는 항상 `Future<T>` — async/await 강제
- iOS / Android 양쪽 모두 구현해야 출시 가능 (한쪽 누락 시 `MissingPluginException`)

**활용 예시**: 카메라 RAW 캡처, BLE 통신, In-App Purchase, Health 데이터, Widget 통계 collection

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Dart 예제 (MethodChannel)**:
```dart
class BatteryService {
  static const _channel = MethodChannel('com.example.app/battery');

  Future<int> getLevel() async {
    try {
      final int level = await _channel.invokeMethod('getBatteryLevel');
      return level;
    } on PlatformException catch (e) {
      throw Exception('Battery level failed: ${e.message}');
    }
  }
}
```

**Kotlin 예제 (Android 측 핸들러)**:
```kotlin
class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger,
                      "com.example.app/battery")
            .setMethodCallHandler { call, result ->
                if (call.method == "getBatteryLevel") {
                    val bm = getSystemService(BATTERY_SERVICE) as BatteryManager
                    val level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
                    result.success(level)
                } else {
                    result.notImplemented()
                }
            }
    }
}
```

**Dart 예제 (EventChannel — 가속도 센서 스트림)**:
```dart
const _sensorChannel = EventChannel('com.example.app/accelerometer');
final stream = _sensorChannel
    .receiveBroadcastStream()
    .map((event) => List<double>.from(event));   // [x, y, z]
stream.listen((xyz) => print(xyz));
```

**관련 패턴**: [mobile-app.md](mobile-app.md), Hot Reload, [FFI / Native Interop](../languages/index.md)

---

## 3. React Native Bridge → New Architecture (JSI / TurboModules / Fabric)

<a id="rn-bridge-new-arch"></a>

**목적**: React Native 의 JS ↔ Native 통신 구조를 *비동기 직렬화 브릿지* 에서 *동기 C++ JSI 인터페이스* 로 전환하여, 60+fps 인터랙션과 동기 호출(예: 측정·레이아웃)을 가능하게 합니다.

**메커니즘 (Old vs New)**:
- **Old Bridge (≤0.67)** — JSON 직렬화된 메시지를 비동기 큐로 전달. JS ↔ Native 사이 *3-thread* (JS / Shadow / Main). 문제: (1) 직렬화 오버헤드, (2) async-only, (3) 시작 시 모든 native 모듈 eager load
- **JSI (JavaScript Interface)** — C++ 추상 레이어. JS Engine (Hermes / JSC) 에 *직접 메서드 호출* 가능. 동기 호출 가능, 직렬화 없음
- **TurboModules** — JSI 기반 native module. *lazy load* + 타입 안전 (Codegen). `NativeMyModule.spec.ts` → Codegen → Obj-C/Java 인터페이스 자동 생성
- **Fabric Renderer** — 새 UI manager. C++ 으로 작성, Shadow Tree 를 main thread 와 동기 commit 가능. 측정·레이아웃 동기 호출, 우선순위 기반 렌더링
- **Hermes** — 페북 자체 JS engine. AOT bytecode (`.hbc`) → 시작 속도·메모리 우수. RN 0.70+ 기본
- **Codegen** — TS spec → C++/Java/Obj-C 바인딩 자동 생성. New Arch 의 핵심

**장점**:
- 시작 시간 단축 (lazy module load)
- 동기 호출로 list 측정·레이아웃 정밀화 (`MeasureMode`)
- JS ↔ Native 직렬화 오버헤드 제거
- 타입 안전 (Codegen)

**단점/주의**:
- 마이그레이션 비용 — 기존 native module 을 TurboModule spec 으로 재작성 필요
- Codegen 설정 (`codegenConfig` in package.json) + Xcode/Gradle 통합
- 디버깅 도구 (Flipper) 일부 호환성 이슈 — React DevTools 권장
- Old Bridge 와 New Arch 가 한 앱에 공존 (점진 마이그레이션) — 둘 다 검증 필요

**활용 예시**: Reanimated 3 (JSI worklets), Skia (`@shopify/react-native-skia`), FlashList (Fabric), Vision Camera (JSI)

**난이도**: 매우 높음 | **사용 빈도**: ★★★★★ (2024+ 신규 앱은 New Arch 기본)

**TypeScript 예제 (TurboModule spec)**:
```typescript
// NativeCalc.ts — Codegen 입력
import type { TurboModule } from 'react-native';
import { TurboModuleRegistry } from 'react-native';

export interface Spec extends TurboModule {
  add(a: number, b: number): number;            // 동기 호출 (JSI)
  fetchAsync(url: string): Promise<string>;
}

export default TurboModuleRegistry.getEnforcing<Spec>('Calc');
```

**Kotlin 예제 (Codegen 후 구현)**:
```kotlin
class CalcModule(ctx: ReactApplicationContext) : NativeCalcSpec(ctx) {
    override fun add(a: Double, b: Double): Double = a + b   // 동기 반환
    override fun fetchAsync(url: String, promise: Promise) {
        // 비동기 (Promise)
    }
    override fun getName() = NAME
    companion object { const val NAME = "Calc" }
}
```

**TypeScript 예제 (사용 측 — Fabric 호환 컴포넌트)**:
```typescript
import NativeCalc from './NativeCalc';
const result = NativeCalc.add(2, 3);    // 동기 — JSI 직접 호출, 5 반환
```

**관련 패턴**: Hot Reload / Fast Refresh, [mobile-app.md](mobile-app.md), Expo / EAS

---

## 4. Kotlin Multiplatform (KMP) — expect / actual

<a id="kmp-expect-actual"></a>

**목적**: 공통 비즈니스 로직(`commonMain`)을 한 번 작성하고, 플랫폼별 구현(`androidMain` / `iosMain` / `jvmMain` / `jsMain`)을 *선언-구현 페어* (`expect`/`actual`) 로 연결하여 코드 재사용률을 극대화합니다.

**메커니즘**:
- **소스 셋 계층** — `commonMain` → `androidMain`, `iosMain`, `jvmMain`, `jsMain` 등. `commonMain` 만 모든 타겟에 컴파일
- **`expect` 선언** — `commonMain` 에서 "있다고 약속". 구현 없음. 함수·클래스·프로퍼티 모두 가능
- **`actual` 구현** — 각 플랫폼 소스 셋에서 동일 시그니처로 실제 구현 제공. 컴파일러가 페어링 검증
- **Kotlin/Native (iOS)** — LLVM 기반. Obj-C interop (`@ObjCName`, `cinterop`). Swift 와 자동 헤더 생성
- **Coroutines / Ktor / SQLDelight / Compose Multiplatform** — KMP 표준 라이브러리 생태계
- **Hierarchical Source Sets** — `appleMain` (iOS + macOS), `mobileMain` (Android + iOS) 등 중간 노드. 공통 라이브러리 의존성 정의 단순화
- **Compose Multiplatform 차이** — KMP 는 비즈니스 로직 공유, CMP 는 *UI 까지* 공유 (별도 항목 §8)

**장점**:
- 비즈니스 로직·네트워크·DB·도메인 모델 공유 (UI 만 네이티브 유지 가능)
- Android 팀이 iOS 협업 가능 (Kotlin 단일 언어)
- Native 성능 (Kotlin/Native AOT)
- 점진 도입 가능 — 기존 앱에 KMP 라이브러리만 추가 가능

**단점/주의**:
- iOS 측 빌드 셋업 (Xcode + Gradle + cocoapods/SwiftPM) 복잡
- Kotlin/Native GC 가 JVM 대비 다른 성능 특성 — 메모리 프로파일링 필요
- Swift 측에서 Kotlin enum / sealed class 사용 시 `@ObjCName` 또는 SKIE 도움 필요
- iOS 18+ / Xcode 16 호환성 변화 추적 필요 (2024 dynamic linking, K2 compiler)

**활용 예시**: Netflix / Cash App / Philips / VMware — 도메인 모델 + Ktor 네트워크 + SQLDelight 로컬 DB 공유

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제 (commonMain — expect 선언)**:
```kotlin
// shared/src/commonMain/kotlin/Platform.kt
expect class Platform() {
    val name: String
}

expect fun currentTimeMillis(): Long

expect class HttpClient {
    suspend fun get(url: String): String
}
```

**Kotlin 예제 (androidMain — actual 구현)**:
```kotlin
// shared/src/androidMain/kotlin/Platform.android.kt
actual class Platform actual constructor() {
    actual val name: String = "Android ${android.os.Build.VERSION.SDK_INT}"
}

actual fun currentTimeMillis(): Long = System.currentTimeMillis()
```

**Kotlin 예제 (iosMain — actual 구현)**:
```kotlin
// shared/src/iosMain/kotlin/Platform.ios.kt
import platform.UIKit.UIDevice
import platform.Foundation.NSDate
import platform.Foundation.timeIntervalSince1970

actual class Platform actual constructor() {
    actual val name: String =
        UIDevice.currentDevice.systemName() + " " + UIDevice.currentDevice.systemVersion
}

actual fun currentTimeMillis(): Long =
    (NSDate().timeIntervalSince1970 * 1000).toLong()
```

**Kotlin 예제 (commonMain — 비즈니스 로직 사용)**:
```kotlin
class GreetUseCase {
    fun greet(): String {
        val platform = Platform()
        val timestamp = currentTimeMillis()
        return "Hello from $platform at $timestamp!"
    }
}
// → Android·iOS 양쪽에서 동일하게 호출, 내부 구현만 분기
```

**관련 패턴**: Compose Multiplatform, SwiftUI ↔ Compose Interop, [`../languages/index.md`](../languages/index.md)

---

## 5. Expo / EAS (Expo Application Services)

<a id="expo-eas"></a>

**목적**: React Native 의 *빌드·배포·OTA 갱신* 인프라 복잡도를 추상화. Xcode/Android Studio 없이 클라우드에서 빌드·서명·심사·OTA 배포를 수행합니다.

**메커니즘**:
- **Managed Workflow** — `app.json` / `app.config.ts` 만 작성, native 코드 직접 노출 없음. 기본 SDK 가 카메라·푸시·위치 등 핵심 모듈 포함
- **Bare Workflow** — `ios/`·`android/` 폴더 노출. 커스텀 native 모듈 자유롭게 추가
- **Dev Client** — 커스텀 native 코드를 포함한 개발용 클라이언트 (Expo Go 대체). `eas build --profile development`
- **EAS Build** — 클라우드 빌드. macOS 환경(iOS) 무료, Android `apk`/`aab` 동시 생성. 동시 빌드 큐
- **EAS Submit** — App Store Connect / Google Play 자동 업로드
- **EAS Update** — JS bundle / 에셋의 OTA 배포. 네이티브 코드 변경 없는 한 *재심사 없이* 즉시 사용자에게 배포. Channel / Branch / Update group 으로 단계 출시
- **Expo Router** — 파일 기반 라우팅 (Next.js 스타일). `app/(tabs)/home.tsx` 같은 구조
- **EAS Workflows (2024+)** — CI/CD 파이프라인 (PR 빌드, 릴리즈 게이트)

**장점**:
- iOS 빌드를 위해 Mac 불필요 (EAS 클라우드)
- OTA 로 JS 버그 hotfix 가능 (앱 스토어 우회 *비즈니스 로직 한정*)
- `expo-config-plugins` 로 native 설정 (Info.plist / AndroidManifest) 선언형 패치
- React Native 의 New Architecture (Fabric/TurboModule) 기본 지원

**단점/주의**:
- EAS 빌드 큐 대기 시간 (무료 plan 은 길 수 있음)
- OTA 로 native code 변경 불가 — native 변경 시 새 binary 배포 필요
- App Store 정책: OTA 로 "스토어 가이드라인 우회" 금지 (UI 변경은 OK, 결제 로직 우회는 거부)
- Expo SDK 버전 업그레이드는 React Native major bump 와 동반 — breaking change 추적

**활용 예시**: 인디 개발자 (Mac 없이 iOS 배포), 스타트업 (빠른 hotfix), 사내 앱 (EAS Internal Distribution)

**난이도**: 중간 | **사용 빈도**: ★★★★★ (RN 신규 앱 default)

**TypeScript 예제 (`app.config.ts`)**:
```typescript
import { ExpoConfig } from 'expo/config';

const config: ExpoConfig = {
  name: 'MyApp',
  slug: 'myapp',
  version: '1.2.3',
  runtimeVersion: { policy: 'appVersion' },   // OTA 호환성 그룹
  updates: { url: 'https://u.expo.dev/PROJECT_ID' },
  ios: { bundleIdentifier: 'com.example.myapp', supportsTablet: true },
  android: { package: 'com.example.myapp', versionCode: 123 },
  plugins: [
    ['expo-camera', { cameraPermission: '카메라로 QR 스캔' }],
    'expo-router',
  ],
};
export default config;
```

**Bash 예제 (EAS 빌드·OTA 배포)**:
```bash
# 빌드 (preview 프로파일)
eas build --platform ios --profile preview

# Store 제출
eas submit --platform ios --latest

# OTA 배포 (production 채널)
eas update --branch production --message "Fix login crash"

# 채널 → branch 매핑 (단계 출시)
eas channel:edit production --branch v1-stable
```

**관련 패턴**: React Native New Arch, Hot Reload / Fast Refresh, [mobile-app.md](mobile-app.md)

---

## 6. Capacitor (Web → Native Hybrid)

<a id="capacitor"></a>

**목적**: 기존 웹 앱(React / Vue / Angular / Svelte) 을 *최소 변경* 으로 네이티브 모바일 앱·데스크탑 앱으로 wrapping. WebView 위에 Native API 브릿지를 얹어 카메라·푸시·파일시스템 등에 접근합니다.

**메커니즘**:
- **WebView 호스팅** — iOS WKWebView / Android Chrome WebView 가 웹 자산(`dist/`)을 로드. SPA 라우팅 그대로 사용
- **Capacitor Plugins** — JS API → Native 브릿지. 공식 플러그인 (Camera, Geolocation, Filesystem, Preferences, Push Notifications, Local Notifications) + 커뮤니티 플러그인
- **Custom Plugin** — Swift/Kotlin 으로 자체 native 모듈 작성. `@capacitor/cli` 가 스캐폴딩
- **Live Updates** — Ionic Appflow / VoltBuilder 등으로 OTA 웹 자산 갱신
- **Cordova 후속작** — 같은 Ionic 팀, 더 현대적 (TypeScript-first, ES modules, Promise API)
- **Ionic Framework** — Capacitor 위의 UI 키트 (선택사항). Capacitor 자체는 UI 비종속

**장점**:
- 웹 개발자 ergonomics — HTML/CSS/JS 그대로
- 동일 코드베이스가 웹·iOS·Android·Electron 4 타겟 (Capacitor 6+)
- App Store / Play Store 정책 준수 가능 (단, "단순 웹 wrapper" 거절 위험 §단점)
- 점진 도입 — 기존 PWA 에 Capacitor 추가 가능

**단점/주의**:
- 성능 — WebView 는 native UI 보다 느림 (특히 Android 저가 기기). 60fps 인터랙션 어려움
- App Store Guideline 4.2 — "기능 없는 웹 wrapper" 거절. native API 사용·오프라인 동작 등으로 부가가치 증명 필요
- WebView 버전 분산 — Android 는 OEM·WebView 업데이트에 따라 ES2023 미지원 기기 존재
- 메모리 사용량 — Chromium engine 가 ~50MB baseline 소비
- 보안 — `allowFileAccess`, `mixedContentMode` 등 WebView 설정 잘못하면 XSS / RCE 위험

**활용 예시**: 사내용 도구, 콘텐츠 앱 (뉴스·매거진), 기존 SaaS 의 모바일 진출

**난이도**: 낮음 | **사용 빈도**: ★★★☆☆

**TypeScript 예제 (Capacitor Camera 플러그인)**:
```typescript
import { Camera, CameraResultType } from '@capacitor/camera';

async function capturePhoto() {
  const image = await Camera.getPhoto({
    quality: 90,
    allowEditing: false,
    resultType: CameraResultType.Uri,    // file:// URI
  });
  return image.webPath;                  // <img src={webPath} /> 로 표시
}
```

**TypeScript 예제 (커스텀 플러그인 — 웹 측 인터페이스)**:
```typescript
import { registerPlugin } from '@capacitor/core';

interface BatteryPlugin {
  getLevel(): Promise<{ level: number }>;
}
const Battery = registerPlugin<BatteryPlugin>('Battery');

const { level } = await Battery.getLevel();
```

**Kotlin 예제 (커스텀 플러그인 — Android 측 구현)**:
```kotlin
@CapacitorPlugin(name = "Battery")
class BatteryPlugin : Plugin() {
    @PluginMethod
    fun getLevel(call: PluginCall) {
        val bm = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        val ret = JSObject().put("level", level)
        call.resolve(ret)
    }
}
```

**관련 패턴**: Tauri / Electron 비교, [web-rendering.md](web-rendering.md), [mobile-app.md](mobile-app.md)

---

## 7. Tauri vs Electron (Desktop Cross-Platform)

<a id="tauri-vs-electron"></a>

**목적**: 웹 기술(HTML/CSS/JS)로 데스크탑 앱을 만들되, 바이너리 크기·메모리 사용량·보안 모델을 *system WebView 활용* (Tauri) 또는 *Chromium 동봉* (Electron) 으로 다르게 해결합니다.

**메커니즘 비교**:
| 축 | Tauri (1.x → 2.x) | Electron |
|---|---|---|
| WebView | OS 내장 (WKWebView/WebView2/WebKitGTK) | Chromium 동봉 |
| 백엔드 언어 | Rust | Node.js |
| 바이너리 크기 | ~3-10 MB | ~80-150 MB |
| 메모리 | ~50-80 MB | ~150-300 MB |
| IPC | `invoke('cmd', args)` (직렬화) | `ipcMain` / `ipcRenderer` |
| 모바일 지원 | Tauri 2.0+ (iOS/Android) | 없음 |
| 보안 모델 | Allowlist 기반 (capability) | Node integration 끄기 + contextBridge |
| 성숙도 | 신생 (2022 v1, 2024 v2) | 성숙 (2013+, VS Code, Slack, Discord) |

**Tauri 특징**:
- Rust 의 메모리 안전 + 작은 바이너리
- WebView 가 OS 마다 다름 → 렌더링 일관성 부족 (특히 Linux WebKitGTK)
- v2 부터 iOS/Android 도 지원 (Capacitor 경쟁)
- Capability 시스템 — 각 plugin 마다 명시 허용 (보안 default-deny)

**Electron 특징**:
- Chromium 동봉 → 모든 플랫폼 동일 렌더링
- 큰 바이너리·메모리 — 사용자 PC 자원 소비 크다는 비판
- Node.js fs/child_process 직접 사용 가능 (생산성)
- contextBridge / sandbox / `nodeIntegration: false` 안 하면 RCE 위험

**장점**:
- 웹 개발자가 데스크탑 앱 제작 가능 (Win/Mac/Linux 단일 코드)
- HTML/CSS 의 풍부한 디자인 시스템 활용
- 자동 업데이트 (electron-builder, tauri-updater)

**단점/주의**:
- 네이티브 성능 필요 시 부적합 (게임, 영상 편집)
- Tauri Linux 빌드는 WebKitGTK 버전 차이로 깨질 수 있음
- Electron 은 *모든 앱 = Chromium 브라우저 1개* → 메모리 사고 시 1 시스템에 5+ Chromium
- 보안 업데이트 강제 (Electron 은 Chromium CVE 따라 매월)

**활용 예시**: Tauri (1Password 7, Console 앱, 노트 앱), Electron (VS Code, Slack, Discord, Figma Desktop)

**난이도**: 중간 | **사용 빈도**: Tauri ★★★☆☆ / Electron ★★★★★

**Rust 예제 (Tauri 커맨드)**:
```rust
// src-tauri/src/main.rs
#[tauri::command]
async fn read_config(path: String) -> Result<String, String> {
    std::fs::read_to_string(&path).map_err(|e| e.to_string())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![read_config])
        .run(tauri::generate_context!())
        .expect("error running app");
}
```

**TypeScript 예제 (Tauri 프론트엔드 호출)**:
```typescript
import { invoke } from '@tauri-apps/api/core';

const content = await invoke<string>('read_config', { path: '/etc/app.toml' });
console.log(content);
```

**TypeScript 예제 (Electron 프리로드 — 안전 패턴)**:
```typescript
// preload.ts
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  readConfig: (path: string) => ipcRenderer.invoke('read-config', path),
});
// renderer 에서: window.electronAPI.readConfig('/etc/app.toml')
// nodeIntegration: false + contextIsolation: true 필수
```

**관련 패턴**: Capacitor, [`../security/index.md`](../security/index.md), [deployment.md](deployment.md)

---

## 8. Compose Multiplatform (CMP)

<a id="compose-multiplatform"></a>

**목적**: Jetpack Compose (Android UI 툴킷) 의 *선언형 UI 모델* 을 iOS / Desktop / Web 까지 확장하여, KMP 의 비즈니스 로직 공유에 더해 **UI 코드까지 공유**합니다.

**메커니즘**:
- **JetBrains 주도** — Jetpack Compose API 와 동일 (`@Composable`, `Modifier`, `remember`, `LaunchedEffect`)
- **Skia 렌더링** — Android·iOS·Desktop 모두 Skia 백엔드. Flutter 와 동일한 그래픽 엔진
- **Compose for iOS (Stable 2024)** — Kotlin/Native + Skia + UIKit interop. UIViewController 로 감싸 SwiftUI 안에 삽입 가능
- **Compose for Desktop** — JVM + Skiko. macOS·Windows·Linux 데스크탑
- **Compose for Web** — DOM 백엔드 (`html`) 와 Canvas 백엔드 (`wasm`) 2 모드. wasm 은 Skia, html 은 web-native
- **Resources API** — `compose-resources` 로 이미지·폰트·문자열을 모든 타겟에서 공통 로드
- **Material 3 / Material You** — 공통 컴포넌트 라이브러리 제공

**장점**:
- UI 코드까지 공유 → KMP 대비 추가 절감
- Jetpack Compose 경험 그대로 — Android 개발자가 iOS 화면 즉시 작성
- Hot Reload (desktop·web), Live Edit (Android)
- Skia 기반 일관 렌더링 (iOS UIKit 라이브 흉내가 아닌 *진짜 동일 픽셀*)

**단점/주의**:
- iOS native look & feel 100% 재현 어려움 — Cupertino 스타일 컴포넌트 부족
- Compose for iOS 는 2024 stable 이지만 일부 시스템 컴포넌트(텍스트 입력, 스크롤 관성)는 SwiftUI 와 미세 차이
- 바이너리 크기 — Skia + Kotlin/Native 런타임으로 iOS 앱 base size 증가
- Accessibility — iOS VoiceOver 지원이 SwiftUI 대비 미흡 (개선 중)
- Web 백엔드 (wasm) 는 SEO·초기 로딩 시간 불리

**활용 예시**: JetBrains 자체 제품 (Toolbox), 사내 도구, 모바일 ↔ 데스크탑 동시 출시 앱

**난이도**: 중간 | **사용 빈도**: ★★★☆☆ (성장 중)

**Kotlin 예제 (commonMain — 공통 화면)**:
```kotlin
// shared/src/commonMain/kotlin/App.kt
@Composable
fun App() {
    var count by remember { mutableStateOf(0) }
    MaterialTheme {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text("Count: $count", style = MaterialTheme.typography.headlineMedium)
            Button(onClick = { count++ }) { Text("Increment") }
        }
    }
}
```

**Kotlin 예제 (androidApp 진입점)**:
```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { App() }
    }
}
```

**Swift 예제 (iosApp 진입점 — SwiftUI 통합)**:
```swift
import SwiftUI
import shared    // KMP 모듈

struct ContentView: View {
    var body: some View {
        ComposeView()
            .ignoresSafeArea(.keyboard)
    }
}

struct ComposeView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        Main_iosKt.MainViewController()    // CMP 에서 생성
    }
    func updateUIViewController(_ vc: UIViewController, context: Context) {}
}
```

**관련 패턴**: KMP expect/actual, SwiftUI ↔ Compose Interop, Flutter State Management

---

## 9. SwiftUI ↔ Compose Interop

<a id="swiftui-compose-interop"></a>

**목적**: 한 앱 내에서 *SwiftUI 와 Jetpack Compose / Compose Multiplatform* 을 양방향으로 임베드. 기존 native 앱에 KMP/CMP 화면을 점진 도입하거나, KMP 앱에 native 정밀 화면만 별도 작성합니다.

**메커니즘 (양방향)**:

**Compose → iOS (SwiftUI 안에 Compose 임베드)**:
- KMP 모듈에서 `ComposeUIViewController { App() }` 노출
- Swift 측 `UIViewControllerRepresentable` 로 SwiftUI 안에 wrap
- KMP 측 데이터 흐름은 `Flow<T>` / `StateFlow<T>` → Swift 측 `SKIE` 또는 `KMP-NativeCoroutines` 으로 async sequence 변환

**SwiftUI → Compose (Compose 안에 SwiftUI 임베드)**:
- iOS 만 가능. `UIKitView` Composable 로 UIView/UIViewController wrap
- `interactive = true` 면 터치 이벤트 전달, `false` 면 그리기만

**Android 측 Interop**:
- `AndroidView { ... }` Composable 로 기존 View (XML 레이아웃, MapView, WebView, ExoPlayer SurfaceView) 임베드
- Compose → View 데이터는 `update` 람다로 갱신

**Swift 측 KMP 호출**:
- Kotlin sealed class → Obj-C 에서 `__kClass__` prefix 변환 (SKIE 가 enum/sealed 를 swift enum 으로)
- Kotlin suspend → Obj-C completion handler, SKIE 적용 시 Swift async
- Generic 클래스는 Obj-C 비호환 — `@ObjCName` 로 명시 또는 type erasure

**장점**:
- 점진 마이그레이션 — 기존 SwiftUI/UIKit 앱을 한 화면씩 KMP/CMP 로 이전
- 정밀 native 컴포넌트(Apple Pay sheet, Health 통합 UI) 는 SwiftUI 유지
- 팀 역할 분담 — iOS 팀이 native 정밀 화면, Android 팀이 공통 화면

**단점/주의**:
- 데이터 동기화 복잡 — 양 측 viewModel 중복 또는 KMP shared ViewModel 결정 필요
- Lifecycle 차이 — SwiftUI `onAppear/onDisappear` vs Compose `DisposableEffect` 매핑 필요
- 빌드 시간 증가 — Kotlin/Native + Xcode 두 단계 컴파일
- 디버깅 — 한쪽 stack trace 가 다른 쪽 진입 지점에서 끊김

**활용 예시**: 대형 앱의 점진 KMP 도입 (Cash App, Wayfair, Philips), 정밀 BLE/HealthKit 화면만 SwiftUI 유지

**난이도**: 매우 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 예제 (CMP — iOS 진입점 export)**:
```kotlin
// shared/src/iosMain/kotlin/MainViewController.kt
import androidx.compose.ui.window.ComposeUIViewController

fun MainViewController() = ComposeUIViewController {
    App()    // 공통 Composable
}
```

**Swift 예제 (SwiftUI → Compose embed)**:
```swift
struct ProfileScreen: View {
    var body: some View {
        VStack {
            Text("Native SwiftUI Header")        // SwiftUI

            ComposeView()                         // Compose embedded
                .frame(height: 400)

            Button("Native Action") { ... }
        }
    }
}

struct ComposeView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        Main_iosKt.MainViewController()
    }
    func updateUIViewController(_ vc: UIViewController, context: Context) {}
}
```

**Kotlin 예제 (Compose → UIKit embed, iOS 측)**:
```kotlin
@Composable
fun MapScreen() {
    UIKitView(
        factory = {
            MKMapView().apply {
                showsUserLocation = true
            }
        },
        modifier = Modifier.fillMaxSize(),
        update = { mapView -> /* 좌표 갱신 */ },
        interactive = true,    // 터치 이벤트 전달
    )
}
```

**Kotlin 예제 (Compose → Android View embed)**:
```kotlin
@Composable
fun VideoPlayer(uri: String) {
    AndroidView(
        factory = { ctx ->
            PlayerView(ctx).apply {
                player = ExoPlayer.Builder(ctx).build()
            }
        },
        update = { view ->
            (view.player as ExoPlayer).setMediaItem(MediaItem.fromUri(uri))
            view.player?.prepare()
        },
    )
}
```

**관련 패턴**: KMP expect/actual, Compose Multiplatform, Flutter Platform Channel

---

## 10. Hot Reload / Fast Refresh

<a id="hot-reload-fast-refresh"></a>

**목적**: 코드 변경을 *앱 재시작 없이* 실행 중인 앱에 즉시 반영하여, 개발 사이클(저장→확인) 을 초 단위로 단축합니다. 각 프레임워크가 *상태 보존 정책* 과 *바이트코드 교체 메커니즘* 에서 차이.

**메커니즘 (프레임워크별)**:

**Flutter Hot Reload (가장 정교)**:
- Dart VM 의 *increment compilation* + library reload
- 실행 중 isolate 의 method table 을 새 코드로 교체. 객체 상태(field) 와 stack frame 유지
- `main()`·`initState()` 은 재호출 안 함 — 상태 보존
- 한계: enum 추가/`const` 변경/global state 의 초기화 코드는 *Hot Restart* 필요
- 명령: 터미널 `r` (reload) / `R` (restart)

**Flutter Hot Restart**:
- Dart VM 의 모든 isolate 재시작 → main 부터 재실행
- 상태 손실, 그러나 앱 재컴파일·재배포는 없음 (~1-2초)

**React Native Fast Refresh**:
- Metro bundler 가 변경 모듈만 재빌드 → JS engine 에 patch 전송
- React Component 트리의 *지역 boundary* 만 재마운트. `useState` 보존 (단, hook 시그니처 변경 시 리셋)
- *Function component* 상태 보존, *class component* 는 리셋
- "Reload Boundary" 가 오류 발생 시 자동으로 모듈 전체 reload
- React Hooks rules 위반 시 hot reload 깨짐

**Jetpack Compose Live Edit / Live Literals**:
- Live Literals: 리터럴(`"Hello"`, `16.dp`) 만 즉시 갱신 — composable 함수 본문 변경 불필요
- Live Edit (Android Studio Iguana+): composable 함수 본문 변경도 즉시 적용. 단, function signature 변경은 재컴파일 필요
- 한계: state hoisting · class 변경은 즉시 반영 안 됨

**SwiftUI Previews + Hot Reload**:
- `#Preview` 매크로 — Xcode Canvas 가 *부분 트리* 만 격리 렌더링
- Inject (3rd party) — `@_dynamicReplacement` 으로 method 교체 (앱 전체 hot reload)
- Swift 6 / Xcode 16 의 Live Preview 는 actor isolation 검증 포함

**Compose Multiplatform Hot Reload**:
- Desktop: JVM HotSwap + Compose `runComposable`. macOS·Windows·Linux 모두 가능
- iOS: 미지원 (Kotlin/Native AOT 한계). Live Edit 보완 작업 중

**Webpack / Vite HMR (Capacitor, Tauri 프론트엔드)**:
- Vite 의 ESM-based HMR — 변경된 모듈만 invalidate
- React Refresh / Vue HMR 플러그인 통합

**장점**:
- 개발 속도 5-10x — UI tuning 의 즉시 피드백
- 디자인 토큰·layout 조정 시 디자이너 협업 효율
- 상태 보존으로 깊은 화면(5뎁스) 디버깅도 빠름

**단점/주의**:
- *프로덕션 버그 ≠ Hot Reload 후 동작* — 진짜 검증은 cold start 로 확인
- Native code (Kotlin/Swift/C++) 변경은 항상 재빌드 필요
- Global state / DI 초기화 코드 변경은 reload 만으로 부족 — restart 필요
- `const` / `enum` / generic constraint 변경은 reload 실패 빈번 — error 메시지 확인
- Flutter Web 의 Hot Reload 는 모바일 대비 제약 (full restart 필요한 경우 많음)

**활용 예시**: 디자인 시스템 토큰 조정, 다국어 검수, 폼 검증 메시지 변경, A/B 테스트 분기 시각 비교

**난이도**: 낮음 (사용) / 매우 높음 (구현) | **사용 빈도**: ★★★★★

**Dart 예제 (Flutter Hot Reload 친화 패턴)**:
```dart
// 좋음 — 상태가 위젯 외부에 있어 reload 시 보존
class CounterPage extends StatelessWidget {
  final ValueNotifier<int> counter;
  const CounterPage({super.key, required this.counter});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<int>(
      valueListenable: counter,
      builder: (ctx, value, _) => Text('$value'),
    );
  }
}

// 주의 — initState 안에서만 초기화하면 Hot Restart 시 매번 리셋
class _BadCounterState extends State<BadCounter> {
  late int counter;
  @override
  void initState() {
    super.initState();
    counter = loadFromDisk();    // 매 reload 마다 0 으로 갈 위험 없음 (initState 는 reload 안 함)
                                  // 단, Hot Restart 는 호출됨
  }
}
```

**TypeScript 예제 (React Native Fast Refresh 친화 패턴)**:
```typescript
// 좋음 — function component + useState
export default function Counter() {
  const [count, setCount] = useState(0);     // hook 시그니처 안 바꾸면 보존
  return <Button onPress={() => setCount(c => c + 1)} title={`${count}`} />;
}

// 주의 — class component 는 Fast Refresh 시 항상 unmount/remount
export class BadCounter extends React.Component<{}, { count: number }> {
  state = { count: 0 };
  render() { return <Text>{this.state.count}</Text>; }
}

// 주의 — anonymous default export 는 displayName 추적 실패로 boundary 깨질 수 있음
// export default () => <View/>     ❌
// export default function Foo(){...} ✅
```

**Kotlin 예제 (Compose Live Literals 친화)**:
```kotlin
@Composable
fun Hero() {
    // Live Literals — 이 리터럴들은 앱 실행 중 즉시 반영
    Text(
        text = "Welcome",                       // 문자열 즉시 변경 가능
        fontSize = 24.sp,                       // 숫자 즉시 변경 가능
        modifier = Modifier.padding(16.dp),     // dp 값 즉시 변경 가능
    )
}

// Live Edit (Iguana+) — 함수 본문 변경도 즉시 적용
@Composable
fun NewlyEditedScreen() {
    Column { Text("Edit this and watch it update") }
}
```

**관련 패턴**: Flutter State Management, React Native New Arch, Compose Multiplatform, Expo / EAS (Fast Refresh + EAS Update OTA)

---

## 정리표 (10 항목 한눈에)

| # | 패턴 | 프레임워크 | 추상화 레벨 | 적용 시점 |
|---|---|---|---|---|
| 1 | Flutter State Management | Flutter | UI ↔ State 결합 | 모든 Flutter 앱 |
| 2 | Flutter Platform Channel | Flutter | Dart ↔ Native bridge | Flutter 가 미제공 API 필요 시 |
| 3 | RN Bridge → New Arch | React Native | JS ↔ Native runtime | 신규 RN 앱 (default) |
| 4 | KMP expect/actual | KMP | 소스 셋 분기 | 로직 공유, UI 는 native |
| 5 | Expo / EAS | RN + Expo | 빌드·OTA 인프라 | Mac 없이 iOS 배포, hotfix |
| 6 | Capacitor | Web → Native | WebView wrapper | 웹 앱의 모바일 진출 |
| 7 | Tauri vs Electron | Desktop | WebView vs Chromium | 데스크탑 앱 (크기·메모리 결정) |
| 8 | Compose Multiplatform | KMP + Compose | UI 까지 공유 | 모든 타겟 동일 UI |
| 9 | SwiftUI ↔ Compose Interop | KMP/CMP + iOS | 양방향 embed | 점진 마이그레이션 |
| 10 | Hot Reload / Fast Refresh | 전 프레임워크 | 개발 사이클 | 모든 개발 단계 |

**선택 가이드**:
- *비즈니스 로직만 공유 + 각 플랫폼 native UI* → **KMP** (§4)
- *완전한 단일 UI 코드베이스 + Skia 렌더링* → **Flutter** (§1, §2) 또는 **CMP** (§8)
- *기존 React 팀 + 모바일 진출* → **React Native + Expo** (§3, §5)
- *기존 웹 앱 wrapping* → **Capacitor** (§6)
- *데스크탑 단독* → **Tauri** (작은 크기 우선) 또는 **Electron** (성숙도 우선) (§7)
- *점진 마이그레이션* → **SwiftUI ↔ Compose Interop** (§9)
- *모든 경우* → **Hot Reload / Fast Refresh** 환경 구축 (§10)
