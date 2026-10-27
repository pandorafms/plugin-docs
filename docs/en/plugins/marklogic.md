# MarkLogic monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The plugin monitors a MarkLogic installation from Pandora FMS. Each run reads the
MarkLogic management REST API, takes the inventory of the installation — hosts,
databases, forests and application servers — and builds one Pandora FMS agent per
entity, holding the modules that describe its state, load and replication.

Nothing is installed on the MarkLogic nodes: the plugin runs on one host, connects
over HTTP or HTTPS and delivers the generated agents to Pandora FMS. Every
execution reads the whole inventory again, so the plugin keeps no state between
runs and the agents always reflect the installation at the moment of the run.

Three groups of settings shape a run:

- **What it collects.** Each entity type (hosts, databases, forests, application
  servers) is enabled or disabled independently, individual entities can be
  excluded by name, and each type produces either a summary set of modules or a
  detailed set.
- **How it is identified.** A common prefix names every generated agent, and the
  agents land in a configured group with a configured interval.
- **Where it delivers.** The generated agent documents travel with Tentacle or are
  copied into a local Pandora FMS data folder.

The entity agents are always delivered that way. The `as_agent_plugin` setting only
selects what the plugin prints on standard output: enabled, it prints a
`Plugin message` module for a Pandora FMS agent to collect; disabled, it prints the
run result as a number for a server plugin module or a scheduled job.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| MarkLogic management REST API reachable on the configured host and port | `Required` | Every collection reads `/manage/<api-version>/...` with `format=json` from that host and port |
| An `ml_api_version` value the installation accepts: `V1`, `V2` or `LATEST` | `Required` | The value is a path segment of every request; the shipped configuration file documents these three values |
| A MarkLogic user allowed to read the management API | `Required` | The plugin authenticates with `ml_user`, `ml_pass` and `ml_realm` |
| A Perl runtime providing `LWP::UserAgent`, `JSON`, `IO::Socket::INET6` and `PerlIO::encoding` | `Required` | The plugin does not start without them |
| Network access from the plugin host to `ml_server:ml_port` | `Required` | The plugin connects to the management API from that host |
| Network access from the plugin host to each application server port, when port checks are enabled | `Required` | The port check opens a TCP connection for each application server |
| Network access to the Pandora FMS Tentacle port, `41121` by default, when delivering with Tentacle | `Required` | Tentacle delivery is the default mode |
| MarkLogic server version | `Not validated` | No MarkLogic version matrix has been recorded for this addon; the shipped file documents `LATEST` as the MarkLogic 8 API version |
| Operating system of the host that runs the plugin | `Not validated` | No operating system has been recorded for this version |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its entries are compatible with Pandora FMS NG 784 and later versions; it is a catalogue-wide statement covering this addon, not a test record |

### Requirements

1. **A MarkLogic installation** whose management API answers on the configured
   host and port. The plugin and its shipped configuration file use `8002`.
2. **A MarkLogic account** that can read the management API at
   `/manage/<api-version>/`.
