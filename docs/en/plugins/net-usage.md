# Net usage plugin

*Article last updated: 2026-10-26.*

## What it does

The Net usage plugin measures the traffic of the network interfaces of a Linux
host and publishes it in Pandora FMS. Each run reads the kernel interface
counters of the machine where it runs, adds the bytes received and transmitted
by every selected interface, and writes the result as Pandora FMS module XML on
standard output.

It is an **agent plugin**: the Pandora FMS agent runs it as one of its
`module_plugin` lines at every agent interval and ingests the modules it prints.
There is no configuration file, no credential and no network request — every
figure comes from the local interface counters of the monitored host.

One run always emits one incremental module per selected interface plus one
module with the total of all of them. The interface names can be narrowed with
inclusion and exclusion filters, and a prefix can be added to every module name
so that the same host, or several hosts in the same agent, keep their modules
apart.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.pandora_netusage`, version `1.1` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| A Linux host that exposes `/proc/net/dev` | `Required` | It is the only data source of the plugin: the run fails on any host that does not provide that file |
| Rocky Linux 9 | `Known compatible` | The legacy guide for this addon records Rocky 9 as the system where it was tested. Not re-validated for version `1.1` |
| Other Linux distributions | `Not validated` | No distribution range or version matrix has been recorded for this addon |
| A Pandora FMS agent on the monitored host | `Required` | The plugin is executed by the agent and its output is consumed as agent plugin modules |
| Pandora FMS versions | `Not validated` | The Marketplace carries a general banner for all its integrations, not a statement specific to this addon |

The plugin runs on the monitored host itself, so it reports the interfaces of
that host only. It has no remote execution mode and no connection to any other
system.

### Requirements

1. **A Linux host** with `/proc/net/dev` readable by the user that runs the
   agent. The plugin only reads that file; it needs no elevation and no other
   privilege.
2. **A Pandora FMS agent** installed on that host and able to execute plugins.
   The agent is what turns the printed modules into modules in the console.
3. **A Marketplace account with a license**: the download of this addon is
   limited to licensed users.

### Install the plugin

Download the package from the Marketplace entry:

[https://marketplace.pandorafms.com/entries/pandorafms.pandora_netusage](https://marketplace.pandorafms.com/entries/pandorafms.pandora_netusage)

The package installs the `pandora_netusage` executable. Copy it to the plugins
directory of the agent and make it executable. With the default paths of a
Linux agent that is:

```bash
cp pandora_netusage /usr/share/pandora_agent/plugins/
chmod 755 /usr/share/pandora_agent/plugins/pandora_netusage
```

Instead of copying the file by hand, the agent can distribute it to its hosts
as a file collection; the destination is the same plugins directory.

!!! warning "The agent package already contains a plugin with this name"
    The Linux agent distribution includes its own `plugins/pandora_netusage`.
    That file is a different plugin: it publishes a single
    `Network_Usage_Bytes` module for the sum of all interfaces and accepts no
    options. Both files have the same name in the same directory, and the
    default agent configuration file already contains a
    `module_plugin pandora_netusage` line, so a copy installed under that name
    replaces the bundled plugin and starts running from that existing line with
    no options. Check that line, or install this addon under a different file
    name and use that name in the `module_plugin` line.

## Configure

### Add the plugin to the agent

The plugin is configured in the agent configuration file
(`pandora_agent.conf`), as one `module_plugin` line. The executable path is
followed by the options you want to apply; the agent runs the line and ingests
the module XML it prints:

```apache
module_plugin /usr/share/pandora_agent/plugins/pandora_netusage
```

Without options the plugin reports every interface of the host, including the
loopback interface, and adds the total. Restart or reload the agent after
editing the file so that the new line takes effect.

Every `module_plugin` line is an independent execution that produces its own
set of modules. Two lines with different `--module_prefix` values on the same
host publish two separate sets of modules, which is the way to keep, for
example, one unfiltered view and one filtered view of the same interfaces.

!!! note "One line, many modules"
    A single `module_plugin` line is enough for the whole host. The plugin has no
    option to publish one interface per module: every run emits all the selected
    interfaces plus the total, and the agent creates one module for each. If the
    default `module_plugin pandora_netusage` line of the agent is still in the
    file, the plugin runs twice per interval; with the same prefix both
    executions publish modules with the same names, so keep one line, or give
    each of them its own `--module_prefix`.

### Filter the interfaces

Two options narrow the set of interfaces. Both take a regular expression that
is compared with the interface name, and both are optional:

- **`--allow_regexp`** keeps only the interfaces whose name matches. Empty or
  absent, every interface is measured.
- **`--deny_regexp`** removes the interfaces whose name matches. It is applied
  after the inclusion filter, so an interface matched by both is removed.

The expression is searched anywhere in the name: `eth` matches `eth0` and
`veth1`. Anchor it with `^` and `$` to match a complete name. Names are matched
as the kernel reports them, so an interface called `ens192` is not matched by
`eth`.

```apache
module_plugin /usr/share/pandora_agent/plugins/pandora_netusage --allow_regexp "^eth|^ens" --deny_regexp "^lo$"
```

With that line the plugin measures the `eth*` and `ens*` interfaces, leaves the
loopback out, and publishes their total. Quote each pattern: the agent runs the
line as a shell command, and characters such as `|` or `$` are interpreted
before the plugin receives them.

A filtered interface disappears from the plugin output, and so does its share
of the total: the total is the sum of the interfaces that survive both filters.
If the combination selects no interface, the run still emits the total module,
with value `0`.

A pattern that is not a valid regular expression is not detected when the agent
starts: the run aborts with an error and prints no modules. Test the pattern
manually before putting it in the agent configuration (see [Verify](#verify)).

### Prefix the module names

`--module_prefix` adds text in front of every module name. The prefix is
concatenated with no separator, so include your own:

```apache
module_plugin /usr/share/pandora_agent/plugins/pandora_netusage --module_prefix "host01-" --allow_regexp "^eth"
```

That line produces `host01-eth0 Network_Usage_Bytes` and
`host01-Network_Usage_Bytes_Total`. Use a prefix that identifies the host or
the environment, and keep it stable: changing it creates a new set of modules
and leaves the previous ones without data.

## Verify

Run the plugin manually from the directory that contains the executable:

```bash
./pandora_netusage --allow_regexp "^eth"
```

Each run executes once and exits. A successful run prints one `<module>` block
per selected interface, in the order in which the kernel lists them, and the
total block last:

```xml
<module>
	<name><![CDATA[eth0 Network_Usage_Bytes]]></name>
	<type>generic_data_inc</type>
	<data><![CDATA[4821936642]]></data>
	<description><![CDATA[Total bytes/sec transfered in this system]]></description>
	<unit><![CDATA[Bytes]]></unit>
