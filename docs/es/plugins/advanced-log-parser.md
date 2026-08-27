# Advanced Log Parser

## Introducción

Este documento describe la configuración y uso del plugin Advanced Log Parser para la monitorización de logs en Pandora FMS. El plugin escanea un directorio en busca de ficheros de log, aplica filtros mediante expresiones regulares sobre el nombre de fichero y el contenido de las líneas, y genera módulos de tipo log con los resultados codificados en base64.

A diferencia de otros plugins de monitorización de logs, Advanced Log Parser utiliza un sistema de índices incremental: solo procesa las líneas nuevas que aparecen en los ficheros desde la última ejecución, evitando relecturas y duplicados.

## Matriz de compatibilidad

| **Sistemas donde se ha probado** | Rocky 9 |
| --- | --- |
| **Sistemas donde funciona** | Cualquier sistema Linux soportado por Pandora FMS |

## Prerrequisitos

- Acceso de lectura a los ficheros de log del directorio especificado.
- Acceso de lectura y escritura al directorio de índices. Por defecto se usa `/tmp`.
- El usuario que ejecuta el plugin debe tener permisos para leer los ficheros de log y escribir en el directorio de índices.

## Parámetros

> **Importante**: Entrecomille siempre los parámetros que contengan `*`, `?`, `|` u otros metacaracteres para evitar que el shell los expanda. Por ejemplo: `'*.log'`, `'(?i)error'`.

### Tabla de parámetros

| **Parámetro** | **Descripción** |
| --- | --- |
| `--dir` * | Directorio que contiene los ficheros de log a procesar. |
| `--name-regex` | Expresión regular para filtrar nombres de fichero. Por defecto: `.*` (todos los ficheros). |
| `--content-regex` | Expresión regular para filtrar líneas del contenido del log. Por defecto: `.*` (todas las líneas). |
| `--source-type` | Valor del campo `source` en el modulo de log. Identifica el origen de los datos en Pandora FMS. |
| `--idx-dir` | Directorio donde se almacenan los ficheros de índice. Por defecto: `/tmp`. |

* Parámetro obligatorio.

### Ejemplos de expresiones regulares

**Filtro por nombre de fichero (`name_regex`):**

```
.*\.log              → solo ficheros con extensión .log
access.*\.log        → ficheros que empiezan por "access" y terminan en ".log"
(app|sys)\.log       → ficheros "app.log" o "sys.log"

```

**Filtro por contenido (`content_regex`):**

```
(?i)error                → líneas que contienen "error" (sin distinción de mayúsculas/minúsculas)
(?i)error|critical|fail  → líneas con error, critical o fail
^ERROR                   → líneas que empiezan por ERROR
[0-9]{3}\s               → líneas que contienen un codigo de 3 digitos seguido de espacio

```

## Ejecución manual

### Formato de ejecución

El plugin recibe todas las opciones por línea de comandos:

```
pandora_logparser --dir <path> [opciones]

```

#### Ejemplos

##### Capturar todas las líneas nuevas de ficheros .log

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log'

```

##### Filtrar solo líneas con ERROR

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type myapp_errors

```

##### Filtrar por nombre de fichero y contenido, con directorio de índices personalizado

```bash
pandora_logparser --dir /opt/app/logs --name-regex 'access.*\.log' --content-regex '^50[023]' --source-type http_errors --idx-dir /var/spool/pandora

```

##### Flujo típico de ejecuciones

```bash
# Primera ejecución: crea índices, sin salida
pandora_logparser --dir /tmp/logs --name-regex '.+\.log' --content-regex 'ERROR' --source-type my_source

# Se escriben nuevas líneas en el log
printf 'INFO: ok\nERROR: disco lleno\n' >> /tmp/logs/app.log

# Segunda ejecución: solo captura las líneas nuevas que contienen ERROR
pandora_logparser --dir /tmp/logs --name-regex '.+\.log' --content-regex 'ERROR' --source-type my_source

```

Salida generada:

```xml
<log_module>
  <source><![CDATA[my_source]]></source>
  <data encoding="base64">RVJST1I6IGRpc2NvIGxsZW5v</data>
</log_module>

```

```bash
# Tercera ejecución sin cambios: sin salida
pandora_logparser --dir /tmp/logs --name-regex '.+\.log' --content-regex 'ERROR' --source-type my_source

```

