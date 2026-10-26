# Docker

*Article last updated: 2026-10-23.*

<!-- DRAFT: Static artifact verification only; distributed-package installation, live Docker collection and EndPoint ingestion remain unvalidated. -->

## What it monitors

The Docker plugin collects statistics from running containers and writes Pandora FMS module XML to standard output. Run it as an EndPoint plugin with `module_plugin` so the EndPoint includes the modules in its agent data. It is not a Discovery application and does not create or transfer separate agents.

Choose **global** mode for daemon-wide aggregate statistics or **container** mode for individually named container modules. Both modes report CPU, memory, network and block I/O; only global mode includes daemon state and the running-container count.

## Prepare

### Requirements and compatibility

| Scope | State | Requirement or limitation |
| --- | --- | --- |
| Docker daemon access | Required | The account running the plugin must be able to connect, ping the daemon, list running containers and read their statistics |
| Pandora FMS EndPoint | Required for ingestion | The EndPoint executes `module_plugin` and includes the returned XML in its own agent data |
| Module group | Prepare before use | The configuration defaults to `Docker`; create or select the intended group in Pandora FMS |
| Specific Docker, EndPoint and operating-system releases | Not validated | The older guide's Docker 18.03.1-ce development reference is not a compatibility statement for this artifact |

Place the distributed `docker_stats` executable and its configuration file on the machine where the EndPoint will execute it. Choose paths that the EndPoint account can access and ensure that it can execute the plugin and read the configuration. Installation and runtime requirements of the supplied package still need validation; this page does not prescribe a build or dependency-installation procedure.

The connection uses the process's Docker connection environment. There is no daemon host, token, password or certificate field in the plugin configuration. Confirm access under the **EndPoint account and execution environment**, not only under an interactive administrator session. No `docker_machine` procedure is established for this artifact, and `docker` does not select a connection or invoke a Docker executable.

Do not grant blanket administrative access merely to make the example run. Have the administrator authorize the required daemon access according to the deployment's security policy. Protect any connection credentials provided through the execution environment; do not place secrets in commands, logs or screenshots.

## Configure

### Write the plugin configuration

Use a plain text file with `key=value` lines, without a section header. This example retains the defaults and has not been executed:

```ini
docker=Docker
module_interval=1
module_group=Docker
mode=global
```

- Set `mode=container` to obtain modules per running container instead of the global modules.
- In container mode, `docker` is the **module-name prefix**. For example, `docker=Docker` produces names such as `Docker - <CONTAINER_NAME> - CPU Usage`. It is not an executable path or pre-command. Global module names ignore this setting.
- `module_group` and `module_interval` are written into every output module. `module_interval` is the module interval multiplier relative to the agent interval, not a delay or execution scheduler inside the plugin. Use the value appropriate to the EndPoint's execution schedule; the plugin passes it through without numeric validation.

### Register EndPoint execution

Add the following line to the EndPoint configuration, replacing both placeholders with the installed paths:

```text
module_plugin <PATH_TO_PLUGIN> --conf <PATH_TO_CONFIG>
```

The documented conventional paths can be used if that is where you installed the files:

```text
module_plugin /usr/share/pandora_agent/plugins/docker_stats --conf /usr/share/pandora_agent/plugins/docker_stats.conf
```

Apply the configuration through the EndPoint's normal configuration process. This is an agent-plugin registration, not a server-plugin or Discovery task setup. The examples above have not been executed against an EndPoint.

## Verify

1. Run the installed executable manually under the same account and connection environment as the EndPoint:

   ```bash
   <PATH_TO_PLUGIN> --conf <PATH_TO_CONFIG>
   ```

