# 이미지 처리 알고리즘 (Image Processing Algorithms)

컴퓨터 비전 기초 8 알고리즘. OpenCV / PIL / scikit-image / Halide 의 핵심.

**원전·표준 참고**:
- Rafael C. Gonzalez, Richard E. Woods — *Digital Image Processing*, 4th ed. (2017)
- Richard Szeliski — *Computer Vision: Algorithms and Applications*, 2nd ed. (2022)
- John Canny — "A Computational Approach to Edge Detection" (PAMI 1986)
- David Lowe — "Distinctive Image Features from Scale-Invariant Keypoints" (IJCV 2004) — SIFT
- Bruce Lucas, Takeo Kanade — Lucas-Kanade Optical Flow (IJCAI 1981)
- OpenCV Documentation

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [convolution-kernel](#convolution-kernel) | Convolution / Kernel Filtering | 합성곱 / 커널 필터링 | 중간 |
| [edge-detection](#edge-detection) | Edge Detection (Sobel / Canny / Laplacian) | 에지 검출 | 중간 |
| [hough-transform](#hough-transform) | Hough Transform | 허프 변환 | 높음 |
| [morphology](#morphology) | Morphological Operations | 형태학적 연산 | 중간 |
| [histogram-equalization](#histogram-equalization) | Histogram & Equalization | 히스토그램 평활화 (CLAHE) | 낮음 |
| [image-segmentation](#image-segmentation) | Image Segmentation | 이미지 분할 (Watershed / GrabCut) | 높음 |
| [feature-detection](#feature-detection) | Feature Detection (Harris / SIFT / ORB) | 특징점 검출 | 높음 |
| [optical-flow](#optical-flow) | Optical Flow (Lucas-Kanade / Farneback) | 광학 흐름 | 높음 |

**카테고리 분류**:

| ID | 카테고리 | 용도 |
|----|---------|------|
| convolution-kernel | Filter | blur / sharpen / edge |
| edge-detection | Edge | edge map |
| hough-transform | Detection | line / circle |
| morphology | Binary | noise / shape |
| histogram-equalization | Enhancement | contrast |
| image-segmentation | Segmentation | foreground extract |
| feature-detection | Feature | keypoint matching |
| optical-flow | Motion | pixel motion |

**관련 카탈로그**:
- [ml.md](ml.md) — K-Means (segmentation), Transformer (CV)
- [geometry.md](geometry.md) — CCW, Convex Hull
- [`../patterns/ai-llm.md`](../patterns/ai-llm.md) — Vision-LLM (CLIP/SAM)

---

<a id="convolution-kernel"></a>
## 1. Convolution / Kernel Filtering (합성곱 / 커널 필터링)

**개념**: 이미지의 각 픽셀 주변 영역에 작은 행렬(커널)을 곱해 합산한 값으로 새 픽셀을 생성하는 연산. 거의 모든 이미지 처리(블러·샤픈·에지·엠보싱)의 기본 원시 연산.

**알고리즘** (2D Convolution 수식):

```
(I * K)(x, y) = Σ_{i=-a}^{a} Σ_{j=-b}^{b} I(x - i, y - j) · K(i, j)

여기서:
  I  : 입력 이미지 (H × W)
  K  : 커널 (k × k, k = 2a+1 = 2b+1)
  *  : 합성곱 연산자
```

대표 커널:

```
Gaussian (σ=1, 3×3, 정규화 전):
  1 2 1
  2 4 2    /  16
  1 2 1

Sobel X (수평 에지):
 -1 0 1
 -2 0 2
 -1 0 1

Laplacian:
  0  1  0
  1 -4  1
  0  1  0

Sharpening:
  0 -1  0
 -1  5 -1
  0 -1  0
```

**Separable Kernel 최적화**: 2D 커널 K가 두 1D 커널 외적으로 분해 가능하면 (K = v · u^T) 2D O(k²) → 1D 2회 O(2k)로 가속. Gaussian, Box filter, Sobel 모두 separable.

```
Gaussian 1D (σ=1):  [1, 2, 1] / 4
2D Gaussian = (Gaussian 1D)^T × (Gaussian 1D)
```

**시간 복잡도**:
- 일반 2D: O(H · W · k²)
- Separable: O(H · W · 2k)
- FFT 기반 (큰 커널): O(H · W · log(H · W))

**공간 복잡도**: O(H · W) - 출력 이미지

**특징**:
- 선형 시불변(LTI) 필터
- 경계(padding) 처리 필요: zero / reflect / replicate
- Cross-correlation과 부호만 다름 (대칭 커널이면 동일)

**장점**:
- 모든 선형 필터 일반화
- GPU/SIMD 병렬화 용이
- Separable / FFT 가속 가능

**단점**:
- 큰 커널 비용 ↑ → FFT 전환점 통상 k ≥ 15
- 비선형 효과(median filter)는 합성곱 아님

**활용 예시**:
- Gaussian Blur (노이즈 제거, 안티앨리어싱)
- Sobel / Prewitt (에지 검출 사전 단계)
- 이미지 샤프닝
- CNN의 합성곱 레이어

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Python (OpenCV / numpy) 예제**:
```python
import cv2
import numpy as np

img = cv2.imread("input.jpg", cv2.IMREAD_GRAYSCALE)

# 1. Gaussian Blur (separable)
blurred = cv2.GaussianBlur(img, ksize=(5, 5), sigmaX=1.0)

# 2. 커스텀 커널 (sharpening)
kernel_sharpen = np.array([[ 0, -1,  0],
                           [-1,  5, -1],
                           [ 0, -1,  0]], dtype=np.float32)
sharpened = cv2.filter2D(img, ddepth=-1, kernel=kernel_sharpen)

# 3. Separable 최적화 직접 구현
def separable_gaussian(img, sigma=1.0):
    # 1D Gaussian kernel 생성
    k = cv2.getGaussianKernel(ksize=5, sigma=sigma)  # 5×1
    # 행 방향 1D conv → 열 방향 1D conv
    tmp = cv2.filter2D(img, -1, k)         # vertical
    out = cv2.filter2D(tmp, -1, k.T)       # horizontal
    return out

result = separable_gaussian(img, sigma=1.0)

# 4. numpy 수동 구현 (학습용, 실전은 cv2 사용)
def conv2d_manual(img, kernel):
    H, W = img.shape
    kh, kw = kernel.shape
    pad_h, pad_w = kh // 2, kw // 2
    padded = np.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode="reflect")
    out = np.zeros_like(img, dtype=np.float32)
    for y in range(H):
        for x in range(W):
            region = padded[y:y+kh, x:x+kw]
            out[y, x] = np.sum(region * kernel)
    return np.clip(out, 0, 255).astype(np.uint8)
```

**관련 알고리즘**: Edge Detection (Sobel/Laplacian), Bilateral Filter (비선형), CNN

---

<a id="edge-detection"></a>
## 2. Edge Detection (Sobel / Canny / Laplacian)

**개념**: 이미지에서 픽셀 값이 급격히 변하는 경계(에지)를 찾는 알고리즘. 객체 윤곽 추출의 첫 단계.

**알고리즘**:

### 2.1 Sobel (Gradient Magnitude)

1차 미분 근사. 수평·수직 gradient를 계산해 크기와 방향 추출.

```
Gx = I * Kx,   Gy = I * Ky
|G| = sqrt(Gx² + Gy²)
θ   = atan2(Gy, Gx)

Kx = [-1 0 1; -2 0 2; -1 0 1]
Ky = [-1 -2 -1; 0 0 0; 1 2 1]
```

### 2.2 Laplacian (2차 미분, Zero-Crossing)

이미지의 2차 미분 → 에지에서 부호 변화(zero-crossing) 발생.

```
∇²I = ∂²I/∂x² + ∂²I/∂y²

3×3 커널:
  0  1  0
  1 -4  1
  0  1  0
```

LoG (Laplacian of Gaussian): 노이즈 민감도를 줄이기 위해 Gaussian smoothing 선행.

### 2.3 Canny — 4 단계 (PAMI 1986)

가장 정교한 에지 검출. 다음 4단계로 구성:

```
Stage 1. Gaussian Smoothing
    노이즈 제거 (σ ≈ 1.4 통상)

Stage 2. Gradient Computation (Sobel)
    |G|, θ 계산. θ를 0°/45°/90°/135° 4방향으로 양자화

Stage 3. Non-Maximum Suppression (NMS)
    각 픽셀에서 gradient 방향 양쪽 두 픽셀과 |G| 비교
    자신이 최대가 아니면 0 으로 억제 → 1픽셀 두께 에지

Stage 4. Hysteresis Thresholding
    T_high, T_low 두 임계값 사용
    |G| > T_high            → strong edge (확정)
    T_low < |G| <= T_high   → weak edge
    weak edge가 strong edge에 연결돼 있으면 채택, 아니면 제거
```

**시간 복잡도**: O(H · W) - 모든 단계 픽셀당 상수 시간

**공간 복잡도**: O(H · W)

**특징**:
- Sobel: 빠름, 두꺼운 에지
- Laplacian: zero-crossing, 노이즈 민감
- Canny: 1픽셀 두께, 연결성 보장, 가장 강건

**장점**:
- Canny: 위치 정확성, 단일 응답, 좋은 검출률 (Canny 3 criteria)
- Sobel: GPU 친화, 실시간 가능

**단점**:
- 임계값 튜닝 필요 (Canny T_high / T_low)
- 노이즈에 민감 (Gaussian 선행 필수)
- 텍스처가 강한 영역에서 false edge

**활용 예시**:
- 객체 윤곽 추출
- 차선 검출 (자율주행 전처리)
- 의료 영상 (장기 경계)
- OCR 문자 분리

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Python (OpenCV) 예제**:
```python
import cv2
import numpy as np

img = cv2.imread("input.jpg", cv2.IMREAD_GRAYSCALE)

# 1. Sobel — gradient magnitude
gx = cv2.Sobel(img, cv2.CV_64F, dx=1, dy=0, ksize=3)
gy = cv2.Sobel(img, cv2.CV_64F, dx=0, dy=1, ksize=3)
magnitude = np.sqrt(gx**2 + gy**2)
sobel_edge = np.clip(magnitude, 0, 255).astype(np.uint8)

# 2. Laplacian
lap = cv2.Laplacian(img, cv2.CV_64F, ksize=3)
laplacian_edge = np.uint8(np.absolute(lap))

# 3. Canny — 4 stage
#    cv2.Canny 내부에서 Gaussian → Sobel → NMS → Hysteresis 수행
canny_edge = cv2.Canny(img, threshold1=50, threshold2=150, apertureSize=3, L2gradient=True)

# 4. Canny 임계값 자동 추정 (median 기반 휴리스틱)
def auto_canny(image, sigma=0.33):
    v = np.median(image)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    return cv2.Canny(image, lower, upper)

auto_edge = auto_canny(cv2.GaussianBlur(img, (5, 5), 1.4))
```

**관련 알고리즘**: Hough Transform (에지 후속), Convolution (Sobel 기반)

---

<a id="hough-transform"></a>
## 3. Hough Transform (허프 변환)

**개념**: 에지 픽셀들을 parameter space로 변환해 voting을 통해 직선·원 등 파라메트릭 도형을 검출. Paul Hough가 1962년에 특허로 제안.

**알고리즘**:

### 3.1 Hough Line Transform

직선의 normal form 표현:

```
x · cos(θ) + y · sin(θ) = ρ

(x, y)  : 에지 픽셀
(ρ, θ)  : 직선 파라미터 (원점에서 직선까지의 수직거리, 수직선 각도)
```

각 에지 픽셀이 가능한 모든 (ρ, θ) 직선에 1표씩 투표 → accumulator 배열에서 peak가 실제 직선.

```
1. Edge map 생성 (Canny)
2. Accumulator A[ρ][θ] = 0 초기화
3. for each edge pixel (x, y):
       for θ in [0, π):
           ρ = round(x·cos θ + y·sin θ)
           A[ρ][θ] += 1
4. Threshold 이상 A[ρ][θ] peak를 직선으로 추출
```

### 3.2 Hough Circle Transform

원: `(x - a)² + (y - b)² = r²` → 3D accumulator A[a][b][r].
각 에지 픽셀에서 가능한 모든 (a, b, r) 원에 투표. cv2는 gradient 방향을 이용해 차원 축소 (Hough Gradient method).

**Probabilistic Hough**: 모든 에지 픽셀이 아닌 무작위 표본만 투표 → 속도 개선.

**시간 복잡도**:
- Standard Line: O(N · Θ), N: 에지 픽셀 수, Θ: θ 양자화 수
- Circle: O(N · R · Θ), R: 반경 범위
- Probabilistic Line: O(N · Θ / k), k: 표본 비율

**공간 복잡도**:
- Line: O(ρ_max · Θ)
- Circle: O(W · H · R) — 메모리 ↑

**특징**:
- 노이즈/부분 차단(occlusion)에 강건
- 양자화 해상도가 정확도 결정
- 곡선은 일반화 가능 (Generalized Hough)

**장점**:
- 부분적으로 끊긴 도형도 검출
- 노이즈에 강함
- 명확한 수학적 기반

**단점**:
- accumulator 메모리 부담 (특히 원/타원)
- 양자화 오차
- 여러 도형이 겹치면 peak 분리 어려움

**활용 예시**:
- 차선 검출 (자율주행)
- 동전·홍채 검출 (원)
- 문서 기울기 보정 (직선)
- 산업용 부품 정렬

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Python (OpenCV) 예제**:
```python
import cv2
import numpy as np

img = cv2.imread("input.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150)

# 1. Standard Hough Line — 모든 (ρ, θ) 반환
lines = cv2.HoughLines(edges, rho=1, theta=np.pi/180, threshold=200)
if lines is not None:
    for rho, theta in lines[:, 0]:
        a, b = np.cos(theta), np.sin(theta)
        x0, y0 = a*rho, b*rho
        x1, y1 = int(x0 + 1000*(-b)), int(y0 + 1000*(a))
        x2, y2 = int(x0 - 1000*(-b)), int(y0 - 1000*(a))
        cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

# 2. Probabilistic Hough Line — 선분 끝점 직접 반환 (실전 추천)
linesP = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180,
                         threshold=80, minLineLength=50, maxLineGap=10)
if linesP is not None:
    for x1, y1, x2, y2 in linesP[:, 0]:
        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

# 3. Hough Circle — gradient method
circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                           param1=100, param2=30, minRadius=10, maxRadius=100)
if circles is not None:
    for cx, cy, r in np.round(circles[0]).astype(int):
        cv2.circle(img, (cx, cy), r, (255, 0, 0), 2)
```

**관련 알고리즘**: Canny (선행 단계), RANSAC (대체 도형 적합)

---

<a id="morphology"></a>
## 4. Morphological Operations (형태학적 연산)

**개념**: 구조적 요소(structuring element, SE)를 사용해 이진/그레이스케일 이미지의 형태를 변형하는 연산. 노이즈 제거·연결성 분석·모양 단순화의 기본 도구.

**알고리즘** (이진 이미지 기준, SE = B):

```
Erosion (침식):    (I ⊖ B)(x) = { x | B_x ⊆ I }
                   픽셀 주변 SE 영역이 모두 foreground일 때만 유지
                   → 작은 객체/돌출부 제거

Dilation (팽창):   (I ⊕ B)(x) = { x | B_x ∩ I ≠ ∅ }
                   SE 영역 중 하나라도 foreground이면 채움
                   → 작은 구멍 메움, 객체 확장

Opening (열림):    I ∘ B = (I ⊖ B) ⊕ B
                   Erosion 후 Dilation
                   → 작은 noise 제거, 원래 크기 보존

Closing (닫힘):    I • B = (I ⊕ B) ⊖ B
                   Dilation 후 Erosion
                   → 내부 구멍 메움, 끊긴 경계 연결

Gradient:          (I ⊕ B) − (I ⊖ B)        → 경계 추출
Top-Hat:           I − (I ∘ B)                → 밝은 작은 객체 부각
Black-Hat:         (I • B) − I                → 어두운 작은 객체 부각
```

**그레이스케일 확장**: erosion = local min, dilation = local max로 일반화.

**SE 종류**: rect, ellipse, cross. 크기와 모양이 효과 결정.

**시간 복잡도**:
- 기본: O(H · W · |B|), |B|: SE 픽셀 수
- van Herk-Gil-Werman (rect SE): O(H · W) - SE 크기 무관

**공간 복잡도**: O(H · W)

**특징**:
- 이진/그레이 모두 지원
- 비선형 연산 (합성곱 아님)
- Duality: erosion ↔ dilation (보색 관점)

**장점**:
- 노이즈 제거에 효과적
- 모양 보존하며 정제
- 빠른 구현 (rect SE)

**단점**:
- 큰 객체 영향
- SE 크기/모양 튜닝 필요
- 회전 비변환 (SE에 의존)

**활용 예시**:
- 텍스트 OCR 전처리 (글자 끊김 메움)
- 의료 영상 분할 후 정제
- 지문 인식 (능선 추출)
- 위성 사진 (도로 추출)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Python (OpenCV) 예제**:
```python
import cv2
import numpy as np

# 이진화 (Otsu)
img = cv2.imread("input.jpg", cv2.IMREAD_GRAYSCALE)
_, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Structuring Element
se_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
se_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
se_cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))

# 4 기본 연산
eroded   = cv2.erode(binary, se_rect, iterations=1)
dilated  = cv2.dilate(binary, se_rect, iterations=1)
opened   = cv2.morphologyEx(binary, cv2.MORPH_OPEN,  se_rect)  # noise 제거
closed   = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, se_rect)  # 구멍 메움

# 파생 연산
gradient = cv2.morphologyEx(binary, cv2.MORPH_GRADIENT, se_rect)
tophat   = cv2.morphologyEx(img,    cv2.MORPH_TOPHAT,   se_rect)
blackhat = cv2.morphologyEx(img,    cv2.MORPH_BLACKHAT, se_rect)

# 실전: 텍스트 분리 (수평 SE로 가로 줄 강조)
horizontal_se = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_se)
```

**관련 알고리즘**: Connected Component Labeling, Distance Transform, Watershed

---

<a id="histogram-equalization"></a>
## 5. Histogram & Equalization (히스토그램 평활화)

**개념**: 이미지 픽셀 값의 분포(histogram)를 조작해 대비(contrast)를 개선. 어두운 영역의 디테일을 끌어올리거나 과노출을 보정.

**알고리즘**:

### 5.1 Histogram

```
h[i] = (값이 i인 픽셀의 개수)     for i in [0, 255]
p[i] = h[i] / (H · W)             (확률 분포)
```

### 5.2 Global Histogram Equalization

CDF(누적 분포 함수)를 사용해 픽셀 값을 재매핑 → 평탄한 분포로 만듦.

```
1. histogram h[i] 계산
2. CDF[i] = Σ_{j=0..i} h[j]
3. 정규화: CDF_norm[i] = (CDF[i] - CDF_min) / (H·W - CDF_min)
4. 매핑: I'(x, y) = round(255 · CDF_norm[I(x, y)])
```

### 5.3 CLAHE (Contrast Limited Adaptive Histogram Equalization)

전역 평활화의 문제(노이즈 증폭, 지역 디테일 손실)를 해결:

```
1. 이미지를 tile (예: 8×8)로 분할
2. 각 tile 마다 local histogram 평활화
3. Clip Limit β: 히스토그램 bin이 β를 넘으면 잘라내고 균등 분배
   → 동일 값 영역(평탄 영역)의 노이즈 증폭 억제
4. tile 경계에서 bilinear interpolation으로 매끄럽게 결합
```

**시간 복잡도**:
- Global: O(H · W + 256)
- CLAHE: O(H · W) - tile 단위 병렬화 가능

**공간 복잡도**: O(256) 글로벌, O(N_tiles · 256) CLAHE

**특징**:
- 컬러 이미지: RGB 직접 적용 X (색 왜곡) → YCrCb / HSV의 Y/V 채널에만 적용
- CLAHE 클립 한도가 키 파라미터 (β = 2~4 통상)

**장점**:
- 빠르고 자동
- 어두운/안개 낀 이미지 개선
- 의료/위성 사진 강화

**단점**:
- Global EQ: 노이즈 증폭, 부자연
- 정보 손실 가능 (양자화)
- 컬러 채널 직접 평활화 시 색 왜곡

**활용 예시**:
- 의료 X-ray / CT
- 야간 / 저조도 사진
- 위성 영상 전처리
- OCR 가독성 향상

**난이도**: 낮음 | **사용 빈도**: ★★★★☆

**Python (OpenCV / numpy) 예제**:
```python
import cv2
import numpy as np
import matplotlib.pyplot as plt

img = cv2.imread("input.jpg", cv2.IMREAD_GRAYSCALE)

# 1. Histogram 계산
hist = cv2.calcHist([img], [0], None, [256], [0, 256])
# numpy 직접: np.histogram(img.ravel(), bins=256, range=[0, 256])

# 2. Global Histogram Equalization
equ = cv2.equalizeHist(img)

# 3. CLAHE
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
clahe_img = clahe.apply(img)

# 4. 수동 구현 (학습용)
def equalize_manual(img):
    hist, _ = np.histogram(img.flatten(), 256, [0, 256])
    cdf = hist.cumsum()
    cdf_m = np.ma.masked_equal(cdf, 0)  # 0 제외
    cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
    cdf_final = np.ma.filled(cdf_m, 0).astype("uint8")
    return cdf_final[img]

manual = equalize_manual(img)

# 5. 컬러 이미지 - YCrCb로 변환 후 Y 채널만 평활화
color = cv2.imread("input.jpg")
ycrcb = cv2.cvtColor(color, cv2.COLOR_BGR2YCrCb)
ycrcb[:, :, 0] = clahe.apply(ycrcb[:, :, 0])
color_eq = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
```

**관련 알고리즘**: Gamma Correction, Histogram Matching, Adaptive Thresholding

---

<a id="image-segmentation"></a>
## 6. Image Segmentation (이미지 분할)

**개념**: 이미지를 의미 있는 영역들로 분할. 객체 추출, 의료 영상 분석, 배경 제거의 핵심.

**알고리즘**:

### 6.1 Watershed (분수령)

이미지를 지형으로 간주 — gray value = 고도. "물을 부으면" 골짜기에서 시작해 능선에서 만나며 영역 분할.

```
1. Gradient magnitude로 변환 (에지가 능선)
2. Marker (seed) 지정: foreground / background / 미정 영역
3. Priority queue로 픽셀 침수 시뮬레이션
4. 다른 영역이 만나는 곳이 경계
```

Over-segmentation 위험 → marker 기반 watershed 필수.

### 6.2 Region Growing

```
1. Seed 픽셀 선택
2. seed의 이웃 픽셀 중 유사도(|I(p) - mean(region)| < T)가 임계값 이내인 것을 영역에 편입
3. 더 이상 추가할 픽셀 없을 때까지 반복
```

### 6.3 K-Means Color Segmentation (cross-link: ml.md K-Means)

```
1. 픽셀을 (R, G, B) 또는 (L, a, b) 벡터로 변환
2. K-Means로 K개 클러스터 (ml.md §1 참조)
3. 각 픽셀에 클러스터 ID 할당 → K개 영역
```

색상 양자화·간단 분할에 적합. 공간 정보(위치)는 미반영 — (x, y, R, G, B) 5D로 확장 가능.

### 6.4 GrabCut (Graph Cut 기반)

사용자가 ROI 박스 지정 → GMM(Gaussian Mixture Model)로 foreground/background 모델링 → min-cut으로 분할.

```
1. ROI 박스 입력 → 박스 안 = probable FG, 밖 = sure BG
2. FG/BG에 각각 GMM (K=5 통상) fit
3. Graph 구성: 픽셀=node, edge weight = GMM likelihood + smoothness term
4. min-cut / max-flow로 분할
5. 사용자가 brush로 수정 → iterative refinement
```

**시간 복잡도**:
- Watershed: O(H · W · log(H · W)) - priority queue
- Region Growing: O(H · W) ~ O(H · W · log(H · W))
- K-Means: O(n · k · i) (ml.md 참조)
- GrabCut: O(H · W · K · iter) - GMM iter

**공간 복잡도**: O(H · W) ~ O(H · W · K)

**특징**:
- Watershed: 정밀하나 over-segmentation 주의
- Region Growing: 직관적, seed 의존
- K-Means: 비지도, 색상 기준
- GrabCut: 사용자 입력 필요, 자연스러운 객체 분할

**장점**:
- 객체별 분할 자동화
- 의미 정보 추출 가능
- 다양한 접근법 선택 가능

**단점**:
- Watershed: noise 민감 → marker 필수
- 경계가 모호한 객체에서 정확도 ↓
- 딥러닝 기반(U-Net, SAM)이 현재 SOTA

**활용 예시**:
- 의료 영상 (장기·종양 분할)
- 배경 제거 (사진 편집)
- 자율주행 (도로/차량 분할)
- 위성 영상 (토지 분류)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Python (OpenCV) 예제**:
```python
import cv2
import numpy as np

img = cv2.imread("input.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 1. Watershed (marker-based)
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
kernel = np.ones((3, 3), np.uint8)
opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

sure_bg = cv2.dilate(opening, kernel, iterations=3)
dist = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
_, sure_fg = cv2.threshold(dist, 0.7 * dist.max(), 255, 0)
sure_fg = np.uint8(sure_fg)
unknown = cv2.subtract(sure_bg, sure_fg)

_, markers = cv2.connectedComponents(sure_fg)
markers = markers + 1
markers[unknown == 255] = 0
markers = cv2.watershed(img, markers)
img[markers == -1] = [0, 0, 255]  # 경계 빨강

# 2. K-Means color segmentation
pixels = img.reshape(-1, 3).astype(np.float32)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
_, labels, centers = cv2.kmeans(pixels, K=4, bestLabels=None,
                                criteria=criteria, attempts=10,
                                flags=cv2.KMEANS_PP_CENTERS)
centers = np.uint8(centers)
kmeans_seg = centers[labels.flatten()].reshape(img.shape)

# 3. GrabCut
mask = np.zeros(img.shape[:2], np.uint8)
bgd_model = np.zeros((1, 65), np.float64)
fgd_model = np.zeros((1, 65), np.float64)
rect = (50, 50, 400, 400)  # ROI 박스
cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")
grabcut_result = img * mask2[:, :, np.newaxis]
```

**관련 알고리즘**: K-Means (ml.md), Connected Components, Morphology, U-Net (딥러닝)

---

<a id="feature-detection"></a>
## 7. Feature Detection (Harris / SIFT / ORB)

**개념**: 이미지에서 다른 이미지와 매칭 가능한 "특징점(keypoint)"과 그것을 표현하는 "기술자(descriptor)"를 추출. 파노라마 스티칭·SLAM·3D 복원의 핵심.

**알고리즘**:

### 7.1 Harris Corner Detection (1988)

코너 = 두 방향 모두 강한 gradient 변화.

```
1. 윈도우 W에서 자기 상관 행렬 M 계산:
   M = Σ_W [ Ix²    Ix·Iy ]
            [ Ix·Iy  Iy²  ]

2. 코너 응답 R = det(M) - k · trace(M)²        (k ≈ 0.04)
   - R > threshold → corner
   - R < 0         → edge
   - |R| 작음      → flat

3. Non-Maximum Suppression
```

방향 정보 없음, scale 비변환.

### 7.2 SIFT (Scale-Invariant Feature Transform, Lowe 2004)

스케일·회전 모두 변환에 강건.

```
Stage 1. Scale-space Extrema
    DoG (Difference of Gaussians) 피라미드 구성
    3D (x, y, σ) 공간에서 local extrema 탐색 → 키포인트 후보

Stage 2. Keypoint Localization
    Taylor 전개로 부픽셀 위치 정밀화
    낮은 contrast / 에지 응답 키포인트 제거

Stage 3. Orientation Assignment
    키포인트 주변 gradient 방향 히스토그램(36 bin)
    peak를 dominant orientation으로 → 회전 비변환

Stage 4. Descriptor (128-D)
    16×16 윈도우를 4×4 셀로 나누고 각 셀에서 8-bin gradient histogram
    4 × 4 × 8 = 128 차원 벡터, L2 정규화
```

특허 문제로 OpenCV main에서 한때 제외 → 2020년 특허 만료 후 복귀.

### 7.3 ORB (Oriented FAST and Rotated BRIEF, 2011)

SIFT 대안. 빠르고 무료.

```
1. FAST corner detector → 키포인트
2. Harris 응답으로 상위 N개 선택
3. Intensity centroid로 방향 부여
4. BRIEF descriptor (256 bit binary)
5. 키포인트 방향에 맞춰 BRIEF 패턴 회전
```

이진 descriptor → Hamming distance로 빠른 매칭.

**시간 복잡도**:
- Harris: O(H · W)
- SIFT: O(H · W · k · log(H · W)), k: octave 수 — 100~1000ms (HD)
- ORB: O(H · W) — 10ms 미만 (HD), 약 10~100배 빠름

**공간 복잡도**: SIFT 128 · 4 byte/keypoint, ORB 32 byte/keypoint

**특징**:
- Harris: corner만, scale 비변환 없음
- SIFT: 강건, 무겁고 (2020년 이전) 특허 제약
- ORB: 빠르고 자유, scale 약함 (FAST 기반)

**장점**:
- SIFT: 매칭 정확도 최고 수준
- ORB: 실시간 가능 (SLAM, AR)
- Harris: 단순, 빠름

**단점**:
- SIFT: 무거움, 메모리
- ORB: 큰 scale 변화에 약함
- Harris: 매칭 불가 (descriptor 없음)

**활용 예시**:
- 파노라마 스티칭
- Visual SLAM (ORB-SLAM)
- 객체 인식
- AR 마커리스 추적
- 이미지 검색 (BoVW)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Python (OpenCV) 예제**:
```python
import cv2
import numpy as np

img1 = cv2.imread("scene.jpg", cv2.IMREAD_GRAYSCALE)
img2 = cv2.imread("object.jpg", cv2.IMREAD_GRAYSCALE)

# 1. Harris Corner
gray = np.float32(img1)
harris = cv2.cornerHarris(gray, blockSize=2, ksize=3, k=0.04)
harris = cv2.dilate(harris, None)
corners = np.zeros_like(img1)
corners[harris > 0.01 * harris.max()] = 255

# 2. SIFT
sift = cv2.SIFT_create(nfeatures=500)
kp1, des1 = sift.detectAndCompute(img1, None)
kp2, des2 = sift.detectAndCompute(img2, None)

# FLANN matcher (SIFT)
FLANN_INDEX_KDTREE = 1
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
search_params = dict(checks=50)
flann = cv2.FlannBasedMatcher(index_params, search_params)
matches = flann.knnMatch(des1, des2, k=2)

# Lowe's ratio test
good_matches = []
for m, n in matches:
    if m.distance < 0.75 * n.distance:
        good_matches.append(m)

# 3. ORB
orb = cv2.ORB_create(nfeatures=1000)
kp1o, des1o = orb.detectAndCompute(img1, None)
kp2o, des2o = orb.detectAndCompute(img2, None)

# Hamming matcher (binary descriptor)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches_orb = sorted(bf.match(des1o, des2o), key=lambda m: m.distance)

# 매칭 결과 시각화
result = cv2.drawMatches(img1, kp1o, img2, kp2o, matches_orb[:30], None,
                        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

# 4. Homography 추정 (응용 — 객체 위치 찾기)
if len(good_matches) > 10:
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
```

**관련 알고리즘**: RANSAC (outlier 제거), Bag of Visual Words, Optical Flow

---

<a id="optical-flow"></a>
## 8. Optical Flow (Lucas-Kanade / Farneback)

**개념**: 연속된 두 프레임 사이 픽셀의 움직임 벡터(motion field)를 추정. 영상 추적·동작 인식·비디오 압축의 핵심.

**기본 가정** (밝기 항상성, brightness constancy):

```
I(x, y, t) = I(x + dx, y + dy, t + dt)

Taylor 전개:
  Ix · u + Iy · v + It = 0      (광학 흐름 방정식)

(u, v) : 광학 흐름 벡터
Ix, Iy, It : 공간/시간 편미분
```

방정식 1개 / 미지수 2개 → 추가 제약 필요 (aperture problem).

### 8.1 Lucas-Kanade (LK, 1981) — Sparse

윈도우 내 모든 픽셀이 동일 (u, v)를 갖는다고 가정 → 최소제곱:

```
[ ΣIx²   ΣIxIy ] [u]   [-ΣIxIt]
[ ΣIxIy  ΣIy²  ] [v] = [-ΣIyIt]

A^T A · v = A^T b   →   v = (A^T A)^{-1} A^T b
```

문제: 큰 움직임 처리 못 함 → **Pyramidal LK**: 이미지 피라미드를 만들고 거친 레벨부터 추정.

특징점(코너 등)에서만 계산 → **sparse** flow.

### 8.2 Farneback (2003) — Dense

모든 픽셀의 flow 계산. 각 픽셀 주변 영역을 2차 다항식으로 근사:

```
I(x) ≈ x^T A x + b^T x + c

두 프레임의 다항식 계수 변화에서 displacement field 추출
```

피라미드 + iterative refinement.

**현대 대안**: 딥러닝 기반 (RAFT, FlowNet) — 정확도 ↑, 속도 ↑.

**시간 복잡도**:
- LK: O(N · k²), N: 특징점 수, k: 윈도우 크기
- Farneback: O(H · W · k²)

**공간 복잡도**:
- LK: O(N)
- Farneback: O(H · W) - dense field

**특징**:
- LK: sparse, 특징점 추적용
- Farneback: dense, 모든 픽셀
- 두 가정 모두 큰/빠른 움직임에서 깨짐

**장점**:
- LK: 빠름, 실시간 가능
- Farneback: dense, 모든 픽셀
- 단순한 수학적 기반

**단점**:
- 밝기 변화에 민감
- aperture problem (선만 보이면 평행 성분 미정)
- 큰 변위·회전에 약함 → 피라미드 필수

**활용 예시**:
- 비디오 객체 추적
- 동작 인식 (스포츠 분석)
- 비디오 압축 (MPEG motion estimation)
- 자율주행 (ego-motion)
- 안정화 (video stabilization)

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Python (OpenCV) 예제**:
```python
import cv2
import numpy as np

cap = cv2.VideoCapture("video.mp4")
ret, frame1 = cap.read()
prev_gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

# ---------- 1. Lucas-Kanade (Sparse) ----------
# Shi-Tomasi corner를 추적 특징점으로 사용
feature_params = dict(maxCorners=100, qualityLevel=0.3,
                      minDistance=7, blockSize=7)
lk_params = dict(winSize=(15, 15), maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

p0 = cv2.goodFeaturesToTrack(prev_gray, mask=None, **feature_params)
mask = np.zeros_like(frame1)

while True:
    ret, frame2 = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Pyramidal LK
    p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, gray, p0, None, **lk_params)
    good_new = p1[st == 1]
    good_old = p0[st == 1]

    # 궤적 시각화
    for new, old in zip(good_new, good_old):
        a, b = new.ravel().astype(int)
        c, d = old.ravel().astype(int)
        cv2.line(mask, (a, b), (c, d), (0, 255, 0), 2)
        cv2.circle(frame2, (a, b), 5, (0, 0, 255), -1)

    output = cv2.add(frame2, mask)
    prev_gray = gray.copy()
    p0 = good_new.reshape(-1, 1, 2)

# ---------- 2. Farneback (Dense) ----------
cap2 = cv2.VideoCapture("video.mp4")
ret, frame1 = cap2.read()
prev = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
hsv = np.zeros_like(frame1)
hsv[..., 1] = 255

while True:
    ret, frame2 = cap2.read()
    if not ret:
        break
    next_gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    flow = cv2.calcOpticalFlowFarneback(
        prev, next_gray, None,
        pyr_scale=0.5, levels=3, winsize=15,
        iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
    )

    # flow → HSV 색상 (방향=hue, 크기=value)
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv[..., 0] = ang * 180 / np.pi / 2
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    prev = next_gray
```

**관련 알고리즘**: Feature Detection (LK는 corner 추적), Kalman Filter (motion smoothing), RAFT (딥러닝 dense flow)

---
