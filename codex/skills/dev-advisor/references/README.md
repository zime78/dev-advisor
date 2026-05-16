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
| OMX 에이전트 hand-off 상세 계약 | [references/handoff.md](handoff.md) |
| advisor 9 모드 + lookup 예시 10 (A~J) | [references/examples.md](examples.md) |
| 언어별 코드 템플릿 | [references/code_templates.md](code_templates.md) |
| advisor 9 모드 산출물 마크다운 스켈레톤 | [references/output_templates.md](output_templates.md) |
| 미시 원칙 18 부록 (DRY/KISS/YAGNI/LoD/SoC/Tell-Don't-Ask/Composition/SSoT + Conway/Hyrum/Postel/Brooks 등) | [references/principles/micro-principles.md](principles/micro-principles.md) |

## 디렉토리

- `patterns/` — 547 디자인·아키텍처 패턴 (55 카테고리)
- `algorithms/` — 273 알고리즘 (32 카테고리)
- `languages/` — 75 프로그래밍 언어
- `security/` — 106 보안 항목 (15 파일)
- `principles/` — 212 SW 공학 원칙 + 18 미시 부록
- `quality/` — 20 QA/QC 품질 항목 (QA 10 + QC 10)

자세한 카탈로그 진입점은 SKILL.md `## 데이터 기반` 표 참조.