2. Inspect standard output. A clean global run produces 11 `<module>` fragments; container mode produces six per container whose statistics were collected. The output is not a complete `<agent_data>` document and has no Discovery summary or agent-transfer result.
3. Check module names, types, group and interval against the [reference](#reference), then compare representative values with the daemon's statistics. A zero value can also result from missing statistics or partial collection; inspect error text.
4. After an EndPoint collection cycle, confirm that the expected modules appear under **that EndPoint's agent**. Manual XML output alone does not verify ingestion or transport to Pandora FMS.

No live Docker run, package installation or EndPoint ingestion test was performed for this documentation. These are operator verification steps, not observed successful results.

## Understand the results

| Mode | Output | Interpretation |
| --- | --- | --- |
| `global` | 11 fixed-name modules | State, running count, average container CPU, total container memory against host memory, I/O counters and incremental variants |
| `container` | Six named modules per collected running container | CPU, memory against the container's limit, network input/output and block reads/writes; no global state/count modules |

Only containers listed as `running` are considered. Stopped containers do not receive new modules. With no running containers, global mode produces state plus zero count/usage/I/O values; container mode produces no modules.

### Value semantics

- **CPU:** calculated from CPU/system counter deltas and the reported CPU count. Global CPU is the sum of collected percentages divided by the number of listed running containers, including containers whose collection failed. It is not a sum of container CPU percentages or a host-wide CPU percentage.
- **Memory:** global usage is the sum of reported container memory usage divided by the daemon's host `MemTotal`. Container mode divides reported usage by the container's memory limit. Both multiply by 100. A missing/zero denominator produces `0`; a failure to read host information can therefore make global memory percentage `0` despite running containers.
- **I/O:** network bytes are summed across the container's returned interfaces. Block bytes are summed from returned read/write entries. Missing network/block statistics contribute `0`. The plugin outputs counters as `generic_data_inc`; it does not calculate a per-second rate itself.
- **Incremental CPU, memory and count:** global mode also emits these values as `generic_data_inc`. They repeat the corresponding snapshot values; do not interpret their processed rates as ordinary CPU/memory percentages or a running-container count.

In container mode, names depend on `docker` and the container name, not its short ID. Changing either changes module names; the short ID appears in descriptions. Use simple prefix/container names without XML-special characters: values are inserted into output XML without escaping, so such characters can make the output invalid.

## Operate and troubleshoot

Manual execution is a single collection run. The EndPoint provides scheduled execution. A scheduler can invoke the executable, but scheduling it alone does not ingest the printed module fragments into Pandora FMS; no standalone XML transfer is implemented here.

There is no plugin debug/verbose flag, pre-command, per-container agent transfer or server-plugin mode. Do not reuse `pre_command`, `metrics_per_container` or `as_server_plugin` settings from another Docker artifact.

| Signal | Check or limitation |
| --- | --- |
| `Error file: ... does not exist` | Supply an existing, nonempty configuration path readable by the execution account |
| `Error while reading configuration file: ...` | Check file access and `key=value` syntax; do not add a section header |
| `Could not connect to the Docker daemon...` | Check daemon availability and access from the EndPoint account/environment. Connection exceptions exit with status `1`, without emitting a `Docker state=0` module |
| `Warning: The information could not be obtained from the Docker system: ...` | Host information could not be read; global memory percentage uses `0` when host memory is unavailable |
| `Statistics could not be obtained for the container ...` | Global collection continues; totals may be partial while count and CPU divisor still include the listed container |
| `Detailed statistics for the container could not be obtained. ...` | Container collection continues with other containers; the affected container can be absent |
| `Invalid operating mode: ...` | Use `global` or `container`; matching is case-insensitive |
| `Fatal error in plugin execution: ...` | A collection/output error prevented normal completion; inspect the reported detail |
| Empty output in container mode | There may be no running containers, or every container's statistics may have failed |
| Output exists but modules are not ingested | Inspect `module_plugin` paths, execution account, configuration, connection environment and EndPoint collection/transport. Error text can be mixed into standard output and invalidate module XML |

Configuration, connection, invalid-mode and fatal failures exit with status `1`. Argument errors are handled by the CLI help/parser. Per-container failures and host-information warnings can leave a normal exit with partial output: exit status alone is not proof of complete collection. Review output safely before sharing it, because errors/descriptions can include daemon or container identifiers.

## Reference

### Command line

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `--conf <PATH_TO_CONFIG>` | Yes | None | Configuration file path |
| `-h`, `--help` | No | Not applicable | Display argument help and exit |

### Configuration file

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `docker` | No | `Docker` | Prefix for container-mode module names; ignored for global names; not an executable path |
| `module_interval` | No | `1` | Written as `<module_interval>` in each module; no numeric validation in the plugin |
| `module_group` | No | `Docker` | Written as `<module_group>` in each module; prepare the intended Pandora FMS group |
| `mode` | No | `global` | `global` or `container`, case-insensitive; other values cause an error |

These are the four configuration keys consumed by this artifact. A commented `module_tags` line in an older example does not define a supported input here. The plugin exposes no separate connection-related environment-variable reference; its connection is inherited from the execution environment.

### Global modules

| Name | Type | Unit | Value |
| --- | --- | --- | --- |
| `Docker state` | `generic_proc` | — | Result of the daemon ping: `1` for true, `0` for false; connection exceptions abort before output |
| `Docker containers running` | `generic_data` | — | Number of listed running containers |
| `Docker CPU usage` | `generic_data` | `%` | Average container CPU percentage as described above, with two decimal places |
| `Docker memory usage` | `generic_data` | `%` | Reported container memory total against host memory, with two decimal places |
| `Docker network input` | `generic_data_inc` | `B` | Summed received bytes |
| `Docker network output` | `generic_data_inc` | `B` | Summed transmitted bytes |
| `Docker blocks in` | `generic_data_inc` | `B` | Summed block-read bytes, not writes or block counts |
| `Docker blocks out` | `generic_data_inc` | `B` | Summed block-write bytes, not reads or block counts |
| `Docker containers running incremental` | `generic_data_inc` | — | Same running count as the snapshot module |
| `Docker CPU usage incremental` | `generic_data_inc` | `%` | Same average CPU value as the snapshot module |
| `Docker memory usage incremental` | `generic_data_inc` | `%` | Same memory percentage as the snapshot module |

### Container modules

Each full name is `<PREFIX> - <CONTAINER_NAME> - <SUFFIX>`, where `<PREFIX>` is the `docker` value. All six are emitted for each successfully collected container; CPU and memory percentages have two decimal places.

| Suffix | Type | Unit | Value |
| --- | --- | --- | --- |
| `CPU Usage` | `generic_data` | `%` | Container CPU percentage |
| `Memory Usage %` | `generic_data` | `%` | Reported usage against the container's memory limit; description also includes usage/limit |
| `Network Input` | `generic_data_inc` | `B` | Received bytes summed across interfaces |
| `Network Output` | `generic_data_inc` | `B` | Transmitted bytes summed across interfaces |
| `Block Read` | `generic_data_inc` | `B` | Block-read bytes |
| `Block Write` | `generic_data_inc` | `B` | Block-write bytes |

Each module contains name, type, data, description, module group, module interval and unit fields. For global modules without a defined unit, this artifact emits the literal text `None` in the unit field; `—` in the table means no meaningful unit. Verify handling by the receiving EndPoint rather than treating this page as an ingestion test.
