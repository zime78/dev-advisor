#!/usr/bin/env bash
# verify-anchors.sh — anchor 무결성·파일 존재·카테고리 카운트·markdown 링크 검증
#
# 검증:
#   [1]  카테고리별 anchor 수 == 기대값 (algorithms 22 카테고리)
#   [2]  전역 anchor unique
#   [5]  languages 디렉토리·메타·파일 수
#   [6]  languages 표준 14 섹션 헤더 spot-check (5개 대표 언어)
#   [6B] languages 전체 품질 게이트 (관련 문서/링크/예제)
#   [7]  patterns 파일 존재 + 카테고리 카운트
#   [8]  security 파일 존재 + 카테고리 카운트
#   [9]  principles 파일 존재 + 카테고리 카운트 + micro-principles 부록
#   [10] Phase 2 확장 신규 카탈로그 anchor/header 일관성
#   [12] 전체 Markdown 내부 링크/anchor 검증
#
# Args:
#   --check anchors | all
#   --help

set -euo pipefail

VERIFY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/_common.sh
source "${VERIFY_DIR}/lib/_common.sh"
# shellcheck source=lib/count_domain.sh
source "${VERIFY_DIR}/lib/count_domain.sh"

print_help() {
  cat <<EOF
Usage: $(basename "$0") [--check anchors|all] [--help]

Verifies per-category anchor counts, file presence, markdown link resolution,
and Phase 2 catalog consistency. Run as a verify-all.sh sub-stage or standalone.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check) shift 2 || { echo "FATAL: --check requires value" >&2; exit 1; } ;;
    --help|-h) print_help; exit 0 ;;
    *) echo "FATAL: unknown argument: $1" >&2; exit 1 ;;
  esac
done

preflight_tmp

ALGO_DIR="${SKILL_DIR}/references/algorithms"
LANG_DIR="${SKILL_DIR}/references/languages"
PATTERNS_DIR="${SKILL_DIR}/references/patterns"
SECURITY_DIR="${SKILL_DIR}/references/security"
PRINCIPLES_DIR="${SKILL_DIR}/references/principles"

# ─────────────────────────────────────────────
# [1] 카테고리별 anchor 수 == 기대 카운트
# ─────────────────────────────────────────────
check_algorithm_anchors() {
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
      *)                    echo 0  ;;
    esac
  }

  local cat file expected actual
  for cat in sorting searching graph dynamic-programming divide-conquer greedy backtracking string math data-structures geometry flow matching crypto compression game-ai ml probabilistic consensus distributed concurrent parsing; do
    file="${ALGO_DIR}/${cat}.md"
    expected=$(expected_count "${cat}")
    actual=$(grep -c '<a id=' "${file}" 2>/dev/null || echo 0)
    if [ "${actual}" -eq "${expected}" ]; then
      ok "${cat}: ${actual}개"
    else
      fail "${cat}: 기대=${expected}, 실제=${actual}"
    fi
  done
}

