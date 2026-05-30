# 네트워크 / 프로토콜 패턴 (Network & Protocol Patterns)

Transport 계층부터 Application 계층까지의 정평 있는 12 패턴/프로토콜. **분산 시스템**·**API 스타일**·**스트리밍 의미론** 의 하부 계층.

**원전 참고**:
- Andrew S. Tanenbaum — *Computer Networks*, 5th/6th ed.
- W. Richard Stevens — *TCP/IP Illustrated*, Vol. 1~3
- IETF RFC 9000 (QUIC), RFC 9110-9114 (HTTP semantics / HTTP/1.1 / HTTP/2 / HTTP/3), RFC 8446 (TLS 1.3), RFC 8445 (ICE)

**관련 카탈로그**:
- [distributed.md](distributed.md) — API Gateway / Service Mesh / BFF
- [reliability.md](reliability.md) — Circuit Breaker / Retry / Timeout (transport 무관)
- [`../security/security-crypto-ops.md`](../security/security-crypto-ops.md) — mTLS, PFS
- [`../security/security-api-web.md`](../security/security-api-web.md) — CSP / SRI / HSTS / CORS

---

<a id="tcp-udp"></a>

## 1. TCP vs UDP

**목적/정의**: 인터넷 transport 계층의 두 축. TCP (RFC 9293) 는 신뢰성 있는 순서 보장 byte stream 을 제공하고, UDP (RFC 768) 는 connectionless 한 비신뢰 datagram 을 제공합니다. 상위 프로토콜(HTTP, TLS, QUIC, DNS, RTP) 선택의 출발점.

**메커니즘**:
- **TCP**: 3-way handshake (SYN / SYN-ACK / ACK) → sequence number + ACK 기반 신뢰성 → in-order delivery → flow control (receive window) → congestion control → 4-way teardown (FIN). Head-of-line (HoL) blocking: 한 segment loss 가 stream 전체 지연
- **UDP**: 8-byte 헤더 (src/dst port, length, checksum) 뿐. 순서·재전송·혼잡 제어 없음. 상위 계층이 자유롭게 의미론 구축
- TCP 는 stateful (kernel 의 socket buffer + TCB), UDP 는 거의 stateless
- 양쪽 모두 16-bit port (0-65535) 로 다중화

**장점**:
- TCP: 애플리케이션이 신뢰성·순서 보장을 무료로 획득. 광범위한 NAT/방화벽 통과
- UDP: 헤더 오버헤드 최소, 1-RTT 미만 전송, 멀티캐스트 가능, 상위가 의미론 통제 (지연 vs 신뢰성 트레이드오프 자유)

**단점·트레이드오프**:
- TCP: HoL blocking, handshake 비용 (특히 짧은 요청), Nagle/delayed ACK 상호작용으로 latency 폭증 가능
- UDP: 신뢰성 직접 구현 필요, NAT/방화벽 차단 흔함, amplification attack 표적

**활용 예시**:
- TCP: HTTP/1.1·HTTP/2, TLS, SSH, SMTP, gRPC over HTTP/2, 대부분의 DB 프로토콜 (PostgreSQL, MySQL, Redis RESP)
- UDP: DNS (53), QUIC/HTTP/3, RTP/SRTP (WebRTC media), DTLS, NTP (123), QUIC 기반 모든 트래픽, 게임 (Fortnite, League of Legends)

**난이도**: 중간

**Kotlin / pseudo-code 예제**:
```kotlin
// TCP — Ktor / OkHttp 는 내부적으로 java.net.Socket 사용
import java.net.Socket
import java.net.DatagramSocket
import java.net.DatagramPacket
import java.net.InetAddress

fun tcpEcho(host: String, port: Int, msg: String): String =
    Socket(host, port).use { sock ->
        sock.getOutputStream().write(msg.toByteArray())
        sock.getInputStream().bufferedReader().readLine() // ordered, reliable
    }

// UDP — 손실/순서 뒤바뀜 가능, 애플리케이션이 처리
fun udpSend(host: String, port: Int, msg: String) {
    DatagramSocket().use { ds ->
        val buf = msg.toByteArray()
        val pkt = DatagramPacket(buf, buf.size, InetAddress.getByName(host), port)
        ds.send(pkt) // fire-and-forget
    }
}
```

