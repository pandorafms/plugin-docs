#!/usr/bin/env bash
# Serves the local gh-pages export through an Apache container, to verify
# the site behaves the same way it will once a prod repo/server serves it
# from that branch. Testing only — nothing here is meant for production.
set -euo pipefail

PORT="${1:-8080}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_DIR"
scripts/build-versioned-site.sh site

printf 'Serving gh-pages export at http://localhost:%s/\n' "$PORT"
printf 'Ctrl+C to stop.\n'

docker run --rm -p "${PORT}:80" \
  -v "$REPO_DIR/site":/usr/local/apache2/htdocs/:ro \
  httpd:2.4-alpine
