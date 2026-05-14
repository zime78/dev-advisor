#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILL_NAME="dev-advisor"

DRY_RUN=0
ONLY=""

usage() {
  cat <<'EOF'
dev-advisor skill installer

Usage:
  scripts/install-skills.sh [--dry-run] [--only codex|claude]

Options:
  --dry-run          Show what would be installed without copying files.
  --only codex       Install only the Codex skill.
  --only claude      Install only the Claude Code skill.
  -h, --help         Show this help.

Environment:
  CODEX_HOME         Override Codex home directory. Default: ~/.codex
  CLAUDE_HOME        Override Claude Code home directory. Default: ~/.claude
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --only)
      if [[ $# -lt 2 || ! "$2" =~ ^(codex|claude)$ ]]; then
        echo "error: --only requires 'codex' or 'claude'" >&2
        exit 2
      fi
      ONLY="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

copy_skill() {
  local source_dir="$1"
  local target_dir="$2"
  local label="$3"

  if [[ ! -d "$source_dir" ]]; then
    echo "✗ ${label}: source not found: ${source_dir}" >&2
    return 1
  fi

  local parent_dir
  parent_dir="$(dirname "$target_dir")"
  local backup_dir="${parent_dir}/.backups/${SKILL_NAME}-$(date +%Y%m%d%H%M%S)"

  echo "→ ${label}"
  echo "  source: ${source_dir}"
  echo "  target: ${target_dir}"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ -d "$target_dir" ]]; then
      echo "  backup: ${backup_dir}"
    fi
    echo "  dry-run: no files copied"
    return 0
  fi

  mkdir -p "$parent_dir"

  if [[ -d "$target_dir" ]]; then
    mkdir -p "$(dirname "$backup_dir")"
    mv "$target_dir" "$backup_dir"
    echo "  backup: ${backup_dir}"
  fi

  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude '.DS_Store' \
      --exclude '__pycache__/' \
      --exclude '*.pyc' \
      "${source_dir}/" "${target_dir}/"
  else
    cp -R "$source_dir" "$target_dir"
    find "$target_dir" \( -name '.DS_Store' -o -name '*.pyc' -o -name '__pycache__' \) -prune -exec rm -rf {} +
  fi

  echo "  installed"
}

install_codex() {
  local codex_home="${CODEX_HOME:-${HOME}/.codex}"
  local source_dir="${REPO_ROOT}/codex/skills/${SKILL_NAME}"
  local target_dir="${codex_home}/skills/${SKILL_NAME}"

  if [[ ! -d "$codex_home" && -z "${CODEX_HOME:-}" && ! "$(command -v codex || true)" ]]; then
    echo "↷ Codex: not detected, skipped"
    return 0
  fi

  copy_skill "$source_dir" "$target_dir" "Codex"
}

install_claude() {
  local claude_home="${CLAUDE_HOME:-${HOME}/.claude}"
  local source_dir="${REPO_ROOT}/claude/skills/${SKILL_NAME}"
  local target_dir="${claude_home}/skills/${SKILL_NAME}"

  if [[ ! -d "$claude_home" && -z "${CLAUDE_HOME:-}" && ! "$(command -v claude || true)" ]]; then
    echo "↷ Claude Code: not detected, skipped"
    return 0
  fi

  copy_skill "$source_dir" "$target_dir" "Claude Code"
}

main() {
  echo "dev-advisor skill installer"
  echo "repo: ${REPO_ROOT}"

  case "$ONLY" in
    codex)
      install_codex
      ;;
    claude)
      install_claude
      ;;
    "")
      install_codex
      install_claude
      ;;
  esac

  echo "done"
}

main
