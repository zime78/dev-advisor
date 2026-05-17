# catalog-index.json 설계

## 목적

`catalog-index.json`은 `dev-advisor`의 Markdown 카탈로그를 런타임에서 빠르게 조회하기 위한 기계용 색인이다. 사람은 계속 `references/**/*.md`와 각 도메인 `index.md`를 편집하고, JSON은 생성기로만 만드는 산출물로 둔다.

이 설계의 1차 목표는 lookup 성능 개선이 아니라 **source of truth 경계 고정**이다. JSON이 또 하나의 수동 관리 대상이 되면 Markdown, index 표, alias, anchor 사이의 불일치가 늘어나므로 생성/검증 규칙을 먼저 고정한다.

## 비목표와 현재 단계

- 이번 단계에서 GitHub Actions를 추가하지 않는다.
- Markdown 문서 구조를 대규모로 재배치하지 않는다.
- 별도 version bump 스크립트는 이번 단계에서 만들지 않는다.

현재 구현 상태:

- `catalog-index.json`과 `scripts/generate-catalog-index.py`는 Codex/Claude 패키지에 생성했다.
- 생성 산출물은 Markdown 원본에서 재생성되며, 수동 편집 대상이 아니다.
- `--check`는 stale JSON을 감지하되 `generated_at` 차이는 비교에서 제외한다.
- `lookup-catalog.py`는 일반 도메인 lookup과 표준 역조회 모두 `catalog-index.json`만 읽는다.
- GitHub Actions 연결은 후속 작업으로 남긴다.

## Source Of Truth

| 데이터 | 원본 | JSON 내 역할 |
|---|---|---|
| 항목 본문 | `references/<domain>/*.md` | `file`, `anchor`, `title`, 본문 위치 |
| 도메인별 primary ID | `patterns/index.md`, `security/index.md`, `quality/index.md`, `algorithms/index.md`, `languages/index.md`, `principles/index.md` | `items[].id` |
| alias | 각 도메인 `index.md`의 별칭 표 | `aliases[]`, `items[].aliases` |
| expected count | `.counts.manifest` | `domains.<domain>.expected_count` 검증 |
| 표준 매핑 | `principles/standards-mapping.md` | `standards_mappings[]` 표준 역조회 색인 |

원칙:

1. Markdown과 `index.md`가 원본이다.
2. `catalog-index.json`은 생성 산출물이다.
3. 생성 산출물은 사람이 직접 편집하지 않는다.
4. 생성기가 해석하지 못하는 anchor 또는 alias는 실패로 처리한다.

## 파일 위치

권장 위치:

```text
codex/skills/dev-advisor/catalog-index.json
claude/skills/dev-advisor/catalog-index.json
```

생성기는 양쪽 패키지에 같은 로직으로 배치한다.

```text
codex/skills/dev-advisor/scripts/generate-catalog-index.py
claude/skills/dev-advisor/scripts/generate-catalog-index.py
```

루트에는 비교/설치 편의를 위해 선택적으로 통합 wrapper를 둘 수 있다.

```text
scripts/generate-catalog-index.sh
```

## JSON 스키마 초안

```json
{
  "schema_version": "1.1",
  "catalog_version": "2026-05",
  "generated_at": "2026-05-17T00:00:00+09:00",
  "source": {
    "root": "references",
    "generator": "scripts/generate-catalog-index.py",
    "source_of_truth": "markdown"
  },
  "domains": {
    "patterns": {
      "index": "references/patterns/index.md",
      "expected_count": 547,
      "actual_count": 547
    }
  },
  "items": [
    {
      "domain": "patterns",
      "id": "singleton",
      "title": "Singleton",
      "title_ko": "싱글톤",
      "category": "creational",
      "file": "references/patterns/creational.md",
      "anchor": "1-singleton-싱글톤",
      "aliases": [],
      "tags": ["creational", "gof"],
      "lookup_keys": ["singleton", "싱글톤"]
    }
  ],
  "aliases": [
    {
      "domain": "principles",
      "alias": "single-responsibility",
      "target_id": "srp",
      "source": "references/principles/index.md"
    }
  ],
  "standards_mappings": [
    {
      "standard": "owasp-api-2023",
      "section_id": "4-2-owasp-api-security-top-10-2023",
      "code": "API3",
      "title": "Broken Object Property Level Authorization",
      "coverage": "✓",
      "references": [
        "references/security/security-api-web.md#8-mass-assignment-방어",
        "references/security/security-authz.md#2-abac-attribute-based-access-control"
      ],
      "lookup_keys": ["api3", "owasp-api-api3", "owasp-api-2023-api3"]
    }
  ]
}
```

