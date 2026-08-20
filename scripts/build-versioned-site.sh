#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${1:-site}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_DIR"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
git archive gh-pages | tar -x -C "$OUTPUT_DIR" --warning=no-timestamp

printf 'Exported local gh-pages to %s\n' "$OUTPUT_DIR"
