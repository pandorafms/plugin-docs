# Pandora Plugin Executor

*Article last updated: 2026-10-26.*

## What it does

`pandora-plugin_exec` is a single standalone executable that monitors anything reachable with an HTTP request or a local command, and turns the result into Pandora FMS agents and modules. It replaces one plugin per technology with one program plus a catalog of YAML **templates**.

Each run reads one template and executes it once:

```text
template.yml → run tasks → filter their output into variables → build agents and modules → deliver
```

A template declares four things:

- **Tasks** — HTTP requests or local commands, executed sequentially. A later task can use values produced by an earlier one, so a login → token → authenticated request chain fits in a single run.
- **Filters** — a `jq` expression or a regular expression that extracts values from a task's output into a **variable**.
- **Agents and modules** — built from those variables with `{{ }}` expressions. One module per declared block, or one per element of an array.
- **Transfer** — how the result reaches Pandora FMS: Tentacle, a local Pandora data directory, or the standard output of a software agent plugin.

The executor is **one-shot**: it runs the template once and exits. Scheduling stays where it already is — the Pandora FMS agent, `cron`, or the Pandora FMS server itself.

The addon ships ready-made templates, including replacements for the `pandora_df_used_go`, `pandora_mem_used` and `pandora_netusage` agent plugins. See [Bundled templates](#bundled-templates).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `Pandora-Plugin-Executor`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| A host that can execute `pandora-plugin_exec` | `Required` | The addon is a standalone executable with no runtime dependencies; it is started by the agent, by `cron` or by hand |
| `/bin/sh` and the commands your templates invoke | `Required` | `local` tasks are executed through `/bin/sh -c`; the binaries and files a template names (`df`, `awk`, `/proc/meminfo`, ...) must exist on that host |
| Network access from that host to the URLs of the template | `Required` when the template has `request` tasks | The executor opens the connection itself |
| The Tentacle client (`tentacle_client`) | `Required` when `transfer.mode: tentacle` | The document is sent by invoking the Tentacle client |
| Write permission on `transfer.local.directory` | `Required` when `transfer.mode: local` | The agent document is written into that directory |
| A Pandora FMS software agent able to run `module_plugin` commands | `Required` when `transfer.mode: agent_plugin` | The agent is what starts the executor and ingests the module fragments it prints |
| Operating system, distribution and architecture | `Not validated` | No platform matrix has been recorded for this addon. The design record mentions end-to-end runs on a real host but does not identify the distribution, version or architecture, and the Marketplace tag `linux` is a tag, not a compatibility statement |
| Windows | `Not validated` | This page describes no Windows installation path, and no Windows artefact is identified for this addon |
| Pandora FMS versions | `Not validated` | The Marketplace banner ("All integrations are compatible with Pandora FMS NG 784 and later versions") is general to every integration, not a statement about this addon |

### Requirements

1. **A host to run the executable.** It is delivered as a standalone file named `pandora-plugin_exec`; there is no installer, no service and no runtime to install.
2. **A shell and the tools your templates call.** Every `local` task is a shell command, so the binaries and the files it references must exist on that host and be readable by the user that runs the executor.
3. **Pandora FMS** to receive the result: the server in `tentacle` or `local` mode, or the Pandora FMS software agent of the monitored host in `agent_plugin` mode.
4. **The Tentacle client**, only when the template delivers with `transfer.mode: tentacle`.

The executor runs with the privileges of the user that starts it. That user needs the Tentacle client in its `PATH` (or an absolute path in the template), or write access to the Pandora data directory, depending on the mode you choose.

### Install the addon

Download the package from the free Marketplace entry:

[https://marketplace.pandorafms.com/entries/Pandora-Plugin-Executor](https://marketplace.pandorafms.com/entries/Pandora-Plugin-Executor)

The file identified for version 1.0 is `Pandora-Plugin-Executor.1.0.zip`. The artefact the addon distributes is the `pandora-plugin_exec` executable.

1. Copy the executable to the host that will run it and make it executable, for example `/usr/bin/pandora-plugin_exec`.
2. Copy the templates you are going to use to a directory that the user running the executor can read, for example `/etc/pandora/templates/`. The executor reads only the template named with `-t`; it never scans a directory.

Nothing is installed on the monitored system unless that system is also the host that runs the executor — which is the case only in `agent_plugin` mode.

## Configure

### Choose a delivery mode

`transfer.mode` is mandatory and decides where the executor runs and what it prints.

| Mode | Runs on | Produces | Requirement |
|------|---------|----------|-------------|
| `agent_plugin` | The monitored host | `<module>` fragments on standard output; the real Pandora FMS agent adds the agent header | The Pandora FMS software agent starts it as a `module_plugin` |
| `tentacle` | Any host with network access to the Pandora FMS server | One complete `<agent_data>` document per template agent, sent with the Tentacle client | `tentacle_client` available, and `transfer.tentacle.address` |
| `local` | The Pandora FMS server, or any host that can write into a Pandora data directory | One complete `<agent_data>` document per template agent, written as a `.data` file | `transfer.local.directory` writable by the user that runs the executor |

This is the shortest complete template, in `agent_plugin` mode: it reads root filesystem usage and publishes one module.

```yaml
tasks:
  - name: disk_root
    type: local
    local:
      command: "df --output=pcent / | tail -1 | tr -d ' %'"
    variable: disk_pct

modules:
  - name: "Root disk used"
    type: generic_data
    data: "{{ disk_pct }}"
    unit: "%"
    min_warning: 80
    min_critical: 90

transfer:
  mode: agent_plugin
```

The same template in `tentacle` mode, with an agent block instead of top-level modules, because a full agent document needs an agent name:

```yaml
tasks:
  - name: api_stats
    type: request
    request:
      url: "https://<TARGET_HOST>/api/stats"
      headers:
        Authorization: "Bearer <API_TOKEN>"
      timeout: 10
    filter:
      type: jq
      expression: ".users.active"
    variable: active_users

agents:
  - name: "myapp"
    group: "Applications"
    interval: 300
    modules:
      - name: "Active users"
        type: generic_data
        data: "{{ active_users }}"

transfer:
  mode: tentacle
  tentacle:
    address: "<PANDORA_FMS_URL>"
```

For `local` mode, replace the last block:

```yaml
transfer:
  mode: local
  local:
    directory: "/var/spool/pandora/data_in"
```

### Register the executor in Pandora FMS

The executor does not install itself anywhere and does not schedule anything. Choose the registration that matches the mode.

**As a software agent plugin** (`agent_plugin`). Add the invocation to the agent configuration file and restart the agent:

```text
module_plugin /usr/bin/pandora-plugin_exec -t /etc/pandora/templates/disk_load.yml
```

The agent runs it at the interval configured for the plugin, and ingests the module fragments it prints. The agent supplies the agent name, the group and the interval: anything the template declares in an `agents:` block is ignored in this mode (see [What reaches Pandora FMS](#what-reaches-pandora-fms)).

<!-- SCREENSHOT NEEDED: Pandora FMS agent configuration file section showing a module_plugin line that invokes pandora-plugin_exec with a template path. -->

**From `cron` or the server** (`tentacle` or `local`). The crontab line *is* the schedule:

```cron
*/5 * * * * pandora-plugin_exec -t /etc/pandora/templates/myapp.yml
```

In `tentacle` mode the document is sent to the server address in the template. In `local` mode the document is written into `transfer.local.directory`; pointing that directory at the Pandora FMS incoming directory (`/var/spool/pandora/data_in` by default) on the server makes the run self-contained.

### Pass parameters to a run

Tokens left after the flags feed two reserved variables, seeded before any task runs:

- `args` — ordered list of positional tokens: `{{ args[0] }}`, `{{ len(args) }}`, `for_each: args`.
- `params` — map of named tokens: `{{ params.host }}`, `{{ params.threshold + 5 }}`.

Each token is split on the **first unescaped `=`**, and it becomes a named parameter only when the resulting key matches `[A-Za-z_][A-Za-z0-9_]*`. Every other token is positional. Numeric-looking values become numbers, so arithmetic works on them, and a repeated named key keeps the last value.

| Token | Becomes |
|-------|---------|
| `sda1` | `args[0]` = `"sda1"` |
| `90` | `args[0]` = `90` (number) |
| `host=db01` | `params.host` = `"db01"` |
| `conn=user=a;pw=b` | `params.conn` = `"user=a;pw=b"` (only the first `=` splits) |
| `'query\=a=b'` | positional `"query=a=b"` (the key would contain `=` and is not an identifier) |
| `k=1 k=2` | `params.k` = `2` (the last one wins) |

Two rules decide whether a run works at all:

- **Flags go before the arguments.** Flag parsing stops at the first token that is not a flag, and an argument that starts with `-` is rejected with an error instead of being silently taken as positional.
- **Bash eats the escape.** To pass a literal `=` that must not split, quote the token so the backslash survives: `'query\=a=b'`, or double it: `query\\=a=b`.

Referencing an undefined variable does not render an empty string: the affected module is skipped, and the notice reaches standard error only with `-v`. A parameter is optional only when the template says so explicitly. The three documented patterns are:

| Pattern | Effect |
|---------|--------|
| `{{ params.missing ?? "default" }}` | Renders a default when the key is absent |
| `when: "'k' in params"` | Includes the module only when the key was passed |
| `{{ len(args) > 1 ? args[1] : "all" }}` | Guards a positional access by count |

Task variables cannot be named `args` or `params`; `for_each: args` is valid.

### Write a template

A template is a YAML file with three sections: `tasks`, `agents` (or top-level `modules`), and `transfer`. Parsing is **strict**: an unknown field name is an error, so a typo stops the run with exit code 1 instead of being ignored.

- **`tasks`** run in declared order. Each one has a unique `name`, a `type` (`request` or `local`), the matching block, an optional `filter` and an optional `variable` that stores the filtered result. Without `variable` the task still runs and its output is discarded. A task only uses variables produced by tasks declared before it.
- **A `request` task** needs `url`, and accepts `method` (default `GET`), `headers`, `body`, `timeout` (seconds, default `30`) and `skip_tls_verify` (default `false`). A status outside 2xx is a task failure.
- **A `local` task** needs `command`, executed through `/bin/sh -c`, and accepts `timeout` (seconds, default `30`). A non-zero exit status is a task failure. Shell `$` is untouched, so `awk '{print $5}'` works as written; only `{{ }}` is substituted.
- **A `filter`** declares `type: jq` or `type: regexp` and an `expression`. Without a filter, the trimmed raw output of the task is the value.
- **`agents`** holds one block per agent with its `modules`; **top-level `modules`** is the alternative, valid only with `transfer.mode: agent_plugin`. The two are mutually exclusive.
- **`transfer`** declares the mode and its options.

The complete field tables are in [Reference](#reference). The rest of this page uses this longer example, which turns one regexp result into two modules per element:

```yaml
tasks:
  - name: df
    type: local
    local:
      command: "df -kTP"
    filter:
      type: regexp
      expression: '(?m)^(?P<fs>\S+)\s+(?P<fstype>\S+)\s+(?P<total>\d+)\s+(?P<used>\d+)\s+\d+\s+(?P<pct>\d+)%\s+(?P<mount>.+)$'
    variable: filesystems

modules:
  - for_each: filesystems
    when: 'value.fstype != "tmpfs"'
    name: "DiskUsed_{{ value.mount }}"
    type: generic_data
    data: "{{ value.pct }}"
    unit: "%"

  - for_each: filesystems
    when: 'value.fstype != "tmpfs"'
    name: "DiskUsed_{{ value.mount }} bytes"
    type: generic_data
    data: "{{ value.used }}"
    unit: "KB"

transfer:
  mode: agent_plugin
```

## Verify

Validate a template without delivering anything. For `tentacle` and `local` mode, `--dry-run` prints the agent document on standard output and does not transfer or write it:

```bash
pandora-plugin_exec -t <PATH_TO_CONFIG> --dry-run
```

Add `-v` to see, on standard error, which variables were stored and which modules were skipped:

```bash
pandora-plugin_exec -t <PATH_TO_CONFIG> --dry-run -v
```

A successful run exits with status `0`. Check it explicitly when you script it:

```bash
pandora-plugin_exec -t <PATH_TO_CONFIG> --dry-run; echo "exit=$?"
```

In `tentacle` and `local` mode the document starts with an XML declaration and one `agent_data` element whose attributes are the agent fields of the template:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<agent_data agent_name="myapp" timestamp="2026/10/27 08:00:00" group="Applications" interval="300" agent_mode="1">
  <module>
    <name><![CDATA[Active users]]></name>
    <type>generic_data</type>
    <data><![CDATA[42]]></data>
  </module>
</agent_data>
```

In `agent_plugin` mode there is nothing to dry-run: the executor only prints module fragments, so a plain execution is already the verification. `--dry-run` changes nothing in this mode.

```bash
pandora-plugin_exec -t /etc/pandora/templates/disk_load.yml
```

```xml
<module>
  <name><![CDATA[Root disk used]]></name>
  <type>generic_data</type>
  <data><![CDATA[81]]></data>
  <unit><![CDATA[%]]></unit>
  <min_warning><![CDATA[80]]></min_warning>
  <min_critical><![CDATA[90]]></min_critical>
</module>
```

For the final check, deliver for real and look at the result in Pandora FMS: in `agent_plugin` mode the modules appear under the agent that runs the plugin, and in `tentacle` or `local` mode the agent named in the template appears with its modules after the next data ingestion.

<!-- SCREENSHOT NEEDED: Pandora FMS agent detail view listing the modules generated by pandora-plugin_exec from one template. -->

## Understand the results

### Variables and module values

Each task with a `variable` stores exactly one value, and its shape comes from the filter:

| Filter result | Stored value |
|---------------|--------------|
| 0 matches | Nothing: the variable stays unset and the task is treated as failed |
| 1 match | A scalar |
| N matches | An array, one element per match |

A task without a filter always produces one element: the trimmed output.

Every captured string that looks numeric becomes a number, recursively inside objects and arrays. Module values are then rendered from numbers, which keeps arithmetic working but drops the original text:

- a captured `1.0` is published as `1`, and `007` as `7`;
- a captured version such as `2.30` is published as `2.3`;
- a counter longer than the precision of a floating-point number loses its last digits.

When a value must keep its exact text, make it non-numeric on purpose (for example with a prefix in the regexp capture) or publish it as `generic_data_string`.

A `jq` expression that emits `null` counts as one match, and a reference to that value is undefined, so the module is skipped like any other unresolved reference. Where the module must publish anyway, give the default inside the expression, as in `{{ value ?? "n/a" }}`.

### Module fan-out and conditions

`for_each` names an array variable and expands the block into **one module per element**. Inside the block, `{{ value }}` is the current element and `{{ index }}` its 0-based position, which is what allows lockstep access to two parallel arrays. Writing several blocks with the same `for_each` is how one element produces several modules.

- A scalar variable iterates as a one-element array.
- An unset `for_each` variable skips the whole block; the notice is written only with `-v`.
- Regexp filters with named capture groups make every element an **object**, so fields are read as `{{ value.mount }}`; two or more unnamed groups make every element a **positional array**, read as `{{ value[0] }}`.

`when` holds a boolean expression without `{{ }}`. It is evaluated per element inside a `for_each` block and against the whole variable store outside it. A false condition skips that element without an error; a condition that fails to evaluate, or that does not return a boolean, is reported and the module is skipped.

The executor does not deduplicate module names. Two elements that render the same name produce two modules with that name in the same document, so make the name unique with the element itself — as the example above does with `{{ value.mount }}`.

### What reaches Pandora FMS

In `tentacle` and `local` mode the executor builds **one `<agent_data>` document per agent of the template**. The agent attributes come from the template: `agent_name`, `agent_alias`, `parent_agent_name`, `description`, `version`, `os_name`, `os_version`, `timestamp`, `address`, `group`, `interval` and `agent_mode`. When `timestamp` is omitted the run time is used, and when `interval` is omitted the document carries `300`.

Each module becomes a `<module>` element with `<name>`, `<type>` and `<data>`; `description`, `unit`, the thresholds and the rest of the supported fields are added when the template sets them. A module whose `data` field is empty or absent publishes the value `0`.

In `agent_plugin` mode none of that header is emitted: only the `<module>` elements are printed, concatenated, with no XML declaration and no root element. The agent fields of the template — `group`, `interval`, `alias`, `description`, `os_*`, `address` — are therefore **not applied**, because the real agent supplies its own identity and interval. When the template declares more than one agent, each module name is prefixed with `<agent name>` + `transfer.module_prefix_separator` (default ` - `) so the modules cannot collide under that single agent.

A module whose value cannot be resolved is **absent** from the document. Pandora FMS receives no data for it in that run: the executor sends no explicit unknown state, so the module simply stops receiving values. That is the behaviour to expect when a task fails, a filter matches nothing or a condition is false.

## Operate and troubleshoot

### Everyday operation

- **One-shot and stateless.** Every run reads its template, executes it and exits. Nothing is cached, so a manual run at any time is equivalent to a scheduled one.
- **Logging.** Errors are always written to standard error with the `pandora-plugin_exec:` prefix and a timestamp. `-v` adds the debug stream there — stored variables, skips and delivery results — and leaves standard output clean for the XML. There is no log file and no log level.
- **`local` mode file names.** The document is written as `<md5 of the agent name>.<epoch seconds>.data` inside `transfer.local.directory`, which is created with mode `0755` if it does not exist. Two runs of the same agent within the same second wait for the next second before writing, so a fast loop does not overwrite data.
- **`tentacle` mode staging.** The document is written to a temporary directory under the system temporary directory, sent with the Tentacle client, and removed when the run ends.
- **Templates are executable content.** A template decides which commands run on the host. Keep template files writable only by the user that runs the executor, and treat a template received from someone else as code you are about to execute.
- **Credentials.** There is no secret store: a credential is written in the template, passed as a runtime parameter, or read by the command itself. A credential passed as a parameter is visible in the process list and in the shell history of whoever typed it, so keep templates at mode `0600` and prefer the credential-reading command pattern when the target supports it.

### Limits

- Two task types only: HTTP requests and local commands. There is no SNMP or database task, and the template has no conditional task execution.
- No scheduling and no daemon mode: the run happens when the agent, `cron` or an operator starts it.
- Tasks are sequential. A slow request delays every later task in the same run, and the run has no global timeout — only the per-task one.
- HTTP responses are read up to 10 MiB. A larger body is truncated silently, and the truncation usually surfaces later as a JSON parse error in the filter.
- A `local` task timeout terminates the `/bin/sh` process that runs the command; a command that starts its own children is responsible for stopping them.
- No retries. A failed task leaves its variable unset, and only `--strict` turns that into a non-zero exit status; without it the reason is visible only with `-v`.
- `webhook` delivery, per-template scheduling and additional task types are announced as not yet available in the addon's own documentation.

### Troubleshooting

- **`error: argument "--dry-run" looks like a flag; flags must come before the arguments`** — the flags were written after a positional token. Move every flag before the arguments.
- **Exit code 1 with `invalid template: ...`** — the template failed to parse. The message names the offending field or line: an unknown field, a duplicated task name, a `type` that does not match its block, an invalid filter type, an invalid variable name, `agents` together with top-level `modules`, top-level `modules` without `agent_plugin` mode, a missing `tentacle.address` or a missing `transfer.mode`.
- **Exit code 1 with `a template is required`** — `-t` was not passed, or the value was consumed by a preceding flag.
- **Exit code 2** — a task failed under `--strict`. Run again with `-v` to see which task and why.
- **A module is missing from the console** — its value was never resolved. Run with `-v` and look for `left unset`, `skipped` or `filter matched nothing`; the usual causes are a task that failed, a filter that matched nothing, and a parameter that was not passed.
- **A module publishes `0`** — the template does not set `data`, or the captured value was the empty string.
- **A number arrives with digits missing or without its decimals** — numeric coercion (see [Variables and module values](#variables-and-module-values)). Publish the value as text when its exact form matters.
- **Exit code 3 with `tentacle send failed`** — the Tentacle client could not deliver. Check that `tentacle_client` is in `PATH` or set `transfer.tentacle.binary`, the address and port in the template, and network access to the server. With several agents, the agents already sent in that run are delivered and the remaining ones are not.
- **`local` mode writes files but no agent appears** — the documents were written into a directory the server does not ingest. Confirm `transfer.local.directory` character by character: a wrong path is created silently instead of reported.
- **`task output is not valid JSON`** — the `jq` filter received something that is not JSON: an HTML error page, an empty body, a truncated body above 10 MiB, or a `local` command that printed a warning before the JSON.
- **`unexpected status 401` / `403` / `500`** — the request failed. The message carries the status and the first 200 characters of the response body, which is usually enough to tell authentication from a server error.
- **A request fails on a certificate** — the endpoint presents a certificate the host does not trust. `skip_tls_verify: true` accepts invalid certificates for that task and disables the protection, so use it only for a target you control.
- **A `local` command hangs until the timeout** — the task timeout expired and the shell was killed. Raise `timeout` for that task if the command legitimately needs longer, and check whether the child process that was left behind still holds a lock or a port.
- **`when` is ignored or the module never appears** — `when` is a raw expression, so `{{ }}` around it is an error; inside a `for_each` block it sees `value` and `index`, not the array variable.

## Reference

### Command-line flags

```text
pandora-plugin_exec -t <template.yml> [flags] [args...] [key=value...]
```

| Flag | Effect |
|------|--------|
| `-t`, `--template <path>` | Template to execute. Required |
| `--dry-run` | Prints the generated document on standard output and does not transfer or write it. Has no effect in `agent_plugin` mode, which always prints |
| `--strict` | Aborts on the first task failure or unresolved module instead of skipping it |
| `-v`, `--verbose` | Debug logging on standard error: task results, skips, warnings, delivery |
| `--version` | Prints the version and exits |

Flags must precede the arguments, and an argument that begins with `-` is rejected with exit code 1.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Template parse or validation error, and usage errors such as a missing `-t` |
| `2` | Task failure under `--strict`, and any error while building an agent document |
| `3` | Transfer error: the Tentacle delivery or the local write failed |

Without `--strict`, a failed task or an unresolved module does not change the exit status: the run delivers the modules that resolved and exits with `0`, and the reason is written to standard error only with `-v`.

### Runtime parameter classification

| Token | Key | Value | Stored as |
|-------|-----|-------|-----------|
| `sda1` | — | `sda1` | `args[0]` |
| `90` | — | `90` | `args[0]`, number |
| `host=db01` | `host` | `db01` | `params.host` |
| `threshold=90` | `threshold` | `90` | `params.threshold`, number |
| `conn=user=a;pw=b` | `conn` | `user=a;pw=b` | `params.conn` |
| `'query\=a=b'` | — | `query=a=b` | positional, because the key is not an identifier |
| `=foo` | — | `=foo` | positional, because the key is empty |
| `k=1 k=2` | `k` | `2` | `params.k`, the last value wins |

`args` is always a list, even when empty, so `for_each: args` and `len(args)` are safe. `params` is always a map. Both are reserved: a task `variable` cannot use those names.

### Template: tasks

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique task identifier, used in log lines |
| `type` | Yes | `request` or `local`, and it must match the block that is present |
| `request` | When `type: request` | HTTP request specification |
| `local` | When `type: local` | Command specification |
| `filter` | No | Extraction filter. Without it the trimmed raw output is the value |
| `variable` | No | Name that stores the result, matching `[A-Za-z_][A-Za-z0-9_]*`. Without it the output is discarded |

Tasks support `{{ }}` in their string fields — URL, body, header values and command. Task `name`, `variable` and `filter.expression` are not rendered.

#### `request`

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `url` | Yes | — | Target URL. Supports `{{ }}` |
| `method` | No | `GET` | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` or `HEAD`. Not rendered |
| `headers` | No | — | Header name to value. Values support `{{ }}` |
| `body` | No | — | Request body. Supports `{{ }}` |
| `timeout` | No | `30` | Seconds, applied to the whole request |
| `skip_tls_verify` | No | `false` | Accepts invalid TLS certificates |

A status outside 2xx fails the task, and the error carries the status and the first 200 characters of the body. The response body is read up to 10 MiB.

#### `local`

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `command` | Yes | — | Executed with `/bin/sh -c`. Supports `{{ }}`; shell `$` is untouched |
| `timeout` | No | `30` | Seconds; the shell process is terminated on expiry |

A non-zero exit status fails the task, and the error carries the first 200 characters of standard error.

### Template: filters

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | `jq` or `regexp` |
| `expression` | Yes | The filter expression. Not rendered |

**`jq`** — the task output must be valid JSON, and the expression runs in an embedded engine, so no `jq` executable is needed. Every value the expression emits is one element: `.token` gives a scalar, `.items[].name` an array of strings, `.items[]` an array of objects, and `.` the whole document as one object.

**`regexp`** — RE2 syntax, applied to the raw output: no backtracking and no lookahead, while `(?m)` and `(?i)` are available. The shape of each match depends on its capture groups:

| Pattern shape | Each match becomes |
|---------------|--------------------|
| No capture group (`cpu\d`) | The full match, as a string |
| One unnamed group (`(\d+)%`) | Capture group 1, as a string |
| Two or more unnamed groups (`(a)(b)(c)`) | A positional array: `[[a, b, c], ...]` |
| Named groups (`(?P<mount>...)`) | An object: group name to captured text |

Named and unnamed groups in the same regexp are not a supported combination for predictable access: as soon as one group is named, each match becomes an object built only from the named groups.

Cardinality is the same for both types: 0 matches leaves the variable unset, 1 match stores a scalar, N matches store an array.

### Template: agents

Required unless the template uses top-level `modules`.

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent name |
| `modules` | Yes | At least one module block |
| `alias` | No | Agent alias |
| `parent_agent_name` | No | Parent agent |
| `description` | No | Description |
| `version` | No | Agent version string |
| `os_name`, `os_version` | No | Operating system identification |
| `timestamp` | No | Overrides the document timestamp. Defaults to the run time |
| `address` | No | IP address or host name |
| `group` | No | Target group |
| `interval` | No | Seconds. The document carries `300` when omitted |
| `agent_mode` | No | Agent mode. The document carries `1` when omitted |

Every string field supports `{{ }}`. These fields are only used in `tentacle` and `local` mode.

### Template: modules

#### Control fields

These are executor semantics and are not sent to Pandora FMS.

| Field | Description |
|-------|-------------|
| `for_each` | Name of an array variable. The block expands to one module per element, with `{{ value }}` and `{{ index }}` available. A scalar variable iterates as one element, and a named-group element is read as `{{ value.field }}` while a positional one is read as `{{ value[0] }}` |
| `when` | Raw boolean expression, without `{{ }}`. False skips the module, or that element inside a `for_each` block |

#### Data fields

`name` and `type` are required; the rest are optional. Values may be numbers or strings in YAML, and all of them support `{{ }}`. The executor passes every field to the data document; only `interval` changes its name, to `module_interval`.

| Field | Description |
|-------|-------------|
| `name` | Module name |
| `type` | Module type: `generic_data`, `generic_proc`, `generic_data_string`, `generic_data_inc`, `async_data`, ... |
| `data` | Module value. An empty or absent `data` publishes `0` |
| `description` | Description |
| `unit` | Unit label |
| `interval` | Module interval, sent as `module_interval` |
| `tags` | Tags |
| `module_group` | Module group |
| `module_parent`, `module_parent_unlink` | Parent module relation |
| `min_warning`, `max_warning`, `min_critical`, `max_critical` | Numeric thresholds |
| `min_warning_forced`, `max_warning_forced`, `min_critical_forced`, `max_critical_forced` | Forced threshold variants |
| `str_warning`, `str_critical` | String-match thresholds |
| `str_warning_forced`, `str_critical_forced` | Forced string thresholds |
| `warning_inverse`, `critical_inverse` | Invert the threshold logic |
| `min`, `max` | Valid data range |
| `post_process` | Multiplier applied by the server |
| `disabled` | Create the module disabled |
| `status` | Force the module status |
| `timestamp` | Overrides the data timestamp |
| `custom_id` | Custom identifier |
| `critical_instructions`, `warning_instructions`, `unknown_instructions` | Operator instructions |
| `quiet` | Quiet mode |
| `min_ff_event`, `min_ff_event_normal`, `min_ff_event_warning`, `min_ff_event_critical` | FlipFlop thresholds |
| `module_ff_interval`, `ff_type`, `ff_timeout`, `each_ff` | FlipFlop behaviour |
| `crontab` | Cron-style module scheduling |
| `extra_data` | Extra payload |
| `alert_templates` | List of alert template names to bind |

### Template: transfer

| Field | Required | Description |
|-------|----------|-------------|
| `mode` | Yes | `tentacle`, `local` or `agent_plugin` |
| `tentacle.address` | For `tentacle` | Pandora FMS server address |
| `tentacle.port` | No | Tentacle port, `41121` by default |
| `tentacle.binary` | No | Path to the Tentacle client when it is not in `PATH` |
| `tentacle.extra_args` | No | Extra Tentacle client arguments, as a list |
| `local.directory` | For `local` | Directory where the `.data` document is written |
| `module_prefix_separator` | No | Separator for the multi-agent prefix in `agent_plugin` mode, `" - "` by default |

| Mode | Output | Use case |
|------|--------|----------|
| `tentacle` | Complete `<agent_data>` document sent with the Tentacle client | Remote execution from `cron` or the server |
| `local` | Complete `<agent_data>` document written as a `.data` file | Running on the Pandora FMS server itself |
| `agent_plugin` | `<module>` fragments on standard output | Running as the `module_plugin` of a software agent |

### Expression language

`{{ }}` placeholders and `when` conditions are expressions in the syntax documented at [expr-lang.org](https://expr-lang.org/docs/language-definition). Useful built-ins for template authors:

| Category | Built-ins and operators |
|----------|-------------------------|
| Strings | `split(s, sep)` · `join(list, sep)` · `upper(s)` · `lower(s)` · `trim(s)` · `replace(s, old, new)` · `contains(s, sub)` · `startsWith(s, pre)` · `endsWith(s, suf)` · `s matches "re2-pattern"` |
| Collections | `x in list` · `len(list)` · `list[i]` · `first(list)` · `last(list)` · `filter(list, pred)` · `map(list, expr)` · `all`/`any`/`none(list, pred)` · `sort(list)` · `uniq(list)` · `concat(a, b)` |
| Logic and nil | `a ?? "default"` · `obj?.field` · `cond ? a : b` · `'key' in map` |
| Numbers | `+ - * / %` · `abs(x)` · `min`/`max(a, b)` · `sum(list)` · `avg(list)` · `int(x)` · `float(x)` · `string(x)` |
| JSON | `toJSON(x)` · `fromJSON(s)` |

Inside the predicates of `filter`, `map`, `all`, `any` and `none` the current element is `#`, as in `filter(filesystems, #.pct > 90)`.

The expression language is used only in `{{ }}` and in `when`. A task's `filter.expression` is `jq` or a RE2 regular expression, never an expression of this language. In regular expressions written inside `when`, double the backslash (`\\d`), because expression string literals process escapes and the engine must receive a verbatim `\d`.

### Bundled templates

| Template | Purpose |
|----------|---------|
| `templates/df_used.yml` | Filesystem usage: one percentage module and one size module per filesystem. Replaces `pandora_df_used_go`, with thresholds at 90 and 95 on the percentage module |
| `templates/pandora_mem_used.yml` | Memory and swap usage in percent and in bytes. Replaces `pandora_mem_used` |
| `templates/pandora_netusage.yml` | Total bytes received and transmitted from `/proc/net/dev`, published as an incremental module. Replaces `pandora_netusage` |
| `templates/http_api_example.yml` | Token authentication chain against a JSON API: login → token → two authenticated requests |
| `templates/local_commands_example.yml` | Local commands as an agent plugin, with the three regexp result shapes |

All three replacements end in `transfer.mode: agent_plugin` and expect the invocation shown in their own header comment, with the template at `/etc/pandora/templates/`.

Copy these templates from the package if it carries a `templates/` directory: the executor never installs a template and never reads one you did not pass with `-t`.

| Template | Parameter | Default | Effect |
|----------|-----------|---------|--------|
| `df_used.yml` | `include` | — | Force monitoring of a mount whose `fstype` is outside the default list. Comma-separated, exact mount matches |
| `df_used.yml` | `exclude` | — | Never monitor a mount. Comma-separated, exact mount matches. Exclude wins over include |
| `pandora_netusage.yml` | `include` | — | Monitor only these interfaces. Comma-separated, exact names |
| `pandora_netusage.yml` | `exclude` | — | Never monitor an interface. Comma-separated, exact names. Exclude wins over include |
| `pandora_mem_used.yml` | `mem_critical` | `95` | Critical threshold of the `Memory_Used` percentage module |
| `pandora_mem_used.yml` | `swap_critical` | `95` | Critical threshold of the `Swap_Used` percentage module |

The two byte modules of `pandora_mem_used.yml` compute their critical threshold inside the command, at 95 % of the corresponding total, and ignore those parameters.

The size module of `df_used.yml` publishes the `Used` column of `df -kTP`, which `df` reports in 1K blocks, while the template declares `unit: "bytes"`. A filesystem whose `df` reports `1000000` in that column is published as `1000000 bytes`, a value 1024 times smaller than the real usage. If you rely on that module, convert the value in the template or correct the unit.

### Addon identity

| Field | Value |
|-------|-------|
| Marketplace identifier | `Pandora-Plugin-Executor` |
| Marketplace name | Pandora Plugin Executor |
| Addon version | `1.0` |
| Marketplace last update | 2026-08-19 |
| Marketplace package | `Pandora-Plugin-Executor.1.0.zip` |
| License | Free download |
| Marketplace type | Miscelaneus |
| Downloads | 4 |
| Executable | `pandora-plugin_exec` |
| Version printed by `--version` | `0.1.0` |
| Workflow | Standalone executor driven by YAML templates, with three delivery modes |
