# Pandora LDAP

*Article last updated: 2026-10-26.*

## What it does

The Pandora LDAP plugin monitors an OpenLDAP directory from Pandora FMS. Each
run binds to the directory with a bind DN and a password, measures how long the
bind takes, and reads the `cn=Monitor` subtree of the server's monitor backend.
The result becomes Pandora FMS modules: the bind response time, the totals of
initiated and completed operations, connection and statistic counters, and two
per-second rates.

The plugin has three delivery paths:

- **Agent plugin mode** (`--as_agent_plugin 1`): prints one `<module>` block per
  module on standard output.
- **Data file mode** (default, `--as_agent_plugin 0`): writes an `agent_data`
  document for the agent into the Pandora FMS data directory and prints `1`.
- **Tentacle delivery** (`--tentacle_address`): writes the document, sends it
  with the Tentacle client and prints `1`. This path takes precedence over
  `--as_agent_plugin`.

Every execution is independent: the plugin keeps no state between runs.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions. It is a general statement, not a test record for this plugin |
| An OpenLDAP server that exposes the `cn=Monitor` subtree | `Required` | The plugin searches `cn=Monitor` and reads its monitor attributes on every run |
| A directory account with read access to `cn=Monitor` | `Required` | Prerequisite, not a compatibility statement: the plugin binds with the credentials given in `-b` and `-p` |
| Network access from the host that runs the plugin to the LDAP listener | `Required` | The plugin connects to the URL given in `-s` |
| `tentacle_client` in `PATH` | `Required` when `--tentacle_address` is used | The plugin executes the Tentacle client to deliver the document |
| Other directory servers, such as Active Directory | `Not validated` | The plugin reads the OpenLDAP monitor tree; no other directory server has been recorded |
| OpenLDAP versions | `Not validated` | No version matrix has been recorded for this plugin |
| Operating system of the host that runs the plugin | `Not validated` | No operating system has been recorded for this version |

### Requirements

