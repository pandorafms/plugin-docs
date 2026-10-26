# Pandora Zendesk

*Article last updated: 2026-10-26.*

## What it does

The Pandora Zendesk addon operates tickets in a Zendesk Support site from
Pandora FMS. One execution performs exactly one operation against the Zendesk
API v2 of the site you name: read the ticket list, create a ticket, update a
ticket or delete a ticket.

The plugin is a one-shot command. It keeps no state, reads no configuration
file, holds no connection between runs and exits after a single API request. Its
input is the command line: the operation, the Zendesk subdomain, one credential
pair and, for the ticket operations, the ticket fields. Its result is the change
made in Zendesk; on success it prints nothing on standard output and it never
produces Pandora FMS module data.

Because the addon reports no values, treat it as an action rather than as a
collector: it creates, edits or closes a ticket as part of a Pandora FMS
workflow, and the ticket itself is where you confirm the outcome. The read
operation queries the ticket list but the response is discarded, so the useful
surface of this version is the write path.

## Prepare

### Compatibility and availability

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.zendesk`, version `1.0` | Documented target | Marketplace entry; see [Addon identity](#addon-identity) |
| Zendesk API v2 on `https://<ZENDESK_SUBDOMAIN>.zendesk.com` | `Required` | Every request is built against that host; see [Operations and endpoints](#operations-and-endpoints) |
| HTTPS access from the host that runs the addon to the Zendesk subdomain port `443` | `Required` | The URL scheme is fixed to `https` and the port is never configurable |
| A Zendesk agent account and API token (or password) authentication | `Required` | One credential pair is mandatory in every run |
| A Zendesk role that may list, create, update and delete tickets | `Required` | Prerequisite of the operations you run; not a compatibility statement |
| Operating system of the host that runs the addon | `Not validated` | No operating system has been recorded for this version |
| Zendesk plans and editions | `Not validated` | No Zendesk plan matrix has been recorded for this addon |
| Pandora FMS versions | `Not validated` | No version matrix has been recorded. The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later |

