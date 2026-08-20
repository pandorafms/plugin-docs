# Playwright

## Introduction

**Ver**. 02-08-2026

This document describes the functionality of the Playwright Discovery plugin (`pandorafms.playwright.1`) and its integration with PandoraFMS. The plugin runs a customer-provided Playwright `.ts` test inside a preconfigured Docker container, turning the result into transactional monitoring modules that plug into the console's WUX transactional view (global status/time, per-phase status/time, error screenshot, custom metrics, and an optional error-history module).

It is the Playwright counterpart of `pandorafms.selenium.4`, but built around Playwright's native execution model: the customer writes standard Playwright code — no custom library to import, no DSL to learn — and the plugin harvests everything from Playwright's own JSON reporter.

**Type**: Discovery plugin (`.disco`)

## Compatibility matrix

| **Systems where tested** | Rocky Linux 9/10 (Pandora server), Docker image `pandorafms/pandora_playwright:noble` (Ubuntu Noble) |
| --- | --- |
| **Systems where it works** | Any system that can run Docker as the local server, or reach a remote host over SSH that can run Docker |

## Pre requisites

**1. Docker**The machine that executes the test must have Docker available: the Discovery/Pandora server itself for `worker_mode = local`, or the SSH target for `worker_mode = remote`.

**2. The Playwright Docker image**`pandorafms/pandora_playwright:noble` must be available on the machine that runs the test (browsers preinstalled).

`docker pull pandorafms/pandora_playwright:noble` once published.

**3. SSH access (remote worker only)**For `worker_mode = remote`, an SSH user able to run Docker on the target host, plus a temporary folder writable by that user (default `/tmp`) to stage the test file.

**4. Tentacle (optional, CLI/standalone use)**If invoking the plugin outside the Discovery task pipeline with `--xml_mode`, a reachable `tentacle_serverd` is required to receive the generated agent XML.

## Parameters

**Discovery task wizard parameters**

| **Field** | **Macro** | **Notes** | **Default** |
| --- | --- | --- | --- |
| Worker mode | `_workerMode_` | `local` or `remote`. `remote` runs Docker on an SSH host. | `local` |
| Browser | `_browser_` | `chromium`, `firefox`, `webkit` | `chromium` |
| SSH address | `_sshAddress_` | Host that runs Docker (remote only) | — |
| SSH port | `_sshPort_` | — | `22` |
| SSH user | `_sshUser_` | Must be able to run Docker | `root` |
| SSH password | `_sshPassword_` | Encryptable via `password_encrypter.py` | — |
| Encrypt password | `_sshPasswordEncrypt_` | Obfuscates the password in the task config | on |
| Temporal folder | `_sshTemp_` | Where the test file is copied on the remote host | `/tmp` |
| Docker image | `_dockerImage_` | — | `pandorafms/pandora_playwright:noble` |
| Browser width | `_browserWidth_` | — | `1920` |
| Browser height | `_browserHeight_` | — | `1080` |
| Test timeout | `_globalTimeout_` | Per-test timeout, in **seconds** | `30` |
| Send full report | `_fullReport_` | Adds a verbose text report module | off |
| Report agent name | `_reportAgent_` | Agent that holds the full report; empty = first test's agent | — |
| Generate error history module | `_errorHistoryModule_` | Adds a synchronous string module per status/phase (`OK` or the error text), so Pandora keeps a historic value series of errors | off |
| Playwright test (.ts) | `_playwrightTest_` | The full test file content | — |

**Task configuration (JSON the runner receives)**

```json
{
  "worker_mode": "local",
  "browser": "chromium",
  "ssh_address": "", "ssh_port": "22", "ssh_user": "root",
  "ssh_password": "", "ssh_password_encrypt": "0", "ssh_temp_folder": "/tmp",
  "docker_image": "pandorafms/pandora_playwright:noble",
  "browser_width": "1920", "browser_height": "1080",
  "global_timeout": "30",
  "full_report": "0",
  "report_agent": "",
  "error_history_module": "0"
}

```

**CLI parameters (manual / standalone execution)**

