# SW 공학 원칙 레퍼런스

소프트웨어 공학의 정평 있는 표준·원칙 15 카테고리. dev-advisor `recommend / validate / refactor / maintain / security-audit` 5 모드의 표준 인용 source.

## 도메인 진입점

### 기존 5 카테고리 (코어 OO·운영·품질·스멜)

| # | 파일 | 항목 수 | 표준 / 저자 | 주요 용도 |
|---|------|--------:|------------|----------|
| 1 | [solid.md](solid.md)             |  5 | Robert C. Martin — *Clean Architecture*, *Agile Software Development: Principles, Patterns, and Practices* | OO 설계 5 원칙 (validate / refactor 기준) |
| 2 | [grasp.md](grasp.md)             |  9 | Craig Larman — *Applying UML and Patterns*, 3rd ed. | 책임 할당 9 원칙 (recommend / validate 기준) |
| 3 | [iso25010.md](iso25010.md)       |  8 | ISO/IEC 25010:2011 — *Systems and software Quality Requirements and Evaluation (SQuaRE)* | 품질 특성 8종 (recommend / maintain 기준) |
| 4 | [12-factor.md](12-factor.md)     | 12 | Adam Wiggins — *The Twelve-Factor App* (12factor.net, Heroku) | 클라우드 네이티브 운영 12 원칙 (validate / maintain / security-audit 기준) |
| 5 | [code-smells.md](code-smells.md) | 22 | Martin Fowler — *Refactoring: Improving the Design of Existing Code*, 2nd ed. (2018) | 코드 스멜 5 그룹 (maintain / refactor 기준) |

**소계**: 56 항목 (5 + 9 + 8 + 12 + 22)

### 신규 10 카테고리 (이론·기법·운영·메트릭)

| # | 파일 | 항목 수 | 표준 / 저자 | 주요 용도 |
|---|------|--------:|------------|----------|
|  6 | [type-systems.md](type-systems.md)                     | 10 | Benjamin C. Pierce — *Types and Programming Languages* (2002) | 타입 시스템 이론 (validate / refactor 기준) |
|  7 | [concurrency-theory.md](concurrency-theory.md)         | 10 | Herlihy & Shavit — *The Art of Multiprocessor Programming*; Lamport — Linearizability / Happens-Before | 동시성 정합성 모델 (validate / security-audit 기준) |
|  8 | [refactoring-techniques.md](refactoring-techniques.md) | 25 | Martin Fowler — *Refactoring*, 2nd ed. (2018) Ch.6~12 catalog | 리팩토링 처방 (refactor 기준 — code-smells 짝) |
|  9 | [sw-economics.md](sw-economics.md)                     | 10 | Boehm — *COCOMO II*; Albrecht — Function Points; Reinertsen — *Product Development Flow* (WSJF/CoD); SWEBOK KA11 | 추정·우선순위·기술부채 정량화 (maintain 기준) |
| 10 | [evolutionary-arch.md](evolutionary-arch.md)           |  8 | Neal Ford, Rebecca Parsons, Patrick Kua — *Building Evolutionary Architectures*, 2nd ed. (2022) | 진화적 아키텍처·Fitness Function (recommend / maintain 기준) |
| 11 | [resilience-theory.md](resilience-theory.md)           |  8 | Hollnagel — *Safety-I/II*; Leveson — *Engineering a Safer World* (STAMP); Taleb — *Antifragile* | 탄력성·안전 공학 이론 (security-audit / maintain 기준) |
| 12 | [documentation.md](documentation.md)                   |  8 | Nygard — ADR; Procida — *Diátaxis*; Martraire — *Living Documentation*; Simon Brown — C4 Model | 기술 문서화 표준 (maintain 기준) |
| 13 | [process-metrics.md](process-metrics.md)               | 10 | Sutherland & Schwaber — *Scrum Guide*; Forsgren, Humble, Kim — *Accelerate* (DORA); SPACE (ACM Queue 2021) | 개발 프로세스·DORA/SPACE 메트릭 (maintain 기준) |
| 14 | [performance-metrics.md](performance-metrics.md)       | 10 | Jeff Dean — *Numbers Every Programmer Should Know*; McCabe — Cyclomatic Complexity; Brendan Gregg — *Systems Performance*, Flame Graphs | 성능 측정·복잡도 메트릭 (refactor / maintain 기준) |
| 15 | [sustainable-sw.md](sustainable-sw.md)                 |  8 | Green Software Foundation — *Principles of Green Software Engineering*; ISO/IEC 21031:2024 (SCI) | 지속가능 SW·탄소 효율 (maintain 기준) |

