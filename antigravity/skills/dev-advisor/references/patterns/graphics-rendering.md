# 그래픽스 렌더링 패턴 (Graphics Rendering Patterns)

실시간 3D 그래픽스의 표준 파이프라인·가시성 결정·라이팅 모델·렌더링 전략 5 항목. *Real-Time Rendering* (Akenine-Möller, 4th ed., 2018) / *Physically Based Rendering* (Pharr, Jakob, Humphreys, 4th ed., 2023) / Vulkan 1.3 spec / Direct3D 12 spec / Metal 3 Shading Language Specification 표준에 기반합니다.

**적용 영역**: 게임 엔진 (Unreal Engine 5 / Unity HDRP / Godot 4 / Bevy), 영화 VFX (Pixar RenderMan / Arnold), CAD/CAM, 의료 영상 렌더링, AR/VR (OpenXR), 자율주행 시뮬레이션 (CARLA).

**관련 카탈로그**:
- [game-dev.md](game-dev.md) — Game Loop / Scene Graph / Component-Based 등 게임 엔진 일반 패턴
- [`../algorithms/spatial.md`](../algorithms/spatial.md) — BVH / Octree / k-d Tree / R-tree (공간 분할)
- [`../algorithms/geometry.md`](../algorithms/geometry.md) — Convex Hull / Line-Plane intersection / Bézier (기하 알고리즘)
- [`../algorithms/image-processing.md`](../algorithms/image-processing.md) — 필터링 / 색 공간 변환 (post-processing 기반)
- [`../languages/glsl.md`](../languages/glsl.md) — OpenGL / Vulkan GLSL 셰이더
- [`../languages/hlsl.md`](../languages/hlsl.md) — Direct3D HLSL / DXIL 셰이더
- [`../languages/cuda-c-cplusplus.md`](../languages/cuda-c-cplusplus.md) — GPGPU / ray tracing kernel
- [concurrency.md](concurrency.md) — Compute shader 의 SIMT / Work group 모델

---

<a id="rasterization-pipeline"></a>

## 1. Rasterization Pipeline (래스터화 파이프라인)

**목적**: 3D 정점(vertex)을 2D 픽셀(fragment)로 투영·이산화하여 화면에 그리는 GPU 표준 파이프라인. 1990 년대 후반(OpenGL 1.1 / Direct3D 7) 이후 모든 실시간 그래픽스의 근간입니다.

**특징/메커니즘**:
- **고정 단계** (Direct3D 12 / Vulkan 1.3 기준 8 단계):
  1. **Input Assembler (IA)** — 정점 버퍼 + 인덱스 버퍼 조립 (`VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST`)
  2. **Vertex Shader (VS)** — 정점 변환 (object → world → view → clip space). `gl_Position = MVP * inPos`
  3. **Tessellation** (선택) — Hull(Control) Shader → Tessellator → Domain(Evaluation) Shader. 동적 LOD / 지형(terrain).
  4. **Geometry Shader (GS)** (선택) — primitive 단위 입출력 (1→N 확장 가능). 모바일 GPU 에서는 성능 페널티 큼 — Mesh Shader (DX12 Ultimate / Vulkan VK_EXT_mesh_shader) 로 대체 권장.
  5. **Rasterizer (RS)** — primitive → fragment 변환 (스캔라인 알고리즘 + 보간). Viewport / Scissor / Cull / Polygon mode.
  6. **Fragment Shader (FS)** (= Pixel Shader, PS) — 픽셀당 색·법선·머터리얼 계산. `out vec4 fragColor`
  7. **Output Merger (OM)** — Depth/Stencil test → Blend → Render target 출력.
- **좌표계**: Right-handed (OpenGL) vs Left-handed (Direct3D) — Vulkan 은 Y-down NDC (`[-1,1]` X, `[-1,1]` Y inverted, `[0,1]` Z) 로 OpenGL 과 다름.
- **MVP 행렬**: `M` (Model) · `V` (View) · `P` (Projection). Projection 은 `glm::perspective(fov, aspect, near, far)` 로 frustum 정의.
- **시간 복잡도**: 정점 N 개, 픽셀 P 개일 때 `O(N + P · fragmentCost)`. 픽셀 셰이더 비용이 지배적 (overdraw 가 핵심 최적화 포인트).

**장점**:
- 하드웨어 가속 — GPU 가 SIMT (Single Instruction Multiple Threads) 로 fragment 수천 개 병렬 처리
- 결정론적 프레임 시간 — 60 FPS / 120 FPS 보장 용이
- 광범위한 도구 생태계 (RenderDoc / PIX / Nsight Graphics)

