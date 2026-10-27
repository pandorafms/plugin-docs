# Kubernetes Discovery

*Article last updated: 2026-10-26.*

<!-- DRAFT: Source-verified for package 1.3; distributed-package installation and live collection remain unvalidated. -->

## What it monitors

The Kubernetes Discovery plugin connects to the Kubernetes API server of a cluster and discovers its workloads and infrastructure: nodes, pods, deployments, namespaces, services, component statuses and the API health endpoints. It generates one Pandora FMS agent per discovered resource and fills it with availability, capacity and performance modules read from the API.

The plugin generates agents for:

- the cluster itself, through a global **Kubernetes** agent;
- every node, when **Scan Nodes** is enabled;
- every deployment with condition data, when **Scan Deployments** is enabled;
- every pod already scheduled to a node, when **Scan Pods** is enabled.

The global agent also carries the cluster-wide API status, health endpoints, service count, namespace count and component statuses.

The plugin runs as a Discovery task: the console creates the task, the Discovery server runs the plugin, and the generated agents and modules are created automatically. The task delivers the generated agent data through Tentacle.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Plugin version `1.3` (`pandorafms.kubernetes`) | Documented target | The version this page describes, as identified by the package definition. See [Plugin identity](#plugin-identity) |
| A Kubernetes cluster exposing the API server over HTTPS | `Required` | The plugin connects to `https://<host>:<port>` and reads the API resources. Prerequisite, not a compatibility statement |
| A Bearer token that can read the queried API resources | `Required` | The plugin authenticates with `Authorization: Bearer <token>` to list nodes, pods, deployments, services, namespaces and component statuses. Health and component endpoints may require elevated permissions. Prerequisite, not a compatibility statement |
| The Kubernetes Metrics API (`metrics.k8s.io`) for CPU and memory usage | `Required` for CPU and memory modules | Node and container CPU and memory modules are read from `/apis/metrics.k8s.io/v1beta1`. Without it, node and pod agents are still generated, but those modules are omitted |
| A specific Kubernetes version | `Not validated` | No published test record establishes compatibility with a concrete Kubernetes release |
| Host operating system running the plugin | `Not validated` | No published test record establishes operating-system compatibility |

### Requirements

1. **A Pandora FMS server with Discovery enabled** to run the task, and the console to define it.
2. **A Kubernetes API server reachable from the Discovery server**, addressed by host and port. The plugin always uses HTTPS; enter the host without a scheme.
3. **A Bearer token** for the API server. It is required to read the protected endpoints; grant it read access to the resources the task queries and no more. The **Scan API health checks** and **Scan component statuses** options may need elevated API permissions, as noted in the task tips.
4. **A target agent group and a monitoring interval** for the generated agents. Both come from the Discovery task and are inherited by every generated agent.
5. **Network reachability to the Tentacle destination**, because the task transfers the generated agent data through Tentacle.
6. The plugin is distributed as a Pandora FMS Discovery application (`.disco` package) that the Discovery server executes on the Pandora FMS server.

Direct API connections use HTTPS without certificate verification: the server identity is not authenticated, so self-signed certificates work. Restrict network access accordingly. Proxy mode uses the supplied proxy URL and omits the Bearer header. The token is entered in the task and written to its configuration; restrict access to both. For manual runs, keep the token in a protected configuration file, not in shell commands.

### Check target access

Before creating the task, verify the Metrics API and the node/pod metrics with an account authorized for the target cluster:

```bash
kubectl get --raw /apis/metrics.k8s.io/v1beta1/
kubectl top node
kubectl top pod --all-namespaces
```

If the cluster does not expose the Metrics API, node and pod agents are still generated, but their CPU and memory modules are omitted. These diagnostic commands do not grant the plugin token any permissions.

### Install the plugin

Obtain the `.disco` package from the [Kubernetes Marketplace entry](https://marketplace.pandorafms.com/entries/pandorafms.kubernetes) and load it in Discovery from **Management → Discovery → Extension manager**. Once loaded, **Kubernetes** appears under the **Applications** category of the Discovery wizard. This page covers package `1.3`.

## Configure the Discovery task

Create the task from **Management → Discovery → Applications → Kubernetes**. The wizard walks through the generic task definition and two plugin steps: **Kubernetes base** and **Kubernetes detailed**. Every field is documented in [Task parameters](#task-parameters).

### Step 1 — Task definition

The generic step asks for the task **name**, the **agent group** and **server** on which the task runs, and the **interval**. The group and the interval are passed to the plugin and inherited by every generated agent.

### Step 2 — Kubernetes base

Connection details and the Tentacle destination:

- **Kubernetes host** is the address or hostname of the API server.
- **Kubernetes port** is the API server port.
- **Kubernetes token** is the Bearer token used to authenticate against the API.
- **Use prefix** shows **Prefix**, the text prepended to generated agent identities. Clear **Prefix** when disabling this option: a populated prefix is still applied in this version.
- **Filter namespace** restricts discovery to a set of namespaces, and **Namespace** is the list of namespaces to monitor.
- **Use proxy** routes the API requests through a proxy; **Proxy url** is that proxy.
- **Tentacle IP** and **Tentacle port** set the Tentacle destination for the generated data. Leave the defaults unless your environment needs another Tentacle target.

![Kubernetes base step](../assets/images/discovery/kubernetes/kubernetes-base.png)

### Step 3 — Kubernetes detailed

What to scan:

- **Scan Deployments**, **Scan Nodes** and **Scan Pods** enable or disable each resource category.
- **Scan API health checks** generates the API health endpoint modules. Health endpoints may require elevated API permissions.
- **Scan component statuses** generates the component count and the component condition modules. Component statuses may require elevated API permissions.

![Kubernetes detailed step](../assets/images/discovery/kubernetes/kubernetes-detailed.png)

## Verify the first run

Run the task from **Management → Discovery → Task list** and check the result in this order.

1. **The task summary** shows the overall progress and a summary with the number of node agents, pod agents and deployment agents generated, and the total number of agents.
2. **The agents.** Expect the global **Kubernetes** agent plus one agent per discovered node, deployment and scheduled pod. Node and pod agents are generated even when the Metrics API is unavailable; deployment agents require returned condition data.
3. **The modules.** Every generated agent carries the modules of its resource; a reachable cluster with the Metrics API available populates the CPU and memory values. Do not treat the summary counters as proof of successful data ingestion.
4. **The execution information.** A successful run reports no errors; any per-request failure is recorded there.

![Task execution summary](../assets/images/discovery/kubernetes/task-summary.png)

If the task fails before generating anything, the host, the port, the network reachability and the token are the first things to check.

## Understand the results

### Agents and identity

The plugin creates one agent per discovered resource. Agent names are built from the original resource name plus the optional prefix.

| Agent | Name | Parent agent |
| --- | --- | --- |
| Global | `[Prefix]Kubernetes` | — |
| Node | `[Prefix]<node>` | The global agent |
| Deployment | `[Prefix]<deployment>` | `Kubernetes` (without the prefix) |
| Pod | `[Prefix]<namespace>/<pod>` | The node agent that runs the pod |

Node agents refer to the prefixed global agent; deployment agents refer to the unprefixed `Kubernetes` parent even when a prefix is set. Each pod agent refers to its prefixed node and uses the pod IP as its address. The global agent is described as `Kubernetes global agent`, node agents as `Kubernetes node`, deployment agents as `Kubernetes deployment` and pod agents as `Kubernetes pod`.

Node and pod agents do not depend on the Metrics API: when it is unavailable, they are still generated without CPU and memory modules. Only pods already scheduled to a node are discovered: a pod without an assigned node is skipped, as are resources the API returns without a name. Pod identities include the namespace, so equal pod names in different namespaces do not collide; deployment identities do not include the namespace, so equal deployment names in different namespaces can collide. Use separate prefixes for different clusters; namespace filtering does not add a namespace to the deployment identity.

Changing **Prefix** later changes the identity of every generated agent. The **Filter namespace** option applies only to deployments and pods, because nodes are cluster-scoped. Namespace matching is exact and case-sensitive, and the list is entered as a JSON array, for example `["default","kube-system"]`. When **Filter namespace** is enabled, list at least one namespace: an empty list matches no workload and no deployment or pod agent is generated.

### Modules by agent

Every agent receives the modules of its resource. The values are read from the API during every task run; the exact name, type and unit of each module are listed in [Generated modules](#generated-modules).

| Agent | Modules it carries |
| --- | --- |
| Global | API status, API health endpoints, service count, namespace count, component statuses, deployment count |
| Node | Pod usage against the node allocatable, node conditions and, when the Metrics API is available, CPU and memory usage |
| Deployment | Replica counts, readiness and availability of the deployment |
| Pod | Pod phase and conditions, container count and, when the Metrics API is available, per-container CPU and memory usage |

![Modules of a generated pod agent](../assets/images/discovery/kubernetes/pod-modules.png)

## Operate

### Manual execution

The plugin can also be run outside the Discovery wizard with a configuration file. This is useful for testing connectivity or for a one-off run. Write a configuration file with the `key=value` pairs listed in [Configuration file keys](#configuration-file-keys), then run the plugin entry point with the file as argument:

```bash
pandora_kubernetes --conf <PATH_TO_CONFIG>
```

For example, this direct-mode configuration enables every resource category and scan option. Replace every placeholder before use; the example has not been executed:

```ini
ip=<TARGET_HOST>
port=<API_PORT>
token=<API_TOKEN>
agents_group_name=<AGENT_GROUP>
interval=300
transfer_mode=tentacle
tentacle_ip=<TENTACLE_HOST>
tentacle_port=41121
prefix=<CLUSTER_PREFIX>
use_prefix=1
use_namespace=1
filter_namespace=["default","kube-system"]
use_proxy=0
deployments=1
nodes=1
pods=1
health_checks=1
component_checks=1
```

Execution returns a Discovery JSON summary and generates XML for each agent. An illustrative summary is `{"summary":{"Total agents":4,"Nodes agents":1,"Pods agents":1,"Deployments agents":1}}`; these counters describe generation, not confirmed delivery.

The operational CLI input is `--conf` (`-h`/`--help` displays help). When the plugin runs as a Discovery task, the server builds that file from the task fields. Manual examples have not been executed against a live target.

## Troubleshoot

| Symptom | Check |
| --- | --- |
| The execution reports a request error | Confirm **Kubernetes host** and **Kubernetes port**, that the API server is reachable from the Discovery server, and that the host does not include a scheme. |
| Requests fail with `401` or `403` | The token is missing, invalid or lacks read access to the queried resources. Health checks and component statuses may need elevated permissions. Check access to the exact paths in the API reference; no validated role definition is provided here. |
| No deployments or pods are generated but nodes are | Review **Scan Deployments** and **Scan Pods**, and **Filter namespace**: when it is enabled, names must match exactly and in the same case, and an empty list matches nothing. |
| Expected pods are missing | Only pods already scheduled to a node are discovered. A pod in `Pending` without an assigned node is not generated. |
| Node CPU and memory modules are missing | The Kubernetes Metrics API is not available in the cluster. The node agent is still generated. |
| Some global, health or component modules are missing | Those endpoints returned `401`, `403` or `404`, or the corresponding scan option is disabled. The plugin skips an optional endpoint that is not accessible instead of failing the whole run. |
| **API status** is `0` | The `/healthz` endpoint did not return `ok`. Check the API server health itself. If `/healthz` is inaccessible, the module is omitted. |
| A deployment has no agent | Check **Scan Deployments**, namespace filtering and returned deployment conditions. |
| Deployment **Available** looks healthy despite a failing condition | It reflects the first condition's type, not its Boolean status. Check replica counts and cluster conditions directly. |
| API requests time out | Requests use a fixed 5-second timeout and it is not configurable. Confirm the latency between the Discovery server and the API server. |
| Tentacle transfer fails | Confirm the Discovery server can reach **Tentacle IP** on **Tentacle port**. |
| The global agent uses proxy mode but is not authenticated | When **Use proxy** is enabled the plugin sends requests to **Proxy url** and does not add the Bearer token. |

## Reference

### Task parameters

The console presents these fields after the generic task definition. The macro column is the identifier used in the generated task configuration.

#### Kubernetes base

| Field | Macro | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- | --- |
| Kubernetes host | `_ip_` | string | Direct mode | Empty | API server address or hostname, without a scheme |
| Kubernetes port | `_port_` | number | Direct mode | Empty | Numeric API server port |
| Kubernetes token | `_token_` | textarea | Protected direct endpoints | Empty | Bearer token; the wizard permits an empty value |
| Use prefix | `_usePrefix_` | checkbox | No | off | Shows the prefix field; does not suppress a populated prefix |
| Prefix | `_prefix_` | string | No | Empty | Shown with **Use prefix**; clear it to stop applying a prefix |
| Filter namespace | `_filterNamespace_` | checkbox | No | off | Restricts deployment and pod agents to listed namespaces |
| Namespace | `_namespace_` | textarea | When filtering | `[]` | JSON array, for example `["default","kube-system"]`; exact, case-sensitive matching |
| Use proxy | `_useProxy_` | checkbox | No | off | Uses **Proxy url** instead of the direct API address; omits Bearer authentication |
| Proxy url | `_proxyUrl_` | string | Proxy mode | Empty | Base URL, including scheme; shown with **Use proxy** |
| Tentacle IP | `_tentacleIP_` | string | Yes | `127.0.0.1` | Transfer destination |
| Tentacle port | `_tentaclePort_` | number | Yes | `41121` | Numeric transfer destination port |

#### Kubernetes detailed

| Field | Macro | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- | --- |
| Scan Deployments | `_scanDeployments_` | checkbox | No | on | Generates deployment agents when condition data is present |
| Scan Nodes | `_scanNodes_` | checkbox | No | on | Generates node agents; CPU and memory modules require the Metrics API |
| Scan Pods | `_scanPods_` | checkbox | No | on | Generates pod agents for scheduled pods; container CPU and memory modules require the Metrics API |
| Scan API health checks | `_healthChecks_` | checkbox | No | on | Generates the API health endpoint modules. May require elevated API permissions |
| Scan component statuses | `_componentChecks_` | checkbox | No | on | Generates the component count and component condition modules. May require elevated API permissions |

### Configuration file keys

The Discovery task builds this file from its own fields; a manual run supplies it with `--conf`. It is a plain text file of `key=value` lines.

Required manual inputs are `ip`, `port` and, for protected endpoints, `token` in direct mode; `proxy_url` in proxy mode; and `transfer_mode=tentacle` with `tentacle_ip` for delivery. Other keys are optional and use the defaults below. Protect the file because it contains the token.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `ip` | Direct mode | Empty | API server host, without a scheme |
| `port` | Direct mode | Empty | API server port |
| `token` | Protected direct endpoints | Empty | Bearer token |
| `agents_group_name` | No | Empty manually; task group | Target agent group |
| `interval` | No | `300` | Agent interval in seconds; task interval in Discovery |
| `transfer_mode` | For delivery | Empty manually; `tentacle` in task | Use `tentacle` for the documented transfer path |
| `tentacle_ip` | For Tentacle | Empty manually; `127.0.0.1` in task | Transfer destination |
| `tentacle_port` | No | `41121` | Transfer port |
| `use_prefix` | No | `0` | Shows the task prefix field; does not suppress a populated `prefix` |
| `prefix` | No | Empty | Prefix applied to agent identities |
| `use_namespace` | No | `0` | `1` enables workload namespace filtering |
| `filter_namespace` | When filtering | `[]` | JSON array; exact namespace matches |
| `use_proxy` | No | `0` | `1` uses `proxy_url` without the Bearer header |
| `proxy_url` | Proxy mode | Empty | Base URL including scheme |
| `deployments` | No | `1` | `1` collects deployments and generates deployment agents |
| `nodes` | No | `1` | `1` collects nodes and generates node agents |
| `pods` | No | `1` | `1` collects pods and generates pod agents |
| `health_checks` | No | `1` | `1` generates the API health endpoint modules |
| `component_checks` | No | `1` | `1` generates the component status modules |
| `data_dir` | No | Empty | Accepted but does not select an output directory |

### Command line

| Command | Description |
| --- | --- |
| `pandora_kubernetes --conf <PATH_TO_CONFIG>` | Runs the plugin with a configuration file |

### Generated modules

#### Global agent

| Module name | Type | What it reports |
| --- | --- | --- |
| `API status` | generic_proc | `1` when `/healthz` returns `ok`, `0` otherwise; created only when `/healthz` responds |
| One module per health endpoint | generic_proc | `1` when the response is `ok`, `0` otherwise; only when **Scan API health checks** is enabled and the endpoint responds |
| `Services` | generic_data | Number of services; omitted if the request is not accessible |
| `Namespaces` | generic_data | Number of namespaces; omitted if the request is not accessible |
| `Components` | generic_data | Number of component statuses; only when **Scan component statuses** is enabled and the request is accessible |
| `<component>.<condition>` | generic_data | `1` when the component condition status is `TRUE`, `0` otherwise |
| `Deployments` | generic_data | Number of deployments; `0` when **Scan Deployments** is disabled |

Health module names and their exact paths are listed in [API requests](#api-requests). A module is created only for an endpoint that responds. Optional endpoint failures do not prevent the global agent from being transferred.

#### Node agents

| Module name | Type | Unit | What it reports |
| --- | --- | --- | --- |
| `Pods` | generic_data | — | Pods counted during collection on the node |
| `Pods (%)` | generic_data | % | Collected pod count against the node's allocatable pod capacity; omitted when the capacity is missing |
| `CPU (cores)` | generic_data | cores | CPU used by the node. Requires the Metrics API |
| `CPU (%)` | generic_data | % | CPU used against the allocatable CPU. Requires the Metrics API |
| `Memory (bytes)` | generic_data | bytes | Memory used by the node. Requires the Metrics API |
| `Memory (%)` | generic_data | % | Memory used against the allocatable memory. Requires the Metrics API |
| `NetworkUnavailable`, `MemoryPressure`, `DiskPressure`, `PIDPressure` | generic_proc | — | `1` when the corresponding condition is `False`, `0` otherwise |
| `Ready` | generic_proc | — | `1` when the condition is `True`, `0` otherwise |

Node agents are generated even when the Metrics API is unavailable; the CPU and memory modules are then omitted. `Pods` counts pods processed from the returned data, not an independently validated count of every pod on the node.

#### Deployment agents

| Module name | Type | Unit | What it reports |
| --- | --- | --- | --- |
| `Ready` | generic_proc | — | `1` when the ready replicas equal the desired replicas, `0` otherwise |
| `Age` | generic_data | `_timeticks_` | Creation timestamp in centiseconds since 1970, not elapsed age |
| `Replicas` | generic_data | — | Desired replicas |
| `Updated replicas` | generic_data | — | Replicas updated to the desired template |
| `Ready replicas` | generic_data | — | Ready replicas |
| `Available replicas` | generic_data | — | Available replicas |
| `Unavailable replicas` | generic_data | — | Replicas still required for the deployment to reach full availability |
| `Available` | generic_data | — | `1` if the first condition type is `Available` or `Progressing`, otherwise `0`; ignores the condition status. Warning threshold at `2`, critical at `0` |

Deployment agents are generated only when the deployment returns at least one condition.

#### Pod agents

| Module name | Type | Unit | What it reports |
| --- | --- | --- | --- |
| `Pod status` | generic_data | — | Pod phase: `0` Failed, `1` Running, `2` Succeeded, `3` Pending, `4` Unknown or other |
| `PodScheduled`, `Ready`, `Initialized`, `ContainersReady` | generic_proc | — | `1` for condition `True`, otherwise `0` |
| `Unschedulable` | generic_proc | — | `1` for condition `False`, otherwise `0` |
| `Containers` | generic_data | — | Number of containers in the pod |
| `Container <name> CPU (cores)` | generic_data | cores | CPU used by the container. Requires the Metrics API |
| `Container <name> CPU (%)` | generic_data | % | CPU used by the container against the allocatable CPU of its node. Requires the Metrics API |
| `Container <name> memory (bytes)` | generic_data | bytes | Memory used by the container. Requires the Metrics API |
| `Container <name> memory (%)` | generic_data | % | Memory used by the container against the allocatable memory of its node. Requires the Metrics API |

A per-container CPU or memory module is created only when the container exposes that metric; the pod agent is still generated when a metric is missing. The percentages use the node's allocatable resources, not container requests or limits.

### API requests

The token needs access to the requests below. The resource scan switches control collection and agent generation; the health and component switches control their own requests. This is the queried surface, not a validated least-privilege role definition.

| Resource | GET path |
| --- | --- |
| Nodes and node details | `/api/v1/nodes`, `/api/v1/nodes/<NODE_NAME>` |
| Pods | `/api/v1/pods` |
| Metrics | `/apis/metrics.k8s.io/v1beta1/nodes`, `/apis/metrics.k8s.io/v1beta1/pods` |
| Deployments | `/apis/apps/v1/deployments` |
| Services | `/api/v1/services` |
| Namespaces | `/api/v1/namespaces` |
| Component statuses | `/api/v1/componentstatuses` |

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

### Plugin identity

| Field | Value |
| --- | --- |
| App short name | `pandorafms.kubernetes` |
| Plugin version | `1.3` |
| Type | Discovery application (`.disco`) |
| Section | Discovery → Applications |
