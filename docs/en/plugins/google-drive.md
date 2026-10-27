# Google Drive monitoring plugin

*Article last updated: 2026-10-26.*

## What it does

The Google Drive monitoring plugin reports how much of a Google Drive storage
quota is in use and, optionally, when one named file was last modified. Each
run reads the storage quota of the Google account that authorized the plugin,
turns the used share into a percentage and delivers one Pandora FMS agent with
that value.

The addon is a **server plugin**: the Pandora FMS Plugin Server executes it and
every run builds the agent document and delivers it to Pandora FMS through
Tentacle or into a local data directory. Nothing is installed on the Google
side, and the plugin never writes to Google Drive.

What it measures has three consequences worth stating before you configure it:

- **It reports one quota, not a file inventory.** The only modules are the
  percentage of the storage quota in use and, when you name a file, that file's
  last modification time. The plugin does not list your Drive, does not report
  per-folder sizes and does not monitor how many files are stored.
- **It is read-only.** The authorization it requests is the Google Drive
  metadata scope, `https://www.googleapis.com/auth/drive.metadata.readonly`. The
  plugin reads quota and metadata only: never file contents, and it deletes,
  moves and uploads nothing.
- **It monitors the account that authorizes it.** The quota and the named file
  belong to the Google account whose authorization is stored on the host, so one
  plugin configuration covers one Google account.

The run prints a single number, `1` or `0`, on standard output. That number is
the value a Pandora FMS plugin module receives; the quota and the file date go
to the separate agent the plugin creates.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Addon `pandorafms.googledrive`, version `1.0` | Documented target | The version this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all integrations are compatible with Pandora FMS NG 784 and later versions. This is a catalogue-wide statement covering the addon, not a test record for it |
| HTTPS access from the host that runs the plugin to the Google Drive API | `Required` | Every run calls the Drive v3 API to read the quota and the file metadata |
| A Google Cloud project with the Google Drive API enabled and an OAuth 2.0 desktop client | `Required` | The plugin authenticates with the client secret JSON of a desktop-app OAuth client |
| A Google account that can authorize the requested scope | `Required` | The quota read and the file lookup run as the authorizing account |
| Rocky Linux and Fedora 34 | `Known compatible` | The legacy guide for this addon records both as the systems where it was tested. Not re-validated for version `1.0` |
| Other Linux distributions | `Not validated` | No distribution range or version matrix has been recorded for this addon |
| `tentacle_client` in `PATH` | `Required` when `--transfer_mode` is not `local` | Tentacle delivery runs that command; the plugin has no option that changes its name |
| Write access to `/tmp` | `Required` | The generated agent XML is staged in `/tmp` before delivery; `--temporal` does not change it |
| Write access to `/var/spool/pandora/data_in/` | `Required` when `--transfer_mode local` is used | Local delivery moves the document into that directory; `--data_dir` does not change it |
| A browser session on the host that performs the first authorization | `Required` | The authorization opens a local web server and a browser. On a headless host, complete it on a machine with a browser and copy `token.json` |

No compatibility statement establishes a Google Workspace edition, a Drive plan
or a Linux distribution other than the record above. Keep each claim at the
scope its source proves.

### Google Cloud requirements

The plugin needs an OAuth client of the **desktop app** type. Prepare it once
for the project that will own the integration:

