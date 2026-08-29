#!/usr/bin/env bash
# One-time setup: enable the repo's git hooks (doc-index auto-sync).
# Cloning fresh? Run this once after clone:
#   bash scripts/docs/doc-impact/setup-git-hooks.sh
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

git config core.hooksPath .githooks
chmod +x "$REPO_ROOT/.githooks/"* 2>/dev/null || true

echo "hooks enabled: core.hooksPath=.githooks"
echo "post-commit will now resync the doc index after doc commits."
echo
echo "Also recommended (once per clone):"
echo "  python3 scripts/docs/doc-impact/doc-index.py status   # verify index freshness"