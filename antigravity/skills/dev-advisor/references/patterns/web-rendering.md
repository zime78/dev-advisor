# Web 렌더링 아키텍처 (Web Rendering Architecture)

프론트엔드 렌더링 전략 10 종. CSR → SSR → SSG → ISR → Streaming → Islands → RSC → Resumability 의 진화. 각각 **TTFB / FCP / TTI / SEO / Server cost / Cache** 의 trade-off 가 다름.

**원전·표준**:
- Patterns.dev — https://www.patterns.dev (Lydia Hallie, Addy Osmani)
- React Docs — https://react.dev (Server Components, Streaming)
- Next.js / Remix / Astro / Qwik / SolidStart 공식 가이드
- Google Web Vitals (LCP / FID / CLS / INP)

**의사결정 매트릭스**:

| 전략 | TTFB | FCP | TTI | SEO | Server 부하 | 적합 |
|------|------|-----|-----|-----|-----------|------|
| CSR | 빠름 | 느림 | 보통 | 약함 | 낮음 | SPA, 인증 후 대시보드 |
| SSR | 느림 | 빠름 | 보통 | 강함 | 높음 | 콘텐츠 가변, 개인화 |
| SSG | 빠름 | 빠름 | 빠름 | 강함 | 0 | 블로그, 문서, 마케팅 |
| ISR | 빠름 | 빠름 | 빠름 | 강함 | 낮음 | 콘텐츠 자주 변경 |
| Streaming SSR | 빠름 | 점진 | 점진 | 강함 | 중간 | 큰 페이지 |
| Islands | 빠름 | 빠름 | 빠름 | 강함 | 0~낮음 | 정적 + 부분 인터랙션 |
| RSC | 빠름 | 빠름 | 빠름 | 강함 | 중간 | 모던 React 앱 |
| Hydration | - | - | 느림 | - | - | (보조 메커니즘) |
| Resumability | 빠름 | 빠름 | 즉시 | 강함 | 낮음 | startup 성능 극대화 |
| Edge | 매우빠름 | 빠름 | 빠름 | 강함 | 낮음 | geo 분산, 글로벌 |

**관련 카탈로그**:
- [architectural.md](architectural.md) — MVC / MVVM / Flux/Redux
- [caching.md](caching.md) — CDN / Edge 캐시
- [networking.md](networking.md) — HTTP/2/3 / QUIC (TTFB 영향)

---

## 1. CSR (Client-Side Rendering)

<a id="csr"></a>

**목적**: 서버는 거의 빈 HTML(shell)만 내려주고, 브라우저에서 JavaScript 번들을 실행해 화면 전체를 그립니다. 전통적 SPA(Single Page Application) 모델.

**메커니즘**:
- 서버 응답: `<div id="root"></div>` + `<script src="bundle.js">`
- 브라우저: bundle 다운로드 → parse → execute → React/Vue/Angular 가 root 에 mount → API fetch → 화면 그림
- 라우팅은 클라이언트에서 `history.pushState` 로 처리 (전체 페이지 reload 없음)
- 검색 엔진은 기본적으로 빈 HTML 만 봄 (Googlebot 은 JS 실행하지만 지연·불완전)

**Web Vitals 영향**:
- **TTFB**: 빠름 (정적 HTML)
- **FCP**: 느림 (JS 다운로드 + parse + execute 후에야 첫 컨텐츠)
- **LCP**: 매우 느림 (이미지·텍스트 모두 JS 이후)
- **TTI**: 보통 (이미 JS 가 실행 중이므로 mount 직후 인터랙티브)
- **CLS**: 위험 (mount 시점에 layout shift 빈번)

**장점**:
- 서버 인프라 단순 (정적 파일 호스팅만으로 충분)
- 라우팅 후속 페이지 전환이 즉시 (no full reload)
- 풍부한 클라이언트 상호작용 (드래그, 애니메이션)
- CDN 캐시 친화 (HTML/JS 모두 정적)

**단점**:
- 초기 화면까지 빈 페이지 시간이 김 (white screen)
- SEO 약함 (크롤러 JS 실행 의존)
- JS 번들 크기 증가에 따라 성능 급격히 악화
- 저사양 기기·느린 네트워크에서 사용자 경험 저하

