# Active Directory

*Article last updated: 2026-10-26.*

## What it does

The Active Directory addon monitors a Microsoft Active Directory domain from Pandora FMS.
Each run reads the forest and the user accounts of the domain, runs the domain
diagnostics `dcdiag` and `repadmin`, and writes the result as Pandora FMS modules on
standard output. The Pandora FMS Windows agent that executes the addon ingests that
output, so every run updates the modules of the agent installed on the domain
controller.

The addon is an agent plugin: it takes a parameter file as its only argument, runs once,
prints one `<module>` block per result and exits. It creates no agent of its own — the
modules belong to the agent that runs it — and it stores no state between runs.

The output covers the state of the user accounts, the accounts that have not been used, the
identity of the forest, the services that Active Directory depends on, the availability
checks and the results of the domain diagnostics.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all integrations are compatible with Pandora FMS NG 784 and later versions |
| A domain controller as the host that runs the addon | `Required` | The addon runs `dcdiag` and `repadmin /showrepl` without a target server, so both act on the local computer and on its domain role |
| Windows PowerShell 5.0 or later with the Active Directory module | `Required` | The addon reads the forest and the accounts through the module's cmdlets, and this build cannot run on earlier versions of Windows PowerShell |
| `dcdiag` and `repadmin` available to the account that runs the addon | `Required` | The addon executes both tools on every run |
| A Pandora FMS Windows agent on the same host | `Required` | The agent is what ingests the modules the addon prints |
| Windows Server versions, and domain and forest functional levels | `Not validated` | No version or functional-level matrix has been recorded |
| Pandora FMS Windows agent versions | `Not validated` | No agent version matrix has been recorded for this addon |

### Requirements

1. **A Windows domain controller** that runs the Pandora FMS Windows agent. The addon
   runs `dcdiag` and `repadmin /showrepl` with no target server: they diagnose the
   local computer and its role in the domain. Run the addon on a domain controller.
2. **Windows PowerShell 5.0 or later**, with the **Active Directory module** and the
   **AD DS command-line tools** (`dcdiag`, `repadmin`). On a domain controller the role
   installs all of them. On another Windows host, install the RSAT capability that
   provides them, for example:

   ```powershell
   Add-WindowsCapability -Online -Name "Rsat.ActiveDirectory.DS-LDS.Tools~~~~0.0.1.0"
   ```

   Check that the three pieces are actually available before registering the execution:

   ```powershell
   Get-Command Get-ADForest
   dcdiag /?
   repadmin /?
   ```

3. **An account authorized to read the directory and run the diagnostics.** The addon
   has no credentials of its own: everything runs under the account that starts it — by
   default, the account of the Pandora FMS agent service. Use that account, or configure
   the agent to run under a domain account with the rights the diagnostics need. No
   official source identifies a narrower role set than the diagnostics themselves
   require.
4. **Pandora FMS** to receive the modules, reachable from the agent over its normal
   Tentacle connection.

Nothing is installed on the other domain controllers, on the member servers or on the
workstations of the domain.

### Install the addon

Download the addon from its Marketplace entry, whose download is limited to licensed
users:

