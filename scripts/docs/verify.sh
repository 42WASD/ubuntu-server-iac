#!/usr/bin/env bash
# Deterministic verification pipeline for the SSOT docs system.
#
# ONE entry point that runs every layer of the toolkit in order, so local
# debugging is byte-identical to CI. Exits non-zero on the first failure.
#
#   ./scripts/docs/verify.sh          # full pipeline (validate -> tests -> build)
#   ./scripts/docs/verify.sh --quick  # skip the full mkdocs build (fast)
#
# Layers covered:
#   Layer 1-2  docs_manifest.py --validate   structural + runbook invariants
#   Layer 3    pytest tests/                 golden + parity + lint
#   Layer 4    mkdocs build --strict         links / anchors / orphans
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

MODE="${1:-full}"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

say "Layer 1+2: manifest + runbook invariant validation"
python3 scripts/docs/docs_manifest.py --repo "$REPO_ROOT"

say "Layer 3: pytest validation suite (golden + structural)"
cd "$REPO_ROOT/projects"
uv run pytest -q

cd "$REPO_ROOT"

if [[ "$MODE" != "full" ]]; then
  say "Skipping mkdocs build (--stage passed)"
  echo "VERIFY OK"
  exit 0
fi

say "Layer 4: strict mkdocs build (links / anchors / orphans)"
cd "$REPO_ROOT/projects"
uv run mkdocs build --strict -f ../mkdocs.yml

echo
echo "VERIFY OK"