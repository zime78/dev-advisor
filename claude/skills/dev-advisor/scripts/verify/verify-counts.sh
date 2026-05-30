#!/usr/bin/env bash
# verify-counts.sh — 도메인 카운트 / manifest / sync-skill-counts SoT 검증
#
# 검증:
#   [0]  manifest 정합성 (repo 모드 codex/claude 동일성, 배포 hygiene)
#   [0B] 카탈로그 ## N. 헤더 합계 == manifest 값
#   [0C] bin/sync-skill-counts.sh --check (SKILL.md 카운트 마커 drift)
#   [3]  algorithms index.md ID 매핑 행 == EXPECTED_ALGORITHMS
#   [4]  algorithms progressive disclosure 구조 (카테고리/별칭/필수 섹션)
#
# Args:
#   --check counts | all (default all = 본 sub-script 의 전체 카운트)
#   --help

set -euo pipefail

VERIFY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/_common.sh
source "${VERIFY_DIR}/lib/_common.sh"

print_help() {
  cat <<EOF
Usage: $(basename "$0") [--check counts|all] [--help]

Verifies catalog counts against .counts.manifest and sync-skill-counts.sh markers.
Run as a sub-stage of verify-all.sh or standalone.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --check)
      shift 2 || { echo "FATAL: --check requires value" >&2; exit 1; }
      ;;
    --help|-h)
      print_help
      exit 0
      ;;
    *)
      echo "FATAL: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

preflight_tmp

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

  # 배포 hygiene: .DS_Store / __pycache__ / *.pyc 금지.
  # scripts/state/ (P2-d 생성 캐시) 와 docs/ (P1-a 이동본) 와 bin/ (P1-c) 는
  # 정상 산출물이므로 allowlist 처리.
  forbidden_files=$(find "${SKILL_DIR}" \
    -path "${SKILL_DIR}/scripts/state" -prune -o \
    -path "${SKILL_DIR}/docs" -prune -o \
    -path "${SKILL_DIR}/bin" -prune -o \
    \( -name .DS_Store -o -name __pycache__ -o -name '*.pyc' \) -print 2>/dev/null || true)
  if [ -z "${forbidden_files}" ]; then
    ok "배포 제외 파일 없음 (.DS_Store / __pycache__ / *.pyc)"
  else
    fail "배포 제외 파일 발견: $(printf '%s' "${forbidden_files}" | tr '\n' ' ')"
  fi

  # data-advisor 분리(2026-05-22) 이전 구 카탈로그 카운트가 마커 밖 prose 로
  # 재유입되는 드리프트를 차단. 마커 기반 sync-skill-counts.sh 가 감지하지 못하는
  # 비마커 파일(output_templates.md / principles/index.md 등)을 커버한다.
  # split-quote 로 작성해 가드 자신의 source 가 패턴에 매칭되지 않게 한다.
  stale_pattern='5'"중"'|7'"모드"'|core 16'"3"'|4'"중 카탈로그"'|5'" 서브에이전트"'|\b49'"6"'\b|\b26'"8"'\b|\b53'"9"'\b|54'"7"' 패턴|27'"3"'개? *알고리즘|21'"4"' 원칙|21'"4"' 합계'
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

  # P2-d 캐시 (scripts/state/catalog/meta.json) 우선 — actual_count 가 manifest 와 일치 확인 시 fast path
  local meta="${SKILL_DIR}/scripts/state/catalog/meta.json"
  local use_cache=0
  if [ -f "${meta}" ] && python3 -c "import json,sys; meta=json.load(open(sys.argv[1])); d=meta['domains']; sys.exit(0 if d['patterns']['actual_count']==${EXPECTED_PATTERNS} and d['principles']['actual_count']==${EXPECTED_PRINCIPLES} and d['security']['actual_count']==${EXPECTED_SECURITY} and d['quality']['actual_count']==${EXPECTED_QUALITY} else 1)" "${meta}" 2>/dev/null; then
    use_cache=1
  fi

  if [ "${use_cache}" -eq 1 ]; then
    ok "patterns 실제 ## N. 헤더 합계 = manifest (${EXPECTED_PATTERNS}) [cache]"
    ok "security 실제 항목 합계 = manifest (${EXPECTED_SECURITY}) [cache]"
    ok "principles 실제 ## N. 헤더 합계 = manifest (${EXPECTED_PRINCIPLES}) [cache]"
    ok "quality 실제 ## N. 헤더 합계 = manifest (${EXPECTED_QUALITY}) [cache]"
    return
  fi

  # Fallback: markdown walk
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

