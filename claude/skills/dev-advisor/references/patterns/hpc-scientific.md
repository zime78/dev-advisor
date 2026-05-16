# HPC/과학 계산 패턴 (HPC & Scientific Computing Patterns)

수천~수십만 코어 / GPU 가속기 / NUMA 다중 소켓 환경에서 **수치 시뮬레이션·선형대수·기계학습 학습**을 확장 가능하게 실행하기 위한 6 패턴. 일반 분산 시스템과 달리 **저지연 인터커넥트(InfiniBand/NVLink) + bulk-synchronous 계산 + 부동소수점 처리량 최대화** 가 핵심.

**적용 영역**: 기후·CFD·분자동역학 시뮬레이션, LLM 사전학습(megatron-LM), 입자물리(LHC), 천체관측(SKA), 양자화학(VASP/Gaussian), 신약개발(AlphaFold), HPC 클러스터(Summit/Frontier/El Capitan).

**관련 카탈로그**:
- [`../algorithms/math.md`](../algorithms/math.md) — 선형대수 알고리즘 (GEMM, LU/QR/SVD)
- [`../algorithms/distributed.md`](../algorithms/distributed.md) — 분산 계산 알고리즘 (Allreduce 자체)
- [`../algorithms/concurrent.md`](../algorithms/concurrent.md) — Lock-free, Memory Barrier
- [`../languages/cuda-c-cplusplus.md`](../languages/cuda-c-cplusplus.md) — CUDA C++ 언어 표면
- [`../languages/fortran.md`](../languages/fortran.md) — 과학 계산 표준 언어
- [`../principles/performance-metrics.md`](../principles/performance-metrics.md) — Speedup, Efficiency, Strong/Weak Scaling
- [`../principles/formal-methods.md`](../principles/formal-methods.md) — 병렬 정합성 증명

---

## 1. MPI (Message Passing Interface) — 분산 메모리 메시지 전달

<a id="hpc-mpi"></a>

**정의**: 분산 메모리 다중 프로세스 간 명시적 메시지 전달로 SPMD(Single Program Multiple Data) 병렬을 표현하는 ANSI 표준 API. MPI Forum 이 1994 년 MPI-1.0 을 발표, 현재 **MPI 4.1 (2023)** 표준. MPICH / Open MPI / Intel MPI / Cray MPI 가 주요 구현. Top500 시스템 100% 가 MPI 기반.

**메커니즘**:
- **Communicator**: 프로세스 그룹 + 컨텍스트 (`MPI_COMM_WORLD` 가 기본)
- **Rank**: 각 프로세스의 0-based 고유 ID
- **Point-to-point**: `MPI_Send` / `MPI_Recv` 한 쌍의 sender↔receiver 통신
- **Collective**: 그룹 전체 동시 통신
  - `MPI_Bcast` (1→N), `MPI_Scatter` (1→N 분할), `MPI_Gather` (N→1 집계)
  - `MPI_Reduce` (N→1 + 연산), `MPI_Allreduce` (N→N + 연산, butterfly/ring)
  - `MPI_Alltoall` (N→N 전치 — FFT/행렬전치 핵심)
  - `MPI_Barrier` (그룹 동기화)
- **비차단(non-blocking)**: `MPI_Isend` / `MPI_Irecv` + `MPI_Wait` — 통신/계산 오버랩
- **비차단 collective (MPI-3)**: `MPI_Iallreduce` / `MPI_Ibcast` — collective 도 오버랩 가능
- **One-sided (MPI-2/3 RMA)**: `MPI_Put` / `MPI_Get` / `MPI_Accumulate` — passive target
- **Datatype**: `MPI_Type_create_struct` 로 비연속 메모리 패턴을 zero-copy 직렬화
- **Communication Topology**: `MPI_Cart_create` (cartesian 2D/3D 격자), `MPI_Graph_create` (임의 그래프) — 물리 인터커넥트와 매핑 최적화

**성능 모델 (α-β 모델, Hockney 1994)**:
```
T(n) = α + β × n
α = 지연(latency, μs)        — InfiniBand HDR ~1 μs, Ethernet ~10 μs
β = 1 / bandwidth (s/byte)   — IB HDR 200 Gbps ≈ 0.04 ns/byte
n = 메시지 크기 (bytes)
```
Allreduce 비용 (ring 알고리즘): `T = 2(P-1)α + 2(P-1)/P × n × β` — 큰 메시지에서는 대역폭이 지배.

**예시 (PI 계산 — Monte Carlo, C + MPI)**:
```c
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    long N = 100000000L / size;  /* 각 rank 가 N/P 샘플 */
    long local_hits = 0;
    unsigned int seed = rank * 7919 + 1;
    for (long i = 0; i < N; i++) {
        double x = (double)rand_r(&seed) / RAND_MAX;
        double y = (double)rand_r(&seed) / RAND_MAX;
        if (x*x + y*y <= 1.0) local_hits++;
    }

    long total_hits;
    /* N→1 reduction. SUM 연산. root=0 */
    MPI_Reduce(&local_hits, &total_hits, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        double pi = 4.0 * total_hits / (N * size);
        printf("PI ≈ %.10f (P=%d)\n", pi, size);
    }
    MPI_Finalize();
    return 0;
}
```

