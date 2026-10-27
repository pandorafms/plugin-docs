# Pandora UX

*Article last updated: 2026-10-26.*

## What it does

Pandora UX replays a recorded check, times it and reports the outcome to
Pandora FMS, with a screenshot of the screen or the page at the moment of
failure. The check is a web session driven through a Selenium server, a
desktop session replayed on the machine that runs the plugin, or an automation
script you already have.

Every run turns the result into Pandora FMS modules: a status module per check
and phase, a latency module per check and phase, and an image module when a
check fails. Desktop checks also keep a reference image of the correct result
and compare every run against it.

The execution mode is chosen by the value of `-exe`, matched as a
case-insensitive substring:

| `-exe` value | Mode | What is replayed |
| --- | --- | --- |
| `PWR` | Web checks | A Selenium IDE suite, in the `.side` format or in the legacy `.html` format |
| `goliat` | Web checks with Pandora Webserver | A Goliat task file. Linux only |
| `stats` | Web performance | One or more URLs timed with `curl` |
| Any other value | Desktop or third-party automation | A SikuliX project through `pdr.cmd`, or any executable with `-args` |

Because the mode is a substring match, a utility whose path contains `pwr`,
`goliat` or `stats` selects the internal mode instead of running your binary.

The plugin delivers its modules in two ways:

- **Agent plugin mode** (default): it prints the module XML on standard output
  and the Pandora FMS agent of the host ingests it.
- **Server plugin mode** (`-agent <name>`): it builds an `agent_data` document
  and delivers it through Tentacle or a local data folder.

