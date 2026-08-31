# Playwright

## Introduction

**Ver**. 31-08-2026

This document describes the Playwright Discovery plugin (`pandorafms.playwright.1`) and its integration with PandoraFMS. The plugin provides synthetic web monitoring with [Playwright](https://playwright.dev/): you supply a single Playwright `.ts` test, the plugin runs it inside a preconfigured Docker container (locally or on a remote host over SSH) and turns the result into PandoraFMS monitoring modules that plug into the console's WUX transactional view (global status/time, per-phase status/time, error screenshot, custom metrics).

The execution model is built around Playwright's native behavior:

1. The Discovery task (or a manual CLI run) launches a Docker container from the Playwright image (`pandorafms/pandora_playwright:noble`).
2. The `.ts` test is copied into the container and executed with `npx playwright test --reporter=json`.
3. The plugin reads the JSON reporter and builds **one agent per Playwright `test(...)`**, with modules for the overall status/time, each `test.step` as a phase, an error screenshot on failure, and any custom metrics.
4. Results are returned as Discovery monitoring data, or (with `-x`) sent as agent XML via Tentacle.

It is the Playwright counterpart of `pandorafms.selenium.4`, but there is **no custom library to import and no DSL to learn**: you write standard Playwright code and the plugin harvests everything from Playwright's JSON reporter. Execution is always in Docker; with `worker_mode = remote` the container runs on a remote host reached over SSH.

**Type**: Discovery plugin (`.disco`). The app short name is `pandorafms.playwright.1` (`id_app = 10`) and `discovery_definition.ini` declares `version = "1.0"`.

## Compatibility matrix

| **Systems where tested** | Playwright runtime **1.62.0** on Node 24; Docker image `pandorafms/pandora_playwright:noble` (based on `mcr.microsoft.com/playwright:v1.62.0-noble`, Ubuntu 24.04, browsers preinstalled); browsers Chromium, Mozilla Firefox and WebKit (plugin `_browser_` option); worker mode `local`; worker mode `remote` (SSH host); PandoraFMS console WUX transactional view (end-to-end QA run against a real Pandora server's Tentacle) |
| --- | --- |
| **Systems where it works** | Any system that can run Docker as the **local** worker, or reach over SSH a host that can run Docker as a **remote** worker. **Not established**: a per-version PandoraFMS server compatibility matrix (no per-version records exist), and the Docker host operating system (the image is Ubuntu 24.04 based and the host OS used in testing was Linux) |

## Prerequisites

1. **Docker** on the machine that runs the test: the Discovery server itself for `worker_mode = local`, or the SSH target for `worker_mode = remote`.
2. **The Playwright Docker image** `pandorafms/pandora_playwright:noble` available on that machine (browsers preinstalled), pulled from the registry:

   ```bash
   docker pull pandorafms/pandora_playwright:noble
   ```

   This is the recommended way to get it. What the image contains, and how to build or customize it yourself, is in [The Docker image](#the-docker-image).
3. **PandoraFMS**: a Discovery server enabled (`discoveryserver 1` in `pandora_server.conf`) to execute tasks, and the console to define them.
4. **Remote worker only** (`worker_mode = remote`): an SSH account that can run Docker on the remote host (address, port, user, and password or encrypted password).
5. **Manual CLI runs only** (outside a packaged install): Python 3 with the runner dependencies:

   ```bash
   python3 -m venv venv
   ./venv/bin/pip install "chardet<6" paramiko scp pycryptodome pandoraPlugintools-basic
   ```

## Parameters

These map to the Discovery task form (console) and to the JSON task configuration the runner receives. The console presents them in **four wizard steps** that match the `[config_steps]` sections of `discovery_definition.ini`: Basic setup, Worker setup (only for `remote`), Test setup and Advanced setup.

### Basic setup

| Field | Macro | Values | Default | Notes |
|-------|-------|--------|---------|-------|
| Worker mode | `_workerMode_` | `local`, `remote` | `local` | `remote` runs Docker on an SSH host |
| Browser | `_browser_` | `chromium`, `firefox`, `webkit` | `chromium` | |

### Worker setup (only shown for `remote`)

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| SSH address | `_sshAddress_` | string | — | Host that runs Docker |
| SSH port | `_sshPort_` | number | `22` | |
| SSH user | `_sshUser_` | string | `root` | Must be able to run Docker |
| SSH password | `_sshPassword_` | password | — | Encryptable |
| Encrypt password | `_sshPasswordEncrypt_` | checkbox | on | Obfuscates the password in the task config |
| Temporal folder | `_sshTemp_` | string | `/tmp` | Where the test file is copied on the host |

### Test setup

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Docker image | `_dockerImage_` | string | `pandorafms/pandora_playwright:noble` | |
| Browser width | `_browserWidth_` | number | `1920` | Viewport width in pixels, applied through the generated config, since `viewport` has no command-line flag. A non-positive value falls back to the default |
| Browser height | `_browserHeight_` | number | `1080` | Viewport height in pixels, same mechanism as the width |
| Test timeout | `_globalTimeout_` | number | `120` | Overall timeout in **seconds** for each test: the budget of a whole `test(...)`, not per step and not per task. For the per-step ones see **Advanced timeouts** and [Timeouts](#timeouts) |
| Send full report | `_fullReport_` | checkbox | off | Adds a verbose text report module |
| Full report agent name | `_reportAgent_` | string | — | Agent that holds the full report; empty = first test's agent. Only shown when **Send full report** is checked |
| Prefix for agents created | `_prefixAgents_` | string | — | Optional. Prepended before the test title when deriving the agent name and alias, so two tasks running a test of the same title do not share one agent. Empty keeps the original naming (and existing agents) untouched |
| Playwright test (.ts) | `_playwrightTest_` | textarea | — | The full test file content |
| Generate error history module | `_errorHistoryModule_` | checkbox | off | Adds a synchronous string module per status/phase (`OK` or the error text), so Pandora keeps a historic value series of errors |

### Advanced setup

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Debug mode | `_debug_` | checkbox | off | Runs the test with Playwright's debug config (trace, screenshot, video) and leaves the artifacts on the debug directory |
| Debug directory | `_debugDirectory_` | string | `/var/spool/pandora/data_in/discovery/tmp/playwright/_taskid_` | **Absolute path** on the machine that actually runs Docker — the local Discovery server for `worker_mode = local`, or the remote SSH host for `worker_mode = remote` — **not** on this console. Docker rejects a relative bind-mount path outright, so the runner validates that the path is absolute and fails fast if it isn't. Required when Debug mode is enabled (the console form cannot express a conditionally-mandatory field, so the runner validates it too). The `_taskid_` placeholder is substituted at runtime by the plugin — it is **not** a real Discovery macro, only recognized inside this field — with the same `md5(id_rt)` value Discovery already computes internally as `__taskMD5__`, so any other tool can recompute it from the task's `id_rt` to locate the matching debug output. Replace it with a fixed absolute path to reuse the same folder across runs of a different task |
| Advanced timeouts | `_advancedTimeouts_` | checkbox | off | Exposes Playwright's three per-step timeouts, which have no command-line flag. When enabled, the three values below are added to the generated config. **The test file is never modified.** See [Timeouts](#timeouts) |
| Action timeout | `_actionTimeout_` | number | `0` | Seconds for each action (`click`, `fill`, `press`, `check`, `selectOption`...). `0` = no limit, Playwright's default. Only shown when **Advanced timeouts** is checked |
| Navigation timeout | `_navigationTimeout_` | number | `0` | Seconds for each navigation (`goto`, `waitForURL`, `waitForNavigation`, `reload`). `0` = no limit, Playwright's default. Only shown when **Advanced timeouts** is checked |
| Expect timeout | `_expectTimeout_` | number | `5` | Seconds for each web-first assertion (`expect(locator).toBeVisible()`, `toHaveText`...). Playwright's default is `5`; `0` = no limit. Only shown when **Advanced timeouts** is checked |
| Remove existing container with the same task name | `_overrideContainer_` | checkbox | off | The runner always starts the test container with `--rm`, so a container orphaned by an interrupted run deletes itself when its `sleep` ends and frees the task name. When enabled, the runner additionally removes (`docker rm -f`) any container that already holds this task's derived name before starting, so a leftover cannot block the next execution with a Docker "name already in use" error. Only enable it if you hit that error: if the same task is ever launched twice at the same time, this removes the other running instance too |

### Task configuration JSON (what the runner reads)

```json
{
  "worker_mode": "local",
  "browser": "chromium",
  "ssh_address": "", "ssh_port": "22", "ssh_user": "root",
  "ssh_password": "", "ssh_password_encrypt": "0", "ssh_temp_folder": "/tmp",
  "docker_image": "pandorafms/pandora_playwright:noble",
  "browser_width": "1920", "browser_height": "1080",
  "global_timeout": "120",
  "full_report": "0",
  "report_agent": "",
  "agent_prefix": "",
  "error_history_module": "0",
  "override_container": "0",
  "advanced_timeouts": "0",
  "action_timeout": "0", "navigation_timeout": "0", "expect_timeout": "5",
  "debug": "0",
  "debug_directory": ""
}
```

The template lives in the `[tempfile_confs]` section of `discovery_definition.ini`; every macro of the form `_xxx_` is substituted from the task's stored values. The SSH password can be stored encrypted: the console calls `password_encrypter.py` (AES-256-CBC) when `_sshPasswordEncrypt_` is on. From the CLI, `password_encrypter.py -e -p <password>` encrypts a password and `password_encrypter.py -d -p <password>` decrypts it.

## Manual execution

The runner entrypoint is `pandora_playwright.py`. A manual run reproduces what the Discovery server does per task execution, but without an `id_rt`: it derives the Docker container name from the `-t` task name (hashing it when it is not already an md5) instead of using `md5(id_rt)`.

### Execution format

```
pandora_playwright.py -c <conf.json> -s <test.ts> -t <task_name> [options]
```

| Option | Long | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-c` | `--conf` | yes | — | Path to the task configuration JSON |
| `-s` | `--test` | yes | — | Path to the Playwright `.ts` test file |
| `-t` | `--task` | yes | — | Task name (used to derive the container name) |
| `-i` | `--interval` | no | `300` | Agent interval (seconds) |
| `-g` | `--group` | no | `0` | Group id for the created agents |
| `-x` | `--xml_mode` | no | off | Build agent XML and send it via Tentacle |
| `-S` | `--server` | no | `127.0.0.1:41121` | Tentacle `server:port` (with `-x`) |
| `-T` | `--temp` | no | `/tmp` | Temp folder for the XML (with `-x`) |
| `-v` | `--verbose` | no | off | Step-by-step trace to STDERR |

`password_encrypter.py` supports `-e/--encrypt`, `-d/--decrypt` and `-p/--password <password>` (`-e` and `-d` are mutually exclusive).

#### Examples

Local run with a test and a matching config:

```bash
./venv/bin/python pandora_playwright.py -c conf.json -s sample.spec.ts -t qa-test -g 0
```

Remote run over SSH (config points `worker_mode` at `remote`):

```bash
./venv/bin/python pandora_playwright.py -c conf_remote.json -s sample.spec.ts -t qa-remote -g 0
```

End-to-end against a Pandora server's Tentacle (creates real agents/modules):

```bash
./venv/bin/python pandora_playwright.py -x -S 127.0.0.1:41121 \
    -c conf.json -s sample.spec.ts -t qa-console -g 13 -T /tmp
```

Encrypt a password for the remote-worker config:

```bash
./venv/bin/python password_encrypter.py -e -p <password>
```

#### Verbose mode

`-v` prints a timestamped, step-by-step trace to STDERR — useful for manual runs. It logs every Docker/SSH command verbatim (`$` local, `ssh$` remote) plus the config summary, report size, screenshot harvest, per-agent build, full-report size and emission. Example (remote):

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

The plugin is installed in the Discovery plugin store. There are **two copies** on disk:

- `<homedir>/attachment/discovery/pandorafms.playwright.1/` — used by the console for the task form.
- `<remote_config>/discovery/pandorafms.playwright.1/`, usually `/var/spool/pandora/data_in/discovery/pandorafms.playwright.1/` — **the copy the Discovery server executes**.

Updating only the first copy silently keeps the old binary running on the Discovery server.

A task is created in the console as a Discovery task of the **Playwright** app (`pandorafms.playwright.1`, `id_app = 10`):

1. Go to **Discovery → Tasks → New task**, pick the Playwright app and set the task name, group, server and interval.
2. Walk the wizard steps: **Basic setup** (worker mode, browser), **Worker setup** (only for `remote`), **Test setup** (image, viewport, timeout, full report, agent prefix, the Playwright test itself, error history module) and **Advanced setup** (debug mode, debug directory, advanced timeouts, remove existing container).
3. Paste the full `.ts` into the **Playwright test (.ts)** field, pick the browser and worker mode, and save.

<!-- SCREENSHOT NEEDED: PandoraFMS Discovery task wizard for the Playwright app (pandorafms.playwright.1): the four steps of the task form — Basic setup (Worker mode, Browser), Worker setup (SSH fields), Test setup (Docker image, viewport, Test timeout, full report, agent prefix, Playwright test .ts, error history module) and Advanced setup (Debug mode, Debug directory, Advanced timeouts, Remove existing container). Image goes at ../assets/images/discovery/playwright/task-wizard.png -->

At execution time the Discovery server invokes the plugin with the command defined in `exec[]` of `discovery_definition.ini`, substituting the task macros:

```
'_exec1_' -c '_tempfileConf_' -s '_tempfileTest_' -t __taskMD5__ -i __taskInterval__ -g __taskGroupID__
```

`_tempfileConf_` expands to the task configuration JSON shown in [Parameters](#parameters) and `_tempfileTest_` to the test file content. `__taskMD5__` is `md5(id_rt)`.

## Agent and modules generated by the plugin

**One agent per Playwright `test(...)`.** The agent name is `a + md5(<agent prefix> + <full title>)`, where the full title is the `describe > test` path and the prefix is the optional `_prefixAgents_` field (empty by default). It does **not** depend on the task, so deleting and recreating the task reports to the same agent and keeps history.

That task independence has a flip side: **two tasks running a test of the same title report to the same agent**, alternating their data on the same modules. When that is not what you want — typically the same transaction pointed at two environments — give each task its own `_prefixAgents_` (for example `prod-`, `dev-`) to split them into separate agents. Leaving it empty reproduces the original naming exactly, so existing agents are never orphaned by an upgrade.

| Module | Type | Source | `extra_data` |
|--------|------|--------|--------------|
| `Global status` | `generic_proc` | test result (`passed` → 1) | `wux:global_status:<test>` |
| `Global time` | `generic_data` (s) | test duration | `wux:global_time:<test>` |
| `Phase <name> status` | `generic_proc` | each `test.step` | `wux:phase_status:<n>:<test>` |
| `Phase <name> time` | `generic_data` (s) | each `test.step` duration | `wux:phase_time:<n>:<test>` |
| `Last error screenshot` | `generic_data_string` (image) | screenshot on failure | `wux:error_screenshot:<test>` |
| `Global error` | `generic_data_string` | `OK` or the test's error text (with `_errorHistoryModule_` on) | `wux:global_error:<test>` |
| `Phase <name> error` | `generic_data_string` | `OK` or the phase's error text (with `_errorHistoryModule_` on) | `wux:phase_error:<n>:<test>` |
| `<metric name>` | `generic_data` / `generic_data_string` | `pandora.metric` annotation | `pw:metric:<name>` |
| `Full report` | `async_string` | verbose JSON-derived report | `pw:full_report` |

The `wux:*` modules render in the console's WUX transactional view. `pw:*` modules are regular agent modules (metrics and the full report).

## Console extension

The plugin ships a companion console extension, **WUX Transactions** (`wux_transactions_ext`), which registers a **"WUX Transactions"** option in the operation menu (under the section that hosts monitoring/state views) and renders the view identified by the "Monitoring → Views → WUX Transactions" breadcrumb. Opening it requires the user to hold at least one of the **AR** or **RR** ACLs; the extension also applies group ACL (AR over the module's group) to everything it lists.

The view provides the transactional monitoring layer for WUX data:

- **Transactions are discovered from module `extra_data`.** The extension lists every module whose `extra_data` starts with `wux:global_status:` (the WUX agent's own `extra_data` is empty, so module markers are the source of transactions). A multi-select filter ("Select transactions") picks one or more transactions to compare their latest execution data.
- **Overview cards** aggregate the selected transactions: Selected / Passing / Failing / Unknown counts and the Average global time. When several Discovery tasks report to the same transaction, a "Shared transactions" warning is shown (for tasks with debug mode enabled, which is all the extension can detect); the recommended fix is a different `_prefixAgents_` per task.
- **Per-transaction panels** show the global status/time, the phases table (Phase, Status, Time, Updated, plus module graph/detail actions), WUX timing metrics, custom metrics (`pw:metric` values emitted by the test), and the evidence block: **Last error screenshot** (when the module holds a valid `data:image/...` value) and the **Full WUX report** when `_fullReport_` is on.
- **Playwright debug evidence**: for tasks of the app `pandorafms.playwright.1` with Debug mode enabled, the extension reads the task's **Debug directory** field from `tdiscovery_apps_tasks_macros` (macro `_debugDirectory_`), substitutes the `_taskid_` placeholder with `md5(id_rt)` exactly like the runner does, reads the `manifest.json` left by the last run and indexes it by agent name. A "Playwright debug" button on the transaction panel opens a modal with one block per task run: Passed/Failed tag, capture timestamp, **failure video** (webm), **failure screenshot** (png), **error context** (markdown page snapshot at failure), the full run report and the Playwright API transaction log (`pw:api`). Artifacts are streamed through an endpoint that only serves the whitelisted kinds (screenshot/video/error-context), enforces group ACL and is never cached.
- **No-evidence reporting**: tasks whose evidence cannot be read are listed at the top of the view with the task, its debug directory and the reason — see the four-reason table in [If the console shows no evidence](#if-the-console-shows-no-evidence).

<!-- SCREENSHOT NEEDED: Console view Monitoring → Views → WUX Transactions: the transaction selector filter, the overview cards (Selected, Passing, Failing, Unknown, Average global time) and a transaction panel with the phases table, custom metrics and the Playwright debug evidence modal open. Image goes at ../assets/images/discovery/playwright/wux-transactions-view.png -->

## The Docker image

Every task runs inside `pandorafms/pandora_playwright:noble`, the default value of the **Docker image** field (`_dockerImage_`). The recommended way to get it is to pull it:

```bash
docker pull pandorafms/pandora_playwright:noble
```

It is a thin layer on top of Microsoft's official Playwright image, which already ships Chromium, Firefox and WebKit with all their system libraries — the part that is slow and fragile to assemble by hand.

### The image contract

The runner generates the complete Playwright configuration on every execution and writes it into the running container (see [Debugging a test](#debugging-a-test)), so the image depends on **one** thing only:

> `@playwright/test` installed in `/pandora/node_modules`, at the same version as the browsers in the image.

Everything else is convenience. Any image that satisfies that line works as a `docker_image` value.

### The Dockerfile

You do not need this to use the plugin — pull the image and you are done. It is here so you can rebuild the image yourself, audit what is in it, or use it as the starting point for a customized one. This is the `docker/Dockerfile` shipped with the plugin:

```dockerfile
# Base image ships the browsers preinstalled (Chromium, Firefox, WebKit).
# Pin the Playwright version to the same tag the runner was validated against.
FROM mcr.microsoft.com/playwright:v1.62.0-noble

# @playwright/test must match the base image Playwright version.
ARG PLAYWRIGHT_VERSION=1.62.0

WORKDIR /pandora

RUN apt update && apt install -y vim

# Minimal project so `npx playwright test` resolves the runner locally.
RUN npm init -y >/dev/null 2>&1 \
    && npm install -D @playwright/test@${PLAYWRIGHT_VERSION}
```

```bash
docker build --pull -t pandorafms/pandora_playwright:noble -f Dockerfile .
```

| Step | Why it is there |
|------|-----------------|
| `FROM mcr.microsoft.com/playwright:v1.62.0-noble` | Ubuntu 24.04 with the three browsers already installed. Pinned, never `:latest`: browsers that move under you turn an unrelated upgrade into a monitoring incident |
| `ARG PLAYWRIGHT_VERSION=1.62.0` | Version of the **test runner** installed below. It has to match the base image tag — see [Two versions that must match](#two-versions-that-must-match) |
| `WORKDIR /pandora` | Every path the runner uses is under `/pandora`: the test, the generated config, `node_modules` |
| `apt install vim` | Convenience only, for [Manual interactive debugging](#manual-interactive-debugging). Nothing in the plugin needs it |
| `npm init -y` + `npm install -D @playwright/test` | The only step that matters. It creates `/pandora/node_modules` so `npx playwright test` resolves the runner **locally**, from inside the project |

Two things the Dockerfile deliberately does **not** do:

- **No `COPY` of any Playwright config.** The runner writes its own on every execution, so a config baked into the image would never be read.
- **No `ENTRYPOINT` and no `CMD`.** The container holds no logic of its own: the runner starts it with `docker run -d <image> sleep <ttl>` and drives everything from outside with `docker cp` and `docker exec`. A custom entrypoint would be bypassed at best, and would break the run at worst.

### Building your own image

If your tests need something extra, layer **on top** of the published image instead of rewriting the Dockerfile — you keep the version pinning and inherit future fixes:

```dockerfile
FROM pandorafms/pandora_playwright:noble

# Extra system packages your tests need (a font pack, a VPN client, a CA bundle...).
USER root
RUN apt-get update && apt-get install -y fonts-noto-cjk && rm -rf /var/lib/apt/lists/*

# Extra npm libraries your tests import, installed into the same project so
# `npx playwright test` resolves them: /pandora/node_modules.
WORKDIR /pandora
RUN npm install -D otplib          # e.g. tests that need a TOTP second factor
```

Build it, make it available on the machine that runs the tests — the Discovery server for `worker_mode = local`, the SSH target for `remote` — and point the task's **Docker image** field at it:

```json
"docker_image": "mycompany/pandora_playwright:noble-corp"
```

Two rules for a custom image:

- **Do not move `WORKDIR` away from `/pandora`.** The runner writes `task.spec.ts` and `playwright.config.task.ts` there by absolute path, and runs `cd /pandora` before `npx playwright test`.
- **Install npm packages into `/pandora`**, not globally. Node resolves a test's imports from its own project tree.

### Two versions that must match

The base image tag and `PLAYWRIGHT_VERSION` are the same number twice, and they have to stay that way: the browsers are baked into the base image, and `@playwright/test` only drives the browser build it was released with. Change it in **both** places at once:

```dockerfile
FROM mcr.microsoft.com/playwright:v1.63.0-noble
ARG PLAYWRIGHT_VERSION=1.63.0
```

A mismatch does not fail at build time. It fails at run time, usually as a browser that refuses to launch or an executable Playwright says it cannot find:

```
browserType.launch: Executable doesn't exist at /ms-playwright/chromium-1234/chrome-linux/chrome
```

Bumping the version moves the runtime the whole plugin was validated against, so re-run the flow in [Testing / QA — step by step](#testing-qa-step-by-step) and update the [Compatibility matrix](#compatibility-matrix) with the version you tested.

## Timeouts

Playwright has several independent timeouts. **Test timeout** (`_globalTimeout_`) is the one always on the wizard, and it is **not** the per-step timeout most people mean. The three per-step ones are off by default and appear in **Advanced setup** once **Advanced timeouts** (`_advancedTimeouts_`) is checked; they can also be set in the test file, which always wins.

| Timeout | What it bounds | Where to set it | Value in this plugin |
|---------|----------------|-----------------|----------------------|
| Per-test | one whole `test(...)`, including every `test.step`, action and assertion inside it | task field **Test timeout** (`_globalTimeout_`) → `npx playwright test --timeout=<s × 1000>` | `120` s by default |
| Action | each individual action: `click`, `fill`, `press`, `check`, `selectOption`... | task field **Action timeout** (`_actionTimeout_`), or the test file | unset → Playwright default `0` (no limit) |
| Navigation | each navigation: `goto`, `waitForURL`, `waitForNavigation`, `reload` | task field **Navigation timeout** (`_navigationTimeout_`), or the test file | unset → Playwright default `0` (no limit) |
| Expect | each web-first assertion: `expect(locator).toBeVisible()`, `toHaveText`... | task field **Expect timeout** (`_expectTimeout_`), or the test file | unset → Playwright default `5000` ms |
| Container TTL | the whole run inside Docker | derived, not configurable | `min(3600, max(120, <Test timeout> × 20))` → `2400` s by default |
| SSH connect | opening the SSH session (`remote` worker only) | derived, not configurable | `<Test timeout>` → `120` s by default |

With **Advanced timeouts** off, the generated config declares none of the three, so Playwright's own defaults apply and there is exactly one place — the task, or your test — where a value can come from.

### Test timeout: per test, not per step and not per task

The field maps straight to Playwright's `--timeout`, which is the **budget for one `test(...)` block as a whole**. All of its steps, actions and assertions spend from the same budget.

When a test exceeds it, Playwright aborts **that test only** and marks it `timedOut`: its `Global status` module reports `0` and the phase that was running is reported as failed. **The remaining `test(...)` blocks in the file still run, and the Discovery task is not killed.** The plugin passes no `--global-timeout` and sets no timeout on the process or SSH command it runs, so nothing in it aborts a run for taking too long overall — with the single exception of the container TTL described below.

### Advanced timeouts: per-step timeouts from the task

Check **Advanced timeouts** in **Advanced setup** and the three per-step fields appear, prefilled with Playwright's own defaults (`0`, `0`, `5` seconds). Leaving them at those values changes nothing.

None of the three has a command-line flag, and only action and navigation are `use` options: `expect.timeout` lives at the top level of the config and cannot be reached from a test file at all. So instead of rewriting your test, the three values are added to the generated config — the file the runner writes into the container on every execution and that already carries the viewport and the capture settings. Your test is not touched, and anything it declares still wins.

### Per-step timeouts, set in the test file

The same three timeouts can be set in the `.ts` you paste into **Playwright test**, either at file level or per test. This overrides the task fields, and is the only option if you need a different value per test rather than one for the whole task.

At file level (also valid inside a `test.describe`, but **not** inside `beforeEach` or `beforeAll`):

```ts
import { test, expect as baseExpect } from '@playwright/test';

// Each action gets 5 s, each navigation 10 s
test.use({ actionTimeout: 5000, navigationTimeout: 10000 });

// Each web-first assertion gets 5 s
const expect = baseExpect.configure({ timeout: 5000 });

test('login', async ({ page }) => {
  await page.goto('https://example.com');       // 10 s
  await page.getByRole('button').click();       // 5 s
  await expect(page.getByText('Welcome')).toBeVisible(); // 5 s
});
```

Per call, when only one step needs a different limit:

```ts
await page.goto('https://slow.example.com', { timeout: 60000 });
await page.getByRole('button').click({ timeout: 2000 });
await expect(page.getByText('Report ready')).toBeVisible({ timeout: 30000 });
```

### Precedence: the test always wins over the task field

When the same test is given a timeout in both places, **the test file wins**. Playwright resolves the per-test timeout in this order, from lowest to highest priority:

```
playwright.config.task.ts  <  --timeout (task field)  <  test.describe.configure({ timeout })  <  test.setTimeout()
```

The task field is a *default* the runner puts on the command line, not a ceiling. It overrides the generated config, and anything the test declares overrides it in turn — per test, so the rest of the file keeps the task value.

```ts
// Task field says 120. This one test gets 5 min; every other test still gets 120 s.
test('long transaction', async ({ page }) => {
  test.setTimeout(300000);
  // ...
});
```

Action, navigation and expect timeouts resolve the same way: **Advanced timeouts** puts them in a config, which is the weakest level, so whatever the test declares overrides it. Either way, **Test timeout** still bounds them in wall-clock terms — see below.

**But the task field is the only thing that sets the container TTL.** The TTL is computed in the runner, before Docker starts, from the task field alone; no `test.setTimeout()` can raise it. A test that grants itself more time than the TTL allows still gets killed with the container (`Playwright produced no report`). So `test.setTimeout()` is safe to **lower** a test's budget, or to raise it within the room the TTL already gives you; to go beyond that, raise **Test timeout** in the task — it is the only input that moves the TTL with it.

### Making per-step timeouts actually fire

The per-test budget always wins. If **Test timeout** is `120` and a step is given `actionTimeout: 180000`, that step never reaches its own limit: the test dies at 120 s first, and the failure is reported as a test timeout rather than as the step that hung. For per-step timeouts to be the deciding limit, the per-test budget must be larger than the sum of the steps you expect — raise **Test timeout** in the task, or override it for one test from the file. Note that raising **Test timeout** also raises the container TTL and the SSH connect timeout, since both are derived from it; `test.setTimeout()` does not.

### Container TTL — the only limit that aborts a whole run

The runner starts the test container as `docker run -d --rm --name <task container> <image> sleep <ttl>` and then runs the test through `docker exec`. The TTL is derived from **Test timeout**:

```
ttl = min(3600, max(120, <Test timeout> × 20))
```

The clamp matters: the TTL only tracks **Test timeout** between `6` s and `180` s. Below that it is always `120` s, above it always `3600` s. With the default `120` s that is `2400` s (40 min). If a run's **total** duration exceeds the TTL, the `sleep` ends, the container stops and takes the in-flight `docker exec` with it: no `report.json` is produced and the task fails with `Playwright produced no report`. This is the closest thing to a whole-task timeout in the plugin — if you run several long tests in one file, size **Test timeout** so that `× 20` still covers the whole file, not just the slowest test.

## Multiple tests in one file

A single `.ts` can carry several `test(...)` blocks. The plugin treats each one as an independent transaction: **one agent per `test(...)`**, each with its own `Global status/time`, phases, screenshot and metrics. All of them run inside the same Docker container, in a single `npx playwright test` invocation.

### Default behavior: sequential

Playwright's default is that **test files run in parallel with each other, but the tests inside a single file run one after another in the same worker process**. This plugin always runs a single file (`task.spec.ts`), so file-level parallelism never applies: your tests start in the order they are written and each one finishes before the next begins.

Consequences:

- Total run time is the **sum** of every test's duration.
- Each `test(...)` gets a fresh browser context/page, so a test cannot leak state into the next one.
- A failing test does **not** abort the others: Playwright reports every test independently and the plugin builds each agent from its own result.
- With a hard `expect`, a failed assertion aborts *that* test — its later phases do not run, and any `pandora.metric` annotation pushed after the failure is never reached (push metrics as they are computed). Use `expect.soft()` to keep measuring the remaining phases.

### Running them in parallel at test level

If the tests are independent, wrap them in `test.describe.parallel(...)` and Playwright will spread them across multiple worker processes inside the container:

```typescript
import { test, expect } from '@playwright/test';

test.describe.parallel('independent checks', () => {
  test('checkout flow', async ({ page }) => { /* ... */ });
  test('login flow', async ({ page }) => { /* ... */ });
});