**비차단 + collective 오버랩 (계산-통신 hiding)**:
```c
MPI_Request req;
MPI_Iallreduce(local_grad, global_grad, N, MPI_FLOAT, MPI_SUM,
               MPI_COMM_WORLD, &req);     /* 비차단 시작 */
compute_other_layer();                     /* 그동안 다른 계산 진행 */
MPI_Wait(&req, MPI_STATUS_IGNORE);         /* 완료 대기 */
```

**Cartesian topology (3D 스텐실 — 18-point 격자)**:
```c
int dims[3] = {0,0,0};                              /* MPI 가 자동 분해 */
MPI_Dims_create(size, 3, dims);
int periods[3] = {1,1,1};                           /* periodic 경계 */
MPI_Comm cart;
MPI_Cart_create(MPI_COMM_WORLD, 3, dims, periods, 1, &cart);
int north, south;
MPI_Cart_shift(cart, 1, 1, &north, &south);         /* Y 방향 이웃 */
MPI_Sendrecv(send_north, M, MPI_DOUBLE, north, 0,
             recv_south, M, MPI_DOUBLE, south, 0, cart, MPI_STATUS_IGNORE);
```

**비교**:
| 항목 | MPI | OpenMP | NCCL/RCCL |
|------|-----|--------|-----------|
| 메모리 모델 | Distributed | Shared | Distributed (GPU) |
| 스케일 | 수만~수십만 프로세스 | 단일 노드 (~수백 스레드) | 다중 노드 GPU |
| API | 명시적 send/recv | 디렉티브 (pragma) | collective 만 |
| 디버깅 | 어렵다 (deadlock/race) | 비교적 쉽다 | 매우 어렵다 |

**표준 인용**: MPI Forum, "MPI: A Message-Passing Interface Standard, Version 4.1" (Nov 2023), §3 (P2P), §5 (Collective), §6 (Groups & Communicators), §11 (One-sided).

**관련**: OpenMP (hybrid MPI+OpenMP), NCCL (GPU collective), [`../algorithms/distributed.md#allreduce`](../algorithms/distributed.md), [`../languages/fortran.md`](../languages/fortran.md) — `coarray Fortran` 은 MPI 의 PGAS 대안.

---

## 2. OpenMP — 공유 메모리 디렉티브 병렬

<a id="openmp-parallel"></a>

**정의**: C/C++/Fortran 에 `#pragma omp` (또는 `!$omp`) 디렉티브를 삽입하여 fork-join 공유 메모리 병렬을 표현하는 표준. OpenMP ARB 가 관리, 현재 **OpenMP 6.0 (2024-11)** (5.2 는 2021). 단일 노드 멀티코어 / NUMA / GPU offload 까지 포괄.

**메커니즘 - 디렉티브**:
- **`#pragma omp parallel`**: 팀 생성, 모든 스레드가 블록 실행
- **`#pragma omp for`** (worksharing): 루프 반복을 스레드에 분배 (`schedule(static|dynamic|guided)`)
- **`#pragma omp sections`**: 독립 코드 블록을 병렬화
- **`#pragma omp task`** (3.0+): irregular / 재귀 작업의 task 큐
- **`#pragma omp taskloop`** (4.5+): 루프를 task 단위로
- **`#pragma omp target`** (4.0+): GPU/가속기 offload
- **`#pragma omp simd`** (4.0+): 벡터화 강제 (AVX-512/SVE)
- **`#pragma omp atomic` / `critical` / `barrier` / `flush`**: 동기화 원시연산

**Data sharing**: `shared`, `private`, `firstprivate`, `lastprivate`, `reduction(+:sum)` — 변수의 가시성 명시.

**Affinity / NUMA 인식 (5.0+)**:
- `OMP_PROC_BIND=close|spread|master` — 스레드를 코어에 고정
- `OMP_PLACES=cores|threads|sockets` — 배치 단위
- `omp_get_place_num()` 으로 현재 위치 조회
- NUMA: **first-touch policy** — 처음 쓰는 스레드의 NUMA 노드에 페이지 할당. `#pragma omp parallel for` 로 초기화하면 자동으로 NUMA-aware 가 된다.

**성능 모델 (Amdahl + parallel overhead)**:
```
T(P) = T_seq × s + T_seq × (1-s) / P + T_overhead(P)
Speedup S(P) = T(1) / T(P)
Efficiency η = S(P) / P
```
디렉티브 진입/종료 비용 ~수 μs — 짧은 루프에는 오히려 손해.

**예시 (행렬-벡터 곱 + reduction, C)**:
```c
#include <omp.h>

void matvec(int N, double **A, double *x, double *y) {
    #pragma omp parallel for schedule(static) default(none) \
            shared(N, A, x, y)
    for (int i = 0; i < N; i++) {
        double sum = 0.0;
        #pragma omp simd reduction(+:sum)        /* 내부 루프 벡터화 */
        for (int j = 0; j < N; j++) sum += A[i][j] * x[j];
        y[i] = sum;
    }
}

double dot(int N, double *a, double *b) {
    double s = 0.0;
    #pragma omp parallel for reduction(+:s)
    for (int i = 0; i < N; i++) s += a[i] * b[i];
    return s;
}
```

