# SAP HANA Database plugin

*Article last updated: 2026-10-26.*

## What it does

The SAP HANA Database addon monitors a SAP HANA database from Pandora FMS with
the SQL queries you write. Each execution opens one connection to the SQL port
of a single database, runs every query of a query file and turns each result
into one Pandora FMS module. Nothing is installed on the database server, and
no SAP command-line tool is needed on the host that runs the addon.

A run is one-shot: it connects, collects, delivers and exits, and it keeps no
state between executions. The modules reach Pandora FMS in one of three ways:

- **Data folder** (default): the run writes one agent data document into a
  Pandora FMS data folder and prints `1`.
- **Agent plugin**: with `--as_agent_plugin 1` the run prints the module XML on
  standard output, for a Pandora FMS agent to ingest, and writes no file.
- **Tentacle**: with `--tentacle_address` the run writes the document and sends
  it to a Tentacle server.

> The Marketplace entry `pandorafms.sap_hana_database` distributes this
> query-file collector. An older variant of the same addon, which needs the SAP
> `hdbsql` and `sapcontrol` client tools on the monitoring host and runs a fixed
> query set from a `key=value` file, takes different options and produces
> different module names. This page does not describe that variant.

SAP HANA Discovery (`pandorafms.sap.hana`) is a different addon: it runs from
the Discovery task wizard and creates one agent per database automatically,
with a fixed set of metric groups. This addon is configured per execution and
publishes what your queries return. See
[SAP HANA Discovery](../discovery/sap-hana.md).

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.sap_hana_database`, version `1.1` | Documented target | Version of the Marketplace entry, last updated 2026-06-02. See [Addon identity](#addon-identity) |
| Pandora FMS release | `Not validated` | No release-specific record exists for this addon. The Marketplace states that its integrations are compatible with Pandora FMS NG 784 and later |
| System of the host that runs the addon | `Not validated` | Not recorded for version `1.1`. The previous documentation of this addon recorded a test on CentOS 7 |
| SAP HANA release | `Not validated` | Not recorded for version `1.1`. The previous documentation of this addon recorded SAP HANA `2.00.059` |
| SQL access from the host that runs the addon to the database port | `Required` | The addon opens one connection with `--ip` and `--port` |
| A SAP HANA user able to read every object your queries read | `Required` | Prerequisite, not a compatibility statement. See [Database access](#database-access) |
| A Pandora FMS data server reading `--data_dir` | `Required` for the data folder mode | The document is only collected when the data server reads the folder where the addon writes it |
| A Pandora FMS server to execute the console plugin | `Required` for the console mode | The plugin server runs the registered plugin |

The download of this addon is limited to licensed users, according to its
Marketplace entry. This page does not describe any further license terms.

### Requirements

1. **Network access** from the host that runs the addon to the SQL port of the
   target database. The addon has no default port: `--port` is required.
2. **A SAP HANA user and its password**, able to read every object your queries
   read. The example queries read the views listed in
   [Database access](#database-access).
3. **A host to run the addon**: the Pandora FMS server for a console server
   plugin, a host with a Pandora FMS agent for agent plugin mode, or any host
   whose data folder the Pandora FMS data server reads. The addon connects to
   the database port directly, so the SAP client tools are not required there.
4. **A query file.** The addon reads it on every execution; without it the run
   publishes nothing (see [Known limitations](#known-limitations)).
5. **A Pandora FMS side** that receives the output: the plugin server that runs
   the registered plugin, the data server that reads the data folder, the agent
   that runs the addon, or the Tentacle server.
6. **Write permission on the data folder** for the user that runs the addon,
   when documents are delivered there.
7. **The Tentacle client (`tentacle_client`) in `PATH`**, only when the run
   delivers through Tentacle.

### Database access

The addon reads only what your queries ask for. The user needs read access to
those objects; SAP HANA defines which privilege each view requires, and no
narrower grant is documented for this addon. The queries in the example file
read:

| Object | Read by |
| --- | --- |
| `DUMMY`, `M_DATABASE` | Timestamp and version |
| `M_CONVERTER_STATISTICS` | Backup size estimate |
| `M_DATA_VOLUMES` | Volume list |
| `SYS_DATABASES.M_SERVICE_STATISTICS` | Requests per second and response time |
| `M_SERVICE_THREADS` | CPU time |
| `M_RS_MEMORY` | Row store fragmentation |
| `M_LICENSE` | License validity, permanence and usage |
| `M_VOLUME_IO_TOTAL_STATISTICS` | Read and write bandwidth |
| `PUBLIC.M_CONNECTIONS` | Running connections |
| `M_HOST_RESOURCE_UTILIZATION` | Memory usage |
| `M_BLOCKED_TRANSACTIONS` | Blocked transactions |
| `SYS.M_BACKUP_CATALOG` | Only the two backup queries of the example set |

The addon sends every line of the query file to the database exactly as
written, with no restriction to `SELECT`. Use a dedicated user with read-only
access and keep only read statements in the file.

### Install the addon

Download the package from the Pandora FMS Marketplace entry, which is limited
to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.sap_hana_database](https://marketplace.pandorafms.com/entries/pandorafms.sap_hana_database)

Copy the addon executable `pandora_hana` and the example query file
`pandora_hana.conf` to the host that will run it. For a console server plugin
the recommended folder is `/usr/share/pandora_server/util/plugin/`. This page
invokes the executable as `pandora_hana`; use the name your copy carries in the
commands below.

## Configure

The addon has no configuration file of its own: every setting is a command-line
option, and the queries live in the separate file named by `--conf`.

### Connection

A run needs the database address, its SQL port, a user, a password and the
query file:

```bash
./pandora_hana --ip <TARGET_HOST> --port 30013 --user <USERNAME> \
    --password <PASSWORD> --conf <PATH_TO_CONFIG> --agent_name sap-hana
