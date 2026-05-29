#!/usr/bin/env bash
# verify-research.sh — research 모드 등록·문서·픽스처 무결성 검증
# (PLAN-research-mode.md §19.4 + §8.13 — 8 항목 11-7 ~ 11-14)
#
# 검증:
#   [11-7]  /dev-advisor research SKILL.md 등록
#   [11-8]  research 자연어 트리거 (최소 2개) — SKILL.md+_routing.md+_help.md scope
#   [11-9]  output_templates.md research 스켈레톤
#   [11-10] examples.md 에 research 예시 K/L/M 3개
#   [11-11] handoff.md 3 에이전트 + OMX/xhigh 정책
#   [11-12] references/research/fixtures/ JSON ≥ 5
#   [11-13] OpenAlex Topics ID 사전 검증 로그 (sources.md)
#   [11-14] references/research/*.md 7개 파일 + 각 ≥ 200 라인
#
# Args:
#   --check research | all
#   --help

set -euo pipefail

VERIFY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/_common.sh
source "${VERIFY_DIR}/lib/_common.sh"

print_help() {
  cat <<EOF
Usage: $(basename "$0") [--check research|all] [--help]

Verifies research mode registration, triggers, fixtures (≥5 JSON), OpenAlex
sources, and 7 research/*.md files (each ≥200 lines).
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

check_research_mode() {
  echo "[R] research 모드 등록·문서·픽스처 검증"

  local skill_file="${SKILL_DIR}/SKILL.md"
  local routing_file="${SKILL_DIR}/references/workflows/_routing.md"
  local help_file="${SKILL_DIR}/references/_help.md"
  local templates_file="${SKILL_DIR}/references/output_templates.md"
  local examples_file="${SKILL_DIR}/references/examples.md"
  local handoff_file="${SKILL_DIR}/references/handoff.md"
  local research_dir="${SKILL_DIR}/references/research"
  local fixtures_dir="${research_dir}/fixtures"
  local sources_file="${research_dir}/sources.md"

  # 11-7. /dev-advisor research SKILL.md 등록 확인
  local research_cmd_count
  research_cmd_count=$(grep -c '/dev-advisor research' "${skill_file}" 2>/dev/null || echo 0)
  if [ "${research_cmd_count}" -ge 1 ]; then
    ok "[11-7] research SKILL.md 등록: ${research_cmd_count}회 노출"
  else
    fail "[11-7] research SKILL.md 등록: /dev-advisor research 미노출"
  fi

  # 11-8. research 자연어 트리거 (최소 2개)
  # Progressive Disclosure scope: SKILL.md + _routing.md + _help.md
  local research_triggers=0
  local trigger trigger_files=("${skill_file}" "${routing_file}" "${help_file}")
  for trigger in '논문' 'research' 'SOTA' 'literature review' '학술' '최신 연구' '근거 논문'; do
    local f found=0
    for f in "${trigger_files[@]}"; do
      [ -f "${f}" ] || continue
      if grep -qF "${trigger}" "${f}"; then
        found=1
        break
      fi
    done
    if [ "${found}" -eq 1 ]; then
      research_triggers=$((research_triggers + 1))
    fi
  done
  if [ "${research_triggers}" -ge 2 ]; then
    ok "[11-8] research 트리거 키워드 (≥2): ${research_triggers}/7 매칭"
  else
    fail "[11-8] research 트리거 키워드: ${research_triggers}/7 매칭 (최소 2개 필요)"
  fi

  # 11-9. output_templates.md 에 research 모드 스켈레톤 존재 확인
  if [ -f "${templates_file}" ]; then
    local research_template_count
    research_template_count=$(grep -cE "research 모드 스켈레톤|^## research 모드" "${templates_file}" 2>/dev/null || echo 0)
    if [ "${research_template_count}" -ge 1 ]; then
      ok "[11-9] output_templates.md research 스켈레톤: ${research_template_count}개 헤더"
    else
      fail "[11-9] output_templates.md research 스켈레톤 누락"
    fi
  else
    fail "[11-9] output_templates.md 파일 없음"
  fi

  # 11-10. examples.md 에 research 예시 K/L/M 3개 존재 확인
  if [ -f "${examples_file}" ]; then
    local klm_count
    klm_count=$(grep -cE '^#{2,3} [KLM]\.' "${examples_file}" 2>/dev/null || echo 0)
    if [ "${klm_count}" -ge 3 ]; then
      ok "[11-10] examples.md research 예시 K/L/M: ${klm_count}개 헤더 존재"
    else
      fail "[11-10] examples.md research 예시 K/L/M: ${klm_count}개 (3개 필요)"
    fi
  else
    fail "[11-10] examples.md 파일 없음"
  fi

  # 11-11. handoff.md 에 3 에이전트 + OMX/xhigh 정책 명시
  if [ -f "${handoff_file}" ]; then
    local handoff_missing=0 agent
    for agent in 'document-specialist' 'analyst' 'scientist'; do
      if ! grep -q "${agent}" "${handoff_file}"; then
        handoff_missing=$((handoff_missing + 1))
      fi
    done
    local omx_policy_count
    omx_policy_count=$(grep -cE 'xhigh|OMX|spawn_agent' "${handoff_file}" 2>/dev/null || echo 0)
    if [ "${handoff_missing}" -eq 0 ] && [ "${omx_policy_count}" -ge 1 ]; then
      ok "[11-11] handoff.md 3 에이전트 등록 + OMX/xhigh 정책 ${omx_policy_count}회"
    elif [ "${handoff_missing}" -gt 0 ]; then
      fail "[11-11] handoff.md 누락 에이전트: ${handoff_missing}/3"
    else
      fail "[11-11] handoff.md OMX/xhigh 정책 미명시"
    fi
  else
    fail "[11-11] handoff.md 파일 없음"
  fi

  # 11-12. references/research/fixtures/ 디렉토리 + 최소 5 JSON
  if [ -d "${fixtures_dir}" ]; then
    local fixture_count
    fixture_count=$(find "${fixtures_dir}" -name "*.json" -type f 2>/dev/null | grep -c . || echo 0)
    if [ "${fixture_count}" -ge 5 ]; then
      ok "[11-12] research/fixtures/ JSON 케이스: ${fixture_count}개 (≥5)"
    else
      fail "[11-12] research/fixtures/ JSON 케이스: ${fixture_count}개 (5개 필요)"
    fi
  else
    fail "[11-12] research/fixtures/ 디렉토리 없음"
  fi

  # 11-13. OpenAlex Topics ID 사전 검증 로그
  if [ -f "${sources_file}" ]; then
    local topics_count
    topics_count=$(grep -cE 'T12490|T11269|T10126|T10734|T10260|T10743|T10320|T10715|T10317' "${sources_file}" 2>/dev/null || echo 0)
    local phase2_present=0
    if grep -q "Phase 2 검증\|Phase 2 실측" "${sources_file}"; then
      phase2_present=1
    fi
    if [ "${topics_count}" -ge 9 ] || [ "${phase2_present}" -eq 1 ]; then
      ok "[11-13] OpenAlex Topics ID 사전 검증: Topics ${topics_count}회 / Phase 2 키워드=${phase2_present}"
    else
      fail "[11-13] OpenAlex Topics ID 사전 검증 부족"
    fi
  else
    fail "[11-13] sources.md 파일 없음"
  fi

  # 11-14. references/research/*.md anchor 무결성 — 7개 핵심 파일 존재 + ≥200 lines
  local research_files=(sources.md query-strategies.md output-format.md mapping-algorithm.md fallback.md performance.md testing.md)
  local missing_files=0
  local short_files=0
  local missing_list=""
  local short_list=""
  local f fpath file_lines
  for f in "${research_files[@]}"; do
    fpath="${research_dir}/${f}"
    if [ ! -f "${fpath}" ]; then
      missing_files=$((missing_files + 1))
      missing_list="${missing_list}${f}, "
      continue
    fi
    file_lines=$(grep -c "" "${fpath}" 2>/dev/null || echo 0)
    if [ "${file_lines}" -lt 200 ]; then
      short_files=$((short_files + 1))
      short_list="${short_list}${f}(${file_lines}), "
    fi
  done
  if [ "${missing_files}" -eq 0 ] && [ "${short_files}" -eq 0 ]; then
    ok "[11-14] research/*.md 7개 파일 모두 존재 + 각 ≥200 라인"
  elif [ "${missing_files}" -gt 0 ]; then
    fail "[11-14] research/*.md 누락 ${missing_files}개: ${missing_list}"
  else
    fail "[11-14] research/*.md 부족 ${short_files}개 (<200 라인): ${short_list}"
  fi
}

echo "=== verify-research ==="
echo ""
check_research_mode

if [ "${VERIFY_ALL_RUNNING:-0}" != "1" ]; then
  finish
fi
