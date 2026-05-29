#!/usr/bin/env bash
# verify-semantic.sh — quality 카탈로그 + semantic index/standards mapping 검증
#
# 검증:
#   [Q]   quality QA/QC 카탈로그 (디렉토리/파일/anchor/index 매핑)
#   [Q2]  QA/QC 호출 노출 (SKILL.md/examples/output_templates/README)
#   [T]   오늘 확장 P0/P1/P2/P3 카탈로그 (anchor/header ≥ 기대값)
#   [S]   semantic index / standards mapping (lib/check_semantic_catalog.py)
#
# Args:
#   --check semantic | quality | today | all
#   --help

set -euo pipefail

VERIFY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/_common.sh
source "${VERIFY_DIR}/lib/_common.sh"

print_help() {
  cat <<EOF
Usage: $(basename "$0") [--check semantic|quality|today|all] [--help]

Verifies quality catalog presence/exposure, today's expansion catalog, and
semantic index / standards mapping resolution (via check_semantic_catalog.py).
EOF
}

SUB_SCOPE="all"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --check)
      if [ "$#" -lt 2 ]; then
        echo "FATAL: --check requires value" >&2; exit 1
      fi
      SUB_SCOPE="$2"
      shift 2
      ;;
    --help|-h) print_help; exit 0 ;;
    *) echo "FATAL: unknown argument: $1" >&2; exit 1 ;;
  esac
done

preflight_tmp

QUALITY_DIR="${SKILL_DIR}/references/quality"
SKILL_FILE="${SKILL_DIR}/SKILL.md"
EXAMPLES_FILE="${SKILL_DIR}/references/examples.md"
TEMPLATES_FILE="${SKILL_DIR}/references/output_templates.md"
ROOT_README="${REPO_ROOT}/README.md"

# ─────────────────────────────────────────────
# [Q] quality QA/QC 카탈로그 검증
# ─────────────────────────────────────────────
check_quality_catalog() {
  echo "[Q] quality QA/QC 카탈로그 검증"

  if [ -d "${QUALITY_DIR}" ]; then
    ok "디렉토리 존재: references/quality/"
  else
    fail "디렉토리 누락: references/quality/"
  fi

  local f
  for f in index.md qa.md qc.md; do
    if [ -f "${QUALITY_DIR}/${f}" ]; then
      ok "파일 존재: references/quality/${f}"
    else
      fail "파일 누락: references/quality/${f}"
    fi
  done

  local entry file expected path anchors headers
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

  local quality_index_count
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

# ─────────────────────────────────────────────
# [Q2] QA/QC 호출 노출 검증
# ─────────────────────────────────────────────
check_quality_exposure() {
  echo ""
  echo "[Q2] QA/QC 호출 노출 검증"

  local token
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

# ─────────────────────────────────────────────
# [T] 오늘 확장 P0/P1/P2/P3 카탈로그
# ─────────────────────────────────────────────
check_today_catalog() {
  echo ""
  echo "[T] 오늘 확장 P0/P1/P2/P3 카탈로그 검증"
  local TODAY_FILES=(
    "patterns/web-performance.md:6"
    "patterns/graphics-rendering.md:5"
    "patterns/ar-vr-xr.md:5"
    "patterns/serverless-faas.md:5"
    "patterns/hpc-scientific.md:6"
    "patterns/mobile-app.md:15"
    "principles/sdlc-models.md:7"
    "principles/scaled-agile.md:6"
    "principles/professional-ethics.md:6"
    "principles/standards-mapping.md:7"
    "principles/configuration-management.md:6"
    "principles/hci-methodology.md:6"
    "principles/formal-methods.md:5"
  )

  local entry file expected path anchors headers
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

# ─────────────────────────────────────────────
# [S] semantic index / standards mapping
# ─────────────────────────────────────────────
check_semantic_catalog() {
  echo ""
  echo "[S] semantic index / standards mapping 검증"

  if python3 "${VERIFY_DIR}/lib/check_semantic_catalog.py" "${SKILL_DIR}"; then
    ok "semantic index / standards mapping 검증 통과"
  else
    fail "semantic index / standards mapping 검증 실패"
  fi
}

echo "=== verify-semantic ==="
echo ""

case "${SUB_SCOPE}" in
  quality)
    check_quality_catalog
    check_quality_exposure
    ;;
  today)
    check_today_catalog
    check_quality_catalog
    check_quality_exposure
    ;;
  semantic)
    check_semantic_catalog
    ;;
  all)
    check_quality_catalog
    check_quality_exposure
    check_today_catalog
    check_semantic_catalog
    ;;
  *)
    echo "FATAL: invalid --check value: ${SUB_SCOPE} (expected quality, today, semantic, all)" >&2
    exit 1
    ;;
esac

if [ "${VERIFY_ALL_RUNNING:-0}" != "1" ]; then
  finish
fi
