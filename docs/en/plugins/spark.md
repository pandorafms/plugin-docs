# Pandora Spark

*Article last updated: 2026-10-26.*

## What it does

Pandora Spark reads the REST API of an Apache Spark server and turns the
metrics of every application executor into Pandora FMS modules. Each run lists
the applications the endpoint knows about, then the executors of each
application, and creates **one agent per application** with one module per
executor metric.

The addon is a **server plugin**. Each run builds the agent data documents and
writes them directly into the Pandora FMS data directory, where the Data Server
reads them. It does not deliver through Tentacle, it does not print module XML
on standard output, and it does not create Discovery tasks: the agent appears
in the console because its data file arrives, not because a task generated it.

The plugin only reads from Spark: it issues two HTTP `GET` requests per
application and never writes to the Spark server.

- `http://<ip>/api/v1/applications` — the applications to monitor.
- `http://<ip>/api/v1/applications/<application-id>/executors` — the executors
  of each of those applications.

The same host and port must serve both resources: the plugin builds both URLs
from the single value of `-i` (see [Configure](#configure)).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.spark`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with these versions. This is a published compatibility statement covering the addon, not a test record for it |
| HTTP access from the Pandora FMS server to the Spark REST endpoint | `Required` | The plugin queries `http://<host:port>/api/v1/applications` and the executors resource of each application |
| One host and port serving both `/api/v1/applications` and `/api/v1/applications/<application-id>/executors` | `Required` | Both URLs are built from the single value passed to `-i` |
| A Spark REST endpoint that answers without authentication | `Required` | The plugin sends no credentials, token or session |
| Write access to the Pandora FMS data directory | `Required` | The plugin writes the agent documents into `--data_dir`; it has no other delivery path |
| Spark versions | `Not validated` | No test record has been published for this addon. The legacy guide stated that it had been tried on CentOS 7 and Fedora; nothing in the available evidence establishes a Spark or operating system range |
| Operating system of the Pandora FMS server | `Not validated` | No operating system has been recorded for this version |
| Spark deployments (standalone, YARN, Kubernetes) | `Not validated` | The addon depends on the REST resources above, not on the deployment mode |

### Requirements

1. **A Spark endpoint with the REST API reachable** from the Pandora FMS
   server: the application UI of a running application, or the Spark history
   server for applications that already finished.
2. **A REST endpoint that answers unauthenticated requests.** If Spark is
   configured to require authentication on its REST API, the plugin has no way
   to provide it (see [Operate and troubleshoot](#operate-and-troubleshoot)).
3. **A Pandora FMS server with write access to the data directory**, by default
   `/var/spool/pandora/data_in/`. The plugin writes there, so it runs on the
   Pandora FMS server itself or on a host that writes to that same directory.
4. **The Data Server enabled**, so the documents written into the data
   directory are read and the agents appear in the console.
5. **The Plugin Server enabled**, when the plugin is registered in the console
   and executed from there.
6. **The `pandora_spark` executable** from the addon package.

### Expose the Spark REST API

The plugin can read two different views of a Spark deployment, and the port you
give to `-i` selects which one:

| What you want to monitor | Endpoint that serves it | Default port |
|--------------------------|-------------------------|--------------|
| Applications that are running now | The application UI of the driver | `4040` |
| Applications that already finished | The Spark history server | `18080` |

Those are Spark's default ports; the plugin does not assume either of them, it
queries whatever port you pass.

For running applications, the UI of the first application binds to `4040` and
each additional concurrent application that cannot bind takes the next free
port. One run with `-i <SPARK_HOST>:4040` therefore sees the applications
published on that port, not every application of the cluster.

For finished applications, enable event logging and the history server on the
Spark side. In `spark-defaults.conf`, for example:

```apache
spark.eventLog.enabled           true
spark.eventLog.dir               <EVENT_LOG_PATH>
spark.history.fs.logDirectory    <EVENT_LOG_PATH>
```

The two path keys must point to the same location, and it must be readable by
the history server. Start the history server with the script that ships with the
Spark installation, next to the master and worker start scripts:

```bash
<SPARK_HOME>/sbin/start-history-server.sh
```

Only the port you actually query has to be reachable from the Pandora FMS
server. The plugin makes plain HTTP requests to that port and nothing else, so
the master, worker and submission ports that a Spark cluster needs for its own
operation are not part of this configuration.

Check the endpoint before configuring the plugin:

```bash
curl -s 'http://<SPARK_HOST>:<SPARK_PORT>/api/v1/applications'
```

The answer must be a JSON list of applications. An empty list (`[]`) means the
endpoint is alive but knows no application: the history server has no event
logs yet, or no application has been submitted on that UI port.

### Install the addon

Download the package from the Pandora FMS Marketplace entry, which is limited
to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.spark](https://marketplace.pandorafms.com/entries/pandorafms.spark)

The package is `pandorafms.spark.1.0.pspz2`. Load it with the console package
manager, or register the plugin by hand:

1. Copy the `pandora_spark` executable to the Pandora FMS server, for example
   to `/usr/share/pandora_server/util/plugin/`, and give it execute permission:

    ```bash
    sudo chmod 0755 /usr/share/pandora_server/util/plugin/pandora_spark
    ```

2. Register it in **Servers → Plugins**, as described in
   [Register the plugin in the console](#register-the-plugin-in-the-console).

Nothing is installed on the Spark server, and no Spark client tools are needed
on the Pandora FMS server.

## Configure

The whole configuration of the plugin is its command line. It reads no
configuration file and no environment variable.

### Command line

```bash
./pandora_spark -i <SPARK_HOST>:<SPARK_PORT>
```

- **`-i`, `--ip`** is required and takes `host:port` **without a scheme**. The
  plugin prepends `http://` to the value, so include the port of the endpoint
  that serves the REST API (`4040` or `18080` by default, see
  [Expose the Spark REST API](#expose-the-spark-rest-api)). A value with its own
  scheme builds an invalid URL and the run fails with the connectivity error.
- **`-g`, `--group`** sets the group of the generated agents. Its default is
  `weblogic`, so a run that omits it puts every Spark agent in that group —
  pass the group you want explicitly.
- **`--data_dir`** sets the directory where the agent documents are written. Its
  default is `/var/spool/pandora/data_in/`.

The same run with every option set:

```bash
./pandora_spark -i <SPARK_HOST>:<SPARK_PORT> -g <GROUP_NAME> --data_dir /var/spool/pandora/data_in/
```

There is no option file, no Tentacle delivery, no TLS, no proxy and no
credential input: the endpoint is queried over plain HTTP and whoever can reach
it can read the metrics.

`-h` and `--help` print the usage summary. A run without `-i` prints the usage
line and the missing-argument error on standard error and exits with status `2`
without querying anything.

### Register the plugin in the console

The plugin is designed to be executed by the Pandora FMS Plugin Server, so
Pandora FMS runs it on the schedule of a plugin module:

1. Open **Servers → Plugins** and register the plugin, with a name, the
   description you prefer and the maximum timeout you want for a run.
2. In **Plugin command**, enter the absolute path of the executable on the
   Pandora FMS server, for example
   `/usr/share/pandora_server/util/plugin/pandora_spark`.
3. In **Plugin parameters**, use the plugin macros `_field1_`, `_field2_`, ... as
   placeholders:

    ```text
    -i _field1_ -g _field2_ --data_dir _field3_
    ```

4. In **Macro parameters**, describe each field. The example uses these values:

    | Field | Description | Example value |
    |-------|-------------|---------------|
    | `_field1_` | Spark REST endpoint as `host:port`, without a scheme | `<SPARK_HOST>:4040` |
    | `_field2_` | Group for the generated agents | `Spark` |
    | `_field3_` | Pandora FMS data directory | `/var/spool/pandora/data_in/` |

<!-- SCREENSHOT NEEDED: Pandora FMS server plugin registration form for pandora_spark with the three macro parameters filled and no real hostnames. -->

Once registered, create a plugin module that executes it, with the same field
values. The module runs on the Pandora FMS server and each execution creates
the Spark agents. The module itself receives the plugin output (`1` on a
successful run), while the Spark metrics arrive through the data directory, in
the agents named after each application.

The `-g` value in the parameters is inherited by every execution of that
module. If you monitor two Spark endpoints, register the plugin once and create
one module per endpoint with its own fields, using a different group for each
one so the two sets of agents stay apart.

<!-- SCREENSHOT NEEDED: plugin module creation form for pandora_spark showing the field values and the target Pandora FMS server. -->

### Delivery and permissions

- Every run writes files named `<agent-name>.<epoch-seconds>.data` into
  `--data_dir`. Each Spark application gets its own agent name, so applications
  do not share documents.
- The directory must exist and be writable by the user that runs the plugin.
  When the write fails, the plugin reports nothing and still ends with `1` (see
  [Operate and troubleshoot](#operate-and-troubleshoot)).
- The files must be readable by the Pandora FMS Data Server. Do not change their
  owner or move them: the Data Server deletes them after processing.
- Nothing travels over the network towards Pandora FMS. If the plugin runs on a
  remote Pandora FMS server, `--data_dir` must point to that server's own data
  directory, not to the main server's.

## Verify

1. Confirm that the endpoint answers with a JSON list:

    ```bash
    curl -s 'http://<SPARK_HOST>:<SPARK_PORT>/api/v1/applications'
    ```

2. Run the plugin once from a terminal on the Pandora FMS server:

    ```bash
    ./pandora_spark -i <SPARK_HOST>:<SPARK_PORT> -g <GROUP_NAME>
    ```

3. A successful run prints `1` and exits with status `0`. Then the data files
   are in the data directory:

    ```bash
    ls -l /var/spool/pandora/data_in/Spark_application*
    ```

    The files disappear as the Data Server processes them, so an empty listing
    shortly after the run can also mean that the documents were already
    consumed. Check the console instead.

4. In the console, one agent per Spark application appears with its modules on
   the next data cycle.

<!-- SCREENSHOT NEEDED: Pandora FMS agent detail view of one Spark application agent listing the executor modules received. -->

If the endpoint cannot be reached, the run prints `0` on standard output and
this message on standard error, then exits with status `1`:

```text
Error requesting http://<SPARK_HOST>:<SPARK_PORT>/api/v1/applications, please check conectivity
```

## Understand the results

### Generated agents

The addon creates **one agent per application** returned by the first request.
The agent is named after the application identifier, so an identifier such as
`application_1630567890123_0001` produces the agent name
`Spark_applicationapplication_1630567890123_0001`: the prefix `Spark_application`
is added in front of the identifier as Spark reports it, with no separator.

| Property | Value |
|----------|-------|
| Agent name | `Spark_application` followed by the application identifier |
| Agent alias | `Spark_application` followed by the application name |
| Description | `Spark_application_detailed stats` |
| Address | `127.0.0.1` |
| Group | The value of `-g`; `weblogic` when the option is omitted |
| Parent agent | None |
| Interval | Not set: the agent keeps the interval Pandora FMS assigns by default |

Two consequences are worth knowing before you build alerts on these agents:

- The address is fixed at `127.0.0.1` and does not identify the Spark server.
  In the console the agent looks local even when the endpoint is remote.
- The application name is copied into the agent alias without escaping. A name
  that contains a single quote (`'`) produces a document Pandora FMS cannot
  read, and the agent is not created.

### What one run delivers

- The plugin asks for the executor list of every application, one application
  after another, and builds each agent document from the executor data of that
  application.
- **One document is written per executor.** Documents are named after the agent
  and the second of the run, so all the executors processed within the same
  second produce the same file name: the first one is kept and the following
  ones are discarded without any message. In practice a run delivers the
  modules of the first executor of each application, plus those of the executors
  that happen to be processed in a later second.
- **The module list is not reset between applications.** The document of the
  second and following applications also carries a copy of the modules of the
  applications processed before it in the same run, so module names repeat
  inside one document. With a single application — the common case — this has
  no effect.

### Modules

Each executor produces 14 modules whose name is the executor identifier
followed by the metric name, concatenated with no separator: an executor with
identifier `1` publishes `1hostPort`, `1rddBlocks`, `1memoryUsed`, and so on.
The executor identifier is `driver` for the driver and a number for the other
executors. Two applications that reuse the same executor identifiers produce
modules with the same names, one set per agent.

`id` and `hostPort` are text modules (`generic_data_string`); the other twelve
are numeric modules (`generic_data`) with no unit. The plugin copies every value
as the API returns it: it does not convert, round, rescale or attach units, and
it sets no thresholds and no alerts. The full list with the meaning of each
value is in [Generated modules](#generated-modules).

## Operate and troubleshoot

### Everyday operation

- The plugin keeps no state between runs: every execution queries the endpoint
  at that moment, so it can be run manually at any time without affecting the
  next scheduled run.
- There is no timeout on the requests. An endpoint that accepts the connection
  and does not answer keeps the run blocked until the Plugin Server timeout
  terminates it, so set a maximum timeout in the plugin definition.
- There is no authentication support: no user, password, token or TLS client
  certificate. A Spark REST API that requires authentication answers `401`, the
  plugin cannot read the answer as an application list, and the run ends with
  the connectivity error.
- Only plain HTTP is used: every request goes to `http://`, so an endpoint that
  offers HTTPS only cannot be monitored by this addon.
- The group defaults to `weblogic`. Agents created by a run that omits `-g` land
  in that group and are easy to miss in the console.
- A failed write is silent: when the data directory does not exist or is not
  writable, the run still prints `1` and reports nothing. Do not use the output
  of the plugin to decide that the data arrived; check the console.
- A run against a Spark endpoint with no application prints `1` and creates no
  agent. That is the expected result, not an error.

### Troubleshooting

- **The run prints `0` and the message `Error requesting .../api/v1/applications`** —
  the first request did not return a readable application list. Check the port,
  the firewall between the Pandora FMS server and Spark, and that the endpoint
  answers `curl` from the same host. The same message appears when the answer is
  not JSON, including a `401` from an endpoint that requires authentication.
- **The run prints `0` and the message names `.../executors`** — the application
  list was read, but the executors of the application in the message could not
  be. The run stops at that point: the documents of the applications already
  processed are written, the remaining ones are not. Check that the same port
  serves the executors resource of that application, which is not the case when
  the application moved to the history server in the meantime.
- **The run prints `1` but no agent appears in the console** — the documents
  were not written or not read. Confirm that `--data_dir` is the data directory
  of the Pandora FMS server that is running, that it is writable by the plugin
  user, and that the Data Server is enabled. Remember that the plugin does not
  report write failures.
- **An agent shows fewer executors than the application has** — the documents
  of the remaining executors were written within the same second and discarded
  because of the file name collision. Run the plugin again later, or accept that
  the addon publishes the first executor of each application per run.
- **The agent shows modules of another application** — both applications were
  processed in the same run and the module list is shared between them. Run the
  plugin with one application per execution when you need a clean agent.
- **A module has no value or the agent is missing entirely** — check the
  application name for a single quote, which breaks the document as explained
  in [Generated agents](#generated-agents).
- **The agents are in the wrong group** — `-g` was omitted and the default
  `weblogic` was applied, or the registered macro has an empty value.
- **The metrics look frozen** — the plugin reports the counters of the executor
  at the moment of the query. A finished application keeps the values of its
  last state in the history server, so a history-server endpoint shows the same
  numbers run after run. Use `4040` to follow a live application.

## Reference

### Command-line options

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `-i`, `--ip` | Yes | — | Spark REST endpoint as `host:port`, without a scheme. The plugin calls `http://<value>/api/v1/applications` and `http://<value>/api/v1/applications/<application-id>/executors`. |
| `-g`, `--group` | No | `weblogic` | Group assigned to the generated agents. |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directory where the agent documents are written. Must exist and be writable by the user that runs the plugin. |
| `-h`, `--help` | No | — | Prints the usage summary and exits. |

The plugin reads no configuration file and no environment variable, and it
accepts no credentials. A run without `-i` exits with status `2`.

### Output and exit status

| Situation | Standard output | Standard error | Exit status |
|-----------|-----------------|----------------|-------------|
| Successful run | `1` | — | `0` |
| The applications request fails, or its answer is not a JSON list | `0` | `Error requesting <url>, please check conectivity` | `1` |
| The executors request of one application fails | `0` | `Error requesting <url>, please check conectivity` | `1` |
| `-i` is missing | — | Usage line and missing-argument error | `2` |

A run that cannot write a data document still reports success: the failure is
not reflected in the output nor in the exit status.

### Generated agents

| Property | Value |
|----------|-------|
| Agent name | `Spark_application` + application identifier, concatenated with no separator |
| Agent alias | `Spark_application` + application name |
| Description | `Spark_application_detailed stats` |
| Address | `127.0.0.1` |
| Group | `-g` value; `weblogic` by default |
| Parent agent | None |
| Interval | Not set |
| Timestamp | Time of the run, `YYYY/MM/DD HH:MM:SS` |
| Cardinality | One agent per application returned by the endpoint |

### Generated modules

`<executor>` is the executor identifier reported by Spark: `driver` for the
driver and a number for each executor.

| Module name | Type | Value |
|-------------|------|-------|
| `<executor>id` | `generic_data_string` | Executor identifier |
| `<executor>hostPort` | `generic_data_string` | Host and port of the executor |
| `<executor>rddBlocks` | `generic_data` | RDD blocks held by the executor |
| `<executor>memoryUsed` | `generic_data` | Memory used, in bytes |
| `<executor>diskUsed` | `generic_data` | Disk space used, in bytes |
| `<executor>activeTasks` | `generic_data` | Tasks running in the executor |
| `<executor>failedTasks` | `generic_data` | Tasks that failed in the executor |
| `<executor>completedTasks` | `generic_data` | Tasks completed by the executor |
| `<executor>totalTasks` | `generic_data` | Tasks assigned to the executor |
| `<executor>totalDuration` | `generic_data` | Accumulated task time, in milliseconds |
| `<executor>totalInputBytes` | `generic_data` | Bytes read by the executor |
| `<executor>totalShuffleRead` | `generic_data` | Bytes read in shuffles |
| `<executor>totalShuffleWrite` | `generic_data` | Bytes written in shuffles |
| `<executor>maxMemory` | `generic_data` | Memory available to the executor |

The two text modules are published with an empty unit; the numeric ones carry no
unit. Values are forwarded as the API returns them, so a field that Spark
reports with a unit in its text (as it does for `maxMemory`) reaches the module
with that text, and the comparison, thresholds and representation of the module
are up to Pandora FMS.

### Addon identity

| Field | Value |
|-------|-------|
| Marketplace identifier | `pandorafms.spark` |
| Marketplace name | Pandora Spark |
| Addon version | `1.0` |
| Marketplace package | `pandorafms.spark.1.0.pspz2` |
| Marketplace last update | 2025-06-27 |
| License | One — download limited to licensed users |
| Marketplace type | Miscelaneus |
| Workflow | Monitoring plugin, server plugin mode |
| Executable | `pandora_spark` |
