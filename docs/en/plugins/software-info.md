# Software Info

*Article last updated: 2026-09-25.*

## What it does

Software Info is a Pandora FMS agent plugin that reports the software packages with a pending update on the host where the agent runs. Each run prints, on standard output, an `extended_data` document of category `software` with one entry per pending package.

When event reporting is enabled, the plugin also prints a sibling `events` block with one event per pending update, so the upgrade can be triggered from the console, for example through an RMM execution.

The plugin only queries the package managers already present on the host with read-only commands. It never installs, upgrades or modifies software. Standard output carries only the generated XML; diagnostics go to a log file.

## Prepare

### Compatibility and availability

The plugin supports Linux and Windows hosts. On Linux it can query apt, dnf, yum, pacman, zypper and apk; on Windows it queries winget. A package manager that is not installed is skipped silently.

### Requirements

1. A Pandora FMS agent installed and running on the monitored host.
2. The package manager or managers to query installed on the host, with the metadata needed to report available versions.
3. Permission to run the package manager query commands for the user that runs the agent.
4. A writable location for the diagnostics log and the state file, or custom paths provided at execution time.

### Install the plugin

The plugin is distributed as the `software_info` binary for Linux and `software_info.exe` for Windows. Deploy it to the endpoint that will run it and register it in the agent configuration as described in Configure.

## Configure

Register the plugin in the agent configuration as an agent plugin. The agent runs it periodically and appends its raw output to the XML it sends:

```
module_begin
module_absoluteinterval 1d
module_plugin software_info
module_end
```

Command-line options can be appended to the `module_plugin` line:

```
module_begin
module_absoluteinterval 1d
module_plugin software_info -timeout 60s -event-mode changes
module_end
```

All options are optional. See Reference for the complete list.

## Verify

Run the plugin manually first to confirm that it collects data and produces well-formed XML:

```
software_info
```

A successful run writes an `extended_data` document to standard output. When a package has a pending update, the document contains one `extended_data_module` named `Software`:

```xml
<extended_data>
	<extended_data_module>
		<name><![CDATA[Software]]></name>
		<category><![CDATA[software]]></category>
		<datalist>
			<data>
				<field name="available_version"><![CDATA[3.0.13-1]]></field>
				<field name="current_version"><![CDATA[3.0.7-1]]></field>
				<field name="fms_object_unique_id"><![CDATA[apt:openssl]]></field>
				<field name="manager"><![CDATA[apt]]></field>
				<field name="name"><![CDATA[openssl]]></field>
			</data>
		</datalist>
	</extended_data_module>
</extended_data>
```

When event reporting is enabled and there is something to report, a sibling `events` block follows. When nothing is pending, only the empty `extended_data` root is printed. With the inventory disabled and no events, nothing is printed.

## Understand the results

### Pending software inventory

The plugin always emits one `extended_data` document of category `software`; the `Software` module is omitted when nothing is pending. Each item exposes the following fields:

| Field | Content |
| --- | --- |
| `name` | Package name as reported by the package manager. |
| `current_version` | Installed version. Empty when the query method cannot report it cheaply. |
| `available_version` | Version offered by the package manager. |
| `manager` | Package manager that reported the update (apt, dnf, yum, pacman, zypper, apk, winget). |
| `fms_object_unique_id` | Stable identifier `<manager>:<name>`. |

Items are sorted alphabetically by manager and name.

### Events

When events are enabled, each emitted update produces one entry in the `events` block. The payload is the base64 encoding of a JSON object with the message (`data`) and the severity, the format accepted by the server event processing. Events are controlled by `-event-mode` and the persisted state file, so an unchanged pending update is not repeated on every run.

## Operate and troubleshoot

### Change detection

By default the plugin persists the pending set in a state file and emits an event only for a package that is newly pending or whose available version changed. Use `-event-mode always` to emit one event per pending update on every run, or `-event-mode off` to never emit events. The state file is only read and written in changes mode.

### Execution and exit code

The command is one-shot. It exits with code 0 on success, including partial or degraded collections, and only returns non-zero on a hard failure while parsing arguments or rendering the XML.

### Diagnostics

Diagnostics are written to the configured log file and fall back to standard error if the file is not writable. They never reach standard output. The log is rotated and the state file is written atomically with restrictive permissions.

### Known limitations

- On Windows, winget output is locale-dependent; rows that cannot be read reliably are dropped rather than reported wrong.
- On systems using dnf or zypper, available versions reflect the last repository metadata refresh performed by the host; the plugin never refreshes metadata.
- The `events` block is an undocumented server surface; there is no other producer of it in the product.
- There is no ITSM inventory schema type for `software` extended data.

## Reference

### Command-line parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-timeout` | No | `60s` | Maximum time allowed for collection. |
| `-log-path` | No | `/var/log/pandora/software_info.log` (Linux), `%ProgramData%\PandoraFMS\software_info.log` (Windows) | Diagnostics log path. |
| `-state-path` | No | `/var/lib/pandora/software_info.state` (Linux), `%ProgramData%\PandoraFMS\software_info.state` (Windows) | Change-detection state path. |
| `-severity` | No | `3` | Severity for emitted events (0-6). |
| `-inventory` | No | `true` | Emit the pending-update `extended_data` inventory. Set `-inventory=false` to report only events. Combining `-inventory=false` with `-event-mode off` is rejected. |
| `-event-mode` | No | `changes` | Event policy: `changes`, `always` or `off`. |
| `-managers` | No | all available | Comma-separated subset of package managers to keep. |

### Supported package managers

| Platform | Manager | Read-only query |
| --- | --- | --- |
| Linux | apt | `apt-get -s -q upgrade` |
| Linux | dnf | `dnf -q check-update` |
| Linux | yum | `yum -q check-update` |
| Linux | pacman | `pacman -Qu` |
| Linux | zypper | `zypper --quiet list-updates` |
| Linux | apk | `apk version -l '<'` |
| Windows | winget | `winget list --upgrade-available --disable-interactivity` |

All query commands run without a shell and with a fixed C locale.