test('always sequential', async ({ page }) => { /* ... */ });
```

`test.describe.configure({ mode: 'parallel' })` at file scope is the equivalent form that applies to the whole file. The default is `mode: 'serial'`, so you only need to opt in.

Caveats:

- Playwright's default worker count is **half of the container's logical CPU cores**, and the plugin does not override it (`--workers` is not passed). With a single-core container the parallel block still runs one test at a time; with two or more cores the tests actually run concurrently.
- Each parallel test runs its own browser instance inside the container, so concurrency raises CPU and memory usage — size the container and the load on the target site accordingly.
- Parallel tests must not share state or depend on execution order. If any of them needs to run strictly after another, keep it outside the parallel block or use `test.describe.configure({ mode: 'serial' })` for that group.

## Recording a transaction

A "transaction" is just a standard Playwright test. You write plain Playwright — no PandoraFMS import required — and the plugin maps three native constructs:

| You write | Becomes |
|-----------|---------|
| `test.step('name', ...)` | a monitored **phase** (status + time) |
| `test.info().annotations.push({ type: 'pandora.metric', description: 'name=value' })` | a custom **metric** module |
| a failing assertion | the test fails; a **screenshot** is captured automatically |

To get the starting code for the flow, record it with any of these tools.

### 1. Record with Playwright codegen

On any machine with Playwright installed, launch the recorder against your site (see the [Playwright test generator](https://playwright.dev/docs/codegen-intro)):

```bash
npx playwright codegen https://your-app.example.com
```

Click through your flow in the browser; Playwright writes the equivalent code. Copy that code as the starting point.

### 2. Record with the Playwright VS Code extension

Install the **Playwright Test for VS Code** extension by Microsoft ([Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-playwright.playwright); requires Playwright v1.38+ in your project). Open the **Test Explorer** sidebar and use the recorder tools:

- **Record new**: opens a browser window where you navigate and interact with the site; the generated test is written into a new `.spec.ts` file in real time.
- **Record at cursor**: inserts newly recorded actions at the current cursor position inside an existing test.
- **Pick locator**: hover over an element in the browser and click to copy its best locator to the clipboard.

The extension works on a Playwright project, so record into any throwaway project and copy the resulting `.ts` as your starting point.

### 3. Record with the Playwright browser extension

Install **Playwright CRX** from the [Chrome Web Store](https://chromewebstore.google.com/detail/playwright-crx/jambeljnbnfbkcpnoiaedcabbgmnnlcd) (community extension by ruifigueira). It bundles the same recorder used by `playwright codegen` as a browser extension, so you can record directly in your own Chrome/Chromium/Edge:

- Attach the current tab with the extension button (or the context menu), or use the side panel; `Alt + Shift + R` starts recording and `Alt + Shift + C` starts inspecting.
- Perform the flow in the page; the recorder generates the Playwright code, in the selected language.
- Copy or export the generated script and use it as your starting point.

### Structure it into phases and add metrics

Whichever way you recorded the flow, wrap each meaningful part in `test.step(...)` so it becomes a phase, and add assertions to actually validate the result:

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
    // publish a custom metric module:
    test.info().annotations.push({ type: 'pandora.metric', description: `cart_items=${count}` });
  });
});
```

