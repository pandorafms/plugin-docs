#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?version required, for example latest}"
TITLE="${2:-Pandora FMS Guides ${VERSION}}"
ALIASES=("${@:3}")
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_DIR"
export PATH="$REPO_DIR/.venv/bin:$PATH"

ORIGINAL_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
trap 'git checkout --quiet "$ORIGINAL_BRANCH"' EXIT

args=(deploy "$VERSION" --title "$TITLE" --branch gh-pages)
if (( ${#ALIASES[@]} > 0 )); then
  args+=("${ALIASES[@]}" --update-aliases)
fi

mike "${args[@]}"

if [[ "$VERSION" == "latest" ]]; then
  mike set-default latest --branch gh-pages
else
  for alias in "${ALIASES[@]}"; do
    if [[ "$alias" == "latest" ]]; then
      mike set-default latest --branch gh-pages
      break
    fi
  done
fi

printf 'Deployed %s to local branch gh-pages.\n' "$VERSION"
if (( ${#ALIASES[@]} > 0 )); then
  printf 'Aliases:\n'
  printf '  - %s\n' "${ALIASES[@]}"
else
  printf 'Aliases: none (the existing root default is unchanged).\n'
fi
printf 'Inspect with: .venv/bin/mike serve\n'
