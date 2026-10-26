# PostgreSQL monitoring plugin

*Article last updated: 2026-10-26.*

<!-- DRAFT: Facts verified against the addon package definition and the distributed executable's documented surface. No live run, database connection or console capture was performed for this page. -->

## What it does

The PostgreSQL monitoring plugin turns your own SQL queries into Pandora FMS modules. Each run connects to a PostgreSQL server, executes every query listed in a configuration file and builds one module per query. It is a server plugin: Pandora FMS executes it on a server, or you run it manually from a terminal.

The plugin is query-driven. It does not ship a fixed PostgreSQL metric model: the example configuration supplied with the addon queries connections, roles, version, locks, commits, rollbacks and tuple counters, and you can replace those queries with your own `SELECT` statements.

A run executes every query in the file once, then delivers the result in one of three ways:

- **Agent data file** (default): the plugin writes an agent data XML file into the Pandora FMS data directory and prints `1`.
- **Tentacle**: with `--tentacle_address`, the plugin writes the same file, sends it with `tentacle_client` and then prints `1`.
- **Module XML on standard output**: with `--as_agent_plugin 1`, the plugin prints one `<module>` block per query on standard output and writes no file.

The plugin keeps no state between runs, so the values it publishes are the values PostgreSQL returns at execution time.

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
|-------|-------|----------|
| Network access from the machine that runs the plugin to the PostgreSQL listener (TCP, `--port`, `5432` by default) | `Required` | The connection parameters `-i` and `--port` |
| A PostgreSQL role able to read `pg_stat_activity`, `pg_roles`, `pg_locks`, `pg_stat_database` and `pg_database` | `Required` | The example queries shipped with the addon |
| PostgreSQL 9.6 or later while the shipped `wait_event` queries are kept | `Required` | `pg_stat_activity.wait_event` exists from PostgreSQL 9.6; on older servers those two queries fail and their modules are skipped |
| Pandora FMS Plugin Server enabled with the `plugin_exec` helper installed, when the plugin is registered in Pandora FMS | `Required` | Pandora FMS runs plugin modules through the Plugin Server |
| A Pandora FMS data directory writable by the user that runs the plugin, for file and Tentacle delivery | `Required` | `--data_dir`, `/var/spool/pandora/data_in/` by default |
| Operating system and distribution of the host that runs the plugin | `Not validated` | No operating system has been recorded for version `1.1` |
| PostgreSQL server releases | `Not validated` | No PostgreSQL version matrix has been recorded for this addon |
| Specific Pandora FMS versions | `Not validated` | No version matrix has been recorded for this addon |
| Tentacle delivery | `Not validated` | `--tentacle_address` needs a reachable `tentacle_client`; no such run has been recorded |