Only the test's **top-level** `test.step` calls become phases — the plugin reads the top-level `steps` array of Playwright's JSON reporter, so a step nested inside another step is not reported as a separate phase. Keep steps flat (one level) for anything you want to see as an independent phase in the console.

Metrics are parsed from the annotation with these exact rules (from the runner):

- `type` must be the literal string `pandora.metric`; anything else is ignored.
- `description` must be `name=value`, split on the **first** `=` only — so a value containing `=` (e.g. a URL query string) is not truncated.
- `name` and `value` are trimmed of surrounding whitespace. If `description` has no `=`, or `name` is empty after trimming, that annotation is silently skipped.
- The module type is inferred from the value: parses as a number → `generic_data`; anything else → `generic_data_string`. The module is named exactly `name` and tagged `extra_data = pw:metric:<name>`.

### Paste it into the task

Paste the full `.ts` into the **Playwright test (.ts)** field of the Discovery task, pick the browser and worker mode, and save.

### Tips

- **Naming**: the module names come from your `test.step` titles, so keep them descriptive (`'login'`, `'add to cart'`). Renaming a test starts a new agent.
- **Continue after a failure**: with a normal `expect`, a failed phase aborts the test and later phases do not run. If you want every phase measured even when one fails, use soft assertions: `await expect.soft(locator).toHaveText('x')`.
- **Multiple transactions**: several `test(...)` blocks in one `.ts` produce several agents.
- **Recorded code is a starting point, not the deliverable**: a recorder writes literal actions but has no way to know which element grouping is unique, whether a badge/status text repeats elsewhere on the page, or whether the real DOM text matches what CSS makes it *look* like (e.g. `text-transform: uppercase`). Review the recorded locators against the live page before wiring it into a Discovery task.

