# Cisco Inventory configuration

*Article last updated: 2026-10-26.*

## What it does

The Cisco Inventory configuration addon reads the running configuration of a Cisco network device and stores it in the Pandora FMS inventory of an agent. Each execution connects to the device over SSH, enters privileged (enable) mode, disables terminal pagination, runs `show running-config`, and writes the returned configuration to standard output. Pandora FMS stores that text as the value of the inventory module that runs the addon.

The addon is an inventory collector, not a monitoring plugin: it does not create agents or monitoring modules. It produces one text result per execution, and the inventory module decides which agent receives it. For an addon that runs an arbitrary command instead of the fixed `show running-config`, see [Inventory SSH plugin](inventory-ssh.md).

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all integrations are compatible with Pandora FMS NG 784 and later versions |
| A Cisco device whose CLI accepts `enable`, `terminal length 0` and `show running-config` | `Required` | These are the commands the addon issues on every run |
| SSH access to the device on the default SSH port (`22`) | `Required` | The addon connects to the SSH service without a port option |
| A device user allowed to enter privileged mode and run `show running-config` | `Required` | The addon enters enable mode before reading the configuration |
| Cisco device models and IOS, IOS XE, IOS XR or NX-OS versions | `Not validated` | No model or firmware matrix has been recorded |
| Host operating system that runs the inventory module | `Not validated` | No operating system matrix has been recorded |

### Requirements

1. **Network access** from the host that runs the inventory module to the device, over SSH on the default port.
2. **Credentials**: a device user and its SSH password, plus the enable password when the device requests one.
3. **The `get-config` executable** on the host that runs the inventory module, with execute permission.
4. **Pandora FMS** with an inventory module assigned to the agent that will store the configuration.

No component is installed on the Cisco device.

### Install the addon

