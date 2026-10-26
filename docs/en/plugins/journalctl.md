# Journalctl plugin

*Article last updated: 2026-10-26.*

## What it does

The Journalctl plugin forwards the systemd journal of a Linux host to Pandora
FMS. On every run it asks `journalctl` for the entries written since the
previous run, filters them with regular expressions and prints them as Pandora
FMS log entries on standard output.

It is an **agent plugin**: the Pandora FMS agent runs it as one of its
`module_plugin` lines, at every agent interval, and appends the entries it
prints to its own data. The plugin creates no agent, opens no network
connection and needs no credential: it only reads the journal of the machine
where it runs.

Collection is incremental. The plugin keeps the time of its last successful run
in a single file under `/tmp` and asks for the journal written after that
moment, so each run delivers the new entries instead of the whole journal. A
regular expression narrows what is delivered, either by keeping only the lines
that match or by dropping the ones that match.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.journalctl`, version `1.0` | Documented target | The version of the Marketplace package `pandorafms.journalctl.1.0.zip`. See [Addon identity](#addon-identity) |
| A Linux host with systemd and `journalctl` in the `PATH` | `Required` | `journalctl` is the only data source of the plugin: when the command is not available the run ends with an error and prints no entries |
| An account allowed to read the journal | `Required` | The plugin reads the journal through `journalctl` with the permissions of the account that runs the agent; when the journal cannot be read the command fails and the run ends with an error |
| A Pandora FMS agent installed on the monitored host | `Required` | The plugin is executed by the agent and its output is consumed as agent plugin output |
| Pandora FMS NG 784 and later | `Not validated` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions. It is a general Marketplace statement, not a statement specific to this addon, so it is not enough for `Supported` |
| Individual Linux distributions and versions | `Not validated` | No distribution or version matrix is recorded for this addon |

The plugin runs on the monitored host itself: it reports the journal of that
host only, and it has no remote execution mode and no connection to another
system.

### Requirements

1. **systemd, with the `journalctl` command available in the `PATH` of the
   account that runs the agent.** The plugin has no fallback: without the
   command there is nothing to read.
2. **Journal read access for that account.** The agent runs the plugin as its
   own user and the plugin does not elevate privileges. Grant that user the
   journal read access of your distribution — commonly through the
   `systemd-journal` group — or run the agent under an account that already has
   it. When the account cannot read the journal, `journalctl` fails and the run
   aborts.
3. **A writable `/tmp`.** The plugin checks it at the start of every run and
   aborts when it cannot write there, because it keeps its collection position
   in `/tmp/journalctl_logs.index`.
4. **A Pandora FMS agent on the host.** The agent is what turns the printed
   entries into log data in the console.
5. **A Marketplace account with a licence.** The download of this addon is
   limited to licensed users.

### Install the plugin

Download the package from the Marketplace entry:

[https://marketplace.pandorafms.com/entries/pandorafms.journalctl](https://marketplace.pandorafms.com/entries/pandorafms.journalctl)

The package distributes the `grep_journalctl` executable — that is the file
name, not the addon identifier — and no configuration file. Copy it to the
plugins directory of the agent and make it executable. On a Linux agent the
plugins directory is `/usr/share/pandora_agent/plugins`, which is also reachable
as `/etc/pandora/plugins`:

```bash
cp grep_journalctl /usr/share/pandora_agent/plugins/
chmod 755 /usr/share/pandora_agent/plugins/grep_journalctl
```

The agent adds its plugins directory to the `PATH`, so the bare executable name
is enough in the `module_plugin` line. An absolute path also works and is the
safer choice when more than one copy of the file exists.

Instead of copying the file by hand, the agent can distribute it to its hosts
as a file collection; the destination is the same plugins directory.

## Configure

### Add the plugin to the agent

The plugin is configured in the agent configuration file (`pandora_agent.conf`)
as one `module_plugin` line. Without options it delivers every new journal line
of the host:

```apache
module_plugin grep_journalctl
```

The line runs once per agent interval, so the coverage of each run is the time
elapsed since the previous run. Restart or reload the agent after editing the
file.

Narrow the delivery with an inclusion filter, and name the source that will
group the entries in the console:

```apache
module_plugin grep_journalctl -in 'Failed password|authentication failure' -s AuthErrors
```

Or drop the lines you do not want and keep everything else:

```apache
module_plugin grep_journalctl -out 'session opened|session closed' -s SystemLog
```

A single `module_plugin` line per host is enough: see
[One collection position per host](#one-collection-position-per-host) before
adding a second one.

To bound the duration of the run, use the block form and add a module timeout.
The block needs no `module_name`: the plugin prints its own entries and the
agent appends them unchanged.

```apache
module_begin
module_plugin grep_journalctl -in 'error|critical' -s SystemErrors
module_timeout 120
module_end
```

The single-line form has no timeout, which means a run that reads a long
backlog can last longer than the agent interval. `module_timeout` is expressed
in seconds and applies to that line only.

When the agent reads its configuration from the console (remote configuration),
the `module_plugin` line belongs to the agent configuration stored there, and a
local edit of `pandora_agent.conf` is overwritten by the agent.

### Quote the patterns

The agent executes the `module_plugin` line through a shell, before the plugin
sees it. A pattern that contains characters such as `|`, `(`, `)`, `$`, `*` or
`&` must be quoted, or the shell interprets it and the plugin receives something
else:

```apache
module_plugin grep_journalctl -in 'Failed password|authentication failure'
```

Use single quotes: they protect every character except a single quote of its
own. Double quotes also work, but the shell still expands `$` inside them, so a
pattern such as `end$` must be written with single quotes.

### Choose the source

`-s` / `--source` sets the source name that the console uses to group the
entries of this line. The default is `Journalctl`, with a capital J. Always set
a non-empty value: an empty `-s ''` is accepted and produces entries with an
empty source, which makes them hard to find and to tell apart.

Changing the source does not reset the collection position. Entries delivered
before the change stay under the previous source, and new entries appear under
the new one, so a renamed source looks like a new journal in the console.

### Filter the lines

Both filters take a regular expression that is searched anywhere in the line.
They are optional and only one of them can act:

- **`-in` / `--regex_in`** keeps only the lines that match.
- **`-out` / `--regex_out`** drops the lines that match.

When both are given, `-in` wins and `-out` is ignored without any warning. An
empty value (`-in ''`) counts as absent, so it does not filter anything.

Matching rules:

- The expression is a search, not a full-line match: `error` matches any line
  that contains `error`.
- Matching is case-sensitive unless the pattern turns it off with `(?i)`:
  `-in '(?i)error'` matches `ERROR` and `Error`.
- The whole journal line is matched, including the date, the host name and the
  unit prefix that `journalctl` writes in its default output format. A pattern
  anchored with `^` therefore sees the timestamp, not the message text: `^error`
  matches almost nothing, while `: error` or `(?i)error` work as expected.
- Each physical line is matched and delivered separately. An entry whose
  message spans several lines arrives as several entries, and a pattern cannot
  match across them.
- A pattern that is not a valid regular expression aborts the run before the
  journal is read, with an error message and exit status `1`.

The filter acts on the collected lines, after the collection position has
advanced: a line that the filter drops is not delivered later and is never
reconsidered. Changing the pattern does not replay the past.

## Verify

Run the plugin by hand before wiring it into the agent. From the plugins
directory:

```bash
./grep_journalctl
```

Each run executes once and exits. A successful run prints one `<log_module>`
block per delivered line on standard output, and writes the collection position
to `/tmp/journalctl_logs.index`:

```xml
<log_module>
	<source><![CDATA[Journalctl]]></source>
	<data>"Tm92IDExIDEyOjUzOjAyIGhvc3QwMSBzc2hkWzEzODJdOiBGYWlsZWQgcGFzc3dvcmQgZm9yIGludmFsaWQgdXNlciBhZG1pbiBmcm9tIDE5Mi4wLjIuMTA="</data>
	<encoding>base64</encoding>
