# MongoDB Discovery

*Article last updated: 2026-09-08.*

## What it monitors

The MongoDB Discovery plugin connects to MongoDB deployments and databases and turns their state and performance into Pandora FMS agents and modules. It reads a list of targets given as connection URIs, authenticates with the user embedded in each URI, and collects engine metrics through the `serverStatus`, `dbStats` and other commands.

A Discovery task creates one agent per target. When **Scan databases** is enabled it also collects per-database metrics, and when **Create agent per database** is enabled it creates one agent per discovered database. Custom queries can be defined to add one module per query and database.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Plugin version `1.6` (`pandorafms.mongodb`) | Documented target | The version this page describes, as identified by the package definition. See [Plugin identity](#plugin-identity). |
| A reachable MongoDB deployment | `Required` | The plugin establishes remote connections to each target through its connection URI. Prerequisite, not a compatibility statement. |
| A MongoDB user with the `read` or `dbAdmin` role on the monitored databases | `Required` | Needed for the database-level commands. Prerequisite, not a compatibility statement. See [Prepare MongoDB access](#prepare-mongodb-access). |
| A MongoDB user with the `clusterMonitor` or `clusterAdmin` role | `Required` | Needed for the server statistics. Prerequisite, not a compatibility statement. |
| A specific MongoDB version | `Not validated` | No published test record establishes compatibility with a concrete MongoDB release. |
| A specific Pandora FMS version | `Not validated` | No published test record establishes console or server version compatibility. |
| A specific host operating system | `Not validated` | No published test record establishes operating-system compatibility for the machine that runs the plugin. |

### Prerequisites

1. **A Pandora FMS server with Discovery enabled** to run the task, and a console to define it.
2. **Connectivity** between the Pandora FMS server and each MongoDB deployment (default port `27017`).
3. **A MongoDB user** with the required roles. See [Prepare MongoDB access](#prepare-mongodb-access).
4. **A target agent group and a monitoring interval** for the generated agents, taken from the Discovery task.

The plugin is distributed as a Pandora FMS Discovery application (`.disco` package) with its Python dependencies bundled, so no extra Python libraries have to be installed on the Discovery server.

### Prepare MongoDB access

The user used by the task must reach each deployment over the network and hold the roles the monitor needs. From the official prerequisites:

- **For databases**: the `read` or `dbAdmin` role on the databases to be monitored.
- **For server statistics**: the `clusterMonitor` or `clusterAdmin` role.

Grant the user only the access required by your monitoring policy; the plugin only reads and never changes MongoDB data or configuration.

### Install the plugin

Load the `.disco` package from **Management → Discovery → Extension manager** (the *Manage disco packages* view). The package is available from the [Pandora FMS library](https://pandorafms.com/library/mongodb-discovery/). Once loaded, **MongoDB** appears under the **Applications** category of the Discovery wizard.

![Manage disco packages view with the MongoDB Discovery application loaded.](../assets/images/discovery/mongodb-discovery/disco-packages.png)

## Configure the Discovery task

Create the task from **Management → Discovery → Applications → MongoDB**. The generic first step defines the task; the package adds **MongoDB Base**, **MongoDB Detailed** and **MongoDB custom**. Every field is documented in [Task parameters](#task-parameters).

**Step 1 — Task definition.** Name, agent group, server and interval. The group ID and the interval are passed to the plugin and applied to every generated agent.

**Step 2 — MongoDB Base.** The targets to connect to:

- **MongoDB target strings** is the list of instances to monitor, comma-separated or one per line. Each target is a MongoDB connection URI, for example `mongodb://172.17.0.2:27017` or `mongodb+srv://monitor.user:password@cluster.example.com/my_db`. Lines starting with `#` are comments.

![MongoDB Discovery task Base step: MongoDB target strings.](../assets/images/discovery/mongodb-discovery/base-step.png)

**Step 3 — MongoDB Detailed.** Execution, agent layout and which metrics to collect:

- **Max threads** distributes the targets across parallel workers.
- **Target agents** sets the agent names for the targets, matching the position of the target list; a blank entry uses the target string.
- **Use prefix for modules** and **Custom module prefix** prepend a prefix to every generated module name.
- **Scan databases** collects the per-database metrics of each target, and **Create agent per database** creates one agent per database, with **Custom database agent prefix** naming them.
- **Agent autodisable mode** creates the generated agents in Pandora FMS mode `2`, which disables an agent when all its modules become unknown.
- **Check engine uptime**, **Retrieve query statistics**, **Analyze connections**, **Retrieve latency statistics** and **Retrieve network statistics** select the engine metric groups collected.

![MongoDB Discovery task Detailed step.](../assets/images/discovery/mongodb-discovery/detailed-step.png)

**Step 4 — MongoDB custom.** The custom queries:

- **Execute custom queries** enables the custom queries, and **Custom queries** defines them.

![MongoDB Discovery task Custom step.](../assets/images/discovery/mongodb-discovery/custom-step.png)

## Verify the first run

Force the task from **Management → Discovery → Task list** and check the result in this order.

1. **The task summary** reports **Total agents**, **Targets up** and **Targets down**. Targets up are the targets the plugin managed to connect to.

2. **The agents.** One agent appears per reachable target, named by the **Target agents** list or by the target string. With **Create agent per database**, one agent appears per discovered database.

3. **The engine modules.** A reachable target carries its connection, uptime, query, connection, latency and network modules according to the enabled toggles.

4. **The database modules.** With **Scan databases** enabled, each database carries its collections, indexes, size, status and custom query modules.

Targets that cannot be reached are counted in **Targets down** and do not produce agents.

![MongoDB Discovery task execution summary.](../assets/images/discovery/mongodb-discovery/task-summary.png)

## Understand the results

### Agents and identity

The plugin creates one agent per target by default. The agent name is the value from the **Target agents** list that matches the target position, or the target string when none is given. Each generated agent reports `MONGODB` as its operating system, its `os_version` is the MongoDB version returned by the server information (or `Discovery` when it cannot be read), and it belongs to the task's group (by ID) with the task interval. With **Agent autodisable mode** enabled the agents are created in Pandora FMS mode `2`. The generated agents are returned in the plugin JSON output.

With **Create agent per database**, the plugin also creates one agent per database, named `<Custom database agent prefix><target agent> <database name>`, and counts them in **Total agents**.

The databases to monitor are collected from the deployment when **Scan databases** is enabled. When a target lists databases after `|` in its URI, only those are monitored; appending `!` to the URI excludes the listed ones and monitors the rest. The engine metrics always go to the target agent, and the per-database metrics go to the database agents when **Create agent per database** is enabled, or to the target agent otherwise.

### Modules by agent

| Agent | Created when | Modules it carries |
| --- | --- | --- |
| Target agent | A target is reachable | `MONGODB connection`, the engine metrics enabled by the toggles, and the per-database modules when **Scan databases** is enabled without **Create agent per database** |
| Database agent | **Create agent per database** enabled and a database is discovered | The `<database>` metrics and the custom query modules |

Module names are `<Custom module prefix>` plus the module name; the database modules also include the database name. The exhaustive module inventory and the toggle that enables each group are in [Generated modules and agents](#generated-modules-and-agents).

## Operate

### Manual execution

The plugin can run outside Discovery, from a Pandora FMS agent or directly from the command line, with a configuration file and the target, agent and custom-query files created manually:

```bash
./pandora_mongodb --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> --target_agents <PATH_TO_AGENTS> --custom_queries <PATH_TO_QUERIES>
```

Only `--conf` and `--target_databases` are required; `--target_agents` and `--custom_queries` are optional. The plugin connects to each target in parallel according to **Max threads** and produces the agents and modules in its Discovery JSON output.

The target list holds the connection URIs, which may embed a username and a password. Restrict them to the account that runs the plugin and keep them out of shared directories, logs and version control.

## Troubleshoot

| Symptom | Check |
| --- | --- |
| No agent is created and the target is reported **Targets down** | Confirm the deployment is reachable from the Pandora FMS server on its port (default `27017`), that the MongoDB service is running, and that the connection URI is correct. |
| Engine modules are missing and the execution information logs command errors | The user needs the `clusterMonitor` or `clusterAdmin` role for the server statistics (`serverStatus`), and `read` or `dbAdmin` on the monitored databases. Grant those roles. |
| Per-database modules are missing | Enable **Scan databases**. A target without a `|` database list and with **Scan databases** off only produces the engine modules. |
| Database agents are not created | Enable **Create agent per database**. Without it, the database modules are placed on the target agent. |
| Custom query modules are missing | The query must be inside `check_begin`/`check_end`, use a permitted read command, and be run with **Scan databases** enabled. Check the crontab expression if the query is scheduled. |
| Expected modules are missing | Review the **Detailed** toggles: a disabled group produces no modules. |

## Reference

### Task parameters

The console presents the task fields in three steps after the generic task definition. The macro column is the identifier used in the generated task configuration.

#### MongoDB Base

| Field | Macro | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| MongoDB target strings | `_dbstrings_` | textarea | — | List of MongoDB connection URIs. Required |

#### MongoDB Detailed

| Field | Macro | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| Max threads | `_threads_` | number | `1` | Workers that distribute the targets |
| Target agents | `_engineAgent_` | textarea | — | Agent names for the targets, matching the target list position; blank uses the target string |
| Use prefix for modules | `_usePrefixmodule_` | checkbox | off | Enables the module prefix |
| Custom module prefix | `_prefixModuleName_` | string | — | Prefix prepended to every module name. Shown only when **Use prefix for modules** is enabled |
| Scan databases | `_scanDatabases_` | checkbox | off | Collects the per-database metrics of each target |
| Create agent per database | `_agentPerDatabase_` | checkbox | off | Creates one agent per database |
| Custom database agent prefix | `_prefix_` | string | — | Prefix for the database agents. Shown only when **Create agent per database** is enabled |
| Agent autodisable mode | `_agentautodisable_` | checkbox | off | Creates agents in Pandora FMS mode `2`, which disables an agent when all its modules become unknown |
| Check engine uptime | `_checkUptime_` | checkbox | on | Server uptime |
| Retrieve query statistics | `_queryStats_` | checkbox | on | Query operation counters |
| Analyze connections | `_checkConnections_` | checkbox | on | Connection counters |
| Retrieve latency statistics | `_checkLatency_` | checkbox | on | Operation latencies |
| Retrieve network statistics | `_checkNetwork_` | checkbox | on | Network traffic counters |

#### MongoDB custom

| Field | Macro | Type | Default | Notes |
| --- | --- | --- | --- | --- |
| Execute custom queries | `_executeCustomQueries_` | checkbox | on | Enables the custom queries |
| Custom queries | `_customQueries_` | textarea | — | Definition of the custom queries. Shown only when **Execute custom queries** is enabled |

### Configuration file

The Discovery task builds a temporary `--conf` file from its own fields. A manual run supplies it directly. The file has a `[CONF]` section; the plugin reads it without a section header.

| Key | Default | Description |
| --- | --- | --- |
| `agents_group_id` | `10` | ID of the group where the agents are created |
| `interval` | `300` | Monitoring interval in seconds, inherited by the agents |
| `threads` | `1` | Number of parallel workers |
| `modules_prefix` | Empty | Prefix for the module names |
| `execute_custom_queries` | `1` | Enables the custom queries |
| `analyze_connections` | `0` | Connection counters |
| `engine_uptime` | `0` | Server uptime |
| `query_stats` | `0` | Query statistics |
| `network` | `0` | Network statistics |
| `latency` | `0` | Latency statistics |
| `scan_databases` | `0` | Collects the per-database metrics |
| `agent_per_database` | `0` | Creates one agent per database |
| `agent_autodisable` | `0` | Creates agents in Pandora FMS mode `2` when enabled |
| `db_agent_prefix` | Empty | Prefix for the database agents |
| `cron_state_dir` | Empty | Folder for the custom query crontab state; derived from the task temporary path |

### Target databases

The `--target_databases` file holds one or more MongoDB connection URIs, comma-separated or one per line. Lines starting with `#` and blank lines are ignored. A URI may include a comma inside a replica-set connection string.

```text
mongodb://172.17.0.2:27017
mongodb://monitor.user:s3cur3P@ss@mongo-prod-01.internal.company.com:27017/my_db
```

To monitor specific databases of a target, append `|` and separate the databases with `;`:

```text
mongodb://172.17.0.2:27017|my_db;test
```

To monitor every database except a set, append `!` before the `|`:

```text
mongodb://172.17.0.2:27017!|my_db;test
```

### Target agents

The optional `--target_agents` file holds one agent name per target, comma-separated or one per line. The position of each name matches the position of the corresponding target in the target list; blank lines are ignored. A blank entry leaves the agent named after the target string.

### Command-line execution

The plugin accepts a configuration file, a target databases file, an optional target agents file and an optional custom queries file:

```bash
./pandora_mongodb --conf <PATH_TO_CONFIG> --target_databases <PATH_TO_TARGETS> --target_agents <PATH_TO_AGENTS> --custom_queries <PATH_TO_QUERIES>
```

| Option | Description |
| --- | --- |
| `--conf` | Required path to the configuration file |
| `--target_databases` | Required path to the file with the target instances |
| `--target_agents` | Optional path to the file with the target agent names |
| `--custom_queries` | Optional path to the file with the custom queries |

Example configuration file:

```ini
[CONF]
agents_group_id=10
interval=300
threads=1
modules_prefix=
execute_custom_queries=1
engine_uptime=1
query_stats=1
analyze_connections=1
latency=1
network=1
scan_databases=1
agent_per_database=0
```

### Custom queries

Each custom query creates one module per matching agent and database and is defined between `check_begin` and `check_end`:

| Field | Description |
| --- | --- |
| `name` | Module name |
| `description` | Module description |
| `operation` | `value` returns a single value, `full` returns all rows as a string |
| `datatype` | `generic_data`, `generic_data_string` or `generic_proc` |
| `min_warning`, `max_warning` | Numeric warning thresholds |
| `str_warning` | String warning condition |
| `warning_inverse` | `1` inverts the warning threshold interval |
| `min_critical`, `max_critical` | Numeric critical thresholds |
| `str_critical` | String critical condition |
| `critical_inverse` | `1` inverts the critical threshold interval |
| `module_interval` | Module interval, as a multiplier of the agent interval |
| `crontab` | 5-field cron expression; the query runs only when the date/time matches. Empty runs every interval |
| `target` | The command, one of `dbStats`, `collStats`, `find`, `count`, `aggregate`, `listCollections` |
| `target_instances` | Targets or agents where the module is created; `all` or empty applies to all |
| `target_databases` | Databases where the module is created; `all` or empty applies to all |
| `ignore_databases` | Databases where the module is not created |

The custom queries are executed against the monitored databases during the database scan, so **Scan databases** must be enabled for them to run. The target accepts the `$__self_dbname` reserved word, which is replaced by the database name currently being analyzed. The supported commands are read-only; `dbStats`, `collStats`, `find`, `count`, `aggregate` and `listCollections` are allowed, other commands are rejected.

```text
check_begin
name Query count
description Number of documents
operation value
datatype generic_data
min_warning 10
target db.coll.count({})
target_databases all
check_end
```

### Generated modules and agents

Module names are `[<Custom module prefix>]<module name>`, and the database modules also include the database name.

**Target agent** (one per reachable target)

Always created:

- `MONGODB connection`: `generic_proc`, `1` when the target is reachable, `0` otherwise.

Created when the matching toggle is enabled:

- **Check engine uptime**: `Uptime` (`generic_data`, estimated time of activity).
- **Retrieve query statistics**: `queries command`, `queries delete`, `queries getmore`, `queries insert`, `queries query`, `queries update` (`generic_data`, operation counters).
- **Analyze connections**: `connections current`, `connections available`, `connections totalCreated` (`generic_data`).
- **Retrieve latency statistics**: `operationlatencies.reads latency`, `operationlatencies.reads ops`, `operationlatencies.writes latency`, `operationlatencies.writes ops`, `operationlatencies.commands latency`, `operationlatencies.commands ops` (`generic_data`).
- **Retrieve network statistics**: `network bytesIn`, `network bytesOut`, `network numRequests` (`generic_data`).

**Database modules** (on the target agent or on the database agent, created when **Scan databases** is enabled, for each database found on the target)

- `<database> collections`: `generic_data`, number of collections.
- `<database> indexes`: `generic_data`, number of indexes.
- `<database> indexSize`: `generic_data`, total size of all indexes (bytes).
- `<database> views`: `generic_data`, number of views.
- `<database> objects`: `generic_data`, number of documents.
- `<database> avgObjSize`: `generic_data`, average document size (bytes).
- `<database> dataSize`: `generic_data`, total size of the data (bytes).
- `<database> storageSize`: `generic_data`, space used on disk (bytes).
- `<database> totalSize`: `generic_data`, sum of the data and index size (bytes).
- `<database> fsUsedSize`: `generic_data`, space used on the file system (bytes).
- `<database> fsTotalSize`: `generic_data`, total file system size (bytes).
- `<database> status`: `generic_data`, `1` when the database responds, `0` otherwise.
- The custom query modules that match the database.

### Plugin identity

| Field | Value |
| --- | --- |
| App short name | `pandorafms.mongodb` |
| Plugin version | `1.6` |
| Type | Discovery application (`.disco`) |
| Section | Discovery → Applications |