The addon has no Discovery task: it runs from a terminal, from the Pandora FMS
agent, or as a registered server plugin.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.pandora_ux`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| A Selenium server reachable from the host, for web checks | `Required` | Web checks open a session against `-pwr_host`:`-pwr_port`, `localhost:4444` by default |
| Selenium 3 server versions | `Not validated` | The client reports a Selenium 3 server older than 3.14 as incompatible when it cannot create a session; no version matrix has been recorded for this addon |
| A Java runtime on the host, for `PDR` and for the PWR server | `Required` | `pdr.cmd` uses `JAVA_HOME`, then `java` from the path, then the standard Java runtime folders; the PWR readme asks for Java 8 |
| `curl` in `PATH`, for `stats` mode | `Required` | The plugin probes for it when it builds its help and uses it to time every URL |
| The Goliat component of Pandora FMS, for `goliat` mode | `Required` | Goliat mode loads its libraries and stops when they are missing |
| An unlocked interactive desktop session, for desktop checks | `Required` | The check captures the desktop of the session that runs the plugin |
| Operating systems | `Not validated` | The plugin help scopes PWR to Windows and Linux, PDR to Windows and Goliat to Linux; no test record exists for this version |
| Third-party automation tools used with `-exe` | `Not validated` | Any executable is accepted; no tool has been recorded as validated |
| Specific Pandora FMS versions | `Not validated` | The Marketplace banner is general to all its integrations, not a statement for this addon |

### Requirements

1. **Pandora FMS** to receive the modules: the agent installed on the host in
   agent plugin mode, or a Pandora FMS server in server plugin mode.
2. **The addon package**: the `pandora_ux_x64.exe` executable, plus the PWR
   server bundle and the PDR launcher when you use those modes.
3. **For web checks**: a Selenium server that the host can reach, a Java
   runtime for that server, and a browser it can start.
4. **For desktop checks**: a Windows host, a Java runtime and SikuliX. The
   PDR launcher in the package provides the SikuliX entry point.
5. **An interactive desktop session** on the host that runs desktop checks.
6. **`curl` on the host** when you use `stats` mode.
7. **Goliat**, from Pandora FMS, when you use `goliat` mode.

The plugin holds no credentials of its own. In agent plugin mode it needs read
access to the scripts and write access to the screenshot folder; in server
plugin mode it writes the `agent_data` file to a temporary folder and then
delivers it. Run it as the user whose desktop is checked, so the desktop
session and the capture belong to the same user.

### Install the addon

Download the package from the Pandora FMS Marketplace entry, which is limited
to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.pandora_ux](https://marketplace.pandorafms.com/entries/pandorafms.pandora_ux)

Extract it on the host that will run the checks. The executable is
`pandora_ux_x64.exe`. The package also provides the PWR server bundle and the
PDR launcher; prepare them as described below when you use those modes.

### Prepare the PWR server

Web checks need a Selenium server, on the same host or on another host that the
plugin can reach. The server does not have to share the machine with the plugin:
`-pwr_host` and `-pwr_port` point at it. On Windows the package includes a PWR
server bundle; the readme shipped with the addon documents this sequence:

1. Install a Java 8 runtime.
2. Prepare the Firefox profile that the server will use.
3. Uncompress `PWR_Server.zip` into `C:\PWR`.
4. Run `C:\PWR\server\service_installer.bat` as administrator.
5. Start the service with `net start PWRSRV`.

The installer registers a Windows service named `PWRSRV` that runs the Selenium
server with the Firefox profile in `C:\PWR\profile`. It uses the 64-bit service
wrapper from the bundle and the `java` found in `PATH`, so it needs a 64-bit
Windows and a Java runtime on the path of the account that runs it. The readme
also documents starting the server in the foreground, on port `4444`, instead
of installing it as a service.

### Prepare a desktop host

Desktop checks replay a session that interacts with the real desktop, so they
run on Windows, in an interactive session:

1. Install a Java runtime. `pdr.cmd` uses `JAVA_HOME` when it is set and
   usable, then `java` from the path, and finally `Program Files\Java\jre8`,
   `jre7` and `jre6`, including the 32-bit program folder. When it finds none it
   prints `Java not found in standard places` and stops.
2. Copy the `PDR` folder of the package to `C:\PDR`. It contains `pdr.cmd` and
   the SikuliX entry point that the launcher runs.
3. Point `-exe` at `C:\PDR\pdr.cmd` and pass `-args -r`, so the launcher
   replays the project given in `-script`.

The desktop session must stay unlocked and in the foreground: a locked session,
a disconnected remote desktop session or a machine without a logged-in user has
no desktop to capture, and the check fails.

## Configure

### Execution modes

Two decisions define a run: how the plugin delivers its modules, and which
checks it executes.

| Mode | Selected by | Modules on standard output |
| --- | --- | --- |
| Agent plugin | No `-agent` value | The module XML, ready for the Pandora FMS agent |
| Server plugin | `-agent <name>` | One line with the global status, `1` or `0`, after delivering the agent |

The minimum command line for a web check is the mode, the Selenium server and
the suite:

```bash
pandora_ux_x64.exe -exe PWR -script C:\pandora_ux\tests\std.side
```

Pass every argument as a `-flag value` pair. The parser reads the command line
as consecutive pairs, so `-flag=value` is taken as a flag named `flag=value`,
and a flag left without a value at the end is ignored.

### PWR scripts and phases

In web mode, `-script` takes one or more Selenium IDE suites separated by
commas. Each suite runs in sequence and produces its own set of modules; a
failure inside a suite stops the remaining commands of that suite but not the
following suites.

Phases come from the suite itself. Add a comment to the Selenium IDE suite to
open and close them:

```text
phase_start:Login
... recorded commands ...
phase_end:Login
```

Every phase between the markers is timed and reported on its own. A suite
without markers produces a single result for the whole suite.

Two more comments publish extra modules from the page:

```text
getValue;Cart total;generic_data;([0-9.]+) items
getScreenshot;Cart page
```

`getValue` reads the page source and publishes the first capture of the regular
expression as a module with the name and type you give. `getScreenshot` captures
the whole page and publishes it as an image module. Both run only while the
suite is still succeeding.

Two clients can talk to the Selenium server:

- The default WebDriver client drives Selenium 2 and Selenium 3 servers and
  accepts both the `.side` and the legacy `.html` suite formats. Against a
  Selenium 2 server it supports Firefox only; Chrome, Internet Explorer and Edge
  need a Selenium 3 server. In this path the comment payload is split at `:`
  and `;`, so keep those two characters out of a `getValue` expression.
- `-pwr_classic 1` uses the legacy Selenium 2 RC client. It needs a Selenium 2
  server and the legacy `.html` suite format.

With Selenium 3, name the browser plainly (`firefox`, `chrome`): the leading
`*` of the default value is removed for Firefox only. Chrome additionally
accepts `-user_data_dir` and `-profile_folder`, and `-accept_insecure_certs`
accepts any TLS certificate presented by the tested site.

### Desktop checks and reference images

In desktop mode `-script` takes one or more SikuliX projects or executables,
separated by commas, and `-folder` is the folder where the plugin keeps its
images. The folder must already exist and must end with the path separator,
because the plugin appends the file name directly.

For every phase the plugin works with three files in that folder:

| File | Role |
| --- | --- |
| `screenshot_<phase>.png` | Result image of the run. If your automation tool writes it, the plugin uses it instead of capturing the screen |
| `ctrl_screenshot_<phase>.png` | Reference image of the correct result |
| `err_screenshot_<phase>.png` | Copy of the result image of a failed run |

The first run of a phase, or any run with `-checkpoint`, rebuilds the reference
image from the result image and publishes it as a `UX_Control_Snapshot` module.
Later runs compare the result with the reference and fail when they differ by
more than `-max_differences`, which is a percentage of differing characters of
the encoded image (`0.5` by default). Because the comparison works on the
encoded image, a change of a single pixel normally changes every following
character, so treat the default as a near-exact match and refresh the reference
with `-checkpoint` when the expected result changes.

`-ss_config` selects what is captured: `active` captures the active window on
Windows; any other value, including a coordinate list such as `0,0,100,100`,
falls back to the whole screen.

The external tool is executed as
`"<utility>" <args> <script>`, so the utility path is quoted but `-args` and the
script path are not: keep the script path free of spaces. If the tool already
wrote `screenshot_<phase>.png`, that image is the result of the run.

`-k` is useful with batch and command files, which always report exit code 0:
with `-k 1` only the process exit code decides the result; without it, an exit
code 0 with `[error]` in the tool output also counts as a failure.

### Macros

`-s name=value` substitutes every `_name_` in the script before it runs:

```bash
pandora_ux_x64.exe -exe PWR -script C:\pandora_ux\tests\std.side -s today=now+1 -f "%Y%m%d"
```

`now`, `now+<days>` and `now-<days>` produce a date with the `-f` format, which
defaults to `%Y%m%d`. The plugin copies the script to a temporary folder,
applies the substitution there, executes the copy and deletes the folder
afterwards. Your original script is never modified.

The command line holds one `-s` value per run: a second `-s` replaces the first,
and so does a second `-f`. For a SikuliX project the substitution also needs the
recursive-copy support of the runtime; when it is missing the plugin exits with
status 1 before running the check, and the reason is printed only with
`-debug 1`.

### Agent plugin mode

Add the plugin to the Pandora FMS agent configuration, or to the remote
configuration of the agent in the console, as a `module_plugin` line:

```text
module_plugin C:\pandora_ux\pandora_ux_x64.exe -exe C:\PDR\pdr.cmd -args -r -script C:\PDR\checkout.sikuli -folder C:\PDR\ -checkpoint
```

The agent executes the plugin on its own interval and ingests the modules it
prints. Generated modules carry the group `UX` and no tags unless you set `-g`
and `-tag_list`.

### Server plugin mode

`-agent <name>` switches the plugin to server plugin mode. It creates an agent
with that name, holds the modules under it, and delivers the document according
to `-mode`:

| `-mode` | Behavior |
| --- | --- |
| `local` (default) | Copies the `agent_data` file into `-local_folder` |
| `tentacle` | Sends it with the Tentacle client to `-tentacle_ip`:`-tentacle_port` |

To run it from the console, register it as a server plugin:

1. Open **Servers → Plugins** and click **Register Plugin**.
2. Set a name, the plugin type **Standard**, an optional timeout and a
   description.
3. In **Plugin command**, enter the path to `pandora_ux_x64.exe` on the Pandora
   FMS server.
4. In **Plugin parameters**, use the plugin macros `_field1_`, `_field2_`, ...
   for the values that change between modules:

```text
-exe PWR -script _field1_ -pwr_host _field2_ -pwr_port _field3_ -agent _field4_ -mode local -local_folder /var/spool/pandora/data_in
```

<!-- SCREENSHOT NEEDED: Servers → Plugins registration form for Pandora UX, with the plugin command, its parameter line and the macro fields. -->

5. In **Macro parameters**, describe each field. The example uses these values:

| Field | Description | Example value |
| --- | --- | --- |
| `_field1_` | Path to the Selenium suite on the Pandora FMS server | `/opt/pandora_ux/tests/std.side` |
| `_field2_` | Host of the Selenium server | `<TARGET_HOST>` |
| `_field3_` | Port of the Selenium server | `4444` |
| `_field4_` | Name of the agent that will hold the modules | `Pandora UX checkout` |

<!-- SCREENSHOT NEEDED: Plugin module creation form with the Pandora UX plugin selected and its _field1_..._field4_ parameters filled. -->

Once registered, create a **plugin server module** on an agent, choose the
Pandora UX plugin and fill its fields. Each module execution launches one run
on the server selected for the module, so the Selenium server must be reachable
from that Pandora FMS server.

Server plugin mode is meant for checks that can run without a desktop. Desktop
checks need the interactive session of the monitored user, so they normally run
as an agent plugin on the host itself.

### Email on failure

Setting `-to` makes the plugin send a message when a phase fails. `-from`,
`-subject` and `-content` set the sender, the subject and the body; the subject
defaults to `Pandora UX test failed: ` followed by the phase name. `-smtp_gw`
and `-smtp_port` point at an SMTP relay (`127.0.0.1` and `25` by default).

The message has no authentication and no TLS options: use a relay that accepts
the host. When the failing phase has an image file, the plugin attaches it; web
checks report no file, so their message carries only the configured content.

## Verify

### A manual run

Run the plugin from a terminal with the same arguments you will schedule. A web
check with Selenium on the same host:

```bash
pandora_ux_x64.exe -exe PWR -script C:\pandora_ux\tests\std.side -debug 1
```

The run executes once and exits. The module XML goes to standard output; pass
`-debug 1` to see the progress messages on standard error, including which mode
is running and the result of the post command. `-v` is accepted but does not
change the output.

A successful single-phase web run prints the status and time modules. The
descriptions below are the ones of the default WebDriver client, which writes
`<phase> OK`; the legacy client writes `Test OK` instead.

```xml
<module>
	<name><![CDATA[UX_Status_std.side]]></name>
	<type>generic_proc</type>
	<data><![CDATA[1]]></data>
	<description><![CDATA[std.side OK]]></description>
	<module_group>UX</module_group>