**단점/주의**:
- 정확한 전역 조명 (global illumination) / 반사 / 굴절 표현 어려움 — Ray Tracing 또는 Hybrid 필요
- **Overdraw**: 같은 픽셀을 여러 번 그리면 fragment shader 비용 누적 — Z-prepass / Early-Z (§3) 로 완화
- 모바일 GPU 는 **TBDR (Tile-Based Deferred Rendering)** — PowerVR / Apple GPU / Mali. Tile 단위로 정점 binning 후 fragment 처리하므로 transparent / framebuffer-fetch 워크플로우 다름.

**활용 예시** (Vulkan 1.3 / GLSL 450 — 최소 그래픽스 파이프라인):

```cpp
// Vulkan 1.3 — VkGraphicsPipelineCreateInfo 핵심 단계 (C++)
VkPipelineShaderStageCreateInfo stages[] = {
    { .stage = VK_SHADER_STAGE_VERTEX_BIT,   .module = vsModule, .pName = "main" },
    { .stage = VK_SHADER_STAGE_FRAGMENT_BIT, .module = fsModule, .pName = "main" },
};
VkPipelineVertexInputStateCreateInfo viState = { /* binding/attribute */ };
VkPipelineInputAssemblyStateCreateInfo iaState = {
    .topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
};
VkPipelineRasterizationStateCreateInfo rsState = {
    .polygonMode = VK_POLYGON_MODE_FILL,
    .cullMode    = VK_CULL_MODE_BACK_BIT,
    .frontFace   = VK_FRONT_FACE_COUNTER_CLOCKWISE,
};
VkPipelineDepthStencilStateCreateInfo dsState = {
    .depthTestEnable = VK_TRUE, .depthWriteEnable = VK_TRUE,
    .depthCompareOp  = VK_COMPARE_OP_LESS, // Reverse-Z 이면 GREATER
};
VkGraphicsPipelineCreateInfo gp = { /* stages + states + renderPass */ };
vkCreateGraphicsPipelines(dev, VK_NULL_HANDLE, 1, &gp, nullptr, &pipeline);
```

```glsl
// vertex.vert — GLSL 450, MVP 변환
#version 450
layout(location = 0) in vec3 inPos;
layout(location = 1) in vec3 inNormal;
layout(set = 0, binding = 0) uniform UBO { mat4 model, view, proj; } ubo;
layout(location = 0) out vec3 vNormal;
void main() {
    gl_Position = ubo.proj * ubo.view * ubo.model * vec4(inPos, 1.0);
    // 법선은 inverse-transpose(model) 로 변환 (non-uniform scale 대응)
    vNormal = mat3(transpose(inverse(ubo.model))) * inNormal;
}
```

```hlsl
// pixel.hlsl — Direct3D 12 / HLSL Shader Model 6.6, 간단한 Lambert
struct PSInput { float4 pos : SV_POSITION; float3 nrm : NORMAL; };
float4 PSMain(PSInput i) : SV_TARGET {
    float3 L = normalize(float3(0.5, 1.0, 0.3));
    float  diffuse = saturate(dot(normalize(i.nrm), L));
    return float4(diffuse.xxx, 1.0);
}
```

**표준 인용**:
- Akenine-Möller et al., *Real-Time Rendering*, 4th ed., CRC Press, 2018 — Ch. 2 (The Graphics Rendering Pipeline)
- Vulkan 1.3 Specification §27 (Rasterization), §28 (Fragment Operations)
- Microsoft, *Direct3D 12 Programming Guide — Graphics Pipeline*
- SIGGRAPH 1995, *Fast Rasterization with Concurrent Z-buffering* (Pineda triangle setup 기반)

---

<a id="ray-tracing-bvh-pathtracing"></a>

## 2. Ray Tracing — BVH / Path Tracing (광선 추적과 가속 구조)

**목적**: 카메라에서 픽셀마다 광선(ray)을 쏘아 장면과 교차(intersection)를 계산하고, 그 결과로 색을 결정. 반사·굴절·소프트 섀도우·전역 조명을 물리적으로 정확하게 표현. Whitted 1980 / Kajiya 1986 (rendering equation) 이론에 기반합니다.

**특징/메커니즘**:
- **광선 종류**:
  - **Primary ray** — 카메라 → 픽셀 → 장면 (가시성)
  - **Shadow ray** — 교차점 → 광원 (occlusion test)
  - **Reflection / Refraction ray** — Whitted recursive (거울 / 유리)
  - **Path / GI ray** — Kajiya rendering equation: `L_o = L_e + ∫ f_r · L_i · cos θ dω` 의 Monte Carlo 적분
