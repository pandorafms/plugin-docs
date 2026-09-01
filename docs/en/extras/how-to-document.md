# How to document

Reference for anyone writing or migrating documentation into this site:
where new content goes, what each page type must cover, and the mechanics
of adding pages, sections, and images.

## How to contribute

All the documentation lives in the
[plugin-docs repository](https://github.com/pandorafms/plugin-docs). To
contribute:

1. Make your changes in a branch (or fork) and open a pull request (PR)
   against the repository. The PR form is pre-filled from the repository's
   PR template (`.github/PULL_REQUEST_TEMPLATE.md`): type of change,
   affected section, language coverage, and local build verification.
2. An administrator verifies the PR and, once everything checks out,
   approves and merges it.

The official documentation is published at
<https://pandorafms.com/docs/integrations/> and is synchronized
periodically with the `main` branch of the repository, so merged changes
reach the live site automatically.

## Where does new content go?

| Section | What belongs here | Example |
| --- | --- | --- |
| **Discovery** | Plugins that integrate with Pandora's *Discovery* task wizard: the console creates a task, runs the plugin, and auto-generates agents/modules from its output. | NGINX, Playwright |
| **Integrations** | Connectors to external communication/collaboration tools, used mainly for alerting (the "send a Pandora alert to X" pattern: configure the external service, then create a Pandora alert command/action). | Telegram, Google Chat, Microsoft Teams |
| **Plugins** | Standalone/manual plugins that are *not* driven by the Discovery wizard — run manually or wired as a regular server plugin, without auto-generated Discovery tasks. | Oculix, Logparser (Advanced Log Parser) |
| **Extras** | Meta content about the site itself: this page, contributor notes, anything that isn't product documentation. | This page |

If a plugin could arguably fit two sections (e.g. it has both a Discovery
task and a manual CLI mode), classify it by its *primary*, documented usage
path — don't duplicate the same content in two sections.

## Required sections per content type

Every page starts with a single `# Title` (this becomes both the sidebar
label and the page `<title>`), followed by the article's last-updated
line and the sections below.

### The reading order is a contract

Whatever the content type, a page walks the reader through the same
journey:

**Overview → Prepare → Configure → Verify → Understand → Troubleshoot → Reference**

The point is progressive disclosure: the reader has to be able to
install, configure and confirm the integration *before* meeting
exhaustive detail. The exhaustive parameter reference goes at the end —
it is what a reader comes back to, not what they read first.

Three rules follow from that:

- **Never reorder the stages to fit the content you already have.** When
  you update or migrate an existing page, realign it to this order; do
  not inherit the order of the older page.
- **Omit a stage that does not apply** instead of emitting an empty
  heading. What is flexible is *which* stages appear and what you call
  them — never the order of the ones that do.
- **English and Spanish must use the same section order.** If the
  existing pair diverges, align both in the same change.

If a section fits none of the stages, or you cannot tell where it goes,
ask before publishing. Do not invent a position, do not drop the
section, and do not leave it where the old page happened to have it.

### Discovery plugins

1. **Overview / What it monitors** — the target, what is collected, what
   the plugin produces, and the Discovery task model.
2. **Prepare** — validated environment and compatibility, prerequisites,
   permissions, target-side setup, and installation.
3. **Configure the Discovery task** — the wizard fields and task
   behaviour, with screenshots where they remove real ambiguity.
4. **Verify** — a successful run, the task summary, the expected agents
   and representative modules.
5. **Understand the results** — agent identity and cardinality, plus a
   functional summary of the module groups.
6. **Troubleshoot** — evidenced failure signals and diagnostics.
7. **Reference** — exhaustive parameters, grouped by input surface
   (console, configuration file, CLI, environment), and the full module
   inventory.

Add an **Operate** stage before Troubleshoot when the plugin has a real
day-to-day surface — manual execution, timeouts, debug modes, custom
runtimes. The Playwright page is the worked example.

Put a short functional summary before any long inventory, and group a
large reference by resource, generated agent, or condition.

### Plugins (agent, server or standalone)

Same journey, with the integration path as the variable:

1. **Overview / What it does** — purpose, execution model, input, output.
2. **Prepare** — prerequisites, installation, dependencies, permissions,
   compatibility.
3. **Configure** — the agent configuration, the server plugin
   registration and module setup, or the standalone configuration,
   whichever the plugin actually supports.
4. **Verify** — expected output, a successful execution, and ingestion
   into Pandora FMS where applicable.
5. **Understand the results** — functional summary first, detailed
   output later.
6. **Operate and troubleshoot** — manual execution, verbose mode,
   limitations, diagnostics.
7. **Reference** — parameters by surface and exhaustive outputs.

Do not write a separate template per plugin subtype, and do not let a
documented manual run imply agent- or server-plugin support.

### Integrations (notifications and external services)

1. **Overview / What it does** — the destination, what is sent, and the
   outcome for the operator.
2. **Prepare the external service** — the steps performed *in the
   external tool* (create a bot, a webhook, a channel...), with
   screenshots. Usually the bulk of the page. Omit it for built-in
   workflows that need nothing there.
3. **Configure Pandora FMS** — the built-in integration, or the alert
   command and the alert action that uses it, with console screenshots.
4. **Verify** — a safe test procedure and the expected result at both
   ends.
5. **Understand the integration** — verified flow, payload behaviour or
   delivery constraints, when they help.
6. **Troubleshoot** — evidenced errors, logs and recovery checks.
7. **Reference** — parameters by surface and any relevant limits.

## Adding a page to an existing section

1. Create a markdown file under `docs/en/<section>/<page>.md` (and its
   `docs/es/<section>/<page>.md` translation, if ready).
2. Start the file with a `# Title` — that's what shows up in the sidebar,
   not the filename.
3. Commit and push. The sidebar picks it up automatically, no `mkdocs.yml`
   edit needed.

## Adding a new section or page

The top-level sections are **Plugins**, **Integrations**, **Discovery**,
and **Extras** (`docs/en/plugins/`, `docs/en/integrations/`,
`docs/en/discovery/`, `docs/en/extras/` — mirrored under `docs/es/`). The
sidebar is generated from this folder structure by
`mkdocs-awesome-pages-plugin` — there's no `nav:` list to maintain by hand
for individual pages.

Top-level section *order*, however, needs a bit more than a `.pages` file:
`mkdocs-static-i18n` always alpha-sorts the top-level nav when it builds
each language's tree, which would silently undo any custom order set via
`.pages`. `hooks.py` (registered in `mkdocs.yml`'s `hooks:` key) runs after
that sort and pins specific section titles to the end — currently just
`Extras`. Any *other* top-level section is left in whatever order
`mkdocs-static-i18n` alphabetized it into; if you need a different fixed
position for a new section, add its title to `PINNED_LAST` in `hooks.py`
(order in that list is the order they'll appear in, all pinned after the
alphabetized ones).

To add a **new top-level section** (e.g. "Dashboards"):

1. Create `docs/en/dashboards/` (and `docs/es/dashboards/`).
2. Add a `.pages` file inside it to set the section title:
   ```yaml
   title: Dashboards
   ```
3. Add at least one `.md` page inside the new folder.
4. It will appear in the sidebar automatically, alphabetized among the
   other non-pinned sections. No `.pages` or `hooks.py` edit required
   unless you specifically need it pinned to a fixed position (see above).

To add a **subcategory** inside an existing section (e.g. group plugins by
"Monitoring" / "Network"), just nest another folder with its own `.pages`:

```
docs/en/plugins/
  example.md
  monitoring/
    .pages           # title: Monitoring
    cpu.md
    memory.md
```

No depth limit — folders inside folders become nested sidebar sections.

## Menu translations

Nothing needs to be translated besides the content: the title shown in the
menu is each page's `# H1`, so it's enough for
`docs/es/<section>/<page>.md` to have its own Spanish title. Section
`.pages` files (`title:`) are translated the same way, by duplicating the
file under `docs/es/` with the corresponding text.

## Adding an image

Images live under `docs/<lang>/assets/images/<section>/<plugin-slug>/`, one
subfolder per plugin/integration — never loose in `assets/images/` directly.
This keeps screenshots from different plugins from colliding on filenames
(BookStack exports things like `image.png` or `nU2image.png`, which are not
unique across plugins) and makes it obvious what a folder belongs to.

Example, following the pattern already used by the Telegram integration:

```
docs/en/assets/images/integrations/telegram/
  nU2image.png
  Qe2image.png
  ...
docs/es/assets/images/integrations/telegram/
  Milimage.png        # ES-only image (see fallback note below)
```

1. Create `docs/<lang>/assets/images/<section>/<plugin-slug>/` (matching the
   page's section — `plugins`, `integrations`, or `discovery`) and drop the
   file there (`git add` or the GitLab/GitHub Web IDE drag & drop).
2. Reference it from markdown with a path relative to the current page. From
   a page inside a section folder (the common case, e.g.
   `integrations/telegram.md`), that's
   `../assets/images/<section>/<plugin-slug>/my-file.png`. From a root-level
   page like `index.md` (no section folder), drop the leading `../`.
3. Per-language images: if a screenshot only differs from the other
   language's version (e.g. because it shows localized UI text), add it
   under `docs/es/assets/images/<section>/<plugin-slug>/` with the same
   filename to override it — `fallback_to_default: true` means any file
   *not* overridden there is served automatically from the `en` folder, so
   you only need to add the images that actually differ.
4. Images are centered and open in a lightbox on click automatically
   (`mkdocs-glightbox` + the centering rule in `stylesheets/extra.css`) —
   no extra markup needed, a plain `![alt](path)` is enough.

## Local preview

**Python:**

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve
```

**Docker (no local Python needed):**

```bash
UID=$(id -u) GID=$(id -g) docker compose up
```

Both open `http://localhost:8000` with live reload — edits to any `.md` or
image refresh the browser automatically.

## Validation

Run the automated checks before opening a pull request:

```bash
python3 -m unittest discover -s tests -p 'test_validate_docs.py'
python3 scripts/validate_docs.py --fail-on blocking
.venv/bin/mkdocs build --strict
```

Blocking gates cover language path parity, one real H1 per page, existing local
images with Spanish-to-English fallback, and high-confidence secret signatures.
The validator also reports local link and anchor problems, cross-language links,
legacy URLs, pending markers, rendered `PandoraFMS` usage, and known content
contamination signatures. Report-only findings remain visible but do not fail the
default command. Use `--fail-on all` to treat every finding as a local failure.

A browser preview is useful for visual review, but it does not replace these
checks.
