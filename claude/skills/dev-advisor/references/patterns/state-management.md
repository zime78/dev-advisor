# 상태 관리 패턴 (State Management Patterns)

UI/앱 상태 관리 9 모델. Flux/Redux 류는 [`architectural.md`](architectural.md#7-flux--redux) 에 본체가 있고, 본 파일은 **계열별 분류** + **Atomic / Signal / Server State / CRDT-collab** 같은 현대 패턴.

**분류축**:
- **Scope**: Local component / Feature scope / Global app
- **Granularity**: Single store / Multiple slices / Atomic / Signal primitive
- **Source**: Client-owned / Server-owned (Server State) / URL-owned / Shared (CRDT)
- **Reactivity Model**: Push (Redux subscribe) / Pull (Signal getter) / Hybrid

**관련 카탈로그**:
- [architectural.md](architectural.md) — Flux/Redux, MVVM (본체)
- [`../algorithms/distributed.md`](../algorithms/distributed.md) — CRDT 변종 (G/PN/OR/LWW)
- [api-design.md](api-design.md) — Server State 와 API 호출 패턴

---

## 1. Single Store <a id="single-store"></a>

**목적**: 애플리케이션의 모든 상태를 단일 글로벌 Store에 보관하고, Action → Reducer → State 의 단방향 흐름으로만 갱신하여 예측 가능성을 극대화합니다.

**메커니즘**:
- 단일 Store 트리(`{ user, cart, ui, ... }`)에 전체 상태 직렬화
- Action 객체(`{ type, payload }`) 발행 → Reducer 순수 함수 → 새 State 반환
- View는 Store 구독(subscribe) → State 변경 시 push 알림
- Immer / structural sharing 으로 불변 객체 효율적 생성
- Middleware 체인(thunk / saga / epic / RTK Query)으로 비동기·부수효과 처리

**장점**:
- 단일 source of truth → 디버깅·로깅 단순
- Time-travel 디버깅, Action 시퀀스 재생으로 버그 재현 가능
- Hot reload 와 Redux DevTools 강력
- 다중 컴포넌트 상태 공유가 직관적

**단점**:
- 작은 변경에도 Action/Reducer/Selector 보일러플레이트
- 비동기 처리는 별도 미들웨어 (Thunk, Saga, Epic) 필요
- 전체 트리 구독 시 불필요한 재렌더 — Selector 최적화 필수
- 상태가 비대해지면 Reducer 분할/메모이제이션 비용 증가

**대표 라이브러리**: Redux Toolkit (RTK), NgRx, Vuex, Pinia(레거시 옵션), Re-frame(ClojureScript)

**재렌더 최소화 전략**:
- `useSelector(state => state.user.name)` 처럼 슬라이스만 구독 — 참조 동일성 비교(`===`)로 skip
- `reselect` / `createSelector` 메모이제이션으로 파생 상태 캐싱
- `shallowEqual` 비교 함수 명시 (얕은 객체 동등성)

**TypeScript 예제 (Redux Toolkit)**:
```typescript
import { createSlice, configureStore, PayloadAction } from '@reduxjs/toolkit';

interface CartState { items: string[]; total: number }
const initialState: CartState = { items: [], total: 0 };

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    addItem(state, action: PayloadAction<{ id: string; price: number }>) {
      state.items.push(action.payload.id);
      state.total += action.payload.price;
    },
  },
});

export const { addItem } = cartSlice.actions;
export const store = configureStore({ reducer: { cart: cartSlice.reducer } });
export type RootState = ReturnType<typeof store.getState>;

// View
// const total = useSelector((s: RootState) => s.cart.total);  // 슬라이스만 구독
// dispatch(addItem({ id: 'A1', price: 1200 }));
```

**관련 패턴**: [Flux/Redux](architectural.md#7-flux--redux), [MVI](architectural.md#4-mvi-model-view-intent), [feature-slice-store](#feature-slice-store)

---

## 2. Feature Slice / Multiple Store <a id="feature-slice-store"></a>

**목적**: 단일 글로벌 Store 대신 feature(도메인) 단위로 작은 store들을 분리하여, 각 feature가 자기 상태만 소유하고 lazy-load 가능한 모듈성을 확보합니다.

**메커니즘**:
- feature마다 독립 store 인스턴스(`useAuthStore` / `useCartStore` / `useUiStore`)
- 컴포넌트는 필요한 store hook만 import → 트리 셰이킹 가능
- store 간 의존이 필요하면 명시적 참조 또는 이벤트 버스로 결합
- selector 함수를 store 내부에 동봉 (`(s) => s.count`)
- React 18 `useSyncExternalStore` 위에 구현되어 concurrent 모드 안전

**장점**:
- 코드 분할(code-splitting) 친화적 — feature 단위로 lazy import
- 보일러플레이트 최소 (Redux의 1/5 수준)
- 학습 곡선 낮음 — `set` / `get` API만 알면 됨
- 글로벌 액션 디스패치 없이 직접 메서드 호출

**단점**:
- Time-travel 디버깅·전역 액션 로그가 약함 (devtools 플러그인 의존)
- store 간 cross-cutting 동기화는 수동
- 미들웨어 생태계가 Redux보다 얕음
- 다수 store가 생기면 컴포지션이 복잡

**대표 라이브러리**: Zustand (React), Pinia (Vue 3), Riverpod scoped providers (Flutter), Valtio, MobX-state-tree

**재렌더 최소화 전략**:
- selector 두 번째 인자로 equality function 전달 (`(a, b) => a.id === b.id`)
- `useStore.subscribe(selector, listener, { equalityFn })` 로 React 외부 subscription
- 객체 분해 시 shallow 비교 helper 사용 (`shallow` from zustand/shallow)

**TypeScript 예제 (Zustand)**:
```typescript
import { create } from 'zustand';
import { shallow } from 'zustand/shallow';

interface CartState {
  items: string[];
  total: number;
  add: (id: string, price: number) => void;
}

export const useCartStore = create<CartState>((set) => ({
  items: [],
  total: 0,
  add: (id, price) =>
    set((s) => ({ items: [...s.items, id], total: s.total + price })),
}));

// View — total만 구독 (items 변경에는 재렌더 안 됨)
// const total = useCartStore((s) => s.total);
// const { items, add } = useCartStore((s) => ({ items: s.items, add: s.add }), shallow);
```

**관련 패턴**: [single-store](#single-store), [atomic-state](#atomic-state), [DDD Bounded Context](ddd-tactical.md)

---

## 3. Atomic State <a id="atomic-state"></a>

**목적**: 상태를 최소 단위인 atom으로 쪼개고, atom 간 의존성 그래프를 자동 추적하여 변경된 atom 을 구독하는 컴포넌트만 fine-grained 하게 재렌더링합니다.

**메커니즘**:
- atom = `(key, default)` primitive — 단일 값을 보관
- derived atom (selector) 은 다른 atom 을 읽어 파생 값을 계산 → DAG 형성
- atom 변경 시 dependency graph 를 따라 영향받는 derived atom 만 무효화
- 컴포넌트는 `useAtom(myAtom)` 으로 구독 → 해당 atom 변경에만 재렌더
- `atomFamily` / `atomWithStorage` 등으로 동적 생성·영속화
- React Suspense 자연 통합 (atom 자체가 promise 보유 가능)

**장점**:
- 매우 작은 재렌더 단위 — global store 보다 효율적
- bottom-up 설계 — 작은 atom 부터 시작해 조합
- code-splitting 친화 (atom 정의가 모듈 단위)
- 보일러플레이트 거의 없음

**단점**:
- atom 이 산재하면 전역 흐름 파악 어려움 — 도메인 그루핑 규칙 필요
- devtools 가 Redux 대비 약함
- Atom-Family 키 관리(garbage collection) 수동
- selector 의존 그래프가 복잡해지면 추적 곤란

**대표 라이브러리**: Jotai (React, Daishi Kato), Recoil (Meta, 유지보수 축소), Riverpod providers (Flutter), Nanostores (framework-agnostic)

**재렌더 최소화 전략**:
- atom 을 가능한 작게 정의 — `firstNameAtom` + `lastNameAtom` 이 `userAtom` 보다 효율적
- `selectAtom(userAtom, u => u.name)` 으로 슬라이스 구독 + equality 옵션
- `useAtomValue` / `useSetAtom` 분리 — write-only 컴포넌트는 read 구독 안 함

**TypeScript 예제 (Jotai)**:
```typescript
import { atom, useAtom, useAtomValue } from 'jotai';

export const countAtom = atom(0);
export const nameAtom = atom('Anon');

// derived atom — countAtom 만 의존
export const doubleAtom = atom((get) => get(countAtom) * 2);

// derived async atom
export const userAtom = atom(async (get) => {
  const id = get(countAtom);
  const res = await fetch(`/api/users/${id}`);
  return res.json() as Promise<{ name: string }>;
});

// View
// const [count, setCount] = useAtom(countAtom);
// const double = useAtomValue(doubleAtom);   // countAtom 변경 시에만 재렌더
// nameAtom 변경에는 영향 없음
```

**관련 패턴**: [signal-based](#signal-based), [feature-slice-store](#feature-slice-store), [Observer](behavioral.md)

---

## 4. Signal-Based <a id="signal-based"></a>

**목적**: 반응형 primitive(Signal)를 변수처럼 다루어, 런타임이 자동으로 의존성을 추적·구독하고 virtual DOM 없이 정확한 DOM 노드만 갱신합니다.

**메커니즘**:
- `signal(initial)` 으로 reactive primitive 생성 → `count()` getter / `count.set(x)` setter
- effect / computed 가 실행될 때 호출된 signal 의 getter 를 dependency 로 자동 등록 (push-pull hybrid)
- signal 변경 → 의존한 effect 만 dirty 표시 → 다음 microtask 에 batched flush
- React 의 reconciliation·VDOM 비용 없이 직접 DOM 노드 patch (Solid·Svelte)
- React 진영도 React Compiler / `useSyncExternalStore` 기반으로 도입 진행

**장점**:
- 컴포넌트 재실행 없이 DOM 일부만 갱신 → 최상위 성능
- `dep array` 같은 수동 의존성 선언 불필요
- 작은 컴포넌트는 1회만 실행됨 (mount 시) — JSX 가 reactive 그래프
- VDOM diff 비용 0

**단점**:
- 멘탈 모델 전환 비용 — `count` 가 아닌 `count()` 호출 (React 와 다름)
- Solid·Svelte·Vue 와 React 간 API 차이로 라이브러리 호환성 분단
- Signal 을 컴포넌트 prop 으로 넘길 때 `() => signal()` 래핑 필요
- React strict mode / concurrent 와의 통합이 아직 정착 단계

**대표 라이브러리**: SolidJS `createSignal`, Vue 3 `ref` / `reactive`, Angular Signals (v17+), Preact Signals, Svelte 5 runes, S.js (선조)

**재렌더 최소화 전략**:
- 컴포넌트는 mount 시 1회 실행 — JSX 내부의 `count()` 호출 지점만 갱신
- `untrack(() => fn())` 으로 특정 호출을 dependency 추적에서 제외
- `batch(() => { a.set(1); b.set(2); })` 로 여러 변경을 단일 flush 로 묶음

**TypeScript 예제 (SolidJS)**:
```typescript
import { createSignal, createEffect, createMemo } from 'solid-js';

function Counter() {
  const [count, setCount] = createSignal(0);
  const [name, setName] = createSignal('Anon');

  // computed — count 만 dependency 로 추적
  const doubled = createMemo(() => count() * 2);

  // effect — name 변경 시에만 로그
  createEffect(() => console.log('name changed:', name()));

  return (
    <button onClick={() => setCount(count() + 1)}>
      {/* {count()} 호출 지점만 patch */}
      count={count()} doubled={doubled()}
    </button>
  );
}
```

**관련 패턴**: [atomic-state](#atomic-state), [Observer](behavioral.md), MVVM ([architectural.md](architectural.md#3-mvvm-model-view-viewmodel))

---

## 5. Server State <a id="server-state"></a>

**목적**: 서버 소유 데이터(`loading` / `error` / `data` / `stale`)를 클라이언트 상태와 명확히 분리하여, 캐시·revalidation·refetch·optimistic update 를 라이브러리에 위임합니다.

**메커니즘**:
- 쿼리 키(`['users', userId]`)로 캐시 엔트리를 식별
- `staleTime` 경과 전 → 캐시 hit, 경과 후 → 백그라운드 refetch (stale-while-revalidate)
- 윈도우 포커스 / 네트워크 재연결 / interval 트리거로 자동 invalidation
- mutation 후 `queryClient.invalidateQueries(['users'])` 로 관련 쿼리 무효화
- Suspense / Error boundary 통합 — `useSuspenseQuery`
- Optimistic update 와 rollback 내장

**장점**:
- "데이터를 어디에 둘 것인가" 결정 비용 제거 — 항상 쿼리 캐시
- 중복 요청 자동 제거 (in-flight deduplication)
- 멀티 탭 동기화, offline-first, polling 등을 선언적으로 처리
- 클라이언트 store(Redux 등)에서 서버 데이터 분리 → 코드 단순화

**단점**:
- 클라이언트 전용 상태(UI 토글, 폼)에는 부적합 — 별도 store 필요
- 캐시 키 설계 미스 시 stale 데이터 누수
- 복잡한 mutation 시 invalidation 그래프 관리 비용
- SSR / hydration 설정이 까다로움

**대표 라이브러리**: TanStack Query (React/Vue/Solid/Svelte), SWR (Vercel), Apollo Client (GraphQL), Relay, RTK Query, urql

**재렌더 최소화 전략**:
- `select: data => data.name` 옵션으로 슬라이스만 구독
- `notifyOnChangeProps: ['data']` 로 특정 prop 변경에만 재렌더
- 쿼리 키 직렬화 안정성 보장 (객체 순서 고정)

**TypeScript 예제 (TanStack Query)**:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface User { id: string; name: string }

function useUser(id: string) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: async (): Promise<User> => (await fetch(`/api/users/${id}`)).json(),
    staleTime: 60_000,   // 1분간 fresh
    select: (data) => ({ name: data.name }),  // 슬라이스 구독
  });
}

function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (u: User) => fetch(`/api/users/${u.id}`, {
      method: 'PUT', body: JSON.stringify(u),
    }),
    onSuccess: (_, u) => qc.invalidateQueries({ queryKey: ['users', u.id] }),
  });
}
```

**관련 패턴**: [optimistic-update](#optimistic-update), [Cache-Aside](caching.md), [api-design.md](api-design.md)

---

## 6. Form State <a id="form-state"></a>

**목적**: 입력 값·검증·터치 상태·dirty 상태·제출 상태를 폼 트리에 격리하여, 글로벌 상태 오염 없이 입력 라이프사이클 전체를 관리합니다.

**메커니즘**:
- 각 필드의 `value` / `error` / `touched` / `dirty` / `isValidating` 을 추적
- **Controlled** — 모든 keystroke 가 React state 업데이트 (Formik 전통 방식)
- **Uncontrolled** — `ref` 기반으로 DOM 에서 직접 읽음 → 키 입력 시 재렌더 0 (React Hook Form)
- 검증 스키마(Zod / Yup / Joi) 를 resolver 로 연결 → 타입 추론 자동
- 필드 배열(`useFieldArray`) 로 동적 폼 (할 일 리스트 등)
- 제출 시 `handleSubmit(onSubmit)(event)` 가 검증 → onSubmit 호출

**장점**:
- 폼 로직을 컴포넌트 외부로 분리 → 재사용성 높음
- 검증 스키마와 TypeScript 타입을 단일 source 에서 도출
- React Hook Form 은 uncontrolled 로 입력당 재렌더 0 → 대형 폼 성능 우수
- 의존 필드(예: 비밀번호 확인) watcher 가 선언적

**단점**:
- Controlled 방식은 keystroke마다 재렌더 → 큰 폼에서 성능 이슈
- 멀티 스텝 폼은 외부 store 와 통합 필요
- 동적 필드 + 비동기 검증 + 폼 배열 조합은 학습 곡선 가파름
- SSR 초기값 / hydration 처리 주의

**대표 라이브러리**: React Hook Form (uncontrolled 권장), Formik (controlled), vee-validate (Vue), Final Form, TanStack Form, VeeValidate, FormKit

**재렌더 최소화 전략**:
- React Hook Form 의 `register` 는 ref 기반 — 입력 시 컴포넌트 재렌더 0
- `useWatch({ name: 'email' })` 로 특정 필드만 구독
- `formState` 는 proxy → 접근한 속성에만 구독 등록

**TypeScript 예제 (React Hook Form + Zod)**:
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});
type FormValues = z.infer<typeof schema>;

function LoginForm() {
  const { register, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  const onSubmit = (data: FormValues) => console.log(data);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {formState.errors.email && <span>{formState.errors.email.message}</span>}
      <input type="password" {...register('password')} />
      <button disabled={!formState.isValid}>Submit</button>
    </form>
  );
}
```

