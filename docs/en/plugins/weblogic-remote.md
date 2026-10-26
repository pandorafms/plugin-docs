# Weblogic remote monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The `Weblogic remote` addon monitors an Oracle WebLogic Server domain from
Pandora FMS over SNMP. Each run walks the WebLogic SNMP agent of one domain and
turns the answer into Pandora FMS modules: the state and heap of every server
instance, JDBC datasource usage, pending JMS messages, Jolt connection pool
state, work manager load, the sessions of the deployed applications, EJB
waiter counts and JRockit heap usage.

The collector does not authenticate against WebLogic and does not need the
administration console: it reads the monitoring tree that the WebLogic SNMP
agent publishes, so the only credential involved is the SNMP community.

The collector runs as a Pandora FMS **server plugin**. Every execution prints
one XML `<module>` block per value on standard output, and Pandora FMS stores
them in the agent that owns the module definition. It creates no agent and
delivers no document by itself.

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.weblogic_remote`, version `1.0` | Documented target | Marketplace entry; see [Addon identity](#addon-identity) |
| CentOS 7 and Fedora | `Known compatible` | The previous edition of this guide records both as tested systems for the addon. Not re-validated for version `1.0` |
| Other operating systems of the Pandora FMS server that runs the collector | `Not validated` | No test record. The previous edition states that any Linux system should work, without evidence |
| WebLogic Server versions and editions | `Not validated` | No version matrix has been recorded for this addon |
| Pandora FMS versions | `Not validated` | No release-specific record. The Marketplace states that its integrations are compatible with Pandora FMS NG 784 and later |
| A WebLogic domain with the SNMP agent enabled and reachable | `Required` | Every module is built from objects under `1.3.6.1.4.1.140.625` |
| An SNMP read community accepted by the WebLogic SNMP agent | `Required` | Every query is sent with that community |
| The `snmpwalk` utility from net-snmp in `PATH` | `Required` | Every data read is a call to `snmpwalk` |
| A Pandora FMS Plugin Server able to reach the WebLogic SNMP port | `Required` | The collector is a server plugin |

### Requirements

1. **A WebLogic Server domain** with its SNMP agent enabled. The agent is not
   enabled by default in every domain: confirm it is running and reachable from
   the machine that executes the collector.
2. **The SNMP port of that agent.** The collector sends to UDP `161` when no
   port is given. When the domain runs the WebLogic SNMP agent on another port,
   pass it as the third argument; the examples on this page use `40161`.
3. **An SNMP community with read access** to the WebLogic monitoring tree.
   SNMP version 1 is the only version the collector sends, so use a community
   defined for v1.
4. **The `snmpwalk` command**, from the net-snmp tools, installed on the
   Pandora FMS server that runs the collector and reachable through `PATH`.
5. **A Pandora FMS Plugin Server** running and able to reach the WebLogic SNMP
   port. The collector is executed by the Plugin Server, so it runs on a
   Pandora FMS server, not on the WebLogic host.

### Install the collector

Download the addon from its Marketplace entry, which is limited to licensed
users:

[https://marketplace.pandorafms.com/entries/pandorafms.weblogic_remote](https://marketplace.pandorafms.com/entries/pandorafms.weblogic_remote)

The console installs the package and registers the plugin definition. To run
the collector outside the console, copy the executable to the Pandora FMS
server plugin folder, `/usr/share/pandora_server/util/plugin/`, and give it
permission to run.

### Enable the WebLogic SNMP agent

The collector reads only what the WebLogic SNMP agent publishes. Enable the
agent for the domain you want to monitor and note its port and read community;
the WebLogic documentation describes the agent configuration. The collector
needs no administrator account, no RESTful Management Services endpoint and no
WebLogic user.

## Configure

### Register the plugin in the console

1. Open **Servers → Plugins** and register the collector as a standard server
   plugin.
2. In **Plugin command**, enter the path of the executable on the Pandora FMS
   server, for example
   `/usr/share/pandora_server/util/plugin/plugin_weblogic_snmp.pl`.
3. In **Plugin parameters**, pass the three arguments as fields:

```text
_field1_ _field2_ _field3_
```

4. In the macro fields, describe each argument. The example uses these values:

| Field | Description | Example value |
| --- | --- | --- |
| `_field1_` | Host name or IP address of the WebLogic SNMP agent | `<TARGET_HOST>` |
| `_field2_` | SNMP read community of that agent | `<COMMUNITY>` |
| `_field3_` | SNMP port of the agent | `40161` |

<!-- SCREENSHOT NEEDED: Pandora FMS server plugin registration form with the path to the WebLogic collector and _field1_ _field2_ _field3_ as parameters, no real hostnames or communities. -->

The three arguments are positional: the host and the community are mandatory
and the port is optional. The collector has no named options and no
configuration file.

### Create the modules

One module definition is needed per module name you want to receive. Because
the collector appends the WebLogic object name to most module names, a module
definition covers the instance, datasource, destination, pool or application
named in it. When a new instance or resource appears in the domain, create the
module for its name.

Register each module as a plugin module of the agent that must hold it, select
the plugin registered above, and keep the default values of the fields: every
module of this collector is filled with the same three arguments.

<!-- SCREENSHOT NEEDED: plugin module definition in the Pandora FMS console for one WebLogic module, showing the plugin selection and the three field values, no real hostnames or communities. -->

### SNMP access and secrets

- The community travels in clear text over the network, because the collector
  sends SNMP version 1. Restrict the SNMP port to the Pandora FMS servers, or
  use a dedicated monitoring network.
- The community is written in the plugin parameters of every module, so it is
  stored in the Pandora FMS database and visible to the users who can read the
  module definition. Use a read-only community dedicated to monitoring.
- The collector passes the community to `snmpwalk` as a command-line argument,
  so it also appears in the process list of the Pandora FMS server while a run
  is in progress.

## Verify

Run the collector manually on the Pandora FMS server:

```bash
cd /usr/share/pandora_server/util/plugin/
./plugin_weblogic_snmp.pl <TARGET_HOST> <COMMUNITY> 40161
```

Each run executes once and exits. A working run prints consecutive
`<module>` blocks, one per collected value:

```xml
<module>
<name>WebLogic_SNMP_Status</name>
<type>generic_proc</type>
<data><![CDATA[1]]></data>
<description><![CDATA[Status of Weblogic SNMP Interface]]></description>
</module>
<module>
<name>WebLogic_ServerStatus_AdminServer</name>
<type>generic_proc</type>
<data><![CDATA[1]]></data>
<description><![CDATA[Status of Weblogic Instance 'AdminServer']]></description>
</module>
```

`WebLogic_SNMP_Status` is the availability check: it reports `1` when the
WebLogic SNMP agent answers the availability subtree and `0` when it does not.
When it reports `0`, the run prints no other module — see
[Operate and troubleshoot](#operate-and-troubleshoot).

A run with fewer than two arguments prints the usage summary and exits with
status `1`. Any other run exits with status `0`, whether it collected data or
not.

Then confirm the arrival in the console: open the agent that owns the module
definitions and check the modules described in
[Understand the results](#understand-the-results) after an interval has passed.

<!-- SCREENSHOT NEEDED: Pandora FMS agent detail view of a WebLogic agent showing the WebLogic_ modules with data, no real hostnames or communities. -->

## Understand the results

A run produces one module per object found in the domain, grouped by the
WebLogic subsystem it belongs to:

- **Availability and server state.** `WebLogic_SNMP_Status` reports whether
  the WebLogic SNMP agent answers. `WebLogic_ServerStatus_<instance>` reports `1` for
  every server instance whose state is `RUNNING` and `0` otherwise.
- **JVM memory.** `WebLogic_FreeHeap_<instance>` reports the free heap and
  `WebLogic_FreeHeap%_<instance>` the free percentage of the heap of each
  server instance. `Weblogic_FreeHeapJrokit%_<instance>` reports the free
  percentage of the JRockit heap, only for instances that publish the JRockit
  tree.
- **JDBC datasources.** For every datasource, `WebLogic_DbpoolTime_<pool>`
  reports the average wait time reported by the datasource, in seconds, `WebLogic_Current_DbpoolConns_<pool>`
  the current connections, `Weblogic_DbpoolConns%_<pool>` the percentage of the
  maximum, and `Weblogic_DbpoolLeakConns_<pool>` the leaked connections.
- **JMS destinations.** `Weblogic_PendingDST_<destination>` reports the pending
  messages of a destination.
- **Jolt connection pools.** `Weblogic_joltpoolStatus_<machine>_<pool>` reports
  the state of every pool.
- **Work managers.** `Weblogic_QueueLength_<threadpool>` reports the queue
  length and `Weblogic_FreeThreads_<threadpool>` the free threads of the thread
  pool that the work manager uses.
- **Applications and EJBs.** `WebLogic_Sessions_<application>` reports the open
  sessions of the deployed applications, and `WebLogic_EjbWaiter_<location>_<name>`
  the waiter count of the EJBs.

The object part of a name is the value WebLogic publishes for that object, so
names change when the domain is renamed or redeployed. Two naming details are worth knowing when you create module
definitions:

- **The prefix case is not uniform.** The status, heap, JDBC, session and EJB
  modules start with `WebLogic_`; the queue, thread, destination, Jolt and
  percentage-of-connections modules start with `Weblogic_`. Module names are
  case-sensitive in Pandora FMS, so copy the exact spelling from the run.
- **Internal applications are excluded** from the session modules: the
  WebLogic internal applications, the administration and asynchronous
  contexts, and the deployment and diagnostics applications produce no module.

Every module is declared as `generic_data` or `generic_proc`, and no module
carries a unit, a threshold or a module group.

## Operate and troubleshoot

- **The collector keeps no state between runs.** Each execution queries the
  WebLogic SNMP agent again, so it can be run manually at any time.
- **Do not run two executions at once on the same Pandora FMS server.** The
  collector writes the whole SNMP walk into the fixed file
  `/tmp/weblogic.snmp.dump`, discards it at the start and at the end of each
  run, and reads all the modules from it. Two concurrent runs — two agents, two
  modules executed at the same time, or an overlapping manual run — reuse and
  delete each other's file, so a run can report the data of another WebLogic
  domain. Stagger the executions or use a different Pandora FMS server per
  domain.
- **There is no verbose mode.** The collector accepts no debug option, and it
  discards the errors of `snmpwalk`. To diagnose a run, repeat the walk
  manually:

```bash
snmpwalk -On -v1 -c <COMMUNITY> <TARGET_HOST>:40161 .1.3.6.1.4.1.140.625.730
```

- **`WebLogic_SNMP_Status` reports `0` and no other module appears** — nothing
  answered on the SNMP tree. Check that the WebLogic SNMP agent is enabled,
  that the port is the agent port and not the administration port, that the
  community is valid for SNMP v1, and that `snmpwalk` is installed on the
  Pandora FMS server: a missing `snmpwalk` produces the same result as an
  unreachable agent.
- **`WebLogic_SNMP_Status` reports `1` and the server modules are missing** —
  the tree answered but the instance table did not. The WebLogic SNMP agent
  publishes only the subsystems that are active in the domain, so an empty or
  partial result reflects the domain, not the collector.
- **`Weblogic_PendingDST_` modules never appear** — this module only accepts
  JMS servers whose published name matches the pattern `CRMNAModule!JMSServer_`
  followed by the destination name. Destinations of a JMS server with another
  name are skipped even when they publish pending messages.
- **The run stops in the middle of the output** — a run aborts when a datasource
  or an instance reports zero capacity, because the percentage module divides
  by it. The modules printed before that point are still valid.
- **Two module values appear to belong to different domains** — the fixed walk
  file described above was reused by a concurrent run. Repeat the execution
  alone and compare the values with a manual `snmpwalk`.
- **A module shows a text value where a number is expected** — the Jolt pool
  state modules are boolean modules, but they publish the state text that
  WebLogic returns. Read them as text and create the alert conditions
  accordingly.

## Reference

### Command line

```text
./plugin_weblogic_snmp.pl <target_address> <target_community> [target_port]
```

| Argument | Required | Default | Description |
| --- | --- | --- | --- |
| `target_address` | Yes | — | Host name or IP address of the WebLogic SNMP agent |
| `target_community` | Yes | — | SNMP v1 read community |
| `target_port` | No | `161` | SNMP port of the agent |

| Condition | Behavior |
| --- | --- |
| Fewer than two arguments | Prints the usage summary and exits with status `1` |
| Two or three arguments | Runs the collection and exits with status `0` |
| A fourth argument | Ignored |
| The SNMP tree does not answer, or `snmpwalk` is missing | Prints only `WebLogic_SNMP_Status` with value `0` and exits with status `0` |

The collector sends SNMP version 1 only. It offers no named options, no
configuration file, no environment variable and no verbose mode.

### Data sources

Every run walks these subtrees of the WebLogic monitoring tree, identified by
the object identifier `.1.3.6.1.4.1.140.625` plus the suffix below:

| Suffix | Feeds |
| --- | --- |
| `.161` | EJB waiter modules |
| `.190` | JDBC datasource modules |
| `.220` | JMS destination modules |
| `.280` | Jolt connection pool modules |
| `.302` | JRockit heap module |
| `.340` | Server heap modules |
| `.360` | Server state and Jolt pool name modules |
| `.367` | Work manager modules |
| `.430` | Application session modules |
| `.730` | SNMP availability check |

### Generated modules

Names are reproduced as the collector prints them. `<instance>`, `<pool>`,
`<destination>`, `<threadpool>`, `<application>`, `<machine>`, `<location>`
and `<name>` are the object names published by WebLogic.

| Module name | Type | Meaning |
| --- | --- | --- |
| `WebLogic_SNMP_Status` | `generic_proc` | `1` when the WebLogic SNMP agent answers the availability subtree, `0` otherwise |
| `WebLogic_ServerStatus_<instance>` | `generic_proc` | `1` when the server instance state is `RUNNING`, `0` otherwise |
| `WebLogic_FreeHeap_<instance>` | `generic_data` | Free heap of the server instance |
| `WebLogic_FreeHeap%_<instance>` | `generic_data` | Free heap as a percentage of the total heap |
| `WebLogic_DbpoolTime_<pool>` | `generic_data` | Average wait time reported by the datasource, in seconds |
| `WebLogic_Current_DbpoolConns_<pool>` | `generic_data` | Connections currently in use in the datasource |
| `Weblogic_DbpoolConns%_<pool>` | `generic_data` | Connections in use as a percentage of the maximum capacity |
| `Weblogic_DbpoolLeakConns_<pool>` | `generic_data` | Connections reported as leaked by the datasource |
| `WebLogic_EjbWaiter_<location>_<name>` | `generic_data` | Waiter count of the EJB |
| `WebLogic_Sessions_<application>` | `generic_data` | Open sessions of the deployed application |
| `Weblogic_QueueLength_<threadpool>` | `generic_data` | Requests waiting in the work manager queue |
| `Weblogic_FreeThreads_<threadpool>` | `generic_data` | Idle threads of the work manager |
| `Weblogic_PendingDST_<destination>` | `generic_data` | Messages pending in the JMS destination |
| `Weblogic_joltpoolStatus_<machine>_<pool>` | `generic_proc` | State text of the Jolt pool, for example `Active` |
| `Weblogic_FreeHeapJrokit%_<instance>` | `generic_data` | Free percentage of the JRockit heap |

### Output

The collector prints an XML document fragment on standard output: one
`<module>` element per value, without a surrounding `<agent_data>` element. Each
element carries `name`, `type`, `data` and `description`. Values of numeric
modules that are not numbers are emptied, and text modules keep their text.

The module names include the WebLogic object name, so the same module
definition receives data only from the object named in it.

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.weblogic_remote` |
| Name | Weblogic remote |
| Version | `1.0` |
| Category | Miscelaneus |
| License | One |
| Marketplace last update | 2025-06-27 |
| Availability | Download limited to licensed users |
| Package | `pandorafms.weblogic_remote.1.0.pspz2` |
| Collector version | `v4r1`, as reported by the usage summary |

The Marketplace record and the previous edition of this guide describe the
addon with a different command surface, `-u <URL> -us <USER> -p <PASSWORD>`
plus an optional `-g` and `--data_dir`, and a collection path that needs
RESTful Management Services in WebLogic. This page documents the SNMP
collector, whose arguments are positional. Compare the command registered in
**Servers → Plugins** with the two lists before creating modules: the parameters
shown there are the ones the installation executes.
