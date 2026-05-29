# 웹 성능 (Web Performance)

웹 성능 측정·진단·최적화의 표준 카탈로그. **Core Web Vitals** 4 종(LCP / INP / CLS + TBT)을 축으로, 브라우저 렌더링 파이프라인(Critical Rendering Path) · 자원 우선순위(Resource Hints / Priority Hints) · 실측 데이터 수집(RUM) · 합성 도구(Lighthouse / WebPageTest / PSI) · 번들 분석(Tree shaking / Code splitting / Module Federation) 을 다룹니다.

**원전·표준**:
- W3C Web Performance Working Group — https://www.w3.org/webperf/
  - Navigation Timing L2 / Resource Timing L3 / Paint Timing / Largest Contentful Paint / Event Timing / Layout Instability / Long Tasks
- Google Chrome `web.dev` — https://web.dev/vitals/
  - Core Web Vitals 정의, INP 전환(2024-03-12)
- Chrome Developer Documentation — https://developer.chrome.com/docs/web-platform/
- `web-vitals` 라이브러리 (GoogleChrome/web-vitals v4+) — https://github.com/GoogleChrome/web-vitals
- HTML Living Standard — https://html.spec.whatwg.org (Resource Hints, Priority Hints)
- Lighthouse — https://github.com/GoogleChrome/lighthouse
- WebPageTest — https://docs.webpagetest.org

**Core Web Vitals 변천사**:

| 시기 | 변경 |
|------|------|
| 2020-05 | Google, Core Web Vitals 발표 (LCP / FID / CLS) |
| 2021-06 | Page Experience Update 검색 랭킹 반영 시작 |
| 2022-05 | INP (Interaction to Next Paint) 실험 metric 공개 |
| 2023-05 | INP, "pending Core Web Vital" 로 격상 |
| **2024-03-12** | **INP 가 FID 대체 — FID deprecated, INP 공식 Core Web Vital** |
| 2024 이후 | LCP / INP / CLS 3 종이 공식 Core Web Vitals |

**관련 카탈로그**:
- [web-rendering.md](web-rendering.md) — CSR / SSR / SSG / Streaming (렌더링 전략별 Vitals 영향)
- [caching.md](caching.md) — CDN / Cache-Control / Service Worker (자원 전달 최적화)
- [observability.md](observability.md) — RUM 데이터 파이프라인, 알람
- [../principles/performance-metrics.md](../principles/performance-metrics.md) — 지표 일반론 (latency / throughput / percentile)

**의사결정 매트릭스**:

| 상황 | 우선 적용 |
|------|---------|
| LCP > 2.5s | preload, Priority Hints, image 최적화 (AVIF/WebP), SSR/SSG |
| INP > 200ms | Long Task 분할, `scheduler.yield()`, Web Worker offload |
| CLS > 0.1 | `width/height` 명시, `aspect-ratio`, `font-display: optional` |
| TBT > 200ms | code splitting, dynamic `import()`, tree shaking |
| 첫 방문 느림 | preconnect, dns-prefetch, HTTP/2 push 대신 103 Early Hints |
| 재방문 느림 | Service Worker, immutable cache, prefetch |
| 번들 비대 | Bundle Analyzer, Module Federation, route-level split |
| 측정 불일치 | Field (RUM) vs Lab (Lighthouse) 분리 진단 |

---

## 1. Core Web Vitals (LCP / FID / INP / CLS / TBT)

<a id="core-web-vitals"></a>

**정의 (Definition)**:
**Core Web Vitals** 는 사용자 체감 품질을 정량화한 Google 의 표준 지표 집합입니다. 2024-03-12 부로 **LCP / INP / CLS** 3 종이 공식 Core Web Vital 이며, FID 는 INP 로 대체되어 deprecated 되었습니다. TBT 는 Lab 측정용 보조 지표입니다.

| 지표 | 풀네임 | 측정 대상 | Good | Needs Improvement | Poor | Field 가능? |
|------|--------|----------|------|-------------------|------|-----------|
| **LCP** | Largest Contentful Paint | 최대 요소 paint 시각 | ≤2.5s | 2.5~4.0s | >4.0s | O |
| ~~FID~~ | First Input Delay | 첫 입력 처리 지연 | ≤100ms | 100~300ms | >300ms | O (deprecated) |
| **INP** | Interaction to Next Paint | 전 인터랙션 중 worst-case latency | ≤200ms | 200~500ms | >500ms | O |
| **CLS** | Cumulative Layout Shift | 누적 layout shift score | ≤0.1 | 0.1~0.25 | >0.25 | O |
| TBT | Total Blocking Time | Long Task blocking 누적 | ≤200ms | 200~600ms | >600ms | X (Lab only) |

**메커니즘 (Mechanism)**:

### 1.1 LCP (Largest Contentful Paint)

