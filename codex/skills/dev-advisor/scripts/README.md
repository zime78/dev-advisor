# scripts/

dev-advisor 스킬 무결성 검증 도구.

## verify-references.sh (권장)

<!-- Counts are synced from .counts.manifest via bin/sync-skill-counts.sh. Do not edit count numbers manually. -->

**6 도메인 reference 무결성 검증** — 패턴 / 알고리즘 / 언어 / 보안 / 원칙 / 품질. 총 <!--counts:total-with-micro-->1267<!--/--> 항목.

```bash
bash scripts/verify-references.sh
bash scripts/verify-references.sh --check semantic
bash scripts/verify-references.sh --check quality
bash scripts/verify-references.sh --check today
```

검증 항목 (13 블록 + preflight/manifest 게이트 + languages 품질 서브게이트):

0. standalone/repo 모드 판별, `.counts.manifest` 동기화, 배포 제외 파일(`.DS_Store`, `__pycache__`, `*.pyc`) 금지, stale token 금지
0B. patterns/security/principles/quality 실제 항목 합계와 manifest 직접 대조
1. 카테고리별 anchor 수 == 헤더 수 (algorithms core 22 파일)
2. 전역 anchor unique
3. index.md 알고리즘 ID 매핑 표 행 == <!--counts:algorithms-->292<!--/-->
4. SKILL.md progressive disclosure 구조 (30 카테고리 진입점, 필수 섹션 헤더, 별칭 표)
5. languages reference 무결성 (≥60 언어 파일, 레거시 잔존 표현 0건)
6. languages 표준 14 섹션 헤더 spot-check (python/kotlin/rust/go/swift 누락 ≥ 2 면 fail)
   - languages 전체 품질 게이트: 75개 언어 파일 정확성, `## 관련 문서` 존재, Markdown 링크 3개 이상, 외부 공식 문서 후보 링크 2개 이상, `실사용 예제` 코드 블록 1개 이상, 예제 섹션 25단어 이상
7. patterns base reference 무결성 (base/P0/P1/P2/P3 카테고리, 부분 합계 == 200; 전체 <!--counts:patterns-->543<!--/-->은 10번과 합산)
8. security base reference 무결성 (base 13 보안 파일, base 합계 == 97; 전체 106은 10번과 합산)
9. **principles reference 무결성** (base/P0/P1/P3 원칙 파일, 부분 합계 == 107; 전체 <!--counts:principles-->211<!--/--> + <!--counts:micro-->20<!--/--> 부록은 10번과 합산)
10. Phase 2 확장 신규 카탈로그 anchor/header 일관성
11. SKILL.md 통합 모드 (`qa` / `qc` / `full` / `swarm`) 등록 검증
12. 핵심 Markdown 내부 링크/anchor 검증
13. semantic 검증
   - `patterns/index.md`, `security/index.md`, `quality/index.md`의 ID 매핑이 실제 파일의 명시 anchor 또는 heading anchor로 해석되는지 확인
   - 같은 도메인 안의 중복 ID를 실패 처리
   - 실제 파일에는 있으나 index에 없는 anchor/heading 후보는 warning으로만 출력
   - `principles/standards-mapping.md`의 `patterns/`, `security/`, `principles/`, `quality/` reference 파일/anchor 연결 확인
   - OWASP Web/API/Mobile/LLM 섹션의 security reference 잔존 여부 확인
   - `security/index.md`의 `Semantic validation 후보` 섹션과 `security-ai-model.md`의 LLM/Agent 보안 체크리스트 확인

6 도메인 항목 수:

| 도메인 | 파일 수 | 항목 수 |
|--------|--------:|--------:|
| Patterns   | 55 + index           | <!--counts:patterns-->543<!--/--> |
| Algorithms | 32 + index           | <!--counts:algorithms-->292<!--/--> |
| Languages  | ≥75 + index + domains | <!--counts:languages-->75<!--/--> |
| Security   | 14 + index           | <!--counts:security-->106<!--/--> |
| Principles | 23 + index + micro appendix | <!--counts:principles-->211<!--/--> + <!--counts:micro-->20<!--/--> appendix |
| Quality    | 2 + index            | <!--counts:quality-->20<!--/--> |
| **합계**   |                      | **<!--counts:total-with-micro-->1267<!--/-->** |

새 항목 추가 후 반드시 실행. CI 또는 pre-commit hook 통합 권장:

```yaml
# lefthook.yml 예시
pre-commit:
  commands:
    verify-references:
      run: bash scripts/verify-references.sh
      glob: ["SKILL.md", "references/**/*.md"]
```

## generate-catalog-index.py

Markdown reference 를 source of truth 로 읽어 런타임 lookup 용 `catalog-index.json`을 생성한다. JSON은 수동 편집하지 않고 이 스크립트로만 갱신한다.

```bash
python3 scripts/generate-catalog-index.py
python3 scripts/generate-catalog-index.py --check
python3 scripts/generate-catalog-index.py --output catalog-index.json
```

동작:

- 기본 실행: `catalog-index.json` 생성
- `--check`: 현재 JSON이 Markdown 원본과 동기화되어 있는지 확인하고, stale이면 실패
- Codex/Claude 패키지의 generator와 JSON은 동일해야 함
- `generated_at`은 `--check` 비교에서 제외하므로 실행 시각 차이로 실패하지 않음

현재 생성 산출물 기준:

| 항목 | 수 |
|---|---:|
| items | 1,276 |
| aliases | 213 |
| standards_mappings | 115 |
| domains | 6 |

Principles는 주 카탈로그 214개를 `entry`, 도메인 진입점 23개를 `category`, 미시 원칙 18개를 `appendix`로 색인한다. manifest의 `actual_count`는 기존과 같이 `entry`만 센다.

## lookup-catalog.py

`catalog-index.json`만 읽어 런타임 lookup을 검증한다. Markdown을 다시 파싱하지 않으므로 JSON-only lookup 전환의 회귀 확인에 사용한다.

```bash
python3 scripts/lookup-catalog.py principle srp
python3 scripts/lookup-catalog.py principle dry
python3 scripts/lookup-catalog.py principle solid
python3 scripts/lookup-catalog.py pattern singleton
python3 scripts/lookup-catalog.py quality quality-gate
python3 scripts/lookup-catalog.py principle search responsibility
python3 scripts/lookup-catalog.py principle list --type category
python3 scripts/lookup-catalog.py standard API3
python3 scripts/lookup-catalog.py standard "OWASP LLM05"
```

동작:

- `<domain> <id-or-alias>`: 같은 domain 안에서 ID → alias → lookup key 순서로 해석
- `<domain> search <query>`: ID, alias, 영문명, 한글명, category를 JSON key로 검색
- `<domain> list [category]`: JSON item 목록 출력. `--type entry|category|appendix` 필터 지원
- `standard <query>`: `standards_mappings[]`에서 표준 코드/명칭을 역조회하고 연결된 dev-advisor references 반환

## verify-anchors.sh (제거됨)

P3 정리 단계에서 `scripts/verify-anchors.sh` deprecated wrapper는 삭제되었다. anchor 검증은 `verify-references.sh` (또는 직접 `scripts/verify/verify-anchors.sh --check anchors`)를 사용한다.

실제 anchor 무결성 검사 로직은 `scripts/verify/verify-anchors.sh` 에 있으며 `verify-all.sh`의 [2/5] 단계로 실행된다.

## 신규 항목 추가 시 절차

1. 해당 도메인 카테고리 파일에 `## N. <영문명> (<한글명>)` 헤더 추가 (N 순차 증가, `^## [0-9]+\.` 패턴 준수)
2. 알고리즘이면 추가로 `<a id="..."></a>` anchor 부여, 카테고리 목차 표 갱신, `algorithms/index.md` ID 매핑 표 행 추가
3. 다른 도메인(패턴/보안/원칙/품질)은 카테고리 파일 + `<domain>/index.md` 매핑 갱신
4. SKILL.md 의 카운트 표 (`## 데이터 기반`, `## 호출 인터페이스`, `## 참조 문서`) 항목 수 +1
5. 루트와 스킬 패키지의 `.counts.manifest` 해당 도메인 카운트 expected 값 +1
6. `bash scripts/verify-references.sh`와 `python3 scripts/generate-catalog-index.py` 재실행
7. `python3 scripts/generate-catalog-index.py --check`까지 PASS 확인 후 커밋

언어 항목을 추가하거나 수정할 때는 `references/languages/<id>.md`에 `## 관련 문서`를 반드시 포함하고, 공식 문서/스펙 또는 레퍼런스/패키지·툴링 문서 링크를 최소 3개 제공한다. 예제는 hello-world가 아니라 해당 언어의 주 사용처를 보여주는 코드 블록으로 작성한다.
