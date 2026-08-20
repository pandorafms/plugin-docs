# Logparser

## Introduccion

Este documento describe la configuracion y uso del plugin Advanced Log Parser para la monitorizacion de logs en Pandora FMS. El plugin escanea un directorio en busca de ficheros de log, aplica filtros mediante expresiones regulares sobre el nombre de fichero y el contenido de las lineas, y genera modulos de tipo log con los resultados codificados en base64.

A diferencia de otros plugins de monitorizacion de logs, Advanced Log Parser utiliza un sistema de indices incremental: solo procesa las lineas nuevas que aparecen en los ficheros desde la ultima ejecucion, evitando relecturas y duplicados.

## Requisitos

- Acceso de lectura a los ficheros de log del directorio especificado.
- Acceso de lectura y escritura al directorio de indices. Por defecto se usa `/tmp`.
- El usuario que ejecuta el plugin debe tener permisos para leer los ficheros de log y escribir en el directorio de indices.

## Matriz de compatibilidad

| **Sistemas donde se ha probado** | Rocky 9 |
| --- | --- |
| **Sistemas donde deberia funcionar** | Cualquier sistema Linux soportado por Pandora FMS |

## Parametros

El plugin recibe todos los parametros directamente por linea de comandos:

```
pandora_logparser --dir <path> [opciones]

```

> **Importante**: Entrecomille siempre los parametros que contengan `*`, `?`, `|` u otros metacaracteres para evitar que el shell los expanda. Por ejemplo: `'*.log'`, `'(?i)error'`.

#### Tabla de parametros

| **Parametro** | **Descripcion** |
| --- | --- |
| `--dir` * | Directorio que contiene los ficheros de log a procesar. |
| `--name-regex` | Expresion regular para filtrar nombres de fichero. Por defecto: `.*` (todos los ficheros). |
| `--content-regex` | Expresion regular para filtrar lineas del contenido del log. Por defecto: `.*` (todas las lineas). |
| `--source-type` | Valor del campo `source` en el modulo de log. Identifica el origen de los datos en Pandora FMS. |
| `--idx-dir` | Directorio donde se almacenan los ficheros de indice. Por defecto: `/tmp`. |

* Parametro obligatorio.

#### Ejemplos de expresiones regulares

**Filtro por nombre de fichero (`name_regex`):**

```
.*\.log              → solo ficheros con extension .log
access.*\.log        → ficheros que empiezan por "access" y terminan en ".log"
(app|sys)\.log       → ficheros "app.log" o "sys.log"

```

**Filtro por contenido (`content_regex`):**

```
(?i)error                → lineas que contienen "error" (sin distincion de mayusculas/minusculas)
(?i)error|critical|fail  → lineas con error, critical o fail
^ERROR                   → lineas que empiezan por ERROR
[0-9]{3}\s               → lineas que contienen un codigo de 3 digitos seguido de espacio

```

## Configuracion del plugin

Copie el binario al directorio de plugins del agente Pandora FMS y configurese como `module_plugin` en el fichero de configuracion del agente.

Ejemplo de configuracion en Linux:

```
module_begin
module_name LogParser_AppErrors
module_plugin /var/opt/PandoraFMS/etc/pandora/plugins/pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error|critical' --source-type app_source --idx-dir /var/spool/pandora
module_interval 300
module_end

```

El agente ejecutara el plugin cada `module_interval` segundos. La primera ejecucion no generara datos: el plugin creara los indices apuntando al final de cada fichero. En las siguientes ejecuciones, el plugin procesara unicamente las lineas nuevas que cumplan los filtros configurados.

#### Varios modulos sobre el mismo directorio

Se pueden definir varios modulos con distintos filtros sobre el mismo directorio de logs:

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

## Ejemplos de uso

#### Capturar todas las lineas nuevas de ficheros .log

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log'

```

#### Filtrar solo lineas con ERROR

```bash
pandora_logparser --dir /var/log/myapp --name-regex '.+\.log' --content-regex '(?i)error' --source-type myapp_errors

```

#### Filtrar por nombre de fichero y contenido, con directorio de indices personalizado

```bash
pandora_logparser --dir /opt/app/logs --name-regex 'access.*\.log' --content-regex '^50[023]' --source-type http_errors --idx-dir /var/spool/pandora

```

#### Flujo tipico de ejecuciones

```bash
# Primera ejecucion: crea indices, sin salida
pandora_logparser --dir /tmp/logs --name-regex '.+\.log' --content-regex 'ERROR' --source-type my_source

# Se escriben nuevas lineas en el log
printf 'INFO: ok\nERROR: disco lleno\n' >> /tmp/logs/app.log

# Segunda ejecucion: solo captura las lineas nuevas que contienen ERROR
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
# Tercera ejecucion sin cambios: sin salida
pandora_logparser --dir /tmp/logs --name-regex '.+\.log' --content-regex 'ERROR' --source-type my_source

```

## Funcionamiento

#### Lectura incremental

El plugin mantiene un fichero de indice por cada fichero de log procesado. El indice almacena la posicion exacta (en bytes) donde se dejo de leer en la ejecucion anterior. En cada nueva ejecucion, el plugin lee unicamente desde esa posicion hasta el final del fichero, procesando solo el contenido nuevo.

#### Primera ejecucion

Cuando el plugin encuentra un fichero de log por primera vez, crea su indice apuntando al final del fichero. De esta forma no se procesa el contenido historico del log, evitando volcados masivos de datos antiguos.

#### Deteccion de rotacion de logs

El plugin detecta automaticamente cuando un fichero de log ha sido rotado:

- Si el fichero ha sido renombrado y se ha creado uno nuevo con el mismo nombre, el plugin lo detecta y comienza a leer desde el principio del nuevo fichero.
- Si el fichero ha sido truncado (su tamano es menor que la posicion guardada), el plugin reinicia la lectura desde el principio.

#### Purga de indices huerfanos

En cada ejecucion, el plugin verifica que todos los indices almacenados correspondan a ficheros de log que aun existen. Si se ha eliminado un fichero de log, su indice asociado se borra automaticamente, evitando la acumulacion de indices innecesarios.

#### Codificacion de la salida

Las lineas capturadas se concatenan y se codifican en base64 antes de incluirse en el XML de salida. Esto garantiza que el XML sea valido independientemente del contenido del log, incluyendo caracteres especiales, logs multilingües (japones, ruso, etc.) o contenido binario.

#### Formato del indice

Cada fichero `.idx` contiene:

```
/ruta/absoluta/al/fichero/log
<posicion_bytes> <numero_inode>

```

- Primera linea: ruta absoluta del fichero de log (usada para la purga de huerfanos).
- Segunda linea: posicion en bytes donde se dejo de leer e identificador interno del fichero (usado para detectar rotaciones).