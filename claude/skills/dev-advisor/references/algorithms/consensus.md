# 분산 합의 알고리즘 (Distributed Consensus)

여러 노드가 단일 결정에 합의(agreement)하도록 하는 분산 시스템 알고리즘입니다. 실제 구현은 etcd, Zookeeper, Consul, TiKV 등 검증된 시스템을 사용해야 하며, 본 카테고리는 의사코드 + 핵심 상태/메시지 타입 학습용입니다.

**관련 카탈로그**:
- [`../principles/formal-methods.md#model-checking`](../principles/formal-methods.md#model-checking) — Model Checking (Spin/NuSMV/TLC) — 2PC/Paxos/Raft 의 안전성·생존성 정합성 형식 증명 (반례 자동 탐색·구현 회귀 검증)

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [2pc](#2pc) | 2PC (Two-Phase Commit) | 2단계 커밋 | 중간 |
| [paxos](#paxos) | Paxos | Basic / Multi-Paxos | 높음 |
| [raft](#raft) | Raft | 래프트 | 높음 |
| [byzantine-pbft](#byzantine-pbft) | Byzantine Fault Tolerance (PBFT / Byzantine Generals) | 비잔틴 결함 허용 | 높음 |
| [leader-election](#leader-election) | Leader Election (Bully / Ring) | 리더 선출 | 중간 |

---

<a id="2pc"></a>
## 1. 2PC (Two-Phase Commit, 2단계 커밋)

**목적**: 분산 트랜잭션이 모든 참여자에서 원자적으로 커밋되거나 모두 롤백되도록 보장

**시간 복잡도**: O(n) 메시지 - n: 참여자 수

**공간 복잡도**: O(n) 코디네이터, O(1) 참여자

**특징**:
- Phase 1 (Prepare): 코디네이터가 모든 참여자에 prepare 전송, 각 참여자는 YES/NO 응답
- Phase 2 (Commit): 모두 YES면 commit, 하나라도 NO면 abort
- 차단형 (blocking) 프로토콜
- ACID 보장하지만 단일 실패점

**장점**:
- 단순한 의미론
- 데이터베이스 표준 (XA)
- 원자성 보장

**단점**:
- 코디네이터 장애 시 차단
- 참여자 장애 시 무한 대기 (in-doubt)
- 성능 오버헤드
- 네트워크 분할에 약함

**활용 예시**:
- 분산 RDBMS (Oracle, PostgreSQL XA)
- 메시지 큐 트랜잭션
- 분산 파일 시스템
- Saga 패턴의 비교 baseline

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// 메시지 타입
sealed class TwoPCMessage {
    data class Prepare(val txnId: String) : TwoPCMessage()
    data class Vote(val txnId: String, val yes: Boolean, val from: String) : TwoPCMessage()
    data class Commit(val txnId: String) : TwoPCMessage()
    data class Abort(val txnId: String) : TwoPCMessage()
    data class Ack(val txnId: String, val from: String) : TwoPCMessage()
}

// 참여자 상태
enum class ParticipantState { IDLE, PREPARED, COMMITTED, ABORTED }

// 코디네이터 상태
enum class CoordinatorState { INIT, WAIT, COMMIT, ABORT }

// 의사코드 (블로킹 동기 흐름):
// Coordinator:
//   state = WAIT
//   send Prepare to all participants
//   collect votes (timeout 시 NO 간주)
//   if 모든 vote == YES:
//       state = COMMIT
//       persist decision (durable log)
//       send Commit to all
//       wait for Acks
//   else:
//       state = ABORT
//       send Abort to all
//
// Participant:
//   on Prepare:
//       if 로컬 검증 + WAL 기록 성공:
//           state = PREPARED
//           reply YES
//       else:
//           reply NO; state = ABORTED
//   on Commit:
//       apply changes
//       state = COMMITTED
//       reply Ack
//   on Abort:
//       rollback; state = ABORTED
//
// 장애 시나리오:
//   참여자 PREPARED 상태에서 코디네이터 장애 → 영원히 대기 (in-doubt)
//   해법: 3PC, Paxos Commit, Raft 기반 코디네이터
```

**Note**: 실제 시스템은 단독 2PC 회피, Saga / Paxos Commit / Raft 기반 트랜잭션 사용 권장.

**관련 알고리즘**: 3PC, Saga, Paxos Commit

---

<a id="paxos"></a>
## 2. Paxos (Basic / Multi-Paxos)

**목적**: 비동기 메시지 + 일부 노드 장애 환경에서 단일 값에 합의

**시간 복잡도**: O(n) 메시지/round, 정상 시 2 round

**공간 복잡도**: O(1) 결정 값, O(로그) 다중 인스턴스

**특징**:
- 역할: Proposer / Acceptor / Learner
- Phase 1a Prepare(n) → 1b Promise(n, accepted)
- Phase 2a Accept(n, v) → 2b Accepted(n, v)
- 과반수(quorum) 기반 안전성
- Multi-Paxos: 리더 고정 시 Phase 1 생략 가능 → 로그 복제

**장점**:
- 이론적으로 가장 검증됨 (Lamport 증명)
- 비동기 + 장애에 강함
- 다양한 응용

**단점**:
- 이해하기 어려움 (Raft가 등장한 이유)
- 정확히 구현하기 매우 어려움
- 라이브락 가능 (리더 선출 필요)

**활용 예시**:
- Google Chubby
- Spanner의 일관성
- Cassandra LWT
- Microsoft Azure Storage

**난이도**: 높음 | **사용 빈도**: ★★★★☆

**Kotlin 코드**:
```kotlin
// 메시지 타입
sealed class PaxosMessage {
    data class Prepare(val n: Long) : PaxosMessage()
    data class Promise(val n: Long, val acceptedN: Long?, val acceptedV: Any?) : PaxosMessage()
    data class Accept(val n: Long, val v: Any) : PaxosMessage()
    data class Accepted(val n: Long, val v: Any) : PaxosMessage()
}

// Acceptor 상태
data class AcceptorState(
    var minProposal: Long = -1L,
    var acceptedProposal: Long? = null,
    var acceptedValue: Any? = null
)

class PaxosAcceptor(val id: String) {
    val state = AcceptorState()

    fun onPrepare(msg: PaxosMessage.Prepare): PaxosMessage.Promise? {
        if (msg.n > state.minProposal) {
            state.minProposal = msg.n
            return PaxosMessage.Promise(msg.n, state.acceptedProposal, state.acceptedValue)
        }
        return null // 거절 (n이 너무 작음)
    }

    fun onAccept(msg: PaxosMessage.Accept): PaxosMessage.Accepted? {
        if (msg.n >= state.minProposal) {
            state.minProposal = msg.n
            state.acceptedProposal = msg.n
            state.acceptedValue = msg.v
            return PaxosMessage.Accepted(msg.n, msg.v)
        }
        return null
    }
}

// Basic Paxos Proposer 의사코드:
// Phase 1:
//   n = 새로운 고유 제안 번호 (예: (counter, nodeId))
//   send Prepare(n) to acceptors
//   wait for majority Promise responses
//   if 어떤 promise에 acceptedV가 있으면:
//       v = 가장 높은 acceptedN의 acceptedV (이전 결정 보존)
//   else:
//       v = 내가 제안하려던 값
// Phase 2:
//   send Accept(n, v) to acceptors
//   if majority Accepted(n, v) 응답:
//       값 v로 결정됨
//   else:
//       n 증가시키고 재시도

// Multi-Paxos 변형:
//   안정 리더가 한번 Phase 1 통과하면 이후 결정마다 Phase 2만 실행
//   로그 인덱스마다 별도 Paxos 인스턴스 → 분산 로그
```

**Note**: 직접 구현 금지. etcd(Raft), Zookeeper(ZAB), Consul(Raft) 사용.

**관련 알고리즘**: Raft, ZAB, EPaxos

---

<a id="raft"></a>
## 3. Raft (래프트)

**목적**: Paxos보다 이해하기 쉬운 합의 알고리즘. 강한 리더 + 로그 복제 + 안전한 리더 선출

**시간 복잡도**: O(n) 메시지/명령, 정상 시 1 round trip

**공간 복잡도**: O(로그 크기) 노드당

**특징**:
- 세 가지 하위 문제 분리: Leader Election / Log Replication / Safety
- 노드 상태: Follower / Candidate / Leader
- Term(임기) 단조 증가, 한 term에 최대 1 리더
- 로그는 leader가 단방향으로 복제
- 과반수 commit 후 적용
- AppendEntries가 heartbeat 겸용

**장점**:
- Paxos보다 이해하기 훨씬 쉬움
- 실제 구현 다수 존재
- 멤버십 변경(joint consensus) 정의됨
- 강한 일관성 + 가용성 (CP)

**단점**:
- 리더 장애 시 election 동안 가용성 저하
- 네트워크 분할 시 소수 측 처리 불가
- 처리량 리더에 병목

**활용 예시**:
- etcd (Kubernetes 핵심)
- Consul
- CockroachDB, TiKV
- HashiCorp Vault

**난이도**: 높음 | **사용 빈도**: ★★★★★

**Kotlin 코드**:
```kotlin
// 노드 상태
enum class RaftRole { FOLLOWER, CANDIDATE, LEADER }

// 로그 엔트리
data class LogEntry(val term: Long, val index: Long, val command: ByteArray)

// 메시지 타입
sealed class RaftMessage {
    data class RequestVote(
        val term: Long,
        val candidateId: String,
        val lastLogIndex: Long,
        val lastLogTerm: Long
    ) : RaftMessage()

    data class RequestVoteReply(
        val term: Long,
        val voteGranted: Boolean,
        val from: String
    ) : RaftMessage()

    data class AppendEntries(
        val term: Long,
        val leaderId: String,
        val prevLogIndex: Long,
        val prevLogTerm: Long,
        val entries: List<LogEntry>,
        val leaderCommit: Long
    ) : RaftMessage()

    data class AppendEntriesReply(
        val term: Long,
        val success: Boolean,
        val matchIndex: Long,
        val from: String
    ) : RaftMessage()
}

// 노드 상태 (영속 + 휘발성)
class RaftNode(val id: String) {
    // 영속 (durable)
    var currentTerm: Long = 0
    var votedFor: String? = null
    val log = mutableListOf<LogEntry>()

    // 휘발성
    var commitIndex: Long = 0
    var lastApplied: Long = 0
    var role: RaftRole = RaftRole.FOLLOWER

    // 리더 전용
    val nextIndex = mutableMapOf<String, Long>()
    val matchIndex = mutableMapOf<String, Long>()
}

// 의사코드:
//
// === Leader Election ===
// Follower 가 election timeout (150~300ms 랜덤) 동안 AppendEntries 못 받으면:
//   role = CANDIDATE
//   currentTerm++
//   votedFor = self
//   send RequestVote to all peers
//   if 과반수 voteGranted:
//       role = LEADER
//       send AppendEntries(empty) heartbeat 시작
//   else if 더 높은 term 발견:
//       role = FOLLOWER, currentTerm = 더높은term
//   else:
//       election timeout 다시 → 재선거
//
// RequestVote 수신자:
//   if msg.term < currentTerm: reject
//   if (votedFor == null || votedFor == candidate) && candidate log이 최소한 내것만큼 최신:
//       grant vote, votedFor = candidate, reset election timer
//
// === Log Replication ===
// Leader가 클라이언트 명령 수신:
//   append to local log
//   send AppendEntries(prevLogIndex, prevLogTerm, [entries], commitIndex) to all followers
//   if 과반수 success → commitIndex = entry.index
//   apply to state machine 까지 lastApplied
//
// Follower의 AppendEntries 처리:
//   if msg.term < currentTerm: reject
//   if log[prevLogIndex].term != prevLogTerm: reject (불일치)
//   delete any conflicting suffix, append new entries
//   if leaderCommit > commitIndex: commitIndex = min(leaderCommit, lastNewIndex)
//
// === Safety ===
// 리더는 자기 term의 엔트리만 직접 commit (Figure 8 시나리오 방어)
// 멤버십 변경: joint consensus (Cold ∪ Cnew → Cnew)
```

**Note**: 직접 구현 금지. etcd, Consul, HashiCorp raft 라이브러리 사용.

**관련 알고리즘**: Paxos, ZAB, Multi-Paxos

---

<a id="byzantine-pbft"></a>
## 4. Byzantine Fault Tolerance (PBFT / Byzantine Generals) (비잔틴 결함 허용)

**목적**: 일부 노드가 임의로 거짓 메시지를 보내거나 악의적으로 동작(Byzantine 장애)하는 환경에서도 정직한 노드들이 단일 값에 합의하도록 보장

**시간 복잡도**: PBFT 정상 동작 시 O(n²) 메시지/합의 (prepare·commit 단계 all-to-all 브로드캐스트) — n: 노드 수

**공간 복잡도**: O(n) 노드당 (메시지 로그·체크포인트 별도)

**특징**:
- Byzantine Generals Problem (Lamport-Shostak-Pease, 1982): 구두 메시지(oral message, 서명 없음)로 f개의 배신자를 견디려면 전체 노드 n ≥ 3f+1 필요 (정직한 노드가 2/3 초과 다수여야 함)
- 구두 메시지 프로토콜은 f개 장애에 대해 m+1 라운드(m=f) 필요, 메시지 수 지수적 증가
- 서명 메시지(signed/written message)를 쓰면 변조 탐지가 가능해 더 적은 노드(n ≥ f+2)로도 합의 가능
- PBFT (Castro-Liskov, OSDI 1999): n = 3f+1 노드, 3단계 프로토콜 — pre-prepare(프라이머리가 순서 제안) → prepare(노드 간 순서 동의) → commit(실행 확정)
- 프라이머리(리더) 장애·악의 시 view change로 새 프라이머리 선출, 부분 동기(partial synchrony) 모델 가정
- 후속 연구: Tendermint(2014, BFT + 블록체인), HotStuff(2019, 선형 O(n) 메시지·리더 회전 파이프라인) 등으로 확장성 개선

**장점**:
- 단순 crash 장애뿐 아니라 임의·악의적(Byzantine) 장애까지 견딤
- 비신뢰 참여자가 섞인 권한형(permissioned) 환경에서 강한 안전성(safety) 보장
- PBFT는 즉시 확정(immediate finality) — 확률적 확정인 PoW와 달리 commit 후 번복 없음

**단점**:
- 정상 경로에서도 O(n²) 메시지로 노드 수 확장성 제약 (수십~수백 노드 한계)
- 노드 정족수(3f+1)가 crash-tolerant 합의(2f+1)보다 많아 비용 큼
- 노드 집합·신원을 알아야 함(permissioned) — 공개 무허가(permissionless) 환경엔 그대로 부적합

**활용 예시**:
- 권한형 블록체인 합의: Hyperledger Fabric, Tendermint/Cosmos, Diem(구 Libra, HotStuff 계열)
- 고신뢰 복제 상태 기계(replicated state machine) — 금융·항공 등 안전 임계 시스템
- 분산 키 관리·인증서 시스템의 비잔틴 내성 복제

**난이도**: 높음 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// PBFT 정상 경로(normal case) 3단계 메시지 + 정족수 판정 시연
// n = 3f + 1 노드, prepare/commit 정족수 = 2f + 1

sealed class PBFTMessage {
    // 프라이머리가 순서(seq) + 요청을 제안
    data class PrePrepare(val view: Long, val seq: Long, val digest: String, val from: Int) : PBFTMessage()
    // 각 노드가 동일 (view, seq, digest)에 동의 브로드캐스트
    data class Prepare(val view: Long, val seq: Long, val digest: String, val from: Int) : PBFTMessage()
    // prepared 도달 후 실행 확정 브로드캐스트
    data class Commit(val view: Long, val seq: Long, val digest: String, val from: Int) : PBFTMessage()
}

class PBFTReplica(val id: Int, val n: Int) {
    val f = (n - 1) / 3                 // 견딜 수 있는 비잔틴 노드 수
    private val quorum = 2 * f + 1      // prepare/commit 정족수
    private val prepares = mutableMapOf<Long, MutableSet<Int>>()
    private val commits = mutableMapOf<Long, MutableSet<Int>>()

    // prepared: 동일 digest 에 대한 prepare 가 정족수만큼 모임 → 순서 합의 완료
    fun onPrepare(m: PBFTMessage.Prepare): Boolean {
        val set = prepares.getOrPut(m.seq) { mutableSetOf() }
        set.add(m.from)
        return set.size >= quorum
    }

    // committed-local: commit 이 정족수만큼 모임 → 안전하게 실행 가능
    fun onCommit(m: PBFTMessage.Commit): Boolean {
        val set = commits.getOrPut(m.seq) { mutableSetOf() }
        set.add(m.from)
        return set.size >= quorum
    }
}

fun main() {
    val n = 4                          // n=4 → f=1 (한 노드의 비잔틴 장애 허용)
    val replica = PBFTReplica(id = 0, n = n)
    val digest = "req#42"
    // 정직한 3개 노드(2f+1=3)가 prepare → prepared 도달
    var prepared = false
    for (peer in listOf(0, 1, 2)) {
        prepared = replica.onPrepare(PBFTMessage.Prepare(view = 0, seq = 1, digest = digest, from = peer))
    }
    // 동일 정족수의 commit → committed-local 도달 → 실행 확정
    var committed = false
    for (peer in listOf(0, 1, 2)) {
        committed = replica.onCommit(PBFTMessage.Commit(view = 0, seq = 1, digest = digest, from = peer))
    }
    println("prepared=$prepared committed=$committed (f=${replica.f})")
    // 출력: prepared=true committed=true (f=1)
}
```

**관련 알고리즘**: Paxos, Raft, 2PC

---

<a id="leader-election"></a>
## 5. Leader Election (Bully / Ring) (리더 선출)

**목적**: 분산 시스템 노드 집합에서 단일 코디네이터(리더) 하나를 합의로 선출

**시간 복잡도**: Bully O(N²) 메시지(최악) / Ring O(N) 메시지(1회 순환)

**공간 복잡도**: O(N) (노드별 멤버십·ID 목록)

**특징**:
- Bully(Garcia-Molina, 1982): 가장 큰 ID 노드가 리더가 된다. 리더 장애를 감지한 노드가 자신보다 큰 ID에게 ELECTION 전송 → 응답(OK)이 없으면 스스로 리더 선언 후 COORDINATOR 브로드캐스트
- Ring: 논리적 링을 따라 후보 ID를 담은 토큰을 단방향 순환시키며 최대 ID를 누적, 한 바퀴 돌아 자신의 ID가 최대로 확정되면 리더 확정
- 비동기 네트워크에서는 완벽한 장애 감지가 불가능(FLP)하므로 timeout 기반 추정에 의존
- Raft/ZAB는 별도 알고리즘이 아니라 election을 합의 프로토콜에 내장: term/epoch 번호 + 과반수(quorum) 투표로 split-brain을 원천 차단
- split-brain 방지에는 fencing token(단조 증가 epoch) 또는 quorum 다수결이 필수 — 순수 Bully/Ring만으로는 네트워크 분할 시 다중 리더 위험

**장점**:
- 개념이 단순하고 구현이 직관적(특히 Ring은 메시지 수가 선형)
- 결정적 결과: 동일 멤버십이면 항상 최대 ID가 선출되어 예측 가능
- 합의 미들웨어 없이 애플리케이션 레벨에서 경량 구현 가능

**단점**:
- Bully는 최악 O(N²) 메시지로 대규모 클러스터에서 폭증
- 부정확한 timeout은 멀쩡한 리더를 죽이는 불필요 재선출 유발
- 순수 Bully/Ring은 네트워크 분할 시 split-brain 방어가 없어 quorum/fencing 보강 필요
- Ring은 토큰을 든 노드가 죽으면 순환이 끊겨 토큰 재생성 메커니즘 별도 필요

**활용 예시**:
- 마스터-워커 클러스터의 코디네이터 선출(스케줄러, 락 매니저)
- ZooKeeper/etcd 부재 환경의 경량 리더 합의
- 분산 작업 큐의 단일 디스패처 보장
- Kafka 컨트롤러, HDFS NameNode HA 등 단일 권한 노드 지정

**난이도**: 중간 | **사용 빈도**: ★★★☆☆

**Kotlin 코드**:
```kotlin
// Bully 알고리즘 — 가장 큰 ID 노드를 리더로 선출 (단일 프로세스 시뮬레이션)
class BullyElection(private val nodeIds: List<Int>) {
    // 살아있는 노드 집합 (장애 노드는 제외)
    private val alive = nodeIds.toMutableSet()

    // 노드 me 가 리더 장애를 감지해 선거를 시작한다. 선출된 리더 ID 반환
    fun startElection(me: Int): Int {
        // me 보다 큰 ID 중 살아있는 노드들에게 ELECTION 전송
        val higher = alive.filter { it > me }
        if (higher.isEmpty()) {
            // 더 큰 노드가 없으면 자신이 리더 — COORDINATOR 브로드캐스트
            return me
        }
        // 살아있는 상위 노드가 OK 로 응답하면, 그중 하나가 선거를 이어받는다.
        // 가장 큰 살아있는 노드가 최종적으로 리더가 됨 (재귀적 위임 결과와 동일)
        return higher.maxOrNull()!!.let { next -> startElection(next) }
    }

    fun killNode(id: Int) { alive.remove(id) }
}

fun main() {
    val election = BullyElection(listOf(1, 2, 3, 4, 5))
    println(election.startElection(2)) // 5 (최대 ID)
    election.killNode(5)
    println(election.startElection(2)) // 4 (5 장애 후 차순위)
}
```

**관련 알고리즘**: Raft, Paxos, Vector Clock, Gossip Protocol