</log_module>

<log_module>
	<source><![CDATA[Journalctl]]></source>
	<data>"Tm92IDExIDEyOjUzOjAzIGhvc3QwMSBzeXN0ZW1kWzFdOiBTdGFydGVkIFNlc3Npb24gNDIgb2YgdXNlciBtb25pdG9yaW5nLg=="</data>
	<encoding>base64</encoding>
</log_module>
```

The value of `<data>` is the journal line encoded in Base64, between double
quotes. Decode it to confirm what was captured:

```bash
printf 'Tm92IDExIDEyOjUzOjAzIGhvc3QwMSBzeXN0ZW1kWzFdOiBTdGFydGVkIFNlc3Npb24gNDIgb2YgdXNlciBtb25pdG9yaW5nLg==' | base64 -d
```

```
Nov 11 12:53:03 host01 systemd[1]: Started Session 42 of user monitoring.
```

Run the same command again immediately. When no journal line was written in
between, the run prints nothing on standard output, prints `No new logs.` on
standard error and exits with status `0`:

```
19:51:45 [INFO] No new logs.
```

The collection position that was written by the successful run can be read
directly:

```bash
cat /tmp/journalctl_logs.index
```

```
2026-10-26 19:51:45
```

A manual run behaves exactly like an agent run, including the advance of that
file. Use it to install, to test patterns and to diagnose, and take it into
account when the agent is already running the same plugin on that host (see
[Everyday operation](#everyday-operation)).

Once the `module_plugin` line is in place and the agent has run it, the entries
appear in the console log viewer under the agent that runs the plugin and the
source you configured:

<!-- SCREENSHOT NEEDED: Pandora FMS log viewer filtered by the agent that runs the plugin and by the source Journalctl, listing several journal entries, with no real customer data. -->

## Understand the results

### Log entries

Each delivered journal line becomes one `log_module` entry with three fields:

| Field | Content |
| --- | --- |
| `source` | The value of `-s` / `--source`, verbatim. The console groups the entries by this name. Default `Journalctl` |
| `data` | The journal line encoded in Base64, between double quotes |
| `encoding` | Always `base64` |

Base64 is what keeps the generated XML valid: the journal can contain angle
brackets, quotes and control characters, and the encoding carries them without
breaking the document. The console decodes the value, so the log viewer shows
the original line.

The plugin sends no module with a numeric value, no availability check and no
alert template: log entries are its only output. Nothing appears in the
monitoring views of the agent as a graph or as a status, so any alerting is
configured in the console on top of the log data.

### What the agent does with the output

- The agent appends the plugin output to the data it sends to the server, so
  the `<log_module>` blocks reach Pandora FMS unchanged.
- **When the plugin exits with a status other than `0`, the agent discards its
  entire output** and records the error code in its own log. A run that fails
  after printing part of its entries delivers none of them.
- The agent sends the standard error of a plugin to `/dev/null`. Every
  diagnostic of this plugin — the regex error, the `journalctl` failure, the
  missing `/tmp` permission, the `No new logs.` notice and the `-v` line — is
  therefore invisible in a scheduled run. Run the command by hand to read it.

### Coverage and the collection position

The plugin stores one timestamp, in the format `YYYY-MM-DD HH:MM:SS`, in
`/tmp/journalctl_logs.index`. Each run asks `journalctl` for the entries since
that moment:

```text
journalctl --since "<stored timestamp>" --no-pager
```

The window of a run therefore starts where the previous successful run ended
and finishes when the current run writes its own timestamp. That position is
written at the very end of the run and only when the run completes. Three
consequences follow, and they are worth knowing before you rely on the log for
auditing:

- **The run covers everything since the last completed run.** This includes
  entries written while the plugin was stopped, so a host whose agent was down
  for a day delivers a day of journal in the first run after it starts. There
  is no line limit: the whole window is read into memory and printed one entry
  per line.
- **A run that fails does not advance the position.** Nothing is lost, but the
  next successful run repeats the same window, so entries can be delivered
  twice: after a failed `journalctl`, after an invalid regular expression, and
  after a run interrupted with `Ctrl+C` or killed before it finishes.
- **A small part of the window is never delivered.** The position is the time
  at the end of the run, while the journal was read earlier in the same run.
  Entries written between the read and the write of the timestamp are older
  than the stored position when the next run starts, so they are skipped. The
  gap is short, but it exists.

Two smaller effects of the same design:

- The timestamp has a resolution of one second and the query includes the
  entries written in that exact second, so a line written in the same second in
  which the previous run ended can be delivered twice.
- The timestamp carries no time zone and `journalctl` reads it in the local
  time of the host. If the host changes its time zone or crosses a
  daylight-saving transition, the window between two runs shifts accordingly.

### One collection position per host

The file name is fixed: every execution of the plugin on the same host uses
`/tmp/journalctl_logs.index`, whatever source, filter or account it uses. There
is no per-module or per-source state.

- Two `module_plugin` lines on the same host share the position. The second
  line finds an almost empty window, because the first one already consumed it,
  and each of them receives an arbitrary part of the journal. Do not run two
  lines: keep one and use `-in` to select what you need.
- A manual run and the scheduled run share it too, so a manual run consumes the
  window that the agent would have delivered.

!!! warning "The position file lives in a shared directory"
    `/tmp` is world-writable and the file name is fixed, so any local account
    can create that file first, replace it, or turn it into a symbolic link. The
    plugin writes its timestamp with the privileges of the agent account, so a
    symbolic link placed there makes the run overwrite another file that this
    account can write. Run the agent with an unprivileged account where your
    installation allows it, and do not treat the content of the file as a
    tamper-proof record.

### First run

When `/tmp/journalctl_logs.index` does not exist, or its content cannot be read
or is not a valid timestamp, the run collects **the last five minutes** of the
journal. This is also what happens after a reboot that clears `/tmp`: journal
entries of the five minutes before the reboot can be delivered a second time,
because the journal may survive the reboot while the position does not.

To force that five-minute window again, delete the file:

```bash
rm -f /tmp/journalctl_logs.index
```

The next run starts from five minutes before it, whatever happened in between.

## Operate and troubleshoot

### Everyday operation

- **One line per host.** The single collection position makes a second line
  useless (see [One collection position per host](#one-collection-position-per-host)).
- **The interval sets the coverage.** The agent runs the line at the agent
  interval, and each run covers what happened since the previous one. A shorter
  interval delivers more often and in smaller batches; it does not change which
  entries are delivered.
- **Bound long runs.** After a long stop, the first run reads the whole window.
  Set `module_timeout` in a block so that a large backlog cannot delay the agent
  beyond the interval, and run the plugin by hand first to drain it.
- **Manual runs consume data.** A manual run prints the entries to your terminal
  and advances the position, so the agent does not deliver them afterwards.
  Use the manual run for installation, for trying a pattern and for diagnosis,
  and expect the next agent run to be empty.
- **`-v` only reports the position write.** The verbose mode raises the
  diagnostic level, but the only message it adds is the line that records the
  new collection position, for example
  `19:51:53 [DEBUG] Saved execution time: 2026-10-26 19:51:53 -> /tmp/journalctl_logs.index`.
  It does not report the applied filters, the number of lines read or the
  number of entries delivered.
- **Keep the patterns stable.** A filter change applies from the next run on;
  the lines already dropped are gone, and a line the new pattern would have
  kept is not recovered.

### Troubleshooting

| Symptom | Likely cause | Check |
| --- | --- | --- |
| No entries in the console, and the manual run prints nothing | The window is empty: another run (the agent, or your own earlier manual run) has already consumed it, or the filter drops everything | Run the plugin by hand with the same options, right after writing a matching test line with `logger 'test journalctl'` |
| `No new logs.` at every run | The position advances but no line passes the filter, or a second execution consumes the window first | Check the filters against real lines with `journalctl --since '10 minutes ago' --no-pager`; keep one `module_plugin` line |
| Entries appear under the wrong source | `-s` is missing (default `Journalctl`), or it was changed and the old entries stayed under their old source | Set `-s` explicitly, and look for the previous source in the log viewer |
| A pattern that works elsewhere matches nothing | The line carries `journalctl`'s date and host prefix, or the case does not match | Remove the `^` anchor, or add `(?i)` |
| `Invalid regex: ...` and no entries | The pattern is not a valid regular expression | Fix the pattern; the run stops before reading the journal, so nothing is lost |
| `Error: 'journalctl' command not found...` | `journalctl` is not installed or not in the `PATH` of the agent | Install systemd, or make sure the `PATH` of the agent includes the directory that contains `journalctl` |
| `Error executing journalctl: ...` followed by the command error | `journalctl` failed: the account cannot read the journal, or the journal is unreadable | Run `journalctl --since '5 minutes ago' --no-pager` as the agent user |
| `No write permissions for /tmp` | `/tmp` is not writable by the account that runs the plugin | Fix the permissions or the mount options of `/tmp` |
| The run ends with status `2` and a usage message | An unknown option, or an option without a value | Compare the line with [Command-line parameters](#command-line-parameters) |
| Entries disappear after a run that also failed | The exit status was not `0`, so the agent discarded the whole output | Look for the error in a manual run: the agent already turned the standard error into `/dev/null` |
| Some entries are missing between two runs | They were written while the run was in progress, or the filter dropped them | This is expected: the window ends at the moment the position is written |
| The same entries arrive twice | The previous run did not complete, the position was deleted, `/tmp` was cleared, or the two runs ended in the same second | Accept it, or use the entry timestamp in the console to identify the duplicate |

## Reference

### Command-line parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-in <regex>`, `--regex_in <regex>` | No | None (every line) | Delivers only the journal lines that match the expression. An empty value counts as absent. Takes precedence over `-out` |
| `-out <regex>`, `--regex_out <regex>` | No | None (nothing excluded) | Drops the journal lines that match the expression. Ignored when `-in` is set |
| `-s <name>`, `--source <name>` | No | `Journalctl` | Value of the `source` field of every entry. An empty value produces entries with an empty source |
| `-v`, `--verbose` | No | Off | Raises the diagnostic level. The only additional message is the one that records the new collection position |
| `-h`, `--help` | No | — | Prints the usage summary and exits with status `0` |