## Self-signed certificates

By default Playwright validates TLS certificates like a real browser, so a target using a self-signed or internally-issued certificate makes every `page.goto(...)` fail with `net::ERR_CERT_AUTHORITY_INVALID` before your test logic even runs.

There is no plugin-level toggle for this — set it explicitly in the transaction with Playwright's own `test.use()`:

```typescript
import { test, expect } from '@playwright/test';

test.use({ ignoreHTTPSErrors: true });

test('checkout flow', async ({ page }) => {
  await page.goto('https://internal.example.com');
  // ...
});
```

- `test.use({ ignoreHTTPSErrors: true })` placed at the top level of the file applies to every `test(...)` below it in that transaction.
- To scope it to only some tests in the same file, wrap them in their own `test.describe(...)` block and call `test.use({ ignoreHTTPSErrors: true })` as the first line inside that block, instead of at the top level.
- This only disables **certificate validation**, not TLS itself — the connection stays encrypted, it just no longer requires a trusted CA chain.

## Generating a transaction with an AI coding agent

Instead of hand-writing the `.ts` transaction (or recording it once and hoping the selectors hold), you can have a local coding agent — Claude Code, opencode, `pi`, or similar — drive a real browser through the flow and write the transaction for you, validating every locator against the live target before handing it over.