**관련 패턴**: [TCP Congestion Control](#tcp-congestion-control), [QUIC / HTTP/3](#quic-http3), [Reliable UDP](#reliable-udp), [Connection Pooling](#connection-pooling)

---

<a id="tcp-congestion-control"></a>

## 2. TCP Congestion Control

**목적/정의**: 네트워크 혼잡 시 송신 속도를 동적으로 조절하여 collapse 를 막고 공정성을 유지하는 알고리즘 군. RFC 5681 (TCP Congestion Control) + 후속 RFC 에 명시. Reno → NewReno → CUBIC (RFC 9438) → BBR 로 진화.

**메커니즘**:
- 핵심 변수: `cwnd` (congestion window), `ssthresh` (slow-start threshold), `rwnd` (receiver window)
- **Slow Start**: `cwnd` 가 매 RTT 마다 2배 증가 (지수). `cwnd >= ssthresh` 가 되면 Congestion Avoidance 진입
- **Congestion Avoidance (AIMD)**: Additive Increase (RTT 당 +1 MSS) / Multiplicative Decrease (loss 시 cwnd 반감)
- **Fast Retransmit / Fast Recovery (Reno/NewReno)**: 3 duplicate ACK 수신 → retransmit + cwnd 반감 (timeout 까지 기다리지 않음)
- **CUBIC** (Linux default since 2.6.19): cwnd 를 시간의 3차 함수로 모델링, 고대역폭·고지연 link 에서 Reno 대비 throughput 우수
- **BBR** (Google, 2016): loss-based 가 아니라 bottleneck bandwidth + RTprop (min RTT) 추정 기반. bufferbloat 환경에서 강함

**장점**:
- 네트워크 안정성 (congestion collapse 회피)
- BBR/CUBIC 은 long fat network 에서 throughput 크게 향상

**단점·트레이드오프**:
- Loss-based (Reno/CUBIC) 는 random loss 환경 (무선) 에서 throughput 저하
- BBR v1 은 CUBIC 과 공존 시 unfair (BBR 이 더 많이 차지). BBR v2/v3 가 개선
- 튜닝(initial cwnd, ssthresh)은 OS/커널 단위 → 애플리케이션 제어 제한적

**활용 예시**:
- Linux 4.9+ 에서 BBR 사용 가능 (`net.ipv4.tcp_congestion_control=bbr`)
- Google internal traffic 대부분 BBR
- macOS / Windows: CUBIC 기본
- YouTube, Spotify, Akamai 등 video streaming 은 BBR 채택률 높음

**난이도**: 높음

**Kotlin / pseudo-code 예제**:
```kotlin
// 의사코드: AIMD core loop (Reno 단순화)
class RenoState(var cwnd: Double = 1.0, var ssthresh: Double = 64.0)

fun onAck(s: RenoState, mss: Int) {
    if (s.cwnd < s.ssthresh) {
        s.cwnd += 1.0           // slow start: exponential per RTT
    } else {
        s.cwnd += 1.0 / s.cwnd  // congestion avoidance: linear per RTT
    }
}

fun onLoss(s: RenoState) {
    s.ssthresh = maxOf(s.cwnd / 2.0, 2.0)
    s.cwnd = s.ssthresh          // fast recovery (NewReno: cwnd = ssthresh + 3)
}

// 운영: Linux 에서 BBR 활성화
// echo bbr | sudo tee /proc/sys/net/ipv4/tcp_congestion_control
```

**관련 패턴**: [TCP vs UDP](#tcp-udp), [Reliable UDP / KCP](#reliable-udp), [Connection Pooling](#connection-pooling)

---

<a id="quic-http3"></a>

## 3. QUIC / HTTP/3

**목적/정의**: TCP+TLS 를 대체하기 위해 UDP 위에 multiplexing·암호화·신뢰성·혼잡 제어를 통합한 transport. IETF RFC 9000 (QUIC), RFC 9001 (TLS 매핑), RFC 9002 (Loss detection & congestion control). HTTP/3 (RFC 9114) 는 QUIC 위 HTTP 매핑.

**메커니즘**:
- UDP 위 user-space transport — 커널 교체 없이 빠른 진화 가능
- Connection 당 다수 stream → 한 stream 의 loss 가 다른 stream 을 막지 않음 (HoL blocking 해소)
- TLS 1.3 통합 → 1-RTT handshake. 재접속 시 0-RTT resumption (단, replay 위험 존재해서 idempotent GET 에만 권장)
- Connection ID (변하지 않는 ID) → IP 변경에도 connection 유지 (mobile WiFi → cellular 전환 시 끊김 없음 = connection migration)
- HTTP/3: HTTP semantics 동일, 헤더 압축은 QPACK (HPACK 의 HoL-free 변형)

**장점**:
- HoL blocking 해소 → 다중 자원 페이지 로딩 가속
- 0-RTT/1-RTT 로 handshake 비용 절감
- Connection migration → mobile 환경 강점
- 암호화 강제 → downgrade attack 방어

**단점·트레이드오프**:
- UDP 차단/throttling 흔한 기업/통신사 환경에서 폴백 (HTTP/2 over TCP) 필요
- User-space 처리 → CPU 비용 TCP 대비 1.5~2× (커널 offload 미성숙)
- Middlebox 호환성 (NAT timeout, load balancer)

**활용 예시**:
- Cloudflare, Google (YouTube, Search), Meta (Facebook, Instagram) 의 edge 트래픽 상당수
- Chrome / Firefox / Safari / Edge 기본 지원
- 라이브러리: ngtcp2, quiche (Cloudflare), msquic (Microsoft), aioquic, Netty incubator

**난이도**: 높음

**Kotlin / pseudo-code 예제**:
```kotlin
// JDK 자체 QUIC 클라이언트는 아직 없음 → OkHttp 4+ 의 cronet 또는 reactor-netty 사용
// 예: Java 21 + Cronet (Chromium net stack) — HTTP/3 활성화
import org.chromium.net.CronetEngine
import org.chromium.net.UrlRequest

val engine = CronetEngine.Builder(ctx)
    .enableQuic(true)
    .addQuicHint("www.example.com", 443, 443)
    .build()

val req = engine.newUrlRequestBuilder(
    "https://www.example.com/",
    object : UrlRequest.Callback() { /* ... */ },
    java.util.concurrent.Executors.newSingleThreadExecutor(),
).build()
req.start() // 첫 요청은 Alt-Svc 헤더로 HTTP/3 학습, 이후 QUIC 사용
```

**관련 패턴**: [HTTP versions](#http-versions), [TLS Handshake](#tls-handshake), [TCP vs UDP](#tcp-udp), [Reliable UDP](#reliable-udp)

---

<a id="http-versions"></a>

## 4. HTTP/1.1 vs HTTP/2 vs HTTP/3

**목적/정의**: 같은 HTTP semantics (RFC 9110) 위 세 가지 wire format. 각각 1.1 (RFC 9112, text/line-based), 2 (RFC 9113, binary frame multiplexing over TCP+TLS), 3 (RFC 9114, binary frame over QUIC/UDP).

**메커니즘 / 비교 표**:

| 항목 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| Transport | TCP | TCP + TLS | QUIC (UDP) + TLS 1.3 |
| 직렬화 | 텍스트 (CRLF) | 바이너리 frame | 바이너리 frame |
| Multiplexing | 없음 (pipelining 사실상 미사용) | 동일 connection 다중 stream | 동일 connection 다중 stream |
| HoL blocking | 있음 (request 직렬화) | TCP 레벨 잔존 (frame-level 해소, transport-level 잔존) | 완전 해소 |
| Header 압축 | 없음 (gzip body 만) | HPACK (RFC 7541) | QPACK (RFC 9204) |
| Server Push | 없음 | 있음 (대부분 비활성) | 있음 |
| Handshake | TCP 3WHS + TLS 1.2 (2~3 RFC RTT) | 동일 | 1-RTT, 0-RTT resumption |
| Connection migration | 없음 | 없음 | 있음 (Connection ID) |

**HTTP/1.1 특징**:
- Keep-Alive 로 connection 재사용 가능하나 한 connection 에 한 번에 한 요청
- 브라우저가 origin 당 보통 6 connection 병렬 사용

**HTTP/2 특징**:
- Stream ID 로 다중 요청 인터리브
- Priority/Dependency tree (RFC 9218 의 Extensible Prioritization 으로 대체됨)
- gRPC 의 기반

**HTTP/3 특징**:
- HTTP/2 와 frame 구조 유사하나 transport 가 QUIC
- Alt-Svc 헤더로 클라이언트가 HTTP/3 학습 (RFC 7838)

**장점**:
- 1.1: 가장 호환성 높음, 디버깅 쉬움 (telnet 가능)
- 2: 단일 TCP 로 다중화, gRPC 의존
- 3: HoL blocking 완전 해소, mobile/lossy network 강점

**단점·트레이드오프**:
- 1.1: 자원 다수 페이지에서 비효율
- 2: TCP HoL 잔존, server push 사용 불가 수렴
- 3: UDP 차단 환경, CPU 비용

**활용 예시**:
- gRPC: HTTP/2 필수 (RFC 9113)
- REST API: 1.1 / 2 / 3 모두 호환
- CDN edge (Cloudflare, Fastly): 1.1 + 2 + 3 모두 지원, Alt-Svc 로 협상

**난이도**: 중간

**Kotlin / pseudo-code 예제**:
```kotlin
// OkHttp 4+ — HTTP/2 협상 (ALPN) 기본
import okhttp3.OkHttpClient
import okhttp3.Protocol
import okhttp3.Request

val client = OkHttpClient.Builder()
    .protocols(listOf(Protocol.HTTP_2, Protocol.HTTP_1_1))
    .build()

val req = Request.Builder().url("https://api.example.com/v1/users").build()
client.newCall(req).execute().use { res ->
    println("negotiated: ${res.protocol}") // h2 or http/1.1
}

// Java HttpClient (JDK 11+) — HTTP/2 우선
import java.net.http.HttpClient
val jdkClient = HttpClient.newBuilder()
    .version(HttpClient.Version.HTTP_2) // HTTP/3 은 별도 라이브러리
    .build()
```

**관련 패턴**: [QUIC / HTTP/3](#quic-http3), [TLS Handshake](#tls-handshake), [Connection Pooling](#connection-pooling)

---

<a id="tls-handshake"></a>

## 5. TLS Handshake

**목적/정의**: 인증·암호화·무결성을 협상하는 보안 채널 수립 절차. TLS 1.2 (RFC 5246) 는 2-RTT, TLS 1.3 (RFC 8446) 는 1-RTT (full) / 0-RTT (resumption) 로 단축. HTTPS, gRPC, SMTPS, MQTT-TLS 등의 기반.

**메커니즘**:
- **TLS 1.2 full handshake (2-RTT)**:
  1. Client → ClientHello (지원 cipher suite, random, SNI, ALPN protocols)
  2. Server → ServerHello + Certificate + ServerKeyExchange + ServerHelloDone
  3. Client → ClientKeyExchange + ChangeCipherSpec + Finished
  4. Server → ChangeCipherSpec + Finished
- **TLS 1.3 full handshake (1-RTT)**:
  1. Client → ClientHello (key_share + supported_versions + signature_algorithms + SNI + ALPN)
  2. Server → ServerHello + {EncryptedExtensions, Certificate, CertificateVerify, Finished} (모두 암호화)
  3. Client → Finished, 곧바로 application data
- **0-RTT resumption (TLS 1.3)**: 이전 세션의 PSK 로 첫 패킷부터 application data 동봉. **Replay 가능 → idempotent 요청만**
- **ALPN** (RFC 7301): h2 / http/1.1 / h3 선택
- **SNI** (RFC 6066): 한 IP 의 다중 가상 호스트 구분. ECH (RFC 9460 + draft) 가 SNI 암호화 도입 중
- **PFS (Perfect Forward Secrecy)**: ECDHE 기반 ephemeral key 로 장기 키 유출 시에도 과거 트래픽 보호

**장점**:
- TLS 1.3 은 handshake 절반 + ServerHello 이후 전부 암호화 → 메타데이터 보호 강화
- 0-RTT 로 모바일 등 RTT 큰 환경에서 체감 latency 단축
- Cipher suite 단순화 (TLS 1.3 은 AEAD 만 허용, 취약한 RSA key exchange 폐기)

**단점·트레이드오프**:
- 0-RTT 의 replay 위험 — POST/PUT 같은 부작용 있는 요청에 사용 금지
- 인증서 검증 (OCSP/CRL) RTT 추가 가능 → OCSP stapling (RFC 6066) 권장
- mTLS 활성화 시 client cert 관리 부담

**활용 예시**:
- 모든 HTTPS, gRPC (TLS 권장), MQTTS, SMTPS, IMAPS
- Service Mesh (Istio, Linkerd) 의 자동 mTLS
- Let's Encrypt + ACME (RFC 8555) 로 인증서 자동 갱신

**난이도**: 높음

**Kotlin / pseudo-code 예제**:
```kotlin
// TLS 1.3 강제 (JDK 11+, OpenJDK 는 TLS 1.3 기본 지원)
import javax.net.ssl.SSLContext
import javax.net.ssl.SSLParameters
import java.net.http.HttpClient

val ctx = SSLContext.getInstance("TLSv1.3").apply { init(null, null, null) }
val params = SSLParameters().apply {
    applicationProtocols = arrayOf("h2", "http/1.1") // ALPN
    serverNames = listOf(javax.net.ssl.SNIHostName("api.example.com")) // SNI
}
val client = HttpClient.newBuilder()
    .sslContext(ctx)
    .sslParameters(params)
    .version(HttpClient.Version.HTTP_2)
    .build()

// 의사 핸드셰이크 흐름 (TLS 1.3 1-RTT)
// C -> S: ClientHello {key_share, ALPN, SNI}
// S -> C: ServerHello {key_share} + {EncryptedExtensions, Cert, CertVerify, Finished}
// C -> S: {Finished} + application_data    // 1-RTT 완료
```

**관련 패턴**: [HTTP versions](#http-versions), [QUIC / HTTP/3](#quic-http3), [`../security/security-crypto-ops.md`](../security/security-crypto-ops.md)

---

<a id="dns-patterns"></a>

## 6. DNS Patterns

**목적/정의**: 도메인 이름을 IP / 메타데이터로 매핑하는 분산 위계 시스템. RFC 1034/1035 (core), RFC 8484 (DoH), RFC 7858 (DoT), RFC 7871 (EDNS Client Subnet). 모든 인터넷 트래픽의 시작점.

**메커니즘**:
- **Authoritative server**: 특정 zone 에 대한 권위 응답 (예: NS for `example.com`)
- **Recursive resolver**: 클라이언트 대신 root → TLD → authoritative 순으로 질의. ISP 제공 또는 8.8.8.8 (Google), 1.1.1.1 (Cloudflare)
- **Caching resolver**: TTL 동안 응답 캐시 → 부하 감소. TTL 60s ~ 1d 일반
- **Record 종류**: A (IPv4), AAAA (IPv6), CNAME (alias), MX (mail), TXT (SPF/DKIM/verification), SRV (port+host), NS (delegation), CAA (인증서 발급 권한), HTTPS/SVCB (RFC 9460)
- **EDNS Client Subnet (ECS)**: resolver 가 client subnet 정보를 authoritative 에 전달 → GeoDNS 가 가까운 PoP 응답
- **DoH (DNS over HTTPS, RFC 8484)** / **DoT (DNS over TLS, RFC 7858)**: 평문 DNS 의 도청·변조 방지
- **GeoDNS**: client 위치에 따라 다른 A 레코드 반환 (Route 53, NS1, Cloudflare)

**장점**:
- 분산 위계 → 단일 장애점 없음, 전 세계 규모로 확장
- TTL 캐시 → 평균 latency < 1ms
- DoH/DoT → privacy 강화

**단점·트레이드오프**:
- 캐시 stale → DNS-based 페일오버 시 TTL 만큼 지연
- DoH 는 검열 우회 가능성 vs 기업 내부 DNS 정책 충돌
- ECS 가 privacy 우려 (client subnet 노출). Cloudflare 1.1.1.1 은 ECS 미전송
- DNS amplification attack (UDP source IP 위장)

**활용 예시**:
- AWS Route 53, Cloudflare DNS, Google Cloud DNS
- CDN traffic steering (Akamai, Fastly): GeoDNS + health check
- DoH: Firefox/Chrome 의 secure DNS, Cloudflare 1.1.1.1, NextDNS
- SRV: Kubernetes service discovery (`<svc>.<ns>.svc.cluster.local`)

**난이도**: 중간

**Kotlin / pseudo-code 예제**:
```kotlin
// JDK 기본 resolver — getByName 은 시스템 resolver 호출
import java.net.InetAddress

fun resolve(host: String): List<String> =
    InetAddress.getAllByName(host).map { it.hostAddress }

// DoH 직접 호출 (Cloudflare)
import okhttp3.OkHttpClient
import okhttp3.Request

fun dohQuery(name: String, type: String = "A"): String {
    val client = OkHttpClient()
    val req = Request.Builder()
        .url("https://cloudflare-dns.com/dns-query?name=$name&type=$type")
        .header("Accept", "application/dns-json")
        .build()
    return client.newCall(req).execute().use { it.body!!.string() }
}

// OkHttp 4+ 에 내장된 DnsOverHttps 사용
import okhttp3.dnsoverhttps.DnsOverHttps
import okhttp3.HttpUrl.Companion.toHttpUrl

val bootstrap = OkHttpClient()
val doh = DnsOverHttps.Builder()
    .client(bootstrap)
    .url("https://1.1.1.1/dns-query".toHttpUrl())
    .build()
val secureClient = bootstrap.newBuilder().dns(doh).build()
```

**관련 패턴**: [CDN / Edge](#cdn-edge), [TLS Handshake](#tls-handshake), [`../security/security-api-web.md`](../security/security-api-web.md)

---

<a id="cdn-edge"></a>

## 7. CDN / Edge Patterns

**목적/정의**: 사용자에 지리적으로 가까운 PoP (Point of Presence) 에서 캐시·계산을 제공하여 origin 부하·latency·대역폭 비용을 절감하는 분산 인프라. Akamai (1998 년 첫 CDN) → Cloudflare, Fastly, CloudFront, Bunny 까지 다양.

**메커니즘**:
- **PoP**: 전 세계 수십~수천 위치의 edge 노드. anycast IP 로 가장 가까운 PoP 로 라우팅 (BGP)
- **Cache Hierarchy**: edge PoP → regional cache (mid-tier) → origin. 미스 시 상위로 fan-in 하여 origin thundering herd 방지
- **Origin Shield** (Cloudflare, Fastly): 모든 PoP 가 한 designated cache 만 origin 으로 사용 → origin RPS 극단 감소
- **Anycast**: 동일 IP 를 여러 PoP 에서 announce → BGP 가 가장 짧은 경로 선택. UDP/QUIC 친화
- **Edge Compute**: 캐시 옆에서 JS/WASM 실행. Cloudflare Workers (V8 isolate), Fastly Compute@Edge (WASM), AWS Lambda@Edge / CloudFront Functions, Vercel Edge Functions, Deno Deploy
- **Cache key**: URL + Vary 헤더 + (선택) query string + cookie subset
- **Stale-While-Revalidate (RFC 5861)**: TTL 만료 후에도 stale 응답 즉시 반환 + 백그라운드 갱신

**장점**:
- TTFB 단축 (50ms → 5ms 흔함)
- Origin 트래픽 90%+ offload → 비용/스케일 절감
- DDoS 흡수 (Cloudflare/Akamai 의 Tbps 급 capacity)
- Edge compute 로 personalization/A-B 까지 origin 없이 처리

**단점·트레이드오프**:
- Cache invalidation 의 어려움 ("computer science 의 2대 난제" 중 하나)
- Personalized content 캐시 키 폭증 → hit rate 저하
- Edge compute 의 runtime/SDK 제약 (Node.js 호환 부분 한정)
- Vendor lock-in

**활용 예시**:
- 정적 자산 (JS/CSS/이미지/비디오) 의 기본 인프라
- API 캐싱: `Cache-Control: s-maxage=60` + Vary 활용
- WAF / Bot mitigation 통합 (Cloudflare, Akamai)
- Edge compute: Vercel Next.js Edge Runtime, Cloudflare Workers KV/D1

**난이도**: 중간

**Kotlin / pseudo-code 예제**:
```kotlin
// Origin (Ktor) 에서 CDN 친화 헤더 설정
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.http.*

fun Application.cdnFriendly() = routing {
    get("/api/products/{id}") {
        val id = call.parameters["id"]!!
        // edge 60s, browser 5s, stale 1h while revalidating
        call.response.header(HttpHeaders.CacheControl,
            "public, s-maxage=60, max-age=5, stale-while-revalidate=3600")
        call.response.header(HttpHeaders.Vary, "Accept-Encoding, Accept-Language")
        call.respondText("""{"id":"$id"}""", ContentType.Application.Json)
    }
}

// Cloudflare Workers (TypeScript pseudo, JS isolate)
// export default {
//   async fetch(req, env, ctx) {
//     const cache = caches.default;
//     let res = await cache.match(req);
//     if (!res) {
//       res = await fetch(req); // origin
//       ctx.waitUntil(cache.put(req, res.clone()));
//     }
//     return res;
//   }
// }
```

**관련 패턴**: [DNS Patterns](#dns-patterns), [Connection Pooling](#connection-pooling), [caching.md](caching.md)

---

<a id="nat-traversal"></a>

## 8. NAT Traversal

**목적/정의**: NAT 뒤에 있는 두 peer 가 직접 통신할 수 있도록 외부 reflexive 주소를 발견하고 (필요 시) relay 를 경유하는 절차. STUN (RFC 8489) / TURN (RFC 8656) / ICE (RFC 8445) 가 표준 3종. WebRTC, VoIP, P2P, 게임 매치메이킹의 기반.

**메커니즘**:
- **NAT 종류**:
  - Full Cone: 한번 outbound 매핑되면 임의 외부가 들어올 수 있음
  - Restricted Cone: 매핑된 외부 IP 만 수신 허용
  - Port-Restricted Cone: 외부 IP+port 매칭만
  - **Symmetric NAT**: 목적지가 다르면 매번 다른 외부 포트 할당 → STUN 만으로 통신 불가, TURN 필수
- **STUN (Session Traversal Utilities for NAT)**: client 가 STUN server (예: `stun.l.google.com:19302`) 에 binding request → 응답에 client 의 reflexive (NAT 외부) IP:port 가 담김
- **TURN (Traversal Using Relays around NAT)**: STUN 으로 부족할 때 relay server 가 두 peer 트래픽 중계. 비용·지연 증가
- **ICE (Interactive Connectivity Establishment)**: 후보 (host / server reflexive / relayed) 를 모아 priority 부여 → connectivity check (STUN binding requests) → 성공한 쌍 사용. **Trickle ICE** (RFC 8838) 는 후보를 incremental 로 교환하여 setup 시간 단축
- **Hole Punching**: 양 peer 가 동시에 outbound 패킷을 보내 NAT 매핑 생성

**장점**:
- P2P 직접 통신 → 서버 대역폭/지연 절감
- Symmetric NAT 같은 어려운 케이스도 TURN 으로 보장

**단점·트레이드오프**:
- TURN 은 모든 미디어를 relay → 서버 대역폭 비용 (시간당 GB 단위)
- 기업 방화벽이 STUN/TURN 차단 흔함 → TURN over TLS (TURNS, 443) 폴백
- ICE 후보 수집·체크에 1~수초 소요

**활용 예시**:
- WebRTC (Google Meet, Zoom, Discord, Slack huddles, Whereby)
- VoIP (SIP + ICE)
- P2P 파일 공유 (libp2p, Tailscale 의 DERP relay)
- 게임 매치메이킹 (Steam 의 SDR, EOS Relay)

**난이도**: 높음

**Kotlin / pseudo-code 예제**:
```kotlin
// 의사코드 — ICE 후보 수집 + connectivity check
data class IceCandidate(
    val foundation: String,
    val transport: String,         // udp/tcp
    val priority: Long,
    val address: String,
    val port: Int,
    val type: Type,                // HOST, SRFLX (server reflexive), RELAY
) { enum class Type { HOST, SRFLX, RELAY } }

class IceAgent(
    private val stunServers: List<String>,
    private val turnServers: List<Pair<String, String>>, // host -> credential
) {
    suspend fun gather(): List<IceCandidate> = buildList {
        // 1) host: local NIC 모든 주소
        addAll(localNics().map { IceCandidate("h", "udp", 126 shl 24, it.ip, it.port, IceCandidate.Type.HOST) })
        // 2) srflx: STUN 으로 reflexive 발견
        for (stun in stunServers) {
            val reflex = stunBinding(stun) // RFC 8489 Binding Request
            add(IceCandidate("s", "udp", 100 shl 24, reflex.ip, reflex.port, IceCandidate.Type.SRFLX))
        }
        // 3) relay: TURN allocate
        for ((turn, cred) in turnServers) {
            val allocated = turnAllocate(turn, cred) // RFC 8656
            add(IceCandidate("r", "udp", 0, allocated.ip, allocated.port, IceCandidate.Type.RELAY))
        }
    }
}
// 이후 SDP offer/answer 로 후보 교환 → STUN binding request 로 connectivity check
```

**관련 패턴**: [WebRTC](#webrtc), [TCP vs UDP](#tcp-udp), [Reliable UDP](#reliable-udp)

---

<a id="websocket"></a>

## 9. WebSocket Protocol

**목적/정의**: 단일 TCP connection 위 양방향·full-duplex 메시지 전송 프로토콜. RFC 6455. HTTP/1.1 `Upgrade` 로 시작하여 이후 frame 기반 binary protocol 로 전환. 실시간 채팅·알림·라이브 데이터의 표준.

**메커니즘**:
- **Opening Handshake**:
  - Client → `GET /chat HTTP/1.1 \r\n Upgrade: websocket \r\n Connection: Upgrade \r\n Sec-WebSocket-Key: <base64> \r\n Sec-WebSocket-Version: 13 \r\n Sec-WebSocket-Protocol: chat.v2`
  - Server → `HTTP/1.1 101 Switching Protocols \r\n Upgrade: websocket \r\n Connection: Upgrade \r\n Sec-WebSocket-Accept: <SHA1(key + magic GUID)>`
- **Frame format**: FIN(1) + RSV(3) + opcode(4) + MASK(1) + payload_len(7/7+16/7+64) + masking-key(0/32) + payload
- **Opcodes**: 0x0 continuation, 0x1 text (UTF-8), 0x2 binary, 0x8 close, 0x9 ping, 0xA pong
- **Masking**: 클라이언트 → 서버 frame 은 반드시 masking (proxy cache poisoning 방지). 서버 → 클라이언트는 masking 금지
- **Subprotocol**: `Sec-WebSocket-Protocol` 헤더로 협상 (예: `mqtt`, `graphql-ws`, `stomp`)
- **WSS**: TLS 위 WebSocket. `wss://` URL, 443 포트

**장점**:
- HTTP polling 대비 latency 극저 (RTT 한 번)
- 양방향 push 가능 → 서버 발신 이벤트 자연스러움
- 80/443 위라 방화벽 통과율 높음

**단점·트레이드오프**:
- HTTP/2 multiplexing 과 안 맞음 (전용 connection 점유) → 다수 사용자 시 connection 폭증
- Stateful → 로드밸런서 sticky session 필요
- 메시지 ordering 외엔 신뢰성 (재전송/순서) 직접 구현
- HTTP/3 WebSocket (RFC 9220) 은 구현 초기 단계

**활용 예시**:
- 실시간 채팅 (Slack, Discord), 협업 (Figma, Google Docs presence)
- 주식/암호화폐 시세 (Binance, Coinbase)
- 라이브 알림, 게임 lobby, IoT 텔레메트리
- 라이브러리: Ktor WebSocket, Spring WebFlux, ws (Node), Socket.IO (위에 메시징 계층)

**난이도**: 중간

**Kotlin / pseudo-code 예제**:
```kotlin
// Ktor server WebSocket
import io.ktor.server.application.*
import io.ktor.server.websocket.*
import io.ktor.websocket.*

fun Application.chat() {
    install(WebSockets) {
        pingPeriodMillis = 15_000
        timeoutMillis = 30_000
    }
    routing {
        webSocket("/chat") {
            send(Frame.Text("welcome"))
            for (frame in incoming) {
                if (frame is Frame.Text) {
                    val msg = frame.readText()
                    send(Frame.Text("echo: $msg"))
                }
            }
        }
    }
}

// OkHttp client WebSocket
import okhttp3.*
val client = OkHttpClient()
val req = Request.Builder().url("wss://api.example.com/chat")
    .addHeader("Sec-WebSocket-Protocol", "chat.v2")
    .build()
client.newWebSocket(req, object : WebSocketListener() {
    override fun onMessage(ws: WebSocket, text: String) { println(text) }
    override fun onOpen(ws: WebSocket, res: Response) { ws.send("hi") }
})
```

**관련 패턴**: [HTTP versions](#http-versions), [TLS Handshake](#tls-handshake), [WebRTC](#webrtc)

---

<a id="webrtc"></a>

## 10. WebRTC

**목적/정의**: 브라우저·앱 간 실시간 오디오·비디오·임의 데이터 P2P 통신 표준. W3C WebRTC API + IETF RTCWEB. 컴포넌트: ICE/STUN/TURN (NAT 통과), DTLS-SRTP (미디어 암호화), SCTP over DTLS (DataChannel).

**메커니즘**:
- **Signaling** (앱이 직접 구현 — 표준에 없음): SDP offer/answer 와 ICE 후보를 두 peer 간 교환 (대개 WebSocket 사용)
- **SDP (Session Description Protocol, RFC 8866)**: 미디어 설정 (codec, payload type, ICE 후보, fingerprint) 텍스트 기술
- **PeerConnection**:
  - `createOffer()` → SDP offer 생성
  - `setLocalDescription()` → 로컬 적용 + ICE gathering 시작
  - 시그널링 채널로 offer 전송, 상대가 answer 회신
  - `setRemoteDescription()` → 적용
- **Trickle ICE**: 후보를 모두 모은 후 한꺼번에 보내지 않고 발견 즉시 전송 → setup 가속
- **미디어 경로**:
  - **P2P (mesh)**: N 인 회의에서 각자 N-1 stream → 4~5명까지만 실용
  - **SFU (Selective Forwarding Unit)**: 서버가 stream 을 단순 fan-out (decode 없음). 효율적 (Janus, mediasoup, LiveKit, Jitsi Videobridge, Cloudflare Calls)
  - **MCU (Multipoint Control Unit)**: 서버가 모든 stream 을 decode + mix + re-encode → CPU 비싸지만 클라이언트 부하 최소
- **DataChannel**: SCTP over DTLS over UDP. ordered/unordered, reliable/unreliable 선택 가능 (게임용 unreliable 가능)

**장점**:
- 브라우저 기본 (플러그인 불요)
- End-to-end 암호화 (DTLS-SRTP) 표준
- DataChannel 로 임의 데이터 P2P 전송 가능

**단점·트레이드오프**:
- API 복잡도 매우 높음 (~50 메서드/이벤트)
- TURN relay 비용 (사용자의 ~20% 가 symmetric NAT)
- 대규모 회의는 SFU 필수 + 운영 부담
- 시그널링 표준 부재 — 앱마다 재구현

**활용 예시**:
- Google Meet, Microsoft Teams, Zoom (일부), Discord 음성, Slack huddles
- Cloudflare Stream / Calls, LiveKit, Daily, Twilio Video
- Cloud gaming (GeForce NOW WebRTC 모드), 원격 데스크톱 (Parsec, Moonlight)
- libp2p 의 webrtc-direct transport

**난이도**: 높음

**Kotlin / pseudo-code 예제**:
```kotlin
// JS pseudo (브라우저) — 실제 PeerConnection 흐름
// const pc = new RTCPeerConnection({
//   iceServers: [
//     { urls: 'stun:stun.l.google.com:19302' },
//     { urls: 'turn:turn.example.com:3478', username: 'u', credential: 'p' },
//   ],
// });
// pc.onicecandidate = (e) => signaling.send({ type: 'candidate', candidate: e.candidate });
// pc.ontrack = (e) => remoteVideo.srcObject = e.streams[0];
// const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
// stream.getTracks().forEach(t => pc.addTrack(t, stream));
// const offer = await pc.createOffer();
// await pc.setLocalDescription(offer);
// signaling.send({ type: 'offer', sdp: offer.sdp });

// Android — google-webrtc / webrtc-android Kotlin wrapper
val factory: PeerConnectionFactory = PeerConnectionFactory.builder().createPeerConnectionFactory()
val cfg = PeerConnection.RTCConfiguration(listOf(
    PeerConnection.IceServer.builder("stun:stun.l.google.com:19302").createIceServer(),
))
val pc = factory.createPeerConnection(cfg, object : PeerConnection.Observer { /* ... */ })
val dc = pc?.createDataChannel("game", DataChannel.Init().apply {
    ordered = false                // 게임용 unordered
    maxRetransmits = 0             // unreliable
})
```

**관련 패턴**: [NAT Traversal](#nat-traversal), [Reliable UDP](#reliable-udp), [WebSocket](#websocket) (시그널링 채널로 자주 사용)

---

<a id="reliable-udp"></a>

## 11. Reliable UDP / KCP / RUDP

**목적/정의**: UDP 위에 선택적 신뢰성 (ACK / NACK / FEC) + 낮은 지연을 구현하는 transport 군. 게임·실시간 미디어처럼 "TCP 신뢰성은 과하고 UDP 비신뢰는 모자란" 영역. 대표: KCP (skywind/kcp), ENet, RakNet, RUDP, Aeron, QUIC (별도 항목), UDT.

**메커니즘**:
- **신뢰성 선택**: 패킷 단위로 reliable / unreliable / unreliable-sequenced 지정 (RakNet/ENet style)
- **ACK 기반**: 송신측이 retransmit 큐 유지, 수신측이 누락 시 retransmit 요청
- **NACK 기반**: 수신측이 누락한 sequence 만 알림 (대역 절약)
- **FEC (Forward Error Correction)**: 패킷 N 개당 M 개 redundant 추가 → 손실률 ≤ M/N 이면 재전송 없이 복구. Reed-Solomon, Raptor 흔함
- **KCP 특징**: ARQ 알고리즘 변형. early retransmit + fast resend + non-concession flow control → TCP 대비 평균 latency 30~40% 감소 (대신 대역 1.1~2× 소비)
- **Aeron**: low-latency messaging (Real Logic, Martin Thompson). Single-digit µs latency, financial trading 에서 사용

**장점**:
- TCP HoL blocking 회피 + 신뢰성 일부 보장
- 게임/실시간 미디어에서 체감 latency 큰 폭 개선
- FEC 로 lossy network 에서도 매끄러운 흐름

**단점·트레이드오프**:
- 자체 congestion control 미흡 시 대역 침해 → 공정성 문제
- 라이브러리/프로토콜 비표준 → 디버깅·관측 도구 적음
- NAT/방화벽이 UDP 차단하면 무력
- 대부분 QUIC 가 표준화된 대안으로 흡수 중

**활용 예시**:
- KCP: 중국계 게임 (대전 격투, FPS), v2ray/shadowsocks 의 transport 옵션
- ENet: Quake III, 다수 인디 게임
- RakNet: Minecraft (구버전), Unity 의 일부 멀티플레이어
- Aeron: 금융 거래소, IEX, 일부 HFT
- 게임 엔진 (Unity Mirror, Unreal Engine 의 NetDriver) 의 reliable UDP 레이어

**난이도**: 높음

**Kotlin / pseudo-code 예제**:
```kotlin
// KCP 의사 인터페이스 (kcp-java 또는 JNI 바인딩)
class KcpSession(val conv: Long) {
    private val sendBuf = ArrayDeque<Segment>()    // retransmit queue
    private val recvBuf = ArrayDeque<Segment>()    // out-of-order buffer
    private var sndUna = 0L                        // 가장 오래된 unacked seq

    fun send(data: ByteArray, reliable: Boolean = true) {
        val seg = Segment(seq = nextSeq(), reliable = reliable, payload = data)
        if (reliable) sendBuf.addLast(seg)
        transmit(seg)
    }

    fun onAck(seq: Long) {
        sendBuf.removeIf { it.seq <= seq }
        sndUna = seq + 1
    }

    fun tick(nowMs: Long) {
        // 만료된 segment 재전송 (RTO 기반)
        sendBuf.filter { nowMs - it.sentAt > it.rto }
            .forEach { transmit(it); it.sentAt = nowMs; it.rto = (it.rto * 1.5).toLong() }
    }
}

// FEC 의사 코드 — Reed-Solomon (k=4, m=2)
// for every 4 data packets, send 2 parity packets
// receiver can lose up to 2 of 6 packets and still recover
```

**관련 패턴**: [TCP vs UDP](#tcp-udp), [QUIC / HTTP/3](#quic-http3), [WebRTC](#webrtc), [NAT Traversal](#nat-traversal)

---

<a id="connection-pooling"></a>

## 12. Connection Pooling & Keep-Alive

**목적/정의**: TCP·TLS handshake 비용을 다수 요청에 amortize 하기 위해 connection 을 재사용·풀링하는 패턴. HTTP/1.1 Keep-Alive (RFC 9112), HTTP/2 multiplexing, DB connection pool 모두 같은 원칙.

**메커니즘**:
- **HTTP/1.1 Keep-Alive**: `Connection: keep-alive` (1.1 기본) → 같은 connection 으로 직렬 요청. 단, multiplexing 없음
- **HTTP/2 / HTTP/3 multiplexing**: 한 connection 에 동시 다중 stream → pool 크기 작아도 throughput 유지
- **풀 설정 축**:
  - `maxIdleConnections` — 유지할 idle 수
  - `maxConnectionsPerHost` — host 당 동시 connection 상한 (HTTP/1.1 보통 5~10)
  - `idleTimeout` — 미사용 시 닫기 (서버 timeout 보다 짧게)
  - `connectTimeout` / `readTimeout`
- **Keep-Alive 충돌**: 클라이언트 idle timeout > 서버 timeout → 서버가 먼저 RST 보냄 → 클라이언트가 stale connection 에 쓰기 시도 → `IOException`. 해결: 서버 timeout 의 80% 로 클라이언트 timeout
- **TCP_NODELAY** (Nagle off) + **TCP keep-alive (OS 레벨)**: 다른 메커니즘. Nagle 은 작은 패킷 묶기, OS keep-alive 는 dead peer 감지
- **DB connection pool**: HikariCP (Java), pgbouncer (PostgreSQL), pgpool. `connect()` 가 100ms+ → 풀 사용은 거의 필수

**장점**:
- handshake 비용 (TCP 1-RTT + TLS 1-2 RTT) 제거 → p50 latency 큰 감소
- 서버 측 SYN flood 감소, 메모리 절감
- HTTP/2 는 풀 크기 < HTTP/1.1 로도 동등 throughput

**단점·트레이드오프**:
- Stale connection — 미사용 동안 NAT/방화벽이 dropped 가능. 첫 사용 시 silent failure → retry 필요
- Pool exhaustion 시 deadlock 위험 (특히 DB pool 이 1 connection 점유 후 다른 connection 필요할 때)
- HTTP/2 의 단일 connection 이 손실되면 모든 stream 영향 → HTTP/3 가 해소
- 메모리: idle connection 마다 socket buffer + TLS state

**활용 예시**:
- OkHttp `ConnectionPool` (기본 maxIdleConnections=5, keepAliveDuration=5분)
- Apache HttpClient `PoolingHttpClientConnectionManager`
- gRPC-Java: 채널 = HTTP/2 multiplexed connection
- DB: HikariCP (Spring Boot 기본), pgbouncer transaction mode
- nginx upstream keepalive

**난이도**: 중간

**Kotlin / pseudo-code 예제**:
```kotlin
// OkHttp pool 튜닝
import okhttp3.ConnectionPool
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

val pool = ConnectionPool(
    maxIdleConnections = 32,
    keepAliveDuration = 4,            // 서버 timeout(5분)보다 짧게
    timeUnit = TimeUnit.MINUTES,
)
val client = OkHttpClient.Builder()
    .connectionPool(pool)
    .connectTimeout(2, TimeUnit.SECONDS)
    .readTimeout(10, TimeUnit.SECONDS)
    .callTimeout(15, TimeUnit.SECONDS)
    .retryOnConnectionFailure(true)   // stale connection 자동 retry
    .build()

// HikariCP — DB pool
import com.zaxxer.hikari.HikariConfig
import com.zaxxer.hikari.HikariDataSource

val cfg = HikariConfig().apply {
    jdbcUrl = "jdbc:postgresql://db/app"
    maximumPoolSize = 20
    minimumIdle = 5
    idleTimeout = 600_000             // 10분
    maxLifetime = 1_800_000           // 30분 (DB 측 idle_in_transaction_session_timeout 보다 짧게)
    connectionTimeout = 3_000
}
val ds = HikariDataSource(cfg)
```

**관련 패턴**: [HTTP versions](#http-versions), [TLS Handshake](#tls-handshake), [TCP vs UDP](#tcp-udp), [reliability.md#timeout](reliability.md), [data-access.md](data-access.md)

---

<a id="osi-tcpip-model"></a>

## 13. OSI / TCP-IP Layering Model (OSI / TCP-IP 계층 모델)

**목적/정의**: 네트워크 통신을 책임이 분리된 계층 스택으로 분해하여, 각 계층이 바로 위·아래 계층과만 정해진 인터페이스로 상호작용하도록 만드는 참조 모델. OSI 7계층 모델 (ISO/IEC 7498-1) 은 개념·교육·진단의 공통 어휘를 제공하고, 실제 인터넷이 구현하는 것은 TCP/IP 4계층 모델 (RFC 1122 *Requirements for Internet Hosts*) 입니다. 이 카탈로그의 TCP/UDP·TLS·HTTP·DNS 가 "어느 계층에 속하고 어디서 만나는가" 를 정리하는 지도.

**메커니즘**:
- **OSI 7계층 (위→아래)** 과 각 계층 책임:
  | # | OSI 계층 | 책임 (PDU 단위) | 대표 프로토콜/요소 |
  |---|---|---|---|
  | 7 | Application | 사용자 대면 프로토콜 의미론 (data) | HTTP, DNS, SMTP, gRPC |
  | 6 | Presentation | 직렬화·인코딩·암호화·압축 | TLS, MIME, JSON/Protobuf, gzip |
  | 5 | Session | 세션 수립·재개·동기화 | TLS 세션 재개, RPC 세션 |
  | 4 | Transport | end-to-end 전달·다중화·신뢰성 (segment/datagram) | TCP, UDP, QUIC* |
  | 3 | Network | 논리 주소·라우팅 (packet) | IP, ICMP, BGP, IPsec |
  | 2 | Data Link | 인접 노드 frame 전달·MAC (frame) | Ethernet, Wi-Fi (802.11), ARP, PPP |
  | 1 | Physical | 비트의 전기/광/전파 전송 (bit) | 동축/광케이블, 802.3 PHY, 무선 |
- **TCP/IP 4계층 ↔ OSI 매핑**: Application(OSI 5~7) / Transport(OSI 4) / Internet(OSI 3) / Link(OSI 1~2). TCP/IP 는 Presentation·Session 을 별도 계층으로 두지 않고 Application 안에서 처리 — 그래서 TLS 는 "OSI 로는 6/5, TCP/IP 로는 Application 과 Transport 사이" 라는 애매함이 생깁니다 (QUIC* 이 transport+crypto 를 합치는 이유와 직결).
- **Encapsulation (송신, 위→아래)**: 각 계층이 위 계층의 PDU 를 payload 로 받아 자기 헤더(+필요 시 trailer) 를 붙입니다. 예: HTTP 요청 → TLS record → TCP segment (src/dst port, seq) → IP packet (src/dst IP, TTL) → Ethernet frame (src/dst MAC, FCS trailer) → bit stream.
- **Decapsulation (수신, 아래→위)**: 역순으로 각 계층이 자기 헤더를 떼어내고 payload 를 상위로 올립니다. 각 헤더의 다음-계층 식별 필드 (Ethernet `EtherType=0x0800`, IP `Protocol=6`, TCP `dst port=443`) 가 어느 상위 핸들러로 보낼지 결정 — 이것이 demultiplexing.
- **계층 경계의 식별자**: Physical=없음 / Data Link=MAC(48bit) / Network=IP / Transport=port(16bit) / Application=URL·hostname. 한 계층은 자기 식별자만 알면 되고 위/아래는 불투명(opaque) — 이것이 계층화의 핵심 추상화.

**장점**:
- 관심사 분리 — 한 계층 구현을 교체해도 (Ethernet→Wi-Fi, TCP→QUIC) 인접 인터페이스만 지키면 나머지 계층 무영향
- 공통 어휘 — "L4 로드밸런서 vs L7 로드밸런서", "L3 라우팅", "L2 스위칭" 처럼 진단·설계 대화가 정확해짐
- 상호운용성 — 벤더·OS·언어가 달라도 각 계층 표준만 따르면 통신 성립

**단점·트레이드오프**:
- OSI 7계층은 이상적 모델일 뿐 실제 구현과 1:1 이 아님 — TLS, QUIC 처럼 여러 계층을 가로지르는 프로토콜이 흔해 6/5 계층 구분이 모호
- 엄격한 계층화는 오버헤드 (계층마다 헤더·복사·context switch) → 고성능 영역은 의도적으로 계층을 위반 (kernel bypass, DPDK, RDMA, QUIC 의 transport+crypto 통합)
- 계층 누수 (leaky abstraction) — MTU/MSS, Nagle, NAT 등 하위 계층 특성이 상위 성능에 새어 나옴

**활용 예시**:
- 방화벽/로드밸런서 분류: L3/4 (IP·port 기반, 빠름) vs L7 (HTTP path/header 기반, 유연) — AWS NLB(L4) vs ALB(L7)
- 트러블슈팅 사다리: ping(L3) → telnet/nc port(L4) → curl -v(L7 TLS+HTTP) 순으로 계층을 좁혀 가며 원인 격리
- 패킷 분석: Wireshark 가 frame→IP→TCP→TLS→HTTP 로 decapsulation 한 결과를 계층 트리로 표시
- 캡슐화 응용: VPN/터널링 (IPsec, WireGuard, VXLAN) 은 한 계층 패킷을 다른 계층 payload 로 다시 감싸는 것

**난이도**: 중간

**Kotlin / pseudo-code 예제**:
```kotlin
// 의사코드 — encapsulation: 상위 PDU 를 하위가 헤더로 감싼다 (송신, 위→아래)
data class Pdu(val header: ByteArray, val payload: ByteArray, val trailer: ByteArray = ByteArray(0)) {
    fun bytes(): ByteArray = header + payload + trailer
}

fun encapsulate(httpRequest: ByteArray): ByteArray {
    val tls  = Pdu(header = tlsRecordHeader(),            payload = httpRequest)        // L6: TLS record
    val tcp  = Pdu(header = tcpHeader(srcPort = 51000, dstPort = 443, seq = 1L),
                   payload = tls.bytes())                                               // L4: segment
    val ip   = Pdu(header = ipHeader(proto = 6 /*TCP*/, ttl = 64),
                   payload = tcp.bytes())                                               // L3: packet
    val frame = Pdu(header  = ethHeader(etherType = 0x0800 /*IPv4*/),
                    payload = ip.bytes(),
                    trailer = fcs(ip.bytes()))                                          // L2: frame (+trailer)
    return frame.bytes()                                                               // L1: bit stream 으로 송출
}

// decapsulation: 다음-계층 식별 필드로 demultiplex (수신, 아래→위)
fun dispatch(ipProtocol: Int, dstPort: Int): String = when {
    ipProtocol == 6  && dstPort == 443 -> "L4 TCP -> L6 TLS -> L7 HTTP"   // HTTPS
    ipProtocol == 17 && dstPort == 53  -> "L4 UDP -> L7 DNS"              // DNS over UDP
    ipProtocol == 1                    -> "L3 ICMP (ping)"                // transport 없음
    else                               -> "unknown next-layer handler"
}
```

**관련 패턴**: [TCP vs UDP](#tcp-udp) (Transport / L4), [TLS Handshake](#tls-handshake) (Presentation·Session / L6~5), [HTTP versions](#http-versions) (Application / L7), [DNS Patterns](#dns-patterns) (Application / L7)

---

<a id="ip-routing"></a>

## 14. IP Routing & Forwarding (IP 라우팅 / 포워딩)

**목적/정의**: 패킷이 발신지에서 목적지까지 도달하기 위해, 각 라우터가 (1) **forwarding** — 들어온 패킷을 어느 인터페이스로 내보낼지 결정하고, (2) **routing** — 그 forwarding table 을 어떻게 채울지 경로 정보를 교환·계산하는 두 단계로 나뉩니다. forwarding 은 패킷 단위 data plane (빠름, 하드웨어), routing 은 control plane (느림, 프로토콜). 핵심 결정 규칙은 **longest-prefix match (LPM)**, 주소 체계는 **CIDR / subnet / netmask**. 라우팅 프로토콜은 도메인(AS) 내부 IGP (RIP / OSPF / IS-IS) 와 도메인 간 EGP (BGP) 로 나뉩니다.

**메커니즘**:
- **IP forwarding + longest-prefix match (LPM)**: 목적지 IP 와 forwarding table 의 모든 prefix 를 비교해 **가장 긴 (가장 구체적인) prefix** 가 매칭되는 entry 의 next-hop 으로 전달. 예: `10.1.0.0/16` 과 `10.1.2.0/24` 가 모두 매칭되면 `/24` 우선. `0.0.0.0/0` 은 default route (모두 매칭, prefix 길이 0 → 최후순위)
- **Subnet / CIDR / netmask**: IP = network prefix + host. netmask `255.255.255.0` ↔ CIDR `/24` ↔ host 254 개. CIDR (RFC 4632) 는 classful (A/B/C) 폐지 후 임의 길이 prefix 로 주소 집약(aggregation) 가능 → 라우팅 테이블 크기 억제
- **Distance-Vector (RIP, RFC 2453)**: 각 라우터가 "목적지까지 거리(hop count)" 벡터를 이웃에게만 주기적 전파 (Bellman-Ford). 전체 topology 모름. hop 16 = 무한대(도달 불가) → 소규모 한정. **count-to-infinity** 문제를 split horizon / poison reverse 로 완화
- **Link-State (OSPF RFC 2328 / IS-IS ISO 10589)**: 각 라우터가 자신의 link 상태(LSA)를 영역 전체에 flooding → 모두가 동일한 topology DB 보유 → **Dijkstra SPF** 로 각자 최단 경로 독립 계산. 빠른 수렴, area 로 계층화하여 확장
- **BGP (path-vector, EGP, RFC 4271)**: AS(Autonomous System) 간 경로 교환. metric 이 아니라 **AS_PATH (거쳐온 AS 목록)** 로 경로 비교 + loop 방지. policy (LOCAL_PREF, MED, AS_PATH prepend) 기반 결정 → 기술적 최단이 아니라 비즈니스/계약 우선. TCP 179 위 동작, eBGP(AS 간) / iBGP(AS 내) 구분
- **도메인 간 vs 내부**: IGP(OSPF/IS-IS/RIP) 는 한 AS **내부** 최단 경로 최적화, BGP 는 AS **사이** 도달성·정책 — 인터넷은 IGP 다수가 BGP 로 묶인 구조

**장점**:
- LPM: 구체적 경로 우선 + default route fallback 으로 거대한 인터넷을 작은 테이블로 표현
- Link-State (OSPF/IS-IS): 전체 topology 인식 → 빠른 수렴, loop 적음, area 계층화로 대규모 확장
- Distance-Vector (RIP): 구현·설정 단순, 소규모 망에 충분
- BGP: policy 표현력으로 multi-homing / traffic engineering / 계약 관계 반영, 인터넷 규모(100만+ prefix) 운용

**단점·트레이드오프**:
- Distance-Vector: count-to-infinity, 느린 수렴, hop 15 한계 → 대규모 부적합
- Link-State: LSA flooding + SPF 계산의 CPU/메모리 비용, 설정 복잡, area 설계 필요
- BGP: 수렴 느림(수십 초~분), 설정 오류가 전 세계 영향(route leak / hijack — 2008 Pakistan→YouTube, 2021 Facebook 장애), RPKI/ROA 미배포 시 origin 검증 약함
- LPM: 라인레이트 검색 위해 TCAM/trie 등 특수 하드웨어 필요

**활용 예시**:
- RIP: 소규모 LAN, 교육·레거시 (Cisco/Juniper 기본 비활성에 가까움)
- OSPF: 기업 캠퍼스/데이터센터 IGP 표준, 멀티벤더
- IS-IS: 대형 ISP / 통신사 백본 (IP 비의존 CLNS 기반이라 확장성 선호)
- BGP: 인터넷 AS 간 라우팅 전부, 클라우드(AWS Direct Connect / Transit Gateway), CDN anycast announce ([CDN / Edge](#cdn-edge) 참고), Kubernetes(Calico/Cilium 의 BGP 모드)
- LPM/CIDR: 모든 라우터·L3 스위치·Linux `ip route`, VPC 서브넷 설계

**난이도**: 높음

**Kotlin / pseudo-code 예제**:
```kotlin
// longest-prefix match — forwarding table 핵심 (선형 스캔 버전; 실제는 trie/TCAM)
data class Route(val prefix: Int, val maskLen: Int, val nextHop: String)

// "10.1.2.0/24" 같은 prefix 를 32-bit Int 로
fun ipToInt(ip: String): Int =
    ip.split(".").fold(0) { acc, oct -> (acc shl 8) or oct.toInt() }

// CIDR maskLen → netmask (예: 24 -> 0xFFFFFF00)
fun maskOf(len: Int): Int = if (len == 0) 0 else (-1 shl (32 - len))

fun lookup(table: List<Route>, dst: String): Route? {
    val d = ipToInt(dst)
    return table
        .filter { (d and maskOf(it.maskLen)) == (it.prefix and maskOf(it.maskLen)) } // 매칭되는 모든 prefix
        .maxByOrNull { it.maskLen }   // ← longest prefix 승리 (가장 구체적)
}

val fib = listOf(
    Route(ipToInt("0.0.0.0"),   0,  "default-gw"),  // default route, 최후순위
    Route(ipToInt("10.1.0.0"),  16, "router-A"),
    Route(ipToInt("10.1.2.0"),  24, "router-B"),     // 더 구체적
)
// 10.1.2.7 -> /24 매칭 + /16 매칭 + /0 매칭 → maskLen 최대인 router-B 선택
println(lookup(fib, "10.1.2.7")?.nextHop)   // router-B
println(lookup(fib, "8.8.8.8")?.nextHop)    // default-gw (오직 /0 매칭)
```

**관련 패턴**: [DNS Patterns](#dns-patterns), [CDN / Edge](#cdn-edge), [TCP vs UDP](#tcp-udp), [NAT Traversal](#nat-traversal)

---

<a id="reliable-data-transfer"></a>

## 15. Reliable Data Transfer / ARQ (신뢰성 데이터 전송 / ARQ)

**목적/정의**: 손실·중복·순서 뒤바뀜이 가능한 비신뢰 채널 위에서 무손실·순서 보장 전달을 구축하는 핵심 원리. ARQ (Automatic Repeat reQuest) 는 sequence number + ACK/NAK + timeout 재전송으로 신뢰성을 달성합니다. Stop-and-Wait → Go-Back-N → Selective Repeat 로 발전했으며, sliding window 흐름 제어와 결합되어 TCP (RFC 9293) 신뢰성·flow control 의 직접적 기반이 됩니다. Kurose & Ross 의 `rdt 1.0~3.0` 점진 모델로 정평.

**메커니즘**:
- **Sequence number (seq)**: 각 패킷에 고유 번호 부여 → 수신측이 중복 검출·순서 복원. **Cumulative ACK** (ACK n = "n 까지 다 받음") 또는 selective ACK 사용
- **ACK / NAK / timeout**: 송신측은 ACK 수신까지 패킷 보관, RTO (Retransmission Timeout) 만료 시 재전송. NAK 는 명시적 손실 통보(생략 시 timeout 만 의존)
- **Stop-and-Wait (rdt 3.0)**: 한 번에 1 패킷만 전송 후 ACK 대기. 1-bit seq (0/1) 로 충분. 단순하나 utilization = `L/R / (RTT + L/R)` 로 RTT 큰 link 에서 처참
- **Go-Back-N (GBN)**: window 크기 N 만큼 ACK 없이 연속 전송. cumulative ACK. 손실 발생 시 **해당 패킷부터 window 끝까지 전부 재전송** → 수신 버퍼 불필요(out-of-order 폐기)하나 손실 시 재전송 낭비
- **Selective Repeat (SR)**: 개별 패킷 단위 ACK + 손실 패킷만 재전송. 수신측이 out-of-order 패킷을 버퍼링. seq 공간 ≥ 2 × window 필요(미달 시 ambiguity). 효율 최고, 복잡도·버퍼 비용 증가
- **Sliding window flow control**: 송신 window(`swnd`) + 수신 window(`rwnd`) 로 receiver overflow 방지. 송신 가능량 = `min(cwnd, rwnd)` (TCP 는 congestion window 와 결합)
- **utilization 향상**: window 를 키워 RTT 한 번에 N 패킷 in-flight → 이상적으로 `N·L/R / (RTT + L/R)`

**장점**:
- 비신뢰 채널 위에 무손실·순서 보장이라는 강한 추상화 제공
- pipelining (GBN/SR) 으로 link utilization 을 Stop-and-Wait 대비 N 배 향상
- sliding window 로 빠른 송신측이 느린 수신측을 압도하지 않도록 흐름 제어

**단점·트레이드오프**:
- Stop-and-Wait: RTT 지배 환경에서 utilization 극저 (대역 낭비)
- GBN: 단일 손실에 window 전체 재전송 → 손실률 높은 link 에서 비효율
- SR: 수신 버퍼 + per-packet 타이머 + seq 공간 제약(≥2×window) 으로 구현 복잡
- 고정 RTO 는 가변 RTT 에 취약 → 적응형 RTO (Jacobson/Karels: `SRTT`, `RTTVAR`) 필요
- 신뢰성 자체는 congestion control 과 별개 — window 만 키우면 혼잡 유발

**활용 예시**:
- TCP: cumulative ACK + sliding window + 적응형 RTO + fast retransmit (SR 성향의 SACK, RFC 2018) 의 혼합
- QUIC (RFC 9002): 단조 증가 packet number + ACK ranges 로 SR 스타일 loss detection
- KCP / RUDP / ENet: UDP 위 ARQ 변형 (앞 항목 참조)
- 데이터링크: HDLC, LAPB 의 GBN/SR window
- 애플리케이션 레벨 at-least-once 메시징의 ACK/재전송 의미론

**난이도**: 높음

**Kotlin / pseudo-code 예제**:
```kotlin
// Selective Repeat 송신측 핵심 — sliding window + per-packet timer + 개별 ACK
class SelectiveRepeatSender(
    private val windowSize: Int,          // N: in-flight 상한
    private val rtoMs: Long = 200,
) {
    private data class InFlight(var sentAt: Long, val payload: ByteArray, var acked: Boolean = false)

    private val window = LinkedHashMap<Long, InFlight>() // seq -> 상태
    private var nextSeq = 0L                              // 다음 부여할 seq
    private var sendBase = 0L                             // 가장 오래된 unacked seq

    /** window 에 여유가 있으면 즉시 전송, 아니면 호출측이 backpressure */
    fun trySend(data: ByteArray, now: Long, transmit: (Long, ByteArray) -> Unit): Boolean {
        if (nextSeq >= sendBase + windowSize) return false // window full → flow control
        window[nextSeq] = InFlight(sentAt = now, payload = data)
        transmit(nextSeq, data)
        nextSeq++
        return true
    }

    /** 개별 ACK 처리 (SR: 누적이 아니라 해당 seq 만 ack) */
    fun onAck(seq: Long) {
        window[seq]?.acked = true
        // sendBase 를 연속 acked 구간만큼 전진 → window slide
        while (window[sendBase]?.acked == true) window.remove(sendBase++)
    }

    /** RTO 만료된 패킷만 선택 재전송 (GBN 과 달리 window 전체가 아님) */
    fun onTick(now: Long, transmit: (Long, ByteArray) -> Unit) {
        for ((seq, f) in window) {
            if (!f.acked && now - f.sentAt >= rtoMs) {
                transmit(seq, f.payload)               // 해당 패킷만 재전송
                f.sentAt = now
            }
        }
    }
}
// Go-Back-N 대비: onAck 가 cumulative 이고, onTick 이 sendBase 부터 nextSeq 까지 전부 재전송이면 GBN.
```

**관련 패턴**: [TCP vs UDP](#tcp-udp), [TCP Congestion Control](#tcp-congestion-control), [Reliable UDP / KCP / RUDP](#reliable-udp), [QUIC / HTTP/3](#quic-http3)
