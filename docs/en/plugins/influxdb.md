# Pandora InfluxDB

*Article last updated: 2026-10-26.*

## What it does

The Pandora InfluxDB plugin collects the internal statistics of an InfluxDB
instance and publishes them as Pandora FMS modules. Each run connects to the
InfluxDB HTTP API, executes the InfluxQL statement `SHOW STATS` once, and turns
the `runtime`, `queryExecutor`, `httpd`, `write`, `subscriber` and `cq`
sections of the response into modules. Nothing is installed on the InfluxDB
server, and the plugin keeps no state between runs: every execution reports the
counters of that moment.

The plugin supports two execution models:

- **Server plugin mode** (default): each run builds an agent document and writes
  it into the Pandora FMS data directory, where the server ingests it. The
  statistics are split into five agents named after the InfluxDB section they
  come from.
- **Agent plugin mode** (requires `--as_agent_plugin 1`): each run prints the
  modules as XML on standard output, and the Pandora FMS agent that runs the
  plugin stores them under its own agent.

All generated modules are of type `generic_data`.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.influxdb`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG `784` and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions. It is a general compatibility statement covering the plugin, not a test record for it |
| An InfluxDB endpoint that accepts a user and a password and answers `SHOW STATS` | `Required` | The plugin exposes `--user` and `--password` and executes that statement; it has no token authentication option |
| InfluxDB server versions | `Not validated` | No InfluxDB version matrix has been recorded for this addon |
| Operating system of the host that runs the plugin | `Not validated` | No operating system has been recorded for this version |
| Network access from that host to the InfluxDB HTTP API | `Required` | The plugin connects to the host and port you configure |

### Requirements

1. **An InfluxDB instance reachable over TCP** from the host that will run the
   plugin, with its HTTP API listening on the configured port (`8086` by
   default), and able to answer `SHOW STATS`.
2. **Credentials for that instance** when it requires authentication: a user
   and a password. The plugin authenticates only when both are supplied.
3. **Pandora FMS**:
    - In server plugin mode, the Pandora FMS plugin server to run the
      registered plugin, and a data directory processed by the data server.
    - In agent plugin mode, an agent that runs the plugin and ingests its
      output.
4. **The addon package installed in Pandora FMS** through the console.

### Install the addon

Download the package from the Pandora FMS Marketplace entry, which is limited
to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.influxdb](https://marketplace.pandorafms.com/entries/pandorafms.influxdb)

Load it into Pandora FMS. Once loaded, the plugin is registered with its
parameters and becomes available in the plugin list.

<!-- SCREENSHOT NEEDED: Pandora FMS console plugin list after loading the pandorafms.influxdb package, showing the registered Pandora InfluxDB plugin. -->

The contents of the distributed package could not be inspected for this page,
so no build or dependency-installation procedure is prescribed here. Use the
executable that the package installs and that the plugin definition shows.

## Configure

The plugin has no configuration file: every setting is a command-line option,
documented in [Command-line parameters](#command-line-parameters). Choose the
execution model first; the connection options are the same in both.

### Server plugin mode

Server plugin mode is the default: it applies unless `--as_agent_plugin` is
`1`. Each run writes one agent document per statistics section into
`--data_dir`:

```text
--host <INFLUXDB_URL> --port 8086 --user <USERNAME> --password <PASSWORD> --group <GROUP_ID> --data_dir /var/spool/pandora/data_in
```

- **`--host`** takes the host name or IP address of the InfluxDB instance,
  without the scheme and without the port. Pass the port in `--port`.
- **`--group`** sets the Pandora FMS group written into the five generated
  agent documents. Its default value is the literal `genieacs`, which is not a
  group identifier, so pass the numeric ID of an existing group. Without it,
  the generated documents carry that literal value in their group field.
- **`--data_dir`** defaults to `/var/spool/pandora/data_in/`, the data
  directory of a Pandora FMS server. It must exist and be writable by the user
  that runs the plugin.
- The five agents are named `InfluxDB_Runtime`, `InfluxDB_queryExecutor`,
  `InfluxDB_Httpd`, `InfluxDB_Write` and `InfluxDB_Subscriber_cq`. The plugin
  offers no option to rename them or to change their interval.

### Agent plugin mode

Agent plugin mode requires `--as_agent_plugin 1`. The run prints the modules as
XML on standard output instead of writing agent documents:

```text
--host <INFLUXDB_URL> --port 8086 --user <USERNAME> --password <PASSWORD> --as_agent_plugin 1
```

In this mode `--group` and `--data_dir` are ignored: the modules are stored
under the agent that runs the plugin, not under the five section agents.

### Credentials and transport

- Authentication is enabled only when both `--user` and `--password` are set.
  With only one of them the plugin connects without credentials, and an
  instance that requires authentication rejects the request.
- The plugin talks to the InfluxDB HTTP API without TLS: it exposes no option
  to enable it or to verify a certificate. The credentials and the statistics
  travel unencrypted, so keep the API on a trusted network segment or protect
  the path with a tunnel.
- The password is passed as a command-line option. It can appear in the shell
  history of a manual run and in the process list while the plugin executes,
  including runs started by Pandora FMS. Restrict access to the host that runs
  the plugin and rotate the credential if it is exposed.

### Register the plugin in the console

1. Install the package (see [Install the addon](#install-the-addon)).
2. Create a plugin module in an agent and select **Pandora InfluxDB**.
3. Fill the host, port and credential parameters the package exposes, and keep
   `8086` when the HTTP API listens on its default port.
4. In server plugin mode, also set the group and the data directory when they
   differ from the defaults.

<!-- SCREENSHOT NEEDED: Plugin module form for Pandora InfluxDB with host, port, user and a masked password, using lab values. -->

In server plugin mode the module only triggers the run: the statistics appear in
the five `InfluxDB_*` agents, not in the agent that owns the module. In agent
plugin mode the modules appear under the agent that executes the plugin.

## Verify

Run the installed plugin executable on the host that will execute it, in server
plugin mode and with a test data directory, so the output can be inspected
without feeding the Pandora FMS server:

```bash
<PLUGIN_EXECUTABLE> --host <INFLUXDB_URL> --port 8086 --user <USERNAME> --password <PASSWORD> --group <GROUP_ID> --data_dir /tmp/influxdb-check
```

Create the directory first: the plugin does not create it, and a failed write is
silent. A successful run prints `1` as its last line and writes one agent
document per statistics section:

```text
InfluxDB_Runtime.<EPOCH>.data
InfluxDB_queryExecutor.<EPOCH>.data
InfluxDB_Httpd.<EPOCH>.data
InfluxDB_Write.<EPOCH>.data
InfluxDB_Subscriber_cq.<EPOCH>.data
```

`<EPOCH>` is the time of the run in seconds. Each file is an agent document
with its modules:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<agent_data agent_name='InfluxDB_Runtime' agent_alias='InfluxDB_Runtime' parent_agent_name='' description='InfluxDB_Runtime' version='' os_name='' os_version='' timestamp='2026/10/26 10:00:00' address='127.0.0.1' group='10' interval=''>
<module>
	<name><![CDATA[Alloc]]></name>
	<type>generic_data</type>
	<data><![CDATA[4194304]]></data>
</module>
<module>
	<name><![CDATA[Frees]]></name>
	<type>generic_data</type>
	<data><![CDATA[1024]]></data>
</module>
</agent_data>
```

