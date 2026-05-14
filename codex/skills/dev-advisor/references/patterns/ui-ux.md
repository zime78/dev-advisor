# UI/UX 패턴 (UI/UX Patterns)

프론트엔드·앱 UI/UX 의 정평 있는 11 패턴. 컴포넌트 설계 (Atomic Design / Compound) + 로딩/오류 상태 (Skeleton / Empty State) + i18n / a11y 표준.

**원전·표준 참고**:
- Brad Frost — *Atomic Design* (https://atomicdesign.bradfrost.com/, 2013)
- Dan Abramov — "Presentational and Container Components" (2015, blog)
- Jakob Nielsen — *10 Usability Heuristics* (Nielsen Norman Group)
- WCAG 2.2 (W3C Recommendation, 2023) — Accessibility
- ICU MessageFormat (Unicode standard)
- Material Design (Google), Apple Human Interface Guidelines
- Radix UI / Headless UI (compound components)
- Style Dictionary (Amazon), Tokens Studio for Figma
- Web.dev / web Vitals (Google) — Loading UX

**관련 카탈로그**:
- [web-rendering.md](web-rendering.md) — SSR/SSG/Islands (렌더링 전략)
- [state-management.md](state-management.md) — Optimistic Update / Server State
- [mobile-app.md](mobile-app.md) — 모바일 UI 운영 (Pull-to-Refresh 등)
- [crossplatform.md](crossplatform.md) — Flutter / RN UI 패턴
- [architectural.md](architectural.md) — MVC / MVVM / MVI (UI 아키텍처 본체)

---

## 1. Atomic Design

<a id="atomic-design"></a>

**목적**: Brad Frost 가 2013 년 제안한 컴포넌트 라이브러리 설계 방법론. UI 를 화학의 원자→분자→유기체→템플릿→페이지 5 단계로 분해하여, **재사용 가능한 최소 단위에서 화면을 합성**하는 모듈형 컴포넌트 시스템을 구축합니다.

**메커니즘 (5 단계 위계)**:

```
┌──────────────────────────────────────────────────────────────┐
│  Atoms        ─ Button, Input, Label, Icon, Color, Font      │ 더 이상 쪼갤 수 없는 최소 단위
│      ↓                                                       │
│  Molecules    ─ SearchForm (Label + Input + Button)          │ 의미 있는 기능 단위로 결합
│      ↓                                                       │
│  Organisms    ─ Header (Logo + Nav + SearchForm)             │ 페이지의 한 섹션을 구성
│      ↓                                                       │
│  Templates    ─ HomePageTemplate (Header + Body + Footer)    │ 레이아웃 + placeholder
│      ↓                                                       │
│  Pages        ─ HomePage (Template + 실제 데이터)            │ 사용자가 보는 최종 화면
└──────────────────────────────────────────────────────────────┘
```

- **Atoms**: HTML 태그·CSS 변수 수준의 최소 단위. 자체로는 거의 쓸모 없지만 모든 것의 빌딩 블록
- **Molecules**: Atoms 의 단순 조합. 단일 책임 원칙(SRP) 준수
- **Organisms**: Molecules + Atoms 의 복합. 도메인 의미 보유 (Header, ProductCard)
- **Templates**: 와이어프레임 수준의 페이지 레이아웃. 데이터 placeholder 만 존재
- **Pages**: Template 에 실제 데이터를 주입. 콘텐츠 다양성 검증

**장점**:
- 컴포넌트 재사용성 극대화 — Atom 한 번 만들면 모든 곳에서 활용
- 디자인 시스템과 자연스럽게 매핑 (Storybook / Figma 라이브러리)
- 점진적 합성 가능 — Atom 부터 차근차근 빌드
- 디자이너·개발자 공통 언어 (atom 단위 변경 영향 추적)
- 변경 격리 — Atom 수정이 모든 화면에 자동 반영

**단점**:
- 5 단계 분류 자체가 주관적 — "이건 Molecule 인가 Organism 인가" 논쟁
- Atom·Molecule 폭증으로 폴더 구조 복잡 (100+ 컴포넌트)
- 모든 UI 를 5 단계에 강제 매핑하면 오버엔지니어링
- 페이지 고유 일회성 UI 를 위해 Atom 부터 만드는 비용
- 동적·데이터 의존 컴포넌트가 5 단계 모델에 잘 안 맞음

**활용 예시**:
- 디자인 시스템 구축 (Material UI, Ant Design, Chakra UI 류)
- Storybook 컴포넌트 라이브러리
- 다중 제품 공통 UI 코드베이스
- 디자이너-개발자 협업 어휘 정립

**React/TypeScript 예제**:
```tsx
// atoms/Button.tsx — 최소 단위
interface ButtonProps {
  variant: 'primary' | 'secondary';
  onClick: () => void;
  children: React.ReactNode;
}
export const Button = ({ variant, onClick, children }: ButtonProps) => (
  <button className={`btn btn-${variant}`} onClick={onClick}>
    {children}
  </button>
);

// atoms/Input.tsx
export const Input = ({ value, onChange, placeholder }: InputProps) => (
  <input className="input" value={value} onChange={(e) => onChange(e.target.value)}
         placeholder={placeholder} />
);

// molecules/SearchForm.tsx — Atom 의 조합
export const SearchForm = ({ onSearch }: { onSearch: (q: string) => void }) => {
  const [query, setQuery] = useState('');
  return (
    <div className="search-form">
      <Input value={query} onChange={setQuery} placeholder="검색어 입력" />
      <Button variant="primary" onClick={() => onSearch(query)}>검색</Button>
    </div>
  );
};

// organisms/Header.tsx — Molecule + Atom 의 복합
export const Header = ({ onSearch }: HeaderProps) => (
  <header className="site-header">
    <Logo />
    <Navigation links={NAV_LINKS} />
    <SearchForm onSearch={onSearch} />
  </header>
);

// pages/HomePage.tsx — Template 에 실데이터 주입
export const HomePage = () => (
  <PageTemplate header={<Header onSearch={handleSearch} />} body={<ProductGrid />} />
);
```

**관련 패턴**: [Compound Components](#compound-components), [Design Tokens](#design-tokens), [Container/Presenter](#container-presenter)

---

## 2. Container / Presenter (Smart / Dumb)

<a id="container-presenter"></a>

**목적**: Dan Abramov 가 2015 년 정립한 React 컴포넌트 분리 패턴. **로직(상태·API·이벤트 처리)**과 **렌더링(JSX·스타일)**을 별도 컴포넌트로 분리하여, 프레젠테이션 컴포넌트의 재사용성과 테스트 용이성을 높입니다. (저자가 2019 년 "Hooks 등장 이후 더 이상 권장하지 않음" 으로 update — 그러나 패턴 자체는 여전히 유효)

**메커니즘**:

```
┌──────────────────────────────────────────────────────────────┐
│  Container (Smart)                                           │
│  ─ useState / useEffect / API 호출 / Redux dispatch           │
│  ─ 로직 책임                                                  │
│       ↓ props 로 데이터·콜백 전달                              │
│  Presenter (Dumb)                                            │
│  ─ props 받아 JSX 만 렌더                                     │
│  ─ 상태·side effect 없음                                      │
│  ─ 순수 함수처럼 동작                                          │
└──────────────────────────────────────────────────────────────┘
```

- **Container**: data fetching, state management, mutation handler. Redux/MobX 와 연결
- **Presenter**: stateless functional component, props in → JSX out, 디자인 시스템에 가까움
- 분리 기준: "이 컴포넌트가 redux store 를 알아야 하는가?" 알아야 하면 Container

**장점**:
- Presenter 는 Storybook 에 격리해서 다양한 props 조합 시각화 쉬움
- 테스트 — Presenter 는 snapshot test, Container 는 mock 으로 로직 테스트
- 재사용 — 동일 Presenter 를 여러 Container 에서 활용 (다른 데이터 소스)
- 디자이너가 Presenter 만 다루기 좋음 (HTML/CSS 변경에 로직 위험 없음)

**단점**:
- 두 파일로 분리하는 보일러플레이트 — 작은 컴포넌트엔 과함
- props drilling — Container → Presenter → 자식 Presenter 로 props 가 깊어짐
- Hooks 시대에는 `useXxx` custom hook 으로 더 간결히 분리 가능
- "어디까지 Container, 어디부터 Presenter" 모호

**활용 예시**:
- Redux/MobX 시대 (~2018) React 프로젝트의 표준 패턴
- 디자인 시스템의 stateless 컴포넌트 라이브러리
- Server-driven UI 의 클라이언트 렌더 레이어
- MVVM 의 View / ViewModel 분리와 동일 사상

**React 예제**:
```tsx
// presenters/UserCard.tsx — Dumb, props 만 받음
interface UserCardProps {
  name: string;
  email: string;
  avatarUrl: string;
  onFollow: () => void;
  isFollowing: boolean;
}
export const UserCard = ({ name, email, avatarUrl, onFollow, isFollowing }: UserCardProps) => (
  <div className="user-card">
    <img src={avatarUrl} alt={name} />
    <h3>{name}</h3>
    <p>{email}</p>
    <button onClick={onFollow}>
      {isFollowing ? '팔로잉' : '팔로우'}
    </button>
  </div>
);

// containers/UserCardContainer.tsx — Smart, 로직 담당
export const UserCardContainer = ({ userId }: { userId: string }) => {
  const { data: user, loading } = useFetchUser(userId);
  const [isFollowing, setIsFollowing] = useState(false);
  const followMutation = useFollowMutation();

  if (loading || !user) return <Skeleton />;

  const handleFollow = async () => {
    await followMutation.mutate(userId);
    setIsFollowing(true);
  };

  return (
    <UserCard
      name={user.name}
      email={user.email}
      avatarUrl={user.avatarUrl}
      onFollow={handleFollow}
      isFollowing={isFollowing}
    />
  );
};

// Hooks 시대 등가 패턴 — 같은 분리, 더 간결
function useUserCardLogic(userId: string) {
  const { data: user, loading } = useFetchUser(userId);
  const [isFollowing, setIsFollowing] = useState(false);
  return { user, loading, isFollowing, handleFollow: () => setIsFollowing(true) };
}
```

**관련 패턴**: [MVVM](architectural.md), [Atomic Design](#atomic-design), [Compound Components](#compound-components), [Hooks 패턴](state-management.md)

---

## 3. Skeleton Screen / Shimmer

<a id="skeleton-shimmer"></a>

**목적**: 데이터 로딩 중 회색 박스로 **레이아웃의 골격(skeleton)**을 미리 보여주어, 사용자가 "곧 콘텐츠가 나타날 것"임을 인지하게 합니다. Spinner 대비 체감 로딩 시간 단축. Facebook 이 2013 년경 도입, 이후 LinkedIn / YouTube / Slack 표준화.

**메커니즘**:
- 실제 콘텐츠와 동일한 크기·위치의 회색 placeholder 박스 렌더
- **Shimmer 효과**: gradient 가 좌→우로 이동하는 CSS 애니메이션 (살아 있음을 표현)
- 데이터 도착 시 skeleton → 실제 콘텐츠로 swap (fade transition 권장)
- Layout shift 방지 — skeleton 크기가 실제 콘텐츠와 같아야 함 (CLS 0)

**Loading UX 4 단계**:
1. **No feedback** — 최악 (사용자는 멈춘 줄 앎)
2. **Spinner** — 보통 (시간 인지 부담 큼, 페이지 빈 상태 그대로)
3. **Skeleton** — 좋음 (레이아웃 미리 제공, 인지 부담 감소)
4. **Progressive content** — 최선 (서버 streaming, 데이터 도착 순서대로 표시)

**장점**:
- 체감 로딩 시간 30-40% 단축 (실제 시간은 동일)
- Layout shift 없음 (CLS 점수 개선)
- 사용자가 "어떤 UI 가 나올지" 미리 예상
- Spinner 처럼 시간 인지에 집중되지 않음

**단점**:
- 모든 화면에 skeleton 컴포넌트 별도 구현 비용
- 실제 콘텐츠와 크기가 다르면 layout shift 발생
- 너무 정교한 skeleton 은 가짜 콘텐츠처럼 보여 혼란
- 200ms 미만 빠른 로딩에는 깜빡임만 발생 → 사용 금지

**활용 예시**:
- 피드 / 리스트 / 카드 그리드 (Facebook, LinkedIn, Twitter)
- 사용자 프로필 카드, 댓글 영역
- 상세 페이지의 이미지·텍스트 영역
- 검색 결과 페이지

**React/CSS 예제**:
```tsx
// SkeletonCard.tsx
import './skeleton.css';

export const SkeletonCard = () => (
  <div className="skeleton-card">
    <div className="skeleton-avatar shimmer" />
    <div className="skeleton-line shimmer" style={{ width: '60%' }} />
    <div className="skeleton-line shimmer" style={{ width: '90%' }} />
    <div className="skeleton-line shimmer" style={{ width: '40%' }} />
  </div>
);

// 사용처
export const UserList = () => {
  const { data, loading } = useFetchUsers();
  if (loading) {
    return (
      <div>
        {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    );
  }
  return <div>{data.map((u) => <UserCard key={u.id} user={u} />)}</div>;
};
```

```css
/* skeleton.css — Shimmer 애니메이션 */
.shimmer {
  background: linear-gradient(
    90deg,
    #e0e0e0 0%,
    #f0f0f0 50%,
    #e0e0e0 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-card {
  padding: 16px;
  border-radius: 8px;
  background: #fff;
}
.skeleton-avatar {
  width: 48px; height: 48px;
  border-radius: 50%;
  margin-bottom: 12px;
}
.skeleton-line {
  height: 12px;
  border-radius: 4px;
  margin-bottom: 8px;
}

/* prefers-reduced-motion 시 애니메이션 제거 */
@media (prefers-reduced-motion: reduce) {
  .shimmer { animation: none; }
}
```

**관련 패턴**: [Empty / Error / Loading State](#empty-error-loading-state), [Optimistic UI](#optimistic-ui-update), [Accessibility](#a11y-wcag)

---

## 4. Optimistic UI Update

<a id="optimistic-ui-update"></a>

**목적**: 사용자 액션(좋아요, 댓글 작성, 삭제)에 대해 서버 응답을 **기다리지 않고 UI 를 즉시 업데이트**합니다. 서버 실패 시 rollback. 네트워크 지연이 있는 환경에서 즉각적인 반응성 제공.

**메커니즘**:
```
사용자 클릭
   │
   ├─→ [1] 로컬 상태 즉시 변경 (UI 반영)
   │
   ├─→ [2] 서버 mutation 요청 (백그라운드)
   │
   ├─→ [3a] 성공: 서버 응답으로 로컬 상태 confirm
   │
   └─→ [3b] 실패: rollback + 에러 토스트
```

- Pessimistic (전통): 서버 응답 후 UI 갱신 → 즉각성 낮음
- Optimistic: UI 먼저 갱신 → 응답 후 confirm/rollback
- Idempotent 한 요청에 적합 (좋아요 토글, 즐겨찾기, 읽음 처리)
- Non-idempotent (결제, 1회성 작업)에는 부적합

**구현 라이브러리**:
- **TanStack Query**: `useMutation` + `onMutate` (낙관적 캐시 갱신) + `onError` (rollback)
- **SWR**: `mutate(key, optimisticData, { revalidate: true })`
- **Redux Toolkit Query**: `updateQueryData` + `try/catch undo`
- **Apollo Client**: `optimisticResponse` 옵션

**장점**:
- 즉각 반응성 — 사용자는 네트워크 지연을 느끼지 못함
- 모바일·저속 네트워크에서 UX 극적 개선
- 액션 연쇄 (좋아요 → 댓글 → 공유) 시 흐름 끊김 없음

**단점**:
- Rollback 로직 복잡 — 실패 시 원상복구 + 에러 메시지
- 사용자가 "성공으로 봤는데 사라짐" → 혼란 가능
- 일관성 문제 — 다른 사용자가 본 상태와 일시적 불일치
- 멱등성 없는 작업(결제·예약)에 적용 시 데이터 불일치

**활용 예시**:
- 좋아요 / 별점 / 즐겨찾기 토글 (Twitter, Instagram, YouTube)
- 댓글 작성 (Facebook, Reddit, Discord)
- 메시지 전송 (WhatsApp, Slack, Telegram)
- TODO 체크박스 (Todoist, Asana, Linear)
- 드래그앤드롭 reorder (Trello, Notion)

**TanStack Query 예제**:
```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface Post { id: string; title: string; likes: number; liked: boolean; }

function useToggleLike() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (postId: string) => {
      const res = await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    // 1. 요청 직전: 즉시 캐시 업데이트
    onMutate: async (postId) => {
      await qc.cancelQueries({ queryKey: ['posts'] });
      const previous = qc.getQueryData<Post[]>(['posts']);
      qc.setQueryData<Post[]>(['posts'], (old) =>
        old?.map((p) => p.id === postId
          ? { ...p, liked: !p.liked, likes: p.liked ? p.likes - 1 : p.likes + 1 }
          : p
        ),
      );
      return { previous }; // rollback 용 context
    },
    // 2. 실패 시: rollback
    onError: (_err, _postId, context) => {
      if (context?.previous) {
        qc.setQueryData(['posts'], context.previous);
      }
      toast.error('좋아요 처리에 실패했어요');
    },
    // 3. 완료 후: 서버 데이터로 재동기화
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['posts'] });
    },
  });
}
```

**관련 패턴**: [Skeleton](#skeleton-shimmer), [Server State](state-management.md), [Retry](reliability.md), [Saga](state-management.md)

---

## 5. Pull-to-Refresh / Infinite Scroll / Pagination UI

<a id="infinite-scroll-pagination-ui"></a>

**목적**: 큰 데이터셋을 표시하는 3 가지 표준 모바일/웹 UI 패턴. **Pull-to-Refresh**(상단 끌어내려 새로고침), **Infinite Scroll**(스크롤 끝에서 자동 로드), **Pagination**(명시적 페이지 번호) 의 트레이드오프를 이해하고 선택합니다.

**3 패턴 비교**:

| 패턴 | 사용자 부담 | 메모리 | SEO | 위치 기억 | 적합 |
|------|----------|-------|-----|---------|------|
| **Pagination** | 클릭 필요 | 낮음 | 강함 | 강함 (URL) | 검색 결과, 어드민 테이블 |
| **Infinite Scroll** | 무한 스크롤 | 높음 | 약함 | 약함 | 피드, 타임라인, 갤러리 |
| **Load More 버튼** | 클릭 + 스크롤 | 중간 | 보통 | 보통 | 적당한 데이터셋, 푸터 접근 필요 |
| **Pull-to-Refresh** | 위로 끌기 | - | - | - | 모바일 피드 갱신 |

**Pull-to-Refresh 메커니즘**:
- 스크롤 위치가 최상단인 상태에서 추가 아래로 스크롤 시도
- Threshold (예: 80px) 초과하면 spinner 표시 + refresh 트리거
- 햅틱 피드백 (iOS Taptic Engine) 으로 임계점 알림
- Apple Mail 이 2008 년 도입한 패턴

**Infinite Scroll 메커니즘**:
- `IntersectionObserver` 로 리스트 끝의 sentinel 요소 가시화 감지
- 가시화 시 다음 페이지 fetch + append
- **가상 스크롤 (Virtualization)** 필수 — DOM 노드 폭증 방지 (react-window, react-virtualized)
- 스크롤 위치 복원: 페이지 이탈 후 복귀 시 이전 스크롤 위치로 복귀

**장점**:
- Pull-to-Refresh: 사용자 의도 명확, 새 콘텐츠 갱신 자연스러움
- Infinite Scroll: 끊김 없는 탐색, 모바일 친화
- Pagination: 위치 기억, 공유 가능 (URL), SEO

**단점**:
- Infinite Scroll: 푸터 접근 어려움, 스크롤 위치 잃기 쉬움, 메모리 누적
- Pagination: 클릭 부담, 모바일 UX 부자연스러움
- Pull-to-Refresh: 데스크톱 부재, 실수 트리거 가능

**활용 예시**:
- Pull-to-Refresh: 모바일 메일·SNS·뉴스 (Mail, Twitter, Instagram)
- Infinite Scroll: SNS 피드, 이미지 갤러리 (Pinterest, Instagram, TikTok)
- Pagination: 검색 결과, 게시판, 어드민 (Google Search, Stack Overflow)
- Hybrid: 5 페이지까지 Infinite + 그 후 Load More 버튼 (Google Image)

**React Infinite Scroll 예제 (IntersectionObserver)**:
```tsx
import { useEffect, useRef, useState } from 'react';

interface Item { id: string; title: string; }

function useInfiniteList() {
  const [items, setItems] = useState<Item[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const loadMore = async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    const res = await fetch(`/api/items?page=${page}&limit=20`);
    const next = await res.json();
    setItems((prev) => [...prev, ...next.items]);
    setHasMore(next.hasMore);
    setPage((p) => p + 1);
    setLoading(false);
  };

  return { items, loadMore, hasMore, loading };
}

export const InfiniteFeed = () => {
  const { items, loadMore, hasMore, loading } = useInfiniteList();
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const obs = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) loadMore();
    }, { rootMargin: '200px' }); // 200px 미리 prefetch

    if (sentinelRef.current) obs.observe(sentinelRef.current);
    return () => obs.disconnect();
  }, [loadMore]);

  return (
    <div>
      {items.map((it) => <ItemCard key={it.id} item={it} />)}
      {hasMore && <div ref={sentinelRef} aria-hidden="true" />}
      {loading && <SkeletonCard />}
      {!hasMore && <p>모든 항목을 다 봤어요</p>}
    </div>
  );
};
```

**Flutter Pull-to-Refresh 예제**:
```dart
class FeedPage extends StatelessWidget {
  Future<void> _onRefresh() async {
    await context.read<FeedViewModel>().refresh();
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _onRefresh,
      child: ListView.builder(
        itemCount: items.length,
        itemBuilder: (_, i) => ItemCard(item: items[i]),
      ),
    );
  }
}
```

**관련 패턴**: [Skeleton](#skeleton-shimmer), [Optimistic UI](#optimistic-ui-update), [Empty State](#empty-error-loading-state), [Pagination Strategies](api-design.md)

---

## 6. Empty State / Error State / Loading State

<a id="empty-error-loading-state"></a>

**목적**: 모든 데이터 표시 화면은 **4 가지 상태** — Loading / Empty / Error / Success — 를 명시적으로 처리해야 합니다. UI 개발 시 흔히 Success 만 디자인하고 나머지 3 가지를 빠뜨려 사용자 혼란 유발.

**4 상태 매트릭스**:

```
┌───────────────────────────────────────────────────────────┐
│              [상태]    →    [UI 표현]                      │
│  ─────────────────────────────────────────────             │
│  Loading             →   Skeleton / Spinner                │
│  Empty (정상 빈)     →   Illustration + 안내 + CTA         │
│  Error (실패)        →   에러 메시지 + Retry 버튼          │
│  Success (데이터)    →   실제 콘텐츠                       │
└───────────────────────────────────────────────────────────┘
```

**각 상태의 디자인 원칙**:

**Loading State**:
- 200ms 미만: 표시 안 함 (깜빡임 방지)
- 200ms ~ 1s: Spinner
- 1s 이상: Skeleton (레이아웃 미리 보여주기)
- 10s 이상: 진행률 표시 + 백그라운드 옵션

**Empty State (Zero State)**:
- 무엇이 비어있는지 명확히 (예: "아직 작성한 게시글이 없어요")
- 다음에 할 행동 안내 (CTA — "첫 게시글 작성하기")
- 일러스트레이션으로 친근한 분위기 (필수 X, 권장)
- 사용자 잘못이 아님을 분명히

**Error State**:
- 사용자가 이해할 수 있는 언어 ("ERR_500" 금지 → "잠시 후 다시 시도해주세요")
- Retry 버튼 제공 (한 클릭 복구)
- 영구 실패와 일시 실패 구분
- 에러 ID/추적 코드는 상세 영역에 (지원 요청용)

**Success State**:
- 명시적 처리 — `data && data.length > 0` 보장
- Loading/Empty/Error 와 자동으로 mutually exclusive

**Nielsen Heuristic 매핑**:
- "Visibility of system status" — Loading 필수
- "Help users recognize, diagnose, recover from errors" — Error retry 필수
- "Match between system and real world" — 친화적 언어

**장점**:
- 4 상태 모두 처리하면 모든 사용자 경로 보장
- 디자이너 핸드오프 명확 (4 화면 모두 디자인)
- 사용자 혼란 감소 (왜 비었는지, 어떻게 복구하는지)
- 에러 발생 시 사용자가 스스로 복구

**단점**:
- 모든 화면에 4 상태 구현 비용
- 상태별 컴포넌트 일관성 유지 어려움
- 에러 메시지 번역 / 일러스트레이션 자산 관리

**활용 예시**:
- 이메일 받은편지함 (Empty: "메일이 없어요" + 메일 작성 CTA)
- 검색 결과 (Empty: "결과가 없어요" + 검색 팁)
- 장바구니 (Empty: 일러스트 + "쇼핑하러 가기")
- 알림 페이지, 친구 목록, 주문 내역

**React 예제 (4 상태 처리)**:
```tsx
type LoadState<T> =
  | { status: 'loading' }
  | { status: 'empty' }
  | { status: 'error'; error: Error }
  | { status: 'success'; data: T };

export const PostList = () => {
  const state = useLoadPosts();

  switch (state.status) {
    case 'loading':
      return <SkeletonList count={5} />;

    case 'empty':
      return (
        <EmptyState
          illustration="/empty-posts.svg"
          title="아직 게시글이 없어요"
          description="첫 게시글을 작성해 보세요"
          ctaText="글쓰기"
          onCta={() => navigate('/new-post')}
        />
      );

    case 'error':
      return (
        <ErrorState
          title="게시글을 불러오지 못했어요"
          description="잠시 후 다시 시도해주세요"
          onRetry={() => state.retry()}
          errorId={state.error.message} // 지원 요청용
        />
      );

    case 'success':
      return (
        <ul>
          {state.data.map((p) => <PostCard key={p.id} post={p} />)}
        </ul>
      );
  }
};

// EmptyState.tsx
interface EmptyStateProps {
  illustration?: string;
  title: string;
  description: string;
  ctaText?: string;
  onCta?: () => void;
}
export const EmptyState = ({ illustration, title, description, ctaText, onCta }: EmptyStateProps) => (
  <div className="empty-state" role="status">
    {illustration && <img src={illustration} alt="" aria-hidden="true" />}
    <h2>{title}</h2>
    <p>{description}</p>
    {ctaText && onCta && (
      <button className="btn btn-primary" onClick={onCta}>{ctaText}</button>
    )}
  </div>
);
```

**관련 패턴**: [Skeleton](#skeleton-shimmer), [Optimistic UI](#optimistic-ui-update), [Error Handling](error-handling.md), [Accessibility](#a11y-wcag)

---

## 7. Internationalization (i18n)

<a id="i18n"></a>

**목적**: 애플리케이션을 다국어·다지역으로 확장 가능하게 설계. 텍스트 번역 외에도 **숫자/날짜/통화 포맷, 복수형(plural), 성별(gender), RTL(우→좌 언어), 시간대(timezone)** 처리.

**핵심 표준**:
- **ICU MessageFormat** (Unicode 표준) — plural / select / number / date 통합 문법
- **CLDR** (Common Locale Data Repository) — 언어별 포맷·복수형 규칙 데이터셋
- **BCP 47** — 언어 태그 (`ko-KR`, `en-US`, `zh-Hant-TW`)

**i18n vs L10n**:
- **i18n** (internationalization) — 코드 구조를 다국어 가능하게 (디자인 시간)
- **L10n** (localization) — 특정 지역으로 번역·문화 적응 (운영 시간)

**메커니즘**:

```
소스 코드 (key 사용)
    │
    │   "user.greeting" → t('user.greeting', { name: 'Alice' })
    ▼
번역 리소스 파일
    ├─ ko.json  →  "user.greeting": "안녕하세요, {name}님"
    ├─ en.json  →  "user.greeting": "Hello, {name}"
    └─ ja.json  →  "user.greeting": "{name}さん、こんにちは"
    │
    ▼
런타임 (locale 감지)
    ├─ 브라우저: navigator.language
    ├─ 사용자 설정 우선
    └─ 서버 헤더: Accept-Language
```

**대표 라이브러리**:
- **react-i18next** / **i18next** — 가장 보편적
- **format.js** (FormatJS) — ICU MessageFormat 표준 준수
- **next-intl** — Next.js 통합
- **Flutter**: `intl` 패키지 + `flutter gen-l10n`

**ICU MessageFormat 예제 (plural / select)**:
```
{count, plural,
  =0    {게시물이 없어요}
  one   {게시물 #개}
  other {게시물 #개}
}

{gender, select,
  male   {그가 답글을 남겼어요}
  female {그녀가 답글을 남겼어요}
  other  {답글이 달렸어요}
}
```

**RTL (Right-to-Left)**:
- 아랍어 / 히브리어 / 페르시아어 → 텍스트 방향 우→좌
- 레이아웃도 거울 반전 (네비게이션 좌→우, 아이콘 방향)
- CSS: `[dir="rtl"]` selector + logical properties (`margin-inline-start`)
- HTML: `<html lang="ar" dir="rtl">`

**번역 키 네이밍 규칙**:
- 화면별 그룹화: `login.title`, `login.submit`, `signup.title`
- 의미 기반 (콘텐츠 X): `error.network_failed` (NOT `red_message_1`)
- 중첩 구조: `home.banner.title`, `home.banner.subtitle`
- 컨텍스트 명시: `button.cancel` ≠ `dialog.cancel` (재사용 시 충돌 회피)

**장점**:
- 글로벌 시장 진입 — 사용자 모국어 지원
- 코드 변경 없이 번역 파일만 교체
- 번역 외주 / 크라우드소싱 (Crowdin, Lokalise)
- 법적 요구사항 충족 (EU, 캐나다 등)

**단점**:
- 텍스트 길이 변동 — 독일어는 영어보다 ~30% 김 (레이아웃 깨짐)
- 복수형 규칙 다양 — 아랍어 6 가지, 러시아어 3 가지
- 날짜·시간·통화 포맷 차이 (`$1,234.56` vs `1.234,56 €` vs `¥1,234`)
- 번역 비용·관리 부담
- 동적 텍스트 결합 금지 (`"Hello" + name` → 어순 못 바뀜)

**활용 예시**:
- 글로벌 서비스 (Airbnb 60+ 언어, Netflix 30+ 언어)
- 게임 (Steam, Riot Games)
- 모바일 앱 (App Store/Play Store 글로벌 출시)
- 정부/공공 서비스 (다언어 의무)

**react-i18next 예제**:
```tsx
import { useTranslation, Trans } from 'react-i18next';

// public/locales/ko/common.json
// {
//   "greeting": "안녕하세요, {{name}}님",
//   "post_count": "{{count}}개의 게시물",
//   "post_count_zero": "게시물이 없어요"
// }

export const UserGreeting = ({ user }: { user: User }) => {
  const { t, i18n } = useTranslation('common');

  return (
    <div>
      <h1>{t('greeting', { name: user.name })}</h1>
      <p>{t('post_count', { count: user.postCount })}</p>

      {/* 숫자 포맷 — Intl API */}
      <p>{new Intl.NumberFormat(i18n.language, {
        style: 'currency', currency: 'KRW',
      }).format(user.balance)}</p>

      {/* 날짜 포맷 */}
      <p>{new Intl.DateTimeFormat(i18n.language, {
        dateStyle: 'long', timeStyle: 'short',
      }).format(user.joinedAt)}</p>

      {/* React 컴포넌트 보간 */}
      <Trans i18nKey="welcome_html">
        Welcome <strong>back</strong>!
      </Trans>
    </div>
  );
};

// 언어 전환
const { i18n } = useTranslation();
i18n.changeLanguage('en');
```

**Flutter ARB 예제**:
```json
// lib/l10n/app_ko.arb
{
  "greeting": "안녕하세요, {name}님",
  "@greeting": { "placeholders": { "name": { "type": "String" } } },
  "postCount": "{count, plural, =0{게시물이 없어요} other{{count}개의 게시물}}",
  "@postCount": { "placeholders": { "count": { "type": "int" } } }
}
```

**관련 패턴**: [Design Tokens](#design-tokens), [Accessibility](#a11y-wcag), [Responsive](#responsive-adaptive), [Error Handling](error-handling.md)

---

## 8. Accessibility (A11y) — WCAG 2.2

<a id="a11y-wcag"></a>

**목적**: 시각·청각·운동·인지 장애가 있는 사용자도 동등하게 웹/앱을 사용할 수 있도록 설계. WCAG 2.2 (Web Content Accessibility Guidelines, W3C 2023 권고) 가 표준. 법적 요구사항인 국가 다수 (EU EAA 2025, 미국 ADA, 한국 장애인차별금지법).

**POUR 4 원칙 (WCAG)**:

| 원칙 | 의미 | 예시 |
|------|------|------|
| **Perceivable** | 인지 가능 | 이미지 alt 텍스트, 비디오 자막, 색대비 |
| **Operable** | 조작 가능 | 키보드 탐색, 충분한 시간, 발작 유발 차단 |
| **Understandable** | 이해 가능 | 명확한 언어, 일관된 네비게이션, 오류 안내 |
| **Robust** | 견고함 | 표준 HTML, ARIA, 보조 기술 호환 |

**준수 레벨**:
- **Level A** — 최소 요구사항 (기본 alt 텍스트, 키보드 접근)
- **Level AA** — 일반 권장 (색대비 4.5:1, focus 표시) — **법적 기준 다수**
- **Level AAA** — 최고 수준 (색대비 7:1, 수화 비디오)

**핵심 체크리스트**:

1. **시맨틱 HTML** — `<div>` 남용 금지, `<button>` `<nav>` `<main>` 활용
2. **Alt 텍스트** — 모든 의미 있는 이미지에 (`alt=""` 장식용은 빈 값)
3. **키보드 탐색** — Tab/Shift+Tab/Enter/Space/Escape/화살표 키만으로 모든 기능 사용
4. **Focus 표시** — `:focus-visible` 명확한 outline (CSS `outline: none` 금지)
5. **색 대비** — 텍스트 4.5:1 (Level AA), 큰 텍스트 3:1
6. **색만으로 의미 전달 금지** — 빨강·녹색만으로 에러/성공 구분 X (텍스트 + 아이콘 병행)
7. **ARIA 라벨** — `aria-label`, `aria-labelledby`, `aria-describedby`
8. **Live regions** — 동적 변경을 보조기술에 알림 (`role="status"`, `aria-live="polite"`)
9. **Form 라벨** — `<label for="id">` 또는 `aria-label` 필수
10. **언어 선언** — `<html lang="ko">`
11. **Skip link** — 콘텐츠로 바로 이동 (스크린리더 사용자)
12. **Reduced motion** — `prefers-reduced-motion` 대응

**WCAG 2.2 신규 항목 (vs 2.1)**:
- **Focus Not Obscured** — sticky 헤더로 focus 가린 상태 금지
- **Dragging Movements** — 드래그 대안 입력 제공
- **Target Size (Minimum)** — 클릭 영역 24×24px 이상
- **Consistent Help** — 도움 옵션 일관 위치

**테스트 도구**:
- **axe DevTools** (Deque) — 브라우저 확장
- **Lighthouse Accessibility** — Chrome 내장
- **WAVE** (WebAIM)
- **NVDA** / **JAWS** (Windows 스크린리더)
- **VoiceOver** (macOS/iOS)
- **TalkBack** (Android)

**장점**:
- 글로벌 인구 15%(WHO 통계) 의 접근권 보장
- 법적 리스크 회피 (EU EAA, ADA 소송)
- SEO 부수효과 — 시맨틱 HTML, alt 텍스트 → 크롤러 친화
- 노년층·일시적 장애(팔 부상, 밝은 야외) 도 혜택
- 코드 품질 자동 상승 (시맨틱 마크업)

**단점**:
- 초기 학습 곡선 — ARIA 사용법 오용 시 오히려 악화
- 자동 테스트는 ~30% 만 커버 — 수동 테스트 필수
- 일부 디자인 의도(완전 커스텀 컨트롤) 와 충돌
- 보조기술 다양성 — 모든 조합 검증 어려움

**활용 예시**:
- 공공기관 / 정부 사이트 (법적 의무)
- 금융 / 헬스케어 (규제 산업)
- 교육 콘텐츠 (학생 접근성)
- 대기업 제품 (브랜드 책임)

**React 예제 (a11y-friendly 컴포넌트)**:
```tsx
// 1. 시맨틱 HTML + ARIA
export const Modal = ({ isOpen, onClose, title, children }: ModalProps) => {
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);

  // ESC 키로 닫기
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  // Focus trap — 모달 내부로 focus 가둠
  useEffect(() => {
    if (isOpen) dialogRef.current?.focus();
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      tabIndex={-1}
      className="modal"
    >
      <h2 id={titleId}>{title}</h2>
      {children}
      <button onClick={onClose} aria-label="모달 닫기">
        <svg aria-hidden="true">{/* X icon */}</svg>
      </button>
    </div>
  );
};

// 2. Live region — 동적 변경 알림
export const Toast = ({ message, type }: { message: string; type: 'success' | 'error' }) => (
  <div
    role={type === 'error' ? 'alert' : 'status'}
    aria-live={type === 'error' ? 'assertive' : 'polite'}
    className={`toast toast-${type}`}
  >
    {message}
  </div>
);

// 3. Form 라벨 + 에러 연결
export const EmailInput = ({ value, onChange, error }: Props) => {
  const id = useId();
  const errorId = `${id}-error`;
  return (
    <div>
      <label htmlFor={id}>이메일</label>
      <input
        id={id}
        type="email"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        required
      />
      {error && <span id={errorId} role="alert">{error}</span>}
    </div>
  );
};

// 4. Skip link — 키보드 사용자
export const SkipLink = () => (
  <a href="#main" className="skip-link">본문 바로가기</a>
);
```

```css
/* :focus-visible — 키보드 사용자에게만 outline */
button:focus-visible {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}

/* 색 대비: 4.5:1 이상 */
.text { color: #595959; background: #ffffff; /* 7.0:1 — AAA */ }

/* Skip link — 평소 가림, focus 시 표시 */
.skip-link {
  position: absolute;
  top: -40px;
}
.skip-link:focus {
  top: 0;
}

/* Reduced motion 대응 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Target size — 24×24px 최소 (WCAG 2.2) */
button { min-width: 24px; min-height: 24px; padding: 8px 12px; }
```

**관련 패턴**: [i18n](#i18n), [Design Tokens](#design-tokens), [Responsive](#responsive-adaptive), [Skeleton](#skeleton-shimmer)

---

## 9. Responsive vs Adaptive

<a id="responsive-adaptive"></a>

**목적**: 다양한 화면 크기(모바일 / 태블릿 / 데스크톱 / TV / 워치) 에서 최적 UX 를 제공하는 두 접근. **Responsive**(fluid, 유체) 는 단일 레이아웃이 부드럽게 늘어나고, **Adaptive**(adaptive, 적응) 는 고정 breakpoint 별 별도 레이아웃을 선택.

**Responsive vs Adaptive**:

```
Responsive Design (유체)
─────────────────────────────────
한 레이아웃이 화면 너비에 따라 부드럽게 변형
flexbox / grid + % / em / rem / fr 단위 + media query
모든 화면 크기에 매끄럽게 대응

[모바일] 320px ════════════ 1920px [데스크톱]
        ↑ 컬럼 1개         ↑ 컬럼 4개  부드럽게 변화


Adaptive Design (적응)
─────────────────────────────────
정해진 breakpoint 마다 다른 레이아웃 선택
device class 감지 → 다른 컴포넌트/레이아웃 렌더

[모바일 ≤768] → MobileLayout
[태블릿 769-1024] → TabletLayout
[데스크톱 >1024] → DesktopLayout
```

**Mobile-First 원칙**:
- 모바일 CSS 를 default 로 작성, 큰 화면에서 `min-width` media query 로 확장
- 작은 → 큰 방향이 자연스러움 (제약 → 풍부함)
- 반대(데스크톱 → 모바일) 는 의도치 않은 누락 빈번

**Breakpoint 전략**:

| 범주 | 너비 | 디바이스 |
|------|------|----------|
| `xs` | < 576px | 모바일 (세로) |
| `sm` | ≥ 576px | 모바일 (가로) |
| `md` | ≥ 768px | 태블릿 |
| `lg` | ≥ 1024px | 데스크톱 |
| `xl` | ≥ 1280px | 큰 데스크톱 |
| `2xl` | ≥ 1536px | 4K / TV |

**Container Query (2023+)**:
- 부모 컨테이너 크기 기준으로 반응 (viewport 가 아님)
- 컴포넌트 단위 반응형 가능 (재사용성↑)
- `@container (min-width: 400px) { ... }`

**Fluid Typography**:
- `clamp(MIN, PREFERRED, MAX)` — 화면 크기에 따라 자동 보간
- 예: `font-size: clamp(1rem, 0.9rem + 0.5vw, 1.5rem)`

**Responsive 장점**:
- 단일 코드베이스 — 유지보수 비용↓
- 미래 디바이스 자동 대응 (새 화면 크기 출시 시도 동작)
- SEO 단일 URL — 모바일/데스크톱 분리 사이트 불필요

**Responsive 단점**:
- 양 극단 (320px 와 4K) 동시 최적화 어려움
- 데스크톱 콘텐츠가 모바일에서도 다 로드 (네트워크 낭비)
- 디자이너가 모든 breakpoint 검토 필요

**Adaptive 장점**:
- 각 디바이스에 100% 최적화된 UX
- 디바이스별 다른 콘텐츠/기능 제공 가능
- 모바일에 불필요한 데스크톱 자산 안 보냄

**Adaptive 단점**:
- 다중 레이아웃 유지보수 비용
- 새 디바이스/해상도 출시 시 추가 작업
- Sniffing 의 부정확성 (User-Agent 기반)

**활용 예시**:
- Responsive: Bootstrap / Tailwind / Material 기반 모던 웹
- Adaptive: 모바일 앱 (네이티브 별도 UI), 기업 어드민 (데스크톱 전용)
- Hybrid: Twitter — 모바일 ≠ 데스크톱 (다른 레이아웃) 이지만 fluid 내부 + 거대 breakpoint 1개

**Tailwind Responsive 예제 (Mobile-First)**:
```tsx
export const ProductGrid = ({ products }: { products: Product[] }) => (
  <div
    className="
      grid gap-4
      grid-cols-1
      sm:grid-cols-2
      md:grid-cols-3
      lg:grid-cols-4
      xl:grid-cols-5
    "
  >
    {products.map((p) => (
      <ProductCard key={p.id} product={p} />
    ))}
  </div>
);

// 출력 CSS (Tailwind 컴파일):
// .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
// @media (min-width: 640px) { .sm\:grid-cols-2 { grid-template-columns: ... } }
// @media (min-width: 768px) { .md\:grid-cols-3 { ... } }
```

**CSS Container Query 예제**:
```css
.product-card-container {
  container-type: inline-size;
  container-name: product-card;
}

.product-card {
  display: flex;
  flex-direction: column;
}

/* 컨테이너 폭이 400px 이상이면 가로 레이아웃 */
@container product-card (min-width: 400px) {
  .product-card {
    flex-direction: row;
  }
}
```

**React Adaptive 예제 (디바이스별 다른 컴포넌트)**:
```tsx
function useDeviceType() {
  const [type, setType] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');

  useEffect(() => {
    const update = () => {
      const w = window.innerWidth;
      if (w < 768) setType('mobile');
      else if (w < 1024) setType('tablet');
      else setType('desktop');
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return type;
}

export const Navigation = () => {
  const device = useDeviceType();

  if (device === 'mobile') return <MobileBottomNav />;
  if (device === 'tablet') return <TabletSideNav collapsed />;
  return <DesktopTopNav />;
};
```

**관련 패턴**: [Design Tokens](#design-tokens), [Atomic Design](#atomic-design), [Accessibility](#a11y-wcag), [Mobile Patterns](mobile-app.md)

---

## 10. Design Tokens

<a id="design-tokens"></a>

**목적**: 디자인 시스템의 시각 속성(컬러·간격·타이포·라운드·섀도) 을 **의미 있는 추상 변수(token)** 로 정의하여, 코드/디자인 도구 간 single source of truth 를 구축합니다. Salesforce 가 2014 년 *Lightning Design System* 에서 정식화, 이후 Adobe Spectrum / Material 3 등에 표준화.

**3 단계 토큰 위계**:

```
┌──────────────────────────────────────────────────────────────┐
│  1. Primitive (Atomic) — 원시 값                              │
│     blue-50: #EFF6FF                                         │
│     blue-500: #3B82F6                                        │
│     blue-900: #1E3A8A                                        │
│           ↓ 의미 부여                                         │
│  2. Semantic (Alias) — 용도별 의미                            │
│     color-text-primary: blue-900                             │
│     color-background-surface: blue-50                        │
│     color-action-primary: blue-500                           │
│           ↓ 컴포넌트별 매핑                                   │
│  3. Component — 컴포넌트 전용                                 │
│     button-primary-bg: color-action-primary                  │
│     button-primary-text: color-on-action                     │
└──────────────────────────────────────────────────────────────┘
```

**토큰 카테고리**:
- **Color** — primitive(blue-500) + semantic(text-primary) + state(hover/disabled)
- **Spacing** — `4 / 8 / 12 / 16 / 24 / 32 / 48 / 64`
- **Typography** — font-family / size / weight / line-height / letter-spacing
- **Border Radius** — `2 / 4 / 8 / 16 / 9999(pill)`
- **Shadow / Elevation** — sm / md / lg / xl
- **Motion** — duration / easing
- **Z-index** — modal / dropdown / tooltip 위계

**대표 도구**:
- **Style Dictionary** (Amazon) — JSON → CSS / iOS / Android / Flutter 등 다중 플랫폼 빌드
- **Tokens Studio for Figma** — Figma 토큰 관리
- **W3C Design Tokens Format Module** (드래프트) — 표준화 진행 중
- **CSS Custom Properties** — `--color-primary: #3B82F6`

**Multi-Brand / Theme**:
- Primitive 동일 + Semantic 만 변경 → 다크 모드 / 브랜드 변종
- 예: 라이트 `text-primary = gray-900`, 다크 `text-primary = gray-50`

**장점**:
- 디자인-코드 single source of truth
- 다크/라이트 모드 전환 자동 (semantic 토큰만 변경)
- 다중 브랜드 / 화이트라벨 지원
- 디자이너 변경이 코드에 자동 반영 (CI/CD 연동)
- 일관성 — 임의 hex 값 사용 방지

**단점**:
- 초기 구조 설계 비용 (토큰 위계 / 네이밍)
- 토큰명 변경이 곧 breaking change
- 너무 많은 토큰 → 디자이너가 어느 걸 쓸지 혼란
- Figma ↔ 코드 동기화 자동화 도구 필요
- 컴포넌트별 토큰 폭발 (token explosion)

**활용 예시**:
- 디자인 시스템 (Material 3, Carbon, Polaris, Spectrum, Lightning)
- 모바일 + 웹 + 데스크톱 멀티플랫폼 (Atlassian, Shopify)
- 화이트라벨 / 다중 브랜드 (Slack workspace 테마)
- 다크 모드 지원 모든 앱

**Style Dictionary JSON 예제**:
```json
// tokens/color.json
{
  "color": {
    "primitive": {
      "blue": {
        "50":  { "value": "#EFF6FF" },
        "500": { "value": "#3B82F6" },
        "900": { "value": "#1E3A8A" }
      },
      "gray": {
        "50":  { "value": "#F9FAFB" },
        "900": { "value": "#111827" }
      }
    },
    "semantic": {
      "text": {
        "primary":   { "value": "{color.primitive.gray.900}" },
        "secondary": { "value": "{color.primitive.gray.500}" }
      },
      "background": {
        "default": { "value": "{color.primitive.gray.50}" },
        "surface": { "value": "#FFFFFF" }
      },
      "action": {
        "primary":       { "value": "{color.primitive.blue.500}" },
        "primary-hover": { "value": "{color.primitive.blue.900}" }
      }
    }
  }
}

// tokens/spacing.json
{
  "spacing": {
    "xs": { "value": "4px" },
    "sm": { "value": "8px" },
    "md": { "value": "16px" },
    "lg": { "value": "24px" },
    "xl": { "value": "32px" }
  }
}
```

**Style Dictionary 빌드 → 다중 플랫폼**:
```javascript
// build.js
const StyleDictionary = require('style-dictionary');
StyleDictionary.extend({
  source: ['tokens/**/*.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'dist/css/',
      files: [{ destination: 'tokens.css', format: 'css/variables' }],
    },
    ios: {
      transformGroup: 'ios',
      buildPath: 'dist/ios/',
      files: [{ destination: 'Tokens.swift', format: 'ios-swift/class.swift' }],
    },
    android: {
      transformGroup: 'android',
      buildPath: 'dist/android/',
      files: [{ destination: 'tokens.xml', format: 'android/resources' }],
    },
    flutter: {
      transformGroup: 'flutter',
      buildPath: 'dist/flutter/',
      files: [{ destination: 'tokens.dart', format: 'flutter/class.dart' }],
    },
  },
}).buildAllPlatforms();
```

**생성된 CSS 사용**:
```css
/* dist/css/tokens.css (자동 생성) */
:root {
  --color-text-primary: #111827;
  --color-action-primary: #3B82F6;
  --spacing-md: 16px;
}

[data-theme="dark"] {
  --color-text-primary: #F9FAFB;
  --color-action-primary: #60A5FA;
}

.btn-primary {
  background: var(--color-action-primary);
  color: white;
  padding: var(--spacing-md);
}
```

**Flutter 사용 예제**:
```dart
// design_system/lib/tokens.dart (자동 생성)
class DsColor {
  static const textPrimary = Color(0xFF111827);
  static const actionPrimary = Color(0xFF3B82F6);
}

class DsSpacing {
  static const md = 16.0;
  static const lg = 24.0;
}

// 사용처 — raw hex 금지
Container(
  padding: const EdgeInsets.all(DsSpacing.md),
  color: DsColor.actionPrimary,
)
```

**관련 패턴**: [Atomic Design](#atomic-design), [Responsive](#responsive-adaptive), [Accessibility](#a11y-wcag), [Compound Components](#compound-components)

---

## 11. Compound Components / Slot

<a id="compound-components"></a>

**목적**: 부모-자식 컴포넌트가 **암묵적 Context 를 공유**하여 하나의 일체화된 UI 를 구성하는 React 패턴. `<select>` `<option>` 의 HTML 네이티브 동작을 React 로 모방. 사용자가 컴포넌트 구조를 자유롭게 조립하면서도 내부 동작이 일관되게 유지됩니다.

**Compound Components vs 단일 props 컴포넌트**:

```
❌ 단일 props 방식 — 모든 옵션을 props 로 전달
<Tabs
  tabs={[
    { id: 'a', label: 'A', content: <ContentA /> },
    { id: 'b', label: 'B', content: <ContentB /> },
  ]}
  active="a"
  onChange={...}
/>
→ 확장성↓ — 새 기능(아이콘, badge) 추가 시 props 폭발

✅ Compound Components — 사용자가 직접 조립
<Tabs defaultValue="a">
  <Tabs.List>
    <Tabs.Trigger value="a"><Icon /> A 탭 <Badge>3</Badge></Tabs.Trigger>
    <Tabs.Trigger value="b">B 탭</Tabs.Trigger>
  </Tabs.List>
  <Tabs.Panel value="a"><ContentA /></Tabs.Panel>
  <Tabs.Panel value="b"><ContentB /></Tabs.Panel>
</Tabs>
→ 사용자가 마크업 구조 자유롭게 결정, 내부 동작은 Context 로 동기화
```

**메커니즘**:
- 부모(`<Tabs>`)가 Context 로 상태(`activeTab`, `setActiveTab`) 제공
- 자식(`<Tabs.Trigger>` / `<Tabs.Panel>`) 이 useContext 로 상태 구독
- Dot notation 으로 자식 노출 (`Tabs.Trigger = TabsTrigger`)
- Headless 패턴과 결합 — 로직만 제공, 스타일은 사용자 자유

**유사 패턴**:
- **Slot Pattern** — 자식 요소를 명명된 슬롯에 배치 (`<Card.Header>` / `<Card.Body>` / `<Card.Footer>`)
- **Render Props** — 자식에 함수 전달 (`<Tabs render={(state) => ...} />`)
- **Children as Function** — `<Tabs>{({state}) => ...}</Tabs>`
- **Headless UI** — Radix UI, Headless UI, React Aria — 로직만 제공

**장점**:
- 유연성 — 사용자가 마크업 구조 자유 결정 (조건부 렌더, 아이콘 추가 등)
- 의미적 마크업 — 의도가 코드에 그대로 표현
- 확장성 — 새 자식 컴포넌트 추가 시 부모 props 변경 불필요
- React 다운 작성법 (children 활용)
- a11y 자동화 — 라이브러리가 ARIA 처리 (Radix UI)

**단점**:
- 잘못된 사용 어려움 — `<Tabs.Trigger>` 를 `<Tabs>` 밖에 두면 Context 에러
- 학습 곡선 — 사용자가 구조 학습 필요
- TypeScript 정의 복잡 (`forwardRef` + Context + dot notation)
- 디버깅 — 어느 자식이 어느 부모를 참조하는지 추적
- 너무 자유로워 — 디자인 일관성 강제 어려움

**활용 예시**:
- Tabs, Accordion, Disclosure (Radix UI, Headless UI)
- Select, Combobox, Listbox
- Dialog, Tooltip, Popover
- Form 컴포넌트 (`<Form>` `<Form.Field>` `<Form.Label>`)
- Card 류 (`<Card.Header>` `<Card.Body>` `<Card.Footer>`)
- Table 류 (`<Table.Row>` `<Table.Cell>`)

**React Compound Components 예제 (Tabs)**:
```tsx
import { createContext, useContext, useState, ReactNode } from 'react';

interface TabsContextValue {
  active: string;
  setActive: (v: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('Tabs.* 는 <Tabs> 안에서만 사용 가능');
  return ctx;
}

// 1. 부모 컴포넌트 — Context provider
interface TabsProps {
  defaultValue: string;
  children: ReactNode;
}
export function Tabs({ defaultValue, children }: TabsProps) {
  const [active, setActive] = useState(defaultValue);
  return (
    <TabsContext.Provider value={{ active, setActive }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

// 2. 자식: List
Tabs.List = function TabsList({ children }: { children: ReactNode }) {
  return <div role="tablist" className="tabs-list">{children}</div>;
};

// 3. 자식: Trigger (탭 버튼)
interface TriggerProps {
  value: string;
  children: ReactNode;
}
Tabs.Trigger = function TabsTrigger({ value, children }: TriggerProps) {
  const { active, setActive } = useTabsContext();
  const isActive = active === value;
  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-controls={`panel-${value}`}
      id={`tab-${value}`}
      tabIndex={isActive ? 0 : -1}
      className={isActive ? 'tab-active' : 'tab'}
      onClick={() => setActive(value)}
    >
      {children}
    </button>
  );
};

// 4. 자식: Panel (탭 콘텐츠)
interface PanelProps {
  value: string;
  children: ReactNode;
}
Tabs.Panel = function TabsPanel({ value, children }: PanelProps) {
  const { active } = useTabsContext();
  if (active !== value) return null;
  return (
    <div
      role="tabpanel"
      id={`panel-${value}`}
      aria-labelledby={`tab-${value}`}
      tabIndex={0}
    >
      {children}
    </div>
  );
};

// 사용처 — 사용자가 자유롭게 조립
export const Settings = () => (
  <Tabs defaultValue="profile">
    <Tabs.List>
      <Tabs.Trigger value="profile">
        <UserIcon /> 프로필 <Badge>NEW</Badge>
      </Tabs.Trigger>
      <Tabs.Trigger value="security">보안</Tabs.Trigger>
      <Tabs.Trigger value="billing">결제</Tabs.Trigger>
    </Tabs.List>

    <Tabs.Panel value="profile"><ProfileForm /></Tabs.Panel>
    <Tabs.Panel value="security"><SecurityForm /></Tabs.Panel>
    <Tabs.Panel value="billing"><BillingForm /></Tabs.Panel>
  </Tabs>
);
```

**Headless UI 라이브러리 사용 (Radix UI)**:
```tsx
import * as Tabs from '@radix-ui/react-tabs';

// 로직·a11y 는 Radix 가 처리, 스타일만 우리가 결정
export const SettingsRadix = () => (
  <Tabs.Root defaultValue="profile">
    <Tabs.List className="flex gap-2 border-b">
      <Tabs.Trigger value="profile" className="px-4 py-2 data-[state=active]:border-b-2">
        프로필
      </Tabs.Trigger>
      <Tabs.Trigger value="security" className="px-4 py-2">보안</Tabs.Trigger>
    </Tabs.List>
    <Tabs.Content value="profile"><ProfileForm /></Tabs.Content>
    <Tabs.Content value="security"><SecurityForm /></Tabs.Content>
  </Tabs.Root>
);
```

**관련 패턴**: [Atomic Design](#atomic-design), [Container/Presenter](#container-presenter), [Design Tokens](#design-tokens), [Render Props](functional.md), [Context Pattern](state-management.md)

---

## 마무리

UI/UX 패턴 11 종은 **컴포넌트 설계**(Atomic / Compound / Container-Presenter), **로딩 UX**(Skeleton / Optimistic / Empty-Error-Loading State / Infinite Scroll), **글로벌 품질**(i18n / a11y / Responsive), **시스템화**(Design Tokens) 4 군으로 묶인다.

**선택 흐름**:

```
새 화면 설계 시:
   ├─→ 컴포넌트 분해 → Atomic Design 5 단계
   ├─→ 로직/렌더 분리 → Container/Presenter 또는 custom hook
   ├─→ 4 상태 처리 → Empty/Error/Loading/Success
   ├─→ 로딩 UX → Skeleton + Optimistic
   ├─→ 다국어 필요 → i18n (react-i18next / format.js)
   ├─→ 접근성 검증 → WCAG 2.2 AA
   ├─→ 반응형 → Mobile-first responsive (Tailwind / CSS Grid)
   ├─→ 디자인 일관성 → Design Tokens (Style Dictionary)
   └─→ 재사용 가능 위젯 → Compound Components (Radix UI)
```

**최우선 순위 (모든 프로젝트 필수)**:
1. **Empty/Error/Loading State** — 4 상태 누락 시 사용자 혼란
2. **A11y WCAG 2.2 AA** — 법적 요구사항·SEO·15% 인구
3. **Design Tokens** — single source of truth
4. **Responsive (Mobile-first)** — 모바일 트래픽 60%+ 시대

**관련 카탈로그 cross-link 정리**:
- 렌더링 전략: [web-rendering.md](web-rendering.md)
- 상태 관리: [state-management.md](state-management.md)
- 모바일 특화: [mobile-app.md](mobile-app.md)
- UI 아키텍처: [architectural.md](architectural.md) (MVC / MVVM / MVI)
- 에러 핸들링: [error-handling.md](error-handling.md)
- 함수형(Render Props): [functional.md](functional.md)