- **BVH (Bounding Volume Hierarchy)**: 삼각형 N 개를 AABB (Axis-Aligned Bounding Box) 트리로 묶어 광선-장면 교차를 `O(log N)` 으로 가속. SAH (Surface Area Heuristic) 빌드가 표준.
- **k-d Tree / Octree**: BVH 대안. 정적 장면에 유리하나 빌드 비용 큼 — 현대 실시간 RT 는 BVH 가 사실상 표준.
- **시간 복잡도**: 광선 R 개, 삼각형 N 개일 때 BVH 빌드 `O(N log N)`, 광선당 trace `O(log N)`, 총 `O(R log N)`. 1080p 1 ray/pixel = ~2M ray/frame.
- **DXR (DirectX Raytracing)** / **VK_KHR_ray_tracing_pipeline** (Vulkan 1.2+) / **MetalRT**: 하드웨어 RT 코어 활용. NVIDIA RTX (Turing 2018+) / AMD RDNA2 (2020+) / Apple A17/M3 (2023+) 부터 HW 가속.
- **셰이더 단계**: Ray Generation → Acceleration Structure traversal → Intersection / Any-Hit / Closest-Hit / Miss → Recursive trace.
- **Denoising**: 1 ray/pixel 은 노이즈 심함 — NVIDIA OptiX denoiser / Intel Open Image Denoise / DLSS 3.5 Ray Reconstruction 필수.

**장점**:
- 물리적으로 정확한 반사·굴절·소프트 섀도우·간접광 (global illumination)
- 장면 복잡도와 무관하게 광선당 `O(log N)` — 정점 셰이더가 N 에 비례하는 래스터화와 대조
- 비사실적 렌더링 (NPR) / VFX / 영화에서 표준 (Arnold / RenderMan)

**단점/주의**:
- **연산 비용**: 4K 60 FPS 풀 path tracing 은 RTX 4090 도 어려움 — Hybrid (rasterization + RT shadow / RT reflection) 가 실시간 표준 (Unreal Lumen, Cyberpunk 2077 RT Overdrive)
- **BVH 갱신 비용**: 애니메이션 장면은 매 프레임 refit 필요. 동적 객체는 TLAS (Top-Level AS) refit, 정적은 BLAS (Bottom-Level AS) 재사용
- **Divergence**: 광선마다 다른 셰이더 → SIMT GPU 의 wavefront divergence → 성능 저하. Ray sorting / Shader Execution Reordering (NVIDIA Ada) 로 완화
- **메모리**: BVH 가 정점 데이터의 1~2 배 차지 (RTX Mega Geometry 로 압축 시도 중)

**활용 예시** (DXR / HLSL Shader Model 6.3 — 최소 ray generation):

```hlsl
// raygen.hlsl — DirectX Raytracing (DXR), HLSL SM 6.3
RaytracingAccelerationStructure scene : register(t0);
RWTexture2D<float4>             output : register(u0);
cbuffer Cam : register(b0) { float4x4 invViewProj; float3 origin; };

[shader("raygeneration")]
void RayGen() {
    uint2 px = DispatchRaysIndex().xy;
    uint2 sz = DispatchRaysDimensions().xy;
    float2 ndc = (px + 0.5) / sz * 2.0 - 1.0;
    float4 dirH = mul(invViewProj, float4(ndc.x, -ndc.y, 1, 1));
    RayDesc ray;
    ray.Origin    = origin;
    ray.Direction = normalize(dirH.xyz / dirH.w - origin);
    ray.TMin = 0.001; ray.TMax = 1000.0;

    HitPayload payload = { float3(0,0,0), 0 };
    TraceRay(scene, RAY_FLAG_NONE, 0xFF, 0, 1, 0, ray, payload);
    output[px] = float4(payload.color, 1.0);
}

[shader("closesthit")]
void ClosestHit(inout HitPayload p, BuiltInTriangleIntersectionAttributes a) {
    // 교차점 normal / material 계산, shadow ray 추가 발사 등
    p.color = float3(a.barycentrics, 1.0 - a.barycentrics.x - a.barycentrics.y);
}

[shader("miss")]
void Miss(inout HitPayload p) { p.color = float3(0.6, 0.7, 0.9); } // sky
```

