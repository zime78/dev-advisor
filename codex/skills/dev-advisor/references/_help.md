# `/dev-advisor --help` 출력 (source of truth)

`dev-advisor` `--help` 호출 시 표시되는 도움말 텍스트의 source of truth. SKILL.md는 이 파일을 참조.

<!-- Counts are synced from .counts.manifest via bin/sync-skill-counts.sh. Do not edit count numbers manually. -->

```
dev-advisor — 추천 / 검증 / 리팩토링 / 유지보수 / 보안 점검 / QA / QC / 통합(audit) 어드바이저

사용법:
  /dev-advisor <mode> <input>                        advisor 모드 명시 호출
  /dev-advisor audit [--mode=serial|parallel] <…>    통합 점검 (serial 기본 / parallel = OMX ultrawork)
  /dev-advisor --help                                이 도움말

Advisor 모드 (옵션) — 8 기본 + 1 통합 (audit):
  recommend        추천 + 근거 (대안 trade-off, 표준 인용)
  validate         기존 코드/구조 검증 (SOLID/GRASP/DDD/Clean Arch/ISO 25010/12-Factor/OWASP/NIST)
  refactor         리팩토링 단계별 가이드 (Before/After + 회귀 위험)
  maintain         안티패턴/기술 부채 점검 (코드 스멜 5 그룹)
  security-audit   STRIDE / OWASP / NIST 보안 점검 (DREAD + 컴플라이언스)
  qa               요구사항/테스트 전략/추적성/릴리즈 승인 중심 QA 점검
  qc               빌드/테스트 실행/품질 게이트/결함 증거 중심 QC 검증
  research         학술 논문 검색 + 카탈로그 cross-ref (arXiv/S2/OpenAlex 무료 API)
  audit            7 모드 통합 보고 + 통합 우선순위 Top 10 + 단일 6 필드
                   --mode=serial   (default) 단일 컨텍스트 순차 통합
                   --mode=parallel OMX ultrawork 기반 7 Codex 서브에이전트 병렬 → reviewer 통합

Legacy aliases (deprecated, 호환 유지):
  full             ≡ audit --mode=serial
  swarm            ≡ audit --mode=parallel

research 옵션 예시:
  /dev-advisor research <topic|catalog-id|query> [--limit N] [--years YYYY-YYYY] [--source arxiv|s2|openalex|all] [--bias recency|citation]

카탈로그 lookup (기존 보존):
  /pattern   <id|list|search>             <!--counts:patterns-->543<!--/--> 패턴 (55 카테고리 — GoF + 아키텍처/분산/신뢰성/동시성/통합/DDD 전술·전략/데이터 접근/테스트/Observability/AI-LLM/배포/캐싱/안티패턴/모바일/임베디드/게임/네트워크/크로스플랫폼/Offline-First/에러 처리/API 설계·스타일/Web 렌더링/상태 관리/FP/Reactive/레거시 코드/워크플로우/스트리밍/데이터 모델링/UI-UX/FinOps/테스트 전략/빌드·버전/MLOps/DX/블록체인/요구공학/MDM/DQ 거버넌스/Web Performance/Data Warehousing & BI/Graphics Rendering/AR-VR-XR/Serverless-FaaS/HPC-Scientific/도메인 5종(Fintech·Healthcare·eCommerce·Logistics·IoT))
  /algorithm <id|list [category]|search>  <!--counts:algorithms-->292<!--/--> 알고리즘 (32 카테고리 — 정렬/탐색/그래프/DP/문자열/수학/자료구조/계산기하/플로우/매칭/암호/압축/게임AI/ML/확률/분산합의/분산알고/동시성/파싱 + DB 인덱스/DB 스토리지 엔진/DB 쿼리 옵티마이저/공간 인덱싱/검색·랭킹/부하 분산/OS 기초/이미지/신호/코덱)
  /language  <id|list|search>             <!--counts:languages-->75<!--/--> 언어
  /security  <id|list|search>             <!--counts:security-->106<!--/--> 보안 항목 (15 파일 — 인증/인가/암호 운영/데이터 보호/API·Web/공급망/플랫폼/SDLC/탐지/모바일/AI 모델/Privacy Engineering/규제 컴플라이언스)
  /principle <id|list|search>             <!--counts:principles-->211<!--/--> + <!--counts:micro-->20<!--/--> 부록 SW 공학 원칙
                                          기본 5: SOLID 5 / GRASP 9 / ISO 25010 8 / 12-Factor 12 / Code Smells 22
                                          확장 10: Type Systems 10 / Concurrency Theory 10 / Refactoring Techniques 25 / SW Economics 10 / Evolutionary Arch 8 / Resilience Theory 8 / Documentation 8 / Process Metrics (DORA) 10 / Performance Metrics 10 / Sustainable SW (Green) 8
                                          P0 신설 4: Database Fundamentals 8 / SDLC Models 7 / Scaled Agile 6 / Professional Ethics 6
                                          P1 신설 2: Standards Mapping (SWEBOK/CS2023/DMBOK/OWASP/NIST-ISO) 5 / Configuration Management (IEEE 828) 6
                                          P3 신설 2: HCI Methodology (ISO 9241 / Persona / Journey Map / Heuristic Eval) 6 / Formal Methods (TLA+ / Alloy / Hoare / Model Checking) 5
                                          부록 18: DRY/KISS/YAGNI/LoD/SoC/Tell-Don't-Ask/Composition/SSoT + Conway/Inverse Conway/Hyrum/Postel/Brooks/Hollywood/Boy Scout/Pareto/Goodhart/Cunningham
  /quality   <id|list|search>             <!--counts:quality-->20<!--/--> QA/QC 항목 (QA 10 — 요구사항 추적성/테스트 전략/릴리즈 준비도, QC 10 — 빌드 검증/테스트 증거/품질 게이트)

라우팅 우선순위:
  카탈로그 ID 명시 발화 ("JWT 보안", "싱글톤 패턴", "SRP")            → 해당 도메인 lookup
  코드/모듈/API 입력 동반 발화 ("이 코드 검증", "이 API 보안 점검")    → advisor 모드
  의도 동사만 ("추천", "리팩토링", "기술 부채")                       → advisor 모드
  QA/QC 키워드 ("QA 점검", "테스트 전략", "품질 게이트", "QC 검증")    → qa / qc
  통합 키워드 ("전체 점검", "종합 분석", "모두 체크", "full audit")    → audit --mode=serial (legacy alias: full)
  병렬 키워드 ("병렬 점검", "심층 분석", "swarm", "ultra audit")       → audit --mode=parallel (legacy alias: swarm)
  둘 다 모호                                                          → lookup 후 감사 범위 질문
```

상세 라우팅 규칙은 [`workflows/_routing.md`](workflows/_routing.md) 참조.
