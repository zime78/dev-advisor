# dev-advisor references — 디렉토리 가이드

## 상대경로 규약

- **SKILL.md 본문 link**: `references/<file>` 접두어 사용 (예: `references/principles/solid.md`)
- **references/* 내부 link**: 접두어 없이 sibling 참조 (예: `principles/solid.md` from `references/handoff.md`)
- 둘 다 GitHub-flavored markdown 표준 (link 의 base 는 link 가 속한 파일 자신의 위치)

## SKILL.md.bak → references/* split 매핑 (분할 추적)

| 분할 전 SKILL.md.bak 섹션 | 분할 후 위치 |
|---|---|
| 알고리즘 32 카테고리 표 | [references/algorithms/index.md](algorithms/index.md) |
| 언어 자동 감지 13 패턴 표 | [references/languages/index.md](languages/index.md) |
| OMC 에이전트 hand-off 상세 계약 | [references/handoff.md](handoff.md) |
| advisor 9 모드 + lookup 예시 10 (A~J) | [references/examples.md](examples.md) |
| 언어별 코드 템플릿 | [references/code_templates.md](code_templates.md) |
| advisor 9 모드 산출물 마크다운 스켈레톤 | [references/output_templates.md](output_templates.md) |
| 미시 원칙 <!--counts:micro-->20<!--/--> 부록 (DRY/KISS/YAGNI/LoD/SoC/Tell-Don't-Ask/Composition/SSoT + Conway/Hyrum/Postel/Brooks 등) | [references/principles/micro-principles.md](principles/micro-principles.md) |

## 디렉토리

<!-- Counts are synced from .counts.manifest via bin/sync-skill-counts.sh. Do not edit count numbers manually. -->

### 6 카탈로그 (도메인 데이터)

- `patterns/` — <!--counts:patterns-->543<!--/--> 디자인·아키텍처 패턴 (55 카테고리)
- `algorithms/` — <!--counts:algorithms-->292<!--/--> 알고리즘 (32 카테고리)
- `languages/` — <!--counts:languages-->75<!--/--> 프로그래밍 언어
- `security/` — <!--counts:security-->106<!--/--> 보안 항목 (15 파일)
- `principles/` — <!--counts:principles-->211<!--/--> SW 공학 원칙 + <!--counts:micro-->20<!--/--> 미시 부록
- `quality/` — <!--counts:quality-->20<!--/--> QA/QC 품질 항목 (QA 10 + QC 10)

### Workflows (advisor 9 모드 절차·산출물 — Progressive Disclosure)

- `workflows/` — 모드별 1 파일 (9 모드 + `_routing.md` + `_severity.md` + `index.md`)
  - 진입점: [`workflows/index.md`](workflows/index.md)
  - 모드: [`recommend.md`](workflows/recommend.md) / [`validate.md`](workflows/validate.md) / [`refactor.md`](workflows/refactor.md) / [`maintain.md`](workflows/maintain.md) / [`security-audit.md`](workflows/security-audit.md) / [`qa.md`](workflows/qa.md) / [`qc.md`](workflows/qc.md) / [`research.md`](workflows/research.md) / [`full.md`](workflows/full.md) / [`swarm.md`](workflows/swarm.md)
  - 공통: [`_routing.md`](workflows/_routing.md) (라우팅 우선순위), [`_severity.md`](workflows/_severity.md) (공통 severity + 통합 우선순위 매트릭스)
- `_help.md` — `/dev-advisor --help` 출력의 source of truth

### Research 모드 자산

- `research/` — research 모드 자산 (7+ 파일: sources / query-strategies / output-format / mapping-algorithm / fallback / performance / testing + fixtures)

### 부가 자산

- `code_templates.md` — 자동 코드 생성 4 언어 템플릿 (Kotlin/Java/Swift/Python)
- `output_templates.md` — advisor 9 모드 산출물 마크다운 스켈레톤
- `examples.md` — advisor 9 모드 + 카탈로그 lookup 실제 호출/응답 10 예시 (A~J)
- `handoff.md` — OMC hand-off 상세 정식 입출력 계약

자세한 카탈로그 진입점은 SKILL.md `## 데이터 기반` 표 참조.