```

SAP HANA publishes one SQL port per database, and the port encodes the
instance number `NN`:

| Database | Port |
| --- | --- |
| Tenant database | `3NN13` |
| System database (`SYSTEMDB`) of a multitenant system | `3NN13` |
| System database of a single-tenant system | `3NN15` |

With instance `00`, for example, a tenant database listens on `30013` and the
system database of a single-tenant system on `30015`.

`--password` is passed on the command line: the shell keeps it in its history
and the operating system process list shows it while the run lasts. In the
console, mark the field that holds the password as hidden, and restrict who can
read the server process list. The addon has no option to read the password from
a file.

### Choose the delivery mode

| Mode | Options | Behavior |
| --- | --- | --- |
| Data folder (default) | none | Writes one `<agent_name>.<epoch>.data` document into `--data_dir` (default `/var/spool/pandora/data_in/`) and prints `1` |
| Agent plugin | `--as_agent_plugin 1` | Prints one `<module>` block per module on standard output and writes no file |
| Tentacle | `--tentacle_address <ADDRESS>` | Writes the document into `--data_dir`, sends it with `tentacle_client` and prints `1` |

`--tentacle_address` takes precedence over `--as_agent_plugin`. Any
`--as_agent_plugin` value other than `1` selects the data folder mode, which is
also the default. `--tentacle_port` defaults to `41121` and is only used when
`--tentacle_address` is set.

Use agent plugin mode when a Pandora FMS agent runs the addon: the agent
ingests the printed modules. Use the data folder mode when the plugin server
runs the addon in the console and the local data server collects the document.
Use Tentacle when the addon runs on a host that must deliver to a remote
Pandora FMS server.

`--agent_name` names the agent that holds the modules; without it the addon
uses `Sap_Hana`. `--prefix_module` prepends `<prefix>_` to every module name, so
several runs can publish into the same agent without duplicate module names.
`-g`/`--group` sets the name of the Pandora FMS group written in the agent
document; its default is `SAP`.

### Define the queries

The query file has one query per line, split into colon-separated fields:

```text
name:query:module_type[:description]
```

- `name` becomes the module name, `module_type` the Pandora FMS module type and
  the optional fourth field the module description. The first three fields are
  mandatory.
- The query cannot contain a colon. The line is split on every colon, so a `:`
  inside the query shifts the type and the description, and a `:` inside the
  description truncates it, both without warning.
- A line that contains `#` anywhere is skipped as a comment, not only a line
  that starts with `#`.
