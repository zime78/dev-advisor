# 신호 처리 알고리즘 (Signal Processing Algorithms)

Digital Signal Processing 정평 있는 8 알고리즘. [`math.md#fast-fourier-transform`](math.md#fast-fourier-transform) (FFT) 의 응용 + 필터·추정·resampling 영역. 오디오/이미지/센서 신호 처리에 광범위하게 사용된다.

**원전·표준 참고**:
- Alan V. Oppenheim, Ronald W. Schafer — *Discrete-Time Signal Processing*, 3rd ed. (2009)
- Steven Smith — *The Scientist and Engineer's Guide to Digital Signal Processing* (free, 1999)
- Rudolf Kálmán — "A New Approach to Linear Filtering and Prediction Problems" (Transactions of ASME, 1960)
- Stephane Mallat — *A Wavelet Tour of Signal Processing*, 3rd ed. (2009)
- MATLAB Signal Processing Toolbox / Python scipy.signal

## 알고리즘 목차

| ID | 알고리즘 | 카테고리 | 용도 | 난이도 |
|----|---------|---------|------|--------|
| [fir-filter](#fir-filter) | FIR Filter | Filter | linear phase | 중간 |
| [iir-filter](#iir-filter) | IIR Filter | Filter | fewer taps | 중간 |
| [stft](#stft) | Short-Time Fourier Transform | Time-Freq | spectrogram | 중간 |
| [wavelet](#wavelet) | Wavelet Transform | Multi-res | denoising/compression | 높음 |
| [resampling](#resampling) | Up/Downsample | Rate Conv | sample rate | 중간 |
| [kalman-filter](#kalman-filter) | Kalman Filter | Estimation | sensor fusion | 높음 |
| [extended-kalman](#extended-kalman) | EKF / UKF | Estimation | nonlinear | 높음 |
| [autocorrelation](#autocorrelation) | Auto/Cross-correlation | Similarity | lag detection | 중간 |

**관련 카탈로그**:
- [math.md](math.md) — FFT 본체, Newton-Raphson, 수치 해석
- [ml.md](ml.md) — 신호 기반 feature extraction 후단 (분류/회귀)
- [`../patterns/domains/iot-edge.md`](../patterns/domains/iot-edge.md) — sensor data (Kalman 응용)

---

<a id="fir-filter"></a>
## 1. FIR Filter (Finite Impulse Response, 유한 임펄스 응답 필터)

**개념**: 입력의 유한 개 과거 샘플만 가중합하여 출력을 만드는 비순환 필터. 출력 `y[n] = Σ b_k · x[n−k]` (k=0..M).

**수식**:
```
y[n] = b_0·x[n] + b_1·x[n−1] + ... + b_M·x[n−M]
     = Σ_{k=0}^{M} b_k · x[n−k]
```
계수 `b_k`가 곧 임펄스 응답 `h[n]`이며, 길이가 `M+1` 로 유한. Z-변환 전달함수: `H(z) = Σ b_k z^{−k}`.

**목적**: 저역/고역/대역 통과·차단, 노이즈 제거, 안티앨리어싱

**시간 복잡도**: 샘플당 O(M) — naive convolution. FFT-based overlap-add 사용 시 블록당 O(N log N)

**공간 복잡도**: O(M) — 계수 + delay line

**특징**:
- 비순환 (non-recursive) — 피드백 없음
- 항상 BIBO 안정 (계수가 유한하므로)
- Linear phase 설계 가능 (대칭 계수 `b_k = b_{M−k}`)
- 설계법: Window method, Parks-McClellan (Remez exchange), Frequency sampling

**장점**:
- **무조건 안정** — pole 이 z=0 외에 없음
- **Linear phase** 가능 → 위상 왜곡 없이 그룹 지연 일정 (오디오/이미지 필수)
- 양자화 오차에 강건
- 고정소수점 구현 용이

**단점**:
- 동일 차단 sharpness 를 위해 IIR 보다 차수 큼 (10~100배)
- 지연(latency) 큼 — `M/2` 샘플 그룹 지연
- 실시간 응용에서 계산 비용 큼

**활용 예시**:
- 오디오 EQ, 디지털 라디오 (decimation 필터)
- ECG 베이스라인 제거, EMG 노이즈 제거
- 이미지 컨볼루션 (sharpen, blur, edge detection)
- 통신 시스템의 matched filter / pulse shaping (raised cosine)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Python (scipy) 코드**:
```python
import numpy as np
from scipy import signal

# 1) 저역통과 FIR 설계 (Hamming window, cutoff = 0.2 × Nyquist)
fs = 1000.0           # 샘플레이트 Hz
cutoff = 100.0        # 차단 주파수 Hz
numtaps = 51          # 필터 차수 + 1 (홀수 → 정확한 linear phase)
taps = signal.firwin(numtaps, cutoff, fs=fs, window='hamming')

# 2) 적용 - lfilter (causal, 그룹 지연 포함)
x = np.random.randn(2000)        # 입력 신호
y = signal.lfilter(taps, 1.0, x) # FIR: denominator = [1.0]

# 3) filtfilt - 제로 위상 (forward + backward) — 실시간 불가지만 오프라인 분석용
y_zero_phase = signal.filtfilt(taps, 1.0, x)

# 4) Parks-McClellan (equiripple) 설계
taps_pm = signal.remez(numtaps, [0, 90, 110, 500], [1, 0], fs=fs)
```

**Kotlin 코드**:
```kotlin
// 직접형 FIR (오디오 실시간 처리용 ring buffer)
class FirFilter(private val taps: DoubleArray) {
    private val delayLine = DoubleArray(taps.size)
    private var idx = 0

    /** 한 샘플 입력 → 한 샘플 출력 */
    fun process(x: Double): Double {
        delayLine[idx] = x
        var acc = 0.0
        var j = idx
        for (k in taps.indices) {
            acc += taps[k] * delayLine[j]
            j = if (j == 0) taps.size - 1 else j - 1
        }
        idx = (idx + 1) % taps.size
        return acc
    }
}

// Hamming window 기반 저역통과 계수 생성
fun firLowpassHamming(numTaps: Int, cutoffNorm: Double): DoubleArray {
    // cutoffNorm = fc / (fs/2), 0 < cutoffNorm < 1
    val taps = DoubleArray(numTaps)
    val m = (numTaps - 1) / 2.0
    for (n in 0 until numTaps) {
        val k = n - m
        val sinc = if (k == 0.0) cutoffNorm
                   else Math.sin(Math.PI * cutoffNorm * k) / (Math.PI * k)
        val w = 0.54 - 0.46 * Math.cos(2 * Math.PI * n / (numTaps - 1))
        taps[n] = sinc * w
    }
    return taps
}
```

**관련 알고리즘**: [IIR Filter](#iir-filter), [FFT](math.md#fast-fourier-transform) (overlap-add convolution), Windowing

---

<a id="iir-filter"></a>
## 2. IIR Filter (Infinite Impulse Response, 무한 임펄스 응답 필터)

**개념**: 출력에 과거 출력을 되먹임(recursive)하여 계산. 임펄스 응답이 이론상 무한히 지속됨.

**수식**:
```
y[n] = Σ_{k=0}^{M} b_k · x[n−k] − Σ_{k=1}^{N} a_k · y[n−k]
```
Z-변환 전달함수:
```
H(z) = (b_0 + b_1 z^{−1} + ... + b_M z^{−M})
       / (1 + a_1 z^{−1} + ... + a_N z^{−N})
```
극점(pole) `a_k`가 분모에 존재 → 안정성 조건: 모든 pole 이 단위원 내부 (|z| < 1).

**목적**: 가파른 cutoff 가 필요하면서도 계산량을 줄여야 할 때

**시간 복잡도**: 샘플당 O(N+M) — 통상 N=M=2~8 정도 (FIR 보다 1~2 자리 작음)

**공간 복잡도**: O(N+M)

**특징**:
- 아날로그 prototype 변환 → Butterworth, Chebyshev I/II, Bessel, Elliptic
- Bilinear transform 으로 s-domain → z-domain 매핑
- SOS (Second-Order Sections) cascaded 구현이 수치적으로 안정적
- 일반적으로 nonlinear phase

**장점**:
- 동일 sharpness 에 FIR 대비 차수 ~10× 작음 → 계산량/메모리 절약
- 짧은 그룹 지연
- 임베디드/실시간 처리에 유리

**단점**:
- Pole 위치에 따라 **불안정** 가능 — 양자화/오차에 민감
- Nonlinear phase → 위상 왜곡 (오디오에서 transient smearing)
- Limit cycle (자기 진동) 발생 가능 (fixed-point 구현)
- 설계 후 검증 필수 (`abs(poles) < 1`)

**활용 예시**:
- 임베디드 센서 노이즈 제거 (저전력)
- 오디오 시뮬레이션 IIR (analog modeling)
- 제어 시스템 PID → IIR 등가
- 전력선 50/60Hz hum 제거 (notch filter)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Python (scipy) 코드**:
```python
import numpy as np
from scipy import signal

# 1) Butterworth 저역통과 (4차) 설계 → SOS 형식
fs = 1000.0
sos = signal.butter(N=4, Wn=100.0, btype='low', fs=fs, output='sos')

# 2) 적용 - SOS 가 transposed direct form II 라 수치적으로 가장 안정
x = np.random.randn(2000)
y = signal.sosfilt(sos, x)

# 3) 제로 위상 IIR (오프라인) — forward + backward
y_zero = signal.sosfiltfilt(sos, x)

# 4) 안정성 검증
z, p, k = signal.tf2zpk(*signal.butter(4, 0.2, output='ba'))
assert np.all(np.abs(p) < 1.0), "IIR 불안정: pole 이 단위원 밖"

# 5) Notch (50Hz hum 제거) — IIR 이 자연스러움
b_notch, a_notch = signal.iirnotch(w0=50.0, Q=30.0, fs=fs)
```

**Kotlin 코드**:
```kotlin
/**
 * Biquad (2차 IIR section) — IIR 의 기본 building block.
 * Transposed Direct Form II 구현 (수치적으로 가장 안정).
 *   y[n] = b0·x[n] + s1
 *   s1   = b1·x[n] − a1·y[n] + s2
 *   s2   = b2·x[n] − a2·y[n]
 */
class Biquad(
    private val b0: Double, private val b1: Double, private val b2: Double,
    private val a1: Double, private val a2: Double
) {
    private var s1 = 0.0
    private var s2 = 0.0

    fun process(x: Double): Double {
        val y = b0 * x + s1
        s1 = b1 * x - a1 * y + s2
        s2 = b2 * x - a2 * y
        return y
    }
    fun reset() { s1 = 0.0; s2 = 0.0 }
}

/** SOS cascade — 고차 IIR 안정 구현 */
class SosFilter(private val sections: List<Biquad>) {
    fun process(x: Double): Double {
        var y = x
        for (s in sections) y = s.process(y)
        return y
    }
}

// RBJ Audio EQ Cookbook 기반 저역통과 biquad 계수
fun lowpassBiquad(fc: Double, q: Double, fs: Double): Biquad {
    val w0 = 2 * Math.PI * fc / fs
    val alpha = Math.sin(w0) / (2 * q)
    val cosW = Math.cos(w0)
    val a0 = 1 + alpha
    val b0 = (1 - cosW) / 2 / a0
    val b1 = (1 - cosW) / a0
    val b2 = (1 - cosW) / 2 / a0
    val a1 = -2 * cosW / a0
    val a2 = (1 - alpha) / a0
    return Biquad(b0, b1, b2, a1, a2)
}
```

**관련 알고리즘**: [FIR Filter](#fir-filter), Butterworth/Chebyshev prototype, Bilinear transform

---

<a id="stft"></a>
## 3. STFT (Short-Time Fourier Transform, 단시간 푸리에 변환)

**개념**: 신호를 짧은 시간 윈도우로 잘라 각 구간에 FFT 적용 → 시간-주파수 평면 표현 획득. 결과를 `|X(t,f)|²` 로 시각화한 것이 **spectrogram**.

**수식**:
```
X(m, ω) = Σ_{n=−∞}^{∞}  x[n] · w[n − mH] · e^{−jωn}
```
- `w[·]` : 윈도우 함수 (Hann, Hamming, Blackman 등)
- `H` : hop size (윈도우 이동 간격)
- `m` : 프레임 인덱스 (시간 축)
- `ω` : 정규화 주파수

**목적**: 비정상 신호 (시간에 따라 주파수 성분이 변하는 신호) 의 시간-주파수 분석

**시간 복잡도**: O((L/H) · N log N), L=신호 길이, N=윈도우 길이

**공간 복잡도**: O(L/H · N/2) — 복소 스펙트럼 매트릭스

**특징**:
- 시간-주파수 해상도 trade-off (Heisenberg 불확정성):
  - 윈도우 짧음 → 시간 해상도 ↑, 주파수 해상도 ↓
  - 윈도우 김 → 주파수 해상도 ↑, 시간 해상도 ↓
- COLA (Constant OverLap Add) 조건 충족 시 완전 재구성 가능
- 통상 50% overlap (`H = N/2`) 의 Hann 윈도우 사용

**장점**:
- FFT 기반 — 빠르고 구현 단순
- spectrogram 시각화 직관적
- 음성/음악 분석 표준 도구

**단점**:
- 시간-주파수 해상도 고정 (윈도우 크기로 결정됨)
- 저주파 정확도와 고주파 정확도 동시 확보 불가 → wavelet 으로 보완
- 윈도우 경계 효과 (spectral leakage) — 적절한 window 선택 필수

**활용 예시**:
- 음성 인식 (Mel-spectrogram 전처리 → 딥러닝 입력)
- 음악 분석 (chord/onset detection, pitch tracking)
- 라디오 신호 분석, EEG/EMG 시간-주파수 분석
- 기계 결함 진단 (vibration spectrogram)

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Python (scipy) 코드**:
```python
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

fs = 8000.0
t = np.linspace(0, 2, int(fs * 2), endpoint=False)
# Chirp: 100Hz → 2000Hz (시간에 따라 주파수 변화)
x = signal.chirp(t, f0=100, f1=2000, t1=2, method='linear')

# 1) STFT
f, t_seg, Zxx = signal.stft(
    x, fs=fs,
    window='hann',
    nperseg=512,        # 윈도우 길이 N
    noverlap=256,       # overlap (hop = N − overlap = 256)
    nfft=512
)
# Zxx.shape = (n_freq, n_frames), complex
spec_db = 20 * np.log10(np.abs(Zxx) + 1e-10)

# 2) Inverse STFT (재구성)
_, x_reconstructed = signal.istft(Zxx, fs=fs, window='hann',
                                   nperseg=512, noverlap=256)

# 3) Spectrogram 시각화
plt.pcolormesh(t_seg, f, spec_db, shading='gouraud')
plt.ylabel('Frequency [Hz]'); plt.xlabel('Time [s]')

# Mel-spectrogram (음성 인식 표준) - librosa
# import librosa
# mel = librosa.feature.melspectrogram(y=x, sr=fs, n_fft=512, hop_length=256, n_mels=80)
```

**Kotlin 코드**:
```kotlin
import kotlin.math.PI
import kotlin.math.cos

/** Hann 윈도우 */
fun hannWindow(n: Int): DoubleArray =
    DoubleArray(n) { i -> 0.5 * (1.0 - cos(2 * PI * i / (n - 1))) }

/**
 * STFT — 입력 신호를 N 길이 프레임으로 윈도우 적용 후 FFT.
 * fft() 는 math.md 의 FFT 구현을 재사용 한다고 가정.
 */
fun stft(
    x: DoubleArray,
    frameSize: Int = 512,
    hopSize: Int = 256
): Array<DoubleArray> {
    val window = hannWindow(frameSize)
    val nFrames = (x.size - frameSize) / hopSize + 1
    val magnitude = Array(nFrames) { DoubleArray(frameSize / 2 + 1) }

    for (m in 0 until nFrames) {
        val frame = DoubleArray(frameSize) { i ->
            x[m * hopSize + i] * window[i]
        }
        val spectrum = fftReal(frame)   // Complex 배열 반환 (math.md FFT 활용)
        for (k in 0..frameSize / 2) {
            val re = spectrum[k].re
            val im = spectrum[k].im
            magnitude[m][k] = Math.sqrt(re * re + im * im)
        }
    }
    return magnitude   // [frame][freqBin]
}
```

**관련 알고리즘**: [FFT](math.md#fast-fourier-transform), [Wavelet Transform](#wavelet), Window functions, [Auto-correlation](#autocorrelation)

---

<a id="wavelet"></a>
## 4. Wavelet Transform (웨이블릿 변환)

**개념**: 신호를 시간-주파수가 아닌 시간-스케일 평면으로 분해. 스케일이 작을수록 시간 해상도 ↑, 클수록 주파수 해상도 ↑ → **다중 해상도 분석** (Multi-Resolution Analysis).

**수식**:
- 연속 웨이블릿 변환 (CWT):
  ```
  W(a, b) = (1/√a) · ∫ x(t) · ψ*((t − b) / a) dt
  ```
  - `ψ(t)` : mother wavelet (Morlet, Mexican hat, Daubechies 등)
  - `a` : 스케일 (주파수 ∝ 1/a), `b` : 시간 이동
- 이산 웨이블릿 변환 (DWT, Mallat algorithm):
  ```
  cA_{j+1}[k] = Σ_n h[n − 2k] · cA_j[n]    (low-pass + downsample)
  cD_{j+1}[k] = Σ_n g[n − 2k] · cA_j[n]    (high-pass + downsample)
  ```
  - `cA` : approximation (저주파), `cD` : detail (고주파)
  - 매 레벨마다 길이가 반으로 줄어 다단계 분해

**목적**: 비정상 신호의 다중 해상도 분석, 압축, 노이즈 제거

**시간 복잡도**: DWT O(N), CWT O(N·S) (S=스케일 개수)

**공간 복잡도**: DWT O(N) — 원본과 동일

**특징**:
- STFT 대비 **시간-주파수 해상도가 가변** (저주파 → 긴 윈도우, 고주파 → 짧은 윈도우)
- Filter bank 로 구현 (Mallat pyramid)
- Daubechies (dbN), Symlets (symN), Coiflets, Biorthogonal 등 wavelet family
- Soft/Hard thresholding 으로 denoising

**장점**:
- 시간 국소화 + 주파수 국소화 동시 개선
- transient/edge 검출에 강함
- 압축률 ↑ (JPEG 2000 의 핵심)

**단점**:
- Wavelet 선택이 결과에 큰 영향 → 도메인 지식 필요
- 직관적 해석이 STFT 보다 어려움
- shift-variant (입력 위치 이동 시 계수 변화 큼) — Stationary WT 로 보완

**활용 예시**:
- **JPEG 2000** 이미지 압축 (CDF 9/7 biorthogonal wavelet)
- ECG/EEG 노이즈 제거 (medical signal)
- 지진파 분석, 금융 시계열 분석
- 이미지 fusion, multi-resolution edge detection

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Python (PyWavelets) 코드**:
```python
import numpy as np
import pywt

# 1) DWT 다단계 분해 (Daubechies 4, 레벨 4)
x = np.random.randn(1024) + np.sin(np.linspace(0, 20*np.pi, 1024))
coeffs = pywt.wavedec(x, wavelet='db4', level=4)
# coeffs = [cA4, cD4, cD3, cD2, cD1]
cA4, cD4, cD3, cD2, cD1 = coeffs

# 2) 재구성
x_reconstructed = pywt.waverec(coeffs, wavelet='db4')

# 3) Soft thresholding denoising (Donoho-Johnstone universal threshold)
sigma = np.median(np.abs(cD1)) / 0.6745   # MAD noise estimate
threshold = sigma * np.sqrt(2 * np.log(len(x)))
coeffs_denoised = [coeffs[0]] + [
    pywt.threshold(c, threshold, mode='soft') for c in coeffs[1:]
]
x_denoised = pywt.waverec(coeffs_denoised, wavelet='db4')

# 4) CWT (Morlet wavelet) — spectrogram 유사 출력
scales = np.arange(1, 128)
cwt_matrix, freqs = pywt.cwt(x, scales, 'morl', sampling_period=1.0/1000)
# cwt_matrix.shape = (n_scales, n_samples)
```

**Kotlin 코드**:
```kotlin
/**
 * Haar Wavelet 1-level DWT — 가장 단순한 wavelet.
 * h = [1/√2, 1/√2] (lowpass), g = [1/√2, −1/√2] (highpass).
 */
fun haarDwt1Level(x: DoubleArray): Pair<DoubleArray, DoubleArray> {
    require(x.size % 2 == 0) { "입력 길이는 짝수여야 함" }
    val half = x.size / 2
    val cA = DoubleArray(half)   // approximation
    val cD = DoubleArray(half)   // detail
    val invSqrt2 = 1.0 / Math.sqrt(2.0)
    for (k in 0 until half) {
        cA[k] = (x[2 * k] + x[2 * k + 1]) * invSqrt2
        cD[k] = (x[2 * k] - x[2 * k + 1]) * invSqrt2
    }
    return cA to cD
}

/** N-level Haar DWT — pyramidal decomposition */
fun haarDwt(x: DoubleArray, levels: Int): List<DoubleArray> {
    val result = mutableListOf<DoubleArray>()
    var current = x
    repeat(levels) {
        val (cA, cD) = haarDwt1Level(current)
        result.add(0, cD)        // 가장 미세한 detail 이 마지막
        current = cA
    }
    result.add(0, current)        // 최종 approximation
    return result                  // [cA_n, cD_n, cD_{n-1}, ..., cD_1]
}

/** Soft threshold — denoising */
fun softThreshold(x: DoubleArray, lambda: Double): DoubleArray =
    DoubleArray(x.size) { i ->
        val v = x[i]
        when {
            v > lambda -> v - lambda
            v < -lambda -> v + lambda
            else -> 0.0
        }
    }
```

**관련 알고리즘**: [STFT](#stft), Multi-resolution analysis, [FFT](math.md#fast-fourier-transform) (CWT 가속), Subband coding

---

<a id="resampling"></a>
## 5. Resampling — Upsampling / Downsampling (재표본화)

**개념**: 신호의 샘플레이트를 변경. 단순 보간/추출이 아닌 **anti-aliasing/anti-imaging 필터** 동반 필수.

**수식**:
- 업샘플링 (L배 증가): zero-insertion 후 저역통과 필터
  ```
  x_L[n] = x[n/L]  if n mod L = 0,  else 0
  y[n]   = x_L[n] * h_LP[n]   (anti-imaging filter, cutoff = π/L)
  ```
- 다운샘플링 (M배 감소): 저역통과 필터 후 추출
  ```
  v[n] = x[n] * h_LP[n]       (anti-aliasing filter, cutoff = π/M)
  y[n] = v[nM]
  ```
- 유리수 비율 변경 (L/M): 업샘플 L 배 → 단일 LP (cutoff = min(π/L, π/M)) → 다운샘플 M 배

**목적**: 샘플레이트 변환 (44.1kHz ↔ 48kHz, 16kHz → 8kHz 등)

**시간 복잡도**: Polyphase 구현 시 출력 샘플당 O(N/L) (N=필터 차수, L=업샘플 배수)

**공간 복잡도**: O(N) — 필터 계수 + delay line

**특징**:
- **Polyphase decomposition** 으로 zero 곱셈 회피 → 계산량 1/L 로 감소
- Sinc interpolation (이론상 ideal) 은 무한 길이 → 윈도잉된 sinc 가 표준 (Kaiser window)
- Multi-rate processing 의 핵심 building block

**장점**:
- 정확한 샘플레이트 변환
- Polyphase 로 효율적
- Cascaded decimation (CIC + FIR) 으로 더 큰 비율 효율 처리

**단점**:
- 필터 설계 잘못 → aliasing/imaging 아티팩트 발생
- 비정수 비율은 polyphase 가 복잡
- 그룹 지연 발생

**활용 예시**:
- 오디오 44.1kHz ↔ 48kHz 변환 (CD ↔ DAT/DVD)
- 디지털 라디오의 sample rate adaptation
- 이미지 zoom in/out (2D resampling)
- 통신 시스템의 baseband ↔ IF 변환 (decimation/interpolation)

**난이도**: 중간 | **사용 빈도**: ★★★★☆

**Python (scipy) 코드**:
```python
import numpy as np
from scipy import signal

fs_in = 48000.0
fs_out = 16000.0
x = np.random.randn(48000)   # 1초 신호

# 1) 단순 정수 비율 (M=3 다운샘플) — anti-aliasing 자동
y_decimated = signal.decimate(x, q=3, ftype='fir', zero_phase=True)

# 2) 임의 비율 (44.1k → 48k 등) — polyphase
y_resampled = signal.resample_poly(x, up=1, down=3)   # 48000 → 16000

# 3) FFT-based (deprecated for production — boundary 아티팩트)
y_fft = signal.resample(x, num=16000)

# 4) Upsample by L=2 + Lowpass filter (수동 polyphase 시연)
L = 2
x_up = np.zeros(len(x) * L)
x_up[::L] = x                                        # zero-insertion
h = signal.firwin(63, cutoff=0.5/L, window='kaiser', fs=2.0)  # cutoff = π/L
y_up = signal.lfilter(h, 1.0, x_up) * L              # L 곱해 진폭 보정

# 5) librosa 권장 (음성/음악) — scipy 보다 antialiasing 품질 ↑
# import librosa
# y_lr = librosa.resample(x, orig_sr=48000, target_sr=16000, res_type='kaiser_best')
```

**Kotlin 코드**:
```kotlin
/**
 * 정수배 업샘플링 (factor L) — zero-insertion 후 anti-imaging FIR.
 */
fun upsample(x: DoubleArray, L: Int, taps: DoubleArray): DoubleArray {
    val xUp = DoubleArray(x.size * L)
    for (i in x.indices) xUp[i * L] = x[i] * L     // L 곱해 진폭 보존
    // FIR 적용 (anti-imaging)
    val fir = FirFilter(taps)
    return DoubleArray(xUp.size) { fir.process(xUp[it]) }
}

/**
 * 정수배 다운샘플링 (factor M) — anti-aliasing FIR 후 M 마다 추출.
 */
fun downsample(x: DoubleArray, M: Int, taps: DoubleArray): DoubleArray {
    val fir = FirFilter(taps)
    val filtered = DoubleArray(x.size) { fir.process(x[it]) }
    val out = DoubleArray(x.size / M)
    for (i in out.indices) out[i] = filtered[i * M]
    return out
}

/**
 * Polyphase decomposition (L=2 단순 예시)
 * 필터 h 를 짝수/홀수 인덱스 sub-filter 로 분해 → zero 곱셈 제거.
 */
fun polyphaseInterpolateBy2(x: DoubleArray, h: DoubleArray): DoubleArray {
    val h0 = DoubleArray(h.size / 2) { h[2 * it] }       // 짝수 phase
    val h1 = DoubleArray(h.size / 2) { h[2 * it + 1] }   // 홀수 phase
    val out = DoubleArray(x.size * 2)
    val f0 = FirFilter(h0)
    val f1 = FirFilter(h1)
    for (i in x.indices) {
        out[2 * i]     = f0.process(x[i]) * 2
        out[2 * i + 1] = f1.process(x[i]) * 2
    }
    return out
}
```

**관련 알고리즘**: [FIR Filter](#fir-filter), [IIR Filter](#iir-filter), CIC filter, Kaiser window design

---

<a id="kalman-filter"></a>
## 6. Kalman Filter (칼만 필터)

**개념**: 노이즈 섞인 선형 동적 시스템에서 상태(state)의 **최적 베이즈 추정**. Predict (시간 업데이트) + Update (측정 업데이트) 2단계 반복.

**시스템 모델**:
```
상태 방정식:  x_k   = F_k · x_{k−1} + B_k · u_k + w_k       (w_k ~ N(0, Q_k))
측정 방정식:  z_k   = H_k · x_k + v_k                        (v_k ~ N(0, R_k))
```
- `x_k` : 상태 벡터 (n×1), `z_k` : 측정 벡터 (m×1)
- `F` : 상태 전이 행렬, `H` : 측정 행렬
- `Q` : 프로세스 잡음 공분산, `R` : 측정 잡음 공분산
- `P` : 상태 추정 오차 공분산

**Predict 단계** (a priori):
```
x̂_k|k−1 = F_k · x̂_{k−1|k−1} + B_k · u_k
P_k|k−1 = F_k · P_{k−1|k−1} · F_k^T + Q_k
```

**Update 단계** (a posteriori):
```
y_k = z_k − H_k · x̂_k|k−1                       (innovation, residual)
S_k = H_k · P_k|k−1 · H_k^T + R_k                 (innovation covariance)
K_k = P_k|k−1 · H_k^T · S_k^{−1}                  (Kalman gain)
x̂_k|k = x̂_k|k−1 + K_k · y_k
P_k|k = (I − K_k · H_k) · P_k|k−1
```

**목적**: 잡음·불확실성 하 동적 시스템 상태 추정 — 위치, 속도, 자세 등

**시간 복잡도**: 스텝당 O(n³ + m³) (행렬 곱셈/역행렬)

**공간 복잡도**: O(n²)

**특징**:
- 선형 + Gaussian 가정 하 **MMSE 최적 추정기** (Minimum Mean Square Error)
- Recursive — 과거 측정 저장 불필요
- `K_k` 가 0 에 가까우면 모델 신뢰, 1 에 가까우면 측정 신뢰

**장점**:
- 실시간 처리 가능
- 다중 센서 융합 자연스러움 (H 확장)
- 수학적으로 엄밀, 수렴 보장 (관측가능성 만족 시)

**단점**:
- 선형 시스템 전제 — 비선형은 EKF/UKF 필요
- Gaussian 잡음 전제 → outlier 에 약함
- Q, R 튜닝 까다로움 — 잘못 설정하면 발산
- 비관측 상태 추정 시 P 발산

**활용 예시**:
- **GPS + IMU sensor fusion** (드론, 차량 navigation)
- 미사일/위성 궤도 추적 (역사적 첫 응용)
- 금융 시계열 추적 (state-space ARIMA)
- 컴퓨터 비전 object tracking (등속도/등가속 모델)
- 배터리 SOC (State of Charge) 추정

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Python (numpy) 코드**:
```python
import numpy as np

class KalmanFilter1D:
    """
    상수 속도 모델: 상태 x = [position, velocity], 측정 = position.
        F = [[1, dt], [0, 1]],  H = [[1, 0]]
    """
    def __init__(self, dt=1.0, process_var=1e-3, meas_var=1e-1):
        self.x = np.zeros((2, 1))                 # 초기 상태
        self.P = np.eye(2) * 1.0                  # 초기 공분산
        self.F = np.array([[1, dt], [0, 1]])
        self.H = np.array([[1, 0]])
        self.Q = np.array([[dt**4/4, dt**3/2],    # 등가속도 잡음 모델
                           [dt**3/2, dt**2  ]]) * process_var
        self.R = np.array([[meas_var]])

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x

    def update(self, z):
        z = np.atleast_2d(z).reshape(-1, 1)
        y = z - self.H @ self.x                   # innovation
        S = self.H @ self.P @ self.H.T + self.R   # innovation cov
        K = self.P @ self.H.T @ np.linalg.inv(S)  # Kalman gain
        self.x = self.x + K @ y
        self.P = (np.eye(2) - K @ self.H) @ self.P
        return self.x

# 사용 예
kf = KalmanFilter1D(dt=0.1, process_var=1e-3, meas_var=0.5)
true_pos = np.linspace(0, 10, 100)
noisy_meas = true_pos + np.random.randn(100) * 0.5
estimates = []
for z in noisy_meas:
    kf.predict()
    estimates.append(kf.update(z)[0, 0])
```

**Kotlin 코드**:
```kotlin
/**
 * 1D Kalman Filter — 위치/속도 추정.
 * 행렬 라이브러리 없이 명시적 구현 (학습용).
 * 실제로는 EJML / Multik / la4k 사용 권장.
 */
class KalmanFilter1D(
    private val dt: Double = 1.0,
    private val processVar: Double = 1e-3,
    private val measVar: Double = 1e-1
) {
    // 상태 [position, velocity]
    private var x = doubleArrayOf(0.0, 0.0)
    // 공분산 P (2×2 row-major)
    private var p = doubleArrayOf(1.0, 0.0, 0.0, 1.0)

    fun predict() {
        // x = F · x  where F = [[1, dt], [0, 1]]
        x = doubleArrayOf(x[0] + dt * x[1], x[1])

        // P = F P F^T + Q
        val dt2 = dt * dt; val dt3 = dt2 * dt; val dt4 = dt3 * dt
        val q00 = dt4 / 4 * processVar
        val q01 = dt3 / 2 * processVar
        val q11 = dt2 * processVar

        val p00n = p[0] + dt * (p[1] + p[2]) + dt2 * p[3] + q00
        val p01n = p[1] + dt * p[3] + q01
        val p10n = p[2] + dt * p[3] + q01
        val p11n = p[3] + q11
        p = doubleArrayOf(p00n, p01n, p10n, p11n)
    }

    fun update(z: Double): Double {
        // H = [1, 0]
        val y = z - x[0]                           // innovation
        val s = p[0] + measVar                     // S = H P H^T + R
        val k0 = p[0] / s                          // Kalman gain
        val k1 = p[2] / s

        x[0] += k0 * y
        x[1] += k1 * y

        // P = (I − K H) P
        val p00 = (1 - k0) * p[0]
        val p01 = (1 - k0) * p[1]
        val p10 = p[2] - k1 * p[0]
        val p11 = p[3] - k1 * p[1]
        p = doubleArrayOf(p00, p01, p10, p11)
        return x[0]
    }

    fun position(): Double = x[0]
    fun velocity(): Double = x[1]
}
```

**관련 알고리즘**: [Extended/Unscented Kalman](#extended-kalman), Particle Filter, Recursive Least Squares, Hidden Markov Model

---

<a id="extended-kalman"></a>
## 7. Extended / Unscented Kalman Filter (EKF / UKF, 확장/무향 칼만 필터)

**개념**: 비선형 시스템에 Kalman Filter 적용을 위한 확장. EKF 는 **Jacobian 선형화**, UKF 는 **unscented transform** (시그마 포인트 기반 통계량 전파) 사용.

**EKF 시스템 모델**:
```
x_k = f(x_{k−1}, u_k) + w_k          (비선형 상태 전이)
z_k = h(x_k) + v_k                    (비선형 측정)
```

**EKF Predict**:
```
x̂_k|k−1 = f(x̂_{k−1|k−1}, u_k)
F_k     = ∂f/∂x | x̂_{k−1|k−1}        (Jacobian)
P_k|k−1 = F_k · P_{k−1|k−1} · F_k^T + Q_k
```

**EKF Update**:
```
H_k = ∂h/∂x | x̂_k|k−1
y_k = z_k − h(x̂_k|k−1)
S_k = H_k · P_k|k−1 · H_k^T + R_k
K_k = P_k|k−1 · H_k^T · S_k^{−1}
x̂_k|k = x̂_k|k−1 + K_k · y_k
P_k|k = (I − K_k · H_k) · P_k|k−1
```

**UKF 시그마 포인트** (2n+1 개):
```
χ_0 = x̂
χ_i        = x̂ + (√((n+λ) P))_i        i = 1..n
χ_{i+n}    = x̂ − (√((n+λ) P))_i        i = 1..n
```
- 각 시그마 포인트를 비선형 `f`, `h` 로 직접 전파한 뒤 가중 평균/공분산 재계산
- `λ = α²(n+κ) − n` (튜닝 파라미터, 통상 α=1e-3, κ=0)

**목적**: GPS+IMU, 로봇 SLAM 등 비선형 상태 추정

**시간 복잡도**:
- EKF: 스텝당 O(n³) + Jacobian 비용
- UKF: 스텝당 O(n³) (sigma point: 2n+1 회 비선형 함수 평가)

**공간 복잡도**: O(n²)

**특징**:
- EKF: 1차 Taylor 근사 → 비선형성 강할수록 부정확/발산
- UKF: 2차 정확도까지 보존, Jacobian 불필요
- Cubature Kalman Filter (CKF) — UKF 의 변형, 더 안정

**장점**:
- 비선형 시스템 적용 가능
- UKF 는 미분 불가 함수에도 적용 (Jacobian 없음)
- 실시간 가능

**단점**:
- EKF: Jacobian 유도 번거롭고 오류 발생 가능, 강한 비선형성에서 발산
- UKF: 시그마 포인트 가중치/스케일 파라미터 튜닝 필요
- 둘 다 multimodal posterior 표현 불가 → Particle Filter

**활용 예시**:
- 드론/로봇 자세 추정 (Attitude — quaternion 비선형)
- SLAM (Simultaneous Localization and Mapping) — EKF-SLAM
- 차량 GPS+IMU+Odometer 융합
- 화학 공정 비선형 제어
- 배터리 SOC + SOH 동시 추정

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Python (filterpy 사용) 코드**:
```python
import numpy as np
from filterpy.kalman import ExtendedKalmanFilter, UnscentedKalmanFilter
from filterpy.kalman import MerweScaledSigmaPoints

# === EKF: 비선형 측정 = range 측정 (radar) ===
# 상태 x = [pos, vel], 측정 = sqrt(pos² + h²) (h=레이더 고도)
def hx(x, h=20.0):
    return np.array([np.sqrt(x[0]**2 + h**2)])

def H_jacobian(x, h=20.0):
    r = np.sqrt(x[0]**2 + h**2)
    return np.array([[x[0] / r, 0.0]])

ekf = ExtendedKalmanFilter(dim_x=2, dim_z=1)
ekf.x = np.array([0.0, 1.0])
ekf.F = np.array([[1, 0.1], [0, 1]])
ekf.P *= 10
ekf.R = np.array([[0.5]])
ekf.Q = np.diag([0.01, 0.01])

# 한 스텝
z = np.array([22.0])
ekf.predict()
ekf.update(z, HJacobian=H_jacobian, Hx=hx)

# === UKF: 동일 시스템, Jacobian 없이 ===
def fx(x, dt):
    return np.array([x[0] + dt * x[1], x[1]])

points = MerweScaledSigmaPoints(n=2, alpha=1e-3, beta=2.0, kappa=0.0)
ukf = UnscentedKalmanFilter(dim_x=2, dim_z=1, dt=0.1, fx=fx, hx=hx, points=points)
ukf.x = np.array([0.0, 1.0])
ukf.P *= 10
ukf.R = np.array([[0.5]])
ukf.Q = np.diag([0.01, 0.01])

ukf.predict()
ukf.update(z)
```

**Kotlin 코드**:
```kotlin
/**
 * 1D EKF — 비선형 측정 h(x) = √(x² + h_alt²) (range measurement).
 * 상태 = [position, velocity], 측정 = scalar range.
 *
 * 실전에서는 EJML/la4k 등 행렬 라이브러리 사용 권장.
 */
class ExtendedKalmanFilter1D(
    private val dt: Double = 0.1,
    private val altitude: Double = 20.0,
    private val processVar: Double = 0.01,
    private val measVar: Double = 0.5
) {
    private var x = doubleArrayOf(0.0, 1.0)       // [pos, vel]
    private var p = doubleArrayOf(10.0, 0.0, 0.0, 10.0)

    /** 비선형 측정 모델 h(x) */
    private fun hx(state: DoubleArray): Double =
        Math.sqrt(state[0] * state[0] + altitude * altitude)

    /** Jacobian H = ∂h/∂x at current state */
    private fun jacobianH(state: DoubleArray): DoubleArray {
        val r = hx(state)
        return doubleArrayOf(state[0] / r, 0.0)
    }

    fun predict() {
        // 선형 상태 전이 F = [[1, dt], [0, 1]]
        x = doubleArrayOf(x[0] + dt * x[1], x[1])
        val dt2 = dt * dt
        // P = F P F^T + Q (단순 diag Q)
        val p00 = p[0] + dt * (p[1] + p[2]) + dt2 * p[3] + processVar
        val p01 = p[1] + dt * p[3]
        val p10 = p[2] + dt * p[3]
        val p11 = p[3] + processVar
        p = doubleArrayOf(p00, p01, p10, p11)
    }

    fun update(z: Double): DoubleArray {
        val h = jacobianH(x)
        // S = H P H^T + R  (스칼라)
        val ph0 = p[0] * h[0] + p[1] * h[1]
        val ph1 = p[2] * h[0] + p[3] * h[1]
        val s = h[0] * ph0 + h[1] * ph1 + measVar
        // K = P H^T / S
        val k0 = ph0 / s
        val k1 = ph1 / s
        // y = z − h(x)
        val y = z - hx(x)
        x = doubleArrayOf(x[0] + k0 * y, x[1] + k1 * y)
        // P = (I − K H) P
        val p00 = (1 - k0 * h[0]) * p[0] - k0 * h[1] * p[2]
        val p01 = (1 - k0 * h[0]) * p[1] - k0 * h[1] * p[3]
        val p10 = -k1 * h[0] * p[0] + (1 - k1 * h[1]) * p[2]
        val p11 = -k1 * h[0] * p[1] + (1 - k1 * h[1]) * p[3]
        p = doubleArrayOf(p00, p01, p10, p11)
        return x
    }
}
```

**관련 알고리즘**: [Kalman Filter](#kalman-filter), Particle Filter, Cubature Kalman Filter, [Newton-Raphson](math.md#newton-raphson) (Jacobian 동일 개념)

---

<a id="autocorrelation"></a>
## 8. Auto-correlation / Cross-correlation (자기/교차 상관)

**개념**: 신호 자기 자신 또는 다른 신호와의 lag 별 유사도 측정. 주기성·지연·매칭 검출의 기본 도구.

**수식**:
- 자기 상관 (Autocorrelation):
  ```
  R_xx[τ] = Σ_n x[n] · x[n + τ]
  ```
- 교차 상관 (Cross-correlation):
  ```
  R_xy[τ] = Σ_n x[n] · y[n + τ]
  ```
- 정규화 (NCC, Normalized Cross-Correlation):
  ```
  ρ_xy[τ] = R_xy[τ] / √(R_xx[0] · R_yy[0])      ∈ [−1, 1]
  ```
- **Wiener-Khinchin 정리** — 자기 상관과 PSD (Power Spectral Density) 는 푸리에 쌍:
  ```
  R_xx[τ] ⟷ |X(ω)|²
  ```
  → FFT 로 O(N log N) 자기 상관 계산 가능

**목적**: 신호의 lag, 주기, 유사 패턴 탐지

**시간 복잡도**:
- Naive: O(N²)
- FFT 기반: O(N log N) (Wiener-Khinchin)

**공간 복잡도**: O(N)

**특징**:
- Autocorrelation 의 peak 위치 = 신호의 주기성
- Cross-correlation 의 peak 위치 = 두 신호 간 time delay
- Autocorr 는 even function: `R_xx[−τ] = R_xx[τ]`
- 정규화 NCC 는 진폭 변화에 강건 (template matching)

**장점**:
- 개념·구현 단순
- FFT 로 매우 빠름
- 노이즈에 비교적 강건 (적분/평균 효과)

**단점**:
- Stationary signal 가정
- Peak 가 여러 개면 모호 (multipath echo)
- Cyclic vs linear correlation 구분 필요 (FFT 사용 시 zero-padding 필수)

**활용 예시**:
- **Pitch detection** (음성 기본 주파수 추정)
- **Echo cancellation** — 마이크 입력과 출력 신호 간 지연 측정
- 레이더/소나 TOF (Time-Of-Flight) 측정
- GPS 의사거리 측정 (PRN code correlation)
- 통신 시스템 frame synchronization
- ECG QRS 검출, 지진파 P/S wave 도착 시각

**난이도**: 중간 | **사용 빈도**: ★★★★★

**Python (numpy/scipy) 코드**:
```python
import numpy as np
from scipy import signal

# 1) Naive correlation
x = np.array([1, 2, 3, 4, 5], dtype=float)
y = np.array([0, 1, 2, 3, 0], dtype=float)

# np.correlate — full mode 반환 (lag = −(N−1) ~ +(N−1))
r_full = np.correlate(x, y, mode='full')
lags = np.arange(-len(x) + 1, len(y))
best_lag = lags[np.argmax(r_full)]

# 2) FFT 기반 (Wiener-Khinchin) — 자기 상관
def autocorr_fft(x):
    n = len(x)
    N = 1 << (2 * n - 1).bit_length()       # 2의 거듭제곱, zero-padded
    X = np.fft.fft(x, N)
    psd = X * np.conjugate(X)                # |X|²
    r = np.fft.ifft(psd).real
    return r[:n]                              # 양의 lag 만

# 3) 정규화 교차 상관 (NCC) — template matching
def ncc(x, template):
    x = (x - x.mean()) / x.std()
    t = (template - template.mean()) / template.std()
    r = signal.correlate(x, t, mode='valid')
    return r / len(t)

# 4) Pitch detection 예 — 240Hz sinusoid at fs=8000
fs = 8000
t = np.arange(0, 1, 1/fs)
sig = np.sin(2 * np.pi * 240 * t) + 0.1 * np.random.randn(len(t))
ac = autocorr_fft(sig)
# 첫 번째 양의 peak (lag > min_period) 찾기
min_lag = int(fs / 500)                       # 500Hz 상한
peak_lag = min_lag + np.argmax(ac[min_lag:int(fs/50)])
estimated_pitch = fs / peak_lag               # ≈ 240
```

**Kotlin 코드**:
```kotlin
/**
 * Naive autocorrelation — O(N²).
 * 짧은 신호 또는 학습용. 긴 신호는 FFT 기반 사용.
 */
fun autocorrNaive(x: DoubleArray): DoubleArray {
    val n = x.size
    val r = DoubleArray(n)
    for (lag in 0 until n) {
        var sum = 0.0
        for (i in 0 until n - lag) {
            sum += x[i] * x[i + lag]
        }
        r[lag] = sum
    }
    return r
}

/**
 * Cross-correlation — full lag 범위 반환.
 *   lag = −(N−1) ~ +(N−1) 총 2N−1 개
 *   r[i]  = Σ x[k] · y[k + (i − (N−1))]
 */
fun crossCorrelate(x: DoubleArray, y: DoubleArray): DoubleArray {
    val n = x.size
    val m = y.size
    val out = DoubleArray(n + m - 1)
    for (i in out.indices) {
        var sum = 0.0
        val lag = i - (n - 1)
        for (k in 0 until n) {
            val j = k + lag
            if (j in 0 until m) sum += x[k] * y[j]
        }
        out[i] = sum
    }
    return out
}

/** 가장 잘 맞는 lag (peak 위치) */
fun bestLag(x: DoubleArray, y: DoubleArray): Int {
    val r = crossCorrelate(x, y)
    val argmax = r.indices.maxByOrNull { r[it] } ?: 0
    return argmax - (x.size - 1)                 // lag 보정
}

/**
 * FFT 기반 자기 상관 — O(N log N).
 * fft() 는 math.md 의 FFT 구현을 가정.
 */
fun autocorrFft(x: DoubleArray): DoubleArray {
    val n = x.size
    var N = 1
    while (N < 2 * n) N *= 2                     // zero-pad to power of 2
    val padded = DoubleArray(N) { if (it < n) x[it] else 0.0 }
    val spectrum = fftReal(padded)               // Complex[]
    // PSD = |X|²
    val psd = Array(N) { Complex(spectrum[it].magnitudeSquared(), 0.0) }
    val inv = ifft(psd)
    return DoubleArray(n) { inv[it].re }
}
```

**관련 알고리즘**: [FFT](math.md#fast-fourier-transform) (Wiener-Khinchin), [STFT](#stft), Matched filter, PSD estimation

---

## 신호 처리 체인 — 실전 예

전형적 오디오/센서 처리 파이프라인:

```
1. 신호 입력 (ADC)
        ↓
2. Anti-aliasing FIR/IIR  ───────  [FIR] [IIR]
        ↓
3. Resampling (target fs)  ───────  [Up/Downsample]
        ↓
4. 시간-주파수 분석          ───────  [STFT] or [Wavelet]
        ↓
5. Feature extraction
   - Pitch       ←  [Autocorrelation]
   - Onset       ←  [Spectral flux from STFT]
   - Energy
        ↓
6. (Optional) 상태 추정      ───────  [Kalman / EKF / UKF]
        ↓
7. 분류 / 회귀 (딥러닝)      ───────  → ml.md
```

각 단계에서 알고리즘 선택은 **신호 정상성**, **계산 자원**, **위상 제약**, **해상도 요구**에 따라 결정한다. 임베디드는 IIR + Kalman, 오프라인 분석은 FIR (linear phase) + Wavelet 이 일반적.

---

## 카탈로그 끝

본 카탈로그는 DSP 의 가장 자주 쓰이는 8 알고리즘만 다룬다. 다음 항목은 별도 카탈로그 또는 신설 예정:
- **Adaptive Filter** (LMS, RLS, NLMS) — 에코 캔슬, 노이즈 캔슬
- **Particle Filter** — 비-Gaussian/Multimodal 상태 추정
- **Beamforming** — 마이크 어레이, 안테나 어레이
- **MFCC / Mel-Filterbank** — 음성 인식 feature (ml.md 와 연계)
- **Hilbert Transform** — analytic signal, envelope/phase 추출

추가가 필요하면 카탈로그 신설 절차에 따라 `index.md` 와 본 파일을 함께 갱신한다.
