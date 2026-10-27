# Pandora Azure SQL plugin

*Article last updated: 2026-10-26.*

!!! warning "Discovery integration recommended"
    For new installations use [Azure SQL Discovery](../discovery/azure-sql.md), which is the recommended integration for this service. This plugin is the legacy path.

## What it does

The Pandora Azure SQL plugin turns the Azure Monitor metrics of one Azure SQL database into Pandora FMS modules. Each run authenticates in Microsoft Entra with a service principal, reads 23 metrics of the database over the last hour at five-minute resolution, and publishes them as a new agent with 23 modules.

The database is identified by its full Azure resource ID, which you write in a local configuration file together with the credentials. The plugin never opens a SQL connection: it reads the metrics Azure Monitor already stores for the resource, so nothing is installed on the database server and no port has to be reachable on it.

One run covers one database and produces one agent. Monitoring several databases means one execution per database, each with its own configuration file and its own agent name.

The addon supports the two execution models of a Pandora FMS plugin:

- **Server plugin mode** (default): each run builds the agent document and either copies it into the Pandora FMS data directory or sends it with Tentacle.
- **Agent plugin mode** (`--as_agent_plugin 1`): each run prints the module XML on standard output, for the Pandora FMS agent to ingest.

> **This page documents two different command lines.** The Marketplace record and the package's registration file describe only the metric collector, `pandora_azuresql`, which is the subject of this page. A second executable, `pandora_azuresqlquery`, runs SQL sentences against the same database over ODBC, with its own options, its own configuration format and its own output. The Marketplace record does not describe it and does not state whether your package contains it. It is documented separately in [The query runner](#the-query-runner) so that the two are never confused.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Marketplace addon `pandorafms.azuresql`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions. A general public statement that covers every entry, not a test record for this addon |
| An Azure SQL database, identified by its full resource ID | `Required` | The configuration file carries one `database_id` and every metric query is made against it. Prerequisite, not a compatibility statement |
| A Microsoft Entra service principal allowed to read that database resource and its metrics | `Required` | The plugin authenticates with a tenant, an application identifier and a client secret, and reads Azure Monitor metrics for the resource. No official source names a narrower role for this addon |
| HTTPS access to the public Azure endpoints | `Required` | The plugin has no endpoint option, so it authenticates and queries the public cloud only. Sovereign or custom clouds are `Not validated` |
| `tentacle_client` on the host that runs the plugin | `Required` when `--tentacle_address` is used | Tentacle delivery |
| Microsoft ODBC Driver 18 for SQL Server on the host that runs the plugin | `Required` when using the query runner | The query runner requests that driver by name and has no option to change it. See [The query runner](#the-query-runner) |
| Azure SQL service tier and edition | `Not validated` | Some metrics apply only to vCore-based or serverless databases, and others not at all to data warehouses. The plugin requests all 23 regardless of the tier |
| Operating system of the host that runs the plugin | `Not validated` | The legacy guide names CentOS 7, Fedora and Rocky Linux as tested and "any Linux" as expected. No test record supports either claim |

### Requirements

1. **An Azure SQL database** and its full resource ID.
2. **A Microsoft Entra service principal**: tenant identifier, application (client) identifier and a client secret.
3. **Read access for that service principal** to the database resource and to its Azure Monitor metrics. Grant read access on the smallest scope that covers the database.
4. **Outbound HTTPS** from the host that runs the plugin to the public Azure endpoints.
5. **Pandora FMS** to receive the output: the Pandora FMS server in server plugin mode, or the Pandora FMS agent of the monitored host in agent plugin mode.
6. **The Tentacle client (`tentacle_client`) available in `PATH`**, only when you deliver with `--tentacle_address`.

The metrics are read from Azure Monitor and never from the database itself, so the account that reads them is an Azure identity, not a database user.

### Install the plugin

Download the `pandorafms.azuresql.1.0.pspz2` package from the Marketplace entry:

[https://marketplace.pandorafms.com/entries/pandorafms.azuresql](https://marketplace.pandorafms.com/entries/pandorafms.azuresql)

Register the package from the Pandora FMS console plugin manager. The package carries a registration file that declares the plugin command and its three module fields, documented in [Register the plugin in the console](#register-the-plugin-in-the-console).

The executable can also be deployed on its own and run from a terminal or from a scheduler; see [Command-line execution](#command-line-execution).

### Prepare Azure access

1. **Create or select an application registration** in Microsoft Entra ID and generate a client secret for it.
2. **Record three values**: the tenant (directory) identifier, the application (client) identifier, and the secret **value**. Copy the value, not the secret identifier: the plugin sends it verbatim to the authentication endpoint.
3. **Grant the service principal read access** to the database resource and to its metrics.
4. **Copy the database's full resource ID.** It has this form:

```text
/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.Sql/servers/<SQL_SERVER>/databases/<DATABASE>
```

The plugin sends that string as the resource URI of every metric query, so it must be the **database** resource, not the server.

## Configure

The plugin takes its credentials and its target from one configuration file, and everything else from the command line. There is no precedence between the two: no delivery setting can be written in the file, and no credential can be passed as a flag.

### The configuration file

The file is mandatory and is passed with `-c`/`--conf`. It holds one `key:value` pair per line:

```ini
# Azure credentials
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
# Target database
database_id:/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.Sql/servers/<SQL_SERVER>/databases/<DATABASE>
```

The parser applies these rules:

- The separator is a **colon**, not an equals sign.
- Blank lines are skipped.
- **A line that contains `#` anywhere is skipped**, not only a line that starts with it. Do not append a comment to a value line.
- A value ends at the next colon: a client secret that itself contains `:` is truncated, and authentication fails.
- A repeated key keeps its last value.
- The four keys are matched by name. If one is missing, the run stops with a `NameError` traceback instead of a message naming the missing key.

The file holds the client secret in plain text. Restrict it to the account that runs the plugin (for example with `chmod 600`) and keep it out of shared directories and version control.

### Command-line execution

The minimum server-mode run, which writes the agent document into the Pandora FMS data directory:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG>
```

The same run delivered with Tentacle, with an explicit agent name and group:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG> \
    --agent_name <AGENT_NAME> -g <GROUP> \
    --tentacle_address <PANDORA_FMS_SERVER> --tentacle_port 41121
```

Agent plugin mode, which prints the module XML instead of building an agent:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG> --as_agent_plugin 1
```

The command line selects one of three output branches. `--tentacle_address` takes precedence over the mode option:

| Command line | What the run does |
| --- | --- |
| `--tentacle_address` is set, with or without `--as_agent_plugin` | Builds the agent document, sends it with `tentacle_client` and prints `1` |
| No `--tentacle_address`, and `--as_agent_plugin` is absent or not `1` | Builds the agent document, writes it into `--data_dir` and prints `1` |
| `--as_agent_plugin 1` and no `--tentacle_address` | Prints the module XML on standard output and writes no file |

Key points:

- **`--as_agent_plugin 1` selects agent plugin mode; the default is server plugin mode.** The option name is the inverse of the default, so confirm the mode before reading any output.
- **`--data_dir`, `--agent_name` and `-g` have no effect in agent plugin mode.** No file and no agent document are built, so the agent name and the group never reach Pandora FMS.
- **`--prefix_module` is accepted and ignored.** No module name receives a prefix in this collector; see [Generated modules](#generated-modules).
- The group is written by name into the agent document, so it must be a group that exists in the console. The registration file suggests `azuresql`; the built-in default is `Azure`.
- The agent document always declares agent mode `1` and an empty interval, so the interval is applied by the console, not by the plugin.
- The plugin keeps no state between runs, so any execution can be repeated manually.

### Register the plugin in the console

1. Open **Servers → Plugins** and register the `pandorafms.azuresql.1.0.pspz2` package, or add the plugin manually with the path of the `pandora_azuresql` executable as its command.
2. The parameters already declared by the package are:

```text
-c " _field1_ " --agent_name " _field2_ " -g " _field3_ "
```

3. The package defines three fields:

| Field | Description in the package | Value to supply |
| --- | --- | --- |
| `_field1_` | `Conf path (obligatory)` | Absolute path of the configuration file on the Pandora FMS server |
| `_field2_` | `Agent name (optional)` | Name of the agent that will hold the 23 modules |
| `_field3_` | No definition in the package | Name of an existing Pandora FMS group |

!!! warning "The packaged parameters break the configuration path"
    Each macro is quoted with a space inside the quotes: `-c " _field1_ "`. After the console substitutes the field value, the argument keeps a leading and a trailing space, and the plugin opens that path without trimming it, so the run fails with `FileNotFoundError`. Remove the spaces when you register the plugin, for example `-c "_field1_" --agent_name "_field2_" -g "_field3_"`.

    The registration file declares `total_macros_provided = 3` but defines `[macro_1]`, `[macro_2]` and `[macro_4]`. There is no `[macro_3]`, so the third field, which the command line uses as `_field3_`, is the one the package leaves without a description, and the `group` definition is the one that is not used.

4. Give each field a value per module. The plugin module is only the trigger: in server plugin mode its own value is `1`, and the 23 metric modules land on the agent named by `--agent_name`, not on the agent that holds the trigger module.
5. Each plugin module executes on the Pandora FMS server selected for it, including a remote server, so several databases can be monitored from the server closest to each one without installing anything on the database host.

<!-- SCREENSHOT NEEDED: Registered plugin parameter screen in the Pandora FMS console, showing the three macro fields and which of them has a description. -->

## Verify

Run the plugin manually in agent plugin mode to see the output without publishing anything:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG> --as_agent_plugin 1
```

A successful run prints 23 `<module>` blocks on standard output. Every block is a `generic_data_string` module whose value is a `<datalist>` with one entry per data point of the last hour:

```xml
<module>
	<name><![CDATA[cpu_percent]]></name>
	<type>generic_data_string</type>
	<datalist>
	<data>
		<value><![CDATA[The cpu_percent at 2026-10-27 09:05:00+00:00 is 2.4]]></value>
	</data>
	<data>
		<value><![CDATA[The cpu_percent at 2026-10-27 09:10:00+00:00 is 3.1]]></value>
	</data>
	</datalist>
	<description><![CDATA[CPU percentage]]></description>
</module>
```

This excerpt shows the document structure the plugin produces; it was not captured from a live database.

Then run the plugin without `--as_agent_plugin` to deliver the agent:

```bash
./pandora_azuresql -c <PATH_TO_CONFIG> --agent_name <AGENT_NAME>
```

A successful server-mode run prints `1` and writes `<AGENT_NAME>.<epoch>.data` into the data directory, or sends it with Tentacle. Once the data server processes the file, the agent named `<AGENT_NAME>` appears in Pandora FMS with its 23 modules.

The plugin prints its usage summary with `./pandora_azuresql -h`.

<!-- SCREENSHOT NEEDED: Agent detail view in the Pandora FMS console listing the 23 modules generated by the plugin, with one datalist module expanded. -->

## Understand the results

### What each run publishes

One agent with 23 modules, always the same set, grouped by the part of the service they describe:

| Family | Modules |
| --- | --- |
| Compute | `cpu_percent`, `cpu_limit`, `cpu_used`, `sqlserver_process_core_percent`, `app_cpu_percent`, `app_cpu_billed` |
| Storage | `storage`, `storage_percent`, `allocated_data_storage` |
| I/O and log | `physical_data_read_percent`, `log_write_percent` |
| Connections and sessions | `connection_successful`, `connection_failed`, `blocked_by_firewall`, `sessions_percent`, `workers_percent`, `sqlserver_process_memory_percent`, `app_memory_percent` |
| TempDB and in-memory OLTP | `tempdb_data_size`, `tempdb_log_size`, `tempdb_log_used_percent`, `xtp_storage_percent` |
| Contention | `deadlock` |

### Why every module is a list of text

Each module is a `generic_data_string` whose value is a `<datalist>`, and each entry reads `The <metric> at <timestamp> is <value>`. This has consequences worth knowing before you build anything on top of the data:

- **The value is text, not a number.** Pandora FMS cannot plot the module as a numeric series or apply numeric thresholds to it, and the plugin sets no unit, interval or threshold on any module.
- **Every run republishes the whole last hour.** With a five-minute execution interval, each data point appears in the module value of 12 consecutive runs.
- **A point without a value is published as `None`.** Azure Monitor does not fill every point of every metric, and the plugin writes what it receives.
- **All 23 modules are created on every run**, including metrics the database does not report. Such a module appears with an empty `<datalist>`. An empty module is not proof of a failure.
- **The counters are averaged like the gauges.** `connection_successful`, `connection_failed`, `blocked_by_firewall` and `deadlock` are requested with the `Average` aggregation over the five-minute granularity, so the published numbers are per-interval averages, not totals.
- **There is no availability module.** Nothing in the output states whether the run could reach Azure. A failed run publishes nothing at all, and the missing data is the only signal.

### One agent per database

The agent name and the target database are both per-execution settings, so monitoring several databases means one configuration file per database (a different `database_id`) and one execution per database (a different `--agent_name`). Reusing the same agent name for two databases merges both sets of modules into one agent, and the second run overwrites the first.

### Compared with Azure SQL Discovery

[Azure SQL Discovery](../discovery/azure-sql.md) addresses the same service through a Discovery task. The differences that matter when choosing:

| | This plugin | Azure SQL Discovery |
| --- | --- | --- |
| Databases monitored | One, named by its resource ID in the configuration file | Every database of the subscription or Resource Group, or those matching the name filters |
| Agents | One agent per run, named with `--agent_name` | One agent per database, or a single target agent |
| Modules | 23 string datalists covering the last hour | Numeric modules, one per enabled metric family |
| Credentials | A plain-text file on the host that runs the plugin | The Pandora FMS credential store, referenced by the task |
| Configuration | Command-line flags | A Discovery task |
| Recommended for new installations | No | Yes |

## Operate and troubleshoot

- **23 sequential requests per run.** The package declares a plugin timeout of `20` seconds. On a slow connection, or when the client retries a request, the run can be cut before it finishes; force the module and check the timestamp of the agent data.
- **A successful server-mode run prints `1`.** That `1` is the value of the trigger module, not a summary of the delivery. With Tentacle, a failed transfer still prints `1`: the plugin ignores the result of the send and prints `1` unconditionally, and it leaves the `.data` file in `--data_dir` because it deletes the file only after a successful transfer. Check the agent data in the console, not the `1`.
- **The data file is opened in exclusive mode.** Two executions of the same agent name within the same second stop with `ERROR - Could not write file: ... please check directory permissions`, which is also the message for a real permission problem.
- **There is no debug mode.** Errors reach standard error as a traceback, and the messages below are the ones to look for.

| Symptom | Cause and action |
| --- | --- |
| The run ends with status `2` and a usage error on standard error | `-c` is missing. It is a required argument. |
| Traceback ending in `NameError` naming `tenant_id`, `client_id`, `secret` or `database_id` | The configuration file has no line for that key, or the line was skipped because it contains `#`. The plugin has no message for a missing key. |
| `FileNotFoundError` on the configuration path | The path is wrong, or it arrived with surrounding spaces from the packaged parameter template. See the warning in [Register the plugin in the console](#register-the-plugin-in-the-console). |
| `ERROR - Could not write file` | `--data_dir` is not writable by the plugin user, or another run of the same agent wrote in the same second. |
| `1` is printed but no agent appears in the console | With `--tentacle_address`, the transfer failed. Check the address, the port and the Tentacle server log. Without Tentacle, check that the data server is running and reading `--data_dir`. |
| Traceback from the authentication step | The tenant, the client identifier or the secret is wrong, the secret has expired, or the service principal has no read access to the resource. |
| Traceback naming a metric or an Azure response error | Azure rejected one of the 23 requests. The run has no error handling, so the execution stops and publishes nothing. Check the database tier and the resource ID. |
| A module shows only `None` values | Azure Monitor has no datapoints for that metric and that database. |
| `--prefix_module` is set but the module names are unchanged | The option has no effect in this collector. |

## Reference

### Command-line options

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `-c`, `--conf` | Yes | — | Path of the configuration file with the credentials and the database resource ID |
| `--agent_name` | No | `Azure_SQL` | Name of the agent created in Pandora FMS. Has no effect in agent plugin mode |
| `-g`, `--group` | No | `Azure` | Name of the Pandora FMS group assigned to the agent. Has no effect in agent plugin mode |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directory where the agent document is written. Has no effect in agent plugin mode |
| `--tentacle_address` | No | — | Address of the Tentacle server. When set, the agent document is sent and the other two delivery modes are ignored |
| `--tentacle_port` | No | `41121` | Tentacle server port |
| `--as_agent_plugin` | No | `0` | `1` prints the module XML on standard output. Any other value builds the agent document |
| `--prefix_module` | No | — | Accepted and ignored |
| `-h`, `--help` | No | — | Prints the usage summary and exits |

### Configuration file keys

| Key | Required | Description |
| --- | --- | --- |
| `tenant_id` | Yes | Microsoft Entra tenant (directory) identifier |
| `client_id` | Yes | Application (client) identifier of the service principal |
| `secret` | Yes | Client secret value |
| `database_id` | Yes | Full resource ID of the Azure SQL database |

The file uses `key:value` lines. See [The configuration file](#the-configuration-file) for the parsing rules, including the lines that are skipped.

### Generated modules

Every module is `generic_data_string` with a `<datalist>` of the datapoints of the last hour, sampled every five minutes. The plugin sets no unit and no threshold; the description is the text it writes into the module.

| Module name | Family | Description written by the plugin |
| --- | --- | --- |
| `cpu_percent` | Compute | CPU percentage |
| `cpu_limit` | Compute | CPU limit. Applies to vCore-based databases |
| `cpu_used` | Compute | CPU used. Applies to vCore-based databases |
| `sqlserver_process_core_percent` | Compute | CPU usage as a percentage of the SQL DB process. Not applicable to data warehouses |
| `app_cpu_percent` | Compute | App CPU percentage. Applies to serverless databases |
| `app_cpu_billed` | Compute | App CPU billed. Applies to serverless databases |
| `storage` | Storage | Data space used. Not applicable to data warehouses |
| `storage_percent` | Storage | Data space used percent. Not applicable to data warehouses or hyperscale databases |
| `allocated_data_storage` | Storage | Allocated data storage. Not applicable to data warehouses |
| `physical_data_read_percent` | I/O and log | Data IO percentage |
| `log_write_percent` | I/O and log | Log IO percentage. Not applicable to data warehouses |
| `connection_successful` | Connections | Successful connections |
| `connection_failed` | Connections | Failed connections |
| `blocked_by_firewall` | Connections | Blocked by firewall |
| `sessions_percent` | Connections | Sessions percentage. Not applicable to data warehouses |
| `workers_percent` | Connections | Workers percentage. Not applicable to data warehouses |
| `sqlserver_process_memory_percent` | Connections | Memory usage as a percentage of the SQL DB process. Not applicable to data warehouses |
| `app_memory_percent` | Connections | App memory percentage. Applies to serverless databases |
| `tempdb_data_size` | TempDB and XTP | Space used in tempdb data files, in kilobytes. Not applicable to data warehouses |
| `tempdb_log_size` | TempDB and XTP | Space used in the tempdb transaction log file, in kilobytes. Not applicable to data warehouses |
| `tempdb_log_used_percent` | TempDB and XTP | Space used percentage in the tempdb transaction log file. Not applicable to data warehouses |
| `xtp_storage_percent` | TempDB and XTP | In-Memory OLTP storage percent. Not applicable to data warehouses |
| `deadlock` | Contention | Not applicable to data warehouses |

### The query runner

A second executable, `pandora_azuresqlquery`, is a different tool: it runs SQL sentences against the database over ODBC and turns their rows into modules. It shares neither the options nor the configuration format of the metric collector described above. The Marketplace record does not describe it and does not state whether your package contains it; confirm that the file is present before relying on it.

```bash
./pandora_azuresqlquery -s <TARGET_HOST> -d <DATABASE> -u <USERNAME> -p <PASSWORD> \
    --conf <PATH_TO_CONFIG> --agent_name <AGENT_NAME>
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `-s`, `--servidor` | Yes | — | Server name, passed to the driver as `tcp:<TARGET_HOST>` |
| `-d`, `--database` | Yes | — | Database name |
| `-u`, `--user` | Yes | — | Database user |
| `-p`, `--password` | Yes | — | Password for that user |
| `--conf` | Yes | — | Path of the file with the queries |
| `--agent_name` | No | `AzureSQL` | Name of the agent created in Pandora FMS |
| `-g`, `--group` | No | `Azure` | Pandora FMS group name |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directory where the agent document is written |
| `--tentacle_address` | No | — | Tentacle server address; takes precedence over `--as_agent_plugin` |
| `--tentacle_port` | No | `41121` | Tentacle server port |
| `--as_agent_plugin` | No | `0` | `1` prints the module XML on standard output |
| `--prefix_module` | No | — | Prefix prepended to every module name, followed by `_` |

The query file holds one query per line, in this form:

```text
<module name>:<SQL sentence>:<module type>:<description>
```

The third field is written verbatim as the module type, without validation, and the fourth is optional. An example from the configuration shipped with the tool:

```text
User_connections:SELECT count(*) FROM sys.dm_exec_connections:generic_data_string:shows user connections.
```

The parser applies the rules of the metric collector with the same consequences: a line containing `#` anywhere is skipped, and a value ends at the next colon, so **a SQL sentence that contains a colon is truncated**. A line with fewer than three fields stops the run and drops every query after it. A query that fails prints its error on standard error, is skipped, and the run continues with the next one.

Each module value is a `<datalist>` in which every row is one `;`-joined string of the returned columns, so these modules are text as well. The token `_database_` in a query is replaced by the database name, quoted.

Two behaviours are worth knowing before using it in production:

- **A connection failure is reported as a successful run.** The tool prints `Error while creating PostgreSQL table` and the driver error, then a second `Error:` line on standard error, then `0`, and it exits with status `0`. The messages name PostgreSQL, not Azure SQL: the agent description it writes is literally `PostgreSQL agent`.
- **The database password is a command-line argument.** It is visible in the process list and in the shell history of the account that runs the tool.

### Addon identity

| Field | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.azuresql` |
| Marketplace name | Pandora Azure SQL |
| Addon version | `1.0` |
| Marketplace last update | 2025-06-26 |
| Marketplace package | `pandorafms.azuresql.1.0.pspz2` |
| License | Download limited to licensed users (Marketplace tag `One`) |
| Marketplace type | Miscelaneus |
| Workflow | Monitoring plugin, server or agent plugin mode |
| Executable | `pandora_azuresql` |
| Secondary executable | `pandora_azuresqlquery`, query runner, not described by the Marketplace record |