- **측정 대상**: viewport 안에서 가장 큰 텍스트 블록·이미지·video poster 가 paint 된 시각.
- **API**: `PerformanceObserver` + `largest-contentful-paint` entry type.
- **하위 분해**:
  1. TTFB (Time To First Byte) — 서버 응답
  2. Resource load delay — preload 늦음, render-blocking
  3. Resource load duration — 이미지 크기, 압축
  4. Element render delay — main thread blocked
- **개선 패턴**: `<link rel="preload" as="image" fetchpriority="high">`, AVIF/WebP, `loading="eager"`(LCP 이미지) / `lazy`(below-fold), SSR HTML, CDN.

### 1.2 FID → INP 전환 (2024-03-12)

- **FID 한계**: "첫 번째" 입력만 측정. 페이지 전체 인터랙션 품질을 대표하지 못함.
- **INP**: 페이지 전 생애 모든 click/tap/keyboard 인터랙션의 input → next paint 지연 중 worst (보통 98th percentile 근사).
- **INP 하위 분해**:
  1. Input delay — main thread busy, event handler 시작까지
  2. Processing time — event handler 실행
  3. Presentation delay — handler 종료 → next frame paint
- **개선 패턴**: Long Task 분할(`scheduler.yield()` / `setTimeout` / `MessageChannel`), Web Worker offload, debounce/throttle, React `useTransition`, 큰 컴포넌트 lazy mount.

### 1.3 CLS (Cumulative Layout Shift)

- **공식**: `impact fraction × distance fraction` 합, **session window** 기준 5 초 이내 묶음의 최대치 (2021-06 update).
- **유발 요인**: 이미지·iframe `width/height` 누락, 웹폰트 swap (FOUT), 광고 삽입, `position: sticky` 와 충돌, 동적 컨텐츠 prepend.
- **개선 패턴**: `<img width height>` 또는 CSS `aspect-ratio`, `font-display: optional`, skeleton placeholder, `min-height` reserve.

### 1.4 TBT (Total Blocking Time)

- Lab 전용 (RUM 측정 불가). TTI - FCP 구간에서 50ms 초과 Long Task 의 초과분 합산.
- INP 의 lab 근사치 — 50ms 임계 초과한 task 가 input delay 의 잠재 원인.

**측정 (Measurement)**:

```javascript
// web-vitals v4+ — 표준 측정 라이브러리
import { onCLS, onINP, onLCP, onFCP, onTTFB } from 'web-vitals';

onLCP(({ name, value, rating, id, navigationType, entries }) => {
  navigator.sendBeacon('/rum', JSON.stringify({ name, value, rating, id }));
});
onINP(report);
onCLS(report);
```

**예시 코드 (Example)** — 원시 PerformanceObserver:

```javascript
// LCP 직접 측정
const observer = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lcp = entries[entries.length - 1];
  console.log('LCP:', lcp.startTime, lcp.element);
});
observer.observe({ type: 'largest-contentful-paint', buffered: true });

// CLS 세션 윈도우 알고리즘
let clsValue = 0;
let sessionValue = 0;
let sessionEntries = [];
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.hadRecentInput) continue;
    const first = sessionEntries[0];
    const last = sessionEntries[sessionEntries.length - 1];
    if (sessionValue && entry.startTime - last.startTime < 1000 && entry.startTime - first.startTime < 5000) {
      sessionValue += entry.value;
      sessionEntries.push(entry);
    } else {
      sessionValue = entry.value;
      sessionEntries = [entry];
    }
    clsValue = Math.max(clsValue, sessionValue);
  }
}).observe({ type: 'layout-shift', buffered: true });
```

**INP 개선 — Long Task 분할**:

```javascript
// Bad: 50ms+ blocking
function processItems(items) {
  for (const item of items) heavyWork(item);
}

// Good: scheduler.yield() (Chrome 129+) 또는 setTimeout
async function processItems(items) {
  for (const item of items) {
    heavyWork(item);
    if (navigator.scheduling?.isInputPending()) {
      await (scheduler.yield?.() ?? new Promise(r => setTimeout(r, 0)));
    }
  }
}
```

**표준 인용 (Standard Reference)**:
- W3C Largest Contentful Paint — https://www.w3.org/TR/largest-contentful-paint/
- W3C Event Timing API — https://www.w3.org/TR/event-timing/ (INP 의 기반)
- W3C Layout Instability — https://www.w3.org/TR/layout-instability/
- web.dev "INP becomes a Core Web Vital on March 12, 2024" — https://web.dev/blog/inp-cwv-march-12

**관련 카탈로그**: [web-rendering.md](web-rendering.md) (SSR/SSG 가 LCP 영향), [../principles/performance-metrics.md](../principles/performance-metrics.md) (percentile 일반론)

---

## 2. Critical Rendering Path (CRP)