Download the addon from its Marketplace entry, which is limited to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.cisco_inventory_configuration](https://marketplace.pandorafms.com/entries/pandorafms.cisco_inventory_configuration)

Extract the package and copy the `get-config` executable to a path readable and executable by the user that runs the inventory module, for example `/usr/local/bin/get-config`. Keep its execute permission:

```bash
chmod 0755 /usr/local/bin/get-config
```

## Configure

### Arguments and order

Pandora FMS runs the executable with positional arguments. Configure the inventory module so the values arrive in this order:

| Position | Argument | Required | Description |
| --- | --- | --- | --- |
| 1 | `address` | Yes | IP address or host name of the device |
| 2 | `username` | Yes | Device user |
| 3 | `sshpassword` | Yes | SSH password of that user |
| 4 | `enablepassword` | Yes | Enable password; use an empty value when the device does not request one |
| 5 | `sleep` | No | Seconds to wait after each command; default `5` |

The argument names are the names used by the executable's help. The inventory module passes values by position, so the order matters more than any label the console shows. If the inventory module always sends the fifth value, enter a number: an empty value is rejected because the argument is parsed as an integer. Omit the argument entirely to use the default.

### Enable mode

Every run sends `enable` and the enable password before reading the configuration. If the device does not ask for an enable password, pass an empty value in the fourth position:

```bash
./get-config <TARGET_HOST> <USERNAME> <PASSWORD> ""
```

If the device asks for one, put it in the same position:

```bash
./get-config <TARGET_HOST> <USERNAME> <PASSWORD> "<ENABLE_PASSWORD>"
```

The addon does not detect whether the enable step succeeded. A wrong enable password, or a user without privilege, is not reported as an enable failure: the module stores whatever the device returns, which can be an error message or an incomplete configuration.

### Register the inventory module

Create an inventory module in the Pandora FMS console and point it at the executable on its host. Add the module to the agent that will store the configuration, and enter the five values in the order above. Mark the SSH password and the enable password as hidden values where the console offers that option. If the console offers an inline-code mode, leave it disabled: the addon runs as an executable.

The module runs on the host of the agent to which it is assigned, so that host must reach the device. The addon does not copy anything to the device.

<!-- SCREENSHOT NEEDED: Inventory module registration form for the Cisco Inventory configuration addon, showing the executable path and the inline-code option left disabled. -->

<!-- SCREENSHOT NEEDED: Agent inventory module configuration with the five positional fields (address, username, SSH password, enable password, sleep) and both password fields masked. -->

### Credentials and transport

- The SSH password and enable password are passed as command-line arguments. On a manual run they appear in the shell history and in the process list while the addon runs. In the console, they are stored in the inventory module configuration. Restrict access to the console and to the agent configuration.
- The SSH session encrypts the credentials in transit. The addon accepts any SSH host key and does not verify it, so a man-in-the-middle on the network path can impersonate the device. Run the addon only from a trusted management network, or enforce device identity at the network layer.
- The running configuration is stored as inventory data and can contain `enable secret`, user password hashes, SNMP communities, crypto keys and other sensitive values. Anyone who can read the agent inventory can read those values. Restrict inventory access accordingly.

The addon has no credential-file option, no port option, and no host-key verification option.

## Verify

Run the executable manually from the host that will run the inventory module:

```bash
./get-config <TARGET_HOST> <USERNAME> <PASSWORD> ""
```

A successful run exits with status `0`, prints the running configuration on standard output, and prints progress messages on standard error:

```text
Connected. Enabling...
Now dumping running-config...
```

The last line of the response is removed; in a normal run it is the device prompt. The remaining text is the configuration that the inventory module stores.

With the default `sleep` of `5` seconds, the addon waits about 25 seconds per run before it finishes: it waits once after opening the shell, once after each of the enable, password and pagination steps, and once after `show running-config`. Allow a module timeout longer than that.

Then check the agent inventory. The module value is the configuration text returned by the device.

<!-- SCREENSHOT NEEDED: Agent inventory view showing a running configuration stored by the Cisco Inventory configuration module, captured on a lab device with no real credentials or customer data. -->

If the run prints an error or no configuration, see [Operate and troubleshoot](#operate-and-troubleshoot).

## Understand the results

The addon stores the raw text of the running configuration. It does not parse the configuration into interfaces, routes, users or other objects, and it does not create one module per section: the complete text is the value of the inventory module.

- The inventory value can be large. The addon reads a single response of up to about 1 MB; a configuration larger than that, or a device that returns its output in several slower blocks, can be truncated.
- The addon always removes the last line of the response, assuming it is the device prompt. When the response does not end with a prompt, the last configuration line is lost.
- The addon does not filter the configuration. Every line the device returns, except the last line it removes, is stored, including credentials and keys.
- The addon does not validate that the text is a configuration. If the device returns an error message, the message is stored as the module value.
- Each execution produces the configuration at that moment. The addon itself does not compare runs or report changes.

## Operate and troubleshoot

### Scheduling and timing

Run the inventory module on the interval you need. Each execution opens a new SSH session and closes it at the end. The `sleep` value controls how long the addon waits after each command; increase it for slow devices or large configurations. Lower values make the run faster but can capture an incomplete response.

### Exit status and diagnostics

| Condition | Status | Output |
| --- | --- | --- |
| Successful capture | `0` | Configuration on standard output; progress messages on standard error |
| SSH connection failure | `1` | `Connection error: <reason>` on standard error |
| Missing or invalid positional argument | `2` | Usage summary on standard error |

### Common failures

- **`Connection error: ...`** — the device is unreachable, the SSH service is not on the default port, the user or password is wrong, or the device rejects the connection. Check the address, the SSH service and the credentials from the same host.
- **The output is a device error or an incomplete configuration** — the enable step failed, the user lacks privilege, or the device does not accept `terminal length 0`. Check the enable password, the user privilege and the device CLI.
- **The output is empty** — `show running-config` returned nothing, the session did not reach privileged mode, or the wait was too short. Increase `sleep` and run the command manually on the device.
- **The output is truncated** — the configuration exceeded the single read of about 1 MB or the device needed more time. This version has no option to read further; retrieve the configuration with a narrower command outside the addon if you need the complete text.
- **The run never returns** — the addon has no configurable connection or read timeout. A device that stops responding can leave the execution waiting. Use the inventory module timeout where the console provides one, and check the device.

### Limitations

- No SSH port option: the addon uses the SSH default port.
- No connection or read timeout option.
- One response read of up to about 1 MB per run.
- No credential file: credentials are positional arguments.
- No host-key verification: any SSH host key is accepted.
- No output filtering or redaction: the full configuration is stored.

## Reference

### Command-line arguments

| Argument | Position | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `address` | 1 | Yes | — | IP address or host name of the Cisco device |
| `username` | 2 | Yes | — | Device user |
| `sshpassword` | 3 | Yes | — | SSH password |
| `enablepassword` | 4 | Yes | — | Enable password; pass `""` when the device does not request one |
| `sleep` | 5 | No | `5` | Seconds to wait after each command |

`-h` or `--help` prints the usage summary and exits.

### Execution and output

```bash
./get-config <TARGET_HOST> <USERNAME> <PASSWORD> <ENABLE_PASSWORD> [SLEEP]
```

| Stream | Content |
| --- | --- |
| Standard output | Running configuration, with CRLF normalized to LF and the last line removed |
| Standard error | `Connected. Enabling...`, `Now dumping running-config...`, or a connection error |
| Exit status | `0` on success, `1` on a connection error, `2` on an argument error |

The addon uses the SSH default port and has no option to change it. It reads a single response of up to 999999 bytes; it does not loop to collect more.

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.cisco_inventory_configuration` |
| Name | Cisco Inventory configuration |
| Version | `1.0` |
| Marketplace last update | 2025-06-25 |
| Package | `pandorafms.cisco_inventory_configuration.1.0.zip` |
| Executable | `get-config` |
| Availability | Download limited to licensed users (license One) |
