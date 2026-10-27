# Pandora Azure Storage monitoring plugin

*Article last updated: 2026-10-27.*

!!! warning "Discovery integration recommended"
    For new installations use [Azure Storage Discovery](../discovery/azure-storage.md), which is the recommended integration for this service. This plugin is the legacy path.

## What it does

The Pandora Azure Storage plugin reads the Azure Monitor metrics of one Azure
storage account, and of the account services you enable — Blob, File, Queue,
Table and Data Lake Storage — and publishes them as Pandora FMS modules,
grouped in one agent per service.

Every run works on the resource IDs written in a configuration file: the
storage account itself and each service you want to read. The plugin asks Azure
Monitor for the last hour of every metric and builds the modules from the
answer. There is no discovery step and no Azure resource enumeration: the
account and the services are the ones you write in that file.

The plugin has three execution paths:

- **No delivery option (default).** It prints one `<module>` XML block per
  module on standard output, for a Pandora FMS agent to collect.
- **`--as_agent_plugin 1`.** It builds one `agent_data` XML document per
  enabled service, writes each one into `data_dir` and prints `1`. Despite its
  name, this option produces the server-side run.
- **`--tentacle_address`.** It builds the same `agent_data` documents, delivers
  each one with the Tentacle client and prints `1`.

This page documents the **`pandorafms.azure_storage`** plugin, distributed as a
`.pspz2` package. Azure Storage **Discovery** is a different addon: it runs
from a Discovery task, enumerates the storage accounts of a subscription or of
one resource group, creates one agent per discovered account and needs no
configuration file. See [Azure Storage Discovery](../discovery/azure-storage.md).
The Discovery application also uses `pandorafms.azure_storage` as its short
name, so check the package type before installing: `.pspz2` is this plugin,
`.disco` is Discovery.

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.azure_storage`, version `1.0` | Documented target | Version of the Marketplace entry and of the distributed package. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions. It is a catalogue-wide statement covering this addon, not a test record for it |
| CentOS 7, Fedora and Rocky Linux as the host system | `Known compatible` | The previous edition of this guide records these systems as the ones where the plugin was tested; not re-validated for version `1.0` |
| Other host systems | `Not validated` | No other system is recorded for this addon |
| A Microsoft Entra app registration that can read the Azure Monitor metrics of the account | `Required` | Every collection call authenticates with its tenant ID, client ID and secret |
| The Azure resource ID of the storage account and of each service you enable | `Required` | Each value is queried directly as the metrics resource of that service |
| `tentacle_client` in `PATH` | `Required` when `--tentacle_address` is used | Delivery runs the Tentacle client |
| A writable `data_dir` | `Required` when the agent document is written | The XML document is created in that folder |
| Azure sovereign or custom clouds | `Not validated` | The addon exposes no endpoint option, so the Microsoft endpoints cannot be redirected |

The Marketplace entry does not state any maintenance or lifecycle status for
this addon.

### Requirements

1. **A Pandora FMS installation with the plugin server enabled**, to run the
   plugin, and the data server to ingest the `agent_data` documents when the
   run writes them.
2. **An Azure subscription with at least one storage account** to monitor.
3. **A Microsoft Entra app registration** for the plugin: its tenant ID, its
   client ID and a client secret.
4. **The Azure resource IDs** of the storage account and of each service you
   want to read, written in the configuration file.
5. **The Tentacle client (`tentacle_client`) available in `PATH`**, only when
   the run delivers through Tentacle.

### Prepare Azure access

Create an app registration in Microsoft Entra ID and note its **tenant ID**,
its **client ID** and a **client secret** value. These three values go to the
configuration file.

The plugin does not name the Azure role to assign. It only calls the Azure
Monitor metrics API for the resource IDs in the configuration, so the
registration needs permission to read the metrics of those resources. Assign
the narrowest role that grants that read on the storage account or on its
resource group.

Two further groups of values are needed:

- **The resource ID of the storage account**, the account scope the plugin
  queries for its account-level metrics. Its form is
  `/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>/providers/Microsoft.Storage/storageAccounts/<ACCOUNT>`.
- **The resource ID of each service** you enable — Blob, File, Queue, Table
  and Data Lake Storage. The previous edition of this guide obtains all of them
  from the account's own pages in the Azure portal.

The plugin sends each value exactly as written. A malformed identifier, or one
that the app registration cannot read, fails the run with the Azure exception;
a valid identifier that has no data for a metric only produces no module for
that metric. Copy the identifiers from Azure instead of typing them.

### Install the plugin

Upload the `.pspz2` package from the console plugin registration page. The
package registers the plugin with the definition described in
[Register the plugin in the console](#register-the-plugin-in-the-console),
including the three macros of the registration form.

The plugin reads a configuration file that you provide. The shipped value of
the first macro is
`/var/www/html/pandora_console/attachment/plugin/pandora_azure.conf`, so either
write the file there or change the macro to the path you use. The
[Configuration file](#configuration-file) section describes the content.

## Configure

### Configuration file

The file is plain text and uses `key:value` lines. Every value is trimmed.
Three rules decide what the plugin reads:

- A line that contains `#` anywhere is skipped, so comments start anywhere and
  a value that contains `#` is lost with its line.
