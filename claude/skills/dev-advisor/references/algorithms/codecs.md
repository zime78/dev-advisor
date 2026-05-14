# 코덱·미디어 알고리즘 (Codec & Media Algorithms)

이미지 / 동영상 / 오디오 코덱 정평 있는 8 알고리즘. [`compression.md`](compression.md) (LZ77/Huffman/RLE 같은 *범용 압축*) 와 differentiate — 본 파일은 **미디어 특화 코덱**.

**원전·표준 참고**:
- ITU-T T.81 (JPEG), W3C PNG Specification, ITU-T H.264/H.265/H.266
- ISO/IEC 14496-3 (AAC), RFC 6716 (Opus)
- *Introduction to Data Compression*, Khalid Sayood, 5th ed. (2017)
- *Video Compression* — Iain Richardson, 2nd ed. (2010)
- AV1 Bitstream & Decoding Process Specification (Alliance for Open Media)
- Jarek Duda — Asymmetric Numeral Systems (2009)
- Bell Labs psychoacoustic model

## 알고리즘 목차

| ID | 알고리즘 | 카테고리 | 압축 |
|----|---------|---------|------|
| [jpeg](#jpeg) | JPEG (DCT) | Image | lossy |
| [png](#png) | PNG (DEFLATE) | Image | lossless |
| [webp-avif-heic](#webp-avif-heic) | WebP/AVIF/HEIC | Image | modern |
| [h264](#h264) | H.264 (AVC) | Video | 기준 |
| [h265-h266-av1](#h265-h266-av1) | HEVC/VVC/AV1 | Video | next-gen |
| [mp3-aac](#mp3-aac) | MP3 / AAC | Audio | perceptual |
| [opus](#opus) | Opus | Audio | low-latency |
| [entropy-coding](#entropy-coding) | Arithmetic/Range/ANS | Entropy | post-Huffman |

**관련 카탈로그**:
- [compression.md](compression.md) — LZ77 / Huffman / RLE / BWT (범용)
- [math.md](math.md) — FFT / DCT / Wavelet (signal processing 기초)
- [`../patterns/networking.md`](../patterns/networking.md) — HTTP/3 (미디어 전송)
- [crypto.md](crypto.md) — DRM·암호화 (미디어 보호)

---

<a id="jpeg"></a>
## 1. JPEG (DCT-based, ITU-T T.81)

**개념**: 8×8 블록 단위 **Discrete Cosine Transform (DCT)** 으로 공간 도메인 픽셀을 주파수 도메인으로 변환한 뒤, **양자화(quantization)** 로 고주파 성분을 버리고 Huffman 으로 엔트로피 부호화하는 **lossy** 이미지 코덱.

**압축 파이프라인**:
```
RGB → YCbCr 색공간 변환 → Chroma Subsampling (4:2:0 등)
    → 8×8 블록 분할 → DCT (forward)
    → Quantization (Q-table 나눗셈)
    → Zig-Zag scan → Run-Length 인코딩
    → Huffman (DC + AC 분리)
```

**DCT 수식** (2D forward DCT, 8×8 블록):
```
F(u,v) = (1/4) C(u) C(v) Σ Σ f(x,y) · cos[(2x+1)uπ/16] · cos[(2y+1)vπ/16]
                          x=0..7 y=0..7
C(0) = 1/√2,  C(k>0) = 1
```

**양자화**: `F'(u,v) = round(F(u,v) / Q(u,v))` — Q-table 은 고주파일수록 큰 값 → 고주파 성분 0 으로 만듦. 이게 lossy 의 핵심.

**압축률**: 일반 사진 기준 **10:1 ~ 20:1** (24bpp → 1.2~2.4bpp). Quality 50 기준 PSNR ~32dB.

**baseline vs progressive**:
- **Baseline**: 위에서 아래로 순차 디코드. 다운로드 중에는 윗부분만 보임
- **Progressive**: DC 계수 먼저 전체, AC 계수를 단계적으로 추가 → 다운로드 중 흐릿한 전체 → 점차 선명
- **Lossless mode**: T.81 에 정의되어 있으나 거의 미사용 (PNG/WebP-LL 가 우세)

**장점**:
- 자연 이미지(사진)에서 압축률·품질 균형 우수
- 사실상 모든 디바이스·브라우저·OS 지원 (30+ 년 유산)
- 디코더 빠름, ASIC/SoC 가속 광범위

**단점**:
- 텍스트·라인 아트·로고에서 **ringing artifact** (8×8 블록 경계 mosquito noise)
- 알파 채널 없음
- HDR / 10bit+ 지원 약함 (JPEG XT 확장 있으나 보급 X)
- 8×8 블록 자체가 시각적 결함 원인

**실제 사용**:
- 디지털 카메라 (DCF/EXIF), 웹 사진, JPEG 2000 (wavelet 기반 후속, 의료/시네마 DCI 에서)
- HEIC/AVIF 가 모바일에서 잠식 중이나 호환성에서 JPEG 압도

**Python 예제 (Pillow)**:
```python
from PIL import Image
import io

# 인코딩
img = Image.open("photo.png")
buf = io.BytesIO()
img.convert("RGB").save(
    buf, format="JPEG",
    quality=85,            # 1~95 권장 (95 초과는 손실 대비 비효율)
    progressive=True,      # progressive 모드
    optimize=True,         # Huffman table 최적화
    subsampling=2,         # 0=4:4:4, 1=4:2:2, 2=4:2:0 (기본)
)
print(f"JPEG size: {len(buf.getvalue())} bytes")

# 디코더에서 quality 추정 (Q-table 분석)
import numpy as np
def estimate_quality(qtable):
    # 표준 luma Q-table 과 비교 → quality factor 역추정
    std_q = np.array([16,11,10,16,24,40,51,61])  # 첫 8개만
    ratio = qtable[:8] / std_q
    return int(50 / np.mean(ratio)) if np.mean(ratio) > 0 else 50
```

**관련 알고리즘**: DCT ([math.md](math.md)), Huffman ([greedy.md](greedy.md#2-huffman-coding-허프만-코딩)), JPEG2000 (wavelet 기반), [webp-avif-heic](#webp-avif-heic) (intra-frame 후속)

---

<a id="png"></a>
## 2. PNG (DEFLATE-based, W3C/ISO 15948)

**개념**: 행 단위 **filter** (예측기) 로 인접 픽셀 차이를 만들어 entropy 를 낮춘 뒤, **DEFLATE (LZ77 + Huffman)** 로 압축하는 **lossless** 이미지 코덱. 알파 채널·indexed color·gamma·sRGB 메타데이터를 표준 지원.

**압축 파이프라인**:
```
RGB(A) → 행별 filter (5 종 중 선택)
       → DEFLATE (LZ77 sliding window + Huffman)
       → IDAT chunk 로 패킹
```

**5 종 filter** (각 행마다 최적 선택):
| 코드 | 이름 | 수식 (현재 픽셀 X, 좌 A, 위 B, 좌상 C) |
|---|---|---|
| 0 | None | X (변환 없음) |
| 1 | Sub | X − A |
| 2 | Up | X − B |
| 3 | Average | X − ⌊(A + B) / 2⌋ |
| 4 | Paeth | X − Paeth(A, B, C) |

**Paeth predictor**: `p = A + B − C; closest of A,B,C to p`. 매끄러운 그라디언트에서 가장 우수.

**압축률**: 사진은 JPEG 대비 **2~5× 큼** (lossless 한계). 라인 아트/스크린샷/UI 자산에서는 GIF 대비 **10~30% 더 작음**.

**장점**:
- 무손실 + 알파 채널 + 1/2/4/8/16 bit depth
- 모든 브라우저·OS 지원
- DEFLATE 라이브러리(zlib) 보편 → 디코더 안정성 검증됨
- Interlaced 모드 (Adam7) — 7-pass progressive

**단점**:
- 사진에서 JPEG 대비 압축률 열위
- 인코딩 느림 (filter 선택 + DEFLATE 풀 스캔)
- 단일 이미지만 (애니메이션은 APNG 확장, MNG 폐기됨)

**실제 사용**:
- 웹 UI 자산, 스크린샷, 라인 아트, 로고
- 게임 텍스처 (lossless 필요할 때)
- 의료·과학 시각화 (lossless 필수)

**Python 예제 (Pillow + zopfli 권장)**:
```python
from PIL import Image
import io

img = Image.open("logo.svg.png")

# 기본 PNG 저장
buf = io.BytesIO()
img.save(buf, format="PNG", optimize=True, compress_level=9)
print(f"PNG: {len(buf.getvalue())} bytes")

# zopfli (DEFLATE 의 brute-force optimizer, 5~30% 더 작음, 매우 느림)
try:
    import zopfli.png
    optimized = zopfli.png.optimize_png(buf.getvalue())
    print(f"PNG (zopfli): {len(optimized)} bytes")
except ImportError:
    pass

# 행 필터 분석 (학습용)
import numpy as np
def paeth_predictor(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc: return a
    elif pb <= pc: return b
    else: return c
```

**관련 알고리즘**: [DEFLATE](compression.md#2-lz77-lempel-ziv-1977-슬라이딩-윈도우) (LZ77 + Huffman), APNG (animated extension), [jpeg](#jpeg) (lossy 대척점)

---

<a id="webp-avif-heic"></a>
## 3. WebP / AVIF / HEIC (Modern Image Codecs)

**개념**: 비디오 코덱의 **intra-frame (I-frame) 압축 기법** 을 정지 이미지에 차용한 차세대 코덱 3 종. JPEG/PNG 의 한계 (블록 artifact, 알파 채널 부재, HDR 미지원) 를 해결.

**3 종 비교**:

| 코덱 | 베이스 비디오 코덱 | 표준 | 컨테이너 | 알파 | HDR | 애니메이션 |
|---|---|---|---|---|---|---|
| **WebP** | VP8 | Google (2010) | RIFF | ◯ | ✕ | ◯ |
| **HEIC** | HEVC (H.265) | MPEG-H Part 12 (2015) | HEIF (ISOBMFF) | ◯ | ◯ (10/12 bit) | ◯ |
| **AVIF** | AV1 | AOMedia + MIAF (2019) | HEIF | ◯ | ◯ (10/12 bit) | ◯ |

**핵심 기법** (3 종 공통):
- **Intra Prediction**: 블록 내부에서 인접 픽셀로 현재 블록 예측 (수직/수평/대각 등 35+ 모드, JPEG 의 DCT-only 대비 강력)
- **Larger Transform Blocks**: 4×4 ~ 64×64 (JPEG 의 8×8 고정 대비)
- **Loop Filter**: 블록 경계 deblocking → 8×8 mosquito noise 제거
- **CABAC / Arithmetic Coding**: Huffman 보다 압축률 우수 ([entropy-coding](#entropy-coding) 참고)

**압축률** (동일 PSNR 기준 JPEG 대비):
- WebP: **25~35% 더 작음**
- HEIC: **40~50% 더 작음**
- AVIF: **50% 더 작음** (현재 최강)

**장점**:
- JPEG 대비 절반 크기로 동일 품질
- 알파 채널·HDR·wide color gamut (Rec.2020) 지원
- AVIF/HEIC 은 애니메이션 (motion JPEG 대안)

**단점**:
- **인코딩 매우 느림**: AVIF 가 JPEG 의 100~1000×
- HEIC 는 **특허/로열티 부담** (Nokia, Apple 사용 권리)
- AV1 (AVIF 기반) 은 royalty-free 지만 인코더 성숙도 부족
- 디코더 호환성: Chrome/Firefox/Safari 만점, 구형 OS / 이메일 클라이언트 부족

**실제 사용**:
- WebP: Google 검색 / YouTube 썸네일 (보편)
- HEIC: iPhone 사진 (iOS 11+ 기본)
- AVIF: Netflix·Cloudflare·Vercel (CDN 측 자동 변환)

**Python 예제 (Pillow + pillow-avif-plugin)**:
```python
from PIL import Image
import io

img = Image.open("photo.jpg")

# WebP (Pillow 내장)
buf_webp = io.BytesIO()
img.save(buf_webp, format="WebP", quality=80, method=6)  # method 0~6, 높을수록 느림+압축↑
print(f"WebP: {len(buf_webp.getvalue())} bytes")

# AVIF (pillow-avif-plugin 필요)
try:
    import pillow_avif  # noqa: F401  (import 만으로 register)
    buf_avif = io.BytesIO()
    img.save(
        buf_avif, format="AVIF",
        quality=60,        # WebP/JPEG quality 와 스케일 다름 — 60 ≈ JPEG 80
        speed=6,           # 0~10, 낮을수록 느림+압축↑
        codec="aom",
    )
    print(f"AVIF: {len(buf_avif.getvalue())} bytes")
except ImportError:
    pass

# HEIC (pyheif 또는 pillow-heif)
# from pillow_heif import register_heif_opener
# register_heif_opener()
# img.save("photo.heic", quality=70)
```

**관련 알고리즘**: [h264](#h264), [h265-h266-av1](#h265-h266-av1) (비디오 베이스), [entropy-coding](#entropy-coding)

---

<a id="h264"></a>
## 4. H.264 / AVC (ITU-T Rec. H.264 | ISO/IEC 14496-10)

**개념**: **블록 기반 motion compensation** 으로 시간 축 중복 (temporal redundancy) 을 제거하고, **DCT-like integer transform** 으로 공간 축 중복을 제거하는 비디오 코덱. **CABAC** 엔트로피 코딩으로 마무리. 2003 년 표준화 이후 사실상 비디오의 lingua franca.

**핵심 개념 — Frame 타입**:

| 타입 | 정식명 | 참조 | 특징 |
|---|---|---|---|
| **I-frame** | Intra-coded | 자기 자신만 | JPEG 와 유사한 정지 이미지. 시작점·seek point. GOP 의 첫 프레임 |
| **P-frame** | Predicted | 이전 I/P | 이전 프레임으로부터 motion vector 로 예측. I 대비 ~30% 크기 |
| **B-frame** | Bi-directional | 이전+미래 I/P | 양방향 예측. P 대비 더 작음. 디코드 지연 ↑ |

**GOP (Group of Pictures)**: `I B B P B B P B B P ...` 패턴. GOP 크기 (= keyframe interval) 가 클수록 압축률 ↑, seek 정밀도 ↓.

**압축 파이프라인** (P-frame 기준):
```
1. Motion Estimation: 16×16 macroblock 단위로 참조 프레임에서 가장 비슷한 블록 검색
   → motion vector (dx, dy) 산출
2. Motion Compensation: 참조 블록 + motion vector 로 예측 블록 생성
3. Residual = 현재 블록 − 예측 블록 (대부분 0 근처)
4. Integer DCT → Quantization
5. Zig-Zag scan → CABAC (Context-Adaptive Binary Arithmetic Coding)
6. In-Loop Deblocking Filter (블록 경계 부드럽게)
```

**압축률**: MPEG-2 대비 **2×** (동일 품질 절반 비트레이트). 1080p 영화 ~5~10 Mbps.

**Profile / Level**:
- **Baseline**: 모바일·화상통화 (B-frame 없음, CAVLC)
- **Main**: SDTV
- **High**: Blu-ray, 스트리밍 (CABAC, 8×8 transform, 가장 보편)
- **Level 4.1**: 1080p@30, Level 5.1: 4K@30

**장점**:
- 사실상 모든 디바이스에 HW 디코더 (ASIC) — 배터리 소모 최소
- 압축률·복잡도·호환성 균형 최강
- 안정적 spec, 도구 생태계 성숙 (FFmpeg, x264)

**단점**:
- 라이센스 (MPEG LA pool) — 디코더 무료, 인코더는 유료 (스트리밍 사업자)
- HEVC/AV1 대비 압축률 떨어짐 (~40% 더 큼)
- 8-bit, Rec.709 만 본질 지원 (10-bit, HDR 은 확장)

**실제 사용**:
- Blu-ray, YouTube/Netflix 기본 폴백, Zoom/Teams, 모바일 카메라
- 거의 모든 비디오 컨테이너 (MP4, MKV, FLV) 의 기본 비디오 트랙

**FFmpeg 예제 (Python ffmpeg-python)**:
```python
import ffmpeg

# H.264 인코딩 (x264, CRF 모드 = 일정 품질)
(
    ffmpeg
    .input("input.mov")
    .output(
        "output.mp4",
        vcodec="libx264",
        crf=23,             # 0=lossless, 18=시각적 무손실, 23=기본, 28=낮은 품질
        preset="medium",    # ultrafast~veryslow (느릴수록 압축률↑)
        profile="high",
        level="4.1",
        pix_fmt="yuv420p",  # 4:2:0 chroma subsampling
        movflags="+faststart",  # MP4 meta 를 앞으로 → 스트리밍 시작 빠름
        acodec="aac", audio_bitrate="128k",
    )
    .overwrite_output()
    .run()
)

# 2-pass (target bitrate 정밀 제어)
common = {"vcodec": "libx264", "video_bitrate": "5M"}
ffmpeg.input("input.mov").output("/dev/null", pass_=1, **common, format="null").run()
ffmpeg.input("input.mov").output("output.mp4", pass_=2, **common).run()
```

**관련 알고리즘**: [DCT](math.md), Motion Estimation (block matching), [entropy-coding](#entropy-coding) (CABAC), [h265-h266-av1](#h265-h266-av1) (후속)

---

<a id="h265-h266-av1"></a>
## 5. H.265 (HEVC) / H.266 (VVC) / AV1 (Next-Gen Video)

**개념**: H.264 의 16×16 매크로블록을 **CTU (Coding Tree Unit, 최대 64×64 또는 128×128) + Quadtree 분할** 로 확장하고, intra prediction mode 를 35+ 로 늘려 **50% 더 압축**하는 차세대 비디오 코덱 3 종.

**3 종 비교**:

| 코덱 | 표준화 | 표준 기관 | 라이선스 | H.264 대비 |
|---|---|---|---|---|
| **HEVC (H.265)** | 2013 | ITU-T/MPEG | MPEG LA + HEVC Advance + Velos (**triple-pool**) | **−50% bitrate** |
| **AV1** | 2018 | AOMedia (Google+Netflix+Cisco+...) | **Royalty-free** | **−50% bitrate** |
| **VVC (H.266)** | 2020 | ITU-T/MPEG | MPEG LA 단일 | **−50% vs HEVC** = −75% vs H.264 |

**공통 핵심 기법**:
- **CTU + Quadtree**: 최대 64×64 (HEVC) / 128×128 (AV1, VVC) 블록을 재귀 분할. 평탄 영역은 큰 블록, 복잡 영역은 작은 블록
- **35+ Intra Prediction Modes**: H.264 의 9 모드 대비 4×↑
- **Improved Motion Compensation**: 1/4 → 1/16 pixel precision, 비대칭 분할
- **SAO (Sample Adaptive Offset)** / **CDEF (AV1)**: ringing artifact 제거 후처리
- **Tile-based parallel decoding**: 멀티스레드 디코드

**압축률** (동일 PSNR 기준):
- HEVC: H.264 대비 **−50%** (4K@60fps 가 H.264 1080p 와 동일 비트레이트)
- AV1: HEVC 와 동등 또는 5~10% 우위
- VVC: HEVC 대비 **−50%**, AV1 대비 ~10% 우위

**장점**:
- 4K/8K HDR 시대 필수 — 4K@60fps 가 ~15 Mbps 로 가능
- AV1 은 **royalty-free** → YouTube/Netflix 전면 채택
- HW 디코더 보급 가속 중 (iPhone 7+, Android 8+, NVIDIA RTX 30+)

**단점**:
- **인코딩 매우 느림**: AV1 SW (libaom) 가 x264 의 50~100×, x265 가 x264 의 5~10×
- HEVC 는 **3 개 특허 풀** → 라이선스 정글 (Microsoft 가 HEVC 디코더에 윈도우 추가 결제 요구하는 이유)
- 구형 디바이스 (iOS 10 이하, 저가 Android) 디코더 부재
- AV1 인코더 성숙도 부족 (libaom slow, SVT-AV1 fast 하지만 품질 trade-off)

**실제 사용**:
- HEVC: iPhone 카메라 (HEIC + HEVC), Apple TV 4K, Blu-ray UHD, Netflix HDR
- AV1: YouTube (8K), Netflix Premium tier, Chrome/Firefox
- VVC: 8K 방송 (시작 단계), 6G 라이브 스트리밍 후보

**FFmpeg 예제**:
```python
import ffmpeg

# HEVC (x265)
ffmpeg.input("input.mov").output(
    "out_hevc.mp4",
    vcodec="libx265",
    crf=28,                # HEVC 의 CRF 28 ≈ x264 의 CRF 23
    preset="medium",
    **{"x265-params": "log-level=warning"},
    tag="hvc1",            # Apple QuickTime/iOS 호환 (기본 hev1 은 Safari 거부)
    pix_fmt="yuv420p10le", # 10-bit (HDR 권장)
).overwrite_output().run()

# AV1 (libaom, 매우 느림)
ffmpeg.input("input.mov").output(
    "out_av1.mp4",
    vcodec="libaom-av1",
    crf=30, **{"b:v": "0"},
    cpu_used=6,            # 0~8, 높을수록 빠름+품질↓ (8 은 실시간 근접)
    row_mt=1,              # 멀티스레드 row decode
).overwrite_output().run()

# AV1 (SVT-AV1, libaom 의 5~10× 빠름, Netflix 권장)
ffmpeg.input("input.mov").output(
    "out_svtav1.mp4",
    vcodec="libsvtav1",
    crf=30, preset=6,      # 0(slowest)~13(fastest)
).overwrite_output().run()
```

**관련 알고리즘**: [h264](#h264) (전 세대), [entropy-coding](#entropy-coding), [webp-avif-heic](#webp-avif-heic) (intra-frame 차용)

---

<a id="mp3-aac"></a>
## 6. MP3 / AAC (Perceptual Audio Coding)

**개념**: **Psychoacoustic Model (심리음향 모델)** 을 사용해 사람이 못 듣는 주파수 성분 (**masking** 으로 가려지는) 을 식별 후 제거하는 lossy 오디오 코덱.

**MP3 vs AAC**:

| 항목 | MP3 | AAC |
|---|---|---|
| 표준 | MPEG-1/2 Audio Layer III (1993) | MPEG-2/4 Part 7 (1997) |
| 변환 | 32-band PQF + MDCT(18) | **MDCT(1024/128)** — 더 효율 |
| 채널 | Stereo + Joint Stereo | up to 48 채널 (5.1, 7.1, Atmos) |
| 권장 비트레이트 | 192~320 kbps | **96~256 kbps** (동등 품질) |
| 라이선스 | 만료 (2017) | MPEG LA 진행중 |

**Psychoacoustic Masking 2 종**:
1. **Frequency Masking (동시 마스킹)**: 큰 소리가 인접 주파수의 작은 소리를 가림. 예) 1kHz 80dB tone 옆 1.1kHz 60dB tone 들리지 않음
2. **Temporal Masking (시간 마스킹)**:
   - **Pre-masking**: 큰 소리 직전 5ms (귀가 적응 못 함)
   - **Post-masking**: 큰 소리 직후 100~200ms

**압축 파이프라인**:
```
PCM (16-bit, 44.1kHz) → MDCT (Modified DCT, overlapping window)
                      → Psychoacoustic Model 로 masking threshold 계산
                      → 각 frequency bin 의 quantizer 결정 (가려질 만큼만 정밀도)
                      → Huffman (MP3) 또는 Noiseless Coding (AAC)
                      → bit reservoir (가변 비트레이트 평활)
```

**MDCT (Modified Discrete Cosine Transform)**:
- 50% overlap window 로 블록 경계 artifact 제거
- 1024-point (AAC long block) / 128-point (AAC short block, transient 시 자동 전환)

**압축률**: PCM 1.4 Mbps (CD) → **128 kbps (~11×)** 가 일반 인지 한계.

**비트레이트 가이드**:
| 비트레이트 | MP3 품질 | AAC 품질 | 용도 |
|---|---|---|---|
| 64 kbps | 라디오 미만 | AM 라디오 수준 | 팟캐스트 voice |
| 128 kbps | "MP3 표준" | CD 근접 | 일반 음악 |
| 192~256 kbps | CD 근접 | CD 동등 | 고품질 |
| 320 kbps | "MP3 최대" | overkill | 아카이브 |

**장점**:
- 사실상 모든 디바이스 지원 (MP3 는 30+ 년, AAC 는 20+ 년)
- HW 디코더 보편 → 배터리 소모 최소
- 적절한 비트레이트에서 **무손실 청취 구분 불가**

**단점**:
- Lossy — 재인코딩 시 누적 손실
- Pre-echo: transient (drum hit) 직전 ringing artifact
- 70Hz 이하 / 16kHz 이상 보존 약함

**실제 사용**:
- MP3: 레거시 음원 파일, 팟캐스트
- AAC: iTunes, YouTube, Spotify, iPhone 통화, Apple Music
- AAC 변형: HE-AAC (low bitrate), xHE-AAC (DRC, Amazon Audible)

**Python 예제 (ffmpeg-python)**:
```python
import ffmpeg

# MP3 (LAME, 가변 비트레이트 권장 = -q:a)
ffmpeg.input("input.wav").output(
    "out.mp3", acodec="libmp3lame",
    **{"q:a": 2},          # 0(best,~245kbps)~9(worst,~65kbps), 2 ≈ 190kbps VBR
).overwrite_output().run()

# AAC (FDK-AAC 가 최고 품질, but 라이선스 제약 → libfdk_aac 컴파일 필요)
ffmpeg.input("input.wav").output(
    "out.aac", acodec="aac",   # FFmpeg 내장 (FDK 보다 품질 낮음)
    audio_bitrate="128k",
).overwrite_output().run()

# Joint Stereo / Mid-Side encoding (스테레오 효율↑)
ffmpeg.input("input.wav").output(
    "out.mp3", acodec="libmp3lame",
    audio_bitrate="192k",
    **{"joint_stereo": 1},
).overwrite_output().run()
```

**관련 알고리즘**: [DCT](math.md) (MDCT 베이스), [Huffman](compression.md), [opus](#opus) (저지연 후속)

---

<a id="opus"></a>
## 7. Opus (RFC 6716, IETF Internet Voice/Audio Standard)

**개념**: **SILK (Skype, voice 특화) + CELT (Xiph, music 특화)** 2 코덱을 하이브리드 결합한 IETF 표준 오디오 코덱. **저지연** (5ms~) + **광대역** (6~510 kbps) + **로열티 프리**.

**하이브리드 구조**:
- **SILK** (linear prediction, LPC 기반): 8kHz/12kHz/16kHz/24kHz 샘플링, voice 에서 효율
- **CELT** (MDCT, transform 기반): 48kHz, music 에서 효율
- **Hybrid mode**: SILK + CELT 동시 사용 (24kHz 미만 SILK, 그 이상 CELT)
- 인코더가 입력에 따라 자동 전환 — 사용자 의식 안 함

**핵심 매개변수**:

| Mode | 샘플링 | 적정 비트레이트 | 적정 용도 |
|---|---|---|---|
| Narrowband (SILK) | 8 kHz | 6~20 kbps | 음성 통화 (전화급) |
| Wideband (SILK) | 16 kHz | 12~32 kbps | HD voice |
| Super-wideband (Hybrid) | 24 kHz | 24~64 kbps | 화상회의 |
| Fullband (CELT) | 48 kHz | 32~510 kbps | 음악 |

**Frame size (지연)**: 2.5 / 5 / 10 / 20 / 40 / 60 ms — **5ms 가 라이브 게이밍**, **20ms 가 WebRTC 기본**.

**압축률**:
- 32 kbps Opus ≈ 64 kbps AAC ≈ 128 kbps MP3 (음성 기준)
- 96 kbps Opus ≈ 128 kbps AAC (음악 기준)
- **모든 비트레이트에서 AAC/MP3 압도** (2016 listening test)

**장점**:
- **로열티 프리** — WebRTC, Zoom, Discord, YouTube 채택 이유
- **저지연** — 5~20ms (AAC 의 100~200ms 대비)
- **광범위 비트레이트** — 6 kbps (전화) ~ 510 kbps (음악)
- **packet loss concealment** 내장 — VoIP/스트리밍 패킷 손실에 강함
- 음성과 음악 자동 전환

**단점**:
- 구형 HW 디코더 없음 (모두 SW 디코드) → 모바일 배터리 약간 손해
- 컨테이너 호환성 — MP4 안에 넣을 때 일부 player 거부
- 비디오 코덱처럼 ASIC 가속이 없어 동시 디코드 수 제한

**실제 사용**:
- **WebRTC** (Chrome, Firefox, Safari) - 기본 오디오 코덱
- **Discord** (게임 보이스), **Zoom**, **Microsoft Teams**
- **YouTube** (Vorbis 후속), **PS4/PS5 보이스챗**
- **Telegram voice messages**, **WhatsApp calls**

**Python 예제 (ffmpeg-python + opuslib)**:
```python
import ffmpeg

# Opus 인코딩 (FFmpeg libopus)
ffmpeg.input("input.wav").output(
    "out.opus",
    acodec="libopus",
    audio_bitrate="64k",
    **{
        "application": "audio",     # voip | audio | lowdelay
        "frame_duration": 20,        # 2.5, 5, 10, 20, 40, 60 ms
        "vbr": "on",                # constrained-vbr / off 도 가능
        "compression_level": 10,    # 0~10, 높을수록 느림+품질↑ (인코딩만)
    },
).overwrite_output().run()

# 실시간 voice 용 저지연 설정
ffmpeg.input("mic_input.wav").output(
    "voice.opus",
    acodec="libopus",
    audio_bitrate="32k",
    **{
        "application": "voip",       # voice DSP (DTX, noise gate)
        "frame_duration": 10,        # 10ms 지연
        "packet_loss": 10,           # 10% 패킷 손실 예상 → FEC 활성
        "vbr": "off",                # CBR (네트워크 jitter 최소)
    },
).overwrite_output().run()
```

**관련 알고리즘**: [mp3-aac](#mp3-aac) (구세대), LPC (Linear Prediction Coding), [MDCT](math.md), WebRTC

---

<a id="entropy-coding"></a>
## 8. Entropy Coding (Arithmetic / Range / ANS)

**개념**: Shannon entropy 한계에 근접하는 무손실 부호화 기법. **Huffman 의 정수 비트 제약** 을 넘어 fractional bit 를 부여하여 압축률을 짜낸다. 대부분의 모던 코덱 (H.264/265/AV1, JPEG-XL, zstd) 의 **마지막 단계** 에 사용.

**3 종 비교**:

| 기법 | 시기 | 핵심 idea | 속도 | 활용 |
|---|---|---|---|---|
| **Arithmetic Coding** | 1976 | 메시지 → [0,1) 실수 | 느림 | JPEG2000, H.264/265 CABAC |
| **Range Coding** | 1979 | Arithmetic 의 정수 정밀도 변형 | 보통 | LZMA, 7z |
| **ANS** (Asymmetric Numeral Systems) | 2009 (Duda) | **상태 머신** 으로 인코딩 | **빠름** (Huffman 급) | zstd, AV1, JPEG-XL |

### 8.1 Arithmetic Coding (산술 부호화)

**원리**: 메시지 전체를 [0,1) 구간의 단일 실수로 부호화. 각 심볼이 등장할 때마다 현재 구간을 심볼 확률에 따라 분할.

```
초기:           [0.0, 1.0)
'A' (P=0.6):    [0.0, 0.6)
'B' (P=0.3):    [0.42, 0.6)
'C' (P=0.1):    [0.534, 0.546)
...
```

**장점**: 이론적 entropy 한계까지 도달. Huffman 이 정수 비트 (1 심볼 = 1 비트 이상) 제약을 받는 반면, AC 는 0.001 비트도 표현 가능.

**단점**: 실수 정밀도 문제 → 실제 구현은 정수 산술 + renormalization. **특허** (~2010 만료) 가 보급 늦춤.

자세한 코드 예제는 [compression.md §4 Arithmetic Coding](compression.md#arithmetic-coding) 참조.

### 8.2 Range Coding (구간 부호화)

**원리**: Arithmetic Coding 의 변형. 실수 [0,1) 대신 **정수 큰 범위 [0, 2^32)** 사용 → 부동소수점 없이 비슷한 압축률.

**장점**: 특허 우회 (수학적으로 동치이나 구현 차이로 별도 특허). 정수 연산만 → 임베디드에서 유리.

**활용**: LZMA (7z), bzip2 변형

### 8.3 ANS (Asymmetric Numeral Systems) — **현대의 winner**

**원리** (Jarek Duda, 2009): 메시지 → 단일 자연수 `x`. 각 심볼이 `x` 의 비트 패턴을 결정.

```
인코딩: 심볼 s 추가 → x' = (x / freq[s]) * total + cumFreq[s] + (x mod freq[s])
디코딩: 역연산
```

**rANS / tANS 변형**:
- **rANS** (range): 큰 알파벳 + 정밀한 확률. zstd 가 사용
- **tANS** (table): 작은 알파벳 + 빠름 (lookup table). FSE (Finite State Entropy) = tANS, zstd dictionary 모드에서 사용

**장점**:
- **Arithmetic Coding 의 압축률** + **Huffman 의 속도** (CPU 측정 시 Huffman 의 1.5× 정도, AC 의 2~3×)
- **로열티 프리** (Duda 가 의도적으로 특허 출원 안 함)
- 병렬화 우수 (multi-stream interleave)

**단점**:
- 디코딩이 인코딩의 **역순** → 메시지를 뒤에서부터 디코드 (스트리밍 어색, 작은 청크로 해결)
- Huffman 보다 구현 복잡

**활용**:
- **zstd** (Facebook 2015) — gzip 대체 표준
- **AV1, JPEG XL** — 미디어 코덱 차세대 표준
- **Apple LZFSE** — macOS/iOS 압축
- **Oodle Kraken** — 게임 (PS5 디스크 압축 HW)

**Python 예제 (zstandard, AV1 분석)**:
```python
import zstandard as zstd

# zstd 압축 (Huffman + FSE/tANS + LZ77 결합)
data = open("text.json", "rb").read()
cctx = zstd.ZstdCompressor(level=22)  # 1~22, 22 가 최강 (느림)
compressed = cctx.compress(data)
print(f"Original: {len(data)}, zstd L22: {len(compressed)}, ratio: {len(data)/len(compressed):.2f}×")

# zstd dictionary 모드 (작은 파일 다수 압축 시 효과적)
samples = [open(f"sample_{i}.json", "rb").read() for i in range(100)]
dict_data = zstd.ZstdCompressionDict.train_from_buffer(samples, dict_size=16384)
cctx_dict = zstd.ZstdCompressor(dict_data=dict_data)
small = cctx_dict.compress(samples[0])  # 작은 파일에서 dict 없을 때보다 훨씬 작음

# ANS 의 entropy 한계 측정
import math
from collections import Counter
def shannon_entropy(data):
    counts = Counter(data)
    total = sum(counts.values())
    return -sum((c/total) * math.log2(c/total) for c in counts.values())

bits_per_byte = shannon_entropy(data)
theoretical_min = (len(data) * bits_per_byte) / 8
print(f"Theoretical min: {theoretical_min:.0f} bytes, zstd: {len(compressed)} bytes")
print(f"zstd is {len(compressed)/theoretical_min:.2f}× of Shannon limit")
```

**관련 알고리즘**: [Huffman](compression.md), [Arithmetic Coding](compression.md#arithmetic-coding), [LZ77](compression.md#2-lz77-lempel-ziv-1977-슬라이딩-윈도우), [h264](#h264) (CABAC 사용), [webp-avif-heic](#webp-avif-heic) (AV1/AVIF 가 ANS 사용)

---