This is an excerpt with illustrative values; the real counters depend on the
instance. In agent plugin mode the same connection prints `<module>` blocks on
standard output, with no `<agent_data>` envelope:

```bash
<PLUGIN_EXECUTABLE> --host <INFLUXDB_URL> --port 8086 --user <USERNAME> --password <PASSWORD> --as_agent_plugin 1
```

```xml
<module>
	<name><![CDATA[Alloc]]></name>
	<type>generic_data</type>
	<data><![CDATA[4194304]]></data>
</module>
```

The final `1` is printed after the module blocks. `--help` prints the option
list and exits without collecting anything.

<!-- SCREENSHOT NEEDED: The five InfluxDB_* agents and their modules in the Pandora FMS console after a successful server plugin run. -->

## Understand the results

### Agents generated

In server plugin mode the plugin writes five agents, one per group of
statistics:

| Agent | Statistics section | Modules |
|-------|--------------------|---------|
| `InfluxDB_Runtime` | `runtime` | 15 |
| `InfluxDB_queryExecutor` | `queryExecutor` | 5 |
| `InfluxDB_Httpd` | `httpd` | 24 |
| `InfluxDB_Write` | `write` | 9 |
| `InfluxDB_Subscriber_cq` | `subscriber` and `cq` | 5 |

