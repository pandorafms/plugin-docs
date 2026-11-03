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

import json
import os
import shutil
from pathlib import Path
from urllib.parse import urlsplit

from mkdocs.plugins import event_priority
from mkdocs.utils import log

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


def _scoped_search_tag(page) -> str:
    """<script> tag for the scoped-search hook, relative to the page depth."""
    depth = page.url.count("/")
    return f'<script src="{"../" * depth}javascripts/scoped-search.js"></script>'


def on_post_page(output, page, config):
    """Load the scoped-search hook before Material's bundle.

    The bundle requests the search index as soon as it runs, so a script loaded
    through `extra_javascript` (end of body) arrives too late and the shared
    index is already in memory. Injecting the tag as the first child of <head>
    puts it ahead of the bundle without forking the theme.
    """
    tag = _scoped_search_tag(page)
    head = output.find("<head")
    if head == -1:
        return output
    end = output.find(">", head)
    return output[: end + 1] + tag + output[end + 1 :]


def _split_search_index(site_dir, config):
    """Write one search index per language at the site root.

    mkdocs-static-i18n builds a separate index for each locale (the default one
    lands at the site root, the others under `<locale>/search/`), but Material
    always fetches `search/search_index.json` from the site root, so a search in
    one language competes with the pages of the others. Each build slices its
    own index by the first segment of every `location` and writes the slice at
    the site root, where `docs/javascripts/scoped-search.js` sends each locale.

    The shared index is left untouched on purpose: it is the fallback when a
    slice is missing, and rewriting it would make this hook destructive when it
    runs once per locale build.
    """
    index = site_dir / "search" / "search_index.json"
    if not index.is_file():
        return
    plugin = config["plugins"].get("i18n")
    if plugin is None:
        return
    locales = [lang.locale for lang in plugin.config.languages if lang.build]
    default = next(
        (lang.locale for lang in plugin.config.languages if lang.default), locales[0]
    )
    # The default locale builds into the site root; the rest build into
    # `<root>/<locale>/`, so the slices always go to the parent in that case.
    root = site_dir.parent if site_dir.name in locales else site_dir
    (root / "search").mkdir(parents=True, exist_ok=True)

    data = json.loads(index.read_text(encoding="utf-8"))
    docs = data.get("docs", [])
    slices = {locale: [] for locale in locales}
    for doc in docs:
        location = doc.get("location") or ""
        owner = next(
            (
                locale
                for locale in locales
                if locale != default and location.startswith(locale + "/")
            ),
            default,
        )
        slices[owner].append(doc)

    written = []
    for locale, entries in slices.items():
        if not entries:
            # Each locale build only sees its own pages, so the slices of the
            # other locales are written by their own build into this same
            # directory. Nothing to do here, and never overwrite a good slice.
            continue
        target = root / "search" / f"search_index.{locale}.json"
        target.write_text(
            json.dumps({**data, "docs": entries}, ensure_ascii=False),
            encoding="utf-8",
        )
        written.append(f"{locale}={len(entries)}")
    if written:
        log.info("scoped search index: %s", ", ".join(written))


def on_post_build(config):
    """
    Patch versioned-build quirks in the generated site. Only rewrites the
    sitemap when building under mike (see _version_prefix); plain root-hosted
    builds are left untouched.
    """
    site_dir = Path(config.site_dir)

    _split_search_index(site_dir, config)

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