1. **An OpenLDAP directory** reachable from the host that runs the plugin, with
   the monitor backend enabled and readable. See
   [Prepare the LDAP server](#prepare-the-ldap-server).
2. **A bind account with read access to `cn=Monitor`.** The plugin needs no
   other permission, because it reads only the monitor subtree.
3. **Pandora FMS** to receive the output: the plugin server for data file and
   Tentacle delivery, or a Pandora FMS agent for agent plugin mode.
4. **A writable data directory** when the plugin writes the document itself.
   The default is `/var/spool/pandora/data_in/`.
5. **The Tentacle client** (`tentacle_client`) in `PATH`, only for Tentacle
   delivery.

### Prepare the LDAP server

The plugin reads the monitor backend of OpenLDAP. Check that the module is
loaded; run this on the directory server as root:

```bash
ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=module{0},cn=config" -s base '(objectClass=*)' olcModuleLoad
```

If `back_monitor` appears among the `olcModuleLoad` values in the response, the
monitor backend is enabled. Otherwise load it in `cn=config`; on a default
installation the module entry is `cn=module{0},cn=config`. Use an LDIF file:

```ldif
dn: cn=module{0},cn=config
changetype: modify
add: olcModuleLoad
olcModuleLoad: back_monitor
```

```bash
ldapmodify -Y EXTERNAL -H ldapi:/// -f <PATH_TO_CONFIG>
```

Then grant the bind account read access to the whole monitor subtree: in the
`cn=config` ACL of the `Monitor` database, give `read` on
`dn.subtree="cn=Monitor"` to the bind DN and deny it to everyone else. The
database entry index (`olcDatabase={n}Monitor`) depends on the server, so list
the databases of `cn=config` before editing the entry.

Verify the access with the account the plugin will use:

```bash
ldapsearch -x -LLL -H 'ldap://<TARGET_HOST>:389' -D '<BIND_DN>' -W -b 'cn=Monitor' -s sub '(objectClass=*)' monitorCounter
```

A correct account receives the entries of the monitor tree with their
`monitorCounter` values. `-W` prompts for the password, so it is not stored in
the shell history or exposed in the process list.

### Install the addon

Download the `.pspz2` package from the Marketplace entry, which is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.pandoraldap](https://marketplace.pandorafms.com/entries/pandorafms.pandoraldap)

Upload it in the Pandora FMS console with the plugin registration, described in
[Register the plugin in the console](#register-the-plugin-in-the-console). The
package contains the `pandora_ldap` executable and its plugin definition: the
name **Pandora LDAP**, a 20-second maximum timeout, the parameter string and
seven macros. The distributed package is self-contained: the host that runs it
needs no Python installation.

Pandora FMS installs the executable in its plugin directory, typically
`/usr/share/pandora_server/util/plugin/`, and executes it from the server
selected for the module.

## Configure

### Execution models

The plugin selects the delivery path in this order:

1. **`--tentacle_address` is present.** The plugin writes the `agent_data`
   document into `--data_dir` and sends it with `tentacle_client` to
   `<tentacle_address>:<tentacle_port>`. It prints `1` and removes the file
   after a successful transfer. `--as_agent_plugin` is ignored in this path.
2. **`--as_agent_plugin 1`.** The plugin prints one `<module>` block per module
   on standard output, without an `agent_data` wrapper, and writes no file.
   This is the output a Pandora FMS agent plugin expects.
3. **Any other value, or the option omitted.** The plugin writes the
   `agent_data` document into `--data_dir` and prints `1`. The default value is
   `0`, which selects this path.

`--as_agent_plugin` accepts only an integer: a value such as `true` is a usage
error and the run stops with exit status 2.

### Run from the command line

A minimum agent plugin run needs the four mandatory options:

```bash
./pandora_ldap -s 'ldap://<TARGET_HOST>:389' -b 'cn=monitor,dc=example,dc=com' \
    -p '<PASSWORD>' -a ldap-lab --as_agent_plugin 1
```

A data file run, with the destination group and data directory made explicit:

```bash
./pandora_ldap -s 'ldap://<TARGET_HOST>:389' -b 'cn=monitor,dc=example,dc=com' \
    -p '<PASSWORD>' -a ldap-lab -g ldap --data_dir /var/spool/pandora/data_in/
```

A Tentacle run:

```bash
./pandora_ldap -s 'ldap://<TARGET_HOST>:389' -b 'cn=monitor,dc=example,dc=com' \
    -p '<PASSWORD>' -a ldap-lab --tentacle_address <PANDORA_FMS_SERVER> --tentacle_port 41121
```

- `-s` takes the LDAP URL, including the scheme and the port. Both `ldap://`
  and `ldaps://` are accepted; the plugin has no TLS options of its own, so the
  URL and the LDAP client configuration of the host govern the connection.
- `-a` names the agent that the `agent_data` document creates or updates in the
  console. It is also the base of the output file name.
- `-g` is the destination group of that agent. The default is `ldap`.
- `-m` prefixes every module name, so the same directory can feed several
  agents with distinguishable modules. It has no default.
- `--data_dir` must exist and be writable by the user that runs the plugin.
- The Tentacle path uses `tentacle_client` from `PATH`, and there is no option
  for a Tentacle password.

### Register the plugin in the console

1. Open **Servers → Plugins** and upload the `.pspz2` package with **Register
   Plugin**. The upload registers the plugin, its executable and its macros.
2. Open the plugin in the list. The definition shows the name **Pandora LDAP**,
   a 20-second maximum timeout and this parameter string:

```text
-s _field1_ -b _field2_ -p _field3_ -a _field4_ --as_agent_plugin _field5_ -g _field6_ --data_dir _field7_
```

3. Fill each macro with the values of the directory. The macros are the
   registration surface of the addon:

| Field | Option | Value to enter |
|-------|--------|----------------|
| `_field1_` | `-s` | LDAP URL with the port, for example `ldap://<TARGET_HOST>:389` |
| `_field2_` | `-b` | Bind DN, for example `cn=monitor,dc=example,dc=com` |
| `_field3_` | `-p` | Password of the bind DN. Enable **Hide value** |
| `_field4_` | `-a` | Name of the agent that will hold the modules |
| `_field5_` | `--as_agent_plugin` | `1` to print the module XML, `0` to write the data file |
| `_field6_` | `-g` | Destination group of the agent, for example `ldap` |
| `_field7_` | `--data_dir` | Pandora FMS data directory, for example `/var/spool/pandora/data_in/` |

<!-- SCREENSHOT NEEDED: Pandora FMS plugin registration form for the Pandora LDAP package, showing the parameter string and the seven macros. -->

Once registered, the plugin is available when creating plugin modules, and
each module fills the macros individually.

The parameter string passes a value to every option, so it runs as it is only
when every macro has a value. A macro left empty leaves its option followed by
the next one, and the run stops with a usage error such as
`error: argument -g/--group: expected one argument`. In practice `_field6_` and
`_field7_` must be filled even though the package describes them as optional,
or the parameter string must be edited to remove `-g` and `--data_dir` and let
the defaults apply.

The package defines every macro with `hide = 0`, including the password. The
console therefore shows the value of `_field3_` in clear text in the macro
editor: enable **Hide value** for it when you register the plugin, and treat
access to the plugin definition as access to the credential.

### Credentials and transport

- The bind password is passed with `-p`, so the command is visible in the shell
  history and, while the plugin runs, in the process list of the host.
- In the console the password lives in the module or plugin macro `_field3_`.
  With `hide = 0` it is not masked; enable **Hide value** and restrict who can
  read the plugin configuration.
- A plain `ldap://` connection sends the bind password and the results
  unencrypted. Prefer `ldaps://` when the directory supports it, or keep the
  traffic on a trusted network.
- The generated `agent_data` document contains metrics only: no bind DN and no
  password are written into it.

## Verify

Run the plugin manually from a terminal with the mandatory options and
`--as_agent_plugin 1`:

```bash
./pandora_ldap -s 'ldap://<TARGET_HOST>:389' -b 'cn=monitor,dc=example,dc=com' \
    -p '<PASSWORD>' -a ldap-lab --as_agent_plugin 1
```

`./pandora_ldap -h` prints the option list and the usage header, which also
reports the version of the executable.

In agent plugin mode a successful run prints one `<module>` block per module.
The excerpt below shows the shape of the output; the values depend on the
directory:

```xml
<module>
	<name><![CDATA[Response time]]></name>
	<type>generic_data</type>
	<data><![CDATA[0.004]]></data>
	<description><![CDATA[response time un sec]]></description>
	<unit><![CDATA[s]]></unit>
</module>
<module>
	<name><![CDATA[active operations]]></name>
	<type>generic_data</type>
	<data><![CDATA[3]]></data>
	<description><![CDATA[Number of active operations]]></description>
</module>
```

In data file mode the run prints `1` and writes
`<data_dir>/<agent_name>.<epoch>.data`, where `<epoch>` is the number of seconds
of the run. In Tentacle mode the run also prints `1`, and the document is sent
to the configured Tentacle server.

**Before relying on this output, check the version limitation in
[Operate and troubleshoot](#operate-and-troubleshoot).** With the current
package, a run against a directory that returns only the attributes the plugin
requests ends with a `KeyError` before any module is delivered, in every
delivery path.

<!-- SCREENSHOT NEEDED: The LDAP agent and its modules in the Pandora FMS console after a successful run. -->

## Understand the results

### Agent generated

Data file and Tentacle delivery create one agent, named after `-a`:

| Property | Value |
|----------|-------|
| Name and alias | The `-a` value |
| Description | `Ldap metrics` |
| Group | The `-g` value, `ldap` by default |
| Address | Empty |
| Operating system and version | Empty |
| Interval | Empty: the plugin does not set one |
| Timestamp | Local time of the run, in `YYYY/MM/DD HH:MM:SS` form |

Agent plugin mode creates no agent: the modules belong to the Pandora FMS agent
that executes the plugin.

### Modules generated

The plugin always builds four fixed modules and adds the modules derived from
the monitor subtree:

- **Response time.** Seconds the bind took. The timer covers the bind only, not
  the search, so this module is not a measure of the whole run.
- **Total operation counters.** `active operations`,
  `operations/sec` and `authentications/sec` come from the aggregate
  `cn=Operations,cn=Monitor` entry and from its `Bind` child:
  `active operations` is the difference between the initiated and the
  completed totals, while the two `/sec` modules receive the cumulative totals
  as incremental modules, so Pandora FMS derives the rate between samples.
- **Connection and statistic counters.** One module per monitor entry that
  carries a `monitorCounter` value, renamed from the entry DN: connection
  counters, statistics and waiters.
- **Operation counters per type.** For every operation entry, one
  `<operation>initiated` module and one `<operation>completed` module.

`-m` prefixes every module name of the run. Names are built by concatenating
the prefix, the name and, for operation modules, the `initiated` or `completed`
suffix without a space, so the names are `Bind operationsinitiated` and
`Bind operationscompleted`, not `Bind operations initiated`.

The friendly counter names come from the entry DN, not from the attribute
value: every entry whose DN contains `Current` is published as
`Current connections`, including entries that describe something else. When two
entries of the monitor tree collapse into the same name, the last one read
wins and the other value is lost. An entry whose DN matches none of the
keywords keeps its full DN as the module name.

The complete name list, including the DN keyword that produces each name, is in
[Generated modules](#generated-modules).

## Operate and troubleshoot

- Run the plugin periodically from the plugin server, or from a Pandora FMS
  agent in agent plugin mode. Each run queries the directory once; there is no
  cache and no state to reset.
- In data file mode the file name includes the epoch second of the run. Two
  runs of the same agent within the same second collide: the second run reports
  `ERROR - Could not write file: [Errno 17] File exists: ... please check directory permissions`
  and exits with status 1. The message names permissions but the actual cause is
  the existing file.
- In Tentacle mode the plugin prints `1` and exits with status 0 even when the
  client fails. The failure appears on standard error as `Tentacle error`, and
  the data file is kept instead of being removed, so it can be sent again.
- **`KeyError: 'cn=Operations,cn=Monitor'` and no output.** This is the
  limitation of the current package. The plugin searches `cn=Monitor`
  requesting only the `monitorCounter` attribute, while the totals and the
  per-type operation modules are built from `monitorOpInitiated` and
  `monitorOpCompleted`. A directory returns only the attributes that were
  requested, so those values are empty and the run stops before building or
  delivering any module. The plugin has no option that changes the requested
  attributes, and the run exits with status 1.
- **`Your username or password is incorrect.`** The bind was rejected. The
  plugin prints the message and exits with status 0, and delivers nothing, so a
  scheduler may report the run as successful. Check the bind DN, the password
  and the account state.
- **`AttributeError: type object 'LDAPError' has no attribute 'message'` in a
  traceback.** The bind failed for a reason other than invalid credentials, for
  example an unreachable server or a refused connection, and the error handler
  itself fails. Exit status is 1. Check that the host resolves the URL of `-s`
  and that the LDAP listener is reachable.
- **`error: argument -g/--group: expected one argument`** or the same message
  for `--data_dir`: the macro that feeds the option is empty in the console
  parameter string. Fill it, or edit the parameter string.
- **`JSONDecodeError` while reading the monitor tree.** A `monitorCounter` or
  operation value is not numeric, and the plugin cannot parse it. Check the
  entry the traceback names.
- **A module is missing or reports the value of a different counter.** Several
  monitor entries can share a DN keyword and therefore a module name. See
  [Modules generated](#modules-generated).

## Reference

### Command-line options

```text
pandora_ldap -s <server> -b <binddn> -p <password> -a <agent> [options]
```

| Option | Default | Required | Description |
|--------|---------|----------|-------------|
| `-s`, `--server` | — | Yes | LDAP URL with scheme and port, for example `ldap://<TARGET_HOST>:389` or `ldaps://<TARGET_HOST>:636` |
| `-b`, `--binddn` | — | Yes | DN of the account that binds to the directory |
| `-p`, `--password` | — | Yes | Password of the bind account |
| `-a`, `--agent` | — | Yes | Name of the agent created or updated by the document |
| `--as_agent_plugin` | `0` | No | `1` prints the module XML on standard output; any other integer writes the data file |
| `--tentacle_address` | none | No | Tentacle server address. When set, delivery uses Tentacle and overrides `--as_agent_plugin` |
| `--tentacle_port` | `41121` | No | Tentacle server port, used only with `--tentacle_address` |
| `-m`, `--module_prefix` | empty | No | Text prepended to every module name. Not exposed as a console macro |
| `-g`, `--group` | `ldap` | No | Destination group of the generated agent |
| `--data_dir` | `/var/spool/pandora/data_in/` | No | Directory where the data file is written |
| `-h`, `--help` | — | No | Prints the usage and stops |

### Console macros

The package registers seven macros. All of them are single-line text values.

| Macro | Option | Type | Default in package | Required | Hidden | Description |
|-------|--------|------|--------------------|----------|--------|-------------|
| `_field1_` | `-s` | text | empty | Yes | No | LDAP URL with the port |
| `_field2_` | `-b` | text | empty | Yes | No | Bind DN |
| `_field3_` | `-p` | text | empty | Yes | No | Bind password. The package sets `hide = 0`; enable **Hide value** |
| `_field4_` | `-a` | text | empty | Yes | No | Agent name |
| `_field5_` | `--as_agent_plugin` | text | `0` | No | No | `0` writes the data file; `1` prints the module XML |
| `_field6_` | `-g` | text | empty | No | No | Destination group. In practice it must be filled: see below |
| `_field7_` | `--data_dir` | text | empty | No | No | Data directory. In practice it must be filled: see below |

The parameter string always passes `-g _field6_` and `--data_dir _field7_`. An
empty value for either macro leaves the option without a value, and the run
stops with `error: argument ...: expected one argument`. Fill both macros, or
remove the options from the parameter string and let the executable defaults
(`ldap` and `/var/spool/pandora/data_in/`) apply.

`-m`, `--tentacle_address` and `--tentacle_port` have no macro in the package;
they are available only when the plugin runs from the command line or when the
parameter string is edited.

### Generated modules

`<prefix>` is the `-m` value. `<DN>` is a monitor entry DN that matches none of
the keywords.

| Module name | Type | Source |
|-------------|------|--------|
| `<prefix>Response time` | `generic_data`, unit `s` | Duration of the bind |
| `<prefix>active operations` | `generic_data` | Aggregate `cn=Operations,cn=Monitor`: initiated minus completed |
| `<prefix>operations/sec` | `generic_data_inc` | Aggregate `cn=Operations,cn=Monitor`: initiated total |
| `<prefix>authentications/sec` | `generic_data_inc` | `Bind` entry: initiated total |
| `<prefix>Max Descriptor connections` | `generic_data` | Any `monitorCounter` entry whose DN contains `Max` |
| `<prefix>Total connections` | `generic_data` | Any `monitorCounter` entry whose DN contains `Total` |
| `<prefix>Current connections` | `generic_data` | Any `monitorCounter` entry whose DN contains `Current` |
| `<prefix>Bytes statics` | `generic_data` | Any `monitorCounter` entry whose DN contains `Bytes` |
| `<prefix>PDU statics` | `generic_data` | Any `monitorCounter` entry whose DN contains `PDU` |
| `<prefix>Entries statics` | `generic_data` | Any `monitorCounter` entry whose DN contains `Entries` |
| `<prefix>Referrals statics` | `generic_data` | Any `monitorCounter` entry whose DN contains `Referrals` |
| `<prefix>Read waiters` | `generic_data` | Any `monitorCounter` entry whose DN contains `Read` |
| `<prefix>Write waiters` | `generic_data` | Any `monitorCounter` entry whose DN contains `Write` |
| `<prefix><DN>` | `generic_data` | A `monitorCounter` entry that matches none of the keywords |
| `<prefix><operation>initiated` | `generic_data` | `monitorOpInitiated` of an operation entry |
| `<prefix><operation>completed` | `generic_data` | `monitorOpCompleted` of an operation entry |

The operation entries are renamed from their DN with these names, in this
order of evaluation:

| DN contains | `<operation>` |
|-------------|---------------|
| `Bind` | `Bind operations` |
| `Unbind` | `Unbind Operations` |
| `Search` | `Search operations` |
| `Compare` | `Compare operations` |
| `Modify` | `Modify operations` |
| `Modrdn` | `Modrdn` |
| `Add` | `Add operations` |
| `Delete` | `Delete operations` |
| `Abandon` | `Abandon operations` |
| `Extended` | `Extended operations` |
| none of them | The full DN, for example `cn=Operations,cn=Monitor` |

The suffix is appended without a space: `Bind operationsinitiated`,
`Bind operationscompleted`, `cn=Operations,cn=Monitorinitiated`.

### Output file

In data file and Tentacle modes the plugin writes one file per run:

```text
<data_dir>/<agent_name>.<epoch>.data
```

The file contains an `agent_data` document with the attributes of
[Agent generated](#agent-generated) and one `<module>` block per module. The
plugin creates the file exclusively: a second run for the same agent within the
same second fails instead of overwriting the first file. In Tentacle mode the
file is removed after a successful transfer and kept when the transfer fails.

### Addon identity

| Property | Value |
|----------|-------|
| Marketplace identifier | `pandorafms.pandoraldap` |
| Name | Pandora LDAP |
| Version | `1.1` |
| Version reported by the plugin help | `050821` |
| License | One |
| Availability | Download limited to licensed users |
| Marketplace last update | 2025-10-01 |
| Author (Marketplace) | Pandora FMS |