**활용 예시**:
- 인증 후 대시보드 (Gmail, Figma, Notion, Trello)
- 어드민 패널, 내부 도구
- 풍부한 상호작용이 핵심인 앱 (Excel 웹, Canva)
- 검색 노출 불필요한 closed product

**React 예제**:
```tsx
// public/index.html
// <!DOCTYPE html>
// <html><body><div id="root"></div><script src="/bundle.js"></script></body></html>

// src/App.tsx
import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

interface User {
  id: string;
  name: string;
}

function App() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // 브라우저에서만 실행 → 첫 paint 이후 데이터 fetch
    fetch("/api/me")
      .then((r) => r.json())
      .then((data: User) => setUser(data));
  }, []);

  if (!user) return <div>Loading…</div>;
  return <h1>Hello, {user.name}</h1>;
}

createRoot(document.getElementById("root")!).render(<App />);
```

**관련 패턴**: [SSR](#ssr), [Hydration](#hydration), [SPA Router](architectural.md)

---

## 2. SSR (Server-Side Rendering)

<a id="ssr"></a>

**목적**: 매 요청마다 서버에서 React/Vue 컴포넌트를 실행해 완성된 HTML 을 생성하여 응답합니다. 클라이언트는 HTML 을 즉시 paint 한 뒤 hydration 으로 인터랙티브로 만듭니다.

**메커니즘**:
- 요청 → 서버에서 데이터 fetch → 컴포넌트 트리 render → HTML 문자열 직렬화 → 응답
- 동일 컴포넌트가 클라이언트에서도 mount (hydration) → 이벤트 핸들러 attach
- Next.js: `getServerSideProps` / App Router default
- Nuxt: `asyncData` / `useFetch` (server context)
- Remix: loader 함수가 server-only

**Web Vitals 영향**:
- **TTFB**: 느림 (서버 render + DB fetch 시간 포함)
- **FCP**: 빠름 (응답 즉시 paint)
- **LCP**: 빠름 (콘텐츠가 HTML 에 포함)
- **TTI**: 보통 (hydration 비용)
- **CLS**: 낮음 (서버에서 layout 확정)

**장점**:
- SEO 강함 (크롤러가 완전한 HTML 즉시 수집)
- FCP/LCP 우수 — 마케팅·콘텐츠 사이트 핵심
- 개인화 가능 (요청별 cookie/header 로 다른 HTML)
- JS 비활성 환경에서도 콘텐츠 표시 (progressive enhancement)

**단점**:
- 서버 부하 큼 — 요청당 render 비용
- TTFB 증가 → 첫 byte 까지 대기
- 캐싱 전략 복잡 (개인화 vs 캐시)
- hydration 비용으로 TTI 가 SSG 보다 늦음

**활용 예시**:
- 전자상거래 상품 페이지 (Shopify storefronts, Amazon)
- 뉴스·미디어 (NYT, Vercel.com 자체)
- 로그인 후 개인화 dashboard 의 첫 페이지
- Next.js `app router` default, Remix, Nuxt

**React/Next.js 예제**:
```tsx
// app/products/[id]/page.tsx (Next.js App Router — server component default)
import { notFound } from "next/navigation";

interface Product {
  id: string;
  name: string;
  priceKrw: number;
}

async function fetchProduct(id: string): Promise<Product | null> {
  // 서버에서만 실행 (DB / API)
  const res = await fetch(`https://api.shop.com/products/${id}`, {
    cache: "no-store", // 매 요청마다 fresh fetch → SSR
  });
  if (!res.ok) return null;
  return res.json();
}

