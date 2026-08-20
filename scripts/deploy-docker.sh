#!/usr/bin/env bash
# Docker equivalent of scripts/deploy.sh — no local Python needed on the server.
# Usage: scripts/deploy-docker.sh <branch> <serve-dir>
#   scripts/deploy-docker.sh staging /var/www/docs-staging
#   scripts/deploy-docker.sh main    /var/www/docs
set -euo pipefail

BRANCH="${1:?branch required, e.g. main or staging}"
SERVE_DIR="${2:?serve dir required, e.g. /var/www/docs}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="mkdocs-pilot"

cd "$REPO_DIR"
git fetch origin
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

docker build -t "$IMAGE" .
mkdir -p "$SERVE_DIR"

# Run as the calling user so the built files aren't owned by root on the host.
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$REPO_DIR":/docs \
  -v "$SERVE_DIR":/site \
  "$IMAGE" build --strict -d /site
