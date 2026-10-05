# Autodiscover

*Article last updated: 2026-10-05.*

## What it does

The Autodiscover plugin finds the system services of an endpoint and turns them into Pandora FMS
modules. It runs as an **agent plugin**: the agent executes it, the plugin prints the module
definitions as XML on standard output, and the agent ingests them.

The plugin has two operating modes, and it needs one of them to do anything:

- **Built-in list** (`--default`) — monitors a list of common services (databases, web servers, mail
  servers, containers...) that is built into the plugin. Each entry is matched against the whole
  service name, so `ssh` never selects `sshd-keygen@rsa`.
- **Custom list** (`--list`) — monitors exactly the services you name, as substrings or regular
  expressions.

An endpoint has many units that are not running and does not have every service of the built-in
list installed; the plugin reports only what matches the list it is given, so a run is not a report
about the health of the whole endpoint.

- **Result.** One `generic_proc` status module per service that exists in the service manager and
  matches the active list: `1` while the service is running and `0` while it is stopped or inactive.
  A name of the list that does not exist on the endpoint produces no module at all.
- **Optional usage.** With `--usage`, the plugin also adds a CPU usage module and a memory usage
  module for each running service whose process can be resolved and whose usage is greater than
  zero.
- **Scope.** The plugin reads the service manager of the endpoint: systemd on Linux, the `service`
  command and `/etc/init.d` when systemd is not available, and the Service Control Manager on
  Windows.