export default async function ProductPage({
  params,
}: {
  params: { id: string };
}) {
  const product = await fetchProduct(params.id);
  if (!product) notFound();

  // 서버에서 HTML 생성 후 응답 → 브라우저는 즉시 paint
  return (
    <article>
      <h1>{product.name}</h1>
      <p>{product.priceKrw.toLocaleString("ko-KR")}원</p>
    </article>
  );
}
```

**관련 패턴**: [Hydration](#hydration), [Streaming SSR](#streaming-ssr), [ISR](#isr)

---

## 3. SSG (Static Site Generation)

<a id="ssg"></a>

**목적**: 빌드 시점에 모든 페이지의 HTML 을 미리 생성하여 CDN 에 배포합니다. 런타임 서버 비용 0, 응답 속도 극대화.

**메커니즘**:
- `next build` / `astro build` / `gatsby build` / `hugo` 실행 시 컴포넌트 + 데이터 → HTML 파일 생성
- 페이지마다 `.html` 파일이 디스크에 떨어짐 → CDN 에 업로드
- 요청 시 CDN 이 정적 파일 즉시 응답 (서버 process 없음)
- 데이터 변경 시 전체 또는 부분 재빌드 필요

**Web Vitals 영향**:
- **TTFB**: 빠름 (CDN edge)
- **FCP**: 빠름 (완성된 HTML)
- **LCP**: 매우 빠름
- **TTI**: 빠름 (hydration 만)
- **CLS**: 낮음

**장점**:
- 응답 속도 최강 (CDN 정적 캐시)
- 서버 운영 비용 사실상 0
- DDoS 에 강함 (CDN 흡수)
- SEO 우수 (완전한 HTML)
- 보안 표면 최소 (런타임 코드 없음)

**단점**:
- 빌드 시간 증가 — 페이지 수에 선형 비례
- 데이터 변경 반영이 다음 빌드까지 지연
- 개인화 불가 (모두에게 동일 HTML)
- 페이지 폭증 시 빌드 수 분~시간

**활용 예시**:
- 기술 블로그·문서 사이트 (React docs, Tailwind docs, Astro starlight)
- 마케팅 랜딩 페이지
- 정적 컨텐츠 포트폴리오
- Jamstack 아키텍처

**Astro 예제**:
```astro
---
// src/pages/blog/[slug].astro
// Astro는 기본적으로 SSG (build 시 HTML 생성)
export async function getStaticPaths() {
  // 빌드 시 호출 → 모든 slug 에 대해 HTML 생성
  const posts = await fetch("https://cms.example.com/posts").then((r) =>
    r.json(),
  );
  return posts.map((p: { slug: string }) => ({
    params: { slug: p.slug },
    props: { post: p },
  }));
}

const { post } = Astro.props as { post: { title: string; body: string } };
---

<html>
  <body>
    <h1>{post.title}</h1>
    <div set:html={post.body} />
  </body>
</html>
```

**관련 패턴**: [ISR](#isr), [Islands Architecture](#islands-architecture), [Edge Rendering](#edge-rendering)

---

## 4. ISR (Incremental Static Regeneration)

<a id="isr"></a>

**목적**: SSG 의 응답 속도와 SSR 의 신선도를 결합. 빌드 후에도 백그라운드에서 페이지를 재생성하여 캐시를 점진적으로 갱신합니다.

**메커니즘**:
- 첫 요청: 캐시된 정적 HTML 응답 (stale 가능)
- 동시에 백그라운드에서 새 HTML 재생성 → 캐시 교체
- `revalidate: N` 옵션으로 N 초 후 stale 판정
- on-demand revalidation: webhook 으로 특정 path 즉시 무효화 가능
- Next.js 가 정립, Vercel/Netlify 가 인프라로 지원

**Web Vitals 영향**:
- **TTFB**: 빠름 (캐시 HIT)
- **FCP**: 빠름
- **LCP**: 빠름
- **TTI**: 빠름
- **CLS**: 낮음

**장점**:
- SSG 성능 + SSR 신선도
- 빌드 시간 단축 — 자주 변경되는 페이지만 백그라운드 갱신
- CDN 캐시 친화
- on-demand revalidation 으로 정확한 무효화 가능

**단점**:
- stale-while-revalidate 모델 → 첫 사용자가 오래된 데이터 볼 수 있음
- Vercel/Netlify 등 인프라 의존 (자체 호스팅 복잡)
- 디버깅 어려움 (캐시 상태 불투명)
- 개인화 여전히 불가

**활용 예시**:
- 전자상거래 카탈로그 (가격/재고 변동)
- 뉴스·블로그 (publish 후 분 단위 반영)
- 위키·문서 (사용자 편집 반영)
- Next.js `revalidate` / Vercel ISR

**Next.js 예제**:
```tsx
// app/products/[id]/page.tsx
export const revalidate = 60; // 60초마다 백그라운드 재생성 → ISR