## 필드 규칙

### Root

| 필드 | 필수 | 설명 |
|---|---|---|
| `schema_version` | 예 | JSON 구조 버전. breaking change 때 증가 |
| `catalog_version` | 예 | 카탈로그 릴리즈 버전 또는 날짜 기반 버전 |
| `generated_at` | 예 | ISO-8601 생성 시각 |
| `source` | 예 | 생성기와 원본 경로 정보 |
| `domains` | 예 | 도메인별 index/카운트 요약 |
| `items` | 예 | primary ID 색인 |
| `aliases` | 예 | alias -> primary ID 매핑 |
| `standards_mappings` | 예 | 국제 표준 코드/명칭 -> dev-advisor reference 역방향 색인 |

### items[]

| 필드 | 필수 | 설명 |
|---|---|---|
| `domain` | 예 | `patterns`, `algorithms`, `languages`, `security`, `principles`, `quality` |
| `id` | 예 | primary lookup ID |
| `item_type` | 예 | 현재는 catalog 본문 항목을 뜻하는 `entry` |
| `title` | 예 | 영문 또는 원문 제목 |
| `title_ko` | 아니오 | 한글명. index 표에 있으면 채움 |
| `category` | 예 | 파일 stem 또는 도메인 내 카테고리 |
| `file` | 예 | skill root 기준 상대 경로 |
| `anchor` | 예 | 실제 본문 anchor. 명시 anchor 우선, heading anchor fallback |
| `aliases` | 예 | 해당 ID로 직접 연결되는 alias 목록 |
| `tags` | 아니오 | 검색 보조 태그 |
| `lookup_keys` | 예 | ID, alias, title, title_ko를 정규화한 검색 key |

### aliases[]

| 필드 | 필수 | 설명 |
|---|---|---|
| `domain` | 예 | alias가 적용되는 도메인 |
| `alias` | 예 | 사용자 입력 alias |
| `target_id` | 예 | `items[].id` 중 하나 |
| `source` | 예 | alias가 선언된 Markdown 파일 |

### standards_mappings[]

| 필드 | 필수 | 설명 |
|---|---|---|
| `standard` | 예 | `swebok-v4`, `cs2023`, `dmbok-2`, `owasp-api-2023` 같은 표준 family ID |
| `section_id` | 예 | `standards-mapping.md` 안의 표준 섹션 heading anchor |
| `code` | 예 | 표준 row 코드. 예: `API3`, `LLM05`, `SP 800-53 Rev.5`, `AI` |
| `title` | 예 | 표준 항목명 |
| `coverage` | 예 | `✓`, `◐`, `✗` 중 원문 커버리지 |
| `references` | 예 | `references/<domain>/<file>.md` 또는 `#anchor` 포함 reference 배열 |
| `lookup_keys` | 예 | 표준명, 코드, title, 표준 alias 조합의 정규화 검색 key |

## Anchor 해석 규칙

생성기는 현재 semantic 검증과 같은 순서로 anchor를 해석한다.

1. 대상 파일의 명시 anchor `<a id="...">`를 수집한다.
2. Markdown heading을 GitHub 유사 slug로 변환해 heading anchor 후보를 수집한다.
3. `id`와 같은 anchor가 있으면 그것을 사용한다.
4. `id`가 heading anchor의 prefix 또는 suffix로 해석되면 사용한다.
5. 명시 anchor가 없는 기존 문서는 index row 순서와 `## N. Title` heading을 매칭한다.
6. 그래도 해석하지 못하면 생성 실패로 처리한다.

명시 anchor가 있는 경우에는 명시 anchor를 JSON의 `anchor`로 우선 저장한다. heading anchor fallback은 기존 문서 호환용이며, 신규 항목은 명시 anchor를 권장한다.

## 도메인별 파싱 전략