This works because these agents can use a **Playwright CLI/browser-automation skill** (a tool that opens a real browser, clicks, fills, and reads the DOM under agent control) to actually execute the flow step by step, not just guess selectors from a screenshot. A recorder records literal actions but has no way to know which element grouping is unique, whether a badge/status text repeats elsewhere, or whether the real DOM text matches what CSS makes it *look* like; an agent that can re-run each locator against the live page, see a strict-mode violation, and fix the scope before delivering the file catches exactly the class of bug that makes a transaction flaky in production.

### Prompt template

```
Validate [FLOW NAME] on [URL] and write it as a Playwright transaction for the
pandorafms.playwright.1 plugin.

What the transaction should check:
- [step 1, e.g. "open the page and confirm the title"]
- [step 2, e.g. "log in and confirm the dashboard loads"]
- [step 3, e.g. "read a value and publish it as a pandora.metric"]

Deliverable:
- Plain Playwright: wrap each meaningful step in `test.step('name', ...)` so it
  becomes a WUX phase, and use
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

### After you get the file

Run it through the plugin's own local flow before wiring it into a Discovery task — see [Testing / QA — step by step](#testing-qa-step-by-step) below — so you see the real agent/module output, not just "the test passed."

## Testing / QA — step by step

This is the flow used to validate the plugin end to end. It covers the ready-to-use samples referenced by [Manual execution](#manual-execution).

### 1. A sample test and configuration

`sample.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('passing check', async ({ page }) => {
  await test.step('open', async () => { await page.setContent('<h1 id=t>Hello</h1>'); });
  await test.step('assert', async () => { await expect(page.locator('#t')).toHaveText('Hello'); });
  test.info().annotations.push({ type: 'pandora.metric', description: 'items=3' });
});