interface Product {
  id: string;
  name: string;
  priceKrw: number;
  stock: number;
}

async function fetchProduct(id: string): Promise<Product> {
  const res = await fetch(`https://api.shop.com/products/${id}`, {
    next: { revalidate: 60 }, // fetch 단위 revalidate
  });
  return res.json();
}

export default async function ProductPage({
  params,
}: {
  params: { id: string };
}) {
  const product = await fetchProduct(params.id);
  return (
    <article>
      <h1>{product.name}</h1>
      <p>재고: {product.stock}</p>
    </article>
  );
}

// on-demand revalidation (별도 API route)
// import { revalidatePath } from "next/cache";
// revalidatePath(`/products/${id}`);
```

**관련 패턴**: [SSG](#ssg), [SSR](#ssr), [Edge Rendering](#edge-rendering)

---

## 5. Streaming SSR

<a id="streaming-ssr"></a>

**목적**: SSR 응답을 한꺼번에 보내지 않고, HTML 을 청크 단위로 흘려보내며 준비된 부분부터 즉시 paint 합니다. 느린 데이터 fetch 가 빠른 부분의 paint 를 막지 않음.

**메커니즘**:
- 서버: `renderToPipeableStream` (React 18+) 으로 HTML stream 시작
- `<Suspense>` 경계에서 데이터 대기 — fallback 을 먼저 flush
- 데이터 준비되면 해당 청크를 stream 으로 추가 push
- 브라우저: HTTP chunked transfer 로 받으면서 incremental paint
- React 18 / Next.js App Router / Remix `defer()` 가 지원

**Web Vitals 영향**:
- **TTFB**: 빠름 (shell 먼저 flush)
- **FCP**: 빠름 (shell paint)
- **LCP**: 점진적 (데이터 청크 도착마다)
- **TTI**: 점진적
- **CLS**: 주의 (청크 도착 시 layout shift 가능 — 명시 reserve 필요)

**장점**:
- 가장 느린 fetch 가 전체를 막지 않음 → 인지된 성능 향상
- SEO + 빠른 첫 paint 동시 달성
- 백엔드 다중 fetch 병렬화 자연스러움
- 사용자가 위에서부터 차례로 컨텐츠 본다 (UX 자연)

**단점**:
- 인프라 요구사항 (HTTP chunked, edge 호환)
- 에러 처리 복잡 (header 이미 flush 된 상태에서 5xx 불가)
- Suspense boundary 설계 필요
- 디버깅 어려움 (스트리밍 상태 추적)

**활용 예시**:
- 대시보드 (위 헤더는 즉시, 하단 차트는 stream)
- 검색 결과 페이지 (메타 즉시, 결과 청크 stream)
- React 18 / Next.js App Router default
- Shopify Hydrogen, Remix

**React 18 예제**:
```tsx
// app/dashboard/page.tsx (Next.js App Router)
import { Suspense } from "react";

async function fetchStats(): Promise<{ users: number }> {
  // 빠름 — 50ms
  return fetch("https://api.example.com/stats", { cache: "no-store" }).then(
    (r) => r.json(),
  );
}

async function fetchSlowAnalytics(): Promise<{ revenue: number }> {
  // 느림 — 3000ms (대용량 집계)
  return fetch("https://api.example.com/analytics", {
    cache: "no-store",
  }).then((r) => r.json());
}

async function Stats() {
  const stats = await fetchStats();
  return <div>활성 사용자: {stats.users}</div>;
}

async function Analytics() {
  const data = await fetchSlowAnalytics();
  return <div>매출: {data.revenue.toLocaleString("ko-KR")}원</div>;
}

