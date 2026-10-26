# Hyper-V local

*Article last updated: 2026-10-26.*

## What it does

The Hyper-V local addon reads the inventory of a Microsoft Hyper-V host and
returns the definition of the Pandora FMS agents and modules that correspond to
it, as a JSON document. It is a local-execution tool: it runs on the Windows
Server host that has the Hyper-V role, queries Hyper-V through the PowerShell of
that host, and needs no remote connection, no WinRM listener and no credentials.

Each run produces:

- **One agent for the Hyper-V host**, with memory, local drive and Virtual
  Machine Management service modules. It is optional and disabled by default.
- **One agent per virtual machine (VM)**, with state, CPU, memory, uptime,
  replication and, when enabled, network adapter and virtual disk modules. It is
  enabled by default.

The addon prints the JSON document on standard output, or writes it to a file in
the current directory when `--save_file` is used. It does not send the document
to Pandora FMS and it does not create the agents: the JSON document is the
deliverable of the run.

The Hyper-V plugin is also distributed as a Discovery addon, with a remote
connection and a Discovery task. That addon and its own local mode are documented
in [Hyper-V Discovery](../discovery/hyper-v.md#local-mode).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.hyperv.local`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Windows Server 2022 with the Hyper-V role, local execution | `Known compatible` | The addon's official guide, linked from its Marketplace entry, states that local execution was tested on Windows Server 2022; no separate test record is available |
| Other Windows Server versions with the Hyper-V role | `Not validated` | No test record or support statement covers them |
| PowerShell available in `PATH` (`pwsh`, `powershell.exe` or `powershell`) | `Required` | The executable runs every Hyper-V query through PowerShell |
| The Hyper-V role and its PowerShell cmdlets on the host | `Required` | The queries use `Get-VM`, `Get-VMHost`, `Get-VMNetworkAdapter`, `Get-VMHardDiskDrive`, `Get-VHD`, `Get-CimInstance`, `Get-PSDrive` and `Get-Service` |
| An account allowed to run those cmdlets | `Required` | Prerequisite, not a compatibility statement. See [Permissions](#permissions) |
| Hyper-V integration services in Linux guests | `Required` for VM address reporting | A Linux guest reports no IP address to Hyper-V without them; the agent address then falls back to the host name |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that its integrations are compatible with these versions; a catalogue-wide statement covering this addon, not a test record |

### Requirements

1. **A Windows Server host with the Hyper-V role** where the VMs run. The addon
   queries the local Hyper-V instance; it cannot query another host.
2. **PowerShell that can load the Hyper-V cmdlets**, available in the `PATH` of
   the account that runs the executable.
3. **An account allowed to run those cmdlets** on the host.
4. **A configuration file**, passed with `--conf` on every run.

Linux guests need the Hyper-V integration services (the KVP daemon,
`hv-kvp-daemon`) to report their IP addresses. Without them the VM agent still
exists, but its address is the host name.

### Permissions

The addon only reads. It queries the Hyper-V inventory, the host memory, the
local drives and the state of the `vmms` service; it does not start, stop, change
or create VMs, disks or services.

No official source identifies a narrower set of permissions than running those
cmdlets. Use a dedicated account with the access the queries need and grant it
nothing else. In local execution the executable runs with the privileges of the
account that starts it.

### Security considerations

- Local execution opens no network connection and sends nothing outside the
  host. It needs no credentials, and the remote-mode keys are ignored.
- The JSON document contains the host name, the VM names, the virtual disk paths
  and the IP addresses of the VMs. Treat a saved document as an inventory of the
  host: store it where only the operators who need it can read it.
- The document contains no credentials or tokens.

### Install the addon

Download the addon from its Marketplace entry. The download is free and is a
single Windows executable, listed as `pandorafms.hyperv.local.1.0.exe`. Copy it
to the Hyper-V host, for example into the folder where you keep the Pandora FMS
tools.

The examples in this page use the file name `pandora_hyperV.exe`; use the name
you gave the downloaded file.

Nothing else has to be installed on the host beyond the Hyper-V role and
PowerShell.

## Configure

The executable reads all its settings from the file passed with `--conf`. The
file is required on every run, also in local execution, but it can be empty: an
empty file applies the defaults.

### Configuration file format

The file uses one `key = value` per line:

- A `[section]` header is optional. A file without one is read as a single
  section.
- Key names are case-insensitive.
- Lines that start with `#` or `;` are comments.
- Inline comments are not supported: a `#` after a value is part of the value.
- Flags accept `1`, `true`, `yes` or `on` to enable, in any case; any other value
  disables them.

Local execution ignores the remote-mode keys `hyperv_host` and `credentials`,
even when they are present in the file.

This is a complete configuration for local execution:

```ini
# Local execution on the Hyper-V host
agent_prefix = HyperV
agents_group_id = 0
interval = 300
scan_hypervisor = 1
scan_vm = 1
scan_networking = 1
scan_storage = 1
```

### Select what to collect

| Key | Default | Effect |
|-----|---------|--------|
| `scan_hypervisor` | Off | Creates the Hyper-V host agent |
| `scan_vm` | On | Creates one agent per VM with the VM modules |
| `scan_networking` | Off | Adds the network adapter modules to each VM agent |
| `scan_storage` | Off | Adds the virtual disk modules to each VM agent |

The module groups are independent: enabling only `scan_networking` creates VM
agents that contain only the adapter modules. A VM that produces no module from
the enabled groups does not get an agent. [Reference](#reference) lists every
module.

### Name the agents and set the interval

- `agent_prefix` is placed before the host or VM name, separated by one space.
  The default is `HyperV`, so a VM named `vm01` produces the agent
  `HyperV vm01`. With an empty prefix the agent name is the host or VM name
  alone.
- In the prefix, characters other than letters, digits, `.`, `_` and `-` are
  replaced with `_`, and trailing `_` and spaces are removed. In the VM name,
  characters other than letters, digits, `.`, `_`, `-` and spaces are replaced
  with `_`.
- The agent name is the identity of the agent: changing the prefix or renaming a
  VM produces a different agent name.
- `agents_group_id` is the identifier of the group assigned to the generated
  agents. The default is `0`.
- `interval` is the agent interval, in seconds. The default is `300`.

### Filter the VMs

`allow_list` and `reject_list` are regular expressions, searched anywhere in the
VM name, ignoring case, and tested against the VM name without the prefix:

- A VM must match `allow_list`, when it is set, to produce an agent.
- A VM that matches `reject_list` does not produce an agent.
- The host agent is not filtered.
- An invalid regular expression is ignored, so it filters nothing.

## Verify

Run the executable on the Hyper-V host, passing the configuration file with
`--conf` and selecting local execution with `--execute_local`:

```powershell
.\pandora_hyperV.exe --conf <PATH_TO_CONFIG> --execute_local
```

A successful run prints the JSON document and exits with status `0`. The document
is an array with one element per generated agent. This is an excerpt with a VM
agent and three of its modules:

```json
[
  {
    "agent_data": {
      "agent_name": "HyperV vm01",
      "agent_alias": "HyperV vm01",
      "os": "Windows",
      "os_version": "Windows",
      "interval": 300,
      "id_group": 0,
      "address": "<HYPERV_HOST>",
      "description": "VM vm01 on Hyper-V host <HYPERV_HOST>"
    },
    "module_data": [
      {
        "name": "State",
        "type": "generic_data",
        "data": 2,
        "description": "VM state: 2=Running 3=Off 32768=Paused 32769=Saved 32770=Starting 32771=Stopping 32772=Pausing 32773=Resuming 32774=Saving 32775=FastSaved 0=Unknown. Current: Running",
        "min_critical": 3,
        "max_critical": 3.1
      },
      {
        "name": "CPU Usage",
        "type": "generic_data",
        "data": 7.0,
        "description": "CPU usage percentage",
        "unit": "%"
      },
      {
        "name": "Uptime",
        "type": "generic_data",
        "data": 88423900,
        "description": "VM uptime",
        "unit": "_timeticks_"
      }
    ]
  }
]
```

In this example the VM reports no usable IPv4 address, so the agent address is
the host name. When the VM reports one, the address is that IPv4 address.

## Understand the results

### Agents generated

| Agent | Created when | Name | Address | Operating system fields |
|-------|--------------|------|---------|-------------------------|
| Host agent | `scan_hypervisor` is on | `<prefix> <ComputerName>` | The name of the local computer | `Windows`, `Windows Server` |
| VM agent | At least one scan group applies and the VM passes the filters | `<prefix> <VM name>` | First usable IPv4 address of the VM; the local computer name when it has none | `Windows`, `Windows` |

Details that apply to both:

- A usable IPv4 address excludes loopback (`127.x`) and link-local
  (`169.254.x`) addresses.
- Every VM agent is reported with operating system `Windows` and version
  `Windows`, including Linux guests: the addon reads the VM from Hyper-V, not
  from the guest.
- VM agents are not children of the host agent.
- The number of agents is the host agent, when enabled, plus one agent per VM
  that passes the filters and produces at least one module.

### Module groups

- **Host.** `HyperV Local Status`, `Memory Used Percent`, one
  `DiskUsed_<drive>` module per file-system drive with used space, and
  `VMMS Service Status`.
- **VM.** `State`, `CPU Usage`, `Memory Assigned MB`, `Memory Demand MB`,
  `Uptime`, `Status`, `Generation` and `Replication State`.
- **Network adapters.** Four modules per adapter: `<nic>-connected`,
  `<nic>-status`, `<nic>-switchname` and `<nic>-ipaddresses`.
- **Virtual disks.** Five modules per disk: `disk<n>-path`, `disk<n>-SizeGB`,
  `disk<n>-FileSizeGB`, `disk<n>-DiskType` and `disk<n>-DiskFormat`.

### Partial results

The addon records a failed query as a missing group and keeps the rest of the
document:

- If the host query fails, the host agent is still emitted with only
  `HyperV Local Status`.
- If the VM inventory query fails, no VM agent is emitted.
- If the adapter or disk query fails, those modules are missing and the other
  modules of the VM are kept.

`HyperV Local Status` is `1` in every run of the executable. It does not change
to `0` when a query fails, so use the presence of the other modules to detect a
failed query.

The exit status is `0` for these partial results. Only an invalid command line or
an unreadable configuration file produces a non-zero exit status.

## Operate and troubleshoot

### Save the output to a file

Add `--save_file` to write the document to a file instead of printing it:

```powershell
.\pandora_hyperV.exe --conf <PATH_TO_CONFIG> --execute_local --save_file
```

- The file is named `hyperv_local_<hostname>_<timestamp>.txt` and is written to
  the current directory, in UTF-8.
- The executable prints nothing on standard output and reports the absolute path
  of the file on standard error, with the prefix `[save_file] JSON saved to:`.
- `--save_file` is only valid together with `--execute_local`.

### Execution characteristics

- The addon keeps no state between runs and only reads. It can be executed
  manually at any time, as often as needed.
- It does not deliver data to Pandora FMS: each run returns the JSON document and
  ends.
- The executable tries `pwsh` first, then `powershell.exe`, then `powershell`.
  The first one that exists must be able to load the Hyper-V cmdlets; a
  PowerShell that starts and fails is not retried with the next one.
- The size of the document grows with the number of VMs, adapters and disks.

### Troubleshooting

- **The executable exits with status `2` and prints a usage message on standard
  error** — the command line is not valid: `--conf` is missing, an option is
  unknown, or `--save_file` was used without `--execute_local`.
- **The executable exits with status `1` and prints `[]`** — the path passed
  with `--conf` does not exist or cannot be read. With `--save_file` the saved
  file contains the empty array. The diagnostic message is not printed in local
  mode.
- **The document is `[]` with exit status `0`** — no scan group is enabled, or
  no VM passed the filters. Check the `scan_*` keys and the regular expressions.
- **The host agent contains only `HyperV Local Status`** — the host queries
  failed. Check that the PowerShell found in `PATH` can run `Get-VMHost`,
  `Get-CimInstance`, `Get-PSDrive` and `Get-Service`, and that the account can
  use them.
- **There are no VM agents but the host agent exists** — the VM inventory query
  failed, or every VM was filtered out by `allow_list` or `reject_list`.
- **A VM agent has no network or disk modules** — `scan_networking` or
  `scan_storage` is off, or the corresponding query failed for that VM.
- **A VM has no address of its own** — the guest reports no usable IPv4 address,
  for example because its integration services are not running, so the agent
  uses the host name.
- **A VM shows `State` critical** — the VM is turned off (`State` `3`). The other
  modules keep the values Hyper-V returns.
- **`--save_file` produces no output on the screen** — expected: the document
  goes to the file and only the path is reported, on standard error.

## Reference

### Command line

```powershell
.\pandora_hyperV.exe --conf <PATH_TO_CONFIG> --execute_local [--save_file]
```

| Option | Required | Description |
|--------|----------|-------------|
| `--conf <PATH_TO_CONFIG>` | Yes | Path to the [configuration file](#configuration-file). It must exist, also in local execution; an empty file applies the defaults. |
| `--execute_local` | For local execution | Runs the PowerShell queries on the machine where the executable runs. No host and no credentials are needed. |
| `--save_file` | No | Only with `--execute_local`. Writes the JSON document to `hyperv_local_<hostname>_<timestamp>.txt` in the current directory instead of printing it. |
| `-h`, `--help` | No | Prints the usage summary and exits. |

Without `--execute_local` the executable runs the remote WinRM mode of the
Hyper-V plugin, which needs `hyperv_host` and credentials. That mode belongs to
the Discovery workflow and is documented in
[Hyper-V Discovery](../discovery/hyper-v.md).

### Configuration file

One `key = value` per line. Local execution ignores `hyperv_host` and
`credentials`.

| Key | Default | Description |
|-----|---------|-------------|
| `agent_prefix` | `HyperV` | Text placed before the host or VM name, separated by one space. Empty uses the name alone |
| `agents_group_id` | `0` | Identifier of the group of the generated agents |
| `interval` | `300` | Agent interval, in seconds |
| `scan_hypervisor` | Off | Creates the host agent |
| `scan_vm` | On | Creates one agent per VM with the VM modules |
| `scan_networking` | Off | Adds the network adapter modules |
| `scan_storage` | Off | Adds the virtual disk modules |
| `allow_list` | Empty | Regular expression; only matching VMs produce an agent |
| `reject_list` | Empty | Regular expression; matching VMs produce no agent |
| `monitor_hypervisor` | Off | Legacy name for `scan_hypervisor`, used when that key is absent or empty |
| `token_vm` | On | Legacy name for `scan_vm`, used when that key is absent or empty |
| `token_networking` | Off | Legacy name for `scan_networking`, used when that key is absent or empty |
| `token_storage` | Off | Legacy name for `scan_storage`, used when that key is absent or empty |
| `hyperv_host` | Empty | Remote mode only. Ignored in local execution |
| `credentials` | Empty | Remote mode only. Ignored in local execution |

### Agent fields

| Field | Content |
|-------|---------|
| `agent_name`, `agent_alias` | The agent name; both fields hold the same value |
| `os` | `Windows` |
| `os_version` | `Windows Server` for the host agent; `Windows` for every VM agent |
| `interval` | Agent interval, in seconds |
| `id_group` | Group identifier |
| `address` | Host agent: the name of the local computer. VM agent: the first usable IPv4 address, or the host name when the VM has none |
| `description` | Host agent: `Hyper-V host <ComputerName> (<host>)`. VM agent: `VM <name> on Hyper-V host <host>` |

### Modules of the host agent

| Module | Type | Description |
|--------|------|-------------|
| `HyperV Local Status` | `generic_proc` | `1` in every run; it does not change when a query fails |
| `Memory Used Percent` | `generic_data` | Host memory in use, in `%` |
| `DiskUsed_<drive>` | `generic_data` | Used space of each file-system drive that has used space, in `GB`; the free space is in the description |
| `VMMS Service Status` | `generic_data` | Status of the `vmms` service: `1` Stopped, `2` StartPending, `3` StopPending, `4` Running, `5` ContinuePending, `6` PausePending, `7` Paused; `0` when the service is not found. Critical at `1` and `2` |

### Modules of the VM agent

| Module | Type | Description |
|--------|------|-------------|
| `State` | `generic_data` | `2` Running, `3` Off, `32768` Paused, `32769` Saved, `32770` Starting, `32771` Stopping, `32772` Pausing, `32773` Resuming, `32774` Saving, `32775` FastSaved, `0` Unknown. Critical at `3` |
| `CPU Usage` | `generic_data` | CPU usage, in `%` |
| `Memory Assigned MB` | `generic_data` | Memory assigned to the VM, in `MB` |
| `Memory Demand MB` | `generic_data` | Memory the VM demands, in `MB` |
| `Uptime` | `generic_data` | Uptime in timeticks (1/100 s), computed from the uptime Hyper-V reports |
| `Status` | `generic_data_string` | Operational status text reported by Hyper-V |
| `Generation` | `generic_data` | VM generation |
| `Replication State` | `generic_data` | `0` Disabled, `1` ReadyForReplication, `2` InitialReplicationInProgress, `3` Replicating, `4` Synced, `5` Recovered, `6` Committed, `7` Suspended, `8` Resynchronizing, `9` ResynchronizeSuspended, `10` Error |

### Modules of the network adapters

`<nic>` is the adapter name with characters other than letters, digits, `.`, `_`
and `-` replaced with `_`. When a VM has several adapters with the same name,
`_1`, `_2` and so on are appended.

| Module | Type | Description |
|--------|------|-------------|
| `<nic>-connected` | `generic_proc` | `1` when the adapter is connected, `0` otherwise |
| `<nic>-status` | `generic_data` | `1` Ok, `2` Degraded, `3` Unknown, `4` Error, inferred from the connection state: `1` connected, `4` not. Warning `2`–`3`, critical `4` |
| `<nic>-switchname` | `generic_data_string` | Virtual switch name; `0` when none |
| `<nic>-ipaddresses` | `generic_data_string` | Comma-separated IP addresses; `0` when none |

### Modules of the virtual disks

`<n>` numbers the disks of each VM in the order Hyper-V returns them, starting
at `1`.

| Module | Type | Description |
|--------|------|-------------|
| `disk<n>-path` | `generic_data_string` | Path of the virtual disk file |
| `disk<n>-SizeGB` | `generic_data` | Maximum configured size, in `GB` |
| `disk<n>-FileSizeGB` | `generic_data` | Size of the file on the host, in `GB` |
| `disk<n>-DiskType` | `generic_data` | `1` Fixed, `2` Dynamic, `3` Differencing; `0` when unknown |
| `disk<n>-DiskFormat` | `generic_data_string` | Disk format, for example `VHD` or `VHDX` |

### Output document

The document is a JSON array. Each element has an `agent_data` object and a
`module_data` array:

| Field | Content |
|-------|---------|
| `agent_data` | Agent identity and metadata; see [Agent fields](#agent-fields) |
| `module_data` | One object per module: `name`, `type`, `data`, `description` and, when the module defines them, `unit` and the `min_warning`, `max_warning`, `min_critical` and `max_critical` thresholds |

Local execution prints only this array. The `summary` and `info` objects of the
remote mode are not part of the local output.

### Exit status

| Status | Meaning |
|--------|---------|
| `0` | The run finished. The array can be empty or contain partial results |
| `1` | The configuration file does not exist or cannot be read. The output is an empty array |
| `2` | Invalid command line: missing `--conf`, unknown option, or `--save_file` without `--execute_local` |

### Addon identity

| Property | Value |
|----------|-------|
| Marketplace identifier | `pandorafms.hyperv.local` |
| Name | Hyper-V local |
| Version | `1.0` |
| Marketplace last update | 2026-05-28 |
| License | Free download |
| Author | Pandora FMS |
| Download file | `pandorafms.hyperv.local.1.0.exe` |
| Marketplace entry | [pandorafms.hyperv.local](https://marketplace.pandorafms.com/entries/pandorafms.hyperv.local) |
| Official documentation | [English](https://pandorafms.com/guides/public/books/hyper-v-windows-Hcs) · [Spanish](https://pandorafms.com/guides/public/books/hyper-v-windows) |
