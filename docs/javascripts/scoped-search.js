/*
 * Scope the site search to the language being read.
 *
 * mkdocs-static-i18n builds a separate index per locale but Material always
 * requests `search/search_index.json` from the site root, so every language
 * searches the whole site: a query in Spanish returns the English pages and
 * the other way round.
 *
 * `scripts/hooks.py` writes one slice per language next to the shared index
 * (`search/search_index.<locale>.json`); this script rewrites the request to
 * the slice of the current `<html lang>`. Material loads the index with
 * XMLHttpRequest rather than fetch, so the hook goes on `open()`, which runs
 * before the response is requested.
 */
(function () {
  var shared = "search/search_index.json";
  var lang = document.documentElement.lang || "en";
  var scoped = "search/search_index." + lang + ".json";
  var open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    if (url && String(url).indexOf(shared) !== -1) {
      var args = Array.prototype.slice.call(arguments);
      args[1] = String(url).replace(shared, scoped);
      return open.apply(this, args);
    }
    return open.apply(this, arguments);
  };
})();
