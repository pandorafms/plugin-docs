# SAP R3 Discovery

*Article last updated: 2026-10-26.*

## What it monitors

The SAP R3 Discovery addon monitors SAP systems remotely, with no software installed on the SAP hosts. It connects to the SAP system with a SAP user and turns the result into a Pandora FMS agent whose modules report availability, work processes, IDocs, ABAP dumps, background jobs, RFC queues, database figures and, optionally, security and audit indicators.

A Discovery task monitors one SAP system (one SAP hostname, client and system number) and generates **a single agent** with:

- A `SAP connection` module that reports whether the SAP system answered.
- The modules you select in the task, plus optional custom modules that run SAP checks defined by you.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.sap`, version `1.8` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Network access from the Discovery server to the SAP system | `Required` | The addon opens a remote connection to the SAP system. The package does not record the port; use the one your SAP system exposes for remote connections |
| A SAP user with a password and the access needed by the selected modules | `Required` | See [SAP user](#sap-user) |
| SAP releases and SAP products | `Not validated` | No SAP release matrix has been recorded for this version |
| Operating system of the Discovery server | `Not validated` | No operating system has been recorded for this version |
| Specific Pandora FMS versions | `Not validated` | No version matrix has been recorded for this addon |

### Prerequisites

1. **Connectivity** from the Discovery server to the SAP system.
2. **A SAP user** and its password, registered in the Pandora FMS credential store as a SAP credential.
3. **The SAP client and system number** of the system to monitor.
4. **Pandora FMS**: a Discovery server to run the task and the console to define it.

The addon ships its own executable, `bin/pandora_sap`, together with everything it needs to query SAP, so nothing else has to be installed on the Discovery server or on the SAP hosts.

### SAP user

The addon authenticates with the user and password stored in the credential. The SAP authorizations that this user needs for each module have not been recorded for this version, so this page does not state a minimum set. Create a dedicated user for Pandora FMS and grant only what your SAP administrators confirm is required by the modules you enable; a module the user is not authorized to run can report the error returned by SAP in its description.

The credential stored in Pandora FMS must provide the keys `user` and `password`.

!!! warning
    The SAP user and password are passed to the process that queries SAP as command arguments, so they may be visible in the process list of the Discovery server. Restrict access to that server.

### Install the addon

Download the `.disco` package from the Pandora FMS Marketplace entry, which is limited to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.sap](https://marketplace.pandorafms.com/entries/pandorafms.sap)

Load it into Pandora FMS. Once loaded, **SAP R3** is available among the application Discovery tasks.

## Configure the Discovery task

Create the task from the Discovery applications and choose **SAP R3**. The console presents the fields in two steps; every field is documented in [Task parameters](#task-parameters).

1. **SAP R3 Base** — the SAP system and the credential:

    - **SAP Hostname**: address or name of the SAP system.
    - **SAP Client**: SAP client.
    - **SAP System Number**: SAP system number.
    - **SAP Credentials**: the SAP credential registered in the credential store.
    - **SAP SNC Mode**: enables SNC protection for the communication. When enabled, the console shows **SAP SNC Partner name**, **SAP SNC QOP** and **Client SNC name**.

    <!-- SCREENSHOT NEEDED: SAP R3 Base wizard step showing SAP Hostname, SAP Client, SAP System Number and SAP Credentials, with no real addresses or credentials. -->

    <!-- SCREENSHOT NEEDED: SAP R3 Base wizard step with SAP SNC Mode enabled, showing the SNC partner name, SNC QOP and client SNC name fields. -->

2. **SAP R3 Detailed** — execution and monitoring options:

    - **Max threads**: number of parallel workers that run the modules.
    - **Target agent**: name of the agent that receives the modules. When empty, the **SAP Hostname** is used.
    - **Security and Audit Modules**: adds the security and audit modules. It may increase the task execution time.
    - **SAP modules**: predefined modules to monitor.
    - **Custom modules definitions**: your own modules, one per line. See [Custom modules](#custom-modules).

    <!-- SCREENSHOT NEEDED: SAP R3 Detailed wizard step showing Max threads, Target agent, Security and Audit Modules, SAP modules and Custom modules definitions. -->

The task's group and interval come from the generic task-definition step and are applied to the agent the task creates.

## Verify the first run

Force the task from the Discovery task list and check the result in this order.

1. **The task summary.** A task that completes successfully reports:

    - **SAP Target**, **SAP Client** and **SAP System**: the values of the task.
    - **Total modules**: modules generated, including `SAP connection`.

    A task that does not complete successfully records the errors in its execution information instead.

    <!-- SCREENSHOT NEEDED: Discovery task execution summary for a SAP R3 task showing SAP Target, SAP Client, SAP System and Total modules. -->

2. **The agent.** One agent, named after the **Target agent** or, when empty, the **SAP Hostname**.

3. **The `SAP connection` module.** It is `1` when SAP answered. When it is `0`, no other module is generated; read its description and the task execution information.

## Understand the results

### Agent generated

| Item | Value |
|------|-------|
| Agent name and alias | The **Target agent**, or the **SAP Hostname** when empty |
| Operating system | `SAP` |
| Operating system version | The operating system and the version reported by the SAP system |
| Address | The address reported by the SAP system |
| Group and interval | The group and interval of the Discovery task |

The agent name is the only identity the addon sets, so use **Target agent** to give each monitored SAP system a distinct, stable agent name.

### How the connection is checked

Before running any module, the addon runs the `SAP System info` check (`120`). A valid answer provides the agent address, the operating system version and the system identifier. If the check fails, the addon reports the error, creates only the `SAP connection` module with value `0` and does not run the remaining modules. When the check succeeds, the module description reads `SAP is reachable. Running on <DATABASE_TYPE> <INSTANCE>`.

### Modules

Every module carries the SAP system identifier as extra data. Modules are grouped below; the full list with identifiers is in [Predefined modules](#predefined-modules).

| Group | What it reports |
|-------|-----------------|
| System and availability | System information, login status, SAPGUI response time and dialog users |
| Work processes | Failed, restart-disabled, stopped and available work processes, as counts and percentages |
| IDocs | IDocs failed and processed since yesterday |
| Dumps | ABAP dumps of yesterday, today and the last hour, as counts, lists and grouped counts |
| Jobs and batch input | Cancelled jobs of yesterday and today and failed batch input |
| External send operations | Send operations processed and not processed since yesterday |
| Database | Oracle tablespace usage, Microsoft SQL Server log figures and SAP HANA memory |
| Business and system data | System block entries, customer account figures, profile parameters and authorization profile changes |
| RFC queues | Entries and failed attempts in the RFC inbound and outbound queues |
| Security and audit | Users with sensitive authorizations and monthly imported orders. Enabled with **Security and Audit Modules** |

By default the task selects ten modules: `102`, `103`, `104`, `105`, `109`, `111`, `113`, `116`, `150` and `151`.

## Operate

### Custom modules

Besides the predefined modules, **Custom modules definitions** accepts your own modules. Write one module per line:

```text
<MODULE_NAME>;<MODULE_TYPE>;<SAP_CHECK>;<DESCRIPTION>
```

- `<MODULE_NAME>`: name of the module.
- `<MODULE_TYPE>`: Pandora FMS module type, for example `generic_data` or `generic_data_string`.
- `<SAP_CHECK>`: the arguments of the SAP check to run, in the same form the predefined modules use, for example `-m 120`.
- `<DESCRIPTION>`: optional.

Empty lines and lines that start with `#` are ignored. A line with fewer than three fields is ignored without an error. The package does not list the checks available beyond the predefined modules, so only use `<SAP_CHECK>` values supplied by Pandora FMS.

