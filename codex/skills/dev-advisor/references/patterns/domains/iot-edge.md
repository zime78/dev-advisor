# IoT / Edge Computing 도메인 패턴 (IoT & Edge Computing Patterns)

연결된 디바이스·게이트웨이·클라우드 분산의 정평 있는 10 패턴. AWS IoT Core / Azure IoT Hub / Google Cloud IoT / Tesla OTA / Nest / Industrial IoT (Siemens MindSphere) 사례.

**원전·표준 참고**:
- AWS IoT — Device Shadow, Greengrass, FreeRTOS
- Azure IoT Hub / IoT Edge — Module Twin, IoT Plug and Play
- MQTT v5 (OASIS, 2019)
- CoAP (RFC 7252) — Constrained device protocol
- LwM2M (OMA) — Device management standard
- ISO/IEC 21823 (IoT interoperability framework)
- NIST SP 800-213 (IoT Device Cybersecurity)
- IEC 62443 (Industrial IoT security)

**핵심 비기능 요구**:
- **간헐적 연결 (Intermittent connectivity)** — 디바이스 offline 시 graceful degradation
- **제약된 자원 (Constrained)** — MCU KB 메모리, battery 제약, MQTT/CoAP 같은 경량 프로토콜
- **fleet 규모 (Scalability)** — 디바이스 수백만, 동시 연결 수십만
- **보안 (Security)** — Mutual TLS, OTA 서명 검증, hardware-backed key

**관련 카탈로그**:
- [`../embedded.md`](../embedded.md) — 임베디드/RTOS 패턴 (디바이스 펌웨어 측)
- [`../../security/security-crypto-ops.md`](../../security/security-crypto-ops.md) — mTLS, Key Rotation, PFS
- [`../../security/security-mobile.md`](../../security/security-mobile.md) — App Attest (모바일 컴패니언 앱)
- [`../caching.md`](../caching.md) — Edge cache pattern

---

## 1. Device Twin (Digital Twin) — 디바이스 트윈

<a id="device-twin"></a>

**목적**: 클라우드에 디바이스의 **논리적 복제본(twin)** 을 유지하여 디바이스 offline 시에도 상태 조회·원하는 상태 설정이 가능하게 합니다. AWS IoT 의 **Device Shadow** 와 Azure IoT Hub 의 **Module/Device Twin** 이 동일 개념.

**메커니즘**:
- **Desired state**: 클라우드/앱이 원하는 설정 (예: `{ "thermostat": 22.5 }`)
- **Reported state**: 디바이스가 실제 보고한 현재 값
- **Delta**: desired - reported, 디바이스 online 시 디바이스가 수신하여 reconcile
- **Versioning**: 각 twin document 에 `version` / `metadata.lastUpdated` — optimistic concurrency
- **Eventual consistency**: 클라우드 ↔ 디바이스 비동기 sync, 디바이스 offline 시에도 desired 변경 가능

**장점**:
- 디바이스 offline 시에도 앱/대시보드 UX 유지 (last-known + desired 표시)
- 명령 전달이 비동기·idempotent (디바이스가 reconnect 시 자동 수신)
- Device-side 코드 단순화 (delta 수신만 처리)

**단점·주의**:
- Twin document 크기 제한 (AWS Shadow 8KB, Azure 32KB) → 대용량 데이터 부적합
- Eventual consistency — 즉각 명령 응답 보장 안 됨, 별도 ACK 채널 필요
- Desired 변경 폭주 시 race — 마지막 desired 만 유효
- 보안: twin 은 device identity 와 1:1, mTLS·SAS token 필수

**표준 매핑**:
- **AWS IoT Device Shadow** (Classic / Named Shadow)
- **Azure IoT Hub Device Twin / Module Twin**
- **LwM2M Object/Resource model** (OMA 표준)
- **IoT Plug and Play DTDL** — Digital Twins Definition Language

**JSON 예제** (AWS Shadow document):
```json
{
  "state": {
    "desired": {
      "thermostat": 22.5,
      "mode": "auto",
      "fan_speed": 2
    },
    "reported": {
      "thermostat": 21.8,
      "mode": "auto",
      "fan_speed": 1,
      "firmware": "1.4.2",
      "battery_pct": 87
    },
    "delta": {
      "thermostat": 22.5,
      "fan_speed": 2
    }
  },
  "metadata": {
    "desired": { "thermostat": { "timestamp": 1715600000 } },
    "reported": { "thermostat": { "timestamp": 1715599800 } }
  },
  "version": 142,
  "timestamp": 1715600005
}
```

**Kotlin 예제** (Azure IoT Hub Device Twin — 디바이스 측 SDK):
```kotlin
// Device 측: desired 변경 수신 → reconcile
class ThermostatTwin(private val client: DeviceClient) {

    fun start() {
        // 1) 초기 desired 조회 + reported 동기화
        val twin = client.getTwin()
        applyDesired(twin.properties.desired)

        // 2) desired 변경 콜백 등록
        client.startDeviceTwin { delta ->
            applyDesired(delta)
            // 3) reconcile 후 reported 업데이트
            val reported = TwinCollection().apply {
                put("thermostat", currentSetpoint)
                put("mode", currentMode)
                put("firmware", FW_VERSION)
            }
            client.sendReportedProperties(reported)
        }
    }

    private fun applyDesired(desired: TwinCollection) {
        desired["thermostat"]?.let { currentSetpoint = (it as Number).toDouble() }
        desired["mode"]?.let     { currentMode = it as String }
        // 하드웨어에 실제 반영
        hardware.setTarget(currentSetpoint, currentMode)
    }
}

// Cloud 측: desired 만 변경 — 디바이스 offline 이어도 OK
suspend fun setTargetTemperature(deviceId: String, target: Double) {
    val twin = registryManager.getTwin(deviceId)
    twin.desired = TwinCollection().apply { put("thermostat", target) }
    registryManager.updateTwin(twin)
}
```