</module>
<module>
	<name><![CDATA[Network_Usage_Bytes_Total]]></name>
	<type>generic_data_inc</type>
	<data><![CDATA[4821936642]]></data>
	<description><![CDATA[Total bytes/sec transfered in this system (all interfaces)]]></description>
	<unit><![CDATA[Bytes]]></unit>
</module>
```

The numbers are the cumulative counters of that moment. Run the command twice,
a few seconds apart, and compare: on an interface that carries traffic the
second value is larger than the first.

`./pandora_netusage --help` prints the usage summary, with the version and the
three options.

Once the `module_plugin` line is in place and the agent has run it, the modules
appear in the agent in the console:

<!-- SCREENSHOT NEEDED: Pandora FMS agent view listing the modules generated by pandora_netusage for one Linux host, with the per-interface modules and Network_Usage_Bytes_Total. -->

To confirm what the console stores for one of them, open the module:

<!-- SCREENSHOT NEEDED: Definition view of one Network_Usage_Bytes module showing type incremental, unit Bytes and the description text, with no real customer data. -->

## Understand the results

### Module names

| Module name | Type | Unit | Value |
| --- | --- | --- | --- |
| `<PREFIX><interface> Network_Usage_Bytes` | `generic_data_inc` | `Bytes` | Bytes received plus bytes transmitted by that interface, cumulative |
| `<PREFIX>Network_Usage_Bytes_Total` | `generic_data_inc` | `Bytes` | Sum of the previous values over the selected interfaces |

`<PREFIX>` is the value of `--module_prefix`, empty by default. The interface
name is followed by a space and `Network_Usage_Bytes`, so a host with `eth0` and
`eth1` and no prefix produces `eth0 Network_Usage_Bytes`,
`eth1 Network_Usage_Bytes` and `Network_Usage_Bytes_Total`.

The plugin sends no module group, no interval and no threshold: the modules are
sampled at the agent interval, and any alerting or grouping is configured in the
console on top of them.

### What the value means

Each module carries the raw kernel counter, which is what the host has
accumulated since the interface came up, and the module type is **incremental**.
Pandora FMS therefore records the growth between two consecutive samples, not
the cumulative figure: an interface that has been running for weeks reports a
counter in the thousands of millions, while the stored value is the traffic of
the last interval. Two consecutive samples are needed before any increment
exists.

The total is computed after the filters, so it always matches the interface
modules of that same run. A host whose selection is empty reports a total of
`0`, which is the only module of that run.

There is no availability or status module. When the plugin cannot read
`/proc/net/dev`, it prints no module at all and the existing modules simply
receive no new data.

The description text of every module says `Total bytes/sec transfered in this
system`, which describes the derived increment in the console, not the raw
counter that the plugin prints.

## Operate and troubleshoot

### Everyday operation

- The plugin keeps no state: every execution reads the counters of that moment,
  so it can be run manually at any time without disturbing the agent modules.
- The agent schedules it. Choose the agent interval according to the resolution
  you need: the stored increment covers the interval between two executions.
- Interface names are part of the module names. When an interface is renamed —
  a new NIC naming scheme, a new virtual interface — the previous modules stop
  receiving data and new ones appear. Keep the filters and the prefix stable to
  avoid it.
- The counters restart at zero when the host reboots or when an interface goes
  down and up again. The sample that follows carries a value lower than the
  previous one; it is not real traffic.

### Troubleshooting

- **No modules appear in the agent** — check that the `module_plugin` line
  points to the executable that is really in the plugins directory and that the
  file is executable, then run it manually. Remember that the agent package
  contains a plugin with the same name (see [Install the plugin](#install-the-plugin)).
- **The run prints `Error:` and nothing else** — `/proc/net/dev` could not be
  read. Confirm that the host is Linux, that the file exists and that the agent
  user can read it. The message goes to standard output, and the exit status is
  `0`, so the failure is easy to miss in a scheduled run: the agent sees a
  successful execution and logs nothing. Look for the message, not for the exit
  status.
- **The run prints no modules and reports an error about the pattern** — one of
  the two regular expressions is not valid. Test each pattern on its own. Under
  the agent, a run that ends with a non-zero exit status has its output
  discarded and the error code logged, and the standard error of a plugin is not
  kept: run the command manually to read the message.
- **The total is `0`** — the filters exclude every interface. Simplify
  `--allow_regexp`, or remove `--deny_regexp`, and run the plugin again.
- **Loopback traffic dominates the figures** — the loopback interface is
  measured like any other. Exclude it with `--deny_regexp "^lo$"`.
- **Modules named `Network_Usage_Bytes` appear instead of the documented ones** —
  that module name belongs to the plugin bundled with the agent package, not to
  this addon. Check which executable the `module_plugin` line runs.
- **A module stopped updating after a network change** — the interface name
  changed. Compare the module names with the current interfaces and adjust the
  filters.

## Reference

### Command-line parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `--module_prefix` | No | Empty | Text placed immediately before every module name, with no separator added. |
| `--allow_regexp` | No | Empty (all interfaces) | Regular expression searched in the interface name; only matching interfaces are measured. Anchor it with `^` and `$` to match a complete name. |
| `--deny_regexp` | No | Empty (nothing excluded) | Regular expression searched in the interface name; matching interfaces are excluded. Applied after `--allow_regexp`, so it wins when both match. |
| `-h`, `--help` | No | — | Prints the usage summary, with the version and the three options, and exits. |

All the options are optional and none of them takes a mandatory value. Options
are given in `--name value` form; `--name=value` is also accepted.

### Generated modules

| Module name | Type | Unit | Description sent by the plugin |
| --- | --- | --- | --- |
| `<PREFIX><interface> Network_Usage_Bytes` | `generic_data_inc` | `Bytes` | `Total bytes/sec transfered in this system` |
| `<PREFIX>Network_Usage_Bytes_Total` | `generic_data_inc` | `Bytes` | `Total bytes/sec transfered in this system (all interfaces)` |

The per-interface modules are emitted in the order in which `/proc/net/dev`
lists the interfaces; the total is always the last block of the run.

### Output and exit status

| Situation | Output | Exit status |
| --- | --- | --- |
| Successful run | One `<module>` block per selected interface and the total block, on standard output | `0` |
| `--help` | Usage summary on standard output | `0` |
| Unknown option or malformed command line | Usage error on standard error | `2` |
| `/proc/net/dev` cannot be read | `Error: ` followed by the command error, on standard output, and no modules | `0` |
| Invalid regular expression | Error on standard error and no modules | Non-zero |
| Interrupted with `Ctrl+C` or `SIGTERM` | `Signal received, exiting cleanly...` | `0` |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.pandora_netusage` |
| Name | Net usage |
| Version | `1.1` — the version of the Marketplace package `pandorafms.pandora_netusage.1.1.zip`, also reported by the usage summary |
| Category | Miscelaneus |
| License | One; the download is limited to licensed users |
| Marketplace last update | 2026-02-05 |
| Marketplace entry | [pandorafms.pandora_netusage](https://marketplace.pandorafms.com/entries/pandorafms.pandora_netusage) |
| Workflow | Monitoring plugin, executed by the Pandora FMS agent |
| Executable | `pandora_netusage` |
