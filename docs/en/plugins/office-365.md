# Pandora Office 365 Monitoring

*Article last updated: 2026-10-27.*

!!! warning "Discovery integration recommended"
    For new installations use [Office 365 Discovery](../discovery/office-365.md), which is the recommended integration for this service. This plugin is the legacy path. The Marketplace entry states that this addon is no longer actively maintained.

## What it does

The Pandora Office 365 Monitoring plugin reports the health of a Microsoft 365
tenant in Pandora FMS. Each run authenticates against Microsoft Entra ID with
the credentials of an application registration, reads the health overview of
every Microsoft 365 service the tenant subscribes to, and publishes it as one
agent with two modules per service: the status Microsoft reports for that
service and the list of its unresolved incidents.

The plugin runs as a server plugin: it builds the agent document and delivers it
to a Pandora FMS data directory or sends it through Tentacle. It does not print
module XML on standard output, so it cannot be run as an agent plugin.

It can also read the service announcements — the messages Microsoft publishes
about incidents and planned maintenance — and send them to the Pandora FMS log
collector.

> This page documents the server plugin `pandorafms.office365_plugin`.
> Discovering Microsoft 365 tenants and generating their agents from a
> Discovery task is a different addon: see
> [Office 365 Discovery](../discovery/office-365.md).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.office365_plugin`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG `784` and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions. It is a general compatibility statement covering the plugin, not a test record for it |
| The Pandora FMS plugin server, enabled | `Required` | The addon is a server plugin and is executed by the plugin server |
| Network access from the host that runs the plugin to `login.microsoftonline.com` and `graph.microsoft.com` over HTTPS | `Required` | The plugin obtains its token and reads its data from those two hosts; it exposes no option to change either endpoint |
| A Microsoft Entra ID application with the permissions in [Microsoft Graph permissions](#microsoft-graph-permissions) | `Required` | Prerequisite, not a compatibility statement |
| Operating system of the host that runs the plugin | `Not validated` | No operating system has been recorded for this version |

The Marketplace entry states that this addon is no longer actively maintained
and that alternative plugins in the library should be considered. That notice is
a maintenance statement by the publisher; this page describes the behaviour of
version `1.0` as it is distributed.

### Requirements

1. **Connectivity** from the host that runs the plugin to
   `login.microsoftonline.com` and `graph.microsoft.com`.
2. **A Microsoft Entra ID application registered in the tenant to monitor**,
   with a client secret and the application permissions described below.
3. **The tenant ID, the client ID and the client secret** of that application.
4. **Pandora FMS**:
    - The plugin server enabled, to execute the registered plugin.
    - A data directory processed by the data server, or a Tentacle server that
      receives the agent document. When the delivery uses Tentacle, the
      `tentacle_client` executable must be available in `PATH` on the host that
      runs the plugin.
5. **The addon package installed in Pandora FMS** through the console.

### Microsoft Graph permissions

The plugin requests an application token with the
`https://graph.microsoft.com/.default` scope, so it receives the application
permissions granted to the registered application, with no signed-in user. Each
data set it reads is covered by the following Microsoft Graph application
permissions:

| Microsoft Graph request | Used for | Application permission |
|-------------------------|----------|------------------------|
| `/admin/serviceAnnouncement/healthOverviews?$expand=issues` | Service status and unresolved incidents | `ServiceHealth.Read.All` |
| `/admin/serviceAnnouncement/messages` | Service announcements sent as log entries | `ServiceMessage.Read.All` |

Grant only what the run collects: `ServiceMessage.Read.All` is needed only when
log collection is enabled with `-l`. Both permissions require administrator
consent. Do not grant the `ReadWrite` variants.

The client secret is a credential: store it only in the plugin configuration and
revoke it in Microsoft Entra ID when it is no longer needed.

### Register the application in Microsoft Entra ID

1. Open Microsoft Entra ID and register a new application in **App
   registrations**. Register it in the tenant you want to monitor.