**소계**: 107 항목 (10 + 10 + 25 + 10 + 8 + 8 + 8 + 10 + 10 + 8)

**총합**: **163 항목** (56 + 107)

### 부록: 미시 원칙

| 파일 | 항목 수 | 설명 |
|------|--------:|------|
| [micro-principles.md](micro-principles.md) | 18 | 핵심 8 (DRY / KISS / YAGNI / LoD / SoC / Tell-Don't-Ask / Composition over Inheritance / SSoT) + 사회·조직·확장 10 (Conway / Inverse Conway / Hyrum / Postel / Brooks / Hollywood-IoC / Boy Scout / Pareto / Goodhart / Cunningham). verify 카운트 외 부록 — 163 합계에 포함되지 않음 |

## 카테고리 선택 가이드

| 상황 | 우선 참조 |
|------|----------|
| 클래스/모듈 책임이 모호하다 | [solid.md](solid.md) — SRP / [grasp.md](grasp.md) — Information Expert, High Cohesion |
| 변경 시 여러 클래스가 흔들린다 | [solid.md](solid.md) — OCP / [code-smells.md](code-smells.md) — Shotgun Surgery, Divergent Change |
| 인터페이스가 비대하다 | [solid.md](solid.md) — ISP / [code-smells.md](code-smells.md) — Refused Bequest |
| 상속 계층이 깨진다 | [solid.md](solid.md) — LSP / [code-smells.md](code-smells.md) — Parallel Inheritance Hierarchies |
| 구체 의존이 많아 테스트 어렵다 | [solid.md](solid.md) — DIP / [grasp.md](grasp.md) — Pure Fabrication, Indirection |
| 결합도가 높다 | [grasp.md](grasp.md) — Low Coupling / [code-smells.md](code-smells.md) — Feature Envy, Inappropriate Intimacy |
| 응집도가 낮다 | [grasp.md](grasp.md) — High Cohesion / [code-smells.md](code-smells.md) — Large Class, Long Method |
| 시스템 비기능 요구사항 정의 | [iso25010.md](iso25010.md) — 8 품질 특성 매트릭스 |
| 클라우드/SaaS 운영 검증 | [12-factor.md](12-factor.md) — 12 인자 체크리스트 |
| 레거시 코드 부채 점검 | [code-smells.md](code-smells.md) — 22 스멜 5 그룹 |
| 타입 시스템이 헷갈린다 (static/dynamic, generics, variance, nullable) | [type-systems.md](type-systems.md) — Pierce 10 개념 |
| 동시성 정합성·메모리 모델·합의 검증 | [concurrency-theory.md](concurrency-theory.md) — Linearizability / Happens-Before / CAP / FLP |
| 스멜은 찾았는데 어떻게 고칠지 모른다 | [refactoring-techniques.md](refactoring-techniques.md) — Fowler 25 기법 (code-smells 짝) |
| 작업 산정·우선순위·기술부채 비용화 | [sw-economics.md](sw-economics.md) — Function Points / COCOMO II / WSJF / 기술부채 정량화 |
| 아키텍처가 변경에 취약하다 / Fitness Function 도입 | [evolutionary-arch.md](evolutionary-arch.md) — Ford·Parsons·Kua |
| 장애·안전·복원력 설계 (Chaos / Antifragile / STAMP) | [resilience-theory.md](resilience-theory.md) — Hollnagel / Leveson / Taleb |
| 결정 기록·사용자 문서·문서 자동화 | [documentation.md](documentation.md) — ADR / Diátaxis / C4 / Living Documentation |
| 개발 프로세스·생산성 측정 (DORA / SPACE / Trunk-Based) | [process-metrics.md](process-metrics.md) — Accelerate / SPACE |
| 성능 수치 감각·복잡도 측정·Tail latency | [performance-metrics.md](performance-metrics.md) — Dean numbers / McCabe / Flame Graph |
| 탄소 효율·에너지·하드웨어 효율 운영 | [sustainable-sw.md](sustainable-sw.md) — GSF / SCI (ISO 21031) |
| 일상 코딩 격언 (DRY/KISS/YAGNI/Conway/Hyrum 등) | [micro-principles.md](micro-principles.md) — 18 미시 원칙 |

## 호출 인터페이스

dev-advisor SKILL.md `## 호출 인터페이스` 와 동일하게 `list / search / <id>` 3 형태:

- `/principle list` — 위 15 도메인 진입점 표
- `/principle search <kw>` — 키워드 매칭 (예: `/principle search 결합도` → Low Coupling / Feature Envy)
- `/principle <id>` — 단일 항목 본문 (예: `/principle srp`, `/principle high-cohesion`, `/principle code-smell-feature-envy`, `/principle linearizability`, `/principle dora-metrics`)

### ID 명명 규칙

- 영문명 kebab-case 변환 후 lowercase
- 약어는 lowercase 유지: `srp`, `ocp`, `lsp`, `isp`, `dip`, `dora`, `space`, `sci`, `cap`, `flp`, `wsjf`, `cod`, `adr`, `c4`
- 카테고리 prefix 로 충돌 해소:
  - GRASP 항목: `low-coupling`, `high-cohesion`, `information-expert`, `pure-fabrication`, `protected-variations`
  - ISO 25010 특성: `iso-functional-suitability`, `iso-performance-efficiency`, `iso-maintainability` 등
  - 12-Factor 인자: `12f-codebase`, `12f-config`, `12f-logs` 등
  - 코드 스멜: `code-smell-<name>` (예: `code-smell-feature-envy`, `code-smell-long-method`)
  - 리팩토링 기법: `refactor-<name>` (예: `refactor-extract-function`, `refactor-replace-conditional-with-polymorphism`)
  - 타입 시스템: `type-<concept>` (예: `type-static-vs-dynamic`, `type-variance`, `type-hindley-milner`)
  - 동시성 이론: `conc-<concept>` (예: `conc-linearizability`, `conc-happens-before`, `conc-cap`)
  - SW 경제: `econ-<concept>` (예: `econ-function-points`, `econ-cocomo`, `econ-wsjf`)
  - 진화적 아키텍처: `evo-<concept>` (예: `evo-fitness-function`, `evo-architectural-quanta`)
  - 탄력성 이론: `res-<concept>` (예: `res-antifragility`, `res-stamp`, `res-chaos-engineering`)
  - 문서화: `doc-<concept>` (예: `doc-adr`, `doc-diataxis`, `doc-c4-model`)
  - 프로세스 메트릭: `proc-<concept>` (예: `proc-dora`, `proc-space`, `proc-trunk-based`)
  - 성능 메트릭: `perf-<concept>` (예: `perf-cyclomatic-complexity`, `perf-flame-graph`, `perf-apdex`)
  - 지속가능 SW: `green-<concept>` (예: `green-sci`, `green-carbon-aware`)

### 별칭

| 별칭 | Primary ID | 비고 |
|------|-----------|-----|
| single-responsibility           | srp                              | SOLID |
| single-responsibility-principle | srp                              | SOLID 정식 명칭 |
| open-closed                     | ocp                              | SOLID |
| open-closed-principle           | ocp                              | SOLID 정식 명칭 |
| liskov-substitution             | lsp                              | SOLID |
| liskov-substitution-principle   | lsp                              | SOLID 정식 명칭 |
| interface-segregation           | isp                              | SOLID |
| interface-segregation-principle | isp                              | SOLID 정식 명칭 |
| dependency-inversion            | dip                              | SOLID |
| dependency-inversion-principle  | dip                              | SOLID 정식 명칭 |
| controller-pattern              | controller                       | GRASP |
| god-class                       | code-smell-large-class           | Fowler smell |
| spaghetti-code                  | code-smell-message-chains        | Fowler smell |
| 12factor                        | 12-factor                        | 도메인 별칭 |
| twelve-factor                   | 12-factor                        | 도메인 별칭 |
| 12-factor-app                   | 12-factor                        | 정식 명칭 |
| twelve-factor-app               | 12-factor                        | 정식 명칭 |
| iso-25010                       | iso25010                         | 도메인 별칭 (하이픈 변형) |
| iso/iec-25010                   | iso25010                         | 표준명 |
| 25010                           | iso25010                         | 약식 |
| smell                           | code-smells                      | 도메인 단축 |
| smells                          | code-smells                      | 도메인 단축 |
| refactoring-smells              | code-smells                      | Fowler 책 명칭 |
| solid-principles                | solid                            | 도메인 단축 |
| grasp-principles                | grasp                            | 도메인 단축 |
| dont-repeat-yourself            | dry                              | 미시 원칙 |
| keep-it-simple                  | kiss                             | 미시 원칙 |
| you-arent-gonna-need-it         | yagni                            | 미시 원칙 |
| law-of-demeter                  | lod                              | 미시 원칙 |
| demeter                         | lod                              | 미시 원칙 |
| separation-of-concerns          | soc                              | 미시 원칙 |
| tell-dont-ask                   | tell-dont-ask                    | 미시 원칙 (primary) |
| composition-over-inheritance    | composition-over-inheritance     | 미시 원칙 (primary) |
| favor-composition               | composition-over-inheritance     | 미시 원칙 |
| single-source-of-truth          | ssot                             | 미시 원칙 |
| conways-law                     | conway                           | 미시 원칙 |
| inverse-conway                  | inverse-conway-maneuver          | 미시 원칙 |
| hyrums-law                      | hyrum                            | 미시 원칙 |
| postels-law                     | postel                           | 미시 원칙 |
| robustness-principle            | postel                           | 미시 원칙 (Postel 별칭) |
| brooks-law                      | brooks                           | 미시 원칙 |
| hollywood-principle             | hollywood                        | 미시 원칙 |
| inversion-of-control            | hollywood                        | 미시 원칙 (IoC 별칭) |
| ioc                             | hollywood                        | 미시 원칙 (약어) |
| boy-scout-rule                  | boy-scout                        | 미시 원칙 |
| 80-20-rule                      | pareto                           | 미시 원칙 |
| goodharts-law                   | goodhart                         | 미시 원칙 |
| cunninghams-law                 | cunningham                       | 미시 원칙 |
| type-system                     | type-systems                     | 도메인 단축 |
| types                           | type-systems                     | 도메인 단축 |
| concurrency                     | concurrency-theory               | 도메인 단축 |
| linearizability                 | conc-linearizability             | 동시성 (Herlihy-Wing) |
| happens-before                  | conc-happens-before              | 동시성 (Lamport) |
| cap-theorem                     | conc-cap                         | 동시성 (Brewer) |
| flp-impossibility               | conc-flp                         | 동시성 (Fischer-Lynch-Paterson) |
| refactoring                     | refactoring-techniques           | 도메인 단축 |
| extract-method                  | refactor-extract-function        | Fowler 1st ed. 명칭 |
| extract-function                | refactor-extract-function        | Fowler 2nd ed. 정식 |
| function-points                 | econ-function-points             | SW 경제 (Albrecht) |
| cocomo                          | econ-cocomo                      | SW 경제 (Boehm) |
| wsjf                            | econ-wsjf                        | SW 경제 (Reinertsen) |
| cost-of-delay                   | econ-cod                         | SW 경제 |
| reference-class-forecasting     | econ-rcf                         | SW 경제 (Kahneman) |
| evolutionary-architecture       | evolutionary-arch                | 도메인 단축 |
| fitness-function                | evo-fitness-function             | 진화적 아키텍처 |
| architectural-quanta            | evo-architectural-quanta         | 진화적 아키텍처 |
| antifragile                     | res-antifragility                | 탄력성 (Taleb) |
| chaos-engineering               | res-chaos-engineering            | 탄력성 |
| stamp                           | res-stamp                        | 탄력성 (Leveson) |
| safety-i-safety-ii              | res-safety-i-ii                  | 탄력성 (Hollnagel) |
| docs                            | documentation                    | 도메인 단축 |
| adr                             | doc-adr                          | 문서화 (Nygard) |
| diataxis                        | doc-diataxis                     | 문서화 (Procida) |
| c4-model                        | doc-c4-model                     | 문서화 (Brown) |
| living-documentation            | doc-living-documentation         | 문서화 (Martraire) |
| dora                            | proc-dora                        | 프로세스 (Accelerate) |
| dora-metrics                    | proc-dora                        | 프로세스 (4 keys) |
| space                           | proc-space                       | 프로세스 (ACM Queue 2021) |
| trunk-based                     | proc-trunk-based                 | 프로세스 |
| gitops                          | proc-gitops                      | 프로세스 |
| platform-engineering            | proc-platform-engineering        | 프로세스 |
| cyclomatic-complexity           | perf-cyclomatic-complexity       | 성능 메트릭 (McCabe) |
| halstead                        | perf-halstead                    | 성능 메트릭 |
| flame-graph                     | perf-flame-graph                 | 성능 메트릭 (Gregg) |
| apdex                           | perf-apdex                       | 성능 메트릭 |
| tail-latency                    | perf-tail-latency                | 성능 메트릭 |
| numbers-every-programmer-should-know | perf-dean-numbers           | 성능 메트릭 (Dean) |
| green-software                  | sustainable-sw                   | 도메인 단축 |
| green                           | sustainable-sw                   | 도메인 단축 |
| sci                             | green-sci                        | 지속가능 SW (ISO 21031) |
| carbon-aware                    | green-carbon-aware               | 지속가능 SW |

## 표준 인용 매트릭스

| 표준 / 저작 | 발행 | 적용 도메인 |
|-------------|------|------------|
| Robert C. Martin — *Clean Architecture* (2017) | Prentice Hall | solid.md, refactor 모드 |
| Robert C. Martin — *Agile Software Development: Principles, Patterns, and Practices* (2002) | Pearson | solid.md (원전) |
| Craig Larman — *Applying UML and Patterns* 3rd ed. (2004) | Prentice Hall | grasp.md (원전) |
| ISO/IEC 25010:2011 | ISO | iso25010.md (8 품질 특성) |
| ISO/IEC 25023:2016 | ISO | iso25010.md 측정 지표 (참조) |
| Adam Wiggins — *The Twelve-Factor App* (2011~) | 12factor.net | 12-factor.md (원전) |
| Martin Fowler — *Refactoring* 2nd ed. (2018) | Addison-Wesley | code-smells.md (원전), refactoring-techniques.md (catalog) |
| Joshua Kerievsky — *Refactoring to Patterns* (2004) | Addison-Wesley | refactoring-techniques.md (보강) |
| Michael Feathers — *Working Effectively with Legacy Code* (2004) | Prentice Hall | refactoring-techniques.md (legacy 보강) |
| Kent Beck — *Implementation Patterns* (2007) | Addison-Wesley | code-smells.md 참조 (Fowler 인용) |
| Benjamin C. Pierce — *Types and Programming Languages* (2002) | MIT Press | type-systems.md (원전) |
| Benjamin C. Pierce ed. — *Advanced Topics in Types and Programming Languages* (2005) | MIT Press | type-systems.md (보강) |
| Maurice Herlihy & Nir Shavit — *The Art of Multiprocessor Programming* 2nd ed. (2020) | Morgan Kaufmann | concurrency-theory.md (원전) |
| Herlihy & Wing — "Linearizability: A Correctness Condition for Concurrent Objects" (TOPLAS 1990) | ACM | concurrency-theory.md (Linearizability) |
| Leslie Lamport — "Time, Clocks, and the Ordering of Events in a Distributed System" (CACM 1978) | ACM | concurrency-theory.md (Happens-Before) |
| Eric Brewer — "Towards Robust Distributed Systems" (PODC 2000) | ACM | concurrency-theory.md (CAP) |
| Fischer, Lynch, Paterson — "Impossibility of Distributed Consensus with One Faulty Process" (JACM 1985) | ACM | concurrency-theory.md (FLP) |
| Allan Albrecht — "Measuring Application Development Productivity" (IBM, 1979) | IBM | sw-economics.md (Function Points) |
| Barry Boehm — *Software Cost Estimation with COCOMO II* (2000) | Prentice Hall | sw-economics.md (COCOMO II) |
| Mike Cohn — *Agile Estimating and Planning* (2005) | Prentice Hall | sw-economics.md (Story Points / Planning Poker) |
| Don Reinertsen — *The Principles of Product Development Flow* (2009) | Celeritas | sw-economics.md (CoD / WSJF) |
| Daniel Kahneman — *Thinking, Fast and Slow* (2011) | FSG | sw-economics.md (Reference Class Forecasting) |
| SWEBOK v3 KA11 (2014) | IEEE CS | sw-economics.md (SW Economics) |
| Neal Ford, Rebecca Parsons, Patrick Kua — *Building Evolutionary Architectures* 2nd ed. (2022) | O'Reilly | evolutionary-arch.md (원전) |
| Neal Ford — *Fundamentals of Software Architecture* (2020) | O'Reilly | evolutionary-arch.md (보강) |
| Henderson-Sellers — *Object-Oriented Metrics: Measures of Complexity* (1996) | Prentice Hall | evolutionary-arch.md (LCOM) |
| Erik Hollnagel — *Safety-I and Safety-II* (2014) | Ashgate | resilience-theory.md (안전 패러다임) |
| Erik Hollnagel — *Resilience Engineering in Practice* (2011) | Ashgate | resilience-theory.md (4 Cornerstones) |
| Sidney Dekker — *Drift into Failure* (2011) | Ashgate | resilience-theory.md (Drift) |
| Nancy Leveson — *Engineering a Safer World* (MIT Press, 2011) | MIT Press | resilience-theory.md (STAMP) |
| Nassim Nicholas Taleb — *Antifragile* (2012) | Random House | resilience-theory.md (Antifragility) |
| Michael Nygard — "Documenting Architecture Decisions" (2011, blog) | cognitect.com | documentation.md (ADR) |
| Daniele Procida — *Diátaxis* (https://diataxis.fr) | web | documentation.md (Diátaxis) |
| Cyrille Martraire — *Living Documentation* (2019) | Addison-Wesley | documentation.md (Living Documentation) |
| Simon Brown — *The C4 Model for Software Architecture* (c4model.com) | web | documentation.md (C4 Model) |
| Andrew Etter — *Modern Technical Writing* | self-pub | documentation.md (Docs-as-Code) |
| Jeff Sutherland & Ken Schwaber — *Scrum Guide* (2020 ed.) | scrumguides.org | process-metrics.md (Scrum) |
| David J. Anderson — *Kanban* (2010) | Blue Hole | process-metrics.md (Kanban) |
| Kent Beck — *Extreme Programming Explained* 2nd ed. (2004) | Addison-Wesley | process-metrics.md (XP) |
| Nicole Forsgren, Jez Humble, Gene Kim — *Accelerate* (2018) | IT Revolution | process-metrics.md (DORA) |
| McConnell, Storey, Forsgren, Houck, Zimmermann — "The SPACE of Developer Productivity" (ACM Queue 2021) | ACM | process-metrics.md (SPACE) |
| Jeff Dean — "Numbers Every Programmer Should Know" (Stanford talk, 2010) | Stanford | performance-metrics.md (Dean numbers) |
| Thomas McCabe — *A Complexity Measure* (IEEE TSE, 1976) | IEEE | performance-metrics.md (Cyclomatic) |
| Maurice Halstead — *Elements of Software Science* (1977) | Elsevier | performance-metrics.md (Halstead) |
| Brendan Gregg — *Systems Performance* 2nd ed. (2020) | Pearson | performance-metrics.md (Profiling / Flame Graph) |
| Green Software Foundation — *Principles of Green Software Engineering* | learn.greensoftware.foundation | sustainable-sw.md (원전) |
| ISO/IEC 21031:2024 — *Software Carbon Intensity Specification* | ISO | sustainable-sw.md (SCI) |

## Cross-link 규약

- `principles/<file>.md` 내부에서 다른 원칙 파일 참조 시: `<항목명> -> ../principles/<file>.md#<anchor>`
- 다른 도메인(patterns/security 등)에서 principles 참조 시: `<항목명> -> principles/<file>.md#<anchor>`
- SKILL.md 본문에서 참조 시: `<항목명> -> references/principles/<file>.md#<anchor>`
- 양방향 cross-link 권장 — 예: `code-smells.md` 의 *Feature Envy* 항목은 `solid.md` *SRP* / `grasp.md` *Information Expert* / `refactoring-techniques.md` *Move Function* 로 link.

## 무결성 검증

`scripts/verify-references.sh` 의 CHECK 9 블록이 이 도메인을 검증:
- **16 파일 존재** (`index.md` + 15 카테고리 md: solid / grasp / iso25010 / 12-factor / code-smells / type-systems / concurrency-theory / refactoring-techniques / sw-economics / evolutionary-arch / resilience-theory / documentation / process-metrics / performance-metrics / sustainable-sw)
- 항목 합계 **163** (`^## [0-9]+\.` 헤더 카운트)
- 도메인별 카운트: solid=5, grasp=9, iso25010=8, 12-factor=12, code-smells=22, type-systems=10, concurrency-theory=10, refactoring-techniques=25, sw-economics=10, evolutionary-arch=8, resilience-theory=8, documentation=8, process-metrics=10, performance-metrics=10, sustainable-sw=8
- **부록 검증** (별도 검사): `micro-principles.md` 존재 + **18** 항목 카운트 (`^## ` 헤더 — 표준 인용·매트릭스·분류 섹션 3 제외). 163 합계에는 포함되지 않음.