**관련 패턴**: Telemetry Buffer, Command & Control, Device Provisioning

---

## 2. OTA Firmware Update — 무선 펌웨어 업데이트

<a id="ota-firmware"></a>

**목적**: 디바이스 펌웨어를 **무선으로 안전하게 배포·검증·롤백** 합니다. Tesla / Nest / Apple AirPods 등 모든 connected device 의 필수 메커니즘. 신뢰의 시작점은 secure boot.

**메커니즘**:
- **A/B partition (dual-bank)**: 활성 슬롯 A 동작 중에 슬롯 B 로 다운로드 → reboot 시 B 부팅, 실패 시 A 로 자동 rollback
- **Delta image (binary diff)**: bsdiff/Courgette/zucchini 로 변경분만 전송 (전체 image 대비 80~95% 감소)
- **Signature verification**: ECDSA-P256 / RSA-3072 으로 image 서명, 디바이스는 root public key 로 검증
- **Staged rollout**: canary 1% → 10% → 50% → 100%, 실패율 임계 초과 시 자동 중단
- **Anti-rollback counter**: 보안 패치된 버전으로의 다운그레이드 방지 (eFuse / OTP)

**장점**:
- 출하 후 보안 패치·기능 추가 가능 — 디바이스 lifecycle 연장
- A/B rollback 으로 brick (벽돌화) 위험 제거
- Delta 로 대역폭·battery 절감

**단점·주의**:
- Flash 용량 2배 필요 (A/B partition) — cost 증가
- 검증 순서가 핵심: **서명 검증 → 버전 검증 → flash → 활성 partition 전환** 순. 순서 어기면 보안 우회
- Power-fail 중 update → 부분 write → 다음 boot 손상. 반드시 atomic flag 사용
- Key compromise 시 fleet 전체 위험 — HSM 보호·key rotation 필수

**표준 매핑**:
- **TUF (The Update Framework)** — Uptane (자동차 OTA 표준 SAE J3061 기반)
- **LwM2M Firmware Update Object** (Object ID 5)
- **MCUboot** (Zephyr / NCS / Mbed 기본 부트로더)
- **NIST SP 800-193** (Platform Firmware Resiliency — protect/detect/recover)

**OTA Manifest JSON 예제** (TUF/Uptane 스타일):
```json
{
  "signed": {
    "_type": "Targets",
    "version": 142,
    "expires": "2026-12-31T23:59:59Z",
    "targets": {
      "thermostat-v1.5.0.bin": {
        "length": 524288,
        "hashes": {
          "sha256": "9a1f3e7c4b8d2a5f6e0c1b9d4a7f3e2c5b8d1a4f7e0c3b6d9a2f5e8c1b4d7a0f"
        },
        "custom": {
          "ecu_identifier": "thermostat-mcu-v2",
          "min_version": "1.4.0",
          "rollout_pct": 10,
          "delta_from": "1.4.2",
          "delta_url": "https://ota.example.com/delta/1.4.2_to_1.5.0.bin"
        }
      }
    }
  },
  "signatures": [
    {
      "keyid": "ota-targets-key-2026",
      "method": "ecdsa-sha2-nistp256",
      "sig": "MEUCIQDxq..."
    }
  ]
}
```

**C 의사코드** (A/B partition + 서명 검증):
```c
typedef enum { SLOT_A = 0, SLOT_B = 1 } slot_t;
typedef struct { uint32_t magic; uint8_t version[16]; uint8_t signature[64]; uint8_t image_sha256[32]; } image_hdr_t;

extern const uint8_t OTA_ROOT_PUBKEY[64];   /* 펌웨어에 박힌 root key */
extern uint32_t  current_version_num(void);  /* anti-rollback */

/* OTA 적용 순서 — 절대 어기지 말 것 */
int ota_apply(slot_t inactive, const uint8_t *blob, size_t len) {
    image_hdr_t *h = (image_hdr_t*)blob;
    if (h->magic != IMAGE_MAGIC)                    return -1;

    /* 1) 서명 검증 — flash 쓰기 전 */
    if (!ecdsa_verify_p256(OTA_ROOT_PUBKEY,
                           blob + sizeof(image_hdr_t),
                           len  - sizeof(image_hdr_t),
                           h->signature))           return -2;

    /* 2) 해시 검증 (서명 payload 와 image 내용 일치) */
    if (!sha256_match(blob + sizeof(image_hdr_t),
                      len  - sizeof(image_hdr_t),
                      h->image_sha256))             return -3;

    /* 3) Anti-rollback: 최소 버전 이상인가 */
    uint32_t new_ver = parse_version(h->version);
    if (new_ver < current_version_num())            return -4;

    /* 4) 비활성 slot 에 flash */
    flash_erase_slot(inactive);
    flash_write_slot(inactive, blob, len);
    if (!flash_verify(inactive, blob, len))         return -5;

    /* 5) Boot flag 원자적 전환 — power-fail 안전 */
    boot_set_pending(inactive);                     /* "다음 부팅 시 시도" */
    /* 부팅 후 health-check 성공 → boot_set_confirmed(inactive)
       실패 → bootloader 가 자동 이전 slot 으로 fallback */
    return 0;
}
```

**관련 패턴**: Device Identity & mTLS, Device Twin (firmware 버전 reported), Telemetry Buffer

---

## 3. Telemetry Buffer (Store-and-Forward) — 텔레메트리 버퍼

<a id="telemetry-buffer"></a>

**목적**: 디바이스가 **offline / 약전계 / cellular 없음** 상태에서 발생한 텔레메트리를 로컬에 보존했다가 재연결 시 batch upload 합니다. 산업 IoT·자동차·웨어러블의 필수 패턴.

