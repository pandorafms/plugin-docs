# Pandora CLI

## Introduction

**Ver**. 04-09-2026

`pandora-cli` is a command-line client for the Pandora FMS **API v2**. It lets you read and change
console data from a terminal or a script, without going through the web interface.

**Type**: Standalone command-line tool

Every command follows the same shape:

```
pandora-cli <entity> <verb> [arguments] [flags]
```

```bash
pandora-cli user list
pandora-cli event list --size 10
pandora-cli tag get 5
pandora-cli group create --set name=Servers
```

It is a single self-contained executable with no runtime dependencies. It performs one API call per
command: all validation, permissions and business rules stay in the console.

## Compatibility matrix

| **Consoles where tested** | Pandora FMS v8.0NG.800.4 (LTS), v8.0NG.804 (RRR) |
| --- | --- |
| **Consoles where it works** | Consoles publishing API v2. Older consoles lack some filtering features; see [Filtering features by console](#filtering-features-by-console). |
| **Systems where tested** | Linux x86-64 |
| **Executables provided for** | Linux (x86-64, ARM64), macOS (Intel, Apple silicon), Windows (x86-64) |

## Prerequisites

**An API v2 token.** Create it in the console under the user whose permissions the CLI should use.
Every command runs with that user's ACL profile.

**Network access to the console** over HTTP or HTTPS.

**The client's address allowed by the API ACL.** The console restricts API access by IP. If the
address is not on the list, every call fails with:

```
401 IP 10.0.0.5 is not in ACL list
```

That is a console setting, not a CLI one: add the address to the API ACL list in the console
configuration before continuing.

## Configure access

### Store a token

`auth login` checks the token against the console **before** writing anything. If it is rejected,
nothing is stored.

```bash
pandora-cli auth login --token <token> --url https://console.example.com/pandora_console/api/v2/
```

The URL defaults to `http://localhost/pandora_console/api/v2/`. It must point at the API root and
end in `/api/v2/`.

Credentials are written to `~/.pandora-cli/config.json` with the directory set to `0700` and the
file to `0600`. The token is stored base64-encoded, which keeps it out of casual terminal output;
the file permissions are what actually protects it. The CLI refuses to read a configuration file
whose permissions are wider than `0600`.

Set `PANDORA_CLI_HOME` to keep the configuration somewhere else.

### Several consoles

Each console is a named context.

```bash
pandora-cli auth login --token <token> --url https://prod/pandora_console/api/v2/ --context prod
pandora-cli auth login --token <token> --url https://lab/pandora_console/api/v2/  --context lab --insecure

pandora-cli auth context list
pandora-cli auth context use prod
pandora-cli user list --context lab      # one command against another console
```

`--token` and `--url` can also be passed to any command directly. Used that way the token is never
written to disk, which suits a CI job that already holds it in a secret.

### Self-signed certificates

`--insecure` skips TLS verification. It is never applied by default. Passed to `auth login` it is
remembered for that context; passed to any other command it applies to that command only.

## Verify

```bash
pandora-cli auth status
```

```
Context:  prod
URL:      https://console.example.com/pandora_console/api/v2/
Insecure: false
Config:   /home/user/.pandora-cli/config.json
Token:    valid
Probed:   2026-09-04T08:01:42Z

Capabilities:
  filter.fieldConditions   supported (--where)
  filter.multipleSearch    supported (--in)
  filter.requestedFields   supported (--fields)

Console specification: 137 operations, 22 entities (read 2026-09-04T08:01:42Z)
```

`Token: valid` means the console accepted it. The command exits non-zero if it did not.

Then read something real:

```bash
pandora-cli user list
```

```
IDUSER  FULLNAME  EMAIL              ISADMIN  DISABLED
admin   Pandora   admin@example.com  true     false

1 shown, 1 total.
```

## Understand the output

Output is a **table on a terminal** and **JSON when redirected or piped**, so scripts get parseable
output without passing a flag:

```bash
pandora-cli user list                      # table
pandora-cli user list | jq '.[].idUser'    # JSON
pandora-cli user list > users.json         # JSON
```

Force a format with `-o json`, `-o table` or `-o yaml`.

Informational lines such as `1 shown, 1 total.` appear only in table format. In JSON and YAML they
are suppressed, so piped output is always valid.

Listings are paginated by the console. `1 shown, 1 total.` reports how many rows came back and how
many exist; use `--page` and `--size` to walk a large result.

### Filtering features by console

Three filtering features depend on API support that older consoles do not have. The CLI detects
which ones the console offers when you log in, and caches the answer for that context:

| Feature | Flag |
| --- | --- |
| `fieldConditions` | `--where` |
| `requestedFields` | `--fields` |
| `multipleSearchString` | `--in` |

If a console does not support one, the command is refused locally with an explanation instead of
producing an obscure server error:

```
Error: --fields (requestedFields) is not available on this console.
The console at https://console.example.com/pandora_console/api/v2/ rejects that parameter.
```

After upgrading a console, refresh the cached answer:

```bash
pandora-cli auth status --refresh
```

## Operate

### Filtering a list

```bash
pandora-cli user list --filter isAdmin=true
pandora-cli user list --where 'fullName like admin' --sort fullName
pandora-cli user list --search backup
pandora-cli user list --in idUser=admin,root
pandora-cli user list --fields idUser,email --size 50
```

All filter flags are repeatable and combine with **AND**.

**Two different field sets apply per entity.** `--filter` accepts any field of the entity, but
`--where`, `--fields` and `--in` accept a narrower set — for `user` it is `idUser` and `fullName`
only. The two sets are not nested: an entity may accept a field for `--fields` that is not a normal
entity field. The CLI validates both locally and lists the valid names when it refuses, so read the
error rather than guessing again.

Values are converted to their JSON type: `true` and `false` become booleans, digits become numbers,
`null` becomes null. Quote to force a string:

```bash
pandora-cli tag list --filter name='"42"'
```

### Creating and changing

```bash
pandora-cli user create --set idUser=jdoe --set fullName='Jane Doe' --set password=secret
pandora-cli user update jdoe --set email=jane@example.com
pandora-cli user delete jdoe --yes
```

`--set` is repeatable. For a full payload, read JSON from a file or from standard input:

```bash
pandora-cli user create --from-file user.json
cat user.json | pandora-cli user create --from-file -
```

`--set` and `--from-file` cannot be combined.

`delete` asks for confirmation. In a non-interactive session it **refuses** instead of prompting, so
a script that forgot `--yes` fails loudly rather than deleting silently.

### Nested entities

Some entities live under a parent. Their commands take the parent identifier first:

```bash
pandora-cli report-design-page list 12
pandora-cli report-design-page-widget list 12 3
```

### Documentation and agent usage

```bash
pandora-cli docs                  # full command reference for this build
pandora-cli docs --out ref.md
```

For coding agents working in a terminal, install a usage skill describing this build:

```bash
pandora-cli skill install         # writes ~/.claude/skills/pandora-cli/SKILL.md
pandora-cli skill install --print # show it without installing
pandora-cli skill install --force # overwrite an existing one
```

Re-run it after upgrading so the skill keeps matching the executable.

### Diagnosing a call

`--verbose` traces the request line, the request body and the response status to standard error,
leaving standard output clean for piping:

```bash
pandora-cli user list --filter isAdmin=true -v -o json > users.json
```

```
→ POST https://console.example.com/pandora_console/api/v2/user/list
→ body: {"isAdmin":true}
← 200, 1834 bytes
```

## Troubleshoot

| Symptom | Cause and remedy |
| --- | --- |
| `401 ... token was rejected` | The token is wrong or expired. Re-run `auth login`. |
| `401 IP ... is not in ACL list` | The client address is not permitted by the console's API ACL. Add it in the console configuration. |
| `403 ... lacks permission` | The token is valid but the owning user's ACL profile does not allow the operation. |
| `404 ... or the API base URL is wrong` | Check `auth status`; the URL must end in `/api/v2/`. |
| `TLS verification failed` | Self-signed certificate. Re-run with `--insecure`, or store it for the context at login. |
| `has permissions 0644` | The configuration file is readable by others. Run `chmod 0600 ~/.pandora-cli/config.json`. |
| `--fields ... is not available on this console` | The console lacks that filtering feature. See [Filtering features by console](#filtering-features-by-console). |
| `unknown field "..."` | The field does not exist on that entity. The message lists the valid names. |
| `the "..." entity does not exist on this console` | The console does not publish that entity. Run `auth status --refresh` if it was upgraded. |
| `--... is required by this endpoint` | A parameter the API declares as required was not supplied. |

A command exits `0` on success and non-zero on failure, so it can be used directly in a script's
control flow.

## Reference

### Global flags

| Flag | Meaning |
| --- | --- |
| `--context <name>` | Named context to use. Defaults to the current one. |
| `--url <url>` | API base URL, overriding the context. |
| `--token <token>` | Token for this command only. Never written to disk. |
| `--insecure` | Skip TLS certificate verification. |
| `-o, --output json\|table\|yaml` | Output format. Table on a terminal, JSON otherwise. |
| `-v, --verbose` | Trace requests to standard error. |
| `--timeout <duration>` | Request timeout. Defaults to `30s`. |

### List flags

| Flag | Effect | Example |
| --- | --- | --- |
| `--filter <field>=<value>` | Field equality. | `--filter isAdmin=true` |
| `--where '<field> <op> <value>'` | Advanced condition. | `--where 'fullName like admin'` |
| `--search <text>` | Free-text search. | `--search backup` |
| `--in <field>=<v1,v2>` | Field within a list of values. | `--in idUser=admin,root` |
| `--fields <a,b,c>` | Restrict the returned fields. | `--fields idUser,email` |
| `--page <n>` | Page number. | `--page 2` |
| `--size <n>` | Rows per page. | `--size 50` |
| `--sort <field>` | Field to sort by. | `--sort fullName` |
| `--order asc\|desc` | Sort direction. | `--order desc` |

Operators accepted by `--where`: `=`, `like`, `regex`, `in`, `between`, `is_not_empty`. For a JSON
column, address a path with `--where '<field>:<jsonPath> <op> <value>'`.

### Write flags

| Flag | Effect |
| --- | --- |
| `--set <field>=<value>` | One payload field. Repeatable. |
| `--from-file <path>` | Read the whole JSON payload from a file, or `-` for standard input. |
| `--yes` | Skip the confirmation prompt on a destructive command. |

### Authentication commands

| Command | Effect |
| --- | --- |
| `auth login` | Validate a token and store it in a context. |
| `auth status` | Show the active context and verify the token. `--refresh` re-checks console features. |
| `auth context list` | List stored contexts. |
| `auth context use <name>` | Select the current context. |
| `auth logout [context]` | Remove a stored context. |

### Entities

Every entity supports the verbs listed. Run `pandora-cli <entity> --help` for its exact commands and
arguments, and `pandora-cli docs` for the full reference of the installed build.

| Entity | Covers | Verbs |
| --- | --- | --- |
| `agent-extended-data` | Extended data attached to agents | `list`, `get`, `create`, `update`, `delete` |
| `bulk-draft` | Bulk operation drafts | `list`, `get`, `delete` + 1 more |
| `bulk-queue` | Bulk operation queue | `list`, `get`, `delete` |
| `data-translation` | Data translation definitions | `list`, `get`, `create`, `update`, `delete` |
| `event` | Monitoring events | `list`, `get`, `create`, `update`, `delete` + 10 more |
| `event-filter` | Saved event filters | `list`, `get`, `create`, `update`, `delete` |
| `event-tag` | Event tags | `list`, `get`, `create`, `update`, `delete` |
| `group` | Agent groups | `list`, `get`, `create`, `update`, `delete` |
| `monitoring` | Push monitoring data | `create` |
| `pandora-itsm-inventory` | Pandora ITSM inventory | `list`, `get` |
| `profile` | ACL profiles | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource` | Report data sources | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource-agent` | Agents attached to a report data source | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource-group` | Groups attached to a report data source | `list`, `get`, `create`, `update`, `delete` |
| `report-design` | Report designs | `list`, `get`, `create`, `update`, `delete` + 5 more |
| `report-design-page` | Pages of a report design | `list`, `get`, `create`, `update`, `delete` |
| `report-design-page-widget` | Widgets on a report design page | `list`, `get`, `create`, `update`, `delete` |
| `report-design-report` | Report entries of a report design | `list`, `get`, `create`, `update`, `delete` |
| `report-design-template` | Templates of a report design | `list`, `get`, `create`, `update`, `delete` |
| `siem-group` | SIEM groups | `list`, `get`, `create`, `update`, `delete` |
| `siem-rule` | SIEM rules | `list`, `get`, `create`, `update`, `delete` + 4 more |
| `tag` | Module tags | `list`, `get`, `create`, `update`, `delete` |
| `token` | API tokens | `list`, `get`, `create`, `update`, `delete` |
| `user` | Console users and their profile assignments | `list`, `get`, `create`, `update`, `delete` + 5 more |
| `widget` | Dashboard widgets | `list`, `get` |

The entities an executable knows are those of the API version it was built against. A console newer
than the executable may publish more; `pandora-cli auth status` reports what the console itself
publishes.

### Files and environment

| Path or variable | Purpose |
| --- | --- |
| `~/.pandora-cli/config.json` | Stored contexts and tokens. Mode `0600`. |
| `~/.pandora-cli/schema-<context>.json` | Cached description of that console's API. |
| `PANDORA_CLI_HOME` | Overrides the configuration directory. |
| `CLAUDE_CONFIG_DIR` | Overrides where `skill install` writes. |