```cpp
// Vulkan VK_KHR_acceleration_structure — TLAS build 핵심 (C++)
VkAccelerationStructureBuildGeometryInfoKHR build = {
    .type  = VK_ACCELERATION_STRUCTURE_TYPE_TOP_LEVEL_KHR,
    .flags = VK_BUILD_ACCELERATION_STRUCTURE_PREFER_FAST_TRACE_BIT_KHR, // SAH
    .mode  = VK_BUILD_ACCELERATION_STRUCTURE_MODE_BUILD_KHR,
    .geometryCount = 1,
    .pGeometries   = &tlasGeo,
};
vkCmdBuildAccelerationStructuresKHR(cmd, 1, &build, &range);
```

**표준 인용**:
- Whitted, T., *An Improved Illumination Model for Shaded Display*, CACM 23(6), 1980 — Recursive ray tracing 원조
- Kajiya, J. T., *The Rendering Equation*, SIGGRAPH 1986 — Path tracing 수학 정식화
- Wald, I. et al., *On Fast Construction of SAH-based Bounding Volume Hierarchies*, IEEE RT 2007 — BVH SAH 빌드
- Microsoft, *DirectX Raytracing (DXR) Functional Spec* — DispatchRays / TraceRay / Acceleration Structure
- Vulkan 1.3 Specification §35 (Ray Tracing), VK_KHR_ray_tracing_pipeline + VK_KHR_acceleration_structure
- NVIDIA, *Ray Tracing Gems* I (2019) & II (2021), Apress

---

<a id="z-buffering-depth-test"></a>

## 3. Z-buffering / Depth Buffer (가시성 결정과 깊이 정밀도)

**목적**: 카메라에서 가까운 픽셀만 그리고 가려진 픽셀(hidden surface)을 제거하는 표준 알고리즘. Catmull (1974) 박사 논문에서 제안된 이후 모든 GPU 의 기본 가시성 결정 방식.

**특징/메커니즘**:
- **Z-buffer**: 화면 해상도 크기의 2D float 배열에 각 픽셀의 가장 가까운 깊이값 저장. fragment 가 들어올 때마다 `if (newZ < storedZ) { write color & depth }`.
- **Painter's algorithm 과 대조**: 정렬 후 뒤→앞 그리기. 교차하는 삼각형 처리 불가 — Z-buffer 가 표준이 된 이유.
- **Early-Z (Early Depth Test)**: Fragment shader **이전에** depth test 수행 → 가려진 픽셀의 fragment 셰이더 호출 자체를 스킵. `discard` / 알파 테스트 / depth write in shader 가 있으면 비활성화.
- **Hi-Z (Hierarchical Z)**: Z-buffer 의 mip-map. 타일(8×8 등) 단위로 max-Z 저장 → 타일 전체가 기존 max-Z 보다 멀면 전체 스킵. NVIDIA / AMD 모두 HW 지원.
- **Z-prepass**: 1 패스로 depth 만 그리고, 2 패스에서 expensive shading 수행. Overdraw 제거 — Doom 2016 / id Tech 6 표준.
- **Reverse-Z**: 깊이를 `[1, 0]` 로 반전 사용. 부동소수점의 `[0.5, 1)` 정밀도가 `[0, 0.5)` 의 4 배 큰데, 카메라 가까운 영역에 더 많은 정밀도가 필요 — 대형 scene 의 z-fighting 해소 표준 기법. `glClipControl(GL_LOWER_LEFT, GL_ZERO_TO_ONE)` (OpenGL 4.5+) / `VK_EXT_depth_clip_control` (Vulkan).
- **포맷**: `D24_UNORM_S8_UINT` (전통), `D32_SFLOAT` (Reverse-Z 권장), `D32_SFLOAT_S8_UINT` (stencil 병행).

**장점**:
- 정렬 불필요 — 임의 순서로 삼각형 제출 가능
- 교차·복잡한 점유 정확히 처리
- HW 가속 — 별도 CPU 작업 없음

**단점/주의**:
- **Z-fighting**: 두 표면이 같은 깊이일 때 점멸. Near/far plane 비율 (`far/near` 가 1000 이하 권장) + Reverse-Z + polygonOffset (`glPolygonOffset`) 로 완화.
- **투명도 처리 어려움**: 알파 블렌딩은 뒤→앞 정렬 필요 — OIT (Order-Independent Transparency, Weighted Blended OIT 등) 별도 기법 필요
- **Memory bandwidth**: 1080p D32 = 8 MB / frame. 모바일 TBDR 은 on-chip tile memory 로 절약.

**활용 예시** (Direct3D 12 / HLSL — Reverse-Z 설정):

