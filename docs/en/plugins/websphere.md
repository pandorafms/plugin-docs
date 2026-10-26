# Pandora WebSphere plugin

*Article last updated: 2026-10-26.*

## What it does

The Pandora WebSphere plugin reads the state of every running application
server in an IBM WebSphere Application Server cell and publishes it in Pandora
FMS. Each run invokes the `wsadmin` administration client of a WebSphere profile
with a small administration script, reads the instance list it returns and, for
every application server reported as a managed process, builds a Pandora FMS
agent named after that server with nine modules: process type, process ID, state,
operating system, heap size, free heap memory, two WebContainer thread pool
figures and the number of running applications.

Nothing is installed inside WebSphere and the addon opens no listener of its own:
it uses the administration connection that the WebSphere profile already
defines. The host that runs the addon must therefore have the WebSphere client
files and the profile of the cell.

One run produces two different surfaces:

- **Standard output** carries two modules for the host that executes the addon,
  `Websphere_status` and `Websphere_count`, so the Pandora FMS agent or plugin
  module that runs it reports the outcome of the execution.
- **One agent document per instance** is sent to a Tentacle server, so the
  console receives an agent per WebSphere application server with that server's
  modules.

This page documents the Marketplace addon `pandorafms.websphere`. It is not the
separate WebSphere PMI plugin whose modules are named `Wbs_*`: the Marketplace
entry, its package and the guide linked from it all match the addon described
here. See [Addon identity](#addon-identity).

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.websphere`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| CentOS 7, Fedora, AIX 7.1, AIX 7.2 | `Known compatible` | The addon guide linked from the Marketplace entry records these as the systems where the plugin was tested. Not re-validated for version `1.0` |
| Other Linux distributions and other operating systems | `Not validated` | No distribution or version matrix has been recorded for this addon |
| IBM WebSphere Application Server versions | `Not validated` | No WebSphere release has been recorded. The addon reads `AdminControl` and `AdminConfig` attributes and the JVM `heapSize` and `freeMemory` properties |
| At least one running application server of type `ManagedProcess` | `Required` | Only instances reporting that process type are published; a deployment manager or a node agent is not |
| `wsadmin` of a WebSphere profile, with Jython support | `Required` | It is the only data source: every run executes it |
| The `PandoraFMS::PluginTools` Perl library | `Required` | The addon fails to start without it. The addon guide lists it as a prerequisite |
| A Tentacle server reachable from the host that runs the addon | `Required` when `mode=tentacle` | Each instance agent is delivered to `tentacle_ip:tentacle_port` |
| A writable data folder | `Required` when `mode` is not `tentacle` | Each instance agent document is copied into `local_folder` |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions; it is a catalogue-wide statement covering this addon, not a test record for it |

### Requirements

1. **A WebSphere cell with the application servers you want to monitor
   running.** The plugin lists the servers through the cell and node
   administration objects, so the cell metadata must be reachable by `wsadmin`.
2. **The `wsadmin` client of a WebSphere profile** on the host that runs the
   addon, with Jython support (`-lang jython`). The addon passes no host or port
   to `wsadmin`, so it uses the connection configured in that profile.
3. **A WebSphere administrative user** that can run `AdminConfig` and
   `AdminControl` queries on the cell. The credential pair travels to `wsadmin`
   on its command line.
4. **An administration script** that the addon passes to `wsadmin` with `-f`.
   The addon guide puts `pandora_websphere.pl`, `pandora_websphere.conf` and this
   script in the same folder.
5. **The `PandoraFMS::PluginTools` Perl library, in a `PandoraFMS` directory
   next to the executable.** The addon adds its own directory to the Perl
   library path, so a copy placed there is always found; a system-wide
   installation of the library also works. If the distributed package already
   places it next to the executable, no action is needed.
6. **The Tentacle client (`tentacle_client`) available in `PATH`** on the host
   that runs the addon. Every instance agent is delivered with it when
   `mode=tentacle`.
7. **A Marketplace account with a license**: the download of this addon is
   limited to licensed users.
8. **Pandora FMS** to receive the data: the Pandora FMS Data Server enabled to
   accept the Tentacle deliveries, and the Plugin Server enabled if you register
   the addon as a console plugin module.

### Install the addon

Download the package from the Marketplace entry:

[https://marketplace.pandorafms.com/entries/pandorafms.websphere](https://marketplace.pandorafms.com/entries/pandorafms.websphere)

The package contains the addon executable `pandora_websphere.pl`, its sample
configuration file `pandora_websphere.conf` and the administration script
`list_servers.py`. Copy them to the host that will run the addon — the
recommended folder for a server plugin is
`/usr/share/pandora_server/util/plugin/` — and edit a copy of the configuration
file, because its values are examples.

Place `PluginTools.pm` in a `PandoraFMS` subdirectory of that folder if the
package does not include it. The library ships with Pandora FMS.

## Configure

### Configuration file

The addon reads exactly one configuration file, passed as the first argument.
Each line holds a `key;value` pair separated by a semicolon. Values are trimmed,
blank lines and lines that start with `#` are skipped, and the last occurrence of
a repeated key wins. There are no sections and the key set is not validated.

```ini
wsadmin;<PATH_TO_WSADMIN>
jython;<PATH_TO_JYTHON_SCRIPT>
user;<USERNAME>
password;<PASSWORD>
mode;tentacle
tentacle_ip;<PANDORA_FMS_URL>
tentacle_port;41121
```

The names in the sample file, `pandora_websphere.conf` and `list_servers.py`, are
conventions: the file name is free and the script is whatever path you put in
`jython`.

### Key points

- **`wsadmin` is the absolute path to the profile's `wsadmin` client**, for
  example `/opt/IBM/WebSphere/AppServer/profiles/AppSrv01/bin/wsadmin.sh` on
  Linux or AIX. The addon runs it as
  `<wsadmin> -lang jython -user <user> -password <password> -f <jython>`.
- **`jython` is the absolute path to the administration script.** A relative
  value is resolved from the working directory of the process that runs the
  addon. The shipped sample writes `listservers.py`, while the script delivered
  with the addon is `list_servers.py`: set the name that exists in your copy,
  because the value is passed to `wsadmin` unchanged.
- **`user` and `password` are the WebSphere administrative credentials.**
  `wsadmin` receives them on its command line, and the configuration file stores
  the password in plain text.
- **`mode` selects the delivery.** `tentacle` (lowercase) runs the Tentacle
  client for every instance agent. Any other non-empty value copies the agent
  document into `local_folder` instead. The key `transfer_mode` is accepted as
  an alias when `mode` is absent, but the addon's own earlier check reads `mode`
  only, so use `mode`.
- **`tentacle_ip` and `tentacle_port` are the Tentacle destination.** The port
  defaults to `41121`. The address is used exactly as written; there is no
  default host.
- **`module_group`, `module_interval` and `module_tag_list` are applied to every
  module of the run**, including `Websphere_status` and `Websphere_count`. The
  uppercase variants `MODULE_GROUP`, `MODULE_INTERVAL` and `MODULE_TAG_LIST` take
  precedence when both spellings are present.
- **`debug` prints the addon's own diagnostics on standard error.** Delivery
  errors, Tentacle output and temporary-file errors are silent without it.
- **`temp` (or `tmp`) sets the folder used to write the agent documents.** It is
  `/tmp` on Linux when it is not set. There is no default on other operating
  systems: set it explicitly, because otherwise the document path resolves to
  the filesystem root.

### Execution paths

The addon can be run in two places. Both produce the same two surfaces, so pick
the one that matches where the WebSphere administration client lives.

**As a plugin of the Pandora FMS agent on the WebSphere host (recommended).**
Declare it in the agent configuration so the agent executes it at every
interval:

```text
module_plugin perl /opt/pandora/plugins/websphere/pandora_websphere.pl /opt/pandora/plugins/websphere/pandora_websphere.conf
```

The agent ingests the two modules printed on standard output and reports them in
its own agent, while the instance agents arrive through Tentacle. This is the
only path where the machine that runs `wsadmin` is also monitored by the agent.

**As a console plugin module.** The addon guide describes registering the addon
in Pandora FMS and then calling it from a plugin module of an agent:

1. Open **Servers → Plugins**.
2. Register the addon, either by uploading the `.pspz2` package of the
   Marketplace entry or by adding it manually with the command that runs
   `pandora_websphere.pl` and the macro `_field1_` as the configuration file
   path.
3. In the agent, create a plugin module and select the registered plugin, with
   the configuration file path as the field value.

<!-- SCREENSHOT NEEDED: Pandora FMS console plugin registration form for server plugins, showing the pandora_websphere.pl command and its _field1_ macro field. -->

Pandora FMS executes a console plugin module on the server that processes it,
not on the host of the agent, so this path requires the WebSphere client files
and the profile on that Pandora FMS server. It also changes what the module
shows: the whole standard output of the run is stored as the module value, so
the module displays the XML of `Websphere_status` and `Websphere_count` instead
of a single number. The instance agents still arrive through Tentacle, because
the addon delivers them independently of how it was started.

### Credentials and transport

- The configuration file holds the WebSphere password in plain text: restrict it
  to the user that runs the addon, for example with `chmod 600`, and keep it out
  of shared folders.
- `wsadmin` receives the password as the value of `-password`, so it is visible
  in the process list of the host while the client runs. Use a dedicated
  WebSphere administrative account for this addon instead of a personal one.
- The command is assembled by direct interpolation: a path or a password that
  contains whitespace or shell metacharacters (`;`, `&`, `$`, quotes) is split
  or interpreted by the shell and the run fails. Choose a password without those
  characters and paths without spaces.
- The addon has no transport options of its own. The `wsadmin` connection is the
  one configured in the WebSphere profile, and the instance agents travel to the
  Tentacle server in `tentacle_ip:tentacle_port` as configured.

## Verify

Run the addon manually from a terminal, passing the configuration file as its
only argument:

```bash
perl pandora_websphere.pl pandora_websphere.conf
```

The relative form works when the terminal is already in the folder that contains
both files. Each run executes once and exits.

A successful run prints two module blocks on standard output and nothing else.
This is their exact shape; the values are illustrative:

```xml
<module>
	<name><![CDATA[Websphere_status]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[Estado de la ejecucion del plugin de websphere]]></description>
</module>
<module>
	<name><![CDATA[Websphere_count]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<description><![CDATA[Numero de instancias (application servers) recopiladas por el plugin de websphere]]></description>
</module>
```

`Websphere_count` must match the number of running application servers of type
`ManagedProcess` in the cell. Each of them also becomes an agent in Pandora FMS,
named exactly after the WebSphere server, with the modules listed in
[Generated modules](#generated-modules).

<!-- SCREENSHOT NEEDED: Pandora FMS agent list or an agent view showing the agents created by the WebSphere addon, one per application server, with the nine modules of one of them. -->

A run that prints `Websphere_status` with `1` proves only that the addon reached
the end. It does not prove that `wsadmin` returned data: check `Websphere_count`.

## Understand the results

The addon produces two independent surfaces in every run:

- **The agent that executes it receives `Websphere_status` and
  `Websphere_count`.** These are the only modules written to standard output.
  When a delivery fails the addon prints a third module, `Pandora_websphere`,
  with value `0`, and ends the run before the two status modules.
- **Every published instance becomes its own agent.** The agent document carries
  the WebSphere server name as the agent name and the nine modules below, each
  prefixed with that same name. The document sets no address, no agent group and
  no interval, so the new agent takes the values that the Pandora FMS server
  applies by default.

How the instance list is read:

- **Only servers whose process type is exactly `ManagedProcess` are
  published.** Deployment managers, node agents and other process types are
  skipped silently, and they do not increase `Websphere_count`.
- **The addon discards the first two semicolon-separated segments of the
  `wsadmin` output** before parsing instances, because it expects the `wsadmin`
  connection banner there. If a version of `wsadmin`, another connector type or
  an extra line changes that count, the discarded segments can include the first
  instance: compare the number of agents created with the number of running
  application servers on the first runs.
- **All whitespace is removed from the `wsadmin` output before parsing.**
  A server name that contains whitespace is therefore published without it, and
  a value that contains a comma or a semicolon breaks the field split of that
  instance.
- **One agent per server name.** Two application servers with the same name in
  different cells, or in different nodes of the same cell, are delivered to the
  same agent, where their modules overwrite each other.

How the values are read:

- `Heapsize` and `Free memory` are the `heapSize` and `freeMemory` attributes of
  the instance JVM, in bytes.
- `Status` is the state that `AdminControl` reports for the server, such as
  `STARTED`; `OS` is the `os.name` property of the instance JVM, and `Proceso`
  is the process type.
- `Threadpool ActiveCount` and `Threadpool PoolSize` come from the statistics of
  the `WebContainer` thread pool. When those statistics do not provide the two
  expected values, both modules are published empty, which the console shows as
  unknown.
- `Numero de aplicaciones` counts the applications that the instance reports as
  running.

The per-instance modules carry no unit, no description and no threshold: create
the units, thresholds and alerts you need in the console. The two status modules
carry only the descriptions shown above. The module names are published in the
language used by the addon, so `Numero de aplicaciones` and `Free memory` keep
that spelling on both language versions of this page.

## Operate and troubleshoot

### Everyday operation

- The addon keeps no state between runs: every execution queries the cell at that
  moment, so it can be run manually at any time.
- In the agent plugin path, the Pandora FMS agent executes it according to the
  plugin schedule of its configuration. In the console path, Pandora FMS executes
  it according to the module interval.
- Each instance document is written to the `temp` folder as
  `<server>.<epoch>.data` and removed after a successful delivery. A failed
  delivery leaves the file in place: check that folder when deliveries fail
  repeatedly.
- Set `debug` to `1` while diagnosing. Without it the addon writes delivery
  errors, Tentacle output and temporary-file errors nowhere.

### Troubleshooting

- **`Websphere_status` is `1` but `Websphere_count` is `0`** — `wsadmin`
  returned nothing usable. Check that `wsadmin` and `jython` point to existing
  files, that the credentials can run administration queries, and that the
  `wsadmin` command works when you run it by hand on that host. The status
  module does not reflect the outcome of `wsadmin`.
- **`Pandora_websphere` appears with `0`** — the Tentacle delivery of an
  instance failed. Check that `tentacle_client` is installed and in `PATH`, that
  `tentacle_ip` names a reachable Tentacle server with `tentacle_port` open, and
  that `mode` is exactly `tentacle`. Run once with `debug` set to `1` to see the
  client message. The run stops at the first failure, so the remaining instances
  of that run are not delivered.
- **A line starting with `ERROR:` appears on standard output** — `mode` is
  `tentacle` and `tentacle_ip` is empty. The addon prints the message but does
  not stop; the delivery then fails as described above. In the agent plugin path
  that line is mixed into the module XML.
- **No agent appears for one instance** — that instance may have been consumed
  as part of the `wsadmin` banner, it may not be a `ManagedProcess`, or its name
  may contain a character that breaks the field split. Compare the cell
  inventory with `Websphere_count`.
- **`Can't locate PandoraFMS/PluginTools.pm` and no output** — the library is not
  next to the executable. Place `PluginTools.pm` in a `PandoraFMS` folder in the
  same directory as `pandora_websphere.pl`.
- **The addon prints `Websphere_status` and `Websphere_count` for an empty
  configuration** — a first argument that does not name an existing file is not
  read as a configuration file. The run continues with no values, `wsadmin` is
  not called and the count is `0`. Check the path of the configuration file.
- **A module shows unknown values while its agent exists** — one of the
  per-instance figures was empty, typically the thread pool statistics. Check the
  instance in the WebSphere console.
- **On AIX, or on any host where `temp` is not set, `Pandora_websphere` reports
  `0`** — the addon only defaults the temporary folder to `/tmp` on Linux.
  Elsewhere the document path resolves to the filesystem root and the write
  fails before the delivery starts. Set `temp` to a writable folder in the
  configuration file.

## Reference

### Configuration file keys

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `wsadmin` | Yes | — | Absolute path to the `wsadmin` client of the WebSphere profile. It is invoked with `-lang jython -user <user> -password <password> -f <jython>`. |
| `jython` | Yes | — | Path to the administration script passed to `wsadmin` with `-f`. A relative value is resolved from the working directory of the process. |
| `user` | Yes | — | WebSphere administrative user passed to `wsadmin` with `-user`. |
| `password` | Yes | — | Password passed to `wsadmin` with `-password`. Stored in plain text in this file. |
| `mode` | Yes | — | `tentacle` delivers every instance agent with the Tentacle client; any other non-empty value copies it into `local_folder`. `transfer_mode` is accepted as an alias when `mode` is absent. |
| `tentacle_ip` | Required when `mode=tentacle` | — | Address of the Tentacle server that receives the instance agents. |
| `tentacle_port` | No | `41121` | Port of the Tentacle server. |
| `tentacle_client` | No | `tentacle_client` | Tentacle client executable, resolved in `PATH` or given as an absolute path. |
| `tentacle_opts` | No | Empty | Extra options passed to the Tentacle client, separated by whitespace. |
| `local_folder` | Required when `mode` is not `tentacle` | — | Folder that receives the instance agent documents when they are not sent with Tentacle. |
| `temp` (`tmp`) | No | `/tmp` on Linux; none elsewhere | Folder where the instance agent documents are written before delivery. Without it on a system other than Linux, the path resolves to the filesystem root and the write fails. |
| `module_group` | No | Empty (no group) | Module group assigned to every generated module, including the two printed on standard output. The uppercase `MODULE_GROUP` takes precedence when both are present. |
| `module_interval` | No | Agent interval | Module interval assigned to every generated module. The uppercase `MODULE_INTERVAL` takes precedence when both are present. |
| `module_tag_list` | No | Empty (no tags) | Module tags assigned to every generated module, passed through as given. The uppercase `MODULE_TAG_LIST` takes precedence when both are present. |
| `debug` | No | `0` | `1` (or any numeric value greater than `0`) writes delivery errors, Tentacle output and temporary-file errors to standard error. |

Boolean keys are enabled by any numeric value greater than `0`. Unknown keys are
accepted and ignored.

### Command-line execution

```bash
perl pandora_websphere.pl <PATH_TO_CONFIG> [ -key value ... ]
```

| Condition | Behavior |
| --- | --- |
| The first argument names an existing file | It is read as the configuration file and removed from the argument list |
| The first argument names a file that does not exist | It is not read as a configuration file; the run continues from the defaults plus the flags |
| `-key value` pairs after the configuration file | Each one replaces the value of the same key |
| `--key value` or `-key=value` | Not recognized as that key: only one leading hyphen is removed, so the pair is stored under a key the addon ignores |
| A trailing argument without a value | Ignored |
| `-h`, `--help` | Not a help option; ignored, and the run continues |
| Exit status | `0` for a normal run, for a failed delivery and for configuration errors; a non-zero status means Perl could not load the addon or its library |

### Delivery behavior

| Situation | Result |
| --- | --- |
| `mode=tentacle` and the transfer succeeds | The temporary file is removed and the run continues with the next instance |
| `mode=tentacle` and the transfer fails | `Pandora_websphere` is printed with `0`, the temporary file stays in `temp`, and the run ends without `Websphere_status` or `Websphere_count` |
| `mode=tentacle` without `tentacle_ip` | An `ERROR:` line is written to standard output, the run continues, and the delivery fails as above |
| Any other non-empty `mode` | The document is copied into `local_folder`; a missing or unwritable folder makes the delivery fail as above |
| No `mode` and no `transfer_mode` | No delivery is attempted; the failure is reported only with `debug` enabled, the run ends as above |

### Generated modules

Modules of every instance agent. `<server>` is the WebSphere server name:

| Module name | Type | Value |
| --- | --- | --- |
| `<server>.Proceso` | `generic_data_string` | Process type of the instance, `ManagedProcess` |
| `<server>.Id` | `generic_data` | Process ID |
| `<server>.Status` | `generic_data_string` | State reported by `AdminControl`, such as `STARTED` |
| `<server>.OS` | `generic_data_string` | `os.name` of the instance JVM |
| `<server>.Heapsize` | `generic_data` | Heap size of the instance JVM, in bytes |
| `<server>.Free memory` | `generic_data` | Free heap memory of the instance JVM, in bytes |
| `<server>.Threadpool ActiveCount` | `generic_data` | Active count of the `WebContainer` thread pool |
| `<server>.Threadpool PoolSize` | `generic_data` | Size of the `WebContainer` thread pool |
| `<server>.Numero de aplicaciones` | `generic_data` | Number of applications running on the instance |

Modules of the agent that executes the addon:

| Module name | Type | Value | Generated when |
| --- | --- | --- | --- |
| `Websphere_status` | `generic_proc` | `1` | The run reaches its end |
| `Websphere_count` | `generic_data` | Number of instances published in the run | The run reaches its end |
| `Pandora_websphere` | `generic_proc` | `0` | A delivery fails; the run then stops |

### Addon identity

| Field | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.websphere` |
| Marketplace name | Pandora websphere |
| Addon version | `1.0` |
| Marketplace last update | 2025-06-27 |
| Marketplace package | `pandorafms.websphere.1.0.pspz2` |
| License | `One` (download limited to licensed users) |
| Marketplace type | Miscelaneus |
| Marketplace tags | applications, plugins, web |
| Author | Pandora FMS |
| Workflow | WebSphere application server monitoring, from a Pandora FMS agent with Tentacle delivery of the per-instance agents |
| Addon executable | `pandora_websphere.pl` |
| Configuration file | `pandora_websphere.conf` |
