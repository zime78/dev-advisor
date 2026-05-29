#!/usr/bin/env bash
# verify-references.sh — DEPRECATED ENTRY POINT
# scripts/verify/verify-all.sh 로 위임. CI/lefthook 등 기존 호출자 호환용.
#
# 본 wrapper 는 모든 인자를 그대로 전달한다.
#   --check all|today|quality|semantic|research|counts|anchors|modes
# 5 sub-stage 분할 후에도 기존 scope 키워드(today, quality, semantic, research) 유지.
set -euo pipefail
exec "$(dirname "$0")/verify/verify-all.sh" "$@"
