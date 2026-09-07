# Pandora CLI

## Introduction

**Ver**. 07-09-2026

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
| **Consoles where it works** | Consoles publishing API v2. Whether a filter parameter is accepted is decided by the console per entity, at request time; older consoles may reject more of them. See [Filtering features by entity](#filtering-features-by-entity). |
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

Console specification: 137 operations, 22 entities (read 2026-09-07T08:01:42Z)
```

`Token: valid` means the console accepted it. The command exits non-zero if it did not. With `-o json`
the output is exactly five values — `context`, `url`, `insecure`, `config` and `token` — without the
informational summary line shown above in table format.

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

### Filtering features by entity

`--where`, `--fields` and `--in` map to API parameters that each console entity implements on its
own: acceptance is **per entity**, not per console. `/user/list` may accept `fieldConditions` while
`/event/list` rejects it. The CLI keeps no per-console capability cache: it always sends the request
and the console answers.

| Feature | Flag |
| --- | --- |
| `fieldConditions` | `--where` |
| `requestedFields` | `--fields` |
| `multipleSearchString` | `--in` |

If the entity does not accept the parameter, the console rejects the request with
`400 Field: ... is not a valid parameter` and the CLI explains what happened, naming the flag that
sent the parameter. The flag stays usable on the entities that do accept it; only the rejected
request fails:

```
Error: POST event/list failed: 400 Field: fieldConditions is not a valid parameter
--where (fieldConditions) is not available on this console.
The console at https://console.example.com/pandora_console/api/v2/ rejects that parameter.
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

All filter flags are repeatable and combine with **AND**. When the field's schema declares it as an
array, repeating `--filter` for the same field accumulates into one array parameter instead of
ANDing: `--filter severity=4 --filter severity=2` sends `{"severity":[4,2]}`.

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

When the schema declares a field as an **array** — for example `severity` on `event-filter` or
`wildcardAgents` on `report-datasource` — a `--set` value is serialized as an array with one
element, and repeating the flag accumulates elements into that array.

`--from-file` accepts a JSON **array** as the whole body, not only an object. Endpoints whose body is
a list require it, such as `pandora-cli monitoring create` below. One edge case: the schema may
declare a scalar where the console endpoint expects an array (a documented mismatch, for example
`position` on `report-design-page-widget`); write the array into the file and send it with
`--from-file`.

`delete` asks for confirmation. In a non-interactive session it **refuses** instead of prompting, so
a script that forgot `--yes` fails loudly rather than deleting silently.

### Pushing monitoring data

`pandora-cli monitoring create` pushes agent data into Pandora FMS. Its body is an **array** of
payloads with snake_case keys — `agent_data` and `module_data` — not the `Monitoring` object the
console's API documentation shows. That console annotation is wrong and will be corrected; until
then the array shape below is the one that works:

```bash
cat > payload.json << 'EOF'
[
  {
    "agent_data": {"agent_name": "web1", "address": "10.0.0.5", "interval": 300},
    "module_data": [
      {"name": "cpu_usage", "data": 12.5},
      {"name": "mem_used", "datalist": [{"value": 2048, "timestamp": "2026/09/07 11:00:00"}]}
    ]
  }
]
EOF
pandora-cli monitoring create --from-file payload.json
```

The agent is created if it does not exist. `agent_name` is required; other `agent_data` keys are
optional. A payload may also carry `events`, `inventory_data`, `log_data`, `trap_data`,
`discovery_data` and `cmd_data`. Re-sending the same agent, module and timestamp updates the
existing value instead of duplicating it.

### Nested entities

Some entities live under a parent. Their commands take the parent identifier first:

```bash
pandora-cli report-design-page list 12
pandora-cli report-design-page-widget list 12 3
```

### Inspecting the console's API

`spec` reads the API description the console publishes about itself, so you can see which fields an
entity accepts without opening the console's `swagger.json`:

```bash
pandora-cli spec list                # schemas the console publishes
pandora-cli spec show EventFilter    # one schema, allOf resolved: types, enums, readOnly
pandora-cli spec raw                 # the console's full swagger.json
```

For `create` and `update`, ask for the entity's schema with `spec show <Entity>`; for the fields a
list filter accepts, ask for the matching filter schema with `spec show <Entity>Filter`. `allOf`
composition is resolved, so inherited fields appear as the schema's own properties. Schema names are
the ones the console publishes — `EventFilter`, `EventFilterFilter`, `ReportDataSource` — which are
not the CLI's hyphenated entity names; `spec list` shows the exact names, and `spec show` suggests
the closest match if you mistype one. Output follows the usual `-o json`, `-o table` or `-o yaml`
format.

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
| `--fields ... is not available on this console` | The entity does not implement that filter parameter; the console rejected the request and the CLI named the flag that sent it. See [Filtering features by entity](#filtering-features-by-entity). |
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
| `auth status` | Show the active context, verify the token and report the console's published specification. `--refresh` re-reads that specification. |
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