**메커니즘**:
- **Local FIFO buffer**: SPI NOR flash 또는 RAM 의 ring buffer
- **Backpressure 정책**: full 시 (a) 가장 오래된 drop, (b) 최신 drop, (c) 압축 후 retry — 도메인별 선택
- **Batch upload**: reconnect 시 N 개씩 묶어 송신, ACK 확인 후 buffer 에서 삭제
- **Timestamp at source**: 디바이스 RTC 로 timestamp 박아 — 서버 도착 시각이 아닌 발생 시각 보존
- **Compression**: gzip / cbor / protobuf → 대역폭·battery 절감

**장점**:
- 간헐 연결 환경에서 데이터 무손실
- 재연결 시 batch → 네트워크 overhead 감소
- battery·cellular 비용 절감 (큰 묶음으로 무선 module wake-up 최소화)

**단점·주의**:
- Flash 마모 (NOR 100K cycle, NAND 3K~10K) — wear-leveling 필요
- Timestamp 정확도가 RTC 정확성에 의존 — NTP sync 또는 GNSS sync 권장
- Replay 시 서버 측 idempotency 필요 (중복 도착 가능)
- Buffer overflow 정책이 도메인 요구와 일치해야 (의료·항공은 oldest-drop 절대 금지)

**표준 매핑**:
- **MQTT v5 Persistent Session** + `Session Expiry Interval` — 서버 측 buffering
- **AWS IoT Device SDK** built-in offline publish queue
- **Azure IoT Edge** module의 local storage

**Kotlin 예제** (Android — Room DB 기반 buffer + WorkManager batch upload):
```kotlin
@Entity(tableName = "telemetry_buffer")
data class TelemetryRow(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val deviceId: String,
    val timestampMs: Long,          // 발생 시각 (소스)
    val payloadJson: String,
    val attempts: Int = 0,
)

@Dao
interface TelemetryDao {
    @Insert suspend fun enqueue(row: TelemetryRow): Long
    @Query("SELECT * FROM telemetry_buffer ORDER BY timestampMs ASC LIMIT :n")
    suspend fun peekBatch(n: Int): List<TelemetryRow>
    @Query("DELETE FROM telemetry_buffer WHERE id IN (:ids)")
    suspend fun ackAndDelete(ids: List<Long>)
    @Query("SELECT COUNT(*) FROM telemetry_buffer") suspend fun size(): Int
}

class TelemetryRecorder(private val dao: TelemetryDao, private val maxRows: Int = 5_000) {
    suspend fun record(deviceId: String, payload: Map<String, Any>) {
        // Full 시 oldest drop (도메인에 따라 정책 변경)
        if (dao.size() >= maxRows) dao.dropOldest(maxRows / 10)
        dao.enqueue(TelemetryRow(
            deviceId = deviceId,
            timestampMs = System.currentTimeMillis(),
            payloadJson = Json.encodeToString(payload),
        ))
    }
}

class TelemetryUploadWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val batch = dao.peekBatch(n = 50)
        if (batch.isEmpty()) return Result.success()
        return try {
            // 서버 측 idempotency: row.id + deviceId 조합으로 dedup
            api.uploadBatch(batch)
            dao.ackAndDelete(batch.map { it.id })
            Result.success()
        } catch (e: IOException) {
            Result.retry()                    // exponential backoff (WorkManager 내장)
        }
    }
}
```

**관련 패턴**: MQTT Pub-Sub (Persistent Session), Idempotency Key, Time-Series Storage

---

## 4. Device Provisioning / Onboarding — 디바이스 프로비저닝

<a id="device-provisioning"></a>

**목적**: 출하된 디바이스가 **첫 부팅 시 자동으로 클라우드에 등록·인증·구성** 됩니다. 수십만 대를 수동 등록할 수 없으므로 zero-touch 가 필수.

**메커니즘**:
- **Zero-touch (DPS)**: 제조 시 X.509 cert 또는 TPM/Secure Element 의 endorsement key 를 prov 서비스에 사전 등록 → 디바이스 첫 부팅 시 DPS 가 적절한 IoT Hub 로 자동 할당
- **QR pairing**: 디바이스가 QR 코드(WiFi SSID + token) 표시 → 모바일 앱 스캔 → BLE/SoftAP 로 WiFi 자격증명 전달
- **EST / SCEP**: 디바이스가 CSR 생성 → CA 가 cert 발급 (RFC 7030)
- **Per-device cert**: 각 디바이스마다 고유 cert, 한 대 침해 시 그 한 대만 revoke
- **Pre-shared key (PSK)**: 자원 제약 디바이스 대안 — TLS-PSK (cert 보다 가볍지만 단일 키 노출 위험)

**장점**:
- 수동 입력 0 — 박스 개봉 후 전원만 켜면 동작
- 디바이스 ↔ 클라우드 자동 매핑 (region, customer, fleet)
- Per-device cert 로 보안 분리

**단점·주의**:
- 제조 단계 보안 인프라 필요 (HSM, secure provisioning station)
- Endorsement key 누출 시 fleet 전체 영향
- QR pairing 은 사용자 UX 양호하나 BLE/SoftAP 구간이 공격 표면 — channel binding 권장
- DPS 단일 장애점 — region failover 설계 필요

**표준 매핑**:
- **AWS IoT Fleet Provisioning** — claim cert + provisioning template
- **Azure IoT Hub Device Provisioning Service (DPS)**
- **EST (RFC 7030)** — Enrollment over Secure Transport
- **WiFi Easy Connect (DPP)** — QR/NFC 기반 표준
- **Matter (formerly CHIP)** — smart home 표준 commissioning flow

