#!/usr/bin/env bash
# verify-references.sh — dev-advisor 스킬의 6 도메인 reference 무결성 검증
# 검증 항목:
#   [1] 카테고리별 anchor 수 == 헤더 수 (algorithms base 23 파일 — db-query-optimizer 추가)
#   [2] 전역 anchor unique
#   [3] index.md 알고리즘 ID 매핑 표 행 == EXPECTED_ALGORITHMS (273)
#   [4] SKILL.md progressive disclosure 구조 (32 카테고리 진입점)
#   [5] languages reference 무결성 (75+ 언어)
#   [6] languages 표준 14 섹션 헤더 spot-check + 전체 언어 품질 게이트
#   [7] patterns reference 무결성 (base/P0/P1/P2/P3 카테고리 파일 존재, 전체 547)
#   [8] security reference 무결성 (base 14 파일 — 별도 도메인, 97 보안 패턴 + Privacy/Compliance 확장 = 106)
#   [9] principles reference 무결성 (base/P0/P1/P3 파일, 전체 212 + 부록 micro-principles 18)
#   [10] Phase 2 확장 신규 카탈로그 anchor/header 일관성
#   [11] SKILL.md 통합 모드 (qa / qc / full / swarm) 등록 검증
#   [12] 핵심 Markdown 내부 링크/anchor 검증
#
# 빠른 선택 검증:
#   --check quality  QA/QC 카탈로그와 문서 노출만 검증
#   --check today    오늘 확장 P0/P1/P2/P3 항목과 QA/QC만 검증
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ALGO_DIR="${SKILL_DIR}/references/algorithms"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../" && pwd)"
REPO_MODE=0
if [ -f "${REPO_ROOT}/README.md" ] && [ -d "${REPO_ROOT}/codex/skills/dev-advisor" ] && [ -d "${REPO_ROOT}/claude/skills/dev-advisor" ]; then
  REPO_MODE=1
fi

CHECK_SCOPE="all"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --check)
      if [ "$#" -lt 2 ]; then
        echo "FATAL: --check requires one of: all, today, quality" >&2
        exit 1
      fi
      CHECK_SCOPE="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--check all|today|quality]"
      exit 0
      ;;
    *)
      echo "FATAL: unknown argument: $1" >&2
      echo "Usage: $0 [--check all|today|quality]" >&2
      exit 1
      ;;
  esac
done

case "${CHECK_SCOPE}" in
  all|today|quality) ;;
  *)
    echo "FATAL: invalid --check value: ${CHECK_SCOPE} (expected all, today, quality)" >&2
    exit 1
    ;;
esac

# Shared counts manifest — silent divergence 차단.
# claude/codex 양쪽 verify 가 이 파일을 source 하여 expected 정수를 동일화한다.
# 탐색 우선순위: (1) repo root (SCRIPT_DIR 4단계 상위 — scripts/dev-advisor/skills/<runtime>/repo)
#                (2) skill root (SCRIPT_DIR 1단계 상위 — 배포 사본 fallback)
MANIFEST_REPO="${REPO_ROOT}/.counts.manifest"
MANIFEST_SKILL="$(cd "${SCRIPT_DIR}/../" && pwd)/.counts.manifest"
if [ "${REPO_MODE}" -eq 1 ] && [ -f "${MANIFEST_REPO}" ]; then
    # shellcheck disable=SC1090
    source "${MANIFEST_REPO}"
    MANIFEST="${MANIFEST_REPO}"
elif [ -f "${MANIFEST_SKILL}" ]; then
    # shellcheck disable=SC1090
    source "${MANIFEST_SKILL}"
    MANIFEST="${MANIFEST_SKILL}"
else
    echo "FATAL: .counts.manifest not found at ${MANIFEST_REPO} or ${MANIFEST_SKILL}" >&2
    exit 1
fi

PASS=0
FAIL=0

# 개별 검증 성공 메시지를 출력하고 통과 카운터를 증가시킨다.
ok() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
# 개별 검증 실패 메시지를 출력하고 실패 카운터를 증가시킨다.
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }

count_numbered_headers() {
  /usr/bin/grep -cE '^## [0-9]+\.' "$1" 2>/dev/null || echo 0
}

count_index_rows() {
  local file="$1"
  local start="$2"
  awk -v start="${start}" '
    index($0, start) == 1 {found=1; next}
    found && /^## / {found=0}
    found && /^\| `/ {count++}
    END {print count+0}
  ' "${file}" 2>/dev/null || echo 0
}

finish() {
  echo ""
  echo "======================================"
  if [ "${FAIL}" -eq 0 ]; then
    echo "✓ All integrity checks passed (${EXPECTED_PATTERNS} patterns / ${EXPECTED_ALGORITHMS} algorithms / ${EXPECTED_SECURITY} security / ${EXPECTED_LANGUAGES} languages / ${EXPECTED_PRINCIPLES} principles / ${EXPECTED_QUALITY} quality + ${EXPECTED_MICRO_PRINCIPLES} 부록 — 6 domains, ${EXPECTED_TOTAL} items + ${EXPECTED_MICRO_PRINCIPLES} 부록 = ${EXPECTED_TOTAL_WITH_MICRO} total)"
    exit 0
  else
    echo "✗ ${FAIL}개 검사 실패, ${PASS}개 통과"
    exit 1
  fi
}

check_quality_catalog() {
  echo "[Q] quality QA/QC 카탈로그 검증"
  QUALITY_DIR="${SKILL_DIR}/references/quality"

  if [ -d "${QUALITY_DIR}" ]; then
    ok "디렉토리 존재: references/quality/"
  else
    fail "디렉토리 누락: references/quality/"
  fi

  for f in index.md qa.md qc.md; do
    if [ -f "${QUALITY_DIR}/${f}" ]; then
      ok "파일 존재: references/quality/${f}"
    else
      fail "파일 누락: references/quality/${f}"
    fi
  done

  for entry in "qa.md:10" "qc.md:10"; do
    file="${entry%%:*}"
    expected="${entry##*:}"
    path="${QUALITY_DIR}/${file}"
    anchors=$(/usr/bin/grep -c '<a id=' "${path}" 2>/dev/null || echo 0)
    headers=$(/usr/bin/grep -cE '^## [0-9]+\.' "${path}" 2>/dev/null || echo 0)
    if [ "${anchors}" -eq "${expected}" ] && [ "${headers}" -eq "${expected}" ]; then
      ok "quality/${file}: anchors=${anchors} headers=${headers}"
    else
      fail "quality/${file}: anchors=${anchors} headers=${headers} expected=${expected}"
    fi
  done

  quality_index_count=$(awk '
    /^## Quality ID 매핑/{found=1; next}
    found && /^## /{found=0}
    found && /^\| `/{count++}
    END{print count+0}
  ' "${QUALITY_DIR}/index.md" 2>/dev/null || echo 0)
  if [ "${quality_index_count}" -eq "${EXPECTED_QUALITY}" ]; then
    ok "quality/index.md ID 매핑: ${quality_index_count}개"
  else
    fail "quality/index.md ID 매핑: 기대=${EXPECTED_QUALITY}, 실제=${quality_index_count}"
  fi
}

