# 게임 개발 패턴 (Game Development Patterns)

Robert Nystrom *Game Programming Patterns* (2014) 표준 + 현대 게임 엔진(Unity / Unreal / Godot / Bevy) 실무 패턴 12 항목. 일반 앱 패턴과 별개의 **실시간(16~33 ms / frame)·데이터 지향·상태 중심** 패턴.

**적용 영역**: 콘솔/PC 게임, 모바일 게임, VR/AR, 게임 같은 인터랙티브 시뮬레이션(자율주행 시뮬레이션 / 디지털 트윈).

**관련 카탈로그**:
- [`../algorithms/game-ai.md`](../algorithms/game-ai.md) — Minimax / Alpha-Beta / MCTS / GA / SA (AI 알고리즘)
- [concurrency.md](concurrency.md) — Job system 은 Fork-Join / Work-Stealing 변형
- [caching.md](caching.md) — Asset cache 는 Multi-Tier Cache 변형
- [state machine](behavioral.md#7-state) — 행위 패턴 State 의 게임 특화

---

<a id="1-game-loop"></a>

## 1. Game Loop (게임 루프)

**목적**: 입력 처리·게임 상태 갱신·렌더링을 무한 반복하면서, 프레임 시간 변동과 무관하게 일관된 게임 진행 속도를 보장합니다.

**특징/메커니즘**:
- 가장 핵심적인 패턴 — 모든 게임은 어떤 형태로든 Game Loop 를 가짐
- 세 가지 변형:
  - **Fixed timestep**: `update(dt=const)` 고정. 물리·네트워크 결정론적. 렌더 프레임이 늦으면 게임이 느려짐
  - **Variable timestep**: `update(dt=actualElapsed)`. 프레임 시간만큼 진행. 물리 불안정(스파이럴 오브 데스)
  - **Semi-fixed / Decoupled**: 물리는 fixed timestep accumulator 로 N 회 update, 렌더링은 보간(interpolation) 으로 부드럽게. 현대 표준
- Render 와 Update 분리: `accumulator += dt; while(accumulator >= STEP) { update(STEP); accumulator -= STEP } render(accumulator / STEP)`
- 60 FPS (16.67 ms) / 120 FPS (8.33 ms) / 144 FPS — 모바일은 30 FPS 도 흔함

**장점**:
- 프레임율 변동에도 결정론적 시뮬레이션 (Semi-fixed)
- 입력 응답성 / 렌더 부드러움 양립
- 리플레이·네트워크 동기화 기반

**단점/주의**:
- Variable timestep 의 스파이럴 오브 데스: 프레임이 늦어지면 dt 가 커지고, 큰 dt 로 물리가 더 늦어지고 → 무한 악순환
- V-sync / 멀티 모니터 / VRR(가변 주사율) 환경 처리 추가 필요
- 모바일 thermal throttling 시 frame skip 전략 필요

**활용 예시**:
- Unity `FixedUpdate` (물리) + `Update` (입력/렌더) + `LateUpdate` (카메라)
- Unreal `Tick(DeltaTime)`
- Bevy `App::run` schedule
- 모든 게임 엔진의 메인 루프

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
// Semi-fixed timestep + interpolation (Glenn Fiedler "Fix Your Timestep" 표준)
class GameLoop(private val game: Game) {
    private val stepMs = 1000L / 60   // 16.67ms fixed step
    private var accumulator = 0L
    private var previousTime = System.currentTimeMillis()

    fun run() {
        while (game.isRunning) {
            val now = System.currentTimeMillis()
            val frameTime = (now - previousTime).coerceAtMost(250L)  // clamp 폭주 방지
            previousTime = now
            accumulator += frameTime

            game.processInput()

            // 누적된 시간만큼 fixed step 으로 update
            while (accumulator >= stepMs) {
                game.fixedUpdate(stepMs / 1000.0)
                accumulator -= stepMs
            }

            // 보간 비율로 렌더링 → 화면이 부드러움
            val alpha = accumulator.toDouble() / stepMs
            game.render(alpha)
        }
    }
}
```

**관련 패턴**: [Double Buffer](#9-double-buffer-game), [Update Method](#3-component-pattern), [Dirty Flag](#8-dirty-flag)

---

<a id="2-ecs"></a>

## 2. Entity-Component-System (ECS)

**목적**: 게임 객체를 Entity(ID) + Component(데이터) + System(로직) 셋으로 완전히 분리하여, 데이터 지향 설계로 CPU 캐시 적중률을 극대화하고 수만~수십만 개체를 60 FPS 로 처리합니다.

**특징/메커니즘**:
- **Entity**: 단순 ID(u64 / u32). 로직·데이터 없음
- **Component**: Plain Old Data(POD) 구조체. `Position{x,y,z}`, `Velocity{dx,dy,dz}`, `Health{hp}`
- **System**: 특정 Component 조합을 가진 Entity 들을 순회하며 로직 실행. `MovementSystem` → `Position + Velocity` 쿼리
- 두 가지 저장 구조:
  - **Archetype-based** (Unity DOTS, Bevy): 동일 Component 조합끼리 묶어 chunk 에 배열로 저장. cache-friendly, 컴포넌트 추가/제거는 chunk 이동
  - **Sparse Set** (EnTT, flecs): 각 Component 타입마다 별도 dense array + sparse index. 컴포넌트 추가/제거 빠름, 순회는 약간 느림
- OOP 의 상속 트리(`Enemy : GameObject`) 대신 조합(`Entity + Health + AI + Sprite`)
- "Composition over inheritance" 의 극단적 적용

**장점**:
- **데이터 지향**: 같은 타입 Component 가 메모리에 연속 배치 → CPU 캐시 미스 최소화 → SIMD 적용 가능
- 컴포넌트 단위 조합 자유도 (런타임에 능력 추가/제거)
- System 간 의존성이 명확 (input/output Component 만)
- 멀티스레딩 친화 (시스템 간 read/write component 충돌만 관리하면 병렬화)

**단점/주의**:
- 학습 곡선 가파름 (OOP 멘탈 모델과 다름)
- 디버깅 도구 부족 (객체 단위 추적 어려움)
- Component 간 강한 참조가 필요한 경우 어색 (Entity ID 로 lookup)
- Archetype 변경 비용 (Bevy 의 `Commands` 는 frame 끝에서 batch 적용)

**활용 예시**:
- Unity DOTS (Data-Oriented Technology Stack) + Burst Compiler + Job System
- Bevy (Rust) — Archetype ECS
- EnTT (C++) — Sparse Set ECS, Minecraft Bedrock 에서 사용
- Overwatch 의 ECS 발표 (GDC 2017) — 결정론적 lockstep 의 핵심

**난이도**: 높음 | **사용 빈도**: ★★★★☆ (AAA / 인디 양쪽 표준화 중)

**Pseudo-code 예제**:
```kotlin
// 단순 ECS — 실제로는 archetype chunk 로 구현
typealias Entity = Int

data class Position(val x: Float, val y: Float)
data class Velocity(val dx: Float, val dy: Float)
data class Health(val hp: Int)

class World {
    private val positions = HashMap<Entity, Position>()
    private val velocities = HashMap<Entity, Velocity>()
    private val healths = HashMap<Entity, Health>()
    private var nextId = 0

    fun spawn(): Entity = nextId++
    fun add(e: Entity, c: Any) = when (c) {
        is Position -> positions[e] = c
        is Velocity -> velocities[e] = c
        is Health -> healths[e] = c
        else -> error("unknown component")
    }

    // System: Position + Velocity 를 가진 모든 entity 이동
    fun movementSystem(dt: Float) {
        for ((e, p) in positions) {
            val v = velocities[e] ?: continue
            positions[e] = Position(p.x + v.dx * dt, p.y + v.dy * dt)
        }
    }
}

// 사용
val world = World()
val enemy = world.spawn()
world.add(enemy, Position(0f, 0f))
world.add(enemy, Velocity(1f, 0f))
world.add(enemy, Health(100))
world.movementSystem(0.016f)
```

**관련 패턴**: [Component Pattern](#3-component-pattern) (ECS 의 OOP 변형), [Data Locality](#5-spatial-partition), Flyweight

---

<a id="3-component-pattern"></a>

## 3. Component Pattern (컴포넌트 패턴)

**목적**: GameObject(Entity) 가 능력별 Component 를 보유하여 다중 상속 없이 조합 가능한 행동 모델을 제공합니다. ECS 의 OOP 변형.

**특징/메커니즘**:
- ECS 와 달리 Component 가 **데이터 + 로직** 둘 다 가짐 (자체 `Update()` 메서드)
- GameObject 는 Component list 보유 + 위임 (`gameObject.GetComponent<Rigidbody>()`)
- 상속 트리 폭발 회피: `FlyingFireBreathingEnemy` 대신 `Enemy + FlyComponent + FireBreathComponent`
- Component 간 통신:
  - GameObject 경유 lookup
  - 메시지 시스템 (`SendMessage` — 느리지만 유연)
  - 직접 참조 (캐싱)

**장점**:
- 디자이너 친화적 (Unity Inspector / Unreal Blueprint 에서 드래그)
- OOP 익숙한 개발자 학습 비용 낮음
- 런타임에 Component 추가/제거 (`AddComponent<T>()`)

**단점/주의**:
- ECS 만큼 cache-friendly 하지 않음 (가상 함수 호출, 분산 메모리)
- Component 간 의존성 그래프가 암시적이라 추적 어려움
- 직렬화 / Undo 구현 복잡 (Component 간 참조)

**활용 예시**:
- Unity `MonoBehaviour` — 가장 대표적
- Unreal `UActorComponent` (Actor + Component 모델)
- Godot — Node 트리는 컴포넌트보다는 Scene Graph 에 가까우나 비슷한 사상

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
abstract class Component {
    var owner: GameObject? = null
    open fun update(dt: Float) {}
    open fun render() {}
}

class GameObject {
    private val components = mutableListOf<Component>()

    fun <T : Component> addComponent(c: T): T {
        c.owner = this
        components.add(c)
        return c
    }

    inline fun <reified T : Component> getComponent(): T? =
        components.filterIsInstance<T>().firstOrNull()

    fun update(dt: Float) = components.forEach { it.update(dt) }
    fun render() = components.forEach { it.render() }
}

class TransformComponent(var x: Float = 0f, var y: Float = 0f) : Component()
class PhysicsComponent(var vx: Float = 0f, var vy: Float = 0f) : Component() {
    override fun update(dt: Float) {
        val t = owner?.getComponent<TransformComponent>() ?: return
        t.x += vx * dt
        t.y += vy * dt
    }
}
class SpriteComponent(val texture: String) : Component() {
    override fun render() {
        val t = owner?.getComponent<TransformComponent>() ?: return
        println("draw $texture at ${t.x}, ${t.y}")
    }
}

// 사용
val enemy = GameObject().apply {
    addComponent(TransformComponent(100f, 200f))
    addComponent(PhysicsComponent(vx = 10f))
    addComponent(SpriteComponent("enemy.png"))
}
enemy.update(0.016f)
enemy.render()
```

**관련 패턴**: [ECS](#2-ecs) (데이터 지향 변형), Strategy, Bridge

---

<a id="4-object-pool-game"></a>

## 4. Object Pool (오브젝트 풀) — 게임 특화

**목적**: 빈번하게 생성·파괴되는 객체(총알·파티클·적·이펙트)를 미리 할당해 두고 재사용하여, 동적 할당 비용과 GC stop-the-world 일시정지를 회피합니다.

**특징/메커니즘**:
- Pool 초기화 시 N 개 객체 일괄 할당 (`Bullet[1000]`)
- 활성/비활성 플래그로 구분 — 또는 free-list 로 비활성 객체 연결
- `Acquire()`: 비활성 객체 반환 + 활성화. 풀 고갈 시 → 정책에 따라 가장 오래된 객체 재활용 / null / 풀 확장
- `Release(obj)`: 활성 해제 (실제 메모리 해제 X)
- 일반 [Object Pool](creational.md) 과 차이: **fixed-size + per-frame 빈번 사용 + GC 회피가 주목적**

**장점**:
- 동적 할당 0 → 60 FPS 동안 GC 일시정지 회피 (특히 모바일 / Unity IL2CPP)
- 메모리 단편화 방지 (연속 영역)
- 캐시 친화적 (연속 배열 순회)

**단점/주의**:
- 초기 메모리 사용량 큼 (사용 안 해도 할당)
- Pool 고갈 정책 결정 필요 (확장 vs 재활용 vs 거부)
- 객체 reset 누락 시 이전 상태 leak (`Acquire` 시 초기화 보장)

**활용 예시**:
- 슈팅 게임 총알/탄막 (수천 발 동시)
- 파티클 시스템 (폭발·연기·불꽃)
- Unity `ObjectPool<T>` (2021+) / Unreal `FObjectPool` / 자체 구현
- 사운드 인스턴스 풀 (AudioSource)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class Bullet {
    var x = 0f; var y = 0f
    var vx = 0f; var vy = 0f
    var active = false
    var life = 0f

    fun reset(x: Float, y: Float, vx: Float, vy: Float) {
        this.x = x; this.y = y; this.vx = vx; this.vy = vy
        this.life = 3f; this.active = true
    }
    fun update(dt: Float) {
        if (!active) return
        x += vx * dt; y += vy * dt
        life -= dt
        if (life <= 0f) active = false
    }
}

class BulletPool(size: Int) {
    private val pool = Array(size) { Bullet() }

    fun acquire(x: Float, y: Float, vx: Float, vy: Float): Bullet? {
        // 비활성 객체 찾기 — free-list 로 O(1) 가능
        val b = pool.firstOrNull { !it.active } ?: return null
        b.reset(x, y, vx, vy)
        return b
    }

    fun updateAll(dt: Float) = pool.forEach { it.update(dt) }
    fun activeCount() = pool.count { it.active }
}

// 사용 — 총알 발사
val pool = BulletPool(1000)
repeat(60) { pool.acquire(0f, 0f, vx = 100f, vy = 0f) }
pool.updateAll(0.016f)
```

**관련 패턴**: [Object Pool (일반)](creational.md), Flyweight, Spatial Partition

---

<a id="5-spatial-partition"></a>

## 5. Spatial Partition (공간 분할)

**목적**: 게임 월드를 공간적으로 분할하여, 충돌 검사·이웃 탐색·뷰 프러스텀 컬링을 O(N²) → O(N log N) 또는 O(N) 으로 줄입니다.

**특징/메커니즘**:
- 모든 객체 쌍 충돌 검사 = O(N²) → N=1000 이면 50만 쌍, 60 FPS 에서 불가능
- 핵심: **같은 영역의 객체끼리만 검사**
- 변형:
  - **Grid (Uniform Grid)**: 균일 격자. 균등 분포 / 비슷한 크기 객체에 최적. 구현 간단
  - **Quadtree (2D) / Octree (3D)**: 재귀 사분/팔분할. 객체 밀도 비균등에 적합. 동적 객체는 노드 재배치 비용
  - **BSP (Binary Space Partitioning)**: 평면으로 재귀 이분할. 정적 레벨 지오메트리에 강함 (Doom / Quake)
  - **BVH (Bounding Volume Hierarchy)**: AABB / sphere 의 계층 트리. 레이트레이싱 / 물리 엔진 표준
  - **k-d tree**: 축 정렬 hyperplane 으로 분할. 정적 점 집합 최근접 탐색
- 동적 vs 정적: 정적 지형은 BSP/BVH 구축 후 고정, 동적 객체는 Grid / loose octree

**장점**:
- 충돌 검사 N² → N log N (또는 N)
- 뷰 프러스텀 컬링 (안 보이는 객체 렌더 스킵)
- AI 시야 / 청각 범위 쿼리 가속
- 레이캐스트(레이트레이싱) 가속

**단점/주의**:
- 자료구조 구축·유지 비용 (동적 객체는 매 프레임 재배치)
- 큰 객체가 여러 셀에 걸침 → 중복 검사
- 균등 분포가 아니면 일부 셀에 객체 폭주

**활용 예시**:
- 물리 엔진 broad-phase (Box2D / Bullet / PhysX)
- 뷰 프러스텀 컬링 / occlusion culling
- 멀티플레이어 AOI (Area of Interest) — 시야 안 플레이어만 동기화
- 미니맵 / 레이더

**난이도**: 중간~높음 | **사용 빈도**: ★★★★☆

**Kotlin 예제**:
```kotlin
// 가장 단순한 Uniform Grid spatial hash
class GridPartition(
    private val cellSize: Float,
    private val worldW: Float,
    private val worldH: Float,
) {
    private val cols = (worldW / cellSize).toInt() + 1
    private val rows = (worldH / cellSize).toInt() + 1
    private val cells = Array(cols * rows) { mutableListOf<GameObject>() }

    private fun index(x: Float, y: Float): Int {
        val cx = (x / cellSize).toInt().coerceIn(0, cols - 1)
        val cy = (y / cellSize).toInt().coerceIn(0, rows - 1)
        return cy * cols + cx
    }

    fun rebuild(objects: List<GameObject>) {
        cells.forEach { it.clear() }
        for (o in objects) {
            val t = o.getComponent<TransformComponent>() ?: continue
            cells[index(t.x, t.y)].add(o)
        }
    }

    // 한 객체 주변 후보만 반환 — O(1) 평균
    fun nearby(x: Float, y: Float): List<GameObject> {
        val cx = (x / cellSize).toInt()
        val cy = (y / cellSize).toInt()
        val out = mutableListOf<GameObject>()
        for (dy in -1..1) for (dx in -1..1) {
            val nx = cx + dx; val ny = cy + dy
            if (nx in 0 until cols && ny in 0 until rows) {
                out.addAll(cells[ny * cols + nx])
            }
        }
        return out
    }
}
```

**관련 패턴**: [Object Pool](#4-object-pool-game), [Scene Graph](#6-scene-graph), [Dirty Flag](#8-dirty-flag)

---

<a id="6-scene-graph"></a>

## 6. Scene Graph (씬 그래프)

**목적**: 게임 월드의 객체를 부모-자식 트리로 구성하여, 부모의 변환(이동·회전·스케일)을 자식이 자동 상속받게 합니다.

**특징/메커니즘**:
- 각 노드는 **local transform** 보유 (`Mat4`)
- **World transform** = parent.worldTransform × local.transform — 트리 순회로 계산
- 캐릭터의 손에 든 검: 캐릭터 노드의 자식으로 두면 캐릭터가 움직일 때 검도 자동 따라옴
- 추가 기능: 가시성 상속, 활성/비활성 상속, 컬링용 bounding volume 계층 (BVH 와 결합)
- 트리 순회 순서:
  - **Depth-first pre-order**: 부모 변환 후 자식 변환 (대부분의 엔진)
  - **Post-order**: bounding volume 계산 시 자식 먼저

**장점**:
- 계층적 변환 자동화 (캐릭터 + 장비 + 이펙트)
- 가시성/활성 상태 일괄 토글 (씬 전체 끄기)
- 그룹 단위 컬링·LOD

**단점/주의**:
- 트리 깊이가 깊으면 변환 계산 누적 비용
- 부모 변경(reparenting) 시 world transform 재계산
- 자식이 많으면 캐시 미스 (포인터 따라가기)

**활용 예시**:
- Unity `Transform` 계층 (`Hierarchy` 창)
- Unreal `USceneComponent` 계층
- Godot `Node` 트리 (Scene Graph 가 엔진 핵심)
- glTF / FBX 본(bone) 계층 — 스켈레톤 애니메이션

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class SceneNode(val name: String) {
    var localX = 0f; var localY = 0f
    var worldX = 0f; var worldY = 0f
    private val children = mutableListOf<SceneNode>()
    var parent: SceneNode? = null

    fun addChild(c: SceneNode) { c.parent = this; children.add(c) }

    // 부모 world transform 이 주어지면 자식 world transform 계산 후 재귀
    fun updateWorldTransform(parentWorldX: Float = 0f, parentWorldY: Float = 0f) {
        worldX = parentWorldX + localX
        worldY = parentWorldY + localY
        children.forEach { it.updateWorldTransform(worldX, worldY) }
    }
}

// 사용 — 캐릭터의 손에 검 부착
val character = SceneNode("character").apply { localX = 100f; localY = 200f }
val hand = SceneNode("hand").apply { localX = 30f; localY = 0f }
val sword = SceneNode("sword").apply { localX = 5f; localY = 0f }
character.addChild(hand); hand.addChild(sword)
character.updateWorldTransform()
// sword.worldX = 100 + 30 + 5 = 135
```

**관련 패턴**: [Spatial Partition](#5-spatial-partition), Composite (GoF), [Dirty Flag](#8-dirty-flag) (transform 재계산 최적화)

---

<a id="7-ai-state-machine"></a>

## 7. State Machine for AI (AI 상태 기계)

**목적**: NPC / 적 AI 의 행동을 상태(state)와 전이(transition)로 모델링하여, 명확한 행동 흐름과 디자이너 친화적 시각화를 제공합니다.

**특징/메커니즘**:
- **FSM (Finite State Machine)**: 상태 + 전이 조건. `Idle → Patrol → Chase → Attack`
- **Hierarchical FSM (HFSM)**: 상태 안에 sub-FSM. `Combat` 상태 안에 `Aim / Shoot / Reload`. 상태 폭발 완화
- **Behavior Tree (BT)**: 트리 구조의 우선순위 평가. Selector / Sequence / Decorator / Leaf(Action/Condition). Halo 2 (2004) 이후 표준. Unreal 내장
- **GOAP (Goal-Oriented Action Planning)**: 목표 + 전제조건/효과 기반 행동 자동 조합. F.E.A.R. (2005). A* 로 계획 탐색
- **Utility AI**: 각 행동에 점수(utility) 산출 → 최고점 선택. Sims / RimWorld 계열. 점진적 행동 우선순위

**장점**:
- FSM: 디자이너가 이해하기 쉬움, 디버깅 명확
- BT: 재사용 가능한 노드 라이브러리, 시각 편집기 친화
- GOAP/Utility: 창발적 행동 (emergent behavior)

**단점/주의**:
- FSM 은 상태 수가 N 일 때 전이가 O(N²) 폭발 → HFSM/BT 로 대응
- BT 는 매 tick 마다 트리 전체 평가 (캐싱 필요)
- GOAP 는 계획 탐색 비용 큼, planner 디버깅 어려움
- Utility 는 점수 튜닝이 디자이너 영역 — 의도 추적 어려움

**활용 예시**:
- FSM: 거의 모든 단순 AI (적 보초, 문 열기)
- HFSM: Halo 1 의 Covenant AI
- BT: Halo 2~5, Bioshock, Spore, Unreal `UBehaviorTree`
- GOAP: F.E.A.R., S.T.A.L.K.E.R., Just Cause 2
- Utility AI: The Sims, RimWorld, Total War

**난이도**: 중간(FSM/BT) ~ 높음(GOAP) | **사용 빈도**: ★★★★★

**Kotlin 예제** (FSM):
```kotlin
sealed class EnemyState {
    abstract fun update(enemy: Enemy, dt: Float): EnemyState
}
object Idle : EnemyState() {
    override fun update(e: Enemy, dt: Float) =
        if (e.canSeePlayer()) Chase else this
}
object Chase : EnemyState() {
    override fun update(e: Enemy, dt: Float): EnemyState {
        e.moveTowardsPlayer(dt)
        return when {
            !e.canSeePlayer() -> Idle
            e.distanceToPlayer() < 2f -> Attack
            else -> this
        }
    }
}
object Attack : EnemyState() {
    override fun update(e: Enemy, dt: Float): EnemyState {
        e.attack()
        return if (e.distanceToPlayer() > 3f) Chase else this
    }
}

class Enemy {
    var state: EnemyState = Idle
    fun tick(dt: Float) { state = state.update(this, dt) }
    fun canSeePlayer(): Boolean = TODO()
    fun moveTowardsPlayer(dt: Float) {}
    fun attack() {}
    fun distanceToPlayer(): Float = TODO()
}
```

**관련 패턴**: [State (GoF)](behavioral.md#7-state), Strategy, [Dirty Flag](#8-dirty-flag), [game-ai algorithms](../algorithms/game-ai.md)

---

<a id="8-dirty-flag"></a>

## 8. Dirty Flag (더티 플래그)

**목적**: 비싼 계산 결과를 캐시하고, 입력이 바뀌었을 때만 재계산 플래그(dirty)를 세워, 매 프레임 무조건 재계산하는 비용을 회피합니다.

**특징/메커니즘**:
- 데이터에 `isDirty: Boolean` 플래그
- 입력 변경 시 → `isDirty = true`
- 결과 요청 시 → dirty 면 재계산 + 캐싱 + `isDirty = false`. clean 이면 캐시 반환
- 변형:
  - **상향 전파**: 자식이 dirty 면 부모 bounding volume 도 dirty (Scene Graph + BVH)
  - **하향 전파**: 부모 transform 이 바뀌면 모든 자식 world transform 도 dirty (Scene Graph)
  - **그룹 dirty**: 여러 객체를 묶어 일괄 재계산 (batching)

**장점**:
- 비싼 계산 (matrix multiply, 물리 시뮬레이션, 렌더 명령 빌드) 회피
- 메모리/CPU 양쪽 최적화
- Scene Graph 와 결합 시 큰 효과

**단점/주의**:
- dirty 누락 버그: 입력 변경 시 dirty 세팅 까먹으면 stale data
- 플래그 자체 메모리 비용 (수만 객체면 합산)
- 멀티스레딩에서 race condition 위험 (atomic 처리)

**활용 예시**:
- Scene Graph 의 world transform 재계산
- UI 레이아웃 (CSS / Flutter render object dirty rect)
- 셰이더 uniform 업로드 (변경된 것만)
- Save 시스템 (변경된 청크만 디스크에 기록 — incremental save)
- React 의 `setState` → 가상 DOM diff (Dirty Flag 의 함수형 변형)

**난이도**: 낮음 | **사용 빈도**: ★★★★★

**Kotlin 예제**:
```kotlin
class Transform2D {
    var x: Float = 0f
        set(v) { field = v; isDirty = true }
    var y: Float = 0f
        set(v) { field = v; isDirty = true }
    var rotation: Float = 0f
        set(v) { field = v; isDirty = true }

    private var isDirty = true
    private val cachedMatrix = FloatArray(9)

    fun getMatrix(): FloatArray {
        if (isDirty) {
            val cos = kotlin.math.cos(rotation)
            val sin = kotlin.math.sin(rotation)
            cachedMatrix[0] = cos;  cachedMatrix[1] = -sin; cachedMatrix[2] = x
            cachedMatrix[3] = sin;  cachedMatrix[4] = cos;  cachedMatrix[5] = y
            cachedMatrix[6] = 0f;   cachedMatrix[7] = 0f;   cachedMatrix[8] = 1f
            isDirty = false
        }
        return cachedMatrix
    }
}
```

**관련 패턴**: [Scene Graph](#6-scene-graph), Observer, Memoization, Lazy Initialization

---

<a id="9-double-buffer-game"></a>

## 9. Double Buffer (더블 버퍼) — 게임 특화

**목적**: 두 개의 버퍼를 번갈아 사용해, 한 버퍼에 쓰는 동안 다른 버퍼는 읽기/표시되도록 하여, tearing(찢김) 과 frame-coherent 문제를 해결합니다.

**특징/메커니즘**:
- **Front buffer**: 현재 화면에 표시 중. 읽기 전용
- **Back buffer**: 다음 프레임 렌더링 중. 쓰기 전용
- 프레임 완성 시 swap (포인터 교환 — O(1))
- **Triple buffering**: 버퍼 3개. swap 대기 없이 렌더 진행 가능. latency 1프레임 추가
- V-sync 와 결합: 디스플레이 refresh 신호에 swap 동기화 → tearing 제거
- 일반 [Double Buffer](concurrency.md) 와 차이: **GPU presentation queue / frame coherence** 가 주목적

**장점**:
- 렌더링 중간 상태가 화면에 노출 안 됨 (no flicker / tearing)
- 게임 로직과 렌더의 frame-coherent 분리
- GPU/CPU 병렬 (CPU 가 N+1 프레임 준비, GPU 는 N 프레임 렌더)

**단점/주의**:
- 메모리 2배 (해상도 × 색심도 × 2)
- V-sync 미스 시 stuttering (60 FPS 미달 → 30 FPS 로 떨어짐, VRR 로 완화)
- Triple buffering 은 input latency 증가

**활용 예시**:
- 모든 GPU 렌더 파이프라인 (DirectX / Vulkan / Metal swap chain)
- 물리 시뮬레이션의 "current state / next state" 분리 (Conway's Game of Life)
- 셀룰러 오토마타
- 네트워크 snapshot interpolation 의 from/to 버퍼

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Kotlin 예제** (셀룰러 오토마타 ─ 게임 of Life):
```kotlin
class CellGrid(val w: Int, val h: Int) {
    private var current = Array(h) { BooleanArray(w) }
    private var next = Array(h) { BooleanArray(w) }

    fun get(x: Int, y: Int) = current[y][x]
    fun set(x: Int, y: Int, alive: Boolean) { current[y][x] = alive }

    fun step() {
        for (y in 0 until h) for (x in 0 until w) {
            val n = neighbors(x, y)
            next[y][x] = if (current[y][x]) n in 2..3 else n == 3
        }
        // swap — current 의 쓰기와 읽기가 섞이지 않음
        val tmp = current; current = next; next = tmp
    }

    private fun neighbors(x: Int, y: Int): Int {
        var c = 0
        for (dy in -1..1) for (dx in -1..1) {
            if (dx == 0 && dy == 0) continue
            val nx = x + dx; val ny = y + dy
            if (nx in 0 until w && ny in 0 until h && current[ny][nx]) c++
        }
        return c
    }
}
```

**관련 패턴**: [Double Buffer (일반)](concurrency.md), [Game Loop](#1-game-loop), [Dirty Flag](#8-dirty-flag)

---

<a id="10-netcode"></a>

## 10. Game Netcode (게임 네트코드)

**목적**: 멀티플레이어 게임에서 네트워크 지연(50~200ms)·패킷 손실·대역폭 제약하에 모든 클라이언트가 일관된 게임 상태를 보도록 합니다.

**특징/메커니즘**:
- 4가지 주요 모델:
  - **Lockstep**: 모든 클라이언트가 동일 입력을 동일 tick 에 동시 실행. 결정론적 시뮬레이션 필수. **RTS (StarCraft / AoE)**
  - **Snapshot Interpolation**: 서버가 권위적 시뮬레이션, 일정 간격(10~30 Hz)으로 상태 스냅샷 전송. 클라이언트는 두 스냅샷 사이를 보간. 100ms 지연 효과. **FPS / MMO**
  - **Client Prediction + Server Reconciliation**: 클라이언트가 입력을 즉시 적용(예측), 서버 응답이 다르면 rewind & replay. **FPS (Source / Quake / Overwatch)**
  - **Rollback Netcode**: 매 프레임 입력 예측, 상대 입력 도착 시 과거로 롤백 + 재시뮬레이션. **격투 게임 (GGPO / Street Fighter 6)**
- 추가 기법:
  - **Reliable UDP**: TCP 는 head-of-line blocking, UDP 위에 selective ACK + retransmit (ENet / GameNetworkingSockets / Steam Networking)
  - **Delta encoding**: 이전 스냅샷 대비 변경분만 전송
  - **Interest Management / AOI**: 시야 밖 객체 동기화 생략 (MMO 필수)
  - **Lag compensation**: hitscan 무기에서 서버가 과거 시점으로 rewind 하여 hit 판정

**장점**:
- Lockstep: 대역폭 극소 (입력만), 결정론적
- Snapshot Interpolation: 클라이언트 부담 적음, 치트 어려움
- Client Prediction: 입력 응답성 (지연 숨김)
- Rollback: 느낌상 무지연, 격투에 최적

**단점/주의**:
- Lockstep: 한 명만 늦으면 전체 정지, 결정론 깨지면 desync
- Snapshot: 대역폭 큼, 보간 지연 누적
- Client Prediction: 서버와 클라 시뮬레이션 동일성 보장 어려움 (롤백/재계산 비용)
- Rollback: 시뮬레이션 비용 N배 (N프레임 롤백)
- 모든 네트코드 공통: 부정행위 방지(authoritative server), 가변 ping 처리

**활용 예시**:
- Lockstep: StarCraft, AoE, Supreme Commander
- Snapshot Interpolation: Source Engine (Counter-Strike), Halo, World of Warcraft
- Client Prediction: 거의 모든 현대 FPS, Overwatch GDC 2017 발표
- Rollback: GGPO (Street Fighter / Skullgirls / Guilty Gear Strive), Roll-back 의 Nintendo Smash Bros Ultimate (논쟁)

**난이도**: 매우 높음 | **사용 빈도**: ★★★★☆ (멀티플레이어 게임)

**Pseudo-code 예제** (Client Prediction + Reconciliation):
```kotlin
class NetworkedPlayer {
    var serverState: PlayerState = PlayerState()
    var predictedState: PlayerState = PlayerState()
    private val pendingInputs = mutableListOf<Pair<Int, Input>>()
    private var inputSeq = 0

    // 클라이언트: 입력을 즉시 적용 + 서버에 전송 + 큐에 보관
    fun applyInput(input: Input) {
        inputSeq++
        predictedState = simulate(predictedState, input)
        pendingInputs.add(inputSeq to input)
        sendToServer(inputSeq, input)
    }

    // 서버 응답 도착: 권위적 상태 + 마지막 처리된 입력 seq
    fun onServerSnapshot(state: PlayerState, lastProcessedSeq: Int) {
        serverState = state
        // 서버가 이미 처리한 입력은 큐에서 제거
        pendingInputs.removeAll { it.first <= lastProcessedSeq }
        // 미처리 입력을 서버 상태 위에 재적용 (reconciliation)
        predictedState = pendingInputs.fold(serverState) { s, (_, i) -> simulate(s, i) }
    }

    private fun simulate(s: PlayerState, i: Input): PlayerState = TODO()
    private fun sendToServer(seq: Int, i: Input) {}
}
```

**관련 패턴**: [Snapshot](data-access.md), [Memento (GoF)](#11-save-system), [Game Loop](#1-game-loop) (fixed timestep 필수), Lockstep ⊃ deterministic simulation

---

<a id="11-save-system"></a>

## 11. Save System / Serialization (저장 시스템)

**목적**: 게임 상태를 디스크에 저장하고 복원하면서, 게임 버전 업그레이드 후에도 이전 세이브를 로드할 수 있는 backward compatibility 를 제공합니다.

**특징/메커니즘**:
- 직렬화 포맷:
  - **JSON / YAML**: 가독성 좋음, 디버깅 쉬움, 크기 큼, 모드 친화적
  - **Binary (custom)**: 작음, 빠름, 디버깅 어려움
  - **FlatBuffers / Protobuf / Cap'n Proto**: 스키마 기반, 빠른 직렬화 + zero-copy 읽기, 버전 호환 내장
  - **MessagePack**: 작은 binary JSON
- **Versioned save**: `version` 필드 + 마이그레이션 함수 체인 (`v1 → v2 → v3`)
- **Memento 변형**: GoF Memento 의 게임 특화 — 전체 월드 스냅샷
- 추가 기법:
  - **Incremental save**: 변경된 청크만 저장 (Minecraft region file)
  - **Save slot**: 다중 슬롯 + 자동 저장 + 빠른 저장
  - **Cloud save**: Steam Cloud / iCloud 동기화 (충돌 해결 필요)
  - **암호화 / 체크섬**: 치트 방지 + 손상 검출
  - **압축**: zstd / lz4 (메모리 vs CPU 트레이드오프)

**장점**:
- 게임 진행 보존 (필수 기능)
- 디버깅 / 테스트 시 특정 상태 재현
- 멀티 디바이스 동기화
- 리플레이 시스템 기반

**단점/주의**:
- 버전 호환 부담 (출시 후 마이그레이션 코드 영구 유지)
- 직렬화 가능한 자료구조 제약 (포인터 / 람다 직렬화 불가)
- 큰 월드 = 큰 세이브 (월드 1GB+, Minecraft / No Man's Sky)
- 치트 방지 vs 모드 친화성 트레이드오프

**활용 예시**:
- Minecraft: Region file (32×32 청크 단위 incremental save, NBT 포맷)
- The Witcher 3 / Cyberpunk 2077: 압축된 binary 세이브
- 모든 RPG / 시뮬레이션 게임
- 스피드런용 save state (에뮬레이터, RetroArch)

**난이도**: 중간~높음 | **사용 빈도**: ★★★★★

**Kotlin 예제** (Versioned save + migration):
```kotlin
data class SaveV1(val playerName: String, val hp: Int)
data class SaveV2(val playerName: String, val hp: Int, val maxHp: Int)  // maxHp 추가
data class SaveV3(val playerName: String, val hp: Int, val maxHp: Int, val gold: Long)

object SaveMigrator {
    fun load(json: Map<String, Any?>): SaveV3 {
        val version = (json["version"] as? Number)?.toInt() ?: 1
        var s3 = when (version) {
            1 -> migrate1to2(json).let(::migrate2to3)
            2 -> migrate2to3(json)
            3 -> parseV3(json)
            else -> error("unknown save version: $version")
        }
        return s3
    }

    private fun migrate1to2(j: Map<String, Any?>): Map<String, Any?> =
        j + ("maxHp" to (j["hp"] as Number).toInt()) + ("version" to 2)
    private fun migrate2to3(j: Map<String, Any?>): Map<String, Any?> =
        j + ("gold" to 0L) + ("version" to 3)
    private fun parseV3(j: Map<String, Any?>) = SaveV3(
        j["playerName"] as String,
        (j["hp"] as Number).toInt(),
        (j["maxHp"] as Number).toInt(),
        (j["gold"] as Number).toLong(),
    )
}
```

**관련 패턴**: [Memento (GoF)](behavioral.md), [Snapshot](data-access.md), [Schema Versioning](deployment.md), [Netcode](#10-netcode) (rollback 의 state snapshot)

---

<a id="12-asset-pipeline"></a>

## 12. Asset Pipeline (에셋 파이프라인)

**목적**: 디자이너가 만든 source asset(PSD / FBX / WAV)을 게임 런타임에 최적화된 cooked asset(압축 텍스처 / 메시 binary / 스트리밍 오디오)으로 변환하고, 빌드/배포/로딩을 자동화합니다.

**특징/메커니즘**:
- **Source vs Cooked**:
  - Source: PSD / Blend / FBX / WAV — 작업용, 큼, 플랫폼 무관
  - Cooked: BC7 / ASTC 압축 텍스처, 플랫폼별 mesh binary, ADPCM/Vorbis 오디오
- **Import / Cook 단계**: 빌드 시 또는 변경 감지 시 자동 변환. Unity `AssetImporter` / Unreal `UAssetEditor`
- **Hot reload**: 게임 실행 중 에셋 변경 → 재로드. 이터레이션 속도 핵심
- **Streaming**: 큰 에셋(텍스처 / 메시 / 오디오)을 부분 로딩. 거리·시야 기반 우선순위 (LOD 와 결합)
- **LOD (Level of Detail)**: 카메라 거리에 따라 폴리곤 / 해상도 / 텍스처 mipmap 단계 변경
- **Texture atlas / Sprite sheet**: 작은 텍스처를 큰 한 장으로 묶어 draw call 감소
- **Asset bundle / Addressables**: 그룹 단위로 패키징 + 동적 다운로드 (Live ops, 패치)
- **Dependency graph**: 메시 → 머티리얼 → 텍스처 의존성 추적, 변경 시 부분 재빌드

**장점**:
- 런타임 메모리 / CPU 효율 (디코딩 불요)
- 플랫폼별 최적화 (모바일 ASTC, PC BC7, PS5 GNF)
- 디자이너 반복 속도 (hot reload)
- 패치 크기 최소화 (변경 에셋만)

**단점/주의**:
- 빌드 시간 증가 (수만 에셋 변환은 수 시간)
- 변환 결정론성 필수 (동일 input → 동일 output, 캐시 가능)
- Source asset 관리 (Git LFS / Perforce / Plastic SCM)
- 압축 손실 (블록 압축은 비가역)
- 콘솔 인증 시 에셋 제약 (메모리 한계, 로딩 시간)

**활용 예시**:
- Unity `AssetBundle` / `Addressables`
- Unreal `UAsset` / `Cooked Content`
- Godot `.import` 사이드카 파일
- Source Engine `vbsp` / `vrad` 맵 컴파일
- Minecraft `resource pack` / texture atlas

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Pseudo-code 예제** (의존성 기반 incremental cook):
```kotlin
data class Asset(val path: String, val deps: List<String>, val mtime: Long)

class AssetPipeline(private val sourceDir: String, private val cookedDir: String) {
    private val cache = mutableMapOf<String, Long>()  // path -> last cook mtime

    fun cookAll(assets: List<Asset>) {
        // 의존성 순서로 정렬 (위상정렬)
        val order = topologicalSort(assets)
        for (asset in order) {
            if (needsRecook(asset, assets)) {
                cookOne(asset)
                cache[asset.path] = System.currentTimeMillis()
            }
        }
    }

    private fun needsRecook(asset: Asset, all: List<Asset>): Boolean {
        val lastCook = cache[asset.path] ?: return true
        if (asset.mtime > lastCook) return true
        // 의존성 중 하나라도 더 최근에 변경되었으면 재쿡
        return asset.deps.any { dep ->
            val depAsset = all.find { it.path == dep } ?: return@any false
            depAsset.mtime > lastCook
        }
    }

    private fun cookOne(asset: Asset) {
        when (asset.path.substringAfterLast('.')) {
            "png", "tga" -> compressTexture(asset)   // BC7 / ASTC
            "fbx", "obj" -> processMesh(asset)        // optimize + LOD
            "wav" -> encodeAudio(asset)               // Vorbis / ADPCM
        }
    }

    private fun topologicalSort(assets: List<Asset>): List<Asset> = TODO()
    private fun compressTexture(a: Asset) {}
    private fun processMesh(a: Asset) {}
    private fun encodeAudio(a: Asset) {}
}
```

**관련 패턴**: [Multi-Tier Cache](caching.md), [Dependency Injection](structural.md), [Versioned save](#11-save-system), [Streaming](deployment.md)

---

## 카탈로그 요약

| # | 패턴 | 목적 | 난이도 | 사용 빈도 |
|---|------|------|--------|-----------|
| 1 | [Game Loop](#1-game-loop) | 입력·갱신·렌더 반복 + 시간 안정화 | 낮음 | ★★★★★ |
| 2 | [ECS](#2-ecs) | 데이터 지향 entity 시스템 | 높음 | ★★★★☆ |
| 3 | [Component Pattern](#3-component-pattern) | OOP 기반 component 조합 | 중간 | ★★★★★ |
| 4 | [Object Pool](#4-object-pool-game) | GC 회피용 객체 재사용 | 낮음 | ★★★★★ |
| 5 | [Spatial Partition](#5-spatial-partition) | 충돌·근접 검색 O(N²)→O(N log N) | 중간~높음 | ★★★★☆ |
| 6 | [Scene Graph](#6-scene-graph) | 부모-자식 변환 상속 트리 | 중간 | ★★★★★ |
| 7 | [AI State Machine](#7-ai-state-machine) | NPC 행동 모델링 (FSM/BT/GOAP) | 중간~높음 | ★★★★★ |
| 8 | [Dirty Flag](#8-dirty-flag) | 변경분만 재계산 | 낮음 | ★★★★★ |
| 9 | [Double Buffer](#9-double-buffer-game) | 읽기/쓰기 버퍼 분리 | 중간 | ★★★★★ |
| 10 | [Netcode](#10-netcode) | 멀티플레이어 동기화 | 매우 높음 | ★★★★☆ |
| 11 | [Save System](#11-save-system) | 직렬화 + 버전 호환 | 중간~높음 | ★★★★★ |
| 12 | [Asset Pipeline](#12-asset-pipeline) | source→cooked 변환 자동화 | 높음 | ★★★★★ |

## 함께 보기

- [`../algorithms/game-ai.md`](../algorithms/game-ai.md) — Minimax / Alpha-Beta / MCTS / GA / SA
- [behavioral.md](behavioral.md) — State / Strategy / Observer (게임 AI 기반)
- [concurrency.md](concurrency.md) — Job System / Fork-Join (병렬 시뮬레이션)
- [caching.md](caching.md) — Multi-Tier Cache (에셋 캐시 기반)
- [data-access.md](data-access.md) — Snapshot / CQRS (네트워크 / 저장 기반)
- [creational.md](creational.md) — Object Pool 의 일반 형태
- [structural.md](structural.md) — Flyweight (메시·텍스처 공유), Composite (Scene Graph 기반)