| **Short** | **Long** | **Required** | **Default** | **Description** |
| --- | --- | --- | --- | --- |
| `-c` | `--conf` | yes | — | Path to the task configuration JSON |
| `-s` | `--test` | yes | — | Path to the Playwright `.ts` test file |
| `-t` | `--task` | yes | — | Task name (used to derive the container name) |
| `-i` | `--interval` | no | `300` | Agent interval (seconds) |
| `-g` | `--group` | no | `0` | Group id for the created agents |
| `-x` | `--xml_mode` | no | off | Build agent XML and send it via Tentacle (standalone mode) |
| `-S` | `--server` | no | `127.0.0.1:41121` | Tentacle `server:port` (with `-x`) |
| `-T` | `--temp` | no | `/tmp` | Temp folder for the XML (with `-x`) |
| `-v` | `--verbose` | no | off | Step-by-step trace to STDERR |

`password_encrypter -e -p <password>` encrypts a password; `-d` decrypts it (used by the console for the SSH password field).

## Manual execution

### Execution format

```
pandora_playwright -c <conf.json> -s <test.ts> -t <task_name> \
  [-i <interval>] [-g <group_id>] \
  [-x [-S <server:port>] [-T <temp_folder>]] \
  [-v]

```

- Without `-x`, the plugin prints Discovery JSON to STDOUT (native Discovery task mode).
- With `-x`, it builds agent XML and sends it via Tentacle directly (standalone/manual mode).

#### Examples

Native mode (JSON to STDOUT, as run by a Discovery task):

```bash
pandora_playwright -c conf.json -s task.spec.ts -t qa-test -g 0 -v

```

Standalone mode against a real Pandora server (creates real agents/modules via Tentacle):

```bash
pandora_playwright -x -S 127.0.0.1:41121 \
    -c conf.json -s task.spec.ts -t qa-console -g 2 -T /tmp

```

Remote worker (Docker runs over SSH; `worker_mode=remote` in `conf.json`):

```bash
pandora_playwright -c conf_remote.json -s task.spec.ts -t qa-remote -g 0 -v

```

#### Verbose mode

`-v` prints a timestamped, step-by-step trace to STDERR — useful for manual runs. It logs every Docker/SSH command verbatim (`$` local, `ssh$` remote), the config summary, report size, screenshot harvest, per-agent build, and emission summary:

```
Task <id>: worker=remote browser=chromium image=...:noble timeout=15s ...
Connecting SSH to 10.0.0.5:22 as root
SSH authenticated
SCP test.ts -> /tmp/<id>.spec.ts
ssh$ docker run -d --name <id> ...:noble sleep 300
ssh$ docker cp "/tmp/<id>.spec.ts" <id>:/pandora/task.spec.ts
ssh$ docker exec <id> sh -c 'cd /pandora && ... npx playwright test ... --reporter=json'
ssh$ docker exec <id> cat /tmp/report.json
Report retrieved (10744 bytes)
Screenshot harvested: .../test-failed-1.png (7416 b64 chars)
ssh$ docker rm -f <id>
Agent a...  [passing checkout]: PASS, 2 phases, 9 modules
Emitting monitoring_data: 2 agents

```

## Configuration in PandoraFMS

The plugin is delivered as a `.disco` Discovery package. To configure it:

**1. Install the `.disco` package**, if not already installed: go to **Discovery → Extension manager** and upload the package (or confirm it is already listed).

**2. Create a new Discovery task**: go to **Discovery → Applications → Playwright**.