check_quality_exposure() {
  echo ""
  echo "[Q2] QA/QC 호출 노출 검증"
  SKILL_FILE="${SKILL_DIR}/SKILL.md"
  EXAMPLES_FILE="${SKILL_DIR}/references/examples.md"
  TEMPLATES_FILE="${SKILL_DIR}/references/output_templates.md"
  ROOT_README="${REPO_ROOT}/README.md"

  for token in '/dev-advisor qa' '/dev-advisor qc' '/quality'; do
    if grep -q "${token}" "${SKILL_FILE}"; then
      ok "SKILL.md 노출: ${token}"
    else
      fail "SKILL.md 누락: ${token}"
    fi
  done

  if grep -q '/dev-advisor qa' "${EXAMPLES_FILE}" && grep -q '/dev-advisor qc' "${EXAMPLES_FILE}"; then
    ok "examples.md 에 qa/qc 예시 존재"
  else
    fail "examples.md 에 qa 또는 qc 예시 누락"
  fi

  if grep -q '^## 6\. qa' "${TEMPLATES_FILE}" && grep -q '^## 7\. qc' "${TEMPLATES_FILE}"; then
    ok "output_templates.md 에 qa/qc 템플릿 존재"
  else
    fail "output_templates.md 에 qa 또는 qc 템플릿 누락"
  fi

  if [ "${REPO_MODE}" -eq 1 ]; then
    if [ -f "${ROOT_README}" ] && grep -q '/quality' "${ROOT_README}" && grep -q '/dev-advisor qa' "${ROOT_README}" && grep -q '/dev-advisor qc' "${ROOT_README}"; then
      ok "README.md 에 /quality 및 qa/qc 노출"
    else
      fail "README.md 에 /quality 또는 qa/qc 노출 누락"
    fi
  else
    ok "standalone 설치본: repo README 검증 생략"
  fi
}

check_today_catalog() {
  echo "[T] 오늘 확장 P0/P1/P2/P3 카탈로그 검증"
  TODAY_FILES=(
    "patterns/master-data-management.md:6"
    "patterns/data-quality-governance.md:6"
    "patterns/web-performance.md:6"
    "patterns/data-warehousing-bi.md:6"
    "patterns/graphics-rendering.md:5"
    "patterns/ar-vr-xr.md:5"
    "patterns/serverless-faas.md:5"
    "patterns/hpc-scientific.md:6"
    "patterns/mobile-app.md:15"
    "algorithms/db-query-optimizer.md:5"
    "principles/database-fundamentals.md:8"
    "principles/sdlc-models.md:7"
    "principles/scaled-agile.md:6"
    "principles/professional-ethics.md:6"
    "principles/standards-mapping.md:5"
    "principles/configuration-management.md:6"
    "principles/hci-methodology.md:6"
    "principles/formal-methods.md:5"
  )

  for entry in "${TODAY_FILES[@]}"; do
    file="${entry%%:*}"
    expected="${entry##*:}"
    path="${SKILL_DIR}/references/${file}"
    if [ ! -f "${path}" ]; then
      fail "${file}: 파일 누락"
      continue
    fi
    anchors=$(/usr/bin/grep -c '<a id=' "${path}" 2>/dev/null || echo 0)
    headers=$(/usr/bin/grep -cE '^## [0-9]+\.' "${path}" 2>/dev/null || echo 0)
    if [ "${anchors}" -ge "${expected}" ] && [ "${headers}" -ge "${expected}" ]; then
      ok "${file}: anchors=${anchors} headers=${headers} (expected≥${expected})"
    else
      fail "${file}: anchors=${anchors} headers=${headers} expected≥${expected}"
    fi
  done
}

check_manifest_alignment() {
  echo "[0] manifest / 배포 hygiene 검증"

  if [ "${REPO_MODE}" -eq 1 ]; then
    for manifest_path in \
      "${REPO_ROOT}/.counts.manifest" \
      "${REPO_ROOT}/codex/skills/dev-advisor/.counts.manifest" \
      "${REPO_ROOT}/claude/skills/dev-advisor/.counts.manifest"
    do
      if [ -f "${manifest_path}" ]; then
        ok "manifest 존재: ${manifest_path#${REPO_ROOT}/}"
      else
        fail "manifest 누락: ${manifest_path#${REPO_ROOT}/}"
      fi
    done

    if cmp -s "${REPO_ROOT}/.counts.manifest" "${REPO_ROOT}/codex/skills/dev-advisor/.counts.manifest" \
      && cmp -s "${REPO_ROOT}/.counts.manifest" "${REPO_ROOT}/claude/skills/dev-advisor/.counts.manifest"; then
      ok "root/codex/claude manifest 동일"
    else
      fail "root/codex/claude manifest 불일치"
    fi
  else
    ok "standalone 설치본 manifest 사용: ${MANIFEST#${SKILL_DIR}/}"
  fi

  forbidden_files=$(find "${SKILL_DIR}" \( -name .DS_Store -o -name __pycache__ -o -name '*.pyc' \) -print 2>/dev/null || true)
  if [ -z "${forbidden_files}" ]; then
    ok "배포 제외 파일 없음 (.DS_Store / __pycache__ / *.pyc)"
  else
    fail "배포 제외 파일 발견: $(printf '%s' "${forbidden_files}" | tr '\n' ' ')"
  fi

  stale_pattern='5'"중"'|7'"모드"'|core 16'"3"'|4'"중 카탈로그"'|5'" 서브에이전트"'|\b49'"6"'\b|\b26'"8"'\b|\b53'"9"'\b'
  stale_hits=$(
    {
      /usr/bin/grep -RInE "${stale_pattern}" \
        "${SKILL_DIR}/SKILL.md" "${SKILL_DIR}/references" "${SKILL_DIR}/scripts/README.md" 2>/dev/null || true
      if [ "${REPO_MODE}" -eq 1 ]; then
        /usr/bin/grep -InE "${stale_pattern}" \
          "${REPO_ROOT}/README.md" 2>/dev/null || true
      fi
    }
  )
  if [ -z "${stale_hits}" ]; then
    ok "stale token 금지 검사 통과"
  else
    fail "stale token 발견: $(printf '%s' "${stale_hits}" | head -n 5 | tr '\n' ' ')"
  fi
}