export default function DashboardPage() {
  return (
    <main>
      <h1>대시보드</h1>
      {/* Stats 는 빠르게 흘러나옴 */}
      <Suspense fallback={<div>로딩…</div>}>
        <Stats />
      </Suspense>
      {/* Analytics 는 늦게 도착하지만 위 컨텐츠를 막지 않음 */}
      <Suspense fallback={<div>분석 로딩…</div>}>
        <Analytics />
      </Suspense>
    </main>
  );
}
```

**관련 패턴**: [SSR](#ssr), [React Server Components](#react-server-components), [Hydration](#hydration)

---

## 6. Islands Architecture

<a id="islands-architecture"></a>

**목적**: 페이지 대부분은 정적 HTML 로 보내고, 인터랙티브가 필요한 부분만 "섬(island)"으로 격리하여 해당 영역만 hydration 합니다. 전체 JS 번들 대신 부분 번들만 다운로드·실행.

**메커니즘**:
- 빌드 시 페이지를 정적 HTML 로 생성
- `client:load` / `client:visible` / `client:idle` 같은 directive 로 마킹된 컴포넌트만 클라이언트 번들 생성
- 브라우저: 정적 HTML 즉시 paint → 마킹된 컴포넌트만 개별 hydrate
- partial hydration / selective hydration 의 일종
- Astro 가 대표, Marko / Fresh / Eleventy is-land 도 채택

**Web Vitals 영향**:
- **TTFB**: 빠름 (정적)
- **FCP**: 빠름
- **LCP**: 빠름
- **TTI**: 빠름 (제한된 JS 만 실행)
- **INP**: 우수 (작은 번들)

**장점**:
- JS 번들 크기 극소화 → 모바일·저사양 최적
- 정적 페이지 부분은 hydration 비용 0
- 다양한 프레임워크 혼용 가능 (Astro 안에 React + Vue + Svelte)
- SEO 우수

**단점**:
- 섬 사이 상태 공유 어려움 (각 섬이 독립 mount)
- 글로벌 상태(예: 장바구니) 별도 전략 필요 (nano-store 등)
- 풍부한 상호작용(SPA)에는 부적합
- 라우팅이 multi-page (각 페이지 전체 reload)

**활용 예시**:
- 기술 블로그 + 댓글 위젯 (블로그 정적, 댓글만 인터랙티브)
- 문서 사이트 + 검색 박스
- 마케팅 + 가격 계산기
- Astro 기반 사이트, Fresh (Deno)

**Astro Islands 예제**:
```astro
---
// src/pages/blog/post.astro
// Astro 컴포넌트는 기본 정적 (서버에서 HTML 생성)
import LikeButton from "../components/LikeButton.tsx"; // React 컴포넌트
import CommentList from "../components/CommentList.tsx";

const post = await fetch("https://cms.example.com/posts/1").then((r) =>
  r.json(),
);
---

<html>
  <body>
    <article>
      <h1>{post.title}</h1>
      <div set:html={post.body} />
    </article>

    {/* 이 부분만 클라이언트에서 hydrate → 별도 JS 번들 */}
    <LikeButton client:load initialCount={post.likes} />

    {/* 뷰포트 진입 시에만 hydrate → 더 적극적 lazy */}
    <CommentList client:visible postId={post.id} />
  </body>
</html>
```

```tsx
// src/components/LikeButton.tsx
import { useState } from "react";

interface Props {
  initialCount: number;
}