<a id="critical-rendering-path"></a>

**정의 (Definition)**:
**Critical Rendering Path** 는 브라우저가 HTML / CSS / JS 를 받아 픽셀로 변환하기까지의 단계: **HTML 파싱 → DOM 트리 → CSSOM 트리 → Render Tree → Layout → Paint → Composite**. 각 단계의 blocking 요인을 제거·지연시키는 것이 LCP/FCP 의 본질입니다.

**메커니즘 (Mechanism)**:

### 2.1 단계별 흐름

| 단계 | 입력 | 출력 | Blocking 요소 |
|------|------|------|-------------|
| 1. HTML 파싱 | bytes | DOM | `<script>` 동기 |
| 2. CSS 파싱 | CSS bytes | CSSOM | render-blocking (모든 CSS) |
| 3. Render Tree 구축 | DOM + CSSOM | Render Tree | DOM/CSSOM 완료 대기 |
| 4. Layout | Render Tree | 박스 모델 (위치/크기) | 큰 트리, reflow trigger |
| 5. Paint | Layout | 픽셀 비트맵 (layer 별) | 큰 영역, `box-shadow`/`filter` |
| 6. Composite | Layers | 최종 프레임 | GPU 합성, `will-change`/`transform` 유도 |

### 2.2 Render-blocking vs Parser-blocking

- **Render-blocking**: CSS 는 모두 render-blocking. CSSOM 완성 전까지 paint 안 됨.
  - 회피: critical CSS inline, `<link rel="stylesheet" media="print" onload="this.media='all'">` 트릭, `media="(min-width: 800px)"` 조건부.
- **Parser-blocking**: 동기 `<script>` 는 parser 를 멈춤.
  - 회피: `<script defer>` (DOM 완성 후 실행, 순서 보장), `<script async>` (로드 즉시 실행, 순서 없음), `type="module"` (기본 defer).

### 2.3 Reflow & Repaint

- **Reflow (Layout)**: 박스 크기/위치 변경 → 자식·이후 형제 재계산. `offsetWidth`, `getBoundingClientRect()` 등은 강제 동기 layout 유발.
- **Repaint**: 색상·visibility 변경. layout 없이 paint 만.
- **Composite-only**: `transform`, `opacity` → GPU layer 만 갱신. **60fps 애니메이션 핵심**.

**측정 (Measurement)**:

| 도구 | 측정 |
|------|------|
| Chrome DevTools Performance 탭 | Long Tasks, Layout shifts, Paint events |
| `performance.getEntriesByType('paint')` | FP, FCP timing |
| `PerformanceObserver({ type: 'longtask' })` | 50ms+ task |
| Lighthouse "Eliminate render-blocking resources" | blocking CSS/JS 리스트 |

**예시 코드 (Example)** — Critical CSS inline 패턴:

```html
<!doctype html>
<html>
<head>
  <!-- Above-the-fold critical CSS inline -->
  <style>
    body { font-family: system-ui; margin: 0; }
    .hero { height: 50vh; background: #0066cc; }
  </style>
  <!-- 나머지 CSS 는 비동기 로드 -->
  <link rel="preload" href="/main.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="/main.css"></noscript>
  <!-- JS defer -->
  <script src="/app.js" defer></script>
</head>
<body>
  <div class="hero"></div>
</body>
</html>
```

**Long Task 측정**:

```javascript
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.warn(`Long Task: ${entry.duration}ms`, entry.attribution);
  }
}).observe({ type: 'longtask', buffered: true });
```

**Composite-friendly 애니메이션**:

```css
/* Bad — reflow */
.box { left: 0; transition: left 0.3s; }
.box.move { left: 200px; }

/* Good — composite only */
.box { transform: translateX(0); transition: transform 0.3s; will-change: transform; }
.box.move { transform: translateX(200px); }
```

**표준 인용 (Standard Reference)**:
- HTML Living Standard "Parsing HTML documents" — https://html.spec.whatwg.org/multipage/parsing.html
- web.dev "Critical rendering path" — https://web.dev/learn/performance/understanding-the-critical-path
- Chrome DevTools "Performance features reference" — https://developer.chrome.com/docs/devtools/performance/reference

**관련 카탈로그**: [web-rendering.md](web-rendering.md) (Streaming SSR 이 CRP 단축), [caching.md](caching.md) (CSS/JS 캐시 전략)

---

## 3. Resource Hints & Priority Hints

<a id="resource-hints"></a>

**정의 (Definition)**:
**Resource Hints** 는 브라우저에게 향후 필요한 자원을 미리 알려 DNS/TCP/TLS 비용·다운로드 시점을 앞당기는 `<link>` 지시문 모음. **Priority Hints (`fetchpriority`)** 는 동일 자원군 내 상대 우선순위를 명시. **103 Early Hints** 는 서버가 본 응답 전에 hint 만 먼저 보내는 HTTP 응답.

