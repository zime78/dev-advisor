# scripts/

dev-advisor 스킬 무결성 검증 도구.

## verify-references.sh (권장)

**6 도메인 reference 무결성 검증** — 패턴 / 알고리즘 / 언어 / 보안 / 원칙 / 품질. 총 1,251 항목.

```bash
bash scripts/verify-references.sh
bash scripts/verify-references.sh --check quality
bash scripts/verify-references.sh --check today
```

검증 항목 (12 블록 + preflight/manifest 게이트 + languages 품질 서브게이트):

0. standalone/repo 모드 판별, `.counts.manifest` 동기화, 배포 제외 파일(`.DS_Store`, `__pycache__`, `*.pyc`) 금지, stale token 금지
0B. patterns/security/principles/quality 실제 항목 합계와 manifest 직접 대조
1. 카테고리별 anchor 수 == 헤더 수 (algorithms base 23 파일)
2. 전역 anchor unique
3. index.md 알고리즘 ID 매핑 표 행 == 273
4. SKILL.md progressive disclosure 구조 (32 카테고리 진입점, 필수 섹션 헤더, 별칭 표)
5. languages reference 무결성 (≥60 언어 파일, 레거시 잔존 표현 0건)
6. languages 표준 14 섹션 헤더 spot-check (python/kotlin/rust/go/swift 누락 ≥ 2 면 fail)
   - languages 전체 품질 게이트: 75개 언어 파일 정확성, `## 관련 문서` 존재, Markdown 링크 3개 이상, 외부 공식 문서 후보 링크 2개 이상, `실사용 예제` 코드 블록 1개 이상, 예제 섹션 25단어 이상
7. patterns base reference 무결성 (base/P0/P1/P2/P3 카테고리, 부분 합계 == 208; 전체 547은 10번과 합산)
8. security base reference 무결성 (base 13 보안 파일, base 합계 == 97; 전체 106은 10번과 합산)
9. **principles reference 무결성** (base/P0/P1/P3 원칙 파일, 부분 합계 == 105; 전체 212 + 18 부록은 10번과 합산)
10. Phase 2 확장 신규 카탈로그 anchor/header 일관성
11. SKILL.md 통합 모드 (`qa` / `qc` / `full` / `swarm`) 등록 검증
12. 핵심 Markdown 내부 링크/anchor 검증

6 도메인 항목 수:

| 도메인 | 파일 수 | 항목 수 |
|--------|--------:|--------:|
| Patterns   | 55 + index           | 547 |
| Algorithms | 32 + index           | 273 |
| Languages  | ≥75 + index + domains | 75 |
| Security   | 14 + index           | 106 |
| Principles | 23 + index + micro appendix | 212 + 18 appendix |
| Quality    | 2 + index            | 20 |
| **합계**   |                      | **1,251** |

새 항목 추가 후 반드시 실행. CI 또는 pre-commit hook 통합 권장:

```yaml
# lefthook.yml 예시
pre-commit:
  commands:
    verify-references:
      run: bash scripts/verify-references.sh
      glob: ["SKILL.md", "references/**/*.md"]
```

## verify-anchors.sh (deprecated wrapper)

호환성을 위해 유지되는 wrapper. `verify-references.sh` 로 그대로 위임한다. 신규 사용처는 `verify-references.sh` 를 직접 호출한다.

## 신규 항목 추가 시 절차

1. 해당 도메인 카테고리 파일에 `## N. <영문명> (<한글명>)` 헤더 추가 (N 순차 증가, `^## [0-9]+\.` 패턴 준수)
2. 알고리즘이면 추가로 `<a id="..."></a>` anchor 부여, 카테고리 목차 표 갱신, `algorithms/index.md` ID 매핑 표 행 추가
3. 다른 도메인(패턴/보안/원칙/품질)은 카테고리 파일 + `<domain>/index.md` 매핑 갱신
4. SKILL.md 의 카운트 표 (`## 데이터 기반`, `## 호출 인터페이스`, `## 참조 문서`) 항목 수 +1
5. 루트와 스킬 패키지의 `.counts.manifest` 해당 도메인 카운트 expected 값 +1
6. 스크립트 재실행, 12 블록 모두 PASS 확인 후 커밋

언어 항목을 추가하거나 수정할 때는 `references/languages/<id>.md`에 `## 관련 문서`를 반드시 포함하고, 공식 문서/스펙 또는 레퍼런스/패키지·툴링 문서 링크를 최소 3개 제공한다. 예제는 hello-world가 아니라 해당 언어의 주 사용처를 보여주는 코드 블록으로 작성한다.
