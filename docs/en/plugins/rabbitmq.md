# RabbitMQ monitoring plugin

*Article last updated: 2026-10-29.*

!!! warning "Discovery integration recommended"
    For new installations use [RabbitMQ Discovery](../discovery/rabbitmq-discovery.md), which is the recommended integration for this service. This plugin is the legacy path.

## What it does

The RabbitMQ monitoring plugin turns the state of a RabbitMQ broker or cluster
into Pandora FMS modules. Each run queries the RabbitMQ management HTTP API and
builds one module set: cluster totals and message rates, memory and process
usage per node, the status of each node, exchange publish rates, connection
counters and an availability check.

Nothing is installed on the RabbitMQ nodes. The plugin runs on the host you
choose and reads the broker over HTTP with a single credential pair.

The plugin supports two execution models:

- **Server plugin mode** (default when `as_agent_plugin` is absent or disabled):
  each run builds an agent document and delivers it to Pandora FMS through
  Tentacle or a local data folder.
- **Agent plugin mode** (requires `as_agent_plugin=1`): each run prints the
  generated modules as XML on standard output, for the Pandora FMS agent to
  ingest.

This page documents the Marketplace addon `pandorafms.rabbitmq`. The RabbitMQ
Local plugin that ships with the Pandora FMS agent is a **different addon**:
it reads the same API but has its own configuration keys and generates its own
module set. It is documented in
[RabbitMQ Local monitoring plugin](rabbitmq-local.md); do not mix the two
configurations.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.rabbitmq`, version `1.1` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| A RabbitMQ broker with the management plugin enabled | `Required` | The plugin reads `/api/overview`, `/api/nodes`, `/api/exchanges` and `/api/connections`, which the management plugin provides |
| HTTP access from the host that runs the plugin to the management listener (TCP, `15672` by default in RabbitMQ) | `Required` | The plugin sends every request to the base URL in `host` |
| A RabbitMQ user allowed to read node and connection data | `Required` | One HTTP Basic credential pair, `user` and `pass`; RabbitMQ's own documentation states that the `monitoring` tag grants node-level data and other users' connections |
| `tentacle_client` on the host that runs the plugin | `Required` when `transfer_mode=tentacle` | Server plugin delivery |
| RabbitMQ broker versions | `Not validated` | No version matrix has been recorded. The legacy guide only states that the plugin was developed against RabbitMQ `3.7.18`; the plugin itself asks nothing beyond an API that answers the four documented endpoints |
| Operating system of the host that runs the plugin | `Not validated` | No operating system has been recorded for this version |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions; it is a catalogue-wide statement covering this addon, not a test record for it |
| TLS to the management API | `Not validated` | The addon has no TLS, proxy or CA option: the base URL is used as given |

### Prerequisites

1. **The RabbitMQ management plugin enabled** on at least one node. It is
   included in the RabbitMQ distribution and is enabled with
   `rabbitmq-plugins enable rabbitmq_management`; no restart is needed. Any node
   with the plugin enabled answers for the whole cluster, so one address is
   enough even in a multi-node deployment.
2. **Network access** from the host that runs the plugin to that listener. The
   management UI and API use port `15672` by default, and `15671` when RabbitMQ
   serves them over TLS.
3. **A RabbitMQ user that can query the four endpoints.** The plugin
   authenticates with HTTP Basic, so it needs a user name and a password. The
   `monitoring` tag is what RabbitMQ documents for node-level data and other
   users' connections; a monitoring-only user is created with that tag and with
   empty resource permissions.
4. **Pandora FMS** to receive the output: the Pandora FMS server in server
   plugin mode, or the Pandora FMS agent of the monitored host in agent plugin
   mode.
5. **The Tentacle client (`tentacle_client`) available in `PATH`**, only when
   server plugin mode delivers through Tentacle.

The shipped example configuration uses the RabbitMQ `guest` account. In a
standard RabbitMQ installation `guest` can only connect from `localhost`, so
replace it with the dedicated monitoring user.

### Install the addon

Download the package from the Marketplace entry (the download is limited to
licensed users):

[https://marketplace.pandorafms.com/entries/pandorafms.rabbitmq](https://marketplace.pandorafms.com/entries/pandorafms.rabbitmq)

Copy the `rabbitmq_monitor` executable to the host that will run it — for
example `/usr/share/pandora_server/util/plugin/rabbitmq_monitor` when it runs on
the Pandora FMS server — and place its configuration file next to it or in any
directory you can protect. The package also includes an example
`rabbitmq_monitor.conf`; edit a copy of it, because its values are examples.

Nothing is installed on the RabbitMQ nodes, and no RabbitMQ client tools are
needed on the monitoring host: all data comes from the management HTTP API.

## Configure

The plugin combines three sources, in increasing precedence:

```text
defaults < configuration file < command-line arguments
```

The configuration file is optional. When it is used it must be the **first
argument** of the command line; a path placed after a flag is not read as a
configuration file. It is a plain-text file with one `key=value` pair per line.
Blank lines and lines that start with `#` are skipped, keys and values are
trimmed, and the last occurrence of a repeated key wins. There are no sections:
a bracketed header is stored as an unused key.

