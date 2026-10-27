# Pandora Openshift monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The Pandora Openshift plugin monitors an OpenShift cluster from Pandora FMS by
running the OpenShift command-line client (`oc`) on the host where the plugin
executes. Each run logs in with a user name and password, selects one project,
reads cluster and project objects, and builds Pandora FMS agents from the
command output: one agent per node, pod and deployment, one agent per resource
group, and a summary agent with element counts.

Every run delivers the agents itself, as `agent_data` documents, through the
Tentacle client or into a local data folder. The plugin does not print modules
for a Pandora FMS agent to collect, so it runs as a server plugin or from a
scheduler, never as an agent plugin.

This page documents the **`pandorafms.openshift_plugin`** addon, the
CLI-based monitoring plugin. OpenShift **Discovery** (`pandorafms.openshift`)
is a different addon: it runs from the Discovery task wizard, talks to the
cluster API with a token and generates its agents from the task. It does not
use `oc`, a project or these configuration files. See
[OpenShift Discovery](../discovery/openshift.md).

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.openshift_plugin`, version `1.0` | Documented target | Version of the Marketplace entry and of the plugin. See [Addon identity](#addon-identity) |
| The `oc` client on the host that runs the plugin | `Required` | Every collection step is an `oc` command; `cli` names the binary |
| Network access from that host to the OpenShift API endpoint | `Required` | `oc login` and every command reach the API named in `ip` |
| An OpenShift account with cluster-wide read access and project access | `Required` | The commands in [`oc` commands](#openshift-cli-commands) are cluster-scoped and project-scoped; see [Requirements](#requirements) |
| The OpenShift metrics API | `Required` for node and pod metrics | The node CPU/memory data and the pod stats agent come from `oc adm top nodes` and `oc adm top pods` |
| `tentacle_client` in `PATH` | `Required` when `mode=tentacle` (the shipped value) | Delivery runs the Tentacle client |
| A writable `local_folder` | `Required` when `mode` is not `tentacle` | Delivery copies the XML into that folder |
| CentOS 7 and Fedora as the operating system of the host | `Known compatible` | The previous edition of this guide records those systems as the ones where the plugin was tested; not re-validated for version `1.0` |
| Other operating systems of the host | `Not validated` | No other system is recorded. The plugin needs an `oc` client and a Tentacle client for the host platform |
| OpenShift versions | `Not validated` | No version matrix is recorded. The plugin calls `oc get cs`, an API Kubernetes deprecated and recent clusters may no longer serve |
| Pandora FMS versions | `Not validated` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later; there is no statement specific to this addon |

The Marketplace entry advises exploring the alternative plugins in its library
for the latest features and support.

### Requirements

1. **The `oc` client on the host that runs the plugin**, of a version that can
   talk to the target cluster. The plugin runs the binary named in `cli`; it
   applies no default path and does not check that the file exists.
2. **Network access to the OpenShift API endpoint** from that host, normally on
   TCP port `6443`. `ip` must be the API URL that `oc login` accepts, scheme and
   port included, for example `https://<TARGET_HOST>:6443`.
3. **An OpenShift account** able to run the read commands of this plugin. The
   node, namespace, API-service, component-status and cluster-operator reads are
   cluster-scoped; the pods, deployments, services, replication controllers,
   imagestreams and cluster service version reads are limited to the selected
   project. The previous edition of this guide recommends the `cluster-reader`
   role; no narrower role has been validated for this plugin.
4. **The OpenShift metrics API** enabled in the project and the cluster, so
   `oc adm top nodes` and `oc adm top pods` return rows.
5. **Pandora FMS** to receive the agents: the Pandora FMS server, either
   through its Tentacle server or through a data folder it reads.
6. **The Tentacle client (`tentacle_client`) in `PATH`**, when delivery uses
   Tentacle.

### Install and register the plugin

The Marketplace package is `pandorafms.openshift_plugin.1.0.pspz2`. It carries
the plugin, a configuration file and the registration definition that the
console reads:

| File | Destination after registration |
| --- | --- |
| `pandora_openshift.pl` | `<attachment_store>/plugin/pandora_openshift.pl` |
| `pandora_openshift.conf` | `<attachment_store>/plugin/pandora_openshift.conf` |
| `plugin_definition.ini` | Read and removed by the registration |

