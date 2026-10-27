# OpenShift Discovery

*Article last updated: 2026-10-23.*

<!-- DRAFT: Static verification for Discovery package 1.0 only; package installation, target-version UI and live collection remain unvalidated. -->

## What it monitors

OpenShift Discovery reads the cluster API and produces a global agent plus agents for nodes, pods and deployments. The Discovery task generates agent XML and sends it through Tentacle. The global agent summarizes services, namespaces, component statuses, replication controllers and API services; resource agents report capacity, conditions and container CPU/memory.

This page covers the Discovery application, not the older OpenShift CLI/server plugin. Do not reuse that plugin's `cli`, `user`, `password`, `project`, `agent_*` or `as_server_plugin` settings here.

## Prepare

### Compatibility and requirements

| Scope | State | Requirement or limitation |
| --- | --- | --- |
| `pandorafms.openshift`, package `1.0` | Documented target | Discovery application (`.disco`) |
| Pandora FMS Discovery server and console | Required | Define and execute the application task |
| OpenShift API reachable from Discovery | Required | Direct connections use `https://<TARGET_HOST>:<API_PORT>` |
| Bearer token | Required for protected direct endpoints | Read access to the exact resources and health paths in [API requests](#api-requests); no validated least-privilege role is supplied |
| Metrics API (`metrics.k8s.io/v1beta1`) | Required for node/pod discovery | Discovery starts from metrics, not just from resource lists |
| Tentacle destination | Required for delivery | Reachable from the Discovery server |
| Specific OpenShift, Pandora FMS or host OS releases | Not validated | No release-specific compatibility or live test result is established here |

Obtain the `.disco` package from the [OpenShift Marketplace entry](https://marketplace.pandorafms.com/entries/pandorafms.openshift) and load it as a Discovery application. Select the application named **Openshift** in its package definition. No `oc` executable, CLI login or project parameter is used by this task.

Ask the cluster administrator to provide API access and confirm node/pod metrics are available. The administrator must authorize the queried surface; the older CLI guide's role and local cluster setup are not a validated access policy for this application.

### Connection safety

Direct API requests use HTTPS **without certificate verification**, so they do not authenticate the server identity. Restrict network access. The task stores the token in its generated configuration file; protect task configuration and file access. Manual runs should use a protected configuration file, not a token in command arguments.

With **Use proxy** enabled, requests use **Proxy url** and omit the Bearer header. The proxy URL must include its scheme. No request timeout is configured by this package; network delays can hold up collection.

## Configure the Discovery task

Define the task name, execution server, agent group and interval in Discovery. All generated agents inherit the task group and interval. The package defines two configuration steps, **Openshift base** and **Openshift detailed**. The exhaustive field reference is below.

1. In **Openshift base**, provide **Openshift host** without a scheme, **Openshift port**, and **Openshift token** for direct API access. For proxy access, enable **Use proxy** and supply **Proxy url** instead.
2. Set **Tentacle IP** and **Tentacle port** to the destination that receives the generated XML; defaults are `127.0.0.1` and `41121`.
3. In **Openshift detailed**, choose **Scan Deployments**, **Scan Nodes** and **Scan Pods**. All default to enabled.
4. Run the task and inspect its execution information and generated agents.

There are no wizard controls for namespace filtering, prefixes, health checks, components, operators or imagestreams. The three scan switches control resource-agent generation; metrics, deployment and global requests still run when those switches are disabled.

<!-- SCREENSHOT NEEDED: Safe OpenShift Discovery 1.0 base and detailed steps, with empty credentials, to validate the rendered target-version interface. -->

## Verify the first run

1. Inspect the Discovery summary: **Total agents**, **Nodes agents**, **Pods agents**, and **Deployments agents** count generated agents. They do not confirm successful Tentacle delivery.
2. Check the global **Openshift** agent and the resource categories enabled in the task. Node/pod agents require complete metric, allocation, node and IP data. Deployment agents require a condition of type `Available` or `Progressing` with status `True`.
3. Compare representative replica counts and CPU/memory values with the target cluster. Percentages use the node's allocatable resources, not container requests or limits.
4. Inspect execution errors before treating missing agents or modules as absence of resources. A partial run can produce some agents and still report failures.

**Do not use `API status = 1` as proof of connectivity:** this package always assigns that value. Check the health endpoint modules and request errors. Likewise, deployment `Available` is always `0` for generated deployments in this package; verify actual availability from replicas and cluster conditions.

No live cluster execution or package installation was performed for this documentation. The manual example below is unexecuted.

## Understand the results

### Agents and identity

| Agent | Alias | Parent |
| --- | --- | --- |
| Global | `Openshift` | None |
| Node | `<NODE_NAME>` | `Openshift` |
| Deployment | `<DEPLOYMENT_NAME>` | `Openshift` |
| Pod | `<POD_NAME>` | Its node |

The task does not expose a prefix. Manual configuration accepts `prefix`, prepending it to aliases and identities. Nodes then use the prefixed global parent and pods the prefixed node; deployments still refer to unprefixed `Openshift`. Pod agents use the pod IP as their address.

Pod and deployment identities omit the namespace. Equal names in different namespaces can collide; unprefixed identities can also collide across clusters. There is no namespace filter in this application. Changing a manual prefix changes generated identities; the deployment-parent limitation still applies.

### Functional summary

| Agent | Results |
| --- | --- |
| Global | Health checks, service/namespace counts and lists, components, replication-controller and API-service counts/status lists, deployment count |
| Node | Collected pod count and capacity percentage, CPU/memory and node conditions |
| Deployment | Desired, updated, ready, available and unavailable replicas; `Available` and `Progressing` modules with the limitations below |
| Pod | Phase, one condition module, container count and per-container CPU/memory |

Node agents originate from node metrics; pod agents originate from pod metrics. Incomplete data can interrupt an entire processing stage and leave partial output. The node `Pods` count reflects processed pods with metrics, not a separately validated count of every scheduled pod.

Node conditions are **not normalized to healthy = 1**: every returned condition is `1` for status `True`, otherwise `0`, including pressure conditions. Pod output contains only the **last returned condition**, not a module for every condition. Check the module name before interpreting its value.

## Operate

### Manual execution

Use the distributed executable with a protected file of `key=value` lines:

```bash
pandora_openshift --conf <PATH_TO_CONFIG>
```

Replace all placeholders in this unexecuted direct-mode example:

```ini
ip=<TARGET_HOST>
port=<API_PORT>
token=<API_TOKEN>
agents_group_name=<AGENT_GROUP>
interval=300
transfer_mode=tentacle
tentacle_ip=<TENTACLE_HOST>
tentacle_port=41121
use_proxy=0
deployments=1
nodes=1
pods=1
```

Execution produces Discovery JSON with generation counters and creates/transfers agent XML. An illustrative summary is `{"summary":{"Total agents":4,"Nodes agents":1,"Pods agents":1,"Deployments agents":1}}`. Do not apply the older server plugin's numeric success/error codes to this executable. `-h`/`--help` displays argument help.

## Troubleshoot

| Signal | Check |
| --- | --- |
| `Error en la solicitud a <endpoint>: <status>` | Inspect host, port, endpoint reachability and HTTP status. For `401`/`403`, check the token and authorization for that exact path. Direct host values must not contain a scheme. |
| `Can't get metrics`, `Error: Nodes` or `Error: Pods` | Check Metrics API responses, allocatable CPU/memory/pods, assigned nodes, pod IPs and condition data. Missing fields can interrupt collection or generation. |
| Missing deployments or `Error: Deployments` | Check the scan switch, returned deployment data and a `True` `Available`/`Progressing` condition. |
| `Available` is `0` although the deployment is available | A package limitation makes this value unreliable; use replica counts and cluster conditions. |
| `Progressing` is `0` although that condition is `True` | The selected status is the first matching `True` `Available`/`Progressing` condition. A preceding `Available` condition takes precedence. |
| `API status` remains `1` during API failures | It is a constant, not a connectivity test. Inspect health modules and execution errors. Failed health requests omit their modules. |
| Missing global modules or `Error: global_agent` | Inspect each request and the deployment data. Failed optional global requests can omit individual module groups; other incomplete data can prevent global-agent transfer. |
| Only one pod condition appears | This version emits only the final condition returned for the pod. |
| Collection stalls | There is no configured HTTP request timeout; inspect network connectivity and task execution. |
| Proxy access fails | Check the complete proxy base URL and its authentication arrangement; the task does not send the Bearer header in proxy mode. |
| Agents counted but not received | Check connectivity to the configured Tentacle destination; summary counters precede transfer. |

## Reference

### Console fields — Openshift base

| Name | Macro | Required | Default | Description |
| --- | --- | --- | --- | --- |
| Openshift host | `_ip_` | Direct mode | Empty | API server host without scheme |
| Openshift port | `_port_` | Direct mode | Empty | Numeric API port |
| Openshift token | `_token_` | Protected direct endpoints | Empty | Bearer token; the wizard permits empty input |
| Use proxy | `_useProxy_` | No | off | Uses proxy URL without Bearer header |
| Proxy url | `_proxyUrl_` | Proxy mode | Empty | Base URL including scheme; visible when Use proxy is enabled |
| Tentacle IP | `_tentacleIP_` | Yes | `127.0.0.1` | XML destination |
| Tentacle port | `_tentaclePort_` | Yes | `41121` | Numeric transfer port |

### Console fields — Openshift detailed

| Name | Macro | Required | Default | Description |
| --- | --- | --- | --- | --- |
| Scan Deployments | `_scanDeployments_` | No | on | Generates eligible deployment agents |
| Scan Nodes | `_scanNodes_` | No | on | Generates node agents from collected metrics |
| Scan Pods | `_scanPods_` | No | on | Generates pod agents from collected metrics |

### Configuration file

These defaults apply to manual execution unless the table specifies task values. Discovery supplies group, interval, transfer and console fields automatically. Integer scan/proxy switches use `1` to enable, `0` to disable.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `ip` | Direct mode | Empty | API host without scheme |
| `port` | Direct mode | Empty | API port |
| `token` | Protected direct endpoints | Empty | Bearer token; protect the file |
| `use_proxy` | No | `0` | Use proxy without Bearer header |
| `proxy_url` | Proxy mode | Empty | Base URL including scheme |
| `agents_group_name` | No | Empty; task group in Discovery | Agent group |
| `interval` | No | `300`; task interval in Discovery | Agent interval in seconds |
| `prefix` | No | Empty | Manual-only identity prefix; not exposed in the wizard |
| `transfer_mode` | For delivery | Empty; `tentacle` in Discovery | Use `tentacle` for this documented transfer path |
| `tentacle_ip` | For Tentacle | Empty; `127.0.0.1` in Discovery | Transfer destination |
| `tentacle_port` | No | `41121` | Transfer port |
| `deployments` | No | `1` | Generate deployment agents |
| `nodes` | No | `1` | Generate node agents |
| `pods` | No | `1` | Generate pod agents |
| `data_dir` | No | Empty | Accepted, but does not select the XML output directory |

### Generated modules

#### Global agent

| Name | Type | Value or condition |
| --- | --- | --- |
| `API status` | `generic_proc` | Constant `1`, not evidence of API health |
| One module per health endpoint below | `generic_proc` | `1` for response exactly `ok`, otherwise `0`; omitted on request failure |
| `Services count` | `generic_data` | Number of returned services |
| `List Services` | `generic_data_string` | Service names |
| `Namespaces count` | `generic_data` | Number of returned namespaces |
| `List Namespaces` | `generic_data_string` | Namespace names |
| `Components` | `generic_data` | Number of component statuses |
| `<component>.<condition>` | `generic_proc` | `1` only for status exactly `TRUE`, otherwise `0` |
| `Replication Controllers count` | `generic_data` | Number of returned replication controllers |
| `Replication Controllers Status` | `generic_data_string` | Entries `<name>.<namespace>.Status : <status>` |
| `APIServices count` | `generic_data` | Number of registered API services |
| `APIServices Status` | `generic_data_string` | Entries `<name>.Status : <conditions>` |
| `Deployments` | `generic_data` | Number of returned deployments, independent of generation switches |

Service, namespace, component, replication-controller and API-service groups require a successful corresponding response. This application does not generate the older CLI plugin's imagestream, operator, CSV or separate pod-statistics agents.

#### Node agents

| Name | Type | Unit | Value |
| --- | --- | --- | --- |
| `Pods` | `generic_data` | — | Processed pod count on the node |
| `Pods (%)` | `generic_data` | `%` | Count divided by allocatable pod capacity, multiplied by 100 |
| `CPU (cores)` | `generic_data` | `cores` | Node CPU usage |
| `CPU (%)` | `generic_data` | `%` | Usage against allocatable node CPU |
| `Memory (bytes)` | `generic_data` | `bytes` | Node memory usage |
| `Memory (%)` | `generic_data` | `%` | Usage against allocatable node memory |
| Each returned node condition | `generic_proc` | — | `1` for `True`, otherwise `0`; pressure conditions are not inverted |

#### Deployment agents

Agents are generated only when a returned `Available` or `Progressing` condition has status `True`; the first match determines the selected status.

| Name | Type | Value |
| --- | --- | --- |
| `Replicas` | `generic_data` | Desired replica count |
| `Updated replicas` | `generic_data` | Updated replica count; `0` if absent |
| `Ready replicas` | `generic_data` | Ready replica count; `0` if absent |
| `Available replicas` | `generic_data` | Available replica count; `0` if absent |
| `Unavailable replicas` | `generic_data` | Unavailable replica count; `0` if absent |
| `Available` | `async_proc` | Always `0` in this package; do not interpret as actual availability |
| `Progressing` | `async_proc` | `1` if the selected status is `Progressing`, otherwise `0` |

There are no deployment `Age` or `Ready` modules in this application.

#### Pod agents

| Name | Type | Unit | Value |
| --- | --- | --- | --- |
| `Pod status` | `generic_data` | — | `0` Failed, `1` Running, `2` Succeeded, `3` Pending, `4` Unknown/other |
| Last returned pod condition | `generic_proc` | — | For `PodScheduled`, `Ready`, `Initialized`, `ContainersReady`: `1` for `True`; for `Unschedulable`: `1` for `False`; otherwise `0`. Unrecognized conditions are not reliably interpreted |
| `Containers` | `generic_data` | — | Number of containers in collected pod metrics |
| `Container <name> CPU (cores)` | `generic_data` | `cores` | Container CPU usage, when calculated |
| `Container <name> CPU (%)` | `generic_data` | `%` | Usage against its node's allocatable CPU, when calculated |
| `Container <name> memory (bytes)` | `generic_data` | `bytes` | Container memory usage, when calculated |
| `Container <name> memory (%)` | `generic_data` | `%` | Usage against its node's allocatable memory, when calculated |

### API requests

This is the queried surface, not a validated role definition. Global queries are not separately switchable.

| Resource | GET path |
| --- | --- |
| Node details | `/api/v1/nodes/<NODE_NAME>` |
| Node metrics | `/apis/metrics.k8s.io/v1beta1/nodes` |
| Pods | `/api/v1/pods` |
| Pod metrics | `/apis/metrics.k8s.io/v1beta1/pods` |
| Deployments | `/apis/apps/v1/deployments` |
| Services | `/api/v1/services` |
| Namespaces | `/api/v1/namespaces` |
| Component statuses | `/api/v1/componentstatuses` |
| Replication controllers | `/api/v1/replicationcontrollers` |
| Registered API services | `/apis/apiregistration.k8s.io/v1/apiservices` |

| Health module name | GET path |
| --- | --- |
| `healthz` | `/healthz` |
| `healthzPing` | `/healthz/ping` |
| `healthzLog` | `/healthz/log` |
| `healthzEtcd` | `/healthz/etcd` |
| `healthzPoststarthook crd informer synced` | `/healthz/poststarthook/crd-informer-synced` |
| `healthzPoststarthook generic apiserver start informers` | `/healthz/poststarthook/generic-apiserver-start-informers` |
| `healthzPoststarthook start apiextensions controllers` | `/healthz/poststarthook/start-apiextensions-controllers` |
| `healthzPoststarthook start apiextensions informers` | `/healthz/poststarthook/start-apiextensions-informers` |
