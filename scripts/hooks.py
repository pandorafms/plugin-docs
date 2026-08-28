"""
mkdocs-static-i18n always alpha-sorts the top-level nav when it flattens the
per-language section (see mkdocs_static_i18n/folder.py, reconfigure_navigation),
overriding whatever order mkdocs-awesome-pages-plugin set up via .pages files.
That sort runs at event_priority(-100), so we run even later to have the
final say and pin specific sections to a fixed position regardless of it.

The rest of the hooks patch mkdocs-static-i18n / Material quirks in the
versioned (mike) deployment, where the per-version site is nested under a
path prefix such as /docs/integrations/latest/ instead of being served at
the domain root:

- Material's language switcher reuses the mkdocs-material version-selector
  JS, which fetches "sitemap.xml" relative to the *current page's own
  directory* — not the site root, not even the language root. A page at
  /es/plugins/oculix/ requests /es/plugins/oculix/sitemap.xml, which 404s
  because mkdocs-static-i18n only writes one combined sitemap.xml at the
  site root. The same file is mirrored into every page directory to silence
  that 404.
- mkdocs-static-i18n builds the sitemap <xhtml:link> alternates with
  urljoin(site_url, alternate_url) on the *versioned* site_url that mike sets
  without a trailing slash (e.g. https://.../latest). Joining "es/..." onto
  it produces .../latestes/... instead of .../latest/es/..., i.e. a 404 for
  every Spanish alternate. We repair that join in the generated sitemap.
"""

import os
import shutil
from pathlib import Path
from urllib.parse import urlsplit

from mkdocs.plugins import event_priority

# Section titles that must always render last, in this exact order.
PINNED_LAST = ["Extras"]


@event_priority(-200)
def on_nav(nav, config, files):
    def sort_key(item):
        title = item.title or ""
        if title in PINNED_LAST:
            return (1, PINNED_LAST.index(title))
        return (0, 0)

    nav.items.sort(key=sort_key)
    return nav


def _version_prefix(config):
    """
    Return the domain-root-relative path of the current mike version, e.g.
    "/docs/integrations/latest/", or None when not building under mike.

    mike sets site_url per version (via urljoin(site_url, version), without a
    trailing slash) and exports MIKE_DOCS_VERSION to the build subprocess, so
    both signals are reliable. Plain builds/serve are root-hosted, where the
    sitemap alternates are built correctly and must NOT be rewritten.
    """
    if not os.environ.get("MIKE_DOCS_VERSION"):
        return None
    path = urlsplit(config.get("site_url") or "").path
    if not path.startswith("/") or path == "/":
        return None
    return path if path.endswith("/") else path + "/"


def _fix_sitemap_alternates(site_dir, prefix):
    sitemap = site_dir / "sitemap.xml"
    if not sitemap.exists():
        return
    text = sitemap.read_text(encoding="utf-8")
    # urljoin(site_url_without_trailing_slash, "es/...") yields
    # "/docs/integrations/latestes/..." — note the missing slash between the
    # version segment and the language segment. Repair that join.
    broken = prefix.rstrip("/") + "es/"
    fixed = prefix + "es/"
    if broken in text:
        sitemap.write_text(text.replace(broken, fixed), encoding="utf-8")


def on_post_build(config):
    """
    Patch versioned-build quirks in the generated site. Only rewrites the
    sitemap when building under mike (see _version_prefix); plain root-hosted
    builds are left untouched.
    """
    site_dir = Path(config.site_dir)

    prefix = _version_prefix(config)
    if prefix is not None:
        _fix_sitemap_alternates(site_dir, prefix)

    # Material's language switcher fetches sitemap.xml relative to the current
    # page's own directory; mirror the one combined sitemap into every
    # directory that contains a page so that request never 404s.
    sitemap = site_dir / "sitemap.xml"
    if sitemap.exists():
        for index_html in site_dir.rglob("index.html"):
            page_dir = index_html.parent
            if page_dir == site_dir:
                continue
            shutil.copy2(sitemap, page_dir / "sitemap.xml")