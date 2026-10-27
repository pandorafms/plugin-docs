# Kafka monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The Kafka monitoring plugin collects the performance metrics of a Kafka client
and publishes them as Pandora FMS modules. Each run creates a producer and a
consumer against one Kafka endpoint, takes a snapshot of the metrics both
clients report, and writes the result into a Pandora FMS agent.

The plugin is a **server plugin**: the Pandora FMS Plugin Server executes it,
and each run delivers the generated agent XML to Pandora FMS through Tentacle or
into a local data directory. Nothing is installed on the Kafka broker.

What the plugin measures has three consequences worth stating before you
configure it:

- **It does not read Kafka broker JMX metrics.** The modules describe the
  producer and consumer clients that the plugin creates, not the producers and
  consumers of your applications, and not the broker's own MBeans.
- **It does not send or consume records.** The plugin creates both clients,
  optionally subscribes the consumer to topics, reads the metric snapshot and
  closes them. It does not poll the consumer and commits no offsets.
- **It creates one agent per `--bootstrap_servers` entry.** Two successfully
  processed endpoints produce two agents, even when both point to the same
  cluster.

The plugin prints `1` when it processed every endpoint without an exception and
`0` when any endpoint raised one. That printed value is what a Pandora FMS
plugin module receives. A broker that cannot be reached makes the run print `0`;
the value does not prove that the generated agent was delivered, so verify
delivery separately (see [Verify](#verify)).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.apache_kafka`, version `1.1` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all integrations are compatible with Pandora FMS NG 784 and later versions. This is a catalogue-wide statement covering the addon, not a test record for it |
| A Kafka listener reachable from the Pandora FMS server over TCP | `Required` | The plugin connects to every endpoint listed in `--bootstrap_servers` |
| A listener that accepts unauthenticated PLAINTEXT connections | `Required` | The addon exposes no options for SASL authentication or TLS, so it can only use the Kafka client's default connection settings |
| Rocky Linux | `Known compatible` | The legacy guide for this addon records Rocky Linux as the system where it was tested. Not re-validated for version `1.1` |
| Other Linux distributions | `Not validated` | No distribution range or version matrix has been recorded for this addon |
| Kafka broker versions | `Not validated` | No broker version matrix has been recorded for this addon |
| `tentacle_client` in `PATH` | `Required` when `--transfer_mode` is not `local` | Tentacle delivery runs that command |
| Write access to `/tmp` | `Required` | The plugin stages the generated XML in `/tmp` before delivery |
| Write access to `/var/spool/pandora/data_in/` | `Required` when `--transfer_mode local` is used | The XML document is moved into that directory |

No compatibility statement establishes a Kafka version range, a broker
distribution or a Linux distribution other than the Rocky Linux record above.
Keep each claim at the scope its source proves.

### Kafka requirements

1. **A reachable Kafka listener.** Use the listener address and port in
   `--bootstrap_servers`, for example `<TARGET_HOST>:9092`. Include the port
   explicitly in every endpoint; Kafka's default client port is `9092`.
2. **A listener that accepts the client's default connection.** The addon has
   no `security_protocol`, SASL or TLS options. A cluster whose listeners
   require SASL authentication, TLS client certificates or another
   authenticated protocol cannot be monitored with this version.
3. **No Kafka account or JMX access.** The plugin authenticates with nothing,
   so it needs no Kafka user, no JMX port and no RMI credentials. If anonymous
   access to the listener is disabled, the connection fails and the run reports
   it only as a broker processing error.

The plugin does not read or write topic data, so it needs no topic ACL for the
applications you monitor. Restrict the listener to the Pandora FMS server
network instead of opening it broadly.

### Pandora FMS requirements

1. **Pandora FMS with the Plugin Server enabled** on the server that will run
   the plugin.
2. **A Tentacle server** reachable at `--tentacle_ip` and `--tentacle_port`
   when the default Tentacle delivery is used, plus the `tentacle_client`
   command in `PATH`.
3. **A writable data directory** when `--transfer_mode local` is used. The
   plugin moves the XML into `/var/spool/pandora/data_in/`; the option does not
   let you choose another directory.
4. **Write access to `/tmp`** for the user that runs the Plugin Server. The
   generated XML is staged there before delivery.

### Install the plugin

Download the addon from its Marketplace entry, whose download is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.apache_kafka](https://marketplace.pandorafms.com/entries/pandorafms.apache_kafka)

Copy the `pandora_kafka` executable to the Pandora FMS server and give it
execute permission. The recommended directory for server plugins is:

```text
/usr/share/pandora_server/util/plugin/
```

```bash
sudo chmod 755 /usr/share/pandora_server/util/plugin/pandora_kafka
```

Nothing is installed on the Kafka broker, and the Kafka server does not need
JMX enabled.

## Configure

The plugin has no configuration file. It takes all its settings from the
command line, starting from built-in defaults:

```text
built-in defaults < command-line options
```

Every option is documented in [Command-line parameters](#command-line-parameters).
This section explains the decisions that change what the plugin measures and
where the result goes.

### Endpoints

`--bootstrap_servers` is mandatory and accepts a comma-separated list of Kafka
endpoints in `host:port` form:

```text
--bootstrap_servers <KAFKA_HOST_1>:9092,<KAFKA_HOST_2>:9092
```

Each non-empty item is processed independently and produces one agent. Empty
items between commas are ignored. The plugin does not create one agent per
cluster broker: it creates one producer and one consumer per item and names the
agent after that item.

### Topics

The consumer can subscribe to a list of topics, a regular expression, or
nothing:

- `--topics orders,payments` subscribes to the listed topics.
- `--topic_regex '^prod-.*'` subscribes to the topics that match the pattern.
- When both are given, `--topic_regex` takes precedence and `--topics` is
  ignored.
- When neither is given, the consumer is created without a subscription.

Subscription does not make the plugin read messages. It never polls the
consumer, so no records are consumed and no offsets are committed. The consumer
uses the fixed group identifier `monitoring-client` with automatic commit
disabled.

An invalid regular expression is not rejected before the run starts: the error
is printed only with `--verbose`, and the subscription then raises during that
endpoint's processing, which makes the run print `0`. Test the pattern with
`--verbose` before registering it.

### Agent and module prefixes

`--agent_prefix` is prepended to both the name and the alias of every generated
agent, and `--module_prefix` is prepended to every generated module name. Both
default to an empty string.

```text
--agent_prefix KAFKA_ --module_prefix METRIC_
```

With the broker `kafka1:9092`, the agent is named `KAFKA_kafka1:9092`, and the
module `producer-metrics.request-rate` becomes
`METRIC_producer-metrics.request-rate`.

### Delivery

The default is Tentacle delivery. `--transfer_mode` accepts one meaningful
value:

| Value | Behavior |
|-------|----------|
| `tentacle` (default) | Sends the XML document with `tentacle_client` to `--tentacle_ip`:`--tentacle_port` |
| `local` | Moves the XML document into `/var/spool/pandora/data_in/` |
| Any other value, including a misspelling | Also uses Tentacle; the plugin only treats the exact value `local` as local delivery |

`--tentacle_ip` defaults to `127.0.0.1` and `--tentacle_port` to `41121`. They
are only used by Tentacle delivery. Local delivery has no configurable folder:
if the Pandora FMS server does not use `/var/spool/pandora/data_in/`, use
Tentacle instead.

Tentacle failures are printed on standard error, but they do not change the
`1` or `0` the plugin prints. See [Output and exit status](#output-and-exit-status).

### Register the plugin in the console

1. Open **Servers → Plugins** and click **Register Plugin**.
2. Set a name, the plugin type **Standard**, an optional maximum timeout and a
   description.
3. In **Plugin command**, enter the full path to the executable on the Pandora
   FMS server:
   `/usr/share/pandora_server/util/plugin/pandora_kafka`.
4. In **Plugin parameters**, combine the mandatory endpoint with the options you
   need, using the plugin macros `_field1_`, `_field2_`, ... as placeholders:

```text
--bootstrap_servers _field1_ --agent_prefix _field2_ --module_prefix _field3_ --transfer_mode tentacle --tentacle_ip 127.0.0.1 --tentacle_port 41121
```

5. In **Macro parameters**, describe each field. The example uses these values:

| Field | Description | Example value |
|-------|-------------|---------------|
| `_field1_` | Kafka endpoint, including the port; several endpoints separated by commas | `<KAFKA_HOST>:9092` |
| `_field2_` | Prefix for the generated agent names and aliases | `KAFKA_` |
| `_field3_` | Prefix for the generated module names | `METRIC_` |

<!-- SCREENSHOT NEEDED: Server plugin registration form in the Pandora FMS console showing the pandora_kafka command path and the parameter fields, with lab placeholders and no real hosts. -->

Add `--topics _field4_` or `--topic_regex _field4_` only when you want a
subscription. Every flag that remains in the parameter string must receive a
value: a blank macro leaves the flag without an argument, and the plugin exits
with an argument-parsing error instead of running. Remove the flag rather than
leaving its field empty.

After the server plugin is created, open an agent, create a **plugin** module
and select the registered plugin. That module receives the printed `1` or `0`.
The Kafka metrics do not go into that module: they arrive in the separate agents
the plugin creates.

<!-- SCREENSHOT NEEDED: Plugin module form in the Pandora FMS console with the Kafka plugin selected and its macro fields filled, without real credentials or hostnames. -->

### Security

- The addon has no user, password or token options, and no SASL or TLS
  settings. It connects with the Kafka client's default unauthenticated
  PLAINTEXT configuration.
- Because there is no transport encryption, metrics and connection metadata
  travel in clear text between the Pandora FMS server and the Kafka listener.
  Restrict the listener to a trusted network, or do not use this addon where
  authentication or encryption is mandatory.
- The plugin stores no credentials, so there is no secret to protect in a
  configuration file. Its command line only carries broker addresses, prefixes
  and delivery settings.
- `--verbose` prints broker error details on standard output. Those messages
  can include broker addresses and exception text, so review them before
  sharing a manual run.

## Verify

Run the plugin manually from a terminal on the Pandora FMS server:

```bash
./pandora_kafka \
  --bootstrap_servers <TARGET_HOST>:9092 \
  --topics <TOPIC> \
  --agent_prefix KAFKA_ \
  --transfer_mode tentacle \
  --tentacle_ip <PANDORA_FMS_SERVER> \
  --tentacle_port 41121 \
  --verbose
```

A successful run ends with `1` on standard output. With Tentacle delivery, the
agent `KAFKA_<TARGET_HOST>:9092` and its modules appear in Pandora FMS after the
next data processing cycle. With `local` delivery, check that a `.data` file has
been moved into `/var/spool/pandora/data_in/` and that the agent appears after
the data server processes it.

The printed value alone is not enough to verify the integration:

- `1` means the plugin created the producer and the consumer for every endpoint
  and collected their metrics without an exception. Client creation resolves the
  broker version over the network, so a broker that rejects or does not answer
  the connection produces `0` instead.
- `1` does not prove delivery: a Tentacle failure is printed on standard error
  but still leaves `1` on standard output.

Verify the data, not only the exit line:

1. Confirm the generated agent exists and its name follows the prefix rule.
2. Open its modules and check that connection and request metrics report
   activity.
3. If every value is zero, check connectivity before assuming the plugin
   delivered correctly.

<!-- SCREENSHOT NEEDED: Kafka agent in the Pandora FMS console with its generated modules and current values for one lab broker. -->

Use `./pandora_kafka -h` to print the usage summary, the plugin version and the
execution example.

## Understand the results

### Agents

The plugin creates one agent per successfully processed non-empty
`--bootstrap_servers` item. Name and alias use the same value:

```text
<agent_prefix><host:port>
```

For example, with `--agent_prefix KAFKA_` and the endpoint `kafka1:9092`, the
agent is `KAFKA_kafka1:9092`. Every generated agent has an interval of 300
seconds, the description `Created by plugin` and no agent group assigned.

Running the plugin twice with the same endpoint updates the same agent name.
Running it with two endpoints that belong to the same cluster creates two
agents with duplicated module sets.

### Modules

The plugin iterates over every metric group and metric name reported by the
producer and the consumer. The module name is:

```text
<module_prefix><metric_group>.<metric_name>
```

All modules are created as `generic_data`, without a unit and without a
description. Floating-point values that are `NaN`, positive infinity or
negative infinity are written as `0.0`.

The exact catalogue depends on the Kafka client state and the Kafka version.
The stable groups and representative modules are:

| Source | Metric group | Representative modules without prefix |
|--------|--------------|---------------------------------------|
| Producer and consumer | `kafka-metrics-count` | `kafka-metrics-count.count` |
| Producer | `producer-metrics` | `producer-metrics.connection-count`, `producer-metrics.request-rate`, `producer-metrics.request-latency-avg`, `producer-metrics.outgoing-byte-rate` |
| Producer | `producer-node-metrics.node-<node>` | `producer-node-metrics.node-<node>.outgoing-byte-rate`, `producer-node-metrics.node-<node>.request-rate`, `producer-node-metrics.node-<node>.response-rate` |
| Consumer | `consumer-metrics` | `consumer-metrics.connection-count`, `consumer-metrics.request-rate`, `consumer-metrics.incoming-byte-rate`, `consumer-metrics.request-latency-avg` |
| Consumer | `consumer-node-metrics.node-<node>` | `consumer-node-metrics.node-<node>.incoming-byte-rate`, `consumer-node-metrics.node-<node>.request-rate`, `consumer-node-metrics.node-<node>.response-rate` |
| Consumer | `consumer-fetch-manager-metrics` | `consumer-fetch-manager-metrics.fetch-size-avg`, `consumer-fetch-manager-metrics.bytes-consumed-rate`, `consumer-fetch-manager-metrics.records-consumed-rate`, `consumer-fetch-manager-metrics.records-lag-max` |
| Consumer | `consumer-coordinator-metrics` | `consumer-coordinator-metrics.commit-rate`, `consumer-coordinator-metrics.assigned-partitions` |

In the node groups, `<node>` is the numeric Kafka node identifier, for example
`node-1`. The group name already contains it, so a full module name looks like
`producer-node-metrics.node-1.outgoing-byte-rate`. Node groups appear only for
the nodes the probe client actually contacts; the set depends on the cluster
metadata returned to that client.

Both clients register their own `kafka-metrics-count` group, so the generated
agent XML contains `kafka-metrics-count.count` twice: once with the producer's
count and once with the consumer's count. This is expected behavior, not a
duplicated agent.

### What the values represent

Each run creates new clients and reads their metrics immediately. The values are
therefore a snapshot of a freshly created probe, not a continuous sample of your
application:

- Connection counters, request counters and request latency describe the
  plugin's own client connections.
- Record and commit rates describe traffic that the probe client does not
  generate: the plugin sends no records, polls no records and commits no
  offsets, so those rates normally remain at their initial values. Byte and
  request rates reflect only the probe's own connection and metadata traffic,
  not your application's throughput.
- Averages that need samples from the client's lifetime can be `0.0` because
  the plugin converts their initial `NaN` to zero.
- Consumer group metrics do not reflect your application's consumer groups. The
  consumer uses the fixed group identifier `monitoring-client`, with automatic
  commit disabled, and never joins a group during the run.

Use the connection and request metrics to observe whether the Kafka listener is
reachable and responsive from the Pandora FMS server. Do not use this addon as a
substitute for Kafka broker JMX monitoring or for instrumenting application
producers and consumers.

## Operate and troubleshoot

The plugin keeps no state between executions. Every run creates its clients,
collects one snapshot, delivers one agent document and exits, so it can be run
manually at any time without affecting offsets or topic data.

Schedule the registered plugin module at the interval you want. The generated
agents keep their fixed 300-second interval, but their values are refreshed only
when the plugin module runs; align the module interval with the desired data
cadence. Use `--verbose` for manual diagnosis, but do not leave it in the
registered parameter string: its diagnostic lines are written to standard
output and become part of the value the plugin module receives.

### Output and exit status

| Result | Meaning |
|--------|---------|
| Standard output `1` | Every endpoint was processed without an exception: its clients were created and their metrics collected. Delivery is not guaranteed |
| Standard output `0` | At least one endpoint raised an exception, for example because the broker was unreachable or rejected the connection. Run again with `--verbose` to see the detail |
| No standard output without `--verbose` | The bootstrap list contained no non-empty item. The process exits with status `0` |
| Argument-parsing error on standard error | A required option is missing or a flag has no value, for example a blank macro field. The process exits with status `2` |
| Process exit status `0` with `1` or `0` on standard output | Normal run. The printed number is the module value, not the process status |

### Common problems

- **The run prints `1` but no agent appears.** The broker processing succeeded
  but delivery failed. Check that `tentacle_client` exists in `PATH` and can
  reach `--tentacle_ip`:`--tentacle_port`. Run manually with `--verbose` and read
  standard error; Tentacle errors do not alter the printed `1`. For local
  delivery, check that `/var/spool/pandora/data_in/` exists and is writable.
- **The run prints `0`.** At least one endpoint failed. Run with `--verbose` and
  read the `Error with broker ...` line. The usual causes are a wrong address or
  port, a listener that requires authentication or TLS, an invalid
  `--topic_regex`, or a malformed endpoint.
- **The run prints nothing without `--verbose`.** `--bootstrap_servers` was
  accepted but contained no non-empty item, for example a comma or spaces only.
  The process exits `0` without an agent or a value. Correct the endpoint list.
- **The plugin exits before connecting.** An option is missing its value. This
  is the usual result of leaving a `_fieldN_` macro empty for a flag that you
  kept in the parameter string. Remove the unused flag or fill the field.
- **The agent exists but every value is zero.** The probe connected, but it did
  not exchange further data with the cluster. Check the listener address and
  port, and whether the listener accepts unauthenticated PLAINTEXT connections.
  Remember that record and commit rates are expected to stay at their initial
  values because the probe sends and consumes no records, and byte and request
  rates reflect only the probe's own traffic.
- **The cluster requires SASL or TLS.** This version cannot connect to it. The
  addon has no option to configure authentication or encryption; use a Kafka
  monitoring path that supports those settings.
- **`--transfer_mode local` does not deliver.** The plugin always moves the XML
  into `/var/spool/pandora/data_in/`. If the Pandora FMS server uses another
  data directory, use Tentacle delivery instead.
- **A misspelled transfer mode still tries Tentacle.** Only the exact value
  `local` selects local delivery; every other value falls back to Tentacle.
- **Values look stale.** Every run returns the snapshot taken at that moment.
  Check the plugin module interval and the broker state rather than expecting a
  continuous series.

## Reference

### Command-line parameters

```text
./pandora_kafka --bootstrap_servers <host:port> [--topics <topic1,topic2>] [--topic_regex <regex>] [--agent_prefix <prefix>] [--module_prefix <prefix>] [--transfer_mode <mode>] [--tentacle_ip <ip>] [--tentacle_port <port>] [--verbose]
```

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `-h`, `--help` | No | — | Prints the usage summary, the plugin version and the execution example, then exits |
| `--bootstrap_servers` | Yes | — | Comma-separated Kafka endpoints in `host:port` form. Empty items are ignored. Each remaining item produces one agent |
| `--topics` | No | Empty | Comma-separated topics for the consumer subscription. Ignored when `--topic_regex` is set |
| `--topic_regex` | No | Empty | Regular expression for the consumer subscription. Takes precedence over `--topics`. An invalid pattern fails during the run |
| `--agent_prefix` | No | Empty | Prefix added to the name and alias of every generated agent |
| `--module_prefix` | No | Empty | Prefix added to every generated module name |
| `--transfer_mode` | No | `tentacle` | `local` moves the XML into `/var/spool/pandora/data_in/`. Any other value, including the default, uses Tentacle |
| `--tentacle_ip` | No | `127.0.0.1` | Tentacle server address for Tentacle delivery |
| `--tentacle_port` | No | `41121` | Tentacle server port for Tentacle delivery |
| `--verbose` | No | Disabled | Prints broker error and diagnostic messages on standard output |

### Delivery

| Setting | Value |
|---------|-------|
| Default delivery | Tentacle |
| Tentacle client command | `tentacle_client`, resolved through `PATH` |
| Tentacle address and port | `--tentacle_ip` and `--tentacle_port` |
| Local delivery selector | `--transfer_mode local` (exact value) |
| Local destination | `/var/spool/pandora/data_in/` |
| Configurable local destination | No |
| XML staging directory | `/tmp` |
| Runtime dependency on the broker | None; nothing is installed on the Kafka broker |

### Generated agents

| Attribute | Value |
|-----------|-------|
| Cardinality | One agent per successfully processed non-empty `--bootstrap_servers` item |
| Name | `<agent_prefix><host:port>` |
| Alias | Same as the name |
| Description | `Created by plugin` |
| Interval | `300` seconds |
| Group | Not set |
| Data source | Producer and consumer metrics of the clients created in that run |

### Consumer behaviour

| Behavior | Value |
|----------|-------|
| Consumer group identifier | `monitoring-client` |
| Automatic offset commit | Disabled |
| Records consumed | None; the plugin never polls the consumer |
| Offsets committed | None |
| Subscription | Optional, through `--topics` or `--topic_regex` |
| Effect on topic data | None |

### Metric groups

The plugin prefixes every module name with `<module_prefix>`. The metric part is
`<metric_group>.<metric_name>`, where `<node>` is the numeric Kafka node
identifier.

| Source | Metric group | Example metric names |
|--------|--------------|----------------------|
| Producer and consumer | `kafka-metrics-count` | `count` |
| Producer | `producer-metrics` | `connection-count`, `request-rate`, `request-latency-avg`, `outgoing-byte-rate`, `incoming-byte-rate` |
| Producer | `producer-node-metrics.node-<node>` | `outgoing-byte-rate`, `incoming-byte-rate`, `request-rate`, `response-rate`, `request-latency-avg` |
| Consumer | `consumer-metrics` | `connection-count`, `request-rate`, `request-latency-avg`, `incoming-byte-rate`, `outgoing-byte-rate` |
| Consumer | `consumer-node-metrics.node-<node>` | `incoming-byte-rate`, `outgoing-byte-rate`, `request-rate`, `response-rate`, `request-latency-avg` |
| Consumer | `consumer-fetch-manager-metrics` | `fetch-size-avg`, `fetch-size-max`, `bytes-consumed-rate`, `records-consumed-rate`, `records-lag-max` |
| Consumer | `consumer-coordinator-metrics` | `commit-latency-avg`, `commit-latency-max`, `commit-rate`, `assigned-partitions` |

This list is a functional catalogue, not a fixed contract: the exact metric set
depends on the Kafka client version and on the state of the clients at
execution time. All generated modules use `generic_data`, with no unit and no
description.

The metric definitions published by Kafka for its clients help interpret the
values:

- [Consumer monitoring](https://kafka.apache.org/documentation/#consumer_monitoring)
- [Producer monitoring](https://kafka.apache.org/documentation/#producer_monitoring)

### Addon identity

| Field | Value |
|-------|-------|
| Marketplace identifier | `pandorafms.apache_kafka` |
| Marketplace name | Kafka monitoring |
| Version | `1.1` — the current Marketplace version, also reported by `-h` |
| Marketplace last update | 2026-08-28 |
| License | One — the download is limited to licensed users |
| Marketplace type | Miscelaneus |
| Downloads | 9 |
| Workflow | Monitoring plugin, server plugin mode |
| Executable | `pandora_kafka` |
| Marketplace entry | [pandorafms.apache_kafka](https://marketplace.pandorafms.com/entries/pandorafms.apache_kafka) |
