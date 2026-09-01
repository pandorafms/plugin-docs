# Repository Agent Workflow

This repository publishes the Pandora FMS integration documentation. Treat `mkdocs.yml`, the [contributor guide](docs/en/extras/how-to-document.md), and `.github/PULL_REQUEST_TEMPLATE.md` as the sources of truth.

Documentation skills govern content research, writing, and content validation. This file governs Git workflow and delivery in this repository.

## Git safety

- Check the working tree before switching branches or starting work.
- Never overwrite or discard changes you did not create.
- Do not work or commit directly on `main`. Create a branch from `main`; no branch naming pattern is required yet.
- Commit only when the user explicitly requests it. Use Conventional Commits when creating a commit; no ticket reference is required by this repository.
- Never add AI attribution or `Co-Authored-By` trailers.
- Never run `git push`. Remote publication is a human responsibility.

## Pull requests

- Target `main` and use `.github/PULL_REQUEST_TEMPLATE.md`.
- Report the affected languages and section, sidebar impact, changed files, and verification performed.
- Do not invent approval, issue, or label requirements.

## Validation

Previewing the site is not validation. Run one strict build:

```bash
.venv/bin/mkdocs build --strict
```

or:

```bash
UID=$(id -u) GID=$(id -g) docker compose run --rm docs build --strict
```

Report honestly when validation was not run. Do not enforce rules for a future validator until it exists and is documented.

## Content safeguards

- Preserve published slugs by default. Do not rename an existing page without explicit authorization and an approved redirect mechanism.
- Maintain English/Spanish parity and image fallback behavior as documented in the contributor guide.