export default function LikeButton({ initialCount }: Props) {
  const [count, setCount] = useState(initialCount);
  return <button onClick={() => setCount(count + 1)}>좋아요 {count}</button>;
}
```

**관련 패턴**: [SSG](#ssg), [React Server Components](#react-server-components), [Resumability](#resumability)

---

## 7. React Server Components (RSC)

<a id="react-server-components"></a>

**목적**: 서버에서만 실행되는 React 컴포넌트. 클라이언트 번들에 포함되지 않으며, 직접 DB·파일시스템에 접근할 수 있고, 결과는 직렬화된 트리로 stream 됨.

**메커니즘**:
- `'use client'` 지시어가 없는 컴포넌트는 default 로 server component (Next.js App Router)
- 서버에서 컴포넌트 실행 → React 가 직렬화 가능한 트리("RSC payload") 생성 → stream
- 클라이언트는 payload 를 React tree 로 재구성 → DOM 에 반영
- 클라이언트 컴포넌트(`'use client'`)는 별도 JS 번들로 hydrate
- async/await 를 컴포넌트에서 직접 사용 가능

**Web Vitals 영향**:
- **TTFB**: 빠름~보통 (서버 fetch 비용)
- **FCP**: 빠름
- **LCP**: 빠름 (데이터 포함된 HTML)
- **TTI**: 빠름 (클라이언트 번들 축소)
- **INP**: 우수

**장점**:
- 클라이언트 번들 크기 대폭 감소 (server-only 코드 제외)
- DB · 파일시스템 · 비밀키 직접 사용 가능 (서버에서만 실행)
- waterfall 자연스럽게 server-side 로 이동 → 네트워크 round-trip 감소
- SEO 강함

**단점**:
- 클라이언트 상호작용 영역은 명시적 분리 필요 (`'use client'`)
- mental model 학습 곡선 (server vs client 경계)
- 일부 라이브러리는 클라이언트 전용 (server 에서 깨짐)
- React 18 + Next.js App Router 등 한정된 런타임

**활용 예시**:
- Next.js 13+ App Router
- Vercel commerce template, Hashnode
- 데이터 헤비 페이지 (DB 직접 접근)
- Shopify Hydrogen v2

**Next.js RSC 예제**:
```tsx
// app/posts/page.tsx (server component - default)
import { db } from "@/lib/db";
import LikeButton from "./LikeButton";

// 서버에서만 실행 → DB 직접 호출, 비밀번호 등 노출 위험 없음
async function getPosts() {
  return db.query("SELECT id, title, likes FROM posts ORDER BY id DESC");
}

export default async function PostsPage() {
  const posts = await getPosts();
  return (
    <ul>
      {posts.map((p) => (
        <li key={p.id}>
          <h2>{p.title}</h2>
          {/* 인터랙티브 부분만 클라이언트 컴포넌트 */}
          <LikeButton postId={p.id} initial={p.likes} />
        </li>
      ))}
    </ul>
  );
}
```

```tsx
// app/posts/LikeButton.tsx
"use client"; // 클라이언트 컴포넌트 — JS 번들 포함

import { useState } from "react";

interface Props {
  postId: string;
  initial: number;
}

export default function LikeButton({ postId, initial }: Props) {
  const [count, setCount] = useState(initial);
  return (
    <button
      onClick={async () => {
        await fetch(`/api/posts/${postId}/like`, { method: "POST" });
        setCount(count + 1);
      }}
    >
      ♥ {count}
    </button>
  );
}
```

**관련 패턴**: [Streaming SSR](#streaming-ssr), [Islands Architecture](#islands-architecture), [Hydration](#hydration)

---

## 8. Hydration

<a id="hydration"></a>

**목적**: 서버에서 생성된 정적 HTML 에 클라이언트에서 이벤트 핸들러를 부착하여 인터랙티브로 만드는 메커니즘. SSR/SSG 의 필수 후속 단계.

**메커니즘**:
- 서버: HTML + 데이터 (직렬화된 props) 응답
- 브라우저: HTML paint → JS 번들 다운로드 → React 가 동일 컴포넌트 트리 재구성 → 기존 DOM 노드에 핸들러 attach (`hydrateRoot`)
- 컴포넌트 트리가 서버/클라이언트에서 동일해야 함 (불일치 → "hydration mismatch" 에러)
- 점진적 개선: selective hydration (React 18), partial hydration (Astro)

**Web Vitals 영향**:
- **TTFB**: -
- **FCP**: - (이미 HTML paint 완료)
- **LCP**: -
- **TTI**: **느림** — hydration 완료 전까지 인터랙션 불가
- **INP**: 영향 큼 — 큰 트리 hydration 은 main thread block

**장점**:
- SSR/SSG 의 빠른 첫 paint 와 SPA 의 풍부한 상호작용 결합
- 검색 엔진은 정적 HTML, 사용자는 인터랙티브 — 양쪽 만족
- 점진적 향상 (progressive enhancement)
- 서버/클라이언트 코드 공유 (isomorphic)

**단점**:
- "hydration tax" — 전체 트리를 클라이언트에서 다시 실행 → CPU 소모
- 인터랙티브 가능까지 지연 (uncanny valley: 보이지만 클릭 안 됨)
- 번들 크기와 hydration 시간 선형 비례
- mismatch 에러 (서버/클라이언트 결과 차이 — 시간/locale/random)

**활용 예시**:
- Next.js, Nuxt, Remix, Gatsby 모든 SSR/SSG
- React 18 `hydrateRoot` API
- selective hydration (Suspense + lazy)
- partial hydration (Astro islands)

**React Hydration 예제**:
```tsx
// 서버 (Express + React 18)
import express from "express";
import { renderToString } from "react-dom/server";
import App from "./App";

