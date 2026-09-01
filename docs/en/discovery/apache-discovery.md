# Apache Discovery

*Article last updated: 2026-09-01.*

## What it monitors

Apache Discovery queries the machine-readable Apache HTTP Server `mod_status` endpoint. A Discovery task creates one Pandora FMS agent per unique URL network location (or per unique configured `agent_name`) and adds an availability module plus one module for every parsed, non-filtered `key: value` line returned by Apache.

The plugin can process URLs entered in the Discovery task, a key/value configuration file, or a file containing multiple named configuration sections. It generates and transfers Pandora FMS XML data files for the resulting agents.

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Plugin version `1.5` | Documented target | The version this page describes, as identified by the distributed package and its Marketplace entry. |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that its integrations are compatible with these versions. This is a published compatibility statement covering the plugin, not a test record for it. |
| Any operating system running the plugin | `Not validated` | No published test record establishes operating-system compatibility for this plugin. |
| Any specific Apache HTTP Server version or MPM | `Not validated` | No published test record establishes Apache-version compatibility. Available metrics vary by version, MPM and enabled modules. |
| A machine-readable `mod_status` response | `Required` | Prerequisite, not a compatibility statement. See [Requirements](#requirements). |

The package is available to licensed Pandora FMS ONE users from the [Pandora FMS Marketplace](https://marketplace.pandorafms.com/entries/pandorafms.apache). Distribution follows the Pandora FMS ONE licensing model; the Marketplace entry states the applicable terms.

### Requirements

- A packaged `pandora_apache` executable.
- Network access from the system that runs the plugin to each Apache status URL.
- Apache `mod_status` enabled with a machine-readable `server-status?auto` response.
- Basic-authentication credentials when the status endpoint requires them. The plugin applies authentication only when both username and password are present.
- A transfer destination accepted by the packaged Pandora plugin tools.

### Configure Apache `mod_status`

Enable a status location in the applicable Apache configuration and restrict it to the system that runs the plugin:

```apache
<Location "/server-status">
    SetHandler server-status
    Require ip <MONITORING_HOST_IP>
</Location>
```

`Require all granted` exposes operational server information broadly. Do not use it unless that exposure is explicitly intended and protected by other controls. See the authoritative [Apache `mod_status` documentation](https://httpd.apache.org/docs/2.4/mod/mod_status.html) for target-side configuration and security details.

After applying the Apache configuration through the procedure appropriate for the target system, verify the machine-readable endpoint:

```bash
curl "https://<TARGET_HOST>/server-status?auto"
```

The response must contain plain-text `key: value` lines. Protect the endpoint with appropriate network restrictions, authentication, and TLS.

### Install the Discovery package

Obtain the Apache Discovery package from the [Pandora FMS Marketplace](https://marketplace.pandorafms.com/entries/pandorafms.apache) and load the `.disco` package into Pandora FMS. The plugin is distributed under Pandora FMS ONE licensing; consult the Marketplace entry for the applicable terms.

## Configure the Discovery task

Create an Apache application Discovery task after loading the package. The package defines two configuration steps: `Apache Basic` and `Apache Detailed`.

In `Apache Basic`, configure direct target URLs and transfer settings. All UI fields are optional individually, but the task needs at least one URL in this step or a target section in `Apache Detailed` to collect data.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `Apache Urls` | No | Empty | One or more Apache status URLs, separated by commas or line breaks. |
| `User` | No | Empty | Basic-authentication username. Used only when a password is also present. |
| `Password` | No | Empty | Basic-authentication password. Used only when a username is also present. |
| `Verify SSL` | No | `true` | Requires an HTTPS URL and verifies its certificate when enabled. |
| `transfer mode` | No | `tentacle` | XML transfer mode passed to the plugin tools. |
| `tentacle ip` | No | `127.0.0.1` | IPv4 destination used by Tentacle transfer. |
| `tentacle port` | No | `41121` | Tentacle destination port. |
| `Module Group` | No | Empty | Module group selected for generated modules; an empty value is handled as group `0`. |

![Apache Basic Discovery task step](../assets/images/discovery/apache-discovery/wizard-basic.png)

In `Apache Detailed`, use `Advance Apache` for one or more named configuration sections and optionally set the task-level `User-Agent` value.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `Advance Apache` | No | Commented example template | INI content with one uniquely named section per target. Each section requires `urls` for collection. |
| `User-Agent` | No | Empty | Custom HTTP `User-Agent` header applied only to the `Apache Urls` targets. It is written to the temporary key/value configuration consumed by the plugin, so `Advance Apache` sections never receive it; each of those sections applies only its own `user_agent` key. |

Credentials entered in the task are written to a temporary key/value configuration consumed by the plugin. Restrict access to Pandora FMS and its configuration and temporary files according to the deployment's security policy.

## Verify

Run the task and confirm these observable results:

1. The execution summary reports at least one generated agent and module.
2. Each unique URL network location (or unique configured `agent_name`) produces an agent with an `Apache Connection` module.
3. A reachable status endpoint sets `Apache Connection` to `1`; a request failure still creates or updates the agent and sets this module to `0`, with the request error in its description.
4. Parsed Apache values appear as additional modules. The exact set depends on the response.

![Apache Discovery execution summary](../assets/images/discovery/apache-discovery/task-summary.png)

A task can create an agent and still report diagnostic information when expected metrics are absent. Review the execution information instead of treating agent creation alone as complete success.

## Understand the results

For each URL without a configured `agent_name`, the plugin derives the internal Pandora FMS agent name as the MD5 of the URL network location, which also becomes the readable alias. When `agent_name` is configured, the internal name is the MD5 of that value, which also becomes the alias. Agent identity is therefore not per-URL: URLs that share a network location, such as different paths on the same host and port, share a single agent, and their modules accumulate on it. URLs or sections configured with the same `agent_name` also share a single agent.

Every agent receives `Apache Connection` as a `generic_proc` module. Every other parsed, non-filtered `key: value` becomes either `generic_data` when its value is numeric or `generic_data_string` otherwise. `CurrentTime`, `RestartTime`, `Scoreboard`, `ServerUptime`, and `TLSSessionCacheStatus` are filtered. Other parsed keys are emitted even when they are not in the plugin's known-description list.

Known keys include `ServerVersion`, `ServerMPM`, `Server Built`, `ParentServerConfigGeneration`, `ParentServerMPMGeneration`, `ServerUptimeSeconds`, `Load1`, `Load5`, `Load15`, `Total Accesses`, `Total kBytes`, `Total Duration`, `CPUUser`, `CPUSystem`, `CPUChildrenUser`, `CPUChildrenSystem`, `CPULoad`, `Uptime`, `ReqPerSec`, `BytesPerSec`, `BytesPerReq`, `DurationPerReq`, `BusyWorkers`, `GracefulWorkers`, `IdleWorkers`, `Processes`, `Stopping`, `ConnsTotal`, `ConnsAsyncWriting`, `ConnsAsyncKeepAlive`, `ConnsAsyncClosing`, and the `Cache*` metrics defined by the plugin. This list supplies descriptions; it is not an output allowlist. In particular, `ReqPerSec` and `BytesPerSec` are emitted when Apache returns them.

![Modules generated by the Apache Discovery task](../assets/images/discovery/apache-discovery/module-list.png)

When `module_prefix` is set, the plugin prepends it directly to every generated module name, including `Apache Connection`, without adding a separator.

## Troubleshoot

| Symptom | Check |
| --- | --- |
| The task reports that URL and configuration inputs are empty | Provide at least one target through `Apache Urls`, `--conf`, or `--string_conf`. |
| HTTPS verification fails | Confirm the URL uses HTTPS and presents a certificate trusted by the plugin host. `Verify SSL`/`--ssl` set to `true` rejects HTTP URLs. |
| The task works only with verification disabled | Correct the target certificate or trust chain. A `false` value disables certificate verification and suppresses the related warning; use it only after assessing the interception risk. |
| `Apache Connection` is `0` | Check network reachability, authentication, HTTP status, target URL, and access restrictions on `server-status`. The module description contains the request error. |
| Fewer modules appear than expected | Inspect the raw `?auto` response. Apache versions, MPMs, and optional modules can expose different keys; the Discovery information lists a bounded subset of missing known keys. |
| Server-plugin mode prints `0` although an agent exists | This mode prints `1` only when at least one agent was counted and `info_value` is empty. Missing expected metrics or another diagnostic can therefore produce `0` after agent creation. |
| XML transfer fails | Verify the selected transfer mode and its destination. Transfer failures are added to the execution information. |

The plugin has no verbose or debug CLI flag. Its diagnostics are returned through Discovery execution information.

## Reference

### CLI parameters

At least one of `--urls`, `--conf`, or `--string_conf` is operationally required. When several are supplied, the plugin processes each applicable surface.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `--urls` | Conditional | Not set | Comma- or newline-separated status URLs. Required when no configuration file supplies a target. |
| `--conf` | Conditional | Not set | Path to one key/value configuration with no section header; the plugin prepends `[CONF]`. |
| `--string_conf` | Conditional | Not set | Path to an INI file containing one or more named target sections. |
| `--user` | No | Not set | Basic-authentication username for `--urls`; used only with `--password`. |
| `--password` | No | Not set | Basic-authentication password for `--urls`; used only with `--user`. |
| `--user_agent` | No | Not set | Custom HTTP `User-Agent` header for `--urls`. |
| `--ssl` | No | `true` | Parses `yes`, `true`, `t`, `y`, or `1` as enabled; other values disable verification. Enabled verification also requires HTTPS. |
| `-tm`, `--transfer_mode` | No | `tentacle` | XML transfer mode. |
| `-ti`, `--tentacle_ip` | No | `127.0.0.1` | Tentacle destination; the CLI validator accepts IPv4 format. |
| `-tp`, `--tentacle_port` | No | `41121` | Tentacle destination port. |
| `-in`, `--interval` | No | Not set | Agent interval in seconds. |
| `--as_server_plugin` | No | `false` | Prints only `1` or `0` and exits instead of printing Discovery output. |

Passing `--user` and `--password` exposes credentials in the command line, where shell history and the operating-system process list may reveal them. Prefer a protected configuration file when manual execution requires authentication, and restrict that file to the account that runs the plugin.

### Configuration file parameters

The `--conf` file contains key/value lines only. Do not add `[CONF]`, because the plugin adds that section header before parsing. A `--string_conf` file instead requires one or more uniquely named INI sections.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `urls` | Yes per target | Empty | Comma- or newline-separated status URLs. |
| `agent_name` | No | Empty | Readable alias source; the internal name is its MD5 value. |
| `module_prefix` | No | Empty | Text prepended directly to module names. |
| `username` | No | Empty | Basic-authentication username; used only with `password`. |
| `password` | No | Empty | Basic-authentication password; used only with `username`. |
| `verify_ssl` | No | `false` | Certificate-verification boolean for configuration-file targets. |
| `transfer_mode` | No | Empty | XML transfer mode. |
| `tentacle_ip` | No | Empty | Tentacle destination. |
| `tentacle_port` | No | Empty | Tentacle destination port. |
| `interval` | No | `0` | Agent interval after integer parsing when omitted or invalid. |
| `user_agent` | No | Empty | Custom HTTP `User-Agent` header. |
| `module_group` | No | `0` | Empty values are normalized to module group `0`. |

Protect configuration files as plaintext secrets when they contain credentials. Do not place them in shared directories, logs, or version control.

Example `--conf` file:

```ini
urls=https://<TARGET_HOST>/server-status
agent_name=<READABLE_ALIAS>
username=<USERNAME>
password=<PASSWORD>
verify_ssl=true
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER_IPV4>
tentacle_port=41121
interval=300
module_group=0
```

Example `--string_conf` file:

```ini
[apache_target_1]
urls=https://<TARGET_HOST>/server-status
agent_name=<READABLE_ALIAS>
verify_ssl=true
transfer_mode=tentacle
tentacle_ip=<PANDORA_FMS_SERVER_IPV4>
tentacle_port=41121
```

### Manual execution

Run the packaged executable with safe placeholders:

```bash
./pandora_apache \
  --urls "https://<TARGET_HOST>/server-status" \
  --ssl true \
  --transfer_mode tentacle \
  --tentacle_ip <PANDORA_FMS_SERVER_IPV4> \
  --tentacle_port 41121
```

The plugin appends `?auto` when the URL query does not already contain `auto`. Normal execution prints Discovery output with total-agent and total-module summaries and transfers one XML data file per generated agent.

With `--as_server_plugin true`, output is `1` only when at least one agent was counted and no information message was recorded. Every other result prints `0`.