Values are given as `-in <value>` or `--regex_in <value>`; the forms
`-in=<value>` and `--regex_in=<value>` are also accepted. Options can be given
in any order.

The agent adds two directives of its own around the same line, in the block
form: `module_timeout <seconds>` to bound the run and `module_end` to close the
block. They belong to the agent configuration, not to the plugin.

### Output

| Situation | Standard output | Standard error | Exit status |
| --- | --- | --- | --- |
| At least one line survives the filters | One `<log_module>` block per line, each followed by a blank line | Nothing | `0` |
| The journal holds no entry in the window | Nothing | `HH:MM:SS [INFO] No new logs.` | `0` |
| Every collected line is filtered out | Nothing | Nothing | `0` |
| The regular expression is invalid | Nothing | `HH:MM:SS [ERROR] Invalid regex: <reason>` | `1` |
| `journalctl` is not available | Nothing | `HH:MM:SS [ERROR] Error: 'journalctl' command not found...` | `1` |
| `journalctl` fails | Nothing | `HH:MM:SS [ERROR] Error executing journalctl: ...` and the command error | `1` |
| `/tmp` is not writable | Nothing | `HH:MM:SS [ERROR] No write permissions for /tmp` | `1` |
| A processing error while building the entries | The entries printed so far | `HH:MM:SS [ERROR] Error processing logs: <reason>` | `1` |
| Interrupted with `Ctrl+C` during the processing | The entries printed so far | `HH:MM:SS [INFO] Execution interrupted.` | `0` |
| `-h`, `--help` | Usage summary | Nothing | `0` |
| Unknown option or missing value | Nothing | Usage message and the error | `2` |