The addon is published in the Pandora FMS Marketplace, with download limited to
licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.zendesk](https://marketplace.pandorafms.com/entries/pandorafms.zendesk)

### Requirements

1. **A Zendesk Support site** with API access enabled for the account, and the
   subdomain of that site at hand. The subdomain is the part before
   `.zendesk.com`: a site at `https://example.zendesk.com` has the subdomain
   `example`.
2. **A dedicated Zendesk agent account** allowed to list, create, update and
   delete the tickets the plugin works with. A dedicated account keeps the
   Pandora FMS activity identifiable in the ticket history and its token
   revocable on its own.
3. **One credential pair**: the account email plus an API token, or the account
   email plus its password. See [Credentials](#credentials).
4. **HTTPS egress** from the host that runs the addon to the Zendesk subdomain.
   The plugin offers no proxy, custom certificate authority, timeout or port
   option, so the connection has to succeed with the default TLS settings of the
   host.
5. **A Pandora FMS installation** where the plugin is registered and executed.
   See [Register the plugin in the console](#register-the-plugin-in-the-console).

### Credentials

The plugin accepts two authentication modes and sends the credentials with HTTP
basic authentication:

| Mode | Flags | What is sent |
| --- | --- | --- |
| API token | `-us <EMAIL> -t <API_TOKEN>` | User `<EMAIL>/token` with the token as password |
| Account password | `-us <EMAIL> -p <PASSWORD>` | The email and the account password |

Use the API token mode. Zendesk issues and revokes tokens per account, so the
credential can be rotated without changing the account password, and password
authentication has to be enabled separately in Zendesk.

The two modes are not exclusive in the code: pass exactly one of `-t` and `-p`.
When both are present the plugin sends the request twice, once per mode, so a
create produces two tickets and an update is applied twice. When neither is
present it sends nothing and exits successfully.

The plugin has no credential file and reads no environment variable, so the
credential is always a command-line argument. It is therefore visible in the
shell history and in the process list of the host while the run lasts, and there
it is stored in the plugin parameters configured in the console. Use a dedicated
token, mark the field as a hidden value when it is registered as a server plugin
and revoke the token if it is exposed. See
[Register the plugin in the console](#register-the-plugin-in-the-console).

### Install the addon

Download the package from the Marketplace entry and copy the `pandora_zendesk`
executable to the host that will run it. For a server plugin, the recommended
directory is the plugin directory of the Pandora FMS server:

```bash
/usr/share/pandora_server/util/plugin/pandora_zendesk
```

Give the file execution permission for the user that runs the Pandora FMS
server. The addon needs no companion configuration file: everything it needs
arrives on the command line.

## Configure

The addon has two configuration surfaces: the command line, used for a manual
run, and the server plugin registration in the console, used to execute it from
Pandora FMS. Both pass the same flags; the registration only replaces the values
with console macros.

### Command line

```text
pandora_zendesk -m <method> -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> [ticket fields]
```

`-m` and `-i` and `-us` are always mandatory. The remaining flags depend on the
operation. Create a ticket:

```bash
./pandora_zendesk -m post -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> \
    -tn "Backup failure on the database server" \
    -tb "The scheduled backup did not finish. Check the job log." \
    -ts new -tp urgent -tt incident
```

Update the ticket with identifier `19`:

```bash
./pandora_zendesk -m put -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> \
    -id 19 -tn "Backup failure on the database server" \
    -tb "Restarted the backup job." -ts open -tp high -tt incident
```

Delete the ticket with identifier `4`:

```bash
./pandora_zendesk -m delete -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> -id 4
```

Read the first page of tickets:

```bash
./pandora_zendesk -m get -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN>
```

Replace `19` and `4` with the identifiers of your own tickets. The `get`
operation prints nothing, whatever the site contains; see
[Operations](#operations).

`-i` takes the subdomain only, never a URL: a value with `https://` or with
`.zendesk.com` produces a hostname that does not exist and the run fails to
resolve it.

The ticket fields are inserted verbatim into the JSON document that is sent, so
a double quote, a backslash or a line break inside `-tn`, `-tb`, `-ts`, `-tp` or
`-tt` produces a document Zendesk rejects. Keep the values on one line and
without escaping characters, or send the text through the Zendesk interface
instead.

For `post` and `put` the plugin always sends all five ticket fields. A flag you
omit is sent as an empty string, which is not a valid ticket value, so supply
every field of the operation: `-tn`, `-tb`, `-ts`, `-tp` and `-tt`.

### Register the plugin in the console

Registering the addon as a server plugin lets Pandora FMS execute it on the
server that runs the module, instead of from a terminal.

1. Open **Servers → Plugins** and register a new plugin.
2. Set a name and a description, and keep the plugin type **Standard**.
3. In **Plugin command**, enter the absolute path of the executable on the
   Pandora FMS server, for example
   `/usr/share/pandora_server/util/plugin/pandora_zendesk`.
4. In **Plugin parameters**, write the flags with the plugin macros
   `_field1_`, `_field2_`, ... in the place of the values. Keep the operation
   fixed in the parameters and leave the variable data as macros:

```text
-m post -i _field1_ -us _field2_ -t _field3_ -tn _field4_ -tb _field5_ -ts new -tp _field6_ -tt _field7_
```

5. In **Macro parameters**, describe each field. The example uses these values:

| Field | Description | Example value |
| --- | --- | --- |
| `_field1_` | Zendesk subdomain, without scheme and without `.zendesk.com` | `example` |
| `_field2_` | Email of the Zendesk account | `pandora@example.com` |
| `_field3_` | API token of that account; mark **Hide value** | — |
| `_field4_` | Ticket subject | `Backup failure` |
| `_field5_` | Ticket comment | `The scheduled backup did not finish.` |
| `_field6_` | Ticket priority | `urgent` |
| `_field7_` | Ticket type | `incident` |

<!-- SCREENSHOT NEEDED: Server plugin registration form in the Pandora FMS console, with the pandora_zendesk command path and the _field1_..._field7_ parameter line, no real token or account data. -->

Register one plugin per operation, or one plugin whose parameters begin with
the operation as a macro, because `-m` and the ticket fields differ between
create, update and delete. Update and delete also need `-id`, which is another
macro when the ticket identifier comes from the module.

Once registered, the plugin is available when creating plugin modules. Each
module fills the fields with its own values, so the same registration serves
several ticket workflows.

<!-- SCREENSHOT NEEDED: Plugin module fields for the registered pandora_zendesk plugin, showing the macros resolved to per-module values with the token field masked. -->

## Verify

Run the addon manually before wiring it into Pandora FMS. Use a ticket you can
delete, and confirm the effect in Zendesk rather than in the command output:

1. Create a ticket with the `post` example of
   [Command line](#command-line) and note the exit status:

    ```bash
    ./pandora_zendesk -m post -i <ZENDESK_SUBDOMAIN> -us <EMAIL> -t <API_TOKEN> \
        -tn "Pandora FMS connectivity test" \
        -tb "Created by the Pandora FMS Zendesk addon." \
        -ts new -tp normal -tt question
    echo $?
    ```

2. The command prints nothing and `echo $?` reports `0`. That pair does not
   prove that the ticket exists: it is also the output of a rejected request.
3. Open the ticket list of the site in Zendesk and check the new ticket: its
   subject, comment, status, priority and type must match the flags.
4. Delete the test ticket with the `delete` example and its identifier, and
   confirm that it no longer appears in the ticket list.

A successful run produces no standard output in any operation:

| Situation | Standard output | Exit status |
| --- | --- | --- |
| Request accepted by Zendesk | empty | `0` |
| No `-t` and no `-p` | empty | `0`, nothing is sent |
| `-m` value other than `get`, `post`, `put` or `delete` | empty | `0`, nothing is sent |
| Zendesk answered an error with a JSON body (wrong credentials, unknown ticket, invalid field value) | empty | `0` |
| Transport error, or a response body that is not JSON | `0` | `1`, with a diagnostic on standard error |

The `0` line of the last row is the only output the addon writes on its own. It
is not a module value: it is a failure marker. See
[Operate and troubleshoot](#operate-and-troubleshoot).

## Understand the results

### Operations

| Method | Zendesk request | Effect |
| --- | --- | --- |
| `get` | `GET /api/v2/tickets` | Reads the first page of the ticket list and discards it. Nothing is printed |
| `post` | `POST /api/v2/tickets` | Creates a ticket with the subject, comment, status, priority and type |
| `put` | `PUT /api/v2/tickets/<id>` | Updates those fields of the ticket and adds the comment |
| `delete` | `DELETE /api/v2/tickets/<id>` | Deletes the ticket |

The response body is parsed and never printed, in every method. What the plugin
leaves behind is the state of the ticket in Zendesk; what it returns to Pandora
FMS is an exit status, not data.

`get` does not paginate: Zendesk returns the first page of the ticket list and
offers the following pages in `next_page`, which the plugin ignores. Since the
result is discarded as well, `get` is only useful to check that the credentials
and the site name work at the transport level — and even that only when the run
writes something on standard error.

For `put`, the comment is added, not replaced: each update appends the `-tb`
text to the ticket as a new comment, and the plugin sends no `public` flag, so
Zendesk records it as a public reply to the requester.

### What Pandora FMS receives

A plugin module that executes this addon receives no module data, because the
addon emits no XML and no value on standard output. The module records the
execution, and the ticket in Zendesk is the result. Do not define thresholds or
graphs on this module: there is nothing to measure.

## Operate and troubleshoot

### Known limitations

These are behaviors of this version, not configuration mistakes:

- **Every error is silent unless the connection itself fails.** The plugin never
  checks the HTTP status. A `401` for wrong credentials, a `404` for an unknown
  ticket identifier and a `422` for an invalid field return a JSON error body
  that is parsed and discarded, so the run ends with status `0` and no message.
- **Both credentials execute the operation twice.** `-t` and `-p` are handled as
  independent branches, so supplying both sends two requests.
- **`get` produces no output** and reads only the first page of tickets.
- **Ticket fields are not escaped.** A double quote, a backslash or a line break
  in a ticket field invalidates the JSON document and Zendesk rejects it, again
  with no visible message.
- **`put` and `delete` need `-id`.** The flag is optional in the argument
  parser, but without it the URL is built from an empty identifier and the run
  stops with a `TypeError` traceback before sending anything.
- **An unsupported `-m` value does nothing.** Any value other than `get`,
  `post`, `put` or `delete`, including `GET`-style mixed case such as `Get`,
  exits with status `0` without sending a request. The built-in help describes
  `-m` as "get or post", yet `put` and `delete` are supported.
- **The diagnostic path repeats the request.** When a request raises an
  exception, the error handler issues the request again to build its message,
  and in the `put` and `delete` branches it uses a different method from the one
  that failed. The printed diagnostic can therefore describe a second call, and
  a second `post` can duplicate a ticket that was already created.

### Common failures

| Symptom | Cause | What to do |
| --- | --- | --- |
| The run prints nothing and returns `0`, but the ticket did not change | Zendesk rejected the request with a JSON error: credentials, permissions, ticket identifier or field value | Check the account, the token, the identifier and the five ticket fields; confirm the effect in Zendesk after every run |
| `0` on standard output and a traceback | The request raised an exception, and the retry inside the error handler raised it again | Check DNS resolution and HTTPS access to `<ZENDESK_SUBDOMAIN>.zendesk.com` from that host |
| `0` on standard output and `Error requesting <Response [<code>]>, please check conectivity` | The response body was not JSON, so the first attempt failed while parsing; the retry returned a response | Read the status code in the message: it is the answer of the retried request |
| `TypeError: can only concatenate str (not "NoneType") to str` | `put` or `delete` without `-id` | Add `-id` with the ticket identifier |
| Two identical tickets after one `post` | Both `-t` and `-p` were supplied | Keep exactly one credential flag |
| A ticket is created but the comment is empty or the update is rejected | A ticket field contains a double quote, a backslash or a line break, or one of the five fields was omitted and sent empty | Send all five fields on one line, without escaping characters |
| `Name or service not known`, or a hostname that contains `.zendesk.com` twice | `-i` received a URL or a full hostname instead of the subdomain | Pass only the subdomain |

## Reference

### Command-line parameters

The addon has no configuration file and reads no environment variable. Every
parameter is a command-line flag, and each flag has a long alias.

| Name | Alias | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `-m` | `--method` | Yes | — | Operation: `get`, `post`, `put` or `delete`. The value is compared literally, so `get`, `GET`, `post`, `POST`, `put`, `PUT`, `delete` and `DELETE` are the accepted spellings. Any other value sends nothing and exits with `0` |
| `-i` | `--ip` | Yes | — | Subdomain of the Zendesk site, without scheme and without `.zendesk.com`. Host is built as `https://<value>.zendesk.com` |
| `-us` | `--user` | Yes | — | Email of the Zendesk account |
| `-t` | `--token` | One of `-t` or `-p` | — | API token. Sent as the password of the `<EMAIL>/token` user |
| `-p` | `--password` | One of `-t` or `-p` | — | Account password, sent with the email in HTTP basic authentication |
| `-tn` | `--ticketname` | `post` and `put` | Empty string | Ticket subject |
| `-tb` | `--ticketbody` | `post` and `put` | Empty string | Ticket comment. On `put` it is added as a new comment |
| `-id` | `--idticket` | `put` and `delete` | — | Identifier of the ticket to update or delete. Omitting it stops the run with a traceback |
| `-ts` | `--ticketstatus` | `post` and `put` | Empty string | Ticket status. The built-in help describes it as "ticket body" |
| `-tp` | `--ticketpriority` | `post` and `put` | Empty string | Ticket priority. The built-in help describes it as "ticket body" |
| `-tt` | `--tickettype` | `post` and `put` | Empty string | Ticket type. The built-in help describes it as "ticket body" |

`-h` and `--help` print the usage summary and exit with `0`.

### Operations and endpoints

Every request is sent to `https://<ZENDESK_SUBDOMAIN>.zendesk.com`, with the
headers `Accept: application/json` and `Content-Type: application/json`.

| Method | Endpoint | Body |
| --- | --- | --- |
| `get` | `GET /api/v2/tickets` | None |
| `post` | `POST /api/v2/tickets` | `{"ticket": {"subject", "comment": {"body"}, "status", "priority", "type"}}` |
| `put` | `PUT /api/v2/tickets/<id>` | `{"ticket": {"subject", "comment": {"body"}, "status", "priority", "type"}}` |
| `delete` | `DELETE /api/v2/tickets/<id>` | None |

The body is assembled by concatenation, with no escaping of the ticket field
values.

### Ticket values

The plugin does not validate these values; it sends them as received and
Zendesk decides whether they are accepted. The values published for this addon
are:

| Field | Flag | Accepted values |
| --- | --- | --- |
| Status | `-ts` | `new`, `open`, `hold`, `pending`, `solved`, `closed` |
| Priority | `-tp` | `urgent`, `high`, `normal`, `low` |
| Type | `-tt` | `problem`, `incident`, `question`, `task` |

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.zendesk` |
| Name | Pandora Zendesk |
| Version | `1.0` |
| Marketplace last update | 2025-06-26 |
| Distributed file | `pandorafms.zendesk.1.0.zip` |
| Category | Miscelaneus |
| License | One |
| Availability | Download limited to licensed users |
| Author | Pandora FMS |
| Downloads | 3 |