#### Modo verbose

El plugin no dispone de ningún parámetro de verbose o depuración. Los diagnósticos van a la
salida de error estándar: un aviso cuando no se puede crear o cargar un índice, y un error cuando no se
puede leer un fichero de log o construir un módulo. La salida estándar contiene únicamente el XML
generado, de modo que redirigir ambos flujos por separado mantiene los datos limpios.

## Configuración en PandoraFMS

Copie el binario al directorio de plugins del agente Pandora FMS y configurese como `module_plugin` en el fichero de configuración del agente.

Ejemplo de configuración en Linux:

```
module_begin
module_name LogParser_AppErrors
module_plugin /var/opt/PandoraFMS/etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error|critical' --source-type app_source --idx-dir /var/spool/pandora
module_interval 300
module_end

```

El agente ejecutara el plugin cada `module_interval` segundos. La primera ejecución no generara datos: el plugin creara los índices apuntando al final de cada fichero. En las siguientes ejecuciones, el plugin procesara unicamente las líneas nuevas que cumplan los filtros configurados.

### Varios módulos sobre el mismo directorio

Se pueden definir varios módulos con distintos filtros sobre el mismo directorio de logs:

```
# Modulo para errores
module_begin
module_name Log_AppErrors
module_plugin /opt/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type app_errors
module_interval 300
module_end

# Modulo para avisos
module_begin
module_name Log_AppWarnings
module_plugin /opt/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)warn' --source-type app_warnings
module_interval 300
module_end

```

## Agentes y módulos generados por el plugin

El plugin no crea ningún agente propio. Lo ejecuta un agente de Pandora FMS como módulo de
plugin, y los módulos de log que genera se asocian a ese agente.

Por cada fichero analizado que tenga líneas nuevas coincidentes con `--content-regex`, el plugin emite
una entrada `log_module` que contiene:

| Campo | Contenido |
| --- | --- |
| `source` | El valor de `--source-type`, literal. Identifica el origen de los datos en Pandora FMS. |
| `data` | Las líneas coincidentes, unidas por saltos de línea y codificadas en base64 (`encoding="base64"`). |

Los ficheros sin líneas nuevas coincidentes no producen ninguna entrada, y una ejecución en la que nada
coincide no escribe absolutamente nada en la salida estándar. El plugin no crea módulos numéricos ni
informa de un módulo de estado: los módulos de log son su única salida.

## Funcionamiento

### Lectura incremental

El plugin mantiene un fichero de índice por cada fichero de log procesado. El índice almacena la posición exacta (en bytes) donde se dejo de leer en la ejecución anterior. En cada nueva ejecución, el plugin lee unicamente desde esa posición hasta el final del fichero, procesando solo el contenido nuevo.

### Primera ejecución

Cuando el plugin encuentra un fichero de log por primera vez, crea su índice apuntando al final del fichero. De esta forma no se procesa el contenido historico del log, evitando volcados masivos de datos antiguos.

### Detección de rotación de logs

El plugin detecta automáticamente cuando un fichero de log ha sido rotado:

- Si el fichero ha sido renombrado y se ha creado uno nuevo con el mismo nombre, el plugin lo detecta y comienza a leer desde el principio del nuevo fichero.
- Si el fichero ha sido truncado (su tamaño es menor que la posición guardada), el plugin reinicia la lectura desde el principio.

### Purga de índices huérfanos

En cada ejecución, el plugin verifica que todos los índices almacenados correspondan a ficheros de log que aun existen. Si se ha eliminado un fichero de log, su índice asociado se borra automáticamente, evitando la acumulacion de índices innecesarios.

### Codificación de la salida

Las líneas capturadas se concatenan y se codifican en base64 antes de incluirse en el XML de salida. Esto garantiza que el XML sea valido independientemente del contenido del log, incluyendo caracteres especiales, logs multilingües (japones, ruso, etc.) o contenido binario.

### Formato del índice

Cada fichero `.idx` contiene:

```
/ruta/absoluta/al/fichero/log
<posición_bytes> <numero_inode>

```

- Primera linea: ruta absoluta del fichero de log (usada para la purga de huérfanos).
- Segunda linea: posición en bytes donde se dejo de leer e identificador interno del fichero (usado para detectar rotaciones).