**Provisioning Template JSON 예제** (AWS Fleet Provisioning):
```json
{
  "Parameters": {
    "SerialNumber":   { "Type": "String" },
    "Location":       { "Type": "String" },
    "CSR":            { "Type": "String" }
  },
  "Resources": {
    "certificate": {
      "Type": "AWS::IoT::Certificate",
      "Properties": { "CertificateSigningRequest": { "Ref": "CSR" }, "Status": "Active" }
    },
    "policy": {
      "Type": "AWS::IoT::Policy",
      "Properties": { "PolicyName": "ThermostatPolicy" }
    },
    "thing": {
      "Type": "AWS::IoT::Thing",
      "Properties": {
        "ThingName":  { "Ref": "SerialNumber" },
        "ThingGroups": [ { "Ref": "Location" } ],
        "AttributePayload": {
          "version": "1.0",
          "serialNumber": { "Ref": "SerialNumber" }
        }
      }
    }
  }
}
```

**Kotlin 예제** (Android 컴패니언 앱 — BLE QR 페어링 수신측):
```kotlin
class ProvisioningCoordinator(
    private val ble: BleClient,
    private val cloudApi: IotCloudApi,
) {
    suspend fun pair(qrPayload: QrPayload, wifi: WifiCredential): ProvisionResult {
        // 1) QR 의 ephemeral pubkey 로 BLE 채널 secure (channel binding)
        val session = ble.connect(qrPayload.bleAddress, qrPayload.ephemeralPubKey)

        // 2) 디바이스로 WiFi 자격증명 전달 (encrypted over BLE)
        session.send(WifiConfigFrame(wifi.ssid, wifi.password))

        // 3) 디바이스가 자체 keypair 생성 + CSR 반환
        val csr = session.receive<CsrFrame>().csrPem

        // 4) Cloud DPS 호출 — claim cert 와 함께 등록 요청
        val deviceCert = cloudApi.provision(
            serialNumber = qrPayload.serialNumber,
            csrPem = csr,
            claimToken = qrPayload.claimToken,
        )

        // 5) 발급된 cert 를 디바이스로 전달
        session.send(DeviceCertFrame(deviceCert.pem, deviceCert.iotHubHost))

        // 6) 디바이스가 IoT Hub 연결 + reported state 전송 대기
        return cloudApi.awaitFirstReport(qrPayload.serialNumber, timeout = 60.seconds)
    }
}
```

**관련 패턴**: Device Identity & mTLS, Device Twin (초기 reported), OTA Firmware (provisioning 후 첫 update)

---

## 5. Edge Gateway — 엣지 게이트웨이

<a id="edge-gateway"></a>

**목적**: 클라우드에 직접 연결할 수 없는 **제약 디바이스(BLE/Zigbee/Modbus)** 들을 묶어 클라우드로 protocol-translate / aggregate / filter 합니다. Industrial IoT·smart home hub·자동차 telematics control unit (TCU) 의 핵심.

**메커니즘**:
- **Protocol translation**: Modbus RTU / CoAP / BLE GATT / Zigbee → MQTT / HTTPS / AMQP
- **Edge filtering**: 1000 Hz 진동 센서 → 통계량(mean, RMS, peak)만 클라우드로 → 99% 대역폭 절감
- **Local cache**: 클라우드 단절 시에도 로컬 분석/제어 지속
- **Edge module orchestration**: Docker container / WebAssembly module 단위로 배포 (Greengrass, IoT Edge)
- **Time sync source**: 게이트웨이가 NTP/GNSS 받아 하위 디바이스에 timestamp 부여

**장점**:
- 제약 디바이스도 클라우드 통합 가능
- 대역폭·latency 절감 (edge 에서 filter/aggregate)
- 클라우드 단절 시 local autonomy

**단점·주의**:
- Gateway 가 단일 장애점 — HA 또는 device-direct fallback 설계 필요
- Edge 배포 파이프라인 (CI/CD for edge) 복잡
- 다중 protocol 지원으로 보안 표면 증가 (Modbus 는 인증 없음 — VLAN 격리 필수)
- Edge 와 클라우드의 모듈 버전 mismatch 관리

**표준 매핑**:
- **AWS IoT Greengrass V2** — Lambda/container 를 edge 에 배포
- **Azure IoT Edge** — module twin, custom IoT Edge runtime
- **Eclipse Kura / Kapua** — Java OSGi 기반 industrial gateway
- **EdgeX Foundry** — LF Edge 표준 microservice 프레임워크

**YAML 예제** (Azure IoT Edge deployment manifest):
```yaml
modulesContent:
  $edgeAgent:
    properties.desired:
      runtime: { type: docker, settings: { minDockerVersion: v1.25 } }
      modules:
        modbusReader:
          type: docker
          version: "1.2"
          status: running
          restartPolicy: always
          settings:
            image: myregistry.azurecr.io/modbus-reader:1.2
            createOptions: '{ "HostConfig": { "Devices":[{ "PathOnHost":"/dev/ttyUSB0","PathInContainer":"/dev/ttyUSB0","CgroupPermissions":"rwm" }] } }'
        edgeAggregator:
          type: docker
          version: "0.8"
          status: running
          settings:
            image: myregistry.azurecr.io/aggregator:0.8
  $edgeHub:
    properties.desired:
      routes:
        modbusToAggregator: FROM /messages/modules/modbusReader/* INTO BrokeredEndpoint("/modules/edgeAggregator/inputs/raw")
        aggregatorToCloud:  FROM /messages/modules/edgeAggregator/outputs/agg INTO $upstream
      storeAndForwardConfiguration:
        timeToLiveSecs: 7200
```

**Kotlin 의사코드** (Modbus → MQTT bridge + edge aggregation):
```kotlin
class EdgeGateway(
    private val modbus: ModbusMaster,
    private val mqtt: MqttClient,
) {
    private val window = SlidingWindow(durationMs = 60_000)  // 1분 통계

    suspend fun run() = coroutineScope {
        while (true) {
            // 1) 하위 디바이스 polling (Modbus RTU 1Hz)
            val raw = modbus.readHoldingRegisters(unitId = 1, address = 0x100, count = 8)
            val sample = parseVibration(raw)
            window.add(sample)

            // 2) Edge filter: 임계 초과 raw 만 + 매 60s 통계
            if (sample.peakG > 5.0) {
                mqtt.publish("alerts/${gatewayId}/${sensorId}",
                             encodeCbor(sample), qos = 1)
            }
            if (window.elapsedFullCycle()) {
                val agg = window.snapshot()  // mean, rms, peak, p99
                mqtt.publish("telemetry/${gatewayId}/${sensorId}/agg",
                             encodeCbor(agg), qos = 1, retained = false)
                window.reset()
            }
            delay(1.seconds)
        }
    }
}
```