test('failing check', async ({ page }) => {
  await test.step('render', async () => { await page.setContent('<h1 id=t>Hello</h1>'); });
  await test.step('bad assert', async () => { await expect(page.locator('#t')).toHaveText('Goodbye', { timeout: 1500 }); });
});
```

`conf.json`:

```json
{ "worker_mode": "local", "browser": "chromium",
  "docker_image": "pandorafms/pandora_playwright:noble",
  "global_timeout": "15", "full_report": "1", "report_agent": "" }
```

### 2. Local run (inspect the monitoring data)

```bash
./venv/bin/python pandora_playwright.py -c conf.json -s sample.spec.ts -t qa-test -g 0 -v
```

STDERR shows the step-by-step trace; STDOUT is the Discovery JSON. Expect two agents (`Playwright - passing check`, `Playwright - failing check`), each with `Global status/time`, per-phase modules, an error screenshot (a `data:image/png;base64,...` value on the failing one, `None` on the passing one), the metric `items`, and a `Full report` module. Checklist: passing test → `Global status = 1`; failing test → `Global status = 0`; each `test.step` produces `Phase <name> status/time`; the failing test's `Last error screenshot` starts with `data:image/png;base64,`; no leftover containers (`docker ps -a` is clean).

### 3. Remote run (SSH)

Point the config at an SSH host that has Docker and the image:

```json
{ "worker_mode": "remote", "browser": "chromium",
  "ssh_address": "10.0.0.5", "ssh_port": "22", "ssh_user": "root",
  "ssh_password": "secret", "ssh_password_encrypt": "0", "ssh_temp_folder": "/tmp",
  "docker_image": "pandorafms/pandora_playwright:noble",
  "global_timeout": "15", "full_report": "1" }
