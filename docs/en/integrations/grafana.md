# Grafana

*Article last updated: 2026-10-26.*

## What it does

The Grafana addon is a **data source plugin for Grafana**. It is not a Pandora
FMS monitoring plugin: it is installed inside Grafana, it runs no process on a
Pandora FMS server, and it creates no agents and no modules. It adds
**Pandorafms Grafana** to the Grafana data source list, so Grafana panels can
plot the history of numeric Pandora FMS modules.

The data comes from the **Grafana API extension of the Pandora FMS console**,
located under `pandora_console/extensions/grafana`. The addon stores the base
URL of that extension plus a Pandora FMS user and password, asks the extension
which groups, agents and modules that user can see, and then requests the values
of one module for the time range of each panel.

Two execution paths use the configured data source:

- **Panels query from the Grafana web client.** The browser of each Grafana user
  sends the requests to the Pandora FMS console, so the browser — not only the
  Grafana server — must be able to reach it.
- **Alert rules are evaluated by the Grafana server.** The server must reach the
  console too, and the server-side path of this version does not receive data
  (see [Alert rules](#alert-rules)).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that its integrations are compatible with Pandora FMS NG 784 and later versions |
| Grafana `10.0.3` or later | `Required` | The plugin declares `grafanaDependency` `>=10.0.3` |
| A Pandora FMS node console with the Grafana API extension available | `Required` | The addon appends `/search` and `/query` to the configured extension URL, and the extension answers `403` on a metaconsole node |
| A Pandora FMS user with the read-agents privilege (`AR`) | `Required` | Both extension endpoints check that privilege before returning any group |
| Grafana versions above the declared minimum | `Not validated` | No Grafana version matrix is recorded for this addon |
| Operating system of the Grafana host | `Not validated` | The addon runs inside Grafana; no operating system is recorded |

The Pandora FMS version, the Grafana version and the node console are
installation requirements, not compatibility statements about other versions.

### Requirements

#### On the Pandora FMS side

1. **A node console, not the Metaconsole.** The extension answers `403` when it
   runs on a metaconsole node. Point the data source at the node console that
   stores the agents you want to plot.
2. **The Grafana API extension served by that console.** It is part of the
   console directory (`pandora_console/extensions/grafana`) and needs no separate
   installation on the Pandora FMS side. It answers at
   `https://<PANDORA_FMS_URL>/pandora_console/extensions/grafana/`.
3. **A Pandora FMS user with the read-agents privilege (`AR`)** and its
   password. The extension returns no data when the user does not hold that
   privilege, and only the groups where the user holds it.
4. **A CORS origin that allows the Grafana URL.** The extension sends
   `Access-Control-Allow-Origin` with the value of
   **Setup → General → Security**, field **Grafana Access-Control-Allow-Origin**.
   The default is `*`, which allows any origin. Set the origin of the Grafana
   server — scheme, host and port — to narrow it.

#### On the Grafana side

1. **Grafana `10.0.3` or later.**
2. **Write access to the Grafana plugins directory and to `grafana.ini`**, plus
   permission to restart Grafana. In the Linux packages the plugins directory is
   `/var/lib/grafana/plugins`.
3. **The plugin loaded as an unsigned plugin** (see
   [Allow the unsigned plugin](#allow-the-unsigned-plugin)).

#### Network

- The browser of every Grafana user that opens a dashboard must reach the
  Pandora FMS console.
- The Grafana server must reach the console to evaluate alert rules.

### Install the data source

1. Download `pandorafms.grafana.1.0.zip` from the
   [Marketplace entry](https://marketplace.pandorafms.com/entries/pandorafms.grafana).
   The download is limited to licensed users.
2. Extract the archive inside the Grafana plugins directory, so that the plugin
   folder sits directly under it:

```bash
cd /var/lib/grafana/plugins
sudo unzip /path/to/pandorafms.grafana.1.0.zip
```

3. Restart Grafana so that it loads the plugin.

<!-- SCREENSHOT NEEDED: Grafana data source list after installation, showing the Pandorafms Grafana data source type. -->

### Allow the unsigned plugin

The plugin is not signed, so Grafana loads it only when its identifier is listed
as allowed. Add the key to `/etc/grafana/grafana.ini`:

```ini
[plugins]
allow_loading_unsigned_plugins = "pandorafms-pandorafmsgrafana-datasource"
```

When the key already lists other plugins, add this identifier to the
comma-separated list. Restart Grafana again after the change.

`pandorafms-pandorafmsgrafana-datasource` is the data source plugin identifier
and must match exactly. Without it, Grafana does not load the plugin and
**Pandorafms Grafana** does not appear in the data source list.

## Configure

### Create the data source

1. In Grafana open **Connections → Data sources** and select **Add data source**.
2. Choose **Pandorafms Grafana**.
3. Fill in the three fields:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| **Pandora extension** | Yes | — | Base URL of the Pandora FMS Grafana API extension, with the scheme and without a trailing slash or endpoint suffix: `https://<PANDORA_FMS_URL>/pandora_console/extensions/grafana`. The addon appends `/search` and `/query`. |
| **Pandora user** | Yes | — | Pandora FMS user with the `AR` privilege. Every Grafana user queries with this identity. |
| **Password** | Yes | — | Password of that user. It is stored in the data source JSON settings, not in Grafana's encrypted secure fields, because the browser sends it with every request. |

4. Select **Save & Test**. The test does not contact Pandora FMS (see
   [Verify](#verify)).

<!-- SCREENSHOT NEEDED: Pandorafms Grafana data source settings with a lab extension URL, a user and a masked password, no real credentials. -->

Notes:

- Use an `https` extension URL whenever the console is served over TLS. If
  Grafana is served over HTTPS, the browser blocks a plain `http` extension URL
  as mixed content.
- Any Pandora FMS user with the `AR` privilege works; it does not need
  administrator rights. It does need to see every group whose modules the
  dashboards must show, because the group list only contains groups where the
  user holds `AR`.

### Build a panel query

1. Create a dashboard, add a panel and select **Pandorafms Grafana** in
   **Query**.
2. Choose **Group**, then **Agent**, then **Module**. The lists narrow in that
   order, and **Module** stays empty until an **Agent** is selected.
3. The panel shows one series per query.

| Field | Default | Description |
|-------|---------|-------------|
| **Label** | Empty | Not used. The addon does not send it, and the series keeps the module name. |
| **Tip** | Unchecked | Full-scale switch. Checked, Pandora FMS returns the stored samples. Unchecked, it returns compacted values (averages) and the series name ends in ` (avg)`. |
| **Group** | Empty | Narrows the agent list. `All` (value `0`) lists every agent. Only groups where the data source user holds `AR` appear. |
| **Agent** | Empty | Narrows the module list to the enabled agents of the selected group; with `All`, to every enabled agent. |
| **Module** | Empty | Module to plot: enabled, non-string modules of the selected agent. The module identifier is what the request carries. |

- Only **Module** decides the data. The extension reads the module identifier and
  ignores the agent value.
- Changing **Group** or **Agent** does not clear the previous **Agent** or
  **Module**. The panel keeps querying the old module until you choose a new one,
  so re-select the module after narrowing the lists.
- Every change in the editor reloads the three lists in full, and a change of
  **Tip**, **Group**, **Agent** or **Module** also runs the query. On
  installations with many groups, agents or modules this makes the editor
  slower.
- The data source returns numeric values without unit metadata. Set the unit of
  the panel to match the module.
- To compare modules, add one query per module to the same panel.

<!-- SCREENSHOT NEEDED: Grafana panel query editor with the Pandorafms Grafana data source and the Label, Tip, Group, Agent and Module fields filled with lab values. -->

### Alert rules

The data source declares alerting support, so a Grafana alert rule can use a
Pandora FMS query. Grafana evaluates alert rules on the server, not in the
browser. In this version the server-side path does not carry the extension URL
and the password stored in the form, so a rule evaluated by the server does not
receive data. Check [Limitations](#limitations) before building one, and test any
rule end to end before relying on it.

## Verify

**Save & Test does not check the connection.** The data source returns success
without contacting Pandora FMS, so a green result only means that Grafana saved
the form. Run both checks below.

### Check the extension directly

```bash
curl -sS -u <USERNAME> \
  -H 'Content-Type: application/json' \
  -d '{"type":"group"}' \
  'https://<PANDORA_FMS_URL>/pandora_console/extensions/grafana/search'
```

`curl` asks for the password interactively, so the password does not appear in
the shell history or in the process list. The extension accepts the standard
HTTP basic authentication that `curl` sends.

A user with the `AR` privilege receives a JSON array with the `All` entry first,
followed by one entry per group:

```json
[{"value":0,"text":"All"},{"value":"<GROUP_ID>","text":"<GROUP_NAME>"}]
```

Read the result as follows:

| Result | Meaning |
|--------|---------|
| A JSON array with `All` and your groups | The extension, the console and the credentials work |
| `[]` | The extension reached Pandora FMS but rejected the credentials, or the user holds no `AR` privilege. A rejected login is **not** an HTTP error |
| `403` | The URL points at a metaconsole node |
| `404` | The URL, the extension directory or the web server rewrite rule is wrong |

### Run a query from Grafana

1. Open a panel or Explore with the **Pandorafms Grafana** data source.
2. Select a group, an agent and a module that has known data in the selected
   time range.
3. The expected result is one series named after the module — with the ` (avg)`
   suffix while **Tip** is unchecked — and points across the range.
4. Check **Tip** and run the query again. The same series appears without the
   suffix and with the original samples.

If the extension check works and the panel still shows no data, read
[Operate and troubleshoot](#operate-and-troubleshoot).

## Understand the results

- **One series per query.** Its name is the module name reported by Pandora FMS.
  With **Tip** unchecked the addon appends ` (avg)` to show that the values are
  compacted averages; with **Tip** checked the series keeps the original samples.
  The **Label** field does not rename the series.
- **The time range is the panel range.** The extension derives the period from
  the range and returns the module history inside it.
- **Unknown periods are gaps.** When Pandora FMS has no value, or marks the
  module data as unknown, the point is null and the panel draws a gap instead of
  a zero.
- **Only numeric modules.** The module picker excludes string modules, so they
  cannot be plotted with this data source. Disabled agents and disabled modules
  are also excluded from the pickers.
- **Permissions stop at the group list.** The extension authenticates the Pandora
  FMS user, requires `AR` on at least one group, and filters the group list by
  that permission. The agent and module lookups and the data request are resolved
  from the identifiers the browser sends, without checking the group permission
  again. Treat every Grafana user who can use this data source as able to read
  any numeric module whose identifier is requested.
- **One Pandora FMS identity per data source.** Every Grafana user who can use
  the data source reads the same data with the same Pandora FMS user. Grafana's
  own permissions on the data source decide who can use it.

## Operate and troubleshoot

### Day-to-day operation

- The addon has no scheduler: it queries Pandora FMS when a panel is loaded or
  refreshed, and when an alert rule is evaluated. Nothing is stored on the
  Grafana side beyond the data source settings.
- Each query is one request to the extension. A panel with three module queries
  sends three requests.
- Keep the Grafana data source URL and the Pandora FMS console URL reachable from
  both the browser and the Grafana server; a change in firewalls, reverse proxies
  or TLS certificates breaks the panels.

### Permissions and transport

- The password is stored in the data source JSON settings, because the browser
  needs it for every query. It is not kept in Grafana's encrypted secure fields,
  and it is returned to the Grafana web client. Restrict who can read or edit
  data sources in Grafana, and use a dedicated Pandora FMS user for the addon.
- HTTP basic authentication encodes the credentials, it does not encrypt them.
  Use an `https` extension URL so that the credentials travel encrypted.
- The default CORS origin is `*`: any web origin may call the extension when it
  can send credentials. Set **Grafana Access-Control-Allow-Origin** to the
  Grafana origin to narrow it.
- The Pandora FMS user needs only the `AR` privilege. Do not use an
  administrator account for the data source.

### Common failures

| Symptom | Cause and check |
|---------|-----------------|
| **Save & Test** reports success but the panel shows no data | Expected: the test does not contact Pandora FMS. Check the extension with the `curl` command in [Verify](#verify) |
| The **Group** list is empty | Rejected credentials, a user without `AR`, or a CORS block. Run the extension check and read the browser console |
| The **Module** list is empty | No **Agent** has been selected yet; agents and modules are also excluded when they are disabled |
| The panel shows **No data** | No stored values in the time range, a string module, or a module left over from a previous agent. Re-select the module and widen the range |
| The browser console reports a CORS error | **Grafana Access-Control-Allow-Origin** does not match the Grafana origin, or the extension URL is `http` while Grafana is `https` |
| The extension answers `403` | The URL points at a metaconsole node; use the node console |
| The extension answers `404` | Wrong path (it must end in `/pandora_console/extensions/grafana`), a missing extension directory, or a web server that does not apply the rewrite rules that resolve `/search` and `/query` |
| **Pandorafms Grafana** does not appear in the data source list | The plugin folder is not under the plugins directory, `allow_loading_unsigned_plugins` lacks the identifier, or Grafana was not restarted |
| The series name ends in ` (avg)` | **Tip** is unchecked; check it to receive the original samples |
| An alert rule returns no data | See [Limitations](#limitations): the server-side evaluation path does not use the connection details stored in the form |

### Limitations

- **The `Label` field does nothing.** The series is always named after the
  module, with the ` (avg)` suffix when the values are compacted.
- **`Save & Test` always reports success.** It does not open a connection to
  Pandora FMS, so it cannot detect a wrong URL, rejected credentials or an
  unreachable console.
- **A rejected login is not an error.** When the user or the password is wrong,
  or the user has no `AR` privilege, the extension answers HTTP `200` with an
  empty array. The panel shows **No data** instead of an authentication error.
- **Alert rules cannot reach the console in this version.** Grafana evaluates
  them on the server, and the server-side path builds its request from the data
  source URL and password fields, while the form stores the console URL and the
  password in custom fields the server side does not read. A rule therefore
  fails or evaluates without data. Panel queries are not affected because the
  browser runs them.
- **The settings contain a single Pandora FMS user, with a single set of
  permissions.** All Grafana users who can use the data source see the same data.
- **String modules cannot be plotted**, and they are not offered in the module
  picker.
- **The pickers load complete lists.** The addon sends no text filter: the
  group, agent and module lists are downloaded in full each time the editor
  changes, and Grafana filters them in the browser.

## Reference

### Data source settings

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| **Pandora extension** | Yes | — | Base URL of the extension, with scheme: `https://<PANDORA_FMS_URL>/pandora_console/extensions/grafana`. No trailing slash and no `/search` or `/query` suffix |
| **Pandora user** | Yes | — | Pandora FMS user queried by every request |
| **Password** | Yes | — | Password of that user, stored in the data source JSON settings |

### Query fields

| Field | Default | Description |
|-------|---------|-------------|
| **Label** | Empty | Not used |
| **Tip** | Unchecked | Checked: original samples. Unchecked: compacted averages with the ` (avg)` series suffix |
| **Group** | Empty | Group filter for the agent list; `All` is value `0` |
| **Agent** | Empty | Agent filter for the module list |
| **Module** | Empty | Module identifier sent to the extension |

### Extension endpoints

The addon uses two endpoints relative to the configured base URL. Both accept
HTTP basic authentication and return JSON.

| Endpoint | Purpose | Request body | Response |
|----------|---------|--------------|----------|
| `<extension>/search` | Group, agent and module lists | `{"type":"group"}`, `{"type":"agent","extra":"<group-id>"}` or `{"type":"module","extra":"<agent-id>"}` | Array of `{"value": <id>, "text": "<name>"}`; groups include `{"value":0,"text":"All"}` |
| `<extension>/query` | Module values for a time range | `{"targets":[{"target":{"agent":"<agent-id>","module":"<module-id>","tip":<boolean>}}],"range":{"from":"<date>","to":"<date>"}}` | Array of objects with the series name in `target` and pairs of `[<value>, <timestamp in milliseconds>]` in `datapoints` |

In `/query` only `module` and `tip` are read: the series name is the module name
reported by Pandora FMS, and the agent value is ignored. Dates are accepted in
any format that Pandora FMS can parse, for example ISO 8601.

### Addon identity

| Property | Value |
|----------|-------|
| Marketplace identifier | `pandorafms.grafana` |
| Name | Grafana |
| Version | `1.0` — the version of the Marketplace package `pandorafms.grafana.1.0.zip` |
| Data source plugin identifier | `pandorafms-pandorafmsgrafana-datasource`, the value required by `allow_loading_unsigned_plugins` |
| Category | Miscelaneus |
| License | One — the download is limited to licensed users |
| Availability | Licensed download |
| Marketplace last update | 2025-06-25 |
| Minimum Grafana version | `10.0.3`, declared by the plugin |
| Marketplace entry | [pandorafms.grafana](https://marketplace.pandorafms.com/entries/pandorafms.grafana) |
