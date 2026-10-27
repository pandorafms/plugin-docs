# Pandora Zammad

*Article last updated: 2026-10-26.*

## What it does

The Pandora Zammad addon manages tickets in Zammad from the command line. Each
run performs one operation against the Zammad REST API: read the ticket list,
create a ticket, update a ticket or delete a ticket. It is a standalone
command: it creates no agent, generates no Pandora FMS modules and keeps no
state between runs.

The addon addresses the Zammad Cloud account of one subdomain. The endpoint is
built from the value of `-i`, which is the subdomain label only:

```text
https://<ZAMMAD_SUBDOMAIN>.zammad.com/api/v1/tickets
```

`put` and `delete` append the ticket ID to that path. Every request and
response is JSON over HTTPS.

A successful run prints nothing. The command returns no data to the caller:
the only result is the exit status, and a Zammad refusal does not always change
it (see [Exit status](#exit-status)). The effect of the operation is visible
only in Zammad.

The addon is not a Pandora FMS server plugin or agent plugin: a run produces no
agent XML and no module value, so nothing from it is ingested by Pandora FMS.

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Addon `pandorafms.zammad`, version `1.0` | Documented target | The Marketplace package this page describes. See [Addon identity](#addon-identity) |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all its integrations are compatible with Pandora FMS NG 784 and later versions |
| HTTPS access from the host that runs the addon to `<ZAMMAD_SUBDOMAIN>.zammad.com` (TCP `443`) | `Required` | Every request goes to that address; the addon has no option to change the scheme, the domain or the port |
| A Zammad user or access token allowed to read and write tickets | `Required` | The addon authenticates with the credentials it receives and checks no permission itself |
| A Zammad Cloud account addressed as `<name>.zammad.com` | `Required` | The endpoint is always `https://<value of -i>.zammad.com` |
| Zammad versions | `Not validated` | No version matrix has been recorded for this addon |
| Operating system of the host that runs the addon | `Not validated` | No operating system has been recorded for this version |

**Address scope.** The URL is fixed to
`https://<value of -i>.zammad.com/api/v1/tickets`, so `-i` is a subdomain
label, not a URL. A self-hosted Zammad served from another domain, over plain
HTTP or on a custom port is outside this interface: the addon cannot be pointed
at it.

### Requirements

1. **Network access** from the host that runs the addon to
   `https://<ZAMMAD_SUBDOMAIN>.zammad.com` on TCP `443`.
2. **A Zammad account with API access**, and one credential method: an access
   token, or a user and password when the instance keeps basic authentication
   enabled.
3. **Ticket permission for that identity.** It must be able to read, create,
   update and delete the tickets you operate on. The addon sends the request
   and does not inspect the answer.
4. **Values that exist in the instance**: the ticket group name, the numeric
   priority and state IDs, the article type and the customer. The addon does
   not validate them; Zammad accepts or refuses each request.

### Zammad access

Zammad supports token authentication and HTTP basic authentication, and either
method can be disabled in an instance. The addon implements the two:

- **Access token** (`-t`): sent in the `Authorization: Token token=<API_TOKEN>`
  header. Zammad recommends tokens over basic authentication, and the token
  works with the permissions of the user that created it.
- **User and password** (`-us` and `-p`): sent as HTTP basic authentication.

Pass exactly one credential method. With both, the addon sends the request
twice (see [Credentials and transport](#credentials-and-transport)).

The identity must be allowed to work with tickets in the target group, because
the requests carry no other identity.

### Install the addon

Download `pandorafms.zammad.1.0.zip` from the Marketplace entry, which is
limited to licensed users, and place the `pandora_zammad` executable on the
host that will run it:

[https://marketplace.pandorafms.com/entries/pandorafms.zammad](https://marketplace.pandorafms.com/entries/pandorafms.zammad)

The examples in this page run the executable from its own directory as
`./pandora_zammad`. The addon has no console component: nothing is added to the
Pandora FMS console, and the host only has to reach the Zammad API.

## Configure

Every run takes the operation, the Zammad subdomain and one credential method
as arguments:

```bash
./pandora_zammad -m <METHOD> -i <ZAMMAD_SUBDOMAIN> [-t <API_TOKEN> | -us <USERNAME> -p <PASSWORD>]
```

The addon has no configuration file and reads no environment variable: every
value, including the credentials, is a command-line argument. The method is
matched ignoring case.

### Methods

| `-m` value | Request | Effect |
| --- | --- | --- |
| `get` | `GET https://<ZAMMAD_SUBDOMAIN>.zammad.com/api/v1/tickets` | Reads the ticket list. The response is discarded |
| `post` | `POST` on the same endpoint | Creates a ticket with the ticket fields and one article |
| `put` | `PUT .../tickets/<TICKET_ID>` | Sends the same fields to an existing ticket |
| `delete` | `DELETE .../tickets/<TICKET_ID>` | Deletes the ticket |

A value other than these four sends no request and exits `0` without output.

### Create a ticket

```bash
./pandora_zammad -m post -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN> \
    -tn "Printer offline on floor 2" -tg Users -tp 2 -ts 1 \
    -tt note -tsub "Printer offline" \
    -tb "The printer does not answer on the network." \
    -tc <CUSTOMER_EMAIL> -tnote "Created by Pandora FMS"
```

Every ticket field flag in this command is required in practice: a create or
update that omits one does not send a request and stops with an error (see
[Command-line parameters](#command-line-parameters)). The addon does not
validate the values; Zammad does.

The same create with basic authentication instead of a token:

```bash
./pandora_zammad -m post -i <ZAMMAD_SUBDOMAIN> -us <USERNAME> -p <PASSWORD> \
    -tn "Printer offline on floor 2" -tg Users -tp 2 -ts 1 \
    -tt note -tsub "Printer offline" \
    -tb "The printer does not answer on the network." \
    -tc <CUSTOMER_EMAIL> -tnote "Created by Pandora FMS"
```

### Update a ticket

`put` appends the ticket ID to the endpoint and sends the same body as
`post`:

```bash
./pandora_zammad -m put -id <TICKET_ID> -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN> \
    -tn "Printer offline on floor 2" -tg Users -tp 2 -ts 4 \
    -tt note -tsub "Escalated" \
    -tb "The printer was replaced by the facilities team." \
    -tc <CUSTOMER_EMAIL> -tnote "Updated by Pandora FMS"
```

### Delete a ticket

`delete` needs the ticket ID and one credential method. The ticket field flags
are not used by this method:

```bash
./pandora_zammad -m delete -id <TICKET_ID> -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN>
```

### Credentials and transport

- The credentials are command-line arguments, so the shell history keeps them
  and the operating system process list exposes them while the command runs.
  Use a dedicated Zammad identity, and protect with file permissions any script
  or `cron` entry that stores the command.
- **Never pass both `-t` and `-p`.** The addon runs both authentication
  branches, so the request is sent twice: a `post` creates two tickets, and a
  `delete` follows the first removal with a second request that fails.
- The connection is always HTTPS. The addon exposes no TLS option: certificate
  validation is the client default against the system trust store, and there is
  no flag to add a CA bundle or to accept an unverified certificate.
- The token travels in a header, not in the URL, so it does not appear in a
  captured request line or in the server access log.
- Each request has no timeout. An endpoint that accepts the connection and
  never answers keeps the run open (see
  [Operate and troubleshoot](#operate-and-troubleshoot)).

## Verify

A successful request prints nothing, and the exit status alone does not prove
that Zammad accepted the operation. Verify the effect in Zammad.

1. **Check connectivity and authentication** with a read:

```bash
./pandora_zammad -m get -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN>
echo "exit=$?"
```

Expected output: nothing at all, and `exit=0`. A wrong token, or a token
without ticket permission, prints the same nothing and normally exits `0` as
well, because the addon parses the body and does not evaluate the HTTP status.

2. **Create a ticket in a test group** and confirm it in Zammad:

```bash
./pandora_zammad -m post -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN> \
    -tn "Pandora FMS connectivity test" -tg Users -tp 2 -ts 1 \
    -tt note -tsub "Connectivity test" \
    -tb "Test ticket created to validate the addon." \
    -tc <CUSTOMER_EMAIL> -tnote "Created by Pandora FMS"
```

Expected: no output, exit `0`, and the ticket with its article visible in the
Zammad group `Users`.

3. **Delete the test ticket** and confirm that it is gone:

```bash
./pandora_zammad -m delete -id <TICKET_ID> -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN>
```

4. **Force the error path** by omitting a ticket field from a create:

```bash
./pandora_zammad -m post -i <ZAMMAD_SUBDOMAIN> -t <API_TOKEN> -tn "Only a title"
```

The run stops before sending the request, reports the failure on standard error
and exits `1`.

## Understand the results

The addon never writes the API response anywhere. A `get` run reads the ticket
list and discards it, so the command cannot list tickets in a terminal; use the
Zammad interface or another client for that.

| `-m` value | What the run changes in Zammad |
| --- | --- |
| `post` | A new ticket with the title, group, priority, state, customer and note, and one article with the subject, body and type you passed |
| `put` | The same fields on an existing ticket, plus one article |
| `delete` | The ticket is removed. The ticket field flags are not used |
| `get` | Nothing: the response is discarded |

The request body is assembled from the flags in [Request body](#request-body).
Flags the method does not use are still accepted and have no effect.

**The exit status is not a success report.** The addon checks whether the
response body is JSON, not whether Zammad accepted the request. A `401`, a
`403`, a `404` or a `422` answered with a JSON body therefore looks like a
success: no output, exit `0`. Only a body that is not valid JSON, or a
transport failure, produces an error.

## Operate and troubleshoot

Each run is independent: the command sends its request and exits. There is no
daemon, no cache and no state to reset, so it can be executed by hand, from
`cron`, or from any Pandora FMS surface that runs an external command.

- The addon reports a result only through its exit status; the ticket itself is
  the evidence. When the outcome matters, read the ticket in Zammad after the
  run.
- The request has no timeout. Set a maximum execution time at the caller (the
  timeout of the surface that runs the command, or `timeout(1)`) so a silent
  endpoint cannot block the schedule.
- Because a rejected request exits `0` like an accepted one, a wrapper that must
  react to failure has to check the ticket in Zammad; the exit status is not
  enough.

| Symptom | Cause and fix |
| --- | --- |
| No output and exit `0` | Normal for an accepted request, and also for a rejected one. Confirm the effect in Zammad (see [Verify](#verify)) |
| `0` on standard output followed by `Error requesting <Response [404]>, please check conectivity`, exit `1` | The API answered with a body that is not valid JSON, usually because `-i` does not match a Zammad Cloud account, or because a proxy returned an error page. Check the subdomain |
| An unhandled error naming a failed request, exit `1` | The retry inside the error handler also failed, so the API is unreachable: DNS, TCP `443`, TLS or a firewall |
| An unhandled error before any request is sent, exit `1` | A ticket field is missing on `post` or `put`, or `-id` is missing on `put` or `delete`. Add every value the body needs |
| Two tickets appear, or the operation is applied twice | `-t` and `-p` were both passed. Pass exactly one credential method |
| No request is sent and the command exits `0` | Neither `-t` nor `-p` was passed, or `-m` has a value other than `get`, `post`, `put` and `delete` |
| A usage error listing the required arguments, exit `2` | `-m` or `-i` is missing, or a flag is misspelled |
| Zammad rejects the ticket and the command still exits `0` | The token or user lacks ticket permission, the token is wrong, or a value does not exist in the instance. The addon does not report the HTTP status |
| The request is rejected when the text contains a double quote or a line break | Values are inserted into the body without escaping, so such a value produces an invalid request. Remove the character from the text |
| A run never returns | The endpoint accepted the connection and does not answer, and there is no timeout. Interrupt the run and set a timeout at the caller |

## Reference

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.zammad` |
| Name | Pandora Zammad |
| Version | `1.0` |
| Marketplace last update | 2025-06-26 |
| Category | Miscellaneous |
| License | One; the download is limited to licensed users |
| Downloads | 2 |
| Marketplace entry | [pandorafms.zammad](https://marketplace.pandorafms.com/entries/pandorafms.zammad) |

### Command-line parameters

```bash
./pandora_zammad -m <METHOD> -i <ZAMMAD_SUBDOMAIN> [options]
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `-m`, `--method` | Yes | — | Operation: `get`, `post`, `put` or `delete`, ignoring case. Another value sends nothing and exits `0` |
| `-i`, `--ip` | Yes | — | Zammad Cloud subdomain label, not a URL. The endpoint is `https://<value>.zammad.com/api/v1/tickets`. The built-in help describes it as a "zendesk subdomain name" |
| `-t`, `--token` | Conditional | — | One credential method. Zammad access token, sent as `Authorization: Token token=<value>` |
| `-us`, `--user` | Conditional | — | Required with `-p`. Zammad user for HTTP basic authentication |
| `-p`, `--password` | Conditional | — | Required with `-us`. Password of that user |
| `-id`, `--idticket` | Conditional | — | Required for `put` and `delete`. Ticket ID appended to the endpoint |
| `-tn`, `--ticketname` | Conditional | — | Required for `post` and `put`. Ticket title |
| `-tg`, `--ticketgroup` | Conditional | — | Required for `post` and `put`. Group name |
| `-tp`, `--ticketpriority` | Conditional | — | Required for `post` and `put`. Priority ID |
| `-ts`, `--ticketstatus` | Conditional | — | Required for `post` and `put`. State ID |
| `-tt`, `--tickettype` | Conditional | — | Required for `post` and `put`. Article type |
| `-tsub`, `--ticketsubject` | Conditional | — | Required for `post` and `put`. Article subject |
| `-tb`, `--ticketbody` | Conditional | — | Required for `post` and `put`. Article body |
| `-tc`, `--ticketcustomer` | Conditional | — | Required for `post` and `put`. Customer, as the email address or the ID that Zammad expects |
| `-tnote`, `--ticketnote` | Conditional | — | Required for `post` and `put`. Note, sent as a top-level ticket field |
| `-h`, `--help` | No | — | Usage summary |

The ticket field flags are optional in the command line but required for a
create or an update: the body cannot be assembled without them, so the run
stops with an error instead of sending a partial request. A `put` or `delete`
without `-id` stops the same way.

### Request body

`post` and `put` send one JSON document. The method `delete` and the method
`get` send no body.

| Flag | JSON field | Notes |
| --- | --- | --- |
| `-tn` | `title` | |
| `-tg` | `group` | |
| `-tp` | `priority_id` | Sent as a string |
| `-ts` | `state_id` | Sent as a string |
| `-tc` | `customer` | |
| `-tnote` | `note` | Top-level ticket field |
| `-tsub` | `article.subject` | |
| `-tb` | `article.body` | |
| `-tt` | `article.type` | |
| — | `article.internal` | Always `false`; there is no flag for it |

The body is sent with `Content-Type: application/json`. The values are
inserted as they arrive, without escaping, so a double quote or a line break
inside a ticket field makes the body invalid.

Only the fields in this table are part of the interface: tags, owner, pending
time and attachments have no flag and cannot be set from the addon.

### Exit status

| Status | When |
| --- | --- |
| `0` | The API answered and the body was valid JSON, which includes `4xx` responses with a JSON error body. Also the runs that send no request: no credential method, or a `-m` value other than the four methods |
| `1` | The body was not valid JSON: the command prints `0` and an `Error requesting ...` message. Also an unhandled error before or during the request: a missing ticket field, a missing ticket ID, or a connectivity failure |
| `2` | Command-line usage error: missing `-m` or `-i`, or an unrecognised flag |
