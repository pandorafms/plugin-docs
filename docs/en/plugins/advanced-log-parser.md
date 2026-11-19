# Advanced Log Parser

*Article last updated: 2026-11-19.*

## What it does

Advanced Log Parser monitors log files from Pandora FMS. On each run it scans a directory, selects files by name and lines by content with regular expressions, and prints the matching lines as Pandora FMS `log_module` entries on standard output.

The plugin reads each log file incrementally. It keeps an index per log file and per source type, so a run captures only the lines written since the previous run instead of the whole file. Captured lines are encoded in Base64, which keeps the generated XML valid whatever the contents of the log.

The plugin always emits UTF-8. A log file written in a legacy single-byte code page, such as Windows-1251, is converted line by line before the lines are matched and encoded; see [Log file encoding](#log-file-encoding).

The plugin runs as a Pandora FMS agent plugin (`module_plugin`), and it can also be run by hand. It creates no agent of its own: the log modules it emits belong to the agent that executes it.

## Prepare

### Compatibility

| Systems where it has been tested | Rocky 9; Windows 11 with the Pandora FMS agent for Windows |
| --- | --- |
| Systems where it works | Any Linux system supported by Pandora FMS |

### Requirements

- Read access to the scanned directory and to the log files inside it.
- Read and write access to the index directory. By default the plugin uses the temporary directory of the operating system: `/tmp` on most Linux systems, or the path in `TMPDIR` when that variable is set.
- The user that runs the plugin must have those permissions, because the agent runs the plugin as its own user.

### Install

The plugin is distributed as a single binary. Two deployment paths are available.

**Manual upload** — copy the binary to the plugins directory of the Pandora FMS agent and make it executable. On Linux the plugins directory of the agent is `/etc/pandora/plugins`, and on Windows it is `%ProgramFiles%\pandora_agent\util`.

**Collections** — deploy the same binary to many agents at once from the Pandora FMS console. This route requires:

- Remote configuration enabled on the agent, which is only available with the Tentacle transfer mode.
- The `unzip` command on the agent. Each collection is transferred as a ZIP file and the agent extracts it locally.

Create the collection in **Configuration → Collections**, add the binary to it, and assign the collection to each agent from the **Collection** tab of the agent. The agent extracts the collection under a directory named after the collection short name, so the binary does not end up in the plugins directory:

| Platform | Path of the binary in the agent |
| --- | --- |
| Linux | `/etc/pandora/collections/<short-name>/pandora_logparser` |
| Windows | `%ProgramFiles%\pandora_agent\collections\<short-name>\pandora_logparser.exe` |

On Linux `/etc/pandora/collections` is the same directory as `/usr/share/pandora_agent/collections`.

Because the path carries the short name, the `module_plugin` line must use the full path:

```
module_plugin /etc/pandora/collections/<short-name>/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --idx-dir /var/tmp/pandora-logparser
```

The console keeps each collection in sync with an MD5 hash: when the collection changes in the console, the agent replaces its copy and discards any local modification. With remote configuration enabled the agent also overwrites its local `pandora_agent.conf` with the configuration stored in the console, so register the module from the console rather than editing the file on the agent.

## Configure

### Register the plugin in the agent

Add a `module_plugin` block to the agent configuration file. The agent runs the plugin at its own interval and attaches the emitted log modules to itself:

```
module_begin
module_plugin /etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error|critical' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
module_end
```

The block needs no `module_name`: the plugin generates its own modules and the agent appends them unchanged, so a name there would not name anything you see in the console. The agent only uses it in its own log messages, and derives one when the directive is absent.

The first execution produces no data: the plugin records each matching file at its current end. Later executions capture only the new matching lines.

Always quote options that contain `*`, `?`, `|` or other shell metacharacters, for example `'.+\.log'` or `'(?i)error'`, so that the shell does not expand them. That is Linux shell quoting; the Windows agent runs the command through `cmd.exe`, where the rules are different. See [Windows: non-ASCII values and shell metacharacters](#windows-non-ascii-values-and-shell-metacharacters).

### Indexes and the source type

Each log file has one index per source type. The `--source-type` value is part of the identity of that index, which has three consequences:

- Two modules that read the same log file must use different `--source-type` values. If they share it, they share the index and only the module that runs first sees the new lines.
- Changing the `--source-type` of an existing module makes that module start again at the end of the file. Everything written since the last run of the previous source type is skipped.
- The `source` field of the generated log modules carries the `--source-type` value verbatim, so it also identifies the data origin in Pandora FMS.

Do not reuse a `--source-type` value for a different log file and filter combination unless you intend to share the read position.

### Several modules over the same files

Define one `module_plugin` block per filter and give each block its own `--source-type`:

```
# Module for errors
module_begin
module_plugin /etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
module_end

# Module for warnings
module_begin
module_plugin /etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)warn' --source-type app_warnings --idx-dir /var/tmp/pandora-logparser
module_end
```

### Configuration file

Use `--config <path>` to read the options from a UTF-8 file instead of, or in addition to, the command line:

```
dir = /var/log/myapp
name_regex = .+\.log
content_regex = (?i)error
source_type = app_errors
idx_dir = /var/tmp/pandora-logparser
```

File format:

- One `key = value` per line. The valid keys are `dir`, `name_regex`, `content_regex`, `content_regex_base64`, `source_type`, `idx_dir`, `max_line_bytes`, `charset` and `charset_fallback`.
- Whitespace around `=` is ignored and the value is trimmed. A pattern that must begin or end with a space uses the escape `\x20`.
- `#` starts a comment only at the beginning of a line, so a value may contain `#`. Blank lines are ignored.
- A UTF-8 BOM and CR/LF line endings are accepted.
- The file may be partial: a key that is not present keeps its built-in default.
- An unknown key, a duplicate key, an empty value, or a line without `=` is an error, and the run stops. The key `config` is rejected because recursion is not supported.
- The configuration file must not exceed 4 MiB.

Precedence:

- An option set explicitly on the command line wins per key over the value in the configuration file. An explicit `--name-regex '.*'` is still an explicit choice.
- The content filter is resolved as a group. When the command line provides `--content-regex` or `--content-regex-base64`, the `content_regex` and `content_regex_base64` keys of the file are ignored entirely.
- Two content filter sources inside the same layer are an error: two command-line options, or both `content_regex` and `content_regex_base64` in the file.
- With no source at all, the default `.*` applies. At least one option source must provide `dir`.

### Log file encoding

The plugin sends every log line to Pandora FMS as UTF-8. The `--charset` option (or the `charset` key of the configuration file) tells it how to read the log file:

| Value | Behaviour |
| --- | --- |
| `auto` (default) | Decides line by line. A line that is already valid UTF-8 is sent unchanged. Any other line is converted with the first charset of the fallback chain that defines every byte of the line. |
| `utf-8` | No conversion: every line is sent exactly as it is in the file. |
| A code page name, such as `cp1251` | Every line is converted from that code page, without inspecting the content. A wrong value produces readable but incorrect text. |

The fallback chain of `auto` is `cp1251,cp1252`. Change it with `--charset-fallback` (or the `charset_fallback` key), which takes a comma-separated list tried in order. It is only valid together with `--charset auto`.

```
module_plugin /etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --source-type app_errors --idx-dir /var/tmp/pandora-logparser --charset-fallback cp1252
```

```
charset = auto
charset_fallback = cp1252,cp1251
```

Behaviour to know:

- The decision is taken for every line and nothing is stored in the index, so the same bytes always produce the same text. A file can mix UTF-8 lines and lines in a legacy code page.
- The default order assumes Cyrillic data. A single-byte code page cannot be told apart from another by its bytes alone, and Windows-1251 accepts almost every byte, so text in Latin-1 or Windows-1252 such as `café` is read as Windows-1251 (`cafй`) unless the chain starts with `cp1252`. Set `charset_fallback = cp1252` for logs in Western European languages.
- A byte that is not defined in the chosen code page (or in the last charset of the chain, in `auto`) is replaced with the character `U+FFFD`. The line is still sent and a warning is written to standard error.
- Conversion happens before the content filter, so a UTF-8 `--content-regex` also matches text read from a single-byte file. `--max-line-bytes` is measured on the bytes of the file.
- Only single-byte code pages are supported. Multi-byte encodings such as Shift_JIS and UTF-16 are rejected at startup. The accepted names are: `cp437`, `cp850`, `cp852`, `cp855`, `cp858`, `cp860`, `cp862`, `cp863`, `cp865`, `cp866`, `cp1250` to `cp1258`, `iso-8859-1` to `iso-8859-10`, `iso-8859-13` to `iso-8859-16`, `koi8-r`, `koi8-u`, `macintosh` and `macintosh-cyrillic`. Common spellings such as `windows-1251` and `latin1` are accepted as aliases.
- Use `--verbose` to see which charsets were applied; see [Diagnostics and exit status](#diagnostics-and-exit-status).

#### Choose the charset for your language

The default `auto` mode already handles UTF-8 and Windows-1251 (Cyrillic). For any other code page, put it first in the chain with `charset_fallback`. Each row below was run with the plugin and produced the text shown:

| The log is written in | Setting | Result |
| --- | --- | --- |
| UTF-8 | nothing | The lines are sent unchanged. |
| Russian on Windows (Windows-1251) | nothing | `Транзакция прошла успешно` |
| Spanish and other Western European languages (Windows-1252, Latin-1) | `charset_fallback = cp1252` | `Conexión rechazada: señor año` |
| Russian on Unix (KOI8-R) | `charset_fallback = koi8-r` | `Ошибка соединения` |
| Central European, such as Polish (Windows-1250) | `charset_fallback = cp1250` | `Łódź: błąd połączenia` |
| Greek (Windows-1253) | `charset_fallback = cp1253` | `Σφάλμα σύνδεσης` |

Without the setting, a log in another code page is still sent, but it is read as Windows-1251. The same Spanish line, run with `--verbose`:

```
$ pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --source-type app_errors --idx-dir /var/tmp/pandora-logparser --verbose
charset auto in /var/log/myapp/app.log: 0 utf-8, 1 converted from cp1251
Conexiуn rechazada: seсor aсo

$ pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --source-type app_errors --idx-dir /var/tmp/pandora-logparser --charset-fallback cp1252 --verbose
charset auto in /var/log/myapp/app.log: 0 utf-8, 1 converted from cp1252
Conexión rechazada: señor año
```

The second line of each result is the decoded `data` value. When the summary names a charset that is not the language of your log, add the right one with `--charset-fallback`.

Prefer `auto` with `charset_fallback` to a fixed `--charset cp1252`. A fixed charset converts every line without looking at it, so a line that is already UTF-8 in the same file would be damaged.

On Linux, add the option to the module:

```
module_begin
module_plugin /etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --source-type app_errors --idx-dir /var/tmp/pandora-logparser --charset-fallback cp1252
module_end
```

On Windows, keep the options in a configuration file and use a persistent index directory, so the index survives the cleaning of the temporary directory:

```
module_plugin "%ProgramFiles%\pandora_agent\util\pandora_logparser.exe" --config "C:\ProgramData\PandoraFMS\logparser.conf"
```

```
dir = C:\logs\myapp
name_regex = .+\.log
source_type = app_errors
idx_dir = C:\ProgramData\PandoraFMS\logparser-idx
charset_fallback = cp1252
```

### Windows: non-ASCII values and shell metacharacters

The plugin has no encoding problem of its own. On Windows, Go reads the command line through the wide-character API and converts it to UTF-8, and the plugin reads configuration files as UTF-8 and log files as described in [Log file encoding](#log-file-encoding). The corruption happens before the plugin starts.

The Windows agent runs every `module_plugin` as `cmd.exe /c "<command>"` and converts the command line from UTF-8 to the ANSI code page of the system. Non-ASCII text does not survive that conversion, so the plugin never receives the text you wrote.

The two failure modes are not equally visible:

| Value | Symptom |
| --- | --- |
| `dir` | The path does not exist after the conversion. The run fails with exit status `1`. |
| `content_regex`, `name_regex` | The pattern compiles and never matches. The run succeeds, prints nothing and captures no data. |

The second case is the dangerous one: nothing fails, so a non-ASCII pattern looks correct in the configuration while it quietly captures nothing.

#### Metacharacters of cmd.exe

The command also passes through `cmd.exe`, so its metacharacters stay active. Single quotes are not quoting characters for `cmd.exe`, so they never protect a pattern:

```
module_plugin ... --content-regex '(?i)error|critical' ...
```

```
'critical'' is not recognized as an internal or external command
```

Double quotes inside the pattern do protect it, because they survive the outer quotes the agent adds around the whole command. `%` is the exception, because `cmd.exe` expands it before the plugin starts:

| Pattern contains | Without quotes | With double quotes |
| --- | --- | --- |
| <code>&#124;</code> | fails, exit status `255` | works |
| `&` | fails, exit status `1` | works |
| `<` | fails, exit status `1` | works |
| `>` | **fails silently**, exit status `0` | works |
| `^` | **fails silently**, exit status `0` | works |
| a lone `%` | works | works |
| `%NAME%` | **fails silently** | **fails silently** |

A silent failure is the dangerous case: the run reports success, the plugin receives a truncated pattern, and it then captures lines the pattern you wrote would never match. `^` is the sharpest example, because it is the anchor at the start of patterns such as `^ERROR`: unprotected, the anchor disappears and the pattern matches anywhere in the line.

The two `%` rows are consistent: `cmd.exe` only expands a name between two percent signs, and double quotes do not prevent that expansion.

Only the configuration file and Base64 avoid every case above. Use one of them whenever a pattern contains any of these characters.

#### Passing non-ASCII values

Only the first of these routes works for a path.

**Configuration file (`--config`)** — the only route for a non-ASCII `dir`. The command line carries only the path to the file, which must be ASCII, and the values inside the file are read as UTF-8 from disk, so they never travel through the code page conversion:

```
dir = C:\registros_日本語_Ошибка
content_regex = (?i)error|critical
source_type = app_errors
```

```
module_plugin "%ProgramFiles%\pandora_agent\util\pandora_logparser.exe" --config "C:\ProgramData\PandoraFMS\logparser.conf"
```

**Base64 (`--content-regex-base64`)** — for the content pattern. Base64 is ASCII and carries no shell metacharacter, so it avoids both the code page and `cmd.exe`. Generate the value from the UTF-8 bytes of the pattern:

```bash
printf '%s' 'Ошибка' | base64
```

That command prints `0J7RiNC40LHQutCw`. On Windows, use PowerShell:

```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('Ошибка'))
```

**Unicode escapes (`\x{...}`)** — keeps the command line ASCII without a configuration file. The Go regular expression engine resolves them, so they are valid in `--content-regex` and `--name-regex`:

```
--content-regex '\x{041E}\x{0428}\x{0418}\x{0411}\x{041A}\x{0410}'
```

An escape works inside a regular expression only. There is no escape syntax for a path: `\x{...}` in `--dir` is the name of a literal directory.

#### What does not work

- Non-ASCII text on the command line. The agent converts it before the plugin starts, so `--dir` fails with exit status `1` and `--content-regex` fails silently.
- Writing the values in the ANSI code page inside `pandora_agent.conf`. The agent reads the command line as UTF-8 and converts it to ANSI, so ANSI bytes are already corrupted before that conversion.
- Single quotes around a pattern that contains any of the metacharacters above. `cmd.exe` does not treat single quotes as quoting, so the pattern is split and the run fails.
- A pattern containing `%NAME%`. `cmd.exe` expands it before the plugin starts and double quotes do not prevent it, so no command-line form works. Use the configuration file.

## Verify

Confirm the plugin works before wiring it into the agent. The example uses a fresh directory.

1. Create the log file and run the plugin once:

```bash
touch /var/log/myapp/app.log
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
```

The first run prints nothing and exits with status `0`: it has recorded the file at its current end.

2. Append a matching line:

```bash
printf 'ERROR: disk full\n' >> /var/log/myapp/app.log
```

3. Run the plugin again:

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
```

It now prints one `log_module` entry:

```xml
<log_module>
  <source><![CDATA[app_errors]]></source>
  <data>&#34;RVJST1I6IGRpc2sgZnVsbA==&#34;</data>
  <encoding>base64</encoding>
</log_module>
```

4. Decode the value of `data` to confirm the captured text:

```bash
printf 'RVJST1I6IGRpc2sgZnVsbA==' | base64 -d
```

```
ERROR: disk full
```

A third run with no new lines prints nothing and exits with status `0`. Files with no new matching lines produce no entry, and a run in which nothing matches writes nothing to standard output at all.

To check a log file that is not in UTF-8, append a line written in Windows-1251 (the word `Транзакция` as the bytes `D2 F0 E0 ED E7 E0 EA F6 E8 FF`) and run the plugin again with `--verbose`:

```bash
printf '\xd2\xf0\xe0\xed\xe7\xe0\xea\xf6\xe8\xff\n' >> /var/log/myapp/app.log
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --source-type app_errors --idx-dir /var/tmp/pandora-logparser --verbose
```

Standard error reports the decision, and the `data` value decodes to UTF-8 text:

```
charset auto in /var/log/myapp/app.log: 0 utf-8, 1 converted from cp1251
```

```
Транзакция
```

## Understand the results

### Incremental reading

The plugin keeps one index per log file and source type in `--idx-dir`. The index records the byte offset where reading stopped.

When the plugin encounters a log file for the first time it records the file at its current end and captures nothing, so historical content is never dumped. On later runs it reads from the recorded offset and processes only the new lines.

Removing or losing an index makes that log file start again at end-of-file: the next run records the file at its current end and skips the lines already written.

The scan is not recursive. Only the files directly inside `--dir` are considered, and subdirectories are ignored.

### Rotation and truncation

The plugin detects when a log file has been replaced or truncated:

- If the file was renamed and a new file was created under the same name, the plugin detects the new file and reads it from the beginning.
- If the file is smaller than the saved position, the plugin restarts the read from the beginning.

### Index maintenance

On every run the plugin removes indexes whose log file no longer exists, which prevents the index directory from growing with entries for deleted logs. It never touches index files that it does not own.

### Matching model

- Matching is applied to each physical line of the log.
- Matching is case-sensitive. A pattern that should ignore case needs an explicit `(?i)`, as in `(?i)error`.
- A multi-line entry such as a stack trace is captured as separate line fragments and cannot be matched as a whole.
- Lines are converted to UTF-8 before matching, as set by `--charset`, so a UTF-8 pattern also matches a log file written in a single-byte code page. See [Log file encoding](#log-file-encoding). UTF-16 and other multi-byte encodings are not decoded.
- A leading UTF-8 BOM in a log file is removed before matching, so `^` anchors still apply to the first line.

### Output

For every scanned file that has new matching lines, the plugin emits one `log_module` entry:

| Field | Content |
| --- | --- |
| `source` | The value of `--source-type`, verbatim. It identifies the data origin in Pandora FMS. |
| `data` | The matched lines joined by newlines and encoded in Base64, between double quotes. The XML serializer writes each quote as `&#34;`. |
| `encoding` | Always `base64`. |

The plugin creates no numeric or status module: log modules are its only output.

## Operate and troubleshoot

### Run the plugin manually

The plugin takes every option on the command line:

```
pandora_logparser --dir <path> [options]
pandora_logparser --config <path> [options]
```

Capture all new lines from `.log` files:

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --idx-dir /var/tmp/pandora-logparser
```

Filter only the lines that match a pattern:

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors --idx-dir /var/tmp/pandora-logparser
```

Filter by file name and content with a custom index directory:

```bash
pandora_logparser --dir /opt/app/logs --name-regex 'access.*\.log' --content-regex '^50[023]' --source-type http_errors --idx-dir /var/tmp/pandora-logparser
```

Read every option from a configuration file:

```bash
pandora_logparser --config /etc/pandora/logparser.conf
```

### Diagnostics and exit status

Standard output carries only the generated XML, and every diagnostic goes to standard error, so redirecting the two streams separately keeps the data clean.

`-v` or `--verbose` adds, in `--charset auto` mode, one line per scanned file and run that lists how its new lines were decoded, for example `charset auto in /var/log/myapp/app.log: 2 utf-8, 1 converted from cp1251`. It also reports lines that needed replacement characters. Nothing is printed for a file with no new lines, and the option has no effect in the other charset modes.

Warnings are issued when an index cannot be resolved or created, when an index cannot be loaded, when orphan cleanup fails, when a line is skipped for exceeding `--max-line-bytes`, and when a line contains bytes that are not defined in the chosen code page and is sent with `U+FFFD` replacement characters. Errors are issued when a directory or a log file cannot be read, when a log module cannot be built, and when an index cannot be saved.

The exit status is `0` for a successful run or for `--help`, and `1` for invalid input or for a processing error.

### Limits

- A line longer than `--max-line-bytes` is skipped with a warning and the file keeps working. The default is `1048576` bytes.
- A file that does not end with a newline keeps its trailing partial line unread until the terminator arrives. A line that is never terminated is never emitted.
- The plugin validates at most the 64 KiB immediately before the saved offset. An in-place rewrite that leaves the file identity, the size and those bytes unchanged is not detected.
- Only UTF-8 and single-byte code pages are decoded. UTF-16 and other multi-byte encodings are not supported.
- The plugin is not recursive and ignores subdirectories.

### Troubleshooting

| Symptom | Likely cause | Check |
| --- | --- | --- |
| No output on the first run | Expected behaviour: the index records each file at its end. | Append a matching line and run the plugin again. |
| A module never produces data | Another module uses the same `--source-type` over the same file, or the source type was changed and the index restarted at end-of-file. | Give each module its own `--source-type`; see [Indexes and the source type](#indexes-and-the-source-type). |
| A pattern that worked elsewhere matches nothing | Matching is case-sensitive, or the log file is in an encoding the plugin does not decode, such as UTF-16. | Add `(?i)` if case must be ignored; confirm the file encoding. |
| Accented text arrives with the wrong letters, for example `cafй` instead of `café` | The log is in Windows-1252 or Latin-1 and the default chain read it as Windows-1251. | Run with `--verbose` to see the charset applied, then set `--charset-fallback cp1252`. |
| A warning says that bytes are undefined and the line contains `�` | The line has bytes that the chosen code page does not define. | Check the charset of the file; set `--charset` or `--charset-fallback` to the right code page. |
| A non-ASCII pattern matches nothing on Windows | The agent converted the command line to the ANSI code page before the plugin started. | Put the value in the configuration file, or use `--content-regex-base64`; see [Windows: non-ASCII values and shell metacharacters](#windows-non-ascii-values-and-shell-metacharacters). |
| A module whose pattern has an alternation never runs on Windows | `cmd.exe` splits the command at the bare pipe. | Move the pattern to the configuration file or pass it in Base64. |
| A line is missing from the output | The line exceeds `--max-line-bytes`, or it was still unterminated when the plugin ran. | Check the warning on standard error; raise `--max-line-bytes` if needed. |
| `error: --dir is required unless the config file provides dir` | Neither the command line nor the configuration file provides a directory. | Pass `--dir`, or add `dir` to the configuration file. |
| A very long pattern is rejected or truncated on Windows | The Windows command line has a length limit and Base64 inflates the pattern. | Put the pattern in the configuration file. |

## Reference

### Command-line options

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `--dir <path>` | Yes, unless the configuration file provides `dir` | — | Directory to scan for log files. The scan is not recursive. |
| `--config <path>` | No | — | Read the parameters from a UTF-8 configuration file. |
| `--name-regex <regex>` | No | `.*` | Regular expression to filter file names. |
| `--content-regex <regex>` | No | `.*` | Regular expression to filter log lines. Conflicts with `--content-regex-base64`. |
| `--content-regex-base64 <value>` | No | — | Base64 value that decodes to the content regular expression. Conflicts with `--content-regex`. |
| `--source-type <name>` | No | `syslog` | Value of the `source` field of the generated log modules and part of the index identity. An empty value falls back to `syslog`. |
| `--idx-dir <dir>` | No | Temporary directory of the operating system | Directory where the index files are stored. It is created if it does not exist. |
| `--max-line-bytes <n>` | No | `1048576` | Maximum accepted log line size in bytes. Must be a positive integer. |
| `--charset <name>` | No | `auto` | Charset of the log file: `auto`, `utf-8` or a single-byte code page. See [Log file encoding](#log-file-encoding). |
| `--charset-fallback <list>` | No | `cp1251,cp1252` | Comma-separated charsets that `--charset auto` tries, in order, on lines that are not UTF-8. Only valid with `--charset auto`. |
| `-v`, `--verbose` | No | — | In `--charset auto` mode, report on standard error how the lines of each file were decoded. |
| `-h`, `--help` | No | — | Print the help and exit with status `0`. |

### Configuration file keys

| Key | Default | Description |
| --- | --- | --- |
| `dir` | — | Directory to scan. Equivalent to `--dir`. |
| `name_regex` | `.*` | Equivalent to `--name-regex`. |
| `content_regex` | `.*` | Equivalent to `--content-regex`. |
| `content_regex_base64` | — | Equivalent to `--content-regex-base64`. |
| `source_type` | `syslog` | Equivalent to `--source-type`. |
| `idx_dir` | Temporary directory of the operating system | Equivalent to `--idx-dir`. |
| `max_line_bytes` | `1048576` | Equivalent to `--max-line-bytes`. It must be a valid integer. |
| `charset` | `auto` | Equivalent to `--charset`. |
| `charset_fallback` | `cp1251,cp1252` | Equivalent to `--charset-fallback`. |

`content_regex` and `content_regex_base64` cannot both be present in the same file.

### Regular expression syntax

Patterns accept the common regular expression constructions, including `(?i)` for case-insensitive matching, POSIX classes such as `[[:digit:]]`, hexadecimal escapes such as `\x20`, and Unicode escapes such as `\x{041E}`. Lookaround is not supported: a pattern such as `a(?=b)` is rejected.

Examples for the file name filter:

```
.+\.log              → only files with the .log extension
access.*\.log        → files that start with "access" and end in ".log"
(app|sys)\.log       → files named "app.log" or "sys.log"
```

Examples for the content filter:

```
(?i)error                → lines containing "error", ignoring case
(?i)error|critical|fail  → lines containing error, critical or fail
^ERROR                   → lines that start with ERROR
[0-9]{3}\s               → lines with a three-digit code followed by a space
```

`--content-regex-base64` accepts the standard and URL-safe Base64 alphabets, padded or unpadded, and must decode to valid UTF-8; a leading BOM and trailing CR/LF bytes are ignored. To pass non-ASCII values through the Windows agent, see [Windows: non-ASCII values and shell metacharacters](#windows-non-ascii-values-and-shell-metacharacters).
