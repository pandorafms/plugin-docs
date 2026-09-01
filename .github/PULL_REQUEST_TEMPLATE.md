## Summary

<!-- What does this change add or fix? 1–3 sentences. -->

## Type of change

<!-- Check exactly one -->

- [ ] New page
- [ ] New section / subcategory
- [ ] Edit to an existing page
- [ ] Image(s) only
- [ ] Repository/tooling change (workflows, config, template, ...)

## Details

- **Section affected:** Plugins / Integrations / Discovery / Extras / Other
- **Languages:**
  - [ ] English (`docs/en/`)
  - [ ] Spanish (`docs/es/`) — if not ready, say why
- **Sidebar impact:** none / new top-level section (check `hooks.py` pin if so)
- **Files changed:**
  - `path/to/file` — what changed

## Verification

- [ ] Validator tests pass: `python3 -m unittest discover -s tests -p 'test_validate_docs.py'`
- [ ] Blocking quality gates pass: `python3 scripts/validate_docs.py --fail-on blocking`
- [ ] Strict build completed successfully (check one command):
  - [ ] `.venv/bin/mkdocs build --strict`
  - [ ] `UID=$(id -u) GID=$(id -g) docker compose run --rm docs build --strict`
- [ ] Images referenced with correct relative path and per-language fallback
- [ ] Optional: preview checked at http://localhost:8000 (preview is not validation)
