# Tomcat monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The plugin monitors an Apache Tomcat instance from Pandora FMS. Each run
authenticates against the Tomcat Manager web application, reads the connector
and JVM status document and the JVM information report, and builds **one
Pandora FMS agent** whose modules are the metrics it collected. The agent
document is then delivered to Pandora FMS with Tentacle or copied into a local
data folder.

Nothing is installed on the Tomcat host: the plugin runs on a host that can
reach the Manager application, and it keeps no state between runs. Every
execution reads the current state again.

The plugin is a standalone command that delivers its own agent. It is not an
agent plugin and prints no module XML for a Pandora FMS agent to collect; it
prints `1` when a run completes and `0` when it stops with an error. See
[Verify](#verify) for what that output does and does not prove.

Two reads are configured independently, and each one produces its own group of
modules:

- **Status document** (`/manager/status/all?XML=true`): free, total and maximum
  JVM memory, plus the thread and request counters of a connector.
- **JVM information report** (`/manager/text/vminfo`): runtime, operating
  system, thread, class loading, compilation, garbage collector and memory pool
  metrics of the JVM that runs Tomcat.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.tomcat`, version `1.0` | Documented target | The Marketplace package version this page describes. See [Addon identity](#addon-identity) |
| The Tomcat Manager web application deployed at `<TARGET_HOST>:<port>` | `Required` | Every read is an HTTP request to `/manager/status/all?XML=true` or `/manager/text/vminfo` |
| A Tomcat user with the `manager-script` role | `Required` | The Manager application restricts `/manager/text/*` to that role and also admits it on `/manager/status/*` |
| Network access from the plugin host to the Tomcat connector | `Required` | The plugin connects from the host where it runs |
| Network access to the Tentacle port, `41121` by default | `Required` when the delivery is not a local copy | Tentacle delivery is the default |
| A writable `/var/spool/pandora/data_in/` on the plugin host | `Required` for the local copy | `transfer_mode=local` moves the document into that folder |
| Tomcat versions | `Not validated` | No version matrix has been recorded for version `1.0` |
| Operating system of the plugin host | `Not validated` | No operating system has been recorded for version `1.0` |
| Pandora FMS NG 784 and later | `Not validated` | No release-specific validation record exists. The Marketplace states that its integrations are compatible with Pandora FMS NG 784 and later |

### Requirements

1. **A Tomcat installation with the Manager web application deployed.** Every
   read targets a `/manager/...` path, so a Tomcat without the Manager
   application cannot be monitored by this plugin.
2. **A Tomcat user with the `manager-script` role** in `tomcat-users.xml`, as
   described in [Create the Tomcat user](#create-the-tomcat-user).
3. **Network access** from the plugin host to the connector that answers the
   Manager application.
4. **A destination for the generated agent**: the Pandora FMS Tentacle service,
   or a local data folder that the Pandora FMS server reads.
5. **A host to run the plugin.** The Pandora FMS server itself is the usual
   choice, because the agent is delivered from there.

### Create the Tomcat user

The plugin authenticates with HTTP Basic against the Manager application. Add a
user with the `manager-script` role to the Tomcat user file:

```xml
<tomcat-users>
  <role rolename="manager-script"/>
  <user username="<USERNAME>" password="<PASSWORD>" roles="manager-script"/>
</tomcat-users>
```

`manager-script` is the only role the plugin needs: the Manager application
maps the `/text/*` interface to that role and also accepts it on the `/status/*`
interface. Apply the change and restart Tomcat.

Credentials travel with every request:

- Over plain HTTP the user and the password are sent unencrypted, in a header
  that is only encoded, not encrypted. Use `https=1` when the path between the
  plugin host and Tomcat is not trusted.
- The password is stored in the plugin configuration file in plain text.
  Restrict the file permissions to the user that runs the plugin.

### Install the plugin

Download the addon from the Pandora FMS Marketplace entry, which is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.tomcat](https://marketplace.pandorafms.com/entries/pandorafms.tomcat)

Install the executable on the host that will run it and keep its configuration
file next to it. The plugin takes that file as its only argument, so any
location is valid as long as the execution uses the same path. Give the
executable permission to run.

## Configure

The plugin takes a single option, `--conf`, with the path of its configuration
file:

```bash
./pandora_tomcat --conf <PATH_TO_CONFIG>
```

The configuration file is an INI file with a single section named `CONF`. The
values in it override the built-in defaults. These rules apply:

- **The `[CONF]` header is mandatory.** A file with only `key=value` lines, as
  the previous generation of the addon used, is rejected: the plugin prints the
  parser message and `0` and exits (see [Troubleshooting](#troubleshooting)).
- **Only the keys inside `[CONF]` are read.** A key written outside the section
  is ignored and its default applies.
- **A missing key keeps its default.** The default of every key is listed in
  [Configuration file](#configuration-file).
- **Do not put comments after a value.** Everything after the `=` reaches the
  plugin as part of the value; use whole lines that start with `#` for comments.
- **A repeated key keeps its last value.**

Use `password`, not `pass`: the plugin reads the key `password` only. Keys from
the previous generation of the addon — `pass`, `instance`, `custom_url`,
`threads`, `MODULE_GROUP`, `enable_thread_monitoring`,
`enable_jvm_memory_monitoring` and the rest — are read by nothing and change
nothing.

### Connection to Tomcat

```ini
[CONF]
host=<TARGET_HOST>
port=8080
user=<USERNAME>
password=<PASSWORD>
https=0
```

- `host` is a bare host name or IP address. It takes no scheme and no port: the
  plugin builds `http://<host>:<port>/manager/...` itself, so a value such as
  `http://<TARGET_HOST>` is taken as a host named `http` and the run fails to
  connect.
- `port` is the connector that serves the Manager application, `8080` by
  default. A non-numeric value is read as `0`.
- `https` switches the scheme to `https` only when its value is exactly `1`.
  Any other value, including `true`, keeps `http`.
- The Manager context path is fixed to `/manager`. A Tomcat whose Manager
  application is deployed under another path cannot be configured here.

### Choose what to collect

```ini
enable_status_monitoring=1
enable_vminfo_monitoring=1
```

Each switch enables its read only when its value is exactly `1`; `0`, `2`, an
empty value or a non-numeric value disables it. This is not the "any value
greater than zero" rule of some other addons.

- `enable_status_monitoring` collects the status document. It produces the
  three JVM memory modules and the thread and request modules of a connector.
- `enable_vminfo_monitoring` collects the JVM information report.

With both switches disabled the plugin still builds and delivers an agent, but
the agent has no modules.

### Filter the metric names

```ini
allow_regexp=
deny_regexp=
```

Both values are regular expressions matched anywhere in the metric name:

- `allow_regexp`: when it is not empty, only the metrics whose name contains a
  match are published. `allow_regexp=bytes` keeps `bytesReceived` and
  `bytesSent` and drops the rest.
- `deny_regexp`: metrics whose name contains a match are dropped.
- Both empty, the default, applies no filter.

The filters apply to the connector thread and request metrics and to the JVM
information metrics. They do not apply to `memory_free`, `memory_total` or
`memory_max`.

### Agent identity

```ini
agent_name=Tomcat
agents_group_name=tomcat
interval=300
module_prefix=
```

- `agent_name` is the alias of the generated agent. The agent name that Pandora
  FMS stores is a 32-character hash derived from this value, so the configured
  text identifies the agent as its alias and never as its name. Changing
  `agent_name` changes the hash and creates a different agent, leaving the
  previous one without data.
- `agents_group_name` is the group of the agent, by name.
- `interval` is the agent interval in seconds. A non-numeric value is read as
  `0`.
- `module_prefix` is prepended to every module name with no separator, so
  `module_prefix=tc01` turns `maxThreads` into `tc01maxThreads`. Leave it empty
  unless the modules of several Tomcat instances must be told apart.

### Delivery to Pandora FMS

Tentacle is the default. It needs the Tentacle server address:

```ini
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_URL>
tentacle_port=41121
```

The local copy writes the document into the Pandora FMS data folder, which is
the usual choice when the plugin runs on the Pandora FMS server itself:

```ini
transfer_mode=local
```

- `transfer_mode` selects the local copy only when its value is exactly
  `local`. Any other value, including the default `tentacle` and a misspelling
  such as `tentacle_`, delivers with the Tentacle client.
- The Tentacle client is the `tentacle_client` executable found in `PATH`. The
  client errors are written to standard error.
- `temporal`, `data_dir`, `tentacle_client` and `tentacle_opts` are accepted
  and ignored. The document is always written to `/tmp`, the local copy always
  goes to `/var/spool/pandora/data_in/`, and no extra Tentacle options are
  passed. Create `/var/spool/pandora/data_in/` before the first local run.

### Run it from Pandora FMS

The plugin delivers its own agent, so it runs as a scheduled command on a host,
not as a module of a Pandora FMS agent:

- **As a server plugin.** Register the executable in the console as a standard
  server plugin and pass `--conf <PATH_TO_CONFIG>` as its parameters. Pandora
  FMS then runs it on the server that owns the module, at the plugin interval.
- **As a scheduled job.** Add the command to the `cron` of the plugin host, as
  described in [Scheduled execution](#scheduled-execution).

Do not register it as an agent plugin expecting module XML: it prints `1` or
`0`, not modules. Running it from an agent command produces that single value
as a module while the Tomcat agent is delivered separately.

<!-- SCREENSHOT NEEDED: Pandora FMS server plugin registration form with the path to the pandora_tomcat executable and --conf <PATH_TO_CONFIG> as parameters, no real hostnames or credentials. -->

## Verify

Run the plugin manually from a terminal, passing the configuration file:

```bash
./pandora_tomcat --conf <PATH_TO_CONFIG>
```

Each run executes once and exits.

- `1` on standard output means the run reached the end without an exception.
  It does **not** prove that the agent reached Pandora FMS.
- `0` on standard output means the run stopped with an error it handled. The
  error message is printed on the line before the `0`.
- A traceback on standard error, with no `1` and no `0`, means the run stopped
  before delivering anything: the Manager application could not be reached, the
  credentials were rejected, or the answer was not the expected document.

A run with no argument, or with `--conf` and no value, prints the usage summary
and exits with status `2`. `-h` prints the same summary and exits with status
`0`.

Then confirm the arrival in the console: an agent with the configured
`agent_name` as its alias — its stored name is the 32-character hash described
in [Agent identity](#agent-identity) — carrying the modules described in
[Understand the results](#understand-the-results) once the interval has passed.

<!-- SCREENSHOT NEEDED: Pandora FMS agent detail view of the Tomcat agent, showing the configured alias and the connector thread and request modules with data, no real hostnames or credentials. -->

A run that prints `1` does not prove that every collection worked either: see
[Known limitations of this version](#known-limitations-of-this-version).

## Understand the results

The plugin always produces **one agent**. Its modules fall into four groups:

- **JVM memory.** `memory_free`, `memory_total` and `memory_max` report the
  values of the `<memory>` element of the status document, in bytes. Their
  value is written with braces and quotes, so they are not usable as numbers in
  this version; see the limitations below.
- **Connector threads.** One module per attribute of the first connector's
  thread information: `maxThreads`, `currentThreadCount` and
  `currentThreadsBusy` in a current Tomcat.
- **Connector requests.** One module per attribute of the first connector's
  request information: `maxTime`, `processingTime`, `requestCount`,
  `errorCount`, `bytesReceived` and `bytesSent`.
- **JVM information.** One module per line of the JVM information report that
  survives the plugin filter, named after the line label with the spaces
  replaced by underscores, for example `heap_used` or `availableprocessors`.

Every module is declared as `generic_data`, including the ones whose value is
text, and none of them carries a unit, a threshold or a module group. Values
that describe bytes are therefore published as plain numbers.

The agent is created with the configured group and interval, an empty operating
system, an empty address and the timestamp of the run. It has no parent agent.

## Operate and troubleshoot

### Scheduled execution

The plugin has no internal scheduler, so an external one runs it: the server
plugin scheduler of Pandora FMS, or a `cron` entry on the plugin host:

```cron
*/5 * * * * root /usr/share/pandora_server/util/plugin/pandora_tomcat --conf <PATH_TO_CONFIG>
```

Match the schedule to the agent interval so the agent receives data at the rate
the console expects for it.

### Run behaviour

- The plugin keeps no state between runs and can be executed manually at any
  time.
- It sets no request timeout. A Manager application that accepts the connection
  and never answers keeps the run waiting; bound the execution externally when
  that risk exists, for example by running the command through `timeout`.
- When it receives `SIGTERM` it prints `Received SIGTERM signal. Cleaning up...`
  and exits with status `0`. A run cut short this way is not distinguished from
  a completed one by its exit status.

### Known limitations of this version

- **The three JVM memory modules carry a wrapped value.** `memory_free`,
  `memory_total` and `memory_max` are written as `{'<number>'}`, braces and
  quotes included, instead of a bare number. Pandora FMS cannot read them as a
  numeric series. The connector and JVM information modules are not affected.
- **Only the first connector is read.** The plugin takes the first `<threadInfo>`
  and the first `<requestInfo>` of the status document and names their modules
  after the attribute alone. On a Tomcat with several connectors, only the one
  that appears first is collected, and the modules do not identify which
  connector they belong to.
- **The agent name is a hash.** Pandora FMS stores the agent under a
  32-character hash; `agent_name` is sent as the alias. Plan the name before the
  first run, because changing it creates a new agent.
- **`temporal`, `data_dir`, `tentacle_client` and `tentacle_opts` do nothing.**
  The write folder is always `/tmp`, the local copy always goes to
  `/var/spool/pandora/data_in/`, and the Tentacle client is always the one in
  `PATH` without extra options.
- **Delivery failures are not reported in the output.** With Tentacle, a failed
  transfer writes the client error to standard error, deletes the generated
  document and still prints `1`. With the local copy, a failure prints the error
  and `0`.
- **The exit status does not describe the run.** `1` and `0` are printed on
  standard output and the process exits with status `0` in both cases. Only
  command-line errors (status `2`) and uncaught connection, authentication or
  parse failures (status `1` with a traceback) differ.
- **The Manager path is fixed.** The plugin always requests `/manager/...`;
  there is no custom URL setting.
- **HTTPS has no certificate override.** With `https=1` the certificate of the
  Tomcat connector must be trusted by the plugin host. There is no option to
  skip the verification, so a self-signed certificate stops the run.
- **Every JVM information module is `generic_data`.** Text values such as
  `vmname`, `vmversion` or `vmvendor` are sent as text inside a numeric module,
  so they cannot be read as a series.
- **JVM information names repeat.** The report has one block per garbage
  collector and per memory pool, and the plugin uses only the line label, so
  names such as `getcollectioncount`, `current_used` or `peak_max` appear once
  per collector or pool in the same document, with no way to tell them apart.
- **No application, session or worker modules.** This version reads the status
  and JVM information reports only. It does not query the application list, so
  it produces no per-application status or session modules, no `[workers]`
  totals and no threading usage percentage.

### Troubleshooting

- **A traceback ending in an invalid-URL error that mentions `No host
  supplied`** — `host` is empty. The `[CONF]` section or the `host` key is
  missing, or the configuration file path is wrong and the built-in defaults
  were used.
- **The plugin prints a parser message and `0`, and no module is generated** —
  the configuration file has no `[CONF]` header. Add the header.
- **A traceback ending in an XML parse error** — the Manager application
  answered with something that is not the status document. Check the
  credentials, the `user` and `password` keys, and that the Manager application
  is deployed. A rejected authentication produces an error page, not the
  document.
- **A traceback ending in a connection error** — Tomcat is not listening on
  `host:port`, the port is wrong, or `https` does not match the connector. Check
  the connector configuration of Tomcat.
- **A traceback ending in an SSL error** — `https=1` and the certificate is not
  trusted by the plugin host. Import the CA into the trust store of the host, or
  serve the Manager application over a trusted certificate.
- **The three memory modules carry `{'...'}` values** — expected in this
  version; see the limitations above. Use the connector and JVM information
  modules for memory analysis.
- **Fewer modules than expected** — `enable_status_monitoring` or
  `enable_vminfo_monitoring` is not exactly `1`, or `allow_regexp` and
  `deny_regexp` are filtering names out. Check both.
- **The thread and request modules cover a single connector** — expected; the
  plugin reads the first connector only.
- **The agent does not appear in the console after a run that printed `1`** —
  the delivery failed. Check the Tentacle client in `PATH`, `tentacle_ip` and
  `tentacle_port`, or that `transfer_mode=local` was really selected and
  `/var/spool/pandora/data_in/` is writable.

## Reference

### Configuration file

The file is passed with `--conf` and holds `key=value` lines inside a `CONF`
section. Values in the file override the built-in defaults shown below.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `host` | Yes | Empty | Host name or IP address of Tomcat, without scheme and without port |
| `port` | No | `8080` | Connector port that serves the Manager application; a non-numeric value is read as `0` |
| `user` | Yes | Empty | Tomcat user with the `manager-script` role |
| `password` | Yes | Empty | Password of `user`, stored in plain text |
| `https` | No | `0` | Only `1` queries `https://`; any other value queries `http://` |
| `enable_status_monitoring` | No | `1` | Only `1` collects the status document: memory, connector threads and connector requests |
| `enable_vminfo_monitoring` | No | `1` | Only `1` collects the JVM information report |
| `allow_regexp` | No | Empty | Regular expression; only metric names that contain a match are published. Does not apply to the memory modules |
| `deny_regexp` | No | Empty | Regular expression; metric names that contain a match are dropped. Same scope as `allow_regexp` |
| `agent_name` | No | `Tomcat` | Alias of the generated agent; the stored agent name is a 32-character hash of this value |
| `agents_group_name` | No | `tomcat` | Group of the generated agent, by name |
| `interval` | No | `300` | Agent interval in seconds; a non-numeric value is read as `0` |
| `module_prefix` | No | Empty | Text prepended to every module name, with no separator |
| `transfer_mode` | No | `tentacle` | Only `local` copies the document into `/var/spool/pandora/data_in/`; any other value delivers with Tentacle |
| `tentacle_ip` | No | `127.0.0.1` | Tentacle server address; used unless `transfer_mode=local` |
| `tentacle_port` | No | `41121` | Tentacle server port |
| `temporal` | No | — | Accepted and ignored; the document is always written to `/tmp` |
| `data_dir` | No | — | Accepted and ignored; the local copy always goes to `/var/spool/pandora/data_in/` |
| `tentacle_client` | No | — | Accepted and ignored; the client is always `tentacle_client` from `PATH` |
| `tentacle_opts` | No | — | Accepted and ignored; no extra Tentacle options are passed |

### Command-line execution

```bash
./pandora_tomcat --conf <PATH_TO_CONFIG>
```

| Condition | Behavior |
| --- | --- |
| No argument, or `--conf` without a value | The usage summary on standard error and exit status `2` |
| `-h` or `--help` | The usage summary and exit status `0` |
| `--conf` names a readable file with a `[CONF]` section | The run uses that configuration |
| `--conf` names a file that does not exist | The file is ignored, the defaults apply and the run stops with an invalid-URL error, exit status `1` |
| The file has no `[CONF]` section | The parser message and `0` on standard output, exit status `0` |
| The run reaches the end | `1`, or `0` after an error it handled, and exit status `0` |
| The Manager request fails or its answer cannot be parsed | A traceback on standard error and exit status `1` |
| `SIGTERM` is received | `Received SIGTERM signal. Cleaning up...` and exit status `0` |

### Generated modules

Every module is declared as `generic_data`, carries no unit and receives the
`module_prefix` value in front of its name. The descriptions the plugin writes
are `Metrics type: JVM` for the memory modules, `Metrics type: THREADS` for the
thread modules, `Metrics type: REQUESTS` for the request modules and
`Metrics type: VMINFO` for the JVM information modules.

#### JVM memory modules

| Module | When | Meaning |
| --- | --- | --- |
| `memory_free` | `enable_status_monitoring=1` | Free memory reported by the JVM, in bytes, wrapped as `{'<number>'}` |
| `memory_total` | `enable_status_monitoring=1` | Total memory reported by the JVM, in bytes, wrapped as `{'<number>'}` |
| `memory_max` | `enable_status_monitoring=1` | Maximum memory reported by the JVM, in bytes, wrapped as `{'<number>'}` |

#### Connector modules

One module per attribute, named after the attribute alone, from the first
`<threadInfo>` and the first `<requestInfo>` of the status document:

| Module | Source | Meaning |
| --- | --- | --- |
| `maxThreads` | `threadInfo` | Maximum threads of the connector |
| `currentThreadCount` | `threadInfo` | Threads in the connector pool |
| `currentThreadsBusy` | `threadInfo` | Threads serving a request |
| `maxTime` | `requestInfo` | Longest request processing time |
| `processingTime` | `requestInfo` | Total request processing time |
| `requestCount` | `requestInfo` | Requests handled |
| `errorCount` | `requestInfo` | Requests that ended in an error |
| `bytesReceived` | `requestInfo` | Bytes received by the connector |
| `bytesSent` | `requestInfo` | Bytes sent by the connector |

The list is the set of attributes a current Tomcat publishes in the status
document; an attribute the connector does not publish produces no module.

#### JVM information modules

The report is filtered before it becomes modules: lines without a value, keys
that start with `org.`, `java.`, `sun.`, `user.`, `package.`, `tomcat.`,
`catalina.`, `awt.` or `jdk.`, keys that contain `classpath`, `librarypath`,
`loader`, `path`, `separator`, `vendor.url`, `level=` or `parent=`, and keys
that contain none of `vm`, `heap`, `non-heap`,
`current`, `peak`, `collection`, `uptime`, `processor`, `load`, `thread`,
`compilation`, `gc` or `memory` are dropped. The module name is the remaining
label, lowercased, with spaces replaced by underscores.

For a current Tomcat the surviving modules are:

| Group | Modules | Meaning |
| --- | --- | --- |
| Runtime | `vmname`, `vmversion`, `vmvendor`, `uptime` | JVM name, version and vendor; JVM uptime in milliseconds |
| Operating system | `availableprocessors`, `systemloadaverage` | Processors available to the JVM and system load average |
| Threads | `iscurrentthreadcputimesupported`, `isthreadcputimesupported`, `isthreadcputimeenabled`, `isthreadcontentionmonitoringsupported`, `isthreadcontentionmonitoringenabled`, `peak` | JVM capability flags and peak thread count |
| Class loading | `totalloaded` | Classes loaded since the JVM started |
| Compilation | `totalcompilationtime`, `iscompilationtimemonitoringsupported` | Just-in-time compilation time and its support flag |
| Garbage collectors | `getcollectioncount`, `getcollectiontime` | Collections and collection time, once per collector under the same name |
| Heap and non-heap | `heap_init`, `heap_used`, `heap_committed`, `heap_max`, `non-heap_init`, `non-heap_used`, `non-heap_committed`, `non-heap_max` | Heap and non-heap memory usage, in bytes |
| Memory pools | `current_init`, `current_used`, `current_committed`, `current_max`, `collection_init`, `collection_used`, `collection_committed`, `collection_max`, `peak_init`, `peak_used`, `peak_committed`, `peak_max`, `getcollectionusagethreshold`, `getcollectionusagethresholdcount` | Usage thresholds and usage of each memory pool, once per pool under the same name |

The exact module set depends on the garbage collectors and memory pools of the
JVM, so a different JVM can add or remove names.

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.tomcat` |
| Name | Tomcat monitoring plugin |
| Version | `1.0` |
| Category | Miscelaneus |
| License | One |
| Marketplace last update | 2026-05-25 |
| Availability | Download limited to licensed users |
| Executable | `pandora_tomcat` |