| Agent property | Value |
|----------------|-------|
| Name, alias and description | The fixed section name, for example `InfluxDB_Runtime` |
| Address | `127.0.0.1` |
| Group | The value of `--group` |
| Interval | Not set by the plugin |
| Module type | `generic_data` for every module |

### How to read the modules

The plugin publishes the counters exactly as `SHOW STATS` returns them. It does
not compute rates, deltas or thresholds.

- `runtime` reports memory allocation and runtime counters of the InfluxDB
  process.
- `queryExecutor` counts the query workload.
- `httpd` counts the requests handled by the HTTP API, including Flux,
  Prometheus and write requests.
- `write` counts the write path.
- `subscriber` counts subscriber writes, and `cq` counts continuous-query
  executions.

Fields whose name ends in `Ns` are nanoseconds and fields whose name ends in
`Bytes` are bytes. The `*Req` fields are request counts.

In agent plugin mode the section grouping is lost: every module is stored under
the agent that runs the plugin, and the five section agents are not created.
Two module names then describe two different sections, because `req` appears in
`httpd` and in `write`, and `recoveredPanics` in `queryExecutor` and in
`httpd`. In server plugin mode the `subscriber` and `cq` counters are delivered
together in a single `InfluxDB_Subscriber_cq` document.

A statistics section that returns more than one row produces the same module
names once per row.

## Operate and troubleshoot

### Operation

- The plugin is a single collection run: it queries InfluxDB, delivers the
  result and exits. It keeps no state and can be executed manually at any time.
- Schedule it from Pandora FMS (server plugin schedule) or with `cron`. There is
  no interval option: the generated agent documents carry no interval, so the
  execution frequency is the one you configure in the scheduler.
- The agent document of each section is written as
  `<agent_name>.<EPOCH>.data`. An existing file is not overwritten and the write
  is skipped without an error, so do not run the same configuration more than
  once per second.
