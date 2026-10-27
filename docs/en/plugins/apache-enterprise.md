# Apache Enterprise Plugin

*Article last updated: 2026-10-27.*

!!! warning "Discovery integration recommended"
    For new installations use [Apache Discovery](../discovery/apache-discovery.md), which is the recommended integration for this service. This plugin is the legacy path.

## What it does

The Apache Enterprise Plugin reads the `mod_status` page of an Apache HTTP Server
and turns its counters into Pandora FMS modules: request and traffic rates, total
accesses and traffic, CPU load, uptime, restart time, requests in progress, idle
workers and an availability check.

The plugin runs as an **agent plugin**. The Pandora FMS software agent executes
it, reads the module XML it prints on standard output and stores the values in
the agent that runs it. Nothing is installed on the Apache server: the plugin
only makes an HTTP request to a status URL that must already exist.

This page documents the server monitoring plugin. Discovering Apache servers and
generating their agents is a different addon, documented in
[Apache Discovery](../discovery/apache-discovery.md).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `Apache`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with these versions. This is a published compatibility statement covering the addon, not a test record for it |
| `curl` on the host that runs the plugin | `Required` | The plugin retrieves the status page by running the `curl` command; it has no other HTTP client |
| Network access from the Pandora FMS agent to the status URL | `Required` | Prerequisite, not a compatibility statement |
| An Apache `mod_status` page served over HTTP | `Required` | The plugin parses the text of that page. See [Enable the status page](#enable-the-status-page) |
| Basic-authentication credentials for the status location, when it is protected | `Required` when the location requires authentication | The plugin sends them with `-user` and `-pass` |
| Apache HTTP Server versions | `Not validated` | No test record has been published for this addon. The legacy guide stated Apache 1.3 or later; nothing in the available evidence establishes that range |
| Operating system of the host that runs the plugin | `Not validated` | No operating system has been recorded for this version. The legacy guide stated it was developed and tested on Rocky Linux and Fedora 34; no record confirms it |
| Apache module set and MPM | `Not validated` | The available counters depend on the server configuration, not on the plugin |

### Requirements

1. **Apache `mod_status` enabled** and reachable from the Pandora FMS agent,
   with `ExtendedStatus On` so that the counters the plugin reads are present.
2. **A status URL that serves the HTML status page.** The plugin extracts the
   counters from the text of that page, so a machine-readable variant such as
   `server-status?auto` does not provide the lines it looks for.
3. **`curl` available in `PATH`** for the user that runs the Pandora FMS agent.
4. **Basic-authentication credentials**, when the status location is protected.
5. **A Pandora FMS software agent** on the host that runs the plugin, to execute
   it and ingest its modules.

The plugin only reads the status page. No official source identifies a narrower
set of Apache permissions; restrict who can reach the status location, as it
exposes request data.

### Enable the status page

Create the status location in a file included by the Apache configuration. The
exact path depends on the distribution; on a Red Hat-family layout it is a file
under `/etc/httpd/conf.d/`, for example `/etc/httpd/conf.d/server-status.conf`:

```apache
ExtendedStatus On

<Location "/server-status">
    SetHandler server-status
    Require valid-user

    AuthType Basic
    AuthName "Restricted Access"
    AuthUserFile /etc/httpd/.htpasswd
</Location>
```

Create the password file and the account the plugin will use, then reload or
restart the service:

```bash
sudo htpasswd -c /etc/httpd/.htpasswd <USERNAME>
```

The status location is open to anyone who can reach it unless the configuration
restricts it. The snippet above requires a user; `Require ip
<MONITORING_HOST_IP>` restricts it by address instead, and both can be combined.

Check that the page loads before configuring the plugin:

```bash
curl -s -u <USERNAME>:<PASSWORD> 'http://<TARGET_HOST>/server-status'
```

The response must contain the human-readable counter lines (`Total accesses:`,
`requests/sec`, `idle workers`, ...). A response with `ExtendedStatus` off, or a
`?auto` page, does not carry the lines the plugin reads.

### Install the plugin

Download the addon from the Pandora FMS Marketplace entry, which is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/Apache](https://marketplace.pandorafms.com/entries/Apache)

Copy the `pandora_apache` executable to the host that runs the Pandora FMS
agent, for example into `/etc/pandora/plugins/`, and give it execute permission:

```bash
sudo chmod 755 /etc/pandora/plugins/pandora_apache
```

Nothing is installed on the Apache server, and no Apache client tools are needed
on the monitoring host beyond `curl`.

## Configure

The plugin takes its configuration from two sources:

```text
built-in defaults < configuration file < command-line options
```

The configuration file is optional. When it is used, it must be the first
argument of the command line, and it is a plain-text file with one `key=value`
pair per line. Command-line options override the file values.

### Agent configuration

Declare the plugin in the Pandora FMS agent configuration file,
`/etc/pandora/pandora_agent.conf`, with a `module_plugin` line:

```text
module_plugin /etc/pandora/plugins/pandora_apache -url http://<TARGET_HOST>/server-status -user <USERNAME> -pass <PASSWORD>
```

The agent executes the line on every execution cycle, reads the module XML the
plugin prints and stores the modules in its agent. Use the absolute path of the
executable, and keep the whole invocation on one line: the agent splits it on
whitespace, so a password that contains spaces breaks the line.

If the installation uses centralized agent configuration, add the same
`module_plugin` line there instead of editing the local file.

<!-- SCREENSHOT NEEDED: Pandora FMS agent configuration view showing a module_plugin line for pandora_apache with a lab status URL, a user and a masked password. -->

### Configuration file and options

A configuration file keeps the credentials out of the `module_plugin` line:

```ini
url=http://<TARGET_HOST>/server-status
user=<USERNAME>
pass=<PASSWORD>
```

The file is passed as the only positional argument:

```bash
./pandora_apache /etc/pandora/plugins/apache.conf
```

The same run with options only, without a file:

```bash
./pandora_apache -url 'http://<TARGET_HOST>/server-status' -user <USERNAME> -pass <PASSWORD>
```

Key points:

- **`url`** is the complete status URL, including the scheme. It defaults to
  `http://127.0.0.1/server-status`, so a run that omits it queries the local
  server.
- Options use the single-dash form with a separate value: `-url <value>`. The
  forms `--url <value>` and `-url=<value>` are read as different keys and have no
  effect, and a trailing option without a value is silently dropped.
- Any option that the plugin does not use is accepted and ignored, so a
  misspelling does not stop the run — it silently leaves the documented value in
  place.
- **`preffix`** (spelled with the double `f`) is prepended to every module name.
  Leave it empty for a single Apache instance per agent. To monitor two instances
  from the same agent, give each one a different prefix; otherwise the second run
  overwrites the modules of the first, because the names are identical.
- The configuration file accepts `#` comment lines. Keys and values are trimmed
  and the last occurrence of a repeated key wins.

### Credentials and transport

- The plugin authenticates with HTTP Basic authentication only. It sends
  credentials when **both** `user` and `pass` are set; with only one of them the
  request goes out without authentication and the status page answers with an
  HTTP error.
- The password is passed to `curl` as a command-line argument, so it is visible
  in the operating system process list while the request runs (`ps`, for
  example), and it is stored in clear text in the configuration file or in the
  `module_plugin` line.
- Restrict the configuration file and the agent configuration to the user that
  runs the agent, for example `chmod 600`. There is no separate credentials file
  and no environment-variable input.
- With an `http` URL the credentials and the status page travel unencrypted. With
  an `https` URL the traffic is encrypted, but the plugin accepts any server
  certificate: it does not validate it, so HTTPS gives confidentiality without
  authenticating the server.

## Verify

Run the plugin manually from the host that runs the agent, with the
configuration file or with the options:

```bash
./pandora_apache -url 'http://<TARGET_HOST>/server-status' -user <USERNAME> -pass <PASSWORD>
```

Each run executes once and exits. A successful run prints one XML `<module>`
block per metric on standard output, in this form:

```xml
<module>
	<name><![CDATA[Apache Connection]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
</module>
<module>
	<name><![CDATA[Apache requests/sec]]></name>
	<type>generic_data</type>
	<data><![CDATA[0.3400]]></data>
	<unit><![CDATA[rq/sec]]></unit>
</module>
<module>
	<name><![CDATA[Apache last restart]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[Tuesday, 14-Oct-2025 08:12:34 CEST]]></data>
</module>
```

A module has a `<description>` element only when the status URL returned an HTTP
status other than 200; in that case the description carries the HTTP error.

The exit status is `0` whenever modules are printed, including runs that could
not reach the server, and `1` only when the command line is empty. Do not use the
exit status to decide whether the request worked.

In the console, the agent that runs the plugin shows the modules on its next
execution. Confirm that a numeric module such as `Apache requests/sec` receives
values.

<!-- SCREENSHOT NEEDED: Pandora FMS agent detail view listing the modules generated by pandora_apache for one Apache server. -->

## Understand the results

The plugin generates the same eleven modules on every successful run. They cover
four areas:

- **Availability.** `Apache Connection` reports `1` when the status URL answered
  HTTP 200 and `0` for any other HTTP status code.
- **Throughput.** `Apache requests/sec`, `Apache KB/sec` and `Apache KB/request`
  report the rates of the moment, in requests per second, kilobytes per second
  and kilobytes per request.
- **Totals since the last restart.** `Apache total accesses`,
  `Apache total traffic` and `Apache last restart` describe the accumulated
  counters, which reset when the server restarts.
- **Load and workers.** `Apache CPU Load`, `Apache current requests` and
  `Apache iddle workers` report the load figure, the requests being processed and
  the idle worker count.

Notes:

- Most numeric modules are printed with four decimals (`0.3400`, `1234.0000`),
  even for values that are integers on the status page. `Apache CPU Load` is the
  exception, described below.
- `Apache KB/sec` and `Apache KB/request` are always in kilobytes: the plugin
  converts bytes by dividing by 1024 and megabytes by multiplying by 1024.
  `Apache total traffic` keeps the unit the status page reports (`kB`, `MB`, ...)
  as the module unit.
- `Apache server uptime` is published in seconds, computed from the
  `Server uptime` line. A year counts as 360 days in that conversion.
- `Apache CPU Load` reads the second field of the `Server load:` line when the
  page has one; that field can carry the percentage in parentheses, for example
  `(5%)`, which is not a plain number. When the page has no such line, the plugin
  publishes the `% CPU load` figure with two decimals.
- `Apache iddle workers` is the module name as the plugin publishes it, with that
  spelling. Use it verbatim when you define alerts or dashboards.
- When `preffix` is set, it is prepended to every name above.
- A counter that is missing from the status page (typically because
  `ExtendedStatus` is off) is published as a zero — `0.0000` in the modules with
  four decimals, `0.00` in `Apache CPU Load` — and a missing `Restart Time` line is
  published as an empty string. A zero does not necessarily mean the server
  reported zero.
- `Apache Connection` is `1` when the response could not be interpreted at all,
  as well as on HTTP 200. See [Operate and troubleshoot](#operate-and-troubleshoot).

## Operate and troubleshoot

### Everyday operation

- The plugin keeps no state between runs: every execution reads the status page
  at that moment, so it can be run manually at any time without affecting the
  next scheduled run.
- The Pandora FMS agent runs the plugin with the agent's own execution cycle. Use
  the agent configuration to change how often the counters are read.
- The plugin sets no timeout on the request: a status location that accepts the
  connection and never answers keeps the run blocked until `curl` returns or the
  agent terminates it. The `timeout` key is read but not applied, and `curl` is
  invoked without a time limit.
- There is no verbose or debug mode: `-debug 1` is accepted but produces no
  additional diagnostics.
- Use a different `preffix` per Apache instance when one agent runs the plugin
  against several servers.

### Troubleshooting

- **`Apache Connection` is `1` but every counter reads zero** — the request did
  not complete. A failure that stops `curl` (no `curl` in `PATH`, DNS failure,
  connection refused, TLS error) leaves the availability module at `1` and prints
  the rest of the modules with zeros, together with a Perl warning on standard
  error. Check that `curl` exists for the agent user and that the URL is reachable
  from the agent host; do not rely on `Apache Connection` alone to detect an
  unreachable server.
- **`Apache Connection` is `0` and the module description shows an HTTP error** —
  the status location answered with that code. `401` means the credentials are
  missing or wrong: check `user` and `pass`. The plugin sends credentials only
  when both are set, so a run with just one of them also produces a `401`. `403`
  is an access rule rejecting the agent address. `404` is a wrong path. A
  `301`/`302` means the URL redirects: the plugin does not follow redirects, so
  point it at the final URL.
- **The page loads in a browser but every counter reads zero** — the URL is not
  serving the HTML status page the plugin parses (for example a `?auto`
  endpoint), or `ExtendedStatus` is off so the counters are absent. Compare the
  URL with the one you tested in [Enable the status page](#enable-the-status-page).
- **No module XML is printed** — the command line was empty. The plugin then
  prints its usage summary on standard error and exits with status `1`. There is
  no help option: `-h` is treated as an unknown key and the plugin runs against
  the default URL.
- **A run against the wrong server** — `url` was omitted and the default
  `http://127.0.0.1/server-status` was used, or the option was written as
  `--url`/`-url=...` and ignored.
- **The configuration file seems to be ignored** — it was not the first argument,
  or it cannot be opened. An unreadable file prints its error on standard error
  and the run continues with the built-in defaults instead of stopping, so the
  plugin may end up querying `http://127.0.0.1/server-status`. Check the argument
  order and the file permissions.
- **Two Apache servers overwrite each other's modules** — both runs publish the
  same module names. Give each one a different `preffix`, or use one agent per
  server.
- **Alert thresholds fire on zeros after an Apache restart** — the totals reset
  with the server. Compare `Apache total accesses` and `Apache total traffic`
  against the value of `Apache last restart` before treating a drop as an
  incident.

## Reference

### Configuration keys

The same keys are accepted in the configuration file and as single-dash options.

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `url` | No | `http://127.0.0.1/server-status` | Complete URL of the HTML `mod_status` page, including the scheme. |
| `user` | Required when the status location is protected | — | User for HTTP Basic authentication. Applied only together with `pass`. |
| `pass` | Required when the status location is protected | — | Password for `user`. Applied only together with `user`. |
| `preffix` | No | Empty | Text prepended to every generated module name. Spelled with the double `f`. |

Other keys are accepted and ignored, including `timeout`, `tag` and `debug`. In
the configuration file, blank lines and lines starting with `#` are skipped, keys
and values are trimmed, and the last occurrence of a repeated key wins.

### Command-line execution

```bash
./pandora_apache [config-file] [ -key value ... ]
```

| Condition | Behavior |
|-----------|----------|
| The command line is empty | The plugin prints its usage summary on standard error and exits with status `1`; no module is generated |
| The first argument names an existing file | The plugin reads it as the configuration file and applies the remaining options over its values |
| The first argument does not name a file | It is read as an option or ignored; the file is not loaded |
| `-key value` | Replaces the value of `key` from the file or the defaults |
| `--key value` or `-key=value` | Read as a different key and ignored, so the documented key keeps its default or file value |
| A trailing option without a value | Silently dropped; no error is reported |
| An unknown key | Accepted and ignored; the key set is not validated |
| `-h` or `--help` | No help option exists: it is treated as an unknown key |
| Exit status | `0` whenever modules are printed, including HTTP errors and unreachable servers; `1` only for an empty command line |

### Generated modules

Modules are printed in this order, with `preffix` prepended to each name when it
is set.

| Module | Type | Value | Unit |
|--------|------|-------|------|
| `Apache Connection` | `generic_proc` | `1` when the status URL answered HTTP 200, `0` for any other HTTP status code | — |
| `Apache CPU Load` | `generic_data` | Load figure of the status page | — |
| `Apache requests/sec` | `generic_data` | Requests per second | `rq/sec` |
| `Apache KB/sec` | `generic_data` | Traffic per second, converted to kilobytes | `KB/sec` |
| `Apache KB/request` | `generic_data` | Traffic per request, converted to kilobytes | `KB/rq` |
| `Apache last restart` | `generic_data_string` | Value of the `Restart Time` line | — |
| `Apache server uptime` | `generic_data` | Uptime in seconds | — |
| `Apache total accesses` | `generic_data` | Accesses since the last restart | — |
| `Apache total traffic` | `generic_data` | Traffic since the last restart | Unit reported by the status page |
| `Apache current requests` | `generic_data` | Requests currently being processed | — |
| `Apache iddle workers` | `generic_data` | Idle workers | — |

### Addon identity

| Field | Value |
|-------|-------|
| Marketplace identifier | `Apache` |
| Marketplace name | Apache Enterprise Plugin |
| Addon version | `1.0` |
| Marketplace package | `Apache.1.0.64` |
| Marketplace last update | 2025-06-10 |
| License | One — download limited to licensed users |
| Marketplace type | Miscelaneus |
| Workflow | Monitoring plugin, agent plugin mode |
| Executable | `pandora_apache` |