Example, using a predefined check:

```text
SAP info;generic_data_string;-m 120
```

### Manual execution

The addon can run outside a Discovery task. The executable takes the path to a configuration file described in [Configuration file](#configuration-file) and, optionally, the path to a custom modules file with the format above:

```bash
./pandora_sap --conf <PATH_TO_CONFIG> --custom_modules <PATH_TO_CUSTOM_MODULES>
```

It prints a JSON document to the standard output with a `summary`, an `info` key when there are messages, and `monitoring_data` with the agent and its modules. It does not send data to Pandora FMS by itself. The exit code is `1` when any error occurred.

A configuration file contains the SAP user and password encoded in `credentials`. Protect the file with restrictive permissions.

## Troubleshoot

The addon has no verbose or debug flag. Its diagnostic channel is the `info` field of the JSON execution result, which is shown in the task's execution information.

- **`Parameter [server] not defined`, `Parameter [client] not defined` or `Parameter [system] not defined`**: a mandatory task field is empty.
- **`Can't get user from [credentials] parameter` or `Can't get password from [credentials] parameter`**: the credential does not provide `user` and `password`, or `credentials` is not valid base64-encoded JSON.
- **`Parameter [snc_partner] not defined`, `Parameter [snc_qop] not defined` or `Parameter [snc_myname] not defined`**: **SAP SNC Mode** is enabled and the field is empty. All three SNC fields are required when SNC is enabled.
- **`Failed to connect SAP server: ...`**: the connection check failed. The message contains the error returned by SAP, for example an `RFC_ERROR_...` code. Check the hostname, client, system number, credential, network access and SNC settings. Only the `SAP connection` module, with value `0`, is created.
- **`Error while running module <NAME>: ...`**: a module failed. The remaining modules still run.
- **A module description contains an `RFC_ERROR_...` message**: SAP returned an error for that check, for example because the user is not authorized to run it.
- **`Error while reading configuration modules: ...`**: the module list is not a valid list of identifiers.
- **`Error while reading custom modules file: ...`**: the custom modules file could not be read.
- **Missing modules**: identifiers that the addon does not know are ignored without an error.
- **The task takes too long**: increase **Max threads**, or disable **Security and Audit Modules** and the modules you do not need. More threads increase the CPU usage of the Discovery server.

## Reference

### Task parameters

#### SAP R3 Base

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| SAP Hostname | `_server_` | string | — | Mandatory |
| SAP Client | `_sapClient_` | string | — | Mandatory |
| SAP System Number | `_sapSystem_` | string | — | Mandatory |
| SAP Credentials | `_credentials_` | credential select (SAP) | — | Mandatory. Must provide `user` and `password` |
| SAP SNC Mode | `_sapSNCMode_` | checkbox | off | Enables SNC protection. The three fields below are shown when it is on |
| SAP SNC Partner name | `_sapSNCPartnerName_` | string | — | A valid SAP server SNC name, equal to the Distinguished Name (DN) of the SAP server PSE. Required by the addon when SNC mode is on |
| SAP SNC QOP | `_sapSNCQOP_` | select | `8` | Quality of protection: `1` Authentication only, `2` Authentication and integrity protection, `3` Authentication, integrity and privacy protection, `8` Global default protection, `9` Maximum protection |
| Client SNC name | `_sapSNCMyName_` | string | — | A valid client SNC name, equal to the Distinguished Name (DN) of the client PSE. Required by the addon when SNC mode is on |

#### SAP R3 Detailed

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Max threads | `_threads_` | number | `1` | Optional. Never more threads than modules |
| Target agent | `_targetAgent_` | string | — | Optional. When empty, the SAP hostname is used |
| Security and Audit Modules | `_secAudit_` | checkbox | on | Adds modules `220` to `228` to the selection |
| SAP modules | `_customModules_` | multiselect | `102`, `103`, `104`, `105`, `109`, `111`, `113`, `116`, `150`, `151` | Optional. See [Predefined modules](#predefined-modules) |
| Custom modules definitions | `_customModulesDefinition_` | text area | — | Optional. One module per line: `module name;module type;SAP check definition;module description` |

### Configuration file

Used by manual execution. One `key = value` per line. Numeric options accept `1` to enable and `0` to disable; a value that is not a number is read as `0`.

| Key | Default | Description |
|-----|---------|-------------|
| `agents_group_id` | `10` | Group ID of the generated agent |
| `interval` | `300` | Agent interval, in seconds |
| `threads` | `1` | Number of parallel workers |
| `server` | empty | Mandatory. SAP hostname |
| `client` | empty | Mandatory. SAP client |
| `system` | empty | Mandatory. SAP system number |
| `credentials` | empty | Mandatory. Base64 of the JSON `{"user": "<SAP_USER>", "password": "<SAP_PASSWORD>"}` |
| `snc_mode` | `0` | `1` enables SNC |
| `snc_partner` | empty | SNC partner name. Mandatory when `snc_mode` is `1` |
| `snc_qop` | empty | SNC quality of protection (`1`, `2`, `3`, `8` or `9`). Mandatory when `snc_mode` is `1` |
| `snc_myname` | empty | Client SNC name. Mandatory when `snc_mode` is `1` |
| `sec_audit` | `1` | `1` adds modules `220` to `228` to `modules` |
| `agent` | empty | Name of the agent. When empty, `server` is used |
| `modules` | `[]` | JSON list of predefined module identifiers, for example `[120, 104]` |

Example:

```ini
agents_group_id = 10
threads         = 4
interval        = 300
server          = <SAP_HOSTNAME>
client          = <SAP_CLIENT>
system          = <SAP_SYSTEM_NUMBER>
credentials     = <BASE64_CREDENTIALS>
sec_audit       = 0
agent           = <AGENT_NAME>
modules         = [120, 104, 105, 109]
```

### Predefined modules

The **Wizard list** column tells whether the module can be chosen in **SAP modules**. Modules marked `No` can only be generated through the default selection, **Security and Audit Modules** or the `modules` key of the configuration file. Modules whose type is `async_string` are asynchronous.

#### System and availability

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `120` | SAP System info | `generic_data_string` | Yes |
| `160` | SAP Login status - Text | `generic_data_string` | Yes |
| `102` | Average time of SAPGUI response- Count | `generic_data` | No |
| `103` | Dialog Logged users - Count | `generic_data` | No |

#### Work processes

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `114` | WP DIA failed - Count | `generic_data` | Yes |
| `115` | WP BGD failed - Count | `generic_data` | Yes |
| `116` | WP UPD failed - Count | `generic_data` | Yes |
| `117` | WP UP2 failed - Count | `generic_data` | Yes |
| `118` | WP SPO failed - Count | `generic_data` | Yes |
| `119` | WP ENQ failed - Count | `generic_data` | Yes |
| `150` | WP with restart not active - Count | `generic_data` | Yes |
| `151` | WP stopped - Count | `generic_data` | Yes |
| `202` | WP DIA available - Count | `generic_data` | Yes |
| `203` | WP BGD available - Count | `generic_data` | Yes |
| `204` | WP UPD available - Count | `generic_data` | Yes |
| `302` | WP DIA available - Percent | `generic_data` | Yes |
| `303` | WP BGD available - Percent | `generic_data` | Yes |
| `304` | WP UPD available - Percent | `generic_data` | Yes |

#### IDocs

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `104` | IDOCs failed from yesterday - Count | `generic_data` | Yes |
| `105` | IDOCs ok from yesterday - Count | `generic_data` | Yes |

#### Dumps

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `108` | Dumps from yesterday - List | `async_string` | Yes |
| `109` | Dumps from yesterday - Count | `generic_data` | Yes |
| `123` | Dumps data from yesterday - Count | `generic_data` | Yes |
| `124` | Dumps data from yesterday - List | `async_string` | Yes |
| `125` | Dumps data today - Count | `generic_data` | Yes |
| `126` | Dumps data today - List | `async_string` | Yes |
| `128` | Dumps data from the last hour - Count | `generic_data` | Yes |
| `129` | Dumps data from the last hour - List | `async_string` | Yes |
| `148` | Dumps today - Grouped count list | `async_string` | Yes |
| `149` | Dumps today - Count | `generic_data` | Yes |

#### Jobs and batch input

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `112` | Jobs canceled from yesterday - List | `async_string` | Yes |
| `113` | Jobs canceled from yesterday - Count | `generic_data` | Yes |
| `122` | Jobs canceled from yesterday - Grouped count list | `async_string` | Yes |
| `121` | Batch input failed from yesterday - Count | `generic_data` | Yes |
| `142` | Jobs canceled today - List | `async_string` | Yes |
| `143` | Jobs canceled today - Count | `generic_data` | Yes |
| `144` | Jobs canceled today - Grouped count list | `async_string` | Yes |

#### External send operations

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `206` | External send operations not processed from yesterday - Count | `generic_data` | Yes |
| `207` | External send operations processed from yesterday - Count | `generic_data` | Yes |

#### Database

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `106` | Oracle tablespaces usage - List | `generic_data_string` | No |
| `107` | Oracle tablespaces usage greater equal 95% - Count | `generic_data` | No |
| `127` | Oracle tablespaces usage greater equal 99% - Count | `generic_data` | No |
| `130` | MS SQL log size | `generic_data` | No |
| `131` | MS SQL log free | `generic_data` | No |
| `132` | MS SQL log free % | `generic_data` | No |
| `210` | Hana free memory bytes | `generic_data` | No |
| `211` | Hana used memory bytes | `generic_data` | No |

#### Business and system data

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `110` | System block entries - List | `async_string` | Yes |
| `111` | System block entries - Count | `generic_data` | Yes |
| `1221` | Customers accounts open items - Count | `generic_data` | Yes |
| `1101` | Closing balance of customers accounts - List | `async_string` | Yes |
| `1110` | Customers accounts clearing transactions - Count | `generic_data` | Yes |
| `1201` | PFL parameters values - List | `async_string` | Yes |
| `1202` | Changes on auth profiles from yesterday - Count | `generic_data` | Yes |
| `1203` | Changes on auth profiles from yesterday - List | `async_string` | Yes |

#### RFC queues

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `190` | RFC Queue OUT - Count | `generic_data` | Yes |
| `191` | RFC Queue IN - Count | `generic_data` | Yes |
| `192` | RFC send tries failed - Count | `generic_data` | Yes |
| `193` | RFC send tries failed return O - Count | `generic_data` | Yes |
| `194` | RFC send tries failed return I - Count | `generic_data` | Yes |
| `195` | RFC Error queue OUT failed - Count | `generic_data` | Yes |
| `196` | RFC Error queue IN failed - Count | `generic_data` | Yes |
| `197` | RFC Queue OUT - Older entry seconds not processing | `generic_data` | Yes |
| `198` | RFC Queue IN - Older entry seconds not processing | `generic_data` | Yes |

#### Security and audit

| ID | Module | Type | Wizard list |
|----|--------|------|-------------|
| `220` | Users - Change passwords and block users (count) | `generic_data` | No |
| `221` | Users - Change passwords and block users (table) | `generic_data_string` | No |
| `222` | Users - Manage profiles (count) | `generic_data` | No |
| `223` | Users - Manage profiles (table) | `generic_data_string` | No |
| `224` | Users - Restart server application (count) | `generic_data` | No |
| `225` | Users - Restart server application (table) | `generic_data_string` | No |
| `226` | Users - Run and stop work processes (count) | `generic_data` | No |
| `227` | Users - Run and stop work processes (table) | `generic_data_string` | No |
| `228` | Month imported orders | `generic_data_inc_abs` | No |

### Addon identity

| Item | Value |
|------|-------|
| Name | SAP R3 |
| Identifier | `pandorafms.sap` |
| Version | `1.8` |
| Type and section | Discovery, `app` |
| Marketplace entry | [pandorafms.sap](https://marketplace.pandorafms.com/entries/pandorafms.sap), updated 2026-05-07 |
| Availability | The Marketplace entry states that the download is limited to licensed users |