**관련 패턴**: MQTT Pub-Sub, Edge ML Inference, Telemetry Buffer, Time-Series Storage

---

## 6. MQTT Pub-Sub — MQTT 발행/구독

<a id="mqtt-pubsub"></a>

**목적**: 제약 디바이스용 경량 publish-subscribe 프로토콜. **TCP 위 2 byte 헤더**·QoS 3 단계·persistent session 으로 IoT 의 사실상 표준이 됨. MQTT v3.1.1 (OASIS, 2014) → v5 (OASIS, 2019).

**메커니즘**:
- **Topic hierarchy**: `building/floor3/room12/temp` — slash 구분, `+` 단일 레벨 와일드카드, `#` multi-level
- **QoS 0 (At most once)**: fire-and-forget, fastest, telemetry 에 적합
- **QoS 1 (At least once)**: PUBACK 필수, 중복 가능 → 수신 측 idempotency
- **QoS 2 (Exactly once)**: 4-way handshake (PUBLISH/PUBREC/PUBREL/PUBCOMP) — 가장 무거움, 결제 같은 critical
- **Retained message**: 토픽의 "마지막 값" 을 broker 가 보존 → 새 subscriber 가 즉시 last-known 수신
- **LWT (Last Will & Testament)**: 디바이스 비정상 절단 시 broker 가 자동 publish — "오프라인 됨" 알림
- **v5 추가**: Session Expiry, Message Expiry, Topic Alias (긴 토픽 압축), Shared Subscriptions (`$share/{group}/topic`)

**장점**:
- 헤더 2 byte — 제약 환경(NB-IoT, LoRa-IP) 친화
- Broker 중심 → 디바이스 끼리 직접 통신 불필요
- QoS·LWT·Retained 가 기본 — 별도 구현 불필요

**단점·주의**:
- TCP 기반 → mobile/cellular 에서 keepalive 비용 (15~60s ping)
- QoS 2 는 IoT 에서 거의 권장 안 됨 (4-way, 자원 소모) — QoS 1 + 앱 레벨 idempotency 가 표준
- Topic hierarchy 가 곧 보안 경계 — `+`/`#` 권한 설계 신중히
- Broker 장애 시 fleet 전체 영향 — clustering (HiveMQ, EMQX, AWS IoT Core) 필수

**표준 매핑**:
- **MQTT v3.1.1 (OASIS Standard, 2014)** — 가장 광범위
- **MQTT v5 (OASIS Standard, 2019)** — 신규 배포는 v5 권장
- **MQTT-SN (Sensor Networks)** — UDP 기반, ZigBee/802.15.4 게이트웨이용
- **Sparkplug B (Eclipse)** — Industrial IoT 위 MQTT topic 컨벤션

**Kotlin 예제** (HiveMQ MQTT v5 client — QoS 1 + LWT + retained):
```kotlin
val client: Mqtt5AsyncClient = MqttClient.builder()
    .useMqttVersion5()
    .identifier("thermostat-001")
    .serverHost("mqtt.example.com").serverPort(8883)
    .sslWithDefaultConfig()
    .willPublish()
        .topic("devices/thermostat-001/status")
        .payload("offline".toByteArray())
        .qos(MqttQos.AT_LEAST_ONCE)
        .retain(true)
        .applyWillPublish()
    .buildAsync()

// 연결 + 자동 retained "online" 표시
client.connectWith()
    .cleanStart(false)                              // persistent session
    .sessionExpiryInterval(86_400)                  // 24h
    .send().await()

client.publishWith()
    .topic("devices/thermostat-001/status")
    .payload("online".toByteArray())
    .qos(MqttQos.AT_LEAST_ONCE).retain(true)
    .send().await()

// Telemetry — QoS 0 fire-and-forget
suspend fun reportTemp(c: Double) {
    client.publishWith()
        .topic("devices/thermostat-001/telemetry/temp")
        .payload(c.toString().toByteArray())
        .qos(MqttQos.AT_MOST_ONCE)                  // QoS 0 — high frequency
        .send().await()
}

// Command 수신 — QoS 1 + shared subscription (v5 only)
client.subscribeWith()
    .topicFilter("\$share/cmdGroup/devices/+/cmd")  // 부하 분산
    .qos(MqttQos.AT_LEAST_ONCE)
    .callback { msg ->
        val cmd = Json.decodeFromString<Command>(msg.payloadAsBytes.decodeToString())
        if (!seen.contains(cmd.idempotencyKey)) {   // QoS1 중복 방지
            seen.add(cmd.idempotencyKey)
            handleCommand(cmd)
        }
    }
    .send().await()
```

**관련 패턴**: Telemetry Buffer (Persistent Session), Command & Control, Device Identity & mTLS

---

## 7. Edge Inference (ML at the Edge) — 엣지 ML 추론

<a id="edge-ml-inference"></a>

**목적**: 클라우드 round-trip 없이 **디바이스/게이트웨이에서 ML 추론** 을 수행하여 latency 절감·offline 동작·프라이버시 보호. 카메라 사람 감지, 스마트 스피커 wake-word, 산업 anomaly detection.

**메커니즘**:
- **Model conversion**: TensorFlow → TensorFlow Lite (.tflite), PyTorch → ONNX Runtime, Apple Core ML, NVIDIA TensorRT
- **Quantization**:
  - **INT8 PTQ (Post-Training Quantization)**: 4배 크기 감소, 2-3 배 추론 가속, 정확도 1-3%p loss
  - **QAT (Quantization-Aware Training)**: 학습 중 quant 시뮬레이션, loss 더 작음