**5 종 + Priority Hint + Early Hints 비교**:

| Hint | 효과 | 비용 | 적용 시점 |
|------|------|------|---------|
| `dns-prefetch` | DNS lookup 만 미리 | 매우 낮음 | 3rd-party 도메인 (사용 가능성 중간) |
| `preconnect` | DNS + TCP + TLS | 낮음 (소켓 점유) | 곧 사용 확실한 origin |
| `preload` | 현재 페이지 critical 자원 다운로드 | 중간 (대역폭) | LCP 이미지, font, critical CSS |
| `modulepreload` | ES module + 의존 module 그래프 | 중간 | dynamic import 예정 module |
| `prefetch` | 다음 navigation 자원 (low priority) | 중간 | 다음 페이지 예측 |
| `fetchpriority` | 동일 자원군 내 우선순위 | 0 | LCP 이미지 vs decorative 이미지 |
| `103 Early Hints` | 서버 처리 중 hint 만 미리 송신 | 0 (HTTP/2/3) | TTFB 길 때 가장 강력 |

**메커니즘 (Mechanism)**:

### 3.1 `dns-prefetch` / `preconnect`

- `dns-prefetch`: A/AAAA 쿼리만. ~수십 ms 절약.
- `preconnect`: DNS + TCP handshake (1 RTT) + TLS (1~2 RTT). ~수백 ms 절약 가능. **3 rd-party origin 4 ~ 6 개 이하**로 제한 (소켓 비용).

### 3.2 `preload` (current navigation)

- `as` 속성 필수 (`image` / `font` / `style` / `script` / `fetch`). 잘못된 `as` → 두 번 다운로드.
- `crossorigin` 속성 — font/fetch 는 필수.
- LCP 이미지에 `preload + fetchpriority="high"` 결합이 핵심.

### 3.3 `modulepreload`

- ES module + 그 import graph 까지 미리 가져옴. `<link rel="preload" as="script">` 와 달리 module compile 단계까지 진행.

### 3.4 `prefetch`

- low priority, idle network 사용. 다음 navigation 예측 (homepage → product page).
- 주의: 미사용 prefetch 는 데이터 비용.

### 3.5 `fetchpriority` (Priority Hints)

- 2023 표준화. `high` / `low` / `auto`. 자원 종류별 기본 우선순위를 override.
- LCP 이미지: `<img fetchpriority="high">` — Lighthouse "Image elements do not have explicit width and height" 와 함께 자주 권장.
- Hero 외 below-fold 이미지: `loading="lazy"` + `fetchpriority="low"`.

### 3.6 `103 Early Hints` (HTTP)

- 서버가 본 응답 작성 동안 `103 Early Hints` 응답으로 `Link: </main.css>; rel=preload; as=style` 헤더 미리 송신.
- Chrome 103+ (2022-06), Cloudflare/Fastly/Vercel 지원. **TTFB 가 길 때 가장 효과적** (DB query 100~500ms 동안 브라우저는 이미 자원 가져옴).

**측정 (Measurement)**:

- Chrome DevTools Network 탭 "Initiator" 컬럼 — preload/prefetch 로 시작된 자원 확인.
- Lighthouse "Preconnect to required origins", "Preload key requests" 감사.
- `PerformanceResourceTiming.initiatorType === 'link'` 로 RUM 추적.

**예시 코드 (Example)**:

```html
<!doctype html>
<html>
<head>
  <!-- 3rd-party origin: DNS+TCP+TLS 미리 -->
  <link rel="preconnect" href="https://cdn.example.com" crossorigin>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="dns-prefetch" href="https://analytics.example.com">

  <!-- LCP 이미지 preload + 최고 우선순위 -->
  <link rel="preload" as="image" href="/hero.avif"
        imagesrcset="/hero-800.avif 800w, /hero-1600.avif 1600w"
        imagesizes="100vw" fetchpriority="high">

  <!-- Font preload (crossorigin 필수) -->
  <link rel="preload" as="font" type="font/woff2"
        href="/Inter.woff2" crossorigin>

  <!-- 다음 페이지 예측 prefetch -->
  <link rel="prefetch" href="/checkout.html">

  <!-- Module preload -->
  <link rel="modulepreload" href="/checkout.mjs">
</head>
<body>
  <img src="/hero.avif" fetchpriority="high" width="1600" height="900" alt="...">
  <img src="/below-fold.avif" loading="lazy" fetchpriority="low" width="800" height="600" alt="...">
</body>
</html>
```

**서버측 103 Early Hints (Node.js)**:

```javascript
// Node.js 18+ http
server.on('request', (req, res) => {
  res.writeEarlyHints({
    link: [
      '</main.css>; rel=preload; as=style',
      '</hero.avif>; rel=preload; as=image; fetchpriority=high',
    ],
  });
  // 이후 DB 쿼리 등 비동기 작업
  setTimeout(() => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(html);
  }, 200);
});
```

**표준 인용 (Standard Reference)**:
- W3C Resource Hints — https://www.w3.org/TR/resource-hints/
- WHATWG HTML "Link types" — https://html.spec.whatwg.org/multipage/links.html#linkTypes
- Priority Hints (web.dev) — https://web.dev/articles/fetch-priority
- RFC 8297 "An HTTP Status Code for Indicating Hints" — https://datatracker.ietf.org/doc/html/rfc8297

**관련 카탈로그**: [caching.md](caching.md) (preload 후 캐시 hit), [web-rendering.md](web-rendering.md) (SSR 과 103 Early Hints 결합)

---

## 4. RUM (Real User Monitoring)

<a id="rum-monitoring"></a>

**정의 (Definition)**:
**RUM (Real User Monitoring)** 은 실제 사용자 브라우저에서 수집한 Field 데이터로, Lab(합성) 측정이 잡지 못하는 디바이스·네트워크·지역 분포 차이를 반영합니다. **Performance Observer API** 와 **`web-vitals` 라이브러리**가 표준. Field vs Lab 의 불일치 진단이 핵심.

**Field vs Lab**:

| 구분 | Field (RUM) | Lab (Synthetic) |
|------|------------|----------------|
| 출처 | 실사용자 | 통제된 환경 (Lighthouse, WPT) |
| 디바이스 | 실제 분포 (저가 안드로이드 포함) | 시뮬 (Moto G Power 등) |
| 네트워크 | 실제 (4G/5G/Wi-Fi/3G) | Throttled 4G 등 |
| 지역 | 글로벌 | 단일 region |
| INP 측정 | O (전 인터랙션) | X (Lab 은 TBT 로 근사) |
| 대표성 | 높음 (대량) | 재현성 높음 |
| 용도 | SLO/SLI, 회귀 탐지 | 변경 전후 비교, CI |

**메커니즘 (Mechanism)**:

### 4.1 `PerformanceObserver` API

- entry types: `navigation` / `resource` / `paint` / `largest-contentful-paint` / `layout-shift` / `event` / `first-input` / `longtask` / `mark` / `measure` / `element` / `long-animation-frame` (2024).
- `buffered: true` — observer 등록 전 발생한 entry 도 받기.

### 4.2 `web-vitals` v4 라이브러리

- Google 공식. Core Web Vitals 의 표준 측정 알고리즘(세션 윈도우 CLS, INP percentile 등) 캡슐화.
- `onLCP / onINP / onCLS / onFCP / onTTFB` — 페이지 visibility hidden / pagehide 시점에 final value 호출.
- `attribution` 빌드 — INP/LCP/CLS 의 원인 요소까지 (LCP element, INP event target, CLS source).

### 4.3 전송 패턴

- `navigator.sendBeacon()` — visibility change/pagehide 시점에서도 신뢰성 있게 송신 (fetch 와 달리 unload race condition 없음).
- `visibilitychange` 이벤트 — `hidden` 시점 final value 전송.
- batching — 페이지 종료 직전 한 번에 묶어 전송.

### 4.4 Chrome UX Report (CrUX)

- Chrome 사용자 28-day rolling field data. Origin 단위/page 단위 percentile.
- BigQuery (`chrome-ux-report.all.YYYYMM`), PageSpeed Insights API, CrUX API.
- p75 기준으로 Core Web Vitals "Pass" 판정 (LCP p75 ≤ 2.5s 등).

**측정 (Measurement)**:

- 최소 sample size: page view 75 백분위 안정화 ~10 k+ 권장.
- 차원 분리: device (mobile/desktop), connection (4g/3g), country, page template.
- p75 / p95 / p99 분포 함께 추적 (평균값 함정 회피).

**예시 코드 (Example)** — web-vitals v4 + Beacon:

```javascript
import { onLCP, onINP, onCLS, onFCP, onTTFB } from 'web-vitals/attribution';

function sendToAnalytics(metric) {
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,            // 'good' | 'needs-improvement' | 'poor'
    id: metric.id,
    navigationType: metric.navigationType,
    delta: metric.delta,
    attribution: metric.attribution,  // INP target, LCP element selector 등
    deviceMemory: navigator.deviceMemory,
    connection: navigator.connection?.effectiveType,
    url: location.href,
  });
  (navigator.sendBeacon && navigator.sendBeacon('/rum', body)) ||
    fetch('/rum', { body, method: 'POST', keepalive: true });
}

onLCP(sendToAnalytics);
onINP(sendToAnalytics);
onCLS(sendToAnalytics);
onFCP(sendToAnalytics);
onTTFB(sendToAnalytics);
```