```

```bash
./venv/bin/python pandora_playwright.py -c conf_remote.json -s sample.spec.ts -t qa-remote -g 0 -v
```

The verbose output is identical to local but with the `ssh$` prefix and extra `Connecting SSH` / `SSH authenticated` / `SCP` / remote-temp-cleanup lines.

### 4. End-to-end against a real Pandora (console rendering)

Run against a Pandora server's Tentacle to create real agents/modules:

```bash
./venv/bin/python pandora_playwright.py -x -S 127.0.0.1:41121 \
    -c conf.json -s sample.spec.ts -t qa-console -g 13 -T /tmp
```

Then verify in the database (the console's WUX view is driven by `extra_data`):

```sql
-- transactions found by the console:
SELECT id_agente_modulo, nombre, extra_data FROM tagente_modulo
WHERE extra_data LIKE 'wux:global_status:%' AND parent_module_id = 0;

-- phases of a transaction share the agent:
SELECT nombre, extra_data FROM tagente_modulo
WHERE extra_data LIKE 'wux:phase_status:%';
```

Finally, open the agent in the console and confirm the **WUX transactional view** shows the phases, and that `Last error screenshot` renders as an image.

## Debugging a test

When a transaction fails and the plugin's screenshot/`Full report` isn't enough to see what happened, there are two ways to get richer evidence: let the task itself capture it automatically (**Debug mode**), or drop into the image interactively and browse Playwright's own HTML report. Both use the same capture settings — `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'` — but they get them from different places: a task run from the generated config, a manual run from a config you write inside the container yourself (the image ships none).

### Debug mode (automated, per task run)

Enable **Debug mode** in the task's **Advanced setup** and set a **Debug directory** (defaults to `/var/spool/pandora/data_in/discovery/tmp/playwright/_taskid_`, with `_taskid_` auto-substituted by `md5(id_rt)`; a custom absolute path also works). Debug output always ends up **centralized on the Discovery server**, at that same path, regardless of `worker_mode`:

1. The runner wipes and recreates the debug directory on the Docker host (the Discovery server itself for `worker_mode = local`, or the SSH worker for `remote`), `chmod 777` so the container can write into it regardless of its internal user, and bind-mounts it into the container at `/pandora/debug`.
2. The test runs with the generated config, which carries the debug capture settings, and `--output` redirected into that mount, so screenshots, trace and video land directly under `<debug_directory>/test-results/<test>/` on that host.
3. The runner writes a `report.md` summary (status, phases, errors) into the same directory.
4. For `worker_mode = remote` only: the runner downloads the whole debug directory from the remote worker back onto the Discovery server (over the same SSH session, at the identical absolute path), then removes the remote copy — but only once the local copy is confirmed on disk. If the download fails, the remote copy is left in place instead of being deleted.
5. Finally the runner writes `manifest.json` into the directory, mapping each agent this run reported to its own artifacts.

The directory holds a **single run's worth of artifacts** — it is wiped, not appended to, on every execution, so only the latest run is kept. This is meant to be read later by another tool (e.g. the console extension), not browsed live — for interactive debugging with a served HTML report, use the manual flow below.

### manifest.json: mapping agents back to their evidence