```cpp
// D3D12 — Reverse-Z 프로젝션 행렬 + depth state
XMMATRIX proj = XMMatrixPerspectiveFovLH(
    XMConvertToRadians(60.0f), aspect, /*near*/0.1f, /*far*/10000.0f);
// near/far swap for reverse-Z
XMMATRIX reverseZ = XMMatrixSet(
    1,0,0,0,  0,1,0,0,  0,0,-1,0,  0,0,1,1) * proj;

D3D12_DEPTH_STENCIL_DESC ds = {};
ds.DepthEnable    = TRUE;
ds.DepthWriteMask = D3D12_DEPTH_WRITE_MASK_ALL;
ds.DepthFunc      = D3D12_COMPARISON_FUNC_GREATER_EQUAL; // reverse-Z 핵심
psoDesc.DSVFormat = DXGI_FORMAT_D32_FLOAT;
psoDesc.DepthStencilState = ds;

// clear: 0.0 (most distant in reverse-Z)
cmd->ClearDepthStencilView(dsv, D3D12_CLEAR_FLAG_DEPTH, 0.0f, 0, 0, nullptr);
```

```glsl
// fragment.frag — Early-Z 친화적 셰이더 (depth write 없음, discard 없음)
#version 450
layout(early_fragment_tests) in;  // 명시적 Early-Z 강제 (GLSL 4.20+)
layout(location = 0) out vec4 outColor;
void main() {
    outColor = vec4(0.7, 0.5, 0.2, 1.0);
    // discard 나 gl_FragDepth 쓰면 Early-Z 비활성화됨 — 주의
}
```

**표준 인용**:
- Catmull, E., *A Subdivision Algorithm for Computer Display of Curved Surfaces*, PhD diss., Univ. of Utah, 1974 — Z-buffer 제안
- Lapidous, E. & Jiao, G., *Optimal Depth Buffer for Low-Cost Graphics Hardware*, SIGGRAPH/Eurographics Workshop 1999 — Reverse-Z 분석
- Akenine-Möller et al., *Real-Time Rendering*, 4th ed., Ch. 23 (Graphics Hardware)
- NVIDIA, *Depth Precision Visualized*, 2015 (Reverse-Z 권장)
- Vulkan 1.3 Specification §28.5 (Depth Test), VK_EXT_depth_clip_control

---

<a id="pbr-cook-torrance"></a>

## 4. PBR (Physically Based Rendering) — Cook-Torrance BRDF

**목적**: 실제 물리 법칙(에너지 보존 / Fresnel / microfacet 이론)에 기반한 라이팅 모델. 같은 머터리얼이 다양한 조명 환경에서 일관되게 보이도록 보장. 2012 년 Disney *Principled BRDF* 이후 게임/영화 표준.

**특징/메커니즘**:
- **Phong / Blinn-Phong (legacy, 1975/1977)**: `color = ambient + diffuse · max(0, N·L) + specular · pow(max(0, N·H), shininess)`. 에너지 보존 안 됨, 머터리얼 파라미터가 비물리적 (shininess 1~1000 임의값).
- **Cook-Torrance BRDF (1982)**: `f_r = (D · F · G) / (4 · (N·L) · (N·V))`
  - **D (Normal Distribution Function, NDF)** — GGX / Trowbridge-Reitz 표준. `D_GGX(h) = α² / (π · ((N·h)²·(α²-1)+1)²)`
  - **F (Fresnel)** — Schlick 근사: `F(θ) = F0 + (1-F0) · (1 - cos θ)⁵`
  - **G (Geometry / Shadowing-Masking)** — Smith joint masking 표준
- **Metallic-Roughness workflow** (Disney / glTF 2.0 / Unreal / Unity URP 기본): `baseColor (RGB) + metallic [0,1] + roughness [0,1] + normal + AO`. 직관적, 텍스처 메모리 적음. **권장**.
- **Specular-Glossiness workflow**: `diffuse (RGB) + specular (RGB) + glossiness [0,1]`. 비금속의 specular 색 자유 — legacy / 일부 영화 파이프라인.
- **IBL (Image-Based Lighting)**:
  - **Diffuse irradiance map**: HDR 환경맵의 cosine-weighted 적분 → 32×32 cubemap pre-bake
  - **Specular pre-filtered map**: roughness 단계별 mip-map cubemap (Mipmap level = roughness 인덱스)
  - **Split-sum approximation (Karis, UE4, 2013)**: BRDF LUT 2D texture (`NdotV`, `roughness` → `scale`, `bias`) 로 분리 → 실시간 가능
- **HDR + Tone mapping**: 라이팅은 linear HDR (>1.0 허용) 으로 계산 → ACES / Reinhard / Uncharted2 tone map 으로 LDR `[0,1]` 변환 → sRGB γ 보정 (`pow(c, 1/2.2)`).
- **시간 복잡도**: 픽셀당 light L 개에 대해 `O(L)`. Many lights 는 Forward+ / Deferred (§5) 필요.