The Marketplace record states that this plugin is no longer actively maintained and recommends an alternative plugin for new deployments. The record also limits the download to licensed users; see [Addon identity](#addon-identity).

### Prerequisites

1. **Connectivity** between the machine that runs the plugin and the PostgreSQL server. When the plugin runs as a server plugin, that machine is the Pandora FMS server that executes the module, which may be a remote server.
2. **A PostgreSQL role and password** for monitoring. The shipped queries read cluster-wide views, so a role that only sees its own sessions undercounts the connection modules: to see every session, use a superuser or, in PostgreSQL 10 and later, a role with `pg_read_all_stats`.
3. **A Pandora FMS installation** with the Plugin Server enabled, the console to register the plugin and create the module, and a writable data directory for the delivery mode you choose.
4. **The query file**. The addon supplies an example; you can edit it or write your own. See [Query configuration file](#query-configuration-file).

### Install the addon

Download the `.pspz2` package from the Marketplace entry, which is limited to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.postgresql_plugin](https://marketplace.pandorafms.com/entries/pandorafms.postgresql_plugin)

Register it in the console:

1. Open **Servers → Register plugin** and upload the `.pspz2` file with **Upload file**.
2. Pandora FMS unpacks the package into the console's plugin attachment store, registers the plugin **Pandora PostgreSQL** with a maximum timeout of 20 seconds and 10 macros, and points the plugin command at the installed executable.
3. A package whose plugin name is already registered is rejected with `Plugin already registered. Aborting!`.

<!-- SCREENSHOT NEEDED: Plugin registration screen with a plugin package selected and no plugin data yet loaded. -->

The executable is named `pandora_postgresql`. If you prefer to register the plugin by hand instead of importing the package, place the executable on the Pandora FMS server and enter its absolute path as the plugin command; the parameters and macros are the ones in [Register the server plugin](#register-the-server-plugin).

## Configure

### Register the server plugin

A plugin registered this way is available when creating plugin modules, and each module fills the macros individually. The packaged definition uses this parameter string:

```text
-d _field1_ -u _field2_ -p _field3_ -i _field4_ --port _field5_ --conf _field6_ --agent_name _field7_ --prefix_module _field8_ -g _field9_ _field10_
```

The packaged definition wraps every macro in quotes. When you register the plugin manually, use the unquoted form above so each value reaches the executable without surrounding spaces.

| Field | Description | Example value |
|-------|-------------|---------------|
| `_field1_` | Database name | `<DB_NAME>` |
| `_field2_` | PostgreSQL user | `<USERNAME>` |
| `_field3_` | Password for that user | `<PASSWORD>` |
| `_field4_` | PostgreSQL host or IP address | `<TARGET_HOST>` |
| `_field5_` | Database port; `5432` by default | `5432` |
| `_field6_` | Absolute path to the query file | `<PATH_TO_CONFIG>` |
| `_field7_` | Agent name; `_agentname_` by default | `_agentname_` |
| `_field8_` | Module name prefix | `<DB_NAME>` |
| `_field9_` | Destination group; `Postgres` by default | `<GROUP_NAME>` |
| `_field10_` | Extra raw arguments, appended at the end | `--data_dir /var/spool/pandora/data_in/` |

Two packaged defaults need attention before the first run:

- **The password macro is not hidden.** The package imports `_field3_` as a visible macro, so the password you enter is stored unencrypted and shown in the macro list. Enable the macro's **Hide value** option, which stores the value as a hidden, encrypted macro, and set the password afterwards.
- **The prefix default is a single dot.** The plugin joins the prefix to the module name with an underscore, so leaving the packaged `.` produces names such as `._number_connections`. Replace it with a meaningful prefix such as the database name, or clear it.

<!-- SCREENSHOT NEEDED: Macro list of the registered Pandora PostgreSQL plugin with a lab database, user, masked password, host, port, configuration path, agent name, prefix, group and no real credentials. -->

### Query configuration file

The file is plain text with one query per line and four colon-separated fields:

```text
module_name:SELECT ...:module_type:description
```

- The description is optional. A line with fewer than three fields stops the run before any module is produced, with `It is mandatory to specify name, query and type!`.
- Any line containing `#` is ignored, and empty lines are ignored. Use comments on their own line.
- The module name is written as the Pandora FMS module name, with the prefix from `--prefix_module` in front of it.
- The module type is written into the module definition as it appears. Use Pandora FMS module types: `generic_data`, `generic_data_inc`, `generic_data_string` or `generic_proc`.
- `_database_` in a query is replaced by the database name given with `-d`, quoted with single quotes, so `WHERE db.datname = _database_` becomes `WHERE db.datname = '<DB_NAME>'`.
- The whole line is split on every colon. Do not use `:` inside the statement, including `::` casts and time literals: the query is truncated and the module fails.

Minimal example:

```text
number_connections:SELECT count(*) FROM pg_stat_activity;:generic_data:Number of sessions
database_size_mb:SELECT ROUND(pg_database_size(current_database())/1024/1024);:generic_data:Database size in MB
db_version:SELECT version();:generic_data_string:PostgreSQL version
commits:SELECT sum(xact_commit) FROM pg_stat_database WHERE datname = _database_;:generic_data:Commits in the monitored database
```

Put the file where the user that runs the plugin can read it. The packaged default macro points to `/var/www/html/pandora_console/attachment/plugin/pandora_postgresql.conf`, next to the executable in a standard installation; change it to the path you actually use.

The addon executes every statement it finds. Keep the file to read-only `SELECT` statements, and verify each query manually before adding it to a production file.

### Create the plugin module

1. Open the agent that will hold the modules and create a module of type plugin.
2. Select the registered **Pandora PostgreSQL** plugin and fill the macros for the target database.
3. Save the module.

<!-- SCREENSHOT NEEDED: Plugin module creation form with the Pandora PostgreSQL plugin selected and its macros filled with lab values. -->

Every execution of a plugin module runs the whole query file and publishes all its modules. Create one plugin module per query file and database; several modules pointing at the same file repeat the same queries on every interval.

`_agentname_` resolves to the agent that owns the module, so in this mode the generated modules land in that agent instead of creating a separate one. Replace it with a literal name only when you want a different agent.

A plugin module stores the plugin's standard output as its value. Keep the default delivery mode, which writes the agent data file and prints `1`, so the module records `1` and the agent data file carries the metrics. Add `--as_agent_plugin 1` only when the module is meant to receive module XML.

### Credentials and transport

- The password is part of the plugin parameters. In a plugin module it lives in the stored macro; with a hidden macro value it is stored encrypted. Avoid passing `-p <PASSWORD>` in an interactive command line: the shell history and the process list can expose it while the plugin runs.
- The addon exposes no TLS parameters. Encryption and authentication of the database connection follow the PostgreSQL server and client configuration of the machine that runs the plugin.
- Use a dedicated PostgreSQL role for Pandora FMS and grant only what its queries need.

## Verify

Run the plugin manually on the Pandora FMS server, under the same user that executes plugin modules:

```bash
./pandora_postgresql -d <DB_NAME> -u <USERNAME> -p <PASSWORD> -i <TARGET_HOST> \
    --port 5432 --conf <PATH_TO_CONFIG> --agent_name PostgreSQL
```

The default mode writes an agent data file into `--data_dir` and prints `1`. A printed `0` means the run failed; see [Operate and troubleshoot](#operate-and-troubleshoot).

To inspect the generated modules without writing a file, add `--as_agent_plugin 1`. The plugin then prints one `<module>` block per query, for example:

```xml
<module>
	<name><![CDATA[number_connections]]></name>
	<type>generic_data</type>
	<datalist>
	<data>
		<value><![CDATA[12]]></value>
	</data>
	</datalist>
	<description><![CDATA[Number of sessions]]></description>
</module>
```

Values in the sample are illustrative. Once the plugin module runs on its interval, confirm in the console that the agent holds one module per query and that the plugin module itself reports `1`.

<!-- SCREENSHOT NEEDED: Agent module list after the first plugin run, showing the generated PostgreSQL modules and the plugin module value 1. -->

No live run, database connection or console ingestion was performed while writing this page. The steps above are operator checks, not observed results.

## Understand the results

A successful run produces one agent and one module per query:

| Property | Value |
|----------|-------|
| Agent name | `--agent_name`; `PostgreSQL` by default, `_agentname_` in the registered plugin |
| Agent description | `PostgreSQL agent` |
| Group | `--group`; `Postgres` by default |
| Interval | Empty in the agent definition; an agent that already exists keeps its own interval |
| Module name | The first field of the query line, prefixed with `<prefix>_` when `--prefix_module` is set |
| Module type | The third field of the query line, as written |
| Module description | The fourth field of the query line, empty when omitted |

Each module is emitted with a `<datalist>`: one entry per row returned by the query, with the columns of a row joined by `;`. A single-row, single-column query — a `count(*)`, for example — produces a list with one entry. Keep monitoring queries to one row and one column when you expect a single value.

The plugin does not set thresholds, units or alert templates. Thresholds and the module interval are configured in Pandora FMS on the generated module.

### Example queries

The example file supplied with the addon defines these queries:

| Module | Query | Notes |
|--------|-------|-------|
| `number_connections` | `SELECT count(*) FROM pg_stat_activity;` | Sessions in the whole cluster, all databases, including the monitoring session |
| `connections_waiting_in_locks` | `SELECT count(*) FROM pg_stat_activity WHERE wait_event = 'Lock';` | Sessions waiting on a heavyweight lock |
| `connections_idle_in_transaction` | `SELECT count(*) FROM pg_stat_activity WHERE wait_event = 'idle in transaction';` | Always `0`: `idle in transaction` is a session state, not a wait event, so the filter matches no row |
| `number_users` | `SELECT COUNT(usename) FROM pg_stat_activity;` | Sessions that have a user name, not distinct roles |
| `number_roles` | `SELECT count(*) FROM pg_roles;` | Roles in the cluster |
| `psql_version` | `SELECT version();` | Server version string |
| `num_blocks` | `SELECT COUNT(*) FROM pg_locks;` | Rows in `pg_locks`, that is current lock entries, not deadlocks |
| `number_commits` | `sum(xact_commit)` for the monitored database | Cumulative counter |
| `number_rollbacks` | `sum(xact_rollback)` for the monitored database | Cumulative counter |
| `tuples_returned` | `sum(tup_returned)` for the monitored database | Cumulative counter |
| `tuples_searched` | `sum(tup_fetched)` for the monitored database | Cumulative counter |
| `tuples_inserted` | `sum(tup_inserted)` for the monitored database | Cumulative counter |
| `tuples_updated` | `sum(tup_updated)` for the monitored database | Cumulative counter |
| `tuples_removed` | `sum(tup_deleted)` for the monitored database | Cumulative counter |
| `state` | `SELECT state FROM pg_stat_activity WHERE datname = _database_;` | One row per session of the database |
| `number_connections_list` | `SELECT * FROM pg_stat_activity;` | One row per session, columns joined by `;` |
| `number_databases_list` | `select * from pg_database;` | One row per database |

The counters use `generic_data`, so Pandora FMS stores the cumulative value returned by PostgreSQL. Define the module as `generic_data_inc` in the query file when you want the increment between runs instead.

A query that fails does not stop the run: the plugin writes the error to standard error and continues with the next query, so its module is missing for that execution while the others are still published.

## Operate and troubleshoot

- Every run opens one connection, executes the queries sequentially and closes the connection. There is no parallelism and no debug or verbose flag; the diagnostic channels are standard output, standard error and the exit status.
- When the plugin runs as a server plugin, Pandora FMS schedules it on the module interval. Run it manually only under the same user and with the same macros as the module.
- The package registers a maximum timeout of 20 seconds per execution, and Pandora FMS applies the lower of that value and the server's `plugin_timeout`. A query file with slow statements can hit the limit; keep the queries cheap.

| Signal | Cause and check |
|--------|-----------------|
| `the following arguments are required: -d/--database, -u/--user, -p/--password, -i/--ip, --conf` | A required argument is missing. The parser prints its usage and exits with status `2` |
| `Error while creating PostgreSQL table ...` followed by `Error: ...` and `0` | The connection failed: unreachable host or port, wrong database, wrong credentials, or `pg_hba.conf` rejecting the client. The first message is printed on standard output, the rest on standard error |
| `Error al conectarse ...` | The query file could not be opened. Check `--conf` and the permissions of the file for the user that runs the plugin |
| `error with the query:<query>.<error>` | PostgreSQL rejected one query. The remaining queries still run; fix the statement or the privileges of the role |
| `It is mandatory to specify name, query and type!` | A query line has fewer than three colon-separated fields. The run stops without producing modules |
| A module is missing while the others appear | Its query failed, its line is malformed, or it uses a column that does not exist in that PostgreSQL release |
| `ERROR - Could not write file: ..., please check directory permissions` | `--data_dir` does not exist or is not writable by the user that runs the plugin. The run exits with status `1` |
| `Tentacle error` or `Tentacle error: ...` and no `1` | Tentacle delivery failed: `tentacle_client` is missing or `--tentacle_address`/`--tentacle_port` are wrong. The data file stays in `--data_dir` |
| `0` printed instead of `1` | The run failed before generating modules; read the preceding messages |
| The module reports `1` but no data reaches Pandora FMS | The data file was written somewhere the Data Server does not read. Check `--data_dir` against the server's `incomingdir` |

The plugin exits with status `0` for a successful run and also for a run that failed after reading its arguments — a connection error, an unreadable query file or a malformed line — because those failures are reported by the printed `0` and the error messages, not by the exit status. Use the printed value and the message text, not the exit status alone, to judge a manual run.

## Reference

### Command line

```bash
./pandora_postgresql -d <DB_NAME> -u <USERNAME> -p <PASSWORD> -i <TARGET_HOST> [options]
```

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `-d`, `--database` | Yes | — | Database to connect to and the value substituted for `_database_` |
| `-u`, `--user` | Yes | — | PostgreSQL user |
| `-p`, `--password` | Yes | — | Password for that user. It is not the port |
| `-i`, `--ip` | Yes | — | PostgreSQL host or IP address |
| `--conf` | Yes | — | Path to the query configuration file |
| `--port` | No | `5432` | PostgreSQL port |
| `--agent_name` | No | `PostgreSQL` | Name of the agent written in the agent data file |
| `--prefix_module` | No | Empty | Prefix joined to every module name with `_` |
| `-g`, `--group` | No | `Postgres` | Group written in the agent definition |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directory where the agent data file is written |
| `--tentacle_address` | No | Empty | Tentacle server address. When set, the data file is sent with `tentacle_client` |
| `--tentacle_port` | No | `41121` | Tentacle server port |
| `--as_agent_plugin` | No | `0` | `1` prints the module XML on standard output; any other value writes the agent data file |
| `-h`, `--help` | No | — | Print the help and exit |

### Query file fields

| Position | Field | Required | Description |
|----------|-------|----------|-------------|
| 1 | Module name | Yes | Pandora FMS module name, without the prefix |
| 2 | Query | Yes | SQL statement executed as written, after `_database_` substitution |
| 3 | Type | Yes | Pandora FMS module type written into the module definition |
| 4 | Description | No | Module description; empty when omitted |

### Addon identity

| Property | Value |
|----------|-------|
| Marketplace identifier | `pandorafms.postgresql_plugin` |
| Name | PostgreSQL monitoring |
| Version | `1.1` |
| Marketplace last update | 2025-08-20 |
| Package | `pandorafms.postgresql_plugin.1.1.pspz2` |
| Registered plugin name | Pandora PostgreSQL |
| License | One; the download is limited to licensed users |
| Maintenance | The Marketplace record states the plugin is no longer actively maintained |
| Maximum execution timeout | 20 seconds |
