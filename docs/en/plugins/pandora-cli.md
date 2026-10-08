# Pandora CLI

*Article last updated: 2026-10-08.*

## Introduction

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

### AI session correlation

Use an optional AI session ID to attach correlation metadata to API v2 requests. Save it in a
named context when logging in. Tokens passed as command arguments may appear in shell history or
the operating system process list.

```bash
pandora-cli auth login --token '<API_TOKEN>' --url https://console.example.com/pandora_console/api/v2/ --context prod --ai-session-id ai-session-example-001
pandora-cli user list --context prod
```

After a successful login, the first command stores `ai_session_id` in the destination context in
`~/.pandora-cli/config.json`. The later command reuses that ID without repeating the flag.

Resolution order is **explicit `--ai-session-id` (including an empty value) → selected/current
context `ai_session_id` → absent**. A nonempty ID sends `X-Pandora-AI-Session` on every API v2
request, including authentication and the console specification fetch. An absent or empty ID omits
the header. Control characters are rejected.

Login and other commands treat overrides differently:

| Invocation | Effect on the stored ID |
| --- | --- |
| Successful `auth login --ai-session-id <id>` | Saves the explicit ID in the destination context. |
| Successful `auth login` without the flag | Preserves that context's prior ID. |
| Successful `auth login --ai-session-id=` | Clears that context's stored ID; the empty field is omitted from JSON. |
| Failed login or invalid ID | Writes nothing; the existing configuration remains unchanged. |
| Any other command with `--ai-session-id <id>` or `--ai-session-id=` | Overrides or disables the header for that invocation only; never changes the stored ID. |

For example, disable the header for one read without clearing the saved ID, or clear it with a
successful login:

```bash
pandora-cli user list --context prod --ai-session-id=
pandora-cli auth login --token '<API_TOKEN>' --url https://console.example.com/pandora_console/api/v2/ --context prod --ai-session-id=
```

The ID is correlation metadata, not a credential: it does not authenticate the caller or grant
permissions. Sending the header does not establish that the console records or displays it in an
audit log.

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

Console specification: 282 operations, 46 entities (read 2026-09-22T09:12:37Z)
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
many exist; use `--page` and `--size` to walk a large result. Pagination is **1-based**: `--page 1`
is the first page. `--size` alone also returns the first page, because the console ignores a page
size without a page number on some endpoints; the CLI sends both.

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
ANDing: `--filter severity=4 --filter severity=2` sends `{"severity":[4,2]}`. An explicit `null`
value is the exception: it is sent as a plain null (never as `[null]`), so it clears the field
regardless of position among the repeated flags.

**Two different field sets apply per entity.** `--filter` accepts any field of the entity, but
`--where`, `--fields` and `--in` accept a narrower, per-entity set — for `agent-secondary-group` it
is just `idAgent` and `idGroup`; for `user` it is a fixed subset of 20 fields out of the entity's 81.
The two sets are not nested: an entity may accept a field for `--fields` that is not a normal entity
field. The CLI validates both locally and lists the valid names when it refuses, so read the error
rather than guessing again. Several entities — including `group`, `tag`, `profile`, `token` and
`data-translation` — accept a wider `--where`/`--fields`/`--in` field set than earlier builds; run
`pandora-cli <entity> --help` to see the exact list for the installed build.

`agent list` additionally accepts module counters — `criticalCount`, `warningCount`,
`unknownCount`, `normalCount`, `notinitCount`, `totalCount` and `firedCount` — in `--fields`,
`--where` and `--in`, alongside the entity's own columns:

```bash
pandora-cli agent list --fields idAgent,alias,criticalCount,totalCount
```

The new entities follow the same rule. `policy` accepts `applyToSecondaryGroups`,
`createLinkedModules`, `description`, `forceApply`, `idGroup`, `idPolicy`, `name` and `status`;
`collection` accepts `description`, `idCollection`, `idGroup`, `name`, `shortName` and `status`;
`service` accepts `asynchronous`, `autoCalculate`, `cascadeProtection`, `cpsInhibit`, `critical`,
`description`, `evaluateSla`, `idGroup`, `idService`, `isFavourite`, `name`, `quiet`,
`serviceInterval`, `slaInterval`, `status`, `unknownAsCritical`, `utimestamp` and `warning`. The
`token` set now includes `isPandoraAi`, next to `idToken`, `idUser`, `label`, `lastUsage` and
`validity`. `--filter` still accepts every other field of each entity.

