# Network bandwidth SNMP

*Article last updated: 2026-09-30.*

## What it does

The Network bandwidth SNMP plugin retrieves the bandwidth usage of a network device, as a percentage, using SNMP. It reports the amount of information sent and received over a particular time, either for the whole device or for a single interface selected by its index.

The plugin runs as a Pandora FMS server plugin: each execution queries the device, prints one numeric value on standard output, and Pandora FMS stores that value in the module.

- **Result.** A single number, the bandwidth usage as a percentage, formatted with 9 decimals (for example `12.345678901`).
- **What is measured.** By default, the overall bandwidth usage. With `-inUsage 1` it reports the input usage only, and with `-outUsage 1` the output usage only. If both are enabled, the input usage is reported.
- **Scope.** With `-ifIndex <n>` the plugin measures that interface. Without it, the plugin measures every interface of the device and prints the average of the per-interface percentages, computed over the interfaces that have a usable speed.
- **Measurement window.** The value is computed from the difference between the counters read in the current execution and the counters stored by the previous execution. The module interval is therefore the measurement window.

## Prepare

### Requirements

1. **SNMP read access to the device** from the machine that runs the plugin, normally the Pandora FMS server. The default SNMP port is UDP 161.
2. **A device that exposes the IF-MIB objects** `ifIndex`, `ifInOctets`, `ifOutOctets`, `ifHighSpeed` and `ifSpeed`, and preferably the 64-bit counters `ifHCInOctets` and `ifHCOutOctets`. The `dot3StatsDuplexStatus` object of EtherLike-MIB is optional and is used to detect the duplex mode.
3. **Write permission in the temporary directory** (`/tmp` by default) for the user that runs the plugin. The plugin stores the counters of each execution there to compute the next one.

### Installation

The plugin is distributed with the Pandora FMS server and needs no separate installation. Its executable is:

```text
/usr/share/pandora_server/util/plugin/pandora_snmp_bandwidth
```

It is registered in Pandora FMS as the server plugin **Network bandwidth SNMP**, with a maximum timeout of 300 seconds.

### Choose the SNMP version

- **SNMP v1** always uses 32-bit counters, because 64-bit counters do not exist in SNMP v1.
- **SNMP v2c and v3** use 64-bit counters when the device provides them.

On fast links, prefer SNMP v2c or v3. A 32-bit octet counter wraps after 4,294,967,295 octets, which takes about 34 seconds at 1 Gbit/s. The plugin corrects at most one wrap per interval, so long intervals on fast links with 32-bit counters report values lower than the real ones.

## Configure

Create one module for each metric and each interface that you want to monitor, using the **Network bandwidth SNMP** server plugin, and fill in the plugin fields. The plugin returns a numeric percentage; choose the thresholds that fit your environment.

