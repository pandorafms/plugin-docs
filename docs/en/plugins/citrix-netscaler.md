# Citrix NetScaler monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The plugin monitors a Citrix NetScaler (ADC) appliance from Pandora FMS through
the NITRO REST stat API. Each run asks the appliance which statistic objects it
exposes, reads the ones listed in the configuration file and creates Pandora FMS
agents from the result: one agent per object returned for each configured
service, plus a status module on the main agent.

The plugin is a standalone executable run once per invocation and then exits. It
takes a single configuration file, keeps no state between runs, and starts no
service. It is not a Discovery plugin: Pandora FMS does not drive it from a task.

The agents are never printed for an agent to collect. Every run builds Pandora
FMS agent XML documents and delivers them, either through Tentacle or by copying
them into a local data folder. The only Pandora FMS modules the plugin produces
on standard output are the ones of a failed run (see [Verify](#verify)).

Nothing is installed on the appliance. The plugin reads statistics with HTTP GET
requests authenticated by NITRO headers, so the account only needs read access.

The module catalogue is not fixed. The modules of an object are the statistic
fields the appliance returns for it, filtered by the list in the configuration
file, so the same plugin adapts to the fields a device or firmware exposes.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its entries are compatible with Pandora FMS NG 784 and later versions; it is a catalogue-wide statement covering this addon, not a test record |
| A Citrix NetScaler appliance exposing the NITRO stat API at `ns_url` | `Required` | The catalogue request targets `<ns_url>`, and each service read appends `/<service>` |
| A NetScaler account allowed to read the stat API | `Required` | The credentials travel in the `X-NITRO-USER` and `X-NITRO-PASS` headers of every request |
| A Perl runtime providing `LWP::UserAgent` and `JSON` | `Required` | The plugin does not start without them |
| Network access from the plugin host to the appliance | `Required` | Statistics are read over HTTP or HTTPS from that host |
| A writable temporary directory | `Required` | Each agent document is written to `temp` before it is delivered |
| A delivery destination: the Pandora FMS Tentacle service, or a writable local data folder | `Required` | `mode` selects one of the two |
| NetScaler models and firmware versions | `Not validated` | No model or firmware matrix has been recorded for this addon. The legacy guide names `NSMPX-10500` as the platform it was tested on; no current record confirms it |
| Operating system of the host that runs the plugin | `Not validated` | No operating system has been recorded for this version |

### Requirements

1. **A Citrix NetScaler appliance** whose NITRO stat API answers on the
   configured URL, reachable from the host that runs the plugin.
2. **An account on the appliance** allowed to read the statistics of the
   services you want to monitor. Use a dedicated read-only account.
3. **A host to run the plugin** with the Perl runtime and the two modules listed
   in [Compatibility](#compatibility).
4. **A destination for the generated agents**: the Pandora FMS Tentacle service,
   with the Tentacle client available, or a local data folder that the Pandora
   FMS server reads.
5. **Write access** to the `temp` directory and, in local mode, to
   `local_folder`.

### Install the plugin

Download the addon from the Pandora FMS Marketplace entry, which is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.citrix_netscaler](https://marketplace.pandorafms.com/entries/pandorafms.citrix_netscaler)

The addon consists of the `citrix_netscaler.pl` executable and its configuration
file `citrix_netscaler.conf`. Copy both to the host that will run the plugin and
make the executable runnable. The configuration file can live anywhere, because
every execution passes its path as the only argument.

The sample file ships with example hosts, an example account and example Tentacle
and API addresses. Replace them before running the plugin (see
[Configure](#configure)), and restrict the file permissions: it holds the
appliance password in plain text.

## Configure

The plugin takes one argument, the path of its configuration file, and no
command-line options:

```bash
./citrix_netscaler.pl <PATH_TO_CONFIG>
```

The equivalent explicit form, useful when the executable bit is not set or the
interpreter must be selected by hand:

```bash
perl citrix_netscaler.pl <PATH_TO_CONFIG>
```

There is no `-h` or `--help` option: a run without any argument prints the usage
summary and exits with status `1`.

### Configuration file format

The file is plain text with one `key = value` per line:

- A blank line is ignored.
- A line whose first character is `#` is a comment. A `#` anywhere else is part
  of the value, so trailing comments are not supported.
- The key and the value are trimmed of leading and trailing blanks.
- A key repeated with a scalar value keeps the last occurrence.
- `ns_services` is the exception: every occurrence adds one service.
- The parser accepts any key. A key the plugin does not read has no effect (see
  [Accepted but not applied](#accepted-but-not-applied)).
- A line without `=` is stored with an empty value instead of being reported.

This is a complete configuration for a first run that delivers with Tentacle:

```ini
ns_url = https://<NETSCALER_HOST>/nitro/v1/stat/
ns_user = <USERNAME>
ns_pass = <PASSWORD>

ns_services = system;0
ns_services = lbvserver;1

modules_list = state,status,cpuusage,memusagepcnt

agent_name = netscaler-main
agent_interval = 300

mode = tentacle
tentacle_ip = <PANDORA_FMS_URL>
tentacle_port = 41121
```

The same collection copied into a local data folder instead:

```ini
ns_url = https://<NETSCALER_HOST>/nitro/v1/stat/
ns_user = <USERNAME>
ns_pass = <PASSWORD>

ns_services = system;0
ns_services = lbvserver;1

agent_name = netscaler-main

mode = local
local_folder = /var/spool/pandora/data_in
```

### Connection and credentials

- `ns_url` is the base URL of the stat API, for example
  `https://<NETSCALER_HOST>/nitro/v1/stat/`. The plugin requests that URL once to
  obtain the catalogue of statistic objects, then appends `/` and the service
  name for each read, so the value must include the API path and not only the
  host.
- Both `http://` and `https://` URLs are accepted. Use HTTPS: over plain HTTP the
  headers carrying the credentials and the collected statistics travel
  unencrypted.
- The credentials are sent as the `X-NITRO-USER` and `X-NITRO-PASS` headers on
  every request.
- The plugin exposes no certificate option. An HTTPS device certificate must be
  trusted by the host that runs the plugin, including any private certification
  authority in its trust store.
- `lwp_timeout` sets the HTTP request timeout in seconds. It is absent from the
  sample file, and with no value the plugin applies no explicit timeout, so a
  silent appliance can hold the run for as long as the HTTP client waits.
- The HTTP client honours the `http_proxy`, `https_proxy` and `no_proxy`
  environment variables.
- `ns_pass` is stored in plain text. Restrict the file to the user that runs the
  plugin, for example with `chmod 600`, and do not keep it in a shared directory.

### Services and modules to collect

`ns_services` selects what to read. Each line has the form
`ns_services=<service>;<value>`:

- `<service>` is the name of a NITRO statistic object, such as `system` or
  `lbvserver`. It is compared with the catalogue the appliance returns, and a
  service the appliance does not list is skipped without an error.
- `<value>` is `1` or `0` and only controls the parent of the generated agents:
  with `1` they declare the configured `agent_name` as their parent, with `0`
  (or with no value) they are generated without a parent.

There is no default service. A configuration file without any `ns_services` line
reads the catalogue and nothing else, so the run only reports the status module
on the main agent.

`modules_list` filters the statistic fields of each object. It is a
comma-separated list of exact, case-sensitive field names, without blanks:

```ini
modules_list = state,status,cpuusage,memusagepcnt
```

Each name in the list becomes a module only when the object returns that field.
The sample file suggests `state,status,vbshealth,primaryaddress,cpuusage,disk1avail,memusagepcnt,powersupply2status`;
adjust the list to the fields your appliance and firmware actually return. When
`modules_list` is absent or empty, the filter is disabled and every field of the
object becomes a module, including its name field.

The filter applies to the stat fields of the object itself. The stat-bindings
modules described in [Understand the results](#understand-the-results) are not
filtered: they are generated for every service the appliance answers with a list
of objects, whatever its value.

`ns_service_prefix` prepends a fixed text to the name of the agents generated for
the objects of a multi-instance service, which helps when several appliances
deliver to the same Pandora FMS installation. A single-instance service is named
after the value the appliance returns.

### Agents and delivery

`agent_name` names the main agent and is also the parent declared by the object
agents of a service configured with value `1`. It defaults to `NetScaler`, so set
it explicitly for every monitored appliance.

`mode` selects how the documents leave the host:

- `mode = tentacle` (the default) writes the document to `temp` and sends it with
  the Tentacle client:
  `tentacle_client -v -a tentacle_ip -p tentacle_port tentacle_opts <file>`.
  The document is deleted after a successful transfer. `tentacle_client` defaults
  to `tentacle_client`, resolved through `PATH`; set it to a full path when the
  client is not in the search path. `tentacle_opts` is inserted verbatim into
  that command line, so treat its value as trusted operator input. `tentacle_ip`
  takes the address of the Pandora FMS server, without scheme or path.
- Any other value of `mode`, including `local`, copies the document into
  `local_folder` and deletes the temporary copy on success. `local_folder` has no
  default; without it the copy fails and the plugin reports the error on standard
  error.

`temp` is the directory used to write the document before delivery. It defaults
to `/tmp` and must exist and be writable by the user that runs the plugin.

A failed Tentacle transfer is retried once, after one second. If the second
attempt also fails, the document is discarded and the plugin prints
`[<file>] discarted` on standard error; the exit status of the run is not
affected.

### Schedule the run

The plugin does not schedule itself. Run it from `cron` with the period you want
to monitor at, for example every five minutes. This entry assumes the executable
is installed in the Pandora FMS server plugin directory:

```cron
*/5 * * * * root /usr/share/pandora_server/util/plugin/citrix_netscaler.pl <PATH_TO_CONFIG>
```

`agent_interval` only declares the agent interval to Pandora FMS; it does not
change when the plugin runs. Keep the cron period and `agent_interval` aligned so
the declared interval matches the real data rate.

## Verify

Run the plugin once from a terminal:

```bash
cd /usr/share/pandora_server/util/plugin
./citrix_netscaler.pl <PATH_TO_CONFIG>
echo $?
```

A successful run is quiet: the plugin prints nothing on standard output and exits
with status `0`. On success:

- With `mode = tentacle`, the document is written to `temp`, transferred and
  deleted. Nothing remains in `temp` for the finished agent.
- With `mode = local`, a file named `<agent>_<epoch>.data` appears in
  `local_folder`, and the copy in `temp` is removed.
- In Pandora FMS, the configured main agent appears with the `Plugin message`
  module, followed by the object agents of the services you configured.

When the first request to `ns_url` fails, the run takes the opposite path: it
prints the agent document on standard output, still delivers it, and exits with
status `1`. That document holds a single module:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<agent_data description='' version='' os_version='NetScaler Plugin' os_name='NetScaler Plugin' timestamp='2026/10/26 09:00:00' interval='300' parent_agent_name='' agent_name='netscaler-main'>
<module>
	<name><![CDATA[Plugin message]]></name>
	<type>generic_proc</type>
	<data><![CDATA[0]]></data>
	<description><![CDATA[No response from https://netscaler.example.com/nitro/v1/stat/]]></description>
	<module_interval><![CDATA[1]]></module_interval>
</module>
</agent_data>
```

The same document shape is delivered with `Plugin message` set to `1` and the
description `Execution OK` on a successful run, without being printed. Attribute
order inside `<agent_data>` is not significant and can change between runs.

## Understand the results

### Agents generated

Every generated agent declares `NetScaler Plugin` as both operating system and
operating system version, an empty version, the timestamp of the run, the
configured `agent_interval` and the configured `agent_desc` as description.

| Agent | Agent name | Parent |
| --- | --- | --- |
| Main agent | `agent_name`, `NetScaler` when it is empty | None |
| Object of a multi-instance service, value `1` | `ns_service_prefix` + the `name` field of the object | The main agent |
| Object of a multi-instance service, value `0` | `ns_service_prefix` + the `name` field of the object | None |
| Single-instance service, such as `system` | The `name` field returned for the service; `ns_service_prefix` + `agent_name` when it is empty | Per the service value |

Because a single-instance service names its agent after the appliance, the agent
called `agent_name` usually holds only the `Plugin message` module, and the
device statistics live in the agent named after the appliance. That is the
documented behaviour, not a missing module: the status module is always delivered
on the configured main agent.

### Modules generated

| Module | Type | Condition | Meaning |
| --- | --- | --- | --- |
| `Plugin message` | `generic_proc` | Always, on the main agent | `1` when the run completed and the catalogue was read; `0` when the request to `ns_url` failed, with the failing URL in the description |
| `<field>` | `generic_data` when the value is numeric, `generic_data_string` otherwise | The object returns the field and `modules_list` allows it, or the filter is disabled | The statistic value exactly as the appliance returns it |
| `<object> statbindings` | `generic_data_string` | Multi-instance service | `OK` when the stat-bindings request returned valid JSON, `UNREACHABLE` when it did not, with the cause in the description |
| `<object> <binding>` | `generic_data` when the state is numeric, `generic_data_string` otherwise | Multi-instance service and a valid stat-bindings response | The state of each server bound to the object; the description carries its `Primary IP Address` |

Statistic field names are the identifiers the appliance returns, so the module
names depend on the device and firmware. A module name is not prefixed with the
service name: it is the field name alone.

Every module carries `<module_interval>` with `module_interval` (`1` in the
sample file) and `<module_group>` with `module_group` (`NetScaler` by default,
empty in the sample file). The keys `module_tags` and `agent_group` are accepted
but have no effect, so the generated documents carry no tags and no group.

## Operate and troubleshoot

### Run behaviour

- The plugin runs once, reads the appliance and exits. It keeps no state, so two
  consecutive runs return the values the appliance reports at their own time.
- Standard output is empty on success. Diagnostics, copy errors and discarded
  transfers go to standard error. There is no log file and no debug or verbose
  option.
- A delivery failure does not change the exit status: `cron` reports success even
  when the document was discarded. Use the freshness of the agents and of
  `Plugin message` in Pandora FMS, not the exit status alone, to confirm delivery.
- Set `lwp_timeout` on networks where the appliance can be slow to answer;
  without it the run waits for the HTTP client default.
- Store the configuration file with restrictive permissions: it contains the
  appliance password.

### Troubleshooting

- **The usage summary is printed and the status is `1`** — the plugin received no
  argument. Pass the configuration file path.
- **Nothing is reported about a wrong configuration path** — the plugin does not
  diagnose an unreadable configuration file: it continues with empty values and
  fails later, typically on the first request. Check the path in the `cron`
  entry.
- **`Plugin message` reports `0` with `No response from ...`** — the request to
  `ns_url` did not return a successful JSON response. Check the URL and its API
  path, that the appliance is reachable from the plugin host, that the account
  can authenticate, and that the device certificate is trusted.
- **The run stops with an error and delivers nothing** — the appliance answered
  with a body that is not the expected JSON, and decoding it ends the run before
  any agent is built. Confirm that `ns_url` points to the stat API and not to a
  login page or another endpoint.
- **A service in `ns_services` produces no agent** — its name is not in the
  catalogue the appliance returns, or it was written with different case or
  blanks. Compare the name with the objects the device exposes.
- **The run stops after some agents were delivered** — a service listed in the
  catalogue answered with an error, and this version does not recover from it:
  the remaining services are not processed. Correct the credentials or the
  service permissions and run the plugin again.
- **`<object> statbindings` reports `UNREACHABLE`** — the stat-bindings request
  failed or returned invalid JSON; the rest of the object modules are still
  generated.
- **`<object> statbindings` reports `OK` and no per-server module appears** — the
  response contains no bound server for that object.
- **An object agent holds only a few modules** — `modules_list` does not include
  the fields the object returns, or the appliance does not return them. Remove
  the filter to see every field in a test run.
- **No document reaches Pandora FMS** — check that `temp` exists and is writable,
  and then the destination: `tentacle_client`, `tentacle_ip` and `tentacle_port`
  for Tentacle, or an existing writable `local_folder` for local mode. The
  cause is printed on standard error.
- **`There was a problem copying local file to ...`** — `mode` is not `tentacle`
  and the copy into `local_folder` failed. Check that the directory exists and is
  writable.
- **`[...] discarted`** — both Tentacle attempts failed and the document was
  removed. Check the Tentacle service and the client path.
- **The values look stale** — the plugin always reports what the appliance
  returns at run time. Check that `cron` still runs it and that `agent_interval`
  matches the cron period.

## Reference

### Configuration file

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `ns_url` | Yes | Empty | Base URL of the NITRO stat API, with scheme and API path. The plugin requests it to read the catalogue and appends `/<service>` for each service read |
| `ns_user` | Yes | Empty | Account used to read the stat API, sent in the `X-NITRO-USER` header |
| `ns_pass` | Yes | Empty | Password of that account, sent in the `X-NITRO-PASS` header. Stored in plain text |
| `ns_services` | Yes, at least one | None | Repeatable. `ns_services=<service>;<value>`, where `<value>` is `1` to declare `agent_name` as parent, `0` or empty for no parent |
| `modules_list` | No | Empty, filter disabled | Comma-separated allowlist of statistic field names, exact and case-sensitive, without blanks |
| `ns_service_prefix` | No | Empty | Text prepended to the names of the agents generated for the objects of a multi-instance service |
| `agent_name` | No | `NetScaler` | Name of the main agent and parent reference of the object agents |
| `agent_desc` | No | Empty | Description written into every generated agent |
| `agent_interval` | No | `300` | Agent interval declared to Pandora FMS, in seconds |
| `module_interval` | No | `1` | Value written as `module_interval` in every module |
| `module_group` | No | `NetScaler` | Value written as `module_group` in every module |
| `mode` | No | `tentacle` | `tentacle` delivers with the Tentacle client; any other value copies the document into `local_folder` |
| `local_folder` | Yes when `mode` is not `tentacle` | Empty | Destination folder for the copied agent documents |
| `tentacle_ip` | Yes when `mode = tentacle` | Empty | Address of the Pandora FMS Tentacle server |
| `tentacle_port` | No | `41121` | Port of the Pandora FMS Tentacle server |
| `tentacle_client` | No | `tentacle_client` | Tentacle client to execute, resolved through `PATH` when it is a bare name |
| `tentacle_opts` | No | Empty | Extra options inserted verbatim into the Tentacle command line |
| `temp` | No | `/tmp` | Directory where the agent document is written before delivery. Must exist and be writable |
| `lwp_timeout` | No | Not set | HTTP request timeout, in seconds. With no value the plugin applies no explicit timeout |

Keys and values are trimmed; a repeated scalar key keeps its last value, and
`ns_services` accumulates.

### Accepted but not applied

These keys are read without error but have no effect on the generated documents
in this version:

| Name | Effect |
| --- | --- |
| `module_tags` | No tags are written into the modules |
| `agent_group` | The agent document carries no group |
| `log` | No log file is written |
| `api_url`, `api_user`, `api_user_pass`, `api_pass` | The Pandora FMS API is never called; no group or tag is created in the console |

The sample configuration file still lists them, so removing or keeping them
changes nothing.

### Command-line execution

| Condition | Behaviour |
| --- | --- |
| No argument | Prints the usage summary and exits with status `1` |
| One argument | Runs with that file as configuration |
| More than one argument | Only the first is read; the rest are ignored |
| Any option, such as `-h` or `--help` | Treated as the configuration file path; there is no option parsing |
| The argument names an unreadable file | The run continues with empty configuration values and fails later, without a diagnostic about the file |

### Environment

| Variable | Effect |
| --- | --- |
| `http_proxy`, `https_proxy`, `no_proxy` | Used by the HTTP client for the requests to the appliance |

### Generated modules

| Module | Type | Emitted on | Description |
| --- | --- | --- | --- |
| `Plugin message` | `generic_proc` | `agent_name` | `1` with `Execution OK`, or `0` with `No response from <ns_url>` |
| Statistic field names returned by the object | `generic_data` or `generic_data_string` | Agent of the object | One module per allowed field and returned value |
| `<object> statbindings` | `generic_data_string` | Agent of the object, multi-instance service | `OK` or `UNREACHABLE` |
| `<object> <binding>` | `generic_data` or `generic_data_string` | Agent of the object, multi-instance service and valid response | State of a bound server, with its primary IP address in the description |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.citrix_netscaler` |
| Name | Citrix NetScaler monitoring |
| Version | `1.0` |
| Package | `pandorafms.citrix_netscaler.1.0.zip` |
| License | One; the download is limited to licensed users |
| Marketplace last update | 2025-07-09 |
| Downloads | 1 |
| Author | Pandora FMS |