- **Pruning / distillation**: weight 의 0 만들기, teacher → student 작은 모델로 지식 증류
- **NPU / DSP 활용**: Qualcomm Hexagon, Apple Neural Engine, Google Edge TPU, Coral
- **OTA model update**: 펌웨어와 분리된 model bundle 별도 배포 → 모델만 반복 갱신

**장점**:
- Latency 100ms → 5ms (네트워크 round-trip 제거)
- Offline 동작 — 클라우드 단절 무관
- 프라이버시 — 원본 영상/음성이 디바이스 밖으로 안 나감 (의료·아동)
- 클라우드 GPU 비용 절감

**단점·주의**:
- 모델 크기·연산 제약 (MCU 는 KB 단위 모델만 — TensorFlow Lite Micro)
- Quantization accuracy drop — 안전 critical 도메인은 검증 필수
- 모델 IP 보호 어려움 (디바이스에서 추출 가능) — 가능하면 NPU 의 secure model store 사용
- Heterogeneous fleet — 디바이스 SoC 별 model variant 관리

**표준 매핑**:
- **TensorFlow Lite / TFLite Micro** (Google) — MCU 부터 모바일까지
- **ONNX Runtime** — cross-framework 표준
- **MLPerf Tiny / Mobile / Edge** — 성능 벤치마크
- **Apple Core ML** / **Android NNAPI**
- **Edge Impulse / TinyML** — MCU 학습/배포 파이프라인

**Python 예제** (TFLite 변환 + INT8 PTQ):
```python
import tensorflow as tf

# 1) 학습된 Keras 모델 로드
model = tf.keras.models.load_model("vibration_anomaly.h5")

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# 2) INT8 PTQ — representative dataset 으로 activation 범위 calibration
def rep_gen():
    for batch in calibration_loader.take(200):
        yield [batch.astype("float32")]
converter.representative_dataset = rep_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type  = tf.int8
converter.inference_output_type = tf.int8

tflite_int8 = converter.convert()
open("vibration_anomaly_int8.tflite", "wb").write(tflite_int8)

# 결과: float32 1.8MB → int8 460KB, MCU 추론 ~12ms (Cortex-M7 @ 480MHz)
```

**Kotlin 예제** (Android — TFLite + NNAPI delegate):
```kotlin
class EdgeAnomalyDetector(ctx: Context) {
    private val interpreter: Interpreter
    init {
        val model = FileUtil.loadMappedFile(ctx, "vibration_anomaly_int8.tflite")
        val opts = Interpreter.Options().apply {
            // NNAPI 우선 (NPU/DSP), 없으면 GPU, 없으면 CPU
            if (Build.VERSION.SDK_INT >= 27) addDelegate(NnApiDelegate())
            else                            setNumThreads(4)
        }
        interpreter = Interpreter(model, opts)
    }

    fun infer(samples: ByteArray /* int8 quantized */): Float {
        val input  = ByteBuffer.allocateDirect(samples.size).put(samples).rewind()
        val output = ByteBuffer.allocateDirect(4).order(ByteOrder.nativeOrder())
        interpreter.run(input, output)
        // dequantize: scale, zero_point 는 .tflite 메타에 포함
        val rawInt8 = output.get(0).toInt()
        return (rawInt8 - ZERO_POINT) * SCALE         // anomaly score
    }
}
```

**관련 패턴**: Edge Gateway, OTA Firmware (model bundle), Telemetry Buffer (anomaly 시 raw 업로드)

---

## 8. Time-Series Storage — 시계열 저장소

<a id="time-series-storage"></a>

**목적**: 디바이스가 발생시키는 **(timestamp, tag set, value) 시계열 데이터** 를 효율적으로 저장·압축·집계·만료시킵니다. RDB 로 다루면 인덱스 폭증·집계 느림.

**메커니즘**:
- **Column-oriented + chunked**: timestamp 정렬 column, 시간 chunk 단위 분할
- **Compression**: Gorilla (Facebook) / delta-of-delta / zstd — 10:1 ~ 100:1 압축
- **Downsampling (continuous aggregates)**: raw 1s → 1m mean, 1m → 1h mean, 1h → 1d mean. 오래된 데이터는 raw 폐기, aggregate 만 보존
- **Retention policy**: 1s raw 7일, 1m 90일, 1h 영구 — 비용·query 균형
- **Tag-based indexing**: `device_id`, `region`, `firmware_version` 같은 cardinality 낮은 tag 만 index, value 는 index 안 함
- **Out-of-order writes**: 디바이스 시계 어긋남·offline upload — TSDB 는 일정 lateness 허용

**장점**:
- 압축률 압도적 (수십 배) → 저장 비용 절감
- Aggregate query 빠름 (chunk 메타 만 읽고 skip)
- Retention 자동화 — 운영 부담 감소

**단점·주의**:
- High-cardinality tag (예: user_id) 폭주 시 인덱스 폭발 — InfluxDB v1 의 고질병
- Out-of-order write 의 lateness 한계 — 너무 오래된 데이터는 reject (별도 backfill API)
- Schema 변경 어려움 (tag/field 추가는 OK, 기존 변경 어려움)
- TSDB 별로 SQL/PromQL/Flux 등 query 언어 상이

**표준 매핑**:
- **InfluxDB** (open source, Flux/InfluxQL)
- **TimescaleDB** (PostgreSQL extension, hypertable + continuous aggregate)
- **AWS Timestream** — managed, separate hot/cold tier
- **Prometheus** (metrics 중심, scrape pull model — IoT 보다 모니터링)
- **VictoriaMetrics** (Prometheus 호환, high-cardinality 강점)
- **Apache IoTDB** — IoT 특화 (Apache TLP, 2020)

