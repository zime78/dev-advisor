# 블록체인/Web3 패턴 (Blockchain & Web3 Patterns)

블록체인 운영·스마트 컨트랙트의 정평 있는 10 패턴. Ethereum / Solana / Bitcoin / Cosmos / Polkadot 사례.

**원전·표준 참고**:
- Satoshi Nakamoto — *Bitcoin: A Peer-to-Peer Electronic Cash System* (2008)
- Vitalik Buterin — Ethereum Yellow Paper
- ERC standards (https://eips.ethereum.org)
- OpenZeppelin Contracts — Upgrade pattern (Transparent/UUPS), Multi-sig
- Chainlink — Decentralized Oracle Network
- Flashbots — MEV research
- The Graph — Subgraph specification

**핵심 비기능 요구**:
- **불변성 (Immutability)** — 한 번 commit 된 트랜잭션은 변경 불가
- **합의 (Consensus)** — 분산 노드 간 단일 ledger 합의 (algorithms/consensus.md cross-link)
- **gas 비용** — 모든 연산이 비용 (storage > compute), 최적화 압력
- **공격 표면** — reentrancy / front-running / oracle manipulation 등 고유 취약점

**관련 카탈로그**:
- [`../algorithms/consensus.md`](../algorithms/consensus.md) — Paxos / Raft / 2PC (전통 합의)
- [`../algorithms/crypto.md`](../algorithms/crypto.md) — SHA-256 / RSA / AES
- [`../security/security-crypto-ops.md`](../security/security-crypto-ops.md) — KMS / HSM / Key Ceremony
- [distributed.md](distributed.md) — Idempotency / Saga

---

<a id="consensus-blockchain"></a>

## 1. Consensus Mechanism 비교 (PoW / PoS / PBFT / DPoS / PoA)

**목적**: 분산 노드들이 단일 ledger 상태에 합의하는 알고리즘. 블록체인의 가장 근본 패턴으로, 보안·탈중앙성·확장성의 트릴레마(Trilemma)를 결정합니다.

**메커니즘**:
- **PoW (Proof of Work)**: 채굴자가 SHA-256 nonce 탐색으로 블록 제안권 획득 (Bitcoin)
- **PoS (Proof of Stake)**: 스테이킹된 토큰 양에 비례해 validator 선출 (Ethereum 2.0 / Cosmos)
- **PBFT (Practical Byzantine Fault Tolerance)**: 3단계 voting(pre-prepare/prepare/commit)으로 즉시 finality (Hyperledger Fabric)
- **DPoS (Delegated PoS)**: 토큰 홀더가 21~101명의 witness/delegate 투표 (EOS / TRON)
- **PoA (Proof of Authority)**: 사전 허가된 validator 집합 (private chain / sidechain)

**장점**:
- **PoW**: 검증된 보안 모델 (15년+ 운영), 낮은 가정(공격자 < 51% hashrate)
- **PoS**: 에너지 효율 99.95% 절감, 빠른 finality (12분 in Ethereum)
- **PBFT**: 즉시 finality, 결정론적 합의, 높은 TPS
- **DPoS**: 높은 처리량, 거버넌스 명시화
- **PoA**: 매우 높은 TPS, 운영 단순

**단점·공격 표면**:
- **PoW**: 막대한 에너지 소비, 51% 공격, mining centralization
- **PoS**: Nothing-at-Stake / Long Range Attack, 부의 집중
- **PBFT**: O(n²) 통신, n ≤ ~100 제약
- **DPoS**: vote buying, delegate cartel 위험
- **PoA**: 탈중앙성 거의 없음, validator 담합

**활용 예시**:
- PoW: Bitcoin, Litecoin, Ethereum Classic
- PoS: Ethereum (Merge 2022), Cardano, Polkadot
- PBFT 변종: Hyperledger Fabric, Tendermint(Cosmos), HotStuff
- DPoS: EOS, TRON, Steem
- PoA: VeChain, Binance Smart Chain (PoSA)

**난이도**: 매우 높음 | **사용 빈도**: ★★★★★

**pseudo-code 예제** (PoW 채굴 vs PoS 선출 비교):
```kotlin
// PoW: nonce brute-force until hash < target
fun mine(blockHeader: ByteArray, target: BigInteger): Long {
    var nonce = 0L
    while (true) {
        val hash = sha256(sha256(blockHeader + nonce.toBytes()))
        if (BigInteger(1, hash) < target) return nonce
        nonce++
    }
}

// PoS: pseudo-random validator selection weighted by stake
fun selectValidator(validators: List<Validator>, randao: ByteArray): Validator {
    val totalStake = validators.sumOf { it.stake }
    val seed = BigInteger(1, randao).mod(BigInteger.valueOf(totalStake))
    var cumulative = 0L
    for (v in validators) {
        cumulative += v.stake
        if (seed < BigInteger.valueOf(cumulative)) return v
    }
    error("unreachable")
}
```

**관련 패턴**: [Layer 2 Scaling](#layer-2-scaling), [Smart Contract Upgrade](#smart-contract-upgrade), `../algorithms/consensus.md` (Paxos/Raft)

---

<a id="smart-contract-upgrade"></a>

## 2. Smart Contract Upgrade (Proxy Pattern)

**목적**: 스마트 컨트랙트의 불변성(immutable bytecode)을 우회하여 로직 버그 수정·기능 추가를 가능하게 합니다. Proxy가 storage를 보유하고 `delegatecall`로 implementation 컨트랙트의 함수를 호출합니다.

**메커니즘**:
- **Transparent Proxy (EIP-1967)**: Admin 주소가 upgrade 호출, 일반 user는 fallback으로 delegatecall. Admin/user 함수 분리
- **UUPS (Universal Upgradeable Proxy, EIP-1822)**: upgrade 로직이 implementation에 위치 → proxy gas 비용 감소
- **Diamond (EIP-2535)**: 여러 facet 컨트랙트로 분할, 함수별 라우팅 → 24KB 컨트랙트 크기 한도 우회
- **Beacon Proxy**: 여러 proxy가 한 beacon을 공유, beacon 한 번 upgrade로 전체 갱신

**Transparent vs UUPS 비교**:

| 항목 | Transparent | UUPS |
|---|---|---|
| Upgrade 로직 위치 | Proxy | Implementation |
| Proxy gas 비용 | 더 비쌈 (admin check) | 더 저렴 |
| Implementation 위험 | 낮음 | upgradeTo 누락 시 lock |
| Storage 충돌 | 슬롯 분리 (EIP-1967) | 동일 |

**장점**:
- 버그 fix, 기능 추가 가능
- Storage 보존
- 주소 고정 (사용자 친화)

**단점·공격 표면**:
- **Centralization risk** — admin key 탈취 시 전체 자금 위험
- **Storage collision** — 신구 implementation의 storage layout 불일치 시 데이터 손상
- **Function selector clash** — Transparent proxy에서 admin·user 함수 selector 충돌
- **Uninitialized implementation** — proxy 외부에서 implementation 직접 호출하여 takeover
- 진정한 immutability 상실 → "코드가 법(Code is Law)" 원칙 위반

**활용 예시**:
- OpenZeppelin Upgrades Plugin (Hardhat/Foundry)
- Compound, Aave (UUPS)
- USDC, USDT (Transparent)
- Diamond: Aavegotchi, OpenSea Seaport

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Solidity 예제** (UUPS 패턴):
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";

contract MyTokenV1 is UUPSUpgradeable, OwnableUpgradeable {
    uint256 public totalSupply;

    function initialize() public initializer {
        __Ownable_init(msg.sender);
        __UUPSUpgradeable_init();
        totalSupply = 1_000_000 ether;
    }

    // upgrade authority — only owner
    function _authorizeUpgrade(address newImpl) internal override onlyOwner {}
}

// V2 must preserve V1 storage layout, then append new state
contract MyTokenV2 is MyTokenV1 {
    mapping(address => uint256) public balanceOf; // appended at next slot
    function mint(address to, uint256 amt) external onlyOwner {
        balanceOf[to] += amt;
        totalSupply += amt;
    }
}
```

**관련 패턴**: [Custody](#custody-mpc-multisig) (multi-sig admin), [Gas Optimization](#gas-optimization) (storage slot)

---

<a id="oracle-pattern"></a>

## 3. Oracle Pattern

**목적**: 스마트 컨트랙트는 결정론적이어야 하므로 외부 데이터(주가, 환율, 날씨, 스포츠 결과)를 직접 읽을 수 없습니다. Oracle은 off-chain 데이터를 on-chain으로 가져오는 신뢰 계층입니다.

**메커니즘**:
- **Centralized Oracle**: 단일 노드가 데이터 보고 (단일 신뢰점)
- **Decentralized Oracle Network (DON)**: 다수 노드가 보고 → median/aggregation 으로 합의 (Chainlink)
- **Optimistic Oracle**: 누구나 데이터 제출, 분쟁 시 dispute resolution (UMA)
- **Push vs Pull**: heartbeat마다 자동 update (push) / 컨트랙트가 요청 시 (pull)

**구성 요소**:
- Off-chain data source (CEX API, weather feed)
- Off-chain reporter nodes
- On-chain aggregator contract
- Consumer contract (Oracle 가격 읽음)

**장점**:
- DeFi 가격 피드 가능 → 대출/파생상품 시장
- 보험·예측시장 → 외부 이벤트 트리거
- 무작위성 공급 (Chainlink VRF)

**단점·공격 표면**:
- **Oracle manipulation** — TWAP 부재 시 단일 블록 가격 조작 (flash loan + DEX) → 대출 프로토콜 청산
- **Stale data** — heartbeat 실패 시 오래된 가격 사용 (Cream Finance 사건)
- **Centralization** — DON 노드 담합 위험
- **Cost** — 모든 update가 gas 소비 → 빈도 vs 비용 트레이드오프

**활용 예시**:
- Chainlink Price Feeds (BTC/USD, ETH/USD 등)
- Pyth Network (Solana, low-latency price)
- Band Protocol
- UMA Optimistic Oracle
- Chainlink VRF (lottery, NFT mint randomness)

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Solidity 예제** (Chainlink Price Feed 소비):
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface AggregatorV3Interface {
    function latestRoundData() external view returns (
        uint80 roundId, int256 answer, uint256 startedAt,
        uint256 updatedAt, uint80 answeredInRound);
    function decimals() external view returns (uint8);
}

contract PriceConsumer {
    AggregatorV3Interface public immutable feed;
    uint256 public constant STALENESS_THRESHOLD = 3600; // 1h

    constructor(address _feed) { feed = AggregatorV3Interface(_feed); }

    function ethUsdPrice() public view returns (uint256 price) {
        (, int256 answer,, uint256 updatedAt,) = feed.latestRoundData();
        require(answer > 0, "negative price");
        require(block.timestamp - updatedAt < STALENESS_THRESHOLD, "stale");
        // normalize to 18 decimals
        price = uint256(answer) * 10 ** (18 - feed.decimals());
    }
}
```

**관련 패턴**: [MEV](#mev) (oracle front-run), [Cross-chain Bridge](#cross-chain-bridge) (bridge oracle)

---

<a id="gas-optimization"></a>

## 4. Gas Optimization

**목적**: EVM의 모든 연산은 gas 비용을 발생시키며, storage 쓰기가 가장 비쌉니다(SSTORE=20,000 gas). 컨트랙트 설계 시 슬롯 packing, calldata 활용, opcode 선택으로 사용자 비용을 절감합니다.

**메커니즘**:
- **Storage slot packing**: 같은 32-byte 슬롯에 여러 작은 변수 묶기 (uint128 + uint128, bool + address)
- **calldata vs memory**: 외부 함수 인자에 `calldata` 사용 (복사 없음)
- **uint256 선호**: uint8/uint16은 EVM word boundary 처리로 오히려 비쌀 수 있음 (구조체 내 packing 제외)
- **Short-circuit ordering**: `require(cheap && expensive)`
- **Unchecked arithmetic** (Solidity 0.8+): overflow 검사 생략으로 ~30 gas 절감
- **Custom errors** (0.8.4+): `revert "string"` 대비 ~50 gas 절감
- **Events for off-chain data**: storage 대신 indexed event 사용
- **Bitmap**: bool 배열 → uint256 비트 사용 (256배 압축)

**Gas 비용 위계** (대략):
| 연산 | Gas | 비고 |
|---|---|---|
| SSTORE (0→non-zero) | 20,000 | 가장 비쌈 |
| SSTORE (non-zero→non-zero) | 5,000 | |
| SLOAD | 2,100 (cold) / 100 (warm) | EIP-2929 |
| CALL | 700+ | |
| LOG (event) | 375 + 8/byte | storage 대비 매우 저렴 |
| ADD / MUL | 3-5 | |

**장점**:
- 사용자 트랜잭션 비용 절감 → 채택률 증가
- 블록 한도 내 더 많은 로직 가능

**단점**:
- 가독성 저하 (bitmap, assembly)
- 버그 위험 증가 (unchecked overflow)
- 유지보수 비용

**활용 예시**:
- ERC-721A (Azuki) — 배치 mint storage 최적화
- Uniswap V3 — concentrated liquidity packed structs
- Solady library — assembly-optimized utilities

**난이도**: 중간~높음 | **사용 빈도**: ★★★★★

**Solidity 예제** (slot packing + calldata + custom error):
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Bad: 3 slots used
contract Unoptimized {
    uint128 a;   // slot 0
    uint256 b;   // slot 1 (uint128 + uint256 cannot pack)
    uint128 c;   // slot 2
}

// Good: 2 slots used (a + c packed into slot 0)
contract Optimized {
    uint128 a;   // slot 0 (low)
    uint128 c;   // slot 0 (high) — packed
    uint256 b;   // slot 1

    error InsufficientBalance(uint256 have, uint256 want);

    function transfer(address[] calldata to, uint256 amt) external {
        // calldata avoids memory copy; unchecked saves gas when overflow impossible
        uint256 len = to.length;
        unchecked {
            for (uint256 i = 0; i < len; ++i) {
                if (b < amt) revert InsufficientBalance(b, amt);
                b -= amt;
            }
        }
    }
}
```

**관련 패턴**: [Smart Contract Upgrade](#smart-contract-upgrade) (storage layout), [Layer 2 Scaling](#layer-2-scaling) (off-chain compute)

---

<a id="custody-mpc-multisig"></a>

## 5. Custody (Self / MPC / Multi-sig)

**목적**: 개인 키(private key)를 안전하게 관리하여 자산 도난을 방지합니다. 단일 키 단일 실패점(SPOF)을 분산하는 세 가지 모델이 존재합니다.

**메커니즘**:
- **Self-custody**: 사용자가 직접 키 보관 (MetaMask, Ledger hardware wallet)
- **Multi-sig (M-of-N)**: N 개 키 중 M 개 서명 필요 (Gnosis Safe). 각 서명이 on-chain 검증
- **MPC (Multi-Party Computation)**: 단일 키를 N 조각으로 분산, threshold 조합으로 서명 생성 (Fireblocks). On-chain은 단일 서명으로 보임 (off-chain MPC)
- **Smart Contract Wallet (ERC-4337)**: 컨트랙트 자체가 지갑, social recovery / gas sponsorship 지원

**비교**:

| 항목 | Self | Multi-sig | MPC |
|---|---|---|---|
| On-chain 흔적 | 단일 서명 | N 서명 (gas 비쌈) | 단일 서명 (저렴) |
| Recovery | seed phrase | M-of-N 서명 | shard re-sharing |
| 프라이버시 | 평범 | 낮음 (서명자 공개) | 높음 |
| 호환성 | 모든 체인 | 체인별 컨트랙트 | 모든 체인 (off-chain) |
| 구현 난이도 | 낮음 | 중간 | 매우 높음 |

**장점**:
- **Self**: 완전 자율, 0 trust
- **Multi-sig**: 명시적 거버넌스 (DAO treasury)
- **MPC**: gas 효율 + 프라이버시 + chain-agnostic

**단점·공격 표면**:
- **Self**: seed phrase 분실/탈취 → 영구 손실
- **Multi-sig**: signer 담합, signer set 변경 복잡, gas 비용
- **MPC**: shard 동시 탈취, MPC 구현 버그 (학술적으로 더 어려움)
- **ERC-4337 wallet**: 컨트랙트 버그, paymaster 의존

**활용 예시**:
- Self: MetaMask, Trust Wallet, Ledger
- Multi-sig: Gnosis Safe (DAO/기업 표준), Bitcoin multi-sig
- MPC: Fireblocks (institutional), Coinbase Custody, ZenGo
- ERC-4337: Argent, Safe{Wallet} v1.4+

**난이도**: 중간 (Self) ~ 매우 높음 (MPC) | **사용 빈도**: ★★★★★

**Solidity 예제** (M-of-N Multi-sig 핵심):
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MultiSig {
    address[] public owners;
    uint256 public threshold; // M
    uint256 public nonce;

    constructor(address[] memory _owners, uint256 _threshold) {
        require(_threshold > 0 && _threshold <= _owners.length, "bad M");
        owners = _owners;
        threshold = _threshold;
    }

    function execute(
        address to, uint256 value, bytes calldata data,
        bytes[] calldata signatures
    ) external {
        bytes32 hash = keccak256(abi.encode(to, value, data, nonce++, block.chainid));
        require(signatures.length >= threshold, "not enough sigs");

        address prev;
        for (uint256 i = 0; i < threshold; ++i) {
            address signer = recover(hash, signatures[i]);
            require(_isOwner(signer) && signer > prev, "bad signer or dup");
            prev = signer; // enforce strictly ascending → no duplicates
        }
        (bool ok,) = to.call{value: value}(data);
        require(ok, "exec failed");
    }

    function recover(bytes32 h, bytes memory sig) internal pure returns (address) { /* ecrecover */ }
    function _isOwner(address a) internal view returns (bool) { /* loop */ }
}
```

**관련 패턴**: [Smart Contract Upgrade](#smart-contract-upgrade) (multi-sig as admin), `../security/security-crypto-ops.md` (HSM, Key Ceremony)

---

<a id="event-indexer-graph"></a>

## 6. Event Indexer (The Graph)

**목적**: 스마트 컨트랙트는 GraphQL/SQL 같은 query를 직접 지원하지 않습니다. RPC `eth_getLogs`로는 복잡한 join/aggregation 불가능. Event Indexer는 on-chain event를 off-chain DB로 색인하여 GraphQL queryable 하게 만듭니다.

**메커니즘**:
1. 컨트랙트가 `event Transfer(address indexed from, address indexed to, uint256 value)` emit
2. Subgraph가 RPC `eth_subscribe`로 event 수신
3. `mapping.ts`(AssemblyScript)에서 event → entity 변환
4. Postgres 색인 → GraphQL endpoint 노출
5. Frontend가 GraphQL query

**구성 요소**:
- `subgraph.yaml` — manifest (컨트랙트 주소, ABI, event handler 매핑)
- `schema.graphql` — entity 정의 (User, Transaction, Pool 등)
- `mapping.ts` — event → entity 변환 로직

**장점**:
- 복잡한 query (join, aggregation, pagination) 가능
- Frontend 응답 속도 향상 (RPC 직접 호출 대비 100배+)
- 탈중앙 indexer 네트워크(The Graph hosted vs decentralized)
- 재조직(reorg) 처리 자동

**단점·공격 표면**:
- Sync 지연 (수십 초~분, finality 대기)
- Indexer 운영 비용 (Postgres + node)
- Event 누락 시 재색인 필요 (full resync)
- 신뢰 모델 — hosted Graph는 중앙화

**활용 예시**:
- The Graph (decentralized indexing protocol)
- Goldsky, Subsquid, Ponder (alternative indexers)
- Uniswap subgraph (TVL, volume, pool stats)
- OpenSea collection indexer

**난이도**: 중간 | **사용 빈도**: ★★★★★

**pseudo-code 예제** (Subgraph mapping):
```typescript
// schema.graphql
// type Transfer @entity {
//   id: ID!
//   from: Bytes!
//   to: Bytes!
//   value: BigInt!
//   timestamp: BigInt!
// }

// mapping.ts (AssemblyScript)
import { Transfer as TransferEvent } from "../generated/Token/Token";
import { Transfer } from "../generated/schema";

export function handleTransfer(event: TransferEvent): void {
    const id = event.transaction.hash.toHex() + "-" + event.logIndex.toString();
    const entity = new Transfer(id);
    entity.from = event.params.from;
    entity.to = event.params.to;
    entity.value = event.params.value;
    entity.timestamp = event.block.timestamp;
    entity.save();
}

// Frontend GraphQL query
// {
//   transfers(where: { from: "0xabc..." }, orderBy: timestamp, orderDirection: desc, first: 50) {
//     to value timestamp
//   }
// }
```

**관련 패턴**: [Gas Optimization](#gas-optimization) (event over storage), [Cross-chain Bridge](#cross-chain-bridge) (multi-chain indexing)

---

<a id="token-standard-erc"></a>

## 7. Token Standard (ERC-20 / ERC-721 / ERC-1155)

**목적**: 표준 인터페이스 덕분에 지갑·DEX·marketplace가 임의 토큰을 자동 인식·처리할 수 있습니다. 토큰의 fungibility(대체가능성)와 batching 요구에 따라 표준 선택.

**비교**:

| 표준 | 명칭 | Fungibility | 식별 | 대표 사례 |
|---|---|---|---|---|
| **ERC-20** | Fungible Token | 완전 대체 가능 | `(address) → balance` | USDC, DAI, UNI |
| **ERC-721** | NFT (Non-Fungible) | 고유 | `tokenId → owner` | CryptoPunks, BAYC |
| **ERC-1155** | Multi-Token | 둘 다 지원 | `(tokenId, address) → balance` | OpenSea, 게임 아이템 |
| **ERC-777** | Advanced Fungible | ERC-20 호환 + hooks | 동일 | Rare (reentrancy 위험) |
| **ERC-4626** | Tokenized Vault | ERC-20 + share/asset 변환 | 동일 | Yearn vaults |

**핵심 인터페이스**:
- ERC-20: `balanceOf`, `transfer`, `transferFrom`, `approve`, `allowance`, `Transfer/Approval` events
- ERC-721: `ownerOf`, `safeTransferFrom`, `approve`, `setApprovalForAll`, `tokenURI`
- ERC-1155: `balanceOfBatch`, `safeBatchTransferFrom`, `setApprovalForAll`

**장점**:
- 지갑/DEX 즉시 호환 (zero integration)
- OpenZeppelin reference implementation 사용 가능
- 메타데이터 표준 (tokenURI → IPFS JSON)

**단점·공격 표면**:
- **ERC-20 approve race**: `approve(spender, 100)` → `approve(spender, 50)` 사이 race로 150 인출 가능 → `permit` (EIP-2612) 또는 `increaseAllowance` 사용
- **ERC-721 reentrancy**: `safeTransferFrom`이 receiver 컨트랙트 콜백 → reentrancy 위험
- **ERC-777 hooks**: tokensToSend/tokensReceived hook → reentrancy 공격 발생 (Cream Finance 2021)
- **Approval phishing**: `setApprovalForAll` 무한 권한 sign → 지갑 drain

**활용 예시**:
- ERC-20: 모든 DeFi 토큰
- ERC-721: NFT collections, ENS 도메인
- ERC-1155: 게임 (Decentraland, Axie Infinity wearables)
- ERC-4626: Yearn, Maple Finance vaults

**난이도**: 낮음 (사용) / 중간 (구현) | **사용 빈도**: ★★★★★

**Solidity 예제** (OpenZeppelin ERC-20 + permit):
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";

contract MyToken is ERC20, ERC20Permit {
    constructor() ERC20("MyToken", "MTK") ERC20Permit("MyToken") {
        _mint(msg.sender, 1_000_000 ether);
    }

    // permit(): EIP-2612 gas-less approval via signature
    //   user signs (owner, spender, value, deadline) off-chain
    //   any relayer submits permit() → no separate approve tx needed
    //   avoids ERC-20 approve race condition
}

// ERC-721 minimal
contract MyNFT {
    mapping(uint256 => address) private _owners;
    mapping(uint256 => string) private _tokenURIs;

    function ownerOf(uint256 tokenId) external view returns (address) {
        return _owners[tokenId];
    }
    function safeTransferFrom(address from, address to, uint256 tokenId) external {
        require(_owners[tokenId] == from, "not owner");
        _owners[tokenId] = to;
        // omitted: ERC-721 receiver hook
    }
}
```

**관련 패턴**: [Smart Contract Upgrade](#smart-contract-upgrade) (upgradable token), [MEV](#mev) (approve front-run)

---

<a id="layer-2-scaling"></a>

## 8. Layer 2 Scaling

**목적**: Ethereum L1의 TPS 한계(~15 TPS)와 높은 gas 비용을 해결하기 위해 트랜잭션을 off-chain에서 실행하고 압축된 결과만 L1에 commit 합니다.

**메커니즘**:
- **Optimistic Rollup**: 모든 tx를 일단 valid 로 가정, 7일 challenge window 동안 fraud proof 제출 가능 (Optimism, Arbitrum)
- **ZK Rollup**: 각 batch마다 zero-knowledge validity proof 생성·검증, 즉시 finality (zkSync Era, StarkNet, Polygon zkEVM, Scroll)
- **Validium**: ZK Rollup + off-chain data availability (낮은 비용, 약한 보안 보장)
- **State Channel**: 양자 간 off-chain tx, 분쟁 시 L1 정산 (Lightning Network for Bitcoin)
- **Plasma**: child chain → root chain (현재 deprecated, Rollup이 대체)
- **Sidechain**: 독립 합의 (Polygon PoS) — 엄밀히 L2 아님 (Ethereum 보안 미상속)

**Optimistic vs ZK 비교**:

| 항목 | Optimistic Rollup | ZK Rollup |
|---|---|---|
| Finality | 7일 (challenge window) | 즉시 (proof 검증 후) |
| Withdrawal | 7일 대기 | 즉시 |
| Proof 비용 | 낮음 (lazy) | 높음 (proof gen ~분 단위) |
| EVM 호환성 | 100% (Bedrock, Nitro) | 부분~완전 (zkEVM Type 1~4) |
| 보안 가정 | 최소 1명 정직 watcher | 수학적 (cryptographic) |

**장점**:
- L1 대비 10~100배 TPS, 10~100배 낮은 gas
- L1 보안 상속 (Rollup의 경우)
- L1 컨트랙트와 messaging 가능 (canonical bridge)

**단점·공격 표면**:
- **Sequencer centralization** — 대부분 단일 sequencer 운영 (검열 위험)
- **Data Availability** — L1 calldata 비용 (EIP-4844 blob으로 완화)
- **Bridge risk** — L1↔L2 bridge 컨트랙트 버그 (Wormhole / Nomad hacks)
- **ZK proof bugs** — circuit 구현 오류 시 false validity

**활용 예시**:
- Optimistic: Optimism, Arbitrum, Base
- ZK: zkSync Era, StarkNet, Polygon zkEVM, Scroll, Linea
- App-specific Rollup: dYdX v4, Immutable X (gaming NFT)

**난이도**: 매우 높음 | **사용 빈도**: ★★★★★

**pseudo-code 예제** (L1 ↔ L2 messaging 흐름):
```
L1 ----------------- L2
                     |
User: deposit 1 ETH  |
  → L1 Bridge        |
    (lock 1 ETH)     |
  → emit DepositMsg  |
                     |
Sequencer: sees msg  → mint 1 ETH on L2
                     → user spends on L2 (cheap)
                     |
User: withdraw 0.5 ETH on L2
                     → burn 0.5 ETH on L2
                     → emit WithdrawMsg
                     |
[Optimistic: wait 7d]
[ZK: wait proof ~hours]
                     |
User: claim on L1    |
  → L1 Bridge        |
    (release 0.5 ETH)|
```

```solidity
// L2 contract emits message; L1 verifier (rollup contract) processes after challenge/proof
interface IL2Bridge {
    function withdraw(address l1Token, uint256 amount) external;
    // ↑ on L2: burn + emit MessageSent
}

interface IL1Bridge {
    function finalizeWithdrawal(
        address user, uint256 amount, bytes calldata proof
    ) external; // verifies proof, releases L1 funds
}
```

**관련 패턴**: [Consensus](#consensus-blockchain), [Cross-chain Bridge](#cross-chain-bridge), [Gas Optimization](#gas-optimization)

---

<a id="mev"></a>

## 9. MEV (Maximal Extractable Value)

**목적**: 블록 제안자(miner/validator/sequencer)는 mempool의 pending tx를 보고 tx 순서를 재배치하여 추가 수익을 추출할 수 있습니다. MEV는 이로 인한 가치 추출의 상한선을 의미합니다.

**MEV 공격 유형**:
- **Front-running**: victim의 큰 swap을 보고 그 앞에 같은 swap 삽입 → 가격 슬리피지로 victim 손실, attacker 이익
- **Sandwich attack**: front-run + back-run 동시. (1) attacker가 토큰 매수 → (2) victim의 swap이 가격 push → (3) attacker가 매도하여 차익
- **Back-running**: 청산 가능한 포지션·oracle update 직후 빠르게 청산
- **Time-bandit attack**: 채굴자가 과거 블록 재조직하여 큰 MEV 추출 (수익 > 블록 보상일 때)
- **JIT (Just-In-Time) liquidity**: Uniswap V3에서 큰 swap 직전 liquidity 추가 → fee 가로채기 → 직후 제거

**해결책 (Fair Ordering)**:
- **Flashbots / MEV-Boost**: builder/proposer 분리 (PBS), private mempool로 front-run 차단
- **Commit-Reveal**: 두 단계 트랜잭션 (commit hash → reveal value)
- **TWAP oracle**: 단일 블록 가격 조작 방어
- **Fair sequencing service**: Chainlink FSS, decentralized sequencer
- **Encrypted mempool**: Shutter Network — threshold encryption으로 mempool 암호화

**장점 (good MEV)**:
- 청산·차익거래는 시장 효율성 (DEX 가격 align)
- DeFi 안정성 (under-collateralized 포지션 신속 청산)

**단점·공격 표면**:
- 사용자 슬리피지 손실 → swap UX 악화
- 채굴자 ↔ searcher gas 경매로 gas 가격 인플레이션
- Time-bandit 시 합의 안정성 위협
- 부정한 ordering으로 신뢰 훼손

**활용 예시**:
- Flashbots Auction (Ethereum)
- MEV-Boost (post-Merge: ~90% validator 사용)
- CoW Swap — batch auction으로 MEV 차단
- 1inch Fusion — RFQ + MEV protection

**난이도**: 매우 높음 | **사용 빈도**: ★★★★★ (모든 DeFi 사용자가 노출)

**pseudo-code 예제** (Sandwich attack 흐름):
```
Mempool 상태:
  [tx_V] victim: swap 10 ETH → USDC (slippage 1%)
                ^
                attacker가 spot

Attacker 액션:
  1. tx_A1: swap N ETH → USDC  (gas 가격 ↑↑, victim보다 먼저)
              ↓ ETH price ↑ pushed
  2. tx_V  : victim swap 실행 (불리한 가격)
              ↓ ETH price ↑↑↑
  3. tx_A2: swap USDC → ETH    (높은 가격으로 매도)

Profit = (3) ETH 수령 − (1) ETH 지출 − gas

방어 (Solidity):
function swap(uint256 amountIn, uint256 minOut) external {
    uint256 out = _doSwap(amountIn);
    require(out >= minOut, "slippage"); // 사용자가 minOut 엄격하게 설정
    // 또는 Flashbots private bundle로 mempool 우회
}
```

**관련 패턴**: [Oracle Pattern](#oracle-pattern) (TWAP), [Consensus](#consensus-blockchain) (PBS), [Layer 2 Scaling](#layer-2-scaling) (sequencer fairness)

---

<a id="cross-chain-bridge"></a>

## 10. Cross-chain Bridge

**목적**: 서로 다른 블록체인(Ethereum ↔ Polygon, Ethereum ↔ Bitcoin, EVM ↔ Solana) 간 자산·메시지를 이동시킵니다. 각 체인은 독립 합의를 가지므로 직접 통신 불가능 → bridge가 신뢰 계층.

**메커니즘**:
- **Lock-and-Mint**: source chain에 lock, destination chain에 wrapped token mint. Unlock 시 burn + release (WBTC, wormhole-wrapped assets)
- **Burn-and-Mint**: source에서 burn, destination에서 native mint (canonical bridge)
- **Liquidity Pool**: 양쪽 체인에 LP, swap-like mechanic (Stargate, Hop Protocol)
- **Atomic Swap**: HTLC(Hash Time-Locked Contract)로 trust-less 1:1 교환 (Bitcoin-Litecoin)

**신뢰 모델**:
- **Native / Canonical** — chain 자체의 bridge (Ethereum→Optimism). L1 보안 상속. 7일 지연
- **External Validator Set** — N 명 validator의 M-of-N 서명 (Wormhole guardians: 19명, Multichain MPC)
- **Light Client** — destination chain이 source chain의 헤더 검증 (IBC in Cosmos, zkBridge)
- **Optimistic** — challenge window (Nomad, before hack)

**장점**:
- 멀티체인 유동성 통합
- 사용자가 체인 간 자산 이동 가능
- App이 멀티체인 deploy → 사용자층 확대

**단점·공격 표면**:
- **Bridge hack** — 가장 큰 공격 표면. 2022년 bridge hack 총 $2.5B+ 손실
  - Ronin Bridge (2022.03): $625M — validator 5-of-9 키 탈취
  - Wormhole (2022.02): $325M — signature verification 버그
  - Nomad (2022.08): $190M — initialization 결함, copy-paste 공격
  - Poly Network (2021.08): $611M (전액 회수) — privilege escalation
- **Wrapped token risk** — wrapped asset은 bridge 신용에 의존, native asset 아님
- **Liveness 위험** — validator offline 시 bridge halt
- **Fragmentation** — 여러 wrapped 버전 공존 (USDC.e, USDC.bridged, native USDC)

**활용 예시**:
- Native: Optimism / Arbitrum / Base canonical bridges (L1↔L2)
- External validator: Wormhole, LayerZero, Axelar
- Light client: Cosmos IBC, Polkadot XCM
- LP: Stargate, Hop, Across, Synapse
- ZK: zkBridge (Polyhedra), Succinct

**난이도**: 매우 높음 | **사용 빈도**: ★★★★☆

**Solidity 예제** (Lock-and-Mint canonical bridge 핵심):
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// L1 side: locks user tokens
contract L1Bridge {
    mapping(address => uint256) public locked;
    event Deposit(address indexed user, address token, uint256 amount, uint64 nonce);

    function deposit(address token, uint256 amount) external {
        IERC20(token).transferFrom(msg.sender, address(this), amount);
        locked[token] += amount;
        emit Deposit(msg.sender, token, amount, _nextNonce());
        // off-chain relayer observes event → submits to L2
    }

    function finalizeWithdrawal(
        address user, address token, uint256 amount, bytes calldata proof
    ) external {
        require(_verifyProof(proof), "invalid proof"); // ZK / fraud proof / validator sig
        locked[token] -= amount;
        IERC20(token).transfer(user, amount);
    }

    function _verifyProof(bytes calldata) internal returns (bool) { /* ... */ }
    function _nextNonce() internal returns (uint64) { /* ... */ }
}

// L2 side: mints wrapped token
contract L2Bridge {
    function finalizeDeposit(address user, uint256 amount, bytes calldata proof) external {
        require(_verifyProof(proof), "invalid proof");
        IWrappedToken(wrapped).mint(user, amount);
    }
    function _verifyProof(bytes calldata) internal returns (bool) { /* ... */ }
}

interface IERC20 { function transfer(address,uint256) external returns (bool); function transferFrom(address,address,uint256) external returns (bool); }
interface IWrappedToken { function mint(address,uint256) external; }
```

**관련 패턴**: [Layer 2 Scaling](#layer-2-scaling), [Custody](#custody-mpc-multisig) (validator multi-sig), [Oracle Pattern](#oracle-pattern) (cross-chain message verification)

---
