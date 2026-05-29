# 임베디드/RTOS 패턴 (Embedded & Real-Time Patterns)

자원 제약(메모리 KB 단위, MCU 단일 코어)·실시간 deadline(WCET) 가 있는 임베디드/IoT/실시간 시스템 10 패턴. 일반 서버/모바일 패턴과 달리 **하드 deadline / 동적 메모리 금지 / 인터럽트 우선** 환경에서 검증된 표준.

**적용 영역**: MCU 펌웨어, RTOS(FreeRTOS / Zephyr / VxWorks / QNX), 자동차 ECU(AUTOSAR), 항공/방산(DO-178C), 의료기기(IEC 62304), 산업제어(IEC 61508).

**관련 카탈로그**:
- [concurrency.md](concurrency.md) — Producer-Consumer, Reactor (일반 동시성)
- [reliability.md](reliability.md) — Bulkhead, Timeout (장애 격리)
- [`../algorithms/concurrent.md`](../algorithms/concurrent.md) — CAS, RCU, Memory Barriers
- [`../security/security-mobile.md`](../security/security-mobile.md) — 임베디드 보안은 일부 모바일 보안과 겹침

---

## 1. Rate Monotonic Scheduling (RMS) — 단조 비율 스케줄링

<a id="rate-monotonic-scheduling"></a>

**목적**: 주기적 태스크에 **정적 우선순위**를 부여하되 짧은 주기일수록 높은 우선순위를 주어 모든 deadline 을 보장합니다. Liu & Layland 1973 의 고전 이론.

**특징/이론**:
- 정적 우선순위 (priority = 1 / period) — 컴파일 타임 결정
- 선점형 (preemptive) 스케줄러 필요
- 모든 태스크가 주기적·독립적·deadline = period 가정
- Utilization bound (Liu & Layland):

```
U = Σ (C_i / T_i)  ≤  n × (2^(1/n) − 1)
n=1: 1.00   n=2: 0.828   n=3: 0.779   n→∞: ln 2 ≈ 0.693
```

**장점**:
- 컴파일 타임 schedulability 분석 가능 (정적 증명)
- 구현 단순 (RTOS 의 fixed-priority 만 있으면 충분)
- 안전인증(DO-178C, ISO 26262) 친화적

**단점**:
- Utilization 상한 ~69% (모든 deadline 보장 시 평균)
- 비주기적·산발(sporadic) 태스크에 부적합 → polling server / sporadic server 보강 필요
- 우선순위 역전(priority inversion) — Priority Ceiling / Priority Inheritance 로 해결

**활용 예시**:
- 자동차 ECU 의 100ms / 10ms / 1ms 태스크 분리 (AUTOSAR OS)
- 항공기 FBW(Fly-By-Wire) 제어 루프
- 산업용 PLC 사이클

**C 예제** (FreeRTOS):
```c
#include "FreeRTOS.h"
#include "task.h"

/* 주기가 짧을수록 우선순위 높음 — RMS 규칙 */
#define PRIO_1MS    (configMAX_PRIORITIES - 1)   /* 가장 높음 */
#define PRIO_10MS   (configMAX_PRIORITIES - 2)
#define PRIO_100MS  (configMAX_PRIORITIES - 3)

static void task_control_1ms(void *pv) {
    TickType_t last = xTaskGetTickCount();
    for (;;) {
        read_sensor(); compute_pid(); write_actuator();
        vTaskDelayUntil(&last, pdMS_TO_TICKS(1));   /* 정확한 주기 */
    }
}
static void task_telemetry_100ms(void *pv) {
    TickType_t last = xTaskGetTickCount();
    for (;;) { send_telemetry(); vTaskDelayUntil(&last, pdMS_TO_TICKS(100)); }
}

void app_main(void) {
    xTaskCreate(task_control_1ms,    "ctrl", 256, NULL, PRIO_1MS,   NULL);
    xTaskCreate(task_telemetry_100ms,"tlm",  256, NULL, PRIO_100MS, NULL);
    vTaskStartScheduler();
}
```