</module>
<module>
	<name><![CDATA[UX_Time_std.side]]></name>
	<type>generic_data</type>
	<data><![CDATA[16.317]]></data>
	<description><![CDATA[std.side OK]]></description>
	<module_group>UX</module_group>
	<module_parent>UX_Status_std.side</module_parent>
</module>
```

A failing run reports `0` in the status module, the error text in the
description, and adds an image module with the capture of the failure:

```xml
<module>
	<name><![CDATA[UX_Snapshot_std.side]]></name>
	<type>async_string</type>
	<data><![CDATA[data:image/png;base64, iVBORw0KGgoAAAANSUhEUg...]]></data>
	<description><![CDATA[Image (last error)]]></description>
</module>
```

In server plugin mode the run prints nothing else: the last line is the global
status, `1` or `0`, and the agent appears in Pandora FMS with its modules.

### In the console

With the agent plugin configured, the modules appear in the agent of the host at
its next interval. Because names carry no host or instance prefix, one agent per
machine keeps the module tree readable, and the `UX_Status` modules are the ones
to alert on.

<!-- SCREENSHOT NEEDED: Agent module list showing a UX_Status module with its UX_Time children and the snapshot module of a failed run. -->

## Understand the results

### Status, time and images

The three families mean the same in web and desktop checks:

- `UX_Status_*` is `generic_proc`: `1` when the check or phase succeeded, `0`
  when it failed.
- `UX_Time_*` is `generic_data`: the duration in seconds.
- `UX_Snapshot_*` and `UX_Control_Snapshot_*` are `async_string` modules whose
  value is a `data:image/png;base64,` URI of the PNG.

The description of a status or time module carries the outcome: `<phase> OK`
(`Test OK` with the legacy client), the error of the Selenium command, or the
output of the automation tool.

<!-- SCREENSHOT NEEDED: Module detail of a UX_Snapshot module showing the captured image of the failure. -->

### Transaction and phase names

When a transaction name exists, the plugin also reports the transaction as a
whole and labels each phase with its position. A transaction name comes from
`-t`, or is taken from the suite name when a web suite defines more than one
phase. The label counts from `0` and reads `Phase <n>: `, so it becomes part of
the module name:

| Run | Module names |
| --- | --- |
| Web check, one suite, no phase markers, no `-t` | `UX_Status_<suite>`, `UX_Time_<suite>` |
| Web check with phase markers or `-t` | `UX_Status_Phase <n>: <transaction>.<phase>`, `UX_Time_Phase <n>: <transaction>.<phase>`, plus `UX_Global_Status_<transaction>`, `UX_Global_Time_<transaction>` and, on failure, `UX_Global_Snapshot_<transaction>` |
| Desktop check, no `-t` | `UX_Status_<phase>`, `UX_Time_<phase>`, `UX_Control_Snapshot_<phase>` and, on failure, `UX_Snapshot_<phase>` |
| Desktop check with `-t` | `UX_Status_Phase <n>: <phase>`, `UX_Time_Phase <n>: <phase>`, the phase images, plus the `UX_Global_*` modules |

`<transaction>` is the `-t` value or, in a web suite without `-t`, the suite
name. `<phase>` is the phase marker of the suite in web checks, and the `-name`
value for that position or the base name of the script in desktop checks.

Two details follow from the numbering: the global web summary is enumerated
before the phases in the WebDriver path, so the first phase is reported as
`Phase 1: `; the legacy client enumerates it last, so its numbering starts at
`0`. And the transaction prefix stays inside the phase name, which is why a web
phase appears as `Phase 1: std.side.Login` when the suite is `std.side` and the
marker is `Login`.

`UX_Global_Status_<transaction>` is `1` only when every phase succeeded, and its
description is the list of the phase outcomes. `UX_Global_Time_<transaction>` is
the total duration: the wall-clock time of the web run, or the sum of the phase
durations in desktop mode. With `-pwr_override_global_phase_time 1` a web run
uses the sum of the phases as well, and `-pwr_phases_time 1` adds a separate
`UX_Phases_Time_<transaction>` module with that sum.

### stats and Goliat results

`stats` reports timings for a URL without a browser. For each URL the tag is the
`-name` value for that position; without `-name` it is the last path segment of
the URL, or the whole URL when that segment is empty. The modules are
`<tag>_Global_Status` (`generic_proc`) and `<tag>_UX_Stats_TT`, `_DNS`, `_TTCP`,
`_TST` and `_TTC` (`generic_data`, in milliseconds), plus `_TSSL` for an
`https` URL. `Global_Status` is `1` only when `curl` returned exit code 0; the
description names the `curl` error otherwise.

`goliat` reports one `UX_Status_<task>` and one `UX_Time_<task>` module per
`task_begin` block of the task file, with the duration Goliat measured for it.
It publishes no image modules.

## Operate and troubleshoot

### Retries and the post command

`-retries` sets how many times the whole transaction is attempted; the default
is one attempt. A failed attempt is repeated in full, all phases included, not
phase by phase, and the next attempt starts from the first script. Retries apply
to web and desktop checks; `stats` and `goliat` runs execute once.

`-post` runs a command once, after the modules have been generated, whatever the
result of the check. Use it to close what the check opened:

```text
-post "taskkill /F /IM calc.exe"
```

It is not executed in `stats` mode, which ends before the report stage.

### Operating a desktop host

- Keep the agent running inside the interactive session of the monitored user,
  with the desktop unlocked. A machine at the logon screen has no desktop to
  capture.
- Start the agent automatically at boot, so a machine restart does not leave
  the checks stopped until somebody logs in.
- Reset a reference image by deleting `ctrl_screenshot_<phase>.png`, or by
  running the check once with `-checkpoint` when the expected result changes.
- Keep `-folder` on a local disk: the plugin writes and re-reads the images
  there on every run.

### Common failures

- **The plugin prints its parameter list and exits with status 1** — no
  argument, only `-h`, or a missing `-exe` or `-script`. The message mentions
  `Missing <script> in arguments` even when the missing value is `-exe`; check
  both.
- **A web run reports `0` in every status module with a connection error in the
  description** — the Selenium server is not reachable or not ready. Check
  `-pwr_host` and `-pwr_port`, the service on the server (`net start PWRSRV` on
  Windows) and the firewall between the host and the server.
- **A web run publishes nothing at all and ends with status 0** — the run had
  `-exit_on_fail 1` and could not reach the Selenium server. The option makes
  the plugin abandon the run instead of publishing a failed status, so use it
  only where an external scheduler watches the exit code.
- **A desktop run reports `Control image not found, please check directory
  permissions`** — the folder in `-folder` does not exist, does not end with the
  path separator, or is not writable by the user that runs the plugin.
- **A desktop run fails with `Error: Snapshot doesn't match the control one`
  on a check that works** — the reference image no longer matches the expected
  screen. Review the image in the `UX_Snapshot` module and refresh the reference
  with `-checkpoint`.
