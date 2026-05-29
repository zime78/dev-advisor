#!/usr/bin/env bash
# _common.sh — 공통 함수·환경 부트스트랩 (verify-*.sh 가 source 한다)
#
# 제공:
#   - SKILL_DIR / SCRIPT_DIR / VERIFY_DIR / REPO_ROOT / REPO_MODE 환경변수
#   - .counts.manifest source (EXPECTED_* 정수)
#   - PASS/FAIL 카운터 + ok()/fail() 출력
#   - count_numbered_headers / count_index_rows 헬퍼
#   - finish() / preflight() 공통 게이트
#
# bash 3.2 (macOS 시스템 bash) 호환 — `declare -A` 미사용.

# Idempotent guard — verify-all.sh 가 sub-script 를 호출할 때 중복 source 방지
if [ "${_DEV_ADVISOR_COMMON_LOADED:-0}" = "1" ]; then
  return 0 2>/dev/null || exit 0
fi
_DEV_ADVISOR_COMMON_LOADED=1

set -euo pipefail

# verify/<script>.sh 에서 source 한 경우: BASH_SOURCE[1] 이 verify/<script>.sh
# 직접 source 하면 BASH_SOURCE[0] 이 lib/_common.sh
_COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_DIR="$(cd "${_COMMON_DIR}/.." && pwd)"
SCRIPT_DIR="$(cd "${VERIFY_DIR}/.." && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# repo 모드 (codex/claude 양쪽 sync 검증용) — standalone 설치본은 0
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../" 2>/dev/null && pwd || echo "${SKILL_DIR}")"
REPO_MODE=0
if [ -f "${REPO_ROOT}/README.md" ] && [ -d "${REPO_ROOT}/codex/skills/dev-advisor" ] && [ -d "${REPO_ROOT}/claude/skills/dev-advisor" ]; then
  REPO_MODE=1
fi

# Shared counts manifest — silent divergence 차단.
MANIFEST_REPO="${REPO_ROOT}/.counts.manifest"
MANIFEST_SKILL="${SKILL_DIR}/.counts.manifest"
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

# 카운터는 sub-script 가 직접 set 한다 — verify-all.sh 가 sub-script 출력에서 집계
PASS=${PASS:-0}
FAIL=${FAIL:-0}

# 개별 검증 성공 메시지를 출력하고 통과 카운터를 증가시킨다.
ok() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
# 개별 검증 실패 메시지를 출력하고 실패 카운터를 증가시킨다.
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }

# ## N. 형식 헤더 카운트 (markdown 카탈로그 항목 수)
count_numbered_headers() {
  /usr/bin/grep -cE '^## [0-9]+\.' "$1" 2>/dev/null || echo 0
}

# 특정 섹션 헤더 이후 link table 행 카운트
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

# Pre-flight: TMPDIR/temp-file writability check.
# 사유: here-doc 및 process substitution 이 임시파일을 생성한다.
# sandbox / read-only 환경에서 임시파일 생성이 막히면 본문 검사가 silent
# skip 되어 false PASS 가 발생하므로 시작 시점에 명시 FAIL 처리한다.
preflight_tmp() {
  local _tmp_probe
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
}

# Standalone sub-script 종료 처리. verify-all.sh 에서는 호출하지 않는다.
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