**3. Fill in the wizard steps** (see [Parameters](#parameters) above):

- *Basic setup*: worker mode and browser.
- *Worker setup*: only shown when worker mode is `remote` — SSH connection details.
- *Test setup*: Docker image, browser size, timeout, `Send full report`, `Generate error history module`, and the Playwright test `.ts` content itself.

**4. Save the task.** On each execution, the plugin runs the test in Docker and reports one agent per Playwright `test(...)` found in the file.

**5. Open the resulting agent(s)** in the console. The **WUX transactional view** renders the phases derived from `test.step(...)`; standard module views show status, time, error screenshot, metrics, and (if enabled) the error-history modules.

## Agent and modules generated by the plugin

**One agent per Playwright `test(...)`.**

| **Module name** | **Type** | **Description** | **`extra_data`** |
| --- | --- | --- | --- |
| `Global status` | `generic_proc` | Overall test result: 1 if `passed`, 0 otherwise | `wux:global_status:<test>` |
| `Global time` | `generic_data` | Total test duration, in seconds | `wux:global_time:<test>` |
| `Phase <name> status` | `generic_proc` | Result of each `test.step`: 1 if it had no error, 0 otherwise | `wux:phase_status:<n>:<test>` |
| `Phase <name> time` | `generic_data` | Duration of each `test.step`, in seconds | `wux:phase_time:<n>:<test>` |
| `Last error screenshot` | `generic_data_string` | Screenshot on failure, as a `data:image/png;base64,...` value (renders as an image in the console) | `wux:error_screenshot:<test>` |
| `Global error` | `generic_data_string` | Only when `_errorHistoryModule_` is on. `OK` when the test passes, or the test's error text when it fails — a synchronous module, so Pandora keeps a real historic value series (not just the status module's description, which gets overwritten every run) | `wux:global_error:<test>` |
| `Phase <name> error` | `generic_data_string` | Only when `_errorHistoryModule_` is on. `OK` or the phase's error text, same history rationale as `Global error` | `wux:phase_error:<n>:<test>` |
| `metric name` | `generic_data` / `generic_data_string` | From a `pandora.metric` annotation (`name=value`, split on the first `=`); numeric values become `generic_data`, everything else `generic_data_string` | `pw:metric:<name>` |
| `Full report` | `async_string` | Only when `_fullReport_` is on. Verbose text report derived from the JSON reporter (status, steps, stdout/stderr, annotations, attachments) | `pw:full_report` |

The `wux:*` modules render in the console's WUX transactional view. `pw:*` modules are regular agent modules (metrics and the full report).

## Recording a transaction

A "transaction" is a standard Playwright test — no PandoraFMS import required. Three native constructs map to plugin behavior:

| You write | Becomes |
| --- | --- |
| `test.step('name', ...)` | a monitored **phase** (status + time) |
| `test.info().annotations.push({ type: 'pandora.metric', description: 'name=value' })` | a custom **metric** module |
| a failing assertion | the test fails; a **screenshot** is captured automatically |

### 1. Record the flow with Playwright's recorder (`codegen`)

Playwright ships its own recorder, `codegen`: it opens a real browser, and every click, fill, and navigation you perform is turned into Playwright code in real time, plus a Pick Locator / Explore mode to test selectors against the live page. Official documentation: **[playwright.dev/docs/codegen-intro](https://playwright.dev/docs/codegen-intro)**. General authoring reference: **[playwright.dev/docs/writing-tests](https://playwright.dev/docs/writing-tests)**.

On any machine with Node and Playwright installed (this does not need to be the plugin's Docker image):

```bash
npm init playwright@latest    # first time only, if the project isn't set up yet
npx playwright codegen https://your-app.example.com

```

Two windows open: the browser you interact with, and the **Playwright Inspector**, which shows the generated code live and lets you pick/copy a locator for any element on the page. Useful flags:

- `--browser=firefox` / `--browser=webkit` — record against a specific engine (matches the plugin's `_browser_` setting).
- `--viewport-size=1920,1080` — record at the same resolution the plugin will run (matches `_browserWidth_`/`_browserHeight_`).
- `--save-storage=state.json` — capture cookies/localStorage after an interactive login, to seed later authenticated recordings with `--load-storage=state.json` (see [Authentication](https://playwright.dev/docs/auth) in the official docs if the flow needs a persisted session).

`codegen` output is **flat, ungrouped code** — clicks and assertions one after another, with no `test.step(...)` and no metric annotations. It is a starting point, not the final transaction: copy it into your `.ts` file and go to step 2.

### 2. Turn it into phases

Wrap each meaningful part of the recorded flow in `test.step('name', async () => { ... })`. Every **top-level** `test.step` call — one written directly inside the `test(...)` callback — becomes one phase, with its own `Phase <name> status` and `Phase <name> time` module (see [Agent and modules generated by the plugin](#agent-and-modules-generated-by-the-plugin)). Official reference: **[test.step() API](https://playwright.dev/docs/api/class-test#test-step)**.

```typescript
await test.step('open home', async () => {
  await page.goto('https://your-app.example.com');
  await expect(page).toHaveTitle(/Shop/);
});

```

Things to know:

- **Only top-level steps become phases.** A `test.step(...)` nested *inside* another `test.step(...)` is not reported as a separate phase — the plugin only reads the test's own top-level `steps` array from Playwright's JSON reporter. Keep steps flat (one level) for anything you want to see as an independent phase in the console.
- **Assertions belong inside the step**, not after it — `expect(...)` must run while the step is still open so a failure is attributed to that phase (and captured in its status/description), not to a later one or to the test as a whole.
- **A phase with no assertion is only a timing box.** `test.step('open home', async () => { await page.goto(...); })` with no `expect` will basically always report `status = 1`, since Playwright only marks a step failed when something inside it throws. Add at least one assertion per phase you actually want monitored, not just timed.
- **Ordering and duration**: the phase order in the console matches the order the steps run in; `Phase <name> time` is that step's own wall-clock duration, not cumulative.

### 3. Add custom metrics

Push a `pandora.metric` annotation with `test.info()` — from anywhere in the test body, including inside a `test.step`:

```typescript
const count = await page.locator('.cart-count').innerText();
test.info().annotations.push({ type: 'pandora.metric', description: `cart_items=${count}` });

```

Official reference for annotations: **[test.info().annotations](https://playwright.dev/docs/api/class-testinfo#test-info-annotations)**.

Parsing rules (exact, from the runner):

- `type` must be the literal string `pandora.metric`; anything else is ignored.
- `description` must be `name=value`, split on the **first** `=` only — so a value containing `=` (e.g. a URL query string) is not truncated.
- `name` and `value` are trimmed of surrounding whitespace. If `description` has no `=`, or `name` is empty after trimming, that annotation is silently skipped — no module, no error.
- The module type is inferred from `value`: parses as a number → `generic_data`; anything else → `generic_data_string`.
- The module is named exactly `name` and tagged `extra_data = pw:metric:<name>`.
- Push **one annotation per metric name per test run.** The annotation list is not deduplicated — pushing the same name twice in one run queues two modules with the same name/`extra_data`, which is redundant at best and ambiguous for Pandora to reconcile at worst.

### Full example

```typescript
import { test, expect } from '@playwright/test';

test('checkout flow', async ({ page }) => {
  await test.step('open home', async () => {
    await page.goto('https://your-app.example.com');
    await expect(page).toHaveTitle(/Shop/);
  });

  await test.step('login', async () => {
    await page.fill('#user', 'demo');
    await page.fill('#password', 'demo');
    await page.click('#submit');
    await expect(page.locator('.dashboard')).toBeVisible();
  });

  await test.step('add to cart', async () => {
    await page.click('text=Add to cart');
    const count = await page.locator('.cart-count').innerText();
    test.info().annotations.push({ type: 'pandora.metric', description: `cart_items=${count}` });
  });
});

```

### Notes

- **Naming**: module names come from `test.step` titles — keep them descriptive. Renaming a test starts a new agent.
- **Continue after a failure**: a normal `expect` aborts the test on failure, so later phases do not run at all (they simply don't appear in that run). Use `expect.soft(locator)` if every phase must be measured even when one fails.
- **Multiple transactions**: several `test(...)` blocks in one `.ts` file produce several agents.
- Instead of hand-writing or manually recording the transaction, it can also be generated end-to-end by an AI coding agent that drives a real browser (via a Playwright/browser-automation tool) to validate every locator against the live target before handing over the file — catching ambiguous or strict-mode-violating selectors that plain `codegen` cannot.

## Generating tests with an AI agent

Instead of hand-writing the `.ts` transaction, or recording it once with `codegen` and hoping the selectors hold, a local coding agent — Claude Code, Codex, or similar — can drive a real browser through the flow and write the transaction for you, validating every locator against the live target before handing it over. This catches exactly the class of bug that makes a transaction flaky in production (duplicate status badges, ambiguous `hasText` filters, a CSS-only visual match that isn't really unique in the DOM) — things plain `codegen` cannot, because it only records literal actions without checking whether the resulting locator is actually unique.

### 1. Install a Playwright browser-automation capability

The agent needs a tool that can open a real browser and drive it (click, fill, read the DOM), not just guess from a screenshot. The standard way is the official Playwright MCP server, `@playwright/mcp` (by Microsoft) — it exposes browser control as MCP tools to any MCP-compatible agent.

**Claude Code**:

```bash
claude mcp add playwright -- npx @playwright/mcp@latest

```

(Anthropic's official plugin marketplace also ships a ready-made "playwright" plugin that wires this same MCP server — either path works.)

**Codex CLI**:

```bash
codex mcp add playwright -- npx @playwright/mcp@latest

```

Both commands register the server for stdio use; `npx` fetches `@playwright/mcp` on first run. This needs Node available on the machine running the agent — not the plugin's Docker image, since this step happens locally, before the test file even exists.

### 2. Prompt template

```
Validate [FLOW NAME] on [URL] and write it as a Playwright transaction for the
pandorafms.playwright.1 plugin.

What the transaction should check:
- [step 1, e.g. "open the page and confirm the title"]
- [step 2, e.g. "log in and confirm the dashboard loads"]
- [step 3, e.g. "read a value and publish it as a pandora.metric"]

Deliverable:
- Plain Playwright: wrap each meaningful step in a top-level `test.step('name', ...)`
  so it becomes a monitored phase, and use
  `test.info().annotations.push({ type: 'pandora.metric', description: 'name=value' })`
  for anything that should become a custom metric module.
- No PandoraFMS import, no DSL — this plugin harvests everything from
  Playwright's own JSON reporter.
- Validate every locator against the real target yourself (drive the browser,
  don't just infer from a snapshot) before handing me the file — fix anything
  ambiguous or strict-mode-violating first.
- If a later step depends on a hard assertion in an earlier step, tell me
  whether to keep it that way or switch to `expect.soft()` so every phase gets
  measured even when one fails.

```

### 3. After you get the file

Run it through the plugin locally before wiring it into a Discovery task — see [Manual execution](#manual-execution) above — so you see the real agent/module output, not just "the test passed."

## Self-signed certificates

By default Playwright validates TLS certificates like a real browser, so a target using a self-signed or internally-issued certificate makes every `page.goto(...)` fail with `net::ERR_CERT_AUTHORITY_INVALID` before the test logic even runs.

There is no plugin-level toggle for this — it is set explicitly in the transaction with Playwright's own `test.use()`:

```typescript
import { test, expect } from '@playwright/test';

test.use({ ignoreHTTPSErrors: true });

test('checkout flow', async ({ page }) => {
  await page.goto('https://internal.example.com');
  // ...
});

```

- `test.use({ ignoreHTTPSErrors: true })` at the top level of the file applies to every `test(...)` below it.
- To scope it to only some tests in the same file, wrap them in their own `test.describe(...)` block and call `test.use({ ignoreHTTPSErrors: true })` as the first line inside that block instead of at the top level.
- This only disables **certificate validation**, not TLS itself — the connection stays encrypted, it just no longer requires a trusted CA chain.

## Debugging and Troubleshooting

### Debugging a test

When a transaction fails and the screenshot/`Full report` isn't enough, run the test interactively inside the same image the plugin uses, with Playwright's HTML report (trace + failure video) served from the container. The image ships `playwright.config.debug.ts` (in `/pandora`) preconfigured with `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`, and an HTML reporter bound to `0.0.0.0:9323`.

```bash
docker run -it --rm \
  -v "$(pwd)/test.spec.ts:/pandora/test.spec.ts" \
  -p 9323:9323 \
  pandorafms/pandora_playwright:noble bash

# inside the container:
npx playwright test test.spec.ts --config=playwright.config.debug.ts --browser=chromium --timeout=30000
npx playwright show-report --host 0.0.0.0 --port 9323

```

With `-p 9323:9323` published, open `http://localhost:9323` on the host to browse the report: per-step results, the trace viewer, and the video of the failure.

### Troubleshooting

- **"Playwright produced no report"** — the test failed to run (syntax error, bad import, missing browser). Run with `-v` and read the `docker exec` stderr.
- **Screenshot shows as text, not an image** — the value must be `generic_data_string` with a `data:image/png;base64,` prefix; check the plugin build includes this.
- **`Cannot find module '@playwright/test'`** — the test must run from `/pandora` inside the image so Node resolves `node_modules`; the plugin copies it to `/pandora/task.spec.ts` for this reason.
- **Agents land in the wrong group (standalone `-x` mode)** — Pandora agent XML expects the group **name**, not the numeric id. The Discovery `monitoring_data` path uses the numeric `id_group` correctly.
- **A later phase still shows "ok" after an earlier failure** — a failed hard assertion aborts the run, so later phases keep their previous value. Use `expect.soft()` if every phase must be measured on every run.
- **`net::ERR_CERT_AUTHORITY_INVALID`** — see [Self-signed certificates](#self-signed-certificates).