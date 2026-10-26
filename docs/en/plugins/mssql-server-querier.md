# MSSQL Server Querier Tool

*Article last updated: 2026-10-26.*

## What it does

`msql_query` runs one SQL query against a Microsoft SQL Server database and
prints the result on standard output. Pandora FMS executes it as a server
plugin, so that output is the value of the module that calls it: a count, a
size, a status code or any other single value a query can return.

Each run opens a connection, executes one query and exits. The command keeps
no state and creates no agent. The module, its interval, its thresholds and
its alerts belong to Pandora FMS; the query supplies only the value.

The addon documents two invocation forms under the same `msql_query` name:

- **Flag-based form.** The connection and the query are passed as options
  (`-Q`, `-U`, `-P`, `-H`, `-D`). The output starts with a header line that
  contains the column names and continues with one tab-separated line per
  row. The connection selects no database, so SQL Server uses the default
  database of the login.
- **Positional form.** The connection and the query are passed as ordered
  arguments. The output has no header line, and the fields of each row are
  joined with a delimiter, `,` by default.

Both forms return plain text: results go to standard output and errors go to
standard error. Neither writes files, sends data to Pandora FMS by itself or
returns the result in a structured format.

The Marketplace entry marks this addon as no longer actively maintained.

This page does not describe the Microsoft SQL Server Discovery addon
(`pandorafms.mssql`), which creates agents and modules from Discovery tasks;
see [Microsoft SQL Server Discovery](../discovery/mssql-discovery.md).

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.mssql_querier`, version `1.0` | Documented target | The Marketplace package version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that its integrations are compatible with Pandora FMS NG 784 and later versions |
| Network access from the Pandora FMS server to the SQL Server instance (TCP, `1433` by default) | `Required` | Both forms open a TCP connection to SQL Server. The positional form always uses port `1433` |
| A SQL Server login allowed to run the query | `Required` | The command authenticates with the login and password you pass to it |
| Microsoft ODBC Driver 18 for SQL Server on the Pandora FMS server | `Required` | The positional form requests that driver by name |
| An ODBC driver for SQL Server and the DBI ODBC package on the Pandora FMS server | `Required` | The flag-based form connects through DBI over ODBC |
| Microsoft SQL Server versions | `Not validated` | No SQL Server version matrix has been recorded for this addon |
| Operating system of the Pandora FMS server | `Not validated` | No operating system has been recorded for this version |

### Prerequisites

1. **A Pandora FMS server** that can reach the SQL Server instance over the
   network. The command runs on the Pandora FMS server, not on the database
   host.
2. **A SQL Server login and password** that can connect to the database and
   run the query you configure. No narrower permission set is published for
   this addon: grant the login only what the queries read.
3. **The database connectivity components required by the invocation form you
   use**, as listed in [Compatibility](#compatibility).
4. **The `msql_query` executable** from the addon package, copied to the
   Pandora FMS server.

The command reads no configuration file and no environment variables: every
setting is a command-line argument.

### Install the addon

Download the package from the Marketplace entry, whose download is limited to
licensed users, and extract the executable. The vendor documentation calls
the command `msql_query`.

Copy it to the Pandora FMS server and make it executable:

```bash
sudo cp msql_query /usr/share/pandora_server/util/plugin/msql_query
sudo chmod 0755 /usr/share/pandora_server/util/plugin/msql_query
```

Nothing has to be installed on the SQL Server host, and no agent is involved.

## Configure

All the configuration is a command line: the invocation form, the connection
values and the query. Pandora FMS runs the command in two ways:

- **As a server plugin.** Register the executable once in the console and
  create the module that calls it. Each run's standard output becomes the
  module value.
- **Manually or from a scheduler** such as `cron`, to test the command or to
  obtain the value outside a console module.

### Register the command as a server plugin

1. Open **Servers → Plugins** and register a new server plugin.
2. Set its command to the absolute path of the executable, for example
   `/usr/share/pandora_server/util/plugin/msql_query`.
3. Write the parameters with the options of the form you use, and replace the
   query and the credentials with plugin fields: `_field1_`, `_field2_`, ...

```text
-Q _field1_ -U _field2_ -P _field3_ -H _field4_
```

| Field | Description |
| --- | --- |
| `_field1_` | SQL query |
| `_field2_` | SQL Server login |
| `_field3_` | Password for that login; mark the value as hidden |
| `_field4_` | SQL Server host, including the instance when one is needed |

The same registration serves every query: each module fills the fields with
its own query and credentials. For the positional form, write the arguments
in their order and use the fields in the same positions.

<!-- SCREENSHOT NEEDED: server plugin registration form for msql_query, showing the command path and the parameter fields with a query and masked credentials. -->

### Flag-based invocation

```bash
./msql_query -Q "SELECT 1 AS total" -U <USERNAME> -P <PASSWORD> -H <TARGET_HOST>
```

- `-Q` is the query. Without it the command prints its usage summary and
  exits without connecting.
- `-H` defaults to `localhost`.
- `-D` sets the ODBC driver name and defaults to
  `ODBC Driver 17 for SQL Server`.
- There is no database option: the connection selects no database and SQL
  Server uses the default database of the login. Qualify objects as
  `database.schema.table` when the query must read another database.
- Options are read in pairs and their letter is not case-sensitive. An
  argument the command does not recognise makes it print the usage summary
  and exit.
- The output contains a first line with the column names and then one
  tab-separated line per row.

### Positional invocation

```bash
./msql_query "<TARGET_HOST>" "<USERNAME>" "<PASSWORD>" "<DB_NAME>" "SELECT 1 AS total" "none"
```

- The order is host, login, password, database, query, empty-result text and
  delimiter.
- Six arguments are required in practice. With fewer, the command prints
  `Not enough arguments in call.` and the usage summary, although the vendor
  documentation marks the empty-result text as optional. Pass any value, for
  example `none`, when you do not need it.
- The empty-result text is accepted but never printed in this version: when
  the query returns no rows, the command prints nothing.
- The port is fixed at `1433`. This form has no argument to change it.
- The delimiter is `,` unless you pass a seventh argument. A delimiter passed
  as the sixth argument is read as the empty-result text and has no effect.
- The output has no header line: each row is printed with its fields joined
  by the delimiter.
- The connection sets `TrustServerCertificate=yes` and accepts any server
  certificate.

The same run with `;` as the field delimiter:

```bash
./msql_query "<TARGET_HOST>" "<USERNAME>" "<PASSWORD>" "<DB_NAME>" "SELECT 1 AS total" "none" ";"
```

### Credentials and transport

- Both forms take the password as a command-line argument. It is visible in
  the process list while the command runs and stays in the shell history. In
  the console it is stored with the plugin or module definition. Use a
  dedicated login limited to what the queries read, and restrict who can read
  module definitions and who can inspect processes on the server.
- If you invoke the command from a script or a `cron` entry, that file holds
  the password in plain text. Protect it with file permissions.
- The connection string is assembled by concatenation: a login or a password
  that contains `;` breaks it and the connection fails. Use credentials that
  do not contain that character.
- The flag-based form passes no encryption options. Encryption and
  certificate validation come from the ODBC driver configuration on the
  Pandora FMS server.
- The positional form always sets `TrustServerCertificate=yes`: the client
  accepts any certificate the server presents, so the connection does not
  authenticate the SQL Server. Use it only on a trusted network or against an
  instance whose identity you verify another way.

## Verify

Run the form you configured manually before you rely on the module. A scalar
query without table dependencies proves connectivity, authentication and
output shape at once.

Flag-based form:

```bash
./msql_query -Q "SELECT 1 AS total" -U <USERNAME> -P <PASSWORD> -H <TARGET_HOST>
```

Expected output: the column name and then the value.

```text
total
1
```

Positional form:

```bash
./msql_query "<TARGET_HOST>" "<USERNAME>" "<PASSWORD>" "<DB_NAME>" "SELECT 1 AS total" "none"
```

Expected output:

```text
1
```

Repeat the run with a wrong password. The flag-based form prints
`Can't connect to <TARGET_HOST>: ...` on standard error and exits with a
non-zero status. The positional form prints the database driver error on
standard error and exits with a non-zero status.

