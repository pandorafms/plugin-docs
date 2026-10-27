# IBM Z Series Mainframe

*Article last updated: 2026-10-26.*

## What it does

Pandora FMS Mainframe monitors IBM Z mainframes running z/OS through the RMF
Monitor III Data Portal. The addon has two parts that are installed and
configured separately:

- **The Mainframe Server** (`mf_server`), a service installed on a Linux host.
  It reads the RMF Data Portal over HTTP with basic authentication, turns the
  answer into Pandora FMS modules and delivers one agent document per
  mainframe. Nothing is installed on the mainframe and no agent runs on it.
- **The Z/OS console extension**, which adds **Operation → Z/OS** to the
  Pandora FMS console: a browser of the portal resource tree that generates the
  definition of the module you pick, a list of the mainframe agents and a
  module status view.

This is neither an agent plugin nor a server plugin registered per module. The
service is a licensed component with its own configuration directory, its own
license key, its own schedule and its own delivery path, and a single instance
collects for every mainframe you define in its configuration directory.

The addon is distributed through the Pandora FMS Marketplace as
`pandorafms.mainframe`. Its download is limited to licensed users.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.mainframe`, version `2.0` | Documented target | The Marketplace version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions. This is a published statement for the catalogue, not a test record for this addon |
| A Pandora FMS console with the Enterprise extensions directory | `Required` | The console extension installs under `enterprise/extensions` and registers its menu option through the Enterprise extension interface |
| A Pandora FMS license key | `Required` | The service logs an invalid-license error and stops when `pandora_license` does not hold a valid key |
| An operating system named `Mainframe` in the console | `Required` | Agents are published with `os_name` `Mainframe`, and both console views select agents by that operating system name |
| The RMF Monitor III Data Portal, reachable over HTTP with basic authentication | `Required` | Every dataportal module reads `gpm/perform.xml` from the portal |
| Network access from the service host to the portal and to the Pandora FMS Tentacle port | `Required` | The service collects over HTTP and delivers with the Tentacle client |
| A Linux host with systemd | `Required` | The installer writes a systemd unit and enables it |
| RHEL, CentOS, Rocky Linux and AlmaLinux 8, 9 and 10, and Ubuntu 22.04 | `Not validated` | The installer recognises these releases and any other distribution prints `WARNING: Not supported OS found`. No test record exists |
| z/OS versions | `Not validated` | The legacy guide states that the addon was tested on z/OS 1.10 and 1.13; no test record supports that claim |
| RMF Data Portal versions | `Not validated` | No version matrix is recorded for this addon |

### Requirements

1. **An IBM Z mainframe** with RMF Monitor III active and the RMF Data Portal
   serving the reports you want to collect. The portal must accept HTTP basic
   authentication and answer the `gpm` resources described in
   [Portal requests](#portal-requests).
2. **A Linux host with systemd** for the service. It can be the Pandora FMS
   server host or any other host that reaches both the portal and the Tentacle
   server.
3. **A Pandora FMS console** with the Enterprise extensions directory, to
   install the Z/OS extension and to receive the agent data.
4. **A Pandora FMS license key**, configured in the service.
5. **Network access**: HTTP to the portal, and the Tentacle port (`41121` by
   default) to the Pandora FMS server, in both directions when you use remote
   configuration.

### Install the Mainframe Server

Unpack the package and run the installer as `root` from the directory it
creates:

```bash
tar zxf pandorafms_mf_server-<version>.tar.gz
cd mf_server
sudo ./mf_server_installer --install
```

The installer:

- copies the `mf_server` executable and the Tentacle client to `/usr/bin`;
- copies `mf_server.conf` and `mf_server.env` to `/etc/pandora`;
- creates the agent configuration directory `/etc/pandora/conf`;
- writes `/etc/systemd/system/mf_server.service`, reloads the systemd
  configuration and enables the unit.

It does **not** start the service, and it does not touch the console. Edit
`/etc/pandora/mf_server.conf` first ([Configure](#configure)), then start it:

```bash
sudo systemctl start mf_server
```

The unit runs the service as `root`, restarts it if it stops and expects it to
detach into the background, so `daemon 1` is required.

### Install the Z/OS console extension

The package ships the console extension in the `extensions` directory. Copy it
into the Enterprise extensions directory of the console:

```bash
sudo cp -r ./extensions/* <PANDORA_CONSOLE>/enterprise/extensions/
```

`<PANDORA_CONSOLE>` is the console installation directory. After the copy,
**Operation → Z/OS** appears in the console menu; the views it opens require the
read-agents privilege (`AR`).

<!-- SCREENSHOT NEEDED: Operation menu of the Pandora FMS console with the Z/OS entry highlighted. -->

The extension is not installed by the service installer and is not removed by
its uninstaller: it is a console file copy that you manage separately.

### Create the Mainframe operating system

The service publishes every agent with the operating system `Mainframe`. If the
console does not have that operating system, create it in
**Administration → Setup → OS** before starting the service; the Z/OS views
select agents by that name, so a missing operating system leaves them empty
even when the agents exist.

## Configure

Configuration is split between the service and the console:

- `/etc/pandora/mf_server.conf` holds the settings shared by every mainframe.
- `/etc/pandora/conf/*.conf` holds one file per mainframe: the agent, its portal
  credentials and its module blocks.
- The console holds what Pandora FMS does with the modules: thresholds set in a
  module block, and the remote configuration of each agent.

### Server configuration file

`/etc/pandora/mf_server.conf` uses one `token value` pair per line. Lines
starting with `#` are comments, surplus white space is trimmed, an unknown
token is stored without complaint and the last occurrence of a repeated token
wins. Paths must be absolute: the service changes to `/tmp` when it detaches
into the background.

This excerpt contains what you normally have to set:

```ini
# Pandora FMS license key: the service does not start without it.
pandora_license <PANDORA_LICENSE_KEY>

# Tentacle address of the Pandora FMS server, used to deliver the agents.
server_ip <PANDORA_FMS_SERVER>

# Console group for every mainframe agent (must exist in the console).
group Servers

# Directory scanned for one configuration file per mainframe.
agent_conf_dir /etc/pandora/conf
```

Every token, its built-in default and the value the shipped file sets are in
[Server configuration tokens](#server-configuration-tokens). Restart the
service after editing the file; the service does not watch it.

### Register a mainframe agent

Create one file per mainframe in `/etc/pandora/conf`. The package ships
`agent.conf.sample` as a starting point:

```bash
sudo cp agent.conf.sample /etc/pandora/conf/<MAINFRAME_AGENT_NAME>.conf
sudo chmod 600 /etc/pandora/conf/<MAINFRAME_AGENT_NAME>.conf
```

```ini
agent_name <MAINFRAME_AGENT_NAME>
dataportal_url http://<RMF_DATA_PORTAL_HOST>:8803
dataportal_user <USERNAME>
dataportal_pass <PASSWORD>

module_begin
module_plugin dataportal
module_resource <RESOURCE>
module_metric <METRIC_ID>
module_end
```

Key points:

- The file must end in `.conf`. On start the service renames it to
  `<md5 of the agent name>.conf`, which is also the name the remote
  configuration uses. That md5 name is the file you keep editing afterwards.
- `agent_name`, `dataportal_url`, `dataportal_user` and `dataportal_pass` are
  mandatory in every file, including files that only define storage modules.
- The service reads the directory only at start. A new file, a new module or an
  edited file needs `sudo systemctl restart mf_server`; only changes made
  through the console remote configuration are picked up while it runs.
- The agent interval is not per agent: every agent takes `agent_interval` from
  the service configuration.

### Module definitions

A module block starts with `module_begin`, ends with `module_end` and holds
`module_<token> value` lines. A block without `module_plugin` is accepted and
never executed, so it is the first thing to check when a module produces no
data. The console browser writes the block for you
([Build a module with the RMF Data Portal Browser](#build-a-module-with-the-rmf-data-portal-browser));
the full token list is in
[Module definition tokens](#module-definition-tokens).

Only a few tokens have an effect on what Pandora FMS receives: the plugin
selector, the resource and metric (or the dataset URL and record length), the
collection interval and the four thresholds with their two inverse flags.
`module_type`, `module_unit`, `module_description`, `module_group` and the rest
of the `module_*` tokens are parsed but do not reach the published modules;
configure those values in the console instead.

### Build a module with the RMF Data Portal Browser

The browser walks the portal resource tree and returns a ready-to-paste block
for the metric you choose.

1. Open **Operation → Z/OS** and the **RMF Data Portal Browser** tab.
2. Fill in the portal address, the user, the password and the depth, and click
   **Browse**. An address without a port gets `:8803`.
3. The tree starts at the portal root: the first level is a sysplex, the second
   the MVS images, then the I/O subsystems and processors.
4. Click the eye icon of a resource to list its metrics.
5. Click a metric to open a dialog with its module block:

    ```text
    module_begin
    module_plugin dataportal
    module_description <DESCRIPTION FROM THE PORTAL>
    module_type generic_data
    module_resource <RESOURCE>
    module_metric <METRIC_ID>
    module_end
    ```

6. Copy the block into the agent configuration: either the agent file on disk
   and a restart, or the agent remote configuration in the console
   (**Operation → Z/OS → Mainframes**, edit icon), which the running service
   applies by itself.

<!-- SCREENSHOT NEEDED: RMF Data Portal Browser tab with the address, user, masked password, depth fields and the Browse button. -->

<!-- SCREENSHOT NEEDED: Metric list of one resource with the module block dialog open. -->

The browser does not store the portal credentials: they are typed again on
every visit, and they travel from the browser to the console in each request.

### Storage modules

The `storage` plugin reads a dataset over FTP(S) instead of the HTTP portal,
converts it from EBCDIC and publishes four modules per storage group found in
it. The dataset is fetched from `module_url`; the RMF portal is not involved in
that request:

```text
module_begin
module_plugin storage
module_url ftp://<FTP_HOST>/<DATASET>
module_lrecl 80
module_end
```

Each record of the dataset must contain, in this order, `P=` followed by the
storage group, `Es=` followed by the capacity, `Libre=` followed by the free
percentage and `T=` followed by the description. `module_lrecl` is the record
length and defaults to `80`.

The `storage_sms` plugin reads a dataset with the SMS totals and publishes nine
fixed modules. Each total must appear as `Gb.` followed by the label — `Usado
SMS`, `Reservado SMS`, `Usado No SMS` or `Reservado No SMS` — one or more
non-digit characters and the numeric value:

```text
module_begin
module_plugin storage_sms
module_url ftp://<FTP_HOST>/<DATASET>
module_lrecl 80
module_end
```

The labels are literal: a dataset in another language produces no match, and
the nine modules are then published with `0`.

### Delivery to Pandora FMS

The service delivers every document through the Tentacle client, or copies it
to a local data directory:

| `transfer_mode` | What the service does | Settings that matter |
| --- | --- | --- |
| `tentacle` (default) | Runs `tentacle_client` against `server_ip:server_port` | `tentacle_client`, `server_ip`, `server_port`, optional `server_opts` |
| `local` | Copies the document to `server_path` | `server_path`, which must be writable |

Any other value is not supported and the document is not delivered. With
`xml_buffer 1` a document that could not be delivered stays in `temporal` and is
retried on every pass, until the free space of that directory falls below
`temporal_min_size` bytes.

### License

The service requires a Pandora FMS license key in `pandora_license`:

- Without a key, or with a key that fails validation, the log reports
  `Invalid license` and the service exits.
- The key's limit is enforced against the number of agents in
  `agent_conf_dir`, or against the number of module blocks, depending on the
  license mode. Above the limit the service exits; an expired client license
  only logs a warning, while an expired trial license stops it.
- The service reports the license holder on start (`Licensed to: ...`) and
  always logs `Remote configuration enabled.`, whatever `remote_config` says.

### Credentials and transport

- The portal password is stored in clear text in the agent file. Keep the file
  readable only by `root` (`chmod 600`), together with the license key in
  `mf_server.conf`.
- The portal credentials travel in the `Authorization` header of every HTTP
  request. With an `http://` portal they are not encrypted, so keep the portal
  on a trusted network or publish it through TLS and use an `https://`
  `dataportal_url`.
- The console browser disables TLS certificate verification. Do not expose the
  console over plain HTTP or to untrusted networks, because the portal user and
  password pass through it on every browse.
- Use a dedicated portal user with read access only. No official source
  identifies a narrower role for the RMF Data Portal, and the addon performs no
  write operation against it.

## Verify

1. **The service is running.** `systemctl status mf_server` reports the unit as
   active. If it is not, read the log: the unit restarts the service, so a
   failure repeats every few seconds.
2. **The log shows a full start.** `/var/log/mf_server.log` is rewritten on
   every start. A successful start contains these messages in order:

    - `Configuration file loaded.`
    - `Reading agent configuration directory.`
    - one `Loading file <name>.conf.` per agent file
    - `Valid enterprise license found.` and `Licensed to: <holder>`
    - `modules: <n> Threads: <t> modules per thread: <m>`
    - one `Launched thread <id>.` per thread
    - `Waiting for data...`

    With no agent file the module count is `0`: the service runs and delivers no
    agent data.

3. **The mainframe appears in the console.** **Operation → Z/OS →
   Mainframes** lists one row per agent, with the `Mainframe` operating system
   icon and a recent last contact. The agent also appears in the regular agent
   list.

    <!-- SCREENSHOT NEEDED: Mainframes tab of the Z/OS extension with one demo agent and no real host data. -->

4. **The modules carry data.** **Operation → Z/OS → Metrics** shows the modules
   of every mainframe agent with their status, data and timestamp. The
   **Monitor status** filter starts at **Not init**, so set it to **All** to see
   modules that are already receiving data.

    <!-- SCREENSHOT NEEDED: Metrics tab with the Monitor status filter set to All and a few modules with data. -->

5. **The portal answers.** From the service host, repeat one of the requests the
   service makes, with the same credentials, and check that the XML comes
   back. The service wraps the resource in double quotes, as in the example:

    ```bash
    curl -s -u <USERNAME>:<PASSWORD> \
      'http://<RMF_DATA_PORTAL_HOST>:8803/gpm/perform.xml?resource="<RESOURCE>"&id=<METRIC_ID>'
    ```

## Understand the results

Each mainframe becomes one top-level agent in the group taken from the server
configuration, with the operating system `Mainframe` and the interval of
`agent_interval`. Every collection cycle produces one agent document per module
block: the service reads the report, converts each row or total into a module
and delivers the document. Nothing accumulates locally beyond the retry buffer.

**Dataportal modules.** Each row of the report becomes a module. The name
concatenates the resource, a space, the metric identifier and the metric or row
description, with no separator between the last two, so names look technical
rather than descriptive. The type is always `generic_data` and the description
is the one the portal publishes for that metric or row; the thresholds of the
block are copied to every module it generates. A report without rows produces a
document without modules: the agent keeps its last contact, but nothing new is
published. The agent description is replaced by the description of the metric
on every cycle.

**Storage modules.** Four modules per storage group, in GB, with the thresholds
of the block only on `STORGRP % free <group>`.

**SMS modules.** Nine fixed totals in GB, all of them with the thresholds of the
block. The addon maps the dataset labels literally: `Used` is the `Usado`
amount, `Free` is the `Reservado` amount and `Available` is their sum. A value
named `Free` therefore holds reserved space, not free space.

**Failure behaviour.** When the portal does not answer or answers with an error,
the log receives the response body and the cycle publishes no modules for that
block. The service then retries on the next scheduled run; no state is kept.

## Operate and troubleshoot

### Service control

```bash
sudo systemctl start mf_server
sudo systemctl status mf_server
sudo systemctl stop mf_server
sudo systemctl restart mf_server
tail -f /var/log/mf_server.log
```

The log file is truncated on every start, so a restart erases the previous run.
Copy it before restarting if you need the history.

The uninstaller removes the unit, the executables, `/etc/pandora/mf_server.conf`,
`/etc/pandora/mf_server.env` and the whole directory `/etc/pandora/conf`. On a
host that also runs other Pandora FMS components, back that directory up before
running `mf_server_installer --uninstall`.

### Run in the foreground

Set `daemon 0` in the service configuration and run it as `root`:

```bash
sudo /usr/bin/mf_server /etc/pandora/mf_server.conf
```

The service still writes to `log_file`, not to standard output, and it does not
detach, so the process stays in the terminal until you interrupt it.
Remember to restore `daemon 1` before starting the systemd unit again: the unit
expects the service to detach.

With no argument, or with more than one, the service prints a usage summary and
exits. That summary still lists `-r` and `-m`; neither option is accepted, and
the RMF Data Portal Browser in the console replaces both.

### Known limitations of this version

- **Every module is numeric.** The published type is `generic_data` for all
  modules, whatever `module_type` says, so a report that returns text (partition
  names, status text) cannot become a usable module value.
- **Most `module_*` tokens do not reach the console:** `module_type`,
  `module_unit`, `module_description`, `module_group`, `module_tags`,
  `module_disabled`, `module_quiet`, string thresholds, instructions and the
  flap-detection tokens are parsed and ignored. A block sent with
  `module_group` arrives with an empty group. Configure these values in the
  console.
- **`timeout` in `mf_server.conf` is inert.** The HTTP timeout of the portal
  requests is the agent token `timeout` (`5` seconds by default) and the FTP
  timeout is `ftp_timeout`.
- **`secondary_mode` and `secondary_server_ip` are inert.** They only add a line
  to the log; no secondary delivery is implemented.
- **The service's own remote configuration does not apply.** Only agent
  configuration files are exchanged with the console; `mf_server.conf` is
  always the file on disk.
- **The license tolerance is not applied to the number of agents.** In agent
  mode the service stops as soon as the agent count exceeds the key limit; the
  ten per cent margin the code computes is never used and the warning line is
  unreachable. In module mode the margin is applied and the warning appears
  between the limit and the margin.
- **With `xml_buffer 1` the service scans the whole `temporal` directory** and
  sends and deletes every `*.data` file it finds there, not only its own. Keep
  `temporal` private: the shipped value of `temporal` is `/tmp` and the shipped
  value of `xml_buffer` is `0`.
- **The SMS dataset labels are Spanish** (`Usado`, `Reservado`). Any other
  language yields nine zero values without an error.
- **The default portal port is only applied by the browser.** The service uses
  the scheme default when `dataportal_url` has no port, so write `:8803`
  explicitly.
- **The browser's agent selector uses a fixed operating system identifier**
  while the tables filter by the operating system name `Mainframe`. When the
  console assigns a different identifier, the **Agent name** selector can list
  no agents while the table still shows them.
- **The Metrics tab starts filtered by Not init**, so a healthy agent shows no
  rows until you change **Monitor status** to **All**.
- **`--destdir` does not relocate the systemd unit**, which is always written to
  `/etc/systemd/system`.
- **The systemd unit declares `PIDFile=/var/run/mf_server.pid`**, but the service
  never creates that file. When `systemctl status` does not show the process,
  look for it with `ps`. The uninstaller removes the path anyway.

### Troubleshooting

| Symptom | Cause and check |
| --- | --- |
| The service does not start and the log ends with `Invalid license` | `pandora_license` is empty or invalid. Set a valid key and restart |
| The log ends with `Error opening file .../mf_server.conf` | The unit passes `/etc/pandora/mf_server.conf`; the file is missing, or the service was started with another path. Reinstall or fix the path |
| The log ends with `Error opening directory .../conf` | `agent_conf_dir` does not exist or is not readable by `root` |
| `Agent name not defined in file <file>!` | The agent file has no `agent_name`. The file is not renamed and the agent is skipped |
| `Dataportal not configured in file <file>` | One of `dataportal_url`, `dataportal_user` or `dataportal_pass` is missing |
| `Invalid module definition in: <file>` | A block has neither `module_metric` and `module_resource` nor `module_plugin` |
| The agent exists in the console but has no modules | The blocks have no `module_plugin`, or the report returned no rows. Check the log and repeat the portal request |
| `Error sending file '<file>'` | Delivery failed: check `server_ip`, `server_port`, the Tentacle client path and the firewall. With `xml_buffer 1` the document is retried |
| Modules stop updating while the service runs | The portal answers with an error or not at all. The log holds the response body; repeat the request with `curl` |
| The RMF browser tree is empty | The port is wrong, the credentials are refused, or **Depth** is empty. An address without a port gets `:8803` |
| A module name looks like `RESOURCE METRICID...` | That is the naming rule of dataportal modules, not an error |
| Data appears at a different time than in the portal | The service timestamps each document with the collection time. Use `autotime 1` to let Pandora FMS stamp it on reception |

## Reference

### Server configuration tokens

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `agent_conf_dir` | Yes | `./conf` (shipped: `/etc/pandora/conf`) | Directory scanned for one `*.conf` file per mainframe. Use an absolute path |
| `group` | No | empty (shipped: `Servers`) | Console group for every agent. It must exist; an agent file may override it |
| `agent_interval` | No | `300` | Agent interval in seconds, shared by every agent and sent in every document |
| `conf_interval` | No | not set (shipped: `300`) | Seconds between remote-configuration checks. Without a value the check runs on every pass of the main loop |
| `daemon` | No | not set (shipped: `1`) | `1` detaches into the background and writes standard streams to `/dev/null`. Any other value or absence keeps the service in the foreground, which the systemd unit does not expect |
| `log_file` | Yes | `/var/log/mf_server.log` | Log file, truncated on every start |
| `module_interval` | No | `300` | Default collection interval, in seconds, for blocks that do not set `module_interval` |
| `module_threads` | No | `2` (shipped: `5`) | Threads that run the blocks. Blocks are distributed evenly |
| `pandora_license` | Yes | empty (shipped: commented out) | Pandora FMS license key |
| `remote_config` | No | `0` (shipped: `1`) | `1` enables the remote configuration exchange for every agent that does not override it |
| `server_ip` | Yes | `127.0.0.1` | Tentacle server address, used to deliver and to receive files |
| `server_port` | No | `41121` | Tentacle port |
| `server_path` | Required for local delivery | `/var/spool/pandora/data_in` | Destination directory of `transfer_mode local` |
| `temporal` | Yes | `/tmp` | Directory where documents are written before delivery and where the buffer is retried. Use a private directory |
| `tentacle_client` | Yes for Tentacle delivery | `/usr/bin/tentacle_client` | Full path to the Tentacle client |
| `timeout` | No | — | Accepted and stored, never used. The portal timeout is the agent token `timeout` |
| `ftp_timeout` | No | `10` | Timeout in seconds for the FTP(S) requests of storage modules |
| `transfer_mode` | No | `tentacle` | `tentacle` delivers with the Tentacle client; `local` copies to `server_path`. Any other value is unsupported |
| `xml_buffer` | No | `1` (shipped: `0`) | `1` keeps an undelivered document in `temporal` and retries it on every pass |
| `temporal_min_size` | No | `1` (shipped: `1024`) | Free bytes that `temporal` must have for the buffer to keep a failed document. Below that, the document is deleted |
| `keepalive` | No | `300` | Seconds between the `server_data` documents the service sends to identify itself |
| `startup_delay` | No | `2` | Seconds each collection thread waits after start |
| `send_udelay` | No | `1000` | Microseconds between remote-configuration requests |
| `server_name` | No | host name | Name sent in the `server_data` document |
| `server_opts` | No | empty | Extra options passed to the Tentacle client, without validation |
| `secondary_mode`, `secondary_server_ip` | No | `0`, unset | Accepted and echoed in the log only. No secondary delivery is implemented |

### Agent configuration tokens

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `agent_name` | Yes | — | Agent name in the console. The file is renamed to the md5 of this name on start |
| `dataportal_url` | Yes | — | Portal URL. Only scheme, host and port are used: the service always requests `<scheme>://<host>:<port>/gpm/...`, so a path is discarded and the port must be written explicitly |
| `dataportal_user` | Yes | — | Basic authentication user for the portal |
| `dataportal_pass` | Yes | — | Password for that user. Stored in clear text |
| `description` | No | `Mainframe agent` | Agent description. Dataportal blocks replace it with the metric description on every cycle |
| `group` | No | the server `group` | Agent group |
| `remote_config` | No | the server `remote_config` | Per-agent remote configuration switch |
| `timeout` | No | `5` | HTTP timeout in seconds for the portal requests of this agent |
| `encoding` | No | `UTF-8` | Encoding declared in the document |
| `autotime` | No | `0` | `1` omits the document timestamp, so Pandora FMS stamps it on reception |
| `custom_id`, `url_address` | No | empty | Sent as `custom_id` and `url_address` |
| `address` | No | not sent | Agent address, sent only when defined |
| `parent_agent_name` | No | not sent | Parent agent, sent only when defined |
| `os_name` | No | `Mainframe` | Agent operating system. Change it only together with the console views |
| `os_version` | No | empty | Agent operating system version |
| `include <file>` | No | — | Merges agent tokens from another file. Module blocks are not read from included files. Use an absolute path |

### Module definition tokens

A block is delimited by `module_begin` and `module_end`. Only these tokens
change what the service collects or publishes:

| Token | Applies to | Description |
| --- | --- | --- |
| `module_plugin` | All | `dataportal`, `storage` or `storage_sms`. Without it the block is loaded and never executed |
| `module_resource` | `dataportal` | Resource label, as returned by the portal |
| `module_metric` | `dataportal` | Metric identifier, as returned by the portal |
| `module_url` | `storage`, `storage_sms` | `ftp://` or `ftps://` URL of the dataset |
| `module_lrecl` | `storage`, `storage_sms` | Record length of the dataset. Default `80` |
| `module_interval` | All | Collection interval of the block in seconds, default `module_interval` from the service |
| `module_min_warning`, `module_max_warning` | All | Warning thresholds, copied to every module of the block |
| `module_min_critical`, `module_max_critical` | All | Critical thresholds, copied to every module of the block |
| `module_warning_inverse`, `module_critical_inverse` | All | Inverse threshold flags, copied to every module of the block |

These tokens are accepted and parsed, and have no effect on the published
modules: `module_type`, `module_unit`, `module_description`, `module_group`,
`module_tags`, `module_disabled`, `module_quiet`, `module_custom_id`,
`module_min_ff_event`, `module_ff_interval`, `module_str_warning`,
`module_str_critical`, the instruction tokens and `module_postprocess`.

### Generated modules

**Dataportal blocks** publish one `generic_data` module per report row, named
`<RESOURCE> <METRIC_ID><DESCRIPTION>`, where the trailing description is the row
label for a list report or the metric description otherwise. Rows without a
value are skipped.

**Storage blocks** publish four `generic_data` modules per storage group found
in the dataset:

| Module | Unit | Value |
| --- | --- | --- |
| `STORGRP available <group>` | `GB` | `Es=` value: capacity of the storage group |
| `STORGRP % free <group>` | none | `Libre=` value. The only storage module that carries the block thresholds |
| `STORGRP %used <group>` | none | `100` minus the `Libre=` value |
| `Free Space (DASD) - <group>` | `GB` | Capacity multiplied by the free percentage divided by `100` |

**SMS blocks** publish nine `generic_data` modules in `GB`, all of them with the
block thresholds:

| Module | Value |
| --- | --- |
| `Total Space (SMS) - Available` | `Usado SMS` plus `Reservado SMS` |
| `Total Space (SMS) - Used` | `Usado SMS` |
| `Total Space (SMS) - Free` | `Reservado SMS` |
| `Total Space (NOSMS) - Available` | `Usado No SMS` plus `Reservado No SMS` |
| `Total Space (NOSMS) - Used` | `Usado No SMS` |
| `Total Space (NOSMS) - Free` | `Reservado No SMS` |
| `Total Space (DASD) - Used` | `Usado SMS` plus `Usado No SMS` |
| `Total Space (DASD) - Free` | `Reservado SMS` plus `Reservado No SMS` |
| `Total Space (DASD) - Available` | Sum of the four amounts |

### Portal requests

The service and the console browser read these resources of the RMF Data
Portal. The service sends basic authentication on each of them.

| Request | Used by | Purpose |
| --- | --- | --- |
| `gpm/perform.xml?resource="<resource>"&id=<metric>` | Service | Metric report of one resource |
| `gpm/root.xml` | Browser | Root of the resource tree |
| `gpm/contained.xml?resource=<resource>` | Browser | Children of a tree node |
| `gpm/listmetrics.xml?resource=<resource>` | Browser | Metrics available for a resource |

### Installer options

| Option | Effect |
| --- | --- |
| `--install` | Installs the service, the Tentacle client, the configuration files, the agent directory and the systemd unit, and enables the unit |
| `--uninstall` | Stops and disables the unit, then removes it with the executables, `/etc/pandora/mf_server.conf`, `/etc/pandora/mf_server.env`, `/var/run/mf_server.pid` and the whole `/etc/pandora/conf` directory |
| `--destdir <dir>` | Installs everything under `<dir>` except the systemd unit, which is always written to `/etc/systemd/system` |
| `--force-perl` | Reinstalls the bundled runtime even when a newer one is already present |
| no option, or an unknown one | Prints the usage summary and exits |

### Console extension

| Surface | Detail |
| --- | --- |
| Menu | **Operation → Z/OS**, page title `Z/OS Monitoring` |
| Tabs | `RMF Data Portal Browser`, `Mainframes`, `Metrics` |
| Required privilege | `AR` (read agents) for the browser and the mainframe list; `AR` or `AW` for the module view; `AW` to see the remote-configuration icon |
| Mainframes tab | Agents whose operating system is `Mainframe`, top level and enabled: agent, description, OS, interval, group, modules, status, alerts, last contact, and the remote-configuration edit icon |
| Metrics tab | Modules of the mainframe agents, filterable by agent name, module name, monitor status and a free-text search; columns for agent, type, module name, interval, status, graph, warning, data and timestamp |

Browser fields:

| Field | Detail |
| --- | --- |
| **RMF IP address** | Portal host, with or without port. `:8803` is appended when no port is written |
| **Username** | Basic authentication user |
| **Password** | Password for that user. Masked in the form and not stored |
| **Depth** | Maximum tree depth. The form starts at `3`; an empty value stops the tree immediately |
| **Browse** | Builds the tree. The request can be slow on large trees |
| **Search options** | Text search across the tree, with first, previous, next and last match, plus expand and collapse |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.mainframe` |
| Name | IBM Z Series Mainframe |
| Version | `2.0` |
| Category | Miscelaneus |
| License | One |
| Availability | Download limited to licensed users |
| Marketplace last update | 2026-07-08 |
| Package | `pandorafms.mainframe.2.0.zip` |
| Service version reported in the agent documents | `7.0 (Build 191107)` |

The service version in the last row is its own build identifier, reported in the
agent documents and in the usage summary. It is independent of the addon
version of the Marketplace entry.