**Long Animation Frame (LoAF) — 2024 신규**:

```javascript
// 50ms 이상의 frame 정체와 그 원인 script 추적 (INP 디버깅 핵심)
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('LoAF', entry.duration, entry.blockingDuration, entry.scripts);
  }
}).observe({ type: 'long-animation-frame', buffered: true });
```

**SLO 예시**:

```
SLO: 75 백분위 LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1
SLI: 28 일 rolling window, mobile 기기 한정
경보: p75 LCP > 2.5s 가 24h 지속 → on-call
```

**표준 인용 (Standard Reference)**:
- W3C Performance Timeline L2 — https://www.w3.org/TR/performance-timeline/
- W3C Resource Timing L3 — https://www.w3.org/TR/resource-timing-3/
- web.dev "Field data vs lab data" — https://web.dev/articles/lab-and-field-data-differences
- Chrome UX Report — https://developer.chrome.com/docs/crux

**관련 카탈로그**: [observability.md](observability.md) (RUM 데이터 파이프라인, SLO/SLI), [../principles/performance-metrics.md](../principles/performance-metrics.md) (percentile / histogram)

---

## 5. Lighthouse / WebPageTest / PageSpeed Insights

<a id="lighthouse-webpagetest"></a>

**정의 (Definition)**:
합성(Synthetic) 측정 도구 3 종. **Lighthouse** 는 단일 페이지 audit (Chrome DevTools / CLI / CI), **WebPageTest** 는 전 세계 실디바이스 분산 테스트, **PageSpeed Insights** 는 Lighthouse Lab + CrUX Field 데이터 결합. 변경 전후 비교·CI 회귀 방지에 사용.

**3 도구 비교**:

| 항목 | Lighthouse | WebPageTest | PSI |
|------|-----------|-------------|-----|
| 측정 | Lab | Lab (실디바이스) | Lab + Field (CrUX) |
| 디바이스 | Chrome 시뮬 | 전 세계 실기기 (Moto G4, iPhone 등) | Chrome 시뮬 + CrUX |
| 지역 | 1 (실행 위치) | 30+ region | 1 (실행) + Field 글로벌 |
| 회귀 | CI plugin (lighthouse-ci) | API 자동화 | CI 직접 지원 X |
| Filmstrip | 제한적 | 6 단계 frame-by-frame | 제한적 |
| 무료 | O | O (제한) + 유료 plan | O (rate-limited) |
| 비용 분석 | TBT, JS coverage | Bytes-in, requests, waterfall | Lighthouse 동일 |

**메커니즘 (Mechanism)**:

### 5.1 Lighthouse

- **5 카테고리**: Performance / Accessibility / Best Practices / SEO / PWA.
- **Performance score (v10+)**: FCP 10% + SI 10% + LCP 25% + TBT 30% + CLS 25%. **INP 는 아직 score 포함 안 됨 (Field only)**.
- **CLI**: `npx lighthouse https://example.com --output=json --output-path=./report.json --chrome-flags="--headless"`.
- **lighthouse-ci**: PR 별 회귀 탐지. `.lighthouserc.json` 으로 budget assert.

### 5.2 WebPageTest

- **First View / Repeat View** 자동 비교 — 캐시 효과 측정.
- **Filmstrip / Speed Index / Visual Complete** — 시각 진행도.
- **Carbon Control** — 탄소 배출 추정 (Sustainable Web Design).
- **API**: `https://www.webpagetest.org/runtest.php?url=...&k=API_KEY&f=json`.

### 5.3 PageSpeed Insights (PSI)

- Lighthouse Lab 결과 + CrUX Field 데이터 (origin/url, 28-day p75) 동시 표시.
- **공식 판정**: CrUX p75 가 모두 Good → "Core Web Vitals Assessment: Passed".
- API: `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=...&strategy=mobile`.

**측정 (Measurement)** — Performance Budget 패턴:

| 지표 | Budget |
|------|--------|
| LCP | ≤ 2.5s |
| TBT | ≤ 200ms |
| CLS | ≤ 0.1 |
| Total bytes | ≤ 1 MB |
| JS bytes | ≤ 300 KB |
| Image bytes | ≤ 500 KB |
| Lighthouse Performance score | ≥ 90 |

**예시 코드 (Example)** — `.lighthouserc.json` CI:

```json
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000/", "http://localhost:3000/product"],
      "numberOfRuns": 3,
      "settings": { "preset": "desktop" }
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.9 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "total-blocking-time": ["error", { "maxNumericValue": 200 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "resource-summary:script:size": ["warn", { "maxNumericValue": 300000 }]
      }
    },
    "upload": { "target": "temporary-public-storage" }
  }
}
```

**WebPageTest API 자동화 (Node.js)**:

