#!/usr/bin/env bash
# deprecated: verify-anchors.sh → use verify-references.sh
echo "[deprecated] verify-anchors.sh — use verify-references.sh" >&2
exec "$(dirname "$0")/verify-references.sh" "$@"
