#!/usr/bin/env bash
# Run on the server after (or as part of) a git pull.
# Usage: scripts/deploy.sh <branch> <serve-dir>
#   scripts/deploy.sh staging /var/www/docs-staging
#   scripts/deploy.sh main    /var/www/docs
set -euo pipefail

BRANCH="${1:?branch required, e.g. main or staging}"
SERVE_DIR="${2:?serve dir required, e.g. /var/www/docs}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_DIR"
git fetch origin
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install --quiet -r requirements.txt

.venv/bin/mkdocs build --strict -d "$SERVE_DIR"
