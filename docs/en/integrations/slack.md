# Slack integration

*Article last updated: 2026-10-27.*

## What it does

The Slack integration delivers Pandora FMS alerts to a Slack channel as chat messages. When an alert
fires or recovers, Pandora FMS runs a connector on the server that processes the alert and the
connector posts the alert fields through the Slack Web API, as the Slack app you authorize.

The connector ships with Pandora FMS. There is no Marketplace entry for it and nothing to download
from the catalogue: the executable and the default alert command named **Pandora Slack** are already
part of the product, and you only add the Slack side and the credentials.

Each run posts **two messages** by default: the alert (an emoji, a bold title, an italic description
and one `key : value` line per data pair) and, separately, a footer message with the text
`PandoraFMS`. Both are configurable, and the footer can be suppressed.

Optionally the connector can attach a module graph image obtained from the Pandora FMS API. That path
depends on a Slack file-upload method that Slack retired, so the image is not delivered any more. The
alert text is unaffected. See [Understand the integration](#understand-the-integration).

## Prepare the external service

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| A Slack workspace where you can create and install an app | `Required` | The connector authenticates with a Slack app bot token, so the app must exist and be installed in the workspace |
| A Slack app with a bot user and the `chat:write` scope | `Required` | Every message is posted with `chat.postMessage`, which requires `chat:write` |
| The app as a member of the target channel, or the `chat:write.public` scope | `Required` | Slack rejects a post from an app that is not in the channel with `not_in_channel`; `chat:write.public` allows public channels without joining |
| Outbound HTTPS from the Pandora FMS server to `slack.com` (TCP `443`) | `Required` | All calls go to the Slack Web API |
| Pandora FMS release that ships the **Pandora Slack** command | `Not validated` | No release-specific record exists for this connector |
| Operating system of the Pandora FMS server | `Not validated` | No operating system has been recorded for this connector |
| A corporate proxy or TLS interception between the server and Slack | `Not validated` | The connector has no proxy or CA option of its own; see [Troubleshoot](#troubleshoot) |

### Create the Slack app

1. Open `https://api.slack.com/apps` and choose **Create New App** → **From scratch**.
2. Enter a name, select the workspace that owns the channel, and confirm.
3. Open **OAuth & Permissions**, scroll to **Scopes** → **Bot Token Scopes**, and add `chat:write`.
4. Choose **Install to Workspace** and authorize the app.
5. Copy the **Bot User OAuth Token**. It starts with `xoxb-`; this is the value the connector needs.

<!-- SCREENSHOT NEEDED: Slack app "OAuth & Permissions" page with the Bot Token Scopes section showing chat:write, app name anonymised. -->

<p class="callout warning">The connector authenticates with a bot token. An <strong>Incoming Webhook</strong> URL does not work: the connector posts through the Slack Web API, so a webhook endpoint copied into the token parameter is refused with an authentication error. Ignore instructions that ask you to enable Incoming Webhooks for this integration.</p>

### Invite the app to the channel

In the target channel, run `/invite @<APP_NAME>` and select the app you created. Slack requires the
app to be a member of the conversation: a post to a channel the app has not joined fails with
`not_in_channel`. As an alternative, request the `chat:write.public` scope and reinstall the app; that
scope covers public channels the app has not joined, but not private channels.

### Get the channel identifier

Open the target channel, open its details, and copy the channel ID. It starts with `C` for a public
channel and `G` for a private one. A channel name also works, but the ID is the only value that
survives a rename, so prefer it.

## Configure Pandora FMS

### Place the connector on the server

1. Make sure the connector is on the Pandora FMS server, in a directory readable and executable by
   the user that runs the Pandora FMS server; copy it from its package if it is not. The default
   command uses `/usr/share/pandora_server/util/plugin/`.
2. Install the runtime requirements that the package ships with before the first run. The package
   includes a requirements file for them.
3. Make the installed path match the alert command. The shipped command calls
   `/usr/share/pandora_server/util/plugin/pandora-slack-cli`, without extension, while the packaged
   file is named `pandora-slack-cli.py`. Rename the file to `pandora-slack-cli`, or edit the command
   so it names the file you installed.
4. Repeat the copy on every Pandora FMS server that can process alerts. The command is not internal
   to the console, so the server that fires the alert is the one that executes it.

### Edit the shipped alert command

The console already contains the alert command **Pandora Slack**. Open **Alerts** → **Commands** and
edit it; if your installation does not have that command, create one with the same command line. In
both cases:

1. Replace the literal `TOKEN` in the command line with the bot token you copied.
2. Leave the rest of the command line as it is, or adjust the installation path (previous step).

The shipped command line is:

```text
/usr/share/pandora_server/util/plugin/pandora-slack-cli -t "TOKEN" -d "_field1_" -c "_field2_" -e "_field3_" -T "_field4_" -D "_field5_"
```

The five fields use these descriptions and preset values in the console:

| Field | Console description | Preset value | Purpose |
| --- | --- | --- | --- |
| 1 | `Data in coma separate keypairs` | `data=_data_` | One `key=value` pair per fact of the message |
| 2 | `Slack channel id/name` | empty | Channel that receives the alert |
| 3 | `Title emoji` | `:red_circle:,Red circle;:green_circle:,Green circle` | Emoji that prefixes the title line; the preset is a two-entry list |
| 4 | `Title` | `[PANDORA] Alert FIRED on _agent_ / _module_` | Bold title line |
| 5 | `Description` | `_agent_ \| _module_ \| _data_ \| _timestamp_` | Italic line under the title |

The token is written in the **command body**, not in a field. This differs from older instructions
that place it in the second field: in the shipped command, field 2 is the channel and the token is the
literal `TOKEN` you replace. If you prefer to keep the token out of the command body, replace
`-t "TOKEN"` with a reference to a spare field, describe that field, and tick its **Hide** box. Hiding
a field only masks it in the console; the value is still substituted into the command line when the
alert runs.

<!-- SCREENSHOT NEEDED: Alert command edit form for "Pandora Slack" showing the command line with the token redacted and the five field rows with their descriptions and preset values. -->

### Create or edit the alert action

Open **Alerts** → **Actions** and edit the action **Pandora Slack**, which ships as a default action.
Its fields come pre-filled from the command; check three things:

- Field 2 (channel) is **empty**: enter the channel ID.
- The **Triggering** fields use `:red_circle:` and the **Recovery** fields use `:green_circle:`.
- Triggering and Recovery have their own title and description, which you can rewrite. Keep the
  macros: they carry the agent, module, value and timestamp into Slack.

<!-- SCREENSHOT NEEDED: Alert action form for "Pandora Slack" with a lab channel ID, the triggering and recovery field rows, and no real channel or credentials. -->

### Attach the action to what you monitor

Create or edit an alert template under **Alerts** → **Templates** and add this action to it, then
apply the template to the modules or the policy that must notify Slack. See the Pandora FMS manual on
[alerts](https://pandorafms.com/manual/en/documentation/pandorafms/management_and_operation/01_alerts)
for templates, actions and macro substitution.

## Verify

Run the connector once by hand on the Pandora FMS server before relying on an alert:

```bash
/usr/share/pandora_server/util/plugin/pandora-slack-cli \
  -t "<API_TOKEN>" \
  -c "<CHANNEL_ID>" \
  -d "Agent=<AGENT_NAME>,Module=<MODULE_NAME>,Status=Critical,Data=22" \
  -T "Pandora FMS test alert" \
  -D "Manual verification" \
  -F ""
```

A successful run prints exactly one line on standard output:

```text
> Message sent successfully
```

and the channel receives one message:

```text
:red_circle: *Pandora FMS test alert*
_Manual verification_

*Agent* : <AGENT_NAME>
*Module* : <MODULE_NAME>
*Status* : Critical
*Data* : 22
```

Because the example passes `-F ""`, no footer message is posted. Remove that argument and the same
run posts a second message containing only `PandoraFMS`.

Two checks complete the verification:

1. **The connector alone** — the manual run above. If it fails here, the console cannot succeed.
2. **The console path** — trigger the alert from a module with the action attached, and confirm that
   the message reaches the channel with the agent, module and value of that alert.

Do not use the exit status to decide whether the delivery worked: the connector exits with status `0`
after a Slack error too (see [Exit codes](#exit-codes)). Look at the channel and at the message the
connector printed.

## Understand the integration

### Flow

1. An alert fires or recovers, and Pandora FMS selects the actions of the alert template.
2. The server substitutes the alert macros in the command fields (`_agent_`, `_module_`, `_data_`,
   `_timestamp_`, `_field1_`…`_field5_`) and runs the command line of the alert command.
3. The connector turns `-d` into the fact lines, joins them with the title, description and emoji, and
   calls `chat.postMessage` for that text.
4. If a footer is configured, it calls `chat.postMessage` a second time with the footer text alone.
5. If a module graph was requested, it fetches the image from the Pandora FMS API and tries to upload
   it to the channel.

The connector keeps no state and has no queue: each run is a synchronous HTTP call from the server
that processes the alert. A failed call is reported on the command output and is not retried.

### Message composition

- The first line is the emoji followed by the title in bold: `:red_circle: *<TITLE>*`.
- The second line is the description in italics. An empty description leaves an empty italic line, not
  no line.
- Then a blank line and one line per data pair, with the key in bold: `*<KEY>* : <VALUE>`.
- Pairs are read from left to right with `=` as the separator between key and value and `,` between
  pairs. A value that contains `=` breaks the pair: the warning
  `Warning, error parsing keypairs values: too many values to unpack` is printed and the pairs after
  it are dropped.
- Slack applies its own message formatting and may rewrite parts of the text (links, for example). The
  connector compares the text Slack returns with the text it sent, so a rewritten message produces a
  traceback **after** the message has been delivered (see [Troubleshoot](#troubleshoot)).

### Delivery constraints

- Slack accepts roughly one message per second per channel from an app. With the default footer, every
  alert consumes two of those slots, and a burst of alerts to one channel can be rate limited.
- The message is plain text with Slack markup. The connector sends no blocks, attachments or
  interactive elements.
- There is no retry and no persistence: if the server cannot reach Slack at that moment, that alert is
  not delivered.

### Module graphs are no longer delivered

The graph path exists and is documented for completeness, but it cannot succeed today:

- The connector requests the graph from the Pandora FMS external API (`module_graph`), decodes it and
  writes it to `--tmp_dir` as `graph_<module_id>.<epoch>.png`.
- It then uploads the file with the Slack `files.upload` method. Slack deprecated that method and
  stopped it on **12 November 2025**, so the upload is refused and the connector prints
  `File Got an error: <error>`. The alert text has already been sent at that point.
- The temp file is removed at the end of the run. Two runs for the same module in the same second
  share the same file name.

Also note that `--api_conf` carries the Pandora FMS API password and API pass in the command line, so
they are visible in the process list while the alert runs.

### TLS and proxies

- At startup the connector forces its own CA bundle, so the operating system trust store is not used.
  A Slack endpoint or an interception proxy with a private certificate fails verification unless the
  certificate is added to that bundle.
- The connector has no proxy option. The Slack client reads `HTTPS_PROXY`, `https_proxy`,
  `HTTP_PROXY` and `http_proxy` from the environment of the user that runs the command, so set them in
  the service environment if the server needs a proxy.

## Troubleshoot

The connector reports most failures on standard output and keeps going. Read the message, not the
exit status.

| Symptom | Cause and action |
| --- | --- |
| `Got an Slack auth error: invalid_auth` | The token is wrong or revoked, or it is not a bot token; an Incoming Webhook URL cannot authenticate this call. Copy the **Bot User OAuth Token** of the installed app again. |
| `Got an Slack auth error: not_in_channel` | The app is not a member of the channel. Invite it with `/invite @<APP_NAME>`, or grant `chat:write.public`. |
| `Got an Slack auth error: channel_not_found` | The channel ID or name is wrong, or the app cannot see a private channel it does not belong to. |
| `Got an Slack auth error: missing_scope` | The app lacks `chat:write`. Add the scope in **OAuth & Permissions** and reinstall the app: scopes only take effect after a reinstall. |
| `Got an Slack auth error: ratelimited` | Too many messages to that channel in a short time. Space the alerts or remove the footer message to halve the traffic. |
| `File Got an error: <error>` (for example `method_deprecated`) | The graph upload uses the Slack method retired on 12 November 2025. Remove `--api_conf` and `--module_graph`; the text alert was already delivered. |
| `Warning, error parsing keypairs values: …` and missing facts | A data value contains `=` or the pair list is malformed. Quote values without `=`, or restructure the alert command. |
| The channel shows the alert but the run ends with a traceback about `assert` | Slack rewrote the message text, and the connector compares it with what it sent. The delivery succeeded; the failure is cosmetic. |
| `bad interpreter: No such file or directory` | The command calls the packaged file directly and the interpreter declared inside that file is not available on the server. Call the connector through the interpreter installed on the host, or provide the declared name. |
| `No such file or directory` naming the connector path | The installed path and the alert command disagree, usually because of the `.py` suffix. Rename the file or edit the command. |
| A certificate verification error | Private CA or TLS interception: the connector trusts only its own CA bundle (see above). |
| The server log records `exceeded the global alert timeout` | The command did not finish within the configured global alert timeout. Check the server's connectivity to `slack.com` and Slack's status. |
| Nothing in the channel and nothing printed | The action is not attached to the module, the alert is not firing, or the command line never ran. Check the alert history in the console first. |

For a failure that leaves no clue, run the command line by hand with the same values the console
substitutes and read the output. The connector prints its own diagnostics there.

## Reference

### Command-line parameters

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `-d`, `--data` | Yes | — | Facts as `key=value` pairs separated by commas, for example `Agent=<AGENT_NAME>,Module=<MODULE_NAME>,Data=22`. Empty is accepted and produces no fact lines. |
| `-t`, `--token` | Yes | — | Slack app bot token (`xoxb-…`). A webhook URL is not valid here. |
| `-c`, `--channel` | Yes | — | Channel ID (`C…`, `G…`) or channel name. The app must be a member of the channel. |
| `-e`, `--emoji` | No | `:red_circle:` | Emoji that prefixes the title line. Slack emoji markup, for example `:warning:`. |
| `-T`, `--tittle` | No | `PandoraFMS alert` | Title line, in bold. The long name is `--tittle`, with the double `t`. |
| `-D`, `--desc` | No | empty | Description line, in italics. Empty leaves an empty italic line. |
| `-F`, `--footer` | No | `PandoraFMS` | Text of a second, separate message. An empty value (`-F ""`) suppresses that message. |
| `--api_conf` | No | empty | Pandora FMS API details for graph generation: `user=…,pass=…,api_pass=…,api_url=…`. `api_url` defaults to `http://127.0.0.1/pandora_console/include/api.php`. Without `user`, `pass` and `api_pass`, graph generation is skipped. |
| `--module_graph` | No | empty | Graph request: `module_id=…,interval=…`. `interval` defaults to `3600` seconds. Requires `--api_conf`. |
| `--tmp_dir` | No | `/tmp` | Directory where the graph image is written before upload. |

With `--api_conf`, the run prints `Api config enable` before the message. Argument errors — a missing
required option, for example — are reported by the argument parser on standard error and end the run
with status `2`.

### Message layout

| Line | Content | Source |
| --- | --- | --- |
| 1 | `<emoji> *<title>*` | `-e` and `-T` |
| 2 | `_<description>_` | `-D` |
| 3 | empty | — |
| 4… | `*<key>* : <value>`, one per pair | `-d`, in the order given |
| Separate message | `<footer>` | `-F`, skipped when empty |

### Exit codes

| Situation | Status |
| --- | --- |
| Message accepted by Slack | `0` |
| Slack API error (`invalid_auth`, `not_in_channel`, `missing_scope`, `ratelimited`…) | `0` — the error is printed and the run ends |
| Graph generation or upload error | `0` — the alert text was already sent |
| `SIGINT` or `SIGTERM` | `0` |
| Slack returns text that differs from the text sent | `1` — traceback, after delivery |
| Missing or invalid command-line arguments | `2` |

### Console objects shipped with the product

| Object | Detail |
| --- | --- |
| Alert command | **Pandora Slack**, not an internal command, so it runs the executable on the alert server |
| Alert action | **Pandora Slack**, shipped as a default action, with separate triggering and recovery fields |
| Command path expected | `/usr/share/pandora_server/util/plugin/pandora-slack-cli` |
| Packaged file name | `pandora-slack-cli.py` |
| Marketplace entry | None — the connector ships with Pandora FMS |
| Published version | None — the connector reports no version, so this page documents the behaviour observed on 2026-10-27 |

### Slack surface used

| Slack method | Scope | Used for | Current state |
| --- | --- | --- | --- |
| `chat.postMessage` | `chat:write` | The alert message and the footer message | Available |
| `files.upload` | `files:write` | The module graph image | Retired by Slack on 12 November 2025; the upload fails |
