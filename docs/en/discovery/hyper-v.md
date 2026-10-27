# Hyper-V Discovery

*Article last updated: 2026-10-26.*

## What it monitors

The Hyper-V Discovery addon monitors a Microsoft Hyper-V host and the virtual machines (VMs) it runs. It connects remotely to the host over WinRM, runs read-only queries and turns the result into Pandora FMS agents and modules: host memory, drives and Virtual Machine Management service state, and, for each VM, its state, CPU, memory, uptime, replication, network adapters and virtual disks.

A Discovery task generates two kinds of agents, depending on the options you enable:

- **One agent for the Hyper-V host** (optional), with host-level modules.
- **One agent per VM**, with the modules of the enabled scan options. VMs are not agents of their own operating system: the addon sees them only through the host.

Nothing is installed on the Hyper-V host or inside the VMs.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.hyperv`, version `1.1` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| WinRM listener on TCP port `5985` of the Hyper-V host, reachable from the Discovery server | `Required` | The addon connects to `http://<host>:5985/wsman` |
| Account accepted by the host through HTTP Basic authentication that can run the Hyper-V PowerShell cmdlets | `Required` | Prerequisite, not a compatibility statement. See [Permissions](#permissions) |
| `curl` command available on the Discovery server | `Required` | The addon runs `curl` to talk to the host |
| Windows Server and Hyper-V versions of the monitored host | `Not validated` | No version has been recorded for this addon |
| Operating system of the Discovery server | `Not validated` | No operating system has been recorded for this version |
| Specific Pandora FMS versions | `Not validated` | No version matrix has been recorded for this addon |

### Prerequisites

1. **Connectivity** from the Discovery server to TCP port `5985` of the Hyper-V host. Port `5985` is the WinRM HTTP port; the addon does not use HTTPS (`5986`).
2. **WinRM enabled on the Hyper-V host**, accepting HTTP Basic authentication over the unencrypted HTTP listener.
3. **A user and password** for the host, registered in the Pandora FMS credential store as a **custom** credential that provides the keys `user` and `password`.
4. **Pandora FMS**: a Discovery server to run the task and the console to define it.

The addon ships its own executable (`bin/pandora_hyperV`), so nothing else has to be installed on the Discovery server except the `curl` command.

### Permissions

The addon runs the Hyper-V PowerShell queries `Get-VM`, `Get-VMHost`, `Get-VMNetworkAdapter`, `Get-VMHardDiskDrive` and `Get-VHD`, plus read-only queries of the host operating system, drives and the `vmms` service, through the WinRM session. The account therefore needs permission to open a WinRM session on the host and to run those cmdlets. No official source identifies a narrower set of roles, so no least-privilege policy is documented here; use a dedicated account for Pandora FMS and grant it only what those queries need.

The task is read-only: it does not start, stop, change or create anything on the host.

### Security considerations

The addon authenticates with HTTP Basic over `http://` on port `5985`. The user and password travel Base64-encoded, which is not encryption, so anyone who can observe the traffic between the Discovery server and the host can read them. Run the task only on a network you trust or isolate that path. Use a dedicated account with a password used for nothing else.

The addon does not verify TLS certificates, because it does not use TLS.

### Install the addon

Download the `.disco` package from the Pandora FMS Marketplace entry, which is limited to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.hyperv](https://marketplace.pandorafms.com/entries/pandorafms.hyperv)

Load it into Pandora FMS. Once loaded, **Hyper-V** is available when creating Discovery tasks.

## Configure the Discovery task

Create the task from the Discovery applications and choose **Hyper-V**. The console presents the fields in two steps; every field is documented in [Task parameters](#task-parameters).

1. **Hyper-V Connection** — where and how to connect, and how agents are named:

    - **Hyper-V IP**: address or name of the Hyper-V host. Required.
    - **HyperV Credentials**: the custom credential with the `user` and `password` keys. Required.
    - **Agent prefix (optional)**: text placed before the name of every generated agent. Defaults to `HyperV`.
    - **Agent autodisable mode**: disables the agent when all its modules become unknown until data returns.

    <!-- SCREENSHOT NEEDED: Hyper-V Connection wizard step showing Hyper-V IP, HyperV Credentials, Agent prefix and Agent autodisable mode, with no real addresses or credentials. -->

2. **Monitoring Tokens and Filters** — what is monitored:

    - **Scan Hypervisor**: creates the agent of the Hyper-V host. Off by default.
    - **Scan VM**: creates one agent per VM. On by default.
    - **Scan Networking**: adds the network adapter modules of each VM. Off by default.
    - **Scan Storage**: adds the virtual disk modules of each VM. Off by default.
    - **Regexp to filter agents** and **Allow regexp**: only VMs whose name matches the pattern are created. **Allow regexp** is shown when the checkbox is on.
    - **Regexp to discard agents** and **Deny regexp**: VMs whose name matches the pattern are not created. **Deny regexp** is shown when the checkbox is on.

    <!-- SCREENSHOT NEEDED: Monitoring Tokens and Filters wizard step showing the four scan checkboxes and the allow and deny regexp fields, using lab values only. -->

The task's group and interval come from the generic task-definition step and are applied to every agent the task creates.

## Verify the first run

Force the task from the Discovery task list and check the result in this order.

1. **The task summary.** A task that connects successfully reports:

    - **hyperv_host**: the host the task queried.
    - **VMs**: VMs found on the host, before the allow and deny filters are applied.
    - **Agents**: agents generated.

    <!-- SCREENSHOT NEEDED: Discovery task execution summary for a Hyper-V task showing hyperv_host, VMs and Agents. -->

    When the addon cannot connect, the summary shows `status` as `ERROR`, the host, and a `message` that identifies the cause; see [Troubleshoot](#troubleshoot).

2. **The agents.** One per VM that passes the filters and, when **Scan Hypervisor** is enabled, one for the host.
3. **The modules.** With **Scan VM** enabled, every VM agent has `State`, `CPU Usage` and the other modules listed in [Modules per agent](#modules-per-agent). A VM in the `Off` state has `State` set to `3`, which is critical.

## Understand the results

### Agents generated

| Agent | Name | Address | Notes |
|-------|------|---------|-------|
| Host agent | `<prefix> <ComputerName>` | The **Hyper-V IP** value | Created only when **Scan Hypervisor** is enabled. `ComputerName` is the name reported by the host; the **Hyper-V IP** value is used when the host returns none. Operating system `Windows`, version `Windows Server` |
| VM agent | `<prefix> <VM name>` | First usable IPv4 address of the VM; the **Hyper-V IP** value when it has none | One per VM that passes the filters. Operating system `Windows`, version `Windows` |

Details that apply to both:

- The prefix is separated from the name by a space. In the prefix, characters other than letters, digits, `.`, `_` and `-` are replaced with `_`, and trailing `_` and spaces are removed. In the VM name, characters other than letters, digits, `.`, `_`, `-` and spaces are replaced with `_`. With an empty prefix the name is the host or VM name alone.
- A usable IPv4 address excludes loopback (`127.x`) and link-local (`169.254.x`) addresses. The address is taken from the VM first and from its network adapters second.
- Agent identity depends on the agent name: changing **Agent prefix**, or renaming a VM, creates a new agent instead of updating the existing one.
- VM agents are not children of the host agent.
- With **Scan VM** disabled, VM agents are still created when **Scan Networking** or **Scan Storage** is enabled, and they contain only those modules. When none of the three options applies, no VM agent is created.

### Modules per agent

**Host agent**

| Module | Type | Description |
|--------|------|-------------|
| `HyperV Connection Status` | `generic_proc` | `1` when the WinRM connection works. Always present |
| `Memory Used Percent` | `generic_data` | Percentage of host memory in use, in `%` |
| `DiskUsed_<drive>` | `generic_data` | Used space of each file-system drive with used space, in `GB`. The free space is in the description |
| `VMMS Service Status` | `generic_data` | State of the Hyper-V Virtual Machine Management service: `1` Stopped, `2` StartPending, `3` StopPending, `4` Running, `5` ContinuePending, `6` PausePending, `7` Paused; `0` when the service is not found. Critical at `1` and `2` |

When the host queries fail, the agent is still created with only `HyperV Connection Status`.

**VM agent, Scan VM**

| Module | Type | Description |
|--------|------|-------------|
| `State` | `generic_data` | `2` Running, `3` Off, `32768` Paused, `32769` Saved, `32770` Starting, `32771` Stopping, `32772` Pausing, `32773` Resuming, `32774` Saving, `32775` FastSaved, `0` Unknown. Critical at `3` |
| `CPU Usage` | `generic_data` | CPU usage, in `%` |
| `Memory Assigned MB` | `generic_data` | Memory assigned to the VM, in `MB` |
| `Memory Demand MB` | `generic_data` | Memory demanded by the VM, in `MB` |
| `Uptime` | `generic_data` | VM uptime, in timeticks |
| `Status` | `generic_data_string` | Operational status text reported by Hyper-V |
| `Generation` | `generic_data` | VM generation |
| `Replication State` | `generic_data` | `0` Disabled, `1` ReadyForReplication, `2` InitialReplicationInProgress, `3` Replicating, `4` Synced, `5` Recovered, `6` Committed, `7` Suspended, `8` Resynchronizing, `9` ResynchronizeSuspended, `10` Error |

**VM agent, Scan Networking**: four modules per network adapter of the VM. `<nic>` is the adapter name with characters other than letters, digits, `.`, `_` and `-` replaced with `_`; when a VM has several adapters with the same name, `_1`, `_2` and so on are appended.

| Module | Type | Description |
|--------|------|-------------|
| `<nic>-connected` | `generic_proc` | `1` when the adapter is connected, `0` otherwise |
| `<nic>-status` | `generic_data` | `1` when connected, `4` when not. Warning from `2` to `3`, critical at `4` |
| `<nic>-switchname` | `generic_data_string` | Virtual switch name; `0` when none |
| `<nic>-ipaddresses` | `generic_data_string` | Comma-separated IP addresses; `0` when none |

**VM agent, Scan Storage**: five modules per virtual disk that the host can read, numbered `disk1`, `disk2` and so on in the order returned.

| Module | Type | Description |
|--------|------|-------------|
| `disk<n>-path` | `generic_data_string` | Path of the virtual disk file |
| `disk<n>-SizeGB` | `generic_data` | Maximum configured size, in `GB` |
| `disk<n>-FileSizeGB` | `generic_data` | Size of the file on the host, in `GB` |
| `disk<n>-DiskType` | `generic_data` | `1` Fixed, `2` Dynamic, `3` Differencing |
| `disk<n>-DiskFormat` | `generic_data_string` | Disk format, for example `VHD` or `VHDX` |

## Operate

### Manual execution

The addon can run outside a Discovery task. The executable takes the path to a configuration file described in [Configuration file](#configuration-file):

```bash
./pandora_hyperV --conf <PATH_TO_CONFIG>
```

It prints a JSON document with the `summary`, the `monitoring_data` of every agent and, when errors occur, an `info` key with the messages. The exit code is `1` when an error was recorded.

A configuration file contains the credential encoded in `credentials`. Protect it with restrictive permissions.

### Local mode

With `--execute_local` the executable runs the PowerShell queries on the machine where it is started instead of connecting over WinRM. No `hyperv_host` or credentials are needed, and any credential in the file is ignored. The machine must be the Hyper-V host and have PowerShell (`pwsh`, `powershell.exe` or `powershell`) available.

```bash
./pandora_hyperV --conf <PATH_TO_CONFIG> --execute_local
```

In this mode it prints only the `monitoring_data` as indented JSON, and the host agent contains `HyperV Local Status` instead of `HyperV Connection Status`. Add `--save_file` to write that JSON to `hyperv_local_<hostname>_<timestamp>.txt` in the current directory instead of printing it; `--save_file` is rejected without `--execute_local`. The Discovery task does not use local mode.

## Troubleshoot

The addon has no verbose or debug flag. Its diagnostic channel is the `info` field of the JSON execution result, shown in the task's execution information.

When the connection probe fails, the task ends with the exit code `1`, `status` `ERROR` and one of these messages:

- **`Unable to authenticate to host '<host>' authentication failed.`**: HTTP `401`. Check the user and password in the credential and that the host accepts Basic authentication.
- **`Access denied when connecting to host '<host>'.`**: HTTP `403`. The account is not allowed to open a WinRM session.
- **`Unable to reach host '<host>' connection timed out.`**: no answer within 15 seconds to connect or 30 seconds in total. Check routing and firewalls.
- **`Unable to connect to host '<host>' verify WinRM is enabled and the firewall allows TCP 5985.`**: connection refused. WinRM is not listening on `5985`.
- **`Unable to connect to the specified host '<host>'. Error: ...`**: any other failure, such as an unresolvable name (`Unable to resolve host`), an unreachable host or a missing `curl`. The message includes the error.

Other signals appear in `info` with exit code `1`:

- **`Missing required parameter: hyperv_host`**: the host is empty.
- **`Missing credentials (user or password empty)`** or **`Error while parsing configuration credentials: ...`**: the credential lacks `user` or `password`, or is not valid Base64-encoded JSON.
- **`Configuration file not found: ...`** or **`Error reading config: ...`**: the configuration file passed with `--conf` is missing or unreadable.

Situations that do not fail the task:

- **The task succeeds but creates no agents**: the connection works but the Hyper-V queries returned nothing or failed. The messages (`[vms] Get-VM error: ...`) are only in `info`, and the summary reports `VMs` as `0`. Check that the account can run the cmdlets listed in [Permissions](#permissions) and that the Hyper-V role is installed on the host.
- **Fewer VM agents than `VMs`**: the allow or deny regular expression filtered them out. `VMs` counts the VMs found before filtering.
- **A VM agent has no network or disk modules**: **Scan Networking** or **Scan Storage** is disabled, or the host could not read that VM's adapters or disks. Disks whose file cannot be read by `Get-VHD` are skipped.
- **A VM has no address of its own**: the VM reports no usable IPv4 address, for example because the integration services are not running, so the agent uses the **Hyper-V IP** value.
- **A VM agent shows `State` critical**: the VM is turned off (`State` `3`). The agent keeps reporting; the other modules keep the values Hyper-V returns.

## Reference

### Task parameters

#### Hyper-V Connection

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Hyper-V IP | `_hypervhost_` | string | empty | Required. Address or name of the Hyper-V host |
| HyperV Credentials | `_credentials_` | credential select (custom) | — | Required. Must provide the keys `user` and `password` |
| Agent prefix (optional) | `_agentprefix_` | string | `HyperV` | Optional. Text before the agent name; see [Agents generated](#agents-generated) |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Disables the agent when all its modules become unknown until data returns |

#### Monitoring Tokens and Filters

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Scan Hypervisor | `_monitorHypervisor_` | checkbox | off | Creates the host agent |
| Scan VM | `_tokenVM_` | checkbox | on | Creates one agent per VM with the VM modules |
| Scan Networking | `_tokenNetworking_` | checkbox | off | Adds network adapter modules to each VM agent |
| Scan Storage | `_tokenStorage_` | checkbox | off | Adds virtual disk modules to each VM agent |
| Regexp to filter agents | `_regexpFilter_` | checkbox | off | Shows **Allow regexp** |
| Allow regexp | `_allowRegexp_` | string | empty | Optional. Only VMs whose name matches are created |
| Regexp to discard agents | `_regexpDiscard_` | checkbox | off | Shows **Deny regexp** |
| Deny regexp | `_denyRegexp_` | string | empty | Optional. VMs whose name matches are not created |

Both regular expressions are searched anywhere in the VM name, ignoring case, and are tested against the VM name without the prefix. They apply to VM agents only; the host agent is not filtered. A VM must pass the allow expression and not match the deny expression.

### Configuration file

Used by manual execution and written by the Discovery task from the fields above. One `key = value` per line. Flags accept `1`, `true`, `yes` or `on` to enable.

| Key | Default | Description |
|-----|---------|-------------|
| `hyperv_host` | empty | Required except in local mode. Hyper-V host address or name |
| `credentials` | empty | Required except in local mode. Base64 of the JSON `{"user": "<USERNAME>", "password": "<PASSWORD>"}` |
| `agent_prefix` | `HyperV` | Agent name prefix |
| `agents_group_id` | `0` | Identifier of the group of the generated agents |
| `interval` | `300` | Agent interval, in seconds |
| `agent_autodisable` | `0` | Autodisable mode |
| `scan_hypervisor` | `0` | Host agent |
| `scan_vm` | `1` | VM agents |
| `scan_networking` | `0` | Network adapter modules |
| `scan_storage` | `0` | Virtual disk modules |
| `allow_list` | empty | Allow regular expression |
| `reject_list` | empty | Deny regular expression |

Example:

```ini
hyperv_host       = <HYPERV_HOST>
credentials       = <BASE64_CREDENTIALS>
agent_prefix      = HyperV
agents_group_id   = 0
interval          = 300
agent_autodisable = 0
scan_hypervisor   = 1
scan_vm           = 1
scan_networking   = 1
scan_storage      = 1
allow_list        =
reject_list       = ^template-
```

### Command line

| Option | Required | Description |
|--------|----------|-------------|
| `--conf <conf_file>` | Yes | Path to the configuration file |
| `--execute_local` | No | Run the PowerShell queries locally instead of over WinRM |
| `--save_file` | No | Only with `--execute_local`. Save the JSON to a file instead of printing it |

### Addon identity

| Item | Value |
|------|-------|
| Name | Hyper-V |
| Identifier | `pandorafms.hyperv` |
| Version | `1.1` |
| Type and section | Discovery, `app` |
| Marketplace entry | [pandorafms.hyperv](https://marketplace.pandorafms.com/entries/pandorafms.hyperv), updated 2026-08-24 |
| Availability | The Marketplace entry states that the download is limited to licensed users |