```javascript
const WPT = require('webpagetest');
const wpt = new WPT('www.webpagetest.org', process.env.WPT_API_KEY);

wpt.runTest('https://example.com', {
  location: 'Dulles_MotoG4:Chrome',
  connectivity: '4G',
  runs: 3,
  firstViewOnly: false,
  video: true,
  pollResults: 5,
}, (err, data) => {
  console.log('Speed Index:', data.data.average.firstView.SpeedIndex);
  console.log('LCP:', data.data.average.firstView.chromeUserTiming.LargestContentfulPaint);
});
```

**PSI API**:

```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?\
url=https://example.com&strategy=mobile&category=performance&key=$PSI_KEY"
```

**표준 인용 (Standard Reference)**:
- Lighthouse Scoring Calculator — https://googlechrome.github.io/lighthouse/scorecalc/
- Lighthouse architecture — https://github.com/GoogleChrome/lighthouse/blob/main/docs/architecture.md
- WebPageTest Documentation — https://docs.webpagetest.org
- PageSpeed Insights API — https://developers.google.com/speed/docs/insights/v5/get-started

**관련 카탈로그**: [../principles/performance-metrics.md](../principles/performance-metrics.md) (Lab metric 한계), [observability.md](observability.md) (CI 회귀 알람)

---

## 6. Bundle Analysis (Tree shaking / Code splitting / Module Federation)

<a id="bundle-analysis"></a>

**정의 (Definition)**:
JavaScript 번들의 크기·구성을 분석하고 줄이는 기법군. **Tree shaking** (미사용 export 제거), **Code splitting** (route/component 단위 분할), **Bundle Analyzer / Source Map Explorer** (시각화), **Module Federation** (런타임 micro-frontend 공유). TBT/INP 의 1 차 원인인 JS 실행 시간 단축이 목표.

**4 기법 비교**:

| 기법 | 목적 | 도구 | 효과 |
|------|------|------|------|
| Tree shaking | 미사용 코드 제거 | Webpack 5+, Rollup, esbuild, Vite | 10~40% bundle 감소 |
| Code splitting | route/feature 단위 분할 | `import()`, React.lazy, Vite dynamic | 초기 bundle 50%+ 감소 |
| Bundle Analyzer | 시각화 | webpack-bundle-analyzer, rollup-plugin-visualizer | 진단 |
| Source Map Explorer | 실배포 bundle 진단 | source-map-explorer | 실제 배포 진단 |
| Module Federation | 런타임 module 공유 | Webpack 5 ModuleFederationPlugin, Vite plugin | micro-frontend 중복 제거 |

**메커니즘 (Mechanism)**:

### 6.1 Tree shaking

- **전제**: ES module (`import` / `export`). CommonJS (`require`) 는 tree-shaking 불가능.
- **`sideEffects: false`** (package.json) — bundler 에게 부수효과 없음 보장.
- **Re-export 함정**: `export * from './big-lib'` 는 전체 포함. `export { x } from './big-lib'` 로 명시.
- **lodash 함정**: `import _ from 'lodash'` ❌ → `import debounce from 'lodash/debounce'` 또는 `lodash-es` ✓.

### 6.2 Code splitting

- **Route-level**: 라우터별 lazy load — React Router `lazy()`, Next.js 자동.
- **Component-level**: heavy modal/chart 만 lazy.
- **Vendor split**: `node_modules` 를 별도 chunk — 캐시 친화 (앱 코드만 변경 시 vendor 캐시 hit).
- **Dynamic import + prefetch**: `import(/* webpackPrefetch: true */ './heavy')` — idle 시 prefetch.

### 6.3 Bundle Analyzer

- **webpack-bundle-analyzer**: treemap 시각화. chunk 별 module 크기.
- **rollup-plugin-visualizer**: Vite/Rollup. `template: 'treemap' | 'sunburst' | 'network'`.
- **source-map-explorer**: 배포된 bundle + source map 으로 진단 (CI 와 결합).

### 6.4 Module Federation (Webpack 5)

- 런타임 module 공유 — host 가 remote 의 module 을 fetch 하여 실행.
- **공유 의존성** — React/Vue 등을 host/remote 가 singleton 으로 공유, 중복 제거.
- 사용 사례: micro-frontend (각 팀이 독립 배포), shared design system, plugin architecture.
- **트레이드오프**: 런타임 fetch 비용, 버전 호환 관리.

**측정 (Measurement)**:

| 지표 | 도구 | Budget |
|------|------|--------|
| Initial JS (gzip) | webpack-bundle-analyzer | ≤ 170 KB (mobile 3G) |
| Initial JS (uncompressed) | source-map-explorer | ≤ 500 KB |
| 3rd-party JS | Lighthouse "Reduce 3rd-party" | ≤ 30% of total |
| Unused JS | Chrome Coverage 탭 | ≤ 30% |
| Compile time | Web Vitals JS exec time | ≤ 350ms (mid-tier mobile) |

