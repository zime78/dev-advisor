# AR/VR/XR 패턴 (Augmented / Virtual / Extended Reality Patterns)

AR(Augmented Reality) / VR(Virtual Reality) / MR(Mixed Reality) / XR(Extended Reality, 통칭) 시스템의 5 핵심 패턴. 일반 모바일/그래픽 앱과 달리 **6DoF 추적·motion-to-photon latency·시각적 멀미(simulator sickness)** 가 1차 품질 지표이며, **OpenXR 1.1 표준**(Khronos, 2024) 과 플랫폼별 SDK(ARKit / ARCore / visionOS) 위에서 구현됩니다.

**적용 영역**: VR 헤드셋(Meta Quest 3, Valve Index, Apple Vision Pro), AR 모바일(iOS ARKit / Android ARCore), MR 헤드셋(HoloLens 2, Vision Pro Passthrough), 자동차 HUD/디지털 트윈, 산업용 원격 협업.

**관련 카탈로그**:
- [graphics-rendering.md](graphics-rendering.md) — Rasterization / Ray Tracing / PBR / Forward vs Deferred (XR 의 렌더 백엔드)
- [game-dev.md](game-dev.md) — Game Loop / ECS / Spatial Partition (XR 도 실시간 16~11 ms 루프 기반)
- [`../algorithms/spatial.md`](../algorithms/spatial.md) — KD-Tree / Octree / BVH (SLAM 의 공간 인덱스)
- [`../algorithms/signal-processing.md`](../algorithms/signal-processing.md) — Kalman / EKF / Complementary Filter (IMU + Camera Sensor Fusion)
- [`../principles/performance-metrics.md`](../principles/performance-metrics.md) — motion-to-photon latency / frame pacing / jitter 지표

**XR 품질 지표** (필수 KPI):
- **Motion-to-Photon Latency (MTP)**: 사용자 머리 움직임 → 디스플레이 반영까지 < 20 ms (멀미 한계, Carmack 2013). Vision Pro 12 ms, Quest 3 ~ 30 ms (Reprojection 후 체감 15 ms).
- **Frame Rate**: 90 Hz (Quest 3 / Index) / 120 Hz (PSVR2) / 90~100 Hz (Vision Pro) — 11.1 ms / 8.3 ms / 10 ms budget.
- **Tracking Jitter**: 정지 시 위치 변동 < 1 mm RMS (Inside-Out 기준).
- **Drift**: SLAM 누적 오차 < 1 % / m (loop closure 후).

---

## 1. 6DoF Tracking (Six Degrees of Freedom)

<a id="xr-6dof-tracking"></a>

**목적**: 사용자 머리/컨트롤러/손의 **위치(x, y, z) 3축 + 회전(yaw, pitch, roll) 3축 = 6 자유도**를 실시간으로 추정하여 가상 카메라를 1:1 동기화합니다. 3DoF(회전만) 는 360 비디오용, 6DoF 가 모든 인터랙티브 XR 표준입니다.

**특징/메커니즘**:
- **Inside-Out Tracking** (현대 표준): 헤드셋 내부 카메라(보통 4~6개) + IMU 가 외부 환경을 SLAM 으로 추적. 외부 센서 불필요. Meta Quest, Vision Pro, HoloLens 2, Pico 4.
- **Outside-In Tracking** (구세대): 외부 라이트하우스/베이스 스테이션이 헤드셋 LED/마커를 추적. Valve Index, HTC Vive (구형), Optitrack 모션캡처. 정밀도 0.1 mm 가능하나 설치·이동성 약점.
- **6DoF Pose**: SE(3) 군 — `R ∈ SO(3) (3x3 회전행렬) + t ∈ R^3 (위치 벡터)`. 쿼터니언 `(w, x, y, z)` 로 표현 (gimbal lock 회피).
- **Predictive Pose**: 디스플레이 발광 시점 예측 — `pose_predicted(t + display_latency)` 로 reprojection 입력. OpenXR `xrLocateViews(predictedDisplayTime)`.
- **Controller / Hand / Eye 별도 6DoF**: 컨트롤러는 IR LED + IMU, 손은 카메라 기반 hand-tracking ML (Quest, Vision Pro 기본), 눈은 적외선 + IR LED (Vision Pro, Quest Pro).

**알고리즘 스택**:
1. IMU 가속도/각속도 200~1000 Hz 샘플링 → 적분으로 단기 pose (drift 빠름)
2. 카메라 30~60 Hz 프레임 → Visual-Inertial Odometry (VIO) 로 IMU 보정
3. SLAM 맵에 정합 → loop closure 로 drift 보정
4. Pose 예측 후 디스플레이로 송신

**측정 (motion-to-photon latency)**:
- 헤드셋 IMU 샘플링 → 렌더 → 디스플레이 발광까지의 end-to-end 지연
- 측정법: 고속 카메라(240 fps 이상) 로 머리 회전 시작 프레임과 디스플레이 반영 프레임 차이 측정
- 목표: < 20 ms (Carmack), 실제 Vision Pro 12 ms / Quest 3 약 30 ms (raw) → Reprojection 으로 체감 15 ms

**장점**:
- 사용자 자유 이동 → 룸스케일 / 자연스러운 인터랙션
- Outside-In 대비 설치 0 단계
- 컨트롤러 없이도 hand tracking 으로 입력 가능