The file name in the examples, `rabbitmq_monitor.conf`, is a convention, not a
requirement.

### Execution modes

Agent plugin mode is the shortest configuration: the Pandora FMS agent runs the
plugin and ingests the module XML it prints.

```ini
host=http://<TARGET_HOST>:15672
user=<USERNAME>
pass=<PASSWORD>
as_agent_plugin=1
```

Server plugin mode needs an agent name and a delivery target. With Tentacle:

```ini
host=http://<TARGET_HOST>:15672
user=<USERNAME>
pass=<PASSWORD>
agent_name=RabbitMQ
interval=300
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_URL>
tentacle_port=41121
```

Or copy the agent document into a local data folder instead of using Tentacle:

```ini
host=http://<TARGET_HOST>:15672
user=<USERNAME>
pass=<PASSWORD>
agent_name=RabbitMQ
interval=300
transfer_mode=local
local_folder=/var/spool/pandora/data_in
```

The same agent plugin run with arguments only, without a configuration file:

```bash
./rabbitmq_monitor -host http://<TARGET_HOST>:15672 -user <USERNAME> -pass <PASSWORD> -as_agent_plugin 1
```

Key points:

- **`host` is the base URL of the management API**, including the scheme and
  the port: `http://<TARGET_HOST>:15672`. The plugin appends the `/api/...`
  paths to this value, so a bare `host:port` is not a complete request URL. The
  shipped example (`host=192.168.80.20:8080`) is a placeholder with a non-default
  port; replace it.
