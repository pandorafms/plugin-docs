# Amazon EC2 Discovery

*Article last updated: 2026-10-26.*

## What it monitors

The Amazon EC2 Discovery addon monitors Amazon Web Services EC2 instances and the regions that contain them. It queries the AWS APIs and turns the result into Pandora FMS agents and modules: instance state, CPU, disk, IOPS and network performance, volume storage, Elastic IP addresses and, optionally, cost per region.

A Discovery task generates three kinds of agents:

- **A global statistics agent** (optional) with the number of instances and the total cost.
- **One agent per monitored region**, with summary modules aggregated over the instances of that region.
- **One agent per monitored instance**, with its state and performance modules. The instance agent is a child of its region agent.

A region can be selected as a whole, in which case every instance it contains is monitored, including instances created later. Individual instances can also be selected without selecting their region.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.aws.ec2`, version `1.5` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Network access from the Discovery server to the AWS APIs | `Required` | The addon calls the AWS EC2, CloudWatch and Cost Explorer APIs |
| AWS access key with the permissions listed in [AWS permissions](#aws-permissions) | `Required` | Prerequisite, not a compatibility statement |
| Operating system of the Discovery server | `Not validated` | No operating system has been recorded for this version |
| Specific Pandora FMS versions | `Not validated` | No version matrix has been recorded for this addon |

### Prerequisites

1. **Connectivity** from the Discovery server to the AWS APIs, directly or through an HTTPS proxy.
2. **An AWS access key** (access key ID and secret access key) with the permissions described below, registered in the Pandora FMS credential store as an AWS credential.
3. **Pandora FMS**: a Discovery server to run the task and the console to define it.

The addon ships its own executables, `bin/pandora_aws_ec2` and `bin/aws_ec2`, so nothing else has to be installed on the Discovery server to run a task.

### AWS permissions

The addon performs read-only requests. Which ones it issues depends on the options you enable:

| AWS action | Used for |
|------------|----------|
| `ec2:DescribeInstances` | Listing regions and instances (always) |
| `cloudwatch:GetMetricStatistics` | CPU, disk, IOPS and network metrics (when **Scan and general monitoring** is enabled) |
| `ec2:DescribeVolumes` | Storage modules (when **Storage** is enabled) |
| `ec2:DescribeAddresses` | Elastic IP modules (when **Elastic IP Adresses** is enabled) |
| `ce:GetCostAndUsage` | Cost modules (when **Total cost** is enabled) |

An IAM policy that grants all of them:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses",
        "cloudwatch:GetMetricStatistics",
        "ce:GetCostAndUsage"
      ],
      "Resource": "*"
    }
  ]
}
```

Attach the policy to a dedicated IAM user created for Pandora FMS and generate an access key for it. Omit the actions of the options you will not enable.

The credential stored in Pandora FMS must provide the keys `access_key_id` and `secret_access_key`; the plugin fails with `Error while parsing credentials` when either is missing.

### Install the addon

