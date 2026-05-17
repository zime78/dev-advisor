# catalog-index.json 설계

## 목적

`catalog-index.json`은 `dev-advisor`의 Markdown 카탈로그를 런타임에서 빠르게 조회하기 위한 기계용 색인이다. 사람은 계속 `references/**/*.md`와 각 도메인 `index.md`를 편집하고, JSON은 생성기로만 만드는 산출물로 둔다.

이 설계의 1차 목표는 lookup 성능 개선이 아니라 **source of truth 경계 고정**이다. JSON이 또 하나의 수동 관리 대상이 되면 Markdown, index 표, alias, anchor 사이의 불일치가 늘어나므로 생성/검증 규칙을 먼저 고정한다.

## 비목표와 현재 단계

- 이번 단계에서 lookup 런타임을 JSON 기반으로 바꾸지 않는다.
- 이번 단계에서 GitHub Actions를 추가하지 않는다.
- Markdown 문서 구조를 대규모로 재배치하지 않는다.

현재 구현 상태:

- `catalog-index.json`과 `scripts/generate-catalog-index.py`는 Codex/Claude 패키지에 생성했다.
- 생성 산출물은 Markdown 원본에서 재생성되며, 수동 편집 대상이 아니다.
- `--check`는 stale JSON을 감지하되 `generated_at` 차이는 비교에서 제외한다.
- GitHub Actions 연결과 JSON 기반 런타임 전환은 후속 작업으로 남긴다.

## Source Of Truth

| 데이터 | 원본 | JSON 내 역할 |
|---|---|---|
| 항목 본문 | `references/<domain>/*.md` | `file`, `anchor`, `title`, 본문 위치 |
| 도메인별 primary ID | `patterns/index.md`, `security/index.md`, `quality/index.md`, `algorithms/index.md`, `languages/index.md`, `principles/index.md` | `items[].id` |
| alias | 각 도메인 `index.md`의 별칭 표 | `aliases[]`, `items[].aliases` |
| expected count | `.counts.manifest` | `domains.<domain>.expected_count` 검증 |
| 표준 매핑 | `principles/standards-mapping.md` | cross-link 검증 대상, 런타임 표준 역조회 후보 |

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
  "schema_version": "1.0",
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
| Principles | `references/principles/index.md`의 도메인/alias 정보 + 원칙 파일 anchor | `entry` 212 + `category` 23 + `appendix` 18 색인 |
| Quality | `references/quality/index.md`의 `Quality ID 매핑` | 명시 anchor 중심 |

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
```

동작:

| 옵션 | 동작 |
|---|---|
| 기본 | Markdown을 파싱해 `catalog-index.json` 생성 |
| `--check` | 생성 결과와 기존 `catalog-index.json`이 같은지 확인. 다르면 실패 |
| `--output <path>` | 출력 파일 경로 지정 |
| `--pretty` | 안정적인 pretty JSON 출력. 기본값으로 권장 |

출력은 deterministic 해야 한다.

`lookup-catalog.py`는 `catalog-index.json`만 읽는 JSON 우선 lookup 검증기다. `<domain> <id-or-alias>`, `<domain> search <query>`, `<domain> list [category]`를 지원하고, 파일/anchor 해석 결과를 JSON으로 출력한다.

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
8. `catalog-index.json`은 Codex/Claude 패키지에서 reference 내용 기준 동일해야 한다.

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
| 6 | 런타임 활용 | lookup이 JSON을 우선 사용하고 Markdown fallback 유지 |

1-4단계는 완료 상태다. 6단계는 `lookup-catalog.py`로 JSON 우선 해석 경로를 검증 가능한 상태까지 진행했다. 실제 에이전트 응답은 JSON을 먼저 보고, JSON에 없는 예외 상황에서만 Markdown fallback을 사용한다. 5단계 CI 연결은 별도 변경으로 진행한다.

## Open Questions

1. Languages는 항목 수 75와 파일 stem 기반 lookup이면 충분한지, 별칭을 `items`에 흡수할지 결정해야 한다.
2. `standards-mapping.md`의 역방향 색인을 JSON에 포함할지 별도 `standards` 섹션으로 둘지 결정해야 한다.
3. JSON 기반 lookup 전환 후 Markdown fallback을 언제 제거할지 결정해야 한다.

## 현재 권장 결정

- `catalog-index.json`은 생성 산출물로 git에 커밋한다.
- Markdown을 source of truth로 유지한다.
- `generated_at`은 포함하되 `--check` 비교에서는 제외한다.
- generator는 Codex/Claude 패키지 내부에 각각 둔다.
- root wrapper와 GitHub Actions는 후속 단계에서 추가한다.
- 런타임 전환은 JSON 생성/검증이 안정화된 뒤 별도 작업으로 진행한다.