1. Open the [Google Cloud console](https://console.cloud.google.com/) and select
   or create a project.
2. In **APIs & Services → Library**, search for **Google Drive API** and enable
   it for the project.
3. In **APIs & Services → OAuth consent screen**, configure the consent screen
   and add the scope
   `https://www.googleapis.com/auth/drive.metadata.readonly`, which is the only
   scope the plugin requests.
4. In **APIs & Services → Credentials**, choose **Create credentials → OAuth
   client ID**, set the application type to **Desktop app** and download the
   JSON file. That file is the input of `--creds_json`.

While the consent screen is in **Testing** status, only the Google accounts you
add as test users can authorize the client. Add the account you want to monitor,
or publish the app, before the first run.

### Requirements

1. **A Google account to monitor.** One plugin configuration reads one account's
   quota. To monitor several accounts, run the plugin once per account with a
   different `token.json` directory and a different `--agent_prefix`.
2. **The client secret JSON** of the desktop OAuth client, readable by the user
   that runs the plugin.
3. **Pandora FMS with the Plugin Server enabled** on the server that will run the
   plugin.
4. **A delivery target**: a Tentacle server reachable at `--tentacle_address`
   and `--tentacle_port` with `tentacle_client` in `PATH`, or a writable
   `/var/spool/pandora/data_in/` directory.
5. **Write access to `/tmp`** for the user that runs the Plugin Server, where the
   agent XML is staged.
6. **A file name**, only if you want the last modification module. The file must
   be visible to the authorized account.

Authorize the plugin with the account whose storage you want to monitor: the
quota and the named file are read as that account.

### Install the plugin

Download the package from its Marketplace entry, whose download is limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.googledrive](https://marketplace.pandorafms.com/entries/pandorafms.googledrive)

Copy the `pandora_googledrive` executable to the Pandora FMS server and give it
execute permission. The recommended directory for server plugins is:

```text
/usr/share/pandora_server/util/plugin/
```

```bash
sudo chmod 755 /usr/share/pandora_server/util/plugin/pandora_googledrive
```

Nothing is installed on Google Drive, and the Google account needs no agent or
connector.

## Configure

The plugin has no configuration file. It takes every setting from the command
line, starting from built-in defaults:

```text
built-in defaults < command-line options
```

Every option is listed in [Command-line parameters](#command-line-parameters).
This section explains the decisions that change what the plugin reads and where
the result goes.

### Authorize the account

The plugin authenticates as an OAuth client and stores the authorization it
obtains in a file named `token.json`, in the **current working directory** of the
process. That relative path drives the whole authorization model:

- When `token.json` exists in the working directory, the plugin loads it and
  does not read `--creds_json` or `--creds_base64` at all. Later runs need no
  credential option.
- When `token.json` does not exist, the plugin opens the OAuth flow with the
  client secret JSON and writes `token.json` when the flow finishes. Run the
  plugin from the directory where the authorization must live, and keep that
  directory for the scheduled runs.

The first authorization is interactive: the plugin starts a local web server on
the port set by `--port` (`8080` by default) and opens a browser to complete the
Google sign-in. Consequences:

- The host needs a browser session. On a headless server, authorize on a machine
  with a browser, in a directory of your choice, and copy the resulting
  `token.json` into the working directory of the plugin on the server. The file
  holds the stored authorization for that OAuth client.
- Port `8080` must be free on the host that runs the flow. Change it with
  `--port` when another service already listens there.
- `token.json` must stay readable only by the user that runs the plugin. It
  contains a refresh token, which is a credential.

`--creds_base64` does not authenticate. The plugin decodes the value and writes
it as `cred.json`, but then opens `creds.json` for the OAuth flow:

- If `creds.json` does not exist in the working directory, the run stops with a
  `FileNotFoundError` traceback and leaves `cred.json` behind.
- If `creds.json` does exist, that file is used and the decoded value is
  discarded after a successful run.

Both outcomes are the current behavior, not a configuration mistake. Use
`--creds_json <PATH_TO_CREDENTIALS_JSON>` for the first authorization and
`token.json` afterwards.

When `token.json` is absent, exactly one credential option must be given:

| Options on the command line | Result |
|-----------------------------|--------|
| Neither `--creds_json` nor `--creds_base64` | The plugin writes a message to `--log_file`, prints `0` and exits with status `0`. No agent is generated |
| Both options | Same result: the plugin prints `0` and exits with status `0`, and the log says only one may be selected |
| `--creds_json` only | The OAuth flow starts with that client secret JSON |

### Choose the monitored file

`--file_name` selects one file and is optional. The plugin searches the Drive of
the authorized account for an **exact name match**, including the extension and
the letter case, and reads the modification date of the first match it receives.
Points to keep in mind:

- The lookup uses the Drive v3 file search with no shared-drive options, so it
  resolves files in the account's own Drive. A file that lives only in a shared
  drive is not found.
- A file name that contains a single quote cannot be queried, because the name is
  interpolated into the search expression as it is typed.
- When the name does not resolve, the plugin prints
  `Error al obtener la fecha de modificación: ...` on standard output, generates
  the agent **without** the file module, and still prints `1`. A missing module is
  therefore the visible symptom of a wrong name.
- The module name is built from the text you passed, not from the name Google
  returns, so the two normally match.

Without `--file_name`, the run makes only the quota call.

### Agent and module prefixes

`--agent_prefix` and `--module_prefix` both default to an empty string, and they
do not behave the same way:

- **`--agent_prefix`** is prepended once to the agent alias,
  `<agent_prefix>GoogleDrive`, with no space in between. Pandora FMS identifies
  the agent by a hash derived from that alias, so the same prefix always updates
  the same agent and a different prefix creates a second one.
- **`--module_prefix`** is applied twice to every module name, because the prefix
  is added when the module name is composed and again when the module is built.
  With no prefix, every module name starts with a space.

The resulting names, for `--agent_prefix PROD_ --module_prefix PROD.` and the
file `report.csv`:

| Element | Name |
|---------|------|
| Agent alias | `PROD_GoogleDrive` |
| Agent identifier | Hash derived from `PROD_GoogleDrive` (shown by the console, not typed) |
| Quota module | `PROD.PROD. Google Drive Used` |
| File module | `PROD.PROD. report.csv` |

With both prefixes left empty, the same names are ` Google Drive Used` and
` report.csv`. Write the combined name in alerts, reports and module filters, and
expect the duplication: it is the current behavior, not a rendering artifact.

### Delivery

The default is Tentacle delivery. `--transfer_mode` accepts one meaningful
value:

| Value | Behavior |
|-------|----------|
| `tentacle` (default) | Sends the XML document with `tentacle_client` to `--tentacle_address`:`--tentacle_port` |
| `local` | Moves the XML document into `/var/spool/pandora/data_in/` |
| Any other value, including a misspelling | Also uses Tentacle; the plugin only treats the exact value `local` as local delivery |

`--tentacle_address` defaults to `127.0.0.1` and `--tentacle_port` to `41121`.
Four options are accepted but not used by the delivery: `--temporal`,
`--data_dir`, `--tentacle_client` and `--tentacle_opts`. The document is always
staged in `/tmp`, local delivery always targets `/var/spool/pandora/data_in/`
and the Tentacle command is always `tentacle_client` resolved through `PATH`.
Because none of those paths is configurable, the host must provide them: the
Tentacle client in `PATH`, a writable `/tmp`, and the server's data directory at
the default location when local delivery is used.

Tentacle failures are printed on standard error, but they do not change the `1`
or `0` the plugin prints. See [Output and exit status](#output-and-exit-status).

### Register the plugin in the console

1. Open **Servers → Plugins** and click **Register Plugin**.
2. Set a name, the plugin type **Standard**, an optional maximum timeout and a
   description.
3. In **Plugin command**, enter the full path to the executable on the Pandora
   FMS server:
   `/usr/share/pandora_server/util/plugin/pandora_googledrive`.
4. In **Plugin parameters**, combine the options you need, using the plugin
   macros `_field1_`, `_field2_`, ... as placeholders:

```text
--creds_json _field1_ --agent_prefix _field2_ --interval 300 --transfer_mode tentacle --tentacle_address 127.0.0.1 --tentacle_port 41121
```

5. In **Macro parameters**, describe each field. The example uses these values:

| Field | Description | Example value |
|-------|-------------|---------------|
| `_field1_` | Path to the client secret JSON of the desktop OAuth client, readable by the Plugin Server user | `<PATH_TO_CREDENTIALS_JSON>` |
| `_field2_` | Prefix for the generated agent alias | `PROD_` |

<!-- SCREENSHOT NEEDED: Server plugin registration form in the Pandora FMS console showing the pandora_googledrive command path and the parameter fields, with lab placeholders and no real account data. -->

Add `--file_name _field3_` and `--module_prefix _field4_` only when you need
them. Every flag that remains in the parameter string must receive a value: a
blank macro leaves the flag without an argument and the plugin stops with an
argument-parsing error instead of running. Remove the flag rather than leaving
its field empty.

The credential option is only needed while `token.json` is missing from the
working directory of the Plugin Server. Once the authorization exists, the
parameter string can drop `--creds_json`.

After the server plugin is created, open an agent, create a **plugin** module
and select the registered plugin. That module receives the printed `1` or `0`.
The quota percentage and the file date do not go into that module: they arrive
in the separate agent the plugin creates.

<!-- SCREENSHOT NEEDED: Plugin module form in the Pandora FMS console with the Google Drive plugin selected and its macro fields filled, without real credentials, account names or hostnames. -->

### Security

- **The authorization is the secret.** `token.json` holds a refresh token that
  grants read-only access to the metadata of the authorized account. Restrict it
  to the plugin user (`chmod 600`) and do not copy it into tickets, images or
  repositories.
- **The client secret JSON is also a secret.** It identifies the OAuth client of
  the project. Keep it readable only by the plugin user and outside any
  directory served by a web server.
- **Both files are plain text.** Their protection is the file system permission
  model, so keep them owned by the plugin user.
- **The scope is read-only and minimal for this purpose.** The plugin requests
  `drive.metadata.readonly`, which allows reading metadata but not file
  contents. It cannot modify the Drive.
- **Do not pass a base64 credential on the command line.** The value is the
  client secret itself: it would appear in the shell history, in the operating
  system process list and in the plugin parameters stored by the console. That
  option also does not complete the authorization, as described above.
- **The first authorization opens a browser on the host.** Complete it on a
  trusted machine and copy `token.json`, rather than exposing an interactive
  session on a production server.
- **A failed authorization or quota read prints a traceback.** Those messages
  can include the Google API error text. Review them before sharing a manual
  run.

## Verify

Run the plugin manually from the directory that holds `token.json` on the
Pandora FMS server:

```bash
./pandora_googledrive \
  --file_name report.csv \
  --agent_prefix PROD_ \
  --transfer_mode tentacle \
  --tentacle_address <PANDORA_FMS_SERVER> \
  --tentacle_port 41121
```

A successful run ends with `1` on standard output. The plugin then creates or
updates the agent `PROD_GoogleDrive`, whose quota module reports the current
percentage and whose second module reports the file date. With `local` delivery,
check that a `.data` file has been moved into `/var/spool/pandora/data_in/` and
that the agent appears after the data server processes it.

The printed value alone is not enough to verify the integration:

- `1` means the quota call succeeded and the agent document was built. It does
  not prove delivery: a Tentacle failure is printed on standard error but still
  leaves `1` on standard output.
- `0` means no agent was built. The usual cause is a missing `token.json` with
  no credential option, or both credential options at once.
- A traceback with process exit status `1` means the authorization or the quota
  read failed. The `1`/`0` value is not printed at all in that case.

Verify the data, not only the output line:

1. Confirm the agent exists under the alias `<agent_prefix>GoogleDrive`.
2. Open its modules and check that the quota percentage is plausible for the
   account, and that the file module shows an ISO 8601 date.
3. If the file module is missing while the quota module reports a value, the file
   name did not resolve. Check the name and the shared-drive limitation above.

<!-- SCREENSHOT NEEDED: The generated GoogleDrive agent in the Pandora FMS console with its quota and file-date modules and current values for a lab account. -->

Use `./pandora_googledrive -h` to print the usage summary in Pandora FMS style.
The header reports `Version = 1.0`, and the summary shows the manual execution
form. The form is a schematic template: it never states which of the two
credential options to use, and `--creds_json/creds_base64` is not a valid flag
name. Pass one of the two options, as shown above.

## Understand the results

### Agent

The plugin generates a single agent. Its identity is derived from
`--agent_prefix`, so one prefix maps to one agent:

| Attribute | Value |
|-----------|-------|
| Alias | `<agent_prefix>GoogleDrive`, with no space before `GoogleDrive` |
| Identifier | Hash derived from the alias |
| Description | Empty |
| Interval | `--interval`, `300` seconds by default |
| Group | `--group`, empty by default |
| Operating system fields | Empty |
| Parent agent | None |

Running the plugin twice with the same prefix updates the same agent. Changing
the prefix creates a second agent with its own module set, which is how you
monitor two Google accounts from the same Pandora FMS installation.

### Modules

The plugin always generates the quota module, and the file module only when
`--file_name` is set and the name resolves:

| Module name | Type | Unit | Value |
|-------------|------|------|-------|
| `<module_prefix><module_prefix> Google Drive Used` | `generic_data` | `%` | Percentage of the storage quota in use, unrounded |
| `<module_prefix><module_prefix> <file_name>` | `generic_data_string` | None | Modification time Google returns for the file, as an ISO 8601 UTC string such as `2026-10-24T08:15:00.123Z` |

The quota module description is `Percentage of space used` and the file module
description is `Last change`.

The percentage is computed as the used storage divided by the storage limit,
multiplied by 100. Google reports both figures for the whole account, so the
value describes the account's storage usage against its quota, not the size of
one folder or the space taken by Drive files alone.

The file module publishes Google's timestamp string. Pandora FMS stores it as a
text value: it is not converted to a Pandora FMS timestamp, so a threshold on
that module compares strings. To detect changes, compare consecutive values or
use the module history rather than a numeric threshold.

## Operate and troubleshoot

The plugin keeps no state between runs beyond `token.json`. Every execution
reads the quota anew, so it can be run manually at any time without affecting the
Google account.

Schedule the registered plugin module at the interval you want the data
refreshed. The generated agent carries its own `--interval`, which is the
interval Pandora FMS assigns to the agent, but its values change only when the
plugin module runs. Align both.

### Output and exit status

| Result | Meaning |
|--------|---------|
| Standard output `1` | The quota was read and the agent document was built. Delivery is not guaranteed |
| Standard output `0` | No agent was built: `token.json` was absent and the credential options were missing or both were given. Process exit status `0` |
| Traceback, process exit status `1` | The authorization or the quota read raised an error. The `1`/`0` value is not printed and `--log_file` receives nothing from that failure |
| Argument-parsing error on standard error, process exit status `2` | A flag has no value, for example a blank macro field |
| `Error al obtener la fecha de modificación: ...` followed by `1` | The named file did not resolve. The agent is delivered without the file module |

### Common problems

- **The run prints `0`.** There is no `token.json` in the working directory and
  the credential options are missing or contradictory. Authorize the account, or
  run the plugin from the directory that holds `token.json`.
- **The OAuth flow restarts on every run.** The `token.json` written by the first
  authorization is not in the working directory of the current run. Remember that
  the file is resolved relative to the process working directory, not to the
  executable. Point the execution at the right directory, or move the file.
- **The run ends with a `FileNotFoundError` traceback in the authorization
  stage.** It used `--creds_base64` without a `creds.json` in the working
  directory. Use `--creds_json` for the first authorization.
- **The run ends with a `TypeError` traceback after the authorization.** The
  quota read failed, for example because the quota response does not include a
  limit, or reports a zero limit. The plugin cannot publish a percentage in that
  case, and the failure is reported only as that traceback.
- **No browser opens, or the flow waits forever.** The host has no browser
  session, or port `8080` is busy. Authorize on a machine with a browser and copy
  `token.json`, or change the port with `--port`.
- **Google refuses the authorization.** The consent screen is in **Testing**
  status and the account is not a test user, or the scope was not added to the
  consent screen. Fix it in the Google Cloud project and authorize again.
- **The run prints `1` but no agent appears.** The quota was read but delivery
  failed. Check that `tentacle_client` exists in `PATH` and can reach
  `--tentacle_address`:`--tentacle_port`. The plugin has no option to change the
  client name. For local delivery, check that `/var/spool/pandora/data_in/`
  exists and is writable.
- **The file module never appears.** The name did not resolve: check case,
  extension, a single quote in the name, or a file that lives only in a shared
  drive. The quota module keeps reporting.
- **The module names look wrong.** The prefix appears twice and the name starts
  with a space when no prefix is used. That is how this version composes names;
  use the exact name in alerts and filters.
- **`--transfer_mode local` does not deliver to another folder.** The destination
  is fixed. Use Tentacle delivery when the Pandora FMS server uses a different
  data directory.
- **The log file is missing or has an unexpected name.** `--log_file` defaults to
  `/tmp/exchangemail_logfile.txt`, a path left over from another addon. Set it
  explicitly, and note that the log only records the authentication warning and
  one success line, which reads `getting mail data` even though this plugin reads
  Drive metadata.

## Reference

### Command-line parameters

```text
./pandora_googledrive [--creds_json <path> | --creds_base64 <value>] [--port <port>] [--file_name <name>] [--module_prefix <prefix>] [--agent_prefix <prefix>] [--group <group>] [--interval <seconds>] [--temporal <dir>] [--data_dir <dir>] [--transfer_mode <mode>] [--tentacle_client <path>] [--tentacle_opts <options>] [--tentacle_port <port>] [--tentacle_address <address>] [--log_file <path>]
```

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `-h`, `--help` | No | — | Prints the usage summary, including `Version = 1.0`, and exits |
| `--creds_json` | Required only when `token.json` is absent | — | Path to the client secret JSON of the desktop OAuth client. Starts the interactive authorization when no `token.json` exists |
| `--creds_base64` | No | — | Base64 of the client secret JSON. The decoded content is written as `cred.json` but the OAuth flow opens `creds.json`, so this option does not complete the authorization on its own |
| `--port` | No | `8080` | Local port of the OAuth callback server used during the first authorization |
| `--file_name` | No | Empty | Exact name of the file whose last modification date is published. The module is omitted when the name does not resolve |
| `--module_prefix` | No | Empty | Prefix for module names. It is applied twice to every module name |
| `--agent_prefix` | No | Empty | Prefix for the agent alias; the agent identifier is derived from the alias |
| `--group` | No | Empty | Group written into the generated agent. The value is not validated before delivery; the help text mentions `exchange` as default, but the effective default is empty |
| `--interval` | No | `300` | Interval, in seconds, assigned to the generated agent |
| `--temporal` | No | `/tmp` | Accepted and not used: the agent XML is always staged in `/tmp` |
| `--data_dir` | No | `/var/spool/pandora/data_in/` | Accepted and not used: local delivery always targets `/var/spool/pandora/data_in/` |
| `--transfer_mode` | No | `tentacle` | `local` moves the XML into the data directory. Any other value, including the default, uses Tentacle |
| `--tentacle_client` | No | `tentacle_client` | Accepted and not used: the Tentacle command is always `tentacle_client`, resolved through `PATH` |
| `--tentacle_opts` | No | Empty | Accepted and not used: no extra options are passed to the Tentacle client |
| `--tentacle_port` | No | `41121` | Tentacle server port for Tentacle delivery |
| `--tentacle_address` | No | `127.0.0.1` | Tentacle server address for Tentacle delivery |
| `--log_file` | No | `/tmp/exchangemail_logfile.txt` | Log file for the authentication warning and the success line |

### Delivery

| Setting | Value |
|---------|-------|
| Default delivery | Tentacle |
| Tentacle client command | `tentacle_client`, resolved through `PATH`; not configurable |
| Tentacle address and port | `--tentacle_address` and `--tentacle_port` |
| Local delivery selector | `--transfer_mode local` (exact value) |
| Local destination | `/var/spool/pandora/data_in/`; not configurable |
| Extra Tentacle options | None; `--tentacle_opts` is not forwarded |
| XML staging directory | `/tmp`; not configurable |

### Google API surface

| Call | Fields read | Purpose |
|------|-------------|---------|
| `about().get` | `storageQuota` | Total limit and current usage of the account quota |
| `files().list` | `id`, `name` | Resolves `--file_name` by exact name, first match |
| `files().get` | `modifiedTime` | Modification time of the resolved file |
| OAuth scope | `https://www.googleapis.com/auth/drive.metadata.readonly` | Read-only metadata access for the three calls above |

The plugin makes no other Google API call: it does not enumerate the Drive, does
not read file content and does not change anything.

### Generated agent

| Attribute | Value |
|-----------|-------|
| Cardinality | One agent; its identity is derived from `--agent_prefix` |
| Alias | `<agent_prefix>GoogleDrive` |
| Identifier | Hash derived from the alias |
| Description | Empty |
| Interval | `--interval` (`300` seconds by default) |
| Group | `--group` (empty by default) |
| Operating system fields | Empty |
| Modules | The quota module always; the file module when the name resolves |

### Generated modules

| Module name | Type | Unit | Description |
|-------------|------|------|-------------|
| `<module_prefix><module_prefix> Google Drive Used` | `generic_data` | `%` | `Percentage of space used` |
| `<module_prefix><module_prefix> <file_name>` | `generic_data_string` | None | `Last change` |

### Addon identity

| Field | Value |
|-------|-------|
| Marketplace identifier | `pandorafms.googledrive` |
| Marketplace name | Google Drive |
| Version | `1.0` — the current Marketplace version, also printed by `-h` |
| Marketplace last update | 2025-06-25 |
| License | One — the download is limited to licensed users |
| Marketplace type | Miscelaneus |
| Marketplace category and tag | Miscelaneus; `cloud` |
| Downloads | 5 |
| Workflow | Monitoring plugin, server plugin mode |
| Executable | `pandora_googledrive` |