To register it, open **Servers → Register plugin** in the Pandora FMS console,
select the `.pspz2` file and click **Upload file**. The console registers a
plugin named **Pandora Openshift** with a single macro, `_field1_`, whose
default value is the configuration file path. The registration values are in
[Register the package in the console](#register-the-package-in-the-console).

The registered default path assumes the default attachment directory,
`/var/www/html/pandora_console/attachment`. If the installation uses another
`attachment_store`, edit the macro value to the real path.

The shipped configuration file cannot collect anything: it has no `oc` path,
no credentials and no Tentacle host, and its project and prefix are both
`prueba`. Edit the configuration file on the server that runs the plugin before
the first run, as described in [Configure](#configure).

The plugin can also be registered by hand from **Servers → Plugins** with
**Add plugin**, using **Plugin command**
`<attachment_store>/plugin/pandora_openshift.pl` and the parameters ` _field1_ `.

<!-- SCREENSHOT NEEDED: Pandora FMS "Register plugin" page with the OpenShift .pspz2 selected in the upload form and no real host or account data. -->

### Credentials and connection safety

- The OpenShift user and password are stored in plain text in the
  configuration file. Registration extracts every package file with mode
  `0755`, so the configuration file is readable by every local user until you
  restrict it. Change it to `chmod 600` and make it owned by the user of the
  Pandora FMS server process.
- Every run executes `oc login -u <USERNAME> -p <PASSWORD> <IP>`. The password
  therefore appears in the command line of the `oc` process and any local user
  can read it in the process list while the login runs. There is no
  password-free input surface in this plugin.
- `oc login` stores the session in the kubeconfig of the user that runs the
  plugin, normally `$HOME/.kube/config`. The plugin does not delete it, so the
  token remains on disk between runs.
- The plugin passes no TLS option to `oc`, so `oc` verifies the API certificate
  with its own defaults. With a self-signed API certificate, make the host trust
  the cluster CA; otherwise the login fails and every collector returns nothing.
- The plugin does not read the error output of `oc`. Messages such as an
  authentication failure go to the standard error of the run and do not stop
  it.

## Configure

### Configuration file

The configuration file is a plain-text file with `key=value` lines. Lines that
start with `#` and blank lines are skipped, keys and values are trimmed and the
last occurrence of a repeated key wins. The file has no sections.

Pass the file as the first argument of the plugin:

```bash
pandora_openshift.pl <PATH_TO_CONFIG>
```

The plugin applies no defaults of its own beyond the values in the shipped
file, and it validates nothing: a missing key behaves as an empty value, which
disables the corresponding step or delivery. This is a complete configuration
with placeholders:

```ini
# oc client
cli=/usr/local/bin/oc
user=<USERNAME>
password=<PASSWORD>
ip=https://<TARGET_HOST>:6443
project=<PROJECT>

# delivery
mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER>
tentacle_port=41121

# collectors
prefix=<PREFIX>
as_server_plugin=1
agent_openshift=1
agent_node=1
agent_pod=1
agent_pod_stats=1
agent_deployment=1
agent_imagestreams=1
agent_apiservice=1
agent_services=1
agent_replication_controller=1
agent_component_status=1
agent_operators=1
agent_csv=0
top_imagestreams_count=11
```

Every key is described in [Configuration file keys](#configuration-file-keys).

### Project scope and collectors

The run starts with `oc login` and then `oc project <PROJECT>`. The project
selects the scope of the pods, deployments, services, replication controllers,
imagestreams and cluster service versions that the plugin reads; nodes,
namespaces, API services, component statuses and cluster operators are read
cluster-wide. One run monitors one project plus the cluster-wide objects, so
monitor several projects with several plugin executions and different `prefix`
values.

The `agent_*` keys enable or disable collectors. `1` enables a collector and
`0` disables it; any other value disables it as well. All collectors are
enabled in the shipped file except `agent_csv`.

`prefix` is prepended to every agent name. It is `prueba` in the shipped file;
with an empty value the agent names start with the underscore, for example
`_OS_POD_<POD_NAME>`.

## Verify

Run the plugin manually on the host that executes it, passing the configuration
file as its only argument:

```bash
pandora_openshift.pl <PATH_TO_CONFIG>
```

The plugin is registered as executable; `perl pandora_openshift.pl
<PATH_TO_CONFIG>` produces the same result. With `as_server_plugin=1` (the
shipped value), a complete run prints a single integer and exits:

| Output | Meaning |
| --- | --- |
| `11` | All eleven enabled blocks completed and delivered. This is the value with the shipped switches, where `agent_csv=0` |
| `12` | All twelve blocks completed, including the cluster service version collector (`agent_csv=1`) |
| A lower number | All the blocks counted completed; the number is the count of enabled blocks, so it drops when you disable collectors |
| `0` | No collector ran: every switch is disabled, or no configuration file was loaded |

The printed number counts delivered blocks, not collected data. A block whose
`oc` command returned no rows still completes, so a run can print `11` and
produce agents with no modules.

A failing block does not print a number: the plugin stops at that block and
exits with status `0`. Use `as_server_plugin=0` to see which block failed, as
described in [Reading failures](#reading-failures).

After a successful run, confirm in Pandora FMS that the agents named in
[Agents](#agents) exist with their modules. Delivery through Tentacle requires
that the host can reach `tentacle_ip:tentacle_port`; the default port is
`41121`.

<!-- SCREENSHOT NEEDED: Agent list in the Pandora FMS console showing the <prefix>_Openshift and <prefix>_OS_* agents created by this plugin, with no customer hostnames. -->

## Understand the results

### Agents

| Agent | Created from | Modules |
| --- | --- | --- |
| `<prefix>_Openshift` | Element counts of seven `oc` commands | Seven counters |
| `<prefix>_OS_Nodo_<NODE_NAME>` | Rows of `oc adm top nodes` | Node state, conditions, allocation and CPU/memory |
| `<prefix>_OS_POD_<POD_NAME>` | Rows of `oc get pods` | `Ready`, `Status`, `Restarts`, `Age` |
| `<prefix>_OS_POD_Stats` | Rows of `oc adm top pods` | Two modules per pod |
| `<prefix>_OS_DEPLOYMENT_<DEPLOYMENT_NAME>` | Rows of `oc get deployments` | `Ready`, `Up to date`, `Avalaible`, `Age` |
| `<prefix>_OS_Imagestreams` | Rows of `oc adm top imagestreams` | Two modules per imagestream |
| `<prefix>_OS_Api_service` | Rows of `oc get apiservice` | One module per API service |
| `<prefix>_OS_Services` | Rows of `oc get services` | One module per service |
| `<prefix>_OS_Replication_Controllers` | Rows of `oc get rc -o wide` | Four modules per replication controller |
| `<prefix>_Component_status` | `etcd` rows of `oc get cs` | One availability module per component |
| `<prefix>_Cluster_operator` | Rows of `oc get co` | One availability module per operator |
| `<prefix>_Cluster_service_version` | Rows of `oc get csv` | One phase module per cluster service version; disabled by default |

The per-node, per-pod and per-deployment agents exist only while their `oc`
command returns rows. The grouped agents are delivered even when the command
returns nothing, so an agent with no modules means the command produced no
rows, not that the plugin failed to run.

### Values

- Only the summary counters, the condition checks and the cluster checks are
  numeric: `generic_data` for the counters and `generic_proc` for the checks.
  Every per-resource value is a `generic_data_string` module that stores the
  text `oc` printed, so values such as `2/2`, `120m`, `10Gi` or `2d` cannot be
  used with numeric thresholds.
- The seven summary counters are line counts of the command output after the
  header line. An `oc` command that fails produces no lines and therefore
  publishes `0`; the plugin does not distinguish an empty project from a failed
  command.
- The services counter module is named `Services ` — the name ends with a
  space, which is easy to miss when you search for it in the console.
- The deployment availability module is named `Avalaible`, with that spelling.
  Its value is the `AVAILABLE` column of `oc get deployments`.
- `MemoryPressure`, `DiskPressure` and `PIDPressure` report `1` when
  `oc describe node` returns `False` for the condition, that is, when there is
  no pressure. `Ready` reports `1` when the status is `True`.
- `oc get cs` returns the etcd component rows only for components whose name
  contains `etcd`. A cluster whose API no longer serves the `componentstatuses`
  resource produces no rows and the agent is delivered with no modules.
- `Allocated cpu` and `Allocated memory` are not the allocation percentage. The
  plugin takes the fourth whitespace-separated token of the `cpu` or `memory`
  row in the node's **Allocated resources** block, which in the standard `oc
  describe node` layout is the absolute value of the **Limits** column, removes
  its last two characters and then its first character, and compares the rest
  with 80 and 90. In the usual layout the result is a mangled number and both
  modules normally report `1`.

### The node agents

The node collector behaves differently from the rest:

- Per-node documents are built from `oc get nodes` and six `oc describe node`
  calls per node, but that first pass is not delivered.
- The delivered agents come from `oc adm top nodes`. The module list is never
  reset between the nodes of the first pass, so the agent of the **first** row
  of `oc adm top nodes` receives the `Status`, `Roles`, `Age`, `Version`,
  condition and `Allocated` modules of **every** node, with the same module
  names repeated once per node, plus its four `adm top` metrics.
- Every other node agent receives only `Cpu (cores)`, `Cpu %`, `Memory` and
  `Memory %`.

In a cluster with a single node the first agent carries the complete node
inventory. In a multi-node cluster its inventory modules mix several nodes and
cannot be attributed to one of them, so read node state from `oc get nodes` or
from the CPU and memory modules of the other node agents.

## Operate and troubleshoot

### Running and scheduling

- A run is one-shot: it logs in, collects, delivers and exits. It keeps no
  state except the kubeconfig that `oc login` writes.
- Schedule the plugin from a plugin module in Pandora FMS, or from `cron` when
  it delivers to a local folder. Each execution collects the state of the
  cluster at that moment.
- The registered package sets a maximum timeout of `20` seconds. A run starts
  a new `oc` process for the login, the project switch, the counts and every
  collector, and the node collector runs six `oc describe node` commands per
  node. A cluster with many nodes can exceed that timeout; raise the plugin
  timeout when you register it or edit it.
- Set `debug=1` to have delivery errors printed on standard error. Without it,
  a failed Tentacle transfer or a failed local copy is silent.

### Reading failures

With `as_server_plugin=0`, a failing block prints one XML module on standard
output instead of the numeric result:

```xml
<module>
	<name><![CDATA[Pandora_Openshift]]></name>
	<type>generic_proc</type>
	<data><![CDATA[0]]></data>
	<description><![CDATA[Nodes node-01]]></description>
</module>
```

The description names the block and the resource that failed: `Nodes <node>`,
`Pods <pod>`, `Pods stats`, `Deployments <deployment>`, `Imagestreams`,
`Api service`, `Services`, `Replication Controllers`, `Component status`,
`Cluster operator`, `Cluster service version` or `Openshift Agent`. The global
block uses the name `<prefix>_Pandora_Openshift` instead of
`Pandora_Openshift`.

`as_server_plugin=0` does not print the collected modules: on a successful run
standard output is empty. The plugin always delivers its agents itself, so it
cannot be used as an agent plugin through `module_plugin`.

The run exits with status `0` whether it delivered everything or nothing. Do
not use the exit status to detect a failure.

### Limitations

- The login result is never checked. With wrong credentials, an unreachable API
  or an untrusted certificate, every command returns nothing and the plugin
  publishes agents with `0` counters and no resource modules, still exiting
  with `0`.
- The plugin reads one project per run. There is no namespace list, filter or
  multi-project mode.
- Only the module detail `oc` prints is published. The plugin defines no
  thresholds, alerts or metric transformations of its own.
- `agent_csv` is disabled in the shipped file, and `oc get csv` requires the
  Operator Lifecycle Manager.

### Troubleshooting

| Signal | Check |
| --- | --- |
| A run prints `0` | No collector was enabled or no configuration file was read. Check that `_field1_` points to an existing file and that the `agent_*` keys are `1` |
| A run prints nothing and exits with status `0` | A block failed to deliver. Repeat with `as_server_plugin=0` to get the failing block, and with `debug=1` to see the delivery error |
| `ERROR: [transfer_mode] set to [tentacle], but no [tentacle_ip] provided.` on standard output | `mode=tentacle` has no `tentacle_ip`. The message does not stop the run; every delivery fails afterwards |
| Agents appear with `0` counters and no resource modules | Login or permissions failed. Run `oc login` and the commands of [`oc` commands](#openshift-cli-commands) with the same user and project on the same host |
| Node agents appear with only four modules | Normal behaviour in a multi-node cluster; see [The node agents](#the-node-agents) |
| `Allocated cpu` and `Allocated memory` are always `1` | Documented parsing behaviour; the modules do not measure allocation. See [Values](#values) |
| `<prefix>_OS_POD_Stats` has no modules | The metrics API did not answer `oc adm top pods`. Check the metrics server and the project |
| `<prefix>_Component_status` has no modules | `oc get cs` returned no `etcd` rows, or the cluster does not serve `componentstatuses` any more |
| No node or pod agents at all | `agent_node` or `agent_pod` is disabled, or the corresponding `oc` command returned no rows |
| Agents are delivered but do not appear in Pandora FMS | Check `tentacle_ip`, `tentacle_port` and the Tentacle server, or that `local_folder` exists and is writable by the plugin user |
| The run is killed by the plugin timeout | Raise the plugin timeout; see [Running and scheduling](#running-and-scheduling) |

## Reference

### Register the package in the console

The registration definition of the `.pspz2` package sets these values:

| Field | Value |
| --- | --- |
| Plugin name | `Pandora Openshift` |
| Description | `Plugin to monitor a Openshift environment using Openshift CLI` |
| Plugin type | `Standard` |
| Maximum timeout | `20` seconds |
| Plugin command | `<attachment_store>/plugin/pandora_openshift.pl` |
| Plugin parameters | ` _field1_ ` |

The package defines one macro:

| Macro | Required | Default | Hide | Description and help |
| --- | --- | --- | --- | --- |
| `_field1_` | Yes, according to its description | `/var/www/html/pandora_console/attachment/plugin/pandora_openshift.conf` | No | `Conf path (obligatory)`. Help: `Path to conf file` |

`Hide` is off, so the console shows the field as plain text. The console does
not enforce the macro: an empty or wrong value leaves the run without a
configuration file and it collects nothing.

<!-- SCREENSHOT NEEDED: Plugin module form in the Pandora FMS console with the _field1_ configuration path field of this plugin, no real host or credentials. -->

### Configuration file keys

| Key | Required | Default | Description |
| --- | --- | --- | --- |
| `cli` | Yes | Empty | Path to the `oc` binary on the host that runs the plugin |
| `user` | Yes | Empty | OpenShift user name |
| `password` | Yes | Empty | Password of that user, in plain text |
| `ip` | Yes | Empty | API URL accepted by `oc login`, with scheme and port, for example `https://<TARGET_HOST>:6443` |
| `project` | Yes | `prueba` | Project selected with `oc project`; it scopes the pods, deployments, services, replication controllers and imagestreams |
| `prefix` | No | `prueba` | Prefix of every agent name |
| `mode` | No | Empty | Delivery mode. `tentacle` uses the Tentacle client; any other value copies the XML into `local_folder`. Empty with `local_folder` unset delivers nothing |
| `transfer_mode` | No | Empty | Alias of `mode`, used only when `mode` is empty |
| `tentacle_ip` | Yes when `mode=tentacle` | Empty | Tentacle server address |
| `tentacle_port` | No | `41121` | Tentacle server port |
| `tentacle_client` | No | `tentacle_client` | Name or path of the Tentacle client executable |
| `tentacle_opts` | No | Empty | Extra options passed to the Tentacle client |
| `local_folder` | Yes when `mode` is not `tentacle` | Empty | Folder that receives the `agent_data` files, for example a Pandora FMS data inbox |
| `tmp` | No | `/tmp` | Folder where the XML file is written before delivery |
| `as_server_plugin` | No | `1` | `1` prints the block count and suppresses the per-block error module; `0` prints the error module of a failing block |
| `as_agent_plugin` | No | Empty | Alias that sets `as_server_plugin` to `0` when it is enabled and `as_server_plugin` is not set |
| `debug` | No | Empty | `1` prints delivery errors on standard error |
| `module_group` | No | Empty | Module group assigned to every generated module |
| `module_interval` | No | Empty | Module interval assigned to every generated module, in seconds |
| `top_imagestreams_count` | No | `11` | Number of `oc adm top imagestreams` output lines passed to the parser, header included, so it yields at most one imagestream fewer |
| `agent_openshift` | No | `1` | Summary counters agent |
| `agent_node` | No | `1` | Per-node agents |
| `agent_pod` | No | `1` | Per-pod agents |
| `agent_pod_stats` | No | `1` | Pod stats agent |
| `agent_deployment` | No | `1` | Per-deployment agents |
| `agent_imagestreams` | No | `1` | Imagestreams agent |
| `agent_apiservice` | No | `1` | API service agent |
| `agent_services` | No | `1` | Services agent |
| `agent_replication_controller` | No | `1` | Replication controller agent |
| `agent_component_status` | No | `1` | Component status agent |
| `agent_operators` | No | `1` | Cluster operator agent |
| `agent_csv` | No | `0` | Cluster service version agent |

The defaults in this table are the values of the shipped configuration file.
A key that is absent from the file behaves as an empty value, so leaving a key
out is not the same as setting it to `1`.

### Collector blocks and the result value

The plugin runs its collectors in this fixed order. The result number printed
with `as_server_plugin=1` is the count of enabled blocks that completed.

| # | Switch | Command | Agent |
| --- | --- | --- | --- |
| 1 | `agent_node` | `oc get nodes`, `oc describe node` (six times per node), `oc adm top nodes` | `<prefix>_OS_Nodo_<NODE_NAME>` |
| 2 | `agent_pod` | `oc get pods` | `<prefix>_OS_POD_<POD_NAME>` |
| 3 | `agent_pod_stats` | `oc adm top pods` | `<prefix>_OS_POD_Stats` |
| 4 | `agent_deployment` | `oc get deployments` | `<prefix>_OS_DEPLOYMENT_<DEPLOYMENT_NAME>` |
| 5 | `agent_imagestreams` | `oc adm top imagestreams` | `<prefix>_OS_Imagestreams` |
| 6 | `agent_apiservice` | `oc get apiservice` | `<prefix>_OS_Api_service` |
| 7 | `agent_services` | `oc get services` | `<prefix>_OS_Services` |
| 8 | `agent_replication_controller` | `oc get rc -o wide` | `<prefix>_OS_Replication_Controllers` |
| 9 | `agent_component_status` | `oc get cs --no-headers`, filtered by `grep etcd` | `<prefix>_Component_status` |
| 10 | `agent_operators` | `oc get co --no-headers` | `<prefix>_Cluster_operator` |
| 11 | `agent_csv` | `oc get csv` with a name and phase column selection | `<prefix>_Cluster_service_version` |
| 12 | `agent_openshift` | Seven count commands | `<prefix>_Openshift` |

A block that fails to deliver stops the run before its count is incremented,
so a failure never produces a number.

### Generated modules

#### Summary agent

| Module | Type | Value |
| --- | --- | --- |
| `Services ` | `generic_data` | Line count of `oc get services` |
| `Deployments` | `generic_data` | Line count of `oc get deployments` |
| `Namespaces` | `generic_data` | Line count of `oc get namespaces` |
| `Nodes` | `generic_data` | Line count of `oc get nodes` |
| `Pods` | `generic_data` | Line count of `oc get pods` |
| `Imagestreams` | `generic_data` | Line count of `oc adm top imagestreams`, without the `top_imagestreams_count` limit |
| `Replication controllers` | `generic_data` | Line count of `oc get rc` |

#### Node agents

| Module | Type | Value |
| --- | --- | --- |
| `Status`, `Roles`, `Age`, `Version` | `generic_data_string` | Columns of `oc get nodes`; see [The node agents](#the-node-agents) |
| `MemoryPressure`, `DiskPressure`, `PIDPressure` | `generic_proc` | `1` when the condition status is `False` |
| `Ready` | `generic_proc` | `1` when the condition status is `True` |
| `Allocated memory`, `Allocated cpu` | `generic_proc` | `1` below 80, `2` from 80 to 90, `3` above 90, on a value that does not measure allocation |
| `Cpu (cores)`, `Cpu %`, `Memory`, `Memory %` | `generic_data_string` | Columns of `oc adm top nodes` |

#### Pod agents

| Module | Type | Value |
| --- | --- | --- |
| `Ready` | `generic_data_string` | `READY` column, for example `1/1` |
| `Status` | `generic_data_string` | `STATUS` column |
| `Restarts` | `generic_data_string` | `RESTARTS` column |
| `Age` | `generic_data_string` | `AGE` column |

#### Pod stats agent

| Module | Type | Value |
| --- | --- | --- |
| `<POD_NAME>_Cpu (cores)` | `generic_data_string` | `CPU(cores)` column |
| `<POD_NAME>_Memory (bytes)` | `generic_data_string` | `MEMORY(bytes)` column |

#### Deployment agents

| Module | Type | Value |
| --- | --- | --- |
| `Ready` | `generic_data_string` | `READY` column, for example `2/2` |
| `Up to date` | `generic_data_string` | `UP-TO-DATE` column |
| `Avalaible` | `generic_data_string` | `AVAILABLE` column |
| `Age` | `generic_data_string` | `AGE` column |

#### Imagestreams agent

| Module | Type | Value |
| --- | --- | --- |
| `<IMAGESTREAM_NAME>_Storage` | `generic_data_string` | `STORAGE` column |
| `<IMAGESTREAM_NAME>_Images` | `generic_data_string` | `IMAGES` column |

#### API service agent

| Module | Type | Value |
| --- | --- | --- |
| `<API_SERVICE_NAME>` | `generic_data_string` | `AVAILABLE` column; the description holds the service and age columns |

#### Services agent

| Module | Type | Value |
| --- | --- | --- |
| `<SERVICE_NAME>` | `generic_data_string` | `PORT(S)` column; the description holds the type, cluster IP and external IP |

#### Replication controller agent

| Module | Type | Value |
| --- | --- | --- |
| `<RC_NAME>_Ready` | `generic_data_string` | `READY` column |
| `<RC_NAME>_Desired` | `generic_data_string` | `DESIRED` column |
| `<RC_NAME>_Current` | `generic_data_string` | `CURRENT` column |
| `<RC_NAME>_Age` | `generic_data_string` | `AGE` column; the description holds containers, images and selector |

#### Component status agent

| Module | Type | Value |
| --- | --- | --- |
| `<COMPONENT_NAME>` | `generic_proc` | `1` for `Healthy`, `0` otherwise |

#### Cluster operator agent

| Module | Type | Value |
| --- | --- | --- |
| `<OPERATOR_NAME>` | `generic_proc` | `1` when the `AVAILABLE` column is `True`, `0` otherwise, including `Unknown` |

#### Cluster service version agent

| Module | Type | Value |
| --- | --- | --- |
| `<CSV_NAME>` | `generic_proc` | `1` when the phase is `Succeeded`, `0` otherwise |

### OpenShift CLI commands

| Command | Scope | Used for |
| --- | --- | --- |
| `oc login -u <USERNAME> -p <PASSWORD> <IP>` | — | Session, once per run |
| `oc project <PROJECT>` | — | Selects the project |
| `oc get nodes` | Cluster | Node inventory and the `Nodes` counter |
| `oc describe node <NODE_NAME>` | Cluster | Node conditions and `Allocated` modules, six times per node |
| `oc adm top nodes` | Cluster | Node CPU and memory modules |
| `oc get pods` | Project | Pod agents and the `Pods` counter |
| `oc adm top pods` | Project | Pod stats agent |
| `oc get deployments` | Project | Deployment agents and the `Deployments` counter |
| `oc adm top imagestreams` | Project | Imagestreams agent and the `Imagestreams` counter |
| `oc get apiservice` | Cluster | API service agent |
| `oc get services` | Project | Services agent and the `Services ` counter |
| `oc get rc -o wide` | Project | Replication controller agent |
| `oc get rc` | Project | `Replication controllers` counter |
| `oc get cs --no-headers`, filtered by `grep etcd` | Cluster | Component status agent |
| `oc get co --no-headers` | Cluster | Cluster operator agent |
| `oc get csv -o custom-columns=NAME:.metadata.name,PHASE:.status.phase --no-headers` | Project | Cluster service version agent |
| `oc get namespaces` | Cluster | `Namespaces` counter |

### Addon identity

| Field | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.openshift_plugin` |
| Marketplace name | Pandora Openshift |
| Addon version | `1.0` |
| Marketplace last update | 2025-06-26 |
| Marketplace package | `pandorafms.openshift_plugin.1.0.pspz2` |
| License | One |
| Availability | Download limited to licensed users |
| Marketplace type | Miscelaneus |
| Workflow | Server plugin: CLI collector that delivers agent XML |
| Executable | `pandora_openshift.pl` |

[https://marketplace.pandorafms.com/entries/pandorafms.openshift_plugin](https://marketplace.pandorafms.com/entries/pandorafms.openshift_plugin)
