# Meraki Discovery

*Article last updated: 2026-10-26.*

## What it monitors

The Meraki Discovery addon monitors Cisco Meraki network devices through the Meraki Dashboard REST API. For one Meraki network it reads the status of the devices of three product types, **appliance**, **switch** and **wireless**, and turns the result into Pandora FMS agents and modules: device status, appliance uplink status and performance score, switch port status and traffic, wireless throughput and connected clients, and optionally the aggregated appliance traffic of the network.

A Discovery task generates these agents:

- **One agent per appliance** with its status and uplink status.
- **One agent per switch** with its status and the status and traffic of each port.
- **One agent per wireless device** with its status, throughput and client count.
- **One network traffic agent** (optional) with the aggregated traffic of the appliances of the network.

The task authenticates with a Bearer token and sends the generated agent data to Pandora FMS with Tentacle.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.meraki`, version `1.1` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Network access from the Discovery server to the Meraki Dashboard API | `Required` | Every request goes to the API URL configured in the task |
| Meraki API Bearer token with access to the organization | `Required` | Prerequisite, not a compatibility statement |
| Operating system of the Discovery server | `Not validated` | No operating system has been recorded for this version |
| Specific Pandora FMS versions | `Not validated` | No version matrix has been recorded for this addon |
| Specific Meraki hardware models and firmware | `Not validated` | No model or firmware matrix has been recorded |

### Prerequisites

1. **Connectivity** from the Discovery server to the Meraki Dashboard API (the task form suggests `https://api.meraki.com/api/v1` as the URL).
2. **A Meraki API Bearer token** that can read the organization, its networks and their devices. The addon only issues read (`GET`) requests.
3. **The organization ID** and, for the network to monitor, its **name** (or part of it) and its **network ID**. See [Configure the Discovery task](#configure-the-discovery-task) for how each value is used.
4. **Pandora FMS**: a Discovery server to run the task and the console to define it. The generated data is sent with Tentacle, so the Tentacle server address and port must be reachable from the Discovery server.

The addon ships its own executable, `bin/pandora_meraki`, so nothing else has to be installed on the Discovery server to run a task.

### Install the addon

Download the `.disco` package from the Pandora FMS Marketplace entry, which is limited to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.meraki](https://marketplace.pandorafms.com/entries/pandorafms.meraki)

Load it into Pandora FMS. Once loaded, **Meraki** is available among the applications when creating Discovery tasks.

## Configure the Discovery task

Create the task from **Management → Discovery → Application → Meraki**. The console presents the fields in two steps, **Meraki base** and **Meraki Detailed**; every field is documented in [Task parameters](#task-parameters).

One task monitors **one network**. To monitor several networks, create one task per network.

1. **Meraki base** — connection and target:

    - **ID**: text that identifies the network by name. The addon looks for the first network of the organization whose **name** contains this text (a plain substring match, not a regular expression) and monitors the devices that belong to it.
    - **Token**: the Meraki API Bearer token.
    - **Url**: the API base URL, for example `https://api.meraki.com/api/v1`.
    - **Organization**: the organization ID.
    - **Network**: the **ID** of the network. It is used as-is in the network-level requests (aggregated appliance traffic and wireless usage), so enter the ID of the same network selected with **ID**.
    - **Use location** and **Location**: secondary groups added to the generated agents.
    - **Tentacle IP** and **Tentacle port**: where the generated agent data is sent.

    <!-- SCREENSHOT NEEDED: Meraki base wizard step showing ID, Token, Url, Organization, Network, Use location and Tentacle fields, with no real token, organization or addresses. -->

2. **Meraki Detailed** — naming and scope:

    - **Use prefix**, **Agent Prefix** and **Module Prefix**: prefixes added to agent and module names.
    - **Interval monitoring**: time window of the switch port statistics, in seconds.
    - **Use API** and the **Api** fields: reserved fields that this version does not use. See [Task parameters](#task-parameters).
    - **Name Agent Hostname**: name the agents after the device name instead of its serial number.
    - **Scan appliances**, **Scan switches**, **Scan wireless** and **Scan Appliance Traffic Network**: which device types and data to collect.

    <!-- SCREENSHOT NEEDED: Meraki Detailed wizard step showing the prefix, Interval monitoring, Name Agent Hostname and scan checkboxes. -->

The task's group and interval come from the generic task-definition step and are applied to the agents the task creates.

## Verify the first run

Force the task from **Management → Discovery → Task list** and check the result in this order.

1. **The task summary.** A task that completes successfully reports:

    - **Total agents**: all agents generated.
    - **Total appliance agents**, **Total switches agents** and **Total wireless agents**: agents per device type.
    - **Total network appliance traffic agents**: `1` when the network traffic agent was generated.

    A task that does not complete successfully records the errors in its execution information instead.

    <!-- SCREENSHOT NEEDED: Discovery task execution summary for a Meraki task showing the total agent counters. -->

2. **The agents.** Their aliases start with the agent prefix (if any) followed by `Appliance_`, `Switch_` or `Wireless_` and the device name or serial number.

3. **The modules.** Every device agent has a `status` module. See [Understand the results](#understand-the-results) for the rest.

## Understand the results

### Agents generated

| Agent | Alias | Address | Secondary groups |
|-------|-------|---------|------------------|
| Appliance | `<agent prefix>Appliance_<name or serial>` | Public IP address of the device | **Location**, plus `Router` |
| Switch | `<agent prefix>Switch_<name or serial>` | Public IP address of the device | **Location**, plus `Switch` |
| Wireless | `<agent prefix>Wireless_<name or serial>` | Public IP address of the device | **Location**, plus `Access Points` |
| Network traffic | `<agent prefix> Traffic Appliance_<Network>` | None | **Location** |

- With **Name Agent Hostname** enabled, switch and wireless agents use the device name, falling back to the serial number when the device has no name; when disabled, the serial number is used. Appliance agents also read the flag, but they take the name from the switch data, which the appliance path does not have: with **Name Agent Hostname** enabled the run stops with an error when it reaches an appliance. Disable it to create appliance agents named after the serial number.
- The agent identity is derived from the agent prefix and the name or serial used. Changing the prefix or the **Name Agent Hostname** setting, or renaming a device, produces a new agent instead of updating the previous one.
- Only devices that belong to the monitored network and whose type is enabled (**Scan appliances**, **Scan switches**, **Scan wireless**) produce agents.
- Agents report with the task group and interval.

### Modules per agent

Module names are shown without the module prefix.

**Appliance agent**

| Module | Type | Condition | Description |
|--------|------|-----------|-------------|
| `status` | `generic_proc` | Always | `1` when the device status is `online`, `0` otherwise. The description carries the status reported by Meraki |
| `perfScore` | `generic_data` | When Meraki returns a performance score for the device | Performance score, in `%` |
| `Uplink <interface>_ifOperStatus` | `generic_proc` | One per uplink reported for the device | `1` when the uplink status is `active`, `0` otherwise. The description carries the uplink status |

**Switch agent**

| Module | Type | Condition | Description |
|--------|------|-----------|-------------|
| `status` | `generic_proc` | Always | `1` when the device status is `online`, `0` otherwise |
| `Port <portId>_ifOperStatus` | `generic_proc` | One per port | `1` when the port status is `Connected`, `0` otherwise |
| `Port <portId>_ifOutOctets` | `generic_data` | One per port | Traffic sent by the port, in `Kbps` |
| `Port <portId>_ifInOctets` | `generic_data` | One per port | Traffic received by the port, in `Kbps` |

**Wireless agent**

| Module | Type | Condition | Description |
|--------|------|-----------|-------------|
| `status` | `generic_proc` | Always | `1` when the device status is `online`, `0` otherwise |
| `totalKbps` | `generic_data` | When Meraki returns usage data | Total throughput, in `Kbps` |
| `sentKbps` | `generic_data` | When Meraki returns usage data | Throughput sent, in `Kbps` |
| `receivedKbps` | `generic_data` | When Meraki returns usage data | Throughput received, in `Kbps` |
| `clientCount` | `generic_data` | When Meraki returns the client count | Clients connected |

**Network traffic agent** (when **Scan Appliance Traffic Network** is enabled)

| Module | Type | Description |
|--------|------|-------------|
| `Traffic appliance <Network> total_sent` | `generic_data` | Sum of the data sent over all the applications reported by Meraki for the appliances of the network |
| `Traffic appliance <Network> total_recv` | `generic_data` | Sum of the data received over the same applications |
| `Traffic appliance <Network> total_clients` | `generic_data` | Sum of the number of clients over the same applications |

### How the values are obtained

- Device status, appliance uplink status and the device list are read for the whole organization and then filtered by the monitored network.
- The switch port statistics cover the last **Interval monitoring** seconds.
- The wireless throughput and client count, and the network appliance traffic, are read for the last 86400 seconds (24 hours) and are not configurable.
- For wireless devices, the module values are the first data point that Meraki returns for the device.
- The network traffic agent is generated whenever **Scan Appliance Traffic Network** is enabled, even when **Scan appliances** is disabled.

## Operate

### Manual execution

The addon can run outside a Discovery task. The executable takes a single parameter, the path to a configuration file described in [Configuration file](#configuration-file):

```bash
./pandora_meraki --conf <PATH_TO_CONFIG>
```

It prints a JSON execution result with the summary and any error messages, and sends one data file per agent using the configured transfer mode. In `tentacle` mode (the default) the `tentacle_client` executable must be available in the `PATH` of the user running the addon.

The configuration file contains the Bearer token. Protect it with restrictive permissions.

## Troubleshoot

The addon has no verbose or debug flag. Its diagnostic channel is the information of the JSON execution result, which is shown in the task's execution information.

- **`error: id its required`, `error: base url its required`, `error: bearer token its required`, `error: organization its required`, `error: network its required`**: the named setting is empty. All five are mandatory.
- **`Meraki nets could not be obtained.`**: the request to list the networks of the organization did not return data. Check the **Url**, the **Organization** ID, the validity of the **Token** and the connectivity to the API.
- **`Request Error: <detail>`**: the connection to the API failed. The detail carries the error of the HTTP client.
- **`Error: 204 : Data could not be obtained.` and `Error: 204 : PerfScore data could not be obtained.`**: Meraki answered without content for a request. The corresponding modules are not created.
- **No agents are generated**: the text in **ID** does not match the name of any network of the organization, the monitored network has no devices of the enabled types, or the device types are disabled.
- **No `perfScore` or `Uplink` modules on an appliance**: Meraki did not return performance or uplink data for that device.
- **No wireless modules besides `status`**: the network-level wireless requests returned no data for the device in the last 24 hours.
- **`Error getting switch data: <detail>`, `Error getting wireless data: <detail>` or `Error getting appliance data: <detail>`**: the data of a device could not be processed. The detail carries the cause.
- **Data does not reach Pandora FMS**: check **Tentacle IP** and **Tentacle port**, and the connectivity to the Tentacle server.

## Reference

### Task parameters

#### Meraki base

| Field | Macro | Type | Required | Default | Notes |
|-------|-------|------|----------|---------|-------|
| ID | `_id_` | string | Yes | — | Text contained in the name of the network to monitor. First network that matches is used |
| Token | `_token_` | password | Yes | — | Meraki API Bearer token |
| Url | `_baseUrl_` | string | Yes | — | API base URL. The form suggests `https://api.meraki.com/api/v1` |
| Organization | `_organization_` | string | Yes | — | Organization ID |
| Network | `_network_` | string | Yes | — | Network ID used in the network-level requests |
| Use location | `_useLocation_` | checkbox | No | off | Enables **Location** |
| Location | `_location_` | string | No | — | Secondary groups added to the agents. Shown when **Use location** is on |
| Tentacle IP | `_tentacleIP_` | string | No | `127.0.0.1` | Server that receives the agent data |
| Tentacle port | `_tentaclePort_` | number | No | `41121` | Tentacle port |

#### Meraki Detailed

| Field | Macro | Type | Required | Default | Notes |
|-------|-------|------|----------|---------|-------|
| Use prefix | `_usePrefix_` | checkbox | No | off | Enables the prefix fields |
| Agent Prefix | `_agentPrefix_` | string | No | — | Added to the agent names and aliases. Shown when **Use prefix** is on |
| Module Prefix | `_modulePrefix_` | string | No | — | Added to the module names. Shown when **Use prefix** is on |
| Interval monitoring | `_intervalMonitoring_` | number | No | `3600` | Time window of the switch port statistics, in seconds |
| Use API | `_useApi_` | checkbox | No | off | Enables the **Api** fields. This version does not use them |
| Api url | `_apiUrl_` | string | No | — | Not used by this version. Shown when **Use API** is on |
| Api user | `_apiUser_` | string | No | — | Not used by this version |
| Api password | `_apiPass_` | password | No | — | Not used by this version |
| Api user password | `_apiUserpass_` | password | No | — | Not used by this version |
| Name Agent Hostname | `_agentHostname_` | checkbox | No | on | On: agents named after the device name. Off: named after the serial number |
| Scan appliances | `_scanAppliance_` | checkbox | No | on | Generate appliance agents |
| Scan switches | `_scanSwitch_` | checkbox | No | on | Generate switch agents |
| Scan wireless | `_scanWireless_` | checkbox | No | on | Generate wireless agents |
| Scan Appliance Traffic Network | `_scanApplianceTrafficNetwork_` | checkbox | No | on | Generate the network traffic agent |

There is no option to monitor Meraki cellular gateway devices in this version.

### Configuration file

Used by manual execution. One `key = value` per line, without sections. Numeric options accept `1` to enable and `0` to disable; a value that is not a number is read as `0`.

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `id` | Yes | — | Text contained in the name of the network to monitor |
| `base_url` | Yes | — | API base URL |
| `bearer_token` | Yes | — | Bearer token |
| `organization` | Yes | — | Organization ID |
| `network` | Yes | — | Network ID used in the network-level requests |
| `location` | No | empty | Secondary groups of the agents |
| `agents_group_name` | No | empty | Group of the generated agents |
| `interval` | No | `300` | Agent interval, in seconds |
| `agent_prefix` | No | empty | Prefix of the agents |
| `module_prefix` | No | empty | Prefix of the modules |
| `interval_monitoring` | No | `3600` | Time window of the switch port statistics, in seconds |
| `agentname_hostname` | No | `1` | `1` names agents after the device name, `0` after the serial number |
| `scan_appliance` | No | `1` | Appliance agents |
| `scan_switch` | No | `1` | Switch agents |
| `scan_wireless` | No | `1` | Wireless agents |
| `scan_traffic_appliance_network` | No | `1` | Network traffic agent |
| `transfer_mode` | No | `tentacle` | `tentacle` sends the data files with Tentacle; `local` moves them to the default Pandora FMS data directory (`/var/spool/pandora/data_in/`) |
| `tentacle_address` | No | `127.0.0.1` | Tentacle server address |
| `tentacle_port` | No | `41121` | Tentacle server port |
| `tentacle_client` | No | `tentacle_client` | Tentacle client executable |
| `tentacle_opts` | No | empty | Extra Tentacle client options. This version reads the value but does not pass it to the transfer, which always runs without extra options |
| `temporal` | No | `/tmp` | Directory where the data files are written before sending. This version reads the value but does not pass it to the transfer, which always uses `/tmp` |
| `data_dir` | No | `/var/spool/pandora/data_in/` | Destination of the data files in `local` mode. This version reads the value but does not pass it to the transfer, which always uses `/var/spool/pandora/data_in/` |

The keys `api_url`, `api_user`, `api_pass` and `api_user_pass` are accepted but not used by this version.

Example:

```ini
base_url = https://api.meraki.com/api/v1
bearer_token = <API_TOKEN>
organization = <ORGANIZATION_ID>
id = <NETWORK_NAME_TEXT>
network = <NETWORK_ID>
location = <SECONDARY_GROUP>

agents_group_name = MerakiAgents
agent_prefix = Meraki
module_prefix = Meraki_
interval = 300
interval_monitoring = 3600
agentname_hostname = 1

scan_appliance = 1
scan_switch = 1
scan_wireless = 1
scan_traffic_appliance_network = 1

tentacle_address = <TENTACLE_SERVER_IP>
tentacle_port = 41121
```

### Meraki API requests

All requests are `GET` requests with the Bearer token, sent to the configured **Url**.

| Data | Request |
|------|---------|
| Networks of the organization | `/organizations/<organization>/networks` |
| Device status | `/organizations/<organization>/devices/statuses` |
| Appliance uplink status | `/organizations/<organization>/uplinks/statuses` |
| Appliance performance | `/devices/<serial>/appliance/performance` |
| Network appliance traffic | `/networks/<network>/traffic` |
| Switch port status and traffic | `/devices/<serial>/switch/ports/statuses` |
| Wireless usage | `/networks/<network>/wireless/usageHistory` |
| Wireless clients | `/networks/<network>/wireless/clientCountHistory` |

### Addon identity

| Item | Value |
|------|-------|
| Name | Meraki |
| Identifier | `pandorafms.meraki` |
| Version | `1.1` |
| Type and section | Discovery, `app` |
| Marketplace entry | [pandorafms.meraki](https://marketplace.pandorafms.com/entries/pandorafms.meraki), updated 2025-08-20 |
| Availability | The Marketplace entry states that the download is limited to licensed users |
