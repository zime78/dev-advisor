# 분산 합의 알고리즘 (Distributed Consensus)

여러 노드가 단일 결정에 합의(agreement)하도록 하는 분산 시스템 알고리즘입니다. 실제 구현은 etcd, Zookeeper, Consul, TiKV 등 검증된 시스템을 사용해야 하며, 본 카테고리는 의사코드 + 핵심 상태/메시지 타입 학습용입니다.

## 알고리즘 목차

| ID | 영문명 | 한글명 | 난이도 |
|----|--------|--------|--------|
| [2pc](#2pc) | 2PC (Two-Phase Commit) | 2단계 커밋 | 중간 |
| [paxos](#paxos) | Paxos | Basic / Multi-Paxos | 높음 |
| [raft](#raft) | Raft | 래프트 | 높음 |

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
