#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${1:-site}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_DIR"

if ! git rev-parse --verify --quiet gh-pages >/dev/null; then
  printf 'No local gh-pages branch found. Run scripts/deploy-version.sh first, e.g.:\n' >&2
  printf '  scripts/deploy-version.sh latest "Pandora FMS Guides"\n' >&2
  exit 1
fi

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
git archive gh-pages | tar -x -C "$OUTPUT_DIR" --warning=no-timestamp

printf 'Exported local gh-pages to %s\n' "$OUTPUT_DIR"
