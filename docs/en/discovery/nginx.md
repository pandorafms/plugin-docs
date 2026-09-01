# NGINX Discovery

*Article last updated: 2026-09-01.*

## Introduction

This NGINX discovery plugin for Pandora FMS is designed to automate the monitoring of your NGINX servers by leveraging the information provided by the `ngx_http_stub_status_module` (stub_status). By interacting with that endpoint, the plugin collects real-time metrics that are crucial to understanding the performance and health of your NGINX environment, including active connections, accepted and handled connections, processed requests, and the state of connections in reading, writing, and waiting states. One agent will be created in Pandora FMS for each NGINX URL, with one module per available metric.

## Compatibility matrix

| **Systems where tested** | NGINX `nginx:alpine` containers exposed over plain HTTP and over HTTPS with basic authentication (the plugin's own test environment) |
| --- | --- |
| **Systems where it works** | Not validated. The plugin ships as a compiled binary that bundles its dependencies, so it needs no Python installation on the host. No host operating systems have been recorded. |

## Prerequisites

- The plugin is distributed as a compiled binary that already contains all the dependencies needed for its use, so it does not require installing Python or additional libraries.
- The NGINX `stub_status` module must be enabled and accessible. See the [NGINX Configuration](#nginx-configuration) section for the steps.

## NGINX Configuration

For the plugin to obtain the statistics, NGINX must expose the `stub_status` endpoint. Enabling it is done by editing the NGINX configuration file (by default at `/etc/nginx/nginx.conf` or `/etc/nginx/sites-available/default`).

> The `ngx_http_stub_status_module` module is not included in every NGINX build. To verify whether it is available, run `nginx -V 2>&1 | grep stub_status`. Most Linux distributions include it by default.

### Minimal configuration (no authentication, no SSL)

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

### Configuration with basic authentication

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

The same `username` and `password` must be provided to the plugin through `--user` / `--password` (or the `username` / `password` fields of the configuration file).

### Configuration with SSL/TLS

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

In the plugin the URL will be indicated with the `https://` scheme and the `--ssl` parameter (or `verify_ssl`) depending on whether the certificate should be validated:

- `verify_ssl = true` → for valid certificates in production.
- `verify_ssl = false` → for self-signed certificates or test environments.

### Full configuration (SSL + authentication)

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

### Verification

To verify that the endpoint responds correctly, you can make a manual request to the status page:

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

## Configuration in PandoraFMS

This plugin can be integrated with Pandora FMS *Discovery*.

To do so, load the ".disco" package that you can download from the Pandora FMS library:

[https://marketplace.pandorafms.com/](https://marketplace.pandorafms.com/)

Once loaded, NGINX instances can be monitored by creating *Discovery* tasks from the *Management &gt; Discovery &gt; Application &gt; NGINX* section.

For each task the following minimum data will be requested in the **NGINX Basic** step:

- **NGINX Status URLs:** NGINX stub_status endpoint URLs, separated by commas or one per line. Each URL will generate an agent.
- **Username:** username for the NGINX endpoint if it requires HTTP basic authentication, optional
- **Password:** password for the NGINX endpoint if it requires HTTP basic authentication, optional
- **Verify SSL:** active if the URL SSL certificate needs to be verified, inactive by default
- **Transfer mode:** transfer mode (native or tentacle), optional
- **Tentacle IP:** tentacle IP, optional
- **Tentacle port:** tentacle port, optional

In the **NGINX Advanced** step additional options can be configured:

- **Module prefix:** prefix to add to all created module names, optional
- **Request timeout:** maximum wait time for the HTTP request in seconds, optional (default 10)
- **Allow list:** regular expression to include only modules whose name matches, optional
- **Deny list:** regular expression to exclude modules whose name matches, optional

Successfully completed tasks will show an execution summary with the following information:

- **Total agents** : Total number of agents generated by the task.
- **Total modules:** Total number of modules generated by the task.

## Agent and modules generated by the plugin

The plugin will create one agent per indicated NGINX URL. The agent name is computed by applying an MD5 hash over the URL `netloc` (host:port), and the alias corresponds to that `netloc` (for example, `nginx1.example.com`). Each agent will include the modules obtained by parsing the plain text of the NGINX stub_status endpoint.

The `Status` module is created for each agent by default, with value `1` if the endpoint is reachable, indicating that NGINX is running. It can be excluded through the allow/deny list, like any other module. If the endpoint is not reachable, the plugin reports the error in the execution information. The remaining numeric fields are included as `generic_data` modules (instantaneous values) or `generic_data_inc` modules (incremental counters with per-second rate calculation), following the `<prefix><MetricName>` format.

The fields available in the NGINX stub_status, which give rise to modules, are:

```bash
Status: stub_status endpoint state (1=UP, 0=DOWN) — always monitored (generic_proc).
Active_connections: Total active connections, including waiting ones (generic_data).
Accepts: Accepted connections accumulated since NGINX started (generic_data_inc, per-second rate).
Handled: Handled connections accumulated since NGINX started (generic_data_inc, per-second rate).
          If the value is lower than Accepts, NGINX is dropping traffic.
Requests: Client requests processed accumulated since NGINX started (generic_data_inc, per-second rate).
Reading: Connections reading request headers from the client (generic_data).
Writing: Connections writing a response to the client or processing a request (generic_data).
Waiting: Idle keep-alive connections waiting for the next request (generic_data).


```

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

## Parameters

**Simple mode**

| Parameter | Description |
| --- | --- |
| `--urls` | NGINX stub_status endpoint URLs, separated by commas. Each URL will generate an agent. |
| `--user` | username if the NGINX endpoint requires HTTP basic authentication, optional |
| `--password` | password if the NGINX endpoint requires HTTP basic authentication, optional |
| `--ssl` | whether to verify the URL HTTPS certificate or not, optional (default true) |
| `--prefix` | prefix for module names, optional |
| `--transfer_mode` | data transfer mode (native or tentacle), optional |
| `--tentacle_ip` | tentacle IP, optional |
| `--tentacle_port` | tentacle port, optional |
| `--interval` | monitoring interval in seconds, optional (default 300) |
| `--allow_list` | regular expression to include only modules whose name matches, optional |
| `--deny_list` | regular expression to exclude modules whose name matches, optional |
| `--timeout` | maximum wait time for the HTTP request in seconds, optional (default 10) |
| `--as_server_plugin` | return a single `1` (agents were created without errors) or `0` instead of the JSON summary, so the plugin can be used as a server plugin, optional (default false) |

> When running in simple mode with `--urls`, the module prefix, transfer mode, tentacle address, and interval parameters listed above are not applied: the plugin uses the defaults (`native`, `127.0.0.1:41121`, `300` seconds). To change them, use the configuration file with `--conf`.

**Advanced mode**

| Parameter | Description |
| --- | --- |
| `--conf` | path to the configuration file |
| `--targets_file` | path to the file containing the NGINX URLs (mandatory when using --conf) |

**Configuration file (--conf)**

```
username= username if the NGINX endpoint requires HTTP basic authentication, optional
password= password if the NGINX endpoint requires HTTP basic authentication, optional
verify_ssl= whether to verify the URL HTTPS certificate or not, optional
prefix= prefix for module names, optional
transfer_mode= data transfer mode (native or tentacle), optional
tentacle_ip= tentacle IP, optional
tentacle_port= tentacle port, optional
agents_group= name of the agent group the created agents will be assigned to, optional
agents_group_id= id of the agent group the created agents will be assigned to, optional
interval= monitoring interval in seconds, optional
allow_list= regular expression to include only modules whose name matches, optional
deny_list= regular expression to exclude modules whose name matches, optional
timeout= maximum wait time for the HTTP request in seconds, optional


```

**Example**

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

Targets file (`--targets_file`):

```
http://<TARGET_HOST_1>/nginx_status
http://<TARGET_HOST_2>/nginx_status


```

## Manual execution

The execution will return a JSON output with information about the run, and will generate one XML file per monitored agent (in tentacle mode) which will be sent to the Pandora FMS server using the transfer method indicated in the configuration. In `native` mode the data is exposed in the `monitoring_data` field of the JSON output so that it is consumed by the Discovery server.

### Execution format

The plugin execution format is as follows:

```bash
./pandora_nginx --urls <NGINX endpoint URLs separated by commas> --user <username> --password <password> --ssl <true|false> --prefix <prefix> --transfer_mode <native|tentacle> --tentacle_ip <tentacle IP> --tentacle_port <tentacle port> --interval <interval> --allow_list <regex> --deny_list <regex> --timeout <seconds> --as_server_plugin <true|false> --conf <path to configuration file> --targets_file <path to URLs file>


```

#### Examples

to run in simple mode

```bash
./pandora_nginx --urls http://<TARGET_HOST_1>/nginx_status,http://<TARGET_HOST_2>/nginx_status --user <USERNAME> --password <PASSWORD> --ssl false


```

to run in advanced mode

```bash
./pandora_nginx --conf <PATH_TO_CONFIG> --targets_file <PATH_TO_TARGETS>


```

#### Verbose mode

The plugin has no verbose or debug flag. Its only diagnostic channel is the JSON execution summary printed to standard output, which reports the failing endpoint when a request to `stub_status` cannot be completed.

## Console extension

The plugin ships with a companion console extension, `nginx_view`, which renders a dashboard of every
NGINX node the plugin monitors. It is not installed by the `.disco` package: the extension is part of the
console, under `pandora_console_extensions/nginx_view/`.

Once available, it appears in the console under **Operation**, as **NGINX Monitoring**. Viewing it
requires read permission (`AR`) over the agents.

The extension does not need to be told which agents to read. It discovers them by querying the
`extra_data` markers the plugin writes, selecting every module whose `extra_data` starts with
`nginx:metric_` and resolving the agents that own them. Any agent created by the plugin therefore shows
up automatically, with no configuration on the extension side.

It displays summary cards for the number of NGINX nodes, how many are up and down, total active
connections, the aggregated request counter, and idle connections, followed by a per-node table.

<!-- SCREENSHOT NEEDED: the NGINX Monitoring extension dashboard, showing the summary cards and the node table, with at least two monitored nodes -->