**SQL 예제** (TimescaleDB — hypertable + continuous aggregate):
```sql
-- 1) Hypertable 생성 — 시간 chunk 자동 분할
CREATE TABLE telemetry (
    ts          TIMESTAMPTZ NOT NULL,
    device_id   TEXT        NOT NULL,
    metric      TEXT        NOT NULL,
    value       DOUBLE PRECISION
);
SELECT create_hypertable('telemetry', 'ts', chunk_time_interval => INTERVAL '1 day');

-- 2) 인덱스 — tag 만 (value 는 인덱스 안 함)
CREATE INDEX ON telemetry (device_id, metric, ts DESC);

-- 3) 압축 정책 — 7 일 이후 column-oriented + Gorilla 압축
ALTER TABLE telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id, metric'
);
SELECT add_compression_policy('telemetry', INTERVAL '7 days');

-- 4) Continuous aggregate — 1 분 평균 자동 유지
CREATE MATERIALIZED VIEW telemetry_1m
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 minute', ts) AS minute,
       device_id, metric,
       avg(value)   AS avg_v,
       max(value)   AS max_v,
       count(*)     AS n
FROM telemetry
GROUP BY 1, 2, 3;

-- 5) Retention — raw 90 일, aggregate 2 년
SELECT add_retention_policy('telemetry',    INTERVAL '90 days');
SELECT add_retention_policy('telemetry_1m', INTERVAL '2 years');

-- 6) Query: 지난 1 시간 평균 + 95p
SELECT time_bucket('5 minutes', ts) AS bucket,
       device_id,
       avg(value)                                  AS avg_v,
       approx_percentile(0.95, percentile_agg(value)) AS p95_v
FROM telemetry
WHERE metric = 'vibration_rms'
  AND ts > now() - INTERVAL '1 hour'
GROUP BY 1, 2
ORDER BY 1 DESC;
```

**관련 패턴**: Telemetry Buffer, Edge Gateway (aggregation 후 cloud 적재), CQRS (read 측)

---

## 9. Command & Control (C2) — 명령·제어 채널

<a id="command-control"></a>

**목적**: 클라우드/앱에서 **개별 디바이스로 명령을 역방향 전송** 하고 ACK·결과를 회수합니다. Twin 은 desired state 동기화용, C2 는 즉각·일회성 명령용 (reboot, run_diagnostic, take_snapshot).

**메커니즘**:
- **Request/Response correlation**: `request_id` UUID 동봉, 응답 토픽 `devices/{id}/cmd/resp` 로 회수
- **Idempotency**: 동일 `request_id` 는 한 번만 실행, dedup window 유지 (24h~7d)
- **ACK 단계**: receive-ACK (디바이스 수신 확인) → execute-ACK (실행 완료) — UX 와 retry 정책에 활용
- **Retry with backoff**: 디바이스 offline 또는 ACK timeout 시 exponential backoff
- **Reverse-connect (long polling / SSE / MQTT subscribe)**: 디바이스가 outbound TCP 만 사용 (방화벽·NAT 통과)
- **Time-bounded**: 명령에 `expiresAt` — 만료 후 디바이스가 reconnect 해도 무시 (오래된 reboot 명령 방지)

**장점**:
- 양방향 통신 — 사용자가 앱에서 즉시 디바이스 제어
- 명령 추적 가능 (request_id 로 상태 조회)
- 디바이스가 outbound only — 보안 우호

**단점·주의**:
- ACK timeout 정의 어려움 (네트워크 변동성) — 보수적으로 설정
- 동일 `request_id` 중복 도착 처리 필수 (At-least-once 채널)
- 디바이스 long offline 시 명령 누적 — TTL + 우선순위 (latest-wins) 정책
- 보안: 명령은 디바이스 행동 변경 → 반드시 서명 또는 mTLS 인증된 채널만

**표준 매핑**:
- **AWS IoT Jobs** — 명령 큐 + 진행 상태 추적 (QUEUED → IN_PROGRESS → SUCCEEDED / FAILED / TIMED_OUT)
- **Azure IoT Hub Direct Methods** — 요청-응답 동기 호출 (디바이스 online 시만)
- **Azure IoT Hub Cloud-to-Device Messages** — 디바이스 offline 시 큐잉 (TTL 지원)
- **LwM2M Execute Operation** (Object/Instance/Resource 실행)

**JSON 예제** (AWS IoT Job document — reboot 명령):
```json
{
  "version": "1.0",
  "operation": "reboot",
  "parameters": {
    "mode": "graceful",
    "delay_seconds": 30
  },
  "requestId": "0b8e1c2a-5f4e-4d3c-8b7a-1a2b3c4d5e6f",
  "expiresAt": "2026-05-14T12:00:00Z",
  "stepTimeoutInMinutes": 5,
  "rollbackConfig": {
    "rollbackOnFailure": false
  }
}
```

**Kotlin 예제** (디바이스 측 — MQTT 명령 수신 + idempotency + ACK):
```kotlin
class CommandHandler(private val mqtt: MqttClient, private val deviceId: String) {

    private val processedRequests = LruCache<String, ExecutionResult>(maxSize = 256)

    fun start() {
        mqtt.subscribe("devices/$deviceId/cmd/req", qos = 1) { msg ->
            val cmd = Json.decodeFromString<Command>(msg.payload.decodeToString())

            // 1) Expiry 확인
            if (Instant.now() > cmd.expiresAt) {
                ackTimeout(cmd.requestId); return@subscribe
            }
            // 2) Idempotency
            processedRequests[cmd.requestId]?.let {
                ackResult(cmd.requestId, it); return@subscribe
            }
            // 3) Receive ACK (실행 시작 직전)
            mqtt.publish("devices/$deviceId/cmd/resp",
                Json.encodeToString(Ack.received(cmd.requestId)).toByteArray(),
                qos = 1)
            // 4) 실행 (블로킹 작업은 별도 코루틴/큐)
            val result = try {
                when (cmd.operation) {
                    "reboot"        -> performReboot(cmd.parameters)
                    "run_diagnostic"-> runDiagnostic(cmd.parameters)
                    "take_snapshot" -> captureSnapshot(cmd.parameters)
                    else            -> ExecutionResult.unsupported(cmd.operation)
                }
            } catch (e: Throwable) {
                ExecutionResult.failure(e.message ?: "unknown")
            }
            // 5) Execute ACK + dedup 캐시
            processedRequests.put(cmd.requestId, result)
            ackResult(cmd.requestId, result)
        }
    }

    private fun ackResult(requestId: String, result: ExecutionResult) {
        mqtt.publish("devices/$deviceId/cmd/resp",
            Json.encodeToString(Ack.completed(requestId, result)).toByteArray(),
            qos = 1)
    }
}
```

