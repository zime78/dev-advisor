#!/usr/bin/env bash
#
# sync-skill-counts.sh — Single Source of Truth (SoT) templating for dev-advisor counts
#
# Usage:
#   bin/sync-skill-counts.sh            # Apply replacements in-place
#   bin/sync-skill-counts.sh --dry-run  # Show what would change (no writes)
#   bin/sync-skill-counts.sh --check    # Exit 1 if any target file differs from manifest
#
# Source of Truth: .counts.manifest (bash variable file, sourced as-is)
#
# Replacement strategy:
#   Marker-based — only content between <!--counts:KEY-->VALUE<!--/--> is updated.
#   This is idempotent and safe to run repeatedly. No fragile free-text regex.
#
# Markers (HTML comments — invisible in rendered markdown):
#   <!--counts:patterns-->529<!--/-->
#   <!--counts:algorithms-->256<!--/-->
#   <!--counts:languages-->75<!--/-->
#   <!--counts:security-->106<!--/-->
#   <!--counts:principles-->206<!--/-->
#   <!--counts:quality-->20<!--/-->
#   <!--counts:micro-->18<!--/-->
#   <!--counts:total-->1192<!--/-->
#   <!--counts:total-with-micro-->1210<!--/-->
#
# NOTE: Compatible with bash 3.2 (macOS system bash). Uses parallel arrays
# instead of associative arrays (`declare -A`) which require bash 4+.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MANIFEST="${SKILL_ROOT}/.counts.manifest"

if [[ ! -f "${MANIFEST}" ]]; then
  echo "ERROR: .counts.manifest not found at ${MANIFEST}" >&2
  exit 2
fi

# shellcheck source=/dev/null
source "${MANIFEST}"

MODE="apply"
case "${1:-}" in
  --dry-run) MODE="dry-run" ;;
  --check)   MODE="check" ;;
  --help|-h)
    sed -n '2,28p' "${BASH_SOURCE[0]}"
    exit 0
    ;;
  "")        MODE="apply" ;;
  *)
    echo "ERROR: unknown argument: $1" >&2
    exit 2
    ;;
esac

# Target files (absolute paths)
TARGETS=(
  "${SKILL_ROOT}/SKILL.md"
  "${HOME}/.claude/commands/dev-advisor.md"
  "${SKILL_ROOT}/references/README.md"
  "${SKILL_ROOT}/scripts/README.md"
)

# Parallel arrays: MARKER_KEYS[i] ↔ MARKER_VALUES[i]
# Order matters only for predictable output; values are matched by exact key.
MARKER_KEYS=(
  "patterns"
  "algorithms"
  "languages"
  "security"
  "principles"
  "quality"
  "micro"
  "total"
  "total-with-micro"
)
MARKER_VALUES=(
  "${EXPECTED_PATTERNS}"
  "${EXPECTED_ALGORITHMS}"
  "${EXPECTED_LANGUAGES}"
  "${EXPECTED_SECURITY}"
  "${EXPECTED_PRINCIPLES}"
  "${EXPECTED_QUALITY}"
  "${EXPECTED_MICRO_PRINCIPLES}"
  "${EXPECTED_TOTAL}"
  "${EXPECTED_TOTAL_WITH_MICRO}"
)

# replace_markers <input_file> <output_file>
replace_markers() {
  local in_file="$1"
  local out_file="$2"
  local tmp
  tmp="$(mktemp)"
  cp "${in_file}" "${tmp}"
  local i key value pattern
  for i in "${!MARKER_KEYS[@]}"; do
    key="${MARKER_KEYS[$i]}"
    value="${MARKER_VALUES[$i]}"
    # Match: <!--counts:KEY-->ANY<!--/-->  (no '<' inside)
    # Replace inner value while preserving markers.
    # Use ~ as sed delimiter to avoid clashes with /.
    pattern="s~<!--counts:${key}-->[^<]*<!--/-->~<!--counts:${key}-->${value}<!--/-->~g"
    sed -E "${pattern}" "${tmp}" > "${tmp}.next"
    mv "${tmp}.next" "${tmp}"
  done

  # YAML frontmatter description sync (bare numbers, no markers).
  # Skill matching uses description as semantic text — HTML markers add noise tokens.
  # Markers must stay only in the markdown body, never in YAML frontmatter.
  # Pattern: "(NN 패턴 / NN 알고리즘 / NN 언어 / NN 보안 / NN 원칙 / NN 품질 + NN 부록)"
  # Anchored by the surrounding parenthetical so unrelated numeric sequences are untouched.
  local desc_pattern
  desc_pattern="s~\\([0-9]+ 패턴 / [0-9]+ 알고리즘 / [0-9]+ 언어 / [0-9]+ 보안 / [0-9]+ 원칙 / [0-9]+ 품질 \\+ [0-9]+ 부록\\)~(${EXPECTED_PATTERNS} 패턴 / ${EXPECTED_ALGORITHMS} 알고리즘 / ${EXPECTED_LANGUAGES} 언어 / ${EXPECTED_SECURITY} 보안 / ${EXPECTED_PRINCIPLES} 원칙 / ${EXPECTED_QUALITY} 품질 + ${EXPECTED_MICRO_PRINCIPLES} 부록)~g"
  sed -E "${desc_pattern}" "${tmp}" > "${tmp}.next"
  mv "${tmp}.next" "${tmp}"

  mv "${tmp}" "${out_file}"
}

exit_code=0
for target in "${TARGETS[@]}"; do
  if [[ ! -f "${target}" ]]; then
    echo "WARN: target not found, skipping: ${target}" >&2
    continue
  fi
  case "${MODE}" in
    apply)
      tmp_out="$(mktemp)"
      replace_markers "${target}" "${tmp_out}"
      if ! diff -q "${target}" "${tmp_out}" >/dev/null 2>&1; then
        cp "${tmp_out}" "${target}"
        echo "UPDATED ${target}"
      else
        echo "OK      ${target}"
      fi
      rm -f "${tmp_out}"
      ;;
    dry-run)
      tmp_out="$(mktemp)"
      replace_markers "${target}" "${tmp_out}"
      if ! diff -q "${target}" "${tmp_out}" >/dev/null 2>&1; then
        echo "WOULD UPDATE ${target}"
        diff -u "${target}" "${tmp_out}" | sed -n '1,40p'
      else
        echo "OK            ${target}"
      fi
      rm -f "${tmp_out}"
      ;;
    check)
      tmp_out="$(mktemp)"
      replace_markers "${target}" "${tmp_out}"
      if ! diff -q "${target}" "${tmp_out}" >/dev/null 2>&1; then
        echo "DRIFT ${target}" >&2
        exit_code=1
      fi
      rm -f "${tmp_out}"
      ;;
  esac
done

if [[ "${MODE}" == "check" && ${exit_code} -ne 0 ]]; then
  echo "" >&2
  echo "One or more files drift from .counts.manifest." >&2
  echo "Run bin/sync-skill-counts.sh (no args) to fix." >&2
fi

exit ${exit_code}