check_catalog_manifest_totals() {
  echo "[0B] 카탈로그 총계 / manifest 대조"

  patterns_headers=$(find "${SKILL_DIR}/references/patterns" -name '*.md' ! -name 'index.md' -print0 \
    | xargs -0 /usr/bin/grep -hE '^## [0-9]+\.' 2>/dev/null | wc -l | tr -d ' ')
  if [ "${patterns_headers}" -eq "${EXPECTED_PATTERNS}" ]; then
    ok "patterns 실제 ## N. 헤더 합계 = manifest (${patterns_headers})"
  else
    fail "patterns 실제 ## N. 헤더 합계=${patterns_headers}, manifest=${EXPECTED_PATTERNS}"
  fi

  security_privacy=$(/usr/bin/grep -c '<a id=' "${SKILL_DIR}/references/security/privacy-engineering.md" 2>/dev/null || echo 0)
  security_headers=$(for f in security security-authn security-authz security-crypto-ops security-data-protection security-api-web security-supply-chain security-platform security-sdlc security-detect-respond security-mobile security-ai-model compliance; do
      count_numbered_headers "${SKILL_DIR}/references/security/${f}.md"
    done | awk '{s+=$1} END{print s+0}')
  security_total=$((security_headers + security_privacy))
  if [ "${security_total}" -eq "${EXPECTED_SECURITY}" ]; then
    ok "security 실제 항목 합계 = manifest (${security_total})"
  else
    fail "security 실제 항목 합계=${security_total}, manifest=${EXPECTED_SECURITY}"
  fi

  principles_headers=$(find "${SKILL_DIR}/references/principles" -name '*.md' ! -name 'index.md' ! -name 'micro-principles.md' -print0 \
    | xargs -0 /usr/bin/grep -hE '^## [0-9]+\.' 2>/dev/null | wc -l | tr -d ' ')
  if [ "${principles_headers}" -eq "${EXPECTED_PRINCIPLES}" ]; then
    ok "principles 실제 ## N. 헤더 합계 = manifest (${principles_headers})"
  else
    fail "principles 실제 ## N. 헤더 합계=${principles_headers}, manifest=${EXPECTED_PRINCIPLES}"
  fi

  quality_headers=$(find "${SKILL_DIR}/references/quality" -name '*.md' ! -name 'index.md' -print0 \
    | xargs -0 /usr/bin/grep -hE '^## [0-9]+\.' 2>/dev/null | wc -l | tr -d ' ')
  if [ "${quality_headers}" -eq "${EXPECTED_QUALITY}" ]; then
    ok "quality 실제 ## N. 헤더 합계 = manifest (${quality_headers})"
  else
    fail "quality 실제 ## N. 헤더 합계=${quality_headers}, manifest=${EXPECTED_QUALITY}"
  fi
}

# Pre-flight: TMPDIR/temp-file writability check.
# 사유: here-doc 및 process substitution 이 임시파일을 생성한다.
# sandbox / read-only 환경에서 임시파일 생성이 막히면 본문 검사가 silent
# skip 되어 false PASS 가 발생하므로 시작 시점에 명시 FAIL 처리한다.
_tmp_probe="$(mktemp 2>/dev/null)" || _tmp_probe=""
if [ -z "${_tmp_probe}" ] || [ ! -w "${_tmp_probe}" ]; then
  echo "  ✗ FATAL: 임시파일 생성 불가 (TMPDIR=${TMPDIR:-/tmp}) — here-doc/process substitution 무력화로 false PASS 위험" >&2
  FAIL=$((FAIL + 1))
  echo ""
  echo "======================================"
  echo "✗ ${FAIL}개 검사 실패, ${PASS}개 통과 (pre-flight 단계 차단)" >&2
  exit 1
fi
rm -f "${_tmp_probe}"

echo "=== dev-advisor anchor integrity check ==="
echo ""

check_manifest_alignment
echo ""
check_catalog_manifest_totals
echo ""

if [ "${CHECK_SCOPE}" = "quality" ]; then
  check_quality_catalog
  check_quality_exposure
  finish
fi

if [ "${CHECK_SCOPE}" = "today" ]; then
  check_today_catalog
  echo ""
  check_quality_catalog
  check_quality_exposure
  finish
fi

# ─────────────────────────────────────────────
# CHECK 1: 카테고리별 anchor 수 == 기대 카운트
# ─────────────────────────────────────────────
echo "[1] 카테고리별 anchor 수 검증"

expected_count() {
  case "$1" in
    sorting)              echo 16 ;;
    searching)            echo 13 ;;
    graph)                echo 18 ;;
    dynamic-programming)  echo 12 ;;
    divide-conquer)       echo 5  ;;
    greedy)               echo 5  ;;
    backtracking)         echo 5  ;;
    string)               echo 11 ;;
    math)                 echo 14 ;;
    data-structures)      echo 9  ;;
    geometry)             echo 7  ;;
    flow)                 echo 4  ;;
    matching)             echo 3  ;;
    crypto)               echo 6  ;;
    compression)          echo 5  ;;
    game-ai)              echo 5  ;;
    ml)                   echo 13 ;;
    probabilistic)        echo 4  ;;
    consensus)            echo 3  ;;
    distributed)          echo 12 ;;
    concurrent)           echo 10 ;;
    parsing)              echo 10 ;;
    db-query-optimizer)   echo 5  ;;
    *)                    echo 0  ;;
  esac
}

for cat in sorting searching graph dynamic-programming divide-conquer greedy backtracking string math data-structures geometry flow matching crypto compression game-ai ml probabilistic consensus distributed concurrent parsing db-query-optimizer; do
  file="${ALGO_DIR}/${cat}.md"
  expected=$(expected_count "${cat}")
  actual=$(grep -c '<a id=' "${file}" 2>/dev/null || echo 0)
  if [ "${actual}" -eq "${expected}" ]; then
    ok "${cat}: ${actual}개"
  else
    fail "${cat}: 기대=${expected}, 실제=${actual}"
  fi
done

# ─────────────────────────────────────────────
# CHECK 2: 전역 anchor unique 검증
# ─────────────────────────────────────────────
echo ""
echo "[2] 전역 anchor unique 검증"