- **Coverage.** Matching services are reported; nothing is discovered beyond the list you choose.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Plugin version `2.1` | Documented target | The version this page describes |
| Linux with systemd | `Tested` | Exercised on Fedora 44 (systemd 259) and Rocky Linux 10.2 (systemd 257): built-in list, custom lists, exclusions, verbose diagnostics and `oneshot` filtering |
| Linux without systemd (SysV) | `Not validated` | No SysV-only host has been recorded |
| Windows (Service Control Manager, amd64) | `Tested` | Exercised on Windows 11: built-in list, substring and exact matching, exclusions, `.service` suffix, three-character rule and `--usage` |
| Windows service names shorter than three characters | `Required` | The plugin discards list entries under three characters on Windows, see [Matching rules](#matching-rules) |
| An agent able to run `module_plugin` entries on the endpoint | `Required` | Prerequisite, see [Requirements](#requirements) |

### Requirements

1. **A Pandora FMS agent installed on the endpoint.** The plugin is executed by the agent; it is not
   a server plugin and it does not need the Pandora FMS server.
2. **Linux**: systemd, or the `service` command together with the `/etc/init.d` scripts when systemd
   is not booted. The plugin detects systemd at run time and falls back to SysV automatically.
3. **Windows**: no additional component. The plugin reads the Service Control Manager.
4. **Permissions to query the services of the endpoint.** Reading every service status and the
   resource usage of its process may require elevated privileges.

### Installation

The plugin is distributed inside the agent package and needs no separate installation. The agent
launches it through `module_plugin`, so no full path is required on Linux:

| Platform | Executable |
|----------|------------|
| Linux | `/usr/share/pandora_agent/plugins/autodiscover` |
| Windows | `%PROGRAMFILES%\Pandora_Agent\util\autodiscover.exe` |

## Configure

The whole configuration surface of the plugin is the agent configuration file: it has no
configuration file of its own. Add one `module_plugin` entry per run you want, using the
`module_begin` / `module_end` block to set a timeout.

The agent configuration shipped with the agent already contains this block:

```ini
# Service autodiscovery plugin
module_begin
module_plugin autodiscover --default
module_timeout 30
module_end
```

On Windows the same block names the executable explicitly:

```ini
# Service autodiscovery plugin
module_begin
module_plugin "%PROGRAMFILES%\Pandora_Agent\util\autodiscover.exe" --default
module_timeout 30
module_end
```

### Choose what to monitor

- **Built-in list.** Keep `--default` to monitor the services common to most servers. The list per
  platform is in [Built-in default service list](#built-in-default-service-list).
- **Custom list.** Replace it with `--list "<service1,service2>"`. Quote the value so the shell does
  not expand it, and separate the entries with commas.

```ini
# Monitor only the web server and SSH, by name
module_plugin autodiscover --list "httpd,sshd"
```

```ini
# Monitor the services matching a pattern
module_plugin autodiscover --list "apache.*,php[0-9.]*-fpm" --exact-match
```

### Narrow and refine the selection

- **`--exclude "<service1,service2>"`** removes services from the active list, whether it comes from
  `--default` or from `--list`. It is not an action of its own: it can be repeated, and the values
  accumulate. An entry that matches nothing is informational only.
- **`--exact-match`** makes each `--list` entry match the whole service name instead of a substring.
  Use it when a name such as `cron` also selects `cronie` or `crond`. The built-in list always
  matches exactly.
- **`--skip-oneshot`** (Linux with systemd only) ignores units whose type is `oneshot`. Such units
  run once and stay inactive by design, so their status module would be permanently `0`.
- **`-v`, `--verbose`** reports the diagnostics described in
  [Diagnostics](#diagnostics) on standard error. It never changes the exit code, so it is safe to
  leave enabled while tuning a list.

### Combine and order the flags

- `--default`, `--list` and `--help` are actions: **the first well-formed one in the command line
  wins** and the later actions do not run. The value of `--list` and `--exclude` is checked even when
  the action does not win, so `--default --list` fails instead of running `--default`. Add
  `--exclude`, never a second action, to narrow a selection.
- `--usage`, `--exact-match`, `--skip-oneshot`, `-v` and `--exclude` are not actions, so they can
  appear in any position and combine freely.
- A `--list` or `--exclude` without a value, or with a value that starts with `-`, is rejected: the
  plugin prints the error and the help screen.
- An unknown parameter is reported and followed by the help screen. The exit code stays `0` for
  every parameter problem, because the agent reads a non-zero exit as a plugin failure rather than as
  a configuration mistake. Unrecognized operating systems are the only non-zero exit. See
  [Exit codes and streams](#exit-codes-and-streams).

## Verify

Run the plugin manually on the endpoint with the same list you configured, and read the module XML
it prints:

```bash
/usr/share/pandora_agent/plugins/autodiscover --default
```

```xml
<module>
	<name><![CDATA[Service sshd - Status]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
</module>
```

- **One `<module>` block per matched service.** A run that matches nothing prints nothing at all.
- **The exit code is `0`** in every case except an unrecognized operating system. Do not use it to
  detect a bad list: use `-v` instead.
- **In Pandora FMS**, the agent ingests the printed modules on its next run, so
  `Service sshd - Status` appears in the module list of the agent that ran the plugin.

## Understand the results

Every service of the active list that exists in the service manager produces one status module;
`--usage` adds up to two more modules per running service.

| Module name | Type | Data | Unit | Parent | Generated when |
|-------------|------|------|------|--------|----------------|
| `Service <name> - Status` | `generic_proc` | `1` running, `0` stopped or inactive | — | — | The service exists in the service manager and matches the active list |
| `Service <name> - CPU usage` | `generic_data` | CPU usage of the service process | `%` | `Service <name> - Status` | `--usage`, service running, process found |
| `Service <name> - Memory usage` | `generic_data` | Memory usage of the service process | `%` | `Service <name> - Status` | `--usage`, service running, process found |

- **`<name>` is the service name without the platform suffix.** On systemd, the unit
  `sshd.service` produces `Service sshd - Status`.
- **A `0` is not necessarily a problem.** The status is `1` only while the service is running. A
  stopped service and an inactive unit produce `0`, and the module stays in Pandora FMS until it is
  deleted. A service that is not installed produces no module, so a name of the list with no module
  of its own is simply absent from the endpoint.
- **The usage modules are conditional.** They are emitted only for a running service whose process
  can be resolved and whose CPU or memory usage is greater than zero, so a first run may produce the
  status module alone.
- **How the status is read.** On systemd the unit is running when its `active` state is `active`; the
  plugin lists every unit, including inactive ones. With SysV the `service <name> status` output is
  read for `is running` / `is stopped`. On Windows the Service Control Manager report is used.

## Operate and troubleshoot

### Diagnostics

With `-v` (or `--verbose`) the plugin writes one line per finding on standard error, prefixed with
`autodiscover: warning:`. The exit code is never changed.

```bash
/usr/share/pandora_agent/plugins/autodiscover --list "nope" -v
```

```text
autodiscover: warning: entry "nope" matched no service
```

- An entry of `--list` or `--exclude` that matched no service is reported. With `--default`, entries
  for services that are not installed on the endpoint are reported the same way, which is why the
  diagnostics are opt-in: a default run would otherwise report the services the endpoint does not
  have.
- On Windows, list entries under three characters are reported as discarded.
- A `--skip-oneshot` run whose unit types could not be read reports that the filter was ignored.

### Execution limits

- The units are listed, and their type is read with `--skip-oneshot`, with a **30-second internal
  limit** per `systemctl` call; the per-service lookup of the process used by `--usage` has a
  **5-second limit**, and a `service` call has a **10-second limit**.
- The `module_timeout` of the shipped block is **30 seconds**. Raise it if the endpoint has a very
  large number of units, because the limit of the agent applies to the whole run and not only to one
  command.
- `--usage` adds one process lookup per running service, so it is slower than a status-only run.
- The plugin exits by itself when it finishes, and it handles `SIGTERM` by writing a message on
  standard error and exiting with code `0`.

### Troubleshoot

- **The plugin prints nothing.** No service of the active list matched. Check the list with `-v`,
  and remember that `--default` is matched against the whole service name.
- **A service is not monitored.** The name in the list does not match the unit or service name of
  the endpoint, or the service is not installed. Use the exact name, or a pattern that matches it,
  and confirm it with `-v`.
- **A status module is permanently `0`.** The service is stopped or inactive, or the unit is of type
  `oneshot`. Use `--skip-oneshot` to drop the last case. A service that is not installed produces no
  module at all, so a missing module is not a status of `0`.
- **Services you did not ask for appear.** A `--list` entry is a substring or a regular expression
  unless `--exact-match` is used, so `httpd` also selects `httpd-init` on a Linux systemd host, and
  `Spool` also selects `Spooler` on Windows. Add `--exact-match`, or narrow the pattern.
- **No usage module appears for a running service.** The service process could not be resolved, or
  its CPU and memory usage were both zero.
- **An unexpected line appears on standard error while the modules are correct.** A non-zero exit of
  `systemctl` is reported as a real failure, and the run then produces no modules. The messages under
  `-v` are informational and do not affect the result.
- **The agent reports a plugin timeout.** Raise `module_timeout`, reduce the list, or drop
  `--usage`.

## Reference

### Command line parameters

| Name | Value | Required | Default | Description |
|------|-------|----------|---------|-------------|
| `--default` | — | One action is required | — | Monitors the built-in list of the platform, matched exactly |
| `--list` | `<name1,name2,...>` | One action is required | — | Monitors the given list, matched as substrings or regular expressions unless `--exact-match` is set |
| `--exclude` | `<name1,name2,...>` | No | — | Removes matching services from the active list, using the same matching mode as the active list. Repeatable; the values accumulate |
| `--exact-match` | — | No | Disabled | Matches every `--list` entry against the whole service name, case-insensitive |
| `--skip-oneshot` | — | No | Disabled | Linux with systemd only: ignores units whose type is `oneshot` |
| `--usage` | — | No | Disabled | Adds a CPU usage and a memory usage module for every running service |
| `-v`, `--verbose` | — | No | Disabled | Reports diagnostics on standard error; never changes the exit code |
| `--help` | — | No | — | Prints the help screen, including the built-in list of the platform |

An action (`--default`, `--list`, `--help`) is mandatory in practice: with no argument, and with no
recognized action, the plugin prints the help screen and monitors nothing.

### Matching rules

- Each entry of a `--list` or `--exclude` value is a **case-insensitive pattern**.
- With `--exact-match`, and always for `--default`, the pattern must match the **whole** service name
  (`cron` does not match `cronie`). Without it, the pattern is matched anywhere in the name
  (`cron` matches `cronie` and `crond`), and regular expressions such as `php[0-9.]*-fpm` are
  allowed.
- A trailing `.service` is removed from an entry before matching, so `httpd.service` is accepted as
  the service `httpd`. The suffix is kept when the rest of the entry contains any of
  `\ ^ $ * + ? ( ) [ ] { } |`, so a pattern such as `.*\.service` is used as written. The dot itself
  is not a metacharacter here, so a real name such as `dbus-org.freedesktop.NetworkManager.service`
  keeps working.
- On Windows, entries shorter than three characters are discarded.
- On Linux without systemd, the entries of `--list` are used as literal names of `/etc/init.d`
  scripts, so regular expressions do not apply there.

### Built-in default service list

`--default` matches each entry against the whole service name, case-insensitive. The entries are
patterns, so versioned or instance-suffixed names are covered. Entries that do not exist on the
endpoint are ignored.

**Linux**

```text
httpd, apache2, nginx, slapd, postfix, mysqld, mysql, mariadb, postgresql(-\d+)?, oracle,
oracle(-\w+)*, mongod, mongodb, redis, redis-server, elasticsearch, rabbitmq-server, ssh, sshd,
cron, crond, cronie, chronyd, chrony, ntpd, ntp, docker, containerd, php-fpm, php[\d.]*-fpm,
haproxy, keepalived, tomcat, tomcat\d*
```

**Windows**

```text
MySQL(\d+)?, postgresql(-x64-\d+)?, pgsql, OracleService\w*, Oracle\w*TNSListener, MSSQLSERVER,
MSSQL\$\w+, SQLSERVERAGENT, IISADMIN, Apache2\.\d+, nginx, W3svc, NTDS, DNS,
MSExchangeADTopology, MSExchangeServiceHost, MSExchangeSA, MSExchangeTransport, MSExchangeIS,
Spooler, TermService, wuauserv, DHCP, TeamViewer, AnyDesk
```

### Exit codes and streams

| Stream | Content |
|--------|---------|
| Standard output | The module XML, one `<module>` block per module. Also the help screen, which is printed when no action is given, on `--help` and after an unknown parameter |
| Standard error | The error of an unknown or incomplete parameter, the messages prefixed with `autodiscover: warning:` when `-v` is set, and real failures such as a `systemctl` call that could not be run |

| Exit code | Meaning |
|-----------|---------|
| `0` | Normal run, help screen, warning, an unknown parameter, or an error inside the plugin |
| `1` | The operating system is not recognized |