2. In **Certificates & secrets**, create a client secret and copy its value
   immediately: Azure shows it only once.
3. From the application overview, copy the **Application (client) ID** and the
   **Directory (tenant) ID**.
4. In **API permissions**, add the Microsoft Graph application permissions
   listed above and grant administrator consent.

<!-- SCREENSHOT NEEDED: API permissions page of the application showing the Microsoft Graph application permissions ServiceHealth.Read.All and ServiceMessage.Read.All with administrator consent granted. -->

### Install the addon

Download the package from the Pandora FMS Marketplace entry, which is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.office365_plugin](https://marketplace.pandorafms.com/entries/pandorafms.office365_plugin)

Load it into Pandora FMS. Once loaded, the plugin is registered with its
parameters and becomes available when creating plugin modules.

The contents of the distributed package could not be inspected for this page, so
no build or dependency-installation procedure is prescribed here. Use the
`pandora_o365` executable that the package installs on the Pandora FMS server.

### Credentials and transport

- The client secret is passed as the value of `-s`. It appears in the shell
  history of a manual run and in the operating system process list while the
  plugin executes, including runs started by the plugin server.
- The plugin has no option to read the credentials from a protected file: the
  console plugin fields and the command line are its only input surfaces.
  Restrict access to the host that runs the plugin and to the users who can edit
  plugin modules, and revoke and reissue the secret if it is exposed.
- Authentication and every data request go to the fixed Microsoft endpoints over
  HTTPS. The plugin offers no way to change them and exposes no proxy option, so
  a proxy in the path is outside its configuration.

## Configure

The plugin has no configuration file: every setting is a command-line option,
documented in [Command-line parameters](#command-line-parameters). Choose how it
is executed first.

### Register the plugin in the console

1. Open **Servers → Plugins** and click **Register Plugin**.
2. Set the name, the plugin type **Standard**, an optional maximum timeout and a
   description.
3. In **Plugin command**, enter the full path of the `pandora_o365` executable on
   the Pandora FMS server, for example `<PATH_TO_PLUGIN>/pandora_o365`.
4. In **Plugin parameters**, pass the options with the plugin macros
   `_field1_`, `_field2_`, ... as placeholders:

```text
-c _field1_ -t _field2_ -s _field3_ -a _field4_ -g _field5_
```

5. In **Macro parameters**, describe each field. The example uses these values:

| Field | Description | Example value |
|-------|-------------|---------------|
| `_field1_` | Application (client) ID | `<CLIENT_ID>` |
| `_field2_` | Directory (tenant) ID | `<TENANT_ID>` |
| `_field3_` | Client secret value; mark **Hide value** | — |
| `_field4_` | Value hashed into the agent name and used as the agent alias | `Pandora_O365` |
| `_field5_` | Pandora FMS group for the generated agent | `<GROUP_NAME>` |

<!-- SCREENSHOT NEEDED: Server plugin registration form for Pandora Office 365 Monitoring with the command, the parameters and the macro parameter list, using lab values and a masked secret. -->

The plugin writes the agent document itself, so the data directory matters:

- When the plugin is registered on the Pandora FMS server that processes the
  documents, the default `-d /var/spool/pandora/data_in/` is the right
  destination and no extra option is needed.
- When it is registered on a remote Pandora FMS server, add
  `--tentacle_address 127.0.0.1` (and `--tentacle_port` if the Tentacle server
  does not listen on `41121`), so the document is sent to the Tentacle server of
  the machine that executes the module.

The module that uses the plugin does not hold the service status: the status and
incident modules appear in the generated `O365_…` agent, not in the agent that
owns the module. What the plugin prints on standard output is the summary number
described in [The printed summary number](#the-printed-summary-number).

### Command line

This is the minimum run: it collects the service status and incidents and writes
the agent document to the local data directory.

```bash
./pandora_o365 -c <CLIENT_ID> -t <TENANT_ID> -s <CLIENT_SECRET>
```

A full run, with an explicit agent identifier, prefix, group, interval and log
collection:

```bash
./pandora_o365 -c <CLIENT_ID> -t <TENANT_ID> -s <CLIENT_SECRET> \
    -a Pandora_O365 -p O365 -g <GROUP_NAME> -i 300 \
    -d /var/spool/pandora/data_in/ -l
```

`./pandora_o365 -h` prints the usage summary with every option and exits without
contacting Microsoft.

### Agent name, alias and group

The `-a` value does not name the agent: it is hashed into the agent name and
copied to the alias.

- **Agent name**: `<prefix>_<MD5 hash of the -a value>`.
- **Agent alias**: `<prefix>_<-a value>`.

With the defaults (`-a Pandora_O365`, `-p O365`) the agent is named
`O365_dab294b287a0bc7a39f3596e17e2ef50` and its alias is `O365_Pandora_O365`.
The name is the identifier Pandora FMS uses for the agent, so the readable string
lives in the alias. Changing `-a` or `-p` produces a **different agent name**, and
therefore a new agent in the console: set both explicitly and keep them stable
across runs.

The `-g` value is written into the agent document. It must be a group that exists
in the console; otherwise the agent is assigned to the default `unknown` group.

### Choose what to collect

| Goal | Options |
|------|---------|
| Status and incident modules only | Default; do not pass `-l` |
| Status, incidents and service announcements | Add `-l` |
| Service announcements only | Add `-l -n`; `-n` skips the status and incident modules |

Log collection sends the messages to the log collector configured for the
generated agent, so that collector must exist in the Pandora FMS environment.

## Verify

Run the plugin manually with a scratch data directory, so the document can be
inspected before Pandora FMS ingests it:

```bash
mkdir -p /tmp/o365-check/
./pandora_o365 -c <CLIENT_ID> -t <TENANT_ID> -s <CLIENT_SECRET> -a Pandora_O365 -d /tmp/o365-check/
```

The directory must exist and be writable, and the `-d` value must end with `/`:
the plugin concatenates the directory and the file name without adding a
separator, so `-d /tmp/o365-check` produces a file named
`/tmp/o365-checkO365_….data` next to the directory instead of inside it.

A successful run prints a single number as its last line (see
[The printed summary number](#the-printed-summary-number)) and writes:

```text
/tmp/o365-check/O365_dab294b287a0bc7a39f3596e17e2ef50.<EPOCH>.data
```

`<EPOCH>` is the time of the run in seconds. The document has one module pair per
service the tenant subscribes to; this is an excerpt with illustrative values:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<agent_data agent_name='O365_dab294b287a0bc7a39f3596e17e2ef50' agent_alias='O365_Pandora_O365' parent_agent_name='' description='Agent generated by pandora_o365 plugin' version='' os_name='' os_version='' timestamp='2026/10/26 10:00:00' address='127.0.0.1' group='unknown' interval='300'>
<module>
	<name><![CDATA[O365_Exchange_status]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[serviceOperational]]></data>
	<description><![CDATA[O365_Exchange Online]]></description>
</module>
<module>
	<name><![CDATA[O365_Exchange_active_issues]]></name>
	<type>generic_data_string</type>
	<data><![CDATA[EX1: Mail flow delay]]></data>
	<description><![CDATA[Exchange Online Issues Ids]]></description>
</module>
</agent_data>
```

In the console, the generated agent appears with its two modules per service
after the Pandora FMS server processes the document:

<!-- SCREENSHOT NEEDED: The generated O365_ agent in the Pandora FMS console, with the _status and _active_issues modules of several services and no real tenant data. -->

Check, in this order:

1. The last line of the output is a number, and no `ERROR` or `Error` line is
   printed on standard error.
2. The `.data` file exists in the directory passed to `-d`, and its
   `<agent_data>` name and alias are the ones expected.
3. Every service the tenant subscribes to has a `_status` module, and one
   `_active_issues` module.
4. The agent appears in the console under the configured group, with the modules
   receiving data at the next execution.

## Understand the results

### The agent

One execution produces **one agent**, whatever the number of services: the
services are modules of that agent, not separate agents.

| Agent property | Value |
|----------------|-------|
| Name | `<prefix>_<MD5 hash of the -a value>` |
| Alias | `<prefix>_<-a value>` |
| Description | `Agent generated by pandora_o365 plugin` |
| Address | `127.0.0.1` |
| Group | The `-g` value (`unknown` by default) |
| Interval | The `-i` value (`300` by default) |
| Operating system fields | Empty |

### Modules per service

For every service returned by Microsoft Graph, the agent has:

| Module | Type | Description |
|--------|------|-------------|
| `<prefix>_<service id>_status` | `generic_data_string` | The `status` Microsoft Graph reports for the service, verbatim |
| `<prefix>_<service id>_active_issues` | `generic_data_string` | `<issue id>: <issue title>` for each incident that is not resolved, concatenated with no separator between incidents; the literal `None` when the service has no unresolved incident |

`<service id>` is the `id` Graph returns for the service, and the status module
description is `<prefix>_<service name>` (for example `O365_Exchange Online`);
the incident module description is `<service name> Issues Ids`.

The service set is not fixed by the plugin: it is whatever the tenant subscribes
to at execution time, so two tenants, or the same tenant after a subscription
change, do not necessarily produce the same module names.

Two consequences of the value format:

- The status module carries a text status. The plugin applies no threshold and no
  mapping to Pandora FMS warning or critical states, so a degraded service does
  not by itself raise an alert. Alert on the value in the module definition if
  you need one.
- Because incidents are concatenated without a separator, two unresolved
  incidents produce a value such as `EX1: Mail flow delayEX2: Mailbox access`,
  which is hard to read and to compare. A single incident has no separator
  problem, and `None` is unambiguous.

Microsoft documents the possible `status` values for a service health object
(`serviceOperational`, `investigating`, `restoringService`,
`serviceDegradation`, `serviceInterruption`, and the other values of the
`serviceHealthStatus` enumeration). The module publishes the string exactly as
received.

### Log entries

With `-l`, the plugin reads the service announcements and writes one log entry
per announcement, with the source `<prefix>_<service>` of the first service the
announcement lists.

- The request skips the first 100 announcements (`$skip=100`) and does not follow
  the paging of the response. A tenant with fewer than 100 announcements
  therefore produces no log entries at all, and only the announcements after the
  first 100 are ever collected.
- The value of the entry is the whole announcement converted to text: the
  message is serialised as a key/value text with the HTML body turned into plain
  text, not as JSON and not as the body alone. Entries are long and their keys
  keep the quoting of that serialisation.
- The log entries are delivered in a second agent document with the same agent
  name as the status document; see
  [Operation](#operation) for the consequence in local delivery.

## Operate and troubleshoot

### Operation

- The plugin keeps no state between runs: every execution reads the tenant
  health at that moment and delivers a complete document, so it can be run
  manually at any time.
- Schedule it from Pandora FMS through the plugin module or the plugin server
  schedule. `-i` only sets the interval recorded in the agent document; the real
  frequency is the one of the schedule, and `-i` should be equal to or greater
  than it.
- **The exit status is `0` in almost every case**, including a failed data or log
  collection: the plugin prints a summary number and exits successfully. Read the
  number instead of the exit status.
- **Tentacle delivery**: the document is written to `--tmp` and sent with
  `tentacle_client`. If the transfer fails, the plugin writes `Tentacle error`
  on standard error, the file stays in `--tmp`, and it still prints its summary
  number and exits with `0`. Check standard error when the agent does not appear.
- **Local delivery with `-l`**: the status document and the log document have the
  same agent name and are named after the second of the run. When both are
  written within the same second, the second write fails with
  `ERROR - Could not write file: [Errno 17] File exists` and the run stops with
  status `1`. The status document of that run is already in the data directory;
  the log entries are lost. When the collection of the announcements takes more
  than a second, the two writes fall in different seconds and both succeed.
- **`--utf8 0`** writes the incident value as a byte string (`b'…'`) instead of
  text. Leave the default `1` unless the environment requires raw bytes.
- The `-d` and `--tmp` values are concatenated with the file name without adding
  a separator: keep the trailing `/` in both.

#### The printed summary number

The last line of a run is the sum of one contribution per collection stage:

| Status collection | Log collection (`-l`) | Printed number |
|-------------------|-----------------------|----------------|
| Collected | Not requested | `2` |
| Collected | Collected | `3` |
| Collected | Failed | `1` |
| Failed | Collected | `0` |
| Failed | Failed | `-2` |
| Skipped (`-n`) | Collected | `1` |
| Skipped (`-n`) | Failed | `-1` |
| Skipped (`-n`) | Not requested | `0` |

A run that cannot authenticate, or whose status request is rejected by Microsoft
Graph, does not reach this summary: it exits with status `1` and prints an error.

### Troubleshooting

- **`Error Auth Token: 'dict' object has no attribute 'reason'`, exit status
  `1`** — Microsoft Entra ID rejected the token request (wrong tenant ID, client
  ID or client secret, or an expired secret). The message is the plugin's own
  error, not the text Microsoft returns: the authentication error handler fails
  before it can print the HTTP reason, so the real cause is not shown. Verify the
  three values and the secret expiry in Microsoft Entra ID, and retry.
- **`Error requesting url: <reason> (<status>) on https://graph.microsoft.com/...`,
  exit status `1`** — Microsoft Graph rejected the health request. A `401` points
  to a token that Microsoft did not accept; a `403` points to a missing
  application permission or to consent that was not granted. Check the
  permissions in [Microsoft Graph permissions](#microsoft-graph-permissions) and
  grant administrator consent again.
- **The run stops with status `157` and prints no summary** — the request for the
  service announcements failed. This stage exits with that status instead of
  reporting it, so a `403` here means `ServiceMessage.Read.All` is missing while
  `-l` is enabled. Add the permission or drop `-l`.
- **`error data: ...` or `error logs: ...` with a summary number** — Microsoft
  answered, but the response did not have the expected structure and the
  document of that stage was not written. Repeat the run; if it persists, check
  the same request manually with Microsoft Graph and verify the permissions.
- **No agent appears in the console** — check, in this order: the `.data` file
  was written to the directory that the Pandora FMS server processes; the `-d`
  or `--tmp` value ends with `/`; the `-g` value names an existing group; in
  Tentacle delivery, standard error shows no `Tentacle error`.
- **The agent appears, but the modules have no data** — the document was written
  by a different execution user than the one the data server reads with, or the
  data directory is not the one the server processes. Compare the file owner and
  the directory with the data server configuration.
- **A second agent appears after a configuration change** — the agent name is
  derived from `-p` and `-a`. Restore the previous values, or accept the new agent
  and delete the old one in the console.
- **No log entries although `-l` is set** — the tenant has fewer than 100
  announcements, the messages request failed (status `157`), or the log collector
  is not configured for the agent.

## Reference

### Command-line parameters

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `-c`, `--clientid` | Yes | — | Application (client) ID of the Microsoft Entra ID application |
| `-t`, `--tenantid` | Yes | — | Directory (tenant) ID; it is part of the token endpoint |
| `-s`, `--secret` | Yes | — | Client secret value of the application |
| `-a`, `--agent_name` | No | `Pandora_O365` | Value hashed into the agent name and used as the agent alias. It is not the agent name, and its help text advertises a different default (`pandora_o365`) |
| `-p`, `--prefix` | No | `O365` | Prefix for the agent name, the agent alias, the module names and the log source |
| `-g`, `--group` | No | `unknown` | Pandora FMS group written into the agent document. It must exist in the console |
| `-i`, `--interval` | No | `300` | Agent interval in seconds, written into the document |
| `-d`, `--data_in` | No | `/var/spool/pandora/data_in/` | Local data directory for the agent document. Used only when no Tentacle address is set. Keep the trailing `/` |
| `-l`, `--logs` | No | Off | Send the service announcements to the Pandora FMS log collector |
| `-n`, `--nodata` | No | Off | Skip the status and incident modules; useful together with `-l` |
| `--tentacle_address` | No | None | Tentacle server address. When set, the document is sent through Tentacle instead of written to `-d` |
| `--tentacle_port` | No | `41121` | Tentacle server port |
| `--tmp` | No | `/tmp/` | Directory where the document is written before the Tentacle transfer. Keep the trailing `/` |
| `--utf8` | No | `1` | `1` writes text values. `0` writes them as raw bytes |

### Command-line execution

```text
pandora_o365 -c <CLIENT_ID> -t <TENANT_ID> -s <CLIENT_SECRET> [-a <NAME>] [-p <PREFIX>] [-g <GROUP>] [-i <SECONDS>] [-d <DIR>] [-l] [-n] [--tentacle_address <HOST>] [--tentacle_port <PORT>] [--tmp <DIR>] [--utf8 <0|1>]
```

| Condition | Behavior |
|-----------|----------|
| A required option (`-c`, `-t`, `-s`) is missing | The usage summary is printed on standard error and the run exits with status `2`, without contacting Microsoft |
| `-h` or `--help` | The usage summary is printed and the run exits with status `0`, without contacting Microsoft |
| The token request is rejected | An authentication error is printed on standard error and the run exits with status `1` |
| The health request is rejected | The HTTP reason and status are printed and the run exits with status `1` |
| The announcements request is rejected | The run exits with status `157` |
| A collection stage fails after a successful request | `error data: …` or `error logs: …` on standard error; the run continues and prints the summary number |
| A Tentacle transfer fails | `Tentacle error` on standard error; the run continues, prints the summary number and exits with status `0` |
| The destination file name already exists | `ERROR - Could not write file: … File exists` and the run exits with status `1` |
| Any other completed run | The summary number is printed and the run exits with status `0` |

### Generated agent

| Property | Value |
|----------|-------|
| Name | `<prefix>_<MD5 hash of the -a value>` |
| Alias | `<prefix>_<-a value>` |
| Description | `Agent generated by pandora_o365 plugin` |
| Address | `127.0.0.1` |
| Group | The `-g` value |
| Interval | The `-i` value |
| Document file | `<data directory><agent name>.<EPOCH>.data`, or the same name in `--tmp` before a Tentacle transfer |

### Generated modules

| Module | Type | Value |
|--------|------|-------|
| `<prefix>_<service id>_status` | `generic_data_string` | The service status returned by Microsoft Graph |
| `<prefix>_<service id>_active_issues` | `generic_data_string` | Unresolved incidents as `<id>: <title>`, concatenated without a separator; `None` when there is none |

The number of modules depends on the services the tenant subscribes to; the
plugin does not create modules for anything else, and it does not create the
licensing modules that the Discovery addon provides.

### Addon identity

| Property | Value |
|----------|-------|
| Marketplace identifier | `pandorafms.office365_plugin` |
| Name | Pandora Office 365 Monitoring |
| Version | `1.0` |
| Package | `pandorafms.office365_plugin.1.0.zip` |
| Marketplace last update | 2025-07-01 |
| Author | Pandora FMS |
| Availability | Download limited to licensed users |
| License | `One` |
| Maintenance | The Marketplace states that the addon is no longer actively maintained and suggests the alternatives listed in the entry |