- Use a dedicated `--data_dir` while testing, as shown in [Verify](#verify),
  to inspect the documents before they reach the Pandora FMS server.

### Troubleshooting

- **The plugin prints its usage summary and exits with status 2** — `--host`
  is missing. It is the only mandatory option.
- **The run stops with an error from the InfluxDB client and a non-zero exit
  status** — the request failed. Check that `--host` has no scheme or port,
  that `--port` matches the HTTP API, that both `--user` and `--password` are
  set when the instance requires authentication, and that the instance answers
  `SHOW STATS`.
- **Authentication fails although a user is configured** — only one of
  `--user` and `--password` was supplied, so the plugin connected without
  credentials. Set both.
- **The run fails with a value error on `--as_agent_plugin`** — the option
  expects an integer. Use `1` for agent plugin mode and `0`, or nothing, for
  server plugin mode.
- **The run prints `1` but no agent appears in Pandora FMS** — in server mode
  the documents were written to a directory that the server does not process,
  or the directory does not exist. Check `--data_dir` and its permissions.
- **No module XML is printed in agent plugin mode** — the agent must ingest the
  output of the plugin execution. Check that the plugin runs under the agent
  and that the output starts with the `<module>` blocks.
- **A section is missing from the output** — the run stops when the `SHOW STATS`
  response does not contain a section the plugin expects, so the sections after
  it are not published. Compare the output with a direct `SHOW STATS` query on
  the instance.
- **Repeated module names** — the section returned several rows. See
  [How to read the modules](#how-to-read-the-modules).

## Reference

### Command-line parameters

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `--host` | Yes | — | InfluxDB host name or IP address. Do not include the scheme or the port |
| `--port` | No | `8086` | TCP port of the InfluxDB HTTP API |
| `--user` | No | — | User for InfluxDB authentication. Used only together with `--password` |
| `--password` | No | — | Password for `--user`. Used only together with `--user` |
| `--as_agent_plugin` | No | `0` | `1` prints the modules as XML on standard output. Any other integer keeps server plugin mode. A non-numeric value stops the run with an error |
| `-g`, `--group` | No | `genieacs` | Server mode only. Pandora FMS group written into the generated agent documents. The default is not a numeric group ID; set an existing group ID |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Server mode only. Directory where the agent documents are written. It must exist and be writable by the user that runs the plugin |

### Command-line execution

```text
<PLUGIN_EXECUTABLE> [--host <HOST>] [--port <PORT>] [--user <USER>] [--password <PASSWORD>] [-g <GROUP>] [--data_dir <DIR>] [--as_agent_plugin <0|1>]
```

| Condition | Behavior |
|-----------|----------|
| `--host` is missing | The plugin prints the usage summary on standard error and exits with status 2 |
| `--help` | The plugin prints the usage summary and exits with status 0 |
| Only one of `--user` and `--password` is set | The plugin connects without authentication |
| `--as_agent_plugin` has a non-numeric value | The run stops with an error |
| The InfluxDB request fails | The run stops with an error and the remaining sections are not published |
| Server mode, target file already exists | The write is skipped without an error |
| `--group` or `--data_dir` in agent plugin mode | Ignored |

### Generated agents

| Agent | Statistics section | Description |
|-------|--------------------|-------------|
| `InfluxDB_Runtime` | `runtime` | Memory allocation and runtime counters |
| `InfluxDB_queryExecutor` | `queryExecutor` | Query workload counters |
| `InfluxDB_Httpd` | `httpd` | HTTP API request counters |
| `InfluxDB_Write` | `write` | Write path counters |
| `InfluxDB_Subscriber_cq` | `subscriber`, `cq` | Subscriber and continuous-query counters |

### Generated modules

Every module is of type `generic_data`.

#### InfluxDB_Runtime

`runtime` section, 15 modules:

| Module |
|--------|
| `Alloc` |
| `Frees` |
| `HeapAlloc` |
| `HeapIdle` |
| `HeapInUse` |
| `HeapObjects` |
| `HeapReleased` |
| `HeapSys` |
| `Lookups` |
| `Mallocs` |
| `NumGC` |
| `NumGoroutine` |
| `PauseTotalNs` |
| `Sys` |
| `TotalAlloc` |

#### InfluxDB_queryExecutor

`queryExecutor` section, 5 modules:

| Module |
|--------|
| `queriesActive` |
| `queriesExecuted` |
| `queriesFinished` |
| `queryDurationNs` |
| `recoveredPanics` |

#### InfluxDB_Httpd

`httpd` section, 24 modules:

| Module |
|--------|
| `authFail` |
| `clientError` |
| `fluxQueryReq` |
| `fluxQueryReqDurationNs` |
| `pingReq` |
| `pointsWrittenDropped` |
| `pointsWrittenFail` |
| `pointsWrittenOK` |
| `promReadReq` |
| `promWriteReq` |
| `queryReq` |
| `queryReqDurationNs` |
| `queryRespBytes` |
| `recoveredPanics` |
| `req` |
| `reqActive` |
| `reqDurationNs` |
| `serverError` |
| `statusReq` |
| `valuesWrittenOK` |
| `writeReq` |
| `writeReqActive` |
| `writeReqBytes` |
| `writeReqDurationNs` |

#### InfluxDB_Write

`write` section, 9 modules:

| Module |
|--------|
| `pointReq` |
| `pointReqLocal` |
| `req` |
| `subWriteDrop` |
| `subWriteOk` |
| `writeDrop` |
| `writeError` |
| `writeOk` |
| `writeTimeout` |

#### InfluxDB_Subscriber_cq

`subscriber` and `cq` sections, 5 modules:

| Module |
|--------|
| `createFailures` |
| `pointsWritten` |
| `writeFailures` |
| `queryFail` |
| `queryOk` |

### Addon identity

| Property | Value |
|----------|-------|
| Marketplace identifier | `pandorafms.influxdb` |
| Name | Pandora InfluxDB |
| Version | `1.0` |
| Package | `pandorafms.influxdb.1.0.pspz2` |
| Marketplace last update | 2025-06-26 |
| Author | Pandora FMS |
| Availability | Download limited to licensed users |
| License | `One` |