In the console, the module that calls the command shows the value you saw in
the manual run. Confirm that the module uses the same query and the same
login.

## Understand the results

The command returns text, and that text is the whole module value. It does
not classify the result, add units or compare thresholds: thresholds, alerts
and graph settings are configured on the Pandora FMS module, and the query
only supplies the value they act on.

- **One value per run.** A module stores one value. Write queries that return
  a single row and, for numeric modules, a single column. Both forms print
  every row the query returns, so a query with several rows produces several
  output lines.
- **Header line (flag-based form only).** The first output line contains the
  column names, so a one-row result is two lines. The positional form prints
  only the row data.
- **Delimiter (positional form only).** The fields of a row are joined with
  `,` unless you pass another delimiter. With several columns, the module
  value contains the joined fields.
- **Empty result.** The flag-based form prints only the header line; the
  positional form prints nothing. The empty-result argument of the positional
  form has no effect.
- **NULL values.** A `NULL` is printed as `None` by the positional form and
  as an empty field by the flag-based form. Use `ISNULL()` or `COALESCE()` in
  the query when a numeric module must always receive a number.
- **Exit status.** A successful run exits `0`. A connection or SQL error
  exits non-zero. An argument error prints the usage summary and exits `0`,
  so the module can receive the usage text as its value.