# bin/sync-skill-counts.sh --check 결과를 검증 단계로 흡수.
# SKILL.md / commands/dev-advisor.md / README 의 카운트 마커가 manifest 와 일치하지 않으면 drift.
check_sync_skill_counts() {
  echo "[0C] bin/sync-skill-counts.sh --check (카운트 마커 SoT)"
  local sync_script="${SKILL_DIR}/bin/sync-skill-counts.sh"
  if [ ! -x "${sync_script}" ]; then
    fail "bin/sync-skill-counts.sh 누락 또는 실행 권한 없음: ${sync_script}"
    return
  fi
  if "${sync_script}" --check >/dev/null 2>&1; then
    ok "카운트 마커가 manifest 와 일치 (drift 없음)"
  else
    fail "카운트 마커 drift — bin/sync-skill-counts.sh 재실행 필요"
  fi
}

check_algorithms_index() {
  echo "[3] index.md 알고리즘 ID 매핑 표 행 수 검증"

  local index_file="${SKILL_DIR}/references/algorithms/index.md"
  local index_count
  index_count=$(awk '/## 알고리즘 ID 매핑/{found=1; next} found && /^\|.*\.md#/{count++} END{print count+0}' "${index_file}")

  if [ "${index_count}" -eq "${EXPECTED_ALGORITHMS}" ]; then
    ok "index.md 링크 행: ${index_count}개"
  else
    fail "index.md 링크 행: 기대=${EXPECTED_ALGORITHMS}, 실제=${index_count}"
  fi
}

check_algorithms_disclosure() {
  echo "[4] algorithms progressive disclosure 구조 검증"
  local algo_index="${SKILL_DIR}/references/algorithms/index.md"

  # 4-1. 카테고리 진입점 표 데이터 행 == 29
  local cat_rows
  cat_rows=$(awk '
    /^## 알고리즘 ID 인덱스/{f=1; next}
    f && /^## /{f=0}
    f && /^\| / && !/^\|[-| :]+\|/ && !/^\| 카테고리 /{c++}
    END{print c+0}
  ' "${algo_index}")
  if [ "${cat_rows}" -eq 30 ]; then
    ok "카테고리 진입점 표 행: ${cat_rows}개"
  else
    fail "카테고리 진입점 표 행: 기대=30, 실제=${cat_rows}"
  fi

  # 4-2. 필수 섹션 3개 헤더
  local hdr
  for hdr in '## 알고리즘 ID 인덱스' '## 알고리즘 ID 명명 규칙' '## `/algorithm <id>` 호출 동작'; do
    if /usr/bin/grep -qF "${hdr}" "${algo_index}"; then
      ok "섹션 존재: ${hdr}"
    else
      fail "섹션 누락: ${hdr}"
    fi
  done

  # 4-3. 별칭 표 데이터 행 >= 5
  local alias_rows
  alias_rows=$(awk '
    /^### 알고리즘 별칭/{f=1; next}
    f && /^## /{f=0}
    f && /^\| / && !/^\|[-| :]+\|/ && !/^\| 별칭 /{c++}
    END{print c+0}
  ' "${algo_index}")
  if [ "${alias_rows}" -ge 5 ]; then
    ok "별칭 표 행: ${alias_rows}개 (>=5)"
  else
    fail "별칭 표 행: 기대>=5, 실제=${alias_rows}"
  fi
}

echo "=== verify-counts ==="
echo ""
check_manifest_alignment
echo ""
check_catalog_manifest_totals
echo ""
check_sync_skill_counts
echo ""
check_algorithms_index
echo ""
check_algorithms_disclosure

# verify-all.sh 가 source 한 경우 finish() 호출하지 않음
if [ "${VERIFY_ALL_RUNNING:-0}" != "1" ]; then
  finish
fi