| 도메인 | 1차 파싱 원본 | 비고 |
|---|---|---|
| Patterns | `references/patterns/index.md`의 `패턴 ID -> 파일 매핑` | heading fallback 허용 |
| Algorithms | `references/algorithms/index.md`의 ID 매핑 링크 | 명시 anchor 중심 |
| Languages | `references/languages/index.md` + 언어 파일 목록 | 언어 파일 stem이 primary ID |
| Security | `references/security/index.md`의 `보안 ID -> 파일 매핑` | heading fallback 허용 |
| Principles | `references/principles/index.md`의 도메인/alias 정보 + 원칙 파일 anchor | `entry` 214 + `category` 23 + `appendix` 18 색인 |
| Quality | `references/quality/index.md`의 `Quality ID 매핑` | 명시 anchor 중심 |
| Standards Mapping | `references/principles/standards-mapping.md`의 표준별 매핑표 | `standards_mappings[]`로 생성, reference 파일/anchor 검증 |

Principles는 index가 전체 primary ID 매핑표를 완전한 링크 표로 갖고 있지 않다. 현재 구현은 원칙 파일 anchor에서 `entry`를 만들고, `principles/index.md`의 도메인 진입점은 `category`, `micro-principles.md`의 18개 명시 anchor는 `appendix`로 흡수한다. alias target 누락은 생성기 검증 실패로 처리한다.

## 생성기 인터페이스

권장 CLI:

```bash
python3 scripts/generate-catalog-index.py
python3 scripts/generate-catalog-index.py --check
python3 scripts/generate-catalog-index.py --output catalog-index.json
python3 scripts/lookup-catalog.py principle srp
python3 scripts/lookup-catalog.py principle dry
python3 scripts/lookup-catalog.py principle solid
python3 scripts/lookup-catalog.py standard API3
python3 scripts/lookup-catalog.py standard "OWASP LLM05"
```

동작:

| 옵션 | 동작 |
|---|---|
| 기본 | Markdown을 파싱해 `catalog-index.json` 생성 |
| `--check` | 생성 결과와 기존 `catalog-index.json`이 같은지 확인. 다르면 실패 |
| `--output <path>` | 출력 파일 경로 지정 |
| `--pretty` | 안정적인 pretty JSON 출력. 기본값으로 권장 |

출력은 deterministic 해야 한다.

`lookup-catalog.py`는 `catalog-index.json`만 읽는 JSON-only lookup 검증기다. `<domain> <id-or-alias>`, `<domain> search <query>`, `<domain> list [category]`, `standard <query>`를 지원하고, 파일/anchor 해석 결과를 JSON으로 출력한다. JSON에 없는 ID/alias/file/anchor resolve를 위해 Markdown index를 fallback 파싱하지 않는다.

- `items` 정렬: `domain`, `category`, `id`
- `aliases` 정렬: `domain`, `alias`
- JSON key 순서 고정
- 생성 시각 때문에 `--check`가 매번 실패하지 않도록 `generated_at` 처리 정책 필요

권장 정책:

- 커밋 대상 JSON에는 `generated_at`을 포함하되, `--check`에서는 해당 필드를 제외하고 비교한다.
- 또는 `generated_at` 대신 `generated_from_commit`을 후속 CI에서만 채운다.

## 검증 불변식

생성기 또는 별도 `verify-catalog-index.py`는 아래 조건을 모두 검증한다.

1. 모든 `items[].id`는 `(domain, id)` 기준으로 유일하다.
2. 모든 `items[].file`은 존재한다.
3. 모든 `items[].anchor`는 해당 파일의 명시 anchor 또는 heading anchor로 존재한다.
4. 모든 `aliases[].target_id`는 같은 domain의 `items[].id`에 존재한다.
5. alias는 `(domain, alias)` 기준으로 유일하다.
6. `lookup_keys`는 같은 domain 안에서 충돌 시 deterministic 우선순위를 가진다.
7. 도메인별 `actual_count`는 `.counts.manifest`의 expected count와 일치한다.
8. 모든 `standards_mappings[].references` 파일은 존재해야 하며, anchor가 있으면 기존 semantic 검증과 같은 기준으로 해석돼야 한다.
9. `catalog-index.json`은 Codex/Claude 패키지에서 `generated_at` 제외 기준 동일해야 한다.

## 릴리즈/버전 운영 규칙