**장점**:
- 물리적 일관성 — 햇빛/실내/스튜디오 조명에서 같은 머터리얼이 자연스러움
- 아티스트 친화 — `metallic`/`roughness` 2 파라미터로 대부분의 실 머터리얼 표현
- 영화·게임 자산 호환 (glTF 2.0 표준)

**단점/주의**:
- IBL pre-bake 비용 — 동적 환경에서는 SH (Spherical Harmonics) probe / DDGI / Lumen 같은 dynamic GI 필요
- 에너지 보존 ↔ 멀티 스캐터링 (multi-scatter) 보정 — Heitz 2016 추가 보정항으로 거친 금속 어두워지는 문제 해결
- Subsurface scattering / Clearcoat / Sheen / Anisotropy 같은 확장 BRDF 는 별도 항 추가 (Disney Principled 확장)

**활용 예시** (HLSL SM 6.6 — Cook-Torrance + IBL split-sum):

```hlsl
// pbr.hlsl — Cook-Torrance + Metallic-Roughness + IBL
static const float PI = 3.14159265;

float D_GGX(float NoH, float roughness) {
    float a  = roughness * roughness;
    float a2 = a * a;
    float d  = NoH * NoH * (a2 - 1.0) + 1.0;
    return a2 / (PI * d * d);
}
float3 F_Schlick(float HoV, float3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - HoV, 5.0);
}
float G_SmithGGX(float NoV, float NoL, float roughness) {
    float k  = (roughness + 1.0); k = k*k * 0.125; // Karis 2013
    float gv = NoV / (NoV * (1.0 - k) + k);
    float gl = NoL / (NoL * (1.0 - k) + k);
    return gv * gl;
}

float3 PBR_Direct(float3 N, float3 V, float3 L, float3 albedo,
                  float metallic, float roughness, float3 lightColor) {
    float3 H   = normalize(V + L);
    float  NoL = saturate(dot(N, L));
    float  NoV = saturate(dot(N, V));
    float  NoH = saturate(dot(N, H));
    float  HoV = saturate(dot(H, V));

    float3 F0  = lerp(float3(0.04, 0.04, 0.04), albedo, metallic);
    float  D   = D_GGX(NoH, roughness);
    float3 F   = F_Schlick(HoV, F0);
    float  G   = G_SmithGGX(NoV, NoL, roughness);
    float3 spec = (D * F * G) / max(4.0 * NoV * NoL, 1e-4);

    float3 kd  = (1.0 - F) * (1.0 - metallic); // 금속은 diffuse 없음
    float3 diff = kd * albedo / PI;
    return (diff + spec) * lightColor * NoL;
}
```

```glsl
// IBL — split-sum (Karis UE4 2013) GLSL 450
vec3 IBL_Specular(vec3 N, vec3 V, vec3 F0, float roughness) {
    vec3  R       = reflect(-V, N);
    float NoV     = max(dot(N, V), 0.0);
    float mip     = roughness * (MAX_REFLECTION_LOD - 1.0);
    vec3  prefilt = textureLod(prefilterMap, R, mip).rgb;
    vec2  brdf    = texture(brdfLUT, vec2(NoV, roughness)).rg; // 2D LUT
    return prefilt * (F0 * brdf.x + brdf.y);
}
```

**표준 인용**:
- Cook, R. L. & Torrance, K. E., *A Reflectance Model for Computer Graphics*, SIGGRAPH 1982 / ACM TOG 1(1), 1982
- Burley, B., *Physically Based Shading at Disney*, SIGGRAPH 2012 Course Notes — Disney Principled BRDF
- Karis, B., *Real Shading in Unreal Engine 4*, SIGGRAPH 2013 — Split-sum IBL
- Walter, B. et al., *Microfacet Models for Refraction through Rough Surfaces*, EGSR 2007 — GGX/Trowbridge-Reitz
- Heitz, E., *Understanding the Masking-Shadowing Function in Microfacet-Based BRDFs*, JCGT 3(2), 2014
- Khronos Group, *glTF 2.0 Specification — Material PBR Metallic Roughness*
- Pharr, M., Jakob, W., Humphreys, G., *Physically Based Rendering: From Theory to Implementation*, 4th ed., MIT Press, 2023

---

<a id="forward-vs-deferred-rendering"></a>

## 5. Forward vs Deferred Rendering (라이팅 전략과 G-buffer)

