# Azure PostgreSQL monitoring plugin

*Article last updated: 2026-10-26.*

<!-- DRAFT: Facts verified against the addon executable and its configuration file. No live run against Azure Monitor, no console ingestion and no console capture was performed for this page. -->

## What it does

The Azure PostgreSQL monitoring plugin reads Azure Monitor metrics for one Azure Database for PostgreSQL resource and turns them into a Pandora FMS agent: 16 metrics covering CPU, memory, disk I/O, storage, connections, network traffic and replication delay. It is a server plugin: Pandora FMS executes it on a server on the module interval, or you run it manually from a terminal.

Each run authenticates with a Microsoft Entra service principal, asks Azure Monitor for the average of every metric over a time window and builds one agent data document. It works only with the resource identifier in its configuration file: it does not connect to PostgreSQL, so it needs no database user or password and works even when the database is not reachable from the Pandora FMS server.

A run delivers its result in one of three ways:

- **Agent data file** (default): the plugin writes an agent data XML file into the Pandora FMS data directory and prints `1`.
- **Tentacle**: with `--tentacle_address`, the plugin writes the same file, sends it with `tentacle_client` and then prints `1`.
- **Module XML on standard output**: with `--as_agent_plugin 1`, the plugin prints one `<module>` block per value on standard output and writes no file.

The plugin keeps no state between runs: every value it publishes is the average Azure Monitor returns for the requested window at execution time.

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
|-------|-------|----------|
| Addon version `1.0` (`pandorafms.azure_postgresql`) | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions. A catalogue-wide statement covering this addon, not a test record |
| An Azure subscription containing the PostgreSQL resource to monitor | `Required` | The plugin reads the Azure Monitor metrics of the resource identified in its configuration file |
| A Microsoft Entra service principal allowed to read that resource | `Required` | Authentication uses a tenant ID, an application ID and a client secret. Prerequisite, not a compatibility statement |
| Outbound HTTPS access from the Pandora FMS server to the Azure Monitor endpoints of the public Azure cloud | `Required` | The plugin queries Azure Monitor directly and exposes no endpoint, authority or proxy setting |
| A Pandora FMS data directory writable by the user that runs the plugin, for file and Tentacle delivery | `Required` | `--data_dir`, `/var/spool/pandora/data_in/` by default |
| Sovereign or custom Azure clouds | `Not validated` | No endpoint or authority setting exists, so a non-public cloud cannot be selected from the plugin |
| Host operating system and distribution | `Not validated` | No operating system record exists for version `1.0` |
| Azure Database for PostgreSQL server type and version | `Not validated` | The plugin requests a fixed list of 16 metric names. No matrix of server types or versions has been recorded |
| Tentacle delivery | `Not validated` | `--tentacle_address` needs a reachable `tentacle_client`; no such run has been recorded |

