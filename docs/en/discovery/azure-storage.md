# Azure Storage Discovery

*Article last updated: 2026-09-01.*

## What it monitors

The Azure Storage Discovery plugin discovers the storage accounts in a Microsoft Azure subscription and turns their Azure Monitor metrics into Pandora FMS agents and modules: capacity, operations, traffic, latency and availability, for the account itself and for its Blob, File, Queue and Table services.

By default it creates **one agent per Storage Account**, with a reachability module and one module per enabled metric. It can also consolidate every account onto a single agent. Per-file-share and per-container metrics are available as opt-in extras.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Plugin version `1.0` (`pandorafms.azure_storage`) | Documented target | The version this page describes. See [Plugin identity](#plugin-identity) |
| Microsoft Azure Resource Manager and Azure Monitor | `Required` | The plugin reads accounts and metrics through these APIs |
| A Microsoft Entra service principal with **Reader** and **Monitoring Reader** | `Required` | Prerequisite, not a compatibility statement. See [Prepare Azure access](#prepare-azure-access) |
| A Pandora FMS agent group with an ID greater than `0` | `Required` | The `All` group has ID `0` and cannot be used |
| Sovereign or custom Azure clouds | `Not validated` | The endpoints are configurable, but no test record establishes operation against a non-public cloud |
| Host operating system running the plugin | `Not validated` | No test record establishes operating-system compatibility |

### Prerequisites

1. **A Pandora FMS server with Discovery enabled** to execute the task, and the console to define it.
2. **A Microsoft Azure subscription** containing storage accounts.
3. **An Azure credential** stored in the Pandora FMS credential store, or its values supplied directly for a manual run.
4. **A valid agent group** for the task. The `All` group is not valid, because its ID is `0`.
5. **For advanced container metrics only**: the `ContainerLevelCapacityMetrics` rule already enabled in Azure. The plugin checks the state of this rule; it never enables it.

The plugin is distributed as a self-contained executable: the packaged Discovery app ships `bin/pandora_azure_storage`, so no additional runtime has to be installed, on the Pandora FMS server or for a manual run.

### Prepare Azure access

Create a Microsoft Entra service principal and assign it the **Reader** and **Monitoring Reader** roles over the subscription or the Resource Group to be discovered. These two roles are what the plugin needs: Reader to enumerate the storage accounts, Monitoring Reader to read their metrics. Do not grant a broader role.

Store its **Client ID**, **Application secret**, **Tenant or domain name** and **Subscription id** as an Azure credential in the Pandora FMS credential store, so the task references the credential instead of carrying the secret itself.

If per-container monitoring is required, enable the `ContainerLevelCapacityMetrics` rule for the relevant Storage Accounts before running the task.

### Install the plugin

Upload the `.disco` package from **Management → Discovery → Extension manager**.

## Configure the Discovery task

Create the task from **Management → Discovery → Cloud → Azure Storage**. The wizard's generic first step defines the task; the package adds three more. Every field is documented in [Task parameters](#task-parameters).

**Step 1 — Task definition.** Name, group, server and interval. The group must have an ID greater than `0`; `All` cannot be used. The group and interval are passed to the plugin and inherited by every generated agent.

**Step 2 — Azure base.** Which subscription to read and how much of it:

- **Azure credentials** selects the stored Azure credential.
- **Custom Resource Group** narrows discovery to a single Resource Group, and **Resource group** names it exactly. Regular expressions are not accepted here.

<!-- SCREENSHOT NEEDED: Azure base wizard step showing the credential selector, the Custom Resource Group toggle and the Resource group field, with no tenant or subscription identifiers visible. -->

**Step 3 — Advanced options.** Which accounts, how agents are named, and how Azure is reached:

- **Storage account names** filters by exact, case-insensitive account name, several separated by `;`. Empty discovers every account.
- **Create one agent per Storage Account**, **Target agent** and **Agent name prefix** decide the agent layout. See [Understand the results](#understand-the-results).
- **Enable entities file re-scan interval** and **Entities re-scan interval** control how long the discovered-account cache is reused before being rebuilt.
- **Request timeout**, **Azure management endpoint** and **Microsoft login endpoint** cover slow environments and sovereign or custom clouds.
- **Debug** reveals the local mock options, which exist for testing only. See [Troubleshoot](#troubleshoot).

<!-- SCREENSHOT NEEDED: Advanced options wizard step showing the account-name filter, the agent layout toggles and the endpoint fields, with the Debug toggle disabled. -->

**Step 4 — Metrics and module filters.** Which metric families are collected and which modules survive:

- One toggle per service: **Storage account**, **Blob service**, **File service**, **Queue service** and **Table service** metrics. **File share metrics** appears only when File service metrics is enabled.
- **Advanced container metrics** and **Container regexp** add per-container modules.
- **Modules allow regexp** and **Modules deny regexp** take one regular expression per line and filter the final module names.

<!-- SCREENSHOT NEEDED: Metrics and module filters wizard step showing the per-service toggles and the allow and deny regular-expression fields. -->

## Verify the first run

Force the task from **Management → Discovery → Task list** and check the result in this order.

1. **The task summary** reports the generated agents and modules. Expect one agent per discovered Storage Account, or a single **Target agent** when per-account creation is disabled.

    <!-- SCREENSHOT NEEDED: Discovery task execution summary for an Azure Storage task showing the generated agent and module totals. -->

2. **The agents.** Named `<Agent name prefix><storage account name>` by default, so `Azure Storage myaccount`. Each one reports `Azure` as its operating system and inherits the task's group and interval.

3. **`Azure Storage Connection`** is `1` on every discovered account. A `0` means the account was in the cache but is no longer discoverable — see [Troubleshoot](#troubleshoot).

4. **The metric modules** for each enabled service. The exact set depends on the account: quota and percentage modules exist only for Standard accounts, and per-file-share or per-container modules only when those options are enabled.

If no agent appears at all, the credential or its roles are the first thing to check.

## Understand the results

### Agent layout

**With Create one agent per Storage Account enabled**, which is the default, the plugin creates one agent per account, named `<Agent name prefix><storage account name>`. When the prefix does not end in a space, hyphen, period or underscore, a space is inserted, so a prefix of `Azure Storage` behaves like `Azure Storage `.

**With it disabled**, every module goes to the single **Target agent** and the account name is prepended to each module name instead. This matters for filtering: the allow and deny regular expressions are evaluated against the *final* module name, which in consolidated mode includes that account prefix.

Generated agents report `Azure` as their operating system, inherit the task's group and interval, and are created in Pandora FMS agent mode `2` when **Agent autodisable mode** is enabled, or mode `1` when it is disabled.

### What gets created

`Azure Storage Connection` is always created, as `generic_proc`, with value `1` for a discovered account. When a cached account stops being discoverable, its agent is kept and this module reports `0` until the entity is dropped during a cache rebuild.

Everything else is `generic_data`, grouped by the option that enables it:

| Enabled by | What you get |
| --- | --- |
| Storage account metrics | Account capacity, quota and occupancy, plus transactions, ingress, egress, latency and availability. Adds `Data Lake Storage Gen2 Enabled` when the account has a hierarchical namespace |
| Blob service metrics | Blob capacity, object and container counts, index capacity, and the same traffic, latency and availability set |
| File service metrics | File capacity, object, share and snapshot counts, quota, and the same traffic, latency and availability set |
| File share metrics | Used capacity, quota and occupancy per file share |
| Queue service metrics | Queue capacity, queue and message counts, and the same traffic, latency and availability set |
| Table service metrics | Table capacity, table and entity counts, and the same traffic, latency and availability set |
| Advanced container metrics | `Blob Container Metrics Enabled`, plus used capacity and blob count per container |

Capacity quota and occupancy modules are created for Standard accounts only. The exhaustive module names and units are in [Generated modules](#generated-modules).

## Troubleshoot

- **The task fails on the group** — the agent group must have an ID greater than `0`. `All` is group `0` and cannot be used.
- **No storage account is discovered** — check the service principal in this order: the credential values, then that **Reader** and **Monitoring Reader** are assigned over the right scope, then whether **Custom Resource Group** is narrowing the search, then whether **Storage account names** holds a name that does not match exactly. That field matches complete names, case-insensitively; it is not a regular expression.
- **An agent survives with `Azure Storage Connection` at `0`** — the account is in the entity cache but is no longer discoverable, because it was deleted, renamed, or moved out of the configured scope. The agent is kept until the cache is rebuilt, which happens after **Entities re-scan interval**.
- **`Blob Container Metrics Enabled` reports `0`** — the `ContainerLevelCapacityMetrics` rule is not enabled in Azure for that Storage Account. The plugin reports the state; enable the rule in Azure.
- **Per-container modules are missing while the rule is enabled** — **Container regexp** filters container names. It applies only to containers retrieved through **Advanced container metrics**; it never affects general Blob metrics or `Blob Container Count`.
- **Expected modules are missing** — the allow and deny regular expressions are evaluated against the final module name. In consolidated mode that name carries the storage account prefix, so an expression written for per-account mode will not match.
- **Requests time out** — raise **Request timeout**. Each request is retried up to three times; that retry count is fixed in the plugin and is not configurable.
- **A sovereign or custom cloud is unreachable** — set **Azure management endpoint** and **Microsoft login endpoint**. Empty values use `https://management.azure.com` and `https://login.microsoftonline.com`.
- **Debug, Mock Azure API URL and Verify mock TLS certificate** exist to point the plugin at a local mock during testing. Leave **Debug** off in real environments, and never disable **Verify mock TLS certificate** against anything but a trusted local mock.

## Reference

### Task parameters

The console presents the task fields in three steps after the generic task definition. The macro column is the identifier used in the generated task configuration.

#### Azure base

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Azure credentials | `_credentials_` | select | — | Azure credential from the Pandora FMS credential store |
| Custom Resource Group | `_customresourcegroup_` | checkbox | off | Limits discovery to one Resource Group |
| Resource group | `_resourcegroup_` | string | — | Exact Resource Group name. Shown only when the previous option is enabled; not a regular expression |

#### Advanced options

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Storage account names | `_storageaccountregexp_` | string | — | Complete account names separated by `;`. Matching is exact and case-insensitive. Empty discovers every account |
| Create one agent per Storage Account | `_agentperstorageaccount_` | checkbox | on | Disabled sends every module to **Target agent** |
| Target agent | `_targetagent_` | string | `Azure Storage` | Agent used in consolidated mode |
| Agent name prefix | `_agentprefix_` | string | `Azure Storage ` | Prefix for per-account agents. A separator is inserted when the prefix does not end in a space, hyphen, period or underscore |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Enabled creates agents in mode `2`; disabled uses mode `1` |
| Enable entities file re-scan interval | `_enableentitiesinterval_` | checkbox | on | Reuses the discovered-account cache until the interval expires |
| Entities re-scan interval | `_entitiesinterval_` | select | `86400` | Seconds before the cache is rebuilt. Shown only when the previous option is enabled |
| Request timeout | `_timeout_` | number | `30` | Seconds per Azure request |
| Azure management endpoint | `_managementendpoint_` | string | — | Empty uses `https://management.azure.com` |
| Microsoft login endpoint | `_loginendpoint_` | string | — | Empty uses `https://login.microsoftonline.com` |
| Debug | `_debug_` | checkbox | off | Reveals the local mock options below, which exist only for testing |
| Mock Azure API URL | `_mockapiurl_` | string | — | Local mock base URL. Shown only when **Debug** is enabled; leave empty in real environments |
| Verify mock TLS certificate | `_verifyssl_` | checkbox | on | Shown only when **Debug** is enabled. Disable only for a trusted local test mock |

#### Metrics and module filters

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Storage account metrics | `_accountmetrics_` | checkbox | on | Account capacity, traffic, latency and availability |
| Blob service metrics | `_blobmetrics_` | checkbox | on | Blob capacity, counts, traffic and availability |
| File service metrics | `_filemetrics_` | checkbox | on | File capacity, counts, quota, traffic and availability |
| File share metrics | `_filesharemetrics_` | checkbox | on | Used capacity, quota and occupancy per share. Shown only when **File service metrics** is enabled |
| Queue service metrics | `_queuemetrics_` | checkbox | on | Queue capacity, counts, traffic and availability |
| Table service metrics | `_tablemetrics_` | checkbox | on | Table capacity, counts, traffic and availability |
| Advanced container metrics | `_containermetrics_` | checkbox | off | Requires the `ContainerLevelCapacityMetrics` rule in Azure. Creates no additional agents |
| Container regexp | `_containerregexp_` | string | — | Applied only to container names retrieved through the previous option |
| Modules allow regexp | `_moduleallowlist_` | textarea | — | One expression per line. Only modules matching at least one are kept |
| Modules deny regexp | `_moduledenylist_` | textarea | — | One expression per line. Matching modules are excluded |

### Configuration file keys

The Discovery task builds this file from its own fields; a manual run supplies it with `--conf`. The allow and deny lists are passed as file paths, one expression per line.

| Key | Description | Default |
| --- | --- | --- |
| `credentials` | Base64-encoded Azure credential generated by Pandora FMS | Empty |
| `tenant_id`, `client_id`, `client_secret`, `subscription_id` | Manual credential values, used when `credentials` is not provided | Empty |
| `group_id` | Pandora FMS group ID assigned to generated agents. Must be greater than `0` | Required |
| `custom_resource_group_enabled` | Enables discovery within one exact Resource Group | `0` |
| `resource_group` | Exact Resource Group name used when the previous option is enabled | Empty |
| `storage_account_names` | Exact Storage Account names separated by `;`. Empty discovers every account | Empty |
| `create_agent_per_storage_account` | Creates one agent per Storage Account when enabled | `1` |
| `target_agent` | Agent used in consolidated mode | `Azure Storage` |
| `agent_prefix` | Prefix for agents created per Storage Account | `Azure Storage ` |
| `agent_autodisable` | Uses Pandora FMS agent mode `2` when enabled and mode `1` otherwise | `0` |
| `interval` | Monitoring interval inherited from the Discovery task | `300` for manual runs |
| `standard_account_quota_gib` | Quota assumed for Standard accounts, used to derive the occupancy percentage | `5242880` |
| `account_metrics_enabled` | Enables Storage Account metrics | `1` |
| `blob_metrics_enabled` | Enables Blob service metrics | `1` |
| `file_metrics_enabled` | Enables File service metrics | `1` |
| `file_share_metrics_enabled` | Enables per-file-share metrics | `1` |
| `queue_metrics_enabled` | Enables Queue service metrics | `1` |
| `table_metrics_enabled` | Enables Table service metrics | `1` |
| `container_metrics_enabled` | Enables advanced per-container metrics | `0` |
| `container_regexp` | Optional regular expression applied to container names | Empty |
| `module_allow_list_file` | File containing one module allow regular expression per line | Empty |
| `module_deny_list_file` | File containing one module deny regular expression per line | Empty |
| `entities_list` | Path to the Storage Account entity cache | Empty in manual runs |
| `enable_entities_interval` | Retains cached entities until the configured interval expires | `1` |
| `entities_interval` | Entity cache rebuild interval in seconds | `86400` |
| `timeout` | Azure request timeout in seconds | `30` |
| `management_endpoint` | Azure management endpoint for sovereign or custom clouds | `https://management.azure.com` |
| `login_endpoint` | Microsoft login endpoint for sovereign or custom clouds | `https://login.microsoftonline.com` |
| `debug` | Enables the local mock options below. Testing only | `0` |
| `mock_api_url` | Local mock base URL. Testing only | Empty |
| `verify_ssl` | Verifies the mock TLS certificate. Disable only for a trusted local mock | `1` |

Request retries are fixed at `3` internally and are not configurable.

### Command-line execution

The plugin reads a single configuration file. A manual run reproduces what the Discovery server does per task execution.

```bash
./pandora_azure_storage --conf <PATH_TO_CONFIG>
```

| Option | Description |
| --- | --- |
| `--conf`, `-c` | Required path to the configuration file |
| `--pretty` | Pretty-prints the JSON output |
| `--version` | Prints the plugin version |
| `--help`, `-h` | Displays command help |

A minimal configuration file for a manual run:

```ini
[CONF]
tenant_id=<TENANT_ID>
client_id=<CLIENT_ID>
client_secret=<CLIENT_SECRET>
subscription_id=<SUBSCRIPTION_ID>
group_id=<GROUP_ID>
```

That file holds a credential in plain text. Restrict it to the account that runs the plugin, keep it out of shared directories and version control, and prefer the Pandora FMS credential store for task runs, where the task references the credential instead of carrying it.

### Generated modules

Every module below is `generic_data` unless stated otherwise, and is created only when the option that owns it is enabled.

**Always created**

- `Azure Storage Connection`: `generic_proc`, `1` for a discovered account.

**Storage account metrics**

- `Account Used Capacity`: GiB.
- `Account Capacity Quota`: GiB; Standard accounts only.
- `Account Used Capacity Percentage`: percent; Standard accounts only.
- `Account Transactions_Current`: requests.
- `Account Ingress_Current`: bytes.
- `Account Egress_Current`: bytes.
- `Account SuccessServerLatency_Current`: ms.
- `Account SuccessE2ELatency_Current`: ms.
- `Account Availability_Current`: percent.
- `Data Lake Storage Gen2 Enabled`: `generic_proc`; created when the account has a hierarchical namespace.

**Blob service metrics**

- `Blob Used Capacity`: GiB.
- `Blob Object Count`.
- `Blob Container Count`.
- `Blob Index Capacity`: GiB.
- `Blob Transactions_Current`: requests.
- `Blob Ingress_Current`: bytes.
- `Blob Egress_Current`: bytes.
- `Blob SuccessServerLatency_Current`: ms.
- `Blob SuccessE2ELatency_Current`: ms.
- `Blob Availability_Current`: percent.

**File service metrics**

- `File Used Capacity`: GiB.
- `File Object Count`.
- `File Share Count`.
- `File Snapshot Count`.
- `File Snapshot Size`: GiB.
- `File Capacity Quota`: GiB.
- `File Transactions_Current`: requests.
- `File Ingress_Current`: bytes.
- `File Egress_Current`: bytes.
- `File SuccessServerLatency_Current`: ms.
- `File SuccessE2ELatency_Current`: ms.
- `File Availability_Current`: percent.

**File share metrics**

- `File Share <name> Used Capacity`: GiB.
- `File Share <name> Capacity Quota`: GiB.
- `File Share <name> Used Capacity Percentage`: percent.

**Queue service metrics**

- `Queue Used Capacity`: GiB.
- `Queue Count`.
- `Queue Message Count`.
- `Queue Transactions_Current`: requests.
- `Queue Ingress_Current`: bytes.
- `Queue Egress_Current`: bytes.
- `Queue SuccessServerLatency_Current`: ms.
- `Queue SuccessE2ELatency_Current`: ms.
- `Queue Availability_Current`: percent.

**Table service metrics**

- `Table Used Capacity`: GiB.
- `Table Count`.
- `Table Entity Count`.
- `Table Transactions_Current`: requests.
- `Table Ingress_Current`: bytes.
- `Table Egress_Current`: bytes.
- `Table SuccessServerLatency_Current`: ms.
- `Table SuccessE2ELatency_Current`: ms.
- `Table Availability_Current`: percent.

**Advanced container metrics**

- `Blob Container Metrics Enabled`: `generic_proc`, `1` when the Azure rule is enabled and `0` when it is not.
- `Container <name> Used Capacity`: GiB.
- `Container <name> Blob Count`.
- `Container <name> Blob Capacity Percentage`: percent; created when **Blob service metrics** is also enabled and Azure returns `BlobCapacity`.

### Plugin identity

| Field | Value |
|-------|-------|
| App short name | `pandorafms.azure_storage` |
| Plugin version | `1.0` |
| Type | Discovery application (`.disco`) |
| Section | Discovery → Cloud |