`module-alert list` takes an optional `idAgentModule`. With it, it lists that module's alerts, as
before. Without it, it lists every module alert on the console:

```bash
pandora-cli module-alert list
pandora-cli module-alert list --where 'timesFired = 1'
```

Module alerts also expose a `status` field — `fired`, `notFired`, `disabled` or `allEnabled` —
usable with `--filter` (`--filter status=fired`), but not with `--where`, `--fields` or `--in`.

`event` is the one exception: the CLI does not validate `--where`, `--fields` or `--in` locally for
it. It sends whatever is passed and lets the console decide, because the console's event listing
does not implement `fieldConditions`, `requestedFields` or `multipleSearchString` for any field. A
rejection therefore always comes back from the console, explained the same way described in
[Filtering features by entity](#filtering-features-by-entity).

`event list`'s `dateRange` filter takes a JSON string, not a `"<start> - <end>"` string:

```bash
pandora-cli event list --filter 'dateRange={"preset":{"value":"last_24_hours"}}'
pandora-cli event list --filter 'dateRange={"start":{"mode":"relative","value":1,"unit":"hours"},"end":{"mode":"now"}}'
```

The older `"<start> - <end>"` string now fails with `400 Invalid date range format. Must be valid
JSON`.

In Windows PowerShell 5.1 (and PowerShell 7 before 7.3), the double quotes inside an argument are
removed before it reaches `pandora-cli`, so the console receives invalid JSON and answers with the
same `400`. Escape each inner double quote with a backslash:

```powershell
pandora-cli event list --filter 'dateRange={\"preset\":{\"value\":\"last_24_hours\"}}'
```

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

`--set` values are converted to their JSON type exactly like filter values. A string field whose
value looks like a number is therefore sent as a number: `--set permissions=0755` sends the number `755`.
Quote the value to force a string, or send the payload with
`--from-file`:

```bash
pandora-cli <entity> <verb> --set permissions='"0755"'
```

When the schema declares a field as an **array** — for example `severity` on `event-filter` or
`wildcardAgents` on `report-datasource` — a `--set` value is serialized as an array with one
element, and repeating the flag accumulates elements into that array. As with `--filter`, an
explicit `null` is sent as a plain null and clears the accumulated array.

`--from-file` accepts a JSON **array** as the whole body, not only an object. Endpoints whose body is
a list require it, such as `pandora-cli monitoring create` below. A leading UTF-8 BOM in the file is
tolerated, so files written by Windows editors work as-is. One edge case: the schema may
declare a scalar where the console endpoint expects an array (a documented mismatch, for example
`position` on `report-design-page-widget`); write the array into the file and send it with
`--from-file`.

`delete` asks for confirmation. In a non-interactive session it **refuses** instead of prompting, so
a script that forgot `--yes` fails loudly rather than deleting silently.

Some entities enforce server-side rules that are not visible in their field list: `agent create`
needs a real group — `idGroup=0` is rejected with `400 Agent group is missing`; the console assigns
the agent's `name` itself regardless of the payload, so use `alias` for the label you actually
control; `module create` needs `idModule` (the module's server type) together with `idModuleType`,
not only the columns listed under `--where`/`--fields`/`--in`; and a non-admin user created with
`user create` needs at least one profile assigned with `user profile add` before it can log in; an
`event-alert-rule` created with `event-alert-rule create` needs the alert's first ordered rule to
have `operation=NOP` — the console rejects any other operation on that first rule.
`module force-check` requests an immediate check of an agent module; the check itself completes out
of band, so a successful call returns `202` with no body. The console rejects it with `400` for
module types that do not support an immediate check, such as data-push modules. The optional
`--serverId` flag targets a federated node's module from a metaconsole.

### Pushing monitoring data

`pandora-cli monitoring create` pushes agent data into Pandora FMS. Its body is an **array** of
payloads with snake_case keys — `agent_data` and `module_data`:

```bash
cat > payload.json << 'EOF'
[
  {
    "agent_data": {"agent_name": "web1", "address": "10.0.0.5", "interval": 300},
    "module_data": [
      {"name": "cpu_usage", "type": "generic_data", "data": 12.5},
      {"name": "mem_used", "type": "generic_data", "datalist": [{"value": 2048, "timestamp": "2026/09/07 11:00:00"}]}
    ]
  }
]
EOF
pandora-cli monitoring create --from-file payload.json
```

The agent is created if it does not exist. `agent_name`, `address` and `interval` are required;
the console rejects the request without any of them. Other `agent_data` keys are optional. Every entry in
`module_data` needs a `type` such as `generic_data`; the console rejects the request without it. A payload may also carry
`events`, `inventory_data`, `log_data`, `trap_data`, `discovery_data` and `cmd_data`. Re-sending the
same agent, module and timestamp updates the existing value instead of duplicating it.

### Nested entities

Some entities live under a parent. Their commands take the parent identifier first:

```bash
pandora-cli report-design-page list 12
pandora-cli report-design-page-widget list 12 3
```

Nested list commands that read with a filter body also take payload flags: their `--set` fields are
serialized the same way, so a field the endpoint declares as an array — like `requestedFields` —
accumulates from repeated flags:

```bash
pandora-cli user profile list admin --set requestedFields=idUserProfile
```

`user profile get` and `user profile remove` take that same `idUserProfile` — the assignment's own
id, not the profile's id (`idProfile`). `user profile add` is unchanged and still takes `idProfile`:

```bash
pandora-cli user profile get operator1 3
pandora-cli user profile remove operator1 3
```

**Breaking change**: earlier builds took `idProfile` for `user profile get`. When the same profile
is assigned to a user on more than one group, each assignment has its own `idUserProfile`.

### Policies, collections and services

`policy`, `collection` and `service` group part of their commands in **child groups**. The syntax is
`<entity> <group> <verb> <ids...>`, and `pandora-cli <entity> --help` lists the groups of an entity:

```bash
pandora-cli policy module list 7
pandora-cli collection file upload 3 --file ./a.conf
pandora-cli service element add 2 --set description='Frontend CPU' --set idAgenteModulo=42
```

The groups are `policy agent`, `policy alert`, `policy alert-action`, `policy collection`,
`policy group`, `policy log-module`, `policy module`, `policy plugin` and `policy queue`;
`collection file`, `collection folder` and `collection agent`; and `service element`. Collections
are also assigned from the agent side with `agent collection list`, `agent collection add` and
`agent collection remove`.

**Removing marks, it does not delete.** In a policy, `remove`, `delete` and `bulk-delete` on a child
(agent, alert, collection, group, log module, module or plugin) only mark it `pendingDelete`. The
removal takes effect when the policy queue is applied, and `restore` undoes the mark before that
happens. `policy alert-action remove` and `policy queue delete` are not marked: they act at once.

**Purging and the queue are asynchronous.** `policy purge` and the `policy queue` operations enqueue
work and return without waiting. A policy cannot be deleted while queue entries are pending: check
`policy queue list` (or `policy queue summary`) and use `policy queue clear`, or wait, before
deleting it. Nor can it be deleted while it still has assigned agents: run `policy purge` and wait
for the queue to finish first.

**Bulk plugin operations need a JSON array.** `policy plugin bulk-delete`, `bulk-disable`,
`bulk-enable` and `bulk-restore` take a top-level array of plugin ids, which `--set` cannot build.
Send it from standard input or a file with `--from-file`; the result reports the successes and
errors per plugin:

```bash
echo '[4,5]' | pandora-cli policy plugin bulk-enable 7 --from-file -
```

Policy children are identified by their own id, which follows the policy id on the command line
(`<idPolicy> <idPolicyModule>`, `<idPolicy> <idPolicyAgent>`, and so on). The options a user needs
most:

| Group | Verbs | Main options |
| --- | --- | --- |
| `policy agent` | `list`, `get`, `add`, `remove`, `restore` | `add`: `--set idAgent=<id>`. |
| `policy group` | `list`, `get`, `add`, `remove`, `restore` | `add`: `--set idGroup=<id>`. |
| `policy collection` | `list`, `available`, `get`, `add`, `remove`, `restore` | `add`: `--set idCollection=<id>`. `available` lists the collections not linked yet. |
| `policy module` | `list`, `get`, `create`, `update`, `delete`, `enable`, `disable`, `restore` | `create`: `--set name=...`, `--set moduleType=...`, `--set idModule=<id>` and `--set idModuleType=<id>`. |
| `policy log-module` | `list`, `get`, `create`, `update`, `delete`, `enable`, `disable`, `restore` | `create`: `--set collectorMode=...`, `--set moduleName=...`, `--set source=...` and `--set sourceType=...`. |
| `policy plugin` | `list`, `get`, `create`, `update`, `delete`, `enable`, `disable`, `restore`, `bulk-delete`, `bulk-disable`, `bulk-enable`, `bulk-restore` | `create`: `--set pluginExecution=<command>`. The `bulk-*` verbs take a JSON array (see above). |
| `policy alert` | `list`, `get`, `create`, `update`, `delete`, `restore` | `create`: `--set idPolicyModule=<id>` and `--set idAlertTemplate=<id>`. `update`: `--set disabled=true`. |
| `policy alert-action` | `list`, `add`, `remove` | Take `<idPolicy> <idPolicyAlert>`. `add`: `--set idAlertAction=<id>`, `--set firesMin=<n>` and `--set firesMax=<n>`. `remove` also takes `<idPolicyAlertAction>`. |
| `policy queue` | `list`, `get`, `summary`, `add`, `apply-pending`, `clear`, `delete` | `add`: `--set operation=apply` and `--set idAgent=<id>`. `apply-pending` queues the pending changes. `clear` and `delete` ask for confirmation unless `--yes` is given. |

`policy copy` takes `--set name=...` and `--set idGroup=<id>` for the new policy; `policy purge`
takes no options.

```bash
pandora-cli policy agent add 7 --set idAgent=42
pandora-cli policy queue apply-pending 7
pandora-cli policy queue summary 7
```

**Fixed after creation.** The `moduleType`, `idModule` and `idModuleType` of a policy module cannot
be changed once it exists; create a new policy module instead.

**Collections need a remote agent.** Assigning a collection to an agent (`agent collection add`;
`collection agent list` shows the result) requires an agent with remote configuration (`remote=1`)
that is available on the console. Otherwise the console answers
`Agent remote configuration is unavailable`, including for an agent that has `remote=1` but no
remote configuration yet. The assignment is only recorded in the agent's remote configuration; run `collection apply` after changing the files of a collection so that agents pick
up the new package.

**`isPandoraAi` on `token`** can only be set when the token is created.

### Transferring files

Two commands of `collection` move file contents. They use their own flags, and `--from-file` does
not apply to them.

**Upload** (`collection file upload`) sends the request as `multipart/form-data`. Pass each file with
`--file <path>`, or with `--file <field>=<path>` to name the form field; the flag is repeatable and at
least one is required. The text form fields (`folder`, `decompress`, `overwrite` and `permissions`)
go in `--set field=value` and are sent as strings, so no extra quoting is needed there. File
contents are never printed by `-v`.

```bash
pandora-cli collection file upload 3 --file ./a.conf
```

**Download** (`collection file download`) returns raw bytes, so `--output-file <path>` is required;
`--output-file -` writes to standard output. An existing file is replaced only with `--force`, and a
failed download leaves no partial file. `--output-file` is the destination: `-o/--output` still
selects the output format.

```bash
pandora-cli collection file download 3 --path a.conf --output-file ./a.conf
pandora-cli collection file download 3 --path a.conf --output-file ./a.conf --force
```

The other commands of the `collection` file groups take the collection id and these options.
`--path` is always relative to the collection, never an absolute server path.

| Command | Options |
| --- | --- |
| `collection file list` | `--set folder=<path>` is optional; omitting it lists the root. |
| `collection file read` | `--path <path>` (required). Prints the text content of the file. |
| `collection file create` | `--set path=<path>` (required) and `--set content=<text>`; without `content` an empty file is created. |
| `collection file update` | `--set path=<path>` and `--set content=<text>` replace the content of an existing file. |
| `collection file delete` | `--path <path>` (required) and `--yes`. |
| `collection folder create` | `--set path=<path>` (required); `--set recursive=true` also creates missing parent folders. |
| `collection folder delete` | `--path <path>` (required) and `--yes`. The folder must be empty. |
| `collection agent list` | No options. Lists the agents assigned to the collection. |
| `collection apply` | No options. Generates the collection package again. |

```bash
pandora-cli collection folder create 3 --set path=scripts --set recursive=true
pandora-cli collection file create 3 --set path=scripts/check.sh --set content='echo ok'
pandora-cli collection file read 3 --path scripts/check.sh
```

### Module graphs

`module graph` asks the console to render a graph of an agent module. The options (`period`,
`graphType`, `width`, `height` and others) travel in the body as `--set` fields. The response is not
a binary stream: it carries the image base64-encoded in its `graph` field, with its `mimeType`
(`image/png` or `image/jpeg`) and `encoding` (`base64`) next to it. `period` is expressed in seconds
(minimum 300; the default is one day).

```bash
pandora-cli module graph 12 --set period=3600 -o json | jq -r .graph | base64 -d > graph.png
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

Use one correlation ID per AI session and rotate it when starting a new session. Save it with
`auth login --ai-session-id <id>` for reuse in the destination context. On other commands,
`--ai-session-id <id>` is a transient override and `--ai-session-id=` disables the header for that
invocation without clearing the stored ID. Later calls without the flag reuse the saved ID. See
the AI session correlation section for login save and clear behavior.

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
| `--... is required by this endpoint` | A parameter the API declares as required was not supplied (for example `--path` in `collection file download`). |
| A policy cannot be deleted | The policy still has pending queue entries or assigned agents. Check `policy queue list` and use `policy queue clear` or wait; run `policy purge` to unassign its agents. |
| A policy child still appears after `remove` | The removal only marks it `pendingDelete` until the policy queue is applied. Use `restore` to undo it. |
| A collection cannot be assigned to an agent (`Agent remote configuration is unavailable`) | The agent needs remote configuration (`remote=1`) available on the console. |
| A value such as `0755` arrives as `755` | `--set` converts numeric-looking values. Use `--set permissions='"0755"'` or `--from-file`. |

A command exits `0` on success and non-zero on failure, so it can be used directly in a script's
control flow.

## Reference

### Global flags

| Flag | Meaning |
| --- | --- |
| `--context <name>` | Named context to use. Defaults to the current one. |
| `--url <url>` | API base URL, overriding the context. |
| `--token <token>` | Token for this command only. Never written to disk. |
| `--ai-session-id <id>` | Optional correlation ID; overrides the selected/current context. Successful `auth login` saves it; other commands use it transiently. `--ai-session-id=` omits the header and clears the stored ID only on successful login. |
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
| `--page <n>` | Page number, 1-based (`--page 1` is the first page). | `--page 2` |
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

### File transfer flags

| Flag | Effect |
| --- | --- |
| `--file <path>` or `--file <field>=<path>` | File to upload with a multipart command (`collection file upload`). Repeatable; at least one is required. |
| `--output-file <path>` | Destination of a raw-bytes command (`collection file download`). Required; `-` writes to standard output. |
| `--force` | Replace an existing `--output-file`. |

### Authentication commands

| Command | Effect |
| --- | --- |
| `auth login` | Validate a token and store it in a context. On success, an explicit `--ai-session-id` saves the ID in that context, omission preserves the prior ID, and `--ai-session-id=` clears it. Failed login or an invalid ID writes nothing. |
| `auth status` | Show the active context, verify the token and report the console's published specification. `--refresh` re-reads that specification. |
| `auth context list` | List stored contexts. |
| `auth context use <name>` | Select the current context. |
| `auth logout [context]` | Remove a stored context. |

### Entities

Every entity supports the verbs listed. Run `pandora-cli <entity> --help` for its exact commands and
arguments, and `pandora-cli docs` for the full reference of the installed build.

| Entity | Covers | Verbs |
| --- | --- | --- |
| `agent` | Monitoring agents | `list`, `get`, `create`, `update`, `delete` + 4 more (`status` and the `collection` group) |
| `agent-extended-data` | Extended data attached to agents | `list`, `get`, `create`, `update`, `delete` |
| `agent-secondary-group` | Secondary groups of an agent | `list`, `create`, `delete` |
| `alert-action` | Alert actions | `list`, `get`, `create`, `update`, `delete` + 1 more |
| `alert-calendar` | Alert calendars | `list`, `get`, `create`, `update`, `delete` |
| `alert-command` | Alert commands | `list`, `get`, `create`, `update`, `delete` + 1 more |
| `alert-special-day` | Special days of an alert calendar | `list`, `get`, `create`, `update`, `delete` |
| `alert-template` | Alert templates | `list`, `get`, `create`, `update`, `delete` + 1 more |
| `bulk-draft` | Bulk operation drafts | `list`, `get`, `delete` + 1 more |
| `bulk-queue` | Bulk operation queue | `list`, `get`, `delete` |
| `collection` | File collections distributed to agents | `list`, `get`, `create`, `update`, `delete` + 11 more (`apply` and the `file`, `folder` and `agent` groups) |
| `dashboard` | Dashboards | `list`, `get`, `create`, `update`, `delete` |
| `dashboard-widget` | Widgets placed on a dashboard | `list`, `get`, `create`, `update`, `delete` |
| `data-translation` | Data translation definitions | `list`, `get`, `create`, `update`, `delete` |
| `event` | Monitoring events | `list`, `get`, `create`, `update`, `delete` + 12 more |
| `event-alert` | Event alerts | `list`, `get`, `create`, `update`, `delete` |
| `event-alert-action` | Actions of an event alert | `list`, `get`, `create`, `update`, `delete` |
| `event-alert-rule` | Rules that trigger an event alert | `list`, `get`, `create`, `update`, `delete` |
| `event-filter` | Saved event filters | `list`, `get`, `create`, `update`, `delete` |
| `event-tag` | Event tags | `list`, `get`, `create`, `update`, `delete` |
| `group` | Agent groups | `list`, `get`, `create`, `update`, `delete` |
| `module` (alias `agent-module`) | Agent modules | `list`, `get`, `create`, `update`, `delete` + 2 more (`force-check`, `graph`) |
| `module-alert` | Alerts assigned to an agent module | `list`, `get`, `create`, `update`, `delete` |
| `module-alert-action` | Actions fired by an agent module alert | `list`, `get`, `create`, `update`, `delete` |
| `module-data` | Historical data of an agent module | `list`, `get` + 1 more |
| `module-group` | Module groups | `list`, `get`, `create`, `update`, `delete` |
| `module-state` | Current polling state of agent modules | `list`, `get` |
| `module-tag` | Tags attached to an agent module | `list`, `get`, `create`, `delete` |
| `module-type` | Module types | `list`, `get` |
| `monitoring` | Push monitoring data | `create` |
| `pandora-itsm-inventory` | Pandora ITSM inventory | `list`, `get` |
| `policy` | Policies applied to agents | `list`, `get`, `create`, `update`, `delete` + 62 more (`copy`, `purge` and the `agent`, `alert`, `alert-action`, `collection`, `group`, `log-module`, `module`, `plugin` and `queue` groups) |
| `profile` | ACL profiles | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource` | Report data sources | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource-agent` | Agents attached to a report data source | `list`, `get`, `create`, `update`, `delete` |
| `report-datasource-group` | Groups attached to a report data source | `list`, `get`, `create`, `update`, `delete` |
| `report-design` | Report designs | `list`, `get`, `create`, `update`, `delete` + 5 more |
| `report-design-page` | Pages of a report design | `list`, `get`, `create`, `update`, `delete` |
| `report-design-page-widget` | Widgets on a report design page | `list`, `get`, `create`, `update`, `delete` |
| `report-design-report` | Report entries of a report design | `list`, `get`, `create`, `update`, `delete` |
| `report-design-template` | Templates of a report design | `list`, `get`, `create`, `update`, `delete` |
| `service` | Services | `list`, `get`, `create`, `update`, `delete` + 5 more (the `element` group) |
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

Optional field in each context in `config.json`:

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `ai_session_id` | No | Absent | Correlation ID reused when `--ai-session-id` is omitted. A nonempty value sends `X-Pandora-AI-Session`; an empty value omits the header. Successful login can save or clear it; an empty field is omitted from the saved JSON. Existing contexts without this field need no change. |