**목적**: 다수의 광원이 있는 장면에서 라이팅을 효율적으로 계산하는 전략 선택. Forward / Deferred / Forward+ (Tiled Forward) / Tile-based Deferred (TBDR) — 각각의 trade-off 가 명확합니다.

**특징/메커니즘**:

### Forward Rendering (전통)
- 각 fragment 마다 모든 라이트 순회 → fragment shader 안에서 `for (i = 0; i < numLights; ++i) {...}`.
- 시간 복잡도: `O(픽셀 P · 라이트 L · overdraw)` — 라이트 많으면 비용 폭증.
- 장점: MSAA 자연스러움, 투명 객체 OK, 머터리얼 다양성 자유, 모바일 친화 (특히 TBDR).
- 단점: 라이트 수 증가에 약함 (~8 dynamic light 한계).

### Deferred Rendering (G-buffer)
- **Pass 1 (Geometry Pass)**: 머터리얼 속성을 G-buffer 에 기록.
  - 표준 G-buffer (`MRT` Multiple Render Targets, 보통 4 개):
    - `RT0`: Albedo (RGB) + Metallic (A) — `R8G8B8A8_UNORM`
    - `RT1`: Normal (RGB octahedral encoded) + Roughness (A) — `R16G16_FLOAT` 등
    - `RT2`: Emissive (RGB) + AO (A)
    - `RT3`: Motion vector (RG) + Custom — TAA / RT denoising 용
  - `Depth`: D32_SFLOAT (Reverse-Z)
- **Pass 2 (Lighting Pass)**: G-buffer 를 텍스처로 샘플링하면서 라이트마다 quad / sphere volume 그리기.
- 시간 복잡도: `O((픽셀 P · L) + (P · overdraw_geometry))` — 라이트 N 개에 선형, overdraw 와 무관.
- 장점: 라이트 수백 개 가능 (Killzone 2 / Battlefield), 머터리얼-라이트 decoupling.
- 단점: 메모리 대역폭 막대 (4 RT × 1080p ≈ 30 MB / frame), MSAA 어려움 (MS G-buffer 비싸 → TAA / DLAA 대체), 투명 객체는 별도 forward pass 필요.

### Forward+ (Tiled Forward) — Harada 2012
- 화면을 16×16 등 타일로 분할 → compute shader 로 타일당 영향 라이트 리스트(light list) 생성 → forward pass 에서 자기 타일 라이트만 순회.
- 장점: Forward 의 머터리얼/투명 장점 + Deferred 수준의 라이트 수. **현대 PC/콘솔 표준** (Unreal Engine 4/5 Mobile, Unity URP).
- Frustum Culling + Light Culling 함께 활용.

### Tile-Based Deferred Rendering (TBDR) — 모바일
- Apple / PowerVR / Mali — 타일 단위 framebuffer 가 **on-chip tile memory** 에 상주. G-buffer 를 main memory 에 쓰지 않고 그 자리에서 lighting → 모바일에서 deferred 의 대역폭 문제 해소.
- Metal: `[[color(0)]]` framebuffer fetch / Vulkan: subpass input attachment.

### 텍스처 압축 (메모리 + 대역폭 절감)
- **ASTC** (Adaptive Scalable Texture Compression, Khronos 표준, 모바일 표준)
- **BC1~BC7** (Block Compression, DirectX/PC 표준 — BC7 최고 품질, BC6H HDR)
- **ETC2** (OpenGL ES 3.0 mandatory, 모바일)

**장점/단점 요약**:

| 항목 | Forward | Deferred | Forward+ | TBDR (mobile) |
|---|---|---|---|---|
| 라이트 수 | ~8 | 수백 | 수백 | 수십 |
| 메모리 대역폭 | 낮음 | 매우 높음 | 중간 | 낮음 (on-chip) |
| 머터리얼 다양성 | 자유 | 제한 | 자유 | 자유 |
| MSAA | 쉬움 | 어려움 | 쉬움 | 쉬움 |
| 투명 객체 | OK | 별도 forward pass | OK | OK |
| 권장 플랫폼 | 모바일 / VR | PC / 콘솔 (구세대) | PC / 콘솔 (현세대) | 모바일 |

**활용 예시** (HLSL — Forward+ light culling compute shader):