const app = express();
app.get("/", (req, res) => {
  const html = renderToString(<App user={{ name: "Alice" }} />);
  res.send(`
    <!DOCTYPE html>
    <html>
      <body>
        <div id="root">${html}</div>
        <script>
          window.__INITIAL_PROPS__ = ${JSON.stringify({ name: "Alice" })};
        </script>
        <script src="/client.js"></script>
      </body>
    </html>
  `);
});

// 클라이언트 (client.tsx)
import { hydrateRoot } from "react-dom/client";
import App from "./App";

// 서버와 동일한 props 로 hydration → 기존 DOM 에 핸들러만 attach
const initialProps = (window as { __INITIAL_PROPS__: { name: string } })
  .__INITIAL_PROPS__;
hydrateRoot(document.getElementById("root")!, <App user={initialProps} />);
```

**관련 패턴**: [SSR](#ssr), [Islands Architecture](#islands-architecture), [Resumability](#resumability)

---

## 9. Resumability

<a id="resumability"></a>

**목적**: Hydration 자체를 제거하는 새 패러다임. 서버에서 직렬화한 상태·이벤트 리스너 정보를 HTML 에 포함시키고, 브라우저는 필요한 순간에 해당 조각만 lazy-load 하여 "재개(resume)"합니다. O(1) startup.

**메커니즘**:
- 서버: 컴포넌트 트리 + 이벤트 리스너 위치 + 상태를 HTML 의 data-attribute 로 직렬화
- 브라우저: HTML paint → 사용자가 클릭하기 전까지 어떤 JS 도 실행하지 않음
- 사용자 인터랙션 발생 시 해당 핸들러 코드만 lazy import → 실행
- "Speculative loading" 으로 idle 시간에 미리 prefetch 가능
- Qwik 이 정립, qwik-city 가 framework

**Web Vitals 영향**:
- **TTFB**: 빠름
- **FCP**: 빠름
- **LCP**: 빠름
- **TTI**: **즉시** — hydration 비용 0
- **INP**: 인터랙션 시점에 lazy fetch (네트워크 의존, prefetch 로 완화)

**장점**:
- 페이지 크기와 무관하게 startup 시간 일정 (O(1))
- 모바일·저사양 환경에서 큰 이득
- JS 다운로드량 사용한 만큼만 (true lazy)
- SEO 우수

**단점**:
- 인터랙션 시점에 네트워크 fetch → 첫 클릭 지연 가능 (prefetch 필수)
- 라이브러리 호환성 낮음 (React/Vue 컴포넌트 직접 사용 어려움)
- 디버깅 도구·생태계 미성숙
- mental model 새로움 (use of `$` boundary)

**활용 예시**:
- 대형 콘텐츠 사이트 — Builder.io
- Qwik / qwik-city 기반 신규 프로젝트
- 모바일 우선 e-commerce
- HTML-first 접근

**Qwik 예제**:
```tsx
// src/routes/index.tsx (Qwik City)
import { component$, useSignal, $ } from "@builder.io/qwik";