Download the `.disco` package from the Pandora FMS Marketplace entry, which is limited to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.aws.ec2](https://marketplace.pandorafms.com/entries/pandorafms.aws.ec2)

Load it into Pandora FMS. Once loaded, **Amazon EC2** is available in the **Cloud** section when creating Discovery tasks.

## Configure the Discovery task

Create the task from the Discovery cloud applications and choose **Amazon EC2**. The console presents the fields in four steps; every field is documented in [Task parameters](#task-parameters).

1. **EC2 Basic** — credentials, execution and agent options:

    - **AWS Credentials**: the AWS credential registered in the credential store.
    - **Max threads**: number of groups the monitored regions and instances are divided into.
    - **Use proxy**, **Proxy url** and **Verify proxy SSL**: route the AWS requests through an HTTPS proxy.
    - **Tentacle IP**, **Tentacle port** and **Tentacle extra options**: where and how the generated agent data is sent. They rarely need changing.
    - **Add global stats agent** and **Stats agent name**: create the global agent and optionally name it.
    - **Agent autodisable mode**: disables the agent when all its modules become unknown until data returns.

    <!-- SCREENSHOT NEEDED: EC2 Basic wizard step showing credentials, Max threads, proxy, Tentacle and stats agent fields, with no real credentials or addresses. -->

2. **EC2 Instances** — a tree of regions and instances read from your AWS account with the selected credential. Check a region to monitor it and all of its instances, or check individual instances. Instances are grouped by instance type under each region.

    <!-- SCREENSHOT NEEDED: EC2 Instances wizard step showing the region and instance tree with a region and an instance selected, using lab identifiers only. -->

3. **Instances monitoring** — the metrics collected:

    - **Scan and general monitoring**: enables the CPU, IOPs, disk and network options below.
    - **Cpu performance summary**, **IOPs performance summary**, **Disk performance summary**, **Network performance summary**: shown only when **Scan and general monitoring** is enabled.
    - **Storage** and **Elastic IP Adresses**: independent of **Scan and general monitoring**.

    <!-- SCREENSHOT NEEDED: Instances monitoring wizard step showing the monitoring checkboxes. -->

4. **EC2 Costs** — cost monitoring:

    - **Total cost**: enables cost modules.
    - **Cost by region**: regions to query. Shown when **Total cost** is enabled.
    - **Cost interval**: period of time the cost covers. Shown when **Total cost** is enabled.

    <!-- SCREENSHOT NEEDED: EC2 Costs wizard step showing Total cost, Cost by region and Cost interval. -->

The task's group and interval come from the generic task-definition step and are applied to the agents the task creates.

## Verify the first run

Force the task from the Discovery task list and check the result in this order.

1. **The task summary.** A task that completes successfully reports:

    - **Total agents**: all agents generated, including the global agent when enabled.
    - **Zones agents**: regions monitored.
    - **Instances agents**: instances monitored.

    A task that does not complete successfully records the errors in its execution information instead.

    <!-- SCREENSHOT NEEDED: Discovery task execution summary for an Amazon EC2 task showing Total agents, Zones agents and Instances agents. -->

2. **The agents.** One per selected region, one per instance and, when enabled, the global agent. Instance agents are children of their region agent.

3. **The modules.** Every instance agent has `State` and `Instance State (bool)`. Performance modules appear only on running instances; see [Understand the results](#understand-the-results).

## Understand the results

### Agents generated

| Agent | Alias | Parent | Notes |
|-------|-------|--------|-------|
| Global agent | The **Stats agent name**, or `Aws` when empty | None | Created only when **Add global stats agent** is enabled |
| Region agent | The region name, for example `eu-west-1` | The global agent only when a **Stats agent name** was given | One per selected region |
| Instance agent | The instance ID | Its region agent | One per instance, created once even when both the instance and its region are selected. The agent version is the instance type and the address is the public IP address, when it has one |

Agent identity does not depend on the task: region agents are identified by the access key and region, and instance agents by the access key and instance ID. Moving a region or instance between tasks that use the same access key keeps reporting to the same agent and preserves its history.

All agents report the operating system name `Aws`, and `ec2` as the operating system version for regions and instances.

### Modules per agent

**Global agent**

| Module | Type | Description |
|--------|------|-------------|
| `AWS EC2 Instances count` | `generic_data` | Instances found in the selected regions and instances |
| `AWS EC2 Total cost` | `generic_data` | Cost of the selected cost regions over the cost interval. Created only when **Total cost** is enabled |

**Region agent**

| Module | Condition | Description |
|--------|-----------|-------------|
| `summary.aws.ec2.instances` | Region selected as a whole | Instances in the region |
| `cost` | **Total cost** enabled, region in **Cost by region**, and at least one instance in the region | Cost of the region over the cost interval |
| `summary.aws.ec2.CPUUtilization` | **Scan and general monitoring** and **Cpu performance summary** | CPU of the running instances divided by the number of instances in the region |
| `summary.aws.ec2.DiskReadBytes`, `summary.aws.ec2.diskWriteBytes` | **Scan and general monitoring** and **Disk performance summary** | Sum over the running instances, in `Bytes` |
| `summary.aws.ec2.DiskReadOps`, `summary.aws.ec2.DiskWriteOps` | **Scan and general monitoring** and **IOPs performance summary** | Sum over the running instances |
| `summary.aws.ec2.NetworkPacketsIn`, `summary.aws.ec2.NetworkPacketsOut` | **Scan and general monitoring** and **Network performance summary** | Sum over the running instances, in `packets` |
| `summary.aws.ec2.addresses.count` | **Elastic IP Adresses** | Elastic IP addresses in the region |
| `summary.aws.ec2.storage.count`, `summary.aws.ec2.storage.size` | **Storage** | Volumes in the region and their total size in `GB` |

**Instance agent**

| Module | Type | Condition | Description |
|--------|------|-----------|-------------|
| `State` | `generic_data_string` | Always | Instance state as reported by AWS |
| `Instance State (bool)` | `generic_proc` | Always | `1` when the state is `running`, `0` otherwise |
| `CPUUtilization` | `generic_data` | Running, **Cpu performance summary** | CPU usage |
| `DiskReadBytes`, `DiskWriteBytes` | `generic_data` | Running, **Disk performance summary** | Disk bytes read and written, in `Bytes` |
| `DiskReadOps`, `DiskWriteOps` | `generic_data` | Running, **IOPs performance summary** | Disk read and write operations |
| `NetworkPacketsIn`, `NetworkPacketsOut` | `generic_data` | Running, **Network performance summary** | Network packets received and sent, in `packets` |

### How the values are obtained

- Performance values are the latest five-minute average that AWS CloudWatch returns for the last 150 minutes. When CloudWatch returns no data point in that window, the module value is `0`.
- Performance modules are created only for instances in the `running` state.
- The cost modules use the **Cost interval** as their period and are refreshed at that interval, not at the task interval.

## Operate

### Manual execution

The addon can run outside a Discovery task. The executable takes a single parameter, the path to a configuration file described in [Configuration file](#configuration-file):

```bash
./pandora_aws_ec2 --conf <PATH_TO_CONFIG>
```

It prints a JSON summary and sends one data file per agent using the configured transfer mode:

```json
{"summary": {"Total agents": 23, "Zones agents": 5, "Instances agents": 17}}
```

When errors occur, the JSON also contains an `info` key with the messages and the exit code is `1`.

In `local` transfer mode the data files are moved to `data_dir`. In `tentacle` mode the `tentacle_client` executable must be available in the `PATH` of the user running the addon.

A configuration file contains the AWS access key encoded in `creds_b64`. Protect the file with restrictive permissions.

## Troubleshoot

The addon has no verbose or debug flag. Its diagnostic channel is the `info` field of the JSON execution result, which is shown in the task's execution information.

- **`Error while parsing credentials`**: the credential does not provide `access_key_id` and `secret_access_key`, or `creds_b64` is not valid base64-encoded JSON.
- **The instance tree is empty or lacks a region**: regions whose `DescribeInstances` request fails are omitted from the tree without an error. Check the `ec2:DescribeInstances` permission of the key and the status of the region in AWS.
- **Fewer agents than expected**: only the regions and instances you checked are monitored. A selected region with no instances still produces its region agent.
- **`Error getting cost for <region>`**: the cost query for that region failed. Check that the access key has `ce:GetCostAndUsage`; the message includes the error returned by AWS.
- **Performance modules are `0`**: CloudWatch returned no data point in the last 150 minutes for that instance and metric.
- **No performance modules on an instance**: the instance is not `running`, or **Scan and general monitoring** is disabled.
- **`Error getting volumes for <region>` or `Error getting addresses for <region>`**: the key lacks `ec2:DescribeVolumes` or `ec2:DescribeAddresses`.
- **Errors reaching AWS through a proxy**: check **Proxy url**; only HTTPS requests are routed through it.

## Reference

### Task parameters

#### EC2 Basic

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| AWS Credentials | `_credentials_` | credential select (AWS) | — | Mandatory. Credential registered in the credential store |
| Max threads | `_threads_` | number | `1` | Optional. Regions and instances are distributed in groups, never more groups than targets |
| Use proxy | `_useProxy_` | checkbox | off | Route AWS requests through a proxy |
| Proxy url | `_proxyUrl_` | string | — | Optional. Shown when **Use proxy** is on. Applied to HTTPS requests |
| Verify proxy SSL | `_sslCheck_` | checkbox | off | Shown when **Use proxy** is on. When off, the addon does not validate TLS certificates in its AWS connections |
| Tentacle IP | `_tentacleIP_` | string | `127.0.0.1` | Server that receives the agent data |
| Tentacle port | `_tentaclePort_` | number | `41121` | Tentacle port |
| Tentacle extra options | `_tentacleExtraOpt_` | string | — | Optional. Extra Tentacle client options |
| Add global stats agent | `_statsAgent_` | checkbox | on | Create the global agent |
| Stats agent name | `_statsAgentName_` | string | `Aws` | Optional. Shown when **Add global stats agent** is on |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Disables the agent when all its modules become unknown until data returns |

Because **Verify proxy SSL** is only shown with **Use proxy**, a task that does not use a proxy always runs with TLS certificate validation disabled. Run such tasks only from a network you trust.

#### EC2 Instances

| Field | Macro | Type | Notes |
|-------|-------|------|-------|
| EC2 zones and instances | `_ec2Zones_`, `_ec2Instance_` | tree | Regions populate the region list and instances the instance list. Optional |

#### Instances monitoring

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Scan and general monitoring | `_ec2InstanceSummary_` | checkbox | off | Enables performance modules |
| Cpu performance summary | `_ec2CpuPerfSummary_` | checkbox | off | Shown with **Scan and general monitoring** |
| IOPs performance summary | `_ec2IopsPerfSummary_` | checkbox | off | Shown with **Scan and general monitoring** |
| Disk performance summary | `_ec2DiskPerfSummary_` | checkbox | off | Shown with **Scan and general monitoring** |
| Network performance summary | `_ec2NetworkPerfSummary_` | checkbox | off | Shown with **Scan and general monitoring** |
| Storage | `_ec2StorageSummary_` | checkbox | off | Volume modules |
| Elastic IP Adresses | `_ec2ElasticAddressesSummary_` | checkbox | off | Elastic IP modules |

#### EC2 Costs

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Total cost | `_globalTotalCost_` | checkbox | off | Enables cost modules |
| Cost by region | `_globalCostRegion_` | multiselect | none | Regions: `us-east-1`, `us-east-2`, `us-west-1`, `us-west-2`, `ca-central-1`, `eu-central-1`, `eu-west-1`, `eu-west-2`, `eu-west-3`, `ap-northeast-1`, `ap-northeast-2`, `ap-southeast-1`, `ap-southeast-2`, `ap-south-1`, `sa-east-1` |
| Cost interval | `_globalCostInterval_` | select | `604800` (seconds) | Period the cost covers |

### Configuration file

Used by manual execution. One `key = value` per line. List values are JSON arrays. Numeric options accept `1` to enable and `0` to disable; a value that is not a number is read as `0`.

| Key | Default | Description |
|-----|---------|-------------|
| `agents_group_name` | `aws` | Group of the generated agents |
| `interval` | `300` | Agent interval, in seconds |
| `interval_cost` | `300` | Period covered by the cost modules, in seconds. Use an integer number of seconds |
| `threads` | `1` | Number of groups the targets are distributed in |
| `transfer_mode` | `local` | `local` writes the data files to `data_dir`; any other value sends them with Tentacle |
| `tentacle_client` | `tentacle_client` | Tentacle client executable |
| `tentacle_ip` | `127.0.0.1` | Tentacle server address |
| `tentacle_port` | `41121` | Tentacle server port |
| `tentacle_opts` | empty | Extra Tentacle client options |
| `data_dir` | `/var/spool/pandora/data_in/` | Destination of the data files in `local` mode |
| `temporal` | `/tmp` | Directory where the data files are written before sending |
| `storage` | `1` | Storage modules |
| `elastic_ip_address` | `1` | Elastic IP modules |
| `advance_monitoring` | `1` | Performance modules; required for the four options below |
| `cpu_summary` | `1` | CPU modules |
| `iops_summary` | `1` | IOPS modules |
| `disk_summary` | `1` | Disk modules |
| `network_summary` | `1` | Network modules |
| `total_cost` | `1` | Cost modules |
| `cost_regions` | `[]` | Regions to query for costs |
| `aws_regions` | `[]` | Regions to monitor |
| `aws_instances` | `[]` | Instance IDs to monitor |
| `stats_agent` | `1` | Global agent |
| `stats_agent_name` | empty | Name of the global agent; `Aws` alias when empty |
| `agent_autodisable` | `0` | Autodisable mode |
| `use_proxy` | `0` | Use a proxy |
| `proxy_url` | empty | Proxy URL |
| `ssl_check` | `0` | `1` validates TLS certificates; `0` does not |
| `creds_b64` | empty | Mandatory. Base64 of the JSON `{"access_key_id": "<ACCESS_KEY_ID>", "secret_access_key": "<SECRET_ACCESS_KEY>"}` |

Example:

```ini
agents_group_name  = Aws
interval           = 300
interval_cost      = 604800
threads            = 4
transfer_mode      = tentacle
tentacle_ip        = <TENTACLE_SERVER_IP>
tentacle_port      = 41121

storage            = 1
elastic_ip_address = 1
advance_monitoring = 1
cpu_summary        = 1
iops_summary       = 1
disk_summary       = 1
network_summary    = 1

stats_agent        = 1
stats_agent_name   = AwsCloud

total_cost         = 1
cost_regions       = ["us-east-1","us-west-1"]

aws_regions        = ["us-east-1","eu-west-1"]
aws_instances      = ["<INSTANCE_ID>"]

creds_b64          = <BASE64_CREDENTIALS>
```

### Addon identity

| Item | Value |
|------|-------|
| Name | Amazon EC2 |
| Identifier | `pandorafms.aws.ec2` |
| Version | `1.5` |
| Type and section | Discovery, `cloud` |
| Marketplace entry | [pandorafms.aws.ec2](https://marketplace.pandorafms.com/entries/pandorafms.aws.ec2), updated 2026-08-31 |
| Availability | The Marketplace entry states that the download is limited to licensed users |
