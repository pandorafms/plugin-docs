# Redis monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The Redis monitoring plugin turns the statistics of a Redis server into Pandora FMS modules. Each run connects to one Redis instance, reads the `INFO` sections you select, and publishes every field Redis returns as a module named exactly after that field: server identity and uptime, connected clients, memory, persistence, statistics, replication, CPU, per-command counters, cluster state and keyspace sizes.

Nothing is installed on the Redis server. The plugin connects over TCP from the host that runs it, with an optional password.

The plugin supports two execution models:

- **Server plugin mode** (default when neither mode key is set): each run builds an agent document and delivers it to Pandora FMS through Tentacle or a local data folder.
- **Agent plugin mode** (requires `as_agent_plugin=1`): each run prints the generated modules as XML on standard output, for the Pandora FMS agent to ingest.

This page documents the monitoring plugin, which reads the statistics of one instance per run. Discovering Redis instances and generating their agents is a different addon, documented in [Redis Discovery](../discovery/redis.md).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `redis`, version `1.1` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Network access from the host that runs the plugin to the Redis listener (TCP, `6379` by default in Redis) | `Required` | The plugin opens a client connection to the address in `server` |
| A Redis password, when the instance requires authentication | `Required` when authentication is enabled | Prerequisite of the `password` key, not a compatibility statement |
| `tentacle_client` on the host that runs the plugin | `Required` when `mode=tentacle` | Server mode delivery |
| Redis server versions | `Not validated` | No version matrix has been recorded. The legacy guide only states the plugin was developed against Redis `3.2.12`; the plugin itself requires nothing beyond a server that answers `INFO` |
| Operating system of the host that runs the plugin | `Not validated` | No operating system has been recorded for this version |
| Pandora FMS versions | `Not validated` | The Marketplace carries a general banner for all its integrations, not a statement specific to this addon |

### Prerequisites

1. **Network access** from the host that runs the plugin to the Redis host and port.
2. **A Redis password**, when the instance has authentication enabled. The plugin sends a password only: it has no user name key, so an instance that requires an ACL user name cannot be monitored with it. Use the `default` user with `requirepass`, or an ACL user that authenticates with a password alone.
3. **Pandora FMS** to receive the output: the Pandora FMS server in server plugin mode, or the Pandora FMS agent of the monitored host in agent plugin mode.
4. **The Tentacle client (`tentacle_client`) available in `PATH`**, only when server mode delivers through Tentacle.

The account used by the plugin only reads `INFO`. No official source identifies a narrower set of Redis permissions; grant only what the instance needs to answer that command.

### Install the plugin

Download the package from the free Marketplace entry:

[https://marketplace.pandorafms.com/entries/redis](https://marketplace.pandorafms.com/entries/redis)

Copy the `redis_monitor` executable to the host that will run the plugin, and create its configuration file next to it (see [Configure](#configure)). Nothing is installed on the Redis server, and no Redis client tools are needed on the monitoring host.

## Configure

The plugin combines its defaults with two input sources, in increasing precedence:

```text
defaults < configuration file < command-line arguments
```

The configuration file is optional. When it is used, it must be the **first argument** of the command line: a file path placed after a flag is not read. It is a plain-text file with one `key=value` pair per line. Blank lines and lines that start with `#` are skipped, keys and values are trimmed, and the last occurrence of a repeated key wins.

The file has no sections. The plugin reads only the keys listed in [Configuration file keys](#configuration-file-keys); a bracketed header such as `[THRESHOLDS]` is stored as an unused key with an empty value and has no effect.

The two keys that define what is read are:

- **`server`** — the instance to read, as `<REDIS_HOST>:<REDIS_PORT>`. Include the port: the sample configuration always does.
- **`metrics`** — the `INFO` sections to read, separated by spaces. `all` reads every section the server reports.

### Execution modes

Agent plugin mode is the shortest configuration: the Pandora FMS agent runs the plugin and ingests the module XML it prints.

```ini
server=<REDIS_HOST>:<REDIS_PORT>
password=<PASSWORD>
metrics=all
module_group=Redis
as_agent_plugin=1
as_server_plugin=0
```

Server plugin mode needs an agent name and a delivery target. With Tentacle:

```ini
server=<REDIS_HOST>:<REDIS_PORT>
password=<PASSWORD>
metrics=all
module_group=Redis
as_agent_plugin=0
as_server_plugin=1
agent_name=redis-monitoring
temp=/tmp
mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER>
tentacle_port=41121
```

Or copy the agent document into a local data folder instead of using Tentacle:

```ini
server=<REDIS_HOST>:<REDIS_PORT>
password=<PASSWORD>
metrics=all
as_agent_plugin=0
as_server_plugin=1
agent_name=redis-monitoring
temp=/tmp
mode=local
local_folder=/var/spool/pandora/data_in
```

The same agent plugin run with arguments only, without a configuration file:

```bash
./redis_monitor -server <REDIS_HOST>:<REDIS_PORT> -password <PASSWORD> -metrics all -as_agent_plugin 1
```

Key points:

- `as_agent_plugin` and `as_server_plugin` select the execution model. When neither is set, the plugin runs as a server plugin. When both are set to `1`, both models run in the same execution: the module XML is printed **and** the agent document is delivered.
- `agent_name` is required in server mode: it is the name of the agent created in Pandora FMS. The plugin sends that name only; it reads no agent interval, agent group or version key.
- `mode` selects the delivery: `tentacle` uses the Tentacle client, and any other value, including `local`, copies the agent document into `local_folder`.
- `module_group` is the name of the module group assigned to every generated module. Pandora FMS resolves it case-insensitively against the existing groups; when the name does not match one, the modules are created without that group.
- `temp` is the folder where the agent document is written before delivery. On Linux it defaults to `/tmp` when the key is absent.
- `metrics` is a single value: the section names are separated by spaces, so the whole list goes on one line.
- Module names are the Redis field names, with no prefix. Run **one agent per Redis instance**: two instances delivered to the same agent overwrite each other's modules.

### Credentials and transport

- The Redis connection is not encrypted: the plugin has no TLS option, so the password and the statistics travel in clear text. Keep the connection on a trusted network, or place a TLS tunnel in front of Redis.
- Inline `password` is stored in the configuration file in plain text: restrict the file permissions to the user that runs the plugin.
- Avoid `-password` on the command line: the command is stored in the shell history and the operating system process list can expose it while the plugin runs. Prefer the configuration file with restrictive permissions (for example `chmod 600`).
- `debug=1` prints diagnostic dumps to standard output, including the full `INFO` response. Treat that output as sensitive: do not paste it into public tickets, and do not enable `debug` together with agent plugin mode (see [Operate and troubleshoot](#operate-and-troubleshoot)).

### Register the plugin in Pandora FMS

`redis_monitor` can also be registered in the Pandora FMS console as a standard server plugin, so Pandora FMS executes it on the server that runs the modules instead of in a command line. Registered this way the plugin keeps server plugin mode: every run builds the agent document and delivers it, and the agent with its modules appears in the console.

Use the absolute path of the executable as the plugin command, and the documented keys as parameters. The console substitutes its `_fieldN_` macros at execution time, so per-module values can be supplied without editing the plugin:

```text
-server _field1_ -password _field2_ -metrics _field3_ -agent_name _field4_ -mode tentacle -tentacle_ip 127.0.0.1 -tentacle_port 41121
```

| Field | Description | Example value |
| --- | --- | --- |
| `_field1_` | Redis address, including the port | `<REDIS_HOST>:<REDIS_PORT>` |
| `_field2_` | Redis password. It travels in the module command line, so treat the module definition as sensitive | — |
| `_field3_` | `INFO` sections to read, separated by spaces | `all` |
| `_field4_` | Name of the agent that will hold the modules | `redis-monitoring` |

`-tentacle_ip 127.0.0.1` delivers to the Tentacle server of the machine that runs the plugin, so the agent lands in the Pandora FMS server that executes the module. To copy the document into a local data folder instead, replace the Tentacle flags with `-mode local -local_folder /var/spool/pandora/data_in`.

<!-- SCREENSHOT NEEDED: Pandora FMS console plugin registration form for server plugins, showing the redis_monitor plugin command and its parameter and macro fields. -->

Once registered, the plugin is available when creating plugin modules, and each module fills the fields individually. The module is executed on the server selected for it, including a remote Pandora FMS server, so each Redis instance is monitored from the Pandora FMS server closest to it without installing anything on the Redis host.

## Verify

Run the plugin manually from a terminal, passing the configuration file as its first argument:

```bash
./redis_monitor /etc/pandora/plugins/redis_config.conf
```

The relative form `./redis_monitor redis_config.conf` works when the terminal is already in the directory that contains both files. Each run executes once and exits.

In agent plugin mode, a successful run prints one XML `<module>` block per field on standard output, in this form:

```xml
<module>
	<name><![CDATA[redis_version]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[7.2.4]]></data>
	<module_group>Redis</module_group>
</module>
<module>
	<name><![CDATA[connected_clients]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<module_group>Redis</module_group>
</module>
<module>
	<name><![CDATA[db0]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[keys=12,expires=4,avg_ttl=0]]></data>
	<module_group>Redis</module_group>
</module>
```

`<module_group>` is present only when `module_group` is set.

In server plugin mode a successful run prints nothing, and the agent configured in `agent_name` appears in Pandora FMS with its modules. The plugin does not report the delivery result in its exit status, so confirm the arrival in the console instead of relying on the command.

<!-- SCREENSHOT NEEDED: Pandora FMS agent view listing the modules generated by redis_monitor for one Redis instance. -->

## Understand the results

Every module is one field of the Redis `INFO` response. The plugin reads the sections listed in `metrics`, and for each field it creates a module named after the field, with a group when `module_group` is set.

### Module names and types

- The module name is the Redis field name exactly as the server returns it: no prefix, no section prefix. `used_memory` stays `used_memory`, and a keyspace line arrives as `db0`.
- A value that contains a letter becomes a `generic_data_string` module: `redis_version`, `role`, `maxmemory_policy`, `used_memory_human` (`1.05M`), `rdb_last_bgsave_status` and `db0` (`keys=12,expires=4,avg_ttl=0`).
- A value with digits only becomes a `generic_data` module: `connected_clients`, `used_memory`, `uptime_in_seconds`, `maxmemory`, `mem_fragmentation_ratio`, and also the numeric flags `redis_git_dirty` and `aof_enabled`.
- The plugin adds no description, unit or threshold, and no availability module. The module catalog is exactly the set of fields the selected sections return for your Redis version and configuration.

There is no connectivity module: when a run cannot read the instance, it publishes no module at all and the existing modules receive no new data.

### Sections you can read

`metrics` accepts any section name the Redis server accepts, separated by spaces; the plugin only passes each name to `INFO`, so names match case-insensitively as Redis does. `all` reads every section. The sections commonly used with this plugin are:

| `metrics` value | What it reads | Representative modules |
| --- | --- | --- |
| `server` | Identity, version and uptime | `redis_version`, `redis_mode`, `os`, `arch_bits`, `process_id`, `run_id`, `tcp_port`, `uptime_in_seconds`, `uptime_in_days`, `executable`, `config_file` |
| `clients` | Client connections | `connected_clients`, `blocked_clients`, `client_longest_output_list`, `client_biggest_input_buf` |
| `memory` | Memory | `used_memory`, `used_memory_human`, `used_memory_rss`, `used_memory_peak`, `maxmemory`, `maxmemory_policy`, `mem_fragmentation_ratio`, `mem_allocator` |
| `persistence` | RDB and AOF state | `loading`, `rdb_changes_since_last_save`, `rdb_last_bgsave_status`, `rdb_last_save_time`, `aof_enabled`, `aof_last_write_status`, `aof_current_size` |
| `stats` | Counters and rates | `total_connections_received`, `total_commands_processed`, `instantaneous_ops_per_sec`, `keyspace_hits`, `keyspace_misses`, `evicted_keys`, `expired_keys` |
| `replication` | Role and replicas | `role`, `connected_slaves`, `master_replid`, `master_repl_offset`; the `master_*` and `slave*` fields depend on the instance role |
| `cpu` | CPU consumed by the server | `used_cpu_sys`, `used_cpu_user`, `used_cpu_sys_children`, `used_cpu_user_children` |
| `commandstats` | Per-command counters | `cmdstat_get`, `cmdstat_set`, with values such as `calls=1,usec=2,usec_per_call=2.00` |
| `cluster` | Cluster state | `cluster_enabled` |
| `keyspace` | Keys per database | `db0`, `db1`, with values such as `keys=12,expires=4,avg_ttl=0` |
| `all` | Every section above | — |

Fields appear or disappear according to the Redis version and the instance configuration (for example, AOF fields exist only when AOF is enabled), so a module that is missing from the output is a field the server did not report in that run.

## Operate and troubleshoot

### Everyday operation

- The plugin keeps no state: every execution reads the instance at that moment, so it can be run manually at any time.
- In server plugin mode, schedule it from Pandora FMS, for example through the server plugin scheduler or `cron`. In agent plugin mode, the Pandora FMS agent executes it according to the configured plugin schedule.
- Use `debug=1` in manual runs to print the connection details, the section list and the complete `INFO` response. `debug` writes to standard output, so in agent plugin mode it interleaves with the module XML and the agent cannot parse the output: never enable it in a scheduled agent plugin execution.
- Because module names carry no instance prefix, keep one agent per instance and use `module_group` to separate these modules from others in the same agent.

### Troubleshooting

- **No module XML is printed in agent plugin mode** — check that `as_agent_plugin=1` is in effect (when both mode keys are empty the plugin runs as a server plugin), that `metrics` is not empty, and that the configuration file is the first argument of the command.
- **The agent never appears in Pandora FMS in server mode** — the delivery failed silently. Run once with `debug=1` to see the reason: a missing `mode` and a missing `local_folder` are reported only with `debug` enabled, and a Tentacle failure prints the client message only with `debug` enabled.
- **`tentacle_client` cannot be found or cannot connect** — make sure the client is installed and in `PATH` (or set `tentacle_client` to its absolute path) and that `tentacle_ip` and `tentacle_port` reach the Tentacle server.
- **The local folder delivery fails** — check that `local_folder` exists, is writable by the user that runs the plugin, and names a folder, not a file. The error is printed only with `debug=1`.
- **`NOAUTH` or an authentication error from Redis** — the instance requires a password and `password` is empty or wrong. If the instance requires an ACL user name as well, this plugin cannot authenticate (it has no user name key).
- **Connection refused or timeout** — the plugin cannot reach `server`. Check the host, the port, the firewall and that Redis is listening on an address reachable from the monitoring host.
- **Some older modules stop updating after a Redis upgrade or configuration change** — the field no longer exists in the `INFO` output. Adjust `metrics` or the alerting on that module.
- **The module list is empty** — `metrics` is empty or names sections the instance does not report. Start with `metrics=all` and narrow it once you see which modules arrive.

## Reference

### Configuration file keys

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `server` | Yes | — | Redis address, as `<REDIS_HOST>:<REDIS_PORT>`. Include the port. |
| `password` | No | Empty (no authentication) | Password sent to Redis. The plugin has no user name key. |
| `metrics` | Yes | — | `INFO` sections to read, separated by spaces. `all` reads every section. |
| `as_agent_plugin` | No | `0` | `1` (or any value greater than `0`) prints the module XML on standard output. |
| `as_server_plugin` | No | `1` when neither mode key is set | `1` (or any value greater than `0`) builds and delivers the agent document. When both mode keys are `1`, both models run. |
| `agent_name` | Required in server mode | — | Name of the agent created in Pandora FMS. |
| `module_group` | No | Empty (no group sent) | Name of an existing module group assigned to every generated module. Resolved case-insensitively; an unknown name leaves the modules without that group. |
| `mode` | Required in server mode | Empty | `tentacle` delivers with the Tentacle client; any other value copies the agent document into `local_folder`. |
| `transfer_mode` | No | Empty | Alternative key for `mode`, read only when `mode` is empty. |
| `local_folder` | Required when `mode` is not `tentacle` | — | Destination folder for the agent document copy. |
| `temp` | No | `/tmp` on Linux | Folder where the agent document is written before delivery. `tmp` is accepted as an alternative key. |
| `tentacle_ip` | Required when `mode=tentacle` | — | Tentacle server address. |
| `tentacle_port` | No | `41121` | Tentacle server port. |
| `tentacle_client` | No | `tentacle_client` | Tentacle client executable, resolved in `PATH` or given as an absolute path. |
| `tentacle_opts` | No | Empty | Extra options passed to the Tentacle client, separated by whitespace. |
| `debug` | No | `0` | `1` (or any value greater than `0`) prints connection details, the section list and diagnostic messages on standard output. |

Boolean keys are enabled by any numeric value greater than `0`; `0`, an empty value or a non-numeric value means disabled.

### Command-line execution

```bash
./redis_monitor [config-file] [ -key value ... ]
```

| Condition | Behavior |
| --- | --- |
| The first argument names an existing file | The plugin reads it as the configuration file and applies the remaining arguments over its values |
| The first argument is not a file, or the file path comes after a flag | The file is not read; the plugin runs from the defaults plus the arguments |
| `-key value` | Replaces the value of `key` |
| `--key value` or `-key=value` | Not recognized: the pair is read as a different key that the plugin ignores, so the documented key keeps its default or file value |
| Arguments that do not form a `-key value` pair | Ignored; a trailing argument without a value is not reported |
| The command line is empty | The plugin runs with the default values; no usage text is printed |
| `-h` or `--help` | No help option exists: it produces no help output and is treated like any other unknown flag |

Unknown keys are accepted and ignored: the plugin does not validate the key set.

### Delivery behavior

| Situation | Result |
| --- | --- |
| `mode=tentacle` and the Tentacle transfer succeeds | The temporary file is removed after the transfer |
| `mode=tentacle` and the transfer fails | The document is not delivered; the client message is printed only with `debug=1` |
| Any other `mode` | The document is copied into `local_folder` and the temporary file is removed |
| `mode` empty and no `transfer_mode` alternative | Nothing is delivered; the reason is printed only with `debug=1` |
| Delivery result | Not reflected in the exit status; verify in the Pandora FMS console |

### Addon identity

| Field | Value |
| --- | --- |
| Marketplace identifier | `redis` |
| Marketplace name | Redis monitoring |
| Addon version | `1.1` |
| Marketplace last update | 2025-11-03 |
| Marketplace package | `redis.1.1.zip` |
| License | Free download |
| Marketplace type | Miscelaneus |
| Workflow | Monitoring plugin, agent or server plugin mode |
| Executable | `redis_monitor` |
