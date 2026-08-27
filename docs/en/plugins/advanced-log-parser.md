# Advanced Log Parser

## Introduction

This document describes the configuration and usage of the Advanced Log Parser plugin for log monitoring in Pandora FMS. The plugin scans a directory for log files, applies regular expression filters on file names and line content, and generates log-type modules with the results encoded in base64.

Unlike other log monitoring plugins, Advanced Log Parser uses an incremental indexing system: it only processes new lines that appear in files since the last execution, avoiding re-reads and duplicates.

## Compatibility matrix

| **Systems where tested** | Rocky 9 |
| --- | --- |
| **Systems where it works** | Any Linux system supported by Pandora FMS |

## Prerequisites

- Read access to the log files in the specified directory.
- Read and write access to the index directory. Default path: `/tmp`.
- The user running the plugin must have permissions to read the log files and write to the index directory.

## Parameters

> **Important**: Always quote parameters containing `*`, `?`, `|` or other shell metacharacters. Example: `'*.log'`, `'(?i)error'`.

### Parameter reference

| **Parameter** | **Description** |
| --- | --- |
| `--dir` * | Directory containing the log files to process. |
| `--name-regex` | Regular expression to filter file names. Default: `.*` (all files). |
| `--content-regex` | Regular expression to filter lines within the log content. Default: `.*` (all lines). |
| `--source-type` | Value of the `source` field in the log module. Identifies the data source in Pandora FMS. |
| `--idx-dir` | Directory where index files are stored. Default: `/tmp`. |

* Required parameter.

### Regular Expression Examples

**File name filter (`name_regex`):**

```
.*\.log              → only files with .log extension
access.*\.log        → files starting with "access" and ending in ".log"
(app|sys)\.log       → files named "app.log" or "sys.log"

```

**Content filter (`content_regex`):**

```
(?i)error                → lines containing "error" (case-insensitive)
(?i)error|critical|fail  → lines containing error, critical, or fail
^ERROR                   → lines starting with ERROR
[0-9]{3}\s               → lines containing a 3-digit code followed by a space

```

## Manual execution

### Execution format

The plugin takes every option on the command line:

```
pandora_logparser --dir <path> [options]

```

#### Examples

##### Capture all new lines from .log files

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log'

```

##### Filter only lines containing ERROR

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type myapp_errors

```

##### Filter by file name and content, with a custom index directory

```bash
pandora_logparser --dir /opt/app/logs --name-regex 'access.*\.log' --content-regex '^50[023]' --source-type http_errors --idx-dir /var/spool/pandora

```

##### Typical Execution Flow

```bash
# First execution: creates indexes, no output
pandora_logparser --dir /tmp/logs --name-regex '.+\.log' --content-regex 'ERROR' --source-type my_source

# New lines are written to the log
printf 'INFO: ok\nERROR: disk full\n' >> /tmp/logs/app.log

# Second execution: only captures new lines containing ERROR
pandora_logparser --dir /tmp/logs --name-regex '.+\.log' --content-regex 'ERROR' --source-type my_source

```

Generated output:

```xml
<log_module>
  <source><![CDATA[my_source]]></source>
  <data encoding="base64">RVJST1I6IGRpc2NvIGxsZW5v</data>
</log_module>

```

```bash
# Third execution with no changes: no output
pandora_logparser --dir /tmp/logs --name-regex '.+\.log' --content-regex 'ERROR' --source-type my_source

```

#### Verbose mode

The plugin has no verbose or debug flag. Diagnostics go to standard error: a warning when an
index cannot be created or loaded, and an error when a log file cannot be read or a module cannot be
built. Standard output carries only the generated XML, so redirecting the two streams separately keeps
the data clean.

## Configuration in PandoraFMS

Copy the binary to the Pandora FMS agent plugins directory and configure it as a `module_plugin` in the agent configuration file.

Configuration example on Linux:

```
module_begin
module_name LogParser_AppErrors
module_plugin /var/opt/PandoraFMS/etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error|critical' --source-type app_source --idx-dir /var/spool/pandora
module_interval 300
module_end

```

The agent will run the plugin every `module_interval` seconds. The first execution will not generate data: the plugin will create indexes pointing to the end of each file. On subsequent executions, the plugin will only process new lines that match the configured filters.

### Multiple Modules on the Same Directory

You can define several modules with different filters on the same log directory:

```
# Module for errors
module_begin
module_name Log_AppErrors
module_plugin /opt/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors
module_interval 300
module_end

# Module for warnings
module_begin
module_name Log_AppWarnings
module_plugin /opt/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)warn' --source-type app_warnings
module_interval 300
module_end

```

## Agent and modules generated by the plugin

The plugin creates no agent of its own. It is executed by a Pandora FMS agent as a plugin
module, and the log modules it emits are attached to that agent.

For every scanned file that has new lines matching `--content-regex`, the plugin emits one `log_module`
entry containing:

| Field | Content |
| --- | --- |
| `source` | The value of `--source-type`, verbatim. It identifies the data origin in Pandora FMS. |
| `data` | The matched lines, joined by newlines and encoded in base64 (`encoding="base64"`). |

Files with no new matching lines produce no entry, and an execution where nothing matched writes nothing
at all to standard output. The plugin does not create numeric modules, and it reports no status module:
log modules are its only output.

## How it works

### Incremental Reading

The plugin maintains an index file for each processed log file. The index stores the exact byte position where reading stopped in the previous execution. On each new execution, the plugin reads only from that position to the end of the file, processing only new content.

### First Execution

When the plugin encounters a log file for the first time, it creates an index pointing to the end of the file. This way, historical log content is not processed, avoiding massive dumps of old data.

### Log Rotation Detection

The plugin automatically detects when a log file has been rotated:

- If the file has been renamed and a new one created with the same name, the plugin detects it and starts reading from the beginning of the new file.
- If the file has been truncated (its size is smaller than the saved position), the plugin restarts reading from the beginning.

### Orphan Index Cleanup

On each execution, the plugin checks that all stored indexes correspond to log files that still exist. If a log file has been deleted, its associated index is automatically removed, preventing the accumulation of unnecessary indexes.

### Output Encoding

Captured lines are concatenated and encoded in base64 before being included in the output XML. This guarantees valid XML regardless of the log content, including special characters, multilingual logs (Japanese, Russian, etc.), or binary content.

### Index File Format

Each `.idx` file contains:

```
/absolute/path/to/log/file
<byte_position> <inode_number>

```

- First line: absolute path to the log file (used for orphan cleanup).
- Second line: byte position where reading stopped and internal file identifier (used for rotation detection).