**관련 패턴**: [atomic-state](#atomic-state), [server-state](#server-state), Validation ([behavioral.md](behavioral.md))

---

## 7. URL / Routing State <a id="url-routing-state"></a>

**목적**: 공유·복원·새로고침 가능해야 하는 상태(검색어, 필터, 페이지, 탭 인덱스, 정렬)를 URL 자체에 보관하여 브라우저 히스토리·뒤로가기·딥링크를 무료로 얻습니다.

**메커니즘**:
- 경로 segment (`/users/:id`) → path param
- query string (`?q=foo&page=2`) → search param
- hash (`#section-1`) → 클라이언트 전용 스크롤·UI 상태
- 라우터가 URL 파싱 → typed param 객체 제공
- 컴포넌트는 `useSearchParams()` 로 read·write, navigation 으로 history 갱신
- TanStack Router / Remix / Next.js App Router 는 search param 스키마 검증 내장

**장점**:
- URL 복사·공유 → 동일 화면 복원
- 브라우저 뒤로가기·새로고침이 상태 보존
- SSR / SEO 친화 — 서버가 URL 만 보고 페이지 렌더
- 클라이언트 store 가 비대해지지 않음
- 분석(GA, mixpanel) 도구가 URL 만 추적해도 사용자 흐름 파악

**단점**:
- URL 길이 제한 (브라우저별 ~2KB) — 대형 상태 부적합
- 직렬화 가능한 primitive 타입만 보관 가능
- 검증 누락 시 URL 조작으로 invalid state 진입
- 자주 변경되는 상태(드래그·실시간 슬라이더) 는 부적합

**대표 라이브러리**: React Router v6+, TanStack Router (typed search params), Remix, Next.js App Router, Vue Router, SvelteKit, nuqs (React URL state hook), Nanostores `@nanostores/router`

**재렌더 최소화 전략**:
- search param 의 selector 옵션 사용 (`useSearch({ select: s => s.page })`)
- 빈번한 갱신은 `replace: true` 로 history 오염 방지
- URL ↔ store 동기화 시 단방향 binding 으로 루프 회피

**TypeScript 예제 (TanStack Router)**:
```typescript
import { createFileRoute, useSearch } from '@tanstack/react-router';
import { z } from 'zod';

const searchSchema = z.object({
  page: z.number().int().min(1).default(1),
  q: z.string().default(''),
  sort: z.enum(['asc', 'desc']).default('asc'),
});

export const Route = createFileRoute('/users')({
  validateSearch: searchSchema.parse,
  component: UserList,
});

function UserList() {
  const { page, q, sort } = useSearch({ from: '/users' });
  // URL 만 변경하면 컴포넌트 자동 갱신
  // navigate({ search: (prev) => ({ ...prev, page: prev.page + 1 }) });
  return <div>page={page} q={q} sort={sort}</div>;
}
```

**관련 패턴**: [server-state](#server-state), [feature-slice-store](#feature-slice-store)

---

## 8. CRDT-based Collaborative State <a id="crdt-collab-state"></a>

**목적**: 여러 사용자가 동시에 같은 문서를 편집할 때, 중앙 락이나 OT(Operational Transformation) 서버 없이 각 클라이언트의 변경을 자동으로 병합하여 eventual consistency 를 보장합니다.

**메커니즘**:
- CRDT 자료구조(Yjs `Y.Doc`, Automerge `Doc<T>`) 가 모든 변경을 causal 메타데이터(`lamport clock` / `vector clock`)와 함께 기록
- 변경분(update binary)을 WebSocket / WebRTC / Sync server 로 전파
- 각 피어가 받은 update 를 자기 doc 에 merge → **순서·중복 무관**하게 동일 상태로 수렴
- 텍스트(Y.Text), 맵(Y.Map), 배열(Y.Array), Rich text(ProseMirror binding) 등 타입별 CRDT
- offline 편집 후 재연결 시에도 충돌 없이 자동 병합
- Awareness (커서·선택 영역·presence) 는 별도 ephemeral 채널

**장점**:
- 중앙 서버 없이도 P2P 협업 가능 (WebRTC)
- offline-first — 네트워크 단절에 강건
- 충돌 해결 알고리즘이 자료구조 자체에 내장 → 애플리케이션 코드 단순
- 무한 undo / redo 가 자연스럽게 구현됨
- 다중 디바이스 동기화 (한 사용자의 폰 + 노트북)

**단점**:
- 메타데이터 오버헤드 — update 마다 vector clock 누적 (가비지 컬렉션 필요)
- 도메인 불변식(예: 잔액 > 0) 강제 어려움 — eventual 이므로
- 디버깅 난이도 높음 (causal history 추적)
- 텍스트 외 자료구조는 라이브러리 지원 격차
- 보안 — 클라이언트가 임의 update 발행 가능, ACL 별도 설계 필요

**대표 라이브러리**: Yjs (Kevin Jahns), Automerge (Martin Kleppmann 연구실), Liveblocks (서비스), Replicache, ElectricSQL, Loro, PartyKit

**재렌더 최소화 전략**:
- Y.Doc observe 콜백을 필요한 sub-doc(`yMap.observe`) 에만 등록
- 변경 batch — `doc.transact(() => { ... })` 로 다중 변경을 단일 update 로 전파
- React binding (`y-react`) 의 selector 활용

**TypeScript 예제 (Yjs)**:
```typescript
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';

const doc = new Y.Doc();
const provider = new WebsocketProvider('wss://demo.yjs.dev', 'my-room', doc);

const yMap = doc.getMap<string>('user');
const yText = doc.getText('content');

// 변경 감지 — 어느 피어가 변경했든 동일하게 호출됨
yMap.observe((event) => {
  event.changes.keys.forEach((change, key) => {
    console.log(`${key} -> ${yMap.get(key)} (${change.action})`);
  });
});

// 다중 변경을 단일 update 로 묶음
doc.transact(() => {
  yMap.set('name', 'Alice');
  yText.insert(0, 'Hello');
});

// awareness (커서 위치 등 ephemeral state)
provider.awareness.setLocalStateField('cursor', { x: 100, y: 200 });
```

**관련 패턴**: [Optimistic-update](#optimistic-update), [CRDT 변종 (G/PN/OR/LWW)](../algorithms/distributed.md), [Event Sourcing](architectural.md#15-event-driven-architecture)

---

## 9. Optimistic UI Update <a id="optimistic-update"></a>

**목적**: 서버 응답을 기다리지 않고 사용자 액션을 즉시 UI 에 반영하여 체감 속도를 극대화하고, 실패 시 자동 rollback 으로 정합성을 보장합니다.

**메커니즘**:
- 사용자 액션 → 클라이언트에서 예상 결과를 즉시 캐시·store 에 반영
- 동시에 mutation 요청을 서버로 전송 (`fetch` / GraphQL mutation)
- 성공 시 → 서버 응답으로 캐시 갱신 (서버가 권위적 truth)
- 실패 시 → 이전 snapshot 복원 (rollback) + 사용자에게 에러 토스트
- mutation queue / retry — 네트워크 단절 시 큐에 적재 후 재연결 시 flush
- React Query / SWR / Apollo 모두 `onMutate` / `onError` 훅으로 표준화

**장점**:
- 200~500ms 네트워크 지연을 사용자가 느끼지 않음
- "좋아요" / "북마크" / "체크박스" 등 빈번한 액션의 UX 향상
- offline-first 앱에서 필수 — 큐 + retry 와 자연스러운 조합
- React Query / Apollo 와 함께 쓰면 boilerplate 최소

**단점**:
- 실패 시 rollback 로직 누락하면 stale UI / 데이터 불일치
- 도메인 불변식(예: 재고 부족) 위반은 서버만 알 수 있음 → 사용자 혼란
- 동시 mutation 의 순서 보장 어려움 — race condition 위험
- 사용자에게 "실패" 토스트 노출 빈도가 높으면 UX 손상
- 결제·송금 등 중요 액션은 부적합 — 명시적 confirmation 필요

**대표 라이브러리**: TanStack Query (`onMutate` + context), Apollo Client (optimisticResponse), SWR (mutate optimisticData), Redux Toolkit Query (optimistic updates), Replicache, Linear (자체 sync engine)

**재렌더 최소화 전략**:
- 캐시 update 시 reference 가 변경된 슬라이스만 invalidate
- `setQueryData(key, updater)` 로 in-place 갱신 — 전체 refetch 회피
- rollback 시 snapshot 을 closure 로 보관 (메모리 누수 주의)

**TypeScript 예제 (TanStack Query optimistic mutation)**:
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface Todo { id: string; text: string; done: boolean }

function useToggleTodo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      fetch(`/api/todos/${id}/toggle`, { method: 'POST' }),

    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ['todos'] });
      const prev = qc.getQueryData<Todo[]>(['todos']);     // snapshot
      qc.setQueryData<Todo[]>(['todos'], (old) =>
        old?.map((t) => (t.id === id ? { ...t, done: !t.done } : t)),
      );                                                    // 즉시 반영
      return { prev };                                      // context
    },

    onError: (_err, _id, ctx) => {
      qc.setQueryData(['todos'], ctx?.prev);                // rollback
    },

    onSettled: () => qc.invalidateQueries({ queryKey: ['todos'] }),
  });
}
```

**관련 패턴**: [server-state](#server-state), [crdt-collab-state](#crdt-collab-state), [Retry / Circuit Breaker](reliability.md)
