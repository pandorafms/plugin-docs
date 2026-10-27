# Discord integration

*Article last updated: 2026-10-26.*

## What it does

This integration posts Pandora FMS alerts to a Discord text channel through a
channel webhook. Each alert becomes one Discord message: an embed with a title,
a description, one field for every `key=value` pair you pass, and optionally a
thumbnail, a footer and an attached module graph.

The connector is distributed with Pandora FMS; there is no Marketplace entry
and no console component of its own. It is an external command launched by a
standard Pandora FMS alert command, so the Pandora FMS side of the integration
is the alert command plus the alert action that stores the webhook URL. A run
creates no agent, generates no module and keeps no state: it posts once and
exits.

The destination is a webhook, not a bot. The connector writes to one channel
and reads nothing back from Discord.

## Prepare Discord

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Discord connector distributed with Pandora FMS | Documented target | Connector this page describes. It has no Marketplace entry and declares no version. See [Connector identity](#connector-identity) |
| A Discord text channel with a channel webhook | `Required` | Every run posts to one webhook URL |
| HTTPS access from the host that runs the connector to `discord.com` (TCP `443`) | `Required` | The alert is delivered as an HTTPS POST to the webhook URL |
| A `python3` interpreter and the libraries declared in the connector's `requirements.txt` | `Required` | The bundled command definition invokes `python3 pandora_discord_cli.py`, and the connector loads those libraries at start-up |
| Pandora FMS release | `Not validated` | No release-specific validation record exists for this connector |
| Discord API version | `Not validated` | No version of the Discord webhook API has been recorded for this connector |
| Operating system of the Pandora FMS server | `Not validated` | No operating system is recorded for this connector |

### Requirements

1. A Discord account that can manage webhooks in the target channel: the
   **Manage Webhooks** permission on that channel.
2. A text channel to receive the alerts. A dedicated channel keeps alert
   traffic apart and lets you restrict who reads it.
3. Network access from the host that runs the connector to `discord.com` on TCP
   `443`.
4. The connector directory on the Pandora FMS server, with its libraries
   installed, readable and executable by the user the Pandora FMS server runs
   as.
5. The webhook URL, kept as a secret (see
   [Create the webhook](#create-the-webhook)).

### Create the webhook

Create one webhook for the channel that will receive the alerts:

1. Open the target text channel and its settings.
2. Open **Integrations** and create a webhook for that channel.
3. Give it a name and, optionally, an avatar. This is the identity channel
   members see as the sender of every alert.
4. Copy the webhook URL and save the webhook.

<!-- SCREENSHOT NEEDED: Discord channel settings, Integrations view with the created channel webhook and the Copy Webhook URL action -->

The URL has the shape
`https://discord.com/api/webhooks/<WEBHOOK_ID>/<WEBHOOK_TOKEN>` and is the only
credential the connector uses: posting needs no other authentication. Anyone
who holds that URL can post to the channel, so treat it as a secret and create
a new webhook if it leaks. Deleting the webhook in Discord invalidates the URL
immediately.

A webhook is not a bot: it can post into its own channel and nothing else. It
cannot read messages, list channels or react.

## Configure Pandora FMS

### Install the connector

Unzip the connector package on the Pandora FMS server. The command definition
shipped with the package expects it under
`/usr/share/pandora_server/util/pandora-discord`, and the examples in this page
use that path; any other directory works as long as the Pandora FMS server can
read and execute it. Install its libraries from that directory:

```bash
cd /usr/share/pandora_server/util/pandora-discord
pip3 install -r requirements.txt
```

### Create the alert command

Go to **Alerts** → **Commands** → **Create**. The command is a free-text shell
command, and the console replaces `_field1_` … `_field20_` with the alert
values before running it. Paste the definition included in the connector's
`test-exec.txt` file:

```bash
python3 /usr/share/pandora_server/util/pandora-discord/pandora_discord_cli.py -u "_field1_" -d "_field2_" -D "_field3_" --tittle_color _field4_ --thumb _field5_ --api_conf "_field6_" --module_graph "_field7_" -A "Pandora FMS Alert system" --footer "PandoraFMS" --author_icon_url "https://pandorafms.com/wp-content/uploads/2019/04/software-de-monitorizacion-pandorafms-logo.png" --author_url https://pandorafms.com/ --tmp_dir /tmp
```

The command uses seven fields. Describe each one in the command: the
description is the label the alert action shows next to the field.

| Field | Value at run time | Hide |
| --- | --- | --- |
| `_field1_` | Discord webhook URL | Yes |
| `_field2_` | Alert data as comma-separated `key=value` pairs | No |
| `_field3_` | Embed description (`-D`) | No |
| `_field4_` | Embed title colour: six hexadecimal digits (`-T`) | No |
| `_field5_` | Thumbnail URL (`--thumb`) | No |
| `_field6_` | Console API settings used to build the module graph (`--api_conf`) | Yes |
| `_field7_` | Module graph settings (`--module_graph`) | No |

Tick **Hide** on Field 1 so the webhook URL is masked when the action is
edited, and on Field 6 as well if you put console credentials there. The hidden
flag only masks the value on screen; it does not encrypt anything.

The form shows as many field rows as the console setting `max_macro_fields`
allows (10 by default, 20 at most). This command needs seven. The form also has
a **Field N values** column: those values are ignored for this command, because
what the connector receives comes from the alert action.

The remaining options of the line (author, footer, author icon and link,
temporary directory) are constants of the command. Edit the command line if you
need other values.

<!-- SCREENSHOT NEEDED: Alerts > Commands > Create form with the Discord command line and the seven field descriptions -->

Save the command with a name and a group.

### Create the alert action

Go to **Alerts** → **Actions** → **Create** and select the command you just
created. The form shows one pair of values per field the command declares. Fill
the triggering values:

| Field | Example |
| --- | --- |
| Field 1 | `<DISCORD_WEBHOOK_URL>` |
| Field 2 | `Agent=_agent_,Module=_module_,Status=_alert_text_severity_,Data=_data_,Timestamp=_timestamp_` |
| Field 3 | `Alert on _agent_` |
| Field 4 | `ed2512` |
| Field 5 | Do not fill it if you do not want a thumbnail |
| Field 6 | `user=<USERNAME>,pass=<PASSWORD>,api_pass=<API_TOKEN>,api_url=<PANDORA_FMS_URL>/pandora_console/include/api.php` |
| Field 7 | `module_id=_id_module_,interval=3600` |

Field 2 is the payload of the alert: every pair becomes one field of the embed.
The console expands alert macros inside every field value, so `_agent_`,
`_module_`, `_data_`, `_alert_text_severity_` and `_timestamp_` are replaced
with the values of the alert that fired.

Field 4 has no usable default through this command: the command passes its
value even when the field is empty, and an empty value stops the run with an
error before anything is sent. Use six hexadecimal digits without `#`; the
three-digit shorthand is read as a different colour.

Leave Field 5 empty unless you want a thumbnail. Leave Fields 6 and 7 empty if
you do not want the module graph.

<!-- SCREENSHOT NEEDED: Alerts > Actions > Create form for the Discord action, with the seven value rows -->

Set a recovery value for Field 2 if you want a different payload for recovery
events. When a recovery field is left empty, the console prefixes `[RECOVER]`
to the value of fields 2 to 20, so the first pair of the data string arrives as
`[RECOVER]Agent`.

### Apply the action

Give the action a name and a group, then save it with **Create**. To make it
fire, attach it through an alert template to the modules or the policy you want
to monitor, or add it to the alerts of a module.

## Verify

1. Run the connector by hand from the Pandora FMS server, without the graph:

```bash
python3 /usr/share/pandora_server/util/pandora-discord/pandora_discord_cli.py \
  -u "<DISCORD_WEBHOOK_URL>" \
  -d "Agent=<AGENT_NAME>,Module=<MODULE_NAME>,Status=CRITICAL,Data=22"
```

Expected output:

```text
To get graph data api conf shoul be provided please set an api config
Error status code: 204
```

The first line is printed on every run that does not pass `--api_conf`. The
second line reports the HTTP status Discord answered: `Message sent. status
code: 200` when it answered `200`, and `Error status code: <code>` for any
other status. Discord accepts a webhook post with `204 No Content`, so an
accepted message normally prints the `Error status code: 204` form. Confirm the
message in the channel.

2. Open the Discord channel. The message comes from the webhook identity, with
   an embed titled `Pandora FMS alert fired`, the description `alert`, the
   four fields of the data string and a timestamp with the run time.

<!-- SCREENSHOT NEEDED: Discord channel with one alert message, showing the embed and its fields -->

3. Trigger the alert from Pandora FMS: force the module into the state the
   action watches, or use the alert template where you attached the action, and
   confirm that the same message reaches the channel.

## Understand the integration

### How an alert reaches Discord

1. The alert fires and the console builds the command, replacing each
   `_fieldN_` with the value of the same field in the alert action, after
   expanding the alert macros inside it.
2. The Pandora FMS server runs the resulting command with the user it runs as.
3. The connector builds one webhook message and posts it once to the URL.
4. Discord publishes the message in the channel with the identity of the
   webhook.
5. The connector prints the status line and exits.

### Where each option lands

| Part of the message | Set by |
| --- | --- |
| Sender name and avatar | The webhook configuration in Discord. `--avatar_url` overrides the avatar for that message |
| Plain text above the embed | `-m`, `--message`. Empty by default |
| Embed title | `-t`, `--alert_tittle`. Default `PandoraFMS alert fired` |
| Embed description | `-D`, `--alert_desc`. Default `alert` |
| Embed colour bar | `-T`, `--tittle_color`. Default `53e514` |
| Embed author line | `-A`, `--author`, with `--author_url` and `--author_icon_url` |
| Thumbnail | `--thumb`. Omitted when empty |
| Footer | `-F`, `--footer`. Omitted when empty |
| Timestamp | Always the moment of the run. There is no option |
| Fields | One per `key=value` pair of `-d`, in the order you write them |
| Image | The module graph, when `--api_conf` and `--module_graph` are both set |

The embed author is not the sender. The sender is the webhook identity in
Discord; `-A` only fills the author line inside the embed.

### How data is parsed

`-d` is split on commas, and each piece on the equals sign, with spaces
trimmed around the key and the value.

- A piece without an equals sign stops the parse: the run prints `Warning,
  error parsing keypairs values: …`, keeps the pairs read so far and drops the
  rest. A value that itself contains an equals sign, such as `Data=a=b`, and a
  substituted value with a comma, such as an agent name, both trigger it.
- An empty value produces an empty embed field, and Discord refuses the whole
  message with `400`.
- Fields are sent as they arrive: the connector does not truncate, escape or
  reorder them.

### Exit status

| Status | When |
| --- | --- |
| `0` | The POST was answered with any HTTP status, including `4xx` and `429`. Also when the run is interrupted with `Ctrl-C` or `SIGTERM` |
| `1` | An uncaught error before or during the POST: a colour that is not hexadecimal, an empty or malformed webhook URL, or a DNS, TCP or TLS failure |
| `2` | Usage error: `-d` or `-u` missing, or an unknown option |

**The exit status does not report delivery.** Read the printed status line and
confirm the message in the channel.

## Operate

- **Manual execution.** Run the same command the alert command runs, from the
  Pandora FMS server or from any host that reaches `discord.com`. It is also
  the quickest way to test a webhook before creating the action.
- **One attempt per run.** The connector posts once and does not retry. A
  `429` or a `5xx` loses that alert.
- **Rate limit.** Discord limits how often a webhook can post. A burst of
  alerts can be refused; nothing is queued locally.
- **Graph download.** The request the connector makes to the console API to
  build the module graph has no timeout. If that API stops answering, the run
  stays open until the alert system's global timeout ends it.
- **Temporary file.** The graph is written to `--tmp_dir` (default `/tmp`) as
  `graph_<MODULE_ID>.<EPOCH>.png` and deleted at the end of the run. Two runs
  for the same module in the same second share the file name.
- **Server log.** At verbosity `8` or higher, `pandora_server.log` records the
  full command line of the action, including the webhook URL and the console
  credentials of Field 6. Keep that in mind before raising the verbosity for a
  support case.
- **Graph credentials.** The console API request carries the user, the
  password and the API pass in its query string, and the default API URL is
  plain `http://127.0.0.1`. Pointing `api_url` at a remote console sends those
  credentials across the network in the URL and leaves them in the access log
  of that web server.

## Troubleshoot

| Symptom | Cause and fix |
| --- | --- |
| `To get graph data api conf shoul be provided please set an api config` on every run | Normal when no `--api_conf` is given. The graph is skipped and the alert is still sent |
| `Error status code: 204` | The message was accepted: Discord answers `204 No Content`. Confirm it in the channel before treating it as a failure |
| `Error status code: 400` | The payload was refused: an empty field value, an empty pair, more than 25 fields, or a text above the Discord length limits. Fix the data string |
| `Error status code: 401`, `403` or `404` | The webhook URL is wrong, truncated or revoked. Copy it again from the channel settings, or recreate the webhook |
| `Error status code: 429` | Discord is rate-limiting the webhook. The alert is lost: the connector does not retry |
| A traceback ending in `invalid literal for int() with base 16` | Field 4 is empty or contains something other than hexadecimal digits. Use six digits without `#` |
| A traceback ending in `MissingSchema` or a connection error | The webhook URL is empty or malformed, or `discord.com` cannot be reached: DNS, proxy, TCP `443` or TLS |
| `usage: … error: the following arguments are required: -d/--data, -u/--url` | The command line lost one of its options, usually because the command was edited or a field was removed. Restore the definition from `test-exec.txt` |
| `Warning, error parsing keypairs values: …` | A pair has no equals sign, or a substituted value contains a comma or an equals sign. Shorten the values or remove the character |
| The run succeeds and nothing appears in Discord | The message went to the channel of another webhook, or the alert action is not attached to the module or policy that fired |
| A `[RECOVER]` prefix appears in the first field name | Recovery event with an empty recovery value for Field 2. Set a recovery payload if you do not want the prefix |

## Reference

### Connector identity

| Property | Value |
| --- | --- |
| Name | Discord connector |
| Distributed with | Pandora FMS. There is no Marketplace entry |
| Version | Not declared by the connector |
| Entry point | `pandora_discord_cli.py`, run with `python3` |
| Configuration file | None |
| Environment variables | None |
| Console component | None. It uses the standard alert command and alert action |
| Default installation directory in the bundled example | `/usr/share/pandora_server/util/pandora-discord` |

### Command-line parameters

```bash
python3 pandora_discord_cli.py -u <DISCORD_WEBHOOK_URL> -d "<DATA>" [options]
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `-u`, `--url` | Yes | — | Discord webhook URL, the destination channel |
| `-d`, `--data` | Yes | — | Comma-separated `key=value` pairs, one embed field each |
| `-t`, `--alert_tittle` | No | `PandoraFMS alert fired` | Embed title. The option name is spelled with three t's |
| `-D`, `--alert_desc` | No | `alert` | Embed description |
| `-m`, `--message` | No | Empty | Plain text sent above the embed |
| `-T`, `--tittle_color` | No | `53e514` | Embed colour, hexadecimal without `#` |
| `-A`, `--author` | No | `PandoraFMS` | Name of the embed author line |
| `-F`, `--footer` | No | Empty | Footer text. Omitted when empty |
| `--avatar_url` | No | Empty | Avatar of the message, overriding the webhook avatar |
| `--author_url` | No | Empty | Link of the embed author line |
| `--author_icon_url` | No | Empty | Icon of the embed author line |
| `--thumb` | No | Empty | Thumbnail URL. Omitted when empty |
| `--api_conf` | No | — | Console API settings for the module graph: `user`, `pass`, `api_pass` and optionally `api_url` |
| `--module_graph` | No | — | Graph settings: `module_id` and optionally `interval`, in seconds (default `3600`) |
| `--tmp_dir` | No | `/tmp` | Directory for the graph image before it is uploaded |
| `-h`, `--help` | No | — | Usage summary. Its description line is the leftover text `Test parser dic` |

`--api_conf` needs `user`, `pass` and `api_pass`; without them the graph is
skipped and a message says so. `api_url` defaults to
`http://127.0.0.1/pandora_console/include/api.php`. `--module_graph` needs
`module_id`; the graph is only built when both options are present.

### Output strings

| Output | Meaning |
| --- | --- |
| `Message sent. status code: 200` | The POST was answered with `200` |
| `Error status code: <code>` | The POST was answered with any other status, including the `204` of an accepted message |
| `Warning, error parsing keypairs values: <error>` | A pair of `-d` could not be parsed; the rest is dropped |
| `Api config enable` | `--api_conf` was given |
| `To get graph data api conf shoul be provided please set an api config` | No `--api_conf` was given. Printed on every run without it; the graph is skipped |
| `Error no user defined in api_conf keypairs, skipping graph generation.` | `--api_conf` without `user`, `pass` or `api_pass`. The alert is still sent |
| `error no module_id defined in module_graph keypairs, skipping graph generation.` | `--module_graph` without `module_id` |
| `Graph generated on temporary file <path>` | The graph was downloaded and stored |
| `Error requested api url, status code: <code>. skipping graph generation` | The console API refused the graph request |
| `Error, cant generate graph file: <error>` or `Error, cant add graph file: <error>` | The graph could not be stored or attached; the alert is still sent |
| `Interrupted by user` or `Received SIGTERM signal.` | The run was interrupted and exits `0` |

### Limits

| Limit | Value |
| --- | --- |
| Fields per embed | 25 |
| Field name length | 256 characters |
| Field value length | 1024 characters |
| Embed title length | 256 characters |
| Embed description length | 4096 characters |
| Footer length | 2048 characters |
| Author name length | 256 characters |
| Total characters of all embeds in the message | 6000 |
| Plain text content length | 2000 characters |
| Messages per run | 1 |
| Channels per run | 1, the one of the webhook URL |
| Retries | None |
| Attachments | The module graph image, when enabled |

The connector does not truncate: an alert above these limits is refused by
Discord with `400`.