# ─────────────────────────────────────────────
# [2] 전역 anchor unique 검증 (algorithms 디렉토리 한정)
# ─────────────────────────────────────────────
check_algorithm_unique() {
  echo ""
  echo "[2] 전역 anchor unique 검증"

  local dupes
  dupes=$(grep -h '<a id=' "${ALGO_DIR}"/*.md \
    | grep -o 'id="[^"]*"' \
    | sort \
    | uniq -d)

  if [ -z "${dupes}" ]; then
    ok "중복 anchor 없음"
  else
    fail "중복 anchor 발견: ${dupes}"
  fi
}

# ─────────────────────────────────────────────
# [5] languages reference 무결성
# ─────────────────────────────────────────────
check_languages_structure() {
  echo ""
  echo "[5] 프로그래밍 언어 reference 무결성 검증"

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

  local lang_files
  lang_files=$(/bin/ls "${LANG_DIR}"/*.md 2>/dev/null | /usr/bin/grep -vE '/(index|domains)\.md$' | wc -l | tr -d ' ')
  if [ "${lang_files}" -ge 60 ]; then
    ok "언어 파일 수: ${lang_files}개 (>=60)"
  else
    fail "언어 파일 수: 기대>=60, 실제=${lang_files}"
  fi

  local legacy_residue
  legacy_residue=$(/usr/bin/grep -rli 'Codex 스킬용\|로컬 Codex 스킬' "${LANG_DIR}" 2>/dev/null | wc -l | tr -d ' ' || true)
  legacy_residue=${legacy_residue:-0}
  if [ "${legacy_residue}" -eq 0 ]; then
    ok "레거시 잔존 표현: 0건"
  else
    fail "레거시 잔존 표현: ${legacy_residue}건"
  fi

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
}

# ─────────────────────────────────────────────
# [6] languages 표준 14 섹션 헤더 spot-check
# ─────────────────────────────────────────────
check_languages_headers() {
  echo ""
  echo "[6] languages 표준 14 섹션 헤더 spot-check"

  local STD_HEADERS='## 핵심 판단
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

  local lang lf _hdr_cnt_file expected_hdrs missing cur hdr
  for lang in python kotlin rust go swift; do
    lf="${LANG_DIR}/${lang}.md"
    if [ ! -f "${lf}" ]; then
      fail "${lang}.md 누락"
      continue
    fi
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
    if [ "${expected_hdrs}" -ne 14 ]; then
      fail "${lang}.md: STD_HEADERS 전달 손상 (기대=14, 실제 입력=${expected_hdrs})"
      continue
    fi
    if [ "${missing}" -lt 2 ]; then
      ok "${lang}.md: 누락 헤더 ${missing}개 (<2)"
    else
      fail "${lang}.md: 누락 헤더 ${missing}개 (>=2)"
    fi
  done
}

# ─────────────────────────────────────────────
# [6B] languages 전체 품질 게이트
# ─────────────────────────────────────────────
check_languages_quality() {
  echo ""
  echo "[6B] languages 전체 품질 게이트"

  if EXPECTED_LANGUAGES="${EXPECTED_LANGUAGES}" python3 "${VERIFY_DIR}/lib/check_languages_quality.py" "${LANG_DIR}"; then
    ok "languages 관련 문서/링크/예제 품질 기준 통과"
  else
    fail "languages 품질 기준 실패"
  fi
}

# ─────────────────────────────────────────────
# [7] patterns reference 무결성
# ─────────────────────────────────────────────
check_patterns() {
  echo ""
  echo "[7] patterns reference 무결성 검증"

  local f
  for f in index.md creational.md structural.md behavioral.md architectural.md distributed.md reliability.md concurrency.md integration.md ddd-tactical.md data-access.md testing.md observability.md ai-llm.md deployment.md caching.md web-performance.md graphics-rendering.md ar-vr-xr.md serverless-faas.md hpc-scientific.md; do
    if [ -f "${PATTERNS_DIR}/${f}" ]; then
      ok "파일 존재: references/patterns/${f}"
    else
      fail "파일 누락: references/patterns/${f}"
    fi
  done

  # 카테고리별 카운트 (count_domain.sh check_domain 사용)
  check_domain patterns creational                5
  check_domain patterns structural                7
  check_domain patterns behavioral               11
  check_domain patterns architectural            17
  check_domain patterns distributed              11
  check_domain patterns reliability               9
  check_domain patterns concurrency              14
  check_domain patterns integration              17
  check_domain patterns ddd-tactical             11
  check_domain patterns data-access              10
  check_domain patterns testing                  11
  check_domain patterns observability            10
  check_domain patterns ai-llm                   12
  check_domain patterns deployment                9
  check_domain patterns caching                   9
  check_domain patterns web-performance           6
  check_domain patterns graphics-rendering        5
  check_domain patterns ar-vr-xr                  5
  check_domain patterns serverless-faas           5
  check_domain patterns hpc-scientific            6

  local pat_total
  pat_total=$(domain_total patterns "creational structural behavioral architectural distributed reliability concurrency integration ddd-tactical data-access testing observability ai-llm deployment caching web-performance graphics-rendering ar-vr-xr serverless-faas hpc-scientific")
  if [ "${pat_total}" -eq 190 ]; then
    ok "base+P1+P2+P3 패턴 합계: ${pat_total}개"
  else
    fail "base+P1+P2+P3 패턴 합계: 기대=190, 실제=${pat_total}"
  fi
}

# ─────────────────────────────────────────────
# [8] security reference 무결성
# ─────────────────────────────────────────────
check_security() {
  echo ""
  echo "[8] security reference 무결성 검증 (별도 도메인)"

  if [ -d "${SECURITY_DIR}" ]; then
    ok "디렉토리 존재: references/security/"
  else
    fail "디렉토리 누락: references/security/"
  fi

  local f
  for f in index.md security.md security-authn.md security-authz.md security-crypto-ops.md security-data-protection.md security-api-web.md security-supply-chain.md security-platform.md security-sdlc.md security-detect-respond.md security-mobile.md security-ai-model.md compliance.md; do
    if [ -f "${SECURITY_DIR}/${f}" ]; then
      ok "파일 존재: references/security/${f}"
    else
      fail "파일 누락: references/security/${f}"
    fi
  done

  check_domain security security                       4
  check_domain security security-authn                13
  check_domain security security-authz                 7
  check_domain security security-crypto-ops           11
  check_domain security security-data-protection       8
  check_domain security security-api-web              12
  check_domain security security-supply-chain          8
  check_domain security security-platform              7
  check_domain security security-sdlc                  6
  check_domain security security-detect-respond        6
  check_domain security security-mobile                5
  check_domain security security-ai-model              5
  check_domain security compliance                     5

  local sec_total
  sec_total=$(domain_total security "security security-authn security-authz security-crypto-ops security-data-protection security-api-web security-supply-chain security-platform security-sdlc security-detect-respond security-mobile security-ai-model compliance")
  if [ "${sec_total}" -eq 97 ]; then
    ok "base 보안 합계: ${sec_total}개"
  else
    fail "base 보안 합계: 기대=97, 실제=${sec_total}"
  fi
}

# ─────────────────────────────────────────────
# [9] principles reference 무결성
# ─────────────────────────────────────────────
check_principles() {
  echo ""
  echo "[9] principles reference 무결성 검증 (5번째 도메인)"

  if [ -d "${PRINCIPLES_DIR}" ]; then
    ok "디렉토리 존재: references/principles/"
  else
    fail "디렉토리 누락: references/principles/"
  fi

  local f
  for f in index.md solid.md grasp.md iso25010.md 12-factor.md code-smells.md sdlc-models.md scaled-agile.md professional-ethics.md standards-mapping.md configuration-management.md hci-methodology.md formal-methods.md; do
    if [ -f "${PRINCIPLES_DIR}/${f}" ]; then
      ok "파일 존재: references/principles/${f}"
    else
      fail "파일 누락: references/principles/${f}"
    fi
  done

  check_domain principles solid                       5
  check_domain principles grasp                       9
  check_domain principles iso25010                    8
  check_domain principles 12-factor                  12
  check_domain principles code-smells                22
  check_domain principles sdlc-models                 7
  check_domain principles scaled-agile                6
  check_domain principles professional-ethics         6
  check_domain principles standards-mapping           7
  check_domain principles configuration-management    6
  check_domain principles hci-methodology             6
  check_domain principles formal-methods              5

  local pri_total
  pri_total=$(domain_total principles "solid grasp iso25010 12-factor code-smells sdlc-models scaled-agile professional-ethics standards-mapping configuration-management hci-methodology formal-methods")
  if [ "${pri_total}" -eq 99 ]; then
    ok "base+P1+P3 원칙 합계: ${pri_total}개"
  else
    fail "base+P1+P3 원칙 합계: 기대=99, 실제=${pri_total}"
  fi

  # micro-principles 부록
  local mp="${PRINCIPLES_DIR}/micro-principles.md"
  if [ -f "${mp}" ]; then
    ok "파일 존재 (부록): references/principles/micro-principles.md"
    local micro_anchors
    micro_anchors=$(/usr/bin/grep -c '<a id=' "${mp}" 2>/dev/null || echo 0)
    if [ "${micro_anchors}" -eq "${EXPECTED_MICRO_PRINCIPLES}" ]; then
      ok "미시 원칙 부록: ${micro_anchors}개"
    else
      fail "미시 원칙 부록: 기대=${EXPECTED_MICRO_PRINCIPLES}, 실제=${micro_anchors} anchors"
    fi
  else
    fail "파일 누락 (부록): references/principles/micro-principles.md"
  fi
}

# ─────────────────────────────────────────────
# [10] Phase 2 확장 신규 카탈로그 anchor/header 일관성
# ─────────────────────────────────────────────
check_phase2() {
  echo ""
  echo "[10] Phase 2 확장 신규 카탈로그 검증"

  local PHASE2_FILES=(
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
    "algorithms/spatial.md:8"
    "algorithms/search-systems.md:8"
    "algorithms/load-balancing.md:8"
    "algorithms/os-foundations.md:12"
    "algorithms/image-processing.md:8"
    "algorithms/signal-processing.md:8"
    "algorithms/codecs.md:8"
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
    "security/privacy-engineering.md:9"
  )

  local entry file expected path anchors headers
  for entry in "${PHASE2_FILES[@]}"; do
    file="${entry%%:*}"
    expected="${entry##*:}"
    path="${SKILL_DIR}/references/${file}"
    if [ ! -f "${path}" ]; then
      fail "${file}: 파일 누락"
      continue
    fi
    anchors=$(grep -c '<a id=' "${path}" 2>/dev/null || echo 0)
    headers=$(grep -cE '^## [0-9]+\.' "${path}" 2>/dev/null || echo 0)
    if [ "${anchors}" -ge "${expected}" ] && [ "${headers}" -ge "${expected}" ]; then
      ok "${file}: anchors=${anchors} headers=${headers} (expected≥${expected})"
    else
      fail "${file}: anchors=${anchors} headers=${headers} expected≥${expected}"
    fi
  done

  echo "  → Phase 2 신규 카탈로그 ${#PHASE2_FILES[@]} 파일 검증 완료"

  local mp_anchors
  mp_anchors=$(grep -c '<a id=' "${SKILL_DIR}/references/principles/micro-principles.md" 2>/dev/null || echo 0)
  if [ "${mp_anchors}" -ge "${EXPECTED_MICRO_PRINCIPLES}" ]; then
    ok "micro-principles.md: ${mp_anchors} anchors (확장 8→${EXPECTED_MICRO_PRINCIPLES} 반영)"
  else
    fail "micro-principles.md: ${mp_anchors} anchors (확장 미반영 — ${EXPECTED_MICRO_PRINCIPLES} 기대)"
  fi
}

# ─────────────────────────────────────────────
# [12] 전체 Markdown 내부 링크/anchor 검증
# ─────────────────────────────────────────────
check_markdown_links() {
  echo ""
  echo "[12] 전체 Markdown 내부 링크/anchor 검증"

  if python3 "${VERIFY_DIR}/lib/check_anchor_resolution.py" "${SKILL_DIR}"; then
    ok "전체 Markdown 링크/anchor 검증 통과"
  else
    fail "전체 Markdown 링크/anchor 검증 실패"
  fi
}

echo "=== verify-anchors ==="
echo ""
check_algorithm_anchors
check_algorithm_unique
check_languages_structure
check_languages_headers
check_languages_quality
check_patterns
check_security
check_principles
check_phase2
check_markdown_links

if [ "${VERIFY_ALL_RUNNING:-0}" != "1" ]; then
  finish
fi
