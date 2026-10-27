# Sybase monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The Sybase monitoring plugin monitors a Sybase ASE (Adaptive Server Enterprise) server from Pandora FMS. Each execution collects two kinds of data and turns them into Pandora FMS modules:

- **Server state, read with SQL.** Through the Sybase `isql` utility the plugin reads the Adaptive Server catalogs: databases and their allocated and used space, transaction log and segment usage, user connections, locks, blocked processes, offline engines, suspect databases and suspect indexes.
- **Local process state.** From the process list of the host the plugin reports whether the Adaptive Server and the backup server processes are running, and the memory and CPU they consume.

The plugin runs as a Pandora FMS agent plugin: every execution prints one XML `<module>` block per generated module on standard output, and the Pandora FMS agent installed on that host ingests them into the endpoint's agent. The plugin creates no agent and delivers no data by itself, so it is not a server plugin.

Because the process modules read the local process list, run the plugin on the host where the ASE server runs. Executed against a remote server, it reports the processes of the machine it runs on.

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.sybase`, version `1.0` | Documented target | Marketplace entry; see [Addon identity](#addon-identity) |
| Windows 10 | `Known compatible` | The previous edition of this guide records Windows 10 as the tested system, and the Marketplace package is a Windows executable. Not re-validated for version `1.0` |
| Operating systems other than Windows | `Not validated` | No test record; the Marketplace entry distributes a single Windows executable |
| Sybase ASE versions and editions | `Not validated` | No version matrix has been recorded for this addon |
| Pandora FMS versions | `Not validated` | No version matrix has been recorded. The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later |
| A Sybase environment script that exists on the host | `Required` | The plugin stops with exit status `1` when `sybase_env_script` does not name an existing file |
| The Sybase `isql` utility reachable from the host | `Required` | Every SQL check is executed through `isql` |
| A Pandora FMS agent on the ASE host | `Required` | The plugin is executed as an agent plugin |

The addon is published in the Pandora FMS Marketplace, with free download:

[https://marketplace.pandorafms.com/entries/pandorafms.sybase](https://marketplace.pandorafms.com/entries/pandorafms.sybase)

### Requirements

1. **A Sybase ASE server** reachable from the host that runs the plugin, with the server name and port you configure.
2. **The Sybase `isql` utility and the Sybase environment script** on that host. `isql` resolves from `PATH` by default, and on Unix-like systems the environment script is sourced before every query.
3. **A Sybase login** that can read the catalogs and run the procedures of the checks you enable; see [Sybase login](#sybase-login).
4. **A Pandora FMS agent on the same host**, which executes the plugin and ingests its modules.
5. **On Windows, the command-line utilities the plugin calls**: `grep`, `wc`, `tail`, `head`, `sed` and `gawk` in `PATH`, together with `tasklist` and `typeperf` from Windows.

### Sybase login

Each check reads ASE system tables or runs an ASE stored procedure. The login needs access to the objects of the checks you enable:

| Check | Reads |
| --- | --- |
| `Sybase Databases in <server>` | `sp_helpdb` |
| `Sybase Max Size Available`, `Sybase Used Size global`, `Used size<database>` | `master..sysdatabases`, `master..sysusages`, `curunreservedpgs`, `@@maxpagesize` |
| `Sybase Connections Used Ratio`, `Sybase Connections Remaining` | `master..sysprocesses`, `master..syslogins`, `sp_configure 'number of user connections'` |
| `Sybase Num Blocked Processes` | `sp_who` |
| `Sybase Blocker Processes` | `master..sysprocesses` |
| `Sybase Engines Offline` | `master..sysengines` |
| `Sybase Suspect Databases` | `master..sysdatabases` |
| `Sybase Mirror Devices` | `master..sysdevices` |
| `Sybase Locks Remaining` | `sysconfigures`, `syslocks` |
| `Sybase Suspect Index` | `sysindexes` |
| `Log Space Used <database>` | `sp_helpsegment logsegment` |
| `Sybase Segment space [<segment>][<database>]` | `sp_helpsegment` |

No official source defines a narrower grant list than these reads; grant only what the checks you enable need, and use a dedicated login for Pandora FMS.

The password is stored in the configuration file in plain text and passed to `isql` on its command line, so it is visible in the host process list while a query runs. Restrict the configuration file to the account that runs the agent and use a dedicated Sybase login.

### Install the addon

Download the addon from its Marketplace entry. The entry distributes the executable `pandorafms.sybase.1.0.exe`: copy it to the plugins directory of the Pandora FMS agent on the ASE host, for example `C:\Program Files\Pandora_Agent\plugins\`, and create the `pandora_sybase.conf` configuration file next to it. The complete file is documented in [Example configuration](#example-configuration).

## Configure

### Configuration file

The plugin receives its configuration file as its only positional argument:

```bat
pandorafms.sybase.1.0.exe <PATH_TO_CONFIG>
```

The file is plain text with one `key = value` per line. Blank lines and lines that start with `#` are skipped, keys and values are trimmed, and when a key is repeated the last value wins.