```hlsl
// light_cull.hlsl — Forward+ Tile-based light culling, HLSL SM 6.0
#define TILE_SIZE   16
#define MAX_LIGHTS_PER_TILE 256

cbuffer Frame : register(b0) { float4x4 invProj; uint numLights; };
StructuredBuffer<Light>  lights : register(t0);
Texture2D<float>         depthTex : register(t1);
RWStructuredBuffer<uint> tileLightList : register(u0); // tile -> light indices

groupshared uint  gMinDepth, gMaxDepth, gLightCount;
groupshared uint  gLightIdx[MAX_LIGHTS_PER_TILE];

[numthreads(TILE_SIZE, TILE_SIZE, 1)]
void CS_Cull(uint3 gid : SV_GroupID, uint3 dtid : SV_DispatchThreadID,
             uint  gi  : SV_GroupIndex) {
    if (gi == 0) { gMinDepth = 0xFFFFFFFF; gMaxDepth = 0; gLightCount = 0; }
    GroupMemoryBarrierWithGroupSync();

    // 1. tile 의 min/max depth 계산
    float z = depthTex.Load(int3(dtid.xy, 0));
    InterlockedMin(gMinDepth, asuint(z));
    InterlockedMax(gMaxDepth, asuint(z));
    GroupMemoryBarrierWithGroupSync();

    // 2. tile frustum vs 각 light sphere intersection
    for (uint i = gi; i < numLights; i += TILE_SIZE * TILE_SIZE) {
        if (SphereInTileFrustum(lights[i], gid.xy, asfloat(gMinDepth), asfloat(gMaxDepth))) {
            uint slot; InterlockedAdd(gLightCount, 1, slot);
            if (slot < MAX_LIGHTS_PER_TILE) gLightIdx[slot] = i;
        }
    }
    GroupMemoryBarrierWithGroupSync();

    // 3. 결과 write
    if (gi < gLightCount) {
        uint base = (gid.y * tileCountX + gid.x) * MAX_LIGHTS_PER_TILE;
        tileLightList[base + gi] = gLightIdx[gi];
    }
}
```

```cpp
// Metal 3 — TBDR subpass framebuffer fetch (Objective-C++)
// Metal Shading Language: G-buffer 를 [[color(0..3)]] 로 받아서 즉시 lighting
fragment float4 lightingFS(GBufferIn in [[stage_in]],
                           float4 albedo  [[color(0)]],
                           float4 normal  [[color(1)]],
                           float  depth   [[color(2)]],
                           constant LightUBO& lights [[buffer(0)]]) {
    // on-chip tile memory 에서 직접 읽기 — main memory 미경유
    return CalcLighting(albedo.rgb, normal.xyz, depth, lights);
}
```

**표준 인용**:
- Hargreaves, S. & Harris, M., *Deferred Shading*, NVIDIA GDC 2004
- Harada, T., McKee, J., Yang, J. C., *Forward+: Bringing Deferred Lighting to the Next Level*, Eurographics 2012 Short Papers
- Olsson, O. & Assarsson, U., *Clustered Deferred and Forward Shading*, HPG 2012
- Akenine-Möller et al., *Real-Time Rendering*, 4th ed., Ch. 20 (Efficient Shading)
- Imagination Technologies, *PowerVR Architecture Overview* — TBDR
- Apple, *Metal Shading Language Specification 3.x* — Tile shading / subpass
- Khronos Group, *KTX2 / ASTC / BC7 Texture Compression* specifications
- Vulkan 1.3 §8 (Render Pass) — subpass input attachment for TBDR

---

## 카탈로그 통합 참고

본 문서의 5 항목은 패턴 카탈로그 `patterns/` 의 다음 문서들과 함께 사용합니다:
- **[`game-dev.md`](game-dev.md)** — Game Loop 안에서 본 렌더링 파이프라인이 매 프레임 실행됨
- **[`concurrency.md`](concurrency.md)** — Compute shader (Forward+ light culling) 는 SIMT / Job-system 의 변형
- **[`caching.md`](caching.md)** — IBL pre-bake / BVH cache / shader cache

알고리즘 카탈로그 `algorithms/` 연계:
- **[`spatial.md`](../algorithms/spatial.md)** — BVH / Octree / k-d Tree 의 일반 알고리즘 분석
- **[`geometry.md`](../algorithms/geometry.md)** — 광선-삼각형 교차 (Möller-Trumbore), 평면-AABB 교차
- **[`image-processing.md`](../algorithms/image-processing.md)** — Tone mapping / Bloom / FXAA 등 post-processing

언어 카탈로그 `languages/` 연계:
- **[`glsl.md`](../languages/glsl.md)** — OpenGL / Vulkan 셰이더 (SPIR-V 컴파일)
- **[`hlsl.md`](../languages/hlsl.md)** — Direct3D 12 / DXR 셰이더 (DXIL 컴파일)
- **[`cuda-c-cplusplus.md`](../languages/cuda-c-cplusplus.md)** — GPGPU / OptiX ray tracing kernel