- **`Java not found in standard places` when a PDR run starts** — there is no
  `JAVA_HOME`, no `java` in the path and no runtime in the standard Java
  folders. Install a Java runtime or set `JAVA_HOME`.
- **No progress message appears on standard error** — the plugin writes its
  messages only with `-debug 1`. `-v` is accepted for compatibility and changes
  nothing.
- **The plugin stops with `Goliat libraries not found`** or with a message about
  the Selenium 2 RC client — the optional component of that mode is not
  available on the host. Use the WebDriver path, or install the missing
  component.
- **No mail arrives on failure** — `-to` is not set, the SMTP relay in
  `-smtp_gw`:`-smtp_port` refuses the host, or the failure happened before the
  report stage (a configuration error, for example).

## Reference

### Execution parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-exe` | Yes | — | Automation utility, or the internal mode `PDR`, `PWR`, `stats` or `goliat`. The value is matched as a case-insensitive substring |
| `-args` | No | Empty | Arguments passed to the external utility before the script path |
| `-script` | Yes | — | Comma-separated list of suites, projects, executables or URLs, one per phase |
| `-name` | No | Base name of the script | Comma-separated names that match `-script` position by position, used in the module names and, in `stats` mode, as the module prefix |
| `-folder` | No | `%TEMP%\` on Windows, `/tmp/` elsewhere | Folder for the result, reference and error images of desktop checks. Must end with the path separator. Not used by web checks |
| `-retries` | No | `1` | Number of attempts of the whole transaction, in web and desktop modes |
| `-t` | No | — | Transaction name. Enables the `UX_Global_*` modules and the `Phase <n>: ` label |
| `-k` | No | `0` | `1` uses only the process exit code; by default an exit code 0 with `[error]` in the output also fails |
| `-post` | No | — | Command executed once after the modules are generated. Not executed in `stats` mode |
| `-debug` | No | `0` | `1` prints progress messages and Selenium detail on standard error |
| `-v` | No | `0` | Accepted for compatibility. It does not change the output; use `-debug 1` |

### PWR parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-pwr_host` | No | `localhost` | Host of the Selenium server |
| `-pwr_port` | No | `4444` | Port of the Selenium server |
| `-pwr_browser` | No | `*firefox` | Browser the Selenium server starts. With Selenium 3 use the plain name (`firefox`, `chrome`) |
| `-pwr_classic` | No | `0` | `1` uses the legacy Selenium 2 RC client and the legacy `.html` suite format |
| `-pwr_phases_time` | No | `0` | `1` adds `UX_Phases_Time_<transaction>`. Requires a transaction name |
| `-pwr_override_global_phase_time` | No | Not set | `1` sets the global time module to the sum of the phase times. Requires a transaction name |
| `-accept_insecure_certs` | No | `0` | `1` accepts any TLS certificate. Selenium 3 only |
| `-pageLoadTimeout` | No | `300000` | Page load timeout in milliseconds |
| `-user_data_dir` | No | — | Chrome user data directory. Selenium 3 only |
| `-profile_folder` | No | — | Chrome profile folder inside `-user_data_dir`. Selenium 3 only |
| `-exit_on_fail` | No | `0` | `1` abandons the run when the Selenium server cannot be reached, without publishing modules and with exit status 0 |
| `-phase_snapshot` | No | `0` | `1` attaches the failure image to the failed phase in the legacy client |