**단점/주의**:
- 어두운 환경 / 반복 패턴 벽에서 VIO 실패 → drift
- 빠른 회전 시 카메라 motion blur 로 feature 추적 손실
- IMU bias drift 누적 → 5 분 후 위치 오차 cm 단위

**플랫폼 차이**:
| 플랫폼 | 추적 방식 | 카메라 | 손 추적 | 눈 추적 |
|---|---|---|---|---|
| Meta Quest 3 | Inside-Out (VIO) | 4 RGB + 2 depth | O (기본) | X |
| Meta Quest Pro | Inside-Out | 5 카메라 | O | O |
| Apple Vision Pro | Inside-Out | 12 카메라 + LiDAR | O (Optic ID) | O (IR LED + 카메라) |
| Valve Index | Outside-In (라이트하우스 2.0) | 외부 베이스 | X | X |
| HoloLens 2 | Inside-Out | 4 환경 + 2 IR | O | O |

**활용 예시**:
- Beat Saber — 컨트롤러 6DoF + 머리 6DoF 동시
- Apple Vision Pro — 눈+손 제스처(`@FocusState` + pinch) 만으로 UI 조작
- Microsoft Mesh — 멀티 사용자 6DoF 동기화 (네트워크 보간 필요)

**난이도**: 높음 | **사용 빈도**: ★★★★★ (모든 XR 앱 필수)

**Swift 예제 (ARKit 6DoF)**:
```swift
import ARKit

class ViewController: UIViewController, ARSessionDelegate {
    let session = ARSession()

    override func viewDidLoad() {
        super.viewDidLoad()
        let config = ARWorldTrackingConfiguration()
        // 6DoF + Plane + Mesh + People Occlusion 모두 활성
        config.planeDetection = [.horizontal, .vertical]
        config.sceneReconstruction = .meshWithClassification
        config.frameSemantics = [.personSegmentationWithDepth]
        session.delegate = self
        session.run(config)
    }

    // 60 Hz 콜백 — pose 갱신
    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        let cam = frame.camera
        // camera.transform 은 4x4 SE(3) — 위치 + 회전 통합
        let position = cam.transform.columns.3   // t ∈ R^3
        // tracking state 검증 — limited 면 SLAM 신뢰 낮음
        switch cam.trackingState {
        case .normal: break
        case .limited(let reason):
            print("Tracking limited: \(reason)")  // .initializing / .relocalizing / .excessiveMotion / .insufficientFeatures
        case .notAvailable: break
        }
    }
}
```

**Kotlin 예제 (ARCore 6DoF)**:
```kotlin
import com.google.ar.core.*

class ArRenderer(private val session: Session) {
    fun onDrawFrame() {
        val frame = session.update()
        val camera = frame.camera
        // 6DoF pose — Translation(x,y,z) + Quaternion(w,x,y,z)
        val pose = camera.pose
        val tx = pose.tx(); val ty = pose.ty(); val tz = pose.tz()
        val qw = pose.qw(); val qx = pose.qx(); val qy = pose.qy(); val qz = pose.qz()

        if (camera.trackingState != TrackingState.TRACKING) {
            // 추적 손실 — UI 에 안내 후 SLAM 복귀 대기
            return
        }

        // 디스플레이 발광 시점 pose 예측
        val viewMatrix = FloatArray(16)
        camera.getViewMatrix(viewMatrix, 0)
        val projMatrix = FloatArray(16)
        camera.getProjectionMatrix(projMatrix, 0, /*near*/0.1f, /*far*/100f)
        // ... 렌더링
    }
}
```

**표준 인용**:
- OpenXR 1.1 spec §6 (Pose / Space / Reference Space `XR_REFERENCE_SPACE_TYPE_STAGE` / `_LOCAL_FLOOR`)
- Apple ARKit: `ARCamera.transform` (simd_float4x4), `ARWorldTrackingConfiguration`
- Google ARCore: `Camera.getPose()`, `TrackingState.TRACKING`
- Khronos OpenXR: `xrLocateViews` / `xrLocateSpace`