**Task 기반 재귀 (피보나치)**:
```c
int fib(int n) {
    if (n < 2) return n;
    int x, y;
    #pragma omp task shared(x) if(n > 20)        /* cutoff 로 overhead 제한 */
    x = fib(n-1);
    #pragma omp task shared(y) if(n > 20)
    y = fib(n-2);
    #pragma omp taskwait
    return x + y;
}
int main() {
    int r;
    #pragma omp parallel
    #pragma omp single
    r = fib(40);
}
```

**GPU offload (OpenMP 5.0+)**:
```c
#pragma omp target teams distribute parallel for \
        map(to:A[0:N], B[0:N]) map(from:C[0:N])
for (int i = 0; i < N; i++) C[i] = A[i] * B[i];
```

**Hybrid MPI + OpenMP** (각 노드에 1 MPI rank + 노드 내부 OpenMP):
- 노드 간 통신은 MPI, 노드 내부는 공유 메모리 → MPI 메시지 수 감소
- `MPI_Init_thread(MPI_THREAD_MULTIPLE)` 또는 `MPI_THREAD_FUNNELED` 로 thread-safety 명시

**비교**:
| 항목 | OpenMP | pthreads | TBB | std::thread |
|------|--------|----------|-----|-------------|
| 추상화 수준 | 높음 (디렉티브) | 매우 낮음 | 중간 (task) | 중간 |
| 학습 곡선 | 완만 | 가파름 | 완만 | 중간 |
| GPU offload | 5.0+ 지원 | 불가 | 불가 | 불가 |
| 성능 튜닝 | schedule 절 | 완전 수동 | 자동 work-stealing | 수동 |

**표준 인용**: OpenMP Architecture Review Board, "OpenMP Application Programming Interface, Version 5.2" (2021-11), §2.6 (parallel), §2.11 (worksharing), §2.13 (task), §2.14 (target). 6.0 (2024-11) 은 `omp_pause_resource_all` 등 신규 API.

