# Oculix

## Introduction

**Ver**. 03-06-2026

This document describes the functionality of the Oculix plugin and its integration with PandoraFMS. The Oculix plugin enables visual automation of transactions through screenshots, image comparison, and script execution, generating monitoring modules in PandoraFMS.

**Type**: Plug-in server

## Compatibility matrix

| **Systems where tested** | Rocky Linux, Windows Server 2022 |
| --- | --- |
| **Systems where it works** | Any Linux or Windows system |

## Prerequisites

**1. Java Runtime Environment**  
The plugin runs an Oculix JAR file, so it is necessary to have Java installed and accessible in the system PATH. Java 17 or higher is recommended.

**2. Graphical environment**  
The plugin uses `mss` to take screenshots, so it requires a running X11 server (graphical environment). If running in a headless environment, a virtual X server such as `Xvfb` can be used.

**3. The agent runs in process mode, and the session cannot be locked or closed.**  
Once launched by the Pandora FMS Agent, it must run in process mode; if it runs in service mode, it will not function properly. Additionally, it will not be possible to lock the desktop session, so it is recommended to use it on virtual machines.

**3. Write permissions**  
The plugin needs write permissions in the artifacts directory (`--artifacts`) to store screenshots, baseline images, and diffs.

**4. Tentacle (optional)**  
If the `tentacle` transfer mode is used, the `tentacle_client` binary must be installed and accessible on the system.

## Parameters

**Script execution parameters**

| Parameter | Description |
| --- | --- |
| **--script** | Path to the Oculix script to execute. This parameter is mandatory. **Supports commas** for multiple phases: `--script a.py,b.py,c.py` |
| **--jar** | Path to the Oculix JAR file. This parameter is mandatory. |
| **--conf** | Path to the .conf configuration file with Pandora and connection parameters. This parameter is mandatory. |
| **--workspace** | Working directory for Oculix script execution. Optional. |
| **--debug** | Debug verbosity (0 silent → 3 very verbose) |
| **--console** | Enables Oculix console mode. Activated with the flag. |
| **--native-access** | Enables `--enable-native-access=ALL-UNNAMED` in Java execution. Activated with the flag. |
| **--checkpoint** | Enables baseline logic: if no reference image exists, creates one from the current screenshot. Activated with the flag. |
| **--artifacts** | Directory where screenshots, baselines, and diffs are stored. Default "artifacts". |
| **--phase-names** | Phase names separated by commas (e.g. `Login,Search,Logout`). If omitted, the script stem is used. Also configurable in .conf as `phase_names`. **CLI overrides .conf.** |
| **--transaction** | Global transaction name. If set, `Global_Status_{name}`, `Global_Time_{name}` and `Global_Last_Image_{name}` modules are generated. Also configurable in .conf as `transaction_name`. **CLI overrides .conf.** |
| **--retries** | Number of retries for the full transaction (default: 1). If any phase fails, all phases are retried from the start. Also configurable in .conf as `phase_retries`. **CLI overrides .conf.** |
| **--post-command** | Command to execute after all phases complete. CLI-only argument, not available in .conf. |

**Pandora configuration parameters (.conf file)**

| Parameter | Description |
| --- | --- |
| **agent_name** | Name of the agent that will contain the modules. Default: "{script} Oculix". |
| **agents_group_name** | Agent group in PandoraFMS. Default "Oculix". |
| **module_prefix** | Prefix for all modules created by the plugin. |
| **interval** | Agent monitoring interval in seconds. Default 300. |
| **agent_plugin** | Output mode: 1 prints XML to console, 0 writes to file and transfers. Default 0. |
| **temporal** | Temporary directory for XML files. Default "/tmp". |
| **transfer_mode** | Transfer mode: "tentacle" or "local". Default "tentacle". |
| **tentacle_client** | Path to the tentacle_client binary. Default "tentacle_client". |
| **tentacle_ip** | IP address of the tentacle server. Default "127.0.0.1". |
| **tentacle_port** | Tentacle connection port. Default "41121". |
| **tentacle_opts** | Extra options for tentacle connection. |
| **data_dir** | PandoraFMS data directory for local transfer. Default "/var/spool/pandora/data_in/". |