**관련 패턴**: [SLAM](#xr-slam), [Reprojection](#xr-reprojection-atw-asw)

---

## 2. SLAM (Simultaneous Localization and Mapping)

<a id="xr-slam"></a>

**목적**: 알 수 없는 환경에서 **자기 위치를 추정하면서 동시에 맵을 구성**합니다. XR 의 Inside-Out 6DoF 의 핵심 엔진이며, 자율주행/로봇/드론과 공통 알고리즘입니다.

**특징/메커니즘**:
- **Visual SLAM**: RGB / 스테레오 / RGB-D 카메라 기반. ORB-SLAM3 (현재 OSS 표준), VINS-Mono (IMU 결합 monocular), Kimera (semantic), Maplab.
- **LiDAR SLAM**: LOAM, LIO-SAM — 자동차/Vision Pro 의 LiDAR 보조.
- **Sensor Fusion**: IMU (200~1000 Hz, 단기 정확 / 장기 drift) + Camera (30~60 Hz, 장기 안정 / 단기 motion blur) + Depth → Extended Kalman Filter (EKF) 또는 Factor Graph (iSAM2, GTSAM) 로 융합.
- **Front-end / Back-end 분리**:
  - Front-end: feature 추출(ORB, SuperPoint) → matching → pose 추정 (PnP, RANSAC)
  - Back-end: Bundle Adjustment (BA) 로 keyframe + landmark 동시 최적화 (Levenberg-Marquardt, Ceres / g2o)
- **Loop Closure**: 같은 장소 재방문 감지 (DBoW2 bag-of-words, NetVLAD) → 누적 drift 보정
- **Relocalization**: 추적 손실 후 기존 맵에서 현재 pose 재찾기

**알고리즘 분류**:
| 방식 | 대표 | 특징 |
|---|---|---|
| Feature-based | ORB-SLAM3 | ORB feature, sparse 맵, loop closure 강함 |
| Direct | DSO, LSD-SLAM | 픽셀 밝기 직접 최적화, low-texture 강함 |
| Tightly-coupled VIO | VINS-Mono, OKVIS | IMU + Camera factor graph 통합 |
| Learning-based | DROID-SLAM, NICE-SLAM | 딥러닝 feature / depth, 실시간성 약함 |

**측정 (motion-to-photon latency 기여분)**:
- VIO 처리 시간: 5~10 ms / frame (Quest 3 SoC 기준)
- Loop closure 발생 시 BA 가 100~500 ms — 백그라운드 스레드에서 비차단 실행 필수
- 추적 실패 → 재초기화까지 1~5 초 (사용자에게 "주변을 둘러보세요" 안내 필요)

**장점**:
- 외부 인프라 없이 임의 환경에서 동작
- 카메라 + IMU 만으로 cm 단위 정확도
- 다중 세션 맵 저장/공유 가능 (ARKit `ARWorldMap`, ARCore Cloud Anchor)

**단점/주의**:
- Dynamic object (사람/차) 가 많으면 정적 가정 위배 → drift
- Low-texture (흰 벽), 반복 패턴 (체스보드 바닥) 에서 ambiguity
- 메모리 — 큰 공간 매핑 시 keyframe 수백 개, GB 단위
- 프라이버시 — 환경 카메라 데이터는 PII 가능성, 단말 내 처리 + 명시 동의 필요 (Apple Vision Pro 는 raw 카메라 외부 송신 금지)

**플랫폼 차이**:
| 플랫폼 | SLAM 엔진 | 입력 | 맵 공유 |
|---|---|---|---|
| ARKit | Apple 자체 (closed) + LiDAR | RGB + IMU + LiDAR (Pro) | `ARWorldMap`, Shared AR |
| ARCore | Google 자체 (closed) | RGB + IMU + Depth API | Cloud Anchors |
| visionOS | Apple 자체 + LiDAR + 12 카메라 | 광각 RGB + IR + LiDAR | iCloud 기반 |
| OpenXR | 벤더 구현체 | 추상화 | `XR_MSFT_spatial_anchor_persistence` |

**활용 예시**:
- IKEA Place — ARKit plane + SLAM 으로 가구 배치
- Pokémon GO — ARCore Geospatial API + VPS (Visual Positioning System)
- Vision Pro — 거실 메시 자동 스캔 후 윈도우 anchor

**난이도**: 매우 높음 | **사용 빈도**: ★★★★★ (모든 XR 의 기반)

**C++ 예제 (ORB-SLAM3 API)**:
```cpp
#include "System.h"

int main(int argc, char** argv) {
    // Stereo-Inertial SLAM 시스템 초기화
    ORB_SLAM3::System SLAM(
        argv[1],                  // vocabulary 파일 (DBoW2)
        argv[2],                  // 카메라 설정 yaml
        ORB_SLAM3::System::IMU_STEREO,
        true                      // viewer 활성
    );

    while (running) {
        cv::Mat imLeft = grabLeft();
        cv::Mat imRight = grabRight();
        std::vector<ORB_SLAM3::IMU::Point> imuMeas = grabIMU();
        double t = grabTimestamp();
        // 추적 + Local BA + Loop Closure 자동 수행
        Sophus::SE3f Tcw = SLAM.TrackStereo(imLeft, imRight, t, imuMeas);
        // Tcw 가 현재 카메라 → 월드 pose (SE(3))
    }

    SLAM.Shutdown();
    SLAM.SaveTrajectoryEuRoC("trajectory.txt");
    return 0;
}
```

**Python 예제 (factor graph - GTSAM)**:
```python
import gtsam
import numpy as np

# Factor graph 기반 VIO back-end
graph = gtsam.NonlinearFactorGraph()
initial = gtsam.Values()

# IMU preintegration — 두 keyframe 사이 IMU 데이터 압축
params = gtsam.PreintegrationParams.MakeSharedU(9.81)
pim = gtsam.PreintegratedImuMeasurements(params, gtsam.imuBias.ConstantBias())

for imu in imu_samples_between_keyframes:
    pim.integrateMeasurement(imu.accel, imu.gyro, imu.dt)

# IMU factor 추가 — pose_i, vel_i, bias_i 와 pose_j, vel_j 연결
graph.add(gtsam.ImuFactor(
    gtsam.symbol('x', i), gtsam.symbol('v', i),
    gtsam.symbol('x', j), gtsam.symbol('v', j),
    gtsam.symbol('b', i),
    pim
))

# Visual factor — landmark 와 keyframe 사이 projection
graph.add(gtsam.GenericProjectionFactorCal3_S2(
    measured_uv, noise, gtsam.symbol('x', i), gtsam.symbol('l', k), K_camera
))

# 최적화 — Levenberg-Marquardt 또는 ISAM2 (incremental)
isam = gtsam.ISAM2()
isam.update(graph, initial)
result = isam.calculateEstimate()
```

**표준 인용**:
- ORB-SLAM3: Campos et al., IEEE T-RO 2021
- VINS-Mono: Qin et al., IEEE T-RO 2018
- OpenVINS, Kimera, GTSAM 4 (Georgia Tech)
- Apple ARKit `ARWorldMap` (WWDC 2018)

**관련 패턴**: [6DoF Tracking](#xr-6dof-tracking), [`../algorithms/signal-processing.md`](../algorithms/signal-processing.md) (Kalman / EKF)

---

## 3. Foveated Rendering (포비티드 렌더링)

<a id="foveated-rendering"></a>

**목적**: 인간 시각의 **중심와(fovea, 시야 중심 2~3°) 만 고해상도**라는 생리적 특성을 이용해 시야 주변부 해상도를 낮춰 GPU 픽셀 처리량을 30~70 % 절감합니다. VR 의 양안 4K~8K 렌더링 비용을 현실적으로 만드는 핵심 최적화.

**특징/메커니즘**:
- **Fixed Foveated Rendering (FFR)**: 화면 중앙은 항상 풀 해상도, 주변부는 1/2 ~ 1/16 해상도. 눈 추적 불필요. Quest 2 / 3, PICO 4 기본.
- **Eye-Tracked Foveated Rendering (ETFR)**: 적외선 카메라로 시선 좌표 추적 → 해당 영역만 풀 해상도. 더 공격적 절감 가능. PSVR2, Vision Pro, Quest Pro, Varjo XR-3.
- **Variable Rate Shading (VRS)**: 픽셀 쉐이딩 비율을 4x4 / 2x2 / 1x1 픽셀 그룹 단위로 가변. DirectX 12 / Vulkan 표준 — Tier 1 (drawcall 단위) / Tier 2 (screen-space 영역).
- **MultiView (Stereo Rendering)**: 양안 뷰를 단일 패스에서 처리 — `gl_ViewID_OVR` (OpenGL/GLES `OVR_multiview2`), VK_KHR_multiview. drawcall 수 50 % 절감.
- **Foveated transport**: 압축 시에도 fovea 영역만 고품질 (Vision Pro M2-R1 무선 스트리밍).

**해상도 분포** (예: Vision Pro):
- Fovea (시선 중심 ±5°): 100 % (~ 23 megapixel/eye)
- Mid-periphery: ~ 50 %
- Far-periphery: ~ 10 %
- 전체 절감: 약 60 % 픽셀 처리량

**측정**:
- GPU frame time 절감: 30~70 % (콘텐츠 의존)
- Eye-tracking latency 가 MTP 에 추가: 5~10 ms — 너무 느리면 시선 이동 시 흐림 인지
- 시선 추적 정확도: < 0.5° (PSVR2 / Vision Pro)
- Pop-in 인지 임계: foveated boundary 가 시야 6° 이상 떨어지면 인지 불가

**장점**:
- GPU/메모리 대역폭 대폭 절감 → 더 높은 베이스 해상도 가능
- 동일 GPU 로 90 Hz / 120 Hz 도달
- 무선 스트리밍(Air Link) 의 비트레이트 절감

**단점/주의**:
- 시선 추적 실패 시 fallback 필요 (정중앙 fovea 또는 풀 해상도)
- 시야 주변부 텍스트는 가독성 손상 (UI 디자인에서 주변부 텍스트 회피)
- 쉐이더에서 픽셀당 일관성 가정하는 효과(SSAO, TAA) 가 변동 해상도와 충돌

**플랫폼 차이**:
| 플랫폼 | 방식 | API | 절감률 |
|---|---|---|---|
| Quest 2/3 | FFR | Vulkan + `VK_QCOM_fragment_density_map` | 30~50 % |
| Quest Pro | ETFR | `XR_FB_foveation_eye_tracked` | 50~70 % |
| Vision Pro | ETFR + 전체 시각 파이프라인 최적화 | Metal 4 + Compositor Services | 60~70 % |
| PSVR2 | ETFR + VRS | PS5 dedicated VRS hardware | 40~50 % |

**활용 예시**:
- Half-Life Alyx (Index, ETFR 후속 패치)
- Vision Pro 모든 1st-party 앱 (Compositor 자동)
- Quest 3 Asgard's Wrath 2 — dynamic FFR

**난이도**: 중간 (플랫폼 API 호출) ~ 높음 (커스텀 셰이더) | **사용 빈도**: ★★★★ (90 Hz+ XR 필수)

**C++ 예제 (OpenXR + Vulkan FFR)**:
```cpp
// XR_FB_foveation_vulkan + XR_FB_foveation_configuration
XrFoveationLevelProfileCreateInfoFB levelProfile = {
    XR_TYPE_FOVEATION_LEVEL_PROFILE_CREATE_INFO_FB,
    nullptr,
    XR_FOVEATION_LEVEL_HIGH_FB,        // OFF / LOW / MEDIUM / HIGH
    0.0f,                              // verticalOffset
    XR_FOVEATION_DYNAMIC_LEVEL_ENABLED_FB
};
XrFoveationProfileCreateInfoFB profileInfo = {
    XR_TYPE_FOVEATION_PROFILE_CREATE_INFO_FB, &levelProfile
};
XrFoveationProfileFB profile;
xrCreateFoveationProfileFB(session, &profileInfo, &profile);

// 스왑체인에 적용
XrSwapchainStateFoveationFB foveationState = {
    XR_TYPE_SWAPCHAIN_STATE_FOVEATION_FB, nullptr, 0, profile
};
xrUpdateSwapchainFB(swapchain, (XrSwapchainStateBaseHeaderFB*)&foveationState);
```

**Swift 예제 (Metal VRS / visionOS 자동)**:
```swift
import CompositorServices

// visionOS 의 Compositor 는 foveation 을 자동 적용
struct ImmersiveSpace: Scene {
    var body: some Scene {
        ImmersiveSpace(id: "world") {
            CompositorLayer(configuration: MyLayerConfig()) { layerRenderer in
                renderLoop(layerRenderer)
            }
        }
    }
}

struct MyLayerConfig: CompositorLayerConfiguration {
    func makeConfiguration(capabilities: LayerRenderer.Capabilities,
                           configuration: inout LayerRenderer.Configuration) {
        configuration.depthFormat = .depth32Float
        configuration.colorFormat = .rgba16Float
        // foveation 은 시스템이 ETFR 로 자동 적용 — opt-out 만 가능
        configuration.isFoveationEnabled = capabilities.supportsFoveation
    }
}
```

**표준 인용**:
- OpenXR Extensions: `XR_FB_foveation`, `XR_FB_foveation_configuration`, `XR_FB_foveation_eye_tracked`, `XR_QCOM_foveation_dynamic`
- Vulkan: `VK_EXT_fragment_density_map`, `VK_KHR_fragment_shading_rate`
- DirectX 12: Variable Rate Shading Tier 1/2
- Apple: Metal 4 `MTLRasterizationRateMap` (visionOS Compositor 자동)
- Patney et al., "Towards Foveated Rendering for Gaze-Tracked Virtual Reality", SIGGRAPH Asia 2016

**관련 패턴**: [Reprojection](#xr-reprojection-atw-asw), [`graphics-rendering.md` Forward vs Deferred]

---

## 4. Reprojection — ATW / ASW / Spacewarp

<a id="xr-reprojection-atw-asw"></a>

**목적**: 렌더링 프레임이 늦거나(GPU 과부하) 머리 회전이 빠를 때 **이미 렌더된 프레임을 최신 head pose 에 맞춰 워핑**하여 motion-to-photon latency 와 frame rate 를 유지합니다. VR 멀미를 방지하는 마지막 방어선.

**특징/메커니즘**:
- **Asynchronous Time Warp (ATW)**: 회전(rotation) 만 보정. 디스플레이 스캔아웃 직전 최신 pose 로 이미지 평면 회전 변환. Oculus 가 2014 도입.
- **Asynchronous Space Warp (ASW)**: 위치(translation) + 회전 모두 보정. 모션 벡터를 사용해 깊이를 고려한 워핑. FPS 가 90→45 로 떨어져도 ASW 가 중간 프레임 생성. ASW 2.0 은 깊이 버퍼 활용.
- **Asynchronous Projection Warp (APW)**: PSVR2 의 ASW 등가.
- **Application Spacewarp (AppSW)**: Quest 의 게임 측 motion vector + depth 전달 → 시스템이 중간 프레임 합성. 36 Hz 렌더로 72 Hz 체감.
- **Reprojection Rate**: Steam VR Motion Smoothing 등가. SteamVR `Async Reprojection` (회전만) / `Motion Smoothing` (모션 보간).

**파이프라인 위치**:
1. 앱이 view * proj 로 렌더 → 스왑체인에 제출 (pose_predicted_at_t0)
2. 디스플레이 스캔아웃 시점 t1 (= t0 + ~10 ms) 가 다가옴
3. Compositor 가 IMU 최신값으로 pose(t1) 재예측
4. 렌더 결과를 pose(t1) - pose(t0) 만큼 reproject 후 출력
5. ATW: 2D homography (회전), ASW: 깊이 인지 mesh warp (위치)

**측정**:
- Reprojection 후 체감 MTP: 12~15 ms (raw 30 ms 였더라도)
- Reprojection rate: 90 Hz 디스플레이에서 앱은 45 Hz 도 가능
- Artifact 인지율: ASW judder, double-image (반투명 오브젝트), motion vector 오차 → 디버그 오버레이로 측정
- Disocclusion 영역 — ASW 가 채울 수 없음 → black tear

**장점**:
- 앱 GPU spike 시에도 latency 일정
- 저사양 PC 에서 고품질 콘텐츠 가능 (Oculus Rift CV1 시대 핵심)
- 멀미 방지 — 머리 회전과 시각 반응 동기 보장

**단점/주의**:
- Reprojection 이 자주 발동하면 시각적 judder / 잔상 (특히 ASW)
- 투명/반사 오브젝트는 모션 벡터 불일치 → ghosting
- 텍스트 / UI 는 disocclusion artifact 가 두드러짐 → world-locked 가 아니라 head-locked 권장
- 앱이 reprojection 에 의존하면 실제 GPU 최적화 게을러짐 — Meta 는 dashboard 에서 "stale frame" 비율을 노출

**플랫폼 차이**:
| 플랫폼 | 회전 보정 | 위치 보정 | 모션 보간 |
|---|---|---|---|
| Meta Quest | ATW | ASW 2.0 (depth) | AppSW (motion vector) |
| SteamVR | Async Reprojection | Motion Smoothing | X |
| PSVR2 | ATW 등가 | ASW 등가 | dedicated HW |
| Vision Pro | 시스템 compositor 자동 | 자동 + foveated | X (제어 불가) |
| OpenXR | `XR_KHR_composition_layer_*` | `XR_FB_space_warp` | `XR_FB_space_warp` |

**활용 예시**:
- Asgard's Wrath 2 — AppSW 로 36 Hz 렌더 → 72 Hz 출력
- Half-Life Alyx — Motion Smoothing 으로 GTX 1060 지원
- Beat Saber — ATW 만 (60 Hz 정도면 충분)

**난이도**: 낮음 (활성화) ~ 높음 (motion vector 생성) | **사용 빈도**: ★★★★ (저사양 / 모바일 VR 필수)

**C++ 예제 (OpenXR AppSW motion vector layer)**:
```cpp
// XR_FB_space_warp 확장 — Quest 의 AppSW
// 앱이 매 프레임 motion vector + depth 추가 텍스처 제출
XrCompositionLayerSpaceWarpInfoFB warpInfo[2];  // 양안
for (int eye = 0; eye < 2; eye++) {
    warpInfo[eye] = {
        XR_TYPE_COMPOSITION_LAYER_SPACE_WARP_INFO_FB,
        nullptr,
        XR_COMPOSITION_LAYER_SPACE_WARP_INFO_FRAME_SKIP_BIT_FB,  // optional
        /*motionVectorSubImage*/ motionVecImage[eye],
        /*appSpaceDeltaPose*/ appPoseDelta,
        /*depthSubImage*/ depthImage[eye],
        /*minDepth*/ 0.0f, /*maxDepth*/ 1.0f,
        /*nearZ*/ 0.1f,    /*farZ*/ 100.0f
    };
}

XrCompositionLayerProjectionView projViews[2];
projViews[0].next = &warpInfo[0];  // chain
projViews[1].next = &warpInfo[1];
// xrEndFrame 으로 제출 — compositor 가 중간 프레임 생성
```

**Unity 예제 (Application SpaceWarp)**:
```csharp
using Unity.XR.Oculus;

public class SpaceWarpToggle : MonoBehaviour {
    void Start() {
        // 36 Hz 앱 렌더 → 72 Hz 디스플레이 (AppSW 가 중간 프레임 보간)
        OVRPlugin.SetSpaceWarp(true);

        // Application 측은 motion vector 와 depth 를 추가 렌더 타겟에 출력 필요
        // URP/SRP 의 Motion Vector pass 활성화 (URP Renderer Feature)
    }
}
```

**표준 인용**:
- OpenXR: `XR_FB_space_warp`, `XR_KHR_composition_layer_depth`
- Oculus: ATW (2014) / ASW (2016) / AppSW (2021)
- John Carmack, "Latency Mitigation Strategies" (2013) — MTP < 20 ms 근거
- van Waveren, "The Asynchronous Time Warp for Virtual Reality" (2016)

**관련 패턴**: [Foveated Rendering](#foveated-rendering), [6DoF Tracking](#xr-6dof-tracking) (predictive pose)

---

## 5. OpenXR / ARKit / ARCore / visionOS — 4 플랫폼 비교

<a id="xr-platforms-openxr-arkit-arcore-visionos"></a>

**목적**: XR 앱은 헤드셋/스마트폰 마다 SDK 가 달라 cross-platform 어려움이 커서, **Khronos OpenXR** 가 단일 추상화를 제공합니다. Apple 은 OpenXR 비채택(visionOS 는 RealityKit) — 그래서 4 스택 비교가 필수입니다.

**특징/메커니즘**:
- **OpenXR 1.1** (Khronos, 2024-04): 헤드셋 추상화 표준 — Meta, Microsoft, Valve, HTC, Pico, Sony, Qualcomm 모두 채택. Apple **미채택**. 핵심 객체: `XrInstance` / `XrSystem` / `XrSession` / `XrSpace` / `XrSwapchain` / `XrAction`.
- **ARKit** (Apple, iOS / iPadOS): RealityKit + ARKit. World Tracking, Plane, Face (TrueDepth), Body, Mesh (LiDAR), People Occlusion, Object Capture (photogrammetry). visionOS 에서는 일부만 사용.
- **ARCore** (Google, Android): Motion Tracking, Plane, Light Estimation, Depth API, Geospatial API (VPS), Cloud Anchors, Augmented Faces, Augmented Images.
- **visionOS** (Apple, Vision Pro): RealityKit + SwiftUI + ARKit (제한). **Immersive Space / Volumetric Window / Shared Space** 의 3 단계. 손 + 눈 인터랙션은 시스템 제공(앱은 시선 위치 raw 미수신, gaze + tap 제스처만 콜백).

**기능 매트릭스**:
| 기능 | OpenXR | ARKit | ARCore | visionOS |
|---|---|---|---|---|
| **6DoF Tracking** | O (`XR_REFERENCE_SPACE_TYPE_STAGE`) | O (`ARWorldTrackingConfiguration`) | O (`Session.update`) | O (자동, 앱은 query) |
| **Plane Detection** | `XR_MSFT_scene_understanding` | `ARPlaneAnchor` | `Plane` | `PlaneAnchor` (ARKit on visionOS) |
| **Hand Tracking** | `XR_EXT_hand_tracking` (26 joint) | iOS 17+ `ARHandTrackingProvider` (Vision Pro) | MediaPipe Hands (별도) | `HandTrackingProvider` (26 joint) |
| **Eye Tracking** | `XR_EXT_eye_gaze_interaction` | (TrueDepth) `ARFaceAnchor.lookAtPoint` | X | 시스템 자동 — `RealityView` focus, raw 좌표 미공개 (프라이버시) |
| **Passthrough MR** | `XR_FB_passthrough`, `XR_HTC_passthrough` | (X — iOS 비헤드셋) | (X) | 기본 (Mixed Immersion Style) |
| **Spatial Anchor** | `XR_MSFT_spatial_anchor` | `ARAnchor`, Shared AR | `Anchor`, Cloud Anchor | `WorldAnchor` |
| **Scene Mesh** | `XR_MSFT_scene_understanding` | `ARMeshAnchor` (LiDAR) | Depth API + reconstruction | `MeshAnchor` |
| **Cloud Anchor / 멀티유저** | (확장 분산) | `MCSession` Shared AR | Cloud Anchors (Geospatial) | iCloud 기반 SharePlay |
| **언어 / 런타임** | C++ / Vulkan / OpenGL | Swift / Objective-C / Metal | Kotlin / Java / Unity / Unreal | Swift / SwiftUI / RealityKit |
| **저작 도구** | Unity / Unreal / 직접 | Reality Composer Pro / Xcode | Sceneform (deprecated) / Unity | Reality Composer Pro / Xcode |

**측정 차이**:
- MTP: visionOS 12 ms (제어 불가, 시스템 보장) / Quest 3 OpenXR ~ 15 ms (Reprojection 후) / ARKit/ARCore (모바일) 50~100 ms (디스플레이 패널 자체 느림)
- Plane detection 정확도: ARKit LiDAR > ARCore Depth > OpenXR (벤더 의존)
- Hand tracking jitter: visionOS < Quest 3 < 모바일

**장점/플랫폼 선택 가이드**:
- **단일 헤드셋 OEM 앱**: 해당 SDK 직접 (OpenXR 확장이 미지원 기능 접근)
- **Quest + Steam VR 크로스**: OpenXR (Unity OpenXR Plugin 또는 native)
- **iOS 모바일 AR**: ARKit + RealityKit
- **Android 모바일 AR**: ARCore + Sceneform / Filament / Unity
- **Apple Vision Pro 전용**: visionOS RealityKit (OpenXR 미지원, ARKit on visionOS 는 별도 API surface)
- **크로스 플랫폼 게임**: Unity XR Interaction Toolkit + OpenXR (visionOS 는 Unity PolySpatial 별도)

**단점/주의**:
- OpenXR 의 확장(extension) 이 벤더별로 다름 → 실질 호환성은 불완전
- visionOS 는 시선 좌표 raw 미공개 — UI 디자인 패러다임 변화 필요 (hover focus 자동)
- ARKit 의 LiDAR 기능은 iPhone Pro / iPad Pro / Vision Pro 만 지원
- ARCore 디바이스 호환성 리스트 확인 필수 (모든 안드로이드 지원 X)

**Swift 예제 (ARKit on visionOS)**:
```swift
import ARKit
import RealityKit

@MainActor
class XRSession {
    let session = ARKitSession()
    let worldTracking = WorldTrackingProvider()
    let handTracking = HandTrackingProvider()
    let planeDetection = PlaneDetectionProvider(alignments: [.horizontal, .vertical])

    func start() async throws {
        // 권한 요청 — Vision Pro 는 한 번에 모두 요청 권장
        try await session.run([worldTracking, handTracking, planeDetection])

        for await update in worldTracking.anchorUpdates {
            // 6DoF device anchor — pose 갱신
            let transform = update.anchor.originFromAnchorTransform
        }
    }

    func handLoop() async {
        for await update in handTracking.anchorUpdates {
            let hand = update.anchor
            guard hand.isTracked else { continue }
            // 26 joint pose
            if let indexTip = hand.handSkeleton?.joint(.indexFingerTip).anchorFromJointTransform {
                // pinch 제스처 등 — 시선 좌표는 시스템이 자동 hover
            }
        }
    }
}
```

**Kotlin 예제 (ARCore)**:
```kotlin
import com.google.ar.core.*
import com.google.ar.core.exceptions.UnavailableException

class ArCoreActivity : AppCompatActivity() {
    private lateinit var session: Session

    override fun onResume() {
        super.onResume()
        if (session == null) {
            try {
                if (ArCoreApk.getInstance().requestInstall(this, true)
                    != ArCoreApk.InstallStatus.INSTALLED) return
                session = Session(this)
                val config = Config(session).apply {
                    planeFindingMode = Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL
                    depthMode = Config.DepthMode.AUTOMATIC
                    geospatialMode = Config.GeospatialMode.ENABLED
                    lightEstimationMode = Config.LightEstimationMode.ENVIRONMENTAL_HDR
                }
                session.configure(config)
            } catch (e: UnavailableException) {
                finish(); return
            }
        }
        session.resume()
    }
}
```

**C++ 예제 (OpenXR action + space)**:
```cpp
// OpenXR Action System — 컨트롤러 입력의 추상화
XrActionSetCreateInfo asInfo = {XR_TYPE_ACTION_SET_CREATE_INFO};
strcpy(asInfo.actionSetName, "gameplay");
strcpy(asInfo.localizedActionSetName, "Gameplay");
XrActionSet gameplaySet;
xrCreateActionSet(instance, &asInfo, &gameplaySet);

XrActionCreateInfo aInfo = {XR_TYPE_ACTION_CREATE_INFO};
strcpy(aInfo.actionName, "trigger");
aInfo.actionType = XR_ACTION_TYPE_FLOAT_INPUT;
XrAction triggerAction;
xrCreateAction(gameplaySet, &aInfo, &triggerAction);

// Interaction profile binding (Khronos simple controller, oculus touch, valve index, ...)
XrPath triggerPath;
xrStringToPath(instance, "/user/hand/right/input/trigger/value", &triggerPath);
XrActionSuggestedBinding bindings[] = {{triggerAction, triggerPath}};
XrInteractionProfileSuggestedBinding sugg = {
    XR_TYPE_INTERACTION_PROFILE_SUGGESTED_BINDING
};
xrStringToPath(instance, "/interaction_profiles/khr/simple_controller", &sugg.interactionProfile);
sugg.suggestedBindings = bindings; sugg.countSuggestedBindings = 1;
xrSuggestInteractionProfileBindings(instance, &sugg);

// 매 프레임 sync
XrActiveActionSet active = {gameplaySet, XR_NULL_PATH};
XrActionsSyncInfo syncInfo = {XR_TYPE_ACTIONS_SYNC_INFO};
syncInfo.activeActionSets = &active; syncInfo.countActiveActionSets = 1;
xrSyncActions(session, &syncInfo);

XrActionStateFloat state = {XR_TYPE_ACTION_STATE_FLOAT};
XrActionStateGetInfo getInfo = {XR_TYPE_ACTION_STATE_GET_INFO, nullptr, triggerAction};
xrGetActionStateFloat(session, &getInfo, &state);
// state.currentState 가 트리거 0.0 ~ 1.0
```

**표준 인용**:
- **OpenXR 1.1 Specification** (Khronos, 2024-04-15): https://registry.khronos.org/OpenXR/specs/1.1/html/xrspec.html
- **Apple ARKit Documentation**: https://developer.apple.com/documentation/arkit
- **Apple visionOS Documentation** (RealityKit + ARKit on visionOS): https://developer.apple.com/visionos/
- **Google ARCore Developer Guide**: https://developers.google.com/ar
- **Unity OpenXR Plugin** + **Unity PolySpatial** (visionOS)

**관련 패턴**: [6DoF Tracking](#xr-6dof-tracking) (모든 플랫폼 공통), [SLAM](#xr-slam) (내부 엔진), [Reprojection](#xr-reprojection-atw-asw) (각 플랫폼 compositor)

---

## XR 패턴 선택 가이드 (요약)

| 상황 | 권장 패턴 / 플랫폼 |
|---|---|
| iOS 단독 AR 앱 (e-commerce, education) | ARKit + RealityKit, [6DoF](#xr-6dof-tracking) + Plane |
| Android 단독 AR 앱 | ARCore + Sceneform/Filament |
| Quest + SteamVR 멀티 헤드셋 게임 | OpenXR (Unity/Unreal), [Foveated](#foveated-rendering) + [Reprojection AppSW](#xr-reprojection-atw-asw) |
| Vision Pro 전용 MR 앱 | visionOS RealityKit, gaze + pinch UI |
| 자율주행 / 로봇 / 디지털 트윈 | OpenVINS / ORB-SLAM3 + [SLAM 알고리즘](#xr-slam) |
| 위치 기반 AR (Pokémon GO 류) | ARCore Geospatial API (VPS) |
| 산업용 원격 협업 (HoloLens) | OpenXR + `XR_MSFT_spatial_anchor_persistence` |

**금기사항**:
- 90 Hz / 11.1 ms budget 초과 → 즉시 [Reprojection](#xr-reprojection-atw-asw) 발동 → 잦으면 멀미 유발 → GPU 프로파일링 + [Foveated](#foveated-rendering) 적용
- 시야 가장자리에 텍스트 / 중요 UI 배치 → 인지 어려움 + Foveated 해상도 저하 영역
- 사용자에게 갑작스러운 가속도 (인공 이동) → vestibular mismatch → 멀미. Teleport / Snap turn / vignette 활용
- VR 에서 카메라 흔들림 (cinema shake) → 절대 금지. 모든 카메라는 사용자 머리에 1:1 종속

---

**문서 끝.**
