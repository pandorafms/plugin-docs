# HA History Plugin

*Article last updated: 2026-10-23.*

## What it does

`pandora_history_ha` is a standalone plugin for the high availability (HA) of
the Pandora FMS history database on MySQL. It is a management plugin for an
existing HA cluster; it does not provide the HA mechanism itself. It runs on
one host, probes every node on each check cycle, decides which node is the
active primary (master), and promotes a replica when no node is writable. It
monitors replica health and, with `splitbrain_autofix` enabled, reconfigures
replicas that are stopped or point to the wrong source. It can also update the
main Pandora FMS database so its components read the active node as the history
database host.

The service works at server level: it inspects `read_only` and the replica
status, and it issues administrative statements, but it never reads or writes
the history data tables. It generates no Pandora FMS modules and has no console
interface, so it is not a server plugin, an agent plugin or a Discovery plugin.

It is installed as the `pandora_history_ha` systemd service and distributed
through the Marketplace entry `pandorafms.pandora_history_ha`. The download is
limited to licensed users.

## Prepare

### Requirements

1. **A Linux host with systemd.** The service is installed and managed as a
   systemd unit. Installation requires root, because the installer writes under
   `/opt` and `/etc/systemd/system` and manages the service. The generated unit
   does not drop privileges: the service runs as root.
2. **MySQL 8.0.22 or later on every node of the history database cluster.**
   The package declares compatibility with MySQL 8.0.22 or later.
3. **Network access from the service host to every cluster node**, on the
   database port configured with `dbport`. Access to the main Pandora FMS
   database is required only when the main database update is enabled.
4. **Database privileges**, required for operation:

| Credential | Privileges | Applies to |
| --- | --- | --- |
| `dbuser` | `REPLICATION CLIENT`, `RELOAD`, plus `SUPER`, or `SYSTEM_VARIABLES_ADMIN` and `REPLICATION_SLAVE_ADMIN` | Every node in `ha_hosts` |
| `repl_dbuser` | `REPLICATION SLAVE` | Every node that can act as replication source, only when `splitbrain_autofix 1` |
| `main_dbuser` | `UPDATE` on the `tconfig` table | Main Pandora FMS database, only when the main database update is enabled |

5. **Binary logging enabled on every node and a unique `server_id`.** The service
   reads the elected master's binary log position to reconfigure replicas.

**Note:** `REPLICATION_SLAVE_ADMIN` alone cannot change the global `read_only`
or `super_read_only` variables. `RELOAD` is required to reset replica metadata
during automatic reconfiguration.

**Note:** the configuration file stores every database password in plain text,
and the installer does not restrict its permissions. Protect it before or
immediately after installation, for example with `chown root:root` and
`chmod 600`. The service must run on a single host: there is no distributed
lock, so do not run two instances against the same cluster.

### Install