### Desktop and image parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-ss_config` | No | Whole screen | `active` captures the active window on Windows. Any other value falls back to the whole screen |
| `-checkpoint` | No | `0` | Rebuilds the reference image from the current result and publishes `UX_Control_Snapshot_*` |
| `-max_differences` | No | `0.5` | Maximum percentage of differing characters between the reference and the result image |
| `-classic_mode` | No | `0` | `1` publishes the latency modules only when the check succeeded |

### Macro parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-s name=value` | No | — | Substitutes `_name_` in the script. `now`, `now+<days>` and `now-<days>` produce a date. One macro per run |
| `-f format` | No | `%Y%m%d` | Date format for the date macros. One format per run |

### Email parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-to` | No | — | Recipient of the failure notification. Without it, no mail is sent |
| `-from` | No | `pandora_ux@artica.es` | Sender of the message |
| `-subject` | No | `Pandora UX test failed: ` | Subject prefix; the phase name is appended |
| `-content` | No | Empty | Body of the message |
| `-smtp_gw` | No | `127.0.0.1` | SMTP relay |
| `-smtp_port` | No | `25` | SMTP relay port |

### Module, agent and delivery parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-agent` | No | — | Agent name. Switches the plugin to server plugin mode |
| `-agent_group` | No | Empty | Group of the agent created in server plugin mode |
| `-agent_interval` | No | `300` | Interval of the agent created in server plugin mode |
| `-interval` | No | `1` | Accepted and stored, but the generated modules are published without an interval |
| `-g` | No | `UX` | Group of the generated modules |
| `-tag_list` | No | Empty | Comma-separated tags added to the generated modules |
| `-mode` | No | `local` | `local` copies the agent document into `-local_folder`; `tentacle` sends it to `-tentacle_ip`:`-tentacle_port` |
| `-tentacle_ip` | No | `127.0.0.1` | Tentacle server address |
| `-tentacle_port` | No | `41121` | Tentacle server port |
| `-tentacle_opts` | No | Empty | Extra options passed to the Tentacle client |
| `-local_folder` | No | `/var/spool/pandora/data_in` | Destination folder in `local` mode |
| `-temp` | No | System temporary folder | Folder used to write the agent document before delivery |