- A line is split on `:`, and only the second fragment is kept: a value that
  contains `:` is truncated at the first colon.
- Keys are matched by substring, not as an exact key name: a line that contains
  a known key name is read as that key, a line that contains none is ignored,
  and a repeated key keeps the last value read.

This is the complete file shipped with the addon, with placeholders:

```ini
#credentials
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
#id resources
account_id:<ACCOUNT_RESOURCE_ID>
blobservice_id:<BLOB_SERVICE_RESOURCE_ID>
fileservice_id:<FILE_SERVICE_RESOURCE_ID>
queueservice_id:<QUEUE_SERVICE_RESOURCE_ID>
tableservice_id:<TABLE_SERVICE_RESOURCE_ID>
datalakestorage_id:<DATA_LAKE_SERVICE_RESOURCE_ID>
#active agents
account_agent:1
blobservice_agent:1
fileservice_agent:1
queueservice_agent:1
tableservice_agent:1
datalakestorage_agent:1
```

The three credential keys and the six `<service>_agent` switches are
mandatory: the plugin reads all of them before collecting anything, and a
missing one stops the run with a `NameError` traceback. Each `<service>_id` is
only needed when its switch is `1`. A switch holds `1` to enable the service
and `0` to leave it out; any other value stops the run with a `ValueError`.

To monitor only the account and Blob service, for example:

```ini
#credentials
tenant_id:<TENANT_ID>
client_id:<CLIENT_ID>
secret:<CLIENT_SECRET>
#id resources
account_id:<ACCOUNT_RESOURCE_ID>
blobservice_id:<BLOB_SERVICE_RESOURCE_ID>
#active agents
account_agent:1
blobservice_agent:1
fileservice_agent:0
queueservice_agent:0
tableservice_agent:0
datalakestorage_agent:0
```

An empty value is read as empty and fails at authentication time, not at
parse time. Keep the file readable only by the user that runs the plugin: it
holds the client secret in clear text.

### Execution modes and delivery

The plugin processes the enabled services in a fixed order, starting a new
list of modules for each one: account first, then Blob, Queue, File, Table and
Data Lake Storage. Each service delivers its own agent, so a run with all six
switches enabled delivers six agents.

Delivery is chosen per service, by these rules:

| Command line | What the run does |
| --- | --- |
| `--tentacle_address <TARGET_HOST>` | Writes the `agent_data` document of the service and sends it with `tentacle_client -v -a <TARGET_HOST> -p <port> <file>`. Prints `1` after each service |
| `--as_agent_plugin 1` without `--tentacle_address` | Writes the `agent_data` document of the service into `data_dir` and prints `1` |
| Neither option | Prints the modules of the service as `<module>` XML blocks on standard output, and writes no file |

The Tentacle path deletes the local document after a successful send, so the
`data_dir` folder holds nothing when the run succeeds. The plugin passes only
the address and the port to the Tentacle client; it has no option for a
Tentacle password.

