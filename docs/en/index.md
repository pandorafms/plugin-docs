# Pandora FMS Guides — Pilot

This is a pilot migration from BookStack to **MkDocs + Material**, with:

- Multilanguage support (`mkdocs-static-i18n`, folder-based: `docs/en/`, `docs/es/`)
- Image handling via Git commits + lightbox zoom (`mkdocs-glightbox`)
- Staging deploys per branch through GitLab CI/Pages

## Example image

Images live as plain files under `docs/<lang>/assets/images/` and are referenced
from markdown like any static site. If a language folder doesn't have a
localized copy of an asset, it automatically falls back to the default
language's file (`fallback_to_default: true`).

![Pilot screenshot](assets/images/screenshot.png)

Next: [How to document](extras/how-to-document.md)