## Operate and troubleshoot

- Every run is independent: the command connects, runs the query and exits.
  There is no daemon, no cache and no state to reset.
- The command has no timeout of its own. A query that blocks keeps the
  execution open until SQL Server or the caller stops it. Set a timeout in the
  Pandora FMS plugin or module configuration when a query can run long.
- Avoid running the command from an interactive shell with the real password
  when that shell records its history. Use the console module or a protected
  script instead.

| Symptom | Cause and fix |
| --- | --- |
| The usage summary appears instead of a value (flag-based form) | `-Q` is missing, or an argument was not recognised as an option. Check the option letters and that every option has a value. The command exits `0`, so the module can store the usage text. |
| `Not enough arguments in call.` or `Too much arguments in call.` (positional form) | Fewer than six or more than seven arguments. Add the empty-result argument even when you do not need it, and remove extra arguments or join the query into one argument. |
| `Can't connect to <TARGET_HOST>: ...` (flag-based form) | The host, the instance, the login or the password is wrong, port `1433` is not reachable, or the instance does not accept SQL Server logins. |
| `Can't prepare statement: ...` or `Problem while executing: ...` (flag-based form) | The query is not valid for the login or for the default database. Run the same query with the same login in another SQL client. |
| A database driver error on standard error (positional form) | The connection failed or the query was rejected. The message names the driver error; check the host, the credentials, the database and the SQL syntax. |
| A driver or data-source error from the ODBC layer | The ODBC driver name does not exist on the server. Install the driver, or point `-D` at the exact name the server has. |
| The module has no value | The query returned no rows or only `NULL` values. Check the query and the data. |
| A numeric module has no data or an unexpected value | The output contains a header line, more than one row, joined columns or `None`. Return a single numeric scalar in a single row. |
| The connection fails with a password that contains `;` | The semicolon ends the value in the connection string. Use a password without `;`. |

## Reference

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.mssql_querier` |
| Name | MSSQL Server Querier Tool |
| Version | `1.0` |
| Marketplace last update | 2025-06-27 |
| Category | Miscelaneous |
| License | One; the download is limited to licensed users |
| Maintenance status | No longer actively maintained, as stated by the Marketplace |
| Marketplace entry | [pandorafms.mssql_querier](https://marketplace.pandorafms.com/entries/pandorafms.mssql_querier) |

### Flag-based parameters

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `-Q` | Yes | — | SQL query to execute |
| `-U` | Yes | — | SQL Server login |
| `-P` | Yes | — | Password for the login |
| `-H` | No | `localhost` | SQL Server host, or `host\instance` |
| `-D` | No | `ODBC Driver 17 for SQL Server` | ODBC driver name used for the connection |

`-D` names the ODBC driver, not the database. The command has no database
option and no dedicated help option: it prints its usage summary when the
query option is missing or when it meets an argument it does not recognise.

### Positional parameters

| Position | Argument | Required | Default | Description |
| --- | --- | --- | --- | --- |
| 1 | host | Yes | — | `host` or `host\instance`. The connection always uses TCP port `1433` |
| 2 | login | Yes | — | SQL Server login |
| 3 | password | Yes | — | Password for the login |
| 4 | database | Yes | — | Database the connection selects |
| 5 | query | Yes | — | SQL query to execute |
| 6 | empty-result text | Yes in practice | — | Accepted and never printed in this version; pass any value |
| 7 | delimiter | No | `,` | Field separator for each row |

### Output and exit status

| Condition | Flag-based form | Positional form |
| --- | --- | --- |
| The query returns rows | A header line with the column names, then one tab-separated line per row; exit `0` | One delimiter-separated line per row, without a header; exit `0` |
| The query returns no rows | The header line only; exit `0` | No output; exit `0` |
| The connection fails | `Can't connect to ...` on standard error; non-zero exit | The driver error on standard error; non-zero exit |
| The query fails | `Can't prepare statement: ...` or `Problem while executing: ...` on standard error; non-zero exit | The driver error on standard error; non-zero exit |
| Arguments are missing or unknown | The usage summary on standard output; exit `0` | The usage summary on standard output; exit `0` |

Both forms return only text on standard output. The command reads no
configuration file and no environment variables, and it keeps no state
between runs.