**관련 패턴**: Earliest Deadline First, WCET 분석, Time-Triggered Architecture

---

## 2. Earliest Deadline First (EDF) — 최단 마감 우선

<a id="earliest-deadline-first"></a>

**목적**: 매 스케줄링 시점에 **절대 deadline 이 가장 가까운** 태스크를 실행하여 단일 프로세서 환경에서 이론적 최대 utilization(100%) 을 달성합니다.

**특징/이론**:
- 동적 우선순위 — 매번 deadline 비교
- 단일 프로세서 최적성 (Liu & Layland): `U ≤ 1` 이면 모든 deadline 보장
- 멀티프로세서에서는 최적성 깨짐 (Dhall's effect)
- Overload 시 도미노 효과 (한 deadline miss → 연쇄 miss)

**장점**:
- 단일 코어에서 100% utilization 까지 schedulability 보장
- 주기·산발 혼합 태스크에 동일 알고리즘 적용
- 분석 단순: U ≤ 1 단 한 조건

**단점**:
- 컨텍스트 스위치 시마다 deadline 재계산 — 오버헤드 증가
- Overload 시 도미노 효과 — admission control 필요
- 우선순위 역전 처리 복잡 (Stack Resource Protocol 필요)
- 안전인증 친화도 낮음 (정적 분석 도구 빈약)

**활용 예시**:
- Linux SCHED_DEADLINE (Constant Bandwidth Server)
- 멀티미디어 스트리밍 deadline 보장
- 무인기 / 로봇 제어 (동적 환경)

**C 예제** (Linux SCHED_DEADLINE):
```c
#include <sched.h>
#include <linux/sched/types.h>
#include <unistd.h>
#include <sys/syscall.h>

/* Linux 의 EDF 스케줄러 — Constant Bandwidth Server 기반 */
static int sched_setattr(pid_t pid, const struct sched_attr *attr, unsigned flags) {
    return syscall(SYS_sched_setattr, pid, attr, flags);
}

int set_edf_task(uint64_t runtime_ns, uint64_t deadline_ns, uint64_t period_ns) {
    struct sched_attr attr = {0};
    attr.size = sizeof(attr);
    attr.sched_policy   = SCHED_DEADLINE;
    attr.sched_runtime  = runtime_ns;   /* 보장 실행 시간 */
    attr.sched_deadline = deadline_ns;  /* 상대 deadline */
    attr.sched_period   = period_ns;    /* 주기 */
    return sched_setattr(0, &attr, 0);  /* 현재 태스크에 적용 */
}
/* 예: 1ms 실행, 5ms deadline, 10ms 주기 */
/* set_edf_task(1000000ULL, 5000000ULL, 10000000ULL); */
```

**관련 패턴**: Rate Monotonic Scheduling, WCET 분석

---

## 3. Worst-Case Execution Time (WCET) 분석

<a id="wcet-analysis"></a>

**목적**: 코드 경로의 **최악 실행 시간 상한** 을 분석/측정하여 실시간 스케줄러의 schedulability 증명에 사용합니다. Deadline 보장의 전제 조건.

**특징/이론**:
- 정적 분석 (static): 어셈블리 + 캐시/파이프라인 모델 → 안전한 상한, 단 비관적(pessimistic)
- 측정 기반 (measurement): 실제 실행 측정 → 정확하지만 cover 못한 경로 위험
- Hybrid: 정적 + 측정 결합 (산업 표준 — aiT, RapiTime, Bound-T)
- **금지 패턴**: 동적 메모리, 재귀(unbounded), interrupt-disable 임의 사용

```
필수 조건:
  for / while → 반복 횟수 상한 명시 (loop bound annotation)
  malloc / free → 금지 (또는 사전 할당 pool 만)
  재귀 → tail recursion 또는 변환
```

**장점**:
- 실시간 보장의 수학적 근거 제공
- 안전인증(DO-178C, ISO 26262 ASIL-D) 요구 충족
- 캐시/파이프라인 효과 사전 식별

**단점**:
- 정적 분석은 30~300% 비관적 (over-approximation)
- 최신 CPU(out-of-order, branch predictor) 모델링 어려움
- 도구 비용 고가 (aiT 등 상용)

**활용 예시**:
- 자동차 ASIL-D 안전 펑션 (브레이크, ESP)
- 항공기 FCC(Flight Control Computer)
- 의료기기 IEC 62304 Class C

**C 예제** (정적 분석 어노테이션 + 측정):
```c
#include <stdint.h>
#include "cycle_counter.h"   /* ARM DWT_CYCCNT 등 */

/* 정적 분석기용 loop bound annotation (aiT/Bound-T 형식) */
/*@ loop_bound 0..N */
int8_t pid_compute(const int16_t *errors, uint16_t N) {
    int32_t sum = 0;
    /* @ loop_bound 0..N */
    for (uint16_t i = 0; i < N; i++) {      /* N 은 컴파일 타임 상수여야 함 */
        sum += errors[i];
    }
    return (int8_t)(sum / N);
}

/* 측정 기반 WCET — cycle counter 로 envelope 수집 */
uint32_t measure_wcet(void) {
    static uint32_t worst = 0;
    int16_t buf[32];
    uint32_t start = DWT->CYCCNT;
    (void)pid_compute(buf, 32);
    uint32_t elapsed = DWT->CYCCNT - start;
    if (elapsed > worst) worst = elapsed;
    return worst;
}
```

**관련 패턴**: Rate Monotonic Scheduling, Time-Triggered Architecture, Memory Pool

---

## 4. Time-Triggered Architecture (TTA) — 시간 트리거 아키텍처

<a id="time-triggered-architecture"></a>

**목적**: 이벤트 발생 대신 **글로벌 시간표(static schedule)** 에 따라 태스크/통신을 트리거하여 결정론적 동작·증명 가능한 안전성을 확보합니다. Kopetz 의 분류.

**특징/이론**:
- 모든 활동이 사전 정의된 시간 슬롯에 실행 (offline scheduling)
- 분산 노드 간 클럭 동기화 필수 (precision time protocol)
- 네트워크: TTP(Time-Triggered Protocol), TTEthernet, FlexRay
- Event-Triggered 와 대비: ET 는 인터럽트 기반, TT 는 타이머 기반

**장점**:
- 완벽한 결정론 (jitter 최소, deadline 증명 가능)
- 분산 시스템에서 합성성(composability) 보장
- 안전인증 친화적 (행동 예측 가능)

**단점**:
- 유연성 부족 (산발적 이벤트 처리 어려움)
- 클럭 동기화 인프라 필요
- 슬롯 할당 비효율 (utilization 낮음)

**활용 예시**:
- 항공기 IMA(Integrated Modular Avionics) — ARINC 653
- 자동차 X-by-Wire (FlexRay)
- 산업용 EtherCAT, PROFINET IRT

**C 예제** (Major / Minor Cycle 정적 스케줄):
```c
#include <stdint.h>
#include "hw_timer.h"

typedef void (*task_fn_t)(void);

/* Minor cycle = 10ms, Major cycle = 100ms (10 slot) */
static const task_fn_t schedule[10] = {
    task_sensor_read,     /* slot 0:  0ms  */
    task_pid_compute,     /* slot 1: 10ms  */
    task_actuator_write,  /* slot 2: 20ms  */
    task_sensor_read,     /* slot 3: 30ms  */
    task_pid_compute,     /* slot 4: 40ms  */
    task_actuator_write,  /* slot 5: 50ms  */
    task_logging,         /* slot 6: 60ms — 100ms 주기 */
    task_diagnostics,     /* slot 7: 70ms  */
    task_idle,            /* slot 8: 80ms  */
    task_idle             /* slot 9: 90ms — 슬랙 */
};

static volatile uint8_t slot_idx = 0;

/* 10ms 주기 하드웨어 타이머 ISR — 결정론적 트리거 */
void timer_isr_10ms(void) {
    schedule[slot_idx]();              /* 슬롯의 태스크 실행 */
    slot_idx = (slot_idx + 1) % 10;    /* 다음 슬롯 */
}
```

**관련 패턴**: Rate Monotonic Scheduling, WCET 분석, State Machine

---

## 5. Interrupt Service Routine (ISR) — Top-half / Bottom-half

<a id="isr-pattern"></a>

**목적**: 인터럽트 처리를 **즉시 처리(top-half)** 와 **지연 처리(bottom-half)** 로 분할하여 ISR 지속시간을 최소화하고 다른 인터럽트의 latency 를 보호합니다.

**특징/이론**:
- Top-half (ISR): 하드웨어 ack, 데이터 큐 적재, 플래그 설정만 — 수 μs 이내
- Bottom-half: Tasklet / Workqueue / Deferred Procedure Call — 일반 컨텍스트
- Critical section: ISR 과 태스크가 공유하는 데이터는 인터럽트 disable 또는 lock-free 큐
- Nested interrupt: 우선순위 기반 중첩 허용 (Cortex-M NVIC)

```
Interrupt latency = HW 검출 + 컨텍스트 저장 + ISR 진입 + 사용자 ISR
   목표: 모든 ISR ≤ 10μs (대부분 임베디드)
```

**장점**:
- 짧은 ISR → 다른 인터럽트의 응답성 보호
- Bottom-half 에서 RTOS API(블로킹) 사용 가능
- 우선순위 역전 최소화

**단점**:
- Bottom-half 디스패치 오버헤드
- Top-half ↔ Bottom-half 간 동기화 설계 필요
- ISR 누락 시 데이터 손실 (overrun) — DMA 보강 필요

**활용 예시**:
- Linux IRQ → softirq / tasklet / workqueue
- FreeRTOS `xQueueSendFromISR` + 일반 태스크
- UART 수신 byte → ring buffer → 라인 파서 태스크

**C 예제** (FreeRTOS UART ISR + 처리 태스크):
```c
#include "FreeRTOS.h"
#include "queue.h"
#include "stm32f4xx.h"

static QueueHandle_t uart_rx_q;   /* ISR → task 채널 */

/* Top-half: ISR — 짧게, byte 만 큐로 전달 */
void USART1_IRQHandler(void) {
    BaseType_t hp_task_woken = pdFALSE;
    if (USART1->SR & USART_SR_RXNE) {
        uint8_t byte = (uint8_t)USART1->DR;
        xQueueSendFromISR(uart_rx_q, &byte, &hp_task_woken);
    }
    portYIELD_FROM_ISR(hp_task_woken);   /* 깨운 태스크 우선순위 높으면 즉시 스위치 */
}

/* Bottom-half: 일반 태스크 — 파싱 등 무거운 작업 */
static void uart_parser_task(void *pv) {
    uint8_t byte;
    for (;;) {
        if (xQueueReceive(uart_rx_q, &byte, portMAX_DELAY) == pdTRUE) {
            parse_protocol_byte(byte);   /* 블로킹 호출 가능 */
        }
    }
}

void uart_init(void) {
    uart_rx_q = xQueueCreate(64, sizeof(uint8_t));
    xTaskCreate(uart_parser_task, "uart", 512, NULL, 3, NULL);
    NVIC_EnableIRQ(USART1_IRQn);
}
```

**관련 패턴**: Ring Buffer, DMA Buffer, Producer-Consumer

---

## 6. DMA Buffer — Ping-Pong / Circular DMA

<a id="dma-buffer"></a>

**목적**: CPU 개입 없이 페리페럴 ↔ 메모리 전송을 DMA 컨트롤러가 수행하고, **이중 버퍼(ping-pong)** 또는 **순환 버퍼(circular)** 로 무중단 스트리밍을 구현합니다.

**특징/이론**:
- Ping-Pong: 두 버퍼 교대 — DMA 는 buf_A, CPU 는 buf_B 처리, 절반 인터럽트(Half-Transfer)로 스위치
- Circular: 단일 링 버퍼, DMA 는 wrap-around, CPU 는 head/tail 추적
- Cache coherence: ARM Cortex-M7 / Cortex-A 에서 DMA 영역은 non-cacheable 또는 clean/invalidate 필요
- 버퍼 alignment: 4-byte / 32-byte (cache line) 정렬 필수

**장점**:
- CPU 개입 0 → 고대역폭 스트리밍 가능 (ADC, I2S, SPI)
- 인터럽트 빈도 감소 (블록 단위)
- 결정론적 전송 (DMA priority)

**단점**:
- Cache coherence 버그 — invalidate 누락 시 stale data
- 버퍼 alignment / size 제약
- 디버깅 어려움 (CPU 가시성 밖)

**활용 예시**:
- ADC 연속 샘플링 → 신호 처리
- I2S 오디오 더블 버퍼링
- Camera DCMI → frame buffer
- Ethernet DMA descriptor ring

**C 예제** (STM32 HAL ADC Ping-Pong):
```c
#include "stm32f4xx_hal.h"
#include <stdatomic.h>

#define DMA_BUF_SIZE 1024
/* 32-byte alignment — Cortex-M7 cache line */
__attribute__((aligned(32))) static uint16_t dma_buf[DMA_BUF_SIZE * 2];

static volatile uint16_t *ready_buf = NULL;   /* 처리 대기 중인 절반 */
static atomic_int        ready_flag = 0;

/* DMA Half-Transfer: 앞 절반 채움 완료 — CPU 가 처리 */
void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef *h) {
    SCB_InvalidateDCache_by_Addr((uint32_t*)&dma_buf[0],
                                 DMA_BUF_SIZE * sizeof(uint16_t));
    ready_buf = &dma_buf[0];
    atomic_store(&ready_flag, 1);
}
/* DMA Transfer Complete: 뒷 절반 완료 — CPU 가 처리, DMA 는 앞으로 wrap */
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *h) {
    SCB_InvalidateDCache_by_Addr((uint32_t*)&dma_buf[DMA_BUF_SIZE],
                                 DMA_BUF_SIZE * sizeof(uint16_t));
    ready_buf = &dma_buf[DMA_BUF_SIZE];
    atomic_store(&ready_flag, 1);
}

void adc_start(ADC_HandleTypeDef *h) {
    HAL_ADC_Start_DMA(h, (uint32_t*)dma_buf, DMA_BUF_SIZE * 2);
}
/* 메인 루프 또는 태스크에서 ready_flag polling → 처리 */
```

**관련 패턴**: Ring Buffer, ISR Pattern, Producer-Consumer

---

## 7. Watchdog Timer — 시스템 데드락 감지

<a id="watchdog-timer"></a>

**목적**: 하드웨어/소프트웨어 타이머가 주기적으로 "kick" 되지 않으면 시스템을 강제 reset 하여 무한 루프·deadlock·hard fault 로부터 자동 복구합니다.

**특징/이론**:
- Hardware Watchdog (HW WDT): 별도 회로, CPU clock fail 도 감지 — 가장 강력
- Software Watchdog: 고우선 태스크가 다른 태스크의 활성도 모니터링
- Window WDT: kick 시점에 상하한 — 너무 빠른 kick 도 fail (런어웨이 코드 검출)
- Multi-stage: 1차 인터럽트 → 진단 dump → 2차 reset

```
Kick 주기 = WDT timeout × 0.5 (안전 마진)
예: WDT 4s → 2s 마다 kick
```

**장점**:
- 예측 불가 hang 으로부터 자동 복구
- 안전 펑션 필수 요소 (IEC 61508 SIL-2 이상)
- HW WDT 는 펌웨어 버그에도 동작

**단점**:
- Kick 위치 잘못 설계 시 hang 상태에서도 계속 kick (방어 무력화)
- Multi-task 시스템에서 각 태스크 활성도 추적 복잡
- Reset 빈발 시 부트 루프

**활용 예시**:
- 모든 안전 임계 임베디드 시스템 (필수)
- 자동차 ECU IWDG (Independent Watchdog)
- 우주선 / 산업제어 cyclic reset

**C 예제** (STM32 IWDG + 멀티 태스크 활성도):
```c
#include "stm32f4xx_hal.h"
#include <stdatomic.h>

#define N_TASKS 3
static atomic_uint task_alive[N_TASKS];   /* 각 태스크가 setting */

static IWDG_HandleTypeDef hiwdg;

void wdt_init_4s(void) {
    hiwdg.Instance = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_256;   /* 32kHz/256 = 125Hz */
    hiwdg.Init.Reload    = 500;                  /* 500/125 = 4s timeout */
    HAL_IWDG_Init(&hiwdg);
}

/* 각 태스크는 자기 슬롯에 카운터 증가 — alive 신호 */
void task_alive_signal(int task_id) {
    atomic_fetch_add(&task_alive[task_id], 1);
}

/* 감시 태스크: 모든 슬롯이 갱신되었을 때만 kick */
void watchdog_supervisor_task(void *pv) {
    unsigned last[N_TASKS] = {0};
    for (;;) {
        bool all_alive = true;
        for (int i = 0; i < N_TASKS; i++) {
            unsigned cur = atomic_load(&task_alive[i]);
            if (cur == last[i]) { all_alive = false; break; }   /* 갱신 안 됨 */
            last[i] = cur;
        }
        if (all_alive) HAL_IWDG_Refresh(&hiwdg);   /* kick */
        /* 갱신 누락 → kick 안 함 → 4s 후 reset */
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
```

**관련 패턴**: Health Check, ISR Pattern, Reliability 패턴 (reliability.md)

---

## 8. Ring Buffer / Circular Buffer — 단일 SPSC 무락 큐

<a id="ring-buffer"></a>

**목적**: 고정 크기 배열에 head/tail 인덱스로 FIFO 큐를 구현하여 **동적 할당 없이** producer-consumer 통신을 수행합니다. ISR ↔ Task 경계에서 표준.

**특징/이론**:
- 크기는 2의 거듭제곱 — `idx & (SIZE-1)` 마스크로 wrap (mod 연산 회피)
- SPSC(Single Producer Single Consumer): 락 없이 안전, head/tail 만 atomic
- MPMC 는 추가 동기화 필요 (Vyukov queue 등)
- Full / Empty 구분: `head == tail` 모호 → 한 자리 비워두거나 별도 카운터

```
Empty:  head == tail
Full :  ((head + 1) & MASK) == tail   (한 자리 비워두는 변형)
```

**장점**:
- 동적 메모리 0 (사전 할당)
- SPSC 는 락 없음 — ISR 안전
- 캐시 친화적 (연속 메모리)
- WCET 분석 용이 (O(1))

**단점**:
- 크기 고정 — overflow 시 drop / overwrite 정책 결정 필요
- MPMC 확장 시 복잡도 급증
- ARM 약한 메모리 모델에서 `__DMB()` barrier 필수

**활용 예시**:
- UART RX/TX 버퍼
- 로그 큐 (printf → DMA TX)
- Linux kfifo
- FreeRTOS StreamBuffer

**C 예제** (SPSC lock-free ring buffer):
```c
#include <stdint.h>
#include <stdbool.h>
#include <stdatomic.h>
#include "cmsis_compiler.h"   /* __DMB */

#define RB_SIZE 256                          /* 2의 거듭제곱 */
#define RB_MASK (RB_SIZE - 1)

typedef struct {
    uint8_t  buf[RB_SIZE];
    _Atomic uint16_t head;   /* producer 가 write */
    _Atomic uint16_t tail;   /* consumer 가 read */
} ring_buf_t;

/* Producer (ISR) — 한 byte push, full 이면 drop */
bool rb_push(ring_buf_t *rb, uint8_t v) {
    uint16_t h = atomic_load_explicit(&rb->head, memory_order_relaxed);
    uint16_t t = atomic_load_explicit(&rb->tail, memory_order_acquire);
    if (((h + 1) & RB_MASK) == t) return false;     /* full */
    rb->buf[h] = v;
    __DMB();                                         /* 데이터 → 인덱스 순서 보장 */
    atomic_store_explicit(&rb->head, (h + 1) & RB_MASK, memory_order_release);
    return true;
}

/* Consumer (Task) — 한 byte pop, empty 이면 false */
bool rb_pop(ring_buf_t *rb, uint8_t *out) {
    uint16_t t = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    uint16_t h = atomic_load_explicit(&rb->head, memory_order_acquire);
    if (h == t) return false;                        /* empty */
    *out = rb->buf[t];
    __DMB();
    atomic_store_explicit(&rb->tail, (t + 1) & RB_MASK, memory_order_release);
    return true;
}
```

**관련 패턴**: DMA Buffer, ISR Pattern, Producer-Consumer (concurrency.md)

---

## 9. Memory Pool / Static Allocation — 동적 할당 금지

<a id="memory-pool"></a>

**목적**: `malloc` / `free` 를 금지하고 **사전 할당된 고정 크기 블록 pool** 에서 alloc/free 를 수행하여 fragmentation 제거·결정론적 시간·WCET 분석을 가능케 합니다. MISRA-C, AUTOSAR C++ 14, JSF AV C++ 가 요구.

**특징/이론**:
- Pool: 동일 크기 N 블록 사전 할당 → free list 로 관리
- alloc/free 시간 O(1) — WCET 보장
- Slab allocator 변형: 여러 크기 클래스의 pool 묶음
- **금지 패턴**:
  - `malloc/calloc/realloc/free` (libc heap)
  - `new/delete` (C++)
  - 재귀 함수의 자동 변수에 큰 배열

```
Heap fragmentation 위험:
  alloc(100) free(100) alloc(200) → 연속 200 없으면 fail
Pool 은 모든 블록 동일 크기 → fragmentation 0
```

**장점**:
- Fragmentation 0 — 메모리 부족 사전 예측 가능
- alloc/free O(1) — 결정론적
- 안전인증 요구 충족 (MISRA-C Rule 21.3)
- 디버깅 용이 (블록 누수 추적)

**단점**:
- 크기 클래스 사전 결정 필요
- 작은 블록 낭비 (internal fragmentation)
- 가변 크기 데이터에 비효율

**활용 예시**:
- FreeRTOS heap_4 / heap_5 (단, 사용 비권장 — pool 권장)
- lwIP `PBUF_POOL` 네트워크 패킷
- AUTOSAR MemPool
- Zephyr `k_mem_slab`

**C 예제** (고정 크기 블록 pool):
```c
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define POOL_BLOCK_SIZE 64
#define POOL_BLOCK_CNT  32

/* free list — 다음 free 블록의 인덱스를 첫 워드에 저장 (intrusive) */
typedef struct {
    uint8_t storage[POOL_BLOCK_CNT][POOL_BLOCK_SIZE];
    int16_t next[POOL_BLOCK_CNT];          /* free list */
    int16_t free_head;                     /* -1 이면 empty */
} mem_pool_t;

void pool_init(mem_pool_t *p) {
    for (int i = 0; i < POOL_BLOCK_CNT - 1; i++) p->next[i] = (int16_t)(i + 1);
    p->next[POOL_BLOCK_CNT - 1] = -1;
    p->free_head = 0;
}

/* O(1) alloc */
void *pool_alloc(mem_pool_t *p) {
    if (p->free_head < 0) return NULL;     /* 고갈 */
    int16_t idx = p->free_head;
    p->free_head = p->next[idx];
    return &p->storage[idx][0];
}

/* O(1) free */
void pool_free(mem_pool_t *p, void *block) {
    if (!block) return;
    int16_t idx = (int16_t)(((uint8_t*)block - &p->storage[0][0]) / POOL_BLOCK_SIZE);
    p->next[idx] = p->free_head;
    p->free_head = idx;
}

/* 사용 예: 메시지 객체 pool */
static mem_pool_t msg_pool;
typedef struct { uint32_t id; uint8_t payload[60]; } msg_t;
/* 컴파일 타임 검증: sizeof(msg_t) ≤ POOL_BLOCK_SIZE */
_Static_assert(sizeof(msg_t) <= POOL_BLOCK_SIZE, "msg too big");
```

**관련 패턴**: WCET 분석, Ring Buffer, Object Pool (creational.md)

---

## 10. State Machine (Hierarchical / Statechart)

<a id="state-machine-embedded"></a>

**목적**: 시스템 동작을 **유한 상태(state)** 와 **이벤트 → 천이(transition)** 로 모델링하여 임베디드 제어 로직을 결정론적으로 구현합니다. UML Statechart (Harel) 의 hierarchical / orthogonal / history 확장.

**특징/이론**:
- Flat FSM: 상태 N 개, 천이 표 또는 switch
- HSM (Hierarchical): 상태 중첩 → super state 의 행동 상속 → 천이 폭발 방지
- Orthogonal regions: 독립 병행 상태
- Entry / Exit / Do action — 상태별 hook
- **Quantum Framework (QP/C)**: Miro Samek 의 산업용 HSM 라이브러리
- 이벤트는 ISR 에서 발생 → active object 큐로 dispatch (RTC: Run-To-Completion)

**장점**:
- 동작 명시화 — 디자인 단계에서 누락 천이 검출
- 코드 = 모델 (UML state diagram 1:1)
- 안전인증 친화 (정형 검증 가능 — SPIN, NuSMV)
- 깊은 if-else 중첩 회피

**단점**:
- 단순 시퀀스에는 과한 추상화
- HSM 구현 라이브러리(QP) 학습 곡선
- 상태 폭발 (state explosion) — orthogonal region 으로 완화

**활용 예시**:
- 통신 프로토콜 스택 (TCP, BLE, USB)
- 사용자 인터페이스 모드 전환
- 산업용 제어기 (충전기, 인버터)
- 의료기기 운영 모드 (Self-Test → Idle → Running → Alarm)

**C 예제** (간단 HSM — 충전기 예제):
```c
#include <stdint.h>

typedef enum { EV_PLUG_IN, EV_PLUG_OUT, EV_FULL, EV_FAULT, EV_TICK } event_t;
typedef enum { ST_IDLE, ST_CHARGING, ST_FULL, ST_FAULT } state_t;

typedef struct {
    state_t state;
    uint32_t soc_mv;
} charger_t;

/* RTC: 한 이벤트 처리 후 반드시 종료 (블로킹 금지) */
void charger_dispatch(charger_t *c, event_t e) {
    switch (c->state) {
    case ST_IDLE:
        if (e == EV_PLUG_IN) {
            led_set(LED_GREEN_BLINK);   /* entry action */
            c->state = ST_CHARGING;
        }
        break;
    case ST_CHARGING:
        if      (e == EV_PLUG_OUT) { led_set(LED_OFF);   c->state = ST_IDLE;  }
        else if (e == EV_FULL)     { led_set(LED_GREEN); c->state = ST_FULL;  }
        else if (e == EV_FAULT)    { led_set(LED_RED);   c->state = ST_FAULT; }
        else if (e == EV_TICK)     { c->soc_mv = read_battery_mv(); }
        break;
    case ST_FULL:
        if (e == EV_PLUG_OUT) { led_set(LED_OFF); c->state = ST_IDLE; }
        break;
    case ST_FAULT:
        /* PLUG_OUT 만 복구 — super state 동작 상속 효과 */
        if (e == EV_PLUG_OUT) { led_set(LED_OFF); c->state = ST_IDLE; }
        break;
    }
}

/* ISR 에서 이벤트 발생 → active object 큐로 전달 (RTC 보장) */
void plug_irq(void) { queue_post(EV_PLUG_IN); }
```

**관련 패턴**: Time-Triggered Architecture, ISR Pattern, State (behavioral.md)
