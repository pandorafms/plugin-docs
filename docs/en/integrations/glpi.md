# GLPI

*Article last updated: 2026-10-26.*

## What it does

The GLPI addon connects Pandora FMS alerts to the GLPI service desk. It is not a
monitoring plugin: it creates no agents and no monitoring modules. A Pandora FMS
alert command runs it once per alert event, and that run creates, comments or
replaces a GLPI ticket through the GLPI REST API.

Each run works on **one GLPI group** and does one of three things:

- **Create a ticket** when the Pandora FMS module has no ticket registered for
  that group.
- **Add a followup comment** to the registered ticket while it is open.
- **Replace the ticket** when the registered one is solved or closed, so the
  next incident starts a new ticket instead of reviving a finished one.

The addon keeps the link between a module and its tickets in the module's
**custom ID** field, with one entry per GLPI group, and reads and writes that
field through the Pandora FMS console API. It stores nothing on disk: the log
file is the only local artifact.

Two command modes drive the ticket lifecycle:

- `--recovery 0` (trigger) creates tickets and refreshes their content.
- `--recovery 1` (recovery) comments on the open ticket and removes the
  association when the ticket is already closed.

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that its integrations are compatible with Pandora FMS NG 784 and later versions |
| A GLPI instance whose REST API answers at `/apirest.php`, reachable from the host that runs the alert command | `Required` | Every operation uses that endpoint; the addon appends `/apirest.php/...` to `--url` |
| A Pandora FMS node console whose API can read and write the module custom ID, with the host listed in the console's *IP list with API access* | `Required` | The association is read and written through `include/api.php` before and after the GLPI calls |
| GLPI releases | `Not validated` | No GLPI version matrix is recorded for this addon |
| Operating system of the host that runs the alert command | `Not validated` | No operating system is recorded for version `1.0` |
| GLPI installed plugins or custom ticket fields | `Not validated` | The addon only uses core item types |

The GLPI version, the GLPI account and the node console are operational
prerequisites, not compatibility statements.

### Prerequisites

1. **Connectivity** from the Pandora FMS server that executes the alert command
   to the GLPI instance, over HTTPS whenever possible.
2. **A GLPI account and an API application token.** Every request carries the
   account credentials as HTTP basic authentication and the token in the
   `App-Token` header. The account must be able to read GLPI computers, search
   and read tickets, create tickets, add ticket followups and link a computer to
   a ticket.
3. **A Pandora FMS node console** that stores the module the alert belongs to,
   with the console API enabled. The host that runs the command must appear in
   the console's *IP list with API access*, and the API user must be able to read
   the module's agent and hold write permission on it: setting the module custom
   ID is checked against the write ACL. The custom ID functions are not served in
   metaconsole mode, so `--api_url` must address the node console.
4. **Numeric GLPI identifiers** for the ticket category and the group, plus the
   priority and request type you want. The addon sends them as numbers; it does
   not resolve names.
5. **A GLPI computer whose name matches the Pandora FMS agent alias** when the
   ticket has to be linked to that computer. The comparison is case-insensitive.
   Without a match the ticket is still created, but it is not linked to a
   computer and it is placed in entity `0`.

### Install the addon

The Marketplace entry distributes the addon as `pandorafms.glpi.1.0.zip`, with a
free download. Extract the `pandora_glpi` executable and copy it to the Pandora
FMS server that executes the alert command — for example
`/usr/share/pandora_server/util/plugin/pandora_glpi` — then make it executable.

The addon has no configuration file: every setting is a command-line argument,
and the alert command is the place where they are stored.

### Prepare the log file

The default log is `/tmp/glpi_logfile.txt`. To keep the record across reboots,
create the directory of another path first, for example `/var/log/pandora`, and
give write permission to the user that runs the Pandora FMS server process. The
addon creates the file when it is missing, but not its directory; an unwritable
path only prints an error and the run continues.

## Configure

Pandora FMS runs the addon from an **alert command**, and each **alert action**
holds the field values for the triggering and for the recovery event. One
command plus two sets of field values covers both `--recovery` modes.

### Create the alert command