An agent produced by this plugin is named `a + md5(<test title>)` — the task plays no part in that name (recreating a task keeps the agent and its history). The relationship between tasks and agents is genuinely N:M: one task produces many agents, and one agent may come from many tasks. `manifest.json` resolves that link from the side that can own it: each task's debug directory declares which agents *that* run produced, so a consumer can index every manifest by agent name and get an exact mapping, with no need to guess from Playwright's output directory slugs.

```json
{
  "task_id": "<md5(id_rt)>",
  "generated": "2026-08-11T15:53:39.264478",
  "worker_mode": "local",
  "browser": "chromium",
  "report": "report.md",
  "tests": [
    {
      "title": "failing check",
      "agent_name": "a9e960014d5185274a2d527b6f457ee96",
      "status": "failed",
      "passed": false,
      "duration_ms": 1654,
      "error": "Error: expect(locator).toHaveText(expected) failed…",
      "artifacts": {
        "screenshot": "test-results/task-failing-check-chromium/test-failed-1.png",
        "video": "test-results/task-failing-check-chromium/video.webm",
        "error-context": "test-results/task-failing-check-chromium/error-context.md"
      }
    }
  ]
}
```

Notes for consumers:

- `artifacts` paths are **relative to the debug directory**, and only cover files Playwright wrote inside it; a test that passed usually has none, since Playwright only captures screenshot/video on failure.
- Artifact paths come from Playwright's own JSON reporter, not from scanning directories, so they stay correct regardless of how Playwright slugifies test titles into folder names.
- The manifest is written **after** the remote fetch, so for `remote` tasks it describes files that are already local. A missing manifest means the run captured nothing (orchestration failed, or a remote fetch that did not land).
- The console's WUX Transactions extension consumes exactly this file to offer per-transaction debug evidence.

### If the console shows no evidence

The extension reads each task's own **Debug directory** field — there is no path to configure on its side — and lists, at the top of the view, every debug-enabled task whose evidence it could not read, with the reason:

| Reason | Cause |
|--------|-------|
| No absolute debug directory is set | Debug on with an empty or relative path. The run also aborts, since the runner validates it |
| Directory does not exist on this console | Either the task has not run yet, or console and Discovery server are **different hosts** — the path is valid on the server only. Share `data_in` over NFS or sync it |
| Directory exists but holds no `manifest.json` | An **older plugin build** is running (see the two-copy note in [Configuration in PandoraFMS](#configuration-in-pandorafms)), the run failed before capturing anything, or a `remote` fetch failed — in which case the evidence is still on the worker |
| Manifest unreadable or malformed | Permissions, or a run interrupted mid-write |

### The `_taskid_` placeholder

This is a plugin-specific convention, not a Discovery feature. Discovery's own macros (`__taskMD5__`, `__taskGroupID__`, ...) are only substituted server-side in Perl at execution time, so a field's default value reaches the plugin literally; the plugin itself, in Python, substitutes `_taskid_` with `md5(id_rt)` — the same value Discovery computes as `__taskMD5__` — after the value has already arrived inside the task's JSON config. Anything else with access to the task's `id_rt` can recompute the same value and land on the exact same directory name. The one exception is a manual CLI run (`-t <task_name>` with a human-readable name): the plugin hashes that name instead, since `-t` becomes the Docker container name.

### Manual interactive debugging

**1. Start the container**, mounting your `.ts` test directly if you already have it:

```bash
docker run -it --rm \
  -v "$(pwd)/test.spec.ts:/pandora/test.spec.ts" \
  -p 9323:9323 \
  pandorafms/pandora_playwright:noble bash
```

Or start without mounting anything and write the test inside the container (e.g. with `vim`, already installed in the image).

**2. Write a debug config.** The image ships no Playwright config — a task run generates its own and throws it away with the container. For a manual run, write one yourself inside `/pandora`. `video` and `reporter` have no command-line flag, so a config is the only way to get them:

```bash
cat > playwright.config.debug.ts <<'EOF'
import { defineConfig } from '@playwright/test';

export default defineConfig({
  reporter: [
    ['html', { host: '0.0.0.0', port: 9323, open: 'never' }],
    ['list'],
  ],
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
});
EOF
```

These are the same capture settings **Debug mode** puts in the generated config, plus the HTML reporter, which a task run never uses because the runner always passes `--reporter=json`.

**3. Run the test with it:**

```bash
npx playwright test test.spec.ts --config=playwright.config.debug.ts --browser=chromium --timeout=30000
```

**4. Serve and view the report:**

```bash
npx playwright show-report --host 0.0.0.0 --port 9323
```

With `-p 9323:9323` published on `docker run`, open `http://localhost:9323` on the host to browse the report: per-step results, the trace viewer, and the **video of the failure**.

## Troubleshooting

- **`docker: ... name is already in use`** — a previous run was interrupted before its cleanup (e.g. the runner was SIGKILLed) and left the container that owns this task's derived name; its `sleep` can hold the name for up to 30 minutes. The container is always started with `--rm`, so an orphan frees the name on its own once the `sleep` ends. To recover immediately, remove it (`docker rm -f <md5(task name)>`) or enable **Remove existing container with the same task name** in the task's Advanced setup so the runner does it before every run.
- **"Playwright produced no report"** — the test failed to run (syntax error, bad import, missing browser), or the run exceeded the container TTL. Run with `-v` and read the `docker exec` stderr; see [Container TTL](#container-ttl-the-only-limit-that-aborts-a-whole-run).
- **Screenshot shows as text, not an image** — the value must be `generic_data_string` with a `data:image/png;base64,` prefix (handled by the plugin); check you are on a build that includes this.
- **`Cannot find module '@playwright/test'`** — the test must be executed from `/pandora` inside the image so Node resolves `node_modules`; the plugin copies it to `/pandora/task.spec.ts` for this reason.
- **Agents land in the wrong group (xml_mode)** — Pandora agent XML expects the group **name**, not the numeric id. The Discovery `monitoring_data` path uses the numeric `id_group` correctly.
- **A later phase shows "ok" after an earlier failure** — with hard assertions a failed phase aborts the run, so later phases keep their previous value. Use `expect.soft()` if you want every phase measured on every run.
- **The console task form still runs an old build** — remember the two-copy note in [Configuration in PandoraFMS](#configuration-in-pandorafms): update the copy under `<remote_config>/discovery/`, not only the console's attachment.
- **`net::ERR_CERT_AUTHORITY_INVALID`** — see [Self-signed certificates](#self-signed-certificates).