`--tentacle_address` takes precedence over `--as_agent_plugin`, so a run can
write the document, deliver it and print `1` with both options present.

The Data Lake Storage service does not follow the same rule: with
`--as_agent_plugin 1` and no Tentacle address it prints its modules on
standard output instead of writing a document, and it only writes the document
when `--as_agent_plugin` is absent or different from `1`. See
[Limitations](#limitations).

### Credentials and transport

- The client secret is stored in the configuration file in clear text. Restrict
  the file permissions to the user that runs the plugin and keep the file out
  of shared directories and version control.
- The secret is not a command-line option, so it does not appear in the shell
  history or in the process list. It does appear in the configuration file that
  the console plugin command references.
- The addon exposes no endpoint option: authentication and metric queries go to
  the default Microsoft identity and management endpoints. There is no setting
  for a sovereign cloud, a custom endpoint or a proxy.

### Register the plugin in the console

The plugin can be registered in the Pandora FMS console as a server plugin, so
Pandora FMS executes it from the server that runs the modules instead of from a
command line. The registration definition of the `.pspz2` package sets these
values:

| Field | Value |
| --- | --- |
| Plugin name | `Pandora Azure Storage` |
| Description | `Take data from azure storage` |
| Plugin type | `Standard` (`plugin_type = 0`) |
| Maximum timeout | `20` seconds |
| Plugin command | The `pandora_azure` file of the package |
| Plugin parameters | `-c " _field1_ " --agent_name " _field2_ " -g " _field3_ "` |
| Modules provided | `0` (`total_modules_provided = 0`) |

The definition declares three macros. The format has no per-macro type, and
all three have `hide = 0`, so the console shows the three fields in clear
text:

| Macro | Required | Default | Hide | Description and help |
| --- | --- | --- | --- | --- |
| `_field1_` | Yes, according to its description | `/var/www/html/pandora_console/attachment/plugin/pandora_azure.conf` | No | `Conf path (obligatory)`. Help: `Path conf` |
| `_field2_` | No | `_agentname_` | No | `Agent name (optional)`. Help: `Name of the agent`. The default is the console macro replaced with the name of the agent that holds the module |
| `_field3_` | No | `azure` | No | `group (optional)`. Help: `Pandora FMS Target Group ` |

<!-- SCREENSHOT NEEDED: Plugin module form in the Pandora FMS console showing the three macro fields of Pandora Azure Storage, with a placeholder configuration path and no real credential. -->

The registered parameters do not include `--tentacle_address` or
`--as_agent_plugin`, so a module run started from this definition prints the
module XML on standard output. To make each run deliver its agents itself, add
the delivery option to **Plugin parameters**, for example:

```text
-c " _field1_ " --agent_name " _field2_ " -g " _field3_ " --tentacle_address 127.0.0.1
```

Each plugin field is a configuration value, not a service selection: the
services are enabled in the configuration file, so one registered plugin
serves every account whose file you reference. The maximum timeout of `20`
seconds is low for a run that queries every service; raise it if the run
reaches the timeout. See [Scheduling and runtime](#scheduling-and-runtime).

## Verify

Run the plugin manually from a terminal, passing the configuration file after
`-c`. In the default mode it prints the modules of every enabled service:

```bash
./pandora_azure -c <PATH_TO_CONFIG>
```

The run executes once and exits. A successful run prints `<module>` blocks and
nothing on standard error. The sample below shows the shape of the output for
the account service, with one data point per module:

```xml
<module>
	<name><![CDATA[UsedCapacity]]></name>
	<type>generic_data</type>
	<data><![CDATA[1099511627776.0]]></data>
	<description><![CDATA[2026-10-26 09:00:00+00:00 The amount of storage used by the storage account.]]></description>
	<unit><![CDATA[bytes]]></unit>
</module>
<module>
	<name><![CDATA[Transactions]]></name>
	<type>generic_data_string</type>
	<datalist>
	<data>
		<value><![CDATA[The Transactions at 2026-10-26 09:05:00+00:00 is 142.0]]></value>
	</data>
	<description><![CDATA[The number of requests made to a storage service or the specified API operation.]]></description>
</module>
```

The sample is built from the module definitions of the addon; it is not a
captured run, because the values depend on the account.

To check the server-side path, run it with `--as_agent_plugin 1` and a
throwaway data folder, then inspect the file:

```bash
mkdir -p /tmp/azure-storage-check
./pandora_azure -c <PATH_TO_CONFIG> --as_agent_plugin 1 --data_dir /tmp/azure-storage-check
ls /tmp/azure-storage-check
```

A successful run prints `1` once per enabled service, and the folder contains
one `<agent name>.<epoch seconds>.data` document per enabled service. The Data
Lake Storage service is the exception described in
[Limitations](#limitations). The file name uses the `--agent_name` value
followed by the service suffix, so the default names are
`Azure_Monitor.Azure_Storage_Account_Metrics.<epoch>.data` and
`Azure_Monitor.Blob_Service_Metrics.<epoch>.data`.

In Pandora FMS, after the first delivered run, the agents appear with their
modules. The account agent carries `UsedCapacity` and the six string modules;
each service agent carries its capacity modules and its own six string
modules. See [Understand the results](#understand-the-results).

## Understand the results

### Agents

A run creates one agent per enabled service, and the service suffix is appended
to the `--agent_name` value without a separator:

| Service switch | Agent name suffix | Default agent name |
| --- | --- | --- |
| `account_agent` | `Azure_Storage_Account_Metrics` | `Azure_Monitor.Azure_Storage_Account_Metrics` |
| `blobservice_agent` | `Blob_Service_Metrics` | `Azure_Monitor.Blob_Service_Metrics` |
| `queueservice_agent` | `Queue_Service_Metrics` | `Azure_Monitor.Queue_Service_Metrics` |
| `fileservice_agent` | `File_Service_Metrics` | `Azure_Monitor.File_Service_Metrics` |
| `tableservice_agent` | `Tables_Service_Metrics` | `Azure_Monitor.Tables_Service_Metrics` |
| `datalakestorage_agent` | `Datalake_Storage_Service_Metrics` | `Azure_Monitor.Datalake_Storage_Service_Metrics` |

The `agent_data` header sets `agent_mode` to `1` and takes the group from
`-g` (`Azure` when the option is absent), and the alias from the same value as
the name. The plugin does not set an agent interval: `interval` travels empty
in the header.

The File service agent carries the description `Blob Service Metrics`, the
same text as the Blob agent. See [Limitations](#limitations).

### Modules

Every service publishes two kinds of module:

- **Capacity and count modules** are `generic_data`. They carry the value
  returned for one metric, with the unit `bytes` when the metric is a size.
  They only appear when Azure returns data for that metric.
- **Rate and latency modules** are `generic_data_string` with a `datalist`.
  Each entry is the text `The <metric> at <timestamp> is <value>`, one per data
  point of the last hour, so a run normally writes about twelve entries. These
  modules are created even when Azure returns no data, in which case the
  datalist arrives empty.

The account-level set is `UsedCapacity`, `Transactions`, `Ingress`, `Egress`,
`SucessServerLatency`, `SuccessE2ELatency` and `Availity`. Each service
repeats the six rate, latency and availability modules with its own suffix,
for example `Transactions_blobs` or `Availity_tables`. The exhaustive list is
in [Agents and modules](#agents-and-modules).

The module names are the ones the addon publishes, including the spellings
`SucessServerLatency` and `Availity`. Alerts, reports and dashboards must use
those exact names.

A capacity module is created once per data point returned, and every entry has
the same name. A capacity query over one hour with a sixty-minute granularity
normally returns one or two points, so the same module name can appear twice in
one document. See [Limitations](#limitations).

## Operate and troubleshoot

### Scheduling and runtime

- The plugin keeps no state between runs: every execution queries Azure at that
  moment. The run can be repeated manually at any time.
- A run with all six services enabled makes 57 Azure Monitor requests, one per
  metric, one after another: 7 for the account, 10 for Blob, 9 for Queue, 12
  for File, 9 for Table and 10 for Data Lake Storage. The registration
  definition declares a maximum timeout of `20` seconds, which a full run can
  exceed; raise the timeout in the console or enable only the services you
  need.
- In server mode, schedule the plugin from Pandora FMS or from `cron`. The
  plugin does not set the agent interval itself: `interval` travels empty in the
  `agent_data` header.

### Limitations

- **No endpoint option.** Authentication and metric queries go to the default
  Microsoft endpoints, so a sovereign or custom cloud cannot be configured.
- **No proxy option, and the plugin does not retry.** A failed request ends the
  run with the exception that produced it; repeating the collection is up to
  the next scheduled run.
- **Data Lake delivery is inverted.** With `--as_agent_plugin 1` and no
  Tentacle address, the Data Lake Storage service prints its modules on
  standard output instead of writing its document, while the other five
  services write theirs. Use `--tentacle_address` to deliver all six on the
  server side.
- **The delivery option is named after the opposite mode.**
  `--as_agent_plugin 1` produces the server-side document; the default mode is
  the agent plugin one.
- **`--prefix_module` has no effect.** The option is accepted and ignored: it
  does not prefix module names, and the modules keep the names of
  [Agents and modules](#agents-and-modules).
- **One account per configuration file.** The file holds one set of resource
  IDs, so monitoring several accounts needs one file and one plugin run per
  account.
- **No secret protection.** The client secret is stored in clear text in the
  configuration file.
- **Capacity entries can repeat.** A metric that returns more than one data
  point produces several modules with the same name in the same document.
- **The File agent carries the Blob description.** Both agents report
  `Blob Service Metrics`.

### Troubleshooting

- **The run prints a traceback and exits with status 1** — an Azure call
  failed. The usual causes are a wrong or expired client secret, a wrong tenant
  or client ID, and a resource ID the identity cannot read. The traceback names
  the failing call.
- **The run stops with `NameError`** — a mandatory key is missing from the
  configuration file: one of `tenant_id`, `client_id`, `secret`, or one of the
  six `<service>_agent` switches. A line containing `#` is skipped as a
  comment, so a secret with `#` in it produces this error.
- **The run stops with `ValueError`** — a `<service>_agent` value is not an
  integer. Use `1` or `0`.
- **The run stops with `IndexError`** — a line contains a known key name but no
  `:` separator, so the plugin finds no value to read. Use `key:value`.
- **Authentication fails although the secret looks correct** — the value is
  truncated at the first `:` because the parser keeps only the second fragment
  of the line. A secret that contains `:` cannot be used from this file.
- **A service produces no capacity modules** — Azure returned no data for those
  metrics. Traffic, latency and availability modules still appear, with an
  empty datalist.
- **`Could not write file: ...`** — the `data_dir` folder does not exist or is
  not writable by the user that runs the plugin. The document is created with
  an exclusive name `<agent name>.<epoch seconds>.data`; a second run of the
  same service within the same second fails with this message.
- **`Tentacle error` on standard error with `1` on standard output** — the
  Tentacle delivery failed, and the run still prints `1` and exits with status
  0. Check that `tentacle_client` is in `PATH` and that the address and port
  reach the Tentacle server. The document stays in `data_dir` when the send
  fails.
- **No output at all** — every `<service>_agent` switch is `0`.

## Reference

### Command-line options

```bash
./pandora_azure -c <PATH_TO_CONFIG> [--agent_name <AGENT_NAME>] [-g <GROUP>]
    [--data_dir <PATH>] [--as_agent_plugin <0|1>]
    [--tentacle_address <TARGET_HOST>] [--tentacle_port <PORT>]
    [--prefix_module <PREFIX>]
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `-c`, `--conf` | Yes | — | Path to the configuration file. Without it the run stops with the usage message and exit status 2 |
| `--agent_name` | No | `Azure_Monitor.` | Prefix of the agent names. The service suffix is appended without a separator |
| `-g`, `--group` | No | `Azure` | Pandora FMS group assigned to the created agents |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Folder where the `agent_data` documents are written |
| `--as_agent_plugin` | No | `0` | `1` writes the documents into `data_dir` and prints `1`; any other value prints the modules on standard output. The Data Lake Storage service reverses this rule; see [Limitations](#limitations) |
| `--tentacle_address` | No | — | Tentacle server address. When set, each document is delivered with the Tentacle client |
| `--tentacle_port` | No | `41121` | Tentacle server port, passed to the client as `-p` |
| `--prefix_module` | No | — | Accepted and ignored. It does not prefix module names |
| `-h`, `--help` | No | — | Prints the option summary and exits |

### Configuration file keys

| Key | Required | Default | Description |
| --- | --- | --- | --- |
| `tenant_id` | Yes | — | Microsoft Entra tenant ID of the app registration |
| `client_id` | Yes | — | Client ID of the app registration |
| `secret` | Yes | — | Client secret value. Stored in clear text |
| `account_id` | When `account_agent` is `1` | — | Azure resource ID queried for the account-level metrics |
| `blobservice_id` | When `blobservice_agent` is `1` | — | Azure resource ID queried for the Blob service metrics |
| `fileservice_id` | When `fileservice_agent` is `1` | — | Azure resource ID queried for the File service metrics |
| `queueservice_id` | When `queueservice_agent` is `1` | — | Azure resource ID queried for the Queue service metrics |
| `tableservice_id` | When `tableservice_agent` is `1` | — | Azure resource ID queried for the Table service metrics |
| `datalakestorage_id` | When `datalakestorage_agent` is `1` | — | Azure resource ID queried for the Data Lake Storage metrics |
| `account_agent` | Yes | — | `1` collects the account metrics, `0` skips them |
| `blobservice_agent` | Yes | — | `1` collects the Blob service metrics, `0` skips them |
| `fileservice_agent` | Yes | — | `1` collects the File service metrics, `0` skips them |
| `queueservice_agent` | Yes | — | `1` collects the Queue service metrics, `0` skips them |
| `tableservice_agent` | Yes | — | `1` collects the Table service metrics, `0` skips them |
| `datalakestorage_agent` | Yes | — | `1` collects the Data Lake Storage metrics, `0` skips them |

Every value is trimmed, a repeated key keeps the last value read, and any line
that contains `#` is skipped.

### Agents and modules

The metric queries cover the last hour. Capacity metrics use a sixty-minute
granularity; the rate, latency and availability metrics use five minutes. All
of them request the `Average` aggregation.

#### Account agent

| Module | Type | Unit | Metric |
| --- | --- | --- | --- |
| `UsedCapacity` | `generic_data` | bytes | Storage used by the account |
| `Transactions` | `generic_data_string` | — | Requests made to the storage service or API operation, successful and failed |
| `Ingress` | `generic_data_string` | — | Ingress data, in bytes, from external clients and from within Azure |
| `Egress` | `generic_data_string` | — | Egress data, in bytes, to external clients and within Azure |
| `SucessServerLatency` | `generic_data_string` | — | Average time to process a successful request, without network latency |
| `SuccessE2ELatency` | `generic_data_string` | — | Average end-to-end latency of successful requests, in milliseconds |
| `Availity` | `generic_data_string` | — | Percentage of availability of the service or API operation |

#### Blob service agent

| Module | Type | Unit | Metric |
| --- | --- | --- | --- |
| `BlobCapacity` | `generic_data` | bytes | Capacity used by the Blob service |
| `BlobCount` | `generic_data` | — | Number of blobs |
| `ContainerCount` | `generic_data` | — | Number of containers |
| `IndexCapacity` | `generic_data` | bytes | Capacity used by the index |
| `Transactions_blobs` | `generic_data_string` | — | Requests, as in the account agent |
| `Ingress_blobs` | `generic_data_string` | — | Ingress data |
| `Egress_blobs` | `generic_data_string` | — | Egress data |
| `SucessServerLatency_blobs` | `generic_data_string` | — | Server latency |
| `SuccessE2ELatency_blobs` | `generic_data_string` | — | End-to-end latency |
| `Availity_blobs` | `generic_data_string` | — | Availability |

#### Queue service agent

| Module | Type | Unit | Metric |
| --- | --- | --- | --- |
| `QueueCapacity` | `generic_data` | bytes | Capacity used by the Queue service |
| `QueueCount` | `generic_data` | — | Number of queues |
| `QueueMessageCount` | `generic_data` | — | Number of messages |
| `Transactions_queues` | `generic_data_string` | — | Requests |
| `Ingress_queues` | `generic_data_string` | — | Ingress data |
| `Egress_queues` | `generic_data_string` | — | Egress data |
| `SucessServerLatency_queues` | `generic_data_string` | — | Server latency |
| `SuccessE2ELatency_queues` | `generic_data_string` | — | End-to-end latency |
| `Availity_queues` | `generic_data_string` | — | Availability |

#### File service agent

| Module | Type | Unit | Metric |
| --- | --- | --- | --- |
| `FileCapacity` | `generic_data` | bytes | Capacity used by the File service |
| `FileCount` | `generic_data` | — | Number of files |
| `FileShareCount` | `generic_data` | — | Number of file shares |
| `FileShareSnapshotCount` | `generic_data` | — | Number of share snapshots |
| `FileShareSnapshotSize` | `generic_data` | bytes | Size of the share snapshots |
| `FileShareCapacityQuota` | `generic_data` | bytes | Quota of the file shares |
| `Transactions_files` | `generic_data_string` | — | Requests |
| `Ingress_files` | `generic_data_string` | — | Ingress data |
| `Egress_files` | `generic_data_string` | — | Egress data |
| `SucessServerLatency_files` | `generic_data_string` | — | Server latency |
| `SuccessE2ELatency_files` | `generic_data_string` | — | End-to-end latency |
| `Availity_files` | `generic_data_string` | — | Availability |

#### Table service agent

| Module | Type | Unit | Metric |
| --- | --- | --- | --- |
| `TableCapacity` | `generic_data` | bytes | Capacity used by the Table service |
| `TableCount` | `generic_data` | — | Number of tables |
| `TableEntityCount` | `generic_data` | — | Number of entities |
| `Transactions_tables` | `generic_data_string` | — | Requests |
| `Ingress_tables` | `generic_data_string` | — | Ingress data |
| `Egress_tables` | `generic_data_string` | — | Egress data |
| `SucessServerLatency_tables` | `generic_data_string` | — | Server latency |
| `SuccessE2ELatency_tables` | `generic_data_string` | — | End-to-end latency |
| `Availity_tables` | `generic_data_string` | — | Availability |

#### Data Lake Storage agent

| Module | Type | Unit | Metric |
| --- | --- | --- | --- |
| `BlobCapacity` | `generic_data` | bytes | Capacity used by the Data Lake Storage service |
| `BlobCount` | `generic_data` | — | Number of blobs |
| `ContainerCount` | `generic_data` | — | Number of containers |
| `IndexCapacity` | `generic_data` | — | Capacity used by the index. This module carries no unit, unlike the Blob one |
| `Transactions_datalake` | `generic_data_string` | — | Requests |
| `Ingress_datalake` | `generic_data_string` | — | Ingress data |
| `Egress_datalake` | `generic_data_string` | — | Egress data |
| `SucessServerLatency_datalake` | `generic_data_string` | — | Server latency |
| `SuccessE2ELatency_datalake` | `generic_data_string` | — | End-to-end latency |
| `Availity_datalake` | `generic_data_string` | — | Availability |

### Addon identity

| Field | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.azure_storage` |
| Marketplace name | Pandora Azure Storage |
| Addon version | `1.0` |
| Marketplace last update | 2026-02-25 |
| Marketplace package | `pandorafms.azure_storage.1.0.pspz2` |
| License | One |
| Availability | Download limited to licensed users |
| Marketplace type | Miscelaneus |
| Workflow | Server or agent plugin: Azure Monitor metrics for one storage account |
| Executable | `pandora_azure` |

[https://marketplace.pandorafms.com/entries/pandorafms.azure_storage](https://marketplace.pandorafms.com/entries/pandorafms.azure_storage)

<!-- SCREENSHOT NEEDED: The account and service agents of Pandora Azure Storage in the Pandora FMS console, with their module lists and no tenant, subscription or account identifiers visible. -->
