# Pandora FMS Plugin Documentation

Documentation site for Pandora FMS plugins, integrations, and Discovery
modules, built with [MkDocs](https://www.mkdocs.org/) and the
[Material](https://squidfunk.github.io/mkdocs-material/) theme.

## Stack

| Need | Solution | Package |
|---|---|---|
| Theme / UI | Material for MkDocs | `mkdocs-material` |
| Multilingual content | `docs/en/`, `docs/es/` folder structure, with automatic fallback to the default language for untranslated files | `mkdocs-static-i18n` |
| Images | Regular files in the repo + zoom/lightbox on the published site | `mkdocs-glightbox` |
| Sidebar menu | Multi-level tree generated purely from the folder structure | `mkdocs-awesome-pages-plugin` |
| Versioning | Version selector, always published as `latest` | `mike` |

## Quick start

```bash
git clone <repo>
cd plugin-docs
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve
```

Or with Docker, no local Python needed:

```bash
UID=$(id -u) GID=$(id -g) docker compose up
```

Both open `http://localhost:8000` with live reload, serving `/` (en) and
`/es/`.

## Writing documentation

Everything about content standards, adding pages/images, organizing the
sidebar, and translations lives in
[`docs/en/extras/how-to-document.md`](docs/en/extras/how-to-document.md) —
it's published on the site itself (**Extras** section) so it's always
one click away for anyone writing docs.

## Deployment

A server keeps a checkout of the repo and rebuilds the static site:

```bash
scripts/deploy.sh main /var/www/docs          # Python/venv
scripts/deploy-docker.sh main /var/www/docs   # Docker, no Python needed
```

The site is versioned with [mike](https://github.com/jimporter/mike), same
setup as the sibling project
[`pandorafms-mkdocs`](https://github.com/pandorafms/pandorafms-mkdocs), but
always published as `latest` — there's no parallel numbered versions here:

```bash
scripts/deploy-version.sh latest "Pandora FMS Guides"
git push origin gh-pages   # only from the authorized pipeline/checkout
```

Redeploying with the same command overwrites `/latest/`, nothing to clean up
by hand between deployments.
