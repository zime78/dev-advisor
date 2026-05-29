#!/usr/bin/env bash
# verify-modes.sh — SKILL.md / _routing.md / _help.md / workflows/* 모드 등록 검증
#
# P2-a Progressive Disclosure 이후: 자연어 트리거가 SKILL.md 에서
# references/workflows/_routing.md 와 references/_help.md 로 이동했다.
# 본 sub-check 는 세 파일을 합쳐 검색하여 트리거 누락을 정확히 검출한다.
#
# 검증:
#   [11-1~6]  /dev-advisor full/swarm/qa/qc + /quality 명령 등록
#   [11-3]    full 모드 자연어 트리거 ≥ 2개
#   [11-4]    swarm 모드 자연어 트리거 ≥ 2개
#   [11-4B]   qa/qc 자연어 트리거 ≥ 4개
#   [11-5]    examples.md 예시 G/H
#   [11-6]    output_templates.md full/swarm 템플릿
#
# Args:
#   --check modes | all
#   --help

set -euo pipefail

VERIFY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/_common.sh
source "${VERIFY_DIR}/lib/_common.sh"

print_help() {
  cat <<EOF
Usage: $(basename "$0") [--check modes|all] [--help]

Verifies advisor mode registration in SKILL.md, _routing.md, _help.md and the
example/template surface. Adapts to Progressive Disclosure (P2-a).
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

SKILL_FILE="${SKILL_DIR}/SKILL.md"
ROUTING_FILE="${SKILL_DIR}/references/workflows/_routing.md"
HELP_FILE="${SKILL_DIR}/references/_help.md"
EXAMPLES_FILE="${SKILL_DIR}/references/examples.md"
TEMPLATES_FILE="${SKILL_DIR}/references/output_templates.md"

# Trigger discovery: SKILL.md + _routing.md + _help.md (Progressive Disclosure scope)
TRIGGER_SEARCH_FILES=("${SKILL_FILE}" "${ROUTING_FILE}" "${HELP_FILE}")

# 키워드를 trigger 후보 파일 묶음에서 찾는다. 어느 한 파일이라도 매칭되면 found.
trigger_in_scope() {
  local needle="$1"
  local f
  for f in "${TRIGGER_SEARCH_FILES[@]}"; do
    [ -f "${f}" ] || continue
    if grep -qF "${needle}" "${f}"; then
      return 0
    fi
  done
  return 1
}

check_command_registration() {
  echo "[11] 통합 모드 (qa / qc / full / swarm) 등록 검증"

  if grep -q '/dev-advisor full' "${SKILL_FILE}"; then
    ok "/dev-advisor full 명령 등록됨"
  else
    fail "/dev-advisor full 명령 미등록"
  fi

  if grep -q '/dev-advisor swarm' "${SKILL_FILE}"; then
    ok "/dev-advisor swarm 명령 등록됨"
  else
    fail "/dev-advisor swarm 명령 미등록"
  fi

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
}

check_full_triggers() {
  # full 모드 자연어 트리거 (최소 2개) — SKILL.md + _routing.md + _help.md 통합 검색
  local count=0 trigger
  for trigger in '전체 점검' '종합 분석' '모두 체크' '6 도메인 분석' 'full audit'; do
    if trigger_in_scope "${trigger}"; then
      count=$((count + 1))
    fi
  done
  if [ "${count}" -ge 2 ]; then
    ok "full 모드 자연어 트리거: ${count}개 등록"
  else
    fail "full 모드 자연어 트리거: ${count}개 (최소 2개 필요)"
  fi
}

check_swarm_triggers() {
  local count=0 trigger
  for trigger in '병렬 점검' '심층 분석' 'swarm' 'ultra audit'; do
    if trigger_in_scope "${trigger}"; then
      count=$((count + 1))
    fi
  done
  if [ "${count}" -ge 2 ]; then
    ok "swarm 모드 자연어 트리거: ${count}개 등록"
  else
    fail "swarm 모드 자연어 트리거: ${count}개 (최소 2개 필요)"
  fi
}

check_qa_qc_triggers() {
  local count=0 trigger
  for trigger in 'QA 점검' '품질 보증' '테스트 전략' 'QC 검증' '품질 게이트' '테스트 실행'; do
    if trigger_in_scope "${trigger}"; then
      count=$((count + 1))
    fi
  done
  if [ "${count}" -ge 4 ]; then
    ok "qa/qc 자연어 트리거: ${count}개 등록"
  else
    fail "qa/qc 자연어 트리거: ${count}개 (최소 4개 필요)"
  fi
}

check_examples_templates() {
  if grep -qE '^### [GH]\.' "${EXAMPLES_FILE}" 2>/dev/null; then
    ok "examples.md 에 예시 G/H 존재"
  else
    fail "examples.md 에 예시 G 또는 H 누락"
  fi

  if grep -q '/dev-advisor full' "${TEMPLATES_FILE}" 2>/dev/null && grep -q '/dev-advisor swarm' "${TEMPLATES_FILE}" 2>/dev/null; then
    ok "output_templates.md 에 full + swarm 템플릿 존재"
  else
    fail "output_templates.md 에 full 또는 swarm 템플릿 누락"
  fi
}

# 라우팅 문서 자체의 존재 확인 (Progressive Disclosure 인프라가 유지되는지)
check_routing_files() {
  echo ""
  echo "[11-D] Progressive Disclosure 라우팅 파일 존재"
  local f label
  for entry in \
    "${ROUTING_FILE}|references/workflows/_routing.md" \
    "${HELP_FILE}|references/_help.md" \
    "${SKILL_DIR}/references/workflows/index.md|references/workflows/index.md" \
    "${SKILL_DIR}/references/workflows/_severity.md|references/workflows/_severity.md"; do
    f="${entry%%|*}"
    label="${entry##*|}"
    if [ -f "${f}" ]; then
      ok "라우팅 파일 존재: ${label}"
    else
      fail "라우팅 파일 누락: ${label}"
    fi
  done
}

# 10 모드 워크플로우 파일 존재 검증
check_workflow_files() {
  echo ""
  echo "[11-W] 10 advisor 모드 워크플로우 파일 존재"
  local f m
  for m in recommend validate refactor maintain security-audit qa qc research full swarm; do
    f="${SKILL_DIR}/references/workflows/${m}.md"
    if [ -f "${f}" ]; then
      ok "워크플로우 존재: ${m}.md"
    else
      fail "워크플로우 누락: ${m}.md"
    fi
  done
}

echo "=== verify-modes ==="
echo ""
check_command_registration
check_full_triggers
check_swarm_triggers
check_qa_qc_triggers
check_examples_templates
check_routing_files
check_workflow_files

if [ "${VERIFY_ALL_RUNNING:-0}" != "1" ]; then
  finish
fi