**관련**: MPI (hybrid), CUDA/HIP, [`../algorithms/concurrent.md`](../algorithms/concurrent.md), NUMA-aware (#6).

---

## 3. CUDA / HIP HPC 프로파일 — 가속기 고성능 프로그래밍

<a id="cuda-hip-hpc"></a>

**정의**: NVIDIA GPU 를 위한 CUDA (C++/Fortran 확장) 와 AMD GPU 를 위한 HIP (CUDA-portable layer) 로 SIMT(Single Instruction Multiple Thread) 병렬을 구현. **현재 CUDA 12.6 (2024-09) / HIP 6.2**. Top500 상위권은 CUDA(H100/B200) 또는 HIP(MI300X/MI350) 기반.

**메커니즘 - HPC 고급 기능**:
- **Tensor Core** (Volta+/MI200+): 4×4×4 (FP16/BF16/TF32/FP8) 또는 16×8×16 행렬-누산 단위. `wmma::mma_sync` 또는 `cute::gemm` / `cuBLASLt` 로 호출. H100 의 FP8 TC 는 4 PFLOPS/GPU.
- **Shared Memory**: SM 당 ~228 KB (H100), L1 캐시와 통합 분할. `__shared__` 로 선언. tile 단위 GEMM·stencil 의 핵심. Bank conflict (32-way) 회피 필수.
- **Warp Shuffle** (`__shfl_sync` 계열): warp(32 스레드) 내에서 레지스터 간 직접 교환 — shared mem 없이 reduce/scan. butterfly·broadcast·xor 변형.
- **Cooperative Groups** (CUDA 9+): `cg::thread_block`, `cg::grid_group`, `cg::coalesced_group`, `cg::multi_grid_group` — warp/block/grid 수준 동기화 일관 API. Grid-wide sync (`cg::grid_group::sync()`) 는 `cudaLaunchCooperativeKernel` 필요.
- **NVSHMEM** (NVIDIA OpenSHMEM): GPU 메모리를 다중 노드 PGAS 로. `nvshmem_put` / `nvshmem_get` 으로 host CPU 개입 없이 GPU 간 직접 통신. NVLink/NVSwitch + InfiniBand GPUDirect RDMA.
- **CUDA Graphs**: kernel/copy/event 의 DAG 를 미리 빌드해 launch overhead (~5 μs/kernel) 제거 — 작은 kernel 수천 개 시 5~10× 개선.
- **MIG (Multi-Instance GPU)**: A100/H100/B200 을 7 개 분할 (각 ~10 GB + 14 SM) — 멀티 테넌트 격리.

**성능 모델 (Roofline)**:
```
Performance(FLOPS) = min(Peak_compute, Peak_bandwidth × Arithmetic_Intensity)
Arithmetic Intensity AI = FLOPs / Bytes_DRAM
H100 SXM5: Peak_compute=67 TFLOPS(FP64), 989 TFLOPS(TF32), 1979(FP16/BF16), 3958(FP8)
          Peak_bandwidth=3.35 TB/s (HBM3)
GEMM (n=4096): AI ≈ n/2 ≈ 2048 → compute-bound
SpMV: AI ≈ 0.25 → 항상 bandwidth-bound
```

**예시 (Tensor Core GEMM 일부 — CUDA C++)**:
```cuda
#include <cuda_fp16.h>
#include <mma.h>
using namespace nvcuda;

__global__ void gemm_tc(const half *A, const half *B, float *C, int N) {
    /* 16×16×16 fragment — Tensor Core 한 번에 4096 MAC */
    wmma::fragment<wmma::matrix_a, 16,16,16, half, wmma::row_major> a_frag;
    wmma::fragment<wmma::matrix_b, 16,16,16, half, wmma::col_major> b_frag;
    wmma::fragment<wmma::accumulator, 16,16,16, float> c_frag;
    wmma::fill_fragment(c_frag, 0.0f);

    int warpM = (blockIdx.x * blockDim.x + threadIdx.x) / 32;
    int warpN = blockIdx.y * blockDim.y + threadIdx.y;

    for (int k = 0; k < N; k += 16) {
        wmma::load_matrix_sync(a_frag, A + warpM*16*N + k, N);
        wmma::load_matrix_sync(b_frag, B + k*N + warpN*16, N);
        wmma::mma_sync(c_frag, a_frag, b_frag, c_frag);  /* TC 발사 */
    }
    wmma::store_matrix_sync(C + warpM*16*N + warpN*16, c_frag, N, wmma::mem_row_major);
}
```

**Warp shuffle reduce (block 내부 합)**:
```cuda
__inline__ __device__ float warp_reduce_sum(float v) {
    for (int offset = 16; offset > 0; offset /= 2)
        v += __shfl_down_sync(0xffffffff, v, offset);  /* butterfly */
    return v;
}
__global__ void reduce_kernel(const float *in, float *out, int N) {
    float v = (threadIdx.x + blockIdx.x*blockDim.x < N) ? in[threadIdx.x + blockIdx.x*blockDim.x] : 0;
    v = warp_reduce_sum(v);
    if ((threadIdx.x & 31) == 0) atomicAdd(out, v);
}
```

**HIP 포팅 (자동 — `hipify-perl` / `hipify-clang`)**:
```cpp
// CUDA: cudaMalloc(&d, N*sizeof(float));
// HIP:  hipMalloc(&d, N*sizeof(float));
// CUDA: kernel<<<grid,block>>>(args);
// HIP:  hipLaunchKernelGGL(kernel, grid, block, 0, 0, args);
```
대부분 1:1 매핑 — AMD MI300X/MI355X 에서 동일 코드 동작.

**비교**:
| 항목 | CUDA | HIP | OpenCL | SYCL/oneAPI |
|------|------|-----|--------|-------------|
| 벤더 | NVIDIA 전용 | AMD + NVIDIA | 다중 (사양뿐) | Intel + 다중 |
| 도구 성숙도 | 최고 (nsight/cuobjdump) | 중간 (rocprof) | 노쇠 | 성장 중 |
| 라이브러리 | cuBLAS/cuDNN/cuFFT | rocBLAS/MIOpen/rocFFT | clBLAS (방치) | oneMKL/oneDNN |
| HPC 점유 | 80%+ | 15%+ (증가) | 미미 | 5%+ |

**표준 인용**: NVIDIA, "CUDA C++ Programming Guide" v12.6 (2024-09), §5.4 (Memory Hierarchy), §7 (C++ Language Extensions), §C (Tensor Cores via WMMA). AMD, "HIP Programming Guide" v6.2. OpenSHMEM Specification 1.5 (2020).

**관련**: [`../languages/cuda-c-cplusplus.md`](../languages/cuda-c-cplusplus.md), BLAS/LAPACK (#5), Roofline (#6), [`../algorithms/concurrent.md`](../algorithms/concurrent.md).

---

## 4. Slurm Workload Manager — HPC 자원 스케줄러

<a id="slurm-workload-manager"></a>

**정의**: Top500 의 60% 이상이 사용하는 오픈소스 batch 스케줄러. SchedMD 가 유지보수, **현재 Slurm 24.05 (2024-05)**. 노드/소켓/코어/GRES(GPU/FPGA) 단위 자원 추상화·우선순위·공정 공유·체크포인트 제공.

**메커니즘 - 핵심 객체**:
- **Cluster**: Slurm 인스턴스 단위
- **Partition**: 노드 그룹 (예: `gpu`, `bigmem`, `debug`) — 시간 제한·우선순위·접근 권한 분리
- **QoS (Quality of Service)**: 우선순위·자원 한도·과금 정책 (예: `normal`, `premium`, `low`)
- **Job**: `sbatch` 로 제출, `JobID` 부여, 종료까지 상태 추적
- **Job Array**: `--array=0-99%10` — 100 개 작업, 동시 10 개만 실행
- **GRES (Generic Resource)**: GPU/FPGA/MIC 표현. `--gres=gpu:a100:4` — A100 4 개 요청
- **Accounting (sacct/sreport)**: 사용량 추적·과금
- **Backfill scheduler**: 우선순위 큐 + EASY backfill — 작은 작업을 큐 앞으로 끼워넣어 활용도 ↑

**주요 명령**:
- `sbatch script.sh` — batch 제출
- `srun -n 64 ./app` — 즉시 실행 (작업 내부의 step 도 srun)
- `squeue -u $USER` — 대기열
- `scancel <jobid>` — 취소
- `sinfo` — partition/노드 상태
- `sacct -j <jobid>` — 완료 후 사용량
- `scontrol show job <jobid>` — 상세

**예시 (sbatch 스크립트 — 4 노드 × 4 GPU × 64 CPU)**:
```bash
#!/bin/bash
#SBATCH --job-name=llm-train
#SBATCH --partition=gpu
#SBATCH --qos=normal
#SBATCH --nodes=4                       # 노드 수
#SBATCH --ntasks-per-node=4             # 노드당 MPI rank = GPU 수
#SBATCH --cpus-per-task=16              # rank 당 OpenMP 스레드 = 64/4
#SBATCH --gres=gpu:a100:4               # 노드당 A100 4 개
#SBATCH --mem=480G
#SBATCH --time=12:00:00                 # walltime hh:mm:ss
#SBATCH --output=logs/%x-%j.out         # %x=job-name, %j=JobID
#SBATCH --error=logs/%x-%j.err
#SBATCH --mail-user=user@lab.org
#SBATCH --mail-type=END,FAIL

module load cuda/12.6 openmpi/5.0 nccl/2.22
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export NCCL_DEBUG=INFO
export NCCL_IB_HCA=mlx5_0,mlx5_1        # InfiniBand HCA 선택

# srun 가 자동으로 MPI rank ↔ GPU ↔ CPU bind
srun --cpu-bind=cores --gpu-bind=closest \
     python train.py --batch-size 64 --gradient-accumulation 8
```

**Job array (parameter sweep)**:
```bash
#SBATCH --array=0-99%20                 # 100 작업, 동시 20 개
PARAMS=(0.001 0.003 0.01 0.03 ... )    # 100 개 학습률
python train.py --lr ${PARAMS[$SLURM_ARRAY_TASK_ID]}
```

**Dependency (DAG 형태)**:
```bash
JID1=$(sbatch --parsable preprocess.sh)
JID2=$(sbatch --parsable --dependency=afterok:$JID1 train.sh)
sbatch --dependency=afterok:$JID2 evaluate.sh
```

**GPU 토폴로지 인식 (NVLink/NUMA 최적)**:
```bash
srun --cpu-bind=verbose,cores --gpu-bind=closest \
     ./app
# closest = GPU 와 같은 PCIe root complex 의 CPU 코어에 bind
```

**비교**:
| 스케줄러 | 강점 | 약점 |
|---------|------|------|
| **Slurm** | HPC 표준, GRES, plug-in 확장 | 학습 곡선, GUI 빈약 |
| PBS Pro | 오래된 HPC 사이트, 안정 | 라이선스, 커뮤니티 축소 |
| LSF | 엔터프라이즈, GUI | IBM 의존, 가격 |
| Kubernetes Volcano | 클라우드 통합 | gang scheduling 후발, HPC 노드 인식 약함 |

**표준 인용**: SchedMD, "Slurm Workload Manager Documentation" v24.05 (2024), `sbatch(1)`, `srun(1)`, `scontrol(1)`. Yoo, Jette & Grondona, "SLURM: Simple Linux Utility for Resource Management" (2003, JSSPP).

**관련**: MPI (#1), CUDA/HIP (#3), [`../algorithms/distributed.md`](../algorithms/distributed.md) — gang scheduling, [`../principles/performance-metrics.md`](../principles/performance-metrics.md) — utilization.

---

## 5. BLAS / LAPACK / ScaLAPACK — 표준 선형대수 스택

<a id="blas-lapack-scalapack"></a>

**정의**: HPC 수치 라이브러리의 사실상 표준. **BLAS** (Basic Linear Algebra Subprograms, Lawson et al. 1979) — 벡터/행렬 기본 연산. **LAPACK** (Anderson et al. 1992) — BLAS 위의 솔버 (LU/QR/SVD/Eigen). **ScaLAPACK** (Choi et al. 1996) — 분산 메모리 확장. BLAS Reference 4.1 (2023) / LAPACK 3.12 (2023) / ScaLAPACK 2.2 (2022).

**메커니즘 - BLAS 3 단계**:
| Level | 연산 | 예시 | AI (산술강도) | 성능 특성 |
|-------|------|------|---------------|----------|
| **Level 1** | 벡터-벡터 (O(n)) | `daxpy`: y = αx + y, `ddot` | ~0.5 FLOP/byte | Memory-bound |
| **Level 2** | 행렬-벡터 (O(n²)) | `dgemv`: y = αAx + βy | ~1 FLOP/byte | Memory-bound |
| **Level 3** | 행렬-행렬 (O(n³)) | `dgemm`: C = αAB + βC | ~n/2 FLOP/byte | **Compute-bound** |

핵심 통찰: Level 3 만이 캐시·Tensor Core 를 포화시킬 수 있다. 모든 고성능 알고리즘(LU/QR/SVD)이 **블록화**되어 내부적으로 GEMM 을 호출하는 이유.

**LAPACK 솔버**:
- **LU 분해**: `dgetrf` (PA = LU, partial pivoting), `dgesv` (LU + solve)
- **QR 분해**: `dgeqrf` (Householder), `dgels` (최소제곱)
- **SVD**: `dgesvd` (divide & conquer 또는 QR iteration), `dgesdd` (더 빠름, 메모리 더 씀)
- **Symmetric Eigen**: `dsyevd` (Cuppen divide & conquer)
- **Cholesky**: `dpotrf` (대칭 양정치)

**ScaLAPACK (PBLAS + BLACS + LAPACK)**:
- **BLACS**: 프로세스 격자(2D mesh) 추상화. `Cblacs_gridinit`.
- **PBLAS**: parallel BLAS — `pdgemm`, `pdgemv`.
- **분산 행렬 레이아웃**: **2D block-cyclic** — `MB × NB` 블록 단위로 `P × Q` 프로세스 격자에 순환 분배. 부하 균형 + 통신 패턴 균형.
- **솔버**: `pdgesv`, `pdgeqrf`, `pdsyevd` — LAPACK API 와 1:1 대응.

**구현체 비교**:
| 구현 | 벤더 | 타겟 | 최대 GEMM 효율 |
|------|------|------|-------|
| **Reference BLAS** | netlib | 검증용 | ~5% peak (참고용) |
| **OpenBLAS** | 오픈소스 (GotoBLAS 계승) | CPU (x86/ARM/Power) | ~90% peak |
| **Intel MKL (oneMKL)** | Intel | Intel CPU + GPU | ~95% peak (AVX-512/AMX) |
| **AOCL BLIS** | AMD | AMD CPU (Zen) | ~92% peak |
| **Arm Performance Libraries** | Arm | NEON/SVE/SVE2 | ~90% peak |
| **cuBLAS / cuBLASLt** | NVIDIA | NVIDIA GPU | ~95% peak (TC 활용) |
| **rocBLAS / hipBLAS** | AMD | AMD GPU (MI) | ~90% peak |

**예시 (LAPACKE C 인터페이스 — LU + solve)**:
```c
#include <lapacke.h>
#include <cblas.h>

int main(void) {
    int N = 1024, NRHS = 1;
    double *A = malloc(N*N*sizeof(double));
    double *b = malloc(N*sizeof(double));
    int *ipiv = malloc(N*sizeof(int));
    /* ... A, b 초기화 ... */

    /* LAPACK: A = P·L·U 후 Ax=b 풀이 */
    int info = LAPACKE_dgesv(LAPACK_ROW_MAJOR, N, NRHS, A, N, ipiv, b, NRHS);
    if (info != 0) { fprintf(stderr, "dgesv info=%d\n", info); return 1; }

    /* BLAS Level 3: C = A·B (검증용) */
    double *C = calloc(N*N, sizeof(double));
    cblas_dgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans,
                N, N, N, 1.0, A, N, A, N, 0.0, C, N);
    /* MKL 사용 시: -lmkl_intel_lp64 -lmkl_intel_thread -lmkl_core -liomp5 */
}
```

**예시 (ScaLAPACK Fortran — 분산 LU)**:
```fortran
! 2D block-cyclic 분포
CALL BLACS_GET( -1, 0, ICTXT )
CALL BLACS_GRIDINIT( ICTXT, 'Row-major', NPROW, NPCOL )
CALL BLACS_GRIDINFO( ICTXT, NPROW, NPCOL, MYROW, MYCOL )

! 로컬 블록 크기
LOCROW = NUMROC( N, MB, MYROW, 0, NPROW )
LOCCOL = NUMROC( N, NB, MYCOL, 0, NPCOL )
CALL DESCINIT( DESCA, N, N, MB, NB, 0, 0, ICTXT, LOCROW, INFO )

! 분산 LU 분해
CALL PDGETRF( N, N, A, 1, 1, DESCA, IPIV, INFO )
! 해 구하기
CALL PDGETRS( 'N', N, NRHS, A, 1, 1, DESCA, IPIV, B, 1, 1, DESCB, INFO )

CALL BLACS_GRIDEXIT( ICTXT )
CALL BLACS_EXIT( 0 )
```

**비교 — 행렬 계산 라이브러리 스택**:
| 계층 | API | 분산? | 가속기? |
|------|-----|------|---------|
| BLAS | C/Fortran | ✗ | cuBLAS/rocBLAS |
| LAPACK | C/Fortran | ✗ | cuSOLVER/rocSOLVER |
| **ScaLAPACK** | Fortran | ✓ (MPI) | SLATE 가 후속 |
| **SLATE** (2018+) | C++ | ✓ (MPI+OpenMP+CUDA) | ✓ ScaLAPACK 후계 |
| ELPA | Fortran | ✓ | 대칭 eigen 특화 |
| MAGMA | C/Fortran | ✗ (단일 노드) | ✓ multi-GPU |
| PETSc/Trilinos | C/C++ | ✓ | ✓ Sparse 위주 |

**표준 인용**: Lawson, Hanson, Kincaid, Krogh, "Basic Linear Algebra Subprograms for Fortran Usage" (1979, ACM TOMS). Anderson et al., "LAPACK Users' Guide", 3rd ed. (1999, SIAM). Choi, Demmel, Dhillon, Dongarra et al., "ScaLAPACK: A Portable Linear Algebra Library", (1996, ACM/IEEE SC). BLAS Forum, "BLAS Reference Manual" v4.1 (2023).

**관련**: [`../algorithms/math.md`](../algorithms/math.md) — GEMM/LU/QR/SVD 알고리즘, MPI (#1), CUDA/HIP (#3), Tensor Core, Roofline (#6).

---

## 6. NUMA-aware Programming + Roofline Model — 메모리 토폴로지·성능 한계 분석

<a id="numa-roofline-model"></a>

**정의**: 현대 다중 소켓 / GPU 노드는 **비균일 메모리 접근(NUMA)** 구조 — 동일 노드라도 메모리 위치에 따라 지연·대역폭이 달라진다. Roofline 모델은 알고리즘의 성능 상한을 **연산 능력 vs 메모리 대역폭** 두 축으로 시각화하여 최적화 우선순위를 결정한다. Williams, Waterman, Patterson, "Roofline: An Insightful Visual Performance Model" (2009, CACM).

**NUMA 메커니즘**:
- **NUMA 노드**: CPU 소켓(또는 chiplet) + 직결 메모리 컨트롤러. AMD EPYC 9654 (Genoa) 는 NPS=4 시 노드당 24 코어 × 4 NUMA 노드.
- **Local vs Remote 접근**: 같은 노드 ≈ 100 ns / 100 GB/s, 다른 노드 = 1.5~3× 느림 (~150~300 ns).
- **First-touch policy** (Linux 기본): `malloc` 은 가상주소만 잡고, 처음 **쓰는** 스레드의 NUMA 노드에 물리 페이지 할당. 직렬 초기화 → 한 노드에 몰림 → remote access 폭발.
- **hwloc** (Portable Hardware Locality): NUMA/캐시/PCIe 토폴로지 표준 라이브러리. `lstopo` 로 시각화.
- **`numactl` / `libnuma`**: 정책 제어. `numactl --interleave=all` (라운드로빈), `--cpunodebind=0 --membind=0` (단일 노드 고정).
- **GPU 의 NUMA**: GPU↔CPU 는 PCIe root complex 별 NUMA 도메인. `nvidia-smi topo -m` 으로 확인. NCCL 은 자동 인식.

**NUMA 최적화 패턴**:
- **first-touch 병렬 초기화**: 사용할 스레드와 동일한 패턴으로 `#pragma omp parallel for` 로 초기화
- **소켓당 1 MPI rank** (hybrid): rank 간 분리, rank 내부는 OpenMP — remote NUMA 제거
- **인터리브 (작업 패턴 예측 불가)**: `numactl --interleave=all` — 평균 대역폭 ↑, peak 대역폭 ↓
- **HBM (High Bandwidth Memory) 단계**: Intel Xeon Max (HBM2e) / NVIDIA Grace Hopper — HBM 우선 사용 페이지 마이그레이션

**Roofline 모델**:
```
Performance(AI) = min( π,  β × AI )         # FLOPS
π = peak compute (FLOPS)
β = peak memory bandwidth (Bytes/s)
AI = Arithmetic Intensity (FLOPs / DRAM Bytes)

교차점 (ridge point):  AI_ridge = π / β
AI < AI_ridge: memory-bound  →  대역폭 개선 우선
AI > AI_ridge: compute-bound →  벡터화·Tensor Core 우선
```

**참고치 (2024 기준)**:
| 시스템 | π (FP64 TFLOPS) | β (TB/s) | AI_ridge | 대표 알고리즘 |
|--------|----------------|----------|----------|--------------|
| Intel Xeon 8480+ (56c) | 3.2 | 0.31 (DDR5) | ~10 | GEMM (n>256) compute-bound, SpMV memory-bound |
| AMD EPYC 9654 (96c) | 5.4 | 0.46 | ~12 | 동상 |
| NVIDIA H100 SXM5 | 67 (FP64) / 989 (TF32) | 3.35 (HBM3) | ~20 (FP64) / ~295 (TF32) | TF32 GEMM 은 매우 큰 n 필요 |
| AMD MI300X | 81 (FP64) | 5.3 (HBM3) | ~15 (FP64) | 광대역 HBM 으로 ridge ↓ |
| NVIDIA Grace Hopper (GH200) | 67 | 4.0 (HBM3e) + 0.5 (LPDDR5X NVLink-C2C) | 통합 메모리로 AI 정의 확장 |

**Roofline 으로 알고리즘 진단**:
- **GEMM (dgemm)**: AI = n/2 → n=64 면 32, n=1024 면 512. GPU 에서도 항상 compute-bound.
- **SpMV (희소 행렬-벡터)**: AI ≈ 0.25 → **항상 memory-bound**. 캐시 활용 (CSR/ELLPACK) 만 가능.
- **Stencil (3D 7-point)**: AI ≈ 0.5~2 → memory-bound. 시간 블록화(temporal blocking) 로 AI 증가 가능.
- **N-body (직접 합)**: AI ≈ O(N) → compute-bound. FMM 으로 O(N) 알고리즘 변경.
- **FFT (cuFFT)**: AI ≈ O(log N) → memory-bound on small, compute-bound on large.

**측정 도구**:
- **Intel Advisor**: 자동 Roofline 차트 생성 (`advixe-cl --collect=roofline`)
- **NVIDIA Nsight Compute**: `ncu --set=full --metrics=...` — SM efficiency, achieved occupancy, DRAM throughput, achieved/peak %
- **AMD ROCm rocprof**: 동등 기능
- **likwid-perfctr**: CPU PMU 카운터 직접 측정
- **PAPI**: 표준 PMU API

**예시 (NUMA-aware first-touch + Roofline 검증, C + OpenMP)**:
```c
#include <omp.h>
#include <numa.h>
#include <stdio.h>

void init_aligned(double *a, size_t N) {
    /* 잘못된 방법: 직렬 초기화 → 노드 0 에 몰림
       for (size_t i = 0; i < N; i++) a[i] = 0.0;  */

    /* 올바른 방법: 사용할 패턴과 동일하게 병렬 초기화 (first-touch) */
    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < N; i++) a[i] = 0.0;
}

double daxpy_bench(double *y, const double *x, double a, size_t N) {
    double t0 = omp_get_wtime();
    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < N; i++) y[i] = a*x[i] + y[i];
    double t = omp_get_wtime() - t0;

    /* daxpy: 2 FLOPs/iter, 24 Bytes/iter (16 read + 8 write)
       AI = 2/24 = 0.083  →  심하게 memory-bound */
    double flops = 2.0 * N / t;
    double bw_GBps = 24.0 * N / t / 1e9;
    printf("DAXPY: %.2f GFLOPS, %.2f GB/s\n", flops/1e9, bw_GBps);
    return bw_GBps;
}

int main(void) {
    if (numa_available() < 0) { fprintf(stderr, "no NUMA\n"); return 1; }
    size_t N = 1L << 28;        /* 2 GB per array */
    double *x = numa_alloc_interleaved(N*sizeof(double));   /* 라운드로빈 */
    double *y = numa_alloc_interleaved(N*sizeof(double));
    init_aligned(x, N); init_aligned(y, N);
    for (int trial = 0; trial < 5; trial++) daxpy_bench(y, x, 2.0, N);
    numa_free(x, N*sizeof(double)); numa_free(y, N*sizeof(double));
}
```
컴파일: `gcc -fopenmp -lnuma -O3 -march=native daxpy.c` / 실행: `numactl --cpunodebind=0,1 --membind=0,1 ./a.out`

**비교 — 메모리 시스템 모델**:
| 모델 | 추상화 | 강점 | 약점 |
|------|--------|------|------|
| **UMA** | 단일 균일 메모리 | 단순 | 다중 소켓 확장 불가 |
| **NUMA** | 노드별 메모리 | 확장성 | 프로그래머 인식 필요 |
| **CC-NUMA** | + 캐시 일관성 (현대 x86) | 투명 | 일관성 비용 |
| **COMA** | 캐시-only 메모리 | 자동 마이그레이션 | 미상용화 |
| **PGAS** | 전역 주소 공간 | 프로그래밍 단순 | 컴파일러 의존 |

**표준 인용**: Williams, Waterman, Patterson, "Roofline: An Insightful Visual Performance Model for Multicore Architectures" (CACM 52(4), 2009). Lameter, "NUMA (Non-Uniform Memory Access): An Overview" (ACM Queue 11(7), 2013). Goglin et al., "hwloc: A Generic Framework for Managing Hardware Affinities in HPC Applications" (PDP 2010). Intel, "Roofline Performance Model" white paper (2022).

**관련**: OpenMP (#2) — first-touch, MPI (#1) — hybrid, BLAS (#5) — AI 분석 대상, [`../principles/performance-metrics.md`](../principles/performance-metrics.md), [`../algorithms/concurrent.md`](../algorithms/concurrent.md).

---

## 카탈로그 요약

| ID | 패턴 | 핵심 개념 | 표준/출처 |
|----|------|----------|----------|
| `hpc-mpi` | MPI | P2P / Collective / Non-blocking / RMA / Topology | MPI Forum 4.1 (2023) |
| `openmp-parallel` | OpenMP | 디렉티브 / Task / SIMD / Target / Affinity | OpenMP ARB 5.2 (2021) |
| `cuda-hip-hpc` | CUDA/HIP HPC | Tensor Core / Shared Mem / Warp Shuffle / Coop Groups / NVSHMEM | NVIDIA CUDA 12.6, AMD HIP 6.2 |
| `slurm-workload-manager` | Slurm | Partition / QoS / Job Array / GRES / sbatch | SchedMD Slurm 24.05 |
| `blas-lapack-scalapack` | BLAS/LAPACK/ScaLAPACK | Level 1/2/3 / 2D block-cyclic / 분산 솔버 | BLAS 4.1 / LAPACK 3.12 / ScaLAPACK 2.2 |
| `numa-roofline-model` | NUMA + Roofline | first-touch / hwloc / AI / ridge point | Williams 2009, Lameter 2013 |
