# NGINX Discovery

*Article last updated: 2026-09-01.*

## What it monitors

The NGINX Discovery plugin automates the monitoring of NGINX servers through the `ngx_http_stub_status_module` (stub_status) endpoint. It reads that endpoint and turns its counters into Pandora FMS monitoring modules: active connections, accepted and handled connections, processed requests, and connections in the reading, writing and waiting states.

The plugin creates **one agent per NGINX URL**, with one module per available metric, plus a reachability module. A Discovery task can point at several URLs at once, so a single task covers a whole set of NGINX nodes.

A companion console extension, **NGINX Monitoring**, aggregates every node the plugin monitors into a single view. See [NGINX Monitoring console extension](#nginx-monitoring-console-extension).

## Prepare

### Compatibility

| Scope | State | Evidence |
|-------|-------|----------|
| Plugin version `1.0` (`pandorafms.nginx`) | Documented target | The version this page describes. See [Plugin identity](#plugin-identity) |
| NGINX exposing `stub_status` over plain HTTP | `Tested` | Exercised against `nginx:alpine` |
| NGINX exposing `stub_status` over HTTPS with basic authentication | `Tested` | Exercised against `nginx:alpine` with a self-signed certificate |
| `ngx_http_stub_status_module` compiled into the NGINX build | `Required` | Prerequisite, not a compatibility statement. See [Prerequisites](#prerequisites) |
| Network reachability from the Discovery server to the status endpoint | `Required` | The plugin performs an HTTP request per URL |
| Host operating system running the plugin | `Not validated` | No host operating system has been recorded |
| Any specific NGINX release or distribution package | `Not validated` | Compatibility was established against the endpoint contract, not a version matrix |

### Prerequisites

1. **The `stub_status` endpoint must be enabled and reachable** from the machine that runs the plugin. Enabling it is covered in [Enable the status endpoint](#enable-the-status-endpoint).
2. **Pandora FMS**: a Discovery server to execute the task, and the console to define it.
3. **Credentials**, only when the endpoint is protected with HTTP basic authentication.

The plugin is distributed as a self-contained executable: the packaged Discovery app ships `bin/pandora_nginx`, so no additional runtime has to be installed, on the Discovery server or for a manual run.

### Install the plugin

Load the `.disco` package from the Pandora FMS marketplace:

[https://marketplace.pandorafms.com/](https://marketplace.pandorafms.com/)

Once loaded, the **NGINX** application is available when creating Discovery tasks.

The companion console extension is **not** part of that package. It ships with the console, under `pandora_console_extensions/nginx_view/`.

### Enable the status endpoint

For the plugin to obtain the statistics, NGINX must expose the `stub_status` endpoint. Enabling it is done by editing the NGINX configuration file (by default at `/etc/nginx/nginx.conf` or `/etc/nginx/sites-available/default`).

> The `ngx_http_stub_status_module` module is not included in every NGINX build. To verify whether it is available, run `nginx -V 2>&1 | grep stub_status`. Most Linux distributions include it by default.

Pick the variant that matches how the endpoint should be protected.

#### Minimal configuration (no authentication, no SSL)

Add a dedicated `location` for the status inside your `server`:

```nginx
server {
    listen 80;
    server_name _;

    location /nginx_status {
        stub_status on;
        access_log off;
        allow <PANDORA_FMS_SERVER_IP>;   # Pandora FMS server IP
        deny all;
    }
}
```

With this configuration the plugin will consume the URL:

```
http://<SERVER_IP>/nginx_status
```

#### Configuration with basic authentication

To protect the endpoint with username and password, define `auth_basic` and `auth_basic_user_file` in the status location:

```nginx
server {
    listen 80;
    server_name _;

    location /nginx_status {
        stub_status on;
        access_log off;
        auth_basic "NGINX Status";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

Generate the `.htpasswd` file with `htpasswd` or `openssl`:

```bash
htpasswd -c /etc/nginx/.htpasswd <USERNAME>
# or
echo "<USERNAME>:$(openssl passwd -apr1 <PASSWORD>)" > /etc/nginx/.htpasswd
```

The second form places the password in the command line, where the shell history and the operating system process list expose it. Prefer `htpasswd -c`, which prompts for it.

The same `username` and `password` must be provided to the plugin through the task fields, or through `--user` / `--password` for a manual run.

#### Configuration with SSL/TLS

To serve the statistics over HTTPS configure the certificate in the `server`:

```nginx
server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/nginx/certs/status.pem;
    ssl_certificate_key /etc/nginx/certs/status.key;

    location /nginx_status {
        stub_status on;
        access_log off;
        allow <PANDORA_FMS_SERVER_IP>;
        deny all;
    }
}
```

Generate a self-signed test certificate with:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/certs/status.key \
  -out /etc/nginx/certs/status.crt \
  -subj "/CN=localhost"
cat /etc/nginx/certs/status.crt /etc/nginx/certs/status.key > /etc/nginx/certs/status.pem
```

The URL is then given to the plugin with the `https://` scheme, and **Verify SSL** decides whether the certificate chain is validated:

- enabled → for valid certificates in production.
- disabled → for self-signed certificates or test environments.

#### Full configuration (SSL + authentication)

```nginx
server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/nginx/certs/status.pem;
    ssl_certificate_key /etc/nginx/certs/status.key;

    location /nginx_status {
        stub_status on;
        access_log off;
        auth_basic "NGINX Status";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}

server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
```

After modifying the NGINX configuration, reload the service to apply the changes:

```bash
sudo systemctl reload nginx
```

#### Confirm the endpoint responds

Before creating the task, request the status page by hand:

```bash
curl -u <USERNAME>:<PASSWORD> http://<SERVER_IP>/nginx_status
```

The output must be plain text with the following format:

```
Active connections: 291
server accepts handled requests
 16630948 16630948 31070465
Reading: 6 Writing: 179 Waiting: 106
```

- **Active connections**: total number of active connections (includes waiting ones).
- **accepts**: total connections accepted since NGINX started.
- **handled**: total connections handled since NGINX started.
- **requests**: total client requests processed since NGINX started.
- **Reading**: connections reading request headers from the client.
- **Writing**: connections writing a response to the client or processing a request.
- **Waiting**: idle keep-alive connections waiting for the next request.

If this request fails, the task will fail too. Fix it here rather than in the console.

## Configure the Discovery task

Create the task from **Management → Discovery → Application → NGINX**. The console presents the fields in two steps, and every field is documented in [Task parameters](#task-parameters).

1. **NGINX Basic** — the endpoints and how to reach them:

    - **NGINX Status URLs**: stub_status endpoint URLs, separated by commas or one per line. **Each URL generates one agent.**
    - **Username** and **Password**: only when the endpoint requires HTTP basic authentication.
    - **Verify SSL**: validate the certificate chain of an `https://` URL. Disabled by default.
    - **Transfer mode**, **Tentacle IP** and **Tentacle port**: how the data reaches Pandora FMS. `native` lets the Discovery server read the data directly and is the default.

    <!-- SCREENSHOT NEEDED: NGINX Basic wizard step showing the URL textarea, the credential fields, Verify SSL and the transfer-mode selector, with placeholder values and no real credentials. -->

2. **NGINX Advanced** — optional shaping of the result:

    - **Module prefix**: prepended to every created module name.
    - **Request timeout**: seconds to wait for each HTTP request. Defaults to `10`.
    - **Allow list** and **Deny list**: regular expressions to include or exclude modules by name.

    <!-- SCREENSHOT NEEDED: NGINX Advanced wizard step showing module prefix, request timeout, allow list and deny list. -->

The task's own group and interval come from the generic task-definition step, and are passed to the plugin as the agent group and the module interval.

## Verify the first run

Force the task from **Management → Discovery → Task list** and check the result in this order.

1. **The task summary.** A successfully completed task reports:

    - **Total agents**: the number of agents generated by the task.
    - **Total modules**: the number of modules generated by the task.

    Expect one agent per URL you entered. A URL that could not be read is reported as an error in the execution information instead.

    <!-- SCREENSHOT NEEDED: Discovery task execution summary for an NGINX task showing Total agents and Total modules. -->

2. **The agents.** One per URL, with the alias set to the endpoint's `host:port`.

3. **The modules on each agent.** A reachable endpoint produces:

    | Module | Expected value |
    |--------|----------------|
    | `Status` | `1` — the endpoint answered |
    | `Active_connections` | Current active connections |
    | `Accepts`, `Handled`, `Requests` | Accumulated counters; Pandora FMS derives the per-second rate |
    | `Reading`, `Writing`, `Waiting` | Current connections in each state |

    Module names carry the **Module prefix** when one was set, and the allow/deny lists can legitimately remove any of them.

4. **The console extension**, when it is installed: the node should appear in **Operation → NGINX Monitoring** with no extra configuration.

If the task reports no agents, work back through [Confirm the endpoint responds](#confirm-the-endpoint-responds) and then [Troubleshoot](#troubleshoot).

## Understand the results

### Agents and modules generated

The plugin creates **one agent per NGINX URL**. The agent name is the MD5 hash of the endpoint's `netloc` (`host:port`), and the alias is that `netloc` itself, for example `nginx1.example.com`. When a URL has no parsable `netloc`, the whole URL is used instead.

Because the identity comes from the endpoint and not from the task, moving a URL between tasks keeps reporting to the same agent and preserves its history.

The `Status` module is created for every agent by default, with value `1` when the endpoint is reachable. It can be excluded through the allow/deny lists like any other module. When the endpoint cannot be reached, the plugin reports the failure in the execution information. The remaining fields become `generic_data` modules (instantaneous values) or `generic_data_inc` modules (incremental counters, from which Pandora FMS derives a per-second rate), named `<prefix><MetricName>`.

### Module type mapping

| Metric | Pandora FMS module type | Description |
| --- | --- | --- |
| Status | `generic_proc` | Endpoint state (1=reachable, 0=DOWN). Allows configuring critical alerts when the value is 0. |
| Active_connections | `generic_data` | Current active connections (gauge). Includes reading, writing, and waiting connections. |
| Accepts | `generic_data_inc` | Accumulated accepted connections. Pandora FMS automatically calculates the per-second rate. |
| Handled | `generic_data_inc` | Accumulated handled connections. Pandora FMS automatically calculates the per-second rate. If the rate is lower than Accepts, NGINX is dropping connections. |
| Requests | `generic_data_inc` | Accumulated processed requests. Pandora FMS automatically calculates the per-second rate (requests/s). |
| Reading | `generic_data` | Connections in the header-reading state (gauge). |
| Writing | `generic_data` | Connections in the response-writing state (gauge). |
| Waiting | `generic_data` | Idle keep-alive connections (gauge). A high value is normal when keep-alive is enabled. |

### extra_data markers

The plugin assigns stable identifiers in the `extra_data` field of each agent and module, following the `nginx:<kind>:<identifier>` format, to allow later identification from the console, dashboards, extensions, or SQL queries:

- **Agent**: `nginx:target:<sanitized_url>` — identifies the monitored NGINX target.
- **Status module**: `nginx:metric_status:<sanitized_url>`
- **Metric modules**: `nginx:metric_<metric_name>:<sanitized_url>` — for example `nginx:metric_active_connections:...`, `nginx:metric_accepts:...`, etc.

These markers do not contain the agent or module name, but the external identifier (the target URL), which is stable and meaningful at the domain level.

### NGINX Monitoring console extension

The plugin has a companion console extension, `nginx_view`, which renders a dashboard of every NGINX node the plugin monitors. It is not installed by the `.disco` package: the extension is part of the console, under `pandora_console_extensions/nginx_view/`.

Once available, it appears in the console under **Operation**, as **NGINX Monitoring**. Opening it requires the **AR** ACL.

The extension does not need to be told which agents to read. It discovers them from the `extra_data` markers the plugin writes, selecting every module whose `extra_data` starts with `nginx:metric_` and resolving the agents that own them. Any agent created by the plugin therefore shows up automatically, with no configuration on the extension side.

It displays summary cards for the number of NGINX nodes, how many are up and down, total active connections, the aggregated request counter, and idle connections, followed by a per-node table.

<!-- SCREENSHOT NEEDED: NGINX Monitoring extension view showing the summary cards and the per-node table, with lab hostnames only. -->

## Troubleshoot

The plugin has no verbose or debug flag. Its only diagnostic channel is the JSON execution summary printed to standard output, which names the failing endpoint when a request to `stub_status` cannot be completed.

- **The task creates no agents** — every URL failed. Reproduce the request with `curl` as in [Confirm the endpoint responds](#confirm-the-endpoint-responds); the JSON summary of a manual run names the endpoint that failed.
- **`stub_status` is not available** — the module is not in this NGINX build. Check with `nginx -V 2>&1 | grep stub_status` and use a build that includes it.
- **The endpoint answers by hand but not from the task** — the request leaves from the Discovery server, not from your workstation. Check the `allow`/`deny` rules in the status `location` and the network path from that server.
- **HTTPS endpoint fails with a certificate error** — a self-signed or internally-issued certificate does not validate. Disable **Verify SSL** for that task, or install the issuing CA on the Discovery server.
- **`401` on a protected endpoint** — the credentials do not match `auth_basic_user_file`. Regenerate the entry with `htpasswd` and retest with `curl -u`.
- **Module prefix, transfer mode, tentacle address or interval seem ignored in a manual run** — in simple mode (`--urls`) those parameters are not applied; the plugin uses `native`, `127.0.0.1:41121` and `300` seconds. Use the configuration file to change them.
- **`Handled` is consistently lower than `Accepts`** — this is not a plugin fault: NGINX is dropping connections. Investigate the server's resource limits.

## Reference

### Task parameters

The console presents the task fields in two steps.

#### NGINX Basic

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| NGINX Status URLs | `_nginxUrls_` | textarea | — | Mandatory. Comma separated or one per line. Each URL creates one agent |
| Username | `_nginxUser_` | string | — | HTTP basic authentication user, optional |
| Password | `_nginxPassword_` | password | — | HTTP basic authentication password, optional |
| Verify SSL | `_verifySSL_` | checkbox | off | Validate the certificate chain when using HTTPS. Disable for self-signed certificates |
| Transfer mode | `_transferMode_` | select | `native` | `native`: the Discovery server reads the agent data directly. `tentacle`: the plugin sends the data with the Tentacle client |
| Tentacle IP | `_tentacleIp_` | string | `127.0.0.1` | Tentacle server address, used in `tentacle` mode |
| Tentacle port | `_tentaclePort_` | number | `41121` | Tentacle server port, used in `tentacle` mode |

#### NGINX Advanced

| Field | Macro | Type | Default | Notes |
|-------|-------|------|---------|-------|
| Module prefix | `_prefixModules_` | string | — | Prepended to every created module name, for example `nginx_` |
| Request timeout | `_reqTimeout_` | number | `10` | HTTP request timeout in seconds |
| Allow list | `_allowList_` | string | — | Regular expression; only modules whose name matches are included. Empty means all |
| Deny list | `_denyList_` | string | — | Regular expression; modules whose name matches are excluded. Empty means none |

The task's group and interval are taken from the generic task-definition step and reach the plugin as `agents_group`, `agents_group_id` and `interval`.

### Command-line execution

The plugin can also be executed by hand, which is the fastest way to confirm an endpoint and its credentials before wiring them into a task, and is also how it is used as a server plugin.

It has two input modes:

- **Simple mode** passes the endpoints on the command line with `--urls`.
- **Advanced mode** passes a configuration file with `--conf` plus a targets file with `--targets_file`. This is the mode the Discovery task itself uses.

```bash
# Simple mode
./pandora_nginx --urls http://<TARGET_HOST_1>/nginx_status,http://<TARGET_HOST_2>/nginx_status \
    --user <USERNAME> --password <PASSWORD> --ssl false

# Advanced mode
./pandora_nginx --conf <PATH_TO_CONFIG> --targets_file <PATH_TO_TARGETS>
```

Passing a password on the command line exposes it in the shell history and in the operating system process list. Prefer the configuration file for anything but a one-off check.

The run returns a JSON summary of the execution. In `native` mode the collected data is exposed in the summary's `monitoring_data` field, for the Discovery server to consume; in `tentacle` mode the plugin generates one XML file per agent and sends it to the Pandora FMS server.

`--as_server_plugin` replaces the JSON summary with a single `1` (agents created without errors) or `0`, so the plugin can be wired as a server plugin.

```bash
./pandora_nginx --urls <URLs> [options]
./pandora_nginx --conf <path> --targets_file <path>
```

| Parameter | Description |
| --- | --- |
| `--urls` | NGINX stub_status endpoint URLs, separated by commas. Each URL will generate an agent |
| `--user` | Username if the NGINX endpoint requires HTTP basic authentication, optional |
| `--password` | Password if the NGINX endpoint requires HTTP basic authentication, optional |
| `--ssl` | Whether to verify the URL HTTPS certificate or not, optional (default true) |
| `--prefix` | Prefix for module names, optional |
| `--transfer_mode` | Data transfer mode (`native` or `tentacle`), optional |
| `-ti`, `--tentacle_ip` | Tentacle IP, optional (default `127.0.0.1`) |
| `-tp`, `--tentacle_port` | Tentacle port, optional (default `41121`) |
| `--interval` | Monitoring interval in seconds, optional (default 300) |
| `--allow_list` | Regular expression to include only modules whose name matches, optional |
| `--deny_list` | Regular expression to exclude modules whose name matches, optional |
| `--timeout` | Maximum wait time for the HTTP request in seconds, optional (default 10) |
| `--as_server_plugin` | Return a single `1` (agents were created without errors) or `0` instead of the JSON summary, optional (default false) |
| `--conf` | Path to the configuration file |
| `--targets_file` | Path to the file containing the NGINX URLs (mandatory when using `--conf`) |

> In simple mode (`--urls`), the module prefix, transfer mode, tentacle address and interval parameters listed above are not applied: the plugin uses the defaults (`native`, `127.0.0.1:41121`, `300` seconds). To change them, use the configuration file with `--conf`.

### Configuration file

The Discovery task builds this file from its own fields; a manual advanced-mode run supplies it with `--conf`.

| Key | Description |
| --- | --- |
| `username` | HTTP basic authentication user, optional |
| `password` | HTTP basic authentication password, optional |
| `verify_ssl` | Whether to verify the HTTPS certificate, optional |
| `prefix` | Prefix for module names, optional |
| `transfer_mode` | Data transfer mode (`native` or `tentacle`), optional |
| `tentacle_ip` | Tentacle IP, optional |
| `tentacle_port` | Tentacle port, optional |
| `agents_group` | Name of the agent group the created agents are assigned to, optional |
| `agents_group_id` | Id of the agent group the created agents are assigned to, optional |
| `interval` | Monitoring interval in seconds, optional |
| `allow_list` | Regular expression to include only modules whose name matches, optional |
| `deny_list` | Regular expression to exclude modules whose name matches, optional |
| `timeout` | Maximum wait time for the HTTP request in seconds, optional |

Example:

```ini
[CONF]
username=<USERNAME>
password=<PASSWORD>
verify_ssl=false
prefix=nginx_
transfer_mode=native
tentacle_ip=127.0.0.1
tentacle_port=41121
interval=300
allow_list=
deny_list=
timeout=10
```

Targets file (`--targets_file`), one URL per line or comma separated:

```
http://<TARGET_HOST_1>/nginx_status
http://<TARGET_HOST_2>/nginx_status
```

### Plugin identity

| Field | Value |
|-------|-------|
| App short name | `pandorafms.nginx` |
| Plugin version | `1.0` |
| Type | Discovery application (`.disco`) |
| Section | Discovery → Applications |
| Console extension | `nginx_view` (ships with the console, not with the package) |
