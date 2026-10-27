# Inventory SSH plugin

*Article last updated: 2026-10-26.*

## What it does

The Inventory SSH plugin runs a command on a network device over SSH and stores the command output in the Pandora FMS inventory of an agent. The command is chosen by the operator, so the same addon can collect a running configuration, a firmware version, or any other CLI output. Each execution connects to the device, optionally enters enable mode, optionally sends a pagination command, runs the configured command, filters the response, and writes the result to standard output. Pandora FMS stores that text as the value of the inventory module that runs the addon.

The addon is an inventory collector, not a monitoring plugin: it does not create agents or monitoring modules. It produces one text result per execution, and the inventory module decides which agent receives it. For the addon that always collects `show running-config`, see [Cisco Inventory configuration](cisco-inventory-configuration.md).

## Prepare

### Compatibility

| Scope | State | Evidence |
| --- | --- | --- |
| Pandora FMS NG 784 and later | `Supported` | The Marketplace states that all integrations are compatible with Pandora FMS NG 784 and later versions |
| An SSH service on the device that provides an interactive shell | `Required` | The addon opens an interactive SSH shell to run the command |
| SSH access to the device on the default SSH port (`22`) | `Required` | The addon connects to the SSH service without a port option |
| A device user allowed to run the configured command | `Required` | The addon sends the command with the configured user |
| Network device vendors, models and firmware versions | `Not validated` | No device or firmware matrix has been recorded |
| Host operating system that runs the inventory module | `Not validated` | No operating system matrix has been recorded |

### Requirements

1. **Network access** from the host that runs the inventory module to the device, over SSH on the default port.
2. **Credentials**: a device user and its SSH password, plus the enable password when the device requires enable mode.
3. **The `ssh_inventory` executable** on the host that runs the inventory module, with execute permission.
4. **Pandora FMS** with an inventory module assigned to the agent that will store the command output.

No component is installed on the network device.

### Install the addon

Download the addon from its Marketplace entry, which is limited to licensed users:

[https://marketplace.pandorafms.com/entries/pandorafms.inventoryssh](https://marketplace.pandorafms.com/entries/pandorafms.inventoryssh)

Extract the package and copy the `ssh_inventory` executable to a path readable and executable by the user that runs the inventory module, for example `/usr/local/bin/ssh_inventory`. Keep its execute permission:

```bash
chmod 0755 /usr/local/bin/ssh_inventory
```

## Configure

### Arguments and order

Pandora FMS runs the executable with positional arguments. Configure the inventory module so the values arrive in this order:

| Position | Argument | Required | Description |
| --- | --- | --- | --- |
| 1 | `address` | Yes | IP address or host name of the device |
| 2 | `username` | Yes | Device user |
| 3 | `password` | Yes | SSH password, or `<PASSWORD>/<ENABLE_PASSWORD>` when the device requires enable mode |
| 4 | `command` | Yes | Command to run, including its line terminator as an escape sequence |
| 5 | `extra_command` | Yes | Command sent before the main command, normally to disable pagination; use `""` for none |
| — | `--debug` | No | Takes a value; supplying the option enables progress messages |

`extra_command` is positional and therefore required: pass an empty string when you do not need it. `--debug` is an option and can appear before or after the positional values.

The argument names are the names used by the executable's help. The inventory module passes values by position, so the order matters more than any label the console shows.

### Command and pagination

The command is sent to the device as configured, after the addon interprets escape sequences. It must contain the line terminator: use `\n`, and add `\r` when the device requires it. The addon does not append a newline to the command, so a command without `\n` is typed on the device but not executed.

```bash
./ssh_inventory <TARGET_HOST> <USERNAME> '<PASSWORD>' 'show running-config\n' 'terminal length 0'
```

The same addon on a device with a different CLI, for example a MikroTik device:

```bash
./ssh_inventory <TARGET_HOST> <USERNAME> '<PASSWORD>' 'system resource print\n\r' ''
```

Use single quotes around the command so the shell preserves the backslashes and the addon can interpret them.

If the command contains a colon (`:`), the addon discards the text before the first colon and sends the rest. Avoid colons in the command, or account for that truncation.

`extra_command` is sent as plain text followed by a newline; escape sequences in it are not interpreted. It runs after the optional enable step and before the main command. Use it for the vendor command that disables pagination, such as `terminal length 0` or `no page`. Pass an empty string when no extra command is needed.

### Password and enable mode

The `password` argument accepts one value or two values separated by `/`:

| Form | SSH password | Enable password |
| --- | --- | --- |
| `<PASSWORD>` | `<PASSWORD>` | none |
| `<PASSWORD>/<ENABLE_PASSWORD>` | `<PASSWORD>` | `<ENABLE_PASSWORD>` |

The addon splits the value on `/` and uses the first segment as the SSH password and the second as the enable password. A password that itself contains `/` cannot be represented; segments after the second are ignored. The addon sends `enable` and the enable password only when an enable password is present, so a device that requires enable mode without the second value may return a privilege error or an empty result.

### Debug output

`--debug <value>` must be given a value. Supplying the option enables two progress messages on standard error regardless of the value, including `--debug 0`; omit the option to keep them off. The first message is `Connected. Enabling...` and the second is always `Now dumping running-config...`, whatever command you configured.

The addon has no other verbosity option.

### Register the inventory module

Create an inventory module in the Pandora FMS console and point it at the executable on its host. Add the module to the agent that will store the output, and enter the five values in the order above. Mark the password field as a hidden value where the console offers that option. If the console offers an inline-code mode, leave it disabled: the addon runs as an executable.

The module runs on the host of the agent to which it is assigned, so that host must reach the device. The addon does not copy anything to the device.

<!-- SCREENSHOT NEEDED: Inventory module registration form for the Inventory SSH plugin, showing the executable path and the inline-code option left disabled. -->

<!-- SCREENSHOT NEEDED: Agent inventory module configuration with the five positional fields (address, username, password, command, extra command) and the password field masked. -->

### Credentials and transport

- The SSH password and enable password are passed as command-line arguments. On a manual run they appear in the shell history and in the process list while the addon runs. In the console, they are stored in the inventory module configuration. Restrict access to the console and to the agent configuration.
- The SSH session encrypts the credentials in transit. The addon accepts any SSH host key and does not verify it, so a man-in-the-middle on the network path can impersonate the device. Run the addon only from a trusted management network, or enforce device identity at the network layer.
- The command output is stored as inventory data. It can contain credentials, keys, community strings and other sensitive values. Anyone who can read the agent inventory can read them. Restrict inventory access accordingly.
- The line filter described in [Understand the results](#understand-the-results) is not a redaction control. Use a device user with read-only privileges, and choose commands whose output you are prepared to store.

The addon has no credential-file option, no port option, and no host-key verification option.

## Verify

Run the executable manually from the host that will run the inventory module:

```bash
./ssh_inventory <TARGET_HOST> <USERNAME> '<PASSWORD>' 'show version\n' 'terminal length 0' --debug 1
```

A successful run exits with status `0` and prints the filtered command output on standard output. With `--debug 1`, it also prints the two progress messages on standard error:

```text
Connected. Enabling...
Now dumping running-config...
```

The second message is fixed text and names `running-config` even when the command is `show version`. It is a progress message, not a statement about the command that ran.

Then check the agent inventory. The module value is the filtered text returned by the device for the configured command.

<!-- SCREENSHOT NEEDED: Agent inventory view showing command output stored by the Inventory SSH plugin module, captured on a lab device with no real credentials or customer data. -->

If the run prints an error or no output, see [Operate and troubleshoot](#operate-and-troubleshoot).

## Understand the results

### What the module stores

The addon stores the command output as plain text. It does not parse the output into interfaces, routes, firmware fields or other objects, and it does not create one module per line: the filtered text is the value of the inventory module.

Before printing, the addon removes the sent command text, the text captured before the command (normally the device prompt), the last line of the response, leading and trailing whitespace, and empty lines. If the command produces no output, the module value is empty.

### Filtering

The filter is always applied; this version has no option to disable it. It removes any line that contains one of these values:

- `enable`
- `Password:`
- the command text

The match is case-sensitive and applies anywhere in the line. Empty lines are removed afterwards. The `extra_command` value is not added to the filter list.

Because `enable` is matched anywhere, lines such as `enable secret ...` are removed, and so are legitimate configuration lines that contain the word. Because the command text is matched, any output line that repeats the command is removed. The filter can remove useful lines and does not guarantee that every secret is removed; treat it as output cleanup, not as redaction.

### Sensitive content

A running configuration, a firmware inventory or a diagnostic command can expose credentials, keys and internal addresses. The filter removes some lines but not all sensitive values. Restrict access to the agent inventory and choose the command with the same care as the credentials.

## Operate and troubleshoot

### Scheduling and timing

Run the inventory module on the interval you need. Each execution opens a new SSH session and closes it at the end. After sending the command, the addon stops waiting when it detects the prompt or when the device produces no output for 5 seconds. There is no configurable connection timeout or initial-prompt timeout; a device that stops responding can leave the execution waiting.

### Exit status and diagnostics

| Condition | Status | Output |
| --- | --- | --- |
| Successful command | `0` | Filtered command output on standard output |
| SSH connection failure | Non-zero | The SSH error on standard error |
| Missing or invalid argument | `2` | Usage summary on standard error |

### Common failures

- **The connection fails with a non-zero status** — the device is unreachable, the SSH service is not on the default port, the user or password is wrong, or the device rejects the connection. Check the address, the SSH service and the credentials from the same host.
- **The output is empty** — the command has no `\n` and was not executed, the command is not valid for the device, the user lacks the required privilege, enable mode was needed but not supplied, or `extra_command` failed. Run the same command manually on the device.
- **Expected lines are missing** — the filter removed them because they contain `enable`, `Password:` or the command text. Check the complete response on the device and adjust the command. There is no option to disable the filter.
- **The output is truncated** — the device produced no data for 5 seconds before the prompt returned, or the command takes longer than the fixed wait. There is no configurable timeout; use a command that returns its output continuously or faster.
- **The command is truncated at a colon** — the addon sends only the text after the first colon. Remove the colon from the command or use a different command.
- **The password is split unexpectedly** — the addon splits the `password` value on `/`. A password that contains `/` cannot be passed correctly.
- **`--debug` fails with a usage error** — the option requires a value; use `--debug 1`.

### Limitations

- No SSH port option: the addon uses the SSH default port.
- No configurable connection, initial-prompt or read timeout.
- The command must include its own line terminator as an escape sequence.
- Text before the first colon in the command is discarded.
- A password that contains `/` cannot be represented.
- The filter is always on, is case-sensitive, and cannot be disabled.
- No credential file: credentials are positional arguments.
- No host-key verification: any SSH host key is accepted.

## Reference

### Command-line arguments

| Argument | Position | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `address` | 1 | Yes | — | IP address or host name of the device |
| `username` | 2 | Yes | — | Device user |
| `password` | 3 | Yes | — | SSH password, or `<PASSWORD>/<ENABLE_PASSWORD>` |
| `command` | 4 | Yes | — | Command to run, with its line terminator as an escape sequence |
| `extra_command` | 5 | Yes | — | Command sent before the main command; use `""` for none |
| `--debug` | option | No | `0` | Takes a value; supplying the option enables progress messages regardless of the value |

`-h` or `--help` prints the usage summary and exits.

### Command preprocessing

| Step | Behavior |
| --- | --- |
| Colon split | The text before the first colon is discarded; the rest, including later colons, is sent |
| Escape interpretation | Escape sequences such as `\n`, `\r` and `\t` in `command` are interpreted |
| Line terminator | No newline is appended to `command`; include `\n` (and `\r` when required) |
| Extra command | `extra_command` is sent as plain text plus a newline; its escape sequences are not interpreted |

### Output processing

| Step | Behavior |
| --- | --- |
| Command removal | The sent command text is removed from the response |
| Prompt removal | The text captured before the command, normally the prompt, is removed |
| Last line | The last line of the response is always removed |
| Whitespace | Leading and trailing whitespace is removed |
| Line filter | Lines containing `enable`, `Password:` or the command text are removed, case-sensitive |
| Blank lines | Empty lines are removed |

### Execution and output

```bash
./ssh_inventory <TARGET_HOST> <USERNAME> <PASSWORD> <COMMAND> <EXTRA_COMMAND> [--debug <VALUE>]
```

| Stream | Content |
| --- | --- |
| Standard output | Filtered command output |
| Standard error | Progress messages with `--debug`; SSH errors |
| Exit status | `0` on success, non-zero on an SSH failure, `2` on an argument error |

The addon uses the SSH default port and has no option to change it.

### Addon identity

| Property | Value |
| --- | --- |
| Marketplace identifier | `pandorafms.inventoryssh` |
| Name | Inventory SSH plugin |
| Version | `1.0` |
| Marketplace last update | 2025-06-25 |
| Package | `pandorafms.inventoryssh.1.0.zip` |
| Executable | `ssh_inventory` |
| Availability | Download limited to licensed users (license One) |