1. Open **Alerts → Commands → Create**.
2. Fill **Name**, **Group** and **Description** with something the operators of
   the alert will recognise, for example `GLPI ticket`.
3. Paste the command, keeping one line per argument group:

```bash
/usr/share/pandora_server/util/plugin/pandora_glpi \
  -u _field1_ -x _field2_ -i _field3_ -a _field4_ \
  -n _agent_ -m _id_module_ \
  -t "_alert_name_ - _module_" \
  -d "_timestamp_ | _module_ | _data_" \
  -p _field5_ -c _field6_ -g _field7_ -k _field8_ \
  -l /var/log/pandora/glpi.log -r _field9_
```

4. Give every field a description. The command uses these fields:

| Field | Description to enter | Suggested values |
|-------|----------------------|------------------|
| `_field1_` | GLPI user | The account that creates the tickets |
| `_field2_` | GLPI password — mark **Hide** | — |
| `_field3_` | GLPI base URL, without a trailing slash | `https://<GLPI_URL>` |
| `_field4_` | GLPI application token — mark **Hide** | `<APP_TOKEN>` |
| `_field5_` | GLPI ticket priority | `1` to `6`, see [Ticket priority](#ticket-priority) |
| `_field6_` | GLPI category ID | `<CATEGORY_ID>` |
| `_field7_` | GLPI group ID | `<GROUP_ID>` |
| `_field8_` | Ticket title used when the GLPI computer is not found | `Unknown computer` |
| `_field9_` | Mode: `0` trigger, `1` recovery | `0` or `1` |

5. In **Field 9 values**, enter `0,Trigger;1,Recovery` so the field becomes a
   selection list instead of a free text box.

<!-- SCREENSHOT NEEDED: Alert command creation form with the GLPI command, the nine field descriptions and the hidden password and token fields, no real credentials visible. -->

`_agent_`, `_id_module_`, `_alert_name_`, `_module_`, `_data_` and `_timestamp_`
are Pandora FMS alert macros, expanded before the addon starts. `_agent_` gives
the agent alias, which is exactly the value the addon compares with the GLPI
computer name. Keep `-m` as `_id_module_` unless the command serves a single
fixed module: the module ID decides which module stores the ticket association.

### Create the alert action

1. Open **Alerts → Actions → Create**.
2. In **Command**, choose the command created above and fill its fields under
   **Triggering** with `_field9_` = `0`.
3. Fill the same fields under **Recovery** with `_field9_` = `1`.
4. Set **Threshold** to a value that prevents a flapping module from running the
   command repeatedly in a short interval.
5. Save the action and apply it through an alert template or directly on the
   module.

<!-- SCREENSHOT NEEDED: Alert action form with the GLPI command selected, the triggering field values and the recovery field values, with no real credentials visible. -->

Both field sets are stored in the action, so the same command serves every
module. The values that change per module are the ones Pandora FMS expands as
macros; the ones that change per alert are the field values.

### Ticket priority

`--ticket_priority` is the numeric GLPI priority. GLPI defines the scale:

| Value | Priority |
|-------|----------|
| `1` | Very low |
| `2` | Low |
| `3` | Medium |
| `4` | High |
| `5` | Very high |
| `6` | Major |

`--ticket_request_type` is also a numeric identifier — `8` by default — and must
be a request type that exists in your GLPI instance.

### Ticket content and the `%ticketID%` macro

`--ticket_name` and `--ticket_description` become the ticket title and content.
Both accept the macro `%ticketID%`, which the addon replaces with the ID of the
ticket it has just created. GLPI stores the content as sent, so you can include
its markup in `--ticket_description` when you want a formatted ticket body.

The macro is resolved by updating the ticket right after creating it, so the
ticket exists for a moment with the literal `%ticketID%` text. If that update is
refused, the ticket keeps the literal text.

`--ticket_name_error` is the title used when no GLPI computer matches the agent
alias, but the addon renames the new ticket to the resolved `--ticket_name`
immediately afterwards: in practice both titles end up being the same. See
[Limitations](#limitations).

### The module custom ID

The addon stores its state in the **custom ID** field of the module identified by
`--id_module`, as a map of GLPI group → ticket ID. It reads that map before
creating or commenting a ticket and writes it after creating or closing one.

- Treat that field as addon-owned. If you overwrite it with free text, the addon
  cannot parse it, takes the map as empty and creates a new ticket the next time
  the alert fires.
- `--ticket_group` is both the GLPI group assigned to the ticket and the key of
  the map. Changing the group in a command starts a new association, so the next
  trigger creates a new ticket instead of commenting the existing one.
- One module can hold one open ticket per group. Use different groups — in
  separate commands or actions — when a single module has to open tickets in
  different GLPI queues.

## Verify

Run the addon by hand before trusting an alert with it. Use a test module and a
test agent, because a successful run creates a real ticket.

```bash
/usr/share/pandora_server/util/plugin/pandora_glpi \
  -u '<USERNAME>' -x '<PASSWORD>' -i 'https://<GLPI_URL>' -a '<APP_TOKEN>' \
  -n 'test-agent' -m <MODULE_ID> \
  -t 'Pandora FMS test - %ticketID%' \
  -d 'Manual verification run' \
  -p 3 -c <CATEGORY_ID> -g <GROUP_ID> -k 'Unknown computer' \
  -l /var/log/pandora/glpi.log -r 0
```

A run that creates a ticket ends with lines like these on standard output:

```text
Succesful: Added custom id ' <GROUP_ID> : <TICKET_ID> ' in module with id <MODULE_ID>
Succesful: Ticket created successfully.
```

Check all four results:

1. **Standard output** shows the two lines above.
2. **The log file** contains the same messages with a timestamp prefix.
3. **GLPI** has the new ticket, with the title and content from the command.
4. **The module** in Pandora FMS shows the association in its custom ID field.

Then repeat the run with `-r 1` and the same arguments. This time the addon adds
a followup comment to the existing ticket instead of creating one:

```text
Succesful: Added tracking in the ticket : <TICKET_ID>
```

<!-- SCREENSHOT NEEDED: GLPI ticket created by the addon, showing title, content, priority, category, assigned group and the linked computer, with lab data only. -->

<!-- SCREENSHOT NEEDED: The module custom ID field in the Pandora FMS module editor after a run, showing the group and ticket association. -->

## Understand the results

The addon decides what to do from two facts: the association stored in the
module and the current status of the associated ticket.

| Association for the group | `--recovery 0` (trigger) | `--recovery 1` (recovery) |
|---------------------------|--------------------------|---------------------------|
| None | Creates a ticket, links the computer when it exists, stores the ticket ID | Creates nothing; logs `Error: There is no ticket open for the module with id <MODULE_ID> and group <GROUP_ID>` |
| Ticket open — any status other than `5` or `6` | Adds a followup comment with the resolved `--ticket_description`; no new ticket | Adds the same followup comment |
| Ticket solved (`5`) or closed (`6`) | Creates a new ticket, replaces the stored ID with the new one, links the computer | Removes the stored entry and adds the followup comment to the closed ticket |

A created ticket carries these values:

| Ticket field | Value |
|--------------|-------|
| Title | `--ticket_name`, `%ticketID%` resolved |
| Content | `--ticket_description`, `%ticketID%` resolved |
| Priority | `--ticket_priority` |
| Category | `--ticket_category` |
| Assigned group | `--ticket_group` |
| Request type | `--ticket_request_type` |
| Entity | The entity of the matching GLPI computer; `0` when no computer matches. When a closed ticket is replaced, the entity of the previous ticket |
| Linked computer | The GLPI computer whose name matches `--alias_agent`, case-insensitive |

Consequences worth knowing:

- **A solved ticket counts as closed.** GLPI status `5` (Solved) is enough for the
  next trigger to open a new ticket, even if the ticket has not been closed yet.
- **The ticket is never closed, solved or deleted by the addon.** A recovery only
  comments; closing the ticket is a manual or GLPI-side workflow.
- **Repeated triggers do not duplicate tickets** while the ticket stays open:
  every trigger after the first one appends a comment.
- **The comment uses the current command values.** A followup added on recovery
  carries the description resolved for that run, so the ticket history keeps the
  sequence of events the alert reported.

## Operate and troubleshoot

### Scheduling and concurrency

- Every run is one-shot: it authenticates, works on one group, closes the GLPI
  session and exits. There is no daemon, no state on disk and no background
  execution, so a manual run at any time is safe.
- The addon relies on the alert direction. It does not read the module status to
  decide between trigger and recovery; that is why `--recovery` must be driven by
  the action field values.
- **Avoid overlapping runs for the same module and group.** The association is
  read at the start and written after the ticket is created, so two runs that
  start together can both create a ticket. A non-zero action **Threshold** keeps
  the window small.
- Every run that has to create a ticket walks the whole GLPI computer inventory
  page by page to find the agent alias. On a large inventory this is slow: raise
  `--pagination_results` from its default `1` when the run takes too long.

### Credentials and transport

- The GLPI password, the application token and the console credentials are
  command-line arguments. They are visible in the process list while the addon
  runs, and they are stored in the alert command and in the alert action inside
  the console. Mark the secret fields with **Hide**, restrict who can read alert
  commands, and protect the server's process list.
- The console API password and the console user password travel in the query
  string of the `include/api.php` URL, so they can be recorded in the web server
  access log of the console. Use a dedicated API user with the narrowest rights
  that still allow reading the module and setting its custom ID.
- HTTPS certificates are verified against the trust store of the host. The addon
  has no option to disable verification or to supply a CA bundle: a GLPI instance
  with a certificate from a private CA needs that CA installed on the host.
- With plain HTTP the GLPI credentials travel unencrypted in the `Authorization`
  header. Restrict GLPI to a trusted network or place it behind TLS.

### Exit status and the log

Every handled error is printed on standard output and appended to the log file
with a `YYYY-MM-DD HH:MM:SS - ` prefix. The exit status is not a reliable success
signal:

| Status | Meaning |
|--------|---------|
| `0` | The run finished. Most handled failures — rejected credentials, a refused ticket creation, a refused comment — also end with `0` after printing the error |
| `2` | The command line was rejected before any request: a missing required argument or a value of the wrong type, for example a category name instead of its numeric ID |

Read the log file, or check the ticket in GLPI, to decide whether a run worked.
The log is append-only and shared by every run, so rotate it.

### Common failures

| Symptom | Cause and check |
|---------|-----------------|
| `Unauthorized: Check your credentials.` | GLPI rejected the login. Check `--user`, `--password` and `--app_token`, and that the GLPI account is active |
| `Error logging in: <status> - <body>` | The GLPI API answered with an error other than an authentication failure. The body is the GLPI message |
| `Bad Request: <body>` while reading or writing the custom ID | The console API rejected the request. Check `--api_pass`, `--api_user`, `--api_user_pass`, the host entry in the *IP list with API access*, and that `--api_url` points to a node console |
| `Error getting custom id: <status> - <body>` / `Error setting custom id: ...` | The console API answered with an error other than a bad request. The body identifies it |
| `Bad Request: <body>` after a trigger | GLPI refused the ticket. The body names the offending field: usually a category, group or request type that does not exist in that instance |
| `Error: There is no ticket open for the module with id <MODULE_ID> and group <GROUP_ID>` | A recovery ran with no association. Confirm the recovery uses the same `--id_module` and `--ticket_group` as the trigger |
| Two tickets for the same incident | Two overlapping triggers, or `--ticket_group` changed between runs |
| Every trigger creates a new ticket and the module custom ID stays empty | `--api_url` points at a metaconsole, where the custom ID functions are not served. Use the node console that stores the module |
| The run stops with an unexpected error after login | The GLPI session expired or the ticket could not be read. The log records what the addon had done until that point |
| Nothing is written to the log | The log path is not writable. The addon prints the write error and keeps going |

### Limitations

- One GLPI instance per run. Tickets in two instances require two commands.
- One ticket per module and group at a time.
- `--ticket_name_error` does not survive the run: the addon renames the ticket to
  the resolved `--ticket_name` right after creating it, so the title for an
  unknown computer is replaced. Use `%ticketID%` and the description to flag the
  missing computer instead.
- No request timeout is set. If GLPI accepts the connection and stops answering,
  the alert command waits; wrap the call in the system `timeout` command if that
  risk matters in your installation.
- The addon closes the GLPI session only at the end of a completed run. A run that
  exits early leaves its session open until GLPI expires it.
- The log file is the only audit trail the addon keeps; the ticket history in GLPI
  is the record of what the alerts reported.

## Reference

### Command-line arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `-u`, `--user` | Yes | — | GLPI account used to authenticate |
| `-x`, `--password` | Yes | — | Password of the GLPI account |
| `-i`, `--url` | Yes | — | GLPI base URL; the addon appends `/apirest.php/...` to it |
| `-a`, `--app_token` | Yes | — | GLPI application token, sent in the `App-Token` header |
| `-n`, `--alias_agent` | Yes | — | Agent alias, compared case-insensitively with the GLPI computer names |
| `-m`, `--id_module` | Yes | — | Numeric ID of the Pandora FMS module that stores the ticket association |
| `-t`, `--ticket_name` | Yes | — | Ticket title. Accepts `%ticketID%` |
| `-d`, `--ticket_description` | Yes | — | Ticket content and followup comment. Accepts `%ticketID%` |
| `-p`, `--ticket_priority` | Yes | — | Numeric GLPI priority, `1` to `6` |
| `-c`, `--ticket_category` | Yes | — | Numeric ID of the GLPI category |
| `-g`, `--ticket_group` | Yes | — | Numeric ID of the GLPI group assigned to the ticket, and key of the stored association |
| `-k`, `--ticket_name_error` | Yes | — | Title used when no GLPI computer matches the agent alias. It is replaced by `--ticket_name` right after creation |
| `-j`, `--ticket_request_type` | No | `8` | Numeric ID of the GLPI request type |
| `-l`, `--log_file` | No | `/tmp/glpi_logfile.txt` | Log file, appended with timestamped lines |
| `-r`, `--recovery` | No | `0` | `0` for a trigger, `1` for a recovery |
| `--api_url` | No | `http://localhost` | Base URL of the Pandora FMS node console; the addon appends `/pandora_console/include/api.php` |
| `--api_user` | No | `admin` | Console API user |
| `--api_pass` | No | `1234` | Console API password, sent as `apipass` |
| `--api_user_pass` | No | `pandora` | Password of the console API user |
| `--pagination_results` | No | `1` | Page step used while walking the GLPI computer inventory |
| `-h`, `--help` | No | — | Prints the usage summary and exits |

The usage summary of the addon documents a `--ticket_message` argument. No such
argument exists: the ticket content is `--ticket_description`.

### Execution and output

| Condition | Behavior |
|-----------|----------|
| The command line is missing a required argument | The addon prints the usage summary, names the missing arguments and exits with status `2` |
| A numeric argument receives text, for example a category name | The addon prints the rejected value and exits with status `2` |
| GLPI rejects the login | Prints `Unauthorized: Check your credentials.`, appends it to the log and exits |
| The module custom ID cannot be read | Prints the console API answer and stops without touching GLPI |
| No association and `--recovery 0` | Creates the ticket, stores the ID and prints two confirmation lines |
| No association and `--recovery 1` | Prints `Error: There is no ticket open for the module with id ... and group ...` |
| Association to an open ticket | Adds a followup comment and prints `Succesful: Added tracking in the ticket : <TICKET_ID>` |
| Association to a solved or closed ticket, `--recovery 0` | Creates a new ticket and replaces the stored ID |
| Association to a solved or closed ticket, `--recovery 1` | Removes the stored entry and adds the followup comment to the closed ticket |
| The run completes | Closes the GLPI session and exits |

### Addon identity

| Property | Value |
|----------|-------|
| Marketplace identifier | `pandorafms.glpi` |
| Name | GLPI |
| Version | `1.0` — the version of the Marketplace package `pandorafms.glpi.1.0.zip`, also reported by the addon's usage summary |
| Category | Miscelaneus |
| License | Free |
| Marketplace last update | 2026-01-28 |
| Availability | Free download |
| Marketplace entry | [pandorafms.glpi](https://marketplace.pandorafms.com/entries/pandorafms.glpi) |