1. Download the package from the Marketplace entry
   [`pandorafms.pandora_history_ha`](https://marketplace.pandorafms.com/entries/pandorafms.pandora_history_ha).
   The download is limited to licensed users.
2. Transfer the package to the host that will manage the cluster — normally the
   Pandora FMS server — and extract it.
3. As root, run the installer from the extracted directory:

```bash
./pandora_history_ha_installer --install
```

The default installation directory is `/opt/pandorafms/pandora_history_ha`: the
program is installed under `bin/` and the configuration file is
`/opt/pandorafms/pandora_history_ha/pandora_history_ha.conf`.

`--destdir <directory>` prefixes the installation, configuration and unit paths
with that directory. The `PIDFile` of the unit stays
`/var/run/pandora_history_ha.pid`. In a normal installation the installer manages
the host's systemd; with `--destdir` the unit is written under the destination
tree and the host's systemd cannot start it, so start it from the target
environment. Use it only for staged or image-based installations, because the
generated unit references the paths inside that directory. For staged or
image-based installations, review the generated unit and any links under
`/opt/pandorafms` before starting the service.

**Note:** in a normal installation the installer writes and enables the unit and
starts the service immediately, before you edit the configuration. With
`--destdir` the unit is written under the destination tree and the host's
systemd cannot start it; start it from the target environment. The shipped
sample does not describe your cluster, so review the configuration (see
[Configure](#configure)) and stop the service if it is already running with
values that do not apply.

Reinstalling with `--install` is the upgrade path: the existing configuration
stays in `pandora_history_ha.conf`, the new sample is written as
`pandora_history_ha.conf.new`, and the service is restarted. Compare both files
and merge the new tokens you need from `pandora_history_ha.conf.new` into
`pandora_history_ha.conf`.

## Configure

### Configuration file

The configuration file is
`/opt/pandorafms/pandora_history_ha/pandora_history_ha.conf`. Its path is fixed
at installation time.

The file contains one `<token> <value>` pair per line, separated by whitespace.
It is not a `key=value` file. These rules apply:

- `#` starts a comment anywhere in the line; the rest of the line is ignored.
  Because `#` starts a comment anywhere, a value cannot contain `#`.
- Blank lines are ignored.
- Unknown tokens are accepted silently, so a misspelled token is ignored
  instead of reported.
- When a token repeats, the last value wins.
- Empty values cannot be set.

`dbuser`, `dbpass` and `ha_hosts` are required. The service refuses to start if
any of them is missing or empty.

The configuration is read only at startup. After editing the file, restart the
service (see [Service management](#service-management)).

### Example configuration

This example describes a three-node cluster with the main database update
enabled. Replace every placeholder.

```ini
dbuser              <DB_USER>
dbpass              <DB_PASSWORD>
ha_hosts            <HOST_1>,<HOST_2>,<HOST_3>

ha_interval         30
splitbrain_autofix  0

main_dbhost         <PANDORA_DB_HOST>
main_dbuser         <PANDORA_DB_USER>
main_dbpass         <PANDORA_DB_PASSWORD>

# See the configuration reference for the remaining tokens.
```

### Key settings

Beyond the required tokens, two settings change the behavior of the service and
deserve an explicit decision.

`splitbrain_autofix` (default `0`): when set to `1`, the service reconfigures
replica threads that are stopped or pointing to a different source, using
`repl_dbuser` and `repl_dbpass`. It does not control split-brain handling:
forcing `read_only=1` on the extra writable nodes is always automatic. Enable
it only after verifying the replication credentials and the cluster topology,
because a wrong source or a wrong user rewrites the replica configuration.

`main_dbhost` (empty by default): IP address or FQDN of the main Pandora FMS
database. When set, it enables the update of the `history_db_host` row of the
`tconfig` table in that database after every master change. This keeps Pandora FMS pointed at the active node
without manual intervention. All the `main_db*` tokens are ignored while
`main_dbhost` is empty. The configured `main_dbuser` needs `UPDATE` on
`tconfig`.

The order of `ha_hosts` is also a decision: it is the tie-breaker when more than
one node is eligible (see [Master election](#master-election)). Use the same host
spelling in `ha_hosts` as the replication source configured on the replicas. The
service compares the two as text; a mismatch causes an unnecessary
reconfiguration.

## Verify

1. Check that the service is active:

```bash
systemctl status pandora_history_ha
```

2. Follow the log file — by default
   `/opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log`:

```bash
tail -f /opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log
```

The startup lines report the version, the configuration path, the host list,
the database name and port, and the AutoFix state. After that, the service logs
`Checking history DB cluster [...]` on every cycle and establishes a master.
Representative startup sequence:

```text
2026-06-24 10:00:00 [LOG] pandora_history_ha v1.0 starting
2026-06-24 10:00:00 [LOG] Hosts  : <HOST_1>, <HOST_2>, <HOST_3>
2026-06-24 10:00:01 [LOG] Master established: <HOST_1>
```

3. The installed service writes its PID file to
   `/var/run/pandora_history_ha.pid`.
4. When the main database update is enabled, check the row:

```sql
SELECT value FROM tconfig WHERE token = 'history_db_host';
```

It should contain the active node. It is updated on the first election and
after every master change.

The same value is shown in the Pandora FMS console under **Setup → Historical
database**. The screenshots below show the installation before and after a
failover. The host values are redacted as `<HOST_1>` (old master) and
`<HOST_2>` (promoted replica).

![History database settings before failover, host redacted as <HOST_1>](../assets/images/plugins/ha-history-plugin/history-db-before-failover.png)

![History database settings after failover, host redacted as <HOST_2>](../assets/images/plugins/ha-history-plugin/history-db-after-failover.png)

## Understand the HA behavior

### Master election

Every cycle, the service probes each host in `ha_hosts` sequentially, in the
order listed. A node that reports `read_only=0` is writable and is treated as a
master candidate; a node that reports `read_only=1` is a replica candidate, not
necessarily a configured replica. Replica candidates are ranked by their
replication delay, and an unknown delay is treated as the worst possible one.

- Exactly one writable node: that node is the master.
- No writable node: the read-only node with the smallest replication delay is
  selected for promotion. The service stops replication and disables `read_only`
  on it.
- More than one writable node: see
  [Failover and split-brain](#failover-and-split-brain).

### Failover and split-brain

More than one writable node is a split-brain condition. The service keeps the
current master if it is still writable; otherwise it keeps the first writable
node in `ha_hosts` order. Then it forces `read_only=1` on the remaining
writable nodes. On service start the current master is unknown, so the first
writable node in `ha_hosts` wins.

**Note:** to demote the extra writable nodes, the service clears
`super_read_only` and then sets `read_only=1`. This does not block accounts that
hold `SUPER`: those accounts can still write to a node that has been demoted.

When no node is writable, the service promotes the read-only node with the
smallest replication delay. The service requests the promotion: it stops
replication and disables `read_only`. Verify that the node reports `read_only=0`
before relying on it.

### Replica checks

After the election, the service checks every node except the elected master. A
node is healthy when its replication IO and SQL threads are running and its
configured source is the elected master. A healthy node is logged as
`Replication OK: <replica> -> <master> (delay: <n>s)`.

When a node is not healthy, the result depends on `splitbrain_autofix`:

- `splitbrain_autofix 1`: the node is reconfigured as a replica of the elected
  master, using the master binlog position when it is available.
- `splitbrain_autofix 0`: the service only logs a warning on every cycle, with
  the IO and SQL thread state and the expected source.

### Main database update

After a master change — including the first election — and only when
`main_dbhost` is set, the service updates the `history_db_host` value in the
`tconfig` table of the main Pandora FMS database. Only that token is updated.
The update is attempted only on a master change: a failure is retried after the
next master change, not on the next cycle.

### Limitations

The service works with MySQL asynchronous replication. It does not wait for a
replica to apply its relay log before promoting it, and automatic replica
reconfiguration resets the replica metadata and positions it at the master's
current binary log position. Plan failovers with replicas that are caught up,
and validate the data on both nodes after an unplanned failover. Writes accepted
by a node while it was isolated are not reconciled.

`pandora_history_ha` is a controller, not a full cluster manager:

- It provides no quorum, fencing, virtual IP or DNS management.
- The order of `ha_hosts` is the tie-breaker when more than one node is
  eligible.
- It acts only on reachability, `read_only`/`super_read_only` and replica
  status.
- The cycle period is the work time plus `ha_interval`. A cluster-node
  connection uses a 5-second timeout and up to `ha_connect_retries` attempts per
  node (total attempts, not additional retries), with `ha_connect_delay` between
  attempts. The main database connection is a single attempt with a 10-second
  timeout.

## Operate and troubleshoot

### Service management

```bash
systemctl start pandora_history_ha
systemctl stop pandora_history_ha
systemctl restart pandora_history_ha
systemctl status pandora_history_ha
systemctl enable pandora_history_ha
systemctl disable pandora_history_ha
```

Restart the service after every configuration change: the file is read only at
startup. With `Restart=always`, the unit restarts the service 10 seconds after
an unexpected exit; a `systemctl stop` keeps it stopped. The unit declares
ordering after `network.target` and `mysql.service`.

### Logs

Once the configuration is valid, the service writes its application output only
to `log_file`
(`/opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log` by default) and
appends to it; the service does not rotate the file, so configure external
rotation and retention. Startup validation errors are written to standard error
and appear in `systemctl status` and `journalctl -u pandora_history_ha`.

Each line has the format `YYYY-MM-DD HH:MM:SS [LEVEL] message`. The levels are
`LOG`, `WARNING` and `DEBUG`; `DEBUG` messages are written only with
`verbose 1`.

The directory of `log_file` must exist and be writable by the service, which
runs as root.

### Upgrade

Run the installer with `--install` again:

```bash
./pandora_history_ha_installer --install
```

The existing configuration stays in `pandora_history_ha.conf`, the new sample is
written as `pandora_history_ha.conf.new`, and the service is restarted. Compare
both files and merge the new tokens you need from `pandora_history_ha.conf.new`
into `pandora_history_ha.conf`.

On upgrade, the installer may update the shared runtime under `/opt/pandorafms`
when the package includes a newer one. Back up the host or schedule a
maintenance window before upgrading.

### Uninstall

As root, run:

```bash
./pandora_history_ha_installer --uninstall
```

The installer stops and disables the service, and removes the unit and the
program. The configuration file
(`/opt/pandorafms/pandora_history_ha/pandora_history_ha.conf`), the log file and
the installation directory remain in place; remove them manually if they are no
longer needed.

During uninstall the installer may ask whether to remove a shared directory
under `/opt/pandorafms`. If other Pandora FMS components use that directory,
answer no; do not run the uninstaller unattended.

### Troubleshooting

- **The service is not running after installation.** Check
  `systemctl status pandora_history_ha` and `journalctl -u pandora_history_ha`
  for startup validation errors, and confirm the required tokens and the
  `log_file` directory.
- **A host is unreachable.** The log shows
  `Host '<host>' is unreachable, skipping` or
  `Cannot reach replica host '<host>'`. Check the network path, the port and the
  credentials for that node.
- **`Replication problem on '<host>' ... Set splitbrain_autofix=1 to
  auto-reconfigure.` repeats on every cycle.** The replica threads are stopped
  or point to a different source. Verify the replication credentials and the
  topology before enabling `splitbrain_autofix`.
- **`Error configuring replica ... Access denied; you need (at least one of) the
  RELOAD privilege(s) for this operation`.** The monitoring user lacks `RELOAD`,
  which the service needs to reset replica metadata (`RESET REPLICA ALL`). Grant
  `RELOAD` to `dbuser` on the node that is reconfigured.
- **`Split-brain detected! Writable hosts: ...` appears.** More than one node is
  writable. The service keeps one master and forces `read_only=1` on the others,
  but investigate the cluster to remove the cause.
- **`tconfig(history_db_host) row not found...` appears.** The update matched no
  row. Check that `tconfig` contains the `history_db_host` row and that the
  history database is enabled in Pandora FMS.
- **Configuration edits have no effect.** The file is read only at startup, so
  restart the service.
- **`Promoted '<host>' to master` appears but writes fail.** The message records
  the promotion request; verify that the node reports `read_only=0` and that
  replication is stopped before sending writes to it.

## Reference

### Configuration file parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `dbname` | No | `pandora` | Accepted for compatibility and shown in the startup log; the service connects at server level and does not select this database. |
| `dbport` | No | `3306` | TCP port used to reach every node in `ha_hosts`. |
| `dbuser` | Yes | — | Monitoring user. Needs `REPLICATION CLIENT`, `RELOAD` and `SUPER`, or `SYSTEM_VARIABLES_ADMIN` and `REPLICATION_SLAVE_ADMIN`, on every node. |
| `dbpass` | Yes | — | Password for `dbuser`. Stored in plain text in the configuration file. |
| `repl_dbuser` | Only with `splitbrain_autofix 1` | — | Replication user. Needs `REPLICATION SLAVE`. Used to reconfigure replica threads. |
| `repl_dbpass` | Only with `splitbrain_autofix 1` | — | Password for `repl_dbuser`. Stored in plain text. |
| `ha_hosts` | Yes | — | Comma-separated IP addresses or FQDNs of all cluster nodes. The order is the tie-breaker when more than one node is eligible. Use the same spelling as the replication source configured on the replicas. |
| `ha_interval` | No | `30` | Seconds to wait after each check cycle. The effective period is the cycle work time plus this value. Must be 1 or greater. |
| `ha_connect_retries` | No | `3` | Connection attempts per node before it is considered unreachable. Also used when reading the master binlog position. Must be 1 or greater; `0` makes no connection attempts. |
| `ha_connect_delay` | No | `2` | Seconds between connection attempts to the same node. |
| `splitbrain_autofix` | No | `0` | `1` reconfigures replica threads that are stopped or pointing to a different source; it does not control split-brain handling. Reconfiguration resets the replica metadata and positions it at the master's current binary log position. |
| `verbose` | No | `0` | `1` adds `DEBUG` messages to the log. |
| `log_file` | No | `/opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log` | Path to the log file. Its directory must exist and be writable. |
| `pid_file` | No | `/var/run/pandora_history_ha.pid` | PID file used when the service starts without `-p`. The installed unit passes `-p /var/run/pandora_history_ha.pid`, which takes precedence. |
| `main_dbhost` | No | — | IP address or FQDN of the main Pandora FMS database. When set, enables the main database update after each master change. All other `main_db*` tokens are ignored when empty. |
| `main_dbport` | No | `3306` | Port of the main Pandora FMS database. |
| `main_dbname` | No | `pandora` | Name of the main Pandora FMS database. |
| `main_dbuser` | No | — | User for the main database. Needs `UPDATE` on the `tconfig` table. |
| `main_dbpass` | No | — | Password for `main_dbuser`. Stored in plain text. |

The file uses one `<token> <value>` pair per line. `#` starts a comment anywhere
in the line, blank lines are ignored, unknown tokens are accepted silently and
the last occurrence of a repeated token wins.

Values cannot contain `#`. `ha_interval` and `ha_connect_retries` must be 1 or
greater.

### Installer options

The installer requires root. Exactly one of `--install` or `--uninstall` is
required; `--destdir` is optional.

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `--install` | One of `--install` or `--uninstall` | — | Installs the service, or upgrades it when it is already installed. Writes and enables the unit and starts the service. |
| `--uninstall` | One of `--install` or `--uninstall` | — | Stops and disables the service, removes the unit and the program, and keeps the configuration file, the log file and the installation directory. |
| `--destdir <directory>` | No | — | Prefixes the installation, configuration and unit paths with the given directory. The unit's `PIDFile` stays `/var/run/pandora_history_ha.pid`, and the installer manages the systemd instance of the host. Use it only for staged or image-based installations, because the generated unit references the paths inside that directory. Review the generated unit and any links under `/opt/pandorafms` before starting the service. |

### Paths and service

| Item | Value |
| --- | --- |
| Installation | `/opt/pandorafms/pandora_history_ha`, with the program under `bin/` |
| Configuration file | `/opt/pandorafms/pandora_history_ha/pandora_history_ha.conf` |
| Service | `/etc/systemd/system/pandora_history_ha.service`; runs as root, restarts 10 seconds after an unexpected exit, and declares ordering after `network.target` and `mysql.service` |
| Log and PID | `/opt/pandorafms/pandora_history_ha/bin/pandora_history_ha.log` and `/var/run/pandora_history_ha.pid` |

### Log messages

The messages below are representative; `<...>` marks a runtime value and `...`
marks omitted detail.

| Message | Meaning |
| --- | --- |
| `Host '<host>' is unreachable, skipping` | The node did not answer during the election; the cycle continues with the next host. |
| `Cannot reach replica host '<host>'` | The node could not be reached during the replica checks; the cycle continues with the next node. |
| `Split-brain detected! Writable hosts: <list>` | More than one node reports `read_only=0`. |
| `Keeping '<host>' as master; forcing read_only=1 on remaining writable hosts` | The master kept in a split-brain condition. |
| `No writable host found. Best failover candidate: <host> (delay: <n>s or unknown)` | No node is writable; the read-only node selected for promotion. |
| `Promoted '<host>' to master (read_only disabled, replication stopped)` | The promotion was requested on the candidate. |
| `Replication problem on '<host>' (...)` | Replica threads stopped or pointing to another source; see [Troubleshooting](#troubleshooting). |
| `tconfig(history_db_host) updated to '<new>'` / `tconfig(history_db_host) row not found in main DB — history DB may not be enabled in Pandora` | The main database row was updated, or the update matched no row. |