When the first argument is the path of an existing file, the plugin reads it as
`key=value` lines before processing the flags, and the flags override it. The
plugin help does not list this form.

### Generated modules

| Module | Type | Mode | Meaning |
| --- | --- | --- | --- |
| `UX_Status_<phase>` | `generic_proc` | Web, desktop and Goliat | `1` when the phase succeeded, `0` when it failed |
| `UX_Time_<phase>` | `generic_data` | Web, desktop and Goliat | Duration of the phase, in seconds |
| `UX_Control_Snapshot_<phase>` | `async_string` | Desktop | Reference image rebuilt during this run |
| `UX_Snapshot_<phase>` | `async_string` | Web and desktop | Image at the moment of the failure |
| `UX_Global_Status_<transaction>` | `generic_proc` | Web and desktop with a transaction name | `1` when every phase succeeded |
| `UX_Global_Time_<transaction>` | `generic_data` | Web and desktop with a transaction name | Duration of the run, or the sum of the phases with `-pwr_override_global_phase_time 1` |
| `UX_Global_Snapshot_<transaction>` | `async_string` | Web and desktop with a transaction name | Image of the failure, or `No image available` |
| `UX_Phases_Time_<transaction>` | `generic_data` | Any mode with a transaction name and `-pwr_phases_time 1` | Sum of the phase times |
| `<tag>_Global_Status` | `generic_proc` | `stats` | `1` when `curl` completed with exit code 0 |
| `<tag>_UX_Stats_TT` | `generic_data` | `stats` | Total time of the request, in milliseconds |
| `<tag>_UX_Stats_DNS` | `generic_data` | `stats` | Name resolution time, in milliseconds |
| `<tag>_UX_Stats_TTCP` | `generic_data` | `stats` | TCP connection time, in milliseconds |
| `<tag>_UX_Stats_TSSL` | `generic_data` | `stats`, `https` URLs | TLS handshake time, in milliseconds |
| `<tag>_UX_Stats_TST` | `generic_data` | `stats` | Time to the first byte, in milliseconds |
| `<tag>_UX_Stats_TTC` | `generic_data` | `stats` | Transfer time, in milliseconds |

Modules published by the `getValue` comment keep the name and type declared in
the comment. The `Phase <n>: ` transaction label and the `<transaction>.` prefix
are part of the module name when a transaction name exists, as described in
[Transaction and phase names](#transaction-and-phase-names).

### Exit status

| Status | Meaning |
| --- | --- |
| `0` | Normal end, including a run whose modules report failures. In server plugin mode the global status is printed instead: `1` or `0` |
| `1` | The plugin printed its parameter list, or an optional component of the selected mode is missing |
| Other | An internal error stopped the process before it could report |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.pandora_ux` |
| Name | Pandora UX |
| Version | `1.0` |
| Version string printed by the plugin help | `8.0NG.805`, build `260915` |
| Category | Miscelaneus |
| License | One |
| Marketplace last update | 2025-07-02 |
| Availability | Download limited to licensed users |