[https://marketplace.pandorafms.com/entries/pandorafms-active_directory](https://marketplace.pandorafms.com/entries/pandorafms-active_directory)

Extract the package and place the `active_directory.exe` executable together with the
`adparams.txt` parameter file in a folder readable by the account that runs the agent.
The examples below use:

```text
%ProgramFiles%\Pandora_Agent\plugins\active-directory\
```

Pandora FMS can also distribute both files through a collection; see
[Place the files on the agent host](#place-the-files-on-the-agent-host).

## Configure

### The parameter file

The addon reads one parameter file, passed as its only command-line argument. The file is
plain text with `key=value` lines, and the shipped `adparams.txt` is the reference:

```ini
user=all
unused=1
spnm=0
upnm=0
tests=1
```

The file format is strict and silent about mistakes:

- Write the key and the value without spaces around `=`. `user = all` does not match the
  key and the setting is ignored.
- Write one line per key: a repeated key is read as a list of values instead of a single
  value.
- Only the text between the first `=` and the next `=` is used, so a value must not
  contain `=`.
- Comment a line with `#` at the beginning to disable it. A commented or missing key
  leaves its block disabled; a missing `user` key disables the user modules, a missing
  `unused` key the unused-account modules, a missing `tests` key the diagnostic modules.
- Do not move the file: the addon receives its path, and a wrong path is not reported as
  a file error (see [Nothing appears in the console](#nothing-appears-in-the-console)).

`user` accepts the literal `all` — one module per enabled account in the directory — or a
single account name, such as a `SamAccountName`, to report only that account. `unused`,
`spnm`, `upnm` and `tests` are switches: `1` enables the block, `0` or an empty value
disables it.

### Place the files on the agent host

Two options are equivalent once the files are on disk:

**Copy the files.** Place `active_directory.exe` and `adparams.txt` in any folder the
agent account can read — the examples use
`%ProgramFiles%\Pandora_Agent\plugins\active-directory\` — and use that path when
registering the execution.

**Distribute them with a collection.** Create a collection in the Pandora FMS console's
**Collections** section with a short name, upload the executable and the parameter file
to it, and assign the collection to the agent. The agent writes the collection files under
its installation folder, in a subfolder named after the short name, so the execution
points at `%ProgramFiles%\Pandora_Agent\collections\<COLLECTION_NAME>\`.

<!-- SCREENSHOT NEEDED: Pandora FMS console Collections section showing a collection whose Files tab contains active_directory.exe and adparams.txt. -->

### Register the execution

Pandora FMS runs the addon as an agent plugin: the agent executes the command on its
interval and parses the `<module>` blocks the command prints. Register one execution per
domain controller, each one pointing at the executable and at its own parameter file.

In the console, the execution is configured in the agent's plugin list; the same
execution appears on the host as a `module_plugin` entry in `pandora_agent.conf`:

```apache
module_begin
module_plugin "%ProgramFiles%\Pandora_Agent\plugins\active-directory\active_directory.exe" "%ProgramFiles%\Pandora_Agent\plugins\active-directory\adparams.txt"
module_timeout 300
module_end
```

Replace both paths with the ones in the collection folder when you distributed the files
that way.

`module_timeout` matters here: a run executes a full `dcdiag` pass, `repadmin /showrepl`
and, with `tests=1`, a second `dcdiag` pass with fifteen tests. Set a timeout above the
total time of those calls on your domain controller instead of relying on the agent's
default.

A `module_plugin` entry without a surrounding `module_begin`/`module_end` block runs on
every agent interval, which is `interval 300` in the shipped agent configuration. To run
the addon less often than the rest of the agent, keep the block and add
`module_absoluteinterval 1d` (or the frequency you need) inside it.

<!-- SCREENSHOT NEEDED: Agent plugin execution configuration showing the Active Directory executable path and its parameter file argument. -->

## Verify

Run the addon manually on the domain controller, from a PowerShell console, passing the
parameter file as its only argument:

```powershell
& "%ProgramFiles%\Pandora_Agent\plugins\active-directory\active_directory.exe" "%ProgramFiles%\Pandora_Agent\plugins\active-directory\adparams.txt"
```

A successful run prints the module blocks and exits. An excerpt of the output, reduced to
the forest identity, the availability checks and one service:

```xml
<module>
<name><![CDATA[AD: Schema Master]]></name>
<type><![CDATA[generic_data_string]]></type>
<data><![CDATA[dc01.example.com]]></data>
<description>Schema Master in Active Directory</description>
</module>
<module>
<name><![CDATA[CONNECTIVITY]]></name>
<type><![CDATA[generic_proc]]></type>
<data><![CDATA[1]]></data>
<description>Active Directory connectivity</description>
</module>
<module>
<name><![CDATA[AD: Service NTDS]]></name>
<type><![CDATA[generic_proc]]></type>
<data><![CDATA[1]]></data>
<description>Active Directory related services status. OK if Running</description>
</module>
```

Run with no arguments, the executable prints its usage summary — the plugin name, the
`active_directory.exe [config_file]` form and a pointer to the configuration file — and
stops without generating modules. There are no options: the first argument is always
taken as the configuration file, including `-h`.

Then check the agent: after the next run, its modules include the ones above plus the
per-user, unused-account and diagnostic groups. If the console shows none of them, see
[Nothing appears in the console](#nothing-appears-in-the-console).

<!-- SCREENSHOT NEEDED: Agent module list in the Pandora FMS console showing the modules generated by the Active Directory addon. -->

## Understand the results

The addon groups its modules by what they describe:

- **User state.** With `user=all`, every enabled account of the directory produces an
  `AD User <account>` module whose value is `Enabled: <account>`. Disabled accounts get no
  module. With a single account name, one module with that name reports `True` or
  `False`.
- **Unused accounts.** With `unused=1`, one `Unused AD User <account>` module per account
  that is not a critical system object and is disabled, has an expired password, has never
  logged on, or has not logged on for more than 60 days.
- **Forest identity.** `AD: Schema Master`, `AD: Root Domain`, `AD: Forest Domains` and
  `AD: Global Catalogs` are always produced from the forest. The last two are multi-line
  values when the forest has several domains or several global catalogs. With `spnm=1`
  and `upnm=1` the addon adds a block per SPN and UPN suffix.
- **Services.** One `AD: Service <service>` module per service the addon checks: `DNS`,
  `DFSR`, `IsmServ`, `Kdc`, `NetLogon` and `NTDS`. The value is `1` while the service is
  running and `0` otherwise.
- **Availability.** `CONNECTIVITY` and `Replication admin` accompany the `dcdiag` and
  `repadmin` calls; read the limitation below before using them as a check.
- **Diagnostics.** With `tests=1`, one `AD: Test <test>` module for each test `dcdiag`
  reports as started, except `Connectivity`. The value is `1` when the test passed and `0`
  when it ran and failed.

Two behaviours need attention before you rely on these modules. First, `CONNECTIVITY` and
`Replication admin` report `1` on every run of this version, whatever the diagnostics
return; see
[Known limitation: connectivity and replication always report 1](#known-limitation-connectivity-and-replication-always-report-1).
Second, all SPN suffixes share one module name, and so do all UPN suffixes: the console
keeps a single module per name, so read the run output when you need to see each suffix.

## Operate and troubleshoot

### Execution cost and scheduling

Every run starts two external diagnostics, and with `tests=1` a third one. On a healthy
domain controller they complete in seconds to minutes depending on the size of the
directory and the number of replication partners; set `module_timeout` accordingly. The
addon keeps no state, so a manual run at any time is equivalent to a scheduled one.

With `user=all` the addon queries every account of the directory individually, so the run
time grows with the number of accounts. In a large directory, schedule the addon less
often than the agent interval and raise the timeout.

### Known limitation: connectivity and replication always report 1

`CONNECTIVITY` and `Replication admin` report `1` on every run of this version: the
condition that evaluates the `dcdiag` and `repadmin` output is always true, so a failed
connectivity test or a broken replication status is not reflected in the module. Treat
those two modules as a run marker, not as an availability check, and use the
`AD: Test <test>` modules and the `dcdiag` and `repadmin` output for the actual state of
the domain.

### Nothing appears in the console

- **Wrong parameter file path.** The addon does not report an unreadable file: the keys
  resolve to empty values, the user, unused-account and diagnostic blocks stay disabled,
  and the run still prints the forest and service modules. Check the path in the
  `module_plugin` line or in the console execution.
- **The execution is not registered on the agent.** The addon prints nothing until the
  agent runs it, and the agent ignores output it cannot parse. Run the command manually
  first, then check the agent log for the execution.
- **The agent account cannot read the executable or the parameter file.** Copy both files
  to a folder the account can read, or assign the collection to the agent.

### A service module is missing

When a service is not installed on the host, the addon writes an error for it and omits
that module — no `0` value is reported. If a service module is missing while you expect
the service to exist, run `Get-Service <service>` on the host: the module follows the
presence of the service, not only its state.

### The parameter file does not take effect

Most configuration problems come from the file syntax: spaces around `=`, several lines
for the same key, or a value that contains `=`. Rewrite the affected line as `key=value`
and run the addon manually to confirm the new modules appear.

With a single account name in `user`, the addon writes a literal `\n` after the `<module>`
and `</module>` tags of its block, so that block is not clean XML. If the module of a
single account does not appear in the console while `user=all` works, use `user=all` and
filter in the console, or keep a separate parameter file per account and check the run
output first.

### No diagnostic test modules

- With `tests` empty or `0`, the diagnostic block is disabled by design: set `tests=1`.
- The addon creates a module only for a test that `dcdiag` reports as started, and reads
  the result in English or Spanish. When the operating system or `dcdiag` runs in another
  language, no test names are found and no `AD: Test <test>` modules are produced.
- Run the same `dcdiag` command manually (see [Diagnostics executed](#diagnostics-executed))
  and read its output: an error about an unknown test, or a test that never starts, ends
  in a missing module rather than in a `0`.

## Reference

### Parameter file

Passed as the only command-line argument: the file is required, every key inside it is
optional. `key=value` lines, no spaces around `=`.

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `user` | No | `all` in the shipped file | `all` produces one `AD User <account>` module per enabled account. Any other value is read as a single account name and produces one module with that name. Comment the line to disable the user block. |
| `unused` | No | `1` in the shipped file | `1` produces one `Unused AD User <account>` module per unused account. Any other value, or a missing key, disables the block. |
| `spnm` | No | `0` in the shipped file | `1` produces one `AD SPN Suffixes` block per SPN suffix of the forest. Any other value disables the block. |
| `upnm` | No | `0` in the shipped file | `1` produces one `AD UPN Suffixes` block per UPN suffix of the forest. Any other value disables the block. |
| `tests` | No | `1` in the shipped file | `1` runs the named `dcdiag` tests and produces one `AD: Test <test>` module per started test. Any other value disables the block. |

Only the first value segment is read: text after a second `=` is discarded. A key that
appears more than once is read as several values.

### Command line

```text
active_directory.exe [config_file]
```

| Condition | Behavior |
| --- | --- |
| No argument | Prints the usage summary and stops without generating modules |
| One argument | Reads it as the parameter file path |
| Any further argument | Ignored |
| An argument starting with `-`, such as `-h` | Treated as the parameter file path; there is no option parsing |
| The path does not exist | The run continues with empty values and prints only the forest, availability and service modules |

### Diagnostics executed

The addon runs these commands on every execution:

| Command | Purpose | When |
| --- | --- | --- |
| `dcdiag` | Full default test set of the local domain controller | Every run |
| `repadmin /showrepl` | Replication status of the local domain controller | Every run |

With `tests=1` it also runs:

```text
dcdiag /test:Advertising /test:FrsEvent /test:DRSRevent /test:SysVolCheck /test:KccEvent /test:KnowsOfRoleHolders /test:MachineAccount /test:NCSecDesc /test:NetLogons /test:ObjectsReplicated /test:Replications /test:RidManager /test:Services /test:Systemlog /test:VerifyReferences
```

| Test reported by `dcdiag` | Module |
| --- | --- |
| Each started test except `Connectivity` | `AD: Test <test>` |

The addon reads the results in English and Spanish.

### Generated modules

| Module name | Type | Value |
| --- | --- | --- |
| `AD User <account>` | `generic_data_string` | `Enabled: <account>` with `user=all`; `True` or `False` for a single account |
| `Unused AD User <account>` | `generic_data_string` | `<account> is not beign used` (spelled as emitted) |
| `AD: Schema Master` | `generic_data_string` | Schema master of the forest |
| `AD: Root Domain` | `generic_data_string` | Root domain of the forest |
| `AD: Forest Domains` | `generic_data_string` | Domains of the forest, one per line |
| `AD: Global Catalogs` | `generic_data_string` | Global catalog servers of the forest, one per line |
| `AD SPN Suffixes` | `generic_data_string` | One block per SPN suffix, all with this module name |
| `AD UPN Suffixes` | `generic_data_string` | One block per UPN suffix, all with this module name |
| `CONNECTIVITY` | `generic_proc` | `1` on every run of this version |
| `Replication admin` | `generic_proc` | `1` on every run of this version |
| `AD: Service <service>` | `generic_proc` | `1` while the service is running, `0` otherwise; omitted when the service is not installed |
| `AD: Test <test>` | `generic_proc` | `1` when `dcdiag` reports the test as passed, `0` when it ran and failed |

The services checked are `DNS`, `DFSR`, `IsmServ`, `Kdc`, `NetLogon` and `NTDS`.

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms-active_directory` |
| Name | Active Directory |
| Version | `1.1` |
| Package | `pandorafms-active_directory.1.1.zip` |
| License | One; the download is limited to licensed users |
| Marketplace last update | 2026-02-09 |
| Downloads | 30 |
| Author | Pandora FMS |
| Marketplace type | Miscelaneus |
| Executable | `active_directory.exe` |
| Parameter file | `adparams.txt` |