3. **A host to run the plugin** with the Perl runtime and the modules listed in
   [Compatibility](#compatibility).
4. **A destination for the generated agents**: the Pandora FMS Tentacle service,
   or a local data folder that the Pandora FMS server reads.
5. **Optionally**, TCP reachability from the plugin host to each application
   server port, only when the port check is enabled.

### Install the plugin

Download the addon from the Pandora FMS Marketplace entry, which is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.marklogic_monitoring](https://marketplace.pandorafms.com/entries/pandorafms.marklogic_monitoring)

Install it on the host that will run it, keeping the configuration file
`pandora_ml.conf` next to it. The plugin takes that file as its only argument, so
any location is valid as long as the execution uses the same path.

## Configure

The plugin takes one argument, the path of its configuration file, and no
command-line options:

```bash
perl /usr/share/pandora_server/util/pandora_marklogic.pl <PATH_TO_CONFIG>
```

The file holds `key = value` lines, and the values in it override the built-in
defaults. Two parsing rules apply:

- A line whose first character is `#` is a comment. A line that starts with spaces
  is read as a key, so keep comments in the first column.
- Keys and values are trimmed, and the value keeps any `=` after the first one. A
  repeated key keeps its last value; `global_alerts` is the exception, described in
  [Module decoration](#module-decoration).

The shipped `pandora_ml.conf` is a working base: it enables every entity type,
selects summary detail for hosts, databases and forests and detailed information
for application servers. Start from it rather than from an empty file. The
`check_*` and `show_detailed_*` keys have no built-in value — a key missing from the
file behaves as disabled, so an incomplete file collects nothing while still
reporting a successful run.

### Connection to MarkLogic

This block is mandatory; without it the plugin has no API to read.

```ini
ml_server = <MARKLOGIC_HOST>
ml_port = 8002
ml_user = <USERNAME>
ml_pass = <PASSWORD>
ml_realm = public
use_ssl = 0
ml_api_version = LATEST
```

- `ml_server` and `ml_port` build every request URL. The plugin uses exactly the
  port given: there is no fallback to the default port of the scheme.
- `use_ssl` switches the scheme from `http` to `https`. Enable it when the
  management API is served over TLS.
- `ml_api_version` is inserted as a path segment, so `LATEST` reads
  `/manage/LATEST/hosts`, and `V1` or `V2` read the corresponding API version.
  `LATEST` is used when the key is absent.
- `ml_realm` is the authentication realm sent with the credentials. If the server
  challenges with a different realm, authentication fails.

### Delivery to Pandora FMS

The generated agent documents leave the plugin in one of two ways. Tentacle is the
default and requires the Tentacle address:

```ini
mode = tentacle
tentacle_ip = <PANDORA_FMS_URL>
tentacle_port = 41121
tentacle_opts =
tentacle_client = /usr/bin/tentacle_client
```

The local copy writes the documents into a folder that the Pandora FMS server
reads, which is the usual choice when the plugin runs on the Pandora FMS server
itself:

```ini
mode = local
local_folder = /var/spool/pandora/data_in
```

- `mode` is Tentacle only when its value is exactly `tentacle`. Any other value,
  including an empty one, copies the documents into `local_folder`.
- `tentacle_ip` is required when delivering with Tentacle. `tentacle_client` must
  name an executable: an empty value does not fall back to `tentacle_client` in the
  `PATH`, and the delivery fails.
- `tentacle_opts` passes extra options to the Tentacle client, separated by spaces.
- `temp` is where each document is written before delivery, `/tmp` by default.
- **`temp` and `local_folder` must both exist**, even when the plugin delivers with
  Tentacle and never copies anything. A missing directory stops the run before it
  collects any data.

### What it collects

Each entity type is collected only when its key is enabled. The shipped file
enables all four and the port check:

```ini
check_hosts = 1
check_databases = 1
check_forests = 1
check_servers = 1
check_server_ports = 1
```

Boolean keys are numeric: a value greater than `0` enables the feature; `0`, an
empty value or a non-numeric value disables it.

The port check monitors the port of each application server and is part of the
server collection, so it is only generated while `check_servers` is enabled.

To leave entities out, list their exact names, comma separated, in the exclusion
key of their type. Names are matched as MarkLogic reports them:

```ini
exlude_hosts =
exlude_databases = Documents,Modules
exlude_forests =
exlude_servers = Manage
```

The keys are spelled `exlude_*`, without the `c`: the correctly spelled
`exclude_*` is read as an unknown key and excludes nothing.

The detail level adds modules to each entity type:

```ini
show_detailed_hosts = 0
show_detailed_databases = 0
show_detailed_forests = 0
show_detailed_servers = 1
```

A type at `0` produces the summary set described in
[Understand the results](#understand-the-results); at `1` it produces every field
the API reports for the entity.

### Agent identity

Every generated agent uses the same header, name scheme, group and interval:

```ini
agent_name_header = ML_
agent_group = MarkLogic
agent_interval = 300
```

The header is the only free part of the name; the rest is fixed by the entity type
and the name MarkLogic reports, as described in
[Generated agents](#generated-agents). Use a distinctive header, such as `ML_`, so
the agents of several installations stay apart.

`show_server_type_in_agentname` (enabled in the shipped file) appends the
application server type to those agent names:

```ini
show_server_type_in_agentname = 1
```

Turning it on or off renames every application server agent. The agents created
under the previous name stop receiving data and new agents appear, so decide it
before the first run.

`agent_group` is the group the agents are created in, by name, and `agent_interval`
is their interval in seconds. Both apply to every generated agent.

### Module decoration

These settings apply to the generated modules:

```ini
#module_header = Custom_header_
#warning_instructions = Some text to guide the team
#critical_instructions = Some text to guide the team
#global_alerts = critical condition
```

- `module_header` prefixes every module name of every entity.
- `warning_instructions`, `critical_instructions` and `unknown_instructions` add the
  corresponding instruction text to every module.
- `global_alerts` attaches an alert template to every module. Repeat the key once
  per template; the value is the alert template name.

### Create the agent group

The plugin can create the agent group through the Pandora FMS console API before
delivering the agents:

```ini
autocreate_group = 0
api_url = http://<PANDORA_FMS_URL>/pandora_console/include/api.php
api_user = <USERNAME>
api_user_pass = <PASSWORD>
api_pass = <PASSWORD>
group_icon = Servers
```

`api_url`, `api_user`, `api_user_pass` and `api_pass` are used only for this
creation; `group_icon` is the icon the new group receives. Set
`autocreate_group = 1` only when the group does not exist yet:

> Do not enable group creation when the Pandora FMS installation is part of a
> metaconsole environment. Creating groups on a node with an active metaconsole can
> break the group synchronisation of the whole set of nodes.

### Run it from Pandora FMS

The plugin is a command, so Pandora FMS runs it the same way a person does: with the
path of the configuration file. Two integration paths are available, and they can
coexist:

- **As a plugin module of an agent.** The Pandora FMS agent runs the command every
  interval and collects the `Plugin message` module the plugin prints. Enable
  `as_agent_plugin = 1` in the file for this path.
- **As a server plugin module or a scheduled job.** Keep
  `as_agent_plugin = 0`: the plugin prints the result as a number and writes the
  diagnostics to standard error, which is what a server plugin module records.
  Scheduling it from the system `cron` is described in
  [Operate and troubleshoot](#operate-and-troubleshoot).

<!-- SCREENSHOT NEEDED: Pandora FMS module definition screen for the plugin module or server plugin module that runs pandora_marklogic.pl, showing where the command and the configuration file path are entered. -->

The first path needs a Pandora FMS agent on the host that runs the plugin; the
second does not and is the usual choice when the plugin already runs on the Pandora
FMS server. Neither path installs anything on the MarkLogic nodes.

## Verify

Run the plugin with no argument to confirm that the runtime is complete. It prints
its usage summary and stops:

```bash
perl /usr/share/pandora_server/util/pandora_marklogic.pl
```

```text
Pandora FMS Plugin for MarkLogic NoSQL Monitoring <version>

At least one parameter is needed by this plugin:
Usage: pandora_marklogic.pl pandora_ml.conf
```

Then run it with the configuration file:

```bash
perl /usr/share/pandora_server/util/pandora_marklogic.pl <PATH_TO_CONFIG>
```

With `as_agent_plugin = 1` a successful run prints one `Plugin message` module on
standard output:

```xml
<module>
	<name><![CDATA[Plugin message]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[Execution OK]]></description>
</module>
```

With `as_agent_plugin = 0` it prints `1` on standard output and the same message on
standard error:

```text
Plugin execution Result:[Execution OK]
```

A run that cannot read everything prints `0` instead of `1` and lists the failed
requests in the description of the `Plugin message` module, or after
`Plugin execution Result:` on standard error. For example:

```text
Plugin execution Result:[ No response from http://<MARKLOGIC_HOST>:8002/manage/LATEST/hosts?format=json
  No response from http://<MARKLOGIC_HOST>:8002/manage/LATEST/databases?format=json
 ]
```

Finally, confirm that the agents arrived. The plugin deletes each temporary document
only when its delivery succeeds, so a document left in `temp` is a failed delivery.
In Pandora FMS, the generated agents appear with the configured header, and each one
carries the modules described in [Understand the results](#understand-the-results).

<!-- SCREENSHOT NEEDED: Pandora FMS agent list after a first run, filtered by the configured agent name header, showing the generated host, database, forest and application server agents. -->

A run that reports `Execution OK` does not prove that every entity was collected: an
empty inventory produces no error. Compare the number of agents with the inventory
of the installation.

## Understand the results

The plugin creates one agent per entity, in four families, plus a status module when
it runs as an agent plugin. The families are independent: a type that is disabled,
excluded or unreadable simply produces no agent.

- **Hosts** report whether the node is online, whether its status view includes a
  critical issue, and its rate and load. These agents have no parent.
- **Databases** report availability, capacity, replication lag and, in summary mode,
  size and indexing or rebalancing state.
- **Forests** report whether the forest is open and enabled, its load, and its
  replication lag. Each forest agent is parented to the database that contains it,
  when databases are collected.
- **Application servers** report whether the service is open and enabled, its
  detailed state, and whether its port accepts connections.

State modules are `generic_proc` or `async_proc` modules: `1` is a normal state,
`0` is a failure, and a value the plugin cannot map is reported as `3` with the
original state in the module description. A database that reports no state at all
gets `2`. Numeric modules carry the unit the API reports, so rates, loads and sizes
keep their MarkLogic meaning. Summary mode keeps the modules that answer "is it
healthy and how loaded is it"; detailed mode adds the fields of the entity and drops
the summary-only modules, which is why it produces many more modules.

`Plugin message` summarises the run, not the installation: `1` means every request
the plugin attempted returned data, `0` means at least one request failed or a
delivery could not be completed.

## Operate and troubleshoot

### Scheduled execution

The plugin has no internal scheduler, so an external one runs it. A system `cron`
entry on the host, for example:

```cron
*/5 * * * * root perl /usr/share/pandora_server/util/pandora_marklogic.pl <PATH_TO_CONFIG>
```

Match the schedule to the agent interval you configured, so the agents receive data
at the rate the console expects.

### Log

The plugin writes a log file, `pandora_ml.log` in the working directory by default.
Set `log` to an absolute path to place it elsewhere. Each run starts a new log, and a
previous log larger than 3,200,000 bytes is renamed to `.old` before the new one
starts. Every line carries a timestamp and the `execution_id` value, `MarkLogic`
when the key is empty, which helps to tell concurrent executions apart.

### Timeout

`timeout` bounds the whole run, not one request: when it expires the plugin stops
with `Exceeded execution time` on standard error and a non-zero exit status, before
delivering anything. The value is in seconds. The shipped file sets `2`, which is
short for an installation with many entities; raise it when runs are cut off. When
the key is absent the plugin uses `60`.

### Debugging a run

`extra_log = 1` writes the raw JSON answer of each database and forest to the log, in
addition to the normal messages, while that type is in summary mode. Use it to check
what the API returns for an entity that produces unexpected modules, and disable it
afterwards: the output is large.

### Known limitations of this version

- **Application server agents are delivered only while forests are collected.** With
  `check_forests = 0` and `check_servers = 1` the servers are read but their agents
  are never delivered.
- **`module_interval`, `module_tags` and `module_group` have no effect.** They are
  accepted and ignored, so the generated modules carry no tags and no module group,
  and the module interval is not set by the plugin.
- **`status min-capacity` carries the unit string as its value.** The module reports
  the unit returned by the API instead of the numeric capacity, so its value is not a
  measurement.
- **The exclusion keys are spelled `exlude_*`.** The correctly spelled `exclude_*`
  keys exclude nothing.
- **An empty `tentacle_client` does not fall back to the `PATH`.**
- **There is no cluster agent.** The installation itself has no agent, and
  application server agents have no parent; only forests are parented, to their
  database.
- **Detailed mode names modules after the API field.** When the same field name
  appears in more than one section of an entity, the modules repeat the name, and
  fields with an `enum` or `quantity` unit produce no module at all.

### Troubleshooting

- **`Error: Cannot found temporal directory` followed by the usage text** — the
  configuration file could not be read, or `temp` does not exist. The plugin reports
  the missing temporary directory because it falls back to its defaults when the file
  cannot be opened, so check the path first, then the directory.
- **`Error: Cannot found target directory ...`** — `local_folder` does not exist. The
  directory is required even when the plugin delivers with Tentacle.
- **`Plugin message` reports `0` with `No response from <url>`** — that management
  API request failed. Check `ml_server`, `ml_port`, `use_ssl`, the credentials and
  `ml_realm`. A wrong port or a disabled management API fails every request of the
  run.
- **Only one entity type reports `No response`** — its endpoint is unavailable or
  refused for that path, for example `/forests` behind a restricted account. The
  other types still produce agents.
- **`Plugin message` reports `0` with `Failed to retrieve the group id for <server>`**
  — the group relation of an application server could not be read. Its modules are
  still generated.
- **`Plugin message` reports `0` with `There was a problem sending file using
  tentacle`** — Tentacle delivery failed. Check `tentacle_ip`, `tentacle_port`,
  `tentacle_client` and the network path to the Pandora FMS server. The document
  stays in `temp`.
- **`Plugin message` reports `0` with `There was a problem copying local file`** —
  `local_folder` is not writable by the user that runs the plugin.
- **`Exceeded execution time`** — the run exceeded `timeout`. Raise it, or reduce the
  collected scope.
- **No modules on an entity that exists** — its type is disabled, its name is in the
  exclusion list, or the run finished before reaching it. Enable the type, check the
  exclusion value and the log.
- **Fewer modules than expected on one entity** — it is in summary mode. Enable the
  corresponding `show_detailed_*` key.
- **The agents stopped receiving data after a naming change** — the name of the agent
  changed, so the old agent is orphaned. Check `agent_name_header` and
  `show_server_type_in_agentname`, and remove the agents left behind.

## Reference

### Configuration file

The file is passed as the only argument and holds `key = value` lines. Values in the
file override the built-in defaults shown below.

| Key | Required | Default | Description |
| --- | --- | --- | --- |
| `ml_server` | Yes | Empty | MarkLogic host that serves the management API |
| `ml_port` | No | `8002` | Port of the management API |
| `ml_user` | Yes | Empty | MarkLogic user allowed to read the management API |
| `ml_pass` | Yes | Empty | Password of `ml_user` |
| `ml_realm` | No | `public` | Authentication realm sent with the credentials |
| `use_ssl` | No | Not set (`0` in the shipped file, HTTP) | A value greater than `0` queries `https://<ml_server>:<ml_port>`; any other value queries `http://` |
| `ml_api_version` | No | `LATEST` | API version used as a path segment: `V1`, `V2` or `LATEST` |
| `timeout` | No | `60` (`2` in the shipped file) | Seconds the whole run may take |
| `log` | No | `pandora_ml.log` | Log file path |
| `execution_id` | No | `MarkLogic` | Text added to every log line; empty uses `MarkLogic` |
| `temp` | No | `/tmp` | Directory where each document is written before delivery; must exist |
| `mode` | No | `tentacle` | `tentacle` delivers with the Tentacle client; any other value copies into `local_folder` |
| `tentacle_ip` | Yes when `mode=tentacle` | Empty | Tentacle server address |
| `tentacle_port` | No | `41121` | Tentacle server port |
| `tentacle_opts` | No | Empty | Extra options for the Tentacle client, separated by spaces |
| `tentacle_client` | No | `/usr/bin/tentacle_client` | Tentacle client executable; an empty value breaks the delivery |
| `local_folder` | No | `/var/spool/pandora/data_in` | Local destination for the documents; must exist even with Tentacle |
| `as_agent_plugin` | No | `0` | `1` prints a `Plugin message` module on standard output; any other value prints the run result as a number |
| `agent_name_header` | No | Empty | Prefix of every generated agent name |
| `agent_group` | No | `MarkLogic` | Group of the generated agents, by name |
| `agent_interval` | No | `300` | Interval of the generated agents, in seconds |
| `show_server_type_in_agentname` | No | Not set (disabled) | `1` appends the application server type to its agent name |
| `check_hosts` | No | Not set (disabled) | `1` collects hosts; the shipped file sets `1` |
| `check_databases` | No | Not set (disabled) | `1` collects databases; the shipped file sets `1` |
| `check_forests` | No | Not set (disabled) | `1` collects forests and delivers the application server agents; the shipped file sets `1` |
| `check_servers` | No | Not set (disabled) | `1` collects application servers; the shipped file sets `1` |
| `check_server_ports` | No | Not set (disabled) | `1` adds the port check to each application server agent; the shipped file sets `1` |
| `show_detailed_hosts` | No | Not set (summary) | `1` generates every field of each host |
| `show_detailed_databases` | No | Not set (summary) | `1` generates every field of each database |
| `show_detailed_forests` | No | Not set (summary) | `1` generates every field of each forest |
| `show_detailed_servers` | No | Not set (summary) | `1` generates every field of each application server; the shipped file sets `1` |
| `exlude_hosts` | No | Empty | Host names to skip, comma separated |
| `exlude_databases` | No | Empty | Database names to skip, comma separated |
| `exlude_forests` | No | Empty | Forest names to skip, comma separated |
| `exlude_servers` | No | Empty | Application server names to skip, comma separated |
| `autocreate_group` | No | `0` | `1` creates `agent_group` through the console API before delivering |
| `api_url` | Only for group creation | Empty | Console API URL, ending in `/include/api.php` |
| `api_user` | Only for group creation | `admin` | Console user |
| `api_user_pass` | Only for group creation | `pandora` | Password of the console user |
| `api_pass` | Only for group creation | `1234` | API password |
| `group_icon` | No | Not set (`Servers` in the shipped file) | Icon of the created group |
| `module_header` | No | Empty | Prefix of every module name |
| `warning_instructions`, `critical_instructions`, `unknown_instructions` | No | Empty | Instruction text added to every module |
| `global_alerts` | No | Empty | Alert template attached to every module; repeat the key per template |
| `extra_log` | No | Not set (disabled) | `1` writes the raw JSON of each database and forest to the log |
| `module_interval` | No | — | Accepted and ignored in this version |
| `module_tags` | No | — | Accepted and ignored in this version |
| `module_group` | No | — | Accepted and ignored in this version |

### Command-line execution

```bash
perl pandora_marklogic.pl <PATH_TO_CONFIG>
```

| Condition | Behavior |
| --- | --- |
| No argument | Prints the usage summary and exits with status 1 |
| One argument that names a readable file | Runs with that configuration |
| One argument that names a file that cannot be opened | Reports the missing temporary directory, prints the usage summary and exits with status 1, because the defaults replace the unreadable file |
| More than one argument | Only the first argument is read; the rest are ignored |
| `temp` or `local_folder` does not exist | Reports the missing directory, prints the usage summary and exits with status 1 |
| The run completes | Exits with status 0, whether or not a request failed; the result is in the output |
| `timeout` expires | Stops with `Exceeded execution time` on standard error and a non-zero status |

### Generated agents

`<header>` is the `agent_name_header` value and `<name>` is the entity name as
MarkLogic reports it.

| Entity | Agent name | Parent | Modules |
| --- | --- | --- | --- |
| Host | `<header>H_<name>` | None | [Host modules](#host-modules) |
| Database | `<header>DB_<name>` | None | [Database modules](#database-modules) |
| Forest | `<header>F_<name>` | The `<header>DB_<database>` agent of the database that contains it, when databases are collected | [Forest modules](#forest-modules) |
| Application server | `<header>S_<name>`, or `<header>S_<name> [<type>]` with `show_server_type_in_agentname` | None | [Application server modules](#application-server-modules) |

Every agent is created with the operating system `MarkLogic`, no address, the
configured group and interval, and a timestamp of the run. The installation itself
has no agent.

### Generated modules

Module names below are the names the plugin writes; `module_header` is prepended to
each one. A field the API omits does not remove the module: it is written with an
empty value. Only the `enum` and `quantity` fields of detailed mode produce no module
at all.

#### Host modules

| Module | Type | When | Meaning |
| --- | --- | --- | --- |
| `error` | `generic_proc` | Always | `1` when the status view reports no critical issue, `0` when it reports one; the description carries the reported message |
| `online` | `generic_proc` | Always | `1` while the host is online |
| `total-rate` | `generic_data` | Always | Total rate with the unit the API reports |
| `total-load` | `generic_data` | Always | Total load with its unit |
| `deadlock-wait-load` | `generic_data` | Summary mode | Deadlock wait load with its unit |
| `journal-write-rate` | `generic_data` | Summary mode | Journal write rate with its unit; the description repeats the value |
| `secure` | `generic_proc` | Detailed mode | `1` when the host reports a secure state |
| One module per detail field | `generic_data`, `generic_data_string` or a `0`/`1` `generic_data` | Detailed mode | The field name; boolean fields are described as `0 => false, 1 => true` |

Detailed mode covers the `load-detail`, `rate-detail` and `status-detail` sections of
the host status view.

#### Database modules

| Module | Type | When | Meaning |
| --- | --- | --- | --- |
| `state` | `async_proc` | Always | `1` available, `0` unavailable, `2` when the API reports no state, `3` any other state; the description reads `State [<value>]` |
| `status min-capacity` | `generic_data` | When reported | Default `max_warning` `30` and `max_critical` `10`; the value is the unit string, see [Known limitations](#known-limitations-of-this-version) |
| `foreign-forests-lag-exceeded` | `generic_data` | When reported | Default `min_warning` `15`, `max_warning` `20` and `min_critical` `21` |
| `replication_pending-lag (<n>)` | `generic_data` | Per foreign replica | Pending lag; default `min_warning` `10` and `min_critical` `15` |
| `replication journal-archive pending-lag (<n>)` | `generic_data` | Per journal archive | Pending lag; same defaults |
| `total-rate`, `total-load` | `generic_data` | Summary mode | Rate and load with their units |
| `forest-count` | `generic_data` | Summary mode | Number of forests of the database |
| `indexing-state`, `rebalancing-state`, `local-disk-failover` | `generic_data` | Summary mode | `0`/`1` flags, described as `0 => false, 1 => true` |
| `device-space`, `data-size` | `generic_data` | Summary mode | Space with the unit the API reports |
| One module per detail field | `generic_data`, `generic_data_string` or a `0`/`1` `generic_data` | Detailed mode | The field name, for every section of the database status view except `state` |

`<n>` numbers the entries of the list from `0`.

#### Forest modules

| Module | Type | When | Meaning |
| --- | --- | --- | --- |
| `state` | `generic_proc` | Always | `1` open, available or sync replicating; `0` closed or unavailable; `3` an unrecognised state, with the reported value in the description |
| `replication_pending-lag (<n>)` | `generic_data` | Per foreign replica | Pending lag; default `min_warning` `10` and `min_critical` `15` |
| `replication journal-archive pending-lag (<n>)` | `generic_data` | Per journal archive | Pending lag; same defaults |
| `enabled` | `generic_proc` | Summary mode | `1` when the forest is enabled |
| `rebalancing-state`, `local-disk-failover` | `generic_data` | Summary mode | `0`/`1` flags |
| `total-rate`, `total-load`, `query-read-load`, `save-write-load` | `generic_data` | Summary mode | Value with its unit, `sec/sec` when the API omits it |
| One module per detail field | `generic_data`, `generic_data_string` or a `0`/`1` `generic_data` | Detailed mode | The field name, for every section of the forest status view except `state` |

#### Application server modules

| Module | Type | When | Meaning |
| --- | --- | --- | --- |
| `state` | `generic_proc` | Always | `1` open, `0` closed, `3` an unrecognised state |
| `port status` | `generic_proc` | `check_server_ports` and `check_servers` | `1` when a TCP connection to `ml_server` on the port of the application server succeeds; the description reads `Port <port>` |
| `enabled` | `generic_proc` | Summary mode | `1` when the server is enabled |
| One module per detail field | `generic_data`, `generic_data_string` or a `0`/`1` `generic_data` | Detailed mode | The field name, for every section of the server status view except `state` |

The port check always connects to `ml_server`, not to the host that runs the
application server.

#### Global module

| Module | Type | When | Meaning |
| --- | --- | --- | --- |
| `Plugin message` | `generic_proc` | `as_agent_plugin` enabled | `1` with the description `Execution OK`, or `0` with the collected diagnostics in the description |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.marklogic_monitoring` |
| Name | Marklogic monitoring |
| Version | `1.0` |
| Marketplace last update | 2025-07-07 |
| Author | Pandora FMS |
| Availability | Download limited to licensed users |