export default component$(() => {
  const count = useSignal(0);

  // $ 경계: 이 핸들러는 첫 클릭 전까지 다운로드되지 않음
  const handleClick = $(() => {
    count.value++;
  });

  return (
    <div>
      <h1>Count: {count.value}</h1>
      <button onClick$={handleClick}>증가</button>
      {/* 페이지 paint 후 어떤 JS 도 실행 안됨 — 클릭 시 handleClick 만 lazy fetch */}
    </div>
  );
});
```

**관련 패턴**: [Hydration](#hydration), [Islands Architecture](#islands-architecture), [Streaming SSR](#streaming-ssr)

---

## 10. Edge Rendering

<a id="edge-rendering"></a>

**목적**: SSR/ISR/API 를 사용자와 가까운 edge 노드 (전 세계 수십~수백 지점) 에서 실행하여 RTT 를 최소화합니다. CDN POP 에서 V8 Isolates 로 컴퓨팅.

**메커니즘**:
- 코드를 Vercel Edge / Cloudflare Workers / Deno Deploy 등에 배포
- 요청 시 가장 가까운 PoP 가 라우팅 받음 (Anycast)
- V8 Isolates: Node.js 가 아닌 경량 sandbox, cold start ~5ms
- Web Standard API (Fetch, Request, Response, Streams) 사용 — Node API 사용 불가
- KV / D1 등 edge-native 스토리지 활용

**Web Vitals 영향**:
- **TTFB**: **매우 빠름** — 사용자와 물리적 거리 50~200km
- **FCP**: 빠름
- **LCP**: 빠름
- **TTI**: 빠름

**장점**:
- 전 세계 사용자에게 균등한 저지연
- cold start 매우 짧음 (V8 Isolates ~5ms vs Lambda ~수백ms)
- 무한 수평 확장 (PoP 가 자동 분산)
- DDoS 완화 (분산 흡수)

**단점**:
- 런타임 제약 — Node API 일부 미지원 (fs, net, child_process)
- 메모리·CPU 제한 (Cloudflare Workers 128MB / 50ms CPU 등)
- DB connection pool 어려움 — 매 요청마다 새 연결 시도 위험 (HTTP-based DB 권장: Neon, Planetscale, D1)
- 디버깅 어려움 (로컬 재현 한계)

**활용 예시**:
- API gateway / auth middleware (geo IP, A/B 분기)
- ISR + edge revalidation
- 글로벌 e-commerce 동적 라우팅
- Vercel Edge Functions, Cloudflare Workers, Deno Deploy, Netlify Edge Functions

**Cloudflare Workers / Vercel Edge 예제**:
```tsx
// app/api/geo/route.ts (Next.js Edge Runtime)
export const runtime = "edge"; // edge 에서 실행

export async function GET(req: Request): Promise<Response> {
  // geo 정보는 edge 헤더에 자동 포함
  const country = req.headers.get("x-vercel-ip-country") ?? "KR";
  const city = req.headers.get("x-vercel-ip-city") ?? "Seoul";

  // edge-native KV 조회 (예시)
  // const promo = await env.KV.get(`promo:${country}`);

  return new Response(
    JSON.stringify({
      country,
      city,
      message: `안녕하세요, ${city} 에서 접속하셨군요.`,
    }),
    { headers: { "content-type": "application/json" } },
  );
}
```

```ts
// Cloudflare Workers 예시 (별도 런타임)
export default {
  async fetch(request: Request, env: { KV: KVNamespace }): Promise<Response> {
    const country = (request as Request & { cf?: { country: string } }).cf
      ?.country;
    const cached = await env.KV.get(`landing:${country}`);
    if (cached) return new Response(cached, { headers: { "cache-control": "max-age=60" } });

    // origin fetch + KV 저장
    const origin = await fetch("https://origin.example.com/landing");
    const body = await origin.text();
    await env.KV.put(`landing:${country}`, body, { expirationTtl: 60 });
    return new Response(body);
  },
};
```

**관련 패턴**: [ISR](#isr), [SSR](#ssr), [Serverless Architecture](architectural.md)

> **관련 (P1 신설)**: 렌더링 전략은 측정으로 검증한다 — [`web-performance.md#core-web-vitals`](web-performance.md#core-web-vitals) (LCP/INP/CLS 게이트 기준) / [`web-performance.md#rum-monitoring`](web-performance.md#rum-monitoring) (실사용자 측정으로 SSR vs CSR 선택 검증).

---
