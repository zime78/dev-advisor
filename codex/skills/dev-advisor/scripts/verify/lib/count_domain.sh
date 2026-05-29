#!/usr/bin/env bash
# count_domain.sh — patterns/security/principles 카테고리 카운트 일원화 라이브러리
#
# 원본 verify-references.sh 의 count_pat/check_pat (line 1131/1161),
# count_sec/check_sec (line 1224/1243), count_pri/check_pri (line 1296/1317)
# 세 쌍 거의 동일 함수를 단일 check_domain() 으로 통합한다.
#
# 사용:
#   source lib/_common.sh
#   source lib/count_domain.sh
#   check_domain patterns creational 5         # 단일 카테고리
#   total=$(domain_total patterns "${cats}")   # 합계 계산

# ## N. 헤더 카운트 (특정 도메인의 카테고리 .md 파일에서)
# Usage: count_domain_category <domain> <category>
# 예: count_domain_category patterns creational
count_domain_category() {
  local domain="$1"
  local category="$2"
  local path="${SKILL_DIR}/references/${domain}/${category}.md"
  /usr/bin/grep -cE '^## [0-9]+\.' "${path}" 2>/dev/null || echo 0
}

# 단일 카테고리 검증. 실제 값과 기대 값이 다르면 fail.
# Usage: check_domain <domain> <category> <expected>
# 예: check_domain patterns creational 5
check_domain() {
  local domain="$1"
  local category="$2"
  local expected="$3"
  local actual
  actual=$(count_domain_category "${domain}" "${category}")
  if [ "${actual}" -eq "${expected}" ]; then
    ok "${category}: ${actual}개"
  else
    fail "${category}: 기대=${expected}, 실제=${actual}"
  fi
}

# 도메인 전체 합계. 카테고리 공백 구분 리스트를 받는다.
# Usage: domain_total <domain> "cat1 cat2 cat3"
# 예: total=$(domain_total patterns "creational structural behavioral")
domain_total() {
  local domain="$1"
  local categories="$2"
  local sum=0
  local cat n
  for cat in ${categories}; do
    n=$(count_domain_category "${domain}" "${cat}")
    sum=$((sum + n))
  done
  echo "${sum}"
}
