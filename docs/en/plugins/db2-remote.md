# DB2 Remote plugin

*Article last updated: 2026-10-27.*

!!! warning "Discovery integration recommended"
    For new installations use [DB2 Discovery](../discovery/db2.md), which is the recommended integration for this service. This plugin is the legacy path. The Marketplace entry states that this addon is no longer actively maintained.

## What it does

The DB2 Remote addon monitors IBM Db2 databases from Pandora FMS over TCP/IP.
Nothing is installed on the database server: each execution opens one
connection from the host that runs the addon, runs the statements you keep in a
query file and publishes the result as Pandora FMS modules.

A run produces two kinds of output:

- **Query modules.** One module per statement in the query file, with one
  data-list entry per row the statement returns.
- **Default performance modules.** A fixed set of buffer pool and transaction
  log metrics, read from Db2 administrative views. They are enabled unless you
  disable them.

Every execution is one-shot: it connects, collects, delivers and exits. The
addon keeps no state between runs, so an execution at any moment reports the
values the database has at that moment.

The modules reach Pandora FMS either as module XML on standard output, for a
Pandora FMS agent to ingest, or as agent data documents written into a Pandora
FMS data folder (see [Configure](#configure)).

DB2 Discovery (`pandorafms.db2`) is a different addon: it runs from the
Discovery task wizard and generates one agent per database automatically. The
DB2 Remote plugin is configured per execution and publishes the modules
produced by the statements you write. See
[DB2 Discovery](../discovery/db2.md).

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.db2_remote`, version `1.0` | Documented target | Version of the Marketplace entry, also printed by the addon's usage summary. See [Addon identity](#addon-identity) |
| TCP access from the host that runs the addon to the Db2 listener (default port `50000`) | `Required` | The addon connects with `--hostname`, `--port` and `--protocol` |
| A Db2 user allowed to read every object your statements read | `Required` | Prerequisite, not a compatibility statement |
| A `python3` interpreter with the `ibm-db` driver `3.1.4` | `Required` | The package's `requirements.txt` pins `ibm-db==3.1.4` |
| Db2 server versions and platforms | `Not validated` | No version matrix is recorded for this addon |
| Operating system of the host that runs the addon | `Not validated` | No operating system is recorded for version `1.0` |
| Pandora FMS release | `Not validated` | No release-specific validation record exists. The Marketplace states that its integrations are compatible with Pandora FMS NG 784 and later |

The Marketplace entry states that this addon is no longer actively maintained
or updated, and points to the alternatives published in its library.

### Requirements

1. **Network access** from the host that runs the addon to the Db2 listener,
   by default on TCP port `50000`.
2. **A Db2 user and its password**, allowed to read every object your
   statements read and, when default metrics are enabled, the administrative
   views listed in [Database access](#database-access).
3. **A host to run the addon**: the Pandora FMS server for a console server
   plugin, a host with a Pandora FMS agent for agent plugin mode, or any host
   whose data folder the Pandora FMS data server reads.
4. **A `python3` interpreter** with the `ibm-db` driver installed, in the
   version pinned by the package's `requirements.txt`.
5. **A Pandora FMS installation** that receives the output: the plugin server
   that runs the registered plugin, the agent that runs it, or the data server
   that reads the data folder.
6. **Write permission on the data folder** for the user that runs the addon,
   when documents are delivered there.
7. **A query file.** The addon reads it on every execution, including runs
   that only need the default metrics (see [Known limitations](#known-limitations)).

### Database access

The addon reads only what your statements and the default metrics ask for:

| Read | When |
| --- | --- |
| The objects your own statements read | Every execution |
| `SYSCAT.BUFFERPOOLS`, `SYSIBMADM.BP_HITRATIO`, `SYSIBMADM.LOG_UTILIZATION` | Default metrics enabled, which is the default |

Db2 defines which authority each administrative view requires. No official
source for this addon documents a narrower grant, so give the user the minimum
Db2 accepts for the reads you enable.

The addon executes the statement text exactly as written and does not restrict
it to `SELECT`. Use a dedicated user with read-only access and keep only read
statements in the query file.

### Install the addon

Download the package from the Pandora FMS Marketplace entry, which is limited
to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.db2_remote](https://marketplace.pandorafms.com/entries/pandorafms.db2_remote)

Copy the addon script `pandora_db2.py` and its example query file `db2.conf` to
the host that will run it. For a console server plugin the recommended folder
is `/usr/share/pandora_server/util/plugin/`.

Install the driver pinned by the package's `requirements.txt`
(`ibm-db==3.1.4`) for the interpreter that will run the addon.

## Configure

The addon has no configuration file of its own: everything is a command-line
option, and the queries live in the separate file named by `--conf`.

### Connection

A run needs the host, the database, a user and a password:

```bash
python3 pandora_db2.py --hostname <TARGET_HOST> --port 50000 --database <DB_NAME> \
    --uid <USERNAME> --password <PASSWORD> --conf <PATH_TO_CONFIG> --as_agent_plugin 1
```

`--port` defaults to `50000` and `--protocol` to `TCPIP`, so both can be
omitted. The addon builds a complete connection string from these options, so
no local Db2 client, catalog entry or DSN is needed on the host that runs it.

`--password` on the command line is kept in the shell history and is visible in
the process list while the run lasts. The addon has no credentials-file option
in this version; in the console, mark the field that holds the password as
hidden (see
[Register the plugin in the console](#register-the-plugin-in-the-console)).

### Choose the delivery mode

| Mode | Option | Behavior |
| --- | --- | --- |
| Data folder (default) | none | Writes one `<agent_name>.<timestamp>.data` document into `--data_dir` (default `/var/spool/pandora/data_in/`) for every document it produces, and prints `1` per document |
| Agent plugin | `--as_agent_plugin 1` | Prints one `<module>` block per module on standard output and writes no files |
| Tentacle | `--tentacle_address <ADDRESS>` | Configured with `--tentacle_address` and `--tentacle_port`; it does not deliver in version `1.0` (see [Known limitations](#known-limitations)) |

`--tentacle_address` takes precedence over `--as_agent_plugin`; any
`--as_agent_plugin` value other than `1` selects the data folder.

Use agent plugin mode when a Pandora FMS agent runs the addon: the agent
ingests the printed modules. Use the data folder when the plugin server runs it
in the console and the local data server collects the documents.

`--default_metrics` is `1` by default; any other value publishes only the query
modules.

### Define the queries

The query file has one statement per line, split into colon-separated fields:

```text
name:statement:module_type[:description]
```

This is the example shipped with the package:

```text
query_test:select * from department:generic_data:testing query
```

- `name` becomes the module name, `module_type` the module type and the
  optional fourth field the module description. The first three fields are
  mandatory.
- The statement cannot contain a colon. The line is split on every colon, so a
  `:` inside the statement shifts the type and the description and produces a
  different module without warning.
- A line that contains `#` anywhere is skipped as a comment, not only a line
  that starts with `#`.
- Blank lines are ignored.
- `_database_` is replaced by the connected database name in single quotes, so
  it can be used where a string literal is expected. With `--database
  <DB_NAME>`, the line `select * from syscat.tables where tabschema =
  _database_` reaches the database as `select * from syscat.tables where
  tabschema = '<DB_NAME>'`.
- Each statement produces one module. Every returned row becomes one entry of
  the module data list, holding the row as a column/value mapping.
- Every statement in the file is executed on every run.

### Register the plugin in the console

A console server plugin runs the addon from the Pandora FMS server. The plugin
server executes it, the addon writes its documents into the data folder and the
data server ingests them, so the agents and their modules appear in the
console.

1. Open **Servers → Plugins** and click **Register Plugin**.
2. Set the name, the plugin type **Standard**, an optional maximum timeout and
   a description.
3. In **Plugin command**, enter the path to `pandora_db2.py` on the Pandora FMS
   server, for example
   `/usr/share/pandora_server/util/plugin/pandora_db2.py`.
4. In **Plugin parameters**, pass the connection through the plugin macros
   `_field1_`, `_field2_`, ... and keep the query file at a fixed path on the
   server:

```text
--hostname _field1_ --port 50000 --database _field2_ --uid _field3_ --password _field4_ --conf /etc/pandora/plugins/db2.queries --agent_name db2-remote
```

5. In **Macro parameters**, describe each field. The example uses these values:

| Field | Description | Example value |
| --- | --- | --- |
| `_field1_` | Db2 host name or IP address | `<TARGET_HOST>` |
| `_field2_` | Database name | `<DB_NAME>` |
| `_field3_` | Db2 user that runs the statements | `<USERNAME>` |
| `_field4_` | Password for that user; mark **Hide value** | — |

<!-- SCREENSHOT NEEDED: Servers → Plugins registration form for the DB2 Remote addon, showing the command path and the four _fieldN_ parameters. -->

`--agent_name` names the agent that receives the query modules; without it the
addon uses `DB2`, and the metrics agent is `<agent_name>_metrics`.

In this mode the module value is the text the addon prints, normally `1` per
delivered document. An execution that has to deliver several documents is
subject to the data folder limitation described in
[Known limitations](#known-limitations).

## Verify

Run the addon manually with `--as_agent_plugin 1`, so it prints the modules
instead of writing files:

```bash
python3 pandora_db2.py --hostname <TARGET_HOST> --database <DB_NAME> \
    --uid <USERNAME> --password <PASSWORD> --conf <PATH_TO_CONFIG> --as_agent_plugin 1
```

A successful run prints one `<module>` block per module and exits with status
`0`. The values below are illustrative; yours come from your database. This is
the module produced by the example query:

```xml
<module>
	<name><![CDATA[query_test]]></name>
	<type>generic_data</type>
	<datalist>
	<data>
		<value><![CDATA[{'DEPTNO': 'A00', 'DEPTNAME': 'SPIFFY COMPUTER SERVICE DIV.'}]]></value>
	</data>
	</datalist>
	<description><![CDATA[testing query]]></description>
</module>
```

When the default metrics are enabled they are printed after the query modules,
one block per metric:

```xml
<module>
	<name><![CDATA[no_of_bufferpools_<DB_NAME>]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<description><![CDATA[]]></description>
	<unit><![CDATA[count]]></unit>
</module>
```

With the default data folder delivery the same run prints `1` once per document
and writes files named `<agent_name>.<timestamp>.data` in `--data_dir`:

```text
/var/spool/pandora/data_in/db2-remote.<timestamp>.data
```

After the first scheduled execution, check the console:

1. The agent named by `--agent_name` (default `DB2`) with one module per
   statement in the query file.
2. The agent `<agent_name>_metrics` with the default performance modules.
3. The value of the plugin module that triggered the execution.

<!-- SCREENSHOT NEEDED: Module list of the DB2 Remote agent after a successful run, showing a query module and the separate metrics agent. -->

The addon prints its usage summary, with a manual execution example, when it
runs with `-h`.

## Understand the results

A run creates at most two agents. Both are assigned the group passed with
`--group`, and both carry the description `Agent generated by pandora_db2`.

| Agent | Name | Alias | Content | Condition |
| --- | --- | --- | --- | --- |
| Query agent | `--agent_name` (default `DB2`) | Same as the name | One module per statement in the query file | The query file has at least one statement |
| Metrics agent | `<agent_name>_metrics` | `<agent_name>` | The default performance modules | `--default_metrics 1` |

The metrics agent repeats the alias of the query agent, so the console shows
the same alias for both agents.

### Query modules

Each module is named after the first field of its line and typed with the third
field. Its value is a data list with one entry per row, and each entry keeps the
column names of the row visible in the module data. The module description is
the fourth field, and it is empty when that field is absent.

### Default performance modules

The metrics cover three groups: the number of buffer pools, the buffer pool
read counters and the transaction log utilization. Every module name ends with
the database name. The full list is in [Generated modules](#generated-modules).

## Operate and troubleshoot

### Run-time behavior

- One execution connects once, runs every statement of the query file in order,
  then the default metrics, delivers and exits.
- The query modules are delivered before the metrics, so a metrics failure does
  not undo what the statements already published.
- The addon has no verbose or debug option. Its output is the module XML with
  `--as_agent_plugin 1`, one `1` per document in the data folder mode, or an
  error message.
- The addon keeps no state between executions. The query file is re-read on
  every run.

### Known limitations

These are behaviors of version `1.0`, documented as they are.

- **The query file is effectively mandatory.** Every run reads `--conf` before
  anything else. Without it the run prints `Error al conectarse ...` and `0`,
  exits with status `0` and publishes nothing, default metrics included. To
  collect only the default metrics, pass an empty query file.
- **Tentacle delivery does not work.** With `--tentacle_address` the run writes
  the document into `--data_dir` and then stops with an unhandled error before
  sending anything, so no document reaches the Tentacle server. Use the data
  folder or the agent plugin mode.
- **Data folder documents can collide.** Document names use one-second
  resolution (`<agent_name>.<timestamp>.data`) and are created exclusively.
  When a run produces several documents for the same agent within the same
  second and Pandora FMS has not collected the previous file yet, the write
  fails with `ERROR - Could not write file: ... please check directory
  permissions` and the remaining documents of the run are lost. A
  default-metrics run produces, with every metric available, seventeen documents
  for the metrics agent, ten of them with a module, so this is likely in that
  mode. Keep one document per run (`--default_metrics 0` and a single statement)
  or run the addon in agent plugin mode, which writes no files.
- **Four collected metrics are not published.** `total_hit_ratio_percent`,
  `data_hit_ratio_percent`, `index_hit_ratio_percent` and
  `xda_hit_ratio_percent` are read from the database, but no module is created
  for them.
- **A statement cannot contain a colon.** The line format uses the colon as
  separator, so a statement with a colon is silently misread.
- **A malformed query line stops the run with status `0`.** A line with fewer
  than three fields prints `It is mandatory to specify name, query and type!`
  and ends the execution, including the statements that had not run yet.
- **A failed default-metrics query stops the metrics stage.** If the user
  cannot read one of the three views, the stage ends with an unhandled error
  after the query modules were already delivered. Disable the metrics with
  `--default_metrics 0` or grant the reads.
- **The usage summary shows a command that does not run as shipped.** `-h`
  prints the manual execution as `./pandora_db2`, but the distributed script is
  not executable on its own: invoke it through `python3 pandora_db2.py`.

### Diagnostics

| Symptom | Cause and action |
| --- | --- |
| `no connection:` followed by the driver error, status `1` | The connection failed. Check the host, the port, the database name, the user and the password, and the network path to the Db2 listener |
| `Error al conectarse ...` and then `0`, status `0` | The query file could not be opened. Check `--conf`, its path and its read permissions |
| `It is mandatory to specify name, query and type!` | A line of the query file has fewer than three colon-separated fields |
| `error with the query:<statement>.<error>` on standard error | The database rejected that statement. The following lines are still processed |
| `ERROR - Could not write file: ...` | The data folder is not writable, or a document with the same name already exists (see [Known limitations](#known-limitations)) |
| Nothing is printed and no file is written | `--as_agent_plugin 1` prints the modules and writes nothing; without it the addon writes into `--data_dir` and prints `1` per document |
| A performance module is missing | The database returned no value for that metric, or the metrics stage failed (see [Known limitations](#known-limitations)) |

## Reference

### Command-line options

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--hostname` | Yes | — | Db2 host name or IP address |
| `--port` | No | `50000` | Db2 listener port |
| `--protocol` | No | `TCPIP` | Protocol used in the connection string |
| `--database` | Yes | — | Database name on the Db2 server |
| `--uid` | Yes | — | User that runs the statements |
| `--password` | Yes | — | Password for that user |
| `--conf` | Yes | — | Query file. The addon reads it on every run, before the default metrics |
| `--default_metrics` | No | `1` | `1` publishes the default performance modules; any other value disables them |
| `--agent_name` | No | `DB2` | Name of the query agent; the metrics agent is `<agent_name>_metrics` |
| `-g`, `--group` | No | `db2` | Group written in the agent data of both agents |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Folder for the agent data documents in the data folder mode |
| `--as_agent_plugin` | No | `0` | `1` prints the modules on standard output; any other value writes documents into `--data_dir` |
| `--tentacle_address` | No | — | Tentacle server address. It takes precedence over `--as_agent_plugin`, and delivery does not work in version `1.0` |
| `--tentacle_port` | No | `41121` | Tentacle server port |
| `-h`, `--help` | No | — | Prints the usage summary and exits |

### Query file

| Field | Required | Description |
| --- | --- | --- |
| `name` | Yes | Module name |
| `statement` | Yes | Statement executed against the connected database. It cannot contain a colon |
| `module_type` | Yes | Pandora FMS module type, written verbatim into the module |
| `description` | No | Module description |

The field `_database_` in a statement is replaced by the connected database
name in single quotes.

### Generated modules

| Agent | Module | Type | Unit | Source |
| --- | --- | --- | --- | --- |
| Query | As defined in the query file | As defined in the query file | — | One module per statement |
| Metrics | `no_of_bufferpools_<DB_NAME>` | `generic_data` | `count` | Number of buffer pools defined in the database |
| Metrics | `total_logical_reads_<DB_NAME>` | `generic_data` | `count` | Sum of the total logical reads reported by the buffer pools |
| Metrics | `total_physical_reads_<DB_NAME>` | `generic_data` | `count` | Sum of the total physical reads reported by the buffer pools |
| Metrics | `data_logical_reads_<DB_NAME>` | `generic_data` | `count` | Sum of the data logical reads |
| Metrics | `data_physical_reads_<DB_NAME>` | `generic_data` | `count` | Sum of the data physical reads |
| Metrics | `index_logical_reads_<DB_NAME>` | `generic_data` | `count` | Sum of the index logical reads |
| Metrics | `xda_logical_reads_<DB_NAME>` | `generic_data` | `count` | Sum of the XDA logical reads |
| Metrics | `log_utilization_percent_<DB_NAME>` | `generic_data` | `%` | Average transaction log utilization |
| Metrics | `total_log_used_kb_<DB_NAME>` | `generic_data` | `KB` | Total transaction log space in use |
| Metrics | `total_log_available_kb_<DB_NAME>` | `generic_data` | `KB` | Total transaction log space available |

### Exit status

| Status | Meaning |
| --- | --- |
| `0` | Successful run. Also used when the query file cannot be opened or a line of it is malformed |
| `1` | The connection failed, a default-metrics query failed, or a document could not be written |
| `2` | An option received a value of the wrong type, for example a non-integer `--as_agent_plugin` |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.db2_remote` |
| Name | DB2 Remote |
| Version | `1.0` |
| Category | Miscelaneus |
| License | One |
| Marketplace last update | 2025-06-25 |
| Availability | Download limited to licensed users |
| Maintenance | The Marketplace entry states that the addon is no longer actively maintained or updated |