- A line is skipped only when it is completely empty. A line holding spaces is
  read as an incomplete query and stops the run (see
  [Known limitations](#known-limitations)).
- Each query produces one module. Every returned row becomes one entry of the
  module data list, holding the columns of the row joined by `;`.
- Every query in the file is executed on every run, in file order.

The example file that ships with the addon has this shape:

```text
Timestamp:SELECT CURRENT_TIMESTAMP FROM DUMMY;:generic_data_string:Current timestamp
Hana_version:SELECT VERSION FROM M_DATABASE;:generic_data_string:version
Hana_Memory:SELECT HOST, round ( 100 * INSTANCE_TOTAL_MEMORY_USED_SIZE / INSTANCE_TOTAL_MEMORY_ALLOCATED_SIZE, 2), round (INSTANCE_TOTAL_MEMORY_ALLOCATED_SIZE / 1024/1024/1024, 2), round (INSTANCE_TOTAL_MEMORY_USED_SIZE / 1024/1024/1024, 2) from M_HOST_RESOURCE_UTILIZATION:generic_data_string:retrieve memory usages
```

The complete file is in [Example query file](#example-query-file). Keep the
file readable only by the user that runs the addon: it holds the queries, not
credentials, but it reveals the database objects you monitor.

### Register the plugin in the console

A console server plugin runs the addon from the Pandora FMS server. The plugin
server executes it in data folder mode, the addon writes its document and the
data server ingests it, so the agent and its modules appear in the console.

1. Open **Servers → Plugins** and click **Register Plugin**.
2. Set the name, the plugin type **Standard**, an optional maximum timeout and
   a description.
3. In **Plugin command**, enter the path to `pandora_hana` on the Pandora FMS
   server, for example `/usr/share/pandora_server/util/plugin/pandora_hana`.
4. In **Plugin parameters**, pass the connection through the plugin macros
   `_field1_`, `_field2_`, ... and keep the query file at a fixed path on the
   server:

```text
--ip _field1_ --port _field2_ --user _field3_ --password _field4_ --conf /etc/pandora/plugins/pandora_hana.conf --agent_name _field5_
```

5. In **Macro parameters**, describe each field. The example uses these values:

| Field | Description | Example value |
| --- | --- | --- |
| `_field1_` | Database host name or IP address | `<TARGET_HOST>` |
| `_field2_` | SQL port of the database | `30013` |
| `_field3_` | SAP HANA user that runs the queries | `<USERNAME>` |
| `_field4_` | Password for that user; mark **Hide value** | — |
| `_field5_` | Name of the agent that will hold the modules | `sap-hana` |

<!-- SCREENSHOT NEEDED: Servers → Plugins registration form for the SAP HANA Database addon, showing the command path and the five _fieldN_ parameters. -->

Do not add `--as_agent_plugin 1` here: the console run must stay in data folder
mode, because the plugin module value is what the addon prints, and in agent
plugin mode it prints the module XML instead of `1`.

Once registered, the plugin is available when creating plugin modules. Each
module fills the fields individually, and the field values can use the Pandora
FMS macros documented in the console *Plug-in macros* help.

<!-- SCREENSHOT NEEDED: Plugin module form with the SAP HANA Database plugin selected, showing the per-field parameters of one database. -->

## Verify

Run the addon manually with `--as_agent_plugin 1`, so it prints the modules
instead of writing a file:

```bash
./pandora_hana --ip <TARGET_HOST> --port 30013 --user <USERNAME> \
    --password <PASSWORD> --conf <PATH_TO_CONFIG> --as_agent_plugin 1
```

A successful run prints one `<module>` block per query and exits with status
`0`. The values below are illustrative; yours come from your database:

```xml
<module>
	<name><![CDATA[Timestamp]]></name>
	<type>generic_data_string</type>
	<datalist>
	<data>
		<value><![CDATA[2026-10-26 10:14:32.123456789]]></value>
	</data>
	</datalist>
	<description><![CDATA[Current timestamp]]></description>
</module>
<module>
	<name><![CDATA[Hana_get_stated_connections]]></name>
	<type>generic_data</type>
	<datalist>
	<data>
		<value><![CDATA[7]]></value>
	</data>
	</datalist>
	<description><![CDATA[retrieve connection status]]></description>
</module>
```

With the default data folder mode the same run prints `1` and writes one
document:

```text
/var/spool/pandora/data_in/sap-hana.1793001234.data
```

After the first scheduled execution, open the agent named by `--agent_name`
(default `Sap_Hana`) and check that it holds one module per query of the file.

`-h` prints the usage summary with its options and one execution example. The
summary prints the addon's build marker `270622`, which does not match the
Marketplace version (see [Known limitations](#known-limitations)).

## Understand the results

A run creates one agent, or updates the existing one, and never more than one.
The agent document declares these properties:

| Property | Value |
| --- | --- |
| Agent name and alias | `--agent_name` (default `Sap_Hana`) |
| Description | `SAP Hana` |
| Group | `--group` (default `SAP`) |
| Interval | Empty; Pandora FMS assigns the interval of a new agent |
| Address | Empty |

Each line of the query file produces exactly one module:

- The module name is the first field, prefixed with `<prefix>_` when
  `--prefix_module` is set.
- The module type is the third field, written verbatim. Use the Pandora FMS
  module type your data requires: `generic_data` for numbers and
  `generic_data_string` for text.
- The description is the fourth field, and it is empty when the field is
  absent.
- The value is a data list with one entry per returned row. The columns of a
  row are joined by `;` inside the entry, so a query with three columns returns
  entries such as `host01;30003;7`.

Because every column of every row becomes part of one value, write numeric
modules with a query that returns one row and one column. A query that returns
several rows publishes several entries in the same data list, and a query that
returns several columns publishes them concatenated.

A query that returns no rows still produces its module, with an empty data
list. A query the database rejects produces no module at all: the failure is
reported on standard error and the following queries still run.

The example file groups its queries by subject:

- **Backups and volumes.** `Backups_Size` estimates the backup size and
  `Data_disk_information` lists the data volumes.
- **Version and time.** `Timestamp` and `Hana_version` identify the database
  and stamp the run.
- **Performance.** `Hana_service_statics` reports requests per second and
  response time, `Hana_cpu_time` the service CPU time and
  `Hana_IO_Stats` the read and write bandwidth per volume.
- **Memory.** `Hana_Memory` reports the memory in use over the allocated
  memory, and `Hana_rs_fragmentation` the row store free ratio.
- **Capacity and health.** `Hana_license` reports license validity,
  permanence and usage, `Hana_get_stated_connections` the running connections
  and `Hana_Transactions` the blocked transactions.

## Operate and troubleshoot

### Run-time behavior

- One execution opens one connection, runs every query of the file in order,
  delivers and exits. The connection is opened before the query file is read,
  so an unreachable database stops the run before any query is parsed.
- The addon keeps no state between executions. The query file is re-read on
  every run, so a query added to the file is collected from the next execution.
- There is no verbose or debug option. The output is the module XML with
  `--as_agent_plugin 1`, a `1` in the other two modes, or an error message.
- The addon writes one document per run, so a run collects all modules of the
  agent at the same timestamp.

### Known limitations

These are behaviors of version `1.1`, documented as they are.

- **The query file is effectively mandatory.** A run without a readable
  `--conf` prints `Error al conectarse` followed by the operating system error,
  then `Error: name 'f' is not defined` and `0`, and ends with status `0`
  without publishing anything.
- **A blank line with spaces stops the run with status `0`.** Only a line that
  is completely empty is ignored. A line holding spaces or tabs has fewer than
  three fields, so the run prints
  `It is mandatory to specify name, query and type!`, ends immediately and
  publishes nothing, and the exit status is `0`.
- **A query cannot contain a colon and a description loses everything after
  one.** The line is split on every colon, so a colon inside the query shifts
  the module type, and a colon inside the description truncates it. No warning
  is printed in either case.
- **A line with `#` anywhere is skipped.** A `#` inside a query or a description
  removes the whole line from the run, not only a comment line.
- **A failed Tentacle transfer still prints `1`.** With `--tentacle_address`,
  the addon writes the document, sends it and prints `1` even when
  `tentacle_client` fails or is missing; the error goes to standard error and
  the document stays in `--data_dir`.
- **Two runs of the same agent in one second collide.** The document name uses
  one-second resolution and the file is created exclusively. A run that starts
  while the previous document of the same agent is still in the folder ends
  with `ERROR - Could not write file: ... please check directory permissions`
  and status `1`, and the modules of that run are lost.
- **The build marker does not match the Marketplace version.** The usage
  summary prints the build marker `270622`, the date of the build, while the
  Marketplace entry publishes version `1.1`.
- **No TLS or certificate option is exposed.** The addon passes the address,
  port, user and password to the database client, and leaves any encryption
  setting to that client's defaults. It has no option to set a certificate or
  to require an encrypted connection.
- **The password only exists as a command-line option.** There is no
  credentials file and no standard-input form, so the password appears in the
  shell history and in the process list of the host that runs the addon.
- **`--tentacle_port` is ignored without `--tentacle_address`.** The port is
  only used by the Tentacle branch.

### Diagnostics

| Symptom | Cause and action |
| --- | --- |
| A traceback from the database client, ending with the connection call, status `1` | The connection failed. Check `--ip`, `--port`, the user, the password and the network path to the SQL port. Remember that a tenant database and the system database listen on different ports |
| `Error al conectarse` and then `Error: ...` and `0`, status `0` | `--conf` could not be opened. Check the path and its read permissions |
| `It is mandatory to specify name, query and type!` | A line of the query file has fewer than three colon-separated fields, usually because it is blank or holds only spaces |
| `error with the query:<query>.<error>` on standard error | The database rejected that query. The following lines are still processed |
| A module is missing from the agent | Its query failed, or its line was skipped because it contained `#` |
| A numeric module receives more than one data entry per run | The query returns more than one row. Restrict it to one row and one column for numeric modules |
| `Tentacle error` on standard error and a stored `1` | The transfer failed. Check `--tentacle_address`, `--tentacle_port` and that `tentacle_client` is in `PATH`; the document remains in `--data_dir` |
| `ERROR - Could not write file: ...` | The data folder is not writable, or a document with the same name exists already (see [Known limitations](#known-limitations)) |
| The agent does not appear in the console | The document was written to a `--data_dir` the Pandora FMS data server does not read, or the run ended with an error. Check the folder and the run output |
| `bad interpreter` or a missing-interpreter message | The interpreter declared in the first line of the executable is not installed on this host, or the file lost its execute permission. Run the addon from a host that has that interpreter, or restore the permission with `chmod +x` |

## Reference

### Command-line options

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--ip` | Yes | — | Database host name or IP address |
| `--port` | Yes | — | SQL port of the database (`3NN13` for a tenant database, `3NN15` for the system database of a single-tenant system) |
| `--user` | Yes | — | SAP HANA user that runs the queries |
| `--password` | Yes | — | Password for that user |
| `--conf` | Yes | — | Query file. It is read on every run |
| `--agent_name` | No | `Sap_Hana` | Name and alias of the agent that holds the modules |
| `--prefix_module` | No | — | Prefix joined to every module name as `<prefix>_<name>` |
| `-g`, `--group` | No | `SAP` | Name of the Pandora FMS group written in the agent document |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Folder for the agent data document in data folder and Tentacle modes |
| `--as_agent_plugin` | No | `0` | `1` prints the module XML on standard output; any other value writes the document into `--data_dir` |
| `--tentacle_address` | No | — | Tentacle server address. It takes precedence over `--as_agent_plugin` |
| `--tentacle_port` | No | `41121` | Tentacle server port, only used with `--tentacle_address` |
| `-h`, `--help` | No | — | Prints the usage summary and exits |

### Query file

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Module name. With `--prefix_module`, the module name is `<prefix>_<name>` |
| `query` | Yes | SQL statement executed against the database. It cannot contain a colon |
| `module_type` | Yes | Pandora FMS module type, written verbatim into the module |
| `description` | No | Module description. It cannot contain a colon |

A line that contains `#` is skipped. A line that is completely empty is
skipped. Every other line is split on `:` and executed.

### Example query file

This is the example file distributed with the addon:

```text
Backups_Size:SELECT SUM(allocated_page_size) FROM M_CONVERTER_STATISTICS;:generic_data:Estimated backup size
Timestamp:SELECT CURRENT_TIMESTAMP FROM DUMMY;:generic_data_string:Current timestamp
Hana_version:SELECT VERSION FROM M_DATABASE;:generic_data_string:version
Data_disk_information:SELECT HOST,PORT,FILE_NAME,STATE,SIZE,MAX_SIZE FROM M_DATA_VOLUMES:generic_data_string:Retrieve Hana disk info
Hana_service_statics:SELECT SERVICE_NAME, DATABASE_NAME, REQUESTS_PER_SEC, RESPONSE_TIME FROM SYS_DATABASES.M_SERVICE_STATISTICS:generic_data_string:Retrieve Hana Requests per second
Hana_cpu_time:SELECT HOST,PORT,SERVICE_NAME, SUM(CPU_TIME_SELF),SUM(CPU_TIME_CUMULATIVE) FROM M_SERVICE_THREADS GROUP BY HOST,PORT,SERVICE_NAME:generic_data_string:Retrieve Hana cpu usage
Hana_rs_fragmentation:SELECT HOST, PORT, TO_DECIMAL(SUM(FREE_SIZE) * 100 / SUM(ALLOCATED_SIZE),10,2), TO_DECIMAL( SUM(FREE_SIZE)/(1024*1024), 10, 2), TO_DECIMAL( SUM(ALLOCATED_SIZE)/(1024*1024), 10, 2) FROM M_RS_MEMORY WHERE CATEGORY = 'TABLE' OR CATEGORY = 'CATALOG'  GROUP BY HOST, PORT:generic_data_string:Retrieve Hana row store fragmentation
Hana_license:SELECT VALID, PERMANENT, PRODUCT_LIMIT, PRODUCT_USAGE FROM M_LICENSE;:generic_data_string:Retrieve license usage
Hana_IO_Stats:SELECT HOST,PORT,TYPE, TO_DECIMAL((TOTAL_READ_SIZE * 1.048576 / (TOTAL_READ_TIME+1)),10,2), TO_DECIMAL((TOTAL_WRITE_SIZE * 1.048576 / (TOTAL_WRITE_TIME+1)),10,2) FROM M_VOLUME_IO_TOTAL_STATISTICS:generic_data_string:Retrieve IO bandwidth
Hana_get_stated_connections:SELECT COUNT(*) FROM PUBLIC.M_CONNECTIONS WHERE CONNECTION_STATUS ='RUNNING':generic_data:retrieve connection status
Hana_Memory:SELECT HOST, round ( 100 * INSTANCE_TOTAL_MEMORY_USED_SIZE / INSTANCE_TOTAL_MEMORY_ALLOCATED_SIZE, 2), round (INSTANCE_TOTAL_MEMORY_ALLOCATED_SIZE / 1024/1024/1024, 2), round (INSTANCE_TOTAL_MEMORY_USED_SIZE / 1024/1024/1024, 2) from M_HOST_RESOURCE_UTILIZATION:generic_data_string:retrieve memory usages
Hana_Transactions:SELECT count(*) FROM M_BLOCKED_TRANSACTIONS;:generic_data:retrieve SAP transaction status
```

The Marketplace entry also names two backup-catalog modules,
`Check_no_running_backups` and `Backup_id_running_backup`, that this copy of
the file does not include, and its list does not name `Data_disk_information`,
which the file does include. Add the backup lines as your own if you need
backup monitoring:

```text
Check_no_running_backups:select * from SYS.M_BACKUP_CATALOG where STATE_NAME = 'running':generic_data_string:Check that no backup is still running
Backup_id_running_backup:select BACKUP_ID from SYS.M_BACKUP_CATALOG where entry_type_name = 'complete data backup' and state_name = 'running' order by sys_start_time desc:generic_data_string:Query to find the BACKUP_ID of the running data backup
```

### Generated modules

Modules of the example file, in file order:

| Module | Type in the file | Reads |
| --- | --- | --- |
| `Backups_Size` | `generic_data` | Sum of `allocated_page_size` in `M_CONVERTER_STATISTICS` |
| `Timestamp` | `generic_data_string` | `CURRENT_TIMESTAMP` of the database |
| `Hana_version` | `generic_data_string` | `VERSION` from `M_DATABASE` |
| `Data_disk_information` | `generic_data_string` | Host, port, file name, state, size and maximum size of each data volume |
| `Hana_service_statics` | `generic_data_string` | Service, database, requests per second and response time |
| `Hana_cpu_time` | `generic_data_string` | CPU time per host, port and service |
| `Hana_rs_fragmentation` | `generic_data_string` | Free ratio and sizes of the row store per host and port |
| `Hana_license` | `generic_data_string` | Validity, permanence, limit and usage of the license |
| `Hana_IO_Stats` | `generic_data_string` | Read and write bandwidth per host, port and volume type |
| `Hana_get_stated_connections` | `generic_data` | Number of connections in the `RUNNING` state |
| `Hana_Memory` | `generic_data_string` | Memory used percentage, allocated and used memory |
| `Hana_Transactions` | `generic_data` | Number of blocked transactions |
| `Check_no_running_backups` | `generic_data_string` | Backup catalog entries still running, when you add the line |
| `Backup_id_running_backup` | `generic_data_string` | Identifier of the running complete data backup, when you add the line |

### Agent document

| Property | Value |
| --- | --- |
| File name | `<agent_name>.<epoch>.data` in `--data_dir` |
| Agent mode | `1` |
| Timestamp | Local time of the run, as `YYYY/MM/DD HH:MM:SS` |
| Modules | One per query, all at the run timestamp |

### Exit status

| Status | Meaning |
| --- | --- |
| `0` | Successful run. Also used when the query file cannot be opened, when a line of it is malformed and when an error interrupts the query stage |
| `1` | The connection failed, or the document could not be written |
| `2` | An option is missing or received a value of the wrong type, for example a non-integer `--as_agent_plugin` |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.sap_hana_database` |
| Name | SAP HANA Database |
| Version | `1.1` |
| Package | `pandorafms.sap_hana_database.1.1.zip` |
| Other published version | `1.0`, package `pandorafms.sap_hana_database.1.0.zip`, dated 2025-06-25 |
| License | One; the download is limited to licensed users |
| Marketplace last update | 2026-06-02 |
| Downloads | 16 |
| Author | Pandora FMS |
| Marketplace type | Miscelaneus |
| Tags | `applications`, `databases` |
| Executable | `pandora_hana` |
| Example query file | `pandora_hana.conf` |