The Marketplace record limits the download to licensed users. It carries no maintenance or deprecation statement; see [Addon identity](#addon-identity).

### Prerequisites

1. **A Pandora FMS installation** with the Plugin Server enabled, the console to register the plugin and create the module, and a writable data directory for the delivery mode you choose.
2. **An Azure subscription** with the Azure Database for PostgreSQL resource to monitor.
3. **A Microsoft Entra service principal** and its secret, with read access to that resource.
4. **The resource identifier** of the PostgreSQL resource, in the long `/subscriptions/.../resourceGroups/.../providers/...` form.
5. **The addon files** on the Pandora FMS server that will execute the plugin.

### Prepare Azure access

1. In Microsoft Entra ID, choose or create an application registration for the monitoring. From its overview, copy the **Directory (tenant) ID** and the **Application (client) ID**.
2. Create a client secret for that application and copy its **value**, not its identifier: the value is shown only when the secret is created.
3. Grant the application read access to the PostgreSQL resource, or to the Resource Group that contains it. Read-only access is enough, because the plugin only reads the resource and its Azure Monitor metrics.
4. Open the PostgreSQL resource in the Azure portal, select **JSON view** in the overview and copy the value of its `id` field. That string is the resource identifier the plugin needs.

Keep the secret value out of tickets, chat and screenshots. The plugin stores it in a plain-text file (see [Credential and resource file](#credential-and-resource-file)).

<!-- SCREENSHOT NEEDED: Azure portal overview of an Azure Database for PostgreSQL resource with the JSON view open, showing the id field and with subscription, tenant, resource group and server names redacted. -->

### Install the addon

Download the addon package from the Marketplace entry, which is limited to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.azure_postgresql](https://marketplace.pandorafms.com/entries/pandorafms.azure_postgresql)

The package contains the executable `pandora_azurepostgresql` and a configuration file template `pandora_azurepostgresql.conf`. Copy the executable to the Pandora FMS server that will run it and make it executable. The recommended directory for server plugins is `/usr/share/pandora_server/util/plugin/`; any directory readable and executable by the user that runs plugin modules works.

Put the configuration file where that same user can read it, outside the web root, and restrict it to its owner, because it holds the client secret.

## Configure

### Credential and resource file

The plugin reads all its connection data from the file passed with `--conf`. It is plain text with one `key:value` line per setting:

```ini
#credentials
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
#id resources
serverpostgres_id:<POSTGRES_RESOURCE_ID>
```

| Key | Required | Description |
|-----|----------|-------------|
| `tenant_id` | Yes | Directory (tenant) ID of the Microsoft Entra application |
| `client_id` | Yes | Application (client) ID |
| `secret` | Yes | Client secret value. Stored in plain text: restrict the file to its owner |
| `serverpostgres_id` | Yes | Azure resource identifier of the PostgreSQL resource whose metrics are read |

The file format is rigid in four ways that matter when you edit it:

- The separator is `:` and only the text after the first colon is read, so a value cannot contain a colon. Do not add spaces around the value; leading and trailing spaces are trimmed.
- Any line that contains `#` anywhere is ignored. A `#` after a value silently discards that whole setting, so keep comments on their own lines.
- Each key is recognised by its name appearing anywhere in the line. Do not add extra keys whose names contain `tenant_id`, `client_id`, `secret` or `serverpostgres_id`.
- The four keys must be present. A file missing any of them stops the run with an error before any module is generated. The message does not always name the key, so check all four when a run fails at start-up.

### Register the server plugin

Register the executable in the console so Pandora FMS can execute it as a server plugin:

1. Open **Servers → Plugins** and click **Register plugin**.
2. Set a name and a description for the plugin.
3. In **Plugin command**, enter the absolute path of the executable on the Pandora FMS server, for example `/usr/share/pandora_server/util/plugin/pandora_azurepostgresql`.
4. In **Plugin parameters**, combine the plugin macros `_field1_`, `_field2_`, ... with the flags:

```text
--conf _field1_ --agent_name _field2_ --prefix_module _field3_ --data_dir _field4_
```

5. In **Macro parameters**, describe each field:

| Field | Description | Example value |
|-------|-------------|---------------|
| `_field1_` | Absolute path to the credential and resource file on the Pandora FMS server | `/etc/pandora/plugins/azure-postgresql.conf` |
| `_field2_` | Agent that will hold the modules | `Azure_PostgreSQL_prod` |
| `_field3_` | Prefix added to every module name | `prod` |
| `_field4_` | Pandora FMS data directory, read by the Data Server | `/var/spool/pandora/data_in/` |

<!-- SCREENSHOT NEEDED: Plugin registration form with the Azure PostgreSQL plugin command, the parameter string with _fieldN_ macros and the macro list filled with the example values above. -->

Do not add `--as_agent_plugin 1` to the registered parameters. That flag makes the plugin print module XML instead of writing the agent data file, and the plugin module would then publish that XML as its value instead of `1`.

Each registered plugin serves several PostgreSQL resources: register it once and give each plugin module its own credential file, agent name and prefix.

### Create the plugin module

1. Open the agent that will hold the modules and create a module of type **Plugin**.
2. Select the registered plugin and fill its macros with the file, agent name, prefix and data directory of the target resource.
3. Save the module.

Every execution publishes every metric the resource returns, so create one plugin module per PostgreSQL resource. Several modules pointing at the same resource repeat the same queries on every interval.

### Choose the delivery mode

- **Agent data file** (default): the plugin writes the document into `--data_dir` and prints `1`. Use it when the plugin runs on a Pandora FMS server, including a remote server.
- **Tentacle**: add `--tentacle_address <PANDORA_FMS_SERVER>` and, when it is not `41121`, `--tentacle_port <PORT>`. The plugin sends the document with `tentacle_client` and prints `1`.
- **Module XML on standard output**: add `--as_agent_plugin 1` to inspect the generated modules from a terminal without writing a file.

Tentacle delivery has two limits worth knowing before you rely on it:

- The plugin passes only the address and the port to the Tentacle client. It has no Tentacle password option, so a Tentacle server that requires one rejects the transfer.
- A rejected transfer prints `Tentacle error` on standard error but the plugin still prints `1`, and the data file stays in `--data_dir`. Check the agent in the console, not the printed value.

The Tentacle address and port are passed to the Tentacle client unquoted. Use a host name or an IP address only, without shell metacharacters.

### Credentials and transport

- The client secret lives in the configuration file in plain text. Make the file readable only by the user that runs the plugin, for example `chmod 600` and the same owner.
- The secret is never passed on the command line: the plugin receives only the path to the file, so the secret does not appear in the shell history or in the process list.
- The plugin exposes no option to skip TLS certificate verification and no proxy setting. Authentication and metric queries use the Azure endpoints and the default certificate trust store of the machine that runs the plugin. Keep the system CA bundle current.
- Use an application dedicated to Pandora FMS and grant it read access only to the resources you monitor. Rotating its secret means editing one line of the configuration file.

## Verify

Run the plugin manually on the Pandora FMS server, under the same user that executes plugin modules, to inspect the modules it generates:

```bash
./pandora_azurepostgresql --conf <PATH_TO_CONFIG> --as_agent_plugin 1
```

A successful run prints one `<module>` block per metric value. When the window returns more than one value for a metric, the output repeats that module name:

```xml
<module>
	<name><![CDATA[cpu_percent]]></name>
	<type>generic_data</type>
	<data><![CDATA[12.5]]></data>
	<description><![CDATA[2026-10-27 09:00:00+00:00 Average CPU percentage]]></description>
</module>
<module>
	<name><![CDATA[active_connections]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<description><![CDATA[2026-10-27 09:00:00+00:00 Active connections]]></description>
</module>
```

The values and the description text above are illustrative; the module names, the types and the document structure are the ones the plugin produces.

The same run without the flag uses the default mode:

```bash
./pandora_azurepostgresql --conf <PATH_TO_CONFIG> --agent_name <AGENT_NAME>
```

It writes an agent data file into `--data_dir` and prints `1`. The plugin module of a registered plugin publishes that `1`, so a module value of `1` means the run reached delivery, not that the data reached the console.

To confirm ingestion, open the agent named by `--agent_name` and check that it carries the metric modules with recent timestamps. Values only appear when Azure Monitor returned data for the window: a metric with no value is absent from that run.

<!-- SCREENSHOT NEEDED: Agent module list in the Pandora FMS console after a plugin run, showing the Azure PostgreSQL metric modules with recent timestamps and the plugin module value 1. -->

## Understand the results

A successful run produces one agent and its modules:

| Property | Value |
|----------|-------|
| Agent name | `--agent_name`; `Azure_Monitor_Postgresql` by default |
| Agent alias | Same as the agent name |
| Agent description | `Azure PostgreSQL Metrics` |
| Group | `--group`; `Azure` by default. The group must exist in the console |
| Agent address | Empty |
| Agent interval | Empty in the agent definition; an agent that already exists keeps its own interval |
| Module names | Azure Monitor metric name, with `<prefix>_` in front when `--prefix_module` is set |
| Module type | `generic_data` for the 16 metrics; `generic_data_string` for the custom module |
| Module value | The average Azure Monitor returns for one data point of the window |
| Module description | The data point timestamp followed by the description Azure Monitor gives the metric |
| Units, thresholds, module interval | None. Configure them in the console on the generated module |

The 16 modules fall into five groups:

- **Resource usage.** `cpu_percent`, `memory_percent` and `io_consumption_percent` report the processor, memory and disk I/O consumption of the server.
- **Storage.** `storage_percent`, `storage_used` and `storage_limit` report the data storage in use, and `backup_storage_used` the backup storage in use.
- **Server log storage.** `serverlog_storage_percent`, `serverlog_storage_usage` and `serverlog_storage_limit` report the server log storage.
- **Connections and network.** `active_connections` and `connections_failed` count connections, and `network_bytes_egress` and `network_bytes_ingress` report network traffic.
- **Replication.** `pg_replica_log_delay_in_seconds` and `pg_replica_log_delay_in_bytes` report the replication delay.

### One module entry per data point

The plugin emits one module entry for every data point that has a value in the window. When Azure Monitor returns more than one point for a metric, the document repeats that module name with a different value and a different timestamp in its description. The default window is one hour at a 60-minute interval; `--timespan` changes the window and the interval together.

Pandora FMS identifies a module by its name, so repeated names collapse into a single module and only one of those values is kept. Treat each module as "the latest average Azure Monitor returned", and read the time series in Azure Monitor when you need the evolution inside the window. A metric the resource reports as null produces no entry at all, so its module stays at its previous value.

### The custom metric module

With both `--metric` and `--name_module`, the plugin adds one `generic_data_string` module named `--name_module`, prefixed when `--prefix_module` is set. It contains one list entry per data point of that metric, with this fixed text:

```text
The Availity at <data point timestamp> is <average>
```

`Availity` is the literal spelling the plugin writes. The metric name in `--metric` is passed to Azure Monitor as given: it must exist for the resource, otherwise the run stops before generating any module. When no data point has a value, the module is generated with an empty list.

The custom module is additional: the 16 standard metrics are still collected on the same run. `--metric` alone, or `--name_module` alone, adds nothing.

## Operate and troubleshoot

- Every run performs one Azure Monitor query per metric: sixteen by default, plus one for the custom module. The queries are sequential and none is retried, and a rejected query stops the run before the agent data file is written, so a run either publishes the whole set or none of it.
- The window is `--timespan` hours with the interval derived from it: `1` hour at 60 minutes, `6` hours at 360, `12` hours at 720 and `24` hours at 1440. Any other value silently falls back to `1` hour. `--granularity` is accepted and has no effect: the interval always comes from `--timespan`.
- Each run publishes averages of a whole window rather than the latest instantaneous value, so running the plugin more often than the interval does not add resolution. Set the module interval to the window you want to follow.
- The plugin has no verbose or debug flag. The diagnostic channels are standard output, standard error and the exit status. A run that reaches delivery exits with status `0`, an invalid command line exits with status `2`, and a run that stops on an error exits with a non-zero status.

| Signal | Cause and check |
|--------|-----------------|
| `error: the following arguments are required: -c/--conf`, exit status `2` | The configuration file was not passed. The `--conf` flag is mandatory |
| A usage summary naming an invalid value, exit status `2` | A non-integer `--timespan` or `--as_agent_plugin`, or a flag left without a value |
| An error before any module is generated, and no data file | The configuration file lacks one of the four keys, or its credential or resource identifier cannot be read. Check the four keys and the `#` rule first |
| An authentication or authorization error from Azure, no module | Wrong tenant ID, application ID or secret, an expired secret, or an application without access to the resource. Test the credential outside Pandora FMS first |
| An error about one metric and no module at all | Azure Monitor rejected a metric name for that resource. Confirm that the resource exposes the 16 metric names listed in [Generated modules](#generated-modules) |
| `ERROR - Could not write file: ..., please check directory permissions` | `--data_dir` does not exist or is not writable, or two runs started within the same second and the second one collided with the first file name. Retry, and check the directory permissions |
| `Tentacle error` on standard error and `1` on standard output | The Tentacle transfer failed: `tentacle_client` is missing or unreachable, the port is wrong, or the Tentacle server requires a password. The data file stays in `--data_dir` |
| The plugin module value is module XML instead of `1` | `--as_agent_plugin 1` is in the registered parameters. Remove it |
| `1` printed but no agent in the console | The data file was written where the Data Server does not read it. Compare `--data_dir` with the server's incoming directory, and check that the plugin ran as a user with write permission on it |
| The agent exists with fewer modules than expected | Those metrics had no value in the window, or the resource does not report them. Remove null metrics from your expectations, not from the run |
| A metric module shows an older value between runs | The resource returned no value for the last runs, so the module kept its previous value. Confirm in Azure Monitor |
| The agent lands in the wrong group | The `--group` name is written as given and the group must exist in the console |

## Reference

### Command line

```bash
./pandora_azurepostgresql --conf <PATH_TO_CONFIG> [options]
```

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `-c`, `--conf` | Yes | — | Path to the credential and resource file |
| `--timespan` | No | `1` | Window in hours: `1`, `6`, `12` or `24`. Any other value is replaced by `1` |
| `--granularity` | No | Derived from `--timespan` | Accepted and ignored. The interval is always 60, 360, 720 or 1440 minutes, derived from `--timespan` |
| `--metric` | No | Empty | Azure Monitor metric name for the custom module. Only used together with `--name_module` |
| `--name_module` | No | Empty | Name of the custom module. Only used together with `--metric` |
| `--prefix_module` | No | Empty | Prefix joined to every module name with `_` |
| `--agent_name` | No | `Azure_Monitor_Postgresql` | Name of the agent written in the agent data file |
| `-g`, `--group` | No | `Azure` | Group written in the agent definition |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Directory where the agent data file is written |
| `--tentacle_address` | No | Empty | Tentacle server address. When set, the data file is sent with `tentacle_client` |
| `--tentacle_port` | No | `41121` | Tentacle server port |
| `--as_agent_plugin` | No | `0` | `1` prints the module XML on standard output; any other integer value writes the agent data file and prints `1` |
| `-h`, `--help` | No | — | Print the help and exit |

### Configuration file

```ini
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
serverpostgres_id:<POSTGRES_RESOURCE_ID>
```

| Key | Required | Description |
|-----|----------|-------------|
| `tenant_id` | Yes | Directory (tenant) ID of the Microsoft Entra application |
| `client_id` | Yes | Application (client) ID |
| `secret` | Yes | Client secret value |
| `serverpostgres_id` | Yes | Azure resource identifier of the PostgreSQL resource |

`key:value` lines, no colon inside a value, and any line containing `#` is ignored as a whole. Keys are matched by name anywhere in the line.

### Generated modules

The plugin requests these 16 metric names on every run. The module name is the metric name, or `<prefix>_<metric>` when `--prefix_module` is set, and the value is the average Azure Monitor returns for one data point:

| Metric | What it reports |
|--------|-----------------|
| `cpu_percent` | Processor consumption of the server |
| `memory_percent` | Memory consumption of the server |
| `io_consumption_percent` | Disk I/O consumption of the server |
| `storage_percent` | Data storage used, as a percentage of the limit |
| `storage_used` | Data storage used |
| `storage_limit` | Data storage limit |
| `serverlog_storage_percent` | Server log storage used, as a percentage of the limit |
| `serverlog_storage_usage` | Server log storage used |
| `serverlog_storage_limit` | Server log storage limit |
| `active_connections` | Active connections |
| `connections_failed` | Failed connections |
| `backup_storage_used` | Backup storage used |
| `network_bytes_egress` | Network traffic sent |
| `network_bytes_ingress` | Network traffic received |
| `pg_replica_log_delay_in_seconds` | Replication delay in seconds |
| `pg_replica_log_delay_in_bytes` | Replication delay in bytes |

The meaning of each value is the one Azure Monitor assigns to the metric name; the plugin forwards the average and adds no unit, so interpret the value with the metric name and configure the unit in the console.

With `--metric <METRIC> --name_module <NAME>` the run adds one `generic_data_string` module, named `--name_module` or `<prefix>_<name_module>`, whose list holds one entry per data point in the form `The Availity at <timestamp> is <average>`.

### Addon identity

| Property | Value |
|----------|-------|
| Marketplace identifier | `pandorafms.azure_postgresql` |
| Name | Azure PostgreSQL |
| Version | `1.0` |
| Marketplace last update | 2026-06-08 |
| Package | `pandorafms.azure_postgresql.1.0.zip` |
| Category | Miscelaneus |
| Tags | `applications`, `databases` |
| License | One; the download is limited to licensed users |
| Maintenance | The Marketplace record carries no maintenance or deprecation statement |
| Executable | `pandora_azurepostgresql` |
| Configuration file | `pandora_azurepostgresql.conf` |