- `schema_version`: JSON 구조가 소비자 코드를 바꿔야 할 때 증가한다. 이번 `standards_mappings[]` 추가는 호환 확장이므로 `1.1`이다.
- `catalog_version`: 카탈로그 내용, alias, 표준 매핑이 바뀌면 `YYYY-MM` 또는 같은 달 내 추가 릴리즈용 `YYYY-MM.N` 형식으로 갱신한다.
- `generated_at`: 생성 시각이다. stale 비교와 Codex/Claude/설치본 동등성 비교에서는 제외한다.
- 설치본 sync 기준: repo의 `codex/skills/dev-advisor/`를 정본으로 보고 `/Users/zime/.codex/skills/dev-advisor/`에 `rsync -a --delete` 후 검증한다.
- 변경 로그: 이 문서의 변경 추적 섹션에 schema/catalog/lookup 정책 변화를 요약한다.

## lookup 충돌 정책

같은 domain에서 lookup key가 충돌하면 아래 우선순위로 해석한다.

1. primary `id`
2. alias
3. exact `title`
4. exact `title_ko`
5. normalized partial search

primary `id`끼리 충돌하면 생성 실패다. alias가 primary ID와 충돌하면 primary ID를 우선하되 warning을 출력한다. alias끼리 충돌하면 생성 실패다.

## 기존 semantic 검증과의 관계

현재 `verify-references.sh --check semantic`은 JSON 생성 전 단계의 무결성 게이트다. `catalog-index.json` 도입 후에도 이 검증은 유지한다.

추가될 검증 흐름:

```bash
bash scripts/verify-references.sh --check semantic
python3 scripts/generate-catalog-index.py --check
python3 scripts/lookup-catalog.py standard API3
```

`verify-references.sh`는 Markdown 원본의 의미적 무결성을 확인하고, `generate-catalog-index.py --check`는 JSON 산출물이 원본과 동기화되어 있는지 확인한다.

## CI 통합 계획

GitHub Actions 또는 다른 CI에서는 아래 순서가 적합하다.

1. `bash -n`으로 shell script 문법 확인
2. `bash codex/skills/dev-advisor/scripts/verify-references.sh`
3. `bash claude/skills/dev-advisor/scripts/verify-references.sh`
4. `python3 codex/skills/dev-advisor/scripts/generate-catalog-index.py --check`
5. `python3 claude/skills/dev-advisor/scripts/generate-catalog-index.py --check`
6. Codex/Claude `catalog-index.json` 내용 비교

초기에는 JSON 생성기를 CI에 넣지 않고, 설계 문서와 semantic 검증만 유지한다. 생성기가 안정화되면 `--check`를 필수 게이트로 승격한다.

## 단계별 도입

| 단계 | 산출물 | 완료 기준 |
|---|---|---|
| 1 | 이 설계 문서 | schema/source-of-truth/검증 규칙 합의 |
| 2 | generator prototype | Codex 패키지에서 JSON 생성 가능 |
| 3 | verifier/check mode | stale JSON 감지 가능 |
| 4 | Claude 패키지 동기화 | Codex/Claude 동일 로직 |
| 5 | CI 연결 | PR에서 stale/깨진 index 자동 차단 |
| 6 | 런타임 활용 | lookup이 JSON-only로 ID/alias/file/anchor resolve |

1-4단계는 완료 상태다. 6단계는 `lookup-catalog.py`로 JSON-only 해석 경로를 검증 가능한 상태까지 진행했다. 실제 에이전트 응답은 ID/alias/file/anchor resolve에 JSON만 사용하고, Markdown은 본문 인용 source로만 읽는다. 5단계 CI 연결은 별도 변경으로 진행한다.

## Open Questions

1. CI에서 `catalog-index.json` stale 검증을 언제 필수 게이트로 승격할지 결정해야 한다.
2. 표준 매핑이 커질 경우 `standards_mappings[]`를 top-level 유지할지, 별도 생성 산출물로 분리할지 재검토한다.

## 현재 권장 결정

- `catalog-index.json`은 생성 산출물로 git에 커밋한다.
- Markdown을 source of truth로 유지한다.
- `generated_at`은 포함하되 `--check` 비교에서는 제외한다.
- generator는 Codex/Claude 패키지 내부에 각각 둔다.
- root wrapper와 GitHub Actions는 후속 단계에서 추가한다.
- lookup resolve는 JSON-only로 고정하고, Markdown은 본문 source로 유지한다.

## 변경 추적

- 2026-05-17: schema `1.1`로 확장. `standards_mappings[]` 추가, `/language` alias를 JSON `aliases[]`와 item lookup key에 흡수, `lookup-catalog.py standard <query>` 추가, lookup 정책을 JSON-only로 고정.