## Manual execution

### Execution format

```
./pandora_oculix.exe --script <path to oculix script> \
--conf <path to .conf file> \
--jar <path to oculix JAR> \
[--workspace <working directory>] \
[--debug <debug level>] \
[--console] \
[--native-access] \
[--checkpoint] \
[--artifacts <artifacts directory>] \
[--phase-names <phase names, comma-separated>] \
[--transaction <transaction name>] \
[--retries <number of retries>] \
[--post-command <command to execute after completion>]

```

#### Examples

Single script (backward compatible):

```
./pandora_oculix.exe --script scripts/login.py --conf oculix.conf --jar oculix.jar --debug 1

```

With baseline and console:

```
./pandora_oculix.exe --script scripts/login.py --conf oculix.conf --jar oculix.jar --console --checkpoint

```

Multi-phase transaction with retries:

```
./pandora_oculix.exe --script login.py,search.py,logout.py --phase-names Login,Search,Logout --transaction "MiApp" --retries 2 --conf oculix.conf --jar oculix.jar --debug 1

```

With post-command after completion:

```
./pandora_oculix.exe --script login.py,search.py,logout.py --phase-names Login,Search,Logout --transaction "MiApp" --post-command "echo Done" --conf oculix.conf --jar oculix.jar --debug 1

```

## Configuration in PandoraFMS

To configure the plugin in PandoraFMS, follow these steps:

**1. Upload the plugin to PandoraFMS, e.g. in the following path:**

```
/usr/share/pandora_server/util/plugin
```

**2. Upload the Oculix JAR and the required .ocx scripts to the server, in a path accessible by the plugin.**

**3. Create the .conf configuration file with Pandora parameters:**

```ini
[CONF]
agent_name=Oculix Login Test
agents_group_name=Oculix
module_prefix=
interval=300
agent_plugin=1
temporal=/tmp
transfer_mode=tentacle
tentacle_client=tentacle_client
tentacle_ip=127.0.0.1
tentacle_port=41121
tentacle_opts=
data_dir=/var/spool/pandora/data_in/
```

**4. Go to the plugins section and create a new one:**

Add a name, description, and timeout.

**5. Add the plugin path in the command and the necessary parameters for its execution.**

<p class="callout info">For each parameter, a macro must be configured. The macro syntax is: `_fieldx_`, where x is the positional number of the parameter.</p>

Example plugin command:

```
/usr/share/pandora_server/util/plugin/pandora_oculix.py --script _field1_ --jar _field2_ --conf _field3_
```

**6. Configure the macros above, adding the parameter value in each one:**

Example macros:

- `_field1_` = /opt/oculix/scripts/login.py
- `_field2_` = /opt/oculix/oculix.jar
- `_field3_` = /opt/oculix/oculix.conf

**7. Once configured, a module must be created in an agent to run the plugin. In an agent's module menu, create a new plugin-type module:**

**8. In the module configuration menu, give it a name, select the previously configured plugin, and click "create".**

**9. The agent with the modules will be created on the next execution of the plugin.**

## Agent and modules generated by the plugin

The plugin creates an agent with the name specified in `agent_name` (default "{script} Oculix") containing the following modules:

| **Module name** | **Type** | **Description** |
| --- | --- | --- |
| {script_name} status | generic_proc | Script execution status. Value 1 if execution was successful, 0 if there was an error or visual difference. |
| {script_name} time | generic_data | Script execution time in seconds. |
| {script_name} last_image | async_string | Screenshot in base64 format (PNG image). Only generated when the status is 0 (failure or visual difference). |

Example: for a script called `login`, the generated modules would be:

```
login status
login time
login last_image
```