The `HH:MM:SS` prefix is the local time of the message. Every diagnostic of the
plugin goes to standard error, and standard output carries only the entry XML.

### Collection position

| Property | Value |
| --- | --- |
| Path | `/tmp/journalctl_logs.index` |
| Content | A single line with the timestamp of the end of the last successful run, in the format `YYYY-MM-DD HH:MM:SS`, local time without a time zone |
| Written when | At the end of a run that completes, including a run whose lines were all filtered out |
| Not written when | `journalctl` fails, the regular expression is invalid, `/tmp` is not writable, or the run is interrupted |
| Read when | At the start of every run. A missing file, or a content that is not a valid timestamp, starts the window five minutes before the run |
| Scope | One file per host, shared by every execution of the plugin on that host, whatever source, filter or account |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.journalctl` |
| Name | Journalctl |
| Version | `1.0` — the version of the Marketplace package `pandorafms.journalctl.1.0.zip` |
| Category | Miscelaneus |
| License | One; the download is limited to licensed users |
| Marketplace last update | 2026-02-05 |
| Marketplace entry | [pandorafms.journalctl](https://marketplace.pandorafms.com/entries/pandorafms.journalctl) |
| Workflow | Agent plugin, executed by the Pandora FMS agent on the monitored host |
| Executable | `grep_journalctl` |