Every scalar key can also be overridden on the command line without editing the file, with `-key value` pairs after the file path:

```bat
pandorafms.sybase.1.0.exe <PATH_TO_CONFIG> -debug 1 -username <USERNAME>
```

The per-target lists and the thresholds are read only from the file: passing them as flags has no effect (see [Command-line execution](#command-line-execution)).

### Connection settings

These keys identify the client environment and the main login:

```ini
GLOBAL_SERVERNAME = <ASE_SERVER_NAME>
sybase_env_script = /opt/sybase/SYBASE.sh
isql = isql
encryption = 0

username = <USERNAME>
password = <PASSWORD>
servername = <ASE_SERVER_NAME>
port = 5000
```

- `GLOBAL_SERVERNAME` identifies the local Adaptive Server. It must appear in the command line of the local `dataserver` process, because the two status modules look for that process by this value.
- `sybase_env_script` is the Sybase environment script. The plugin requires the file to exist on every platform and stops with `Error, cannot found sybase environment script at [...]` and exit status `1` when it does not. On Unix-like systems it is sourced before each `isql` call, so it must be safe to source in a non-interactive shell. On Windows it is not sourced, and the Sybase environment must already be present in the environment of the Pandora FMS agent.
- `isql` is the command or full path of the Sybase `isql` utility. The default, `isql`, resolves it from `PATH`.
- `encryption = 1` adds the `-X` option to the `isql` invocation, which requests an encrypted connection. It requires the Sybase client to be configured for it.
- `username` and `password` are the login used by every check that does not define its own credentials.
- `servername` and `port` are passed to `isql` as `-S <servername>:<port>`. When the `port` key is absent, only the server name is passed.

### Per-database checks and login checks

Three numbered lists add checks on top of the server-wide modules. Each entry has a numeric suffix and its own format:

| List | Format | Generated module |
| --- | --- | --- |
| `check_dbsizeNN` | `<database>` | Used percentage, log space, availability, and one segment module per segment of that database |
| `check_instanceNN` | `<user>;<password>;<database>` | `Sybase Instance '<database>' availability` |
| `custom_checkNN` | `<user>;<password>;<database>` | `Sybase Login check <database>` |

```ini
check_dbsize01 = <DB_NAME>
check_instance01 = <USERNAME>;<PASSWORD>;<DB_NAME>
custom_check01 = <USERNAME>;<PASSWORD>;<DB_NAME>
```

- The suffix only distinguishes entries; the reference file numbers them from `01` upward. There is no total-count key: every entry present in the file is read.
- Two entries that name the same database produce a single set of modules.
- The third field of `check_instanceNN` and `custom_checkNN` is a **database** name, not an ASE server name: the plugin logs in to that database to test the credentials. The reference configuration file labels that field as an instance.
- `check_dbsizeNN` entries use the main `username` and `password`, never their own.
- The per-database modules of `check_dbsizeNN`, and the `check_instanceNN` modules, are generated only when the main login succeeds (see [Understand the results](#understand-the-results)). `custom_checkNN` modules are generated even when it fails.

### Enable the modules you need

Every server-wide and local module has its own switch. The value `1` enables the module; `0`, an empty value or a missing key disables it. All switches are disabled by default, so the configuration file states explicitly which modules you want:

```ini
sybase_main_status = 1
sybase_backup_status = 1
sybase_memuse = 1
sybase_cpuusage = 1
sybase_count_databases = 1
sybase_max_size = 1
sybase_used_size = 1
sybase_connections_used_ratio = 1
sybase_available_connections = 1
sybase_blocked_processes = 1
sybase_offline_engines = 1
sybase_suspects_databases = 1
```

The full list, with the module each switch enables, is in [Module switches](#module-switches).

### Register the plugin in the agent

The Pandora FMS agent executes agent plugins declared in its configuration file, `pandora_agent.conf`. Add one `module_plugin` line with the executable and the configuration file:

```ini
module_plugin "C:\Program Files\Pandora_Agent\plugins\pandorafms.sybase.1.0.exe" "C:\Program Files\Pandora_Agent\plugins\pandora_sybase.conf"
```

Restart the agent after the change. The agent executes the plugin at every agent interval and ingests the modules it prints, so the module interval is the interval of the agent that holds them. When the agent configuration is managed from the console, add the same line through the console instead of editing the file on the host.

Only one agent should run the plugin for a given ASE server: two agents executing it against the same server create two separate sets of modules.

### Credentials and transport

- The configuration file holds the main password and the password of every `check_instanceNN` and `custom_checkNN` entry in plain text. Restrict its permissions to the account that runs the agent.
- Every query passes the password to `isql` as a command-line argument, so the password is visible in the process list of the host while a query runs. Keep the credentials in the configuration file: a `-username` or `-password` override typed on the command line also remains in the shell history of the host.
- `encryption = 1` adds `-X` to every `isql` call, which asks the Sybase client for an encrypted connection. Confirm that the client and the server are configured for it before enabling the option; otherwise the login checks fail.

## Verify

Run the plugin manually, passing the configuration file as its only positional argument:

```bat
pandorafms.sybase.1.0.exe <PATH_TO_CONFIG>
```

A successful run prints one XML `<module>` block per generated module on standard output and exits with status `0`. The excerpt below shows four of them; the values are illustrative:

```xml
<module>
	<name><![CDATA[Sybase ASE status]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[The status of the Adaptive Server]]></description>
</module>
<module>
	<name><![CDATA[Sybase Memory Use]]></name>
	<type>generic_data</type>
	<data><![CDATA[120.63]]></data>
	<description><![CDATA[Sybase memory use in MB]]></description>
	<unit><![CDATA[MB]]></unit>
</module>
<module>
	<name><![CDATA[Sybase Database <DB_NAME> availability]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[Availability for <DB_NAME>]]></description>
</module>
<module>
	<name><![CDATA[Log Space Used <DB_NAME>]]></name>
	<type>generic_data</type>
	<data><![CDATA[18.40]]></data>
	<unit><![CDATA[%]]></unit>
</module>
```

- `pandorafms.sybase.1.0.exe -h` prints the usage summary and exits with status `0`. The summary goes to standard error, not standard output, and `-h` is recognised only as the first argument.
- A run that cannot find the environment script prints `Error, cannot found sybase environment script at [...]` on standard error, followed by the usage summary, and exits with status `1`.
- A run whose queries fail still exits with status `0`: the failing modules are simply missing from the output. Use `debug = 1` to see the reason (see [Operate and troubleshoot](#operate-and-troubleshoot)).

Once the agent is restarted, the modules appear in the console under the endpoint's agent:

<!-- SCREENSHOT NEEDED: Agent module list in the Pandora FMS console after a successful Sybase plugin run, showing the local and server-wide modules. -->

## Understand the results

The modules fall into four groups:

- **Local host.** `Sybase ASE status` and `Sybase ASE Backup server status` report `1` while the local `dataserver` and `backupserver` processes are running, and `0` otherwise. They are process checks, not connectivity checks: they say nothing about whether `isql` can reach the server. `Sybase Memory Use` and `Sybase CPU Busy` describe the local Adaptive Server process.
- **Server-wide.** `Sybase Databases in <server>`, `Sybase Max Size Available`, `Sybase Used Size global`, `Sybase Connections Used Ratio`, `Sybase Connections Remaining`, `Sybase Num Blocked Processes`, `Sybase Blocker Processes`, `Sybase Engines Offline`, `Sybase Suspect Databases`, `Sybase Mirror Devices`, `Sybase Locks Remaining`, `Sybase Suspect Index` and `Used size all databases` are read with SQL from the configured server.
- **Per database.** Every `check_dbsizeNN` entry adds `Used size<database>`, `Log Space Used <database>`, `Sybase Database <database> availability` and one `Sybase Segment space [<segment>][<database>]` module per segment of the database.
- **Login checks.** Every `check_instanceNN` entry adds an availability module and every `custom_checkNN` entry adds a login check module, both reporting `1` when the login succeeds and `0` otherwise.

**The main login gates the SQL modules.** Before the server-wide checks, the plugin logs in with `username` and `password`. When that login fails, the server-wide modules and the `check_dbsizeNN` and `check_instanceNN` modules are not generated at all, and no module reports the failure; only the local modules and the `custom_checkNN` checks still appear. Use `debug = 1` to see the `isql` error.

**Thresholds.** Numeric modules carry the warning and critical thresholds defined in the configuration file under `thresholds.<key>.<wmin|wmax|cmin|cmax>`; Pandora FMS evaluates them as any other module threshold. See [Thresholds](#thresholds) for the keys and the reference values.

**Order.** The modules generated from `check_dbsizeNN`, `check_instanceNN` and `custom_checkNN` are not emitted in configuration order and their order varies between runs.

## Operate and troubleshoot

The plugin keeps no state between runs: every execution queries the server and the local process list at that moment, so it can be executed manually at any time without affecting the next scheduled run.

Set `debug = 1` to publish diagnostics on standard error. Every message is prefixed with a timestamp, and the channel reports the `isql` error text and the segment parsing failures; without it the plugin stays silent about failed queries.

### Known limitations

These behaviours belong to the current version:

- **Error-log modules.** `sybase_errorlog_size`, `sybase_errorlog` and `sybase_errorlog_updates` exist as switches, but no configuration key sets the Sybase log directory in this version. The size module reports `0.00`, the path module reports an empty value and the update counter receives no directory, so leave the three switches disabled.
- **`sybase_logsize`.** The reference configuration file sets this key, but no check reads it.
- **Per-database percentage name.** The module concatenates the prefix and the database name without a separating space: a database named `master` produces `Used sizemaster`.
- **Per-database percentages.** `sybase_used_size_percent` enables only `Used size all databases`; the per-database percentages are created by `check_dbsizeNN`.
- **Memory unit.** `Sybase Memory Use` publishes the value with unit `MB`; on Unix-like systems the value is the sum of the `%MEM` column of the process list.
- **No failure module.** A failing main login leaves no module behind; diagnose it with `debug = 1`.

### Common failures

- **`Error, cannot found sybase environment script at [...]` and exit status `1`** — `sybase_env_script` is empty or does not name an existing file. Point it at the Sybase environment script of the host, for example `C:\SAP\...\SYBASE.bat` on Windows or `/opt/sybase/SYBASE.sh` on Unix-like systems. The plugin requires the file even on Windows, where it does not source it.
- **The plugin prints the usage summary and no module XML** — `-h` was passed as the first argument, or the configuration file path does not exist. A path that does not exist is not reported as a missing file: it is read as a configuration override, and the run then stops with the environment-script error.
- **No server-wide module appears, but the local modules do** — the main login failed, so every SQL module was skipped. Run with `debug = 1` and check the `isql` error: wrong `username` or `password`, a `servername` or `port` that does not resolve, or a login without access to the catalogs.
- **`Sybase ASE status` is `0` while the server is running** — `GLOBAL_SERVERNAME` does not appear in the command line of the local `dataserver` process. Set it to the name that the process reports.
- **`Sybase Memory Use` and `Sybase CPU Busy` report `0`** — the plugin is not running on the host of the ASE server, or the local account cannot see the server process in the process list.
- **A `check_dbsizeNN` database has no modules** — the main login failed, or the database name in the entry does not exist. A missing database produces the availability module with value `0`; the segment modules are then omitted and, with `debug = 1`, the segment parsing error is reported.
- **`Sybase Segment space [...]` modules are missing for a database** — system databases `sybsystemprocs`, `sybsystemdb`, `model` and `tempdb` are skipped by design, and a database whose segments cannot be read produces no segment module.
- **`Used size<database>` or `Log Space Used <database>` reports `0`** — the login cannot read `master..sysusages` or run `sp_helpsegment`, or the database does not exist.
- **The error-log modules report `0.00`, an empty path or nothing** — this version does not read the Sybase log directory from the configuration, so `sybase_errorlog_size`, `sybase_errorlog` and `sybase_errorlog_updates` cannot produce a value. Leave them disabled; see [Known limitations](#known-limitations).
- **The modules are not in the console** — check that the `module_plugin` line points to the executable and the configuration file, that the agent was restarted, and that the agent can execute the file. The agent log records the execution result.

## Reference

### Configuration file

The file uses `key = value` lines. Blank lines and lines that start with `#` are skipped, keys and values are trimmed, and the last occurrence of a repeated key wins. Numbers are read as text, so write `1` to enable a switch and `0` to disable it.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `GLOBAL_SERVERNAME` | Yes | — | Name of the local Adaptive Server. It must appear in the command line of the local `dataserver` process and it is used in the error-log module name. |
| `sybase_env_script` | Yes | Empty | Sybase environment script. Sourced before every `isql` call on Unix-like systems; the file must exist on every platform. |
| `isql` | No | `isql` | Command or full path of the Sybase `isql` utility. |
| `encryption` | No | `0` | `1` adds the `-X` option to every `isql` call. |
| `username` | Yes | — | Login for the main checks and for `check_dbsizeNN`. |
| `password` | Yes | — | Password of `username`. |
| `servername` | Yes | — | ASE server name, passed to `isql` with `-S`. |
| `port` | No | Absent (no port) | Port passed to `isql` as `<servername>:<port>`. When the key is absent, only the server name is passed. |
| `debug` | No | `0` | `1` prints timestamped diagnostics on standard error. |
| `check_dbsizeNN` | No | — | `<database>`. Adds the used percentage, log space, availability and segment modules of that database. |
| `check_instanceNN` | No | — | `<user>;<password>;<database>`. Adds `Sybase Instance '<database>' availability`. |
| `custom_checkNN` | No | — | `<user>;<password>;<database>`. Adds `Sybase Login check <database>`. |
| `grep_log` | No | Empty | Path of the `grep_log` helper used by the error-log update check. That check cannot produce a value in this version. |
| `custom_error_terms` | No | Built-in term list | Regular expression of terms counted by the error-log update check. |

### Module switches

| Key | Module enabled |
| --- | --- |
| `sybase_main_status` | `Sybase ASE status` |
| `sybase_backup_status` | `Sybase ASE Backup server status` |
| `sybase_memuse` | `Sybase Memory Use` |
| `sybase_cpuusage` | `Sybase CPU Busy` |
| `sybase_count_databases` | `Sybase Databases in <server>` |
| `sybase_max_size` | `Sybase Max Size Available` |
| `sybase_used_size` | `Sybase Used Size global` |
| `sybase_used_size_percent` | `Used size all databases`; the per-database percentages come from `check_dbsizeNN` |
| `sybase_connections_used_ratio` | `Sybase Connections Used Ratio` |
| `sybase_available_connections` | `Sybase Connections Remaining` |
| `sybase_blocked_processes` | `Sybase Num Blocked Processes` |
| `sybase_blocker_processes` | `Sybase Blocker Processes` |
| `sybase_offline_engines` | `Sybase Engines Offline` |
| `sybase_suspects_databases` | `Sybase Suspect Databases` |
| `sybase_mirror_devices` | `Sybase Mirror Devices` |
| `sybase_locks_remaining` | `Sybase Locks Remaining` |
| `sybase_suspect_index` | `Sybase Suspect Index` |
| `sybase_errorlog_size` | `Error Log Size`; cannot produce a value in this version |
| `sybase_errorlog` | `Sybase ErrorLog path`; cannot produce a value in this version |
| `sybase_errorlog_updates` | Error-log update counter; cannot produce a value in this version |

The reference configuration file enables twelve of these switches and also sets `sybase_logsize`, a key that no check reads. To enable the error-log size module, use `sybase_errorlog_size`.

### Thresholds

Each numeric module publishes the thresholds defined for its key. A key whose value is empty leaves the threshold unset; `0` is a real value. These are the values in the reference configuration file:

| Key | Module | `wmin` | `wmax` | `cmin` | `cmax` |
| --- | --- | --- | --- | --- | --- |
| `sybase_used_size` | `Used size<database>` | `90` | `95` | `95` | `100` |
| `sybase_used_size_all` | `Used size all databases` | `85` | `90` | `90` | `100` |
| `sybase_memuse` | `Sybase Memory Use` | — | — | — | — |
| `sybase_cpuusage` | `Sybase CPU Busy` | — | — | `90` | `100` |
| `sybase_connections_used_ratio` | `Sybase Connections Used Ratio` | `85` | — | `90` | — |
| `sybase_available_connections` | `Sybase Connections Remaining` | `5` | `15` | `0` | `5` |
| `sybase_blocked_processes` | `Sybase Num Blocked Processes` | `0` | `0` | `1` | `0` |
| `sybase_blocker_processes` | `Sybase Blocker Processes` | `0` | `0` | `1` | `0` |
| `sybase_offline_engines` | `Sybase Engines Offline` | `0` | `0` | `1` | `0` |
| `sybase_suspects_databases` | `Sybase Suspect Databases` | `0` | `0` | `1` | `0` |
| `sybase_locks_remaining` | `Sybase Locks Remaining` | `50` | `100` | `0` | `50` |
| `sybase_segment_space` | `Sybase Segment space [...]` | `80` | `0` | `90` | `0` |
| `sybase_suspect_index` | `Sybase Suspect Index` | `0` | `0` | `1` | `0` |
| `sybase_errorlog_size` | `Error Log Size` | `100` | — | `250` | — |

The threshold keys have no effect on modules that do not publish thresholds, such as `Sybase Max Size Available` and `Sybase Used Size global`.

### Command-line execution

```bat
pandorafms.sybase.1.0.exe [config-file] [-key value ...]
```

| Condition | Behavior |
| --- | --- |
| The first argument is `-h` | Prints the usage summary on standard error and exits with status `0` |
| No argument at all | Prints the environment-script error and the usage summary on standard error and exits with status `1` |
| The first argument names an existing file | Runs with that file and the remaining flags |
| The first argument names a file that does not exist | Treats the path as a configuration override and stops with the environment-script error; exit status `1` |
| `-key value` | Overrides the configuration value with the same key |
| `-key=value` | Not an override: the whole token becomes a configuration key and has no effect |
| An odd trailing argument | Ignored |
| `check_dbsizeNN`, `check_instanceNN`, `custom_checkNN` or `thresholds.*` as a flag | No effect; these are read only from the configuration file |

The plugin leaves the exit status at `0` when individual queries fail, and reports the failure only through the missing modules and the `debug = 1` diagnostics.

### Generated modules

In the names below, `<server>` is the value of `servername`, `<database>` a database of a `check_dbsizeNN` entry and `<segment>` a segment of that database:

| Module name | Type | Enabled by | Meaning |
| --- | --- | --- | --- |
| `Sybase ASE status` | `generic_proc` | `sybase_main_status` | `1` while the local `dataserver` process matching `GLOBAL_SERVERNAME` runs, `0` otherwise |
| `Sybase ASE Backup server status` | `generic_proc` | `sybase_backup_status` | `1` while the local `backupserver` process matching `GLOBAL_SERVERNAME` runs, `0` otherwise. On Windows the process is `bcksrvr.exe` |
| `Sybase Memory Use` | `generic_data`, unit `MB` | `sybase_memuse` | Memory used by the local Adaptive Server process, as reported by the process list |
| `Sybase CPU Busy` | `generic_data`, unit `%` | `sybase_cpuusage` | CPU used by the local Adaptive Server process |
| `Sybase Databases in <server>` | `generic_data` | `sybase_count_databases` | Databases listed by `sp_helpdb`, excluding those marked `dbo use only` |
| `Sybase Max Size Available` | `generic_data`, unit `MB` | `sybase_max_size` | Space allocated to all databases, excluding log segments |
| `Sybase Used Size global` | `generic_data`, unit `MB` | `sybase_used_size` | Used space of all databases, excluding log segments |
| `Used size all databases` | `generic_data`, unit `%` | `sybase_used_size_percent` | Used percentage of the space allocated to all databases; `0` when the allocated size cannot be read |
| `Sybase Connections Used Ratio` | `generic_data`, unit `%` | `sybase_connections_used_ratio` | User connections in use against the configured maximum |
| `Sybase Connections Remaining` | `generic_data` | `sybase_available_connections` | Configured maximum minus the connections in use |
| `Sybase Num Blocked Processes` | `generic_data` | `sybase_blocked_processes` | `sp_who` entries in `lock sleep` state |
| `Sybase Blocker Processes` | `generic_data` | `sybase_blocker_processes` | Processes holding locks and blocking other processes |
| `Sybase Engines Offline` | `generic_data` | `sybase_offline_engines` | Engines reported as offline in `master..sysengines` |
| `Sybase Suspect Databases` | `generic_data` | `sybase_suspects_databases` | Databases with status `256` or `320` |
| `Sybase Mirror Devices` | `generic_data` | `sybase_mirror_devices` | Devices configured for mirroring that are not currently mirrored |
| `Sybase Locks Remaining` | `generic_data` | `sybase_locks_remaining` | Configured locks minus the locks in `syslocks` |
| `Sybase Suspect Index` | `generic_data` | `sybase_suspect_index` | Indexes marked as suspect |
| `Used size<database>` | `generic_data`, unit `%` | `check_dbsizeNN` | Used percentage of the space allocated to the database |
| `Log Space Used <database>` | `generic_data`, unit `%` | `check_dbsizeNN` | Used percentage of the transaction log segment of the database |
| `Sybase Database <database> availability` | `generic_proc` | `check_dbsizeNN` | `1` when `isql` logs in to the database, `0` otherwise |
| `Sybase Segment space [<segment>][<database>]` | `generic_data`, unit `%` | `check_dbsizeNN` | Used percentage of each segment of the database |
| `Sybase Instance '<database>' availability` | `generic_proc` | `check_instanceNN` | `1` when the entry credentials log in to the database, `0` otherwise |
| `Sybase Login check <database>` | `generic_proc` | `custom_checkNN` | `1` when the entry credentials log in to the database, `0` otherwise |

### Example configuration

```ini
# Local server identification
GLOBAL_SERVERNAME = <ASE_SERVER_NAME>

# Sybase client environment
sybase_env_script = /opt/sybase/SYBASE.sh
isql = isql
encryption = 0

# Main login
username = <USERNAME>
password = <PASSWORD>
servername = <ASE_SERVER_NAME>
port = 5000

# Per-database checks
check_dbsize01 = <DB_NAME>

# Login checks
custom_check01 = <USERNAME>;<PASSWORD>;<DB_NAME>

# Modules
sybase_main_status = 1
sybase_backup_status = 1
sybase_memuse = 1
sybase_cpuusage = 1
sybase_count_databases = 1
sybase_max_size = 1
sybase_used_size = 1
sybase_connections_used_ratio = 1
sybase_available_connections = 1
sybase_blocked_processes = 1
sybase_offline_engines = 1
sybase_suspects_databases = 1

# Thresholds
thresholds.sybase_used_size.wmin = 90
thresholds.sybase_used_size.wmax = 95
thresholds.sybase_used_size.cmin = 95
thresholds.sybase_used_size.cmax = 100
thresholds.sybase_segment_space.wmin = 80
thresholds.sybase_segment_space.cmin = 90
```

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.sybase` |
| Name | Sybase |
| Version | `1.0` |
| Marketplace last update | 2026-05-25 |
| Distributed file | `pandorafms.sybase.1.0.exe` |
| License | Free download |
| Author | Pandora FMS |
