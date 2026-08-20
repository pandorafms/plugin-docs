"""
mkdocs-static-i18n always alpha-sorts the top-level nav when it flattens the
per-language section (see mkdocs_static_i18n/folder.py, reconfigure_navigation),
overriding whatever order mkdocs-awesome-pages-plugin set up via .pages files.
That sort runs at event_priority(-100), so we run even later to have the
final say and pin specific sections to a fixed position regardless of it.
"""

import shutil
from pathlib import Path

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


def on_post_build(config):
    """
    Material's language switcher reuses the mkdocs-material version-selector
    JS, which fetches "sitemap.xml" relative to the *current page's own
    directory* — not the site root, not even the language root. A page at
    /es/plugins/oculix/ requests /es/plugins/oculix/sitemap.xml, which 404s
    because mkdocs-static-i18n only writes one combined sitemap.xml at the
    site root (the correct approach for SEO — one sitemap listing every
    language's alternates, not one per page). Silence the 404 by mirroring
    that same file into every directory that contains a page.
    """
    site_dir = Path(config.site_dir)
    sitemap = site_dir / "sitemap.xml"
    if not sitemap.exists():
        return

    for index_html in site_dir.rglob("index.html"):
        page_dir = index_html.parent
        if page_dir == site_dir:
            continue
        shutil.copy2(sitemap, page_dir / "sitemap.xml")
