# Inventory plugin for MAC

*Article last updated: 2026-10-26.*

## What it does

The Inventory plugin for MAC collects hardware and software inventory from a
macOS endpoint and publishes it to Pandora FMS. Each execution reads the
processor model, the memory, the disk partitions, the network hardware ports and
the contents of `/Applications`, and prints the result as an inventory document
on standard output.

The addon has a single execution model: **agent plugin**. It takes no arguments
and reads no configuration file. The Pandora FMS agent runs it from its
configuration file on every agent execution and forwards the inventory document
to Pandora FMS, where the data appears in the inventory view of the agent.

The addon produces inventory data only. It creates no monitoring modules, so it
adds no graphs, thresholds or alerts.

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.mac_inventory`, version `1.0` | Documented target | Version of the Marketplace entry. See [Addon identity](#addon-identity) |
| A macOS endpoint | `Required` | The addon reads macOS system utilities that exist only on macOS |
| The Pandora FMS agent for macOS, able to run `module_plugin` entries and forward inventory data | `Required` | The addon is started from the agent configuration file |
| A `perl` interpreter for the user that runs the agent | `Required` | The agent starts the addon through `perl` (see [Add the plugin to the agent](#add-the-plugin-to-the-agent)) |
| The macOS utilities `sysctl`, `system_profiler`, `top`, `diskutil`, `networksetup` and `ls` | `Required` | Commands listed in [Generated inventory modules](#generated-inventory-modules) |
| macOS 10.13 High Sierra | `Not validated` | No reproducible record exists for this addon |
| macOS 10.14 Mojave | `Not validated` | No reproducible record exists for this addon |
| Any other macOS release | `Not validated` | No version matrix is recorded for this addon |
| Pandora FMS release | `Not validated` | No release-specific record exists. The Marketplace states that its integrations are compatible with Pandora FMS NG 784 and later |

The guide this page replaces lists macOS High Sierra and macOS Mojave, with
Pandora FMS agent version 755, as the tested environment. That record cannot be
reproduced from the addon and is not presented here as a validated compatibility
statement: the macOS releases above stay `Not validated` until a test record for
this addon exists.

### Requirements

1. **A macOS endpoint** monitored by a Pandora FMS agent.
2. **The Pandora FMS agent for macOS**, installed and reporting to the Pandora
   FMS server, and able to run `module_plugin` entries and forward their
   inventory output.
3. **A `perl` interpreter** available to the user and the environment that run
   the agent.
4. **The standard macOS utilities** the addon calls: `sysctl`,
   `system_profiler`, `top`, `diskutil`, `networksetup` and `ls`. No additional
   software has to be installed on the endpoint.
5. **The five inventory modules** created in Pandora FMS before the first
   execution (see [Create the inventory modules](#create-the-inventory-modules)).

### Install the plugin

Download the package from the Pandora FMS Marketplace entry, which is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.mac_inventory](https://marketplace.pandorafms.com/entries/pandorafms.mac_inventory)

The entry distributes version `1.0` as `pandorafms.mac_inventory.1.0.zip`. Copy
the plugin file `mac_inventory.pl` to the macOS endpoint, for example to
`/usr/local/pandora/mac_inventory.pl`, and make it readable by the user that
runs the agent. There is nothing else to install: the addon has no dependencies
of its own and no configuration file.

## Configure

### Create the inventory modules

The addon supplies data for five inventory modules, and Pandora FMS stores
inventory data in the inventory modules that already exist. Create these five
modules in the console before the first execution, with these exact names:

| Inventory module | Content |
| --- | --- |
| `CPU` | Processor model |
| `RAM` | Installed memory and current memory usage |
| `DISK` | Disk partitions |
| `CARDS` | Network hardware ports |
| `APPS` | Contents of `/Applications` |

The name is the link between the addon and the console: it is matched exactly,
in uppercase, and the disk module is `DISK` in the singular, not `DISKS`. An
inventory module with a different name receives no data, and the addon does not
report the mismatch.

<!-- SCREENSHOT NEEDED: Pandora FMS inventory module definition form filled with the name CPU, with no customer data. -->

### Add the plugin to the agent

Add one line to the end of the agent configuration file `pandora_agent.conf` on
the macOS endpoint:

```text
module_plugin perl /usr/local/pandora/mac_inventory.pl
```

Then restart the agent. The line names the interpreter, `perl`, and the path of
the plugin file; use a path without spaces. This is the whole configuration:
the addon has no parameters, no configuration file, no environment variables and
no flags, and the agent passes it no arguments.

`module_plugin` runs on every agent execution, so the inventory is collected
each time the agent reports. The addon has no interval or schedule option of its
own: the agent interval governs how often the inventory is refreshed.

## Verify

### Run the plugin manually

Run the addon from a terminal on the endpoint, as the user that runs the agent:

```bash
perl /usr/local/pandora/mac_inventory.pl
```

A successful run prints one `<inventory>` document with the five
`<inventory_module>` blocks and exits with status `0`. This is the shape of the
output; the values are illustrative:

```xml
<inventory>
<inventory_module>
<name><![CDATA[CPU]]></name>
<datalist>
<data><![CDATA[Apple M1]]></data>
</datalist>
</inventory_module>
<inventory_module>
<name><![CDATA[RAM]]></name>
<datalist>
<data><![CDATA[      Memory: 16 GB]]></data>
<data><![CDATA[PhysMem: 12G used (2100M wired), 3900M unused.]]></data>
</datalist>
</inventory_module>
<inventory_module>
<name><![CDATA[DISK]]></name>
<datalist>
<data><![CDATA[   0:      GUID_partition_scheme                        *500.3 GB   disk0]]></data>
<data><![CDATA[   1:                        EFI EFI                     209.7 MB   disk0s1]]></data>
</datalist>
</inventory_module>
<inventory_module>
<name><![CDATA[CARDS]]></name>
<datalist>
<data><![CDATA[Hardware Port: Wi-Fi]]></data>
<data><![CDATA[Device: en0]]></data>
</datalist>
</inventory_module>
<inventory_module>
<name><![CDATA[APPS]]></name>
<datalist>
<data><![CDATA[drwxr-xr-x  3 root  wheel  96 Jan  1 00:00 Example.app]]></data>
</datalist>
</inventory_module>
</inventory>
```

The addon prints the document with no header, no logging and no options. When a
command it calls fails, the error goes to standard error — and therefore to the
agent log — while the document is still printed.

### Check the inventory in the console

After the next agent execution, open the inventory view of the macOS agent in
the Pandora FMS console. The five modules are listed with the data collected in
that run.

<!-- SCREENSHOT NEEDED: Inventory view of the macOS agent in the console, showing the CPU, RAM, DISK, CARDS and APPS modules with data. -->

## Understand the results

Every run prints the same five inventory modules, in this order: `CPU`, `RAM`,
`DISK`, `CARDS` and `APPS`. Each module holds a data list whose entries are the
raw output lines of the command that feeds it. The addon does not parse,
convert or normalise them, so every entry is text exactly as the command printed
it.

- **`CPU`.** One entry with the processor brand string reported by the system.
- **`RAM`.** Two entries with two different readings: the installed-memory line
  from `system_profiler`, with its label and padding, and a snapshot of current
  memory use from `top`. Both live in the same module.
- **`DISK`.** One entry per partition line of `diskutil list`, including the
  partition-scheme line of each disk. The size and the disk identifier stay
  inside the raw line. Whole-disk header lines such as
  `/dev/disk0 (internal, physical):` are not matched and are not included.
- **`CARDS`.** One entry per line of `networksetup -listallhardwareports`, so
  the module holds the hardware port, the device and the link-layer address of
  each port. Blank lines in the command output become empty entries.
- **`APPS`.** One entry per line of `ls -l /Applications`: permissions, owner,
  group, size, date and bundle name. It covers `/Applications` only, so
  applications installed anywhere else are not listed.

Because the entries are raw text, the data is informational: it cannot be
graphed or given thresholds, the `RAM` module mixes two formats in one module,
`CARDS` publishes the hardware addresses of the endpoint and `APPS` publishes
the file owner names of the applications.

## Operate and troubleshoot

### Run-time behavior

- One execution reads, prints and exits. The addon keeps no state between runs,
  so each run reports the inventory of that moment.
- It writes nothing to disk and opens no network connection: the document goes
  to standard output, which the agent reads; anything a command writes to
  standard error goes to the agent log.
- It reads no arguments. Any argument passed to it is ignored, and it has no
  `-h` or `--help` option.
- It runs on every agent execution, because that is how `module_plugin` works.
- Every run executes `system_profiler` and `top -l 1`, which sample the system
  on demand, so choose the agent interval with that cost in mind.

### Known limitations

These are behaviors of version `1.0`, documented as they are.

- **The module names are fixed and matched exactly.** `DISK` is singular and
  every name is uppercase. Data for a name that has no matching inventory module
  in the console has nowhere to land in the inventory, and the addon does not
  report it.
- **The addon has no error handling.** It exits with status `0` even when a
  command it calls fails. When a command is missing or returns nothing, the
  corresponding module is still printed, with empty or partial entries, and no
  module is omitted.
- **On a host that is not macOS the result is empty.** The commands do not
  exist, so the five modules are printed with empty data lists and the command
  errors go to standard error.
- **Running the file directly depends on its interpreter line.** That line names
  `/usr/bin/Perl`, with a capital `P`, which resolves on the default
  case-insensitive macOS volume but not on a case-sensitive one. Start the addon
  through `perl`, as the agent configuration does.
- **There is no filtering or limit.** Every line the commands print becomes an
  entry, so the `APPS` module can hold hundreds of entries on a workstation with
  many applications, and `CARDS` repeats the layout of the `networksetup`
  output, blank lines included.
- **The inventory is text only.** No numeric module is created, so there is no
  trend, no threshold and no alerting surface.

### Diagnostics

| Symptom | Cause and action |
| --- | --- |
| The inventory view of the agent shows no data | The `module_plugin` line is missing from `pandora_agent.conf`, the agent has not run since the line was added, or the inventory modules do not exist. Check the line, restart the agent and create the five modules |
| Some modules have data and others do not | The missing inventory module exists with a different name. The match is exact: check the uppercase spelling and `DISK` in the singular |
| `perl: command not found` in the agent log | The interpreter is not in the environment of the agent. Install it or fix the agent `PATH` |
| `diskutil: command not found`, `system_profiler: command not found` or similar in the agent log | The addon is running on a host that is not macOS |
| A module has empty entries | The command that feeds it printed nothing for that entry, for example a blank line in `networksetup` output |
| An application is missing from `APPS` | It is not installed in `/Applications` |
| The data does not change between runs | The values are stable on the endpoint, or the agent is not executing the plugin: check the agent interval and the agent log |

## Reference

### Agent configuration

| Directive | Required | Value |
| --- | --- | --- |
| `module_plugin` | Yes | `perl /usr/local/pandora/mac_inventory.pl` |

The line goes in `pandora_agent.conf` on the macOS endpoint and takes effect
after the agent restarts. There is no other input surface: no configuration
file, no command-line options, no environment variables and no console plugin
registration.

### Command-line execution

| Command | Behavior |
| --- | --- |
| `perl /usr/local/pandora/mac_inventory.pl` | Prints the inventory document and exits with status `0` |
| `perl /usr/local/pandora/mac_inventory.pl -h` | Same output: the addon reads no arguments and has no help option |

### Generated inventory modules

| Module | Source | Entries |
| --- | --- | --- |
| `CPU` | `sysctl -n machdep.cpu.brand_string` | One: the processor brand string |
| `RAM` | `system_profiler SPHardwareDataType` (memory line) and `top -l 1 -s 0` (PhysMem line) | Two: installed memory and current memory use |
| `DISK` | `diskutil list` (partition lines) | One per partition line, partition-scheme line included |
| `CARDS` | `networksetup -listallhardwareports` | One per output line, blank lines included |
| `APPS` | `ls -l /Applications` | One per output line |

These are the exact commands behind each module:

```text
CPU    sysctl -n machdep.cpu.brand_string
RAM    system_profiler SPHardwareDataType | grep "Memory:"
RAM    top -l 1 -s 0 | grep PhysMem
DISK   diskutil list | grep -E "[ ]+[0-9]+:.*disk[0-9]+"
CARDS  networksetup -listallhardwareports
APPS   ls -l /Applications
```

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.mac_inventory` |
| Name | Inventory plugin for MAC |
| Version | `1.0` |
| Category | Miscelaneus |
| License | One |
| Marketplace last update | 2025-06-26 |
| Availability | Download limited to licensed users |