**예시 코드 (Example)** — Vite + bundle analyzer:

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    visualizer({ filename: 'stats.html', template: 'treemap', gzipSize: true }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          vendor: ['lodash-es', 'date-fns'],
        },
      },
    },
  },
});
```

**React + Route-level split**:

```javascript
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

const Home = lazy(() => import('./Home'));
const Product = lazy(() => import(/* webpackPrefetch: true */ './Product'));

export default function App() {
  return (
    <Suspense fallback={<Skeleton />}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/product/:id" element={<Product />} />
      </Routes>
    </Suspense>
  );
}
```

**Webpack 5 Module Federation**:

```javascript
// host webpack.config.js
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'host',
      remotes: {
        checkout: 'checkout@https://cdn.example.com/checkout/remoteEntry.js',
      },
      shared: {
        react: { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
  ],
};

// 사용
const Checkout = React.lazy(() => import('checkout/CheckoutPage'));
```

**source-map-explorer (배포 후 진단)**:

```bash
npx source-map-explorer 'build/static/js/*.js' --html report.html
```

**Tree shaking 검증 — `sideEffects`**:

```json
{
  "name": "my-lib",
  "sideEffects": false,
  "//": "또는 CSS import 같은 부수효과만 한정",
  "sideEffects": ["*.css", "./src/polyfills.js"]
}
```

**표준 인용 (Standard Reference)**:
- ECMAScript Modules (ES2015+) — https://tc39.es/ecma262/#sec-modules
- Webpack Tree Shaking — https://webpack.js.org/guides/tree-shaking/
- Webpack Module Federation — https://webpack.js.org/concepts/module-federation/
- web.dev "Reduce JavaScript payloads" — https://web.dev/articles/reduce-javascript-payloads-with-code-splitting

**관련 카탈로그**: [web-rendering.md](web-rendering.md) (Islands/RSC 가 bundle 자체를 줄임), [caching.md](caching.md) (chunk 캐시 immutable), [build-versioning.md](build-versioning.md) (chunk hash 전략)

---

## 종합 의사결정 트리

```
┌── LCP > 2.5s ?
│   ├─ Yes → preload LCP image + fetchpriority="high"
│   │       → SSR/SSG, 103 Early Hints
│   │       → CDN, AVIF/WebP, image CDN
│   └─ No  → continue
│
├── INP > 200ms ?
│   ├─ Yes → Long Task 분할 (scheduler.yield)
│   │       → Web Worker offload
│   │       → React useTransition, debounce
│   └─ No  → continue
│
├── CLS > 0.1 ?
│   ├─ Yes → width/height, aspect-ratio
│   │       → font-display: optional
│   │       → skeleton placeholder
│   └─ No  → continue
│
├── TBT > 200ms ?
│   ├─ Yes → Bundle Analyzer로 큰 모듈 찾기
│   │       → tree shaking, code splitting
│   │       → 3rd-party JS 제거/지연
│   └─ No  → continue
│
└── Field vs Lab 불일치 ?
    └─ RUM 분포 확인 (device/network/region)
       → CrUX 비교
       → 저성능 segment 별도 최적화
```

---

## Anti-pattern Lookup

| Anti-pattern | 영향 지표 | 카탈로그 |
|--------------|----------|---------|
| 동기 `<script>` head 배치 | LCP, FCP | [anti-patterns.md](anti-patterns.md) |
| `import _ from 'lodash'` | Bundle, TBT | [anti-patterns.md](anti-patterns.md) |
| 이미지 `width/height` 누락 | CLS | [anti-patterns.md](anti-patterns.md) |
| `requestAnimationFrame` 내 reflow trigger | INP | [anti-patterns.md](anti-patterns.md) |
| preload `as` 불일치 (중복 다운로드) | 대역폭 | [anti-patterns.md](anti-patterns.md) |
| 60+ preconnect | 소켓 고갈 | [anti-patterns.md](anti-patterns.md) |
| RUM 평균값만 추적 (p75/p95 무시) | SLO 오판 | [observability.md](observability.md) |

---

**다음 단계 (Further Reading)**:
- [web-rendering.md](web-rendering.md) — CSR/SSR/SSG/RSC/Islands/Resumability 전략별 Vitals 영향
- [caching.md](caching.md) — Cache-Control, immutable, Service Worker, stale-while-revalidate
- [observability.md](observability.md) — RUM 파이프라인, SLO/SLI, 알람 임계
- [../principles/performance-metrics.md](../principles/performance-metrics.md) — percentile / histogram / Apdex 일반론
- [networking.md](networking.md) — HTTP/2 multiplexing, HTTP/3 QUIC, TLS 1.3 0-RTT
- [build-versioning.md](build-versioning.md) — chunk hash, long-term caching