**관련 패턴**: Idempotency Key, MQTT Pub-Sub, Device Twin (장기 state 동기화 vs 일회성 명령 분리)

---

## 10. Device Identity & Mutual TLS — 디바이스 아이덴티티

<a id="device-mtls"></a>

**목적**: 각 디바이스가 **고유 cert + private key** 로 클라우드에 mTLS 인증하여 spoofing·MITM 차단. fleet 침해 시 단일 디바이스만 revoke 가능. 가능한 한 **hardware-backed key (TPM / Secure Element / TrustZone)** 저장.

**메커니즘**:
- **Per-device X.509 cert**: 제조 시 또는 first-boot provisioning 으로 발급
- **Root CA hierarchy**: Root CA (offline HSM) → Intermediate CA (online) → Device cert. Root 만 디바이스에 박음
- **Hardware key storage**:
  - **TPM 2.0** (PC, 서버) — endorsement key + attestation
  - **Secure Element** (ATECC608, NXP SE050) — MCU 외장, I²C
  - **ARM TrustZone TEE** (Cortex-A) / **PSA Crypto** (Cortex-M)
  - **Apple Secure Enclave / Android Strongbox**
- **Cert rotation**: 1~2년 cycle, 디바이스가 online 일 때 rolling rotation (EST renewal)
- **Revocation**: CRL 또는 OCSP — IoT 는 cloud 측 deny-list 가 실용적
- **Attestation**: secure boot chain 측정값을 cert 발급 시 검증 (TPM quote, Secure Element 의 device unique key)

**장점**:
- Spoofing 차단 — private key 가 hardware 밖으로 나가지 않음
- 침해 시 단일 device 만 revoke (PSK 단일 키 대비 격리)
- mTLS 는 application layer 보안과 독립 (decoupled)

**단점·주의**:
- 하드웨어 비용 (Secure Element ~$0.5-2 per unit) — BOM 영향
- Cert lifecycle 관리 인프라 필요 (PKI, OCSP responder)
- Cert expiry 시 디바이스 brick 위험 — rotation 자동화 필수
- Root CA 침해는 fleet 전체 종말 — offline HSM, key ceremony 엄격 운영

**표준 매핑**:
- **X.509 v3** (RFC 5280) + **TLS 1.3 mutual auth** (RFC 8446)
- **IEEE 802.1AR — Secure Device Identity (DevID)** — 영구 IDevID + 갱신 LDevID
- **NIST SP 800-213A** — IoT Device Cybersecurity Capability Core Baseline
- **TPM 2.0** (ISO/IEC 11889), **PSA Certified Level 2/3** (Arm)
- **DICE (Device Identifier Composition Engine)** — TCG, MCU 용 hardware identity

**Kotlin 예제** (디바이스 측 — Android Keystore Strongbox + mTLS):
```kotlin
class DeviceIdentity(private val ctx: Context, private val alias: String) {

    /** 첫 부팅 시 1회 — hardware-backed keypair 생성 (export 불가) */
    fun generateIfNeeded(): X509Certificate {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        if (ks.containsAlias(alias)) return ks.getCertificate(alias) as X509Certificate

        val spec = KeyGenParameterSpec.Builder(alias,
                KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY)
            .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
            .setDigests(KeyProperties.DIGEST_SHA256)
            .setIsStrongBoxBacked(true)               // hardware-backed
            .setAttestationChallenge(randomChallenge()) // key attestation 활성화
            .build()

        val kpg = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore")
        kpg.initialize(spec); kpg.generateKeyPair()
        return ks.getCertificate(alias) as X509Certificate
    }

    /** CSR 생성 → 클라우드 EST 로 cert 발급 받기 */
    suspend fun enrollViaEst(estClient: EstClient): X509Certificate {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val privateKey = ks.getKey(alias, null) as PrivateKey
        val pubCert    = ks.getCertificate(alias) as X509Certificate
        val csr = JcaPKCS10CertificationRequestBuilder(
                X500Name("CN=${Build.SERIAL}, O=ExampleCo"),
                pubCert.publicKey)
            .build(JcaContentSignerBuilder("SHA256withECDSA").build(privateKey))
        return estClient.simpleEnroll(csr)            // RFC 7030
    }

    /** mTLS 로 IoT Hub 연결 */
    fun mtlsHttpClient(deviceCert: X509Certificate, caChain: Array<X509Certificate>): OkHttpClient {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm())
        kmf.init(ks, null)                            // private key 는 KeyStore 가 sign 만 노출, 추출 불가
        val tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm())
            .apply { init(trustStoreOf(caChain)) }
        val sslCtx = SSLContext.getInstance("TLSv1.3").apply {
            init(kmf.keyManagers, tmf.trustManagers, SecureRandom())
        }
        return OkHttpClient.Builder()
            .sslSocketFactory(sslCtx.socketFactory, tmf.trustManagers[0] as X509TrustManager)
            .build()
    }
}
```

**관련 패턴**: Device Provisioning (cert 발급), OTA Firmware (서명 키와 별도 PKI), MQTT Pub-Sub (mTLS over TLS 1.3)

---
