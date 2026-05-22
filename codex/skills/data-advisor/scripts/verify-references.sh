#!/usr/bin/env bash
# verify-references.sh — data-advisor 스킬 무결성 검증 (standalone)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REFS="${SKILL_DIR}/references"

PASS=0; FAIL=0
ok()   { echo "  ✓ $1"; PASS=$((PASS+1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL+1)); }

# .counts.manifest 로드
MANIFEST="${SKILL_DIR}/.counts.manifest"
if [ ! -f "${MANIFEST}" ]; then
  echo "FATAL: .counts.manifest not found" >&2; exit 1
fi
# shellcheck disable=SC1090
source "${MANIFEST}"

echo "=== data-advisor integrity check ==="
echo ""

# [0] manifest 존재 + 배포 파일 없음
echo "[0] manifest / hygiene"
ok "manifest 존재: .counts.manifest"
forbidden=$(find "${SKILL_DIR}" \( -name .DS_Store -o -name __pycache__ -o -name '*.pyc' \) -print 2>/dev/null || true)
if [ -z "${forbidden}" ]; then ok "배포 제외 파일 없음"
else fail "배포 제외 파일: ${forbidden}"; fi
echo ""

# [1] 7개 파일 존재
echo "[1] 참조 파일 존재"
for f in \
  patterns/mdm.md \
  patterns/data-quality.md \
  patterns/data-warehousing.md \
  algorithms/db-indexes.md \
  algorithms/db-storage-engines.md \
  algorithms/db-query-optimizer.md \
  principles/db-fundamentals.md; do
  if [ -f "${REFS}/${f}" ]; then ok "존재: references/${f}"
  else fail "누락: references/${f}"; fi
done
echo ""

# [2] anchor 수 검증
echo "[2] anchor 수 (## N. 헤더 == <a id=> 수)"
check_file() {
  local rel="$1" expected="$2"
  local path="${REFS}/${rel}"
  local anchors headers
  anchors=$(/usr/bin/grep -c '<a id=' "${path}" 2>/dev/null || echo 0)
  headers=$(/usr/bin/grep -cE '^## [0-9]+\.' "${path}" 2>/dev/null || echo 0)
  if [ "${anchors}" -ge "${expected}" ] && [ "${headers}" -ge "${expected}" ]; then
    ok "${rel}: anchors=${anchors} headers=${headers} (≥${expected})"
  else
    fail "${rel}: anchors=${anchors} headers=${headers} expected≥${expected}"
  fi
}
check_file "patterns/mdm.md"              6
check_file "patterns/data-quality.md"     6
check_file "patterns/data-warehousing.md" 6
check_file "principles/db-fundamentals.md" 8
check_file "algorithms/db-indexes.md"      8
check_file "algorithms/db-storage-engines.md" 10
check_file "algorithms/db-query-optimizer.md"  5
echo ""

# [3] 총 항목 수 == manifest
echo "[3] 총 항목 수 검증"
pat_total=$(find "${REFS}/patterns" -name '*.md' ! -name 'index.md' -print0 \
  | xargs -0 /usr/bin/grep -hE '^## [0-9]+\.' 2>/dev/null | wc -l | tr -d ' ')
algo_total=$(find "${REFS}/algorithms" -name '*.md' ! -name 'index.md' -print0 \
  | xargs -0 /usr/bin/grep -hE '^## [0-9]+\.' 2>/dev/null | wc -l | tr -d ' ')
pri_total=$(find "${REFS}/principles" -name '*.md' ! -name 'index.md' -print0 \
  | xargs -0 /usr/bin/grep -hE '^## [0-9]+\.' 2>/dev/null | wc -l | tr -d ' ')
grand=$((pat_total + algo_total + pri_total))

[ "${pat_total}"  -eq "${EXPECTED_PATTERNS}"  ] && ok "patterns: ${pat_total}" || fail "patterns: expect=${EXPECTED_PATTERNS} actual=${pat_total}"
[ "${algo_total}" -eq "${EXPECTED_ALGORITHMS}" ] && ok "algorithms: ${algo_total}" || fail "algorithms: expect=${EXPECTED_ALGORITHMS} actual=${algo_total}"
[ "${pri_total}"  -eq "${EXPECTED_PRINCIPLES}" ] && ok "principles: ${pri_total}" || fail "principles: expect=${EXPECTED_PRINCIPLES} actual=${pri_total}"
[ "${grand}"      -eq "${EXPECTED_TOTAL}"      ] && ok "TOTAL: ${grand}" || fail "TOTAL: expect=${EXPECTED_TOTAL} actual=${grand}"
echo ""

# [4] db-fundamentals key anchors 보존
echo "[4] db-fundamentals key anchors"
DB_PATH="${REFS}/principles/db-fundamentals.md"
for anchor in acid-vs-base tx-isolation-levels consistency-models normalization-1nf-bcnf cap-pacelc; do
  if /usr/bin/grep -q "id=\"${anchor}\"" "${DB_PATH}"; then
    ok "anchor 존재: ${anchor}"
  else
    fail "anchor 누락: ${anchor}"
  fi
done
echo ""

# [5] catalog-index.json 검증 (존재하면)
echo "[5] catalog-index.json"
CATALOG="${SKILL_DIR}/catalog-index.json"
if [ -f "${CATALOG}" ]; then
  if python3 "${SCRIPT_DIR}/generate-catalog-index.py" --check > /dev/null 2>&1; then
    ok "catalog-index.json up-to-date"
  else
    fail "catalog-index.json stale (run: python3 scripts/generate-catalog-index.py)"
  fi
else
  fail "catalog-index.json 누락 (run: python3 scripts/generate-catalog-index.py)"
fi
echo ""

echo "======================================"
if [ "${FAIL}" -eq 0 ]; then
  echo "✓ All integrity checks passed (${EXPECTED_PATTERNS} patterns / ${EXPECTED_ALGORITHMS} algorithms / ${EXPECTED_PRINCIPLES} principles — ${EXPECTED_TOTAL} total)"
  exit 0
else
  echo "✗ ${FAIL}개 검사 실패, ${PASS}개 통과"
  exit 1
fi