1. Set **SNMP Version(1,2c,3)** (`1`, `2c` or `3`) and the credentials for that version.
   - For SNMP v1 and v2c, fill in **Community**.
   - For SNMP v3, fill in **securityName** and, depending on **securityLevel**, the authentication and privacy fields. See [SNMPv3 settings](#snmpv3-settings).
2. Leave **Host** at its default value `_address_`, which is the address of the agent, or enter the address of the device.
3. Set **Port** if the device does not use the default port 161.
4. Fill in **Interface Index (filter)** with the `ifIndex` of the interface to measure. Leave it empty to measure all the interfaces and obtain their average.
5. Select the metric:
   - Overall bandwidth usage: leave **inUsage** and **outUsage** empty.
   - Input usage: set **inUsage** to `1`.
   - Output usage: set **outUsage** to `1`.
6. Set **UniqId** to an identifier that is unique for each module, with no spaces or symbols.
7. Adjust **timeout** (seconds per attempt) and **retries** if the device answers slowly.

!!! warning "Every module needs its own UniqId"
    The plugin stores the counters of the previous execution in a state file named after the host, or after the **UniqId** when one is set. Every module that uses the plugin against the same host must have a different **UniqId**. Otherwise the modules overwrite each other's previous samples and report `0` or wrong values.

### SNMPv3 settings

| Field | Behavior |
| --- | --- |
| **securityName** | Required for SNMP v3. |
| **securityLevel** | `noAuthNoPriv` (default), `authNoPriv` or `authPriv`. Case-insensitive. |
| **authProtocol**, **authKey** | Required with `authNoPriv` and `authPriv`. |
| **privProtocol**, **privKey** | Required with `authPriv`. |
| **context** | Optional SNMPv3 context name. Leave it empty to use no context. |

An invalid combination or value makes the plugin print nothing.

For the 192-bit and 256-bit AES protocols, choose the one that matches the key localization variant that the device implements: `AES192` and `AES256` use the Blumenthal extension (Net-SNMP style), while `AES192C` and `AES256C` use the Reeder extension (Cisco style).

### Options not available in the console

The options `-max`, `-f`, `-debug`, `-parallel`, `-tmp`, `-tmp_file`, `-tmp_separator` and `-log` are not fields of the plugin registration. They can be used only from the command line or from a configuration file. See [Operate](#operate) and [Reference](#reference).

### Protect the credentials

The community and the SNMPv3 passwords passed as command-line options can be visible in the operating system process list. To keep them out of the command line, store them in a configuration file and pass its path as the first argument. See [Use a configuration file](#use-a-configuration-file).

## Verify

Run the plugin manually with a `-uniqid` different from the one used by any production module, so that the test does not alter the samples of that module:

```bash
/usr/share/pandora_server/util/plugin/pandora_snmp_bandwidth -version 2c -community <COMMUNITY> -host <TARGET_HOST> -ifIndex <IFINDEX> -uniqid <UNIQUE_ID>
```

1. The first run prints `0.000000000`, because there is no previous data yet.
2. Wait some seconds while the interface carries traffic and run the same command again. The second run prints the real value, for example `12.345678901`.

An empty output means that the plugin failed. Run the command again with `-debug 1` and read the log file, as described in [Debug log](#debug-log).

## Understand the results

### Output and exit status

- The plugin always exits with status 0.
- On a failure (no SNMP answer, invalid parameters, unreachable device) it prints nothing.
- Running it without arguments prints the help text.

### Meaning of the value

For each interface the plugin computes a percentage from the octet counter differences (`Δin`, `Δout`), the seconds between executions (`Δt`) and the interface speed in bit/s:

| Metric | Formula |
| --- | --- |
| Bandwidth, half duplex or unknown duplex | `(Δin + Δout) × 8 / (Δt × speed) × 100` |
| Bandwidth, full duplex | `(Δin × 8 / (Δt × speed) + Δout × 8 / (Δt × speed)) / 2 × 100` |
| Input usage | `Δin × 8 / (Δt × speed) × 100`, capped at 100 |
| Output usage | `Δout × 8 / (Δt × speed) × 100`, capped at 100 |

- If the speed or `Δt` is 0, the value of the interface is 0.
- If a counter is lower than in the previous execution, the plugin treats it as a wrap and computes the difference as `max − previous + current + 1`, where `max` is 4,294,967,295 for 32-bit counters and 18,446,744,073,709,551,615 for 64-bit counters.
- Without `-ifIndex`, the result is the arithmetic mean of the per-interface values.

### First execution and zero values

The plugin prints `0.000000000` when it has no previous data for the counters. This happens on the first execution, after the counter width changes (for example, when the device stops returning 64-bit values), and the first time the plugin runs over a state file written by an earlier version of the plugin.

### Counter width

- Without `-ifIndex`, the plugin reads the interface table and uses the 64-bit counters `ifHCInOctets` and `ifHCOutOctets` when the device returns numeric values for `ifHCInOctets`. Otherwise it uses the 32-bit counters `ifInOctets` and `ifOutOctets`.
- With `-ifIndex <n>`, it uses the 64-bit counters when `ifHCInOctets.<n>` returns a number, and the 32-bit counters otherwise.
- With SNMP v1 it always uses the 32-bit counters.

### Interface speed

The speed, in bit/s, is selected in this order:

1. The value of `-max`, when it is set. It overrides the speed reported by the device for every measured interface and is intended for port channels and aggregated links, where the reported speed is not the real one.
2. `ifHighSpeed` (in Mbit/s) multiplied by 1,000,000, when it is greater than 0.
3. `ifSpeed` (in bit/s), when it is greater than 0.

An interface without a usable speed is skipped: it is not measured and it is not included in the average. With `-ifIndex`, the plugin prints `0.000000000` in that case.

!!! warning "The value of -max is in bit/s"
    `-max` is expressed in bit/s, not in Mbit/s, even though `ifHighSpeed` is reported in Mbit/s. For a port channel of 2 × 1 Gbit/s, use `-max 2000000000`. The value `-max 2000` means 2 kbit/s: the input and output usage saturate at 100 % and the overall bandwidth reports values far above 100.

### Duplex mode

The plugin reads the duplex mode from `dot3StatsDuplexStatus`: the value `2` means half duplex and `3` means full duplex. Any other value, or no answer, is an unknown duplex mode, which is handled as half duplex. Use `-f 1` to handle an unknown duplex mode as full duplex.

### Duplicate ifIndex values

When the plugin measures all the interfaces, it identifies each interface by the value of `ifIndex`. If the device reports the same value in several rows, the plugin keeps a single entry for that value:

- The last row that has a usable speed replaces the earlier ones.
- A later row without a usable speed does not remove an earlier valid one.
- The state file has one line per distinct value, and the average divides by the number of distinct values.

## Operate

### Use a configuration file

If the first argument is an existing file, the plugin reads it as a configuration file. Use it to keep credentials out of the command line:

```bash
/usr/share/pandora_server/util/plugin/pandora_snmp_bandwidth <PATH_TO_CONFIG> -ifIndex 5
```

- Each line has the form `key=value`. The keys are the option names without the leading dash.
- Lines that start with `#` are comments.
- The directive `include=<file>` includes another file.
- Options given on the command line override the values of the file.

### Debug log

With `-debug 1` the plugin writes a log file while it runs. The value printed on standard output does not change.

- The file is `<tmp>/pandora_bandwidth_<host or uniqid>.log`, with the same character replacement as the state file (see [State file](#state-file)). Use `-log` to write it to another path.
- Each line has the form `<date> - [info] <message>`. The first message of an execution truncates the file.
- The log records the target, the SNMP version, the timeout and retries, the state file, every SNMP request and answer with its timing, the counter width selected and the reason, the speed source and the duplex mode of each interface, the skipped interfaces and the reason, the previous and saved state, the formulas with their values substituted, the averages and the printed value.
- The community, the authentication and privacy passwords and the SNMPv3 user are never written to the log. Secret values are masked as `***` if they appear.

### Concurrency and timing

- `-parallel <N>` sets the maximum number of concurrent SNMP requests when all the interfaces are measured. The default is 8. A value that is not a positive integer keeps the default.
- `-timeout` sets the seconds to wait for each attempt and `-retries` the number of retries. Values out of range make the plugin print nothing.
- Keep the module interval short enough that a 32-bit counter cannot wrap more than once between executions.

### Command-line syntax

- Options are `-name value` pairs. A trailing option without a value is ignored.
- Boolean options (`-inUsage`, `-outUsage`, `-f`, `-debug`) are enabled with a number greater than 0, for example `1`.
- Short aliases exist for the connection options. See [Command line and configuration file options](#command-line-and-configuration-file-options).
- The option `-extra` is accepted and ignored.

### Connectivity check

Before it measures anything, the plugin reads `sysObjectID` (`.1.3.6.1.2.1.1.2.0`) from the device. If the device gives no answer, the plugin stops without printing anything.

## Troubleshoot

- **The plugin prints nothing.** The device did not answer the `sysObjectID` request, a parameter is invalid, `-timeout` or `-retries` is out of range, or the SNMPv3 settings are incomplete. Run the plugin with `-debug 1` and read the [debug log](#debug-log).
- **The value is always 0.**
  - It is the first execution, and the second one has not run yet.
  - Another module uses the same **UniqId** (or the same host without a **UniqId**), and both overwrite the previous samples. Give each module its own **UniqId**.
  - The interface has no usable speed. See "The interface is not measured" below.
  - The time between executions is 0.
  - The counter width changed since the previous execution.
- **The input or output usage is stuck at 100 %, or the bandwidth exceeds 100 %.** The speed used is too low. Check that `-max` is expressed in bit/s and not in Mbit/s, and check the `ifHighSpeed` and `ifSpeed` values that the device reports.
- **The values are lower than expected on a fast link.** The plugin is using 32-bit counters that wrap more than once per interval. Use SNMP v2c or v3 so that 64-bit counters are used, or shorten the module interval.
- **The interface is not measured.** Neither `ifHighSpeed` nor `ifSpeed` is greater than 0. Set the speed with `-max`.
- **The duplex mode is unknown.** If the link is full duplex, use `-f 1`.

## Reference

### Console fields (Network bandwidth SNMP)

| Field | Required | Default | Description |
| --- | --- | --- | --- |
| SNMP Version(1,2c,3) | No | `2c` | SNMP version: `1`, `2c` or `3`. Passed as `-version`. |
| Community | Yes for v1 and v2c | — | SNMP community. It may be empty. Passed as `-community`. |
| Host | No | `_address_` | Address of the device. The default is the address of the agent. Passed as `-host`. |
| Port | No | `161` | UDP port of the SNMP service. Passed as `-port`. |
| Interface Index (filter) | No | Empty | `ifIndex` of the interface to measure. Empty measures all the interfaces. Passed as `-ifIndex`. |
| securityName | Yes for v3 | — | SNMPv3 user name. Passed as `-securityName`. |
| context | No | Empty | SNMPv3 context name. Empty means no context. Passed as `-context`. |
| securityLevel | No | `noAuthNoPriv` | `noAuthNoPriv`, `authNoPriv` or `authPriv`. Passed as `-securityLevel`. |
| authProtocol | Yes with `authNoPriv` and `authPriv` | — | `MD5`, `SHA` (or `SHA1`), `SHA224`, `SHA256`, `SHA384` or `SHA512`. Passed as `-authProtocol`. |
| authKey | Yes with `authNoPriv` and `authPriv` | — | Authentication password. Passed as `-authKey`. |
| privProtocol | Yes with `authPriv` | — | `DES`, `AES` (or `AES128`), `AES192`, `AES256`, `AES192C` or `AES256C`. Passed as `-privProtocol`. |
| privKey | Yes with `authPriv` | — | Privacy password. Passed as `-privKey`. |
| UniqId | Yes, one per module | — | Unique identifier of the module, with no spaces or symbols. The plugin needs to store information in the temporary directory to calculate the bandwidth. Passed as `-uniqid`. |
| inUsage | No | Empty | Set to `1` to retrieve the input usage (%). Passed as `-inUsage`. |
| outUsage | No | Empty | Set to `1` to retrieve the output usage (%). Passed as `-outUsage`. |
| timeout | No | `2` | Seconds to wait for each attempt. Passed as `-timeout`. |
| retries | No | `1` | Number of retries. Passed as `-retries`. |

The plugin registration builds this parameter line:

```text
-version '_field1_' -community '_field2_' -host '_field3_' -port '_field4_' -ifIndex '_field5_' -securityName '_field6_' -context '_field7_' -securityLevel '_field8_' -authProtocol '_field9_' -authKey '_field10_' -privProtocol '_field11_' -privKey '_field12_' -uniqid '_field13_' -inUsage '_field14_' -outUsage '_field15_' -timeout '_field16_' -retries '_field17_'
```

### Command line and configuration file options

The same names are valid as keys of the configuration file, without the leading dash.

| Name | Alias | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `-version` | `-v` | No | `2c` | SNMP version: `1`, `2`, `2c` or `3`. |
| `-community` | `-c` | Yes for v1 and v2c | — | SNMP community. It may be empty. |
| `-host` | `-h` | No | `127.0.0.1` | Address of the device. |
| `-port` | `-p` | No | `161` | UDP port, from 0 to 65535. |
| `-timeout` | — | No | `2` | Seconds per attempt, from 1 to 60. Decimals are allowed. |
| `-retries` | — | No | `1` | Retries, from 0 to 20. |
| `-securityName` | `-u` | Yes for v3 | — | SNMPv3 user name. |
| `-context` | `-n` | No | Empty | SNMPv3 context name. |
| `-securityLevel` | `-l` | No | `noAuthNoPriv` | `noAuthNoPriv`, `authNoPriv` or `authPriv` (case-insensitive). |
| `-authProtocol` | `-a` | Yes with `authNoPriv` and `authPriv` | — | `MD5`, `SHA` (or `SHA1`), `SHA224`, `SHA256`, `SHA384` or `SHA512`. |
| `-authKey` | `-A` | Yes with `authNoPriv` and `authPriv` | — | Authentication password. |
| `-privProtocol` | `-x` | Yes with `authPriv` | — | `DES`, `AES` (or `AES128`), `AES192`, `AES256`, `AES192C` or `AES256C` (case-insensitive). |
| `-privKey` | `-X` | Yes with `authPriv` | — | Privacy password. |
| `-ifIndex` | — | No | Empty | `ifIndex` of the interface to measure. Without it, all the interfaces are measured and averaged. |
| `-inUsage` | — | No | Disabled | A number greater than 0 reports the input usage only. |
| `-outUsage` | — | No | Disabled | A number greater than 0 reports the output usage only. If `-inUsage` is also enabled, the input usage is reported. |
| `-max` | — | No | Not set | Interface speed in bit/s, used for every measured interface instead of the speed reported by the device. |
| `-f` | — | No | Disabled | A number greater than 0 handles an unknown duplex mode as full duplex. |
| `-uniqid` | — | No | Not set | Identifier used to name the state file and the log instead of the host. Required in practice when several modules query the same host. |
| `-parallel` | — | No | `8` | Maximum concurrent SNMP requests when all the interfaces are measured. |
| `-tmp` | — | No | `/tmp` | Directory of the state file and the log. |
| `-tmp_file` | — | No | Not set | Full path of the state file. |
| `-tmp_separator` | — | No | `;` | Field separator of the state file. |
| `-debug` | — | No | Disabled | A number greater than 0 writes the debug log. |
| `-log` | — | No | Not set | Path of the debug log file. |

### State file

The plugin stores the counters of each execution in a state file:

- Default path: `<tmp>/pandora_bandwidth_<host>.idx`, or `<tmp>/pandora_bandwidth_<uniqid>.idx` when `-uniqid` is set.
- Every `.` in the whole path is replaced with `_`. For host `192.0.2.10`, the file is `/tmp/pandora_bandwidth_192_0_2_10.idx`.
- `-tmp` changes the directory, `-tmp_file` sets the full path and `-tmp_separator` sets the field separator.

The file has one line per interface, in this format:

```text
timestamp;ifIndex;inOctets;outOctets;width;
```

`width` is `32` or `64`. Lines with a missing or different width are ignored, which is treated as having no previous data. Each execution rewrites the file with only the interfaces measured in that execution.

### OIDs used

| Object | OID | Use |
| --- | --- | --- |
| `sysObjectID` | `.1.3.6.1.2.1.1.2.0` | Connectivity check |
| `ifIndex` | `.1.3.6.1.2.1.2.2.1.1` | List of interfaces |
| `ifInOctets` | `.1.3.6.1.2.1.2.2.1.10` | 32-bit input counter |
| `ifOutOctets` | `.1.3.6.1.2.1.2.2.1.16` | 32-bit output counter |
| `ifHCInOctets` | `.1.3.6.1.2.1.31.1.1.1.6` | 64-bit input counter |
| `ifHCOutOctets` | `.1.3.6.1.2.1.31.1.1.1.10` | 64-bit output counter |
| `ifHighSpeed` | `.1.3.6.1.2.1.31.1.1.1.15` | Speed in Mbit/s |
| `ifSpeed` | `.1.3.6.1.2.1.2.2.1.5` | Speed in bit/s |
| `dot3StatsDuplexStatus` | `.1.3.6.1.2.1.10.7.2.1.19` | Duplex mode (`2` half, `3` full) |
