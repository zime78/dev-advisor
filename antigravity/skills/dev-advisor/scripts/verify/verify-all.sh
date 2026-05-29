#!/usr/bin/env bash
# verify-all.sh — dev-advisor 5 단계 무결성 검증 오케스트레이터
#
# 5 sub-stage 를 직렬 실행하여 누적 결과를 요약한다.
#   [1/5] verify-counts.sh    카탈로그 카운트 / manifest / sync 마커 SoT
#   [2/5] verify-anchors.sh   per-category anchor / file 존재 / markdown 링크
#   [3/5] verify-modes.sh     advisor 모드 등록 + Progressive Disclosure 트리거
#   [4/5] verify-semantic.sh  quality 카탈로그 + semantic index / standards mapping
#   [5/5] verify-research.sh  research 모드 등록·문서·픽스처
#
# CLI:
#   verify-all.sh                           # 모두 실행
#   verify-all.sh --check counts            # 단일 sub-check
#   verify-all.sh --check anchors|modes|semantic|research
#   verify-all.sh --check all
#   verify-all.sh --check today             # → verify-semantic.sh --check today
#   verify-all.sh --check quality           # → verify-semantic.sh --check quality
#
# 종료 코드: sub 중 1개라도 실패하면 1, 모두 통과하면 0.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# .counts.manifest 를 한 번 읽어 최종 요약 메시지에서 사용
MANIFEST_SKILL="${SKILL_DIR}/.counts.manifest"
if [ -f "${MANIFEST_SKILL}" ]; then
  # shellcheck disable=SC1090
  source "${MANIFEST_SKILL}"
fi

CHECK_SCOPE="all"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --check)
      if [ "$#" -lt 2 ]; then
        echo "FATAL: --check requires one of: all, counts, anchors, modes, semantic, research, today, quality" >&2
        exit 1
      fi
      CHECK_SCOPE="$2"
      shift 2
      ;;
    --help|-h)
      cat <<EOF
Usage: $(basename "$0") [--check all|counts|anchors|modes|semantic|research|today|quality]

5-stage orchestrator: counts → anchors → modes → semantic → research.
Backward-compat: 'today' and 'quality' map to verify-semantic.sh sub-scope.
EOF
      exit 0
      ;;
    *)
      echo "FATAL: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

case "${CHECK_SCOPE}" in
  all|counts|anchors|modes|semantic|research|today|quality) ;;
  *)
    echo "FATAL: invalid --check value: ${CHECK_SCOPE}" >&2
    exit 1
    ;;
esac

# sub-script 들이 finish() 를 건너뛰도록 시그널
export VERIFY_ALL_RUNNING=1

TOTAL_FAIL=0
TOTAL_PASS=0
# bash 3.2 호환: 빈 배열 + set -u 조합 시 unbound variable. 미리 한 원소 초기화 후 첫 add 시 제거.
RESULTS=("__init__")

# run_stage <stage_num> <total> <label> <script> [args...]
# sub-script 의 stdout 을 그대로 출력하고 마지막 ok/fail 카운트를 누적한다.
run_stage() {
  local n="$1" total="$2" label="$3" script="$4"
  shift 4
  local tmp_out
  tmp_out="$(mktemp)"
  local exit_code=0

  # sub-script 실행 — set -e 비활성 (exit 코드 분석 필요)
  set +e
  bash "${script}" "$@" > "${tmp_out}" 2>&1
  exit_code=$?
  set -e

  cat "${tmp_out}"

  # 카운트 집계: ✓ / ✗ 라인 수
  # grep -c 가 매칭 0 일 때 exit 1 → || echo 0 의 echo 가 추가로 "0" 을 붙여
  # "0\n0" 이 되어 산술 평가 실패. awk 로 항상 단일 정수 보장.
  local pass fail
  pass=$(awk '/^  ✓ /{c++} END{print c+0}' "${tmp_out}")
  fail=$(awk '/^  ✗ /{c++} END{print c+0}' "${tmp_out}")
  TOTAL_PASS=$((TOTAL_PASS + pass))
  TOTAL_FAIL=$((TOTAL_FAIL + fail))

  rm -f "${tmp_out}"

  local status="OK"
  if [ "${fail}" -gt 0 ] || [ "${exit_code}" -ne 0 ]; then
    status="FAIL"
  fi
  RESULTS+=("[${n}/${total}] ${label} ${status} (${pass} pass, ${fail} fail)")
}

case "${CHECK_SCOPE}" in
  counts)
    run_stage 1 1 "verify-counts.sh   " "${SCRIPT_DIR}/verify-counts.sh"
    ;;
  anchors)
    run_stage 1 1 "verify-anchors.sh  " "${SCRIPT_DIR}/verify-anchors.sh"
    ;;
  modes)
    run_stage 1 1 "verify-modes.sh    " "${SCRIPT_DIR}/verify-modes.sh"
    ;;
  semantic)
    run_stage 1 1 "verify-semantic.sh " "${SCRIPT_DIR}/verify-semantic.sh" --check semantic
    ;;
  today)
    run_stage 1 1 "verify-semantic.sh " "${SCRIPT_DIR}/verify-semantic.sh" --check today
    ;;
  quality)
    run_stage 1 1 "verify-semantic.sh " "${SCRIPT_DIR}/verify-semantic.sh" --check quality
    ;;
  research)
    run_stage 1 1 "verify-research.sh " "${SCRIPT_DIR}/verify-research.sh"
    ;;
  all)
    run_stage 1 5 "verify-counts.sh   " "${SCRIPT_DIR}/verify-counts.sh"
    echo ""
    run_stage 2 5 "verify-anchors.sh  " "${SCRIPT_DIR}/verify-anchors.sh"
    echo ""
    run_stage 3 5 "verify-modes.sh    " "${SCRIPT_DIR}/verify-modes.sh"
    echo ""
    run_stage 4 5 "verify-semantic.sh " "${SCRIPT_DIR}/verify-semantic.sh"
    echo ""
    run_stage 5 5 "verify-research.sh " "${SCRIPT_DIR}/verify-research.sh"
    ;;
esac

echo ""
echo "======================================"
echo "Stage summary:"
for line in "${RESULTS[@]}"; do
  [ "${line}" = "__init__" ] && continue
  echo "  ${line}"
done
echo "--------------------------------------"

if [ "${TOTAL_FAIL}" -eq 0 ]; then
  if [ -n "${EXPECTED_PATTERNS:-}" ]; then
    echo "✓ All integrity checks passed (${EXPECTED_PATTERNS}/${EXPECTED_ALGORITHMS}/${EXPECTED_LANGUAGES}/${EXPECTED_SECURITY}/${EXPECTED_PRINCIPLES}/${EXPECTED_QUALITY} + ${EXPECTED_MICRO_PRINCIPLES} — 6 domains, ${EXPECTED_TOTAL} items + ${EXPECTED_MICRO_PRINCIPLES} 부록 = ${EXPECTED_TOTAL_WITH_MICRO} total)"
  else
    echo "✓ All integrity checks passed (${TOTAL_PASS} pass)"
  fi
  exit 0
else
  echo "✗ ${TOTAL_FAIL}개 검사 실패, ${TOTAL_PASS}개 통과"
  exit 1
fi