- **`user` and `pass` are sent as HTTP Basic credentials on every request.** They
  must belong to a user that can read the endpoints listed in
  [Prerequisites](#prerequisites). There is no token, certificate or
  alternative authentication surface.
- **`as_agent_plugin` selects the model.** `1` (or any numeric value greater
  than `0`) prints module XML on standard output; `0`, an empty value or a
  non-numeric value keeps server plugin mode. `as_server_plugin=0` also selects
  agent plugin mode when `as_agent_plugin` is absent, and `as_agent_plugin` wins
  when both keys are present.
- **`agent_name` names the agent created in Pandora FMS**, and `interval` is its
  interval in seconds. Both are server plugin mode only.
- **`transfer_mode` selects the delivery.** `tentacle` (case-sensitive) runs the
  Tentacle client; any other value copies the agent document into
  `local_folder`.
- **`module_group` names the module group assigned to every generated module.**
  `module_interval` and `module_tag_list` set the module interval and the module
  tags in the same way. When they are absent the modules carry no group, no own
  interval and no tags.
- **One agent per broker.** Module names carry no broker prefix, so two brokers
  delivered to the same agent overwrite each other's modules. Use a different
  `agent_name` per broker, or one agent plugin installation per broker.

In agent plugin mode the executable is declared as a plugin of the Pandora FMS
agent — in the agent configuration file or through remote configuration — with
the configuration file as the first argument of the plugin command and
`as_agent_plugin=1` inside that file. The agent runs the plugin, reads the module
XML from standard output and reports the modules in its own agent, so
`agent_name`, `interval` and the transfer keys are not used in this mode.

### Credentials and transport

- The plugin has no TLS options of its own: it requests the base URL you give
  it. With an `http://` base URL the credentials and the collected metrics
  travel unencrypted, so keep the management listener on a trusted network or
  serve it through a TLS terminator. RabbitMQ serves the management API over
  HTTPS on port `15671` when it is configured for TLS; an `https://` base URL
  depends on the TLS support available to the executable and is not validated
  here.
- There is no CA bundle, proxy or certificate-verification key. A private or
  self-signed certificate therefore has no supported configuration path in this
  addon.
- `pass` is stored in the configuration file in plain text: restrict the file
  permissions to the user that runs the plugin (for example `chmod 600`).
- Avoid `-pass` on the command line: the command is stored in the shell history
  and the operating system process list can expose it while the plugin runs. A
  scheduled server plugin keeps its parameters in the Pandora FMS database, so
  treat the module definition as sensitive as well.

### Register the plugin in Pandora FMS

`rabbitmq_monitor` can also be registered in the Pandora FMS console as a
standard server plugin, so Pandora FMS executes it on the server that runs the
modules instead of in a command line. Registered this way the plugin keeps
server plugin mode: every run builds the agent document and delivers it, and the
agent with its modules appears in the console.

1. Open **Servers → Plugins** and click **Register Plugin**.
2. Set the name, the plugin type **Standard**, an optional maximum timeout and a
   description.
3. In **Plugin command**, enter the absolute path to `rabbitmq_monitor` on the
   Pandora FMS server, for example
   `/usr/share/pandora_server/util/plugin/rabbitmq_monitor`.
4. In **Plugin parameters**, pass the documented keys and use the plugin
   macros `_field1_`, `_field2_`, ... as placeholders. For one broker in server
   plugin mode with Tentacle:

    ```text
    -host _field1_ -user _field2_ -pass _field3_ -agent_name _field4_ -transfer_mode tentacle -tentacle_ip 127.0.0.1 -tentacle_port 41121
    ```

5. In **Macro parameters**, describe each field. The example uses these values:

    | Field | Description | Example value |
    | --- | --- | --- |
    | `_field1_` | Management API base URL, including scheme and port | `http://<TARGET_HOST>:15672` |
    | `_field2_` | RabbitMQ user allowed to read the management API | `<USERNAME>` |
    | `_field3_` | Password for that user; mark **Hide value** | — |
    | `_field4_` | Name of the agent that will hold the modules | `RabbitMQ` |

`-tentacle_ip 127.0.0.1` delivers to the Tentacle server of the machine that
runs the plugin, so the agent lands in the Pandora FMS server that executes the
module. To copy the document into a local data folder instead, replace the
Tentacle parameters with `-transfer_mode local -local_folder /var/spool/pandora/data_in`.

<!-- SCREENSHOT NEEDED: Pandora FMS console plugin registration form for server plugins, showing the rabbitmq_monitor plugin command and its parameter and macro fields. -->

Once registered, the plugin is available when creating plugin modules, and each
module fills the fields individually. The module is executed on the server
selected for it, including a remote Pandora FMS server, so each broker is
monitored from the Pandora FMS server closest to it without installing anything
on the broker host.

## Verify

Run the plugin manually from a terminal, passing the configuration file as its
first argument:

```bash
./rabbitmq_monitor /etc/pandora/plugins/rabbitmq_monitor.conf
```

The relative form `./rabbitmq_monitor rabbitmq_monitor.conf` works when the
terminal is already in the directory that contains both files. Each run executes
once and exits.

An empty command line prints the usage summary:

```text
- Syntax:

./rabbitmq_monitor <plugin_configuration_file_path>
```

There is no help flag: `-h` and `--help` are treated like any other argument.

In agent plugin mode, a successful run prints one XML `<module>` block per
generated module on standard output. This is an excerpt of the document built
for a single-node cluster:

```xml
<module>
	<name><![CDATA[Cluster name]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[rabbit@node01]]></data>
</module>
<module>
	<name><![CDATA[Availability]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[Rabbit MQ API availability]]></description>
</module>
<module>
	<name><![CDATA[Memory used - rabbit@node01]]></name>
	<type>generic_data</type>
	<data><![CDATA[174895104]]></data>
	<description><![CDATA[Usually in bytes. Represents the total memory that the RabbitMQ node is using at that instant.]]></description>
</module>
```

`Availability` is `1` only when the overview request succeeds; a `0` there means
the overview request did not return HTTP 200 (see
[Operate and troubleshoot](#operate-and-troubleshoot)).

In server plugin mode a run prints `1` and exits. That `1` is printed after the
delivery attempt, **not** as its result: a failed Tentacle transfer or a failed
local copy also prints `1`. Confirm the agent and its modules in the console.

<!-- SCREENSHOT NEEDED: Pandora FMS agent view listing the modules generated by the rabbitmq_monitor plugin for one broker. -->

## Understand the results

The module catalog is fixed. A run emits eight modules on every execution, adds
six when the overview request succeeds and adds five per node when the nodes
request succeeds. A single-node cluster with a healthy API therefore produces
19 modules.

- **Availability and connection counters (always).** `Availability`, `Total
  connections`, `Connections running`, `Connections blocked`, `Total received
  octets`, `Total sent octets`, `Exchanges in rate` and `Exchanges out rate` are
  generated on every run, even when no request succeeds.
- **Cluster totals (overview request).** `Cluster name`, `Total queue
  messages`, `Messages unacknowledged`, `Total exchanges`, `Queue publish
  rate`, `Queue deliver get rate` and `Queue deliver noack rate` are generated
  only when `/api/overview` answers with HTTP 200.
- **Per node (nodes request).** For every node the API returns, `Memory used -
  <node>`, `Memory rate`, `Proc used - <node>`, `Proc details` and `Node status
  - <node>` are generated. When the nodes request fails, none of these modules
  is generated, and the rest of the run is unaffected.

How the values are read:

- **Rates are per-second rates** taken from the `rate` fields the management
  API computes over its own sampling interval. `Memory rate` and `Proc details`
  are the memory and process rates of a node; `Exchanges in rate` and
  `Exchanges out rate` are publish rates of **one** exchange, not cluster
  totals: the plugin walks the exchange list and keeps the last exchange that
  reports a non-zero rate. When no exchange reports one, both modules report
  `0`.
- **`Connections blocked` is every connection whose state is not exactly
  `running`.** It is not a count of connections in RabbitMQ's `blocked` state.
- **`Total received octets` and `Total sent octets`** are the sum of the
  per-connection receive and send octet rates, so they are throughput in
  octets per second, not accumulated totals.
- **`Memory rate` and `Proc details` carry no node name**, unlike the other
  three per-node modules. In a cluster with more than one node each node adds
  its own module with the same name, so these two series cannot be attributed to
  a node. Use them only on single-node clusters where the name is unambiguous.
- **`Queue deliver get rate` does not report what its name says.** The module
  reads the publish rate when the get rate is present, so in practice it repeats
  `Queue publish rate` or reports `0`. Use `Queue publish rate` for publish
  activity and do not alert on `Queue deliver get rate`.

When the management API cannot be reached — wrong credentials, network problem,
management plugin disabled — every request fails: `Availability` reports `0`,
the six cluster modules and the five per-node modules are not generated, and the
seven remaining modules report `0`.

The agent document created in server plugin mode carries the name and alias from
`agent_name` and the interval from `interval`. Its address attribute is derived
from `host` by splitting on `:`; in this version it holds the number of
colon-separated parts (for example `3` for `http://<TARGET_HOST>:15672`), not the
broker address, so do not expect the agent address field to show the broker.

## Operate and troubleshoot

### Everyday operation

- The plugin keeps no state between runs: every execution reads the broker at
  that moment, so it can be run manually at any time.
- In server plugin mode, schedule it from Pandora FMS (the server plugin
  scheduler or `cron`) or from any external scheduler. In agent plugin mode, the
  Pandora FMS agent executes it according to the configured plugin schedule.
  `interval` only sets the interval of the agent created in the console; it does
  not schedule the plugin.
- **Use `debug=1` for diagnostics.** The addon writes its own messages to
  standard error only when `debug` is enabled: temporary-file write errors,
  Tentacle output and local-copy errors are silent without it. `debug` does not
  write to standard output, so it does not corrupt the module XML in agent
  plugin mode.
- The agent document is written to the folder in `tmp` (default `/tmp`) as
  `<agent_name>.<epoch>.data`, and the file is removed after a successful
  Tentacle or local delivery. A failed delivery leaves it in place: check that
  folder when deliveries fail repeatedly, and clear it once the cause is fixed.
- A run stopped with `SIGTERM` prints `Received SIGTERM, exiting...` and exits
  with status `0`, so a timeout looks like a successful run. Set a maximum
  timeout in the plugin definition only if you can verify the expected run time
  for your broker size.
- Create one agent per broker, with a distinct `agent_name`, and use
  `module_group` to separate these modules from others in the same agent.

### Troubleshooting

- **`Availability` reports `0`** — the overview request did not return HTTP
  200. Check that the management plugin is enabled, that `host` names the
  management listener of a node that answers for the cluster, and that user and
  password authenticate. A `401`/`403` from RabbitMQ, an unreachable host, a
  wrong port and a disabled plugin all produce the same result: the plugin reads
  only HTTP 200 responses and reports no error for the others.
- **No per-node modules appear** while `Availability` reports `1` — the nodes
  request failed. `monitoring` users see node-level data; a user without that
  tag is refused. The rest of the run still generates its modules.
- **All values are `0`** — the overview request failed while the later requests
  returned empty lists: this is the same cause as an `Availability` of `0`.
- **The agent never appears in the console in server plugin mode** — the
  delivery failed and the run still printed `1`. Re-run once with `debug=1` to
  see the reason, then check that `tentacle_client` is installed and in `PATH`,
  that `tentacle_ip:tentacle_port` is reachable, or that `local_folder` exists
  and is writable by the user that runs the plugin.
- **`ERROR: ...` lines** — the plugin prints its own configuration errors on
  standard output, before the usage summary, and still exits with status `0`.
  Read the output, not the exit status.
- **A required value is not reported** — the required-value checks run only when
  at least two arguments remain after the configuration file is consumed. With
  the documented single-file form (`./rabbitmq_monitor rabbitmq_monitor.conf`)
  they do not run: a missing `host`, `user`, `pass`, `agent_name`,
  `tentacle_ip` or `local_folder` is not reported, and the run proceeds with the
  values it has. Always run once with an explicit flag (`debug=1` works) after
  editing the file, or verify the first result in the console.
- **The modules never update and the broker is healthy** — check the execution
  schedule of the plugin in Pandora FMS and the interval of the agent, and run
  the plugin manually with `debug=1` to confirm that the management API answers
  from the host that executes it.
- **An `https://` base URL with a private certificate** — the addon has no CA or
  verification option, so a private or self-signed certificate has no supported
  path here. Monitor the plain HTTP listener from a trusted network, or
  terminate TLS in front of RabbitMQ with a certificate the host trusts.

## Reference

### Configuration file keys

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `host` | Yes | — | Base URL of the RabbitMQ management API, including scheme and port, for example `http://<TARGET_HOST>:15672`. The plugin appends `/api/overview`, `/api/nodes`, `/api/exchanges` and `/api/connections` to this value. |
| `user` | Yes | — | RabbitMQ user sent as HTTP Basic credentials. |
| `pass` | Yes | — | Password for `user`. |
| `agent_name` | Required in server plugin mode | — | Name and alias of the agent created in Pandora FMS. |
| `interval` | No | `300` | Server plugin mode only. Interval of the created agent, in seconds. |
| `as_agent_plugin` | No | `0` (server plugin mode) | `1` (or any numeric value greater than `0`) prints the module XML on standard output. `0`, empty or non-numeric keeps server plugin mode. |
| `as_server_plugin` | No | `1` | Accepted by the configuration reader. `0` selects agent plugin mode when `as_agent_plugin` is absent; `as_agent_plugin` takes precedence when both are present. |
| `transfer_mode` | Required in server plugin mode | Empty | `tentacle` delivers with the Tentacle client; any other value copies the document into `local_folder`. |
| `local_folder` | Required when `transfer_mode` is not `tentacle` | — | Destination folder for the agent document copy. |
| `tentacle_ip` | Required when `transfer_mode=tentacle` | — | Tentacle server address. |
| `tentacle_port` | No | `41121` | Tentacle server port. |
| `tentacle_client` | No | `tentacle_client` | Tentacle client executable, resolved in `PATH` or given as an absolute path. |
| `tentacle_opts` | No | Empty | Extra options passed to the Tentacle client, separated by whitespace. |
| `tmp` | No | `/tmp` | Folder where the agent document is written before delivery. |
| `module_group` | No | Empty (no group sent) | Module group assigned to every generated module. |
| `module_interval` | No | Empty (agent interval) | Module interval assigned to every generated module. |
| `module_tag_list` | No | Empty (no tags) | Module tags assigned to every generated module, passed through as given. |
| `debug` | No | `0` | `1` (or any numeric value greater than `0`) writes diagnostic messages, Tentacle output and delivery errors to standard error. |

Boolean keys are enabled by any numeric value greater than `0`; `0`, an empty
value or a non-numeric value means disabled. Unknown keys are accepted and
ignored: the plugin does not validate the key set.

### Command-line execution

```bash
./rabbitmq_monitor [config-file] [ -key value ... ]
```

| Condition | Behavior |
| --- | --- |
| The command line is empty | The plugin prints the usage summary and exits `0` |
| The first argument names an existing file | It is read as the configuration file and removed from the argument list |
| The first argument is not an existing file | It is not read as a configuration file; the run continues from the defaults plus the flags |
| `-key value` | Replaces the value of `key` |
| `--key value` or `-key=value` | Not recognized: only one leading hyphen is removed, so the pair is stored under a key the plugin ignores and the documented key keeps its file or default value |
| Arguments that do not form a `-key value` pair | Ignored; a trailing argument without a value is not reported |
| `-h` or `--help` | Not a help option; the flag is ignored and the run continues |
| Configuration error | Reported on standard output, followed by the usage summary, with exit status `0` |

The flags can appear before or after the configuration file path, but only a
file in the first position is read as the configuration file.

### Delivery behavior

| Situation | Result |
| --- | --- |
| `transfer_mode=tentacle` and the transfer succeeds | The temporary file is removed after the transfer |
| `transfer_mode=tentacle` and the transfer fails | Nothing is delivered; the client message is written to standard error only with `debug=1`, and the temporary file stays in `tmp` |
| Any other `transfer_mode` | The document is copied into `local_folder` and the temporary file is removed; a copy error is written to standard error only with `debug=1` |
| `transfer_mode` empty | Nothing is delivered; the reason is written to standard error only with `debug=1` |
| Delivery result as seen on standard output | A `1` is printed in every case |
| Exit status | `0` for configuration errors, failed delivery and `SIGTERM` |

### Generated modules

`<node>` is a node name reported by the broker.

| Module name | Type | Meaning | Generated when |
| --- | --- | --- | --- |
| `Cluster name` | `generic_data_string` | Cluster name reported by the broker | Overview request succeeds |
| `Total queue messages` | `generic_data` | Total messages in all queues | Overview request succeeds |
| `Messages unacknowledged` | `generic_data` | Messages delivered but not acknowledged | Overview request succeeds |
| `Total exchanges` | `generic_data` | Number of exchanges | Overview request succeeds |
| `Queue publish rate` | `generic_data` | Cluster publish rate | Overview request succeeds |
| `Queue deliver get rate` | `generic_data` | Reports the publish rate when a get rate is present (see [Understand the results](#understand-the-results)) | Overview request succeeds |
| `Queue deliver noack rate` | `generic_data` | Messages delivered to consumers without acknowledgement | Overview request succeeds |
| `Availability` | `generic_proc` | `1` when the overview request returns HTTP 200, `0` otherwise | Always |
| `Memory used - <node>` | `generic_data` | Memory used by the node, in bytes | Nodes request succeeds |
| `Memory rate` | `generic_data` | Rate at which the node memory is consumed or released | Nodes request succeeds |
| `Proc used - <node>` | `generic_data` | Erlang processes used by the node | Nodes request succeeds |
| `Proc details` | `generic_data` | Rate at which the node Erlang processes are created or terminated | Nodes request succeeds |
| `Node status - <node>` | `generic_proc` | `1` while the node is running, `0` otherwise | Nodes request succeeds |
| `Exchanges in rate` | `generic_data` | Publish-in rate of the last exchange that reports one; `0` when none reports activity | Always |
| `Exchanges out rate` | `generic_data` | Publish-out rate of the last exchange that reports one; `0` when none reports activity | Always |
| `Total connections` | `generic_data` | Number of connections returned by the API | Always |
| `Connections running` | `generic_data` | Connections whose state is exactly `running` | Always |
| `Connections blocked` | `generic_data` | Connections whose state is not `running` | Always |
| `Total received octets` | `generic_data` | Sum of the per-connection received-octet rates | Always |
| `Total sent octets` | `generic_data` | Sum of the per-connection sent-octet rates | Always |

Module names are created exactly as listed, without any broker or instance
prefix. The modules have no thresholds, no units and no alert templates: set
them in the console.

### Addon identity

| Field | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.rabbitmq` |
| Marketplace name | RabbitMQ monitoring plugin |
| Addon version | `1.1` |
| Marketplace last update | 2025-08-26 |
| Marketplace package | `pandorafms.rabbitmq.1.1.zip` |
| License | `One` (download limited to licensed users) |
| Marketplace type | Miscelaneus |
| Workflow | Monitoring plugin, agent or server plugin mode |
| Executable | `rabbitmq_monitor` |