dupes=$(grep -h '<a id=' "${ALGO_DIR}"/*.md \
  | grep -o 'id="[^"]*"' \
  | sort \
  | uniq -d)

if [ -z "${dupes}" ]; then
  ok "중복 anchor 없음"
else
  fail "중복 anchor 발견:\n${dupes}"
fi

# ─────────────────────────────────────────────
# CHECK 3: index.md ID 매핑 표 링크 행 수 == EXPECTED_ALGORITHMS
# ─────────────────────────────────────────────
echo ""
echo "[3] index.md 알고리즘 ID 매핑 표 행 수 검증"

INDEX_FILE="${ALGO_DIR}/index.md"
index_count=$(awk '/## 알고리즘 ID 매핑/{found=1; next} found && /^\|.*\.md#/{count++} END{print count+0}' "${INDEX_FILE}")

if [ "${index_count}" -eq "${EXPECTED_ALGORITHMS}" ]; then
  ok "index.md 링크 행: ${index_count}개"
else
  fail "index.md 링크 행: 기대=${EXPECTED_ALGORITHMS}, 실제=${index_count}"
fi

# ─────────────────────────────────────────────
# CHECK 4: SKILL.md progressive disclosure 구조 검증
#   - 카테고리 진입점 표 데이터 행 == 19
#   - 필수 섹션 3개 존재 (ID 인덱스 / 명명 규칙 / 호출 동작)
#   - 별칭 표 존재 + 데이터 행 >= 5
# ─────────────────────────────────────────────
echo ""
echo "[4] algorithms reference progressive disclosure 구조 검증 (SKILL.md → references/algorithms/index.md redirect)"

SKILL_FILE="${SKILL_DIR}/SKILL.md"
ALGO_INDEX="${SKILL_DIR}/references/algorithms/index.md"
# redirect 사유: progressive disclosure 표준 패턴, 원본 SKILL.md 의
#   ## 알고리즘 ID 인덱스 + ## 알고리즘 ID 명명 규칙
#   + ## `/algorithm <id>` 호출 동작 + ### 알고리즘 별칭
#   4 섹션을 references/algorithms/index.md 로 이동 후 hard-check 도 같이 이동.

# 4-1. 카테고리 진입점 표 (## 알고리즘 ID 인덱스 이후 첫 ## 헤더 전까지) 데이터 행 22개
cat_rows=$(awk '
  /^## 알고리즘 ID 인덱스/{f=1; next}
  f && /^## /{f=0}
  f && /^\| / && !/^\|[-| :]+\|/ && !/^\| 카테고리 /{c++}
  END{print c+0}
' "${ALGO_INDEX}")

if [ "${cat_rows}" -eq 32 ]; then
  ok "카테고리 진입점 표 행: ${cat_rows}개"
else
  fail "카테고리 진입점 표 행: 기대=32, 실제=${cat_rows}"
fi

# 4-2. 필수 섹션 3개 헤더 존재 (algorithms/index.md 내)
for hdr in '## 알고리즘 ID 인덱스' '## 알고리즘 ID 명명 규칙' '## `/algorithm <id>` 호출 동작'; do
  if grep -qF "${hdr}" "${ALGO_INDEX}"; then
    ok "섹션 존재: ${hdr}"
  else
    fail "섹션 누락: ${hdr}"
  fi
done

# 4-3. 별칭 표 데이터 행 >= 5 (algorithms/index.md 내)
alias_rows=$(awk '
  /^### 알고리즘 별칭/{f=1; next}
  f && /^## /{f=0}
  f && /^\| / && !/^\|[-| :]+\|/ && !/^\| 별칭 /{c++}
  END{print c+0}
' "${ALGO_INDEX}")

if [ "${alias_rows}" -ge 5 ]; then
  ok "별칭 표 행: ${alias_rows}개 (>=5)"
else
  fail "별칭 표 행: 기대>=5, 실제=${alias_rows}"
fi

# 4-4. index.md 의 ID 매핑이 lookup 대체이므로, index.md 매핑 행 카운트(check 3)가 EXPECTED_ALGORITHMS 인지로 보강.
#       이미 check 3 에서 검증됨.

# ─────────────────────────────────────────────
# CHECK 5: 프로그래밍 언어 reference 무결성
#   - references/languages/ 디렉토리 존재
#   - index.md / domains.md 존재
#   - 언어 파일 (kebab-case .md) >= 60개
#   - 레거시 잔존 표현 0건
#   - SKILL.md 의 "## 프로그래밍 언어 reference" 섹션 + "### 언어 별칭" 표 존재
# ─────────────────────────────────────────────
echo ""
echo "[5] 프로그래밍 언어 reference 무결성 검증"

LANG_DIR="${SKILL_DIR}/references/languages"

if [ -d "${LANG_DIR}" ]; then
  ok "디렉토리 존재: references/languages/"
else
  fail "디렉토리 누락: references/languages/"
fi

if [ -f "${LANG_DIR}/index.md" ] && [ -f "${LANG_DIR}/domains.md" ]; then
  ok "메타 파일 존재: index.md + domains.md"
else
  fail "메타 파일 누락 (index.md 또는 domains.md)"
fi

lang_files=$(/bin/ls "${LANG_DIR}"/*.md 2>/dev/null | /usr/bin/grep -vE '/(index|domains)\.md$' | wc -l | tr -d ' ')
if [ "${lang_files}" -ge 60 ]; then
  ok "언어 파일 수: ${lang_files}개 (>=60)"
else
  fail "언어 파일 수: 기대>=60, 실제=${lang_files}"
fi

legacy_residue=$(/usr/bin/grep -rli 'Codex 스킬용\|로컬 Codex 스킬' "${LANG_DIR}" 2>/dev/null | wc -l | tr -d ' ' || true)
legacy_residue=${legacy_residue:-0}
if [ "${legacy_residue}" -eq 0 ]; then
  ok "레거시 잔존 표현: 0건"
else
  fail "레거시 잔존 표현: ${legacy_residue}건"
fi

# CHECK 5 redirect: SKILL.md → references/languages/index.md
# redirect 사유: progressive disclosure 표준 패턴, 원본 SKILL.md 의
#   ## 프로그래밍 언어 reference + ### 언어 별칭 헤더를 languages/index.md 로 이동.
if /usr/bin/grep -q '^## 프로그래밍 언어 reference' "${LANG_DIR}/index.md"; then
  ok "languages/index.md 섹션 존재: ## 프로그래밍 언어 reference"
else
  fail "languages/index.md 섹션 누락: ## 프로그래밍 언어 reference"
fi

if /usr/bin/grep -q '^### 언어 별칭' "${LANG_DIR}/index.md"; then
  ok "languages/index.md 섹션 존재: ### 언어 별칭"
else
  fail "languages/index.md 섹션 누락: ### 언어 별칭"
fi

# ─────────────────────────────────────────────
# CHECK 6: languages 표준 14 섹션 헤더 spot-check
#   - 5개 대표 언어(python, kotlin, rust, go, swift)에서 14 표준 헤더 모두 존재해야 함
#   - 누락 ≥ 2 면 해당 언어 fail
# ─────────────────────────────────────────────
echo ""
echo "[6] languages 표준 14 섹션 헤더 spot-check"

STD_HEADERS='## 핵심 판단
## 사용처
## 특징
## 장점
## 제약
## 적합한 프로젝트
## 부적합하거나 주의할 프로젝트
## 대표 생태계와 도구
## 학습 난이도와 선행 지식
## 운영/배포 관점
## 타입/런타임 특성
## 실사용 예제
## 비교 포인트
## 도입 전 체크리스트'

for lang in python kotlin rust go swift; do
  lf="${LANG_DIR}/${lang}.md"
  if [ ! -f "${lf}" ]; then
    fail "${lang}.md 누락"
    continue
  fi
  # here-doc 대신 printf | while … 패턴 사용.
  # 사유: here-doc 은 bash 가 임시파일을 만들어 redirect 하므로 TMPDIR 이
  # 읽기전용/쓰기불가일 때 stdin 이 비어 silent skip → false PASS 가능.
  # printf 의 stdout 을 직접 파이프로 넘기면 임시파일 없이 stream 으로 처리되며,
  # 변수 공유 손실은 임시 cnt 파일로 우회 (pre-flight 에서 mktemp 통과 보장).
  _hdr_cnt_file="$(mktemp)" || { fail "${lang}.md: cnt tmpfile 생성 실패"; continue; }
  echo 0 > "${_hdr_cnt_file}"
  expected_hdrs=0
  printf '%s\n' "${STD_HEADERS}" | while IFS= read -r hdr; do
    [ -z "${hdr}" ] && continue
    if ! /usr/bin/grep -qF "${hdr}" "${lf}"; then
      cur=$(cat "${_hdr_cnt_file}")
      echo $((cur + 1)) > "${_hdr_cnt_file}"
    fi
  done
  expected_hdrs=$(printf '%s\n' "${STD_HEADERS}" | /usr/bin/grep -c '^## ' || true)
  missing=$(cat "${_hdr_cnt_file}")
  rm -f "${_hdr_cnt_file}"
  # 14 표준 헤더가 입력에 모두 전달되지 않았다면(파이프 손상 등) FAIL
  if [ "${expected_hdrs}" -ne 14 ]; then
    fail "${lang}.md: STD_HEADERS 전달 손상 (기대=14, 실제 입력=${expected_hdrs}) — pipe/redirect 무력화 의심"
    continue
  fi
  if [ "${missing}" -lt 2 ]; then
    ok "${lang}.md: 누락 헤더 ${missing}개 (<2)"
  else
    fail "${lang}.md: 누락 헤더 ${missing}개 (>=2)"
  fi
done

# ─────────────────────────────────────────────
# CHECK 6B: languages 전체 품질 게이트
#   - 언어 파일 75개 정확히 존재
#   - 모든 언어 파일에 `## 관련 문서` 존재
#   - Markdown 링크 최소 3개
#   - 외부 공식 문서 후보 링크 최소 2개
#   - `## 실사용 예제` 섹션에 코드 블록 1개 이상
#   - 예제 섹션 단어 수 25개 이상
# ─────────────────────────────────────────────
echo ""
echo "[6B] languages 전체 품질 게이트"

if EXPECTED_LANGUAGES="${EXPECTED_LANGUAGES}" python3 - "${LANG_DIR}" <<'PY'
import os
import re
import sys
from pathlib import Path

lang_dir = Path(sys.argv[1])
expected_langs = int(os.environ["EXPECTED_LANGUAGES"])
files = sorted(p for p in lang_dir.glob("*.md") if p.name not in {"index.md", "domains.md"})
issues = []

if len(files) != expected_langs:
    issues.append(f"언어 파일 수 기대={expected_langs}, 실제={len(files)}")

section_re = re.compile(r"(?ms)^## 실사용 예제\n(.*?)(?=^## |\Z)")
link_re = re.compile(r"\[[^\]\n]+\]\(([^)\n]+)\)")
fence_re = re.compile(r"```[A-Za-z0-9_#+.-]*\n.*?\n```", re.S)
word_re = re.compile(r"[A-Za-z0-9_가-힣]+")

for path in files:
    text = path.read_text(encoding="utf-8")
    rel = path.name
    if "## 관련 문서" not in text:
        issues.append(f"{rel}: `## 관련 문서` 누락")

    links = link_re.findall(text)
    external_links = [
        link for link in links
        if link.startswith(("https://", "http://"))
    ]
    if len(links) < 3:
        issues.append(f"{rel}: Markdown 링크 {len(links)}개 (<3)")
    if len(external_links) < 2:
        issues.append(f"{rel}: 외부 공식 문서 후보 링크 {len(external_links)}개 (<2)")

    match = section_re.search(text)
    if not match:
        issues.append(f"{rel}: `## 실사용 예제` 섹션 누락")
        continue
    example = match.group(1).strip()
    if not fence_re.search(example):
        issues.append(f"{rel}: 실사용 예제 코드 블록 누락")
    words = word_re.findall(example)
    if len(words) < 25:
        issues.append(f"{rel}: 실사용 예제 단어 수 {len(words)}개 (<25)")

if issues:
    for issue in issues:
        print(issue)
    sys.exit(1)
print(f"{expected_langs}개 언어 파일 품질 기준 통과")
PY
then
  ok "languages 관련 문서/링크/예제 품질 기준 통과"
else
  fail "languages 품질 기준 실패"
fi

# ─────────────────────────────────────────────
# CHECK 7: patterns reference 무결성
#   - patterns/ index.md + base 15 카테고리 md 파일 존재
#     (GoF 3: creational/structural/behavioral +
#      아키텍처/분산/신뢰성/동시성/통합 +
#      DDD 전술/데이터 접근/테스트/Observability/AI-LLM/배포/캐싱)
#   - base 패턴 개수 합계 == 159
# ─────────────────────────────────────────────
echo ""
echo "[7] patterns reference 무결성 검증"

PATTERNS_DIR="${SKILL_DIR}/references/patterns"

for f in index.md creational.md structural.md behavioral.md architectural.md distributed.md reliability.md concurrency.md integration.md ddd-tactical.md data-access.md testing.md observability.md ai-llm.md deployment.md caching.md master-data-management.md data-quality-governance.md web-performance.md data-warehousing-bi.md graphics-rendering.md ar-vr-xr.md serverless-faas.md hpc-scientific.md; do
  if [ -f "${PATTERNS_DIR}/${f}" ]; then
    ok "파일 존재: references/patterns/${f}"
  else
    fail "파일 누락: references/patterns/${f}"
  fi
done

count_pat() {
  /usr/bin/grep -cE '^## [0-9]+\.' "${PATTERNS_DIR}/$1.md" 2>/dev/null || echo 0
}

pat_creational=$(count_pat creational)
pat_structural=$(count_pat structural)
pat_behavioral=$(count_pat behavioral)
pat_architectural=$(count_pat architectural)
pat_distributed=$(count_pat distributed)
pat_reliability=$(count_pat reliability)
pat_concurrency=$(count_pat concurrency)
pat_integration=$(count_pat integration)
pat_ddd=$(count_pat ddd-tactical)
pat_data=$(count_pat data-access)
pat_testing=$(count_pat testing)
pat_observ=$(count_pat observability)
pat_aillm=$(count_pat ai-llm)
pat_deploy=$(count_pat deployment)
pat_caching=$(count_pat caching)
# P0 신설 2 카테고리
pat_mdm=$(count_pat master-data-management)
pat_dq=$(count_pat data-quality-governance)
# P1 신설 2 카테고리
pat_webperf=$(count_pat web-performance)
pat_dwh=$(count_pat data-warehousing-bi)
# P2 신설 3 카테고리
pat_gfx=$(count_pat graphics-rendering)
pat_xr=$(count_pat ar-vr-xr)
pat_faas=$(count_pat serverless-faas)
# P3 신설 1 카테고리
pat_hpc=$(count_pat hpc-scientific)
pat_total=$((pat_creational + pat_structural + pat_behavioral + pat_architectural + pat_distributed + pat_reliability + pat_concurrency + pat_integration + pat_ddd + pat_data + pat_testing + pat_observ + pat_aillm + pat_deploy + pat_caching + pat_mdm + pat_dq + pat_webperf + pat_dwh + pat_gfx + pat_xr + pat_faas + pat_hpc))

check_pat() {
  if [ "$2" -eq "$3" ]; then
    ok "$1: $2개"
  else
    fail "$1: 기대=$3, 실제=$2"
  fi
}

check_pat creational                     "${pat_creational}"     5
check_pat structural                     "${pat_structural}"     7
check_pat behavioral                     "${pat_behavioral}"     11
check_pat architectural                  "${pat_architectural}"  17
check_pat distributed                    "${pat_distributed}"    11
check_pat reliability                    "${pat_reliability}"    9
check_pat concurrency                    "${pat_concurrency}"    14
check_pat integration                    "${pat_integration}"    17
check_pat ddd-tactical                   "${pat_ddd}"            11
check_pat data-access                    "${pat_data}"           10
check_pat testing                        "${pat_testing}"        11
check_pat observability                  "${pat_observ}"         10
check_pat ai-llm                         "${pat_aillm}"          12
check_pat deployment                     "${pat_deploy}"         9
check_pat caching                        "${pat_caching}"        9
# P0 신설 2 카테고리
check_pat master-data-management         "${pat_mdm}"            6
check_pat data-quality-governance        "${pat_dq}"             6
# P1 신설 2 카테고리
check_pat web-performance                "${pat_webperf}"        6
check_pat data-warehousing-bi            "${pat_dwh}"            6
# P2 신설 3 카테고리
check_pat graphics-rendering             "${pat_gfx}"            5
check_pat ar-vr-xr                       "${pat_xr}"             5
check_pat serverless-faas                "${pat_faas}"           5
# P3 신설 1 카테고리
check_pat hpc-scientific                 "${pat_hpc}"            6

# 15 base + 2 P0 신설 + 2 P1 신설 + 3 P2 신설 + 1 P3 신설 + P2 확장 (architectural +1, integration +1, distributed +2) = 159 + 12 + 12 + 15 + 6 + 4 = 208
if [ "${pat_total}" -eq 208 ]; then
  ok "base+P0+P1+P2+P3 패턴 합계: ${pat_total}개"
else
  fail "base+P0+P1+P2+P3 패턴 합계: 기대=208, 실제=${pat_total}"
fi

# ─────────────────────────────────────────────
# CHECK 8: security reference 무결성 (4번째 도메인)
#   - security/ index.md + 13 보안 md 파일 존재
#   - base 보안 합계 == 97
# ─────────────────────────────────────────────
echo ""
echo "[8] security reference 무결성 검증 (별도 도메인)"

SECURITY_DIR="${SKILL_DIR}/references/security"

if [ -d "${SECURITY_DIR}" ]; then
  ok "디렉토리 존재: references/security/"
else
  fail "디렉토리 누락: references/security/"
fi

for f in index.md security.md security-authn.md security-authz.md security-crypto-ops.md security-data-protection.md security-api-web.md security-supply-chain.md security-platform.md security-sdlc.md security-detect-respond.md security-mobile.md security-ai-model.md compliance.md; do
  if [ -f "${SECURITY_DIR}/${f}" ]; then
    ok "파일 존재: references/security/${f}"
  else
    fail "파일 누락: references/security/${f}"
  fi
done

count_sec() {
  /usr/bin/grep -cE '^## [0-9]+\.' "${SECURITY_DIR}/$1.md" 2>/dev/null || echo 0
}

sec_meta=$(count_sec security)
sec_authn=$(count_sec security-authn)
sec_authz=$(count_sec security-authz)
sec_crypto=$(count_sec security-crypto-ops)
sec_data=$(count_sec security-data-protection)
sec_api=$(count_sec security-api-web)
sec_supply=$(count_sec security-supply-chain)
sec_platform=$(count_sec security-platform)
sec_sdlc=$(count_sec security-sdlc)
sec_detect=$(count_sec security-detect-respond)
sec_mobile=$(count_sec security-mobile)
sec_ai=$(count_sec security-ai-model)
sec_compliance=$(count_sec compliance)
sec_total=$((sec_meta + sec_authn + sec_authz + sec_crypto + sec_data + sec_api + sec_supply + sec_platform + sec_sdlc + sec_detect + sec_mobile + sec_ai + sec_compliance))

check_sec() {
  if [ "$2" -eq "$3" ]; then
    ok "$1: $2개"
  else
    fail "$1: 기대=$3, 실제=$2"
  fi
}

check_sec security                       "${sec_meta}"           4
check_sec security-authn                 "${sec_authn}"          13
check_sec security-authz                 "${sec_authz}"          7
check_sec security-crypto-ops            "${sec_crypto}"         11
check_sec security-data-protection       "${sec_data}"           8
check_sec security-api-web               "${sec_api}"            12
check_sec security-supply-chain          "${sec_supply}"         8
check_sec security-platform              "${sec_platform}"       7
check_sec security-sdlc                  "${sec_sdlc}"           6
check_sec security-detect-respond        "${sec_detect}"         6
check_sec security-mobile                "${sec_mobile}"         5
check_sec security-ai-model              "${sec_ai}"             5
check_sec compliance                     "${sec_compliance}"     5

if [ "${sec_total}" -eq 97 ]; then
  ok "base 보안 합계: ${sec_total}개"
else
  fail "base 보안 합계: 기대=97, 실제=${sec_total}"
fi

# ─────────────────────────────────────────────
# CHECK 9: principles reference 무결성 (5번째 도메인)
#   - principles/ index.md + 5 카테고리 md 파일 존재
#     (solid / grasp / iso25010 / 12-factor / code-smells)
#   - 원칙 합계 == 56 (5 + 9 + 8 + 12 + 22)
# ─────────────────────────────────────────────
echo ""
echo "[9] principles reference 무결성 검증 (5번째 도메인)"

PRINCIPLES_DIR="${SKILL_DIR}/references/principles"

if [ -d "${PRINCIPLES_DIR}" ]; then
  ok "디렉토리 존재: references/principles/"
else
  fail "디렉토리 누락: references/principles/"
fi

for f in index.md solid.md grasp.md iso25010.md 12-factor.md code-smells.md database-fundamentals.md sdlc-models.md scaled-agile.md professional-ethics.md standards-mapping.md configuration-management.md hci-methodology.md formal-methods.md; do
  if [ -f "${PRINCIPLES_DIR}/${f}" ]; then
    ok "파일 존재: references/principles/${f}"
  else
    fail "파일 누락: references/principles/${f}"
  fi
done

count_pri() {
  /usr/bin/grep -cE '^## [0-9]+\.' "${PRINCIPLES_DIR}/$1.md" 2>/dev/null || echo 0
}

pri_solid=$(count_pri solid)
pri_grasp=$(count_pri grasp)
pri_iso=$(count_pri iso25010)
pri_12f=$(count_pri 12-factor)
pri_smells=$(count_pri code-smells)
# P0 신설 4
pri_db=$(count_pri database-fundamentals)
pri_sdlc=$(count_pri sdlc-models)
pri_scaled=$(count_pri scaled-agile)
pri_ethics=$(count_pri professional-ethics)
# P1 신설 2
pri_standards=$(count_pri standards-mapping)
pri_config=$(count_pri configuration-management)
# P3 신설 2
pri_hci=$(count_pri hci-methodology)
pri_formal=$(count_pri formal-methods)
pri_total=$((pri_solid + pri_grasp + pri_iso + pri_12f + pri_smells + pri_db + pri_sdlc + pri_scaled + pri_ethics + pri_standards + pri_config + pri_hci + pri_formal))

check_pri() {
  if [ "$2" -eq "$3" ]; then
    ok "$1: $2개"
  else
    fail "$1: 기대=$3, 실제=$2"
  fi
}

check_pri solid                  "${pri_solid}"   5
check_pri grasp                  "${pri_grasp}"   9
check_pri iso25010               "${pri_iso}"     8
check_pri 12-factor              "${pri_12f}"    12
check_pri code-smells            "${pri_smells}" 22
# P0 신설 4 카테고리
check_pri database-fundamentals  "${pri_db}"      8
check_pri sdlc-models            "${pri_sdlc}"    7
check_pri scaled-agile           "${pri_scaled}"  6
check_pri professional-ethics    "${pri_ethics}"  6
# P1 신설 2 카테고리
check_pri standards-mapping        "${pri_standards}"  5
check_pri configuration-management "${pri_config}"     6
# P3 신설 2 카테고리
check_pri hci-methodology          "${pri_hci}"        6
check_pri formal-methods           "${pri_formal}"     5

# 5 base + 4 P0 신설 + 2 P1 신설 + 2 P3 신설 = 56 + 27 + 11 + 11 = 105
if [ "${pri_total}" -eq 105 ]; then
  ok "base+P0+P1+P3 원칙 합계: ${pri_total}개"
else
  fail "base+P0+P1+P3 원칙 합계: 기대=105, 실제=${pri_total}"
fi

# 미시 원칙 부록 검증 (Phase 2 확장: 8 → 18 항목)
# micro-principles.md 헤더 형식: `## <원칙명>` (숫자 없음).
# 본문 18 항목 (기존 8 + Conway/Inverse/Hyrum/Postel/Brooks/Hollywood/Boy Scout/Pareto/Goodhart/Cunningham 10)
# + `## 거시 원칙·스멜 cross-link 매트릭스` + `## 카테고리별 분류` + `## 표준 인용` = 21 헤더.
if [ -f "${PRINCIPLES_DIR}/micro-principles.md" ]; then
  ok "파일 존재 (부록): references/principles/micro-principles.md"
  # anchor 기반 검증 (헤더 카운트는 거시 섹션 변동에 약함)
  micro_anchors=$(/usr/bin/grep -c '<a id=' "${PRINCIPLES_DIR}/micro-principles.md" 2>/dev/null || echo 0)
  if [ "${micro_anchors}" -eq "${EXPECTED_MICRO_PRINCIPLES}" ]; then
    ok "미시 원칙 부록: ${micro_anchors}개 (기존 8 + Conway/Hyrum/Postel/Brooks 등 확장 10)"
  else
    fail "미시 원칙 부록: 기대=${EXPECTED_MICRO_PRINCIPLES}, 실제=${micro_anchors} anchors"
  fi
else
  fail "파일 누락 (부록): references/principles/micro-principles.md"
fi

# ─────────────────────────────────────────────
# CHECK 10: Phase 2 확장 신규 카탈로그 anchor/header 일관성
# ─────────────────────────────────────────────
echo ""
echo "[10] Phase 2 확장 신규 카탈로그 검증"

# 신규 추가된 카탈로그 파일 목록 (patterns/algorithms/principles/security/domains)
PHASE2_FILES=(
  # patterns/ (확장 카테고리 32개)
  "patterns/anti-patterns.md:18"
  "patterns/mobile-app.md:15"
  "patterns/embedded.md:10"
  "patterns/game-dev.md:12"
  "patterns/networking.md:12"
  "patterns/crossplatform.md:10"
  "patterns/offline-first.md:8"
  "patterns/error-handling.md:11"
  "patterns/api-design.md:14"
  "patterns/api-styles.md:9"
  "patterns/web-rendering.md:10"
  "patterns/state-management.md:9"
  "patterns/functional.md:11"
  "patterns/reactive-streams.md:8"
  "patterns/legacy-code.md:10"
  "patterns/workflow-jobs.md:9"
  "patterns/streaming-semantics.md:9"
  "patterns/data-modeling.md:12"
  "patterns/ddd-strategic.md:12"
  "patterns/ui-ux.md:11"
  "patterns/finops.md:8"
  "patterns/testing-strategies.md:10"
  "patterns/build-versioning.md:9"
  "patterns/mlops.md:10"
  "patterns/dx-engineering.md:8"
  "patterns/blockchain.md:10"
  "patterns/requirements-engineering.md:10"
  "patterns/domains/fintech.md:12"
  "patterns/domains/healthcare.md:10"
  "patterns/domains/ecommerce.md:12"
  "patterns/domains/logistics.md:10"
  "patterns/domains/iot-edge.md:10"
  # algorithms/ (확장 카테고리 9개)
  "algorithms/db-indexes.md:8"
  "algorithms/db-storage-engines.md:10"
  "algorithms/spatial.md:8"
  "algorithms/search-systems.md:8"
  "algorithms/load-balancing.md:8"
  "algorithms/os-foundations.md:12"
  "algorithms/image-processing.md:8"
  "algorithms/signal-processing.md:8"
  "algorithms/codecs.md:8"
  # principles/ (확장 카테고리 8개 + micro-principles 확장)
  "principles/type-systems.md:10"
  "principles/concurrency-theory.md:10"
  "principles/refactoring-techniques.md:25"
  "principles/sw-economics.md:10"
  "principles/evolutionary-arch.md:8"
  "principles/resilience-theory.md:8"
  "principles/documentation.md:8"
  "principles/process-metrics.md:10"
  "principles/performance-metrics.md:10"
  "principles/sustainable-sw.md:8"
  # security/ (확장 1개)
  "security/privacy-engineering.md:9"
)

for entry in "${PHASE2_FILES[@]}"; do
  file="${entry%%:*}"
  expected="${entry##*:}"
  path="${SKILL_DIR}/references/${file}"
  if [ ! -f "${path}" ]; then
    fail "${file}: 파일 누락"
    continue
  fi
  anchors=$(grep -c '<a id=' "${path}" 2>/dev/null || echo 0)
  # ^## N. 헤더만 카운트 (sub-section ## 외부 제외)
  headers=$(grep -cE '^## [0-9]+\.' "${path}" 2>/dev/null || echo 0)
  if [ "${anchors}" -ge "${expected}" ] && [ "${headers}" -ge "${expected}" ]; then
    ok "${file}: anchors=${anchors} headers=${headers} (expected≥${expected})"
  else
    fail "${file}: anchors=${anchors} headers=${headers} expected≥${expected}"
  fi
done

# Phase 2 합계
phase2_count=${#PHASE2_FILES[@]}
echo "  → Phase 2 신규 카탈로그 ${phase2_count} 파일 검증 완료"

# micro-principles 부록 확장 검증 (8 → EXPECTED_MICRO_PRINCIPLES)
mp_anchors=$(grep -c '<a id=' "${SKILL_DIR}/references/principles/micro-principles.md" 2>/dev/null || echo 0)
if [ "${mp_anchors}" -ge "${EXPECTED_MICRO_PRINCIPLES}" ]; then
  ok "micro-principles.md: ${mp_anchors} anchors (확장 8→${EXPECTED_MICRO_PRINCIPLES} 반영)"
else
  fail "micro-principles.md: ${mp_anchors} anchors (확장 미반영 — ${EXPECTED_MICRO_PRINCIPLES} 기대)"
fi

# ─────────────────────────────────────────────
# CHECK 10B: quality QA/QC 신규 도메인 검증
# ─────────────────────────────────────────────
echo ""
check_quality_catalog

# ─────────────────────────────────────────────
# CHECK 11: SKILL.md 통합 모드 (qa / qc / full / swarm) 등록 검증
# ─────────────────────────────────────────────
echo ""
echo "[11] 통합 모드 (qa / qc / full / swarm) 등록 검증"

SKILL_FILE="${SKILL_DIR}/SKILL.md"

# 11-1. /dev-advisor full 호출 명령 등록 확인
if grep -q '/dev-advisor full' "${SKILL_FILE}"; then
  ok "/dev-advisor full 명령 등록됨"
else
  fail "/dev-advisor full 명령 미등록"
fi

# 11-2. /dev-advisor swarm 호출 명령 등록 확인
if grep -q '/dev-advisor swarm' "${SKILL_FILE}"; then
  ok "/dev-advisor swarm 명령 등록됨"
else
  fail "/dev-advisor swarm 명령 미등록"
fi

# 11-2B. /dev-advisor qa/qc + /quality 호출 명령 등록 확인
if grep -q '/dev-advisor qa' "${SKILL_FILE}"; then
  ok "/dev-advisor qa 명령 등록됨"
else
  fail "/dev-advisor qa 명령 미등록"
fi

if grep -q '/dev-advisor qc' "${SKILL_FILE}"; then
  ok "/dev-advisor qc 명령 등록됨"
else
  fail "/dev-advisor qc 명령 미등록"
fi

if grep -q '/quality' "${SKILL_FILE}"; then
  ok "/quality lookup 등록됨"
else
  fail "/quality lookup 미등록"
fi

# 11-3. full 모드 자연어 트리거 (최소 2개)
full_triggers=0
for trigger in '전체 점검' '종합 분석' '모두 체크' '6 도메인 분석' 'full audit'; do
  if grep -q "${trigger}" "${SKILL_FILE}"; then
    full_triggers=$((full_triggers + 1))
  fi
done
if [ "${full_triggers}" -ge 2 ]; then
  ok "full 모드 자연어 트리거: ${full_triggers}개 등록"
else
  fail "full 모드 자연어 트리거: ${full_triggers}개 (최소 2개 필요)"
fi

# 11-4. swarm 모드 자연어 트리거 (최소 2개)
swarm_triggers=0
for trigger in '병렬 점검' '심층 분석' 'swarm' 'ultra audit'; do
  if grep -q "${trigger}" "${SKILL_FILE}"; then
    swarm_triggers=$((swarm_triggers + 1))
  fi
done
if [ "${swarm_triggers}" -ge 2 ]; then
  ok "swarm 모드 자연어 트리거: ${swarm_triggers}개 등록"
else
  fail "swarm 모드 자연어 트리거: ${swarm_triggers}개 (최소 2개 필요)"
fi

# 11-4B. qa/qc 자연어 트리거
qa_qc_triggers=0
for trigger in 'QA 점검' '품질 보증' '테스트 전략' 'QC 검증' '품질 게이트' '테스트 실행'; do
  if grep -q "${trigger}" "${SKILL_FILE}"; then
    qa_qc_triggers=$((qa_qc_triggers + 1))
  fi
done
if [ "${qa_qc_triggers}" -ge 4 ]; then
  ok "qa/qc 자연어 트리거: ${qa_qc_triggers}개 등록"
else
  fail "qa/qc 자연어 트리거: ${qa_qc_triggers}개 (최소 4개 필요)"
fi

# 11-5. examples.md 에 예시 G / H 존재 확인
EXAMPLES_FILE="${SKILL_DIR}/references/examples.md"
if grep -qE '^### [GH]\.' "${EXAMPLES_FILE}" 2>/dev/null; then
  ok "examples.md 에 예시 G/H 존재"
else
  fail "examples.md 에 예시 G 또는 H 누락"
fi

# 11-6. output_templates.md 에 full + swarm 템플릿
TEMPLATES_FILE="${SKILL_DIR}/references/output_templates.md"
if grep -q '/dev-advisor full' "${TEMPLATES_FILE}" 2>/dev/null && grep -q '/dev-advisor swarm' "${TEMPLATES_FILE}" 2>/dev/null; then
  ok "output_templates.md 에 full + swarm 템플릿 존재"
else
  fail "output_templates.md 에 full 또는 swarm 템플릿 누락"
fi

check_quality_exposure

# ─────────────────────────────────────────────
# CHECK 12: 전체 Markdown 내부 링크/anchor 검증
# ─────────────────────────────────────────────
echo ""
echo "[12] 전체 Markdown 내부 링크/anchor 검증"

if python3 - "${SKILL_DIR}" <<'PY'
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

root = Path(sys.argv[1])
check_files = sorted(
    set(root.glob("*.md"))
    | set((root / "references").rglob("*.md"))
    | set((root / "scripts").glob("*.md"))
)

def strip_fences(text):
    """검증 대상에서 fenced code block을 제거해 예제 링크 오탐을 막는다."""
    return re.sub(r"```.*?```", "", text, flags=re.S)

def strip_inline_code(text):
    """인라인 코드 안의 괄호/링크 모양 문자열을 검증 대상에서 제외한다."""
    return re.sub(r"`[^`]*`", "", text)

def slugify(heading):
    """GitHub Markdown과 유사한 방식으로 heading anchor 후보를 만든다."""
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[`*_~]", "", heading).strip().lower()
    heading = re.sub(r"[^\w\s\-\u3131-\u318E\uAC00-\uD7A3]", "", heading)
    heading = re.sub(r"\s+", "-", heading)
    heading = re.sub(r"-+", "-", heading)
    return heading.strip("-")

anchor_cache = {}

def anchors_for(path):
    """파일의 명시적 anchor와 heading 기반 anchor를 수집해 캐시한다."""
    path = path.resolve()
    if path in anchor_cache:
        return anchor_cache[path]
    text = path.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a\s+id="([^"]+)"', text))
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            slug = slugify(m.group(2))
            if slug:
                anchors.add(slug)
    anchor_cache[path] = anchors
    return anchors

def anchor_matches(fragment, anchors):
    """짧은 고정 fragment가 한국어 suffix heading anchor와 매칭되는지 확인한다."""
    if fragment in anchors:
        return True
    # Many catalog links intentionally use a stable short prefix for Korean-suffixed headings.
    return any(a.startswith(fragment + "-") for a in anchors)

link_re = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
issues = []

for src in check_files:
    if not src.exists():
        issues.append(f"{src.relative_to(root)}: missing checked file")
        continue
    raw_text = src.read_text(encoding="utf-8")
    text = strip_inline_code(strip_fences(raw_text))
    for match in link_re.finditer(text):
        raw_target = match.group(1).strip()
        line_no = text.count("\n", 0, match.start()) + 1
        target = raw_target.split()[0].strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if "<" in raw_target or ">" in raw_target:
            continue
        if target == "./<lang>.md":
            continue
        path_part, _, fragment = target.partition("#")
        path_part = unquote(path_part)
        fragment = unquote(fragment)
        if path_part and not path_part.endswith(".md"):
            continue
        dest = src if not path_part else (src.parent / path_part).resolve()
        try:
            dest.relative_to(root)
        except ValueError:
            continue
        if not dest.exists():
            issues.append(f"{src.relative_to(root)}:{line_no}: missing file -> {raw_target}")
            continue
        if fragment and not anchor_matches(fragment, anchors_for(dest)):
            issues.append(f"{src.relative_to(root)}:{line_no}: missing anchor -> {raw_target}")

if issues:
    for issue in issues[:50]:
        print("  - " + issue)
    if len(issues) > 50:
        print(f"  ... {len(issues) - 50} more")
    sys.exit(1)
PY
then
  ok "전체 Markdown 링크/anchor 검증 통과"
else
  fail "전체 Markdown 링크/anchor 검증 실패"
fi

# ─────────────────────────────────────────────
# 결과 요약
# ─────────────────────────────────────────────
echo ""
echo "======================================"
if [ "${FAIL}" -eq 0 ]; then
  echo "✓ All integrity checks passed (${EXPECTED_PATTERNS} patterns / ${EXPECTED_ALGORITHMS} algorithms / ${EXPECTED_SECURITY} security / ${EXPECTED_LANGUAGES} languages / ${EXPECTED_PRINCIPLES} principles / ${EXPECTED_QUALITY} quality + ${EXPECTED_MICRO_PRINCIPLES} 부록 — 6 domains, ${EXPECTED_TOTAL} items + ${EXPECTED_MICRO_PRINCIPLES} 부록 = ${EXPECTED_TOTAL_WITH_MICRO} total)"
  exit 0
else
  echo "✗ ${FAIL}개 검사 실패, ${PASS}개 통과"
  exit 1
fi
